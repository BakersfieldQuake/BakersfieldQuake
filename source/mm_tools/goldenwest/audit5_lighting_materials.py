"""audit5_lighting_materials.py — Audit 5 of 5: Sunny Daylight Lighting, DarkPlaces WASM
web.cfg Parity, 0 Photo / 0 Generic Texture Enforcement, Signage Placement & Scale Check
for Golden West Casino & S Union Ave.

Outputs:
  - source/mm_tools/goldenwest/out/audit5_report.json
  - source/mm_tools/goldenwest/out/audit5_dp_webcfg_sheet.png
  - source/mm_tools/goldenwest/out/audit5_webgl_interiors.png
"""
from __future__ import annotations

import argparse
import collections
import functools
import http.server
import importlib
import json
import os
import re
import shutil
import socketserver
import struct
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR = os.path.dirname(HERE)
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GAME_ROOT = os.path.dirname(MOD_DIR)

if HERE not in sys.path:
    sys.path.insert(0, HERE)

from gw_lib import (  # noqa: E402
    ADAMS_ST_Y,
    AMADOR_AVE_Y,
    BELLE_TERRACE_Y,
    CASINO_BOUNDS_FT,
    DEFAULT_WAD_PATHS,
    DELAWARE_ST_X,
    MARIPOSA_AVE_Y,
    MAX_TEX_NAME_LEN,
    SPECIAL_TEXTURES,
    TRINITY_AVE_Y,
    U_FT,
    MapBuilder,
    is_forbidden_tex,
)
from audit1_capture import GW_AUDIT1_VIEWS  # noqa: E402
from audit3_nav import (  # noqa: E402
    DP_EXE,
    QuietHandler,
    SPOTS_CANDIDATES,
    _running_darkplaces_pids,
    load_spots,
)

OUT_DIR = os.path.join(HERE, "out")
BSP_PATH = os.path.join(MOD_DIR, "maps", "goldenwest.bsp")
LIT_PATH = os.path.join(MOD_DIR, "maps", "goldenwest.lit")
WEB_DIR = os.path.join(MM_TOOLS_DIR, "out", "web", "goldenwest")
MAP_CANDIDATES = (
    os.path.join(OUT_DIR, "goldenwest.map"),
    os.path.join(MM_TOOLS_DIR, "out", "maps", "goldenwest.map"),
)

# Zones sampled for BSP + QLIT luminance (ft)
LIGHTING_ZONES_FT: Tuple[Tuple[str, float, float, float, float, float, float], ...] = (
    ("EXT S Union Ave North", 178.0, 350.0, 277.0, 650.0, -0.5, 16.0),
    ("EXT S Union Ave Casino Front", 178.0, -60.0, 277.0, 120.0, -0.5, 16.0),
    ("EXT S Union Ave South", 178.0, -740.0, 277.0, -350.0, -0.5, 16.0),
    ("EXT E Belle Terrace", -120.0, BELLE_TERRACE_Y - 22.0, 520.0, BELLE_TERRACE_Y + 22.0, -0.5, 16.0),
    ("EXT Casino Courtyard & Portico", 90.0, -65.0, 172.0, 90.0, -0.5, 24.0),
    ("EXT El Don Brownfield", 285.0, 424.0, 600.0, 532.0, -0.5, 16.0),
    ("EXT Trinity & Delaware", -300.0, TRINITY_AVE_Y - 20.0, DELAWARE_ST_X + 20.0, TRINITY_AVE_Y + 20.0, -0.5, 16.0),
    ("EXT Adams St East", 285.0, ADAMS_ST_Y - 20.0, 520.0, ADAMS_ST_Y + 20.0, -0.5, 16.0),
    ("INT Golden West Casino Main Pit", -52.0, -70.0, 55.0, 75.0, 0.0, 18.0),
    ("INT Golden West Casino Rotunda", 55.0, -48.0, 102.0, 0.0, 0.0, 28.0),
    ("INT Carnitas Birria Diner", 102.0, 612.0, 146.0, 660.0, 0.0, 14.0),
    ("INT Star-Liter Motel", 296.0, 33.0, 493.0, 210.0, 0.0, 14.0),
    ("INT Ramos Tires Shop", -98.0, -334.0, 24.0, -284.0, 0.0, 16.0),
    ("INT Compas Auto Sales", -102.0, -584.0, 172.0, -342.0, 0.0, 14.0),
    ("INT Sunland Motel", 311.0, -315.0, 559.0, -275.0, 0.0, 14.0),
    ("INT Country Inn Motel", 310.0, -555.0, 636.0, -374.0, 0.0, 14.0),
    ("INT Playfair Market", 295.0, -662.0, 353.0, -605.0, 0.0, 14.0),
    ("INT Super 8 Hotel", -97.0, -728.0, 142.0, -591.0, 0.0, 18.0),
    ("EXT West Trinity / Delaware Residential", -400.0, -430.0, -145.0, -170.0, -0.5, 16.0),
    ("EXT S Union Ave Great Castle Front", 178.0, 880.0, 277.0, 1170.0, -0.5, 16.0),
    ("EXT E 4th St & Deal Time", 80.0, 755.0, 415.0, 885.0, -0.5, 16.0),
    ("EXT Great Castle South Lot", 285.0, 885.0, 412.0, 992.0, -0.5, 16.0),
    ("EXT E 5th St & Reyes Tires", 80.0, 1165.0, 415.0, 1300.0, -0.5, 16.0),
    ("INT Great Castle Vestibule", 355.0, 997.0, 375.0, 1009.0, 0.2, 12.2),
    ("INT Great Castle Dining Hall", 337.0, 1007.5, 388.5, 1066.5, 0.2, 12.2),
    ("INT Great Castle Restrooms", 389.5, 997.0, 412.5, 1013.0, 0.2, 10.8),
    ("INT Great Castle Kitchen BOH", 389.5, 1014.0, 412.5, 1066.5, 0.2, 10.8),
    ("INT Reyes Tires Service Bay", 318.0, 1236.0, 358.0, 1268.0, 0.0, 11.6),
)


