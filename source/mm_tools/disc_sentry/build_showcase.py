"""Pack all 4 Disc Sentry Gun MD3s, textures, and redesigned scary WAV sounds into
a 100% self-contained interactive WebGL2 + WebAudio voting HTML at:
  docs/disc_sentry_vote.html

Also renders a 2x2 comparison sheet via Blender 5.2 (or PIL fallback) and optionally
deploys to VPS and sends to Telegram.

Usage:
    python source/mm_tools/disc_sentry/build_showcase.py
    python source/mm_tools/disc_sentry/build_showcase.py --deploy --telegram
"""
from __future__ import annotations

import argparse
import base64
import gzip
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
REPO_ROOT = MM_TOOLS.parents[1]
OUT_ROOT = MM_TOOLS / "out" / "disc_sentry"
TEX_DIR = OUT_ROOT / "tex"
MODEL_DIR = OUT_ROOT / "models"
SOUND_DIR = OUT_ROOT / "sounds"
RENDER_DIR = OUT_ROOT / "renders"

TEMPLATE_HTML = HERE / "disc_sentry_vote.template.html"
OUT_HTML = REPO_ROOT / "docs" / "disc_sentry_vote.html"
COMPARE_JPG = OUT_ROOT / "disc_sentry_concepts_compare.jpg"

BLENDER_EXE = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
VPS_HOST = "root@72.62.241.93"
VPS_WEBROOT = "/var/www/megaman"
LIVE_URL = "https://bakersfield.larrywew.fun/disc_sentry_vote.html"
CRED_SOURCE_SCRIPT = MM_TOOLS / "build_tank_showcase_and_deploy.py"

if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
import md3lib  # noqa: E402


class ArenaPacker:
    def __init__(self):
        self.buf = bytearray()

    def add_bytes(self, raw: bytes) -> list[int]:
        while len(self.buf) & 7:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(raw)
        return [off, len(raw)]


def _edges_for_tris(tri_arr: np.ndarray) -> np.ndarray:
    e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
    e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
    e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


def pack_md3(packer: ArenaPacker, md3_path: Path) -> dict:
    m = md3lib.read(str(md3_path))
    nf = m["nframes"]
    surfs_out = []
    for s in m["surfaces"]:
        nv = len(s["st"])
        nt = len(s["tris"])
        pos_i16 = np.zeros((nf, nv, 4), dtype="<i2")
        nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
        for fi, (vv, nn) in enumerate(s["frames"]):
            av = np.asarray(vv, dtype=np.float32)
            an = np.asarray(nn, dtype=np.float32)
            pos_i16[fi, :, :3] = np.clip(np.round(av * 64.0), -32767, 32767).astype("<i2")
            nl = np.maximum(np.linalg.norm(an, axis=1, keepdims=True), 1e-8)
            nrm_i8[fi, :, :3] = np.clip(np.round((an / nl) * 127.0), -127, 127).astype("<i1")

        uv_arr = np.asarray(s["st"], dtype="<f4")
        tri_arr = np.asarray(s["tris"], dtype="<u2")
        edge_arr = _edges_for_tris(tri_arr)

        sh = s["shader"].lower()
        tex_stem = os.path.splitext(os.path.basename(sh))[0]
        is_emissive = 1 if ("leds" in tex_stem or "_scr_" in tex_stem or s["name"] == "crt_screen") else 0

        surfs_out.append({
            "name": s["name"],
            "nv": nv,
            "nt": nt,
            "ne": len(edge_arr),
            "posScale": 1.0 / 64.0,
            "texKey": tex_stem,
            "emissive": is_emissive,
            "tris": packer.add_bytes(tri_arr.tobytes()),
            "edges": packer.add_bytes(edge_arr.tobytes()),
            "uv": packer.add_bytes(uv_arr.tobytes()),
            "pos": packer.add_bytes(pos_i16.tobytes()),
            "nrm": packer.add_bytes(nrm_i8.tobytes()),
        })
    return {"nframes": nf, "surfaces": surfs_out}


