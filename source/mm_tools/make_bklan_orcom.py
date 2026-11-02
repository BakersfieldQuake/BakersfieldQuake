"""The ORCOM CONNECT LAN PARTY (December 2002, rebuilt from Orcom 2.mpg) merged into bklan as a real enterable
banquet-hall building on the east end of Larry's block (exec'd by make_bklan.py).

Site choice: SW corner parcel of Sumner St & Sonora St, hall interior at x = 360..436, y = 295..347 (shell x = 344..448,
y = 288..348). Chosen because:
  1. OpenStreetMap / Bakersfield GIS (bklan_osm.json) and the satellite aerials show this corner parcel is vacant paved
     ground with zero existing buildings, roads, rail tracks, or Street View hero facades.
  2. Its east porch (x = 448) meets the existing west concrete sidewalk of Sonora St (x = 448..460), so the hall's east
     vestibule and carved double doors open straight onto the street with zero rotation (kitchen = west, entrance = east,
     BAWLS banner + exit = south, "Computer" banner = north).
  3. A 22 ft paved alley separates its south wall (y = 288) from building #59 (y_max = 266.2), allowing the south EXIT
     vestibule (Orcom 2.mpg 1712 s) to open cleanly onto the alley as a second walkthrough route.
Note: Orcom 2.mpg is 100% indoor footage and never shows the venue's exterior or address; the outer stucco/block wrapper
and porch are clean architectural shell geometry without invented signage."""

ORCOM_X0, ORCOM_Y0 = 360, 295
OC_L, OC_W, OC_H = 76, 52, 10


def oc_tile(tex, ft):
    s = ft * U / TEXSIZE[tex][1]
    return "%s 0 0 0 %.5f %.5f" % (tex, s, s)


def oc_octagon(cx, cy, r, z0, z1, tex, group="detail"):
    if XF:
        cx, cy = _xf(cx, cy)
    P_ = [(u(cx + r * math.cos((k + .5) * math.pi / 4), OX),
           u(cy + r * math.sin((k + .5) * math.pi / 4), OY)) for k in range(8)]
    Z0, Z1 = u(z0), u(z1)
    s = "{\n"
    for i in range(8):
        a, b = P_[i], P_[(i + 1) % 8]
        s += face((a[0], a[1], Z0), (b[0], b[1], Z0), (a[0], a[1], Z0 + 64),
                  (b[1] - a[1], -(b[0] - a[0]), 0), "%s 0 0 0 1 1" % tex)
    s += face((P_[0][0], P_[0][1], Z1), (P_[3][0], P_[3][1], Z1), (P_[6][0], P_[6][1], Z1), (0, 0, 1), "%s 0 0 0 1 1" % tex)
    s += face((P_[0][0], P_[0][1], Z0), (P_[3][0], P_[3][1], Z0), (P_[6][0], P_[6][1], Z0), (0, 0, -1), "%s 0 0 0 1 1" % tex)
    GROUPS[group].append(s + "}\n")


_OC_CHR_SEQ = [0]
_OC_CHR_RING = (1, 1, 2, 1, 3, 1, 4, 1)   # mostly burgundy banquet chairs + BYOC executive/folding/task chairs


def oc_table(x, y, length=8, depth=2.5, top="bk_wood"):
    table(x, y, "x", length=length, depth=depth, z=ROADZ)


def oc_pc(x, y, facing, tower=True, z=2.5):
    pc(x, y, facing, z=ROADZ + 2.5, tower=tower)


def oc_chair(x, y, facing):
    idx = _OC_CHR_SEQ[0]
    _OC_CHR_SEQ[0] = idx + 1
    chair(x, y, facing, z=ROADZ, variant=_OC_CHR_RING[idx % len(_OC_CHR_RING)])


def oc_ficus(x, y, pedestal=0.0):
    zbase = ROADZ if pedestal == 0 else pedestal
    if pedestal:
        oc_octagon(x, y, 0.9, ROADZ, pedestal, "oc_white")
    oc_octagon(x, y, 0.8, zbase, zbase + 1.3, "bk_bark")
    prop(x - .15, y - .15, zbase + 1.3, x + .15, y + .15, zbase + 4, "bk_bark")
    for dx, dy, z0, r in ((0, 0, 3.4, 1.1), (.6, -.4, 4.3, .8), (-.5, .5, 4.9, .7), (.2, .3, 5.6, .55)):
        box(x + dx - r, y + dy - r, zbase + z0, x + dx + r, y + dy + r, zbase + z0 + r * 1.3, "bk_leaf", group="illus")


