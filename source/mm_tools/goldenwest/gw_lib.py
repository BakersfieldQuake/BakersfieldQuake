"""gw_lib.py — Shared Bakersfield 1:1 Scale (12 Quake units/ft) Valve-220 MapBuilder,
Coordinate Contracts, WAD2/Bootstrap Texture Validation, and Hull-1 Navigation Guards
for the updated Golden West Casino & S Union Ave Quake map.

All 5 geometry modules (streets, casino_ext, casino_int, east_union, west_union)
MUST import coordinate constants, parcel boundaries, and MapBuilder from here so
the assembled map has zero seams, zero parcel overlaps, zero legacy bklan*/bk_*
textures, and deterministic Quake Hull-1 (32x32x56) player navigability.
"""
from __future__ import annotations

import json
import math
import os
import struct
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union


# ==============================================================================
# 1. SCALE, ORIGIN & WORLD BOUNDS
# ==============================================================================
U_FT: float = 12.0                         # Exact 1:1 Quake scale: 12 units per foot
M_PER_FT: float = 0.3048
FT_PER_M: float = 1.0 / M_PER_FT           # 3.280839895013123 ft/m
U_M: float = U_FT / M_PER_FT               # 39.37007874015748 units/m

# Origin (0, 0) in feet maps to Golden West Casino reference point
ORIGIN_LATLON: Tuple[float, float] = (35.345186, -119.0037921)
OX: float = 0.0
OY: float = 0.0
FOX_OFFSET_FT: Tuple[float, float] = (-1683.9, 11577.8)

# Full map envelope in feet (x in [-490, +650], y in [-820, +1340])
HX0: float = -490.0
HX1: float = 650.0
HY0: float = -820.0
HY1: float = 1340.0
SOUTH_ZONE_HY1: float = 750.0
SKY_Z: float = 142.0
SKY_Z_BOT: float = -24.0
WORLD_BOUNDS_FT: Tuple[float, float, float, float] = (HX0, HY0, HX1, HY1)

# Snapping & spatial chunking
WORLD_SNAP_U: float = 1.0
DETAIL_SNAP_U: float = 0.5
CHUNK_SIZE_M: float = 48.0
CHUNK_SIZE_FT: float = CHUNK_SIZE_M * FT_PER_M       # ~157.4803 ft
CHUNK_SIZE_U: float = CHUNK_SIZE_M * U_M             # ~1889.76 u
FENCE_CHUNK_SIZE_M: float = 52.0
FENCE_CHUNK_SIZE_U: float = FENCE_CHUNK_SIZE_M * U_M # ~2047.24 u (~170.60 ft)

# Default Bakersfield Sunny Sky & Sun Angle
SKY_NAME: str = "gwsky_"
SUN_AZIMUTH_DEG: float = 32.0                        # NE sun illuminating portico + Union
SUN_ELEVATION_DEG: float = 58.0
SUN_MANGLE: str = "212 -58 0"

# Quake Hull-1 (32x32x56 bbox) player navigability thresholds
HULL1_MIN_DOOR_W_U: float = 64.0                     # 5.333 ft minimum doorway clear width
HULL1_MIN_DOOR_H_U: float = 96.0                     # 8.000 ft minimum doorway clear height
HULL1_MAX_STEP_U: float = 18.0                       # 1.500 ft max Quake step-up height
HULL1_MIN_CEIL_U: float = 112.0                      # 9.333 ft minimum interior ceiling clear

# Special compiler/engine surface names (never looked up in WAD)
SPECIAL_TEXTURES = frozenset({"sky", "clip", "skip", "trigger"})

# Legacy textures strictly forbidden in the updated Golden West build
FORBIDDEN_TEX_PREFIXES: Tuple[str, ...] = (
    "bklan",
    "bk_",
    "{bk3_",
    "{bk",
    "{chain",
    "sky_bk",
)
MAX_TEX_NAME_LEN: int = 15

# Default paths resolved relative to this module (G:\Quake\Combat\BakersfieldQuake\source\mm_tools\goldenwest\)
GW_DIR: str = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR: str = os.path.dirname(GW_DIR)
MOD_DIR: str = os.path.dirname(os.path.dirname(MM_TOOLS_DIR))
TEX_DIR: str = os.path.join(MOD_DIR, "textures")
DEFAULT_WAD_PATH: str = os.path.join(MM_TOOLS_DIR, "out", "maps", "gw2.wad")
DEFAULT_WAD_PATHS: Tuple[str, ...] = (
    DEFAULT_WAD_PATH,
    os.path.join(GW_DIR, "out", "gw2.wad"),
    os.path.join(GW_DIR, "out", "maps", "gw2.wad"),
)


# ==============================================================================
# 2. EXACT BAKERSFIELD COORDINATE CONTRACTS (FEET)
# ==============================================================================

# --- S Union Ave (CA-99 BUS) 3+3 divided boulevard + raised red brick median ---
UNION_W_SIDEWALK_X: Tuple[float, float] = (172.0, 178.0)
UNION_SB_CARRIAGE_X: Tuple[float, float] = (178.0, 219.0)  # OSM WAY 244524856 centerline ~202.5, 3 SB lanes
UNION_MEDIAN_X: Tuple[float, float] = (219.0, 238.0)       # Raised red herringbone brick median
UNION_NB_CARRIAGE_X: Tuple[float, float] = (238.0, 277.0)  # OSM WAY 244531372 centerline ~254.0, 3 NB lanes
UNION_E_SIDEWALK_X: Tuple[float, float] = (277.0, 283.0)   # Utility poles at x ~= 282.0 ft
UNION_CORRIDOR_X: Tuple[float, float] = (172.0, 283.0)
UNION_SB_CENTER_X: float = 202.5
UNION_NB_CENTER_X: float = 254.0
UNION_POLE_X: float = 282.0

# --- Bakersfield GIS S Union Ave median tree & palm nodes (ft) ---
# North Casino / Star-Liter cluster: tall Washingtonia fan palms
MEDIAN_PALMS_NORTH_LOT_FT: Tuple[Tuple[float, float], ...] = (
    (236.8, 268.6),
    (235.6, 256.3),
    (235.6, 240.5),
    (237.6, 195.2),
    (237.4, 181.0),
)
# Casino NE frontage cluster: compact shrubs / ornamentals (never full-height trunks blocking signage)
MEDIAN_SHRUBS_CASINO_FRONT_FT: Tuple[Tuple[float, float], ...] = (
    (236.5, 120.9),
    (236.5, 110.2),
    (236.5, 101.0),
    (236.5, 89.6),
    (236.5, 79.8),
    (236.5, 62.8),
    (236.5, 42.8),
    (236.5, 22.4),
    (236.5, 3.1),
    (236.5, -5.1),
)
# South Casino / Ramos / Star-Liter South cluster: medium deciduous shade trees & shrubs
MEDIAN_TREES_SOUTH_FT: Tuple[Tuple[float, float], ...] = (
    (236.5, -73.0),
    (236.5, -107.0),
    (236.5, -180.3),
    (236.5, -238.5),
    (236.5, -250.2),
    (236.5, -260.0),
    (236.5, -312.3),
    (236.5, -324.2),
    (236.5, -336.1),
)

# --- Cross streets (exact OSM centers & road/sidewalk corridors in ft) ---
BELLE_TERRACE_Y: float = 557.7
BELLE_TERRACE_ROAD_Y: Tuple[float, float] = (538.0, 576.0)
BELLE_TERRACE_CORRIDOR_Y: Tuple[float, float] = (532.0, 582.0)

TRINITY_AVE_Y: float = -145.5
TRINITY_AVE_ROAD_Y: Tuple[float, float] = (-161.0, -130.0)
TRINITY_AVE_CORRIDOR_Y: Tuple[float, float] = (-166.0, -125.0)

DELAWARE_ST_X: float = -122.5
DELAWARE_ST_ROAD_X: Tuple[float, float] = (-138.0, -107.0)
DELAWARE_ST_CORRIDOR_X: Tuple[float, float] = (-143.0, -102.0)

MARIPOSA_AVE_Y: float = -456.5
MARIPOSA_AVE_ROAD_Y: Tuple[float, float] = (-471.0, -441.0)
MARIPOSA_AVE_CORRIDOR_Y: Tuple[float, float] = (-476.0, -436.0)

ADAMS_ST_Y: float = -576.0
ADAMS_ST_ROAD_Y: Tuple[float, float] = (-590.0, -560.0)
ADAMS_ST_CORRIDOR_Y: Tuple[float, float] = (-595.0, -555.0)

AMADOR_AVE_Y: float = -767.4
AMADOR_AVE_ROAD_Y: Tuple[float, float] = (-781.0, -751.0)
AMADOR_AVE_CORRIDOR_Y: Tuple[float, float] = (-786.0, -746.0)

# Northern Great Castle Extension corridors (shifted dx=-11.0 ft, dy=-4814.0 ft from OSM route_3)
E_4TH_ST_Y: float = 862.0
E_4TH_ST_ROAD_Y: Tuple[float, float] = (847.0, 877.0)
E_4TH_ST_CORRIDOR_Y: Tuple[float, float] = (842.0, 882.0)

E_5TH_ST_Y: float = 1188.0
E_5TH_ST_ROAD_Y: Tuple[float, float] = (1173.0, 1203.0)
E_5TH_ST_CORRIDOR_Y: Tuple[float, float] = (1168.0, 1208.0)

GC_ALLEY_X: Tuple[float, float] = (414.0, 430.0)

STREETS: Dict[str, Dict[str, object]] = {
    "s_union_ave": {
        "axis": "ns",
        "x": UNION_CORRIDOR_X,
        "y": (HY0, HY1),
        "w_walk_x": UNION_W_SIDEWALK_X,
        "sb_x": UNION_SB_CARRIAGE_X,
        "sb_center_x": UNION_SB_CENTER_X,
        "median_x": UNION_MEDIAN_X,
        "nb_x": UNION_NB_CARRIAGE_X,
        "nb_center_x": UNION_NB_CENTER_X,
        "e_walk_x": UNION_E_SIDEWALK_X,
        "pole_x": UNION_POLE_X,
    },
    "e_4th_st": {
        "axis": "ew",
        "center_y": E_4TH_ST_Y,
        "road_y": E_4TH_ST_ROAD_Y,
        "corridor_y": E_4TH_ST_CORRIDOR_Y,
        "x": (HX0, HX1),
    },
    "e_5th_st": {
        "axis": "ew",
        "center_y": E_5TH_ST_Y,
        "road_y": E_5TH_ST_ROAD_Y,
        "corridor_y": E_5TH_ST_CORRIDOR_Y,
        "x": (UNION_E_SIDEWALK_X[0], HX1),
    },
    "gc_alley": {
        "axis": "ns",
        "center_x": 422.0,
        "road_x": GC_ALLEY_X,
        "corridor_x": GC_ALLEY_X,
        "y_segments": (
            (E_4TH_ST_CORRIDOR_Y[1], E_5TH_ST_CORRIDOR_Y[0]),
            (E_5TH_ST_CORRIDOR_Y[1], HY1),
        ),
    },
    "e_belle_terrace": {
        "axis": "ew",
        "center_y": BELLE_TERRACE_Y,
        "road_y": BELLE_TERRACE_ROAD_Y,
        "corridor_y": BELLE_TERRACE_CORRIDOR_Y,
        "x": (HX0, HX1),
    },
    "trinity_ave": {
        "axis": "ew",
        "center_y": TRINITY_AVE_Y,
        "road_y": TRINITY_AVE_ROAD_Y,
        "corridor_y": TRINITY_AVE_CORRIDOR_Y,
        "x": (HX0, DELAWARE_ST_CORRIDOR_X[1]),
    },
    "delaware_st": {
        "axis": "ns",
        "center_x": DELAWARE_ST_X,
        "road_x": DELAWARE_ST_ROAD_X,
        "corridor_x": DELAWARE_ST_CORRIDOR_X,
        "y": (AMADOR_AVE_ROAD_Y[1], TRINITY_AVE_CORRIDOR_Y[1]),
    },
    "mariposa_ave": {
        "axis": "ew",
        "center_y": MARIPOSA_AVE_Y,
        "road_y": MARIPOSA_AVE_ROAD_Y,
        "corridor_y": MARIPOSA_AVE_CORRIDOR_Y,
        "x": (HX0, DELAWARE_ST_ROAD_X[0]),
    },
    "adams_st": {
        "axis": "ew",
        "center_y": ADAMS_ST_Y,
        "road_y": ADAMS_ST_ROAD_Y,
        "corridor_y": ADAMS_ST_CORRIDOR_Y,
        "x": (UNION_MEDIAN_X[0], HX1),
    },
    "amador_ave": {
        "axis": "ew",
        "center_y": AMADOR_AVE_Y,
        "road_y": AMADOR_AVE_ROAD_Y,
        "corridor_y": AMADOR_AVE_CORRIDOR_Y,
        "x": (HX0, UNION_SB_CENTER_X),
    },
}

# --- Golden West Casino Building (OSM BLDG 59517066) & Parcel (OSM WAY 192135162) ---
# Exact 26-vertex closed polygon in feet relative to (OX, OY)
CASINO_POLY_FT: Tuple[Tuple[float, float], ...] = (
    (-54.07, 77.17), (-43.23, 77.61), (-43.35, 88.31), (5.42, 89.70),
    (7.30, 71.11),   (41.97, 70.52),  (43.23, -15.49), (60.56, -14.17),
    (65.78, -8.44),  (71.02, -4.60),  (80.05, -2.23),  (87.61, -3.29),
    (96.73, -8.87),  (100.19, -16.80),(102.15, -24.36),(100.96, -32.07),
    (97.86, -39.12), (89.61, -43.61), (78.11, -48.06), (61.28, -44.19),
    (54.76, -35.13), (53.62, -71.66), (-20.14, -71.51),(-19.33, -68.77),
    (-53.35, -68.37),(-54.07, 77.17),
)
CASINO_BOUNDS_FT: Tuple[float, float, float, float] = (-54.1, -71.7, 102.2, 89.7)
CASINO_ROTUNDA_CENTER_FT: Tuple[float, float] = (78.9, -25.5)
CASINO_ROTUNDA_R_FT: float = 23.1
CASINO_LOT_FT: Tuple[float, float, float, float] = (-157.7, -270.9, 172.0, 304.2)