def encode_tex_uri(png_path: Path, max_dim: int = 1024, force_png: bool = False) -> str:
    im = Image.open(png_path).convert("RGB")
    w0, h0 = im.size
    if max(w0, h0) > max_dim:
        sc = max_dim / float(max(w0, h0))
        im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))), Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    if force_png:
        im.save(bio, "PNG", optimize=True)
        mime = "image/png"
    else:
        im.save(bio, "JPEG", quality=88, optimize=True)
        mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def build_html() -> Path:
    manifest = json.loads((OUT_ROOT / "models_manifest.json").read_text(encoding="utf-8"))
    s_manifest = json.loads((SOUND_DIR / "sounds_manifest.json").read_text(encoding="utf-8"))

    packer = ArenaPacker()
    textures = {}
    for png in sorted(TEX_DIR.glob("*.png")):
        stem = png.stem
        is_png = ("_scr_" in stem or "leds" in stem or "floppy" in stem)
        textures[stem] = encode_tex_uri(png, max_dim=1024 if "body" in stem else 512, force_png=is_png)

    concepts_out = []
    for c in manifest["concepts"]:
        cid = c["id"]
        concepts_out.append({
            **c,
            "base": pack_md3(packer, MODEL_DIR / c["base_md3"]),
            "turret": pack_md3(packer, MODEL_DIR / c["turret_md3"]),
            "floppy": pack_md3(packer, MODEL_DIR / c["floppy_md3"]),
            "gibs": [pack_md3(packer, MODEL_DIR / g) for g in c["gib_md3s"]],
            "crt_keys": {k: Path(v).stem for k, v in c["crt_screens"].items()},
        })

    sounds_out = {}
    for key, sinfo in s_manifest["sounds"].items():
        wav_bytes = (SOUND_DIR / sinfo["file"]).read_bytes()
        sounds_out[key] = {
            **sinfo,
            "b64": base64.b64encode(wav_bytes).decode("ascii"),
        }

    arena_bytes = bytes(packer.buf)
    payload = {
        "arena_b64": base64.b64encode(arena_bytes).decode("ascii"),
        "textures": textures,
        "concepts": concepts_out,
        "sounds": sounds_out,
    }

    tpl = TEMPLATE_HTML.read_text(encoding="utf-8")
    js_str = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = tpl.replace("/*__PAYLOAD_JSON__*/", js_str)

    # Guard against accidental external links or leaked credentials
    assert "http://" not in html and "https://" not in html, "External URL leaked into offline HTML!"

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    sz_mb = OUT_HTML.stat().st_size / (1024 * 1024)
    print(f"[build_showcase] Wrote {OUT_HTML} ({sz_mb:.2f} MB, arena={len(arena_bytes)/1024:.1f} KB)")
    return OUT_HTML


