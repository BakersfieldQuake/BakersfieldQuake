"""Explores 4 calibrated non-blown-out lighting presets (plus the old blown-out baseline for Before/After comparison)
on the already-vis'd `out/maps/bklan5_vis_base.bsp` without re-running qbsp or vis!

1. Rewrites only Lump 0 (entities: worldspawn lighting keys + point-light multiplier) on copies of `bklan5_vis_base.bsp`.
2. Runs `light.exe -threads 16` for each preset (and `-extra` 4x supersampling on the winning default `soft_daylight`).
3. Saves each preset's `.bsp` + `.lit` into `out/lighting_presets/<preset>/` (switchable anytime via `apply_bklan5_preset.py`).
4. Installs `soft_daylight` (`-extra`) into `maps/bklan5.bsp` and `maps/bklan5.lit`.
5. After `export_web_viewer.py` runs, `build_preset_lightmaps()` packs pixel-aligned `lightmap_<preset>.png` atlases into
   `out/web/warehouse5/` so the live 3D browser viewer & showcase can toggle all presets in real time!

Usage:
  python explore_bklan5_lighting.py bake
  python explore_bklan5_lighting.py atlases out/web/warehouse5
"""
import math
import os
import re
import shutil
import struct
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", ".."))
MAPS_OUT = os.path.join(HERE, "out", "maps")
PRESET_DIR = os.path.join(HERE, "out", "lighting_presets")
LIGHT_EXE = r"D:\vibe\quake1opensource\tools\ericw\light.exe"
THREADS = str(os.cpu_count() or 16)

# Note: `bklan5_vis_base.bsp` already scaled point lights by 0.56x during `make_bklan_v6.py`.
# `pt_mult` below is relative to that 0.56x base (so 1.0 = 0.56x original, 1.786 = 1.0x original).
PRESETS = {
    "before_blownout": {
        "label": "Before (Old Blown-Out: Sun 300 + Sky 140)",
        "extra": False,
        "pt_mult": 1.786,
        "ws": {
            "_minlight": "42",
            "_minlight_color": "255 245 228",
            "_sunlight": "300",
            "_sunlight_mangle": "60 -52 0",
            "_sunlight_color": "1 0.94 0.78",
            "_sunlight2": "140",
            "_sunlight2_color": "0.90 0.92 1",
            "_sunlight3": "55",
            "_sunlight3_color": "1 0.90 0.72",
            "_sunlight_penumbra": "2",
            "_bounce": "1",
            "_bouncescale": "0.75",
            "_dirt": "1",
            "_dirtscale": "0.42",
            "_sunlight_dirt": "0.4",
            "_sunlight2_dirt": "0.5",
        },
    },
    "soft_daylight": {
        "label": "Preset A — Soft Diffused California Daylight (Installed Default)",
        "extra": True,
        "pt_mult": 0.92,
        "ws": {
            "_minlight": "26",
            "_minlight_color": "230 234 242",
            "_sunlight": "38",
            "_sunlight_mangle": "132 -48 0",
            "_sunlight_color": "1.0 0.96 0.89",
            "_sunlight2": "62",
            "_sunlight2_color": "0.90 0.94 1.0",
            "_sunlight3": "20",
            "_sunlight3_color": "0.96 0.93 0.88",
            "_sunlight_penumbra": "9.0",
            "_bounce": "1",
            "_bouncescale": "0.30",
            "_dirt": "1",
            "_dirtscale": "0.30",
            "_dirtgain": "0.72",
            "_dirtdepth": "104",
            "_sunlight_dirt": "0.28",
            "_sunlight2_dirt": "0.38",
        },
    },
    "sunny_balanced": {
        "label": "Preset B — Balanced Sunny Bakersfield (Mild Shadow Relief)",
        "extra": False,
        "pt_mult": 1.00,
        "ws": {
            "_minlight": "21",
            "_minlight_color": "224 230 242",
            "_sunlight": "54",
            "_sunlight_mangle": "132 -46 0",
            "_sunlight_color": "1.0 0.94 0.84",
            "_sunlight2": "54",
            "_sunlight2_color": "0.85 0.92 1.0",
            "_sunlight3": "17",
            "_sunlight3_color": "0.96 0.91 0.84",
            "_sunlight_penumbra": "6.0",
            "_bounce": "1",
            "_bouncescale": "0.32",
            "_dirt": "1",
            "_dirtscale": "0.36",
            "_dirtgain": "0.75",
            "_dirtdepth": "112",
            "_sunlight_dirt": "0.35",
            "_sunlight2_dirt": "0.45",
        },
    },
    "warm_amber": {
        "label": "Preset C — Warm Late-Afternoon Amber (Soft Golden Wash)",
        "extra": False,
        "pt_mult": 1.00,
        "ws": {
            "_minlight": "22",
            "_minlight_color": "220 224 238",
            "_sunlight": "48",
            "_sunlight_mangle": "62 -38 0",
            "_sunlight_color": "1.0 0.88 0.70",
            "_sunlight2": "56",
            "_sunlight2_color": "0.80 0.87 1.0",
            "_sunlight3": "18",
            "_sunlight3_color": "1.0 0.90 0.78",
            "_sunlight_penumbra": "6.5",
            "_bounce": "1",
            "_bouncescale": "0.32",
            "_dirt": "1",
            "_dirtscale": "0.36",
            "_dirtgain": "0.75",
            "_dirtdepth": "112",
            "_sunlight_dirt": "0.35",
            "_sunlight2_dirt": "0.45",
        },
    },
    "twilight_neon": {
        "label": "Preset D — Cool Early-Dusk / Neon & Marquee Pop",
        "extra": False,
        "pt_mult": 1.22,
        "ws": {
            "_minlight": "19",
            "_minlight_color": "192 206 235",
            "_sunlight": "24",
            "_sunlight_mangle": "68 -28 0",
            "_sunlight_color": "1.0 0.82 0.64",
            "_sunlight2": "46",
            "_sunlight2_color": "0.72 0.83 1.0",
            "_sunlight3": "14",
            "_sunlight3_color": "0.85 0.86 0.96",
            "_sunlight_penumbra": "8.0",
            "_bounce": "1",
            "_bouncescale": "0.30",
            "_dirt": "1",
            "_dirtscale": "0.38",
            "_dirtgain": "0.78",
            "_dirtdepth": "112",
            "_sunlight_dirt": "0.38",
            "_sunlight2_dirt": "0.48",
        },
    },
}

