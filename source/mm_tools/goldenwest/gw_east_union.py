"""gw_east_union.py — East Side of S Union Ave Neighborhood & Interiors Geometry.

Exclusive module for the East Union Ave parcels (x = 283.0 .. 650.0 ft):
  South / Central Block (y = -820.0 .. +750.0 ft, excl. Belle Terrace & Adams St):
  1. Century Glass & Auto Detail Yard (y=582..750) — enterable shop bay
  2. SE Belle Terrace Demolished El Don MOTEL Brownfield (y=424..532) — open lot + 2 signs
  3. Redwood Senior Living (y=326..424) — enterable front reception/lobby
  4. Star-Liter Motor Motel (x=283..505, y=26..326) — front office + 4 courtyard guest rooms
  5. 922 S Union Mobile Home / RV Park (y=-268..26 & x=505..650, y=26..326) — enterable office
  6. Sunland Motel (y=-366..-268) — check-in lobby + 2 guest rooms + breeze-block + bench
  7. Country Inn Motel (y=-555..-366) — front lobby + 4 courtyard guest rooms + Googie sign
  8. Playfair Market (y=-670..-595) — full enterable market w/ >=48u aisles & coolers
  9. South Strip (y=-820..-670) — 60016928, 60017599 (enterable front room), 60016099, 60017185

  Northern Great Castle Extension (y = 750.25 .. 1340.0 ft, excl. E 4th/E 5th/GC Alley/GC Lot):
  10. Deal Time Auto Sales & Yard (gc_deal_time, y=750.25..842)
  11. East of Alley Warehouse, Dirt Lot & Wallace Cottages (gc_alley_east, y=882..1168)
  12. Reyes Tires & Auto Bays + E 6th Rear Mass (gc_reyes_tires, y=1208..1340) — enterable bay
  13. North-of-E-5th Alley-East Cottages & Fringe (gc_north_fringe, y=1208..1340)

Uses ONLY cataloged gwc_* / {gwc_* textures + special textures (skip, clip).
Respects Hull-1 navigation tolerances (>=64x96u doors, >=112u ceilings, <=18u steps).
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, List, Optional, Sequence, Tuple

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

try:
    from gw_lib import (
        ADAMS_ST_CORRIDOR_Y,
        BELLE_TERRACE_CORRIDOR_Y,
        DEFAULT_WAD_PATHS,
        E_4TH_ST_CORRIDOR_Y,
        E_5TH_ST_CORRIDOR_Y,
        GC_ALLEY_X,
        GC_LOT_FT,
        HX1,
        HY0,
        HY1,
        PARCELS,
        U_FT,
        Fit,
        MapBuilder,
        Tile,
        tex_from_spec,
    )
except ImportError:  # package-qualified import fallback
    from .gw_lib import (  # type: ignore
        ADAMS_ST_CORRIDOR_Y,
        BELLE_TERRACE_CORRIDOR_Y,
        DEFAULT_WAD_PATHS,
        E_4TH_ST_CORRIDOR_Y,
        E_5TH_ST_CORRIDOR_Y,
        GC_ALLEY_X,
        GC_LOT_FT,
        HX1,
        HY0,
        HY1,
        PARCELS,
        U_FT,
        Fit,
        MapBuilder,
        Tile,
        tex_from_spec,
    )


# Safe inner X boundary inside HX1=650.0 so brushes never touch world sky hull wall.
EAST_X_MIN = 283.0
EAST_X_MAX = 649.5
BLDG_X_MAX = 647.5

GROUND_BOT = 0.0
GROUND_TOP = 2.0 / 12.0   # 2.0 u — flush with gw_streets Z_ROAD_FT
ACCENT_TOP = 2.5 / 12.0   # 2.5 u — non-overlapping lot driveway / pad overlay
FLOOR_TOP = 0.32
CEIL_CLR_H = 10.0  # 120u clear ceiling >= HULL1_MIN_CEIL_U (112u)
WALL_T = 0.60


# =============================================================================
# SHARED GEOMETRY HELPERS
# =============================================================================

def _ground_pad(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    tex: str | Tile | Fit,
    z0: float = GROUND_BOT,
    z1: float = GROUND_TOP,
) -> None:
    """Emit a flat parcel ground/lot surface pad with skipped underside."""
    mb.detail_box_ft(
        x0,
        y0,
        z0,
        x1,
        y1,
        z1,
        tex,
        faces={"b": "skip"},
    )


def _gable_roof(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_eave: float,
    rise: float,
    ridge_axis: str = "x",
    eave: float = 0.75,
    tex_roof: str = "gwc_resshing",
    tex_gable: str = "gwc_crmstuc",
    tex_fascia: str = "gwc_white",
    fascia_h: float = 0.35,
) -> None:
    """Build a crisp browser-friendly pitched gable roof with overhang fascia."""
    rx0, rx1 = x0 - eave, x1 + eave
    ry0, ry1 = y0 - eave, y1 + eave
    # Keep fascia strictly above interior z_ceil (z_eave - 0.36 >= z_ceil + 0.19)
    eff_fascia_h = min(float(fascia_h), 0.36)
    mb.detail_box_ft(
        rx0,
        ry0,
        z_eave - eff_fascia_h,
        rx1,
        ry1,
        z_eave + 0.08,
        Tile(tex_fascia, w_ft=4.0),
        faces={"t": "skip", "b": "gwc_white"},
    )
    roof_spec = Tile(tex_roof, w_ft=6.0)
    gable_spec = Tile(tex_gable, w_ft=8.0)
    z0 = z_eave + 0.08
    z_pk = z0 + rise
    if ridge_axis == "x":
        # Ridge runs E-W (along X); gable ends face W (x0) and E (x1)
        ym = 0.5 * (ry0 + ry1)
        mb.prism_yz_ft(
            [(ry0, z0), (ry1, z0), (ym, z_pk)],
            rx0,
            rx1,
            tex_side=roof_spec,
            tex_end=gable_spec,
            group="detail",
        )
    else:
        # Ridge runs N-S (along Y); gable ends face S (y0) and N (y1)
        xm = 0.5 * (rx0 + rx1)
        mb.prism_xz_ft(
            [(rx0, z0), (rx1, z0), (xm, z_pk)],
            ry0,
            ry1,
            tex_side=roof_spec,
            tex_end=gable_spec,
            group="detail",
        )


def _hip_roof(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_eave: float,
    rise: float,
    eave: float = 0.85,
    tex_roof: str = "gwc_resshing",
    tex_fascia: str = "gwc_white",
    fascia_h: float = 0.35,
) -> None:
    """Build a compact sloped hip-mansard roof profile cleanly above eaves."""
    rx0, rx1 = x0 - eave, x1 + eave
    ry0, ry1 = y0 - eave, y1 + eave
    eff_fascia_h = min(float(fascia_h), 0.36)
    mb.detail_box_ft(
        rx0,
        ry0,
        z_eave - eff_fascia_h,
        rx1,
        ry1,
        z_eave + 0.08,
        Tile(tex_fascia, w_ft=4.0),
        faces={"t": "skip", "b": "gwc_white"},
    )
    inset_x = min(0.28 * (rx1 - rx0), 6.0)
    inset_y = min(0.28 * (ry1 - ry0), 6.0)
    z0 = z_eave + 0.08
    z1 = z0 + rise
    roof_spec = Tile(tex_roof, w_ft=6.0)
    mb.prism_xz_ft(
        [(rx0, z0), (rx1, z0), (rx1 - inset_x, z1), (rx0 + inset_x, z1)],
        ry0,
        ry1,
        tex_side=roof_spec,
        tex_end=roof_spec,
        group="detail",
    )
    mb.detail_box_ft(
        rx0 + inset_x + 0.4,
        ry0 + inset_y,
        z1 - 0.15,
        rx1 - inset_x - 0.4,
        ry1 - inset_y,
        z1 + 0.45,
        roof_spec,
        faces={"b": "skip"},
    )


def _emit_detail_wall(
    mb: MapBuilder,
    axis: str,
    pos_ft: float,
    span0_ft: float,
    span1_ft: float,
    z0_ft: float,
    z1_ft: float,
    thick_ft: float,
    tex_pos: str | Tile | Fit,
    tex_neg: str | Tile | Fit,
    doors: Optional[List[Tuple[float, float, float, str]]],
    windows: Optional[List[Tuple[float, float, float, float]]],
    flush_bot: bool,
    flush_top: bool,
    skip_start: bool,
    skip_end: bool,
) -> None:
    """Emit func_detail room wall panels with concealed floor/ceiling/sill/abutment faces skipped."""
    u = mb.u_per_ft
    s0, s1 = sorted((span0_ft, span1_ft))
    z0, z1 = sorted((z0_ft, z1_ft))
    half_t = 0.5 * thick_ft
    pos_key, neg_key = ("n", "s") if axis == "x" else ("e", "w")
    lo_key, hi_key = ("w", "e") if axis == "x" else ("s", "n")

    def emit_panel(
        ps0: float, ps1: float, pz0: float, pz1: float,
        skip_lo: bool, skip_hi: bool, skip_b: bool, skip_t: bool,
    ) -> None:
        if (ps1 - ps0) * u < 0.5 or (pz1 - pz0) * u < 0.5:
            return
        faces: dict[str, str | Tile | Fit] = {pos_key: tex_pos, neg_key: tex_neg}
        if skip_lo:
            faces[lo_key] = "skip"
        if skip_hi:
            faces[hi_key] = "skip"
        if skip_b:
            faces["b"] = "skip"
        if skip_t:
            faces["t"] = "skip"
        if axis == "x":
            mb.box_ft(ps0, pos_ft - half_t, pz0, ps1, pos_ft + half_t, pz1, tex_pos, faces=faces, group="detail")
        else:
            mb.box_ft(pos_ft - half_t, ps0, pz0, pos_ft + half_t, ps1, pz1, tex_pos, faces=faces, group="detail")

    openings: List[Tuple[float, float, float, float, bool]] = []
    if doors:
        for idx, d in enumerate(doors):
            d0, d1, dtop = float(d[0]), float(d[1]), float(d[2])
            dname = str(d[3]) if len(d) >= 4 else f"door_{axis}_{idx}"
            a0, a1 = sorted((d0, d1))
            mb.register_door(dname, (a1 - a0) * u, (dtop - z0) * u, axis=axis)
            openings.append((a0, a1, z0, dtop, False))
    if windows:
        for w in windows:
            w0, w1 = sorted((float(w[0]), float(w[1])))
            wz0, wz1 = sorted((float(w[2]), float(w[3])))
            openings.append((w0, w1, wz0, wz1, True))

    clipped: List[Tuple[float, float, float, float, bool]] = []
    for o0, o1, oz0, oz1, is_win in sorted(openings, key=lambda o: o[0]):
        co0, co1 = max(s0, o0), min(s1, o1)
        if co1 > co0:
            clipped.append((co0, co1, oz0, oz1, is_win))

    cursor = s0
    for idx, (co0, co1, oz0, oz1, is_win) in enumerate(clipped):
        if co0 > cursor:
            emit_panel(cursor, co0, z0, z1, (cursor == s0 and skip_start), False, flush_bot, flush_top)
        next_start = clipped[idx + 1][0] if idx + 1 < len(clipped) else s1
        has_left_solid = (co0 == s0 and skip_start) or ((co0 - cursor) * u >= 1.0)
        has_right_solid = (co1 == s1 and skip_end) or ((next_start - co1) * u >= 1.0)
        if oz0 > z0:
            # Window spandrel top is buried inside the overhanging window sill box below.
            emit_panel(co0, co1, z0, min(oz0, z1), has_left_solid, has_right_solid, flush_bot, is_win)
        if oz1 < z1:
            # Door/window lintel bottom ('b') is the exposed soffit reveal; never skip it.
            emit_panel(co0, co1, max(oz1, z0), z1, has_left_solid, has_right_solid, False, flush_top)
        cursor = max(cursor, co1)
    if cursor < s1:
        emit_panel(cursor, s1, z0, z1, (cursor == s0 and skip_start), skip_end, flush_bot, flush_top)


def _room_wall(
    mb: MapBuilder,
    axis: str,
    pos_ft: float,
    span0_ft: float,
    span1_ft: float,
    z0_ft: float,
    z1_ft: float,
    thick_ft: float,
    out_side: str,
    tex_out: str | Tile | Fit,
    tex_in: str | Tile | Fit,
    doors: Optional[List[Tuple[float, float, float, str]]] = None,
    windows: Optional[List[Tuple[float, float, float, float]]] = None,
    win_tex: str = "gwc_blind",
    frame_tex: str = "gwc_dark",
    force_world: bool = False,
    flush_bot: bool = False,
    flush_top: bool = False,
    skip_start: bool = False,
    skip_end: bool = False,
) -> None:
    """Emit a room wall (func_detail by default; explicit force_world only for solid VIS blockers)."""
    # wall_xft assigns tex -> 'n' and tex_inside -> 's'.
    # wall_yft assigns tex -> 'e' and tex_inside -> 'w'.
    use_world = bool(force_world and not doors and not windows)
    if axis == "x":
        tex_pos = tex_out if out_side == "n" else tex_in
        tex_neg = tex_in if out_side == "n" else tex_out
    else:
        tex_pos = tex_out if out_side == "e" else tex_in
        tex_neg = tex_in if out_side == "e" else tex_out

    if use_world:
        # Keep structural worldspawn VIS walls at 0 skip faces.
        if axis == "x":
            mb.wall_xft(
                pos_ft, span0_ft, span1_ft, z0_ft, z1_ft, thick_ft, tex_pos,
                doorways=doors, windows=windows, tex_inside=tex_neg,
                group="world", force_world=True,
            )
        else:
            mb.wall_yft(
                pos_ft, span0_ft, span1_ft, z0_ft, z1_ft, thick_ft, tex_pos,
                doorways=doors, windows=windows, tex_inside=tex_neg,
                group="world", force_world=True,
            )
    else:
        _emit_detail_wall(
            mb, axis, pos_ft, span0_ft, span1_ft, z0_ft, z1_ft, thick_ft,
            tex_pos, tex_neg, doors, windows,
            flush_bot=flush_bot, flush_top=flush_top,
            skip_start=skip_start, skip_end=skip_end,
        )

    half_t = 0.5 * thick_ft
    if doors:
        # wall_xft/wall_yft already register each doorway via register_doorway_ft
        for d0, d1, dtop, _dname in doors:
            # Crisp door jamb header trim (1u above dtop so zero coplanar face with header soffit)
            if axis == "x":
                mb.detail_box_ft(
                    d0 - 0.15,
                    pos_ft - half_t - 0.04,
                    dtop + 0.08,
                    d1 + 0.15,
                    pos_ft + half_t + 0.04,
                    dtop + 0.32,
                    frame_tex,
                    faces={"t": "skip"},
                )
            else:
                mb.detail_box_ft(
                    pos_ft - half_t - 0.04,
                    d0 - 0.15,
                    dtop + 0.08,
                    pos_ft + half_t + 0.04,
                    d1 + 0.15,
                    dtop + 0.32,
                    frame_tex,
                    faces={"t": "skip"},
                )

    if windows:
        for w0, w1, wz0, wz1 in windows:
            if axis == "x":
                mb.detail_box_ft(
                    w0,
                    pos_ft - 0.08,
                    wz0,
                    w1,
                    pos_ft + 0.08,
                    wz1,
                    Fit(win_tex),
                    faces={"t": "skip", "b": "skip", "w": "skip", "e": "skip"},
                )
                mb.detail_box_ft(
                    w0 - 0.15,
                    pos_ft - half_t - 0.06,
                    wz0 - 0.18,
                    w1 + 0.15,
                    pos_ft + half_t + 0.06,
                    wz0 + 0.08,
                    frame_tex,
                )
            else:
                mb.detail_box_ft(
                    pos_ft - 0.08,
                    w0,
                    wz0,
                    pos_ft + 0.08,
                    w1,
                    wz1,
                    Fit(win_tex),
                    faces={"t": "skip", "b": "skip", "n": "skip", "s": "skip"},
                )
                mb.detail_box_ft(
                    pos_ft - half_t - 0.06,
                    w0 - 0.15,
                    wz0 - 0.18,
                    pos_ft + half_t + 0.06,
                    w1 + 0.15,
                    wz0 + 0.08,
                    frame_tex,
                )


def _build_room_shell(
    mb: MapBuilder,
    room_name: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_floor: float = FLOOR_TOP,
    ceil_h: float = CEIL_CLR_H,
    tex_ext: str | Tile | Fit = "gwc_crmstuc",
    tex_in: str | Tile | Fit = "gwc_wainscot",
    tex_floor: str | Tile | Fit = "gwc_tile",
    tex_ceil: str | Tile | Fit = "gwc_ceil2x2",
    doors_w: Optional[List[Tuple[float, float, float, str]]] = None,
    doors_e: Optional[List[Tuple[float, float, float, str]]] = None,
    doors_s: Optional[List[Tuple[float, float, float, str]]] = None,
    doors_n: Optional[List[Tuple[float, float, float, str]]] = None,
    wins_w: Optional[List[Tuple[float, float, float, float]]] = None,
    wins_e: Optional[List[Tuple[float, float, float, float]]] = None,
    wins_s: Optional[List[Tuple[float, float, float, float]]] = None,
    wins_n: Optional[List[Tuple[float, float, float, float]]] = None,
    win_tex: str = "gwc_blind",
    light: float = 280.0,
    light_color: Tuple[int, int, int] = (255, 224, 176),
    nx: int = 1,
    ny: int = 1,
    spot_yaw: float = 0.0,
    spot_desc: str = "",
    vis_walls: Sequence[str] = (),
    light_drop_ft: float = 0.85,
    skip_ceil_top: bool = True,
) -> float:
    """Construct a complete Hull-1-compliant enterable room and return ceiling top Z."""
    z_ceil = z_floor + ceil_h
    z_roof = z_ceil + 0.55
    ht = 0.5 * WALL_T

    # Floor & ceiling slabs in func_detail to keep worldspawn clean for macro VIS blockers
    mb.detail_box_ft(
        x0,
        y0,
        0.0,
        x1,
        y1,
        z_floor,
        tex_floor,
        faces={"b": "skip"},
    )
    ceil_faces: dict[str, str | Tile | Fit] = {"b": tex_ceil}
    if skip_ceil_top:
        ceil_faces["t"] = "skip"
    mb.detail_box_ft(
        x0,
        y0,
        z_ceil,
        x1,
        y1,
        z_roof,
        tex_ext,
        faces=ceil_faces,
    )

    # Four perimeter walls centered along inner inset by ht so exterior matches x0..x1, y0..y1
    _room_wall(
        mb,
        "y",
        x0 + ht,
        y0,
        y1,
        z_floor,
        z_ceil,
        WALL_T,
        "w",
        tex_ext,
        tex_in,
        doors=doors_w,
        windows=wins_w,
        win_tex=win_tex,
        force_world=("w" in vis_walls),
        flush_bot=True,
        flush_top=True,
    )
    _room_wall(
        mb,
        "y",
        x1 - ht,
        y0,
        y1,
        z_floor,
        z_ceil,
        WALL_T,
        "e",
        tex_ext,
        tex_in,
        doors=doors_e,
        windows=wins_e,
        win_tex=win_tex,
        force_world=("e" in vis_walls),
        flush_bot=True,
        flush_top=True,
    )
    _room_wall(
        mb,
        "x",
        y0 + ht,
        x0 + WALL_T,
        x1 - WALL_T,
        z_floor,
        z_ceil,
        WALL_T,
        "s",
        tex_ext,
        tex_in,
        doors=doors_s,
        windows=wins_s,
        win_tex=win_tex,
        force_world=("s" in vis_walls),
        flush_bot=True,
        flush_top=True,
        skip_start=True,
        skip_end=True,
    )
    _room_wall(
        mb,
        "x",
        y1 - ht,
        x0 + WALL_T,
        x1 - WALL_T,
        z_floor,
        z_ceil,
        WALL_T,
        "n",
        tex_ext,
        tex_in,
        doors=doors_n,
        windows=wins_n,
        win_tex=win_tex,
        force_world=("n" in vis_walls),
        flush_bot=True,
        flush_top=True,
        skip_start=True,
        skip_end=True,
    )

    mb.register_room_ft(room_name, z_floor, z_ceil)
    mb.interior_lights_ft(
        x0 + 1.5,
        y0 + 1.5,
        x1 - 1.5,
        y1 - 1.5,
        z_ceil - light_drop_ft,
        nx=nx,
        ny=ny,
        light=light,
        color=light_color,
        wait=0.75,
    )
    mb.spot_ft(
        room_name,
        0.5 * (x0 + x1),
        0.5 * (y0 + y1),
        z_floor + 5.2,
        yaw=spot_yaw,
        kind="interior",
        desc=spot_desc or room_name,
    )
    return z_roof


def _fence_run(
    mb: MapBuilder,
    axis: str,
    pos_ft: float,
    segs: Sequence[Tuple[float, float]],
    z0: float = GROUND_TOP,
    z1: float = 6.5,
    tex: str = "{gwc_chain",
    post_tex: str = "gwc_steel",
    post_step: float = 24.0,
    solid_clip: bool = True,
    skip_top: bool = False,
) -> None:
    """Build non-gate fence spans in group='fence' with skip-culled bases/ends and optional clip."""
    post_faces: dict[str, str] = {"b": "skip"}
    for a0, a1 in segs:
        if a1 - a0 < 0.5:
            continue
        if axis == "x":
            span_faces: dict[str, str] = {"b": "skip", "w": "skip", "e": "skip"}
            if skip_top:
                span_faces["t"] = "skip"
            mb.box_ft(
                a0,
                pos_ft - 0.08,
                z0,
                a1,
                pos_ft + 0.08,
                z1,
                Tile(tex, w_ft=6.0),
                faces=span_faces,
                group="fence",
            )
            if solid_clip:
                mb.clip_box_ft(a0, pos_ft - 0.12, z0, a1, pos_ft + 0.12, z1)
            x = a0
            while x <= a1 + 0.01:
                mb.detail_box_ft(
                    x - 0.12,
                    pos_ft - 0.12,
                    z0,
                    x + 0.12,
                    pos_ft + 0.12,
                    z1 + 0.15,
                    post_tex,
                    faces=post_faces,
                )
                x += post_step
        else:
            span_faces = {"b": "skip", "n": "skip", "s": "skip"}
            if skip_top:
                span_faces["t"] = "skip"
            mb.box_ft(
                pos_ft - 0.08,
                a0,
                z0,
                pos_ft + 0.08,
                a1,
                z1,
                Tile(tex, w_ft=6.0),
                faces=span_faces,
                group="fence",
            )
            if solid_clip:
                mb.clip_box_ft(pos_ft - 0.12, a0, z0, pos_ft + 0.12, a1, z1)
            y = a0
            while y <= a1 + 0.01:
                mb.detail_box_ft(
                    pos_ft - 0.12,
                    y - 0.12,
                    z0,
                    pos_ft + 0.12,
                    y + 0.12,
                    z1 + 0.15,
                    post_tex,
                    faces=post_faces,
                )
                y += post_step


def _tree_cutout(
    mb: MapBuilder,
    cx: float,
    cy: float,
    z0: float = GROUND_TOP,
    h: float = 22.0,
    w: float = 16.0,
    tex: str = "{gwc_tree2",
    trunk_h: float = 6.0,
) -> None:
    """Emit a low-brush 2-plane alpha cutout tree with skip-culled edges and slim bark trunk."""
    hw = 0.5 * w
    mb.detail_box_ft(cx - 0.45, cy - 0.45, z0, cx + 0.45, cy + 0.45, z0 + trunk_h, "gwc_bark", faces={"b": "skip"})
    mb.box_ft(cx - hw, cy - 0.06, z0, cx + hw, cy + 0.06, z0 + h, Fit(tex), faces={"t": "skip", "b": "skip", "w": "skip", "e": "skip"}, group="fence")
    mb.box_ft(cx - 0.06, cy - hw, z0, cx + 0.06, cy + hw, z0 + h, Fit(tex), faces={"t": "skip", "b": "skip", "n": "skip", "s": "skip"}, group="fence")


def _double_pole_sign(
    mb: MapBuilder,
    cx: float,
    cy: float,
    axis: str,
    width: float,
    height: float,
    z_bot: float,
    tex: str,
    pole_tex: str = "gwc_steel",
    frame_tex: str = "gwc_dark",
    z0: float = GROUND_TOP,
    glow_light: float = 0.0,
) -> None:
    """Build a double-pole roadside motel marquee sign with 2:1 front/back decals."""
    thick = 0.85
    hw = 0.5 * width
    ht = 0.5 * thick
    z_top = z_bot + height
    pole_off = 0.30 * width
    if axis == "y":
        # Faces West (toward Union Ave) and East
        for dy in (-pole_off, pole_off):
            mb.cyl_ft(cx, cy + dy, 0.28, z0, z_bot + 0.3, sides=8, tex_side=pole_tex, tex_top="skip")
        mb.detail_box_ft(cx - ht, cy - hw, z_bot, cx + ht, cy + hw, z_top, frame_tex)
        mb.sign_decal_ft("w", cx - ht, cy - hw + 0.2, cy + hw - 0.2, z_bot + 0.2, z_top - 0.2, tex)
        mb.sign_decal_ft("e", cx + ht, cy - hw + 0.2, cy + hw - 0.2, z_bot + 0.2, z_top - 0.2, tex)
        if glow_light > 0:
            mb.light_ft(cx - 2.2, cy, 0.5 * (z_bot + z_top), light=glow_light, color=(255, 224, 152))
    else:
        # Faces North and South (along Belle Terrace / Adams St)
        for dx in (-pole_off, pole_off):
            mb.cyl_ft(cx + dx, cy, 0.28, z0, z_bot + 0.3, sides=8, tex_side=pole_tex, tex_top="skip")
        mb.detail_box_ft(cx - hw, cy - ht, z_bot, cx + hw, cy + ht, z_top, frame_tex)
        mb.sign_decal_ft("s", cy - ht, cx - hw + 0.2, cx + hw - 0.2, z_bot + 0.2, z_top - 0.2, tex)
        mb.sign_decal_ft("n", cy + ht, cx - hw + 0.2, cx + hw - 0.2, z_bot + 0.2, z_top - 0.2, tex)
        if glow_light > 0:
            mb.light_ft(cx, cy - 2.2, 0.5 * (z_bot + z_top), light=glow_light, color=(255, 224, 152))


def _tile_fit_z(tex: str, w_ft: float, z0: float, z1: float, x_align: float = 0.0) -> Tile:
    """Tile a wall texture vertically matched from z0 to z1 with crisp floor/top alignment."""
    h_ft = max(0.25, z1 - z0)
    return Tile(
        tex,
        w_ft=w_ft,
        h_ft=h_ft,
        u_ofs=(x_align / w_ft) % 1.0 if w_ft > 0.0 else 0.0,
        v_ofs=(z1 / h_ft) % 1.0,
    )


def _motel_bed(
    mb: MapBuilder,
    cx: float,
    cy: float,
    z0: float = FLOOR_TOP,
    orient: str = "y",
    head: str = "",
    nightstand_side: int = 1,
) -> None:
    """Authenticated quilted gwc_bed motel bed, walnut headboard, and nightstand+lamp."""
    if not head:
        head = "e" if orient == "x" else "n"
    if head in ("n", "s"):
        bx0, bx1 = cx - 2.6, cx + 2.6
        by0, by1 = cy - 3.3, cy + 3.3
        top_spec: Tile | Fit = Fit("gwc_bed", flip_v=(head == "s"))
        mb.detail_box_ft(bx0, by0, z0, bx1, by1, z0 + 1.85, "gwc_wood", faces={"t": top_spec, "b": "skip", head: "skip"})
        hy0, hy1 = (by1 - 0.10, by1 + 0.30) if head == "n" else (by0 - 0.30, by0 + 0.10)
        mb.detail_box_ft(bx0 - 0.1, hy0, z0, bx1 + 0.1, hy1, z0 + 3.6, "gwc_wood", faces={"b": "skip", head: "skip"})
        nx = cx + nightstand_side * 3.8
        ny0, ny1 = (by1 - 1.8, by1) if head == "n" else (by0, by0 + 1.8)
        mb.detail_box_ft(nx - 0.9, ny0, z0, nx + 0.9, ny1, z0 + 2.1, "gwc_wood", faces={"t": "gwc_granite", "b": "skip", head: "skip"})
        ny = 0.5 * (ny0 + ny1)
        mb.detail_box_ft(nx - 0.25, ny - 0.25, z0 + 2.1, nx + 0.25, ny + 0.25, z0 + 2.75, "gwc_goldurn", faces={"t": "skip", "b": "skip"})
        mb.detail_box_ft(nx - 0.55, ny - 0.55, z0 + 2.75, nx + 0.55, ny + 0.55, z0 + 3.45, "gwc_white")
    else:
        bx0, bx1 = cx - 3.3, cx + 3.3
        by0, by1 = cy - 2.6, cy + 2.6
        if head == "e":
            top_spec = Tile("gwc_bed", w_ft=5.2, h_ft=6.6, rot_deg=90.0, u_ofs=(by1 / 5.2) % 1.0, v_ofs=(bx1 / 6.6) % 1.0)
            hx0, hx1 = bx1 - 0.10, bx1 + 0.30
            nx0, nx1 = bx1 - 1.8, bx1
        else:
            top_spec = Tile("gwc_bed", w_ft=5.2, h_ft=6.6, rot_deg=270.0, u_ofs=-(by0 / 5.2) % 1.0, v_ofs=-(bx0 / 6.6) % 1.0)
            hx0, hx1 = bx0 - 0.30, bx0 + 0.10
            nx0, nx1 = bx0, bx0 + 1.8
        mb.detail_box_ft(bx0, by0, z0, bx1, by1, z0 + 1.85, "gwc_wood", faces={"t": top_spec, "b": "skip", head: "skip"})
        mb.detail_box_ft(hx0, by0 - 0.1, z0, hx1, by1 + 0.1, z0 + 3.6, "gwc_wood", faces={"b": "skip", head: "skip"})
        if nightstand_side != 0:
            ny = cy + nightstand_side * 3.8
            mb.detail_box_ft(nx0, ny - 0.9, z0, nx1, ny + 0.9, z0 + 2.1, "gwc_wood", faces={"t": "gwc_granite", "b": "skip", head: "skip"})
            nx = 0.5 * (nx0 + nx1)
            mb.detail_box_ft(nx - 0.25, ny - 0.25, z0 + 2.1, nx + 0.25, ny + 0.25, z0 + 2.75, "gwc_goldurn", faces={"t": "skip", "b": "skip"})
            mb.detail_box_ft(nx - 0.55, ny - 0.55, z0 + 2.75, nx + 0.55, ny + 0.55, z0 + 3.45, "gwc_white")


def _desk_and_tv(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z0: float = FLOOR_TOP,
    is_office: bool = False,
) -> None:
    """Compact motel/office desk + sleek matte dark monitor/TV directly seated on desk (skip bottom)."""
    mb.detail_box_ft(x0, y0, z0, x1, y1, z0 + 2.55, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mx = 0.5 * (x0 + x1)
    my = 0.5 * (y0 + y1)
    mw = 0.95 if is_office else 1.25
    if (x1 - x0) >= (y1 - y0):
        # Desk spans East-West; monitor faces N/S
        mb.detail_box_ft(mx - mw, my - 0.18, z0 + 2.55, mx + mw, my + 0.18, z0 + 4.10, "gwc_dark", faces={"s": "gwc_carwin", "n": "gwc_carwin", "b": "skip"})
    else:
        # Desk spans North-South; monitor faces E/W
        mb.detail_box_ft(mx - 0.18, my - mw, z0 + 2.55, mx + 0.18, my + mw, z0 + 4.10, "gwc_dark", faces={"w": "gwc_carwin", "e": "gwc_carwin", "b": "skip"})


def _parked_car(
    mb: MapBuilder,
    cx: float,
    cy: float,
    z0: float = GROUND_TOP,
    axis: str = "x",
    body_tex: str = "gwc_carwht",
) -> None:
    """Low-brush parked sedan silhouette (chassis + cabin with skip-culled seam)."""
    if axis == "x":
        mb.detail_box_ft(cx - 7.0, cy - 2.8, z0 + 0.5, cx + 7.0, cy + 2.8, z0 + 2.7, body_tex, faces={"b": "skip"})
        mb.detail_box_ft(cx - 3.2, cy - 2.4, z0 + 2.7, cx + 2.4, cy + 2.4, z0 + 4.4, "gwc_carwin", faces={"t": body_tex, "b": "skip"})
    else:
        mb.detail_box_ft(cx - 2.8, cy - 7.0, z0 + 0.5, cx + 2.8, cy + 7.0, z0 + 2.7, body_tex, faces={"b": "skip"})
        mb.detail_box_ft(cx - 2.4, cy - 3.2, z0 + 2.7, cx + 2.4, cy + 2.4, z0 + 4.4, "gwc_carwin", faces={"t": body_tex, "b": "skip"})


def _sealed_motel_facade_bay(
    mb: MapBuilder,
    face: str,
    wall_pos: float,
    center: float,
    z0: float = FLOOR_TOP,
) -> None:
    """Paint flush painted door + blinded window on sealed wing bays."""
    if face in ("s", "n"):
        mb.sign_decal_ft(face, wall_pos, center - 4.2, center - 1.2, z0 + 0.1, z0 + 7.2, "gwc_wooddoor", thick_ft=0.10)
        mb.sign_decal_ft(face, wall_pos, center + 0.5, center + 4.5, z0 + 3.0, z0 + 6.8, "gwc_blind", thick_ft=0.10)
    else:
        mb.sign_decal_ft(face, wall_pos, center - 4.2, center - 1.2, z0 + 0.1, z0 + 7.2, "gwc_wooddoor", thick_ft=0.10)
        mb.sign_decal_ft(face, wall_pos, center + 0.5, center + 4.5, z0 + 3.0, z0 + 6.8, "gwc_blind", thick_ft=0.10)


def _pickup_truck(
    mb: MapBuilder,
    cx: float,
    cy: float,
    z0: float = GROUND_TOP,
    axis: str = "y",
    body_tex: str = "gwc_carred",
) -> None:
    """Low-brush 3-piece pickup truck silhouette with open bed."""
    if axis == "x":
        mb.detail_box_ft(cx - 7.4, cy - 2.9, z0 + 0.5, cx + 7.4, cy + 2.9, z0 + 2.8, body_tex, faces={"b": "skip"})
        mb.detail_box_ft(cx - 1.6, cy - 2.5, z0 + 2.8, cx + 3.0, cy + 2.5, z0 + 4.9, "gwc_carwin", faces={"t": body_tex, "b": "skip"})
        mb.detail_box_ft(cx - 7.0, cy - 2.4, z0 + 2.8, cx - 2.0, cy + 2.4, z0 + 3.05, "gwc_dark", faces={"b": "skip"})
    else:
        mb.detail_box_ft(cx - 2.9, cy - 7.4, z0 + 0.5, cx + 2.9, cy + 7.4, z0 + 2.8, body_tex, faces={"b": "skip"})
        mb.detail_box_ft(cx - 2.5, cy - 1.6, z0 + 2.8, cx + 2.5, cy + 3.0, z0 + 4.9, "gwc_carwin", faces={"t": body_tex, "b": "skip"})
        mb.detail_box_ft(cx - 2.4, cy - 7.0, z0 + 2.8, cx + 2.4, cy - 2.0, z0 + 3.05, "gwc_dark", faces={"b": "skip"})


def _sealed_cottage(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    wall_tex: str,
    roof_tex: str = "gwc_resshing",
    ridge_axis: str = "x",
    face_side: str = "e",
    wall_h: float = 9.8,
    peak_h: float = 2.8,
    boarded: bool = False,
) -> None:
    """Emit a sealed residential cottage mass with gable roof and door/window facade decals."""
    mb.structural_box_ft(x0, y0, 0.0, x1, y1, wall_h, Tile(wall_tex, w_ft=8.0))
    _gable_roof(mb, x0, y0, x1, y1, wall_h, peak_h, ridge_axis=ridge_axis, tex_roof=roof_tex, tex_gable=wall_tex)
    wall_pos = {"w": x0, "e": x1, "s": y0, "n": y1}[face_side]
    center = 0.5 * (y0 + y1) if face_side in ("w", "e") else 0.5 * (x0 + x1)
    if boarded:
        mb.sign_decal_ft(face_side, wall_pos, center - 4.5, center - 1.3, GROUND_TOP + 0.1, GROUND_TOP + 6.8, "gwc_dark", thick_ft=0.10)
        mb.sign_decal_ft(face_side, wall_pos, center + 0.6, center + 4.6, GROUND_TOP + 2.8, GROUND_TOP + 6.5, "gwc_dark", thick_ft=0.10)
    else:
        _sealed_motel_facade_bay(mb, face_side, wall_pos, center, z0=GROUND_TOP)


# =============================================================================
# 1. CENTURY GLASS & AUTO DETAIL YARD (y = 582..750)
# =============================================================================

def _build_century_glass(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["srm_century_glass"]
    x1 = min(x1, EAST_X_MAX)
    y1 = min(y1, HY1 - 0.5)

    # Paved work court + east gravel storage pad
    _ground_pad(mb, x0, y0, 460.0, y1, Tile("gwc_asph", w_ft=12.0))
    _ground_pad(mb, 460.0, y0, x1, y1, Tile("gwc_dirt", w_ft=12.0))

    # Chain-link fenced corner lot with wide walkable gate openings on Union & Belle Terrace
    _fence_run(mb, "y", 285.5, [(584.5, 628.0), (648.0, 706.0)], z1=6.8)
    _fence_run(mb, "x", 584.5, [(285.5, 330.0), (350.0, 462.0)], z1=6.8)
    _fence_run(mb, "y", 532.0, [(584.5, 746.0)], z1=6.8)

    # Century Glass white CMU south frontage + enterable front shop bay (strictly y <= 748)
    sx0, sy0, sx1, sy1 = 304.0, 706.0, 404.0, 748.0
    z_roof = _build_room_shell(
        mb,
        "century_glass_shop",
        sx0,
        sy0,
        sx1,
        sy1,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=Tile("gwc_cinder", w_ft=6.0),
        tex_in=_tile_fit_z("gwc_drywall", 8.0, FLOOR_TOP, FLOOR_TOP + CEIL_CLR_H),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x4", w_ft=4.0),
        doors_s=[(320.0, 328.0, 9.0, "century_glass_entry")],
        wins_s=[(334.0, 356.0, 2.8, 8.6)],
        win_tex="gwc_glass",
        light=300.0,
        light_color=(240, 246, 255),
        nx=2,
        ny=1,
        spot_yaw=90.0,
        spot_desc="Century Glass Showroom",
    )
    # Raised black parapet + WINDOWS & DOORS fascia + twin royal-blue door accent + roll-up service bay
    mb.detail_box_ft(sx0, sy0, z_roof, sx1, sy1, 16.0, "gwc_dark", faces={"t": "gwc_tpo", "b": "skip"})
    mb.sign_decal_ft("s", sy0, 320.0, 340.0, 10.9, 15.9, "gwc_windoor")
    # Twin royal-blue entry door accent adjacent to open doorway + ajar interior door leaf
    mb.sign_decal_ft("s", sy0, 311.5, 316.0, FLOOR_TOP, 8.8, "gwc_royaldoor", thick_ft=0.10)
    mb.detail_box_ft(320.0, sy0 + 0.8, FLOOR_TOP, 320.35, sy0 + 4.3, 8.8, Fit("gwc_royaldoor"), faces={"b": "skip"})
    # Roll-up bay panel on east frontage
    mb.sign_decal_ft("s", sy0, 368.0, 392.0, FLOOR_TOP, 9.2, "gwc_rollup", thick_ft=0.12)
    # Showroom service counter, POS terminal & showroom window displays facing spot_26 (354, 727, yaw=90)
    mb.detail_box_ft(336.0, 737.5, FLOOR_TOP, 372.0, 740.5, 3.5, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mb.detail_box_ft(344.0, 738.3, 3.5, 346.4, 739.5, 4.7, "gwc_dark", faces={"s": "gwc_carwin", "n": "gwc_carwin", "b": "skip"})
    mb.detail_box_ft(358.0, 738.0, 3.5, 365.0, 739.6, 4.5, "gwc_galv", faces={"s": Fit("gwc_glass"), "n": Fit("gwc_glass"), "b": "skip"})
    mb.sign_decal_ft("s", 747.4, 342.0, 366.0, 5.2, 8.8, "gwc_windoor", thick_ft=0.12)
    for dx0 in (326.0, 372.0):
        mb.flush_panel_ft(dx0, 747.2, 3.6, dx0 + 10.0, 747.4, 8.4, {"s": Fit("gwc_glass")})
    # West & East interior glass-sheet A-frame racks + front glazing worktable
    for rx in (312.0, 384.0):
        mb.detail_box_ft(rx, 724.0, FLOOR_TOP, rx + 8.0, 742.0, 1.0, "gwc_steel", faces={"b": "skip"})
        mb.detail_box_ft(rx + 2.5, 725.0, 1.0, rx + 5.5, 741.0, 7.2, "gwc_galv", faces={"w": Fit("gwc_glass"), "e": Fit("gwc_glass"), "b": "skip"})
    mb.detail_box_ft(378.0, 712.0, FLOOR_TOP, 394.0, 720.0, 2.9, "gwc_steel", faces={"t": "gwc_glass", "b": "skip"})
    for tx in (334.0, 374.0):
        mb.detail_box_ft(tx - 2.0, 726.0, 10.24, tx + 2.0, 728.0, 10.32, Fit("gwc_troffer"), faces={"t": "skip"})

    # Shed BLDG 60058447 (OSM: x=465.9..506.6, y=589.4..662.8; sealed cleanly from z=0.0)
    mb.structural_box_ft(466.0, 590.0, 0.0, 506.0, 662.0, 10.5, Tile("gwc_corrug", w_ft=6.0))
    mb.sign_decal_ft("w", 466.0, 608.0, 622.0, GROUND_TOP, 8.8, "gwc_rollup", thick_ft=0.12)
    _gable_roof(mb, 466.0, 590.0, 506.0, 662.0, 10.5, 3.2, ridge_axis="y", tex_roof="gwc_galv", tex_gable="gwc_corrug", tex_fascia="gwc_steel")

    # Stacked framed glass A-frame racks in yard
    for rx in (412.0, 428.0):
        mb.detail_box_ft(rx, 672.0, GROUND_TOP, rx + 7.5, 676.0, 1.0, "gwc_steel", faces={"b": "skip"})
        mb.detail_box_ft(rx + 0.5, 673.2, 1.0, rx + 7.0, 674.8, 6.2, "gwc_glass", faces={"t": "gwc_galv", "w": "gwc_galv", "e": "gwc_galv", "b": "skip"})

    # Portable toilet (blue)
    mb.detail_box_ft(438.0, 596.0, GROUND_TOP, 442.2, 600.2, 7.6, "gwc_carblu", faces={"t": "gwc_white", "w": "gwc_white", "b": "skip"})

    # Blue tarp Auto Detail / Car Wash canopy + sedan + roadside flags
    cx0, cy0, cx1, cy1 = 352.0, 640.0, 386.0, 664.0
    for px in (cx0 + 0.5, cx1 - 0.5):
        for py in (cy0 + 0.5, cy1 - 0.5):
            mb.detail_box_ft(px - 0.2, py - 0.2, GROUND_TOP, px + 0.2, py + 0.2, 9.0, "gwc_steel", faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(cx0 - 0.5, cy0 - 0.5, 9.0, cx1 + 0.5, cy1 + 0.5, 9.45, "gwc_carblu")
    # Crisp CAR WASH / AUTO DETAIL tricolor canopy valence banner facing Union Ave
    mb.detail_box_ft(cx0 - 0.55, cy0, 7.8, cx0 - 0.25, cy1, 9.0, "gwc_white", faces={"s": "gwc_red", "n": "gwc_carblu"})
    _parked_car(mb, 369.0, 652.0, z0=GROUND_TOP, axis="x", body_tex="gwc_carwht")

    # Tall AUTO DETAIL roadside feather flags near Union corner
    for idx, (fy, ftex) in enumerate(((596.0, "gwc_red"), (610.0, "gwc_carblu"), (668.0, "gwc_goldurn"))):
        mb.detail_box_ft(291.0, fy - 0.12, GROUND_TOP, 291.24, fy + 0.12, 12.2, "gwc_steel", faces={"b": "skip"})
        mb.detail_box_ft(291.24, fy - 0.08, 4.2, 293.6, fy + 0.08, 12.0, ftex, faces={"w": "skip"})

    _tree_cutout(mb, 570.0, 680.0, h=20.0, w=15.0, tex="{gwc_tree2")
    mb.spot_ft("century_glass_yard", 342.0, 634.0, 5.5, yaw=45.0, kind="exterior", desc="Century Glass & Auto Detail Yard")


# =============================================================================
# 2. SE BELLE TERRACE DEMOLISHED EL DON BROWNFIELD (y = 424..532)
# =============================================================================

def _build_el_don_brownfield(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["el_don_brownfield"]
    x1 = min(x1, EAST_X_MAX)

    # Strictly open vacant grass/dirt corner lot — NO buildings
    _ground_pad(mb, x0, y0, x1, y1, Tile("gwc_drygrs", w_ft=14.0))
    _ground_pad(mb, 296.0, 444.0, 446.0, 502.0, Tile("gwc_dirt", w_ft=12.0), z0=GROUND_TOP, z1=ACCENT_TOP)

    # Chain-link fence along Union & Belle Terrace with wide walkable openings
    _fence_run(mb, "y", 285.5, [(426.0, 458.0), (482.0, 528.0)], z1=6.2)
    _fence_run(mb, "x", 529.5, [(286.0, 336.0), (362.0, 480.0)], z1=6.2)

    # 2 Freestanding yellow-and-black El Don MOTEL double-pole signs
    _double_pole_sign(mb, 291.0, 518.0, "y", width=11.0, height=5.5, z_bot=9.5, tex="gwc_eldon", pole_tex="gwc_dark")
    _double_pole_sign(mb, 396.0, 523.0, "x", width=11.0, height=5.5, z_bot=9.5, tex="gwc_eldon", pole_tex="gwc_dark")

    # Warm corner bounce & audit spot
    mb.light_ft(298.0, 510.0, 14.0, light=170.0, color=(255, 228, 178))
    mb.spot_ft("el_don_brownfield", 352.0, 476.0, 5.5, yaw=30.0, kind="exterior", desc="El Don Demolished Lot")


# =============================================================================
# 3. REDWOOD SENIOR LIVING (y = 326..424)
# =============================================================================

def _build_redwood_senior(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["redwood_senior"]
    x1 = min(x1, EAST_X_MAX)

    _ground_pad(mb, x0, y0, 412.0, y1, Tile("gwc_lawn", w_ft=12.0))
    _ground_pad(mb, 412.0, y0, x1, y1, Tile("gwc_drygrs", w_ft=14.0))
    _ground_pad(mb, x0, 364.0, 428.0, 386.0, Tile("gwc_asph", w_ft=10.0), z0=GROUND_TOP, z1=ACCENT_TOP)

    # Low beige masonry wall + wrought-iron fence with open 22 ft driveway (y=364..386)
    for ya, yb in ((328.0, 364.0), (386.0, 422.0)):
        mb.detail_box_ft(285.2, ya, GROUND_TOP, 286.6, yb, 2.8, Tile("gwc_bstucco", w_ft=6.0), faces={"b": "skip"})
        _fence_run(mb, "y", 285.9, [(ya, yb)], z0=2.8, z1=6.2, tex="{gwc_ironfence", post_tex="gwc_dark", post_step=16.0)

    # Redwood Senior Living monument sign near south drive pier
    mb.detail_box_ft(291.5, 349.0, GROUND_TOP, 293.0, 357.5, 5.2, Tile("gwc_bstucco", w_ft=4.0), faces={"b": "skip"})
    mb.sign_decal_ft("w", 291.5, 349.4, 357.1, 1.1, 4.9, "gwc_redwood")

    # Front courtyard Valley Oak shade trees
    for tx, ty in ((328.0, 342.0), (336.0, 408.0), (380.0, 344.0)):
        _tree_cutout(mb, tx, ty, h=22.0, w=16.0, tex="{gwc_tree2")

    # Main 1-storey cream/tan gable complex (BLDG 60060817: x=410..563, y=334..421)
    # Enterable front reception/lobby room (x=438..474, y=358..392)
    z_roof = _build_room_shell(
        mb,
        "redwood_lobby",
        438.0,
        358.0,
        474.0,
        392.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=Tile("gwc_crmstuc", w_ft=8.0),
        tex_in=Tile("gwc_wainscot", w_ft=8.0),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_w=[(371.0, 379.0, 9.0, "redwood_lobby_entry")],
        wins_w=[(361.0, 368.0, 3.0, 7.6), (382.0, 389.0, 3.0, 7.6)],
        win_tex="gwc_glass",
        light=320.0,
        nx=2,
        ny=1,
        spot_yaw=0.0,
        spot_desc="Redwood Senior Living Reception",
    )
    # Front portico columns + gable canopy
    mb.detail_box_ft(428.0, 365.0, 0.0, 438.0, 385.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    for py in (366.0, 384.0):
        mb.detail_box_ft(429.0, py - 0.3, FLOOR_TOP, 429.6, py + 0.3, z_roof - 0.4, "gwc_white", faces={"b": "skip", "t": "skip"})
    _gable_roof(mb, 428.5, 364.0, 439.0, 386.0, z_roof - 0.3, 2.8, ridge_axis="x", eave=0.5, tex_roof="gwc_resshing", tex_gable="gwc_crmstuc")

    # Sealed North, South & Rear residential wings forming authentic H/U footprint
    mb.structural_box_ft(410.5, 334.0, 0.0, 562.5, 358.0, z_roof, Tile("gwc_crmstuc", w_ft=8.0))
    mb.structural_box_ft(410.5, 392.0, 0.0, 562.5, 421.0, z_roof, Tile("gwc_crmstuc", w_ft=8.0))
    mb.structural_box_ft(474.0, 358.0, 0.0, 562.5, 392.0, z_roof, Tile("gwc_crmstuc", w_ft=8.0))
    for wy in (342.0, 402.0):
        mb.sign_decal_ft("w", 410.5, wy, wy + 8.0, 3.2, 7.2, "gwc_blind", thick_ft=0.10)
    _gable_roof(mb, 410.5, 334.0, 562.5, 358.0, z_roof, 3.5, ridge_axis="x")
    _gable_roof(mb, 410.5, 392.0, 562.5, 421.0, z_roof, 3.5, ridge_axis="x")
    _gable_roof(mb, 438.0, 358.0, 562.5, 392.0, z_roof, 3.8, ridge_axis="x")

    # Lobby reception counter, POS monitor, framed Redwood plaque, credenzas & waiting seating
    _desk_and_tv(mb, 461.5, 366.0, 465.5, 384.0, is_office=True)
    mb.detail_box_ft(462.7, 368.0, 2.87, 463.7, 369.0, 4.15, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    mb.detail_box_ft(473.05, 368.0, 4.6, 473.32, 382.0, 8.2, "gwc_wood", faces={"w": Fit("gwc_redwood"), "e": "skip"})
    for cy0, cy1 in ((359.2, 366.2), (383.8, 390.8)):
        mb.detail_box_ft(471.2, cy0, FLOOR_TOP, 473.3, cy1, 6.2, "gwc_wood", faces={"t": "gwc_granite", "b": "skip", "e": "skip"})
        mb.detail_box_ft(471.6, cy0 + 2.2, 6.2, 472.9, cy1 - 2.2, 7.4, "gwc_dark", faces={"t": "gwc_drygrs", "b": "skip"})
    mb.detail_box_ft(447.0, 359.0, FLOOR_TOP, 456.0, 363.2, 2.4, "gwc_leather", faces={"b": "skip"})
    mb.detail_box_ft(448.0, 364.5, FLOOR_TOP, 455.0, 367.5, 1.65, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mb.detail_box_ft(447.0, 386.8, FLOOR_TOP, 456.0, 391.0, 2.4, "gwc_leather", faces={"b": "skip"})


# =============================================================================
# 4. STAR-LITER MOTOR MOTEL (x = 283..505, y = 26..326) — HIGH PRIORITY
# =============================================================================

def _build_star_liter_motel(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["star_liter_motel"]  # 283, 26, 505, 326

    # Site paving: rear lot north of motel, concrete walk along Union, central asphalt court
    _ground_pad(mb, 296.0, y0, x1, 217.0, Tile("gwc_asph", w_ft=12.0))
    _ground_pad(mb, x0, 217.0, x1, y1, Tile("gwc_drygrs", w_ft=14.0))
    _ground_pad(mb, x0, 217.0, 410.0, 294.5, Tile("gwc_asph", w_ft=12.0), z0=GROUND_TOP, z1=ACCENT_TOP)

    # Missing OSM Residence BLDG 60020129 (x=288.2..338.0, y=295.8..321.5, strictly < 326 south of Redwood)
    mb.detail_box_ft(284.8, 305.0, 0.0, 288.2, 312.5, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.structural_box_ft(288.2, 295.8, 0.0, 338.0, 321.5, 9.8, Tile("gwc_wstucco", w_ft=8.0))
    _gable_roof(mb, 288.2, 295.8, 338.0, 321.5, 9.8, 3.0, ridge_axis="x", eave=0.8, tex_roof="gwc_resshing", tex_gable="gwc_wstucco")
    mb.sign_decal_ft("w", 288.2, 307.0, 310.2, FLOOR_TOP, 7.3, "gwc_wooddoor", thick_ft=0.10)
    for wy0, wy1 in ((299.0, 304.5), (313.0, 318.5)):
        mb.sign_decal_ft("w", 288.2, wy0, wy1, 3.0, 7.0, "gwc_blind", thick_ft=0.10)
    for wx0, wx1 in ((296.0, 302.0), (322.0, 328.0)):
        mb.sign_decal_ft("s", 295.8, wx0, wx1, 3.0, 7.0, "gwc_blind", thick_ft=0.10)
    mb.detail_box_ft(x0, y0, 0.0, 296.0, 217.0, 0.30, "gwc_conc", faces={"b": "skip"})

    # Low white CMU front wall along Union leaving wide courtyard driveway open (y=90..178)
    for ya, yb in ((27.0, 88.0), (180.0, 217.0)):
        mb.detail_box_ft(285.2, ya, 0.30, 286.8, yb, 3.0, Tile("gwc_wstucco", w_ft=6.0), faces={"t": "gwc_white", "b": "skip"})

    # Iconic Star-Liter MOTEL (VACANCY / REFRIG) double-pole sign at Union driveway edge
    _double_pole_sign(mb, 291.0, 188.0, "y", width=12.0, height=6.0, z_bot=13.5, tex="gwc_starlt", z0=0.30, glow_light=180.0)

    # Interior concrete walkway apron wrapping U-shaped courtyard
    mb.detail_box_ft(346.0, 75.0, 0.0, 463.0, 81.5, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(456.5, 81.5, 0.0, 463.0, 179.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(313.0, 172.5, 0.0, 456.5, 179.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(296.0, 89.0, GROUND_TOP, 346.0, 96.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})

    ext_red = Tile("gwc_redsid", w_ft=8.0)

    # 1) Enterable Front Office (x=298..346, y=33..89)
    z_roof = _build_room_shell(
        mb,
        "starliter_office",
        298.0,
        33.0,
        346.0,
        89.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=ext_red,
        tex_in=Tile("gwc_wainscot", w_ft=8.0),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_n=[(316.0, 323.0, 9.0, "starliter_office_entry")],
        wins_w=[(46.0, 72.0, 2.8, 8.2)],
        wins_n=[(304.0, 313.0, 2.8, 8.2), (326.0, 338.0, 2.8, 8.2)],
        win_tex="gwc_glass",
        light=205.0,
        nx=2,
        ny=2,
        spot_yaw=270.0,
        spot_desc="Star-Liter Front Office",
    )
    _desk_and_tv(mb, 304.0, 45.0, 326.0, 48.5, is_office=True)
    mb.detail_box_ft(323.0, 38.0, FLOOR_TOP, 326.0, 45.0, 2.85, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mb.detail_box_ft(323.9, 40.5, 2.85, 324.9, 41.5, 4.15, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    mb.detail_box_ft(305.5, 33.65, 4.6, 313.5, 33.92, 8.6, "gwc_wood", faces={"n": Fit("gwc_starlt"), "s": "skip"})
    mb.detail_box_ft(315.5, 33.65, 4.6, 323.5, 33.92, 8.6, "gwc_wood", faces={"n": Fit("gwc_keyrack"), "s": "skip"})
    mb.detail_box_ft(332.0, 39.0, FLOOR_TOP, 340.5, 45.0, 2.4, "gwc_leather", faces={"b": "skip"})
    mb.detail_box_ft(333.5, 47.5, FLOOR_TOP, 339.0, 51.5, 1.65, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    _gable_roof(mb, 298.0, 33.0, 346.0, 89.0, z_roof, 3.4, ridge_axis="y", tex_gable="gwc_redsid")

    # 2) South Wing: Corner seal (346..366) + Guest Room 1 (366..406) + Guest Room 2 (406..446) + East corner seal (446..463)
    mb.structural_box_ft(346.0, 45.0, 0.0, 366.0, 75.0, z_roof, ext_red)
    mb.structural_box_ft(446.0, 45.0, 0.0, 463.0, 75.0, z_roof, ext_red)
    rm_wall = _tile_fit_z("gwc_drywall", 8.0, FLOOR_TOP, FLOOR_TOP + CEIL_CLR_H)
    rm_cpt = Tile("gwc_motelcpt", w_ft=6.0)
    for idx, (rx0, rx1) in enumerate(((366.0, 406.0), (406.0, 446.0)), start=1):
        cx = 0.5 * (rx0 + rx1)
        _build_room_shell(
            mb,
            f"starliter_room_{idx}",
            rx0,
            45.0,
            rx1,
            75.0,
            z_floor=FLOOR_TOP,
            ceil_h=CEIL_CLR_H,
            tex_ext=ext_red,
            tex_in=rm_wall,
            tex_floor=rm_cpt,
            tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
            doors_n=[(cx - 3.5, cx + 3.0, 8.9, f"starliter_rm{idx}_door")],
            wins_n=[(cx + 5.0, cx + 11.5, 3.0, 7.4)],
            win_tex="gwc_blind",
            light=270.0,
            nx=1,
            ny=1,
            spot_yaw=270.0,
            spot_desc=f"Star-Liter Room {idx}",
            vis_walls=("s",),
        )
        _motel_bed(mb, cx - 6.0, 49.3, head="s", nightstand_side=-1)
        _desk_and_tv(mb, cx + 5.0, 46.2, cx + 13.0, 49.0)
        mb.detail_box_ft(cx + 6.5, 45.6, 4.6, cx + 11.5, 45.8, 7.8, "gwc_wood", faces={"n": "gwc_glass", "s": "skip"})
    _gable_roof(mb, 346.0, 45.0, 463.0, 75.0, z_roof, 3.0, ridge_axis="x", tex_gable="gwc_redsid")

    # 3) East Wing: Sealed ends + Guest Room 3 (x=463..493, y=98..154)
    mb.structural_box_ft(463.0, 45.0, 0.0, 493.0, 98.0, z_roof, ext_red)
    mb.structural_box_ft(463.0, 154.0, 0.0, 493.0, 211.0, z_roof, ext_red)
    _build_room_shell(
        mb,
        "starliter_room_3",
        463.0,
        98.0,
        493.0,
        154.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=ext_red,
        tex_in=rm_wall,
        tex_floor=rm_cpt,
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_w=[(122.0, 128.5, 8.9, "starliter_rm3_door")],
        wins_w=[(106.0, 113.0, 3.0, 7.4), (136.0, 143.0, 3.0, 7.4)],
        win_tex="gwc_blind",
        light=280.0,
        nx=1,
        ny=2,
        spot_yaw=0.0,
        spot_desc="Star-Liter Suite 3",
        vis_walls=("e",),
    )
    _motel_bed(mb, 488.8, 112.0, head="e", nightstand_side=0)
    _motel_bed(mb, 488.8, 140.0, head="e", nightstand_side=0)
    mb.detail_box_ft(489.8, 124.5, FLOOR_TOP, 492.0, 127.5, FLOOR_TOP + 2.1, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mb.detail_box_ft(490.5, 125.7, FLOOR_TOP + 2.1, 491.3, 126.3, FLOOR_TOP + 3.3, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    _desk_and_tv(mb, 464.5, 102.0, 467.5, 111.0)
    mb.detail_box_ft(465.5, 142.0, FLOOR_TOP, 470.5, 148.0, 2.4, "gwc_leather", faces={"b": "skip"})
    _gable_roof(mb, 463.0, 45.0, 493.0, 211.0, z_roof, 3.0, ridge_axis="y", tex_gable="gwc_redsid")

    # 4) North Wing: Guest Room 4 (x=372..418, y=179..211) + sealed bays (313..372, 418..463)
    mb.structural_box_ft(313.0, 179.0, 0.0, 372.0, 211.0, z_roof, ext_red)
    mb.structural_box_ft(418.0, 179.0, 0.0, 463.0, 211.0, z_roof, ext_red)
    _build_room_shell(
        mb,
        "starliter_room_4",
        372.0,
        179.0,
        418.0,
        211.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=ext_red,
        tex_in=rm_wall,
        tex_floor=rm_cpt,
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_s=[(391.0, 397.5, 8.9, "starliter_rm4_door")],
        wins_s=[(378.0, 385.0, 3.0, 7.4), (402.0, 410.0, 3.0, 7.4)],
        win_tex="gwc_blind",
        light=270.0,
        nx=1,
        ny=1,
        spot_yaw=90.0,
        spot_desc="Star-Liter Room 4",
        vis_walls=("n",),
    )
    _motel_bed(mb, 386.0, 206.8, head="n", nightstand_side=-1)
    _desk_and_tv(mb, 402.0, 207.2, 410.0, 210.0)
    mb.detail_box_ft(403.5, 210.10, 4.6, 408.5, 210.32, 7.8, "gwc_wood", faces={"s": "gwc_glass", "n": "skip"})
    _gable_roof(mb, 313.0, 179.0, 463.0, 211.0, z_roof, 3.0, ridge_axis="x", tex_gable="gwc_redsid")

    # Courtyard veranda fascia beams, support posts, sealed room facades & warm courtyard lights
    for px in (354.0, 380.0, 414.0, 448.0):
        mb.detail_box_ft(px, 75.5, FLOOR_TOP, px + 0.35, 75.85, z_roof - 0.5, "gwc_white", faces={"b": "skip", "t": "skip"})
        mb.detail_box_ft(px, 177.2, FLOOR_TOP, px + 0.35, 177.55, z_roof - 0.5, "gwc_white", faces={"b": "skip", "t": "skip"})
    for rx in (330.0, 355.0, 436.0):
        _sealed_motel_facade_bay(mb, "s", 179.0, rx)
    _sealed_motel_facade_bay(mb, "n", 75.0, 355.0)
    _sealed_motel_facade_bay(mb, "w", 463.0, 180.0)
    # Courtyard planter island + parked cars clear of walk paths, pickups & spot_35 (390, 126)
    mb.detail_box_ft(416.0, 99.0, GROUND_TOP, 428.0, 107.0, 1.5, "gwc_conc", faces={"t": Tile("gwc_drygrs", w_ft=6.0), "b": "skip"})
    _tree_cutout(mb, 422.0, 103.0, h=14.0, w=9.0, tex="{gwc_palmfr")
    _parked_car(mb, 408.0, 86.0, axis="x", body_tex="gwc_carblu")
    _parked_car(mb, 438.0, 166.0, axis="x", body_tex="gwc_carwht")
    mb.light_ft(388.0, 126.0, 11.0, light=260.0, color=(255, 220, 172))
    mb.light_ft(446.0, 126.0, 10.0, light=240.0, color=(255, 220, 172))
    mb.spot_ft("starliter_courtyard", 390.0, 126.0, 5.5, yaw=0.0, kind="exterior", desc="Star-Liter Motel Courtyard")


# =============================================================================
# 5. 922 S UNION MOBILE HOME / RV PARK (y=-268..26 & x=505..649.5, y=26..326)
# =============================================================================

def _trailer_unit(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    wall_tex: str = "gwc_wstucco",
    roof_tex: str = "gwc_galv",
    height: float = 9.5,
    door_side: str = "n",
    skip_roof_top: bool = False,
) -> None:
    """Low-brush mobile home / RV exterior detail box with skip-culled base/top & 1-face decals."""
    mb.detail_box_ft(x0, y0, GROUND_TOP, x1, y1, GROUND_TOP + height, Tile(wall_tex, w_ft=8.0), faces={"b": "skip", "t": "skip"})
    roof_faces: dict[str, str] = {"b": "skip"}
    if skip_roof_top:
        roof_faces["t"] = "skip"
    mb.detail_box_ft(x0 - 0.3, y0 - 0.3, GROUND_TOP + height, x1 + 0.3, y1 + 0.3, GROUND_TOP + height + 0.55, Tile(roof_tex, w_ft=6.0), faces=roof_faces)
    z_d0, z_d1 = GROUND_TOP + 0.25, min(GROUND_TOP + 7.2, GROUND_TOP + height - 0.8)
    z_w0, z_w1 = GROUND_TOP + 3.4, min(GROUND_TOP + 6.9, GROUND_TOP + height - 1.0)
    if door_side in ("n", "s"):
        py0, py1 = (y1, y1 + 0.09) if door_side == "n" else (y0 - 0.09, y0)
        mb.flush_panel_ft(x0 + 6.0, py0, z_d0, x0 + 9.4, py1, z_d1, {door_side: Fit("gwc_wooddoor")})
        mb.flush_panel_ft(x0 + 13.5, py0, z_w0, x0 + 20.5, py1, z_w1, {door_side: Fit("gwc_blind")})
        mb.flush_panel_ft(x1 - 13.5, py0, z_w0, x1 - 6.5, py1, z_w1, {door_side: Fit("gwc_blind")})
    else:
        px0, px1 = (x0 - 0.09, x0) if door_side == "w" else (x1, x1 + 0.09)
        mb.flush_panel_ft(px0, y0 + 4.5, z_d0, px1, y0 + 7.9, z_d1, {door_side: Fit("gwc_wooddoor")})
        mb.flush_panel_ft(px0, y0 + 10.5, z_w0, px1, y0 + 16.5, z_w1, {door_side: Fit("gwc_blind")})
        mb.flush_panel_ft(px0, y1 - 9.0, z_w0, px1, y1 - 3.0, z_w1, {door_side: Fit("gwc_blind")})


def _build_rv_park_922(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["rv_park_922"]          # 283, -268, 650, 26
    nx0, ny0, nx1, ny1 = PARCELS["rv_park_922_north"]  # 505, 26, 650, 326
    x1 = min(x1, EAST_X_MAX)
    nx1 = min(nx1, EAST_X_MAX)

    # Dry valley grass base + playable open asphalt driveways between trailer rows
    _ground_pad(mb, x0, y0, x1, y1, Tile("gwc_drygrs", w_ft=14.0))
    _ground_pad(mb, nx0, ny0, nx1, ny1, Tile("gwc_drygrs", w_ft=14.0))
    for ly0, ly1 in ((-206.0, -176.0), (-132.0, -104.0), (-36.0, -12.0)):
        _ground_pad(mb, x0, ly0, 646.0, ly1, Tile("gwc_asph", w_ft=12.0), z0=GROUND_TOP, z1=ACCENT_TOP)
    _ground_pad(mb, 508.0, -12.0, 544.0, 290.0, Tile("gwc_asph", w_ft=12.0), z0=GROUND_TOP, z1=ACCENT_TOP)

    # Chain-link frontage along Union keeping all 3 main park driveways wide open
    _fence_run(mb, "y", 285.5, [(-266.0, -208.0), (-174.0, -134.0), (-102.0, -38.0), (-10.0, 24.0)], z1=6.0)

    # Enterable Front Office / Unit BLDG 60014841 (OSM x=356.7..403.4, widened cleanly 17 ft N-S y=2..20)
    z_off = _build_room_shell(
        mb,
        "rv_park_922_office",
        356.0,
        2.0,
        404.0,
        20.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=Tile("gwc_crmstuc", w_ft=8.0),
        tex_in=_tile_fit_z("gwc_drywall", 8.0, FLOOR_TOP, FLOOR_TOP + CEIL_CLR_H),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_s=[(376.0, 383.0, 9.0, "rv_922_office_entry")],
        wins_w=[(6.0, 14.0, 3.0, 7.6)],
        wins_s=[(362.0, 370.0, 3.0, 7.6), (388.0, 397.0, 3.0, 7.6)],
        win_tex="gwc_blind",
        light=280.0,
        nx=2,
        ny=1,
        spot_yaw=180.0,
        spot_desc="922 S Union RV Park Office",
    )
    # West-end check-in counter, key rack & waiting seating cleanly visible from spot_36 (yaw=180)
    _desk_and_tv(mb, 362.0, 6.5, 365.5, 16.0, is_office=True)
    mb.detail_box_ft(363.2, 13.8, 2.87, 364.2, 14.8, 4.15, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    mb.detail_box_ft(361.0, 19.05, 4.6, 368.0, 19.32, 8.1, "gwc_wood", faces={"s": Fit("gwc_keyrack"), "n": "skip"})
    mb.detail_box_ft(357.2, 16.5, FLOOR_TOP, 360.4, 19.3, 6.2, "gwc_wood", faces={"t": "gwc_granite", "b": "skip", "n": "skip"})
    mb.detail_box_ft(387.0, 15.5, FLOOR_TOP, 396.0, 19.3, 2.4, "gwc_leather", faces={"b": "skip", "n": "skip"})
    mb.detail_box_ft(388.5, 11.5, FLOOR_TOP, 394.5, 14.0, 1.65, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    _gable_roof(mb, 356.0, 2.0, 404.0, 20.0, z_off, 2.5, ridge_axis="x")

    # Front Union house BLDG 60015919 (x=318..365, y=-158..-112) & corner shed 60019458 (321..388, -247..-212)
    _trailer_unit(mb, 318.0, -158.0, 365.0, -112.0, wall_tex="gwc_bstucco", roof_tex="gwc_resshing", height=10.0, door_side="n", skip_roof_top=True)
    _gable_roof(mb, 318.0, -158.0, 365.0, -112.0, 10.15, 2.8, ridge_axis="x", tex_gable="gwc_bstucco")
    _trailer_unit(mb, 321.0, -247.0, 388.0, -212.0, wall_tex="gwc_crmstuc", roof_tex="gwc_resshing", height=9.5, door_side="n")

    # Single & Double-Wide Mobile Homes / RVs with generous playable lanes (strictly <= 646)
    trailers = (
        # North-main row (y=-2..22 east of office, facing south drive)
        (454.0, -2.0, 504.0, 22.0, "gwc_wstucco", "s"),
        (556.0, -2.0, 622.0, 22.0, "gwc_corrug", "s"),
        # Row A (y=-96..-64, facing north courtyard lane)
        (372.0, -96.0, 434.0, -64.0, "gwc_bstucco", "n"),
        (458.0, -96.0, 520.0, -64.0, "gwc_wstucco", "n"),
        (554.0, -96.0, 642.0, -64.0, "gwc_slatstuc", "n"),
        # Row B (y=-168..-138, facing north lane)
        (414.0, -168.0, 478.0, -138.0, "gwc_wstucco", "n"),
        (502.0, -168.0, 566.0, -138.0, "gwc_crmstuc", "n"),
        (588.0, -168.0, 645.0, -138.0, "gwc_corrug", "n"),
        # Row C (y=-248..-214, facing north lane)
        (410.0, -248.0, 474.0, -214.0, "gwc_bstucco", "n"),
        (498.0, -248.0, 562.0, -214.0, "gwc_wstucco", "n"),
        (584.0, -248.0, 645.0, -214.0, "gwc_crmstuc", "n"),
        # North Bay east of Star-Liter (x=556..636, facing west lane x=508..544)
        (556.0, 36.0, 636.0, 64.0, "gwc_wstucco", "w"),
        (556.0, 96.0, 636.0, 126.0, "gwc_corrug", "w"),
        (556.0, 158.0, 636.0, 188.0, "gwc_bstucco", "w"),
        (556.0, 248.0, 636.0, 278.0, "gwc_wstucco", "w"),
    )
    for tx0, ty0, tx1, ty1, wtex, dside in trailers:
        _trailer_unit(mb, tx0, ty0, tx1, ty1, wall_tex=wtex, roof_tex="gwc_tpo", height=9.2, door_side=dside)

    # Mature elm/ash shade trees across park lanes & front lawns
    for tx, ty, ttex in (
        (308.0, 6.0, "{gwc_tree2"),
        (312.0, -62.0, "{gwc_tree2"),
        (422.0, -4.0, "{gwc_tree3"),
        (478.0, -118.0, "{gwc_tree2"),
        (338.0, -190.0, "{gwc_tree2"),
        (536.0, 138.0, "{gwc_tree2"),
        (526.0, 224.0, "{gwc_tree3"),
    ):
        _tree_cutout(mb, tx, ty, h=22.0, w=15.0, tex=ttex)

    mb.spot_ft("rv_park_922", 342.0, -24.0, 5.5, yaw=0.0, kind="exterior", desc="922 S Union Mobile Home Park Lane")


# =============================================================================
# 6. SUNLAND MOTEL (y = -366..-268) — MEDIUM-HIGH PRIORITY
# =============================================================================

def _build_sunland_motel(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["sunland_motel"]  # 283, -366, 650, -268
    x1 = min(x1, EAST_X_MAX)

    _ground_pad(mb, x0, y0, x1, y1, Tile("gwc_asph", w_ft=12.0))
    _ground_pad(mb, x0, -276.0, x1, y1, Tile("gwc_drygrs", w_ft=12.0), z0=GROUND_TOP, z1=ACCENT_TOP)
    mb.detail_box_ft(311.0, -322.0, 0.0, 560.0, -315.5, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})

    # Decorative white diamond breeze-block screen walls with wide courtyard & S Union driveway gaps
    for sx0, sx1 in ((322.0, 354.0), (392.0, 434.0)):
        _fence_run(mb, "x", -362.0, [(sx0, sx1)], z0=GROUND_TOP, z1=6.6, tex="{gwc_breezeblk", post_tex="gwc_wstucco", post_step=16.0, skip_top=True)
        mb.detail_box_ft(sx0, -362.35, 6.6, sx1, -361.65, 7.0, "gwc_wstucco")
    _fence_run(mb, "y", 288.0, [(-362.0, -342.0), (-314.0, -272.0)], z0=GROUND_TOP, z1=6.6, tex="{gwc_breezeblk", post_tex="gwc_wstucco", post_step=14.0, skip_top=True)
    for uy0, uy1 in ((-362.0, -342.0), (-314.0, -272.0)):
        mb.detail_box_ft(287.65, uy0, 6.6, 288.35, uy1, 7.0, "gwc_wstucco")

    # Retro Sunland MOTEL teal/gold marquee sign near Union frontage
    _double_pole_sign(mb, 293.0, -330.0, "y", width=12.0, height=6.0, z_bot=10.5, tex="gwc_sunlnd", glow_light=180.0)

    # Painted light-blue wooden sidewalk bus bench on Union curb edge
    mb.detail_box_ft(284.2, -347.0, GROUND_TOP, 285.8, -340.0, 1.85, "gwc_carblu", faces={"w": "gwc_steel", "e": "gwc_steel", "b": "skip"})
    mb.detail_box_ft(285.4, -347.0, 1.85, 285.9, -340.0, 3.3, "gwc_carblu", faces={"b": "skip"})

    # Long cream-stucco motel strip (BLDG 60014900: x=311..559, y=-315.5..-275.5)
    # Enterable Check-In Lobby + 2 Enterable Guest Rooms
    crm = Tile("gwc_crmstuc", w_ft=8.0)
    z_roof = _build_room_shell(
        mb,
        "sunland_lobby",
        311.0,
        -315.5,
        355.0,
        -275.5,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=crm,
        tex_in=Tile("gwc_wainscot", w_ft=8.0),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_s=[(329.0, 336.5, 9.0, "sunland_lobby_entry")],
        wins_w=[(-305.0, -288.0, 2.8, 8.2)],
        wins_s=[(316.0, 325.0, 2.8, 8.2), (340.0, 349.0, 2.8, 8.2)],
        win_tex="gwc_glass",
        light=320.0,
        nx=2,
        ny=1,
        spot_yaw=90.0,
        spot_desc="Sunland Motel Lobby",
    )
    _desk_and_tv(mb, 316.0, -284.5, 336.0, -281.0, is_office=True)
    mb.detail_box_ft(333.5, -283.8, 2.87, 334.5, -282.8, 4.15, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    mb.detail_box_ft(316.0, -276.42, 4.6, 324.0, -276.15, 8.6, "gwc_wood", faces={"s": Fit("gwc_sunlnd"), "n": "skip"})
    mb.detail_box_ft(326.0, -276.42, 4.6, 334.0, -276.15, 8.6, "gwc_wood", faces={"s": Fit("gwc_keyrack"), "n": "skip"})
    mb.detail_box_ft(342.0, -287.0, FLOOR_TOP, 350.0, -280.0, 2.4, "gwc_leather", faces={"b": "skip"})
    mb.detail_box_ft(343.0, -293.0, FLOOR_TOP, 349.0, -290.0, 1.65, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})

    # Sealed connecting bays & enterable Guest Rooms 1 & 2
    mb.structural_box_ft(355.0, -315.5, 0.0, 382.0, -275.5, z_roof, crm)
    mb.structural_box_ft(426.0, -315.5, 0.0, 456.0, -275.5, z_roof, crm)
    mb.structural_box_ft(500.0, -315.5, 0.0, 559.0, -275.5, z_roof, crm)

    sun_wall = _tile_fit_z("gwc_drywall", 8.0, FLOOR_TOP, FLOOR_TOP + CEIL_CLR_H)
    sun_cpt = Tile("gwc_motelcpt", w_ft=6.0)
    for idx, (rx0, rx1) in enumerate(((382.0, 426.0), (456.0, 500.0)), start=1):
        cx = 0.5 * (rx0 + rx1)
        _build_room_shell(
            mb,
            f"sunland_room_{idx}",
            rx0,
            -315.5,
            rx1,
            -275.5,
            z_floor=FLOOR_TOP,
            ceil_h=CEIL_CLR_H,
            tex_ext=crm,
            tex_in=sun_wall,
            tex_floor=sun_cpt,
            tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
            doors_s=[(cx - 3.2, cx + 3.2, 8.9, f"sunland_rm{idx}_door")],
            wins_s=[(cx + 5.5, cx + 13.0, 3.0, 7.4)],
            win_tex="gwc_blind",
            light=310.0,
            nx=1,
            ny=1,
            spot_yaw=90.0,
            spot_desc=f"Sunland Guest Room {idx}",
        )
        _motel_bed(mb, cx - 6.0, -279.8, head="n", nightstand_side=-1)
        _desk_and_tv(mb, cx + 5.0, -279.2, cx + 12.8, -276.4)
        mb.detail_box_ft(cx + 6.5, -276.42, 4.6, cx + 11.5, -276.15, 7.8, "gwc_wood", faces={"s": "gwc_glass", "n": "skip"})

    for bx in (368.0, 441.0, 514.0, 542.0):
        _sealed_motel_facade_bay(mb, "s", -315.5, bx)

    # Teal/forest-green fascia eaves (strictly above room ceilings) & brown shingle gable roof
    _gable_roof(
        mb,
        311.0,
        -315.5,
        559.0,
        -275.5,
        z_roof,
        3.6,
        ridge_axis="x",
        eave=1.4,
        tex_roof="gwc_resshing",
        tex_gable="gwc_crmstuc",
        tex_fascia="gwc_dumpstr",
        fascia_h=0.35,
    )
    mb.light_ft(388.0, -334.0, 10.0, light=240.0, color=(255, 224, 178))
    mb.light_ft(495.0, -334.0, 10.0, light=240.0, color=(255, 224, 178))
    mb.light_ft(420.0, -316.8, 8.6, light=170.0, color=(255, 214, 155))
    mb.spot_ft("sunland_courtyard", 405.0, -336.0, 5.5, yaw=90.0, kind="exterior", desc="Sunland Motel Courtyard")


# =============================================================================
# 7. COUNTRY INN MOTEL (y = -555..-366, NE Adams St) — HIGH PRIORITY
# =============================================================================

def _build_country_inn_motel(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["country_inn_motel"]  # 283, -555, 650, -366
    x1 = min(x1, EAST_X_MAX)

    # Broad asphalt parking court along Adams St & central courtyard
    _ground_pad(mb, x0, y0, x1, y1, Tile("gwc_asph", w_ft=12.0))
    # Courtyard concrete aprons along front lobby, south/Adams wing, and north wing (stop at x=614 clear of East wing)
    mb.detail_box_ft(298.0, -552.0, 0.0, 309.0, -495.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(360.0, -518.0, 0.0, 614.0, -511.5, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(312.0, -418.5, 0.0, 614.0, -412.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})

    # Googie slanted yellow-fin "Country Inn MOTEL" tall roadside pole sign
    mb.cyl_ft(291.0, -445.0, 0.42, GROUND_TOP, 14.8, sides=8, tex_side="gwc_steel", tex_top="skip")
    mb.prism_yz_ft(
        [(-452.5, 13.8), (-437.5, 13.8), (-435.5, 21.8), (-454.5, 21.8)],
        290.5,
        291.5,
        tex_side="gwc_goldurn",
        tex_end="gwc_dark",
        group="detail",
    )
    mb.sign_decal_ft("w", 290.5, -451.0, -439.0, 14.5, 20.5, "gwc_cntry")
    mb.sign_decal_ft("e", 291.5, -451.0, -439.0, 14.5, 20.5, "gwc_cntry")
    mb.light_ft(288.5, -445.0, 17.5, light=190.0, color=(255, 224, 140))

    # Covered green/yellow walk-up booth beside Union driveway
    mb.detail_box_ft(302.0, -482.0, GROUND_TOP, 310.0, -474.0, 8.2, Tile("gwc_booth", w_ft=6.0), faces={"t": "skip", "b": "skip"})
    mb.detail_box_ft(300.5, -483.5, 8.2, 311.5, -472.5, 9.2, "gwc_dumpstr", faces={"w": "gwc_goldurn", "n": "gwc_goldurn", "t": "gwc_resshing"})

    crm = Tile("gwc_crmstuc", w_ft=8.0)
    wst = Tile("gwc_wstucco", w_ft=8.0)

    # 1) Front SW White/Cream Stucco Lobby Wing + Small White Porch (x=309..360, y=-553.5..-495)
    z_lob = _build_room_shell(
        mb,
        "countryinn_lobby",
        309.0,
        -553.5,
        360.0,
        -495.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=wst,
        tex_in=Tile("gwc_wainscot", w_ft=8.0),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_w=[(-527.0, -519.5, 9.0, "countryinn_porch_entry")],
        doors_n=[(330.0, 338.0, 9.0, "countryinn_court_entry")],
        wins_w=[(-546.0, -533.0, 2.8, 8.2), (-512.0, -501.0, 2.8, 8.2)],
        wins_s=[(316.0, 332.0, 2.8, 8.2)],
        win_tex="gwc_glass",
        light=300.0,
        nx=2,
        ny=2,
        spot_yaw=45.0,
        spot_desc="Country Inn Lobby",
    )
    # Small white porch roof & posts facing Union/Adams (stops outside x=309.0 lobby wall)
    for py in (-534.0, -512.0):
        mb.detail_box_ft(299.0, py - 0.3, FLOOR_TOP, 299.6, py + 0.3, z_lob - 0.4, "gwc_white", faces={"b": "skip", "t": "skip"})
    _gable_roof(mb, 298.5, -536.0, 309.0, -510.0, z_lob, 2.6, ridge_axis="x", eave=0.4, tex_fascia="gwc_dumpstr", fascia_h=0.35)
    _hip_roof(mb, 309.0, -553.5, 360.0, -495.0, z_lob, 3.8, eave=1.0, tex_fascia="gwc_dumpstr", fascia_h=0.35)
    # Check-in L-counter, marquee plaque, key rack & waiting seating visible from spot_42 (yaw=45)
    _desk_and_tv(mb, 351.0, -534.0, 354.5, -512.0, is_office=True)
    mb.detail_box_ft(344.0, -512.0, FLOOR_TOP, 354.5, -509.0, 2.85, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mb.detail_box_ft(352.2, -515.0, 2.87, 353.2, -514.0, 4.15, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    mb.detail_box_ft(359.05, -527.0, 4.6, 359.32, -519.0, 8.6, "gwc_wood", faces={"w": Fit("gwc_cntry"), "e": "skip"})
    mb.detail_box_ft(359.05, -516.0, 4.6, 359.32, -508.0, 8.6, "gwc_wood", faces={"w": Fit("gwc_keyrack"), "e": "skip"})
    mb.detail_box_ft(343.0, -499.8, FLOOR_TOP, 353.0, -496.2, 2.4, "gwc_leather", faces={"b": "skip", "n": "skip"})
    mb.detail_box_ft(354.0, -500.0, FLOOR_TOP, 358.2, -496.2, 2.1, "gwc_wood", faces={"t": "gwc_granite", "b": "skip", "n": "skip"})
    mb.detail_box_ft(355.7, -498.5, 2.1, 356.5, -497.7, 3.3, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    mb.detail_box_ft(314.0, -548.0, FLOOR_TOP, 323.0, -542.0, 2.4, "gwc_leather", faces={"b": "skip"})

    # 2) Long East Guest Room Wing Extending 300+ ft East along Adams St (x=360..646, y=-553.5..-518)
    # 3 Enterable courtyard rooms + sealed connecting bays
    mb.structural_box_ft(360.0, -553.5, 0.0, 378.0, -518.0, z_lob, crm)
    mb.structural_box_ft(424.0, -553.5, 0.0, 458.0, -518.0, z_lob, crm)
    mb.structural_box_ft(504.0, -553.5, 0.0, 538.0, -518.0, z_lob, crm)
    mb.structural_box_ft(584.0, -553.5, 0.0, 646.0, -518.0, z_lob, crm)

    ci_wall = _tile_fit_z("gwc_drywall", 8.0, FLOOR_TOP, FLOOR_TOP + CEIL_CLR_H)
    ci_cpt = Tile("gwc_motelcpt", w_ft=6.0)
    for idx, (rx0, rx1) in enumerate(((378.0, 424.0), (458.0, 504.0), (538.0, 584.0)), start=1):
        cx = 0.5 * (rx0 + rx1)
        _build_room_shell(
            mb,
            f"countryinn_room_{idx}",
            rx0,
            -553.5,
            rx1,
            -518.0,
            z_floor=FLOOR_TOP,
            ceil_h=CEIL_CLR_H,
            tex_ext=crm,
            tex_in=ci_wall,
            tex_floor=ci_cpt,
            tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
            doors_n=[(cx - 3.2, cx + 3.2, 8.9, f"countryinn_rm{idx}_door")],
            wins_n=[(cx + 5.5, cx + 13.0, 3.0, 7.4)],
            win_tex="gwc_blind",
            light=270.0,
            nx=1,
            ny=1,
            spot_yaw=270.0,
            spot_desc=f"Country Inn Room {idx}",
        )
        _motel_bed(mb, cx - 6.0, -549.3, head="s", nightstand_side=-1)
        _desk_and_tv(mb, cx + 5.0, -552.5, cx + 13.0, -549.5)
        mb.detail_box_ft(cx + 6.5, -552.82, 4.6, cx + 11.5, -552.55, 7.8, "gwc_wood", faces={"n": "gwc_glass", "s": "skip"})

    for bx in (441.0, 521.0, 602.0, 630.0):
        _sealed_motel_facade_bay(mb, "n", -518.0, bx)
    _gable_roof(mb, 360.0, -553.5, 646.0, -518.0, z_lob, 3.4, ridge_axis="x", eave=1.0, tex_fascia="gwc_dumpstr", fascia_h=0.35)

    # 3) North Wing + East Closure Wing wrapping Courtyard (strictly <= 646) + Enterable Room 4
    mb.structural_box_ft(312.0, -412.0, 0.0, 438.0, -375.0, z_lob, crm)
    mb.structural_box_ft(484.0, -412.0, 0.0, 646.0, -375.0, z_lob, crm)
    mb.structural_box_ft(614.0, -518.0, 0.0, 646.0, -412.0, z_lob, crm)

    _build_room_shell(
        mb,
        "countryinn_room_4",
        438.0,
        -412.0,
        484.0,
        -375.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=crm,
        tex_in=ci_wall,
        tex_floor=ci_cpt,
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_s=[(458.0, 464.5, 8.9, "countryinn_rm4_door")],
        wins_s=[(444.0, 452.0, 3.0, 7.4)],
        win_tex="gwc_blind",
        light=270.0,
        nx=1,
        ny=1,
        spot_yaw=90.0,
        spot_desc="Country Inn North Room 4",
    )
    _motel_bed(mb, 454.0, -379.2, head="n", nightstand_side=-1)
    _desk_and_tv(mb, 468.0, -378.8, 476.0, -375.8)
    mb.detail_box_ft(469.5, -375.95, 4.6, 474.5, -375.68, 7.8, "gwc_wood", faces={"s": "gwc_glass", "n": "skip"})
    for bx in (330.0, 366.0, 404.0, 512.0, 550.0, 588.0):
        _sealed_motel_facade_bay(mb, "s", -412.0, bx)
    _gable_roof(mb, 312.0, -412.0, 646.0, -375.0, z_lob, 3.4, ridge_axis="x", eave=1.1, tex_fascia="gwc_dumpstr", fascia_h=0.35)
    _gable_roof(mb, 614.0, -518.0, 646.0, -412.0, z_lob, 3.0, ridge_axis="y", eave=0.9, tex_fascia="gwc_dumpstr", fascia_h=0.35)

    _tree_cutout(mb, 304.0, -428.0, h=22.0, w=14.0, tex="{gwc_tree1")
    # Courtyard planter island, parked cars & wall sconces clear of doors, pickup (395,-465) & spot_47 (445,-468)
    mb.detail_box_ft(482.0, -468.0, GROUND_TOP, 502.0, -458.0, 1.5, "gwc_conc", faces={"t": Tile("gwc_drygrs", w_ft=6.0), "b": "skip"})
    _tree_cutout(mb, 492.0, -463.0, h=16.0, w=10.0, tex="{gwc_palmfr")
    _parked_car(mb, 441.0, -504.0, axis="x", body_tex="gwc_carblu")
    _parked_car(mb, 521.0, -504.0, axis="x", body_tex="gwc_carwht")
    _parked_car(mb, 540.0, -426.0, axis="x", body_tex="gwc_carred")
    mb.light_ft(505.0, -516.8, 8.6, light=180.0, color=(255, 214, 155))
    mb.light_ft(505.0, -413.2, 8.6, light=180.0, color=(255, 214, 155))
    mb.light_ft(420.0, -470.0, 11.0, light=260.0, color=(255, 224, 178))
    mb.light_ft(550.0, -470.0, 11.0, light=260.0, color=(255, 224, 178))
    mb.spot_ft("countryinn_courtyard", 445.0, -468.0, 5.5, yaw=0.0, kind="exterior", desc="Country Inn Parking Court")


# =============================================================================
# 8. PLAYFAIR MARKET (y = -670..-595, SE Adams St) — HIGH PRIORITY
# =============================================================================

def _build_playfair_market(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["playfair_market"]  # 283, -820, 650, -595 (market owns -670..-595)
    x1 = min(x1, EAST_X_MAX)

    # Market concrete perimeter aprons carved cleanly outside Playfair interior tile floor (295..353, -663..-606)
    mb.detail_box_ft(x0, -606.0, 0.0, 356.0, -595.5, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(x0, -670.0, 0.0, 356.0, -663.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(x0, -663.0, 0.0, 295.0, -606.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    mb.detail_box_ft(353.0, -663.0, 0.0, 356.0, -606.0, FLOOR_TOP, "gwc_conc", faces={"b": "skip"})
    _ground_pad(mb, 356.0, -670.0, x1, -595.5, Tile("gwc_asph", w_ft=12.0))

    # Blue steel curb bollards protecting NW corner sidewalk (kept >= 6 ft from walls/entry)
    for bx, by in ((287.0, -634.0), (287.0, -622.0), (287.0, -610.0), (287.0, -599.5), (300.0, -598.5), (336.0, -598.5)):
        mb.cyl_ft(bx, by, 0.25, FLOOR_TOP, 3.6, sides=8, tex_side="gwc_carblu", tex_top="gwc_carblu")

    # Full Enterable Square Market (BLDG 60020226: x=295..353, y=-663..-606, 15 ft tall)
    z_roof = _build_room_shell(
        mb,
        "playfair_market_int",
        295.0,
        -663.0,
        353.0,
        -606.0,
        z_floor=FLOOR_TOP,
        ceil_h=10.5,  # 126u clear >= 112u
        tex_ext=Tile("gwc_wstucco", w_ft=8.0),
        tex_in=Tile("gwc_wainscot", w_ft=8.0),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x4", w_ft=4.0),
        doors_n=[(316.0, 325.0, 9.3, "playfair_front_entry")],  # 9x9 ft clear entry
        wins_n=[(301.0, 313.0, 2.2, 8.8), (328.0, 346.0, 2.2, 8.8)],
        win_tex="gwc_glass",
        light=195.0,
        light_color=(248, 250, 255),
        nx=2,
        ny=2,
        spot_yaw=270.0,
        spot_desc="Playfair Market Interior",
        vis_walls=("w", "s", "e"),
        light_drop_ft=1.5,
    )
    # 15 ft Parapet Shell + Stepped West Blue Parapet + North Play Fair Fascia + Mural
    mb.detail_box_ft(295.0, -663.0, z_roof, 353.0, -606.0, 15.0, "gwc_wstucco", faces={"t": "gwc_tpo", "b": "skip"})
    mb.detail_box_ft(304.0, -606.5, 10.6, 344.0, -605.7, 17.6, "gwc_red", faces={"b": "skip"})
    mb.sign_decal_ft("n", -605.7, 305.5, 342.5, 10.8, 17.4, "gwc_playfr", thick_ft=0.16)
    mb.light_ft(324.0, -601.5, 15.0, light=140.0, color=(255, 240, 220))

    # West Facade: Bakersfield Union Ave mural (2:1) + Stepped Blue Parapet MARKET sign (4:1)
    mb.detail_box_ft(294.5, -652.0, 11.2, 295.3, -616.0, 18.2, "gwc_carblu", faces={"b": "skip"})
    mb.sign_decal_ft("w", 294.5, -650.0, -618.0, 11.5, 17.9, "gwc_pfmarket", thick_ft=0.16)
    mb.sign_decal_ft("w", 295.0, -648.0, -620.0, 1.4, 11.0, "gwc_pfmural", thick_ft=0.16)
    mb.light_ft(290.5, -634.0, 13.0, light=145.0, color=(255, 232, 198))

    # Full Playfair Market Interior: check-out counter w/ POS, stocked grocery gondolas (>= 10 ft aisles), glowing coolers
    mb.detail_box_ft(301.0, -622.0, FLOOR_TOP, 314.0, -618.5, 3.6, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mb.detail_box_ft(305.0, -621.0, 3.6, 307.2, -619.8, 4.8, "gwc_dark", faces={"s": "gwc_carwin", "n": "gwc_carwin", "b": "skip"})
    shelf_tex = _tile_fit_z("gwc_grocery", 6.5, FLOOR_TOP, 6.20)
    for gx0 in (304.0, 317.0, 332.0):  # 3 ft wide gondolas with 10..12 ft clear aisles (>> 48u)!
        mb.detail_box_ft(
            gx0, -652.0, FLOOR_TOP, gx0 + 3.0, -626.0, 6.20,
            "gwc_white",
            faces={"w": shelf_tex, "e": shelf_tex, "s": shelf_tex, "n": shelf_tex, "t": "gwc_steel", "b": "skip"},
        )
    mb.detail_box_ft(349.0, -652.0, FLOOR_TOP, 352.2, -622.0, 6.20, "gwc_steel", faces={"w": shelf_tex, "b": "skip", "e": "skip"})
    # Glowing backlit beverage coolers along south back wall (8 double-door bays across 50 ft)
    cooler_tex = _tile_fit_z("gwc_cooler", 6.25, FLOOR_TOP, 8.32, x_align=298.0)
    mb.detail_box_ft(298.0, -662.2, FLOOR_TOP, 348.0, -658.4, 8.32, "gwc_steel", faces={"n": cooler_tex, "b": "skip", "s": "skip"})
    mb.light_ft(312.0, -656.0, 5.5, light=130.0, color=(205, 236, 255))
    mb.light_ft(336.0, -656.0, 5.5, light=130.0, color=(205, 236, 255))
    # 4 Ceiling troffer panels
    for tx in (310.0, 338.0):
        for ty in (-648.0, -624.0):
            mb.detail_box_ft(tx - 2.0, ty - 1.0, 10.74, tx + 2.0, ty + 1.0, 10.82, Fit("gwc_troffer"), faces={"t": "skip"})

    # Behind-market taller residence BLDG 60017856 (x=395..428, y=-653..-618) + oak tree
    mb.structural_box_ft(395.0, -653.0, 0.0, 428.0, -618.0, 10.5, Tile("gwc_crmstuc", w_ft=8.0))
    _gable_roof(mb, 395.0, -653.0, 428.0, -618.0, 10.5, 4.5, ridge_axis="x", tex_roof="gwc_resshing", tex_gable="gwc_crmstuc")
    _tree_cutout(mb, 444.0, -628.0, h=20.0, w=15.0, tex="{gwc_tree2")


# =============================================================================
# 9. SOUTH STRIP (y = -820..-670)
# =============================================================================

def _build_south_strip(mb: MapBuilder) -> None:
    x0 = EAST_X_MIN
    x1 = EAST_X_MAX
    y0 = HY0 + 0.5  # -819.5

    _ground_pad(mb, x0, y0, 370.0, -670.0, Tile("gwc_asph", w_ft=12.0))
    _ground_pad(mb, 370.0, y0, x1, -670.0, Tile("gwc_drygrs", w_ft=14.0))
    _fence_run(mb, "y", 285.5, [(-818.0, -782.0), (-766.0, -720.0), (-704.0, -672.0)], z1=5.8)

    # 1) BLDG 60016928 (x=312..646, y=-713..-676)
    mb.structural_box_ft(312.0, -713.0, 0.0, 646.0, -676.0, 10.5, Tile("gwc_bstucco", w_ft=8.0))
    _gable_roof(mb, 312.0, -713.0, 646.0, -676.0, 10.5, 3.2, ridge_axis="x", tex_gable="gwc_bstucco")
    _sealed_motel_facade_bay(mb, "w", 312.0, -694.0)

    # 2) BLDG 60017599 (x=315..367, y=-771..-715) — Enterable front commercial/office room
    z_front = _build_room_shell(
        mb,
        "south_strip_60017599",
        315.0,
        -756.0,
        345.0,
        -720.0,
        z_floor=FLOOR_TOP,
        ceil_h=CEIL_CLR_H,
        tex_ext=Tile("gwc_wstucco", w_ft=8.0),
        tex_in=_tile_fit_z("gwc_drywall", 8.0, FLOOR_TOP, FLOOR_TOP + CEIL_CLR_H),
        tex_floor=Tile("gwc_tile", w_ft=4.0),
        tex_ceil=Tile("gwc_ceil2x2", w_ft=4.0),
        doors_w=[(-742.0, -735.0, 9.0, "south_60017599_entry")],
        wins_w=[(-752.0, -745.0, 3.0, 7.6), (-731.0, -724.0, 3.0, 7.6)],
        win_tex="gwc_glass",
        light=260.0,
        nx=1,
        ny=1,
        spot_yaw=0.0,
        spot_desc="60017599 Front Room",
    )
    _desk_and_tv(mb, 334.0, -744.0, 338.0, -732.0, is_office=True)
    mb.detail_box_ft(335.2, -735.0, 2.87, 336.2, -734.0, 4.15, "gwc_goldurn", faces={"t": "gwc_white", "b": "skip"})
    mb.detail_box_ft(344.05, -743.0, 4.6, 344.32, -733.0, 8.2, "gwc_wood", faces={"w": "gwc_glass", "e": "skip"})
    mb.detail_box_ft(341.8, -731.0, FLOOR_TOP, 344.2, -723.0, 5.8, "gwc_wood", faces={"t": "gwc_granite", "b": "skip", "e": "skip"})
    mb.detail_box_ft(324.0, -755.2, FLOOR_TOP, 332.0, -751.2, 2.4, "gwc_leather", faces={"b": "skip", "s": "skip"})
    mb.detail_box_ft(325.0, -749.5, FLOOR_TOP, 331.0, -746.5, 1.65, "gwc_wood", faces={"t": "gwc_granite", "b": "skip"})
    mb.detail_box_ft(324.0, -724.8, FLOOR_TOP, 332.0, -720.8, 2.4, "gwc_leather", faces={"b": "skip", "n": "skip"})
    mb.structural_box_ft(345.0, -771.0, 0.0, 367.0, -715.0, z_front, Tile("gwc_wstucco", w_ft=8.0))
    mb.structural_box_ft(315.0, -771.0, 0.0, 345.0, -756.0, z_front, Tile("gwc_wstucco", w_ft=8.0))
    _gable_roof(mb, 315.0, -771.0, 367.0, -715.0, z_front, 3.0, ridge_axis="y", tex_gable="gwc_wstucco")

    # 3) BLDG 60016099 (x=368..646, y=-773..-733) & BLDG 60017185 (x=317..482, y=-807..-778)
    mb.structural_box_ft(368.0, -773.0, 0.0, 646.0, -733.0, 10.5, Tile("gwc_crmstuc", w_ft=8.0))
    _gable_roof(mb, 368.0, -773.0, 646.0, -733.0, 10.5, 3.0, ridge_axis="x")

    mb.structural_box_ft(317.0, -807.0, 0.0, 482.0, -778.0, 10.5, Tile("gwc_bstucco", w_ft=8.0))
    _gable_roof(mb, 317.0, -807.0, 482.0, -778.0, 10.5, 3.0, ridge_axis="x", tex_gable="gwc_bstucco")
    _sealed_motel_facade_bay(mb, "w", 317.0, -792.0)
    _tree_cutout(mb, 298.0, -782.0, h=20.0, w=14.0, tex="{gwc_tree2")


# =============================================================================
# 10. DEAL TIME AUTO SALES & YARD (gc_deal_time: y = 750.25..842.0)
# =============================================================================

def _build_gc_deal_time(mb: MapBuilder) -> None:
    x0, _y0, x1, y1 = PARCELS["gc_deal_time"]
    x1 = min(x1, EAST_X_MAX)
    y0 = 750.25

    _ground_pad(mb, x0, y0, 502.0, y1, Tile("gwc_asph", w_ft=12.0))
    _ground_pad(mb, 502.0, y0, x1, y1, Tile("gwc_dirt", w_ft=14.0))
    _ground_pad(mb, 514.0, 756.0, x1 - 2.0, 836.0, Tile("gwc_drygrs", w_ft=14.0), z0=GROUND_TOP, z1=ACCENT_TOP)

    # Tall dark wrought-iron perimeter fence with open driveways off Union & E 4th
    _fence_run(mb, "y", 285.0, [(752.0, 774.0), (794.0, 839.0)], z1=6.2, tex="{gwc_ironfence", post_tex="gwc_dark")
    _fence_run(mb, "x", 840.0, [(285.0, 326.0), (348.0, 360.0), (402.0, 444.0), (466.0, 500.0)], z1=6.2, tex="{gwc_ironfence", post_tex="gwc_dark")
    _fence_run(mb, "x", 840.0, [(502.0, 560.0), (582.0, 646.0)], z1=6.0)

    # Deal Time Auto Sales office (BLDG 60056105): white stucco + bright-red corner pilasters + hipped peak
    bx0, by0, bx1, by1 = 360.0, 782.0, 402.0, 822.0
    mb.structural_box_ft(bx0, by0, 0.0, bx1, by1, 12.2, Tile("gwc_wstucco", w_ft=8.0))
    _gable_roof(mb, bx0 + 4.0, by0 + 4.0, bx1 - 4.0, by1 - 4.0, 12.2, 3.2, ridge_axis="x", tex_roof="gwc_resshing", tex_gable="gwc_wstucco", tex_fascia="gwc_dark")
    for px0, px1 in ((bx0 - 0.22, bx0 + 3.5), (bx1 - 3.5, bx1 + 0.22)):
        for py0, py1 in ((by0 - 0.22, by0 + 3.5), (by1 - 3.5, by1 + 0.22)):
            mb.detail_box_ft(px0, py0, GROUND_TOP, px1, py1, 12.3, "gwc_red", faces={"b": "skip"})

    # 3 vertical dark glass windows + entry recess facing E 4th St & Union Ave
    for wx0, wx1 in ((366.0, 372.0), (376.0, 382.0), (386.0, 392.0)):
        mb.sign_decal_ft("n", by1, wx0, wx1, 3.0, 8.2, "gwc_glass", thick_ft=0.10)
    mb.sign_decal_ft("n", by1, 393.5, 397.0, GROUND_TOP, 7.8, "gwc_wooddoor", thick_ft=0.10)
    mb.sign_decal_ft("w", bx0, 787.0, 791.0, GROUND_TOP, 7.8, "gwc_wooddoor", thick_ft=0.10)
    for wy0, wy1 in ((794.0, 801.0), (806.0, 813.0)):
        mb.sign_decal_ft("w", bx0, wy0, wy1, 3.0, 8.2, "gwc_glass", thick_ft=0.10)
    mb.sign_decal_ft("n", by1, 372.0, 388.0, 8.7, 12.7, "gwc_dealtime")
    mb.sign_decal_ft("w", bx0, 794.0, 810.0, 8.7, 12.7, "gwc_dealtime")

    # Dealership pickup trucks & sedans along E 4th & Union fences
    _pickup_truck(mb, 310.0, 828.5, axis="y", body_tex="gwc_carred")
    _pickup_truck(mb, 326.0, 828.5, axis="y", body_tex="gwc_carwht")
    _pickup_truck(mb, 344.0, 828.5, axis="y", body_tex="gwc_carsil")
    _parked_car(mb, 418.0, 828.5, axis="y", body_tex="gwc_carblu")
    _pickup_truck(mb, 434.0, 828.5, axis="y", body_tex="gwc_carwht")
    _pickup_truck(mb, 298.0, 804.0, axis="x", body_tex="gwc_carwht")
    _parked_car(mb, 298.0, 764.0, axis="x", body_tex="gwc_carsil")

    # Rear tire / industrial shed (BLDG 60052271 north bay inside gc_deal_time)
    mb.structural_box_ft(456.0, 752.0, 0.0, 496.0, 826.0, 11.0, Tile("gwc_cinder", w_ft=8.0))
    _gable_roof(mb, 456.0, 752.0, 496.0, 826.0, 11.0, 2.2, ridge_axis="y", tex_roof="gwc_galv", tex_gable="gwc_corrug", tex_fascia="gwc_steel")
    mb.sign_decal_ft("w", 456.0, 766.0, 780.0, GROUND_TOP, 8.5, "gwc_rollup", thick_ft=0.12)
    mb.sign_decal_ft("w", 456.0, 796.0, 810.0, GROUND_TOP, 8.5, "gwc_rollup", thick_ft=0.12)
    mb.detail_box_ft(451.5, 784.0, GROUND_TOP, 455.5, 792.0, 4.5, "gwc_tire", faces={"b": "skip"})

    _tree_cutout(mb, 536.0, 782.0, h=19.0, w=14.0, tex="{gwc_tree2")
    mb.spot_ft("gc_deal_time_lot", 336.0, 792.0, 5.5, yaw=40.0, kind="exterior", desc="Deal Time Auto Sales Lot")


# =============================================================================
# 11. EAST OF ALLEY WAREHOUSE, DIRT LOT & COTTAGES (gc_alley_east: y = 882..1168)
# =============================================================================

def _build_gc_alley_east(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["gc_alley_east"]
    x1 = min(x1, EAST_X_MAX)

    _ground_pad(mb, x0, y0, 566.0, y1, Tile("gwc_dirt", w_ft=14.0))
    _ground_pad(mb, 566.0, y0, 572.0, y1, Tile("gwc_conc", w_ft=6.0))
    _ground_pad(mb, 572.0, y0, 596.0, y1, Tile("gwc_asph", w_ft=12.0))
    _ground_pad(mb, 596.0, y0, 602.0, y1, Tile("gwc_conc", w_ft=6.0))
    _ground_pad(mb, 602.0, y0, x1, y1, Tile("gwc_drygrs", w_ft=14.0))

    # Corrugated metal fence on red steel top rail wrapping north vacant dirt lot
    mb.detail_box_ft(430.6, 992.0, GROUND_TOP, 431.1, 1165.5, 6.2, Tile("gwc_corrug", w_ft=6.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(430.5, 992.0, 6.2, 431.2, 1165.5, 6.55, "gwc_red", faces={"b": "skip"})
    mb.detail_box_ft(431.2, 1165.0, GROUND_TOP, 564.0, 1165.5, 6.2, Tile("gwc_corrug", w_ft=6.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(431.2, 1164.9, 6.2, 564.0, 1165.6, 6.55, "gwc_red", faces={"b": "skip"})

    # Gabled corrugated sheet-metal warehouse flush along east edge of GC alley (BLDG 60055037)
    mb.structural_box_ft(431.0, 915.0, 0.0, 465.0, 984.0, 14.0, Tile("gwc_corrug", w_ft=6.0))
    _gable_roof(mb, 431.0, 915.0, 465.0, 984.0, 14.0, 3.8, ridge_axis="y", tex_roof="gwc_galv", tex_gable="gwc_corrug", tex_fascia="gwc_steel")
    _fence_run(mb, "y", 431.5, [(884.0, 914.5)], z1=6.2)
    _fence_run(mb, "x", 884.0, [(431.5, 465.0)], z1=6.2)

    # Weathered tan E 4th corner cottage (BLDG 60057341) + 2 Wallace St cottages
    _sealed_cottage(mb, 470.0, 888.0, 499.0, 913.0, "gwc_bstucco", ridge_axis="x", face_side="s", wall_h=9.5, peak_h=2.6, boarded=True)
    _fence_run(mb, "x", 884.0, [(468.0, 504.0)], z1=5.0)
    _sealed_cottage(mb, 514.0, 896.0, 553.0, 958.0, "gwc_crmstuc", ridge_axis="y", face_side="e", wall_h=9.8, peak_h=3.0)
    _sealed_cottage(mb, 490.0, 990.0, 553.0, 1022.0, "gwc_wstucco", ridge_axis="x", face_side="e", wall_h=9.8, peak_h=2.8)

    # East-of-Wallace sealed cottages cleanly framing east corridor edge
    _sealed_cottage(mb, 612.0, 918.0, 647.5, 978.0, "gwc_crmstuc", roof_tex="gwc_shingle", ridge_axis="y", face_side="w", wall_h=10.0, peak_h=3.0)
    _sealed_cottage(mb, 612.0, 996.0, 647.5, 1046.0, "gwc_bstucco", ridge_axis="x", face_side="w", wall_h=9.8, peak_h=2.8)
    _fence_run(mb, "y", 603.0, [(890.0, 985.0), (1010.0, 1150.0)], z1=4.8)

    for tx, ty in ((482.0, 962.0), (504.0, 976.0), (540.0, 1044.0)):
        _tree_cutout(mb, tx, ty, h=20.0, w=14.0, tex="{gwc_tree2")
    mb.spot_ft("gc_alley_east_lot", 582.0, 1030.0, 5.5, yaw=200.0, kind="exterior", desc="Wallace St & Alley East Block")


# =============================================================================
# 12. REYES TIRES & SERVICE + E 6TH MASS (gc_reyes_tires: y = 1208..1339.5)
# =============================================================================

def _build_gc_reyes_tires(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["gc_reyes_tires"]
    y1 = min(y1, HY1 - 0.5)

    _ground_pad(mb, x0, y0, x1, y1, Tile("gwc_asph", w_ft=12.0))

    # Tall wrought-iron perimeter fence with wide open drive gates off E 5th & Union Ave
    _fence_run(mb, "x", 1209.5, [(285.0, 316.0), (350.0, 390.0)], z1=6.2, tex="{gwc_ironfence", post_tex="gwc_dark")
    _fence_run(mb, "y", 285.0, [(1209.5, 1244.0), (1270.0, 1336.0)], z1=6.2, tex="{gwc_ironfence", post_tex="gwc_dark")

    # 2-sided white pole sign (REYES TIRE SHOP / Y MOFLES) at SW Union & E 5th corner
    mb.cyl_ft(292.0, 1220.0, 0.35, GROUND_TOP, 10.7, sides=8, tex_side="gwc_steel", tex_top="skip")
    mb.detail_box_ft(291.6, 1217.0, 10.5, 292.4, 1223.0, 16.5, "gwc_dark")
    mb.sign_decal_ft("w", 291.6, 1217.2, 1222.8, 10.7, 16.3, "gwc_reyespole")
    mb.sign_decal_ft("e", 292.4, 1217.2, 1222.8, 10.7, 16.3, "gwc_reyespole")

    # Enterable Reyes Tires service bay (>= 112u ceiling, dual 11x9.3ft bay doors + west office door)
    z_roof = _build_room_shell(
        mb,
        "reyes_tires_bay",
        318.0,
        1236.0,
        358.0,
        1268.0,
        z_floor=FLOOR_TOP,
        ceil_h=11.0,
        # Offset 2 texels (0.015625 tile) avoids float32 rounding on integer-ft luxel edges
        # at y>1048ft in export_web_viewer.py; structural E/N walls prevent interior detail splits.
        tex_ext=Tile("gwc_rstucco", w_ft=8.0, u_ofs=0.015625, v_ofs=0.015625),
        tex_in=_tile_fit_z("gwc_drywall", 8.0, FLOOR_TOP, FLOOR_TOP + 11.0, x_align=0.125),
        tex_floor=Tile("gwc_concslab", w_ft=6.0, u_ofs=0.015625, v_ofs=0.015625),
        tex_ceil=Tile("gwc_ceil2x4", w_ft=4.0, u_ofs=0.015625, v_ofs=0.015625),
        doors_s=[(324.0, 335.0, 9.6, "reyes_bay_door_w"), (341.0, 352.0, 9.6, "reyes_bay_door_e")],
        doors_w=[(1242.0, 1250.0, 9.0, "reyes_bay_office")],
        wins_w=[(1254.0, 1263.0, 3.0, 7.6)],
        win_tex="gwc_glass",
        vis_walls=("e", "n"),
        light=175.0,
        light_color=(255, 240, 210),
        nx=2,
        ny=1,
        spot_yaw=45.0,
        spot_desc="Reyes Tires Service Bay",
        light_drop_ft=1.4,
    )
    # Sealed rear shop annex + shared parapet fascia + gwc_reyes 8:1 service beam
    mb.structural_box_ft(318.0, 1268.0, 0.0, 358.0, 1298.0, z_roof, Tile("gwc_bstucco", w_ft=8.0, u_ofs=0.015625, v_ofs=0.015625))
    mb.detail_box_ft(
        318.0,
        1236.0,
        z_roof,
        358.0,
        1298.0,
        14.5,
        Tile("gwc_wstucco", w_ft=8.0, u_ofs=0.015625, v_ofs=0.015625),
        faces={"t": Tile("gwc_tpo", w_ft=8.0, u_ofs=0.015625, v_ofs=0.015625), "b": "skip"},
    )
    mb.sign_decal_ft("s", 1236.0, 322.0, 354.0, 10.2, 14.2, "gwc_reyes")
    mb.sign_decal_ft("w", 318.0, 1244.0, 1276.0, 10.2, 14.2, "gwc_reyes")

    # Service bay interior equipment kept along rear/perimeter walls (>=32u East clearance for carlift)
    mb.detail_box_ft(319.0, 1262.0, FLOOR_TOP, 324.5, 1267.2, 5.2, "gwc_tire", faces={"b": "skip", "n": "skip", "w": "skip"})
    mb.detail_box_ft(338.0, 1263.5, FLOOR_TOP, 356.5, 1267.2, 3.4, "gwc_steel", faces={"t": "gwc_wood", "b": "skip", "n": "skip"})
    mb.detail_box_ft(353.2, 1249.5, FLOOR_TOP, 354.7, 1251.0, 9.5, "gwc_carlift", faces={"b": "skip"})
    for tx in (328.0, 348.0):
        mb.detail_box_ft(
            tx - 2.0,
            1251.0,
            11.24,
            tx + 2.0,
            1253.0,
            11.32,
            Tile("gwc_wstucco", w_ft=4.0, u_ofs=0.015625, v_ofs=0.015625),
            faces={"t": "skip", "b": Tile("gwc_troffer", w_ft=4.0, h_ft=2.0, u_ofs=0.5078125, v_ofs=0.515625)},
        )

    # Open steel corrugated carport along alley with 2 hydraulic lift silhouettes & tire stacks
    for cx in (385.0, 411.0):
        for cy in (1237.0, 1265.0, 1293.0):
            mb.detail_box_ft(cx - 0.2, cy - 0.2, GROUND_TOP, cx + 0.2, cy + 0.2, 12.2, "gwc_steel", faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(383.5, 1235.5, 12.2, 412.5, 1294.5, 12.7, "gwc_corrug", faces={"t": "gwc_galv"})
    _fence_run(mb, "y", 412.2, [(1212.0, 1298.0)], z1=6.5)
    for ly in (1252.0, 1278.0):
        mb.detail_box_ft(390.0, ly - 0.7, GROUND_TOP, 391.2, ly + 0.7, 9.5, "gwc_carlift", faces={"b": "skip"})
        mb.detail_box_ft(402.0, ly - 0.7, GROUND_TOP, 403.2, ly + 0.7, 9.5, "gwc_carlift", faces={"b": "skip"})
        mb.detail_box_ft(390.0, ly - 0.5, 9.5, 403.2, ly + 0.5, 10.0, "gwc_steel")
    mb.detail_box_ft(407.0, 1242.0, GROUND_TOP, 410.5, 1286.0, 5.2, "gwc_tire", faces={"b": "skip"})

    # E 6th 2-story rear apartment mass & north yard annex framing north skyline
    mb.structural_box_ft(304.0, 1314.0, 0.0, 374.0, y1 - 1.0, 20.5, Tile("gwc_bstucco", w_ft=8.0))
    mb.detail_box_ft(303.5, 1313.5, 20.5, 374.5, y1 - 0.5, 21.5, "gwc_dark", faces={"t": "gwc_tpo", "b": "skip"})
    mb.detail_box_ft(312.0, 1313.6, 13.8, 366.0, 1314.0, 19.2, "gwc_dark", faces={"b": "skip", "n": "skip"})
    mb.detail_box_ft(312.0, 1313.2, 11.0, 366.0, 1313.6, 13.8, Tile("gwc_bstucco", w_ft=6.0), faces={"b": "skip"})
    mb.structural_box_ft(374.0, 1316.0, 0.0, 411.0, y1 - 1.0, 11.5, Tile("gwc_bstucco", w_ft=8.0))

    mb.spot_ft("gc_reyes_tires_yard", 344.0, 1220.0, 5.5, yaw=50.0, kind="exterior", desc="Reyes Tires & Service Lot")


# =============================================================================
# 13. NORTH OF E 5TH ALLEY-EAST COTTAGES & FRINGE (gc_north_fringe: y = 1208..1339.5)
# =============================================================================

def _build_gc_north_fringe(mb: MapBuilder) -> None:
    x0, y0, x1, y1 = PARCELS["gc_north_fringe"]
    x1 = min(x1, EAST_X_MAX)
    y1 = min(y1, HY1 - 0.5)

    _ground_pad(mb, x0, y0, 566.0, y1, Tile("gwc_drygrs", w_ft=14.0))
    _ground_pad(mb, 566.0, y0, 572.0, y1, Tile("gwc_conc", w_ft=6.0))
    _ground_pad(mb, 572.0, y0, 596.0, y1, Tile("gwc_asph", w_ft=12.0))
    _ground_pad(mb, 596.0, y0, 602.0, y1, Tile("gwc_conc", w_ft=6.0))
    _ground_pad(mb, 602.0, y0, x1, y1, Tile("gwc_drygrs", w_ft=14.0))

    # Tan/grey CMU cinderblock yard wall along east side of GC alley & E 5th corner
    mb.detail_box_ft(430.5, 1210.0, GROUND_TOP, 431.4, 1304.0, 6.2, Tile("gwc_cinder", w_ft=6.0), faces={"b": "skip"})
    mb.detail_box_ft(430.5, 1318.0, GROUND_TOP, 431.4, y1 - 1.5, 6.2, Tile("gwc_cinder", w_ft=6.0), faces={"b": "skip"})
    mb.detail_box_ft(431.4, 1209.5, GROUND_TOP, 562.0, 1210.3, 5.2, Tile("gwc_cinder", w_ft=6.0), faces={"b": "skip"})

    # West-of-Wallace residential cottages (BLDG 60053091, 60057548, 60057204, 60053622)
    _sealed_cottage(mb, 486.0, 1224.0, 532.0, 1252.0, "gwc_bstucco", roof_tex="gwc_shingle", ridge_axis="x", face_side="s", wall_h=9.6, peak_h=2.8)
    _sealed_cottage(mb, 482.0, 1270.0, 516.0, 1302.0, "gwc_crmstuc", ridge_axis="y", face_side="e", wall_h=9.6, peak_h=2.8)
    _sealed_cottage(mb, 488.0, 1316.0, 526.0, y1 - 1.0, "gwc_wstucco", ridge_axis="x", face_side="e", wall_h=9.6, peak_h=2.6)
    mb.structural_box_ft(437.0, 1312.0, 0.0, 458.0, y1 - 1.0, 9.5, Tile("gwc_corrug", w_ft=6.0))
    _gable_roof(mb, 437.0, 1312.0, 458.0, y1 - 1.0, 9.5, 2.5, ridge_axis="y", tex_roof="gwc_galv", tex_gable="gwc_corrug")

    # East-of-Wallace residential cottages cleanly closing eastern fringe
    _sealed_cottage(mb, 612.0, 1232.0, 647.5, 1274.0, "gwc_crmstuc", ridge_axis="x", face_side="w", wall_h=9.8, peak_h=2.8)
    _sealed_cottage(mb, 612.0, 1290.0, 647.5, 1320.0, "gwc_bstucco", ridge_axis="x", face_side="w", wall_h=9.8, peak_h=2.6)

    for tx, ty in ((466.0, 1258.0), (544.0, 1296.0), (468.0, 1296.0)):
        _tree_cutout(mb, tx, ty, h=20.0, w=14.0, tex="{gwc_tree2")


# =============================================================================
# PUBLIC ENTRYPOINT & STANDALONE VALIDATION
# =============================================================================

def build_east_union(mb: MapBuilder) -> None:
    """Build all East Side of S Union Ave parcels North -> South."""
    global Fit, Tile
    mb_mod = sys.modules.get(mb.__class__.__module__)
    if mb_mod is not None:
        Fit = getattr(mb_mod, "Fit", Fit)
        Tile = getattr(mb_mod, "Tile", Tile)
    _build_century_glass(mb)
    _build_el_don_brownfield(mb)
    _build_redwood_senior(mb)
    _build_star_liter_motel(mb)
    _build_rv_park_922(mb)
    _build_sunland_motel(mb)
    _build_country_inn_motel(mb)
    _build_playfair_market(mb)
    _build_south_strip(mb)
    _build_gc_deal_time(mb)
    _build_gc_alley_east(mb)
    _build_gc_reyes_tires(mb)
    _build_gc_north_fringe(mb)


def _check_spatial_contracts(mb: MapBuilder) -> List[str]:
    """Verify every emitted brush lies strictly inside East Union bounds and outside streets/GC."""
    errors: List[str] = []
    bt_y0, bt_y1 = BELLE_TERRACE_CORRIDOR_Y
    ad_y0, ad_y1 = ADAMS_ST_CORRIDOR_Y
    e4_y0, e4_y1 = E_4TH_ST_CORRIDOR_Y
    e5_y0, e5_y1 = E_5TH_ST_CORRIDOR_Y
    al_x0, al_x1 = GC_ALLEY_X
    gc_x0, gc_y0, gc_x1, gc_y1 = GC_LOT_FT
    for grp, brushes in mb._brushes.items():  # noqa: SLF001
        for idx, (bbox_u, _planes) in enumerate(brushes):
            ux0, uy0, _uz0, ux1, uy1, _uz1 = bbox_u
            bx0, by0, bx1, by1 = ux0 / U_FT, uy0 / U_FT, ux1 / U_FT, uy1 / U_FT
            if bx0 < EAST_X_MIN - 1e-3 or bx1 > HX1 + 1e-3:
                errors.append(f"{grp}[{idx}] X=[{bx0:.2f}, {bx1:.2f}] outside [283, 650]")
            if by0 < HY0 - 1e-3 or by1 > HY1 + 1e-3:
                errors.append(f"{grp}[{idx}] Y=[{by0:.2f}, {by1:.2f}] outside [{HY0}, {HY1}]")
            if by1 > bt_y0 + 1e-3 and by0 < bt_y1 - 1e-3:
                errors.append(f"{grp}[{idx}] Y=[{by0:.2f}, {by1:.2f}] overlaps Belle Terrace ({bt_y0}..{bt_y1})")
            if by1 > ad_y0 + 1e-3 and by0 < ad_y1 - 1e-3:
                errors.append(f"{grp}[{idx}] Y=[{by0:.2f}, {by1:.2f}] overlaps Adams St ({ad_y0}..{ad_y1})")
            if by1 > e4_y0 + 1e-3 and by0 < e4_y1 - 1e-3:
                errors.append(f"{grp}[{idx}] Y=[{by0:.2f}, {by1:.2f}] overlaps E 4th St ({e4_y0}..{e4_y1})")
            if by1 > e5_y0 + 1e-3 and by0 < e5_y1 - 1e-3:
                errors.append(f"{grp}[{idx}] Y=[{by0:.2f}, {by1:.2f}] overlaps E 5th St ({e5_y0}..{e5_y1})")
            if by1 > gc_y0 + 1e-3 and bx1 > al_x0 + 1e-3 and bx0 < al_x1 - 1e-3:
                errors.append(f"{grp}[{idx}] X=[{bx0:.2f}, {bx1:.2f}] Y=[{by0:.2f}, {by1:.2f}] overlaps GC Alley ({al_x0}..{al_x1})")
            if bx1 > gc_x0 + 1e-3 and bx0 < gc_x1 - 1e-3 and by1 > gc_y0 + 1e-3 and by0 < gc_y1 - 1e-3:
                errors.append(f"{grp}[{idx}] X=[{bx0:.2f}, {bx1:.2f}] Y=[{by0:.2f}, {by1:.2f}] overlaps gc_great_castle {GC_LOT_FT}")
            if by0 < 750.25 - 1e-3 and by1 > 750.0 + 1e-3:
                errors.append(f"{grp}[{idx}] Y=[{by0:.2f}, {by1:.2f}] crosses Century Glass / Deal Time seam (750.0..750.25)")
    return errors


if __name__ == "__main__":
    mb = MapBuilder(
        wad_paths=DEFAULT_WAD_PATHS,
        strict_vis=True,
        check_textures=True,
        require_gwc_prefix=True,
    )
    build_east_union(mb)
    mb.validate_all()
    spatial_errs = _check_spatial_contracts(mb)
    if spatial_errs:
        for err in spatial_errs[:15]:
            print(f"[SPATIAL ERROR] {err}")
        raise SystemExit(1)

    st = mb.stats()
    all_brushes = [b for brushes in mb._brushes.values() for b in brushes]  # noqa: SLF001
    total_brushes = st["total_brushes"]
    total_faces = sum(len(planes) for _bb, planes in all_brushes)
    active_faces = sum(
        1
        for _bb, planes in all_brushes
        for ln in planes
        if ln.rsplit(")", 1)[-1].strip().split(None, 1)[0].lower() != "skip"
    )
    lights = sum(1 for e in mb._entities if e.get("classname") == "light")  # noqa: SLF001
    print(
        f"gw_east_union OK: brushes={total_brushes} {st['brushes']}, "
        f"faces={total_faces} (active={active_faces}), "
        f"rooms={st['rooms']}, doors={st['doorways']}, spots={st['spots']}, "
        f"lights={lights}, textures={len(st['textures_used'])}, "
        f"missing={len(st['missing_textures'])}"
    )
