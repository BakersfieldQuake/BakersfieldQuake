"""bklan3: the owner's review of bklan2 (video 2026-10-31 16:03). exec'd by make_bklan.py after make_bklan_v3.py, only
when BKLAN_V4=1 (with BKLAN_V3=1); build_bklan3.sh builds it as maps/bklan3.bsp. Like v3 it only adds brushes and
entities, or drops specific old ones by position. Small switches inside make_bklan.py / make_bklan_v3.py /
make_bklan_v3_cars.py read BKLAN_V4 too: the 500 ft sky, no jump pads closer than PAD_GAP, the office pads aimed
higher, the old teleport hubs left out (they are placed here), parked cars as exploding misc_vehicle_* entities.

What the video asked for (video m:ss; positions are the dev overlay's map feet):
  0:08-0:16  remove the Larry's lot teleport hub, put the teleports inside the units      -> warehouse pads
  0:17-0:36  the parked cars: the exploding vehicles, a majority of them                    -> make_bklan_v3_cars.py
  0:53       "remove these car pictures" (bk_darkwin: a photo with parked cars in it)     -> bk4_win
  1:04-1:31  118/120 behind the roll-ups: a full-blown warehouse with lots of racks        -> warehouse()
  1:22-2:45  the 120A room: a bedroom, CRT + computer, Mega Man sitting on the bed, still  -> bedroom()
  2:50-3:05  from the LAN lot you should be able to walk out to the street                 -> gap in the north wall
  3:09-3:21  the sky much higher (flew to ~290 ft)                                         -> SKY_Z 500
  3:24-4:44  vehicles driving a loop: E 21st, Sacramento, north street, Buck Owens, under  -> ROUTE, bk_cruiser x2
             the Sign, Manning St, the cul-de-sac, slowly through Amberton Park, back
  4:15-4:32  a trash can in the park that explodes in fire and shoots up into the sky      -> bk_trashcan
  4:48-6:35  the Podracer Sky-Chariot and the pink supercar drive it ("it's not pink", music)
  6:35-7:13  the F-69 Mouth-Breather biplane flies around, floats down, you jump on, up high -> bk_flyer
  7:13-7:38  never so many jump pads close together; pads high enough for the tall office  -> PAD_GAP, office pads
  7:38-7:54  "these teleports could be over here" (the Sign hub -> the tall office roof)    -> hubs
  7:54-8:18  drivable cars near Larry's, the Sign, the park, Manning St, some corners      -> misc_vehicle_van
Review 2 (video 2026-10-31 17:48, 2.4 min, in the web viewer):
  0:00-0:40  a coloured launch pad in the street at Larry's that flings you to the Bakersfield Sign  -> launch_pad() 1
  0:51-1:08  another at the Sign that flings you to Manning St                                     -> launch_pad() 2
  1:26-1:40  another at Manning St that flings you to the park                                     -> launch_pad() 3
  1:45-2:00  the trash can moved and made more defined; a pad there flings you back to the warehouse -> launch_pad() 4
  2:19       "I don't know how to get into these vans": H now works beside any free van, with a prompt -> vehicle_drive.qc
"""
WAD3 = "bklan3.wad;bklan4.wad"            # worldspawn "wad" (relative, qbsp runs in out/maps)
with open(os.path.join(HERE, "out", "maps", "bklan4.wad"), "rb") as _f:
    _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
    _f.seek(_ofs)
    _dirs = [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]
    for _pos, _, _, _, _, _, _name in _dirs:
        _f.seek(_pos)
        _nm, _w, _h = struct.unpack("<16s2I", _f.read(24))
        TEXSIZE[_name.split(b"\0")[0].decode()] = (_w, _h)

V4_SPOTS = []


def _drop_ents(pred):
    """Remove entities (by classname and origin in feet) that pred(classname, x, y, z) picks; returns how many."""
    keep, n = [], 0
    for s in ENTS:
        m = re.search(r'"classname" "([^"]+)"', s)
        o = re.search(r'"origin" "(-?\d+) (-?\d+) (-?\d+)"', s)
        if m and o and pred(m.group(1), int(o.group(1)) / U + OX, int(o.group(2)) / U + OY, int(o.group(3)) / U):
            n += 1
        else:
            keep.append(s)
    ENTS[:] = keep
    return n


