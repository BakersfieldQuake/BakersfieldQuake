#!/usr/bin/env python3
"""Builds a 100% self-contained, ZERO-dependency offline WebGL2 HTML 3D viewer
for Bakersfield-ish (`maps/bakersfieldish.bsp`).

Design guarantees:
  - Single standalone HTML file (`docs/bakersfieldish_viewer.html` by default).
  - ZERO external CDN links, ZERO `<script type="module">`, ZERO `fetch()`,
    ZERO external asset files — double-clicking via `file://` works 100% offline!
  - Parses compiled BSP2 / BSP29 geometry + `.lit` RGB lightmaps (or BSP lump 8
    fallback) + real textures & `_glow` maps from `bakersfield.pk3`, `zz_*.pk3`,
    `quake15/q15.pk3`, loose files, or embedded miptex.
  - Compresses all vertex/index buffers with gzip (level 9) + base64 and decodes
    natively in browser via `DecompressionStream('gzip')` into pure WebGL2 VAOs.
  - Smooth WASD + mouse-drag / PointerLock free-fly camera + 8 landmark presets:
    Padre Hotel, Fox Theater, Parking Garage, Golden West Casino, The Great Castle,
    Larry's Warehouse, Bakersfield Sign, and SkyPad View (with 3D SkyPad arcs!).
  - Live interactive in-browser demolition & animation triggers driven directly by
    the compiled map's `bako_*` & `func_breakable` BSP submodels:
      * Fox Theater: staggered collapse + billowing dust + rubble + 25s slow rebuild!
      * Padre Hotel: rhythmic charge pops + 12s inward V-collapse + 24 3D rolling
        bouncing street boulders + massive non-blinding translucent base-surge dust!
      * Bakersfield Sign: hinge topple + neon sparks + elastic street bounce!
      * Shatterable Glass: crisp window shatter + flying sparkling shards!

Usage:
  python source/mm_tools/build_bakersfieldish_html.py
  python source/mm_tools/build_bakersfieldish_html.py --bsp maps/bakersfieldish.bsp --out docs/bakersfieldish_viewer.html
"""
from __future__ import annotations

import argparse
import base64
import gzip
import io
import json
import math
import os
import re
import struct
import sys
import time
import zipfile
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT_DIR = os.path.abspath(os.path.join(MOD_DIR, ".."))

DEFAULT_BSP = os.path.join(MOD_DIR, "maps", "bakersfieldish.bsp")
DEFAULT_OUT = os.path.join(MOD_DIR, "docs", "bakersfieldish_viewer.html")

PAK0_CANDIDATES = [
    os.path.join(ROOT_DIR, "id1", "pak0.pak"),
    r"G:\Quake\Combat\id1\pak0.pak",
    r"G:\Quake\nQuake\nQuake\id1\pak0.pak",
]

SKIP_TEX_PREFIXES = ("sky", "clip", "skip", "trigger", "hint", "nodraw", "origin", "caulk")
HERO_TEX_PREFIXES = (
    "bk5_bsign", "bk3_larry", "bk3_pylon", "bk_bupper", "bk5_ortiz", "bk5_cblogo",
    "fox", "fx_", "pad_", "farm_", "gwc_", "nile", "sand", "jer", "fn_", "dan_",
)

# Bakersfield Downtown / Bakersfield-ish D-frame -> Quake map units (`1 ft = 12 u`, SHIFT=(835,-285))
D_SHIFT_X = 835.0
D_SHIFT_Y = -285.0
D_SCALE = 12.0


def d_to_u(dx: float, dy: float, dz: float = 0.0) -> List[float]:
    return [
        round((dx - D_SHIFT_X) * D_SCALE, 1),
        round((dy - D_SHIFT_Y) * D_SCALE, 1),
        round(dz * D_SCALE, 1),
    ]


