"""audit4_perf.py — Audit 4 of 5: Browser-First Performance, PVS, DarkPlaces `timerefresh`,
Playwright WebGL FPS/Bundle Profiling, and WASM DarkPlaces Pack Budget Check
for Golden West Casino & S Union Ave.

Outputs:
  - source/mm_tools/goldenwest/out/audit4_perf_report.json
"""
from __future__ import annotations

import argparse
import collections
import functools
import http.server
import json
import math
import os
import re
import socketserver
import struct
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR = os.path.dirname(HERE)
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GAME_ROOT = os.path.dirname(MOD_DIR)

if MM_TOOLS_DIR not in sys.path:
    sys.path.insert(0, MM_TOOLS_DIR)
if HERE not in sys.path:
    sys.path.append(HERE)

from goldenwest import gw_lib as _gw_lib  # noqa: E402

sys.modules["gw_lib"] = _gw_lib
sys.modules["goldenwest.gw_lib"] = _gw_lib

MapBuilder = _gw_lib.MapBuilder
U_FT = _gw_lib.U_FT
from goldenwest.audit3_nav import (  # noqa: E402
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


def default_map_path() -> Optional[str]:
    return next((p for p in MAP_CANDIDATES if os.path.isfile(p)), None)


def decompress_vis(visdata: bytes, offset: int, num_clusters_bytes: int) -> bytes:
    out = bytearray()
    i = offset
    n = len(visdata)
    while len(out) < num_clusters_bytes and i < n:
        b = visdata[i]
        i += 1
        if b != 0:
            out.append(b)
        else:
            cnt = visdata[i] if i < n else 1
            i += 1
            out.extend(b"\x00" * cnt)
    return bytes(out[:num_clusters_bytes])


LUMP_NAMES = (
    "entities", "planes", "textures", "vertices", "visdata",
    "nodes", "texinfo", "faces", "lighting", "clipnodes",
    "leafs", "marksurfaces", "edges", "surfedges", "models",
)


def _extract_plane_tex(plane_line: str) -> str:
    parts = plane_line.split(")")
    if len(parts) >= 4:
        toks = parts[3].strip().split()
        if toks:
            return toks[0]
    return ""


def analyze_modules() -> Dict[str, object]:
    """Build each goldenwest module sequentially into MapBuilder to inspect per-module brush/face budgets."""
    from goldenwest import make_gw

    existing_wads = [p for p in _gw_lib.DEFAULT_WAD_PATHS if os.path.isfile(p)]
    mb = MapBuilder(
        wad_paths=existing_wads if existing_wads else _gw_lib.DEFAULT_WAD_PATHS,
        u_per_ft=U_FT,
        strict_vis=True,
        check_textures=False,
        require_gwc_prefix=False,
    )
    stages = list(make_gw._import_stage_builders()) + [("spawns_pickups_lights", make_gw.place_spawns_and_pickups)]
    prev_counts = {g: 0 for g in mb._brushes}
    prev_ents = 0
    modules = []

    for mod_name, fn in stages:
        fn(mb)
        counts_by_grp: Dict[str, int] = {}
        active_faces = 0
        skip_faces = 0
        clip_faces = 0
        thin_world = 0
        tex_counter: collections.Counter[str] = collections.Counter()
        for grp in ("world", "clip", "detail", "illus", "fence"):
            cur = mb._brushes[grp]
            added = cur[prev_counts[grp]:]
            prev_counts[grp] = len(cur)
            counts_by_grp[grp] = len(added)
            for bbox_u, planes in added:
                if grp == "world":
                    dims = sorted((bbox_u[3] - bbox_u[0], bbox_u[4] - bbox_u[1], bbox_u[5] - bbox_u[2]))
                    if dims[0] < 6.0 or dims[1] < 24.0:
                        thin_world += 1
                for pl in planes:
                    t = _extract_plane_tex(pl)
                    low = t.lower()
                    if low == "skip":
                        skip_faces += 1
                    elif low == "clip":
                        clip_faces += 1
                    else:
                        active_faces += 1
                        if t:
                            tex_counter[t] += 1
        ents_added = mb._entities[prev_ents:]
        prev_ents = len(mb._entities)
        modules.append({
            "module": mod_name,
            "world_brushes": counts_by_grp["world"],
            "clip_brushes": counts_by_grp["clip"],
            "detail_brushes": counts_by_grp["detail"],
            "illus_brushes": counts_by_grp["illus"],
            "fence_brushes": counts_by_grp["fence"],
            "total_brushes": sum(counts_by_grp.values()),
            "thin_world_brushes": thin_world,
            "active_faces": active_faces,
            "skip_faces": skip_faces,
            "clip_faces": clip_faces,
            "point_entities": len(ents_added),
            "top_5_textures": [{"tex": t, "faces": c} for t, c in tex_counter.most_common(5)],
        })

    spatial_chunks = {
        "detail_entities": len(mb._spatial_chunks(mb._brushes["detail"])),
        "illus_entities": len(mb._spatial_chunks(mb._brushes["illus"])),
        "fence_entities": len(mb._spatial_chunks(mb._brushes["fence"], cell_u=mb.fence_chunk_size_u)),
    }
    return {"modules": modules, "spatial_chunks": spatial_chunks}


def analyze_web_bundle() -> Dict[str, object]:
    """Break down source/mm_tools/out/web/goldenwest/ file sizes by category."""
    if not os.path.isdir(WEB_DIR):
        return {"exists": False}
    cats: collections.Counter[str] = collections.Counter()
    counts: collections.Counter[str] = collections.Counter()
    largest: List[Tuple[str, float]] = []
    for root, _dirs, files in os.walk(WEB_DIR):
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, WEB_DIR).replace("\\", "/")
            sz = os.path.getsize(p)
            if rel.startswith("tex/"):
                cat = "tex"
            elif rel.startswith("sky/"):
                cat = "sky"
            elif rel.startswith("progs/"):
                cat = "progs"
            elif rel.endswith(".bin"):
                cat = "hull1_bin" if "hull" in rel.lower() else "geom_bin"
            elif rel.endswith(".json"):
                cat = "json"
            else:
                cat = "html_js_other"
            cats[cat] += sz
            counts[cat] += 1
            largest.append((rel, round(sz / 1024.0, 1)))
    largest.sort(key=lambda x: -x[1])
    lm_atlas: Dict[str, object] = {}
    lm_path = os.path.join(WEB_DIR, "lightmap.png")
    if os.path.isfile(lm_path):
        try:
            from PIL import Image
            with Image.open(lm_path) as im:
                rgb = im.convert("RGB")
                aw, ah = rgb.size
                px = rgb.load()
                bg = (255, 255, 255)
                last_y = -1
                for yy in range(ah - 1, -1, -1):
                    if any(px[xx, yy] != bg for xx in range(aw)):
                        last_y = yy
                        break
                used_h = last_y + 1
                lm_atlas = {
                    "width_px": aw,
                    "height_px": ah,
                    "used_h_px": used_h,
                    "headroom_px": ah - used_h,
                    "headroom_pct": round(100.0 * (ah - used_h) / max(1, ah), 2),
                }
        except Exception as exc:
            lm_atlas = {"error": str(exc)}
    return {
        "exists": True,
        "total_disk_mb": round(sum(cats.values()) / (1024.0 * 1024.0), 2),
        "by_category_kb": {k: round(v / 1024.0, 1) for k, v in sorted(cats.items())},
        "file_counts": dict(counts),
        "lightmap_atlas": lm_atlas,
        "top_10_largest_files": [{"file": f, "kb": kb} for f, kb in largest[:10]],
    }