WS_LIGHT_KEYS = {
    "_minlight", "_minlight_color", "_sunlight", "_sunlight_mangle", "_sunlight_color",
    "_sunlight2", "_sunlight2_color", "_sunlight3", "_sunlight3_color", "_sunlight_penumbra",
    "_bounce", "_bouncescale", "_dirt", "_dirtscale", "_dirtgain", "_dirtdepth",
    "_sunlight_dirt", "_sunlight2_dirt",
}


def rewrite_bsp_entities(base_bsp_bytes: bytes, ws_overrides: dict, pt_mult: float) -> bytes:
    e_ofs, e_len = struct.unpack_from("<2i", base_bsp_bytes, 4)
    ent_txt = base_bsp_bytes[e_ofs : e_ofs + e_len].decode("latin1")

    blocks = re.findall(r"\{[^}]*\}", ent_txt)
    out_blocks = []
    for i, blk in enumerate(blocks):
        if i == 0 and '"classname" "worldspawn"' in blk:
            lines = []
            for ln in blk.splitlines():
                m = re.match(r'^"([^"]+)"\s+"([^"]*)"$', ln.strip())
                if m and m.group(1) in WS_LIGHT_KEYS:
                    continue
                if ln.strip() == "}":
                    for k, v in ws_overrides.items():
                        lines.append(f'"{k}" "{v}"')
                lines.append(ln)
            out_blocks.append("\n".join(lines))
        elif '"classname" "light"' in blk and abs(pt_mult - 1.0) > 0.01:
            def _scale_m(m):
                v = max(20, int(round(float(m.group(1)) * pt_mult)))
                return f'"light" "{v}"'
            out_blocks.append(re.sub(r'"light" "(\d+(?:\.\d+)?)"', _scale_m, blk, count=1))
        else:
            out_blocks.append(blk)

    new_ent = ("\n".join(out_blocks) + "\n\x00").encode("latin1")
    pad = (4 - (len(base_bsp_bytes) % 4)) % 4
    new_ofs = len(base_bsp_bytes) + pad
    hdr = bytearray(base_bsp_bytes[:4 + 15 * 8])
    struct.pack_into("<2i", hdr, 4, new_ofs, len(new_ent))
    return bytes(hdr) + base_bsp_bytes[4 + 15 * 8 :] + (b"\x00" * pad) + new_ent