def _read_wad_names(wad_path: str) -> List[str]:
    names: List[str] = []
    if not wad_path or not os.path.isfile(wad_path):
        return names
    with open(wad_path, "rb") as f:
        wd = f.read()
    if len(wd) < 12 or wd[:4] not in (b"WAD2", b"WAD3"):
        return names
    _magic, num_lumps, dir_off = struct.unpack_from("<4sii", wd, 0)
    for i in range(num_lumps):
        entry_off = dir_off + 32 * i
        if entry_off + 32 > len(wd):
            break
        nm = wd[entry_off + 16 : entry_off + 32].split(b"\x00", 1)[0].decode("latin1", errors="replace").lower()
        if nm:
            names.append(nm)
    return names


def audit_textures_strict(check_web: bool = True) -> Dict[str, object]:
    """Verify 100% custom procedural gwc_* / {gwc_* textures across .map, .bsp, .wad, textures/, web/tex/."""
    map_path = next((p for p in MAP_CANDIDATES if os.path.isfile(p)), None)
    if not map_path:
        raise FileNotFoundError(f"goldenwest.map not found in {MAP_CANDIDATES}")
    if not os.path.isfile(BSP_PATH):
        raise FileNotFoundError(f"Compiled BSP not found: {BSP_PATH}")

    # 1. .map textures
    map_tex = collections.Counter()
    with open(map_path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            s = raw.strip()
            if s.startswith("("):
                parts = s.split(")")
                if len(parts) >= 4:
                    tok = parts[3].strip().split()[0].lower()
                    map_tex[tok] += 1

    forbidden_map = {t: c for t, c in map_tex.items() if is_forbidden_tex(t)}
    non_gwc_map = {t: c for t, c in map_tex.items() if not re.match(r"^\{?gwc_", t) and t not in SPECIAL_TEXTURES}
    oversize_map = [t for t in map_tex if t not in SPECIAL_TEXTURES and len(t) > MAX_TEX_NAME_LEN]

    # 2. .bsp miptex
    with open(BSP_PATH, "rb") as f:
        d = f.read()
    lumps = [struct.unpack("<2i", d[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    l_miptex = d[lumps[2][0] : lumps[2][0] + lumps[2][1]]
    num_mip = struct.unpack_from("<i", l_miptex, 0)[0]
    bsp_miptex: List[str] = []
    for i in range(num_mip):
        off = struct.unpack_from("<i", l_miptex, 4 + 4 * i)[0]
        if off >= 0 and off + 16 <= len(l_miptex):
            name = l_miptex[off : off + 16].split(b"\x00", 1)[0].decode("latin1", errors="replace").lower()
            bsp_miptex.append(name)
    forbidden_bsp = [t for t in bsp_miptex if is_forbidden_tex(t)]
    non_gwc_bsp = [t for t in bsp_miptex if not re.match(r"^\{?gwc_", t) and t not in SPECIAL_TEXTURES]

    # 3. gw2.wad
    wad_path = next((p for p in DEFAULT_WAD_PATHS if os.path.isfile(p)), "")
    wad_names = _read_wad_names(wad_path)
    forbidden_wad = [t for t in wad_names if is_forbidden_tex(t)]
    non_gwc_wad = [t for t in wad_names if not re.match(r"^\{?gwc_", t) and t not in SPECIAL_TEXTURES]

    # 4. Disk textures/gwc_* & optional albedo cap check
    tex_dir = os.path.join(MOD_DIR, "textures")
    disk_gwc = (
        sorted(f for f in os.listdir(tex_dir) if re.match(r"^\{?gwc_", f, re.I) and f.lower().endswith(".png"))
        if os.path.isdir(tex_dir) else []
    )

    # 5. WebGL tex/ completeness & naming check
    web_pngs: List[str] = []
    web_used = set()
    non_gwc_web: List[str] = []
    missing_web_png: List[str] = []
    model_skin_pngs: List[str] = []
    allowed_model_skins = {"gw_gold.png", "gw_horse.png", "gw_pedestal.png", "gw_rock.png"}
    if check_web and os.path.isdir(WEB_DIR):
        wtex_dir = os.path.join(WEB_DIR, "tex")
        if os.path.isdir(wtex_dir):
            web_pngs = sorted(f for f in os.listdir(wtex_dir) if f.endswith(".png"))
            model_skin_pngs = [f for f in web_pngs if f.lower() in allowed_model_skins]
            non_gwc_web = [
                f for f in web_pngs
                if not re.match(r"^(?:fence_|\{)?gwc_", f, re.I) and f.lower() not in allowed_model_skins
            ]
        mj = os.path.join(WEB_DIR, "map.json")
        if os.path.isfile(mj):
            with open(mj, "r", encoding="utf-8") as f:
                wj = json.load(f)
            for g in wj.get("world", []):
                t = g["tex"]
                web_used.add(t)
                if not os.path.isfile(os.path.join(wtex_dir, t + ".png")):
                    missing_web_png.append(t + ".png")
                if g.get("glow") and not os.path.isfile(os.path.join(wtex_dir, t + "_glow.png")):
                    missing_web_png.append(t + "_glow.png")

    legacy_map = [t for t in map_tex if t.startswith(("bklan", "bk_"))]
    legacy_bsp = [t for t in bsp_miptex if t.startswith(("bklan", "bk_"))]
    legacy_wad = [t for t in wad_names if t.startswith(("bklan", "bk_"))]
    legacy_web = [f for f in web_pngs if re.match(r"^(?:fence_|\{)?(?:bklan|bk_)", f, re.I)]
    rendered_bsp = [t for t in bsp_miptex if t not in SPECIAL_TEXTURES and not t.startswith("sky")]
    gwc_bsp = [t for t in rendered_bsp if re.match(r"^\{?gwc_", t)]
    gwc_pct_bsp = round(100.0 * len(gwc_bsp) / max(1, len(rendered_bsp)), 2)

    ok = not (
        forbidden_map or non_gwc_map or oversize_map or legacy_map
        or forbidden_bsp or non_gwc_bsp or legacy_bsp
        or forbidden_wad or non_gwc_wad or legacy_wad
        or non_gwc_web or missing_web_png or legacy_web
        or not wad_names
    )
    return {
        "map_path": map_path,
        "wad_path": wad_path,
        "map_rendered_textures": len([t for t in map_tex if t not in SPECIAL_TEXTURES]),
        "map_special_textures": sorted(t for t in map_tex if t in SPECIAL_TEXTURES),
        "forbidden_in_map": forbidden_map,
        "non_gwc_in_map": non_gwc_map,
        "oversize_in_map": oversize_map,
        "bsp_miptex_count": len(bsp_miptex),
        "gwc_pct_in_bsp": gwc_pct_bsp,
        "forbidden_in_bsp": forbidden_bsp,
        "non_gwc_in_bsp": non_gwc_bsp,
        "wad_texture_count": len(wad_names),
        "forbidden_in_wad": forbidden_wad,
        "non_gwc_in_wad": non_gwc_wad,
        "disk_textures_gwc_count": len(disk_gwc),
        "web_tex_png_count": len(web_pngs),
        "web_used_materials": len(web_used),
        "web_model_skin_pngs": model_skin_pngs,
        "non_gwc_in_web_tex": non_gwc_web,
        "missing_web_png": missing_web_png,
        "legacy_bklan_bk_counts": {
            "map": len(legacy_map),
            "bsp": len(legacy_bsp),
            "wad": len(legacy_wad),
            "web_tex": len(legacy_web),
        },
        "pass": ok,
    }


def audit_lit_zones(check_web: bool = True) -> Dict[str, object]:
    """Analyze BSP + QLIT per-face RGB lightmap luma across ALL Golden West exteriors & interiors."""
    with open(BSP_PATH, "rb") as f:
        d = f.read()
    with open(LIT_PATH, "rb") as f:
        lit = f.read()
    assert lit[:4] == b"QLIT", f"Bad LIT magic: {lit[:4]!r}"
    lit_rgb = np.frombuffer(lit, dtype=np.uint8, offset=8)

    lumps = [struct.unpack("<2i", d[4 + 8 * i : 12 + 8 * i]) for i in range(15)]

    def lmp(i: int) -> bytes:
        return d[lumps[i][0] : lumps[i][0] + lumps[i][1]]

    l_mip = lmp(2)
    num_mip = struct.unpack_from("<i", l_mip, 0)[0]
    mip_names: Dict[int, str] = {}
    for i in range(num_mip):
        off = struct.unpack_from("<i", l_mip, 4 + 4 * i)[0]
        if off >= 0 and off + 16 <= len(l_mip):
            mip_names[i] = l_mip[off : off + 16].split(b"\x00", 1)[0].decode("latin1", errors="replace").lower()

    verts = np.frombuffer(lmp(3), dtype=np.float32).reshape(-1, 3)
    l_tex = lmp(6)
    tex_vecs = []
    tex_miptex = []
    for off in range(0, len(l_tex), 40):
        vals = struct.unpack_from("<8fii", l_tex, off)
        tex_vecs.append((vals[:4], vals[4:8]))
        tex_miptex.append(mip_names.get(vals[8], "?"))

    l_edges = np.frombuffer(lmp(12), dtype=np.int32).reshape(-1, 2)
    l_surf = np.frombuffer(lmp(13), dtype=np.int32)
    l_faces = lmp(7)
    n_faces = len(l_faces) // 28

    face_records = []
    unlit_non_special = 0
    for fi in range(n_faces):
        _pl, _side, firstedge, numedges, texinfo, _s0, _s1, _s2, _s3, lightofs = struct.unpack_from("<5i4Bi", l_faces, 28 * fi)
        tname = tex_miptex[texinfo]
        if tname in SPECIAL_TEXTURES or tname.startswith("sky"):
            continue
        se = l_surf[firstedge : firstedge + numedges]
        vidx = [l_edges[e, 0] if e >= 0 else l_edges[-e, 1] for e in se]
        fpts = verts[vidx]
        cx, cy, cz = (fpts.mean(axis=0) / U_FT).tolist()

        if lightofs < 0:
            unlit_non_special += 1
            continue

        sv, tv = tex_vecs[texinfo]
        s_vals = fpts[:, 0] * sv[0] + fpts[:, 1] * sv[1] + fpts[:, 2] * sv[2] + sv[3]
        t_vals = fpts[:, 0] * tv[0] + fpts[:, 1] * tv[1] + fpts[:, 2] * tv[2] + tv[3]
        nw = int(np.floor(s_vals.max() / 16.0)) - int(np.floor(s_vals.min() / 16.0)) + 1
        nh = int(np.floor(t_vals.max() / 16.0)) - int(np.floor(t_vals.min() / 16.0)) + 1
        nsamp = nw * nh
        rgb_start = lightofs * 3
        rgb_end = min(len(lit_rgb), rgb_start + nsamp * 3)
        if rgb_end <= rgb_start:
            continue
        samp = lit_rgb[rgb_start:rgb_end].reshape(-1, 3).astype(np.float32)
        luma = 0.2126 * samp[:, 0] + 0.7152 * samp[:, 1] + 0.0722 * samp[:, 2]
        face_records.append((cx, cy, cz, float(luma.mean()), float(luma.min()), float(luma.max()), tname))

    arr_xyz = np.array([(r[0], r[1], r[2]) for r in face_records], dtype=np.float32) if face_records else np.zeros((0, 3), dtype=np.float32)
    arr_mean = np.array([r[3] for r in face_records], dtype=np.float32) if face_records else np.zeros((0,), dtype=np.float32)
    arr_min = np.array([r[4] for r in face_records], dtype=np.float32) if face_records else np.zeros((0,), dtype=np.float32)
    arr_max = np.array([r[5] for r in face_records], dtype=np.float32) if face_records else np.zeros((0,), dtype=np.float32)

    zone_stats = []
    dark_zones = []
    empty_zones = []
    for zname, x1, y1, x2, y2, z1, z2 in LIGHTING_ZONES_FT:
        if len(arr_xyz) == 0:
            empty_zones.append(zname)
            zone_stats.append({"zone": zname, "faces": 0})
            continue
        mask = (
            (arr_xyz[:, 0] >= x1) & (arr_xyz[:, 0] <= x2) &
            (arr_xyz[:, 1] >= y1) & (arr_xyz[:, 1] <= y2) &
            (arr_xyz[:, 2] >= z1) & (arr_xyz[:, 2] <= z2)
        )
        cnt = int(mask.sum())
        if cnt == 0:
            empty_zones.append(zname)
            zone_stats.append({"zone": zname, "faces": 0})
            continue
        zm = arr_mean[mask]
        zmin = arr_min[mask]
        zmax = arr_max[mask]
        rec = {
            "zone": zname,
            "faces": cnt,
            "mean_luma": round(float(zm.mean()), 1),
            "p10_luma": round(float(np.percentile(zm, 10)), 1),
            "min_sample": round(float(zmin.min()), 1),
            "max_sample": round(float(zmax.max()), 1),
        }
        zone_stats.append(rec)
        if rec["mean_luma"] < 28.0:
            dark_zones.append(rec)

    web_lm_info: Dict[str, object] = {}
    lm_path = os.path.join(WEB_DIR, "lightmap.png")
    if check_web and os.path.isfile(lm_path):
        lm_img = np.array(Image.open(lm_path).convert("RGB"), dtype=np.float32)
        lm_luma = 0.2126 * lm_img[:, :, 0] + 0.7152 * lm_img[:, :, 1] + 0.0722 * lm_img[:, :, 2]
        web_lm_info = {
            "shape": list(lm_img.shape[:2]),
            "mean_luma": round(float(lm_luma.mean()), 1),
            "p95_luma": round(float(np.percentile(lm_luma, 95)), 1),
            "pct_clipped_ge252": round(float((lm_luma >= 252.0).mean() * 100.0), 2),
        }

    ext_means = [z["mean_luma"] for z in zone_stats if z["faces"] > 0 and z["zone"].startswith("EXT ")]
    int_means = [z["mean_luma"] for z in zone_stats if z["faces"] > 0 and z["zone"].startswith("INT ")]
    zone_sorted = sorted([z for z in zone_stats if z["faces"] > 0], key=lambda x: x["mean_luma"])

    return {
        "lit_faces_audited": len(face_records),
        "unlit_non_special_faces": unlit_non_special,
        "total_zones_checked": len(LIGHTING_ZONES_FT),
        "empty_zones": empty_zones,
        "dark_zones_lt28": dark_zones,
        "exterior_mean_range": [min(ext_means), max(ext_means)] if ext_means else [],
        "interior_mean_range": [min(int_means), max(int_means)] if int_means else [],
        "darkest_10_zones": zone_sorted[:10],
        "brightest_10_zones": zone_sorted[-10:],
        "web_lightmap_png": web_lm_info,
        "pass": (len(empty_zones) == 0 and len(dark_zones) == 0 and unlit_non_special == 0),
    }


CURATED_AUDIT5_IDS: Tuple[str, ...] = (
    "ext_03_union_looking_north",
    "ext_05_casino_pylon_facade",
    "ext_07_casino_ne_portico_horse",
    "ext_09_belle_terrace_carnitas",
    "ext_13_ramos_and_compas",
    "ext_14_sunland_country_playfair",
    "int_02_casino_poker_pit",
    "int_05_casino_lounge_bar",
    "int_08_carnitas_diner",
    "int_09_star_liter_interior",
    "int_13_playfair_market_interior",
    "int_15_west_house_interior",
    "ext_17_gc_aerial",
    "ext_18_gc_union_west",
    "ext_19_gc_watchtower_entry",
    "ext_20_gc_e5th_north",
    "int_16_gc_vestibule",
    "int_17_gc_dining_lanterns",
    "gc_dining_restrooms_view",
    "int_18_gc_kitchen_boh",
    "gc_deal_time_lot",
    "reyes_tires_bay",
    "ext_west_4th_shamrock",
    "ext_west_dg_market",
)


def _select_audit_views(spots: Sequence[Dict[str, object]]) -> List[Tuple[str, Tuple[float, float, float], float, float]]:
    by_id = {str(v["id"]): v for v in GW_AUDIT1_VIEWS}
    overrides: Dict[str, Tuple[Tuple[float, float, float], float, float]] = {
        "int_09_star_liter_interior": ((426.0, 68.0, 5.5), 6.0, -90.0),
        "int_15_west_house_interior": ((-182.0, -235.0, 5.5), 2.0, 180.0),
        "gc_dining_restrooms_view": ((378.0, 1005.2, 4.7), 2.0, 0.0),
        "gc_deal_time_lot": ((336.0, 792.0, 5.5), 0.0, 40.0),
        "reyes_tires_bay": ((338.0, 1252.0, 5.5), 0.0, 45.0),
        "ext_west_4th_shamrock": ((164.0, 768.0, 5.5), 0.0, 135.0),
        "ext_west_dg_market": ((146.0, 1198.0, 5.5), 0.0, 180.0),
    }
    curated: List[Tuple[str, Tuple[float, float, float], float, float]] = []
    for vid in CURATED_AUDIT5_IDS:
        if vid in overrides:
            (px, py, pz), pitch, yaw = overrides[vid]
            curated.append((vid, (px * U_FT, py * U_FT, pz * U_FT), pitch, yaw))
            continue
        v = by_id.get(vid)
        if v is None:
            continue
        px, py, pz = v["pos_ft"]
        curated.append((vid, (float(px) * U_FT, float(py) * U_FT, float(pz) * U_FT), float(v["pitch"]), float(v["yaw"])))
    if curated:
        return curated
    if spots:
        sel = spots if len(spots) <= 8 else spots[:: max(1, len(spots) // 8)][:8]
        return [(str(s["name"]), tuple(s["origin"]), float(s.get("pitch", 0.0)), float(s.get("yaw", 0.0))) for s in sel]
    return [
        ("Casino_NE_Plaza", (125.0 * U_FT, 12.0 * U_FT, 6.0 * U_FT), 2.0, 210.0),
        ("Casino_Main_Pit", (0.0, 0.0, 6.0 * U_FT), 2.0, 180.0),
        ("Casino_Rotunda", (76.0 * U_FT, -25.0 * U_FT, 6.0 * U_FT), 0.0, 180.0),
        ("Union_Belle_Signal", (202.0 * U_FT, 505.0 * U_FT, 6.0 * U_FT), 0.0, 90.0),
        ("StarLiter_Courtyard", (380.0 * U_FT, 120.0 * U_FT, 6.0 * U_FT), 2.0, 180.0),
        ("Carnitas_Diner", (124.0 * U_FT, 632.0 * U_FT, 6.0 * U_FT), 2.0, 90.0),
    ]


def audit_darkplaces_webcfg(spots: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Capture Desktop DarkPlaces views at exact WASM web.cfg calibration (v_gamma 1, v_contrast 1)."""
    if not os.path.isfile(DP_EXE) or not os.path.isfile(BSP_PATH):
        return {"ran": False, "ok": False, "reason": "darkplaces.exe or BSP not found"}

    for _ in range(10):
        if not _running_darkplaces_pids():
            break
        time.sleep(1.0)
    else:
        return {"ran": False, "ok": False, "reason": f"Existing darkplaces.exe active: {_running_darkplaces_pids()}"}

    scr_dir = os.path.join(MOD_DIR, "screenshots")
    os.makedirs(scr_dir, exist_ok=True)
    before = set(os.listdir(scr_dir))
    tmp_cfgs: List[str] = []

    cfg_path = os.path.join(MOD_DIR, "config.cfg")
    cfg_backup = open(cfg_path, "rb").read() if os.path.isfile(cfg_path) else None

    dp_views = _select_audit_views(spots)
    for idx, (label, (px, py, pz), pitch, yaw) in enumerate(dp_views):
        scfg_name = f"_gw_audit5_dp_{idx}.cfg"
        scfg = os.path.join(MOD_DIR, scfg_name)
        tmp_cfgs.append(scfg)
        next_cmd = f'defer 0.25 "exec _gw_audit5_dp_{idx + 1}.cfg"' if idx + 1 < len(dp_views) else 'defer 0.25 "quit"'
        step_lines = []
        if idx == 0:
            step_lines += [
                "sv_cheats 1", "freelook 0", "-mlook", "cl_anglespeedkey 0",
                "v_hwgamma 0", "r_hdr_scenebrightness 1", "v_gamma 1", "v_contrast 1", "v_brightness 0", "v_glslgamma 0",
                "r_glsl_saturation 1", "r_bloom 0", "gl_polyblend 0",
                "r_glsl_offsetmapping 0", "r_glsl_offsetmapping_reliefmapping 0",
                "r_water 0", "r_shadow_realtime_dlight_shadows 0", "r_shadow_shadowmapping 0",
                "cl_stainmaps 0",
                "crosshair 0", "r_drawviewmodel 0", "cl_viewmodel_scale 0", "showfps 0", "viewsize 120",
                "scr_screenshot_png 1",
                "prvm_edictset server 1 movetype 8",
                "prvm_edictset server 1 solid 0",
                'prvm_edictset server 1 weaponmodel ""',
            ]
        safe_lbl = re.sub(r"[^A-Za-z0-9_]", "_", label)[:28]
        step_lines += [
            f'prvm_edictset server 1 origin "{px:.1f} {py:.1f} {pz - 22.0:.1f}"',
            f'prvm_edictset server 1 angles "{pitch:.1f} {yaw:.1f} 0"',
            f'prvm_edictset server 1 v_angle "{pitch:.1f} {yaw:.1f} 0"',
            "prvm_edictset server 1 fixangle 1",
            'prvm_edictset server 1 velocity "0 0 0"',
            f"scr_screenshot_name gw_a5_{idx:02d}_{safe_lbl}_",
            'defer 0.15 "screenshot"',
            next_cmd,
        ]
        with open(scfg, "w", encoding="ascii") as f:
            f.write("\n".join(step_lines) + "\n")

    proc = None
    try:
        proc = subprocess.Popen(
            [
                DP_EXE,
                "-window", "-width", "1280", "-height", "720",
                "-game", "quake15", "-game", "BakersfieldQuake",
                "-nosound", "-nohome",
                "+vid_mouse", "0", "+joy_enable", "0",
                "+map", "goldenwest",
                "+defer", "3", "exec _gw_audit5_dp_0.cfg",
            ],
            cwd=GAME_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            proc.wait(timeout=75)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            return {"ran": True, "ok": False, "reason": "DarkPlaces webcfg screenshot run timed out"}

        after = set(os.listdir(scr_dir))
        new_files = sorted(f for f in (after - before) if f.lower().endswith((".png", ".tga")))
        stats = []
        tiles = []
        for fn in new_files:
            fp = os.path.join(scr_dir, fn)
            im = Image.open(fp).convert("RGB")
            arr = np.array(im, dtype=np.float32)
            luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
            stats.append({
                "file": fn,
                "mean_luma": round(float(luma.mean()), 1),
                "p10_luma": round(float(np.percentile(luma, 10)), 1),
                "p95_luma": round(float(np.percentile(luma, 95)), 1),
                "pct_dark_lt12": round(float((luma < 12.0).mean() * 100.0), 1),
                "pct_clipped_ge253": round(float((luma >= 253.0).mean() * 100.0), 1),
            })
            tiles.append((fn, im.resize((640, 360), Image.Resampling.LANCZOS)))

        if tiles:
            cols = 2
            rows = (len(tiles) + 1) // 2
            sheet = Image.new("RGB", (cols * 640, rows * 384), (20, 22, 26))
            draw = ImageDraw.Draw(sheet)
            for idx, (fn, tile) in enumerate(tiles):
                r, c = divmod(idx, cols)
                x0, y0 = c * 640, r * 384
                sheet.paste(tile, (x0, y0 + 24))
                draw.text((x0 + 8, y0 + 5), f"DP web.cfg (hdr=1, gamma=1): {fn}", fill=(240, 210, 120))
            sheet.save(os.path.join(OUT_DIR, "audit5_dp_webcfg_sheet.png"))

        for fn in new_files:
            try:
                os.remove(os.path.join(scr_dir, fn))
            except OSError:
                pass
        return {
            "ran": True,
            "ok": (proc.returncode == 0 and len(stats) == len(dp_views)),
            "returncode": proc.returncode,
            "expected": len(dp_views),
            "captured": len(stats),
            "views": stats,
        }
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
        for p in tmp_cfgs:
            if os.path.isfile(p):
                os.remove(p)
        if cfg_backup is not None:
            with open(cfg_path, "wb") as f:
                f.write(cfg_backup)
        elif os.path.isfile(cfg_path):
            try:
                os.remove(cfg_path)
            except OSError:
                pass


def audit_webgl_interiors(spots: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Capture interior and exterior lighting screenshots in WebGL viewer and check luma."""
    if not os.path.isdir(WEB_DIR) or not os.path.isfile(os.path.join(WEB_DIR, "index.html")):
        return {"ran": False, "pass": False, "reason": f"WEB_DIR missing: {WEB_DIR}"}

    from playwright.sync_api import sync_playwright

    handler = functools.partial(QuietHandler, directory=WEB_DIR)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    views = _select_audit_views(spots)
    console_errors, page_errors, bad_responses = [], [], []
    stats = []
    tiles = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"],
            )
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on("response", lambda r: bad_responses.append(f"{r.status} {r.url}") if r.status >= 400 else None)

            page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
            page.wait_for_function("!document.getElementById('start').disabled", timeout=25000)
            page.evaluate("document.getElementById('intro').style.display = 'none'")
            page.wait_for_timeout(300)

            for name, (px, py, pz), pitch_deg, yaw_deg in views:
                page.evaluate(
                    """([x,y,z,yaw,pitch]) => {
                        __viewer.setFly(true);
                        __viewer.teleport({pos: [x, y, z], yaw: yaw, pitch: pitch});
                    }""",
                    [px, py, pz, yaw_deg, pitch_deg],
                )
                page.wait_for_timeout(350)
                shot_path = os.path.join(OUT_DIR, f"_tmp_gw_a5_{re.sub(r'[^A-Za-z0-9_]', '_', name)}.png")
                page.screenshot(path=shot_path)
                im = Image.open(shot_path).convert("RGB")
                arr = np.array(im, dtype=np.float32)
                luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
                stats.append({
                    "view": name,
                    "mean_luma": round(float(luma.mean()), 1),
                    "p10_luma": round(float(np.percentile(luma, 10)), 1),
                    "p95_luma": round(float(np.percentile(luma, 95)), 1),
                    "pct_dark_lt12": round(float((luma < 12.0).mean() * 100.0), 1),
                    "pct_clipped_ge253": round(float((luma >= 253.0).mean() * 100.0), 1),
                })
                tiles.append((name, im.resize((640, 360), Image.Resampling.LANCZOS)))
                os.remove(shot_path)

            browser.close()
    finally:
        httpd.shutdown()

    if tiles:
        cols = 2
        rows = (len(tiles) + 1) // 2
        sheet = Image.new("RGB", (cols * 640, rows * 384), (20, 22, 26))
        draw = ImageDraw.Draw(sheet)
        for idx, (nm, tile) in enumerate(tiles):
            r, c = divmod(idx, cols)
            x0, y0 = c * 640, r * 384
            sheet.paste(tile, (x0, y0 + 24))
            draw.text((x0 + 8, y0 + 5), f"WebGL (bright=1.00): {nm}", fill=(160, 220, 255))
        sheet.save(os.path.join(OUT_DIR, "audit5_webgl_interiors.png"))

    return {
        "ran": True,
        "views": stats,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "bad_responses": bad_responses,
        "pass": not (console_errors or page_errors or bad_responses),
    }


def audit_scale_and_signage() -> Dict[str, object]:
    """Verify U_FT=12 scale contract, Hull-1 clearances, and signage textures placed in BSP."""
    if MM_TOOLS_DIR not in sys.path:
        sys.path.insert(0, MM_TOOLS_DIR)
    builder_stats: Dict[str, object] = {}
    for mod_name in ("make_gw", "goldenwest.make_gw", "make_goldenwest"):
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        mb = MapBuilder(wad_paths=(), strict_vis=True, check_textures=False)
        fn = next((getattr(mod, k) for k in ("build_goldenwest", "build_all", "build_map") if callable(getattr(mod, k, None))), None)
        if fn is not None:
            fn(mb)
            raw_stats = mb.stats()
            builder_stats = {
                k: v for k, v in raw_stats.items()
                if isinstance(v, (int, float, str, bool))
            }
            break

    signage_textures: List[str] = []
    if os.path.isfile(BSP_PATH):
        with open(BSP_PATH, "rb") as f:
            d = f.read()
        lumps = [struct.unpack("<2i", d[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
        l_mip = d[lumps[2][0] : lumps[2][0] + lumps[2][1]]
        num_mip = struct.unpack_from("<i", l_mip, 0)[0]
        for i in range(num_mip):
            off = struct.unpack_from("<i", l_mip, 4 + 4 * i)[0]
            if off >= 0 and off + 16 <= len(l_mip):
                nm = l_mip[off : off + 16].split(b"\x00", 1)[0].decode("latin1", errors="replace").lower()
                if any(k in nm for k in (
                    "sign", "gw", "union", "belle", "super8", "starl", "carn", "ramos", "playf", "marq",
                    "gc", "deal", "reyes", "shamrock", "dgmrkt", "e4st", "e5st",
                )):
                    signage_textures.append(nm)

    return {
        "u_per_ft": U_FT,
        "casino_bounds_ft": CASINO_BOUNDS_FT,
        "builder_stats": builder_stats,
        "signage_textures_in_bsp": sorted(set(signage_textures)),
        "pass": U_FT == 12.0 and len(signage_textures) > 0,
    }


def audit_standalone_and_wasm_pack(check_web: bool = True) -> Dict[str, object]:
    """Verify standalone DarkPlaces, WebGL bundle, models, skybox, and WASM pack readiness."""
    sky_files = [f"gwsky_{s}.png" for s in ("bk", "dn", "ft", "lf", "rt", "up")]
    missing_sky = [f for f in sky_files if not os.path.isfile(os.path.join(MOD_DIR, "gfx", "env", f))]
    duplicate_sky_tga = [
        fn for fn in (f"gwsky_{s}.tga" for s in ("bk", "dn", "ft", "lf", "rt", "up"))
        if os.path.isfile(os.path.join(MOD_DIR, "gfx", "env", fn))
    ]

    req_web = [
        "index.html", "map.json", "map.bin", "lightmap.png",
        "dev_overlay.js", "lib/three.module.min.js",
        "sky/bk.jpg", "sky/dn.jpg", "sky/ft.jpg", "sky/lf.jpg", "sky/rt.jpg", "sky/up.jpg",
    ]
    missing_web = [f for f in req_web if not os.path.isfile(os.path.join(WEB_DIR, f))] if check_web else []

    progs_dir = os.path.join(MOD_DIR, "progs")
    missing_models = [m for m in ("gw_horse.md3", "gw_buddha.md3") if not os.path.isfile(os.path.join(progs_dir, m))]

    server_cfg_path = os.path.join(MOD_DIR, "server.cfg")
    server_cfg_txt = open(server_cfg_path, encoding="latin1").read() if os.path.isfile(server_cfg_path) else ""
    in_server_maplist = "goldenwest" in server_cfg_txt.lower()

    has_id1 = os.path.isdir(os.path.join(GAME_ROOT, "id1"))
    has_quake15 = os.path.isdir(os.path.join(GAME_ROOT, "quake15"))

    ok = (
        os.path.isfile(BSP_PATH)
        and os.path.isfile(LIT_PATH)
        and not missing_sky
        and not duplicate_sky_tga
        and not missing_models
        and (not check_web or not missing_web)
    )
    return {
        "bsp_exists": os.path.isfile(BSP_PATH),
        "lit_exists": os.path.isfile(LIT_PATH),
        "missing_sky_files": missing_sky,
        "duplicate_sky_tga": duplicate_sky_tga,
        "missing_models": missing_models,
        "missing_web_files": missing_web,
        "make_web_pack_exists": os.path.isfile(os.path.join(MOD_DIR, "web", "make_web_pack.py")),
        "web_cfg_exists": os.path.isfile(os.path.join(MOD_DIR, "web", "site", "web.cfg")),
        "bakoweb_exists": os.path.isfile(os.path.join(MOD_DIR, "web", "bakoweb.py")),
        "goldenwest_in_server_cfg_maplist": in_server_maplist,
        "wasm_pack_base_dirs_present": {"id1": has_id1, "quake15": has_quake15},
        "pass": ok,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit 5: Golden West Lighting, Materials & Signage Compliance")
    parser.add_argument("--skip-darkplaces", action="store_true", help="Skip live DarkPlaces web.cfg screenshot pass")
    parser.add_argument("--skip-web", action="store_true", help="Skip WebGL interior screenshot checks")
    args = parser.parse_args(argv)

    os.makedirs(OUT_DIR, exist_ok=True)
    spots_path = next((p for p in SPOTS_CANDIDATES if os.path.isfile(p)), None)
    spots = load_spots(spots_path) if spots_path else []

    check_web = not args.skip_web
    dp_res = {"ran": False, "skipped": True} if args.skip_darkplaces else audit_darkplaces_webcfg(spots)
    wg_res = {"ran": False, "pass": True, "skipped": True} if args.skip_web else audit_webgl_interiors(spots)
    parity = []
    if dp_res.get("ran") and wg_res.get("ran"):
        for d_v, w_v in zip(dp_res.get("views", []), wg_res.get("views", [])):
            parity.append({
                "view": w_v["view"],
                "dp_mean": d_v["mean_luma"],
                "wg_mean": w_v["mean_luma"],
                "delta_dp_minus_wg": round(d_v["mean_luma"] - w_v["mean_luma"], 1),
                "dp_p95": d_v["p95_luma"],
                "wg_p95": w_v["p95_luma"],
                "dp_clip_pct": d_v["pct_clipped_ge253"],
                "wg_clip_pct": w_v["pct_clipped_ge253"],
                "dp_dark_pct": d_v["pct_dark_lt12"],
                "wg_dark_pct": w_v["pct_dark_lt12"],
            })

    report = {
        "textures": audit_textures_strict(check_web=check_web),
        "lighting_lit": audit_lit_zones(check_web=check_web),
        "darkplaces_webcfg": dp_res,
        "webgl_interiors": wg_res,
        "dp_vs_webgl_parity": parity,
        "scale_and_signage": audit_scale_and_signage(),
        "standalone_and_wasm": audit_standalone_and_wasm_pack(check_web=check_web),
    }
    report["overall_pass"] = (
        report["textures"]["pass"]
        and report["lighting_lit"]["pass"]
        and report["webgl_interiors"]["pass"]
        and report["scale_and_signage"]["pass"]
        and report["standalone_and_wasm"]["pass"]
        and (args.skip_darkplaces or report["darkplaces_webcfg"].get("ok", False))
    )
    out_json = os.path.join(OUT_DIR, "audit5_report.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if not report["overall_pass"]:
        print("Audit 5 failed one or more checks!")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