import re  # noqa: E402

# ---------------------------------------------------------------------------------------------- the warehouse (118/120)
# The seven narrow units behind the roll-ups and the solid block behind them become one warehouse hall:
# x -228.3 .. -143.7 (the inside of B76), y 60.7 .. 186.3, plus the strip behind the south roll-ups (x > -183.3).
WX0, WX1 = B76[0] + T, B76[2] - T
WY0, WY1 = B76[1] + T, B76[3] - T
BED_X1, BED_Y1 = -183.33, 60.7                       # the 120A room (the bedroom) is x < BED_X1, y < BED_Y1
_n = drop("world", lambda b: inside(b, WX0 - 0.1, BED_Y1 - 0.1, BED_X1 + 0.1, WY1 + 0.1, -0.1, WALL_H + 0.05))   # the solid fill
_n += drop("world", lambda b: inside(b, BED_X1 - 0.5, WY0 - 0.1, WX1 + 0.05, WY1 + 0.1, -0.1, WALL_H + 0.05))  # partitions, back wall, car clips
_n += drop("detail", lambda b: inside(b, BED_X1 - 0.5, WY0 - 0.1, WX1 + 0.05, WY1 + 0.1, -0.1, WALL_H + 0.05))  # unit floors, racks, crates, lights
_n += _drop_ents(lambda c, x, y, z: c in ("misc_model", "misc_vehicle_sedan", "misc_vehicle_coupe", "misc_vehicle_van",
                                           "misc_vehicle_truck") and BED_X1 - 0.5 < x < WX1 and WY0 < y < WY1)
box(WX0, BED_Y1, 0, WX1, WY1, ROADZ, "bk_floor", group="detail")
box(BED_X1, WY0, 0, WX1, BED_Y1, ROADZ, "bk_floor", group="detail")
joists(WX0, WX1, BED_Y1, WY1)
joists(BED_X1, WX1, WY0, BED_Y1)
# the bedroom's east wall (the units' back wall used to be it), with a doorway into the warehouse
box(BED_X1 - 0.67, WY0, 0, BED_X1, 44, WALL_H, "bk_wall")
box(BED_X1 - 0.67, 48, 0, BED_X1, BED_Y1, WALL_H, "bk_wall")
box(BED_X1 - 0.67, 44, 7.2, BED_X1, 48, WALL_H, "bk_wall")
prop(BED_X1 - 0.75, 43.8, 0, BED_X1 + 0.08, 44, 7.3, "bk_wood")                   # door frame
prop(BED_X1 - 0.75, 48, 0, BED_X1 + 0.08, 48.2, 7.3, "bk_wood")
prop(BED_X1 - 0.75, 43.8, 7.2, BED_X1 + 0.08, 48.2, 7.4, "bk_wood")
# pallet racks ("full-blown warehouse with lots of bars"): five rows along the hall, a cross aisle in the middle
_RACKS = ("rack_composition_a04", "rack_composition_a05", "rack_bulk_storage_a03", "rack_composition_a04")
_nr = 0
for _k, _rx in enumerate((WX0 + 2.3, WX0 + 13.0, WX0 + 17.5, WX0 + 28.2, WX0 + 32.7)):
    for _j, _ry in enumerate([68 + 8 * i for i in range(7)] + [132 + 8 * i for i in range(7)]):
        if sr(_RACKS[(_k * 3 + _j) % len(_RACKS)], _rx, _ry, 0, 90 if _k % 2 == 0 else 270):
            _nr += 1
# forklifts, pallet jacks and pallets in the aisles (the owner liked the forklift)
sr("vehicle_forklift_orange_a01", WX0 + 7.6, 124, 0, 0)
sr("vehicle_forklift_blue_a01", WX0 + 22.8, 100, 0, 90)
sr("palletJack_heavyDuty_a01", WX0 + 37.5, 150, 0, 90)
sr_stack("pallet_block_a01", WX0 + 38, 80, 4)
sr_stack("pallet_block_a01", WX0 + 38, 172, 6)
for _px, _py in ((-170, 70), (-170, 90), (-160, 180), (-176, 130)):
    sr("box_cardboard_large_a02", _px, _py, 0, 15)
