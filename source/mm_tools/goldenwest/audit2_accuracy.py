"""audit2_accuracy.py — Audit 2 of 5: Quantitative Architectural, Road, Landscape,
Brownfield, Signage & Enterable-Interior Accuracy Check for Golden West Casino & S Union Ave.

Modeled on source/mm_tools/soi6/audit2_accuracy.py and checked directly against
REF_INVENTORY.md, OSM survey metrics (osm_route), and gw_lib.py coordinate contracts (U_FT = 12.0).

Outputs:
  - source/mm_tools/goldenwest/out/audit2_accuracy_report.json
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

if HERE not in sys.path:
    sys.path.insert(0, HERE)

from gw_lib import (  # noqa: E402
    ADAMS_ST_Y,
    BELLE_TERRACE_Y,
    CASINO_BOUNDS_FT,
    CASINO_LOT_FT,
    CASINO_ROTUNDA_CENTER_FT,
    CASINO_ROTUNDA_R_FT,
    E_4TH_ST_Y,
    E_5TH_ST_Y,
    GC_ALLEY_X,
    GC_ANNEX_BOUNDS_FT,
    GC_BLDG_BOUNDS_FT,
    GC_LOT_FT,
    GC_TOWER_BOUNDS_FT,
    HX0,
    HX1,
    HY0,
    HY1,
    MAX_TEX_NAME_LEN,
    PARCELS,
    SPECIAL_TEXTURES,
    U_FT,
    UNION_MEDIAN_X,
    UNION_NB_CARRIAGE_X,
    UNION_SB_CARRIAGE_X,
    is_forbidden_tex,
)
from audit3_nav import SPOTS_CANDIDATES, load_spots  # noqa: E402

OUT_DIR = os.path.join(HERE, "out")
REPORT_PATH = os.path.join(OUT_DIR, "audit2_accuracy_report.json")
MAP_CANDIDATES = (
    os.path.join(OUT_DIR, "goldenwest.map"),
    os.path.join(MM_TOOLS, "out", "maps", "goldenwest.map"),
)

PLANE_RE = re.compile(
    r"^\(\s*([^)]+)\s*\)\s*\(\s*([^)]+)\s*\)\s*\(\s*([^)]+)\s*\)\s+(\S+)"
)
KV_RE = re.compile(r'^"([^"]*)"\s+"([^"]*)"\s*$')

# Textures indicative of organic foliage/trees/palms in the corridor
FOLIAGE_HINTS = ("palm", "tree", "hedge", "leaf", "bark", "shrub", "bush")


def _vsub(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vcross(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _vdot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vlen(a: Sequence[float]) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def parse_map(path: str) -> Tuple[List[Dict[str, object]], List[List[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float], str]]]]:
    """Parse all entities and brushes from a Quake Valve-220 .map file."""
    entities: List[Dict[str, object]] = []
    brushes: List[List[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float], str]]] = []
    cur_ent: Optional[Dict[str, object]] = None
    cur_brush: Optional[List[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float], str]]] = None
    depth = 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if line == "{":
                depth += 1
                if depth == 1:
                    cur_ent = {"_brush_count": 0}
                elif depth == 2:
                    cur_brush = []
                continue
            if line == "}":
                if depth == 2 and cur_brush is not None:
                    brushes.append(cur_brush)
                    if cur_ent is not None:
                        cur_ent["_brush_count"] = int(cur_ent.get("_brush_count", 0)) + 1
                    cur_brush = None
                elif depth == 1 and cur_ent is not None:
                    entities.append(cur_ent)
                    cur_ent = None
                depth = max(0, depth - 1)
                continue

            if depth == 2 and cur_brush is not None:
                m = PLANE_RE.match(line)
                if m:
                    p1 = tuple(float(v) for v in m.group(1).split())
                    p2 = tuple(float(v) for v in m.group(2).split())
                    p3 = tuple(float(v) for v in m.group(3).split())
                    tex = m.group(4).lower()
                    if len(p1) == 3 and len(p2) == 3 and len(p3) == 3:
                        cur_brush.append((p1, p2, p3, tex))  # type: ignore[arg-type]
            elif depth == 1 and cur_ent is not None:
                mk = KV_RE.match(line)
                if mk:
                    cur_ent[mk.group(1)] = mk.group(2)

    return entities, brushes


def _solve_3_planes(
    n1: Tuple[float, float, float], d1: float,
    n2: Tuple[float, float, float], d2: float,
    n3: Tuple[float, float, float], d3: float,
) -> Optional[Tuple[float, float, float]]:
    c23 = _vcross(n2, n3)
    det = _vdot(n1, c23)
    if abs(det) < 1e-6:
        return None
    c31 = _vcross(n3, n1)
    c12 = _vcross(n1, n2)
    x = (d1 * c23[0] + d2 * c31[0] + d3 * c12[0]) / det
    y = (d1 * c23[1] + d2 * c31[1] + d3 * c12[1]) / det
    z = (d1 * c23[2] + d2 * c31[2] + d3 * c12[2]) / det
    return (x, y, z)


def brush_record_ft(
    brush: Sequence[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float], str]],
) -> Optional[Dict[str, object]]:
    """Compute exact 3D bounding box (in feet), textures, and unit face normals for a brush."""
    if len(brush) < 4:
        return None

    planes: List[Tuple[Tuple[float, float, float], float, str]] = []
    textures: set = set()
    axis_aligned = (len(brush) == 6)

    for p1, p2, p3, tex in brush:
        textures.add(tex)
        n_raw = _vcross(_vsub(p3, p1), _vsub(p2, p1))
        L = _vlen(n_raw)
        if L < 1e-9:
            continue
        n = (n_raw[0] / L, n_raw[1] / L, n_raw[2] / L)
        d = _vdot(n, p1)
        planes.append((n, d, tex))
        if axis_aligned and max(abs(n[0]), abs(n[1]), abs(n[2])) < 0.999:
            axis_aligned = False

    if len(planes) < 4:
        return None

    # O(1) exact path for 6-face axis-aligned rectangular prisms (majority of world brushes)
    if axis_aligned and len(planes) == 6:
        xs: List[float] = []
        ys: List[float] = []
        zs: List[float] = []
        for n, d, _tex in planes:
            if abs(n[0]) > 0.999:
                xs.append(d / n[0])
            elif abs(n[1]) > 0.999:
                ys.append(d / n[1])
            elif abs(n[2]) > 0.999:
                zs.append(d / n[2])
        if len(xs) == 2 and len(ys) == 2 and len(zs) == 2:
            x0, x1 = min(xs) / U_FT, max(xs) / U_FT
            y0, y1 = min(ys) / U_FT, max(ys) / U_FT
            z0, z1 = min(zs) / U_FT, max(zs) / U_FT
            return {
                "bbox_ft": (x0, y0, z0, x1, y1, z1),
                "size_ft": (x1 - x0, y1 - y0, z1 - z0),
                "center_ft": ((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5),
                "textures": textures,
                "normals": [p[0] for p in planes],
            }

    # General convex polyhedron path supporting both inward and outward plane windings
    candidates: List[Tuple[float, float, float]] = []
    np_len = len(planes)
    for i in range(np_len):
        n1, d1, _ = planes[i]
        for j in range(i + 1, np_len):
            n2, d2, _ = planes[j]
            for k in range(j + 1, np_len):
                n3, d3, _ = planes[k]
                pt = _solve_3_planes(n1, d1, n2, d2, n3, d3)
                if pt is not None:
                    candidates.append(pt)

    best_verts: List[Tuple[float, float, float]] = []
    best_sign = 1.0
    for sign in (1.0, -1.0):
        verts = [
            pt
            for pt in candidates
            if all(sign * (_vdot(n, pt) - d) <= 0.25 for n, d, _ in planes)
        ]
        if len(verts) > len(best_verts):
            best_verts = verts
            best_sign = sign
        if len(best_verts) >= 4:
            break

    if not best_verts:
        pts = [p for face in brush for p in face[:3]]
        x0 = min(p[0] for p in pts) / U_FT
        x1 = max(p[0] for p in pts) / U_FT
        y0 = min(p[1] for p in pts) / U_FT
        y1 = max(p[1] for p in pts) / U_FT
        z0 = min(p[2] for p in pts) / U_FT
        z1 = max(p[2] for p in pts) / U_FT
    else:
        x0 = min(p[0] for p in best_verts) / U_FT
        x1 = max(p[0] for p in best_verts) / U_FT
        y0 = min(p[1] for p in best_verts) / U_FT
        y1 = max(p[1] for p in best_verts) / U_FT
        z0 = min(p[2] for p in best_verts) / U_FT
        z1 = max(p[2] for p in best_verts) / U_FT

    outward_normals = [
        (best_sign * n[0], best_sign * n[1], best_sign * n[2]) for n, _d, _t in planes
    ]
    return {
        "bbox_ft": (x0, y0, z0, x1, y1, z1),
        "size_ft": (x1 - x0, y1 - y0, z1 - z0),
        "center_ft": ((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5),
        "textures": textures,
        "normals": outward_normals,
    }


def _overlaps_2d(b: Tuple[float, float, float, float, float, float], box: Tuple[float, float, float, float]) -> bool:
    return b[0] < box[2] and b[3] > box[0] and b[1] < box[3] and b[4] > box[1]


def _inside_2d(cx: float, cy: float, box: Tuple[float, float, float, float], pad: float = 0.0) -> bool:
    return (box[0] - pad) <= cx <= (box[2] + pad) and (box[1] - pad) <= cy <= (box[3] + pad)


def _merge_intervals(intervals: Sequence[Tuple[float, float]], merge_tol: float = 1.0) -> List[Tuple[float, float]]:
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged: List[Tuple[float, float]] = [ordered[0]]
    for a, b in ordered[1:]:
        pa, pb = merged[-1]
        if a <= pb + merge_tol:
            merged[-1] = (pa, max(pb, b))
        else:
            merged.append((a, b))
    return merged


def _covered_length(intervals: Sequence[Tuple[float, float]], lo: float, hi: float, merge_tol: float = 2.0) -> Tuple[float, float, List[Tuple[float, float]]]:
    clipped = [(max(lo, a), min(hi, b)) for a, b in intervals if b > lo and a < hi]
    merged = _merge_intervals(clipped, merge_tol=merge_tol)
    covered = sum(b - a for a, b in merged)
    gaps: List[Tuple[float, float]] = []
    cur = lo
    for a, b in merged:
        if a > cur + merge_tol:
            gaps.append((round(cur, 2), round(a, 2)))
        cur = max(cur, b)
    if cur < hi - merge_tol:
        gaps.append((round(cur, 2), round(hi, 2)))
    max_gap = max((b - a for a, b in gaps), default=0.0)
    return covered, max_gap, gaps


def check_textures_and_stones_purge(
    records: Sequence[Dict[str, object]],
    entities: Sequence[Dict[str, object]],
) -> Dict[str, object]:
    """Assert 0 legacy bklan*/bk_* textures, length <= 15, burgundy felt present, 0 STONES green felt."""
    all_tex: set = set()
    for r in records:
        all_tex.update(r["textures"])  # type: ignore[arg-type]

    forbidden = sorted(t for t in all_tex if is_forbidden_tex(t))
    overlong = sorted(t for t in all_tex if t not in SPECIAL_TEXTURES and len(t) > MAX_TEX_NAME_LEN)
    stones_tex = sorted(t for t in all_tex if "stones" in t or "green_felt" in t or "felt_green" in t)
    stones_ents = [
        e.get("classname", "entity")
        for e in entities
        if any("stones" in str(v).lower() for k, v in e.items() if k != "_brush_count")
    ]

    red_felt_tex = sorted(
        t for t in all_tex if t in ("gwc_fbj", "gwc_fbacc", "gwc_fpoker", "gwc_futh") or ("felt" in t and "red" in t)
    )
    red_felt_in_casino = [
        r
        for r in records
        if (r["textures"] & set(red_felt_tex))  # type: ignore[operator]
        and _inside_2d(r["center_ft"][0], r["center_ft"][1], CASINO_BOUNDS_FT, pad=3.0)  # type: ignore[index]
    ]

    passed = (
        len(forbidden) == 0
        and len(overlong) == 0
        and len(stones_tex) == 0
        and len(stones_ents) == 0
        and len(red_felt_in_casino) > 0
    )
    return {
        "pass": passed,
        "unique_textures_in_map": len(all_tex),
        "forbidden_legacy_textures": forbidden,
        "overlong_textures_gt15": overlong,
        "stones_green_felt_textures": stones_tex,
        "stones_entity_hits": stones_ents,
        "burgundy_felt_textures": red_felt_tex,
        "burgundy_felt_casino_brushes": len(red_felt_in_casino),
    }


def check_union_boulevard_and_median(records: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Verify 3+3 S Union carriageways (~39-41 ft), concrete middle lane slabs, and continuous brick median."""
    sb_x0, sb_x1 = UNION_SB_CARRIAGE_X  # 178..219 (41 ft)
    nb_x0, nb_x1 = UNION_NB_CARRIAGE_X  # 238..277 (39 ft)
    med_x0, med_x1 = UNION_MEDIAN_X     # 219..238 (19 ft)

    sb_x_intervals: List[Tuple[float, float]] = []
    nb_x_intervals: List[Tuple[float, float]] = []
    sb_conc_y: List[Tuple[float, float]] = []
    nb_conc_y: List[Tuple[float, float]] = []
    sb_line_xs: List[float] = []
    nb_line_xs: List[float] = []
    med_brick_y: List[Tuple[float, float]] = []

    for r in records:
        x0, y0, z0, x1, y1, z1 = r["bbox_ft"]  # type: ignore[misc]
        dx, dy, dz = r["size_ft"]  # type: ignore[misc]
        cx, cy, _cz = r["center_ft"]  # type: ignore[misc]
        texs: set = r["textures"]  # type: ignore[assignment]
        tjoin = " ".join(sorted(texs))

        # Exclude giant outer sky/world-hull bottom slabs
        if dx > 900.0 or (x0 < -400.0 and x1 > 550.0):
            continue

        # Road surface slabs (-2.5 <= z1 <= 0.6)
        if -2.5 <= z1 <= 0.6 and dy >= 6.0:
            if x1 > sb_x0 + 1.0 and x0 < sb_x1 - 1.0 and dx >= 6.0 and "brick" not in tjoin:
                sb_x_intervals.append((max(sb_x0, x0), min(sb_x1, x1)))
            if x1 > nb_x0 + 1.0 and x0 < nb_x1 - 1.0 and dx >= 6.0 and "brick" not in tjoin:
                nb_x_intervals.append((max(nb_x0, x0), min(nb_x1, x1)))

            # Concrete middle lane slabs inside lane 2 of each 3-lane carriageway
            if ("concslab" in tjoin or "gwc_conc" in tjoin) and 7.0 <= dx <= 16.0:
                if (sb_x0 + 5.0) <= cx <= (sb_x1 - 5.0):
                    sb_conc_y.append((y0, y1))
                elif (nb_x0 + 5.0) <= cx <= (nb_x1 - 5.0):
                    nb_conc_y.append((y0, y1))

        # Dashed white lane lines splitting 3 lanes per side (dx <= 1.2 ft, strictly interior)
        if -0.5 <= z1 <= 0.6 and dx <= 1.2 and ("wline" in tjoin or "stripe" in tjoin or "line" in tjoin):
            if (sb_x0 + 6.0) <= cx <= (sb_x1 - 6.0):
                sb_line_xs.append(round(cx, 1))
            elif (nb_x0 + 6.0) <= cx <= (nb_x1 - 6.0):
                nb_line_xs.append(round(cx, 1))

        # Raised red herringbone brick median from Adams (-576) to Belle Terrace (+557.7)
        if (
            0.05 <= z1 <= 1.5
            and x1 > med_x0 + 1.0
            and x0 < med_x1 - 1.0
            and dx >= 10.0
            and ("brick" in tjoin or "median" in tjoin or "curbred" in tjoin)
        ):
            med_brick_y.append((y0, y1))

    # Cluster lane line X coords by >= 4 ft separation
    def _distinct_clusters(vals: Sequence[float]) -> List[float]:
        clusters: List[float] = []
        for v in sorted(vals):
            if not clusters or abs(v - clusters[-1]) >= 4.0:
                clusters.append(v)
        return clusters

    sb_width_cov, _, _ = _covered_length(sb_x_intervals, sb_x0, sb_x1, merge_tol=0.8)
    nb_width_cov, _, _ = _covered_length(nb_x_intervals, nb_x0, nb_x1, merge_tol=0.8)
    sb_conc_cov, _, _ = _covered_length(sb_conc_y, -780.0, 720.0, merge_tol=8.0)
    nb_conc_cov, _, _ = _covered_length(nb_conc_y, -780.0, 720.0, merge_tol=8.0)

    sb_dividers = _distinct_clusters(sb_line_xs)
    nb_dividers = _distinct_clusters(nb_line_xs)

    med_span = BELLE_TERRACE_Y - ADAMS_ST_Y  # ~1133.7 ft
    med_cov, med_max_gap, med_gaps = _covered_length(
        med_brick_y, ADAMS_ST_Y + 20.0, BELLE_TERRACE_Y - 22.0, merge_tol=5.0
    )
    med_cov_pct = (med_cov / max(1.0, (BELLE_TERRACE_Y - 22.0) - (ADAMS_ST_Y + 20.0))) * 100.0
    cut_at_north_drive = any(a <= 165.0 <= b for a, b in med_gaps)
    cut_at_south_drive = any(a <= -87.0 <= b for a, b in med_gaps)

    passed = (
        sb_width_cov >= 38.0
        and nb_width_cov >= 36.0
        and len(sb_dividers) >= 2
        and len(nb_dividers) >= 2
        and sb_conc_cov >= 400.0
        and nb_conc_cov >= 400.0
        and med_cov_pct >= 90.0
        and not cut_at_north_drive
        and not cut_at_south_drive
    )
    return {
        "pass": passed,
        "sb_carriageway_expected_ft": round(sb_x1 - sb_x0, 2),
        "sb_carriageway_covered_ft": round(sb_width_cov, 2),
        "nb_carriageway_expected_ft": round(nb_x1 - nb_x0, 2),
        "nb_carriageway_covered_ft": round(nb_width_cov, 2),
        "sb_lane_divider_x_ft": sb_dividers,
        "nb_lane_divider_x_ft": nb_dividers,
        "sb_concrete_midlane_cov_ft": round(sb_conc_cov, 1),
        "nb_concrete_midlane_cov_ft": round(nb_conc_cov, 1),
        "median_adams_to_belle_span_ft": round(med_span, 1),
        "median_brick_coverage_pct": round(med_cov_pct, 1),
        "median_max_gap_ft": round(med_max_gap, 1),
        "median_gaps_ft": med_gaps,
        "illegal_cut_at_north_drive_165": cut_at_north_drive,
        "illegal_cut_at_south_drive_neg87": cut_at_south_drive,
    }


