"""Upload Kyle Tillet HTML showcases to VPS (root@72.62.241.93:22:/var/www/megaman/),
verify live HTTPS endpoints, and notify @HelloDavid99 on Telegram.

Does NOT touch /opt/quake or restart any Quake server.
"""

import io
import json
import os
import subprocess
import sys
import tarfile
import urllib.request
import uuid
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
COMPLETE_HTML = REPO / "docs" / "kyle_complete_showcase.html"
SHOWCASE_HTML = REPO / "docs" / "kyle_weapon_showcase.html"
PROJ_HTML = REPO / "docs" / "kyle_projectile_showcase.html"
SOUND_HTML = REPO / "docs" / "kyle_scissors_sound_preview.html"
AUDIT_JPG = (
    Path(__file__).resolve().parent / "assets" / "pocket_kyle_hd" / "_audit_ik_progression.jpg"
)
PROJ_AUDIT_JPG = (
    Path(__file__).resolve().parent / "assets" / "sprites" / "_audit_studio_final.jpg"
)
PREVIEW_JPG = AUDIT_JPG

VPS_HOST = "root@72.62.241.93"
BASE_URL = "https://bakersfield.larrywew.fun"
BOT_TOKEN = "8930587733:AAGhpBMINk6vadL6IPxmKBjIJJ_GwB-31Uc"
CHAT_ID = "1071627213"


def make_preview_jpg() -> Path:
    return PREVIEW_JPG


def upload_to_vps(projectile_only: bool = False) -> None:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=4) as tf:
        if COMPLETE_HTML.exists():
            tf.add(COMPLETE_HTML, arcname="kyle_complete_showcase.html")
        if not projectile_only:
            tf.add(SHOWCASE_HTML, arcname="kyle_weapon_showcase.html")
            tf.add(SOUND_HTML, arcname="kyle_scissors_sound_preview.html")
        if PROJ_HTML.exists():
            tf.add(PROJ_HTML, arcname="kyle_projectile_showcase.html")
    payload = buf.getvalue()
    print(f"Uploading {len(payload) / (1024 * 1024):.2f} MB to {VPS_HOST}:/var/www/megaman/ ...")

    remote_cmd = (
        "mkdir -p /var/www/megaman/kyle-weapon /var/www/megaman/kyle && "
        "tar -xzf - -C /var/www/megaman && "
        "ln -sf /var/www/megaman/kyle_complete_showcase.html /var/www/megaman/kyle/index.html && "
        "ln -sf /var/www/megaman/kyle_weapon_showcase.html /var/www/megaman/kyle-weapon/index.html && "
        "chmod a+r /var/www/megaman/kyle_complete_showcase.html /var/www/megaman/kyle_weapon_showcase.html /var/www/megaman/kyle_scissors_sound_preview.html /var/www/megaman/kyle_projectile_showcase.html && "
        "chmod -R a+rX /var/www/megaman/kyle-weapon /var/www/megaman/kyle && "
        "ls -lh /var/www/megaman/kyle_complete_showcase.html /var/www/megaman/kyle_weapon_showcase.html /var/www/megaman/kyle_projectile_showcase.html /var/www/megaman/kyle_scissors_sound_preview.html"
    )
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-p", "22", VPS_HOST, remote_cmd],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    print(proc.stdout.decode("utf-8", errors="replace"))


def verify_https() -> None:
    urls = [
        f"{BASE_URL}/kyle_complete_showcase.html",
        f"{BASE_URL}/kyle/",
        f"{BASE_URL}/kyle_weapon_showcase.html",
        f"{BASE_URL}/kyle-weapon/",
        f"{BASE_URL}/kyle_projectile_showcase.html",
        f"{BASE_URL}/kyle_scissors_sound_preview.html",
    ]
    print("Verifying live HTTPS endpoints:")
    for u in urls:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "KyleShowcaseVerifier/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            cl = resp.headers.get("Content-Length", "?")
            print(f"  [HTTP {resp.status}] {u} ({cl} bytes)")
            assert resp.status == 200, f"Unexpected status {resp.status} for {u}"


def send_telegram(photo_path: Path, projectile: bool = False) -> None:
    caption = (
        "THE POCKET KYLE — Complete Animations, POV Gun Tuner & In-Game Polish!\n\n"
        "In-Game Fixes Just Compiled:\n"
        "- Milky-style propelled throw: cock-back squeeze -> explosive whip -> launches right off your open palm twirling 180 deg!\n"
        "- Unique Sky Throw (aim up): soars high chopping giant scissors OVERHEAD (and dives onto nearby enemies/John Bird!)\n"
        "- Active ground running/roaming (MOVETYPE_STEP + walkmove) when nobody is around — no more standing still!\n"
        "- Smaller realistic US $100 bills & 2024 coins — ONLY erupt when Kyle successfully hits someone!\n\n"
        f"All-in-One Showcase (Weapon + POV + Studio Projectiles + Money + Sounds):\n{BASE_URL}/kyle_complete_showcase.html\n\n"
        f"Dedicated Quake POV Gun Positioning Tuner:\n{BASE_URL}/kyle_weapon_showcase.html\n\n"
        f"Studio Projectiles & US Currency:\n{BASE_URL}/kyle_projectile_showcase.html\n\n"
        f"Clean Soundboard (17 WAVs):\n{BASE_URL}/kyle_scissors_sound_preview.html"
    )
    boundary = f"----Antigravity{uuid.uuid4().hex}"
    body = bytearray()
    for k, v in {"chat_id": CHAT_ID, "caption": caption}.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8"))
    fdata = photo_path.read_bytes()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="photo"; filename="{photo_path.name}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: image/jpeg\r\n\r\n")
    body.extend(fdata)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    print("Telegram sendPhoto:", json.dumps({"ok": res.get("ok"), "message_id": res.get("result", {}).get("message_id")}))
    assert res.get("ok") is True, f"Telegram error: {res}"


def main() -> None:
    photo = PROJ_AUDIT_JPG if PROJ_AUDIT_JPG.exists() else make_preview_jpg()
    upload_to_vps(projectile_only=False)
    verify_https()
    send_telegram(photo, projectile=False)


if __name__ == "__main__":
    main()