for _ly in range(70, 184, 16):                                            # rows of tube lights over the aisles
    tube_light(WX0 + 7.6, _ly, 8, 14, "y", 230)
    tube_light(WX0 + 22.8, _ly, 8, 14, "y", 230)
    tube_light(-163, _ly, 8, 14, "y", 230)
tube_light(-163, 40, 8, 14, "y", 230)

# --- Larry's Warehouse (118/120) LAN Party Stations: SE LAN Bay & North TV LAN Pod ---
# 1) SE LAN Party Bay (x = -170.5..-153.5, y = 26.2..57.7, facing South Daniel TV & warehouse center):
table(-170.5, 38.5, "x", variant=1)
table(-162.5, 38.5, "x", variant=2)
table(-170.5, 41.0, "x", variant=3)
table(-162.5, 41.0, "x", variant=4)
for _wi, _wpx in enumerate((-169.0, -166.0, -163.2, -159.6, -156.2)):
    pc(_wpx, 39.65, "s", z=ROADZ + 2.5, mon_var=(_wi % 4) + 1, pc_var=((_wi + 1) % 4) + 1, skin=_wi % 6)
    chair(_wpx, 36.2, "n", z=ROADZ, variant=(_wi % 4) + 1)
    pc(_wpx, 42.35, "n", z=ROADZ + 2.5, tower=(_wi != 2), mon_var=((_wi + 2) % 4) + 1, pc_var=((_wi + 3) % 4) + 1, skin=(_wi + 3) % 6)
    chair(_wpx, 45.8, "s", z=ROADZ, variant=((_wi + 2) % 4) + 1)
for _wcx, _wcy, _wmd in ((-167.5, 39.1, "soda_can"), (-161.2, 42.8, "soda_bottle"), (-157.8, 39.2, "cup"), (-164.6, 42.7, "soda_can")):
    model(_wmd, _wcx, _wcy, ROADZ + 2.5, "e")

# South wall LAN row flanking the South Warehouse TV (-162.0, 25.2):
table(-170.5, 26.2, "x", variant=1)
table(-162.5, 26.2, "x", variant=3)
for _wi, _wpx in enumerate((-168.8, -165.2, -159.8, -156.2)):
    pc(_wpx, 27.35, "n", z=ROADZ + 2.5, mon_var=((_wi + 1) % 4) + 1, pc_var=(_wi % 4) + 1, skin=(_wi * 2 + 1) % 6)
    chair(_wpx, 30.8, "s", z=ROADZ, variant=((_wi + 1) % 4) + 1)

# NE Clan Server & Admin Desk (compact 5.8-ft Honey-Oak lan_table4s):
table(-159.5, 55.2, "x", length=5.83, variant=5)
pc(-157.8, 56.35, "s", z=ROADZ + 2.5, mon_var=2, pc_var=2, skin=5)
ent("misc_lan_monitor", -155.2, 56.35, ROADZ + 2.5, angles="0 270 0", cnt=3, skin=2)
ent("misc_lan_pc", -154.2, 56.35, ROADZ + 2.5, angles="0 270 0", cnt=4)
chair(-156.6, 52.4, "n", z=ROADZ, variant=2)
model("soda_bottle", -159.0, 56.8, ROADZ + 2.5, "s", scale=1.5)

# 2) North Warehouse TV LAN Pod (x = -180.0..-164.0, y = 171.3..180.7, right under the big North Warehouse TV):
table(-180.0, 173.5, "x", variant=2)
table(-172.0, 173.5, "x", variant=4)
table(-180.0, 176.0, "x", variant=1)
table(-172.0, 176.0, "x", variant=3)
for _wi, _wpx in enumerate((-178.2, -174.2, -170.0, -166.0)):
    pc(_wpx, 174.65, "s", z=ROADZ + 2.5, mon_var=(_wi % 4) + 1, pc_var=((_wi + 2) % 4) + 1, skin=(_wi + 1) % 6)
    chair(_wpx, 171.3, "n", z=ROADZ, variant=((_wi + 3) % 4) + 1)
    pc(_wpx, 177.35, "n", z=ROADZ + 2.5, tower=(_wi != 1), mon_var=((_wi + 1) % 4) + 1, pc_var=(_wi % 4) + 1, skin=(_wi + 4) % 6)
    chair(_wpx, 180.7, "s", z=ROADZ, variant=(_wi % 4) + 1)