with placed(False, ORCOM_X0, ORCOM_Y0):
    L, W, H = OC_L, OC_W, OC_H
    T_OC = 1.0

    # --- Exterior building shell & sealed roof (blocks outdoor _sunlight from entering the hall) ---
    # Footprint in local coords: x = -16..88 (344..448 world, flush with Sonora St sidewalk at x=448), y = -7..53 (288..348 world)
    box(-16, -7, 0, 88, W + 1, ROADZ, "oc_floor", {"e": "bk_walk", "s": "bk_walk", "w": "bk_walk", "n": "bk_walk"})
    # Solid world roof slab from z=H (10 ft) to z=15 ft over the entire interior (hall, kitchen, exit corridor, vestibule)
    box(-16, -7, H, 85, W + 1, 15, "bk_roof", {"b": oc_tile("oc_ceiling", 4), "e": "bk_hstucco", "w": "bk_hstucco",
                                               "n": "bk_hstucco", "s": "bk_hstucco"})
    # East entry porch canopy (x = 85..88, over threshold from Sonora St sidewalk) + parapet round the roof
    box(85, 24, 9.5, 88, 36.5, 15, "bk_roof", {"b": "bk_hstucco", "e": "bk_hstucco", "n": "bk_hstucco", "s": "bk_hstucco"})
    for px0, py0, px1, py1 in ((-16, -7, -15, W + 1), (-16, W, 85, W + 1), (-16, -7, 85, -6), (84, -7, 85, 24),
                               (84, 36.5, 85, W + 1), (87, 24, 88, 36.5)):
        box(px0, py0, 15, px1, py1, 16.5, "bk_hstucco", {"t": "bk_btan"}, group="detail")
    # Porch columns on Sonora St sidewalk edge (x = 87.2..88) and warm porch soffit light
    for py0 in (24.2, 35.5):
        prop(87.0, py0, ROADZ, 88.0, py0 + 1.0, 9.5, "bk_hstucco")
    light(86.4, 30.2, 8.8, 130, "1 0.92 0.78")
    # Exterior masonry wainscot trim along the north, west, south and east outer walls
    prop(-16.15, -7, 0, -16, W + 1, 3.5, "bk_extwall")
    prop(-16, W + 1, 0, 85, W + 1.15, 3.5, "bk_extwall")
    prop(85, 36.5, 0, 85.15, W + 1, 3.5, "bk_extwall")
    prop(85, -7, 0, 85.15, 24, 3.5, "bk_extwall")

    # --- Hall main walls (world brushes so vis seals rooms cleanly) ---
    # North ("Computer" banner) wall
    box(-1, W, ROADZ, L + 1, W + 1, H, "oc_wall", {"n": "bk_hstucco"})
    # South (BAWLS) wall, with 4.0 ft opening at x = 55.8..59.8, z = ROADZ..7.4 for the south EXIT vestibule (55 s, 1712 s, 1880 s)
    box(-1, -1, ROADZ, 55.8, 0, H, "oc_wall", {"s": "bk_hstucco"})
    box(55.8, -1, 7.4, 59.8, 0, H, "oc_wall", {"s": "oc_wall"})
    box(59.8, -1, ROADZ, L + 1, 0, H, "oc_wall", {"s": "bk_hstucco"})
    # Fill the south-west & south-east exterior pockets (-16..-1 and -7..-1 outside the south exit vestibule)
    box(-16, -7, ROADZ, 54.5, -1, H, "bk_hstucco")
    box(-16, -1, ROADZ, -1, 3, H, "bk_hstucco")
    box(-16, 25, ROADZ, -1, W + 1, H, "bk_hstucco")
    box(62.5, -7, ROADZ, 85, -1, H, "bk_hstucco")
    box(L + 1, -1, ROADZ, 85, 25, H, "bk_hstucco")
    box(L + 1, 35.5, ROADZ, 85, W + 1, H, "bk_hstucco")

    # East wall with the vestibule opening (y = 26..34.5, z = ROADZ..8.5)
    box(L, 0, ROADZ, L + T_OC, 26, H, "oc_wall")
    box(L, 34.5, ROADZ, L + T_OC, W, H, "oc_wall")
    box(L, 26, 8.5, L + T_OC, 34.5, H, "oc_wall")

    # West wall: kitchen doorway (y = 7.4..11.2, 3.8 ft clear) and pass-through (y = 15..19, sill 3.75 ft, 2.5 ft tall)
    box(-T_OC, 0, ROADZ, 0, 7.4, H, "oc_wall")
    box(-T_OC, 7.4, 7.2, 0, 11.2, H, "oc_wall")
    box(-T_OC, 11.2, ROADZ, 0, 15, H, "oc_wall")
    box(-T_OC, 15, ROADZ, 0, 19, 3.75, "oc_wall", {"t": "oc_white"})
    box(-T_OC, 15, 6.25, 0, 19, H, "oc_wall")
    box(-T_OC, 19, ROADZ, 0, W, H, "oc_wall")
    box(0, 0, 9, 2.5, 43, H, "oc_wall", group="detail")                         # dropped soffit along the kitchen wall
    # Folding brown wood pass-through shutter stacked at north jamb (1122 s)
    prop(-0.15, 18.4, 3.75, 0.15, 19.0, 6.2, "oc_wood")

    # North-west jut with wide recessed EXIT doorway (718 s: orange-wood left panel + open dark alcove on right under EXIT)
    box(0, 43, ROADZ, 3, 45.2, H, "oc_wall")
    box(0, 50.8, ROADZ, 3, W, H, "oc_wall")
    box(0, 45.2, 7.3, 3, 50.8, H, "oc_wall")
    box(0, 45.2, ROADZ, 0.4, 50.8, 7.3, "bk_dark")                              # recessed hallway shadow
    prop(2.85, 48.0, ROADZ, 3.05, 50.8, 7.2, "oc_wood")                         # left orange-wood panel (718 s)
    prop(2.95, 45.0, 7.2, 3.12, 51.0, 7.45, "oc_white")
    prop(3.0, 47.1, 7.6, 3.35, 48.9, 8.2, "oc_white", {"e": Fit("oc_exit")})
    light(3.6, 48.0, 7.9, 14, "1 0.2 0.2")

    # --- Black vinyl cove base (~4 in tall) round the cream plaster walls (8 s, 1880 s) ---
    for bx0, by0, bx1, by1 in (
        (0, 0, 55.7, 0.05), (59.9, 0, L, 0.05),                                 # south wall
        (0, W - 0.05, L, W),                                                    # north wall
        (L - 0.05, 0, L, 7.9), (L - 0.05, 11.1, L, 26.0), (L - 0.05, 34.5, L, W),  # east wall
        (0, 0, 0.05, 7.3), (0, 11.3, 0.05, 43.0),                               # west wall
    ):
        box(bx0, by0, ROADZ, bx1, by1, ROADZ + 0.35, "oc_band", group="illus")

    # --- East entrance vestibule (x = 76..85, y = 25..35.5): carved double doors, one closed & one open to Sonora St ---
    box(L + T_OC, 25, ROADZ, 85, 26, 9.5, "oc_wall")
    box(L + T_OC, 34.5, ROADZ, 85, 35.5, 9.5, "oc_wall")
    # East wall of vestibule (x = 84..85) with 7.0 ft double-door opening at y = 26.8..33.8, z = ROADZ..7.4
    box(84, 26, ROADZ, 85, 26.8, 9.5, "oc_wall", {"e": "bk_hstucco"})
    box(84, 33.8, ROADZ, 85, 34.5, 9.5, "oc_wall", {"e": "bk_hstucco"})
    box(84, 26.8, 7.4, 85, 33.8, 9.5, "oc_wall", {"e": "bk_hstucco"})
    box(L + T_OC, 26, 8.5, 84, 34.5, H, oc_tile("oc_ceiling", 4))
    prop(77.5, 26, ROADZ, 83.5, 26.12, 8.2, "oc_white", {"n": Fit("oc_accordion")})
    # South carved leaf closed (y = 26.8..30.2); north carved leaf swung 90 deg open (3.6 ft clear walkthrough!)
    prop(83.85, 26.8, ROADZ, 84.15, 30.2, 7.35, "bk_chairbk", {"w": Fit("oc_carved"), "e": Fit("oc_carved")})
    prop(80.6, 33.65, ROADZ, 84.0, 33.85, 7.35, "bk_chairbk", {"s": Fit("oc_carved"), "n": Fit("oc_carved")})
    prop(83.8, 26.6, 7.35, 84.2, 34.0, 7.65, "bk_chairbk")
    for gx in (79, 82):
        box(gx - 1, 29.3, 8.42, gx + 1, 31.3, 8.5, "oc_grille", group="illus")
    light(80.5, 30.2, 7.6, 130, "1 0.98 0.92")

    # --- South EXIT vestibule/corridor (Orcom 2.mpg 55 s, 1712 s, 1880 s) opening out to the south alley ---
    # Corridor interior: x = 54.5..62.5, y = -6.2..-1.0, opening to south alley at x = 58.2..62.0, y = -7..-6.2
    box(54.5, -7, ROADZ, 58.2, -6.2, H, "oc_wall", {"s": "bk_hstucco"})
    box(58.2, -7, 7.4, 62.0, -6.2, H, "oc_wall", {"s": "bk_hstucco"})
    box(62.0, -7, ROADZ, 62.5, -6.2, H, "oc_wall", {"s": "bk_hstucco"})
    box(54.5, -6.2, 8.5, 62.5, -1.0, H, oc_tile("oc_ceiling", 4))
    # Cream steel panic-bar door (oc_exitdoor, 1880 s) swung open into the vestibule so both the door and corridor show
    prop(55.8, -4.6, ROADZ, 55.98, -1.0, 7.3, "oc_white", {"e": Fit("oc_exitdoor"), "w": Fit("oc_exitdoor")})
    # Exterior white panic-bar leaf swung open on east jamb, meter/locker bank on south wall, leaning white board + mat (1712 s)
    prop(61.82, -6.2, ROADZ, 62.0, -2.8, 7.3, "oc_white", {"w": Fit("oc_exitdoor"), "e": "oc_white"})
    prop(54.6, -6.15, ROADZ, 58.0, -5.9, 6.8, "oc_white", {"n": "oc_grille"})
    prop(54.8, -4.8, ROADZ, 55.1, -1.8, 3.2, "oc_white")                        # leaning white board (1712 s)
    box(56.2, -5.2, ROADZ, 59.8, -2.0, ROADZ + 0.03, "oc_bandgrey", group="illus")  # dark entry mat
    light(58.8, -3.6, 7.8, 95, "0.95 1 0.95")

    # --- Kitchen (west end, x = -15..-1, y = 3..25) ---
    box(-15, 3, ROADZ, -14, 25, 9.5, "oc_wall", {"e": "bk_white"})
    box(-15, 3, ROADZ, -1, 4, 9.5, "oc_wall", {"n": "bk_white"})
    box(-15, 24, ROADZ, -1, 25, 9.5, "oc_wall", {"s": "bk_white"})
    box(-14, 4, 9, -T_OC, 24, H, "bk_white")
    prop(-14, 18, ROADZ, -11.5, 21.5, 7, "bk_duct")
    prop(-6.5, 20.5, ROADZ, -3.8, 23, 3, "bk_steel")
    prop(-6.2, 20.8, 3, -4.2, 22.4, 4.2, "oc_white", {"w": "bk_glass"})
    for z in (0.4, 2.3, 4.3, 6.3):
        prop(-13, 4, z, -4, 5.5, z + .2, "bk_steel")
    for x in (-13, -4.2):
        prop(x, 4, ROADZ, x + .2, 5.5, 7, "bk_steel")
    prop(-2.5, 13.5, ROADZ, -T_OC, 20.5, 3.0, "oc_white")
    prop(-4.2, 7.25, ROADZ, -T_OC, 7.4, 7.1, "oc_wood")                         # kitchen door swung open
    light(-7, 14, 8.3, 210)

    # --- Wall fixtures & props ---
    # South wall: EXIT sign above doorway, OrCom/BAWLS banner, corrected cooler order (1880 s: red+box left/+x, white right/-x)
    prop(56.8, 0, 7.6, 58.8, 0.4, 8.2, "oc_white", {"n": Fit("oc_exit")})
    light(57.8, 0.8, 7.9, 14, "1 0.2 0.2")
    prop(61, 0, 4, 67, 0.08, 7, "oc_white", {"n": Fit("oc_bawls")})
    # Large white cooler on west/right side (x = 61.0..64.3), red cooler on east/left side (x = 64.6..67.2) with open BAWLS box
    prop(61.0, 0.4, ROADZ, 64.3, 2.3, 1.85, "oc_white", {"t": "oc_white"})
    prop(64.6, 0.4, ROADZ, 67.2, 2.2, 1.65, "oc_red", {"t": "oc_white"})
    prop(65.0, 0.6, 1.65, 66.7, 1.9, 2.55, "bk_crate", {"n": "oc_blue"})        # open BAWLS shipping box atop red cooler (1880 s)
    for z in (ROADZ, ROADZ + 0.8, ROADZ + 1.6):
        prop(52.6, 0.4, z, 55, 2.2, z + .8, "oc_blue")                          # stacked blue BAWLS cases west of exit door
    prop(69.6, 0, ROADZ, 75.6, 2, 4.4, "oc_oak", {"n": Fit("oc_case")})
    prop(75.3, 2.9, ROADZ, 75.5, 3.1, 8.2, "bk_steel")
    prop(72.3, 2.95, 4.6, 75.3, 3.05, 7.6, "oc_flag", {"n": Fit("oc_flag"), "s": Fit("oc_flag")})

    # East wall: honey-oak L counter, louvered closet door, switch plates, stepped portrait board + ficus, NE corner TV + ficus
    prop(67, 5, ROADZ, 69.5, 18, 3.4, "oc_oak")
    prop(69.5, 18, ROADZ, L, 20.5, 3.4, "oc_oak")
    prop(66.8, 4.8, 3.4, 69.7, 18.2, 3.6, "oc_oak")
    prop(69.5, 17.8, 3.4, L, 20.7, 3.6, "oc_oak")
    # Explodable 3D check-in admin rig & live tournament bracket CRT station on the honey-oak L-counter:
    pc(68.25, 8.35, "e", z=ROADZ + 3.62, mon_var=2, pc_var=4, skin=5)
    chair(71.4, 8.35, "w", "office", z=ROADZ, variant=2)
    pc(68.30, 12.65, "w", z=ROADZ + 3.62, mon_var=3, pc_var=2, skin=0)
    chair(71.4, 12.65, "w", "office", z=ROADZ, variant=4)
    for _scy in (38.0, 39.6, 41.2):
        chair(72.6, _scy, "w", z=ROADZ, variant=1)
    prop(67.8, 15.5, 3.6, 68.5, 16.2, 4.4, "bk_leaf", group="illus")
    prop(L - .12, 8, ROADZ, L, 11, 7, "oc_white", {"w": Fit("oc_louver")})
    prop(L - .1, 13, 4, L, 14.5, 6.2, "bk_steel")
    for k in range(3):
        prop(L - .05, 24.4 + k * .45, 4.3, L, 24.7 + k * .45, 4.8, "oc_white", group="illus")
    prop(L - .15, 37, 5, L, 42, 7.4, "oc_wood", {"w": Fit("oc_photos")})
    prop(L - .15, 38.7, 7.4, L, 40.3, 7.9, "oc_wood")                           # stepped center header on portrait plaque (726 s)
    oc_ficus(74.2, 35.9, pedestal=2.2)
    oc_ficus(74.2, 43.2, pedestal=2.2)
    oc_octagon(71.4, 48.4, 2.6, ROADZ, 2.45, "oc_white")
    prop(70.3, 46.6, 2.45, 72.6, 50.2, 6.6, "bk_chairbk", {"w": Fit("oc_tv")})
    prop(69.0, 47.4, 2.45, 69.8, 48.2, 2.75, "bk_leg")
    prop(69.0, 48.6, 2.45, 69.8, 49.3, 2.7, "bk_white")
    oc_ficus(74.6, 45.2)
    oc_ficus(67.6, 50.6)
    # Stack of spare burgundy banquet chairs near the NE wall (498 s)
    for sz in range(3):
        prop(65.0, 50.2, ROADZ + 1.45 + sz * 0.35, 66.5, 51.7, ROADZ + 1.65 + sz * 0.35, "oc_chair")
    prop(65.0, 51.6, ROADZ + 1.65, 66.5, 51.75, 3.7, "oc_chair")
    prop(65.05, 50.25, ROADZ, 65.15, 51.65, 2.2, "bk_steel")
    prop(66.35, 50.25, ROADZ, 66.45, 51.65, 2.2, "bk_steel")
    # Tournament bracket whiteboard on easel
    prop(63.9, 9.3, 3, 64.05, 13.3, 6, "oc_white", {"w": Fit("oc_whiteboard")})
    for ly in (9.6, 13.0):
        prop(64.05, ly, ROADZ, 64.2, ly + .15, 6.3, "oc_wood")
    prop(64.4, 11.2, ROADZ, 64.55, 11.35, 6.0, "oc_wood")

    # West wall: framed picture and clock above pass-through, gingham food table, blue round trash barrel
    prop(0, 14.3, 6.8, 0.1, 16.6, 8.4, "oc_wood", {"e": Fit("oc_picture")})
    prop(0, 18.0, 7.0, 0.1, 19.4, 8.4, "oc_white", {"e": Fit("oc_clock")})
    prop(0.5, 13, 2.35, 3, 21, 2.5, "oc_gingham", {k: Fit("oc_gingham") for k in "nsewt"})
    for ly in (13.6, 20.2):
        prop(0.7, ly, ROADZ, 2.8, ly + .15, 2.35, "bk_leg")
    oc_octagon(2, 23, 0.9, ROADZ, 2.6, "oc_blue")

    # North wall: "Computer RENAISSANCE" banner (684 s) and round white table
    prop(28, W - .08, 6.7, 38, W, 9.5, "oc_white", {"s": Fit("oc_computer")})
    oc_octagon(36, 44.5, 2.5, 2.35, 2.5, "oc_white")
    prop(35.9, 44.4, ROADZ, 36.1, 44.6, 2.35, "bk_leg")

    # --- Ceiling troffers (indoor fluorescent lighting, ~175; _dirt -1 keeps indoor lay-in ceiling clean) ---
    for tx in range(8, 69, 10):
        for y0 in (8, 22, 36):
            box(tx - 1, y0, H - .08, tx + 1, y0 + 8, H, "oc_troffer", {"b": Fit("oc_troffer")}, group="illus")
            light(tx, y0 + 4, H - 1.6, 175, "1 1 0.96", _dirt=-1)
    light(49, 4.5, 8.2, 65, "1 1 0.96", _dirt=-1)                                           # soft wash on BAWLS banner
    light(33, 47.5, 8.2, 65, "1 1 0.96", _dirt=-1)                                          # soft wash on Computer banner
    for gx, gy in ((13, 19), (33, 19), (53, 19), (13, 33), (33, 33), (53, 33), (23, 47), (63, 47), (43, 5)):
        box(gx - 1, gy - 1, H - .05, gx + 1, gy + 1, H, "oc_grille", group="illus")

    BX0, BY0, BX1, BY1 = 6, 6, 70, 46
    F0, F1 = ROADZ, ROADZ + 1 / U

    def oc_band(x0, y0, x1, y1, tex="oc_band"):
        box(x0, y0, F0, x1, y1, F1, tex, group="illus")

    oc_band(BX0, BY0, BX1, BY0 + .75)
    oc_band(BX0, BY1 - .75, BX1, BY1)
    oc_band(BX0, BY0, BX0 + .75, BY1)
    oc_band(BX1 - .75, BY0, BX1, BY1)
    oc_band(BX0 + .75, BY0 + .75, BX1 - .75, BY0 + 1.5, "oc_bandgrey")
    oc_band(BX0 + .75, BY1 - 1.5, BX1 - .75, BY1 - .75, "oc_bandgrey")
    oc_band(BX0 + .75, BY0 + 1.5, BX0 + 1.5, BY1 - 1.5, "oc_bandgrey")
    oc_band(BX1 - 1.5, BY0 + 1.5, BX1 - .75, BY1 - 1.5, "oc_bandgrey")
    cy_, cx_ = (BY0 + BY1) / 2, (BX0 + BX1) / 2
    oc_band(BX0 + 1.5, cy_ - .375, BX1 - 1.5, cy_ + .375)
    oc_band(cx_ - .375, BY0 + 1.5, cx_ + .375, BY1 - 1.5)
    for qx, qy in ((BX0 + 1.5, BY0 + 1.5), (BX1 - 6.5, BY0 + 1.5), (BX0 + 1.5, BY1 - 6.5), (BX1 - 6.5, BY1 - 6.5)):
        oc_band(qx, qy, qx + 5, qy + 5, "oc_bandgrey")
        oc_band(qx, qy, qx + 5, qy + .5)
        oc_band(qx, qy + 4.5, qx + 5, qy + 5)
        oc_band(qx, qy, qx + .5, qy + 5)
        oc_band(qx + 4.5, qy, qx + 5, qy + 5)

    # --- Rows of 8 ft LAN tables, beige CRTs/towers, and burgundy banquet chairs ---
    OC_EMPTY = {(1, 2), (3, 6), (4, 0), (2, 5), (5, 3)}

    def oc_station(row, k, x, y, facing, chair_y):
        if (row, k % 7) in OC_EMPTY and k % 3 == 1:
            model("soda_can", x, y, ROADZ + 2.5, facing)
        else:
            oc_pc(x, y, facing, tower=(k % 4 != 2))
        oc_chair(x, chair_y, "n" if facing == "s" else "s")

    for k, tx in enumerate(range(10, 66, 8)):
        oc_table(tx, W - 2.5)
        for j, dx in enumerate((1.35, 3.9, 6.45)):
            oc_station(0, k * 3 + j, tx + dx, W - 1.1, "s", W - 4.6)
    for k, tx in enumerate(range(6, 54, 8)):
        oc_table(tx, 0.1)
        for j, dx in enumerate((1.35, 3.9, 6.45)):
            oc_station(1, k * 3 + j, tx + dx, 1.2, "n", 4.7)
    for r, y0 in enumerate((14, 30)):
        for k, tx in enumerate(range(10, 66, 8)):
            oc_table(tx, y0)
            oc_table(tx, y0 + 2.5)
            for j, dx in enumerate((1.35, 3.9, 6.45)):
                oc_station(2 + r * 2, k * 3 + j, tx + dx, y0 + 1.15, "s", y0 - 2.3)
                oc_station(3 + r * 2, k * 3 + j, tx + dx, y0 + 3.85, "n", y0 + 7.3)
    # West head-of-aisle Tournament Dedicated Server Desk (compact 5.8-ft Honey-Oak lan_table4s):
    table(2.8, 29.5, "y", length=5.83, z=ROADZ, variant=5)
    pc(4.15, 31.1, "e", z=ROADZ + 2.5, mon_var=2, pc_var=2, skin=5)
    pc(4.15, 33.8, "e", z=ROADZ + 2.5, tower=True, mon_var=3, pc_var=4, skin=3)
    chair(6.9, 32.4, "w", "office", z=ROADZ, variant=4)
    model("soda_bottle", 3.5, 34.9, ROADZ + 2.5, "e", scale=1.5)

    # --- Deathmatch spawns & items inside ORCOM ---
    for sx_, sy_, sa_ in ((5, 8, 0), (5, 40, 0), (72, 27, 180), (79.5, 30, 180), (-8, 12, 0), (30, 25.5, 90),
                          (50, 25.5, 270), (20, 7.8, 0), (45, 44, 270), (60, 41.5, 180), (40, 7.6, 90), (68, 25.5, 180)):
        ent("info_player_deathmatch", sx_, sy_, 2.2, angle=sa_)
    for iname, ix, iy in (("weapon_supershotgun", 38, 25.5), ("weapon_nailgun", 6, 25), ("weapon_grenadelauncher", 66, 25),
                          ("weapon_rocketlauncher", -8, 11), ("item_armor2", 79.5, 28.2), ("item_health", 20, 25.5),
                          ("item_health", 56, 25.5), ("item_shells", 5.5, 40.5), ("item_spikes", 64, 44),
                          ("item_rockets", 38, 8), ("item_cells", 38, 42)):
        ent(iname, ix, iy, 1.1)


def oc_pt(x, y):
    return ORCOM_X0 + x, ORCOM_Y0 + y


ORCOM_SPOTS = [
    ("ORCOM CONNECT LAN PARTY", *oc_pt(72, 24.5), 2.2, 180),
    ("ORCOM: Entrance vestibule", *oc_pt(79.5, 30.0), 2.2, 180),
    ("ORCOM: BAWLS banner and exit", *oc_pt(58.0, 8.5), 2.2, 290),
    ("ORCOM: Counter and whiteboard", *oc_pt(64.5, 16.5), 2.5, 325),
    ("ORCOM: Dedicated Server Desk", *oc_pt(9.5, 32.4), 2.5, 180),
    ("ORCOM: Kitchen end", *oc_pt(6.0, 24.5), 2.2, 0),
    ("ORCOM: Entrance on Sonora St", 476, 325, 2.2, 180),
]
