"""Golden West Casino, 1001 S Union Ave (CA-99 BUS), Bakersfield, and the first 4400 ft of the street north of it: the map "goldenwest"
(segment 1 of 3; see make_union.py for union2 / union3). The casino parcel is hand-built from the aerials and photos (see gwbase.py
for the frame and the scale correction); the street, cross streets and buildings come from OpenStreetMap (gw_route.py).
Build: sh build_goldenwest.sh   ->  maps/goldenwest.bsp        usage: python make_goldenwest.py out/maps/goldenwest.map"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(HERE, "gwbase.py"), encoding="utf-8").read(), "gwbase.py", "exec"), globals())

# ============================================================================================ ground and hull
with unscaled():
    _hx0, _hx1, _hy0, _hy1 = HX0, HX1, HY0, HY1
    box(_hx0 - 1, _hy0 - 1, -3, _hx1 + 1, _hy1 + 1, -2, "bk_dirt")
    box(_hx0 - 1, _hy0 - 1, SKY_Z, _hx1 + 1, _hy1 + 1, SKY_Z + 1, "sky_bk")
    for x0, y0, x1, y1 in ((_hx0 - 1, _hy0 - 1, _hx0, _hy1 + 1), (_hx1, _hy0 - 1, _hx1 + 1, _hy1 + 1), (_hx0, _hy1, _hx1, _hy1 + 1),
                           (_hx0, _hy0 - 1, _hx1, _hy0)):
        box(x0, y0, -3, x1, y1, SKY_Z, "sky_bk")
    for x0, y0, x1, y1 in ((_hx0, _hy0, _hx0 + 4, _hy1), (_hx1 - 4, _hy0, _hx1, _hy1), (_hx0, _hy1 - 4, _hx1, _hy1), (_hx0, _hy0, _hx1, _hy0 + 4)):
        box(x0, y0, 0, x1, y1, SKY_Z, "clip")
    box(_hx0, _hy0, -2, _hx1, _hy1, 0, "gw_dirt", {"t": tspec("gw_dirt", 24)})                       # bare desert ground, the vacant lots round it


def paved(x0, y0, x1, y1, tex="gw_lot", z=0.0):
    box(x0, y0, z - 2, x1, y1, z + ROADZ * 0.5, tex, group="detail")


# ============================================================================================ S Union Ave (CA-99 BUS)
# x: stone wall 95, sidewalk 95-100.5, west carriageway (2 lanes) 100.5-125, red-brick median 126-136, east carriageway 138-160,
# east sidewalk 160-164. Two lane lines, white edge lines, the median curbs 0.5 ft. (zoom-20 aerial + photos 037-044)
UX = (100.5, 125.0)
UY_H = 520.0                                   # the hand-built stretch ends here; gw_route.py takes over
box(UX[0], HY0, 0, UX[1], UY_H, ROADZ, "gw_road", {"t": tspec("gw_road", 15)}, group="detail")
box(138, HY0, 0, 160, UY_H, ROADZ, "gw_road", {"t": tspec("gw_road", 15)}, group="detail")
box(125, HY0, 0, 126, UY_H, WALKZ, "bk_walk", group="detail")                                       # median curbs
box(136, HY0, 0, 138, UY_H, WALKZ, "bk_walk", group="detail")
box(126, HY0, 0, 136, UY_H, WALKZ, "gw_brick", {"t": tspec("gw_brick", 4)}, group="detail")        # the pink-red pavers
box(95, HY0, 0, 100.5, UY_H, WALKZ, "bk_walk", group="detail")
box(160, HY0, 0, 164, UY_H, WALKZ, "bk_walk", group="detail")
for _lx in (108.65, 116.8, 145.3, 152.7):
    with unscaled():
        lines_y(HY0, UY_H, _lx * K, "bk_wline", w=0.35, dash=(10, 30))
with unscaled():
    for _lx, _t in ((101.2, "bk_wline"), (124.4, "bk_yline"), (138.6, "bk_yline"), (159.4, "bk_wline")):
        lines_y(HY0, UY_H, _lx * K, _t, w=0.4)
    for y in range(int(HY0) + 12, int(UY_H) - 10, 28):                                              # palms on the median
        palm(131 * K, y, h=24 + (y // 28) % 3 * 3)
    for y0_ in range(int(HY0), int(UY_H), 60):
        box(131 * K - 5.5, y0_ + 6, WALKZ, 131 * K + 5.5, y0_ + 26, 3.0, "bk_hedge", group="detail")

# ============================================================================================ the casino parcel
LOT = (-72, -106, 95, 250)                     # x0 y0 x1 y1: the whole parking parcel (zoom-19 aerial)
paved(LOT[0], LOT[1], 95, 250)
paved(-100, 95, -72, 250)                      # the small west lot with its own stalls
# the low flagstone wall with the green iron fence on top along Union Ave (photo 043): 1.7 ft stone, iron to 5.7 ft
GATE = ((-61, -41), (60, 76))                 # two drives (y ranges): the lot entrance (pano 034/035: stone gate pillars) and the NE drive
segs = []
y = LOT[1]
for g0, g1 in GATE:
    segs.append((y, g0))
    y = g1
segs.append((y, LOT[3]))
for a, b in segs:
    if b - a < 1:
        continue
    box(94.6, a, 0, 96.3, b, 1.7, "gw_stone", {"e": tspec("gw_stone", 5), "w": tspec("gw_stone", 5), "t": "gw_stone"})
    box(94.9, a, 1.7, 95.1, b, 5.7, Fit("{gw_iron", ((b - a) / 5.3, 4 / 5.3)), group="fence")
    box(93, a, 0, 94.6, b, 2.6, "bk_hedge", group="detail")                                          # trimmed hedge inside the wall
for g0, g1 in GATE:
    for yy in (g0 - 2.6, g1):
        box(93.4, yy, 0, 96.6, yy + 2.6, 7.2, tspec("gw_stone", 3), {"t": "gw_stone"})                # white rubble gate pillars (photo 035)
        box(93.2, yy - 0.1, 7.2, 96.8, yy + 2.7, 7.6, "gw_trim")
        box(94.2, yy + 0.4, 7.6, 95.8, yy + 2.2, 9.0, "bk_white", group="detail")                     # the lamp globe
    lines_y(g0, g1, 97, "bk_wline", w=0.4)
    paved(95, g0, 101, g1)

# --- parking stripes (aerial 008): south lot: three double-stall bands with a planting island at each end; stalls 9 ft true wide
ST = 9 / K
for cx in (-31, 6, 51):
    for k in range(0, 13):
        lines_x(cx - 17, cx + 17, -25 - ST * k)
    lines_y(-94, -23, cx, w=0.3)
    for yi in (-20, -97):
        box(cx - 11, yi - 2, 0, cx + 11, yi + 2, 0.5, "bk_walk", {"t": "bk_lawn"}, group="detail")
for k in range(0, 14):                                                                               # east-edge stalls along the wall
    lines_x(80, 94, -24 - ST * k)
for k in range(0, 12):
    lines_x(-71, -60, -24 - ST * k)
for k in range(0, 13):                                                                               # north lot
    lines_x(-62, 24, 125 + ST * k, w=0.3)
for cx in (-42, 20):
    box(cx - 2, 120, 0, cx + 2, 200, 0.5, "bk_walk", {"t": "bk_lawn"}, group="detail")
for xx in range(-94, -73, 4):
    lines_y(100, 160, xx, w=0.3)

# --- the building (aerial 008/006, grid read at 7x). Walls: pale stucco, tan stone to 3 ft; roofs: terracotta tile
WALL_H = 13.0
TILE = tspec("gw_tile", 5)
exec(compile(open(os.path.join(HERE, "gw_casino.py"), encoding="utf-8").read(), "gw_casino.py", "exec"), globals())    # the rooms inside (gw_casino.py)


def walls(x0, y0, x1, y1, h, face="gw_stucco"):
    if (x0, y0, x1, y1) in CASINO_HOLLOW:                                                           # built as a room by build_casino()
        return
    box(x0, y0, 0, x1, y1, h, tspec("gw_stone" if face == "gw_stucco" else face, 6), {"t": "bk_roof"})
    for yy in (y0, y1):                                                                              # stone base course on the long sides
        pass


# west flat-roofed wing (white membrane roof, parapet, rooftop plant)
walls(-51, 9, -24, 78, 15)
walls(-51, 78, -7, 102, 15)
walls(-37, 102, -6, 113, 21)                                                                         # the taller white box at the back
for (a, b, c, d) in ((-51, 9, -50, 78), (-51, 77, -7, 78), (-8, 78, -7, 102), (-51, 101, -37, 102), (-51, 9, -24, 10)):
    prop(a, b, 15, c, d, 17.0, "bk_extwall", {"t": "bk_roof"})                                       # parapet
for ax_, ay_ in ((-40, 20), (-33, 45), (-44, 60), (-30, 90), (-20, 95), (-14, 84)):
    prop(ax_, ay_, 15, ax_ + 5, ay_ + 3.5, 18.5, "bk_beige", {"t": "bk_steel"})                       # roof-top units
# main hall and its roofs (terracotta). A: north-south gable x -24..-8; B: hip x -8..21; D: the north wing; E: the turret
walls(-24, 9, 21, 31, WALL_H)
walls(-24, 31, 21, 68, WALL_H)
walls(-6, 68, 14, 109, WALL_H - 1)
gable_rect(-24, 9, -8, 68, WALL_H, TILE, tspec("gw_wood", 4), pitch=0.9)
hip_rect(-8, 9, 21, 55, WALL_H, TILE, pitch=0.66, eave=1.6, ridge="x")
hip_rect(-6, 55, 14, 109, WALL_H - 1, TILE, pitch=0.8, eave=1.6, ridge="y")
# the round turret at (39, 39), radius 12.5: wall to 14 ft, then the cone
poly_box(circle(39, 39, 11.2), 0, 14, tspec("gw_stone", 6))
cone(39, 39, 12.6, 14, 34, TILE)
prop(38.5, 38.5, 34, 39.5, 39.5, 37.5, "bk_steel")                                                    # finial
# the east block: flat roof with a parapet and plant (aerial: two roof levels, the east one lighter)
walls(21, 9, 59, 31, WALL_H)
prop(21, 9, WALL_H, 59, 10, WALL_H + 2, "bk_extwall", {"t": "bk_roof"})
prop(58, 9, WALL_H, 59, 31, WALL_H + 2, "bk_extwall", {"t": "bk_roof"})
prop(26, 12, WALL_H, 32, 17, WALL_H + 3.2, "bk_beige", {"t": "bk_steel"})
prop(40, 16, WALL_H, 45, 21, WALL_H + 3.0, "bk_beige", {"t": "bk_steel"})
# eave trim, stone base, entrances (dark recesses at x 22-27 and x -14..-10 on the south face, aerial) and windows
for _a, _b in ((-24, -14.5), (-9.5, 21), (21, 21.7), (27.6, 59)):                                   # the stone base, open at the two doors (gw_casino.py)
    box(_a, 8.4, 0, _b, 9, 3, "gw_stone", {"s": tspec("gw_stone", 5)})
box(-51, 8.4, 0, -24, 9, 3, "gw_stone", {"s": tspec("gw_stone", 5)})
prop(21.5, 7.0, 8.5, 28.5, 9.2, 9.6, "gw_trim")                                                       # entrance canopy beam
build_casino()                                                                                        # card room, lobby, north wing, portico, plaza, statue
for xw in (-6, 0, 5, 10, 31, 37, 45, 52):
    prop(xw, 8.35, 3.2, xw + 3.2, 9, 8.0, "bk_darkwin", {"s": Fit("bk_darkwin")})                     # windows on the south face
box(2, 2, 0, 16, 7, 0.4, "bk_lawn", group="detail")                                                   # planter beds in front (aerial: hedge strips)
box(-10, 2, 0, 3, 7, 0.4, "bk_lawn", group="detail")
box(32, 2, 0, 60, 7, 0.4, "bk_lawn", group="detail")
box(-9, 2.5, 0.4, 3, 6.5, 2.6, "bk_hedge", group="detail")
box(33, 2.5, 0.4, 59, 6.5, 2.6, "bk_hedge", group="detail")
# the garden / drive east of the building (beige paving with palms, aerial)
paved(25, 52, 62, 108, "gw_dirt")
with unscaled():
    for px_, py_ in ((16, 85), (24, 75), (40, 95), (55, 70)):
        palm(px_ * K, py_ * K, h=14)

# --- the Golden West pylon (photo 043 / 036): purple post, rounded cap with the gold script, blue LED board.
# Triangulated from panoramas 034-036 and 042-044: just inside the wall near the south drive.
SX, SY = 84.0, -5.0
prop(SX - 0.8, SY - 1.7, 0, SX + 0.8, SY + 1.7, 12, "gw_trim")                                  # the thick purple post
extrude_x([(SY * K + dy, z) for dy, z in [(-4.2, 11), (4.2, 11), (4.2, 26.2), (3.3, 27.5), (-1.2, 27.5), (-3.4, 26.5), (-4.2, 24.6)]],
          SX * K - 0.75, SX * K + 0.75, "gw_pylon")
ent("light", SX, SY - 4, 14, light=160, _color="255 230 200")

# --- the neighbours (zoom-19 aerial 006, offsets (+32, +33) into this frame)
# (the blue-roof building south of the lot comes from OpenStreetMap now)
paved(16, -151, 92, -113, "bk_walk")                                                                  # the pale concrete pad east of it
paved(-72, -290, 94, -155)                                                                            # the used-car lot south of it
for k in range(0, 28):
    lines_y(-290, -158, -66 + k * 6.0, w=0.25)
DEAL_CARS = []                                                                                        # the used-car lot (parked() is defined below)
for i in range(0, 5):
    for j in range(0, 6):
        if rng.random() < 0.6:
            DEAL_CARS.append((-60 + i * 30 + rng.uniform(-3, 3), -175 - j * 20, 90, rng.choice(("sedan", "coupe", "van", "truck"))))
# (houses, Trinity Ave, Delaware St, the motels and RV parks come from OpenStreetMap: gw_route.py)
# street lamps (cobra heads) every 80 ft along the median, power poles along the west edge
with unscaled():
    for y in range(int(HY0) + 20, int(HY1), 90):
        prop(131 * K - 0.3, y - 0.3, 0, 131 * K + 0.3, y + 0.3, 30, "bk_steel")
        prop(131 * K - 9.5, y - 0.3, 30, 131 * K + 0.3, y + 0.3, 30.6, "bk_steel")
        ent("light", 131 * K - 8, y, 28, light=180, _color="255 240 210")
    for y in range(int(HY0) + 50, int(HY1), 100):                                                  # power poles along the west edge of the lots
        prop(-100 * K - 0.4, y - 0.4, 0, -100 * K + 0.4, y + 0.4, 34, "bk_pole")
        prop(-100 * K - 4, y - 0.2, 32, -100 * K + 4, y + 0.2, 32.5, "bk_pole")

# ============================================================================================ refinements (2nd pass)
def sprite_tree(x, y, height, kind="t2"):
    """Kenney CC0 foliage-pack sprite tree (two crossed see-through quads): the pepper trees of photos 043/036."""
    name, w, h = {"t1": ("{bk3_tree1", 86, 208), "t2": ("{bk3_tree2", 122, 208), "t3": ("{bk3_tree3", 109, 214)}[kind]
    wd = w * height / h
    f = Fit(name)
    box(x - wd / 2, y - 0.06, 0.5, x + wd / 2, y + 0.06, height, name, {"n": f, "s": f}, group="illus")
    box(x - 0.06, y - wd / 2, 0.5, x + 0.06, y + wd / 2, height, name, {"e": f, "w": f}, group="illus")
    prop(x - 0.4, y - 0.4, 0, x + 0.4, y + 0.4, min(8.0, height * 0.35), "bk_bark")


with unscaled():
    for tx, ty, th, tk in ((72, 46, 32, "t2"), (66, -22, 28, "t3"), (82, 74, 30, "t2"), (-58, 96, 26, "t1"), (-82, 140, 24, "t3")):
        sprite_tree(tx * K, ty * K, th, tk)
    # clipped shrubs inside the fence (photo 043: one every ~20 ft true) and globe lamps on posts outside the wall
    _gt = [(g0 * K, g1 * K) for g0, g1 in GATE]
    for y in range(int(LOT[1] * K) + 4, int(LOT[3] * K), 21):
        if any(g0 - 3 < y < g1 + 3 for g0, g1 in _gt):
            continue
        box(92.4 * K - 1.8, y, 0, 92.4 * K + 1.8, y + 3.0, 3.4, "bk_hedge", group="detail")
    for y in range(int(LOT[1] * K) + 8, int(LOT[3] * K), 38):
        if any(g0 - 4 < y < g1 + 4 for g0, g1 in _gt):
            continue
        prop(97.0 * K, y, 0, 97.0 * K + 0.4, y + 0.4, 9, "bk_steel")
        box(97.0 * K - 0.5, y - 0.4, 9, 97.0 * K + 0.9, y + 0.8, 10.2, "bk_white", group="detail")
    # the lot's tall light poles at the island ends (aerial: shadows of poles at the islands)
    for lx in (-31, 6, 51):
        for ly in (-20, -97):
            prop(lx * K - 0.3, ly * K - 0.3, 0.5, lx * K + 0.3, ly * K + 0.3, 30, "bk_steel")
            prop(lx * K - 3.2, ly * K - 0.2, 30, lx * K + 0.3, ly * K + 0.2, 30.6, "bk_steel")
            ent("light", lx * K - 3, ly * K, 28, light=190, _color="255 240 210")
    # parked cars: the vehicle models, one per dark shape in the aerial's south lot (zoom 20), about half of them
    CARS = {"sedan": (17.0, 6.8, 5.3), "coupe": (16.0, 6.9, 4.3), "truck": (19.6, 8.2, 7.5), "van": (18.6, 7.7, 7.8)}

    def parked(x, y, yaw, kind):
        L, W, H = CARS[kind]
        ent("misc_model", x, y, 0.2, mdl="progs/veh_%s.md3" % kind, angles="0 %d 0" % yaw, scale="1.0")
        hl, hw = (L / 2, W / 2) if yaw in (0, 180) else (W / 2, L / 2)
        box(x - hl, y - hw, 0.7, x + hl, y + hw, H, "clip")                  # clip box starts above the origin: a model whose origin is inside solid is lit black

    for x, y, yaw, kind in ((-38, -35, 0, "sedan"), (-24, -35, 180, "van"), (-38, -53, 0, "coupe"), (-24, -62, 180, "sedan"), (-38, -80, 0, "truck"),
                            (0, -35, 0, "coupe"), (12, -44, 180, "sedan"), (0, -62, 0, "sedan"), (12, -80, 180, "van"), (45, -44, 0, "sedan"),
                            (57, -71, 180, "coupe"), (87, -30, 90, "sedan"), (87, -57, 90, "truck"), (87, -78, 90, "coupe"), (-66, -45, 90, "sedan"),
                            (-66, -88, 90, "coupe"), (87, 12, 90, "sedan"), (87, 33, 90, "sedan"), (87, 52, 90, "coupe")):
        parked(x * K, y * K, yaw, kind)
    for x, y, yaw, kind in DEAL_CARS:
        parked(x * K, y * K, yaw, kind)

# ============================================================================================ the street (OpenStreetMap)
if not os.environ.get("GW_FAST"):                                                                    # GW_FAST=1: no street, for quick test builds
    with unscaled():
        exec(compile(open(os.path.join(HERE, "gw_route.py"), encoding="utf-8").read(), "gw_route.py", "exec"), globals())

# ============================================================================================ gameplay
for x, y, a in ((60, -60, 90), (-30, -60, 90), (112, -150, 90), (113, 120, 270), (-60, 150, 0), (10, 125, 270), (90, 60, 180),
                (60, -135, 90), (-62, 5, 270), (150, -40, 180)):
    ent("info_player_deathmatch", x, y, 2.2, angle=a)
if os.environ.get("GW_START"):                                   # test views: GW_START="x y z yaw" (feet)
    _sx, _sy, _sz, _sa = (float(v) for v in os.environ["GW_START"].split())
    ent("info_player_start", _sx, _sy, _sz, angle=int(_sa))
else:
    ent("info_player_start", 112, -20, 2.2, angle=90)
for name, x, y, z in (("weapon_supershotgun", 20, -50, 1), ("weapon_rocketlauncher", 45, 100, 1), ("weapon_nailgun", -45, -40, 1),
                      ("weapon_lightning", 128, 40, 1.8), ("item_armor2", 131, -100, 1.8), ("item_health", 90, -60, 1),
                      ("item_health", -20, 140, 1), ("item_shells", 5, -50, 1), ("item_spikes", 51, -60, 1), ("item_rockets", 112, 90, 1)):
    ent(name, x, y, z)
SPOTS = [("Golden West Casino, the south lot", 20, -60, 2.2, 90), ("Golden West: the entrance", 24, -8, 2.2, 90),
         ("S Union Ave in front of the casino", 112, 5, 2.2, 270), ("The pylon sign", 100, -25, 2.2, 180),
         ("The north lot", -20, 150, 2.2, 270), ("On the median", 131, 40, 2.2, 270)]
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
json.dump([{"name": n, "pos": [u(x * K, OX), u(y * K, OY), u(z)], "yaw": a} for n, x, y, z, a in SPOTS],
          open(os.path.join(os.path.dirname(os.path.abspath(out)), "goldenwest.spots.json"), "w"))
with open(out, "w") as f:
    f.write('{\n"classname" "worldspawn"\n"wad" "%s;goldenwest.wad;bklan3.wad;gwcasino.wad"\n"message" "Golden West Casino - S Union Ave, Bakersfield"\n' % WAD_BK)
    f.write('"skyname" "bklan_"\n"_minlight" "28"\n"_sunlight" "115"\n"_sunlight_mangle" "60 -52 0"\n'
            '"_sunlight_color" "1 0.94 0.8"\n"_sunlight2" "65"\n"_sunlight2_color" "0.62 0.8 1"\n"_sunlight_penumbra" "1"\n'
            '"_dirt" "1"\n"_dirtscale" "0.8"\n')
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    f.write('{\n"classname" "func_wall"\n' + "".join(GROUPS["fence"]) + "}\n")
    f.write('{\n"classname" "func_detail_illusionary"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))
if check_placed():
    sys.exit("spawns / items inside brushes")
print("wrote", out, len(GROUPS["world"]), "world +", len(GROUPS["detail"]), "detail +", len(GROUPS["fence"]), "fence,", len(ENTS), "entities")
