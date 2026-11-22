#!/usr/bin/env python3
"""BAKOQUAKE updater v2: verifies all game assets, checks GitHub with VPS fallback, and applies differential updates.

bq_update.py [--root DIR] [--check | --launch | --standalone] [--force-rehash] [--no-gui]
             [--manifest-url URL] [--fallback-url URL] [--platform NAME] [--bundle-mac-inputs PATH] [--version]

How it works (docs/updater-v2-plan.md):
- Checks GitHub Releases (releases/latest/download/manifest-<platform>.json), failing over to the VPS mirror
  (https://bakersfield.larrywew.fun/updates/manifest-<platform>.json) if GitHub is unreachable.
- Always stats every managed file in the manifest (even when the build number matches) so missing or damaged
  models, sounds, maps, pk3s, configs, or binaries are automatically detected and repaired.
- Downloads changed/missing files from the GitHub release zip via HTTP Range requests, automatically failing over
  per-file to content-addressed VPS blobs (<vps_base>/files/<sha256>). Every file is verified by size and sha256
  in .bq/staging before atomic replacement (with rollback from .bq/backup on locked files).
- On macOS (.app), checks Contents/Resources/mac-inputs against the manifest; if a new signed DMG is required,
  downloads and verifies it with the same progress bar, opens it, and blocks launching the old app.
- Shows a dark-theme GUI with live download speed and ETA when prompting or updating (invisible on fast up-to-date
  or offline launches). Only allows playing the installed version when genuinely offline (both GitHub and VPS
  unreachable).

Exit codes:
  0  Up to date (all managed files verified), genuinely offline during --launch, or closed in --standalone
  3  Files updated/repaired cleanly (--launch or CLI; launcher must re-exec itself)
  4  Update/repair required and declined/cancelled/failed, or macOS DMG update required (do NOT launch game)
  10 --check only: update or repair is available
  2  Bad CLI arguments
Stdlib only (+ optional tkinter for GUI), so it freezes cleanly with PyInstaller.
"""
import argparse
import hashlib
import json
import os
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

VERSION = 2
REPO = "BakersfieldQuake/BakersfieldQuake"
LATEST = f"https://github.com/{REPO}/releases/latest/download/manifest-{{platform}}.json"
VPS_BASE_DEFAULT = "https://bakersfield.larrywew.fun/updates"
VPS_LATEST = f"{VPS_BASE_DEFAULT}/manifest-{{platform}}.json"
UA = {"User-Agent": f"bq-update/{VERSION}"}
TIMEOUT = 12            # seconds per file/range request
CHECK_TIMEOUT = 4       # GitHub manifest check timeout
FALLBACK_TIMEOUT = 5    # VPS manifest fallback timeout
LOCK_STALE = 30 * 60
LOCK_WAIT_SECS = 20.0   # wait briefly if another updater holds update.lock before blocking launch
LOCK_POLL_SECS = 0.25
CRITICAL_VERIFY_SUFFIXES = (".bsp", ".lit", ".pk3", ".exe")


def _fsync_file(f):
    """Flushes Python buffers and forces OS write-through to disk before atomic rename."""
    f.flush()
    os.fsync(f.fileno())


def hash_file(path, check_cancel=None):
    """Streams a file from disk and returns (byte_size, sha256_hex)."""
    h = hashlib.sha256()
    total = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            if check_cancel:
                check_cancel()
            h.update(chunk)
            total += len(chunk)
    return total, h.hexdigest()


def acquire_lock(lock_path, log, wait_secs=None, poll_secs=None):
    """Acquires update.lock exclusively, waiting up to wait_secs if held by another active updater."""
    if wait_secs is None:
        wait_secs = LOCK_WAIT_SECS
    if poll_secs is None:
        poll_secs = LOCK_POLL_SECS
    deadline = time.monotonic() + max(0.0, float(wait_secs))
    waited = False
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, f"{os.getpid()}\n".encode("ascii"))
                os.fsync(fd)
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            try:
                stale = time.time() - lock_path.stat().st_mtime > LOCK_STALE
            except OSError:
                stale = True
            if stale:
                lock_path.unlink(missing_ok=True)
                continue
            now = time.monotonic()
            if now >= deadline:
                log(f"another update is still running after waiting {wait_secs:.1f}s; blocking launch")
                return False
            if not waited:
                log("another update is running; waiting for update.lock to clear...")
                waited = True
            time.sleep(min(poll_secs, max(0.01, deadline - now)))


class OfflineError(IOError):
    """Raised when neither GitHub nor the VPS fallback can be reached."""


class UpdateCancelled(Exception):
    """Raised when the user cancels or closes the updater mid-operation."""


def default_platform():
    if sys.platform.startswith("win"):
        return "windows-x64"
    if sys.platform == "darwin":
        return "macos-arm64"
    return "linux-x86_64"


def default_root():
    # Update.exe in package root -> its parent is the package root.
    # tools/bq_update.py (or legacy tools/bq-update.exe) -> package root is one folder up.
    me = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    if me.parent.name.lower() == "tools":
        return me.parent.parent
    return me.parent


def _ensure_streams(attach_console=False):
    """Ensures sys.stdout and sys.stderr are writable even in Windows --noconsole PyInstaller builds."""
    if os.name == "nt" and attach_console and (sys.stdout is None or sys.stderr is None):
        try:
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                if sys.stdout is None:
                    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                if sys.stderr is None:
                    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")


def fmt(n):
    if n >= 1e9:
        return f"{n / 1e9:.2f} GB"
    if n >= 1e5:
        return f"{n / 1e6:.1f} MB"
    if n >= 1e3:
        return f"{n / 1e3:.0f} KB"
    return f"{int(n)} B"


def fmt_speed(bps):
    if bps <= 0:
        return "calculating..."
    if bps >= 1e6:
        return f"{bps / 1e6:.1f} MB/s"
    if bps >= 1e3:
        return f"{bps / 1e3:.0f} KB/s"
    return f"{bps:.0f} B/s"


def fmt_eta(secs):
    if secs is None:
        return "estimating..."
    s = max(0, int(round(secs)))
    if s < 60:
        return f"~{s}s remaining"
    m, rem = divmod(s, 60)
    if m < 60:
        return f"~{m}m {rem:02d}s remaining"
    h, m = divmod(m, 60)
    return f"~{h}h {m:02d}m remaining"


class RateTracker:
    """EWMA download speed and ETA calculator resilient to retries and brief stalls."""

    def __init__(self, alpha=0.25, clock=time.monotonic):
        self.alpha = alpha
        self.clock = clock
        self.start_t = clock()
        self.last_t = self.start_t
        self.total_bytes = 0
        self.total_done = 0
        self.window_bytes = 0
        self.speed_bps = 0.0

    def start(self, total_bytes=0):
        now = self.clock()
        self.start_t = now
        self.last_t = now
        self.total_bytes = max(0, int(total_bytes))
        self.total_done = 0
        self.window_bytes = 0
        self.speed_bps = 0.0

    def update(self, new_total_done):
        """Updates tracker with monotonic total downloaded bytes."""
        delta = max(0, int(new_total_done) - self.total_done)
        self.total_done = max(self.total_done, int(new_total_done))
        self.window_bytes += delta
        now = self.clock()
        dt = now - self.last_t
        if dt >= 0.25 and self.window_bytes > 0:
            inst = self.window_bytes / dt
            self.speed_bps = inst if self.speed_bps <= 0.0 else (
                self.alpha * inst + (1.0 - self.alpha) * self.speed_bps
            )
            self.last_t = now
            self.window_bytes = 0

    def current_speed(self):
        elapsed = self.clock() - self.start_t
        if self.speed_bps > 0.0:
            return self.speed_bps
        if elapsed >= 0.3 and self.total_done > 0:
            return self.total_done / elapsed
        return 0.0

    def eta_seconds(self, remaining_bytes=None):
        if remaining_bytes is None:
            remaining_bytes = max(0, self.total_bytes - self.total_done)
        if remaining_bytes <= 0:
            return 0.0
        spd = self.current_speed()
        if spd <= 0.0:
            return None
        return remaining_bytes / spd


@dataclass
class UpdatePlan:
    kind: str  # "up_to_date" | "update" | "repair" | "dmg"
    manifest: dict
    source: str
    installed_build: int
    installed_version: str
    fetch: list = field(default_factory=list)
    delete: list = field(default_factory=list)
    total_bytes: int = 0
    missing_count: int = 0
    corrupt_count: int = 0
    total_managed: int = 0
    notes: str = ""
    cache: dict = field(default_factory=dict)
    dmg_url: str = ""
    dmg_vps_url: str = ""
    dmg_size: int = 0
    dmg_sha256: str = ""
    strays: list = field(default_factory=list)
    preserve_build: int = 0

    @property
    def needs_action(self):
        return self.kind in ("update", "repair", "dmg")


