"""fox_neighborhood.py — Builds the complete 1:1 Downtown Bakersfield neighborhood
from G St (west) to K St (east) and 18th St (south) to 21st St (north), matched to:
  1. padre-hotel-gallery-self-contained.html (199 images + iGUIDE floor plans)
  2. fox-block-gallery-self-contained.html (424 images + aerials + Street View 360s)

Includes the fully player-explorable 8-story Padre Hotel + Clover Ballroom (via padre_hotel.py),
Playable 5-Story Public Parking Garage, Walk-in 1720 20th St Warehouse, Nile Theater (true
south-of-19th location), Ovation Theatre, Zama, Buena Vista Museum (2018 Chester Ave), Aura,
Woolworth's Luncheonette (1400 19th St), S.H. Kress, Tiki-Ko, Bobby Cloud Law, Mi Casa
Furniture, The Mint Bar, The 18hundred (Brazilian Acai / Habibi's Hookah), Chain Cohn Clark,
Bakersfield Central Fire Station, American Legion Post 26 banners, Today Cleaners pylon,
Central Academy gear mural at 18th & H, 1701/1715 18th St, KCCD, GET bus, and accurate
intersection crosswalks, STOP/ONE WAY signs, and asphalt stencils.
"""
from __future__ import annotations
import math
from padre_hotel import build_padre_hotel