def render_blender_previews() -> Path:
    """Render crisp Blender 5.2 EEVEE hero 3/4 shots for all 4 concepts + composite 1920x1280 sheet."""
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((OUT_ROOT / "models_manifest.json").read_text(encoding="utf-8"))

    if BLENDER_EXE.is_file():
        script_path = OUT_ROOT / "_blender_render.py"
        blender_script = f'''
import json, math, os, sys
import bpy
sys.path.insert(0, {repr(str(MM_TOOLS))})
import md3lib

OUT_ROOT = {repr(str(OUT_ROOT))}
TEX_DIR = {repr(str(TEX_DIR))}
MODEL_DIR = {repr(str(MODEL_DIR))}
RENDER_DIR = {repr(str(RENDER_DIR))}
manifest = json.loads(open(os.path.join(OUT_ROOT, "models_manifest.json"), "r").read())

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def make_mat(name, png_path, emissive=False):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(png_path, check_existing=True)
    if emissive:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.45
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    else:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 0.44
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def add_md3_frame(md3_path, frame_idx, tex_overrides=None):
    m = md3lib.read(md3_path)
    objs = []
    for s in m["surfaces"]:
        vv, nn = s["frames"][frame_idx]
        mesh = bpy.data.meshes.new(s["name"])
        mesh.from_pydata(vv, [], s["tris"])
        uv_layer = mesh.uv_layers.new(name="UVMap")
        st = s["st"]
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                vi = mesh.loops[li].vertex_index
                u, v = st[vi]
                uv_layer.data[li].uv = (u, 1.0 - v)
        mesh.update()
        obj = bpy.data.objects.new(s["name"], mesh)
        bpy.context.collection.objects.link(obj)
        sh = os.path.splitext(os.path.basename(s["shader"]))[0]
        if tex_overrides and s["name"] in tex_overrides:
            sh = tex_overrides[s["name"]]
        emissive = ("leds" in sh or "_scr_" in sh or s["name"] == "crt_screen")
        mat = make_mat(sh, os.path.join(TEX_DIR, sh + ".png"), emissive=emissive)
        obj.data.materials.append(mat)
        objs.append(obj)
    return objs

for c in manifest["concepts"]:
    cid = c["id"]
    clear_scene()
    scn = bpy.context.scene
    scn.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in scn.render.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    scn.render.resolution_x = 920
    scn.render.resolution_y = 580
    scn.view_settings.view_transform = "Standard"

    # Studio world
    w = bpy.data.worlds.new("W")
    scn.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.025, 0.04, 0.075, 1.0)
        bg.inputs["Strength"].default_value = 0.7

    # Floor plane
    bpy.ops.mesh.primitive_plane_add(size=220, location=(0, 0, 0))
    fl = bpy.context.active_object
    fmat = bpy.data.materials.new("floor")
    fmat.use_nodes = True
    bsdf = fmat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.045, 0.065, 0.105, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.38
    fl.data.materials.append(fmat)

    # Lights
    for lpos, lrot, energy, col in [
        ((70, -65, 95), (0.7, 0.2, 0.7), 280000, (1.0, 0.96, 0.90)),
        ((-65, 65, 55), (1.0, -0.2, -2.3), 120000, (0.55, 0.78, 1.0)),
        ((-60, -40, 60), (0.9, 0.1, -0.8), 90000, (1.0, 0.75, 0.55)),
    ]:
        ldata = bpy.data.lights.new("L", type="AREA")
        ldata.energy = energy
        ldata.size = 45
        ldata.color = col
        lobj = bpy.data.objects.new("L", ldata)
        lobj.location = lpos
        lobj.rotation_euler = lrot
        bpy.context.collection.objects.link(lobj)

    add_md3_frame(os.path.join(MODEL_DIR, c["base_md3"]), 15)
    add_md3_frame(os.path.join(MODEL_DIR, c["turret_md3"]), 10)
    # Place 5 flying/scattered custom 3D floppy disks around the sentry for hero shot!
    for fpos, frot in [
        ((31, -14, 32), (0.15, 0.18, 0.25)),
        ((40, 14, 30), (-0.2, -0.1, -0.3)),
        ((28, 22, 1.5), (0.0, 0.0, 0.75)),
        ((24, -22, 1.5), (0.0, 0.0, -0.55)),
        ((46, -4, 24), (0.1, -0.15, 0.85)),
    ]:
        fobjs = add_md3_frame(os.path.join(MODEL_DIR, c["floppy_md3"]), 0)
        for fo in fobjs:
            fo.location = fpos
            fo.rotation_euler = frot

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 36
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scn.camera = cam_obj
    cam_obj.location = (104, -76, 54)
    direction = (-104 + 6, 76, -54 + 31)
    from mathutils import Vector
    cam_obj.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()

    out_png = os.path.join(RENDER_DIR, f"hero_{{cid}}.png")
    scn.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print("RENDERED", out_png)
'''
        script_path.write_text(blender_script, encoding="utf-8")
        print("[render] Rendering 4 Blender 5.2 hero shots...")
        subprocess.run([str(BLENDER_EXE), "-b", "--python", str(script_path)], check=True)

    # Composite 1920x1280 2x2 Comparison Sheet
    W, H = 1920, 1280
    canvas = Image.new("RGB", (W, H), (10, 15, 26))
    dr = ImageDraw.Draw(canvas)

    def _f(sz, bold=True):
        p = r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"
        return ImageFont.truetype(p, sz) if os.path.isfile(p) else ImageFont.load_default()

    dr.rectangle([0, 0, W, 86], fill=(14, 21, 36))
    dr.line([0, 86, W, 86], fill=(56, 189, 248), width=2)
    dr.text((24, 12), "DISC SENTRY GUN — 4 INTERACTIVE 3D CONCEPTS READY TO VOTE!", font=_f(32), fill=(241, 246, 255))
    dr.text((24, 52), "Retro 90s CRT + PC Tower + TF Sentry Gun + Custom 3D Floppy Projectiles + Bouncing Floppy Explosion + Scary SFX", font=_f(18, False), fill=(148, 163, 184))

    pad = 22
    cw = (W - pad * 3) // 2
    ch = (H - 120 - pad * 2) // 2
    for i, c in enumerate(manifest["concepts"]):
        col = i % 2
        row = i // 2
        x0 = pad + col * (cw + pad)
        y0 = 104 + row * (ch + pad)
        hero_p = RENDER_DIR / f"hero_{c['id']}.png"
        if hero_p.is_file():
            im = Image.open(hero_p).convert("RGB").resize((cw, ch - 82), Image.Resampling.LANCZOS)
            canvas.paste(im, (x0, y0))
        acc_hex = c["accent"].lstrip("#")
        acc = tuple(int(acc_hex[k:k+2], 16) for k in (0, 2, 4))
        dr.rectangle([x0, y0, x0 + cw, y0 + ch], outline=acc, width=3)
        dr.rectangle([x0, y0 + ch - 82, x0 + cw, y0 + ch], fill=(15, 22, 38))
        dr.text((x0 + 14, y0 + ch - 74), f"#{c['num']} {c['title'].upper()}  —  {c['floppy_name']}", font=_f(21), fill=acc)
        dr.text((x0 + 14, y0 + ch - 42), c["subtitle"], font=_f(16, False), fill=(218, 228, 242))

    dr.text((24, H - 30), f"Interactive 3D Preview + Scary SFX: {LIVE_URL}", font=_f(17), fill=(52, 211, 153))
    canvas.save(COMPARE_JPG, "JPEG", quality=90, optimize=True)
    print(f"[render] Saved comparison sheet -> {COMPARE_JPG} ({COMPARE_JPG.stat().st_size/1024:.1f} KB)")
    return COMPARE_JPG