def default_open_dmg(dmg_path):
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(dmg_path)])
    elif os.name == "nt":
        os.startfile(str(dmg_path))  # type: ignore[attr-defined]


def default_downloads_dir():
    dl = Path.home() / "Downloads"
    if dl.is_dir():
        return dl
    return Path(tempfile.gettempdir())


def _is_github_url(url):
    return "github.com" in (url or "").lower() or "githubusercontent.com" in (url or "").lower()


def _summarize_files(fetch, delete, kind):
    if not fetch and not delete:
        return ""
    sample = list(fetch[:4])
    extra = len(fetch) - len(sample)
    parts = []
    if sample:
        verb = "Repairing" if kind == "repair" else "Files"
        s = ", ".join(Path(p).name for p in sample)
        if extra > 0:
            s += f" (+{extra} more)"
        parts.append(f"{verb}: {s}")
    if delete:
        parts.append(f"Removing {len(delete)} obsolete file(s)")
    return "\n".join(parts)


class Updater:
    def __init__(self, root, platform, manifest_url, log, fallback_url=None,
                 bundle_mac_inputs=None, open_dmg=None, downloads_dir=None, cancel_event=None):
        self.root = Path(root)
        self.platform = platform
        self.manifest_url = manifest_url
        self.fallback_url = fallback_url
        self.bundle_mac_inputs = Path(bundle_mac_inputs) if bundle_mac_inputs else None
        self.bq = self.root / ".bq"
        self.log = log
        self.open_dmg = open_dmg or default_open_dmg
        self.downloads_dir = Path(downloads_dir) if downloads_dir else None
        self.cancel_event = cancel_event or threading.Event()
        self.manifest = None
        self.manifest_source = "GitHub"
        self.zip_src = None
        self.zip_url = None
        self.zip_size = 0
        self._zip_entries = None

    def _check_cancel(self):
        if self.cancel_event.is_set():
            raise UpdateCancelled()

    # ---- state -------------------------------------------------------------------------------------------------
    def load_state(self):
        try:
            return json.loads((self.bq / "state.json").read_text("utf-8"))
        except (OSError, ValueError):
            return None

    def save_state(self, state):
        self.bq.mkdir(parents=True, exist_ok=True)
        tmp = self.bq / "state.json.tmp"
        payload = json.dumps(state, indent=1, sort_keys=True)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(payload)
            _fsync_file(f)
        os.replace(tmp, self.bq / "state.json")

    def local_sha(self, rel, cache, force):
        p = self.root / rel
        try:
            st = p.stat()
        except OSError:
            return None
        hit = cache.get(rel)
        if not force and hit and hit[0] == st.st_size and hit[1] == st.st_mtime_ns:
            return hit[2]
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                self._check_cancel()
                h.update(chunk)
        cache[rel] = [st.st_size, st.st_mtime_ns, h.hexdigest()]
        return cache[rel][2]

    # ---- network -----------------------------------------------------------------------------------------------
    def get_json(self, url, timeout):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.load(r)

    def fetch_manifest(self):
        """Fetches manifest from primary (GitHub) and falls back to VPS if configured."""
        primary_label = "GitHub" if _is_github_url(self.manifest_url) else "Primary"
        errors = []
        try:
            m = self.get_json(self.manifest_url, CHECK_TIMEOUT)
            self.manifest = m
            self.manifest_source = primary_label
            return m, primary_label
        except Exception as e:
            errors.append(f"{primary_label}: {e}")
            self.log(f"primary manifest fetch failed ({self.manifest_url}): {e}")

        if self.fallback_url:
            try:
                m = self.get_json(self.fallback_url, FALLBACK_TIMEOUT)
                self.manifest = m
                self.manifest_source = "VPS"
                self.log(f"using VPS fallback manifest: {self.fallback_url}")
                return m, "VPS"
            except Exception as e:
                errors.append(f"VPS: {e}")
                self.log(f"VPS manifest fetch failed ({self.fallback_url}): {e}")

        raise OfflineError("; ".join(errors))

    def resolve_vps_base(self, manifest):
        base = (manifest.get("vps_base") or "").strip().rstrip("/")
        if base:
            return base
        if self.fallback_url:
            return self.fallback_url.rsplit("/", 1)[0]
        return None

    def resolve(self, url):
        """Follows the release redirect once; returns (final signed URL, total size)."""
        req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.status != 206:
                raise IOError(f"server ignored Range (HTTP {r.status})")
            return r.geturl(), int(r.headers["Content-Range"].split("/")[1])

    def ranged(self, start, end):
        """Opens bytes start..end (inclusive) of the zip, re-resolving the signed URL once if it expired."""
        for attempt in (0, 1):
            self._check_cancel()
            req = urllib.request.Request(self.zip_url, headers={**UA, "Range": f"bytes={start}-{end}"})
            try:
                r = urllib.request.urlopen(req, timeout=TIMEOUT)
            except urllib.error.HTTPError as e:
                if e.code in (401, 403) and attempt == 0:
                    self.zip_url, _ = self.resolve(self.zip_src)
                    continue
                raise
            if r.status != 206:
                r.close()
                raise IOError(f"server ignored Range (HTTP {r.status})")
            return r
        raise IOError("unreachable")

    def central_directory(self):
        """Reads the zip's central directory with a few Range requests: {package path: ZipInfo}."""
        up = self

        class RangeFile:
            pos = 0

            def seekable(self):
                return True

            def tell(self):
                return self.pos

            def seek(self, off, whence=0):
                self.pos = off if whence == 0 else self.pos + off if whence == 1 else up.zip_size + off
                return self.pos

            def read(self, n=-1):
                up._check_cancel()
                n = up.zip_size - self.pos if n < 0 else min(n, up.zip_size - self.pos)
                if n <= 0:
                    return b""
                with up.ranged(self.pos, self.pos + n - 1) as r:
                    data = r.read()
                self.pos += len(data)
                return data

        zf = zipfile.ZipFile(RangeFile())
        prefix = self.manifest.get("root", "")
        return {i.filename[len(prefix):]: i for i in zf.infolist()
                if i.filename.startswith(prefix) and not i.is_dir()}

    def _ensure_zip_entries(self):
        if self._zip_entries is None:
            self.zip_src = self.manifest["zip"]
            self.zip_url, self.zip_size = self.resolve(self.zip_src)
            self._zip_entries = self.central_directory()
        return self._zip_entries

    def fetch_entry(self, info, dest, want_sha, want_size, progress):
        """One Range GET per entry: local header + data. Streams, inflates and hashes into dest."""
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise IOError(f"{info.filename}: unsupported compression {info.compress_type}")
        start = info.header_offset
        end = min(start + 30 + len(info.orig_filename.encode()) + 65535 + info.compress_size, self.zip_size) - 1
        h = hashlib.sha256()
        inflate = zlib.decompressobj(-15) if info.compress_type == zipfile.ZIP_DEFLATED else None
        written = 0
        with self.ranged(start, end) as r, open(dest, "wb") as out:
            hdr = r.read(30)
            if len(hdr) < 30 or hdr[:4] != b"PK\x03\x04":
                raise IOError(f"{info.filename}: bad local header")
            n, m = struct.unpack("<HH", hdr[26:30])
            skip = n + m
            while skip:
                self._check_cancel()
                chunk = r.read(min(skip, 1 << 16))
                if not chunk:
                    raise IOError(f"{info.filename}: connection closed early")
                skip -= len(chunk)
            left = info.compress_size
            while left:
                self._check_cancel()
                chunk = r.read(min(left, 1 << 16))
                if not chunk:
                    raise IOError(f"{info.filename}: connection closed early")
                left -= len(chunk)
                data = inflate.decompress(chunk) if inflate else chunk
                h.update(data)
                out.write(data)
                written += len(data)
                progress(len(data))
            if inflate:
                tail = inflate.flush()
                if tail:
                    h.update(tail)
                    out.write(tail)
                    written += len(tail)
                    progress(len(tail))
            _fsync_file(out)
        if want_size is None or written != int(want_size) or not want_sha or h.hexdigest().lower() != want_sha.lower():
            raise IOError(f"{info.filename}: downloaded file does not match the manifest")

    def fetch_url(self, url, dest, want_sha, want_size, progress):
        """Plain HTTPS GET for content-addressed VPS blobs or DMG files. Strictly verifies size and sha256."""
        if want_size is None or int(want_size) < 0:
            raise IOError(f"{url}: missing expected size for integrity verification")
        if not want_sha or len(str(want_sha).strip()) != 64:
            raise IOError(f"{url}: missing or invalid expected sha256 for integrity verification")
        expected_size = int(want_size)
        expected_sha = str(want_sha).strip().lower()
        req = urllib.request.Request(url, headers=UA)
        h = hashlib.sha256()
        written = 0
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(dest, "wb") as out:
            while True:
                self._check_cancel()
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                h.update(chunk)
                out.write(chunk)
                written += len(chunk)
                progress(len(chunk))
            _fsync_file(out)
        if written != expected_size:
            raise IOError(f"{url}: size mismatch (got {written}, expected {expected_size})")
        if h.hexdigest().lower() != expected_sha:
            raise IOError(f"{url}: sha256 mismatch")

    def find_unmanaged_strays(self, manifest):
        """Detects unmanaged BakersfieldQuake/zz_*.pk3 and loose maps/*.bsp/.lit not in the manifest."""
        managed_lower = {rel.replace("\\", "/").lower() for rel in manifest.get("files", {})}
        strays = []
        bq_game = self.root / "BakersfieldQuake"
        if bq_game.is_dir():
            try:
                for p in bq_game.iterdir():
                    if not p.is_file():
                        continue
                    nl = p.name.lower()
                    if nl.startswith("zz_") and nl.endswith(".pk3"):
                        rel = f"BakersfieldQuake/{p.name}"
                        if rel.lower() not in managed_lower:
                            strays.append(rel)
            except OSError:
                pass
            maps_dir = bq_game / "maps"
            if maps_dir.is_dir():
                try:
                    for p in maps_dir.iterdir():
                        if not p.is_file():
                            continue
                        nl = p.name.lower()
                        if nl.endswith((".bsp", ".lit")):
                            rel = f"BakersfieldQuake/maps/{p.name}"
                            if rel.lower() not in managed_lower:
                                strays.append(rel)
                except OSError:
                    pass
        strays.sort()
        for rel in strays:
            self.log(f"WARNING: unmanaged stray file not in manifest (may override game assets): {rel}")
        return strays

    # ---- planning & verification -------------------------------------------------------------------------------
    def plan_update(self, force=False, verify_progress=None):
        """Fetches manifest and inspects local files without modifying anything on disk."""
        self._zip_entries = None
        state = self.load_state()
        m, source = self.fetch_manifest()
        installed = state["build"] if state else 0
        installed_version = (state or {}).get("version", "") or (f"build {installed}" if installed else "not tracked")

        if m.get("schema") != 1:
            self.log(f"update skipped: manifest schema {m.get('schema')} is newer than this updater")
            return UpdatePlan("up_to_date", m, source, installed, installed_version,
                              total_managed=len(m.get("files", {})), cache=(state or {}).get("cache", {}))

        strays = self.find_unmanaged_strays(m)

        if m["build"] < installed:
            # Never downgrade an intact newer build, but STILL verify local managed files so missing/corrupt
            # assets are never silently ignored when failing over to a lagging mirror.
            orig_cache = dict((state or {}).get("cache", {}))
            cache = dict(orig_cache)
            install_only = set(m.get("install_only", []))
            managed_local = sorted(set((state or {}).get("managed", [])) | set(m.get("files", {})))
            fetch = []
            missing_count = 0
            corrupt_count = 0
            unrepairable = []
            total_check = len(managed_local)
            for idx, rel in enumerate(managed_local, 1):
                self._check_cancel()
                if verify_progress:
                    verify_progress(idx, total_check, rel)
                if rel in install_only and (self.root / rel).exists():
                    continue
                if rel not in (state or {}).get("managed", []):
                    continue
                sha = self.local_sha(rel, cache, force)
                orig_entry = orig_cache.get(rel)
                expected_installed_sha = orig_entry[2] if (orig_entry and len(orig_entry) >= 3) else None
                mf_entry = m["files"].get(rel)
                if sha is None:
                    missing_count += 1
                    if mf_entry and (expected_installed_sha is None or mf_entry["sha256"] == expected_installed_sha):
                        fetch.append(rel)
                    else:
                        unrepairable.append(f"{rel} (missing)")
                elif expected_installed_sha and sha != expected_installed_sha:
                    corrupt_count += 1
                    if mf_entry and mf_entry["sha256"] == expected_installed_sha:
                        fetch.append(rel)
                    else:
                        unrepairable.append(f"{rel} (corrupted/modified)")

            if unrepairable:
                detail = ", ".join(unrepairable[:5])
                if len(unrepairable) > 5:
                    detail += f" (+{len(unrepairable) - 5} more)"
                raise IOError(
                    f"local integrity failure ({detail}) and manifest build {m['build']} is older than "
                    f"installed build {installed}; cannot repair without the latest release"
                )
            if fetch:
                total_bytes = sum(m["files"][p]["size"] for p in fetch)
                self.log(f"fallback manifest build {m['build']} < installed {installed}: repairing {len(fetch)} missing/corrupt unchanged file(s)")
                return UpdatePlan(
                    kind="repair",
                    manifest=m,
                    source=source,
                    installed_build=installed,
                    installed_version=installed_version,
                    fetch=fetch,
                    delete=[],
                    total_bytes=total_bytes,
                    missing_count=missing_count,
                    corrupt_count=corrupt_count,
                    total_managed=len(m.get("files", {})),
                    notes=_summarize_files(fetch, [], "repair"),
                    cache=cache,
                    strays=strays,
                    preserve_build=installed,
                )
            self.log(f"update skipped: release build {m['build']} is older than installed {installed} (local files verified intact)")
            return UpdatePlan("up_to_date", m, source, installed, installed_version,
                              total_managed=len(m.get("files", {})), cache=cache, strays=strays)

        # macOS app bundle check: new engine/launcher requires downloading a new signed DMG.
        if self.bundle_mac_inputs and self.bundle_mac_inputs.is_file():
            local_inputs = self.bundle_mac_inputs.read_text("utf-8").strip()
            remote_inputs = (m.get("mac_inputs") or "").strip()
            if local_inputs and remote_inputs and local_inputs != remote_inputs and (m.get("dmg_url") or m.get("dmg_vps_url")):
                return UpdatePlan(
                    kind="dmg",
                    manifest=m,
                    source=source,
                    installed_build=installed,
                    installed_version=installed_version,
                    total_bytes=int(m.get("dmg_size") or 0),
                    total_managed=len(m.get("files", {})),
                    notes=(m.get("notes") or "").strip() or "Includes an updated engine or app launcher.",
                    cache=(state or {}).get("cache", {}),
                    dmg_url=m.get("dmg_url", ""),
                    dmg_vps_url=m.get("dmg_vps_url", ""),
                    dmg_size=int(m.get("dmg_size") or 0),
                    dmg_sha256=m.get("dmg_sha256", ""),
                    strays=strays,
                )

        # Always check every managed file on disk (even if m["build"] == installed) so missing/damaged assets repair.
        cache = dict((state or {}).get("cache", {}))
        install_only = set(m.get("install_only", []))
        fetch = []
        missing_count = 0
        corrupt_count = 0
        items = sorted(m["files"].items())
        total_managed = len(items)
        for idx, (rel, f) in enumerate(items, 1):
            self._check_cancel()
            if verify_progress:
                verify_progress(idx, total_managed, rel)
            if rel in install_only and (self.root / rel).exists():
                continue
            sha = self.local_sha(rel, cache, force)
            if sha != f["sha256"]:
                fetch.append(rel)
                if sha is None:
                    missing_count += 1
                else:
                    corrupt_count += 1

        previous = set((state or {}).get("managed", []))
        delete = sorted(p for p in previous - set(m["files"]) if (self.root / p).exists())
        total_bytes = sum(m["files"][p]["size"] for p in fetch)

        if not fetch and not delete:
            kind = "up_to_date"
            # Refresh state cleanly if first run or force-rehash validated everything.
            if not state or force or state.get("build") != m["build"] or state.get("updater") != VERSION:
                self._commit_state(m, cache)
        elif state and installed == m["build"]:
            kind = "repair"
        else:
            kind = "update"

        notes = (m.get("notes") or "").strip()
        if kind == "repair":
            notes = _summarize_files(fetch, delete, "repair")
        elif not notes and kind == "update":
            notes = _summarize_files(fetch, delete, "update")

        return UpdatePlan(
            kind=kind,
            manifest=m,
            source=source,
            installed_build=installed,
            installed_version=installed_version,
            fetch=fetch,
            delete=delete,
            total_bytes=total_bytes,
            missing_count=missing_count,
            corrupt_count=corrupt_count,
            total_managed=total_managed,
            notes=notes,
            cache=cache,
            strays=strays,
        )

    def _commit_state(self, m, cache, preserve_build=0):
        if preserve_build and preserve_build > m["build"]:
            prev = self.load_state() or {}
            merged_cache = dict(prev.get("cache", {}))
            merged_cache.update({p: cache[p] for p in cache if p in prev.get("managed", []) or p in m["files"]})
            self.save_state({
                "build": preserve_build,
                "version": prev.get("version", ""),
                "managed": prev.get("managed", sorted(m["files"])),
                "cache": merged_cache,
                "updater": VERSION,
            })
            return
        self.save_state({
            "build": m["build"],
            "version": m.get("version", ""),
            "managed": sorted(m["files"]),
            "cache": {p: cache[p] for p in m["files"] if p in cache},
            "updater": VERSION,
        })
        # Clean up legacy v1 tools/bq-update.exe after migrating to root Update.exe (v1 couldn't unlink itself while running).
        if os.name == "nt" and "tools/bq-update.exe" not in m["files"]:
            legacy = self.root / "tools" / "bq-update.exe"
            if legacy.is_file():
                try:
                    legacy.unlink()
                except OSError:
                    pass

    # ---- apply -------------------------------------------------------------------------------------------------
    def _download_single(self, rel, dest, f, completed_bytes, progress_cb, prefer_vps, vps_base):
        want_sha, want_size = f["sha256"], f["size"]
        m = self.manifest
        has_github = bool(m.get("zip"))
        has_vps = bool(vps_base)

        sources = []
        zip_label = "GitHub" if _is_github_url(m.get("zip", "")) else "Primary"
        if prefer_vps:
            if has_vps:
                sources.append(("VPS", 2))
            if has_github:
                sources.append((f"{zip_label} fallback", 2))
        else:
            if has_github:
                sources.append((zip_label, 2))
            if has_vps:
                sources.append(("VPS fallback", 2))

        if not sources:
            raise IOError(f"no download source available for {rel}")

        last_err = None
        for source_label, attempts in sources:
            for attempt in range(attempts):
                self._check_cancel()
                attempt_bytes = [0]

                def on_chunk(n, label=source_label):
                    attempt_bytes[0] += n
                    cur = completed_bytes + min(attempt_bytes[0], want_size)
                    progress_cb(cur, rel, label)

                try:
                    if "VPS" in source_label:
                        url = f"{vps_base}/files/{want_sha}"
                        self.fetch_url(url, dest, want_sha, want_size, on_chunk)
                    else:
                        entries = self._ensure_zip_entries()
                        if rel not in entries:
                            raise IOError(f"{rel} is in the manifest but not in the release zip")
                        self.fetch_entry(entries[rel], dest, want_sha, want_size, on_chunk)
                    return source_label
                except UpdateCancelled:
                    raise
                except Exception as e:
                    last_err = e
                    self.log(f"{source_label} attempt {attempt + 1} failed for {rel}: {e}")
                    if "VPS" not in source_label:
                        # Force re-resolving zip on next try in case signed URL or range failed.
                        self._zip_entries = None
        raise IOError(f"failed to download {rel}: {last_err}") from last_err

    def apply_plan(self, plan, progress_cb=None, status_cb=None):
        """Downloads and atomically applies a plan. Returns True if changes were made."""
        if plan.kind == "dmg":
            return self.download_and_open_dmg(plan, progress_cb=progress_cb, status_cb=status_cb)

        m = plan.manifest
        self.manifest = m
        self.manifest_source = plan.source
        fetch, delete, cache = plan.fetch, plan.delete, plan.cache
        changed = bool(fetch or delete)
        if not changed:
            self._commit_state(m, cache)
            return False

        staging, backup = self.bq / "staging", self.bq / "backup"
        for d in (staging, backup):
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True, exist_ok=True)

        try:
            if fetch:
                completed_bytes = 0
                vps_base = self.resolve_vps_base(m)
                prefer_vps = (plan.source == "VPS")

                def report(done_bytes, rel, src_label):
                    if progress_cb:
                        progress_cb(done_bytes, plan.total_bytes, rel, src_label)

                for rel in fetch:
                    self._check_cancel()
                    dest = staging / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    f = m["files"][rel]
                    if status_cb:
                        status_cb(f"Downloading {Path(rel).name}...")
                    self._download_single(rel, dest, f, completed_bytes, report, prefer_vps, vps_base)
                    completed_bytes += f["size"]
                    if progress_cb:
                        progress_cb(completed_bytes, plan.total_bytes, rel, plan.source)

            if status_cb:
                status_cb("Installing & verifying files...")
            exec_set = set(m.get("exec", []))
            moved, rel = [], "?"
            try:
                for rel in fetch:
                    target = self.root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        (backup / rel).parent.mkdir(parents=True, exist_ok=True)
                        replace_running(target, backup / rel)
                    moved.append(rel)
                    os.replace(staging / rel, target)
                    f_info = m["files"][rel]
                    want_size = int(f_info["size"])
                    want_sha = str(f_info["sha256"]).lower()
                    st = target.stat()
                    if st.st_size != want_size:
                        raise IOError(
                            f"post-replace size mismatch for {rel} (got {st.st_size}, expected {want_size})"
                        )
                    if rel.lower().endswith(CRITICAL_VERIFY_SUFFIXES) or rel in exec_set:
                        if status_cb:
                            status_cb(f"Verifying {Path(rel).name}...")
                        actual_size, actual_sha = hash_file(target, self._check_cancel)
                        if actual_size != want_size or actual_sha.lower() != want_sha:
                            raise IOError(
                                f"post-replace sha256 mismatch for {rel} (got {actual_sha[:12]}, expected {want_sha[:12]})"
                            )
                        st = target.stat()
                        cache[rel] = [st.st_size, st.st_mtime_ns, actual_sha]
                    else:
                        cache[rel] = [st.st_size, st.st_mtime_ns, want_sha]
            except (OSError, UpdateCancelled) as e:
                failed = rel
                for r_rel in reversed(moved):
                    try:
                        if (backup / r_rel).exists():
                            os.replace(backup / r_rel, self.root / r_rel)
                        else:
                            (self.root / r_rel).unlink()
                    except OSError as rb_err:
                        self.log(f"rollback failed for {r_rel}: {rb_err}")
                    cache.pop(r_rel, None)
                if isinstance(e, UpdateCancelled):
                    self.log(f"update cancelled during replace/verify of {failed}; rolled back cleanly")
                    raise
                raise IOError(f"could not replace/verify {failed} ({e}); is the game or a server running "
                              f"from this folder? The update was rolled back.") from e

            if os.name != "nt":
                for rel in m.get("exec", []):
                    p = self.root / rel
                    if p.exists() and not os.access(p, os.X_OK):
                        p.chmod(p.stat().st_mode | 0o111)

            for rel in delete:
                try:
                    (self.root / rel).unlink()
                except OSError as e:
                    self.log(f"could not remove {rel}: {e}")

            self._commit_state(m, cache, preserve_build=plan.preserve_build)
            self.log(f"updated to build {plan.preserve_build or m['build']} ({len(fetch)} fetched, {len(delete)} removed)")
            return True
        finally:
            shutil.rmtree(staging, ignore_errors=True)
            shutil.rmtree(backup, ignore_errors=True)

    def download_and_open_dmg(self, plan, progress_cb=None, status_cb=None):
        dl_dir = self.downloads_dir or default_downloads_dir()
        dl_dir.mkdir(parents=True, exist_ok=True)
        dest = dl_dir / "BAKOQUAKE-macos-arm64.dmg"
        part = dl_dir / "BAKOQUAKE-macos-arm64.dmg.part"

        urls = []
        if plan.source == "VPS":
            if plan.dmg_vps_url:
                urls.append(("VPS", plan.dmg_vps_url))
            if plan.dmg_url:
                urls.append(("GitHub fallback", plan.dmg_url))
        else:
            if plan.dmg_url:
                urls.append(("GitHub", plan.dmg_url))
            if plan.dmg_vps_url:
                urls.append(("VPS fallback", plan.dmg_vps_url))

        if not urls:
            raise IOError("manifest does not specify a DMG download URL")

        last_err = None
        for label, url in urls:
            written = [0]

            def on_chunk(n, src=label):
                written[0] += n
                if progress_cb:
                    progress_cb(written[0], plan.dmg_size or max(written[0], 1),
                                "BAKOQUAKE-macos-arm64.dmg", src)

            try:
                if status_cb:
                    status_cb(f"Downloading macOS app ({label})...")
                self.fetch_url(url, part, plan.dmg_sha256, plan.dmg_size, on_chunk)
                os.replace(part, dest)
                if status_cb:
                    status_cb("Opening DMG...")
                self.open_dmg(dest)
                self.log(f"downloaded and opened DMG {dest} from {label}")
                return dest
            except UpdateCancelled:
                part.unlink(missing_ok=True)
                raise
            except Exception as e:
                part.unlink(missing_ok=True)
                last_err = e
                self.log(f"DMG download failed from {label}: {e}")
        raise IOError(f"failed to download macOS DMG: {last_err}") from last_err

    # ---- headless convenience entry point ----------------------------------------------------------------------
    def run(self, check=False, force=False, launch=False, standalone=False, ui=None):
        if ui is None:
            ui = CliUpdateUI(interactive=False, quiet=launch)
        return ui.run_flow(self, check=check, force=force, launch=launch, standalone=standalone)


