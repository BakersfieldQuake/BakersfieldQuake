"""Builds the self-contained WebGL2 + Canvas Kyle Tillet Weapon & Sprite Design Studio.

Reads generated staging assets from:
  - assets/weapons/manifest.json
  - assets/sprites/manifest.json
  - assets/sfx/manifest.json

Packs all 5 animated 3D MD3 viewmodels, PNG skins, 4x8-dir Kyle sprites, cash FX,
synthesized WAV SFX, and cleaned Kyle voice clips into a single offline HTML file:
  docs/kyle_weapon_showcase.html
"""

import argparse
import base64
import gzip
import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(MM_TOOLS))

DEFAULT_STAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
TEMPLATE_HTML = os.path.join(HERE, "kyle_weapon_showcase.template.html")
DEFAULT_OUT_HTML = os.path.join(REPO, "docs", "kyle_weapon_showcase.html")

sys.path.insert(0, MM_TOOLS)
import md3lib


WEAPON_STYLE_META = {
    "v_kyle_v1_cannon": {
        "code": "V1",
        "badge": "PROTOTYPE 1 · PRESSURE CANNON",
        "accent": "#ffb454",
        "accentRgb": [1.0, 0.71, 0.33],
        "orbitAz": 2.38,
        "orbitEl": 0.28,
        "presets": [
            ["3/4 Hero", 2.38, 0.28, 24.0],
            ["Glass Head Tank", 1.72, 0.42, 20.5],
            ["Scissor Muzzle", 0.35, 0.16, 21.0],
            ["Top Brass", 2.10, 1.15, 24.0],
        ],
    },
    "v_kyle_v2_hand": {
        "code": "V2",
        "badge": "PROTOTYPE 2 · KINETIC DART",
        "accent": "#fb7185",
        "accentRgb": [0.98, 0.44, 0.52],
        "orbitAz": 2.30,
        "orbitEl": 0.26,
        "presets": [
            ["3/4 Grip", 2.30, 0.26, 21.5],
            ["Overhead Shears", 1.45, 0.48, 19.5],
            ["Front Face", 0.18, 0.14, 19.0],
            ["Top View", 2.00, 1.16, 22.0],
        ],
    },
    "v_kyle_v3_register": {
        "code": "V3",
        "badge": "PROTOTYPE 3 · CASH REGISTER",
        "accent": "#34d399",
        "accentRgb": [0.20, 0.83, 0.60],
        "orbitAz": 2.42,
        "orbitEl": 0.32,
        "presets": [
            ["3/4 Register", 2.42, 0.32, 24.5],
            ["Side Crank", 1.55, 0.20, 22.0],
            ["Cash Drawer", 0.30, 0.12, 22.5],
            ["Top Keys", 2.15, 1.15, 24.5],
        ],
    },
    "v_kyle_v4_shears": {
        "code": "V4",
        "badge": "PROTOTYPE 4 · BARBER RAILGUN",
        "accent": "#38bdf8",
        "accentRgb": [0.22, 0.74, 0.97],
        "orbitAz": 2.36,
        "orbitEl": 0.28,
        "presets": [
            ["3/4 Shears", 2.36, 0.28, 24.0],
            ["Barber Core", 1.65, 0.32, 20.0],
            ["Blade Tips", 0.32, 0.14, 21.5],
            ["Top Hinge", 2.05, 1.15, 23.5],
        ],
    },
    "v_kyle_v5_invoice": {
        "code": "V5",
        "badge": "PROTOTYPE 5 · PAPER PLANE",
        "accent": "#c084fc",
        "accentRgb": [0.75, 0.52, 0.99],
        "orbitAz": 2.34,
        "orbitEl": 0.34,
        "presets": [
            ["3/4 Clipboard", 2.34, 0.34, 23.5],
            ["$100 Glider", 1.85, 0.68, 20.5],
            ["Nose & Kyle", 0.35, 0.22, 20.0],
            ["Top Invoice", 2.10, 1.18, 23.5],
        ],
    },
}