for _wcx, _wcy, _wmd in ((-176.2, 175.0, "soda_can"), (-168.0, 177.0, "cup"), (-172.0, 175.8, "soda_bottle")):
    model(_wmd, _wcx, _wcy, ROADZ + 2.5, "n")
V4_SPOTS.append(("Larry's Warehouse: SE LAN Party Bay", -152.5, 42.0, 2.8, 192))
V4_SPOTS.append(("Larry's Warehouse: North TV LAN Pod", -161.5, 176.0, 2.8, 155))
print("v4: warehouse hall (%d old brushes/ents dropped, %d racks)" % (_n, _nr))
V4_SPOTS.append(("Warehouse (118 / 120)", -150, 120, 2.2, 180))

# ---------------------------------------------------------------------------------------------- the bedroom (the 120A room)
_n = drop("detail", lambda b: inside(b, WX0 - 0.1, WY0 - 0.1, -183.9, BED_Y1 + 0.1, -0.1, 12.0))
_n += drop("world", lambda b: inside(b, WX0 - 0.1, WY0 - 0.1, -183.9, BED_Y1 + 0.1, -0.1, 12.0) and b[5] - b[2] < 11)
_n += _drop_ents(lambda c, x, y, z: (c == "misc_model" or c.startswith(("misc_vehicle", "misc_lan_"))) and WX0 - 1 < x < BED_X1 and WY0 - 1 < y < BED_Y1)   # the shop's car too
box(WX0, WY0, 0, BED_X1 - 0.67, BED_Y1 - 0.67, 0.15, "bk4_carpet", group="detail")
# the bed against the west wall, head to the wall
BX0, BX1, BY0, BY1 = WX0, WX0 + 6.8, 38.0, 43.4
prop(BX0, BY0, 0, BX1, BY1, 1.3, "bk_wood")
prop(BX0 + 0.1, BY0 + 0.1, 1.3, BX1 - 0.1, BY1 - 0.1, 2.1, "bk4_sheet", {"t": Fit("bk4_quilt")})
prop(BX0 + 0.25, BY0 + 0.5, 2.1, BX0 + 1.5, BY1 - 0.5, 2.55, "bk4_pillow")
prop(BX0, BY0 - 0.2, 0, BX0 + 0.35, BY1 + 0.2, 4.2, "bk_wood")                   # headboard
for _sy in (BY0 - 2.0, BY1 + 0.2):                                                # bedside tables, a lamp on one
    prop(BX0 + 0.1, _sy, 0, BX0 + 1.9, _sy + 1.8, 2.0, "bk_wood")
prop(BX0 + 0.7, BY1 + 0.7, 2.0, BX0 + 1.3, BY1 + 1.3, 3.1, "bk_steel")
prop(BX0 + 0.4, BY1 + 0.4, 3.1, BX0 + 1.6, BY1 + 1.6, 3.8, "bk_beige")
light(BX0 + 1.0, BY1 + 1.0, 4.4, 120, "255 215 160")
# Mega Man (the Precision Chrome Bar & Dish-Tires rig) sitting on the bed, not moving (misc_model with no frame range)
ent("misc_model", BX0 + 3.9, (BY0 + BY1) / 2, 2.1 + 2.44 * 2.6 / 12, mdl="progs/bklan/mm_rig.md3", angles="0 0 0", scale="2.6")
box(BX0 + 2.6, BY0 + 0.3, 2.1, BX0 + 5.2, BY1 - 0.3, 4.6, "clip")
# the computer desk on the north wall: CRT, tower, keyboard, an office chair
DX = -209.0
table(DX - 2.92, BED_Y1 - 3.2, "x", length=5.83, z=0.16)
pc(DX, BED_Y1 - 1.9, "s", z=2.66, mon_var=2, pc_var=2, skin=0)
chair(DX, BED_Y1 - 4.6, "n", "office", z=0.22, variant=2)
light(DX, BED_Y1 - 2.5, 6, 70, "120 200 255")                                     # the screen's glow
# a dresser, a rug, a poster over the bed
prop(-198.5, BED_Y1 - 2.4, 0, -193.5, BED_Y1 - 0.7, 3.4, "bk_wood")
prop(-216.0, 34.0, 0.15, -206.0, 46.0, 0.22, "bk4_rug", {"t": Fit("bk4_rug")})
prop(WX0, 39.2, 4.6, WX0 + 0.05, 42.2, 9.1, "bk_steel", {"e": Fit("bk4_poster")})
print("v4: bedroom (%d old brushes/ents dropped)" % _n)
V4_SPOTS.append(("Bedroom (Mega Man)", -200, 40, 2.2, 180))

