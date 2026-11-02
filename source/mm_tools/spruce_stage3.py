"""spruce_stage3.py — Stage 3 builders for `make_spruce.py`:
Surrounding streets, commercial landmarks (CITYSERVE Main Hub, Smart & Final Extra / Dollar Tree,
Westchester Apartments & NE parking lot, 3037 & 3036 Jacaranda Dr, Beech x Hubbard, 2883 & 2801 Spruce St),
fences, '3035' & curbside bins, utility poles & overhead wires, street signs, parked vehicles, and trees.
"""
import math
import random

from spruce_lib import (
    Fit,
    GIS,
    box,
    brush_ent,
    brush_vehicle,
    cedar_tree,
    convex_parts,
    ent,
    eucalyptus_tree,
    fence_line,
    hiproof,
    light,
    obox,
    ogable,
    osloped_panel,
    palm_tree,
    prism,
    prop,
    road_stencil,
    shade_tree,
    strut_3d,
    trash_bin,
    tspec,
    utility_pole,
    wire_span,
)


def build_stage3(by_sid):
    # ==========================================================================
    # 1. CITYSERVE MAIN HUB WAREHOUSE & CRACKED LOT (`*8229`, img_145..152)
    # ==========================================================================
    # Vast cracked paved commercial lot south & west of CITYSERVE (x = 340..910, y = -620..-350)
    box(340.0, -620.0, -0.2, 915.0, -352.0, 0.10, tspec("sp_lot", 18), group="detail", solid=True)
    # Concrete apron right in front of the 6 roll-up bays (x = 412..596, y = -372..-356)
    box(412.0, -372.0, 0.0, 598.0, -356.0, 0.22, tspec("sp_conc", 10), group="detail", solid=True)

    # Main 1-storey tan brick/CMU warehouse wing facing South (yaw = 270) at x = 418.9..595.5, y = -358.5..-298.5!
    tan_brk = tspec("sp_tanbrk", 10)
    box(421.0, -356.0, 0.0, 593.0, -301.0, 17.5, "sp_roof_lt", group="world")
    box(418.9, -358.5, 0.2, 595.5, -298.5, 18.8, tan_brk, {"t": tspec("sp_roof_lt", 16)}, group="detail", solid=True)
    # Dark bronze overhanging canopy fascia across the south bay wall (z = 12.2..13.4, y = -362.5..-358.5)
    box(415.0, -362.5, 12.2, 596.0, -358.2, 13.3, "sp_roof_drk", group="detail", solid=True)
    # Parapet cap trim
    box(418.5, -359.0, 18.8, 596.0, -357.8, 19.3, "sp_roof_drk", group="detail", solid=False)

    # 6 bays on south wall (img_145: Bay 1 has man-door + blue placard, Bays 2-4 black rollups, gap of tan brick, Bays 5-6 rollups!)
    bay_xs = [
        (427.0, 442.0, "sp_rollup1"),
        (452.0, 467.0, "sp_rollup"),
        (478.0, 493.0, "sp_rollup"),
        (503.0, 518.0, "sp_rollup"),
        # Wide solid tan-brick pier 518..542 under the CITYSERVE banner (exact match to img_145!)
        (542.0, 557.0, "sp_rollup"),
        (563.0, 578.0, "sp_rollup"),
    ]
    for bx0, bx1, btex in bay_xs:
        box(bx0, -358.8, 0.22, bx1, -358.3, 11.4, tan_brk, {"s": Fit(btex)}, group="detail", solid=True)
        # Yellow steel pipe bollards flanking roll-up jambs
        for jx in (bx0 - 0.5, bx1 + 0.5):
            prop(jx - 0.25, -359.4, 0.22, jx + 0.25, -358.8, 3.2, "sp_gar_yel")

    # Royal-blue 'CITYSERVE / MAIN HUB' sign centered above Bays 4 and the brick pier (x = 516..542, z = 13.8..18.2, img_145!)
    box(515.0, -358.9, 13.8, 541.0, -358.4, 18.2, "sp_bin_blu", {"s": Fit("sp_cityserve")}, group="detail", solid=False)

    # East 2-storey / tall commercial wing of *8229 (x = 595.5..914.0, y = -482.0..-250.0)
    box(598.0, -478.0, 0.0, 910.0, -254.0, 22.0, "sp_roof_lt", group="world")
    box(595.5, -482.0, 0.1, 914.0, -250.0, 24.0, tan_brk, {"t": tspec("sp_roof_lt", 20)}, group="detail", solid=True)
    # Chain-link fence & yellow gate bollards west of CITYSERVE (`x = 345..419, y = -358.5`, img_145 left!)
    fence_line([(345.0, -358.5), (418.9, -358.5)], 0.1, 6.2, "{sp_chain", group="fence", fit_len=3.0)
    for ybol in (-359.5, -357.5):
        for xbol in (352.0, 362.0):
            prop(xbol - 0.35, ybol - 0.35, 0.1, xbol + 0.35, ybol + 0.35, 3.8, "sp_gar_yel")

    # Tall twin-arm silver parking lot light poles across CITYSERVE & Smart & Final lots (img_130, img_146)
    for lx, ly in ((455.0, -490.0), (585.0, -520.0), (412.0, -185.0), (535.0, -140.0)):
        prop(lx - 0.6, ly - 0.6, 0.1, lx + 0.6, ly + 0.6, 2.2, "sp_conc")
        prop(lx - 0.28, ly - 0.28, 2.2, lx + 0.28, ly + 0.28, 29.0, "sp_wt_tank")
        prop(lx - 5.5, ly - 0.18, 28.5, lx + 5.5, ly + 0.18, 29.0, "sp_wt_tank")
        prop(lx - 6.2, ly - 0.55, 28.2, lx - 4.8, ly + 0.55, 28.7, "sp_stuc_wht")
        prop(lx + 4.8, ly - 0.55, 28.2, lx + 6.2, ly + 0.55, 28.7, "sp_stuc_wht")

    # ==========================================================================
    # 2. SMART & FINAL EXTRA! / DOLLAR TREE & PINE-30TH ALLEY (`*6170, *8730`, img_130, img_154)
    # ==========================================================================
    # Paved rear loading lot & parking lot (x = 350..880, y = -245..+220)
    box(350.0, -245.0, -0.2, 890.0, 220.0, 0.10, tspec("sp_lot", 18), group="detail", solid=True)
    # White commercial shopping center buildings (*6170 at cx=592,cy=33, yaw=-43 deg -> SW rear dock at yaw=223, NE front at yaw=43!)
    wht_com = tspec("sp_stuc_wht", 14)
    obox(591.7, 33.3, 0.1, 24.5, 80.0, 78.0, 47.0, wht_com,
         {"front": wht_com, "t": tspec("sp_roof_lt", 20)}, group="detail", solid=True)
    box(550.0, -10.0, 0.0, 632.0, 75.0, 22.0, "sp_roof_lt", group="world")
    # Smart & Final Extra! red sign & Dollar Tree green sign on NE shopping-center frontage
    obox(632.0, 74.0, 17.5, 22.5, 24.0, 0.6, 47.0, "sp_redstep", {"front": Fit("sp_smartfin")}, group="detail", solid=False)
    obox(748.0, -40.0, 16.5, 21.0, 22.0, 0.6, 47.0, "sp_wt_green", {"front": Fit("sp_dollartr")}, group="detail", solid=False)
    # Adjacent SE wing (*8730 at cx=711, cy=-80) + 1-storey rear loading dock projection (img_130!)
    obox(710.9, -80.2, 0.1, 21.0, 68.0, 64.0, 47.0, wht_com, {"t": tspec("sp_roof_lt", 20)}, group="detail", solid=True)
    obox(516.0, -34.0, 0.1, 15.5, 42.0, 28.0, 47.0, wht_com,
         {"back": tspec("sp_rollup", 12), "left": tspec("sp_rollup", 12), "t": tspec("sp_roof_lt", 16)}, group="detail", solid=True)

    # Destructible white delivery vans & white roll-off container in rear dock lot (img_130!)
    brush_vehicle(501.0, -82.0, 227.0, "sp_stuc_wht", kind="van", z0=0.10)
    brush_vehicle(525.0, -102.0, 227.0, "sp_stuc_wht", kind="van", z0=0.10)
    obox(512.0, -124.0, 0.1, 6.2, 4.5, 11.0, 47.0, "sp_stuc_wht", {"left": "sp_gar_rib", "right": "sp_gar_rib"}, group="detail", solid=True)

    # Green-screened chain-link fence along the Pine/30th alley (`img_130.jpg` foreground!)
    fence_line([(295.0, -245.0), (368.0, -162.0), (435.0, -85.0)], 0.1, 6.2, "{sp_chaingrn", group="fence", fit_len=3.2)

    # Yellow directional arrow signs (`<-` and `->`) + palm trees along Pine / 30th lane (img_154!)
    for ax, ay, atex in ((378.0, -348.0, "sp_arrow_l"), (402.0, -328.0, "sp_arrow_r")):
        prop(ax - 0.15, ay - 0.15, 0.1, ax + 0.15, ay + 0.15, 6.2, "sp_wt_tank")
        obox(ax, ay, 5.2, 6.8, 1.8, 0.15, 310.0, "sp_gar_yel", {"front": Fit(atex), "back": Fit(atex)}, group="detail", solid=False)
    for px, py in ((655.0, 128.0), (685.0, 96.0), (725.0, 56.0), (775.0, 8.0)):
        palm_tree(px, py, h=40.0)

    # White solar carports between 3000-block alley and Pine lot (`loop_ids_1266.jpg` bottom-right, x=240..410, y=-310..-40!)
    for k in range(5):
        cx = 278.0 + k * 26.0
        cy = -255.0 + k * 42.0
        obox(cx, cy, 8.8, 9.4, 9.5, 48.0, 52.0, tspec("sp_stuc_wht", 10), {"t": tspec("sp_solar", 8)}, group="detail", solid=True)
        for sv in (-36.0, 0.0, 36.0):
            rad = math.radians(52.0)
            px = cx + sv * math.cos(rad)
            py = cy + sv * math.sin(rad)
            prop(px - 0.35, py - 0.35, 0.1, px + 0.35, py + 0.35, 8.8, "sp_wt_tank")

    # ==========================================================================
    # 3. WESTCHESTER APARTMENTS & NE PARKING LOT (`img_184`, `img_185`, `img_006`)
    # ==========================================================================
    # Camera `sv-water-tower-east-pano` stands at `(128, 616)` looking SW (`yaw 225`) directly at the Water Tower `(-11.6, 473.4)`!
    # Left of sightline: N-S cream apartment wing `*3180` (`x = 69..98, y = 418..582`, north gable end at `y = 582`).
    # Right of sightline: E-W cream apartment wing `*1710` (`x = -8..66, y = 587..615`, east gable end at `x = 66`), leaving the exact
    # narrow breezeway gap (`66..69, 582..587`) through which the Water Tower's gravel yard & chain-link fence show in `img_185`!
    box(92.0, 574.0, -0.2, 205.0, 668.0, 0.10, tspec("sp_lot", 16), group="detail", solid=True)
    # Crisp lawn strip & concrete sidewalk along the north & east sides of the apartment wings (`img_185`!)
    box(40.0, 560.0, -0.1, 132.0, 600.0, 0.06, tspec("sp_lawn", 14), group="detail", solid=True)
    box(66.0, 584.0, 0.0, 122.0, 588.0, 0.16, tspec("sp_conc", 6), group="detail", solid=True)
    box(102.0, 584.0, 0.0, 107.0, 598.0, 0.16, tspec("sp_conc", 6), group="detail", solid=True)
    # White parking stall stripes on right side of `img_185` (`x = 92..112, y = 598..642`)!
    for sy in (602.0, 612.0, 622.0, 632.0):
        box(92.0, sy - 0.18, 0.11, 110.0, sy + 0.18, 0.15, "sp_stuc_wht", group="illus", solid=False)

    apt_stuc = tspec("sp_stuc_crm", 10)
    apt_roof = tspec("sp_roof_brn", 8)
    # Wing A (`*3180`, N-S wing on LEFT of `img_185`: `x = 69..98, y = 418..582`, north gable at `y = 582`)
    box(71.0, 420.0, 0.0, 96.0, 580.0, 9.0, "sp_roof_brn", group="world")
    obox(83.5, 500.0, 0.06, 9.6, 14.5, 82.0, 90.0, apt_stuc, group="detail", solid=True)
    ogable(83.5, 500.0, 9.6, 13.5, 14.5, 82.0, 90.0, apt_roof, apt_stuc, eave=1.4)

    # Wing B (`*1710`, E-W wing on RIGHT of `img_185`: `x = -8..66, y = 587..615`, east gable at `x = 66`)
    box(-6.0, 589.0, 0.0, 64.0, 613.0, 9.0, "sp_roof_brn", group="world")
    obox(29.0, 601.0, 0.06, 9.6, 14.0, 37.0, 0.0, apt_stuc, group="detail", solid=True)
    ogable(29.0, 601.0, 9.6, 13.5, 14.0, 37.0, 0.0, apt_roof, apt_stuc, eave=1.4)

    # Wing C (`*2465`, E-W cream wing w/ dark shutters SE of parking lot in `img_184` left: `x = 122..178, y = 544..572`)
    box(124.0, 546.0, 0.0, 176.0, 570.0, 9.0, "sp_roof_brn", group="world")
    obox(150.0, 558.0, 0.06, 9.6, 14.0, 28.0, 180.0, apt_stuc, group="detail", solid=True)
    ogable(150.0, 558.0, 9.6, 13.4, 14.0, 28.0, 180.0, apt_roof, apt_stuc, eave=1.4)

    # Rooftop swamp coolers along the apartment ridges (`img_185`!)
    for cy_c in (450.0, 490.0, 530.0, 568.0):
        prop(81.5, cy_c - 1.5, 13.0, 85.0, cy_c + 1.5, 15.6, "sp_cooler")
    for cx_c in (8.0, 34.0, 54.0):
        prop(cx_c - 1.5, 599.5, 13.0, cx_c + 1.5, 603.0, 15.6, "sp_cooler")

    # Apartment windows, doors & foundation shrubs facing the courtyard & lot (`img_184`, `img_185`)
    for wy in range(440, 576, 22):
        box(98.0, wy, 2.8, 98.4, wy + 5.0, 6.8, apt_stuc, {"e": Fit("sp_win_wht")}, group="detail", solid=False)
        prop(98.3, wy - 3.5, 0.06, 100.8, wy - 0.5, 2.8, "sp_hedge")
    for wx in range(6, 60, 18):
        box(wx, 615.0, 2.8, wx + 4.8, 615.4, 6.8, apt_stuc, {"n": Fit("sp_win_wht")}, group="detail", solid=False)
        prop(wx + 5.2, 615.3, 0.06, wx + 8.2, 617.8, 2.8, "sp_hedge")
    for wx in (132.0, 154.0):
        box(wx, 572.0, 3.0, wx + 7.2, 572.4, 6.8, apt_stuc, {"n": Fit("sp_win_dksh")}, group="detail", solid=False)

    # Parked vehicles in NE apartment lot matching `img_185` (white van + white SUV on left; dark blue Dodge pickup + orange cone + silver sedan on right!)
    brush_vehicle(132.0, 586.0, 270.0, "sp_stuc_wht", kind="van", z0=0.10)
    brush_vehicle(122.0, 585.0, 270.0, "sp_stuc_wht", kind="suv_4runner", z0=0.10)
    brush_vehicle(96.0, 607.0, 180.0, "sp_bin_blu", kind="pickup", z0=0.10)
    brush_vehicle(100.0, 618.0, 180.0, "sp_stuc_gry", kind="sedan", z0=0.10)
    # Orange cone right beside front bumper of blue pickup (`img_185`!)
    prop(105.2, 610.5, 0.10, 106.3, 611.6, 2.3, "sp_redstep")
    # Tall winter bare/airy tree on left of `img_185` (`(115, 574)`) + bright green leafy tree on right (`(84, 628)`)!
    shade_tree(115.0, 574.0, h=35.0, r_crown=11.0, leaf_tex="{sp_euc", z_clear=9.5, seed=31)
    shade_tree(84.0, 628.0, h=26.0, r_crown=10.0, leaf_tex="{sp_weep", z_clear=8.0, seed=32)

    # Mark apartment & commercial GIS footprints as custom-built so auto-GIS loop skips them!
    by_sid["done"].update({3180, 1710, 2465, 9104, 714, 8806, 3992, 8229, 6170, 8730})

    # ==========================================================================
    # 4. JACARANDA DR LANDMARKS (`*7012` / `*9884` Yellow-Garage Solar Ranch & `*4126` 3037 Jacaranda, img_162..168)
    # ==========================================================================
    # `img_168.jpg` (looking NW yaw 315 from (-502, -18) on Jacaranda Dr):
    # Sage-grey ranch house facing SE (yaw = 318 deg) with OLIVE-YELLOW 2-car garage door on left,
    # stone-veneer porch pier in center, double sage-grey lap-siding gables on right, and BLACK SOLAR PANELS on grey roof!
    jac_sage = tspec("sp_sid_sage", 8)
    jac_roof = tspec("sp_roof_lt", 8)
    jcx, jcy, jyaw = -538.0, 26.0, 318.0
    rad_j = math.radians(jyaw)
    jvx, jvy = math.cos(rad_j), math.sin(rad_j)
    jux, juy = -math.sin(rad_j), math.cos(rad_j)

    # Wide concrete driveway leading from Jacaranda Dr NW curb to the yellow garage door!
    obox(jcx - 16.0 * jux + 24.0 * jvx, jcy - 16.0 * juy + 24.0 * jvy, 0.02, 0.16, 11.5, 18.0, jyaw,
         tspec("sp_conc", 8), group="detail", solid=True)
    # Left garage & center stucco/siding wing (`img_168`: pitched roof displaying black PV solar panels!)
    obox(jcx - 10.0 * jux, jcy - 10.0 * juy, 0.06, 9.2, 20.0, 15.0, jyaw, jac_sage, group="detail", solid=True)
    ogable(jcx - 10.0 * jux, jcy - 10.0 * juy, 9.2, 15.4, 20.0, 15.0, jyaw + 90.0, jac_roof, jac_sage, eave=1.3)
    # Olive-yellow 2-car garage door (`sp_gar_yel`) on left front!
    obox(jcx - 18.5 * jux + 15.1 * jvx, jcy - 18.5 * juy + 15.1 * jvy, 0.16, 7.6, 8.2, 0.2, jyaw,
         "sp_gar_yel", {"front": Fit("sp_gar_yel")}, group="detail", solid=False)
    # Center white window + stone-veneer accent wall (`sp_stone`, img_168!)
    obox(jcx - 5.5 * jux + 15.1 * jvx, jcy - 5.5 * juy + 15.1 * jvy, 3.6, 7.2, 3.2, 0.2, jyaw,
         "sp_win_whtw", {"front": Fit("sp_win_whtw")}, group="detail", solid=False)
    obox(jcx + 2.2 * jux + 15.1 * jvx, jcy + 2.2 * juy + 15.1 * jvy, 0.06, 8.8, 3.6, 0.3, jyaw,
         tspec("sp_stone", 5), group="detail", solid=True)
    # Right projecting double-gable sage-grey lap-siding wing (img_168 right half!)
    obox(jcx + 18.0 * jux + 3.0 * jvx, jcy + 18.0 * juy + 3.0 * jvy, 0.06, 9.4, 15.0, 16.5, jyaw, jac_sage, group="detail", solid=True)
    ogable(jcx + 18.0 * jux + 3.0 * jvx, jcy + 18.0 * juy + 3.0 * jvy, 9.4, 14.8, 15.0, 16.5, jyaw, jac_roof, jac_sage, eave=1.3)
    for du_w in (12.5, 23.5):
        obox(jcx + du_w * jux + 19.6 * jvx, jcy + du_w * juy + 19.6 * jvy, 3.8, 7.2, 3.6, 0.2, jyaw,
             "sp_win_whtw", {"front": Fit("sp_win_whtw")}, group="detail", solid=False)
    # Two stepped Black PV Solar Panel arrays sloped prominently on the SE roof face (`sp_solar`, img_168!)
    osloped_panel(jcx - 17.0 * jux + 7.5 * jvx, jcy - 17.0 * juy + 7.5 * jvy, 10.1, 13.5, 9.5, 5.2, jyaw,
                  Fit("sp_solar", (2.0, 1.0)), thick=0.35)
    osloped_panel(jcx - 3.0 * jux + 5.0 * jvx, jcy - 3.0 * juy + 5.0 * jvy, 11.2, 14.6, 8.5, 5.2, jyaw,
                  Fit("sp_solar", (2.0, 1.0)), thick=0.35)
    # Silver Prius / sedan parked in driveway + cedar side fences (img_168!)
    brush_vehicle(jcx - 21.0 * jux + 24.0 * jvx, jcy - 21.0 * juy + 24.0 * jvy, jyaw, "sp_stuc_gry", kind="sedan", z0=0.16)
    fence_line([(jcx - 31 * jux + 12 * jvx, jcy - 31 * juy + 12 * jvy), (jcx - 38 * jux + 12 * jvx, jcy - 38 * juy + 12 * jvy)],
               0.1, 6.0, "sp_redfnc")
    fence_line([(jcx + 33 * jux + 16 * jvx, jcy + 33 * juy + 16 * jvy), (jcx + 42 * jux + 16 * jvx, jcy + 42 * juy + 16 * jvy)],
               0.1, 6.0, "sp_redfnc")

    # Opposite on SE side of Jacaranda Dr: `*4126` (3037 Jacaranda Dr, charcoal-grey w/ white breeze-block screen, img_164!)
    # and `*4906` (2-storey cream stucco house w/ brown/terracotta roof on right of img_162!)
    obox(-441.7, -76.1, 0.06, 9.6, 26.0, 18.0, 138.0, tspec("sp_roof_drk", 8), group="detail", solid=True)
    ogable(-441.7, -76.1, 9.6, 14.0, 26.0, 18.0, 138.0, tspec("sp_roof_drk", 8), tspec("sp_roof_drk", 8), eave=1.2)
    obox(-399.6, -12.1, 0.06, 18.5, 22.0, 20.0, 138.0, tspec("sp_stuc_crm", 10), group="detail", solid=True)
    ogable(-399.6, -12.1, 18.5, 23.0, 22.0, 20.0, 138.0, tspec("sp_redstep", 8), tspec("sp_stuc_crm", 10), eave=1.4)
    shade_tree(-456.0, -48.0, h=28.0, r_crown=10.5, leaf_tex="{sp_gold", seed=41)
    trash_bin(-452.0, 8.0, 138.0, col_tex="sp_bin_blu", z0=0.45)
    by_sid["done"].update({7012, 9884, 4126, 4906})

    # ==========================================================================
    # 5. NORTH ALLEY ('3035' BINS, WHITE LATTICE FENCE & SOLAR ROOFS, img_113..128)
    # ==========================================================================
    # `*7040` (3035 Spruce St, cx=102.6, cy=164.5) + rear garage `*3319` (cx=124.5, cy=129.7, facing South onto y=105 alley!)
    # Look at `img_113.jpg` (camera at (116, 104) looking North yaw 0 = Quake 90):
    # - Left half (x = 92..114, y = 115.5): WHITE DIAGONAL LATTICE FENCE (`sp_latfence`) + corrugated patio cover weighted with red bricks!
    # - In front of lattice fence at (99.5, 113.5) and (104.5, 113.5): BLUE '30035 / CITY OF BAKERSFIELD' BIN & GREEN '3035' BIN!
    # - Right half (x = 114.5..134.5, y = 116..138): cream stucco garage (`*3319`) with WIDE GREY RIBBED STEEL ROLL-UP DOOR (`sp_gar_rib`)
    #   and brown hipped roof topped with sloped BLACK SOLAR PANELS (`sp_solar`), and behind `3035`'s solar roof (`*7040`) rises the
    #   SILVER-WHITE WATER TOWER (`(-11.6, 473.4)`) in the upper-left sky!!
    box(114.5, 116.0, 0.06, 134.5, 138.0, 8.8, tspec("sp_stuc_crm", 8),
        {"s": tspec("sp_stuc_crm", 8)}, group="detail", solid=True)
    box(116.2, 115.8, 0.12, 132.8, 116.1, 7.6, "sp_gar_rib", {"s": Fit("sp_gar_rib")}, group="detail", solid=False)
    hiproof([(114.5, 116.0), (134.5, 116.0), (134.5, 138.0), (114.5, 138.0)], 8.8, tspec("sp_roof_brn", 7), eave=1.0, pitch=4.0 / 12)
    osloped_panel(124.5, 122.0, 9.3, 11.4, 7.8, 4.2, 270.0, Fit("sp_solar", (2.0, 1.0)))

    # 3035 Main House (`*7040`, x = 86..127, y = 143..177) with brown hipped roof + 2 solar arrays + satellite dish!
    box(88.0, 145.0, 0.0, 125.0, 175.0, 8.8, "sp_roof_brn", group="world")
    box(86.0, 143.2, 0.06, 127.5, 177.2, 9.6, tspec("sp_stuc_crm", 10), group="detail", solid=True)
    hiproof([(86.0, 143.2), (127.5, 143.2), (127.5, 177.2), (86.0, 177.2)], 9.6, tspec("sp_roof_brn", 8), eave=1.3, pitch=4.2 / 12)
    osloped_panel(106.5, 150.0, 10.2, 13.0, 13.5, 4.8, 270.0, Fit("sp_solar", (3.0, 1.0)))

    # White diagonal lattice fence (`sp_latfence`) + corrugated lean-to patio roof weighted down with red bricks (`img_113`!)
    box(92.0, 115.4, 0.10, 114.5, 116.0, 6.6, tspec("sp_latfence", 6.6, 6.5),
        {"s": Fit("sp_latfence", (3.2, 1.0))}, group="detail", solid=True)
    box(92.0, 115.8, 6.6, 114.5, 136.0, 7.0, tspec("sp_gar_rib", 6), group="detail", solid=True)
    for rbx, rby in ((96.0, 116.8), (103.5, 116.6), (109.0, 117.2), (99.0, 121.0), (107.0, 120.5)):
        prop(rbx, rby, 7.0, rbx + 0.8, rby + 0.45, 7.3, "sp_redbrk")

    # Iconic '30035 / CITY OF BAKERSFIELD' Blue Bin & '3035' Green Bin right in front of the lattice fence (`img_113`!)
    trash_bin(100.2, 112.4, 270.0, col_tex="sp_bin_blu", lid_tex="sp_bin_3035b", z0=0.10)
    trash_bin(105.0, 112.4, 270.0, col_tex="sp_bin_grn", lid_tex="sp_bin_3035g", z0=0.10)
    # Neighboring gable house on far left of `img_113` (`x = 66..90, y = 122..152`, replacing overlapping `sid=3553`!)
    obox(78.0, 137.0, 0.06, 9.4, 14.0, 11.5, 0.0, tspec("sp_stuc_crm", 10), group="detail", solid=True)
    ogable(78.0, 137.0, 9.4, 14.2, 14.0, 11.5, 0.0, tspec("sp_roof_drk", 8), tspec("sp_stuc_crm", 10), eave=1.1)
    # Additional bins along North Alley & 3000-block Alley
    for bx, by, bcol in ((64.0, 113.2, "sp_bin_brn"), (68.0, 113.2, "sp_bin_blu"), (-18.0, -104.0, "sp_bin_blu"), (-21.0, -106.0, "sp_bin_blu")):
        trash_bin(bx, by, 270.0, col_tex=bcol, z0=0.10)
    by_sid["done"].update({7040, 3319, 3553})

    # ==========================================================================
    # 6. NE ARM PICKET-FENCE HOUSE (`*2521` & `*8199`, img_097..104)
    # ==========================================================================
    # `*2521` (cx=231.1, cy=120.9) beige stucco, brown hipped roof + rooftop swamp cooler + white dog-ear picket fence (`{sp_picket`)!
    obox(231.1, 120.9, 0.06, 9.6, 20.5, 16.5, 48.0, tspec("sp_stuc_tan", 10),
         {"back": tspec("sp_stuc_tan", 10)}, group="detail", solid=True)
    # White back door & windows facing NW toward alley (img_097!)
    obox(221.5, 130.0, 0.2, 7.2, 1.8, 0.2, 138.0, "sp_door_wht", {"front": Fit("sp_door_wht")}, group="detail", solid=False)
    for off_u in (-6.5, 5.5):
        rad138 = math.radians(138.0)
        wx = 221.5 + off_u * math.sin(rad138)
        wy = 130.0 - off_u * math.cos(rad138)
        obox(wx, wy, 3.0, 6.8, 2.6, 0.2, 138.0, "sp_win_wht", {"front": Fit("sp_win_wht")}, group="detail", solid=False)
    for part in convex_parts(by_sid["map"][2521][0]["pts"]):
        hiproof(part, 9.6, tspec("sp_roof_brn", 8), eave=1.3, pitch=4.2 / 12)
    prop(228.0, 122.0, 13.5, 231.5, 125.5, 16.4, "sp_cooler")
    # White dog-ear picket fence wrapping from Spruce St NE arm up the SE edge of alley 1882 (`img_097`!)
    fence_line([(256.0, 92.0), (235.0, 68.0), (206.0, 96.0), (182.0, 114.0)], 0.1, 5.6, "{sp_picket", group="fence", fit_len=5.5)
    trash_bin(202.0, 96.5, 225.0, col_tex="sp_bin_brn", z0=0.10)
    shade_tree(246.0, 102.0, h=26.0, r_crown=9.5, leaf_tex="{sp_leaf", seed=61)
    by_sid["done"].add(2521)

    # ==========================================================================
    # 7. BEECH ST x HUBBARD ST & 3000-BLOCK ALLEY FENCES, POLES & STREET SIGNS
    # ==========================================================================
    # Long weathered cedar corner fence & STOP sign at Beech St x Hubbard St (`img_138..142`!)
    fence_line([(-615.0, -565.0), (-545.0, -510.0), (-490.0, -555.0)], 0.1, 6.0, "sp_woodfnc", fit_len=8.0)
    # 3000-block east alley grey CMU block wall (`img_107`) & wooden yard fences (`img_105..112`)
    fence_line([(146.0, -330.0), (255.0, -185.0), (352.0, -55.0)], 0.1, 6.2, "sp_cmu", fit_len=8.0)
    fence_line([(124.0, -338.0), (234.0, -192.0), (332.0, -64.0)], 0.1, 6.0, "sp_woodfnc", fit_len=8.0)

    # Stop signs (`{sp_stopsign`) at Beech St junctions + `SPEED LIMIT 25` sign at 3000 Spruce St (`img_035`!)
    for sx, sy, syaw in ((-34.0, -336.0, 52.0), (-96.0, -396.0, 232.0), (-585.0, -618.0, 42.0)):
        prop(sx - 0.12, sy - 0.12, 0.1, sx + 0.12, sy + 0.12, 7.2, "sp_wt_tank")
        obox(sx, sy, 6.8, 9.2, 1.2, 0.08, syaw, "{sp_invis",
             {"front": Fit("{sp_stopsign"), "back": "sp_wt_tank"}, group="fence", solid=False)
    # SPEED LIMIT 25 at Spruce & Beech SE curb (img_035!)
    prop(8.0, -296.0, 0.45, 8.24, -295.76, 7.0, "sp_wt_tank")
    obox(8.12, -295.88, 5.4, 7.6, 0.85, 0.10, 142.0, "sp_spd25", {"front": Fit("sp_spd25")}, group="detail", solid=False)

    # Utility poles + overhead wires along Water Tower South Alley (`img_169`: pole on RIGHT at `x = -58`!), North Alley, and 3000-Block Alley!
    wt_poles = [(-158.0, 381.5), (-58.0, 381.5), (18.0, 381.5), (96.0, 381.5), (175.0, 381.5)]
    for px, py in wt_poles:
        utility_pole(px, py, yaw_deg=90.0, h=33.0)
    for a, b in zip(wt_poles, wt_poles[1:]):
        wire_span(a, b, 30.8, 30.8, sag=1.1)
        wire_span((a[0], a[1] + 1.5), (b[0], b[1] + 1.5), 30.8, 30.8, sag=1.1)

    al_poles = [(132.0, -332.0), (186.0, -258.0), (242.0, -184.0), (298.0, -110.0), (350.0, -42.0)]
    for px, py in al_poles:
        utility_pole(px, py, yaw_deg=52.0, h=30.0)
    for a, b in zip(al_poles, al_poles[1:]):
        wire_span(a, b, 28.0, 28.0, sag=1.0)

    # ==========================================================================
    # 8. 3001 SPRUCE ST (`*53`, `img_039`), NEIGHBORHOOD TREES & STREET VEHICLES
    # ==========================================================================
    # Custom 3001 Spruce St (`*53`, cx=-104.6, cy=-252.6, facing SE `yaw = 322` next to 3003, `img_023` left & `img_039`!):
    obox(-104.6, -252.6, 0.04, 9.4, 20.5, 16.0, 322.0, tspec("sp_stuc_crm", 10), group="detail", solid=True)
    obox(-104.6, -252.6, 0.0, 8.6, 17.5, 13.0, 322.0, tspec("sp_stuc_crm", 10), group="world", solid=True)
    _r53 = math.radians(322.0)
    _vx53, _vy53 = math.cos(_r53), math.sin(_r53)
    _ux53, _uy53 = math.sin(_r53), -math.cos(_r53)
    hiproof([(-104.6 + su * 20.5 * _ux53 + sv * 16.0 * _vx53, -252.6 + su * 20.5 * _uy53 + sv * 16.0 * _vy53)
             for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
            9.4, tspec("sp_roof_brn", 8), eave=1.3, pitch=5.0 / 12.0)
    obox(-94.5, -264.5, 3.2, 7.4, 4.4, 0.2, 322.0, "sp_win_pic", {"front": Fit("sp_win_pic")}, group="detail", solid=False)
    # Silver sedan parked at 3001 curb (`img_039` foreground!)
    brush_vehicle(-62.0, -296.0, 232.0, "sp_stuc_gry", kind="sedan", z0=0.12)
    by_sid["done"].add(53)

    # West Loop (`3054` img_089): red hatchback at left curb, white pickup, weeping green tree, weathered wooden fence!
    brush_vehicle(-124.0, 38.0, 76.0, "sp_redstep", kind="sedan", z0=0.12)
    brush_vehicle(-128.0, -12.0, 256.0, "sp_stuc_wht", kind="pickup", z0=0.12)
    shade_tree(-114.0, 88.0, h=29.0, r_crown=11.0, leaf_tex="{sp_weep", z_clear=9.5, seed=71)
    shade_tree(-84.0, 46.0, h=28.0, r_crown=10.5, leaf_tex="{sp_leaf", z_clear=10.0, seed=72)
    fence_line([(-96.0, 26.0), (-88.0, 68.0), (-64.0, 68.0)], 0.1, 5.8, "sp_woodfnc", fit_len=7.0)

    # Additional trees framing loop, Beech St, 2883/2801 Spruce St & alleys without blocking anchor sightlines!
    extra_trees = [
        (-76.0, -276.0, 32.0, 13.5, "{sp_gold"),      # 3001 Spruce St golden autumn tree IN FRONT LAWN (`img_039` center, `img_023` left!)
        (-4.0, -198.0, 29.0, 10.5, "{sp_gold"),       # 3005 Spruce St right-side autumn tree (img_023 right!)
        (32.0, -296.0, 32.0, 11.5, "{sp_leaf"),       # 3000 Spruce St evergreen/ivy tree behind SPEED LIMIT 25 (img_035!)
        (-36.0, 26.0, 29.0, 11.0, "{sp_weep"),        # 3051 Spruce St weeping tree across from 3075 (img_073/080!)
        (-12.0, 18.0, 27.0, 10.0, "{sp_weep"),        # 3051 second weeping tree
        (54.0, -12.0, 28.0, 10.5, "{sp_leaf"),        # Between 3055 & 3059 (img_064 center-left!)
        (108.0, -22.0, 34.0, 6.5, "{sp_cedar"),       # Slim conifer between 3059 & 3013 (img_064 right!)
        (192.0, 188.0, 30.0, 11.0, "{sp_leaf"),       # North-east loop shade tree
        (38.0, 252.0, 31.0, 11.0, "{sp_leaf"),        # North loop shade tree
        (-155.0, -435.0, 30.0, 11.0, "{sp_leaf"),     # 2883 Spruce St
        (-228.0, -515.0, 32.0, 11.5, "{sp_cedar"),    # 2801 Spruce x Hubbard
    ]
    for idx, (tx, ty, th, tr, ltex) in enumerate(extra_trees):
        shade_tree(tx, ty, h=th, r_crown=tr, leaf_tex=ltex, z_clear=9.5, seed=100 + idx)

    # Additional street-parked destructible vehicles across the loop & NE arm (active in Single-Player AND Deathmatch!)
    brush_vehicle(28.0, -258.0, 52.0, "sp_stuc_gry", kind="sedan", z0=0.12)
    brush_vehicle(225.0, 18.0, 52.0, "sp_bin_blu", kind="pickup", z0=0.12)
    brush_vehicle(198.0, -16.0, 52.0, "sp_redstep", kind="coupe", z0=0.12)
    brush_vehicle(55.0, 222.0, 0.0, "sp_redstep", kind="coupe", z0=0.12)
    brush_vehicle(-472.0, 58.0, 65.0, "sp_stuc_wht", kind="van", z0=0.12)