# Shared Casino structural interface contract between casino_ext and casino_int
CASINO_WALL_T_FT: float = 1.0
CASINO_FLOOR_Z_FT: float = 0.5
CASINO_CEIL_Z_FT: float = 16.0
CASINO_ROOF_Z_FT: float = 17.0
CASINO_PARAPET_Z_FT: float = 21.5
CASINO_ROTUNDA_DOME_Z_FT: float = 34.0
# Primary NE rotunda entry vestibule clear doorway (x, y, yaw_deg)
CASINO_ENTRY_DOOR_FT: Tuple[float, float, float] = (92.0, -7.0, 225.0)

# --- Great Castle Chinese Restaurant (410 Union Ave, OSM BLDG 60053468 / WAY 59254511) ---
# Exact orthogonalized 6-vertex closed SW-notched footprint (77.5 x 71.5 ft) aligned dx=-11, dy=-4814
GC_DX_FT: float = -11.0
GC_DY_FT: float = -4814.0
GC_LOT_FT: Tuple[float, float, float, float] = (283.0, 882.0, 414.0, 1168.0)
GC_POLY_FT: Tuple[Tuple[float, float], ...] = (
    (336.0, 1006.5),
    (336.0, 1067.5),
    (413.5, 1067.5),
    (413.5, 996.0),
    (354.0, 996.0),
    (354.0, 1006.5),
    (336.0, 1006.5),
)
GC_BLDG_BOUNDS_FT: Tuple[float, float, float, float] = (336.0, 996.0, 413.5, 1067.5)
GC_SW_NOTCH_FT: Tuple[float, float, float, float] = (336.0, 996.0, 354.0, 1006.5)
GC_ANNEX_BOUNDS_FT: Tuple[float, float, float, float] = (383.0, 899.0, 410.5, 948.0)

# Shared Great Castle structural interface contract between gw_gc_ext and gw_gc_int
# gw_gc_int owns floor slab (<=0.5), exterior & partition walls up to ceiling seams
# (<=12.0 west main hall, <=10.5 east BOH wing), and interior furnishings/rooms.
# gw_gc_ext owns lot pavement/props/annex strictly outside GC_POLY_FT plus roof slabs &
# parapets/turret/coolers strictly above z=12.0 (x<=389.5) and z=10.5 (x>=389.5).
GC_WALL_T_FT: float = 1.0
GC_FLOOR_Z_FT: float = 0.5
GC_CEIL_Z_FT: float = 12.0
GC_ROOF_Z_FT: float = 13.0
GC_PARAPET_Z_FT: float = 16.5
GC_EAST_BOH_X_FT: float = 389.0
GC_BOH_CEIL_Z_FT: float = 10.5
GC_BOH_ROOF_Z_FT: float = 11.5
GC_BOH_PARAPET_Z_FT: float = 12.75
GC_TOWER_BOUNDS_FT: Tuple[float, float, float, float] = (354.0, 996.0, 374.0, 1010.0)
GC_TOWER_PARAPET_Z_FT: float = 19.5

GC_VESTIBULE_BOUNDS_FT: Tuple[float, float, float, float] = (355.0, 997.0, 375.0, 1009.0)
GC_DINING_BOUNDS_FT: Tuple[float, float, float, float] = (337.0, 1007.5, 388.5, 1066.5)
GC_RESTROOM_BOUNDS_FT: Tuple[float, float, float, float] = (389.5, 997.0, 412.5, 1013.0)
GC_BOH_BOUNDS_FT: Tuple[float, float, float, float] = (389.5, 1014.0, 412.5, 1066.5)

GC_ENTRY_DOOR_FT: Tuple[float, float, float] = (366.0, 996.5, 90.0)
GC_DOORS_FT: Dict[str, Dict[str, object]] = {
    "south_main_entry": {
        "box_ft": (362.0, 996.0, 0.5, 370.0, 997.0, 9.0),
        "center_ft": (366.0, 996.5),
        "w_ft": 8.0,
        "h_ft": 8.5,
        "yaw": 90.0,
    },
    "north_dining_exit": {
        "box_ft": (358.0, 1066.5, 0.5, 365.0, 1067.5, 9.0),
        "center_ft": (361.5, 1067.0),
        "w_ft": 7.0,
        "h_ft": 8.5,
        "yaw": 270.0,
    },
    "north_kitchen_exit": {
        "box_ft": (398.0, 1066.5, 0.5, 405.0, 1067.5, 9.0),
        "center_ft": (401.5, 1067.0),
        "w_ft": 7.0,
        "h_ft": 8.5,
        "yaw": 270.0,
    },
    "foyer_to_dining": {
        "box_ft": (362.5, 1009.0, 0.5, 369.5, 1010.0, 9.0),
        "center_ft": (366.0, 1009.5),
        "w_ft": 7.0,
        "h_ft": 8.5,
        "yaw": 90.0,
    },
    "dining_to_kitchen": {
        "box_ft": (388.5, 1032.0, 0.5, 389.5, 1039.0, 9.0),
        "center_ft": (389.0, 1035.5),
        "w_ft": 7.0,
        "h_ft": 8.5,
        "yaw": 0.0,
    },
    "dining_to_restrooms": {
        "box_ft": (388.5, 1002.0, 0.5, 389.5, 1008.5, 9.0),
        "center_ft": (389.0, 1005.25),
        "w_ft": 6.5,
        "h_ft": 8.5,
        "yaw": 0.0,
    },
}

# --- Disjoint Parcel Map (ft: (x0, y0, x1, y1)) ---
PARCELS: Dict[str, Tuple[float, float, float, float]] = {
    # Golden West Casino compound (West of S Union Ave)
    "casino_lot":        CASINO_LOT_FT,                        # (-157.7, -270.9, 172.0, 304.2)
    "casino_building":   CASINO_BOUNDS_FT,                     # (-54.1,  -71.7,  102.2, 89.7)

    # West of S Union Ave (North & South of Casino, excluding streets)
    "green_mesh_891":    (-150.0, 582.0,   48.0,  668.0),      # 891 S Union green-mesh vacant dirt lot
    "carnitas_birria":   (  48.0, 582.0,  172.0,  668.0),      # Carnitas Birria Menudo diner (x=102..146, y=612..660)
    "happy_truck":       (-150.0, 668.0,  172.0,  750.0),      # Happy Truck Sales warehouse & yard
    "billboard_lot":     (-490.0, 304.2,  172.0,  532.0),      # SW corner E Belle Terrace & Union sandy lot + billboard
    "ramos_tires":       (-102.0,-342.0,  172.0, -270.9),      # Ramos Tires & Service 3-bay shop (x=-98..24)
    "compas_auto":       (-102.0,-586.0,  172.0, -342.0),      # Compas Auto Sales / Best Deal lot & office
    "super8_motel":      (-102.0,-746.0,  172.0, -586.0),      # Super 8 by Wyndham hotel & pylon (x=-97..142)
    "west_north_outer":  (-490.0, 582.0, -150.0,  750.0),      # NW residential/industrial fringe
    "west_casino_fringe":(-490.0,-125.0, -157.7,  304.2),      # West fringe behind Casino (north of Trinity)
    "west_trinity_south":(-490.0,-436.0, -143.0, -166.0),      # Trinity/Delaware ranch houses north of Mariposa
    "west_mariposa_south":(-490.0,-746.0,-143.0, -476.0),      # Mariposa/Amador houses + In Heaven complex
    "west_south_amador": (-490.0,-820.0,  172.0, -786.0),      # South of Amador fringe

    # East of S Union Ave (tiling y=[-820, +750] outside Belle Terrace & Adams St)
    "srm_century_glass": ( 283.0, 582.0,  650.0,  750.0),      # NE corner E Belle Terrace & Union
    "el_don_brownfield": ( 283.0, 424.0,  650.0,  532.0),      # SE Belle Terrace demolished El Don brownfield
    "redwood_senior":    ( 283.0, 326.0,  650.0,  424.0),      # Redwood Senior Living (bldg x=410..563, y=334..420)
    "star_liter_motel":  ( 283.0,  26.0,  505.0,  326.0),      # Star-Liter Motor Motel (bldg x=296..493, y=33..210)
    "rv_park_922_north": ( 505.0,  26.0,  650.0,  326.0),      # 922 S Union RV park north bay behind Star-Liter
    "rv_park_922":       ( 283.0,-268.0,  650.0,   26.0),      # 922 S Union RV & mobile home park
    "sunland_motel":     ( 283.0,-366.0,  650.0, -268.0),      # Sunland Motel breeze-block (bldg x=311..559)
    "country_inn_motel": ( 283.0,-555.0,  650.0, -366.0),      # Country Inn Motel U-courtyard (bldg x=310..636)
    "playfair_market":   ( 283.0,-820.0,  650.0, -595.0),      # Playfair Market SE corner Union & Adams (x=295..353)

    # Northern Great Castle Extension (non-overlapping tiling y=[750, 1340] outside E 4th, E 5th & GC Alley)
    "gc_deal_time":       ( 283.0,  750.0, 650.0,  842.0),     # SE Union & E 4th: Deal Time Auto Sales & cottages
    "gc_great_castle":    GC_LOT_FT,                           # (283.0, 882.0, 414.0, 1168.0) 410 Union Ave Great Castle block
    "gc_alley_east":      ( 430.0,  882.0, 650.0, 1168.0),     # East of rear alley E 4th..E 5th warehouse & cottages
    "gc_reyes_tires":     ( 283.0, 1208.0, 414.0, 1340.0),     # NE Union & E 5th: Reyes Tires & Auto bays
    "gc_north_fringe":    ( 430.0, 1208.0, 650.0, 1340.0),     # North of E 5th East of alley cottages & fringe
    "gc_west_4th_onestop":(-490.0,  750.0, 172.0,  842.0),     # SW Union & 4th St: One Stop & commercial/residential strip
    "gc_west_manila_dg":  (-490.0,  882.0, 172.0, 1340.0),     # West Union 4th St..HY1: Manila Inn, DG Market & north lot
}

# Disjoint ownership zones across downstream geometry modules
# Format: zone_name -> tuple of parcel/corridor (x0, y0, x1, y1) bounding boxes or metadata
ZONE_BOUNDS_FT: Dict[str, Dict[str, object]] = {
    "streets": {
        "owner": "streets_builder",
        "summary": "Sky/world hull, S Union Ave 3+3 boulevard (-820..1340), brick median, GIS median palms/trees, E 4th/5th & GC alley, signals, poles, road decals.",
        "corridors": [
            (UNION_CORRIDOR_X[0], HY0, UNION_CORRIDOR_X[1], HY1),
            (HX0, E_4TH_ST_CORRIDOR_Y[0], HX1, E_4TH_ST_CORRIDOR_Y[1]),
            (UNION_E_SIDEWALK_X[0], E_5TH_ST_CORRIDOR_Y[0], HX1, E_5TH_ST_CORRIDOR_Y[1]),
            (GC_ALLEY_X[0], E_4TH_ST_CORRIDOR_Y[1], GC_ALLEY_X[1], E_5TH_ST_CORRIDOR_Y[0]),
            (GC_ALLEY_X[0], E_5TH_ST_CORRIDOR_Y[1], GC_ALLEY_X[1], HY1),
            (HX0, BELLE_TERRACE_CORRIDOR_Y[0], HX1, BELLE_TERRACE_CORRIDOR_Y[1]),
            (HX0, TRINITY_AVE_CORRIDOR_Y[0], DELAWARE_ST_CORRIDOR_X[1], TRINITY_AVE_CORRIDOR_Y[1]),
            (DELAWARE_ST_CORRIDOR_X[0], AMADOR_AVE_ROAD_Y[1], DELAWARE_ST_CORRIDOR_X[1], TRINITY_AVE_CORRIDOR_Y[1]),
            (HX0, MARIPOSA_AVE_CORRIDOR_Y[0], DELAWARE_ST_ROAD_X[0], MARIPOSA_AVE_CORRIDOR_Y[1]),
            (UNION_MEDIAN_X[0], ADAMS_ST_CORRIDOR_Y[0], HX1, ADAMS_ST_CORRIDOR_Y[1]),
            (HX0, AMADOR_AVE_CORRIDOR_Y[0], UNION_SB_CENTER_X, AMADOR_AVE_CORRIDOR_Y[1]),
        ],
    },
    "casino_ext": {
        "owner": "casino_ext_builder",
        "summary": "Golden West Casino 26-vertex exterior walls, 45-deg NE portico, rotunda cylinder & dome, roofs, neon signage, bronze horse plaza, lot parking & perimeter fences.",
        "bbox": CASINO_LOT_FT,
        "excludes": [
            CASINO_BOUNDS_FT,
            (*DELAWARE_ST_CORRIDOR_X, HY0, TRINITY_AVE_CORRIDOR_Y[1]),
            (HX0, TRINITY_AVE_CORRIDOR_Y[0], DELAWARE_ST_CORRIDOR_X[1], TRINITY_AVE_CORRIDOR_Y[1]),
        ],
        "parcels": ["casino_lot"],
    },
    "casino_int": {
        "owner": "casino_int_builder",
        "summary": "Golden West Casino enterable interior rooms: lobby, gaming pit w/ burgundy felt tables, bar/tap room, cage, restrooms, lounge, stairs/mezzanine, Buddha altar.",
        "bbox": CASINO_BOUNDS_FT,
        "parcels": ["casino_building"],
    },
    "east_union": {
        "owner": "east_union_builder",
        "summary": "All parcels East of S Union Ave (x >= 283.0, y <= 750.0): SRM/Century Glass, El Don brownfield, Redwood Senior, Star-Liter Motel, 922 RV Park, Sunland, Country Inn, Playfair Market.",
        "bbox": (283.0, HY0, HX1, SOUTH_ZONE_HY1),
        "parcels": [
            "srm_century_glass",
            "el_don_brownfield",
            "redwood_senior",
            "star_liter_motel",
            "rv_park_922_north",
            "rv_park_922",
            "sunland_motel",
            "country_inn_motel",
            "playfair_market",
        ],
    },
    "west_union": {
        "owner": "west_union_builder",
        "summary": "All parcels West of S Union Ave (x <= 172.0, y <= 750.0) excluding Casino lot & street corridors: 891 green-mesh lot, Carnitas Birria, Happy Truck, billboard lot, Ramos Tires, Compas Auto, Super 8, West residential.",
        "bbox": (HX0, HY0, 172.0, SOUTH_ZONE_HY1),
        "parcels": [
            "green_mesh_891",
            "carnitas_birria",
            "happy_truck",
            "billboard_lot",
            "ramos_tires",
            "compas_auto",
            "super8_motel",
            "west_north_outer",
            "west_casino_fringe",
            "west_trinity_south",
            "west_mariposa_south",
            "west_south_amador",
        ],
    },
    "gc_ext": {
        "owner": "gc_ext_builder",
        "summary": "410 Union Ave Great Castle lot outside GC_POLY_FT plus roofs/parapets/SW watchtower/red barrel awning/signage/SE annex/swamp coolers strictly above wall ceilings.",
        "bbox": GC_LOT_FT,
        "excludes": [GC_BLDG_BOUNDS_FT],
        "parcels": ["gc_great_castle"],
    },
    "gc_int": {
        "owner": "gc_int_builder",
        "summary": "410 Union Ave Great Castle structural floor/wall shell & enterable interior rooms: carved wood vestibule, red-carpet dining hall, booths/lanterns, restrooms & East BOH kitchen.",
        "bbox": GC_BLDG_BOUNDS_FT,
        "poly": GC_POLY_FT,
        "parcels": ["gc_great_castle"],
    },
    "north_union": {
        "owner": "north_union_builder",
        "summary": "Northern framing parcels (y in [750.0, 1340.0]) surrounding Great Castle: Deal Time Auto, Alley East warehouse/cottages, Reyes Tires, North Fringe, One Stop, Manila Inn & DG Market.",
        "bbox": (HX0, SOUTH_ZONE_HY1, HX1, HY1),
        "excludes": [
            GC_LOT_FT,
            (UNION_CORRIDOR_X[0], SOUTH_ZONE_HY1, UNION_CORRIDOR_X[1], HY1),
            (HX0, E_4TH_ST_CORRIDOR_Y[0], HX1, E_4TH_ST_CORRIDOR_Y[1]),
            (UNION_E_SIDEWALK_X[0], E_5TH_ST_CORRIDOR_Y[0], HX1, E_5TH_ST_CORRIDOR_Y[1]),
            (GC_ALLEY_X[0], E_4TH_ST_CORRIDOR_Y[1], GC_ALLEY_X[1], E_5TH_ST_CORRIDOR_Y[0]),
            (GC_ALLEY_X[0], E_5TH_ST_CORRIDOR_Y[1], GC_ALLEY_X[1], HY1),
        ],
        "parcels": [
            "gc_deal_time",
            "gc_alley_east",
            "gc_reyes_tires",
            "gc_north_fringe",
            "gc_west_4th_onestop",
            "gc_west_manila_dg",
        ],
    },
}