def bake_all():
    base_path = os.path.join(MAPS_OUT, "bklan5_vis_base.bsp")
    assert os.path.isfile(base_path), f"Missing {base_path}"
    base_bytes = open(base_path, "rb").read()
    os.makedirs(PRESET_DIR, exist_ok=True)

    summary = {}
    for key, cfg in PRESETS.items():
        pdir = os.path.join(PRESET_DIR, key)
        os.makedirs(pdir, exist_ok=True)
        bsp_p = os.path.join(pdir, "bklan5.bsp")
        lit_p = os.path.join(pdir, "bklan5.lit")
        log_p = os.path.join(pdir, "light.log")

        patched = rewrite_bsp_entities(base_bytes, cfg["ws"], cfg["pt_mult"])
        with open(bsp_p, "wb") as fp:
            fp.write(patched)

        cmd = [LIGHT_EXE, "-threads", THREADS]
        if cfg["extra"]:
            cmd.append("-extra")
        cmd.append("bklan5.bsp")
        print(f"Baking [{key}] ({'extra 4x' if cfg['extra'] else '1x fast'})...", flush=True)
        with open(log_p, "w", encoding="utf-8") as lf:
            res = subprocess.run(cmd, cwd=pdir, stdout=lf, stderr=subprocess.STDOUT)
        assert res.returncode == 0, f"light.exe failed on {key} (see {log_p})"

        lit_arr = np.frombuffer(open(lit_p, "rb").read()[8:], dtype=np.uint8)
        pcts = [round(float(x), 1) for x in np.percentile(lit_arr, [10, 25, 50, 75, 90, 99])]
        # Estimate % roof/stucco blowouts under DarkPlaces (albedo=0.80 cream stucco, scenebrightness=1.1875, 4x overbright)
        dp_stucco = 0.80 * 4.0 * (lit_arr.astype(np.float32) / 255.0) * 1.1875 * 1.125
        clip_pct = round(float((dp_stucco >= 1.0).mean() * 100.0), 1)
        summary[key] = {"label": cfg["label"], "pcts": pcts, "stucco_clip_pct": clip_pct}
        print(f"  -> {key}: .lit p10/25/50/75/90/99 = {pcts}, cream-stucco clip% = {clip_pct}%", flush=True)

    with open(os.path.join(PRESET_DIR, "summary.json"), "w", encoding="utf-8") as fp:
        import json
        json.dump(summary, fp, indent=2)

    # Install soft_daylight (-extra) as the active maps/bklan5.bsp + maps/bklan5.lit!
    win_dir = os.path.join(PRESET_DIR, "soft_daylight")
    shutil.copy2(os.path.join(win_dir, "bklan5.bsp"), os.path.join(MOD, "maps", "bklan5.bsp"))
    shutil.copy2(os.path.join(win_dir, "bklan5.lit"), os.path.join(MOD, "maps", "bklan5.lit"))
    print("Installed soft_daylight (-extra) -> maps/bklan5.bsp & maps/bklan5.lit")


