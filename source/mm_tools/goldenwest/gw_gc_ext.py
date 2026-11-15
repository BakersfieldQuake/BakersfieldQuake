"""gw_gc_ext.py — 410 Union Ave Great Castle Restaurant Exterior, Sitework,
Roofs, SW Watchtower, Signage & SE Annex for BakersfieldQuake.

Exclusive module ownership:
  - Exports ``build_gc_ext(mb)`` + standalone CLI self-test & ``validate_all()``.
  - Owns all Great Castle lot sitework inside ``GC_LOT_FT = (283.0, 882.0, 414.0, 1168.0)``
    strictly outside ``GC_POLY_FT``, plus ``GC_ANNEX_BOUNDS_FT = (383.0, 899.0, 410.5, 948.0)``,
    plus Main Building roofs, parapets, merlons, SW Watchtower, crimson crow's nest,
    crimson arched entry canopy, SW rock garden & monolith, BOH swamp coolers & exhaust,
    and exterior signage strictly above ``GC_CEIL_Z_FT = 12.0`` (``x <= 389.5``) /
    ``GC_BOH_CEIL_Z_FT = 10.5`` (``x >= 389.5``) and outside ``GC_POLY_FT``.
  - Zero world brushes (all geometry uses ``detail`` / ``illus`` / ``clip``), aggressive
    ``skip`` culling on hidden faces, <=18u Hull-1 steps, and 100% cataloged ``gwc_*`` /
    ``{gwc_*`` / ``skip`` / ``clip`` textures.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

if __package__:
    from .gw_lib import (
        GC_ANNEX_BOUNDS_FT,
        GC_BLDG_BOUNDS_FT,
        GC_BOH_CEIL_Z_FT,
        GC_BOH_PARAPET_Z_FT,
        GC_BOH_ROOF_Z_FT,
        GC_CEIL_Z_FT,
        GC_EAST_BOH_X_FT,
        GC_FLOOR_Z_FT,
        GC_LOT_FT,
        GC_PARAPET_Z_FT,
        GC_ROOF_Z_FT,
        GC_SW_NOTCH_FT,
        GC_TOWER_BOUNDS_FT,
        GC_TOWER_PARAPET_Z_FT,
        GC_WALL_T_FT,
        HULL1_MAX_STEP_U,
        Fit,
        MapBuilder,
        Tile,
        snap_val,
    )
else:
    GW_DIR = os.path.dirname(os.path.abspath(__file__))
    if GW_DIR not in sys.path:
        sys.path.insert(0, GW_DIR)
    from gw_lib import (  # noqa: E402
        GC_ANNEX_BOUNDS_FT,
        GC_BLDG_BOUNDS_FT,
        GC_BOH_CEIL_Z_FT,
        GC_BOH_PARAPET_Z_FT,
        GC_BOH_ROOF_Z_FT,
        GC_CEIL_Z_FT,
        GC_EAST_BOH_X_FT,
        GC_FLOOR_Z_FT,
        GC_LOT_FT,
        GC_PARAPET_Z_FT,
        GC_ROOF_Z_FT,
        GC_SW_NOTCH_FT,
        GC_TOWER_BOUNDS_FT,
        GC_TOWER_PARAPET_Z_FT,
        GC_WALL_T_FT,
        HULL1_MAX_STEP_U,
        Fit,
        MapBuilder,
        Tile,
        snap_val,
    )

# Exact snapped Z elevations matching gw_streets.py & gw_gc_int (12 u/ft)
Z_GROUND_FT: float = 0.0
Z_LOT_FT: float = 2.0 / 12.0      # 2.0 u: lot asphalt flush with street roadways
Z_MARK_FT: float = 2.5 / 12.0     # 2.5 u: flush thermoplastic stall stripes
Z_WALK_FT: float = GC_FLOOR_Z_FT  # 0.50 ft (6.0 u): sidewalks & interior slab datum
Z_CURB_FT: float = 0.65           # 7.8 u: perimeter curb / planter lip (<= 5.8 u step)


def _refresh_tiles() -> None:
    """Refresh cataloged Tile specs cleanly across package or standalone imports."""
    global TEX_ASPH, TEX_BARK, TEX_BRICK, TEX_CONC, TEX_CURB, TEX_CURBRED
    global TEX_DARK, TEX_DUMPSTR, TEX_GALV, TEX_GCCMU, TEX_GCRAMP, TEX_GCSTONE
    global TEX_GLASS, TEX_HEDGE, TEX_HVAC, TEX_MULCH, TEX_RED, TEX_STEEL
    global TEX_SWAMP, TEX_TPO, TEX_WHITE, TEX_WLINE

    TEX_ASPH = Tile("gwc_asph", 14.0, 14.0)
    TEX_BARK = Tile("gwc_bark", 2.5, 4.0)
    TEX_BRICK = Tile("gwc_brick", 5.0, 5.0)
    TEX_CONC = Tile("gwc_conc", 8.0, 8.0)
    TEX_CURB = Tile("gwc_curb", 6.0, 1.0)
    TEX_CURBRED = Tile("gwc_curbred", 6.0, 1.0)
    TEX_DARK = Tile("gwc_dark", 6.0, 6.0)
    TEX_DUMPSTR = Tile("gwc_dumpstr", 6.0, 4.0)
    TEX_GALV = Tile("gwc_galv", 4.0, 4.0)
    TEX_GCCMU = Tile("gwc_gccmu", 8.0, 8.0)
    TEX_GCRAMP = Tile("gwc_gcramp", 4.0, 4.0)
    TEX_GCSTONE = Tile("gwc_gcstone", 6.0, 6.0)
    TEX_GLASS = Tile("gwc_glass", 6.0, 6.0)
    TEX_HEDGE = Tile("gwc_hedge", 5.0, 5.0)
    TEX_HVAC = Tile("gwc_hvac", 6.0, 6.0)
    TEX_MULCH = Tile("gwc_mulch", 4.0, 4.0)
    TEX_RED = Tile("gwc_red", 4.0, 4.0)
    TEX_STEEL = Tile("gwc_steel", 4.0, 4.0)
    TEX_SWAMP = Tile("gwc_swamp", 3.0, 3.0)
    TEX_TPO = Tile("gwc_tpo", 12.0, 12.0)
    TEX_WHITE = Tile("gwc_white", 6.0, 6.0)
    TEX_WLINE = Tile("gwc_wline", 4.0, 4.0)


_refresh_tiles()


def _curb_ft(
    mb: MapBuilder,
    x0: float,
    y0: float,
    z0: float,
    x1: float,
    y1: float,
    z1: float,
    tex=TEX_CONC,
    faces: Optional[Dict[str, object]] = None,
) -> None:
    """Emit a Hull-1-verified curb/walk detail slab with bottom culled to skip."""
    rise_u = abs(z1 - z0) * mb.u_per_ft
    if rise_u > HULL1_MAX_STEP_U + 1e-4:
        raise ValueError(f"Curb height {rise_u:.1f}u exceeds Hull-1 step limit ({HULL1_MAX_STEP_U:.0f}u)")
    if hasattr(mb, "_curbs"):
        mb._curbs.append({"rise_u": rise_u})
    f: Dict[str, object] = {"b": "skip"}
    if faces:
        f.update(faces)
    mb.detail_box_ft(x0, y0, z0, x1, y1, z1, tex, faces=f)


def _mark_top(mb: MapBuilder, x0: float, y0: float, x1: float, y1: float, tex=TEX_WLINE) -> None:
    """Emit a flush non-solid parking-stripe top decal (5 faces culled to skip)."""
    mb.flush_panel_ft(x0, y0, Z_LOT_FT, x1, y1, Z_MARK_FT, {"t": tex}, group="illus")


def _alpha_quad_tree(
    mb: MapBuilder,
    cx: float,
    cy: float,
    z0: float,
    half_w: float,
    height_ft: float,
    tex_name: str,
    trunk_h: float = 0.0,
    trunk_r: float = 0.45,
) -> None:
    """Emit a lean crossed-quad alpha cutout tree/cypress with optional clipped trunk."""
    if trunk_h > 0.1:
        mb.cyl_ft(cx, cy, trunk_r, z0, z0 + trunk_h, sides=6, tex_side=TEX_BARK, tex_top="skip", group="detail")
        mb.clip_box_ft(cx - trunk_r, cy - trunk_r, z0, cx + trunk_r, cy + trunk_r, z0 + max(trunk_h, 6.0))
    z_top = z0 + height_ft
    # Crossed X/Y thin non-solid billboards with all hidden thickness edges skipped
    mb.flush_panel_ft(
        cx - half_w, cy - 0.04, z0, cx + half_w, cy + 0.04, z_top,
        {"s": Fit(tex_name), "n": Fit(tex_name)}, group="illus",
    )
    mb.flush_panel_ft(
        cx - 0.04, cy - half_w, z0, cx + 0.04, cy + half_w, z_top,
        {"w": Fit(tex_name), "e": Fit(tex_name)}, group="illus",
    )


def _merlon_strip_x(
    mb: MapBuilder,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    pitch: float = 4.2,
    tooth_w: float = 2.1,
    face_dir: str = "s",
) -> None:
    """Emit spaced white masonry parapet merlons along an East-West wall edge."""
    span = x1 - x0
    count = max(1, int(span // pitch))
    step = span / float(count)
    w = min(tooth_w, step * 0.62)
    for idx in range(count):
        mx = x0 + (idx + 0.5) * step
        faces: Dict[str, object] = {"b": "skip", face_dir: Fit("gwc_gcmerlon")}
        mb.detail_box_ft(mx - w * 0.5, y0, z0, mx + w * 0.5, y1, z1, TEX_GCCMU, faces=faces)


def _merlon_strip_y(
    mb: MapBuilder,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    pitch: float = 4.2,
    tooth_w: float = 2.1,
    face_dir: str = "w",
) -> None:
    """Emit spaced white masonry parapet merlons along a North-South wall edge."""
    span = y1 - y0
    count = max(1, int(span // pitch))
    step = span / float(count)
    w = min(tooth_w, step * 0.62)
    for idx in range(count):
        my = y0 + (idx + 0.5) * step
        faces: Dict[str, object] = {"b": "skip", face_dir: Fit("gwc_gcmerlon")}
        mb.detail_box_ft(x0, my - w * 0.5, z0, x1, my + w * 0.5, z1, TEX_GCCMU, faces=faces)


def _barrel_canopy_xz_ft(
    mb: MapBuilder,
    xc: float,
    half_w: float,
    y0: float,
    y1: float,
    z_spring: float,
    z_crown: float,
    thick_ft: float = 0.28,
    segs: int = 6,
) -> None:
    """Emit a convex 6-segment crimson arched barrel-vault canopy along XZ cross-section."""
    arch_h = z_crown - z_spring
    pts_outer: List[Tuple[float, float]] = []
    pts_inner: List[Tuple[float, float]] = []
    for i in range(segs + 1):
        ang = math.pi * (1.0 - float(i) / float(segs))
        ox = xc + math.cos(ang) * half_w
        oz = z_spring + math.sin(ang) * arch_h
        ix = xc + math.cos(ang) * max(half_w - thick_ft, 0.2)
        iz = z_spring + math.sin(ang) * max(arch_h - thick_ft, 0.2)
        pts_outer.append((ox, oz))
        pts_inner.append((ix, iz))

    u = mb.u_per_ft
    snap = mb.detail_snap_u
    ay0, ay1 = sorted((snap_val(y0 * u, snap), snap_val(y1 * u, snap)))
    for i in range(segs):
        quad_ft = [
            pts_outer[i],
            pts_outer[i + 1],
            pts_inner[i + 1],
            pts_inner[i],
        ]
        poly = [(snap_val(x * u, snap), snap_val(z * u, snap)) for x, z in quad_ft]
        area2 = sum(poly[k][0] * poly[(k + 1) % 4][1] - poly[(k + 1) % 4][0] * poly[k][1] for k in range(4))
        ccw_sign = 1.0 if area2 >= 0.0 else -1.0
        # North cap (y1=996) sits flush against Watchtower CMU wall; internal joints i<segs-1 & i>0 are concealed.
        t_edges = [
            TEX_RED,
            "skip" if i < segs - 1 else TEX_RED,
            TEX_RED,
            "skip" if i > 0 else TEX_RED,
        ]
        plane_defs: List[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], object]] = [
            ([(px, ay0, pz) for px, pz in poly], (0.0, -1.0, 0.0), TEX_RED),
            ([(px, ay1, pz) for px, pz in poly], (0.0, 1.0, 0.0), "skip"),
        ]
        for k in range(4):
            x0, z0 = poly[k]
            x1, z1 = poly[(k + 1) % 4]
            dx, dz = x1 - x0, z1 - z0
            L = math.hypot(dx, dz)
            if L < 0.25:
                continue
            out = (ccw_sign * dz / L, 0.0, -ccw_sign * dx / L)
            plane_defs.append(([(x0, ay0, z0), (x1, ay0, z1), (x1, ay1, z1), (x0, ay1, z0)], out, t_edges[k]))
        mb._emit_brush(plane_defs, group="detail")


def _shoebox_light(mb: MapBuilder, x_ft: float, y_ft: float) -> None:
    """Emit a 24-ft tall dark steel parking lot shoebox pole light."""
    mb.cyl_ft(x_ft, y_ft, 0.75, Z_LOT_FT, 2.0, sides=6, tex_side=TEX_CONC, tex_top=TEX_CONC, group="detail")
    mb.detail_box_ft(x_ft - 0.26, y_ft - 0.26, 2.0, x_ft + 0.26, y_ft + 0.26, 24.0, TEX_DARK, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(x_ft - 1.1, y_ft - 0.65, 23.5, x_ft + 1.1, y_ft + 0.65, 24.2, TEX_DARK, faces={"b": TEX_WHITE})
    mb.clip_box_ft(x_ft - 0.80, y_ft - 0.80, Z_LOT_FT, x_ft + 0.80, y_ft + 0.80, 9.0)
    mb.light_ft(x_ft, y_ft, 22.8, light=210.0, color=(255, 232, 196), wait=0.65)


def _parked_car(mb: MapBuilder, cx: float, cy: float, axis: str, tex_body: str, is_suv: bool = False) -> None:
    """Emit a lean 2-brush low-poly parked vehicle cleanly spaced inside a bay."""
    length_ft = 14.4
    width_ft = 6.0
    h_low = 2.6 if not is_suv else 2.9
    h_top = 4.9 if not is_suv else 5.5
    body = Tile(tex_body, 6.0, 4.0)
    win = Fit("gwc_carwin")
    if axis == "x":
        hx, hy = length_ft * 0.5, width_ft * 0.5
        mb.detail_box_ft(cx - hx, cy - hy, Z_LOT_FT + 0.45, cx + hx, cy + hy, Z_LOT_FT + h_low, body, faces={"b": "skip"})
        mb.detail_box_ft(
            cx - hx * 0.48, cy - hy * 0.82, Z_LOT_FT + h_low,
            cx + hx * 0.42, cy + hy * 0.82, Z_LOT_FT + h_top,
            body, faces={"w": win, "e": win, "s": win, "n": win, "b": "skip"},
        )
    else:
        hx, hy = width_ft * 0.5, length_ft * 0.5
        mb.detail_box_ft(cx - hx, cy - hy, Z_LOT_FT + 0.45, cx + hx, cy + hy, Z_LOT_FT + h_low, body, faces={"b": "skip"})
        mb.detail_box_ft(
            cx - hx * 0.82, cy - hy * 0.48, Z_LOT_FT + h_low,
            cx + hx * 0.82, cy + hy * 0.42, Z_LOT_FT + h_top,
            body, faces={"w": win, "e": win, "s": win, "n": win, "b": "skip"},
        )


def _build_gc_lot_paving(mb: MapBuilder) -> None:
    """Lot asphalt, driveway aprons, perimeter walks, door entry ramps, stripes & wheel stops."""
    lx0, ly0, lx1, ly1 = GC_LOT_FT
    ax0, ay0, ax1, ay1 = GC_ANNEX_BOUNDS_FT
    bx0, by0, bx1, by1 = GC_BLDG_BOUNDS_FT
    nx0, ny0, nx1, ny1 = GC_SW_NOTCH_FT  # (336.0, 996.0, 354.0, 1006.5)

    # 1. Exact non-overlapping lot asphalt partition strictly OUTSIDE GC_POLY_FT & GC_ANNEX_BOUNDS_FT
    asphalt_rects = [
        (lx0, ly0, ax0, by0),       # South-West parking lot (283..383, 882..996)
        (ax0, ly0, lx1, ay0),       # South of Annex apron (383..414, 882..899)
        (ax1, ay0, lx1, ay1),       # East of Annex alley edge (410.5..414, 899..948)
        (ax0, ay1, lx1, by0),       # North of Annex / South of Kitchen (383..414, 948..996)
        (lx0, by0, bx0, by1),       # West frontage strip (283..336, 996..1067.5)
        (bx1, by0, lx1, by1),       # East BOH alley sliver (413.5..414, 996..1067.5)
        (lx0, by1, lx1, ly1),       # North parking lot (283..414, 1067.5..1168)
    ]
    for rx0, ry0, rx1, ry1 in asphalt_rects:
        mb.detail_box_ft(rx0, ry0, Z_GROUND_FT, rx1, ry1, Z_LOT_FT, TEX_ASPH, faces={"b": "skip"})

    # 2. Concrete driveway ramps bridging Z_WALK_FT (0.50) -> Z_LOT_FT (0.167) at street cuts
    mb.slab_ramp_xft(lx0, lx0 + 3.0, 948.0, 978.0, Z_WALK_FT, Z_LOT_FT, TEX_CONC, thick_ft=0.16)   # South Union drive
    mb.slab_ramp_xft(lx0, lx0 + 3.0, 1094.0, 1126.0, Z_WALK_FT, Z_LOT_FT, TEX_CONC, thick_ft=0.16) # North Union drive
    mb.slab_ramp_yft(342.0, 368.0, ly0, ly0 + 3.0, Z_WALK_FT, Z_LOT_FT, TEX_CONC, thick_ft=0.16)    # E 4th St drive
    mb.slab_ramp_yft(342.0, 370.0, ly1 - 3.0, ly1, Z_WALK_FT, Z_LOT_FT, TEX_CONC, thick_ft=0.16)    # E 5th St drive

    # 3. Main Building Perimeter Pedestrian Sidewalks & Doorway Entry Ramps (flush at Z_WALK_FT = 0.50)
    # 3a. South main entry green rubber mat landing & sloped ramp snug to barrel canopy drip line
    _curb_ft(mb, 361.0, 988.0, Z_LOT_FT, 371.0, 996.0, Z_WALK_FT, TEX_GCRAMP, faces={"n": "skip"})
    mb.slab_ramp_yft(361.0, 371.0, 985.2, 988.0, Z_LOT_FT, Z_WALK_FT, TEX_GCRAMP, thick_ft=0.16)

    # 3b. South wall walks East & West of main green mat + small SE exit mat under 2nd red awning
    _curb_ft(mb, 330.0, 991.5, Z_LOT_FT, 361.0, 996.0, Z_WALK_FT, TEX_CONC, faces={"e": "skip"})
    _curb_ft(mb, 371.0, 991.5, Z_LOT_FT, 380.5, 996.0, Z_WALK_FT, TEX_CONC, faces={"w": "skip"})
    _curb_ft(mb, 380.5, 991.5, Z_LOT_FT, 386.5, 996.0, Z_WALK_FT, TEX_GCRAMP, faces={"w": "skip", "e": "skip", "n": "skip"})
    _curb_ft(mb, 386.5, 991.5, Z_LOT_FT, bx1, 996.0, Z_WALK_FT, TEX_CONC, faces={"w": "skip", "n": "skip"})

    # 3c. West Union wall walk connecting SW rock garden cleanly around NW corner to North walk
    _curb_ft(mb, 330.0, 996.0, Z_LOT_FT, 336.0, 1008.0, Z_WALK_FT, TEX_CONC, faces={"s": "skip", "n": "skip"})
    _curb_ft(mb, 330.0, 1008.0, Z_LOT_FT, 334.0, 1067.5, Z_WALK_FT, TEX_CONC, faces={"s": "skip", "n": "skip"})
    _curb_ft(mb, 330.0, 1067.5, Z_LOT_FT, 336.0, 1072.0, Z_WALK_FT, TEX_CONC, faces={"s": "skip", "e": "skip"})

    # 3d. North wall concrete walk + wide open ramps at north_dining_exit (358..365) & north_kitchen_exit (398..405)
    # Segments keep recessed mulch beds (337..357, 366..397, 406..413.5 at y=1067.5..1070.5) clear!
    _curb_ft(mb, 336.0, 1070.5, Z_LOT_FT, 357.0, 1072.5, Z_WALK_FT, TEX_CONC, faces={"w": "skip", "e": "skip"})
    _curb_ft(mb, 357.0, 1067.5, Z_LOT_FT, 366.0, 1072.5, Z_WALK_FT, TEX_CONC, faces={"s": "skip"})
    mb.slab_ramp_yft(357.0, 366.0, 1072.5, 1075.5, Z_WALK_FT, Z_LOT_FT, TEX_CONC, thick_ft=0.16)
    _curb_ft(mb, 366.0, 1070.5, Z_LOT_FT, 397.0, 1072.5, Z_WALK_FT, TEX_CONC, faces={"w": "skip", "e": "skip"})
    _curb_ft(mb, 397.0, 1067.5, Z_LOT_FT, 406.0, 1072.5, Z_WALK_FT, TEX_CONC, faces={"s": "skip"})
    mb.slab_ramp_yft(397.0, 406.0, 1072.5, 1075.5, Z_WALK_FT, Z_LOT_FT, TEX_CONC, thick_ft=0.16)
    _curb_ft(mb, 406.0, 1070.5, Z_LOT_FT, bx1, 1072.5, Z_WALK_FT, TEX_CONC, faces={"w": "skip"})

    # 4. South Lot Parking Stripes & Wheel Stops (preserving >=22 ft driving aisles)
    # West edge head-in stalls along Union planter (x=286..303, y=900..945 -> 5 bays @ 9ft)
    for idx in range(6):
        sy = 900.0 + idx * 9.0
        _mark_top(mb, 287.5, sy - 0.16, 303.0, sy + 0.16)
        if idx < 5:
            _curb_ft(mb, 288.0, sy + 1.5, Z_LOT_FT, 289.0, sy + 7.5, Z_LOT_FT + 0.35, TEX_CURB)

    # Central double-loaded row South Lot (x=310..340, y=900..936, non-overlapping divider at 324.8..325.2)
    _mark_top(mb, 324.8, 900.0, 325.2, 936.0)
    for idx in range(5):
        sy = 900.0 + idx * 9.0
        _mark_top(mb, 310.0, sy - 0.16, 324.8, sy + 0.16)
        _mark_top(mb, 325.2, sy - 0.16, 340.0, sy + 0.16)
        if idx < 4:
            _curb_ft(mb, 323.0, sy + 1.5, Z_LOT_FT, 324.0, sy + 7.5, Z_LOT_FT + 0.35, TEX_CURB)
            _curb_ft(mb, 326.0, sy + 1.5, Z_LOT_FT, 327.0, sy + 7.5, Z_LOT_FT + 0.35, TEX_CURB)

    # South facade customer stalls east of main canopy ramp (keeping 381..386 walk completely unobstructed)
    for sx in (375.0, 384.5, 394.0, 403.5):
        _mark_top(mb, sx - 0.16, 973.5, sx + 0.16, 988.0)
        if sx >= 394.0 and sx < 403.0:
            _curb_ft(mb, sx + 1.6, 986.5, Z_LOT_FT, sx + 7.9, 987.5, Z_LOT_FT + 0.35, TEX_CURB)

    # West ADA Accessible Stall facing West Union sidewalk (x=298..324, y=1016..1034)
    _mark_top(mb, 304.0, 1016.0, 326.0, 1016.35)
    _mark_top(mb, 304.0, 1025.0, 326.0, 1025.35)
    _mark_top(mb, 304.0, 1034.0, 326.0, 1034.35)
    _curb_ft(mb, 324.5, 1026.5, Z_LOT_FT, 325.5, 1032.5, Z_LOT_FT + 0.35, TEX_CURB)

    # 5. North Lot Parking Stripes & Wheel Stops (leaving North Union drive 1094..1126 & E 5th drive 342..370 open)
    # North E 5th edge bays East of E 5th driveway (x=372..400, y=1148..1165)
    for idx in range(4):
        sx = 372.0 + idx * 9.0
        _mark_top(mb, sx - 0.16, 1148.0, sx + 0.16, 1164.5)
        if idx < 3:
            _curb_ft(mb, sx + 1.5, 1163.0, Z_LOT_FT, sx + 7.5, 1164.0, Z_LOT_FT + 0.35, TEX_CURB)

    # North E 5th edge bays West of E 5th driveway (x=302..338, y=1148..1165)
    for idx in range(5):
        sx = 302.0 + idx * 9.0
        _mark_top(mb, sx - 0.16, 1148.0, sx + 0.16, 1164.5)
        if idx < 4:
            _curb_ft(mb, sx + 1.5, 1163.0, Z_LOT_FT, sx + 7.5, 1164.0, Z_LOT_FT + 0.35, TEX_CURB)

    # North wall head-in stalls West & East of dining exit (y=1076..1092, keeping 356..367 & 396..407 wide clear)
    for sx in (306.0, 315.5, 325.0, 334.5, 372.0, 381.5, 391.0):
        _mark_top(mb, sx - 0.16, 1076.5, sx + 0.16, 1091.5)
        if sx in (306.0, 315.5, 325.0, 372.0, 381.5):
            _curb_ft(mb, sx + 1.5, 1077.5, Z_LOT_FT, sx + 7.5, 1078.5, Z_LOT_FT + 0.35, TEX_CURB)


def _build_gc_roofs_and_watchtower(mb: MapBuilder) -> None:
    """Dining Hall flat roof, parapets & merlons (>12ft), SW Watchtower & crow's nest, and East BOH (>10.5ft)."""
    wt = GC_WALL_T_FT  # 1.0 ft
    tx0, ty0, tx1, ty1 = GC_TOWER_BOUNDS_FT  # (354.0, 996.0, 374.0, 1010.0)
    z_hall = GC_CEIL_Z_FT         # 12.0 ft
    z_par = GC_PARAPET_Z_FT       # 16.5 ft
    z_mtop = z_par + 1.7          # 18.2 ft
    z_tpar = GC_TOWER_PARAPET_Z_FT  # 19.5 ft
    z_tmtop = z_tpar + 1.8        # 21.3 ft
    x_split = GC_EAST_BOH_X_FT + 0.5  # 389.5 ft dividing seam between Main Hall and BOH

    # 1. Main Dining Hall TPO Roof Decks (strictly above z=12.0, tucked cleanly inside 1ft parapets & outside Watchtower)
    _tpo_faces = {"b": "skip", "w": "skip", "e": "skip", "s": "skip", "n": "skip"}
    mb.detail_box_ft(337.0, 1007.5, z_hall, tx0, 1066.5, GC_ROOF_Z_FT, TEX_TPO, faces=_tpo_faces)
    mb.detail_box_ft(tx0, ty1, z_hall, x_split - wt, 1066.5, GC_ROOF_Z_FT, TEX_TPO, faces=_tpo_faces)
    mb.detail_box_ft(tx1, 997.0, z_hall, x_split - wt, ty1, GC_ROOF_Z_FT, TEX_TPO, faces=_tpo_faces)

    # 2. Main Dining Hall White CMU Parapet Walls (z = 12.0 .. 16.5, non-overlapping around SW Watchtower)
    # West wall parapet (x=336..337, y=1006.5..1067.5)
    mb.detail_box_ft(336.0, 1006.5, z_hall, 337.0, 1067.5, z_par, TEX_GCCMU, faces={"b": "skip"})
    # North wall parapet (x=337..389.5, y=1066.5..1067.5)
    mb.detail_box_ft(337.0, 1066.5, z_hall, x_split, 1067.5, z_par, TEX_GCCMU, faces={"b": "skip", "w": "skip"})
    # SW Notch South return parapet (x=337..354, y=1006.5..1007.5)
    mb.detail_box_ft(337.0, 1006.5, z_hall, tx0, 1007.5, z_par, TEX_GCCMU, faces={"b": "skip", "w": "skip", "e": "skip"})
    # South-East main dining parapet East of Watchtower (x=374..389.5, y=996..997)
    mb.detail_box_ft(tx1, 996.0, z_hall, x_split, 997.0, z_par, TEX_GCCMU, faces={"b": "skip", "w": "skip"})
    # East step-down parapet closing Dining Hall roof above BOH (x=388.5..389.5, y=997..1066.5)
    mb.detail_box_ft(x_split - wt, 997.0, z_hall, x_split, 1066.5, z_par, TEX_GCCMU, faces={"b": "skip", "s": "skip", "n": "skip"})

    # 3. Main Dining Hall Stepped Merlons (z = 16.5 .. 18.2)
    _merlon_strip_y(mb, 336.0, 337.0, 1007.0, 1067.0, z_par, z_mtop, pitch=4.3, face_dir="w")
    _merlon_strip_x(mb, 337.5, 389.0, 1066.5, 1067.5, z_par, z_mtop, pitch=4.3, face_dir="n")
    _merlon_strip_x(mb, 337.5, 353.5, 1006.5, 1007.5, z_par, z_mtop, pitch=4.1, face_dir="s")
    _merlon_strip_x(mb, 374.5, 389.0, 996.0, 997.0, z_par, z_mtop, pitch=3.8, face_dir="s")
    _merlon_strip_y(mb, 388.5, 389.5, 997.5, 1006.0, z_par, z_mtop, pitch=4.2, face_dir="e")

    # 4. Raised SW Watchtower Bastion (354..374 x 996..1010, z = 12.0 .. 19.5 + merlons 21.3)
    mb.detail_box_ft(tx0, ty0, z_hall, tx0 + wt, ty1, z_tpar, TEX_GCCMU, faces={"b": "skip"})          # West
    mb.detail_box_ft(tx1 - wt, ty0, z_hall, tx1, ty1, z_tpar, TEX_GCCMU, faces={"b": "skip"})          # East
    mb.detail_box_ft(tx0 + wt, ty0, z_hall, tx1 - wt, ty0 + wt, z_tpar, TEX_GCCMU, faces={"b": "skip", "w": "skip", "e": "skip"})# South
    mb.detail_box_ft(tx0 + wt, ty1 - wt, z_hall, tx1 - wt, ty1, z_tpar, TEX_GCCMU, faces={"b": "skip", "w": "skip", "e": "skip"})# North
    # Watchtower TPO roof deck + coping strip
    mb.detail_box_ft(tx0 + wt, ty0 + wt, 17.5, tx1 - wt, ty1 - wt, 18.5, TEX_TPO, faces=_tpo_faces)
    # 4-sided Watchtower merlons
    _merlon_strip_x(mb, tx0 + 0.3, tx1 - 0.3, ty0, ty0 + wt, z_tpar, z_tmtop, pitch=4.0, face_dir="s")
    _merlon_strip_x(mb, tx0 + 0.3, tx1 - 0.3, ty1 - wt, ty1, z_tpar, z_tmtop, pitch=4.0, face_dir="n")
    _merlon_strip_y(mb, tx0, tx0 + wt, ty0 + 1.2, ty1 - 1.2, z_tpar, z_tmtop, pitch=3.9, face_dir="w")
    _merlon_strip_y(mb, tx1 - wt, tx1, ty0 + 1.2, ty1 - 1.2, z_tpar, z_tmtop, pitch=3.9, face_dir="e")

    # 5. Signature Rooftop Crimson Crow's Nest centered on SW Watchtower (x=364.0, y=1002.0)
    cx_n, cy_n = 364.0, 1002.0
    mb.detail_box_ft(cx_n - 0.25, cy_n - 0.25, 18.5, cx_n + 0.25, cy_n + 0.25, 24.6, TEX_RED, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(cx_n - 1.4, cy_n - 0.22, 24.2, cx_n - 0.25, cy_n + 0.22, 24.6, TEX_RED, faces={"e": "skip"})
    mb.detail_box_ft(cx_n + 0.25, cy_n - 0.22, 24.2, cx_n + 1.4, cy_n + 0.22, 24.6, TEX_RED, faces={"w": "skip"})
    mb.cyl_ft(cx_n, cy_n, 1.7, 24.6, 26.1, sides=8, tex_side=TEX_RED, tex_top="skip", group="detail")
    mb.cyl_ft(cx_n, cy_n, 2.05, 26.1, 27.3, sides=8, tex_side=TEX_RED, tex_top="skip", group="detail")
    mb.cyl_ft(cx_n, cy_n, 2.15, 27.3, 27.55, sides=8, tex_side=TEX_WHITE, tex_top=TEX_DARK, group="detail")
    # Upper crow's nest mast & angled boom arm (#164)
    mb.detail_box_ft(cx_n - 0.14, cy_n - 0.14, 27.55, cx_n + 0.14, cy_n + 0.14, 30.8, TEX_DARK, faces={"b": "skip"})
    mb.prism_xz_ft(
        [(cx_n - 3.0, 31.3), (cx_n - 2.85, 31.5), (cx_n - 0.14, 29.85), (cx_n - 0.14, 29.60)],
        cy_n - 0.10, cy_n + 0.10, TEX_DARK, tex_end=TEX_DARK, group="detail",
    )

    # 6. Dining Hall Rooftop HVAC Units & Supply Ducts (z = 13.0 .. 16.0)
    mb.detail_box_ft(358.0, 1028.0, GC_ROOF_Z_FT, 365.5, 1035.5, 15.8, TEX_HVAC, faces={"b": "skip"})
    mb.detail_box_ft(365.5, 1030.5, 13.2, 376.0, 1033.0, 14.6, TEX_GALV, faces={"w": "skip"})
    mb.detail_box_ft(344.0, 1044.0, GC_ROOF_Z_FT, 350.5, 1050.5, 15.5, TEX_HVAC, faces={"b": "skip"})

    # 7. East BOH Wing Flat Roof & Plain Parapet (x = 389.5 .. 413.5, z = 10.5 .. 12.75, NO East Merlons!)
    z_boh_c = GC_BOH_CEIL_Z_FT     # 10.5 ft
    z_boh_r = GC_BOH_ROOF_Z_FT     # 11.5 ft
    z_boh_p = GC_BOH_PARAPET_Z_FT  # 12.75 ft
    bx1 = GC_BLDG_BOUNDS_FT[2]     # 413.5 ft

    mb.detail_box_ft(x_split, 997.0, z_boh_c, bx1 - wt, 1066.5, z_boh_r, TEX_TPO, faces={"b": "skip", "e": "skip", "s": "skip", "n": "skip"})
    # 3-sided BOH parapet walls + concrete top caps
    mb.detail_box_ft(x_split, 1066.5, z_boh_c, bx1, 1067.5, z_boh_p, TEX_GCCMU, faces={"b": "skip", "t": TEX_CONC})
    mb.detail_box_ft(x_split, 996.0, z_boh_c, bx1, 997.0, z_boh_p, TEX_GCCMU, faces={"b": "skip", "t": TEX_CONC})
    mb.detail_box_ft(bx1 - wt, 997.0, z_boh_c, bx1, 1066.5, z_boh_p, TEX_GCCMU, faces={"b": "skip", "t": TEX_CONC, "s": "skip", "n": "skip"})

    # 3 Tan Louvered Swamp Coolers + Round Galvanized Kitchen Exhaust Stack on East BOH roof
    for sy in (1010.0, 1028.0, 1050.0):
        mb.detail_box_ft(396.2, sy - 1.6, z_boh_r, 399.8, sy + 1.6, z_boh_r + 0.65, TEX_GALV, faces={"b": "skip"})
        mb.detail_box_ft(
            395.5, sy - 2.2, z_boh_r + 0.65, 400.5, sy + 2.2, z_boh_r + 3.85,
            TEX_SWAMP, faces={"t": TEX_HVAC, "b": "skip"},
        )
    # Round galvanized kitchen hood exhaust stack + mushroom cap
    mb.cyl_ft(406.8, 1039.5, 1.05, z_boh_r, z_boh_r + 3.4, sides=8, tex_side=TEX_GALV, tex_top="skip", group="detail")
    mb.cyl_ft(406.8, 1039.5, 1.55, z_boh_r + 3.4, z_boh_r + 3.9, sides=8, tex_side=TEX_GALV, tex_top=TEX_GALV, group="detail")
    mb.detail_box_ft(399.5, 1038.5, z_boh_r + 0.4, 406.0, 1040.5, z_boh_r + 1.8, TEX_GALV)


def _build_gc_facades_and_canopies(mb: MapBuilder) -> None:
    """Main West channel sign, SW 410 & plaque, crimson barrel-vault canopy, secondary awning & BOH alley wall."""
    # 1. West Main Wall Channel Sign "GREAT CASTLE RESTAURANT 長城飯" (exact 8:1 aspect of 1024x128)
    mb.sign_decal_ft("w", 336.0, 1017.0, 1057.0, 11.5, 16.5, Fit("gwc_gcwest"))
    mb.light_ft(333.2, 1026.5, 17.2, light=135.0, color=(255, 232, 198), wait=0.75)
    mb.light_ft(333.2, 1047.5, 17.2, light=135.0, color=(255, 232, 198), wait=0.75)

    # 2. SW Watchtower West Face House Number "410" + Sconce Spotlight above SW rock garden
    mb.sign_decal_ft("w", 354.0, 999.8, 1002.2, 12.4, 13.6, Fit("gwc_gc410"))
    mb.detail_box_ft(352.9, 1000.1, 14.3, 354.0, 1000.9, 14.55, TEX_DARK, faces={"e": "skip"})
    mb.detail_box_ft(352.5, 999.9, 13.9, 353.3, 1001.1, 14.3, TEX_DARK, faces={"b": TEX_WHITE})
    mb.light_ft(351.8, 1000.5, 13.4, light=140.0, color=(255, 224, 178), wait=0.75)

    # 3. SW Watchtower South Face Illuminated Yellow Plaque "城堡" (2:1 aspect of 256x128) + Unclipped "OPEN"
    mb.sign_decal_ft("s", 996.0, 362.5, 369.5, 13.0, 16.5, Fit("gwc_gcplaque"))
    mb.sign_decal_ft("s", 996.0, 371.5, 373.7, 6.0, 7.1, Fit("gwc_gcopen"))

    # 4. Crimson Arched Barrel-Vault Canopy over south_main_entry (x=362..370, z=0.5..9.0 unobstructed!)
    # Vault spring z=9.45 -> crown z=11.90; non-overlapping valence skirt z=9.20..9.45 (104.4u clear above 6u floor)
    _barrel_canopy_xz_ft(mb, xc=366.0, half_w=4.5, y0=987.5, y1=996.0, z_spring=9.45, z_crown=11.90, thick_ft=0.28, segs=6)
    mb.detail_box_ft(361.5, 987.5, 9.20, 361.85, 996.0, 9.45, TEX_WHITE, faces={"n": "skip", "t": "skip"})
    mb.detail_box_ft(370.15, 987.5, 9.20, 370.5, 996.0, 9.45, TEX_WHITE, faces={"n": "skip", "t": "skip"})
    mb.detail_box_ft(361.85, 987.5, 9.20, 370.15, 987.75, 9.45, TEX_WHITE, faces={"w": "skip", "e": "skip"})
    # Two thin crimson support pipe columns strictly outside 362..370 (clear width = 8.3ft = 99.6u >> 78u)
    mb.cyl_ft(361.70, 988.15, 0.14, Z_WALK_FT, 9.25, sides=6, tex_side=TEX_RED, tex_top="skip", group="detail")
    mb.cyl_ft(370.30, 988.15, 0.14, Z_WALK_FT, 9.25, sides=6, tex_side=TEX_RED, tex_top="skip", group="detail")
    mb.clip_box_ft(361.50, 987.95, Z_WALK_FT, 361.90, 988.35, 9.25)
    mb.clip_box_ft(370.10, 987.95, Z_WALK_FT, 370.50, 988.35, 9.25)
    # Pulled-back scissor security gates strictly flanking outside 362..370
    mb.flush_panel_ft(360.8, 995.5, Z_WALK_FT, 361.5, 995.9, 8.8, {"s": Fit("{gwc_gcgate")}, group="illus")
    mb.flush_panel_ft(370.5, 995.5, Z_WALK_FT, 371.2, 995.9, 8.8, {"s": Fit("{gwc_gcgate")}, group="illus")
    mb.light_ft(366.0, 991.8, 10.6, light=160.0, color=(255, 224, 185), wait=0.7)

    # 5. Secondary Sloped Red Awning East of Watchtower (x=381..386, y=992..996) + framed grey steel service door
    mb.sign_decal_ft("s", 996.0, 381.9, 385.1, Z_WALK_FT, 7.6, TEX_CONC)
    mb.detail_box_ft(381.7, 995.8, Z_WALK_FT, 381.9, 996.0, 7.8, TEX_WHITE, faces={"n": "skip", "b": "skip"})
    mb.detail_box_ft(385.1, 995.8, Z_WALK_FT, 385.3, 996.0, 7.8, TEX_WHITE, faces={"n": "skip", "b": "skip"})
    mb.detail_box_ft(381.9, 995.8, 7.6, 385.1, 996.0, 7.8, TEX_WHITE, faces={"n": "skip", "w": "skip", "e": "skip"})
    mb.sign_decal_ft("s", 995.92, 382.7, 384.3, 4.4, 6.2, TEX_GLASS)
    mb.detail_box_ft(382.2, 995.75, 3.6, 384.8, 995.92, 3.85, TEX_STEEL, faces={"n": "skip"})
    mb.awning_ft("y", 381.0, 992.0, 386.0, 996.0, 10.2, 8.6, -1, Fit("gwc_gcawn"), thick_ft=0.25)
    mb.detail_box_ft(381.0, 991.75, 8.10, 386.0, 992.0, 8.65, TEX_RED, faces={"s": Fit("gwc_gcawn")})

    # 6. East BOH Alley Wall Utility Gear & Scissor Screen (clipped strictly inside x <= 413.95)
    bx1 = GC_BLDG_BOUNDS_FT[2]  # 413.5 ft
    # Framed recessed grey steel service door behind translucent {gwc_gcgate diamond cage (zero solid black backing!)
    mb.sign_decal_ft("e", bx1, 1012.2, 1018.8, Z_WALK_FT, 7.6, TEX_CONC)
    mb.detail_box_ft(bx1, 1011.9, Z_WALK_FT, bx1 + 0.25, 1012.2, 7.9, TEX_WHITE, faces={"w": "skip", "b": "skip"})
    mb.detail_box_ft(bx1, 1018.8, Z_WALK_FT, bx1 + 0.25, 1019.1, 7.9, TEX_WHITE, faces={"w": "skip", "b": "skip"})
    mb.detail_box_ft(bx1, 1012.2, 7.6, bx1 + 0.25, 1018.8, 7.9, TEX_WHITE, faces={"w": "skip", "s": "skip", "n": "skip"})
    mb.flush_panel_ft(bx1 + 0.30, 1012.0, Z_WALK_FT, bx1 + 0.38, 1019.0, 7.8, {"e": Fit("{gwc_gcgate")}, group="illus")
    # Small neat weathered light-grey/white plywood boarded window (#087 / #095 parity)
    mb.detail_box_ft(bx1, 1037.0, 4.1, bx1 + 0.14, 1040.8, 7.5, TEX_CONC, faces={"w": "skip"})
    mb.detail_box_ft(bx1, 1052.5, 2.2, bx1 + 0.45, 1055.0, 6.2, TEX_GALV, faces={"w": "skip"})
    mb.detail_box_ft(bx1, 1053.6, 6.2, bx1 + 0.25, 1054.0, 12.4, TEX_GALV, faces={"w": "skip"})
    mb.light_ft(bx1 + 1.0, 1015.5, 9.2, light=135.0, color=(255, 230, 190), wait=0.75)
    # Small green refuse bin tucked just south of BOH corner
    mb.detail_box_ft(410.0, 991.5, Z_WALK_FT, 413.4, 995.5, 3.6, TEX_DUMPSTR, faces={"b": "skip", "t": TEX_DARK})
    mb.clip_box_ft(410.0, 991.5, Z_WALK_FT, 413.4, 995.5, 3.8)


def _build_gc_sw_rock_garden(mb: MapBuilder) -> None:
    """SW Notch cobblestone rock garden, clustered granite boulders, monolith & tiered shrubs (#164)."""
    nx0, ny0, nx1, ny1 = GC_SW_NOTCH_FT  # (336.0, 996.0, 354.0, 1006.5)

    # Raised concrete perimeter border curb + river-rock stone bed (outside GC_POLY_FT)
    _curb_ft(mb, nx0, ny0, Z_GROUND_FT, nx1, ny0 + 1.0, Z_CURB_FT, TEX_CONC)
    _curb_ft(mb, nx0, ny0 + 1.0, Z_GROUND_FT, nx0 + 1.0, ny1, Z_CURB_FT, TEX_CONC, faces={"s": "skip"})
    _curb_ft(mb, nx0 + 1.0, ny0 + 1.0, Z_GROUND_FT, nx1, ny1, 0.55, TEX_GCSTONE, faces={"w": "skip", "s": "skip"})

    # Standing tapered granite monolith (~5.8 ft tall at x=346.0, y=1001.0) + Hull-1 clip flush to Dining wall
    bx, by = 346.0, 1001.0
    mb.cyl_ft(bx, by, 1.55, 0.55, 3.3, sides=6, tex_side=TEX_GCSTONE, tex_top=TEX_GCSTONE, group="detail")
    mb.cyl_ft(bx + 0.15, by + 0.10, 0.95, 3.3, 6.0, sides=6, tex_side=TEX_GCSTONE, tex_top=TEX_GCSTONE, group="detail")
    mb.clip_box_ft(bx - 1.55, by - 1.55, 0.55, bx + 1.55, ny1, 6.1)

    # Clustered lower granite accent boulders across stone bed
    for rx, ry, rr, rh in (
        (342.4, 998.4, 1.05, 1.6),
        (348.8, 998.6, 1.25, 2.3),
        (338.8, 1002.2, 0.95, 1.4),
    ):
        mb.cyl_ft(rx, ry, rr, 0.55, 0.55 + rh, sides=6, tex_side=TEX_GCSTONE, tex_top=TEX_GCSTONE, group="detail")

    # 6 Varied tiered sculpted shrubs (non-blocking illus so rock garden has zero Hull-1 trap hollows)
    for sx, sy, sr, sh in (
        (338.6, 998.8, 1.35, 2.1),
        (339.0, 1004.6, 1.40, 5.2),
        (342.4, 1004.0, 1.45, 3.6),
        (349.8, 1004.0, 1.45, 3.2),
        (345.0, 998.0, 1.15, 1.8),
        (352.0, 999.2, 1.25, 2.6),
    ):
        mb.illus_box_ft(sx - sr, sy - sr, 0.55, sx + sr, sy + sr, 0.55 + sh, TEX_HEDGE, faces={"b": "skip"})

    # 4 West facade low planter shrubs along Union wall (x=334..336)
    _curb_ft(mb, 334.0, 1008.0, Z_LOT_FT, 336.0, 1067.5, Z_CURB_FT, TEX_MULCH, faces={"w": TEX_CURB})
    for sy in (1014.0, 1028.0, 1044.0, 1058.0):
        mb.detail_box_ft(334.1, sy - 1.4, Z_CURB_FT, 335.9, sy + 1.4, Z_CURB_FT + 1.9, TEX_HEDGE, faces={"b": "skip"})


def _build_gc_se_annex(mb: MapBuilder) -> None:
    """SE Annex BLDG 60028772 (383..410.5 x 899..948): white CMU, eyebrow canopy, barred windows, vents & roll-up bay."""
    ax0, ay0, ax1, ay1 = GC_ANNEX_BOUNDS_FT  # (383.0, 899.0, 410.5, 948.0)

    # Flush concrete storefront sidewalk along West annex frontage
    _curb_ft(mb, ax0 - 3.5, ay0, Z_LOT_FT, ax0, ay1, Z_WALK_FT, TEX_CONC, faces={"e": "skip"})

    # Solid CMU lower commercial mass (stepped chamfered SW alcove at x=383..386, y=899..908)
    mb.detail_box_ft(ax0, ay0 + 9.0, Z_LOT_FT, ax1, ay1, 13.5, TEX_GCCMU, faces={"b": "skip", "t": TEX_TPO})
    mb.detail_box_ft(ax0 + 3.0, ay0, Z_LOT_FT, ax1, ay0 + 9.0, 13.5, TEX_GCCMU, faces={"b": "skip", "t": TEX_TPO})

    # Raised SE architectural corner parapet & south fascia parapet
    mb.detail_box_ft(398.0, ay0, 13.5, ax1, ay0 + 15.0, 15.8, TEX_GCCMU, faces={"b": "skip"})
    mb.detail_box_ft(ax0 + 3.0, ay0, 13.5, 398.0, ay0 + 1.2, 14.8, TEX_GCCMU, faces={"b": "skip", "e": "skip"})
    mb.detail_box_ft(ax0, ay0 + 9.0, 13.5, ax0 + 1.0, ay1, 14.2, TEX_GCCMU, faces={"b": "skip"})
    mb.detail_box_ft(ax1 - 1.0, ay0 + 15.0, 13.5, ax1, ay1, 14.2, TEX_GCCMU, faces={"b": "skip", "s": "skip"})
    mb.detail_box_ft(ax0 + 1.0, ay1 - 1.0, 13.5, ax1 - 1.0, ay1, 14.2, TEX_GCCMU, faces={"b": "skip", "w": "skip", "e": "skip"})

    # Rooftop compact HVAC condenser box
    mb.detail_box_ft(391.0, 922.0, 13.5, 395.5, 926.5, 16.0, TEX_HVAC, faces={"b": "skip"})

    # SW chamfered entry alcove: horizontal white eyebrow awning over closed barred glass door
    mb.detail_box_ft(ax0, ay0, Z_LOT_FT, ax0 + 3.0, ay0 + 9.0, Z_WALK_FT, TEX_CONC, faces={"b": "skip", "w": "skip", "e": "skip", "n": "skip"})
    mb.detail_box_ft(ax0 - 0.5, ay0 + 0.5, 8.3, ax0 + 3.0, ay0 + 8.5, 8.8, TEX_WHITE, faces={"e": "skip"})
    mb.sign_decal_ft("w", ax0 + 3.0, ay0 + 1.8, ay0 + 6.8, Z_WALK_FT, 7.8, TEX_GLASS)
    mb.flush_panel_ft(ax0 + 2.75, ay0 + 1.8, Z_WALK_FT, ax0 + 2.83, ay0 + 6.8, 7.8, {"w": Fit("{gwc_ironfence")}, group="illus")
    mb.light_ft(ax0 + 1.2, ay0 + 4.5, 8.0, light=130.0, color=(255, 226, 185), wait=0.75)

    # West facade barred store windows + 3 upper dark rectangular louver vents
    for wy0, wy1 in ((915.0, 923.0), (930.0, 938.0)):
        mb.sign_decal_ft("w", ax0, wy0, wy1, 3.0, 7.6, TEX_GLASS)
        mb.flush_panel_ft(ax0 - 0.25, wy0, 3.0, ax0 - 0.17, wy1, 7.6, {"w": Fit("{gwc_ironfence")}, group="illus")
        mb.detail_box_ft(ax0 - 0.30, wy0 - 0.15, 2.75, ax0, wy1 + 0.15, 3.0, TEX_DARK, faces={"e": "skip"})

    for vy in (914.0, 926.0, 938.0):
        mb.sign_decal_ft("w", ax0, vy - 2.0, vy + 2.0, 10.4, 11.8, TEX_SWAMP)

    # East alley corrugated roll-up bay door + protective yellow pipe bollards + sconce
    mb.sign_decal_ft("e", ax1, 926.0, 936.0, Z_WALK_FT, 8.5, Fit("gwc_rollup"))
    for by in (925.2, 936.8):
        mb.cyl_ft(ax1 + 0.7, by, 0.22, Z_LOT_FT, 3.8, sides=6, tex_side=TEX_CURBRED, tex_top=TEX_CURBRED, group="detail")
        mb.clip_box_ft(ax1 + 0.45, by - 0.25, Z_LOT_FT, ax1 + 0.95, by + 0.25, 4.0)
    mb.light_ft(ax1 + 1.5, 931.0, 9.6, light=135.0, color=(255, 228, 188), wait=0.75)


def _build_gc_signs_fences_props(mb: MapBuilder) -> None:
    """Union pylon signs, E 5th stepped brick-cap CMU wall, north cypresses, SW Valley Oak, dumpsters, lights & cars."""
    lx0, ly0, lx1, ly1 = GC_LOT_FT

    # 1. Union Ave Two-Post Pylon Cabinet "GREAT CASTLE / RESTAURANT" + 6 mini merlons (y=980..992)
    _curb_ft(mb, lx0, 978.5, Z_LOT_FT, lx0 + 5.2, 993.5, 0.55, TEX_MULCH, faces={"w": TEX_CURB, "e": TEX_CURB, "s": TEX_CURB, "n": TEX_CURB})
    mb.detail_box_ft(285.8, 981.6, 0.55, 286.6, 982.4, 11.5, TEX_WHITE, faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(285.8, 989.6, 0.55, 286.6, 990.4, 11.5, TEX_WHITE, faces={"b": "skip", "t": "skip"})
    mb.clip_box_ft(285.6, 981.4, Z_LOT_FT, 286.8, 990.6, 11.5)
    # 12 ft x 6 ft cabinet = exact 2:1 aspect of 512x256 gwc_gcpylon
    mb.detail_box_ft(
        285.5, 980.0, 11.5, 286.9, 992.0, 17.5,
        TEX_WHITE, faces={"w": Fit("gwc_gcpylon"), "e": Fit("gwc_gcpylon")},
    )
    _merlon_strip_y(mb, 285.6, 286.8, 980.3, 991.7, 17.5, 18.6, pitch=1.9, tooth_w=1.1, face_dir="w")
    mb.light_ft(283.8, 986.0, 14.5, light=145.0, color=(255, 240, 210), wait=0.7)
    mb.light_ft(288.6, 986.0, 14.5, light=145.0, color=(255, 240, 210), wait=0.7)

    # 2. NW Corner (Union & E 5th) Empty 2-Post Pylon Frame (tall steel/white posts, no sign face!)
    _curb_ft(mb, lx0, 1150.5, Z_LOT_FT, lx0 + 5.2, 1164.0, 0.55, TEX_MULCH, faces={"w": TEX_CURB, "e": TEX_CURB, "s": TEX_CURB, "n": TEX_CURB})
    mb.detail_box_ft(285.9, 1152.2, 0.55, 286.6, 1152.9, 18.5, TEX_WHITE, faces={"b": "skip"})
    mb.detail_box_ft(285.9, 1160.1, 0.55, 286.6, 1160.8, 18.5, TEX_WHITE, faces={"b": "skip"})
    mb.detail_box_ft(286.0, 1152.9, 12.2, 286.5, 1160.1, 12.7, TEX_STEEL, faces={"s": "skip", "n": "skip"})
    mb.detail_box_ft(286.0, 1152.9, 18.0, 286.5, 1160.1, 18.5, TEX_STEEL, faces={"s": "skip", "n": "skip"})
    mb.clip_box_ft(285.7, 1152.0, Z_LOT_FT, 286.8, 1161.0, 12.0)

    # 3. Union Frontage Landscape Mulch Strips & SW Corner Valley Oak Broadleaf Tree
    for y0, y1 in ((896.0, 947.0), (995.0, 1093.0), (1127.0, 1149.5)):
        _curb_ft(mb, lx0, y0, Z_LOT_FT, lx0 + 2.6, y1, 0.52, TEX_MULCH, faces={"e": TEX_CURB, "w": TEX_CURB})
    # SW corner planter + 1 medium Valley Oak broadleaf tree ({gwc_tree2, strictly inside GC_LOT_FT)
    _curb_ft(mb, lx0, ly0, Z_LOT_FT, 295.0, 895.0, 0.62, TEX_MULCH, faces={"e": TEX_CURB, "n": TEX_CURB})
    _alpha_quad_tree(mb, 289.2, 889.2, 0.62, half_w=5.6, height_ft=18.0, tex_name="{gwc_tree2", trunk_h=6.2, trunk_r=0.50)

    # 4. E 4th St Perimeter Low Wheel Curb Segments (open driveway cut at x=342..368)
    _curb_ft(mb, 295.5, ly0, Z_LOT_FT, 341.0, ly0 + 1.5, 0.62, TEX_CURB)
    _curb_ft(mb, 369.0, ly0, Z_LOT_FT, 383.0, ly0 + 1.5, 0.62, TEX_CURBRED)

    # 5. Stepped White CMU + Red Brick-Cap Wall along E 5th St & NE Alley (open driveway cut at x=342..370)
    # Non-overlapping wall spans cleanly segmented between brick-capped masonry pilasters
    mb.detail_box_ft(292.8, ly1 - 1.4, Z_LOT_FT, 294.2, ly1, 3.9, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK})
    mb.detail_box_ft(294.2, ly1 - 1.2, Z_LOT_FT, 325.1, ly1, 3.6, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK, "w": "skip", "e": "skip"})
    mb.detail_box_ft(325.1, ly1 - 1.4, Z_LOT_FT, 326.5, ly1, 3.9, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK})
    mb.detail_box_ft(326.5, ly1 - 1.2, Z_LOT_FT, 341.5, ly1, 2.4, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK, "w": "skip"})
    # East of E 5th driveway: 5.2ft privacy wall + pilasters + red brick coping wrapping NE alley corner
    mb.detail_box_ft(370.1, ly1 - 1.4, Z_LOT_FT, 371.5, ly1, 5.5, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK})
    mb.detail_box_ft(371.5, ly1 - 1.2, Z_LOT_FT, 391.3, ly1, 5.2, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK, "w": "skip", "e": "skip"})
    mb.detail_box_ft(391.3, ly1 - 1.4, Z_LOT_FT, 392.7, ly1, 5.5, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK})
    mb.detail_box_ft(392.7, ly1 - 1.2, Z_LOT_FT, 412.5, ly1, 5.2, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK, "w": "skip", "e": "skip"})
    mb.detail_box_ft(412.5, ly1 - 1.4, Z_LOT_FT, lx1, ly1, 5.5, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK})
    mb.detail_box_ft(lx1 - 1.2, 1138.0, Z_LOT_FT, lx1, ly1 - 1.4, 5.2, TEX_GCCMU, faces={"b": "skip", "t": TEX_BRICK, "n": "skip"})

    # 6. North Wall Soil Planter Beds + 6 Slender Italian Cypress Trees ({gwc_cypress) + NE Gas Meter
    for bx0, bx1 in ((336.5, 356.5), (366.5, 396.5), (406.5, 413.5)):
        _curb_ft(mb, bx0, 1067.5, Z_LOT_FT, bx1, 1070.5, 0.55, TEX_MULCH, faces={"s": "skip", "n": TEX_CURB})
    for cy_x in (342.0, 350.0, 372.0, 380.5, 389.0, 410.0):
        _alpha_quad_tree(mb, cy_x, 1069.1, 0.55, half_w=1.45, height_ft=14.0, tex_name="{gwc_cypress", trunk_h=0.0)
    # NE gas meter & 2 yellow guard bollards cleanly clear of north_kitchen_exit (398..405)
    mb.detail_box_ft(407.5, 1067.5, 1.5, 409.5, 1068.5, 4.2, TEX_GALV, faces={"s": "skip"})
    for blx in (407.2, 411.5):
        mb.cyl_ft(blx, 1068.4, 0.20, 0.55, 3.6, sides=6, tex_side=TEX_CURBRED, tex_top=TEX_CURBRED, group="detail")
        mb.clip_box_ft(blx - 0.22, 1068.2, 0.55, blx + 0.22, 1068.7, 3.8)
    mb.light_ft(401.5, 1069.5, 9.6, light=135.0, color=(255, 228, 190), wait=0.75)

    # 7. NE Alley Corner 2 Green Commercial Steel Dumpsters (x=402..411.5, y=1144..1163)
    _curb_ft(mb, 401.5, 1142.0, Z_LOT_FT, 412.2, 1165.0, 0.42, TEX_CONC)
    for dy in (1147.0, 1158.0):
        mb.detail_box_ft(403.5, dy - 3.6, 0.42, 410.5, dy + 3.6, 4.6, TEX_DUMPSTR, faces={"b": "skip", "t": "skip"})
        mb.detail_box_ft(403.2, dy - 3.8, 4.6, 410.8, dy + 3.8, 5.1, TEX_DARK)

    # 8. Two Parking Lot Shoebox Lights & 4 Cleanly Spaced Lot Vehicles
    _shoebox_light(mb, 337.0, 944.0)
    _shoebox_light(mb, 338.0, 1118.0)

    _parked_car(mb, 295.0, 913.5, axis="x", tex_body="gwc_carsil", is_suv=False)
    _parked_car(mb, 389.5, 983.5, axis="y", tex_body="gwc_carblu", is_suv=True)
    _parked_car(mb, 316.0, 1020.5, axis="x", tex_body="gwc_carwht", is_suv=False)
    _parked_car(mb, 320.5, 1084.0, axis="y", tex_body="gwc_carred", is_suv=True)


