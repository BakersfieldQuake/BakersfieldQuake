"""padre_hotel.py — Full 1:1 architectural & interior builder for The Padre Hotel
(1702 18th St, NW corner of 18th St & H St, Downtown Bakersfield) + Clover Ballroom wing.

Built from the 199 reference photos, iGUIDE floor plans, and video walkthrough in
padre-hotel-gallery-self-contained.html:
- Basement (z = -11.5 .. -1.5): 24-Hour Gym below Brimstone (2 treadmills, 1 elliptical,
  1 weight machine, full-wall mirrors; NO pool).
- Ground Floor (z = 0.5 .. 15.5): Grand Lobby (basketweave marble floor, cowgirl & oil-derricks
  mural behind fluted check-in desk, gold two-tier drum chandeliers, white marble grand staircase),
  Farmacy Cafe (spelled with F, pitchfork blade sign, pop-art wall, outdoor 18th St patio),
  Brimstone Bar & Lounge (glowing blue bar + TVs, communal high-top, booths, billiards).
- Clover Ballroom Wing (x = -232 .. -136, across the 20 ft west courtyard): Clover 2 (striped
  carpet, central pillar, cocktail tables, lighting truss) & Clover 1 (white arched banquet hall).
- Floor 2 (z = 16.5 .. 29.5): All iGUIDE rooms — Upper Lobby (PADRE HOTEL mat, gold-horseshoe
  wall, elevators), Stampede Room, Fox Room, Conference Room (wood walls, yellow chairs, linear
  pendants, TV), Fireside Room (dandelion mural, black table, NO fireplace) — opening directly
  onto the open-air Prairie Fire Rooftop Bar & Lounge (string lights, patio heaters, outdoor bar,
  Fox Theater sightline).
- Floor 4 (z = 42.5 .. 53.5): Damask hallway w/ oil-derrick art & north Fox-view window;
  Room 406 (2 queens, yellow headboards, pink pillow, open vanity + barn door), Double Deuce,
  Corner Pocket (18th & H corner + fire escape access), 40 Winks, Maverick.
- Floor 6 (z = 66.5 .. 77.5): Room 608 (king + bedroom-window shower w/ sheer curtain),
  Oil Baron Suite (charcoal panels, herringbone wood, Jacuzzi), Head Honcho Suite (corner views,
  Jacuzzi), Farmer's Daughter Suite (bright red walls/drapes, Jacuzzi, north Fox Tower view).
- Floor 8 Rooftop (z = 102.5): Walkable L-tower roof, angled red neon 'PADRE HOTEL' scaffold sign,
  north scaffold sign, Spanish parapets, SE fire escape ladder, and Jetpack / Rocket pickups.
"""
from __future__ import annotations
import math


# Basement Gym sub-grade cutout bounds (used by make_fox.py ground slab carver)
PADRE_SUB_X0, PADRE_SUB_X1 = -52.0, -4.0
PADRE_SUB_Y0, PADRE_SUB_Y1 = -658.0, -604.0


