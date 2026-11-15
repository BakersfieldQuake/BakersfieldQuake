"""gw_casino_ext.py — Golden West Casino Exterior, Sitework & Roofs for BakersfieldQuake.

Exclusive module ownership:
  - Exports `build_casino_ext(mb)` operating inside `CASINO_LOT_FT` outside
    `CASINO_POLY_FT` (excluding Delaware St & Trinity Ave road corridors) plus
    the complete Casino roof superstructure strictly above `gw_casino_int` walls
    (`z >= 16.0 ft` on spine/BOH/SE wings; `z >= 13.0 ft` on 12-sided Rotunda).
  - Uses ONLY cataloged `gwc_*` / `{gwc_*` / `skip` / `clip` textures (`0` legacy
    `bklan*` / `bk_*` / `{chain` / `sky_bk` names).
  - Doorway & roof seams locked with `gw_casino_int` (#20/#23) and S Union Ave
    aprons / elevations locked with `gw_streets`.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

GW_DIR = os.path.dirname(os.path.abspath(__file__))
if GW_DIR not in sys.path:
    sys.path.insert(0, GW_DIR)

from gw_lib import (  # noqa: E402
    CASINO_BOUNDS_FT,
    CASINO_FLOOR_Z_FT,
    CASINO_LOT_FT,
    CASINO_ROTUNDA_CENTER_FT,
    CASINO_ROTUNDA_R_FT,
    Fit,
    MapBuilder,
    Tile,
    snap_val,
)

# ---------------------------------------------------------------------------
# Shared seam elevations (12 u/ft, locked with gw_streets.py & gw_casino_int)
# ---------------------------------------------------------------------------
Z_GROUND_FT: float = 0.0
Z_ROAD_FT: float = 2.0 / 12.0       # 2.0 u — lot asphalt & driveway aprons
Z_MARK_FT: float = 2.5 / 12.0       # 2.5 u — flush parking stripes
Z_WALK_FT: float = CASINO_FLOOR_Z_FT  # 0.50 ft = 6.0 u — courtyard & thresholds

Z_WALL_TOP_FT: float = 16.0         # Spine / BOH / SE stone wing exterior top
Z_ROTUNDA_TOP_FT: float = 13.0      # 12-sided Rotunda stone wall top

# NE 45-deg main storefront chord (#20): (43.0, 7.0) -> (62.0, -12.0) (x+y=50)
NE_CENTER_FT: Tuple[float, float] = (52.5, -2.5)
_INV_SQRT2: float = 1.0 / math.sqrt(2.0)
NE_U: Tuple[float, float] = (_INV_SQRT2, -_INV_SQRT2)   # Along facade (SE)
NE_N: Tuple[float, float] = (_INV_SQRT2, _INV_SQRT2)    # Outward normal (NE)

# Shared texture specs (100% cataloged gwc_* / {gwc_* names)
def _refresh_shared_tiles() -> None:
    global TEX_ASPH, TEX_CONC, TEX_CONCSLAB, TEX_FLAG, TEX_CURB, TEX_CURBRED
    global TEX_STONE, TEX_STUCCO, TEX_CRMSTUC, TEX_CINDER, TEX_DARK, TEX_WHITE
    global TEX_SHINGLE, TEX_TPO, TEX_BATTEN, TEX_BEAM, TEX_WOOD, TEX_GALV, TEX_DUCT
    global TEX_GLASS, TEX_GOLDWIN, TEX_HEDGE, TEX_MULCH, TEX_BARK, TEX_PALMHAT
    global TEX_PURPLE, TEX_BOOTH, TEX_IRON, TEX_CHAIN
    TEX_ASPH = Tile("gwc_asph", 14.0, 14.0)
    TEX_CONC = Tile("gwc_conc", 8.0, 8.0)
    TEX_CONCSLAB = Tile("gwc_concslab", 10.0, 10.0)
    TEX_FLAG = Tile("gwc_flag", 8.0, 8.0)
    TEX_CURB = Tile("gwc_curb", 6.0, 1.0)
    TEX_CURBRED = Tile("gwc_curbred", 6.0, 1.0)
    TEX_STONE = Tile("gwc_stone", 6.0, 4.0)
    TEX_STUCCO = Tile("gwc_stucco", 8.0, 8.0)
    TEX_CRMSTUC = Tile("gwc_crmstuc", 8.0, 8.0)
    TEX_CINDER = Tile("gwc_cinder", 6.0, 4.0)
    TEX_DARK = Tile("gwc_dark", 6.0, 6.0)
    TEX_WHITE = Tile("gwc_white", 4.0, 4.0)
    TEX_SHINGLE = Tile("gwc_shingle", 8.0, 8.0)
    TEX_TPO = Tile("gwc_tpo", 12.0, 12.0)
    TEX_BATTEN = Tile("gwc_batten", 6.0, 8.0)
    TEX_BEAM = Tile("gwc_beam", 6.0, 4.0)
    TEX_WOOD = Tile("gwc_wood", 6.0, 6.0)
    TEX_GALV = Tile("gwc_galv", 6.0, 6.0)
    TEX_DUCT = Tile("gwc_duct", 4.0, 4.0)
    TEX_GLASS = Tile("gwc_glass", 6.0, 6.0)
    TEX_GOLDWIN = Tile("gwc_goldwin", 6.0, 6.0)
    TEX_HEDGE = Tile("gwc_hedge", 5.0, 5.0)
    TEX_MULCH = Tile("gwc_mulch", 4.0, 4.0)
    TEX_BARK = Tile("gwc_bark", 2.5, 4.0)
    TEX_PALMHAT = Tile("gwc_palmhat", 3.0, 3.0)
    TEX_PURPLE = Tile("gwc_purple", 6.0, 8.0)
    TEX_BOOTH = Tile("gwc_booth", 6.0, 6.0)
    TEX_IRON = Tile("{gwc_ironfence", 6.0, 4.5)
    TEX_CHAIN = Tile("{gwc_chain", 8.0, 6.5)


_refresh_shared_tiles()


# ---------------------------------------------------------------------------
# Geometry primitives helpers
# ---------------------------------------------------------------------------

def _vsub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vcross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _vnorm(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if m < 1e-8:
        return (0.0, 0.0, 1.0)
    return (v[0] / m, v[1] / m, v[2] / m)


def _emit_convex_ft(
    mb: MapBuilder,
    faces_ft: Sequence[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], object]],
    group: str = "detail",
    force_world: bool = False,
) -> None:
    """Convert arbitrary convex planes from feet to units and emit via MapBuilder."""
    u = mb.u_per_ft
    snap = mb.world_snap_u if (group in ("world", "clip") or force_world) else mb.detail_snap_u
    faces_u = []
    for pts_ft, out, spec in faces_ft:
        pts_u = [
            (snap_val(p[0] * u, snap), snap_val(p[1] * u, snap), snap_val(p[2] * u, snap))
            for p in pts_ft
        ]
        faces_u.append((pts_u, _vnorm(out), spec))
    mb._emit_brush(faces_u, group=group, force_world=force_world)


def _extrude_poly_skip_ft(
    mb: MapBuilder,
    pts_2d_ft: Sequence[Tuple[float, float]],
    plane: str,
    w0_ft: float,
    w1_ft: float,
    tex_edges: Sequence[object],
    tex_w0: object,
    tex_w1: object,
    group: str = "detail",
) -> None:
    """Extrude a convex 2D polygon (xy, xz, or yz) with per-edge skip support."""
    u = mb.u_per_ft
    snap = mb.world_snap_u if group in ("world", "clip") else mb.detail_snap_u
    aw0, aw1 = sorted((snap_val(w0_ft * u, snap), snap_val(w1_ft * u, snap)))
    if aw1 - aw0 < 0.25 or len(pts_2d_ft) < 3:
        return
    poly = [(snap_val(a * u, snap), snap_val(b * u, snap)) for a, b in pts_2d_ft]
    n = len(poly)
    area2 = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    ccw_sign = 1.0 if area2 >= 0.0 else -1.0

    def _pt(pa: float, pb: float, pw: float) -> Tuple[float, float, float]:
        if plane == "xy":
            return (pa, pb, pw)
        if plane == "xz":
            return (pa, pw, pb)
        return (pw, pa, pb)

    def _n2d(na: float, nb: float) -> Tuple[float, float, float]:
        if plane == "xy":
            return (na, nb, 0.0)
        if plane == "xz":
            return (na, 0.0, nb)
        return (0.0, na, nb)

    n_w0, n_w1 = {
        "xy": ((0.0, 0.0, -1.0), (0.0, 0.0, 1.0)),
        "xz": ((0.0, -1.0, 0.0), (0.0, 1.0, 0.0)),
        "yz": ((-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
    }[plane]
    plane_defs: List[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], object]] = [
        ([_pt(a, b, aw0) for a, b in poly], n_w0, tex_w0),
        ([_pt(a, b, aw1) for a, b in poly], n_w1, tex_w1),
    ]
    for i in range(n):
        a0, b0 = poly[i]
        a1, b1 = poly[(i + 1) % n]
        da, db = a1 - a0, b1 - b0
        L = math.hypot(da, db)
        if L < 0.25:
            continue
        out = _n2d(ccw_sign * db / L, -ccw_sign * da / L)
        plane_defs.append(
            ([_pt(a0, b0, aw0), _pt(a1, b1, aw0), _pt(a1, b1, aw1), _pt(a0, b0, aw1)], out, tex_edges[i])
        )
    mb._emit_brush(plane_defs, group=group)


def _ne_pt(s: float, d: float, z: float) -> Tuple[float, float, float]:
    """Map local (s along SE facade, d outward NE, z up) to world feet."""
    cx, cy = NE_CENTER_FT
    return (
        cx + s * NE_U[0] + d * NE_N[0],
        cy + s * NE_U[1] + d * NE_N[1],
        z,
    )


def _ne_vec(vs: float, vd: float, vz: float) -> Tuple[float, float, float]:
    return (
        vs * NE_U[0] + vd * NE_N[0],
        vs * NE_U[1] + vd * NE_N[1],
        vz,
    )


def _ne_box(
    mb: MapBuilder,
    s0: float,
    s1: float,
    d0: float,
    d1: float,
    z0: float,
    z1: float,
    tex: object,
    faces: Optional[Dict[str, object]] = None,
    group: str = "detail",
) -> None:
    """Emit a 45-degree rotated box in the NE Portico frame (s, d, z)."""
    p00 = (_ne_pt(s0, d0, z0)[:2])
    p10 = (_ne_pt(s1, d0, z0)[:2])
    p11 = (_ne_pt(s1, d1, z0)[:2])
    p01 = (_ne_pt(s0, d1, z0)[:2])
    ov = faces or {}
    if ov:
        pts = [p00, p10, p11, p01]
        b0 = [(x, y, z0) for x, y in pts]
        b1 = [(x, y, z1) for x, y in pts]
        plane_defs = [
            ([b0[0], b0[3], b1[3], b1[0]], _ne_vec(-1.0, 0.0, 0.0), ov.get("w", tex)),
            ([b0[1], b0[2], b1[2], b1[1]], _ne_vec(1.0, 0.0, 0.0), ov.get("e", tex)),
            ([b0[0], b0[1], b1[1], b1[0]], _ne_vec(0.0, -1.0, 0.0), ov.get("s", tex)),
            ([b0[3], b0[2], b1[2], b1[3]], _ne_vec(0.0, 1.0, 0.0), ov.get("n", tex)),
            ([b0[0], b0[1], b0[2], b0[3]], (0.0, 0.0, -1.0), ov.get("b", tex)),
            ([b1[0], b1[3], b1[2], b1[1]], (0.0, 0.0, 1.0), ov.get("t", tex)),
        ]
        _emit_convex_ft(mb, plane_defs, group=group)
    else:
        mb.prism_ft([p00, p10, p11, p01], z0, z1, tex_side=tex, tex_top=tex, tex_bot="skip", group=group)


def _curved_canopy(
    mb: MapBuilder,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z_eave: float,
    z_crown: float,
    attach_side: str,
    tex: object = TEX_DARK,
    skip_end: Optional[str] = None,
) -> None:
    """Build a crisp convex 2-slope arched dark metal awning over an exterior doorway."""
    t = 0.32
    mid_z = z_eave + 0.65 * (z_crown - z_eave)
    sb_faces = {skip_end: "skip"} if skip_end else None
    if attach_side in ("s", "n"):
        plane, lo, hi, ext0, ext1, low_dir, high_dir = "yz", y0, y1, x0, x1, "s", "n"
        mb.detail_box_ft(x0, y0, z_eave - 0.35, x0 + 0.35, y1, z_eave + 0.15, tex, faces=sb_faces)
        mb.detail_box_ft(x1 - 0.35, y0, z_eave - 0.35, x1, y1, z_eave + 0.15, tex, faces=sb_faces)
    else:
        plane, lo, hi, ext0, ext1, low_dir, high_dir = "xz", x0, x1, y0, y1, "w", "e"
        mb.detail_box_ft(x0, y0, z_eave - 0.35, x1, y0 + 0.35, z_eave + 0.15, tex, faces=sb_faces)
        mb.detail_box_ft(x0, y1 - 0.35, z_eave - 0.35, x1, y1, z_eave + 0.15, tex, faces=sb_faces)

    mid = 0.5 * (lo + hi)
    if attach_side in ("n", "e"):
        za, zb = z_eave, z_crown
    else:
        za, zb = z_crown, z_eave
    seg_a = [(lo, za), (mid, mid_z), (mid, mid_z + t), (lo, za + t)]
    seg_b = [(mid, mid_z), (hi, zb), (hi, zb + t), (mid, mid_z + t)]
    end_a = "skip" if skip_end == low_dir else tex
    end_b = "skip" if skip_end == high_dir else tex
    _extrude_poly_skip_ft(mb, seg_a, plane, ext0, ext1, [tex, "skip", tex, end_a], tex, tex)
    _extrude_poly_skip_ft(mb, seg_b, plane, ext0, ext1, [tex, end_b, tex, "skip"], tex, tex)


def _conical_wedges_ft(
    mb: MapBuilder,
    cx: float,
    cy: float,
    r_outer: float,
    r_top: float,
    z0: float,
    z_eave_h: float,
    z_top: float,
    sides: int,
    tex_slope: object,
    tex_rim: object,
    angle_ofs_deg: float = 15.0,
    tex_bot: Optional[object] = None,
) -> None:
    """Build a watertight multi-sided conical shingle roof using N convex 6-plane radial wedges."""
    z_shoulder = z0 + z_eave_h
    bot_mat = tex_rim if tex_bot is None else tex_bot
    for i in range(sides):
        a0 = math.radians(angle_ofs_deg + 360.0 * i / sides)
        a1 = math.radians(angle_ofs_deg + 360.0 * (i + 1) / sides)
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)

        bo0 = (cx + r_outer * c0, cy + r_outer * s0, z0)
        bo1 = (cx + r_outer * c1, cy + r_outer * s1, z0)
        so0 = (cx + r_outer * c0, cy + r_outer * s0, z_shoulder)
        so1 = (cx + r_outer * c1, cy + r_outer * s1, z_shoulder)

        bi0 = (cx + r_top * c0, cy + r_top * s0, z0)
        bi1 = (cx + r_top * c1, cy + r_top * s1, z0)
        ti0 = (cx + r_top * c0, cy + r_top * s0, z_top)
        ti1 = (cx + r_top * c1, cy + r_top * s1, z_top)

        amid = 0.5 * (a0 + a1)
        out_rad = (math.cos(amid), math.sin(amid), 0.0)
        in_rad = (-out_rad[0], -out_rad[1], 0.0)
        side0_out = (math.sin(a0), -math.cos(a0), 0.0)
        side1_out = (-math.sin(a1), math.cos(a1), 0.0)
        slope_n = _vcross(_vsub(so1, so0), _vsub(ti0, so0))
        if slope_n[2] < 0.0:
            slope_n = (-slope_n[0], -slope_n[1], -slope_n[2])

        plane_defs = [
            ([bo0, bo1, so1, so0], out_rad, tex_rim),
            ([bi0, ti0, ti1, bi1], in_rad, "skip"),
            ([bi0, bo0, so0, ti0], side0_out, "skip"),
            ([bo1, bi1, ti1, so1], side1_out, "skip"),
            ([bi0, bi1, bo1, bo0], (0.0, 0.0, -1.0), bot_mat),
            ([so0, so1, ti1, ti0], _vnorm(slope_n), tex_slope),
        ]
        _emit_convex_ft(mb, plane_defs, group="detail")


# ---------------------------------------------------------------------------
# A. Lot Pavement, Driveways, North Patio & NE 45-deg Flagstone Courtyard
# ---------------------------------------------------------------------------

def _asph_slab(mb: MapBuilder, x0: float, y0: float, x1: float, y1: float) -> None:
    mb.detail_box_ft(x0, y0, Z_GROUND_FT, x1, y1, Z_ROAD_FT, TEX_ASPH, faces={"b": "skip"})


def _curb_ft(
    mb: MapBuilder,
    x0: float,
    y0: float,
    z0: float,
    x1: float,
    y1: float,
    z1: float,
    tex: object,
    extra_skip: Optional[Dict[str, object]] = None,
) -> None:
    """Emit a Hull-1-checked detail curb/pad with hidden ground underside culled to skip."""
    rise_u = abs(z1 - z0) * mb.u_per_ft
    if rise_u > 18.0 + 1e-4:
        raise ValueError(f"Curb height {rise_u:.1f}u exceeds Hull-1 step limit (18u)")
    mb._curbs.append({"rise_u": rise_u})
    faces: Dict[str, object] = {"b": "skip"}
    if extra_skip:
        faces.update(extra_skip)
    mb.detail_box_ft(x0, y0, z0, x1, y1, z1, tex, faces=faces)


def _build_lot_pavement_and_plaza(mb: MapBuilder) -> None:
    """Tile non-overlapping parking asphalt and the NE 45-deg flagstone courtyard."""
    # Disjoint lot asphalt sheets strictly outside CASINO_POLY_FT, Delaware St & Trinity Ave
    _asph_slab(mb, -157.5, 89.7, 167.0, 304.2)    # North main parking lot
    _asph_slab(mb, -54.1, 77.6, -43.4, 89.7)      # NW pocket west of mech bump
    _asph_slab(mb, -157.5, -125.0, -54.1, 89.7)   # West corridor north of Trinity Ave
    _asph_slab(mb, -54.1, -125.0, 54.0, -71.7)    # South building frontage north of -125
    _asph_slab(mb, -54.1, -71.7, -20.1, -68.4)    # SW service alcove under overhang
    _asph_slab(mb, -102.0, -270.9, 167.0, -125.0) # South main lot (east of Delaware St)
    _asph_slab(mb, 54.0, -125.0, 167.0, -71.7)    # SE drive aisle & south bay
    _asph_slab(mb, 102.2, -71.7, 167.0, -10.0)    # East drive south of drop-off
    _asph_slab(mb, 118.0, -10.0, 167.0, 89.7)     # East drive east of drop-off bay

    # SE corner asphalt collar south of Rotunda (clean rectangle up to Rotunda R=23.1)
    _asph_slab(mb, 54.0, -71.7, 102.2, -48.5)
    _asph_slab(mb, 92.0, -48.5, 102.2, -36.0)

    # Flush Driveway Aprons joining gw_streets S Union Ave curb cuts (y=154..176, y=-98..-76)
    _asph_slab(mb, 167.0, 154.0, 172.0, 176.0)
    _asph_slab(mb, 167.0, -98.0, 172.0, -76.0)

    # Concrete Frontage Sidewalk Margin (x=167..172, Z=0.50 flush with gw_streets sidewalk)
    for fy0, fy1 in ((-270.9, -98.0), (-76.0, 154.0), (176.0, 304.2)):
        _curb_ft(mb, 167.0, fy0, Z_GROUND_FT, 172.0, fy1, Z_WALK_FT, TEX_CONC)

    # Arched / Linear Concrete Drop-Off Driveway beside Courtyard (x=102.2..118.0, y=-10..89.7)
    mb.detail_box_ft(
        102.2, -10.0, Z_GROUND_FT, 118.0, 89.7, Z_ROAD_FT,
        TEX_CONCSLAB, faces={"b": "skip"},
    )
    # Red painted fire-lane drop-off curb along eastern edge of flagstone plaza
    _curb_ft(mb, 101.4, -10.0, Z_GROUND_FT, 102.2, 89.7, Z_WALK_FT, TEX_CURBRED, extra_skip={"w": "skip"})

    # North Lot Exit Patio strictly outside gw_casino_int North Poker floor slabs (#71 zero overlap!)
    _curb_ft(mb, 7.35, 71.10, Z_GROUND_FT, 43.0, 89.7, Z_WALK_FT, TEX_CONC, extra_skip={"e": "skip"})
    _curb_ft(mb, 42.02, 70.50, Z_GROUND_FT, 43.0, 71.10, Z_WALK_FT, TEX_CONC, extra_skip={"n": "skip", "e": "skip"})

    # NE 45-deg Stamped Flagstone Courtyard Plaza flush at Z_WALK_FT=0.50 outside doorway x+y=50
    _curb_ft(mb, 43.0, 10.0, Z_GROUND_FT, 101.4, 89.7, Z_WALK_FT, TEX_FLAG, extra_skip={"e": "skip"})
    # Diagonal entrance apron meeting (43,7)->(62,-12) storefront threshold with zero overlap
    _extrude_poly_skip_ft(
        mb,
        [(43.0, 7.0), (62.0, -12.0), (62.0, 10.0), (43.0, 10.0)],
        "xy", Z_GROUND_FT, Z_WALK_FT, [TEX_CURB, "skip", "skip", TEX_CURB], "skip", TEX_FLAG, group="detail",
    )
    # Courtyard south fan north of Rotunda shoulder (62..-12 to 101.4..-2.2)
    _curb_ft(mb, 62.0, -2.2, Z_GROUND_FT, 101.4, 10.0, Z_WALK_FT, TEX_FLAG, extra_skip={"e": "skip", "w": "skip", "n": "skip"})
    mb.poly_prism_ft(
        [(62.0, -12.0), (65.8, -8.4), (71.0, -4.6), (80.0, -2.2), (62.0, -2.2)],
        Z_GROUND_FT, Z_WALK_FT, TEX_CURB, tex_top=TEX_FLAG, tex_bot="skip", group="detail",
    )
    mb.poly_prism_ft(
        [(80.0, -2.2), (87.6, -3.3), (96.7, -8.9), (97.3, -10.0), (101.4, -10.0), (101.4, -2.2)],
        Z_GROUND_FT, Z_WALK_FT, TEX_CURB, tex_top=TEX_FLAG, tex_bot="skip", group="detail",
    )

    # SW Service Exit concrete stoop ramp flush at Z_WALK_FT=0.50 (doorway y=-68.4, x=-42..-34)
    _curb_ft(mb, -44.0, -72.0, Z_ROAD_FT, -32.0, -68.4, Z_WALK_FT, TEX_CONC)
    mb.slab_ramp_yft(-44.0, -32.0, -74.0, -72.0, Z_ROAD_FT, Z_WALK_FT, TEX_CONC, thick_ft=0.25, group="detail")

    # South Center Exit concrete stoop flush at Z_WALK_FT=0.50 (doorway y=-71.6, x=24..34)
    _curb_ft(mb, 22.0, -76.0, Z_ROAD_FT, 36.0, -71.7, Z_WALK_FT, TEX_CONC)
    mb.slab_ramp_yft(22.0, 36.0, -78.0, -76.0, Z_ROAD_FT, Z_WALK_FT, TEX_CONC, thick_ft=0.25, group="detail")


# ---------------------------------------------------------------------------
# B. Casino Roof Superstructure & Canopies
# ---------------------------------------------------------------------------

def _hvac_rtu(mb: MapBuilder, cx: float, cy: float, z0: float, sx: float = 5.4, sy: float = 6.2, h: float = 3.6) -> None:
    """Emit a commercial boxy rooftop HVAC RTU with louvered face and supply hood."""
    x0, x1 = cx - 0.5 * sx, cx + 0.5 * sx
    y0, y1 = cy - 0.5 * sy, cy + 0.5 * sy
    mb.detail_box_ft(x0, y0, z0, x1, y1, z0 + h, Fit("gwc_hvac"), faces={"t": TEX_GALV, "b": "skip"})
    mb.detail_box_ft(x0 + 0.4, y0 + 0.4, z0 + h, x1 - 0.4, y1 - 0.4, z0 + h + 0.5, TEX_DARK, faces={"b": "skip"})


def _emit_miter_parapet_strip(
    mb: MapBuilder,
    pts: Sequence[Tuple[float, float]],
    off_out: float,
    off_in: float,
    z0: float,
    z1: float,
    tex_side: object,
    tex_top: object,
    tex_bot: object,
) -> None:
    """Emit watertight mitered parapet quads along a CW perimeter polyline."""
    normals: List[Tuple[float, float]] = []
    for i in range(len(pts) - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        m = math.hypot(dx, dy)
        normals.append((-dy / m, dx / m) if m > 1e-6 else (0.0, 1.0))

    def _offset_ring(d: float) -> List[Tuple[float, float]]:
        ring: List[Tuple[float, float]] = []
        for idx, (px, py) in enumerate(pts):
            if idx == 0:
                nx, ny = normals[0]
            elif idx == len(pts) - 1:
                nx, ny = normals[-1]
            else:
                na, nb = normals[idx - 1], normals[idx]
                denom = 1.0 + na[0] * nb[0] + na[1] * nb[1]
                if denom > 0.15:
                    nx, ny = (na[0] + nb[0]) / denom, (na[1] + nb[1]) / denom
                else:
                    nx, ny = nb
            ring.append((px + d * nx, py + d * ny))
        return ring

    outer = _offset_ring(off_out)
    inner = _offset_ring(off_in)
    n_segs = len(pts) - 1
    for i in range(n_segs):
        t1 = "skip" if i < n_segs - 1 else tex_side
        t3 = "skip" if i > 0 else tex_side
        _extrude_poly_skip_ft(
            mb,
            [outer[i], outer[i + 1], inner[i + 1], inner[i]],
            "xy", z0, z1, [tex_side, t1, tex_side, t3], tex_bot, tex_top, group="detail",
        )


def _build_roof_superstructure(mb: MapBuilder) -> None:
    """Build all Casino roofs strictly above gw_casino_int exterior walls."""
    z_top = Z_WALL_TOP_FT  # 16.0 ft
    z_tpo = z_top - 0.12   # 15.88 ft (seals cleanly into lowered 15.92 interior decks -> 0 cracks!)

    # 1. West BOH Wing Flat TPO Roof (convex quads inset strictly inside walls/parapets -> 0 Z-fighting!)
    mb.prism_ft(
        [(-52.45, -67.5), (-17.0, -67.5), (-17.0, 76.7), (-53.15, 76.7)],
        z_tpo, z_top + 0.25, TEX_DARK, tex_top=TEX_TPO, tex_bot="skip", group="detail",
    )
    mb.prism_ft(
        [(-42.4, 76.7), (5.2, 76.7), (4.5, 88.8), (-42.4, 87.4)],
        z_tpo, z_top + 0.25, TEX_DARK, tex_top=TEX_TPO, tex_bot="skip", group="detail",
    )
    mb.detail_box_ft(-17.0, 70.6, z_tpo, 6.2, 76.7, z_top + 0.25, TEX_TPO, faces={"b": "skip", "w": "skip"})

    # Continuous CW perimeter for West/NW BOH matching gw_casino_int PERIM_PTS[23,24,0,1,2,3,4]
    west_boh_ring = [
        (-19.33, -68.77), (-53.35, -68.37), (-54.07, 77.17),
        (-43.23, 77.61), (-43.35, 88.31), (5.42, 89.70), (7.30, 71.11),
    ]
    # Unify blind West BOH rear wall (v24->v00) cleanly in cream stucco + proud overlapping parapet (z=15.65..17.55)
    _emit_miter_parapet_strip(
        mb, [(-53.35, -68.37), (-54.07, 77.17)],
        off_out=0.12, off_in=0.0, z0=Z_ROAD_FT, z1=15.68,
        tex_side=TEX_CRMSTUC, tex_top="skip", tex_bot="skip",
    )
    _emit_miter_parapet_strip(
        mb, west_boh_ring,
        off_out=0.16, off_in=-0.90, z0=15.65, z1=17.55,
        tex_side=TEX_CRMSTUC, tex_top=TEX_DARK, tex_bot=TEX_CRMSTUC,
    )
    # West rear BOH electrical / mechanical utility enclosures flush against stucco service wall
    mb.detail_box_ft(-54.45, -18.0, 3.8, -53.85, -11.0, 8.2, TEX_GALV, faces={"t": TEX_DARK, "e": "skip"})
    mb.detail_box_ft(-54.40, -6.0, 4.2, -53.85, 0.0, 7.6, TEX_DARK, faces={"e": "skip"})

    # 6 Boxy HVAC RTUs + silver galvanized trunk ductwork on West BOH TPO roof
    rtu_coords = [
        (-42.0, -40.0), (-29.0, -40.0),
        (-42.0, -2.0),  (-29.0, -2.0),
        (-42.0, 38.0),  (-26.0, 82.0),
    ]
    for rx, ry in rtu_coords:
        _hvac_rtu(mb, rx, ry, z_top + 0.25)
    # Trunk & branch galvanized ducts (seated on TPO with undersides culled to skip)
    mb.detail_box_ft(-36.5, -52.0, z_top + 0.25, -34.5, 76.0, z_top + 2.2, TEX_DUCT, faces={"b": "skip"})
    for by in (-40.0, -2.0, 38.0):
        mb.detail_box_ft(-40.0, by - 0.8, z_top + 0.25, -27.0, by + 0.8, z_top + 1.8, TEX_DUCT, faces={"b": "skip"})
    # SW rear curved dark canopy over SW Service Exit (y=-68.4, x=-42..-34, z=0.5..9.5)
    _curved_canopy(mb, -43.5, -32.5, -73.4, -68.4, 9.8, 12.2, attach_side="s", tex=TEX_DARK, skip_end="n")
    mb.light_ft(-38.0, -70.6, 9.4, light=170.0, color=(255, 224, 178), wait=0.7)

    # 2. SE Flat Stone Wing Roof (TPO strictly inset inside parapets -> 0 Z-fighting at x=20/54.6/y=-71.7!)
    mb.prism_ft(
        [(20.95, -70.75), (52.75, -70.75), (53.85, -35.15), (20.95, -35.15)],
        z_tpo, z_top + 0.25, TEX_DARK, tex_top=TEX_TPO, tex_bot="skip", group="detail",
    )
    _emit_miter_parapet_strip(
        mb, [(20.12, -71.56), (53.62, -71.66), (54.76, -35.13)],
        off_out=0.08, off_in=-0.88, z0=15.80, z1=17.60,
        tex_side=TEX_STONE, tex_top=TEX_DARK, tex_bot=TEX_STONE,
    )
    mb.detail_box_ft(20.12, -70.75, z_tpo, 20.95, -35.15, 17.60, TEX_STONE, faces={"t": TEX_DARK, "b": "skip", "s": "skip"})
    _hvac_rtu(mb, 31.0, -56.0, z_top + 0.25, sx=4.8, sy=5.2, h=3.2)
    _hvac_rtu(mb, 44.0, -49.0, z_top + 0.25, sx=4.8, sy=5.2, h=3.2)
    mb.detail_box_ft(31.0, -51.0, z_top + 0.25, 44.0, -49.5, z_top + 1.6, TEX_DUCT, faces={"b": "skip"})
    # South Center Exit curved dark canopy (y=-71.6, x=24..34, z=0.5..9.5)
    _curved_canopy(mb, 22.0, 36.0, -77.2, -71.7, 9.8, 12.6, attach_side="n", tex=TEX_DARK)
    mb.light_ft(29.0, -74.0, 9.4, light=150.0, color=(255, 224, 178), wait=0.7)
    # SE wing dark arched accent canopy near SE corner
    _curved_canopy(mb, 45.0, 54.5, -75.8, -71.7, 9.8, 12.2, attach_side="n", tex=TEX_DARK)

    # Watertight cricket deck behind NE 45-deg lobby collar & Rotunda shoulder (2 convex quads skipping internal seam)
    _extrude_poly_skip_ft(
        mb,
        [(43.2, -35.1), (54.4, -35.1), (60.1, -14.2), (43.2, -14.2)],
        "xy", z_tpo, z_top + 0.35, [TEX_DARK, TEX_DARK, "skip", TEX_DARK], "skip", TEX_TPO, group="detail",
    )
    _extrude_poly_skip_ft(
        mb,
        [(43.2, -14.2), (60.1, -14.2), (61.3, -12.0), (43.2, 6.4)],
        "xy", z_tpo, z_top + 0.35, ["skip", TEX_DARK, TEX_DARK, TEX_DARK], "skip", TEX_TPO, group="detail",
    )
    # Hidden attic seal slabs strictly inside spine walls (15.88..16.00) preventing cracks if interior deck is 15.92
    mb.detail_box_ft(-17.0, -35.1, z_tpo, 41.8, 70.0, z_top, TEX_DARK, faces={"b": "skip", "t": "skip", "w": "skip"})
    mb.detail_box_ft(-17.0, -70.4, z_tpo, 19.8, -35.1, z_top, TEX_DARK, faces={"b": "skip", "t": "skip", "n": "skip"})

    # 3. Center Pitched Spine Roof (~30 deg terracotta shingle) + Dark-Brown Clerestory Wood Gable
    # Lower pitched shingle slopes over (x=-17.0..43.2, y=-35.1..70.5) & south west-half (-17..20, y=-71.7..-35.1)
    # Split symmetrically around ridge axis x = 13.0 (west eave -17.0 at z=16.0, east eave 43.2 at z=16.0)
    # North main pitched roof: y = -35.1 .. 70.5
    spine_pts_n = [
        (-17.0, z_top),
        (13.0, 25.4),
        (43.2, z_top),
    ]
    mb.prism_xz_ft(spine_pts_n, -35.1, 70.5, TEX_SHINGLE, tex_end=TEX_CRMSTUC, group="detail")
    # Overhanging eastern shingle eave outside x=43.2 (y=7.0..70.5) cleanly above walls
    mb.prism_xz_ft(
        [(43.2, z_top - 0.8), (43.2, z_top + 0.5), (45.2, z_top - 0.6), (45.2, z_top - 1.2)],
        7.0, 71.2, TEX_SHINGLE, tex_end=TEX_DARK, group="detail",
    )
    # Overhanging western valley flashing & north eave over North Lot Exit (y=70.58..72.2)
    mb.detail_box_ft(6.3, 70.58, z_top - 1.2, 45.2, 72.2, z_top + 0.4, TEX_SHINGLE)

    # South wing west pitched span (x=-17.0..20.0, y=-71.7..-35.1)
    spine_pts_s = [
        (-17.0, z_top),
        (2.0, 23.8),
        (20.0, z_top),
    ]
    mb.prism_xz_ft(spine_pts_s, -71.7, -35.1, TEX_SHINGLE, tex_end=TEX_CRMSTUC, group="detail")
    # South eave overhang west of SE wing (x=-17.0..20.0, y=-73.2..-71.7)
    mb.detail_box_ft(-17.0, -73.2, z_top - 1.0, 20.0, -71.7, z_top + 0.2, TEX_SHINGLE)

    # Elevated Dark-Brown Vertical Wood Board-and-Batten Clerestory Monitor Gable (gwc_batten)
    # Rises cleanly above main terracotta roof: x = -5.0 .. 31.0 (36 ft wide), y = -58.0 .. 62.0, apex ~30.2 ft
    cx0, cx1, cx_mid = -5.0, 31.0, 13.0
    cy0, cy1 = -58.0, 62.0
    cz_base = 21.5
    cz_eave = 25.4
    cz_apex = 30.2
    # Vertical board-and-batten monitor walls + glazed clerestory strips along W/E flanks (strictly between N/S gable ends)
    for sx0, sx1 in ((cx0, cx0 + 0.9), (cx1 - 0.9, cx1)):
        mb.detail_box_ft(sx0, cy0 + 0.9, cz_base, sx1, cy1 - 0.9, cz_eave - 2.2, TEX_BATTEN, faces={"b": "skip", "t": "skip", "s": "skip", "n": "skip"})
        mb.detail_box_ft(sx0, cy0 + 0.9, cz_eave - 0.9, sx1, cy1 - 0.9, cz_eave, TEX_WHITE, faces={"b": "skip", "t": "skip", "s": "skip", "n": "skip"})
        # Recessed clerestory window panes divided into 4 bays
        for by in (-52.0, -24.0, 4.0, 32.0):
            mb.detail_box_ft(sx0, by, cz_eave - 2.2, sx1, by + 22.0, cz_eave - 0.9, TEX_GOLDWIN, faces={"b": "skip", "t": "skip", "s": "skip", "n": "skip"})
            mb.detail_box_ft(sx0, by + 22.0, cz_eave - 2.2, sx1, by + 28.0 if by < 32.0 else cy1 - 0.9, cz_eave - 0.9, TEX_BATTEN, faces={"b": "skip", "t": "skip", "s": "skip", "n": "skip"})
        mb.detail_box_ft(sx0, cy0 + 0.9, cz_eave - 2.2, sx1, -52.0, cz_eave - 0.9, TEX_BATTEN, faces={"b": "skip", "t": "skip", "s": "skip", "n": "skip"})
    # Dark wood triangular N & S clerestory gable ends (gwc_batten) + crisp white bargeboard fascia
    gable_tri = [(cx0, cz_base), (cx0, cz_eave), (cx_mid, cz_apex), (cx1, cz_eave), (cx1, cz_base)]
    mb.prism_xz_ft(gable_tri, cy0, cy0 + 0.9, TEX_BATTEN, tex_end=TEX_BATTEN, group="detail")
    mb.prism_xz_ft(gable_tri, cy1 - 0.9, cy1, TEX_BATTEN, tex_end=TEX_BATTEN, group="detail")
    # Crisp tan/white gable fascia bargeboards framing S and N gable peaks
    mb.prism_xz_ft([(cx0 - 1.2, cz_eave - 0.4), (cx_mid, cz_apex + 0.4), (cx_mid, cz_apex + 0.9), (cx0 - 1.2, cz_eave + 0.2)], cy0 - 0.6, cy1 + 0.6, TEX_WHITE, tex_end=TEX_WHITE, group="detail")
    mb.prism_xz_ft([(cx_mid, cz_apex + 0.4), (cx1 + 1.2, cz_eave - 0.4), (cx1 + 1.2, cz_eave + 0.2), (cx_mid, cz_apex + 0.9)], cy0 - 0.6, cy1 + 0.6, TEX_WHITE, tex_end=TEX_WHITE, group="detail")
    # Upper terracotta shingle clerestory gable roof capping apex z=30.8 ft
    upper_roof = [(cx0 - 1.2, cz_eave + 0.1), (cx_mid, cz_apex + 0.8), (cx1 + 1.2, cz_eave + 0.1)]
    mb.prism_xz_ft(upper_roof, cy0 - 0.5, cy1 + 0.5, TEX_SHINGLE, tex_end=TEX_BATTEN, group="detail")

    # 4. East 12-Sided Conical Rotunda Roof (center=(78.9,-25.5), R=23.1, walls z=0.5..13.0)
    rcx, rcy = CASINO_ROTUNDA_CENTER_FT
    r_cone = CASINO_ROTUNDA_R_FT + 1.5  # Overhanging eave 24.6 ft
    # Overhanging cream fascia collar ring strictly at z=12.6..13.4 ft
    mb.cyl_ft(rcx, rcy, r_cone, Z_ROTUNDA_TOP_FT - 0.3, Z_ROTUNDA_TOP_FT + 0.35, sides=12, tex_side=TEX_CRMSTUC, tex_top=TEX_DARK, tex_bot=TEX_DARK, group="detail")
    # 12 radial watertight conical terracotta shingle wedges rising from z=13.2 to 27.2 ft
    _conical_wedges_ft(
        mb, rcx, rcy,
        r_outer=r_cone, r_top=1.0,
        z0=Z_ROTUNDA_TOP_FT + 0.2, z_eave_h=0.45, z_top=27.2,
        sides=12, tex_slope=TEX_SHINGLE, tex_rim=TEX_DARK, angle_ofs_deg=15.0, tex_bot="skip",
    )
    # Finial cap & bronze spire tip at Rotunda apex (z=26.9..29.4 ft)
    mb.cyl_ft(rcx, rcy, 1.25, 26.8, 27.6, sides=8, tex_side=TEX_DARK, tex_top=TEX_DARK, group="detail")
    mb.cyl_ft(rcx, rcy, 0.32, 27.6, 29.5, sides=8, tex_side=TEX_BEAM, tex_top=TEX_DARK, group="detail")

    # 5. 45-deg NE Portico Gable, 4 Clerestory Glass Transoms & Angled US Flagpoles
    # Flanking piers at s = +-11.2, d = 9.0 (leaves 20.0 ft clear passage outside 12 ft doors!)
    for s_c in (-11.2, 11.2):
        _ne_box(mb, s_c - 1.2, s_c + 1.2, 7.8, 10.2, Z_WALK_FT, 3.6, TEX_STONE, faces={"b": "skip"})
        _ne_box(mb, s_c - 1.0, s_c + 1.0, 8.0, 10.0, 3.6, 9.9, TEX_CRMSTUC, faces={"b": "skip", "t": "skip"})

    # Portico Header Cross-Beam above z=9.5 ft doorway (z=9.9..11.2) + Side Beams (non-overlapping)
    _ne_box(mb, -13.4, 13.4, 7.6, 10.6, 9.9, 11.2, TEX_BEAM, faces={"b": TEX_WOOD, "t": TEX_DARK})
    _ne_box(mb, -12.6, -10.2, 0.2, 7.55, 9.9, 11.15, TEX_BEAM, faces={"b": TEX_WOOD, "t": TEX_DARK})
    _ne_box(mb, 10.2, 12.6, 0.2, 7.55, 9.9, 11.15, TEX_BEAM, faces={"b": TEX_WOOD, "t": TEX_DARK})

    # Rear gable infill cleanly ABOVE z=16.0 storefront top (z=16.0..18.8 at d=0.2..0.8)
    rear_g = [
        _ne_pt(-6.0, 0.2, 16.0), _ne_pt(6.0, 0.2, 16.0), _ne_pt(0.0, 0.2, 19.0),
        _ne_pt(-6.0, 0.8, 16.0), _ne_pt(6.0, 0.8, 16.0), _ne_pt(0.0, 0.8, 19.0),
    ]
    _emit_convex_ft(
        mb,
        [
            ([rear_g[0], rear_g[1], rear_g[2]], _ne_vec(0.0, -1.0, 0.0), TEX_BATTEN),
            ([rear_g[3], rear_g[5], rear_g[4]], _ne_vec(0.0, 1.0, 0.0), TEX_BATTEN),
            ([rear_g[0], rear_g[3], rear_g[4], rear_g[1]], (0.0, 0.0, -1.0), TEX_DARK),
            ([rear_g[0], rear_g[2], rear_g[5], rear_g[3]], _ne_vec(-0.6, 0.0, 1.0), TEX_BATTEN),
            ([rear_g[1], rear_g[4], rear_g[5], rear_g[2]], _ne_vec(0.6, 0.0, 1.0), TEX_BATTEN),
        ],
        group="detail",
    )

    # 4 Trapezoidal Clerestory Glass Transom Panels inside front NE gable (d=8.7..9.1, z=11.2..18.4)
    # Gable slope line from (s=+-13.4, z=10.8) to (s=0.0, z=18.8): z(s) = 18.8 - 0.597 * |s|
    def _gable_z(s_val: float) -> float:
        return 18.8 - 0.597 * abs(s_val)

    panel_spans = [(-10.2, -5.3), (-5.0, -0.2), (0.2, 5.0), (5.3, 10.2)]
    for ps0, ps1 in panel_spans:
        z_l = max(11.6, _gable_z(ps0) - 0.45)
        z_r = max(11.6, _gable_z(ps1) - 0.45)
        f0 = [_ne_pt(ps0, 8.7, 11.2), _ne_pt(ps1, 8.7, 11.2), _ne_pt(ps1, 8.7, z_r), _ne_pt(ps0, 8.7, z_l)]
        f1 = [_ne_pt(ps0, 9.1, 11.2), _ne_pt(ps1, 9.1, 11.2), _ne_pt(ps1, 9.1, z_r), _ne_pt(ps0, 9.1, z_l)]
        _emit_convex_ft(
            mb,
            [
                ([f0[0], f0[1], f0[2], f0[3]], _ne_vec(0.0, -1.0, 0.0), TEX_GLASS),
                ([f1[0], f1[3], f1[2], f1[1]], _ne_vec(0.0, 1.0, 0.0), TEX_GLASS),
                ([f0[0], f1[0], f1[1], f0[1]], (0.0, 0.0, -1.0), "skip"),
                ([f0[3], f0[2], f1[2], f1[3]], (0.0, 0.0, 1.0), TEX_DARK),
                ([f0[0], f0[3], f1[3], f1[0]], _ne_vec(-1.0, 0.0, 0.0), "skip"),
                ([f0[1], f1[1], f1[2], f0[2]], _ne_vec(1.0, 0.0, 0.0), "skip"),
            ],
            group="detail",
        )
    # 3 dark bronze mullions + dark wood gable side triangles flanking glass panels
    for ms, mh in ((-5.15, 15.6), (0.0, 18.6), (5.15, 15.6)):
        _ne_box(mb, ms - 0.18, ms + 0.18, 8.6, 9.3, 11.2, mh, TEX_DARK, faces={"b": "skip", "t": "skip"})
    for side_sgn in (-1.0, 1.0):
        s_out, s_in = side_sgn * 13.0, side_sgn * 10.2
        z_in = _gable_z(s_in) - 0.35
        ga = [_ne_pt(min(s_out, s_in), 8.6, 11.2), _ne_pt(max(s_out, s_in), 8.6, 11.2), _ne_pt(s_in, 8.6, z_in)]
        gb = [_ne_pt(min(s_out, s_in), 9.2, 11.2), _ne_pt(max(s_out, s_in), 9.2, 11.2), _ne_pt(s_in, 9.2, z_in)]
        _emit_convex_ft(
            mb,
            [
                ([ga[0], ga[1], ga[2]], _ne_vec(0.0, -1.0, 0.0), TEX_BATTEN),
                ([gb[0], gb[2], gb[1]], _ne_vec(0.0, 1.0, 0.0), TEX_BATTEN),
                ([ga[0], gb[0], gb[1], ga[1]], (0.0, 0.0, -1.0), "skip"),
                ([ga[0], ga[2], gb[2], gb[0]], _ne_vec(-0.6, 0.0, 1.0), TEX_BATTEN),
                ([ga[1], gb[1], gb[2], ga[2]], _ne_vec(0.6, 0.0, 1.0), TEX_BATTEN),
            ],
            group="detail",
        )

    # Portico Terracotta Shingle Sloped Roof Slabs:
    # Keep low eaves strictly outside building (d >= 0.2), ridge cap z>=16 merges back to d=-4.0
    for sgn in (-1.0, 1.0):
        s_eave = sgn * 14.0
        s_mid = 0.0
        d0_eave, d1_eave = 0.2, 11.4
        # Slanted shingle slab (0.65 ft thick)
        sa0 = _ne_pt(min(s_eave, s_mid), d0_eave, 10.5 if s_eave < 0 else 19.0)
        sa1 = _ne_pt(max(s_eave, s_mid), d0_eave, 19.0 if s_eave < 0 else 10.5)
        if sgn < 0:
            p_l, p_r, zl, zr = s_eave, s_mid, 10.6, 19.1
        else:
            p_l, p_r, zl, zr = s_mid, s_eave, 19.1, 10.6
        t_r = 0.70
        c0 = [_ne_pt(p_l, d0_eave, zl), _ne_pt(p_r, d0_eave, zr), _ne_pt(p_r, d0_eave, zr + t_r), _ne_pt(p_l, d0_eave, zl + t_r)]
        c1 = [_ne_pt(p_l, d1_eave, zl), _ne_pt(p_r, d1_eave, zr), _ne_pt(p_r, d1_eave, zr + t_r), _ne_pt(p_l, d1_eave, zl + t_r)]
        n_top = _ne_vec(-0.55 if sgn < 0 else 0.55, 0.0, 1.0)
        n_bot = (-n_top[0], -n_top[1], -n_top[2])
        _emit_convex_ft(
            mb,
            [
                ([c0[0], c0[1], c0[2], c0[3]], _ne_vec(0.0, -1.0, 0.0), TEX_BEAM),
                ([c1[0], c1[3], c1[2], c1[1]], _ne_vec(0.0, 1.0, 0.0), TEX_BEAM),
                ([c0[3], c0[2], c1[2], c1[3]], n_top, TEX_SHINGLE),
                ([c0[0], c1[0], c1[1], c0[1]], n_bot, TEX_WOOD),
                ([c0[0], c0[3], c1[3], c1[0]], _ne_vec(-1.0, 0.0, 0.0), "skip" if sgn > 0 else TEX_BEAM),
                ([c0[1], c1[1], c1[2], c0[2]], _ne_vec(1.0, 0.0, 0.0), "skip" if sgn < 0 else TEX_BEAM),
            ],
            group="detail",
        )
    # High portico ridge extension (z>=16.2) tucking cleanly into main roof spine behind facade
    for sgn in (-1.0, 1.0):
        p_l, p_r, zl, zr = ((-5.0, 0.0, 16.0, 19.1) if sgn < 0 else (0.0, 5.0, 19.1, 16.0))
        c0 = [_ne_pt(p_l, -4.5, zl), _ne_pt(p_r, -4.5, zr), _ne_pt(p_r, -4.5, zr + 0.7), _ne_pt(p_l, -4.5, zl + 0.7)]
        c1 = [_ne_pt(p_l, 0.25, zl), _ne_pt(p_r, 0.25, zr), _ne_pt(p_r, 0.25, zr + 0.7), _ne_pt(p_l, 0.25, zl + 0.7)]
        n_top = _ne_vec(-0.55 if sgn < 0 else 0.55, 0.0, 1.0)
        _emit_convex_ft(
            mb,
            [
                ([c0[0], c0[1], c0[2], c0[3]], _ne_vec(0.0, -1.0, 0.0), TEX_BEAM),
                ([c1[0], c1[3], c1[2], c1[1]], _ne_vec(0.0, 1.0, 0.0), TEX_BEAM),
                ([c0[3], c0[2], c1[2], c1[3]], n_top, TEX_SHINGLE),
                ([c0[0], c1[0], c1[1], c0[1]], (-n_top[0], -n_top[1], -n_top[2]), TEX_WOOD),
                ([c0[0], c0[3], c1[3], c1[0]], _ne_vec(-1.0, 0.0, 0.0), "skip" if sgn > 0 else TEX_BEAM),
                ([c0[1], c1[1], c1[2], c0[2]], _ne_vec(1.0, 0.0, 0.0), "skip" if sgn < 0 else TEX_BEAM),
            ],
            group="detail",
        )

    # 2 Angled US Flagpoles mounted cleanly on NE Portico front fascia brackets (d >= 11.4, clear of roof tiles!)
    for s_flag in (-11.2, 11.2):
        # Fascia bracket collar bolted flush on front roof bargeboard edge (d=11.40..11.75, z=12.30..13.05)
        _ne_box(mb, s_flag - 0.35, s_flag + 0.35, 11.40, 11.75, 12.30, 13.05, TEX_DARK, faces={"s": "skip"})
        # Galvanized flagpole angling strictly forward/upward from bracket (d=11.65, z=12.65 -> d=16.4, z=19.4)
        pole_r = 0.14
        pole_pts0 = [
            _ne_pt(s_flag - pole_r, 11.65 - pole_r, 12.65),
            _ne_pt(s_flag + pole_r, 11.65 - pole_r, 12.65),
            _ne_pt(s_flag + pole_r, 11.65 + pole_r, 12.65),
            _ne_pt(s_flag - pole_r, 11.65 + pole_r, 12.65),
        ]
        pole_pts1 = [
            _ne_pt(s_flag - pole_r, 16.4 - pole_r, 19.4),
            _ne_pt(s_flag + pole_r, 16.4 - pole_r, 19.4),
            _ne_pt(s_flag + pole_r, 16.4 + pole_r, 19.4),
            _ne_pt(s_flag - pole_r, 16.4 + pole_r, 19.4),
        ]
        _emit_convex_ft(
            mb,
            [
                ([pole_pts0[0], pole_pts0[1], pole_pts1[1], pole_pts1[0]], _ne_vec(0.0, -6.75, 4.75), TEX_GALV),
                ([pole_pts0[2], pole_pts0[3], pole_pts1[3], pole_pts1[2]], _ne_vec(0.0, 6.75, -4.75), TEX_GALV),
                ([pole_pts0[0], pole_pts1[0], pole_pts1[3], pole_pts0[3]], _ne_vec(-1.0, 0.0, 0.0), TEX_GALV),
                ([pole_pts0[1], pole_pts0[2], pole_pts1[2], pole_pts1[1]], _ne_vec(1.0, 0.0, 0.0), TEX_GALV),
                ([pole_pts0[0], pole_pts0[3], pole_pts0[2], pole_pts0[1]], _ne_vec(0.0, -4.75, -6.75), "skip"),
                ([pole_pts1[0], pole_pts1[1], pole_pts1[2], pole_pts1[3]], _ne_vec(0.0, 4.75, 6.75), TEX_DARK),
            ],
            group="detail",
        )
        # Hanging alpha-cutout US flag banner projecting NE from upper pole (thinner than pole_r -> 0 Z-fighting!)
        _ne_box(
            mb,
            s_flag - 0.05, s_flag + 0.05,
            12.5, 16.3,
            14.3, 17.5,
            "skip",
            faces={"w": Fit("{gwc_usflag"), "e": Fit("{gwc_usflag")},
            group="illus",
        )

    # Golden West Casino Live Action Sports Banner (gwc_nflban) on portico courtyard flank (x=43.2, y=14..26)
    mb.detail_box_ft(43.25, 13.8, 10.6, 43.65, 26.2, 14.0, TEX_DARK, faces={"w": "skip", "b": "skip"})
    mb.sign_decal_ft("e", 43.65, 14.0, 26.0, 10.8, 13.8, Fit("gwc_nflban"), thick_ft=0.06, group="illus")

    # Warm portico entrance ceiling lights
    pt_c = _ne_pt(0.0, 5.2, 9.7)
    mb.light_ft(pt_c[0], pt_c[1], pt_c[2], light=260.0, color=(255, 224, 178), wait=0.7)
    mb.light_ft(pt_c[0] + 1.5, pt_c[1] + 1.5, 14.2, light=170.0, color=(255, 215, 165), wait=0.8)


# ---------------------------------------------------------------------------
# C. NE Courtyard Monuments, Horse Statue, Trees & Sago/Fan Palms
# ---------------------------------------------------------------------------

def _fan_palm(mb: MapBuilder, x_ft: float, y_ft: float, h_ft: float = 30.0, z_base_ft: float = Z_WALK_FT) -> None:
    """Emit a Washingtonia Mexican Fan Palm (solid lower bark trunk + alpha frond rosette)."""
    z_mid = z_base_ft + h_ft * 0.50
    z_top = z_base_ft + h_ft * 0.88
    mb.cyl_ft(x_ft, y_ft, 0.52, z_base_ft - 0.1, z_mid, sides=6, tex_side=TEX_BARK, tex_top="skip", group="detail")
    mb.cyl_ft(x_ft, y_ft, 0.40, z_mid - 0.1, z_top, sides=6, tex_side=TEX_BARK, tex_top=TEX_BARK, group="illus")
    mb.cyl_ft(x_ft, y_ft, 0.82, z_top - 4.0, z_top - 0.3, sides=6, tex_side=TEX_PALMHAT, tex_top=TEX_PALMHAT, group="illus")
    span = 6.0
    fz0, fz1 = z_top - 2.0, z_top + 4.5
    mb.flush_panel_ft(x_ft - span, y_ft - 0.08, fz0, x_ft + span, y_ft + 0.08, fz1, {"n": Fit("{gwc_palmfr"), "s": Fit("{gwc_palmfr")}, group="illus")
    mb.flush_panel_ft(x_ft - 0.08, y_ft - span, fz0, x_ft + 0.08, y_ft + span, fz1, {"e": Fit("{gwc_palmfr"), "w": Fit("{gwc_palmfr")}, group="illus")
    mb.slab_ramp_xft(x_ft - 4.8, x_ft, y_ft - 3.4, y_ft + 3.4, z_top + 0.8, z_top + 2.6, Fit("{gwc_palmfr"), thick_ft=0.12, group="illus")
    mb.slab_ramp_xft(x_ft, x_ft + 4.8, y_ft - 3.4, y_ft + 3.4, z_top + 2.6, z_top + 0.8, Fit("{gwc_palmfr"), thick_ft=0.12, group="illus")


def _sago_palm(mb: MapBuilder, x_ft: float, y_ft: float, z_base_ft: float = Z_WALK_FT, scale: float = 1.0) -> None:
    """Low courtyard rosette sago palm in round stone planter w/ sloped radial palm fronds."""
    mb.cyl_ft(x_ft, y_ft, 1.55 * scale, z_base_ft, z_base_ft + 0.85, sides=8, tex_side=TEX_STONE, tex_top=TEX_MULCH, group="detail")
    h_t = 2.0 * scale
    zc = z_base_ft + 0.8 + h_t
    span = 2.6 * scale
    band = 0.85 * scale
    mb.cyl_ft(x_ft, y_ft, 0.44 * scale, z_base_ft + 0.8, zc, sides=6, tex_side=TEX_PALMHAT, tex_top=TEX_PALMHAT, group="detail")
    # Flared radial rosette fronds (sloped X & Y wings -> spiky sago crown, zero upright green box!)
    fr = Fit("{gwc_palmfr")
    mb.slab_ramp_xft(x_ft - span, x_ft, y_ft - band, y_ft + band, zc + 1.05 * scale, zc - 0.15, fr, thick_ft=0.08, group="illus")
    mb.slab_ramp_xft(x_ft, x_ft + span, y_ft - band, y_ft + band, zc - 0.15, zc + 1.05 * scale, fr, thick_ft=0.08, group="illus")
    mb.slab_ramp_yft(x_ft - band, x_ft + band, y_ft - span, y_ft, zc + 1.05 * scale, zc - 0.15, fr, thick_ft=0.08, group="illus")
    mb.slab_ramp_yft(x_ft - band, x_ft + band, y_ft, y_ft + span, zc - 0.15, zc + 1.05 * scale, fr, thick_ft=0.08, group="illus")


def _ornamental_tree(mb: MapBuilder, x_ft: float, y_ft: float, h_ft: float = 17.0, z_base_ft: float = 0.65, tex_canopy: str = "{gwc_tree2") -> None:
    """Broadleaf ornamental parking-island shade tree (trunk + crossed alpha foliage)."""
    z_fork = z_base_ft + h_ft * 0.34
    z_top = z_base_ft + h_ft
    w = h_ft * 0.72
    mb.cyl_ft(x_ft, y_ft, 0.46, z_base_ft - 0.1, z_fork, sides=6, tex_side=TEX_BARK, tex_top="skip", group="detail")
    mb.cyl_ft(x_ft, y_ft, 0.32, z_fork - 0.1, z_top - 4.0, sides=6, tex_side=TEX_BARK, tex_top="skip", group="illus")
    mb.flush_panel_ft(x_ft - 0.5 * w, y_ft - 0.08, z_fork - 0.8, x_ft + 0.5 * w, y_ft + 0.08, z_top, {"n": Fit(tex_canopy), "s": Fit(tex_canopy)}, group="illus")
    mb.flush_panel_ft(x_ft - 0.08, y_ft - 0.5 * w, z_fork - 0.8, x_ft + 0.08, y_ft + 0.5 * w, z_top, {"e": Fit(tex_canopy), "w": Fit(tex_canopy)}, group="illus")


def _build_courtyard_monuments(mb: MapBuilder) -> None:
    """Build circular stone planter, Cowboy-on-Horse statue, courtyard palms, and trash bin."""
    hx, hy = 68.0, 22.0
    z_plaza = Z_WALK_FT  # 0.50 ft

    # 1. Circular white split-face stone planter (R=7.0 ft, curb wall z=0.5..2.1 ft > 18u rim)
    mb.cyl_ft(hx, hy, 7.0, z_plaza, z_plaza + 1.45, sides=12, tex_side=TEX_STONE, tex_top=TEX_CONC, group="detail")
    # Stepped bark mulch bed & central stone pedestal (subtle low trim matching 018/113.jpg)
    mb.cyl_ft(hx, hy, 6.2, z_plaza + 1.4, z_plaza + 1.58, sides=12, tex_side=TEX_MULCH, tex_top=TEX_MULCH, group="detail")
    mb.cyl_ft(hx, hy, 4.9, z_plaza + 1.58, z_plaza + 1.76, sides=12, tex_side=TEX_MULCH, tex_top=TEX_MULCH, group="detail")
    mb.cyl_ft(hx, hy, 2.7, z_plaza + 1.76, z_plaza + 2.55, sides=10, tex_side=TEX_STONE, tex_top=TEX_CONC, group="detail")

    # 2. Cowboy-on-Horse Bronze Monument (progs/gw_horse.md3): rock bottom -1.4..+1.8 -> origin z=3.85 ft
    mb.ent_ft(
        "misc_model",
        hx, hy, 3.85,
        mdl="progs/gw_horse.md3",
        angles="0 120 0",
    )
    # Clean cylindrical clip column preventing players from clipping inside MD3 statue
    mb.cyl_ft(hx, hy, 3.2, z_plaza + 2.5, z_plaza + 14.0, sides=8, tex_side="clip", tex_top="clip", tex_bot="clip", group="clip")
    # Uplight highlighting statue hero silhouette at dusk/shadow angle
    mb.light_ft(hx + 6.5, hy + 4.0, 9.5, light=165.0, color=(255, 224, 178), wait=0.7)

    # 3. Courtyard Sago Palms, Fan Palms & Exposed-Aggregate Trash Bin (zero trunk/frond collisions!)
    _sago_palm(mb, 48.0, 26.0, z_plaza, scale=1.0)
    _sago_palm(mb, 82.5, 9.5, z_plaza, scale=0.95)
    _fan_palm(mb, 94.0, 4.0, h_ft=31.0, z_base_ft=z_plaza)
    _fan_palm(mb, 53.0, 54.0, h_ft=30.0, z_base_ft=z_plaza)

    # Round exposed-aggregate courtyard trash bin near NW patio corner
    mb.cyl_ft(46.5, 13.5, 1.05, z_plaza, z_plaza + 3.0, sides=8, tex_side=TEX_CONC, tex_top=TEX_DARK, group="detail")
    mb.cyl_ft(46.5, 13.5, 0.85, z_plaza + 3.0, z_plaza + 3.3, sides=8, tex_side=TEX_DARK, tex_top=TEX_DARK, group="detail")


# ---------------------------------------------------------------------------
# D. S Union Ave Frontage (Knee Wall, Iron Fence, Hedges, Lamps, Gate Pillars, Bus Bench)
# ---------------------------------------------------------------------------

def _frontage_lamppost(mb: MapBuilder, x_ft: float, y_ft: float, z0: float = Z_WALK_FT) -> None:
    """Single-globe dark-green decorative frontage lamppost (~9.8 ft tall)."""
    mb.detail_box_ft(x_ft - 0.35, y_ft - 0.35, z0, x_ft + 0.35, y_ft + 0.35, z0 + 2.2, TEX_DARK, faces={"b": "skip"})
    mb.cyl_ft(x_ft, y_ft, 0.16, z0 + 2.2, z0 + 8.4, sides=6, tex_side=TEX_DARK, tex_top="skip", group="detail")
    mb.detail_box_ft(x_ft - 0.48, y_ft - 0.48, z0 + 8.4, x_ft + 0.48, y_ft + 0.48, z0 + 9.5, TEX_WHITE, faces={"b": TEX_DARK, "t": TEX_DARK})
    mb.light_ft(x_ft + 0.8, y_ft, z0 + 9.2, light=170.0, color=(255, 224, 178), wait=0.75)


def _build_union_frontage(mb: MapBuilder) -> None:
    """Build S Union Ave knee wall, wrought-iron spear fence, hedges, south pillars, lamps & bus bench."""
    z0 = Z_WALK_FT  # 0.50 ft (flush on x=167..172 concrete strip)

    # 3 walled spans leaving open North Drive (152..178) and South Drive (-100..-74)
    spans = [
        (-270.0, -103.0, {"n": "skip"}),  # North end flush against South Gate south pillar
        (-71.0, 150.0,   {"s": "skip"}),  # South end flush against South Gate north pillar
        (178.0, 303.5,   {}),             # North span north of North Drive
    ]
    for y0, y1, end_skip in spans:
        # Clipped boxwood hedge INSIDE/BEHIND the wall & fence (x=167.0..168.4, z=0.5..2.8)
        mb.detail_box_ft(167.0, y0 + 1.0, z0, 168.4, y1 - 1.0, z0 + 2.3, TEX_HEDGE, faces={"b": "skip"})
        # Cream split-face stone knee wall facing S Union Ave sidewalk (x=168.6..170.1, z=0.5..3.0) + cap
        mb.detail_box_ft(168.6, y0, z0, 170.1, y1, z0 + 2.5, TEX_STONE, faces={"b": "skip", "t": "skip", **end_skip})
        mb.detail_box_ft(168.5, y0, z0 + 2.5, 170.2, y1, z0 + 2.8, TEX_CONC, faces={"b": "skip", **end_skip})
        # Dark-green spear-top wrought-iron fence ({gwc_ironfence, z=3.3..7.5 ft)
        mb.detail_box_ft(169.1, y0, z0 + 2.8, 169.6, y1, z0 + 7.0, TEX_IRON, faces={"t": "skip", "b": "skip", **end_skip})

    # South Lot Entrance Two Tall Slender Cream Split-Face Stone Gate Pillars (flanking y=-100..-74)
    for py0, py1 in ((-103.0, -100.0), (-74.0, -71.0)):
        mb.detail_box_ft(167.8, py0, z0, 170.8, py1, z0 + 8.5, TEX_STONE, faces={"b": "skip", "t": "skip"})
        # Crisp overhanging stepped concrete cap (z=9.0..10.0 ft)
        mb.detail_box_ft(167.3, py0 - 0.5, z0 + 8.5, 171.3, py1 + 0.5, z0 + 9.0, TEX_CONC, faces={"b": TEX_DARK})
        mb.detail_box_ft(167.9, py0 + 0.1, z0 + 9.0, 170.7, py1 - 0.1, z0 + 9.5, TEX_CONC, faces={"b": "skip"})

    # 6 Dark-Green Single-Globe Lampposts along S Union Ave frontage (outside wall/coping)
    for ly in (-215.0, -140.0, -30.0, 48.0, 125.0, 245.0):
        _frontage_lamppost(mb, 171.1, ly, z0=z0)

    # Blue Transit Bus Bench outside wall near North Driveway (x=170.3..172.0, y=190..198, facing +X)
    mb.detail_box_ft(170.5, 190.5, z0 + 1.2, 172.0, 197.5, z0 + 1.55, Tile("gwc_carblu", 4.0, 4.0))
    mb.detail_box_ft(170.3, 190.5, z0 + 1.55, 170.65, 197.5, z0 + 3.2, Tile("gwc_carblu", 4.0, 4.0), faces={"b": "skip"})
    for leg_y in (191.2, 196.8):
        mb.detail_box_ft(170.6, leg_y - 0.2, z0, 171.8, leg_y + 0.2, z0 + 1.2, TEX_DARK, faces={"b": "skip", "t": "skip"})


# ---------------------------------------------------------------------------
# E. Enterable North Lot Guard Booth + Lot Signage
# ---------------------------------------------------------------------------

def _build_guard_booth(mb: MapBuilder) -> None:
    """Build enterable ~9x9 ft Guard Booth at (120, 195) with >=64x96u doorway & >=112u headroom."""
    cx, cy = 120.0, 195.0
    x0, x1 = cx - 4.5, cx + 4.5   # 115.5 .. 124.5 (8 ft clear inside between 0.5 ft walls)
    y0, y1 = cy - 4.5, cy + 4.5   # 190.5 .. 199.5
    wt = 0.5
    z_fl = Z_WALK_FT              # 0.50 ft = 6u (flush island pad)
    z_ceil = 10.2                 # 9.70 ft = 116.4u clear headroom (>= 112u!)

    # Concrete curbed booth island pad (step <= 4u from North Lot asphalt)
    _curb_ft(mb, 114.0, 187.0, Z_GROUND_FT, 126.0, 202.5, z_fl, TEX_CONC)

    # Register room & doorway cleanly for Hull-1 validation
    mb.register_room_ft("Guard Booth", floor_z_ft=z_fl, ceil_z_ft=z_ceil)

    # South wall with open doorway x=117.0..123.0 (6.0 ft = 72u wide x 8.5 ft = 102u high, z=0.5..9.0)
    mb.wall_xft(
        y0 + 0.5 * wt, x0, x1, z_fl, z_ceil, wt, TEX_STUCCO,
        doorways=[(cx - 3.0, cx + 3.0, 9.0, "guard_booth_door")],
        tex_inside=TEX_STUCCO, group="detail", force_world=False,
    )

    # North wall (lower wainscot + genuinely OPEN panoramic teller window w/ slim bronze frame + header)
    mb.detail_box_ft(x0, y1 - wt, z_fl, x1, y1, 3.8, TEX_STUCCO, faces={"b": "skip"})
    mb.detail_box_ft(x0, y1 - wt, 3.8, x0 + 1.0, y1, 8.3, TEX_STUCCO, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(x1 - 1.0, y1 - wt, 3.8, x1, y1, 8.3, TEX_STUCCO, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(x0 + 1.0, y1 - wt + 0.08, 3.8, x1 - 1.0, y1 - 0.08, 3.95, TEX_DARK, faces={"b": "skip", "w": "skip", "e": "skip"})
    mb.detail_box_ft(x0 + 1.0, y1 - wt + 0.08, 8.15, x1 - 1.0, y1 - 0.08, 8.3, TEX_DARK, faces={"t": "skip", "w": "skip", "e": "skip"})
    mb.detail_box_ft(x0 + 1.0, y1 - wt + 0.08, 3.95, x0 + 1.15, y1 - 0.08, 8.15, TEX_DARK, faces={"b": "skip", "t": "skip", "w": "skip"})
    mb.detail_box_ft(x1 - 1.15, y1 - wt + 0.08, 3.95, x1 - 1.0, y1 - 0.08, 8.15, TEX_DARK, faces={"b": "skip", "t": "skip", "e": "skip"})
    mb.detail_box_ft(cx - 0.08, y1 - wt + 0.1, 3.95, cx + 0.08, y1 - 0.1, 8.15, TEX_DARK, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(x0, y1 - wt, 8.3, x1, y1, z_ceil, TEX_STUCCO, faces={"t": "skip"})

    # West & East wraparound teller walls (genuinely OPEN clear cutouts above counter height!)
    for wx0, wx1 in ((x0, x0 + wt), (x1 - wt, x1)):
        mb.detail_box_ft(wx0, y0 + wt, z_fl, wx1, y1 - wt, 3.8, TEX_STUCCO, faces={"b": "skip", "s": "skip", "n": "skip"})
        mb.detail_box_ft(wx0, y0 + wt, 3.8, wx1, y0 + 1.2, 8.3, TEX_STUCCO, faces={"b": "skip", "t": "skip", "s": "skip"})
        mb.detail_box_ft(wx0, y1 - 1.2, 3.8, wx1, y1 - wt, 8.3, TEX_STUCCO, faces={"b": "skip", "t": "skip", "n": "skip"})
        mb.detail_box_ft(wx0 + 0.08, y0 + 1.2, 3.8, wx1 - 0.08, y1 - 1.2, 3.95, TEX_DARK, faces={"b": "skip", "s": "skip", "n": "skip"})
        mb.detail_box_ft(wx0 + 0.08, y0 + 1.2, 8.15, wx1 - 0.08, y1 - 1.2, 8.3, TEX_DARK, faces={"t": "skip", "s": "skip", "n": "skip"})
        mb.detail_box_ft(wx0 + 0.08, y0 + 1.2, 3.95, wx1 - 0.08, y0 + 1.35, 8.15, TEX_DARK, faces={"b": "skip", "t": "skip", "s": "skip"})
        mb.detail_box_ft(wx0 + 0.08, y1 - 1.35, 3.95, wx1 - 0.08, y1 - 1.2, 8.15, TEX_DARK, faces={"b": "skip", "t": "skip", "n": "skip"})
        mb.detail_box_ft(wx0 + 0.1, cy - 0.08, 3.95, wx1 - 0.1, cy + 0.08, 8.15, TEX_DARK, faces={"b": "skip", "t": "skip"})
        mb.detail_box_ft(wx0, y0 + wt, 8.3, wx1, y1 - wt, z_ceil, TEX_STUCCO, faces={"t": "skip", "s": "skip", "n": "skip"})

    # Interior flat ceiling flush below overhanging roof fascia (saves 5 hidden faces + eliminates overlap)
    mb.flush_panel_ft(x0 + 0.1, y0 + 0.1, z_ceil, x1 - 0.1, y1 - 0.1, z_ceil + 0.1, {"b": TEX_WHITE}, group="detail")
    # North guard desk counter (y=197.3..199.0) + end pedestal supports
    mb.detail_box_ft(x0 + wt, y1 - wt - 1.7, 3.15, x1 - wt, y1 - wt, 3.45, TEX_WOOD, faces={"w": "skip", "e": "skip", "n": "skip"})
    mb.detail_box_ft(x0 + wt, y1 - wt - 1.7, z_fl, x0 + wt + 0.4, y1 - wt, 3.15, TEX_DARK, faces={"b": "skip", "t": "skip", "w": "skip", "n": "skip"})
    mb.detail_box_ft(x1 - wt - 0.4, y1 - wt - 1.7, z_fl, x1 - wt, y1 - wt, 3.15, TEX_DARK, faces={"b": "skip", "t": "skip", "e": "skip", "n": "skip"})
    # Compact desk monitor + stand + keyboard pad (at NW desk bay x=117.0..118.8)
    mb.detail_box_ft(x0 + 1.9, y1 - wt - 1.0, 3.45, x0 + 2.7, y1 - wt - 0.4, 3.75, TEX_DARK, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(x0 + 1.5, y1 - wt - 1.05, 3.75, x0 + 3.1, y1 - wt - 0.65, 4.90, TEX_DARK, faces={"s": Fit("gwc_pylled"), "b": "skip"})
    mb.detail_box_ft(x0 + 1.7, y1 - wt - 1.55, 3.45, x0 + 2.9, y1 - wt - 1.15, 3.55, TEX_DARK, faces={"b": "skip"})
    # Guard swivel chair tucked cleanly under desk bay (x=117.4..119.0, y=195.8..197.2 -> leaves >57u south floor & >60u east aisle clear!)
    mb.detail_box_ft(x0 + 2.4, y1 - wt - 2.9, z_fl, x0 + 2.9, y1 - wt - 2.4, 1.55, TEX_DARK, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(x0 + 1.9, y1 - wt - 3.2, 1.55, x0 + 3.4, y1 - wt - 1.8, 1.85, TEX_DARK)
    mb.detail_box_ft(x0 + 1.9, y1 - wt - 3.2, 1.85, x0 + 3.4, y1 - wt - 2.9, 3.25, TEX_DARK, faces={"b": "skip"})

    # Overhanging brown pyramidal hip roof (eaves 114.0..126.0, 189.0..201.0, z=10.2..13.5 ft)
    mb.detail_box_ft(x0 - 1.5, y0 - 1.5, z_ceil + 0.1, x1 + 1.5, y1 + 1.5, z_ceil + 0.45, TEX_DARK, faces={"t": "skip"})
    _conical_wedges_ft(
        mb, cx, cy,
        r_outer=6.0 * math.sqrt(2.0), r_top=0.6,
        z0=z_ceil + 0.4, z_eave_h=0.25, z_top=13.6,
        sides=4, tex_slope=TEX_SHINGLE, tex_rim=TEX_DARK, angle_ofs_deg=45.0, tex_bot="skip",
    )
    mb.light_ft(cx, cy, z_ceil - 0.8, light=240.0, color=(255, 224, 178), wait=0.7)
    mb.spot_ft("guard_booth_interior", cx + 1.8, cy - 2.4, z_fl + 2.5, yaw=127.0, desc="Inside enterable North Lot Guard Booth toward desk/monitor & lot")

    # Blue directional / ADA parking sign on post near North Driveway apron (x=159, y=181)
    mb.cyl_ft(159.0, 181.5, 0.12, Z_ROAD_FT, 7.8, sides=6, tex_side=TEX_GALV, tex_top="skip", group="detail")
    mb.detail_box_ft(158.85, 180.6, 5.4, 159.15, 182.4, 7.6, Tile("gwc_carblu", 2.0, 2.5))
    mb.sign_decal_ft("e", 159.15, 180.8, 182.2, 5.8, 7.3, Fit("gwc_oneway"), thick_ft=0.05, group="illus")
    # Red fire-lane apron curbs beside North Drive
    _curb_ft(mb, 146.0, 178.0, Z_ROAD_FT, 166.5, 179.0, Z_WALK_FT, TEX_CURBRED)
    _curb_ft(mb, 146.0, 151.0, Z_ROAD_FT, 166.5, 152.0, Z_WALK_FT, TEX_CURBRED)


# ---------------------------------------------------------------------------
# F. Purple Pylon Marquee Sign (x=155, y=0)
# ---------------------------------------------------------------------------

def _build_pylon_marquee(mb: MapBuilder) -> None:
    """Build ~28 ft fluted royal-purple pylon marquee sign with LED & crown cabinets."""
    px, py = 155.0, 0.0
    # Planter bed around base
    _curb_ft(mb, px - 6.0, py - 8.5, Z_ROAD_FT, px + 6.0, py + 8.5, 1.3, TEX_STONE)
    mb.detail_box_ft(px - 5.2, py - 7.7, 1.0, px + 5.2, py + 7.7, 1.35, TEX_MULCH, faces={"b": "skip"})
    mb.detail_box_ft(px - 4.6, py - 7.0, 1.35, px + 4.6, py + 7.0, 2.4, TEX_HEDGE, faces={"b": "skip"})

    # Fluted purple pylon column base (z=1.3..12.2)
    mb.detail_box_ft(px - 2.4, py - 4.2, 1.3, px + 2.4, py + 4.2, 12.2, TEX_PURPLE, faces={"b": "skip", "t": "skip"})
    for fy in (-3.6, 3.6):
        mb.detail_box_ft(px - 2.6, py + fy - 0.5, 1.3, px + 2.6, py + fy + 0.5, 27.6, TEX_PURPLE, faces={"b": "skip"})

    # Programmable LED cabinet ("POKER BLACKJACK BACCARAT", z=12.2..19.4)
    mb.detail_box_ft(
        px - 2.8, py - 5.8, 12.2, px + 2.8, py + 5.8, 19.4,
        TEX_DARK,
        faces={"e": Fit("gwc_pylled"), "w": Fit("gwc_pylled"), "t": "skip"},
    )
    # Top cursive/neon Golden West crown cabinet (z=19.4..27.4) + arched finial cap (27.4..28.6)
    mb.detail_box_ft(
        px - 3.0, py - 6.4, 19.4, px + 3.0, py + 6.4, 27.4,
        TEX_PURPLE,
        faces={"e": Fit("gwc_pyltop"), "w": Fit("gwc_pyltop"), "t": TEX_DARK},
    )
    mb.detail_box_ft(px - 2.2, py - 5.2, 27.4, px + 2.2, py + 5.2, 28.5, TEX_PURPLE, faces={"b": "skip"})

    mb.light_ft(px + 6.0, py, 20.5, light=260.0, color=(235, 195, 255), wait=0.7)
    mb.light_ft(px - 6.0, py, 20.5, light=240.0, color=(235, 195, 255), wait=0.7)


# ---------------------------------------------------------------------------
# G. Parking Lot Stalls, Wheel Stops, Tree Islands, Pole Lights, Fences & Parked Cars
# ---------------------------------------------------------------------------

def _stripe_x(mb: MapBuilder, x0: float, x1: float, y: float, w: float = 0.25) -> None:
    mb.flush_panel_ft(x0, y - 0.5 * w, Z_ROAD_FT, x1, y + 0.5 * w, Z_MARK_FT, {"t": TEX_WHITE}, group="illus")


def _stripe_y(mb: MapBuilder, x: float, y0: float, y1: float, w: float = 0.25) -> None:
    mb.flush_panel_ft(x - 0.5 * w, y0, Z_ROAD_FT, x + 0.5 * w, y1, Z_MARK_FT, {"t": TEX_WHITE}, group="illus")


def _shoebox_light(mb: MapBuilder, x_ft: float, y_ft: float) -> None:
    """26-ft tall dark bronze parking lot shoebox pole light."""
    mb.cyl_ft(x_ft, y_ft, 0.9, Z_ROAD_FT, 2.2, sides=6, tex_side=TEX_CONC, tex_top=TEX_CONC, group="detail")
    mb.detail_box_ft(x_ft - 0.3, y_ft - 0.3, 2.2, x_ft + 0.3, y_ft + 0.3, 26.0, TEX_DARK, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(x_ft - 1.2, y_ft - 0.7, 25.4, x_ft + 1.2, y_ft + 0.7, 26.2, TEX_DARK, faces={"b": TEX_WHITE})
    mb.light_ft(x_ft, y_ft, 24.5, light=245.0, color=(255, 232, 195), wait=0.65)


def _parked_car(mb: MapBuilder, cx: float, cy: float, axis: str, tex_body: str, is_suv: bool = False) -> None:
    """Emit a lean 2-brush low-poly parked car (clean detail boxes for Hull-1)."""
    L = 14.8
    W = 6.2
    h_low = 2.6 if not is_suv else 2.9
    h_top = 4.9 if not is_suv else 5.6
    sp = Tile(tex_body, 6.0, 4.0)
    win = Fit("gwc_carwin")
    if axis == "x":
        hx, hy = 0.5 * L, 0.5 * W
        cab0, cab1 = -0.26 * L, 0.22 * L
        mb.detail_box_ft(cx - hx, cy - hy, Z_ROAD_FT + 0.25, cx + hx, cy + hy, h_low, sp, faces={"b": "skip"})
        mb.detail_box_ft(cx + cab0, cy - hy + 0.35, h_low, cx + cab1, cy + hy - 0.35, h_top, win, faces={"t": sp, "b": "skip"})
    else:
        hx, hy = 0.5 * W, 0.5 * L
        cab0, cab1 = -0.24 * L, 0.24 * L
        mb.detail_box_ft(cx - hx, cy - hy, Z_ROAD_FT + 0.25, cx + hx, cy + hy, h_low, sp, faces={"b": "skip"})
        mb.detail_box_ft(cx - hx + 0.35, cy + cab0, h_low, cx + hx - 0.35, cy + cab1, h_top, win, faces={"t": sp, "b": "skip"})


def _chain_fence_x(mb: MapBuilder, y_ft: float, x0: float, x1: float, z0: float = Z_ROAD_FT, h: float = 6.2) -> None:
    mb.detail_box_ft(x0, y_ft - 0.12, z0, x1, y_ft + 0.12, z0 + h, TEX_CHAIN, faces={"t": "skip", "b": "skip"})
    px = x0
    while px <= x1 + 0.5:
        mb.detail_box_ft(px - 0.14, y_ft - 0.14, z0, px + 0.14, y_ft + 0.14, z0 + h + 0.2, TEX_GALV, faces={"b": "skip"})
        px += min(48.0, max(18.0, (x1 - x0) / 4.0))


def _chain_fence_y(mb: MapBuilder, x_ft: float, y0: float, y1: float, z0: float = Z_ROAD_FT, h: float = 6.2) -> None:
    mb.detail_box_ft(x_ft - 0.12, y0, z0, x_ft + 0.12, y1, z0 + h, TEX_CHAIN, faces={"t": "skip", "b": "skip"})
    py = y0
    while py <= y1 + 0.5:
        mb.detail_box_ft(x_ft - 0.14, py - 0.14, z0, x_ft + 0.14, py + 0.14, z0 + h + 0.2, TEX_GALV, faces={"b": "skip"})
        py += min(48.0, max(18.0, (y1 - y0) / 4.0))


def _build_parking_details(mb: MapBuilder) -> None:
    """Build OSM-aligned stall markings, wheel stops, tree islands, lights, fences & parked cars."""
    # 1. Stall Stripes matching OSM WAY 755013749..761 bays
    # North Lot double-loaded rows: y=172..204 (bay1) and y=234..266 (bay2) + north row 288..303
    for bay_y0, bay_y1 in ((172.0, 204.0), (234.0, 266.0)):
        ym = 0.5 * (bay_y0 + bay_y1)
        _stripe_x(mb, -108.0, 96.0, ym)
        for sx in range(-108, 100, 12):
            _stripe_y(mb, float(sx), bay_y0, bay_y1)
    for sx in range(-108, 100, 12):
        _stripe_y(mb, float(sx), 289.0, 303.0)

    # East Strip angled/perpendicular row along frontage (x=147..166)
    for sy_base, sy_top in ((-260, -110), (-64, -14), (24, 144), (192, 294)):
        for sy in range(sy_base, sy_top, 12):
            _stripe_x(mb, 147.0, 165.5, float(sy))

    # South Lot double-loaded bay (y=-202..-170) & southern perimeter row (y=-269..-254)
    _stripe_x(mb, -50.0, 118.0, -186.0)
    for sx in range(-48, 124, 12):
        _stripe_y(mb, float(sx), -202.0, -170.0)
    for sx in range(-48, 124, 12):
        _stripe_y(mb, float(sx), -269.0, -254.0)

    # Concrete wheel stops (4.2u low curb -> easily stepped by Hull-1) on key visible stalls
    wheel_stop_xs = (-84.0, -60.0, -24.0, 0.0, 24.0, 60.0, 84.0)
    for wx in wheel_stop_xs:
        mb.detail_box_ft(wx - 2.6, 185.6, Z_ROAD_FT, wx + 2.6, 186.2, Z_ROAD_FT + 0.35, TEX_CONC, faces={"b": "skip"})
        mb.detail_box_ft(wx - 2.6, 247.6, Z_ROAD_FT, wx + 2.6, 248.2, Z_ROAD_FT + 0.35, TEX_CONC, faces={"b": "skip"})
    for wx in (-36.0, 0.0, 36.0, 72.0, 96.0):
        mb.detail_box_ft(wx - 2.6, -188.4, Z_ROAD_FT, wx + 2.6, -187.8, Z_ROAD_FT + 0.35, TEX_CONC, faces={"b": "skip"})
    for wy in (48.0, 72.0, 96.0, 216.0, 240.0):
        mb.detail_box_ft(163.2, wy - 2.6, Z_ROAD_FT, 163.8, wy + 2.6, Z_ROAD_FT + 0.35, TEX_CONC, faces={"b": "skip"})

    # 2. Landscaped Curbed Tree Islands w/ Ornamental / Valley Oak & Cypress Trees
    tree_islands = [
        (-116.0, 188.0, 7.0, 16.0, "{gwc_tree2"),
        (-42.0,  188.0, 6.0, 16.0, "{gwc_tree3"),
        (36.0,   188.0, 6.0, 16.0, "{gwc_tree2"),
        (-116.0, 250.0, 7.0, 16.0, "{gwc_tree2"),
        (-42.0,  250.0, 6.0, 16.0, "{gwc_tree2"),
        (36.0,   250.0, 6.0, 16.0, "{gwc_tree3"),
        (138.0,  128.0, 6.0, 10.0, "{gwc_tree2"),
        (-60.0, -186.0, 7.0, 16.0, "{gwc_tree2"),
        (18.0,  -186.0, 6.0, 16.0, "{gwc_tree3"),
        (110.0, -186.0, 6.0, 16.0, "{gwc_tree2"),
    ]
    for ix, iy, iw, il, tcan in tree_islands:
        _curb_ft(mb, ix - 0.5 * iw, iy - 0.5 * il, Z_ROAD_FT, ix + 0.5 * iw, iy + 0.5 * il, 0.65, TEX_CURB)
        mb.detail_box_ft(ix - 0.5 * iw + 0.4, iy - 0.5 * il + 0.4, 0.35, ix + 0.5 * iw - 0.4, iy + 0.5 * il - 0.4, 0.70, TEX_MULCH, faces={"b": "skip"})
        _ornamental_tree(mb, ix, iy, h_ft=18.5, z_base_ft=0.70, tex_canopy=tcan)

    # 3. Tall 26-ft Dark Shoebox Parking Pole Lights
    for lx, ly in (
        (-78.0, 188.0), (0.0, 188.0), (72.0, 188.0),
        (-78.0, 250.0), (72.0, 250.0),
        (136.0, 32.0), (-22.0, -186.0), (66.0, -186.0),
    ):
        _shoebox_light(mb, lx, ly)

    # 4. BOH CMU Dumpster Enclosure + Dual Dumpsters (tucked cleanly along West service perimeter x=-156.8..-143.5, y=42..58)
    mb.detail_box_ft(-156.8, 42.0, Z_ROAD_FT, -155.8, 58.0, 6.5, TEX_CINDER, faces={"b": "skip"})
    mb.detail_box_ft(-155.8, 42.0, Z_ROAD_FT, -143.5, 43.0, 6.5, TEX_CINDER, faces={"b": "skip", "w": "skip"})
    mb.detail_box_ft(-155.8, 57.0, Z_ROAD_FT, -143.5, 58.0, 6.5, TEX_CINDER, faces={"b": "skip", "w": "skip"})
    mb.detail_box_ft(-154.6, 44.5, Z_ROAD_FT, -149.0, 49.5, 4.6, Fit("gwc_dumpstr"), faces={"t": TEX_DARK, "b": "skip"})
    mb.detail_box_ft(-154.6, 50.5, Z_ROAD_FT, -149.0, 55.5, 4.6, Fit("gwc_dumpstr"), faces={"t": TEX_DARK, "b": "skip"})

    # 5. West, North, Delaware-East & South Chain-Link Boundary Fences ({gwc_chain, open walk gates)
    _chain_fence_y(mb, -157.3, -124.5, 303.6)                 # West boundary north of Trinity Ave
    _chain_fence_x(mb, -124.5, -157.3, -101.6)                # Trinity Ave North lot jog
    _chain_fence_y(mb, -101.6, -270.4, -214.0)                # Delaware St East (south section)
    _chain_fence_y(mb, -101.6, -192.0, -124.5)                # Delaware St East (north section; 22ft gate gap!)
    _chain_fence_x(mb, -270.4, -101.6, 166.5)                 # South boundary beside Ramos Tires
    _chain_fence_x(mb, 303.8, -157.3, 166.5)                  # North boundary beside Billboard Lot

    # 6. Clean Low-Poly Parked Cars (14 vehicles = 28 detail boxes, spaced >= 18 ft apart for clean Hull-1)
    cars = [
        # North Lot
        (-90.0, 195.0, "y", "gwc_carblu", False),
        (-66.0, 179.0, "y", "gwc_carsil", True),
        (-18.0, 195.0, "y", "gwc_carwht", False),
        (18.0,  241.0, "y", "gwc_carred", False),
        (-66.0, 259.0, "y", "gwc_carsil", False),
        (78.0,  259.0, "y", "gwc_carblu", True),
        # East Strip
        (156.0, 54.0,  "x", "gwc_carwht", False),
        (156.0, 102.0, "x", "gwc_carred", True),
        (156.0, 234.0, "x", "gwc_carsil", False),
        # South Lot
        (-30.0, -177.0, "y", "gwc_carred", False),
        (6.0,   -195.0, "y", "gwc_carwht", True),
        (54.0,  -177.0, "y", "gwc_carsil", False),
        (90.0,  -195.0, "y", "gwc_carblu", False),
        (30.0,  -261.0, "y", "gwc_carwht", False),
    ]
    for cx_c, cy_c, ax, tcol, suv in cars:
        _parked_car(mb, cx_c, cy_c, ax, tcol, is_suv=suv)


# ---------------------------------------------------------------------------
# Public Entrypoint & Spots
# ---------------------------------------------------------------------------

def _register_exterior_spots(mb: MapBuilder) -> None:
    mb.spot_ft("casino_ne_courtyard", 78.0, 34.0, 4.5, yaw=225.0, desc="NE Flagstone Courtyard facing Portico & Horse Monument")
    mb.spot_ft("casino_horse_plaza", 56.0, 22.0, 4.5, yaw=350.0, desc="Plaza beside Cowboy-on-Horse stone planter")
    mb.spot_ft("casino_pylon_view", 142.0, -32.0, 4.5, yaw=65.0, desc="East Drive view toward Purple Pylon Marquee")
    mb.spot_ft("casino_north_lot", 0.0, 218.0, 4.5, yaw=270.0, desc="North Parking Lot center aisle toward Casino")
    mb.spot_ft("casino_south_lot", 24.0, -152.0, 4.5, yaw=90.0, desc="South Parking Lot toward SE Stone Wing & Clerestory")
    mb.spot_ft("casino_west_service", -78.0, -16.0, 4.5, yaw=60.0, desc="West BOH service drive")
    mb.spot_ft("casino_south_gate", 146.0, -87.0, 4.5, yaw=180.0, desc="South Lot gate pillars looking west")


def build_casino_ext(mb: MapBuilder) -> Dict[str, object]:
    """Populate MapBuilder with Golden West Casino exterior sitework, roofs, and monuments."""
    global Tile, Fit
    mb_mod = sys.modules.get(type(mb).__module__)
    if mb_mod is not None and hasattr(mb_mod, "Tile") and hasattr(mb_mod, "Fit"):
        if mb_mod.Tile is not Tile or mb_mod.Fit is not Fit:
            Tile = mb_mod.Tile  # type: ignore[misc]
            Fit = mb_mod.Fit    # type: ignore[misc]
            _refresh_shared_tiles()

    _build_lot_pavement_and_plaza(mb)
    _build_roof_superstructure(mb)
    _build_courtyard_monuments(mb)
    _build_union_frontage(mb)
    _build_guard_booth(mb)
    _build_pylon_marquee(mb)
    _build_parking_details(mb)
    _register_exterior_spots(mb)
    return mb.stats()


def _count_faces(mb: MapBuilder) -> Tuple[int, int]:
    """Return (total_faces, active_non_skip_faces) across all MapBuilder brushes."""
    total = 0
    active = 0
    for grp_brushes in mb._brushes.values():
        for _bbox, lines in grp_brushes:
            total += len(lines)
            for line in lines:
                if " ) skip " not in line:
                    active += 1
    return total, active


# ---------------------------------------------------------------------------
# Standalone Self-Test
# ---------------------------------------------------------------------------

def _build_standalone_test_shell(mb: MapBuilder) -> None:
    """Emit minimal sealed standalone sky/ground enclosure when running gw_casino_ext.py solo."""
    x0, y0, x1, y1 = CASINO_LOT_FT
    pad = 40.0
    st = 8.0
    sx0, sy0, sx1, sy1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    sz0, sz1 = -12.0, 128.0
    mb.structural_box_ft(sx0 - st, sy0 - st, sz1, sx1 + st, sy1 + st, sz1 + st, "sky")
    mb.structural_box_ft(sx0 - st, sy0 - st, sz0 - st, sx1 + st, sy1 + st, sz0, "sky")
    mb.structural_box_ft(sx0 - st, sy0 - st, sz0, sx0, sy1 + st, sz1, "sky")
    mb.structural_box_ft(sx1, sy0 - st, sz0, sx1 + st, sy1 + st, sz1, "sky")
    mb.structural_box_ft(sx0, sy0 - st, sz0, sx1, sy0, sz1, "sky")
    mb.structural_box_ft(sx0, sy1, sz0, sx1, sy1 + st, sz1, "sky")
    mb.structural_box_ft(sx0, sy0, sz0, sx1, sy1, Z_GROUND_FT, Tile("gwc_dirt", 24.0, 24.0))
    mb.ent_ft("info_player_start", 84.0, 40.0, 3.0, angle=225)
    mb.light_ft(68.0, 22.0, 48.0, light=245.0, color=(255, 238, 206), wait=0.5)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Validate gw_casino_ext.py standalone with MapBuilder.")
    ap.add_argument("--out", default="", help="Optional path to write standalone test .map")
    args = ap.parse_args(argv)

    mb = MapBuilder(check_textures=True, require_gwc_prefix=True)
    _build_standalone_test_shell(mb)
    build_casino_ext(mb)

    errors = mb.validate_all()
    stats = mb.stats()
    total_faces, active_faces = _count_faces(mb)
    legacy = [
        t for t in stats["textures_used"]
        if any(t.lstrip("{").startswith(p) for p in ("bk_", "bklan", "bk3_", "chain", "sky_bk"))
    ]
    print("gw_casino_ext standalone summary:")
    print(f"  brushes: {stats['brushes']}")
    print(f"  faces: total={total_faces}, active_non_skip={active_faces}")
    for k in (
        "total_brushes", "entities", "rooms", "doorways", "spots",
        "missing_textures",
    ):
        print(f"  {k}: {stats[k]}")
    print(f"  textures_used_count: {len(stats['textures_used'])}")
    print(f"  textures_used: {sorted(stats['textures_used'])}")
    print(f"  legacy_textures: {legacy}")
    print(f"  validation_errors ({len(errors)}): {errors}")

    if args.out:
        mb.write_map(args.out)
        print(f"  wrote test map: {args.out}")

    return 0 if (not errors and not legacy and not stats["missing_textures"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