def build_gc_ext(mb: MapBuilder) -> Dict[str, object]:
    """Build all Great Castle exterior, sitework, roofs, SW watchtower & SE annex."""
    _refresh_tiles()

    _build_gc_lot_paving(mb)
    _build_gc_roofs_and_watchtower(mb)
    _build_gc_facades_and_canopies(mb)
    _build_gc_sw_rock_garden(mb)
    _build_gc_se_annex(mb)
    _build_gc_signs_fences_props(mb)

    # Registered exterior camera/QA spots (inside GC_LOT_FT / adjacent GC_ALLEY_X w/ explicit yaw & pitch)
    mb.spot_ft("gc_union_pylon", 296.0, 946.0, 6.0, yaw=82.0, pitch=-4.0, desc="South Union lot view framing Union pylon and Great Castle West wall")
    mb.spot_ft("gc_sw_watchtower_entry", 355.0, 966.0, 5.5, yaw=76.0, pitch=-5.0, desc="Watchtower, crimson barrel canopy, 城堡, OPEN & SW rock garden")
    mb.spot_ft("gc_sw_rock_garden", 338.0, 978.0, 5.5, yaw=64.0, pitch=-3.0, desc="SW river-rock garden, monolith boulder, 410 sconce & entry canopy")
    mb.spot_ft("gc_south_lot", 316.0, 954.0, 6.0, yaw=38.0, pitch=-3.0, desc="South parking lot looking NE at Watchtower and SE Annex")
    mb.spot_ft("gc_north_lot", 336.0, 1136.0, 6.0, yaw=290.0, pitch=-3.0, desc="North parking lot looking SSE at North exits & Italian cypresses")
    mb.spot_ft("gc_se_annex_alley", 421.5, 892.0, 6.0, yaw=112.0, pitch=-2.0, desc="East alley centerline looking NNW along SE Annex roll-up bay to BOH coolers")
    return mb.stats()


