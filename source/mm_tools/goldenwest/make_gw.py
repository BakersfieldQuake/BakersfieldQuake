"""make_gw.py — Master Map Orchestrator & Integrator for the 1:1 Scale (12 u/ft)
Golden West Casino & S Union Ave Quake & WebGL/WASM Map.

Assembles all 5 geometry modules strictly in deterministic order:
  1. goldenwest.gw_streets      -> build_streets(mb)
  2. goldenwest.gw_casino_ext   -> build_casino_ext(mb)
  3. goldenwest.gw_casino_int   -> build_casino_int(mb)
  4. goldenwest.gw_east_union   -> build_east_union(mb)
  5. goldenwest.gw_west_union   -> build_west_union(mb)

Adds info_player_start, distributed info_player_deathmatch spawns, arena weapons/ammo/armor
pickups, subtle shaded-corridor fill lights, calibrated sunny Bakersfield worldspawn lighting,
validates Hull-1/texture budgets via mb.validate_all(), and writes goldenwest.map +
goldenwest.spots.json (goldenwest/out/, out/maps/, and BakersfieldQuake/maps/).
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

GW_DIR = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR = os.path.dirname(GW_DIR)
MOD_DIR = os.path.dirname(os.path.dirname(MM_TOOLS_DIR))

if MM_TOOLS_DIR not in sys.path:
    sys.path.insert(0, MM_TOOLS_DIR)
if GW_DIR not in sys.path:
    sys.path.append(GW_DIR)

# Unify gw_lib and goldenwest.gw_lib so Tile/Fit/MapBuilder share a single class object
if "gw_lib" in sys.modules and "goldenwest.gw_lib" not in sys.modules:
    sys.modules["goldenwest.gw_lib"] = sys.modules["gw_lib"]
elif "goldenwest.gw_lib" in sys.modules and "gw_lib" not in sys.modules:
    sys.modules["gw_lib"] = sys.modules["goldenwest.gw_lib"]

from goldenwest import gw_lib as _gw_lib  # noqa: E402

sys.modules["gw_lib"] = _gw_lib
sys.modules["goldenwest.gw_lib"] = _gw_lib

CASINO_FLOOR_Z_FT = _gw_lib.CASINO_FLOOR_Z_FT
DEFAULT_WAD_PATH = _gw_lib.DEFAULT_WAD_PATH
DEFAULT_WAD_PATHS = _gw_lib.DEFAULT_WAD_PATHS
DELAWARE_ST_X = _gw_lib.DELAWARE_ST_X
SKY_NAME = _gw_lib.SKY_NAME
SUN_MANGLE = _gw_lib.SUN_MANGLE
TRINITY_AVE_Y = _gw_lib.TRINITY_AVE_Y
U_FT = _gw_lib.U_FT
MapBuilder = _gw_lib.MapBuilder

DEFAULT_OUT_MAP = os.path.join(GW_DIR, "out", "goldenwest.map")
LEGACY_OUT_MAP = os.path.join(MM_TOOLS_DIR, "out", "maps", "goldenwest.map")
MOD_SPOTS_PATH = os.path.join(MOD_DIR, "maps", "goldenwest.spots.json")
LEGACY_SPOTS_PATH = os.path.join(MM_TOOLS_DIR, "out", "maps", "goldenwest.spots.json")

# Arena spawns in feet: (x_ft, y_ft, z_ft, yaw_deg, label)
# Grounded cleanly on pavement (z=0 -> spawn z=2.5 ft = 30u >= 24u bbox half-height)
# or Casino floor (z=0.5 ft -> spawn z=3.0 ft = 36u), keeping wide clearance from props/walls.
DM_SPAWNS_FT: Tuple[Tuple[float, float, float, int, str], ...] = (
    (248.0, 0.0, 2.5, 180, "S Union NB opposite Casino Pylon & Rotunda"),
    (190.0, 215.0, 2.5, 290, "S Union SB north of Casino North Drive"),
    (142.0, 165.0, 2.5, 135, "Casino North Drive east of Guard Booth"),
    (148.0, -90.0, 2.5, 150, "Casino South Gate stone-pillar driveway apron"),
    (-2.0, -145.0, 2.5, 90, "Casino South Parking Lot center spine"),
    (48.0, -4.0, CASINO_FLOOR_Z_FT + 2.5, 180, "Casino NE Entrance Lobby"),
    (14.0, -24.0, CASINO_FLOOR_Z_FT + 2.5, 0, "Casino Main Poker Hall center aisle"),
    (60.0, -25.5, CASINO_FLOOR_Z_FT + 2.5, 0, "Casino Blackjack Lounge Rotunda floor"),
    (175.0, 520.0, 3.0, 315, "E Belle Terrace & S Union NW apron"),
    (345.0, 130.0, 2.5, 180, "Star-Liter Motor Motel courtyard"),
    (65.0, -310.0, 2.5, 180, "Ramos Tires & Service paved yard"),
    (135.0, -465.0, 2.5, 180, "Compas Auto Sales lot entrance"),
    (154.0, -630.0, 2.5, 180, "Super 8 front apron facing S Union"),
    (290.0, -580.0, 2.5, 315, "Playfair Market & Adams St NW corner"),
    (DELAWARE_ST_X, TRINITY_AVE_Y, 2.5, 0, "Delaware St & Trinity Ave residential junction"),
    (148.0, 862.0, 2.5, 0, "S Union Ave & E 4th St junction"),
    (344.0, 932.0, 2.5, 90, "Great Castle South Lot"),
    (363.0, 1015.0, 3.0, 115, "Great Castle Dining Hall"),
)

# Arena pickups in feet: (classname, x_ft, y_ft, z_ft, angle)
ARENA_ITEMS_FT: Tuple[Tuple[str, float, float, float, int], ...] = (
    ("item_armor2", 12.0, -5.0, CASINO_FLOOR_Z_FT + 1.0, 0),       # Red Armor: Casino main pit
    ("item_armor1", 385.0, 130.0, 1.0, 0),                         # Green Armor: Star-Liter courtyard
    ("item_armor1", 395.0, -465.0, 1.0, 0),                        # Green Armor: Country Inn courtyard
    ("weapon_rocketlauncher", 40.0, 415.0, 1.0, 270),              # 891 S Union open dirt lot
    ("weapon_rocketlauncher", 380.0, 475.0, 1.0, 180),             # SE El Don open brownfield
    ("weapon_lightning", 64.0, -18.0, CASINO_FLOOR_Z_FT + 1.0, 0), # Rotunda Lounge threshold
    ("weapon_supershotgun", 42.0, -310.0, 1.0, 0),                 # Ramos Tires yard
    ("weapon_supershotgun", 156.0, 608.0, 1.0, 180),               # Carnitas Diner front apron
    ("weapon_nailgun", DELAWARE_ST_X, -456.5, 1.0, 90),            # Delaware & Mariposa junction
    ("weapon_nailgun", 280.0, -630.0, 1.5, 0),                     # Playfair Market sidewalk
    ("weapon_grenadelauncher", 42.0, -680.0, 1.0, 90),             # Super 8 south yard
    ("item_health", 56.0, 12.0, CASINO_FLOOR_Z_FT + 1.0, 0),       # Casino vestibule courtyard
    ("item_health", 335.0, -295.0, 1.0, 0),                        # Sunland Motel courtyard
    ("item_rockets", 52.0, 415.0, 1.0, 0),
    ("item_cells", 72.0, -32.0, CASINO_FLOOR_Z_FT + 1.0, 0),
    ("item_shells", 46.0, -325.0, 1.0, 0),
    ("item_spikes", -115.0, -240.0, 1.0, 0),
    ("item_shells", 346.0, 1114.0, 1.0, 0),
    ("item_cells", 361.5, 1058.5, 1.5, 0),
    ("item_spikes", 336.0, 792.0, 1.0, 0),
)


def _import_stage_builders():
    """Import all 7 domain geometry builders lazily so package imports stay decoupled."""
    builders = []
    for mod_rel, fn_name in (
        ("gw_streets", "build_streets"),
        ("gw_casino_ext", "build_casino_ext"),
        ("gw_casino_int", "build_casino_int"),
        ("gw_gc_ext", "build_gc_ext"),
        ("gw_gc_int", "build_gc_int"),
        ("gw_east_union", "build_east_union"),
        ("gw_west_union", "build_west_union"),
    ):
        last_err: Optional[Exception] = None
        mod = None
        for mod_name in (f"goldenwest.{mod_rel}", mod_rel):
            try:
                mod = importlib.import_module(mod_name)
                break
            except ImportError as exc:
                last_err = exc
        if mod is None:
            raise ImportError(
                f"Could not import required builder module {mod_rel} ({last_err})"
            ) from last_err
        fn = getattr(mod, fn_name, None)
        if not callable(fn):
            raise AttributeError(f"Module {mod.__name__} missing callable {fn_name}(mb)")
        builders.append((mod_rel, fn))
    return builders


def place_spawns_and_pickups(mb: MapBuilder) -> None:
    """Place info_player_start, distributed DM spawns, arena pickups, and subtle alley lift."""
    # Golden West NE Courtyard primary spawn overlooking horse monument & 45-deg portico
    mb.ent_ft("info_player_start", 94.0, 26.0, 3.0, angle="215")

    for sx, sy, sz, yaw, _desc in DM_SPAWNS_FT:
        mb.ent_ft("info_player_deathmatch", sx, sy, sz, angle=str(yaw))

    for cname, ix, iy, iz, yaw in ARENA_ITEMS_FT:
        mb.ent_ft(cname, ix, iy, iz, angle=str(yaw))

    # Subtle shadow-lift lights behind Casino west service alley and south driveway apron
    # (S Union corridor and cross streets already receive fill lights from gw_streets)
    mb.street_fill_lights_ft(
        -88.0, -70.0, 80.0, z_ft=20.0, step_ft=75.0, light=185.0, color=(255, 236, 198), wait=0.55
    )


def build_world_kv(wad_path: Optional[str], mb: Optional[MapBuilder] = None) -> Dict[str, str]:
    """Return sunny Bakersfield worldspawn settings tuned for -extra4 -bounce 1 & WASM gamma 1."""
    wad_name = os.path.basename(wad_path) if wad_path else os.path.basename(DEFAULT_WAD_PATH)
    kv = mb.default_world_kv() if mb is not None else {}
    kv.update({
        "classname": "worldspawn",
        "message": "Golden West Casino & S Union Ave - Bakersfield, CA (1:1)",
        "wad": wad_name,
        "sky": SKY_NAME,
        "_sunlight": "220",
        "_sunlight_color": "255 247 226",
        "_sun_mangle": SUN_MANGLE,
        "_sunlight_mangle": SUN_MANGLE,
        "_sunlight_penumbra": "2.5",
        "_sunlight2": "150",
        "_sunlight2_color": "212 232 255",
        "_sunlight3": "70",
        "_sunlight3_color": "234 222 204",
        "_dirt": "1",
        "_dirtscale": "0.32",
        "_dirtdepth": "72",
        "_minlight": "26",
        "_bounce": "1",
        "_anglescale": "0.5",
        "fog": "0.338 0.67 0.74 0.79 1 4200 8100 504 360",
    })
    return kv


def _verify_misc_models(mb: MapBuilder) -> None:
    """Guard against misc_model entities emitted with 'model' instead of QC-required 'mdl'."""
    bad = []
    for ent in getattr(mb, "_entities", []):
        if str(ent.get("classname", "")).lower() != "misc_model":
            continue
        if not str(ent.get("mdl", "")).strip() or "model" in ent:
            bad.append(f"misc_model at {ent.get('origin', '?')}: keys={sorted(ent.keys())}")
    if bad:
        raise ValueError(
            "misc_model entities must use 'mdl' (not 'model') per misc_soc.qc & export_web_viewer.py: "
            + "; ".join(bad)
        )


def assemble_into(mb: MapBuilder) -> None:
    """Run all 5 domain builders + spawns/pickups + fill lights into an existing MapBuilder."""
    stage_builders = _import_stage_builders()
    for _mod_name, fn in stage_builders:
        fn(mb)
    place_spawns_and_pickups(mb)
    _verify_misc_models(mb)


def build_goldenwest(mb: MapBuilder) -> None:
    """Alias taking a MapBuilder instance directly (used by audit5_lighting_materials.py)."""
    assemble_into(mb)


build_all = build_goldenwest


def build_map(
    out_map: object = DEFAULT_OUT_MAP,
    check_textures: bool = True,
    fast: bool = False,
    validate: bool = True,
) -> Dict[str, object]:
    """Assemble goldenwest.map and sync goldenwest.spots.json across all standard locations."""
    if isinstance(out_map, MapBuilder):
        assemble_into(out_map)
        return dict(out_map.stats())

    out_abs = os.path.abspath(str(out_map or DEFAULT_OUT_MAP))
    existing_wads = [p for p in DEFAULT_WAD_PATHS if os.path.isfile(p)]
    if check_textures and not existing_wads:
        raise FileNotFoundError(
            "Missing gw2.wad in expected paths ("
            + ", ".join(DEFAULT_WAD_PATHS)
            + "). Run goldenwest/build_textures.py first."
        )

    mb = MapBuilder(
        wad_paths=existing_wads if existing_wads else DEFAULT_WAD_PATHS,
        u_per_ft=U_FT,
        strict_vis=not fast,
        check_textures=check_textures,
        require_gwc_prefix=check_textures,
    )

    assemble_into(mb)

    if validate:
        mb.validate_all()

    wad_used = mb.loaded_wads[0] if mb.loaded_wads else (existing_wads[0] if existing_wads else None)
    world_kv = build_world_kv(wad_used, mb=mb)

    local_spots = os.path.splitext(out_abs)[0] + ".spots.json"
    mb.write_map(out_abs, world_kv=world_kv, validate=False, spots_path=local_spots)

    written_spots: List[str] = [local_spots]
    for extra_spots in (MOD_SPOTS_PATH, LEGACY_SPOTS_PATH):
        if os.path.abspath(extra_spots) != os.path.abspath(local_spots):
            mb.write_spots(extra_spots)
            written_spots.append(os.path.abspath(extra_spots))

    stats = dict(mb.stats())
    stats["map_path"] = out_abs
    stats["spots_paths"] = written_spots
    stats["wad_used"] = wad_used
    stats["fast"] = fast
    bstats = stats.get("brushes") or {}
    print(
        f"[make_gw] wrote {out_abs}: "
        f"world={bstats.get('world', 0)} detail={bstats.get('detail', 0)} "
        f"clip={bstats.get('clip', 0)} total_brushes={stats.get('total_brushes', 0)} "
        f"entities={stats.get('entities', 0)} spots={stats.get('spots', 0)} "
        f"rooms={stats.get('rooms', 0)} doors={stats.get('doorways', 0)}"
    )
    print(f"[make_gw] spots synced -> {', '.join(written_spots)}")
    return stats


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble Golden West Casino & S Union Ave .map and .spots.json"
    )
    parser.add_argument(
        "out_map",
        nargs="?",
        default=DEFAULT_OUT_MAP,
        help=f"Output .map path (default: {DEFAULT_OUT_MAP})",
    )
    parser.add_argument("--fast", action="store_true", help="Fast assembly mode (relaxed vis strictness)")
    parser.add_argument(
        "--no-check-textures",
        action="store_true",
        help="Do not require textures/gw2.wad validation at build time",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip mb.validate_all() checks before writing .map",
    )
    args = parser.parse_args(argv)

    build_map(
        out_map=args.out_map,
        check_textures=not args.no_check_textures,
        fast=args.fast,
        validate=not args.no_validate,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