def build_neighborhood(ctx):
    box = ctx["box"]
    prop = ctx["prop"]
    prism = ctx["prism"]
    frustum_ring = ctx["frustum_ring"]
    circle_poly = ctx["circle_poly"]
    wall_x = ctx["wall_x"]
    wall_y = ctx["wall_y"]
    ent = ctx["ent"]
    light = ctx["light"]
    brush_ent = ctx["brush_ent"]
    tspec = ctx["tspec"]
    Fit = ctx["Fit"]
    fan_palm = ctx["fan_palm"]
    double_globe_lamp = ctx["double_globe_lamp"]
    fox_model = ctx["fox_model"]

    STUCCO = tspec("fx_stucco", 12)
    STUCCO_DK = tspec("fx_stucco_dk", 10)
    TERRA = tspec("fx_terra", 6)
    REDBRK = tspec("fn_redbrk", 10)
    BRKPAVE = tspec("fn_brkpave", 4)

    # ==========================================================================
    # HELPER BUILDERS
    # ==========================================================================
    def stripe_x(x0, x1, y, w=0.35, tex="bk_wline", dash=None):
        if dash is None:
            box(x0, y - w / 2, 0.0, x1, y + w / 2, 0.07, tex, group="illus")
        else:
            on, gap = dash
            cur = x0
            while cur + on <= x1:
                box(cur, y - w / 2, 0.0, cur + on, y + w / 2, 0.07, tex, group="illus")
                cur += on + gap

    def stripe_y(x, y0, y1, w=0.35, tex="bk_wline", dash=None):
        if dash is None:
            box(x - w / 2, y0, 0.0, x + w / 2, y1, 0.07, tex, group="illus")
        else:
            on, gap = dash
            cur = y0
            while cur + on <= y1:
                box(x - w / 2, cur, 0.0, x + w / 2, cur + on, 0.07, tex, group="illus")
                cur += on + gap

    def crosswalk_ns(x0, x1, y_center, yellow=False):
        tex = "bk_yline" if yellow else "bk_wline"
        if yellow:
            box(x0 + 1.0, y_center - 4.8, 0.0, x1 - 1.0, y_center - 4.2, 0.07, tex, group="illus")
            box(x0 + 1.0, y_center + 4.2, 0.0, x1 - 1.0, y_center + 4.8, 0.07, tex, group="illus")
        for cx in range(int(x0) + 3, int(x1) - 3, 6):
            box(cx, y_center - 4.5, 0.0, cx + 2.4, y_center + 4.5, 0.07, tex, group="illus")

    def crosswalk_ew(x_center, y0, y1, yellow=False):
        tex = "bk_yline" if yellow else "bk_wline"
        if yellow:
            box(x_center - 4.8, y0 + 1.0, 0.0, x_center - 4.2, y1 - 1.0, 0.07, tex, group="illus")
            box(x_center + 4.2, y0 + 1.0, 0.0, x_center + 4.8, y1 - 1.0, 0.07, tex, group="illus")
        for cy in range(int(y0) + 3, int(y1) - 3, 6):
            box(x_center - 4.5, cy, 0.0, x_center + 4.5, cy + 2.4, 0.07, tex, group="illus")

    def road_stencil(cx, cy, tex_name, w=12.0, h=6.0):
        box(cx - w / 2, cy - h / 2, 0.0, cx + w / 2, cy + h / 2, 0.08, Fit(tex_name), group="illus")

    def mast_signal(px, py, arm_dir, blade_tex=None, green=True):
        prop(px - 0.35, py - 0.35, 0.5, px + 0.35, py + 0.35, 22.0, "bk_steel")
        dx, dy = {"e": (18.0, 0.0), "w": (-18.0, 0.0), "n": (0.0, 18.0), "s": (0.0, -18.0)}[arm_dir]
        ax0, ax1 = sorted((px, px + dx))
        ay0, ay1 = sorted((py, py + dy))
        if abs(dx) > 0:
            prop(ax0, py - 0.22, 17.6, ax1, py + 0.22, 18.2, "bk_steel")
            if blade_tex:
                bx0, bx1 = sorted((px + dx * 0.22, px + dx * 0.62))
                prop(bx0, py - 0.32, 16.0, bx1, py + 0.32, 17.6, "bk_steel",
                     {"n": Fit(blade_tex), "s": Fit(blade_tex)})
            sx = px + dx * 0.78
            prop(sx - 0.55, py - 0.55, 14.5, sx + 0.55, py + 0.55, 18.0, "fx_drapeblk")
            col_tex = "bk_leaf" if green else "fx_foxred"
            z_lamp = 14.8 if green else 17.0
            prop(sx - 0.35, py - 0.62, z_lamp, sx + 0.35, py + 0.62, z_lamp + 0.7, col_tex)
        else:
            prop(px - 0.22, ay0, 17.6, px + 0.22, ay1, 18.2, "bk_steel")
            if blade_tex:
                by0, by1 = sorted((py + dy * 0.22, py + dy * 0.62))
                prop(px - 0.32, by0, 16.0, px + 0.32, by1, 17.6, "bk_steel",
                     {"e": Fit(blade_tex), "w": Fit(blade_tex)})
            sy = py + dy * 0.78
            prop(px - 0.55, sy - 0.55, 14.5, px + 0.55, sy + 0.55, 18.0, "fx_drapeblk")
            col_tex = "bk_leaf" if green else "fx_foxred"
            z_lamp = 14.8 if green else 17.0
            prop(px - 0.62, sy - 0.35, z_lamp, px + 0.62, sy + 0.35, z_lamp + 0.7, col_tex)

    def post_sign(x, y, tex_name, face_dir="e", alpha=False, w_ft=2.2, h_ft=2.2):
        prop(x - 0.12, y - 0.12, 0.5, x + 0.12, y + 0.12, 8.2, "bk_steel")
        grp = "fence" if alpha else "detail"
        base_tex = tex_name if alpha else "bk_steel"
        if face_dir in ("e", "w"):
            box(x - 0.16, y - w_ft / 2, 7.6, x + 0.16, y + w_ft / 2, 7.6 + h_ft,
                base_tex, {"e": Fit(tex_name), "w": Fit(tex_name)}, group=grp)
        else:
            box(x - w_ft / 2, y - 0.16, 7.6, x + w_ft / 2, y + 0.16, 7.6 + h_ft,
                base_tex, {"n": Fit(tex_name), "s": Fit(tex_name)}, group=grp)

    def street_tree(x, y, h=20.0, winter=False):
        prop(x - 0.42, y - 0.42, 0.5, x + 0.42, y + 0.42, h * 0.48, "bk_bark")
        if winter:
            for ang in (0.4, 1.9, 3.5, 5.0):
                bx = x + math.cos(ang) * 2.6
                by = y + math.sin(ang) * 2.6
                prism([(x - 0.2, y - 0.2), (x + 0.2, y - 0.2), (bx + 0.2, by + 0.2), (bx - 0.2, by + 0.2)],
                      [h * 0.44, h * 0.44, h * 0.85, h * 0.85],
                      [h * 0.48, h * 0.48, h * 0.90, h * 0.90], "bk_bark", group="illus")
            prism(circle_poly(x, y, 4.2, 8), h * 0.55, h * 0.92, "bk_drygrass", group="illus")
        else:
            prism(circle_poly(x, y, 5.2, 8), h * 0.46, h * 0.82, "bk_leaf", group="illus")
            prism(circle_poly(x, y, 3.6, 8), h * 0.78, h, "bk_leaf", group="illus")

    def street_clock(scx, scy):
        fox_model("fox_clockpost", scx, scy, 0.52, yaw=0, z_off=0.06,
                  clip_box=(scx - 0.92, scy - 0.92, 0.85, scx + 0.92, scy + 0.92, 13.5))
        light(scx, scy, 16.5, 145, "255 228 176")

    def solid_block_building(x0, y0, x1, y1, z_top, wall_tex, faces=None, core=True):
        if core and (x1 - x0 > 12) and (y1 - y0 > 12) and z_top >= 16.0:
            box(x0 + 2.0, y0 + 2.0, 0.0, x1 - 2.0, y1 - 2.0, z_top - 1.0, "bk_roof", group="world")
        fmap = dict(faces or {})
        fmap.setdefault("t", "bk_roof")
        box(x0, y0, 0.5, x1, y1, z_top, wall_tex, fmap, group="detail", solid=True)
        prop(x0 - 0.3, y0 - 0.3, z_top, x1 + 0.3, y1 + 0.3, z_top + 0.8, STUCCO_DK)

    # ==========================================================================
    # 1. COMPLETE SIDEWALK GRID & CURBS (G St .. K St, 18th St .. 21st St)
    # ==========================================================================
    # N-S Roadways: G (-352..-304), H (+16..+68), Eye (+360..+408), Chester (+702..+766), K (+1046..+1094)
    # E-W Roadways: 21st (+284..+332), 20th Pl (+182..+206 Eye..Chester), 20th (-64..-16),
    #               Service (-222..-194), 19th (-400..-352), Wall (-546..-518), 18th (-728..-680)
    block_slabs = [
        # West of G St (x = -418 .. -352)
        (-418, +332, -352, +416), (-418, -16, -352, +284),
        (-418, -194, -352, -64), (-418, -352, -352, -222),
        (-418, -518, -352, -400), (-418, -680, -352, -546), (-418, -824, -352, -728),
        # G St to H St (x = -304 .. +16, split by West Alley x = -142..-122 north of 19th)
        (-304, +332, +16, +416),                                    # Central Fire Station block
        (-304, -16, -142, +284),                                    # 1720 20th Warehouse block
        (-122, -16, +16, +284),                                     # FOX THEATER & TODAY CLEANERS!
        (-304, -194, -142, -64), (-304, -352, -142, -222),          # G..Alley 20th-19th
        (-122, -352, +16, -64),                                     # Lino's & Historic Tevis Brick block
        (-304, -518, +16, -400),                                    # THE NILE THEATER & Front Porch Music!
        # (Padre Hotel block -304..+16, -680..-546 is laid selectively below around Padre & Clover!)
        (-304, -824, +16, -728),                                    # 1701 / 1715 / 1725 18th St across from Padre!
        # H St to Eye St (x = +68 .. +360, split by H-Eye Alley 206..224 & Service St -222..-194)
        (+68, +332, +360, +416),
        (+68, -16, +206, +284),                                     # 2000 H & American Legion Post 26
        (+224, -16, +360, +284),                                    # Dagny's / Jones Bldg & 21st/Eye lot
        (+68, -194, +206, -64),                                     # PG&E Building
        (+224, -194, +360, -64),                                    # Sub Station & Lattice Tower
        (+68, -352, +360, -222),                                    # Ovation Theatre, Tegeler, TOSS it, JIN Sushi
        (+68, -518, +360, -400),                                    # Zama, Art Center Gallery, Encore! Boutique
        (+68, -680, +360, -546),                                    # 18th & Eye 5-Story Public Parking Garage!
        (+68, -824, +360, -728),                                    # Central Academy Gear Mural & SW Frieze!
        # Eye St to Chester Ave (x = +408 .. +702, split by 20th Pl +182..+206 & Service St -222..-194)
        (+408, +332, +702, +416),                                   # GET Transit & North Eye-Chester
        (+408, +206, +702, +284),                                   # 1924 Brick & Guarantee Shoe Center
        (+408, -16, +702, +182),                                    # AT&T & NW 20th/Chester
        (+408, -194, +702, -64),                                    # Bakersfield Music Theatre & Bobby Cloud Law
        (+408, -352, +702, -222),                                   # Tina Marie's, Foothills Mural, Manna House
        (+408, -518, +702, -400),                                   # Roosters / Eye-Chester 19th-Wall
        (+408, -680, +702, -546),                                   # Chain | Cohn | Clark & 18th/Eye pilaster bldg
        (+408, -824, +702, -728),                                   # 1415 18th St 6-story tower block
        # Chester Ave to K St (x = +766 .. +1046, split by Service St -222..-194)
        (+766, +332, +1046, +416),                                  # Kern Community College District (KCCD)!
        (+766, -16, +1046, +284),                                   # Buena Vista Museum, Aura & Wild Mama!
        (+766, -194, +1046, -64),                                   # Tiki-Ko & Service/K block
        (+766, -352, +1046, -222),                                  # Woolworth's Luncheonette (1400 19th St)!
        (+766, -518, +1046, -400),                                  # Jalisco Jewelry, Antique Mall & S.H. Kress!
        (+766, -680, +1046, -546),                                  # The 18hundred (1800 Chester) & K St Garage!
        (+766, -824, +1046, -728),                                  # SE 18th & Chester block
        # East of K St (x = +1094 .. +1234)
        (+1094, +332, +1234, +416),
        (+1094, -16, +1234, +284),                                  # Larry E. Reider Education Center
        (+1094, -194, +1234, -64),
        (+1094, -352, +1234, -222),                                 # Mi Casa Home Furniture (NE 19th & K)!
        (+1094, -518, +1234, -400),                                 # The Mint Bar (19th St east) & SE 19th/K!
        (+1094, -680, +1234, -546),
        (+1094, -824, +1234, -728),
    ]
    for bx0, by0, bx1, by1 in block_slabs:
        if bx0 == -122 and by0 == -16:
            box(-122, -16, 0.0, +16, 0.0, 0.5, "bk_walk", group="detail")
            box(0.0, 0.0, 0.0, +16, +284, 0.5, "bk_walk", group="detail")
            box(-122, +196, 0.0, 0.0, +284, 0.5, "bk_walk", group="detail")
            box(-122, 0.0, 0.0, -96, +196, 0.5, "bk_walk", group="detail")
        else:
            box(bx0, by0, 0.0, bx1, by1, 0.5, "bk_walk", group="detail")

    # Padre Hotel & Clover Ballroom surrounding sidewalks (preserving interior floors & Basement Gym!)
    box(-304.0, -680.0, 0.0, +16.0, -666.0, 0.5, "bk_walk", group="detail")     # 18th St north sidewalk
    box(0.0, -666.0, 0.0, +16.0, -546.0, 0.5, "bk_walk", group="detail")        # H St west sidewalk
    box(-304.0, -556.0, 0.0, 0.0, -546.0, 0.5, "bk_walk", group="detail")       # Wall St south sidewalk
    box(-304.0, -666.0, 0.0, -232.0, -556.0, 0.5, "bk_walk", group="detail")    # G St east sidewalk/lot
    box(-232.0, -666.0, 0.0, -136.0, -660.0, 0.5, "bk_walk", group="detail")    # South of Clover
    box(-232.0, -608.0, 0.0, -136.0, -556.0, 0.5, "bk_walk", group="detail")    # North of Clover

    # Build the complete multi-floor explorable Padre Hotel + Clover 1 & 2 Ballroom!
    build_padre_hotel(ctx)

    # Terracotta-red brick sidewalk corner bands & 19th x Eye circular brick intersection stamp (fblk_012/304!)
    for ix in (16, 68, 360, 408, 702, 766, 1046, 1094):
        dx = -5.0 if ix in (16, 360, 702, 1046) else 5.0
        for iy in (-680, -400, -352, -64, -16, 284):
            dy = 5.0 if iy in (-352, -16) else -5.0
            xa, xb = sorted((ix, ix + dx))
            ya, yb = sorted((iy, iy + dy))
            box(xa, ya, 0.5, xb, yb, 0.54, BRKPAVE, group="illus")
    prism(circle_poly(384.0, -376.0, 14.0, 12), 0.0, 0.06, BRKPAVE, group="illus")

    # Chester Ave continuous brick paver curb strip + landscaped center median islands
    for cy0, cy1 in ((-676, -550), (-514, -404), (-348, -68), (-12, +280)):
        box(696, cy0, 0.5, 702, cy1, 0.54, BRKPAVE, group="illus")
        box(766, cy0, 0.5, 772, cy1, 0.54, BRKPAVE, group="illus")
    for my0, my1 in ((-668, -556), (-508, -412), (-340, -78), (-2, +270), (+344, +408)):
        box(730.0, my0, 0.0, 738.0, my1, 0.65, STUCCO_DK, group="detail")
        box(731.2, my0 + 4.0, 0.65, 736.8, my1 - 4.0, 1.3, "bk_hedge", group="detail")
        street_tree(734.0, (my0 + my1) / 2.0, 22.0, winter=False)

    # Yellow flower-bed curb bulb-outs at 21st St & Eye St (fblk_410)
    for fx0, fx1 in ((354.0, 362.0), (406.0, 414.0)):
        box(fx0, 260.0, 0.0, fx1, 276.0, 0.65, STUCCO_DK, group="detail")
        box(fx0 + 1.0, 261.5, 0.65, fx1 - 1.0, 274.5, 1.6, "bk_yline", group="detail")

    # ==========================================================================
    # 2. LANE STRIPES, YELLOW & WHITE CROSSWALKS, ROAD STENCILS & TRAFFIC SIGNALS
    # ==========================================================================
    ns_segs = [(-818, -738), (-670, -554), (-510, -408), (-344, -72), (-8, +276), (+340, +410)]
    for y_lo, y_hi in ns_segs:
        for off in (-0.4, 0.4):
            stripe_y(42.0 + off, y_lo, y_hi, 0.32, "bk_yline")
            stripe_y(384.0 + off, y_lo, y_hi, 0.32, "bk_yline")
        for lx in (29.0, 55.0):
            stripe_y(lx, y_lo, y_hi, 0.28, "bk_wline", (10, 18))
        for lx in (372.0, 396.0):
            stripe_y(lx, y_lo, y_hi, 0.28, "bk_wline", (10, 18))
        stripe_y(-328.0, y_lo, y_hi, 0.30, "bk_yline", (12, 16))
        for lx in (716.0, 752.0):
            stripe_y(lx, y_lo, y_hi, 0.28, "bk_wline", (10, 18))
        stripe_y(1070.0, y_lo, y_hi, 0.28, "bk_wline", (10, 18))

    ew_segs = [(-412, -360), (-296, +8), (+76, +352), (+416, +694), (+774, +1038), (+1102, +1228)]
    for x_lo, x_hi in ew_segs:
        for yc in (308.0, -376.0, -704.0):
            stripe_x(x_lo, x_hi, yc - 0.35, 0.3, "bk_yline")
            stripe_x(x_lo, x_hi, yc + 0.35, 0.3, "bk_yline")
        for ly in (-48.0, -32.0):
            stripe_x(x_lo, x_hi, ly, 0.28, "bk_wline", (10, 18))
        stripe_x(x_lo, x_hi, -532.0, 0.28, "bk_wline", (10, 18))

    # Diagonal street parking stalls on 20th St & 19th St (Woolworth's / Nile)
    for px in list(range(-98, -18, 14)) + list(range(436, 668, 16)):
        prism([(px, -16.0), (px + 0.35, -16.0), (px - 5.65, -25.0), (px - 6.0, -25.0)],
              0.0, 0.07, "bk_wline", group="illus")
    for px in range(890, 1032, 15):
        prism([(px, -352.0), (px + 0.35, -352.0), (px - 5.65, -361.0), (px - 6.0, -361.0)],
              0.0, 0.07, "bk_wline", group="illus")

    # Crosswalks: Yellow ladder crosswalks at 18th & H & 18th & G (padre_052 / fblk_330!), White elsewhere!
    for ix0, ix1 in ((-352, -304), (16, 68), (360, 408), (702, 766), (1046, 1094)):
        for iy_lo, iy_hi in ((-728, -680), (-400, -352), (-64, -16), (284, 332)):
            is_ylw = (iy_lo == -728 and ix0 in (-352, 16))
            crosswalk_ns(ix0, ix1, iy_lo - 5.0, yellow=is_ylw)
            crosswalk_ns(ix0, ix1, iy_hi + 5.0, yellow=is_ylw)
            crosswalk_ew(ix0 - 5.0, iy_lo, iy_hi, yellow=is_ylw)
            crosswalk_ew(ix1 + 5.0, iy_lo, iy_hi, yellow=is_ylw)

    # Painted Asphalt Street-Name & STOP Stencils
    road_stencil(48.0, 18.0, "fn_rd_hst")
    road_stencil(35.0, 265.0, "fn_rd_hst")
    road_stencil(48.0, -338.0, "fn_rd_hst")
    road_stencil(48.0, -660.0, "fn_rd_hst")
    road_stencil(-28.0, -692.0, "fn_rd_18th")
    road_stencil(110.0, -714.0, "fn_rd_18th")
    road_stencil(-68.0, -36.0, "fn_rd_20th")
    road_stencil(340.0, -36.0, "fn_rd_20th")
    road_stencil(680.0, -36.0, "fn_rd_20th")
    road_stencil(-176.0, -388.0, "fn_rd_19th")
    road_stencil(976.0, -388.0, "fn_rd_19th")
    road_stencil(392.0, -336.0, "fn_rd_eye")
    road_stencil(376.0, 266.0, "fn_rd_eye")
    road_stencil(750.0, -336.0, "fn_rd_ches")
    road_stencil(720.0, -28.0, "fn_rd_ches")
    road_stencil(342.0, -532.0, "fn_rd_wall")
    road_stencil(-328.0, -110.0, "fn_rd_gst")
    road_stencil(1070.0, -280.0, "fn_rd_kst")
    road_stencil(1070.0, -418.0, "fn_rd_stop")                  # 'STOP' stencil at 19th & K St (fblk_171)!
    road_stencil(-328.0, -666.0, "fn_rd_stop")                  # 'STOP' stencil at 18th & G St (fblk_329)!

    # Mast-Arm Traffic Signals across Key Intersections
    mast_signal(12.0, -68.0, "e", "fn_st_20th", green=True)
    mast_signal(72.0, -12.0, "w", "fn_st_hst", green=True)
    mast_signal(72.0, -348.0, "w", "fn_st_19th", green=True)
    mast_signal(12.0, -404.0, "e", "fn_st_hst", green=True)
    mast_signal(12.0, -732.0, "e", "fn_st_18th", green=True)    # SW 18th & H across from Padre!
    mast_signal(72.0, -676.0, "w", "fn_st_hst", green=True)     # NE 18th & H (padre_052!)
    mast_signal(12.0, 280.0, "e", "fn_st_21st", green=True)
    mast_signal(72.0, 336.0, "w", "fn_st_hst", green=True)
    mast_signal(356.0, -12.0, "e", "fn_st_eye", green=True)
    mast_signal(412.0, -68.0, "w", "fn_st_20th", green=True)
    mast_signal(412.0, -348.0, "w", "fn_st_19th", green=True)
    mast_signal(356.0, -676.0, "e", "fn_st_eye", green=True)    # NW 18th & Eye (fblk_345)
    mast_signal(356.0, 280.0, "e", "fn_st_21st", green=True)
    mast_signal(698.0, -12.0, "s", "fn_st_20th", green=False)
    mast_signal(770.0, -12.0, "w", "fn_st_ches", green=False)
    mast_signal(770.0, -348.0, "w", "fn_st_19th", green=True)
    mast_signal(770.0, -676.0, "w", "fn_st_18th", green=True)   # NE 18th & Chester

    # Regulatory Signs: DO NOT ENTER, STOP, and ONE WAY (fblk_038, 105, 171, 329, 378)
    post_sign(356.0, -342.0, "fn_dne", "s")
    post_sign(412.0, -342.0, "fn_dne", "s")
    post_sign(236.0, -206.0, "fn_dne", "e")
    post_sign(74.0, -522.0, "fn_dne", "e")
    post_sign(1098.0, -406.0, "{fn_stopsg", "s", alpha=True)    # STOP sign at 19th & K!
    post_sign(1042.0, -348.0, "{fn_stopsg", "e", alpha=True)
    post_sign(-300.0, -674.0, "{fn_stopsg", "s", alpha=True)    # STOP sign at 18th & G!
    post_sign(74.0, -68.0, "fn_oneway", "n", w_ft=2.8, h_ft=1.4)
    post_sign(1098.0, -228.0, "fn_oneway", "w", w_ft=2.8, h_ft=1.4)

    # ==========================================================================
    # 3. BLOCK-BY-BLOCK 1:1 BUILDINGS & LANDMARKS
    # ==========================================================================

    # --- A. 21ST & H + FOX BLOCK NORTH/WEST (Central Fire Station, Today Cleaners, 1720 20th) ---
    # Bakersfield Central Fire Station at NW corner of 21st & H (fblk_209..211!)
    solid_block_building(-118.0, 344.0, 8.0, 412.0, 22.0, STUCCO,
                         {"e": Fit("fn_firest", (1.2, 1)), "s": Fit("fn_firest", (2, 1))})
    solid_block_building(-292.0, 344.0, -142.0, 412.0, 18.0, STUCCO_DK)

    # Today Cleaners (2033 H St, SW of 21st & H, fblk_198..200): plant + drive-thru + 'IN BY 10 READY AT 4' pylon!
    solid_block_building(-78.0, 204.0, -18.0, 258.0, 16.5, STUCCO_DK,
                         {"e": tspec("fn_darkgl", 12), "n": tspec("fn_darkgl", 12)})
    prop(-18.0, 206.0, 11.8, 7.5, 260.0, 15.2, STUCCO_DK,
         {"n": Fit("fn_cleaners"), "e": Fit("fn_cleaners"), "s": STUCCO_DK, "b": STUCCO})
    for col_y in (210.0, 254.0):
        prop(5.5, col_y, 0.5, 7.0, col_y + 1.5, 11.8, STUCCO)
    box(-16.0, 260.0, 0.5, 10.0, 279.0, 0.72, "bk_leaf", group="detail")
    prop(-2.0, 266.0, 0.72, -1.0, 267.0, 9.5, STUCCO)
    prop(-4.2, 264.0, 9.5, 1.2, 269.0, 14.0, STUCCO_DK,
         {"e": Fit("fn_tdpyl"), "w": Fit("fn_tdpyl"), "n": Fit("fn_tdpyl"), "s": Fit("fn_tdpyl")})
    fan_palm(-10.0, 270.0, 14.0)

    # 1720 20th St Warehouse & Open Walk-In Truck Bay across West Stage Alley
    box(-236.0, 2.0, 0.5, -196.0, 88.0, 19.0, STUCCO_DK, group="world")
    wall_x(-196.0, -146.0, 2.0, 1.5, 0.5, 19.0, STUCCO_DK,
           holes=[(-180.0, -166.0, 0.5, 11.5)], group="detail")
    prop(-180.0, 2.2, 11.5, -166.0, 3.3, 14.0, tspec("fx_rollup", 6))
    box(-147.5, 2.0, 0.5, -146.0, 46.0, 19.0, STUCCO_DK, group="detail")
    box(-196.0, 44.5, 0.5, -146.0, 46.0, 19.0, STUCCO_DK, group="detail")
    box(-196.0, 2.0, 17.5, -146.0, 46.0, 19.2, STUCCO_DK, {"t": "bk_roof"}, group="detail")
    light(-172.0, 24.0, 15.5, 195, "255 240 210")
    solid_block_building(-236.0, 90.0, -146.0, 256.0, 21.0, STUCCO_DK)
    solid_block_building(-292.0, 4.0, -242.0, 256.0, 18.0, STUCCO,
                         {"w": tspec("fn_darkgl", 12), "s": tspec("fx_shopwin", 12)})
    prop(-145.5, 112.0, 0.5, -141.5, 120.0, 5.2, "fx_awngrn")

    # --- B. H..EYE NORTH (2000 H + American Legion Military Banners + Dagny's Coffee / Jones Bldg) ---
    solid_block_building(86.0, 4.0, 202.0, 108.0, 19.5, STUCCO_DK,
                         {"w": tspec("fn_darkgl", 14), "s": tspec("fn_darkgl", 14)})
    prop(85.2, 34.0, 14.2, 86.0, 68.0, 18.6, "bk_white")
    prop(84.8, 3.5, 0.5, 86.0, 108.0, 4.2, tspec("fn_stone", 8))
    prop(84.8, 2.8, 0.5, 202.0, 4.0, 4.2, tspec("fn_stone", 8))
    prop(78.5, 3.0, 10.5, 86.0, 106.0, 13.6, tspec("fn_bwawn", 6), {"b": STUCCO})
    prop(78.5, -2.5, 10.5, 198.0, 4.0, 13.6, tspec("fn_bwawn", 6), {"b": STUCCO})
    for py in (18.0, 56.0, 92.0):
        fan_palm(72.5, py, 24.0)

    # American Legion Post 26 with 5 U.S. Military Service Portrait Banners (fblk_195..197!)
    solid_block_building(86.0, 116.0, 202.0, 242.0, 21.0, STUCCO_DK,
                         {"w": Fit("fn_legban", (2, 1))})
    prop(76.5, 136.0, 10.5, 86.0, 162.0, 12.8, STUCCO_DK,
         {"n": Fit("fn_usflag"), "s": Fit("fn_usflag"), "w": STUCCO, "b": STUCCO})
    for cy in (137.0, 161.0):
        prop(77.0, cy - 0.4, 0.5, 77.8, cy + 0.4, 10.5, "bk_steel")
    prop(78.0, 268.0, 0.5, 78.5, 268.5, 38.5, "bk_steel")
    prop(78.5, 268.1, 31.5, 87.5, 268.4, 36.2, STUCCO, {"n": Fit("fn_usflag"), "s": Fit("fn_usflag")})

    # Dagny's Coffee / Jones Building (1600 20th St, NW 20th & Eye, fblk_113..120)
    solid_block_building(228.0, 4.0, 342.0, 94.0, 28.5, STUCCO,
                         {"s": Fit("fn_jones", (2, 1)), "e": Fit("fn_jones", (2, 1))})
    prop(252.0, -1.5, 10.2, 342.5, 4.0, 13.0, tspec("fn_coffee", 10),
         {"s": Fit("fn_coffee", (3, 1)), "b": STUCCO})
    prop(342.0, 4.0, 10.2, 347.5, 72.0, 13.0, tspec("fn_coffee", 10),
         {"e": Fit("fn_coffee", (3, 1)), "b": STUCCO})
    box(228.0, 98.0, 0.5, 348.0, 272.0, 0.58, "bk_dirt", group="illus")

    # --- C. G..H MID BLOCKS (Lino's + Street Clock + 3-Story Historic Red-Brick Bldg + TRUE NILE THEATER!) ---
    solid_block_building(-68.0, -168.0, 10.0, -80.0, 26.5, STUCCO_DK,
                         {"n": tspec("fn_linos", 18), "e": tspec("fn_linos", 18)})
    solid_block_building(-140.0, -158.0, -68.0, -80.0, 16.5, STUCCO_DK,
                         {"n": tspec("fx_shopwin", 14)})
    for ax0, ax1 in ((-132, -108), (-102, -76), (-58, -34), (-26, -2)):
        prop(ax0, -80.0, 9.8, ax1, -76.2, 12.0, tspec("fn_awnblk", 4))
    street_clock(9.5, -72.5)                                    # SW 20th & H bronze street clock (fblk_020!)

    # NW 19th & H: 3-Story Historic Red-Brick Arched Building w/ Green Rounded Awnings (fblk_049 / 289!)
    solid_block_building(-118.0, -340.0, 10.0, -238.0, 36.0, REDBRK,
                         {"e": Fit("fn_tevis", (2.5, 1.3)), "s": Fit("fn_tevis", (3, 1.3)), "n": REDBRK})
    for ga_y in (-328.0, -304.0, -280.0):
        prop(10.0, ga_y, 9.6, 13.4, ga_y + 14.0, 12.2, "fx_awngrn")
    for ga_x in (-104.0, -76.0, -48.0, -20.0):
        prop(ga_x, -343.4, 9.6, ga_x + 14.0, -340.0, 12.2, "fx_awngrn")
    # Dark-green cast-iron corner sidewalk bollards at 19th & H (fblk_048.jpg!)
    for bx, by in [(13.2, -349.0), (13.2, -341.0), (5.0, -349.0), (70.8, -349.0), (70.8, -403.0), (13.2, -403.0)]:
        prop(bx - 0.35, by - 0.35, 0.5, bx + 0.35, by + 0.35, 3.2, "fx_awngrn")
        prop(bx - 0.42, by - 0.42, 3.2, bx + 0.42, by + 0.42, 3.45, "fx_bronze")
    # North of 19th between G & West Alley (clean 2-story brick/stucco commercial, fblk_284)
    solid_block_building(-292.0, -186.0, -152.0, -78.0, 20.0, STUCCO_DK)
    solid_block_building(-292.0, -340.0, -152.0, -230.0, 22.0, STUCCO,
                         {"s": tspec("fx_shopwin", 14), "w": tspec("fx_shopwin", 14)})

    # TRUE LOCATION OF THE NILE THEATER (1721 19th St — SOUTH side of 19th St between G & H, facing NORTH!
    # Verified in fblk_001, padre_010, fblk_132..134, fblk_292..295!)
    solid_block_building(-216.0, -514.0, -142.0, -412.0, 34.0, "bk_white",
                         {"n": Fit("fn_nileup", (2, 1)), "e": Fit("fn_mural"), "w": STUCCO})
    # Cobalt-blue mosaic tile entrance & ticket booth under marquee
    prop(-214.0, -412.0, 0.5, -144.0, -410.5, 11.2, "fn_nilebl", {"n": Fit("fn_nilebl")})
    # Projecting Feb 2026 Nile Marquee ('SPLOONKY RAVE 2.6 / LOS HERMANOS MENDOZA 2.15' | 'CUP CAKKE / SOLD OUT 2.21')
    prop(-210.0, -410.5, 11.2, -148.0, -401.5, 18.8, "fn_nilemq",
         {"n": Fit("fn_nilemq"), "e": Fit("fx_mqwing"), "w": Fit("fx_mqwing"), "b": tspec("fx_mqsoffit", 6)})
    # Tall vertical 'NILE' blade sign rising above the marquee (fblk_047 / 294!)
    prop(-180.5, -408.0, 18.8, -177.5, -401.0, 50.0, "fn_nile",
         {"e": Fit("fn_nile"), "w": Fit("fn_nile"), "n": Fit("fn_nile")})
    light(-179.0, -399.0, 15.0, 220, "255 220 175")
    # Adjacent West of Nile (-292..-218): 1-story retail; Adjacent East (-142..-84): 'FRONT PORCH MUSIC' (fblk_292)!
    solid_block_building(-292.0, -514.0, -218.0, -412.0, 19.0, STUCCO,
                         {"n": tspec("fx_shopwin", 14), "w": tspec("fx_shopwin", 14)})
    solid_block_building(-142.0, -514.0, -84.0, -412.0, 21.0, STUCCO,
                         {"n": Fit("fn_fporch")})
    # SW Corner of 19th & H Parking Lot (-82..+8) + 'THIRST TRAP' Billboard (fblk_046/047!)
    box(-82.0, -514.0, 0.5, 8.0, -410.0, 0.56, "bk_asphalt", group="illus")
    prop(-38.0, -456.0, 0.5, -36.5, -454.5, 14.0, "bk_steel")
    prop(-54.0, -456.5, 14.0, -20.0, -454.0, 28.0, "fn_thirst",
         {"n": Fit("fn_thirst"), "s": Fit("fn_thirst")})

    # --- D. H..EYE MID BLOCKS (PG&E + Lattice Tower + Tegeler + OVATION THEATRE + ZAMA + Art Center + Encore) ---
    solid_block_building(86.0, -164.0, 202.0, -80.0, 19.5, REDBRK,
                         {"w": tspec("fn_darkgl", 14), "n": tspec("fn_darkgl", 14)})
    prop(84.5, -92.0, 0.5, 96.5, -78.8, 20.5, REDBRK, {"w": Fit("fn_pge"), "n": Fit("fn_pge")})
    solid_block_building(250.0, -162.0, 344.0, -80.0, 26.5, STUCCO,
                         {"n": Fit("fn_substat", (2, 1)), "e": Fit("fn_substat", (2, 1)), "s": STUCCO})
    street_clock(351.0, -72.0)

    # Guard booth + 140-ft Lattice Telecom Tower on Service St
    prop(318.0, -192.0, 0.5, 344.0, -174.0, 11.5, "bk_white", {"s": STUCCO, "e": STUCCO, "t": "bk_roof"})
    prop(324.5, -194.8, 8.2, 339.5, -192.0, 9.8, "fn_awnblk")
    LX, LY = 237.0, -152.0
    prop(LX - 11.0, LY - 11.0, 0.5, LX + 11.0, LY + 11.0, 2.5, STUCCO_DK)
    for tz0, tz1, hw in [(2.5, 32.5, 9.5), (32.5, 62.5, 7.6), (62.5, 90.5, 5.8),
                         (90.5, 118.5, 4.2), (118.5, 142.5, 2.8)]:
        rep_y = (1.5, 2.5)
        box(LX - hw, LY - hw, tz0, LX + hw, LY - hw + 0.25, tz1, Fit("{fn_lattice", rep_y), group="fence")
        box(LX - hw, LY + hw - 0.25, tz0, LX + hw, LY + hw, tz1, Fit("{fn_lattice", rep_y), group="fence")
        box(LX - hw, LY - hw, tz0, LX - hw + 0.25, LY + hw, tz1, Fit("{fn_lattice", rep_y), group="fence")
        box(LX + hw - 0.25, LY - hw, tz0, LX + hw, LY + hw, tz1, Fit("{fn_lattice", rep_y), group="fence")
    prop(LX - 0.6, LY - 0.6, 152.0, LX + 0.6, LY + 0.6, 153.2, "fx_foxred")
    light(LX, LY, 154.0, 140, "255 80 70")

    # NE 19th & H 4-Story Loft / Tegeler Building (x = 86..164) + THE OVATION THEATRE (1622 19th St, x = 166..224, fblk_137!)
    solid_block_building(86.0, -338.0, 164.0, -224.0, 42.0, STUCCO,
                         {"w": Fit("fn_woolw", (2, 1.5)), "s": Fit("fn_woolw", (2, 1.5))})
    prop(90.0, -330.0, 42.0, 160.0, -228.0, 53.0, REDBRK, {"n": Fit("fn_tegsign"), "t": "bk_roof"})
    # The Ovation Theatre (1622 19th St): 2-story cream facade w/ 5 blue awnings & OVATION window sign!
    solid_block_building(166.0, -338.0, 224.0, -260.0, 28.0, STUCCO,
                         {"s": Fit("fn_ovation")})
    # JIN Sushi & TOSS it + Walkable Corner Patio (x = 226..344)
    solid_block_building(226.0, -338.0, 344.0, -258.0, 26.5, STUCCO,
                         {"e": Fit("fn_jinsushi", (2, 1)), "s": Fit("fn_jinsushi", (2, 1))})
    solid_block_building(226.0, -258.0, 330.0, -224.0, 26.5, STUCCO, {"n": Fit("fn_tossit", (1.2, 1))})
    prop(330.0, -258.0, 10.4, 350.0, -222.0, 11.4, "fn_awnblk", {"b": STUCCO})
    for px in (331.5, 348.5):
        for py in (-256.5, -223.5):
            prop(px - 0.35, py - 0.35, 0.5, px + 0.35, py + 0.35, 10.4, "fx_drapeblk")

    # South side of 19th St (H .. Eye): SE 19th & H arched bldg (fblk_045) + ZAMA brick row (fblk_141)
    # + ART CENTER GALLERY (fblk_309) + Encore! Boutique on Wall St (fblk_073)!
    solid_block_building(86.0, -508.0, 158.0, -412.0, 19.0, STUCCO_DK,
                         {"w": tspec("fn_darkgl", 14), "n": tspec("fn_darkgl", 14)})
    solid_block_building(162.0, -508.0, 256.0, -412.0, 20.0, REDBRK,
                         {"n": Fit("fn_zama", (1.4, 1))})
    solid_block_building(260.0, -460.0, 344.0, -412.0, 26.0, "bk_white",
                         {"n": Fit("fn_artctr"), "e": Fit("fn_artctr")})
    solid_block_building(260.0, -508.0, 344.0, -462.0, 26.0, "bk_white",
                         {"s": Fit("fn_encore", (1.5, 1)), "e": STUCCO})
    prop(290.0, -511.5, 9.4, 343.0, -508.0, 11.8, "fx_awnred")

    # --- E. PLAYABLE 5-STORY 18TH & EYE PUBLIC PARKING GARAGE + 18TH & H MURAL ---
    # Garage spans y = -666 .. -558, x = 148 .. 344 (extending south to 18th St per fblk_099 / 345!),
    # with low white courtyard building at NE 18th & H (x = 84..140, fblk_104)!
    solid_block_building(84.0, -666.0, 140.0, -598.0, 17.5, "bk_white",
                         {"w": tspec("fn_darkgl", 12), "s": tspec("fn_darkgl", 12)})
    box(148.0, -666.0, 0.0, 344.0, -558.0, 0.52, "bk_asphalt", group="detail")
    box(148.0, -596.0, 12.5, 344.0, -558.0, 13.5, "bk_asphalt", group="detail")
    box(296.0, -666.0, 12.5, 344.0, -596.0, 13.5, "bk_asphalt", group="detail")
    box(148.0, -666.0, 12.5, 176.0, -596.0, 13.5, "bk_asphalt", group="detail")
    # Smooth 24-ft wide driveable/walkable ramp from Ground (x=176, z=0.52) to Level 2 (x=296, z=13.5)
    prism([(176.0, -628.0), (296.0, -628.0), (296.0, -604.0), (176.0, -604.0)],
          [0.0, 12.0, 12.0, 0.0], [0.52, 13.5, 13.5, 0.52], "bk_asphalt", group="detail", solid=True)
    prop(148.0, -560.0, 13.5, 344.0, -558.0, 17.2, STUCCO)
    prop(342.0, -666.0, 13.5, 344.0, -558.0, 17.2, STUCCO)
    prop(148.0, -666.0, 13.5, 344.0, -664.0, 17.2, STUCCO)
    for gp_x in (148.0, 198.0, 248.0, 298.0, 340.0):
        prop(gp_x, -560.0, 0.52, gp_x + 4.0, -558.0, 24.5, STUCCO)
        prop(gp_x, -666.0, 0.52, gp_x + 4.0, -664.0, 24.5, STUCCO)
    prop(316.0, -561.0, 0.52, 329.0, -557.2, 56.0, tspec("fn_linos", 14))
    # Upper Garage Levels 3-5 (z = 24.5 .. 54.5)
    box(152.0, -662.0, 25.0, 340.0, -562.0, 53.5, "bk_roof", group="world")
    box(148.0, -666.0, 24.5, 344.0, -558.0, 54.5, tspec("fn_garage", 24),
        {"n": Fit("fn_garage", (6, 1.2)), "s": Fit("fn_garage", (6, 1.2)),
         "e": Fit("fn_garage", (3, 1.2)), "w": Fit("fn_garage", (3, 1.2)), "t": "bk_asphalt"},
        group="detail", solid=True)
    for rx0, rx1, ry0, ry1 in ((148, 344, -559.2, -558), (148, 344, -666, -664.8),
                               (148, 149.2, -666, -558), (342.8, 344, -666, -558)):
        prop(rx0, ry0, 54.5, rx1, ry1, 57.8, STUCCO)
    for gx in (175.0, 235.0, 305.0):
        light(gx, -580.0, 11.2, 185, "255 244 214")
    # Level 2 -> Level 5 Garage Roof Jump Pad!
    prop(156.0, -582.0, 13.5, 162.0, -576.0, 13.9, "fx_goldleaf")
    brush_ent("trigger_push", 156.0, -582.0, 13.9, 162.0, -576.0, 18.0, angles="-78 0 0", speed="1060")

    # --- F. SOUTH OF 18TH ST LANDMARKS (1701/1715 18th St + Central Academy Gear Mural + SW Frieze) ---
    # Directly south across 18th St from The Padre Hotel (fblk_091..095):
    solid_block_building(-92.0, -818.0, 6.0, -740.0, 26.0, "bk_white",
                         {"n": Fit("fn_b1701", (1.5, 1)), "e": Fit("fn_b1701")})
    solid_block_building(-152.0, -818.0, -94.0, -740.0, 25.0, STUCCO,
                         {"n": Fit("fn_b1715")})
    solid_block_building(-244.0, -818.0, -154.0, -740.0, 26.0, REDBRK,
                         {"n": Fit("fn_b1701", (1.4, 1)), "w": Fit("fn_b1701")})
    # SE corner of 18th & H: Vibrant Blue & Orange Gear/Ribbon Mural Building w/ 3D windows & parapet (padre_052 / fblk_343!)
    solid_block_building(82.0, -818.0, 212.0, -740.0, 28.0, "fn_caamur",
                         {"w": Fit("fn_caamur"), "n": Fit("fn_caamur", (1.4, 1))})
    prop(81.2, -772.0, 28.8, 128.0, -739.2, 31.2, STUCCO_DK)
    for wx in (92.0, 122.0, 152.0, 182.0):
        prop(wx, -740.5, 2.2, wx + 14.0, -739.8, 9.6, "fx_bronze", {"n": Fit("fx_shopwin")})
        prop(wx - 0.4, -740.8, 1.8, wx + 14.4, -739.8, 2.2, STUCCO)
    for wy in (-806.0, -776.0):
        prop(81.5, wy, 2.2, 82.2, wy + 14.0, 9.6, "fx_bronze", {"w": Fit("fx_shopwin")})
        prop(81.2, wy - 0.4, 1.8, 82.2, wy + 14.4, 2.2, STUCCO)
    # SW corner of 18th & Eye: Southwestern Geometric Frieze Building (fblk_349!)
    solid_block_building(238.0, -818.0, 348.0, -740.0, 19.5, STUCCO_DK,
                         {"n": Fit("fn_swfrz"), "e": Fit("fn_swfrz")})

    # --- G. EYE .. CHESTER BLOCKS (AT&T, 20th Pl, Guarantee Shoe, Bakersfield Music Theatre, Chain Cohn Clark) ---
    solid_block_building(424.0, 46.0, 566.0, 176.0, 54.0, tspec("fn_att", 24),
                         {"w": Fit("fn_att", (2, 2)), "s": tspec("fn_att", 24), "n": tspec("fn_att", 24)})
    prop(456.0, 82.0, 54.0, 532.0, 144.0, 62.0, STUCCO_DK)
    solid_block_building(574.0, 4.0, 688.0, 102.0, 16.5, "fx_drapeblk",
                         {"s": tspec("fn_darkgl", 12), "e": tspec("fn_darkgl", 12)})
    # North of 20th Pl (+206..+284): 1924 Red-Brick Bldg + Guarantee Shoe Center at SW 21st & Chester (fblk_423)!
    solid_block_building(424.0, 212.0, 556.0, 274.0, 27.5, REDBRK)
    solid_block_building(576.0, 212.0, 688.0, 274.0, 20.0, STUCCO,
                         {"e": Fit("fn_guarsh"), "n": Fit("fn_guarsh")})
    # Bakersfield Music Theatre (1425 20th St / Service St, x=536..636, y=-188..-78):
    # Honest plain white stucco pilaster wall — NO invented sign per clean.html!
    solid_block_building(536.0, -188.0, 636.0, -78.0, 24.0, "bk_white",
                         {"s": "bk_white", "n": STUCCO})
    for px in range(542, 636, 18):
        prop(px, -189.0, 0.5, px + 2.0, -187.8, 23.5, STUCCO)
    solid_block_building(424.0, -188.0, 528.0, -78.0, 22.0, STUCCO,
                         {"w": tspec("fx_shopwin", 14), "n": tspec("fx_shopwin", 14)})
    # Bobby Cloud Law at SW Service & Chester (fblk_375)
    solid_block_building(640.0, -188.0, 690.0, -124.0, 21.0, REDBRK,
                         {"s": Fit("fn_bobby"), "e": Fit("fn_bobby")})
    # Tina Marie's, Foothills Mural & NW 19th/Chester Ribbon-Window Building
    solid_block_building(424.0, -338.0, 536.0, -264.0, 18.5, STUCCO_DK,
                         {"w": Fit("fn_tinam"), "s": Fit("fn_tinam")})
    solid_block_building(424.0, -262.0, 536.0, -226.0, 23.0, STUCCO, {"w": Fit("fn_mural")})
    solid_block_building(556.0, -338.0, 688.0, -228.0, 38.0, tspec("fn_linos", 18),
                         {"e": tspec("fn_linos", 18), "s": tspec("fn_linos", 18)})
    # Eye..Chester south blocks: Roosters / 19th-Wall + Chain | Cohn | Clark (NW 18th & Chester, fblk_183) + 1415 18th Tower!
    solid_block_building(424.0, -508.0, 688.0, -412.0, 24.0, STUCCO,
                         {"n": tspec("fx_shopwin", 14), "e": tspec("fx_shopwin", 14)})
    solid_block_building(424.0, -668.0, 536.0, -558.0, 26.0, "bk_white",
                         {"w": tspec("fn_darkgl", 14), "s": tspec("fn_darkgl", 14)})
    solid_block_building(548.0, -668.0, 690.0, -562.0, 24.0, STUCCO,
                         {"s": Fit("fn_chain"), "e": Fit("fn_chain")})
    solid_block_building(548.0, -818.0, 690.0, -740.0, 68.0, tspec("fn_woolw", 20),
                         {"n": Fit("fn_woolw", (2, 3)), "e": Fit("fn_woolw", (1.5, 3))})

    # --- H. CHESTER AVE .. K ST & EAST OF K ST LANDMARKS ---
    # 1) Buena Vista Museum of Natural History & Science (2018 Chester Ave) + AURA + Wild Mama + KCCD!
    solid_block_building(780.0, 8.0, 912.0, 96.0, 25.0, "bk_white",
                         {"w": Fit("fn_aura"), "s": STUCCO})
    solid_block_building(780.0, 98.0, 912.0, 192.0, 26.0, STUCCO,
                         {"w": Fit("fn_bvm")})
    # Green bicycle-shaped MD3 bike rack on sidewalk in front of Buena Vista Museum (fblk_163)!
    fox_model("bvm_bikerack", 773.2, 117.0, 0.52, yaw=90,
              clip_box=(772.7, 113.8, 0.85, 773.7, 120.2, 3.3))
    solid_block_building(780.0, 212.0, 900.0, 274.0, 20.0, "fn_wildm",
                         {"n": Fit("fn_wildm"), "w": Fit("fn_wildm")})
    solid_block_building(924.0, 12.0, 1036.0, 272.0, 22.0, STUCCO_DK)
    solid_block_building(780.0, 344.0, 1036.0, 412.0, 28.0, STUCCO_DK,
                         {"s": Fit("fn_kccd", (2, 1)), "w": Fit("fn_kccd")})

    # 2) Tiki-Ko (Service & K) + THE WOOLWORTH'S LUNCHEONETTE (1400 19th St, NW 19th & K, fblk_169/328)!
    solid_block_building(780.0, -186.0, 938.0, -78.0, 32.0, STUCCO,
                         {"w": tspec("fn_darkgl", 14), "n": tspec("fn_darkgl", 14)})
    solid_block_building(948.0, -188.0, 1036.0, -108.0, 24.0, "bk_white",
                         {"s": Fit("fn_tikiko"), "e": Fit("fn_tikiko")})
    # Woolworth's 3-story white mid-century building + wrap-around red/gold 'F. W. WOOLWORTH CO.' sign + green awnings!
    solid_block_building(896.0, -340.0, 1036.0, -228.0, 40.0, "bk_white",
                         {"s": Fit("fn_woolup", (1.5, 1)), "e": Fit("fn_woolup", (1.2, 1))})
    prop(894.5, -342.0, 11.2, 1038.2, -339.5, 16.2, "fn_woolsg", {"s": Fit("fn_woolsg", (1.4, 1))})
    prop(1035.5, -339.5, 11.2, 1038.2, -264.0, 16.2, "fn_woolsg", {"e": Fit("fn_woolsg")})
    prop(896.0, -346.0, 9.5, 1036.0, -341.5, 11.2, "fx_awngrn")
    prop(1036.0, -341.5, 9.5, 1040.5, -268.0, 11.2, "fx_awngrn")
    solid_block_building(780.0, -340.0, 892.0, -228.0, 36.0, STUCCO,
                         {"w": Fit("fn_jalisco", (1.5, 1.5)), "s": tspec("fx_shopwin", 14)})

    # 3) Jalisco / Antique Mall / 4-Story S. H. Kress Art Deco Bldg (1401 19th St, SW 19th & K, fblk_172..175)!
    solid_block_building(780.0, -508.0, 858.0, -412.0, 30.0, STUCCO,
                         {"w": Fit("fn_jalisco", (1.2, 1.2)), "n": tspec("fx_shopwin", 14)})
    solid_block_building(860.0, -508.0, 938.0, -412.0, 22.0, STUCCO_DK,
                         {"n": Fit("fn_antiq")})
    solid_block_building(940.0, -508.0, 1036.0, -412.0, 50.0, STUCCO,
                         {"n": Fit("fn_kress", (1.2, 1.2)), "e": Fit("fn_kress", (1.2, 1.2))})
    prop(1036.0, -424.0, 18.0, 1040.0, -421.5, 46.0, "fn_kressbl",
         {"n": Fit("fn_kressbl"), "s": Fit("fn_kressbl")})

    # 4) The 18hundred (1800 Chester Ave: Brazilian Acai & Habibi's Hookah, fblk_179) + K St Parking Structure!
    solid_block_building(780.0, -668.0, 916.0, -558.0, 28.0, STUCCO,
                         {"w": Fit("fn_h1800", (1.4, 1)), "s": Fit("fn_h1800")})
    solid_block_building(924.0, -668.0, 1036.0, -558.0, 36.0, tspec("fn_garage", 20),
                         {"e": Fit("fn_garage", (3, 1)), "s": Fit("fn_garage", (3, 1))})
    solid_block_building(780.0, -818.0, 920.0, -740.0, 36.0, REDBRK,
                         {"n": tspec("fn_linos", 18), "w": tspec("fn_linos", 18)})

    # 5) East of K St (Mi Casa Home Furniture, The Mint Bar, Larry E. Reider Education Center)!
    solid_block_building(1106.0, -340.0, 1226.0, -234.0, 21.0, "bk_white",
                         {"s": Fit("fn_micasa"), "w": Fit("fn_micasa")})
    solid_block_building(1106.0, -508.0, 1226.0, -412.0, 20.0, STUCCO,
                         {"n": Fit("fn_mint"), "w": tspec("fn_garage", 20)})
    solid_block_building(1106.0, 12.0, 1226.0, 168.0, 58.0, STUCCO,
                         {"w": Fit("fn_woolw", (2, 2.5)), "s": Fit("fn_woolw", (2, 2.5))})
    solid_block_building(-414.0, -668.0, -364.0, 240.0, 20.0, STUCCO_DK)

    # Smooth-shaded 3D Golden Empire Transit ('GET bus') City Bus on Chester Ave near Buena Vista Museum (fblk_418)!
    fox_model("get_bus", 720.0, 168.0, 0.0, yaw=270, z_off=0.06,
              clip_box=(715.8, 149.0, 0.6, 724.2, 187.0, 10.2))

    # ==========================================================================
    # 4. STREET TREES, ORNAMENTAL LAMPS & DRIVEABLE / PARKED VEHICLES
    # ==========================================================================
    for px, py, ph in ((12.5, -110.0, 26), (12.5, -185.0, 28), (12.5, -270.0, 25),
                       (71.5, -135.0, 25), (71.5, -245.0, 27), (71.5, 185.0, 26), (71.5, 228.0, 24)):
        fan_palm(px, py, ph)

    for tx, ty, wtr in (
        (-128.0, -660.0, False), (-128.0, -616.0, False),           # Lush courtyard trees beside Padre & Clover!
        (-196.0, -672.0, False), (-156.0, -672.0, False),
        (270.0, -12.5, False), (315.0, -12.5, False),
        (465.0, -12.5, True), (535.0, -12.5, True), (615.0, -12.5, True),
        (475.0, -68.0, False), (555.0, -68.0, False), (635.0, -68.0, True),
        (355.0, -295.0, True), (413.0, -280.0, True), (696.0, -290.0, True),
        (772.0, 88.0, True), (772.0, 142.0, True),                  # Trees along Buena Vista Museum sidewalk
        (1040.0, -450.0, False), (1100.0, -450.0, False),           # K St trees near Kress & Woolworth's
    ):
        street_tree(tx, ty, 20.0, winter=wtr)

    for lx, ly, al in (
        (13.5, -150.0, "y"), (13.5, -290.0, "y"), (13.5, -620.0, "y"),
        (70.5, -195.0, "y"), (70.5, 145.0, "y"), (70.5, -620.0, "y"),
        (357.5, -140.0, "y"), (410.5, -250.0, "y"), (699.5, -220.0, "y"),
        (772.0, 56.0, "y"), (1042.0, -300.0, "y"),
    ):
        double_globe_lamp(lx, ly, al)

    vehicles = [
        (36.0, 250.0, 270, "sedan"),
        (48.0, -320.0, 90, "sedan"),
        (48.0, -630.0, 90, "sedan"),                # Sedan on H St outside Padre Hotel / Brimstone!
        (-58.0, -688.0, 0, "coupe"),                # Coupe outside Padre Hotel 1702 main entrance!
        (-178.0, -392.0, 0, "sedan"),               # Car outside The Nile Theater on 19th St!
        (268.0, -176.0, 180, "coupe"),
        (265.0, -532.0, 180, "truck"),
        (220.0, -578.0, 0, "coupe"),                # Driveable coupe inside 18th & Eye Parking Garage!
        (720.0, -310.0, 90, "sedan"),
        (960.0, -366.0, 135, "sedan"),              # Diagonal parked car outside Woolworth's Luncheonette!
    ]
    for vx, vy, vyaw, vkind in vehicles:
        ent("misc_vehicle_" + vkind, vx, vy, 0.2, angle=vyaw)

    # ==========================================================================
    # 5. NEIGHBORHOOD DEATHMATCH SPAWNS, WEAPONS, JETPACKS & PICKUPS
    # ==========================================================================
    nb_spawns = [
        (36.0, -356.0, 2.5, 90),                    # 19th & H looking North at Fox Tower
        (36.0, -700.0, 2.5, 125),                   # 18th & H looking NW at Padre Hotel!
        (-178.0, -366.0, 2.5, 270),                 # 19th St facing The Nile Theater!
        (36.0, 292.0, 2.5, 270),                    # 21st & H (Central Fire Station / Today Cleaners)
        (384.0, -40.0, 2.5, 180),                   # 20th & Eye (Dagny's Coffee / Jones Bldg)
        (720.0, 110.0, 2.5, 15),                    # Chester Ave facing Buena Vista Museum!
        (384.0, -360.0, 2.5, 90),                   # 19th & Eye (JIN Sushi / Art Center)
        (1068.0, -376.0, 2.5, 145),                 # 19th & K St facing Woolworth's Luncheonette!
        (748.0, -610.0, 2.5, 0),                    # Chester Ave facing The 18hundred!
        (225.0, -578.0, 16.0, 180),                 # 18th & Eye Garage Level 2 Overlook toward Padre!
    ]
    for sx, sy, sz, sang in nb_spawns:
        ent("info_player_deathmatch", sx, sy, sz, angle=sang)

    nb_items = [
        ("weapon_rocketlauncher", 225.0, -572.0, 56.0),     # 18th & Eye Garage Level 5 Rooftop!
        ("weapon_lightning", 200.0, -172.0, 1.8),           # Service St Lattice Tower plaza
        ("weapon_supernailgun", 1042.0, -346.0, 2.0),       # Outside Woolworth's Luncheonette (19th & K)!
        ("weapon_grenadelauncher", -172.0, 26.0, 2.0),      # Inside 1720 20th St open warehouse bay
        ("weapon_supershotgun", 772.0, 132.0, 2.0),         # Outside Buena Vista Museum!
        ("weapon_nailgun", -178.0, -405.0, 2.0),            # Under The Nile Theater marquee!
        ("item_armor2", 74.0, -674.0, 2.0),                 # Jetpack at NE 18th & H facing Padre Hotel!
        ("item_armor2", 352.0, -78.0, 2.0),                 # Jetpack at SW 20th & Eye
        ("item_armor2", 1042.0, -406.0, 2.0),               # Jetpack at SW 19th & K (Kress corner)!
        ("item_armorInv", 225.0, -574.0, 15.0),             # Red Armor on Garage Level 2
        ("item_armor1", -4.0, 232.0, 2.0),                  # Green Armor under Today Cleaners drive-thru
        ("item_health", 82.0, 148.0, 2.0),
        ("item_health", 196.0, -346.0, 2.0),                # Outside The Ovation Theatre
        ("item_health", 772.0, -610.0, 2.0),                # Outside The 18hundred on Chester
        ("item_rockets", 235.0, -572.0, 56.0),
        ("item_cells", 192.0, -172.0, 1.8),
        ("item_spikes", 1032.0, -346.0, 2.0),
        ("item_shells", 772.0, 140.0, 2.0),
    ]
    for iname, ix, iy, iz in nb_items:
        ent(iname, ix, iy, iz)