# ==============================================================================
# 3. UNIT CONVERSION, SNAPPING & TEXTURE SPECIFICATIONS
# ==============================================================================

def fu(ft: float, snap_u: Optional[float] = None) -> float:
    """Convert feet to exact Quake units (12.0 u/ft), optionally snapped."""
    val = float(ft) * U_FT
    if snap_u is not None and snap_u > 0:
        return round(val / snap_u) * snap_u
    return val


def fui(ft: float, snap_u: float = WORLD_SNAP_U) -> float:
    """Convert feet to snapped Quake units (defaults to 1.0u world grid)."""
    return round((float(ft) * U_FT) / snap_u) * snap_u


def mu(m: float, snap_u: Optional[float] = None) -> float:
    """Convert meters to exact Quake units (39.3700787 u/m), optionally snapped."""
    val = float(m) * U_M
    if snap_u is not None and snap_u > 0:
        return round(val / snap_u) * snap_u
    return val


def mui(m: float, snap_u: float = WORLD_SNAP_U) -> float:
    """Convert meters to snapped Quake units (defaults to 1.0u world grid)."""
    return round((float(m) * U_M) / snap_u) * snap_u


def snap_val(val: float, grid_u: float) -> float:
    """Snap a Quake-unit coordinate cleanly to grid_u."""
    if grid_u <= 0:
        return float(val)
    return round(float(val) / grid_u) * grid_u


class Fit:
    """Fit a texture edge-to-edge across a brush face using Valve-220 projection."""

    def __init__(
        self,
        name: str,
        repeat: Tuple[float, float] = (1.0, 1.0),
        flip_u: bool = False,
        flip_v: bool = False,
    ) -> None:
        self.name = str(name)
        self.repeat = (float(repeat[0]), float(repeat[1]))
        self.flip_u = bool(flip_u)
        self.flip_v = bool(flip_v)


class Tile:
    """Tile a texture at a physical world period (default in feet; w_m/h_m optional)."""

    def __init__(
        self,
        name: str,
        w_ft: float = 8.0,
        h_ft: Optional[float] = None,
        u_ofs: float = 0.0,
        v_ofs: float = 0.0,
        rot_deg: float = 0.0,
        w_m: Optional[float] = None,
        h_m: Optional[float] = None,
    ) -> None:
        self.name = str(name)
        if w_m is not None:
            self.w_u = float(w_m) * U_M
            self.h_u = float(h_m if h_m is not None else w_m) * U_M
        else:
            self.w_u = float(w_ft) * U_FT
            self.h_u = float(h_ft if h_ft is not None else w_ft) * U_FT
        self.u_ofs = float(u_ofs)
        self.v_ofs = float(v_ofs)
        self.rot_deg = float(rot_deg)


def TileM(
    name: str,
    w_m: float = 2.5,
    h_m: Optional[float] = None,
    u_ofs: float = 0.0,
    v_ofs: float = 0.0,
    rot_deg: float = 0.0,
) -> Tile:
    """Convenience constructor for metric-period Tile specs."""
    return Tile(name=name, u_ofs=u_ofs, v_ofs=v_ofs, rot_deg=rot_deg, w_m=w_m, h_m=h_m)


TexSpec = Union[str, Fit, Tile]


def tex_from_spec(spec: TexSpec) -> str:
    """Return raw Quake texture name string from a spec object or string."""
    if isinstance(spec, (Fit, Tile)):
        return spec.name
    return str(spec)


def is_forbidden_tex(name: str) -> bool:
    """Return True if a texture name belongs to banned legacy bklan*/bk_* sets."""
    low = str(name).strip().lower()
    if low in SPECIAL_TEXTURES:
        return False
    return any(low.startswith(pref) for pref in FORBIDDEN_TEX_PREFIXES)


# ==============================================================================
# 4. WAD2 & PNG BOOTSTRAP TEXTURE METADATA
# ==============================================================================

def load_wad_sizes(wad_path: str) -> Dict[str, Tuple[int, int]]:
    """Read (width, height) of every MIPTEX entry inside a Quake WAD2 archive."""
    sizes: Dict[str, Tuple[int, int]] = {}
    if not wad_path or not os.path.isfile(wad_path):
        return sizes
    with open(wad_path, "rb") as f:
        data = f.read()
    if len(data) < 12 or data[:4] != b"WAD2":
        return sizes
    _magic, num_entries, dir_ofs = struct.unpack_from("<4sII", data, 0)
    if dir_ofs + num_entries * 32 > len(data):
        return sizes
    for idx in range(num_entries):
        entry_ofs = dir_ofs + idx * 32
        fofs, dsize, _size, typ, _comp, _pad, raw_name = struct.unpack_from(
            "<IIIBBH16s", data, entry_ofs
        )
        name = raw_name.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()
        if not name:
            continue
        # WAD2 MIPTEX type is 0x44 ('D') or 0x43 ('C'); header: char[16] name, uint32 w, uint32 h
        if typ in (0x43, 0x44) and fofs + 24 <= len(data):
            _mname, w, h = struct.unpack_from("<16sII", data, fofs)
            if w > 0 and h > 0:
                sizes[name.lower()] = (int(w), int(h))
    return sizes


