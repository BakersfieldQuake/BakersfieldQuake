"""Deploys the Green-Suit Wheelman 60 FPS 360° (16-Angle) Live-Action Sprite Monster
to VPS root@72.62.241.93:22 (/var/www/megaman/) and verifies live HTTPS endpoints.

Live URLs:
  https://bakersfield.larrywew.fun/greensuit_wheelman_monster.html
  https://bakersfield.larrywew.fun/greensuit-monster/
  https://bakersfield.larrywew.fun/greensuit-monster/turnaround_and_accuracy_poster.jpg
  https://bakersfield.larrywew.fun/greensuit-monster/greensuit_monster_360_preview.gif
  https://bakersfield.larrywew.fun/greensuit-monster/greensuit_wheelman.spr32
"""
from __future__ import annotations

import io
import json
import mimetypes
import os
import subprocess
import tarfile
import time
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PACK_DIR = os.path.join(MOD_ROOT, "greensuit_wheelman_monster")
HTML_FILE = os.path.join(MOD_ROOT, "greensuit_wheelman_monster.html")
SPR32_FILE = os.path.join(MOD_ROOT, "progs", "greensuit_wheelman.spr32")

BOT_TOKEN = "8930587733:AAGhpBMINk6vadL6IPxmKBjIJJ_GwB-31Uc"
CHAT_ID = "1071627213"


def build_deployment_tar() -> bytes:
    print("[1/4] Building compressed in-memory deployment tar.gz archive...")
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz", compresslevel=1) as tf:
        tf.add(HTML_FILE, arcname="greensuit_wheelman_monster.html")
        tf.add(os.path.join(PACK_DIR, "turnaround_and_accuracy_poster.jpg"), arcname="greensuit-monster/turnaround_and_accuracy_poster.jpg")
        tf.add(os.path.join(PACK_DIR, "greensuit_monster_360_preview.gif"), arcname="greensuit-monster/greensuit_monster_360_preview.gif")
        tf.add(os.path.join(PACK_DIR, "sprite_meta.json"), arcname="greensuit-monster/sprite_meta.json")
        atlas_dir = os.path.join(PACK_DIR, "atlases")
        for fn in sorted(os.listdir(atlas_dir)):
            tf.add(os.path.join(atlas_dir, fn), arcname=f"greensuit-monster/atlases/{fn}")
        tf.add(SPR32_FILE, arcname="greensuit-monster/greensuit_wheelman.spr32")
    tar_bytes = tar_buf.getvalue()
    print(f"  -> Archive size: {len(tar_bytes) / (1024 * 1024):.2f} MB")
    return tar_bytes


def deploy_to_vps(tar_bytes: bytes) -> None:
    print("[2/4] Streaming deployment archive to root@72.62.241.93:22...")
    t0 = time.perf_counter()
    remote_script = (
        "rm -rf /var/www/megaman/greensuit-monster && "
        "mkdir -p /var/www/megaman/greensuit-monster/atlases && "
        "tar -xzf - -C /var/www/megaman && "
        "ln -sf /var/www/megaman/greensuit_wheelman_monster.html /var/www/megaman/greensuit-monster/index.html && "
        "chmod -R a+rX /var/www/megaman/greensuit_wheelman_monster.html /var/www/megaman/greensuit-monster && "
        "ls -lh /var/www/megaman/greensuit_wheelman_monster.html /var/www/megaman/greensuit-monster/"
    )
    cmd = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        "-p", "22",
        "root@72.62.241.93",
        remote_script,
    ]
    proc = subprocess.run(cmd, input=tar_bytes, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    print(proc.stdout.decode("utf-8", errors="replace"))
    print(f"  -> VPS extraction finished in {time.perf_counter() - t0:.1f}s!")


def verify_live_endpoints() -> None:
    print("[3/4] Verifying live HTTPS endpoints on https://bakersfield.larrywew.fun/ ...")
    urls = [
        "https://bakersfield.larrywew.fun/greensuit_wheelman_monster.html",
        "https://bakersfield.larrywew.fun/greensuit-monster/",
        "https://bakersfield.larrywew.fun/greensuit-monster/turnaround_and_accuracy_poster.jpg",
        "https://bakersfield.larrywew.fun/greensuit-monster/greensuit_monster_360_preview.gif",
        "https://bakersfield.larrywew.fun/greensuit-monster/greensuit_wheelman.spr32",
    ]
    for url in urls:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "BakersfieldQuakeVerifier/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            cl = resp.headers.get("Content-Length", "unknown")
            ct = resp.headers.get("Content-Type", "unknown")
            print(f"  [PASS] {resp.status} {url} ({cl} bytes, {ct})")


def send_telegram_notification() -> None:
    print("[4/4] Sending Telegram preview & live links to @HelloDavid99...")
    poster_path = os.path.join(PACK_DIR, "turnaround_and_accuracy_poster.jpg")
    gif_path = os.path.join(PACK_DIR, "greensuit_monster_360_preview.gif")

    caption = (
        "🟢🛞 GREEN-SUIT WHEELMAN MONSTER — 60 FPS 360° (16-Angle) Live-Action Sprite Ready!\n\n"
        "✅ All old 3D models of Wheelman & Green-Suit Wheelman deleted cleanly (local + VPS)\n"
        "✅ 100% Real Photo-Digitized Live-Action Sprite (4,224 frames @ 60 FPS across 16 angles every 22.5°)\n"
        "✅ 7 Animations: Seated Low-Rider Cruise, Screaming Ab-Roller Charge, Pipe-Vault Mid-Air Crane-Kick Sky-Point Slam, 360° Whirlwind Melee, Wheelie Taunt, Pain Skid & 3D Quake Mega-Gibs (bouncing tires + stainless pipe!)\n"
        "✅ Wired into BakersfieldQuake (`progs/greensuit_wheelman.spr32` + `progs.dat`, `impulse 46`)\n\n"
        "🌐 Self-Contained Interactive HTML5 Showcase:\n"
        "https://bakersfield.larrywew.fun/greensuit_wheelman_monster.html\n"
        "📦 Asset Directory & Raw Sheets:\n"
        "https://bakersfield.larrywew.fun/greensuit-monster/"
    )

    def _multipart_post(endpoint: str, fields: dict, file_field: str, file_path: str) -> None:
        boundary = f"----AntigravityBoundary{uuid.uuid4().hex}"
        body = bytearray()
        for k, v in fields.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8"))
        fn = os.path.basename(file_path)
        ctype = mimetypes.guess_type(fn)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            fdata = f.read()
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{file_field}"; filename="{fn}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {ctype}\r\n\r\n".encode())
        body.extend(fdata)
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}"
        req = urllib.request.Request(url, data=bytes(body), method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"  -> Telegram {endpoint}: ok={res.get('ok')}")

    _multipart_post("sendPhoto", {"chat_id": CHAT_ID, "caption": caption}, "photo", poster_path)
    _multipart_post("sendAnimation", {"chat_id": CHAT_ID, "caption": "360° @ 60 FPS Preview: Seated Cruise → Ab-Roller Charge → Pipe-Vault Sky-Point Slam → Whirlwind → Quake Gibs!"}, "animation", gif_path)


if __name__ == "__main__":
    archive = build_deployment_tar()
    deploy_to_vps(archive)
    verify_live_endpoints()
    send_telegram_notification()