def replace_running(target, backup):
    """Moves target to backup. Windows allows renaming a running exe, which lets the updater replace itself."""
    os.replace(target, backup)


# ---- UI implementations ------------------------------------------------------------------------------------
class UpdateUI:
    def run_flow(self, updater, check=False, force=False, launch=False, standalone=False):
        raise NotImplementedError


class CliUpdateUI(UpdateUI):
    """Terminal / headless UI with speed and ETA reporting."""

    def __init__(self, interactive=False, quiet=False):
        self.interactive = interactive
        self.quiet = quiet

    def run_flow(self, updater, check=False, force=False, launch=False, standalone=False):
        try:
            plan = updater.plan_update(force=force)
        except OfflineError as e:
            if standalone:
                print(f"Could not reach update servers ({e}).")
                return 0
            updater.log(f"offline: update check skipped ({e})")
            return 0

        if check:
            if plan.kind == "dmg":
                print(f"app update required: build {plan.installed_build} -> {plan.manifest['build']} "
                      f"(DMG {fmt(plan.dmg_size)})")
                return 10
            if plan.needs_action:
                print(f"build {plan.installed_build} installed, build {plan.manifest['build']} available: "
                      f"{len(plan.fetch)} files ({plan.total_bytes / 1e6:.1f} MB) to download, "
                      f"{len(plan.delete)} to remove")
                return 10
            if not self.quiet:
                print(f"up to date (build {plan.manifest['build']}, {plan.total_managed} files verified)")
            return 0

        if not plan.needs_action:
            if plan.strays and not self.quiet:
                print(f"Warning: {len(plan.strays)} unmanaged stray file(s) not in manifest: "
                      f"{', '.join(plan.strays[:5])}")
            if standalone or not self.quiet:
                print(f"BAKOQUAKE is up to date ({plan.manifest.get('version') or plan.manifest['build']} — "
                      f"{plan.total_managed} files verified).")
            return 0

        if self.interactive and sys.stdin and sys.stdin.isatty():
            if plan.kind == "dmg":
                print(f"\nNew BAKOQUAKE macOS App required ({fmt(plan.dmg_size)} via {plan.source}).")
                if plan.notes:
                    print(f"Notes: {plan.notes}")
                ans = input("Download & open DMG now? [Y/n]: ").strip().lower()
            else:
                verb = "Repair" if plan.kind == "repair" else "Update"
                print(f"\nBAKOQUAKE {verb}: {plan.installed_version} -> "
                      f"{plan.manifest.get('version') or plan.manifest['build']}")
                print(f"  {len(plan.fetch)} files ({fmt(plan.total_bytes)}) via {plan.source}")
                if plan.notes:
                    print(f"  {plan.notes}")
                ans = input(f"{verb} now? [Y/n]: ").strip().lower()
            if ans in ("n", "no"):
                return 4

        if plan.kind == "dmg":
            if not self.interactive and launch:
                updater.log("macOS app update required (no interactive UI)")
                return 4
            tracker = RateTracker()
            tracker.start(plan.dmg_size)

            def on_dmg_prog(done, total, _name, src):
                tracker.update(done)
                pct = (done * 100 // total) if total else 0
                print(f"\r  {pct:3d}%  {fmt(done)} / {fmt(total)}  {fmt_speed(tracker.current_speed())}  "
                      f"{fmt_eta(tracker.eta_seconds(max(0, total - done)))} [{src}]   ", end="", flush=True)

            try:
                dest = updater.download_and_open_dmg(plan, progress_cb=on_dmg_prog)
                print(f"\nOpened {dest}. Drag BAKOQUAKE and Update BAKOQUAKE into Applications.")
            except Exception as e:
                print(f"\nDMG update failed: {e}", flush=True)
                updater.log(f"DMG update failed: {e}")
            return 4

        if not self.quiet or launch or standalone:
            verb = "Repairing" if plan.kind == "repair" else "Updating"
            print(f"{verb} BAKOQUAKE build {plan.installed_build} to {plan.manifest['build']}: "
                  f"{len(plan.fetch)} files, {fmt(plan.total_bytes)} ({plan.source})", flush=True)

        tracker = RateTracker()
        tracker.start(plan.total_bytes)

        def on_prog(done, total, _rel, src):
            tracker.update(done)
            pct = (done * 100 // total) if total else 100
            rem = max(0, total - done)
            print(f"\r  {pct:3d}%  {fmt(done)} / {fmt(total)}  {fmt_speed(tracker.current_speed())}  "
                  f"{fmt_eta(tracker.eta_seconds(rem))} [{src}]   ", end="", flush=True)

        try:
            changed = updater.apply_plan(plan, progress_cb=on_prog)
            print("\n  done.", flush=True)
            if standalone:
                return 0
            return 3 if changed else 0
        except UpdateCancelled:
            print("\nUpdate cancelled.", flush=True)
            return 4
        except Exception as e:
            print(f"\nUpdate failed: {e}", flush=True)
            updater.log(f"update failed: {e}")
            return 4


class ZenityUpdateUI(UpdateUI):
    """Linux fallback GUI via zenity when python3-tk is unavailable and a display server is present."""

    def __init__(self, zenity_bin):
        self.zenity = zenity_bin

    def _ask(self, title, text, ok_label="Update", cancel_label="Exit"):
        res = subprocess.run([
            self.zenity, "--question", "--title", title, "--text", text,
            "--ok-label", ok_label, "--cancel-label", cancel_label, "--width", "420"
        ])
        return res.returncode == 0

    def _msg(self, kind, title, text):
        subprocess.run([self.zenity, f"--{kind}", "--title", title, "--text", text, "--width", "420"])

    def run_flow(self, updater, check=False, force=False, launch=False, standalone=False):
        try:
            plan = updater.plan_update(force=force)
        except OfflineError as e:
            if standalone:
                self._msg("warning", "BAKOQUAKE Updater", f"Could not reach update servers.\n\n{e}")
                return 0
            updater.log(f"offline: update check skipped ({e})")
            return 0

        if not plan.needs_action:
            if standalone:
                ver = plan.manifest.get("version") or f"build {plan.manifest['build']}"
                self._msg("info", "BAKOQUAKE Updater",
                          f"BAKOQUAKE is up to date ({ver}).\nAll {plan.total_managed} files verified.")
            return 0

        ver_new = plan.manifest.get("version") or f"build {plan.manifest['build']}"
        if plan.kind == "repair":
            body = (f"Missing or damaged game files detected ({len(plan.fetch)} files, {fmt(plan.total_bytes)}).\n"
                    f"Source: {plan.source}")
            title = "Repair BAKOQUAKE"
            ok = "Repair"
        else:
            body = (f"A new version of BAKOQUAKE is available.\n\n"
                    f"Installed: {plan.installed_version}\nLatest: {ver_new}\n"
                    f"Download: {len(plan.fetch)} files ({fmt(plan.total_bytes)}) via {plan.source}")
            if plan.notes:
                body += f"\n\n{plan.notes}"
            title = "BAKOQUAKE Update Available"
            ok = "Update"

        cancel = "Close" if standalone else "Exit"
        if not self._ask(title, body, ok_label=ok, cancel_label=cancel):
            return 0 if standalone else 4

        proc = subprocess.Popen(
            [self.zenity, "--progress", "--title", "BAKOQUAKE Updater",
             "--text", "Starting download...", "--percentage", "0", "--auto-close", "--width", "440"],
            stdin=subprocess.PIPE, text=True
        )
        tracker = RateTracker()
        tracker.start(plan.total_bytes)
        last_ui = [0.0]

        def on_prog(done, total, rel, src):
            if proc.poll() is not None:
                updater.cancel_event.set()
                return
            tracker.update(done)
            now = time.monotonic()
            if now - last_ui[0] < 0.1 and done < total:
                return
            last_ui[0] = now
            pct = (done * 100 // total) if total else 100
            rem = max(0, total - done)
            line = (f"# {Path(rel).name} ({src})\n"
                    f"# {fmt(done)} / {fmt(total)}  •  {fmt_speed(tracker.current_speed())}  •  "
                    f"{fmt_eta(tracker.eta_seconds(rem))}\n{pct}\n")
            try:
                proc.stdin.write(line)
                proc.stdin.flush()
            except OSError:
                updater.cancel_event.set()

        try:
            changed = updater.apply_plan(plan, progress_cb=on_prog)
            try:
                if proc.stdin:
                    proc.stdin.write("100\n")
                    proc.stdin.close()
            except OSError:
                pass
            proc.wait(timeout=2)
            if standalone:
                self._msg("info", "BAKOQUAKE Updater", f"Updated to {ver_new}!")
                return 0
            return 3 if changed else 0
        except UpdateCancelled:
            proc.terminate()
            return 0 if standalone else 4
        except Exception as e:
            proc.terminate()
            updater.log(f"update failed: {e}")
            self._msg("error", "BAKOQUAKE Update Failed", f"Update failed:\n\n{e}")
            return 0 if standalone else 4


class TkUpdateUI(UpdateUI):
    """Dark-theme tkinter GUI with 1.5s delayed show on --launch, live speed/ETA, and Verify & Repair."""

    BG = "#16161a"
    CARD = "#1f2026"
    SUNKEN = "#121318"
    FG = "#f0f0f4"
    MUTED = "#9a9aa6"
    ACCENT = "#e8ae12"
    ACCENT_HOVER = "#f4be2a"
    ACCENT_TEXT = "#141418"
    BTN_SEC = "#2b2d36"
    BTN_SEC_HOVER = "#373a46"
    GREEN = "#4ade80"
    RED = "#f87171"
    AMBER = "#f59e0b"

    def __init__(self):
        import tkinter as tk
        from tkinter import ttk
        self.tk = tk
        self.ttk = ttk

    def run_flow(self, updater, check=False, force=False, launch=False, standalone=False):
        tk = self.tk
        ttk = self.ttk

        root = tk.Tk()
        root.title("BAKOQUAKE Updater")
        root.configure(bg=self.BG)
        root.resizable(False, False)
        w, h = 490, 330
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self._load_icon(root, updater.root)

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("BQ.Horizontal.TProgressbar",
                        troughcolor="#2a2b34", background=self.ACCENT,
                        bordercolor="#2a2b34", lightcolor=self.ACCENT, darkcolor=self.ACCENT,
                        thickness=14)

        if launch and not standalone:
            root.withdraw()

        container = tk.Frame(root, bg=self.BG, padx=20, pady=18)
        container.pack(fill="both", expand=True)
        card = tk.Frame(container, bg=self.CARD, highlightbackground="#2d2f3a", highlightthickness=1, padx=20, pady=18)
        card.pack(fill="both", expand=True)

        state = {
            "exit_code": 0 if standalone else 4,
            "shown": not (launch and not standalone),
            "checking": True,
            "plan": None,
            "downloading": False,
        }
        q = queue.Queue()
        tracker = RateTracker()

        def reveal():
            if not state["shown"]:
                state["shown"] = True
                root.deiconify()
            root.lift()
            if sys.platform == "darwin" or os.name == "nt":
                root.attributes("-topmost", True)
                root.after(150, lambda: root.attributes("-topmost", False))

        def clear_card():
            for child in card.winfo_children():
                child.destroy()

        def make_button(parent, text, cmd, primary=False):
            bg = self.ACCENT if primary else self.BTN_SEC
            fg = self.ACCENT_TEXT if primary else self.FG
            hv = self.ACCENT_HOVER if primary else self.BTN_SEC_HOVER
            btn = tk.Button(
                parent, text=text, command=cmd, bg=bg, fg=fg,
                activebackground=hv, activeforeground=fg,
                relief="flat", bd=0, padx=16, pady=7,
                font=("Segoe UI" if os.name == "nt" else "Helvetica", 10, "bold" if primary else "normal"),
                cursor="hand2"
            )
            btn.bind("<Enter>", lambda _e: btn.config(bg=hv))
            btn.bind("<Leave>", lambda _e: btn.config(bg=bg))
            return btn

        def finish(code):
            state["exit_code"] = code
            updater.cancel_event.set()
            try:
                root.destroy()
            except tk.TclError:
                pass

        def on_close():
            if state["downloading"]:
                updater.cancel_event.set()
            finish(0 if standalone else 4)

        root.protocol("WM_DELETE_WINDOW", on_close)

        def show_checking(title_text="Checking for updates...", sub_text="Connecting to GitHub / VPS..."):
            clear_card()
            tk.Label(card, text="BAKOQUAKE", bg=self.CARD, fg=self.ACCENT,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 10, "bold")).pack(anchor="w")
            lbl_title = tk.Label(card, text=title_text, bg=self.CARD, fg=self.FG,
                                 font=("Segoe UI" if os.name == "nt" else "Helvetica", 14, "bold"))
            lbl_title.pack(anchor="w", pady=(6, 4))
            lbl_sub = tk.Label(card, text=sub_text, bg=self.CARD, fg=self.MUTED,
                               font=("Segoe UI" if os.name == "nt" else "Helvetica", 9))
            lbl_sub.pack(anchor="w", pady=(0, 18))
            pb = ttk.Progressbar(card, style="BQ.Horizontal.TProgressbar", mode="indeterminate", length=410)
            pb.pack(fill="x", pady=(4, 18))
            pb.start(14)
            btn_row = tk.Frame(card, bg=self.CARD)
            btn_row.pack(side="bottom", fill="x")
            make_button(btn_row, "Exit" if launch and not standalone else "Cancel", on_close).pack(side="right")
            return lbl_title, lbl_sub, pb

        def delayed_reveal_checking():
            if state["checking"]:
                reveal()

        lbl_chk_title, lbl_chk_sub, _ = show_checking()
        if launch and not standalone:
            root.after(1500, delayed_reveal_checking)

        def start_check(rehash=False):
            state["checking"] = True
            updater.cancel_event.clear()
            nonlocal lbl_chk_title, lbl_chk_sub
            title = "Verifying all game files..." if rehash else "Checking for updates..."
            sub = "Checking SHA-256 hashes..." if rehash else "Connecting to GitHub / VPS..."
            lbl_chk_title, lbl_chk_sub, _ = show_checking(title, sub)

            def worker():
                def on_verify(idx, total, rel):
                    if rehash:
                        q.put(("verify_prog", idx, total, rel))
                try:
                    plan = updater.plan_update(force=rehash, verify_progress=on_verify)
                    q.put(("plan_ok", plan, rehash))
                except OfflineError as e:
                    q.put(("offline", str(e)))
                except UpdateCancelled:
                    pass
                except Exception as e:
                    q.put(("error", str(e)))

            threading.Thread(target=worker, daemon=True).start()

        def show_up_to_date(plan):
            clear_card()
            reveal()
            ver = plan.manifest.get("version") or f"build {plan.manifest['build']}"
            tk.Label(card, text="UP TO DATE", bg=self.CARD, fg=self.GREEN,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 10, "bold")).pack(anchor="w")
            tk.Label(card, text="BAKOQUAKE is up to date", bg=self.CARD, fg=self.FG,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 14, "bold")).pack(anchor="w", pady=(6, 4))
            tk.Label(card, text=f"Version: {ver}  •  Build {plan.manifest['build']}",
                     bg=self.CARD, fg=self.MUTED,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 10)).pack(anchor="w")
            tk.Label(card, text=f"All {plan.total_managed} game files verified (via {plan.source}).",
                     bg=self.CARD, fg=self.MUTED,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 9)).pack(anchor="w", pady=(8, 0))
            btn_row = tk.Frame(card, bg=self.CARD)
            btn_row.pack(side="bottom", fill="x", pady=(14, 0))
            make_button(btn_row, "Verify & Repair All Files", lambda: start_check(rehash=True)).pack(side="left")
            close_btn = make_button(btn_row, "Close", lambda: finish(0), primary=True)
            close_btn.pack(side="right")
            root.bind("<Return>", lambda _e: finish(0))
            root.bind("<Escape>", lambda _e: finish(0))

        def show_offline(err_text):
            clear_card()
            reveal()
            tk.Label(card, text="OFFLINE", bg=self.CARD, fg=self.AMBER,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 10, "bold")).pack(anchor="w")
            tk.Label(card, text="Could not reach update servers", bg=self.CARD, fg=self.FG,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 14, "bold")).pack(anchor="w", pady=(6, 4))
            tk.Label(card, text="Tried GitHub Releases and the VPS fallback. Check your internet connection.",
                     bg=self.CARD, fg=self.MUTED, wraplength=410, justify="left",
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 9)).pack(anchor="w", pady=(2, 8))
            detail = tk.Label(card, text=err_text[:180], bg=self.SUNKEN, fg=self.MUTED,
                              wraplength=400, justify="left", padx=8, pady=6,
                              font=("Consolas" if os.name == "nt" else "Menlo", 8))
            detail.pack(fill="x", pady=(4, 8))
            btn_row = tk.Frame(card, bg=self.CARD)
            btn_row.pack(side="bottom", fill="x")
            make_button(btn_row, "Retry", lambda: start_check(rehash=False), primary=True).pack(side="left")
            make_button(btn_row, "Close", lambda: finish(0)).pack(side="right")

        def show_prompt(plan):
            clear_card()
            reveal()
            state["plan"] = plan
            ver_new = plan.manifest.get("version") or f"build {plan.manifest['build']}"
            if plan.kind == "dmg":
                badge, badge_col = "APP UPDATE REQUIRED", self.ACCENT
                title = "New BAKOQUAKE App Required"
                ver_line = f"Installed: {plan.installed_version}  →  Latest: {ver_new}"
                stat_line = f"macOS App DMG  •  {fmt(plan.dmg_size)}  (via {plan.source})"
                ok_text = "Download & Open (.dmg)"
            elif plan.kind == "repair":
                badge, badge_col = "REPAIR NEEDED", self.AMBER
                title = "Missing or Damaged Files Detected"
                ver_line = f"Current release: {ver_new}  •  Build {plan.manifest['build']}"
                stat_line = f"{len(plan.fetch)} file(s) to repair  •  {fmt(plan.total_bytes)}  (via {plan.source})"
                ok_text = "Repair"
            else:
                badge, badge_col = "UPDATE AVAILABLE", self.ACCENT
                title = "A new BAKOQUAKE update is ready"
                ver_line = f"{plan.installed_version}  →  {ver_new}"
                extra = f", {len(plan.delete)} removed" if plan.delete else ""
                stat_line = f"{len(plan.fetch)} file(s){extra}  •  {fmt(plan.total_bytes)}  (via {plan.source})"
                ok_text = "Update"

            tk.Label(card, text=badge, bg=self.CARD, fg=badge_col,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 9, "bold")).pack(anchor="w")
            tk.Label(card, text=title, bg=self.CARD, fg=self.FG,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 13, "bold")).pack(anchor="w", pady=(4, 2))
            tk.Label(card, text=ver_line, bg=self.CARD, fg=self.FG,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 9)).pack(anchor="w")
            tk.Label(card, text=stat_line, bg=self.CARD, fg=self.MUTED,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 9)).pack(anchor="w", pady=(2, 8))

            notes_box = tk.Text(card, height=4, bg=self.SUNKEN, fg=self.FG, relief="flat", bd=0,
                                padx=10, pady=8, wrap="word",
                                font=("Segoe UI" if os.name == "nt" else "Helvetica", 9))
            notes_box.insert("1.0", plan.notes or "Ready to update.")
            notes_box.config(state="disabled")
            notes_box.pack(fill="both", expand=True, pady=(0, 12))

            btn_row = tk.Frame(card, bg=self.CARD)
            btn_row.pack(side="bottom", fill="x")
            cancel_lbl = "Cancel" if standalone else "Exit"
            cancel_code = 0 if standalone else 4
            make_button(btn_row, cancel_lbl, lambda: finish(cancel_code)).pack(side="right")
            make_button(btn_row, ok_text, lambda: start_download(plan), primary=True).pack(side="right", padx=(0, 10))
            root.bind("<Return>", lambda _e: start_download(plan))
            root.bind("<Escape>", lambda _e: finish(cancel_code))

        def start_download(plan):
            clear_card()
            root.unbind("<Return>")
            root.unbind("<Escape>")
            state["downloading"] = True
            updater.cancel_event.clear()
            total = plan.dmg_size if plan.kind == "dmg" else plan.total_bytes
            tracker.start(total)

            hdr = ("Downloading macOS App..." if plan.kind == "dmg"
                   else "Repairing Files..." if plan.kind == "repair" else "Updating BAKOQUAKE...")
            tk.Label(card, text="DOWNLOADING", bg=self.CARD, fg=self.ACCENT,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 9, "bold")).pack(anchor="w")
            tk.Label(card, text=hdr, bg=self.CARD, fg=self.FG,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 13, "bold")).pack(anchor="w", pady=(4, 12))

            pb = ttk.Progressbar(card, style="BQ.Horizontal.TProgressbar", mode="determinate", maximum=100, length=410)
            pb.pack(fill="x", pady=(0, 8))

            metrics = tk.Frame(card, bg=self.CARD)
            metrics.pack(fill="x", pady=(0, 10))
            lbl_left = tk.Label(metrics, text=f"0%  •  0 KB / {fmt(total)}", bg=self.CARD, fg=self.FG,
                                font=("Segoe UI" if os.name == "nt" else "Helvetica", 9, "bold"))
            lbl_left.pack(side="left")
            lbl_right = tk.Label(metrics, text="calculating...  •  estimating...", bg=self.CARD, fg=self.ACCENT,
                                 font=("Segoe UI" if os.name == "nt" else "Helvetica", 9))
            lbl_right.pack(side="right")

            lbl_status = tk.Label(card, text="Connecting...", bg=self.CARD, fg=self.MUTED,
                                  font=("Segoe UI" if os.name == "nt" else "Helvetica", 9))
            lbl_status.pack(anchor="w")

            btn_row = tk.Frame(card, bg=self.CARD)
            btn_row.pack(side="bottom", fill="x", pady=(14, 0))
            make_button(btn_row, "Cancel", lambda: updater.cancel_event.set()).pack(side="right")

            state["prog_widgets"] = (pb, lbl_left, lbl_right, lbl_status)

            def worker():
                last_emit = [0.0]

                def on_prog(done, tot, rel, src_label):
                    now = time.monotonic()
                    if now - last_emit[0] < 0.05 and done < tot:
                        return
                    last_emit[0] = now
                    q.put(("dl_prog", done, tot, rel, src_label))

                def on_status(msg):
                    q.put(("dl_status", msg))

                try:
                    res = updater.apply_plan(plan, progress_cb=on_prog, status_cb=on_status)
                    q.put(("dl_done", plan, res))
                except UpdateCancelled:
                    q.put(("dl_cancelled",))
                except Exception as e:
                    q.put(("dl_error", plan, str(e)))

            threading.Thread(target=worker, daemon=True).start()

        def show_done(plan):
            clear_card()
            ver = plan.manifest.get("version") or f"build {plan.manifest['build']}"
            if plan.kind == "dmg":
                tk.Label(card, text="INSTALL APP", bg=self.CARD, fg=self.ACCENT,
                         font=("Segoe UI" if os.name == "nt" else "Helvetica", 10, "bold")).pack(anchor="w")
                tk.Label(card, text="BAKOQUAKE DMG Opened", bg=self.CARD, fg=self.FG,
                         font=("Segoe UI" if os.name == "nt" else "Helvetica", 14, "bold")).pack(anchor="w", pady=(6, 6))
                tk.Label(card, text="Drag both BAKOQUAKE and Update BAKOQUAKE into Applications to finish updating, then launch again.",
                         bg=self.CARD, fg=self.MUTED, wraplength=410, justify="left",
                         font=("Segoe UI" if os.name == "nt" else "Helvetica", 10)).pack(anchor="w")
                btn_row = tk.Frame(card, bg=self.CARD)
                btn_row.pack(side="bottom", fill="x")
                make_button(btn_row, "OK", lambda: finish(4), primary=True).pack(side="right")
                root.bind("<Return>", lambda _e: finish(4))
                return

            tk.Label(card, text="COMPLETE", bg=self.CARD, fg=self.GREEN,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 10, "bold")).pack(anchor="w")
            tk.Label(card, text=f"Updated to {ver}", bg=self.CARD, fg=self.FG,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 14, "bold")).pack(anchor="w", pady=(6, 6))
            tk.Label(card, text=f"All {plan.total_managed} game files are verified and ready.",
                     bg=self.CARD, fg=self.MUTED,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 10)).pack(anchor="w")
            btn_row = tk.Frame(card, bg=self.CARD)
            btn_row.pack(side="bottom", fill="x")
            make_button(btn_row, "Close", lambda: finish(0), primary=True).pack(side="right")
            root.bind("<Return>", lambda _e: finish(0))

        def show_error(err_text, retry_plan=None):
            clear_card()
            reveal()
            tk.Label(card, text="UPDATE FAILED", bg=self.CARD, fg=self.RED,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 10, "bold")).pack(anchor="w")
            tk.Label(card, text="Could not complete update", bg=self.CARD, fg=self.FG,
                     font=("Segoe UI" if os.name == "nt" else "Helvetica", 13, "bold")).pack(anchor="w", pady=(6, 6))
            box = tk.Text(card, height=4, bg=self.SUNKEN, fg=self.FG, relief="flat", bd=0,
                          padx=10, pady=8, wrap="word",
                          font=("Segoe UI" if os.name == "nt" else "Helvetica", 9))
            box.insert("1.0", f"{err_text}\n\nLog: {updater.bq / 'update.log'}")
            box.config(state="disabled")
            box.pack(fill="both", expand=True, pady=(0, 12))
            btn_row = tk.Frame(card, bg=self.CARD)
            btn_row.pack(side="bottom", fill="x")
            retry_cmd = (lambda: start_download(retry_plan)) if retry_plan else (lambda: start_check(rehash=False))
            make_button(btn_row, "Retry", retry_cmd, primary=True).pack(side="left")
            exit_code = 0 if standalone else 4
            make_button(btn_row, "Close" if standalone else "Exit", lambda: finish(exit_code)).pack(side="right")

        def poll_queue():
            try:
                while True:
                    ev = q.get_nowait()
                    kind = ev[0]
                    if kind == "verify_prog":
                        _, idx, total, rel = ev
                        lbl_chk_sub.config(text=f"Verifying {idx}/{total}: {Path(rel).name}")
                    elif kind == "plan_ok":
                        _, plan, _rehash = ev
                        state["checking"] = False
                        if not plan.needs_action:
                            if launch and not standalone:
                                finish(0)
                                return
                            show_up_to_date(plan)
                        else:
                            show_prompt(plan)
                    elif kind == "offline":
                        state["checking"] = False
                        if launch and not standalone:
                            updater.log(f"offline: update check skipped ({ev[1]})")
                            finish(0)
                            return
                        show_offline(ev[1])
                    elif kind == "error":
                        state["checking"] = False
                        updater.log(f"check failed: {ev[1]}")
                        show_error(ev[1], retry_plan=None)
                    elif kind == "dl_prog":
                        _, done, tot, rel, src_label = ev
                        tracker.update(done)
                        pb, lbl_l, lbl_r, lbl_s = state["prog_widgets"]
                        pct = min(100, (done * 100 // tot) if tot else 100)
                        pb["value"] = pct
                        lbl_l.config(text=f"{pct}%  •  {fmt(done)} / {fmt(tot)}")
                        rem = max(0, tot - done)
                        lbl_r.config(text=f"{fmt_speed(tracker.current_speed())}  •  {fmt_eta(tracker.eta_seconds(rem))}")
                        lbl_s.config(text=f"Fetching {Path(rel).name} ({src_label})")
                    elif kind == "dl_status":
                        if "prog_widgets" in state:
                            state["prog_widgets"][3].config(text=ev[1])
                    elif kind == "dl_done":
                        _, plan, res = ev
                        state["downloading"] = False
                        if plan.kind == "dmg":
                            show_done(plan)
                        elif launch and not standalone:
                            finish(3 if res else 0)
                            return
                        else:
                            show_done(plan)
                    elif kind == "dl_cancelled":
                        state["downloading"] = False
                        finish(0 if standalone else 4)
                        return
                    elif kind == "dl_error":
                        _, plan, err_text = ev
                        state["downloading"] = False
                        updater.log(f"update failed: {err_text}")
                        show_error(err_text, retry_plan=plan)
            except queue.Empty:
                pass
            if root.winfo_exists():
                root.after(40, poll_queue)

        start_check(rehash=force)
        root.after(40, poll_queue)
        root.mainloop()
        return state["exit_code"]

    @staticmethod
    def _load_icon(root, pkg_root):
        try:
            tools_dir = Path(pkg_root) / "tools"
            if os.name == "nt":
                for name in ("bakoquake-update.ico", "bakoquake.ico"):
                    ico = tools_dir / name
                    if ico.is_file():
                        root.iconbitmap(str(ico))
                        return
            for name in ("bakoquake-update-256.png", "bakoquake-256.png"):
                png = tools_dir / name
                if png.is_file():
                    img = root.tk.call("image", "create", "photo", "-file", str(png))
                    root.iconphoto(True, img)
                    return
        except Exception:
            pass


def choose_ui(args):
    if args.no_gui or args.check or (not args.launch and not args.standalone):
        return CliUpdateUI(interactive=False, quiet=args.launch)
    # Try tkinter GUI first
    try:
        import tkinter as tk
        # Verify display is actually reachable before constructing full UI later
        if os.name != "nt" and sys.platform != "darwin" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            raise tk.TclError("no display")
        return TkUpdateUI()
    except Exception:
        pass
    # Linux fallback: zenity if display exists and no TTY
    if os.name != "nt" and sys.platform != "darwin" and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        z = shutil.which("zenity")
        if z and not (sys.stdin and sys.stdin.isatty()):
            return ZenityUpdateUI(z)
    return CliUpdateUI(interactive=True, quiet=args.launch)


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    wants_console = any(f in raw_argv for f in ("-h", "--help", "--version", "--check", "--no-gui")) or (
        "--launch" not in raw_argv and "--standalone" not in raw_argv
    )
    _ensure_streams(attach_console=wants_console)

    ap = argparse.ArgumentParser(description="BAKOQUAKE differential updater v2")
    ap.add_argument("--root", type=Path, default=None, help="package root (default: the folder above tools/)")
    ap.add_argument("--check", action="store_true", help="only report; exit 10 if an update or repair is available")
    ap.add_argument("--launch", action="store_true", help="run from a launcher (invisible unless slow or updating)")
    ap.add_argument("--standalone", action="store_true", help="standalone updater GUI (never launches the game)")
    ap.add_argument("--force-rehash", action="store_true", help="ignore the hash cache and re-check every file")
    ap.add_argument("--no-gui", action="store_true", help="force terminal/headless mode")
    ap.add_argument("--platform", default=default_platform())
    ap.add_argument("--manifest-url", default=None, help="override primary manifest URL")
    ap.add_argument("--fallback-url", default=None, help="override VPS fallback manifest URL (empty disables)")
    ap.add_argument("--bundle-mac-inputs", type=Path, default=None, help="path to macOS app bundle mac-inputs file")
    ap.add_argument("--version", action="store_true", help="print updater version and exit")
    a = ap.parse_args(raw_argv)

    if a.version:
        print(f"bq-update {VERSION}")
        return 0
    # Double-clicking frozen Update.exe with no flags opens the standalone updater GUI.
    if getattr(sys, "frozen", False) and not any((a.check, a.launch, a.standalone, a.no_gui, a.manifest_url)):
        a.standalone = True
    if os.environ.get("BQ_NO_UPDATE") and not a.standalone:
        return 0

    root = (a.root or default_root()).resolve()
    bq = root / ".bq"
    bq.mkdir(parents=True, exist_ok=True)
    logf = open(bq / "update.log", "a", encoding="utf-8")

    def log(msg):
        logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
        logf.flush()
        if not a.launch and not a.standalone:
            print(msg)

    lock = bq / "update.lock"
    if not acquire_lock(lock, log):
        print("Another BAKOQUAKE update is already running; please wait for it to finish.", file=sys.stderr, flush=True)
        logf.close()
        return 4

    try:
        url = a.manifest_url or os.environ.get("BQ_MANIFEST_URL") or LATEST.format(platform=a.platform)
        if a.fallback_url is not None:
            fb_url = a.fallback_url or None
        elif "BQ_FALLBACK_URL" in os.environ:
            fb_url = os.environ["BQ_FALLBACK_URL"] or None
        elif a.manifest_url is not None:
            # Explicit --manifest-url (e.g. local/CI test) disables external VPS fallback unless specified.
            fb_url = None
        else:
            fb_url = VPS_LATEST.format(platform=a.platform)

        ui = choose_ui(a)
        updater = Updater(
            root=root,
            platform=a.platform,
            manifest_url=url,
            log=log,
            fallback_url=fb_url,
            bundle_mac_inputs=a.bundle_mac_inputs,
        )
        return updater.run(
            check=a.check,
            force=a.force_rehash,
            launch=a.launch,
            standalone=a.standalone,
            ui=ui,
        )
    except OfflineError as e:
        log(f"offline: update check skipped ({e})")
        return 0 if (a.launch and not a.standalone) else 4
    except Exception as e:
        log(f"unexpected updater error: {e}")
        print(f"Update error: {e}", file=sys.stderr, flush=True)
        return 4
    finally:
        lock.unlink(missing_ok=True)
        logf.close()


if __name__ == "__main__":
    sys.exit(main())