def probe_disk_tex_size(name: str, tex_dir: str = TEX_DIR) -> Optional[Tuple[int, int]]:
    """Inspect BakersfieldQuake/textures/<name>.png IHDR dimensions if available."""
    if not tex_dir or not os.path.isdir(tex_dir):
        return None
    low = name.strip()
    candidates = [
        os.path.join(tex_dir, f"{low}.png"),
        os.path.join(tex_dir, f"{low.lower()}.png"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    hdr = f.read(24)
                if len(hdr) == 24 and hdr[:8] == b"\x89PNG\r\n\x1a\n" and hdr[12:16] == b"IHDR":
                    w, h = struct.unpack(">II", hdr[16:24])
                    if w > 0 and h > 0:
                        return (int(w), int(h))
            except OSError:
                pass
    return None


# ==============================================================================
# 5. VECTOR & VALVE-220 PROJECTION MATH
# ==============================================================================

def _vsub(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vdot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vcross(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _vlen(a: Sequence[float]) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _vnorm(a: Sequence[float]) -> Tuple[float, float, float]:
    L = _vlen(a)
    if L < 1e-12:
        return (0.0, 0.0, 1.0)
    return (a[0] / L, a[1] / L, a[2] / L)


def _fmt_num(x: float) -> str:
    if abs(x) < 1e-7:
        return "0"
    r = round(x)
    if abs(x - r) < 1e-5:
        return str(int(r))
    return f"{x:.5f}".rstrip("0").rstrip(".")


def _plane_tri_pts(
    pts_u: Sequence[Tuple[float, float, float]],
    outward: Tuple[float, float, float],
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]:
    """Pick 3 non-collinear points ordered so (p2 - p0) x (p1 - p0) aligns with outward."""
    if len(pts_u) < 3:
        raise ValueError(f"Face requires at least 3 points, got {len(pts_u)}")
    p0 = pts_u[0]
    p1 = pts_u[1]
    best_p2 = None
    best_area = 0.0
    e1 = _vsub(p1, p0)
    for cand in pts_u[2:]:
        c = _vcross(_vsub(cand, p0), e1)
        area = _vlen(c)
        if area > best_area:
            best_area = area
            best_p2 = cand
    if best_p2 is None or best_area < 1e-6:
        raise ValueError(f"Degenerate colinear face points: {pts_u}")
    c = _vcross(_vsub(best_p2, p0), e1)
    if _vdot(c, outward) < 0.0:
        return (p0, best_p2, p1)
    return (p0, p1, best_p2)


def _face_uv_axes(
    outward: Tuple[float, float, float],
    rot_deg: float = 0.0,
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """Compute upright Valve-220 (u_axis, v_axis) looking at face from outside."""
    n = _vnorm(outward)
    if abs(n[2]) > 0.995:
        u_axis = (1.0, 0.0, 0.0)
        v_axis = (0.0, -1.0, 0.0) if n[2] > 0.0 else (0.0, 1.0, 0.0)
    else:
        u_axis = _vnorm(_vcross((0.0, 0.0, 1.0), n))
        v_axis = _vnorm(_vcross(u_axis, n))
        # Ensure +v runs downward (-z) on tilted or vertical faces
        if v_axis[2] > 0.0:
            v_axis = (-v_axis[0], -v_axis[1], -v_axis[2])
    if abs(rot_deg) > 1e-5:
        rad = math.radians(rot_deg)
        ca, sa = math.cos(rad), math.sin(rad)
        ru = (
            u_axis[0] * ca + v_axis[0] * sa,
            u_axis[1] * ca + v_axis[1] * sa,
            u_axis[2] * ca + v_axis[2] * sa,
        )
        rv = (
            -u_axis[0] * sa + v_axis[0] * ca,
            -u_axis[1] * sa + v_axis[1] * ca,
            -u_axis[2] * sa + v_axis[2] * ca,
        )
        return _vnorm(ru), _vnorm(rv)
    return u_axis, v_axis


def _poly_signed_area_2d(pts: Sequence[Tuple[float, float]]) -> float:
    s = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return 0.5 * s


def _point_in_tri_2d(
    p: Tuple[float, float],
    a: Tuple[float, float],
    b: Tuple[float, float],
    c: Tuple[float, float],
) -> bool:
    def cross2(o, u, v):
        return (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0])

    c1 = cross2(a, b, p)
    c2 = cross2(b, c, p)
    c3 = cross2(c, a, p)
    return (c1 >= -1e-7 and c2 >= -1e-7 and c3 >= -1e-7)


def ear_clip_polygon_2d(pts: Sequence[Tuple[float, float]]) -> List[List[Tuple[float, float]]]:
    """Decompose a simple 2D polygon (possibly non-convex, optionally closed) into CCW triangles."""
    clean: List[Tuple[float, float]] = []
    for pt in pts:
        p = (float(pt[0]), float(pt[1]))
        if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-5:
            clean.append(p)
    if len(clean) > 1 and math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) <= 1e-5:
        clean.pop()
    if len(clean) < 3:
        raise ValueError(f"Polygon needs >= 3 distinct vertices, got {len(clean)}")
    if _poly_signed_area_2d(clean) < 0.0:
        clean.reverse()

    # Remove strictly collinear vertices
    filtered: List[Tuple[float, float]] = []
    m = len(clean)
    for i in range(m):
        a = clean[(i - 1) % m]
        b = clean[i]
        c = clean[(i + 1) % m]
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cross) > 1e-7:
            filtered.append(b)
    if len(filtered) < 3:
        raise ValueError("Degenerate zero-area polygon")

    verts = list(range(len(filtered)))
    tris: List[List[Tuple[float, float]]] = []
    guard = 0
    while len(verts) > 3 and guard < len(filtered) * len(filtered):
        guard += 1
        clipped = False
        nv = len(verts)
        for i in range(nv):
            i0 = verts[(i - 1) % nv]
            i1 = verts[i]
            i2 = verts[(i + 1) % nv]
            a, b, c = filtered[i0], filtered[i1], filtered[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-7:
                continue
            has_inside = False
            for k in verts:
                if k in (i0, i1, i2):
                    continue
                if _point_in_tri_2d(filtered[k], a, b, c):
                    has_inside = True
                    break
            if not has_inside:
                tris.append([a, b, c])
                del verts[i]
                clipped = True
                break
        if not clipped:
            raise ValueError("Failed to ear-clip polygon cleanly (possible self-intersection)")
    if len(verts) == 3:
        a, b, c = filtered[verts[0]], filtered[verts[1]], filtered[verts[2]]
        if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) > 1e-6:
            tris.append([a, b, c])
    return tris


# ==============================================================================
# 6. MAPBUILDER (VALVE-220 + WAD/BOOTSTRAP + HULL-1 VALIDATION)
# ==============================================================================

class MapBuilder:
    """Valve-220 Quake MAP builder tuned for 1:1 Bakersfield goldenwest compilation."""

    def __init__(
        self,
        wad_paths: Sequence[str] = DEFAULT_WAD_PATHS,
        tex_dir: str = TEX_DIR,
        u_per_ft: float = U_FT,
        world_snap_u: float = WORLD_SNAP_U,
        detail_snap_u: float = DETAIL_SNAP_U,
        strict_vis: bool = True,
        check_textures: bool = False,
        require_gwc_prefix: bool = False,
        bootstrap_tex_size: Tuple[int, int] = (128, 128),
        chunk_size_u: float = CHUNK_SIZE_U,
        fence_chunk_size_u: Optional[float] = None,
    ) -> None:
        self.wad_paths = list(wad_paths)
        self.tex_dir = str(tex_dir)
        self.u_per_ft = float(u_per_ft)
        self.u_per_m = float(u_per_ft) / M_PER_FT
        self.world_snap_u = float(world_snap_u)
        self.detail_snap_u = float(detail_snap_u)
        self.strict_vis = bool(strict_vis)
        self.check_textures = bool(check_textures)
        self.require_gwc_prefix = bool(require_gwc_prefix)
        self.bootstrap_tex_size = (int(bootstrap_tex_size[0]), int(bootstrap_tex_size[1]))
        self.chunk_size_u = float(chunk_size_u)
        self.fence_chunk_size_u = (
            float(fence_chunk_size_u)
            if fence_chunk_size_u is not None
            else (FENCE_CHUNK_SIZE_M / CHUNK_SIZE_M) * self.chunk_size_u
        )

        self.tex_sizes: Dict[str, Tuple[int, int]] = {}
        self.loaded_wads: List[str] = []
        self.reload_wads()

        self._brushes: Dict[str, List[Tuple[Tuple[float, float, float, float, float, float], List[str]]]] = {
            "world": [],
            "clip": [],
            "detail": [],
            "illus": [],
            "fence": [],
        }
        self._entities: List[Dict[str, str]] = []
        self._textures_used: set[str] = set()
        self._bootstrap_textures_used: set[str] = set()
        self._missing_textures: set[str] = set()
        self._forbidden_textures_seen: List[Tuple[str, str]] = []
        self._oversize_textures_seen: List[str] = []

        # Hull-1 Navigation & Audit QA records
        self._doorways: List[Dict[str, object]] = []
        self._stairs: List[Dict[str, object]] = []
        self._rooms: List[Dict[str, object]] = []
        self._curbs: List[Dict[str, object]] = []
        self._spots: List[Dict[str, object]] = []

    def reload_wads(self) -> None:
        self.tex_sizes.clear()
        self.loaded_wads.clear()
        for p in self.wad_paths:
            if p and os.path.isfile(p):
                loaded = load_wad_sizes(p)
                self.tex_sizes.update(loaded)
                self.loaded_wads.append(p)

    # --- Scaling helpers on builder instance ---
    def fu(self, ft: float, snap_u: Optional[float] = None) -> float:
        val = float(ft) * self.u_per_ft
        return snap_val(val, snap_u) if snap_u else val

    def fui(self, ft: float, snap_u: Optional[float] = None) -> float:
        return snap_val(float(ft) * self.u_per_ft, self.world_snap_u if snap_u is None else snap_u)

    def mu(self, m: float, snap_u: Optional[float] = None) -> float:
        val = float(m) * self.u_per_m
        return snap_val(val, snap_u) if snap_u else val

    def mui(self, m: float, snap_u: Optional[float] = None) -> float:
        return snap_val(float(m) * self.u_per_m, self.world_snap_u if snap_u is None else snap_u)

    def _snap_for_group(self, x_u: float, group: str) -> float:
        grid = self.world_snap_u if group in ("world", "clip") else self.detail_snap_u
        return snap_val(x_u, grid)

    def _resolve_tex_size(self, name: str) -> Tuple[int, int]:
        low = name.strip().lower()
        if low in SPECIAL_TEXTURES:
            return (64, 64)
        if low in self.tex_sizes:
            return self.tex_sizes[low]
        disk_sz = probe_disk_tex_size(name, self.tex_dir)
        if disk_sz is not None:
            self.tex_sizes[low] = disk_sz
            self._bootstrap_textures_used.add(name)
            return disk_sz
        self._missing_textures.add(name)
        self._bootstrap_textures_used.add(name)
        return self.bootstrap_tex_size

    def _record_texture(self, name: str, context: str = "face") -> str:
        clean = str(name).strip()
        if not clean:
            raise ValueError(f"Empty texture name at {context}")
        low = clean.lower()
        if low not in SPECIAL_TEXTURES:
            self._textures_used.add(clean)
            if is_forbidden_tex(clean):
                self._forbidden_textures_seen.append((clean, context))
            if len(clean) > MAX_TEX_NAME_LEN:
                self._oversize_textures_seen.append(clean)
        return clean

    def _resolve_group(
        self,
        group: str,
        bbox_u: Tuple[float, float, float, float, float, float],
        faces_tex: Sequence[str],
        force_world: bool = False,
    ) -> str:
        if any(str(t).strip().lower() == "clip" for t in faces_tex):
            return "clip"
        if group == "illus":
            return "illus"
        if any(str(t).strip().startswith("{") for t in faces_tex):
            return "fence"
        if group == "world" and self.strict_vis and not force_world:
            dims = sorted((bbox_u[3] - bbox_u[0], bbox_u[4] - bbox_u[1], bbox_u[5] - bbox_u[2]))
            # Demote thin trim (< ~0.10m = 3.94u) or narrow headers/piers/sills (< ~2.00m = 78.7u) to func_detail
            if dims[0] < (0.10 * self.u_per_m - 0.05) or dims[1] < (2.00 * self.u_per_m - 0.05):
                return "detail"
        if group in self._brushes:
            return group
        return "detail"

    def _valve_tex(
        self,
        spec: TexSpec,
        outward: Tuple[float, float, float],
        pts_u: Sequence[Tuple[float, float, float]],
    ) -> str:
        if isinstance(spec, Fit):
            name = self._record_tex_and_size(spec.name, "Fit")
            tw, th = self._resolve_tex_size(name)
            u_ax, v_ax = _face_uv_axes(outward, 0.0)
            us = [_vdot(p, u_ax) for p in pts_u]
            vs = [_vdot(p, v_ax) for p in pts_u]
            u0, u1 = min(us), max(us)
            v0, v1 = min(vs), max(vs)
            du = max(u1 - u0, 1e-3)
            dv = max(v1 - v0, 1e-3)
            rx, ry = spec.repeat
            rx = max(abs(rx), 1e-4)
            ry = max(abs(ry), 1e-4)
            if spec.flip_u:
                sx = -du / (rx * tw)
                ox = -u1 / sx
            else:
                sx = du / (rx * tw)
                ox = -u0 / sx
            if spec.flip_v:
                sy = -dv / (ry * th)
                oy = -v1 / sy
            else:
                sy = dv / (ry * th)
                oy = -v0 / sy
        elif isinstance(spec, Tile):
            name = self._record_tex_and_size(spec.name, "Tile")
            tw, th = self._resolve_tex_size(name)
            u_ax, v_ax = _face_uv_axes(outward, spec.rot_deg)
            sx = max(spec.w_u, 1e-3) / tw
            sy = max(spec.h_u, 1e-3) / th
            ox = spec.u_ofs * tw
            oy = spec.v_ofs * th
        else:
            name = self._record_tex_and_size(str(spec), "plain")
            u_ax, v_ax = _face_uv_axes(outward, 0.0)
            sx, sy = 1.0, 1.0
            ox, oy = 0.0, 0.0

        return (
            f"{name} "
            f"[ {_fmt_num(u_ax[0])} {_fmt_num(u_ax[1])} {_fmt_num(u_ax[2])} {_fmt_num(ox)} ] "
            f"[ {_fmt_num(v_ax[0])} {_fmt_num(v_ax[1])} {_fmt_num(v_ax[2])} {_fmt_num(oy)} ] "
            f"0 {_fmt_num(sx)} {_fmt_num(sy)}"
        )

    def _record_tex_and_size(self, name: str, context: str) -> str:
        clean = self._record_texture(name, context)
        self._resolve_tex_size(clean)
        return clean

    def _plane_line(
        self,
        pts_u: Sequence[Tuple[float, float, float]],
        outward: Tuple[float, float, float],
        spec: TexSpec,
    ) -> str:
        p0, p1, p2 = _plane_tri_pts(pts_u, outward)
        tex_tail = self._valve_tex(spec, outward, pts_u)
        return (
            f"( {_fmt_num(p0[0])} {_fmt_num(p0[1])} {_fmt_num(p0[2])} ) "
            f"( {_fmt_num(p1[0])} {_fmt_num(p1[1])} {_fmt_num(p1[2])} ) "
            f"( {_fmt_num(p2[0])} {_fmt_num(p2[1])} {_fmt_num(p2[2])} ) "
            f"{tex_tail}"
        )

    def _emit_brush(
        self,
        faces: Sequence[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], TexSpec]],
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        all_pts = [pt for pts_u, _out, _sp in faces for pt in pts_u]
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        zs = [p[2] for p in all_pts]
        bbox_u = (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
        if (bbox_u[3] - bbox_u[0] < 0.25) or (bbox_u[4] - bbox_u[1] < 0.25) or (bbox_u[5] - bbox_u[2] < 0.25):
            return
        tex_names = [tex_from_spec(sp) for _pts, _out, sp in faces]
        target_group = self._resolve_group(group, bbox_u, tex_names, force_world=force_world)
        lines = [self._plane_line(pts_u, outward, spec) for pts_u, outward, spec in faces]
        self._brushes[target_group].append((bbox_u, lines))

    # ==========================================================================
    # 7. BOX, PRISM, WALL, RAMP, CURB, STAIR & DECAL PRIMITIVES (FEET + METERS)
    # ==========================================================================

    def _box_u(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        tex: TexSpec,
        faces: Optional[Dict[str, TexSpec]] = None,
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        target_snap = self.world_snap_u if (group in ("world", "clip") or force_world) else self.detail_snap_u
        ax0, ax1 = sorted((snap_val(x0, target_snap), snap_val(x1, target_snap)))
        ay0, ay1 = sorted((snap_val(y0, target_snap), snap_val(y1, target_snap)))
        az0, az1 = sorted((snap_val(z0, target_snap), snap_val(z1, target_snap)))
        if (ax1 - ax0) < 0.25 or (ay1 - ay0) < 0.25 or (az1 - az0) < 0.25:
            return
        ov = faces or {}
        sp_w = ov.get("w", ov.get("west", tex))
        sp_e = ov.get("e", ov.get("east", tex))
        sp_s = ov.get("s", ov.get("south", tex))
        sp_n = ov.get("n", ov.get("north", tex))
        sp_b = ov.get("b", ov.get("bot", ov.get("bottom", tex)))
        sp_t = ov.get("t", ov.get("top", tex))

        plane_defs = [
            ([(ax0, ay0, az0), (ax0, ay1, az0), (ax0, ay1, az1), (ax0, ay0, az1)], (-1.0, 0.0, 0.0), sp_w),
            ([(ax1, ay0, az0), (ax1, ay0, az1), (ax1, ay1, az1), (ax1, ay1, az0)], ( 1.0, 0.0, 0.0), sp_e),
            ([(ax0, ay0, az0), (ax0, ay0, az1), (ax1, ay0, az1), (ax1, ay0, az0)], ( 0.0,-1.0, 0.0), sp_s),
            ([(ax0, ay1, az0), (ax1, ay1, az0), (ax1, ay1, az1), (ax0, ay1, az1)], ( 0.0, 1.0, 0.0), sp_n),
            ([(ax0, ay0, az0), (ax1, ay0, az0), (ax1, ay1, az0), (ax0, ay1, az0)], ( 0.0, 0.0,-1.0), sp_b),
            ([(ax0, ay0, az1), (ax0, ay1, az1), (ax1, ay1, az1), (ax1, ay0, az1)], ( 0.0, 0.0, 1.0), sp_t),
        ]
        self._emit_brush(plane_defs, group=group, force_world=force_world)

    def box_ft(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        tex: TexSpec,
        faces: Optional[Dict[str, TexSpec]] = None,
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        self._box_u(
            x0 * self.u_per_ft, y0 * self.u_per_ft, z0 * self.u_per_ft,
            x1 * self.u_per_ft, y1 * self.u_per_ft, z1 * self.u_per_ft,
            tex=tex, faces=faces, group=group, force_world=force_world,
        )

    def box_m(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        tex: TexSpec,
        faces: Optional[Dict[str, TexSpec]] = None,
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        self._box_u(
            x0 * self.u_per_m, y0 * self.u_per_m, z0 * self.u_per_m,
            x1 * self.u_per_m, y1 * self.u_per_m, z1 * self.u_per_m,
            tex=tex, faces=faces, group=group, force_world=force_world,
        )

    def structural_box_ft(self, x0, y0, z0, x1, y1, z1, tex, faces=None) -> None:
        self.box_ft(x0, y0, z0, x1, y1, z1, tex, faces=faces, group="world", force_world=True)

    def structural_box_m(self, x0, y0, z0, x1, y1, z1, tex, faces=None) -> None:
        self.box_m(x0, y0, z0, x1, y1, z1, tex, faces=faces, group="world", force_world=True)

    def detail_box_ft(self, x0, y0, z0, x1, y1, z1, tex, faces=None) -> None:
        self.box_ft(x0, y0, z0, x1, y1, z1, tex, faces=faces, group="detail")

    def detail_box_m(self, x0, y0, z0, x1, y1, z1, tex, faces=None) -> None:
        self.box_m(x0, y0, z0, x1, y1, z1, tex, faces=faces, group="detail")

    def illus_box_ft(self, x0, y0, z0, x1, y1, z1, tex, faces=None) -> None:
        self.box_ft(x0, y0, z0, x1, y1, z1, tex, faces=faces, group="illus")

    def illus_box_m(self, x0, y0, z0, x1, y1, z1, tex, faces=None) -> None:
        self.box_m(x0, y0, z0, x1, y1, z1, tex, faces=faces, group="illus")

    def clip_box_ft(self, x0, y0, z0, x1, y1, z1) -> None:
        self.box_ft(x0, y0, z0, x1, y1, z1, "clip", group="clip")

    def clip_box_m(self, x0, y0, z0, x1, y1, z1) -> None:
        self.box_m(x0, y0, z0, x1, y1, z1, "clip", group="clip")

    def _sign_decal_u(
        self,
        face: str,
        pos_u: float,
        a0_u: float,
        a1_u: float,
        b0_u: float,
        b1_u: float,
        tex: TexSpec,
        thick_u: float = 1.0,
        group: str = "illus",
        flip_u: bool = False,
        flip_v: bool = False,
    ) -> None:
        f = face.strip().lower()
        t = max(float(thick_u), 0.5)
        sp = tex if isinstance(tex, (Fit, Tile)) else Fit(str(tex), flip_u=flip_u, flip_v=flip_v)
        faces = {"w": "skip", "e": "skip", "s": "skip", "n": "skip", "b": "skip", "t": "skip"}
        if f in ("e", "east"):
            faces["e"] = sp
            self._box_u(pos_u, a0_u, b0_u, pos_u + t, a1_u, b1_u, "skip", faces=faces, group=group)
        elif f in ("w", "west"):
            faces["w"] = sp
            self._box_u(pos_u - t, a0_u, b0_u, pos_u, a1_u, b1_u, "skip", faces=faces, group=group)
        elif f in ("n", "north"):
            faces["n"] = sp
            self._box_u(a0_u, pos_u, b0_u, a1_u, pos_u + t, b1_u, "skip", faces=faces, group=group)
        elif f in ("s", "south"):
            faces["s"] = sp
            self._box_u(a0_u, pos_u - t, b0_u, a1_u, pos_u, b1_u, "skip", faces=faces, group=group)
        elif f in ("t", "top"):
            faces["t"] = sp
            self._box_u(a0_u, b0_u, pos_u, a1_u, b1_u, pos_u + t, "skip", faces=faces, group=group)
        elif f in ("b", "bot", "bottom"):
            faces["b"] = sp
            self._box_u(a0_u, b0_u, pos_u - t, a1_u, b1_u, pos_u, "skip", faces=faces, group=group)
        else:
            raise ValueError(f"Unknown decal face '{face}' (expected n/s/e/w/t/b)")

    def sign_decal_ft(
        self,
        face: str,
        pos_ft: float,
        a0_ft: float,
        a1_ft: float,
        b0_ft: float,
        b1_ft: float,
        tex: TexSpec,
        thick_ft: float = 0.08,
        group: str = "illus",
        flip_u: bool = False,
        flip_v: bool = False,
    ) -> None:
        self._sign_decal_u(
            face, pos_ft * self.u_per_ft, a0_ft * self.u_per_ft, a1_ft * self.u_per_ft,
            b0_ft * self.u_per_ft, b1_ft * self.u_per_ft, tex,
            thick_u=max(thick_ft * self.u_per_ft, 0.5),
            group=group, flip_u=flip_u, flip_v=flip_v,
        )

    def sign_decal_m(
        self,
        face: str,
        pos_m: float,
        a0_m: float,
        a1_m: float,
        b0_m: float,
        b1_m: float,
        tex: TexSpec,
        thick_m: float = 0.025,
        group: str = "illus",
        flip_u: bool = False,
        flip_v: bool = False,
    ) -> None:
        self._sign_decal_u(
            face, pos_m * self.u_per_m, a0_m * self.u_per_m, a1_m * self.u_per_m,
            b0_m * self.u_per_m, b1_m * self.u_per_m, tex,
            thick_u=max(thick_m * self.u_per_m, 0.5),
            group=group, flip_u=flip_u, flip_v=flip_v,
        )

    def flush_panel_ft(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        visible_faces: Dict[str, TexSpec],
        group: str = "detail",
    ) -> None:
        """Emit a thin panel keeping ONLY `visible_faces` rendered and culling hidden faces to `skip`."""
        faces: Dict[str, TexSpec] = {"w": "skip", "e": "skip", "s": "skip", "n": "skip", "b": "skip", "t": "skip"}
        faces.update(visible_faces)
        self.box_ft(x0, y0, z0, x1, y1, z1, "skip", faces=faces, group=group)

    def flush_panel_m(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        visible_faces: Dict[str, TexSpec],
        group: str = "detail",
    ) -> None:
        faces: Dict[str, TexSpec] = {"w": "skip", "e": "skip", "s": "skip", "n": "skip", "b": "skip", "t": "skip"}
        faces.update(visible_faces)
        self.box_m(x0, y0, z0, x1, y1, z1, "skip", faces=faces, group=group)

    def _convex_prism_u(
        self,
        pts_xy_u: Sequence[Tuple[float, float]],
        z0_u: float,
        z1_u: float,
        tex_side: TexSpec,
        tex_top: Optional[TexSpec] = None,
        tex_bot: TexSpec = "skip",
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        snap = self.world_snap_u if (group in ("world", "clip") or force_world) else self.detail_snap_u
        az0, az1 = sorted((snap_val(z0_u, snap), snap_val(z1_u, snap)))
        if az1 - az0 < 0.25:
            return
        poly: List[Tuple[float, float]] = []
        for x, y in pts_xy_u:
            pt = (snap_val(x, snap), snap_val(y, snap))
            if not poly or math.hypot(pt[0] - poly[-1][0], pt[1] - poly[-1][1]) > 0.25:
                poly.append(pt)
        if len(poly) > 1 and math.hypot(poly[0][0] - poly[-1][0], poly[0][1] - poly[-1][1]) <= 0.25:
            poly.pop()
        if len(poly) < 3:
            return
        if _poly_signed_area_2d(poly) < 0.0:
            poly.reverse()

        # Verify convexity on CCW ring
        n = len(poly)
        for i in range(n):
            a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross < -1e-3:
                raise ValueError(
                    "prism requires a convex polygon; use poly_prism_ft/poly_prism_m for concave shapes like CASINO_POLY_FT"
                )

        top_spec = tex_side if tex_top is None else tex_top
        bot_pts = [(p[0], p[1], az0) for p in poly]
        top_pts = [(p[0], p[1], az1) for p in poly]
        plane_defs: List[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], TexSpec]] = [
            (bot_pts, (0.0, 0.0, -1.0), tex_bot),
            (top_pts, (0.0, 0.0,  1.0), top_spec),
        ]
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy)
            if L < 0.25:
                continue
            out = (dy / L, -dx / L, 0.0)
            s_pts = [(x0, y0, az0), (x1, y1, az0), (x1, y1, az1), (x0, y0, az1)]
            plane_defs.append((s_pts, out, tex_side))
        self._emit_brush(plane_defs, group=group, force_world=force_world)

    def prism_ft(
        self,
        pts_xy_ft: Sequence[Tuple[float, float]],
        z0_ft: float,
        z1_ft: float,
        tex_side: TexSpec,
        tex_top: Optional[TexSpec] = None,
        tex_bot: TexSpec = "skip",
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        pts_u = [(x * self.u_per_ft, y * self.u_per_ft) for x, y in pts_xy_ft]
        self._convex_prism_u(
            pts_u, z0_ft * self.u_per_ft, z1_ft * self.u_per_ft,
            tex_side, tex_top=tex_top, tex_bot=tex_bot, group=group, force_world=force_world,
        )

    def prism_m(
        self,
        pts_xy_m: Sequence[Tuple[float, float]],
        z0_m: float,
        z1_m: float,
        tex_side: TexSpec,
        tex_top: Optional[TexSpec] = None,
        tex_bot: TexSpec = "skip",
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        pts_u = [(x * self.u_per_m, y * self.u_per_m) for x, y in pts_xy_m]
        self._convex_prism_u(
            pts_u, z0_m * self.u_per_m, z1_m * self.u_per_m,
            tex_side, tex_top=tex_top, tex_bot=tex_bot, group=group, force_world=force_world,
        )

    def poly_prism_ft(
        self,
        pts_xy_ft: Sequence[Tuple[float, float]],
        z0_ft: float,
        z1_ft: float,
        tex_side: TexSpec,
        tex_top: Optional[TexSpec] = None,
        tex_bot: TexSpec = "skip",
        group: str = "world",
        force_world: bool = False,
    ) -> int:
        """Ear-clip any simple (possibly concave) XY footprint into convex triangular prisms."""
        tris = ear_clip_polygon_2d(pts_xy_ft)
        for tri in tris:
            self.prism_ft(
                tri, z0_ft, z1_ft, tex_side, tex_top=tex_top, tex_bot=tex_bot,
                group=group, force_world=force_world,
            )
        return len(tris)

    def poly_prism_m(
        self,
        pts_xy_m: Sequence[Tuple[float, float]],
        z0_m: float,
        z1_m: float,
        tex_side: TexSpec,
        tex_top: Optional[TexSpec] = None,
        tex_bot: TexSpec = "skip",
        group: str = "world",
        force_world: bool = False,
    ) -> int:
        tris = ear_clip_polygon_2d(pts_xy_m)
        for tri in tris:
            self.prism_m(
                tri, z0_m, z1_m, tex_side, tex_top=tex_top, tex_bot=tex_bot,
                group=group, force_world=force_world,
            )
        return len(tris)

    def _prism_xz_u(
        self,
        pts_xz_u: Sequence[Tuple[float, float]],
        y0_u: float,
        y1_u: float,
        tex_side: TexSpec,
        tex_end: Optional[TexSpec] = None,
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        snap = self.world_snap_u if (group in ("world", "clip") or force_world) else self.detail_snap_u
        ay0, ay1 = sorted((snap_val(y0_u, snap), snap_val(y1_u, snap)))
        if ay1 - ay0 < 0.25:
            return
        poly = [(snap_val(x, snap), snap_val(z, snap)) for x, z in pts_xz_u]
        if len(poly) > 1 and math.hypot(poly[0][0] - poly[-1][0], poly[0][1] - poly[-1][1]) <= 0.25:
            poly.pop()
        if len(poly) < 3:
            return
        if _poly_signed_area_2d(poly) < 0.0:
            poly.reverse()
        end_sp = tex_side if tex_end is None else tex_end
        s_pts = [(x, ay0, z) for x, z in poly]
        n_pts = [(x, ay1, z) for x, z in poly]
        plane_defs: List[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], TexSpec]] = [
            (s_pts, (0.0, -1.0, 0.0), end_sp),
            (n_pts, (0.0,  1.0, 0.0), end_sp),
        ]
        n = len(poly)
        for i in range(n):
            x0, z0 = poly[i]
            x1, z1 = poly[(i + 1) % n]
            dx, dz = x1 - x0, z1 - z0
            L = math.hypot(dx, dz)
            if L < 0.25:
                continue
            # Outward normal in XZ (since CCW in (x, z) -> right-hand edge normal is (dz, 0, -dx))
            out = (dz / L, 0.0, -dx / L)
            f_pts = [(x0, ay0, z0), (x1, ay0, z1), (x1, ay1, z1), (x0, ay1, z0)]
            plane_defs.append((f_pts, out, tex_side))
        self._emit_brush(plane_defs, group=group, force_world=force_world)

    def prism_xz_ft(
        self,
        pts_xz_ft: Sequence[Tuple[float, float]],
        y0_ft: float,
        y1_ft: float,
        tex_side: TexSpec,
        tex_end: Optional[TexSpec] = None,
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        self._prism_xz_u(
            [(x * self.u_per_ft, z * self.u_per_ft) for x, z in pts_xz_ft],
            y0_ft * self.u_per_ft, y1_ft * self.u_per_ft,
            tex_side, tex_end=tex_end, group=group, force_world=force_world,
        )

    def prism_xz_m(
        self,
        pts_xz_m: Sequence[Tuple[float, float]],
        y0_m: float,
        y1_m: float,
        tex_side: TexSpec,
        tex_end: Optional[TexSpec] = None,
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        self._prism_xz_u(
            [(x * self.u_per_m, z * self.u_per_m) for x, z in pts_xz_m],
            y0_m * self.u_per_m, y1_m * self.u_per_m,
            tex_side, tex_end=tex_end, group=group, force_world=force_world,
        )

    def _prism_yz_u(
        self,
        pts_yz_u: Sequence[Tuple[float, float]],
        x0_u: float,
        x1_u: float,
        tex_side: TexSpec,
        tex_end: Optional[TexSpec] = None,
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        snap = self.world_snap_u if (group in ("world", "clip") or force_world) else self.detail_snap_u
        ax0, ax1 = sorted((snap_val(x0_u, snap), snap_val(x1_u, snap)))
        if ax1 - ax0 < 0.25:
            return
        poly = [(snap_val(y, snap), snap_val(z, snap)) for y, z in pts_yz_u]
        if len(poly) > 1 and math.hypot(poly[0][0] - poly[-1][0], poly[0][1] - poly[-1][1]) <= 0.25:
            poly.pop()
        if len(poly) < 3:
            return
        if _poly_signed_area_2d(poly) < 0.0:
            poly.reverse()
        end_sp = tex_side if tex_end is None else tex_end
        w_pts = [(ax0, y, z) for y, z in poly]
        e_pts = [(ax1, y, z) for y, z in poly]
        plane_defs: List[Tuple[Sequence[Tuple[float, float, float]], Tuple[float, float, float], TexSpec]] = [
            (w_pts, (-1.0, 0.0, 0.0), end_sp),
            (e_pts, ( 1.0, 0.0, 0.0), end_sp),
        ]
        n = len(poly)
        for i in range(n):
            y0, z0 = poly[i]
            y1, z1 = poly[(i + 1) % n]
            dy, dz = y1 - y0, z1 - z0
            L = math.hypot(dy, dz)
            if L < 0.25:
                continue
            out = (0.0, dz / L, -dy / L)
            f_pts = [(ax0, y0, z0), (ax0, y1, z1), (ax1, y1, z1), (ax1, y0, z0)]
            plane_defs.append((f_pts, out, tex_side))
        self._emit_brush(plane_defs, group=group, force_world=force_world)

    def prism_yz_ft(
        self,
        pts_yz_ft: Sequence[Tuple[float, float]],
        x0_ft: float,
        x1_ft: float,
        tex_side: TexSpec,
        tex_end: Optional[TexSpec] = None,
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        self._prism_yz_u(
            [(y * self.u_per_ft, z * self.u_per_ft) for y, z in pts_yz_ft],
            x0_ft * self.u_per_ft, x1_ft * self.u_per_ft,
            tex_side, tex_end=tex_end, group=group, force_world=force_world,
        )

    def prism_yz_m(
        self,
        pts_yz_m: Sequence[Tuple[float, float]],
        x0_m: float,
        x1_m: float,
        tex_side: TexSpec,
        tex_end: Optional[TexSpec] = None,
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        self._prism_yz_u(
            [(y * self.u_per_m, z * self.u_per_m) for y, z in pts_yz_m],
            x0_m * self.u_per_m, x1_m * self.u_per_m,
            tex_side, tex_end=tex_end, group=group, force_world=force_world,
        )

    def cyl_ft(
        self,
        cx_ft: float,
        cy_ft: float,
        r_ft: float,
        z0_ft: float,
        z1_ft: float,
        sides: int = 16,
        tex_side: TexSpec = "gwc_stucco",
        tex_top: Optional[TexSpec] = None,
        tex_bot: TexSpec = "skip",
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        s = max(int(sides), 6)
        pts = [
            (cx_ft + r_ft * math.cos(2.0 * math.pi * i / s), cy_ft + r_ft * math.sin(2.0 * math.pi * i / s))
            for i in range(s)
        ]
        self.prism_ft(pts, z0_ft, z1_ft, tex_side, tex_top=tex_top, tex_bot=tex_bot, group=group, force_world=force_world)

    def cyl_m(
        self,
        cx_m: float,
        cy_m: float,
        r_m: float,
        z0_m: float,
        z1_m: float,
        sides: int = 16,
        tex_side: TexSpec = "gwc_stucco",
        tex_top: Optional[TexSpec] = None,
        tex_bot: TexSpec = "skip",
        group: str = "detail",
        force_world: bool = False,
    ) -> None:
        s = max(int(sides), 6)
        pts = [
            (cx_m + r_m * math.cos(2.0 * math.pi * i / s), cy_m + r_m * math.sin(2.0 * math.pi * i / s))
            for i in range(s)
        ]
        self.prism_m(pts, z0_m, z1_m, tex_side, tex_top=tex_top, tex_bot=tex_bot, group=group, force_world=force_world)

    # --- Walls with Hull-1 Doorways & Windows ---
    def _wall_axis_u(
        self,
        axis: str,
        pos_u: float,
        s0_u: float,
        s1_u: float,
        z0_u: float,
        z1_u: float,
        thick_u: float,
        tex: TexSpec,
        doorways_u: Optional[Sequence[Tuple[float, ...]]] = None,
        windows_u: Optional[Sequence[Tuple[float, float, float, float]]] = None,
        tex_inside: Optional[TexSpec] = None,
        group: str = "world",
        force_world: bool = False,
        name_prefix: str = "door",
    ) -> None:
        """Build an axis-aligned wall along X ('x' = spans x, thickness on y) or Y ('y' = spans y, thickness on x)."""
        s0, s1 = sorted((s0_u, s1_u))
        z0, z1 = sorted((z0_u, z1_u))
        half_t = 0.5 * thick_u

        def emit_panel(ps0: float, ps1: float, pz0: float, pz1: float) -> None:
            if (ps1 - ps0) < 0.5 or (pz1 - pz0) < 0.5:
                return
            faces = None
            if tex_inside is not None:
                if axis == "x":
                    faces = {"n": tex, "s": tex_inside}
                else:
                    faces = {"e": tex, "w": tex_inside}
            if axis == "x":
                self._box_u(ps0, pos_u - half_t, pz0, ps1, pos_u + half_t, pz1, tex, faces=faces, group=group, force_world=force_world)
            else:
                self._box_u(pos_u - half_t, ps0, pz0, pos_u + half_t, ps1, pz1, tex, faces=faces, group=group, force_world=force_world)

        openings: List[Tuple[float, float, float, float]] = []
        if doorways_u:
            for idx, d in enumerate(doorways_u):
                d0, d1, d_top = float(d[0]), float(d[1]), float(d[2])
                dname = str(d[3]) if len(d) >= 4 else f"{name_prefix}_{axis}_{idx}"
                a0, a1 = sorted((d0, d1))
                w_u = a1 - a0
                h_u = d_top - z0
                self.register_door(dname, w_u, h_u, axis=axis)
                openings.append((a0, a1, z0, d_top))
        if windows_u:
            for w in windows_u:
                w0, w1, wz0, wz1 = sorted((float(w[0]), float(w[1]))) + sorted((float(w[2]), float(w[3])))
                openings.append((w0, w1, wz0, wz1))

        openings.sort(key=lambda o: o[0])
        cursor = s0
        for o0, o1, oz0, oz1 in openings:
            o0 = max(s0, o0)
            o1 = min(s1, o1)
            if o1 <= o0:
                continue
            if o0 > cursor:
                emit_panel(cursor, o0, z0, z1)
            if oz0 > z0:
                emit_panel(o0, o1, z0, min(oz0, z1))
            if oz1 < z1:
                emit_panel(o0, o1, max(oz1, z0), z1)
            cursor = max(cursor, o1)
        if cursor < s1:
            emit_panel(cursor, s1, z0, z1)

    def wall_xft(
        self,
        y_ft: float,
        x0_ft: float,
        x1_ft: float,
        z0_ft: float,
        z1_ft: float,
        thick_ft: float,
        tex: TexSpec,
        doorways: Optional[Sequence[Tuple[float, ...]]] = None,
        windows: Optional[Sequence[Tuple[float, float, float, float]]] = None,
        tex_inside: Optional[TexSpec] = None,
        group: str = "world",
        force_world: bool = False,
        name_prefix: str = "door",
    ) -> None:
        u = self.u_per_ft
        d_u = [
            (d[0] * u, d[1] * u, d[2] * u, *(d[3:] if len(d) > 3 else ()))
            for d in (doorways or [])
        ]
        w_u = [(w[0] * u, w[1] * u, w[2] * u, w[3] * u) for w in (windows or [])]
        self._wall_axis_u(
            "x", y_ft * u, x0_ft * u, x1_ft * u, z0_ft * u, z1_ft * u, thick_ft * u,
            tex, doorways_u=d_u, windows_u=w_u, tex_inside=tex_inside,
            group=group, force_world=force_world, name_prefix=name_prefix,
        )

    def wall_xm(
        self,
        y_m: float,
        x0_m: float,
        x1_m: float,
        z0_m: float,
        z1_m: float,
        thick_m: float,
        tex: TexSpec,
        doorways: Optional[Sequence[Tuple[float, ...]]] = None,
        windows: Optional[Sequence[Tuple[float, float, float, float]]] = None,
        tex_inside: Optional[TexSpec] = None,
        group: str = "world",
        force_world: bool = False,
        name_prefix: str = "door",
    ) -> None:
        u = self.u_per_m
        d_u = [
            (d[0] * u, d[1] * u, d[2] * u, *(d[3:] if len(d) > 3 else ()))
            for d in (doorways or [])
        ]
        w_u = [(w[0] * u, w[1] * u, w[2] * u, w[3] * u) for w in (windows or [])]
        self._wall_axis_u(
            "x", y_m * u, x0_m * u, x1_m * u, z0_m * u, z1_m * u, thick_m * u,
            tex, doorways_u=d_u, windows_u=w_u, tex_inside=tex_inside,
            group=group, force_world=force_world, name_prefix=name_prefix,
        )

    def wall_yft(
        self,
        x_ft: float,
        y0_ft: float,
        y1_ft: float,
        z0_ft: float,
        z1_ft: float,
        thick_ft: float,
        tex: TexSpec,
        doorways: Optional[Sequence[Tuple[float, ...]]] = None,
        windows: Optional[Sequence[Tuple[float, float, float, float]]] = None,
        tex_inside: Optional[TexSpec] = None,
        group: str = "world",
        force_world: bool = False,
        name_prefix: str = "door",
    ) -> None:
        u = self.u_per_ft
        d_u = [
            (d[0] * u, d[1] * u, d[2] * u, *(d[3:] if len(d) > 3 else ()))
            for d in (doorways or [])
        ]
        w_u = [(w[0] * u, w[1] * u, w[2] * u, w[3] * u) for w in (windows or [])]
        self._wall_axis_u(
            "y", x_ft * u, y0_ft * u, y1_ft * u, z0_ft * u, z1_ft * u, thick_ft * u,
            tex, doorways_u=d_u, windows_u=w_u, tex_inside=tex_inside,
            group=group, force_world=force_world, name_prefix=name_prefix,
        )

    def wall_ym(
        self,
        x_m: float,
        y0_m: float,
        y1_m: float,
        z0_m: float,
        z1_m: float,
        thick_m: float,
        tex: TexSpec,
        doorways: Optional[Sequence[Tuple[float, ...]]] = None,
        windows: Optional[Sequence[Tuple[float, float, float, float]]] = None,
        tex_inside: Optional[TexSpec] = None,
        group: str = "world",
        force_world: bool = False,
        name_prefix: str = "door",
    ) -> None:
        u = self.u_per_m
        d_u = [
            (d[0] * u, d[1] * u, d[2] * u, *(d[3:] if len(d) > 3 else ()))
            for d in (doorways or [])
        ]
        w_u = [(w[0] * u, w[1] * u, w[2] * u, w[3] * u) for w in (windows or [])]
        self._wall_axis_u(
            "y", x_m * u, y0_m * u, y1_m * u, z0_m * u, z1_m * u, thick_m * u,
            tex, doorways_u=d_u, windows_u=w_u, tex_inside=tex_inside,
            group=group, force_world=force_world, name_prefix=name_prefix,
        )

    # --- Ramps, Stairs (with <=18u + clip ramp assertions), Curbs, Awnings ---
    def slab_ramp_xft(
        self,
        x0_ft: float,
        x1_ft: float,
        y0_ft: float,
        y1_ft: float,
        z0_ft: float,
        z1_ft: float,
        tex: TexSpec,
        thick_ft: float = 0.5,
        group: str = "detail",
    ) -> None:
        pts = [
            (x0_ft, z0_ft - thick_ft),
            (x1_ft, z1_ft - thick_ft),
            (x1_ft, z1_ft),
            (x0_ft, z0_ft),
        ]
        self.prism_xz_ft(pts, y0_ft, y1_ft, tex, group=group)

    def slab_ramp_xm(
        self,
        x0_m: float,
        x1_m: float,
        y0_m: float,
        y1_m: float,
        z0_m: float,
        z1_m: float,
        tex: TexSpec,
        thick_m: float = 0.15,
        group: str = "detail",
    ) -> None:
        pts = [
            (x0_m, z0_m - thick_m),
            (x1_m, z1_m - thick_m),
            (x1_m, z1_m),
            (x0_m, z0_m),
        ]
        self.prism_xz_m(pts, y0_m, y1_m, tex, group=group)

    def slab_ramp_yft(
        self,
        x0_ft: float,
        x1_ft: float,
        y0_ft: float,
        y1_ft: float,
        z0_ft: float,
        z1_ft: float,
        tex: TexSpec,
        thick_ft: float = 0.5,
        group: str = "detail",
    ) -> None:
        pts = [
            (y0_ft, z0_ft - thick_ft),
            (y1_ft, z1_ft - thick_ft),
            (y1_ft, z1_ft),
            (y0_ft, z0_ft),
        ]
        self.prism_yz_ft(pts, x0_ft, x1_ft, tex, group=group)

    def slab_ramp_ym(
        self,
        x0_m: float,
        x1_m: float,
        y0_m: float,
        y1_m: float,
        z0_m: float,
        z1_m: float,
        tex: TexSpec,
        thick_m: float = 0.15,
        group: str = "detail",
    ) -> None:
        pts = [
            (y0_m, z0_m - thick_m),
            (y1_m, z1_m - thick_m),
            (y1_m, z1_m),
            (y0_m, z0_m),
        ]
        self.prism_yz_m(pts, x0_m, x1_m, tex, group=group)

    def stair_flight_xft(
        self,
        name: str,
        x0_ft: float,
        x1_ft: float,
        y0_ft: float,
        y1_ft: float,
        z0_ft: float,
        z1_ft: float,
        num_steps: int,
        tex_tread: TexSpec,
        tex_riser: Optional[TexSpec] = None,
        add_clip_ramp: bool = True,
    ) -> None:
        n = max(int(num_steps), 1)
        total_rise_u = abs(z1_ft - z0_ft) * self.u_per_ft
        step_rise_u = total_rise_u / n
        if not add_clip_ramp:
            raise ValueError(f"Stair '{name}' requires smooth clip ramp (add_clip_ramp=True) for Hull-1 smoothness")
        self.register_stair(name, step_rise_u=step_rise_u, num_steps=n, has_clip_ramp=True)
        dx = (x1_ft - x0_ft) / n
        dz = (z1_ft - z0_ft) / n
        riser_tex = tex_tread if tex_riser is None else tex_riser
        for i in range(n):
            sx0 = x0_ft + i * dx
            sx1 = x0_ft + (i + 1) * dx
            sz_top = z0_ft + (i + 1) * dz
            sz_bot = min(z0_ft, sz_top - abs(dz))
            self.detail_box_ft(
                sx0, y0_ft, sz_bot, sx1, y1_ft, sz_top,
                riser_tex, faces={"t": tex_tread},
            )
        # Smooth clip wedge across full flight
        clip_pts = [
            (x0_ft, min(z0_ft, z1_ft) - 0.5),
            (x1_ft, min(z0_ft, z1_ft) - 0.5),
            (x1_ft, z1_ft),
            (x0_ft, z0_ft),
        ]
        self.prism_xz_ft(clip_pts, y0_ft, y1_ft, "clip", tex_end="clip", group="clip")

    def stair_flight_yft(
        self,
        name: str,
        x0_ft: float,
        x1_ft: float,
        y0_ft: float,
        y1_ft: float,
        z0_ft: float,
        z1_ft: float,
        num_steps: int,
        tex_tread: TexSpec,
        tex_riser: Optional[TexSpec] = None,
        add_clip_ramp: bool = True,
    ) -> None:
        n = max(int(num_steps), 1)
        total_rise_u = abs(z1_ft - z0_ft) * self.u_per_ft
        step_rise_u = total_rise_u / n
        if not add_clip_ramp:
            raise ValueError(f"Stair '{name}' requires smooth clip ramp (add_clip_ramp=True) for Hull-1 smoothness")
        self.register_stair(name, step_rise_u=step_rise_u, num_steps=n, has_clip_ramp=True)
        dy = (y1_ft - y0_ft) / n
        dz = (z1_ft - z0_ft) / n
        riser_tex = tex_tread if tex_riser is None else tex_riser
        for i in range(n):
            sy0 = y0_ft + i * dy
            sy1 = y0_ft + (i + 1) * dy
            sz_top = z0_ft + (i + 1) * dz
            sz_bot = min(z0_ft, sz_top - abs(dz))
            self.detail_box_ft(
                x0_ft, sy0, sz_bot, x1_ft, sy1, sz_top,
                riser_tex, faces={"t": tex_tread},
            )
        clip_pts = [
            (y0_ft, min(z0_ft, z1_ft) - 0.5),
            (y1_ft, min(z0_ft, z1_ft) - 0.5),
            (y1_ft, z1_ft),
            (y0_ft, z0_ft),
        ]
        self.prism_yz_ft(clip_pts, x0_ft, x1_ft, "clip", tex_end="clip", group="clip")

    def stair_flight_xm(
        self,
        name: str,
        x0_m: float,
        x1_m: float,
        y0_m: float,
        y1_m: float,
        z0_m: float,
        z1_m: float,
        num_steps: int,
        tex_tread: TexSpec,
        tex_riser: Optional[TexSpec] = None,
        add_clip_ramp: bool = True,
    ) -> None:
        self.stair_flight_xft(
            name,
            x0_m * FT_PER_M, x1_m * FT_PER_M,
            y0_m * FT_PER_M, y1_m * FT_PER_M,
            z0_m * FT_PER_M, z1_m * FT_PER_M,
            num_steps, tex_tread, tex_riser=tex_riser, add_clip_ramp=add_clip_ramp,
        )

    def stair_flight_ym(
        self,
        name: str,
        x0_m: float,
        x1_m: float,
        y0_m: float,
        y1_m: float,
        z0_m: float,
        z1_m: float,
        num_steps: int,
        tex_tread: TexSpec,
        tex_riser: Optional[TexSpec] = None,
        add_clip_ramp: bool = True,
    ) -> None:
        self.stair_flight_yft(
            name,
            x0_m * FT_PER_M, x1_m * FT_PER_M,
            y0_m * FT_PER_M, y1_m * FT_PER_M,
            z0_m * FT_PER_M, z1_m * FT_PER_M,
            num_steps, tex_tread, tex_riser=tex_riser, add_clip_ramp=add_clip_ramp,
        )

    def add_stairs(
        self,
        name: str,
        axis: str,
        x0_ft: float,
        x1_ft: float,
        y0_ft: float,
        y1_ft: float,
        z0_ft: float,
        z1_ft: float,
        num_steps: int,
        tex_tread: TexSpec,
        tex_riser: Optional[TexSpec] = None,
        add_clip_ramp: bool = True,
    ) -> None:
        """Unified stair flight helper along 'x' or 'y' (feet) with <=18u rise + clip ramp."""
        ax = axis.strip().lower()
        if ax == "x":
            self.stair_flight_xft(
                name, x0_ft, x1_ft, y0_ft, y1_ft, z0_ft, z1_ft,
                num_steps, tex_tread, tex_riser=tex_riser, add_clip_ramp=add_clip_ramp,
            )
        elif ax == "y":
            self.stair_flight_yft(
                name, x0_ft, x1_ft, y0_ft, y1_ft, z0_ft, z1_ft,
                num_steps, tex_tread, tex_riser=tex_riser, add_clip_ramp=add_clip_ramp,
            )
        else:
            raise ValueError(f"Unsupported stair axis '{axis}' (expected 'x' or 'y')")

    def curb_ft(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        tex: TexSpec,
        group: str = "detail",
    ) -> None:
        rise_u = abs(z1 - z0) * self.u_per_ft
        if rise_u > HULL1_MAX_STEP_U + 1e-4:
            raise ValueError(f"Curb height {rise_u:.1f}u exceeds Hull-1 step limit ({HULL1_MAX_STEP_U:.0f}u)")
        self._curbs.append({"rise_u": rise_u})
        self.box_ft(x0, y0, z0, x1, y1, z1, tex, group=group)

    def curb_m(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        tex: TexSpec,
        group: str = "detail",
    ) -> None:
        self.curb_ft(
            x0 * FT_PER_M, y0 * FT_PER_M, z0 * FT_PER_M,
            x1 * FT_PER_M, y1 * FT_PER_M, z1 * FT_PER_M,
            tex, group=group,
        )

    def awning_ft(
        self,
        axis: str,
        x0_ft: float,
        y0_ft: float,
        x1_ft: float,
        y1_ft: float,
        z_wall_ft: float,
        z_outer_ft: float,
        slope_dir: int,
        tex: TexSpec,
        thick_ft: float = 0.25,
        group: str = "detail",
    ) -> None:
        if axis == "x":
            zl, zr = (z_wall_ft, z_outer_ft) if slope_dir > 0 else (z_outer_ft, z_wall_ft)
            self.slab_ramp_xft(x0_ft, x1_ft, y0_ft, y1_ft, zl, zr, tex, thick_ft=thick_ft, group=group)
        else:
            zb, zt = (z_wall_ft, z_outer_ft) if slope_dir > 0 else (z_outer_ft, z_wall_ft)
            self.slab_ramp_yft(x0_ft, x1_ft, y0_ft, y1_ft, zb, zt, tex, thick_ft=thick_ft, group=group)

    def awning_m(
        self,
        axis: str,
        x0_m: float,
        y0_m: float,
        x1_m: float,
        y1_m: float,
        z_wall_m: float,
        z_outer_m: float,
        slope_dir: int,
        tex: TexSpec,
        thick_m: float = 0.08,
        group: str = "detail",
    ) -> None:
        self.awning_ft(
            axis,
            x0_m * FT_PER_M, y0_m * FT_PER_M,
            x1_m * FT_PER_M, y1_m * FT_PER_M,
            z_wall_m * FT_PER_M, z_outer_m * FT_PER_M,
            slope_dir, tex, thick_ft=thick_m * FT_PER_M, group=group,
        )

    # ==========================================================================
    # 8. HULL-1 NAVIGATION REGISTRATIONS & SPOTS
    # ==========================================================================

    def register_door(
        self,
        name: str,
        width_u: float,
        height_u: float,
        origin_u: Optional[Tuple[float, float, float]] = None,
        axis: str = "x",
    ) -> Dict[str, object]:
        w = float(width_u)
        h = float(height_u)
        if w < HULL1_MIN_DOOR_W_U - 1e-4 or h < HULL1_MIN_DOOR_H_U - 1e-4:
            raise ValueError(
                f"Hull-1 doorway violation for '{name}': {w:.1f}u x {h:.1f}u "
                f"(minimum {HULL1_MIN_DOOR_W_U:.0f}u wide x {HULL1_MIN_DOOR_H_U:.0f}u tall)"
            )
        rec: Dict[str, object] = {
            "name": str(name),
            "width_u": round(w, 2),
            "height_u": round(h, 2),
            "axis": axis,
        }
        if origin_u is not None:
            rec["origin_u"] = [round(float(v), 2) for v in origin_u]
        self._doorways.append(rec)
        return rec

    def register_doorway_ft(
        self,
        name: str,
        width_ft: float,
        height_ft: float,
        origin_ft: Optional[Tuple[float, float, float]] = None,
        axis: str = "x",
    ) -> Dict[str, object]:
        orig_u = tuple(v * self.u_per_ft for v in origin_ft) if origin_ft is not None else None
        return self.register_door(name, width_ft * self.u_per_ft, height_ft * self.u_per_ft, orig_u, axis=axis)

    def register_doorway_m(
        self,
        name: str,
        width_m: float,
        height_m: float,
        origin_m: Optional[Tuple[float, float, float]] = None,
        axis: str = "x",
    ) -> Dict[str, object]:
        orig_u = tuple(v * self.u_per_m for v in origin_m) if origin_m is not None else None
        return self.register_door(name, width_m * self.u_per_m, height_m * self.u_per_m, orig_u, axis=axis)

    def add_doorway(
        self,
        name: str,
        wall_axis: str,
        pos_ft: float,
        span0_ft: float,
        span1_ft: float,
        door0_ft: float,
        door1_ft: float,
        z0_ft: float,
        door_top_ft: float,
        wall_top_ft: float,
        thick_ft: float,
        tex_wall: TexSpec,
        tex_inside: Optional[TexSpec] = None,
        group: str = "world",
        force_world: bool = False,
    ) -> None:
        """Build a wall containing a validated >=64x96u doorway opening along wall_axis ('x' or 'y')."""
        self._wall_axis_u(
            wall_axis,
            pos_ft * self.u_per_ft,
            span0_ft * self.u_per_ft,
            span1_ft * self.u_per_ft,
            z0_ft * self.u_per_ft,
            wall_top_ft * self.u_per_ft,
            thick_ft * self.u_per_ft,
            tex_wall,
            doorways_u=[(door0_ft * self.u_per_ft, door1_ft * self.u_per_ft, door_top_ft * self.u_per_ft, name)],
            tex_inside=tex_inside,
            group=group,
            force_world=force_world,
            name_prefix=name,
        )

    def register_stair(
        self,
        name: str,
        step_rise_u: float,
        num_steps: Optional[int] = None,
        has_clip_ramp: bool = True,
    ) -> Dict[str, object]:
        r = float(step_rise_u)
        if r <= 0.0 or r > HULL1_MAX_STEP_U + 1e-4:
            raise ValueError(
                f"Hull-1 stair violation for '{name}': step rise {r:.2f}u "
                f"(must be 0 < rise <= {HULL1_MAX_STEP_U:.0f}u)"
            )
        if not has_clip_ramp:
            raise ValueError(f"Hull-1 stair violation for '{name}': missing smooth clip ramp")
        rec = {
            "name": str(name),
            "step_rise_u": round(r, 2),
            "num_steps": int(num_steps) if num_steps is not None else None,
            "has_clip_ramp": True,
        }
        self._stairs.append(rec)
        return rec

    def register_room(self, name: str, clear_height_u: float) -> Dict[str, object]:
        ch = float(clear_height_u)
        if ch < HULL1_MIN_CEIL_U - 1e-4:
            raise ValueError(
                f"Hull-1 ceiling violation for '{name}': {ch:.1f}u < {HULL1_MIN_CEIL_U:.0f}u minimum"
            )
        rec = {"name": str(name), "clear_height_u": round(ch, 2)}
        self._rooms.append(rec)
        return rec

    def register_room_ft(self, name: str, floor_z_ft: float, ceil_z_ft: float) -> Dict[str, object]:
        return self.register_room(name, (float(ceil_z_ft) - float(floor_z_ft)) * self.u_per_ft)

    def register_room_m(self, name: str, floor_z_m: float, ceil_z_m: float) -> Dict[str, object]:
        return self.register_room(name, (float(ceil_z_m) - float(floor_z_m)) * self.u_per_m)

    def register_spot(
        self,
        name: str,
        x_u: float,
        y_u: float,
        z_u: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
        kind: str = "audit",
        desc: str = "",
    ) -> Dict[str, object]:
        rec = {
            "name": str(name),
            "kind": str(kind),
            "origin": [round(float(x_u), 1), round(float(y_u), 1), round(float(z_u), 1)],
            "angles": [round(float(pitch), 1), round(float(yaw), 1), 0.0],
            "desc": str(desc),
        }
        self._spots.append(rec)
        return rec

    def spot_ft(
        self,
        name: str,
        x_ft: float,
        y_ft: float,
        z_ft: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
        kind: str = "audit",
        desc: str = "",
    ) -> Dict[str, object]:
        return self.register_spot(
            name, x_ft * self.u_per_ft, y_ft * self.u_per_ft, z_ft * self.u_per_ft,
            yaw=yaw, pitch=pitch, kind=kind, desc=desc,
        )

    def spot_m(
        self,
        name: str,
        x_m: float,
        y_m: float,
        z_m: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
        kind: str = "audit",
        desc: str = "",
    ) -> Dict[str, object]:
        return self.register_spot(
            name, x_m * self.u_per_m, y_m * self.u_per_m, z_m * self.u_per_m,
            yaw=yaw, pitch=pitch, kind=kind, desc=desc,
        )

    # ==========================================================================
    # 9. POINT ENTITIES & LIGHTING HELPERS
    # ==========================================================================

    def ent_u(self, classname: str, x_u: float, y_u: float, z_u: float, **kv) -> Dict[str, str]:
        d: Dict[str, str] = {
            "classname": str(classname),
            "origin": f"{_fmt_num(x_u)} {_fmt_num(y_u)} {_fmt_num(z_u)}",
        }
        for k, v in kv.items():
            if v is None:
                continue
            if isinstance(v, (tuple, list)):
                d[str(k)] = " ".join(_fmt_num(float(c)) for c in v)
            else:
                d[str(k)] = str(v)
        self._entities.append(d)
        return d

    def ent_ft(self, classname: str, x_ft: float, y_ft: float, z_ft: float, **kv) -> Dict[str, str]:
        return self.ent_u(classname, x_ft * self.u_per_ft, y_ft * self.u_per_ft, z_ft * self.u_per_ft, **kv)

    def ent_m(self, classname: str, x_m: float, y_m: float, z_m: float, **kv) -> Dict[str, str]:
        return self.ent_u(classname, x_m * self.u_per_m, y_m * self.u_per_m, z_m * self.u_per_m, **kv)

    def light_ft(
        self,
        x_ft: float,
        y_ft: float,
        z_ft: float,
        light: float = 260.0,
        color: Tuple[int, int, int] = (255, 224, 178),
        style: int = 0,
        wait: float = 0.75,
        delay: int = 0,
    ) -> Dict[str, str]:
        return self.ent_ft(
            "light", x_ft, y_ft, z_ft,
            light=int(round(light)),
            _color=f"{int(color[0])} {int(color[1])} {int(color[2])}",
            style=int(style) if style else None,
            wait=wait,
            delay=int(delay) if delay else None,
        )

    def light_m(
        self,
        x_m: float,
        y_m: float,
        z_m: float,
        light: float = 260.0,
        color: Tuple[int, int, int] = (255, 224, 178),
        style: int = 0,
        wait: float = 0.75,
        delay: int = 0,
    ) -> Dict[str, str]:
        return self.light_ft(
            x_m * FT_PER_M, y_m * FT_PER_M, z_m * FT_PER_M,
            light=light, color=color, style=style, wait=wait, delay=delay,
        )

    def interior_lights_ft(
        self,
        x0_ft: float,
        y0_ft: float,
        x1_ft: float,
        y1_ft: float,
        z_ft: float,
        nx: int = 2,
        ny: int = 2,
        light: float = 260.0,
        color: Tuple[int, int, int] = (255, 224, 178),
        wait: float = 0.75,
    ) -> int:
        cnt = 0
        for ix in range(max(int(nx), 1)):
            fx = (ix + 0.5) / max(int(nx), 1)
            lx = x0_ft + (x1_ft - x0_ft) * fx
            for iy in range(max(int(ny), 1)):
                fy = (iy + 0.5) / max(int(ny), 1)
                ly = y0_ft + (y1_ft - y0_ft) * fy
                self.light_ft(lx, ly, z_ft, light=light, color=color, wait=wait)
                cnt += 1
        return cnt

    def interior_lights_m(
        self,
        x0_m: float,
        y0_m: float,
        x1_m: float,
        y1_m: float,
        z_m: float,
        nx: int = 2,
        ny: int = 2,
        light: float = 260.0,
        color: Tuple[int, int, int] = (255, 224, 178),
        wait: float = 0.75,
    ) -> int:
        return self.interior_lights_ft(
            x0_m * FT_PER_M, y0_m * FT_PER_M, x1_m * FT_PER_M, y1_m * FT_PER_M, z_m * FT_PER_M,
            nx=nx, ny=ny, light=light, color=color, wait=wait,
        )

    # Compatibility alias matching soi6_lib naming
    shophouse_lights_m = interior_lights_m
    shophouse_lights_ft = interior_lights_ft

    def street_fill_lights_ft(
        self,
        x_ft: float,
        y0_ft: float,
        y1_ft: float,
        z_ft: float = 24.0,
        step_ft: float = 95.0,
        light: float = 240.0,
        color: Tuple[int, int, int] = (255, 232, 195),
        wait: float = 0.6,
    ) -> int:
        span = abs(y1_ft - y0_ft)
        count = max(1, int(round(span / max(step_ft, 10.0))) + 1)
        for i in range(count):
            t = 0.5 if count == 1 else i / (count - 1)
            self.light_ft(x_ft, y0_ft + (y1_ft - y0_ft) * t, z_ft, light=light, color=color, wait=wait)
        return count

    def street_fill_lights_m(
        self,
        x_m: float,
        y0_m: float,
        y1_m: float,
        z_m: float = 7.3,
        step_m: float = 29.0,
        light: float = 240.0,
        color: Tuple[int, int, int] = (255, 232, 195),
        wait: float = 0.6,
    ) -> int:
        return self.street_fill_lights_ft(
            x_m * FT_PER_M, y0_m * FT_PER_M, y1_m * FT_PER_M,
            z_ft=z_m * FT_PER_M, step_ft=step_m * FT_PER_M,
            light=light, color=color, wait=wait,
        )

    # ==========================================================================
    # 10. SPATIAL CHUNKING, STATS, VALIDATION & MAP EXPORT
    # ==========================================================================

    def _spatial_chunks(
        self,
        brushes: Sequence[Tuple[Tuple[float, float, float, float, float, float], List[str]]],
        cell_u: Optional[float] = None,
    ) -> List[List[List[str]]]:
        step = float(cell_u or self.chunk_size_u)
        buckets: Dict[Tuple[int, int], List[List[str]]] = {}
        for bbox, lines in brushes:
            cx = 0.5 * (bbox[0] + bbox[3])
            cy = 0.5 * (bbox[1] + bbox[4])
            key = (int(math.floor(cx / step)), int(math.floor(cy / step)))
            buckets.setdefault(key, []).append(lines)
        return [buckets[k] for k in sorted(buckets)]

    def default_world_kv(self) -> Dict[str, str]:
        return {
            "classname": "worldspawn",
            "message": "Golden West Casino & S Union Ave, Bakersfield, CA",
            "wad": os.path.basename(DEFAULT_WAD_PATH),
            "sky": SKY_NAME,
            "_sunlight": "235",
            "_sunlight_color": "255 247 226",
            "_sun_mangle": SUN_MANGLE,
            "_sunlight2": "165",
            "_sunlight2_color": "212 232 255",
            "_sunlight3": "76",
            "_sunlight3_color": "234 222 204",
            "_dirt": "1",
            "_dirtscale": "0.30",
            "_dirtdepth": "72",
            "_minlight": "24",
            "_bounce": "1",
        }

    def validate_all(self) -> List[str]:
        """Validate textures, naming, Hull-1 clearances, and geometry sanity; raises ValueError on violations."""
        errors: List[str] = []
        if self._forbidden_textures_seen:
            unique_bad = sorted({t for t, _ctx in self._forbidden_textures_seen})
            errors.append(
                f"Forbidden legacy textures referenced ({len(unique_bad)}): {', '.join(unique_bad[:12])}"
            )
        if self._oversize_textures_seen:
            unique_long = sorted(set(self._oversize_textures_seen))
            errors.append(
                f"Texture names exceeding {MAX_TEX_NAME_LEN} chars: {', '.join(unique_long[:12])}"
            )
        if self.require_gwc_prefix:
            non_gwc = sorted(
                t for t in self._textures_used
                if not (t.lower().startswith("gwc_") or t.lower().startswith("{gwc_"))
            )
            if non_gwc:
                errors.append(f"Non-gwc textures with require_gwc_prefix=True: {', '.join(non_gwc[:12])}")
        if self.check_textures and self._missing_textures:
            errors.append(
                f"Missing textures from WAD/disk ({len(self._missing_textures)}): "
                + ", ".join(sorted(self._missing_textures)[:15])
            )
        for d in self._doorways:
            if float(d["width_u"]) < HULL1_MIN_DOOR_W_U - 1e-4 or float(d["height_u"]) < HULL1_MIN_DOOR_H_U - 1e-4:
                errors.append(f"Doorway '{d['name']}' under Hull-1 minimum: {d['width_u']}u x {d['height_u']}u")
        for s in self._stairs:
            if float(s["step_rise_u"]) > HULL1_MAX_STEP_U + 1e-4 or not s.get("has_clip_ramp"):
                errors.append(f"Stair '{s['name']}' fails Hull-1 check: {s}")
        for r in self._rooms:
            if float(r["clear_height_u"]) < HULL1_MIN_CEIL_U - 1e-4:
                errors.append(f"Room '{r['name']}' ceiling {r['clear_height_u']}u < {HULL1_MIN_CEIL_U}u")
        if sum(len(v) for v in self._brushes.values()) == 0:
            errors.append("MapBuilder contains 0 brushes")

        if errors:
            raise ValueError("MapBuilder validation failed:\n  - " + "\n  - ".join(errors))

        warnings: List[str] = []
        if not self.loaded_wads:
            warnings.append("Running in pre-WAD bootstrap mode (gw2.wad not found yet)")
        if self._bootstrap_textures_used:
            warnings.append(
                f"{len(self._bootstrap_textures_used)} texture(s) sized via disk PNG or bootstrap fallback"
            )
        return warnings

    def stats(self) -> Dict[str, object]:
        detail_chunks = len(self._spatial_chunks(self._brushes["detail"]))
        illus_chunks = len(self._spatial_chunks(self._brushes["illus"]))
        fence_chunks = len(self._spatial_chunks(self._brushes["fence"], cell_u=self.fence_chunk_size_u))
        total_brushes = sum(len(v) for v in self._brushes.values())
        return {
            "brushes": {k: len(v) for k, v in self._brushes.items()},
            "total_brushes": total_brushes,
            "spatial_chunks": {
                "chunk_size_m": CHUNK_SIZE_M,
                "fence_chunk_size_m": FENCE_CHUNK_SIZE_M,
                "chunk_size_u": round(self.chunk_size_u, 2),
                "fence_chunk_size_u": round(self.fence_chunk_size_u, 2),
                "detail": detail_chunks,
                "illus": illus_chunks,
                "fence_func_wall": fence_chunks,
            },
            "entities": len(self._entities),
            "doorways": len(self._doorways),
            "stairs": len(self._stairs),
            "rooms": len(self._rooms),
            "spots": len(self._spots),
            "textures_used": sorted(self._textures_used),
            "loaded_wads": list(self.loaded_wads),
            "bootstrap_textures_used": sorted(self._bootstrap_textures_used),
            "missing_textures": sorted(self._missing_textures),
        }

    def write_spots(self, path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        payload = {"scale_u_per_ft": self.u_per_ft, "spots": self._spots}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path

    def write_map(
        self,
        out_map_path: str,
        world_kv: Optional[Dict[str, str]] = None,
        validate: bool = True,
        spots_path: Optional[str] = None,
    ) -> Dict[str, object]:
        if validate:
            self.validate_all()

        out_abs = os.path.abspath(out_map_path)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)

        wkv = self.default_world_kv()
        if world_kv:
            wkv.update({str(k): str(v) for k, v in world_kv.items() if v is not None})

        def fmt_brush(planes: Sequence[str], out_lines: List[str]) -> None:
            out_lines.append("{")
            for pl in planes:
                out_lines.append(f"  {pl}")
            out_lines.append("}")

        out: List[str] = ["// Golden West Casino & S Union Ave (Bakersfield, CA) - Valve 220", "{"]
        for k, v in wkv.items():
            out.append(f'  "{k}" "{v}"')
        for _bbox, planes in self._brushes["world"]:
            fmt_brush(planes, out)
        for _bbox, planes in self._brushes["clip"]:
            fmt_brush(planes, out)
        out.append("}")

        for grp, classname, extra_kv in (
            ("detail", "func_detail", {"_chop": "0"}),
            ("illus", "func_detail_illusionary", {"_chop": "0"}),
            ("fence", "func_wall", {"_alpha": "1"}),
        ):
            cell_u = self.fence_chunk_size_u if grp == "fence" else self.chunk_size_u
            for chunk in self._spatial_chunks(self._brushes[grp], cell_u=cell_u):
                out.append("{")
                out.append(f'  "classname" "{classname}"')
                for ek, ev in extra_kv.items():
                    out.append(f'  "{ek}" "{ev}"')
                for planes in chunk:
                    fmt_brush(planes, out)
                out.append("}")

        for ent in self._entities:
            out.append("{")
            for k, v in ent.items():
                out.append(f'  "{k}" "{v}"')
            out.append("}")

        with open(out_abs, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")

        written_spots = spots_path
        if written_spots is None and self._spots:
            base, _ = os.path.splitext(out_abs)
            written_spots = base + ".spots.json"
        if written_spots:
            self.write_spots(written_spots)

        res = self.stats()
        res["map_path"] = out_abs
        res["spots_path"] = written_spots
        return res