def _parse_bsp_light_layout(bsp_path: str):
    d = open(bsp_path, "rb").read()
    bsp2 = d[:4] == b"BSP2"
    lumps = [struct.unpack("<2i", d[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    def lump(i):
        o, n = lumps[i]
        return d[o : o + n]
    face_fmt, face_sz = ("<iiiii4Bi", 28) if bsp2 else ("<hhihh4Bi", 20)
    edge_fmt, edge_sz = ("<2I", 8) if bsp2 else ("<2H", 4)
    verts = [struct.unpack("<3f", lump(3)[i : i + 12]) for i in range(0, len(lump(3)), 12)]
    texinfo = [struct.unpack("<8f2i", lump(6)[i : i + 40]) for i in range(0, len(lump(6)), 40)]
    faces = [struct.unpack(face_fmt, lump(7)[i : i + face_sz]) for i in range(0, len(lump(7)), face_sz)]
    edges = [struct.unpack(edge_fmt, lump(12)[i : i + edge_sz]) for i in range(0, len(lump(12)), edge_sz)]
    surfedges = list(struct.unpack("<%di" % (len(lump(13)) // 4), lump(13)))
    mt = lump(2)
    n_mt = struct.unpack("<i", mt[:4])[0]
    miptex = []
    for o in struct.unpack("<%di" % n_mt, mt[4 : 4 + 4 * n_mt]):
        if o < 0:
            miptex.append(("", 64, 64))
        else:
            nm, w, h = struct.unpack("<16s2I", mt[o : o + 24])
            miptex.append((nm.split(b"\0")[0].decode("latin1"), w, h))

    SKIP = ("sky", "clip", "skip", "trigger")
    blocks = []
    for fi, f in enumerate(faces):
        planenum, side, firstedge, numedges, ti, s0, s1, s2, s3, lightofs = f
        tex = miptex[texinfo[ti][8]][0]
        if tex.startswith(SKIP) or s0 == 255 or lightofs < 0:
            continue
        vec = texinfo[ti]
        pts = [verts[edges[e][0]] if e >= 0 else verts[edges[-e][1]]
               for e in (surfedges[firstedge + k] for k in range(numedges))]
        st = [(p[0] * vec[0] + p[1] * vec[1] + p[2] * vec[2] + vec[3],
               p[0] * vec[4] + p[1] * vec[5] + p[2] * vec[6] + vec[7]) for p in pts]
        mins = [math.floor(min(s[a] for s in st) / 16) for a in (0, 1)]
        maxs = [math.ceil(max(s[a] for s in st) / 16) for a in (0, 1)]
        w, h = maxs[0] - mins[0] + 1, maxs[1] - mins[1] + 1
        blocks.append((h, w, fi, mins))
    blocks.sort(reverse=True)
    aw = 4096 if sum(b[0] * b[1] for b in blocks) > 2048 * 1024 else 2048
    x = y = shelf = 0
    place = {}
    for h, w, fi, mins in blocks:
        if x + w + 2 > aw:
            x, y, shelf = 0, y + shelf + 2, 0
        place[fi] = (x + 1, y + 1, w, h)
        x += w + 2
        shelf = max(shelf, h)
    ah = 1 << max(1, (y + shelf + 2 - 1).bit_length())
    return aw, ah, place


def _pack_preset_atlas(aw: int, ah: int, place: dict, bsp_path: str, lit_path: str) -> Image.Image:
    d = open(bsp_path, "rb").read()
    bsp2 = d[:4] == b"BSP2"
    f_ofs, f_len = struct.unpack_from("<2i", d, 4 + 8 * 7)
    face_fmt, face_sz = ("<iiiii4Bi", 28) if bsp2 else ("<hhihh4Bi", 20)
    faces = [struct.unpack(face_fmt, d[f_ofs + i : f_ofs + i + face_sz]) for i in range(0, f_len, face_sz)]
    lit_raw = open(lit_path, "rb").read()[8:]
    lit_np = np.frombuffer(lit_raw, dtype=np.uint8).reshape(-1, 3)
    n_tot = len(lit_np)

    arr = np.full((ah, aw, 3), 255, dtype=np.uint8)
    for fi, (ax, ay, w, h) in place.items():
        ofs = faces[fi][9]
        if ofs < 0 or ofs >= n_tot:
            continue
        need = w * h
        blk = lit_np[ofs : min(ofs + need, n_tot)]
        if len(blk) < need:
            pad = np.repeat(blk[-1:], need - len(blk), axis=0)
            blk = np.concatenate([blk, pad], axis=0)
        tile = blk.reshape(h, w, 3)
        arr[ay : ay + h, ax : ax + w] = tile
        arr[ay : ay + h, ax - 1] = tile[:, 0]
        arr[ay : ay + h, ax + w] = tile[:, -1]
        arr[ay - 1, ax - 1 : ax + w + 1] = arr[ay, ax - 1 : ax + w + 1]
        arr[ay + h, ax - 1 : ax + w + 1] = arr[ay + h - 1, ax - 1 : ax + w + 1]
    return Image.fromarray(arr, mode="RGB")


def build_preset_lightmaps(web_dir: str):
    main_bsp = os.path.join(MOD, "maps", "bklan5.bsp")
    aw, ah, place = _parse_bsp_light_layout(main_bsp)
    for key in PRESETS:
        pdir = os.path.join(PRESET_DIR, key)
        bsp_p = os.path.join(pdir, "bklan5.bsp")
        lit_p = os.path.join(pdir, "bklan5.lit")
        if not os.path.isfile(lit_p):
            continue
        atl = _pack_preset_atlas(aw, ah, place, bsp_p, lit_p)
        out_p = os.path.join(web_dir, f"lm_{key}.jpg")
        # Save high-quality 4:4:4 subsampling=0 JPEG (~320 KB each vs 2.5 MB PNG!) so switching in browser is instant!
        atl.save(out_p, format="JPEG", quality=94, subsampling=0)
        print(f"  wrote {out_p} ({os.path.getsize(out_p)//1024} KB)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "bake"
    if mode == "bake":
        bake_all()
    elif mode == "atlases":
        build_preset_lightmaps(sys.argv[2])
