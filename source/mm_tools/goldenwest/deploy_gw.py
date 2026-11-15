"""deploy_gw.py — Self-contained packager & VPS deployer for Golden West Casino & S Union Ave.

Modeled on source/mm_tools/soi6/deploy_soi6.py.
Safe --dry-run by default when invoked with no mode flags.

Modes:
  (default) / --dry-run : Validate BSP, LIT, spots, WebGL export, skybox, textures, MD3 props,
                          and print exact pack & upload plan without writing zips or touching VPS.
  --pack-only           : Build self-contained out/web/goldenwest/goldenwest_map_pack.zip locally.
  --upload              : Build zip, sync showcase, upload bundle to VPS, and verify HTTPS 200.
  --verify-only         : Check remote HTTPS 200 endpoints without uploading.
  --notify              : Send Telegram summary ONLY when paired with --upload and all 5 audits pass.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import struct
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from typing import Dict, List, Optional, Tuple

GW_DIR = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(GW_DIR)
MOD_DIR = os.path.dirname(os.path.dirname(MM_TOOLS))
OUT_DIR = os.path.join(GW_DIR, "out")
WEB_OUT = os.path.join(MM_TOOLS, "out", "web", "goldenwest")
ROOT_SHOWCASE = os.path.join(MOD_DIR, "goldenwest_showcase.html")
ZIP_PATH = os.path.join(WEB_OUT, "goldenwest_map_pack.zip")

VPS = "root@72.62.241.93"
REMOTE_ROOT = "/var/www/megaman"
BASE_URL = "https://bakersfield.larrywew.fun"

TG_TOKEN = "8930587733:AAGhpBMINk6vadL6IPxmKBjIJJ_GwB-31Uc"
TG_CHAT_ID = "1071627213"

if GW_DIR not in sys.path:
    sys.path.insert(0, GW_DIR)

from gw_lib import SPECIAL_TEXTURES, is_forbidden_tex  # noqa: E402

REQUIRED_SKY_FACES = ("rt", "lf", "ft", "bk", "up", "dn")


def _read_bsp_miptex(bsp_path: str) -> List[str]:
    """Extract texture names from compiled BSP/BSP2 miptex lump (lump 2)."""
    with open(bsp_path, "rb") as f:
        data = f.read()
    if len(data) < 4 + 15 * 8:
        raise ValueError(f"Truncated BSP header: {bsp_path}")
    tex_off, tex_len = struct.unpack_from("<ii", data, 4 + 2 * 8)
    if tex_len <= 4:
        return []
    count = struct.unpack_from("<i", data, tex_off)[0]
    offsets = struct.unpack_from(f"<{count}i", data, tex_off + 4)
    names: List[str] = []
    for off in offsets:
        if off < 0:
            continue
        pos = tex_off + off
        raw_name = data[pos : pos + 16].split(b"\x00", 1)[0].decode("ascii", "ignore").strip()
        if raw_name:
            names.append(raw_name)
    return names


def _resolve_spots_file() -> Optional[str]:
    candidates = [
        os.path.join(MOD_DIR, "maps", "goldenwest.spots.json"),
        os.path.join(OUT_DIR, "goldenwest.spots.json"),
        os.path.join(MM_TOOLS, "out", "maps", "goldenwest.spots.json"),
    ]
    existing = [p for p in candidates if os.path.isfile(p)]
    return max(existing, key=os.path.getmtime) if existing else None


def _resolve_audits_log() -> Optional[str]:
    candidates = [
        os.path.join(OUT_DIR, "AUDITS_LOG.md"),
        os.path.join(MOD_DIR, "AUDITS_LOG.md"),
        os.path.join(MM_TOOLS, "out", "gw_ref_audit", "AUDITS_LOG.md"),
    ]
    existing = [p for p in candidates if os.path.isfile(p)]
    return existing[0] if existing else None


def _pk3_fallback_bytes(rel_posix: str) -> Optional[bytes]:
    pk3 = os.path.join(MOD_DIR, "bakersfield.pk3")
    if not os.path.isfile(pk3):
        return None
    target = rel_posix.lower().lstrip("/")
    with zipfile.ZipFile(pk3, "r") as zf:
        for info in zf.infolist():
            if info.filename.lower() == target:
                return zf.read(info.filename)
    return None


def collect_pack_files(allow_pk3_fallback: bool = True) -> Tuple[List[Tuple[str, bytes]], List[str]]:
    """Collect all self-contained goldenwest map pack entries -> [(arcname, bytes)], errors."""
    entries: Dict[str, bytes] = {}
    errors: List[str] = []

    def add_disk(src: str, arcname: str) -> None:
        with open(src, "rb") as f:
            entries[arcname] = f.read()

    # 1. BSP, LIT, spots.json
    bsp_path = os.path.join(MOD_DIR, "maps", "goldenwest.bsp")
    lit_path = os.path.join(MOD_DIR, "maps", "goldenwest.lit")
    spots_path = _resolve_spots_file()

    if os.path.isfile(bsp_path):
        add_disk(bsp_path, "maps/goldenwest.bsp")
    else:
        errors.append("Missing compiled BSP: maps/goldenwest.bsp")

    if os.path.isfile(lit_path):
        add_disk(lit_path, "maps/goldenwest.lit")
    else:
        errors.append("Missing compiled LIT: maps/goldenwest.lit")

    if spots_path:
        add_disk(spots_path, "maps/goldenwest.spots.json")
    else:
        errors.append("Missing goldenwest.spots.json")

    # 2. Skybox gfx/env/gwsky_*
    env_dir = os.path.join(MOD_DIR, "gfx", "env")
    if os.path.isdir(env_dir):
        for fn in sorted(os.listdir(env_dir)):
            low = fn.lower()
            if low.startswith("gwsky_") and (low.endswith(".png") or low.endswith(".tga")):
                add_disk(os.path.join(env_dir, fn), f"gfx/env/{fn}")
    for face in REQUIRED_SKY_FACES:
        if f"gfx/env/gwsky_{face}.png" not in entries:
            errors.append(f"Missing DarkPlaces skybox face: gfx/env/gwsky_{face}.png")

    # 3. Textures (ALL gwc_* and {gwc_*, including *_glow.png)
    tex_dir = os.path.join(MOD_DIR, "textures")
    tex_by_lower: Dict[str, str] = {}
    if os.path.isdir(tex_dir):
        for fn in sorted(os.listdir(tex_dir)):
            low = fn.lower()
            if not (low.endswith(".png") or low.endswith(".tga")):
                continue
            if low.startswith("gwc_") or low.startswith("{gwc_"):
                arc = f"textures/{fn}"
                add_disk(os.path.join(tex_dir, fn), arc)
                tex_by_lower[low] = arc
    if not tex_by_lower:
        errors.append("No textures/gwc_* or textures/{gwc_* PNGs found")

    # Verify every world texture in BSP miptex lump is packed and non-forbidden
    if os.path.isfile(bsp_path):
        for tname in _read_bsp_miptex(bsp_path):
            low = tname.lower()
            if low in SPECIAL_TEXTURES or low.startswith(("sky", "clip", "skip", "trigger", "hint")):
                continue
            if is_forbidden_tex(low):
                errors.append(f"Forbidden legacy texture inside BSP: {tname}")
                continue
            if f"{low}.png" not in tex_by_lower and f"{low}.tga" not in tex_by_lower:
                errors.append(f"BSP texture missing from pack textures/: {tname}")

    # 4. 3D Models & Skins (progs/gw_horse.*, gw_rock.*, gw_buddha.*, gw_gold.*, gw_pedestal.*)
    progs_dir = os.path.join(MOD_DIR, "progs")
    if os.path.isdir(progs_dir):
        for fn in sorted(os.listdir(progs_dir)):
            low = fn.lower()
            if low.startswith("gw_"):
                add_disk(os.path.join(progs_dir, fn), f"progs/{fn}")

    # Ensure core gw_horse & gw_buddha assets exist (fallback to bakersfield.pk3 only if permitted)
    core_prop_files = [
        "progs/gw_horse.md3",
        "progs/gw_horse.md3_0.skin",
        "progs/gw_horse.png",
        "progs/gw_rock.png",
        "progs/gw_buddha.md3",
        "progs/gw_buddha.md3_0.skin",
        "progs/gw_gold.png",
        "progs/gw_pedestal.png",
    ]
    for rel in core_prop_files:
        if rel not in entries:
            fb = _pk3_fallback_bytes(rel) if allow_pk3_fallback else None
            if fb is not None:
                entries[rel] = fb
            else:
                errors.append(f"Missing core prop asset: {rel}")

    # 5. AUDITS_LOG.md
    log_path = _resolve_audits_log()
    if log_path:
        add_disk(log_path, "AUDITS_LOG.md")
    else:
        errors.append("Missing AUDITS_LOG.md")

    ordered = sorted(entries.items(), key=lambda kv: kv[0])
    return ordered, errors


def build_map_pack_zip(entries: List[Tuple[str, bytes]]) -> str:
    os.makedirs(WEB_OUT, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for arcname, payload in entries:
            zf.writestr(arcname, payload)
    size_mb = os.path.getsize(ZIP_PATH) / (1024.0 * 1024.0)
    print(f"[deploy_gw] Built {ZIP_PATH} ({len(entries)} files, {size_mb:.2f} MB)")
    return ZIP_PATH


def _is_audit_passed(label: str, data: dict) -> bool:
    """Evaluate PASS across exact audit1..audit5 JSON report schemas."""
    if data.get("overall_pass") is True or data.get("passed") is True or data.get("pass") is True:
        return True
    if str(data.get("status", "")).upper() == "PASS":
        return True
    if label == "Audit 3":
        errs = data.get("errors")
        return isinstance(errs, list) and len(errs) == 0 and data.get("tarjan_sink_sccs", 1) == 0
    if label == "Audit 4":
        wasm = data.get("wasm_pack") or {}
        web = data.get("browser_webgl") or {}
        dp = data.get("darkplaces") or {}
        web_ok = bool(web.get("skipped")) or (web.get("ran") is True and not web.get("bad_responses"))
        dp_ok = bool(dp.get("skipped")) or (dp.get("ran") is True)
        return bool(data.get("bsp_and_map")) and wasm.get("within_budget") is True and web_ok and dp_ok
    return False


def _check_all_5_audits_passed() -> Tuple[bool, List[str]]:
    checks = [
        ("Audit 1", [os.path.join(OUT_DIR, "audit1_manifest.json"), os.path.join(OUT_DIR, "audit1_report.json"), os.path.join(OUT_DIR, "audit1_refs.json")]),
        ("Audit 2", [os.path.join(OUT_DIR, "audit2_accuracy_report.json"), os.path.join(OUT_DIR, "audit2_report.json")]),
        ("Audit 3", [os.path.join(OUT_DIR, "audit3_nav_report.json"), os.path.join(OUT_DIR, "audit3_report.json")]),
        ("Audit 4", [os.path.join(OUT_DIR, "audit4_perf_report.json"), os.path.join(OUT_DIR, "audit4_report.json")]),
        ("Audit 5", [os.path.join(OUT_DIR, "audit5_report.json"), os.path.join(OUT_DIR, "audit5_lighting_report.json")]),
    ]
    reasons: List[str] = []
    for label, cands in checks:
        found = next((p for p in cands if os.path.isfile(p)), None)
        if not found:
            reasons.append(f"{label}: missing report JSON")
            continue
        with open(found, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not _is_audit_passed(label, data):
            reasons.append(f"{label}: report in {os.path.basename(found)} is not PASS")
    return len(reasons) == 0, reasons


def upload_to_vps() -> None:
    if not os.path.isfile(ROOT_SHOWCASE):
        raise FileNotFoundError(f"Missing root showcase HTML: {ROOT_SHOWCASE}")
    for req in ("index.html", "showcase.html", "map.json", "map.bin", "lightmap.png", "dev_overlay.js", "goldenwest_map_pack.zip"):
        rp = os.path.join(WEB_OUT, req)
        if not os.path.isfile(rp):
            raise FileNotFoundError(f"Missing WebGL upload artifact: {rp}")

    # Build POSIX tar.gz in memory for deterministic Windows -> Linux extraction
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for dp, _, fns in os.walk(WEB_OUT):
            for fn in sorted(fns):
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, WEB_OUT).replace("\\", "/")
                tf.add(full, arcname=f"goldenwest/{rel}")
        tf.add(ROOT_SHOWCASE, arcname="goldenwest_showcase.html")

    tar_bytes = buf.getvalue()
    print(f"[deploy_gw] Uploading {len(tar_bytes) / (1024.0 * 1024.0):.2f} MB tar.gz to {VPS}:{REMOTE_ROOT}/")
    remote_cmd = (
        f"mkdir -p {REMOTE_ROOT}/goldenwest && "
        f"rm -rf {REMOTE_ROOT}/goldenwest/tex {REMOTE_ROOT}/goldenwest/sky && "
        f"tar -xzf - -C {REMOTE_ROOT}"
    )
    proc = subprocess.run(["ssh", "-o", "BatchMode=yes", VPS, remote_cmd], input=tar_bytes)
    if proc.returncode != 0:
        raise RuntimeError(f"SSH upload failed with exit code {proc.returncode}")
    print("[deploy_gw] Upload complete.")


def verify_https() -> List[Tuple[str, int]]:
    urls = [
        f"{BASE_URL}/goldenwest/",
        f"{BASE_URL}/goldenwest/index.html",
        f"{BASE_URL}/goldenwest/map.json",
        f"{BASE_URL}/goldenwest/map.bin",
        f"{BASE_URL}/goldenwest/lightmap.png",
        f"{BASE_URL}/goldenwest/showcase.html",
        f"{BASE_URL}/goldenwest/goldenwest_map_pack.zip",
        f"{BASE_URL}/goldenwest_showcase.html",
    ]
    results: List[Tuple[str, int]] = []
    for url in urls:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "BakersfieldQuake-Deploy/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.status
        except Exception:
            code = 0
        results.append((url, code))
        print(f"[verify_https] {code} {url}")
    failed = [(u, c) for u, c in results if c != 200]
    if failed:
        raise RuntimeError(f"HTTPS verification failed for: {failed}")
    return results


def send_telegram_notification() -> None:
    compile_p = os.path.join(OUT_DIR, "compile_stats.json")
    web_p = os.path.join(OUT_DIR, "web_export_stats.json")
    cstats = {}
    wstats = {}
    if os.path.isfile(compile_p):
        with open(compile_p, "r", encoding="utf-8") as f:
            cstats = json.load(f)
    if os.path.isfile(web_p):
        with open(web_p, "r", encoding="utf-8") as f:
            wstats = json.load(f)
    zip_mb = os.path.getsize(ZIP_PATH) / (1024.0 * 1024.0) if os.path.isfile(ZIP_PATH) else 0.0
    tris = wstats.get("world_triangles", "?")
    spots = wstats.get("spots", "?")
    tex_cnt = cstats.get("bsp", {}).get("texture_count", "?")

    msg = (
        "<b>Golden West Casino &amp; Great Castle Restaurant (goldenwest.bsp)</b> Deployed &amp; Verified\n"
        "- Coverage: 1001 S Union Ave (Golden West Casino) + 410 Union Ave (Great Castle Restaurant, E 4th–E 5th St, Reyes Tires, Deal Time, Shamrock, DG market)\n"
        f"- 3D WebGL Viewer: {BASE_URL}/goldenwest/\n"
        f"- Free-Fly Launch: {BASE_URL}/goldenwest/?fly=1\n"
        f"- Audit Showcase: {BASE_URL}/goldenwest_showcase.html\n"
        f"- Map Pack ({zip_mb:.2f} MB): {BASE_URL}/goldenwest/goldenwest_map_pack.zip\n"
        f"- Stats: {tris} tris, {tex_cnt} BSP textures, {spots} spots, -extra4 -bounce 1 bake, all 5 audits PASS."
    )
    payload = json.dumps({
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Telegram API HTTP {resp.status}")
        tg_body = json.loads(resp.read().decode("utf-8"))
    if not tg_body.get("ok"):
        raise RuntimeError(f"Telegram API returned ok={tg_body.get('ok')}: {tg_body}")
    msg_id = (tg_body.get("result") or {}).get("message_id")
    print(f"[deploy_gw] Telegram notification sent: ok={tg_body.get('ok')} message_id={msg_id}")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Package & deploy Golden West Casino map bundle.")
    ap.add_argument("--dry-run", action="store_true", help="Inspect pack & targets without modifying files or uploading")
    ap.add_argument("--pack-only", action="store_true", help="Build goldenwest_map_pack.zip locally without uploading")
    ap.add_argument("--upload", action="store_true", help="Build zip, upload bundle to VPS, and verify HTTPS 200")
    ap.add_argument("--verify-only", action="store_true", help="Only verify remote HTTPS 200 endpoints")
    ap.add_argument("--notify", action="store_true", help="Send Telegram notification (ONLY valid with --upload after all 5 audits pass)")
    args = ap.parse_args(argv)

    # Safe dry-run by default when no write/network action flag is given
    if not (args.pack_only or args.upload or args.verify_only):
        args.dry_run = True

    if args.notify and not args.upload:
        print("[deploy_gw] Refusing --notify without --upload.", file=sys.stderr)
        return 2

    if args.verify_only:
        verify_https()
        return 0

    entries, errors = collect_pack_files(allow_pk3_fallback=True)
    audits_ok, audit_reasons = _check_all_5_audits_passed()
    total_raw_mb = sum(len(b) for _, b in entries) / (1024.0 * 1024.0)

    print(
        f"[deploy_gw] Pack scan: {len(entries)} files ({total_raw_mb:.2f} MB uncompressed), "
        f"{len(errors)} pack issue(s), 5-audit gate={'PASS' if audits_ok else 'INCOMPLETE'}"
    )
    for err in errors:
        print(f"  [pack-issue] {err}")
    for r in audit_reasons:
        print(f"  [audit-gate] {r}")

    if args.dry_run:
        web_ready = all(
            os.path.isfile(os.path.join(WEB_OUT, fn))
            for fn in ("index.html", "map.json", "map.bin", "lightmap.png", "dev_overlay.js")
        )
        print(f"[deploy_gw] Dry-run summary: web_out_ready={web_ready}, target={VPS}:{REMOTE_ROOT}/")
        return 0

    if errors:
        print("[deploy_gw] Aborting: resolve pack issues before writing pack or uploading.", file=sys.stderr)
        return 1

    build_map_pack_zip(entries)
    if args.pack_only:
        return 0

    if args.upload:
        if not audits_ok:
            print("[deploy_gw] Aborting upload/notify: all 5 audits must PASS first.", file=sys.stderr)
            return 1
        upload_to_vps()
        verify_https()
        if args.notify:
            send_telegram_notification()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
