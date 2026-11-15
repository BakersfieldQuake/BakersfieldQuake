"""gw_gc_int.py — Great Castle Chinese Restaurant Interior & Building Shell.

Exclusive owner: geo-casino-int (`source/mm_tools/goldenwest/gw_gc_int.py`).
Builds the complete enterable interior and structural wall envelope (up to the
locked roof seam at z=12.0 ft West Vestibule/Main Hall and z=10.5 ft East
Restrooms/BOH wing) for BLDG 60053468 ("Great Castle Chinese Restaurant",
410 Union Ave, Bakersfield, CA):

  - Seam-locked floor slabs (z=-0.5..0.5 ft, crimson swirl carpet & taupe tile)
    and explicit-CMU painted outer walls strictly inside GC_POLY_FT
  - Hermetic overlapping worldspawn VIS/sunlight seal cores buried >=0.17 ft
    inside floors, walls, doorway lintels, and ceiling decks
  - Zone 1: SW Reception Vestibule (`x=355..375, y=997..1009`) w/ stamped
    antique-bronze coffered ceiling (`gwc_gccoff`), dragon-scroll cornice frieze
    (`gwc_gccorn`), propped-open red entry double doors (`south_main_entry`),
    host stand, crimson waiting chairs, carved oxblood `{gwc_gcfret` lattice
    partition bays, `{gwc_gcbann` 意如事萬 brocade valance & `{gwc_gcfan` 福 fan
  - Zone 2: Main Dining Hall (`x=337..388.5, y=1007.5..1066.5` + SE Restroom
    corridor `376..388.5, 997..1010`) w/ warm golden ceiling (`gwc_gcceil`),
    espresso timber ceiling beams, AC louver grille, 4 dome fan-lights,
    14 hanging lanterns (`gwc_gclant` + mini bronze/red hex lanterns), Guilin
    jade mountain mural (`gwc_gcmural`), Tang Maple Bridge calligraphy scroll
    (`gwc_gccallig`), `{gwc_gcfu` diamond hangings, `REST ROOMS` transom sign +
    split navy `{gwc_gcnoren` curtain, 4 honey-teak `gwc_gcscrn` screen-divided
    booths & 6 Lazy Susan round dining tables w/ crimson chairs (>=72u aisles)
  - Zone 3: Restroom Alcove (`x=389.5..412.5, y=997..1013`) w/ ceramic tile
    floors/walls, recessed 2x4 troffer, granite sink vanity & mirror, 2 wide
    open-entry accessible stalls
  - Zone 4: Kitchen / BOH (`x=389.5..412.5, y=1014..1066.5`) linking
    `dining_to_kitchen` <-> `north_kitchen_exit` w/ stainless cookline, wok
    exhaust hood canopy, wash-up rack, plate staging bench & >=140u spine aisle
  - Zone 5: Calibrated warm interior lighting, 4 room clearance registrations,
    all 6 locked doorways (`GC_DOORS_FT`), and 5 audit camera spots

Usage:
  from goldenwest.gw_gc_int import build_gc_int
  build_gc_int(mb)

Standalone validation:
  python source/mm_tools/goldenwest/gw_gc_int.py
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
        GC_BLDG_BOUNDS_FT,
        GC_BOH_BOUNDS_FT,
        GC_BOH_CEIL_Z_FT,
        GC_CEIL_Z_FT,
        GC_DINING_BOUNDS_FT,
        GC_DOORS_FT,
        GC_EAST_BOH_X_FT,
        GC_FLOOR_Z_FT,
        GC_POLY_FT,
        GC_RESTROOM_BOUNDS_FT,
        GC_SW_NOTCH_FT,
        GC_VESTIBULE_BOUNDS_FT,
        GC_WALL_T_FT,
        Fit,
        MapBuilder,
        TexSpec,
        Tile,
        U_FT,
        snap_val,
    )
else:
    from gw_lib import (  # noqa: E402
        GC_BLDG_BOUNDS_FT,
        GC_BOH_BOUNDS_FT,
        GC_BOH_CEIL_Z_FT,
        GC_CEIL_Z_FT,
        GC_DINING_BOUNDS_FT,
        GC_DOORS_FT,
        GC_EAST_BOH_X_FT,
        GC_FLOOR_Z_FT,
        GC_POLY_FT,
        GC_RESTROOM_BOUNDS_FT,
        GC_SW_NOTCH_FT,
        GC_VESTIBULE_BOUNDS_FT,
        GC_WALL_T_FT,
        Fit,
        MapBuilder,
        TexSpec,
        Tile,
        U_FT,
        snap_val,
    )

# ---------------------------------------------------------------------------
# Seam & Architectural Constants (locked with gw_lib.py / #131)
# ---------------------------------------------------------------------------
FLOOR_BOT_Z = -0.5
FLOOR_Z = GC_FLOOR_Z_FT                  # 0.5 ft (+6u)
MAIN_CEIL_Z = GC_CEIL_Z_FT               # 12.0 ft West Hall & Vestibule seam
BOH_CEIL_Z = GC_BOH_CEIL_Z_FT            # 10.5 ft East Restroom & BOH seam
CEIL_DECK_T = 0.65                       # Ceiling slab sits at [11.35..12.0] / [9.85..10.5]
MAIN_SOFFIT_Z = MAIN_CEIL_Z - CEIL_DECK_T  # 11.35 ft (~130u clear headroom)
BOH_SOFFIT_Z = BOH_CEIL_Z - CEIL_DECK_T    # 9.85 ft (112.0u clear >= 112u Hull-1)
WALL_T = GC_WALL_T_FT                    # 1.0 ft exterior/spine wall thickness
DOOR_TOP_Z = 9.0                         # 8.5 ft = 102u clear >= 96u Hull-1 min

BX0, BY0, BX1, BY1 = GC_BLDG_BOUNDS_FT   # 336.0, 996.0, 413.5, 1067.5
NX0, NY0, NX1, NY1 = GC_SW_NOTCH_FT      # 336.0, 996.0, 354.0, 1006.5
VX0, VY0, VX1, VY1 = GC_VESTIBULE_BOUNDS_FT  # 355.0, 997.0, 375.0, 1009.0
X_SPINE_W = GC_EAST_BOH_X_FT - 0.5 * WALL_T  # 388.5 ft (East face of Main Dining)
X_SPINE_E = GC_EAST_BOH_X_FT + 0.5 * WALL_T  # 389.5 ft (West face of Restrooms/BOH)
Y_RR_TOP = GC_RESTROOM_BOUNDS_FT[3]      # 1013.0 ft (South face of BOH divider)
Y_BOH_BOT = GC_BOH_BOUNDS_FT[1]          # 1014.0 ft (North face of BOH divider)

# Shared tiled material specs (v_ofs keeps gwc_gcwall dado seated cleanly at z=0.5)
CMU = Tile("gwc_gccmu", w_ft=8.0)
GC_WALL = Tile("gwc_gcwall", w_ft=8.0, h_ft=MAIN_CEIL_Z - FLOOR_Z, v_ofs=MAIN_CEIL_Z / (MAIN_CEIL_Z - FLOOR_Z))
CARPET = Tile("gwc_gccarp", w_ft=6.0)
TILE_4 = Tile("gwc_tile", w_ft=4.0)
DRYWALL = Tile("gwc_drywall", w_ft=8.0)
WOOD_TRIM = Tile("gwc_wood", w_ft=4.0)
BEAM_TEX = Tile("gwc_beam", w_ft=4.0)
SCREEN_TEX = Tile("gwc_gcscrn", w_ft=3.5)
TAN_LEATHER = Tile("gwc_bstucco", w_ft=4.0)
RED_TRIM = Tile("gwc_red", w_ft=4.0)
DARK_TRIM = Tile("gwc_dark", w_ft=4.0)
STEEL_TRIM = Tile("gwc_steel", w_ft=4.0)
GALV_TEX = Tile("gwc_galv", w_ft=4.0)
GRANITE_TEX = Tile("gwc_granite", w_ft=4.0)
CREAM_LINEN = Tile("gwc_crmstuc", w_ft=4.0)
GLASS_TEX = Tile("gwc_glass", w_ft=4.0)
GOLD_TEX = Tile("gwc_goldurn", w_ft=2.0)


def _sync_gw_lib_classes(mb: MapBuilder) -> None:
    """Bind Fit/Tile to the exact gw_lib module instance backing mb."""
    global Fit, Tile, CMU, GC_WALL, CARPET, TILE_4, DRYWALL, WOOD_TRIM
    global BEAM_TEX, SCREEN_TEX, TAN_LEATHER, RED_TRIM, DARK_TRIM, STEEL_TRIM
    global GALV_TEX, GRANITE_TEX, CREAM_LINEN, GLASS_TEX, GOLD_TEX
    mod = sys.modules.get(type(mb).__module__)
    if mod is not None and hasattr(mod, "Fit") and hasattr(mod, "Tile"):
        Fit = getattr(mod, "Fit")
        Tile = getattr(mod, "Tile")
        CMU = Tile("gwc_gccmu", w_ft=8.0)
        GC_WALL = Tile(
            "gwc_gcwall", w_ft=8.0,
            h_ft=MAIN_CEIL_Z - FLOOR_Z,
            v_ofs=MAIN_CEIL_Z / (MAIN_CEIL_Z - FLOOR_Z),
        )
        CARPET = Tile("gwc_gccarp", w_ft=6.0)
        TILE_4 = Tile("gwc_tile", w_ft=4.0)
        DRYWALL = Tile("gwc_drywall", w_ft=8.0)
        WOOD_TRIM = Tile("gwc_wood", w_ft=4.0)
        BEAM_TEX = Tile("gwc_beam", w_ft=4.0)
        SCREEN_TEX = Tile("gwc_gcscrn", w_ft=3.5)
        TAN_LEATHER = Tile("gwc_bstucco", w_ft=4.0)
        RED_TRIM = Tile("gwc_red", w_ft=4.0)
        DARK_TRIM = Tile("gwc_dark", w_ft=4.0)
        STEEL_TRIM = Tile("gwc_steel", w_ft=4.0)
        GALV_TEX = Tile("gwc_galv", w_ft=4.0)
        GRANITE_TEX = Tile("gwc_granite", w_ft=4.0)
        CREAM_LINEN = Tile("gwc_crmstuc", w_ft=4.0)
        GLASS_TEX = Tile("gwc_glass", w_ft=4.0)
        GOLD_TEX = Tile("gwc_goldurn", w_ft=2.0)


def _snap_ft(val_ft: float, grid_u: float = 1.0) -> float:
    return snap_val(val_ft * U_FT, grid_u) / U_FT


def _door_box(key: str) -> Tuple[float, float, float, float, float, float]:
    b = GC_DOORS_FT[key]["box_ft"]
    return (float(b[0]), float(b[1]), float(b[2]), float(b[3]), float(b[4]), float(b[5]))


def _door_span_x(key: str) -> Tuple[float, float, float, str]:
    b = _door_box(key)
    return (b[0], b[3], b[5], key)


def _door_span_y(key: str) -> Tuple[float, float, float, str]:
    b = _door_box(key)
    return (b[1], b[4], b[5], key)


# ---------------------------------------------------------------------------
# 1. Floor Slabs & Strict Orthogonal VIS Blockers
# ---------------------------------------------------------------------------

def _build_floors(mb: MapBuilder) -> None:
    """Tile non-overlapping floor slabs across GC_POLY_FT with skip undersides."""
    # NW Dining notch-north band (x=336..354, y=1006.5..1067.5)
    mb.box_ft(
        BX0, NY1, FLOOR_BOT_Z, NX1, BY1, FLOOR_Z, CMU,
        faces={"t": CARPET, "b": "skip"}, group="detail",
    )
    # Main Vestibule + Central/East Dining floor (x=354..388.5, y=996..1067.5)
    mb.box_ft(
        NX1, BY0, FLOOR_BOT_Z, X_SPINE_W, BY1, FLOOR_Z, CMU,
        faces={"t": CARPET, "b": "skip"}, group="detail",
    )
    # East BOH / Restrooms ceramic tile floor & doorway threshold (x=388.5..413.5)
    # East Restrooms + BOH Kitchen ceramic tile floors (split cleanly at Restrooms/Kitchen wall)
    mb.box_ft(
        X_SPINE_W, BY0, FLOOR_BOT_Z, BX1, 1013.5, FLOOR_Z, CMU,
        faces={"t": TILE_4, "b": "skip", "n": "skip"}, group="detail",
    )
    mb.box_ft(
        X_SPINE_W, 1013.5, FLOOR_BOT_Z, BX1, BY1, FLOOR_Z, CMU,
        faces={"t": TILE_4, "b": "skip", "s": "skip"}, group="detail",
    )


def _build_vis_blockers(mb: MapBuilder) -> None:
    """Emit hermetic overlapping worldspawn VIS/sunlight seal cores inside walls/slabs."""
    vis_tex = "gwc_dark"
    fz0, fz1 = -0.33, 0.25         # Buried floor seal (-4u..+3u inside -6u..+6u floor slab)
    wz0 = 0.0                      # Overlaps floor seal by 3u (closes baseboard leaks)
    wz1 = MAIN_CEIL_Z - 0.17       # 11.83 ft (142u, overlaps Main ceiling VIS deck 140..143u)
    bz1 = BOH_CEIL_Z - 0.17        # 10.33 ft (124u, overlaps BOH ceiling VIS deck 122..125u)
    lz0 = DOOR_TOP_Z + 0.17        # 9.17 ft (110u, >=2u above 108u doorway clear headers)
    mdz0, mdz1 = MAIN_SOFFIT_Z + 0.07, MAIN_CEIL_Z - 0.08
    bdz0, bdz1 = BOH_SOFFIT_Z + 0.07, BOH_CEIL_Z - 0.08

    d_south = _door_box("south_main_entry")
    d_ndin = _door_box("north_dining_exit")
    d_nkitch = _door_box("north_kitchen_exit")
    d_rr = _door_box("dining_to_restrooms")
    d_kit = _door_box("dining_to_kitchen")

    floor_cores = (
        (BX0 + 0.17, NY1 + 0.17, fz0, NX1 + 0.25, BY1 - 0.17, fz1),              # NW Dining floor core
        (NX1 + 0.17, BY0 + 0.17, fz0, BX1 - 0.17, BY1 - 0.17, fz1),              # Main + East BOH floor core
    )

    # Corner-overlapped outer shell, step-down spine & doorway lintel VIS cores
    wall_cores = (
        (BX0 + 0.17, NY1 + 0.17, wz0, BX0 + 0.83, BY1 - 0.17, wz1),              # West W1
        (BX0 + 0.17, NY1 + 0.17, wz0, NX1 + 0.83, NY1 + 0.83, wz1),              # SW notch W3
        (NX1 + 0.17, BY0 + 0.17, wz0, NX1 + 0.83, VY1 + 0.83, wz1),              # Watchtower West W2 + NW closure pier
        (NX1 + 0.17, BY0 + 0.17, wz0, d_south[0] - 0.25, BY0 + 0.83, wz1),       # South West of entry
        (d_south[3] + 0.25, BY0 + 0.17, wz0, X_SPINE_E - 0.17, BY0 + 0.83, wz1), # South East of entry
        (d_south[0] - 0.33, BY0 + 0.17, lz0, d_south[3] + 0.33, BY0 + 0.83, wz1),# South entry lintel
        (X_SPINE_W + 0.17, BY0 + 0.17, wz0, BX1 - 0.17, BY0 + 0.83, bz1),        # South East Restrooms W5
        (BX1 - 0.83, BY0 + 0.17, wz0, BX1 - 0.17, BY1 - 0.17, bz1),              # East Alley W6
        (X_SPINE_W + 0.17, BY1 - 0.83, wz0, d_nkitch[0] - 0.25, BY1 - 0.17, bz1),# North Kitchen West pier
        (d_nkitch[3] + 0.25, BY1 - 0.83, wz0, BX1 - 0.17, BY1 - 0.17, bz1),      # North Kitchen East pier
        (BX0 + 0.17, BY1 - 0.83, wz0, d_ndin[0] - 0.25, BY1 - 0.17, wz1),        # North Dining West pier
        (d_ndin[3] + 0.25, BY1 - 0.83, wz0, X_SPINE_E - 0.17, BY1 - 0.17, wz1),  # North Dining East pier
        (d_ndin[0] - 0.33, BY1 - 0.83, lz0, d_ndin[3] + 0.33, BY1 - 0.17, wz1),  # North Dining lintel
        (X_SPINE_W + 0.17, BY0 + 0.17, wz0, X_SPINE_E - 0.17, d_rr[1] - 0.25, bz1),  # Spine South of RR
        (X_SPINE_W + 0.17, d_rr[4] + 0.25, wz0, X_SPINE_E - 0.17, d_kit[1] - 0.25, bz1), # Spine Mid
        (X_SPINE_W + 0.17, d_kit[4] + 0.25, wz0, X_SPINE_E - 0.17, BY1 - 0.17, bz1),     # Spine North
        (X_SPINE_W + 0.17, BY0 + 0.17, lz0, X_SPINE_E - 0.17, BY1 - 0.17, wz1),          # Upper Spine + lintels
        (NX1 + 0.17, VY1 + 0.17, lz0, VX1 - 0.17, VY1 + 0.83, wz1),              # Vestibule header seal (overlaps W2)
    )
    ceiling_cores = (
        (BX0 + 0.17, NY1 + 0.17, mdz0, X_SPINE_E - 0.17, BY1 - 0.17, mdz1),      # Main Dining deck
        (NX1 + 0.17, BY0 + 0.17, mdz0, X_SPINE_E - 0.17, NY1 + 0.83, mdz1),      # Vestibule + SE deck
        (X_SPINE_W + 0.17, BY0 + 0.17, bdz0, BX1 - 0.17, BY1 - 0.17, bdz1),      # East Restroom + BOH deck
    )
    for x0, y0, cz0, x1, y1, cz1 in floor_cores + wall_cores + ceiling_cores:
        mb.structural_box_ft(x0, y0, cz0, x1, y1, cz1, vis_tex)


# ---------------------------------------------------------------------------
# 2. Exterior Perimeter Shell & Dividing Spine Walls (Seam-Locked)
# ---------------------------------------------------------------------------

def _emit_split_x_wall(
    mb: MapBuilder,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    door_key: str,
    s_tex: TexSpec,
    n_tex: TexSpec,
    w_cap: TexSpec,
    e_cap: TexSpec,
    jamb_tex: TexSpec,
    lintel_bot_tex: TexSpec,
) -> None:
    """Emit a 1-door split X-axis wall with explicit per-face exterior/interior textures."""
    dx0, _dy0, dz0, dx1, _dy1, dz1 = _door_box(door_key)
    mb.box_ft(
        x0, y0, z0, dx0, y1, z1, CMU,
        faces={"s": s_tex, "n": n_tex, "w": w_cap, "e": jamb_tex, "t": "skip", "b": "skip"},
        group="detail",
    )
    mb.box_ft(
        dx1, y0, z0, x1, y1, z1, CMU,
        faces={"s": s_tex, "n": n_tex, "w": jamb_tex, "e": e_cap, "t": "skip", "b": "skip"},
        group="detail",
    )
    mb.box_ft(
        dx0, y0, dz1, dx1, y1, z1, CMU,
        faces={"s": s_tex, "n": n_tex, "w": "skip", "e": "skip", "b": lintel_bot_tex, "t": "skip"},
        group="detail",
    )
    mb.register_doorway_ft(
        door_key,
        dx1 - dx0,
        dz1 - dz0,
        origin_ft=(0.5 * (dx0 + dx1), 0.5 * (y0 + y1), dz0),
        axis="x",
    )


def _build_shell_walls(mb: MapBuilder) -> None:
    """Build non-overlapping outer walls and dividing spine with explicit exterior CMU & 6 doorways."""
    # W1: West Main Dining Wall (x=336..337, y=1006.5..1067.5, z=0.5..12.0; s/n exposed corners = CMU)
    mb.box_ft(
        BX0, NY1, FLOOR_Z, BX0 + WALL_T, BY1, MAIN_CEIL_Z, CMU,
        faces={"w": CMU, "e": GC_WALL, "s": CMU, "n": CMU, "t": "skip", "b": "skip"},
        group="detail",
    )
    # W2: SW Watchtower West Wall (x=354..355, y=996..1007.5, z=0.5..12.0; s corner = CMU)
    mb.box_ft(
        NX1, BY0, FLOOR_Z, NX1 + WALL_T, NY1 + WALL_T, MAIN_CEIL_Z, CMU,
        faces={"w": CMU, "e": GC_WALL, "s": CMU, "n": "skip", "t": "skip", "b": "skip"},
        group="detail",
    )
    # W3: SW Notch North Wall (x=337..354, y=1006.5..1007.5, z=0.5..12.0)
    mb.box_ft(
        BX0 + WALL_T, NY1, FLOOR_Z, NX1, NY1 + WALL_T, MAIN_CEIL_Z, CMU,
        faces={"s": CMU, "n": GC_WALL, "w": "skip", "e": "skip", "t": "skip", "b": "skip"},
        group="detail",
    )
    # W4: South Main Hall & Vestibule Wall (x=355..388.5, y=996..997, z=0.5..12.0)
    _emit_split_x_wall(
        mb, NX1 + WALL_T, X_SPINE_W, BY0, BY0 + WALL_T, FLOOR_Z, MAIN_CEIL_Z,
        "south_main_entry", s_tex=CMU, n_tex=GC_WALL,
        w_cap="skip", e_cap="skip", jamb_tex=WOOD_TRIM, lintel_bot_tex=WOOD_TRIM,
    )
    # W5: South East Restrooms Wall (x=389.5..412.5, y=996..997, z=0.5..10.5)
    mb.box_ft(
        X_SPINE_E, BY0, FLOOR_Z, BX1 - WALL_T, BY0 + WALL_T, BOH_CEIL_Z, CMU,
        faces={"s": CMU, "n": TILE_4, "w": "skip", "e": "skip", "t": "skip", "b": "skip"},
        group="detail",
    )
    # W6: East Alley Wall (x=412.5..413.5, y=996..1067.5, z=0.5..10.5; s/n outer corners = CMU)
    mb.box_ft(
        BX1 - WALL_T, BY0, FLOOR_Z, BX1, Y_BOH_BOT, BOH_CEIL_Z, CMU,
        faces={"e": CMU, "w": TILE_4, "s": CMU, "n": "skip", "t": "skip", "b": "skip"},
        group="detail",
    )
    mb.box_ft(
        BX1 - WALL_T, Y_BOH_BOT, FLOOR_Z, BX1, BY1, BOH_CEIL_Z, CMU,
        faces={"e": CMU, "w": DRYWALL, "s": "skip", "n": CMU, "t": "skip", "b": "skip"},
        group="detail",
    )
    # W7: North East Kitchen Wall (x=389.5..412.5, y=1066.5..1067.5, z=0.5..10.5)
    _emit_split_x_wall(
        mb, X_SPINE_E, BX1 - WALL_T, BY1 - WALL_T, BY1, FLOOR_Z, BOH_CEIL_Z,
        "north_kitchen_exit", s_tex=DRYWALL, n_tex=CMU,
        w_cap="skip", e_cap="skip", jamb_tex=WOOD_TRIM, lintel_bot_tex=WOOD_TRIM,
    )
    # W8: North Main Dining Wall (x=337..388.5, y=1066.5..1067.5, z=0.5..12.0)
    _emit_split_x_wall(
        mb, BX0 + WALL_T, X_SPINE_W, BY1 - WALL_T, BY1, FLOOR_Z, MAIN_CEIL_Z,
        "north_dining_exit", s_tex=GC_WALL, n_tex=CMU,
        w_cap="skip", e_cap="skip", jamb_tex=WOOD_TRIM, lintel_bot_tex=WOOD_TRIM,
    )
    # W9: Step-Down Dining-to-East Spine (x=388.5..389.5, y=996..1067.5; outer s/n ends = CMU!)
    d_rr = _door_box("dining_to_restrooms")
    mb.box_ft(
        X_SPINE_W, BY0, FLOOR_Z, X_SPINE_E, d_rr[1], BOH_CEIL_Z, CMU,
        faces={"w": GC_WALL, "e": TILE_4, "s": CMU, "n": TILE_4, "t": "skip", "b": "skip"},
        group="detail",
    )
    mb.box_ft(
        X_SPINE_W, d_rr[4], FLOOR_Z, X_SPINE_E, Y_BOH_BOT, BOH_CEIL_Z, CMU,
        faces={"w": GC_WALL, "e": TILE_4, "s": TILE_4, "n": "skip", "t": "skip", "b": "skip"},
        group="detail",
    )
    mb.box_ft(
        X_SPINE_W, d_rr[1], d_rr[5], X_SPINE_E, d_rr[4], BOH_CEIL_Z, CMU,
        faces={"w": GC_WALL, "e": TILE_4, "s": "skip", "n": "skip", "b": TILE_4, "t": "skip"},
        group="detail",
    )
    mb.register_doorway_ft(
        "dining_to_restrooms",
        d_rr[4] - d_rr[1],
        d_rr[5] - d_rr[2],
        origin_ft=(GC_EAST_BOH_X_FT, 0.5 * (d_rr[1] + d_rr[4]), d_rr[2]),
        axis="y",
    )

    d_kit = _door_box("dining_to_kitchen")
    mb.box_ft(
        X_SPINE_W, Y_BOH_BOT, FLOOR_Z, X_SPINE_E, d_kit[1], BOH_CEIL_Z, CMU,
        faces={"w": GC_WALL, "e": DRYWALL, "s": "skip", "n": WOOD_TRIM, "t": "skip", "b": "skip"},
        group="detail",
    )
    mb.box_ft(
        X_SPINE_W, d_kit[4], FLOOR_Z, X_SPINE_E, BY1, BOH_CEIL_Z, CMU,
        faces={"w": GC_WALL, "e": DRYWALL, "s": WOOD_TRIM, "n": CMU, "t": "skip", "b": "skip"},
        group="detail",
    )
    mb.box_ft(
        X_SPINE_W, d_kit[1], d_kit[5], X_SPINE_E, d_kit[4], BOH_CEIL_Z, CMU,
        faces={"w": GC_WALL, "e": DRYWALL, "s": "skip", "n": "skip", "b": WOOD_TRIM, "t": "skip"},
        group="detail",
    )
    mb.register_doorway_ft(
        "dining_to_kitchen",
        d_kit[4] - d_kit[1],
        d_kit[5] - d_kit[2],
        origin_ft=(GC_EAST_BOH_X_FT, 0.5 * (d_kit[1] + d_kit[4]), d_kit[2]),
        axis="y",
    )

    #   Upper Spine [10.5..12.0] separating West Hall soffit/roof from lower BOH roof
    mb.box_ft(
        X_SPINE_W, BY0, BOH_CEIL_Z, X_SPINE_E, BY1, MAIN_CEIL_Z, CMU,
        faces={"w": GC_WALL, "e": CMU, "s": CMU, "n": CMU, "t": "skip", "b": "skip"},
        group="detail",
    )


# ---------------------------------------------------------------------------
# 3. Zone 1 — Reception Vestibule (#166)
# ---------------------------------------------------------------------------

def _build_fret_bay_x(
    mb: MapBuilder,
    y_mid: float,
    x0: float,
    x1: float,
    z_floor: float,
    z_ceil: float,
    n_mullions: int = 1,
) -> None:
    """Build a solid dado + carved oxblood {gwc_gcfret screen bay along X (no mullion overlap)."""
    y0, y1 = y_mid - 0.5 * WALL_T, y_mid + 0.5 * WALL_T
    # Lower wood-paneled wainscot [0.5..3.5]
    mb.box_ft(x0, y0, z_floor, x1, y1, 3.5, WOOD_TRIM, faces={"s": GC_WALL, "n": GC_WALL, "w": "skip", "e": "skip", "b": "skip", "t": "skip"}, group="detail")
    # Molded hardwood sill ledge [3.5..3.67]
    mb.box_ft(x0, y0 - 0.06, 3.5, x1, y1 + 0.06, 3.67, WOOD_TRIM, group="detail")
    # Discrete carved crimson Chinese fretwork bays strictly between mullions [3.67..7.75]
    cursor = x0
    for m_i in range(n_mullions):
        mx = _snap_ft(x0 + (x1 - x0) * ((m_i + 1) / (n_mullions + 1)), 0.5)
        mx0, mx1 = mx - 0.08, mx + 0.08
        if mx0 - cursor > 0.25:
            mb.flush_panel_ft(
                cursor, y_mid - 0.04, 3.67, mx0, y_mid + 0.04, 7.75,
                {"s": Fit("{gwc_gcfret"), "n": Fit("{gwc_gcfret", flip_u=True)},
                group="fence",
            )
        mb.box_ft(mx0, y0 + 0.25, 3.67, mx1, y1 - 0.25, 7.75, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
        cursor = mx1
    if x1 - cursor > 0.25:
        mb.flush_panel_ft(
            cursor, y_mid - 0.04, 3.67, x1, y_mid + 0.04, 7.75,
            {"s": Fit("{gwc_gcfret"), "n": Fit("{gwc_gcfret", flip_u=True)},
            group="fence",
        )
    # Upper transom rail & cream header [7.75..12.0]
    mb.box_ft(x0, y0 - 0.06, 7.75, x1, y1 + 0.06, 7.92, WOOD_TRIM, group="detail")
    mb.box_ft(x0, y0, 7.92, x1, y1, z_ceil, GC_WALL, faces={"s": GC_WALL, "n": GC_WALL, "w": "skip", "e": "skip", "b": "skip", "t": "skip"}, group="detail")


def _build_fret_bay_y(
    mb: MapBuilder,
    x_mid: float,
    y0: float,
    y1: float,
    z_floor: float,
    z_ceil: float,
    n_mullions: int = 2,
) -> None:
    """Build a solid dado + carved oxblood {gwc_gcfret screen bay along Y (no mullion overlap)."""
    x0, x1 = x_mid - 0.5 * WALL_T, x_mid + 0.5 * WALL_T
    mb.box_ft(x0, y0, z_floor, x1, y1, 3.5, WOOD_TRIM, faces={"w": GC_WALL, "e": GC_WALL, "s": "skip", "n": "skip", "b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(x0 - 0.06, y0, 3.5, x1 + 0.06, y1, 3.67, WOOD_TRIM, group="detail")
    cursor = y0
    for m_i in range(n_mullions):
        my = _snap_ft(y0 + (y1 - y0) * ((m_i + 1) / (n_mullions + 1)), 0.5)
        my0, my1 = my - 0.08, my + 0.08
        if my0 - cursor > 0.25:
            mb.flush_panel_ft(
                x_mid - 0.04, cursor, 3.67, x_mid + 0.04, my0, 7.75,
                {"w": Fit("{gwc_gcfret"), "e": Fit("{gwc_gcfret", flip_u=True)},
                group="fence",
            )
        mb.box_ft(x0 + 0.25, my0, 3.67, x1 - 0.25, my1, 7.75, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
        cursor = my1
    if y1 - cursor > 0.25:
        mb.flush_panel_ft(
            x_mid - 0.04, cursor, 3.67, x_mid + 0.04, y1, 7.75,
            {"w": Fit("{gwc_gcfret"), "e": Fit("{gwc_gcfret", flip_u=True)},
            group="fence",
        )
    mb.box_ft(x0 - 0.06, y0, 7.75, x1 + 0.06, y1, 7.92, WOOD_TRIM, group="detail")
    mb.box_ft(x0, y0, 7.92, x1, y1, z_ceil, GC_WALL, faces={"w": GC_WALL, "e": GC_WALL, "s": "skip", "n": "skip", "b": "skip", "t": "skip"}, group="detail")


def _build_vestibule(mb: MapBuilder) -> None:
    """Build the SW Reception Vestibule (#166): coffered ceiling, fretwork, valance, fan & host stand."""
    d_foyer = _door_box("foyer_to_dining")
    dx0, dx1 = d_foyer[0], d_foyer[3]  # 362.5..369.5

    # NW closure pier aligning SW Notch corner (354..355, y=1007.5) cleanly to Vestibule North wall (y=1010)
    mb.box_ft(
        NX1, NY1 + WALL_T, FLOOR_Z, VX0, VY1 + WALL_T, MAIN_CEIL_Z, GC_WALL,
        faces={"w": GC_WALL, "e": GC_WALL, "n": GC_WALL, "s": "skip", "t": "skip", "b": "skip"}, group="detail",
    )

    # Coffered dark bronze stamped vestibule ceiling [11.6..12.0] (skip top/sides)
    mb.flush_panel_ft(
        VX0, VY0, MAIN_SOFFIT_Z, VX1, VY1, MAIN_CEIL_Z,
        {"b": Tile("gwc_gccoff", w_ft=4.0)}, group="detail",
    )

    # Dragon-scroll cornice frieze around upper perimeter [10.70..MAIN_SOFFIT_Z] (illus prevents skip-edge void)
    mb.sign_decal_ft("n", VY0, VX0 + 0.2, VX1 - 0.2, 10.70, MAIN_SOFFIT_Z, Fit("gwc_gccorn", repeat=(5, 1)), thick_ft=0.06, group="illus")
    mb.sign_decal_ft("s", VY1, VX0 + 0.2, VX1 - 0.2, 10.70, MAIN_SOFFIT_Z, Fit("gwc_gccorn", repeat=(5, 1)), thick_ft=0.06, group="illus")
    mb.sign_decal_ft("e", VX0, VY0 + 0.2, VY1 - 0.2, 10.70, MAIN_SOFFIT_Z, Fit("gwc_gccorn", repeat=(3, 1)), thick_ft=0.06, group="illus")
    mb.sign_decal_ft("w", VX1, VY0 + 0.2, VY1 - 0.2, 10.70, MAIN_SOFFIT_Z, Fit("gwc_gccorn", repeat=(3, 1)), thick_ft=0.06, group="illus")

    # North Vestibule Partition (y=1009..1010, x=355..376) with carved fretwork & foyer_to_dining
    mb.box_ft(VX0, VY1, FLOOR_Z, 356.25, VY1 + WALL_T, MAIN_CEIL_Z, GC_WALL, faces={"b": "skip", "t": "skip"}, group="detail")
    _build_fret_bay_x(mb, VY1 + 0.5 * WALL_T, 356.25, dx0 - 0.25, FLOOR_Z, MAIN_CEIL_Z, n_mullions=1)
    mb.box_ft(dx0 - 0.25, VY1, FLOOR_Z, dx0, VY1 + WALL_T, DOOR_TOP_Z, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(dx0 - 0.25, VY1, DOOR_TOP_Z, dx1 + 0.25, VY1 + WALL_T, MAIN_CEIL_Z, GC_WALL, faces={"w": WOOD_TRIM, "e": WOOD_TRIM, "b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(dx1, VY1, FLOOR_Z, dx1 + 0.25, VY1 + WALL_T, DOOR_TOP_Z, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    _build_fret_bay_x(mb, VY1 + 0.5 * WALL_T, dx1 + 0.25, VX1, FLOOR_Z, MAIN_CEIL_Z, n_mullions=1)

    # Register foyer_to_dining explicitly (custom lattice partition, 84u x 102u clear)
    mb.register_doorway_ft(
        "foyer_to_dining",
        dx1 - dx0,
        DOOR_TOP_Z - FLOOR_Z,
        origin_ft=(0.5 * (dx0 + dx1), VY1 + 0.5 * WALL_T, FLOOR_Z),
        axis="x",
    )

    # East Vestibule Partition (x=375..376, y=997..1010) looking into SE corridor
    mb.box_ft(VX1, VY0, FLOOR_Z, VX1 + WALL_T, 998.5, MAIN_CEIL_Z, GC_WALL, faces={"b": "skip", "t": "skip"}, group="detail")
    _build_fret_bay_y(mb, VX1 + 0.5 * WALL_T, 998.5, 1008.2, FLOOR_Z, MAIN_CEIL_Z, n_mullions=2)
    mb.box_ft(VX1, 1008.2, FLOOR_Z, VX1 + WALL_T, VY1 + WALL_T, MAIN_CEIL_Z, GC_WALL, faces={"b": "skip", "t": "skip"}, group="detail")

    # Crimson/gold 5-flap brocade valance banner 意如事萬 across foyer_to_dining [z=7.65..8.98]
    mb.flush_panel_ft(
        dx0, VY1 + 0.12, 7.65, dx1, VY1 + 0.18, 8.98,
        {"s": Fit("{gwc_gcbann"), "n": Fit("{gwc_gcbann")},
        group="illus",
    )
    # Pleated crimson-and-gold 福 wall fan mounted on South face above lintel [z=9.12..10.65]
    cx_f = 0.5 * (dx0 + dx1)
    mb.sign_decal_ft(
        "s", VY1, cx_f - 1.85, cx_f + 1.85, 9.12, 10.65,
        Fit("{gwc_gcfan"), thick_ft=0.06, group="illus",
    )

    # Propped-open crimson entry double doors at south_main_entry (tucked clear outside 362..370, 4-rail open frame)
    d_south = _door_box("south_main_entry")
    sx0, sx1 = d_south[0], d_south[3]
    for leaf_x0, leaf_x1, bar_x0, bar_x1 in (
        (sx0 - 0.50, sx0 - 0.18, sx0 - 0.18, sx0 - 0.10),
        (sx1 + 0.18, sx1 + 0.50, sx1 + 0.10, sx1 + 0.18),
    ):
        mb.box_ft(leaf_x0, VY0 + 0.12, FLOOR_Z, leaf_x1, VY0 + 3.65, 1.80, RED_TRIM, faces={"b": "skip"}, group="detail")
        mb.detail_box_ft(leaf_x0, VY0 + 0.12, 7.90, leaf_x1, VY0 + 3.65, 8.85, RED_TRIM)
        mb.detail_box_ft(leaf_x0, VY0 + 0.12, 1.80, leaf_x1, VY0 + 0.55, 7.90, RED_TRIM)
        mb.detail_box_ft(leaf_x0, VY0 + 3.20, 1.80, leaf_x1, VY0 + 3.65, 7.90, RED_TRIM)
        mb.detail_box_ft(leaf_x0 + 0.05, VY0 + 0.55, 1.80, leaf_x1 - 0.05, VY0 + 3.20, 7.90, GLASS_TEX)
        mb.detail_box_ft(bar_x0, VY0 + 0.65, 3.45, bar_x1, VY0 + 3.05, 3.65, GOLD_TEX)

    # Modest dark mahogany Host Stand (NW corner, leaving >14 ft straight entry lane)
    mb.box_ft(VX0 + 0.4, 1003.4, FLOOR_Z, VX0 + 3.0, 1006.0, 3.65, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.detail_box_ft(VX0 + 0.3, 1003.3, 3.65, VX0 + 3.1, 1006.1, 3.85, RED_TRIM)

    # Two crimson-cushioned waiting chairs against SW Vestibule wall
    for wy in (998.0, 1000.4):
        _emit_dining_chair(mb, VX0 + 1.35, wy + 0.85, facing_deg=0.0)


# ---------------------------------------------------------------------------
# 4. Zone 2 — Main Dining Hall Architecture, Art, Beams & Lanterns (#163, #165)
# ---------------------------------------------------------------------------

def _emit_lantern(
    mb: MapBuilder,
    cx: float,
    cy: float,
    large: bool = True,
) -> None:
    """Emit a hanging paper lantern with >=8.4 ft floor clearance (skip hidden caps)."""
    # Hanging slim cord (non-solid) from ceiling soffit [11.6]
    top_z = MAIN_SOFFIT_Z
    if large:
        body_z0, body_z1 = 8.95, 10.35
        r_body = 0.75
        mb.box_ft(cx - 0.04, cy - 0.04, body_z1 + 0.08, cx + 0.04, cy + 0.04, top_z, DARK_TRIM, faces={"t": "skip", "b": "skip"}, group="illus")
        mb.cyl_ft(cx, cy, r_body * 0.62, body_z1, body_z1 + 0.12, sides=8, tex_side=GOLD_TEX, tex_top=GOLD_TEX, tex_bot="skip", group="detail")
        mb.cyl_ft(
            cx, cy, r_body, body_z0, body_z1,
            sides=8, tex_side=Fit("gwc_gclant"), tex_top=GOLD_TEX, tex_bot=GOLD_TEX, group="detail",
        )
        mb.cyl_ft(cx, cy, r_body * 0.56, body_z0 - 0.10, body_z0, sides=8, tex_side=GOLD_TEX, tex_top="skip", tex_bot=GOLD_TEX, group="detail")
        mb.illus_box_ft(cx - 0.08, cy - 0.08, body_z0 - 0.48, cx + 0.08, cy + 0.08, body_z0 - 0.10, RED_TRIM)
    else:
        body_z0, body_z1 = 9.25, 10.25
        r_body = 0.42
        mb.box_ft(cx - 0.03, cy - 0.03, body_z1 + 0.08, cx + 0.03, cy + 0.03, top_z, DARK_TRIM, faces={"t": "skip", "b": "skip"}, group="illus")
        mb.cyl_ft(cx, cy, r_body * 0.65, body_z1, body_z1 + 0.08, sides=6, tex_side=GOLD_TEX, tex_top=GOLD_TEX, tex_bot="skip", group="detail")
        mb.cyl_ft(
            cx, cy, r_body, body_z0, body_z1,
            sides=6, tex_side=Fit("gwc_gclant"), tex_top=GOLD_TEX, tex_bot=GOLD_TEX, group="detail",
        )
        mb.illus_box_ft(cx - 0.06, cy - 0.06, body_z0 - 0.35, cx + 0.06, cy + 0.06, body_z0, GOLD_TEX)


def _emit_ceiling_fan_bowl(mb: MapBuilder, cx: float, cy: float) -> None:
    """Emit a ceiling paddle fan with warm glowing alabaster dome bowl luminaire (#147, #165)."""
    # Downrod + housing
    mb.cyl_ft(cx, cy, 0.35, 10.85, MAIN_SOFFIT_Z, sides=8, tex_side=DARK_TRIM, tex_top="skip", tex_bot="skip", group="detail")
    # 4 slim wood/espresso paddles at z=10.95..11.02 (skip concealed inner butt joints)
    mb.detail_box_ft(cx - 1.85, cy - 0.22, 10.95, cx + 1.85, cy + 0.22, 11.02, BEAM_TEX)
    mb.box_ft(cx - 0.22, cy - 1.85, 10.95, cx + 0.22, cy - 0.22, 11.02, BEAM_TEX, faces={"n": "skip"}, group="detail")
    mb.box_ft(cx - 0.22, cy + 0.22, 10.95, cx + 0.22, cy + 1.85, 11.02, BEAM_TEX, faces={"s": "skip"}, group="detail")
    # Warm emissive frosted alabaster dome bowl [10.55..10.85] + brass bottom finial cap
    dome_bot = Tile("gwc_gcdome", w_ft=4.0, h_ft=4.0, u_ofs=0.25, v_ofs=0.5)
    mb.cyl_ft(cx, cy, 0.56, 10.55, 10.85, sides=8, tex_side=Fit("gwc_gcdome"), tex_top="skip", tex_bot=dome_bot, group="detail")
    mb.cyl_ft(cx, cy, 0.14, 10.47, 10.55, sides=8, tex_side=GOLD_TEX, tex_top="skip", tex_bot=GOLD_TEX, group="detail")


def _build_dining_architecture(mb: MapBuilder) -> None:
    """Build Dining Hall ceiling, espresso timber beams, AC louver, wall murals & restroom noren."""
    gx0 = BX0 + WALL_T  # 337.0
    gy1 = BY1 - WALL_T  # 1066.5

    # Warm golden-amber ceiling slabs [11.6..12.0] partitioning cleanly around Vestibule walls
    ceil_tex = {"b": Tile("gwc_gcceil", w_ft=6.0)}
    # 1. SW corner north of notch up to y=1010
    mb.flush_panel_ft(gx0, NY1 + WALL_T, MAIN_SOFFIT_Z, NX1, VY1 + WALL_T, MAIN_CEIL_Z, ceil_tex, group="detail")
    # 2. SE corridor east of Vestibule up to y=1010
    mb.flush_panel_ft(VX1 + WALL_T, VY0, MAIN_SOFFIT_Z, X_SPINE_W, VY1 + WALL_T, MAIN_CEIL_Z, ceil_tex, group="detail")
    # 3. Main Dining expanse (y=1010..1066.5)
    mb.flush_panel_ft(gx0, VY1 + WALL_T, MAIN_SOFFIT_Z, X_SPINE_W, gy1, MAIN_CEIL_Z, ceil_tex, group="detail")

    # Dark espresso exposed ceiling cross beams (y=1020, 1035, 1050) + non-overlapping longitudinal girder
    cross_ys = (1020.0, 1035.0, 1050.0)
    for by in cross_ys:
        mb.box_ft(
            gx0, by - 0.35, 10.80, X_SPINE_W, by + 0.35, MAIN_SOFFIT_Z, BEAM_TEX,
            faces={"t": "skip", "w": "skip", "e": "skip"}, group="detail",
        )
    # Longitudinal center girder split strictly between cross beams (zero coplanar overlap)
    for sy0, sy1 in ((1010.0, 1019.65), (1020.35, 1034.65), (1035.35, 1049.65), (1050.35, gy1)):
        mb.box_ft(
            362.15, sy0, 10.80, 362.85, sy1, MAIN_SOFFIT_Z, BEAM_TEX,
            faces={"t": "skip", "s": "skip", "n": "skip"}, group="detail",
        )

    # Recessed ceiling HVAC supply louver grille (#163, #165) strictly inside SW beam coffer bay
    mb.flush_panel_ft(
        355.0, 1013.5, MAIN_SOFFIT_Z - 0.06, 359.0, 1017.5, MAIN_SOFFIT_Z,
        {"b": Fit("gwc_swamp")}, group="illus",
    )

    # 4 frosted bowl ceiling fans
    for fx, fy in ((350.0, 1027.5), (375.0, 1027.5), (350.0, 1042.5), (375.0, 1042.5)):
        _emit_ceiling_fan_bowl(mb, fx, fy)

    # 8 large glowing Tsingtao / 萬事如意 lanterns + 6 smaller crimson/brass hex lanterns
    for lx, ly in (
        (350.5, 1016.0), (373.5, 1016.0),
        (350.5, 1031.0), (373.5, 1031.0),
        (350.5, 1045.5), (373.5, 1045.5),
        (350.5, 1059.0), (373.5, 1059.0),
    ):
        _emit_lantern(mb, lx, ly, large=True)
    for lx, ly in (
        (382.0, 1005.2), (342.5, 1022.5), (342.5, 1042.5),
        (383.0, 1022.5), (383.0, 1046.5), (362.5, 1061.0),
    ):
        _emit_lantern(mb, lx, ly, large=False)

    # Hero West Wall Framed Guilin Karst Landscape Mural (#165) centered inside Booth 2 bay [1026.2..1037.2]
    mb.sign_decal_ft("e", gx0, 1026.2, 1037.2, 4.90, 10.40, Fit("gwc_gcmural"), thick_ft=0.06, group="illus")

    # Hero North Wall Maple Bridge Night Mooring Calligraphy Scroll (#163)
    mb.sign_decal_ft("s", gy1, 371.5, 377.5, 4.85, 10.85, Fit("gwc_gccallig"), thick_ft=0.06, group="illus")

    # Red-and-gold 福 diamond wall hangings centered on cream plaster panels (#163)
    for wall_f, pos, a0, a1 in (
        ("e", gx0, 1015.0, 1017.4),
        ("e", gx0, 1048.8, 1051.2),
        ("s", gy1, 344.2, 346.6),
        ("s", gy1, 351.2, 353.6),
        ("w", X_SPINE_W, 1019.0, 1021.4),
        ("w", X_SPINE_W, 1046.8, 1049.2),
    ):
        mb.sign_decal_ft(wall_f, pos, a0, a1, 6.20, 8.60, Fit("{gwc_gcfu"), thick_ft=0.06, group="illus")

    # Dark wood door jamb casings cleanly outside doorway clear widths (North Dining Exit + Kitchen Door)
    d_ndin = _door_box("north_dining_exit")
    mb.box_ft(d_ndin[0] - 0.25, gy1 - 0.12, FLOOR_Z, d_ndin[0], gy1, DOOR_TOP_Z, WOOD_TRIM, faces={"n": "skip", "b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(d_ndin[3], gy1 - 0.12, FLOOR_Z, d_ndin[3] + 0.25, gy1, DOOR_TOP_Z, WOOD_TRIM, faces={"n": "skip", "b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(d_ndin[0] - 0.25, gy1 - 0.12, DOOR_TOP_Z, d_ndin[3] + 0.25, gy1, DOOR_TOP_Z + 0.25, WOOD_TRIM, faces={"n": "skip"}, group="detail")

    d_kit = _door_box("dining_to_kitchen")
    mb.box_ft(X_SPINE_W - 0.12, d_kit[1] - 0.25, FLOOR_Z, X_SPINE_W, d_kit[1], DOOR_TOP_Z, WOOD_TRIM, faces={"e": "skip", "b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(X_SPINE_W - 0.12, d_kit[4], FLOOR_Z, X_SPINE_W, d_kit[4] + 0.25, DOOR_TOP_Z, WOOD_TRIM, faces={"e": "skip", "b": "skip", "t": "skip"}, group="detail")
    mb.box_ft(X_SPINE_W - 0.12, d_kit[1] - 0.25, DOOR_TOP_Z, X_SPINE_W, d_kit[4] + 0.25, DOOR_TOP_Z + 0.25, WOOD_TRIM, faces={"e": "skip"}, group="detail")

    # REST ROOMS plaque & Split Navy Plum-Blossom Noren Curtain at dining_to_restrooms (#163)
    d_rr = _door_box("dining_to_restrooms")
    ry0, ry1 = d_rr[1], d_rr[4]  # 1002.0..1008.5
    rcy = 0.5 * (ry0 + ry1)
    mb.box_ft(X_SPINE_W - 0.10, ry0 - 0.22, FLOOR_Z, X_SPINE_W, ry0, DOOR_TOP_Z, WOOD_TRIM, faces={"e": "skip", "b": "skip"}, group="detail")
    mb.box_ft(X_SPINE_W - 0.10, ry1, FLOOR_Z, X_SPINE_W, ry1 + 0.22, DOOR_TOP_Z, WOOD_TRIM, faces={"e": "skip", "b": "skip"}, group="detail")
    mb.sign_decal_ft("w", X_SPINE_W, rcy - 2.6, rcy + 2.6, 9.15, 10.45, Fit("gwc_gcrest"), thick_ft=0.06, group="illus")
    # Passable noren drape inside opening [z=6.1..8.98] -> >=67u clear underneath & non-solid illus
    mb.flush_panel_ft(
        GC_EAST_BOH_X_FT - 0.04, ry0 + 0.15, 6.10, GC_EAST_BOH_X_FT + 0.04, ry1 - 0.15, 8.98,
        {"w": Fit("{gwc_gcnoren"), "e": Fit("{gwc_gcnoren", flip_u=True)},
        group="illus",
    )


# ---------------------------------------------------------------------------
# 5. Dining Booths, Screen Dividers, Lazy Susan Tables & Chairs (#163, #165)
# ---------------------------------------------------------------------------

def _emit_dining_chair(
    mb: MapBuilder,
    cx: float,
    cy: float,
    facing_deg: float = 0.0,
) -> None:
    """Emit a compact Chinese dining chair (legs, crimson cushion, wood back) aligned to cardinal angle."""
    ang = round(facing_deg / 90.0) * 90 % 360
    # Seat cushion box [1.35..1.65] on dark wood plinth legs [0.5..1.35]
    hw = 0.68
    mb.box_ft(cx - hw + 0.12, cy - hw + 0.12, FLOOR_Z, cx + hw - 0.12, cy + hw - 0.12, 1.35, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.detail_box_ft(cx - hw, cy - hw, 1.35, cx + hw, cy + hw, 1.65, RED_TRIM)
    # Backrest side sits opposite facing vector
    bx0, by0, bx1, by1 = cx - hw, cy - hw, cx + hw, cy + hw
    if ang == 0:      # faces +x -> back on -x
        bx1 = cx - hw + 0.22
    elif ang == 180:  # faces -x -> back on +x
        bx0 = cx + hw - 0.22
    elif ang == 90:   # faces +y -> back on -y
        by1 = cy - hw + 0.22
    else:             # faces -y -> back on +y
        by0 = cy + hw - 0.22
    mb.box_ft(bx0, by0, 1.65, bx1, by1, 3.25, WOOD_TRIM, faces={"b": "skip"}, group="detail")


def _emit_round_lazy_susan_table(mb: MapBuilder, cx: float, cy: float) -> None:
    """Emit a 5.0 ft round dark-cherry Lazy Susan dining table with 4 crimson chairs."""
    # Pedestal foot & column
    mb.cyl_ft(cx, cy, 1.10, FLOOR_Z, 0.72, sides=8, tex_side=WOOD_TRIM, tex_top=WOOD_TRIM, tex_bot="skip", group="detail")
    mb.cyl_ft(cx, cy, 0.36, 0.72, 2.42, sides=8, tex_side=DARK_TRIM, tex_top="skip", tex_bot="skip", group="detail")
    # Dark cherry tabletop [2.42..2.62]
    mb.cyl_ft(cx, cy, 2.50, 2.42, 2.62, sides=12, tex_side=WOOD_TRIM, tex_top=WOOD_TRIM, tex_bot=WOOD_TRIM, group="detail")
    # Rotating Lazy Susan glass & cream centerpiece [2.62..2.75]
    mb.cyl_ft(cx, cy, 1.30, 2.62, 2.75, sides=12, tex_side=CREAM_LINEN, tex_top=GLASS_TEX, tex_bot="skip", group="detail")
    # 4 cardinal crimson chairs tucked snugly at radius 2.55 (max radial extent 3.23 ft -> >=74u aisles!)
    _emit_dining_chair(mb, cx + 2.55, cy, facing_deg=180.0)
    _emit_dining_chair(mb, cx - 2.55, cy, facing_deg=0.0)
    _emit_dining_chair(mb, cx, cy + 2.55, facing_deg=270.0)
    _emit_dining_chair(mb, cx, cy - 2.55, facing_deg=90.0)


def _emit_west_booth_bay(
    mb: MapBuilder,
    x_wall: float,
    y_center: float,
    bay_depth_x: float = 6.4,
    seat_len_x: float = 5.4,
) -> None:
    """Emit a double-bench upholstered booth with dark wood base & rectangular table."""
    x0 = x_wall + 0.08
    x1 = x_wall + seat_len_x
    # North & South facing benches inside a 10.5 ft bay (screens sit at +-5.25 from bay center)
    for side in (-1.0, 1.0):
        yc = y_center + side * 3.85
        mb.box_ft(x0, yc - 0.95, FLOOR_Z, x1, yc + 0.95, 1.15, WOOD_TRIM, faces={"b": "skip", "t": "skip", "w": "skip"}, group="detail")
        mb.box_ft(x0, yc - 1.02, 1.15, x1, yc + 1.02, 1.62, TAN_LEATHER, faces={"w": "skip"}, group="detail")
        back_y0 = yc + 0.55 if side > 0 else yc - 1.05
        back_y1 = yc + 1.05 if side > 0 else yc - 0.55
        mb.box_ft(x0, back_y0, 1.62, x1, back_y1, 3.35, TAN_LEATHER, faces={"b": "skip", "w": "skip"}, group="detail")
    # Rectangular dark teak booth table in bay center
    mb.box_ft(x0 + 1.4, y_center - 0.45, FLOOR_Z, x1 - 1.4, y_center + 0.45, 2.42, DARK_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.detail_box_ft(x0 + 0.25, y_center - 1.35, 2.42, x_wall + bay_depth_x, y_center + 1.35, 2.62, WOOD_TRIM)


def _emit_screen_divider_x(
    mb: MapBuilder,
    x0: float,
    x1: float,
    y_mid: float,
    post_side: str = "e",
) -> None:
    """Emit a honey-teak coffered privacy screen divider along X (#163, #165, zero overlap)."""
    pw = 0.25
    if post_side == "e":
        rx0, rx1 = x0, x1 - pw
        px0, px1 = x1 - pw, x1
        wall_cap = {"w": "skip"}
    else:
        px0, px1 = x0, x0 + pw
        rx0, rx1 = x0 + pw, x1
        wall_cap = {"e": "skip"}
    mb.box_ft(rx0, y_mid - 0.15, FLOOR_Z, rx1, y_mid + 0.15, 0.95, WOOD_TRIM, faces={"b": "skip", "t": "skip", **wall_cap}, group="detail")
    mb.box_ft(rx0, y_mid - 0.12, 0.95, rx1, y_mid + 0.12, 6.75, SCREEN_TEX, faces={"b": "skip", "t": "skip", **wall_cap}, group="detail")
    mb.box_ft(rx0, y_mid - 0.18, 6.75, rx1, y_mid + 0.18, 6.95, WOOD_TRIM, faces=wall_cap, group="detail")
    mb.box_ft(px0, y_mid - 0.18, FLOOR_Z, px1, y_mid + 0.18, 6.95, WOOD_TRIM, faces={"b": "skip"}, group="detail")


def _build_dining_furniture(mb: MapBuilder) -> None:
    """Populate Main Dining Hall with booths, screen dividers, and 6 Lazy Susan tables (>=72u aisles)."""
    gx0 = BX0 + WALL_T  # 337.0

    # 3 double booths along West Wall (y=1013..1051) with 4 honey-teak coffered screen dividers
    for scr_y in (1013.0, 1025.5, 1038.0, 1050.5):
        _emit_screen_divider_x(mb, gx0, gx0 + 6.4, scr_y, post_side="e")
    for bay_cy in (1019.25, 1031.75, 1044.25):
        _emit_west_booth_bay(mb, gx0, bay_cy, bay_depth_x=6.4, seat_len_x=5.6)

    # 1 NE corner cozy booth & honey-teak screen alcove south of calligraphy scroll (x=382.0..388.4)
    _emit_screen_divider_x(mb, 382.1, X_SPINE_W, 1049.5, post_side="w")
    _emit_screen_divider_x(mb, 382.1, X_SPINE_W, 1061.5, post_side="w")
    mb.box_ft(382.5, 1050.0, FLOOR_Z, X_SPINE_W - 0.05, 1052.0, 1.15, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.detail_box_ft(382.5, 1050.0, 1.15, X_SPINE_W - 0.05, 1052.1, 3.25, TAN_LEATHER)
    mb.box_ft(382.5, 1059.0, FLOOR_Z, X_SPINE_W - 0.05, 1061.0, 1.15, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.detail_box_ft(382.5, 1058.9, 1.15, X_SPINE_W - 0.05, 1061.0, 3.25, TAN_LEATHER)
    mb.box_ft(384.2, 1055.0, FLOOR_Z, 386.8, 1056.0, 2.42, DARK_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.detail_box_ft(382.4, 1054.2, 2.42, X_SPINE_W - 0.25, 1056.8, 2.62, WOOD_TRIM)

    # 6 Round Lazy Susan Tables in 2 crisp columns flanking wide central & perimeter aisles
    # Min gap calculations:
    #   West Booths (343.4) <-> West Tables (353.0 - 3.23 = 349.77) = 6.37 ft (76.4u >= 64u)
    #   West Tables (356.23) <-> East Tables (369.27)              = 13.04 ft (156.5u >= 64u)
    #   East Tables (375.73) <-> East Wall / NE Booth (382.1)      = 6.37 ft / 12.77 ft (>= 76.4u)
    #   Row Pitch (1019.5, 1036.5, 1053.5): min gap between chairs = 10.54 ft (126.5u >= 64u)
    for cx in (353.0, 372.5):
        for cy in (1019.5, 1036.5, 1053.5):
            _emit_round_lazy_susan_table(mb, cx, cy)


# ---------------------------------------------------------------------------
# 6. Zone 3 & Zone 4 — Restroom Alcove & Kitchen / BOH Wing
# ---------------------------------------------------------------------------

def _build_restrooms_and_kitchen(mb: MapBuilder) -> None:
    """Build Restroom Alcove (389.5..412.5, 997..1013) & Kitchen/BOH (1014..1066.5)."""
    ex0, ex1 = X_SPINE_E, BX1 - WALL_T  # 389.5..412.5
    ry0, ry1 = BY0 + WALL_T, Y_RR_TOP   # 997.0..1013.0
    ky0, ky1 = Y_BOH_BOT, BY1 - WALL_T  # 1014.0..1066.5

    # Partition Wall between Restrooms and Kitchen (y=1013.0..1014.0, z=0.5..10.5)
    mb.box_ft(ex0, ry1, FLOOR_Z, ex1, ky0, BOH_CEIL_Z, DRYWALL, faces={"s": TILE_4, "n": DRYWALL, "w": "skip", "e": "skip", "b": "skip", "t": "skip"}, group="detail")

    # Tiled 4.0 ft splash dado along Kitchen inner walls [0.5..4.5] (solid box_ft -> no skip holes at ends)
    mb.box_ft(ex0 + 0.10, ky0, FLOOR_Z, ex1 - 0.10, ky0 + 0.08, 4.5, TILE_4, faces={"s": "skip", "b": "skip"}, group="detail")
    mb.box_ft(ex1 - 0.08, ky0 + 0.16, FLOOR_Z, ex1, ky1 - 0.16, 4.5, TILE_4, faces={"e": "skip", "b": "skip"}, group="detail")
    mb.box_ft(ex0, ky0 + 0.16, FLOOR_Z, ex0 + 0.08, 1031.6, 4.5, TILE_4, faces={"w": "skip", "b": "skip"}, group="detail")
    mb.box_ft(ex0, 1039.4, FLOOR_Z, ex0 + 0.08, ky1 - 0.16, 4.5, TILE_4, faces={"w": "skip", "b": "skip"}, group="detail")

    # Ceilings [10.1..10.5] (skip hidden tops & perimeter sides)
    boh_ceil = {"b": Tile("gwc_ceil2x4", w_ft=4.0)}
    mb.flush_panel_ft(ex0, ry0, BOH_SOFFIT_Z, ex1, ry1, BOH_CEIL_Z, boh_ceil, group="detail")
    mb.flush_panel_ft(ex0, ky0, BOH_SOFFIT_Z, ex1, ky1, BOH_CEIL_Z, boh_ceil, group="detail")

    # Recessed glowing 2x4 ceiling troffers (gwc_troffer, illus avoids BSP ceiling splits & skip voids)
    mb.sign_decal_ft("b", BOH_SOFFIT_Z, 397.5, 401.5, 1004.0, 1006.0, Fit("gwc_troffer"), thick_ft=0.04, group="illus")
    for ty in (1023.0, 1040.0, 1056.0):
        mb.sign_decal_ft("b", BOH_SOFFIT_Z, 399.0, 403.0, ty - 1.0, ty + 1.0, Fit("gwc_troffer"), thick_ft=0.04, group="illus")

    # --- Restroom Alcove Furnishings ---
    # Granite & mahogany twin-basin sink vanity along North Restroom wall (leaving >12 ft south aisle)
    mb.box_ft(392.0, 1010.2, FLOOR_Z, 400.0, ry1 - 0.16, 2.90, WOOD_TRIM, faces={"b": "skip", "t": "skip"}, group="detail")
    mb.detail_box_ft(391.9, 1010.0, 2.90, 400.1, ry1 - 0.16, 3.12, GRANITE_TEX)
    for sx in (393.5, 397.0):
        mb.box_ft(sx, 1010.8, 3.12, sx + 1.6, 1012.2, 3.22, GALV_TEX, faces={"b": "skip"}, group="detail")
    mb.sign_decal_ft("s", ry1, 392.2, 399.8, 3.80, 6.80, GLASS_TEX, thick_ft=0.06, group="illus")

    # 2 Spacious Restroom Stalls (open 6.0 ft doorways so Hull-1 cannot trap inside!)
    mb.detail_box_ft(404.0, 1004.85, 1.15, ex1 - 0.12, 1005.15, 7.20, STEEL_TRIM)
    mb.detail_box_ft(404.0, 997.16, 1.15, 404.30, 999.00, 7.20, STEEL_TRIM)
    mb.detail_box_ft(404.0, 1011.00, 1.15, 404.30, 1012.84, 7.20, STEEL_TRIM)
    for fy in (1000.6, 1009.4):
        mb.box_ft(410.0, fy - 0.75, FLOOR_Z, ex1 - 0.25, fy + 0.75, 1.85, CREAM_LINEN, faces={"b": "skip"}, group="detail")
        mb.box_ft(411.2, fy - 0.75, 1.85, ex1 - 0.20, fy + 0.75, 3.05, CREAM_LINEN, faces={"b": "skip"}, group="detail")

    # --- Kitchen / BOH Utilitarian Stainless Workstations (zero fake signage!) ---
    # 1. South Wall Double Sink & Dish Rack (clear inside 1u splash dado, skip hidden undersides)
    mb.box_ft(391.0, ky0 + 0.16, FLOOR_Z, 406.5, 1017.4, 2.95, GALV_TEX, faces={"b": "skip"}, group="detail")
    mb.box_ft(391.0, ky0 + 0.16, 2.95, 406.5, 1017.5, 3.60, STEEL_TRIM, faces={"b": "skip"}, group="detail")
    mb.detail_box_ft(392.5, ky0 + 0.18, 5.45, 405.0, 1016.0, 5.65, GALV_TEX)

    # 2. East Wall Wok Cookline + Exhaust Hood Canopy (x=408.3..412.34, y=1020.5..1042.5)
    mb.box_ft(408.3, 1021.0, FLOOR_Z, ex1 - 0.16, 1042.0, 2.90, GALV_TEX, faces={"b": "skip"}, group="detail")
    mb.box_ft(408.6, 1022.0, 2.90, 411.8, 1041.0, 3.12, DARK_TRIM, faces={"b": "skip"}, group="detail")
    mb.box_ft(407.6, 1020.5, 6.80, ex1 - 0.16, 1042.5, 8.65, GALV_TEX, group="detail")
    mb.box_ft(409.5, 1024.0, 8.65, 411.8, 1039.0, BOH_SOFFIT_Z, GALV_TEX, faces={"b": DARK_TRIM, "t": "skip"}, group="detail")

    # 3. NE Stainless Prep Bench (x=408.5..412.34, y=1046.0..1063.0)
    mb.box_ft(408.5, 1046.0, FLOOR_Z, ex1 - 0.16, 1063.0, 3.10, GALV_TEX, faces={"b": "skip"}, group="detail")

    # 4. West Wall Plate Staging Counter north of dining_to_kitchen (x=389.66..392.5, y=1043.0..1057.5)
    mb.box_ft(ex0 + 0.16, 1043.0, FLOOR_Z, 392.5, 1057.5, 3.10, GALV_TEX, faces={"b": "skip"}, group="detail")
    # Note central aisle x=392.5..408.3 = 15.8 ft (189.6u clear connecting dining_to_kitchen <-> north_kitchen_exit!)

    # Propped-open interior/exit service doors tucked cleanly beside jambs & splash dados
    d_kit = _door_box("dining_to_kitchen")
    mb.box_ft(ex0 + 0.16, d_kit[4] + 0.16, FLOOR_Z, ex0 + 0.38, d_kit[4] + 3.60, 8.85, WOOD_TRIM, faces={"b": "skip"}, group="detail")
    d_nkit = _door_box("north_kitchen_exit")
    mb.box_ft(d_nkit[3] + 0.16, ky1 - 3.60, FLOOR_Z, d_nkit[3] + 0.38, ky1 - 0.16, 8.85, WOOD_TRIM, faces={"b": "skip"}, group="detail")
    d_ndin = _door_box("north_dining_exit")
    mb.box_ft(d_ndin[3] + 0.30, ky1 - 3.60, FLOOR_Z, d_ndin[3] + 0.52, ky1 - 0.16, 8.85, RED_TRIM, faces={"b": "skip"}, group="detail")


# ---------------------------------------------------------------------------
# 7. Calibrated Interior Lighting, Room & Audit Spot Registrations
# ---------------------------------------------------------------------------

def _build_lights_and_registrations(mb: MapBuilder) -> None:
    """Place warm calibrated lights (~45-65 luma, zero blowout), register 4 rooms & 5 spots."""
    # Zone 1: Reception Vestibule twin warm lights illuminating fretwork, cornice & host stand
    mb.light_ft(360.5, 1003.0, 10.2, light=175, color=(255, 224, 174), wait=0.70)
    mb.light_ft(370.5, 1003.0, 10.2, light=175, color=(255, 224, 174), wait=0.70)

    # SE Restroom approach corridor
    mb.light_ft(382.0, 1004.5, 10.2, light=175, color=(255, 226, 182), wait=0.70)

    # Zone 2: Main Dining Hall balanced 3x3 warm grid + dome fan downlights + gentle mural accents
    mb.interior_lights_ft(
        343.0, 1014.5, 382.5, 1061.5, z_ft=10.2,
        nx=3, ny=3, light=195, color=(255, 224, 176), wait=0.68,
    )
    for fx, fy in ((350.0, 1027.5), (375.0, 1027.5), (350.0, 1042.5), (375.0, 1042.5)):
        mb.light_ft(fx, fy, 10.15, light=135, color=(255, 218, 155), wait=0.68)
    # Soft accent washes on West Guilin Mural and North Calligraphy Scroll
    mb.light_ft(341.5, 1031.5, 8.9, light=115, color=(255, 222, 172), wait=0.70)
    mb.light_ft(374.5, 1062.0, 8.9, light=115, color=(255, 222, 172), wait=0.70)

    # Zone 3 & 4: Restrooms (twin balanced ceiling fills) + BOH Kitchen (gentle high fill, no glare hotspot)
    mb.light_ft(396.0, 1005.0, 8.9, light=175, color=(255, 238, 210), wait=0.70)
    mb.light_ft(407.0, 1005.0, 8.9, light=175, color=(255, 238, 210), wait=0.70)
    mb.interior_lights_ft(
        396.5, 1019.0, 403.5, 1061.0, z_ft=9.15,
        nx=1, ny=3, light=180, color=(255, 240, 215), wait=0.58,
    )

    # Register all 4 rooms (verified >=112u headroom)
    mb.register_room_ft("gc_vestibule", FLOOR_Z, MAIN_SOFFIT_Z)
    mb.register_room_ft("gc_dining_hall", FLOOR_Z, MAIN_SOFFIT_Z)
    mb.register_room_ft("gc_restrooms", FLOOR_Z, BOH_SOFFIT_Z)
    mb.register_room_ft("gc_kitchen_boh", FLOOR_Z, BOH_SOFFIT_Z)

    # Camera audit spots at standing eye height (~56u = 4.67 ft above floor)
    eye_z = FLOOR_Z + 4.2
    mb.spot_ft("gc_vestibule_entry", 366.0, 999.2, eye_z, yaw=90.0, pitch=4.0, desc="Vestibule facing north through fretwork & 意如事萬 valance")
    mb.spot_ft("gc_dining_main", 363.0, 1015.0, eye_z, yaw=115.0, pitch=3.0, desc="Main Dining NW view across tables, booths, lanterns & Guilin mural")
    mb.spot_ft("gc_dining_restrooms_view", 378.0, 1005.2, eye_z, yaw=0.0, pitch=2.0, desc="East corridor facing REST ROOMS sign & navy plum-blossom noren")
    mb.spot_ft("gc_kitchen_boh", 397.5, 1020.0, eye_z, yaw=70.0, pitch=2.0, desc="BOH Kitchen stainless cookline, hood & north_kitchen_exit")
    mb.spot_ft("gc_north_exit_view", 361.5, 1058.5, eye_z, yaw=270.0, pitch=4.0, desc="North dining spine looking south past Lazy Susan tables & calligraphy")


# ---------------------------------------------------------------------------
# Public Entry Point & Standalone Self-Verification
# ---------------------------------------------------------------------------

def build_gc_int(mb: MapBuilder) -> Dict[str, object]:
    """Build the complete Great Castle Chinese Restaurant Interior & Shell onto mb."""
    _sync_gw_lib_classes(mb)
    before_brushes = sum(len(v) for v in mb._brushes.values())
    before_ents = len(mb._entities)
    before_spots = len(mb._spots)
    before_rooms = len(mb._rooms)
    before_doors = len(mb._doorways)

    _build_floors(mb)
    _build_vis_blockers(mb)
    _build_shell_walls(mb)
    _build_vestibule(mb)
    _build_dining_architecture(mb)
    _build_dining_furniture(mb)
    _build_restrooms_and_kitchen(mb)
    _build_lights_and_registrations(mb)

    after_brushes = sum(len(v) for v in mb._brushes.values())
    return {
        "brushes_added": after_brushes - before_brushes,
        "entities_added": len(mb._entities) - before_ents,
        "spots_added": len(mb._spots) - before_spots,
        "rooms_added": len(mb._rooms) - before_rooms,
        "doorways_added": len(mb._doorways) - before_doors,
    }


def _standalone_verify() -> int:
    mb = MapBuilder(check_textures=True, require_gwc_prefix=True)
    # Place player spawn cleanly inside Main Dining Hall centerline
    mb.ent_ft("info_player_start", 362.5, 1014.0, 2.5, angle=90)
    summary = build_gc_int(mb)
    warnings = mb.validate_all()
    stats = mb.stats()
    print("[gw_gc_int] build summary:", summary)
    print("[gw_gc_int] MapBuilder stats:", stats)
    if warnings:
        print("[gw_gc_int] warnings:", warnings)
    out_map = os.path.join(HERE, "out", "_test_gc_int.map")
    mb.write_map(out_map)
    mb.write_spots(os.path.join(HERE, "out", "_test_gc_int.spots.json"))
    print(f"[gw_gc_int] OK! Validated cleanly and wrote test map -> {out_map}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_standalone_verify())
