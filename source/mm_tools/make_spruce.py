"""make_spruce.py — Generates `out/maps/spruce.map` + `out/maps/spruce.spots.json`:
A 1:1 scale (12 Quake units/ft) replica of the Westchester / Spruce St neighborhood & Water Tower,
Bakersfield, CA 93301, built strictly from `spruce-street-gallery-self-contained.html` + calibrated GIS.

Supports progressive stages via `SPRUCE_STAGE=1|2|3` (default 3 = complete neighborhood):
  Stage 1: Terrain, full curved road & alley network, curbs, road stencils, and the 105-ft Water Tower + compound.
  Stage 2: Anchor houses (3003, 3075/3060 screenshot house, 3013, 3059, 3055, 3058) + all GIS loop/spur houses & garages.
  Stage 3: Commercial landmarks (CITYSERVE, Smart & Final / Dollar Tree, Westchester Apts, Jacaranda Dr, Beech x Hubbard),
           fences, '3035' & curbside bins, utility poles/wires, signs, trees, vehicles, and Deathmatch gameplay.
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from spruce_lib import (  # noqa: E402
    ENTS,
    Fit,
    GIS,
    GROUPS,
    OX,
    OY,
    U,
    WADS,
    box,
    brush_ent,
    brush_vehicle,
    cedar_tree,
    check_placed,
    convex_parts,
    ent,
    eucalyptus_tree,
    fence_line,
    frustum_ring,
    hiproof,
    light,
    obox,
    offset_convex,
    ogable,
    osloped_panel,
    prism,
    prop,
    road_ribbon,
    road_stencil,
    shade_tree,
    smooth_curve,
    strut_3d,
    trash_bin,
    tspec,
    ui,
)
from spruce_stage3 import build_stage3  # noqa: E402

OUT_MAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "maps", "spruce.map")
STAGE = int(os.environ.get("SPRUCE_STAGE", "3"))

# Index GIS buildings by short ID (`id % 10000`)
BY_SID = {"map": {}, "done": set()}
for _b in GIS["buildings"]:
    BY_SID["map"].setdefault(_b["sid"], []).append(_b)

# ==============================================================================
# STAGE 1A. SEALED WORLD HULL & NEIGHBORHOOD GROUND ZONES
# ==============================================================================
HX0, HX1, HY0, HY1, SKY_Z = -780.0, 960.0, -820.0, 800.0, 220.0
LAWN = tspec("sp_lawn", 14)
DRYLAWN = tspec("sp_drylawn", 14)
AUTLAWN = tspec("sp_autlawn", 12)
ASPH = tspec("sp_asphalt", 16)
ALLEY = tspec("sp_alley", 12)
GRAVEL = tspec("sp_gravel", 12)
CONC = tspec("sp_conc", 8)

# Sealed outer skybox + solid lawn world base (z = -4 .. 0)
box(HX0 - 4, HY0 - 4, -6.0, HX1 + 4, HY1 + 4, -4.0, "sp_alley", group="world")
box(HX0, HY0, -4.0, HX1, HY1, 0.0, LAWN, group="world")
box(HX0 - 4, HY0 - 4, SKY_Z, HX1 + 4, HY1 + 4, SKY_Z + 4, "sky_bk", group="world")
box(HX0 - 4, HY0 - 4, -4.0, HX0, HY1 + 4, SKY_Z, "sky_bk", group="world")
box(HX1, HY0 - 4, -4.0, HX1 + 4, HY1 + 4, SKY_Z, "sky_bk", group="world")
box(HX0, HY0 - 4, -4.0, HX1, HY0, SKY_Z, "sky_bk", group="world")
box(HX0, HY1, -4.0, HX1, HY1 + 4, SKY_Z, "sky_bk", group="world")
for cx0, cy0, cx1, cy1 in (
    (HX0, HY0, HX0 + 4, HY1),
    (HX1 - 4, HY0, HX1, HY1),
    (HX0, HY0, HX1, HY0 + 4),
    (HX0, HY1 - 4, HX1, HY1),
):
    box(cx0, cy0, 0.0, cx1, cy1, SKY_Z, "clip", group="world")

# Special yard ground patches matching Street View:
# 1) Water Tower fenced decomposed-granite / gravel yard (x = -132..+34, y = 384.5..560)
prism([(-132.0, 384.5), (34.0, 384.5), (34.0, 560.0), (-102.0, 560.0)], -0.1, 0.06, GRAVEL, group="detail", solid=True)
# 2) 3001 Spruce St golden autumn leaf-strewn front yard (`img_039.jpg`!)
obox(-84.0, -278.0, -0.05, 0.04, 24.0, 22.0, 322.0, AUTLAWN, group="detail", solid=True)
# 3) 3059 Spruce St patchy summer lawn at East Junction fork (`img_064.jpg`!)
obox(82.0, -52.0, -0.05, 0.04, 28.0, 24.0, 298.0, DRYLAWN, group="detail", solid=True)

# ==============================================================================
# STAGE 1B. SATELLITE-CALIBRATED ROAD & ALLEY NETWORK + CURBS + STENCILS
# ==============================================================================
# 1. Spruce St Residential Loop (~200 m across, smooth curves matching `loop_ids_1266.jpg`!)
LOOP_SOUTH = smooth_curve([(-122.0, 8.0), (-106.0, -10.0), (-68.0, -30.0), (-16.0, -57.0), (50.0, -93.0), (111.3, -126.4)], 4)
LOOP_EAST = [(111.3, -126.4), (178.0, -40.0), (243.0, 42.0), (308.0, 125.0)]
LOOP_NORTH = smooth_curve([(308.0, 125.0), (274.0, 174.0), (232.0, 212.0), (188.0, 226.5), (115.0, 227.5), (-35.0, 228.5), (-62.0, 218.0), (-75.0, 186.0)], 4)
LOOP_WEST = smooth_curve([(-75.0, 186.0), (-91.2, 105.7), (-116.0, 22.0), (-122.0, 8.0)], 3)

for seg in (LOOP_SOUTH, LOOP_EAST, LOOP_NORTH, LOOP_WEST):
    road_ribbon(seg, 30.0, ASPH, curbs=True)

# 2. Spruce St 3003 Spur -> Beech St -> 2883/2801 Spruce St -> Hubbard St (`width = 32 ft`)
SPRUCE_SPUR_SW = [(111.3, -126.4), (24.0, -241.0), (-76.6, -374.2), (-209.4, -544.8), (-335.0, -708.0)]
road_ribbon(SPRUCE_SPUR_SW, 32.0, ASPH, curbs=True)

# 3. Spruce St NE Spur (3010-3022 block)
road_ribbon([(308.0, 125.0), (435.0, 285.0)], 30.0, ASPH, curbs=True)

# 4. Beech St / 30th St sweeping curve across SE/S (`width = 40 ft`, sidewalks!)
BEECH_30TH = smooth_curve([
    (-732.0, -638.0), (-344.0, -345.0), (-284.0, -318.5), (-219.0, -311.6),
    (-154.0, -325.0), (-118.0, -342.0), (-76.6, -374.2), (38.0, -467.0),
    (160.0, -558.4), (397.0, -742.6),
], 3)
road_ribbon(BEECH_30TH, 40.0, ASPH, curbs=True, sidewalks=True, sw_w=4.5)

# 5. Hubbard St (SW parallel street, `img_138`: 'Hubbard St' asphalt stencil!)
HUBBARD = [(-735.0, -640.0), (-592.7, -747.2), (-420.0, -810.0)]
road_ribbon(HUBBARD, 34.0, ASPH, curbs=True)

# 6. Jacaranda Dr (`width = 36 ft` with concrete sidewalks, `img_162..168`) + feeder into Loop SW elbow!
JACARANDA = smooth_curve([
    (-734.0, -210.0), (-548.8, -70.2), (-482.3, -5.8), (-455.2, 32.0),
    (-424.0, 96.0), (-392.0, 195.0), (-408.0, 248.0), (-452.0, 265.0),
    (-545.0, 266.0), (-653.0, 330.5),
], 3)
road_ribbon(JACARANDA, 36.0, ASPH, curbs=True, sidewalks=True, sw_w=4.8)
# Short connector / mouth from Loop SW (`-122, 8`) WSW toward Jacaranda / alley
road_ribbon([(-122.0, 8.0), (-162.0, -8.0)], 26.0, ASPH, curbs=True)

# 7. Pine St & Elm St & Golden State Frontage Ave (framing perimeter streets)
road_ribbon([(160.0, -558.4), (295.0, -385.0)], 34.0, ASPH, curbs=True)
ELM_ST = smooth_curve([(-760.0, 320.0), (-623.0, 501.0), (-463.0, 545.0), (-350.0, 700.0)], 3)
road_ribbon(ELM_ST, 38.0, ASPH, curbs=True)
road_ribbon([(940.0, 200.0), (566.0, 538.0), (290.0, 780.0)], 40.0, ASPH, curbs=True)

# 8. Paved Narrow Rear Alleys (`width = 15 ft`, no curbs — flush concrete/asphalt alleys!)
# (a) Water Tower South Alley + West Alley + 3000-block East Alley (`alley 8621`, `img_169`, `img_105`)!
ALLEY_8621_W = [(-299.0, -75.2), (-239.0, 144.3), (-175.8, 375.3)]
ALLEY_WT_SOUTH = [(-175.8, 375.3), (118.8, 374.7), (260.7, 374.5), (345.4, 297.2), (506.9, 149.2)]
ALLEY_3000_EAST = [(506.9, 149.2), (359.1, -45.1), (136.6, -337.7), (38.2, -467.1)]
# (b) Central Loop North Alley (`3035` alley, `alley 1882`, `y = 104.5`, `img_113..128`) + N-S link (`alley 1883`)!
ALLEY_NORTH_3035 = [(-239.0, 144.3), (-91.2, 105.7), (169.3, 102.9), (243.0, 41.9), (359.1, -45.1)]
ALLEY_NS_1883 = [(115.6, 227.5), (118.8, 374.7)]
# (c) 3075 / 3060 Left-Side Alley (`img_077`, `img_078`!) + 3003/3001 Rear Alley (`loop_ids_1266.jpg`)!
ALLEY_3075 = [(-38.0, -68.0), (-58.0, -138.0), (-118.0, -162.0), (-165.0, -195.0)]
ALLEY_3075_W = [(-58.0, -138.0), (-145.0, -142.0), (-235.0, -102.0), (-299.0, -75.2)]
# (d) Water Tower West Fence Alley (`alley 3726`) & Pine/30th Alley (`img_130`)!
ALLEY_WT_WEST = [(-175.8, 375.3), (-151.7, 559.2)]
ALLEY_PINE_30TH = [(274.8, -647.7), (355.0, -540.0), (315.0, -250.0), (415.0, -120.0)]

for al_pts in (
    ALLEY_8621_W, ALLEY_WT_SOUTH, ALLEY_3000_EAST, ALLEY_NORTH_3035,
    ALLEY_NS_1883, ALLEY_3075, ALLEY_3075_W, ALLEY_WT_WEST, ALLEY_PINE_30TH,
):
    road_ribbon(al_pts, 15.0, ALLEY, z_bot=-0.2, z_top=0.13, curbs=False)

# 9. Painted White Asphalt Street-Name Stencils (`img_038`, `img_138`, `img_165`)!
road_stencil(-54.0, -344.0, "{sp_rd_spruc", 232.0, w=12.5, d=4.2)
road_stencil(-50.0, -338.0, "{sp_rd_stop", 232.0, w=9.5, d=3.6)
road_stencil(-598.0, -685.0, "{sp_rd_hubb", 40.0, w=13.5, d=4.2)
road_stencil(-512.0, -34.0, "{sp_rd_jac", 225.0, w=14.0, d=4.2)


# ==============================================================================
# STAGE 1C. ANCHOR #1 — THE WATER TOWER (`(-11.57, +473.35) ft`, `img_169`, `img_185`)
# ==============================================================================
WT_X, WT_Y = -11.57, 473.35
WT_METAL = tspec("sp_wt_tank", 12)
WT_TOP = tspec("sp_wt_top", 12)
WT_GREEN = tspec("sp_wt_green", 6)

# 1. Central vertical silver-white standpipe riser (`z = 0 .. 65 ft`, `r = 2.3 ft`) + concrete base pier
frustum_ring(WT_X, WT_Y, 3.6, 3.2, 0.0, 2.2, CONC, sides=12, group="detail", solid=True)
frustum_ring(WT_X, WT_Y, 2.35, 2.35, 2.0, 65.0, WT_METAL, sides=16, group="phong", solid=True)

# 2. 8 Battered Forest-Green Tubular Steel Legs (`r = 21.8 ft` at base -> `20.6 ft` at `z = 75.6 ft`)
N_LEGS = 8
LEG_ANGLES = [math.tau * k / N_LEGS + math.pi / N_LEGS for k in range(N_LEGS)]


def _leg_pos(k, z):
    t = z / 75.6
    r = 21.8 * (1.0 - t) + 20.6 * t
    ang = LEG_ANGLES[k % N_LEGS]
    return (WT_X + r * math.cos(ang), WT_Y + r * math.sin(ang), z)


for k in range(N_LEGS):
    bx, by, _ = _leg_pos(k, 0.0)
    frustum_ring(bx, by, 1.35, 1.10, 0.0, 2.0, CONC, sides=8, group="detail", solid=True)
    strut_3d(_leg_pos(k, 1.8), _leg_pos(k, 75.8), 0.58, WT_GREEN, group="detail", solid=True)

# 3 Tiers of horizontal forest-green ring struts (`z = 24, 46, 64 ft`) + 3 tiers of 3D green diagonal X-bracing rods!
z_tiers = [2.5, 24.0, 46.0, 64.0, 74.8]
for z_ring in (24.0, 46.0, 64.0):
    for k in range(N_LEGS):
        strut_3d(_leg_pos(k, z_ring), _leg_pos(k + 1, z_ring), 0.28, WT_GREEN, group="detail", solid=False)

for ti in range(len(z_tiers) - 1):
    za, zb = z_tiers[ti], z_tiers[ti + 1]
    for k in range(N_LEGS):
        strut_3d(_leg_pos(k, za + 0.4), _leg_pos(k + 1, zb - 0.4), 0.11, WT_GREEN, group="detail", solid=False)
        strut_3d(_leg_pos(k + 1, za + 0.4), _leg_pos(k, zb - 0.4), 0.11, WT_GREEN, group="detail", solid=False)

# 3. Smooth 24-Sided Oblate Toro-Spherical Silver-White Tank (`z = 64.0 .. 101.8 ft`, `_phong 1`, NO lettering!)
SIDES_WT = 24
# Lower curved dish/bowl (`z = 64.0 -> 75.4 ft`)
frustum_ring(WT_X, WT_Y, 3.6, 12.2, 64.0, 67.2, WT_METAL, sides=SIDES_WT, group="phong", solid=True)
frustum_ring(WT_X, WT_Y, 12.2, 17.8, 67.2, 71.2, WT_METAL, sides=SIDES_WT, group="phong", solid=True)
frustum_ring(WT_X, WT_Y, 17.8, 20.6, 71.2, 75.4, WT_METAL, sides=SIDES_WT, group="phong", solid=True)

# Forest-green ring girder collar + walkable projecting steel catwalk balcony (`r = 23.8 ft`, `z = 75.5..76.3 ft`)!
frustum_ring(WT_X, WT_Y, 20.6, 21.0, 74.7, 75.5, WT_GREEN, sides=SIDES_WT, group="detail", solid=True)
frustum_ring(WT_X, WT_Y, 23.8, 23.8, 75.5, 76.3, WT_METAL, side_tex=WT_GREEN, sides=SIDES_WT, group="detail", solid=True)

# 24-sided dark-green X-braced safety handrail around catwalk (`{sp_wtrail`, `z = 76.3 .. 80.0 ft`)
rail_pts = [
    (WT_X + 23.75 * math.cos(math.tau * k / SIDES_WT), WT_Y + 23.75 * math.sin(math.tau * k / SIDES_WT))
    for k in range(SIDES_WT + 1)
]
fence_line(rail_pts, 76.3, 80.0, "{sp_wtrail", thick=0.14, group="illus", fit_len=6.2)

# Cylindrical vertical silver-white belly (`z = 76.3 .. 88.8 ft`, `r = 20.6 ft`)
frustum_ring(WT_X, WT_Y, 20.6, 20.6, 76.3, 88.8, WT_METAL, sides=SIDES_WT, group="phong", solid=True)

# Smooth 5-tier oblate domed crown (`z = 88.8 .. 101.8 ft`, matching wide oblate profile in `img_169` & `img_185`!)
frustum_ring(WT_X, WT_Y, 20.6, 19.0, 88.8, 92.4, WT_METAL, sides=SIDES_WT, group="phong", solid=True)
frustum_ring(WT_X, WT_Y, 19.0, 15.8, 92.4, 95.8, WT_METAL, sides=SIDES_WT, group="phong", solid=True)
frustum_ring(WT_X, WT_Y, 15.8, 11.2, 95.8, 98.6, WT_TOP, sides=SIDES_WT, group="phong", solid=True)
frustum_ring(WT_X, WT_Y, 11.2, 5.6, 98.6, 100.6, WT_TOP, sides=SIDES_WT, group="phong", solid=True)
frustum_ring(WT_X, WT_Y, 5.6, 1.0, 100.6, 101.8, WT_TOP, sides=SIDES_WT, group="phong", solid=True)
frustum_ring(WT_X, WT_Y, 0.55, 0.55, 101.8, 102.8, WT_METAL, sides=10, group="phong", solid=False)
frustum_ring(WT_X, WT_Y, 1.15, 0.35, 102.8, 103.5, WT_METAL, sides=10, group="phong", solid=False)

# Curved exterior steel inspection ladder on WSW profile (`ang = 168 deg`, clearly visible on left edge of tank in `img_169.jpg`!)
lad_ang = math.radians(168.0)
lad_pts = [
    (21.1, 76.3), (21.1, 88.8), (19.5, 92.4), (16.3, 95.8), (11.6, 98.6), (5.8, 100.7),
]
for (r0, z0), (r1, z1) in zip(lad_pts, lad_pts[1:]):
    for side_off in (-0.65, 0.65):
        perp_x, perp_y = -math.sin(lad_ang) * side_off, math.cos(lad_ang) * side_off
        p0 = (WT_X + r0 * math.cos(lad_ang) + perp_x, WT_Y + r0 * math.sin(lad_ang) + perp_y, z0)
        p1 = (WT_X + r1 * math.cos(lad_ang) + perp_x, WT_Y + r1 * math.sin(lad_ang) + perp_y, z1)
        strut_3d(p0, p1, 0.09, WT_GREEN, group="detail", solid=False)

# 4. Water Tower Chain-Link Perimeter Fence, Double Gate, SW Pump Shed & Eucalyptus Ring (`img_169.jpg`!)
# South fence with double vehicle gate (`x = -96..-72`) + pedestrian gate (`x = -72..-65`) + blue sign (`x = -61.5`)
fence_line([(-132.0, 384.5), (-96.0, 384.5)], 0.06, 6.2, "{sp_chain", group="fence", fit_len=2.8)
fence_line([(-96.0, 384.5), (-72.0, 384.5)], 0.15, 6.2, "{sp_chain", group="fence", fit_len=2.8)
fence_line([(-72.0, 384.5), (34.0, 384.5), (34.0, 560.0), (-102.0, 560.0), (-132.0, 384.5)], 0.06, 6.2, "{sp_chain", group="fence", fit_len=2.8)
# Silver steel gate posts along south fence (`img_169.jpg`!)
for gx in (-131.8, -96.0, -84.0, -72.0, -65.0, -52.0, 33.8):
    prop(gx - 0.16, 384.3, 0.06, gx + 0.16, 384.7, 7.2, "sp_wt_tank")
# 3-strand barbed-wire top strand along south fence
strut_3d((-132.0, 384.5, 6.7), (34.0, 384.5, 6.7), 0.05, "sp_wt_tank", group="illus", solid=False)
strut_3d((-132.0, 384.5, 7.1), (34.0, 384.5, 7.1), 0.05, "sp_wt_tank", group="illus", solid=False)
# Blue utility fence warning sign right of gate (`img_169.jpg`!)
box(-62.2, 384.35, 3.5, -60.8, 384.55, 5.1, "sp_wtsign", {"s": Fit("sp_wtsign")}, group="detail", solid=False)

# SW Beige Horizontal-Lap-Siding Pump Shed (`x = -121..-102, y = 387..404`, `img_169.jpg` left!)
shed_wall = tspec("sp_shed_wall", 6)
obox(-111.5, 395.5, 0.06, 7.8, 9.5, 8.5, 270.0, shed_wall, {"front": Fit("sp_shed_s")}, group="detail", solid=True)
ogable(-111.5, 395.5, 7.8, 10.6, 9.5, 8.5, 270.0, tspec("sp_roof_brn", 6), Fit("sp_shed_vent"), eave=0.65)
# Grey/white water main pipe header east of shed (`x = -101..-95, y = 395`)
prop(-101.5, 394.8, 1.4, -95.2, 395.6, 2.2, "sp_wt_tank")
prop(-96.0, 394.8, 0.06, -95.2, 395.6, 2.2, "sp_wt_tank")
# Secondary tan box NW of shed + central-south concrete pad with olive transformer & canopied white control cabinet (`img_169.jpg`!)
prop(-124.5, 410.0, 0.06, -118.0, 416.5, 4.6, shed_wall)
box(-70.0, 416.0, 0.06, -50.0, 428.0, 0.35, CONC, group="detail", solid=True)
prop(-68.5, 418.0, 0.35, -62.5, 423.0, 3.8, shed_wall)
prop(-69.0, 417.6, 3.8, -62.0, 423.4, 4.2, "sp_roof_brn")
prop(-58.5, 419.0, 0.35, -53.5, 424.0, 6.2, "sp_stuc_wht")
prop(-60.5, 417.5, 7.3, -51.5, 425.5, 7.6, "sp_wt_tank")
for cx_p in (-60.2, -51.8):
    for cy_p in (417.8, 425.2):
        prop(cx_p - 0.12, cy_p - 0.12, 0.35, cx_p + 0.12, cy_p + 0.12, 7.3, "sp_wt_tank")

# Tall Eucalyptus Tree Ring framing the Water Tower (`h = 56..62 ft` so white tank & catwalk `z = 75..105` gleam clearly above!)
WT_EUCALYPTUS = [
    (-35.0, 448.0, 58.0, 12.0),
    (-8.0, 442.0, 60.0, 13.0),
    (16.0, 452.0, 59.0, 12.5),
    (22.0, 480.0, 58.0, 12.0),
    (10.0, 505.0, 60.0, 12.5),
    (-20.0, 504.0, 59.0, 12.0),
    (-38.0, 478.0, 57.0, 11.5),
    (-68.0, 462.0, 54.0, 11.5),
    (-92.0, 486.0, 57.0, 12.0),
]
for idx, (ex, ey, eh, er) in enumerate(WT_EUCALYPTUS):
    eucalyptus_tree(ex, ey, h=eh, r_crown=er, seed=500 + idx)


# ==============================================================================
# STAGE 2. ANCHOR HOUSES (3003, 3075/3060, 3013, 3059, 3055, 3058) + ALL GIS HOUSES
# ==============================================================================
if STAGE >= 2:
    # --------------------------------------------------------------------------
    # ANCHOR #2: 3003 SPRUCE ST ("DAVID OJEDA" HOUSE — FULL WALKABLE INTERIOR & BACKYARD, `img2_023`, `img2_032..046`!)
    # --------------------------------------------------------------------------
    from spruce_3003_interior import build_3003_house
    wpt_3003 = build_3003_house(BY_SID, stage=STAGE)

    # --------------------------------------------------------------------------
    # ANCHOR #3: 3075 SPRUCE ST / USER'S SCREENSHOT HOUSE (`*2879`, cx=-81.2, cy=-96.0, facing NE `yaw = 62 deg`, `img_072`, `img_078`!)
    # --------------------------------------------------------------------------
    # Note: NO house number on 3075 or 3003 (`LIMITS — DO NOT INVENT`)!
    c7_x, c7_y, c7_yaw = -81.2, -96.0, 62.0
    r7 = math.radians(c7_yaw)
    v7x, v7y = math.cos(r7), math.sin(r7)       # +V = NNE toward Loop South Road!
    u7x, u7y = math.sin(r7), -math.cos(r7)      # +U = WNW (Wait: check left-to-right when facing NE `62 deg`!)
    # Wait: let's verify `u7x, u7y` when facing the house from the street!
    # House front normal `+V` points `(cos 62, sin 62) = (+0.47, +0.88)` (NNE).
    # Viewer stands in the street (NNE of house) looking SSW (`-V = (-0.47, -0.88)`).
    # Viewer's LEFT is ESE (`+0.88, -0.47` = `+U`? WAIT A SECOND!! CHECK THIS RIGHT NOW!!):
    # Let's check `u = (sin 62, -cos 62) = (+0.88, -0.47)` (ESE)!
    # When viewer looks SSW (`(-0.47, -0.88)`), viewer's RIGHT hand is `forward x up = (-0.47, -0.88, 0) x (0, 0, 1) = (-0.88, +0.47, 0)` (WNW = `-U`!!)
    # WHOA!! STOP AND CHECK THAT CROSS PRODUCT!!
    # Let's check `_default_axes` vs `obox`:
    # In `_default_axes(N)`: `N = (vx, vy, 0) = (cos yaw, sin yaw, 0)`.
    # Viewer looks at face in direction `F = -N = (-vx, -vy, 0)`.
    # Viewer's RIGHT hand is `R = F x (0, 0, 1) = (-vy, vx, 0) = (-sin yaw, cos yaw, 0)`!!
    # Look at `spruce_lib.py` line 183 (`obox`): we wrote `ux, uy = math.sin(rad), -math.cos(rad)` which is **`-R` (viewer's LEFT)**,
    # whereas `_default_axes` line 96 wrote `(-N[1], N[0], 0) = (-sin yaw, cos yaw, 0)` which is **`+R` (viewer's RIGHT)**!
    # WHAT A CATCH BEFORE COMPILING!! Let's check:
    # For `3003` (`yaw = 322`, `N = (+0.79, -0.62)` SE): viewer looks NW `(-0.79, +0.62)`. Viewer's RIGHT hand is NE `(+0.62, +0.79) = (-sin 322, cos 322)`!
    # And for `3075` (`yaw = 62`, `N = (+0.47, +0.88)` NNE): viewer stands on road looking SSW `(-0.47, -0.88)`.
    # Viewer's LEFT is ESE (toward the alley! Look at `img_078.jpg` & `img_072.jpg` — the alley & projecting gable wing are on the **LEFT (ESE)**, and the green door, red-brick steps, white railings, right window, coiled hose, and neighbor `3058` are on the **RIGHT (WNW)**!!).
    # Let `rgt_x, rgt_y = -math.sin(r7), math.cos(r7)` be VIEWER'S RIGHT when facing the house!
    rgt7x, rgt7y = -math.sin(r7), math.cos(r7)  # WNW = viewer's RIGHT when looking at 3075!

    stuc_3075 = tspec("sp_stuc_3075", 10)
    roof_3075 = tspec("sp_roof_grn", 7)

    # Left projecting front-gable wing (viewer's LEFT = `-rgt7`, `w = 18 ft`, `d = 28 ft`, protrudes `+4.5 ft` forward!)
    lg_cx = c7_x - 11.5 * rgt7x + 2.2 * v7x
    lg_cy = c7_y - 11.5 * rgt7y + 2.2 * v7y
    obox(lg_cx, lg_cy, 0.0, 8.5, 6.5, 11.5, c7_yaw, stuc_3075, group="world", solid=True)
    obox(lg_cx, lg_cy, 0.04, 9.2, 9.0, 14.2, c7_yaw, stuc_3075, group="detail", solid=True)
    ogable(lg_cx, lg_cy, 9.2, 13.0, 9.0, 14.2, c7_yaw, roof_3075, stuc_3075, eave=1.1)

    # Main right wing (`w = 25 ft`, `d = 25 ft`, recessed back from left gable by `4.5 ft` -> exact L-plan in `img_072.jpg`!)
    mr_cx = c7_x + 9.0 * rgt7x - 0.2 * v7x
    mr_cy = c7_y + 9.0 * rgt7y - 0.2 * v7y
    obox(mr_cx, mr_cy, 0.0, 8.5, 10.0, 9.5, c7_yaw, stuc_3075, group="world", solid=True)
    obox(mr_cx, mr_cy, 0.04, 9.2, 12.8, 12.2, c7_yaw, stuc_3075, group="detail", solid=True)
    # Main sage-greenish-grey hipped roof over the full house (`img_072.jpg`!) + 2 grey vent pipes on front slope!
    main_poly_3075 = [
        (c7_x - 18.0 * rgt7x - 12.2 * v7x, c7_y - 18.0 * rgt7y - 12.2 * v7y),
        (c7_x - 18.0 * rgt7x + 11.8 * v7x, c7_y - 18.0 * rgt7y + 11.8 * v7y),
        (c7_x + 21.8 * rgt7x + 11.8 * v7x, c7_y + 21.8 * rgt7y + 11.8 * v7y),
        (c7_x + 21.8 * rgt7x - 12.2 * v7x, c7_y + 21.8 * rgt7y - 12.2 * v7y),
    ]
    hiproof(main_poly_3075, 9.2, roof_3075, eave=1.3, pitch=6.0 / 12.0, fascia_tex="sp_stuc_wht")
    for vp_r in (4.5, 9.2):
        vpx = c7_x + vp_r * rgt7x + 5.5 * v7x
        vpy = c7_y + vp_r * rgt7y + 5.5 * v7y
        frustum_ring(vpx, vpy, 0.20, 0.18, 11.8, 14.4, "sp_wt_tank", sides=6, group="detail", solid=False)

    # Twin multi-pane white windows with FOREST-GREEN SHUTTERS on left gable wing (`sp_win_3075l`, `img_072`!)
    obox(lg_cx + 14.35 * v7x, lg_cy + 14.35 * v7y, 3.0, 7.4, 5.6, 0.2, c7_yaw,
         "sp_win_3075l", {"front": Fit("sp_win_3075l")}, group="detail", solid=False)
    # Pinkish-red flowering bush (`{sp_pinkbush`) under left half of twin window + pale green shrub under right half (`img_072`!)
    for p_yaw in (c7_yaw, c7_yaw + 60, c7_yaw + 120):
        obox(lg_cx - 3.6 * rgt7x + 16.2 * v7x, lg_cy - 3.6 * rgt7y + 16.2 * v7y, 0.04, 4.4, 2.8, 0.06, p_yaw,
             "{sp_invis", {"front": Fit("{sp_pinkbush"), "back": Fit("{sp_pinkbush")}, group="illus", solid=False)
    frustum_ring(lg_cx + 3.4 * rgt7x + 15.8 * v7x, lg_cy + 3.4 * rgt7y + 15.8 * v7y, 2.2, 1.8, 0.04, 2.8,
                 tspec("sp_hedge", 3), sides=8, group="detail", solid=True)

    # Dark forest-green 3-pane front door (`sp_door_3075`) + black wall plaque/mailbox on left + 4 red-brick/white-riser steps + WHITE RAILINGS!
    door7_x = c7_x + 4.2 * rgt7x + 12.1 * v7x
    door7_y = c7_y + 4.2 * rgt7y + 12.1 * v7y
    obox(door7_x, door7_y, 1.6, 8.2, 1.85, 0.25, c7_yaw,
         "sp_door_3075", {"front": Fit("sp_door_3075")}, group="detail", solid=False)
    # Black wall plaque/mailbox & sconce left of door (`img_072`!)
    obox(c7_x + 0.5 * rgt7x + 12.25 * v7x, c7_y + 0.5 * rgt7y + 12.25 * v7y, 5.0, 5.7, 1.05, 0.22, c7_yaw,
         "sp_rollup", group="detail", solid=False)
    obox(c7_x + 1.4 * rgt7x + 12.25 * v7x, c7_y + 1.4 * rgt7y + 12.25 * v7y, 6.2, 7.1, 0.35, 0.22, c7_yaw,
         "sp_rollup", group="detail", solid=False)

    # Porch landing + 4 red-brick steps with crisp white risers (`sp_brkstep_w`)!
    obox(c7_x + 4.2 * rgt7x + 13.6 * v7x, c7_y + 4.2 * rgt7y + 13.6 * v7y, 0.04, 1.6, 3.3, 1.5, c7_yaw,
         tspec("sp_redbrk", 4), {"left": "sp_stuc_wht", "right": "sp_stuc_wht"}, group="detail", solid=True)
    for sk in range(4):
        dv = 15.1 + (sk + 0.5) * 0.92
        zt = 1.6 - (sk + 1) * 0.34
        obox(c7_x + 4.2 * rgt7x + dv * v7x, c7_y + 4.2 * rgt7y + dv * v7y, 0.04, max(0.24, zt), 3.3, 0.48, c7_yaw,
             tspec("sp_redbrk", 4),
             {"front": Fit("sp_brkstep_w"), "left": "sp_stuc_wht", "right": "sp_stuc_wht"}, group="detail", solid=True)

    # WHITE wrought-iron handrails (`{sp_rail_w`) on both sides of the red-brick steps (`img_072`!)
    for s_side in (-3.15, 3.15):
        rx = c7_x + (4.2 + s_side) * rgt7x + 15.8 * v7x
        ry = c7_y + (4.2 + s_side) * rgt7y + 15.8 * v7y
        obox(rx, ry, 0.4, 3.9, 0.08, 2.8, c7_yaw, "{sp_invis",
             {"left": Fit("{sp_rail_w"), "right": Fit("{sp_rail_w")}, group="fence", solid=False)

    # Right single multi-pane window with FOREST-GREEN SHUTTERS (`sp_win_grnsh`, `img_072`!)
    win7r_x = c7_x + 14.5 * rgt7x + 12.15 * v7x
    win7r_y = c7_y + 14.5 * rgt7y + 12.15 * v7y
    obox(win7r_x, win7r_y, 3.4, 7.6, 3.4, 0.2, c7_yaw,
         "sp_win_grnsh", {"front": Fit("sp_win_grnsh")}, group="detail", solid=False)

    # Coiled green garden hose (`{sp_hose`) mounted below right window's left shutter + round clipped shrub (`img_072` & `img_078`!)
    obox(c7_x + 12.2 * rgt7x + 12.3 * v7x, c7_y + 12.2 * rgt7y + 12.3 * v7y, 0.5, 2.3, 0.9, 0.06, c7_yaw,
         "{sp_invis", {"front": Fit("{sp_hose")}, group="illus", solid=False)
    frustum_ring(c7_x + 16.5 * rgt7x + 14.2 * v7x, c7_y + 16.5 * rgt7y + 14.2 * v7y, 2.3, 1.9, 0.04, 3.2,
                 tspec("sp_hedge", 3), sides=8, group="detail", solid=True)

    # Concrete front walkway angling slightly right to the loop curb + red-brick accent band (`img_072`, `img_078`!)
    walk_3075 = [
        (c7_x + 4.2 * rgt7x + 18.8 * v7x, c7_y + 4.2 * rgt7y + 18.8 * v7y),
        (c7_x + 9.5 * rgt7x + 31.0 * v7x, c7_y + 9.5 * rgt7y + 31.0 * v7y),
        (c7_x + 14.5 * rgt7x + 45.0 * v7x, c7_y + 14.5 * rgt7y + 45.0 * v7y),
    ]
    road_ribbon(walk_3075, 3.4, CONC, z_bot=0.0, z_top=0.14, curbs=False)
    obox(c7_x + 11.2 * rgt7x + 35.5 * v7x, c7_y + 11.2 * rgt7y + 35.5 * v7y, 0.02, 0.15, 1.7, 1.4, c7_yaw - 14.0,
         tspec("sp_redbrk", 3), group="detail", solid=True)

    # Clipped green hedge + white birdhouse on post + small concrete garden bench along left/ESE alley edge (`img_078.jpg`!)
    hedge_pts_3075 = [
        (c7_x - 22.5 * rgt7x + 46.0 * v7x, c7_y - 22.5 * rgt7y + 46.0 * v7y),
        (c7_x - 22.5 * rgt7x + 18.0 * v7x, c7_y - 22.5 * rgt7y + 18.0 * v7y),
    ]
    fence_line(hedge_pts_3075, 0.04, 3.2, "sp_hedge", thick=2.2, fit_len=4.0)
    # White birdhouse post & concrete bench right behind hedge (`img_078.jpg`!)
    bh_x = c7_x - 21.5 * rgt7x + 18.5 * v7x
    bh_y = c7_y - 21.5 * rgt7y + 18.5 * v7y
    prop(bh_x - 0.18, bh_y - 0.18, 0.04, bh_x + 0.18, bh_y + 0.18, 3.8, "sp_stuc_wht")
    prop(bh_x - 0.55, bh_y - 0.55, 3.8, bh_x + 0.55, bh_y + 0.55, 4.8, "sp_stuc_wht")
    obox(c7_x - 19.2 * rgt7x + 17.5 * v7x, c7_y - 19.2 * rgt7y + 17.5 * v7y, 0.04, 1.5, 0.9, 2.2, c7_yaw, CONC, group="detail", solid=True)

    # Massive branching deciduous shade tree in 3075's front lawn (`z_clear = 9.4 ft`, wide crown framing `img_072` & `img_078`!)
    shade_tree(c7_x - 2.0 * rgt7x + 33.5 * v7x, c7_y - 2.0 * rgt7y + 33.5 * v7y,
               h=36.0, r_crown=16.5, leaf_tex="{sp_leaf", z_clear=9.4, seed=3075)
    BY_SID["done"].add(2879)

    # Next door WNW (`*0769`, 3058 Spruce St: slate-blue stucco, dark roof, white porch rails, US FLAG `img_079`!)
    obox(-137.5, -87.1, 0.04, 9.2, 19.5, 14.0, 65.0, tspec("sp_stuc_blu", 10), group="detail", solid=True)
    for part in convex_parts(BY_SID["map"][769][0]["pts"]):
        hiproof(part, 9.2, tspec("sp_roof_drk", 8), eave=1.3, pitch=4.8 / 12.0)
    obox(-131.5, -73.5, 4.5, 7.2, 0.06, 1.8, 65.0, "{sp_invis",
         {"left": Fit("{sp_usflag"), "right": Fit("{sp_usflag")}, group="illus", solid=False)
    BY_SID["done"].add(769)

    # Across the alley ESE (`*9555`, 3007's tan garage w/ white garage door & basketball hoop, `img_077`!)
    obox(-18.8, -114.1, 0.06, 8.6, 11.0, 10.5, 144.0, tspec("sp_stuc_tan", 8),
         {"front": Fit("sp_gar_wht")}, group="detail", solid=True)
    for part in convex_parts(BY_SID["map"][9555][0]["pts"]):
        hiproof(part, 8.6, tspec("sp_roof_brn", 7), eave=1.0, pitch=4.0 / 12.0)
    # White basketball backboard above garage door facing the alley (`img_077`!)
    obox(-26.8, -108.2, 8.8, 11.2, 2.0, 0.15, 144.0, "sp_stuc_wht", group="detail", solid=False)
    BY_SID["done"].add(9555)

    # Across the Loop road North of 3075: `*9072` (3055 Spruce St, pale mint-green gable house w/ green shutters & chain-link fence, `img_073`!)
    # Note: `*9072` has 2 entries in `spruce_gis.json`; pick the loop one at `cx=21.5, cy=15.1`!
    b_3055 = [b for b in BY_SID["map"][9072] if b["cy"] > -100][0]
    obox(21.5, 15.1, 0.04, 9.2, 19.0, 18.5, 252.0, tspec("sp_stuc_mint", 10), group="detail", solid=True)
    ogable(21.5, 15.1, 9.2, 13.8, 19.0, 18.5, 252.0, tspec("sp_roof_grn", 8), tspec("sp_stuc_mint", 10), eave=1.2)
    obox(15.5, -3.5, 3.2, 7.2, 4.2, 0.2, 252.0, "sp_win_mint", {"front": Fit("sp_win_mint")}, group="detail", solid=False)
    fence_line([(-12.0, -34.0), (35.0, -56.0)], 0.06, 3.8, "{sp_chain", group="fence", fit_len=5.0)
    BY_SID["done"].add(b_3055["id"])

    # --------------------------------------------------------------------------
    # ANCHOR #4A: 3059 SPRUCE ST — EAST FORK HOUSE (`*3666`, cx=79.1, cy=3.7, facing SSW `yaw = 258 deg`, `img_064`!)
    # --------------------------------------------------------------------------
    c59_x, c59_y, c59_yaw = 79.1, 3.7, 258.0
    r59 = math.radians(c59_yaw)
    v59x, v59y = math.cos(r59), math.sin(r59)
    rgt59x, rgt59y = -math.sin(r59), math.cos(r59)
    obox(c59_x, c59_y, 0.0, 8.6, 17.5, 22.0, c59_yaw, tspec("sp_stuc_tan", 10), group="world", solid=True)
    obox(c59_x, c59_y, 0.04, 9.5, 21.0, 26.0, c59_yaw, tspec("sp_stuc_tan", 10), group="detail", solid=True)
    # Red-brick wainscot base + covered front porch overhang + brick porch piers (`img_064`!)
    obox(c59_x + 26.2 * v59x, c59_y + 26.2 * v59y, 0.04, 2.8, 21.1, 0.25, c59_yaw, tspec("sp_redbrk", 5), group="detail", solid=True)
    obox(c59_x + 28.5 * v59x, c59_y + 28.5 * v59y, 8.2, 9.0, 9.5, 2.8, c59_yaw, tspec("sp_roof_brn", 6), group="detail", solid=True)
    for pr_off in (-8.5, 0.0, 8.5):
        obox(c59_x + pr_off * rgt59x + 30.5 * v59x, c59_y + pr_off * rgt59y + 30.5 * v59y, 0.04, 8.2, 0.55, 0.55, c59_yaw,
             tspec("sp_redbrk", 3), group="detail", solid=True)
    obox(c59_x - 3.5 * rgt59x + 26.2 * v59x, c59_y - 3.5 * rgt59y + 26.2 * v59y, 0.2, 7.6, 1.8, 0.2, c59_yaw,
         "sp_door_3003", {"front": Fit("sp_door_3003")}, group="detail", solid=False)
    for off_r in (-14.0, 14.0):
        obox(c59_x + off_r * rgt59x + 26.2 * v59x, c59_y + off_r * rgt59y + 26.2 * v59y, 3.2, 7.6, 3.4, 0.2, c59_yaw,
             "sp_win_dksh", {"front": Fit("sp_win_dksh")}, group="detail", solid=False)
    poly_3059 = [
        (c59_x - 21.0 * rgt59x - 26.0 * v59x, c59_y - 21.0 * rgt59y - 26.0 * v59y),
        (c59_x - 21.0 * rgt59x + 26.0 * v59x, c59_y - 21.0 * rgt59y + 26.0 * v59y),
        (c59_x + 21.0 * rgt59x + 26.0 * v59x, c59_y + 21.0 * rgt59y + 26.0 * v59y),
        (c59_x + 21.0 * rgt59x - 26.0 * v59x, c59_y + 21.0 * rgt59y - 26.0 * v59y),
    ]
    hiproof(poly_3059, 9.5, tspec("sp_roof_brn", 8), eave=1.5, pitch=5.6 / 12.0)
    prop(62.0, 6.0, 13.5, 65.5, 9.5, 16.5, "sp_cooler")
    # Clipped front hedges + long diagonal red-brick walkway to East Junction curb + white Ford pickup (`img_064`!)
    fence_line([(65.0, -24.0), (88.0, -29.0)], 0.04, 3.4, "sp_hedge", thick=2.4, fit_len=4.0)
    road_ribbon([(76.0, -24.0), (92.0, -62.0), (105.0, -98.0)], 3.5, tspec("sp_redbrk", 4), z_bot=0.0, z_top=0.14, curbs=False)
    brush_vehicle(62.0, -78.0, 152.0, "sp_stuc_wht", kind="pickup", z0=0.12)
    BY_SID["done"].add(3666)

    # --------------------------------------------------------------------------
    # ANCHOR #4B: 3013 SPRUCE ST (`*2063`, cx=125.5, cy=13.3, facing SE `yaw = 322 deg` onto SE Loop arm, `img_081`, `img_088`!)
    # --------------------------------------------------------------------------
    c13_x, c13_y, c13_yaw = 125.5, 13.3, 322.0
    r13 = math.radians(c13_yaw)
    v13x, v13y = math.cos(r13), math.sin(r13)
    rgt13x, rgt13y = -math.sin(r13), math.cos(r13)
    obox(c13_x, c13_y, 0.0, 8.6, 16.5, 13.0, c13_yaw, tspec("sp_stuc_crm", 10), group="world", solid=True)
    obox(c13_x, c13_y, 0.04, 9.4, 20.0, 16.5, c13_yaw, tspec("sp_stuc_crm", 10), group="detail", solid=True)
    for part in convex_parts(BY_SID["map"][2063][0]["pts"]):
        hiproof(part, 9.4, tspec("sp_roof_drk", 8), eave=1.4, pitch=5.2 / 12.0)
    ogable(c13_x + 1.5 * rgt13x + 10.0 * v13x, c13_y + 1.5 * rgt13y + 10.0 * v13y,
           9.2, 13.2, 7.5, 8.0, c13_yaw, tspec("sp_roof_drk", 8), tspec("sp_stuc_crm", 10), eave=1.0)

    # Dark BLUE front door (`sp_door_3013`) + DARK shutters (`sp_win_dksh`) + brick steps + DARK METAL railings (`{sp_rail_dk`)!
    obox(c13_x + 1.0 * rgt13x + 16.65 * v13x, c13_y + 1.0 * rgt13y + 16.65 * v13y, 1.5, 8.1, 1.85, 0.25, c13_yaw,
         "sp_door_3013", {"front": Fit("sp_door_3013")}, group="detail", solid=False)
    for off_r in (-10.5, 11.0):
        obox(c13_x + off_r * rgt13x + 16.65 * v13x, c13_y + off_r * rgt13y + 16.65 * v13y, 3.2, 7.5, 3.4, 0.2, c13_yaw,
             "sp_win_dksh", {"front": Fit("sp_win_dksh")}, group="detail", solid=False)
    for sk in range(3):
        dv = 17.2 + sk * 1.0
        obox(c13_x + 1.0 * rgt13x + dv * v13x, c13_y + 1.0 * rgt13y + dv * v13y, 0.04, 1.5 - sk * 0.42, 3.0, 0.55, c13_yaw,
             tspec("sp_redbrk", 4), group="detail", solid=True)
    for s_side in (-2.9, 2.9):
        obox(c13_x + (1.0 + s_side) * rgt13x + 18.2 * v13x, c13_y + (1.0 + s_side) * rgt13y + 18.2 * v13y,
             0.4, 3.8, 0.08, 2.2, c13_yaw, "{sp_invis",
             {"left": Fit("{sp_rail_dk"), "right": Fit("{sp_rail_dk")}, group="fence", solid=False)

    # Giant 46-ft Deodar Cedar evergreen tree + white lifted Toyota 4Runner SUV RIGHT AT THE NW CURB of `LOOP_EAST` (`img_081`!)
    cedar_tree(142.0, -8.0, h=46.0, r_base=14.5)
    brush_vehicle(159.5, -45.0, 232.0, "sp_stuc_wht", kind="suv_4runner", z0=0.12)
    fence_line([(112.0, -9.0), (124.0, -18.0)], 0.1, 5.5, "sp_redfnc", fit_len=6.0)
    BY_SID["done"].add(2063)


# ==============================================================================
# STAGE 3 PRE-PASS (Marks custom Stage-3 buildings before auto-GIS pass!)
# ==============================================================================
if STAGE >= 3:
    build_stage3(BY_SID)


# ==============================================================================
# STAGE 2B. ALL REMAINING REAL GIS NEIGHBORHOOD HOUSES & REAR ALLEY GARAGES
# ==============================================================================
if STAGE >= 2:
    STUC_PAL = [
        tspec("sp_stuc_crm", 10),
        tspec("sp_stuc_tan", 10),
        tspec("sp_stuc_wht", 10),
        tspec("sp_stuc_gry", 10),
        tspec("sp_stuc_3075", 10),
        tspec("sp_stuc_blu", 10),
    ]
    for b in GIS["buildings"]:
        if b["sid"] in BY_SID["done"] or b["id"] in BY_SID["done"]:
            continue
        cx, cy = b["cx"], b["cy"]
        if not (HX0 + 25.0 <= cx <= HX1 - 25.0 and HY0 + 25.0 <= cy <= HY1 - 25.0):
            continue
        pts = b["pts"]
        parts = convex_parts(pts)
        if not parts:
            continue

        area = b["area"]
        r_sat, g_sat, b_sat = b["rgb"]
        h_rng = random.Random(b["id"])

        # Pick roof color directly from real calibrated satellite RGB!
        lum = (r_sat + g_sat + b_sat) / 3.0
        if lum > 172:
            rtex = tspec("sp_roof_lt", 8)
        elif lum < 82:
            rtex = tspec("sp_roof_drk", 8)
        elif g_sat > r_sat + 10:
            rtex = tspec("sp_roof_grn", 8)
        elif r_sat > b_sat + 12:
            rtex = tspec("sp_roof_brn", 8)
        else:
            rtex = tspec("sp_roof_tan", 8)

        wtex = STUC_PAL[b["id"] % len(STUC_PAL)]
        is_garage = area < 780.0
        is_comm = area > 7500.0
        z_wall = 8.4 if is_garage else (18.5 if is_comm else (9.4 if area < 3400 else 11.2))

        for part in parts:
            # Polygon-aligned inner VIS-blocker core shrunk inward by 2.8 ft so rotated house walls NEVER poke!
            if not is_garage and len(part) >= 4:
                inner = offset_convex(part, -2.8)
                prism(inner, 0.0, z_wall - 0.8, wtex, side=wtex, group="world", solid=True)
            prism(part, 0.04, z_wall, rtex, side=wtex, group="detail", solid=True)
            if not is_comm:
                hiproof(part, z_wall, rtex, eave=(0.8 if is_garage else 1.25), pitch=(4.4 / 12 if is_garage else 5.2 / 12))

        # Add garage doors on rear alley garages (`area < 780`) facing the nearest alley!
        if is_garage:
            gyaw = b["angle"] + 90.0
            # Point toward nearest alley (`y=105`, `y=375`, or `3000-block east alley`)
            if 60 <= cy <= 145:
                gyaw = 90.0 if cy < 105 else 270.0
            elif 330 <= cy <= 382:
                gyaw = 90.0
            rad_g = math.radians(gyaw)
            obox(cx + 8.5 * math.cos(rad_g), cy + 8.5 * math.sin(rad_g), 0.12, 7.2, 6.8, 0.35, gyaw,
                 "sp_gar_wht", {"front": Fit("sp_gar_rib" if (b["id"] % 2) else "sp_gar_wht")}, group="detail", solid=False)
        elif not is_comm:
            # Add rooftop evaporative swamp cooler or solar panels on selected loop houses (matching aerials!)
            if b["id"] % 3 == 0:
                prop(cx - 1.5, cy - 1.5, z_wall + 3.0, cx + 1.5, cy + 1.5, z_wall + 5.6, "sp_cooler")
            if STAGE >= 3 and b["sid"] in (4924, 3743, 4012, 9146, 1726):
                osloped_panel(cx, cy - 3.0, z_wall + 0.8, z_wall + 3.2, 9.0, 4.0, b["angle"] - 90.0, Fit("sp_solar", (2.0, 1.0)))


# ==============================================================================
# GAMEPLAY ENTITIES, WATER TOWER JUMP PAD & GALLERY AUDIT CAMERA SPOTS
# ==============================================================================
# Discreet jump pad at base of Water Tower riser (`(-11.6, 467.0)`) launching players up onto the `z = 76.3 ft` catwalk!
prop(WT_X - 2.2, WT_Y - 7.5, 0.06, WT_X + 2.2, WT_Y - 3.5, 0.45, "sp_wt_green")
brush_ent("trigger_push", WT_X - 2.2, WT_Y - 7.5, 0.45, WT_X + 2.2, WT_Y - 3.5, 4.5, angles="-82 90 0", speed="1320")

# Player Start (`SPRUCE_START="x y z yaw"` override for `view_spruce.sh`!)
if os.environ.get("SPRUCE_START"):
    _vals = [float(v) for v in os.environ["SPRUCE_START"].split()]
    ent("info_player_start", _vals[0], _vals[1], _vals[2], angle=int(round(_vals[3])))
else:
    # Default spawn: right on Spruce St in front of 3003 Spruce St looking NW at the Hero House!
    ent("info_player_start", -22.0, -264.0, 2.5, angle=137)

if STAGE >= 3:
    _liv_x, _liv_y = wpt_3003(1.5, 8.2)
    _pat_x, _pat_y = wpt_3003(14.0, -26.0)
    _pat2_x, _pat2_y = wpt_3003(11.0, -28.0)
    DM_SPAWNS = [
        (-22.0, -264.0, 2.5, 137),      # 3003 Spruce St Hero Front
        (_liv_x, _liv_y, 3.75, 52),     # Inside 3003 Spruce St ("David Ojeda" House Living Room!)
        (-62.0, -42.0, 2.5, 242),       # 3075 Spruce St (User Screenshot House)
        (172.0, -54.0, 2.5, 115),       # 3013 Spruce St & Giant Cedar
        (88.0, -96.0, 2.5, 90),         # 3059 East Junction Fork
        (-112.0, 18.0, 2.5, 82),        # 3054 West Loop looking N at Water Tower
        (242.0, 42.0, 2.5, 95),         # 3018 NE Arm Picket Fence
        (110.0, 104.5, 2.5, 92),        # 3035 North Alley Bins & Solar Roofs
        (-104.0, 374.5, 2.5, 45),       # Water Tower South Alley Gate
        (WT_X, WT_Y - 22.3, 78.8, 270), # High atop the Water Tower 76-ft Catwalk!
        (128.0, 616.0, 2.5, 225),       # Westchester Apts NE Parking Lot
        (468.0, -485.0, 2.5, 88),       # CITYSERVE Main Hub Lot
        (-502.0, -18.0, 2.5, 135),      # Jacaranda Dr 3037/3036
    ]
    for sx, sy, sz, sang in DM_SPAWNS:
        ent("info_player_deathmatch", sx, sy, sz, angle=sang)

    # Active in BOTH Single-Player & Deathmatch in installed `maps/spruce.bsp` (so player can grab RL & blow up cars!);
    # hidden only during `SPRUCE_CLEAN_SHOTS=1` reference photo screenshot comparisons.
    _clean_shots = os.environ.get("SPRUCE_CLEAN_SHOTS") == "1"
    _item_sf = {"spawnflags": 1792} if _clean_shots else {}
    ITEMS = [
        ("weapon_rocketlauncher", _pat_x, _pat_y, 1.5),         # Rocket Launcher on 3003 Spruce St Backyard Patio!
        ("item_rockets", _pat2_x, _pat2_y, 1.5),                # Rockets on 3003 Backyard Patio!
        ("weapon_rocketlauncher", WT_X, WT_Y + 22.3, 77.5),     # Rocket Launcher on Water Tower Catwalk!
        ("weapon_lightning", -76.0, 405.0, 1.5),                # Inside Water Tower Gravel Compound
        ("weapon_supernailgun", 88.0, -82.0, 1.5),              # East Loop Fork (3059)
        ("weapon_grenadelauncher", 108.0, 104.5, 1.5),          # 3035 North Alley
        ("weapon_supershotgun", -14.0, -258.0, 1.5),            # 3003 Spruce St Street Curb
        ("weapon_nailgun", 495.0, -385.0, 1.5),                 # CITYSERVE Apron
        ("item_armor2", -66.0, -52.0, 1.8),                     # Yellow Armor (Jetpack!) outside 3075 Spruce St!
        ("item_armor2", -88.0, 374.5, 1.8),                     # Yellow Armor (Jetpack!) outside Water Tower Gate!
        ("item_armorInv", 525.0, -370.0, 1.8),                  # Red Armor at CITYSERVE Main Hub
        ("item_armor1", -495.0, -8.0, 1.8),                     # Green Armor on Jacaranda Dr
        ("item_health", -28.0, -275.0, 1.5),
        ("item_health", -55.0, -38.0, 1.5),
        ("item_health", 176.0, -46.0, 1.5),
        ("item_health", 136.0, 622.0, 1.5),
        ("item_shells", -18.0, -272.0, 1.5),
        ("item_spikes", 122.0, 104.5, 1.5),
        ("item_rockets", -82.0, 420.0, 1.5),
        ("item_cells", 482.0, -385.0, 1.5),
    ]
    for iname, ix, iy, iz in ITEMS:
        ent(iname, ix, iy, iz, **_item_sf)
    ent("item_health", WT_X + 22.3, WT_Y, 77.5, spawnflags=(1794 if _clean_shots else 2))

# 24 Gallery-Matched Audit / Viewer Camera Spots (16 Neighborhood + 8 Inside/Backyard of 3003 Spruce St!)
_s_kit1 = wpt_3003(14.5, -11.5) if STAGE >= 2 else (-57.5, -230.3)
_s_kit2 = wpt_3003(14.5, -3.2) if STAGE >= 2 else (-57.5, -230.3)
_s_kit5 = wpt_3003(15.8, -12.8) if STAGE >= 2 else (-57.5, -230.3)
_s_liv1 = wpt_3003(-0.3, 11.8) if STAGE >= 2 else (-57.5, -230.3)
_s_bed1 = wpt_3003(-0.3, -4.5) if STAGE >= 2 else (-57.5, -230.3)
_s_bath = wpt_3003(-7.1, -7.8) if STAGE >= 2 else (-57.5, -230.3)
_s_byd1 = wpt_3003(11.5, -18.5) if STAGE >= 2 else (-57.5, -230.3)
_s_byd2 = wpt_3003(-14.5, -45.0) if STAGE >= 2 else (-57.5, -230.3)

SPOTS = [
    ("01 Water Tower South Hero (img_169)", -124.0, 369.5, 2.5, 42),
    ("02 Water Tower NE Westchester Lot (img_185)", 128.0, 616.0, 2.5, 225),
    ("03 3003 Spruce St Hero Front (img_023)", -21.0, -264.0, 2.5, 137),
    ("04 3075 Spruce St User Screenshot Lawn (img_072)", -66.5, -62.0, 2.2, 242),
    ("05 3075 Spruce St Road & Alley View (img_078)", -36.0, -52.0, 2.5, 222),
    ("06 3013 Spruce St & Giant Cedar (img_081)", 144.0, -82.0, 2.5, 64),
    ("07 3059 Loop East Fork Brick Walk (img_064)", 86.0, -92.0, 2.5, 92),
    ("08 3054 West Loop Looking N at Tower (img_089)", -114.0, 12.0, 2.5, 85),
    ("09 3018 NE Arm White Picket Fence (img_097)", 224.0, 62.0, 2.5, 98),
    ("10 North Alley 3035 Bins & Solar (img_113)", 110.0, 102.5, 2.2, 92),
    ("11 3000-Block Rear Alley (img_105)", 197.5, -252.0, 2.2, 52),
    ("12 Pine-30th Green Fence & Dock (img_130)", 344.0, -206.0, 2.5, 45),
    ("13 CITYSERVE Main Hub & Lot (img_145)", 468.0, -485.0, 2.5, 88),
    ("14 Jacaranda Dr Yellow Garage & Solar (img_168)", -496.0, -12.0, 2.5, 138),
    ("15 Jacaranda Dr Looking NE at Tower (img_162)", -505.0, -24.0, 2.5, 45),
    ("16 Spruce & Beech Autumn Tree (img_039)", -48.0, -304.0, 2.5, 135),
    ("17 3003 Kitchen Wide Toward Living (img2_032)", _s_kit1[0], _s_kit1[1], 3.75, 322),
    ("18 3003 Kitchen Sink & Sheer Curtains (img2_034)", _s_kit2[0], _s_kit2[1], 3.75, 142),
    ("19 3003 Kitchen Stove & Vestibule (img2_036)", _s_kit5[0], _s_kit5[1], 3.75, 268),
    ("20 3003 Carpeted Living Room & Blinds (img2_037)", _s_liv1[0], _s_liv1[1], 3.75, 28),
    ("21 3003 Bedroom 1 Twin Windows & Bench (img2_039)", _s_bed1[0], _s_bed1[1], 3.75, 136),
    ("22 3003 Turquoise Bathroom & Curtain (img2_042)", _s_bath[0], _s_bath[1], 3.75, 142),
    ("23 3003 Backyard Patio & Outbuildings (img2_045)", _s_byd1[0], _s_byd1[1], 3.5, 152),
    ("24 3003 Backyard Rear Facade (img2_046)", _s_byd2[0], _s_byd2[1], 2.5, 352),
]

os.makedirs(os.path.dirname(os.path.abspath(OUT_MAP)), exist_ok=True)
spots_path = os.path.splitext(os.path.abspath(OUT_MAP))[0] + ".spots.json"
with open(spots_path, "w", encoding="utf-8") as sf:
    json.dump([{"name": s[0], "pos": [ui(s[1], OX), ui(s[2], OY), ui(s[3])], "yaw": s[4]} for s in SPOTS], sf, indent=2)

wad_str = ";".join(WADS)
with open(OUT_MAP, "w", encoding="utf-8") as f:
    f.write('{\n"classname" "worldspawn"\n')
    f.write('"mapversion" "220"\n')
    f.write(f'"wad" "{wad_str}"\n')
    f.write('"message" "Spruce St & Westchester Water Tower - Bakersfield, CA 93301"\n')
    f.write('"skyname" "bklan_"\n')
    # Balanced sunny Bakersfield daylight (calibrated for DarkPlaces r_hdr_scenebrightness 2.5 — crisp shadows, zero whiteout!)
    f.write(
        '"_minlight" "28"\n"_minlight_color" "255 246 232"\n'
        '"_sunlight" "118"\n"_sunlight_mangle" "115 -52 0"\n'
        '"_sunlight_color" "1 0.94 0.82"\n'
        '"_sunlight2" "65"\n"_sunlight2_color" "0.64 0.82 1"\n'
        '"_sunlight_penumbra" "1.5"\n'
        '"_dirt" "1"\n"_dirtscale" "0.7"\n'
    )
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    if GROUPS["detail"]:
        f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    if GROUPS["phong"]:
        f.write('{\n"classname" "func_detail"\n"_phong" "1"\n"_phong_angle" "89"\n"_minlight" "62"\n"_minlight_color" "245 248 255"\n' + "".join(GROUPS["phong"]) + "}\n")
    if GROUPS["fence"]:
        f.write('{\n"classname" "func_wall"\n"_shadow" "0"\n"_minlight" "58"\n' + "".join(GROUPS["fence"]) + "}\n")
    if GROUPS["illus"]:
        f.write('{\n"classname" "func_detail_illusionary"\n"_shadow" "0"\n"_minlight" "96"\n"_minlight_color" "240 248 225"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))

if check_placed():
    sys.exit("ERROR: spawns or items blocked by solid brushes!")

print(
    f"wrote {OUT_MAP} (stage={STAGE}): {len(GROUPS['world'])} world + {len(GROUPS['detail'])} detail + "
    f"{len(GROUPS['fence'])} fence + {len(GROUPS['illus'])} illus brushes, {len(ENTS)} entities"
)
