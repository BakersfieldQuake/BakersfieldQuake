"""Deploys the 'Jar o' Green Guys' (Impulse 62) 60 FPS Weapon & 12-Gremlin Swarm Showcase
to VPS root@72.62.241.93:22 (/var/www/megaman/), verifies HTTPS endpoints, and sends Telegram preview
to David (@HelloDavid99).

Live URLs:
  https://bakersfield.larrywew.fun/green_guy_jar_weapon.html
  https://bakersfield.larrywew.fun/green-guy-jar/
  https://bakersfield.larrywew.fun/green-guy-jar/greenjar_poster.jpg
  https://bakersfield.larrywew.fun/green-guy-jar/greenjar_preview.gif
"""
from __future__ import annotations

import io
import json
import mimetypes
import os
import subprocess
import sys
import tarfile
import time
import urllib.request
import uuid

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PACK_DIR = os.path.join(MOD_ROOT, "green_guy_jar_weapon")
HTML_FILE = os.path.join(MOD_ROOT, "green_guy_jar_weapon.html")

BOT_TOKEN = "8930587733:AAGhpBMINk6vadL6IPxmKBjIJJ_GwB-31Uc"
CHAT_ID = "1071627213"


def build_deployment_tar() -> bytes:
    print("[1/4] Building compressed in-memory deployment tar.gz archive...")
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz", compresslevel=1) as tf:
        tf.add(HTML_FILE, arcname="green_guy_jar_weapon.html")
        tf.add(os.path.join(PACK_DIR, "greenjar_poster.jpg"), arcname="green-guy-jar/greenjar_poster.jpg")
        tf.add(os.path.join(PACK_DIR, "greenjar_preview.gif"), arcname="green-guy-jar/greenjar_preview.gif")
        tf.add(os.path.join(PACK_DIR, "manifest.json"), arcname="green-guy-jar/manifest.json")
        shot_dir = os.path.join(PACK_DIR, "screenshots")
        if os.path.isdir(shot_dir):
            for fn in sorted(os.listdir(shot_dir)):
                tf.add(os.path.join(shot_dir, fn), arcname=f"green-guy-jar/screenshots/{fn}")
        atlas_dir = os.path.join(PACK_DIR, "atlases")
        for fn in sorted(os.listdir(atlas_dir)):
            tf.add(os.path.join(atlas_dir, fn), arcname=f"green-guy-jar/atlases/{fn}")
    tar_bytes = tar_buf.getvalue()
    print(f"  -> Archive size: {len(tar_bytes) / (1024 * 1024):.2f} MB")
    return tar_bytes


def deploy_to_vps(tar_bytes: bytes) -> None:
    print("[2/4] Streaming deployment archive to root@72.62.241.93:22...")
    t0 = time.perf_counter()
    remote_script = (
        "rm -rf /var/www/megaman/green-guy-jar && "
        "mkdir -p /var/www/megaman/green-guy-jar/atlases /var/www/megaman/green-guy-jar/screenshots && "
        "tar -xzf - -C /var/www/megaman && "
        "ln -sf /var/www/megaman/green_guy_jar_weapon.html /var/www/megaman/green-guy-jar/index.html && "
        "chmod -R a+rX /var/www/megaman/green_guy_jar_weapon.html /var/www/megaman/green-guy-jar && "
        "ls -lh /var/www/megaman/green_guy_jar_weapon.html /var/www/megaman/green-guy-jar/"
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
        "https://bakersfield.larrywew.fun/green_guy_jar_weapon.html",
        "https://bakersfield.larrywew.fun/green-guy-jar/",
        "https://bakersfield.larrywew.fun/green-guy-jar/greenjar_poster.jpg",
        "https://bakersfield.larrywew.fun/green-guy-jar/greenjar_preview.gif",
    ]
    for url in urls:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "BakersfieldQuakeVerifier/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            cl = resp.headers.get("Content-Length", "unknown")
            ct = resp.headers.get("Content-Type", "unknown")
            print(f"  [PASS] {resp.status} {url} ({cl} bytes, {ct})")


def send_telegram_notification() -> None:
    print("[4/4] Sending Telegram preview & live links to @HelloDavid99...")
    poster_path = os.path.join(PACK_DIR, "greenjar_poster.jpg")
    gif_path = os.path.join(PACK_DIR, "greenjar_preview.gif")

    caption = (
        "🫙🟢 JAR O' GREEN GUYS (Impulse 62) — 60 FPS Live-Action Quake Swarm Weapon Ready!\n\n"
        "✅ Held Optical Jar Sprite (v_greenjar.md3): Swirling neon-green mist + 4 manic spaz antics, Hold-Fire Cocktail-Shaker & Whip-Throw!\n"
        "✅ Green-Smoke Shatter -> 12 Mini-Gremlins: Fast floor zoomers, pogo-bouncers & vertical building wall-climbers!\n"
        "✅ 5-Orbit View-Blocking Swarm: Circles victims 5x jumping in their face (1%-2% non-lethal pokes, NEVER kills) -> Rainbow Confetti Pop!\n"
        "✅ 1-Shot Helium Spin + Voice Pack: Shoot any gremlin for a 360° cartwheel spin into confetti + helium laughing & giggling!\n\n"
        "🌐 Interactive 3D Swarm & Shooting Gallery HTML:\n"
        "https://bakersfield.larrywew.fun/green_guy_jar_weapon.html\n"
        "📦 Asset Pack & Live Quake Shots:\n"
        "https://bakersfield.larrywew.fun/green-guy-jar/"
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
    _multipart_post(
        "sendAnimation",
        {
            "chat_id": CHAT_ID,
            "caption": "60 FPS Preview: Held Jar Spaz & Cocktail-Shake → Green Smoke Shatter → Wall-Climbing & 5x Face-Swarm → 1-Shot Helium Spin → Rainbow Confetti Pop!",
        },
        "animation",
        gif_path,
    )


if __name__ == "__main__":
    archive = build_deployment_tar()
    deploy_to_vps(archive)
    verify_live_endpoints()
    send_telegram_notification()