def parse_vec3(s: str, default: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> Tuple[float, float, float]:
    parts = s.strip().split()
    if len(parts) < 3:
        return default
    try:
        return (float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError:
        return default


def parse_float(s: str, default: float = 0.0) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Zircon / DarkPlaces AssetFS (loose -> zz_*.pk3 -> bakersfield.pk3 -> q15.pk3)
# ---------------------------------------------------------------------------
class AssetFS:
    """Resolves game textures/shaders in authentic Zircon resolution order."""

    def __init__(self, mod_dir: str, root_dir: str):
        self.mod_dir = mod_dir
        self.root_dir = root_dir
        pk3_paths: List[str] = []

        # Lower priority: quake15/q15.pk3
        q15_pk3 = os.path.join(root_dir, "quake15", "q15.pk3")
        if os.path.isfile(q15_pk3):
            pk3_paths.append(q15_pk3)

        # Base BakersfieldQuake/bakersfield.pk3
        base_pk3 = os.path.join(mod_dir, "bakersfield.pk3")
        if os.path.isfile(base_pk3):
            pk3_paths.append(base_pk3)

        # Overlay zz_*.pk3 in sorted order (later name wins, per AGENTS.md)
        if os.path.isdir(mod_dir):
            for fn in sorted(os.listdir(mod_dir)):
                fl = fn.lower()
                if fl.startswith("zz_") and fl.endswith(".pk3"):
                    pk3_paths.append(os.path.join(mod_dir, fn))

        self.zips = [zipfile.ZipFile(p, "r") for p in pk3_paths]
        self.zip_map: Dict[str, Tuple[zipfile.ZipFile, str]] = {}
        for zf in self.zips:
            for name in zf.namelist():
                self.zip_map[name.lower()] = (zf, name)

        self.shader_map: Dict[str, str] = {}
        self._load_shaders()

    def close(self) -> None:
        for zf in self.zips:
            try:
                zf.close()
            except Exception:
                pass

    def _load_shaders(self) -> None:
        texts: List[str] = []
        for zf in self.zips:
            for name in zf.namelist():
                nl = name.lower()
                if nl.startswith("scripts/") and nl.endswith(".shader"):
                    try:
                        texts.append(zf.read(name).decode("latin1", errors="replace"))
                    except Exception:
                        pass
        scripts_dir = os.path.join(self.mod_dir, "scripts")
        if os.path.isdir(scripts_dir):
            for fn in sorted(os.listdir(scripts_dir)):
                if fn.lower().endswith(".shader"):
                    try:
                        texts.append(open(os.path.join(scripts_dir, fn), encoding="latin1", errors="replace").read())
                    except OSError:
                        pass
        for txt in texts:
            for m in re.finditer(r"^([^\s{]+)\s*\{(.*?)^\}", txt, re.S | re.M):
                img = re.search(r"\b(?:map|animmap\s+[\d.]+)\s+([^\s\r\n]+)", m.group(2), re.I)
                if img and not img.group(1).startswith("$"):
                    self.shader_map[m.group(1).lower()] = img.group(1)

    def read(self, rel: str) -> Optional[bytes]:
        rel_u = rel.replace("\\", "/")
        for base in (self.mod_dir, os.path.join(self.root_dir, "quake15")):
            disk = os.path.join(base, rel_u.replace("/", os.sep))
            if os.path.isfile(disk):
                return open(disk, "rb").read()
        hit = self.zip_map.get(rel_u.lower())
        if hit is not None:
            return hit[0].read(hit[1])
        return None

    def find_texture(self, rel_base: str) -> Optional[bytes]:
        mapped = self.shader_map.get(rel_base.lower())
        cands = [rel_base]
        if mapped:
            cands.insert(0, mapped)
        stem = os.path.splitext(rel_base)[0]
        cands.extend([stem + ".png", stem + ".tga", stem + ".jpg", stem + ".webp"])
        if mapped:
            mstem = os.path.splitext(mapped)[0]
            cands.extend([mstem + ".png", mstem + ".tga", mstem + ".jpg"])
        for c in cands:
            raw = self.read(c)
            if raw is not None:
                return raw
        return None


def load_quake_palette() -> np.ndarray:
    for pak_path in PAK0_CANDIDATES:
        if not os.path.isfile(pak_path):
            continue
        raw = open(pak_path, "rb").read()
        if raw[:4] != b"PACK":
            continue
        _, dirofs, dirlen = struct.unpack("<4s2i", raw[:12])
        for off in range(dirofs, dirofs + dirlen, 64):
            name = raw[off : off + 56].split(b"\x00")[0].decode("latin1").lower()
            if name == "gfx/palette.lmp":
                fofs, flen = struct.unpack("<2i", raw[off + 56 : off + 64])
                if flen >= 768:
                    return np.frombuffer(raw[fofs : fofs + 768], dtype=np.uint8).reshape(256, 3)
    # Fallback synthetic grayscale palette if pak0.pak is unavailable
    g = np.arange(256, dtype=np.uint8)
    return np.stack([g, g, g], axis=-1)


# ---------------------------------------------------------------------------
# Image Encoding Helpers (WebP Data URIs — Compact, Fast, Alpha-Capable)
# ---------------------------------------------------------------------------
def image_to_data_uri(im: Image.Image, quality: int = 78, force_png: bool = False) -> str:
    bio = io.BytesIO()
    if force_png:
        im.save(bio, "PNG", optimize=True)
        mime = "image/png"
    else:
        im.save(bio, "WEBP", quality=quality, method=4)
        mime = "image/webp"
    return f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def encode_texture_bytes(
    raw: bytes,
    max_dim: int,
    allow_alpha: bool,
    quality: int,
) -> Tuple[str, bool, int, int]:
    im = Image.open(io.BytesIO(raw))
    has_alpha = allow_alpha and ("A" in im.getbands() or "transparency" in im.info)
    im = im.convert("RGBA" if has_alpha else "RGB")
    if max(im.size) > max_dim:
        im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    uri = image_to_data_uri(im, quality=quality)
    return uri, has_alpha, im.size[0], im.size[1]


# ---------------------------------------------------------------------------
# Binary Arena Packer
# ---------------------------------------------------------------------------
class BinaryArena:
    def __init__(self) -> None:
        self.buf = bytearray()

    def add(self, data: bytes) -> List[int]:
        while len(self.buf) & 3:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(data)
        return [off, len(data)]


# ---------------------------------------------------------------------------
# BSP2 / BSP29 Extractor -> Offline WebGL2 Scene Payload
# ---------------------------------------------------------------------------
DESTRUCT_CLASSES = {
    "bako_fox_clock": ("fox", "clock"),
    "bako_fox_piece": ("fox", "piece"),
    "bako_fox_rubble": ("fox", "rubble"),
    "bako_padre_piece": ("padre", "piece"),
    "bako_padre_rubble": ("padre", "rubble"),
    "bako_sign_piece": ("sign", "piece"),
    "bako_sign_rubble": ("sign", "rubble"),
}


def build_scene_payload(
    bsp_path: str,
    lit_path: Optional[str],
    tex_max: int = 256,
    hero_tex_max: int = 512,
    tex_quality: int = 78,
    lm_atlas_max: int = 4096,
    lm_quality: int = 88,
) -> Dict[str, Any]:
    t0 = time.time()
    if not os.path.isfile(bsp_path):
        raise FileNotFoundError(f"BSP file not found: {bsp_path}")

    raw = open(bsp_path, "rb").read()
    magic = raw[:4]
    is_bsp2 = magic == b"BSP2"
    if not is_bsp2:
        ver = struct.unpack("<i", magic)[0]
        if ver != 29:
            raise ValueError(f"Unsupported BSP magic/version in {bsp_path}: {magic!r}")

    lumps = [struct.unpack("<2i", raw[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    mv = memoryview(raw)

    def lump(idx: int) -> memoryview:
        o, n = lumps[idx]
        return mv[o : o + n]

    ent_text = bytes(lump(0)).decode("latin1", errors="replace")
    planes = list(struct.iter_unpack("<4fi", lump(1)))
    verts = list(struct.iter_unpack("<3f", lump(3)))
    texinfo = list(struct.iter_unpack("<8f2i", lump(6)))
    if is_bsp2:
        faces = list(struct.iter_unpack("<iiiii4Bi", lump(7)))
        edges = list(struct.iter_unpack("<2I", lump(12)))
    else:
        faces = list(struct.iter_unpack("<hhihh4Bi", lump(7)))
        edges = list(struct.iter_unpack("<2H", lump(12)))
    surfedges = struct.unpack("<%di" % (len(lump(13)) // 4), lump(13))
    models = list(struct.iter_unpack("<9f7i", lump(14)))
    gray_light = bytes(lump(8))

    # Miptex table (Lump 2)
    tl = lump(2)
    nmip = struct.unpack("<i", tl[:4])[0]
    miptex: List[Tuple[str, int, int]] = []
    bsp_mip_pixels: Dict[str, Tuple[int, int, bytes]] = {}
    for i in range(nmip):
        o = struct.unpack("<i", tl[4 + 4 * i : 8 + 4 * i])[0]
        if o < 0:
            miptex.append(("", 16, 16))
            continue
        raw_name, w, h, m0_ofs = struct.unpack("<16s3I", tl[o : o + 28])
        tname = raw_name.split(b"\x00")[0].decode("latin1")
        miptex.append((tname, max(1, w), max(1, h)))
        if m0_ofs > 0 and o + m0_ofs + w * h <= len(tl):
            bsp_mip_pixels[tname.lower()] = (w, h, bytes(tl[o + m0_ofs : o + m0_ofs + w * h]))

    # Colored `.lit` lightmap (or expand Lump 8 grayscale to RGB)
    lit_bytes: Optional[bytes] = None
    if lit_path and os.path.isfile(lit_path):
        lraw = open(lit_path, "rb").read()
        if lraw[:4] == b"QLIT":
            lit_bytes = lraw[8:]
            print(f"[bsp] Loaded colored .lit ({len(lit_bytes):,} bytes)", flush=True)
    if lit_bytes is None and gray_light:
        g_arr = np.frombuffer(gray_light, dtype=np.uint8)
        lit_bytes = np.repeat(g_arr[:, None], 3, axis=1).tobytes()
        print(f"[bsp] Using BSP Lump 8 grayscale lightmap ({len(gray_light):,} luxels)", flush=True)

    # Parse entities
    entities: List[Dict[str, str]] = []
    for m in re.finditer(r"\{([^}]*)\}", ent_text):
        entities.append(dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m.group(1))))

    # Classify bmodels into static vs dynamic destructibles & shatterable glass
    static_bmodels: List[Tuple[int, Tuple[float, float, float], float]] = [(0, (0.0, 0.0, 0.0), 1.0)]
    dynamic_entries: List[Dict[str, Any]] = []
    skypads: List[Dict[str, Any]] = []
    gokart_count = 0
    jetpack_count = 0
    cannon_count = 0

    for ent_idx, kv in enumerate(entities):
        cls = kv.get("classname", "")
        mdl = kv.get("model", "")
        if cls == "info_skypad":
            skypads.append({
                "origin": list(parse_vec3(kv.get("origin", "0 0 0"))),
                "pos1": list(parse_vec3(kv.get("pos1", "0 0 0"))),
                "height": parse_float(kv.get("height", "2400"), 2400.0),
                "message": kv.get("message", "SkyPad"),
            })
            continue
        if cls.startswith("misc_gokart"):
            gokart_count += 1
        elif cls == "item_jetpack":
            jetpack_count += 1
        elif cls == "misc_eric_cannon":
            cannon_count += 1

        if not mdl.startswith("*"):
            continue
        if cls.startswith("trigger"):
            continue
        try:
            mi = int(mdl[1:])
        except ValueError:
            continue
        if mi <= 0 or mi >= len(models):
            continue

        org = parse_vec3(kv.get("origin", "0 0 0"))
        op = max(0.05, min(1.0, parse_float(kv.get("alpha", "1.0"), 1.0)))

        if cls in DESTRUCT_CLASSES:
            group, kind = DESTRUCT_CLASSES[cls]
            fall_ang = parse_vec3(kv.get("bako_fall_angles", "0 0 0"))
            fall_shift = parse_vec3(kv.get("bako_fall_shift", "0 0 0"))
            fall_drop = parse_float(kv.get("bako_fall_drop", "0"), 0.0)
            delay = parse_float(kv.get("bako_delay", "0"), 0.0)
            dur = parse_float(kv.get("bako_dur", "3.0"), 3.0)
            reb_ord = parse_float(kv.get("bako_rebuild_order", "-1"), -1.0)
            mrec = models[mi]
            bmin = [round(mrec[0] + org[0], 1), round(mrec[1] + org[1], 1), round(mrec[2] + org[2], 1)]
            bmax = [round(mrec[3] + org[0], 1), round(mrec[4] + org[1], 1), round(mrec[5] + org[2], 1)]
            dynamic_entries.append({
                "id": f"{group}_{kind}_{ent_idx}",
                "mi": mi,
                "group": group,
                "kind": kind,
                "role": kv.get("bako_role", kind),
                "origin": [round(org[0], 2), round(org[1], 2), round(org[2], 2)],
                "bmin": bmin,
                "bmax": bmax,
                "fallAngles": [round(fall_ang[0], 2), round(fall_ang[1], 2), round(fall_ang[2], 2)],
                "fallDrop": round(fall_drop, 2),
                "fallShift": [round(fall_shift[0], 2), round(fall_shift[1], 2), round(fall_shift[2], 2)],
                "delay": round(delay, 3),
                "dur": max(0.2, round(dur, 3)),
                "rebuildOrder": reb_ord,
                "alpha": round(op, 2),
            })
        elif cls == "func_breakable" and kv.get("style", "") == "3":
            mrec = models[mi]
            bmin = [round(mrec[0] + org[0], 1), round(mrec[1] + org[1], 1), round(mrec[2] + org[2], 1)]
            bmax = [round(mrec[3] + org[0], 1), round(mrec[4] + org[1], 1), round(mrec[5] + org[2], 1)]
            glass_op = min(op, 0.55) if "alpha" in kv else 0.45
            dynamic_entries.append({
                "id": f"glass_{ent_idx}",
                "mi": mi,
                "group": "glass",
                "kind": "glass",
                "role": "glass",
                "origin": [round(org[0], 2), round(org[1], 2), round(org[2], 2)],
                "bmin": bmin,
                "bmax": bmax,
                "fallAngles": [0.0, 0.0, 0.0],
                "fallDrop": 0.0,
                "fallShift": [0.0, 0.0, 0.0],
                "delay": 0.0,
                "dur": 0.2,
                "rebuildOrder": -1.0,
                "alpha": round(glass_op, 2),
            })
        else:
            static_bmodels.append((mi, org, op))

    # Collect all visible face indices for lightmap packing
    all_visible_faces: List[int] = []
    seen_faces = set()
    for mi, _, _ in static_bmodels:
        mrec = models[mi]
        for fi in range(mrec[14], mrec[14] + mrec[15]):
            if fi not in seen_faces:
                seen_faces.add(fi)
                all_visible_faces.append(fi)
    for dyn in dynamic_entries:
        mrec = models[dyn["mi"]]
        for fi in range(mrec[14], mrec[14] + mrec[15]):
            if fi not in seen_faces:
                seen_faces.add(fi)
                all_visible_faces.append(fi)

    # 1. Shelf-pack lightmap atlases
    pages: List[Dict[str, Any]] = [{"place": {}, "x": 4, "y": 0, "shelf": 4}]
    face_page: Dict[int, int] = {}
    aw = lm_atlas_max
    if lit_bytes:
        max_luxel = len(lit_bytes) // 3
        blocks: List[Tuple[int, int, int, List[int]]] = []
        for fi in all_visible_faces:
            _, _, firstedge, numedges, ti, s0, _, _, _, lightofs = faces[fi]
            tex = miptex[texinfo[ti][8]][0]
            if not tex or tex.lower().startswith(SKIP_TEX_PREFIXES) or s0 == 255 or lightofs < 0:
                continue
            vec = texinfo[ti]
            s_min, s_max = 1e18, -1e18
            t_min, t_max = 1e18, -1e18
            for k in range(numedges):
                se = surfedges[firstedge + k]
                p = verts[edges[se][0]] if se >= 0 else verts[edges[-se][1]]
                sv = p[0] * vec[0] + p[1] * vec[1] + p[2] * vec[2] + vec[3]
                tv = p[0] * vec[4] + p[1] * vec[5] + p[2] * vec[6] + vec[7]
                if sv < s_min:
                    s_min = sv
                if sv > s_max:
                    s_max = sv
                if tv < t_min:
                    t_min = tv
                if tv > t_max:
                    t_max = tv
            m0 = math.floor((s_min + max(5e-4, abs(s_min) * 2.5e-7)) / 16.0)
            m1 = math.floor((t_min + max(5e-4, abs(t_min) * 2.5e-7)) / 16.0)
            x0 = max(m0, math.ceil((s_max - max(5e-4, abs(s_max) * 2.5e-7)) / 16.0))
            x1 = max(m1, math.ceil((t_max - max(5e-4, abs(t_max) * 2.5e-7)) / 16.0))
            w, h = x0 - m0 + 1, x1 - m1 + 1
            if w <= 0 or h <= 0 or lightofs + w * h > max_luxel or w + 4 > aw or h + 4 > aw:
                continue
            blocks.append((h, w, fi, [m0, m1]))

        blocks.sort(reverse=True)
        cur = pages[0]
        for h, w, fi, mins in blocks:
            if cur["x"] + w + 2 > aw:
                cur["x"] = 0
                cur["y"] += cur["shelf"] + 2
                cur["shelf"] = 0
            if cur["y"] + max(cur["shelf"], h) + 2 > aw:
                cur["ah"] = min(aw, 1 << max(4, (cur["y"] + cur["shelf"] + 1).bit_length()))
                cur = {"place": {}, "x": 4, "y": 0, "shelf": 4}
                pages.append(cur)
            ax, ay = cur["x"] + 1, cur["y"] + 1
            cur["place"][fi] = (ax, ay, w, h, mins)
            face_page[fi] = len(pages) - 1
            cur["x"] += w + 2
            cur["shelf"] = max(cur["shelf"], h)
        cur["ah"] = min(aw, 1 << max(4, (cur["y"] + cur["shelf"] + 1).bit_length()))
    else:
        pages[0]["ah"] = 16

    lm_uris: List[str] = []
    for pi, pg in enumerate(pages):
        ah = pg["ah"]
        buf = bytearray(b"\xd8" * (aw * ah * 3))
        if lit_bytes and pg["place"]:
            mv_b = memoryview(buf)
            for fi, (ax, ay, w, h, _mins) in pg["place"].items():
                ofs = faces[fi][9]
                for v in range(h):
                    src_s = 3 * (ofs + v * w)
                    row_rgb = lit_bytes[src_s : src_s + 3 * w]
                    dst_s = 3 * ((ay + v) * aw + ax)
                    mv_b[dst_s : dst_s + 3 * w] = row_rgb
                    mv_b[dst_s - 3 : dst_s] = row_rgb[:3]
                    mv_b[dst_s + 3 * w : dst_s + 3 * (w + 1)] = row_rgb[-3:]
                top_r = mv_b[3 * (ay * aw + ax - 1) : 3 * (ay * aw + ax + w + 1)]
                mv_b[3 * ((ay - 1) * aw + ax - 1) : 3 * ((ay - 1) * aw + ax + w + 1)] = top_r
                bot_r = mv_b[3 * ((ay + h - 1) * aw + ax - 1) : 3 * ((ay + h - 1) * aw + ax + w + 1)]
                mv_b[3 * ((ay + h) * aw + ax - 1) : 3 * ((ay + h) * aw + ax + w + 1)] = bot_r
        lm_im = Image.frombytes("RGB", (aw, ah), bytes(buf))
        lm_uris.append(image_to_data_uri(lm_im, quality=lm_quality))
        print(f"[lm] Page {pi}: {aw}x{ah} ({len(pg['place']):,} faces, {len(lm_uris[-1]) / 1024:.0f} KB b64)", flush=True)

    # 2. Pack Geometry into compact interleaved vertices (28 bytes/vert)
    # Compute world bounds for 4x4 static sector spatial partitioning
    m0 = models[0]
    wx_min, wy_min = m0[0], m0[1]
    wx_span = max(1.0, m0[3] - m0[0])
    wy_span = max(1.0, m0[4] - m0[1])

    used_textures: Dict[str, int] = {}
    tex_names: List[str] = []

    def get_tex_idx(tname: str) -> int:
        idx = used_textures.get(tname)
        if idx is None:
            idx = len(tex_names)
            used_textures[tname] = idx
            tex_names.append(tname)
        return idx

    def append_face_to_bucket(
        bucket: Dict[str, Any],
        fi: int,
        add_org: Tuple[float, float, float],
    ) -> None:
        planenum, side, firstedge, numedges, ti, _, _, _, _, _ = faces[fi]
        vec = texinfo[ti]
        _, tw, th = miptex[vec[8]]
        pl = planes[planenum]
        nx, ny, nz = (-pl[0], -pl[1], -pl[2]) if side else (pl[0], pl[1], pl[2])
        nrm_i8 = (
            max(-127, min(127, int(round(nx * 127.0)))),
            max(-127, min(127, int(round(ny * 127.0)))),
            max(-127, min(127, int(round(nz * 127.0)))),
        )
        pi = face_page.get(fi, 0)
        ah = pages[pi]["ah"]
        pl_entry = pages[pi]["place"].get(fi)

        vmap = bucket["vmap"]
        vlist = bucket["verts"]
        ilist = bucket["indices"]
        poly_idx: List[int] = []
        ox, oy, oz = add_org
        for k in range(numedges):
            se = surfedges[firstedge + k]
            p = verts[edges[se][0]] if se >= 0 else verts[edges[-se][1]]
            s = p[0] * vec[0] + p[1] * vec[1] + p[2] * vec[2] + vec[3]
            t = p[0] * vec[4] + p[1] * vec[5] + p[2] * vec[6] + vec[7]
            u, v = s / tw, t / th
            if pl_entry is not None:
                ax, ay, _w, _h, mins = pl_entry
                lu = (s / 16.0 - mins[0] + 0.5 + ax) / aw
                lv = (t / 16.0 - mins[1] + 0.5 + ay) / ah
            else:
                lu, lv = 1.0 / aw, 1.0 / ah
            lu16 = max(0, min(65535, int(round(lu * 65535.0))))
            lv16 = max(0, min(65535, int(round(lv * 65535.0))))
            px, py, pz = p[0] + ox, p[1] + oy, p[2] + oz
            key = (round(px, 2), round(py, 2), round(pz, 2), round(u, 4), round(v, 4), lu16, lv16, nrm_i8)
            vi = vmap.get(key)
            if vi is None:
                vi = len(vlist)
                vmap[key] = vi
                vlist.append((px, py, pz, u, v, lu16, lv16, nrm_i8[0], nrm_i8[1], nrm_i8[2], 0))
            poly_idx.append(vi)

        # Winding: match Quake front-face CCW convention for WebGL
        for k in range(1, len(poly_idx) - 1):
            ilist.extend((poly_idx[0], poly_idx[k + 1], poly_idx[k]))

    # Static world buckets keyed by (sec_id, tex_idx, lm_page, opacity_q)
    static_buckets: Dict[Tuple[int, int, int, float], Dict[str, Any]] = {}
    sector_bounds: Dict[int, List[float]] = {}

    for mi, org, op in static_bmodels:
        mrec = models[mi]
        op_q = round(op, 2)
        for fi in range(mrec[14], mrec[14] + mrec[15]):
            _, _, firstedge, numedges, ti, _, _, _, _, _ = faces[fi]
            tname = miptex[texinfo[ti][8]][0]
            if not tname or tname.lower().startswith(SKIP_TEX_PREFIXES):
                continue
            tidx = get_tex_idx(tname)
            pi = face_page.get(fi, 0)

            # Determine spatial sector (0..15) or global (-1) for giant ground slabs
            xs, ys, zs = [], [], []
            for k in range(numedges):
                se = surfedges[firstedge + k]
                p = verts[edges[se][0]] if se >= 0 else verts[edges[-se][1]]
                xs.append(p[0] + org[0])
                ys.append(p[1] + org[1])
                zs.append(p[2] + org[2])
            if (max(xs) - min(xs)) > wx_span * 0.45 or (max(ys) - min(ys)) > wy_span * 0.45:
                sec_id = -1
            else:
                cx = 0.5 * (min(xs) + max(xs))
                cy = 0.5 * (min(ys) + max(ys))
                sx = min(3, max(0, int((cx - wx_min) / wx_span * 4.0)))
                sy = min(3, max(0, int((cy - wy_min) / wy_span * 4.0)))
                sec_id = sx * 4 + sy

            sb = sector_bounds.get(sec_id)
            if sb is None:
                sector_bounds[sec_id] = [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]
            else:
                sb[0] = min(sb[0], min(xs))
                sb[1] = min(sb[1], min(ys))
                sb[2] = min(sb[2], min(zs))
                sb[3] = max(sb[3], max(xs))
                sb[4] = max(sb[4], max(ys))
                sb[5] = max(sb[5], max(zs))

            bkey = (sec_id, tidx, pi, op_q)
            bkt = static_buckets.get(bkey)
            if bkt is None:
                bkt = {"vmap": {}, "verts": [], "indices": []}
                static_buckets[bkey] = bkt
            append_face_to_bucket(bkt, fi, org)

    # Pack binary arena (28 bytes per vertex)
    arena = BinaryArena()
    v_struct = struct.Struct("<3f2f2H4b")

    def finalize_bucket(bkt: Dict[str, Any]) -> Tuple[List[int], List[int], int, int]:
        vlist = bkt["verts"]
        ilist = bkt["indices"]
        vbytes = bytearray(len(vlist) * v_struct.size)
        for i, v in enumerate(vlist):
            v_struct.pack_into(vbytes, i * v_struct.size, *v)
        v_ref = arena.add(bytes(vbytes))
        if len(vlist) <= 65535:
            ibytes = np.asarray(ilist, dtype="<u2").tobytes()
            itype = 2
        else:
            ibytes = np.asarray(ilist, dtype="<u4").tobytes()
            itype = 4
        i_ref = arena.add(ibytes)
        return v_ref, i_ref, len(ilist), itype

    static_batches: List[Dict[str, Any]] = []
    total_tris = 0
    for (sec_id, tidx, pi, op_q), bkt in sorted(static_buckets.items()):
        if not bkt["indices"]:
            continue
        v_ref, i_ref, icnt, itype = finalize_bucket(bkt)
        total_tris += icnt // 3
        static_batches.append({
            "s": sec_id,
            "t": tidx,
            "l": pi,
            "a": op_q,
            "v": v_ref,
            "i": i_ref,
            "n": icnt,
            "it": itype,
        })

    # Dynamic destructible & glass submodels (kept in local pivot space!)
    dynamic_out: List[Dict[str, Any]] = []
    for dyn in dynamic_entries:
        mrec = models[dyn["mi"]]
        dyn_buckets: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for fi in range(mrec[14], mrec[14] + mrec[15]):
            tname = miptex[texinfo[faces[fi][4]][8]][0]
            if not tname or tname.lower().startswith(SKIP_TEX_PREFIXES):
                continue
            tidx = get_tex_idx(tname)
            pi = face_page.get(fi, 0)
            bkt = dyn_buckets.setdefault((tidx, pi), {"vmap": {}, "verts": [], "indices": []})
            append_face_to_bucket(bkt, fi, (0.0, 0.0, 0.0))

        batches: List[Dict[str, Any]] = []
        for (tidx, pi), bkt in sorted(dyn_buckets.items()):
            if not bkt["indices"]:
                continue
            v_ref, i_ref, icnt, itype = finalize_bucket(bkt)
            total_tris += icnt // 3
            batches.append({
                "t": tidx,
                "l": pi,
                "v": v_ref,
                "i": i_ref,
                "n": icnt,
                "it": itype,
            })
        if batches:
            entry = dict(dyn)
            entry.pop("mi", None)
            entry["batches"] = batches
            dynamic_out.append(entry)

    # 3. Resolve & inline all used world textures (+ _glow maps) as compact WebP data URIs
    fs = AssetFS(MOD_DIR, ROOT_DIR)
    pal = load_quake_palette()
    textures_out: List[Dict[str, Any]] = []
    missing_cnt = 0
    glow_cnt = 0
    try:
        for tname in tex_names:
            tl_name = tname.lower()
            is_alpha_tex = tname.startswith("{")
            is_hero = tl_name.startswith(HERO_TEX_PREFIXES)
            mdim = hero_tex_max if is_hero else tex_max
            raw_tex = fs.find_texture(f"textures/{tname}")
            if raw_tex is not None:
                uri, has_a, tw, th = encode_texture_bytes(raw_tex, mdim, is_alpha_tex, tex_quality)
                alpha_test = bool(has_a or is_alpha_tex)
            elif tl_name in bsp_mip_pixels:
                mw, mh, pix = bsp_mip_pixels[tl_name]
                im = Image.fromarray(pal[np.frombuffer(pix, dtype=np.uint8).reshape(mh, mw)], "RGB")
                uri = image_to_data_uri(im, quality=tex_quality)
                alpha_test = False
            else:
                missing_cnt += 1
                # Deterministic warm concrete fallback checker
                im = Image.new("RGB", (32, 32), (148, 138, 126))
                uri = image_to_data_uri(im, quality=70)
                alpha_test = False

            glow_uri = ""
            raw_glow = fs.find_texture(f"textures/{tname}_glow")
            if raw_glow is not None:
                glow_uri, _, _, _ = encode_texture_bytes(raw_glow, min(mdim, 256), False, 74)
                glow_cnt += 1

            textures_out.append({
                "n": tname,
                "u": uri,
                "g": glow_uri,
                "at": 1 if alpha_test else 0,
            })
    finally:
        fs.close()

    # 4. Compute Smart Landmark Teleport Presets (auto-refined from BSP destructibles + Scheme A)
    def _group_center(grp: str, fallback: List[float]) -> List[float]:
        boxes = [(d["bmin"], d["bmax"]) for d in dynamic_out if d["group"] == grp and d["kind"] != "rubble"]
        if not boxes:
            return fallback
        mn = [min(b[0][k] for b in boxes) for k in range(3)]
        mx = [max(b[1][k] for b in boxes) for k in range(3)]
        return [round(0.5 * (mn[k] + mx[k]), 1) for k in range(3)]

    padre_c = _group_center("padre", d_to_u(23.6, -724.7, 52.0))
    fox_c = _group_center("fox", d_to_u(22.0, -20.0, 48.0))
    sign_c = _group_center("sign", d_to_u(113.0, -565.0, 18.0))
    garage_c = d_to_u(306.6, -722.2, 34.0)
    gw_c = d_to_u(635.0, 40.0, 18.0)
    gc_c = d_to_u(338.0, -230.0, 16.0)
    larry_c = d_to_u(288.0, 80.0, 16.0)

    roof_sp = [sp for sp in skypads if sp["origin"][2] > 120.0]
    if roof_sp:
        sp_look = [
            round(sum(sp["origin"][0] for sp in roof_sp) / len(roof_sp), 1),
            round(sum(sp["origin"][1] for sp in roof_sp) / len(roof_sp), 1),
            420.0,
        ]
    else:
        sp_look = d_to_u(180.0, -280.0, 35.0)

    landmarks = [
        {
            "key": "1",
            "id": "padre",
            "name": "Padre Hotel",
            "pos": [round(padre_c[0] + 1580, 1), round(padre_c[1] - 320, 1), 240.0],
            "look": [padre_c[0], padre_c[1], 520.0],
        },
        {
            "key": "2",
            "id": "fox",
            "name": "Fox Theater",
            "pos": [round(fox_c[0] + 1240, 1), round(fox_c[1] - 1180, 1), 240.0],
            "look": [round(fox_c[0] + 220, 1), round(fox_c[1] - 420, 1), 540.0],
        },
        {
            "key": "3",
            "id": "garage",
            "name": "Parking Garage",
            "pos": d_to_u(150.0, -830.0, 48.0),
            "look": garage_c,
        },
        {
            "key": "4",
            "id": "golden_west",
            "name": "Golden West Casino",
            "pos": d_to_u(820.0, -135.0, 42.0),
            "look": gw_c,
        },
        {
            "key": "5",
            "id": "great_castle",
            "name": "The Great Castle",
            "pos": d_to_u(475.0, -125.0, 36.0),
            "look": gc_c,
        },
        {
            "key": "6",
            "id": "larrys",
            "name": "Larry's Warehouse",
            "pos": d_to_u(290.0, -90.0, 44.0),
            "look": larry_c,
        },
        {
            "key": "7",
            "id": "sign",
            "name": "Bakersfield Sign",
            "pos": [round(sign_c[0] + 120, 1), round(sign_c[1] - 920, 1), 160.0],
            "look": [sign_c[0], sign_c[1], round(sign_c[2] + 40, 1)],
        },
        {
            "key": "8",
            "id": "skypad",
            "name": "SkyPad View",
            "pos": d_to_u(380.0, -560.0, 215.0),
            "look": sp_look,
        },
    ]

    gz_bin = gzip.compress(bytes(arena.buf), compresslevel=9)
    print(
        f"[pack] {len(static_batches)} static batches, {len(dynamic_out)} dynamic submodels, "
        f"{total_tris:,} tris, {len(textures_out)} textures ({glow_cnt} glow, {missing_cnt} fallback), "
        f"{len(skypads)} skypads | bin {len(arena.buf)/1e6:.2f} MB -> {len(gz_bin)/1e6:.2f} MB gz "
        f"({time.time() - t0:.1f}s)",
        flush=True,
    )

    return {
        "mapName": os.path.splitext(os.path.basename(bsp_path))[0],
        "stats": {
            "tris": total_tris,
            "textures": len(textures_out),
            "glowTextures": glow_cnt,
            "dynamicSubmodels": len(dynamic_out),
            "foxPieces": sum(1 for d in dynamic_out if d["group"] == "fox" and d["kind"] != "rubble"),
            "padrePieces": sum(1 for d in dynamic_out if d["group"] == "padre" and d["kind"] != "rubble"),
            "signPieces": sum(1 for d in dynamic_out if d["group"] == "sign" and d["kind"] != "rubble"),
            "glassBays": sum(1 for d in dynamic_out if d["group"] == "glass"),
            "skypads": len(skypads),
            "gokarts": gokart_count,
            "jetpacks": jetpack_count,
            "ericCannons": cannon_count,
        },
        "sectors": {str(k): [round(x, 1) for x in v] for k, v in sector_bounds.items()},
        "lightmaps": lm_uris,
        "textures": textures_out,
        "static": static_batches,
        "dynamic": dynamic_out,
        "skypads": skypads,
        "landmarks": landmarks,
        "binGz": base64.b64encode(gz_bin).decode("ascii"),
    }


# ---------------------------------------------------------------------------
# Standalone Zero-Dependency Offline HTML5 + Pure WebGL2 Template
# ---------------------------------------------------------------------------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --bg: #0c0e14;
    --panel: rgba(14, 17, 24, 0.84);
    --border: rgba(240, 198, 116, 0.28);
    --gold: #f0c674;
    --amber: #e68a3e;
    --red: #e05252;
    --cyan: #5ed4f3;
    --green: #69d18b;
    --text: #eef1f7;
    --muted: #9aa4b6;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; user-select: none; }
  #gl { position: fixed; inset: 0; width: 100%; height: 100%; display: block; cursor: grab; }
  #gl.dragging { cursor: grabbing; }
  #loading {
    position: fixed; inset: 0; z-index: 50; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 14px;
    background: radial-gradient(circle at 50% 42%, #1d1a16 0%, #0b0d12 72%);
    transition: opacity 0.35s ease;
  }
  #loading.gone { opacity: 0; pointer-events: none; }
  #loading h1 { font-size: 26px; letter-spacing: 0.08em; color: var(--gold); text-transform: uppercase; }
  #load-bar-wrap { width: 320px; height: 8px; border-radius: 99px; background: rgba(255,255,255,0.1); overflow: hidden; }
  #load-bar { width: 8%; height: 100%; background: linear-gradient(90deg, var(--amber), var(--gold)); transition: width 0.15s; }
  #load-msg { font-size: 13px; color: var(--muted); font-family: ui-monospace, Consolas, monospace; }

  .hud { position: fixed; z-index: 10; pointer-events: none; transition: opacity 0.2s; }
  body.hud-hidden .hud { opacity: 0; pointer-events: none; }
  .card {
    pointer-events: auto; background: var(--panel); border: 1px solid var(--border);
    border-radius: 10px; backdrop-filter: blur(8px); box-shadow: 0 10px 28px rgba(0,0,0,0.45);
  }
  #hud-tl { top: 12px; left: 12px; padding: 10px 14px; max-width: 340px; }
  #hud-tl .title { font-weight: 800; font-size: 15px; letter-spacing: 0.06em; color: var(--gold); }
  #hud-tl .sub { font-size: 11px; color: var(--muted); margin-top: 3px; font-family: ui-monospace, Consolas, monospace; }
  #hud-tl .keys { font-size: 11px; color: #c7d0e0; margin-top: 7px; line-height: 1.45; }
  #hud-tl kbd { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); border-radius: 4px; padding: 1px 5px; font-size: 10px; font-family: ui-monospace, Consolas, monospace; }

  #hud-tr { top: 12px; right: 12px; width: 296px; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
  .sec-lbl { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--gold); display: flex; justify-content: space-between; align-items: center; }
  .btn-col { display: grid; grid-template-columns: 1fr; gap: 6px; }
  .btn-row { display: flex; gap: 6px; flex-wrap: wrap; }
  button {
    appearance: none; border: 1px solid rgba(255,255,255,0.16); background: rgba(255,255,255,0.07);
    color: var(--text); border-radius: 7px; padding: 7px 10px; font-size: 12px; font-weight: 600;
    cursor: pointer; transition: background 0.14s, border-color 0.14s, transform 0.08s; text-align: left;
  }
  button:hover { background: rgba(240, 198, 116, 0.16); border-color: var(--gold); }
  button:active { transform: scale(0.98); }
  button.demo-fox { border-color: rgba(230, 138, 62, 0.55); background: rgba(230, 138, 62, 0.14); }
  button.demo-padre { border-color: rgba(224, 82, 82, 0.55); background: rgba(224, 82, 82, 0.15); }
  button.demo-sign { border-color: rgba(240, 198, 116, 0.55); background: rgba(240, 198, 116, 0.13); }
  button.demo-glass { border-color: rgba(94, 212, 243, 0.55); background: rgba(94, 212, 243, 0.13); }
  button.active { background: rgba(240, 198, 116, 0.28); border-color: var(--gold); color: #fff; }
  .btn-sub { display: block; font-size: 10px; font-weight: 400; color: var(--muted); margin-top: 2px; }
  #demo-status {
    font-size: 11px; font-family: ui-monospace, Consolas, monospace; color: var(--gold);
    background: rgba(0,0,0,0.34); border-radius: 6px; padding: 6px 8px; min-height: 28px;
  }
  .opt-row { display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: #ccd4e2; gap: 8px; }
  .opt-row label { display: flex; align-items: center; gap: 5px; cursor: pointer; }
  .opt-row input[type=range] { width: 105px; accent-color: var(--gold); }

  #hud-bot {
    bottom: 12px; left: 50%; transform: translateX(-50%);
    padding: 8px 10px; display: flex; gap: 6px; flex-wrap: wrap; justify-content: center;
    max-width: calc(100vw - 24px);
  }
  #hud-bot button { padding: 6px 10px; font-size: 11.5px; text-align: center; white-space: nowrap; }
  #hud-bot .knum { color: var(--gold); font-family: ui-monospace, Consolas, monospace; margin-right: 4px; }

  #hud-toast {
    position: fixed; top: 14px; left: 50%; transform: translateX(-50%); z-index: 20;
    font-weight: 700; font-size: 13px; letter-spacing: 0.04em; color: #fff6dc;
    text-shadow: 0 2px 6px rgba(0,0,0,0.9); pointer-events: none; opacity: 0; transition: opacity 0.25s;
  }
  #hud-toast.show { opacity: 1; }
  #crosshair {
    position: fixed; left: 50%; top: 50%; width: 10px; height: 10px; margin: -5px 0 0 -5px;
    border: 1.5px solid rgba(255,255,255,0.45); border-radius: 50%; pointer-events: none; z-index: 9;
    display: none;
  }
  body.fps-lock #crosshair { display: block; }
  #show-hud-pill {
    position: fixed; bottom: 12px; right: 12px; z-index: 15; display: none;
    background: var(--panel); border: 1px solid var(--border); color: var(--gold);
    border-radius: 99px; padding: 6px 12px; font-size: 11px; font-weight: 700; cursor: pointer;
  }
  body.hud-hidden #show-hud-pill { display: block; }
</style>
</head>
<body>
<canvas id="gl"></canvas>
<div id="crosshair"></div>
<div id="hud-toast"></div>
<button id="show-hud-pill" type="button">Show HUD (H)</button>

<div id="loading">
  <h1>BAKERSFIELD-ISH 3D VIEWER</h1>
  <div id="load-bar-wrap"><div id="load-bar"></div></div>
  <div id="load-msg">Decompressing inline BSP2 geometry &amp; lightmaps...</div>
</div>

<div id="hud-tl" class="hud card">
  <div class="title">BAKERSFIELD-ISH · OFFLINE 3D</div>
  <div class="sub" id="stat-line">Loading map stats...</div>
  <div class="keys">
    <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> Fly · <kbd>Space</kbd>/<kbd>E</kbd> Up · <kbd>Q</kbd>/<kbd>C</kbd> Down · <kbd>Shift</kbd> Fast<br>
    <b>Drag mouse</b> to look · <kbd>F</kbd> PointerLock · <kbd>1</kbd>–<kbd>8</kbd> Landmarks · <kbd>H</kbd> HUD
  </div>
  <div class="sub" id="cam-pos" style="margin-top:6px;color:#f0c674;">POS: 0, 0, 0</div>
</div>

<div id="hud-tr" class="hud card">
  <div class="sec-lbl">
    <span>Interactive Destructibles</span>
    <span id="fps-badge" style="color:var(--muted);font-family:monospace;">-- FPS</span>
  </div>
  <div class="btn-col">
    <button type="button" class="demo-fox" id="btn-fox">
      Fox Theater — 3-Stage Collapse &amp; Rebuild
      <span class="btn-sub">Click 1→2→3: marquee/clock → tower → full crash + 25s rebuild</span>
    </button>
    <button type="button" class="demo-padre" id="btn-padre">
      Padre Hotel — 3-Stage Controlled Demolition
      <span class="btn-sub">Click 1→2→3: east wing → west/crown → full implosion + 24 boulders</span>
    </button>
    <button type="button" class="demo-sign" id="btn-sign">
      Bakersfield Sign — 3-Stage Break &amp; Topple
      <span class="btn-sub">Click 1→2→3: west cap → east cap → arch crash + bounce</span>
    </button>
    <div class="btn-row">
      <button type="button" class="demo-glass" id="btn-glass-near" style="flex:1;text-align:center;">Shatter Nearby Glass</button>
      <button type="button" class="demo-glass" id="btn-glass-all" style="flex:1;text-align:center;">Shatter All</button>
    </div>
    <div class="btn-row">
      <button type="button" id="btn-fox-reb" style="flex:1;text-align:center;">Fast Rebuild Fox</button>
      <button type="button" id="btn-reset" style="flex:1;text-align:center;border-color:rgba(105,209,139,0.5);color:#bdf5cf;">Reset All</button>
    </div>
  </div>
  <div id="demo-status">All landmarks intact · ready</div>
  <div class="opt-row">
    <label><input type="checkbox" id="chk-autofocus" checked> Auto-frame camera</label>
    <label><input type="checkbox" id="chk-shake" checked> Quake shake</label>
  </div>
  <div class="opt-row">
    <label><input type="checkbox" id="chk-skypads" checked> SkyPad arcs</label>
    <label>Speed <input type="range" id="rng-speed" min="250" max="2400" step="50" value="950"></label>
  </div>
  <div class="btn-row">
    <button type="button" id="btn-lit" style="flex:1;text-align:center;">Light: Baked .lit</button>
    <button type="button" id="btn-fpslock" style="flex:1;text-align:center;">FPS Lock (F)</button>
    <button type="button" id="btn-hidehud" style="padding:6px 9px;text-align:center;">HUD</button>
  </div>
</div>

<div id="hud-bot" class="hud card"></div>

<script>
"use strict";
const SCENE = /*__BAKERSFIELDISH_SCENE_DATA__*/null;

const $ = (id) => document.getElementById(id);
function setLoad(pct, msg) {
  $("load-bar").style.width = pct + "%";
  $("load-msg").textContent = msg;
}
let toastTimer = 0;
function showToast(msg) {
  const el = $("hud-toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2600);
}

// ---------- Inline gzip decode via native DecompressionStream (works offline under file://) ----------
async function gunzipBase64(b64) {
  const binStr = atob(b64);
  const bytes = new Uint8Array(binStr.length);
  for (let i = 0; i < binStr.length; i++) bytes[i] = binStr.charCodeAt(i);
  const ds = new DecompressionStream("gzip");
  const w = ds.writable.getWriter();
  w.write(bytes);
  w.close();
  return await new Response(ds.readable).arrayBuffer();
}

// ---------- Minimal 4x4 Matrix Math (Z-up right-handed Quake coordinates) ----------
function mat4Id(o) {
  o.fill(0); o[0] = o[5] = o[10] = o[15] = 1; return o;
}
function mat4Persp(o, fovy, aspect, near, far) {
  const f = 1.0 / Math.tan(fovy * 0.5), nf = 1.0 / (near - far);
  o.fill(0);
  o[0] = f / aspect; o[5] = f; o[10] = (far + near) * nf; o[11] = -1; o[14] = 2 * far * near * nf;
  return o;
}
function mat4LookAt(o, eye, ctr, up) {
  let zx = eye[0] - ctr[0], zy = eye[1] - ctr[1], zz = eye[2] - ctr[2];
  let l = Math.hypot(zx, zy, zz) || 1; zx /= l; zy /= l; zz /= l;
  let xx = up[1] * zz - up[2] * zy, xy = up[2] * zx - up[0] * zz, xz = up[0] * zy - up[1] * zx;
  l = Math.hypot(xx, xy, xz) || 1; xx /= l; xy /= l; xz /= l;
  const yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
  o[0] = xx; o[1] = yx; o[2] = zx; o[3] = 0;
  o[4] = xy; o[5] = yy; o[6] = zy; o[7] = 0;
  o[8] = xz; o[9] = yz; o[10] = zz; o[11] = 0;
  o[12] = -(xx * eye[0] + xy * eye[1] + xz * eye[2]);
  o[13] = -(yx * eye[0] + yy * eye[1] + yz * eye[2]);
  o[14] = -(zx * eye[0] + zy * eye[1] + zz * eye[2]);
  o[15] = 1;
  return o;
}
function mat4Mul(o, a, b) {
  const r = new Float32Array(16);
  for (let c = 0; c < 4; c++) {
    for (let rw = 0; rw < 4; rw++) {
      r[c * 4 + rw] = a[rw] * b[c * 4] + a[4 + rw] * b[c * 4 + 1] + a[8 + rw] * b[c * 4 + 2] + a[12 + rw] * b[c * 4 + 3];
    }
  }
  o.set(r);
  return o;
}
// Matches Zircon matrixlib.c bmodel convention: T(pos) * Rz(yaw) * Ry(pitch) * Rx(roll) * S(scale)
// Verified: +pitch tips +Z toward +X (East), +roll tips +Z toward -Y (South).
function mat4QuakeEntity(o, px, py, pz, pitchDeg, yawDeg, rollDeg, scale) {
  const D2R = Math.PI / 180;
  const cp = Math.cos(pitchDeg * D2R), sp = Math.sin(pitchDeg * D2R);
  const cy = Math.cos(yawDeg * D2R),   sy = Math.sin(yawDeg * D2R);
  const cr = Math.cos(rollDeg * D2R),  sr = Math.sin(rollDeg * D2R);
  const s = scale === undefined ? 1.0 : scale;
  // R = Rz(yaw) * Ry(pitch) * Rx(roll)
  const r00 = cy * cp;
  const r01 = cy * sp * sr - sy * cr;
  const r02 = cy * sp * cr + sy * sr;
  const r10 = sy * cp;
  const r11 = sy * sp * sr + cy * cr;
  const r12 = sy * sp * cr - cy * sr;
  const r20 = -sp;
  const r21 = cp * sr;
  const r22 = cp * cr;
  o[0] = r00 * s; o[1] = r10 * s; o[2] = r20 * s; o[3] = 0;
  o[4] = r01 * s; o[5] = r11 * s; o[6] = r21 * s; o[7] = 0;
  o[8] = r02 * s; o[9] = r12 * s; o[10] = r22 * s; o[11] = 0;
  o[12] = px;     o[13] = py;     o[14] = pz;      o[15] = 1;
  return o;
}
function clamp01(u) { return u < 0 ? 0 : (u > 1 ? 1 : u); }
function smoothstep(u) { u = clamp01(u); return u * u * (3 - 2 * u); }

// ---------- Main WebGL2 Boot ----------
(async function boot() {
  const canvas = $("gl");
  const gl = canvas.getContext("webgl2", { antialias: true, alpha: false, powerPreference: "high-performance" });
  if (!gl) {
    setLoad(100, "WebGL2 is required to run this viewer.");
    return;
  }
  const anisoExt = gl.getExtension("EXT_texture_filter_anisotropic");
  const maxAniso = anisoExt ? Math.min(8, gl.getParameter(anisoExt.MAX_TEXTURE_MAX_ANISOTROPY_EXT)) : 1;

  setLoad(18, "Decompressing gzipped BSP2 geometry arena...");
  const AB = await gunzipBase64(SCENE.binGz);

  setLoad(42, "Compiling WebGL2 shaders...");
  function mkProg(vs, fs) {
    const p = gl.createProgram();
    for (const [tp, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const sh = gl.createShader(tp);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh));
      gl.attachShader(p, sh);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }

  // 1. Procedural Post-Apocalyptic / Bakersfield Sunset-Blue Sky Dome
  const pSky = mkProg(`#version 300 es
    precision highp float;
    layout(location=0) in vec2 aQ;
    out vec2 vNdc;
    void main() { vNdc = aQ; gl_Position = vec4(aQ, 0.9999, 1.0); }`,
    `#version 300 es
    precision highp float;
    in vec2 vNdc;
    uniform vec3 uFwd;
    uniform vec3 uRight;
    uniform vec3 uUp;
    uniform float uTanHalfFov;
    uniform float uAspect;
    out vec4 fragColor;
    void main() {
      vec3 dir = normalize(uFwd + uRight * (vNdc.x * uAspect * uTanHalfFov) + uUp * (vNdc.y * uTanHalfFov));
      float h = clamp(dir.z, -0.2, 1.0);
      vec3 horizon = vec3(0.84, 0.69, 0.52);
      vec3 midSky  = vec3(0.42, 0.56, 0.72);
      vec3 zenith  = vec3(0.16, 0.28, 0.48);
      vec3 ground  = vec3(0.24, 0.20, 0.17);
      vec3 col = h >= 0.0
        ? mix(mix(horizon, midSky, smoothstep(0.0, 0.28, h)), zenith, smoothstep(0.22, 0.85, h))
        : mix(horizon, ground, smoothstep(0.0, -0.18, h));
      vec3 sunDir = normalize(vec3(0.48, -0.54, 0.69));
      float sd = max(dot(dir, sunDir), 0.0);
      col += vec3(1.0, 0.84, 0.56) * (pow(sd, 12.0) * 0.25 + pow(sd, 180.0) * 0.95);
      fragColor = vec4(col, 1.0);
    }`);

  // 2. World + Destructible BSP Submodel Shader (Baked .lit + Glow + Alpha Cutout + Fog)
  const pWorld = mkProg(`#version 300 es
    precision highp float;
    layout(location=0) in vec3 aPos;
    layout(location=1) in vec2 aUv;
    layout(location=2) in vec2 aLm;
    layout(location=3) in vec3 aNrm;
    uniform mat4 uVP;
    uniform mat4 uModel;
    out vec3 vWPos;
    out vec2 vUv;
    out vec2 vLm;
    out vec3 vNrm;
    void main() {
      vec4 wp = uModel * vec4(aPos, 1.0);
      vWPos = wp.xyz;
      vUv = aUv;
      vLm = aLm;
      vNrm = mat3(uModel) * aNrm;
      gl_Position = uVP * wp;
    }`,
    `#version 300 es
    precision highp float;
    in vec3 vWPos;
    in vec2 vUv;
    in vec2 vLm;
    in vec3 vNrm;
    uniform sampler2D uTex;
    uniform sampler2D uLmTex;
    uniform sampler2D uGlowTex;
    uniform vec3 uEye;
    uniform int uAlphaTest;
    uniform int uHasGlow;
    uniform int uLitMode;
    uniform float uAlpha;
    uniform float uTint;
    out vec4 fragColor;
    void main() {
      vec4 base = texture(uTex, vUv);
      if (uAlphaTest == 1 && base.a < 0.42) discard;
      vec3 N = normalize(gl_FrontFacing ? vNrm : -vNrm);
      vec3 lm = texture(uLmTex, vLm).rgb;
      vec3 sunDir = normalize(vec3(0.48, -0.54, 0.69));
      float ndl = max(dot(N, sunDir), 0.0);
      vec3 col;
      if (uLitMode == 2) {
        col = base.rgb;
      } else if (uLitMode == 1) {
        vec3 warmLm = mix(lm * 1.45, vec3(0.62, 0.56, 0.49) + vec3(0.55, 0.45, 0.34) * ndl, 0.35);
        col = base.rgb * warmLm;
      } else {
        vec3 lit = max(lm * 1.52, vec3(0.14, 0.13, 0.12));
        col = base.rgb * lit;
      }
      if (uHasGlow == 1) {
        col += texture(uGlowTex, vUv).rgb * 1.18;
      }
      // Glass Fresnel highlight
      if (uAlpha < 0.92) {
        vec3 V = normalize(uEye - vWPos);
        float fr = pow(1.0 - abs(dot(N, V)), 2.5);
        col = mix(col, vec3(0.74, 0.86, 0.96), 0.25 + 0.45 * fr);
      }
      // Subtle damage flash tint when triggering demolition
      col = mix(col, vec3(1.0, 0.68, 0.32), uTint);
      // Light warm atmospheric horizon haze (non-blinding)
      float dist = length(uEye - vWPos);
      float fog = clamp((dist - 5500.0) / 14500.0, 0.0, 0.42);
      col = mix(col, vec3(0.72, 0.63, 0.52), fog);
      fragColor = vec4(col, base.a * uAlpha);
    }`);

  // 3. 3D Faceted Concrete Boulder / Debris Shader
  const pBoulder = mkProg(`#version 300 es
    precision highp float;
    layout(location=0) in vec3 aPos;
    layout(location=1) in vec3 aNrm;
    uniform mat4 uVP;
    uniform mat4 uModel;
    out vec3 vNrm;
    out vec3 vWPos;
    void main() {
      vec4 wp = uModel * vec4(aPos, 1.0);
      vWPos = wp.xyz;
      vNrm = normalize(mat3(uModel) * aNrm);
      gl_Position = uVP * wp;
    }`,
    `#version 300 es
    precision highp float;
    in vec3 vNrm;
    in vec3 vWPos;
    uniform vec3 uColor;
    out vec4 fragColor;
    void main() {
      vec3 sun = normalize(vec3(0.48, -0.54, 0.69));
      float d = max(dot(normalize(vNrm), sun), 0.0);
      float hemi = 0.5 + 0.5 * vNrm.z;
      vec3 c = uColor * (mix(vec3(0.28, 0.25, 0.22), vec3(0.54, 0.50, 0.46), hemi) + vec3(0.88, 0.78, 0.64) * d * 0.78);
      fragColor = vec4(c, 1.0);
    }`);

  // 4. Volumetric Translucent Demolition Dust, Charge Flashes, Sparks & Glass Shards
  const pPart = mkProg(`#version 300 es
    precision highp float;
    layout(location=0) in vec3 aPos;
    layout(location=1) in float aSize;
    layout(location=2) in vec4 aCol;
    layout(location=3) in float aKind; // 0=dust, 1=flash/spark, 2=glass
    uniform mat4 uVP;
    uniform float uScalePx;
    out vec4 vCol;
    out float vKind;
    void main() {
      vec4 clip = uVP * vec4(aPos, 1.0);
      gl_Position = clip;
      float ps = aSize * uScalePx / max(clip.w, 16.0);
      gl_PointSize = clamp(ps, 2.0, 260.0);
      vCol = aCol;
      vKind = aKind;
    }`,
    `#version 300 es
    precision highp float;
    in vec4 vCol;
    in float vKind;
    out vec4 fragColor;
    void main() {
      vec2 p = gl_PointCoord * 2.0 - 1.0;
      float r2 = dot(p, p);
      if (r2 > 1.0) discard;
      if (vKind > 1.5) {
        // Sharp sparkling glass shard diamond
        float d = abs(p.x) * 1.4 + abs(p.y);
        if (d > 1.0) discard;
        fragColor = vec4(vCol.rgb * (1.25 - 0.35 * d), vCol.a * (1.0 - d * 0.6));
      } else if (vKind > 0.5) {
        // Bright charge-pop flash / welding & neon spark
        float g = exp(-r2 * 4.2);
        fragColor = vec4(vCol.rgb * (0.9 + 0.8 * g), vCol.a * g);
      } else {
        // Billowing translucent concrete dust curl (never blinding)
        float curl = 0.84 + 0.16 * sin(p.x * 5.2 + p.y * 3.7) * cos(p.y * 4.6 - p.x * 2.9);
        float soft = pow(max(0.0, 1.0 - r2), 1.65) * curl;
        float shade = 0.76 + 0.24 * clamp(0.5 - p.y * 0.6, 0.0, 1.0);
        fragColor = vec4(vCol.rgb * shade, min(0.46, vCol.a * soft));
      }
    }`);

  // 5. SkyPad 3D Parabolic Arc Shader
  const pArc = mkProg(`#version 300 es
    precision highp float;
    layout(location=0) in vec3 aPos;
    layout(location=1) in float aT;
    uniform mat4 uVP;
    out float vT;
    void main() { vT = aT; gl_Position = uVP * vec4(aPos, 1.0); }`,
    `#version 300 es
    precision highp float;
    in float vT;
    uniform float uTime;
    out vec4 fragColor;
    void main() {
      float pulse = 0.45 + 0.55 * pow(0.5 + 0.5 * sin((vT * 10.0 - uTime * 4.2) * 3.14159), 4.0);
      vec3 col = mix(vec3(0.24, 0.78, 1.0), vec3(1.0, 0.86, 0.38), pulse);
      fragColor = vec4(col, 0.45 + 0.45 * pulse);
    }`);

  function mkBuf(target, arr, usage) {
    const b = gl.createBuffer();
    gl.bindBuffer(target, b);
    gl.bufferData(target, arr, usage || gl.STATIC_DRAW);
    return b;
  }

  // Fullscreen sky quad VAO
  const skyVao = gl.createVertexArray();
  gl.bindVertexArray(skyVao);
  mkBuf(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]));
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

  // Procedural 3D faceted concrete boulder VAO (icosahedron with organic rock facets)
  const boulderVao = gl.createVertexArray();
  let boulderCount = 0;
  {
    const t = (1 + Math.sqrt(5)) / 2;
    const baseV = [
      [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
      [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
      [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ].map((v, i) => {
      const l = Math.hypot(v[0], v[1], v[2]);
      const jitter = 0.84 + ((i * 37 % 17) / 17) * 0.34;
      return [v[0] / l * jitter, v[1] / l * jitter, v[2] / l * jitter];
    });
    const faces = [
      [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
      [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
      [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
      [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1],
    ];
    const bData = [];
    for (const [i0, i1, i2] of faces) {
      const a = baseV[i0];
      let b = baseV[i1], c = baseV[i2];
      let ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
      let vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
      let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const cx = (a[0] + b[0] + c[0]) / 3, cy = (a[1] + b[1] + c[1]) / 3, cz = (a[2] + b[2] + c[2]) / 3;
      if (nx * cx + ny * cy + nz * cz < 0) {
        const tmp = b; b = c; c = tmp;
        nx = -nx; ny = -ny; nz = -nz;
      }
      const nl = Math.hypot(nx, ny, nz) || 1;
      nx /= nl; ny /= nl; nz /= nl;
      for (const p of [a, b, c]) bData.push(p[0], p[1], p[2], nx, ny, nz);
    }
    boulderCount = faces.length * 3;
    gl.bindVertexArray(boulderVao);
    mkBuf(gl.ARRAY_BUFFER, new Float32Array(bData));
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 24, 12);
  }

  // SkyPad parabolic arcs VAO
  const arcVao = gl.createVertexArray();
  const arcRanges = [];
  {
    const aVerts = [];
    let cursor = 0;
    const steps = 28;
    for (const sp of SCENE.skypads) {
      const o = sp.origin, d = sp.pos1;
      const apex = Math.max(sp.height || 1800, Math.max(o[2], d[2]) + 320);
      for (let i = 0; i <= steps; i++) {
        const u = i / steps;
        const x = o[0] + (d[0] - o[0]) * u;
        const y = o[1] + (d[1] - o[1]) * u;
        const zBase = o[2] + (d[2] - o[2]) * u;
        const z = zBase + 4 * u * (1 - u) * (apex - 0.5 * (o[2] + d[2]));
        aVerts.push(x, y, z, u);
      }
      arcRanges.push([cursor, steps + 1]);
      cursor += steps + 1;
    }
    gl.bindVertexArray(arcVao);
    mkBuf(gl.ARRAY_BUFFER, new Float32Array(aVerts.length ? aVerts : [0, 0, 0, 0]));
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 16, 0);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1, 1, gl.FLOAT, false, 16, 12);
  }

  // Upload batch VAOs from binary arena (28 bytes per vertex: 3f pos, 2f uv, 2u16 lm, 4i8 nrm)
  setLoad(58, "Building WebGL2 vertex buffers...");
  function createBatchVao(b) {
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const vSlice = new Uint8Array(AB, b.v[0], b.v[1]);
    mkBuf(gl.ARRAY_BUFFER, vSlice);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 28, 0);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 28, 12);
    gl.enableVertexAttribArray(2);
    gl.vertexAttribPointer(2, 2, gl.UNSIGNED_SHORT, true, 28, 20);
    gl.enableVertexAttribArray(3);
    gl.vertexAttribPointer(3, 3, gl.BYTE, true, 28, 24);
    const iSlice = b.it === 2
      ? new Uint16Array(AB, b.i[0], b.i[1] >> 1)
      : new Uint32Array(AB, b.i[0], b.i[1] >> 2);
    mkBuf(gl.ELEMENT_ARRAY_BUFFER, iSlice);
    b.vao = vao;
    b.glType = b.it === 2 ? gl.UNSIGNED_SHORT : gl.UNSIGNED_INT;
  }

  const opaqueStatic = [];
  const transStatic = [];
  for (const b of SCENE.static) {
    createBatchVao(b);
    if (b.a < 0.98) transStatic.push(b);
    else opaqueStatic.push(b);
  }
  for (const d of SCENE.dynamic) {
    for (const b of d.batches) createBatchVao(b);
    d.ctr = [
      0.5 * (d.bmin[0] + d.bmax[0]),
      0.5 * (d.bmin[1] + d.bmax[1]),
      0.5 * (d.bmin[2] + d.bmax[2]),
    ];
    d.shattered = false;
  }

  // Load lightmaps & textures asynchronously (render begins as soon as lightmaps decode!)
  setLoad(74, "Decoding lightmap atlases & textures...");
  function loadGlTex(uri, isRepeat, fallbackRgba) {
    const tx = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tx);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(fallbackRgba));
    const p = new Promise((resolve) => {
      const im = new Image();
      im.onload = () => {
        gl.bindTexture(gl.TEXTURE_2D, tx);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, isRepeat ? gl.REPEAT : gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, isRepeat ? gl.REPEAT : gl.CLAMP_TO_EDGE);
        if (isRepeat) {
          gl.generateMipmap(gl.TEXTURE_2D);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
          if (anisoExt) gl.texParameterf(gl.TEXTURE_2D, anisoExt.TEXTURE_MAX_ANISOTROPY_EXT, maxAniso);
        } else {
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        }
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        resolve();
      };
      im.onerror = () => resolve();
      im.src = uri;
    });
    return { tx, promise: p };
  }

  const lmObjs = SCENE.lightmaps.map((u) => loadGlTex(u, false, [215, 210, 200, 255]));
  const glLm = lmObjs.map((o) => o.tx);
  const glTex = [];
  const glGlow = [];
  const texProms = [];
  for (const t of SCENE.textures) {
    const o = loadGlTex(t.u, true, [135, 128, 118, 255]);
    glTex.push(o.tx);
    texProms.push(o.promise);
    if (t.g) {
      const g = loadGlTex(t.g, true, [0, 0, 0, 255]);
      glGlow.push(g.tx);
      texProms.push(g.promise);
    } else {
      glGlow.push(null);
    }
  }
  await Promise.all(lmObjs.map((o) => o.promise));
  setLoad(92, `Decoded ${SCENE.lightmaps.length} lightmap page(s), streaming ${SCENE.textures.length} textures...`);
  Promise.all(texProms).then(() => {});
  setTimeout(() => $("loading").classList.add("gone"), 180);

  // Dynamic particle buffer (up to 2,200 simultaneous particles: dust surges, flashes, sparks, glass)
  const MAX_PARTS = 2200;
  const parts = [];
  const partArr = new Float32Array(MAX_PARTS * 9); // pos3, size1, rgba4, kind1
  const partVao = gl.createVertexArray();
  gl.bindVertexArray(partVao);
  const partBuf = mkBuf(gl.ARRAY_BUFFER, partArr, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 36, 0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 1, gl.FLOAT, false, 36, 12);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 36, 16);
  gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 1, gl.FLOAT, false, 36, 32);

  function spawnPart(x, y, z, vx, vy, vz, size, sizeRate, r, g, b, a, life, grav, drag, kind) {
    if (parts.length >= MAX_PARTS) parts.shift();
    parts.push({ x, y, z, vx, vy, vz, size, sizeRate, r, g, b, a, age: 0, life, grav, drag, kind });
  }

  function spawnDustSurge(cx, cy, cz, count, spreadXY, spreadZ, outSpeed, upSpeed, scale) {
    for (let i = 0; i < count; i++) {
      const ang = Math.random() * Math.PI * 2;
      const rad = Math.random() * spreadXY;
      const spd = (0.45 + Math.random() * 0.75) * outSpeed;
      const warm = Math.random();
      const r = 0.42 + warm * 0.36;
      const g = 0.38 + warm * 0.33;
      const b = 0.33 + warm * 0.28;
      spawnPart(
        cx + Math.cos(ang) * rad, cy + Math.sin(ang) * rad, cz + Math.random() * spreadZ,
        Math.cos(ang) * spd, Math.sin(ang) * spd, upSpeed * (0.4 + Math.random() * 0.9),
        (55 + Math.random() * 68) * scale, (36 + Math.random() * 34) * scale,
        r, g, b, 0.34 + Math.random() * 0.14,
        5.8 + Math.random() * 4.2, -14.0, 1.45, 0
      );
    }
  }

  function spawnChargeFlash(x, y, z) {
    for (let i = 0; i < 6; i++) {
      spawnPart(
        x + (Math.random() - 0.5) * 28, y + (Math.random() - 0.5) * 28, z + (Math.random() - 0.5) * 18,
        (Math.random() - 0.5) * 240, (Math.random() - 0.5) * 240, 40 + Math.random() * 140,
        46 + Math.random() * 40, 120, 1.0, 0.84, 0.44, 0.95, 0.32 + Math.random() * 0.18, 0, 2.5, 1
      );
    }
    spawnDustSurge(x, y, z, 5, 36, 18, 190, 55, 0.75);
  }

  function spawnSparks(x, y, z, count, col) {
    for (let i = 0; i < count; i++) {
      const a = Math.random() * Math.PI * 2;
      const s = 120 + Math.random() * 340;
      spawnPart(
        x + (Math.random() - 0.5) * 32, y + (Math.random() - 0.5) * 32, z + (Math.random() - 0.5) * 24,
        Math.cos(a) * s, Math.sin(a) * s, 90 + Math.random() * 260,
        14 + Math.random() * 14, -6, col[0], col[1], col[2], 0.95,
        0.55 + Math.random() * 0.65, 520, 0.4, 1
      );
    }
  }

  function spawnGlassShards(ctr, bmin, bmax) {
    const sx = Math.max(24, bmax[0] - bmin[0]), sy = Math.max(24, bmax[1] - bmin[1]), sz = Math.max(24, bmax[2] - bmin[2]);
    for (let i = 0; i < 24; i++) {
      const a = Math.random() * Math.PI * 2;
      const s = 90 + Math.random() * 240;
      spawnPart(
        ctr[0] + (Math.random() - 0.5) * sx * 0.8,
        ctr[1] + (Math.random() - 0.5) * sy * 0.8,
        ctr[2] + (Math.random() - 0.5) * sz * 0.8,
        Math.cos(a) * s, Math.sin(a) * s, 60 + Math.random() * 180,
        15 + Math.random() * 16, -2, 0.72 + Math.random() * 0.26, 0.90 + Math.random() * 0.1, 1.0, 0.92,
        1.1 + Math.random() * 0.9, 640, 0.25, 2
      );
    }
  }

  // Rolling 3D Concrete Boulders (Padre Hotel collapse hero feature!)
  const boulders = [];
  function spawnPadreBoulders(cx, cy, zBase, count) {
    for (let i = 0; i < count; i++) {
      // Fan heavily East toward H St / Parking Garage and South toward 18th St
      const ang = (Math.random() < 0.72)
        ? (-Math.PI * 0.68 + Math.random() * Math.PI * 1.15)
        : (Math.random() * Math.PI * 2);
      const spd = 340 + Math.random() * 480;
      const rad = 18 + Math.random() * 22;
      const shade = 0.50 + Math.random() * 0.24;
      boulders.push({
        x: cx + Math.cos(ang) * (160 + Math.random() * 240),
        y: cy + Math.sin(ang) * (160 + Math.random() * 240),
        z: zBase + 140 + Math.random() * 480,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd,
        vz: 180 + Math.random() * 320,
        rx: Math.random() * 360, ry: Math.random() * 360, rz: Math.random() * 360,
        rad,
        col: [shade * 1.06, shade * 0.98, shade * 0.88],
        age: 0,
        life: 16.0 + Math.random() * 6.0,
        dustT: 0,
      });
    }
  }

  // ---------- Interactive 3-Stage Demolition State Machines ----------
  const demo = {
    fox:   { state: "intact", stage: 0, t: 0, stageT: [0, 0], blasts: 0, surgeDone: false, rebuildPulse: 0 },
    padre: { state: "intact", stage: 0, t: 0, stageT: [0, 0], chargesFired: 0, blasts: 0, wave: 0, surgeDone: false },
    sign:  { state: "intact", stage: 0, t: 0, stageT: [0, 0], impactDone: false },
  };
  let shakeAmp = 0;

  function pieceStage(d) {
    const r = (d.role || "").toLowerCase();
    if (d.group === "fox") {
      if (d.kind === "clock" || r === "marquee") return 1;
      if (r === "tower_upper" || r === "facade_e") return 2;
      return 3;
    }
    if (d.group === "padre") {
      if (r === "east_wing") return 1;
      if (r === "west_wing" || r === "crown") return 2;
      return 3;
    }
    if (d.group === "sign") {
      if (r.includes("west")) return 1;
      if (r.includes("east")) return 2;
      return 3;
    }
    return 3;
  }

  function spawnMultiBlast(cx, cy, cz, count, spreadXY, spreadZ) {
    for (let i = 0; i < count; i++) {
      const a = Math.random() * Math.PI * 2;
      const r = Math.random() * spreadXY;
      const bx = cx + Math.cos(a) * r, by = cy + Math.sin(a) * r, bz = cz + (Math.random() - 0.35) * spreadZ;
      spawnChargeFlash(bx, by, bz);
      spawnSparks(bx, by, bz, 12, [1.0, 0.78, 0.32]);
    }
  }

  function addShake(strength) {
    if (!$("chk-shake").checked) return;
    shakeAmp = Math.min(1.0, Math.max(shakeAmp, strength));
  }

  function groupCenter(grp, fallback) {
    const list = SCENE.dynamic.filter((d) => d.group === grp && d.kind !== "rubble");
    if (!list.length) return fallback;
    let x = 0, y = 0, z = 0;
    for (const d of list) { x += d.ctr[0]; y += d.ctr[1]; z += d.ctr[2]; }
    return [x / list.length, y / list.length, z / list.length];
  }

  const grpCtr = {
    fox:   groupCenter("fox",   SCENE.landmarks[1].look),
    padre: groupCenter("padre", SCENE.landmarks[0].look),
    sign:  groupCenter("sign",  SCENE.landmarks[6].look),
  };

  function updateStatusText() {
    const bits = [];
    if (demo.fox.state !== "intact" || demo.fox.stage > 0) bits.push(`Fox: ${demo.fox.state} [S${demo.fox.stage}/3]`);
    if (demo.padre.state !== "intact" || demo.padre.stage > 0) bits.push(`Padre: ${demo.padre.state} [S${demo.padre.stage}/3]`);
    if (demo.sign.state !== "intact" || demo.sign.stage > 0) bits.push(`Sign: ${demo.sign.state} [S${demo.sign.stage}/3]`);
    const brkGlass = SCENE.dynamic.filter((d) => d.group === "glass" && d.shattered).length;
    if (brkGlass > 0) bits.push(`Glass shattered: ${brkGlass}`);
    $("demo-status").textContent = bits.length ? bits.join(" · ") : "All landmarks intact · ready";
  }

  // Smooth Camera Controller (WASD + Mouse-drag + PointerLock + Teleport Glide)
  const cam = {
    pos: SCENE.landmarks[0].pos.slice(),
    yaw: 0,
    pitch: 0,
    glide: null,
  };
  function aimCamAt(pos, look) {
    const dx = look[0] - pos[0], dy = look[1] - pos[1], dz = look[2] - pos[2];
    const h = Math.hypot(dx, dy) || 1;
    cam.yaw = Math.atan2(dy, dx);
    cam.pitch = Math.atan2(dz, h);
  }
  aimCamAt(cam.pos, SCENE.landmarks[0].look);

  function teleportTo(lm, instant) {
    const dx = lm.look[0] - lm.pos[0], dy = lm.look[1] - lm.pos[1], dz = lm.look[2] - lm.pos[2];
    const ty = Math.atan2(dy, dx);
    const tp = Math.atan2(dz, Math.hypot(dx, dy) || 1);
    if (instant) {
      cam.pos = lm.pos.slice(); cam.yaw = ty; cam.pitch = tp; cam.glide = null;
      return;
    }
    let dyaw = ty - cam.yaw;
    while (dyaw > Math.PI) dyaw -= Math.PI * 2;
    while (dyaw < -Math.PI) dyaw += Math.PI * 2;
    cam.glide = {
      t: 0, dur: 0.75,
      p0: cam.pos.slice(), p1: lm.pos.slice(),
      y0: cam.yaw, y1: cam.yaw + dyaw,
      pt0: cam.pitch, pt1: tp,
    };
    showToast("View: " + lm.name);
  }

  // Populate landmark buttons & stats
  const st = SCENE.stats;
  $("stat-line").textContent =
    `${SCENE.mapName} · ${(st.tris/1000).toFixed(1)}k tris · ${st.textures} tex · ${st.skypads} SkyPads · ${st.gokarts} Karts`;
  const botEl = $("hud-bot");
  SCENE.landmarks.forEach((lm) => {
    const b = document.createElement("button");
    b.type = "button";
    b.innerHTML = `<span class="knum">${lm.key}</span>${lm.name}`;
    b.onclick = () => teleportTo(lm, false);
    botEl.appendChild(b);
  });

  // Trigger Buttons (3-Stage Progressive Break -> Final Crash + Rich Multi-Point Explosions!)
  $("btn-fox").onclick = () => {
    if ($("chk-autofocus").checked) teleportTo(SCENE.landmarks[1], false);
    const fc = grpCtr.fox;
    if (demo.fox.state === "rubble" || demo.fox.state === "rebuilding") {
      demo.fox = { state: "intact", stage: 0, t: 0, stageT: [0, 0], blasts: 0, surgeDone: false, rebuildPulse: 0 };
    }
    if (demo.fox.stage === 0) {
      demo.fox.state = "damaged"; demo.fox.stage = 1; demo.fox.stageT[0] = 0;
      spawnMultiBlast(fc[0] + 180, fc[1] - 380, fc[2] + 160, 4, 240, 220);
      spawnDustSurge(fc[0] + 160, fc[1] - 320, 140, 28, 220, 80, 240, 75, 1.0);
      addShake(0.42);
      showToast("FOX STAGE 1/3 — CLOCK & MARQUEE BLOWN OFF! (Click again for Stage 2)");
    } else if (demo.fox.stage === 1) {
      demo.fox.state = "damaged"; demo.fox.stage = 2; demo.fox.stageT[1] = 0;
      spawnMultiBlast(fc[0] + 140, fc[1] - 240, fc[2] + 340, 5, 280, 260);
      spawnDustSurge(fc[0] + 120, fc[1] - 200, 180, 36, 260, 95, 280, 90, 1.1);
      addShake(0.55);
      showToast("FOX STAGE 2/3 — UPPER BELFRY & EAST FACADE SHEARED! (Click again for Final Crash)");
    } else {
      demo.fox.state = "collapsing"; demo.fox.stage = 3; demo.fox.t = 0; demo.fox.blasts = 0; demo.fox.surgeDone = false;
      spawnMultiBlast(fc[0], fc[1], fc[2] + 120, 6, 360, 320);
      addShake(0.68);
      showToast("FOX STAGE 3/3 — FINAL CATASTROPHIC CRASH & 25s REBUILD!");
    }
  };
  $("btn-fox-reb").onclick = () => {
    demo.fox = { state: "rebuilding", stage: 3, t: 0, stageT: [9, 9], blasts: 10, surgeDone: true, rebuildPulse: 0 };
    if ($("chk-autofocus").checked) teleportTo(SCENE.landmarks[1], false);
    showToast("FOX THEATER — SLOW STAGED REBUILD (25s)");
  };
  $("btn-padre").onclick = () => {
    if ($("chk-autofocus").checked) teleportTo(SCENE.landmarks[0], false);
    const pc = grpCtr.padre;
    if (demo.padre.state === "rubble") {
      demo.padre = { state: "intact", stage: 0, t: 0, stageT: [0, 0], chargesFired: 0, blasts: 0, wave: 0, surgeDone: false };
      boulders.length = 0;
    }
    if (demo.padre.stage === 0) {
      demo.padre.state = "damaged"; demo.padre.stage = 1; demo.padre.stageT[0] = 0;
      spawnMultiBlast(pc[0] + 340, pc[1], 320, 6, 240, 380);
      spawnDustSurge(pc[0] + 320, pc[1], 140, 40, 280, 110, 280, 95, 1.15);
      spawnPadreBoulders(pc[0] + 320, pc[1], 240, 6);
      addShake(0.50);
      showToast("PADRE STAGE 1/3 — EAST WING BLOWN OUT! (Click again for Stage 2)");
    } else if (demo.padre.stage === 1) {
      demo.padre.state = "damaged"; demo.padre.stage = 2; demo.padre.stageT[1] = 0;
      spawnMultiBlast(pc[0] - 260, pc[1], 460, 7, 320, 420);
      spawnDustSurge(pc[0] - 180, pc[1], 180, 48, 340, 120, 320, 105, 1.25);
      spawnPadreBoulders(pc[0], pc[1], 300, 6);
      addShake(0.62);
      showToast("PADRE STAGE 2/3 — WEST WING & CROWN SHEARED! (Click again for Final Implosion)");
    } else {
      demo.padre.state = "collapsing"; demo.padre.stage = 3; demo.padre.t = 0; demo.padre.chargesFired = 0; demo.padre.blasts = 0; demo.padre.wave = 0; demo.padre.surgeDone = false;
      spawnMultiBlast(pc[0], pc[1], 240, 8, 440, 460);
      addShake(0.75);
      showToast("PADRE STAGE 3/3 — FULL CONTROLLED DEMOLITION IMPLOSION!");
    }
  };
  $("btn-sign").onclick = () => {
    if ($("chk-autofocus").checked) teleportTo(SCENE.landmarks[6], false);
    const sc = grpCtr.sign;
    if (demo.sign.state === "rubble") {
      demo.sign = { state: "intact", stage: 0, t: 0, stageT: [0, 0], impactDone: false };
    }
    if (demo.sign.stage === 0) {
      demo.sign.state = "damaged"; demo.sign.stage = 1; demo.sign.stageT[0] = 0;
      spawnMultiBlast(sc[0] - 460, sc[1], 180, 3, 90, 90);
      spawnSparks(sc[0] - 460, sc[1], 160, 32, [0.45, 0.85, 1.0]);
      addShake(0.32);
      showToast("SIGN STAGE 1/3 — WEST CAP SHEARED! (Click again for Stage 2)");
    } else if (demo.sign.stage === 1) {
      demo.sign.state = "damaged"; demo.sign.stage = 2; demo.sign.stageT[1] = 0;
      spawnMultiBlast(sc[0] + 460, sc[1], 180, 3, 90, 90);
      spawnSparks(sc[0] + 460, sc[1], 160, 32, [1.0, 0.84, 0.35]);
      addShake(0.36);
      showToast("SIGN STAGE 2/3 — EAST CAP SHEARED! (Click again for Final Topple)");
    } else {
      demo.sign.state = "collapsing"; demo.sign.stage = 3; demo.sign.t = 0; demo.sign.impactDone = false;
      spawnMultiBlast(sc[0], sc[1], 140, 4, 480, 120);
      spawnSparks(sc[0] - 320, sc[1], 72, 36, [0.45, 0.85, 1.0]);
      spawnSparks(sc[0] + 320, sc[1], 72, 36, [1.0, 0.84, 0.35]);
      addShake(0.45);
      showToast("SIGN STAGE 3/3 — FULL ARCH TOPPLE ACROSS H ST!");
    }
  };
  $("btn-glass-near").onclick = () => {
    let hit = 0;
    for (const d of SCENE.dynamic) {
      if (d.group !== "glass" || d.shattered) continue;
      const dist = Math.hypot(d.ctr[0] - cam.pos[0], d.ctr[1] - cam.pos[1], d.ctr[2] - cam.pos[2]);
      if (dist < 2600) { d.shattered = true; spawnGlassShards(d.ctr, d.bmin, d.bmax); hit++; }
    }
    if (hit === 0) {
      // Shatter closest 12 bays anywhere if camera is high in the sky
      const intact = SCENE.dynamic.filter((d) => d.group === "glass" && !d.shattered);
      intact.sort((a, b) =>
        Math.hypot(a.ctr[0] - cam.pos[0], a.ctr[1] - cam.pos[1]) -
        Math.hypot(b.ctr[0] - cam.pos[0], b.ctr[1] - cam.pos[1])
      );
      for (const d of intact.slice(0, 12)) { d.shattered = true; spawnGlassShards(d.ctr, d.bmin, d.bmax); hit++; }
    }
    showToast(hit ? `SHATTERED ${hit} GLASS WINDOW BAYS!` : "All glass bays already shattered!");
  };
  $("btn-glass-all").onclick = () => {
    let hit = 0;
    for (const d of SCENE.dynamic) {
      if (d.group === "glass" && !d.shattered) {
        d.shattered = true;
        if (hit < 28) spawnGlassShards(d.ctr, d.bmin, d.bmax);
        hit++;
      }
    }
    showToast(`SHATTERED ALL ${hit} GLASS BAYS!`);
  };
  $("btn-reset").onclick = () => {
    demo.fox = { state: "intact", stage: 0, t: 0, stageT: [0, 0], blasts: 0, surgeDone: false, rebuildPulse: 0 };
    demo.padre = { state: "intact", stage: 0, t: 0, stageT: [0, 0], chargesFired: 0, blasts: 0, wave: 0, surgeDone: false };
    demo.sign = { state: "intact", stage: 0, t: 0, stageT: [0, 0], impactDone: false };
    boulders.length = 0;
    for (const d of SCENE.dynamic) d.shattered = false;
    showToast("All landmarks & glass restored intact");
  };

  let litMode = 0;
  const litLabels = ["Light: Baked .lit", "Light: Warm Apoc", "Light: Unlit"];
  $("btn-lit").onclick = () => {
    litMode = (litMode + 1) % 3;
    $("btn-lit").textContent = litLabels[litMode];
  };
  $("btn-hidehud").onclick = () => document.body.classList.toggle("hud-hidden");
  $("show-hud-pill").onclick = () => document.body.classList.remove("hud-hidden");
  $("btn-fpslock").onclick = () => {
    if (document.pointerLockElement === canvas) document.exitPointerLock();
    else canvas.requestPointerLock?.();
  };
  document.addEventListener("pointerlockchange", () => {
    document.body.classList.toggle("fps-lock", document.pointerLockElement === canvas);
  });

  // Keyboard & Mouse Input
  const keys = new Set();
  addEventListener("keydown", (e) => {
    const k = e.key.toLowerCase();
    keys.add(k);
    if (k === "h") document.body.classList.toggle("hud-hidden");
    if (k === "f") {
      if (document.pointerLockElement === canvas) document.exitPointerLock();
      else canvas.requestPointerLock?.();
    }
    const idx = parseInt(k, 10) - 1;
    if (idx >= 0 && idx < SCENE.landmarks.length) teleportTo(SCENE.landmarks[idx], false);
  });
  addEventListener("keyup", (e) => keys.delete(e.key.toLowerCase()));

  let dragging = false, lx = 0, ly = 0;
  canvas.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    dragging = true; lx = e.clientX; ly = e.clientY;
    canvas.classList.add("dragging");
  });
  addEventListener("mouseup", () => { dragging = false; canvas.classList.remove("dragging"); });
  addEventListener("mousemove", (e) => {
    if (document.pointerLockElement === canvas) {
      cam.glide = null;
      cam.yaw -= e.movementX * 0.0026;
      cam.pitch = Math.max(-1.48, Math.min(1.48, cam.pitch - e.movementY * 0.0026));
    } else if (dragging) {
      cam.glide = null;
      const dx = e.clientX - lx, dy = e.clientY - ly;
      lx = e.clientX; ly = e.clientY;
      cam.yaw -= dx * 0.0042;
      cam.pitch = Math.max(-1.48, Math.min(1.48, cam.pitch - dy * 0.0042));
    }
  });
  canvas.addEventListener("wheel", (e) => {
    const rng = $("rng-speed");
    const v = Math.max(250, Math.min(2400, Number(rng.value) - Math.sign(e.deltaY) * 100));
    rng.value = String(v);
  }, { passive: true });

  // ---------- Step Demolitions, Boulders & Particles ----------
  function stepSim(dt) {
    // Advance partial-break stage timers for all 3 landmarks
    for (const grp of ["fox", "padre", "sign"]) {
      const obj = demo[grp];
      if (obj.stage >= 1) obj.stageT[0] += dt;
      if (obj.stage >= 2) obj.stageT[1] += dt;
      if (obj.state === "damaged" && Math.random() < dt * 6) {
        const c = grpCtr[grp];
        spawnDustSurge(c[0], c[1], 180 + Math.random() * 260, 1, 220, 60, 110, 45, 0.72);
      }
    }

    // Fox Theater: 8.5s collapse -> 3.5s rubble hold -> 25s slow rebuild -> intact
    if (demo.fox.state === "collapsing") {
      demo.fox.t += dt;
      const t = demo.fox.t;
      const targetBlasts = Math.min(10, Math.floor(t / 0.72) + 1);
      while (demo.fox.blasts < targetBlasts && t < 7.4) {
        demo.fox.blasts++;
        spawnMultiBlast(grpCtr.fox[0], grpCtr.fox[1], 160 + (1 - clamp01(t / 7.5)) * 520, 2, 340, 220);
      }
      if (t < 7.8 && Math.random() < dt * 16) {
        spawnDustSurge(grpCtr.fox[0], grpCtr.fox[1], 140 + Math.random() * 420, 2, 260, 140, 160, 70, 0.9);
      }
      if (t >= 6.8 && !demo.fox.surgeDone) {
        demo.fox.surgeDone = true;
        spawnMultiBlast(grpCtr.fox[0], grpCtr.fox[1], 95, 5, 420, 160);
        spawnDustSurge(grpCtr.fox[0], grpCtr.fox[1], 48, 70, 380, 90, 380, 115, 1.35);
        addShake(0.75);
      }
      if (t >= 9.0) {
        demo.fox.state = "rubble";
        demo.fox.t = 0;
        showToast("FOX THEATER COLLAPSED — SLOW REBUILD STARTING SOON...");
      }
    } else if (demo.fox.state === "rubble") {
      demo.fox.t += dt;
      if (demo.fox.t >= 3.5) {
        demo.fox.state = "rebuilding";
        demo.fox.t = 0;
        showToast("FOX THEATER — REBUILDING TIER-BY-TIER (25s)...");
      }
    } else if (demo.fox.state === "rebuilding") {
      demo.fox.t += dt;
      demo.fox.rebuildPulse += dt;
      if (demo.fox.rebuildPulse > 0.16) {
        demo.fox.rebuildPulse = 0;
        const h = 40 + (demo.fox.t / 25.0) * 920;
        spawnSparks(grpCtr.fox[0] + (Math.random() - 0.5) * 420, grpCtr.fox[1] + (Math.random() - 0.5) * 480, h, 8, [1.0, 0.84, 0.36]);
      }
      if (demo.fox.t >= 25.0) {
        demo.fox.state = "intact";
        demo.fox.stage = 0;
        demo.fox.stageT = [0, 0];
        demo.fox.t = 0;
        showToast("FOX THEATER RESTORED INTACT!");
      }
    }

    // Padre Hotel: 0-2.2s rhythmic lower charge pops -> 2.2-9.8s inward V-collapse + 18 explosions -> boulders + huge dust surge
    if (demo.padre.state === "collapsing") {
      demo.padre.t += dt;
      const t = demo.padre.t;
      const pc = grpCtr.padre;
      // Rhythmic lower-floor charge pops (8 pops across 0.0..2.1s)
      const targetPops = Math.min(8, Math.floor(t / 0.26) + 1);
      while (demo.padre.chargesFired < targetPops && t < 2.25) {
        const idx = demo.padre.chargesFired++;
        const ang = idx * 0.85;
        spawnChargeFlash(pc[0] + Math.cos(ang) * 420, pc[1] + Math.sin(ang) * 420, 60 + (idx % 3) * 110);
        addShake(0.28);
      }
      // Extra staggered mid-collapse demolition blasts across floors (12 additional bursts!)
      const targetBlasts = Math.min(12, Math.floor(Math.max(0, t - 2.2) / 0.62) + 1);
      while (t >= 2.2 && demo.padre.blasts < targetBlasts && t < 9.8) {
        demo.padre.blasts++;
        const z = 80 + (1.0 - clamp01((t - 2.2) / 7.6)) * 780;
        spawnMultiBlast(pc[0], pc[1], z, 2, 460, 190);
      }
      // Floor-seam vertical dust curtains during pancaking
      if (t >= 2.1 && t < 10.2 && Math.random() < dt * 26) {
        spawnDustSurge(pc[0], pc[1], 120 + (1.0 - clamp01((t - 2.1) / 8.0)) * 820, 3, 460, 120, 220, 85, 1.15);
      }
      // 3 waves of 8 rolling/bouncing 3D concrete boulders (24 total!)
      if (t >= 3.8 && demo.padre.wave < 1) { demo.padre.wave = 1; spawnPadreBoulders(pc[0], pc[1], 360, 8); addShake(0.55); }
      if (t >= 6.4 && demo.padre.wave < 2) { demo.padre.wave = 2; spawnPadreBoulders(pc[0], pc[1], 240, 8); addShake(0.70); }
      if (t >= 9.0 && demo.padre.wave < 3) { demo.padre.wave = 3; spawnPadreBoulders(pc[0], pc[1], 160, 8); addShake(0.95); }
      // Massive non-blinding translucent base-surge dust cloud
      if (t >= 9.4 && !demo.padre.surgeDone) {
        demo.padre.surgeDone = true;
        spawnDustSurge(pc[0], pc[1], 42, 130, 560, 110, 520, 130, 1.65);
        addShake(1.0);
        // Auto-shatter nearby glass bays from shockwave
        for (const d of SCENE.dynamic) {
          if (d.group === "glass" && !d.shattered && Math.hypot(d.ctr[0] - pc[0], d.ctr[1] - pc[1]) < 1450) {
            d.shattered = true;
            spawnGlassShards(d.ctr, d.bmin, d.bmax);
          }
        }
      }
      if (t >= 12.2) {
        demo.padre.state = "rubble";
        demo.padre.t = 0;
        showToast("PADRE HOTEL DEMOLISHED — CLIMBABLE RUBBLE & BOULDERS!");
      }
    }

    // Bakersfield Sign: 4.5s hinge topple (auto-follows sign's actual bako_fall_angles direction) + neon sparks + elastic bounce
    if (demo.sign.state === "collapsing") {
      demo.sign.t += dt;
      const t = demo.sign.t;
      const sc = grpCtr.sign;
      const sp = SCENE.dynamic.find((d) => d.group === "sign" && d.kind === "piece");
      const fallDirY = (sp && sp.fallAngles && sp.fallAngles[2] < 0) ? 1.0 : -1.0;
      if (t < 3.6 && Math.random() < dt * 14) {
        spawnSparks(sc[0] + (Math.random() - 0.5) * 620, sc[1] + fallDirY * t * 65, 180 * (1 - t / 4.2) + 30, 3, [0.55, 0.88, 1.0]);
      }
      if (t >= 3.45 && !demo.sign.impactDone) {
        demo.sign.impactDone = true;
        spawnDustSurge(sc[0], sc[1] + fallDirY * 210, 28, 52, 340, 55, 290, 75, 1.05);
        spawnSparks(sc[0], sc[1] + fallDirY * 216, 48, 36, [1.0, 0.85, 0.35]);
        addShake(0.62);
      }
      if (t >= 4.6) {
        demo.sign.state = "rubble";
        demo.sign.t = 0;
        showToast("BAKERSFIELD SIGN TOPPLED — KART-RAMPABLE WRECKAGE!");
      }
    }

    // Step 3D rolling concrete boulders
    for (let i = boulders.length - 1; i >= 0; i--) {
      const b = boulders[i];
      b.age += dt;
      if (b.age >= b.life) { boulders.splice(i, 1); continue; }
      b.vz -= 780 * dt;
      b.x += b.vx * dt;
      b.y += b.vy * dt;
      b.z += b.vz * dt;
      if (b.z <= b.rad + 4.0) {
        b.z = b.rad + 4.0;
        if (Math.abs(b.vz) > 55) {
          b.vz = Math.abs(b.vz) * 0.52;
          b.vx *= 0.86; b.vy *= 0.86;
          spawnDustSurge(b.x, b.y, 12, 3, 24, 10, 85, 36, 0.42);
        } else {
          b.vz = 0;
          const drag = Math.pow(0.55, dt);
          b.vx *= drag; b.vy *= drag;
        }
      }
      const hspd = Math.hypot(b.vx, b.vy);
      if (hspd > 15) {
        b.rx += (b.vy / Math.max(b.rad, 10)) * dt * 57.3;
        b.ry -= (b.vx / Math.max(b.rad, 10)) * dt * 57.3;
        b.dustT += dt;
        if (b.z < b.rad + 22 && b.dustT > 0.14) {
          b.dustT = 0;
          spawnPart(b.x, b.y, 14, -b.vx * 0.15, -b.vy * 0.15, 28, 22, 18, 0.65, 0.58, 0.50, 0.26, 1.4, -8, 1.6, 0);
        }
      }
    }

    // Step particles
    for (let i = parts.length - 1; i >= 0; i--) {
      const p = parts[i];
      p.age += dt;
      if (p.age >= p.life) { parts.splice(i, 1); continue; }
      const d = Math.exp(-p.drag * dt);
      p.vx *= d; p.vy *= d;
      p.vz = (p.vz - p.grav * dt) * (p.kind === 0 ? d : 1.0);
      p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
      if (p.z < 6 && p.kind !== 0) { p.z = 6; p.vz = Math.abs(p.vz) * 0.35; p.vx *= 0.6; p.vy *= 0.6; }
      p.size = Math.max(2, p.size + p.sizeRate * dt);
    }

    shakeAmp = Math.max(0, shakeAmp - dt * 1.45);
    updateStatusText();
  }

  // Compute live transform matrix & visibility for each dynamic BSP submodel
  const tmpMat = new Float32Array(16);
  const idMat = mat4Id(new Float32Array(16));
  function evalDynamicTransform(d) {
    if (d.group === "glass") {
      if (d.shattered) return null;
      return { mat: mat4QuakeEntity(tmpMat, d.origin[0], d.origin[1], d.origin[2], 0, 0, 0, 1), alpha: d.alpha, tint: 0 };
    }
    const stObj = demo[d.group];
    const [ox, oy, oz] = d.origin;
    if (d.kind === "rubble") {
      if (stObj.state === "intact") return null;
      if (stObj.state === "rubble") {
        return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz, 0, 0, 0, 1), alpha: 1, tint: 0 };
      }
      if (stObj.state === "collapsing") {
        const revealT = d.group === "padre" ? 9.4 : (d.group === "fox" ? 6.8 : 3.5);
        if (stObj.t < revealT) return null;
        const u = smoothstep((stObj.t - revealT) / 0.75);
        return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz - (1 - u) * 240, 0, 0, 0, 1), alpha: 1, tint: 0 };
      }
      if (stObj.state === "rebuilding") {
        if (stObj.t > 3.6) return null;
        const u = smoothstep(stObj.t / 3.6);
        return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz - u * 260, 0, 0, 0, 1), alpha: 1, tint: 0 };
      }
      return null;
    }

    // Intact/damaged/collapsing/rebuilding architectural piece (or Fox clock)
    if (stObj.state === "intact") {
      return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz, 0, 0, 0, 1), alpha: d.alpha, tint: 0 };
    }
    if (stObj.state === "rubble") return null;

    // Early Stage 1 or Stage 2 partial break for this specific piece (while rest of building stands!)
    const pStg = pieceStage(d);
    if (stObj.state !== "rebuilding" && pStg <= 2 && stObj.stage >= pStg) {
      const pt = stObj.stageT[pStg - 1] || 0;
      if (d.kind === "clock") {
        if (pt > 0.55) return null;
        return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz, 0, 0, 0, 1), alpha: 1, tint: 0.7 };
      }
      const pDur = Math.min(3.4, Math.max(1.8, d.dur || 2.6));
      if (pt > pDur + 0.5) return null;
      const u = clamp01(pt / pDur);
      const f = 0.14 * u + 0.86 * Math.pow(u, 2.2);
      const px = ox + (d.fallShift[0] || 0) * f;
      const py = oy + (d.fallShift[1] || 0) * f;
      const pz = oz + (d.fallShift[2] || 0) * f - Math.max(360, d.fallDrop || 480) * f;
      return {
        mat: mat4QuakeEntity(tmpMat, px, py, pz, (d.fallAngles[0] || 0) * f, (d.fallAngles[1] || 0) * f, (d.fallAngles[2] || 0) * f, 1),
        alpha: d.alpha,
        tint: (1 - u) * 0.25,
      };
    }
    if (stObj.state === "damaged") {
      return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz, 0, 0, 0, 1), alpha: d.alpha, tint: 0 };
    }

    if (stObj.state === "collapsing") {
      if (d.kind === "clock") {
        if (stObj.t > 0.55) return null;
        return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz, 0, 0, 0, 1), alpha: 1, tint: 0.7 };
      }
      const revealT = d.group === "padre" ? 10.6 : (d.group === "fox" ? 7.8 : 4.4);
      if (stObj.t > revealT) return null;

      // Non-linear gravity & hinge curve matching docs/bakersfieldish_demolition_reference.md
      const delay = d.delay || (d.group === "padre" ? 2.2 : 0.3);
      const dur = Math.max(0.6, d.dur || (d.group === "padre" ? 6.8 : (d.group === "fox" ? 5.2 : 3.1)));
      if (stObj.t < delay) {
        const sh = (d.group === "padre" && stObj.t < 2.2) ? Math.sin(stObj.t * 48) * 3.0 : 0;
        return { mat: mat4QuakeEntity(tmpMat, ox + sh, oy, oz, 0, 0, 0, 1), alpha: d.alpha, tint: 0 };
      }
      const u = clamp01((stObj.t - delay) / dur);
      let f = 0.14 * u + 0.86 * Math.pow(u, 2.3);
      // Elastic street bounce tail for Bakersfield Sign
      let angMul = f;
      if (d.group === "sign" && u > 0.80) {
        const bu = (u - 0.80) / 0.20;
        const bounce = 0.095 * Math.abs(Math.sin(Math.PI * bu)) * Math.exp(-2.2 * bu);
        angMul = Math.max(0, 1.0 - bounce);
      }
      const px = ox + (d.fallShift[0] || 0) * f;
      const py = oy + (d.fallShift[1] || 0) * f;
      const pz = oz + (d.fallShift[2] || 0) * f - (d.fallDrop || 0) * f;
      const ap = (d.fallAngles[0] || 0) * angMul;
      const ay = (d.fallAngles[1] || 0) * angMul;
      const ar = (d.fallAngles[2] || 0) * angMul;
      return { mat: mat4QuakeEntity(tmpMat, px, py, pz, ap, ay, ar, 1), alpha: d.alpha, tint: 0 };
    }

    if (stObj.state === "rebuilding") {
      // Staged bottom-to-top vertical rebuild over 25s
      const baseWait = 3.2;
      const ord = d.rebuildOrder >= 0 ? d.rebuildOrder : (d.kind === "clock" ? 8 : Math.max(0, 6 - (d.delay || 0)));
      const tStart = baseWait + Math.min(16.0, ord * 2.1);
      const tDur = 4.2;
      if (stObj.t < tStart) return null;
      const u = smoothstep((stObj.t - tStart) / tDur);
      const riseDrop = (1.0 - u) * Math.max(260, d.fallDrop || 340);
      const glowPulse = (1.0 - u) * 0.35;
      return { mat: mat4QuakeEntity(tmpMat, ox, oy, oz - riseDrop, 0, 0, 0, 1), alpha: d.alpha, tint: glowPulse };
    }
    return null;
  }

  // ---------- Main Render Loop ----------
  const mProj = new Float32Array(16);
  const mView = new Float32Array(16);
  const mVP = new Float32Array(16);
  const bMat = new Float32Array(16);
  const fovRad = 68 * Math.PI / 180;
  const tanHalf = Math.tan(fovRad * 0.5);

  const uSky = {
    fwd: gl.getUniformLocation(pSky, "uFwd"),
    right: gl.getUniformLocation(pSky, "uRight"),
    up: gl.getUniformLocation(pSky, "uUp"),
    tan: gl.getUniformLocation(pSky, "uTanHalfFov"),
    asp: gl.getUniformLocation(pSky, "uAspect"),
  };
  const uW = {
    vp: gl.getUniformLocation(pWorld, "uVP"),
    model: gl.getUniformLocation(pWorld, "uModel"),
    tex: gl.getUniformLocation(pWorld, "uTex"),
    lm: gl.getUniformLocation(pWorld, "uLmTex"),
    glow: gl.getUniformLocation(pWorld, "uGlowTex"),
    eye: gl.getUniformLocation(pWorld, "uEye"),
    at: gl.getUniformLocation(pWorld, "uAlphaTest"),
    hg: gl.getUniformLocation(pWorld, "uHasGlow"),
    lmMode: gl.getUniformLocation(pWorld, "uLitMode"),
    alpha: gl.getUniformLocation(pWorld, "uAlpha"),
    tint: gl.getUniformLocation(pWorld, "uTint"),
  };
  const uB = {
    vp: gl.getUniformLocation(pBoulder, "uVP"),
    model: gl.getUniformLocation(pBoulder, "uModel"),
    col: gl.getUniformLocation(pBoulder, "uColor"),
  };
  const uP = {
    vp: gl.getUniformLocation(pPart, "uVP"),
    scalePx: gl.getUniformLocation(pPart, "uScalePx"),
  };
  const uA = {
    vp: gl.getUniformLocation(pArc, "uVP"),
    time: gl.getUniformLocation(pArc, "uTime"),
  };

  let lastT = performance.now(), fpsAcc = 0, fpsFrames = 0, uiTick = 0;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(1, Math.floor(window.innerWidth * dpr));
    const h = Math.max(1, Math.floor(window.innerHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
    }
    gl.viewport(0, 0, w, h);
  }
  addEventListener("resize", resize);
  resize();

  function frame(now) {
    requestAnimationFrame(frame);
    const dt = Math.min(0.05, Math.max(0.001, (now - lastT) * 0.001));
    lastT = now;
    fpsAcc += dt; fpsFrames++;
    if (fpsAcc >= 0.5) {
      $("fps-badge").textContent = Math.round(fpsFrames / fpsAcc) + " FPS";
      fpsAcc = 0; fpsFrames = 0;
    }

    // Camera teleport glide or WASD flight
    if (cam.glide) {
      cam.glide.t += dt;
      const s = smoothstep(cam.glide.t / cam.glide.dur);
      cam.pos[0] = cam.glide.p0[0] + (cam.glide.p1[0] - cam.glide.p0[0]) * s;
      cam.pos[1] = cam.glide.p0[1] + (cam.glide.p1[1] - cam.glide.p0[1]) * s;
      cam.pos[2] = cam.glide.p0[2] + (cam.glide.p1[2] - cam.glide.p0[2]) * s;
      cam.yaw = cam.glide.y0 + (cam.glide.y1 - cam.glide.y0) * s;
      cam.pitch = cam.glide.pt0 + (cam.glide.pt1 - cam.glide.pt0) * s;
      if (cam.glide.t >= cam.glide.dur) cam.glide = null;
    }

    const cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
    const cy = Math.cos(cam.yaw), sy = Math.sin(cam.yaw);
    const fwd = [cy * cp, sy * cp, sp];
    const right = [sy, -cy, 0];
    const spd = Number($("rng-speed").value) * (keys.has("shift") ? 2.8 : 1.0) * dt;
    let mx = 0, my = 0, mz = 0;
    if (keys.has("w") || keys.has("arrowup")) { mx += fwd[0]; my += fwd[1]; mz += fwd[2]; }
    if (keys.has("s") || keys.has("arrowdown")) { mx -= fwd[0]; my -= fwd[1]; mz -= fwd[2]; }
    if (keys.has("d") || keys.has("arrowright")) { mx += right[0]; my += right[1]; }
    if (keys.has("a") || keys.has("arrowleft")) { mx -= right[0]; my -= right[1]; }
    if (keys.has(" ") || keys.has("e")) mz += 1;
    if (keys.has("c") || keys.has("q") || keys.has("control")) mz -= 1;
    const ml = Math.hypot(mx, my, mz);
    if (ml > 0.01) {
      cam.glide = null;
      cam.pos[0] += (mx / ml) * spd;
      cam.pos[1] += (my / ml) * spd;
      cam.pos[2] += (mz / ml) * spd;
    }

    stepSim(dt);

    // Apply clamped non-blinding earthquake tremor
    const tSec = now * 0.001;
    const shPitch = shakeAmp * Math.sin(tSec * 37.0) * (4.2 * Math.PI / 180);
    const shRoll  = shakeAmp * Math.cos(tSec * 29.0) * (2.4 * Math.PI / 180);
    const effP = Math.max(-1.5, Math.min(1.5, cam.pitch + shPitch));
    const cpe = Math.cos(effP), spe = Math.sin(effP);
    const efwd = [cy * cpe, sy * cpe, spe];
    const up = [Math.sin(shRoll) * sy, -Math.sin(shRoll) * cy, Math.cos(shRoll)];
    const ctr = [cam.pos[0] + efwd[0] * 100, cam.pos[1] + efwd[1] * 100, cam.pos[2] + efwd[2] * 100];

    const aspect = canvas.width / Math.max(1, canvas.height);
    mat4Persp(mProj, fovRad, aspect, 8.0, 42000.0);
    mat4LookAt(mView, cam.pos, ctr, up);
    mat4Mul(mVP, mProj, mView);

    // Compute camera basis for sky shader
    const eright = [
      efwd[1] * up[2] - efwd[2] * up[1],
      efwd[2] * up[0] - efwd[0] * up[2],
      efwd[0] * up[1] - efwd[1] * up[0],
    ];
    const erl = Math.hypot(eright[0], eright[1], eright[2]) || 1;
    eright[0] /= erl; eright[1] /= erl; eright[2] /= erl;
    const eup = [
      eright[1] * efwd[2] - eright[2] * efwd[1],
      eright[2] * efwd[0] - eright[0] * efwd[2],
      eright[0] * efwd[1] - eright[1] * efwd[0],
    ];

    gl.clear(gl.DEPTH_BUFFER_BIT);

    // 1. Sky Dome
    gl.disable(gl.DEPTH_TEST);
    gl.disable(gl.BLEND);
    gl.useProgram(pSky);
    gl.uniform3fv(uSky.fwd, efwd);
    gl.uniform3fv(uSky.right, eright);
    gl.uniform3fv(uSky.up, eup);
    gl.uniform1f(uSky.tan, tanHalf);
    gl.uniform1f(uSky.asp, aspect);
    gl.bindVertexArray(skyVao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    // 2. Opaque Static World + Opaque Dynamic Submodels
    gl.enable(gl.DEPTH_TEST);
    gl.depthMask(true);
    gl.enable(gl.CULL_FACE);
    gl.cullFace(gl.BACK);
    gl.useProgram(pWorld);
    gl.uniformMatrix4fv(uW.vp, false, mVP);
    gl.uniform3fv(uW.eye, cam.pos);
    gl.uniform1i(uW.tex, 0);
    gl.uniform1i(uW.lm, 1);
    gl.uniform1i(uW.glow, 2);
    gl.uniform1i(uW.lmMode, litMode);

    // Extract 6 frustum planes from mVP for static sector culling
    const frPlanes = [
      [mVP[3]+mVP[0], mVP[7]+mVP[4], mVP[11]+mVP[8],  mVP[15]+mVP[12]],
      [mVP[3]-mVP[0], mVP[7]-mVP[4], mVP[11]-mVP[8],  mVP[15]-mVP[12]],
      [mVP[3]+mVP[1], mVP[7]+mVP[5], mVP[11]+mVP[9],  mVP[15]+mVP[13]],
      [mVP[3]-mVP[1], mVP[7]-mVP[5], mVP[11]-mVP[9],  mVP[15]-mVP[13]],
      [mVP[3]+mVP[2], mVP[7]+mVP[6], mVP[11]+mVP[10], mVP[15]+mVP[14]],
      [mVP[3]-mVP[2], mVP[7]-mVP[6], mVP[11]-mVP[10], mVP[15]-mVP[14]],
    ];
    const visSec = { "-1": true };
    for (const sk in SCENE.sectors) {
      if (sk === "-1") { visSec[sk] = true; continue; }
      const sb = SCENE.sectors[sk];
      let ok = true;
      for (let pi = 0; pi < 6; pi++) {
        const pl = frPlanes[pi];
        const px = pl[0] >= 0 ? sb[3] : sb[0];
        const py = pl[1] >= 0 ? sb[4] : sb[1];
        const pz = pl[2] >= 0 ? sb[5] : sb[2];
        if (pl[0] * px + pl[1] * py + pl[2] * pz + pl[3] < -128.0) { ok = false; break; }
      }
      visSec[sk] = ok;
    }

    let lastTex = -1, lastLm = -1, lastCull = -1;
    function drawBatchList(list, modelMat, alphaVal, tintVal, checkSec, allowCull) {
      gl.uniformMatrix4fv(uW.model, false, modelMat);
      gl.uniform1f(uW.tint, tintVal);
      for (const b of list) {
        if (checkSec && b.s !== undefined && !visSec[b.s]) continue;
        if (b.t !== lastTex) {
          lastTex = b.t;
          gl.activeTexture(gl.TEXTURE0);
          gl.bindTexture(gl.TEXTURE_2D, glTex[b.t]);
          const tinfo = SCENE.textures[b.t];
          gl.uniform1i(uW.at, tinfo.at);
          if (allowCull) {
            const wantCull = tinfo.at === 0 ? 1 : 0;
            if (wantCull !== lastCull) {
              lastCull = wantCull;
              if (wantCull) gl.enable(gl.CULL_FACE);
              else gl.disable(gl.CULL_FACE);
            }
          }
          if (glGlow[b.t]) {
            gl.activeTexture(gl.TEXTURE2);
            gl.bindTexture(gl.TEXTURE_2D, glGlow[b.t]);
            gl.uniform1i(uW.hg, 1);
          } else {
            gl.uniform1i(uW.hg, 0);
          }
        }
        if (b.l !== lastLm) {
          lastLm = b.l;
          gl.activeTexture(gl.TEXTURE1);
          gl.bindTexture(gl.TEXTURE_2D, glLm[b.l]);
        }
        gl.uniform1f(uW.alpha, alphaVal !== undefined ? alphaVal : b.a);
        gl.bindVertexArray(b.vao);
        gl.drawElements(gl.TRIANGLES, b.n, b.glType, 0);
      }
    }

    drawBatchList(opaqueStatic, idMat, undefined, 0, true, true);

    const transDyn = [];
    for (const d of SCENE.dynamic) {
      const xform = evalDynamicTransform(d);
      if (!xform) continue;
      if (xform.alpha < 0.96) {
        transDyn.push({ d, mat: new Float32Array(xform.mat), alpha: xform.alpha, tint: xform.tint });
      } else {
        drawBatchList(d.batches, xform.mat, xform.alpha, xform.tint, false, true);
      }
    }

    // 3. 3D Tumbling Concrete Boulders
    if (boulders.length) {
      gl.enable(gl.CULL_FACE);
      gl.useProgram(pBoulder);
      gl.uniformMatrix4fv(uB.vp, false, mVP);
      gl.bindVertexArray(boulderVao);
      for (const b of boulders) {
        mat4QuakeEntity(bMat, b.x, b.y, b.z, b.rx, b.ry, b.rz, b.rad);
        gl.uniformMatrix4fv(uB.model, false, bMat);
        gl.uniform3fv(uB.col, b.col);
        gl.drawArrays(gl.TRIANGLES, 0, boulderCount);
      }
    }

    // 4. Translucent Glass & Static Alpha Surfaces
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.depthMask(false);
    gl.disable(gl.CULL_FACE);
    gl.useProgram(pWorld);
    gl.uniformMatrix4fv(uW.vp, false, mVP);
    lastTex = -1; lastLm = -1; lastCull = 0;
    if (transStatic.length) drawBatchList(transStatic, idMat, undefined, 0, true, false);
    for (const item of transDyn) drawBatchList(item.d.batches, item.mat, item.alpha, item.tint, false, false);

    // 5. SkyPad 3D Parabolic Arcs
    if ($("chk-skypads").checked && arcRanges.length) {
      gl.useProgram(pArc);
      gl.uniformMatrix4fv(uA.vp, false, mVP);
      gl.uniform1f(uA.time, tSec);
      gl.bindVertexArray(arcVao);
      for (const [start, count] of arcRanges) {
        gl.drawArrays(gl.LINE_STRIP, start, count);
      }
    }

    // 6. Volumetric Demolition Dust, Flashes, Sparks & Glass Shards
    if (parts.length) {
      const nP = Math.min(parts.length, MAX_PARTS);
      for (let i = 0; i < nP; i++) {
        const p = parts[i];
        const fade = 1.0 - clamp01(p.age / p.life);
        const a = p.a * (p.kind === 0 ? Math.sin(clamp01(p.age / p.life) * Math.PI) : fade);
        const o = i * 9;
        partArr[o] = p.x; partArr[o + 1] = p.y; partArr[o + 2] = p.z;
        partArr[o + 3] = p.size;
        partArr[o + 4] = p.r; partArr[o + 5] = p.g; partArr[o + 6] = p.b; partArr[o + 7] = a;
        partArr[o + 8] = p.kind;
      }
      gl.useProgram(pPart);
      gl.uniformMatrix4fv(uP.vp, false, mVP);
      gl.uniform1f(uP.scalePx, canvas.height / (2.0 * tanHalf));
      gl.bindVertexArray(partVao);
      gl.bindBuffer(gl.ARRAY_BUFFER, partBuf);
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, partArr.subarray(0, nP * 9));
      gl.drawArrays(gl.POINTS, 0, nP);
    }

    gl.depthMask(true);
    gl.disable(gl.BLEND);

    uiTick += dt;
    if (uiTick >= 0.15) {
      uiTick = 0;
      $("cam-pos").textContent = `POS: ${cam.pos[0].toFixed(0)}, ${cam.pos[1].toFixed(0)}, ${cam.pos[2].toFixed(0)} · YAW ${(cam.yaw * 180 / Math.PI).toFixed(0)}°`;
    }
  }
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""