def build_padre_hotel(ctx: dict):
    box = ctx["box"]
    prop = ctx["prop"]
    prism = ctx["prism"]
    wall_x = ctx["wall_x"]
    wall_y = ctx["wall_y"]
    ent = ctx["ent"]
    light = ctx["light"]
    brush_ent = ctx["brush_ent"]
    tspec = ctx["tspec"]
    Fit = ctx["Fit"]
    fox_model = ctx["fox_model"]

    # Material specs
    STUCCO = tspec("pad_stucco", 10)
    BASE = tspec("pad_base", 10)
    NORTH_GRY = tspec("pad_north", 10)
    FRIEZE = tspec("pad_frieze", 8)
    WINBAY = tspec("pad_winbay", 12)
    WINLIT = tspec("pad_winlit", 12)
    LOBFLR = tspec("pad_lobflr", 8)
    EV_CARP = tspec("pad_evcarp", 8)
    CLOV_CARP = tspec("clov_carp", 8)
    RM_CARP = tspec("pad_rmcarp", 6)
    DAMASK = tspec("pad_damask", 6)
    # Exact Floor 2 height alignment (z = 16.5..29.5 -> Z = 198..354, 156u over 128px): white wainscoting sits on floor!
    DANDY = f"pad_dandy 0 {354.0 / (156.0 / 128.0):.3f} 0 {156.0 / 128.0:.5f} {156.0 / 128.0:.5f}"
    HSHOE = tspec("pad_hshoe", 8)
    CONF_WOOD = tspec("conf_wood", 8)
    BARON = tspec("pad_baron", 8)
    HERR = tspec("pad_herr", 6)
    FD_RED = tspec("pad_fdred", 8)
    JACUZ = tspec("pad_jacuz", 4)
    WOOD_FLR = tspec("fx_stageflr", 8)
    WHITE = "bk_white"
    DARK = "fx_drapeblk"
    TERRA = tspec("fx_terra", 6)
    TILE = tspec("fx_tile", 6)
    GLASS = "bk_glass"

    def view_win_x(xa, xb, y, zb, zt):
        """Real see-through hotel sash window along X: player-clip + exterior stucco casing + white muntin bars."""
        box(xa, y - 0.2, zb, xb, y + 0.2, zt, "clip")
        xm, zm = (xa + xb) / 2.0, (zb + zt) / 2.0
        prop(xa, y - 0.18, zm - 0.14, xb, y + 0.18, zm + 0.14, WHITE)
        prop(xm - 0.14, y - 0.18, zb, xm + 0.14, y + 0.18, zt, WHITE)
        prop(xa - 0.7, y - 0.9, zb - 0.7, xb + 0.7, y + 0.9, zb, STUCCO)
        prop(xa - 0.7, y - 0.9, zt, xb + 0.7, y + 0.9, zt + 0.7, STUCCO)
        prop(xa - 0.7, y - 0.9, zb, xa, y + 0.9, zt, STUCCO)
        prop(xb, y - 0.9, zb, xb + 0.7, y + 0.9, zt, STUCCO)

    def view_win_y(x, ya, yb, zb, zt):
        """Real see-through hotel sash window along Y: player-clip + exterior stucco casing + white muntin bars."""
        box(x - 0.2, ya, zb, x + 0.2, yb, zt, "clip")
        ym, zm = (ya + yb) / 2.0, (zb + zt) / 2.0
        prop(x - 0.18, ya, zm - 0.14, x + 0.18, yb, zm + 0.14, WHITE)
        prop(x - 0.18, ym - 0.14, zb, x + 0.18, ym + 0.14, zt, WHITE)
        prop(x - 0.9, ya - 0.7, zb - 0.7, x + 0.9, yb + 0.7, zb, STUCCO)
        prop(x - 0.9, ya - 0.7, zt, x + 0.9, yb + 0.7, zt + 0.7, STUCCO)
        prop(x - 0.9, ya - 0.7, zb, x + 0.9, ya, zt, STUCCO)
        prop(x - 0.9, yb, zb, x + 0.9, yb + 0.7, zt, STUCCO)

    # Helper for smooth walkable stairs along Y or X (each step is a crisp 0.9ft thick riser/tread block
    # so stacked multi-story switchbacks preserve full head clearance underneath!)
    def stairs_y(x0, x1, y_start, y_end, z_start, z_end, nsteps, tex, group="detail"):
        dy = (y_end - y_start) / nsteps
        dz = (z_end - z_start) / nsteps
        for i in range(nsteps):
            ya = y_start + i * dy
            yb = y_start + (i + 1) * dy
            za = z_start + i * dz
            zb = z_start + (i + 1) * dz
            z_lo, z_hi = (za - 0.4, zb) if dz > 0 else (zb - 0.4, za)
            box(x0, min(ya, yb), z_lo, x1, max(ya, yb), z_hi, tex, group=group)

    def stairs_x(x_start, x_end, y0, y1, z_start, z_end, nsteps, tex, group="detail"):
        dx = (x_end - x_start) / nsteps
        dz = (z_end - z_start) / nsteps
        for i in range(nsteps):
            xa = x_start + i * dx
            xb = x_start + (i + 1) * dx
            za = z_start + i * dz
            zb = z_start + (i + 1) * dz
            z_lo, z_hi = (za - 0.4, zb) if dz > 0 else (zb - 0.4, za)
            box(min(xa, xb), y0, z_lo, max(xa, xb), y1, z_hi, tex, group=group)

    def chandelier_drum(cx, cy, z_top):
        """Warm gold two-tier drum chandelier MD3 + warm downlight & ceiling uplight (Grand Lobby, padre_171)."""
        fox_model("pad_chand_drum", cx, cy, z_top - 3.6, yaw=0, z_off=0.0)
        light(cx, cy, z_top - 4.0, 275, "255 228 180")
        light(cx, cy, z_top - 0.8, 175, "255 236 202")

    def bed_unit(cx, cy, z0, orient="n", king=True, pink_pillow=False):
        """Smooth-shaded MD3 hotel bed with mustard-yellow tufted headboard, nightstands & warm lamp glow."""
        mname = "pad_bed_king" if king else "pad_bed_queen"
        hw = 3.0 if king else 2.3
        if orient == "s":
            fox_model(mname, cx, cy + 3.4, z0, yaw=90,
                      clip_box=(cx - hw, cy + 0.4, z0 + 0.5, cx + hw, cy + 6.6, z0 + 2.2))
            light(cx, cy + 1.8, z0 + 5.2, 135, "255 224 172")
        elif orient == "n":
            fox_model(mname, cx, cy - 3.4, z0, yaw=270,
                      clip_box=(cx - hw, cy - 6.6, z0 + 0.5, cx + hw, cy - 0.4, z0 + 2.2))
            light(cx, cy - 1.8, z0 + 5.2, 135, "255 224 172")
        elif orient == "e":
            fox_model(mname, cx - 3.4, cy, z0, yaw=180,
                      clip_box=(cx - 6.6, cy - hw, z0 + 0.5, cx - 0.4, cy + hw, z0 + 2.2))
            light(cx - 1.8, cy, z0 + 5.2, 135, "255 224 172")
        else:
            fox_model(mname, cx + 3.4, cy, z0, yaw=0,
                      clip_box=(cx + 0.4, cy - hw, z0 + 0.5, cx + 6.6, cy + hw, z0 + 2.2))
            light(cx + 1.8, cy, z0 + 5.2, 135, "255 224 172")

    # ==========================================================================
    # 0. SUB-GRADE BASEMENT GYM (z = -11.5 .. -1.5) — BELOW BRIMSTONE BAR (NO POOL!)
    # ==========================================================================
    # Sealed subterranean shell inside PADRE_SUB_X0..X1 (-52..-4), PADRE_SUB_Y0..Y1 (-658..-604)
    # Perimeter walls z = -11.5 .. 0.5
    box(-52.0, -658.0, -11.5, -50.0, -604.0, 0.0, WHITE)     # West basement wall
    box(-6.0, -658.0, -11.5, -4.0, -604.0, 0.0, WHITE)       # East basement wall
    box(-50.0, -658.0, -11.5, -6.0, -656.0, 0.0, WHITE)      # South basement wall
    box(-50.0, -606.0, -11.5, -6.0, -604.0, 0.0, WHITE)      # North basement wall
    # Gym rubber floor overlay
    box(-50.0, -656.0, -11.5, -6.0, -606.0, -11.2, DARK)
    # Basement ceiling / Floor 1 slab (-1.5 .. 0.5), leaving stairwell opening x = -50..-42, y = -630..-606!
    box(-42.0, -656.0, -1.5, -6.0, -606.0, 0.5, WHITE, {"t": WOOD_FLR, "b": WHITE})
    box(-50.0, -656.0, -1.5, -42.0, -630.0, 0.5, WHITE, {"t": LOBFLR, "b": WHITE})
    # Stairwell partition wall separating stair landing from gym with wide 8ft open entry at y=-616..-606
    box(-42.5, -632.0, -11.5, -41.5, -616.0, -1.5, WHITE)
    # Walkable Basement Stair: descends northward from Floor 1 (y=-628, z=0.5) to Basement landing (y=-610, z=-11.2)
    stairs_y(-49.8, -42.6, -628.0, -611.0, 0.5, -11.2, 18, TILE)
    # Guardrail around Floor 1 basement stair opening (open at south y=-628)
    prop(-50.0, -628.0, 0.5, -49.6, -606.0, 3.8, WHITE)
    prop(-42.4, -628.0, 0.5, -42.0, -606.0, 3.8, WHITE)
    prop(-50.0, -606.4, 0.5, -42.0, -606.0, 3.8, WHITE)

    # Full-wall gym mirror on east wall (padre_190.jpg)
    prop(-6.4, -650.0, -10.5, -6.0, -614.0, -3.0, WHITE, {"w": Fit("gym_mir", (3, 1))})
    # 4 recessed LED ceiling light panels
    for lx in (-32.0, -16.0):
        for ly in (-644.0, -622.0):
            prop(lx - 2.5, ly - 2.5, -1.7, lx + 2.5, ly + 2.5, -1.5, WHITE)
            light(lx, ly, -2.4, 210, "245 250 255")
    light(-46.0, -616.0, -3.0, 175, "255 244 224")

    # Exact gym equipment per padre_190.jpg: 2 Precor treadmills, 1 elliptical, 1 bike, 1 cable weight stack & watercooler (NO pool!)
    fox_model("pad_treadmill", -15.0, -646.0, -11.2, yaw=0,
              clip_box=(-18.0, -647.3, -10.8, -12.0, -644.7, -9.5))
    fox_model("pad_treadmill", -15.0, -638.0, -11.2, yaw=0,
              clip_box=(-18.0, -639.3, -10.8, -12.0, -636.7, -9.5))
    fox_model("pad_elliptical", -15.0, -629.5, -11.2, yaw=0,
              clip_box=(-18.0, -630.6, -10.8, -12.0, -628.4, -9.5))
    fox_model("pad_bike", -14.5, -621.5, -11.2, yaw=0,
              clip_box=(-16.2, -622.4, -10.8, -12.8, -620.6, -9.5))
    # Multi-station cable/stack weight machine in NW corner
    prop(-39.0, -653.0, -11.2, -33.5, -647.0, -4.2, "bk_steel")
    prop(-38.2, -652.2, -10.8, -34.3, -647.8, -6.5, DARK)
    prop(-36.8, -647.0, -10.2, -35.2, -644.5, -9.4, DARK)
    # Bottled water cooler against west gym partition
    fox_model("pad_watercooler", -39.5, -632.0, -11.2, yaw=0,
              clip_box=(-40.2, -632.7, -10.8, -38.8, -631.3, -8.0))

    # ==========================================================================
    # 1. GROUND FLOOR SHELL & EXTERIOR STOREFRONTS (z = 0.0 .. 16.5)
    # ==========================================================================
    # Ground floor footprint: x = -116 .. 0, y = -666 .. -556
    # Floor slab z = 0.0 .. 0.5 (leaving Basement Gym sub-box -52..-4, -658..-604 untouched!)
    box(-116.0, -666.0, 0.0, -52.0, -556.0, 0.5, LOBFLR)
    box(-52.0, -666.0, 0.0, 0.0, -658.0, 0.5, WOOD_FLR)
    box(-52.0, -604.0, 0.0, 0.0, -556.0, 0.5, LOBFLR)
    box(-4.0, -658.0, 0.0, 0.0, -604.0, 0.5, WOOD_FLR)
    # Surface carpets / floors inside Floor 1 zones (thin 0.06ft illus/detail overlays where distinct)
    box(-114.5, -664.5, 0.5, -76.0, -616.0, 0.56, TILE, group="illus")        # Farmacy tile floor
    box(-38.0, -664.5, 0.5, -1.5, -590.0, 0.56, WOOD_FLR, group="illus")      # Brimstone hardwood

    # --- Exterior Ground-Floor Walls (z = 0.5 .. 16.0) ---
    # South 18th St wall (y = -666 .. -664.5):
    #   Holes: Farmacy door (-101..-93), Main Padre Lobby Portal (-65..-53), Brimstone door (-21..-13)
    wall_x(-116.0, 0.0, -666.0, 1.5, 0.5, 16.0, BASE,
           holes=[(-101.0, -93.0, 0.5, 10.5), (-65.0, -53.0, 0.5, 11.5), (-21.0, -13.0, 0.5, 10.5)])
    # Storefront windows along 18th St:
    prop(-113.5, -666.2, 1.8, -102.0, -665.8, 10.5, BASE, {"s": Fit("farm_win")})   # Farmacy Cafe window!
    prop(-91.5, -666.2, 1.8, -79.5, -665.8, 10.5, BASE, {"s": Fit("farm_win")})
    prop(-47.0, -666.2, 2.2, -23.0, -665.8, 10.5, BASE, {"s": Fit("brim_win")})     # Brimstone 18th St window!
    prop(-11.5, -666.2, 2.2, -2.0, -665.8, 10.5, BASE, {"s": Fit("brim_win")})

    # 18th St Main Entrance Portal ('1702' + dark-blue 'THE PADRE' marquee canopy + Spanish curved gable above!)
    prop(-69.0, -667.2, 0.5, -65.0, -665.8, 16.0, BASE)
    prop(-53.0, -667.2, 0.5, -49.0, -665.8, 16.0, BASE)
    prop(-62.0, -666.8, 12.5, -56.0, -666.0, 14.7, BASE, {"s": Fit("pad_1702")})     # '1702' address plaque above canopy!
    prop(-68.0, -672.5, 10.6, -50.0, -666.0, 12.2, "pad_canopy",
         {"s": Fit("pad_canopy"), "w": "pad_canopy", "e": "pad_canopy", "b": DARK})
    light(-59.0, -669.0, 9.8, 220, "255 232 190")

    # 18th St Awnings: 2 tan-striped Farmacy awnings on left + blue/tan/blue Brimstone awnings on right (padre_028!)
    for ax0, ax1 in [(-114.5, -101.5), (-92.5, -78.5)]:
        prism([(ax0, -666.0), (ax1, -666.0), (ax1, -671.5), (ax0, -671.5)],
              [10.8, 10.8, 9.6, 9.6], [14.2, 14.2, 10.4, 10.4], tspec("pad_awntan", 6))
        prop(ax0, -671.8, 8.8, ax1, -671.4, 10.4, "pad_awntan", {"s": Fit("pad_awntan")})
    for ax0, ax1, atex in [(-48.0, -22.5, "pad_awnblu"), (-22.0, -12.5, "pad_awntan"), (-12.0, -0.5, "pad_awnblu")]:
        prism([(ax0, -666.0), (ax1, -666.0), (ax1, -671.2), (ax0, -671.2)],
              [10.8, 10.8, 9.6, 9.6], [14.2, 14.2, 10.4, 10.4], tspec(atex, 6))
        prop(ax0, -671.5, 8.8, ax1, -671.1, 10.4, atex, {"s": Fit(atex)})

    # Farmacy Cafe Outdoor Sidewalk Patio on 18th St (-115..-78, y=-675..-666.5, padre_186.jpg)
    box(-115.0, -675.0, 0.5, -78.0, -674.6, 3.2, "{pad_fesc", {"s": "{pad_fesc", "n": "{pad_fesc"}, group="fence")
    for px in (-110.0, -98.0, -85.0):
        prop(px - 1.4, -672.2, 0.5, px + 1.4, -669.4, 2.9, DARK)
        fox_model("pad_stool_yellow", px - 2.3, -670.8, 0.5, yaw=0)
        fox_model("pad_stool_yellow", px + 2.3, -670.8, 0.5, yaw=180)
    # Brimstone sidewalk barstools along 18th St (padre_028: yellow/orange Tolix metal stools!)
    for sx in (-42.0, -37.0, -32.0, -9.0, -5.0):
        fox_model("pad_stool_yellow", sx, -667.6, 0.5, yaw=90)

    # East H St wall (x = -1.5 .. 0.0, y = -666 .. -556):
    #   Holes: Brimstone SE door (-650..-642), H St 'THE PADRE' portal (-602..-592)
    wall_y(-1.5, 1.5, -666.0, -556.0, 0.5, 16.0, BASE,
           holes=[(-650.0, -642.0, 0.5, 10.5), (-602.0, -592.0, 0.5, 11.5)])
    for wy0, wy1 in [(-663.5, -651.5), (-640.5, -622.0), (-620.0, -604.0)]:
        prop(-0.2, wy0, 2.2, 0.2, wy1, 10.5, BASE, {"e": Fit("brim_win")})
    for wy0, wy1 in [(-589.0, -574.0), (-572.0, -558.5)]:
        prop(-0.2, wy0, 2.2, 0.2, wy1, 10.5, BASE, {"e": Fit("farm_win")})
    # H St 'THE PADRE' secondary marquee canopy + awnings (fblk_398.jpg!)
    prop(0.0, -604.0, 10.6, 5.5, -590.0, 12.0, "pad_canopy", {"e": Fit("pad_canopy"), "b": DARK})
    for ay0, ay1, atex in [(-664.5, -641.5, "pad_awnblu"), (-639.5, -605.5, "pad_awnblu"),
                           (-589.5, -557.5, "pad_awntan")]:
        prism([(0.0, ay0), (0.0, ay1), (4.8, ay1), (4.8, ay0)],
              [10.8, 10.8, 9.6, 9.6], [14.2, 14.2, 10.4, 10.4], tspec(atex, 6))
        prop(4.7, ay0, 8.8, 5.1, ay1, 10.4, atex, {"e": Fit(atex)})
    # Concrete sidewalk bollards along H St (fblk_398.jpg)
    for by in range(-662, -562, 14):
        prop(11.8, by - 0.5, 0.5, 12.8, by + 0.5, 3.3, STUCCO)

    # West courtyard wall (x = -116 .. -114.5) & North Wall St wall (y = -557.5 .. -556.0, grey fblk_110!)
    wall_y(-116.0, 1.5, -666.0, -556.0, 0.5, 16.0, NORTH_GRY,
           holes=[(-644.0, -634.0, 0.5, 10.5)])  # Courtyard doorway to Clover Ballroom!
    wall_x(-116.0, 0.0, -557.5, 1.5, 0.5, 16.0, NORTH_GRY,
           holes=[(-70.0, -58.0, 0.5, 10.5)])     # North Valet entrance on Wall St!

    # --- Floor 1 Interior Partitions, Columns, Furniture & Details ---
    # Partition between Farmacy Cafe (west) and Grand Lobby (center), with wide 14ft open arch (-646..-632)
    wall_y(-77.5, 1.5, -664.5, -616.0, 0.5, 15.5, WHITE, holes=[(-646.0, -632.0, 0.5, 12.5)])
    # Hanging wrought-iron pitchfork + tractor 'FARMACY CAFE' alpha-cutout blade sign projecting into Grand Lobby (padre_171.jpg!)
    box(-76.0, -631.6, 10.2, -71.4, -631.4, 13.6, "{farm_sign",
        {"s": Fit("{farm_sign"), "n": Fit("{farm_sign")}, group="fence")
    # Farmacy Cafe interior: wood coffered ceiling beam, dual pop-art canvases (padre_172.jpg), espresso counter, yellow stools & sofa nook!
    prop(-114.0, -664.0, 14.8, -78.0, -618.0, 15.5, CONF_WOOD)
    prop(-114.4, -659.0, 4.6, -113.8, -651.5, 12.1, DARK, {"e": Fit("farm_art")})
    prop(-114.4, -649.5, 4.6, -113.8, -642.0, 12.1, DARK, {"e": Fit("farm_art2")})
    prop(-112.0, -626.0, 0.56, -84.0, -621.0, 3.8, CONF_WOOD, {"t": DARK})       # Espresso & pastry counter
    for tx, ty in [(-106.0, -654.0), (-90.0, -654.0), (-105.0, -636.0)]:
        prop(tx - 1.8, ty - 1.8, 0.56, tx + 1.8, ty + 1.8, 2.8, CONF_WOOD)
        fox_model("pad_stool_yellow", tx - 2.7, ty, 0.56, yaw=0)
        fox_model("pad_stool_yellow", tx + 2.7, ty, 0.56, yaw=180)
    fox_model("pad_sofa_leather", -80.2, -625.5, 0.56, yaw=180,
              clip_box=(-81.5, -629.0, 0.9, -78.9, -622.0, 2.6))
    light(-96.0, -642.0, 13.5, 255, "255 230 185")

    # North Kitchen/Back-of-house partition wall at y = -617.5 closing Farmacy Cafe only (keeping Grand Lobby open!)
    box(-114.5, -617.5, 0.5, -76.0, -616.0, 15.5, WHITE)
    # Stepped Spanish Plaster Arch framing the Grand Lobby Check-In & Cowgirl Mural Alcove (padre_170 / 171.jpg!)
    prop(-76.0, -599.2, 0.5, -71.0, -597.8, 15.5, WHITE)
    prop(-52.0, -599.2, 0.5, -47.8, -597.8, 15.5, WHITE)
    prop(-71.0, -599.2, 13.4, -52.0, -597.8, 15.5, WHITE)
    prop(-71.0, -599.2, 11.6, -68.5, -597.8, 13.4, WHITE)
    prop(-68.5, -599.2, 12.6, -66.5, -597.8, 13.4, WHITE)
    prop(-56.5, -599.2, 12.6, -54.5, -597.8, 13.4, WHITE)
    prop(-54.5, -599.2, 11.6, -52.0, -597.8, 13.4, WHITE)
    # Grand Lobby focal north wall at y = -587.5 with Cowgirl & Oil-Derricks Mural + Black Fluted Front Desk!
    box(-76.0, -587.5, 0.5, -52.0, -585.5, 15.5, WHITE)
    prop(-70.0, -587.8, 1.5, -56.0, -587.4, 13.2, WHITE, {"s": Fit("pad_mural")})
    light(-63.0, -594.5, 12.6, 295, "255 232 188")
    prop(-68.5, -593.5, 0.5, -57.5, -590.2, 3.8, DARK, {"t": WHITE})             # Sleek black check-in desk
    # Grand Lobby white classical columns, two gold two-tier drum chandeliers & espresso leather club armchairs (padre_171.jpg!)
    for cx in (-74.0, -49.0):
        for cy in (-652.0, -632.0, -610.0):
            prop(cx - 1.2, cy - 1.2, 0.5, cx + 1.2, cy + 1.2, 15.5, WHITE)
    for lx, ly, lyaw in [
        (-70.2, -645.0, 20), (-70.2, -622.0, 340),
        (-53.2, -645.0, 160), (-53.2, -622.0, 200),
    ]:
        fox_model("pad_chair_club", lx, ly, 0.5, yaw=lyaw,
                  clip_box=(lx - 1.2, ly - 1.2, 0.85, lx + 1.2, ly + 1.2, 2.5))
    chandelier_drum(-61.5, -646.0, 15.5)
    chandelier_drum(-61.5, -616.0, 15.5)
    # Floor 1 Decorative white elevator doors on east lobby wall (padre_189.jpg)
    prop(-38.2, -604.0, 0.5, -37.6, -598.5, 9.2, WHITE, {"w": Fit("pad_elev")})
    prop(-38.2, -596.5, 0.5, -37.6, -591.0, 9.2, WHITE, {"w": Fit("pad_elev")})

    # Grand Lobby White Marble Staircase to Floor 2 (x = -42..-34, y = -654..-626 -> z = 0.5..16.5!)
    # Sits right beside Brimstone (padre_189.jpg!)
    stairs_y(-41.5, -34.5, -654.0, -626.0, 0.5, 16.5, 24, WHITE)
    prop(-42.0, -654.0, 0.5, -41.5, -626.0, 3.8, "{pad_fesc", {"w": "{pad_fesc", "e": "{pad_fesc"})
    prop(-34.5, -654.0, 0.5, -34.0, -626.0, 3.8, "{pad_fesc", {"w": "{pad_fesc", "e": "{pad_fesc"})

    # Brimstone Bar & Lounge (x = -34 .. -1.5, y = -664.5 .. -590.0, padre_188.jpg)
    # Dark wood columns, glowing blue backbar w/ TVs along north wall, wrap bar counter, fringe chandelier, white Tolix stools & pool table!
    for wcx in (-32.2, -9.5):
        prop(wcx - 0.9, -616.2, 0.56, wcx + 0.9, -614.4, 15.5, CONF_WOOD)
    prop(-30.0, -592.2, 1.5, -6.0, -590.5, 13.2, DARK, {"s": Fit("brim_bar", (2, 1))})
    prop(-30.0, -599.0, 0.56, -6.0, -595.5, 3.9, CONF_WOOD, {"t": DARK})          # Main bar counter
    for sx in range(-28, -6, 4):
        fox_model("pad_stool_white", sx, -600.8, 0.56, yaw=90)                    # White Tolix barstools!
    # Communal high-top table with white Tolix stools & 3-tier gold-fringe chandelier overhead (padre_188.jpg!)
    prop(-28.0, -638.0, 0.56, -22.0, -620.0, 3.6, CONF_WOOD)
    for sy in (-635.0, -629.0, -623.0):
        fox_model("pad_stool_white", -29.4, sy, 0.56, yaw=0)
        fox_model("pad_stool_white", -20.6, sy, 0.56, yaw=180)
    fox_model("pad_chand_fringe", -25.0, -629.0, 15.5 - 3.4, yaw=90, z_off=0.0)
    # Smooth-shaded 8-ft Billiards / Pool Table in SE corner
    fox_model("pad_pooltable", -10.5, -652.0, 0.56, yaw=90,
              clip_box=(-12.9, -656.2, 0.9, -8.1, -647.8, 2.9))
    light(-18.0, -606.0, 13.0, 235, "195 215 255")
    light(-25.0, -629.0, 11.6, 220, "255 220 168")
    light(-12.0, -648.0, 13.0, 225, "255 214 162")

    # ==========================================================================
    # 1B. CLOVER 1 & CLOVER 2 BALLROOM WING (x = -232 .. -136, y = -660 .. -608)
    # ==========================================================================
    # 20-ft Paved Courtyard between Padre West Wall (-116) and Clover Ballroom (-136)
    box(-136.0, -666.0, 0.0, -116.0, -556.0, 0.5, tspec("fn_brkpave", 6))
    light(-126.0, -638.0, 14.0, 200, "255 232 184")
    # Clover Ballroom floor, roof & Spanish clay-tile parapet
    box(-232.0, -660.0, 0.0, -184.0, -608.0, 0.5, TILE)                           # Clover 1 floor
    box(-184.0, -660.0, 0.0, -136.0, -608.0, 0.5, CLOV_CARP)                      # Clover 2 striped carpet!
    box(-232.0, -660.0, 16.0, -136.0, -608.0, 17.2, WHITE, {"t": STUCCO, "b": WHITE})
    for px0, py0, px1, py1 in [(-232.5, -660.5, -135.5, -659.0), (-232.5, -609.0, -135.5, -607.5),
                               (-232.5, -660.5, -231.0, -607.5), (-137.0, -660.5, -135.5, -607.5)]:
        prop(px0, py0, 17.2, px1, py1, 19.2, TERRA)

    # Clover exterior walls with wide playable doors (east to Padre courtyard, south to 18th St, west toward G St)
    wall_y(-137.5, 1.5, -660.0, -608.0, 0.5, 16.0, STUCCO, holes=[(-643.0, -631.0, 0.5, 10.5)])
    wall_x(-232.0, -136.0, -660.0, 1.5, 0.5, 16.0, STUCCO, holes=[(-164.0, -154.0, 0.5, 10.5)])
    wall_y(-232.0, 1.5, -660.0, -608.0, 0.5, 16.0, STUCCO, holes=[(-642.0, -632.0, 0.5, 10.5)])
    wall_x(-232.0, -136.0, -609.5, 1.5, 0.5, 16.0, STUCCO)
    # 3 Tall Spanish Arched Windows on Clover 1 south & west facades (padre_065 / fblk_087!)
    for wx in (-224.0, -208.0, -192.0):
        prop(wx - 4.5, -660.3, 1.5, wx + 4.5, -658.3, 14.5, STUCCO,
             {"s": Fit("clov_arch"), "n": Fit("clov_arch")})
    # Partition between Clover 2 (east) and Clover 1 (west) with wide 14ft open double doors
    wall_y(-185.0, 1.5, -658.5, -609.5, 0.5, 16.0, WHITE, holes=[(-641.0, -627.0, 0.5, 11.5)])
    # Clover 2: central white square pillar (iguide_62!), overhead steel lighting truss, brass chandeliers & banquet sets!
    prop(-161.5, -635.5, 0.5, -158.5, -632.5, 16.0, WHITE)
    box(-176.0, -648.0, 13.5, -144.0, -620.0, 14.3, "{fx_truss", group="fence")
    for cx, cy in [(-172.0, -648.0), (-148.0, -648.0), (-172.0, -620.0), (-148.0, -620.0)]:
        fox_model("pad_banquet_set", cx, cy, 0.5, yaw=15,
                  clip_box=(cx - 2.7, cy - 2.7, 0.85, cx + 2.7, cy + 2.7, 2.6))
    fox_model("pad_chand_brass", -172.0, -634.0, 16.0 - 3.2, yaw=0, z_off=0.0)
    fox_model("pad_chand_brass", -148.0, -634.0, 16.0 - 3.2, yaw=0, z_off=0.0)
    # Clover 1: white ceiling beams, projection screen on north wall, black classroom tables
    for by in (-648.0, -634.0, -620.0):
        prop(-230.5, by - 0.6, 14.8, -185.0, by + 0.6, 16.0, WHITE)
    prop(-216.0, -610.2, 4.5, -198.0, -609.5, 13.5, WHITE)                        # Projection screen
    for ty in (-648.0, -624.0):
        prop(-222.0, ty - 2.0, 0.5, -194.0, ty + 2.0, 2.6, DARK)
    light(-172.0, -634.0, 13.0, 240, "255 240 212")
    light(-148.0, -634.0, 13.0, 240, "255 240 212")
    light(-208.0, -634.0, 14.2, 275, "255 244 224")

    # ==========================================================================
    # 2. VERTICAL CORE: EXPRESS ELEVATOR & CONTINUOUS SWITCHBACK STAIRWELL
    #    Core zone: x = -52.0 .. -36.0, y = -586.0 .. -558.0 (runs z = 0.5 .. 103.5!)
    # ==========================================================================
    # Express Up-Lift Shaft: x = -51.0 .. -45.0, y = -585.0 .. -579.0 (open at F1, F2, F4, F6, F8!)
    # Express Down-Drop Shaft: x = -51.0 .. -45.0, y = -578.0 .. -572.0 (soft air-cushion landing!)
    box(-52.0, -586.0, 0.5, -51.0, -571.0, 109.5, WHITE)                           # Shaft west wall
    box(-51.0, -586.0, 0.5, -44.0, -585.0, 109.5, WHITE)                           # Shaft south wall
    box(-51.0, -579.0, 0.5, -44.0, -578.0, 108.5, WHITE)                           # Divider between UP & DOWN
    box(-51.0, -572.0, 0.5, -44.0, -571.0, 109.5, WHITE)                           # Shaft north wall
    # East face of shaft has doorways at z=0.5..10 (F1), 16.5..26 (F2), 42.5..51.5 (F4), 66.5..75.5 (F6), 102.5..109 (F8)!
    for zb, zt in [(10.0, 16.5), (26.0, 42.5), (51.5, 66.5), (75.5, 102.5)]:
        box(-45.0, -586.0, zb, -44.0, -571.0, zt, "pad_elev")
    # Updraft wind-tunnel inside UP shaft + gentle cushion pad at bottom of DOWN shaft
    prop(-50.8, -584.8, 0.5, -45.2, -579.2, 0.9, "fx_goldleaf")
    brush_ent("trigger_push", -50.8, -584.8, 1.0, -45.2, -579.2, 103.0, angles="-88 0 0", speed="720")
    prop(-50.8, -577.8, 0.5, -45.2, -572.2, 0.9, "pad_mat")
    brush_ent("trigger_push", -50.8, -577.8, 1.0, -45.2, -572.2, 16.0, angles="-90 0 0", speed="280")
    for lz in (8.0, 22.0, 48.0, 72.0, 98.0):
        light(-48.0, -582.0, lz, 160, "255 232 185")

    # Continuous Walkable Switchback Stairwell in x = -44.0 .. -34.0, y = -571.0 .. -557.5
    # Connects F2 (16.5) -> F4 (42.5) -> F6 (66.5) -> F8 Roof (102.5)!
    def build_switchback(z_lo, z_hi):
        z_mid = (z_lo + z_hi) * 0.5
        # West half rises north (y = -570 -> -561), north landing (-561..-557.5), east half rises south (-561 -> -570)
        stairs_y(-44.0, -39.2, -570.0, -561.0, z_lo, z_mid, 18, WHITE)
        box(-44.0, -561.0, z_mid - 0.8, -34.4, -557.5, z_mid, WHITE, group="detail")
        stairs_y(-39.2, -34.4, -561.0, -570.0, z_mid, z_hi, 18, WHITE)

    build_switchback(16.5, 42.5)
    build_switchback(42.5, 66.5)
    build_switchback(66.5, 84.5)
    build_switchback(84.5, 102.5)
    # Core landings connecting Elevator & Switchback Stair to each explorable floor!
    for z_land in (16.5, 42.5, 66.5, 84.5, 102.5):
        y_lo = -574.0 if z_land == 84.5 else -586.0
        box(-44.5, y_lo, z_land - 0.8, -34.4, -570.0, z_land, TILE, {"b": WHITE})

    # ==========================================================================
    # 3. FLOOR 2 — EVENT & MEETING ROOMS + PRAIRIE FIRE TERRACE (z = 16.5 .. 29.5)
    # ==========================================================================
    # Floor 2 Slab (z = 15.5 .. 16.5), leaving Grand Lobby Stair opening (-42.2..-33.8, -655..-625)
    # AND Core Elevator/Stair Shaft (-51.2..-34.4, -586..-557.5) cleanly open!
    box(-116.0, -666.0, 15.5, -51.2, -556.0, 16.5, EV_CARP, {"b": WHITE})
    box(-51.2, -666.0, 15.5, -42.2, -586.0, 16.5, EV_CARP, {"b": WHITE})
    box(-42.2, -666.0, 15.5, 0.0, -655.0, 16.5, EV_CARP, {"b": WHITE})
    box(-33.8, -655.0, 15.5, 0.0, -586.0, 16.5, EV_CARP, {"b": WHITE})
    box(-34.4, -586.0, 15.5, 0.0, -556.0, 16.5, EV_CARP, {"b": WHITE})
    box(-42.2, -625.0, 15.5, -33.8, -586.0, 16.5, TILE, {"b": WHITE})

    # --- Prairie Fire Outdoor Rooftop Bar & Lounge (NW Quadrant: x = -116..-52, y = -620..-556, z = 16.5) ---
    box(-115.0, -619.5, 16.5, -52.5, -557.0, 16.6, tspec("fx_stucco_dk", 8), group="illus")
    # Perimeter 3.8ft Spanish terrace parapet on West (x=-116) & North (y=-556) with open sky above!
    box(-116.0, -620.0, 16.5, -114.5, -556.0, 20.3, STUCCO, {"t": TERRA})
    box(-116.0, -557.5, 16.5, -52.0, -556.0, 20.3, STUCCO, {"t": TERRA})
    # Covered Prairie Fire Outdoor Bar on west side (padre_181 / 182 / 199!)
    prop(-114.5, -606.0, 16.6, -104.0, -574.0, 26.2, DARK)                         # Dark bar canopy roof
    prop(-114.2, -604.0, 18.0, -112.5, -576.0, 24.5, DARK, {"e": Fit("brim_bar", (2, 1))})
    prop(-108.5, -603.0, 16.6, -105.0, -577.0, 20.2, CONF_WOOD, {"t": DARK})       # Outdoor bar counter
    for sy in range(-600, -578, 5):
        fox_model("pad_stool_white", -103.2, sy, 16.6, yaw=180)
    # 3 Smooth-Shaded Glowing Bronze Mushroom Patio Heaters + Outdoor Lounge Tables & Stools (padre_174.jpg!)
    for hx, hy in [(-88.0, -604.0), (-72.0, -588.0), (-88.0, -570.0)]:
        fox_model("pad_heater", hx, hy, 16.6, yaw=0,
                  clip_box=(hx - 0.5, hy - 0.5, 17.0, hx + 0.5, hy + 0.5, 23.4))
        light(hx, hy, 22.6, 205, "255 188 112")
    for tx, ty in [(-92.0, -588.0), (-74.0, -606.0), (-72.0, -568.0)]:
        prop(tx - 1.8, ty - 1.8, 16.6, tx + 1.8, ty + 1.8, 19.1, DARK)
        fox_model("pad_stool_white", tx - 2.6, ty, 16.6, yaw=0)
        fox_model("pad_stool_white", tx + 2.6, ty, 16.6, yaw=180)
    # Overhead festoon string-light cables anchored between outdoor bar roof (-104.0) and East Wing wall (-53.5)!
    for sy in (-604.0, -590.0, -576.0):
        box(-104.0, sy - 0.05, 26.15, -53.5, sy + 0.05, 26.25, DARK, group="illus")
        for sx in range(-100, -56, 8):
            box(sx - 0.10, sy - 0.10, 25.88, sx + 0.10, sy + 0.10, 26.15, WHITE, group="illus")
        light(-79.0, sy, 25.4, 155, "255 224 168")
    # Prairie Fire -> 8th-Floor Rooftop Jump Pad on NW corner (-113..-107, -564..-558)
    prop(-113.0, -564.0, 16.6, -107.0, -558.0, 17.0, "fx_goldleaf")
    brush_ent("trigger_push", -113.0, -564.0, 17.0, -107.0, -558.0, 21.0, angles="-78 0 0", speed="1240")

    # --- Floor 2 Exterior L-Walls (z = 16.0 .. 30.5) ---
    # South 18th St 2nd-floor wall + Spanish curved Mission Gable over 1702 Entrance (padre_028.jpg!)
    box(-116.0, -666.0, 16.0, 0.0, -664.5, 30.5, STUCCO, {"s": WINBAY, "n": DANDY})
    prop(-69.0, -667.0, 16.0, -49.0, -665.8, 33.5, BASE, {"s": WINBAY})
    prop(-63.0, -667.4, 33.5, -55.0, -665.8, 37.5, FRIEZE)                         # Curved Spanish central gable!
    box(-116.5, -666.8, 28.5, 0.5, -665.5, 31.2, FRIEZE)                           # Sawtooth Spanish frieze band!
    # East H St 2nd-floor wall
    box(-1.5, -666.0, 16.0, 0.0, -556.0, 30.5, STUCCO, {"e": WINBAY, "w": DANDY})
    box(-0.5, -666.8, 28.5, 0.8, -555.5, 31.2, FRIEZE)
    # West & North walls enclosing Floor 2 indoor L-wing around Prairie Fire:
    #   West wall at x = -116 (y = -666 .. -620)
    box(-116.0, -666.0, 16.0, -114.5, -620.0, 30.5, STUCCO, {"w": WINBAY, "e": DANDY})
    #   North wall of South Wing facing Prairie Fire (y = -621.5 .. -620.0, x = -116 .. -52)
    wall_x(-116.0, -52.0, -621.5, 1.5, 16.5, 30.5, STUCCO,
           holes=[(-90.0, -82.0, 19.5, 27.0), (-68.0, -60.0, 19.5, 27.0)])
    #   West wall of East Wing facing Prairie Fire (x = -53.5 .. -52.0, y = -620 .. -556)
    #   with wide glass doorway (-608..-596) from Upper Lobby out onto Prairie Fire (padre_108.jpg)!
    wall_y(-53.5, 1.5, -620.0, -556.0, 16.5, 30.5, STUCCO,
           holes=[(-608.0, -596.0, 16.5, 26.5)])
    #   North wall of East Wing (y = -557.5 .. -556.0, x = -52 .. 0)
    box(-52.0, -557.5, 16.0, 0.0, -556.0, 30.5, STUCCO, {"n": WINBAY, "s": DANDY})

    # --- Floor 2 Interior iGUIDE Rooms ---
    # 1) Upper Lobby (x = -52..-30, y = -638..-586): PADRE HOTEL mat + gold-horseshoe dark wall + club armchairs
    box(-50.0, -614.0, 16.5, -36.0, -602.0, 16.58, Fit("pad_mat"), group="illus")
    prop(-52.0, -638.0, 16.5, -51.4, -622.0, 28.5, HSHOE, {"e": Fit("pad_hshoe", (2, 1))})  # Gold horseshoes wall (padre_084)!
    fox_model("pad_chair_club", -48.5, -598.0, 16.5, yaw=315,
              clip_box=(-49.7, -599.2, 16.9, -47.3, -596.8, 19.0))
    fox_model("pad_chair_club", -49.2, -625.0, 16.5, yaw=0,
              clip_box=(-50.4, -626.2, 16.9, -48.0, -623.8, 19.0))
    light(-42.0, -608.0, 27.5, 240, "255 236 204")

    # 2) Fireside Room (SW corner: x = -114.5..-78, y = -664.5..-636, padre_091..096 — NO fireplace!)
    wall_y(-78.0, 1.2, -664.5, -636.0, 16.5, 29.5, DANDY, holes=[(-646.0, -638.0, 16.5, 25.5)])
    wall_x(-114.5, -78.0, -636.0, 1.2, 16.5, 29.5, DANDY, holes=[(-100.0, -90.0, 16.5, 25.5)])
    prop(-106.0, -654.0, 16.5, -86.0, -648.0, 19.2, DARK)                          # Long black executive dining table
    for cx in (-103.0, -98.3, -93.7, -89.0):
        fox_model("pad_chair_yellow", cx, -655.6, 16.5, yaw=90)
        fox_model("pad_chair_yellow", cx, -646.4, 16.5, yaw=270)
    fox_model("pad_chand_brass", -96.0, -651.0, 29.5 - 3.2, yaw=0, z_off=0.0)
    light(-96.0, -651.0, 26.0, 245, "255 232 192")

    # 3) Conference Room (South center: x = -76.8..-53.5, y = -664.5..-638, padre_113..120!)
    wall_x(-76.8, -53.5, -638.0, 1.2, 16.5, 29.5, CONF_WOOD, holes=[(-68.0, -60.0, 16.5, 25.5)])
    wall_y(-53.5, 1.2, -664.5, -638.0, 16.5, 29.5, CONF_WOOD)
    prop(-71.0, -655.0, 16.5, -59.0, -649.0, 19.1, DARK)                           # Dark boardroom table
    for cx in (-69.5, -65.0, -60.5):                                               # Ribbed mustard rolling chairs!
        fox_model("pad_chair_yellow", cx, -656.6, 16.5, yaw=90)
        fox_model("pad_chair_yellow", cx, -647.4, 16.5, yaw=270)
    fox_model("pad_chair_yellow", -72.6, -652.0, 16.5, yaw=0)
    fox_model("pad_chair_yellow", -57.4, -652.0, 16.5, yaw=180)
    prop(-54.0, -655.2, 20.5, -53.5, -648.4, 24.5, DARK, {"w": Fit("pad_tv")})     # Wall flat-screen TV!
    fox_model("pad_chand_linear", -65.0, -652.0, 29.5 - 2.8, yaw=0, z_off=0.0)     # Brass/glass linear pendant!
    light(-65.0, -652.0, 25.8, 240, "255 240 208")

    # 4) Fox Room (East mid: x = -28..-1.5, y = -636..-598, padre_097..104)
    wall_y(-29.2, 1.2, -664.5, -598.0, 16.5, 29.5, DANDY,
           holes=[(-622.0, -610.0, 16.5, 25.5), (-656.0, -646.0, 16.5, 25.5)])
    wall_x(-29.2, -1.5, -598.0, 1.2, 16.5, 29.5, DANDY, holes=[(-19.0, -9.0, 16.5, 25.5)])
    for rx, ry in [(-18.0, -626.0), (-12.0, -608.0)]:
        fox_model("pad_banquet_set", rx, ry, 16.5, yaw=20,
                  clip_box=(rx - 2.7, ry - 2.7, 16.9, rx + 2.7, ry + 2.7, 19.1))
    fox_model("pad_chand_brass", -15.0, -618.0, 29.5 - 3.2, yaw=0, z_off=0.0)
    light(-15.0, -618.0, 26.0, 245, "255 234 196")

    # 5) Stampede Room (NE H St wing: x = -33.5..-1.5, y = -596.8..-557.5, padre_105..112)
    wall_y(-34.4, 1.0, -596.8, -557.5, 16.5, 29.5, DANDY, holes=[(-592.0, -582.0, 16.5, 25.5)])
    for rx, ry in [(-20.0, -584.0), (-11.0, -568.0), (-24.0, -568.0)]:
        fox_model("pad_banquet_set", rx, ry, 16.5, yaw=0,
                  clip_box=(rx - 2.7, ry - 2.7, 16.9, rx + 2.7, ry + 2.7, 19.1))
    fox_model("pad_chand_brass", -18.0, -576.0, 29.5 - 3.2, yaw=0, z_off=0.0)
    light(-18.0, -576.0, 26.0, 260, "255 234 196")

    # ==========================================================================
    # 4. STRUCTURAL INTERMEDIATE FLOORS 3, 5, 7 (Exterior 8-story window rhythm!)
    #    L-tower: South (-116..0, -666..-620) + East (-52..0, -620..-556),
    #    keeping Core (-51..-34.4, -585..-557.5) clear!
    # ==========================================================================
    def solid_ltower_band(z0, z1, lit=False):
        wtex = WINLIT if lit else WINBAY
        # South wing (-116 .. -52, -666 .. -620)
        box(-116.0, -666.0, z0, -52.0, -620.0, z1, STUCCO,
            {"s": wtex, "w": wtex, "n": wtex, "b": WHITE, "t": RM_CARP})
        # SE block (-52 .. 0, -666 .. -586)
        box(-52.0, -666.0, z0, 0.0, -586.0, z1, STUCCO,
            {"s": wtex, "e": wtex, "w": wtex, "b": WHITE, "t": RM_CARP})
        # NE block east of core (-34.4 .. 0, -586 .. -556)
        box(-34.4, -586.0, z0, 0.0, -556.0, z1, STUCCO,
            {"e": wtex, "n": wtex, "b": WHITE, "t": RM_CARP})
        # Thin outer closure west & north of core (-52..-51 and -51..-34.4 at y=-557.5..-556)
        box(-52.0, -586.0, z0, -51.0, -556.0, z1, STUCCO, {"w": wtex})
        box(-51.0, -557.5, z0, -34.4, -556.0, z1, STUCCO, {"n": wtex})

    solid_ltower_band(29.5, 42.5, lit=True)     # Floor 3 structural band
    solid_ltower_band(53.5, 66.5, lit=False)    # Floor 5 structural band
    solid_ltower_band(77.5, 102.5, lit=True)    # Floors 7-8 upper window bays below roof deck!

    # ==========================================================================
    # 5. FLOOR 4 — EXPLORABLE GUEST ROOMS FLOOR (z = 42.5 .. 53.5)
    #    Room 406, Double Deuce, Corner Pocket (fire escape!), 40 Winks, Maverick
    #    + Damask L-Hallway w/ Oil-Derrick Art & North Fox-View Window!
    # ==========================================================================
    Z4 = 42.5
    # Exterior Floor 4 walls with real transparent view windows + SE Fire Escape doorway (-18..-12, y=-666)!
    wall_x(-116.0, 0.0, -666.0, 1.5, Z4, Z4 + 11.0, STUCCO,
           faces={"s": WINBAY, "n": WHITE},
           holes=[(-102.0, -92.0, Z4 + 2.8, Z4 + 8.8), (-68.0, -58.0, Z4 + 2.8, Z4 + 8.8),
                  (-18.0, -11.0, Z4, Z4 + 8.8)])  # Walk-out fire escape opening in Corner Pocket!
    view_win_x(-102.0, -92.0, -665.3, Z4 + 2.8, Z4 + 8.8)
    view_win_x(-68.0, -58.0, -665.3, Z4 + 2.8, Z4 + 8.8)

    wall_y(-1.5, 1.5, -666.0, -556.0, Z4, Z4 + 11.0, STUCCO,
           faces={"e": WINBAY, "w": WHITE},
           holes=[(-656.0, -646.0, Z4 + 2.8, Z4 + 8.8), (-626.0, -616.0, Z4 + 2.8, Z4 + 8.8),
                  (-590.0, -580.0, Z4 + 2.8, Z4 + 8.8)])
    for wy0, wy1 in [(-656.0, -646.0), (-626.0, -616.0), (-590.0, -580.0)]:
        view_win_y(-0.7, wy0, wy1, Z4 + 2.8, Z4 + 8.8)

    box(-116.0, -666.0, Z4, -114.5, -620.0, Z4 + 11.0, STUCCO, {"w": WINBAY, "e": WHITE})
    wall_x(-116.0, -52.0, -621.5, 1.5, Z4, Z4 + 11.0, STUCCO,
           faces={"n": WINBAY, "s": DAMASK},
           holes=[(-96.0, -84.0, Z4 + 2.8, Z4 + 8.8)])                              # Overlooks Prairie Fire!
    view_win_x(-96.0, -84.0, -620.8, Z4 + 2.8, Z4 + 8.8)
    box(-53.5, -620.0, Z4, -52.0, -556.0, Z4 + 11.0, STUCCO, {"w": WINBAY, "e": DAMASK})
    # North end wall (y = -557.5..-556) with Hallway Fox-Tower View Window at x = -34..-26!
    wall_x(-52.0, 0.0, -557.5, 1.5, Z4, Z4 + 11.0, STUCCO,
           faces={"n": WINBAY, "s": DAMASK},
           holes=[(-33.5, -26.5, Z4 + 2.5, Z4 + 9.2)])
    view_win_x(-33.5, -26.5, -556.8, Z4 + 2.5, Z4 + 9.2)

    # L-Shaped Damask Hallway partitions:
    #   South corridor runs x = -114.5 .. -26.0 along y = -638.0 .. -630.0
    #   East corridor runs y = -638.0 .. -557.5 along x = -34.0 .. -26.0 (opening to Core at -585..-565!)
    wall_x(-114.5, -26.0, -639.0, 1.0, Z4, Z4 + 11.0, DAMASK,
           holes=[(-102.0, -95.0, Z4, Z4 + 8.5), (-68.0, -61.0, Z4, Z4 + 8.5), (-25.0, -18.0, Z4, Z4 + 8.5)])
    wall_y(-26.0, 1.0, -664.5, -557.5, Z4, Z4 + 11.0, DAMASK,
           holes=[(-654.0, -647.0, Z4, Z4 + 8.5), (-624.0, -617.0, Z4, Z4 + 8.5), (-590.0, -583.0, Z4, Z4 + 8.5)])
    wall_y(-34.4, 0.8, -630.0, -586.0, Z4, Z4 + 11.0, DAMASK)
    # Framed oil-derrick hallway pictures next to doors (padre_191.jpg)
    for ox, oy in [(-92.0, -638.0), (-58.0, -638.0)]:
        prop(ox - 1.5, oy - 0.1, Z4 + 4.5, ox + 1.5, oy + 0.2, Z4 + 7.5, WHITE, {"n": Fit("pad_oilart")})
    light(-76.0, -634.0, Z4 + 9.8, 200, "255 228 184")
    light(-30.0, -604.0, Z4 + 9.8, 200, "255 228 184")
    light(-30.0, -568.0, Z4 + 9.8, 190, "255 228 184")

    # Room 406 (SW: x = -114.5..-80, y = -664.5..-639): 2 queens w/ yellow headboards, open vanity + barn door, desk/TV & houndstooth chair!
    box(-80.0, -664.5, Z4, -79.0, -639.0, Z4 + 11.0, WHITE)
    for dx0, dx1 in [(-104.2, -102.0), (-92.0, -89.8)]:
        prop(dx0, -664.5, Z4 + 0.2, dx1, -664.2, Z4 + 9.6, "pad_curt_gy", {"n": Fit("pad_curt_gy")})
    bed_unit(-104.0, -664.2, Z4, orient="s", king=False, pink_pillow=True)
    bed_unit(-90.5, -664.2, Z4, orient="s", king=False, pink_pillow=False)
    prop(-114.0, -645.5, Z4, -108.0, -643.0, Z4 + 2.9, DARK, {"t": WHITE})          # Open vanity sink in bedroom!
    prop(-107.8, -647.0, Z4, -107.2, -641.5, Z4 + 8.2, BARON)                       # Sliding grey barn door!
    prop(-82.2, -656.5, Z4, -80.0, -651.0, Z4 + 2.6, CONF_WOOD)                     # Writing desk
    prop(-80.3, -655.8, Z4 + 3.8, -80.0, -651.7, Z4 + 6.5, DARK, {"w": Fit("pad_tv")})
    fox_model("pad_chair_hound", -83.2, -661.2, Z4, yaw=135,
              clip_box=(-84.3, -662.3, Z4 + 0.4, -82.1, -660.1, Z4 + 2.4))
    light(-97.0, -650.0, Z4 + 9.8, 220, "255 234 192")

    # Double Deuce (South mid: x = -79..-46, y = -664.5..-639): 2 queen beds + drapes + TV + houndstooth sitting area
    box(-46.0, -664.5, Z4, -45.0, -639.0, Z4 + 11.0, WHITE)
    for dx0, dx1 in [(-70.2, -68.0), (-58.0, -55.8)]:
        prop(dx0, -664.5, Z4 + 0.2, dx1, -664.2, Z4 + 9.6, "pad_curt_gy", {"n": Fit("pad_curt_gy")})
    bed_unit(-69.0, -664.2, Z4, orient="s", king=False)
    bed_unit(-55.5, -664.2, Z4, orient="s", king=False)
    prop(-46.3, -654.0, Z4 + 3.8, -46.0, -649.8, Z4 + 6.5, DARK, {"w": Fit("pad_tv")})
    fox_model("pad_chair_hound", -48.8, -660.5, Z4, yaw=145,
              clip_box=(-49.9, -661.6, Z4 + 0.4, -47.7, -659.4, Z4 + 2.4))
    light(-62.0, -650.0, Z4 + 9.8, 210, "255 234 192")

    # Corner Pocket (SE corner: x = -25..-1.5, y = -664.5..-638): Cal King + corner views + SE Fire Escape exit!
    box(-25.0, -639.0, Z4, -1.5, -638.0, Z4 + 11.0, WHITE)
    for wy0, wy1 in [(-656.0, -646.0), (-626.0, -616.0), (-590.0, -580.0)]:
        prop(-1.8, wy0 - 2.0, Z4 + 0.2, -1.5, wy0, Z4 + 9.6, "pad_curt_gy", {"w": Fit("pad_curt_gy")})
        prop(-1.8, wy1, Z4 + 0.2, -1.5, wy1 + 2.0, Z4 + 9.6, "pad_curt_gy", {"w": Fit("pad_curt_gy")})
    bed_unit(-1.8, -654.0, Z4, orient="e", king=True)
    fox_model("pad_chair_hound", -21.5, -642.5, Z4, yaw=315,
              clip_box=(-22.6, -643.6, Z4 + 0.4, -20.4, -641.4, Z4 + 2.4))
    light(-13.0, -651.0, Z4 + 9.8, 220, "255 234 192")

    # 40 Winks (-25..-1.5, -638..-602) & Maverick (-25..-1.5, -602..-557.5)
    box(-25.0, -603.0, Z4, -1.5, -602.0, Z4 + 11.0, WHITE)
    bed_unit(-1.8, -620.0, Z4, orient="e", king=True)
    bed_unit(-1.8, -582.0, Z4, orient="e", king=True)
    prop(-25.0, -622.5, Z4 + 3.8, -24.7, -618.0, Z4 + 6.5, DARK, {"e": Fit("pad_tv")})
    prop(-25.0, -578.5, Z4 + 3.8, -24.7, -574.0, Z4 + 6.5, DARK, {"e": Fit("pad_tv")})
    fox_model("pad_chair_hound", -21.5, -607.0, Z4, yaw=315,
              clip_box=(-22.6, -608.1, Z4 + 0.4, -20.4, -605.9, Z4 + 2.4))
    fox_model("pad_chair_hound", -21.5, -563.0, Z4, yaw=315,
              clip_box=(-22.6, -564.1, Z4 + 0.4, -20.4, -561.9, Z4 + 2.4))
    light(-13.0, -620.0, Z4 + 9.8, 210, "255 234 192")
    light(-13.0, -580.0, Z4 + 9.8, 210, "255 234 192")

    # ==========================================================================
    # 6. FLOOR 6 — ROOM 608 & LUXURY SUITES FLOOR (z = 66.5 .. 77.5)
    #    Room 608 (bedroom-window shower!), Oil Baron Suite, Head Honcho Suite,
    #    Farmer's Daughter Suite (crimson red walls + north Fox Theater view!)
    # ==========================================================================
    Z6 = 66.5
    # Exterior Floor 6 walls with real view windows + SE Fire Escape opening (-18..-11, y=-666)!
    wall_x(-116.0, 0.0, -666.0, 1.5, Z6, Z6 + 11.0, STUCCO,
           faces={"s": WINLIT, "n": BARON},
           holes=[(-98.0, -86.0, Z6 + 2.5, Z6 + 8.8), (-42.0, -30.0, Z6 + 2.5, Z6 + 8.8),
                  (-18.0, -11.0, Z6, Z6 + 8.8)])
    view_win_x(-98.0, -86.0, -665.3, Z6 + 2.5, Z6 + 8.8)
    view_win_x(-42.0, -30.0, -665.3, Z6 + 2.5, Z6 + 8.8)

    wall_y(-1.5, 1.5, -666.0, -556.0, Z6, Z6 + 11.0, STUCCO,
           faces={"e": WINLIT, "w": FD_RED},
           holes=[(-656.0, -644.0, Z6 + 2.5, Z6 + 8.8), (-598.0, -584.0, Z6 + 2.5, Z6 + 8.8)])
    view_win_y(-0.7, -656.0, -644.0, Z6 + 2.5, Z6 + 8.8)
    view_win_y(-0.7, -598.0, -584.0, Z6 + 2.5, Z6 + 8.8)

    box(-116.0, -666.0, Z6, -114.5, -620.0, Z6 + 11.0, STUCCO, {"w": WINLIT, "e": BARON})
    wall_x(-116.0, -52.0, -621.5, 1.5, Z6, Z6 + 11.0, STUCCO,
           faces={"n": WINLIT, "s": WHITE},
           holes=[(-102.0, -90.0, Z6 + 2.5, Z6 + 8.8)])
    view_win_x(-102.0, -90.0, -620.8, Z6 + 2.5, Z6 + 8.8)
    box(-53.5, -620.0, Z6, -52.0, -556.0, Z6 + 11.0, STUCCO, {"w": WINLIT, "e": DAMASK})

    # North wall of Floor 6: TWO panoramic Fox-Tower view windows — one in Hallway (-33.5..-26.5)
    # and one in Farmer's Daughter Suite (-22..-8, padre_144/clean.html)!
    wall_x(-52.0, 0.0, -557.5, 1.5, Z6, Z6 + 11.0, STUCCO,
           faces={"n": WINLIT, "s": FD_RED},
           holes=[(-33.5, -26.5, Z6 + 2.5, Z6 + 9.2), (-22.0, -8.0, Z6 + 2.2, Z6 + 9.2)])
    view_win_x(-33.5, -26.5, -556.8, Z6 + 2.5, Z6 + 9.2)
    view_win_x(-22.0, -8.0, -556.8, Z6 + 2.2, Z6 + 9.2)

    # Floor 6 L-Hallway (south corridor y=-639..-631, east corridor x=-34..-26)
    wall_x(-114.5, -26.0, -639.0, 1.0, Z6, Z6 + 11.0, DAMASK,
           holes=[(-82.0, -74.0, Z6, Z6 + 8.5), (-38.0, -30.0, Z6, Z6 + 8.5)])
    wall_x(-114.5, -52.0, -631.0, 1.0, Z6, Z6 + 11.0, DAMASK,
           holes=[(-94.0, -86.0, Z6, Z6 + 8.5)])
    wall_y(-26.0, 1.0, -639.0, -557.5, Z6, Z6 + 11.0, DAMASK,
           holes=[(-608.0, -600.0, Z6, Z6 + 8.5)])
    wall_y(-34.4, 0.8, -631.0, -586.0, Z6, Z6 + 11.0, DAMASK)
    light(-72.0, -635.0, Z6 + 9.8, 205, "255 228 184")
    light(-30.0, -600.0, Z6 + 9.8, 205, "255 228 184")

    # 1) Room 608 (x = -114.5..-78, y = -630..-621.5): King bed + Shower w/ Big Window & Sheer Curtain into Bedroom!
    box(-78.0, -630.0, Z6, -77.0, -621.5, Z6 + 11.0, WHITE)
    prop(-104.2, -621.8, Z6 + 0.2, -102.0, -621.5, Z6 + 9.6, "pad_curt_gy", {"s": Fit("pad_curt_gy")})
    prop(-90.0, -621.8, Z6 + 0.2, -87.8, -621.5, Z6 + 9.6, "pad_curt_gy", {"s": Fit("pad_curt_gy")})
    bed_unit(-106.0, -622.0, Z6, orient="n", king=True)
    fox_model("pad_chair_hound", -91.5, -624.2, Z6, yaw=220,
              clip_box=(-92.6, -625.3, Z6 + 0.4, -90.4, -623.1, Z6 + 2.4))
    # Shower stall in east end of Room 608 with window + {pad_shcur sheer curtain (padre_196/160)!
    prop(-86.0, -629.5, Z6, -78.5, -629.0, Z6 + 9.5, DARK)
    box(-86.5, -629.0, Z6 + 2.2, -86.0, -622.5, Z6 + 8.8, "{pad_shcur", group="fence")
    light(-96.0, -626.0, Z6 + 9.5, 210, "255 236 196")

    # 2) Oil Baron Suite (SW: x = -114.5..-54, y = -664.5..-639, padre_140..143):
    #    Charcoal paneling, herringbone dark wood floor, cognac Chesterfield sofa, sculpted silver-mosaic Jacuzzi tub!
    box(-114.2, -664.2, Z6, -54.5, -639.2, Z6 + 0.08, HERR, group="illus")
    box(-54.5, -664.5, Z6, -53.5, -639.0, Z6 + 11.0, BARON)
    for dx0, dx1 in [(-100.2, -98.0), (-86.0, -83.8)]:
        prop(dx0, -664.5, Z6 + 0.2, dx1, -664.2, Z6 + 9.6, "pad_curt_gy", {"n": Fit("pad_curt_gy")})
    bed_unit(-102.0, -664.2, Z6 + 0.08, orient="s", king=True)
    fox_model("pad_sofa_leather", -78.0, -655.5, Z6 + 0.08, yaw=90,
              clip_box=(-81.5, -656.9, Z6 + 0.5, -74.5, -654.1, Z6 + 2.6))
    fox_model("pad_jacuzzi", -61.5, -658.5, Z6 + 0.08, yaw=0,
              clip_box=(-65.6, -661.1, Z6 + 0.5, -57.4, -655.9, Z6 + 2.2))
    fox_model("pad_chand_brass", -84.0, -651.0, Z6 + 11.0 - 3.2, yaw=0, z_off=0.0)
    light(-84.0, -651.0, Z6 + 7.4, 240, "255 224 176")
    light(-61.5, -656.5, Z6 + 9.2, 185, "255 232 192")

    # 3) Head Honcho Suite (SE Corner: x = -53.5..-1.5, y = -664.5..-639, padre_150..153):
    #    Corner views + SE Fire Escape exit + yellow king bed + cognac sofa + sculpted Jacuzzi tub!
    box(-26.0, -639.0, Z6, -1.5, -638.0, Z6 + 11.0, WHITE)
    for dx0, dx1 in [(-44.2, -42.0), (-30.0, -27.8)]:
        prop(dx0, -664.5, Z6 + 0.2, dx1, -664.2, Z6 + 9.6, "pad_curt_gy", {"n": Fit("pad_curt_gy")})
    prop(-1.8, -658.2, Z6 + 0.2, -1.5, -656.0, Z6 + 9.6, "pad_curt_gy", {"w": Fit("pad_curt_gy")})
    prop(-1.8, -644.0, Z6 + 0.2, -1.5, -641.8, Z6 + 9.6, "pad_curt_gy", {"w": Fit("pad_curt_gy")})
    bed_unit(-44.0, -664.2, Z6, orient="s", king=True)
    fox_model("pad_sofa_leather", -28.0, -655.0, Z6, yaw=90,
              clip_box=(-31.5, -656.4, Z6 + 0.5, -24.5, -653.6, Z6 + 2.6))
    fox_model("pad_jacuzzi", -9.0, -643.5, Z6, yaw=0,
              clip_box=(-13.1, -646.1, Z6 + 0.5, -4.9, -640.9, Z6 + 2.2))
    fox_model("pad_chand_brass", -24.0, -651.0, Z6 + 11.0 - 3.2, yaw=0, z_off=0.0)
    light(-24.0, -651.0, Z6 + 7.4, 235, "255 232 188")

    # 4) Farmer's Daughter Suite (NE H St Wing: x = -25..-1.5, y = -638..-557.5, padre_144..149):
    #    Bold crimson red walls & velvet drapes, Rococo damask & gilded mirror feature wall, red tufted sofa, Jacuzzi tub & Fox view!
    box(-24.8, -637.8, Z6, -1.6, -557.8, Z6 + 0.08, HERR, group="illus")
    prop(-24.2, -557.8, Z6 + 0.2, -22.0, -557.5, Z6 + 9.8, "pad_curt_rd", {"s": Fit("pad_curt_rd")})
    prop(-8.0, -557.8, Z6 + 0.2, -5.8, -557.5, Z6 + 9.8, "pad_curt_rd", {"s": Fit("pad_curt_rd")})
    prop(-1.8, -600.2, Z6 + 0.2, -1.5, -598.0, Z6 + 9.8, "pad_curt_rd", {"w": Fit("pad_curt_rd")})
    prop(-1.8, -584.0, Z6 + 0.2, -1.5, -581.8, Z6 + 9.8, "pad_curt_rd", {"w": Fit("pad_curt_rd")})
    # Black & white Rococo damask accent wall w/ ornate gilded mirror behind red Chesterfield sofa (padre_149.jpg!)
    prop(-25.0, -596.0, Z6 + 0.4, -24.6, -582.0, Z6 + 10.2, DARK, {"e": Fit("pad_rococo")})
    bed_unit(-1.8, -572.0, Z6 + 0.08, orient="e", king=True, pink_pillow=True)
    fox_model("pad_sofa_red", -22.2, -589.0, Z6 + 0.08, yaw=0,
              clip_box=(-23.6, -592.5, Z6 + 0.5, -20.8, -585.5, Z6 + 2.6))
    fox_model("pad_jacuzzi", -18.5, -629.0, Z6 + 0.08, yaw=0,
              clip_box=(-22.6, -631.6, Z6 + 0.5, -14.4, -626.4, Z6 + 2.2))
    fox_model("pad_chand_brass", -13.5, -584.0, Z6 + 11.0 - 3.2, yaw=0, z_off=0.0)
    light(-13.0, -584.0, Z6 + 7.4, 245, "255 220 196")
    light(-13.0, -618.0, Z6 + 9.8, 225, "255 228 198")

    # ==========================================================================
    # 7. EXTERIOR ICONIC DETAILS: VERTICAL 'PADRE HOTEL' BLADE SIGN & SE FIRE ESCAPE
    # ==========================================================================
    # Vertical black neon 'PADRE HOTEL' blade sign on SE corner (Floors 4..7, padre_052 / 173!)
    prop(-2.2, -668.8, 44.0, -0.8, -666.0, 82.0, "pad_blade",
         {"w": Fit("pad_blade"), "e": Fit("pad_blade"), "s": DARK})
    prop(0.0, -664.2, 44.0, 2.8, -662.8, 82.0, "pad_blade",
         {"n": Fit("pad_blade"), "s": Fit("pad_blade"), "e": DARK})
    light(2.0, -667.5, 62.0, 210, "200 220 255")

    # Playable White Steel Fire Escape on South (18th St) facade at x = -20..-9 (padre_028.jpg!)
    # Connects Floor 4 (-18..-11), Floor 6 (-18..-11), and Floor 8 Roof (z=102.5) + drop/jump from 18th St!
    for fz in (30.5, 42.5, 54.5, 66.5, 78.5, 90.5):
        prop(-20.5, -670.5, fz - 0.4, -8.5, -666.0, fz, WHITE)
        box(-20.5, -670.5, fz, -8.5, -670.2, fz + 3.4, "{pad_fesc", group="fence")
    # Angled fire-escape stair flights linking 42.5 <-> 54.5 <-> 66.5 <-> 78.5 <-> 90.5 <-> 102.5!
    for z_a, z_b, dir_lr in [(42.5, 54.5, 1), (54.5, 66.5, -1), (66.5, 78.5, 1),
                             (78.5, 90.5, -1), (90.5, 102.5, 1)]:
        xa, xb = (-19.5, -9.5) if dir_lr > 0 else (-9.5, -19.5)
        stairs_x(xa, xb, -673.2, -670.5, z_a, z_b, 18, WHITE)
        box(-20.5, -673.5, z_a, -8.5, -673.2, z_b + 3.2, "{pad_fesc", group="fence")

    # ==========================================================================
    # 8. FLOOR 8 WALKABLE ROOFTOP DECK & RED NEON 'PADRE HOTEL' SCAFFOLD SIGNS
    # ==========================================================================
    ZR = 102.5
    # Penthouse Stair/Elevator Bulkhead (x = -52..-33.5, y = -586..-556, z = 102.5..111.5)
    box(-52.0, -586.0, ZR, -33.5, -585.0, ZR + 9.0, STUCCO)
    box(-52.0, -557.5, ZR, -33.5, -556.0, ZR + 9.0, STUCCO)
    box(-52.0, -586.0, ZR, -51.0, -556.0, ZR + 9.0, STUCCO)
    wall_y(-34.5, 1.0, -586.0, -556.0, ZR, ZR + 9.0, STUCCO,
           holes=[(-584.5, -568.0, ZR, ZR + 7.8)])                                   # Wide exit onto Roof Deck!
    box(-52.5, -586.5, ZR + 9.0, -33.0, -555.5, ZR + 10.2, TERRA)

    # Perimeter Spanish Revival Rooftop Parapet & Terracotta Tile Cornice (padre_173.jpg!)
    box(-116.5, -666.8, ZR - 2.2, 0.8, -665.5, ZR, FRIEZE)
    box(-0.5, -666.8, ZR - 2.2, 0.8, -555.5, ZR, FRIEZE)
    # 3.8ft safety parapet around entire L-roof (leaving fire-escape notch at x=-19..-10, y=-666!)
    wall_x(-116.0, 0.0, -666.0, 1.4, ZR, ZR + 3.8, STUCCO, holes=[(-19.5, -9.5, ZR, ZR + 3.8)])
    box(-1.4, -666.0, ZR, 0.0, -556.0, ZR + 3.8, STUCCO, {"t": TERRA})
    box(-116.0, -666.0, ZR, -114.6, -620.0, ZR + 3.8, STUCCO, {"t": TERRA})
    box(-116.0, -621.4, ZR, -52.0, -620.0, ZR + 3.8, STUCCO, {"t": TERRA})
    box(-53.4, -620.0, ZR, -52.0, -556.0, ZR + 3.8, STUCCO, {"t": TERRA})
    box(-33.5, -557.4, ZR, 0.0, -556.0, ZR + 3.8, STUCCO, {"t": TERRA})

    # Iconic SE Rooftop Red Neon 'PADRE HOTEL' Scaffold Sign (padre_173.jpg!)
    # Placed near SE corner (-38..-10, -661 & -6.6..-6, -658..-630, z = 106.3..122.3) facing South & East!
    box(-38.0, -661.0, ZR + 3.8, -10.0, -660.4, ZR + 19.8, "{pad_neon",
        {"s": Fit("{pad_neon"), "n": Fit("{pad_neon")}, group="fence")
    box(-6.6, -658.0, ZR + 3.8, -6.0, -630.0, ZR + 19.8, "{pad_neon",
        {"e": Fit("{pad_neon"), "w": Fit("{pad_neon")}, group="fence")
    # Supporting steel scaffold struts behind the rooftop signs
    for sx in (-34.0, -21.0, -8.0):
        prop(sx - 0.3, -660.4, ZR, sx + 0.3, -654.0, ZR + 16.0, "bk_steel")
    light(-21.0, -664.0, ZR + 12.0, 320, "255 76 52")
    light(-2.0, -646.0, ZR + 12.0, 320, "255 76 52")

    # Second North-Facing Rooftop 'PADRE HOTEL' Scaffold Sign facing Fox Theater (padre_173.jpg right!)
    box(-32.0, -558.5, ZR + 3.8, -4.0, -557.9, ZR + 18.8, "{pad_neon",
        {"n": Fit("{pad_neon"), "s": Fit("{pad_neon")}, group="fence")
    light(-18.0, -554.0, ZR + 12.0, 300, "255 76 52")

    # ==========================================================================
    # 9. PADRE HOTEL SPAWNS, WEAPONS, ARMOR / JETPACK & PICKUPS
    # ==========================================================================
    for sx, sy, sz, sang in [
        (-61.5, -632.0, 2.8, 90),       # Padre Grand Lobby facing Cowgirl Mural
        (-16.0, -626.0, 2.8, 90),       # Brimstone Bar & Lounge
        (-196.0, -634.0, 2.8, 0),       # Clover Ballroom
        (-82.0, -586.0, 18.8, 80),      # Prairie Fire Outdoor Terrace looking toward Fox Tower!
        (-96.0, -652.0, 44.8, 90),      # Room 406 (Floor 4)
        (-13.0, -598.0, 68.8, 90),      # Farmer's Daughter Suite (Floor 6)
        (-22.0, -644.0, 104.8, 78),     # Padre 8th-Floor Rooftop under Neon Sign!
    ]:
        ent("info_player_deathmatch", sx, sy, sz, angle=sang)

    for iname, ix, iy, iz in [
        ("weapon_supernailgun", -24.0, -620.0, -9.8),   # Basement 24-Hr Gym reward!
        ("weapon_supershotgun", -96.0, -638.0, 2.0),    # Farmacy Cafe
        ("weapon_grenadelauncher", -168.0, -634.0, 2.0),# Clover 2 Ballroom
        ("weapon_lightning", -80.0, -596.0, 18.0),      # Prairie Fire Terrace
        ("weapon_nailgun", -62.0, -650.0, 44.0),        # Floor 4 Guest Rooms
        ("weapon_rocketlauncher", -82.0, -646.0, 68.0), # Oil Baron Suite (Floor 6)
        ("item_armorInv", -13.0, -612.0, 68.0),         # Red Armor in Farmer's Daughter Suite!
        ("item_armor2", -22.0, -636.0, 104.0),          # Yellow Armor (Jetpack!) on Padre 8th-Floor Roof!
        ("item_armor1", -61.5, -604.0, 2.0),            # Green Armor in Grand Lobby
        ("item_health", -32.0, -638.0, -9.8),
        ("item_health", -38.0, -626.0, 18.0),
        ("item_health", -13.0, -650.0, 44.0),
        ("item_rockets", -28.0, -636.0, 104.0),
        ("item_cells", -86.0, -596.0, 18.0),
    ]:
        ent(iname, ix, iy, iz)