# ---------------------------------------------------------------------------------------------- the lot: out to the street
# (2:50-3:05, standing at the north end of the LAN lot: "I should be able to walk out here and then go to the street").
# The 8 ft block wall across the north end of the lot gets a 12 ft gap at its east end: out past the north side of the
# 130A building and through the BODY SHOP gate (opened in bklan2) onto Sacramento St.
_n = drop("world", lambda b: inside(b, -143.1, 186.9, -87.9, 187.8, -0.1, 8.1))
box(-143.0, 187.0, 0, -100.0, 187.67, 8.0, "bk_blockgr")
prop(-100.4, 186.8, 0, -99.6, 187.9, 8.4, "bk_blockgr")                          # a pier at the end of the wall
print("v4: lot wall opened (%d)" % _n)

# ---------------------------------------------------------------------------------------------- teleports
# Larry's: two pads inside the warehouse, one behind each of two roll-ups. The Sign's hub moves up onto the roof of
# the tall office next to the Sign (the office pads now reach it). Manning St stays where it was.
_ROOF = 55.5


def tp_pad4(hx, hy, hz, dest, label_tex):
    """A teleporter at height hz (feet): a classic Quake portal (see tp_portal in make_bklan_v3.py)."""
    tp_portal(hx, hy, hz, dest)


HUB_ARRIVE = {"L": (-165.0, 128.0, 0.0, 0), "S": (_ocx, _ocy + 10, _ROOF, 270), "M": (MAN_X - 3.0, -422.0, 0.0, 90)}
for _k, (_ax, _ay, _az, _yaw) in HUB_ARRIVE.items():
    ent("info_teleport_destination", _ax, _ay, _az + 0.3, targetname="tp_" + _k, angle=_yaw)
tp_pad4(-152.0, 101.0, 0.0, "S", HUBS["S"]["tex"])            # behind the roll-up at y 100..112
tp_pad4(-152.0, 145.0, 0.0, "M", HUBS["M"]["tex"])            # behind the roll-up at y 144..156
tp_pad4(_ocx - 9, _ocy - 12, _ROOF, "L", HUBS["L"]["tex"])
tp_pad4(_ocx + 9, _ocy - 12, _ROOF, "M", HUBS["M"]["tex"])
for _n_, _ok in enumerate(("L", "S")):
    tp_pad(MAN_X - 3.0 + (_n_ * 2 - 1) * 8, -440.0, _ok, HUBS[_ok]["tex"], "x")
V4_SPOTS += [("Teleports in the warehouse", -165, 128, 2.2, 0), ("Teleports on the tall office roof", _ocx, _ocy + 10, _ROOF + 2.2, 270),
             ("Teleport hub: Manning St", MAN_X - 3.0, -454, 2.2, 90)]
print("v4: teleports: warehouse, office roof (%.0f, %.0f), Manning St" % (_ocx, _ocy))

# ---------------------------------------------------------------------------------------------- the drive loop
# (3:24-4:44) in front of Larry's along E 21st, up Sacramento, east on the north street, down Buck Owens, east under the
# Bakersfield Sign along Sillect, down Manning St past the house, west along the park road, down to the cul-de-sac, slowly
# through Amberton Park, up Buck Owens and back along E 21st. Checked with route_check.py (no buildings in the way; the
# movers pass through the world anyway, so curbs and kerb clutter do not stop them).
ROUTE = [(-600, -8.5, 1), (0, -8.5, 1), (0, 392, 1), (712, 392, 1), (712, -8.5, 1), (1552, -8.5, 1), (1552, -685, 1),
         (1250, -685, 1), (1250, -930, 0.6), (1160, -990, 0.4), (1185, -900, 0.4), (1090, -850, 0.4), (880, -818, 0.4),
         (830, -784, 0.6), (724, -700, 1), (724, 1, 1), (-600, 1, 1)]