def _build_standalone_test_shell(mb: MapBuilder) -> None:
    """Sealed test shell around Great Castle lot + dummy building mass for standalone compilation."""
    t = 16.0
    lx0, ly0, lx1, ly1 = GC_LOT_FT
    pad = 40.0
    sx0, sy0, sx1, sy1 = lx0 - pad, ly0 - pad, lx1 + pad, ly1 + pad
    sz0, sz1 = -8.0, 72.0

    mb.structural_box_ft(sx0 - t, sy0 - t, sz1, sx1 + t, sy1 + t, sz1 + t, "sky")
    mb.structural_box_ft(sx0 - t, sy0 - t, sz0 - t, sx1 + t, sy1 + t, sz0, "sky")
    mb.structural_box_ft(sx0 - t, sy0 - t, sz0, sx0, sy1 + t, sz1, "sky")
    mb.structural_box_ft(sx1, sy0 - t, sz0, sx1 + t, sy1 + t, sz1, "sky")
    mb.structural_box_ft(sx0, sy0 - t, sz0, sx1, sy0, sz1, "sky")
    mb.structural_box_ft(sx0, sy1, sz0, sx1, sy1 + t, sz1, "sky")
    mb.structural_box_ft(sx0, sy0, sz0, sx1, sy1, Z_GROUND_FT, Tile("gwc_dirt", 24.0, 24.0))

    # Minimal closed dummy interior core under Great Castle roofs for isolated leak/lighting preview
    mb.detail_box_ft(336.0, 1006.5, Z_GROUND_FT, 354.0, 1067.5, GC_CEIL_Z_FT, TEX_GCCMU)
    mb.detail_box_ft(354.0, 996.0, Z_GROUND_FT, 389.5, 1067.5, GC_CEIL_Z_FT, TEX_GCCMU)
    mb.detail_box_ft(389.5, 996.0, Z_GROUND_FT, 413.5, 1067.5, GC_BOH_CEIL_Z_FT, TEX_GCCMU)
    mb.ent_ft("info_player_start", 355.0, 965.0, 4.0, angle=85)
    mb.light_ft(340.0, 1030.0, 42.0, light=300.0, color=(255, 244, 224), wait=0.5)


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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate gw_gc_ext.py standalone with MapBuilder.")
    parser.add_argument("--out", default="", help="Optional path to write standalone test .map")
    args = parser.parse_args(argv)

    mb = MapBuilder(check_textures=True, require_gwc_prefix=True)
    _build_standalone_test_shell(mb)
    build_gc_ext(mb)

    errors = mb.validate_all()
    stats = mb.stats()
    total_f, active_f = _count_faces(mb)
    legacy = [
        t for t in stats["textures_used"]
        if any(t.lstrip("{").startswith(p) for p in ("bk_", "bklan", "bk3_", "chain", "sky_bk"))
    ]
    print("gw_gc_ext standalone summary:")
    print(f"  brushes: {stats['brushes']}")
    print(f"  faces: total={total_f}, active_non_skip={active_f}")
    for k in ("total_brushes", "entities", "rooms", "doorways", "spots", "missing_textures"):
        print(f"  {k}: {stats[k]}")
    print(f"  textures_used_count: {len(stats['textures_used'])}")
    print(f"  textures_used: {sorted(stats['textures_used'])}")
    print(f"  legacy_textures: {legacy}")
    print(f"  validation_errors ({len(errors)}): {errors}")

    if args.out:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        mb.write_map(args.out)
        print(f"  wrote test map: {args.out}")

    return 0 if (not errors and not legacy and not stats["missing_textures"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