SPRITE_DESCRIPTIONS = {
    "running_scissors": "8-direction x 6-frame classic running-with-scissors sprint cycle (foot-anchored 192px RGBA).",
    "overhead_scissors": "8-direction x 4-frame overhead barber-shear chop with blade glint (used in flight & peripheral latch).",
    "front_scissors": "8-direction x 4-frame forward-extended jaw chop & lunge with metallic slash glint.",
    "no_scissors": "8-direction x 2-frame unarmed wander/idle cycle (after being shaken off or disarmed).",
}


class BinaryPacker:
    """Packs aligned typed WebGL2 buffers + deduplicated PNG textures."""

    def __init__(self):
        self.buf = bytearray()
        self.tex_map = {}
        self.tex_list = []

    def add_bytes(self, b):
        while len(self.buf) & 3:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(b)
        return [off, len(b)]

    def add_texture(self, key, path, label):
        if key in self.tex_map:
            return self.tex_map[key]
        im = Image.open(path)
        im.load()
        w, h = im.size
        has_alpha = im.mode in ("RGBA", "LA")
        bio = io.BytesIO()
        im.save(bio, "PNG", optimize=True)
        uri = "data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[key] = idx
        self.tex_list.append({
            "key": key,
            "label": label,
            "file": os.path.basename(path),
            "w": w,
            "h": h,
            "alpha": has_alpha,
            "uri": uri,
        })
        return idx


def png_data_uri(path):
    """Encode an existing PNG file cleanly as a base64 data URI."""
    with open(path, "rb") as fh:
        raw = fh.read()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def wav_data_uri(path):
    """Encode a WAV file cleanly as a base64 data URI."""
    with open(path, "rb") as fh:
        raw = fh.read()
    return "data:audio/wav;base64," + base64.b64encode(raw).decode("ascii")


