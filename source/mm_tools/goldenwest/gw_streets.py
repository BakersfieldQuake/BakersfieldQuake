"""gw_streets.py — Sealed Skybox Shell, S Union Ave (CA-99 BUS, 3+3 Lanes),
Continuous Raised Brick Median & GIS Plantings, Cross Streets, Traffic Signals,
Utility Poles, Street Signs & Corridor Lighting for Golden West Casino & S Union Ave.

Exclusive module ownership:
  - Exports `build_streets(mb)` operating strictly within `ZONE_BOUNDS_FT["streets"]`
    plus the outer world shell (`HX0..HX1`, `HY0..HY1`, `SKY_Z_BOT..SKY_Z`).
  - Uses ONLY `gw_lib` constants/helpers and cataloged `gwc_*` / `{gwc_*` / `sky` /
    `clip` / `skip` textures (`0` legacy `bklan*`/`bk_*`/`{chain`/`sky_bk`).
  - Optimized for browser WebGL & WASM DarkPlaces (low brush/face counts, `skip`
    culling via `flush_panel_ft`, `illus` for markings/wires/foliage).
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

if __package__:
    from .gw_lib import (
        ADAMS_ST_CORRIDOR_Y,
        ADAMS_ST_ROAD_Y,
        ADAMS_ST_Y,
        AMADOR_AVE_CORRIDOR_Y,
        AMADOR_AVE_ROAD_Y,
        AMADOR_AVE_Y,
        BELLE_TERRACE_CORRIDOR_Y,
        BELLE_TERRACE_ROAD_Y,
        BELLE_TERRACE_Y,
        DELAWARE_ST_CORRIDOR_X,
        DELAWARE_ST_ROAD_X,
        DELAWARE_ST_X,
        E_4TH_ST_CORRIDOR_Y,
        E_4TH_ST_ROAD_Y,
        E_4TH_ST_Y,
        E_5TH_ST_CORRIDOR_Y,
        E_5TH_ST_ROAD_Y,
        E_5TH_ST_Y,
        GC_ALLEY_X,
        HX0,
        HX1,
        HY0,
        HY1,
        MARIPOSA_AVE_CORRIDOR_Y,
        MARIPOSA_AVE_ROAD_Y,
        MARIPOSA_AVE_Y,
        MEDIAN_PALMS_NORTH_LOT_FT,
        MEDIAN_SHRUBS_CASINO_FRONT_FT,
        MEDIAN_TREES_SOUTH_FT,
        SKY_Z,
        SKY_Z_BOT,
        TRINITY_AVE_CORRIDOR_Y,
        TRINITY_AVE_ROAD_Y,
        TRINITY_AVE_Y,
        UNION_E_SIDEWALK_X,
        UNION_MEDIAN_X,
        UNION_NB_CARRIAGE_X,
        UNION_POLE_X,
        UNION_SB_CARRIAGE_X,
        UNION_W_SIDEWALK_X,
        Fit,
        MapBuilder,
        Tile,
    )
else:
    GW_DIR = os.path.dirname(os.path.abspath(__file__))
    if GW_DIR not in sys.path:
        sys.path.insert(0, GW_DIR)
    from gw_lib import (  # noqa: E402
        ADAMS_ST_CORRIDOR_Y,
        ADAMS_ST_ROAD_Y,
        ADAMS_ST_Y,
        AMADOR_AVE_CORRIDOR_Y,
        AMADOR_AVE_ROAD_Y,
        AMADOR_AVE_Y,
        BELLE_TERRACE_CORRIDOR_Y,
        BELLE_TERRACE_ROAD_Y,
        BELLE_TERRACE_Y,
        DELAWARE_ST_CORRIDOR_X,
        DELAWARE_ST_ROAD_X,
        DELAWARE_ST_X,
        E_4TH_ST_CORRIDOR_Y,
        E_4TH_ST_ROAD_Y,
        E_4TH_ST_Y,
        E_5TH_ST_CORRIDOR_Y,
        E_5TH_ST_ROAD_Y,
        E_5TH_ST_Y,
        GC_ALLEY_X,
        HX0,
        HX1,
        HY0,
        HY1,
        MARIPOSA_AVE_CORRIDOR_Y,
        MARIPOSA_AVE_ROAD_Y,
        MARIPOSA_AVE_Y,
        MEDIAN_PALMS_NORTH_LOT_FT,
        MEDIAN_SHRUBS_CASINO_FRONT_FT,
        MEDIAN_TREES_SOUTH_FT,
        SKY_Z,
        SKY_Z_BOT,
        TRINITY_AVE_CORRIDOR_Y,
        TRINITY_AVE_ROAD_Y,
        TRINITY_AVE_Y,
        UNION_E_SIDEWALK_X,
        UNION_MEDIAN_X,
        UNION_NB_CARRIAGE_X,
        UNION_POLE_X,
        UNION_SB_CARRIAGE_X,
        UNION_W_SIDEWALK_X,
        Fit,
        MapBuilder,
        Tile,
    )

# Exact snapped Z elevations (12 u/ft)
Z_GROUND_FT: float = 0.0                # 0.0 u: continuous valley earth bed top
Z_ROAD_FT: float = 2.0 / 12.0           # 2.0 u: asphalt & concrete roadway top
Z_MARK_FT: float = 2.5 / 12.0           # 2.5 u: flush thermoplastic markings
Z_MEDIAN_FT: float = 0.45               # 5.4 u -> 5.5 u: raised herringbone brick median
Z_WALK_FT: float = 0.50                 # 6.0 u: concrete sidewalk top (<= 18u Hull-1)
Z_SHOULDER_FT: float = 1.0 / 12.0       # 1.0 u: uncurbed Adams St dusty shoulder strip

# E Belle Terrace widened roadway inside BELLE_TERRACE_CORRIDOR_Y (532..582): 46.0 ft OSM width (44-48 ft spec)
BT_ROAD_Y: Tuple[float, float] = (534.5, 580.5)

# Shared tile specs (refreshed per MapBuilder module so package & direct imports both work)
def _refresh_shared_tiles() -> None:
    global TEX_DIRT, TEX_DRYGRS, TEX_ASPH, TEX_CONC, TEX_CURB
    global TEX_BRICK, TEX_HEDGE, TEX_MULCH, TEX_BARK, TEX_PALMHAT
    TEX_DIRT = Tile("gwc_dirt", 24.0, 24.0)
    TEX_DRYGRS = Tile("gwc_drygrs", 18.0, 18.0)
    TEX_ASPH = Tile("gwc_asph", 14.0, 14.0)
    TEX_CONC = Tile("gwc_conc", 8.0, 8.0)
    TEX_CURB = Tile("gwc_curb", 6.0, 1.0)
    TEX_BRICK = Tile("gwc_brick", 5.0, 5.0)
    TEX_HEDGE = Tile("gwc_hedge", 5.0, 5.0)
    TEX_MULCH = Tile("gwc_mulch", 4.0, 4.0)
    TEX_BARK = Tile("gwc_bark", 2.5, 4.0)
    TEX_PALMHAT = Tile("gwc_palmhat", 3.0, 3.0)


_refresh_shared_tiles()


def _road_slab(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    tex=TEX_ASPH,
    skip_faces: Tuple[str, ...] = ("b",),
) -> None:
    """Emit a roadway slab with buried underside (and optional flush perimeter edges) culled to skip."""
    faces = {f: "skip" for f in skip_faces}
    faces.setdefault("b", "skip")
    mb.detail_box_ft(x0, y0, Z_GROUND_FT, x1, y1, Z_ROAD_FT, tex, faces=faces)


def _curb_slab(
    mb: MapBuilder,
    x0: float,
    y0: float,
    z0: float,
    x1: float,
    y1: float,
    z1: float,
    tex=TEX_CONC,
    skip_faces: Tuple[str, ...] = (),
) -> None:
    """Emit a Hull-1-validated curb/sidewalk slab with buried bottom & world-edge/flush seam skip culling."""
    rise_u = abs(z1 - z0) * mb.u_per_ft
    if rise_u > 18.0 + 1e-4:
        raise ValueError(f"Curb height {rise_u:.1f}u exceeds Hull-1 step limit (18u)")
    if hasattr(mb, "_curbs"):
        mb._curbs.append({"rise_u": rise_u})
    faces: Dict[str, object] = {"b": "skip"}
    if abs(x0 - HX0) < 1e-4:
        faces["w"] = "skip"
    if abs(x1 - HX1) < 1e-4:
        faces["e"] = "skip"
    if abs(y0 - HY0) < 1e-4:
        faces["s"] = "skip"
    if abs(y1 - HY1) < 1e-4:
        faces["n"] = "skip"
    for f in skip_faces:
        faces[f] = "skip"
    mb.detail_box_ft(x0, y0, z0, x1, y1, z1, tex, faces=faces)


def _mark_top(mb: MapBuilder, x0: float, y0: float, x1: float, y1: float, tex) -> None:
    """Emit a flush non-solid top-only road marking decal (5 faces culled to skip)."""
    mb.flush_panel_ft(x0, y0, Z_ROAD_FT, x1, y1, Z_MARK_FT, {"t": tex}, group="illus")


def _walk_mark_top(mb: MapBuilder, x0: float, y0: float, x1: float, y1: float, tex) -> None:
    """Emit a flush non-solid top-only panel on raised sidewalks (e.g. ADA tactile pad)."""
    mb.flush_panel_ft(x0, y0, Z_WALK_FT, x1, y1, Z_WALK_FT + (Z_MARK_FT - Z_ROAD_FT), {"t": tex}, group="illus")


def _dash_y(
    mb: MapBuilder,
    xc: float,
    y0: float,
    y1: float,
    width_ft: float = 0.90,
    on_ft: float = 10.0,
    gap_ft: float = 30.0,
    tex: str = "gwc_wline",
) -> None:
    """Emit dashed North-South lane markings using top-only flush panels."""
    hw = 0.5 * width_ft
    y = y0
    while y + on_ft <= y1 + 1e-3:
        mb.flush_panel_ft(
            xc - hw, y, Z_ROAD_FT,
            xc + hw, min(y1, y + on_ft), Z_MARK_FT,
            {"t": Fit(tex)},
            group="illus",
        )
        y += on_ft + gap_ft


def _dash_x(
    mb: MapBuilder,
    yc: float,
    x0: float,
    x1: float,
    width_ft: float = 0.35,
    on_ft: float = 10.0,
    gap_ft: float = 30.0,
    tex: str = "gwc_white",
) -> None:
    """Emit dashed East-West lane markings using top-only flush panels."""
    hw = 0.5 * width_ft
    x = x0
    while x + on_ft <= x1 + 1e-3:
        mb.flush_panel_ft(
            x, yc - hw, Z_ROAD_FT,
            min(x1, x + on_ft), yc + hw, Z_MARK_FT,
            {"t": Tile(tex, 4.0, 4.0)},
            group="illus",
        )
        x += on_ft + gap_ft


def _build_world_shell_and_bed(mb: MapBuilder) -> None:
    """Seal the outer world bounds cleanly against leaks and confine players with clip."""
    shell_t = 8.0
    # 6 structural sky enclosure brushes
    mb.structural_box_ft(HX0 - shell_t, HY0 - shell_t, SKY_Z, HX1 + shell_t, HY1 + shell_t, SKY_Z + shell_t, "sky")
    mb.structural_box_ft(HX0 - shell_t, HY0 - shell_t, SKY_Z_BOT - shell_t, HX1 + shell_t, HY1 + shell_t, SKY_Z_BOT, "sky")
    mb.structural_box_ft(HX0 - shell_t, HY0 - shell_t, SKY_Z_BOT, HX0, HY1 + shell_t, SKY_Z, "sky")
    mb.structural_box_ft(HX1, HY0 - shell_t, SKY_Z_BOT, HX1 + shell_t, HY1 + shell_t, SKY_Z, "sky")
    mb.structural_box_ft(HX0, HY0 - shell_t, SKY_Z_BOT, HX1, HY0, SKY_Z, "sky")
    mb.structural_box_ft(HX0, HY1, SKY_Z_BOT, HX1, HY1 + shell_t, SKY_Z, "sky")

    # Continuous solid valley earth bed across the entire envelope (z = SKY_Z_BOT .. 0)
    # 5 outer faces sit flush behind the 6 structural sky perimeter brushes -> skip-cull to save lightmap pixels
    mb.structural_box_ft(
        HX0, HY0, SKY_Z_BOT, HX1, HY1, Z_GROUND_FT,
        TEX_DIRT,
        faces={"t": TEX_DIRT, "b": "skip", "n": "skip", "s": "skip", "e": "skip", "w": "skip"},
    )

    # Perimeter player clip walls (1.0 ft inside playable bounds) + high sky ceiling clip
    cw = 1.0
    mb.clip_box_ft(HX0, HY0, Z_GROUND_FT, HX0 + cw, HY1, SKY_Z)
    mb.clip_box_ft(HX1 - cw, HY0, Z_GROUND_FT, HX1, HY1, SKY_Z)
    mb.clip_box_ft(HX0 + cw, HY0, Z_GROUND_FT, HX1 - cw, HY0 + cw, SKY_Z)
    mb.clip_box_ft(HX0 + cw, HY1 - cw, Z_GROUND_FT, HX1 - cw, HY1, SKY_Z)
    mb.clip_box_ft(HX0 + cw, HY0 + cw, SKY_Z - 1.5, HX1 - cw, HY1 - cw, SKY_Z)


def _sidewalk_with_aprons(
    mb: MapBuilder,
    x0: float,
    x1: float,
    road_breaks: Sequence[Tuple[float, float]],
    aprons: Sequence[Tuple[float, float]],
    side_label: str,
) -> None:
    """Tile a N-S sidewalk along [HY0, HY1] leaving cross-street breaks open and emitting depressed aprons."""
    events: List[Tuple[float, float, str]] = []
    for r0, r1 in road_breaks:
        events.append((r0, r1, "road"))
    for a0, a1 in aprons:
        events.append((a0, a1, "apron"))
    events.sort(key=lambda e: e[0])

    # Inner street-facing edge of driveway apron touches Union asphalt at Z_ROAD_FT; N/S edges touch concrete ramps
    apron_skip = ("n", "s", "e", "b") if side_label == "union_w" else ("n", "s", "w", "b")

    cur = HY0
    prev_kind: Optional[str] = None
    for e0, e1, kind in events:
        if e0 > cur + 0.1:
            curb_skip = []
            if prev_kind == "apron":
                curb_skip.append("s")
            if kind == "apron":
                curb_skip.append("n")
            _curb_slab(mb, x0, cur, Z_GROUND_FT, x1, e0, Z_WALK_FT, TEX_CONC, skip_faces=tuple(curb_skip))
        if kind == "apron":
            # Flush depressed driveway apron + 2 ft flared concrete transition wings
            flare = min(2.0, max(0.5, 0.12 * (e1 - e0)))
            mb.slab_ramp_yft(x0, x1, e0, e0 + flare, Z_WALK_FT, Z_ROAD_FT, TEX_CONC, thick_ft=0.5, group="detail")
            _road_slab(mb, x0, e0 + flare, x1, e1 - flare, TEX_CONC, skip_faces=apron_skip)
            mb.slab_ramp_yft(x0, x1, e1 - flare, e1, Z_ROAD_FT, Z_WALK_FT, TEX_CONC, thick_ft=0.5, group="detail")
        cur = max(cur, e1)
        prev_kind = kind
    if cur < HY1 - 0.1:
        end_skip = ("s",) if prev_kind == "apron" else ()
        _curb_slab(mb, x0, cur, Z_GROUND_FT, x1, HY1, Z_WALK_FT, TEX_CONC, skip_faces=end_skip)


def _build_s_union_ave(mb: MapBuilder) -> None:
    """Build S Union Ave (CA-99 BUS) 3+3 divided boulevard, concrete middle lanes,
    turn pockets at E Belle Terrace, lane markings, sidewalks, and driveway aprons.
    """
    wx0, wx1 = UNION_W_SIDEWALK_X      # (172.0, 178.0)
    sb0, sb1 = UNION_SB_CARRIAGE_X     # (178.0, 219.0)
    m0, m1 = UNION_MEDIAN_X            # (219.0, 238.0)
    nb0, nb1 = UNION_NB_CARRIAGE_X     # (238.0, 277.0)
    ex0, ex1 = UNION_E_SIDEWALK_X      # (277.0, 283.0)

    bt_r0, bt_r1 = BT_ROAD_Y             # (534.5, 580.5) -> 46.0 ft widened road
    e4_r0, e4_r1 = E_4TH_ST_ROAD_Y       # (847.0, 877.0) -> 30.0 ft road
    e5_r0, e5_r1 = E_5TH_ST_ROAD_Y       # (1173.0, 1203.0) -> East T-junction ONLY
    ad_r0, ad_r1 = ADAMS_ST_ROAD_Y       # (-590.0, -560.0)
    am_r0, am_r1 = AMADOR_AVE_ROAD_Y     # (-781.0, -751.0)

    # 3 SB lanes: outer 15 ft (incl 3 ft shoulder) asphalt, middle 13 ft concrete, inner 13 ft asphalt
    sb_l1 = sb0 + 15.0  # 193.0
    sb_l2 = sb_l1 + 13.0  # 206.0
    # 3 NB lanes: inner 13 ft asphalt, middle 13 ft concrete, outer 13 ft asphalt
    nb_l1 = nb0 + 13.0  # 251.0
    nb_l2 = nb_l1 + 13.0  # 264.0

    tex_sb_conc = Tile("gwc_concslab", 13.0, 24.0, u_ofs=-sb_l1 / 13.0)
    tex_nb_conc = Tile("gwc_concslab", 13.0, 24.0, u_ofs=-nb_l1 / 13.0)

    all_sides_b = ("n", "s", "e", "w", "b")
    for seg_y0, seg_y1 in ((HY0, bt_r0), (bt_r1, e4_r0), (e4_r1, HY1)):
        # Southbound 3 lanes
        _road_slab(mb, sb0, seg_y0, sb_l1, seg_y1, TEX_ASPH, skip_faces=all_sides_b)
        _road_slab(mb, sb_l1, seg_y0, sb_l2, seg_y1, tex_sb_conc, skip_faces=all_sides_b)
        _road_slab(mb, sb_l2, seg_y0, sb1, seg_y1, TEX_ASPH, skip_faces=all_sides_b)
        # Northbound 3 lanes
        _road_slab(mb, nb0, seg_y0, nb_l1, seg_y1, TEX_ASPH, skip_faces=all_sides_b)
        _road_slab(mb, nb_l1, seg_y0, nb_l2, seg_y1, tex_nb_conc, skip_faces=all_sides_b)
        _road_slab(mb, nb_l2, seg_y0, nb1, seg_y1, TEX_ASPH, skip_faces=all_sides_b)

        # Two crisp dashed white lane dividers per carriageway (stop cleanly behind Belle Terrace & E 4th stop bars)
        d0 = (seg_y0 + 6.5) if seg_y0 == bt_r1 else ((seg_y0 + 13.5) if seg_y0 == e4_r1 else seg_y0 + 4.0)
        d1 = (seg_y1 - 6.5) if seg_y1 == bt_r0 else ((seg_y1 - 13.5) if seg_y1 == e4_r0 else seg_y1 - 4.0)
        _dash_y(mb, sb_l1, d0, d1)
        _dash_y(mb, sb_l2, d0, d1)
        _dash_y(mb, nb_l1, d0, d1)
        _dash_y(mb, nb_l2, d0, d1)

    # Solid outer white edge stripes (broken cleanly around Belle Terrace, E 4th, E 5th, & green bike boxes)
    for ey0, ey1 in ((HY0, bt_r0 - 6.0), (bt_r1 + 6.0, e4_r0 - 33.0), (e4_r1 + 33.5, HY1)):
        _mark_top(mb, sb0 + 2.5, ey0, sb0 + 3.5, ey1, Fit("gwc_wline", repeat=(1.0, max(1.0, (ey1 - ey0) / 12.0))))
    for ey0, ey1 in (
        (HY0, bt_r0 - 6.0),
        (bt_r1 + 6.0, e4_r0 - 33.0),
        (e4_r1 + 33.5, e5_r0 - 29.0),
        (e5_r1 + 1.0, HY1),
    ):
        _mark_top(mb, nb1 - 3.5, ey0, nb1 - 2.5, ey1, Fit("gwc_wline", repeat=(1.0, max(1.0, (ey1 - ey0) / 12.0))))

    # Solid double-yellow median curb edge lines (broken at Belle Terrace, E 4th, Adams, Amador, & turn pockets)
    for y0, y1 in ((HY0, am_r0), (am_r1, ad_r0), (ad_r1, bt_r0 - 6.0), (bt_r1 + 6.0, e4_r0 - 13.0), (e4_r1 + 13.0, HY1)):
        _mark_top(mb, sb1 - 1.3, y0, sb1 - 0.1, y1, Fit("gwc_yline", repeat=(1.0, max(1.0, (y1 - y0) / 10.0))))
    # NB median edge yellow line stops at y=448 where NB left-turn pocket opens
    for y0, y1 in ((HY0, am_r0), (am_r1, ad_r0), (ad_r1, 448.0), (700.0, e4_r0 - 13.0), (e4_r1 + 13.0, HY1)):
        _mark_top(mb, nb0 + 0.1, y0, nb0 + 1.3, y1, Fit("gwc_yline", repeat=(1.0, max(1.0, (y1 - y0) / 10.0))))

    # Full E Belle Terrace & E 4th St intersection asphalt boxes across S Union (x=178..277)
    _road_slab(mb, sb0, bt_r0, nb1, bt_r1, TEX_ASPH, skip_faces=all_sides_b)
    _road_slab(mb, sb0, e4_r0, nb1, e4_r1, TEX_ASPH, skip_faces=all_sides_b)

    # E 4th St & E 5th St Union crosswalks, stop bars & green bike conflict/approach lanes (zero Z-fighting)
    for cw_y0, cw_y1 in ((840.5, 846.8), (877.2, 883.5)):
        _mark_top(mb, sb0 + 0.5, cw_y0, sb1 - 0.5, cw_y1, Fit("gwc_xwalk", repeat=(4.0, 1.0)))
        _mark_top(mb, nb0 + 0.5, cw_y0, nb1 - 0.5, cw_y1, Fit("gwc_xwalk", repeat=(4.0, 1.0)))
    _mark_top(mb, nb0 + 0.5, 835.0, nb1 - 6.0, 836.5, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, sb0 + 6.0, 887.5, sb1 - 0.5, 889.0, Tile("gwc_white", 4.0, 4.0))
    for by0, by1 in ((815.0, 839.5), (e4_r0 + 0.2, e4_r1 - 0.2), (884.5, 909.5)):
        _mark_top(mb, sb0 + 0.2, by0, sb0 + 5.5, by1, Fit("gwc_bikelane", repeat=(1.0, 3.0), flip_v=True))
        _mark_top(mb, nb1 - 5.5, by0, nb1 - 0.2, by1, Fit("gwc_bikelane", repeat=(1.0, 3.0)))
    for by0, by1 in ((1145.0, 1172.0), (e5_r0 + 0.2, e5_r1 - 0.2)):
        _mark_top(mb, nb1 - 5.5, by0, nb1 - 0.2, by1, Fit("gwc_bikelane", repeat=(1.0, 3.0)))

    # Full median break asphalt paving at Adams St (-590..-560) and Amador Ave (-781..-751)
    _road_slab(mb, m0, ad_r0, m1, ad_r1, TEX_ASPH, skip_faces=all_sides_b)
    _road_slab(mb, m0, am_r0, m1, am_r1, TEX_ASPH, skip_faces=all_sides_b)

    # Dedicated SB & NB Left-Turn Pockets at E Belle Terrace
    # 1) NB Left-Turn Pocket (South of Belle Terrace: y = 448..534.5, x = 227.5..238)
    _road_slab(mb, 227.5, 476.0, m1, bt_r0, TEX_ASPH, skip_faces=all_sides_b)
    mb.prism_ft([(227.5, 476.0), (m1, 448.0), (m1, 476.0)], Z_GROUND_FT, Z_ROAD_FT, TEX_ASPH, tex_top=TEX_ASPH, group="detail")
    _mark_top(mb, 237.6, 476.0, 238.1, bt_r0 - 6.0, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, 227.9, 476.0, 228.9, bt_r0 - 6.0, Fit("gwc_yline", repeat=(1.0, 6.0)))
    _mark_top(mb, 230.4, 498.0, 235.0, 508.0, Fit("gwc_turnarr"))   # Points North (+Y)
    # NB stop bar across NB lanes + pocket south of Belle Terrace crosswalk
    _mark_top(mb, 228.5, bt_r0 - 5.5, nb1 - 2.0, bt_r0 - 4.0, Tile("gwc_white", 4.0, 4.0))

    # 2) SB Left-Turn Pocket (North of Belle Terrace: y = 580.5..700, x = 219..230)
    _road_slab(mb, m0, bt_r1, 230.0, 670.0, TEX_ASPH, skip_faces=all_sides_b)
    mb.prism_ft([(m0, 670.0), (m0, 700.0), (230.0, 670.0)], Z_GROUND_FT, Z_ROAD_FT, TEX_ASPH, tex_top=TEX_ASPH, group="detail")
    _mark_top(mb, 218.9, bt_r1 + 6.0, 219.4, 670.0, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, 228.5, bt_r1 + 6.0, 229.6, 670.0, Fit("gwc_yline", repeat=(1.0, 8.0)))
    _mark_top(mb, 222.2, 608.0, 226.8, 618.0, Fit("gwc_turnarr", flip_v=True))  # Points South (-Y)
    # SB stop bar across SB lanes + pocket north of Belle Terrace crosswalk
    _mark_top(mb, sb0 + 2.0, bt_r1 + 4.0, 229.0, bt_r1 + 5.5, Tile("gwc_white", 4.0, 4.0))

    # West & East Sidewalks with clean driveway curb aprons (E 5th is East-only T-junction)
    _sidewalk_with_aprons(
        mb, wx0, wx1,
        road_breaks=[(am_r0, am_r1), (bt_r0, bt_r1), (e4_r0, e4_r1)],
        aprons=[
            (-640.0, -604.0),   # Super 8 Motel
            (-486.0, -456.0),   # Compas Auto Sales
            (-326.0, -292.0),   # Ramos Tires & Service
            (-100.0, -74.0),    # Golden West Casino South Drive
            (152.0, 178.0),     # Golden West Casino North Drive
            (588.0, 612.0),     # Carnitas Birria Menudo
            (786.0, 818.0),     # One Stop Market
            (932.0, 956.0),     # Manila Inn
            (1105.0, 1132.0),   # DG Market South Drive
            (1240.0, 1266.0),   # DG Market North Drive
        ],
        side_label="union_w",
    )
    _sidewalk_with_aprons(
        mb, ex0, ex1,
        road_breaks=[(ad_r0, ad_r1), (bt_r0, bt_r1), (e4_r0, e4_r1), (e5_r0, e5_r1)],
        aprons=[
            (-630.0, -590.0),   # Playfair Market corner apron
            (-474.0, -446.0),   # Country Inn Motel
            (-336.0, -312.0),   # Sunland Motel
            (-34.0, -14.0),     # 922 S Union RV Park
            (98.0, 177.0),      # Star-Liter Motor Motel broad apron
            (360.0, 384.0),     # Redwood Senior Living
            (782.0, 810.0),     # Deal Time Auto
            (954.0, 984.0),     # Great Castle South Drive
            (1096.0, 1126.0),   # Great Castle North Drive
            (1242.0, 1272.0),   # Reyes Tires & Auto
        ],
        side_label="union_e",
    )

    # S Union Ave daylight fill lights (spaced evenly to supplement solar bounce)
    mb.street_fill_lights_ft(228.0, HY0 + 50.0, HY1 - 50.0, z_ft=28.0, step_ft=190.0, light=165.0, color=(255, 238, 206), wait=0.55)


def _fan_palm(mb: MapBuilder, x_ft: float, y_ft: float, h_ft: float = 31.0, z_base_ft: float = Z_MEDIAN_FT) -> None:
    """Low-poly Washingtonia Mexican Fan Palm (bark trunk + dry skirt + alpha frond planes)."""
    z_mid = z_base_ft + h_ft * 0.52
    z_top = z_base_ft + h_ft * 0.90
    mb.cyl_ft(x_ft, y_ft, 0.55, z_base_ft - 0.1, z_mid, sides=6, tex_side=TEX_BARK, tex_top="skip", group="detail")
    mb.cyl_ft(x_ft, y_ft, 0.42, z_mid - 0.1, z_top, sides=6, tex_side=TEX_BARK, tex_top="skip", group="illus")
    # Shaggy dry palm petticoat skirt
    mb.cyl_ft(x_ft, y_ft, 0.95, z_top - 4.8, z_top - 0.5, sides=6, tex_side=TEX_PALMHAT, tex_top=TEX_PALMHAT, group="illus")
    # Crossed alpha-cutout palm frond fans + angled crown cap (non-solid illus)
    span = 6.8
    fz0, fz1 = z_top - 2.4, z_top + 5.2
    mb.flush_panel_ft(
        x_ft - span, y_ft - 0.08, fz0, x_ft + span, y_ft + 0.08, fz1,
        {"n": Fit("{gwc_palmfr"), "s": Fit("{gwc_palmfr")}, group="illus",
    )
    mb.flush_panel_ft(
        x_ft - 0.08, y_ft - span, fz0, x_ft + 0.08, y_ft + span, fz1,
        {"e": Fit("{gwc_palmfr"), "w": Fit("{gwc_palmfr")}, group="illus",
    )
    # Angled broad crown top so aerial view shows full palm rosette
    mb.slab_ramp_xft(x_ft - 5.2, x_ft, y_ft - 3.6, y_ft + 3.6, z_top + 1.0, z_top + 2.8, Fit("{gwc_palmfr"), thick_ft=0.12, group="illus")
    mb.slab_ramp_xft(x_ft, x_ft + 5.2, y_ft - 3.6, y_ft + 3.6, z_top + 2.8, z_top + 1.0, Fit("{gwc_palmfr"), thick_ft=0.12, group="illus")


def _deciduous_tree(mb: MapBuilder, x_ft: float, y_ft: float, h_ft: float = 15.5, z_base_ft: float = Z_MEDIAN_FT) -> None:
    """Medium deciduous median shade tree (bark trunk + crossed {gwc_tree2 alpha silhouette)."""
    w_ft = h_ft * 0.72
    hw = 0.5 * w_ft
    mb.cyl_ft(x_ft, y_ft, 0.40, z_base_ft - 0.1, z_base_ft + h_ft * 0.42, sides=6, tex_side=TEX_BARK, tex_top="skip", group="detail")
    mb.flush_panel_ft(
        x_ft - hw, y_ft - 0.08, z_base_ft + 0.2, x_ft + hw, y_ft + 0.08, z_base_ft + h_ft,
        {"n": Fit("{gwc_tree2"), "s": Fit("{gwc_tree2")}, group="illus",
    )
    mb.flush_panel_ft(
        x_ft - 0.08, y_ft - hw, z_base_ft + 0.2, x_ft + 0.08, y_ft + hw, z_base_ft + h_ft,
        {"e": Fit("{gwc_tree2"), "w": Fit("{gwc_tree2")}, group="illus",
    )


def _median_curb_island(
    mb: MapBuilder,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    top_tex=TEX_BRICK,
    skip_faces: Tuple[str, ...] = (),
) -> None:
    """Emit a raised curbed median island segment (brick or dirt top + concrete curb edges)."""
    faces: Dict[str, object] = {"t": top_tex, "b": "skip"}
    for f in skip_faces:
        faces[f] = "skip"
    mb.detail_box_ft(
        x0, y0, Z_GROUND_FT, x1, y1, Z_MEDIAN_FT,
        TEX_CURB,
        faces=faces,
    )


def _build_median_and_plantings(mb: MapBuilder) -> None:
    """Build the continuous raised red herringbone brick median from Adams St (-576)
    to E Belle Terrace (+557.7), south extensions, dirt island patch at 891/Star-Liter,
    and location-accurate Bakersfield GIS median plantings.
    """
    m0, m1 = UNION_MEDIAN_X  # (219.0, 238.0)
    bt_r0, bt_r1 = BT_ROAD_Y
    ad_r0, ad_r1 = ADAMS_ST_ROAD_Y
    am_r0, am_r1 = AMADOR_AVE_ROAD_Y

    # 1. South of Amador Ave (-820 .. -781)
    _median_curb_island(mb, m0, HY0, m1, am_r0, skip_faces=("s",))
    # 2. Amador Ave to Adams St (-751 .. -590)
    _median_curb_island(mb, m0, am_r1, m1, ad_r0)
    # 3. Continuous Adams St to dirt patch (-560 .. 295)
    _median_curb_island(mb, m0, ad_r1, m1, 295.0, skip_faces=("n",))
    # 4. Unpaved dirt/weathered island patch opposite 891 S Union / Star-Liter North (295 .. 325)
    _median_curb_island(mb, m0, 295.0, m1, 325.0, top_tex=TEX_DIRT, skip_faces=("n", "s"))
    # 5. Brick median from 325 up to NB left-turn pocket taper (325 .. 448)
    _median_curb_island(mb, m0, 325.0, m1, 448.0, skip_faces=("n", "s"))
    # 6. Tapered & narrow nose sheltering NB left-turn pocket (448 .. bt_r0)
    mb.prism_ft(
        [(m0, 448.0), (m1, 448.0), (227.5, 476.0), (m0, 476.0)],
        Z_GROUND_FT, Z_MEDIAN_FT, TEX_CURB, tex_top=TEX_BRICK, group="detail",
    )
    _median_curb_island(mb, m0, 476.0, 227.5, bt_r0, skip_faces=("s",))
    # 7. Narrow nose & taper north of E Belle Terrace sheltering SB left-turn pocket (bt_r1 .. 700)
    _median_curb_island(mb, 230.0, bt_r1, m1, 670.0, skip_faces=("n",))
    mb.prism_ft(
        [(230.0, 670.0), (m1, 670.0), (m1, 700.0), (m0, 700.0)],
        Z_GROUND_FT, Z_MEDIAN_FT, TEX_CURB, tex_top=TEX_BRICK, group="detail",
    )
    # 8. North median segments broken cleanly at E 4th St (847..877); E 5th St does NOT cut median
    e4_r0, e4_r1 = E_4TH_ST_ROAD_Y
    _median_curb_island(mb, m0, 700.0, m1, e4_r0, skip_faces=("s",))
    _median_curb_island(mb, m0, e4_r1, m1, HY1, skip_faces=("n",))

    # --- Location-Accurate Plantings (NO uniform 38-ft palms!) ---
    # A. 5 tall Washingtonia fan palms opposite North Casino lot / Star-Liter (y = +181..+269, 33.5..37.5 ft per 013.jpg)
    mb.detail_box_ft(222.0, 178.0, Z_MEDIAN_FT, 236.2, 272.0, Z_MEDIAN_FT + 0.35, TEX_MULCH, faces={"b": "skip"})
    mb.detail_box_ft(223.0, 179.0, Z_MEDIAN_FT + 0.35, 235.2, 270.0, Z_MEDIAN_FT + 2.3, TEX_HEDGE, faces={"b": "skip"})
    north_palm_heights = (34.5, 37.5, 36.0, 33.5, 35.5)
    for idx, (px, py) in enumerate(MEDIAN_PALMS_NORTH_LOT_FT):
        safe_x = min(max(px, 223.5), 233.8)
        _fan_palm(mb, safe_x, py, h_ft=north_palm_heights[idx % len(north_palm_heights)])

    # B. Low clipped shrubs opposite Casino NE courtyard & stone wing (y = +63..+121 and -5..+43)
    for y_lo, y_hi in ((60.0, 124.0), (-7.0, 46.0)):
        mb.detail_box_ft(223.5, y_lo, Z_MEDIAN_FT, 234.5, y_hi, Z_MEDIAN_FT + 0.35, TEX_MULCH, faces={"b": "skip"})
        mb.detail_box_ft(224.5, y_lo + 2.0, Z_MEDIAN_FT + 0.35, 233.5, y_hi - 2.0, Z_MEDIAN_FT + 2.6, TEX_HEDGE, faces={"b": "skip"})
    # Compact ornamentals (kept <= 7.5 ft so they never block Casino pylon/rotunda!)
    for sx, sy in (MEDIAN_SHRUBS_CASINO_FRONT_FT[1], MEDIAN_SHRUBS_CASINO_FRONT_FT[4], MEDIAN_SHRUBS_CASINO_FRONT_FT[7]):
        _deciduous_tree(mb, min(max(sx, 224.0), 233.5), sy, h_ft=6.8)

    # C. Medium deciduous shade trees & shrubs opposite South Casino lot / Ramos Tires (y = -336..-180 & -107..-73)
    for y_lo, y_hi in ((-110.0, -70.0), (-264.0, -234.0), (-339.0, -308.0)):
        mb.detail_box_ft(224.0, y_lo, Z_MEDIAN_FT, 234.5, y_hi, Z_MEDIAN_FT + 0.35, TEX_MULCH, faces={"b": "skip"})
        mb.detail_box_ft(225.0, y_lo + 1.5, Z_MEDIAN_FT + 0.35, 233.5, y_hi - 1.5, Z_MEDIAN_FT + 2.4, TEX_HEDGE, faces={"b": "skip"})
    for idx, (tx, ty) in enumerate((MEDIAN_TREES_SOUTH_FT[2], MEDIAN_TREES_SOUTH_FT[4], MEDIAN_TREES_SOUTH_FT[7])):
        _deciduous_tree(mb, min(max(tx, 224.5), 232.5), ty, h_ft=14.5 + (idx % 2) * 2.5)

    # D. Bare herringbone brick from y = -556..-340 (intentionally ZERO shrubs/trees per #021/#045/#063/#064)

    # E. South palm cluster near y = -820..-770 (south of Amador Ave break)
    mb.detail_box_ft(224.0, -816.0, Z_MEDIAN_FT, 235.0, -783.0, Z_MEDIAN_FT + 2.0, TEX_HEDGE, faces={"b": "skip"})
    for idx, (px, py) in enumerate(((226.5, -813.0), (232.5, -804.0), (227.5, -794.0), (233.0, -786.5))):
        _fan_palm(mb, px, py, h_ft=31.0 + (idx % 3) * 2.5)

    # F. North Union palms south of E 4th St & low shrubs opposite Great Castle south lot
    mb.detail_box_ft(223.5, 746.0, Z_MEDIAN_FT, 234.5, 806.0, Z_MEDIAN_FT + 0.35, TEX_MULCH, faces={"b": "skip"})
    mb.detail_box_ft(224.5, 748.0, Z_MEDIAN_FT + 0.35, 233.5, 804.0, Z_MEDIAN_FT + 2.2, TEX_HEDGE, faces={"b": "skip"})
    for px, py, h_ft in ((227.5, 756.0, 34.0), (231.0, 792.0, 36.0)):
        _fan_palm(mb, px, py, h_ft=h_ft)

    # Keep y = 960..1100 free of tall palms so Great Castle west facade & sign sightlines stay clear
    mb.detail_box_ft(223.5, 905.0, Z_MEDIAN_FT, 234.5, 955.0, Z_MEDIAN_FT + 0.35, TEX_MULCH, faces={"b": "skip"})
    mb.detail_box_ft(224.5, 907.0, Z_MEDIAN_FT + 0.35, 233.5, 953.0, Z_MEDIAN_FT + 2.1, TEX_HEDGE, faces={"b": "skip"})

    # G. Northern median beds & fan palms north of Great Castle (y = 1116..1310, clear of 1275 lamp)
    for y_lo, y_hi in ((1116.0, 1146.0), (1222.0, 1262.0), (1282.0, 1310.0)):
        mb.detail_box_ft(223.5, y_lo, Z_MEDIAN_FT, 234.5, y_hi, Z_MEDIAN_FT + 0.35, TEX_MULCH, faces={"b": "skip"})
        mb.detail_box_ft(224.5, y_lo + 2.0, Z_MEDIAN_FT + 0.35, 233.5, y_hi - 2.0, Z_MEDIAN_FT + 2.2, TEX_HEDGE, faces={"b": "skip"})
    for px, py, h_ft in ((228.5, 1126.0, 33.5), (230.5, 1235.0, 35.5), (227.0, 1295.0, 34.0)):
        _fan_palm(mb, px, py, h_ft=h_ft)


def _ada_curb_ramps(
    mb: MapBuilder,
    rx0: float,
    rx1: float,
    c0: float,
    r0: float,
    r1: float,
    c1: float,
    land_ft: float = 2.0,
) -> None:
    """Emit South & North ADA concrete curb ramps w/ safety-yellow tactile pads inside [c0, c1]."""
    pad_tex = Tile("gwc_yline", w_ft=0.9, h_ft=1.0, rot_deg=90.0)
    # South corner landing + tactile dome pad + ramp down to r0
    _curb_slab(mb, rx0, c0, Z_GROUND_FT, rx1, c0 + land_ft, Z_WALK_FT, TEX_CONC, skip_faces=("n", "e", "w"))
    _walk_mark_top(mb, rx0 + 0.3, c0 + land_ft - 0.9, rx1 - 0.3, c0 + land_ft - 0.1, pad_tex)
    mb.slab_ramp_yft(rx0, rx1, c0 + land_ft, r0, Z_WALK_FT, Z_ROAD_FT, TEX_CONC, thick_ft=0.5, group="detail")
    # North corner ramp up from r1 + landing + tactile dome pad
    mb.slab_ramp_yft(rx0, rx1, r1, c1 - land_ft, Z_ROAD_FT, Z_WALK_FT, TEX_CONC, thick_ft=0.5, group="detail")
    _curb_slab(mb, rx0, c1 - land_ft, Z_GROUND_FT, rx1, c1, Z_WALK_FT, TEX_CONC, skip_faces=("s", "e", "w"))
    _walk_mark_top(mb, rx0 + 0.3, c1 - land_ft + 0.1, rx1 - 0.3, c1 - land_ft + 0.9, pad_tex)


def _alley_sidewalk_crossing(mb: MapBuilder, al0: float, al1: float, y0: float, y1: float) -> None:
    """Emit a depressed concrete alley driveway apron (al0..al1) with 2 ft flared concrete wings."""
    flare = 2.0
    mb.slab_ramp_xft(al0 - flare, al0, y0, y1, Z_WALK_FT, Z_ROAD_FT, TEX_CONC, thick_ft=0.5, group="detail")
    _road_slab(mb, al0, y0, al1, y1, TEX_CONC, skip_faces=("n", "s", "e", "w", "b"))
    mb.slab_ramp_xft(al1, al1 + flare, y0, y1, Z_ROAD_FT, Z_WALK_FT, TEX_CONC, thick_ft=0.5, group="detail")


def _build_cross_streets(mb: MapBuilder) -> None:
    """Build E Belle Terrace, E 4th St, E 5th St, GC rear alley, Trinity, Delaware, Mariposa, Adams, and Amador."""
    bt_c0, bt_c1 = BELLE_TERRACE_CORRIDOR_Y   # (532.0, 582.0)
    bt_r0, bt_r1 = BT_ROAD_Y                  # (534.5, 580.5) -> 46.0 ft asphalt
    e4_c0, e4_c1 = E_4TH_ST_CORRIDOR_Y        # (842.0, 882.0)
    e4_r0, e4_r1 = E_4TH_ST_ROAD_Y            # (847.0, 877.0)
    e5_c0, e5_c1 = E_5TH_ST_CORRIDOR_Y        # (1168.0, 1208.0)
    e5_r0, e5_r1 = E_5TH_ST_ROAD_Y            # (1173.0, 1203.0)
    al_x0, al_x1 = GC_ALLEY_X                 # (414.0, 430.0)
    tr_c0, tr_c1 = TRINITY_AVE_CORRIDOR_Y     # (-166.0, -125.0)
    tr_r0, tr_r1 = TRINITY_AVE_ROAD_Y         # (-161.0, -130.0)
    dl_c0, dl_c1 = DELAWARE_ST_CORRIDOR_X     # (-143.0, -102.0)
    dl_r0, dl_r1 = DELAWARE_ST_ROAD_X         # (-138.0, -107.0)
    mr_c0, mr_c1 = MARIPOSA_AVE_CORRIDOR_Y    # (-476.0, -436.0)
    mr_r0, mr_r1 = MARIPOSA_AVE_ROAD_Y        # (-471.0, -441.0)
    ad_c0, ad_c1 = ADAMS_ST_CORRIDOR_Y        # (-595.0, -555.0)
    ad_r0, ad_r1 = ADAMS_ST_ROAD_Y            # (-590.0, -560.0)
    am_c0, am_c1 = AMADOR_AVE_CORRIDOR_Y      # (-786.0, -746.0)
    am_r0, am_r1 = AMADOR_AVE_ROAD_Y          # (-781.0, -751.0)

    wx0, wx1 = UNION_W_SIDEWALK_X            # (172.0, 178.0)
    ex0, ex1 = UNION_E_SIDEWALK_X            # (277.0, 283.0)
    all_sides_b = ("n", "s", "e", "w", "b")

    # --- 1. E Belle Terrace (y = 532..582 corridor, 534.5..580.5 46 ft roadway) ---
    # Merged continuously across Union sidewalk breaks (wx0..wx1 and ex0..ex1 left open by _sidewalk_with_aprons)
    _road_slab(mb, HX0, bt_r0, wx1, bt_r1, TEX_ASPH, skip_faces=all_sides_b)
    _road_slab(mb, ex0, bt_r0, HX1, bt_r1, TEX_ASPH, skip_faces=all_sides_b)

    # Sidewalks + ADA curb ramps aligned with crosswalks on West & East legs (staying strictly inside 532..582)
    for sx0, sx1, s_skip in (
        (HX0, 165.0, ()),
        (171.0, wx0, ("e",)),
        (ex1, 284.0, ("w",)),
        (290.0, HX1, ()),
    ):
        _curb_slab(mb, sx0, bt_c0, Z_GROUND_FT, sx1, bt_r0, Z_WALK_FT, TEX_CONC, skip_faces=s_skip)
        _curb_slab(mb, sx0, bt_r1, Z_GROUND_FT, sx1, bt_c1, Z_WALK_FT, TEX_CONC, skip_faces=s_skip)
    # 4 ADA ramps at Belle Terrace corners (x=165..171 west leg, x=284..290 east leg)
    for rx0, rx1 in ((165.0, 171.0), (284.0, 290.0)):
        _curb_slab(mb, rx0, bt_c0, Z_GROUND_FT, rx1, bt_c0 + 0.8, Z_WALK_FT, TEX_CONC, skip_faces=("n", "e", "w"))
        mb.slab_ramp_yft(rx0, rx1, bt_c0 + 0.8, bt_r0, Z_WALK_FT, Z_ROAD_FT, TEX_CONC, thick_ft=0.5, group="detail")
        mb.slab_ramp_yft(rx0, rx1, bt_r1, bt_c1 - 0.6, Z_ROAD_FT, Z_WALK_FT, TEX_CONC, thick_ft=0.5, group="detail")
        _curb_slab(mb, rx0, bt_c1 - 0.6, Z_GROUND_FT, rx1, bt_c1, Z_WALK_FT, TEX_CONC, skip_faces=("s", "e", "w"))

    # E Belle Terrace yellow centerlines & lane markings + West leg ladder crosswalk + stop bars
    yline_rot = lambda x_len, y_c: Tile("gwc_yline", w_ft=1.3, h_ft=10.0, u_ofs=(y_c / 1.3) + 0.5, rot_deg=90.0)
    _mark_top(mb, HX0 + 4.0, BELLE_TERRACE_Y - 0.65, 155.0, BELLE_TERRACE_Y + 0.65, yline_rot(645.0, BELLE_TERRACE_Y))
    _mark_top(mb, 298.0, BELLE_TERRACE_Y - 0.65, HX1 - 4.0, BELLE_TERRACE_Y + 0.65, yline_rot(353.0, BELLE_TERRACE_Y))
    _dash_x(mb, bt_r0 + 11.5, HX0 + 8.0, 155.0)
    _dash_x(mb, bt_r1 - 11.5, HX0 + 8.0, 155.0)
    _dash_x(mb, bt_r0 + 11.5, 298.5, HX1 - 8.0)
    _dash_x(mb, bt_r1 - 11.5, 298.5, HX1 - 8.0)

    # White ladder/continental crosswalk on West leg (x=163..172, y=534.5..580.5) + EB stop bar
    _mark_top(
        mb, 163.0, bt_r0, 172.0, bt_r1,
        Tile("gwc_xwalk", w_ft=12.0, h_ft=9.0, v_ofs=172.0 / 9.0, rot_deg=90.0),
    )
    _mark_top(mb, 157.5, bt_r0 + 1.5, 159.0, BELLE_TERRACE_Y - 1.0, Tile("gwc_white", 4.0, 4.0))
    # East leg transverse crosswalk lines & WB stop bar
    _mark_top(mb, 283.0, bt_r0, 284.0, bt_r1, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, 291.0, bt_r0, 292.0, bt_r1, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, 295.0, BELLE_TERRACE_Y + 1.0, 296.5, bt_r1 - 1.5, Tile("gwc_white", 4.0, 4.0))
    # North & South Union crosswalk edge lines (kept across travel lanes only, no overlap on median/stripes)
    for tx0, tx1 in (UNION_SB_CARRIAGE_X, UNION_NB_CARRIAGE_X):
        _mark_top(mb, tx0, bt_r0 - 0.8, tx1, bt_r0, Tile("gwc_white", 4.0, 4.0))
        _mark_top(mb, tx0, bt_r1, tx1, bt_r1 + 0.8, Tile("gwc_white", 4.0, 4.0))

    # --- 2. Trinity Ave (x = -490..-102, y = -166..-125) ---
    _road_slab(mb, HX0, tr_r0, dl_r0, tr_r1, TEX_ASPH, skip_faces=all_sides_b)
    _curb_slab(mb, HX0, tr_r1, Z_GROUND_FT, dl_c1, tr_c1, Z_WALK_FT, TEX_CONC)
    _curb_slab(mb, HX0, tr_c0, Z_GROUND_FT, dl_r0, tr_r0, Z_WALK_FT, TEX_CONC)
    _mark_top(mb, dl_r0 - 4.0, tr_r0 + 1.0, dl_r0 - 2.8, TRINITY_AVE_Y, Tile("gwc_white", 4.0, 4.0))

    # --- 3. Delaware St (x = -143..-102, y = -751..-125) ---
    _road_slab(mb, dl_r0, am_r1, dl_r1, tr_r1, TEX_ASPH, skip_faces=all_sides_b)
    _curb_slab(mb, dl_r1, am_r1, Z_GROUND_FT, dl_c1, tr_r1, Z_WALK_FT, TEX_CONC, skip_faces=("n",))
    _curb_slab(mb, dl_c0, mr_r1, Z_GROUND_FT, dl_r0, tr_c0, Z_WALK_FT, TEX_CONC, skip_faces=("n",))
    _curb_slab(mb, dl_c0, am_c1, Z_GROUND_FT, dl_r0, mr_c0, Z_WALK_FT, TEX_CONC, skip_faces=("n", "s"))
    _mark_top(mb, DELAWARE_ST_X, tr_r0 - 3.5, dl_r1 - 1.0, tr_r0 - 2.3, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, DELAWARE_ST_X, am_r1 + 2.3, dl_r1 - 1.0, am_r1 + 3.5, Tile("gwc_white", 4.0, 4.0))

    # --- 4. Mariposa Ave (x = -490..-138, y = -476..-436) ---
    _road_slab(mb, HX0, mr_r0, dl_r0, mr_r1, TEX_ASPH, skip_faces=all_sides_b)
    _curb_slab(mb, HX0, mr_r1, Z_GROUND_FT, dl_c0, mr_c1, Z_WALK_FT, TEX_CONC, skip_faces=("e",))
    _curb_slab(mb, HX0, mr_c0, Z_GROUND_FT, dl_r0, mr_r0, Z_WALK_FT, TEX_CONC)
    _mark_top(mb, dl_r0 - 4.0, mr_r0 + 1.0, dl_r0 - 2.8, MARIPOSA_AVE_Y, Tile("gwc_white", 4.0, 4.0))

    # --- 5. Adams St (x = 219..650, y = -595..-555: Playfair/Country Inn corner aprons + dusty shoulder east) ---
    _road_slab(mb, ex0, ad_r0, HX1, ad_r1, TEX_ASPH, skip_faces=("w", "e", "b"))
    # Concrete corner aprons at Country Inn (N) and Playfair (S) + gentle transition East
    _curb_slab(mb, ex1, ad_r1, Z_GROUND_FT, 355.0, ad_c1, Z_WALK_FT, TEX_CONC, skip_faces=("w", "e"))
    mb.slab_ramp_xft(355.0, 358.0, ad_r1, ad_c1, Z_WALK_FT, Z_SHOULDER_FT, TEX_CONC, thick_ft=0.5, group="detail")
    _curb_slab(mb, ex1, ad_c0, Z_GROUND_FT, 360.0, ad_r0, Z_WALK_FT, TEX_CONC, skip_faces=("w", "e"))
    mb.slab_ramp_xft(360.0, 363.0, ad_c0, ad_r0, Z_WALK_FT, Z_SHOULDER_FT, TEX_CONC, thick_ft=0.5, group="detail")
    # Uncurbed dusty gravel/dry-grass shoulder east down Adams St (no raised concrete curbs east!)
    mb.detail_box_ft(358.0, ad_r1, Z_GROUND_FT, HX1, ad_c1, Z_SHOULDER_FT, TEX_DRYGRS, faces={"b": "skip", "w": "skip", "e": "skip"})
    mb.detail_box_ft(363.0, ad_c0, Z_GROUND_FT, HX1, ad_r0, Z_SHOULDER_FT, TEX_DRYGRS, faces={"b": "skip", "w": "skip", "e": "skip"})
    # Adams St WB stop bar & short centerline near S Union
    _mark_top(mb, ex1 + 3.0, ADAMS_ST_Y + 0.5, ex1 + 4.5, ad_r1 - 1.5, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, ex1 + 5.5, ADAMS_ST_Y - 0.65, 365.0, ADAMS_ST_Y + 0.65, yline_rot(76.5, ADAMS_ST_Y))

    # --- 6. Amador Ave (x = -490..178, y = -786..-746; Delaware St already spans -751..-130) ---
    _road_slab(mb, HX0, am_r0, wx1, am_r1, TEX_ASPH, skip_faces=all_sides_b)
    _curb_slab(mb, HX0, am_r1, Z_GROUND_FT, dl_r0, am_c1, Z_WALK_FT, TEX_CONC)
    _curb_slab(mb, dl_c1, am_r1, Z_GROUND_FT, wx0, am_c1, Z_WALK_FT, TEX_CONC, skip_faces=("w", "e"))
    _curb_slab(mb, HX0, am_c0, Z_GROUND_FT, wx0, am_r0, Z_WALK_FT, TEX_CONC, skip_faces=("e",))
    _mark_top(mb, wx0 - 4.5, am_r0 + 1.5, wx0 - 3.0, AMADOR_AVE_Y - 0.5, Tile("gwc_white", 4.0, 4.0))

    # --- 7. E 4th St (x = -490..650, y = 842..882, 4-way signalized crossing) ---
    _road_slab(mb, HX0, e4_r0, wx1, e4_r1, TEX_ASPH, skip_faces=all_sides_b)
    _road_slab(mb, ex0, e4_r0, HX1, e4_r1, TEX_ASPH, skip_faces=all_sides_b)
    for sx0, sx1, s_skip in ((HX0, 165.0, ()), (171.0, wx0, ("e",)), (ex1, 284.0, ("w",))):
        _curb_slab(mb, sx0, e4_c0, Z_GROUND_FT, sx1, e4_r0, Z_WALK_FT, TEX_CONC, skip_faces=s_skip)
        _curb_slab(mb, sx0, e4_r1, Z_GROUND_FT, sx1, e4_c1, Z_WALK_FT, TEX_CONC, skip_faces=s_skip)
    _curb_slab(mb, 290.0, e4_c0, Z_GROUND_FT, HX1, e4_r0, Z_WALK_FT, TEX_CONC)
    _curb_slab(mb, 290.0, e4_r1, Z_GROUND_FT, al_x0 - 2.0, e4_c1, Z_WALK_FT, TEX_CONC, skip_faces=("e",))
    _alley_sidewalk_crossing(mb, al_x0, al_x1, e4_r1, e4_c1)
    _curb_slab(mb, al_x1 + 2.0, e4_r1, Z_GROUND_FT, HX1, e4_c1, Z_WALK_FT, TEX_CONC, skip_faces=("w",))
    for rx0, rx1 in ((165.0, 171.0), (284.0, 290.0)):
        _ada_curb_ramps(mb, rx0, rx1, e4_c0, e4_r0, e4_r1, e4_c1)
    # E 4th yellow centerlines, West/East leg crosswalks & EB/WB stop bars
    _mark_top(mb, HX0 + 4.0, E_4TH_ST_Y - 0.65, 155.0, E_4TH_ST_Y + 0.65, yline_rot(645.0, E_4TH_ST_Y))
    _mark_top(mb, 298.5, E_4TH_ST_Y - 0.65, HX1 - 4.0, E_4TH_ST_Y + 0.65, yline_rot(352.0, E_4TH_ST_Y))
    for cx0, cx1 in ((164.0, 171.5), (283.5, 291.0)):
        _mark_top(
            mb, cx0, e4_r0 + 0.2, cx1, e4_r1 - 0.2,
            Tile("gwc_xwalk", w_ft=12.0, h_ft=7.5, v_ofs=cx1 / 7.5, rot_deg=90.0),
        )
    _mark_top(mb, 157.5, e4_r0 + 1.5, 159.0, E_4TH_ST_Y - 1.0, Tile("gwc_white", 4.0, 4.0))
    _mark_top(mb, 294.5, E_4TH_ST_Y + 1.0, 296.0, e4_r1 - 1.5, Tile("gwc_white", 4.0, 4.0))
    # Painted desert-sunset utility cabinet on NE sidewalk clear of ADA ramp & Great Castle parcel
    mb.detail_box_ft(
        290.8, 878.0, Z_WALK_FT, 294.2, 881.2, Z_WALK_FT + 4.8,
        "gwc_galv",
        faces={"n": Fit("gwc_utilart"), "s": Fit("gwc_utilart"), "e": Fit("gwc_utilart"), "w": Fit("gwc_utilart"), "b": "skip"},
    )

    # --- 8. E 5th St (x = 277..650, y = 1168..1208, unsignalized East T-junction) ---
    _road_slab(mb, ex0, e5_r0, HX1, e5_r1, TEX_ASPH, skip_faces=all_sides_b)
    for sx0, sx1, s_skip in ((ex1, 284.0, ("w",)), (290.0, al_x0 - 2.0, ("e",)), (al_x1 + 2.0, HX1, ("w",))):
        _curb_slab(mb, sx0, e5_c0, Z_GROUND_FT, sx1, e5_r0, Z_WALK_FT, TEX_CONC, skip_faces=s_skip)
        _curb_slab(mb, sx0, e5_r1, Z_GROUND_FT, sx1, e5_c1, Z_WALK_FT, TEX_CONC, skip_faces=s_skip)
    _ada_curb_ramps(mb, 284.0, 290.0, e5_c0, e5_r0, e5_r1, e5_c1)
    _alley_sidewalk_crossing(mb, al_x0, al_x1, e5_c0, e5_r0)
    _alley_sidewalk_crossing(mb, al_x0, al_x1, e5_r1, e5_c1)
    _mark_top(mb, 298.5, E_5TH_ST_Y - 0.65, HX1 - 4.0, E_5TH_ST_Y + 0.65, yline_rot(352.0, E_5TH_ST_Y))
    _mark_top(
        mb, 283.5, e5_r0 + 0.2, 291.0, e5_r1 - 0.2,
        Tile("gwc_xwalk", w_ft=12.0, h_ft=7.5, v_ofs=291.0 / 7.5, rot_deg=90.0),
    )
    _mark_top(mb, 294.5, E_5TH_ST_Y + 0.5, 296.0, e5_r1 - 1.5, Tile("gwc_white", 4.0, 4.0))

    # --- 9. Great Castle Rear Service Alley (x = 414..430; keep e/w textured at Z_ROAD_FT) ---
    _road_slab(mb, al_x0, e4_c1, al_x1, e5_c0, TEX_ASPH, skip_faces=("n", "s", "b"))
    _road_slab(mb, al_x0, e5_c1, al_x1, HY1, TEX_ASPH, skip_faces=("n", "s", "b"))

    # Fill lights on cross streets so intersections stay bright & uniform
    for lx, ly in (
        (-320.0, BELLE_TERRACE_Y),
        (-110.0, BELLE_TERRACE_Y),
        (40.0, BELLE_TERRACE_Y),
        (228.0, BELLE_TERRACE_Y),
        (420.0, BELLE_TERRACE_Y),
        (-320.0, E_4TH_ST_Y),
        (-110.0, E_4TH_ST_Y),
        (60.0, E_4TH_ST_Y),
        (228.0, E_4TH_ST_Y),
        (430.0, E_4TH_ST_Y),
        (360.0, E_5TH_ST_Y),
        (510.0, E_5TH_ST_Y),
        (422.0, 1025.0),
        (-260.0, TRINITY_AVE_Y),
        (-122.5, -310.0),
        (-122.5, -600.0),
        (-260.0, MARIPOSA_AVE_Y),
        (430.0, ADAMS_ST_Y),
        (-20.0, AMADOR_AVE_Y),
    ):
        mb.light_ft(lx, ly, 24.0, light=150.0, color=(255, 238, 206), wait=0.55)


def _signal_head(mb: MapBuilder, cx: float, cy: float, z_bot: float, facing_axis: str) -> None:
    """Emit a 3-lens vertical traffic signal head (R/Y/G) facing N/S or E/W."""
    mb.illus_box_ft(cx - 0.65, cy - 0.65, z_bot, cx + 0.65, cy + 0.65, z_bot + 3.6, "gwc_dark", faces={"t": "skip"})
    lenses = (
        (z_bot + 2.45, z_bot + 3.40, "gwc_tsig_r"),
        (z_bot + 1.32, z_bot + 2.27, "gwc_tsig_y"),
        (z_bot + 0.20, z_bot + 1.15, "gwc_tsig_g"),
    )
    for lz0, lz1, tex in lenses:
        if facing_axis == "ns":
            mb.flush_panel_ft(
                cx - 0.50, cy - 0.70, lz0, cx + 0.50, cy + 0.70, lz1,
                {"n": Fit(tex), "s": Fit(tex)}, group="illus",
            )
        else:
            mb.flush_panel_ft(
                cx - 0.70, cy - 0.50, lz0, cx + 0.70, cy + 0.50, lz1,
                {"e": Fit(tex), "w": Fit(tex)}, group="illus",
            )


def _build_signal_rig(
    mb: MapBuilder,
    signals: Sequence[Tuple[float, float, int, int, float, Tuple[float, ...], str, Tuple[float, float]]],
    ped_corners: Sequence[Tuple[float, float]],
) -> None:
    """Emit 4 galvanized cantilever mast-arm traffic signals with blades, luminaires, and ped pedestals."""
    for px, py, dx, dy, arm_len, heads, blade_tex, (b0, b1) in signals:
        # Mast pole + luminaire riser (ground base & concealed ends culled to skip)
        mb.detail_box_ft(px - 0.45, py - 0.45, Z_WALK_FT, px + 0.45, py + 0.45, 22.0, "gwc_galv", faces={"b": "skip"})
        mb.illus_box_ft(px - 0.25, py - 0.25, 22.0, px + 0.25, py + 0.25, 28.5, "gwc_galv", faces={"b": "skip", "t": "skip"})
        if dx != 0:
            ax0, ax1 = sorted((px, px + dx * arm_len))
            arm_skip = {"w": "skip"} if dx > 0 else {"e": "skip"}
            mb.illus_box_ft(ax0, py - 0.28, 19.8, ax1, py + 0.28, 20.4, "gwc_galv", faces=arm_skip)
            lx0, lx1 = sorted((px, px + dx * 10.0))
            mb.illus_box_ft(lx0, py - 0.20, 28.2, lx1, py + 0.20, 28.7, "gwc_galv", faces=arm_skip)
            mb.illus_box_ft(px + dx * 9.5 - 0.7, py - 0.5, 27.9, px + dx * 9.5 + 0.7, py + 0.5, 28.4, "gwc_white")
            for k in heads:
                _signal_head(mb, px + dx * k, py, 16.2, "ns")
            bx0, bx1 = sorted((px + dx * b0, px + dx * b1))
            mb.illus_box_ft(bx0, py - 0.16, 20.5, bx1, py + 0.16, 22.4, "gwc_dark", faces={"n": Fit(blade_tex), "s": Fit(blade_tex), "b": "skip"})
        else:
            ay0, ay1 = sorted((py, py + dy * arm_len))
            arm_skip = {"s": "skip"} if dy > 0 else {"n": "skip"}
            mb.illus_box_ft(px - 0.28, ay0, 19.8, px + 0.28, ay1, 20.4, "gwc_galv", faces=arm_skip)
            ly0, ly1 = sorted((py, py + dy * 9.5))
            mb.illus_box_ft(px - 0.20, ly0, 28.2, px + 0.20, ly1, 28.7, "gwc_galv", faces=arm_skip)
            mb.illus_box_ft(px - 0.5, py + dy * 9.0 - 0.7, 27.9, px + 0.5, py + dy * 9.0 + 0.7, 28.4, "gwc_white")
            for k in heads:
                _signal_head(mb, px, py + dy * k, 16.2, "ew")
            by0, by1 = sorted((py + dy * b0, py + dy * b1))
            mb.illus_box_ft(px - 0.16, by0, 20.5, px + 0.16, by1, 22.4, "gwc_dark", faces={"e": Fit(blade_tex), "w": Fit(blade_tex), "b": "skip"})

    for cx, cy in ped_corners:
        mb.detail_box_ft(cx - 0.22, cy - 0.22, Z_WALK_FT, cx + 0.22, cy + 0.22, 3.8, "gwc_galv", faces={"b": "skip", "t": "skip"})
        mb.detail_box_ft(
            cx - 0.45, cy - 0.45, 3.8, cx + 0.45, cy + 0.45, 4.9, "gwc_dark",
            faces={"n": Fit("gwc_pedx"), "s": Fit("gwc_pedx"), "e": Fit("gwc_pedx"), "w": Fit("gwc_pedx"), "b": "skip"},
        )


def _build_traffic_signals(mb: MapBuilder) -> None:
    """Build 4-way signalized cantilever rigs at E Belle Terrace and E 4th St along S Union Ave."""
    bt_signals = (
        (174.8, 533.25, 1, 0, 36.0, (11.0, 23.5, 34.5), "gwc_sbelle", (4.0, 13.5)),   # SW -> E over SB lanes
        (280.2, 581.25, -1, 0, 36.0, (11.0, 23.5, 34.5), "gwc_sbelle", (4.0, 13.5)),  # NE -> W over NB lanes
        (280.2, 533.25, 0, 1, 36.0, (13.0, 26.0, 34.5), "gwc_sunion", (4.5, 13.5)),   # SE -> N over widened Belle Terrace
        (174.8, 581.25, 0, -1, 36.0, (13.0, 26.0, 34.5), "gwc_sunion", (4.5, 13.5)),  # NW -> S over widened Belle Terrace
    )
    bt_peds = ((176.2, 530.5), (176.2, 583.5), (278.8, 530.5), (278.8, 583.5))
    _build_signal_rig(mb, bt_signals, bt_peds)

    e4_signals = (
        (174.8, 845.2, 1, 0, 36.0, (11.0, 23.5, 34.5), "gwc_e4st", (4.0, 13.5)),    # SW -> E over SB lanes
        (280.2, 878.8, -1, 0, 36.0, (11.0, 23.5, 34.5), "gwc_e4st", (4.0, 13.5)),   # NE -> W over NB lanes
        (280.2, 845.2, 0, 1, 27.0, (15.0, 25.0), "gwc_sunion", (3.5, 9.5)),         # SE -> N over 30 ft E 4th St
        (174.8, 878.8, 0, -1, 27.0, (15.0, 25.0), "gwc_sunion", (3.5, 9.5)),        # NW -> S over 30 ft E 4th St
    )
    e4_peds = ((176.2, 839.2), (176.2, 884.8), (278.8, 839.2), (278.8, 884.8))
    _build_signal_rig(mb, e4_signals, e4_peds)


def _build_utility_poles_and_lamps(mb: MapBuilder) -> None:
    """Build median twin-arm Y cobra-head streetlamps, green electrical boxes,
    East-curb wooden 3-crossarm utility poles w/ transformers, and overhead crossing wires.
    """
    # 1. Silver twin-arm Y cobra-head streetlamps along median (~28-30 ft tall)
    lamp_ys = (-720.0, -515.0, -350.0, -145.0, 52.0, 222.0, 400.0, 708.0, 812.0, 958.0, 1110.0, 1275.0)
    mx = 228.5
    for ly in lamp_ys:
        mb.detail_box_ft(mx - 0.35, ly - 0.35, Z_MEDIAN_FT, mx + 0.35, ly + 0.35, 25.5, "gwc_galv", faces={"b": "skip", "t": "skip"})
        mb.slab_ramp_xft(mx - 8.0, mx - 0.2, ly - 0.22, ly + 0.22, 29.0, 25.4, "gwc_galv", thick_ft=0.38, group="illus")
        mb.slab_ramp_xft(mx + 0.2, mx + 8.0, ly - 0.22, ly + 0.22, 25.4, 29.0, "gwc_galv", thick_ft=0.38, group="illus")
        mb.illus_box_ft(mx - 9.2, ly - 0.55, 28.6, mx - 7.4, ly + 0.55, 29.3, "gwc_galv", faces={"b": "gwc_white"})
        mb.illus_box_ft(mx + 7.4, ly - 0.55, 28.6, mx + 9.2, ly + 0.55, 29.3, "gwc_galv", faces={"b": "gwc_white"})

    # 2. Low green electrical / irrigation boxes along median
    for uy in (-430.0, -165.0, 48.0, 438.0, 896.0):
        mb.detail_box_ft(
            227.0, uy - 1.0, Z_MEDIAN_FT, 229.8, uy + 1.0, Z_MEDIAN_FT + 2.8,
            Fit("gwc_utilbox"), faces={"t": "gwc_galv", "b": "skip"},
        )

    # 3. East curb wooden 3-crossarm utility poles (x = UNION_POLE_X = 282.0)
    pole_ys = (
        -790.0, -685.0, -535.0, -395.0, -245.0, -80.0, 65.0, 210.0, 335.0,
        495.0, 590.0, 725.0, 832.0, 892.0, 1078.0, 1214.0, 1320.0,
    )
    px = UNION_POLE_X
    for idx, py in enumerate(pole_ys):
        mb.detail_box_ft(px - 0.45, py - 0.45, Z_WALK_FT, px + 0.45, py + 0.45, 38.0, TEX_BARK, faces={"b": "skip"})
        for cz in (30.5, 34.0, 37.2):
            mb.illus_box_ft(px - 4.0, py - 0.22, cz, px + 4.0, py + 0.22, cz + 0.42, "gwc_beam")
        if idx in (2, 5, 7, 10, 13, 15):
            mb.cyl_ft(px - 1.2, py, 0.75, 24.5, 28.2, sides=6, tex_side="gwc_galv", tex_top="gwc_galv", group="illus")

    # Longitudinal primary & neutral overhead wires along East curb (skip end caps & unseen 1.7-in sky tops)
    wire_runs = ((-790.0, -395.0), (-395.0, 65.0), (65.0, 495.0), (495.0, 892.0), (892.0, 1320.0))
    for y0, y1 in wire_runs:
        for wx, wz in ((px - 3.2, 37.6), (px + 3.2, 37.6), (px - 2.6, 34.4), (px, 30.9)):
            mb.illus_box_ft(wx - 0.07, y0, wz, wx + 0.07, y1, wz + 0.14, "gwc_dark", faces={"n": "skip", "s": "skip", "t": "skip"})

    # Overhead crossing wires at E 4th St (y=892), E Belle Terrace (y=590), and Adams St (y=-535)
    # Offset vertically above longitudinal wires so orthogonal wires never overlap coplanarly
    for wy in (892.0, 590.0, -535.0):
        for wz in (34.70, 37.90):
            mb.illus_box_ft(HX0 + 8.0, wy - 0.08, wz, px - 0.2, wy + 0.08, wz + 0.16, "gwc_dark", faces={"e": "skip", "w": "skip", "t": "skip"})
    for wy in (-535.0, 892.0):
        for wz in (34.70, 37.90):
            mb.illus_box_ft(px + 0.2, wy - 0.08, wz, HX1 - 8.0, wy + 0.08, wz + 0.16, "gwc_dark", faces={"e": "skip", "w": "skip", "t": "skip"})


def _street_sign_post(
    mb: MapBuilder,
    x_ft: float,
    y_ft: float,
    tex_ew: str,
    tex_ns: str,
    stop_face: Optional[str] = None,
) -> None:
    """Emit a galvanized street-name blade signpost (+ optional octagonal STOP sign)."""
    mb.detail_box_ft(x_ft - 0.15, y_ft - 0.15, Z_WALK_FT, x_ft + 0.15, y_ft + 0.15, 10.6, "gwc_galv", faces={"b": "skip"})
    mb.illus_box_ft(
        x_ft - 2.3, y_ft - 0.10, 9.6, x_ft + 2.3, y_ft + 0.10, 10.7,
        "gwc_steel", faces={"n": Fit(tex_ew), "s": Fit(tex_ew)},
    )
    mb.illus_box_ft(
        x_ft - 0.10, y_ft - 2.3, 8.5, x_ft + 0.10, y_ft + 2.3, 9.6,
        "gwc_steel", faces={"e": Fit(tex_ns), "w": Fit(tex_ns)},
    )
    if stop_face:
        sgn = 1.0 if stop_face in ("n", "e") else -1.0
        p0, p1 = sorted((sgn * 0.16, sgn * 0.28))
        if stop_face in ("e", "w"):
            mb.flush_panel_ft(
                x_ft + p0, y_ft - 1.25, 6.0, x_ft + p1, y_ft + 1.25, 8.4,
                {stop_face: Fit("{gwc_stopsign")}, group="illus",
            )
        else:
            mb.flush_panel_ft(
                x_ft - 1.25, y_ft + p0, 6.0, x_ft + 1.25, y_ft + p1, 8.4,
                {stop_face: Fit("{gwc_stopsign")}, group="illus",
            )


def _guide_sign_post(mb: MapBuilder, x_ft: float, y_ft: float, face: str, tex: str, w_ft: float = 2.6, h_ft: float = 2.6) -> None:
    """Emit a roadside regulatory/route shield post (plate mounted flush in front of post)."""
    mb.detail_box_ft(x_ft - 0.14, y_ft - 0.14, Z_WALK_FT, x_ft + 0.14, y_ft + 0.14, 9.8, "gwc_galv", faces={"b": "skip"})
    hw = 0.5 * w_ft
    sgn = 1.0 if face in ("n", "e") else -1.0
    p0, p1 = sorted((sgn * 0.16, sgn * 0.28))
    if face in ("n", "s"):
        mb.illus_box_ft(
            x_ft - hw, y_ft + p0, 7.0, x_ft + hw, y_ft + p1, 7.0 + h_ft,
            "gwc_galv", faces={face: Fit(tex)},
        )
    else:
        mb.illus_box_ft(
            x_ft + p0, y_ft - hw, 7.0, x_ft + p1, y_ft + hw, 7.0 + h_ft,
            "gwc_galv", faces={face: Fit(tex)},
        )


def _build_street_signs_and_spots(mb: MapBuilder) -> None:
    """Place legible intersection street blades, route/speed signs, and spot_ft markers."""
    # Cross-street intersection blade posts + STOP signs
    _street_sign_post(mb, 280.5, 1205.5, "gwc_e5st", "gwc_sunion", stop_face="e")
    _street_sign_post(mb, 280.5, -557.0, "gwc_sadams", "gwc_sunion", stop_face="e")
    _street_sign_post(mb, 174.5, -748.5, "gwc_samad", "gwc_sunion", stop_face="w")
    _street_sign_post(mb, -140.5, -127.5, "gwc_strin", "gwc_sdel", stop_face="w")
    _street_sign_post(mb, -140.5, -438.5, "gwc_smari", "gwc_sdel", stop_face="w")
    _street_sign_post(mb, -140.5, -748.5, "gwc_samad", "gwc_sdel", stop_face="s")

    # CA-99 Business Union Ave shields & Speed Limit 45 signs along S Union Ave
    _guide_sign_post(mb, 174.5, 1290.0, "n", "gwc_spd45", w_ft=2.4, h_ft=3.0)
    _guide_sign_post(mb, 174.5, 1020.0, "n", "gwc_ca99")
    _guide_sign_post(mb, 174.5, 480.0, "n", "gwc_ca99")
    _guide_sign_post(mb, 174.5, 310.0, "n", "gwc_spd45", w_ft=2.4, h_ft=3.0)
    _guide_sign_post(mb, 280.5, 1295.0, "s", "gwc_ca99")
    _guide_sign_post(mb, 280.5, 920.0, "s", "gwc_spd45", w_ft=2.4, h_ft=3.0)
    _guide_sign_post(mb, 280.5, -490.0, "s", "gwc_ca99")
    _guide_sign_post(mb, 280.5, -260.0, "s", "gwc_spd45", w_ft=2.4, h_ft=3.0)

    # Register canonical street spot_ft markers (z = 4.5 ft -> 2.3 ft above Hull-1 stand z, non-solid)
    mb.spot_ft("S Union Ave Casino Front", 200.0, -35.0, 4.5, yaw=135.0, pitch=2.0, kind="walk", desc="S Union SB opposite 1001 S Union frontage")
    mb.spot_ft("S Union Ave Northbound", 257.5, -180.0, 4.5, yaw=105.0, pitch=2.0, kind="walk", desc="S Union NB mid-corridor looking NNW")
    mb.spot_ft("S Union Ave South", 200.0, -640.0, 4.5, yaw=75.0, pitch=2.0, kind="walk", desc="S Union SB south near Adams and Amador")
    mb.spot_ft("E Belle Terrace Intersection", 148.0, BELLE_TERRACE_Y, 4.5, yaw=0.0, pitch=2.0, kind="walk", desc="E Belle Terrace & S Union 4-way signalized intersection")
    mb.spot_ft("E 4th St Intersection", 148.0, E_4TH_ST_Y, 4.5, yaw=0.0, pitch=2.0, kind="walk", desc="E 4th St & S Union 4-way signalized intersection w/ green bike boxes")
    mb.spot_ft("Great Castle Front", 200.0, 1030.0, 4.5, yaw=0.0, pitch=0.0, kind="walk", desc="S Union Ave looking East at Great Castle 410 Union facade")
    mb.spot_ft("E 5th St T-Junction", 320.0, E_5TH_ST_Y, 4.5, yaw=180.0, pitch=2.0, kind="walk", desc="E 5th St looking West toward STOP sign & S Union Ave")
    mb.spot_ft("Great Castle Rear Alley", 422.0, 1030.0, 4.5, yaw=90.0, pitch=2.0, kind="walk", desc="Rear service alley behind Great Castle looking North toward E 5th St")
    mb.spot_ft("Adams St East", 298.0, ADAMS_ST_Y, 4.5, yaw=10.0, pitch=2.0, kind="walk", desc="Adams St looking East from S Union")
    mb.spot_ft("Delaware St Corridor", DELAWARE_ST_X, -310.0, 4.5, yaw=90.0, pitch=2.0, kind="walk", desc="Delaware St looking North between Mariposa and Trinity")
    mb.spot_ft("Trinity Ave", -220.0, TRINITY_AVE_Y, 4.5, yaw=0.0, pitch=2.0, kind="walk", desc="Trinity Ave looking East toward Delaware St")
    mb.spot_ft("Mariposa Ave", -220.0, MARIPOSA_AVE_Y, 4.5, yaw=0.0, pitch=2.0, kind="walk", desc="Mariposa Ave looking East toward Delaware St")
    mb.spot_ft("Amador Ave", 60.0, AMADOR_AVE_Y, 4.5, yaw=10.0, pitch=2.0, kind="walk", desc="Amador Ave looking East toward S Union Ave")
    mb.spot_ft("Aerial S Union Corridor", 350.0, -80.0, 82.0, yaw=165.0, pitch=26.0, kind="aerial", desc="High aerial overview of S Union Ave & Golden West")
    mb.spot_ft("Aerial North Union Corridor", 340.0, 1040.0, 82.0, yaw=165.0, pitch=26.0, kind="aerial", desc="High aerial overview of E 4th, Great Castle & E 5th St")


def build_streets(mb: MapBuilder) -> Dict[str, object]:
    """Build the sealed skybox hull, continuous earth bed, S Union Ave 3+3 boulevard,
    raised herringbone brick median w/ GIS plantings, all cross streets & GC rear alley,
    traffic signals, utility poles, street signs, and street spot_ft markers.
    """
    global Tile, Fit
    mb_mod = sys.modules.get(type(mb).__module__)
    if mb_mod is not None and hasattr(mb_mod, "Tile") and hasattr(mb_mod, "Fit"):
        if mb_mod.Tile is not Tile or mb_mod.Fit is not Fit:
            Tile = mb_mod.Tile  # type: ignore[misc]
            Fit = mb_mod.Fit    # type: ignore[misc]
            _refresh_shared_tiles()

    _build_world_shell_and_bed(mb)
    _build_s_union_ave(mb)
    _build_median_and_plantings(mb)
    _build_cross_streets(mb)
    _build_traffic_signals(mb)
    _build_utility_poles_and_lamps(mb)
    _build_street_signs_and_spots(mb)
    return mb.stats()


def _count_faces(mb: MapBuilder) -> Tuple[int, int]:
    """Return (total_faces, active_non_skip_faces) across all brushes in MapBuilder."""
    total = 0
    active = 0
    for grp_brushes in mb._brushes.values():
        for _bbox, planes in grp_brushes:
            total += len(planes)
            for pl in planes:
                parts = pl.split(")")
                if len(parts) >= 4:
                    tex = parts[3].strip().split()[0].lower()
                    if tex != "skip":
                        active += 1
    return total, active


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Standalone validation for gw_streets.py")
    parser.add_argument("--compile", action="store_true", help="Also run standalone qbsp -leaktest smoke compile")
    args = parser.parse_args(argv)

    mb = MapBuilder(strict_vis=True, check_textures=True, require_gwc_prefix=True)
    build_streets(mb)
    warnings = mb.validate_all()
    stats = mb.stats()
    total_faces, active_faces = _count_faces(mb)

    print(f"[gw_streets] Loaded WADs: {stats['loaded_wads']}")
    print(f"[gw_streets] Brushes: {stats['brushes']} (total={stats['total_brushes']})")
    print(f"[gw_streets] Faces: total={total_faces}, active_non_skip={active_faces}")
    print(f"[gw_streets] Spots: {stats['spots']} | Entities: {stats['entities']} | Textures: {len(stats['textures_used'])}")
    if warnings:
        print(f"[gw_streets] Warnings: {warnings}")

    if args.compile:
        import shutil
        import tempfile
        if __package__:
            from .compile_gw import compile_map
        else:
            from compile_gw import compile_map

        # Add temporary info_player_start for standalone BSP leaktest check
        mb.ent_ft("info_player_start", 200.0, -35.0, 4.5, angle="135")
        tmp_dir = tempfile.mkdtemp(prefix="gw_streets_test_")
        try:
            tmp_map = os.path.join(tmp_dir, "test_streets.map")
            tmp_stats = os.path.join(tmp_dir, "test_stats.json")
            mb.write_map(tmp_map, validate=True)
            cstats = compile_map(tmp_map, fast=True, no_copy=True, stats_out_path=tmp_stats)
            print(f"[gw_streets] Standalone compile PASS: {cstats['bsp']['format']} {cstats['bsp']['size_bytes']} B in {cstats['total_sec']}s")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
