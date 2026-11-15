"""audit1_capture.py — Audit 1 of 5: Visual Reference Side-by-Side Comparison Capture
for Golden West Casino & S Union Ave.

Modeled on source/mm_tools/soi6/audit1_capture.py and wired directly to:
  - source/mm_tools/out/gw_ref_audit/REF_INVENTORY.md
  - source/mm_tools/out/gw_ref_audit/extracted_html_imgs/ (190 HTML gallery photos)
  - source/mm_tools/ref_sources/golden_west_gallery/ (348 route photos + overhead zooms)
  - source/mm_tools/out/web/goldenwest/ (Three.js WebGL viewer, bright=1.00)
  - G:\\Quake\\Combat\\darkplaces.exe (live windowed DarkPlaces parity shots)

Outputs:
  - source/mm_tools/goldenwest/out/audit1/pair_*.jpg (Ref | WebGL | DarkPlaces plates)
  - source/mm_tools/goldenwest/out/audit1/sheet_exterior_*.jpg & sheet_interior_*.jpg
  - source/mm_tools/goldenwest/out/audit1_manifest.json
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GAME_ROOT = os.path.dirname(MOD_DIR)

if HERE not in sys.path:
    sys.path.insert(0, HERE)

from gw_lib import U_FT  # noqa: E402
from audit3_nav import (  # noqa: E402
    DP_EXE,
    QuietHandler,
    SPOTS_CANDIDATES,
    _running_darkplaces_pids,
    load_spots,
)

OUT_ROOT = os.path.join(HERE, "out")
AUDIT1_DIR = os.path.join(OUT_ROOT, "audit1")
MANIFEST_PATH = os.path.join(OUT_ROOT, "audit1_manifest.json")

REF_AUDIT_DIR = os.path.join(MM_TOOLS, "out", "gw_ref_audit")
REF_INVENTORY_MD = os.path.join(REF_AUDIT_DIR, "REF_INVENTORY.md")
REF_HTML_DIR = os.path.join(REF_AUDIT_DIR, "extracted_html_imgs")
REF_GALLERY_DIR = os.path.join(MM_TOOLS, "ref_sources", "golden_west_gallery")
GC_REF_IMG_DIR = os.path.join(MM_TOOLS, "out", "gc_ref_audit", "images")
DEFAULT_WEB_DIR = os.path.join(MM_TOOLS, "out", "web", "goldenwest")
BSP_PATH = os.path.join(MOD_DIR, "maps", "goldenwest.bsp")

# Curated exterior, aerial & interior comparison views in feet (converted via U_FT=12).
# Ref tuples ("html"|"gallery", filename) match verified files in REF_INVENTORY.md.
# When goldenwest.spots.json is present, matching spot coordinates override fallback interior
# poses so camera positions stay centered inside author-built navigable rooms.
GW_AUDIT1_VIEWS: Tuple[Dict[str, object], ...] = (
    # --- AERIAL & EXTERIOR VIEWS ---
    {
        "id": "ext_01_aerial_casino",
        "category": "exterior",
        "label": "Aerial Oblique: Golden West Casino 26-Vertex Roof, Rotunda & Clerestory",
        "pos_ft": (220.0, -140.0, 125.0),
        "yaw": 158.0,
        "pitch": 34.0,
        "spot_keywords": ("aerial", "casino overhead"),
        "refs": (("gallery", "gw_casino_zoom.jpg"), ("html", "008.jpg")),
    },
    {
        "id": "ext_02_aerial_corridor",
        "category": "exterior",
        "label": "Aerial Corridor: S Union 3+3 Boulevard, Brick Median & Palm Clusters",
        "pos_ft": (228.0, -560.0, 130.0),
        "yaw": 90.0,
        "pitch": 22.0,
        "spot_keywords": (),
        "refs": (("gallery", "gw_grid_z19.jpg"), ("html", "010.jpg")),
    },
    {
        "id": "ext_03_union_looking_north",
        "category": "exterior",
        "label": "S Union Ave Looking N: 3+3 Lanes, Concrete Slab, Brick Median & Star-Liter",
        "pos_ft": (200.0, -145.0, 7.0),
        "yaw": 75.0,
        "pitch": -2.0,
        "spot_keywords": ("union north", "ca-99"),
        "refs": (("html", "012.jpg"), ("gallery", "037.jpg")),
    },
    {
        "id": "ext_04_union_looking_south",
        "category": "exterior",
        "label": "S Union Ave Looking S: North Palms (y=181..269), CA-99 BUS & Fence Line",
        "pos_ft": (202.0, 235.0, 8.0),
        "yaw": -98.0,
        "pitch": 2.0,
        "spot_keywords": (),
        "refs": (("html", "016.jpg"), ("gallery", "029.jpg")),
    },
    {
        "id": "ext_05_casino_pylon_facade",
        "category": "exterior",
        "label": "Golden West Exterior: Purple Pylon, Split-Face Stone, Clerestory & Iron Fence",
        "pos_ft": (205.0, 5.0, 7.0),
        "yaw": 182.0,
        "pitch": -4.0,
        "spot_keywords": ("casino front", "pylon", "golden west exterior"),
        "refs": (("html", "018.jpg"), ("gallery", "043.jpg")),
    },
    {
        "id": "ext_06_casino_south_pillars",
        "category": "exterior",
        "label": "Casino South Driveway: Capped Stone Pillars, SE Stone Wing & Parking",
        "pos_ft": (195.0, -90.0, 6.5),
        "yaw": 175.0,
        "pitch": -2.0,
        "spot_keywords": ("south gate", "stone pillars"),
        "refs": (("html", "026.jpg"), ("gallery", "035.jpg")),
    },
    {
        "id": "ext_07_casino_ne_portico_horse",
        "category": "exterior",
        "label": "Casino NE 45-Deg Portico: Clerestory Transoms, US Flags & Horse Statue",
        "pos_ft": (102.0, 52.0, 6.5),
        "yaw": 225.0,
        "pitch": -4.0,
        "spot_keywords": ("portico", "horse", "courtyard"),
        "refs": (("html", "113.jpg"), ("html", "114.jpg")),
    },
    {
        "id": "ext_08_guard_booth_north_lot",
        "category": "exterior",
        "label": "Casino North Entrance: Tan Guard Booth (120, 195) & North Parking Aisles",
        "pos_ft": (165.0, 165.0, 6.5),
        "yaw": 150.0,
        "pitch": -2.0,
        "spot_keywords": ("guard booth ext", "north entrance"),
        "refs": (("html", "019.jpg"), ("html", "088.jpg")),
    },
    {
        "id": "ext_09_belle_terrace_carnitas",
        "category": "exterior",
        "label": "E Belle Terrace & S Union: Mast Signals, Street Blades & Carnitas Diner",
        "pos_ft": (220.0, 520.0, 8.0),
        "yaw": 122.0,
        "pitch": -3.0,
        "spot_keywords": ("belle terrace", "carnitas"),
        "refs": (("html", "033.jpg"), ("gallery", "059.jpg")),
    },
    {
        "id": "ext_10_891_green_mesh",
        "category": "exterior",
        "label": "891 S Union Open Dirt Lot: Green Privacy-Mesh Fence & Billboards (No Bldgs)",
        "pos_ft": (192.0, 415.0, 7.0),
        "yaw": 180.0,
        "pitch": -2.0,
        "spot_keywords": ("891", "green mesh"),
        "refs": (("html", "084.jpg"), ("gallery", "051.jpg")),
    },
    {
        "id": "ext_11_el_don_brownfield",
        "category": "exterior",
        "label": "SE Belle Terrace Brownfield: Demolished El Don Empty Lot + El Don Signs",
        "pos_ft": (238.0, 520.0, 7.5),
        "yaw": -22.0,
        "pitch": -2.0,
        "spot_keywords": ("el don", "brownfield"),
        "refs": (("html", "039.jpg"), ("html", "041.jpg")),
    },
    {
        "id": "ext_12_star_liter_motel",
        "category": "exterior",
        "label": "Star-Liter Motor Motel & 922 RV Park: Red Siding, CMU Wall & Yellow Pylon",
        "pos_ft": (202.0, 75.0, 7.0),
        "yaw": 42.0,
        "pitch": -4.0,
        "spot_keywords": (),
        "refs": (("html", "013.jpg"), ("html", "086.jpg")),
    },
    {
        "id": "ext_13_ramos_and_compas",
        "category": "exterior",
        "label": "Ramos Tires & Compas Auto (Best DEALS): Slate Office, Palms & Iron Fence",
        "pos_ft": (256.0, -445.0, 7.0),
        "yaw": 148.0,
        "pitch": 2.0,
        "spot_keywords": (),
        "refs": (("html", "067.jpg"), ("html", "021.jpg")),
    },
    {
        "id": "ext_14_sunland_country_playfair",
        "category": "exterior",
        "label": "East Union South: Sunland Breeze-Block, Country Inn Fin & Playfair Mural",
        "pos_ft": (210.0, -576.0, 7.0),
        "yaw": -15.0,
        "pitch": -2.0,
        "spot_keywords": (),
        "refs": (("gallery", "023.jpg"), ("html", "063.jpg")),
    },
    {
        "id": "ext_15_super8_corner",
        "category": "exterior",
        "label": "Super 8 by Wyndham (1219 S Union): Chimney, Diamond Pylon & 2F Rear Wing",
        "pos_ft": (205.0, -675.0, 7.5),
        "yaw": 155.0,
        "pitch": -3.0,
        "spot_keywords": ("ext_15_super8_motel",),
        "refs": (("gallery", "025.jpg"), ("gallery", "026.jpg")),
    },
    {
        "id": "ext_16_west_residential",
        "category": "exterior",
        "label": "Delaware St & Trinity Ave Residential: 1950s Ranch Houses, Carports & Lawns",
        "pos_ft": (-122.0, -230.0, 7.0),
        "yaw": 190.0,
        "pitch": -1.0,
        "spot_keywords": ("ext_16_delaware_trinity", "trinity ave"),
        "refs": (("html", "076.jpg"), ("html", "078.jpg")),
    },
    # --- INTERIOR VIEWS ---
    {
        "id": "int_01_casino_vestibule",
        "category": "interior",
        "label": "Casino Interior: NE Entrance Vestibule & Security/Host Podium",
        "pos_ft": (62.0, 10.0, 5.5),
        "yaw": 215.0,
        "pitch": 2.0,
        "spot_keywords": ("vestibule", "security"),
        "refs": (("html", "113.jpg"), ("html", "169.jpg")),
    },
    {
        "id": "int_02_casino_poker_pit",
        "category": "interior",
        "label": "Casino Interior: Main Poker Hall, Heavy Timber Trusses & Ceiling Soffits",
        "pos_ft": (12.0, -20.0, 5.5),
        "yaw": 175.0,
        "pitch": 5.0,
        "spot_keywords": ("poker", "pit", "gaming floor"),
        "refs": (("html", "169.jpg"), ("html", "171.jpg")),
    },
    {
        "id": "int_03_casino_red_felt_tables",
        "category": "interior",
        "label": "Casino Interior: Burgundy-Red GWC Felt Tables & Brass Cup Holders (0 Stones)",
        "pos_ft": (5.0, 25.0, 5.5),
        "yaw": -90.0,
        "pitch": 14.0,
        "spot_keywords": ("felt", "table"),
        "refs": (("html", "115.jpg"), ("html", "120.jpg")),
    },
    {
        "id": "int_04_casino_cashier_cage",
        "category": "interior",
        "label": "Casino Interior: West Wall 2-Bay Corrugated Cashier Cage & Chip Counter",
        "pos_ft": (2.0, -10.0, 5.5),
        "yaw": 180.0,
        "pitch": 2.0,
        "spot_keywords": ("cage", "cashier"),
        "refs": (("html", "152.jpg"), ("html", "163.jpg")),
    },
    {
        "id": "int_05_casino_lounge_bar",
        "category": "interior",
        "label": "Casino Interior: Rotunda Radial Ribs, Back-Bar & Blackjack Lounge Neon",
        "pos_ft": (62.0, -25.0, 5.5),
        "yaw": -15.0,
        "pitch": -4.0,
        "spot_keywords": ("lounge", "rotunda", "bar"),
        "refs": (("html", "108.jpg"), ("html", "160.jpg")),
    },
    {
        "id": "int_06_casino_buddha_shrine",
        "category": "interior",
        "label": "Casino Interior: South Window Alcove & Golden Laughing Buddha Shrine",
        "pos_ft": (-5.0, -45.0, 5.5),
        "yaw": -90.0,
        "pitch": 4.0,
        "spot_keywords": ("buddha", "shrine", "alcove"),
        "refs": (("html", "165.jpg"), ("html", "171.jpg")),
    },
    {
        "id": "int_07_guard_booth",
        "category": "interior",
        "label": "Interior: North Lot Enterable Guard Booth",
        "pos_ft": (120.0, 195.0, 5.0),
        "yaw": 180.0,
        "pitch": 2.0,
        "spot_keywords": ("booth", "guard"),
        "refs": (("html", "019.jpg"), ("html", "088.jpg")),
    },
    {
        "id": "int_08_carnitas_diner",
        "category": "interior",
        "label": "Interior: Carnitas Birria Menudo Diner (Counter & Dining Booths)",
        "pos_ft": (120.0, 628.0, 5.5),
        "yaw": 45.0,
        "pitch": 2.0,
        "spot_keywords": ("carnitas", "diner", "menudo"),
        "refs": (("html", "033.jpg"), ("gallery", "059.jpg")),
    },
    {
        "id": "int_09_star_liter_interior",
        "category": "interior",
        "label": "Interior: Star-Liter Motor Motel Office / Courtyard Guest Room",
        "pos_ft": (335.0, 120.0, 5.5),
        "yaw": 0.0,
        "pitch": 2.0,
        "spot_keywords": ("star-liter", "star liter", "starliter"),
        "refs": (("html", "013.jpg"), ("html", "086.jpg")),
    },
    {
        "id": "int_10_ramos_tires_interior",
        "category": "interior",
        "label": "Interior: Ramos Tires & Service Bays & Lift",
        "pos_ft": (-20.0, -308.0, 5.5),
        "yaw": 180.0,
        "pitch": 2.0,
        "spot_keywords": ("int_10_ramos_tires", "ramos"),
        "refs": (("html", "067.jpg"), ("html", "060.jpg")),
    },
    {
        "id": "int_11_compas_auto_interior",
        "category": "interior",
        "label": "Interior: Compas Auto Sales Office",
        "pos_ft": (76.0, -499.0, 5.5),
        "yaw": 180.0,
        "pitch": 2.0,
        "spot_keywords": ("compas", "auto sales", "best deal"),
        "refs": (("gallery", "027.jpg"), ("html", "044.jpg")),
    },
    {
        "id": "int_12_sunland_country_interior",
        "category": "interior",
        "label": "Interior: Sunland / Country Inn Motel Check-In & Guest Wing",
        "pos_ft": (345.0, -295.0, 5.5),
        "yaw": 0.0,
        "pitch": 2.0,
        "spot_keywords": ("sunland", "country inn", "country"),
        "refs": (("html", "063.jpg"), ("html", "045.jpg")),
    },
    {
        "id": "int_13_playfair_market_interior",
        "category": "interior",
        "label": "Interior: Playfair Market Aisles, Coolers & Counter",
        "pos_ft": (322.0, -632.0, 5.5),
        "yaw": 0.0,
        "pitch": 2.0,
        "spot_keywords": ("playfair", "market", "liquor"),
        "refs": (("gallery", "023.jpg"), ("html", "046.jpg")),
    },
    {
        "id": "int_14_super8_interior",
        "category": "interior",
        "label": "Interior: Super 8 Lobby / 2F Balcony Wing",
        "pos_ft": (94.0, -622.0, 5.5),
        "yaw": 180.0,
        "pitch": 2.0,
        "spot_keywords": ("super 8", "super8"),
        "refs": (("gallery", "025.jpg"), ("gallery", "026.jpg")),
    },
    {
        "id": "int_15_west_house_interior",
        "category": "interior",
        "label": "Interior: West Delaware / Trinity 1950s Ranch House",
        "pos_ft": (-210.0, -225.0, 5.5),
        "yaw": 180.0,
        "pitch": 2.0,
        "spot_keywords": ("int_15_delaware_house", "delaware_house", "trinity_0665", "ranch_3823"),
        "refs": (("html", "076.jpg"), ("html", "080.jpg")),
    },
    {
        "id": "ext_17_gc_aerial",
        "category": "aerial",
        "label": "Aerial: Great Castle Restaurant (410 S Union) & E 4th / E 5th Block",
        "pos_ft": (245.0, 1015.0, 105.0),
        "yaw": 5.0,
        "pitch": 52.0,
        "fov": 90.0,
        "spot_keywords": (),
        "refs": (("gc_ref", "176_great-castle-z20-close-hybrid.jpg.jpg"), ("gc_ref", "177_great-castle-z20-close-sat.jpg.jpg")),
    },
    {
        "id": "ext_18_gc_union_west",
        "category": "exterior",
        "label": "S Union Ave Looking NE: Great Castle Crenellated West Facade & Pylon",
        "pos_ft": (200.0, 1020.0, 6.0),
        "yaw": 10.0,
        "pitch": -4.0,
        "fov": 90.0,
        "spot_keywords": (),
        "refs": (("gc_ref", "113_p15_yaw_0.jpg"), ("gc_ref", "161_maps_maps-af1qip-1.jpg.jpg")),
    },
    {
        "id": "ext_19_gc_watchtower_entry",
        "category": "exterior",
        "label": "Great Castle South Lot: SW Watchtower, Red Barrel Awning & Neon OPEN",
        "pos_ft": (342.0, 944.0, 6.0),
        "yaw": 64.0,
        "pitch": -7.0,
        "fov": 90.0,
        "spot_keywords": (),
        "refs": (("gc_ref", "164_maps_web-cafes-guide-1.jpg.jpg"), ("gc_ref", "161_maps_maps-af1qip-1.jpg.jpg")),
    },
    {
        "id": "ext_20_gc_e5th_north",
        "category": "exterior",
        "label": "S Union Ave & E 5th St: Reyes Tires, Great Castle North Lot & E 4th/E 5th",
        "pos_ft": (245.0, 1170.0, 6.5),
        "yaw": 310.0,
        "pitch": -2.0,
        "fov": 90.0,
        "spot_keywords": (),
        "refs": (("gc_ref", "145_p19_yaw_0.jpg"), ("gc_ref", "149_p19_yaw_180.jpg")),
    },
    {
        "id": "int_16_gc_vestibule",
        "category": "interior",
        "label": "Interior: Great Castle Entry Vestibule, Lattice Screen & Gold Fan",
        "pos_ft": (366.0, 999.2, 4.7),
        "yaw": 90.0,
        "pitch": 4.0,
        "fov": 90.0,
        "spot_keywords": ("gc_vestibule_entry",),
        "refs": (("gc_ref", "166_maps_web-yelp-1.jpg.jpg"), ("gc_ref", "165_maps_web-interior-restaurantguru.jpg.jpg")),
    },
    {
        "id": "int_17_gc_dining_lanterns",
        "category": "interior",
        "label": "Interior: Great Castle Main Dining Hall, Red Lanterns & Screens",
        "pos_ft": (363.0, 1015.0, 4.7),
        "yaw": 115.0,
        "pitch": 3.0,
        "fov": 90.0,
        "spot_keywords": ("gc_dining_main",),
        "refs": (("gc_ref", "163_maps_maps-places-1.jpg.jpg"), ("gc_ref", "165_maps_web-interior-restaurantguru.jpg.jpg")),
    },
    {
        "id": "int_18_gc_kitchen_boh",
        "category": "interior",
        "label": "Interior: Great Castle Kitchen / Back-of-House Pass & Stainless Tables",
        "pos_ft": (397.5, 1020.0, 4.7),
        "yaw": 70.0,
        "pitch": 2.0,
        "fov": 90.0,
        "spot_keywords": ("gc_kitchen_boh",),
        "refs": (("gc_ref", "166_maps_web-yelp-1.jpg.jpg"), ("gc_ref", "165_maps_web-interior-restaurantguru.jpg.jpg")),
    },
)


def _get_font(sz: int) -> ImageFont.ImageFont:
    for fp in (
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/tahomabd.ttf",
    ):
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, sz)
            except OSError:
                pass
    return ImageFont.load_default()


def resolve_ref_path(kind: str, filename: str) -> str:
    if kind == "html":
        return os.path.join(REF_HTML_DIR, filename)
    if kind == "gallery":
        return os.path.join(REF_GALLERY_DIR, filename)
    if kind == "gc_ref":
        return os.path.join(GC_REF_IMG_DIR, filename)
    raise ValueError(f"Unknown reference source kind: {kind!r}")


def verify_all_refs(views: Sequence[Dict[str, object]] = GW_AUDIT1_VIEWS) -> Tuple[List[str], int]:
    """Verify every reference file referenced by views exists on disk."""
    missing: List[str] = []
    total = 0
    for v in views:
        for kind, fname in v["refs"]:  # type: ignore[index]
            total += 1
            p = resolve_ref_path(str(kind), str(fname))
            if not os.path.isfile(p):
                missing.append(f"{v['id']}:{kind}/{fname} -> {p}")
    return missing, total


# Fallback aims if an exterior audit spot still has default zeroed (0, 0) orientation.
GC_SPOT_FALLBACK_ANGLES: Dict[str, Tuple[float, float]] = {
    "gc_union_pylon": (135.0, -3.0),
    "gc_sw_watchtower_entry": (98.0, -5.0),
    "gc_se_annex_alley": (135.0, -2.0),
}


def _spot_angles(
    sp: Dict[str, object],
    default_yaw: float = 0.0,
    default_pitch: float = 0.0,
) -> Tuple[float, float]:
    """Read (yaw, pitch) from spot metadata (`angles=[pitch, yaw, roll]` or `yaw`/`pitch`)."""
    angles = sp.get("angles")
    if isinstance(angles, (list, tuple)) and len(angles) >= 2:
        syaw = float(angles[1])
        spitch = float(angles[0])
    else:
        syaw = float(sp.get("yaw", default_yaw))
        spitch = float(sp.get("pitch", default_pitch))
    sname = str(sp.get("name", ""))
    if abs(syaw) < 1e-3 and abs(spitch) < 1e-3 and sname in GC_SPOT_FALLBACK_ANGLES:
        return GC_SPOT_FALLBACK_ANGLES[sname]
    return syaw, spitch


def _resolve_views_with_spots(
    views: Sequence[Dict[str, object]],
    spots: Sequence[Dict[str, object]],
) -> List[Dict[str, object]]:
    """Build concrete Quake-unit viewpoints, overriding interiors with matching .spots.json hits."""
    resolved: List[Dict[str, object]] = []
    used_spot_names: set = set()
    for v in views:
        entry = dict(v)
        px_ft, py_ft, pz_ft = v["pos_ft"]  # type: ignore[misc]
        pos_u = [round(px_ft * U_FT, 1), round(py_ft * U_FT, 1), round(pz_ft * U_FT, 1)]
        yaw = float(v["yaw"])  # type: ignore[arg-type]
        pitch = float(v["pitch"])  # type: ignore[arg-type]
        matched_spot: Optional[str] = None

        keywords = tuple(str(k).lower() for k in v.get("spot_keywords", ()))  # type: ignore[attr-defined]
        is_int = v.get("category") == "interior"
        is_gc_view = "_gc_" in str(v.get("id", ""))
        best_spot = None
        for kw in keywords:
            for sp in spots:
                sname = str(sp.get("name", "")).lower()
                skind = str(sp.get("kind", "")).lower()
                sdesc = str(sp.get("desc", "")).lower()
                hay = f"{sname} {sdesc}"
                if is_gc_view and not sname.startswith("gc_"):
                    continue
                if not is_gc_view and sname.startswith("gc_"):
                    continue
                if is_int and not (skind == "interior" or (is_gc_view and skind == "audit")):
                    continue
                if not is_int and skind == "interior":
                    continue
                if kw in hay and str(sp.get("name")) not in used_spot_names:
                    best_spot = sp
                    break
            if best_spot is not None:
                break

        if best_spot is not None:
            pos_u = [round(float(c), 1) for c in best_spot["origin"]]  # type: ignore[index]
            yaw, pitch = _spot_angles(best_spot, yaw, pitch)
            matched_spot = str(best_spot.get("name"))
            used_spot_names.add(matched_spot)

        entry["pos_u"] = pos_u
        entry["yaw"] = yaw
        entry["pitch"] = pitch
        entry["matched_spot"] = matched_spot
        resolved.append(entry)
    return resolved


def capture_webgl_views(
    views: Sequence[Dict[str, object]],
    spots: Sequence[Dict[str, object]],
    web_dir: str,
    out_dir: str,
) -> Dict[str, object]:
    """Capture headless Playwright Chromium WebGL shots for all views and remaining .spots."""
    if not os.path.isdir(web_dir) or not os.path.isfile(os.path.join(web_dir, "index.html")):
        return {
            "ran": False,
            "pass": False,
            "reason": f"WebGL bundle not found at {web_dir}",
            "shots": {},
            "spot_shots": {},
            "console_errors": [],
            "page_errors": [],
            "bad_responses": [],
        }

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return {
            "ran": False,
            "pass": False,
            "reason": f"Missing playwright in {sys.executable} (run with `py -3.13`): {exc}",
            "shots": {},
            "spot_shots": {},
            "console_errors": [],
            "page_errors": [],
            "bad_responses": [],
        }

    os.makedirs(out_dir, exist_ok=True)
    handler = functools.partial(QuietHandler, directory=web_dir)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    console_errors: List[str] = []
    page_errors: List[str] = []
    bad_responses: List[str] = []
    shots: Dict[str, str] = {}
    spot_shots: Dict[str, str] = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"],
            )
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on(
                "response",
                lambda r: bad_responses.append(f"{r.status} {r.url}") if r.status >= 400 else None,
            )

            page.goto(f"http://127.0.0.1:{port}/index.html?fly=1&nointro=1", wait_until="networkidle")
            page.wait_for_function("!document.getElementById('start').disabled", timeout=25000)
            page.evaluate(
                """() => {
                    const intro = document.getElementById('intro');
                    if (intro) intro.style.display = 'none';
                    if (window.__viewer && window.__viewer.setFly) window.__viewer.setFly(true);
                }"""
            )
            page.wait_for_timeout(350)

            for v in views:
                vid = str(v["id"])
                px, py, pz = v["pos_u"]  # type: ignore[misc]
                yaw = float(v["yaw"])  # type: ignore[arg-type]
                pitch = float(v["pitch"])  # type: ignore[arg-type]
                page.evaluate(
                    """([x, y, z, yaw, pitch]) => {
                        if (window.__viewer && window.__viewer.setFly) window.__viewer.setFly(true);
                        window.__viewer.teleport({pos: [x, y, z], yaw: yaw, pitch: pitch});
                    }""",
                    [px, py, pz, yaw, pitch],
                )
                page.wait_for_timeout(350)
                shot_path = os.path.join(out_dir, f"webgl_{vid}.png")
                page.screenshot(path=shot_path)
                shots[vid] = shot_path

            # Also capture all unique spots from goldenwest.spots.json for full tour parity
            for idx, sp in enumerate(spots):
                sname = str(sp.get("name", f"spot_{idx:02d}"))
                sx, sy, sz = (float(c) for c in sp["origin"])  # type: ignore[index]
                syaw, spitch = _spot_angles(sp)
                page.evaluate(
                    """([x, y, z, yaw, pitch]) => {
                        if (window.__viewer && window.__viewer.setFly) window.__viewer.setFly(true);
                        window.__viewer.teleport({pos: [x, y, z], yaw: yaw, pitch: pitch});
                    }""",
                    [sx, sy, sz, syaw, spitch],
                )
                page.wait_for_timeout(250)
                safe = re.sub(r"[^A-Za-z0-9_]", "_", sname)[:40]
                sp_path = os.path.join(out_dir, f"spot_{idx:02d}_{safe}.png")
                page.screenshot(path=sp_path)
                spot_shots[sname] = sp_path

            browser.close()
    finally:
        httpd.shutdown()

    return {
        "ran": True,
        "pass": not (console_errors or page_errors or bad_responses),
        "captured_views": len(shots),
        "captured_spots": len(spot_shots),
        "shots": shots,
        "spot_shots": spot_shots,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "bad_responses": bad_responses,
    }


def capture_darkplaces_views(
    views: Sequence[Dict[str, object]],
    out_dir: str,
) -> Dict[str, object]:
    """Capture live windowed DarkPlaces screenshots via prvm_edictset per CLAUDE.md rules."""
    if not os.path.isfile(DP_EXE):
        return {"ran": False, "pass": False, "reason": f"Missing {DP_EXE}", "shots": {}}
    if not os.path.isfile(BSP_PATH):
        return {"ran": False, "pass": False, "reason": f"Missing {BSP_PATH}", "shots": {}}
    active = _running_darkplaces_pids()
    if active:
        time.sleep(3.0)
        active = _running_darkplaces_pids()
        if active:
            return {
                "ran": False,
                "pass": False,
                "reason": f"Other darkplaces.exe instance active (PIDs {active}); aborting launch",
                "shots": {},
            }

    os.makedirs(out_dir, exist_ok=True)
    scr_dir = os.path.join(MOD_DIR, "screenshots")
    os.makedirs(scr_dir, exist_ok=True)
    before = set(os.listdir(scr_dir))
    tmp_cfgs: List[str] = []

    cfg_path = os.path.join(MOD_DIR, "config.cfg")
    cfg_backup: Optional[bytes] = None
    if os.path.isfile(cfg_path):
        with open(cfg_path, "rb") as f:
            cfg_backup = f.read()

    for idx, v in enumerate(views):
        vid = str(v["id"])
        px, py, pz = v["pos_u"]  # type: ignore[misc]
        yaw = float(v["yaw"])  # type: ignore[arg-type]
        pitch = float(v["pitch"])  # type: ignore[arg-type]
        scfg_name = f"_gw_audit1_dp_{idx}.cfg"
        scfg = os.path.join(MOD_DIR, scfg_name)
        tmp_cfgs.append(scfg)
        next_cmd = (
            f'defer 0.28 "exec _gw_audit1_dp_{idx + 1}.cfg"'
            if idx + 1 < len(views)
            else 'defer 0.28 "quit"'
        )
        lines: List[str] = []
        if idx == 0:
            lines += [
                "sv_cheats 1", "freelook 0", "-mlook", "cl_anglespeedkey 0",
                "r_hdr_scenebrightness 1", "v_gamma 1", "v_contrast 1", "v_brightness 0", "v_glslgamma 0",
                "r_glsl_saturation 1", "r_bloom 0", "gl_polyblend 0",
                "crosshair 0", "r_drawviewmodel 0", "cl_viewmodel_scale 0",
                "showfps 0", "viewsize 120", "scr_screenshot_png 1",
                "prvm_edictset server 1 movetype 8",
                "prvm_edictset server 1 solid 0",
                'prvm_edictset server 1 weaponmodel ""',
            ]
        lines += [
            f'prvm_edictset server 1 origin "{px:.1f} {py:.1f} {pz - 22.0:.1f}"',
            f'prvm_edictset server 1 angles "{pitch:.1f} {yaw:.1f} 0"',
            f'prvm_edictset server 1 v_angle "{pitch:.1f} {yaw:.1f} 0"',
            "prvm_edictset server 1 fixangle 1",
            'prvm_edictset server 1 velocity "0 0 0"',
            f"scr_screenshot_name gw_a1_{idx:02d}_{vid}_",
            'defer 0.20 "screenshot"',
            next_cmd,
        ]
        with open(scfg, "w", encoding="ascii") as f:
            f.write("\n".join(lines) + "\n")

    proc: Optional[subprocess.Popen[bytes]] = None
    shots: Dict[str, str] = {}
    try:
        proc = subprocess.Popen(
            [
                DP_EXE,
                "-window", "-width", "1280", "-height", "720",
                "-game", "quake15", "-game", "BakersfieldQuake",
                "-nosound", "-nohome",
                "+vid_mouse", "0", "+joy_enable", "0",
                "-condebug", "+log_file", "zz_gw_audit1.log",
                "+map", "goldenwest",
                "+defer", "3", "exec _gw_audit1_dp_0.cfg",
            ],
            cwd=GAME_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        timeout_s = max(60, 10 + 3 * len(views))
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            return {"ran": True, "pass": False, "reason": "DarkPlaces screenshot run timed out", "shots": {}}

        after = set(os.listdir(scr_dir))
        new_files = sorted(f for f in (after - before) if f.lower().endswith((".png", ".tga")))
        for idx, v in enumerate(views):
            vid = str(v["id"])
            prefix = f"gw_a1_{idx:02d}_{vid}_"
            match = next((fn for fn in new_files if fn.startswith(prefix)), None)
            if match is None and idx < len(new_files):
                match = new_files[idx]
            if match is not None:
                src = os.path.join(scr_dir, match)
                dst = os.path.join(out_dir, f"dp_{vid}.png")
                with Image.open(src) as dp_im:
                    dp_im.convert("RGB").save(dst)
                shots[vid] = dst

        return {
            "ran": True,
            "pass": len(shots) == len(views),
            "returncode": proc.returncode,
            "captured": len(shots),
            "shots": shots,
        }
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
        for fn in set(os.listdir(scr_dir)) - before:
            if fn.startswith("gw_a1_") and fn.lower().endswith((".png", ".tga")):
                try:
                    os.remove(os.path.join(scr_dir, fn))
                except OSError:
                    pass
        log_path = os.path.join(MOD_DIR, "zz_gw_audit1.log")
        if os.path.isfile(log_path):
            try:
                os.remove(log_path)
            except OSError:
                pass
        for p in tmp_cfgs:
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        if cfg_backup is not None:
            try:
                with open(cfg_path, "wb") as f:
                    f.write(cfg_backup)
            except OSError:
                pass


def _load_fitted_tile(path: Optional[str], w: int, h: int, placeholder_text: str) -> Image.Image:
    if path and os.path.isfile(path):
        with Image.open(path) as src:
            im = src.convert("RGB")
        return ImageOps.contain(im, (w, h), method=Image.Resampling.LANCZOS)
    tile = Image.new("RGB", (w, h), (34, 36, 44))
    dr = ImageDraw.Draw(tile)
    dr.rectangle([2, 2, w - 3, h - 3], outline=(80, 84, 96), width=2)
    dr.text((16, h // 2 - 8), placeholder_text, fill=(175, 180, 195), font=_get_font(16))
    return tile


def build_pair_plate(
    view: Dict[str, object],
    webgl_path: Optional[str],
    dp_path: Optional[str],
    out_path: str,
) -> str:
    """Create a labeled Ref | WebGL (| DarkPlaces) side-by-side comparison plate."""
    refs = view["refs"]  # type: ignore[index]
    ref_kind, ref_fn = refs[0]
    ref_path = resolve_ref_path(str(ref_kind), str(ref_fn))

    include_dp = bool(dp_path and os.path.isfile(dp_path))
    cols = 3 if include_dp else 2
    tile_w, tile_h = (560, 340) if cols == 3 else (640, 380)
    hdr_h = 44
    sub_h = 26
    pad = 12
    total_w = cols * tile_w + (cols + 1) * pad
    total_h = hdr_h + sub_h + tile_h + pad

    canvas = Image.new("RGB", (total_w, total_h), (20, 22, 27))
    draw = ImageDraw.Draw(canvas)
    f_title = _get_font(17)
    f_sub = _get_font(14)

    vid = str(view["id"])
    lbl = str(view["label"])
    draw.rectangle([0, 0, total_w, hdr_h], fill=(32, 36, 46))
    draw.text((pad, 11), f"[{vid}]  {lbl}", fill=(246, 224, 150), font=f_title)

    panes: List[Tuple[str, Optional[str], Tuple[int, int, int], str]] = [
        (f"REFERENCE: {ref_kind}/{ref_fn}", ref_path, (150, 220, 255), "Ref Missing"),
        ("WEBGL RENDER (bright=1.00)", webgl_path, (165, 245, 180), "WebGL Not Captured"),
    ]
    if include_dp:
        panes.append(("DARKPLACES (web.cfg parity)", dp_path, (255, 198, 130), "DP Not Captured"))

    for c_idx, (title, pth, color, fallback) in enumerate(panes):
        x0 = pad + c_idx * (tile_w + pad)
        y_sub = hdr_h + 4
        draw.text((x0, y_sub), title, fill=color, font=f_sub)
        tile = _load_fitted_tile(pth, tile_w, tile_h, fallback)
        bx = x0 + (tile_w - tile.width) // 2
        by = hdr_h + sub_h + (tile_h - tile.height) // 2
        canvas.paste(tile, (bx, by))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path, quality=90)
    return out_path


def build_contact_sheets(
    views: Sequence[Dict[str, object]],
    plates: Dict[str, str],
    out_dir: str,
    rows_per_sheet: int = 5,
) -> List[str]:
    """Stack pair plates into categorized exterior (including aerial) and interior contact sheets."""
    sheet_paths: List[str] = []
    sheet_groups = (
        ("exterior", ("exterior", "aerial")),
        ("interior", ("interior",)),
    )
    for cat, allowed_cats in sheet_groups:
        cat_views = [v for v in views if v.get("category") in allowed_cats and str(v["id"]) in plates]
        if not cat_views:
            continue
        for page_idx in range(0, len(cat_views), rows_per_sheet):
            chunk = cat_views[page_idx : page_idx + rows_per_sheet]
            imgs: List[Image.Image] = []
            for v in chunk:
                with Image.open(plates[str(v["id"])]) as pim:
                    imgs.append(pim.convert("RGB"))
            w = max(im.width for im in imgs)
            gap = 10
            h = sum(im.height for im in imgs) + gap * (len(imgs) + 1)
            sheet = Image.new("RGB", (w + 2 * gap, h), (14, 15, 19))
            y = gap
            for im in imgs:
                sheet.paste(im, (gap, y))
                y += im.height + gap
            s_num = page_idx // rows_per_sheet + 1
            spath = os.path.join(out_dir, f"sheet_{cat}_{s_num:02d}.jpg")
            sheet.save(spath, quality=88)
            sheet_paths.append(spath)
    return sheet_paths


def run_audit1(
    *,
    web_dir: str = DEFAULT_WEB_DIR,
    out_dir: str = AUDIT1_DIR,
    manifest_path: str = MANIFEST_PATH,
    spots_path: Optional[str] = None,
    skip_web: bool = False,
    skip_darkplaces: bool = False,
    verify_refs_only: bool = False,
    max_views: Optional[int] = None,
) -> Dict[str, object]:
    """Execute Audit 1 capture pipeline and write audit1_manifest.json."""
    selected_views = list(GW_AUDIT1_VIEWS[:max_views] if max_views else GW_AUDIT1_VIEWS)
    missing_refs, total_refs = verify_all_refs(selected_views)

    spots: List[Dict[str, object]] = []
    used_spots_path: Optional[str] = None
    candidates = [spots_path] if spots_path else list(SPOTS_CANDIDATES)
    for cand in candidates:
        if cand and os.path.isfile(cand):
            spots = load_spots(cand)
            used_spots_path = cand
            break

    resolved_views = _resolve_views_with_spots(selected_views, spots)

    webgl_res: Dict[str, object] = {"ran": False, "pass": None, "shots": {}, "spot_shots": {}}
    dp_res: Dict[str, object] = {"ran": False, "pass": None, "shots": {}}
    plates: Dict[str, str] = {}
    sheets: List[str] = []

    if not verify_refs_only:
        os.makedirs(out_dir, exist_ok=True)
        if not skip_web:
            webgl_res = capture_webgl_views(resolved_views, spots, web_dir=web_dir, out_dir=out_dir)
        if not skip_darkplaces:
            dp_res = capture_darkplaces_views(resolved_views, out_dir=out_dir)

        wg_shots: Dict[str, str] = webgl_res.get("shots", {})  # type: ignore[assignment]
        dp_shots: Dict[str, str] = dp_res.get("shots", {})  # type: ignore[assignment]
        for v in resolved_views:
            vid = str(v["id"])
            plate_path = os.path.join(out_dir, f"pair_{vid}.jpg")
            build_pair_plate(v, wg_shots.get(vid), dp_shots.get(vid), plate_path)
            plates[vid] = plate_path
        sheets = build_contact_sheets(resolved_views, plates, out_dir=out_dir)

    webgl_ok = True if (verify_refs_only or skip_web) else bool(webgl_res.get("pass"))
    dp_ok = True if (verify_refs_only or skip_darkplaces) else bool(dp_res.get("pass"))
    overall_pass = (len(missing_refs) == 0) and webgl_ok and dp_ok

    wg_shots_map: Dict[str, str] = webgl_res.get("shots", {})  # type: ignore[assignment]
    dp_shots_map: Dict[str, str] = dp_res.get("shots", {})  # type: ignore[assignment]
    pairs_for_showcase: List[Dict[str, object]] = []
    for v in resolved_views:
        vid = str(v["id"])
        ref_kind, ref_fn = v["refs"][0]  # type: ignore[index]
        ref_abs = resolve_ref_path(str(ref_kind), str(ref_fn))
        shot_abs = wg_shots_map.get(vid) or dp_shots_map.get(vid) or plates.get(vid)
        pairs_for_showcase.append(
            {
                "id": vid,
                "title": str(v["label"]),
                "spot": v.get("matched_spot") or vid,
                "spot_query": v.get("matched_spot") or "",
                "notes": (
                    f"Category={v['category']} | Ref={ref_kind}/{ref_fn}"
                    + (f" | Spot={v['matched_spot']}" if v.get("matched_spot") else "")
                ),
                "ref": ref_abs,
                "shot": shot_abs or "",
                "webgl_shot": wg_shots_map.get(vid) or "",
                "dp_shot": dp_shots_map.get(vid) or "",
                "plate": plates.get(vid) or "",
            }
        )

    manifest = {
        "audit": "audit1_capture",
        "status": "PASS" if overall_pass else "FAIL",
        "passed": overall_pass,
        "pass": overall_pass,
        "ref_inventory": REF_INVENTORY_MD,
        "ref_html_dir": REF_HTML_DIR,
        "ref_gallery_dir": REF_GALLERY_DIR,
        "spots_file": used_spots_path,
        "spots_count": len(spots),
        "views_count": len(resolved_views),
        "refs_checked": total_refs,
        "missing_refs": missing_refs,
        "webgl": {k: v for k, v in webgl_res.items() if k not in ("shots", "spot_shots")},
        "darkplaces": {k: v for k, v in dp_res.items() if k != "shots"},
        "plates": plates,
        "sheets": sheets,
        "pairs": pairs_for_showcase,
        "views": [
            {
                "id": v["id"],
                "category": v["category"],
                "label": v["label"],
                "pos_u": v["pos_u"],
                "yaw": v["yaw"],
                "pitch": v["pitch"],
                "matched_spot": v["matched_spot"],
                "refs": [resolve_ref_path(str(k), str(fn)) for k, fn in v["refs"]],  # type: ignore[index]
                "plate": plates.get(str(v["id"])),
            }
            for v in resolved_views
        ],
    }

    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    report_alias = os.path.join(os.path.dirname(manifest_path), "audit1_report.json")
    if os.path.abspath(report_alias) != os.path.abspath(manifest_path):
        with open(report_alias, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit 1: Golden West Reference vs WebGL/DarkPlaces Comparison Capture"
    )
    parser.add_argument("--web-dir", default=DEFAULT_WEB_DIR, help="Path to WebGL output dir")
    parser.add_argument("--out-dir", default=AUDIT1_DIR, help="Output directory for Audit 1 plates/sheets")
    parser.add_argument("--manifest", default=MANIFEST_PATH, help="Manifest JSON output path")
    parser.add_argument("--spots", default=None, help="Optional explicit goldenwest.spots.json path")
    parser.add_argument("--skip-web", action="store_true", help="Skip Chromium WebGL capture")
    parser.add_argument("--skip-darkplaces", action="store_true", help="Skip live DarkPlaces capture")
    parser.add_argument(
        "--verify-refs-only",
        action="store_true",
        help="Validate reference image paths and write manifest without launching browsers/DP",
    )
    parser.add_argument("--max-views", type=int, default=None, help="Limit number of views captured")
    args = parser.parse_args(argv)

    res = run_audit1(
        web_dir=args.web_dir,
        out_dir=args.out_dir,
        manifest_path=args.manifest,
        spots_path=args.spots,
        skip_web=args.skip_web,
        skip_darkplaces=args.skip_darkplaces,
        verify_refs_only=args.verify_refs_only,
        max_views=args.max_views,
    )
    print(
        f"[audit1] views={res['views_count']} refs_checked={res['refs_checked']} "
        f"missing_refs={len(res['missing_refs'])} sheets={len(res['sheets'])} pass={res['pass']}"
    )
    print(f"[audit1] manifest -> {args.manifest}")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
