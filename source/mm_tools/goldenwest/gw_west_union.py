"""West S Union Ave & West Residential Neighborhood geometry builder for Golden West.

Covers all 12 southern ``PARCELS["west_union"]`` zones (``y in [-820.0, +750.0] ft``) plus
both northern West-of-Union framing parcels ``gc_west_4th_onestop`` (``y in [750.0, 842.0]``)
and ``gc_west_manila_dg`` (``y in [882.0, 1340.0]``), remaining strictly within ``x in [-490.0, +172.0] ft``
and strictly outside ``CASINO_LOT_FT`` and all street corridors (including E 4th St ``y in [842.0, 882.0]``).

Exported entry point: ``build_west_union(mb)``.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

if __package__ in (None, ""):
    _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    if _THIS_DIR not in sys.path:
        sys.path.insert(0, _THIS_DIR)
    from gw_lib import (  # type: ignore
        CASINO_LOT_FT,
        E_4TH_ST_CORRIDOR_Y,
        HX0,
        HY0,
        HY1,
        PARCELS,
        STREETS,
        U_FT,
        Fit,
        MapBuilder,
        Tile,
    )
else:
    from .gw_lib import (
        CASINO_LOT_FT,
        E_4TH_ST_CORRIDOR_Y,
        HX0,
        HY0,
        HY1,
        PARCELS,
        STREETS,
        U_FT,
        Fit,
        MapBuilder,
        Tile,
    )


# ---------------------------------------------------------------------------
# Cataloged Texture Palette (strictly gwc_* / {gwc_* + skip / clip)
# ---------------------------------------------------------------------------
TEX = {
    # Ground & paving
    "asphalt": "gwc_asph",
    "wline": "gwc_wline",
    "concrete": "gwc_conc",
    "conc_slab": "gwc_concslab",
    "dirt": "gwc_dirt",
    "grass": "gwc_lawn",
    "weed": "gwc_drygrs",
    "mulch": "gwc_mulch",
    "tile": "gwc_tile",
    "carpet": "gwc_carpet",
    # Walls, stucco, masonry, siding
    "stucco_cream": "gwc_crmstuc",
    "stucco_red": "gwc_rstucco",
    "stucco_white": "gwc_wstucco",
    "stucco_slate": "gwc_slatstuc",
    "stucco_tan": "gwc_bstucco",
    "stucco_mint": "gwc_stucco",
    "cmu_tan": "gwc_cinder",
    "brick": "gwc_brick",
    "siding": "gwc_redsid",
    "wood_dark": "gwc_wood",
    "wood_tan": "gwc_wood",
    "corrug_silver": "gwc_corrug",
    "steel_dark": "gwc_dark",
    "steel_light": "gwc_steel",
    "white": "gwc_white",
    "galv": "gwc_galv",
    "hvac": "gwc_hvac",
    "rust": "gwc_beam",
    # Roofs & canopies
    "shingle_dark": "gwc_shingle",
    "shingle_brown": "gwc_resshing",
    "roof_tpo": "gwc_tpo",
    "fascia_brown": "gwc_batten",
    "drywall": "gwc_drywall",
    "ceil_grid": "gwc_ceil2x4",
    "troffer": "gwc_troffer",
    "granite": "gwc_granite",
    "leather": "gwc_leather",
    "bed": "gwc_bed",
    "motel_cpt": "gwc_motelcpt",
    # Windows, doors, garage bays
    "glass": "gwc_glass",
    "win_house": "gwc_glass",
    "win_motel": "gwc_blind",
    "rollup": "gwc_rollup",
    "door_wood": "gwc_wooddoor",
    # Signs & decals
    "sign_carnitas": "gwc_carnit",
    "sign_menudo_flag": "{gwc_menudof",
    "sign_menu": "gwc_menu",
    "carnmenu": "gwc_carnmenu",
    "sign_uhaul": "gwc_uhaul",
    "sign_trksale": "gwc_trksale",
    "uhaul_box": "gwc_uhaulbox",
    "sign_ramos": "gwc_ramos",
    "sign_ramos_open": "gwc_ramosop",
    "sign_bestdeals": "gwc_bdeal",
    "sign_stop": "{gwc_stopsign",
    "sign_oneway": "gwc_oneway",
    "sign_super8": "gwc_super8",
    "sign_shamrock": "gwc_shamrock",
    "sign_dg": "gwc_dgmrkt",
    "billboard": "gwc_bboard",
    # Fences & foliage
    "green_mesh": "{gwc_greenmesh",
    "iron_fence": "{gwc_ironfence",
    "chain_fence": "{gwc_chain",
    "slat_rail": "{gwc_slat",
    "palm_frond": "{gwc_palmfr",
    "bark": "gwc_bark",
    "tree_1": "{gwc_tree1",
    "tree_2": "{gwc_tree2",
    "tree_3": "{gwc_tree3",
    "hedge": "gwc_hedge",
    # Props & vehicles
    "swamp_cooler": "gwc_swamp",
    "booth": "gwc_booth",
    "dumpster": "gwc_dumpstr",
    "tire": "gwc_tire",
    "car_lift": "gwc_carlift",
    "car_win": "gwc_carwin",
    "car_white": "gwc_carwht",
    "car_silver": "gwc_carsil",
    "car_red": "gwc_carred",
    "car_blue": "gwc_carblu",
}

CAR_COLORS = (
    TEX["car_white"],
    TEX["car_silver"],
    TEX["car_red"],
    TEX["car_blue"],
    TEX["stucco_slate"],
    TEX["stucco_tan"],
)


# ---------------------------------------------------------------------------
# Generic Geometry & Hull-1 Safe Helpers
# ---------------------------------------------------------------------------
def _pad(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    tex: str,
    z0: float = 0.0,
    z1: Optional[float] = None,
) -> None:
    """Place a parcel surface slab flush above gw_streets valley earth bed (0.0)."""
    top_z = z1 if z1 is not None else (2.0 / 12.0 if tex in (TEX["asphalt"], TEX["concrete"], TEX["conc_slab"]) else 1.0 / 12.0)
    faces = {"t": Tile(tex, 12.0), "b": "skip", "e": Tile(tex, 12.0), "w": Tile(tex, 12.0), "n": Tile(tex, 12.0), "s": Tile(tex, 12.0)}
    mb.detail_box_ft(x0, y0, z0, x1, y1, top_z, Tile(tex, 12.0), faces=faces)


def _curb_pad(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    tex: str,
    z0: float = 0.0,
    z1: float = 0.25,
) -> None:
    """Place a walkable low pad or apron slab (<= 3.6u rise)."""
    mb.detail_box_ft(x0, y0, z0, x1, y1, z1, Tile(tex, 8.0), faces={"b": "skip"})


def _sign_panel(
    mb: MapBuilder,
    face: str,
    pos: float,
    a0: float,
    a1: float,
    b0: float,
    b1: float,
    tex: str,
    thick: float = 0.08,
) -> None:
    """Attach a flush Fit-mapped sign decal onto an exterior face."""
    face_norm = {"-y": "s", "+y": "n", "+x": "e", "-x": "w", "+z": "t", "-z": "b"}.get(face, face)
    mb.sign_decal_ft(face_norm, pos, a0, a1, b0, b1, tex, thick_ft=thick, group="illus")


def _gable_roof(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_eave: float,
    z_ridge: float,
    tex_roof: str,
    tex_gable: str,
    over: float = 1.0,
    ridge_along: str = "x",
    fascia_h: float = 0.45,
) -> None:
    """Place a pitched gable roof prism plus overhanging eave fascia."""
    rx0, ry0, rx1, ry1 = x0 - over, y0 - over, x1 + over, y1 + over
    mb.detail_box_ft(
        rx0,
        ry0,
        z_eave - fascia_h,
        rx1,
        ry1,
        z_eave,
        Tile(TEX["fascia_brown"], 8.0),
        faces={"t": "skip"},
    )
    if ridge_along == "x":
        ym = 0.5 * (ry0 + ry1)
        pts = [(ry0, z_eave), (ry1, z_eave), (ym, z_ridge)]
        mb.prism_yz_ft(pts, rx0, rx1, Tile(tex_roof, 8.0), tex_end=Tile(tex_gable, 8.0), group="detail")
    else:
        xm = 0.5 * (rx0 + rx1)
        pts = [(rx0, z_eave), (rx1, z_eave), (xm, z_ridge)]
        mb.prism_xz_ft(pts, ry0, ry1, Tile(tex_roof, 8.0), tex_end=Tile(tex_gable, 8.0), group="detail")


def _hip_roof(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_eave: float,
    z_ridge: float,
    tex_roof: str,
    over: float = 1.1,
) -> None:
    """Place a clean multi-tier hip roof silhouette with overhanging fascia."""
    rx0, ry0, rx1, ry1 = x0 - over, y0 - over, x1 + over, y1 + over
    mb.detail_box_ft(
        rx0,
        ry0,
        z_eave - 0.5,
        rx1,
        ry1,
        z_eave,
        Tile(TEX["fascia_brown"], 8.0),
        faces={"t": "skip"},
    )
    w, d = rx1 - rx0, ry1 - ry0
    tiers = 4
    dz = (z_ridge - z_eave) / tiers
    for i in range(tiers):
        frac = i / float(tiers)
        inset_x = min(w * 0.42, (d * 0.42) * frac + (w - d) * 0.10 * frac)
        inset_y = min(d * 0.42, (d * 0.42) * frac)
        mb.detail_box_ft(
            rx0 + inset_x,
            ry0 + inset_y,
            z_eave + i * dz,
            rx1 - inset_x,
            ry1 - inset_y,
            z_eave + (i + 1) * dz,
            Tile(tex_roof, 8.0),
            faces={"b": "skip"},
        )


def _swamp_cooler(mb: MapBuilder, cx: float, cy: float, z_base: float) -> None:
    """Place a galvanized rooftop evaporative swamp cooler."""
    mb.detail_box_ft(
        cx - 1.75,
        cy - 1.75,
        z_base,
        cx + 1.75,
        cy + 1.75,
        z_base + 2.6,
        Fit(TEX["swamp_cooler"]),
        faces={"b": "skip"},
    )


def _fence_line_x(
    mb: MapBuilder,
    y: float,
    x0: float,
    x1: float,
    z0: float,
    z1: float,
    tex: str,
    gaps: Sequence[Tuple[float, float]] = (),
    post_step: float = 16.0,
    post_tex: Optional[str] = None,
    thick: float = 0.25,
) -> None:
    """Build an east-west fence leaving explicit walkable driveway/gate gaps."""
    spans: List[Tuple[float, float]] = [(x0, x1)]
    for g0, g1 in sorted(gaps):
        nxt: List[Tuple[float, float]] = []
        for s0, s1 in spans:
            if g1 <= s0 or g0 >= s1:
                nxt.append((s0, s1))
            else:
                if g0 > s0 + 0.5:
                    nxt.append((s0, g0))
                if g1 < s1 - 0.5:
                    nxt.append((g1, s1))
        spans = nxt

    ht = thick * 0.5
    p_tex = post_tex or TEX["steel_dark"]
    is_ground_alpha = z0 <= 0.25 and tex in (TEX["green_mesh"], TEX["iron_fence"], TEX["chain_fence"])
    panel_faces: Dict[str, str] = {"b": "skip", "t": "skip"} if is_ground_alpha else {"b": "skip"}
    eff_step = max(post_step, 36.0) if (is_ground_alpha and post_step > 0) else post_step
    for s0, s1 in spans:
        mb.detail_box_ft(s0, y - ht, z0, s1, y + ht, z1, Tile(tex, 6.0), faces=panel_faces)
        if eff_step > 0:
            cur = s0
            while cur <= s1 + 0.01:
                px = min(cur, s1)
                mb.detail_box_ft(px - 0.25, y - 0.25, z0, px + 0.25, y + 0.25, z1 + 0.25, Tile(p_tex, 4.0), faces={"b": "skip"})
                if px >= s1 - 0.01:
                    break
                cur = min(cur + eff_step, s1)


def _fence_line_y(
    mb: MapBuilder,
    x: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    tex: str,
    gaps: Sequence[Tuple[float, float]] = (),
    post_step: float = 16.0,
    post_tex: Optional[str] = None,
    thick: float = 0.25,
) -> None:
    """Build a north-south fence leaving explicit walkable driveway/gate gaps."""
    spans: List[Tuple[float, float]] = [(y0, y1)]
    for g0, g1 in sorted(gaps):
        nxt: List[Tuple[float, float]] = []
        for s0, s1 in spans:
            if g1 <= s0 or g0 >= s1:
                nxt.append((s0, s1))
            else:
                if g0 > s0 + 0.5:
                    nxt.append((s0, g0))
                if g1 < s1 - 0.5:
                    nxt.append((g1, s1))
        spans = nxt

    ht = thick * 0.5
    p_tex = post_tex or TEX["steel_dark"]
    is_ground_alpha = z0 <= 0.25 and tex in (TEX["green_mesh"], TEX["iron_fence"], TEX["chain_fence"])
    panel_faces: Dict[str, str] = {"b": "skip", "t": "skip"} if is_ground_alpha else {"b": "skip"}
    eff_step = max(post_step, 36.0) if (is_ground_alpha and post_step > 0) else post_step
    for s0, s1 in spans:
        mb.detail_box_ft(x - ht, s0, z0, x + ht, s1, z1, Tile(tex, 6.0), faces=panel_faces)
        if eff_step > 0:
            cur = s0
            while cur <= s1 + 0.01:
                py = min(cur, s1)
                mb.detail_box_ft(x - 0.25, py - 0.25, z0, x + 0.25, py + 0.25, z1 + 0.25, Tile(p_tex, 4.0), faces={"b": "skip"})
                if py >= s1 - 0.01:
                    break
                cur = min(cur + eff_step, s1)


def _palm_tree(mb: MapBuilder, cx: float, cy: float, height: float = 22.0, z0: float = 0.0) -> None:
    """Place a tall Bakersfield palm with narrow trunk and crossed alpha-cutout frond crown."""
    trunk_top = z0 + height - 2.0
    mb.cyl_ft(cx, cy, 0.50, z0, trunk_top, sides=6, tex_side=Tile(TEX["bark"], 4.0), tex_top="skip", group="detail")
    # Frond canopy cleanly above Hull-1 jump height (z >= 14 ft) using Fit alpha illus panels
    fz0 = max(z0 + 13.5, trunk_top - 2.0)
    fz1 = z0 + height + 1.4
    span = 5.2
    mb.flush_panel_ft(
        cx - span, cy - 0.08, fz0, cx + span, cy + 0.08, fz1,
        {"n": Fit(TEX["palm_frond"]), "s": Fit(TEX["palm_frond"])}, group="illus",
    )
    mb.flush_panel_ft(
        cx - 0.08, cy - span, fz0, cx + 0.08, cy + span, fz1,
        {"e": Fit(TEX["palm_frond"]), "w": Fit(TEX["palm_frond"])}, group="illus",
    )
    mb.slab_ramp_xft(cx - 4.4, cx, cy - 3.0, cy + 3.0, fz1 - 2.2, fz1 - 0.6, Fit(TEX["palm_frond"]), thick_ft=0.12, group="illus")
    mb.slab_ramp_xft(cx, cx + 4.4, cy - 3.0, cy + 3.0, fz1 - 0.6, fz1 - 2.2, Fit(TEX["palm_frond"]), thick_ft=0.12, group="illus")


def _yard_tree(
    mb: MapBuilder,
    cx: float,
    cy: float,
    height: float = 18.0,
    crown_r: float = 4.5,
    tex_crown: Optional[str] = None,
    z0: float = 0.0,
) -> None:
    """Place a residential/windbreak tree using crossed Fit alpha-cutout canopy panels."""
    mb.cyl_ft(cx, cy, 0.42, z0, z0 + height * 0.44, sides=6, tex_side=Tile(TEX["bark"], 4.0), tex_top="skip", group="detail")
    c_tex = tex_crown or TEX["tree_1"]
    hw = crown_r
    mb.flush_panel_ft(
        cx - hw, cy - 0.08, z0 + 0.2, cx + hw, cy + 0.08, z0 + height,
        {"n": Fit(c_tex), "s": Fit(c_tex)}, group="illus",
    )
    mb.flush_panel_ft(
        cx - 0.08, cy - hw, z0 + 0.2, cx + 0.08, cy + hw, z0 + height,
        {"e": Fit(c_tex), "w": Fit(c_tex)}, group="illus",
    )


def _parked_car(
    mb: MapBuilder,
    cx: float,
    cy: float,
    body_tex: str,
    axis: str = "x",
    z0: float = 0.0,
) -> None:
    """Place a low-poly parked sedan/coupe oriented along ``x`` or ``y`` (3 brushes)."""
    hl, hw = 7.2, 2.9  # 14.4 ft x 5.8 ft compact lot car
    if axis == "x":
        x0, x1, y0, y1 = cx - hl, cx + hl, cy - hw, cy + hw
        mb.detail_box_ft(x0, y0, z0 + 0.5, x1, y1, z0 + 2.6, Tile(body_tex, 6.0))
        mb.detail_box_ft(cx - 3.3, y0 + 0.25, z0 + 2.6, cx + 3.0, y1 - 0.25, z0 + 4.4, Tile(TEX["car_win"], 4.0), faces={"b": "skip"})
        # Single dark lower wheel/undercarriage block (below z0+0.5, zero side overlap)
        mb.detail_box_ft(x0 + 1.1, y0 + 0.08, z0, x1 - 1.1, y1 - 0.08, z0 + 0.5, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
    else:
        x0, x1, y0, y1 = cx - hw, cx + hw, cy - hl, cy + hl
        mb.detail_box_ft(x0, y0, z0 + 0.5, x1, y1, z0 + 2.6, Tile(body_tex, 6.0))
        mb.detail_box_ft(x0 + 0.25, cy - 3.3, z0 + 2.6, x1 - 0.25, cy + 3.0, z0 + 4.4, Tile(TEX["car_win"], 4.0), faces={"b": "skip"})
        mb.detail_box_ft(x0 + 0.08, y0 + 1.1, z0, x1 - 0.08, y1 - 1.1, z0 + 0.5, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})


def _uhaul_truck(mb: MapBuilder, cx: float, cy: float, facing: str = "S", z0: float = 0.0) -> None:
    """Place an orange/white U-Haul box van (facing ``S`` or ``E``) as clean combat cover."""
    if facing in ("S", "N"):
        # Cargo box + cab along Y
        sgn = -1.0 if facing == "S" else 1.0
        bx0, bx1 = cx - 3.7, cx + 3.7
        by0, by1 = (cy - 3.0, cy + 10.5) if sgn < 0 else (cy - 10.5, cy + 3.0)
        mb.detail_box_ft(bx0, by0, z0 + 1.6, bx1, by1, z0 + 9.2, Tile(TEX["stucco_white"], 8.0))
        _sign_panel(mb, "-x", bx0, by0 + 0.5, by1 - 0.5, z0 + 2.2, z0 + 8.6, TEX["uhaul_box"])
        _sign_panel(mb, "+x", bx1, by0 + 0.5, by1 - 0.5, z0 + 2.2, z0 + 8.6, TEX["uhaul_box"])
        cy0, cy1 = (by0 - 5.2, by0) if sgn < 0 else (by1, by1 + 5.2)
        mb.detail_box_ft(cx - 3.2, cy0, z0 + 1.2, cx + 3.2, cy1, z0 + 6.4, Tile(TEX["stucco_red"], 6.0))
        mb.detail_box_ft(bx0 + 0.2, min(by0, cy0) + 1.0, z0, bx1 - 0.2, max(by1, cy1) - 1.0, z0 + 1.6, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
    else:
        bx0, bx1, by0, by1 = cx - 10.0, cx + 3.5, cy - 3.7, cy + 3.7
        mb.detail_box_ft(bx0, by0, z0 + 1.6, bx1, by1, z0 + 9.2, Tile(TEX["stucco_white"], 8.0))
        _sign_panel(mb, "-y", by0, bx0 + 0.5, bx1 - 0.5, z0 + 2.2, z0 + 8.6, TEX["uhaul_box"])
        _sign_panel(mb, "+y", by1, bx0 + 0.5, bx1 - 0.5, z0 + 2.2, z0 + 8.6, TEX["uhaul_box"])
        mb.detail_box_ft(bx1, cy - 3.2, z0 + 1.2, bx1 + 5.2, cy + 3.2, z0 + 6.4, Tile(TEX["stucco_red"], 6.0))
        mb.detail_box_ft(bx0 + 1.0, by0 + 0.2, z0, bx1 + 4.0, by1 - 0.2, z0 + 1.6, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})


def _pole_sign(
    mb: MapBuilder,
    cx: float,
    cy: float,
    w: float,
    h: float,
    z_bot: float,
    z_top: float,
    tex_front: str,
    tex_back: Optional[str] = None,
    face_axis: str = "x",
    double_pole: bool = True,
    pole_tex: Optional[str] = None,
) -> None:
    """Place a single-pole or double-pole commercial pylon sign with front/back panels."""
    p_tex = pole_tex or TEX["steel_dark"]
    if double_pole:
        off = max(1.5, w * 0.34)
        for s in (-1.0, 1.0):
            px, py = (cx + s * off, cy) if face_axis == "y" else (cx, cy + s * off)
            mb.detail_box_ft(px - 0.4, py - 0.4, 0.0, px + 0.4, py + 0.4, z_bot + 0.5, Tile(p_tex, 4.0), faces={"b": "skip", "t": "skip"})
    else:
        mb.detail_box_ft(cx - 0.5, cy - 0.5, 0.0, cx + 0.5, cy + 0.5, z_bot + 0.5, Tile(p_tex, 4.0), faces={"b": "skip", "t": "skip"})

    b_tex = tex_back or tex_front
    if face_axis == "x":
        mb.detail_box_ft(cx - 0.45, cy - w * 0.5, z_bot, cx + 0.45, cy + w * 0.5, z_top, Tile(TEX["steel_dark"], 4.0))
        _sign_panel(mb, "+x", cx + 0.45, cy - w * 0.48, cy + w * 0.48, z_bot + 0.2, z_top - 0.2, tex_front)
        _sign_panel(mb, "-x", cx - 0.45, cy - w * 0.48, cy + w * 0.48, z_bot + 0.2, z_top - 0.2, b_tex)
    else:
        mb.detail_box_ft(cx - w * 0.5, cy - 0.45, z_bot, cx + w * 0.5, cy + 0.45, z_top, Tile(TEX["steel_dark"], 4.0))
        _sign_panel(mb, "-y", cy - 0.45, cx - w * 0.48, cx + w * 0.48, z_bot + 0.2, z_top - 0.2, tex_front)
        _sign_panel(mb, "+y", cy + 0.45, cx - w * 0.48, cx + w * 0.48, z_bot + 0.2, z_top - 0.2, b_tex)


def _carport_canopy(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_roof: float = 10.5,
    tex_roof: Optional[str] = None,
    tex_post: Optional[str] = None,
    attach_side: Optional[str] = None,
) -> None:
    """Place an open freestanding steel/corrugated carport with slender corner posts."""
    r_tex = tex_roof or TEX["steel_dark"]
    p_tex = tex_post or TEX["steel_dark"]
    roof_faces = {attach_side: "skip"} if attach_side in ("w", "e", "s", "n") else None
    mb.detail_box_ft(x0, y0, z_roof, x1, y1, z_roof + 0.45, Tile(r_tex, 8.0), faces=roof_faces)
    pxs = [x0 + 0.6, x1 - 0.6]
    if (x1 - x0) > 34.0:
        pxs.insert(1, 0.5 * (x0 + x1))
    pys = [y0 + 0.6, y1 - 0.6]
    if (y1 - y0) > 34.0:
        pys.insert(1, 0.5 * (y0 + y1))
    for px in pxs:
        for py in pys:
            mb.detail_box_ft(px - 0.28, py - 0.28, 0.0, px + 0.28, py + 0.28, z_roof, Tile(p_tex, 4.0), faces={"b": "skip", "t": "skip"})


def _wall_with_openings(
    mb: MapBuilder,
    axis: str,
    w0: float,
    w1: float,
    s0: float,
    s1: float,
    z0: float,
    z1: float,
    ext_side: str,
    tex_ext: str,
    tex_int: str,
    doorways: Sequence[Tuple[float, float, float, str]] = (),
    windows: Sequence[Tuple[float, float, float, float]] = (),
    structural_min_span: Optional[float] = 28.0,
) -> None:
    """Build a perimeter wall putting long full-height VIS blockers in worldspawn and openings in func_detail."""
    int_side = {"n": "s", "s": "n", "e": "w", "w": "e"}[ext_side]
    events: List[Tuple[float, float, str, object]] = []
    for d0, d1, d_top, dname in doorways:
        events.append((d0, d1, "door", (d_top, dname)))
    for g0, g1, gz0, gz1 in windows:
        events.append((g0, g1, "win", (gz0, gz1)))
    events.sort(key=lambda item: item[0])

    segs: List[Tuple[float, float, float, float]] = []

    def _queue_seg(a0: float, a1: float, bz0: float, bz1: float) -> None:
        if a1 - a0 <= 0.04 or bz1 - bz0 <= 0.04:
            return
        segs.append((a0, a1, bz0, bz1))

    cur = s0
    wm = 0.5 * (w0 + w1)
    for a0, a1, kind, extra in events:
        if a0 > cur:
            _queue_seg(cur, min(a0, s1), z0, z1)
        if kind == "door":
            d_top, dname = extra  # type: ignore[misc]
            _queue_seg(a0, a1, d_top, z1)
            dm = 0.5 * (a0 + a1)
            orig = (dm, wm, z0) if axis == "x" else (wm, dm, z0)
            mb.register_doorway_ft(dname, a1 - a0, d_top - z0, origin_ft=orig, axis=axis)
        else:
            gz0, gz1 = extra  # type: ignore[misc]
            _queue_seg(a0, a1, z0, gz0)
            _queue_seg(a0, a1, gz1, z1)
        cur = max(cur, a1)
    if cur < s1:
        _queue_seg(cur, s1, z0, z1)

    for idx, (a0, a1, bz0, bz1) in enumerate(segs):
        is_full_h = bz0 <= z0 + 0.05 and bz1 >= z1 - 0.05
        is_world = structural_min_span is not None and is_full_h and (a1 - a0) >= structural_min_span
        b_tex: object = Tile(tex_int, 8.0) if (is_world or bz0 > z0 + 0.05) else "skip"
        t_tex: object = Tile(tex_int, 8.0) if (is_world or bz1 < z1 - 0.05) else "skip"
        start_cov = (
            not is_world
            and any(
                j != idx and abs(oa1 - a0) < 0.05 and obz0 <= bz0 + 0.05 and obz1 >= bz1 - 0.05
                for j, (_, oa1, obz0, obz1) in enumerate(segs)
            )
        )
        end_cov = (
            not is_world
            and any(
                j != idx and abs(oa0 - a1) < 0.05 and obz0 <= bz0 + 0.05 and obz1 >= bz1 - 0.05
                for j, (oa0, _, obz0, obz1) in enumerate(segs)
            )
        )
        start_tex: object = "skip" if start_cov else Tile(tex_ext if abs(a0 - s0) < 0.05 else tex_int, 8.0)
        end_tex: object = "skip" if end_cov else Tile(tex_ext if abs(a1 - s1) < 0.05 else tex_int, 8.0)
        if axis == "x":
            faces = {
                ext_side: Tile(tex_ext, 8.0),
                int_side: Tile(tex_int, 8.0),
                "w": start_tex,
                "e": end_tex,
                "b": b_tex,
                "t": t_tex,
            }
            if is_world:
                mb.structural_box_ft(a0, w0, bz0, a1, w1, bz1, tex_ext, faces=faces)
            else:
                mb.detail_box_ft(a0, w0, bz0, a1, w1, bz1, tex_ext, faces=faces)
        else:
            faces = {
                ext_side: Tile(tex_ext, 8.0),
                int_side: Tile(tex_int, 8.0),
                "s": start_tex,
                "n": end_tex,
                "b": b_tex,
                "t": t_tex,
            }
            if is_world:
                mb.structural_box_ft(w0, a0, bz0, w1, a1, bz1, tex_ext, faces=faces)
            else:
                mb.detail_box_ft(w0, a0, bz0, w1, a1, bz1, tex_ext, faces=faces)


def _rect_shell(
    mb: MapBuilder,
    room_name: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_floor: float,
    z_ceil: float,
    tex_ext: str,
    tex_int: str,
    tex_floor: str,
    thick: float = 0.75,
    doors_n: Sequence[Tuple[float, float, float, str]] = (),
    doors_s: Sequence[Tuple[float, float, float, str]] = (),
    doors_e: Sequence[Tuple[float, float, float, str]] = (),
    doors_w: Sequence[Tuple[float, float, float, str]] = (),
    wins_n: Sequence[Tuple[float, float, float, float]] = (),
    wins_s: Sequence[Tuple[float, float, float, float]] = (),
    wins_e: Sequence[Tuple[float, float, float, float]] = (),
    wins_w: Sequence[Tuple[float, float, float, float]] = (),
    tex_ceil: Optional[str] = None,
    add_troffers: bool = False,
    build_floor: bool = True,
    build_ceil: bool = True,
    ceil_top: Optional[float] = None,
    parapet_h: float = 0.0,
    parapet_tex: Optional[str] = None,
    light_level: float = 260.0,
    light_nx: int = 2,
    light_ny: int = 2,
    light_drop: float = 1.2,
    register_room: bool = True,
) -> None:
    """Construct an enterable structural room shell with Hull-1 verified doors and lights."""
    c_top = ceil_top if ceil_top is not None else (z_ceil + 0.65)
    c_tex = tex_ceil or tex_int
    if build_floor:
        slab_z0 = 2.0 / 12.0 if z_floor > (2.0 / 12.0 + 0.04) else 0.0
        mb.detail_box_ft(x0, y0, slab_z0, x1, y1, z_floor, Tile(tex_floor, 8.0), faces={"b": "skip"})
    if build_ceil:
        ceil_faces = {
            "b": Tile(c_tex, 8.0),
            "t": Tile(tex_ext, 8.0),
            "e": Tile(tex_ext, 8.0),
            "w": Tile(tex_ext, 8.0),
            "n": Tile(tex_ext, 8.0),
            "s": Tile(tex_ext, 8.0),
        }
        mb.structural_box_ft(x0, y0, z_ceil, x1, y1, c_top, tex_ext, faces=ceil_faces)
    if add_troffers:
        nx, ny = max(1, light_nx), max(1, light_ny)
        ix0, iy0 = x0 + thick + 2.0, y0 + thick + 2.0
        ix1, iy1 = x1 - thick - 2.0, y1 - thick - 2.0
        for ix in range(nx):
            tx = ix0 + (ix + 0.5) * (ix1 - ix0) / nx
            for iy in range(ny):
                ty = iy0 + (iy + 0.5) * (iy1 - iy0) / ny
                mb.flush_panel_ft(tx - 1.8, ty - 0.9, z_ceil - 0.05, tx + 1.8, ty + 0.9, z_ceil, {"b": Fit(TEX["troffer"])}, group="illus")
    if parapet_h > 0.0:
        p_tex = parapet_tex or tex_ext
        mb.detail_box_ft(x0, y0, c_top, x1, y0 + thick, c_top + parapet_h, Tile(p_tex, 8.0), faces={"b": "skip"})
        mb.detail_box_ft(x0, y1 - thick, c_top, x1, y1, c_top + parapet_h, Tile(p_tex, 8.0), faces={"b": "skip"})
        mb.detail_box_ft(x0, y0 + thick, c_top, x0 + thick, y1 - thick, c_top + parapet_h, Tile(p_tex, 8.0), faces={"b": "skip", "s": "skip", "n": "skip"})
        mb.detail_box_ft(x1 - thick, y0 + thick, c_top, x1, y1 - thick, c_top + parapet_h, Tile(p_tex, 8.0), faces={"b": "skip", "s": "skip", "n": "skip"})

    # Perimeter structural walls with exact exterior vs interior faces
    _wall_with_openings(mb, "x", y0, y0 + thick, x0, x1, z_floor, z_ceil, "s", tex_ext, tex_int, doors_s, wins_s)
    _wall_with_openings(mb, "x", y1 - thick, y1, x0, x1, z_floor, z_ceil, "n", tex_ext, tex_int, doors_n, wins_n)
    _wall_with_openings(mb, "y", x0, x0 + thick, y0 + thick, y1 - thick, z_floor, z_ceil, "w", tex_ext, tex_int, doors_w, wins_w)
    _wall_with_openings(mb, "y", x1 - thick, x1, y0 + thick, y1 - thick, z_floor, z_ceil, "e", tex_ext, tex_int, doors_e, wins_e)

    if register_room:
        mb.register_room_ft(room_name, z_floor, z_ceil)
    if light_level > 0:
        mb.interior_lights_ft(
            x0 + thick + 1.5,
            y0 + thick + 1.5,
            x1 - thick - 1.5,
            y1 - thick - 1.5,
            z_ceil - light_drop,
            nx=light_nx,
            ny=light_ny,
            light=light_level,
        )


def _add_window_glazing(
    mb: MapBuilder,
    axis: str,
    pos: float,
    a0: float,
    a1: float,
    b0: float,
    b1: float,
    tex: str,
) -> None:
    """Place a decorative non-solid glass/blind pane skipping wall-buried perimeter edge caps."""
    if axis == "x":
        mb.flush_panel_ft(a0 + 0.08, pos + 0.32, b0 + 0.08, a1 - 0.08, pos + 0.44, b1 - 0.08, {"n": Fit(tex), "s": Fit(tex)}, group="illus")
    else:
        mb.flush_panel_ft(pos + 0.32, a0 + 0.08, b0 + 0.08, pos + 0.44, a1 - 0.08, b1 - 0.08, {"e": Fit(tex), "w": Fit(tex)}, group="illus")


def _barred_square_window(
    mb: MapBuilder,
    axis: str,
    pos: float,
    a0: float,
    a1: float,
    b0: float,
    b1: float,
    bar_tex: Optional[str] = None,
    cols: int = 3,
    rows: int = 2,
) -> None:
    """Place tinted glass plus crisp interior vertical/horizontal security/sash mullions."""
    _add_window_glazing(mb, axis, pos, a0, a1, b0, b1, TEX["glass"])
    b_t = bar_tex or TEX["stucco_white"]
    bar_w = 0.14
    btile = Tile(b_t, 4.0)
    v_faces = {"n": btile, "s": btile, "e": btile, "w": btile}
    for i in range(1, cols):
        ca = a0 + (a1 - a0) * (i / float(cols))
        ca0, ca1 = max(a0, ca - bar_w * 0.5), min(a1, ca + bar_w * 0.5)
        if axis == "x":
            mb.flush_panel_ft(ca0, pos + 0.18, b0, ca1, pos + 0.56, b1, v_faces, group="illus")
        else:
            mb.flush_panel_ft(pos + 0.18, ca0, b0, pos + 0.56, ca1, b1, v_faces, group="illus")
    h_faces_x = {"n": btile, "s": btile, "t": btile, "b": btile}
    h_faces_y = {"e": btile, "w": btile, "t": btile, "b": btile}
    for j in range(1, rows):
        cb = b0 + (b1 - b0) * (j / float(rows))
        cb0, cb1 = max(b0, cb - bar_w * 0.5), min(b1, cb + bar_w * 0.5)
        if axis == "x":
            mb.flush_panel_ft(a0, pos + 0.18, cb0, a1, pos + 0.56, cb1, h_faces_x, group="illus")
        else:
            mb.flush_panel_ft(pos + 0.18, a0, cb0, pos + 0.56, a1, cb1, h_faces_y, group="illus")


# ---------------------------------------------------------------------------
# 1. North of Belle Terrace (y=582..750)
# ---------------------------------------------------------------------------
def _build_north_belle_commercial(mb: MapBuilder) -> None:
    """Build Carnitas Birria Menudo, 891/U-Haul yard, Happy Truck Warehouse, NW field."""
    # Ground pads for all four north parcels (y=582.25..749.75)
    _pad(mb, -489.75, 582.25, -150.0, 749.75, TEX["dirt"])
    _pad(mb, -150.0, 582.25, 171.75, 749.75, TEX["asphalt"])

    # ---- Carnitas Birria Menudo Diner (x=98.0..146.5, y=611.0..663.5) ----
    # Floor inside x=104..144, y=614..658 stays 100% open & Hull-1 walkable!
    cx0, cy0, cx1, cy1 = 98.0, 611.0, 146.5, 663.5
    _rect_shell(
        mb,
        "INT Carnitas Birria Diner",
        cx0,
        cy0,
        cx1,
        cy1,
        z_floor=0.25,
        z_ceil=11.0,
        tex_ext=TEX["stucco_red"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["tile"],
        thick=0.75,
        doors_s=[(119.0, 127.0, 9.2, "carnitas_south_front")],
        doors_e=[(625.0, 633.0, 9.2, "carnitas_east_patio")],
        doors_w=[(625.0, 633.0, 9.2, "carnitas_west_lot")],
        wins_s=[(105.0, 115.0, 3.2, 8.2), (131.0, 142.0, 3.2, 8.2)],
        wins_e=[(637.0, 652.0, 3.2, 8.2)],
        tex_ceil=TEX["ceil_grid"],
        add_troffers=True,
        parapet_h=1.6,
        parapet_tex=TEX["fascia_brown"],
        light_level=175.0,
        light_nx=2,
        light_ny=2,
        light_drop=1.5,
    )
    # Clean storefront plate glass + dark aluminum mullions (ZERO gwc_windoor / Century Glass!)
    _barred_square_window(mb, "x", cy0, 105.0, 115.0, 3.2, 8.2, bar_tex=TEX["steel_dark"], cols=2, rows=1)
    _barred_square_window(mb, "x", cy0, 131.0, 142.0, 3.2, 8.2, bar_tex=TEX["steel_dark"], cols=2, rows=1)
    _barred_square_window(mb, "y", cx1 - 0.75, 637.0, 652.0, 3.2, 8.2, bar_tex=TEX["steel_dark"], cols=3, rows=1)
    _sign_panel(mb, "-y", cy0, cx0 + 2.0, cx1 - 2.0, 11.4, 13.1, TEX["sign_carnitas"])
    _sign_panel(mb, "+x", cx1, cy0 + 2.0, cy1 - 2.0, 11.4, 13.1, TEX["sign_carnitas"])
    _sign_panel(mb, "-x", cx0, cy0 + 2.0, cy1 - 2.0, 11.4, 13.1, TEX["sign_carnitas"])

    # Kitchen pass-through counter, granite top, register, menu board & booths (x=104..144, y=614..658 stays open)
    mb.detail_box_ft(cx0 + 1.0, 658.4, 0.25, cx1 - 1.0, 661.8, 3.45, Tile(TEX["wood_tan"], 6.0), faces={"b": "skip", "t": "skip", "n": "skip"})
    mb.detail_box_ft(cx0 + 0.9, 658.3, 3.45, cx1 - 0.9, 661.9, 3.7, Tile(TEX["granite"], 4.0), faces={"b": "skip", "n": "skip"})
    mb.detail_box_ft(106.0, 659.2, 3.7, 108.0, 660.8, 4.7, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(cx0 + 1.0, 661.85, 7.1, cx1 - 1.0, 662.75, 11.0, Tile(TEX["corrug_silver"], 6.0), faces={"n": "skip", "t": "skip"})
    _sign_panel(mb, "-y", 661.85, 125.0, 133.0, 7.2, 11.0, TEX["carnmenu"])
    for by in (614.5, 636.0, 648.0):
        mb.detail_box_ft(cx0 + 0.8, by, 0.25, 103.5, by + 4.0, 2.9, Tile(TEX["booth"], 4.0), faces={"b": "skip", "w": "skip"})
        mb.detail_box_ft(cx0 + 0.8, by + 4.0, 0.25, 103.5, by + 5.8, 2.6, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip", "w": "skip"})
    # Rear dumpster beside NW exterior wall (clear of 891 nav box x <= 40)
    mb.detail_box_ft(90.0, 657.0, 0.0, 96.5, 662.5, 4.4, Tile(TEX["dumpster"], 6.0), faces={"b": "skip"})

    # Silver corrugated east patio carport canopy (x=146.5..161.5, y=612.0..658.0) + 2 patio tables
    mb.detail_box_ft(146.5, 612.0, 9.6, 161.5, 658.0, 10.0, Tile(TEX["corrug_silver"], 8.0), faces={"w": "skip"})
    for py in (613.0, 635.0, 657.0):
        mb.detail_box_ft(160.8, py - 0.3, 0.0, 161.4, py + 0.3, 9.6, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
    for ty in (616.5, 642.5):
        mb.detail_box_ft(152.5, ty, 2.35, 157.5, ty + 4.5, 2.55, Tile(TEX["wood_tan"], 4.0))
        mb.detail_box_ft(153.2, ty + 0.6, 0.0, 154.0, ty + 1.2, 2.35, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
        mb.detail_box_ft(156.0, ty + 3.3, 0.0, 156.8, ty + 3.9, 2.35, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
        mb.detail_box_ft(151.3, ty + 0.4, 1.35, 152.3, ty + 4.1, 1.55, Tile(TEX["wood_tan"], 4.0))
        mb.detail_box_ft(157.7, ty + 0.4, 1.35, 158.7, ty + 4.1, 1.55, Tile(TEX["wood_tan"], 4.0))

    # Red "MENUDO" feather flag near Belle Terrace corner (x=166, y=587)
    mb.detail_box_ft(166.0, 586.8, 0.0, 166.35, 587.15, 12.2, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip"})
    _sign_panel(mb, "+x", 166.35, 587.2, 590.2, 3.0, 12.0, TEX["sign_menudo_flag"])
    _sign_panel(mb, "-x", 166.0, 587.2, 590.2, 3.0, 12.0, TEX["sign_menudo_flag"])

    mb.spot_ft("int_08_carnitas_diner", 122.0, 628.0, 5.5, yaw=45.0, kind="interior", desc="Carnitas Birria Menudo diner")
    mb.spot_ft("ext_09_belle_carnitas", 155.0, 592.0, 6.0, yaw=135.0, kind="exterior", desc="Belle Terrace & Carnitas corner")

    # ---- Open 891 North Apron + U-Haul / Truck Sales Yard (x=-150..170, y=582..749) ----
    # South Belle Terrace wrought-iron fence w/ two wide open driveways (keeping -120..40, 588..660 clear)
    _fence_line_x(
        mb,
        583.5,
        -148.0,
        96.0,
        0.0,
        6.0,
        TEX["iron_fence"],
        gaps=[(-125.0, -75.0), (-35.0, 48.0)],
        post_step=24.0,
        post_tex=TEX["stucco_white"],
    )
    # Tan CMU divider segments near U-Haul boundary (y=666..668, open driveway x=-66..140)
    mb.detail_box_ft(-86.0, 665.8, 0.0, -68.0, 667.2, 5.5, Tile(TEX["cmu_tan"], 8.0), faces={"b": "skip"})
    mb.detail_box_ft(146.0, 665.8, 0.0, 170.0, 667.2, 5.5, Tile(TEX["cmu_tan"], 8.0), faces={"b": "skip"})

    # Tall rusted double-pole frame with "U-HAUL" + "TRUCK SALES" stacked signs
    _pole_sign(mb, 158.0, 678.0, w=12.0, h=4.2, z_bot=16.5, z_top=20.7, tex_front=TEX["sign_uhaul"], face_axis="x", pole_tex=TEX["rust"])
    _pole_sign(mb, 158.0, 678.0, w=12.0, h=5.0, z_bot=11.0, z_top=16.0, tex_front=TEX["sign_trksale"], face_axis="x", double_pole=False, pole_tex=TEX["rust"])

    # 4 U-Haul box vans & sprinters cleanly spaced in north yard (y=710..736)
    for ux in (-52.0, -14.0, 32.0, 82.0):
        _uhaul_truck(mb, ux, 722.0, facing="S", z0=0.0)

    # ---- Happy Truck Sales Warehouse edge (x=-142.0..-90.0, y=674.0..749.0) ----
    _rect_shell(
        mb,
        "INT Happy Truck Warehouse",
        -142.0,
        674.0,
        -90.0,
        749.0,
        z_floor=0.25,
        z_ceil=15.0,
        tex_ext=TEX["stucco_tan"],
        tex_int=TEX["corrug_silver"],
        tex_floor=TEX["concrete"],
        tex_ceil=TEX["corrug_silver"],
        add_troffers=True,
        thick=0.75,
        doors_s=[(-124.0, -110.0, 11.5, "happy_truck_south_bay")],
        doors_e=[(694.0, 702.0, 9.2, "happy_truck_east_walk")],
        parapet_h=1.2,
        parapet_tex=TEX["corrug_silver"],
        light_level=220.0,
        light_nx=2,
        light_ny=3,
    )
    # Half-raised roll-up door header + warehouse crates/rack/counter (clear of center walk & doors)
    mb.detail_box_ft(-123.9, 673.85, 11.6, -110.1, 674.7, 14.5, Tile(TEX["rollup"], 6.0), faces={"t": "skip"})
    mb.detail_box_ft(-140.8, 684.0, 0.25, -133.5, 712.0, 4.2, Tile(TEX["wood_tan"], 6.0), faces={"b": "skip"})
    mb.detail_box_ft(-140.2, 688.0, 4.2, -134.5, 694.0, 7.2, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(-140.2, 701.0, 4.2, -134.5, 707.0, 7.0, Tile(TEX["stucco_tan"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(-140.8, 734.0, 0.25, -129.0, 744.0, 3.2, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(-140.9, 733.9, 3.2, -128.9, 744.1, 3.38, Tile(TEX["granite"], 4.0), faces={"b": "skip"})
    for wy in (714.0, 728.0):
        mb.cyl_ft(-93.5, wy, 1.0, 0.25, 5.4, sides=10, tex_side=Tile(TEX["tire"], 4.0), tex_top=TEX["tire"], group="detail")
    mb.spot_ft("int_happy_truck_warehouse", -116.0, 725.0, 6.0, yaw=270.0, kind="interior", desc="Inside Happy Truck Warehouse looking south")

    # Distant NW trailers & desert scrub (x=-485..-155)
    for tx, ty in ((-440.0, 712.0), (-340.0, 712.0)):
        mb.detail_box_ft(tx - 24.0, ty - 4.2, 3.0, tx + 24.0, ty + 4.2, 12.8, Tile(TEX["stucco_white"], 10.0))
        mb.detail_box_ft(tx - 20.0, ty - 3.6, 0.0, tx - 14.0, ty + 3.6, 3.0, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
    _fence_line_y(mb, -152.0, 590.0, 745.0, 0.0, 6.0, TEX["chain_fence"], gaps=[(608.0, 636.0)], post_step=24.0)
    _yard_tree(mb, -240.0, 608.0, height=16.0, crown_r=4.2, tex_crown=TEX["tree_2"])
    _yard_tree(mb, -395.0, 618.0, height=18.0, crown_r=4.8, tex_crown=TEX["tree_2"])


# ---------------------------------------------------------------------------
# 2. SW Belle Terrace to Casino: 891 Vacant Lot & West Open Field w/ Pumpjacks
# ---------------------------------------------------------------------------
def _oil_pumpjack(mb: MapBuilder, cx: float, cy: float) -> None:
    """Build an authentic Bakersfield walking-beam oil pumpjack centered at (cx, cy)."""
    mb.detail_box_ft(cx - 8.5, cy - 3.5, 0.0, cx + 8.5, cy + 3.5, 0.6, Tile(TEX["concrete"], 6.0), faces={"b": "skip"})
    # Samson A-frame legs
    mb.detail_box_ft(cx - 1.2, cy - 1.8, 0.6, cx + 1.2, cy + 1.8, 11.0, Tile(TEX["steel_dark"], 6.0), faces={"b": "skip", "t": "skip"})
    # Walking beam & horsehead
    mb.detail_box_ft(cx - 7.5, cy - 0.8, 11.0, cx + 8.5, cy + 0.8, 12.6, Tile(TEX["rust"], 6.0))
    mb.detail_box_ft(cx + 7.2, cy - 0.9, 8.8, cx + 9.2, cy + 0.9, 13.0, Tile(TEX["steel_dark"], 4.0))
    # Crank counterweight block
    mb.detail_box_ft(cx - 7.0, cy - 2.0, 2.0, cx - 3.8, cy + 2.0, 5.8, Tile(TEX["rust"], 4.0))


def _build_891_billboard_lot(mb: MapBuilder) -> None:
    """Build 891 S Union green-mesh vacant dirt lot, billboards, and West Oil Field."""
    # Strictly inside billboard_lot (y=304.5..531.5)
    _pad(mb, -489.75, 304.5, -150.0, 531.75, TEX["weed"])
    _pad(mb, -150.0, 304.5, 171.75, 531.75, TEX["dirt"])

    # 6 ft chain-link fence w/ dark-green privacy mesh along Union (x=170) & Belle Terrace (y=530)
    _fence_line_y(mb, 170.0, 308.0, 530.0, 0.0, 6.0, TEX["green_mesh"], gaps=[(406.0, 424.0)], post_step=16.0)
    _fence_line_x(mb, 530.0, -148.0, 170.0, 0.0, 6.0, TEX["green_mesh"], gaps=[(6.0, 24.0), (-90.0, -74.0)], post_step=16.0)

    # 2-post weathered blank vacant-lot wooden billboard frame (neutral gwc_tpo + gwc_wood, zero casino/redwood text!)
    for sy in (418.0, 434.0):
        mb.detail_box_ft(112.0, sy - 0.4, 0.0, 112.8, sy + 0.4, 10.6, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(111.5, 417.0, 10.2, 113.3, 435.0, 11.0, Tile(TEX["wood_dark"], 4.0))
    mb.detail_box_ft(106.0, 417.0, 10.6, 118.0, 417.6, 11.1, Tile(TEX["wood_dark"], 4.0))
    mb.detail_box_ft(106.0, 434.4, 10.6, 118.0, 435.0, 11.1, Tile(TEX["wood_dark"], 4.0))
    mb.detail_box_ft(112.1, 418.4, 4.6, 112.7, 433.6, 10.2, Tile(TEX["wood_dark"], 4.0), faces={"s": "skip", "n": "skip", "t": "skip"})
    _sign_panel(mb, "+x", 112.7, 418.5, 433.5, 5.0, 9.9, TEX["roof_tpo"])
    _sign_panel(mb, "-x", 112.1, 418.5, 433.5, 5.0, 9.9, TEX["rust"])

    # Black billboard near E Belle Terrace edge (y=515)
    _pole_sign(
        mb,
        126.0,
        515.0,
        w=26.0,
        h=10.5,
        z_bot=12.0,
        z_top=22.5,
        tex_front=TEX["steel_dark"],
        tex_back=TEX["rust"],
        face_axis="y",
    )

    # Distant white semi-trailers & scrub trees in west open field
    for tx, ty in ((-430.0, 462.0), (-365.0, 446.0)):
        mb.detail_box_ft(tx - 24.0, ty - 4.2, 3.0, tx + 24.0, ty + 4.2, 12.8, Tile(TEX["stucco_white"], 10.0))
        mb.detail_box_ft(tx - 20.0, ty - 3.6, 0.0, tx - 14.0, ty + 3.6, 3.0, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})

    # 2 Oil Pumpjacks (NODE 12861504195 & 12861504196) in north west_casino_fringe (x <= -158, y=150..304)
    _pad(mb, -489.75, 148.0, -158.0, 304.25, TEX["weed"])
    _oil_pumpjack(mb, -449.0, 283.7)
    _oil_pumpjack(mb, -445.1, 234.2)

    mb.spot_ft("ext_10_891_greenmesh", 158.0, 415.0, 6.0, yaw=180.0, kind="exterior", desc="891 S Union green-mesh vacant lot")


# ---------------------------------------------------------------------------
# 3. South of Casino along S Union Ave (y=-820..-271.2)
# ---------------------------------------------------------------------------
def _build_ramos_tires(mb: MapBuilder) -> None:
    """Build Ramos Tires & Service shop, open service bays, lift, tire stacks, signs."""
    _pad(mb, -101.75, -341.75, 171.75, -271.25, TEX["asphalt"])

    # Enterable white stucco/metal shop (x=-98.0..24.0, y=-335.0..-285.0)
    rx0, ry0, rx1, ry1 = -98.0, -335.0, 24.0, -285.0
    _rect_shell(
        mb,
        "INT Ramos Tires Shop",
        rx0,
        ry0,
        rx1,
        ry1,
        z_floor=0.25,
        z_ceil=14.5,
        tex_ext=TEX["stucco_white"],
        tex_int=TEX["concrete"],
        tex_floor=TEX["concrete"],
        thick=0.75,
        doors_e=[(-320.0, -304.0, 12.0, "ramos_east_bay"), (-299.0, -291.5, 9.5, "ramos_east_walk")],
        doors_s=[(-26.0, -10.0, 12.0, "ramos_south_bay")],
        doors_w=[(-316.0, -308.0, 9.5, "ramos_west_door")],
        wins_e=[(-331.0, -323.0, 3.2, 8.0)],
        wins_s=[(-80.0, -64.0, 3.2, 8.0)],
        tex_ceil=TEX["corrug_silver"],
        add_troffers=True,
        parapet_h=1.5,
        parapet_tex=TEX["steel_dark"],
        light_level=310.0,
        light_nx=3,
        light_ny=2,
    )
    _barred_square_window(mb, "y", 23.25, -331.0, -323.0, 3.2, 8.0, TEX["steel_dark"], cols=2, rows=2)
    _barred_square_window(mb, "x", -335.0, -80.0, -64.0, 3.2, 8.0, TEX["steel_dark"], cols=3, rows=2)
    # Interior props (tucked cleanly so x=-92..20, y=-330..-288 stays ultra walkable)
    # Tire stacks along north wall (y=-287.5..-285.8)
    for tx in (-84.0, -76.0, -68.0, -40.0):
        mb.cyl_ft(tx, -286.6, 1.0, 0.25, 6.2, sides=10, tex_side=Tile(TEX["tire"], 4.0), tex_top=TEX["tire"], group="detail")
    # Small office desk tucked in NE corner (x=12..22.8, y=-288..-285.8) w/ granite counter top
    mb.detail_box_ft(12.0, -288.0, 0.25, 22.8, -285.8, 3.0, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip", "t": "skip", "n": "skip"})
    mb.detail_box_ft(11.9, -288.1, 3.0, 22.9, -285.7, 3.18, Tile(TEX["granite"], 4.0), faces={"b": "skip", "n": "skip"})
    # 2-post hydraulic lift columns + lift swing arms + overhead equalization beam + red mechanic workbench
    mb.detail_box_ft(-50.5, -327.0, 0.25, -49.5, -326.0, 12.2, Tile(TEX["car_lift"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(-50.5, -294.0, 0.25, -49.5, -293.0, 12.2, Tile(TEX["car_lift"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(-50.4, -326.0, 11.65, -49.6, -294.0, 12.15, Tile(TEX["steel_dark"], 4.0), faces={"s": "skip", "n": "skip"})
    mb.detail_box_ft(-54.2, -326.8, 0.35, -45.8, -326.1, 0.72, Tile(TEX["steel_dark"], 4.0))
    mb.detail_box_ft(-54.2, -293.9, 0.35, -45.8, -293.2, 0.72, Tile(TEX["steel_dark"], 4.0))
    mb.detail_box_ft(-97.2, -304.0, 0.25, -93.0, -290.0, 3.1, Tile(TEX["stucco_red"], 4.0), faces={"b": "skip", "w": "skip"})
    mb.detail_box_ft(-97.2, -304.1, 3.1, -92.8, -289.9, 3.3, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip", "w": "skip"})

    # Shop exterior fascia signage ("RAMOS TIRE & SERVICE", 4:1 aspect) on South & East walls
    _sign_panel(mb, "-y", ry0, -58.0, -42.0, 12.1, 15.8, TEX["sign_ramos"])
    _sign_panel(mb, "+x", rx1, -318.0, -302.0, 12.1, 15.8, TEX["sign_ramos"])

    # Exterior yard: black wrought-iron fence along S Union (x=170) w/ open driveway + "RAMOS NOW OPEN"
    _fence_line_y(mb, 170.0, -340.0, -273.0, 0.0, 6.0, TEX["iron_fence"], gaps=[(-324.0, -298.0)], post_step=16.0)
    _sign_panel(mb, "+x", 170.25, -296.0, -276.0, 1.8, 5.6, TEX["sign_ramos_open"])
    _sign_panel(mb, "-x", 169.75, -296.0, -276.0, 1.8, 5.6, TEX["sign_ramos_open"])

    # Tan wood privacy fence along north border (-272.0) + double-pole "RAMOS TIRE & SERVICE" pylon
    _fence_line_x(mb, -272.2, -98.0, 166.0, 0.0, 6.5, TEX["wood_tan"], gaps=[], post_step=24.0, post_tex=TEX["wood_dark"])
    _pole_sign(mb, 158.0, -277.5, w=12.0, h=4.8, z_bot=15.0, z_top=19.8, tex_front=TEX["sign_ramos"], face_axis="x")

    # Stacked used tire display hugging north fence east yard
    for tx in (44.0, 62.0, 80.0):
        mb.cyl_ft(tx, -276.0, 1.1, 0.0, 5.5, sides=10, tex_side=Tile(TEX["tire"], 4.0), tex_top=TEX["tire"], group="detail")

    mb.spot_ft("int_10_ramos_tires", -20.0, -308.0, 5.5, yaw=180.0, kind="interior", desc="Inside Ramos Tires Shop")


def _build_compas_auto(mb: MapBuilder) -> None:
    """Build Compas Auto Sales (Best DEALS): enterable slate office, canopies, car rows, palms."""
    _pad(mb, -101.75, -585.75, 171.75, -342.25, TEX["asphalt"])

    # Enterable slate blue-grey & white sales office (BLDG 192135092: x=46.5..106.9, y=-511.0..-488.0)
    ox0, oy0, ox1, oy1 = 46.5, -511.0, 106.9, -488.0
    _rect_shell(
        mb,
        "INT Compas Auto Sales",
        ox0,
        oy0,
        ox1,
        oy1,
        z_floor=0.25,
        z_ceil=11.5,
        tex_ext=TEX["stucco_slate"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["tile"],
        thick=0.75,
        doors_n=[(72.0, 81.0, 9.5, "compas_north_porch")],
        doors_s=[(72.0, 81.0, 9.5, "compas_south_door")],
        doors_e=[(-503.0, -495.0, 9.5, "compas_east_union")],
        wins_n=[(52.0, 68.0, 3.2, 8.2), (85.0, 102.0, 3.2, 8.2)],
        wins_s=[(52.0, 68.0, 3.2, 8.2), (85.0, 102.0, 3.2, 8.2)],
        tex_ceil=TEX["ceil_grid"],
        add_troffers=True,
        light_level=310.0,
        light_nx=3,
        light_ny=1,
    )
    _gable_roof(mb, ox0, oy0, ox1, oy1, z_eave=12.2, z_ridge=16.0, tex_roof=TEX["shingle_dark"], tex_gable=TEX["stucco_white"], ridge_along="x")
    # Glazed window bays
    for wx0, wx1 in ((52.0, 68.0), (85.0, 102.0)):
        _barred_square_window(mb, "x", oy1 - 0.75, wx0, wx1, 3.2, 8.2, TEX["stucco_white"], cols=3, rows=2)
        _barred_square_window(mb, "x", oy0, wx0, wx1, 3.2, 8.2, TEX["stucco_white"], cols=3, rows=2)
    # Peaked entry porch on north face (clear around north doorway x=72..81)
    mb.detail_box_ft(69.5, -488.0, 9.6, 83.5, -482.5, 10.1, Tile(TEX["stucco_white"], 6.0), faces={"s": "skip"})
    _gable_roof(mb, 70.0, -488.0, 83.0, -482.8, z_eave=10.3, z_ridge=13.2, tex_roof=TEX["shingle_dark"], tex_gable=TEX["stucco_white"], over=0.4, ridge_along="y")
    mb.detail_box_ft(70.0, -483.4, 0.0, 70.6, -482.8, 9.6, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(82.4, -483.4, 0.0, 83.0, -482.8, 9.6, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip", "t": "skip"})
    # Sales desk, granite top, wall Best DEALS sign & customer seating (clear of center x=76, y=-499)
    mb.detail_box_ft(48.0, -509.5, 0.25, 53.0, -497.0, 2.9, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(47.9, -509.6, 2.9, 53.2, -496.9, 3.1, Tile(TEX["granite"], 4.0), faces={"b": "skip"})
    _sign_panel(mb, "+x", 47.3, -506.0, -495.5, 4.2, 8.4, TEX["sign_bestdeals"])
    mb.detail_box_ft(90.0, -510.0, 0.25, 102.0, -506.8, 1.8, Tile(TEX["leather"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(90.0, -510.1, 1.8, 102.0, -509.0, 3.3, Tile(TEX["leather"], 4.0), faces={"b": "skip"})

    # 3 Main Metal Carport Canopies + 3 OSM Compas lot canopies (192135105/126/097, open underneath!)
    _carport_canopy(mb, -88.0, -396.0, -22.0, -372.0, z_roof=10.5)
    _carport_canopy(mb, -88.0, -562.0, -22.0, -538.0, z_roof=10.5)
    _carport_canopy(mb, 122.0, -456.0, 162.0, -382.0, z_roof=10.5)
    _carport_canopy(mb, 19.6, -463.8, 40.2, -440.4, z_roof=9.8)
    _carport_canopy(mb, 84.3, -484.0, 106.7, -463.3, z_roof=9.8)
    _carport_canopy(mb, 75.3, -534.9, 98.1, -517.3, z_roof=9.8)

    # Black wrought-iron perimeter fence w/ wide driveways + 5 Canary/Queen Palms
    _fence_line_y(mb, 170.0, -584.0, -344.0, 0.0, 5.5, TEX["iron_fence"], gaps=[(-382.0, -356.0), (-486.0, -460.0), (-578.0, -556.0)], post_step=18.0)
    _fence_line_x(mb, -584.5, -100.0, 168.0, 0.0, 5.5, TEX["iron_fence"], gaps=[(-20.0, 10.0), (110.0, 134.0)], post_step=18.0)
    for py in (-350.0, -408.0, -454.0, -520.0, -574.0):
        _palm_tree(mb, 165.5, py, height=22.0)

    # Neatly spaced low-poly used car rows (>=6 ft / >=72u aisles between every car & wall)
    car_spots = [
        (-74.0, -384.0, "y", 0),
        (-52.0, -384.0, "y", 1),
        (-30.0, -384.0, "y", 2),
        (-74.0, -452.0, "x", 3),
        (-36.0, -452.0, "x", 4),
        (10.0, -412.0, "y", 0),
        (32.0, -412.0, "y", 5),
        (-74.0, -550.0, "y", 2),
        (-52.0, -550.0, "y", 1),
        (-30.0, -550.0, "y", 0),
        (142.0, -412.0, "x", 3),
        (142.0, -438.0, "x", 4),
    ]
    for cx, cy, ax, cidx in car_spots:
        _parked_car(mb, cx, cy, CAR_COLORS[cidx % len(CAR_COLORS)], axis=ax)

    # White sidewalk bench, Best DEALS / STOP / ONE WAY signs & circular corner sign frame
    mb.detail_box_ft(160.5, -450.0, 0.0, 163.5, -443.0, 1.8, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(162.8, -450.0, 1.8, 163.5, -443.0, 3.4, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip"})
    _pole_sign(mb, 158.0, -504.0, w=10.5, h=5.5, z_bot=12.0, z_top=17.5, tex_front=TEX["sign_bestdeals"], face_axis="x")
    # STOP + ONE WAY post near south driveway
    mb.detail_box_ft(156.0, -546.0, 0.0, 156.5, -545.5, 9.5, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip"})
    _sign_panel(mb, "+x", 156.5, -547.8, -543.8, 6.2, 9.4, TEX["sign_stop"])
    _sign_panel(mb, "+x", 156.5, -547.8, -543.8, 4.0, 5.8, TEX["sign_oneway"])
    # Circular-look octagonal corner sign frame at SE Compas corner
    _pole_sign(mb, 156.0, -574.0, w=8.0, h=8.0, z_bot=9.0, z_top=17.0, tex_front=TEX["sign_bestdeals"], face_axis="x", double_pole=False)

    mb.spot_ft("int_11_compas_auto", 76.0, -499.0, 5.5, yaw=180.0, kind="interior", desc="Inside Compas Auto Sales Office")
    mb.spot_ft("ext_13_ramos_compas", 169.0, -365.0, 6.5, yaw=172.0, kind="exterior", desc="Open S Union apron between Ramos Tires & Compas Auto")


def _motel_bed_set(
    mb: MapBuilder,
    x0: float,
    y0: float,
    z_floor: float,
    head_side: str = "n",
) -> None:
    """Place a low-poly motel queen bed, headboard, and nightstand tucked clear of doorways."""
    if head_side in ("n", "s"):
        bw, bl = 5.4, 6.8
        # Bed + headboard
        mb.detail_box_ft(x0, y0, z_floor, x0 + bw, y0 + bl, z_floor + 1.85, Fit(TEX["bed"]), faces={"b": "skip"})
        hb_y0, hb_y1 = (y0 + bl, y0 + bl + 0.35) if head_side == "n" else (y0 - 0.35, y0)
        mb.detail_box_ft(x0 - 0.15, hb_y0, z_floor, x0 + bw + 0.15, hb_y1, z_floor + 3.6, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip"})
        ns_y0, ns_y1 = (y0 + bl - 2.2, y0 + bl) if head_side == "n" else (y0, y0 + 2.2)
        mb.detail_box_ft(x0 + bw + 0.4, ns_y0, z_floor, x0 + bw + 2.4, ns_y1, z_floor + 2.1, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip"})
    else:
        bw, bl = 6.8, 5.4
        mb.detail_box_ft(x0, y0, z_floor, x0 + bw, y0 + bl, z_floor + 1.85, Fit(TEX["bed"]), faces={"b": "skip"})
        hb_x0, hb_x1 = (x0 - 0.35, x0) if head_side == "w" else (x0 + bw, x0 + bw + 0.35)
        mb.detail_box_ft(hb_x0, y0 - 0.15, z_floor, hb_x1, y0 + bl + 0.15, z_floor + 3.6, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip"})
        ns_x0, ns_x1 = (x0, x0 + 2.2) if head_side == "w" else (x0 + bw - 2.2, x0 + bw)
        mb.detail_box_ft(ns_x0, y0 + bl + 0.4, z_floor, ns_x1, y0 + bl + 2.4, z_floor + 2.1, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip"})


def _deck_slab(mb: MapBuilder, x0: float, y0: float, x1: float, y1: float, z0: float = 10.50, z1: float = 11.20) -> None:
    """Intermediate 1F ceiling / 2F floor slab with gwc_ceil2x4 acoustic underside + carpet top."""
    faces = {
        "b": Tile(TEX["ceil_grid"], 8.0),
        "t": Tile(TEX["motel_cpt"], 8.0),
        "n": Tile(TEX["stucco_cream"], 8.0),
        "s": Tile(TEX["stucco_cream"], 8.0),
        "e": Tile(TEX["stucco_cream"], 8.0),
        "w": Tile(TEX["stucco_cream"], 8.0),
    }
    mb.detail_box_ft(x0, y0, z0, x1, y1, z1, TEX["stucco_cream"], faces=faces)


def _build_super8_motel(mb: MapBuilder) -> None:
    """Build Super 8 by Wyndham: enterable 1F lobby + fireplace chimney + 2F U/L motel wing w/ stairs."""
    _pad(mb, -101.75, -745.75, 171.75, -586.25, TEX["asphalt"])

    # ---- Front 1-Storey White-Stucco Lobby (x=46.0..142.0, y=-653.5..-591.5) ----
    lx0, ly0, lx1, ly1 = 46.0, -653.5, 142.0, -591.5
    _rect_shell(
        mb,
        "INT Super 8 Lobby",
        lx0,
        ly0,
        lx1,
        ly1,
        z_floor=0.25,
        z_ceil=11.5,
        tex_ext=TEX["stucco_white"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["tile"],
        tex_ceil=TEX["ceil_grid"],
        add_troffers=True,
        thick=0.75,
        doors_e=[(-644.0, -634.0, 9.5, "super8_lobby_east")],
        doors_w=[(-628.0, -618.0, 9.5, "super8_lobby_west")],
        doors_n=[(86.0, 95.0, 9.5, "super8_lobby_north")],
        wins_e=[(-615.0, -599.0, 3.2, 8.4)],
        wins_n=[(55.0, 78.0, 3.2, 8.4), (104.0, 132.0, 3.2, 8.4)],
        wins_s=[(56.0, 70.0, 3.2, 8.4), (82.0, 96.0, 3.2, 8.4), (112.0, 126.0, 3.2, 8.4)],
        light_level=320.0,
        light_nx=3,
        light_ny=2,
    )
    _hip_roof(mb, lx0, ly0, lx1, ly1, z_eave=12.15, z_ridge=18.0, tex_roof=TEX["shingle_brown"])
    # Tall protruding white stucco exterior fireplace chimney on east facade
    mb.detail_box_ft(142.0, -628.5, 0.0, 146.0, -619.5, 22.0, Tile(TEX["stucco_white"], 8.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(141.8, -628.8, 22.0, 146.3, -619.2, 22.6, Tile(TEX["brick"], 4.0))
    # Security-barred multi-pane white square windows on E, N & S facades (zero gwc_security)
    _barred_square_window(mb, "y", 141.25, -615.0, -599.0, 3.2, 8.4, TEX["stucco_white"], cols=3, rows=2)
    _barred_square_window(mb, "x", -592.25, 55.0, 78.0, 3.2, 8.4, TEX["stucco_white"], cols=4, rows=2)
    _barred_square_window(mb, "x", -592.25, 104.0, 132.0, 3.2, 8.4, TEX["stucco_white"], cols=5, rows=2)
    for sx0, sx1 in ((56.0, 70.0), (82.0, 96.0), (112.0, 126.0)):
        _barred_square_window(mb, "x", -653.5, sx0, sx1, 3.2, 8.4, TEX["stucco_white"], cols=3, rows=2)
    # Lobby reception desk, granite counter top, wall Super 8 plaque, seating & vending alcove (clear of x=94, y=-622)
    mb.detail_box_ft(48.0, -603.0, 0.25, 64.0, -594.0, 3.5, Tile(TEX["wood_tan"], 6.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(47.8, -603.2, 3.5, 64.2, -593.8, 3.72, Tile(TEX["granite"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(53.0, -599.2, 3.72, 55.8, -597.4, 4.9, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip"})
    _sign_panel(mb, "+x", 46.85, -612.0, -604.0, 4.4, 9.2, TEX["sign_super8"])
    mb.detail_box_ft(62.0, -652.0, 0.25, 76.0, -648.0, 1.85, Tile(TEX["leather"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(62.0, -652.4, 1.85, 76.0, -651.0, 3.4, Tile(TEX["leather"], 4.0), faces={"b": "skip"})
    mb.detail_box_ft(124.0, -652.4, 0.25, 135.0, -648.8, 6.2, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip"})

    # Iron fence along north edge w/ open gate + iconic 27 ft "Super 8" pole sign
    _fence_line_x(mb, -587.5, -100.0, 168.0, 0.0, 5.5, TEX["iron_fence"], gaps=[(106.0, 138.0), (18.0, 42.0)], post_step=18.0)
    _pole_sign(mb, 160.0, -616.0, w=11.0, h=11.0, z_bot=16.0, z_top=27.0, tex_front=TEX["sign_super8"], face_axis="x")

    # ---- Rear 2-Storey Stucco U/L Motel Wing (x=-97.0..22.0, y=-729.0..-592.0) ----
    # Shared structural elevations: 1F floor 0.25 -> 1F ceil 10.50 -> 2F floor 11.20 -> 2F ceil 21.40 -> roof 24.5
    # 1F & 2F West Spine (x=-97..-62, y=-695..-625) — linked via interior doors at x=-84..-76 to N & S wings
    _rect_shell(
        mb,
        "INT Super 8 West 1F",
        -97.0,
        -695.0,
        -62.0,
        -625.0,
        z_floor=0.25,
        z_ceil=10.50,
        tex_ext=TEX["stucco_cream"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["motel_cpt"],
        tex_ceil=TEX["ceil_grid"],
        thick=0.75,
        doors_n=[(-84.0, -76.0, 9.2, "s8_w1f_to_north")],
        doors_s=[(-84.0, -76.0, 9.2, "s8_w1f_to_south")],
        doors_e=[(-664.0, -656.0, 9.2, "s8_w1f_courtyard")],
        doors_w=[(-664.0, -656.0, 9.2, "s8_w1f_delaware")],
        wins_e=[(-682.0, -670.0, 3.2, 7.8), (-646.0, -634.0, 3.2, 7.8)],
        build_ceil=False,
        light_level=280.0,
        light_nx=1,
        light_ny=2,
    )
    _rect_shell(
        mb,
        "INT Super 8 West 2F",
        -97.0,
        -695.0,
        -62.0,
        -625.0,
        z_floor=11.20,
        z_ceil=21.40,
        tex_ext=TEX["stucco_cream"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["motel_cpt"],
        tex_ceil=TEX["ceil_grid"],
        add_troffers=True,
        thick=0.75,
        doors_n=[(-84.0, -76.0, 20.1, "s8_w2f_to_north")],
        doors_s=[(-84.0, -76.0, 20.1, "s8_w2f_to_south")],
        doors_e=[(-664.0, -656.0, 20.1, "s8_w2f_balcony")],
        wins_e=[(-682.0, -670.0, 14.2, 18.6), (-646.0, -634.0, 14.2, 18.6)],
        build_floor=False,
        ceil_top=22.0,
        light_level=280.0,
        light_nx=1,
        light_ny=2,
    )
    # 2F floor / 1F ceiling deck slab for West Spine + 1F/2F queen bed sets
    _deck_slab(mb, -97.0, -695.0, -62.0, -625.0)
    mb.flush_panel_ft(-81.5, -646.0, 10.45, -77.5, -642.5, 10.50, {"b": Fit(TEX["troffer"])}, group="illus")
    mb.flush_panel_ft(-81.5, -678.0, 10.45, -77.5, -674.5, 10.50, {"b": Fit(TEX["troffer"])}, group="illus")
    for zf in (0.25, 11.20):
        _motel_bed_set(mb, -95.8, -646.0, zf, head_side="w")
        _motel_bed_set(mb, -95.8, -686.0, zf, head_side="w")
    _gable_roof(mb, -97.0, -695.0, -62.0, -625.0, z_eave=22.0, z_ridge=24.8, tex_roof=TEX["shingle_brown"], tex_gable=TEX["stucco_cream"], ridge_along="y")

    # North Return Wing (x=-97..22, y=-625..-592)
    _rect_shell(
        mb,
        "INT Super 8 North 1F",
        -97.0,
        -625.0,
        22.0,
        -592.0,
        z_floor=0.25,
        z_ceil=10.50,
        tex_ext=TEX["stucco_cream"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["motel_cpt"],
        tex_ceil=TEX["ceil_grid"],
        thick=0.75,
        doors_s=[(-84.0, -76.0, 9.2, "s8_n1f_to_west"), (-34.0, -25.0, 9.2, "s8_n1f_courtyard")],
        doors_e=[(-612.0, -604.0, 9.2, "s8_n1f_lobby")],
        wins_s=[(-54.0, -40.0, 3.2, 7.8), (-10.0, 6.0, 3.2, 7.8)],
        build_ceil=False,
        light_level=280.0,
        light_nx=2,
        light_ny=1,
    )
    _rect_shell(
        mb,
        "INT Super 8 North 2F",
        -97.0,
        -625.0,
        22.0,
        -592.0,
        z_floor=11.20,
        z_ceil=21.40,
        tex_ext=TEX["stucco_cream"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["motel_cpt"],
        tex_ceil=TEX["ceil_grid"],
        add_troffers=True,
        thick=0.75,
        doors_s=[(-84.0, -76.0, 20.1, "s8_n2f_to_west"), (-34.0, -25.0, 20.1, "s8_n2f_balcony")],
        wins_s=[(-54.0, -40.0, 14.2, 18.6), (-10.0, 6.0, 14.2, 18.6)],
        build_floor=False,
        ceil_top=22.0,
        light_level=280.0,
        light_nx=2,
        light_ny=1,
    )
    _deck_slab(mb, -97.0, -625.0, 22.0, -592.0)
    mb.flush_panel_ft(-58.0, -610.0, 10.45, -54.0, -607.5, 10.50, {"b": Fit(TEX["troffer"])}, group="illus")
    mb.flush_panel_ft(-12.0, -610.0, 10.45, -8.0, -607.5, 10.50, {"b": Fit(TEX["troffer"])}, group="illus")
    for zf in (0.25, 11.20):
        _motel_bed_set(mb, -66.0, -600.0, zf, head_side="n")
        _motel_bed_set(mb, -10.0, -600.0, zf, head_side="n")
    _gable_roof(mb, -97.0, -625.0, 22.0, -592.0, z_eave=22.0, z_ridge=24.8, tex_roof=TEX["shingle_brown"], tex_gable=TEX["stucco_cream"], ridge_along="x")

    # South Return Wing (x=-97..22, y=-729..-695)
    _rect_shell(
        mb,
        "INT Super 8 South 1F",
        -97.0,
        -729.0,
        22.0,
        -695.0,
        z_floor=0.25,
        z_ceil=10.50,
        tex_ext=TEX["stucco_cream"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["motel_cpt"],
        tex_ceil=TEX["ceil_grid"],
        thick=0.75,
        doors_n=[(-84.0, -76.0, 9.2, "s8_s1f_to_west"), (-34.0, -25.0, 9.2, "s8_s1f_courtyard")],
        doors_s=[(-34.0, -25.0, 9.2, "s8_s1f_amador")],
        wins_n=[(-54.0, -40.0, 3.2, 7.8), (-10.0, 6.0, 3.2, 7.8)],
        build_ceil=False,
        light_level=280.0,
        light_nx=2,
        light_ny=1,
    )
    _rect_shell(
        mb,
        "INT Super 8 South 2F",
        -97.0,
        -729.0,
        22.0,
        -695.0,
        z_floor=11.20,
        z_ceil=21.40,
        tex_ext=TEX["stucco_cream"],
        tex_int=TEX["drywall"],
        tex_floor=TEX["motel_cpt"],
        tex_ceil=TEX["ceil_grid"],
        add_troffers=True,
        thick=0.75,
        doors_n=[(-84.0, -76.0, 20.1, "s8_s2f_to_west"), (-34.0, -25.0, 20.1, "s8_s2f_balcony")],
        wins_n=[(-54.0, -40.0, 14.2, 18.6), (-10.0, 6.0, 14.2, 18.6)],
        build_floor=False,
        ceil_top=22.0,
        light_level=280.0,
        light_nx=2,
        light_ny=1,
    )
    # Motel room window blinds (west + courtyard wings) & rear service dumpster
    for wy in (-682.0, -646.0):
        _add_window_glazing(mb, "y", -62.75, wy, wy + 12.0, 3.2, 7.8, TEX["win_motel"])
        _add_window_glazing(mb, "y", -62.75, wy, wy + 12.0, 14.2, 18.6, TEX["win_motel"])
    for wx0, wx1 in ((-54.0, -40.0), (-10.0, 6.0)):
        _add_window_glazing(mb, "x", -625.0, wx0, wx1, 3.2, 7.8, TEX["win_motel"])
        _add_window_glazing(mb, "x", -625.0, wx0, wx1, 14.2, 18.6, TEX["win_motel"])
        _add_window_glazing(mb, "x", -695.75, wx0, wx1, 3.2, 7.8, TEX["win_motel"])
        _add_window_glazing(mb, "x", -695.75, wx0, wx1, 14.2, 18.6, TEX["win_motel"])
    mb.detail_box_ft(-96.0, -740.0, 0.0, -89.0, -733.5, 4.4, Tile(TEX["dumpster"], 6.0), faces={"b": "skip"})
    _deck_slab(mb, -97.0, -729.0, 22.0, -695.0)
    mb.flush_panel_ft(-58.0, -714.0, 10.45, -54.0, -711.5, 10.50, {"b": Fit(TEX["troffer"])}, group="illus")
    mb.flush_panel_ft(-12.0, -714.0, 10.45, -8.0, -711.5, 10.50, {"b": Fit(TEX["troffer"])}, group="illus")
    for zf in (0.25, 11.20):
        _motel_bed_set(mb, -66.0, -727.8, zf, head_side="s")
        _motel_bed_set(mb, -10.0, -727.8, zf, head_side="s")
    _gable_roof(mb, -97.0, -729.0, 22.0, -695.0, z_eave=22.0, z_ridge=24.8, tex_roof=TEX["shingle_brown"], tex_gable=TEX["stucco_cream"], ridge_along="x")

    # Continuous U-shaped 2F Exterior Balcony Walkway (7.5 ft wide, z=10.50..11.20, func_detail)
    mb.detail_box_ft(-62.0, -695.0, 10.50, -54.5, -625.0, 11.20, Tile(TEX["concrete"], 8.0), faces={"w": "skip"})
    mb.detail_box_ft(-54.5, -632.5, 10.50, 22.0, -625.0, 11.20, Tile(TEX["concrete"], 8.0), faces={"w": "skip", "n": "skip"})
    mb.detail_box_ft(-54.5, -695.0, 10.50, 22.0, -687.5, 11.20, Tile(TEX["concrete"], 8.0), faces={"w": "skip", "s": "skip"})
    # Balcony & cantilevered landing support columns (including x=21.65 outer stair landing corners!)
    for bx, by in (
        (-55.0, -632.0),
        (-20.0, -632.0),
        (16.0, -632.0),
        (-55.0, -688.0),
        (-20.0, -688.0),
        (16.0, -688.0),
        (21.65, -632.85),
        (21.65, -639.15),
        (21.65, -680.85),
        (21.65, -687.15),
    ):
        mb.detail_box_ft(bx - 0.35, by - 0.35, 0.0, bx + 0.35, by + 0.35, 10.50, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})

    # Balcony + full stair landing perimeter guardrails (continuous around x=12..22 outer edges!)
    _fence_line_y(mb, -54.7, -687.5, -632.5, 11.20, 14.50, TEX["slat_rail"], post_step=12.0)
    _fence_line_x(mb, -632.3, -54.5, 12.0, 11.20, 14.50, TEX["slat_rail"], post_step=12.0)
    _fence_line_x(mb, -687.7, -54.5, 12.0, 11.20, 14.50, TEX["slat_rail"], post_step=12.0)
    _fence_line_y(mb, 21.85, -639.35, -625.25, 11.20, 14.50, TEX["slat_rail"], post_step=7.05)
    _fence_line_x(mb, -639.35, 12.0, 21.75, 11.20, 14.50, TEX["slat_rail"], post_step=9.75)
    _fence_line_y(mb, 21.85, -694.75, -680.65, 11.20, 14.50, TEX["slat_rail"], post_step=7.05)
    _fence_line_x(mb, -680.65, 12.0, 21.75, 11.20, 14.50, TEX["slat_rail"], post_step=9.75)

    # Walkable exterior stairs + sloped steel handrails up to South & North 2F Balcony landings
    # South stair rises West->East from x=-12 (ground z=0.0) to x=+12 (landing z=11.20) along y=-687.5..-680.5
    mb.detail_box_ft(12.0, -687.5, 10.50, 22.0, -680.5, 11.20, Tile(TEX["concrete"], 8.0), faces={"s": "skip", "w": "skip"})
    mb.add_stairs("s8_south_stair", "x", -12.0, 12.0, -687.5, -680.5, 0.0, 11.20, 9, TEX["concrete"], TEX["steel_dark"], add_clip_ramp=True)
    # North stair rises West->East from x=-12 (ground z=0.0) to x=+12 (landing z=11.20) along y=-639.5..-632.5
    mb.detail_box_ft(12.0, -639.5, 10.50, 22.0, -632.5, 11.20, Tile(TEX["concrete"], 8.0), faces={"n": "skip", "w": "skip"})
    mb.add_stairs("s8_north_stair", "x", -12.0, 12.0, -639.5, -632.5, 0.0, 11.20, 9, TEX["concrete"], TEX["steel_dark"], add_clip_ramp=True)
    for hy in (-687.38, -680.62, -639.38, -632.62):
        mb.slab_ramp_xft(-12.0, 12.0, hy - 0.11, hy + 0.11, 3.1, 14.3, Tile(TEX["steel_dark"], 4.0), thick_ft=0.20, group="detail")
        for hx, hz in ((-11.8, 3.05), (-4.0, 6.75), (4.0, 10.45), (11.8, 14.15)):
            mb.detail_box_ft(hx - 0.10, hy - 0.10, max(0.0, hz - 3.05), hx + 0.10, hy + 0.10, hz, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})

    # Courtyard ground lights & interior/exterior spots
    mb.light_ft(-24.0, -660.0, 9.5, light=260.0)
    mb.spot_ft("int_14_super8_lobby", 94.0, -622.0, 5.5, yaw=180.0, kind="interior", desc="Inside Super 8 Lobby")
    mb.spot_ft("int_super8_balcony_2f", -58.0, -660.0, 16.0, yaw=0.0, kind="interior", desc="Super 8 2F Balcony overlooking courtyard")
    mb.spot_ft("ext_15_super8_motel", 160.0, -675.0, 7.5, yaw=155.0, kind="exterior", desc="Super 8 front lobby & diamond sign")


# ---------------------------------------------------------------------------
# 4. South Lot & Eucalyptus Windbreak (y=-820..-786)
# ---------------------------------------------------------------------------
def _build_south_amador_windbreak(mb: MapBuilder) -> None:
    """Build open south dirt yard and tall eucalyptus windbreak row south of Amador Ave."""
    _pad(mb, -489.75, -819.75, 171.75, -786.25, TEX["dirt"])
    for ex in range(-450, 160, 58):
        _yard_tree(mb, float(ex), -803.0, height=30.0, crown_r=6.5, tex_crown=TEX["tree_2"])


# ---------------------------------------------------------------------------
# 5. West Residential Neighborhood (Delaware, Trinity, Mariposa, Amador)
# ---------------------------------------------------------------------------
def _ranch_exterior(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    tex_wall: str,
    tex_roof: Optional[str] = None,
    height: float = 10.5,
    ridge_h: float = 3.5,
    ridge_along: str = "x",
    carport_side: Optional[str] = None,
    cooler_pos: Tuple[float, float] = (0.35, 0.5),
    door_side: str = "x+",
) -> None:
    """Place a lightweight exterior 1950s-60s Bakersfield ranch house + optional steel carport."""
    r_tex = tex_roof or TEX["shingle_brown"]
    mb.detail_box_ft(x0, y0, 0.0, x1, y1, height, Tile(tex_wall, 8.0), faces={"b": "skip", "t": "skip"})
    _gable_roof(mb, x0, y0, x1, y1, z_eave=height, z_ridge=height + ridge_h, tex_roof=r_tex, tex_gable=tex_wall, ridge_along=ridge_along)
    # Swamp cooler perched cleanly on roof slope
    cx = x0 + (x1 - x0) * cooler_pos[0]
    cy = y0 + (y1 - y0) * cooler_pos[1]
    _swamp_cooler(mb, cx, cy, height + ridge_h * 0.45)
    # Street-facing framed window (trim wall-back hidden faces) + sleek rear glazing decal
    wtile = Tile(TEX["stucco_white"], 4.0)
    if door_side == "y+":
        _sign_panel(mb, "+y", y1, x0 + 4.0, x0 + 12.0, 3.2, 7.2, TEX["win_house"])
        mb.flush_panel_ft(x0 + 7.9, y1 + 0.08, 3.2, x0 + 8.1, y1 + 0.16, 7.2, {"n": wtile, "e": wtile, "w": wtile}, group="illus")
        mb.flush_panel_ft(x0 + 3.9, y1, 3.04, x0 + 12.1, y1 + 0.16, 3.2, {"n": wtile, "e": wtile, "w": wtile, "t": wtile, "b": wtile}, group="illus")
        _sign_panel(mb, "-y", y0, x0 + 4.0, x0 + 12.0, 3.2, 7.2, TEX["win_house"])
    else:
        _sign_panel(mb, "-y", y0, x0 + 4.0, x0 + 12.0, 3.2, 7.2, TEX["win_house"])
        mb.flush_panel_ft(x0 + 7.9, y0 - 0.16, 3.2, x0 + 8.1, y0 - 0.08, 7.2, {"s": wtile, "e": wtile, "w": wtile}, group="illus")
        mb.flush_panel_ft(x0 + 3.9, y0 - 0.16, 3.04, x0 + 12.1, y0, 3.2, {"s": wtile, "e": wtile, "w": wtile, "t": wtile, "b": wtile}, group="illus")
        _sign_panel(mb, "+y", y1, x0 + 4.0, x0 + 12.0, 3.2, 7.2, TEX["win_house"])
    if door_side == "y-":
        dx = max(x0 + 14.0, 0.5 * (x0 + x1) - 2.0)
        _sign_panel(mb, "-y", y0, dx, dx + 4.0, 0.4, 7.4, TEX["door_wood"])
    elif door_side == "y+":
        dx = max(x0 + 14.0, 0.5 * (x0 + x1) - 2.0)
        _sign_panel(mb, "+y", y1, dx, dx + 4.0, 0.4, 7.4, TEX["door_wood"])
    elif door_side == "x-":
        _sign_panel(mb, "-x", x0, y0 + 5.0, y0 + 9.0, 0.4, 7.4, TEX["door_wood"])
    else:
        _sign_panel(mb, "+x", x1, y0 + 5.0, y0 + 9.0, 0.4, 7.4, TEX["door_wood"])

    if carport_side == "w":
        _carport_canopy(mb, x0 - 13.0, y0 + 2.0, x0, y1 - 2.0, z_roof=8.5, tex_roof=TEX["corrug_silver"], attach_side="e")
    elif carport_side == "e":
        _carport_canopy(mb, x1, y0 + 2.0, x1 + 13.0, y1 - 2.0, z_roof=8.5, tex_roof=TEX["corrug_silver"], attach_side="w")


def _safe_wall_wins(
    s0: float,
    s1: float,
    doors: Sequence[Tuple[float, float, float, str]],
    b0: float = 3.2,
    b1: float = 7.4,
) -> List[Tuple[float, float, float, float]]:
    """Return 1-2 clean 8 ft window spans along a wall segment, strictly clear of doors."""
    out: List[Tuple[float, float, float, float]] = []
    for cand0, cand1 in ((s0 + 4.5, s0 + 12.5), (s1 - 12.5, s1 - 4.5)):
        if cand1 >= s1 - 2.0 or cand0 <= s0 + 2.0 or cand1 - cand0 < 5.0:
            continue
        if any(cand0 <= d[1] + 2.0 and cand1 >= d[0] - 2.0 for d in doors):
            continue
        if any(cand0 <= prev[1] + 2.5 and cand1 >= prev[0] - 2.5 for prev in out):
            continue
        out.append((cand0, cand1, b0, b1))
    return out


def _furnish_house_interior(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    z_floor: float,
    z_ceil: float,
    doors_n: Sequence[Tuple[float, float, float, str]],
    doors_s: Sequence[Tuple[float, float, float, str]],
    doors_e: Sequence[Tuple[float, float, float, str]],
    doors_w: Sequence[Tuple[float, float, float, str]],
    part_y: Optional[float] = None,
) -> None:
    """Furnish an enterable ranch house cleanly along outer corners & accent credenzas."""
    ix0, iy0 = x0 + 0.75, y0 + 0.75
    ix1, iy1 = x1 - 0.75, y1 - 0.75
    cx, cy = 0.5 * (ix0 + ix1), 0.5 * (iy0 + iy1)

    def _clear(bx0: float, by0: float, bx1: float, by1: float) -> bool:
        for d0, d1, _, _ in doors_n:
            if bx0 <= d1 + 3.5 and bx1 >= d0 - 3.5 and by1 >= iy1 - 5.5:
                return False
        for d0, d1, _, _ in doors_s:
            if bx0 <= d1 + 3.5 and bx1 >= d0 - 3.5 and by0 <= iy0 + 5.5:
                return False
        for d0, d1, _, _ in doors_e:
            if by0 <= d1 + 3.5 and by1 >= d0 - 3.5 and bx1 >= ix1 - 5.5:
                return False
        for d0, d1, _, _ in doors_w:
            if by0 <= d1 + 3.5 and by1 >= d0 - 3.5 and bx0 <= ix0 + 5.5:
                return False
        return True

    # Optional interior drywall partition with wide (>= 10 ft x 8.5 ft) central framed opening
    if part_y is not None:
        gap_half = min(8.0, (ix1 - ix0) * 0.24)
        mx = 0.5 * (ix0 + ix1)
        stub_w0, stub_w1 = ix0, mx - gap_half
        stub_e0, stub_e1 = mx + gap_half, ix1
        if stub_w1 - stub_w0 > 2.0:
            mb.detail_box_ft(stub_w0, part_y - 0.3, z_floor, stub_w1, part_y + 0.3, z_ceil, Tile(TEX["drywall"], 8.0), faces={"b": "skip", "t": "skip", "w": "skip"})
        if stub_e1 - stub_e0 > 2.0:
            mb.detail_box_ft(stub_e0, part_y - 0.3, z_floor, stub_e1, part_y + 0.3, z_ceil, Tile(TEX["drywall"], 8.0), faces={"b": "skip", "t": "skip", "e": "skip"})
        mb.detail_box_ft(stub_w1, part_y - 0.3, 8.85, stub_e0, part_y + 0.3, z_ceil, Tile(TEX["drywall"], 8.0), faces={"t": "skip", "w": "skip", "e": "skip"})

    # Central low area rug flush over floor (adds warmth without affecting Hull-1 movement)
    mb.flush_panel_ft(cx - 5.5, cy - 4.5, z_floor, cx + 5.5, cy + 4.5, z_floor + 0.04, {"t": Fit(TEX["motel_cpt"])}, group="illus")

    # NW kitchenette wood cabinet counter + granite top
    if _clear(ix0, iy1 - 9.5, ix0 + 3.0, iy1):
        mb.detail_box_ft(ix0, iy1 - 9.5, z_floor, ix0 + 2.6, iy1, z_floor + 3.0, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip", "t": "skip", "n": "skip", "w": "skip"})
        mb.detail_box_ft(ix0, iy1 - 9.6, z_floor + 3.0, ix0 + 2.8, iy1, z_floor + 3.18, Tile(TEX["granite"], 4.0), faces={"b": "skip", "n": "skip", "w": "skip"})

    # NE living room leather sofa + coffee table (or SE fallback if NE blocked)
    if _clear(ix1 - 10.5, iy1 - 4.2, ix1, iy1):
        mb.detail_box_ft(ix1 - 9.5, iy1 - 3.4, z_floor, ix1 - 0.5, iy1, z_floor + 1.65, Tile(TEX["leather"], 4.0), faces={"b": "skip", "n": "skip"})
        mb.detail_box_ft(ix1 - 9.5, iy1 - 1.0, z_floor + 1.65, ix1 - 0.5, iy1, z_floor + 3.1, Tile(TEX["leather"], 4.0), faces={"b": "skip", "n": "skip"})
        mb.detail_box_ft(ix1 - 8.0, iy1 - 7.5, z_floor, ix1 - 3.5, iy1 - 5.2, z_floor + 1.45, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip"})
    elif _clear(ix1 - 3.6, iy1 - 11.0, ix1, iy1 - 1.5):
        mb.detail_box_ft(ix1 - 3.4, iy1 - 10.5, z_floor, ix1, iy1 - 1.5, z_floor + 1.65, Tile(TEX["leather"], 4.0), faces={"b": "skip", "e": "skip"})
        mb.detail_box_ft(ix1 - 1.0, iy1 - 10.5, z_floor + 1.65, ix1, iy1 - 1.5, z_floor + 3.1, Tile(TEX["leather"], 4.0), faces={"b": "skip", "e": "skip"})

    # East side console credenza & framed art visible along main sightlines when clear of doors/windows
    for c_y0 in (cy + 5.0, cy + 8.5):
        if not doors_e and c_y0 > cy + 5.1:
            break
        if len(doors_e) == 1 and c_y0 > cy + 5.1 and (iy1 - iy0) > 70.0:
            # 2F Duplex East wall is glazed beside the door; avoid blocking front windows
            continue
        if _clear(ix1 - 2.6, c_y0, ix1, c_y0 + 7.5):
            mb.detail_box_ft(ix1 - 2.4, c_y0 + 0.5, z_floor, ix1, c_y0 + 7.0, z_floor + 2.7, Tile(TEX["wood_tan"], 4.0), faces={"b": "skip", "t": "skip", "e": "skip"})
            mb.detail_box_ft(ix1 - 2.5, c_y0 + 0.4, z_floor + 2.7, ix1, c_y0 + 7.1, z_floor + 2.86, Tile(TEX["granite"], 4.0), faces={"b": "skip", "e": "skip"})
            _sign_panel(mb, "-x", ix1 - 0.08, c_y0 + 1.5, c_y0 + 6.0, 4.4, 7.6, TEX["stucco_mint"])
            break

    # Compact accent loveseat along SE partition wall when part_y leaves east clear bay
    if part_y is not None and _clear(ix1 - 8.0, part_y + 0.3, ix1 - 0.8, part_y + 3.6):
        mb.detail_box_ft(ix1 - 7.6, part_y + 0.3, z_floor, ix1 - 1.2, part_y + 3.3, z_floor + 1.55, Tile(TEX["leather"], 4.0), faces={"b": "skip", "s": "skip"})
        mb.detail_box_ft(ix1 - 7.6, part_y + 0.3, z_floor + 1.55, ix1 - 1.2, part_y + 1.1, z_floor + 2.95, Tile(TEX["leather"], 4.0), faces={"b": "skip", "s": "skip"})

    # SW or SE bedroom queen bed + nightstand (strictly outside center corridor)
    if _clear(ix0, iy0, ix0 + 6.2, iy0 + 8.0):
        _motel_bed_set(mb, ix0 + 0.5, iy0 + 0.4, z_floor, head_side="s")
    elif _clear(ix1 - 8.5, iy0, ix1, iy0 + 8.0):
        _motel_bed_set(mb, ix1 - 6.2, iy0 + 0.4, z_floor, head_side="s")


def _ranch_enterable(
    mb: MapBuilder,
    name: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    tex_ext: str,
    tex_roof: str,
    doors_n: Sequence[Tuple[float, float, float, str]] = (),
    doors_s: Sequence[Tuple[float, float, float, str]] = (),
    doors_e: Sequence[Tuple[float, float, float, str]] = (),
    doors_w: Sequence[Tuple[float, float, float, str]] = (),
    ridge_along: str = "x",
    two_storey: bool = False,
    part_y: Optional[float] = None,
    extra_wins_e: Sequence[Tuple[float, float, float, float]] = (),
    extra_wins_w: Sequence[Tuple[float, float, float, float]] = (),
) -> None:
    """Build an enterable street-facing Bakersfield residence with drywall interior & >=112u ceiling."""
    z_ceil = 10.50
    ceil_top = 11.00 if two_storey else 11.15
    wins_n = _safe_wall_wins(x0 + 0.75, x1 - 0.75, doors_n)
    wins_s = _safe_wall_wins(x0 + 0.75, x1 - 0.75, doors_s)
    wins_e = list(extra_wins_e) if extra_wins_e else _safe_wall_wins(y0 + 0.75, y1 - 0.75, doors_e)
    wins_w = list(extra_wins_w) if extra_wins_w else _safe_wall_wins(y0 + 0.75, y1 - 0.75, doors_w)
    _rect_shell(
        mb,
        name,
        x0,
        y0,
        x1,
        y1,
        z_floor=0.25,
        z_ceil=z_ceil,
        tex_ext=tex_ext,
        tex_int=TEX["drywall"],
        tex_floor=TEX["wood_tan"],
        tex_ceil=TEX["drywall"],
        thick=0.75,
        doors_n=doors_n,
        doors_s=doors_s,
        doors_e=doors_e,
        doors_w=doors_w,
        wins_n=wins_n,
        wins_s=wins_s,
        wins_e=wins_e,
        wins_w=wins_w,
        build_ceil=True,
        ceil_top=ceil_top,
        light_level=185.0,
        light_nx=2,
        light_ny=2,
    )
    # 1950s Bakersfield white-framed sliding glass windows across all exterior walls
    for wx0, wx1, bz0, bz1 in wins_n:
        _barred_square_window(mb, "x", y1 - 0.75, wx0, wx1, bz0, bz1, TEX["stucco_white"], cols=2, rows=1)
    for wx0, wx1, bz0, bz1 in wins_s:
        _barred_square_window(mb, "x", y0, wx0, wx1, bz0, bz1, TEX["stucco_white"], cols=2, rows=1)
    for wy0, wy1, bz0, bz1 in wins_e:
        _barred_square_window(mb, "y", x1 - 0.75, wy0, wy1, bz0, bz1, TEX["stucco_white"], cols=2, rows=1)
    for wy0, wy1, bz0, bz1 in wins_w:
        _barred_square_window(mb, "y", x0, wy0, wy1, bz0, bz1, TEX["stucco_white"], cols=2, rows=1)

    _furnish_house_interior(mb, x0, y0, x1, y1, 0.25, z_ceil, doors_n, doors_s, doors_e, doors_w, part_y=part_y)

    if two_storey:
        # Upper grey-stucco storey massing starting cleanly above 1F drywall ceiling slab (z >= 11.00)
        mb.structural_box_ft(x0, y0, 11.00, x1, y1, 20.5, Tile(tex_ext, 8.0))
        _hip_roof(mb, x0, y0, x1, y1, z_eave=20.5, z_ridge=23.5, tex_roof=tex_roof)
        _sign_panel(mb, "+x", x1, y0 + 10.0, y0 + 18.0, 13.5, 17.5, TEX["win_house"])
        mb.flush_panel_ft(x1 + 0.08, y0 + 13.9, 13.5, x1 + 0.16, y0 + 14.1, 17.5, {"e": Tile(TEX["stucco_white"], 4.0), "n": Tile(TEX["stucco_white"], 4.0), "s": Tile(TEX["stucco_white"], 4.0)}, group="illus")
        _sign_panel(mb, "+x", x1, y1 - 24.0, y1 - 14.0, 13.5, 17.5, TEX["win_house"])
        mb.flush_panel_ft(x1 + 0.08, y1 - 19.1, 13.5, x1 + 0.16, y1 - 18.9, 17.5, {"e": Tile(TEX["stucco_white"], 4.0), "n": Tile(TEX["stucco_white"], 4.0), "s": Tile(TEX["stucco_white"], 4.0)}, group="illus")
        _sign_panel(mb, "+y", y1, x0 + 10.0, x0 + 18.0, 13.5, 17.5, TEX["win_house"])
        mb.flush_panel_ft(x0 + 13.9, y1 + 0.08, 13.5, x0 + 14.1, y1 + 0.16, 17.5, {"n": Tile(TEX["stucco_white"], 4.0), "e": Tile(TEX["stucco_white"], 4.0), "w": Tile(TEX["stucco_white"], 4.0)}, group="illus")
        # Crisp white entry door trim & covered Delaware St front porch (spot_65, strictly west of CASINO_LOT_FT x=-157.7)
        for dy0, dy1, _, _ in doors_e:
            mb.detail_box_ft(x1 - 0.04, dy0 - 0.35, 0.25, x1 + 0.16, dy0, 9.2, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip", "t": "skip", "w": "skip"})
            mb.detail_box_ft(x1 - 0.04, dy1, 0.25, x1 + 0.16, dy1 + 0.35, 9.2, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip", "t": "skip", "w": "skip"})
            mb.detail_box_ft(x1 - 0.04, dy0 - 0.35, 9.2, x1 + 0.18, dy1 + 0.35, 9.65, Tile(TEX["stucco_white"], 4.0), faces={"w": "skip"})
            mb.detail_box_ft(x1, dy0 - 2.0, 0.0, x1 + 3.4, dy1 + 2.0, 0.25, Tile(TEX["concrete"], 6.0), faces={"b": "skip", "w": "skip"})
            mb.detail_box_ft(x1, dy0 - 2.2, 9.6, x1 + 3.6, dy1 + 2.2, 10.15, Tile(TEX["stucco_white"], 6.0), faces={"w": "skip"})
            mb.detail_box_ft(x1 + 3.0, dy0 - 1.9, 0.25, x1 + 3.4, dy0 - 1.5, 9.6, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip", "t": "skip"})
            mb.detail_box_ft(x1 + 3.0, dy1 + 1.5, 0.25, x1 + 3.4, dy1 + 1.9, 9.6, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip", "t": "skip"})
            mb.light_ft(x1 + 1.8, 0.5 * (dy0 + dy1), 9.0, light=180.0)
    else:
        _gable_roof(mb, x0, y0, x1, y1, z_eave=11.15, z_ridge=14.6, tex_roof=tex_roof, tex_gable=tex_ext, ridge_along=ridge_along)
        _swamp_cooler(mb, 0.5 * (x0 + x1), 0.5 * (y0 + y1), 12.8)


def _yard_kit(
    mb: MapBuilder,
    drive_x: Optional[float],
    drive_y0: float,
    drive_y1: float,
    tree_x: float,
    tree_y: float,
) -> None:
    """Place an open residential concrete driveway strip (matching html/076) and Valley Oak shade tree."""
    if drive_x is not None:
        mb.detail_box_ft(drive_x - 4.5, drive_y0, 0.0, drive_x + 4.5, drive_y1, 2.0 / 12.0, Tile(TEX["concrete"], 6.0), faces={"b": "skip"})
    _yard_tree(mb, tree_x, tree_y, height=17.0, crown_r=4.6, tex_crown=TEX["tree_2"])


def _build_west_residential(mb: MapBuilder) -> None:
    """Build West Residential Neighborhood across Casino Fringe, Trinity South & Mariposa South."""
    # ---- Block A: west_casino_fringe (x=-489.75..-158.0, y=-124.75..148.0) ----
    _pad(mb, -489.75, -124.75, -158.0, 148.0, TEX["grass"])
    # Enterable BLDG 59983823 behind casino (x=-275..-187, y=-80..-6)
    _ranch_enterable(
        mb,
        "INT Ranch 59983823",
        -275.0,
        -80.0,
        -187.0,
        -6.0,
        tex_ext=TEX["stucco_cream"],
        tex_roof=TEX["shingle_brown"],
        doors_s=[(-235.0, -227.0, 9.2, "ranch_3823_trinity")],
        doors_w=[(-46.0, -38.0, 9.2, "ranch_3823_west")],
        doors_n=[(-235.0, -227.0, 9.2, "ranch_3823_back")],
        ridge_along="x",
        part_y=-55.0,
    )
    _carport_canopy(mb, -299.0, -48.0, -275.0, -10.0, z_roof=9.4, tex_roof=TEX["corrug_silver"], attach_side="e")
    # Block A lightweight exteriors
    _ranch_exterior(mb, -378.0, -88.0, -322.0, -26.0, TEX["siding"], TEX["shingle_dark"], carport_side="w", door_side="y-")
    _ranch_exterior(mb, -462.0, -88.0, -404.0, -28.0, TEX["stucco_tan"], TEX["shingle_brown"], door_side="y-")
    _ranch_exterior(mb, -372.0, 20.0, -314.0, 76.0, TEX["stucco_mint"], TEX["shingle_brown"], carport_side="e", door_side="y-")
    _ranch_exterior(mb, -460.0, 22.0, -398.0, 80.0, TEX["stucco_cream"], TEX["shingle_dark"], door_side="y-")
    _yard_kit(mb, -287.0, -124.5, -48.0, -205.0, -104.0)
    _parked_car(mb, -287.0, -88.0, CAR_COLORS[1], axis="y")

    # ---- Block B: west_trinity_south (split cleanly around CASINO_LOT_FT -157.7,-270.9) ----
    _pad(mb, -489.75, -271.0, -158.0, -166.25, TEX["grass"])
    _pad(mb, -489.75, -435.75, -143.25, -271.0, TEX["grass"])
    # Enterable BLDG 59933078: 2-storey grey-stucco duplex on Delaware/Trinity corner (#078)
    _ranch_enterable(
        mb,
        "INT Delaware Duplex 59933078",
        -202.0,
        -272.0,
        -161.5,
        -199.5,
        tex_ext=TEX["stucco_slate"],
        tex_roof=TEX["shingle_dark"],
        doors_n=[(-186.0, -178.0, 9.2, "duplex_trinity")],
        doors_e=[(-238.0, -230.0, 9.2, "duplex_delaware")],
        doors_w=[(-238.0, -230.0, 9.2, "duplex_west_breezeway")],
        two_storey=True,
        part_y=-248.5,
        extra_wins_e=[(-266.0, -258.0, 3.2, 7.4), (-248.5, -241.0, 3.2, 7.4), (-227.0, -219.5, 3.2, 7.4), (-212.0, -204.0, 3.2, 7.4)],
    )
    # Covered wood-floored breezeway linking 59933078 West door straight into 59930665 East door (no grass/dark wall!)
    mb.detail_box_ft(-211.0, -256.5, 0.0, -202.0, -199.5, 0.25, Tile(TEX["wood_tan"], 6.0), faces={"b": "skip", "w": "skip", "e": "skip"})
    mb.detail_box_ft(-211.0, -242.5, 9.5, -202.0, -225.5, 10.1, Tile(TEX["drywall"], 6.0), faces={"w": "skip", "e": "skip"})
    mb.light_ft(-206.5, -234.0, 8.8, light=300.0)
    # Enterable BLDG 59930665 on Trinity Ave (x=-251.5..-211.0, y=-256.5..-199.5)
    _ranch_enterable(
        mb,
        "INT Trinity Ranch 59930665",
        -251.5,
        -256.5,
        -211.0,
        -199.5,
        tex_ext=TEX["stucco_mint"],
        tex_roof=TEX["shingle_brown"],
        doors_n=[(-236.0, -228.0, 9.2, "ranch_0665_trinity")],
        doors_s=[(-236.0, -228.0, 9.2, "ranch_0665_rear")],
        doors_e=[(-238.0, -230.0, 9.2, "ranch_0665_breezeway")],
        ridge_along="y",
        extra_wins_w=[(-240.0, -228.0, 3.2, 7.4), (-215.0, -206.0, 3.2, 7.4)],
    )
    # Enterable BLDG 59931762 on Delaware/Mariposa corner (x=-201.5..-167.5, y=-405.0..-338.0)
    _ranch_enterable(
        mb,
        "INT Mariposa Ranch 59931762",
        -201.5,
        -405.0,
        -167.5,
        -338.0,
        tex_ext=TEX["stucco_tan"],
        tex_roof=TEX["shingle_brown"],
        doors_e=[(-375.0, -367.0, 9.2, "ranch_1762_delaware")],
        doors_s=[(-188.0, -180.0, 9.2, "ranch_1762_mariposa")],
        ridge_along="y",
        part_y=-382.5,
    )
    # Missing OSM BLDG 59930598 (x=-253.2..-208.5, y=-405.9..-339.6) + Block B lightweight ranch cottages
    _ranch_exterior(mb, -253.2, -405.9, -208.5, -339.6, TEX["stucco_white"], TEX["shingle_dark"], ridge_along="y", door_side="y-")
    _ranch_exterior(mb, -310.0, -254.0, -264.0, -198.0, TEX["stucco_cream"], TEX["shingle_brown"], ridge_along="y", door_side="y+")
    _ranch_exterior(mb, -372.0, -254.0, -324.0, -198.0, TEX["siding"], TEX["shingle_dark"], ridge_along="y", carport_side="w", door_side="y+")
    _ranch_exterior(mb, -445.0, -254.0, -392.0, -198.0, TEX["stucco_white"], TEX["shingle_brown"], ridge_along="y", door_side="y+")
    _ranch_exterior(mb, -306.0, -404.0, -256.0, -342.0, TEX["stucco_cream"], TEX["shingle_dark"], door_side="y-")
    _ranch_exterior(mb, -376.0, -404.0, -322.0, -342.0, TEX["stucco_mint"], TEX["shingle_brown"], carport_side="w", door_side="y-")
    _ranch_exterior(mb, -448.0, -404.0, -392.0, -342.0, TEX["siding"], TEX["shingle_dark"], door_side="y-")

    # Block B open lawns (zero fences, zero lawn boxes) + driveways, parked sedan & shade trees
    _yard_kit(mb, -206.5, -199.5, -166.5, -172.0, -184.0)
    _yard_kit(mb, -286.0, -198.0, -166.5, -285.0, -305.0)
    _yard_kit(mb, -348.0, -435.5, -404.0, -415.0, -298.0)
    _parked_car(mb, -286.0, -181.0, CAR_COLORS[3], axis="y")

    # ---- Block C: west_mariposa_south (x=-489.75..-143.25, y=-745.75..-476.25) ----
    _pad(mb, -489.75, -745.75, -143.25, -476.25, TEX["grass"])
    # Enterable BLDG 59932077 on Amador/Delaware corner (x=-249.0..-190.0, y=-701.5..-637.5)
    _ranch_enterable(
        mb,
        "INT Amador Ranch 59932077",
        -249.0,
        -701.5,
        -190.0,
        -637.5,
        tex_ext=TEX["stucco_cream"],
        tex_roof=TEX["shingle_brown"],
        doors_e=[(-673.0, -665.0, 9.2, "ranch_2077_delaware")],
        doors_s=[(-224.0, -216.0, 9.2, "ranch_2077_amador")],
        ridge_along="x",
        part_y=-680.5,
    )
    # Block C lightweight exterior cottages
    _ranch_exterior(mb, -225.0, -554.0, -168.0, -496.0, TEX["stucco_tan"], TEX["shingle_brown"], door_side="y+")
    _ranch_exterior(mb, -305.0, -554.0, -250.0, -496.0, TEX["siding"], TEX["shingle_dark"], carport_side="w", door_side="y+")
    _ranch_exterior(mb, -385.0, -554.0, -328.0, -496.0, TEX["stucco_mint"], TEX["shingle_brown"], door_side="y+")
    _ranch_exterior(mb, -460.0, -554.0, -404.0, -496.0, TEX["stucco_cream"], TEX["shingle_dark"], door_side="y+")
    _ranch_exterior(mb, -318.0, -718.0, -264.0, -654.0, TEX["stucco_white"], TEX["shingle_brown"], door_side="y-")
    _ranch_exterior(mb, -396.0, -718.0, -340.0, -654.0, TEX["stucco_tan"], TEX["shingle_dark"], carport_side="e", door_side="y-")
    _ranch_exterior(mb, -468.0, -718.0, -412.0, -654.0, TEX["siding"], TEX["shingle_brown"], door_side="y-")

    _yard_kit(mb, -196.0, -496.0, -476.5, -155.0, -588.0)
    _yard_kit(mb, -290.0, -745.5, -718.0, -325.0, -600.0)
    _parked_car(mb, -290.0, -731.0, CAR_COLORS[4], axis="y")
    _palm_tree(mb, -154.0, -490.0, height=20.0)

    # Required residential interior & Delaware/Trinity exterior audit spots
    mb.spot_ft("int_15_delaware_house", -182.0, -235.0, 5.5, yaw=180.0, kind="interior", desc="Inside Delaware/Trinity 2F Duplex")
    mb.spot_ft("int_trinity_0665", -231.0, -228.0, 5.5, yaw=90.0, kind="interior", desc="Inside Trinity Ranch 59930665")
    mb.spot_ft("int_mariposa_1762", -184.0, -371.0, 5.5, yaw=0.0, kind="interior", desc="Inside Mariposa Ranch 59931762")
    mb.spot_ft("int_amador_2077", -220.0, -669.0, 5.5, yaw=0.0, kind="interior", desc="Inside Amador Ranch 59932077")
    mb.spot_ft("int_ranch_3823", -231.0, -43.0, 5.5, yaw=270.0, kind="interior", desc="Inside Ranch 59983823 behind casino")
    mb.spot_ft("ext_16_delaware_trinity", -145.0, -228.0, 6.5, yaw=188.0, kind="exterior", desc="West Delaware/Trinity 2F Duplex & residential view")


# ---------------------------------------------------------------------------
# 5. Northern Extension West of S Union Ave (y=750.0..1340.0)
# ---------------------------------------------------------------------------
def _build_north_4th_to_hy1(mb: MapBuilder) -> None:
    """Build gc_west_4th_onestop (750..842) and gc_west_manila_dg (882..1340) west of Union."""
    # ---- Block 1: gc_west_4th_onestop (x=-490..172, y=750.0..842.0) ----
    _pad(mb, -195.0, 750.25, 171.75, 841.75, TEX["asphalt"])
    _pad(mb, -489.75, 750.25, -195.0, 841.75, TEX["dirt"])

    # Diamond Shamrock fuel canopy (SW Union & 4th St, >=64u aisles everywhere)
    can_x0, can_y0, can_x1, can_y1 = 104.0, 762.0, 156.0, 824.0
    can_faces = {
        "t": Tile(TEX["roof_tpo"], 8.0),
        "b": Tile(TEX["white"], 8.0),
        "e": Tile(TEX["stucco_white"], 8.0),
        "w": Tile(TEX["stucco_white"], 8.0),
        "n": Tile(TEX["stucco_white"], 8.0),
        "s": Tile(TEX["stucco_white"], 8.0),
    }
    mb.detail_box_ft(can_x0, can_y0, 14.0, can_x1, can_y1, 17.6, Tile(TEX["stucco_white"], 8.0), faces=can_faces)
    _sign_panel(mb, "+x", can_x1, 789.4, 796.6, 14.1, 17.5, TEX["sign_shamrock"])
    _sign_panel(mb, "+y", can_y1, 126.4, 133.6, 14.1, 17.5, TEX["sign_shamrock"])

    for px in (116.0, 144.0):
        for py in (774.0, 812.0):
            mb.detail_box_ft(px - 0.45, py - 0.45, 2.0 / 12.0, px + 0.45, py + 0.45, 14.0, Tile(TEX["steel_light"], 4.0), faces={"b": "skip", "t": "skip"})
        # Fuel pump island (<= 18u curb) cleanly between S (774) and N (812) canopy columns
        mb.detail_box_ft(px - 2.4, 776.5, 2.0 / 12.0, px + 2.4, 809.5, 0.65, Tile(TEX["concrete"], 6.0), faces={"b": "skip"})
        for dy in (784.0, 802.0):
            mb.detail_box_ft(px - 1.3, dy - 1.0, 0.65, px + 1.3, dy + 1.0, 5.4, Tile(TEX["stucco_white"], 4.0), faces={"b": "skip"})
            mb.detail_box_ft(px - 1.35, dy - 1.05, 5.4, px + 1.35, dy + 1.05, 6.0, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip"})
            # Flush canopy ceiling downlight fixture + warm island light directly over each pump
            mb.flush_panel_ft(px - 1.2, dy - 1.2, 13.94, px + 1.2, dy + 1.2, 14.0, {"b": Fit(TEX["troffer"])}, group="illus")
            mb.light_ft(px, dy, 12.8, light=175.0, color=(255, 224, 176))

    # SW Union/4th corner Diamond Shamrock pole sign (exact 2:1 cabinet, well inside parcel bounds)
    mb.detail_box_ft(162.2, 833.2, 2.0 / 12.0, 162.8, 833.8, 12.5, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(161.9, 828.5, 12.5, 163.1, 838.5, 17.5, Tile(TEX["steel_dark"], 4.0))
    _sign_panel(mb, "+x", 163.1, 828.8, 838.2, 12.7, 17.3, TEX["sign_shamrock"])
    _sign_panel(mb, "-x", 161.9, 828.8, 838.2, 12.7, 17.3, TEX["sign_shamrock"])

    # Plain One Stop c-store exterior shell (OSM WAY 59787585; zero unverified signage)
    os_x0, os_y0, os_x1, os_y1 = 24.0, 754.0, 76.0, 814.0
    mb.detail_box_ft(os_x0, os_y0, 2.0 / 12.0, os_x1, os_y1, 14.5, Tile(TEX["stucco_tan"], 8.0), faces={"b": "skip", "t": Tile(TEX["roof_tpo"], 8.0)})
    mb.detail_box_ft(os_x0, os_y0, 14.5, os_x1, os_y1, 15.25, Tile(TEX["fascia_brown"], 8.0), faces={"b": "skip"})
    mb.detail_box_ft(os_x1, 762.0, 9.8, os_x1 + 5.5, 806.0, 10.7, Tile(TEX["stucco_white"], 6.0), faces={"w": "skip"})
    mb.detail_box_ft(os_x1, os_y0, 2.0 / 12.0, os_x1 + 6.0, os_y1, 0.5, Tile(TEX["concrete"], 6.0), faces={"b": "skip"})
    _sign_panel(mb, "+x", os_x1, 766.0, 780.0, 2.8, 8.8, TEX["glass"])
    _sign_panel(mb, "+x", os_x1, 788.0, 802.0, 2.8, 8.8, TEX["glass"])
    _sign_panel(mb, "+x", os_x1, 781.0, 787.0, 0.5, 8.5, TEX["door_wood"])
    mb.detail_box_ft(44.0, 780.0, 15.25, 52.0, 788.0, 17.5, Tile(TEX["hvac"], 4.0), faces={"b": "skip"})

    # West 4th St light-industrial/warehouse strip (OSM WAYs 59795385, 59789784, 59791050)
    mb.detail_box_ft(-86.0, 794.0, 2.0 / 12.0, 14.0, 818.0, 12.0, Tile(TEX["cmu_tan"], 8.0), faces={"b": "skip", "t": Tile(TEX["roof_tpo"], 8.0)})
    for rx0, rx1 in ((-68.0, -52.0), (-22.0, -6.0)):
        _sign_panel(mb, "+y", 818.0, rx0, rx1, 0.5, 9.5, TEX["rollup"])
    mb.detail_box_ft(-42.0, 802.0, 12.0, -34.0, 810.0, 14.2, Tile(TEX["hvac"], 4.0), faces={"b": "skip"})

    mb.detail_box_ft(-194.0, 790.0, 2.0 / 12.0, -144.0, 816.0, 11.5, Tile(TEX["stucco_cream"], 8.0), faces={"b": "skip", "t": Tile(TEX["roof_tpo"], 8.0)})
    _sign_panel(mb, "+y", 816.0, -184.0, -168.0, 2.8, 7.6, TEX["glass"])
    _sign_panel(mb, "+y", 816.0, -162.0, -156.0, 0.5, 8.2, TEX["door_wood"])

    mb.detail_box_ft(-356.0, 794.0, 1.0 / 12.0, -210.0, 816.0, 11.5, Tile(TEX["stucco_tan"], 8.0), faces={"b": "skip", "t": Tile(TEX["corrug_silver"], 8.0)})
    for rx0 in (-342.0, -296.0, -250.0):
        _sign_panel(mb, "+y", 816.0, rx0, rx0 + 16.0, 0.5, 9.2, TEX["rollup"])

    _fence_line_x(mb, 837.5, -486.0, -364.0, 1.0 / 12.0, 6.0, TEX["chain_fence"], gaps=[(-440.0, -408.0)], post_step=36.0)
    _yard_tree(mb, -382.0, 826.0, height=17.0, crown_r=4.6, tex_crown=TEX["tree_2"], z0=1.0 / 12.0)
    _yard_tree(mb, -468.0, 786.0, height=16.0, crown_r=4.4, tex_crown=TEX["tree_2"], z0=1.0 / 12.0)

    # ---- Block 2: gc_west_manila_dg (x=-490..172, y=882.0..1340.0) ----
    _pad(mb, -110.0, 882.25, 171.75, 1339.75, TEX["asphalt"])
    # Residential V St corridor & flanking lawn parcels (strictly disjoint XY)
    _pad(mb, -396.0, 882.25, -368.0, 1339.75, TEX["asphalt"])
    _pad(mb, -489.75, 882.25, -396.0, 1339.75, TEX["grass"])
    _pad(mb, -368.0, 882.25, -110.0, 1339.75, TEX["grass"])

    # Corner plaza landscaping south of Manila Inn (NW Union & 4th St)
    _palm_tree(mb, 162.0, 898.0, height=23.0, z0=2.0 / 12.0)
    _palm_tree(mb, 162.0, 942.0, height=22.0, z0=2.0 / 12.0)
    _yard_tree(mb, 88.0, 912.0, height=16.0, crown_r=4.5, tex_crown=TEX["tree_2"], z0=2.0 / 12.0)

    # Manila Inn low L-shaped stucco wing (zero illegible street signs per #130/#133)
    mb.detail_box_ft(-24.0, 1024.0, 2.0 / 12.0, 104.0, 1068.0, 11.0, Tile(TEX["stucco_tan"], 8.0), faces={"b": "skip", "t": "skip"})
    _gable_roof(mb, -24.0, 1024.0, 104.0, 1068.0, z_eave=11.0, z_ridge=15.0, tex_roof=TEX["shingle_brown"], tex_gable=TEX["stucco_tan"], ridge_along="x")
    mb.detail_box_ft(14.0, 1018.0, 9.4, 104.0, 1024.0, 10.2, Tile(TEX["fascia_brown"], 6.0), faces={"n": "skip", "w": "skip"})
    mb.detail_box_ft(14.0, 1018.0, 2.0 / 12.0, 104.0, 1024.0, 0.5, Tile(TEX["concrete"], 6.0), faces={"b": "skip", "n": "skip"})
    for mx in (16.0, 42.0, 68.0, 90.0):
        _sign_panel(mb, "-y", 1024.0, mx, mx + 4.0, 0.5, 7.6, TEX["door_wood"])
        _sign_panel(mb, "-y", 1024.0, mx + 6.0, mx + 12.0, 3.4, 7.2, TEX["win_motel"])

    mb.detail_box_ft(-24.0, 956.0, 2.0 / 12.0, 14.0, 1024.0, 11.0, Tile(TEX["stucco_tan"], 8.0), faces={"b": "skip", "t": "skip", "n": "skip"})
    _gable_roof(mb, -24.0, 956.0, 14.0, 1022.5, z_eave=11.0, z_ridge=14.6, tex_roof=TEX["shingle_brown"], tex_gable=TEX["stucco_tan"], over=0.8, ridge_along="y")
    mb.detail_box_ft(14.0, 956.0, 9.4, 20.0, 1018.0, 10.2, Tile(TEX["fascia_brown"], 6.0), faces={"w": "skip", "n": "skip"})
    mb.detail_box_ft(14.0, 956.0, 2.0 / 12.0, 20.0, 1018.0, 0.5, Tile(TEX["concrete"], 6.0), faces={"b": "skip", "w": "skip", "n": "skip"})
    for my in (966.0, 994.0):
        _sign_panel(mb, "+x", 14.0, my, my + 4.0, 0.5, 7.6, TEX["door_wood"])
        _sign_panel(mb, "+x", 14.0, my + 6.0, my + 12.0, 3.4, 7.2, TEX["win_motel"])

    for cx, cy, axis, ci in ((52.0, 974.0, "y", 0), (76.0, 974.0, "y", 1), (134.0, 998.0, "x", 2)):
        _parked_car(mb, cx, cy, CAR_COLORS[ci], axis=axis, z0=2.0 / 12.0)

    # DG market tilt-up store set back west behind Union front parking lot (opposite E 5th St)
    dg_x0, dg_y0, dg_x1, dg_y1 = -82.0, 1138.0, 52.0, 1258.0
    mb.detail_box_ft(dg_x0, dg_y0, 2.0 / 12.0, dg_x1, dg_y1, 18.0, Tile(TEX["stucco_tan"], 10.0), faces={"b": "skip", "t": Tile(TEX["roof_tpo"], 10.0)})
    # Perimeter parapet coping + stepped East Union entrance crown with exact 2:1 DG market sign
    mb.detail_box_ft(dg_x0, dg_y0, 18.0, dg_x1, dg_y0 + 1.0, 19.4, Tile(TEX["stucco_cream"], 8.0), faces={"b": "skip"})
    mb.detail_box_ft(dg_x0, dg_y1 - 1.0, 18.0, dg_x1, dg_y1, 19.4, Tile(TEX["stucco_cream"], 8.0), faces={"b": "skip"})
    mb.detail_box_ft(dg_x0, dg_y0 + 1.0, 18.0, dg_x0 + 1.0, dg_y1 - 1.0, 19.4, Tile(TEX["stucco_cream"], 8.0), faces={"b": "skip", "s": "skip", "n": "skip"})
    mb.detail_box_ft(dg_x1 - 1.0, dg_y0 + 1.0, 18.0, dg_x1, 1174.0, 19.4, Tile(TEX["stucco_cream"], 8.0), faces={"b": "skip", "s": "skip"})
    mb.detail_box_ft(dg_x1 - 1.0, 1222.0, 18.0, dg_x1, dg_y1 - 1.0, 19.4, Tile(TEX["stucco_cream"], 8.0), faces={"b": "skip", "n": "skip"})
    mb.detail_box_ft(52.0, 1174.0, 11.4, 52.6, 1222.0, 24.2, Tile(TEX["stucco_cream"], 8.0), faces={"b": "skip", "w": "skip"})
    _sign_panel(mb, "+x", 52.6, 1188.0, 1208.0, 13.8, 23.8, TEX["sign_dg"])

    # DG market canopy, walkway apron, storefront glass, rooftop HVAC & rear dumpster enclosure
    mb.detail_box_ft(52.0, 1162.0, 10.5, 60.0, 1234.0, 11.4, Tile(TEX["steel_dark"], 6.0), faces={"w": "skip"})
    for py in (1165.0, 1188.0, 1208.0, 1231.0):
        mb.detail_box_ft(58.9, py - 0.3, 0.5, 59.5, py + 0.3, 10.5, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
    mb.detail_box_ft(52.0, 1142.0, 2.0 / 12.0, 62.0, 1254.0, 0.5, Tile(TEX["concrete"], 6.0), faces={"b": "skip"})
    _sign_panel(mb, "+x", 52.0, 1166.0, 1186.0, 2.0, 9.2, TEX["glass"])
    _sign_panel(mb, "+x", 52.0, 1210.0, 1230.0, 2.0, 9.2, TEX["glass"])
    _sign_panel(mb, "+x", 52.0, 1190.0, 1206.0, 0.5, 9.0, TEX["glass"])
    mb.light_ft(56.0, 1198.0, 9.6, light=140.0)

    for hy in (1170.0, 1226.0):
        mb.detail_box_ft(-22.0, hy - 4.5, 18.0, -12.0, hy + 4.5, 20.6, Tile(TEX["hvac"], 6.0), faces={"b": "skip"})
    mb.detail_box_ft(-96.0, 1214.0, 2.0 / 12.0, -82.5, 1215.0, 6.0, Tile(TEX["cmu_tan"], 6.0), faces={"b": "skip"})
    mb.detail_box_ft(-96.0, 1238.0, 2.0 / 12.0, -82.5, 1239.0, 6.0, Tile(TEX["cmu_tan"], 6.0), faces={"b": "skip"})
    mb.detail_box_ft(-96.0, 1215.0, 2.0 / 12.0, -95.0, 1238.0, 6.0, Tile(TEX["cmu_tan"], 6.0), faces={"b": "skip", "s": "skip", "n": "skip"})
    mb.detail_box_ft(-93.0, 1221.0, 2.0 / 12.0, -86.0, 1232.0, 4.5, Tile(TEX["dumpster"], 6.0), faces={"b": "skip"})

    # Front Union parking lot (clear center sightline from E 5th St to DG market)
    z_lot, z_mark, sw, hsw = 2.0 / 12.0, 2.5 / 12.0, 0.90, 0.45
    west_banks = (
        (1094.5, 5),   # South wing (frames car at x=96, y=1126)
        (1148.5, 4),   # South-center storefront bays (clear of pole y=1142 & center aisle)
        (1211.5, 4),   # North-center storefront bays (clear of pole y=1254 & center aisle)
        (1258.5, 5),   # North wing (frames car at x=96, y=1272)
    )
    east_banks = (
        (1094.5, 5),   # South wing (frames car at x=136, y=1126)
        (1258.5, 5),   # North wing (frames car at x=136, y=1272)
    )
    for spine_x, tick_x0, tick_x1, banks in (
        (105.0, 87.0, 105.0 - hsw, west_banks),
        (127.0, 127.0 + hsw, 145.0, east_banks),
    ):
        for y_start, n_bays in banks:
            y_end = y_start + n_bays * 9.0
            mb.flush_panel_ft(
                spine_x - hsw, y_start - hsw, z_lot,
                spine_x + hsw, y_end + hsw, z_mark,
                {"t": Fit(TEX["wline"], repeat=(1.0, max(1.0, (y_end - y_start) / 6.0)))},
                group="illus",
            )
            for idx in range(n_bays + 1):
                sy = y_start + idx * 9.0
                mb.flush_panel_ft(
                    tick_x0, sy - hsw, z_lot,
                    tick_x1, sy + hsw, z_mark,
                    {"t": Tile(TEX["wline"], w_ft=sw, h_ft=6.0, u_ofs=(sy / sw) + 0.5, rot_deg=90.0)},
                    group="illus",
                )
    for cx, cy, ci in ((96.0, 1126.0, 3), (136.0, 1126.0, 4), (96.0, 1272.0, 0), (136.0, 1272.0, 2)):
        _parked_car(mb, cx, cy, CAR_COLORS[ci], axis="x", z0=2.0 / 12.0)
    for ly in (1142.0, 1254.0):
        mb.detail_box_ft(115.7, ly - 0.3, 2.0 / 12.0, 116.3, ly + 0.3, 19.0, Tile(TEX["steel_dark"], 4.0), faces={"b": "skip", "t": "skip"})
    for py in (1122.0, 1242.0, 1308.0):
        _palm_tree(mb, 163.0, py, height=23.0, z0=2.0 / 12.0)
    _yard_tree(mb, -25.0, 1304.0, height=18.0, crown_r=4.8, tex_crown=TEX["tree_2"], z0=2.0 / 12.0)
    _yard_tree(mb, 28.0, 1304.0, height=17.0, crown_r=4.6, tex_crown=TEX["tree_2"], z0=2.0 / 12.0)

    # West V St residential cottages (OSM route_3 locations, strictly inside [-490..172] x [882..1340])
    for hx0, hy0, hx1, hy1, wt, rt, ra, ds in (
        (-164.0,  924.0, -118.0, 1004.0, TEX["stucco_cream"], TEX["shingle_brown"], "y", "x+"),
        (-168.0, 1038.0, -120.0, 1092.0, TEX["stucco_mint"],  TEX["shingle_dark"],  "y", "x+"),
        (-278.0, 1054.0, -224.0, 1094.0, TEX["stucco_tan"],   TEX["shingle_brown"], "x", "y-"),
        (-360.0,  976.0, -306.0, 1030.0, TEX["stucco_white"], TEX["shingle_dark"],  "y", "x-"),
        (-360.0, 1110.0, -318.0, 1152.0, TEX["siding"],       TEX["shingle_brown"], "y", "x-"),
        (-362.0, 1176.0, -320.0, 1216.0, TEX["stucco_tan"],   TEX["shingle_dark"],  "y", "x-"),
        (-362.0, 1248.0, -304.0, 1296.0, TEX["stucco_cream"], TEX["shingle_brown"], "y", "x-"),
        (-478.0,  922.0, -422.0,  970.0, TEX["stucco_tan"],   TEX["shingle_brown"], "y", "x+"),
        (-478.0, 1122.0, -424.0, 1168.0, TEX["siding"],       TEX["shingle_dark"],  "y", "x+"),
    ):
        _ranch_exterior(mb, hx0, hy0, hx1, hy1, wt, rt, ridge_along=ra, door_side=ds)

    _fence_line_y(mb, -110.5, 886.0, 1336.0, 1.0 / 12.0, 6.0, TEX["chain_fence"], gaps=[(1076.0, 1126.0)], post_step=36.0)
    _fence_line_y(mb, -366.5, 900.0, 1320.0, 1.0 / 12.0, 3.5, TEX["iron_fence"], gaps=[(970.0, 1036.0), (1105.0, 1158.0), (1172.0, 1222.0), (1242.0, 1300.0)], post_step=36.0)
    _fence_line_y(mb, -397.5, 900.0, 1320.0, 1.0 / 12.0, 3.5, TEX["iron_fence"], gaps=[(916.0, 976.0), (1116.0, 1174.0)], post_step=36.0)
    for tx, ty in ((-342.0, 916.0), (-210.0, 945.0), (-446.0, 1044.0), (-235.0, 1235.0)):
        _yard_tree(mb, tx, ty, height=17.0, crown_r=4.6, tex_crown=TEX["tree_2"], z0=1.0 / 12.0)

    mb.spot_ft("ext_west_4th_shamrock", 164.0, 768.0, 5.5, yaw=135.0, kind="exterior", desc="Diamond Shamrock & One Stop at SW Union/E 4th")
    mb.spot_ft("ext_west_dg_market", 146.0, 1198.0, 5.5, yaw=180.0, kind="exterior", desc="DG market plaza facing West across Union Ave")


# ---------------------------------------------------------------------------
# Top-Level Entry Point
# ---------------------------------------------------------------------------
def build_west_union(mb: MapBuilder) -> None:
    """Build all West S Union Ave & West Residential Neighborhood parcels into ``mb``."""
    _build_north_belle_commercial(mb)
    _build_891_billboard_lot(mb)
    _build_ramos_tires(mb)
    _build_compas_auto(mb)
    _build_super8_motel(mb)
    _build_south_amador_windbreak(mb)
    _build_west_residential(mb)
    _build_north_4th_to_hy1(mb)


# ---------------------------------------------------------------------------
# Standalone Validation Harness
# ---------------------------------------------------------------------------
def _overlaps_box(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> bool:
    """Return True if two XY rectangles overlap with > 0.05 ft penetration."""
    return (
        min(a[2], b[2]) - max(a[0], b[0]) > 0.05
        and min(a[3], b[3]) - max(a[1], b[1]) > 0.05
    )


def _check_west_union_bounds(mb: MapBuilder) -> Tuple[int, int, List[str]]:
    """Verify every brush stays inside [-490,172]x[-820,HY1] and clears forbidden zones."""
    errs: List[str] = []
    cx0, cy0, cx1, cy1 = CASINO_LOT_FT
    forbidden: List[Tuple[str, Tuple[float, float, float, float]]] = [
        ("CASINO_LOT_FT", (cx0, cy0, cx1, cy1)),
        ("E 4th St", (HX0, E_4TH_ST_CORRIDOR_Y[0], 172.0, E_4TH_ST_CORRIDOR_Y[1])),
        ("E Belle Terrace", (-490.0, 532.0, 172.0, 582.0)),
        ("Trinity Ave", (-490.0, -166.0, -102.0, -125.0)),
        ("Delaware St", (-143.0, -751.0, -102.0, -125.0)),
        ("Mariposa Ave", (-490.0, -476.0, -102.0, -436.0)),
        ("Amador Ave", (-490.0, -786.0, 172.0, -746.0)),
    ]

    checked = 0
    total_faces = 0
    for grp, blist in getattr(mb, "_brushes", {}).items():
        for idx, (bbox_u, planes) in enumerate(blist):
            checked += 1
            total_faces += len(planes)
            x0, y0, _, x1, y1, _ = (c / U_FT for c in bbox_u)
            if x0 < HX0 - 0.01 or x1 > 172.01 or y0 < HY0 - 0.01 or y1 > HY1 + 0.01:
                errs.append(f"[{grp}#{idx}] out of West Union bounds: ({x0:.2f},{y0:.2f})..({x1:.2f},{y1:.2f})")
            for fname, fbox in forbidden:
                if _overlaps_box((x0, y0, x1, y1), fbox):
                    errs.append(f"[{grp}#{idx}] ({x0:.2f},{y0:.2f})..({x1:.2f},{y1:.2f}) overlaps {fname} {fbox}")
                    break
    return checked, total_faces, errs


if __name__ == "__main__":
    mb = MapBuilder()
    build_west_union(mb)
    val_errs = mb.validate_all()
    checked_brushes, total_faces, bnd_errs = _check_west_union_bounds(mb)
    stats = mb.stats() if hasattr(mb, "stats") else {}
    print("=== gw_west_union.py standalone validation ===")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"  checked_brushes: {checked_brushes}")
    print(f"  total_faces: {total_faces}")
    print(f"  validate_all errors: {len(val_errs)}")
    for e in val_errs[:25]:
        print("   VAL ERR:", e)
    print(f"  bounds/exclusion errors: {len(bnd_errs)}")
    for e in bnd_errs[:25]:
        print("   BND ERR:", e)
    if checked_brushes == 0 or val_errs or bnd_errs:
        sys.exit(1)
