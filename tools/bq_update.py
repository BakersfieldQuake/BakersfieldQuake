#!/usr/bin/env python3
"""BAKOQUAKE updater: downloads only the files that changed in the newest release, then returns to the launcher.

bq_update.py [--root DIR] [--check | --launch] [--force-rehash] [--manifest-url URL] [--platform NAME]

The launchers run it before starting the engine. It never stops anyone from playing: offline, GitHub down, a bad
download or a locked file all end with the installed version left as it was and exit code 0 (except --check).

How it works (docs/auto-update-plan.md):
- The newest manifest is fetched from the latest release (releases/latest/download/manifest-<platform>.json). It
  lists every package file with its size and sha256, and the URL of that release's zip.
- Local files are compared by sha256 (cached by size and mtime in .bq/state.json, so a normal launch only stats).
- Each changed file is fetched straight out of the release zip with one HTTP Range request, inflated if needed,
  checked against the manifest, staged in .bq/staging, then moved into place. Any failure rolls back and keeps
  the old version.
- Files the player owns are never touched: anything not listed in the new or the previous manifest (id1 paks,
  saved config, demos, screenshots), and install_only files once they exist.

Exit codes: 0 nothing changed (up to date, skipped or failed), 3 files were updated, 10 (--check only) an update
is available, 2 bad arguments. On 3 the launcher must re-run itself: it may have just been replaced, and cmd and
bash read a running script from disk line by line.
Stdlib only, so it can be frozen with PyInstaller (bq-update.exe on Windows, bq-update on macOS).
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from pathlib import Path

VERSION = 1
REPO = "BakersfieldQuake/BakersfieldQuake"
LATEST = f"https://github.com/{REPO}/releases/latest/download/manifest-{{platform}}.json"
UA = {"User-Agent": f"bq-update/{VERSION}"}
TIMEOUT = 10        # seconds per request
CHECK_TIMEOUT = 4   # the manifest fetch: keep a launch snappy when offline
LOCK_STALE = 30 * 60


def default_platform():
    if sys.platform.startswith("win"):
        return "windows-x64"
    if sys.platform == "darwin":
        return "macos-arm64"
    return "linux-x86_64"


def default_root():
    # tools/bq_update.py or tools/bq-update[.exe] -> the package root is one folder up.
    me = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    return me.parent.parent


class Updater:
    def __init__(self, root, platform, manifest_url, log):
        self.root = Path(root)
        self.platform = platform
        self.manifest_url = manifest_url
        self.bq = self.root / ".bq"
        self.log = log

    # ---- state -------------------------------------------------------------------------------------------------
    def load_state(self):
        try:
            return json.loads((self.bq / "state.json").read_text("utf-8"))
        except (OSError, ValueError):
            return None

    def save_state(self, state):
        tmp = self.bq / "state.json.tmp"
        tmp.write_text(json.dumps(state, indent=1, sort_keys=True), "utf-8")
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
                h.update(chunk)
        cache[rel] = [st.st_size, st.st_mtime_ns, h.hexdigest()]
        return cache[rel][2]

    # ---- network -----------------------------------------------------------------------------------------------
    def get_json(self, url, timeout):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.load(r)

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

    def fetch_entry(self, info, dest, want_sha, want_size, progress):
        """One Range GET per entry: local header + data. Streams, inflates and hashes into dest."""
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise IOError(f"{info.filename}: unsupported compression {info.compress_type}")
        # The local header's extra field can differ from the central directory's, so read it from the header itself.
        # Ask for 64 KiB of slack (the extra field's maximum); the read stops at the end of the data.
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
                skip -= len(r.read(min(skip, 1 << 16)))
            left = info.compress_size
            while left:
                chunk = r.read(min(left, 1 << 20))
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
                h.update(tail)
                out.write(tail)
                written += len(tail)
        if written != want_size or h.hexdigest() != want_sha:
            raise IOError(f"{info.filename}: downloaded file does not match the manifest")

    # ---- main flow ---------------------------------------------------------------------------------------------
    def run(self, check=False, force=False, launch=False):
        state = self.load_state()
        try:
            self.manifest = self.get_json(self.manifest_url, CHECK_TIMEOUT)
        except Exception as e:  # offline, GitHub down, no manifest yet: play what is installed
            self.log(f"update check skipped: {e}")
            return 0
        m = self.manifest
        if m.get("schema") != 1:
            self.log(f"update skipped: manifest schema {m.get('schema')} is newer than this updater")
            return 0
        installed = state["build"] if state else 0
        if m["build"] < installed:
            self.log(f"update skipped: release build {m['build']} is older than the installed build {installed}")
            return 0
        if state and m["build"] == installed and not force:
            return 0

        cache = (state or {}).get("cache", {})
        fetch, install_only = [], set(m.get("install_only", []))
        for rel, f in m["files"].items():
            if rel in install_only and (self.root / rel).exists():
                continue
            if self.local_sha(rel, cache, force) != f["sha256"]:
                fetch.append(rel)
        previous = set((state or {}).get("managed", []))
        delete = sorted(p for p in previous - set(m["files"]) if (self.root / p).exists())

        total = sum(m["files"][p]["size"] for p in fetch)
        if check:
            print(f"build {installed} installed, build {m['build']} available: "
                  f"{len(fetch)} files ({total / 1e6:.1f} MB) to download, {len(delete)} to remove")
            return 10 if fetch or delete else 0
        changed = bool(fetch or delete)
        if changed:
            if launch:
                show_console()
            msg = f"Updating BAKOQUAKE build {installed} to {m['build']}: {len(fetch)} files, {fmt(total)}"
            if launch:      # log() already prints when not launched
                print(msg, flush=True)
            self.log(msg)   # launchers discard stdout; the log is the only record of a successful update
            self.apply(fetch, delete, cache)
        self.save_state({"build": m["build"], "version": m.get("version", ""), "managed": sorted(m["files"]),
                         "cache": {p: cache[p] for p in m["files"] if p in cache}, "updater": VERSION})
        if changed:
            self.log(f"updated to build {m['build']}")
        return 3 if changed else 0

    def apply(self, fetch, delete, cache):
        m = self.manifest
        staging, backup = self.bq / "staging", self.bq / "backup"
        for d in (staging, backup):
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True)

        # 1. download and verify everything before touching the install
        if fetch:
            self.zip_src = m["zip"]
            self.zip_url, self.zip_size = self.resolve(self.zip_src)
            entries = self.central_directory()
            done, total = [0], sum(m["files"][p]["size"] for p in fetch) or 1

            def progress(n):
                done[0] += n
                print(f"\r  {done[0] * 100 // total:3d}%  {fmt(done[0])} of {fmt(total)}   ", end="", flush=True)

            for rel in fetch:
                if rel not in entries:
                    raise IOError(f"{rel} is in the manifest but not in the release zip")
                dest = staging / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                f = m["files"][rel]
                for attempt in range(3):
                    try:
                        self.fetch_entry(entries[rel], dest, f["sha256"], f["size"], progress)
                        break
                    except (OSError, zlib.error) as e:
                        if attempt == 2:
                            raise
                        self.log(f"retrying {rel}: {e}")
            print()

        # 2. move files into place, keeping backups so a locked file rolls everything back
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
                st = target.stat()
                cache[rel] = [st.st_size, st.st_mtime_ns, m["files"][rel]["sha256"]]
        except OSError as e:
            failed = rel
            for rel in reversed(moved):
                try:
                    if (backup / rel).exists():
                        os.replace(backup / rel, self.root / rel)
                    else:
                        (self.root / rel).unlink()
                except OSError:
                    pass
                cache.pop(rel, None)
            raise IOError(f"could not replace {failed} ({e}); is the game or a server running "
                          f"from this folder? The update was rolled back.") from e

        # Unzipped on a Mac or Linux box from a zip without mode bits, or just replaced: make them runnable.
        if os.name != "nt":
            for rel in m.get("exec", []):
                p = self.root / rel
                if p.exists() and not os.access(p, os.X_OK):
                    p.chmod(p.stat().st_mode | 0o111)

        # 3. files the new release dropped (only ever ones the previous manifest listed)
        for rel in delete:
            try:
                (self.root / rel).unlink()
                print(f"  removed {rel}")
            except OSError as e:
                self.log(f"could not remove {rel}: {e}")
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
        print("  done.", flush=True)


def replace_running(target, backup):
    """Moves target to backup. Windows lets a running .exe be renamed but not overwritten, which is how the
    updater replaces itself (the old copy stays in .bq/backup until the next update clears it). Anything else that
    is locked raises and triggers the rollback."""
    os.replace(target, backup)


def fmt(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e5 else f"{n / 1e3:.0f} KB"


def show_console():
    """PLAY BAKERSFIELDQUAKE.exe starts Play.cmd with no console window. Open one while downloading, so a big
    update doesn't look like a hang."""
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        if k.GetConsoleWindow():
            return
        k.FreeConsole()
        if k.AllocConsole():
            k.SetConsoleTitleW("BAKOQUAKE update")
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = sys.stdout
    except Exception:
        pass


