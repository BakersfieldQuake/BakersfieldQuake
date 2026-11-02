"""make_gallup.py — Generates `out/maps/gallup.map` + `out/maps/gallup.spots.json`:
A smooth, VIS-optimized 1:1 scale (12 Quake units = 1 foot) Quake map replica of
**7705 Gallup Dr, Bakersfield, CA 93309** (Laurelglen neighborhood), its surrounding
streets/intersections, and its three anchor landmarks (Laurelwood Gardens / West Villas,
Crossway Baptist Church, and Albertsons Shopping Plaza), complete with a network of
parabolic Jump Pads, Jetpacks, drivable/explodable vehicles, and the Pink Supercar loop!

Strict source adherence:
  - 7705 front facade built from the 2026 GEMLS/CRMLS listing photo (`img_011.jpg`).
  - 7705 interior built strictly from the MLS listing description (vaulted living/dining
    ceiling, brick fireplace, open oak kitchen, primary suite w/ walk-in closet, private bath
    & direct backyard patio access, 3BR/2BA, Feb 2025 Carrier HVAC).
  - Zero invented house numbers on residential homes other than `7705` (landmark numbers
    `3200` on Crossway's sign base and `7900` on Albertsons' portico come directly from photos).
  - Zero stray `"Baum Haus"` labels anywhere.
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gallup_lib import (  # noqa: E402
    ENTS,
    Fit,
    GIS,
    GROUPS,
    OX,
    OY,
    PADS,
    WADS,
    box,
    brush_vehicle,
    cedar_tree,
    check_placed,
    convex_parts,
    cul_de_sac_disc,
    ent,
    fence_line,
    fire_hydrant,
    hiproof,
    jump_pad,
    light,
    obox,
    ogable,
    osloped_panel,
    palm_tree,
    prism,
    prop,
    road_ribbon,
    road_stencil,
    shade_tree,
    smooth_curve,
    stop_sign,
    street_blade_pole,
    street_lamp,
    tspec,
    ui,
    vis_core_box,
)
from gallup_7705 import build_7705_and_neighbors, wpt_7705  # noqa: E402

OUT_MAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "maps", "gallup.map")

BY_SID = {"map": {}, "done": set()}
for _b in GIS["buildings"]:
    BY_SID["map"].setdefault(_b["sid"], []).append(_b)

# ==============================================================================
# 1. SEALED WORLD HULL + DEAD-CORNER VIS/LIGHTMAP OPTIMIZATION BLOCKS
# ==============================================================================
HX0, HX1, HY0, HY1, SKY_Z = -1530.0, 960.0, -1650.0, 1320.0, 290.0

LAWN = tspec("sp_lawn", 16)
DRYLAWN = tspec("sp_drylawn", 16)
ASPH = tspec("sp_asphalt", 18)
ALLEY = tspec("sp_alley", 14)
CONC = tspec("sp_conc", 8)
BLOCK_TAN = tspec("ga_block_tan", 8, 6)

# Sealed outer skybox + solid lawn base (`z = -4 .. 0`, 100% axial worldspawn!)
box(HX0 - 4, HY0 - 4, -6.0, HX1 + 4, HY1 + 4, -4.0, "sp_alley", group="world", solid=False)
box(HX0, HY0, -4.0, HX1, HY1, 0.0, LAWN, group="world", solid=False)
box(HX0 - 4, HY0 - 4, SKY_Z, HX1 + 4, HY1 + 4, SKY_Z + 4, "sky_bk", group="world", solid=False)
box(HX0 - 4, HY0 - 4, -4.0, HX0, HY1 + 4, SKY_Z, "sky_bk", group="world", solid=False)
box(HX1, HY0 - 4, -4.0, HX1 + 4, HY1 + 4, SKY_Z, "sky_bk", group="world", solid=False)
box(HX0, HY0 - 4, -4.0, HX1, HY0, SKY_Z, "sky_bk", group="world", solid=False)
box(HX0, HY1, -4.0, HX1, HY1 + 4, SKY_Z, "sky_bk", group="world", solid=False)
for cx0, cy0, cx1, cy1 in (
    (HX0, HY0, HX0 + 4, HY1),
    (HX1 - 4, HY0, HX1, HY1),
    (HX0, HY0, HX1, HY0 + 4),
    (HX0, HY1 - 4, HX1, HY1),
):
    box(cx0, cy0, 0.0, cx1, cy1, SKY_Z, "clip", group="world", solid=False)

# Dead-corner worldspawn sky blocks (culls >35% of unseen subdivision void for ultra-fast VIS & light.exe!):
#   1) NE corner (`x = 530..960, y = 490..1320`)
#   2) SE east corner (`x = 480..960, y = -1650..-310`)
#   3) SE south corner (`x = -360..480, y = -1650..-1040`)
DEAD_BOXES = [
    (530.0, 490.0, HX1, HY1),
    (480.0, HY0, HX1, -310.0),
    (-360.0, HY0, 480.0, -1040.0),
]
for dx0, dy0, dx1, dy1 in DEAD_BOXES:
    box(dx0, dy0, 0.0, dx1, dy1, SKY_Z, "sky_bk", group="world", solid=True)

# Realistic 6.5-ft Laurelglen tan slump-stone perimeter sound walls framing map & dead-corner boundaries
fence_line([(-1518, -1638), (-362, -1638), (-362, -1038), (478, -1038), (478, -308), (948, -308), (948, 488), (528, 488), (528, 1308), (-1518, 1308), (-1518, -1638)],
           0.0, 6.5, "ga_block_tan", thick=0.6)


def _in_dead_zone(x, y, pad=8.0):
    if not (HX0 + 18.0 <= x <= HX1 - 18.0 and HY0 + 18.0 <= y <= HY1 - 18.0):
        return True
    return any(dx0 - pad <= x <= dx1 + pad and dy0 - pad <= y <= dy1 + pad for dx0, dy0, dx1, dy1 in DEAD_BOXES)


# ==============================================================================
# 2. GPS-CALIBRATED LAURELGLEN STREET & ALLEY NETWORK + STENCILS + STREET SIGNS
# ==============================================================================
# Gallup Drive (`width = 34 ft`, smooth 4.3-unit curbs & concrete sidewalks right past 7705!)
GALLUP_DR = smooth_curve([
    (-974.1, 30.7), (-694.5, 30.3), (-414.7, 30.0), (-209.1, 30.0),
    (-156.4, 35.0), (-112.0, 44.5), (-68.8, 58.3), (-27.4, 76.8),
    (12.0, 99.3), (71.3, 141.3), (189.5, 227.4), (341.6, 338.0),
], 2)
road_ribbon(GALLUP_DR, 34.0, ASPH, curbs=True, sidewalks=True, sw_w=4.6)

# Deming Court (`width = 32 ft`, Kandarian -> Gallup -> South Cul-de-sac bulb!)
DEMING_CT = [
    (-182.9, 554.5), (31.6, 199.0), (71.3, 141.3), (107.9, 93.5),
    (168.7, 23.1), (217.3, -27.0), (270.3, -76.0), (324.3, -120.6), (398.0, -175.0),
]
road_ribbon(DEMING_CT, 32.0, ASPH, curbs=True, sidewalks=True, sw_w=4.5)
cul_de_sac_disc(406.8, -181.9, 44.0, ASPH, sides=16, curbs=True)
# Concrete utility manhole diamond patches in Deming Ct cul-de-sac (`img_062.jpg`!)
for mx, my in ((395.0, -174.0), (412.0, -188.0)):
    obox(mx, my, 0.02, 0.13, 2.2, 2.2, 45.0, CONC, solid=False)

# Olympia Drive (`width = 48 ft`, double-yellow center line `{ga_dbl_yel` + sidewalks, `img_067..096`!)
OLYMPIA_DR = [
    (-74.1, 1023.2), (40.9, 831.5), (187.5, 587.2), (341.6, 338.0),
    (431.2, 231.7), (534.9, 138.8), (650.6, 61.2), (787.6, -4.1), (925.0, -45.0),
]
road_ribbon(OLYMPIA_DR, 48.0, ASPH, curbs=True, sidewalks=True, sw_w=5.0, center_stripe="{ga_dbl_yel")

# Litchfield Drive -> Prescott Way & Sonoita Drive (`img_045..055`)
LITCHFIELD_DR = [
    (-414.7, 30.0), (-415.9, -446.4), (-433.2, -536.0),
    (-473.1, -617.6), (-533.0, -686.5), (-651.0, -791.0),
]
PRESCOTT_WAY = [(-533.0, -686.5), (-347.7, -895.5)]
SONOITA_DR = [
    (-135.2, -243.9), (-136.1, -454.3), (-165.0, -615.8),
    (-212.7, -726.4), (-272.3, -816.0), (-347.7, -895.5), (-500.0, -1028.0),
]
road_ribbon(LITCHFIELD_DR, 32.0, ASPH, curbs=True, sidewalks=True, sw_w=4.4)
road_ribbon(PRESCOTT_WAY, 32.0, ASPH, curbs=True, sidewalks=True, sw_w=4.4)
road_ribbon(SONOITA_DR, 30.0, ASPH, curbs=True, sidewalks=False)

# Secondary Laurelglen loop streets (Flagstaff Way, Kandarian Way, Sedona Way, Seligman Dr, Ouray Way, Denver Way)
road_ribbon([(-694.5, 30.3), (-694.0, 424.7), (-693.7, 606.8), (-711.2, 799.4)], 32.0, ASPH, curbs=True)
road_ribbon([(-694.0, 424.7), (-551.2, 447.2), (-387.0, 485.6), (-182.9, 554.5)], 32.0, ASPH, curbs=True)
road_ribbon([(-974.1, 30.7), (-974.4, -245.7), (-995.2, -344.8), (-1089.7, -459.4), (-732.1, -862.5), (-651.0, -791.0)], 30.0, ASPH, curbs=True)
road_ribbon([(-1460.0, -106.8), (-1258.0, -108.6), (-1258.3, -269.7), (-1089.7, -459.4)], 30.0, ASPH, curbs=True)
road_ribbon([(187.5, 587.2), (389.2, 711.3), (475.1, 817.2)], 32.0, ASPH, curbs=True)
road_ribbon([(787.6, -4.1), (866.3, 197.9)], 30.0, ASPH, curbs=True)

# South Laurelglen Blvd (North arterial connecting Olympia Dr <-> Gosford Rd / Crossway Church!)
S_LAURELGLEN = [
    (-1462.0, 785.2), (-1008.0, 783.5), (-711.2, 799.4), (-566.1, 825.9),
    (-395.7, 874.5), (-231.2, 940.2), (-74.1, 1023.2), (81.1, 1129.5),
]
road_ribbon(S_LAURELGLEN, 46.0, ASPH, curbs=True, sidewalks=True, sw_w=5.0, center_stripe="{ga_dbl_yel")

# Gosford Road (Major western N-S arterial `x = -1462`, connecting Crossway Baptist Church <-> Albertsons!)
GOSFORD_RD = [(-1462.0, -1630.0), (-1462.0, -1080.0), (-1462.0, -106.0), (-1462.0, 785.2), (-1462.0, 1295.0)]
road_ribbon(GOSFORD_RD, 62.0, ASPH, curbs=True, sidewalks=True, sw_w=5.5, center_stripe="{ga_dbl_yel")

# Rear Service Alley behind Laurelwood Gardens (`img_031..036`, crossing Gallup Dr at `(189.5, 227.4)`!)
ALLEY_LAURELWOOD = [(-128.0, 746.8), (-77.9, 666.9), (88.9, 386.5), (189.5, 227.4), (258.4, 141.7), (310.7, 89.8), (396.0, 8.9)]
road_ribbon(ALLEY_LAURELWOOD, 18.0, ALLEY, z_bot=-0.2, z_top=0.11, curbs=False)

# Painted White Street-Name Stencils on Asphalt
road_stencil(44.0, 122.0, "{ga_rd_gal", 125.0, w=12.5, d=4.2)
road_stencil(302.0, 309.0, "{ga_rd_gal", 126.0, w=12.5, d=4.2)
road_stencil(94.0, 112.0, "{ga_rd_dem", 38.0, w=12.5, d=4.2)
road_stencil(-415.0, -8.0, "{ga_rd_lit", 0.0, w=13.5, d=4.2)
road_stencil(316.0, 378.0, "{ga_rd_oly", 32.0, w=13.5, d=4.4)

# Green Reflective Intersection Street Signs & Stop Signs (`img_045`, `img_056`, `img_067`)
street_blade_pole(92.0, 134.0, [("ga_sgn_gal", 125.0, 4.2), ("ga_sgn_dem33", 35.0, 4.8)])
stop_sign(92.0, 126.0, 215.0)
street_blade_pole(-394.0, 10.0, [("ga_sgn_gal", 90.0, 4.2), ("ga_sgn_litch", 0.0, 4.8)])
stop_sign(-396.0, 4.0, 90.0)
street_blade_pole(-512.0, -692.0, [("ga_sgn_litch", 45.0, 4.8), ("ga_sgn_presc", 135.0, 4.8)])
street_blade_pole(306.0, 344.0, [("ga_sgn_gal", 126.0, 4.2), ("ga_sgn_oly", 32.0, 4.4)])
stop_sign(302.0, 336.0, 306.0)


# ==============================================================================
# 3. CENTERPIECE: 7705 GALLUP DR (`sid=2410`) + IMMEDIATE NEIGHBORS
# ==============================================================================
HERO_INFO = build_7705_and_neighbors(BY_SID)


# ==============================================================================
# 4. LANDMARK #1: LAURELWOOD GARDENS / WEST VILLAS (`7601 Olympia Dr`, `img_067, 089, 031`)
# ==============================================================================
LAURELWOOD_BLDGS = (2464, 6712, 4993, 7494, 7688, 4228, 3909, 6412, 4969)
LAURELWOOD_CARPORTS = (3371, 3569, 6057, 2729)
APT_STUC = tspec("ga_stuc_apt", 10)
APT_SIDING = tspec("ga_siding_apt", 8)
APT_ROOF = tspec("ga_roof_drk", 9)

for sid in LAURELWOOD_BLDGS:
    BY_SID["done"].add(sid)
    for b in BY_SID["map"].get(sid, []):
        for part in convex_parts(b["pts"]):
            vis_core_box(part, 18.2, APT_STUC, margin=2.4)
            prism(part, 0.0, 19.5, APT_ROOF, side=APT_SIDING, group="detail", solid=True)
            hiproof(part, 19.5, APT_ROOF, eave=1.4, pitch=4.2 / 12.0, fascia_tex="ga_trim_brn")
        # Rooftop HVAC package units visible on Laurelwood 2-storey roofs (`img_067.jpg`!)
        obox(b["cx"], b["cy"], 22.8, 25.4, 2.2, 2.2, 30.0, "sp_cooler")

for sid in LAURELWOOD_CARPORTS:
    BY_SID["done"].add(sid)
    for b in BY_SID["map"].get(sid, []):
        for part in convex_parts(b["pts"]):
            prism(part, 0.0, 9.0, APT_ROOF, side=APT_STUC, group="detail", solid=True)

# Gallup & Olympia SW Corner Monument Sign, Stucco Arch, Boulders, Cobra Lamp & Giant Redwoods (`img_067.jpg`!)
obox(268.0, 332.0, -0.04, 0.12, 34.0, 26.0, 122.0, LAWN, solid=False)
# Monument sign #1 at Gallup & Olympia (`img_067.jpg`)
obox(290.0, 338.0, 0.0, 1.5, 4.4, 0.85, 78.0, APT_STUC)
obox(290.0, 338.0, 1.5, 4.8, 4.2, 0.65, 78.0, APT_STUC,
     faces={"front": Fit("ga_apt_sign"), "back": Fit("ga_apt_sign")})
# Decorative cream stucco entry arch pier behind sign (`img_067.jpg`)
obox(276.0, 334.0, 0.0, 7.6, 1.1, 3.6, 122.0, APT_STUC)
# Landscape boulders (`img_067.jpg`)
for bx_, by_ in ((285.0, 326.0), (298.0, 348.0)):
    obox(bx_, by_, 0.0, 1.6, 1.5, 1.2, 35.0, "ga_stuc_gry")
street_lamp(302.0, 348.0, arm_yaw=55.0, h=22.0, cobra=True)
cedar_tree(282.0, 366.0, h=46.0, r_base=12.5)
cedar_tree(218.0, 278.0, h=48.0, r_base=13.0)
palm_tree(252.0, 346.0, h=44.0)

# Monument sign #2 along Olympia Dr (`img_089.jpg`)
obox(158.0, 568.0, 0.0, 1.5, 4.4, 0.85, 32.0, APT_STUC)
obox(158.0, 568.0, 1.5, 4.8, 4.2, 0.65, 32.0, APT_STUC,
     faces={"front": Fit("ga_apt_sign"), "back": Fit("ga_apt_sign")})
cedar_tree(142.0, 588.0, h=45.0, r_base=12.5)

# Rear Alley White Cinderblock Dumpster Enclosures (`img_031.jpg`)
for ax, ay in ((152.0, 286.0), (96.0, 382.0)):
    obox(ax, ay, 0.0, 5.8, 5.5, 4.5, 122.0, tspec("ga_block_wht", 8, 6))
    obox(ax, ay, 0.1, 4.2, 3.4, 2.4, 122.0, "ga_roof_drk")


# ==============================================================================
# 5. LANDMARK #2: CROSSWAY BAPTIST CHURCH (`3200 Gosford Rd`, NW Landmark, `img_118, 119`)
# ==============================================================================
CHURCH_SIDS = (3790, 3994, 7171)
box(-1428.0, 960.0, -0.04, -1210.0, 1285.0, 0.11, LAWN, group="detail", solid=False)
box(-1360.0, 960.0, -0.02, -1205.0, 1020.0, 0.12, ASPH, group="detail", solid=False)

for sid in CHURCH_SIDS:
    BY_SID["done"].add(sid)
    for b in BY_SID["map"].get(sid, []):
        z_ch = 16.5 if sid in (3790, 3994) else 12.5
        for part in convex_parts(b["pts"]):
            vis_core_box(part, z_ch - 1.0, "ga_stuc_wht", margin=2.2)
            prism(part, 0.0, z_ch, tspec("ga_roof_gry", 10), side=tspec("ga_stuc_wht", 10), group="detail", solid=True)
            hiproof(part, z_ch, tspec("ga_roof_gry", 10), eave=1.3, pitch=3.2 / 12.0, fascia_tex="ga_stuc_wht")

# Wrought-iron fence + red-tipped photinia hedge stretching along Gosford Rd (`img_118.jpg`!)
fence_line([(-1392.0, 985.0), (-1392.0, 1126.0)], 0.0, 6.2, "ga_photinia", thick=1.8)

# Blue `CROSSWAY BAPTIST CHURCH` Monument Sign (`ga_cross_sgn`) on `3200` Concrete Base (`ga_base_3200`) (`img_118.jpg`!)
prop(-1406.0, 1130.0, 0.0, -1394.0, 1134.0, 1.8, "sp_conc",
     faces={"w": Fit("ga_base_3200"), "s": Fit("ga_base_3200")})
prop(-1405.5, 1130.5, 1.8, -1394.5, 1133.5, 6.0, "ga_stuc_wht",
     faces={"s": Fit("ga_cross_sgn"), "n": Fit("ga_cross_sgn"), "w": "ga_stuc_wht"})

# `SPEED LIMIT 55` Sign (`ga_spd55`, vertical 1.8x2.4 ft), Fire Hydrant & Tall Pines along Gosford Rd (`img_118.jpg`!)
obox(-1423.0, 1146.0, 0.0, 8.6, 0.12, 0.12, 270.0, "ga_stuc_gry")
obox(-1423.0, 1146.0, 6.2, 8.6, 0.90, 0.08, 270.0, "ga_stuc_gry",
     faces={"front": Fit("ga_spd55"), "back": "ga_stuc_gry"}, solid=False)
fire_hydrant(-1412.0, 1148.0)
for py_c in (1185.0, 1222.0, 1255.0):
    cedar_tree(-1404.0, py_c, h=44.0, r_base=12.0)
shade_tree(-1406.0, 1160.0, h=30.0, r_crown=9.5, leaf_tex="{ga_olive", z_clear=9.5)


# ==============================================================================
# 6. LANDMARK #3: ALBERTSONS SHOPPING PLAZA (`7900 White Ln` & Gosford Rd, SW Landmark, `img_125, 127`)
# ==============================================================================
PLAZA_SIDS = (3295, 7718, 6330, 8417)
for sid in PLAZA_SIDS:
    BY_SID["done"].add(sid)

# Expansive Asphalt Shopping Center Parking Lot (`x = -1425 .. -560, y = -1635 .. -900`)
prism([(-1425.0, -1635.0), (-560.0, -1635.0), (-560.0, -1380.0), (-920.0, -905.0), (-1425.0, -905.0)],
      -0.06, 0.10, ASPH, group="detail", solid=False)

# Main `Albertsons` Supermarket Building (`sid=3295`, `yaw = 221.4 deg` facing SW parking lot!)
ALB_YAW = 221.4
_arad = math.radians(ALB_YAW)
_avx, _avy = math.cos(_arad), math.sin(_arad)
_aux, _auy = math.sin(_arad), -math.cos(_arad)
ALB_CX, ALB_CY = -975.0, -1235.0


def p_alb(uu, vv):
    return (ALB_CX + uu * _aux + vv * _avx, ALB_CY + uu * _auy + vv * _avy)


# Main supermarket hull (`280 ft` wide storefront x `130 ft` deep, `z = 0 .. 22.0 ft`) + axial VIS core
vis_core_box([p_alb(-135, -62), p_alb(135, -62), p_alb(135, 62), p_alb(-135, 62)], 20.5, "ga_stuc_crm", margin=4.0)
obox(ALB_CX, ALB_CY, 0.0, 22.0, 138.0, 64.0, ALB_YAW, tspec("ga_stuc_crm", 12),
     faces={"t": tspec("ga_roof_gry", 14)})

# Wide storefront concrete walkway + Red Fire-Lane Curb (`ga_curb_red`, `img_125.jpg`!)
obox(*p_alb(0.0, 72.0), -0.02, 0.36, 144.0, 8.0, ALB_YAW, CONC, solid=False)
obox(*p_alb(0.0, 80.4), -0.02, 0.38, 144.0, 0.65, ALB_YAW, tspec("ga_curb_red", 6), solid=False)

# Towering 33-ft Gabled `Albertsons` Entry Pediment (`img_125.jpg`!)
obox(*p_alb(-28.0, 66.5), 0.0, 26.5, 24.0, 4.5, ALB_YAW, tspec("ga_stuc_crm", 10),
     faces={"front": Fit("ga_alb_logo")})
ogable(*p_alb(-28.0, 66.5), 26.5, 33.0, 25.0, 5.2, ALB_YAW, tspec("ga_alb_tile", 8), tspec("ga_stuc_crm", 10), eave=1.2)

# Storefront Glass Windows (`ga_alb_win`: Oreo display & `Shop happy` posters!) + Spanish Red-Clay Tile Mansard (`img_125.jpg`)
for wu in (22.0, 74.0):
    obox(*p_alb(wu, 64.4), 0.36, 3.2, 22.0, 0.6, ALB_YAW, "ga_trim_brn")
    obox(*p_alb(wu, 64.3), 3.2, 11.4, 22.0, 0.5, ALB_YAW, "ga_stuc_crm",
         faces={"front": Fit("ga_alb_win", (2.0, 1.0))})
    osloped_panel(*p_alb(wu, 67.2), 11.6, 15.8, 24.0, 3.4, ALB_YAW, tspec("ga_alb_tile", 6),
                  thick=0.45, edge_tex="ga_trim_brn", group="detail", solid=False)

# Recessed `7900` Corner Portico (`img_127.jpg`) with Ice Chest & Blue Glacier Water Dispenser!
obox(*p_alb(94.0, 69.0), 0.36, 22.0, 2.2, 2.2, ALB_YAW, tspec("ga_stuc_crm", 8))    # Inner portico pier
obox(*p_alb(114.0, 69.0), 0.36, 22.0, 2.2, 2.2, ALB_YAW, tspec("ga_stuc_crm", 8))   # Corner colonnade column
obox(*p_alb(104.0, 69.0), 11.5, 22.0, 8.0, 2.0, ALB_YAW, tspec("ga_stuc_crm", 8),
     faces={"front": Fit("ga_port_7900")})                                          # `7900` Portico lintel (`img_127.jpg`)
obox(*p_alb(101.0, 64.8), 0.36, 6.2, 3.2, 1.4, ALB_YAW, "ga_stuc_wht")              # White Ice Chest (`img_127.jpg`)
obox(*p_alb(108.5, 64.8), 0.36, 7.0, 1.8, 1.5, ALB_YAW, "sp_bin_blu")               # Blue Water Machine (`img_127.jpg`)

# Parking Lot Palm Planter Islands (`img_127.jpg`) + Wells Fargo (`sid=7718`), Shell (`6330`), & North Pad (`8417`)
for pu, pv in ((-70.0, 115.0), (-15.0, 115.0), (45.0, 115.0), (105.0, 115.0), (-45.0, 175.0), (35.0, 175.0)):
    px_, py_ = p_alb(pu, pv)
    obox(px_, py_, 0.0, 0.38, 5.5, 5.5, ALB_YAW, CONC, faces={"t": DRYLAWN}, solid=False)
    palm_tree(px_, py_, h=40.0)

for sid, z_pad, rtex_p in ((7718, 16.5, "ga_alb_tile"), (6330, 15.5, "ga_roof_gry"), (8417, 16.0, "ga_alb_tile")):
    for b in BY_SID["map"].get(sid, []):
        for part in convex_parts(b["pts"]):
            if sid != 6330:
                vis_core_box(part, z_pad - 1.0, "ga_stuc_crm", margin=2.2)
            prism(part, (11.5 if sid == 6330 else 0.0), z_pad, tspec(rtex_p, 8), side=tspec("ga_stuc_crm", 10), group="detail", solid=True)
            if sid != 6330:
                hiproof(part, z_pad, tspec(rtex_p, 8), eave=1.1, pitch=3.8 / 12.0, fascia_tex="ga_trim_brn")
# Shell gas canopy support columns (`sid=6330`)
for scx, scy in ((-1320.0, -1535.0), (-1296.0, -1535.0), (-1320.0, -1608.0), (-1296.0, -1608.0)):
    prop(scx - 0.8, scy - 0.8, 0.0, scx + 0.8, scy + 0.8, 11.6, "ga_stuc_wht")


# ==============================================================================
# 7. ALL REMAINING REAL GIS CORRIDOR HOUSES (WITH AXIAL VIS CORES & SOLAR!)
# ==============================================================================
STUC_PAL = [
    tspec("ga_stuc_crm", 10),
    tspec("ga_stuc_tan", 10),
    tspec("ga_stuc_7705", 10),
    tspec("ga_stuc_wht", 10),
    tspec("ga_stuc_sage", 10),
    tspec("ga_stuc_gry", 10),
]
SOLAR_SIDS = {5765, 5573, 4901, 7339, 5144, 3321, 3130, 4115, 4328, 2874, 6097}

for b in GIS["buildings"]:
    if b["sid"] in BY_SID["done"] or b["id"] in BY_SID["done"]:
        continue
    if any(_in_dead_zone(p[0], p[1], pad=6.0) for p in b["pts"]):
        continue
    if math.hypot(b["cx"] - (-810.0), b["cy"] - 540.0) < 42.0 or math.hypot(b["cx"] - (-685.0), b["cy"] - (-560.0)) < 42.0:
        continue
    parts = convex_parts(b["pts"])
    if not parts:
        continue

    area = b["area"]
    r_sat, g_sat, b_sat = b["rgb"]
    lum = (r_sat + g_sat + b_sat) / 3.0
    if lum < 88:
        rtex = tspec("ga_roof_drk", 8)
    elif r_sat > b_sat + 14:
        rtex = tspec("ga_roof_terra", 8)
    elif lum > 158:
        rtex = tspec("ga_roof_7705", 8)
    elif b_sat > r_sat + 12:
        rtex = tspec("ga_roof_gry", 8)
    else:
        rtex = tspec("ga_roof_brn", 8)

    wtex = STUC_PAL[b["id"] % len(STUC_PAL)]
    is_small = area < 800.0
    is_two_storey = area > 4600.0
    z_wall = 8.5 if is_small else (17.5 if is_two_storey else 9.4)

    for part in parts:
        if not is_small:
            vis_core_box(part, z_wall - 0.8, wtex, margin=2.2)
        prism(part, 0.0, z_wall, rtex, side=wtex, group="detail", solid=True)
        hiproof(part, z_wall, rtex, eave=(0.85 if is_small else 1.2), pitch=4.6 / 12.0, fascia_tex="ga_trim_brn")

    if b["sid"] in SOLAR_SIDS:
        osloped_panel(b["cx"], b["cy"], z_wall + 1.0, z_wall + 3.4, 8.5, 3.8, b["angle"] - 90.0, Fit("sp_solar", (2.0, 1.0)))

# Neighborhood street trees & ornamental blossoms along Gallup, Deming, Litchfield & Olympia (`img_045..090`)
TREE_SPOTS = [
    (-108.0, 18.0, "{ga_blossom", 22.0),
    (-185.0, 6.0, "{sp_leaf", 28.0),
    (-265.0, 62.0, "{ga_jacar", 26.0),
    (-345.0, 6.0, "{sp_leaf", 29.0),
    (-448.0, -85.0, "{ga_olive", 25.0),
    (-448.0, -245.0, "{sp_leaf", 30.0),
    (-495.0, -645.0, "{ga_blossom", 23.0),
    (138.0, 65.0, "{sp_leaf", 28.0),
    (245.0, -45.0, "{ga_olive", 26.0),
    (355.0, -198.0, "{sp_leaf", 30.0),
    (438.0, -225.0, "{sp_leaf", 28.0),
    (112.0, 232.0, "{sp_leaf", 31.0),
    (392.0, 298.0, "{sp_leaf", 32.0),
    (-240.0, 528.0, "{ga_jacar", 27.0),
    (-580.0, 418.0, "{sp_leaf", 29.0),
]
for tx, ty, ltex, th in TREE_SPOTS:
    shade_tree(tx, ty, h=th, r_crown=9.5, leaf_tex=ltex, z_clear=9.5)

for lx, ly, lyaw in (
    (-195.0, 52.0, 270.0),
    (-434.0, -180.0, 0.0),
    (212.0, 10.0, 225.0),
    (448.0, -182.0, 180.0),
):
    street_lamp(lx, ly, arm_yaw=lyaw, h=16.0, cobra=False)


# ==============================================================================
# 8. ELEVATED SKYWAY RELAY PLATFORMS + PARABOLIC JUMP PAD NETWORK!
# ==============================================================================
# Elevated Relay Perch #1 (NW Skyway between Gallup Dr & Crossway Baptist Church, `(-810, 540, z=22 ft)`)
RELAY_NW = (-810.0, 540.0)
prop(RELAY_NW[0] - 14.0, RELAY_NW[1] - 14.0, 0.0, RELAY_NW[0] + 14.0, RELAY_NW[1] + 14.0, 22.0,
     BLOCK_TAN, faces={"t": CONC})
prop(RELAY_NW[0] - 14.6, RELAY_NW[1] - 14.6, 21.4, RELAY_NW[0] + 14.6, RELAY_NW[1] + 14.6, 22.1, "ga_trim_brn",
     faces={"t": CONC})

# Elevated Relay Perch #2 (SW Skyway between Gallup Dr & Albertsons Plaza, `(-685, -560, z=20 ft)`)
RELAY_SW = (-685.0, -560.0)
prop(RELAY_SW[0] - 14.0, RELAY_SW[1] - 14.0, 0.0, RELAY_SW[0] + 14.0, RELAY_SW[1] + 14.0, 20.0,
     BLOCK_TAN, faces={"t": CONC})
prop(RELAY_SW[0] - 14.6, RELAY_SW[1] - 14.6, 19.4, RELAY_SW[0] + 14.6, RELAY_SW[1] + 14.6, 20.1, "ga_trim_brn",
     faces={"t": CONC})

rf7705 = HERO_INFO["roof_7705"]

# --- Neighborhood Rooftop & Tactical Jump Pads ---
# 4) 7705 Roof East Edge -> Laurelwood Gardens 2-Storey Apartment Roof (`sid=2464`, `z = 24.5 ft`)!
rf_east_x, rf_east_y = wpt_7705(24.0, 12.0)
jump_pad(rf_east_x, rf_east_y, 12.2, target=(208.0, 344.0, 25.0), over=38.0, size=5.2)

# 5) Laurelwood Gardens 2-Storey Roof -> 7705 Vaulted Roof Ridge!
jump_pad(196.0, 332.0, 24.5, target=rf7705, over=38.0, size=5.6)

# 6) Gallup & Olympia 165-ft VERTICAL SKY JETPACK PAD (`sky=True`, launches straight up over the whole neighborhood!)
jump_pad(304.0, 322.0, 0.14, target=None, apex=165.0, size=6.6, sky=True)

# 7 & 8) Gallup & Deming <-> Deming Ct Cul-de-Sac Two-Way Express Pads!
jump_pad(96.0, 148.0, 0.14, target=(392.0, -168.0, 1.0), over=42.0, size=6.0)
jump_pad(416.0, -192.0, 0.14, target=(63.0, 25.0, 14.5), over=42.0, size=6.0)

# 9 & 10) Gallup & Litchfield <-> Prescott Way / Sonoita Fork Two-Way Pads!
jump_pad(-398.0, -16.0, 0.14, target=(-516.0, -672.0, 1.0), over=58.0, size=6.0)
jump_pad(-538.0, -698.0, 0.14, target=(-398.0, 28.0, 1.0), over=62.0, size=6.0)

# --- Express 2-Hop Aerial Skyway #1: Gallup Dr <-> Crossway Baptist Church (`3200 Gosford Rd`) ---
jump_pad(-432.0, 52.0, 0.14, target=(RELAY_NW[0], RELAY_NW[1] - 4.0, 22.5), over=58.0, size=6.4, sky=True)
jump_pad(RELAY_NW[0] - 6.0, RELAY_NW[1] + 6.0, 22.1, target=(-1410.0, 1118.0, 1.0), over=72.0, size=6.2, sky=True)
jump_pad(-1414.0, 1096.0, 0.14, target=(RELAY_NW[0], RELAY_NW[1] + 4.0, 22.5), over=78.0, size=6.4, sky=True)
jump_pad(RELAY_NW[0] + 6.0, RELAY_NW[1] - 6.0, 22.1, target=(-382.0, 36.0, 1.0), over=56.0, size=6.2, sky=True)

# --- Express 2-Hop Aerial Skyway #2: Gallup Dr <-> Albertsons Shopping Plaza (`7900 White Ln`) ---
alb_land_x, alb_land_y = p_alb(-28.0, 96.0)
alb_pad_x, alb_pad_y = p_alb(-48.0, 96.0)
alb_roof_pad_x, alb_roof_pad_y = p_alb(4.0, 88.0)

jump_pad(-432.0, 8.0, 0.14, target=(RELAY_SW[0], RELAY_SW[1] + 4.0, 20.5), over=58.0, size=6.4, sky=True)
jump_pad(RELAY_SW[0] - 6.0, RELAY_SW[1] - 6.0, 20.1, target=(alb_land_x, alb_land_y, 1.0), over=72.0, size=6.2, sky=True)
jump_pad(alb_pad_x, alb_pad_y, 0.14, target=(RELAY_SW[0], RELAY_SW[1] - 4.0, 20.5), over=76.0, size=6.4, sky=True)
jump_pad(RELAY_SW[0] + 6.0, RELAY_SW[1] + 6.0, 20.1, target=(-382.0, 18.0, 1.0), over=56.0, size=6.2, sky=True)

# 19) Albertsons Storefront -> Albertsons 22-ft Supermarket Roof!
jump_pad(alb_roof_pad_x, alb_roof_pad_y, 0.14, target=(ALB_CX, ALB_CY, 22.8), over=18.0, size=5.8)


# ==============================================================================
# 9. FUN GAMEPLAY ENTITIES: PINK SUPERCAR LOOP, EXPLODING TRASHCANS, VEHICLES, JETPACKS & DM!
# ==============================================================================
_clean_shots = os.environ.get("GALLUP_CLEAN_SHOTS") == "1"

# Destructible & Drivable 3D Vehicles (`misc_vehicle_*`, `van` is drivable with H!)
VEHICLES = [
    (-76.0, 44.0, 24.0, "coupe"),          # Red sport coupe on Gallup Dr near 7709
    (128.0, 168.0, 36.0, "pickup"),        # Blue 4x4 pickup on East Gallup Dr
    (378.0, -162.0, 135.0, "sedan"),       # Green sedan in Deming Ct cul-de-sac
    (-465.0, -762.0, 315.0, "van"),        # Drivable white van / camper on Prescott Way (`img_048`)!
    (215.0, 505.0, 120.0, "sedan"),        # Sedan on Olympia Dr outside Laurelwood
    (-1325.0, 992.0, 0.0, "sedan"),        # Sedan in Crossway Baptist Church parking lot
    (*p_alb(-55.0, 138.0), 41.0, "van"),   # Drivable white cargo van in Albertsons Plaza!
    (*p_alb(15.0, 142.0), 221.0, "pickup"),
    (*p_alb(75.0, 138.0), 41.0, "coupe"),
]
if not _clean_shots:
    for vx_, vy_, vyaw, vkind in VEHICLES:
        brush_vehicle(vx_, vy_, vyaw, kind=vkind)

    # Hot-Pink Music-Playing Supercar (`bk_cruiser`, `cnt=1` — hop on top right outside 7705 Gallup Dr!)
    PINK_ROUTE = [
        ("ga_r0", -385.0, 30.0, 1.0),
        ("ga_r1", -145.0, 37.0, 1.0),
        ("ga_r2", -12.0, 86.0, 0.85),      # Cruises right past 7705 Gallup Dr!
        ("ga_r3", 71.0, 141.0, 0.85),      # Turns NW onto Deming Ct
        ("ga_r4", -183.0, 554.0, 1.0),     # Turns W onto Kandarian Way
        ("ga_r5", -694.0, 425.0, 1.0),     # Turns S onto Flagstaff Way
        ("ga_r6", -694.0, 30.0, 1.0),      # Turns E onto Gallup Dr
    ]
    for idx, (rname, rx, ry, rspd) in enumerate(PINK_ROUTE):
        nxt = PINK_ROUTE[(idx + 1) % len(PINK_ROUTE)][0]
        ent("bk_route", rx, ry, 1.2, targetname=rname, target=nxt, speed=rspd)
    ent("bk_cruiser", -240.0, 30.0, 1.2, cnt=1, target="ga_r1")

    # Shootable Rocket-Launching Exploding Trash Cans (`bk_trashcan`)!
    for tcx, tcy in (
        (164.0, 272.0),                    # Laurelwood rear dumpster alley
        (108.0, 368.0),                    # Laurelwood alley north
        (434.0, -168.0),                   # Deming Ct cul-de-sac
        (-1384.0, 1095.0),                 # Crossway Campus
        p_alb(92.0, 72.0),                 # Albertsons storefront
    ):
        ent("bk_trashcan", tcx, tcy, 0.4)

# Player Start (`GALLUP_START="x y z yaw"` override for `view_gallup.sh`!)
if os.environ.get("GALLUP_START"):
    _vals = [float(v) for v in os.environ["GALLUP_START"].split()]
    ent("info_player_start", _vals[0], _vals[1], _vals[2], angle=int(round(_vals[3])))
else:
    # Default spawn: on Gallup Dr looking SSE straight at the 7705 Gallup Dr Hero House!
    _st_x, _st_y = wpt_7705(6.0, 74.0)
    ent("info_player_start", _st_x, _st_y, 2.5, angle=292)

# 14 Deathmatch Spawns across 7705 (front, interior, backyard), intersections, rooftops & landmarks!
_liv_sp = wpt_7705(-4.0, 12.0)
_byd_sp = wpt_7705(2.0, -54.0)
_drv_sp = wpt_7705(21.0, 48.0)
_alb_sp = p_alb(-12.0, 108.0)

DM_SPAWNS = [
    (_drv_sp[0], _drv_sp[1], 2.5, 292),          # 7705 Front Driveway
    (_liv_sp[0], _liv_sp[1], 2.8, 112),          # Inside 7705 Vaulted Living Room!
    (_byd_sp[0], _byd_sp[1], 2.5, 112),          # 7705 Backyard Patio
    (72.0, 118.0, 2.5, 220),                     # Gallup & Deming Intersection
    (388.0, -198.0, 2.5, 135),                   # Deming Ct Cul-de-Sac
    (284.0, 308.0, 2.5, 65),                     # Gallup & Olympia / Laurelwood Gardens
    (212.0, 348.0, 26.5, 235),                   # Atop Laurelwood Gardens 2-Storey Roof!
    (175.0, 212.0, 2.5, 125),                    # Rear Apartment Alley & Fence (`img_035`)
    (-382.0, 46.0, 2.5, 180),                    # Gallup & Litchfield Hub
    (-505.0, -678.0, 2.5, 315),                  # Litchfield & Prescott Fork
    (RELAY_NW[0], RELAY_NW[1], 24.5, 135),       # NW Skyway Perch
    (RELAY_SW[0], RELAY_SW[1], 22.5, 225),       # SW Skyway Perch
    (-1412.0, 1138.0, 2.5, 20),                  # Crossway Baptist Church (`3200 Gosford`)
    (_alb_sp[0], _alb_sp[1], 2.5, 41),           # Albertsons Shopping Plaza (`7900`)
]
for sx, sy, sz, sang in DM_SPAWNS:
    ent("info_player_deathmatch", sx, sy, sz, angle=sang)

# Weapons, Jetpacks (`item_armor2`), Quad Damage, Armor, Health & Ammo!
_item_sf = {"spawnflags": 1792} if _clean_shots else {}
_pat_rl = wpt_7705(-2.0, -52.0)
_kit_am = wpt_7705(8.0, 4.0)
_drv_sg = wpt_7705(18.0, 38.0)
_pool_lg = HERO_INFO["pool"]

ITEMS = [
    ("weapon_rocketlauncher", _pat_rl[0], _pat_rl[1], 1.6),     # Rocket Launcher on 7705 Backyard Patio!
    ("weapon_supershotgun", _drv_sg[0], _drv_sg[1], 1.6),       # Super Shotgun on 7705 Front Driveway!
    ("weapon_lightning", _pool_lg[0], _pool_lg[1], 1.8),        # Lightning Gun in 7701's Turquoise Pool!
    ("weapon_rocketlauncher", 214.0, 352.0, 25.5),              # Rocket Launcher on Laurelwood 2-Storey Roof!
    ("weapon_grenadelauncher", 168.0, 232.0, 1.6),              # Grenade Launcher at Rear Apartment Alley!
    ("weapon_supernailgun", 406.0, -182.0, 1.6),                # Super Nailgun in Center of Deming Cul-de-Sac!
    ("weapon_nailgun", -415.0, -120.0, 1.6),                    # Nailgun on Litchfield Dr
    ("weapon_rocketlauncher", ALB_CX, ALB_CY, 23.6),            # Rocket Launcher on Albertsons Roof!
    ("item_armor2", 58.0, 112.0, 1.8),                          # Yellow Armor (JETPACK!) at Gallup & Deming near 7705!
    ("item_armor2", 292.0, 316.0, 1.8),                         # Yellow Armor (JETPACK!) right beside 165-ft Sky Pad!
    ("item_armor2", *p_alb(-8.0, 92.0), 1.8),                   # Yellow Armor (JETPACK!) at Albertsons Storefront!
    ("item_armorInv", -1410.0, 1126.0, 1.8),                    # Red Armor beside Crossway `3200` Sign!
    ("item_armor1", -412.0, 18.0, 1.8),                         # Green Armor at Gallup & Litchfield
    ("item_artifact_super_damage", RELAY_NW[0], RELAY_NW[1], 23.8),  # QUAD DAMAGE on NW Skyway Perch!
    ("item_rockets", _kit_am[0], _kit_am[1], 1.8),              # Rockets inside 7705 Open Kitchen!
    ("item_rockets", RELAY_SW[0], RELAY_SW[1], 21.8),
    ("item_cells", 82.0, 118.0, 1.6),
    ("item_spikes", 392.0, -188.0, 1.6),
    ("item_shells", 272.0, 318.0, 1.6),
    ("item_health", _liv_sp[0], _liv_sp[1] + 5.0, 1.8),
    ("item_health", 298.0, 304.0, 1.6),
    ("item_health", -1414.0, 1110.0, 1.6),
    ("item_health", *p_alb(25.0, 92.0), 1.6),
]
for iname, ix, iy, iz in ITEMS:
    ent(iname, ix, iy, iz, **_item_sf)

# Mega Health right on top of 7705 Gallup Dr's Vaulted Gable Roof Ridge!
ent("item_health", rf7705[0], rf7705[1], rf7705[2] + 0.8, spawnflags=(1794 if _clean_shots else 2))

# ==============================================================================
# 10. GALLERY-MATCHED AUDIT / SCREENSHOT SPOTS & MAP FILE OUTPUT
# ==============================================================================
_s_hero = wpt_7705(8.0, 78.0)       # Standing on Gallup Dr looking straight at 7705 (`img_011.jpg`)!
_s_7701 = (38.0, 98.0)              # Looking SSE at 7701 + 7705 dual mailboxes (`img_016.jpg`)!
_s_int1 = wpt_7705(2.2, 18.2)       # Foyer looking into Vaulted Living Room + Brick Fireplace!
_s_int2 = wpt_7705(-7.0, 14.0)      # Living Room looking across breakfast bar into Open Oak Kitchen!
_s_byd1 = wpt_7705(4.0, -75.0)      # Backyard looking NNW at 7705 Rear Facade, Patio, Carrier HVAC & Jump Pad!
_s_roof = wpt_7705(-8.0, 14.0)      # On 7705's Roof Ridge overlooking Gallup Dr & Jump Pads!
_s_alb1 = p_alb(-32.0, 122.0)       # Looking at Albertsons Pediment + Oreo Windows + Red Curb (`img_125.jpg`)!
_s_alb2 = p_alb(92.0, 92.0)         # Looking at Albertsons `7900` Portico + Ice/Water + Palms (`img_127.jpg`)!

SPOTS = [
    ("01 7705 Gallup Dr Hero Front (img_011)", _s_hero[0], _s_hero[1], 3.0, 292),
    ("02 7701 & 7705 Gallup Dr Mailboxes (img_016)", _s_7701[0], _s_7701[1], 2.8, 294),
    ("03 7705 Interior Vaulted Living & Brick Fireplace", _s_int1[0], _s_int1[1], 2.8, 232),
    ("04 7705 Interior Open Kitchen & Oak Cabinets", _s_int2[0], _s_int2[1], 2.8, 347),
    ("05 7705 Backyard Patio, HVAC & Pool Jump Pad", _s_byd1[0], _s_byd1[1], 2.8, 112),
    ("06 7705 Rooftop Ridge & Laurelwood Jump Pad", _s_roof[0], _s_roof[1], 15.0, 48),
    ("07 Gallup & Deming Corner Hydrant & Flag (img_058)", 106.0, 114.0, 2.8, 232),
    ("08 Rear Apartment Alley & Wood Fence (img_035)", 214.0, 198.0, 2.8, 232),
    ("09 Laurelwood Gardens Sign at Gallup & Olympia (img_067)", 328.0, 318.0, 2.8, 135),
    ("10 Crossway Baptist Church & 3200 Sign (img_118)", -1440.0, 1102.0, 2.8, 52),
    ("11 Albertsons Pediment & Storefront (img_125)", _s_alb1[0], _s_alb1[1], 2.8, 52),
    ("12 Albertsons 7900 Portico & Palms (img_127)", _s_alb2[0], _s_alb2[1], 2.8, 70),
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
    f.write('"message" "7705 Gallup Dr & Laurelglen - Bakersfield, CA 93309"\n')
    f.write('"skyname" "bklan_"\n')
    # Sunny Bakersfield daylight calibrated for DarkPlaces r_hdr_scenebrightness 2.5 (crisp shadows, zero whiteout!)
    f.write(
        '"_minlight" "30"\n"_minlight_color" "255 246 232"\n'
        '"_sunlight" "118"\n"_sunlight_mangle" "125 -52 0"\n'
        '"_sunlight_color" "1 0.94 0.82"\n'
        '"_sunlight2" "65"\n"_sunlight2_color" "0.64 0.82 1"\n'
        '"_sunlight_penumbra" "1.5"\n'
        '"_dirt" "1"\n"_dirtscale" "0.65"\n'
    )
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    if GROUPS["detail"]:
        f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    if GROUPS["phong"]:
        f.write('{\n"classname" "func_detail"\n"_phong" "1"\n"_phong_angle" "89"\n' + "".join(GROUPS["phong"]) + "}\n")
    if GROUPS["fence"]:
        f.write('{\n"classname" "func_wall"\n"_shadow" "0"\n"_minlight" "58"\n' + "".join(GROUPS["fence"]) + "}\n")
    if GROUPS["illus"]:
        f.write('{\n"classname" "func_detail_illusionary"\n"_shadow" "0"\n"_minlight" "92"\n"_minlight_color" "245 248 232"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))

if check_placed():
    sys.exit("ERROR: spawns or items blocked by solid brushes!")

print(
    f"wrote {OUT_MAP}: {len(GROUPS['world'])} world + {len(GROUPS['detail'])} detail + "
    f"{len(GROUPS['fence'])} fence + {len(GROUPS['illus'])} illus brushes, "
    f"{len(PADS)} jump pads, {len(ENTS)} entities"
)