def pack_weapon_models(weapons_dir, packer):
    """Read weapons/manifest.json + all 5 MD3 files and pack GPU buffers."""
    manifest_path = os.path.join(weapons_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        wman = json.load(fh)

    tex_ids = {}
    for key, fname in wman["textures"].items():
        fpath = os.path.join(weapons_dir, fname)
        assert os.path.isfile(fpath), f"Missing weapon texture: {fpath}"
        tex_ids[key] = packer.add_texture(key, fpath, f"Weapon Skin: {key}")

    models_out = []
    for entry in wman["models"]:
        md3_path = os.path.join(weapons_dir, entry["md3"])
        assert os.path.isfile(md3_path), f"Missing MD3: {md3_path}"
        parsed = md3lib.read(md3_path)
        nf = parsed["nframes"]
        assert nf >= 30, f"{entry['id']} has only {nf} frames (<30)"

        meta_surfs = {s["name"]: s for s in entry["surfaces"]}
        surfs_out = []
        tot_v, tot_t = 0, 0

        for ps in parsed["surfaces"]:
            sname = ps["name"]
            sm = meta_surfs.get(sname, {})
            mat_name = sm.get("material", "metals")
            if mat_name not in tex_ids:
                # Fallback match by texture filename
                tex_file = sm.get("texture", "")
                matched = [k for k, fn in wman["textures"].items() if fn == tex_file]
                mat_name = matched[0] if matched else next(iter(tex_ids))

            nv = len(ps["st"])
            nt = len(ps["tris"])
            tot_v += nv
            tot_t += nt

            uv_arr = np.asarray(ps["st"], dtype=np.float32)
            tri_arr = np.asarray(ps["tris"], dtype=np.uint16)
            e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
            e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
            e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
            edges = np.unique(np.vstack([e01, e12, e20]), axis=0).astype(np.uint16)

            pos_f = np.zeros((nf, nv, 3), dtype=np.float32)
            nrm_i8 = np.zeros((nf, nv, 3), dtype=np.int8)
            for fi, (vv, nn) in enumerate(ps["frames"]):
                pos_f[fi] = np.asarray(vv, dtype=np.float32)
                nrm_i8[fi] = np.clip(np.round(np.asarray(nn, dtype=np.float32) * 127.0), -127, 127).astype(np.int8)

            surfs_out.append({
                "name": sname,
                "mat": mat_name,
                "tex": tex_ids[mat_name],
                "nv": nv,
                "nt": nt,
                "ne": len(edges),
                "uv": packer.add_bytes(uv_arr.tobytes()),
                "tris": packer.add_bytes(tri_arr.tobytes()),
                "edges": packer.add_bytes(edges.tobytes()),
                "pos": packer.add_bytes(pos_f.tobytes()),
                "nrm": packer.add_bytes(nrm_i8.tobytes()),
                "metallic": float(sm.get("metallic", 0.35)),
                "roughness": float(sm.get("roughness", 0.40)),
                "spec": float(sm.get("spec", 0.70)),
                "cutout": int(sm.get("alphaTest", 0)),
                "translucent": int(sm.get("translucent", 0)),
                "unlit": int(sm.get("unlit", 0)),
                "additive": int(sm.get("additive", 0)),
                "twoSided": int(sm.get("twoSided", 1)),
                "alphaMul": 1.0,
            })

        style = WEAPON_STYLE_META.get(entry["id"], {})
        fr = entry["frameRanges"]
        models_out.append({
            "id": entry["id"],
            "code": style.get("code", entry["id"]),
            "badge": style.get("badge", entry["id"]),
            "title": entry["title"],
            "tagline": entry["subtitle"],
            "flavor": entry["flavor"],
            "md3Short": entry["md3"],
            "accent": style.get("accent", "#ffb454"),
            "accentRgb": style.get("accentRgb", [1.0, 0.7, 0.3]),
            "nf": nf,
            "nv": tot_v,
            "nt": tot_t,
            "frameNames": entry["frameNames"],
            "idleRange": fr["idle"],
            "lockRange": fr["lock"],
            "fireRange": fr["fire"],
            "launchFrame": fr.get("launchFrame", fr["fire"][0]),
            "muzzle": entry.get("muzzle", [28.0, -4.0, -5.0]),
            "orbitCenter": entry.get("orbitCenter", [20.0, -4.0, -5.5]),
            "orbitDist": float(entry.get("orbitDist", 23.0)),
            "orbitAz": float(style.get("orbitAz", 2.36)),
            "orbitEl": float(style.get("orbitEl", 0.30)),
            "presets": style.get("presets", []),
            "surfaces": surfs_out,
        })
        print(f"  [MD3] {entry['md3']:24s} -> {len(surfs_out)} surfs, {tot_v} verts, {tot_t} tris, {nf} frames")

    return models_out


def pack_sprites(sprites_dir):
    """Read sprites/manifest.json and encode all 4x8-dir sprite frames + cash FX."""
    manifest_path = os.path.join(sprites_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        sman = json.load(fh)

    states_out = []
    state_order = ["running_scissors", "overhead_scissors", "front_scissors", "no_scissors"]
    for sid in state_order:
        st = sman["states"][sid]
        dirs_out = []
        for d in range(8):
            rel_list = st["directions"][str(d)]
            dir_frames = []
            for fi, rel in enumerate(rel_list):
                fpath = os.path.join(sprites_dir, rel)
                assert os.path.isfile(fpath), f"Missing sprite PNG: {fpath}"
                dir_frames.append({
                    "key": f"{sid}_d{d}_f{fi}",
                    "file": rel,
                    "uri": png_data_uri(fpath),
                })
            dirs_out.append(dir_frames)
        states_out.append({
            "id": sid,
            "label": st["title"],
            "fps": st.get("fps", 10),
            "numDirs": st.get("num_dirs", 8),
            "numFrames": st.get("num_frames", len(dirs_out[0])),
            "description": SPRITE_DESCRIPTIONS.get(sid, st["title"]),
            "dirs": dirs_out,
        })
        print(f"  [SPR] {sid:20s} -> 8 dirs x {len(dirs_out[0])} frames")

    bills = []
    for rel in sman["cash_fx"]["dollar_bill"]["frames"]:
        fpath = os.path.join(sprites_dir, rel)
        assert os.path.isfile(fpath), f"Missing cash bill PNG: {fpath}"
        bills.append({"file": rel, "uri": png_data_uri(fpath)})

    coins = []
    for rel in sman["cash_fx"]["gold_coin"]["frames"]:
        fpath = os.path.join(sprites_dir, rel)
        assert os.path.isfile(fpath), f"Missing cash coin PNG: {fpath}"
        coins.append({"file": rel, "uri": png_data_uri(fpath)})

    print(f"  [FX ] cash_fx              -> {len(bills)} bills, {len(coins)} coins")
    return states_out, {"bills": bills, "coins": coins}


def pack_audio(sfx_dir):
    """Read sfx/manifest.json and embed all 8 SFX + 18 Kyle voice WAVs."""
    manifest_path = os.path.join(sfx_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        aman = json.load(fh)

    sfx_out = []
    for item in aman["sfx"]:
        fpath = item["path"]
        assert os.path.isfile(fpath), f"Missing SFX WAV: {fpath}"
        sfx_out.append({
            "id": item["id"],
            "filename": item["filename"],
            "title": item["title"],
            "role": item["role"],
            "description": item.get("description", ""),
            "looping": bool(item.get("looping", False)),
            "duration": float(item["duration"]),
            "peaks": item.get("peaks", []),
            "uri": wav_data_uri(fpath),
        })

    voice_out = []
    for item in aman["voice_clips"]:
        fpath = item["path"]
        assert os.path.isfile(fpath), f"Missing voice WAV: {fpath}"
        voice_out.append({
            "id": item["id"],
            "filename": item["filename"],
            "category": item.get("category", "voice"),
            "title": item["title"],
            "transcript": item.get("transcript", ""),
            "role": item.get("role", "Voice"),
            "description": item.get("notes", ""),
            "duration": float(item["duration"]),
            "peaks": item.get("peaks", []),
            "uri": wav_data_uri(fpath),
        })

    print(f"  [WAV] Packed {len(sfx_out)} game SFX + {len(voice_out)} Kyle voice clips")
    return sfx_out, voice_out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", default=DEFAULT_STAGE, help="Path to scratch/kyle_stage")
    parser.add_argument("--out", default=DEFAULT_OUT_HTML, help="Output HTML path")
    args = parser.parse_args()

    weapons_dir = os.path.join(args.stage, "weapons")
    sprites_dir = os.path.join(args.stage, "sprites")
    sfx_dir = os.path.join(args.stage, "sfx")

    print("1. Packing 5 WebGL2 MD3 Weapon Viewmodels...")
    packer = BinaryPacker()
    models = pack_weapon_models(weapons_dir, packer)

    print("2. Packing 4x8-Dir Kyle Sprites & Cash FX...")
    sprite_states, cash_fx = pack_sprites(sprites_dir)

    print("3. Packing Game SFX & Kyle Voice WAVs...")
    sfx_list, voice_list = pack_audio(sfx_dir)

    gz_bytes = gzip.compress(bytes(packer.buf), compresslevel=6)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    print(f"4. Compressed 3D buffer: raw={len(packer.buf)/1e6:.2f} MB -> gzip={len(gz_bytes)/1e6:.2f} MB")

    payload = {
        "binGz": b64_gz,
        "binLen": len(packer.buf),
        "textures": packer.tex_list,
        "models": models,
        "spriteStates": sprite_states,
        "cashFx": cash_fx,
        "sfx": sfx_list,
        "voice": voice_list,
    }

    with open(TEMPLATE_HTML, "r", encoding="utf-8") as fh:
        tpl = fh.read()
    placeholder = "/*__KYLE_DATA__*/null"
    assert placeholder in tpl, f"Missing {placeholder} in {TEMPLATE_HTML}"

    html_out = tpl.replace(placeholder, json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html_out)

    size_mb = os.path.getsize(args.out) / 1e6
    print(f"5. Wrote self-contained studio: {args.out} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
