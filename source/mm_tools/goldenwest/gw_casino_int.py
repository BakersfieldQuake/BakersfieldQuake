"""gw_casino_int.py — Golden West Casino Interior & Building Shell Geometry Author.

Exclusive owner: geo-casino-int (`source/mm_tools/goldenwest/gw_casino_int.py`).
Builds the complete enterable interior and structural wall envelope (up to the
locked roof seam at z=16.0 ft main/wings and z=13.0 ft 12-sided Rotunda) for
BLDG 59517066 ("Golden West Casino", 156.2 x 161.4 ft) in Bakersfield, CA:

  - Seam-locked outer floor slab (z=-0.5..0.5 ft) & mitered exterior walls
  - 1. NE 45-deg Entrance Vestibule & Security/Host Podium (`x+y=50`)
  - 2. Main Open-Plan Poker Pit w/ heavy wood cross-ties, 2x4 drop soffits,
       hanging flat-screen TVs, [11] table placards, and 13 spaced oval/octagon
       burgundy-red felt tables (ZERO #157 Stones green felt)
  - 3. West 2-Bay Cashier/Chip Cage w/ corrugated roll-down shutters, padded
       granite/leather ledge, vault, BOH hallway, Restrooms, Kitchen & SW exit
  - 4. East 12-sided Rotunda Blackjack Lounge Bar w/ radial laminated arch ribs,
       3-bay mirrored back-bar, cyan neon "Blackjack" / "Lounge", curved granite
       bar over ceramic tile apron, Coors tap towers, 7 spaced leather barstools
  - 5. SE Stone Wing Employee Office/Break Room (`EMPLOYEES ONLY` + E window)
  - 6. South Alcove & Golden Laughing Buddha Shrine (`progs/gw_buddha.md3`)
       flanked by gold urns beneath twin horizontal vinyl-blind windows
  - 7. North Poker Room & North Parking Lot double exit
  - 8. Sunny Bakersfield interior lighting, rooms, doorways, and audit spots

Usage:
  from goldenwest.gw_casino_int import build_casino_int
  build_casino_int(mb)

Standalone validation:
  python source/mm_tools/goldenwest/gw_casino_int.py
"""
from __future__ import annotations

import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if MM_TOOLS_DIR not in sys.path:
    sys.path.insert(0, MM_TOOLS_DIR)

if __package__:
    from .gw_lib import (  # noqa: E402
        CASINO_BOUNDS_FT,
        CASINO_CEIL_Z_FT,
        CASINO_FLOOR_Z_FT,
        CASINO_POLY_FT,
        CASINO_ROTUNDA_CENTER_FT,
        CASINO_ROTUNDA_R_FT,
        CASINO_WALL_T_FT,
        HULL1_MIN_CEIL_U,
        HULL1_MIN_DOOR_H_U,
        HULL1_MIN_DOOR_W_U,
        Fit,
        MapBuilder,
        TexSpec,
        Tile,
        U_FT,
        snap_val,
    )
else:
    from gw_lib import (  # noqa: E402
        CASINO_BOUNDS_FT,
        CASINO_CEIL_Z_FT,
        CASINO_FLOOR_Z_FT,
        CASINO_POLY_FT,
        CASINO_ROTUNDA_CENTER_FT,
        CASINO_ROTUNDA_R_FT,
        CASINO_WALL_T_FT,
        HULL1_MIN_CEIL_U,
        HULL1_MIN_DOOR_H_U,
        HULL1_MIN_DOOR_W_U,
        Fit,
        MapBuilder,
        TexSpec,
        Tile,
        U_FT,
        snap_val,
    )

# ---------------------------------------------------------------------------
# Seam & Architectural Constants (locked with geo-casino-ext, #20/#23)
# ---------------------------------------------------------------------------
FLOOR_BOT_Z = -0.5
FLOOR_Z = CASINO_FLOOR_Z_FT          # 0.5 ft (+6u top surface)
MAIN_WALL_Z = CASINO_CEIL_Z_FT       # 16.0 ft (BOH / Main / Vestibule / SE top)
ROTUNDA_WALL_Z = 13.0                # 13.0 ft (12-sided Rotunda cone base)
WALL_T = CASINO_WALL_T_FT            # 1.0 ft exterior wall thickness
DOOR_TOP_Z = 9.5                     # 9.0 ft = 108u clear >= 96u Hull-1 min

# Locked doorway intervals matching geo-casino-ext plaza/canopies (#23)
NE_STOREFRONT_A = (43.0, 7.0)        # NW end of 45-deg storefront (x+y = 50)
NE_STOREFRONT_B = (62.28, -12.28)    # SE end meeting Rotunda chord v07->v08
SOUTH_EXIT_X = (24.0, 34.0)          # y = -71.6 (10 ft = 120u wide)
SW_EXIT_X = (-42.0, -34.0)           # y = -68.4 (8 ft = 96u wide)
NORTH_EXIT_X = (20.0, 28.0)          # y = 70.5  (8 ft = 96u wide)

# Interior partition X/Y coordinates (all 1/12 ft crisp)
X_BOH_DIV = -19.0                    # West Cashier / BOH stone dividing wall
X_CAGE_BACK = -33.0                  # West wall of Cashier Vault
X_CORR_W = -41.0                     # West wall of Main BOH corridor (8 ft wide)
X_SE_WING = 36.0                     # West wall of SE Employee Office/Break Wing
Y_SE_NORTH = -35.13                  # North wall of SE Wing (v20 level)

# Clockwise perimeter vertices derived from CASINO_POLY_FT with NE 45-deg chamfer
# (indices refer to CASINO_POLY_FT except NE v06 replaced by NE_STOREFRONT_A..B).
PERIM_PTS: List[Tuple[float, float]] = [
    (-54.07, 77.17),   # 0: v00 West wall N end
    (-43.23, 77.61),   # 1: v01 NW step E
    (-43.35, 88.31),   # 2: v02 N wing NW corner
    (5.42, 89.70),     # 3: v03 N wing NE corner
    (7.30, 71.11),     # 4: v04 N wing SE step
    (41.97, 70.52),    # 5: v05 Main NE corner (N Lot exit on 4->5)
    NE_STOREFRONT_A,   # 6: NE 45-deg storefront start (43, 7)
    NE_STOREFRONT_B,   # 7: NE 45-deg storefront end meeting Rotunda (62.28, -12.28)
    (65.78, -8.44),    # 8: v08 Rotunda
    (71.02, -4.60),    # 9: v09 Rotunda
    (80.05, -2.23),    # 10: v10 Rotunda
    (87.61, -3.29),    # 11: v11 Rotunda
    (96.73, -8.87),    # 12: v12 Rotunda
    (100.19, -16.80),  # 13: v13 Rotunda
    (102.15, -24.36),  # 14: v14 Rotunda
    (100.96, -32.07),  # 15: v15 Rotunda
    (97.86, -39.12),   # 16: v16 Rotunda
    (89.61, -43.61),   # 17: v17 Rotunda
    (78.11, -48.06),   # 18: v18 Rotunda
    (61.28, -44.19),   # 19: v19 Rotunda SW
    (54.76, -35.13),   # 20: v20 SE wing NE corner
    (53.62, -71.66),   # 21: v21 SE corner
    (-20.14, -71.51),  # 22: v22 S step W
    (-19.33, -68.77),  # 23: v23 BOH S notch
    (-53.35, -68.37),  # 24: v24 SW corner
]

# Precomputed Rotunda perimeter polyline indices (edge 7->8 .. 19->20 are 12 Rotunda facets)
ROTUNDA_FIRST_EDGE = 7
ROTUNDA_LAST_EDGE = 19  # edge 19 goes PERIM_PTS[19] -> PERIM_PTS[20]
ROTUNDA_V07 = (60.56, -14.17)  # Interior Rotunda NW corner at archway


# ---------------------------------------------------------------------------
# Low-level Clean Convex Geometry Helpers
# ---------------------------------------------------------------------------

def _snap_ft(val: float, grid_u: float = 1.0) -> float:
    return snap_val(val * U_FT, grid_u) / U_FT