def deploy_to_vps() -> None:
    print(f"[deploy] Uploading {OUT_HTML.name} to {VPS_HOST}:{VPS_WEBROOT}/ ...")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=4) as tf:
        tf.add(OUT_HTML, arcname="disc_sentry_vote.html")
    payload = buf.getvalue()
    remote_cmd = (
        f"set -e; tar -xzf - -C {VPS_WEBROOT} && "
        f"chmod a+r {VPS_WEBROOT}/disc_sentry_vote.html && "
        f"ls -lh {VPS_WEBROOT}/disc_sentry_vote.html"
    )
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-p", "22", VPS_HOST, remote_cmd],
        input=payload, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True,
    )
    print(" ", proc.stdout.decode("utf-8", errors="replace").strip())
    req = urllib.request.Request(LIVE_URL, method="HEAD", headers={"User-Agent": "DiscSentryVerifier/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        print(f"  [HTTP {resp.status}] {LIVE_URL}")
        assert resp.status == 200


def _load_telegram_creds() -> tuple[str, str]:
    tok = os.environ.get("TG_TOKEN", "").strip()
    cid = os.environ.get("TG_CHAT_ID", "").strip()
    if tok and cid:
        return tok, cid
    src = CRED_SOURCE_SCRIPT.read_text(encoding="utf-8", errors="replace")
    m_tok = re.search(r'^\s*TG_TOKEN\s*=\s*["\']([^"\']+)["\']', src, re.M)
    m_cid = re.search(r'^\s*TG_CHAT_ID\s*=\s*["\']([^"\']+)["\']', src, re.M)
    assert m_tok and m_cid
    return m_tok.group(1), m_cid.group(1)


def _tg_json(token: str, method: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    assert res.get("ok") is True, f"Telegram {method} error: {res}"
    return res


def send_telegram() -> None:
    print("[telegram] Sending comparison sheet, interactive HTML file, live link & poll...")
    token, chat_id = _load_telegram_creds()

    # 1. Send 2x2 Blender Comparison Photo
    cap = (
        "🖥️🔫 <b>Disc Sentry Gun Redesign — 4 Interactive 3D Concepts Ready!</b>\n\n"
        "• <b>1 · Retro Computer Sentry:</b> Balanced 486 + TF Level 2 tripod &amp; twin floppy pods\n"
        "• <b>2 · Classic Retro Style:</b> Authentic 1994 AT tower, speaker-cannons &amp; stacked disk rack\n"
        "• <b>3 · Badass Weapon Design:</b> Armored gunmetal twin 6-barrel Gatlings &amp; roll-caged CRT\n"
        "• <b>4 · MS-DOS Machine Gun:</b> Bright MS-DOS 6.22 CRT + quad barrels spraying floppy storms!"
    )
    subprocess.run([
        "curl.exe", "-sS", "--max-time", "120",
        "-F", f"chat_id={chat_id}",
        "-F", f"caption={cap}",
        "-F", "parse_mode=HTML",
        "-F", f"photo=@{COMPARE_JPG}",
        f"https://api.telegram.org/bot{token}/sendPhoto",
    ], check=True)

    # 2. Send self-contained HTML preview document directly!
    doc_cap = (
        "Interactive 3D WebGL2 + WebAudio Preview (open directly in browser!). "
        "Includes all 4 concepts, custom 3D floppy projectiles, throw-to-transform, 85-floppy bouncing explosion &amp; scary SFX!"
    )
    subprocess.run([
        "curl.exe", "-sS", "--max-time", "180",
        "-F", f"chat_id={chat_id}",
        "-F", f"caption={doc_cap}",
        "-F", f"document=@{OUT_HTML};type=text/html",
        f"https://api.telegram.org/bot{token}/sendDocument",
    ], check=True)

    # 3. Live HTTPS link + summary
    msg = (
        "🕹️ <b>Live Interactive 3D Preview &amp; Voting Studio:</b>\n"
        f"👉 {LIVE_URL}\n\n"
        "<b>What to test inside the preview:</b>\n"
        "• 📀 <b>Throw &amp; Transform</b> — watch the 3.5&quot; disc land &amp; morph into each computer sentry\n"
        "• 🔥 <b>Fire Floppies</b> — shoots custom 3D floppy disks (Concept 4 sprays them everywhere!)\n"
        "• 💥 <b>EXPLODE!</b> — detonates into 85+ individual bouncing 3D floppy disks + computer gibs\n"
        "• 🔊 <b>Scary Redesigned SFX</b> — terrifying CRT degauss transform, klaxon lock, heavy cannon/MG fire &amp; mega explosion\n\n"
        "Vote below or copy your detailed feedback from the HTML ballot!"
    )
    _tg_json(token, "sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

    # 4. Native Poll
    _tg_json(token, "sendPoll", {
        "chat_id": chat_id,
        "question": "Which Disc Sentry Gun 3D concept direction should we build for BakersfieldQuake?",
        "options": [
            {"text": "1 · Retro Computer Sentry (Balanced 486 + TF Tripod)"},
            {"text": "2 · Classic Retro Style (1994 AT Tower + Speaker Cannons)"},
            {"text": "3 · Badass Weapon Design (Armored Twin Gatling Shredder)"},
            {"text": "4 · MS-DOS Machine Gun (MS-DOS CRT + Chaotic Floppy Storm)"},
            {"text": "Mashup (I'll send notes/ballot from the HTML preview!)"},
        ],
        "is_anonymous": False,
        "allows_multiple_answers": False,
        "type": "regular",
    })
    print("[telegram] All 4 Telegram messages sent cleanly!")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--telegram", action="store_true")
    ap.add_argument("--skip-render", action="store_true")
    args = ap.parse_args()

    build_html()
    if not args.skip_render:
        render_blender_previews()
    if args.deploy:
        deploy_to_vps()
    if args.telegram:
        send_telegram()


if __name__ == "__main__":
    main()