for _i, (_x, _y, _s) in enumerate(ROUTE):
    ent("bk_route", _x, _y, ROADZ + 0.05, targetname="rt%d" % _i, target="rt%d" % ((_i + 1) % len(ROUTE)), speed="%.2f" % _s)
ent("bk_cruiser", ROUTE[0][0], ROUTE[0][1], ROADZ + 0.05, cnt=1, target="rt1")              # the hot pink supercar
ent("bk_cruiser", ROUTE[7][0], ROUTE[7][1], ROADZ + 0.05, cnt=2, target="rt8")              # the Podracer Sky-Chariot
# the trash can in the park (4:15-4:32): shoot it and it goes up like a rocket. Review 2: moved to where the owner stood
# (1216, -794), and drawn as a proper green park drum (build_trashcan.py)
ent("bk_trashcan", 1216, -794, 0.1)
V4_SPOTS += [("Park trash can", 1216, -779, 2.2, 270), ("Drive loop: E 21st", -560, -30, 2.2, 0)]
print("v4: drive loop of %d points, 2 cruisers, the trash can" % len(ROUTE))

# ---------------------------------------------------------------------------------------------- long-range launch pads
# Review 2 (video 17:48): "make it another bounce pad, but a certain color" - violet pads with a board saying where they
# go, each flinging you across the map in one arc (sv_maxvelocity is 4000 in q15_config.cfg). A chain: Larry's -> the Sign
# -> Manning St -> the park -> back to Larry's. Spots are the owner's "right here" positions from the dev overlay; each is
# nudged to the nearest bit of open floor and kept 24 ft from every other pad (the earlier "never so many pads close").
LP_H = 6.0                                                         # 12 x 12 ft pads


def _lp_spot(x, y, half=LP_H, board=False, gap=24.0):
    """The nearest spot to (x, y) feet with room (a pad, and its board when board=True) and no other pad within gap."""
    for r in range(0, 80, 3):
        for dx in range(-r, r + 1, 3):
            for dy in range(-r, r + 1, 3):
                if max(abs(dx), abs(dy)) != r:
                    continue
                px_, py_ = x + dx, y + dy
                if any(math.hypot(px_ - qx, py_ - qy) < gap for qx, qy in PADS):
                    continue
                if free(px_, py_, half + 0.5, 1.0, 8.0) and (not board or free(px_, py_ + half + 1.5, half + 2, 1.0, 10.0, half_y=1.2)):
                    return float(px_), float(py_)
    raise SystemExit("v4: no room for a launch pad near %s, %s" % (x, y))


def launch_pad(x, y, target, sign_tex, over):
    px_, py_ = _lp_spot(x, y, board=True)
    h = LP_H
    box(px_ - h, py_ - h, 0.0, px_ + h, py_ + h, 0.4, "bk_steel", {"t": Fit("bk4_launch")}, group="detail")
    for bx_ in (px_ - h - 1.0, px_ + h + 1.0):                       # the board on two posts, readable from both sides
        prop(bx_ - .2, py_ + h + 1.3, 0.0, bx_ + .2, py_ + h + 1.7, 8.6, "bk_steel")
    prop(px_ - h - 1.2, py_ + h + 1.4, 4.2, px_ + h + 1.2, py_ + h + 1.6, 8.6, "bk_steel", {"s": Fit(sign_tex), "n": Fit(sign_tex)})
    light(px_, py_, 3.0, 160, "230 90 255")
    PADS.append((px_, py_))
    return px_, py_, target, over


_pads = [launch_pad(-172, -4, (800, -70), "bk4_lsign1", 210),
         launch_pad(835, -30, (1590, -540), "bk4_lsign2", 180),
         launch_pad(1545, -500, (1165, -780), "bk4_lsign3", 110),
         launch_pad(1122, -862, (-120, -8), "bk4_lsign4", 300)]
