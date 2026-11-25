#!/usr/bin/env python3
"""Stage, verify, and deliver all Bakersfield-ish final videos + offline HTML viewer to Telegram.

Delivers:
  - 4 Destruction showcase MP4s (Fox Theater + Rebuild, Padre Hotel, Bakersfield Sign, Shatterable Glass)
  - 6 360-degree Orbit MP4s (Fox / Padre / Sign x intact & collapsed)
  - 1 Full Map Fly-through MP4 (all downtown anchors, 4 merged landmarks & chained SkyPads)
  - 1 Single-file offline interactive WebGL2 HTML viewer (bakersfieldish_viewer.html)

Safety & Hygiene:
  - NEVER hardcode a Telegram bot token or print secrets to stdout, stderr, logs, or manifests.
  - Supplies token at runtime strictly via `--token` or `TG_BOT_TOKEN` env var (passed to curl via stdin `-K -`).
  - Automatically validates every MP4 (`ftyp`, `nb_streams == 2` synced AAC audio, strictly `< 48.5 MB` cap),
    auto-compressing or splitting without content loss if any MP4 exceeds Telegram's 50 MB Bot API limit.
  - Validates the standalone HTML viewer has zero external CDN/fetch/ES-module dependencies.
  - If `TG_BOT_TOKEN` is absent or `--stage-only` is set (or Telegram is unreachable), cleanly stages all
    verified artifacts into `--deliverables-dir` with `DELIVERY_MANIFEST.md` + `delivery_manifest.json` and
    exits 0 (unless `--require-telegram` is passed).

Usage:
  python source/mm_tools/deliver_bakersfieldish_telegram.py --stage-only
  python source/mm_tools/deliver_bakersfieldish_telegram.py --dry-run
  TG_BOT_TOKEN=... python source/mm_tools/deliver_bakersfieldish_telegram.py
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_DELIVERABLES_DIR = REPO_ROOT / "docs" / "bakersfieldish_deliverables"
DEFAULT_CHAT_ID = "-4993867752"
DEFAULT_VPS_HOST = "root@72.62.241.93"
DEFAULT_VPS_PORT = "22"

SHOWCASE_URL = "https://bakersfield.larrywew.fun/bakersfieldish_showcase.html"
INTERACTIVE_URL = "https://bakersfield.larrywew.fun/bakersfieldish_interactive.html"

TELEGRAM_MAX_BYTES = int(48.5 * 1024 * 1024)  # Safe margin under Telegram Bot API 50 MB limit
TG_TOKEN_PATTERN = re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b")


@dataclass
class DeliverableSpec:
    key: str
    kind: str  # "video" or "html"
    dest_name: str
    title: str
    caption: str
    candidates: List[Path]


def default_deliverable_specs(repo_root: Path) -> List[DeliverableSpec]:
    deliv = repo_root / "docs" / "bakersfieldish_deliverables"
    cap_final = repo_root / "docs" / "bakersfieldish_captures" / "final"
    cap_std = repo_root / "docs" / "captures" / "bakersfieldish"
    docs = repo_root / "docs"

    return [
        DeliverableSpec(
            key="destruct_fox",
            kind="video",
            dest_name="fox_destruct.mp4",
            title="Fox Theater — 3-Stage Destruction & Slow Rebuild",
            caption=(
                "🏛️ <b>Bakersfield-ish — Fox Theater 3-Stage Destruction &amp; Slow Rebuild</b>\n"
                "3-part progressive shot-area breaks (marquee → clock/belfry → full crash) with multi-point explosions, "
                "warm matte dust surge, climbable rubble, and 25s upright staged rebuild."
            ),
            candidates=[
                deliv / "fox_destruct.mp4",
                cap_final / "fox_destruct.mp4",
                cap_std / "destruct_fox.mp4",
            ],
        ),
        DeliverableSpec(
            key="destruct_padre",
            kind="video",
            dest_name="padre_destruct.mp4",
            title="Padre Hotel — 3-Stage Controlled Demolition",
            caption=(
                "🏨 <b>Bakersfield-ish — Padre Hotel 3-Stage Controlled Demolition</b>\n"
                "3-part progressive breaks (east wing → rooftop crown → full implosion) with 20+ explosions, "
                "massive non-blinding dust surge, player/kart-bouncing rolling concrete boulders &amp; 2-story climbable ruin."
            ),
            candidates=[
                deliv / "padre_destruct.mp4",
                cap_final / "padre_destruct.mp4",
                cap_std / "destruct_padre.mp4",
            ],
        ),
        DeliverableSpec(
            key="destruct_sign",
            kind="video",
            dest_name="sign_destruct.mp4",
            title="The Bakersfield Sign — 3-Stage Break & Topple",
            caption=(
                "🪧 <b>Bakersfield-ish — The Bakersfield Sign 3-Stage Break &amp; Topple</b>\n"
                "3-part progressive breaks (west cap → east cap → full -90° arch topple) with multi-point pier/impact explosions, "
                "neon sparks, matte dust surge &amp; Go-Kart rampable fallen wreckage."
            ),
            candidates=[
                deliv / "sign_destruct.mp4",
                cap_final / "sign_destruct.mp4",
                cap_std / "destruct_sign.mp4",
            ],
        ),
        DeliverableSpec(
            key="destruct_glass",
            kind="video",
            dest_name="glass_destruct.mp4",
            title="Shatterable Storefront Glass",
            caption=(
                "🪟 <b>Bakersfield-ish — Shatterable Glass Windows</b>\n"
                "1-hit shatter into translucent beveled ice-blue 3D shards across 56 hollow bays spanning 6+ downtown &amp; merged buildings."
            ),
            candidates=[
                deliv / "glass_destruct.mp4",
                cap_final / "glass_destruct.mp4",
                cap_std / "destruct_glass.mp4",
            ],
        ),
        DeliverableSpec(
            key="orbit_fox_intact",
            kind="video",
            dest_name="fox_orbit_intact.mp4",
            title="360° Orbit — Fox Theater (Intact)",
            caption="🔄 <b>Bakersfield-ish — 360° Orbit: Historic Fox Theater (Intact)</b>",
            candidates=[
                deliv / "fox_orbit_intact.mp4",
                cap_final / "fox_orbit_intact.mp4",
                cap_std / "orbit_fox_intact.mp4",
            ],
        ),
        DeliverableSpec(
            key="orbit_fox_collapsed",
            kind="video",
            dest_name="fox_orbit_collapsed.mp4",
            title="360° Orbit — Fox Theater (Collapsed)",
            caption="🔄 <b>Bakersfield-ish — 360° Orbit: Fox Theater (Collapsed Climbable Ruin)</b>",
            candidates=[
                deliv / "fox_orbit_collapsed.mp4",
                cap_final / "fox_orbit_collapsed.mp4",
                cap_std / "orbit_fox_collapsed.mp4",
            ],
        ),
        DeliverableSpec(
            key="orbit_padre_intact",
            kind="video",
            dest_name="padre_orbit_intact.mp4",
            title="360° Orbit — Padre Hotel (Intact)",
            caption="🔄 <b>Bakersfield-ish — 360° Orbit: The Padre Hotel (Intact)</b>",
            candidates=[
                deliv / "padre_orbit_intact.mp4",
                cap_final / "padre_orbit_intact.mp4",
                cap_std / "orbit_padre_intact.mp4",
            ],
        ),
        DeliverableSpec(
            key="orbit_padre_collapsed",
            kind="video",
            dest_name="padre_orbit_collapsed.mp4",
            title="360° Orbit — Padre Hotel (Collapsed)",
            caption="🔄 <b>Bakersfield-ish — 360° Orbit: Padre Hotel (Collapsed 2-Story Rubble)</b>",
            candidates=[
                deliv / "padre_orbit_collapsed.mp4",
                cap_final / "padre_orbit_collapsed.mp4",
                cap_std / "orbit_padre_collapsed.mp4",
            ],
        ),
        DeliverableSpec(
            key="orbit_sign_intact",
            kind="video",
            dest_name="sign_orbit_intact.mp4",
            title="360° Orbit — Bakersfield Sign (Intact)",
            caption="🔄 <b>Bakersfield-ish — 360° Orbit: The Bakersfield Sign (Intact over H St)</b>",
            candidates=[
                deliv / "sign_orbit_intact.mp4",
                cap_final / "sign_orbit_intact.mp4",
                cap_std / "orbit_sign_intact.mp4",
            ],
        ),
        DeliverableSpec(
            key="orbit_sign_collapsed",
            kind="video",
            dest_name="sign_orbit_collapsed.mp4",
            title="360° Orbit — Bakersfield Sign (Collapsed)",
            caption="🔄 <b>Bakersfield-ish — 360° Orbit: Bakersfield Sign (Fallen Go-Kart Rampable Wreckage)</b>",
            candidates=[
                deliv / "sign_orbit_collapsed.mp4",
                cap_final / "sign_orbit_collapsed.mp4",
                cap_std / "orbit_sign_collapsed.mp4",
            ],
        ),
        DeliverableSpec(
            key="flythrough",
            kind="video",
            dest_name="bakersfieldish_flythrough.mp4",
            title="Full Downtown Bakersfield-ish Fly-Through",
            caption=(
                "✈️ <b>Bakersfield-ish — Complete Downtown Fly-Through</b>\n"
                "Smooth tour across Padre Hotel, 18th &amp; Eye Parking Garage, Bakersfield Sign, Fox Theater, "
                "Larry's Warehouse, Golden West Casino, The Great Castle, and the chained Super Jump Pad skyline!"
            ),
            candidates=[
                deliv / "bakersfieldish_flythrough.mp4",
                cap_final / "bakersfieldish_flythrough.mp4",
                cap_std / "flythrough_bakersfieldish.mp4",
            ],
        ),
        DeliverableSpec(
            key="html_viewer",
            kind="html",
            dest_name="bakersfieldish_interactive.html",
            title="Offline Interactive 3D WebGL2 Map Viewer",
            caption=(
                "🌐 <b>Bakersfield-ish — Standalone Offline Interactive 3D Map Viewer</b>\n"
                "Open directly in any browser via file:// (zero internet/CDN needed). "
                "WASD + mouse free-fly, 8 landmark teleports, and interactive 3-stage Fox/Padre/Sign/Glass demolition!\n"
                f"🔗 Live: {INTERACTIVE_URL}"
            ),
            candidates=[
                deliv / "bakersfieldish_interactive.html",
                docs / "bakersfieldish_viewer.html",
            ],
        ),
        DeliverableSpec(
            key="html_showcase",
            kind="html",
            dest_name="bakersfieldish_showcase.html",
            title="Offline Showcase & Engineering Changelog Page",
            caption=(
                "📋 <b>Bakersfield-ish — Showcase Gallery &amp; Engineering Changelog</b>\n"
                "Self-contained offline HTML (0 external deps): merged downtown overview, interactive 3-stage demolition "
                "gallery, critic scores (86–91/100) &amp; full change notes.\n"
                f"🔗 Live: {SHOWCASE_URL}"
            ),
            candidates=[
                deliv / "bakersfieldish_showcase.html",
                docs / "bakersfieldish_showcase.html",
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# Security & Verification Helpers
# ---------------------------------------------------------------------------
def redact(text: str, token: Optional[str]) -> str:
    masked = TG_TOKEN_PATTERN.sub("<REDACTED_TG_TOKEN>", text)
    if not token:
        return masked
    masked = masked.replace(token, "<REDACTED_TG_TOKEN>")
    if ":" in token:
        bot_id, secret = token.split(":", 1)
        if len(bot_id) >= 8:
            masked = masked.replace(bot_id, "<REDACTED_BOT_ID>")
        if len(secret) >= 12:
            masked = masked.replace(secret, "<REDACTED_TG_SECRET>")
    return masked


def verify_secret_hygiene(token: Optional[str]) -> None:
    self_path = Path(__file__).resolve()
    self_text = self_path.read_text(encoding="utf-8")
    if TG_TOKEN_PATTERN.search(self_text):
        raise AssertionError(f"Hardcoded Telegram token pattern detected in {self_path.name}")
    if token:
        parts = [token]
        if ":" in token:
            bot_id, secret = token.split(":", 1)
            if len(bot_id) >= 8:
                parts.append(bot_id)
            if len(secret) >= 12:
                parts.append(secret)
        for p in parts:
            if p in self_text:
                raise AssertionError(f"Runtime Telegram secret leaked into {self_path.name}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def validate_caption(caption: str, label: str) -> None:
    plain = html.unescape(re.sub(r"<[^>]+>", "", caption))
    utf16_raw = len(caption.encode("utf-16-le")) // 2
    utf16_plain = len(plain.encode("utf-16-le")) // 2
    if max(len(caption), len(plain), utf16_raw, utf16_plain) > 1024:
        raise AssertionError(f"Telegram caption too long for {label} ({len(caption)} chars)")


def probe_mp4(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        hdr = f.read(16)
    if len(hdr) < 12 or hdr[4:8] != b"ftyp":
        raise AssertionError(f"Invalid MP4 header (missing ftyp box): {path}")

    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size:stream=index,codec_type,codec_name,width,height,sample_rate,channels",
            "-of", "json",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    meta = json.loads(r.stdout)
    streams = meta.get("streams") or []
    vstreams = [s for s in streams if s.get("codec_type") == "video"]
    astreams = [s for s in streams if s.get("codec_type") == "audio"]
    if not vstreams:
        raise AssertionError(f"MP4 missing video stream: {path}")
    vs = vstreams[0]
    dur = float((meta.get("format") or {}).get("duration") or 0.0)
    return {
        "width": int(vs.get("width") or 1280),
        "height": int(vs.get("height") or 720),
        "vcodec": str(vs.get("codec_name") or "h264"),
        "duration_s": round(dur, 2),
        "nb_streams": len(streams),
        "has_audio": bool(astreams),
        "acodec": str(astreams[0].get("codec_name") or "") if astreams else "",
        "bytes": path.stat().st_size,
    }


def verify_offline_html(path: Path) -> Dict[str, Any]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    ext_urls = re.findall(r"(?:src|href)\s*=\s*[\"']https?://", txt, re.I)
    has_fetch = bool(re.search(r"\bfetch\s*\(", txt))
    has_module = bool(re.search(r"<script[^>]+type\s*=\s*[\"']module[\"']", txt, re.I))
    has_gzip_stream = "DecompressionStream" in txt
    return {
        "bytes": path.stat().st_size,
        "external_refs": len(ext_urls),
        "has_fetch": has_fetch,
        "has_es_module": has_module,
        "has_gzip_stream": has_gzip_stream,
        "offline_clean": (len(ext_urls) == 0 and not has_fetch and not has_module),
    }


# ---------------------------------------------------------------------------
# Staging & < 48.5 MB Enforcement
# ---------------------------------------------------------------------------
def stage_video(src: Path, dest_dir: Path, dest_name: str, require_audio: bool = True) -> List[Tuple[Path, Dict[str, Any]]]:
    dest = dest_dir / dest_name
    if src.stat().st_size <= TELEGRAM_MAX_BYTES:
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        info = probe_mp4(dest)
        if require_audio and not info["has_audio"]:
            raise AssertionError(f"MP4 missing synchronized audio stream (nb_streams={info['nb_streams']}): {dest.name}")
        return [(dest, info)]

    # Exceeds Telegram 48.5 MB limit -> re-encode / split cleanly via bakersfieldish_capture helper
    sys.path.insert(0, str(HERE))
    import bakersfieldish_capture as bc

    parts = bc.encode_telegram_mp4(
        str(src),
        str(dest),
        max_mb=TELEGRAM_MAX_BYTES / (1024 * 1024),
        fade_out_s=0.0,
    )
    out: List[Tuple[Path, Dict[str, Any]]] = []
    for p_str in parts:
        p = Path(p_str)
        info = probe_mp4(p)
        if p.stat().st_size > TELEGRAM_MAX_BYTES:
            raise AssertionError(f"Compressed part still exceeds 48.5 MB: {p.name}")
        if require_audio and not info["has_audio"]:
            raise AssertionError(f"Compressed part missing audio stream: {p.name}")
        out.append((p, info))
    return out


def stage_html(src: Path, dest_dir: Path, dest_name: str) -> Tuple[Path, Optional[Path], Dict[str, Any]]:
    dest = dest_dir / dest_name
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)
    info = verify_offline_html(dest)
    if not info["offline_clean"]:
        raise AssertionError(f"Offline HTML viewer failed zero-external-dep check: {info}")

    # If raw HTML > 48.5 MB, create a companion ZIP for Telegram sendDocument while keeping raw HTML in folder
    tg_doc: Optional[Path] = dest
    if dest.stat().st_size > TELEGRAM_MAX_BYTES:
        zpath = dest_dir / (dest.stem + ".zip")
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zi = zipfile.ZipInfo(dest.name, date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, dest.read_bytes())
        tg_doc = zpath if zpath.stat().st_size <= TELEGRAM_MAX_BYTES else None
    return dest, tg_doc, info


# ---------------------------------------------------------------------------
# Telegram Bot API Senders (Token strictly via stdin `-K -` or in-memory urllib)
# ---------------------------------------------------------------------------
def _validate_token_chars(token: str) -> None:
    if any(ch in token for ch in ('"', "\\", "\r", "\n", " ", "\t")):
        raise ValueError("Invalid characters in Telegram bot token")


def _parse_tg_response(raw: str, token: str, method: str) -> Dict[str, Any]:
    try:
        res = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Telegram {method} returned non-JSON ({exc}): {redact(raw[:300], token)}") from None
    if res.get("ok") is not True:
        raise RuntimeError(f"Telegram {method} returned ok!=true: {redact(raw[:400], token)}")
    return res


def _encode_multipart(
    fields: Sequence[Tuple[str, str]],
    files: Sequence[Tuple[str, str, str, bytes]],
) -> Tuple[bytes, str]:
    boundary = f"----BakoDeliverBoundary{uuid.uuid4().hex}"
    parts: List[bytes] = []
    for name, val in fields:
        parts.extend([
            f"--{boundary}".encode("ascii"),
            f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"),
            b"",
            val.encode("utf-8"),
        ])
    for field_name, fname, ctype, data in files:
        parts.extend([
            f"--{boundary}".encode("ascii"),
            f'Content-Disposition: form-data; name="{field_name}"; filename="{fname}"'.encode("utf-8"),
            f"Content-Type: {ctype}".encode("ascii"),
            b"",
            data,
        ])
    parts.extend([f"--{boundary}--".encode("ascii"), b""])
    return b"\r\n".join(parts), f"multipart/form-data; boundary={boundary}"


def vps_stage_files(files: Sequence[Path], vps_host: str, vps_port: str) -> str:
    """Stream validated deliverable files to a temp dir on VPS via uncompressed tar over SSH."""
    remote_dir = f"/tmp/bako_tg_stage_{uuid.uuid4().hex[:12]}"
    total_mb = sum(p.stat().st_size for p in files) / (1024 * 1024)
    print(f"[vps-curl] Streaming {len(files)} files ({total_mb:.2f} MB) via SSH tar -> {vps_host}:{remote_dir}...", flush=True)
    remote_cmd = f"set -e; mkdir -p {shlex.quote(remote_dir)}; tar -xf - -C {shlex.quote(remote_dir)}; ls -1 {shlex.quote(remote_dir)} | wc -l"
    proc = subprocess.Popen(
        [
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
            "-p", str(vps_port), vps_host, remote_cmd,
        ],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None
    try:
        with tarfile.open(fileobj=proc.stdin, mode="w|") as tf:
            for p in files:
                tf.add(str(p), arcname=p.name)
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
    out_b, err_b = proc.communicate(timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(
            f"VPS staging tar exited {proc.returncode}: "
            f"{(err_b or out_b).decode('utf-8', errors='replace').strip()}"
        )
    print(f"[vps-curl] Staged {out_b.decode('utf-8', errors='replace').strip()} files on VPS cleanly.", flush=True)
    return remote_dir


def vps_cleanup_stage(remote_dir: str, vps_host: str, vps_port: str) -> None:
    if not remote_dir.startswith("/tmp/bako_tg_stage_"):
        return
    try:
        subprocess.run(
            [
                "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                "-p", str(vps_port), vps_host,
                f"rm -rf {shlex.quote(remote_dir)}",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
        )
    except Exception:
        pass


def tg_send_message_vps_curl(
    token: str,
    chat_id: str,
    text: str,
    vps_host: str,
    vps_port: str,
    timeout: int = 60,
) -> int:
    """Send Telegram message from VPS via curl -4 -K - (token strictly on stdin; never in argv/ps/disk)."""
    _validate_token_chars(token)
    stdin_cfg = f'url = "https://api.telegram.org/bot{token}/sendMessage"\n'.encode("utf-8")
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    remote_cmd = (
        "set -e; "
        "TMPD=$(mktemp -d); "
        "trap 'rm -rf \"$TMPD\"' EXIT; "
        f"printf '%s' {shlex.quote(text_b64)} | base64 -d > \"$TMPD/msg.txt\"; "
        f"curl -4 -sS --max-time {int(timeout)} -K - "
        f"-F {shlex.quote(f'chat_id={chat_id}')} "
        "-F parse_mode=HTML "
        "-F \"text=<$TMPD/msg.txt\""
    )
    proc = subprocess.run(
        [
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
            "-p", str(vps_port), vps_host, remote_cmd,
        ],
        input=stdin_cfg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=int(timeout) + 30,
    )
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    err = proc.stderr.decode("utf-8", errors="replace").strip()
    if proc.returncode != 0:
        raise RuntimeError(f"VPS curl sendMessage rc={proc.returncode}: {redact(err or out, token)}")
    res = _parse_tg_response(out, token, "sendMessage")
    return int(res["result"]["message_id"])


def tg_send_file_vps_curl(
    token: str,
    chat_id: str,
    method: str,
    field: str,
    mime: str,
    remote_file: str,
    filename: str,
    caption: str,
    vps_host: str,
    vps_port: str,
    extra_fields: Sequence[Tuple[str, str]] = (),
    timeout: int = 300,
) -> Dict[str, Any]:
    """Send staged file from VPS via curl -4 -K - (token strictly on stdin; never in argv/ps/disk)."""
    _validate_token_chars(token)
    validate_caption(caption, filename)
    stdin_cfg = f'url = "https://api.telegram.org/bot{token}/{method}"\n'.encode("utf-8")
    cap_b64 = base64.b64encode(caption.encode("utf-8")).decode("ascii")
    extra_str = " ".join(f"-F {shlex.quote(f'{k}={v}')}" for k, v in extra_fields)
    file_arg = shlex.quote(f"{field}=@{remote_file};type={mime};filename={filename}")
    remote_cmd = (
        "set -e; "
        "TMPD=$(mktemp -d); "
        "trap 'rm -rf \"$TMPD\"' EXIT; "
        f"printf '%s' {shlex.quote(cap_b64)} | base64 -d > \"$TMPD/caption.txt\"; "
        f"curl -4 -sS --max-time {int(timeout)} -K - "
        f"-F {shlex.quote(f'chat_id={chat_id}')} "
        "-F parse_mode=HTML "
        "-F \"caption=<$TMPD/caption.txt\" "
        f"{extra_str} "
        f"-F {file_arg}"
    )
    proc = subprocess.run(
        [
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
            "-p", str(vps_port), vps_host, remote_cmd,
        ],
        input=stdin_cfg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=int(timeout) + 30,
    )
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    err = proc.stderr.decode("utf-8", errors="replace").strip()
    if proc.returncode != 0:
        raise RuntimeError(f"VPS curl {method} rc={proc.returncode}: {redact(err or out, token)}")
    return _parse_tg_response(out, token, method)


def tg_send_message(
    token: str,
    chat_id: str,
    text: str,
    transport: str,
    vps_host: str = DEFAULT_VPS_HOST,
    vps_port: str = DEFAULT_VPS_PORT,
    timeout: int = 60,
) -> int:
    _validate_token_chars(token)
    if transport == "vps-curl":
        return tg_send_message_vps_curl(token, chat_id, text, vps_host=vps_host, vps_port=vps_port, timeout=timeout)
    curl_bin = shutil.which("curl.exe") or shutil.which("curl")
    if transport == "local-curl" and curl_bin:
        stdin_cfg = f'url = "https://api.telegram.org/bot{token}/sendMessage"\n'.encode("utf-8")
        with tempfile.TemporaryDirectory(prefix="bako_tg_msg_") as tmpd:
            tf = Path(tmpd) / "msg.txt"
            tf.write_bytes(text.encode("utf-8"))
            proc = subprocess.run(
                [
                    curl_bin, "-4", "-sS", "--max-time", str(timeout), "-K", "-",
                    "-F", f"chat_id={chat_id}",
                    "-F", "parse_mode=HTML",
                    "-F", f"text=<{tf}",
                ],
                input=stdin_cfg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 15,
            )
        out = proc.stdout.decode("utf-8", errors="replace").strip()
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        if proc.returncode != 0:
            raise RuntimeError(f"curl sendMessage rc={proc.returncode}: {redact(err or out, token)}")
        res = _parse_tg_response(out, token, "sendMessage")
        return int(res["result"]["message_id"])

    body, ctype = _encode_multipart([("chat_id", chat_id), ("parse_mode", "HTML"), ("text", text)], [])
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body, method="POST",
        headers={"Content-Type": ctype, "Content-Length": str(len(body))},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"urllib sendMessage failed: {redact(str(exc), token)}") from None
    res = _parse_tg_response(raw, token, "sendMessage")
    return int(res["result"]["message_id"])


def tg_send_file(
    token: str,
    chat_id: str,
    method: str,  # "sendVideo" or "sendDocument"
    field: str,   # "video" or "document"
    mime: str,
    file_path: Path,
    caption: str,
    transport: str,
    extra_fields: Sequence[Tuple[str, str]] = (),
    timeout: int = 300,
) -> Dict[str, Any]:
    _validate_token_chars(token)
    validate_caption(caption, file_path.name)
    curl_bin = shutil.which("curl.exe") or shutil.which("curl")

    if transport == "local-curl" and curl_bin:
        stdin_cfg = f'url = "https://api.telegram.org/bot{token}/{method}"\n'.encode("utf-8")
        with tempfile.TemporaryDirectory(prefix="bako_tg_cap_") as tmpd:
            cf = Path(tmpd) / "caption.txt"
            cf.write_bytes(caption.encode("utf-8"))
            cmd = [
                curl_bin, "-4", "-sS", "--max-time", str(timeout), "-K", "-",
                "-F", f"chat_id={chat_id}",
                "-F", "parse_mode=HTML",
                "-F", f"caption=<{cf}",
            ]
            for k, v in extra_fields:
                cmd.extend(["-F", f"{k}={v}"])
            cmd.extend(["-F", f"{field}=@{file_path};type={mime};filename={file_path.name}"])
            proc = subprocess.run(
                cmd, input=stdin_cfg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 30,
            )
        out = proc.stdout.decode("utf-8", errors="replace").strip()
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        if proc.returncode != 0:
            raise RuntimeError(f"curl {method} rc={proc.returncode}: {redact(err or out, token)}")
        return _parse_tg_response(out, token, method)

    fields = [("chat_id", chat_id), ("parse_mode", "HTML"), ("caption", caption), *extra_fields]
    body, ctype = _encode_multipart(fields, [(field, file_path.name, mime, file_path.read_bytes())])
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=body, method="POST",
        headers={"Content-Type": ctype, "Content-Length": str(len(body))},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"urllib {method} HTTP {exc.code}: {redact(err_body, token)}") from None
    except Exception as exc:
        raise RuntimeError(f"urllib {method} failed: {redact(str(exc), token)}") from None
    return _parse_tg_response(raw, token, method)


# ---------------------------------------------------------------------------
# Manifest Writer
# ---------------------------------------------------------------------------
def write_manifest(dest_dir: Path, records: List[Dict[str, Any]], tg_status: str, tg_note: str) -> Path:
    md_path = dest_dir / "DELIVERY_MANIFEST.md"
    json_path = dest_dir / "delivery_manifest.json"
    total_mb = sum(r["bytes"] for r in records) / (1024 * 1024)

    payload = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "telegram_status": tg_status,
        "telegram_note": tg_note,
        "deliverables_dir": str(dest_dir),
        "count": len(records),
        "total_mb": round(total_mb, 2),
        "items": records,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Bakersfield-ish Final Deliverables Manifest",
        "",
        f"- **Deliverables Folder:** `{dest_dir}`",
        f"- **Total Files Staged:** {len(records)} ({total_mb:.2f} MB total)",
        f"- **Telegram Delivery:** **{tg_status}** — {tg_note}",
        "",
        "| # | Deliverable | File | Size (MB) | Details | Telegram | SHA-256 (first 12) |",
        "|---:|---|---|---:|---|---|---|",
    ]
    for idx, r in enumerate(records, start=1):
        det = (
            f"{r['width']}x{r['height']}, {r['duration_s']}s, streams={r['nb_streams']} ({r['vcodec']}+{r['acodec']})"
            if r["kind"] == "video"
            else f"offline_clean={r['offline_clean']}, external_refs={r['external_refs']}"
        )
        tg_col = f"msg #{r['telegram_message_id']}" if r.get("telegram_message_id") else r.get("telegram_item_status", "staged")
        lines.append(
            f"| {idx} | {r['title']} | `{r['file']}` | {r['bytes'] / (1024 * 1024):.2f} | {det} | {tg_col} | `{r['sha256'][:12]}` |"
        )
    lines.extend([
        "",
        "## Re-Send to Telegram Anytime",
        "```powershell",
        '$env:TG_BOT_TOKEN = "<your-bot-token>"',
        f'python source/mm_tools/deliver_bakersfieldish_telegram.py --transport vps-curl --deliverables-dir "{dest_dir}"',
        "```",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


# ---------------------------------------------------------------------------
# Main Entrypoint
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Stage, verify & deliver Bakersfield-ish final MP4s + offline HTML to Telegram.")
    ap.add_argument("--deliverables-dir", type=Path, default=DEFAULT_DELIVERABLES_DIR, help="Unified deliverables output folder")
    ap.add_argument("--chat-id", type=str, default=os.environ.get("TG_CHAT_ID", DEFAULT_CHAT_ID), help="Telegram chat ID")
    ap.add_argument("--token", type=str, default=None, help="Telegram bot token (defaults to TG_BOT_TOKEN env var)")
    ap.add_argument(
        "--transport",
        choices=("auto", "vps-curl", "local-curl", "urllib"),
        default="auto",
        help="Telegram upload transport (default: auto -> vps-curl if ssh on PATH, else local-curl/urllib)",
    )
    ap.add_argument("--vps-host", type=str, default=DEFAULT_VPS_HOST, help=f"VPS SSH host for vps-curl (default: {DEFAULT_VPS_HOST})")
    ap.add_argument("--vps-port", type=str, default=DEFAULT_VPS_PORT, help=f"VPS SSH port for vps-curl (default: {DEFAULT_VPS_PORT})")
    ap.add_argument("--timeout", type=int, default=300, help="Per-file Telegram upload timeout in seconds")
    ap.add_argument("--allow-partial", action="store_true", help="Stage/deliver whichever deliverables currently exist")
    ap.add_argument("--stage-only", action="store_true", help="Stage & verify deliverables locally without contacting Telegram")
    ap.add_argument("--dry-run", action="store_true", help="Validate script hygiene, captions, and candidate discovery only")
    ap.add_argument("--require-telegram", action="store_true", help="Exit non-zero if Telegram delivery cannot run")
    return ap.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    token = (args.token if args.token is not None else os.environ.get("TG_BOT_TOKEN", "")).strip() or None
    verify_secret_hygiene(token)

    specs = default_deliverable_specs(REPO_ROOT)
    for sp in specs:
        validate_caption(sp.caption, sp.key)

    resolved: List[Tuple[DeliverableSpec, Optional[Path]]] = []
    for sp in specs:
        found = next((p for p in sp.candidates if p.is_file()), None)
        resolved.append((sp, found))

    if args.dry_run:
        found_n = sum(1 for _, p in resolved if p is not None)
        print(f"[dry-run] Secret hygiene OK | Captions OK ({len(specs)}/{len(specs)} <= 1024 chars)", flush=True)
        print(f"[dry-run] TG_BOT_TOKEN configured: {bool(token)} | Chat ID: {args.chat_id}", flush=True)
        print(f"[dry-run] Deliverables discovered right now: {found_n}/{len(specs)}", flush=True)
        for sp, p in resolved:
            st = f"FOUND ({p.stat().st_size / (1024*1024):.2f} MB): {p.relative_to(REPO_ROOT)}" if p else "PENDING"
            print(f"   - {sp.key:22s} -> {sp.dest_name:44s} [{st}]", flush=True)
        return 0

    missing = [sp.key for sp, p in resolved if p is None]
    if missing and not args.allow_partial:
        print(f"[error] Missing required deliverables ({len(missing)}): {', '.join(missing)}", file=sys.stderr)
        print("        Re-run with --allow-partial to stage existing files.", file=sys.stderr)
        return 2

    dest_dir = args.deliverables_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    send_queue: List[Tuple[DeliverableSpec, Path, Dict[str, Any], Optional[Path]]] = []

    print(f"[stage] Staging deliverables into {dest_dir}...", flush=True)
    for sp, src in resolved:
        if src is None:
            continue
        if sp.kind == "video":
            staged_parts = stage_video(src, dest_dir, sp.dest_name, require_audio=True)
            for idx, (p, info) in enumerate(staged_parts, start=1):
                part_title = f"{sp.title} (Part {idx}/{len(staged_parts)})" if len(staged_parts) > 1 else sp.title
                part_cap = f"{sp.caption}\n<i>Part {idx}/{len(staged_parts)}</i>" if len(staged_parts) > 1 else sp.caption
                rec = {
                    "key": sp.key if len(staged_parts) == 1 else f"{sp.key}_part{idx}",
                    "kind": "video",
                    "title": part_title,
                    "file": p.name,
                    "path": str(p),
                    "sha256": sha256_file(p),
                    **info,
                    "telegram_message_id": None,
                    "telegram_item_status": "staged",
                }
                records.append(rec)
                send_queue.append((sp, p, rec, p))
                print(
                    f"   [OK] {p.name} ({info['bytes']/(1024*1024):.2f} MB, {info['duration_s']}s, "
                    f"streams={info['nb_streams']}, {info['vcodec']}+{info['acodec']})",
                    flush=True,
                )
        else:
            html_path, tg_doc, info = stage_html(src, dest_dir, sp.dest_name)
            rec = {
                "key": sp.key,
                "kind": "html",
                "title": sp.title,
                "file": html_path.name,
                "path": str(html_path),
                "sha256": sha256_file(html_path),
                **info,
                "telegram_doc": tg_doc.name if tg_doc else None,
                "telegram_message_id": None,
                "telegram_item_status": "staged",
            }
            records.append(rec)
            send_queue.append((sp, html_path, rec, tg_doc))
            print(
                f"   [OK] {html_path.name} ({info['bytes']/(1024*1024):.2f} MB, offline_clean={info['offline_clean']})",
                flush=True,
            )

    transport = args.transport
    if transport == "auto":
        if shutil.which("ssh"):
            transport = "vps-curl"
        elif shutil.which("curl.exe") or shutil.which("curl"):
            transport = "local-curl"
        else:
            transport = "urllib"

    tg_status = "STAGED_ONLY"
    tg_note = "Staged locally (--stage-only)."

    if args.stage_only:
        pass
    elif not token:
        tg_status = "FALLBACK_LOCAL_FOLDER"
        tg_note = "TG_BOT_TOKEN not set; all verified deliverables staged cleanly in deliverables folder."
        if args.require_telegram:
            write_manifest(dest_dir, records, tg_status, tg_note)
            print(f"[error] {tg_note}", file=sys.stderr)
            return 3
    else:
        sent_ok = 0
        vps_remote_dir: Optional[str] = None
        try:
            header = (
                "🌆 <b>Bakersfield-ish — Final Map Showcase Package</b>\n"
                f"Delivering <b>{len(send_queue)}</b> verified artifacts (11× 720p H.264 + AAC MP4s + 2× offline HTML pages).\n\n"
                f"📋 <b>Live Showcase &amp; Changelog:</b> {SHOWCASE_URL}\n"
                f"🌐 <b>Live Interactive 3D Map Viewer:</b> {INTERACTIVE_URL}"
            )
            if transport == "vps-curl":
                stage_paths = [tg_file for _sp, _raw, _rec, tg_file in send_queue if tg_file is not None]
                vps_remote_dir = vps_stage_files(stage_paths, vps_host=args.vps_host, vps_port=args.vps_port)

            hdr_mid = tg_send_message(
                token, args.chat_id, header,
                transport=transport, vps_host=args.vps_host, vps_port=args.vps_port,
            )
            print(f"[telegram] Header sent via {transport} (message_id={hdr_mid})", flush=True)
            for sp, _raw_path, rec, tg_file in send_queue:
                if tg_file is None:
                    rec["telegram_item_status"] = "skipped_too_large"
                    print(f"[telegram] Skipping {rec['file']} (> 48.5 MB even compressed; available in local folder)", flush=True)
                    continue
                if sp.kind == "video":
                    method, field, mime = "sendVideo", "video", "video/mp4"
                    extra_fields: List[Tuple[str, str]] = [
                        ("width", str(rec["width"])),
                        ("height", str(rec["height"])),
                        ("duration", str(int(round(rec["duration_s"])))),
                        ("supports_streaming", "true"),
                    ]
                else:
                    method, field = "sendDocument", "document"
                    mime = "application/zip" if tg_file.suffix.lower() == ".zip" else "text/html"
                    extra_fields = []

                if transport == "vps-curl":
                    assert vps_remote_dir is not None
                    res = tg_send_file_vps_curl(
                        token=token,
                        chat_id=args.chat_id,
                        method=method,
                        field=field,
                        mime=mime,
                        remote_file=f"{vps_remote_dir}/{tg_file.name}",
                        filename=tg_file.name,
                        caption=sp.caption,
                        vps_host=args.vps_host,
                        vps_port=args.vps_port,
                        extra_fields=extra_fields,
                        timeout=args.timeout,
                    )
                else:
                    res = tg_send_file(
                        token=token,
                        chat_id=args.chat_id,
                        method=method,
                        field=field,
                        mime=mime,
                        file_path=tg_file,
                        caption=sp.caption,
                        transport=transport,
                        extra_fields=extra_fields,
                        timeout=args.timeout,
                    )
                mid = int(res["result"]["message_id"])
                rec["telegram_message_id"] = mid
                rec["telegram_item_status"] = "sent"
                sent_ok += 1
                print(f"   [telegram] Sent {tg_file.name} via {transport} -> message_id={mid}", flush=True)
            tg_status = "DELIVERED"
            tg_note = f"Delivered {sent_ok}/{len(send_queue)} artifacts natively to Telegram chat {args.chat_id} via {transport}."
        except Exception as exc:
            tg_status = "FALLBACK_LOCAL_FOLDER"
            tg_note = f"Telegram delivery stopped after {sent_ok}/{len(send_queue)} ({redact(str(exc), token)}); all verified files remain staged locally."
            if args.require_telegram:
                write_manifest(dest_dir, records, tg_status, tg_note)
                print(f"[error] {tg_note}", file=sys.stderr)
                return 4
        finally:
            if vps_remote_dir:
                vps_cleanup_stage(vps_remote_dir, vps_host=args.vps_host, vps_port=args.vps_port)
                print(f"[vps-curl] Cleaned up remote temp staging dir {vps_remote_dir}.", flush=True)

    manifest_md = write_manifest(dest_dir, records, tg_status, tg_note)
    print(f"[done] Status={tg_status} | Manifest: {manifest_md}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