def write_offline_html(payload: Dict[str, Any], out_html: str, title: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(out_html)), exist_ok=True)
    # Escape '</' inside JSON so an inline <script> can never terminate prematurely
    json_str = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = (
        HTML_TEMPLATE
        .replace("__TITLE__", title)
        .replace("/*__BAKERSFIELDISH_SCENE_DATA__*/null", json_str, 1)
    )
    with open(out_html, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    sz_mb = os.path.getsize(out_html) / (1024 * 1024)
    print(f"[done] Wrote standalone offline HTML viewer: {out_html} ({sz_mb:.2f} MB)", flush=True)
    return out_html


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Build a single 100% offline self-contained WebGL2 HTML viewer for Bakersfield-ish."
    )
    ap.add_argument("--bsp", default=DEFAULT_BSP, help=f"Path to compiled .bsp (default: {DEFAULT_BSP}).")
    ap.add_argument("--lit", default=None, help="Path to colored .lit lightmap (auto-detected next to --bsp).")
    ap.add_argument("--out", default=DEFAULT_OUT, help=f"Output single HTML path (default: {DEFAULT_OUT}).")
    ap.add_argument("--title", default="Bakersfield-ish — Offline 3D Interactive Viewer", help="HTML page title.")
    ap.add_argument("--tex-max", type=int, default=256, help="Max dimension for regular world textures (default: 256).")
    ap.add_argument("--hero-tex-max", type=int, default=512, help="Max dimension for hero signage textures (default: 512).")
    ap.add_argument("--tex-quality", type=int, default=78, help="WebP quality 1-100 for world textures (default: 78).")
    ap.add_argument("--lm-atlas", type=int, default=4096, help="Lightmap atlas page size (default: 4096).")
    ap.add_argument("--lm-quality", type=int, default=88, help="WebP quality 1-100 for lightmap atlases (default: 88).")
    return ap.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    bsp_path = os.path.abspath(args.bsp)
    lit_path = os.path.abspath(args.lit) if args.lit else os.path.splitext(bsp_path)[0] + ".lit"
    if not os.path.isfile(lit_path):
        lit_path = None

    payload = build_scene_payload(
        bsp_path=bsp_path,
        lit_path=lit_path,
        tex_max=args.tex_max,
        hero_tex_max=args.hero_tex_max,
        tex_quality=args.tex_quality,
        lm_atlas_max=args.lm_atlas,
        lm_quality=args.lm_quality,
    )
    write_offline_html(payload, os.path.abspath(args.out), args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