for _px, _py, (_tx, _ty), _over in [(a, b, t[:2], o) for a, b, t, o in _pads]:
    _lx, _ly = _lp_spot(_tx, _ty, half=5.0, gap=24.0)               # land on open floor, away from every pad
    PADS.append((_lx, _ly))                                          # so the next landing keeps away from this one too
    _v = launch((_px, _py, 0.0), (_lx, _ly, 0.5), _over)
    assert max(abs(c) for c in _v) < 3900, _v
    brush_ent("trigger_push", _px - LP_H + 0.5, _py - LP_H + 0.5, 0.4, _px + LP_H - 0.5, _py + LP_H - 0.5, 5, **push_kv(_v))
    V4_SPOTS.append(("Launch pad (%d, %d) -> %d, %d" % (_px, _py, _lx, _ly), _px - 18, _py, 2.2, 0))
    print("v4: launch pad (%.0f, %.0f) -> (%.0f, %.0f), v = %s" % (_px, _py, _lx, _ly, tuple(int(c) for c in _v)))

# ---------------------------------------------------------------------------------------------- drivable vans
# (7:54-8:18) the ProMaster van of vehicle_drive.qc: walk into the cab, H to drive. Near Larry's, the Sign, the park,
# Manning St and a couple of corners; each spot is checked for room (the van is 21 x 9 ft).
_vans = 0
for _vx, _vy, _yaw in ((-110, -21, 0), (-60, -21, 180), (850, 28, 0), (980, -735, 0), (1592, -300, 90), (470, 32, 180),
                       (40, 420, 0), (1592, -130, 270)):
    _hx, _hy = (11, 5) if _yaw in (0, 180) else (5, 11)
    if free(_vx, _vy, _hx, 1.0, 8.0, half_y=_hy):
        ent("misc_vehicle_van", _vx, _vy, 0.2, angle=_yaw)
        _vans += 1
    else:
        print("v4: no room for a van at", _vx, _vy)
print("v4: %d drivable vans" % _vans)

# ---------------------------------------------------------------------------------------------- TVs
# (owner, 2026-10-31: "TVs that randomly play these videos with low volume, put one in Larry's warehouse".) bk_tv
# (bklan_tv.qc) plays the 8 clips (build_bklan_tv.py) on a 4 x 3 ft screen times `scale`; the casing is brushes here.
_DIR = {"n": (0, 1), "s": (0, -1), "e": (1, 0), "w": (-1, 0)}


def tv(x, y, z, facing, scale=1.0, label=""):
    """A flat screen TV. (x, y, z) = the middle of the screen in feet, facing = the side it looks toward; the casing
    (0.5 ft deep) sits behind the screen plane, so for a wall mount put the plane 0.56 ft in front of the wall."""
    dx, dy = _DIR[facing]
    hw, hh = 2.0 * scale + 0.22, 1.5 * scale + 0.22          # casing half width / half height
    bx, by = x - dx * 0.56, y - dy * 0.56                    # back of the casing
    fx, fy = x - dx * 0.06, y - dy * 0.06                    # front of the casing, just behind the screen
    if dx:
        prop(min(bx, fx), y - hw, z - hh, max(bx, fx), y + hw, z + hh, "bk_dark")
    else:
        prop(x - hw, min(by, fy), z - hh, x + hw, max(by, fy), z + hh, "bk_dark")
    ent("bk_tv", x, y, z, angle=(0, 90, 180, 270)[("e", "n", "w", "s").index(facing)], scale=scale)
    light(x + dx * 2.5, y + dy * 2.5, z, int(40 + 25 * scale), "170 200 255")      # the picture's glow on the room
    V4_SPOTS.append(("TV: " + (label or "%d, %d" % (x, y)), x + dx * 9, y + dy * 9, 2.2, {"e": 180, "n": 270, "w": 0, "s": 90}[facing]))


tv(-172, WY1 - 0.56, 6.6, "s", 1.6, "Larry's warehouse")                    # on the north wall of the hall, over the aisle
tv(-196, 59.34, 4.5, "s", 0.6, "bedroom dresser")                           # on the 120A bedroom's dresser
tv(B45[0] - 0.56, 69, 7.0, "w", 1.4, "the lot, on 130A's wall")             # between two roll-ups, facing the LAN lot
print("v4: 3 TVs")

# ---------------------------------------------------------------------------------------------- no car pictures
for _g in GROUPS:
    GROUPS[_g][:] = [s.replace(" bk_darkwin ", " bk4_win ") for s in GROUPS[_g]]
V3_SPOTS += V4_SPOTS