def _v_sub(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    return (a[0] - b[0], a[1] - b[1])


def _v_add(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    return (a[0] + b[0], a[1] + b[1])


def _v_mul(a: Tuple[float, float], s: float) -> Tuple[float, float]:
    return (a[0] * s, a[1] * s)


def _v_len(a: Tuple[float, float]) -> float:
    return math.hypot(a[0], a[1])


def _poly_area2(pts: Sequence[Tuple[float, float]]) -> float:
    s = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s


def _edge_outward_cw(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return (0.0, 1.0)
    return (-dy / L, dx / L)


def _line_intersect_2d(
    p1: Tuple[float, float],
    d1: Tuple[float, float],
    p2: Tuple[float, float],
    d2: Tuple[float, float],
) -> Optional[Tuple[float, float]]:
    det = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(det) < 1e-6:
        return None
    rhs = (p2[0] - p1[0], p2[1] - p1[1])
    t = (rhs[0] * d2[1] - rhs[1] * d2[0]) / det
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def _compute_inner_miter_ring(
    ring: Sequence[Tuple[float, float]],
    thick_ft: float,
) -> List[Tuple[float, float]]:
    """Inset a CW perimeter polygon cleanly inward by thick_ft with miter clamping."""
    n = len(ring)
    inner: List[Tuple[float, float]] = []
    for i in range(n):
        p_prev = ring[(i - 1) % n]
        p_cur = ring[i]
        p_next = ring[(i + 1) % n]

        e1 = _v_sub(p_cur, p_prev)
        e2 = _v_sub(p_next, p_cur)
        L1, L2 = _v_len(e1), _v_len(e2)
        d1 = _v_mul(e1, 1.0 / max(L1, 1e-6))
        d2 = _v_mul(e2, 1.0 / max(L2, 1e-6))
        n1_out = _edge_outward_cw(p_prev, p_cur)
        n2_out = _edge_outward_cw(p_cur, p_next)
        q1 = _v_sub(p_cur, _v_mul(n1_out, thick_ft))
        q2 = _v_sub(p_cur, _v_mul(n2_out, thick_ft))

        pt = _line_intersect_2d(q1, d1, q2, d2)
        if pt is None or _v_len(_v_sub(pt, p_cur)) > thick_ft * 2.6:
            avg_in = (-0.5 * (n1_out[0] + n2_out[0]), -0.5 * (n1_out[1] + n2_out[1]))
            al = max(_v_len(avg_in), 1e-6)
            pt = _v_add(p_cur, _v_mul(avg_in, thick_ft / al))
        inner.append((_snap_ft(pt[0]), _snap_ft(pt[1])))
    return inner


def _emit_quad_wall_prism_ft(
    mb: MapBuilder,
    p_out_a: Tuple[float, float],
    p_out_b: Tuple[float, float],
    p_in_a: Tuple[float, float],
    p_in_b: Tuple[float, float],
    z0_ft: float,
    z1_ft: float,
    tex_out: TexSpec,
    tex_in: TexSpec,
    tex_cap: TexSpec = "gwc_stone",
    tex_top: Optional[TexSpec] = None,
    tex_bot: Optional[TexSpec] = None,
    group: str = "detail",
    force_world: bool = False,
) -> None:
    """Emit a convex 4-gon extruded brush with explicit outer vs inner textures."""
    snap = mb.world_snap_u if (group in ("world", "clip") or force_world) else mb.detail_snap_u
    az0 = snap_val(z0_ft * U_FT, snap)
    az1 = snap_val(z1_ft * U_FT, snap)
    if az1 - az0 < 0.25:
        return

    raw_xy = [p_out_a, p_out_b, p_in_b, p_in_a]
    poly_u = [(snap_val(x * U_FT, snap), snap_val(y * U_FT, snap)) for x, y in raw_xy]
    if _poly_area2(poly_u) < 0.0:
        poly_u.reverse()

    # Check strict convexity on all 4 corners before emission
    for k in range(4):
        a, b, c = poly_u[k], poly_u[(k + 1) % 4], poly_u[(k + 2) % 4]
        if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-2:
            return

    n_edge_out = _edge_outward_cw(p_out_a, p_out_b)
    bot_pts = [(x, y, az0) for x, y in poly_u]
    top_pts = [(x, y, az1) for x, y in poly_u]
    faces: List[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], TexSpec]] = [
        (bot_pts, (0.0, 0.0, -1.0), tex_cap if tex_bot is None else tex_bot),
        (top_pts, (0.0, 0.0, 1.0), tex_cap if tex_top is None else tex_top),
    ]
    for k in range(4):
        x0, y0 = poly_u[k]
        x1, y1 = poly_u[(k + 1) % 4]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        if L < 0.25:
            continue
        out = (dy / L, -dx / L, 0.0)  # outward on CCW polygon
        dot = out[0] * n_edge_out[0] + out[1] * n_edge_out[1]
        if dot > 0.70:
            sp = tex_out
        elif dot < -0.70:
            sp = tex_in
        else:
            sp = tex_cap
        s_pts = [(x0, y0, az0), (x1, y1, az0), (x1, y1, az1), (x0, y0, az1)]
        faces.append((s_pts, out, sp))
    mb._emit_brush(faces, group=group, force_world=force_world)


def _emit_sloped_beam_ft(
    mb: MapBuilder,
    ax_ft: float,
    ay_ft: float,
    az0_ft: float,
    az1_ft: float,
    bx_ft: float,
    by_ft: float,
    bz0_ft: float,
    bz1_ft: float,
    width_ft: float,
    tex: TexSpec,
    group: str = "detail",
    tex_top: Optional[TexSpec] = None,
    tex_end_a: Optional[TexSpec] = None,
) -> None:
    """Emit a 6-sided convex sloped beam brush running from endpoint A to B."""
    snap = mb.detail_snap_u
    ax, ay = snap_val(ax_ft * U_FT, snap), snap_val(ay_ft * U_FT, snap)
    bx, by = snap_val(bx_ft * U_FT, snap), snap_val(by_ft * U_FT, snap)
    az0, az1 = snap_val(az0_ft * U_FT, snap), snap_val(az1_ft * U_FT, snap)
    bz0, bz1 = snap_val(bz0_ft * U_FT, snap), snap_val(bz1_ft * U_FT, snap)
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L < 1.0 or (az1 - az0) < 0.5 or (bz1 - bz0) < 0.5:
        return
    ux, uy = dx / L, dy / L
    px, py = -uy, ux  # left perpendicular
    hw = 0.5 * width_ft * U_FT

    al_b = (ax + px * hw, ay + py * hw, az0)
    ar_b = (ax - px * hw, ay - py * hw, az0)
    bl_b = (bx + px * hw, by + py * hw, bz0)
    br_b = (bx - px * hw, by - py * hw, bz0)

    al_t = (ax + px * hw, ay + py * hw, az1)
    ar_t = (ax - px * hw, ay - py * hw, az1)
    bl_t = (bx + px * hw, by + py * hw, bz1)
    br_t = (bx - px * hw, by - py * hw, bz1)

    # Top and bottom normals tilted cleanly along beam slope
    dz_t = bz1 - az1
    nt_len = math.hypot(dz_t, L)
    n_top = (-ux * dz_t / nt_len, -uy * dz_t / nt_len, L / nt_len)

    dz_b = bz0 - az0
    nb_len = math.hypot(dz_b, L)
    n_bot = (ux * dz_b / nb_len, uy * dz_b / nb_len, -L / nb_len)

    faces = [
        ([al_t, bl_t, br_t, ar_t], n_top, tex if tex_top is None else tex_top),
        ([al_b, ar_b, br_b, bl_b], n_bot, tex),
        ([al_b, bl_b, bl_t, al_t], (px, py, 0.0), tex),
        ([ar_b, ar_t, br_t, br_b], (-px, -py, 0.0), tex),
        ([al_b, al_t, ar_t, ar_b], (-ux, -uy, 0.0), tex if tex_end_a is None else tex_end_a),
        ([bl_b, br_b, br_t, bl_t], (ux, uy, 0.0), tex),
    ]
    mb._emit_brush(faces, group=group, force_world=False)


def _oct_pts(cx: float, cy: float, rx: float, ry: float, chamfer: float = 0.42) -> List[Tuple[float, float]]:
    """Return a clean convex stadium/octagon polygon centered at (cx, cy)."""
    cx0, cy0 = rx * (1.0 - chamfer), ry * (1.0 - chamfer)
    return [
        (cx - cx0, cy + ry),
        (cx + cx0, cy + ry),
        (cx + rx, cy + cy0),
        (cx + rx, cy - cy0),
        (cx + cx0, cy - ry),
        (cx - cx0, cy - ry),
        (cx - rx, cy - cy0),
        (cx - rx, cy + cy0),
    ]


def _interp_pt(a: Tuple[float, float], b: Tuple[float, float], t: float) -> Tuple[float, float]:
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def _lerp_x_at_y(a: Tuple[float, float], b: Tuple[float, float], y: float) -> float:
    if abs(b[1] - a[1]) < 1e-6:
        return a[0]
    t = (y - a[1]) / (b[1] - a[1])
    return a[0] + t * (b[0] - a[0])


def _lerp_y_at_x(a: Tuple[float, float], b: Tuple[float, float], x: float) -> float:
    if abs(b[0] - a[0]) < 1e-6:
        return a[1]
    t = (x - a[0]) / (b[0] - a[0])
    return a[1] + t * (b[1] - a[1])


# ---------------------------------------------------------------------------
# 1. Floors (Strictly Disjoint Convex World Slabs, z = -0.5 .. 0.5 ft)
# ---------------------------------------------------------------------------

def _build_floors(mb: MapBuilder) -> None:
    """Emit seamless non-overlapping interior floors matching PERIM_PTS & zones."""
    v00, v01, v02, v03 = PERIM_PTS[0], PERIM_PTS[1], PERIM_PTS[2], PERIM_PTS[3]
    v04, v05, v_ne, v_rn = PERIM_PTS[4], PERIM_PTS[5], PERIM_PTS[6], PERIM_PTS[7]
    v20, v21, v22, v23, v24 = PERIM_PTS[20], PERIM_PTS[21], PERIM_PTS[22], PERIM_PTS[23], PERIM_PTS[24]

    # Snap key boundary intersections on West wall v24->v00 and N wing v02->v03 / v04->v05
    xw_m28 = _snap_ft(_lerp_x_at_y(v24, v00, -28.0))
    xw_p6 = _snap_ft(_lerp_x_at_y(v24, v00, 6.0))
    xw_p58 = _snap_ft(_lerp_x_at_y(v24, v00, 58.0))
    yn_at_div = _snap_ft(_lerp_y_at_x(v02, v03, X_BOH_DIV))

    carpet = Tile("gwc_carpet", w_ft=8.0)
    tile_floor = Tile("gwc_tile", w_ft=4.0)
    conc_floor = Tile("gwc_conc", w_ft=8.0)

    def _slab(pts: Sequence[Tuple[float, float]], tex: TexSpec) -> None:
        snapped = [(_snap_ft(x), _snap_ft(y)) for x, y in pts]
        mb.prism_ft(snapped, FLOOR_BOT_Z, FLOOR_Z, "gwc_dark", tex_top=tex, tex_bot="skip", group="detail", force_world=False)

    # --- East of X_BOH_DIV (-19.0) ---
    # S Notch under BOH/Alcove corner (x=-20.14..-19.0, y=-71.51..-68.77)
    _slab([v22, (-19.0, v22[1]), (-19.0, v23[1]), v23], carpet)

    # Band 1 (South Alcove Carpet & SE Wing Tile): y = -71.6 .. -35.13
    y_se_s = _snap_ft(_lerp_y_at_x(v22, v21, X_SE_WING))
    _slab([(X_BOH_DIV, v22[1]), (X_SE_WING, y_se_s), (X_SE_WING, Y_SE_NORTH), (X_BOH_DIV, Y_SE_NORTH)], carpet)
    _slab([(X_SE_WING, y_se_s), v21, v20, (X_SE_WING, Y_SE_NORTH)], tile_floor)

    # Band 2 (Main Pit South-Center + Rotunda Archway Threshold): y = -35.13 .. -14.17
    y_rot_n = ROTUNDA_V07[1]
    x_arch_w = 42.5
    _slab([(X_BOH_DIV, Y_SE_NORTH), (x_arch_w, Y_SE_NORTH), (x_arch_w, y_rot_n), (X_BOH_DIV, y_rot_n)], carpet)
    _slab([(x_arch_w, Y_SE_NORTH), v20, ROTUNDA_V07, (x_arch_w, y_rot_n)], tile_floor)

    # Band 3 (Middle Main Pit + NE 45-deg Entrance Vestibule): y = -14.17 .. 7.0
    x_vest_w = 34.5
    y_ne_a = NE_STOREFRONT_A[1]
    _slab([(X_BOH_DIV, y_rot_n), (x_vest_w, y_rot_n), (x_vest_w, y_ne_a), (X_BOH_DIV, y_ne_a)], carpet)
    _slab([(x_vest_w, y_rot_n), ROTUNDA_V07, v_rn, v_ne, (x_vest_w, y_ne_a)], tile_floor)

    # Band 4 (Upper Main Pit): y = 7.0 .. 70.52
    _slab([(X_BOH_DIV, y_ne_a), v_ne, v05, (X_BOH_DIV, v05[1])], carpet)

    # Band 5 (North transition trapezoid up to v04 y=71.11 + Northmost Poker Room y=71.11..89.70)
    _slab([(X_BOH_DIV, v05[1]), v05, v04, (X_BOH_DIV, v04[1])], carpet)
    _slab([(X_BOH_DIV, v04[1]), v04, v03, (X_BOH_DIV, yn_at_div)], carpet)

    # --- East 12-sided Rotunda Bar Lounge Floor ---
    rot_pts = [ROTUNDA_V07] + list(PERIM_PTS[7:21])
    _slab(rot_pts, tile_floor)

    # --- West of X_BOH_DIV (-19.0): West BOH, Cashier Vault, Restrooms, Kitchen & NW Room ---
    # SW Service / Prep Hall (concrete): y = -68.77 .. -28.0
    _slab([v24, v23, (X_BOH_DIV, v23[1]), (X_BOH_DIV, -28.0), (xw_m28, -28.0)], conc_floor)
    # Cashier Vault + Restrooms + BOH Hall (tile): y = -28.0 .. 6.0 and 6.0 .. 58.0
    _slab([(xw_m28, -28.0), (X_BOH_DIV, -28.0), (X_BOH_DIV, 6.0), (xw_p6, 6.0)], tile_floor)
    _slab([(xw_p6, 6.0), (X_BOH_DIV, 6.0), (X_BOH_DIV, 58.0), (xw_p58, 58.0)], tile_floor)
    # North BOH / Locker transition up to v00/v01 (y = 58.0 .. 77.61)
    _slab([(xw_p58, 58.0), (X_BOH_DIV, 58.0), (X_BOH_DIV, v00[1]), v00], tile_floor)
    _slab([v00, (X_BOH_DIV, v00[1]), (X_BOH_DIV, v01[1]), v01], tile_floor)
    # NW Wing Kitchen/Poker Extension (y = 77.61 .. 88.99, x = -43.35 .. -19.0)
    _slab([v01, (X_BOH_DIV, v01[1]), (X_BOH_DIV, yn_at_div), v02], conc_floor)


# ---------------------------------------------------------------------------
# 2. Exterior Perimeter Shell, Doorways, Windows & 45-Deg Storefront
# ---------------------------------------------------------------------------

def _emit_perim_wall_with_openings(
    mb: MapBuilder,
    p_out_a: Tuple[float, float],
    p_out_b: Tuple[float, float],
    p_in_a: Tuple[float, float],
    p_in_b: Tuple[float, float],
    z0_ft: float,
    wall_top_ft: float,
    tex_out: TexSpec,
    tex_in: TexSpec,
    openings: Sequence[Tuple[float, float, float, float, str]] = (),
    in_wainscot_z: float = 0.0,
) -> None:
    """Slice a mitered perimeter edge into solid piers, sills, lintels & window/door bays.

    openings entries: (u0, u1, oz0_ft, oz1_ft, kind) where kind in {"door", "window", "blind"}.
    """
    ordered = sorted(openings, key=lambda o: o[0])
    spans: List[Tuple[float, float, Optional[Tuple[float, float, str]]]] = []
    cur_u = 0.0
    for u0, u1, oz0, oz1, kind in ordered:
        u0c = max(0.0, min(1.0, u0))
        u1c = max(u0c, min(1.0, u1))
        if u0c - cur_u > 1e-4:
            spans.append((cur_u, u0c, None))
        if u1c - u0c > 1e-4:
            spans.append((u0c, u1c, (oz0, oz1, kind)))
        cur_u = max(cur_u, u1c)
    if 1.0 - cur_u > 1e-4:
        spans.append((cur_u, 1.0, None))

    def _emit_vertical_layered(ua: float, ub: float, za: float, zb: float, cap_skip: bool = False) -> None:
        oa, ob = _interp_pt(p_out_a, p_out_b, ua), _interp_pt(p_out_a, p_out_b, ub)
        ia, ib = _interp_pt(p_in_a, p_in_b, ua), _interp_pt(p_in_a, p_in_b, ub)
        cap = "skip" if cap_skip else tex_out
        bot_t = "skip" if abs(za - FLOOR_Z) < 1e-4 else tex_out
        if in_wainscot_z > za + 0.1 and zb > in_wainscot_z + 0.1:
            _emit_quad_wall_prism_ft(mb, oa, ob, ia, ib, za, in_wainscot_z, tex_out, Tile("gwc_wainscot", w_ft=4.0), cap, tex_top="skip", tex_bot=bot_t)
            _emit_quad_wall_prism_ft(mb, oa, ob, ia, ib, in_wainscot_z, zb, tex_out, tex_in, cap, tex_top=tex_out, tex_bot="skip")
        else:
            ti = Tile("gwc_wainscot", w_ft=4.0) if (in_wainscot_z > za + 0.1 and zb <= in_wainscot_z + 0.1) else tex_in
            _emit_quad_wall_prism_ft(mb, oa, ob, ia, ib, za, zb, tex_out, ti, cap, tex_top=tex_out, tex_bot=bot_t)

    for idx_s, (u0, u1, op) in enumerate(spans):
        if op is None:
            _emit_vertical_layered(u0, u1, z0_ft, wall_top_ft)
            continue
        oz0, oz1, kind = op
        oa, ob = _interp_pt(p_out_a, p_out_b, u0), _interp_pt(p_out_a, p_out_b, u1)
        ia, ib = _interp_pt(p_in_a, p_in_b, u0), _interp_pt(p_in_a, p_in_b, u1)
        has_pier_a = idx_s > 0 and spans[idx_s - 1][2] is None
        has_pier_b = idx_s + 1 < len(spans) and spans[idx_s + 1][2] is None
        between_piers = has_pier_a and has_pier_b
        if oz0 > z0_ft + 0.08:
            _emit_vertical_layered(u0, u1, z0_ft, oz0, cap_skip=between_piers)
        if wall_top_ft > oz1 + 0.08:
            _emit_vertical_layered(u0, u1, oz1, wall_top_ft, cap_skip=between_piers)

        # Window frame + glass/blinds or open doorway trim
        n_out = _edge_outward_cw(p_out_a, p_out_b)
        mid_a = _interp_pt(oa, ia, 0.5)
        mid_b = _interp_pt(ob, ib, 0.5)
        d_vec = _v_sub(mid_b, mid_a)
        L_span = max(_v_len(d_vec), 1e-4)
        u_dir = _v_mul(d_vec, 1.0 / L_span)
        if kind in ("window", "blind"):
            # Thin dark bronze frame perimeter
            ft = 0.16
            # Bottom sill & top header
            _emit_quad_wall_prism_ft(
                mb, _v_add(mid_a, _v_mul(n_out, 0.25)), _v_add(mid_b, _v_mul(n_out, 0.25)),
                _v_sub(mid_a, _v_mul(n_out, 0.25)), _v_sub(mid_b, _v_mul(n_out, 0.25)),
                oz0, oz0 + ft, "gwc_dark", "gwc_dark", "gwc_dark", tex_bot="skip", group="detail", force_world=False,
            )
            _emit_quad_wall_prism_ft(
                mb, _v_add(mid_a, _v_mul(n_out, 0.25)), _v_add(mid_b, _v_mul(n_out, 0.25)),
                _v_sub(mid_a, _v_mul(n_out, 0.25)), _v_sub(mid_b, _v_mul(n_out, 0.25)),
                oz1 - ft, oz1, "gwc_dark", "gwc_dark", "gwc_dark", tex_top="skip", group="detail", force_world=False,
            )
            # Center vertical mullion if wide
            if L_span >= 5.0:
                mc = _interp_pt(mid_a, mid_b, 0.5)
                ma = _v_sub(mc, _v_mul(u_dir, 0.09))
                mb_pt = _v_add(mc, _v_mul(u_dir, 0.09))
                _emit_quad_wall_prism_ft(
                    mb, _v_add(ma, _v_mul(n_out, 0.22)), _v_add(mb_pt, _v_mul(n_out, 0.22)),
                    _v_sub(ma, _v_mul(n_out, 0.22)), _v_sub(mb_pt, _v_mul(n_out, 0.22)),
                    oz0 + ft, oz1 - ft, "gwc_dark", "gwc_dark", "gwc_dark", tex_top="skip", tex_bot="skip", group="detail", force_world=False,
                )
            # Glazing / blind pane
            pane_tex = Fit("gwc_blind", repeat=(1.0, 1.0)) if kind == "blind" else Tile("gwc_glass", w_ft=4.0)
            pane_grp = "detail" if kind == "blind" else "illus"
            _emit_quad_wall_prism_ft(
                mb, _v_add(mid_a, _v_mul(n_out, 0.06)), _v_add(mid_b, _v_mul(n_out, 0.06)),
                _v_sub(mid_a, _v_mul(n_out, 0.06)), _v_sub(mid_b, _v_mul(n_out, 0.06)),
                oz0 + ft, oz1 - ft, pane_tex, pane_tex, "skip", tex_top="skip", tex_bot="skip", group=pane_grp, force_world=False,
            )


def _u_along_x(a: Tuple[float, float], b: Tuple[float, float], x0: float, x1: float) -> Tuple[float, float]:
    dx = b[0] - a[0]
    u0 = (x0 - a[0]) / dx
    u1 = (x1 - a[0]) / dx
    return (min(u0, u1), max(u0, u1))


def _u_along_y(a: Tuple[float, float], b: Tuple[float, float], y0: float, y1: float) -> Tuple[float, float]:
    dy = b[1] - a[1]
    u0 = (y0 - a[1]) / dy
    u1 = (y1 - a[1]) / dy
    return (min(u0, u1), max(u0, u1))


def _build_ne_storefront(
    mb: MapBuilder,
    p_out_a: Tuple[float, float],
    p_out_b: Tuple[float, float],
    p_in_a: Tuple[float, float],
    p_in_b: Tuple[float, float],
) -> None:
    """Build 45-deg bronze glazed storefront & wide propped-open double doorway."""
    L = _v_len(_v_sub(p_out_b, p_out_a))
    n_out = _edge_outward_cw(p_out_a, p_out_b)
    n_in = (-n_out[0], -n_out[1])
    dir_v = _v_mul(_v_sub(p_out_b, p_out_a), 1.0 / L)

    # Outer corner piers sealing up to z=16.0 (or z=13.0 on last 3 ft Rotunda collar)
    u_left_end = 1.4 / L
    u_right_start = (L - 4.0) / L
    u_rot_step = (L - 1.4) / L

    _emit_quad_wall_prism_ft(
        mb, p_out_a, _interp_pt(p_out_a, p_out_b, u_left_end),
        p_in_a, _interp_pt(p_in_a, p_in_b, u_left_end),
        FLOOR_Z, MAIN_WALL_Z, "gwc_stone", "gwc_white", "gwc_dark", tex_bot="skip",
    )
    # Right end steps from z=16 down to z=13 where storefront joins Rotunda
    _emit_quad_wall_prism_ft(
        mb, _interp_pt(p_out_a, p_out_b, u_right_start), _interp_pt(p_out_a, p_out_b, u_rot_step),
        _interp_pt(p_in_a, p_in_b, u_right_start), _interp_pt(p_in_a, p_in_b, u_rot_step),
        9.8, MAIN_WALL_Z, "gwc_stone", "gwc_white", "gwc_stone", tex_bot="skip",
    )
    _emit_quad_wall_prism_ft(
        mb, _interp_pt(p_out_a, p_out_b, u_right_start), _interp_pt(p_out_a, p_out_b, u_rot_step),
        _interp_pt(p_in_a, p_in_b, u_right_start), _interp_pt(p_in_a, p_in_b, u_rot_step),
        FLOOR_Z, 9.8, "gwc_dark", "gwc_dark", "gwc_dark", tex_top="skip", tex_bot="skip",
    )
    _emit_quad_wall_prism_ft(
        mb, _interp_pt(p_out_a, p_out_b, u_rot_step), p_out_b,
        _interp_pt(p_in_a, p_in_b, u_rot_step), p_in_b,
        FLOOR_Z, ROTUNDA_WALL_Z, "gwc_stone", "gwc_istone", "gwc_dark", tex_bot="skip",
    )

    # Upper facade wall over entire glazed storefront bay (z=9.8..16.0)
    _emit_quad_wall_prism_ft(
        mb, _interp_pt(p_out_a, p_out_b, u_left_end), _interp_pt(p_out_a, p_out_b, u_right_start),
        _interp_pt(p_in_a, p_in_b, u_left_end), _interp_pt(p_in_a, p_in_b, u_right_start),
        10.2, MAIN_WALL_Z, Tile("gwc_crmstuc", w_ft=8.0), Tile("gwc_white", w_ft=8.0), "gwc_stone", tex_bot="skip",
    )
    # Dark bronze storefront transom header (z=9.4..10.2)
    _emit_quad_wall_prism_ft(
        mb, _interp_pt(p_out_a, p_out_b, u_left_end), _interp_pt(p_out_a, p_out_b, u_right_start),
        _interp_pt(p_in_a, p_in_b, u_left_end), _interp_pt(p_in_a, p_in_b, u_right_start),
        DOOR_TOP_Z - 0.1, 10.2, "gwc_dark", "gwc_dark", "gwc_dark", tex_top="skip",
    )

    # Doorway opening occupies s = 8.4 .. 18.8 ft (10.4 ft = 124.8u wide x 9.0 ft = 108u high!)
    s_d0, s_d1 = 8.4, 18.8
    # Left & right glazed sidelight bays (s=1.4..8.4 and s=18.8..L-4.0)
    for sa, sb in ((1.4, s_d0), (s_d1, L - 4.0)):
        ua, ub = sa / L, sb / L
        # Lower dark bronze kickplate (z=0.5..1.1)
        _emit_quad_wall_prism_ft(
            mb, _interp_pt(p_out_a, p_out_b, ua), _interp_pt(p_out_a, p_out_b, ub),
            _interp_pt(p_in_a, p_in_b, ua), _interp_pt(p_in_a, p_in_b, ub),
            FLOOR_Z, 1.1, "gwc_dark", "gwc_dark", "gwc_dark", tex_bot="skip",
        )
        # Glazed sidelight center strip
        ma = _interp_pt(_interp_pt(p_out_a, p_out_b, ua), _interp_pt(p_in_a, p_in_b, ua), 0.5)
        mb_pt = _interp_pt(_interp_pt(p_out_a, p_out_b, ub), _interp_pt(p_in_a, p_in_b, ub), 0.5)
        _emit_quad_wall_prism_ft(
            mb, _v_add(ma, _v_mul(n_out, 0.07)), _v_add(mb_pt, _v_mul(n_out, 0.07)),
            _v_sub(ma, _v_mul(n_out, 0.07)), _v_sub(mb_pt, _v_mul(n_out, 0.07)),
            1.1, DOOR_TOP_Z - 0.1, Tile("gwc_glass", w_ft=4.0), Tile("gwc_glass", w_ft=4.0), "skip",
            tex_top="skip", tex_bot="skip", group="illus", force_world=False,
        )
        # Vertical bronze mullions along sidelight & jambs
        for sm in (sa + 0.15, 0.5 * (sa + sb), sb - 0.15):
            mc = _interp_pt(_interp_pt(p_out_a, p_out_b, sm / L), _interp_pt(p_in_a, p_in_b, sm / L), 0.5)
            m0 = _v_sub(mc, _v_mul(dir_v, 0.15))
            m1 = _v_add(mc, _v_mul(dir_v, 0.15))
            _emit_quad_wall_prism_ft(
                mb, _v_add(m0, _v_mul(n_out, 0.30)), _v_add(m1, _v_mul(n_out, 0.30)),
                _v_sub(m0, _v_mul(n_out, 0.30)), _v_sub(m1, _v_mul(n_out, 0.30)),
                1.1, DOOR_TOP_Z - 0.1, "gwc_dark", "gwc_dark", "gwc_dark",
                tex_top="skip", tex_bot="skip", group="detail", force_world=False,
            )

    # Propped-open double glazed entrance doors swung 85 deg inward at s_d0 and s_d1
    # Leaves occupy < 0.7 ft laterally so >= 9.0 ft (108u) center walk stays wide open!
    for s_jamb, inward_sign in ((s_d0 + 0.25, 1.0), (s_d1 - 0.25, -1.0)):
        u_j = s_jamb / L
        j_pt = _interp_pt(_interp_pt(p_out_a, p_out_b, u_j), _interp_pt(p_in_a, p_in_b, u_j), 0.55)
        leaf_dir = _v_add(_v_mul(n_in, 0.985), _v_mul(dir_v, inward_sign * 0.17))
        leaf_dir = _v_mul(leaf_dir, 1.0 / max(_v_len(leaf_dir), 1e-6))
        leaf_perp = (-leaf_dir[1], leaf_dir[0])
        tip = _v_add(j_pt, _v_mul(leaf_dir, 3.4))
        ht = 0.11
        # Bronze frame stiles + lower rail + glass + PUSH TO OPEN decal
        _emit_quad_wall_prism_ft(
            mb, _v_add(j_pt, _v_mul(leaf_perp, ht)), _v_add(tip, _v_mul(leaf_perp, ht)),
            _v_sub(j_pt, _v_mul(leaf_perp, ht)), _v_sub(tip, _v_mul(leaf_perp, ht)),
            0.55, 1.4, "gwc_dark", "gwc_dark", "gwc_dark", group="detail", force_world=False,
        )
        _emit_quad_wall_prism_ft(
            mb, _v_add(j_pt, _v_mul(leaf_perp, ht)), _v_add(tip, _v_mul(leaf_perp, ht)),
            _v_sub(j_pt, _v_mul(leaf_perp, ht)), _v_sub(tip, _v_mul(leaf_perp, ht)),
            8.2, 8.8, "gwc_dark", "gwc_dark", "gwc_dark", group="detail", force_world=False,
        )
        # Door glass + "PUSH TO OPEN" graphic placard at waist/chest height
        _emit_quad_wall_prism_ft(
            mb, _v_add(j_pt, _v_mul(leaf_perp, 0.05)), _v_add(tip, _v_mul(leaf_perp, 0.05)),
            _v_sub(j_pt, _v_mul(leaf_perp, 0.05)), _v_sub(tip, _v_mul(leaf_perp, 0.05)),
            1.4, 8.2, Tile("gwc_glass", w_ft=4.0), Tile("gwc_glass", w_ft=4.0), "gwc_dark",
            tex_top="skip", tex_bot="skip", group="illus", force_world=False,
        )
        p_mid0 = _v_add(j_pt, _v_mul(leaf_dir, 0.8))
        p_mid1 = _v_add(j_pt, _v_mul(leaf_dir, 2.8))
        _emit_quad_wall_prism_ft(
            mb, _v_add(p_mid0, _v_mul(leaf_perp, 0.07)), _v_add(p_mid1, _v_mul(leaf_perp, 0.07)),
            _v_sub(p_mid0, _v_mul(leaf_perp, 0.07)), _v_sub(p_mid1, _v_mul(leaf_perp, 0.07)),
            4.2, 5.2, Fit("gwc_pushtoop"), Fit("gwc_pushtoop"), "gwc_dark",
            group="illus", force_world=False,
        )

    # Sidelight "PUSH TO OPEN" plaques readable straight from plaza
    for s_p0, s_p1 in ((5.8, 7.6), (19.6, 21.4)):
        pa = _interp_pt(p_out_a, p_out_b, s_p0 / L)
        pb = _interp_pt(p_out_a, p_out_b, s_p1 / L)
        _emit_quad_wall_prism_ft(
            mb, _v_add(pa, _v_mul(n_out, 0.02)), _v_add(pb, _v_mul(n_out, 0.02)),
            _v_sub(pa, _v_mul(n_out, 0.56)), _v_sub(pb, _v_mul(n_out, 0.56)),
            4.3, 5.3, Fit("gwc_pushtoop"), Fit("gwc_pushtoop"), "gwc_dark",
            group="illus", force_world=False,
        )

    d_center = _interp_pt(p_out_a, p_out_b, 0.5 * (s_d0 + s_d1) / L)
    mb.register_doorway_ft(
        "casino_ne_main_entrance",
        width_ft=s_d1 - s_d0 - 1.4,
        height_ft=DOOR_TOP_Z - FLOOR_Z,
        origin_ft=(d_center[0], d_center[1], FLOOR_Z),
        axis="x",
    )


def _build_exterior_walls(mb: MapBuilder) -> None:
    """Build all 25 mitered perimeter shell segments + exterior windows/exits."""
    p_in = _compute_inner_miter_ring(PERIM_PTS, WALL_T)
    n = len(PERIM_PTS)
    stone_out = Tile("gwc_stone", w_ft=8.0)
    stone_in = Tile("gwc_istone", w_ft=8.0)
    white_in = Tile("gwc_white", w_ft=8.0)

    # Edges 2 (N wing top), 4 (N lot exit), 8..19 (Rotunda), 20 (SE East), 21 (South), 23 (SW)
    for i in range(n):
        a_out, b_out = PERIM_PTS[i], PERIM_PTS[(i + 1) % n]
        a_in, b_in = p_in[i], p_in[(i + 1) % n]

        if i == 6:
            _build_ne_storefront(mb, a_out, b_out, a_in, b_in)
            continue

        top_z = ROTUNDA_WALL_Z if ROTUNDA_FIRST_EDGE <= i <= ROTUNDA_LAST_EDGE else MAIN_WALL_Z
        in_tex: TexSpec = white_in if i in (0, 1, 24) else stone_in
        wain_z = 3.8 if (i in (3, 4, 5, 20, 21) or ROTUNDA_FIRST_EDGE <= i <= ROTUNDA_LAST_EDGE) else 0.0
        openings: List[Tuple[float, float, float, float, str]] = []

        if i == 2:
            # Northmost Poker Alcove: 3 tall vertical shaded windows
            for wx0, wx1 in ((-14.0, -10.5), (-8.5, -5.0), (-2.5, 1.0)):
                u0, u1 = _u_along_x(a_out, b_out, wx0, wx1)
                openings.append((u0, u1, 2.8, 10.5, "blind"))
        elif i == 4:
            # North Poker Wall facing N Lot: 4 tall shaded windows + N Lot Exit (x=20..28)
            for wx0, wx1 in ((9.8, 12.8), (14.5, 17.5), (32.0, 35.5), (37.0, 39.5)):
                u0, u1 = _u_along_x(a_out, b_out, wx0, wx1)
                openings.append((u0, u1, 2.8, 10.5, "blind"))
            du0, du1 = _u_along_x(a_out, b_out, NORTH_EXIT_X[0], NORTH_EXIT_X[1])
            openings.append((du0, du1, FLOOR_Z, DOOR_TOP_Z, "door"))
            mb.register_doorway_ft(
                "casino_north_lot_exit",
                width_ft=NORTH_EXIT_X[1] - NORTH_EXIT_X[0],
                height_ft=DOOR_TOP_Z - FLOOR_Z,
                origin_ft=(0.5 * (NORTH_EXIT_X[0] + NORTH_EXIT_X[1]), 70.8, FLOOR_Z),
                axis="x",
            )
        elif i in (9, 10, 11, 16, 17):
            # Rotunda Courtyard & South multi-pane windows (leaving East 12..15 solid for back-bar!)
            L_seg = _v_len(_v_sub(b_out, a_out))
            if L_seg >= 7.0:
                margin = 1.6 / L_seg
                openings.append((margin, 1.0 - margin, 3.6, 9.6, "window"))
        elif i == 20:
            # SE Wing East Wall: multi-pane commercial window overlooking south patio
            u0, u1 = _u_along_y(a_out, b_out, -65.0, -50.0)
            openings.append((u0, u1, 3.2, 9.2, "window"))
        elif i == 21:
            # South Exterior Wall: Buddha window (-12.5..-3.5), East blind window (4.5..13.5), S Exit (24..34)
            u_b0, u_b1 = _u_along_x(a_out, b_out, -12.5, -3.5)
            u_w0, u_w1 = _u_along_x(a_out, b_out, 4.5, 13.5)
            u_d0, u_d1 = _u_along_x(a_out, b_out, SOUTH_EXIT_X[0], SOUTH_EXIT_X[1])
            openings.extend([
                (u_d0, u_d1, FLOOR_Z, DOOR_TOP_Z, "door"),
                (u_w0, u_w1, 4.0, 9.0, "blind"),
                (u_b0, u_b1, 4.0, 9.0, "blind"),
            ])
            mb.register_doorway_ft(
                "casino_south_center_exit",
                width_ft=SOUTH_EXIT_X[1] - SOUTH_EXIT_X[0],
                height_ft=DOOR_TOP_Z - FLOOR_Z,
                origin_ft=(0.5 * (SOUTH_EXIT_X[0] + SOUTH_EXIT_X[1]), -71.6, FLOOR_Z),
                axis="x",
            )
        elif i == 23:
            # SW BOH Wall: SW Rear Service Exit (x=-42..-34, y=-68.4)
            du0, du1 = _u_along_x(a_out, b_out, SW_EXIT_X[0], SW_EXIT_X[1])
            openings.append((du0, du1, FLOOR_Z, DOOR_TOP_Z, "door"))
            mb.register_doorway_ft(
                "casino_sw_service_exit",
                width_ft=SW_EXIT_X[1] - SW_EXIT_X[0],
                height_ft=DOOR_TOP_Z - FLOOR_Z,
                origin_ft=(0.5 * (SW_EXIT_X[0] + SW_EXIT_X[1]), -68.5, FLOOR_Z),
                axis="x",
            )

        _emit_perim_wall_with_openings(
            mb, a_out, b_out, a_in, b_in,
            FLOOR_Z, top_z, stone_out, in_tex,
            openings=openings, in_wainscot_z=wain_z,
        )

    # SE Wing Exterior Bronze Golden West Casino Wall Plaque on East Wall (edge 20, x~54.5, y=-44..-39)
    mb.box_ft(54.45, -44.8, 4.4, 54.65, -39.2, 7.2, "gwc_dark", faces={"w": "skip"}, group="detail")
    mb.sign_decal_ft("e", 54.65, -44.4, -39.6, 4.7, 6.9, Fit("gwc_goldwin"))

    # South Center Exit & North Lot Exit propped-open frame/trim accents (non-blocking)
    mb.box_ft(SOUTH_EXIT_X[0], -71.55, DOOR_TOP_Z - 0.1, SOUTH_EXIT_X[1], -70.65, DOOR_TOP_Z + 0.35, "gwc_dark", group="detail")
    mb.box_ft(NORTH_EXIT_X[0], 70.35, DOOR_TOP_Z - 0.1, NORTH_EXIT_X[1], 71.25, DOOR_TOP_Z + 0.35, "gwc_dark", group="detail")
    mb.box_ft(SW_EXIT_X[0], -68.65, DOOR_TOP_Z - 0.1, SW_EXIT_X[1], -67.75, DOOR_TOP_Z + 0.35, "gwc_galv", group="detail")
    # Decorative east stone pilasters on East Main Pit wall (x=41.5..42.4)
    for py in (20.0, 36.0, 52.0):
        mb.box_ft(41.1, py - 1.0, FLOOR_Z, 41.8, py + 1.0, 12.6, Tile("gwc_istone", w_ft=4.0), faces={"b": "skip", "e": "skip"}, group="detail")


# ---------------------------------------------------------------------------
# 3. West Cashier / Chip Cage & West BOH Wing (Restrooms, Kitchen, SW Hall)
# ---------------------------------------------------------------------------

def _emit_int_wall_ft(
    mb: MapBuilder,
    axis: str,
    pos_ft: float,
    s0_ft: float,
    s1_ft: float,
    z0_ft: float,
    z1_ft: float,
    thick_ft: float,
    tex: TexSpec,
    doorways: Sequence[Tuple[float, float, float, str]] = (),
    windows: Sequence[Tuple[float, float, float, float]] = (),
    tex_inside: Optional[TexSpec] = None,
) -> None:
    """Emit an interior func_detail partition wall skipping buried floor/roof/sill/lintel joints."""
    s0, s1 = sorted((s0_ft, s1_ft))
    z0, z1 = sorted((z0_ft, z1_ft))
    ht = 0.5 * thick_ft

    def _emit_panel(ps0: float, ps1: float, pz0: float, pz1: float, end_skip: bool = False) -> None:
        if ps1 - ps0 < 0.04 or pz1 - pz0 < 0.04:
            return
        faces: Dict[str, TexSpec] = {}
        if tex_inside is not None:
            if axis == "x":
                faces["n"] = tex
                faces["s"] = tex_inside
            else:
                faces["e"] = tex
                faces["w"] = tex_inside
        if abs(pz0 - z0) < 1e-4:
            faces["b"] = "skip"
        if abs(pz1 - z1) < 1e-4:
            faces["t"] = "skip"
        if end_skip:
            if axis == "x":
                faces["w"] = "skip"
                faces["e"] = "skip"
            else:
                faces["s"] = "skip"
                faces["n"] = "skip"
        if axis == "x":
            mb.box_ft(ps0, pos_ft - ht, pz0, ps1, pos_ft + ht, pz1, tex, faces=faces, group="detail")
        else:
            mb.box_ft(pos_ft - ht, ps0, pz0, pos_ft + ht, ps1, pz1, tex, faces=faces, group="detail")

    openings: List[Tuple[float, float, float, float]] = []
    for d0, d1, d_top, dname in doorways:
        a0, a1 = sorted((float(d0), float(d1)))
        orig = (0.5 * (a0 + a1), pos_ft, z0) if axis == "x" else (pos_ft, 0.5 * (a0 + a1), z0)
        mb.register_doorway_ft(dname, a1 - a0, float(d_top) - z0, origin_ft=orig, axis=axis)
        openings.append((a0, a1, z0, float(d_top)))
    for w0, w1, wz0, wz1 in windows:
        a0, a1 = sorted((float(w0), float(w1)))
        b0, b1 = sorted((float(wz0), float(wz1)))
        openings.append((a0, a1, b0, b1))

    openings.sort(key=lambda o: o[0])
    cursor = s0
    for o0, o1, oz0, oz1 in openings:
        o0c, o1c = max(s0, o0), min(s1, o1)
        if o1c <= o0c:
            continue
        if o0c > cursor + 1e-4:
            _emit_panel(cursor, o0c, z0, z1)
        has_a = o0c > s0 + 1e-4
        has_b = o1c < s1 - 1e-4
        both_piers = has_a and has_b
        if oz0 > z0 + 1e-4:
            _emit_panel(o0c, o1c, z0, min(oz0, z1), end_skip=both_piers)
        if oz1 < z1 - 1e-4:
            _emit_panel(o0c, o1c, max(oz1, z0), z1, end_skip=both_piers)
        cursor = max(cursor, o1c)
    if cursor + 1e-4 < s1:
        _emit_panel(cursor, s1, z0, z1)


def _build_west_boh_and_cage(mb: MapBuilder) -> None:
    """Build X_BOH_DIV wall, 2 corrugated shutter teller bays, Vault, Restrooms & Kitchen."""
    stone_in = Tile("gwc_istone", w_ft=8.0)
    white_wall = Tile("gwc_white", w_ft=8.0)
    tile_wall = Tile("gwc_tile", w_ft=4.0)

    # 3A. Main N-S dividing wall along x = -19.0..-18.0 (y = -68.77 .. +77.6)
    # Interior partitions cap at z=15.1667 ft (182u) flush against _deck bottom (0 overlap with deck sides/top).
    PART_WALL_Z = 15.1667
    # South solid span (-68.8 .. -35.0) & South BOH Service Door (-35.0 .. -27.5)
    _emit_int_wall_ft(
        mb, "y", -18.5, -68.77, -25.5, FLOOR_Z, PART_WALL_Z, 1.0, stone_in,
        doorways=[(-35.0, -27.5, DOOR_TOP_Z, "casino_west_boh_south_door")],
        tex_inside=white_wall,
    )
    # Trim & wood door leaf propped open inside South BOH door (-35.0..-27.5)
    mb.box_ft(-22.2, -35.1, FLOOR_Z, -19.0, -34.85, 8.8, Fit("gwc_wooddoor"), faces={"b": "skip"}, group="detail")

    # Cashier Cage Teller Wall (-25.5 .. +7.0) w/ 2 Teller Windows:
    # Bay 1: y = -20.5 .. -11.5 (9 ft wide), Bay 2: y = -5.5 .. +3.5 (9 ft wide)
    _emit_int_wall_ft(
        mb, "y", -18.5, -25.5, 7.0, FLOOR_Z, PART_WALL_Z, 1.0, stone_in,
        windows=[(-20.5, -11.5, 3.6, 9.5), (-5.5, 3.5, 3.6, 9.5)],
        tex_inside=white_wall,
    )

    # Cage bay counters, granite/leather ledges, corrugated roll-down shutters & chip racks
    for idx, (by0, by1, shut_bot) in enumerate(((-20.5, -11.5, 5.4), (-5.5, 3.5, 6.2))):
        # Lower stone apron + speckled granite deal ledge + black padded rail (z=0.5..3.75)
        mb.box_ft(-19.5, by0 - 0.3, FLOOR_Z, -17.3, by1 + 0.3, 3.5, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip", "t": "skip"}, group="detail")
        mb.box_ft(-19.6, by0 - 0.4, 3.5, -17.0, by1 + 0.4, 3.78, Fit("gwc_cledge"), group="detail")
        mb.box_ft(-17.3, by0 - 0.4, 3.45, -16.85, by1 + 0.4, 3.82, Tile("gwc_leather", w_ft=2.0), group="detail")
        # Corrugated metal roll-down security shutter in upper bay
        mb.box_ft(-18.7, by0, shut_bot, -18.2, by1, 9.5, Tile("gwc_cageshut", w_ft=4.0), faces={"s": "skip", "n": "skip", "t": "skip"}, group="detail")
        # Security glass between ledge and shutter bottom bar
        mb.box_ft(-18.52, by0, 3.78, -18.42, by1, shut_bot, Tile("gwc_glass", w_ft=4.0), faces={"s": "skip", "n": "skip", "b": "skip", "t": "skip"}, group="illus")
        # Interior teller desk + chip rack inside cage
        yc = 0.5 * (by0 + by1)
        mb.box_ft(-21.8, by0 + 1.0, FLOOR_Z, -19.5, by1 - 1.0, 3.3, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip"}, group="detail")
        mb.box_ft(-20.8, yc - 1.6, 3.3, -19.7, yc + 1.6, 3.85, Fit("gwc_chiprack"), faces={"b": "skip"}, group="detail")

    # Overhead glowing "CASHIER" sign centered over both teller bays facing East (+X)
    # Matches gwc_cashier 4:1 (512x128 / 256x64) natural aspect ratio (7.2 x 1.8 ft)
    # and stays below z=12.0 cross-beams (y=-12.1..-4.9, z=9.5..11.3) for zero overlap.
    mb.box_ft(-18.02, -12.3, 9.3, -17.60, -4.7, 11.45, "gwc_dark", faces={"w": "skip"}, group="detail")
    mb.sign_decal_ft("e", -17.60, -12.1, -4.9, 9.5, 11.3, Fit("gwc_cashier"))
    # Framed promo banner on center stone pier between bays (y = -11.0..-6.0)
    mb.sign_decal_ft("e", -18.00, -10.5, -6.5, 4.8, 8.2, Fit("gwc_goldwin"))

    # Kitchen/North BOH section (+7.0 .. +58.0) w/ open Kitchen Service Doorway (y=19.0..26.5)
    # Plus North Archway (+58.0 .. +68.0) & North pier (+68.0 .. +77.6)
    _emit_int_wall_ft(
        mb, "y", -18.5, 7.0, 77.6, FLOOR_Z, PART_WALL_Z, 1.0, stone_in,
        doorways=[(19.0, 26.5, DOOR_TOP_Z, "casino_west_boh_kitchen_door"), (58.0, 68.0, 10.5, "casino_nw_archway")],
        tex_inside=white_wall,
    )
    mb.box_ft(-22.2, 18.9, FLOOR_Z, -19.0, 19.15, 8.8, Fit("gwc_wooddoor"), faces={"b": "skip"}, group="detail")

    # 3B. Cashier Cage Vault Interior Partition (x=-33.0, y=-25.5..+7.0, plus South & North walls)
    _emit_int_wall_ft(mb, "y", X_CAGE_BACK, -25.5, 7.0, FLOOR_Z, PART_WALL_Z, 0.8, white_wall)
    _emit_int_wall_ft(
        mb, "x", -25.5, X_CAGE_BACK, -19.0, FLOOR_Z, PART_WALL_Z, 0.8, white_wall,
        doorways=[(-30.5, -23.5, DOOR_TOP_Z, "casino_cashier_vault_door")],
    )
    _emit_int_wall_ft(mb, "x", 7.0, X_CAGE_BACK, -19.0, FLOOR_Z, PART_WALL_Z, 0.8, white_wall)
    # Vault back counter, chip racks & twin heavy steel safes
    mb.box_ft(-32.4, -18.0, FLOOR_Z, -29.8, -2.0, 3.5, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(-32.4, -18.0, 3.5, -29.8, -2.0, 3.7, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip"}, group="detail")
    mb.box_ft(-32.0, -14.0, 3.7, -30.2, -9.0, 4.3, Fit("gwc_chiprack"), faces={"b": "skip"}, group="detail")
    mb.box_ft(-32.5, -0.5, FLOOR_Z, -29.6, 5.8, 6.8, Tile("gwc_steel", w_ft=4.0), faces={"b": "skip"}, group="detail")

    # 3C. Restrooms Block (x = -52.8..-41.0, y = -25.5 .. +5.5) along 8 ft BOH corridor (x=-41..-33)
    _emit_int_wall_ft(
        mb, "y", X_CORR_W, -25.5, 6.0, FLOOR_Z, PART_WALL_Z, 0.8, white_wall,
        doorways=[(-21.5, -14.5, DOOR_TOP_Z, "casino_restroom_south_door"), (-6.0, 1.0, DOOR_TOP_Z, "casino_restroom_north_door")],
        tex_inside=tile_wall,
    )
    _emit_int_wall_ft(mb, "x", -25.5, -52.8, X_CORR_W, FLOOR_Z, PART_WALL_Z, 0.8, tile_wall)
    _emit_int_wall_ft(mb, "x", -10.0, -52.8, X_CORR_W, FLOOR_Z, PART_WALL_Z, 0.8, tile_wall)
    _emit_int_wall_ft(mb, "x", 6.0, -52.8, X_CORR_W, FLOOR_Z, PART_WALL_Z, 0.8, tile_wall)
    # Vanity counters & clean enclosed stall cubicles against west wall (wide open entry floor)
    for ry0, ry1 in ((-25.0, -10.4), (-9.6, 5.6)):
        mb.box_ft(-52.5, ry0 + 0.6, FLOOR_Z, -50.8, ry0 + 7.2, 3.2, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip", "w": "skip"}, group="detail")
        mb.box_ft(-52.5, ry0 + 0.8, 3.6, -52.2, ry0 + 7.0, 6.8, Tile("gwc_steel", w_ft=2.0), faces={"w": "skip"}, group="detail")
        mb.box_ft(-52.5, ry1 - 5.2, FLOOR_Z, -48.6, ry1 - 0.6, 6.8, Tile("gwc_steel", w_ft=4.0), faces={"b": "skip", "w": "skip"}, group="detail")

    # 3D. Kitchen / Prep Hallway & NW Wing (y = +7 .. +77)
    # Partition dividing Kitchen (y=7..58) from NW Wing/North Poker (y=58..88) with open 10 ft portal
    _emit_int_wall_ft(
        mb, "x", 58.0, -53.2, X_BOH_DIV, FLOOR_Z, PART_WALL_Z, 0.8, white_wall,
        doorways=[(-38.0, -28.0, DOOR_TOP_Z, "casino_kitchen_north_portal")],
    )
    # Stainless steel prep island (x=-48.5..-44.5, y=22..36 -> 5 ft+ clearance on every side!)
    mb.box_ft(-48.5, 22.0, FLOOR_Z, -44.5, 36.0, 3.2, Tile("gwc_galv", w_ft=4.0), faces={"b": "skip"}, group="detail")
    mb.box_ft(-49.0, 21.5, 7.6, -44.0, 36.5, 11.8, Tile("gwc_galv", w_ft=4.0), group="detail")
    # Employee lockers & prep counter along West wall (y = 42..55) + kitchen snack board on Vault North wall
    mb.box_ft(-53.4, 41.0, FLOOR_Z, -51.0, 55.0, 6.6, Tile("gwc_steel", w_ft=4.0), faces={"b": "skip", "w": "skip"}, group="detail")
    mb.sign_decal_ft("n", 7.4, -29.0, -23.0, 4.8, 7.6, Fit("gwc_menu"))

    # SW Utility Shelf against West wall clear of SW exit
    mb.box_ft(-52.8, -58.0, FLOOR_Z, -50.2, -40.0, 6.5, Tile("gwc_galv", w_ft=4.0), faces={"b": "skip", "w": "skip"}, group="detail")


# ---------------------------------------------------------------------------
# 4. SE Stone Wing & NE Entrance Vestibule Security/Host Podium
# ---------------------------------------------------------------------------

def _build_se_wing_and_vestibule(mb: MapBuilder) -> None:
    """Build SE Employee Office/Break Wing and NE Vestibule Security/Host Podium."""
    stone_in = Tile("gwc_istone", w_ft=8.0)
    white_wall = Tile("gwc_white", w_ft=8.0)

    # SE Office/Break Wing enclosed by X_SE_WING (36.0) & Y_SE_NORTH (-35.13)
    # Open "EMPLOYEES ONLY" doorway on North wall (x=42..49) + West exit door (y=-59..-52)
    _emit_int_wall_ft(
        mb, "x", Y_SE_NORTH, X_SE_WING, 54.35, FLOOR_Z, 15.1667, 0.9, stone_in,
        doorways=[(42.0, 49.0, DOOR_TOP_Z, "casino_se_employees_door")],
        tex_inside=white_wall,
    )
    _emit_int_wall_ft(
        mb, "y", X_SE_WING, -70.8, Y_SE_NORTH, FLOOR_Z, 15.1667, 0.9, white_wall,
        doorways=[(-59.5, -52.0, DOOR_TOP_Z, "casino_se_west_door")],
        tex_inside=stone_in,
    )
    # "EMPLOYEES ONLY" sign above the North SE Wing doorway facing Rotunda/Main Pit
    mb.sign_decal_ft("n", Y_SE_NORTH + 0.48, 43.2, 47.8, 7.6, 8.6, Fit("gwc_emponly"))
    # Open propped door leaf inside West doorway
    mb.box_ft(36.6, -52.2, FLOOR_Z, 39.6, -51.95, 8.8, Fit("gwc_wooddoor"), faces={"b": "skip"}, group="detail")

    # Manager's Desk, Computer Monitor, Chair & Break Table inside SE Wing
    mb.box_ft(45.5, -67.0, FLOOR_Z, 51.0, -63.0, 3.0, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(45.5, -67.0, 3.0, 51.0, -63.0, 3.2, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip"}, group="detail")
    mb.box_ft(47.2, -65.4, 3.2, 49.4, -64.8, 4.6, Fit("gwc_tvscr"), faces={"b": "skip"}, group="detail")
    # Employee break table (center x=45, y=-46)
    mb.box_ft(43.5, -48.0, FLOOR_Z, 47.5, -44.0, 3.0, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip"}, group="detail")

    # --- NE Vestibule Security/Host Podium & Indoor Palms (x=35..58, y=-14..+6) ---
    # White drywall corner accent column near NW corner of Vestibule (x=41.5..43.2, y=6.5..8.2)
    mb.box_ft(41.2, 6.2, FLOOR_Z, 43.0, 8.0, 12.2, white_wall, faces={"b": "skip", "t": "skip"}, group="detail")

    # Mahogany & Granite Security/Host Podium standing at (37.5, -5.0) facing NE (+X/+Y)
    px0, py0, px1, py1 = 35.6, -8.5, 39.2, -2.5
    mb.box_ft(px0, py0, FLOOR_Z, px1, py1, 3.7, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(px0 - 0.15, py0 - 0.15, 3.7, px1 + 0.15, py1 + 0.15, 4.0, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip"}, group="detail")
    # Small host security screen & rule podium
    mb.box_ft(36.8, -6.2, 4.0, 38.0, -4.6, 5.1, Fit("gwc_tvscr"), faces={"b": "skip"}, group="detail")
    mb.box_ft(40.0, 1.8, FLOOR_Z, 41.8, 3.6, 4.1, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip"}, group="detail")

    # Framed glowing "SECURITY" overhead plaque hanging from Vestibule ceiling above podium
    mb.box_ft(37.1, -8.2, 8.7, 37.7, -2.8, 10.4, "gwc_dark", group="detail")
    mb.box_ft(37.3, -7.8, 10.4, 37.5, -7.6, 12.2, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(37.3, -3.4, 10.4, 37.5, -3.2, 12.2, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")
    mb.sign_decal_ft("e", 37.70, -8.0, -3.0, 8.85, 10.25, Fit("gwc_security"))
    mb.sign_decal_ft("w", 37.10, -8.0, -3.0, 8.85, 10.25, Fit("gwc_security"))

    # Two potted indoor palms flanking the 45-deg sidelights (clear of doorway walk)
    for cx, cy in ((44.8, 4.2), (57.6, -9.8)):
        mb.box_ft(cx - 1.1, cy - 1.1, FLOOR_Z, cx + 1.1, cy + 1.1, 2.7, Tile("gwc_stone", w_ft=4.0), faces={"b": "skip"}, group="detail")
        mb.box_ft(cx - 0.25, cy - 0.25, 2.7, cx + 0.25, cy + 0.25, 6.0, Tile("gwc_wood", w_ft=2.0), faces={"b": "skip"}, group="detail")
        mb.box_ft(cx - 1.7, cy - 0.12, 4.5, cx + 1.7, cy + 0.12, 7.6, Fit("{gwc_palmfr"), group="fence")
        mb.box_ft(cx - 0.12, cy - 1.7, 4.5, cx + 0.12, cy + 1.7, 7.6, Fit("{gwc_palmfr"), group="fence")


# ---------------------------------------------------------------------------
# 5. Rotunda Blackjack Lounge Bar & Courtyard Lounge Seating
# ---------------------------------------------------------------------------

def _build_rotunda_bar(mb: MapBuilder) -> None:
    """Build 3-bay dark mahogany back-bar, cyan neon, curved granite bar & barstools."""
    cx, cy = CASINO_ROTUNDA_CENTER_FT  # (78.9, -25.5)

    # Wide Rotunda Archway Header spanning v07 (60.56,-14.17) -> v20 (54.76,-35.13)
    # Leaves z=0.5..11.2 (128.4u!) open for entry & sightline; seals z=11.2..16.0
    _emit_quad_wall_prism_ft(
        mb, (61.2, -13.9), (55.4, -34.9),
        (59.9, -14.4), (54.1, -35.3),
        11.2, MAIN_WALL_Z, Tile("gwc_istone", w_ft=8.0), Tile("gwc_istone", w_ft=8.0),
        "gwc_beam", group="detail", force_world=False,
    )
    # Dark wood archway casing pilasters on north/south jambs
    mb.prism_ft([(59.6, -15.3), (61.1, -13.6), (62.0, -14.8), (60.5, -16.4)], FLOOR_Z, 11.4, Tile("gwc_beam", w_ft=4.0), tex_bot="skip", group="detail")
    mb.prism_ft([(54.2, -35.3), (55.7, -33.6), (56.6, -34.8), (55.1, -36.4)], FLOOR_Z, 11.4, Tile("gwc_beam", w_ft=4.0), tex_bot="skip", group="detail")

    # 3-Bay Dark Mahogany Mirrored Back-Bar along East Rotunda arc (x ~ 94.8..99.6, y = -37..-14)
    mb.box_ft(95.4, -36.5, FLOOR_Z, 98.8, -14.5, 3.5, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(95.1, -36.8, 3.5, 98.9, -14.2, 3.85, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip"}, group="detail")
    # Upper 3-bay mahogany canopy + mirrored/backlit bottle coolers (3 bays: y=-35..-29, -28..-22, -21..-15)
    mb.box_ft(97.0, -36.5, 3.85, 98.9, -14.5, 10.6, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip"}, group="detail")
    for by0, by1 in ((-35.0, -29.2), (-28.4, -22.6), (-21.8, -16.0)):
        # Purple/blue backlit glass liquor display niches inside each bay
        mb.box_ft(96.6, by0, 4.2, 97.1, by1, 8.6, Tile("gwc_glass", w_ft=4.0), group="illus")
        # Shelf accents + overhead flat-screen TVs in outer bays
        mb.box_ft(96.3, by0 + 0.1, 5.7, 97.0, by1 - 0.1, 5.9, "gwc_dark", faces={"e": "skip"}, group="detail")
        mb.box_ft(96.3, by0 + 0.1, 7.2, 97.0, by1 - 0.1, 7.4, "gwc_dark", faces={"e": "skip"}, group="detail")
    for tv_y in (-32.0, -19.0):
        mb.box_ft(95.8, tv_y - 2.2, 8.7, 96.4, tv_y + 2.2, 11.1, "gwc_dark", faces={"e": "skip"}, group="detail")
        mb.sign_decal_ft("w", 95.80, tv_y - 2.0, tv_y + 2.0, 8.9, 10.9, Fit("gwc_tvscr"))

    # Glowing Cyan Neon "Blackjack" + "Lounge" Sign Centered Over Back-Bar (z=9.2..11.4, x=95.6)
    mb.box_ft(95.6, -30.5, 9.6, 96.2, -20.5, 11.4, "gwc_dark", group="detail")
    mb.sign_decal_ft("w", 95.60, -25.4, -20.4, 9.8, 11.2, Fit("{gwc_bjneon"))
    mb.sign_decal_ft("w", 95.60, -30.6, -25.6, 9.8, 11.2, Fit("{gwc_lgneon"))

    # Curved Mottled Dark Granite Bar Counter over Tan Tile Apron (arc centered at x=87.5, y=-25.5, R=10.5..12.8)
    bar_cx, bar_cy = 87.5, cy
    r_in, r_out = 9.4, 11.6
    # 5 angled segments spanning 115 deg -> 245 deg (opening east toward back-bar with 6 ft aisle!)
    n_seg = 5
    ang0, ang1 = math.radians(118.0), math.radians(242.0)
    for k in range(n_seg):
        a0 = ang0 + (ang1 - ang0) * (k / n_seg)
        a1 = ang0 + (ang1 - ang0) * ((k + 1) / n_seg)
        p0_in = (bar_cx + r_in * math.cos(a0), bar_cy + r_in * math.sin(a0))
        p1_in = (bar_cx + r_in * math.cos(a1), bar_cy + r_in * math.sin(a1))
        p0_out = (bar_cx + r_out * math.cos(a0), bar_cy + r_out * math.sin(a0))
        p1_out = (bar_cx + r_out * math.cos(a1), bar_cy + r_out * math.sin(a1))
        # Tan tile apron base (z=0.5..3.55)
        mb.prism_ft([p0_in, p1_in, p1_out, p0_out], FLOOR_Z, 3.55, Tile("gwc_bartile", w_ft=2.0, h_ft=2.0), tex_top="skip", tex_bot="skip", group="detail")
        # Mottled dark granite bar overhang top (z=3.55..3.85)
        po0 = (bar_cx + (r_out + 0.55) * math.cos(a0), bar_cy + (r_out + 0.55) * math.sin(a0))
        po1 = (bar_cx + (r_out + 0.55) * math.cos(a1), bar_cy + (r_out + 0.55) * math.sin(a1))
        pi0 = (bar_cx + (r_in - 0.25) * math.cos(a0), bar_cy + (r_in - 0.25) * math.sin(a0))
        pi1 = (bar_cx + (r_in - 0.25) * math.cos(a1), bar_cy + (r_in - 0.25) * math.sin(a1))
        mb.prism_ft([pi0, pi1, po1, po0], 3.55, 3.85, Tile("gwc_granite", w_ft=4.0), group="detail")

    # Dual Chrome Coors Draft Beer Tap Towers on granite bar top
    for ty in (-29.2, -21.8):
        mb.box_ft(76.4, ty - 0.35, 3.85, 77.2, ty + 0.35, 5.1, Tile("gwc_galv", w_ft=2.0), faces={"b": "skip", "t": "skip"}, group="detail")
        mb.box_ft(76.2, ty - 0.55, 4.9, 77.4, ty + 0.55, 5.25, Tile("gwc_dark", w_ft=2.0), group="detail")

    # 7 Spaced Black Leather Barstools curving cleanly around the bar arc (R=13.5 from bar_cx)
    # Seat z=2.35 ft (> 18u step threshold so Hull-1 never steps into gap behind stools!)
    for idx in range(7):
        ang = math.radians(126.0 + idx * (108.0 / 6.0))
        sx = bar_cx + 13.6 * math.cos(ang)
        sy = bar_cy + 13.6 * math.sin(ang)
        mb.box_ft(sx - 0.3, sy - 0.3, FLOOR_Z, sx + 0.3, sy + 0.3, 2.30, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")
        mb.box_ft(sx - 0.72, sy - 0.72, 2.30, sx + 0.72, sy + 0.72, 2.55, Tile("gwc_leather", w_ft=2.0), faces={"b": "skip"}, group="detail")

    # 2 High-Top Cocktail Tables near North & South courtyard bays (wide walk aisles all around)
    for hx, hy in ((71.0, -10.5), (71.5, -39.0)):
        mb.box_ft(hx - 0.3, hy - 0.3, FLOOR_Z, hx + 0.3, hy + 0.3, 3.2, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")
        mb.cyl_ft(hx, hy, 1.5, 3.2, 3.45, sides=8, tex_side="gwc_dark", tex_top=Tile("gwc_granite", w_ft=3.0), tex_bot="skip", group="detail")


# ---------------------------------------------------------------------------
# 6. Exposed Ceilings, Trusses, Sloped Soffits, 2x4/2x2 Acoustic & Radials
# ---------------------------------------------------------------------------

def _build_ceilings_and_trusses(mb: MapBuilder) -> None:
    """Emit exposed dark-brown heavy timber trusses, sloped soffits, drop tiles & troffers."""
    ceil_2x4 = Tile("gwc_ceil2x4", w_ft=4.0)
    ceil_2x2 = Tile("gwc_ceil2x2", w_ft=4.0)
    roof_seal = Tile("gwc_crmstuc", w_ft=8.0)

    # --- A. Main Hall & Poker Pit (x=-19..43, y=-35..54) ---
    # Structural roof seal deck at z=15.42..15.83 ft (185..190u) inset 0.25 ft inside exterior walls:
    # avoids coplanar wall outer-face overlaps AND avoids z=16.0 (192u) / z=15.90 (191u) roof overlaps!
    p_seal = _compute_inner_miter_ring(PERIM_PTS, 0.25)
    v00, v01, v02, v03 = p_seal[0], p_seal[1], p_seal[2], p_seal[3]
    v04, v05, v_ne, v_rn = p_seal[4], p_seal[5], p_seal[6], p_seal[7]
    v20, v21, v22, v23, v24 = p_seal[20], p_seal[21], p_seal[22], p_seal[23], p_seal[24]
    rot_v07_in = (ROTUNDA_V07[0] - 0.25, ROTUNDA_V07[1])
    yn_at_div = _snap_ft(_lerp_y_at_x(v02, v03, X_BOH_DIV))
    L_ne = _v_len(_v_sub(v_rn, v_ne))
    p_step_ne = _interp_pt(v_ne, v_rn, (L_ne - 4.0) / L_ne)
    x_w_notch = _snap_ft(v22[0] + 1.0)

    def _deck(pts: Sequence[Tuple[float, float]]) -> None:
        mb.prism_ft([(_snap_ft(x), _snap_ft(y)) for x, y in pts], 15.1667, 15.8333, "gwc_stone", tex_top="skip", tex_bot=roof_seal, group="detail", force_world=False)

    _deck([v24, (X_BOH_DIV, v23[1]), (X_BOH_DIV, v00[1]), v00])
    _deck([v01, (X_BOH_DIV, v01[1]), (X_BOH_DIV, yn_at_div), v02])
    _deck([v22, (x_w_notch, v22[1]), (x_w_notch, v23[1]), v23])
    _deck([(x_w_notch, v22[1]), v21, v20, (X_BOH_DIV, Y_SE_NORTH), (X_BOH_DIV, v23[1])])
    _deck([(X_BOH_DIV, Y_SE_NORTH), v20, rot_v07_in, (X_BOH_DIV, rot_v07_in[1])])
    _deck([(X_BOH_DIV, rot_v07_in[1]), rot_v07_in, p_step_ne, v_ne, (X_BOH_DIV, v_ne[1])])
    _deck([(X_BOH_DIV, v_ne[1]), v_ne, v05, (X_BOH_DIV, v05[1])])
    _deck([(X_BOH_DIV, v05[1]), v05, v04, (X_BOH_DIV, v04[1])])
    _deck([(X_BOH_DIV, v04[1]), v04, v03, (X_BOH_DIV, yn_at_div)])

    # Vertical collar sealing 12.92->15.17 step between Vestibule roof deck (p_step_ne) and Rotunda archway
    _emit_quad_wall_prism_ft(
        mb, rot_v07_in, p_step_ne,
        _v_sub(rot_v07_in, (0.4, 0.0)), _v_sub(p_step_ne, (0.4, 0.0)),
        12.5833, 15.1667, "gwc_stone", "gwc_white", "gwc_stone",
    )
    mb.prism_ft([rot_v07_in, p_step_ne, v_rn], 12.5833, 12.9167, "gwc_stone", tex_top="skip", tex_bot=ceil_2x2, group="detail", force_world=False)

    # Center suspended 2x4 acoustic drop-tile soffit (x=-9..+31, y=-35..+54, z=14.6..15.0)
    mb.box_ft(-9.0, -35.0, 14.6, 31.0, 54.0, 15.0, ceil_2x4, faces={"b": ceil_2x4, "t": "skip"}, group="detail")

    # Sloped side perimeter soffits rising from z=12.4 at side walls to z=14.6 at x=-9 / x=+31
    # West starts at x=-18.08 (inside X_BOH_DIV wall); East starts at x=41.8 across y=+7..+54 only.
    _emit_sloped_beam_ft(mb, -18.08, 9.5, 12.2, 12.6, -9.0, 9.5, 14.4, 14.8, width_ft=89.0, tex=roof_seal, group="detail", tex_end_a="skip")
    _emit_sloped_beam_ft(mb, 41.8, 30.5, 12.2, 12.6, 31.0, 30.5, 14.4, 14.8, width_ft=47.0, tex=roof_seal, group="detail")

    # Signature Heavy Dark-Brown Exposed Wood Cross-Tie Beams (z=12.0..13.1 ft, >=138u clear headroom!)
    # South-east bays (by=-30..-2) end cleanly at Vestibule/Lounge bulkhead x=31.0 so beams never clip drop tiles
    for by in (-30.0, -16.0, -2.0, 12.0, 26.0, 40.0, 52.0):
        beam_x1 = 41.8 if by > 7.0 else 31.0
        mb.box_ft(-18.08, by - 0.55, 12.0, beam_x1, by + 0.55, 13.1, Tile("gwc_beam", w_ft=4.0), faces={"w": "skip"}, group="detail")
        # Sloped roof rafters matching outer soffit pitch above the tie beam
        _emit_sloped_beam_ft(mb, -18.08, by, 12.4, 13.3, -9.0, by, 14.3, 15.2, width_ft=0.85, tex=Tile("gwc_beam", w_ft=4.0), tex_end_a="skip")
        if by > 7.0:
            _emit_sloped_beam_ft(mb, 41.8, by, 12.4, 13.3, 31.0, by, 14.3, 15.2, width_ft=0.85, tex=Tile("gwc_beam", w_ft=4.0))

    # Central longitudinal mahogany spine beam tying cross-beams at x=11.0
    mb.box_ft(10.4, -35.0, 12.3, 11.6, 54.0, 13.4, Tile("gwc_beam", w_ft=4.0), group="detail")

    # Rows of recessed glowing 2x4 fluorescent troffers in Main Hall soffit
    for tx in (0.0, 22.0):
        for ty in (-24.0, -9.0, 5.0, 19.0, 33.0, 46.0):
            mb.flush_panel_ft(tx - 1.0, ty - 2.0, 14.55, tx + 1.0, ty + 2.0, 14.61, {"b": Fit("gwc_troffer")})

    # --- B. South Alcove (y=-71.5..-35) & North Poker Wing (y=54..89.5), inset inside wall inner faces ---
    mb.box_ft(-18.08, -70.6, 13.5, 35.6, -35.08, 13.9, ceil_2x4, faces={"b": ceil_2x4, "t": "skip"}, group="detail")
    for tx, ty in ((-8.0, -60.0), (10.0, -60.0), (24.0, -60.0), (-4.0, -42.0), (18.0, -42.0)):
        mb.flush_panel_ft(tx - 2.0, ty - 1.0, 13.45, tx + 2.0, ty + 1.0, 13.51, {"b": Fit("gwc_troffer")})

    mb.box_ft(-18.08, 54.08, 13.5, 41.4, 70.1, 13.9, ceil_2x4, faces={"b": ceil_2x4, "t": "skip"}, group="detail")
    mb.box_ft(-42.5, 70.1, 13.5, 6.4, 88.2, 13.9, ceil_2x4, faces={"b": ceil_2x4, "t": "skip"}, group="detail")
    for tx, ty in ((-6.0, 62.0), (14.0, 62.0), (32.0, 62.0), (-8.0, 80.0), (-28.0, 80.0)):
        mb.flush_panel_ft(tx - 2.0, ty - 1.0, 13.45, tx + 2.0, ty + 1.0, 13.51, {"b": Fit("gwc_troffer")})

    # --- C. NE Entrance Vestibule & Rotunda Archway 2x2 Drop-Tile Ceiling (z=12.2..12.6, 140u clear!) ---
    white_drywall = Tile("gwc_white", w_ft=4.0)
    # Clean vertical drywall fascia bulkheads sealing Vestibule/Lounge ceiling step to Main Pit & South Alcove
    mb.box_ft(31.0, -35.13, 12.2, 31.42, 7.25, 15.0, white_drywall, faces={"t": "skip"}, group="detail")
    mb.box_ft(31.42, 6.85, 12.2, 42.8, 7.25, 15.0, white_drywall, faces={"t": "skip"}, group="detail")
    mb.box_ft(31.42, -35.2, 12.2, 36.2, -34.85, 13.9, white_drywall, faces={"t": "skip"}, group="detail")
    # Drop-tile slabs sit strictly inside bulkhead borders (x >= 31.42, y in [-34.85..6.85]) -> zero Z/edge overlap!
    mb.prism_ft(
        [(31.42, -14.17), (60.2, -14.17), (61.5, -12.3), (42.8, 6.85), (31.42, 6.85)],
        12.2, 12.6, white_drywall, tex_top="skip", tex_bot=ceil_2x2, group="detail",
    )
    mb.prism_ft(
        [(31.42, -34.85), (54.6, -34.85), (60.2, -14.17), (31.42, -14.17)],
        12.2, 12.6, white_drywall, tex_top="skip", tex_bot=ceil_2x2, group="detail",
    )
    for tx, ty in ((42.0, -2.0), (49.5, -8.0), (45.0, -24.5)):
        mb.flush_panel_ft(tx - 1.5, ty - 1.5, 12.16, tx + 1.5, ty + 1.5, 12.21, {"b": Fit("gwc_troffer")})

    # --- D. West BOH Wing & SE Wing Drop Ceilings (z=12.0..12.4 ft, inset inside wall thicknesses) ---
    mb.box_ft(-52.9, -67.6, 12.0, -18.92, 76.6, 12.4, ceil_2x2, faces={"b": ceil_2x2, "t": "skip"}, group="detail")
    for tx, ty in ((-37.0, -54.0), (-37.0, -34.0), (-26.0, -10.0), (-37.0, -10.0), (-47.0, -18.0), (-47.0, -2.0), (-37.0, 22.0), (-37.0, 44.0)):
        mb.flush_panel_ft(tx - 1.0, ty - 2.0, 11.96, tx + 1.0, ty + 2.0, 12.01, {"b": Fit("gwc_troffer")})

    mb.prism_ft([(36.35, -70.7), (52.7, -70.7), (53.4, -35.45), (36.35, -35.45)], 12.5, 12.9, Tile("gwc_dark", w_ft=4.0), tex_top="skip", tex_bot=ceil_2x4, group="detail")
    for ty in (-60.0, -45.0):
        mb.flush_panel_ft(43.5, ty - 2.0, 12.46, 45.5, ty + 2.0, 12.51, {"b": Fit("gwc_troffer")})

    # --- E. East 12-Sided Rotunda Ceiling & 12 Radial Laminated Arch Ribs (strictly < 13.0 ft!) ---
    rot_cx, rot_cy = CASINO_ROTUNDA_CENTER_FT
    rot_pts = [rot_v07_in] + list(p_seal[7:21])
    # Solid detail ceiling cap cleanly terminating at z=12.58..12.92 (151..155u, inset inside walls & below 13.0!)
    mb.poly_prism_ft(rot_pts, 12.5833, 12.9167, "gwc_stone", tex_top="skip", tex_bot=ceil_2x2, group="detail", force_world=False)

    # Inner octagonal ceiling ring beam & recessed troffers around Rotunda center
    hub_pts = _oct_pts(rot_cx, rot_cy, 6.2, 6.2, chamfer=0.29)
    for k in range(8):
        p0, p1 = hub_pts[k], hub_pts[(k + 1) % 8]
        _emit_sloped_beam_ft(mb, p0[0], p0[1], 11.9, 12.5833, p1[0], p1[1], 11.9, 12.5833, width_ft=0.75, tex=Tile("gwc_beam", w_ft=4.0), tex_top="skip")

    # 12 radial dark-brown laminated wood arch ribs from perimeter vertices (z=11.3..12.5) up to hub ring (r=6.6)
    for vx, vy in PERIM_PTS[8:20]:
        dx, dy = vx - rot_cx, vy - rot_cy
        L = max(math.hypot(dx, dy), 1e-4)
        ux, uy = dx / L, dy / L
        ax, ay = rot_cx + ux * (L - 1.2), rot_cy + uy * (L - 1.2)
        bx, by = rot_cx + ux * 6.6, rot_cy + uy * 6.6
        _emit_sloped_beam_ft(mb, ax, ay, 11.3, 12.5833, bx, by, 12.0, 12.5833, width_ft=0.72, tex=Tile("gwc_beam", w_ft=4.0), tex_top="skip")

    for dx, dy in ((-2.4, -2.4), (2.4, -2.4), (-2.4, 2.4), (2.4, 2.4)):
        mb.flush_panel_ft(rot_cx + dx - 1.0, rot_cy + dy - 1.0, 12.53, rot_cx + dx + 1.0, rot_cy + dy + 1.0, 12.59, {"b": Fit("gwc_troffer")})


# ---------------------------------------------------------------------------
# 7. Burgundy-Red Felt Gaming Tables, Chairs, Hanging TVs & [11] Markers
# ---------------------------------------------------------------------------

def _build_gaming_table(
    mb: MapBuilder,
    cx: float,
    cy: float,
    felt_tex: str,
    tbl_num: int,
    compact: bool = False,
) -> None:
    """Build one octagonal/oval burgundy-red felt table + rail + chairs + optional [11] placard."""
    rx = 3.2 if compact else 4.1
    ry = 2.0 if compact else 2.25

    # Single dark mahogany center pedestal tucked cleanly under tabletop
    mb.box_ft(cx - rx * 0.45, cy - 0.55, FLOOR_Z, cx + rx * 0.45, cy + 0.55, 2.45, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")

    # Dark mahogany raceway rim + full Fit(burgundy felt) top (ZERO Stones green felt!)
    rim_pts = _oct_pts(cx, cy, rx, ry, chamfer=0.40)
    mb.prism_ft(rim_pts, 2.45, 2.82, Tile("gwc_wood", w_ft=4.0), tex_top=Fit(felt_tex, repeat=(1.0, 1.0)), tex_bot="skip", group="detail")

    # Raised black padded vinyl arm rail around outer perimeter edge (4 straight bolsters)
    rail_h0, rail_h1 = 2.80, 2.98
    c_off = rx * 0.60
    y_off = ry * 0.60
    rail_faces = {"b": "skip"}
    mb.box_ft(cx - c_off, cy + ry - 0.36, rail_h0, cx + c_off, cy + ry + 0.04, rail_h1, Tile("gwc_leather", w_ft=2.0), faces=rail_faces, group="detail")
    mb.box_ft(cx - c_off, cy - ry - 0.04, rail_h0, cx + c_off, cy - ry + 0.36, rail_h1, Tile("gwc_leather", w_ft=2.0), faces=rail_faces, group="detail")
    mb.box_ft(cx - rx - 0.04, cy - y_off, rail_h0, cx - rx + 0.36, cy + y_off, rail_h1, Tile("gwc_leather", w_ft=2.0), faces=rail_faces, group="detail")
    mb.box_ft(cx + rx - 0.36, cy - y_off, rail_h0, cx + rx + 0.04, cy + y_off, rail_h1, Tile("gwc_leather", w_ft=2.0), faces=rail_faces, group="detail")

    # Dealer chip tray on rail
    mb.box_ft(cx - 0.9, cy - ry + 0.35, 2.82, cx + 0.9, cy - ry + 0.85, 2.95, Fit("gwc_chiprack"), faces={"b": "skip"}, group="detail")

    # 6 Black leather swivel chairs tucked tightly against table (seat z=2.25 ft > 18u Hull-1 step)
    chair_offsets: List[Tuple[float, float, str]] = [
        (-rx * 0.42,  ry + 0.80, "-y"),
        ( rx * 0.42,  ry + 0.80, "-y"),
        (-rx * 0.42, -ry - 0.80, "+y"),
        ( rx * 0.42, -ry - 0.80, "+y"),
        (-rx - 0.80,  0.0,       "+x"),
        ( rx + 0.80,  0.0,       "-x"),
    ]
    for ox, oy, facing in chair_offsets:
        sx, sy = cx + ox, cy + oy
        mb.box_ft(sx - 0.25, sy - 0.25, FLOOR_Z, sx + 0.25, sy + 0.25, 2.15, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")
        mb.box_ft(sx - 0.72, sy - 0.72, 2.15, sx + 0.72, sy + 0.72, 2.38, Tile("gwc_leather", w_ft=2.0), faces={"b": "skip"}, group="detail")
        if facing == "-y":
            mb.box_ft(sx - 0.70, sy + 0.46, 2.38, sx + 0.70, sy + 0.72, 3.65, Tile("gwc_leather", w_ft=2.0), faces={"b": "skip"}, group="detail")
        elif facing == "+y":
            mb.box_ft(sx - 0.70, sy - 0.72, 2.38, sx + 0.70, sy - 0.46, 3.65, Tile("gwc_leather", w_ft=2.0), faces={"b": "skip"}, group="detail")
        elif facing == "+x":
            mb.box_ft(sx - 0.72, sy - 0.70, 2.38, sx - 0.46, sy + 0.70, 3.65, Tile("gwc_leather", w_ft=2.0), faces={"b": "skip"}, group="detail")
        else:
            mb.box_ft(sx + 0.46, sy - 0.70, 2.38, sx + 0.72, sy + 0.70, 3.65, Tile("gwc_leather", w_ft=2.0), faces={"b": "skip"}, group="detail")

    # Hanging square [11] table number placard cleanly overhead (z=8.8..9.9 ft, above head height!)
    if not compact:
        mb.box_ft(cx - 0.06, cy - 0.06, 9.9, cx + 0.06, cy + 0.06, 12.2, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")
        mb.box_ft(cx - 0.55, cy - 0.55, 8.8, cx + 0.55, cy + 0.55, 9.9, "gwc_dark", group="detail")
        for fdir, pos in (("e", cx + 0.55), ("w", cx - 0.55), ("n", cy + 0.55), ("s", cy - 0.55)):
            a0, a1 = (cy - 0.50, cy + 0.50) if fdir in ("e", "w") else (cx - 0.50, cx + 0.50)
            mb.sign_decal_ft(fdir, pos, a0, a1, 8.85, 9.85, Fit("gwc_tblnum"))


def _build_gaming_tables_and_props(mb: MapBuilder) -> None:
    """Place 14 well-spaced red-felt gaming tables, hanging TVs & sports banners."""
    # Main Pit 2x6 clean table grid + North Poker Alcove table + 1 Lounge Blackjack table
    table_specs: List[Tuple[float, float, str, bool]] = [
        (-1.5, -48.0, "gwc_fpoker", False),
        (20.5, -48.0, "gwc_futh",   False),
        (-1.5, -32.0, "gwc_fbacc",  False),
        (20.5, -32.0, "gwc_fpoker", False),
        (-1.5, -16.0, "gwc_fpoker", False),
        (20.5, -16.0, "gwc_fbj",    False),
        (-1.5,   1.0, "gwc_futh",   False),
        (20.5,   1.0, "gwc_fpoker", False),
        (-1.5,  18.0, "gwc_fpoker", False),
        (20.5,  18.0, "gwc_fbacc",  False),
        (-1.5,  35.0, "gwc_fbj",    False),
        (20.5,  35.0, "gwc_fpoker", False),
        (10.0,  54.0, "gwc_fpoker", False),
        (-6.0,  77.0, "gwc_fpoker", False),
    ]
    for idx, (tx, ty, felt, is_compact) in enumerate(table_specs, start=1):
        _build_gaming_table(mb, tx, ty, felt, idx, compact=is_compact)

    # Double-sided Hanging Flat-Screen TVs down main center aisle (z=9.0..11.2, safe above heads)
    for tvy in (-24.0, 8.0, 42.0):
        mb.box_ft(10.8, tvy - 0.1, 11.2, 11.2, tvy + 0.1, 13.0, "gwc_dark", faces={"b": "skip", "t": "skip"}, group="detail")
        mb.box_ft(8.4, tvy - 0.25, 9.0, 13.6, tvy + 0.25, 11.4, "gwc_dark", group="detail")
        mb.sign_decal_ft("n", tvy + 0.25, 8.6, 13.4, 9.2, 11.2, Fit("gwc_tvscr"))
        mb.sign_decal_ft("s", tvy - 0.25, 8.6, 13.4, 9.2, 11.2, Fit("gwc_tvscr"))

    # Wall sports & promotional banners mounted flush on East Pit inner stone wall
    mb.box_ft(41.58, 24.0, 5.1, 41.78, 31.0, 8.9, "gwc_dark", faces={"e": "skip"}, group="detail")
    mb.sign_decal_ft("w", 41.58, 24.1, 30.9, 5.2, 8.8, Fit("gwc_nflban"))
    mb.box_ft(41.30, 41.0, 5.1, 41.50, 48.0, 8.9, "gwc_dark", faces={"e": "skip"}, group="detail")
    mb.sign_decal_ft("w", 41.30, 41.1, 47.9, 5.2, 8.8, Fit("gwc_goldwin"))


# ---------------------------------------------------------------------------
# 8. South Alcove & Golden Laughing Buddha Shrine (progs/gw_buddha.md3)
# ---------------------------------------------------------------------------

def _build_buddha_shrine(mb: MapBuilder) -> None:
    """Build South Alcove Golden Laughing Buddha Shrine + twin gold urns + wall TV."""
    # Altar shelf centered under South Window 1 (x=-12.5..-3.5, y=-70.6..-66.8)
    mb.box_ft(-12.5, -70.6, FLOOR_Z, -3.5, -66.8, 3.0, Tile("gwc_wood", w_ft=4.0), faces={"b": "skip", "t": "skip", "s": "skip"}, group="detail")
    mb.box_ft(-12.7, -70.7, 3.0, -3.3, -66.6, 3.25, Tile("gwc_granite", w_ft=4.0), faces={"b": "skip"}, group="detail")

    # Centerpiece Laughing Buddha MD3 resting flush at z=3.25 ft facing +Y north into Pit
    mb.ent_ft("misc_model", -8.0, -68.8, 3.25, mdl="progs/gw_buddha.md3", angles="0 90 0")
    # Solid clip volume wrapping the Buddha & shelf above z=3.25 so players don't walk into mesh
    mb.clip_box_ft(-9.6, -70.4, 3.25, -6.4, -67.2, 8.8)

    # Flanked by 2 Ornamental Gold Urns on the altar shelf
    for ux in (-11.3, -4.7):
        mb.cyl_ft(ux, -68.7, 0.72, 3.25, 4.9, sides=8, tex_side=Tile("gwc_goldurn", w_ft=2.0), tex_top="gwc_goldurn", tex_bot="skip", group="detail")
        mb.cyl_ft(ux, -68.7, 0.45, 4.9, 5.5, sides=8, tex_side=Tile("gwc_goldurn", w_ft=2.0), tex_top="gwc_goldurn", tex_bot="skip", group="detail")

    # South Wall Flat-Screen TV centered between the 2 horizontal blind windows (x=-2.2..3.2)
    mb.box_ft(-2.4, -70.55, 5.0, 3.4, -70.1, 8.4, "gwc_dark", faces={"s": "skip"}, group="detail")
    mb.sign_decal_ft("n", -70.10, -2.1, 3.1, 5.3, 8.1, Fit("gwc_tvscr"))


# ---------------------------------------------------------------------------
# 9. Sunny Interior Lights, Audit Spots & Room Registrations
# ---------------------------------------------------------------------------

def _build_lights_and_registrations(mb: MapBuilder) -> None:
    """Register all rooms, emit bright sunny interior lights, and place audit spots."""
    warm = (255, 232, 194)
    gold_warm = (255, 218, 150)
    bar_cool = (232, 240, 255)

    # Main Poker Pit + North Wing + South Alcove light grids
    mb.interior_lights_ft(-12.0, -60.0, 34.0, 62.0, 10.2, nx=3, ny=5, light=205.0, color=warm, wait=0.75)
    mb.interior_lights_ft(-36.0, 72.0, 2.0, 86.0, 10.2, nx=2, ny=1, light=200.0, color=warm, wait=0.75)

    # NE Vestibule & Security Podium highlight
    mb.light_ft(47.0, -3.5, 10.6, light=210.0, color=warm, wait=0.75)
    mb.light_ft(41.0, -6.0, 9.8, light=170.0, color=warm, wait=0.75)

    # Rotunda Blackjack Lounge: center bar glow + curved perimeter fill + bar apron under-counter fill + neon accent
    rot_cx, rot_cy = CASINO_ROTUNDA_CENTER_FT
    mb.light_ft(rot_cx - 4.0, rot_cy, 9.8, light=195.0, color=warm, wait=0.75)
    mb.light_ft(rot_cx + 12.0, rot_cy, 9.8, light=185.0, color=bar_cool, wait=0.75)
    mb.light_ft(rot_cx + 4.0, rot_cy + 13.0, 9.8, light=175.0, color=warm, wait=0.75)
    mb.light_ft(rot_cx + 4.0, rot_cy - 13.0, 9.8, light=175.0, color=warm, wait=0.75)
    for bar_ang_deg in (148.0, 180.0, 212.0):
        ba = math.radians(bar_ang_deg)
        mb.light_ft(87.5 + 12.8 * math.cos(ba), rot_cy + 12.8 * math.sin(ba), 2.95, light=95.0, color=warm, wait=0.65)

    # Buddha Shrine warm spotlight
    mb.light_ft(-8.0, -63.0, 9.2, light=215.0, color=gold_warm, wait=0.75)

    # Cashier Cage Interior Vault + West BOH Hallway + Restrooms + Kitchen + SE Wing
    mb.light_ft(-26.0, -10.0, 10.2, light=220.0, color=warm, wait=0.75)
    mb.light_ft(-37.0, -52.0, 10.2, light=200.0, color=warm, wait=0.75)
    mb.light_ft(-37.0, -14.0, 10.2, light=195.0, color=warm, wait=0.75)
    mb.light_ft(-47.0, -17.5, 10.2, light=195.0, color=warm, wait=0.75)
    mb.light_ft(-47.0, -2.0, 10.2, light=195.0, color=warm, wait=0.75)
    mb.light_ft(-37.0, 26.0, 10.2, light=205.0, color=warm, wait=0.75)
    mb.light_ft(-37.0, 48.0, 10.2, light=205.0, color=warm, wait=0.75)
    mb.light_ft(45.0, -48.0, 10.6, light=210.0, color=warm, wait=0.75)
    mb.light_ft(45.0, -63.0, 10.6, light=210.0, color=warm, wait=0.75)

    # Room Ceiling Clearances (verified >= 112u / 9.33 ft everywhere)
    mb.register_room_ft("Casino Main Poker Pit", FLOOR_Z, 12.0)           # 138u beam bottom
    mb.register_room_ft("Casino NE Entrance Vestibule", FLOOR_Z, 12.2)   # 140.4u
    mb.register_room_ft("Casino North Poker Wing", FLOOR_Z, 13.5)        # 156u
    mb.register_room_ft("Casino South Alcove", FLOOR_Z, 13.5)            # 156u
    mb.register_room_ft("Casino Blackjack Lounge Rotunda", FLOOR_Z, 11.3) # 129.6u rib eaves
    mb.register_room_ft("Casino Cashier Cage Vault", FLOOR_Z, 12.0)      # 138u
    mb.register_room_ft("Casino West BOH Hall & Kitchen", FLOOR_Z, 12.0) # 138u
    mb.register_room_ft("Casino West Restrooms", FLOOR_Z, 12.0)          # 138u
    mb.register_room_ft("Casino SE Employee Wing", FLOOR_Z, 12.5)        # 144u

    # Curated Audit1 & Navigation Spots (matched cleanly by keyword in audit1_capture.py)
    mb.spot_ft(
        "Casino Vestibule & Security Podium", 50.5, -4.5, 5.5, yaw=200.0, pitch=-4.0,
        desc="Inside NE 45-deg glass double entrance looking at Security podium, plaque & Poker Pit",
    )
    mb.spot_ft(
        "Casino Main Poker Pit", 10.0, -24.0, 5.5, yaw=135.0, pitch=2.0,
        desc="Center aisle looking across burgundy-red felt poker tables, wood trusses & ceiling troffers",
    )
    mb.spot_ft(
        "Casino Red Felt Poker Tables", 9.5, 25.0, 5.5, yaw=175.0, pitch=14.0,
        desc="Close aisle angle over Golden West burgundy-red felt GWC tables & black leather rails",
    )
    mb.spot_ft(
        "Casino West Cashier Cage", -3.0, -10.0, 5.5, yaw=180.0, pitch=0.0,
        desc="West cage aisle facing twin corrugated shutter teller bays, granite/leather ledge & CASHIER sign",
    )
    mb.spot_ft(
        "Casino Blackjack Lounge & Rotunda Bar", 59.0, -25.0, 5.5, yaw=-5.0, pitch=-2.0,
        desc="Rotunda archway looking east at radial arch ribs, curved granite bar, back-bar & Blackjack Lounge neon",
    )
    mb.spot_ft(
        "Casino South Buddha Shrine & Alcove", -8.0, -56.0, 5.5, yaw=-90.0, pitch=-2.0,
        desc="South alcove facing Golden Laughing Buddha Shrine, twin gold urns & horizontal blind windows",
    )
    mb.spot_ft(
        "Casino West BOH Hallway", -37.0, -45.0, 5.5, yaw=90.0, pitch=0.0,
        desc="West BOH corridor connecting SW service exit, restrooms, vault & kitchen",
    )
    mb.spot_ft(
        "Casino SE Office Wing", 45.0, -42.0, 5.5, yaw=-90.0, pitch=0.0,
        desc="SE stone wing employee break/office space past EMPLOYEES ONLY entrance",
    )


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def _sync_gw_lib_classes(mb: MapBuilder) -> None:
    """Bind Fit/Tile to the exact gw_lib module instance backing mb."""
    global Fit, Tile
    mod = sys.modules.get(type(mb).__module__)
    if mod is not None and hasattr(mod, "Fit") and hasattr(mod, "Tile"):
        Fit = getattr(mod, "Fit")
        Tile = getattr(mod, "Tile")


def _build_vis_blockers(mb: MapBuilder) -> None:
    """Emit >=6u strictly axis-aligned worldspawn VIS blocker cores inside walls/decks.

    Every blocker sits strictly inside solid opaque func_detail outer walls,
    interior spines, or roof _deck slabs (0.0..15.75 ft), eliminating all thin
    worldspawn brushes and oblique prisms while preserving clean VIS separation.
    """
    vis_tex = "gwc_dark"
    z0, z1 = 0.0, 15.6667
    pz1 = 15.5833
    rz0, rz1 = 15.25, 15.75

    # Exterior opaque outer wall cores (0.50 ft = 6.0u thick inside 1.0 ft mitered walls)
    ext_walls = (
        (-53.25, -67.0, z0, -52.75, -30.0, z1),  # West E24 South
        (-53.42, -30.0, z0, -52.92,  10.0, z1),  # West E24 Mid-South
        (-53.58,  10.0, z0, -53.08,  45.0, z1),  # West E24 Mid-North
        (-53.75,  45.0, z0, -53.25,  75.5, z1),  # West E24 North
        (-43.08,  78.0, z0, -42.58,  87.0, z1),  # NW West E01
        (-42.0,   87.75, z0, -31.0,  88.25, z1), # North E02 W
        (-30.5,   88.08, z0, -20.5,  88.58, z1), # North E02 Mid
        (-20.0,   88.33, z0, -14.5,  88.83, z1), # North E02 E
        ( 42.08,   7.5, z0,  42.58,  26.0, z1),  # East Pit E05 S
        ( 41.75,  26.0, z0,  42.25,  48.0, z1),  # East Pit E05 Mid
        ( 41.42,  48.0, z0,  41.92,  69.0, z1),  # East Pit E05 N
        ( 14.0,  -71.42, z0,  23.5, -70.92, z1), # South E21 Pier W
        ( 34.5,  -71.42, z0,  52.5, -70.92, z1), # South E21 Pier E
        (-52.0,  -68.25, z0, -42.5, -67.75, z1), # SW E23 Pier W
        (-33.5,  -68.42, z0, -19.5, -67.92, z1), # SW E23 Pier E
    )
    # Interior opaque spine wall cores (0.50 ft = 6.0u thick, clear of doorways & bay openings)
    int_walls = (
        (-18.75, -67.5, z0, -18.25, -35.5, pz1), # X_BOH_DIV South
        (-18.75,   7.25, z0, -18.25,  18.5, pz1), # X_BOH_DIV Mid
        (-18.75,  27.0, z0, -18.25,  57.5, pz1), # X_BOH_DIV North
        (-33.25, -25.0, z0, -32.75,   6.5, pz1), # X_CAGE_BACK Vault
        ( 35.75, -70.4, z0,  36.25, -60.0, pz1), # X_SE_WING South
        ( 35.75, -51.5, z0,  36.25, -35.6, pz1), # X_SE_WING North
    )
    # Orthogonal roof VIS sealer slabs (6.0u thick inside _deck 15.1667..15.8333)
    roof_slabs = (
        (-52.5, -67.3, rz0, -19.25,  75.8, rz1),  # West BOH
        (-42.2,  75.8, rz0,   4.5,   87.5, rz1),  # NW Wing
        (-19.25, 69.8, rz0,   5.5,   75.8, rz1),  # North Transition
        (-19.25, -35.0, rz0, 41.3,   69.8, rz1),  # Main Pit
        (-19.25, -70.8, rz0, 52.5,  -35.0, rz1),  # South Alcove + SE Wing
    )
    for x0, y0, bz0, x1, y1, bz1 in ext_walls + int_walls + roof_slabs:
        mb.structural_box_ft(x0, y0, bz0, x1, y1, bz1, vis_tex)


def build_casino_int(mb: MapBuilder) -> Dict[str, object]:
    """Build the entire Golden West Casino Interior & Building Shell onto mb."""
    _sync_gw_lib_classes(mb)
    before_brushes = sum(len(v) for v in mb._brushes.values())
    before_ents = len(mb._entities)
    before_spots = len(mb._spots)

    _build_floors(mb)
    _build_vis_blockers(mb)
    _build_exterior_walls(mb)
    _build_west_boh_and_cage(mb)
    _build_se_wing_and_vestibule(mb)
    _build_rotunda_bar(mb)
    _build_ceilings_and_trusses(mb)
    _build_gaming_tables_and_props(mb)
    _build_buddha_shrine(mb)
    _build_lights_and_registrations(mb)

    after_brushes = sum(len(v) for v in mb._brushes.values())
    return {
        "brushes_added": after_brushes - before_brushes,
        "entities_added": len(mb._entities) - before_ents,
        "spots_added": len(mb._spots) - before_spots,
        "rooms": len(mb._rooms),
        "doorways": len(mb._doorways),
    }


def _standalone_verify() -> int:
    mb = MapBuilder(check_textures=True, require_gwc_prefix=True)
    # Test player start inside Poker Pit so standalone .map is runnable too
    mb.ent_ft("info_player_start", 11.0, -22.0, 2.5, angle=0)
    summary = build_casino_int(mb)
    warnings = mb.validate_all()
    stats = mb.stats()
    print("[gw_casino_int] build summary:", summary)
    print("[gw_casino_int] MapBuilder stats:", stats)
    if warnings:
        print("[gw_casino_int] warnings:", warnings)
    out_map = os.path.join(HERE, "out", "_test_casino_int.map")
    mb.write_map(out_map)
    mb.write_spots(os.path.join(HERE, "out", "_test_casino_int.spots.json"))
    print(f"[gw_casino_int] OK! Validated cleanly and wrote test map -> {out_map}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_standalone_verify())