def analyze_bsp_and_map() -> Dict[str, object]:
    """Inspect BSP2 geometry/VIS/clipnode budgets and .map entity/face totals."""
    if not os.path.isfile(BSP_PATH):
        raise FileNotFoundError(f"BSP not found: {BSP_PATH}")
    with open(BSP_PATH, "rb") as f:
        d = f.read()
    assert d[:4] == b"BSP2", f"Expected BSP2 format, got {d[:4]!r}"
    lumps = [struct.unpack("<2i", d[4 + 8 * i : 12 + 8 * i]) for i in range(15)]
    lump_kb = {LUMP_NAMES[i]: round(lumps[i][1] / 1024.0, 1) for i in range(15)}

    def lmp(i: int) -> bytes:
        o, sz = lumps[i]
        return d[o : o + sz]

    entities_raw = lmp(0).decode("latin1")
    planes = [struct.unpack("<4fi", lmp(1)[i : i + 20]) for i in range(0, len(lmp(1)), 20)]
    verts = [struct.unpack("<3f", lmp(3)[i : i + 12]) for i in range(0, len(lmp(3)), 12)]
    lump_vis = lmp(4)
    texinfos = [struct.unpack("<8f2i", lmp(6)[i : i + 40]) for i in range(0, len(lmp(6)), 40)]
    faces = [struct.unpack("<5i4Bi", lmp(7)[i : i + 28]) for i in range(0, len(lmp(7)), 28)]
    clipnodes = [struct.unpack("<iii", lmp(9)[i : i + 12]) for i in range(0, len(lmp(9)), 12)]
    leafs = [struct.unpack("<2i6f2I4B", lmp(10)[i : i + 44]) for i in range(0, len(lmp(10)), 44)]
    marksurfaces = [struct.unpack("<I", lmp(11)[i : i + 4])[0] for i in range(0, len(lmp(11)), 4)]
    models = [struct.unpack("<9f7i", lmp(14)[i : i + 64]) for i in range(0, len(lmp(14)), 64)]

    tl = lmp(2)
    num_tex = struct.unpack("<i", tl[:4])[0]
    miptex: List[str] = []
    for i in range(num_tex):
        ofs = struct.unpack("<i", tl[4 + 4 * i : 8 + 4 * i])[0]
        if ofs < 0 or ofs + 16 > len(tl):
            miptex.append("")
        else:
            nm = struct.unpack("<16s", tl[ofs : ofs + 16])[0].split(b"\0")[0].decode("latin1")
            miptex.append(nm)

    ents = [dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', m.group(1))) for m in re.finditer(r"\{([^}]*)\}", entities_raw)]
    ent_classes = collections.Counter(e.get("classname", "?") for e in ents)
    bmodel_info = {}
    for e in ents:
        if e.get("model", "").startswith("*"):
            mi = int(e["model"][1:])
            bmodel_info[mi] = e.get("classname", "?")

    # Exact PVS across player-accessible leafs (z in -2 .. 18 ft)
    world_visleafs = models[0][13]
    vis_clusters = len({lf[1] for lf in leafs[1 : min(len(leafs), world_visleafs + 1)] if lf[1] >= 0})
    world_faces_end = models[0][14] + models[0][15]
    row_bytes = (world_visleafs + 7) >> 3

    leaf_bmodels: List[List[int]] = [[] for _ in range(len(leafs))]
    for t_li in range(1, min(len(leafs), world_visleafs + 1)):
        lx0, ly0, lz0, lx1, ly1, lz1 = leafs[t_li][2:8]
        bm = []
        for mi in range(1, len(models)):
            mx0, my0, mz0, mx1, my1, mz1 = models[mi][0:6]
            if lx0 <= mx1 and lx1 >= mx0 and ly0 <= my1 and ly1 >= my0 and lz0 <= mz1 and lz1 >= mz0:
                bm.append(mi)
        leaf_bmodels[t_li] = bm

    vis_leaf_counts: List[int] = []
    pvs_face_counts: List[int] = []
    pvs_samples: List[Dict[str, object]] = []
    max_pvs_faces = 0
    max_pvs_pos_ft = [0.0, 0.0, 0.0]
    worst_vis_faces: set[int] = set()
    worst_vis_bmodels: set[int] = set()

    for li in range(1, min(len(leafs), world_visleafs + 1), 4):
        contents, visofs, x0, y0, z0, x1, y1, z1, fms, nms, *_ = leafs[li]
        if contents == -2 or visofs < 0:
            continue
        cz_ft = 0.5 * (z0 + z1) / U_FT
        if cz_ft < -2.0 or cz_ft > 18.0:
            continue
        row = decompress_vis(lump_vis, visofs, row_bytes)
        vis_leaf_cnt = 0
        vis_faces = set()
        vis_bmodels = set()
        for byte_idx, bval in enumerate(row):
            if bval == 0:
                continue
            base_leaf = byte_idx * 8 + 1
            for bit in range(8):
                if bval & (1 << bit):
                    t_li = base_leaf + bit
                    if t_li <= world_visleafs and t_li < len(leafs):
                        vis_leaf_cnt += 1
                        tfms, tnms = leafs[t_li][8], leafs[t_li][9]
                        if tnms:
                            vis_faces.update(marksurfaces[tfms : tfms + tnms])
                        if leaf_bmodels[t_li]:
                            vis_bmodels.update(leaf_bmodels[t_li])
        ent_fc = sum(models[mi][15] for mi in vis_bmodels)
        fc_count = len(vis_faces) + ent_fc
        pos_ft = [round(0.5 * (x0 + x1) / U_FT, 1), round(0.5 * (y0 + y1) / U_FT, 1), round(cz_ft, 1)]
        vis_leaf_counts.append(vis_leaf_cnt)
        pvs_face_counts.append(fc_count)
        pvs_samples.append({
            "pos_ft": pos_ft,
            "vis_leafs": vis_leaf_cnt,
            "total_faces": fc_count,
            "world_faces": len(vis_faces),
            "bmodel_faces": ent_fc,
            "bmodels": len(vis_bmodels),
        })
        if fc_count > max_pvs_faces:
            max_pvs_faces = fc_count
            max_pvs_pos_ft = pos_ft
            worst_vis_faces = vis_faces
            worst_vis_bmodels = vis_bmodels

    pvs_samples.sort(key=lambda s: -int(s["total_faces"]))  # type: ignore[arg-type]
    top_5_pvs_hotspots: List[Dict[str, object]] = []
    for sp in pvs_samples:
        px, py, _ = sp["pos_ft"]  # type: ignore[misc]
        if all(((px - ox) ** 2 + (py - oy) ** 2) ** 0.5 >= 60.0 for ox, oy, _ in (h["pos_ft"] for h in top_5_pvs_hotspots)):  # type: ignore[misc]
            top_5_pvs_hotspots.append(sp)
            if len(top_5_pvs_hotspots) >= 5:
                break

    worst_pvs_tex = collections.Counter()
    for fi in worst_vis_faces:
        mi_idx = texinfos[faces[fi][4]][8]
        tn = miptex[mi_idx] if 0 <= mi_idx < len(miptex) else "?"
        worst_pvs_tex[tn] += 1
    for bmi in worst_vis_bmodels:
        ff, nf = models[bmi][14], models[bmi][15]
        for fi in range(ff, ff + nf):
            mi_idx = texinfos[faces[fi][4]][8]
            tn = miptex[mi_idx] if 0 <= mi_idx < len(miptex) else "?"
            worst_pvs_tex[tn] += 1

    tex_faces = collections.Counter()
    tex_world_faces = collections.Counter()
    tex_bmodel_faces = collections.Counter()
    tex_tris = collections.Counter()
    for fidx, fc in enumerate(faces):
        ti = fc[4]
        mi_idx = texinfos[ti][8]
        tn = miptex[mi_idx] if 0 <= mi_idx < len(miptex) else "?"
        tex_faces[tn] += 1
        if fidx < world_faces_end:
            tex_world_faces[tn] += 1
        else:
            tex_bmodel_faces[tn] += 1
        tex_tris[tn] += max(0, fc[3] - 2)

    submodels = []
    for mi in range(1, len(models)):
        m = models[mi]
        submodels.append({
            "model": f"*{mi}",
            "classname": bmodel_info.get(mi, "?"),
            "faces": m[15],
            "span_xy_ft": [round((m[3] - m[0]) / U_FT, 1), round((m[4] - m[1]) / U_FT, 1)],
        })
    submodels.sort(key=lambda x: -x["faces"])

    ent_brushes = collections.Counter()
    ent_active_faces = collections.Counter()
    ent_skip_faces = collections.Counter()
    map_path = default_map_path()
    if map_path:
        cur_class: Optional[str] = None
        in_brush = False
        brush_tex: List[str] = []
        with open(map_path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                s = raw.strip()
                if s == "{":
                    if cur_class is None:
                        cur_class = "unknown"
                    elif not in_brush:
                        in_brush = True
                        brush_tex = []
                elif s == "}":
                    if in_brush:
                        ent_brushes[cur_class] += 1
                        ent_active_faces[cur_class] += sum(1 for t in brush_tex if t.lower() != "skip")
                        ent_skip_faces[cur_class] += sum(1 for t in brush_tex if t.lower() == "skip")
                        in_brush = False
                    else:
                        cur_class = None
                elif not in_brush and s.startswith('"classname"'):
                    m = re.findall(r'"([^"]*)"', s)
                    if len(m) >= 2:
                        cur_class = m[1]
                elif in_brush and s.startswith("("):
                    parts = s.split(")")
                    if len(parts) >= 4:
                        ent_active_faces_tok = parts[3].strip().split()[0]
                        brush_tex.append(ent_active_faces_tok)

    return {
        "bsp_kb": round(os.path.getsize(BSP_PATH) / 1024.0, 1),
        "lit_kb": round(os.path.getsize(LIT_PATH) / 1024.0, 1) if os.path.isfile(LIT_PATH) else 0.0,
        "lump_kb": lump_kb,
        "visdata_kb": round(len(lump_vis) / 1024.0, 1),
        "planes": len(planes),
        "vertices": len(verts),
        "faces": len(faces),
        "world_faces": models[0][15],
        "bmodel_faces": len(faces) - models[0][15],
        "triangles": sum(max(0, fc[3] - 2) for fc in faces),
        "clipnodes": len(clipnodes),
        "leafs": len(leafs),
        "world_visleafs": world_visleafs,
        "vis_clusters": vis_clusters,
        "total_models": len(models),
        "bsp_entities_total": len(ents),
        "bsp_entity_classes": dict(ent_classes.most_common()),
        "avg_pvs_visleafs": int(round(sum(vis_leaf_counts) / max(1, len(vis_leaf_counts)))),
        "max_pvs_visleafs": max(vis_leaf_counts) if vis_leaf_counts else 0,
        "avg_pvs_faces": int(round(sum(pvs_face_counts) / max(1, len(pvs_face_counts)))),
        "p95_pvs_faces": sorted(pvs_face_counts)[int(0.95 * len(pvs_face_counts))] if pvs_face_counts else 0,
        "max_pvs_faces": max_pvs_faces,
        "max_pvs_hotspot_ft": max_pvs_pos_ft,
        "top_5_pvs_hotspots": top_5_pvs_hotspots,
        "worst_pvs_top_12_textures": [{"tex": t, "faces": c} for t, c in worst_pvs_tex.most_common(12)],
        "map_path": map_path,
        "map_brushes_by_class": dict(ent_brushes),
        "map_active_faces_by_class": dict(ent_active_faces),
        "map_skip_faces_by_class": dict(ent_skip_faces),
        "top_20_textures_by_tris": [
            {
                "tex": t,
                "tris": c,
                "bsp_faces": tex_faces[t],
                "world_faces": tex_world_faces[t],
                "bmodel_faces": tex_bmodel_faces[t],
            }
            for t, c in tex_tris.most_common(20)
        ],
        "top_10_submodels": submodels[:10],
    }


def _select_bench_spots(
    spots: Sequence[Dict[str, object]],
    hotspot_ft: Optional[Sequence[float]] = None,
) -> List[Dict[str, object]]:
    sel: List[Dict[str, object]]
    if spots:
        if len(spots) <= 8:
            sel = list(spots)
        else:
            step = max(1, len(spots) // 8)
            sel = list(spots)[::step][:8]
        # Ensure Great Castle / northern expansion spot is always benchmarked
        has_north = any(
            isinstance(s.get("origin"), (list, tuple)) and len(s["origin"]) >= 2 and float(s["origin"][1]) >= 750.0 * U_FT  # type: ignore[index]
            for s in sel
        )
        if not has_north:
            seen_names = {str(s.get("name", "")) for s in sel}
            gc_cand = next(
                (
                    s for s in spots
                    if str(s.get("name", "")) not in seen_names
                    and ("great" in str(s.get("desc", "")).lower() or str(s.get("name", "")).startswith("gc_"))
                ),
                None,
            )
            if gc_cand is None:
                gc_cand = max(
                    spots,
                    key=lambda s: float(s["origin"][1]) if isinstance(s.get("origin"), (list, tuple)) and len(s["origin"]) >= 2 else -1e9,  # type: ignore[index]
                )
            if gc_cand is not None and str(gc_cand.get("name", "")) not in seen_names:
                sel.append(gc_cand)
    else:
        sel = [
            {"name": "Casino_NE_Plaza", "origin": [120.0 * U_FT, 10.0 * U_FT, 6.0 * U_FT], "pitch": 0.0, "yaw": 210.0},
            {"name": "Casino_Main_Pit", "origin": [0.0, 0.0, 6.0 * U_FT], "pitch": 0.0, "yaw": 180.0},
            {"name": "Union_Belle_Intersection", "origin": [228.0 * U_FT, 520.0 * U_FT, 8.0 * U_FT], "pitch": 5.0, "yaw": 90.0},
            {"name": "Union_South_Super8", "origin": [202.0 * U_FT, -620.0 * U_FT, 8.0 * U_FT], "pitch": 4.0, "yaw": 180.0},
            {"name": "Great_Castle_South_Lot", "origin": [344.0 * U_FT, 932.0 * U_FT, 6.0 * U_FT], "pitch": 0.0, "yaw": 90.0},
            {"name": "Great_Castle_Dining", "origin": [363.0 * U_FT, 1015.0 * U_FT, 4.7 * U_FT], "pitch": 3.0, "yaw": 115.0},
            {"name": "Aerial_Overview", "origin": [360.0 * U_FT, 120.0 * U_FT, 88.0 * U_FT], "pitch": 28.0, "yaw": 195.0},
        ]
    if hotspot_ft and len(hotspot_ft) >= 3:
        hx, hy, hz = float(hotspot_ft[0]), float(hotspot_ft[1]), max(4.5, float(hotspot_ft[2]))
        yaw = round(math.degrees(math.atan2(-hy, -hx)), 1)
        sel.append({
            "name": "PVS_Hotspot_Max",
            "origin": [hx * U_FT, hy * U_FT, hz * U_FT],
            "pitch": 0.0,
            "yaw": yaw,
        })
    return sel


def benchmark_darkplaces(
    spots: Sequence[Dict[str, object]],
    hotspot_ft: Optional[Sequence[float]] = None,
) -> Dict[str, object]:
    """Profile Desktop DarkPlaces `timerefresh` across key viewpoints per CLAUDE.md."""
    if not os.path.isfile(DP_EXE):
        return {"ran": False, "reason": "darkplaces.exe not found"}
    if not os.path.isfile(BSP_PATH):
        return {"ran": False, "reason": "BSP not found"}

    for _ in range(10):
        if not _running_darkplaces_pids():
            break
        time.sleep(1.0)
    else:
        return {"ran": False, "reason": f"Existing darkplaces.exe process active: {_running_darkplaces_pids()}"}

    cfg_name = "_gw_audit4_bench.cfg"
    log_name = "zz_gw_audit4.log"
    cfg_path = os.path.join(MOD_DIR, cfg_name)
    log_path = os.path.join(MOD_DIR, log_name)
    for p in (cfg_path, log_path):
        if os.path.isfile(p):
            os.remove(p)

    sel = _select_bench_spots(spots, hotspot_ft=hotspot_ft)
    lines = ["sv_cheats 1", "noclip", "r_speeds 1"]
    for sp in sel:
        px, py, pz = sp["origin"]
        lines.append(f"echo AUDIT4_SPOT {sp['name']}")
        lines.append(f"setpos {px:.1f} {py:.1f} {pz:.1f} {sp.get('pitch', 0.0):.1f} {sp.get('yaw', 0.0):.1f} 0")
        lines.append("wait")
        lines.append("timerefresh")
    lines.append("quit")
    with open(cfg_path, "w", encoding="ascii") as f:
        f.write("\n".join(lines) + "\n")

    cfg_restore_targets = [
        os.path.join(MOD_DIR, "config.cfg"),
        os.path.join(GAME_ROOT, "id1", "config.cfg"),
    ]
    cfg_backups: Dict[str, Optional[bytes]] = {}
    for cp in cfg_restore_targets:
        if os.path.isfile(cp):
            with open(cp, "rb") as rf:
                cfg_backups[cp] = rf.read()
        else:
            cfg_backups[cp] = None

    proc = None
    try:
        t0 = time.perf_counter()
        proc = subprocess.Popen(
            [
                DP_EXE,
                "-window", "-width", "1280", "-height", "720",
                "-game", "quake15", "-game", "BakersfieldQuake",
                "-nosound", "-nohome", "-condebug",
                "+vid_mouse", "0", "+joy_enable", "0",
                "+log_file", log_name,
                "+map", "goldenwest",
                "+defer", "4", f"exec {cfg_name}",
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
            return {"ran": True, "ok": False, "reason": "DarkPlaces benchmark timed out (75s)"}

        elapsed = round(time.perf_counter() - t0, 2)
        per_spot = []
        if os.path.isfile(log_path):
            raw = open(log_path, "r", encoding="latin1", errors="replace").read()
            cur_spot = None
            for ln in raw.splitlines():
                clean = re.sub(r"\^[0-9]", "", ln).strip()
                if clean.startswith("AUDIT4_SPOT "):
                    cur_spot = clean.split(" ", 1)[1].strip()
                m = re.search(r"([0-9.]+)\s+seconds\s+\(([0-9.]+)\s+fps\)", clean)
                if m and cur_spot:
                    per_spot.append({"spot": cur_spot, "timerefresh_s": float(m.group(1)), "fps": round(float(m.group(2)), 1)})
                    cur_spot = None
        fps_vals = [float(s["fps"]) for s in per_spot]
        min_spot = min(per_spot, key=lambda s: float(s["fps"])) if per_spot else None
        return {
            "ran": True,
            "returncode": proc.returncode,
            "total_sec": elapsed,
            "avg_fps": round(sum(fps_vals) / len(fps_vals), 1) if fps_vals else 0.0,
            "min_fps": round(min(fps_vals), 1) if fps_vals else 0.0,
            "max_fps": round(max(fps_vals), 1) if fps_vals else 0.0,
            "min_spot": min_spot,
            "spots": per_spot,
        }
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
        for p in (cfg_path, log_path):
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        for cp, orig_bytes in cfg_backups.items():
            try:
                if orig_bytes is not None:
                    with open(cp, "wb") as wf:
                        wf.write(orig_bytes)
                elif os.path.isfile(cp):
                    os.remove(cp)
            except OSError:
                pass


def benchmark_browser(
    spots: Sequence[Dict[str, object]],
    hotspot_ft: Optional[Sequence[float]] = None,
) -> Dict[str, object]:
    """Profile browser WebGL cold load, transfer MB, renderer.info, and live WASD+Space+F FPS."""
    if not os.path.isdir(WEB_DIR) or not os.path.isfile(os.path.join(WEB_DIR, "index.html")):
        return {"ran": False, "reason": f"WebGL output not found at {WEB_DIR}"}

    from playwright.sync_api import sync_playwright

    handler = functools.partial(QuietHandler, directory=WEB_DIR)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    transfer_bytes = collections.Counter()
    bad: List[str] = []
    spot_metrics = []
    live_fps = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"],
            )
            page = browser.new_page(viewport={"width": 1280, "height": 720})

            def on_resp(r):
                if r.status >= 400:
                    bad.append(f"{r.status} {r.url}")
                else:
                    try:
                        b = len(r.body())
                    except Exception:
                        b = 0
                    if b <= 0:
                        try:
                            b = int(r.headers.get("content-length") or 0)
                        except Exception:
                            b = 0
                    u = r.url.split(f":{port}/")[-1]
                    bucket = "tex" if u.startswith("tex/") else ("sky" if u.startswith("sky/") else u)
                    transfer_bytes[bucket] += b

            page.on("response", on_resp)
            t0 = time.perf_counter()
            page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
            page.wait_for_function("!document.getElementById('start').disabled", timeout=25000)
            cold_load_s = round(time.perf_counter() - t0, 3)
            page.evaluate("document.getElementById('intro').style.display = 'none'")
            time.sleep(0.4)

            def measure_frames(n: int = 45):
                return page.evaluate(f"""() => new Promise(res => {{
                    let f = 0; const t0 = performance.now();
                    function step() {{
                        f++;
                        if (f < {n}) requestAnimationFrame(step);
                        else {{
                            const dt = (performance.now() - t0) / 1000.0;
                            const ri = __viewer.renderer.info;
                            res({{
                                fps: Math.round((f / dt) * 10) / 10,
                                calls: ri.render.calls,
                                tris: ri.render.triangles,
                                geom: ri.memory.geometries,
                                tex: ri.memory.textures
                            }});
                        }}
                    }}
                    requestAnimationFrame(step);
                }})""")

            for sp in _select_bench_spots(spots, hotspot_ft=hotspot_ft):
                px, py, pz = sp["origin"]
                page.evaluate(
                    """([x,y,z,yaw,pitch]) => {
                        __viewer.setFly(true);
                        __viewer.teleport({pos: [x, y, z], yaw: yaw, pitch: pitch});
                    }""",
                    [px, py, pz, sp.get("yaw", 0.0), sp.get("pitch", 0.0)],
                )
                time.sleep(0.25)
                m = measure_frames(45)
                m["spot"] = sp["name"]
                spot_metrics.append(m)

            # Live walk+jump FPS
            sx, sy, sz = _select_bench_spots(spots)[0]["origin"]
            page.evaluate(
                """([x,y,z]) => {
                    __viewer.setFly(false);
                    __viewer.teleport({pos: [x, y, z], yaw: 180, pitch: 0});
                    __viewer.keys['KeyW'] = true;
                }""",
                [sx, sy, sz],
            )
            time.sleep(0.15)
            page.evaluate("() => { __viewer.keys['Space'] = true; }")
            live_fps["walk_jump"] = measure_frames(60)
            page.evaluate("() => { __viewer.keys['KeyW'] = false; __viewer.keys['Space'] = false; }")

            # Live fly FPS
            page.evaluate(f"""() => {{
                __viewer.setFly(true);
                __viewer.teleport({{pos: [{360.0 * U_FT}, {120.0 * U_FT}, {88.0 * U_FT}], yaw: 195, pitch: 25}});
                __viewer.keys['KeyW'] = true;
            }}""")
            live_fps["fly"] = measure_frames(60)
            page.evaluate("() => { __viewer.keys['KeyW'] = false; }")

            browser.close()
    finally:
        httpd.shutdown()

    return {
        "ran": True,
        "cold_load_s": cold_load_s,
        "total_transfer_mb": round(sum(transfer_bytes.values()) / (1024 * 1024), 2),
        "transfer_kb_by_asset": {k: round(v / 1024.0, 1) for k, v in sorted(transfer_bytes.items())},
        "bad_responses": bad,
        "spot_metrics": spot_metrics,
        "live_fps": live_fps,
    }


def check_wasm_pack_compat(max_budget_mb: float = 64.0) -> Dict[str, object]:
    """Verify Golden West BSP, LIT, textures, skybox, models, and server.cfg fit WebAssembly DarkPlaces budget."""
    tex_dir = os.path.join(MOD_DIR, "textures")
    sky_dir = os.path.join(MOD_DIR, "gfx", "env")
    progs_dir = os.path.join(MOD_DIR, "progs")

    gw_tex = (
        sorted(f for f in os.listdir(tex_dir) if re.match(r"^\{?gwc_", f, re.I) and f.lower().endswith(".png"))
        if os.path.isdir(tex_dir) else []
    )
    gw_sky = (
        sorted(f for f in os.listdir(sky_dir) if f.lower().startswith("gwsky_") and f.lower().endswith((".tga", ".png", ".jpg")))
        if os.path.isdir(sky_dir) else []
    )
    gw_progs = (
        sorted(f for f in os.listdir(progs_dir) if f.lower().startswith(("gw_horse", "gw_buddha")))
        if os.path.isdir(progs_dir) else []
    )

    tex_kb = sum(os.path.getsize(os.path.join(tex_dir, f)) for f in gw_tex) / 1024.0
    sky_kb = sum(os.path.getsize(os.path.join(sky_dir, f)) for f in gw_sky) / 1024.0
    progs_kb = sum(os.path.getsize(os.path.join(progs_dir, f)) for f in gw_progs) / 1024.0
    bsp_kb = os.path.getsize(BSP_PATH) / 1024.0 if os.path.isfile(BSP_PATH) else 0.0
    lit_kb = os.path.getsize(LIT_PATH) / 1024.0 if os.path.isfile(LIT_PATH) else 0.0
    total_mb = round((bsp_kb + lit_kb + tex_kb + sky_kb + progs_kb) / 1024.0, 2)

    server_cfg_path = os.path.join(MOD_DIR, "server.cfg")
    server_cfg_txt = open(server_cfg_path, encoding="latin1").read() if os.path.isfile(server_cfg_path) else ""
    in_server_cfg = "goldenwest" in server_cfg_txt.lower()

    web_pack_py = os.path.join(MOD_DIR, "web", "make_web_pack.py")
    web_cfg = os.path.join(MOD_DIR, "web", "site", "web.cfg")
    return {
        "bsp_kb": round(bsp_kb, 1),
        "lit_kb": round(lit_kb, 1),
        "textures_count": len(gw_tex),
        "textures_kb": round(tex_kb, 1),
        "sky_count": len(gw_sky),
        "sky_kb": round(sky_kb, 1),
        "progs_files": gw_progs,
        "progs_kb": round(progs_kb, 1),
        "total_goldenwest_mb": total_mb,
        "wasm_budget_mb": max_budget_mb,
        "within_budget": total_mb <= max_budget_mb and bsp_kb > 0.0,
        "goldenwest_in_server_cfg": in_server_cfg,
        "make_web_pack_py_exists": os.path.isfile(web_pack_py),
        "web_cfg_exists": os.path.isfile(web_cfg),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit 4: Golden West Performance & WASM Compatibility")
    parser.add_argument("--skip-darkplaces", action="store_true", help="Skip live DarkPlaces timerefresh")
    parser.add_argument("--skip-web", action="store_true", help="Skip live Playwright WebGL benchmark")
    args = parser.parse_args(argv)

    os.makedirs(OUT_DIR, exist_ok=True)
    spots_path = next((p for p in SPOTS_CANDIDATES if os.path.isfile(p)), None)
    spots = load_spots(spots_path) if spots_path else []

    bsp_map = analyze_bsp_and_map()
    mod_stats = analyze_modules()
    web_disk = analyze_web_bundle()
    hotspot_ft = bsp_map.get("max_pvs_hotspot_ft")
    dp_bench = (
        {"ran": False, "skipped": True}
        if args.skip_darkplaces
        else benchmark_darkplaces(spots, hotspot_ft=hotspot_ft)  # type: ignore[arg-type]
    )
    web_bench = (
        {"ran": False, "skipped": True}
        if args.skip_web
        else benchmark_browser(spots, hotspot_ft=hotspot_ft)  # type: ignore[arg-type]
    )
    wasm_compat = check_wasm_pack_compat()

    report = {
        "bsp_and_map": bsp_map,
        "module_breakdown": mod_stats,
        "web_bundle_disk": web_disk,
        "darkplaces": dp_bench,
        "browser_webgl": web_bench,
        "wasm_pack": wasm_compat,
    }
    out_json = os.path.join(OUT_DIR, "audit4_perf_report.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