def check_median_palm_clusters(records: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Verify localized median palm/shrub/tree clusters and bare southern brick zone."""
    tall_palm_pts: List[Tuple[float, float, float]] = []
    shrub_tree_pts: List[Tuple[float, float, float]] = []

    for r in records:
        x0, y0, _z0, x1, y1, z1 = r["bbox_ft"]  # type: ignore[misc]
        dx, dy, _dz = r["size_ft"]  # type: ignore[misc]
        cx, cy, _cz = r["center_ft"]  # type: ignore[misc]
        tjoin = " ".join(sorted(r["textures"]))  # type: ignore[arg-type]

        # Must sit in/over the Union Ave median strip
        if not (216.0 <= cx <= 241.0) or dx > 16.0 or dy > 160.0 or z1 < 2.0:
            continue
        if not any(h in tjoin for h in FOLIAGE_HINTS):
            continue

        if ("palm" in tjoin and z1 >= 14.0) or z1 >= 18.0:
            if dy <= 24.0:
                tall_palm_pts.append((round(cx, 1), round(cy, 1), round(z1, 1)))
        else:
            if dy <= 24.0:
                shrub_tree_pts.append((round(cx, 1), round(cy, 1), round(z1, 1)))
            else:
                # Sample both ends of long hedge strips so full coverage is represented
                shrub_tree_pts.append((round(cx, 1), round(y0 + 3.0, 1), round(z1, 1)))
                shrub_tree_pts.append((round(cx, 1), round(y1 - 3.0, 1), round(z1, 1)))

    # Deduplicate nearby brush fragments belonging to the same tree/palm within 5 ft in Y
    def _cluster_y(pts: Sequence[Tuple[float, float, float]]) -> List[float]:
        ys: List[float] = []
        for _x, y, _z in sorted(pts, key=lambda t: t[1]):
            if not ys or abs(y - ys[-1]) >= 6.0:
                ys.append(y)
        return ys

    palm_ys = _cluster_y(tall_palm_pts)
    shrub_ys = _cluster_y(shrub_tree_pts)

    north_cluster = [y for y in palm_ys if 165.0 <= y <= 290.0]
    casino_front_palms = [y for y in palm_ys if -20.0 <= y <= 145.0]
    casino_front_shrubs = [y for y in shrub_ys if -25.0 <= y <= 145.0]
    south_trees = [y for y in (palm_ys + shrub_ys) if -355.0 <= y <= -55.0]
    bare_zone_foliage = [y for y in (palm_ys + shrub_ys) if -550.0 <= y <= -355.0]

    passed = (
        len(north_cluster) >= 4
        and len(casino_front_palms) == 0
        and len(casino_front_shrubs) >= 2
        and len(south_trees) >= 2
        and len(bare_zone_foliage) == 0
    )
    return {
        "pass": passed,
        "north_lot_tall_palm_ys": north_cluster,
        "casino_front_tall_palm_ys_should_be_empty": casino_front_palms,
        "casino_front_shrub_ys": casino_front_shrubs,
        "south_median_tree_ys": south_trees,
        "bare_southern_brick_zone_foliage_should_be_empty": bare_zone_foliage,
    }


def check_casino_architecture(records: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Verify BLDG 59517066 ~156.2x161.4 ft envelope, 12-sided rotunda, wood clerestory & 45-deg NE portico."""
    env_pad = (
        CASINO_BOUNDS_FT[0] - 4.0,
        CASINO_BOUNDS_FT[1] - 4.0,
        CASINO_BOUNDS_FT[2] + 4.0,
        CASINO_BOUNDS_FT[3] + 4.0,
    )
    bldg_brushes: List[Dict[str, object]] = []
    rotunda_brushes: List[Dict[str, object]] = []
    clerestory_brushes: List[Dict[str, object]] = []
    portico_diag_hits = 0
    portico_entry_props = 0

    rcx, rcy = CASINO_ROTUNDA_CENTER_FT
    for r in records:
        x0, y0, _z0, x1, y1, z1 = r["bbox_ft"]  # type: ignore[misc]
        dx, dy, _dz = r["size_ft"]  # type: ignore[misc]
        cx, cy, _cz = r["center_ft"]  # type: ignore[misc]
        tjoin = " ".join(sorted(r["textures"]))  # type: ignore[arg-type]

        # Skip giant world boxes & ground paving aprons outside building walls
        if dx > 180.0 or dy > 190.0 or z1 < 4.0:
            continue
        if not _inside_2d(cx, cy, CASINO_BOUNDS_FT, pad=5.0):
            continue
        if x0 < env_pad[0] - 6.0 or x1 > env_pad[2] + 6.0 or y0 < env_pad[1] - 6.0 or y1 > env_pad[3] + 6.0:
            continue

        bldg_brushes.append(r)

        # Rotunda cluster around (78.9, -25.5), R=23.1 ft
        dist_r = math.hypot(cx - rcx, cy - rcy)
        if dist_r <= CASINO_ROTUNDA_R_FT + 4.0 and x1 > 50.0 and y0 > -56.0 and y1 < 6.0:
            rotunda_brushes.append(r)

        # Elevated dark-brown vertical wood clerestory gable above center spine
        if z1 >= 23.0 and -28.0 <= cx <= 52.0 and ("batten" in tjoin or "wood" in tjoin or "shingle" in tjoin):
            if "batten" in tjoin or "wood" in tjoin:
                clerestory_brushes.append(r)

        # 45-degree NE portico & plaza (x in [25, 98], y in [-15, 78])
        if 25.0 <= cx <= 98.0 and -15.0 <= cy <= 78.0:
            for nx, ny, nz in r["normals"]:  # type: ignore[attr-defined]
                if abs(nz) < 0.88 and abs(nx) > 0.30 and abs(ny) > 0.30 and abs(abs(nx) - abs(ny)) < 0.35:
                    portico_diag_hits += 1
            if "pushtoop" in tjoin or "usflag" in tjoin or "glass" in tjoin:
                portico_entry_props += 1

    if bldg_brushes:
        bx0 = min(r["bbox_ft"][0] for r in bldg_brushes)  # type: ignore[index]
        by0 = min(r["bbox_ft"][1] for r in bldg_brushes)  # type: ignore[index]
        bx1 = max(r["bbox_ft"][3] for r in bldg_brushes)  # type: ignore[index]
        by1 = max(r["bbox_ft"][4] for r in bldg_brushes)  # type: ignore[index]
        bw = round(bx1 - bx0, 2)
        bd = round(by1 - by0, 2)
        env_ok = abs(bw - 156.2) <= 7.0 and abs(bd - 161.4) <= 7.0
    else:
        bx0 = by0 = bx1 = by1 = bw = bd = 0.0
        env_ok = False

    # Measure distinct radial normal buckets around Rotunda perimeter (expect ~12)
    rot_angles: set = set()
    rot_max_z = 0.0
    for r in rotunda_brushes:
        rot_max_z = max(rot_max_z, float(r["bbox_ft"][5]))  # type: ignore[index]
        for nx, ny, nz in r["normals"]:  # type: ignore[attr-defined]
            if math.hypot(nx, ny) > 0.35 and abs(nz) < 0.85:
                ang_deg = math.degrees(math.atan2(ny, nx)) % 360.0
                bucket = int(round(ang_deg / 20.0)) % 18
                rot_angles.add(bucket)

    rotunda_ok = len(rot_angles) >= 8 and rot_max_z >= 20.0
    clerestory_ok = len(clerestory_brushes) >= 1
    portico_ok = portico_diag_hits >= 2 or portico_entry_props >= 1

    return {
        "pass": env_ok and rotunda_ok and clerestory_ok and portico_ok,
        "envelope_target_ft": [156.2, 161.4],
        "envelope_measured_ft": [bw, bd],
        "envelope_bbox_ft": [round(bx0, 2), round(by0, 2), round(bx1, 2), round(by1, 2)],
        "envelope_ok": env_ok,
        "rotunda_distinct_angle_buckets": len(rot_angles),
        "rotunda_max_z_ft": round(rot_max_z, 2),
        "rotunda_ok": rotunda_ok,
        "clerestory_wood_brushes": len(clerestory_brushes),
        "clerestory_ok": clerestory_ok,
        "portico_45deg_normal_hits": portico_diag_hits,
        "portico_entry_props": portico_entry_props,
        "portico_ok": portico_ok,
    }


def check_great_castle_architecture(records: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Verify Great Castle ~77.5x71.5 ft fortress envelope, >=19 ft SW watchtower, merlons, awning, SE annex & interior."""
    env_pad = (
        GC_BLDG_BOUNDS_FT[0] - 4.0,
        GC_BLDG_BOUNDS_FT[1] - 4.0,
        GC_BLDG_BOUNDS_FT[2] + 4.0,
        GC_BLDG_BOUNDS_FT[3] + 4.0,
    )
    bldg_brushes: List[Dict[str, object]] = []
    merlon_brushes = 0
    awning_brushes = 0
    pylon_brushes = 0
    annex_brushes = 0
    interior_detail_brushes = 0
    tower_max_z = 0.0

    for r in records:
        x0, y0, _z0, x1, y1, z1 = r["bbox_ft"]  # type: ignore[misc]
        dx, dy, _dz = r["size_ft"]  # type: ignore[misc]
        cx, cy, _cz = r["center_ft"]  # type: ignore[misc]
        tjoin = " ".join(sorted(r["textures"]))  # type: ignore[arg-type]

        if "gwc_gcpylon" in tjoin:
            pylon_brushes += 1
        if "gwc_gcawn" in tjoin:
            awning_brushes += 1

        if _inside_2d(cx, cy, GC_ANNEX_BOUNDS_FT, pad=3.0) and z1 >= 6.0 and dx < 60.0 and dy < 80.0:
            annex_brushes += 1

        if _inside_2d(cx, cy, GC_TOWER_BOUNDS_FT, pad=3.0) and z1 <= 26.0 and dx < 40.0 and dy < 40.0:
            tower_max_z = max(tower_max_z, float(z1))

        if dx > 100.0 or dy > 100.0 or z1 < 4.0:
            continue
        if not _inside_2d(cx, cy, GC_BLDG_BOUNDS_FT, pad=3.0):
            continue
        if x0 < env_pad[0] - 4.0 or x1 > env_pad[2] + 4.0 or y0 < env_pad[1] - 4.0 or y1 > env_pad[3] + 4.0:
            continue

        if _inside_2d(cx, cy, GC_BLDG_BOUNDS_FT, pad=0.5) and "gwc_gcawn" not in tjoin:
            bldg_brushes.append(r)
        if "gwc_gcmerlon" in tjoin or z1 >= 15.5:
            merlon_brushes += 1
        if any(k in tjoin for k in ("gwc_gccarp", "gwc_gclant", "gwc_gcwall", "gwc_gcscrn")):
            interior_detail_brushes += 1

    if bldg_brushes:
        bx0 = min(r["bbox_ft"][0] for r in bldg_brushes)  # type: ignore[index]
        by0 = min(r["bbox_ft"][1] for r in bldg_brushes)  # type: ignore[index]
        bx1 = max(r["bbox_ft"][3] for r in bldg_brushes)  # type: ignore[index]
        by1 = max(r["bbox_ft"][4] for r in bldg_brushes)  # type: ignore[index]
        bw = round(bx1 - bx0, 2)
        bd = round(by1 - by0, 2)
        env_ok = abs(bw - 77.5) <= 6.0 and abs(bd - 71.5) <= 6.0
    else:
        bx0 = by0 = bx1 = by1 = bw = bd = 0.0
        env_ok = False

    tower_ok = tower_max_z >= 19.0
    merlons_ok = merlon_brushes >= 4
    awning_pylon_ok = awning_brushes >= 1 and pylon_brushes >= 1
    annex_ok = annex_brushes >= 1
    interior_ok = interior_detail_brushes >= 1

    return {
        "pass": env_ok and tower_ok and merlons_ok and awning_pylon_ok and annex_ok and interior_ok,
        "envelope_target_ft": [77.5, 71.5],
        "envelope_measured_ft": [bw, bd],
        "envelope_bbox_ft": [round(bx0, 2), round(by0, 2), round(bx1, 2), round(by1, 2)],
        "envelope_ok": env_ok,
        "tower_max_z_ft": round(tower_max_z, 2),
        "tower_ok": tower_ok,
        "merlon_brushes": merlon_brushes,
        "merlons_ok": merlons_ok,
        "awning_brushes": awning_brushes,
        "pylon_brushes": pylon_brushes,
        "awning_pylon_ok": awning_pylon_ok,
        "annex_brushes": annex_brushes,
        "annex_ok": annex_ok,
        "interior_detail_brushes": interior_detail_brushes,
        "interior_ok": interior_ok,
    }


def check_brownfields_open(records: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Ensure 891 S Union vacant dirt lot and SE Belle Terrace El Don brownfield remain open."""
    # REF_INVENTORY 4.1: 891 S Union vacant lot sits NW of Casino (billboard_lot: -150..172, 304.2..532.0)
    # plus green_mesh_891 north of Belle Terrace (-150..48, 582..668)
    lot_891_sw = (-148.0, 306.0, 166.0, 528.0)
    lot_891_nw = (-148.0, 584.0, 46.0, 666.0)
    lot_eldon = (286.0, 426.0, 646.0, 528.0)

    def _find_enclosed_buildings(box: Tuple[float, float, float, float]) -> List[Dict[str, object]]:
        violations: List[Dict[str, object]] = []
        for r in records:
            x0, y0, z0, x1, y1, z1 = r["bbox_ft"]  # type: ignore[misc]
            dx, dy, dz = r["size_ft"]  # type: ignore[misc]
            cx, cy, _ = r["center_ft"]  # type: ignore[misc]
            tjoin = " ".join(sorted(r["textures"]))  # type: ignore[arg-type]
            if not _inside_2d(cx, cy, box):
                continue
            # Ignore terrain/ground pads, low rubble curbs, fences, poles, and billboard faces
            if z1 <= 8.0 or z0 >= 28.0:
                continue
            if min(dx, dy) <= 6.0:
                continue
            if any(k in tjoin for k in ("palm", "tree", "greenmesh", "chain", "bboard", "eldon", "sky")):
                continue
            if dx > 14.0 and dy > 14.0 and dz > 6.0:
                violations.append({
                    "bbox_ft": [round(v, 1) for v in r["bbox_ft"]],  # type: ignore[index]
                    "textures": sorted(r["textures"]),  # type: ignore[arg-type]
                })
        return violations

    green_mesh_hits = sum(
        1
        for r in records
        if ("greenmesh" in " ".join(sorted(r["textures"])))  # type: ignore[arg-type]
        and _inside_2d(r["center_ft"][0], r["center_ft"][1], (-155.0, 300.0, 175.0, 675.0))  # type: ignore[index]
    )
    eldon_sign_hits = sum(
        1
        for r in records
        if ("eldon" in " ".join(sorted(r["textures"])))  # type: ignore[arg-type]
        and _inside_2d(r["center_ft"][0], r["center_ft"][1], PARCELS["el_don_brownfield"], pad=6.0)  # type: ignore[index]
    )

    v_891 = _find_enclosed_buildings(lot_891_sw) + _find_enclosed_buildings(lot_891_nw)
    v_eldon = _find_enclosed_buildings(lot_eldon)

    passed = len(v_891) == 0 and len(v_eldon) == 0 and green_mesh_hits >= 1 and eldon_sign_hits >= 1
    return {
        "pass": passed,
        "lot_891_green_mesh_brushes": green_mesh_hits,
        "lot_891_enclosed_building_violations": v_891,
        "el_don_brownfield_sign_brushes": eldon_sign_hits,
        "el_don_enclosed_building_violations": v_eldon,
    }


def check_signage_inventory(records: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Verify placed .map signage and street signs for every landmark."""
    tex_counts: collections.Counter = collections.Counter()
    for r in records:
        for t in r["textures"]:  # type: ignore[attr-defined]
            tex_counts[t] += 1

    required_groups: Dict[str, Tuple[str, ...]] = {
        "Golden West Pylon": ("gwc_pyltop", "gwc_pylled"),
        "Blackjack Lounge Neon": ("gwc_bjneon", "{gwc_bjneon", "gwc_lgneon", "{gwc_lgneon"),
        "Star-Liter Motel Sign": ("gwc_starlt",),
        "Ramos Tires Sign": ("gwc_ramos", "gwc_ramosop"),
        "Compas / Best DEALS Sign": ("gwc_bdeal",),
        "Sunland Motel Sign": ("gwc_sunlnd",),
        "Country Inn Motel Sign": ("gwc_cntry",),
        "Playfair Market / Mural": ("gwc_pfmarket", "gwc_playfr", "gwc_pfmural"),
        "Super 8 Diamond Pylon": ("gwc_super8",),
        "Carnitas Birria Sign": ("gwc_carnit", "gwc_menu", "{gwc_menudof", "gwc_menudof"),
        "El Don Motel Sign": ("gwc_eldon",),
        "S Union Ave Street Blade": ("gwc_sunion",),
        "E Belle Terrace Blade": ("gwc_sbelle",),
        "Traffic Signals": ("gwc_tsig_g", "gwc_tsig_y", "gwc_tsig_r"),
        "CA-99 BUS / Speed 45": ("gwc_ca99", "gwc_spd45"),
        "Great Castle West / Pylon": ("gwc_gcwest", "gwc_gcpylon"),
        "Great Castle Plaque / Address / OPEN": ("gwc_gcplaque", "gwc_gc410", "gwc_gcopen"),
        "E 4th St / E 5th St Blades": ("gwc_e4st", "gwc_e5st"),
        "Deal Time Auto Sign": ("gwc_dealtime",),
        "Reyes Tires Signs": ("gwc_reyespole", "gwc_reyes"),
        "Shamrock / DG Market Signs": ("gwc_shamrock", "gwc_dgmrkt"),
    }
    optional_groups: Dict[str, Tuple[str, ...]] = {
        "Adams St Blade": ("gwc_sadams",),
        "Trinity Ave Blade": ("gwc_strin",),
        "Delaware St Blade": ("gwc_sdel",),
        "Mariposa Ave Blade": ("gwc_smari",),
        "Amador Ave Blade": ("gwc_samad",),
        "Century Glass / Windows & Doors": ("gwc_windoor",),
        "Great Castle Interior Art & Restrooms": ("gwc_gcrest", "gwc_gcmural", "gwc_gccallig"),
    }

    found_req: Dict[str, int] = {}
    missing_req: List[str] = []
    for label, opts in required_groups.items():
        cnt = sum(tex_counts[o] for o in opts)
        if cnt > 0:
            found_req[label] = cnt
        else:
            missing_req.append(label)

    found_opt: Dict[str, int] = {}
    missing_opt: List[str] = []
    for label, opts in optional_groups.items():
        cnt = sum(tex_counts[o] for o in opts)
        if cnt > 0:
            found_opt[label] = cnt
        else:
            missing_opt.append(label)

    return {
        "pass": len(missing_req) == 0,
        "required_found": found_req,
        "required_missing": missing_req,
        "optional_found": found_opt,
        "optional_missing": missing_opt,
    }


def check_interiors_and_lighting(
    entities: Sequence[Dict[str, object]],
    spots: Sequence[Dict[str, object]],
) -> Dict[str, object]:
    """Verify enterable interior zones have dedicated light entities (and spot coverage when loaded)."""
    lights_ft: List[Tuple[float, float, float, float]] = []
    for ent in entities:
        cn = str(ent.get("classname", "")).lower()
        if not cn.startswith("light"):
            continue
        orig = str(ent.get("origin", "")).split()
        if len(orig) != 3:
            continue
        lx, ly, lz = (float(v) / U_FT for v in orig)
        mag = float(ent.get("light", "300"))
        lights_ft.append((lx, ly, lz, mag))

    # Required enterable interior zones in feet (x0, y0, x1, y1)
    required_zones: Dict[str, Tuple[float, float, float, float]] = {
        "Golden West Casino Main & Rotunda": CASINO_BOUNDS_FT,
        "Casino North Guard Booth": (98.0, 174.0, 142.0, 214.0),
        "Carnitas Birria Menudo Diner": PARCELS["carnitas_birria"],
        "Star-Liter Motor Motel": PARCELS["star_liter_motel"],
        "Ramos Tires & Service": PARCELS["ramos_tires"],
        "Compas Auto Sales Office": PARCELS["compas_auto"],
        "Sunland Motel": PARCELS["sunland_motel"],
        "Country Inn Motel": PARCELS["country_inn_motel"],
        "Playfair Market": PARCELS["playfair_market"],
        "Super 8 Motel": PARCELS["super8_motel"],
        "Great Castle Restaurant Interior": GC_BLDG_BOUNDS_FT,
        "Reyes Tires Service Bay": PARCELS["gc_reyes_tires"],
    }
    residential_zones: Dict[str, Tuple[float, float, float, float]] = {
        "West Casino Fringe": PARCELS["west_casino_fringe"],
        "West Trinity South": PARCELS["west_trinity_south"],
        "West Mariposa South": PARCELS["west_mariposa_south"],
    }

    zone_stats: Dict[str, Dict[str, object]] = {}
    missing_zones: List[str] = []

    for name, box in required_zones.items():
        z_lights = [l for l in lights_ft if _inside_2d(l[0], l[1], box, pad=2.0) and 1.0 <= l[2] <= 34.0]
        z_spots = [
            sp
            for sp in spots
            if _inside_2d(
                float(sp["origin"][0]) / U_FT,  # type: ignore[index]
                float(sp["origin"][1]) / U_FT,  # type: ignore[index]
                box,
                pad=2.0,
            )
        ]
        min_req = 6 if "Casino Main" in name else 1
        ok = len(z_lights) >= min_req
        if not ok:
            missing_zones.append(name)
        zone_stats[name] = {
            "lights": len(z_lights),
            "spots": len(z_spots),
            "ok": ok,
        }

    res_lit = 0
    for name, box in residential_zones.items():
        z_lights = [l for l in lights_ft if _inside_2d(l[0], l[1], box, pad=2.0) and 1.0 <= l[2] <= 24.0]
        z_spots = [
            sp
            for sp in spots
            if _inside_2d(
                float(sp["origin"][0]) / U_FT,  # type: ignore[index]
                float(sp["origin"][1]) / U_FT,  # type: ignore[index]
                box,
                pad=2.0,
            )
        ]
        if len(z_lights) > 0:
            res_lit += 1
        zone_stats[name] = {"lights": len(z_lights), "spots": len(z_spots), "ok": len(z_lights) > 0}

    res_ok = res_lit >= 2
    if not res_ok:
        missing_zones.append("West Residential Enterable Houses (>=2 blocks)")

    return {
        "pass": len(missing_zones) == 0,
        "total_light_entities": len(lights_ft),
        "total_spots_loaded": len(spots),
        "missing_interior_lighting": missing_zones,
        "zones": zone_stats,
    }


def run_audit2(
    *,
    map_path: Optional[str] = None,
    spots_path: Optional[str] = None,
    out_path: str = REPORT_PATH,
) -> Dict[str, object]:
    """Run all Audit 2 real-world accuracy checks against the .map and .spots.json."""
    chosen_map = map_path
    if not chosen_map:
        chosen_map = next((p for p in MAP_CANDIDATES if os.path.isfile(p)), MAP_CANDIDATES[0])
    if not os.path.isfile(chosen_map):
        raise FileNotFoundError(f"goldenwest.map not found at {chosen_map}")

    chosen_spots = spots_path
    if not chosen_spots:
        chosen_spots = next((p for p in SPOTS_CANDIDATES if os.path.isfile(p)), None)
    spots = load_spots(chosen_spots) if chosen_spots and os.path.isfile(chosen_spots) else []

    entities, brushes = parse_map(chosen_map)
    records = [r for r in (brush_record_ft(b) for b in brushes) if r is not None]

    c_tex = check_textures_and_stones_purge(records, entities)
    c_road = check_union_boulevard_and_median(records)
    c_palms = check_median_palm_clusters(records)
    c_casino = check_casino_architecture(records)
    c_great_castle = check_great_castle_architecture(records)
    c_brown = check_brownfields_open(records)
    c_signs = check_signage_inventory(records)
    c_interiors = check_interiors_and_lighting(entities, spots)

    all_checks = {
        "textures_and_stones_purge": c_tex,
        "union_3plus3_and_brick_median": c_road,
        "median_palm_clusters": c_palms,
        "casino_architecture": c_casino,
        "great_castle_architecture": c_great_castle,
        "brownfields_open": c_brown,
        "signage_inventory": c_signs,
        "interiors_and_lighting": c_interiors,
    }
    passed = all(bool(v["pass"]) for v in all_checks.values())
    failed_checks = [k for k, v in all_checks.items() if not v["pass"]]

    report = {
        "audit": "audit2_accuracy",
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "pass": passed,
        "map_path": chosen_map,
        "spots_path": chosen_spots,
        "scale_u_per_ft": U_FT,
        "world_bounds_ft": [HX0, HY0, HX1, HY1],
        "entities_count": len(entities),
        "brushes_count": len(records),
        "failed_checks": failed_checks,
        "checks": all_checks,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit 2: Quantitative Architectural, Road, Landscape & Signage Accuracy Audit"
    )
    parser.add_argument("--map", default=None, help="Path to goldenwest.map")
    parser.add_argument("--spots", default=None, help="Path to goldenwest.spots.json")
    parser.add_argument("--out", default=REPORT_PATH, help="JSON report output path")
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Write JSON report and exit 0 even when checks fail",
    )
    args = parser.parse_args(argv)

    rep = run_audit2(map_path=args.map, spots_path=args.spots, out_path=args.out)
    print(
        f"[audit2] status={rep['status']} brushes={rep['brushes_count']} "
        f"entities={rep['entities_count']} failed={rep['failed_checks']}"
    )
    print(f"[audit2] report -> {args.out}")
    if args.no_fail:
        return 0
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
