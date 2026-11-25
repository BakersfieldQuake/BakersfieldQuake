#!/usr/bin/env python3
"""Deploy Bakersfield-ish map, mod files & standalone HTML pages to VPS root@72.62.241.93:22.

Uploads:
  Game / Server (/opt/quake/BakersfieldQuake/):
    - maps/bakersfieldish.bsp
    - maps/bakersfieldish.lit
    - zz_bakersfieldish.pk3
    - progs.dat, progs.lno, csprogs.dat, menu.dat
    - effectinfo.txt, server.cfg
    (Never touches base bakersfield.pk3 or q15.pk3; backs up existing server files first!)
  Web (/var/www/megaman/ and /var/www/larrywew/bakersfield-quake/ if present):
    - bakersfieldish_showcase.html
    - bakersfieldish_interactive.html

Checks `ss -unp | grep ':26000'` before restarting `quake-bakersfield.service` so active
players are never kicked (unless `--force-restart` is explicitly passed), and verifies
HTTP 200 on every live URL via HEAD/curl.

Usage:
  python source/mm_tools/deploy_bakersfieldish_vps.py --dry-run
  python source/mm_tools/deploy_bakersfieldish_vps.py
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path
from typing import List, Tuple

HERE = Path(__file__).resolve().parent
MOD_DIR = HERE.parents[1]
DELIV_DIR = MOD_DIR / "docs" / "bakersfieldish_deliverables"

VPS_HOST = "root@72.62.241.93"
VPS_PORT = "22"

GAME_REL_FILES = [
    "maps/bakersfieldish.bsp",
    "maps/bakersfieldish.lit",
    "zz_bakersfieldish.pk3",
    "progs.dat",
    "progs.lno",
    "csprogs.dat",
    "menu.dat",
    "effectinfo.txt",
    "server.cfg",
]

BACKUP_FILES = [
    "progs.dat",
    "progs.lno",
    "csprogs.dat",
    "menu.dat",
    "effectinfo.txt",
    "server.cfg",
    "zz_bakersfieldish.pk3",
]

WEB_FILES = [
    ("bakersfieldish_showcase.html", DELIV_DIR / "bakersfieldish_showcase.html"),
    ("bakersfieldish_interactive.html", DELIV_DIR / "bakersfieldish_interactive.html"),
]

PRIMARY_BASE = "https://bakersfield.larrywew.fun"
MIRROR_BASE = "https://davidbrazil.site/megaman"
LARRYWEW_BASE = "https://larrywew.fun/bakersfield-quake"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def verify_http_200(url: str, expected_bytes: int) -> Tuple[int, int]:
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "BakersfieldishDeployVerifier/1.0", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = int(resp.status)
        cl = resp.headers.get("Content-Length")
        actual = int(cl.strip()) if (cl and cl.strip().isdigit()) else -1
    if status != 200:
        raise AssertionError(f"HEAD {url} returned HTTP {status}, expected 200")
    if actual >= 0 and actual != expected_bytes:
        raise AssertionError(f"HEAD {url} Content-Length {actual} != expected {expected_bytes}")
    return status, actual


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy Bakersfield-ish map, mod & HTML showcase pages to VPS.")
    ap.add_argument("--host", default=VPS_HOST, help=f"SSH host (default: {VPS_HOST})")
    ap.add_argument("--port", default=VPS_PORT, help=f"SSH port (default: {VPS_PORT})")
    ap.add_argument("--dry-run", action="store_true", help="Validate local files only without SSH upload")
    ap.add_argument("--force-restart", action="store_true", help="Restart quake-bakersfield.service even if peers exist")
    args = ap.parse_args()

    game_items: List[Tuple[Path, str]] = []
    for rel in GAME_REL_FILES:
        p = MOD_DIR / rel
        if not p.is_file():
            raise FileNotFoundError(f"Missing required game file: {p}")
        game_items.append((p, rel))

    web_items: List[Tuple[str, Path]] = []
    for name, p in WEB_FILES:
        if not p.is_file():
            raise FileNotFoundError(f"Missing required HTML file: {p}")
        web_items.append((name, p))

    print(f"[1/4] Verified {len(game_items)} game files + {len(web_items)} web HTML pages:", flush=True)
    for p, rel in game_items:
        print(f"  [game] {rel:26s} {p.stat().st_size / (1024*1024):6.2f} MB  sha256={sha256_file(p)[:12]}", flush=True)
    for name, p in web_items:
        print(f"  [web ] {name:26s} {p.stat().st_size / (1024*1024):6.2f} MB  sha256={sha256_file(p)[:12]}", flush=True)

    if args.dry_run:
        print("[dry-run] All local files verified. Skipping SSH upload.", flush=True)
        return 0

    print("[2/4] Packing streaming tar.gz payload (never touching base bakersfield.pk3 / q15.pk3)...", flush=True)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=3) as tf:
        for p, rel in game_items:
            tf.add(str(p), arcname="bq_game/" + rel)
        for name, p in web_items:
            tf.add(str(p), arcname="web/" + name)
    payload = buf.getvalue()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    print(f"   Tarball size: {len(payload) / (1024*1024):.2f} MB -> streaming to {args.host}:{args.port}...", flush=True)

    backup_list = " ".join(BACKUP_FILES)
    restart_block = (
        "systemctl restart quake-bakersfield.service; sleep 3; "
        "echo \"SERVICE_STATUS=$(systemctl is-active quake-bakersfield.service)\"; "
        if args.force_restart
        else
        "PEERS=$(ss -unp | grep ':26000' || true); "
        "if [ -z \"$PEERS\" ]; then "
        "  systemctl restart quake-bakersfield.service; sleep 3; "
        "  echo \"SERVICE_STATUS=$(systemctl is-active quake-bakersfield.service)\"; "
        "else "
        "  echo \"PLAYERS_ACTIVE_SKIPPED_RESTART:\"; echo \"$PEERS\"; "
        "  echo \"SERVICE_STATUS=$(systemctl is-active quake-bakersfield.service)\"; "
        "fi; "
    )

    remote_cmd = (
        "set -e; "
        "TMPD=$(mktemp -d); "
        "trap 'rm -rf \"$TMPD\"' EXIT; "
        "tar -xzf - -C \"$TMPD\"; "
        "QDIR=/opt/quake/BakersfieldQuake; "
        f"BK=/opt/quake/backup/{stamp}-bakersfieldish; "
        "mkdir -p \"$BK\" \"$QDIR/maps\"; "
        f"for f in {backup_list}; do "
        "  if [ -f \"$QDIR/$f\" ]; then cp -p \"$QDIR/$f\" \"$BK/$f\"; fi; "
        "done; "
        "echo \"BACKUP_DIR=$BK\"; "
        "cp -f \"$TMPD/bq_game/maps/bakersfieldish.bsp\" \"$QDIR/maps/bakersfieldish.bsp\"; "
        "cp -f \"$TMPD/bq_game/maps/bakersfieldish.lit\" \"$QDIR/maps/bakersfieldish.lit\"; "
        "for f in zz_bakersfieldish.pk3 progs.dat progs.lno csprogs.dat menu.dat effectinfo.txt server.cfg; do "
        "  cp -f \"$TMPD/bq_game/$f\" \"$QDIR/$f\"; "
        "done; "
        "chown quake:quake \"$QDIR/maps/bakersfieldish.bsp\" \"$QDIR/maps/bakersfieldish.lit\" "
        "\"$QDIR/zz_bakersfieldish.pk3\" \"$QDIR/progs.dat\" \"$QDIR/progs.lno\" "
        "\"$QDIR/csprogs.dat\" \"$QDIR/menu.dat\" \"$QDIR/effectinfo.txt\" \"$QDIR/server.cfg\"; "
        "chmod 644 \"$QDIR/maps/bakersfieldish.bsp\" \"$QDIR/maps/bakersfieldish.lit\" "
        "\"$QDIR/zz_bakersfieldish.pk3\" \"$QDIR/progs.dat\" \"$QDIR/progs.lno\" "
        "\"$QDIR/csprogs.dat\" \"$QDIR/menu.dat\" \"$QDIR/effectinfo.txt\" \"$QDIR/server.cfg\"; "
        "if [ -d /var/www/megaman ]; then "
        "  cp -f \"$TMPD/web/bakersfieldish_showcase.html\" /var/www/megaman/bakersfieldish_showcase.html; "
        "  cp -f \"$TMPD/web/bakersfieldish_interactive.html\" /var/www/megaman/bakersfieldish_interactive.html; "
        "  chmod 644 /var/www/megaman/bakersfieldish_showcase.html /var/www/megaman/bakersfieldish_interactive.html; "
        "  echo MEGAMAN_WEB_OK=1; "
        "fi; "
        "if [ -d /var/www/larrywew/bakersfield-quake ]; then "
        "  cp -f \"$TMPD/web/bakersfieldish_showcase.html\" /var/www/larrywew/bakersfield-quake/bakersfieldish_showcase.html; "
        "  cp -f \"$TMPD/web/bakersfieldish_interactive.html\" /var/www/larrywew/bakersfield-quake/bakersfieldish_interactive.html; "
        "  chmod 644 /var/www/larrywew/bakersfield-quake/bakersfieldish_showcase.html /var/www/larrywew/bakersfield-quake/bakersfieldish_interactive.html; "
        "  echo LARRYWEW_WEB_OK=1; "
        "else "
        "  echo LARRYWEW_WEB_OK=0; "
        "fi; "
        + restart_block +
        "journalctl -u quake-bakersfield --since '-20 sec' --no-pager | tail -n 35; "
        "ls -lh \"$QDIR/maps/bakersfieldish.bsp\" \"$QDIR/maps/bakersfieldish.lit\" \"$QDIR/zz_bakersfieldish.pk3\" \"$QDIR/progs.dat\" \"$QDIR/csprogs.dat\" \"$QDIR/menu.dat\""
    )

    print("[3/4] Uploading & installing on VPS over SSH...", flush=True)
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "-p", str(args.port), args.host, remote_cmd],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    out_txt = proc.stdout.decode("utf-8", errors="replace")
    print(out_txt, flush=True)

    for err_kw in ("Host_Error", "Failed to load", "couldn't load", "Mod_LoadModel", "Segmentation", "PRVM_"):
        if err_kw.lower() in out_txt.lower():
            print(f"[ERROR] Detected engine error keyword in server log: {err_kw}", file=sys.stderr)
            return 2

    larrywew_ok = "LARRYWEW_WEB_OK=1" in out_txt
    print("[4/4] Verifying live HTTP 200 URLs...", flush=True)
    url_checks: List[Tuple[str, int]] = []
    for name, p in web_items:
        sz = p.stat().st_size
        url_checks.append((f"{PRIMARY_BASE}/{name}", sz))
        url_checks.append((f"{MIRROR_BASE}/{name}", sz))
        if larrywew_ok:
            url_checks.append((f"{LARRYWEW_BASE}/{name}", sz))

    for url, expected in url_checks:
        st, actual = verify_http_200(url, expected)
        print(f"   [HTTP {st}] {url} ({actual:,} bytes)", flush=True)

    print("[SUCCESS] Bakersfield-ish map/mod + showcase & interactive HTML deployed and HTTP-verified!", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