def message_box(text):
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, text, "BAKOQUAKE update", 0x30)
        except Exception:
            pass


def main(argv=None):
    ap = argparse.ArgumentParser(description="BAKOQUAKE differential updater")
    ap.add_argument("--root", type=Path, default=None, help="package root (default: the folder above tools/)")
    ap.add_argument("--check", action="store_true", help="only report; exit 10 if an update is available")
    ap.add_argument("--launch", action="store_true", help="run from a launcher (quiet when up to date)")
    ap.add_argument("--force-rehash", action="store_true", help="ignore the hash cache and re-check every file")
    ap.add_argument("--platform", default=default_platform())
    ap.add_argument("--manifest-url", default=None)
    a = ap.parse_args(argv)
    if os.environ.get("BQ_NO_UPDATE"):
        return 0
    root = (a.root or default_root()).resolve()
    bq = root / ".bq"
    bq.mkdir(exist_ok=True)
    logf = open(bq / "update.log", "a", encoding="utf-8")

    def log(msg):
        logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
        logf.flush()
        if not a.launch:
            print(msg)

    lock = bq / "update.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            stale = time.time() - lock.stat().st_mtime > LOCK_STALE
        except OSError:
            stale = True
        if not stale:
            log("another update is running; skipping")
            return 0
        lock.unlink(missing_ok=True)
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    try:
        url = a.manifest_url or LATEST.format(platform=a.platform)
        return Updater(root, a.platform, url, log).run(check=a.check, force=a.force_rehash, launch=a.launch)
    except Exception as e:  # never block the game
        log(f"update failed: {e}")
        print(f"\nUpdate failed, starting the installed version: {e}", flush=True)
        if a.launch:   # only from a launcher: a dialog would hang a headless run (CI, ssh)
            message_box(f"The update failed, so the installed version will start.\n\n{e}")
        return 0
    finally:
        lock.unlink(missing_ok=True)
        logf.close()


if __name__ == "__main__":
    sys.exit(main())
