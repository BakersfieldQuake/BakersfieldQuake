"""bklan4: Golden West Casino added to bklan3, plus the accuracy pass of the four areas the owner named (2026-10-31
night: "scan Larry's warehouse, the Bakersfield Sign, Manning St, the park for accuracy ... place Golden West Casino
somewhere in the map ... think about jump pads, jetpacks, cars ... keep the size and vibe of bklan3"). exec'd by
make_bklan.py after make_bklan_v4.py, only when BKLAN_V5=1 (with BKLAN_V3=1 BKLAN_V4=1); build_bklan4.sh builds it as
maps/bklan4.bsp. Like v3/v4 it only adds brushes and entities, or drops specific old ones by position.

The casino. In reality Golden West is 2 miles south of Larry's down S Union Ave, so it goes where Union Ave leaves
the map: a new box C south of box A's west end (x -820..-420, y -1000..-340). Union Ave runs on south through it, the
casino parcel is on the west side of the street (as in reality), its front facing south onto its own lot. Nothing is
redrawn: make_goldenwest.py's output (out/bk4/gw.map, GW_FAST=1) is read back with bks_mapio, the parcel window cut out
and moved, the parked car models turned into exploding misc_vehicle_* like the rest of bklan3 (bakolansmall did the
same cut; see make_bakolansmall.py).

Gameplay (the whole map): 12 of bklan3's 47 spawns were inside the ORCOM hall, so 6 go; the casino gets 8 spawns,
a rocket launcher (card room), the map's second lightning gun (high-limit bar), a grenade launcher among the exploding
cars of the south lot, green armour in the lobby, a jetpack (yellow armour) and rockets on the west wing's flat roof
(a jump pad from the north lot gets you up), cells and health on the lobby roof (pad from the south lot). Routes: a
launch pad at Larry's lot flings you to the casino and one on Union in front of the casino flings you back; the
casino's north lot is a teleport hub (to Larry's and the office roof) and the warehouse / office roof pads get a
"casino" destination. The pink supercar and the Podracer now drive down Union Ave to the casino and back; the biplane
lands in the strip east of Union; a drivable van waits in each casino lot. All 93 jump pads stay (nearly all are
"pad up onto a roof with an item" pairs the owner asked for); a new one at the Union / box C junction.
"""
import random as _rnd5

WAD3 = WAD3 + ";goldenwest.wad;gwcasino.wad;bklan5.wad"           # worldspawn "wad" (qbsp runs in out/maps; < 127 chars)
for _wn in ("goldenwest.wad", "gwcasino.wad", "bklan5.wad"):
    with open(os.path.join(HERE, "out", "maps", _wn), "rb") as _f:
        _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
        _f.seek(_ofs)
        _dirs = [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]
        for _pos, _, _, _, _, _, _name in _dirs:
            _f.seek(_pos)
            _nm, _w, _h = struct.unpack("<16s2I", _f.read(24))
            TEXSIZE.setdefault(_name.split(b"\0")[0].decode(), (_w, _h))
WAD = "bklan.wad"                                                 # relative like the others (qbsp runs in out/maps): the key must stay under 127 chars
assert len(WAD + ";" + WAD3) < 127, len(WAD + ";" + WAD3)

V5_SPOTS = []
import bks_mapio as _mio  # noqa: E402  (sys.path has HERE since make_bklan_v2.py)


def _drop_brush_ents(pred):
    """Remove brush entities (trigger_push, trigger_teleport...) whose brush bounds (feet) satisfy pred(classname, bbox)."""
    keep, n = [], 0
    for s in ENTS:
        m = re.search(r'"classname" "([^"]+)"', s)
        if m and "{" in s[s.index("}") if "}" in s else 0:] and '"origin"' not in s:
            b = ft_bbox(s)
            if pred(m.group(1), b):
                n += 1
                continue
        keep.append(s)
    ENTS[:] = keep
    return n


# ============================================================================================== box C: the hull grows south
XC0, XC1, YC0, YC1 = X0, -420, -1000, Y0
_n = drop("world", lambda b: inside(b, X0 - 1.1, Y0 - 1.1, X1 + 0.1, Y0 + 0.1, -3.1, SKY_Z + 0.1) and b[5] > 100)      # box A's south sky wall
_n += drop("world", lambda b: inside(b, X0 - 0.1, Y0 - 0.1, X1 + 0.1, Y0 + 4.1, -0.1, SKY_Z + 0.1) and b[5] > 100)      # ... and its clip strip
_n += drop("world", lambda b: inside(b, X0 - 0.1, Y0 + 4.9, X1 + 0.1, Y0 + 7.1, -0.1, 36.1) and b[3] - b[0] > 1000)    # ... and the v3 sound wall
box(XC1, Y0 - 1, -3, X1, Y0, SKY_Z, "sky_bk")                                   # the same three, east of box C only
box(XC1 - 4, Y0, 0, X1, Y0 + 4, SKY_Z, "clip")
box(XC1 - 7, Y0 + 5, 0, X1, Y0 + 7, 36, tspec("bk3_sw", 8), {"t": "bk3_sw"})
box(XC0 - 1, YC0 - 1, -3, XC1 + 1, YC1 + 1, -2, "bk_dirt")                       # box C: hull floor, sky lid, sky walls
box(XC0 - 1, YC0 - 1, SKY_Z, XC1 + 1, YC1 + 1, SKY_Z + 1, "sky_bk")
box(XC0 - 1, YC0 - 1, -3, XC0, YC1 + 1, SKY_Z, "sky_bk")
box(XC0 - 1, YC0 - 1, -3, XC1 + 1, YC0, SKY_Z, "sky_bk")
box(XC1, YC0 - 1, -3, XC1 + 1, YC1, SKY_Z, "sky_bk")
for _cx0, _cy0, _cx1, _cy1 in ((XC0, YC0, XC0 + 4, YC1), (XC0, YC0, XC1, YC0 + 4), (XC1 - 4, YC0, XC1, YC1)):
    box(_cx0, _cy0, 0, _cx1, _cy1, SKY_Z, "clip")
for _cx0, _cy0, _cx1, _cy1 in ((XC0 + 1, YC0, XC0 + 3, YC1), (XC0 + 1, YC0 + 5, XC1 - 5, YC0 + 7), (XC1 - 7, YC0 + 5, XC1 - 5, Y0 + 7)):
    box(_cx0, _cy0, 0, _cx1, _cy1, 36, tspec("bk3_sw", 8), {"t": "bk3_sw"})     # the sound wall, as make_bklan_v3.py's
# ground: the parcel's dirt west of Union Ave, asphalt east of it; one unit below box A's slab so the parcel's own lot
# pads (cut from goldenwest) sit proud of it instead of fighting it
UNX0, UNX1 = -526.0, -488.0                                                     # Union Ave carriageway (38 ft, as box A's)
box(XC0, YC0, -2, UNX0, YC1, -1 / U, "gw_dirt", {"t": tspec("gw_dirt", 24)})
box(UNX0, YC0, -2, XC1, YC1, -1 / U, "bk_asphalt")
print("v5: box C added (%d hull brushes replaced)" % _n)

# ============================================================================================== the casino, cut from goldenwest
GW_SO, GW_WIN, GW_D = (0.0, 135.0), (-135, -175, 156, 410), (-682.0, -756.0)     # generator origin, window (gw feet), shift
_GW = _mio.read_map(os.path.join(HERE, "out", "bk4", "gw.map"))
_off = (int(round(U * (GW_SO[0] + GW_D[0] - OX))), int(round(U * (GW_SO[1] + GW_D[1] - OY))), 0)
_TAG = {"worldspawn": "world", "func_detail": "detail", "func_wall": "fence", "func_detail_illusionary": "illus"}
_DROP = ("info_player", "weapon_", "item_", "info_teleport", "trigger_")


def C(x, y):
    """goldenwest feet -> map feet"""
    return x + GW_D[0], y + GW_D[1]


def _gw_in(x, y):
    return GW_WIN[0] <= x <= GW_WIN[2] and GW_WIN[1] <= y <= GW_WIN[3]


_cars = []                                                                       # (gw feet x, y, yaw, kind)
for _e in _GW:
    _o = _e.origin()
    if _e.cls == "misc_model" and _o and _e.kv.get("mdl", "").startswith("progs/veh_"):
        _gx, _gy = _o[0] / U + GW_SO[0], _o[1] / U + GW_SO[1]
        if _gw_in(_gx, _gy):
            _cars.append((_gx, _gy, int(float(_e.kv.get("angles", "0 0 0").split()[1])), _e.kv["mdl"][len("progs/veh_"):-4]))
_nb = _ne = 0
for _e in _GW:
    if _e.cls in _TAG:
        for _b in _e.brushes:
            _bx0, _by0, _bx1, _by1 = _b.lo[0] / U + GW_SO[0], _b.lo[1] / U + GW_SO[1], _b.hi[0] / U + GW_SO[0], _b.hi[1] / U + GW_SO[1]
            if not (_bx0 >= GW_WIN[0] and _bx1 <= GW_WIN[2] and _by0 >= GW_WIN[1] and _by1 <= GW_WIN[3]) or "sky_bk" in _b.texs:
                continue
            if _b.texs == {"clip"} and any(abs((_bx0 + _bx1) / 2 - cx_) < 12 and abs((_by0 + _by1) / 2 - cy_) < 12 for cx_, cy_, _, _ in _cars):
                continue                                                        # the cars' clip boxes: the exploding cars collide themselves
            _mb = _b.moved(_off)
            GROUPS[_TAG[_e.cls]].append(_mb.text())
            if _TAG[_e.cls] != "illus":
                SOLIDS.append(_mb.lo + _mb.hi)
            _nb += 1
        continue
    if _e.cls.startswith(_DROP) or _e.cls == "worldspawn":
        continue
    _o = _e.origin()
    if _o is None or not _gw_in(_o[0] / U + GW_SO[0], _o[1] / U + GW_SO[1]):
        continue
    if _e.cls == "misc_model" and _e.kv.get("mdl", "").startswith("progs/veh_"):
        continue                                                                # placed below as misc_vehicle_*
    ENTS.append(_e.text(_off))
    _ne += 1
for _gx, _gy, _yaw, _kind in _cars:                                             # "the cars we created that explode if you shoot them"
    ent("misc_vehicle_" + _kind, *C(_gx, _gy), 0.2, angle=_yaw)
print("v5: casino cut in: %d brushes, %d entities, %d exploding cars" % (_nb, _ne, len(_cars)))
CAS_X0, CAS_Y0 = C(GW_WIN[0], GW_WIN[1])
CAS_X1, CAS_Y1 = C(154.7, 396.2)                                                # the cut's real extents

# Union Ave south of E 21st: the carriageway on from box A's northbound ribbon (it ends at y -345), two lanes, the
# sidewalks, a hedge and lamp strip east of it, the parcel's north sidewalk
box(UNX0, YC0 + 5, -1 / U, UNX1, YC1, ROADZ, "bk_road", group="detail")
lines_y(YC0 + 8, YC1 - 2, (UNX0 + UNX1) / 2 - 0.35, "bk_yline", w=0.35)
lines_y(YC0 + 8, YC1 - 2, (UNX0 + UNX1) / 2 + 0.35, "bk_yline", w=0.35)
for _lx in (UNX0 + 9.5, UNX1 - 9.5):
    lines_y(YC0 + 8, YC1 - 2, _lx, "bk_wline", w=0.35, dash=(10, 30))
box(UNX1, YC0 + 5, 0, UNX1 + 8, YC1, WALKZ, "bk_walk", group="detail")          # east sidewalk
box(UNX0 - 8, YC0 + 5, 0, UNX0, CAS_Y0, WALKZ, "bk_walk", group="detail")        # west sidewalk, south of the parcel ...
box(UNX0 - 8, CAS_Y1, 0, UNX0, YC1, WALKZ, "bk_walk", group="detail")            # ... and north of it
box(XC0 + 3, CAS_Y1, 0, UNX0 - 8, YC1, WALKZ, "bk_walk", group="detail")         # the parcel's north sidewalk
for _hy in range(YC0 + 20, YC1 - 30, 60):                                        # hedge beds along the east sidewalk
    if any(abs(_hy + 12 - q) < 40 for q in (-760, -640)):                       # gaps at the launch pad and the landing strip
        continue
    box(UNX1 + 9, _hy, 0, UNX1 + 11.5, _hy + 24, 3.2, "bk_hedge", group="detail")
for _ly in range(YC0 + 60, YC1 - 40, 120):                                       # cobra-head lamps over the east curb
    prop(UNX1 + 0.3, _ly - 0.3, 0, UNX1 + 0.9, _ly + 0.3, 30, "bk_steel")
    prop(UNX1 - 9.5, _ly - 0.3, 30, UNX1 + 0.9, _ly + 0.3, 30.6, "bk_steel")
    light(UNX1 - 8, _ly, 28, 210, "255 240 210")
for _k, (_tx, _ty) in enumerate(((XC1 - 20, -980), (XC1 - 22, -860), (XC1 - 18, -520), (XC1 - 24, -400), (XC0 + 12, -985), (XC0 + 30, -990))):
    sprite_tree(_tx, _ty, 34 + 6 * (_k % 3), ("t2", "t3", "t1")[_k % 3])
V5_SPOTS += [("Golden West Casino: the entrance",) + C(38.9, -13) + (2.2, 90), ("Golden West: the south lot",) + C(31.7, -95) + (2.2, 90),
             ("Golden West: the lobby",) + C(62, 22) + (2.2, 90), ("Golden West: the card room",) + C(-2.4, 24) + (2.2, 90),
             ("Golden West: the high-limit room and bar",) + C(6.25, 114) + (2.2, 90), ("Golden West: the north lot",) + C(-31.7, 237.75) + (2.2, 270),
             ("S Union Ave in front of the casino", -507, -700, 2.2, 180), ("Union Ave south from E 21st", -507, -300, 2.2, 270)]

# ============================================================================================== casino gameplay
# spawns: card room (3, where goldenwest had them), lobby, bar, the entrance plaza, the south lot, the north lot, Union
for _gx, _gy, _a in ((-2.4, 22, 90), (-30.5, 103, 0), (22, 103, 180), (62, 24, 90), (6.25, 112, 90), (38.9, -20, 90)):
    ent("info_player_deathmatch", *C(_gx, _gy), 2.2, angle=_a)
for _x, _y, _a in ((-603.33, -870, 180), (-714, -518, 270), (-507, -700, 180), (XC1 - 40, -640, 180)):
    if free(_x, _y, 2.0, 0.5, 7.0):
        ent("info_player_deathmatch", _x, _y, 2.2, angle=_a)
    else:
        print("v5: no room for a spawn at", _x, _y)
# weapons and items inside: the card room's rocket launcher on the long aisle, the second lightning gun at the bar
ent("weapon_rocketlauncher", *C(-2.4, 56.5), 1)
ent("item_health", *C(21, 56.5), 1)
ent("item_shells", *C(-30.5, 56.5), 1)
ent("item_rockets", *C(-2.4, 90), 1)
ent("weapon_lightning", *C(6.25, 130), 1)
ent("item_cells", *C(0.5, 146), 1)
ent("item_cells", *C(12.0, 146), 1)
ent("item_armor1", *C(46, 26), 1)                                                # green armour in the lobby
ent("item_rockets", *C(80, 24), 1)
ent("item_health", *C(62, 30), 1)
ent("weapon_supershotgun", *C(38.9, -30), 1)                                     # the entrance plaza
# outside: a grenade launcher among the exploding cars of the south lot, health by the pylon, nails on the north lot
for _cls, _x, _y in (("weapon_grenadelauncher", -650, -851), ("item_health", -700, -850), ("item_shells", -620, -800),
                     ("item_spikes", -560, -790), ("item_health", -740, -540), ("weapon_nailgun", -690, -500),
                     ("item_spikes", -660, -500), ("item_health", -500, -600), ("item_health", XC1 - 30, -900),
                     ("item_rockets", XC1 - 30, -450)):
    _fx, _fy = _lp_spot(_x, _y, half=2.0, gap=0.0)
    ent(_cls, _fx, _fy, 1)
# the roofs: a pad from the north lot up onto the west wing's flat roof (15 ft, parapet to 17) with the jetpack and
# rockets; a pad from the south lot onto the lobby's flat roof (13 ft) with cells and health
_WR = C(-60, 70)                                                                 # west wing roof centre
_LR = C(63, 29)                                                                  # lobby roof centre
if jump_pad(_WR[0], -560, 0.0, target=(_WR[0], _WR[1] + 20, 15.0), size=9, over=24.0):
    ent("item_armor2", _WR[0], _WR[1], 16.0)
    ent("item_rockets", _WR[0] + 8, _WR[1] - 14, 16.0)
    ent("item_health", _WR[0] - 8, _WR[1] - 14, 16.0)
    V5_SPOTS.append(("Golden West: pad up to the west roof", _WR[0], -575, 2.2, 90))
else:
    print("v5: no room for the west roof pad")
if jump_pad(_LR[0] + 10, -800, 0.0, target=C(80, 30) + (13.0,), size=9, over=24.0):   # clear of the two rooftop units
    ent("item_cells", *C(85, 22), 14.0)
    ent("item_health", *C(55, 38), 14.0)
    V5_SPOTS.append(("Golden West: pad up to the lobby roof", _LR[0] + 10, -815, 2.2, 90))
else:
    print("v5: no room for the lobby roof pad")
jump_pad(UNX1 + 24, YC1 - 20, 0.0, apex=70)                                      # straight up at the Union / box C junction: a look south
# a TV over the bar's back shelves (the owner's clips, as the other three)
tv(*C(6.25, 171.21), 8.95, "s", 0.8, "Golden West bar")

# teleports: the casino's north lot is a hub (pads to Larry's and the office roof); the warehouse and the office roof
# get a pad to the casino
HUB_ARRIVE["C"] = (-694.0, -534.0, 0.0, 270)
ent("info_teleport_destination", -694.0, -534.0, 0.3, targetname="tp_C", angle=270)
for _k, (_hx, _hy) in (("L", (-704, -556)), ("S", (-684, -556))):
    _px, _py = _lp_spot(_hx, _hy, half=5.5, board=True, gap=12.0)
    tp_pad4(_px, _py, 0.0, _k, HUBS[_k]["tex"])
    PADS.append((_px, _py))
_px, _py = _lp_spot(-152.0, 123.0, half=5.5, board=True, gap=12.0)             # the warehouse: a third pad
tp_pad4(_px, _py, 0.0, "C", "bk5_tpsign4")
PADS.append((_px, _py))
if _oy0 + 8 < _ocy - 30:                                                        # the office roof: a third pad, south of the two
    tp_pad4(_ocx, _ocy - 26, _ROOF, "C", "bk5_tpsign4")
else:
    print("v5: office roof too short for a third pad")
V5_SPOTS.append(("Teleports: casino north lot", -694, -575, 2.2, 90))

# launch pads: Larry's lot -> Union Ave by the casino's north lot, and back from the parcel's north sidewalk (the chain
# of make_bklan_v4.py stays). Both arcs must cross y = Y0 west of XC1, through box C's opening: the first try aimed at the
# casino's front and the player hit the south sky wall at x -323 and slid down it.
# Measured in game: both flights land 5-10 % long (the push is re-applied while the player rises through the trigger), so
# the targets are aimed short; the first landed at (-528, -420), the second at (-74, 63) - through 130A's open roll-up.
_pads5 = [launch_pad(-125, 70, (-505, -372), "bk5_lsign5", 170),
          launch_pad(-560, -352, (-172, 8), "bk4_lsign4", 170)]
for _px, _py, (_tx, _ty), _over in [(a, b, t[:2], o) for a, b, t, o in _pads5]:
    _lx, _ly = _lp_spot(_tx, _ty, half=5.0, gap=24.0)
    PADS.append((_lx, _ly))
    _v = launch((_px, _py, 0.0), (_lx, _ly, 0.5), _over)
    assert max(abs(c) for c in _v) < 3900, _v
    brush_ent("trigger_push", _px - LP_H + 0.5, _py - LP_H + 0.5, 0.4, _px + LP_H - 0.5, _py + LP_H - 0.5, 5, **push_kv(_v))
    V5_SPOTS.append(("Launch pad (%d, %d) -> %d, %d" % (_px, _py, _lx, _ly), _px - 18, _py, 2.2, 0))
    print("v5: launch pad (%.0f, %.0f) -> (%.0f, %.0f), v = %s" % (_px, _py, _lx, _ly, tuple(int(c) for c in _v)))

# vehicles: the drive loop now goes down Union Ave to the casino and back (east lane south, west lane north), a drivable van in each casino lot
_n = _drop_ents(lambda c, x, y, z: c in ("bk_route", "bk_cruiser"))
_UNB = [(-575, 2), (-538, -121), (-531, -146), (-521, -193), (-507, -260), (-507, -345)]    # box A's northbound centre line
ROUTE5 = [(x + 8, y, 1) for x, y in _UNB] + [(-499, -960, 0.8), (-515, -960, 0.4)] + [(x - 8, y, 1) for x, y in reversed(_UNB)]
ROUTE5 = ROUTE5[:-1] + [(-583, -8.5, 1), (0, -8.5, 1), (0, 392, 1), (712, 392, 1), (712, -8.5, 1), (1552, -8.5, 1), (1552, -685, 1),
                        (1250, -685, 1), (1250, -930, 0.6), (1160, -990, 0.4), (1185, -900, 0.4), (1090, -850, 0.4), (880, -818, 0.4),
                        (830, -784, 0.6), (724, -700, 1), (724, 1, 1), (-567, 1, 1)]
for _i, (_x, _y, _s) in enumerate(ROUTE5):
    ent("bk_route", _x, _y, ROADZ + 0.05, targetname="rt%d" % _i, target="rt%d" % ((_i + 1) % len(ROUTE5)), speed="%.2f" % _s)
ent("bk_cruiser", ROUTE5[14][0], ROUTE5[14][1], ROADZ + 0.05, cnt=1, target="rt15")       # the hot pink supercar, on E 21st
ent("bk_cruiser", ROUTE5[3][0], ROUTE5[3][1], ROADZ + 0.05, cnt=2, target="rt4")          # the Podracer, heading for the casino
_vans = 0
for _vx, _vy, _yaw in ((-590, -905, 0), (-745, -505, 0), (XC1 - 32, -560, 90)):
    _hx, _hy = (11, 5) if _yaw in (0, 180) else (5, 11)
    if free(_vx, _vy, _hx, 1.0, 8.0, half_y=_hy):
        ent("misc_vehicle_van", _vx, _vy, 0.2, angle=_yaw)
        _vans += 1
    else:
        print("v5: no room for a van at", _vx, _vy)
for _k, (_vx, _vy) in enumerate(((XC1 - 32, -700), (XC1 - 32, -730), (XC1 - 32, -880), (XC1 - 32, -470))):
    if free(_vx, _vy, 5, 1.0, 8.0, half_y=10):
        ent("misc_vehicle_" + ("sedan", "coupe", "truck", "sedan")[_k], _vx, _vy, 0.2, angle=90)
print("v5: drive loop of %d points (%d old route ents dropped), %d vans" % (len(ROUTE5), _n, _vans))

# spawn balance: 6 of the ORCOM hall's 12 spawns go
_n = _drop_ents(lambda c, x, y, z: c == "info_player_deathmatch" and 300 < y < 345 and round(x) in (365, 380, 400, 410, 428, 432))
# a jetpack for Manning St (the Sillect corner had the only one), and spawns where whole areas had none
if free(1605, -700, 3, 1, 5):
    ent("item_armor2", 1605, -700, 1.8)
for _x, _y, _a in ((1605, -760, 90), (860, -140, 0), (-300, -200, 90)):
    if free(_x, _y, 2.0, 0.5, 7.0):
        ent("info_player_deathmatch", _x, _y, 2.2, angle=_a)
print("v5: %d ORCOM spawns dropped" % _n)

# ============================================================================================== accuracy: the Bakersfield Sign
# (audit of ref_v2/0.jpg, 14.jpg against bklan_sign.py / make_bklan_v2.py)
_SY_S, _SY_N = -3 - BS.HALF, -3 + BS.HALF                                       # tower centres (south, north)
# 1. the letters stand plumb on the real sign (only the baseline follows the arc): bk5_bsign, same size, drawn upright
for _g in GROUPS:
    GROUPS[_g][:] = [s.replace("bk_bsign ", "bk5_bsign ") for s in GROUPS[_g]]
# 2. the band is a clad truss about 2.6 ft deep along the road, not 1.6: the 24 segments drawn again, wider
_n = drop("detail", lambda b: inside(b, SIGN_X - 0.9, -3 - BS.HALF - 0.1, SIGN_X + 0.9, -3 + BS.HALF + 0.1, 16.9, 31.2))
DEPTH5, YC5, N5 = 2.6, -3.0, 24                                    # the road's centre line and 24 segments, as make_bklan_v2.py (its yc / N get rebound later)
xa, xb = u(SIGN_X - DEPTH5 / 2, OX), u(SIGN_X + DEPTH5 / 2, OX)
for k in range(N5):
    sa, sb = -BS.HALF + BS.SPACING * k / N5, -BS.HALF + BS.SPACING * (k + 1) / N5
    ya, yb = u(YC5 + sa, OY), u(YC5 + sb, OY)
    zba, zta, zbb, ztb = u(BS.zb(sa)), u(BS.zt(sa)), u(BS.zb(sb)), u(BS.zt(sb))
    band = spec("bk_bband")
    brush([((xa, ya, zba), (xa, yb, zbb), (xa, ya, zta), (-1, 0, 0), west.replace("bk_bsign", "bk5_bsign")),
           ((xb, ya, zba), (xb, ya, zta), (xb, yb, zbb), (1, 0, 0), east.replace("bk_bsign", "bk5_bsign")),
           ((xa, ya, zba), (xb, ya, zba), (xa, ya, zta), (0, -1, 0), band),
           ((xa, yb, zbb), (xb, yb, zbb), (xa, yb, ztb), (0, 1, 0), band),
           ((xa, ya, zta), (xb, ya, zta), (xa, yb, ztb), (0, 0, 1), band),
           ((xa, ya, zba), (xb, ya, zba), (xa, yb, zbb), (0, 0, -1), band)], "detail")
print("v5: sign band redrawn %.1f ft deep (%d old segments)" % (DEPTH5, _n))
# 3. the SPEED LIMIT 35 sign stands at the curb just west of the south tower, not 30 ft east of it
_n = drop("detail", lambda b: inside(b, SIGN_X + 29.7, SIL_Y0 - 4.6, SIGN_X + 30.4, SIL_Y0 - 1.9, -0.1, 10.1))
prop(SIGN_X - 15, SIL_Y0 - 1.9, 0, SIGN_X - 14.75, SIL_Y0 - 1.65, 9.8, "bk_steel")
prop(SIGN_X - 15.15, SIL_Y0 - 3.0, 7, SIGN_X - 15.0, SIL_Y0 - 0.5, 10, "bk_white", {"w": Fit("bk_speed35"), "e": "bk_white"})
# 4. the south tower's hedge is low (about 2.4 ft) and wraps the west face and the south end, not the outer face
_n += drop("detail", lambda b: inside(b, SIGN_X - 7.6, _SY_S - 7.7, SIGN_X + 7.6, _SY_S - 0.9, 0.4, 3.9) and b[5] > 3.5)
prop(SIGN_X - 7.8, _SY_S - 7.5, WALKZ, SIGN_X - 5.2, _SY_S + 5.5, 2.4, "bk_hedge")
prop(SIGN_X - 7.8, _SY_S - 7.5, WALKZ, SIGN_X + 7.8, _SY_S - 5.0, 2.4, "bk_hedge")
prop(SIGN_X + 5.2, _SY_S - 7.5, WALKZ, SIGN_X + 7.8, _SY_S + 5.5, 2.4, "bk_hedge")
# 5. the tan impost moulding round every base face at the arch springing (7.0-7.7 ft), continuous with the arch trim
for _ty in (_SY_S, _SY_N):
    for _sf in (-1, 1):
        for _a0, _a1 in ((-5.15, -2.85), (2.85, 5.15)):
            prop(SIGN_X + _a0, _ty + _sf * 5 - 0.15, 7.0, SIGN_X + _a1, _ty + _sf * 5 + 0.15, 7.7, "bk_btan")
            prop(SIGN_X + _sf * 5 - 0.15, _ty + _a0, 7.0, SIGN_X + _sf * 5 + 0.15, _ty + _a1, 7.7, "bk_btan")
# 6. warm golden sunlight fill on both faces of the BAKERSFIELD arch + pale cream wash on both towers
for _s in range(-36, 37, 12):
    for _sx in (-1, 1):
        light(SIGN_X + _sx * 4.5, -3 + _s, 23.5, 95, "255 228 165")
for _ty in (_SY_S, _SY_N):
    for _sx in (-1, 1):
        light(SIGN_X + _sx * 8.5, _ty, 18.0, 90, "255 238 196")
# warm exterior architectural pools along E 21st, the LAN lot, and Buck Owens' Crystal Palace
for _lx in (-260, -210, -160, -110, -50, 20):
    light(_lx, -14, 24, 185, "255 232 185")
for _ly in (30, 90, 150):
    light(-125, _ly, 18, 175, "255 235 190")
for _ly in (55, 95, 135):
    light(865, _ly, 20, 170, "255 226 175")
# 8. the north tower's base: low planting at the corners and the grey utility cabinet east of it
for _dx, _dy in ((-6.5, -6.5), (6.5, -6.5), (-6.5, 6.5), (6.5, 6.5)):
    if free(SIGN_X + _dx, _SY_N + _dy, 1.2, 0.6, 2.0):
        prop(SIGN_X + _dx - 1, _SY_N + _dy - 1, WALKZ, SIGN_X + _dx + 1, _SY_N + _dy + 1, 1.9, "bk_hedge")
if free(SIGN_X + 11.5, 45, 2.0, 0.6, 4.0):
    prop(SIGN_X + 10, 44, WALKZ, SIGN_X + 13, 46, 3.5, "bk_steel")
print("v5: sign: speed sign moved, hedge low on the west face, imposts, green lights (%d old brushes)" % _n)

# ============================================================================================== accuracy: Amberton Park
# (audit of the review video's aerials 224/230/236 and Street View 240/243 against make_bklan_v2.py; GIS tags in
# bklan_site_manning.json: the pads are PICNIC TABLE pads, the only building is the shelter)


def _pad_c(wid):
    pts = [M(q) for q in site_way(SITE_M, wid)["pts"][:-1]]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _table(cx, cy, along="y"):
    """One picnic table (the pads hold one each, not two)."""
    if along == "y":
        prop(cx - 1.25, cy - 3, 2.4, cx + 1.25, cy + 3, 2.6, "bk_wood")
        for bx_ in (-2.1, 1.6):
            prop(cx + bx_, cy - 3, 1.4, cx + bx_ + .5, cy + 3, 1.55, "bk_wood")
    else:
        prop(cx - 3, cy - 1.25, 2.4, cx + 3, cy + 1.25, 2.6, "bk_wood")
        for by_ in (-2.1, 1.6):
            prop(cx - 3, cy + by_, 1.4, cx + 3, cy + by_ + .5, 1.55, "bk_wood")
    prop(cx - .2, cy - .2, 0.16, cx + .2, cy + .2, 2.4, "bk_steel")


def _bench(bx_, by_, facing):
    """A park bench, its back on the side away from `facing`."""
    if facing in "ns":
        sg = 1 if facing == "s" else -1
        prop(bx_ - 3, by_ - .8, 1.4, bx_ + 3, by_ + .8, 1.6, "bk_bark")
        prop(bx_ - 3, by_ + sg * .6, 1.6, bx_ + 3, by_ + sg * .85, 2.9, "bk_bark")
        for lx_ in (-2.2, 2.0):
            prop(bx_ + lx_, by_ - .7, 0.14, bx_ + lx_ + .25, by_ + .7, 1.4, "bk_leg")
    else:
        sg = 1 if facing == "w" else -1
        prop(bx_ - .8, by_ - 3, 1.4, bx_ + .8, by_ + 3, 1.6, "bk_bark")
        prop(bx_ + sg * .6, by_ - 3, 1.6, bx_ + sg * .85, by_ + 3, 2.9, "bk_bark")
        for ly_ in (-2.2, 2.0):
            prop(bx_ - .7, by_ + ly_, 0.14, bx_ + .7, by_ + ly_ + .25, 1.4, "bk_leg")


_n = 0
# 1. the "restroom" was invented: GIS 60644823 is a picnic-table pad
_cx, _cy = _pad_c("60644823")
_n += drop("world", lambda b: inside(b, _cx - 9.1, _cy - 8.1, _cx + 9.1, _cy + 8.1, 0.1, 9.1))
_n += drop("detail", lambda b: inside(b, _cx - 11, _cy - 10, _cx + 11, _cy + 10, 8.9, 18))
_table(_cx, _cy)
# 5. the red backflow pad is really by Placer Ct; GIS 60646979 is another table pad
_cx, _cy = _pad_c("60646979")
_n += drop("detail", lambda b: inside(b, _cx - 7.1, _cy - 5.1, _cx + 7.1, _cy + 5.1, 0.1, 3.1))
_table(_cx, _cy)
box(1190, -864, 0, 1200, -856, 0.3, "bk_walk", group="detail")
prop(1195.5, -860.2, 0.3, 1197.5, -859.8, 2.6, "bk_playred")
prop(1196.3, -860.5, 2.6, 1196.7, -859.5, 3.0, "bk_playred")
prop(1190.3, -862.8, 0.3, 1193.8, -859.3, 3.3, "bk_hedge")
prop(1196.2, -860.3, 0.3, 1199.7, -856.8, 3.3, "bk_hedge")
box(1201, -870.5, 0, 1205, -866.5, 0.3, "bk_walk", group="detail")
prop(1202, -869.5, 0.3, 1204.5, -867.5, 3.5, "bk_steel")
# 11. one table per pad: the second table of the other two small pads goes
for _wid in ("60645180", "60645415"):
    _cx, _cy = _pad_c(_wid)
    _n += drop("detail", lambda b, cx_=_cx, cy_=_cy: inside(b, cx_ + 4 - 1.35, cy_ - 3.1, cx_ + 4 + 1.35, cy_ + 3.1, 0.1, 2.7))
# 4. the shelter: a 24 x 40 ft gabled brown-shingle roof on six posts (aerial 224), not a 32 ft square white one
_cx, _cy = _pad_c("60645771")
_n += drop("detail", lambda b: inside(b, _cx - 18.1, _cy - 18.1, _cx + 18.1, _cy + 18.1, 0.1, 16))
for _px in (_cx - 11, _cx + 11):
    for _py in (_cy - 19, _cy, _cy + 19):
        prop(_px - .4, _py - .4, 0.16, _px + .4, _py + .4, 9.5, "bk_bark")
box(_cx - 13, _cy - 21, 9.0, _cx + 13, _cy + 21, 9.6, "bk_white", group="detail")
hiproof([(_cx - 12, _cy - 20), (_cx + 12, _cy - 20), (_cx + 12, _cy + 20), (_cx - 12, _cy + 20)], 9.6, "bk_cpshingle", eave=1.5, pitch=4 / 12)
_table(_cx, _cy - 8)
prop(_cx + 7, _cy + 10, 0.16, _cx + 9, _cy + 11.5, 3.0, "bk_leg")                 # the grill
prop(_cx + 8, _cy + 16, 0.16, _cx + 10, _cy + 18, 3.0, "bk_chairbk")              # the bin
# 2 + 3. the play area is a concrete plaza with two sand pits; the play structure belongs in the west lobe and the
# swing set (long axis north-south) with a tot-lot canopy in the north-east lobe; the light pole out of the swing pit
_play = [M(q) for q in site_way(SITE_M, "60647048")["pts"][:-1]]
_n += drop("detail", lambda b: " bk_sand " in "" or inside(b, 1040, -990, 1160, -855, -0.1, 0.15) and b[5] - b[2] < 0.15)
_n += drop("detail", lambda b: inside(b, 1085, -906.5, 1112, -882, 0.1, 12))                  # the old structure
_n += drop("illus", lambda b: inside(b, 1085, -906.5, 1112, -882, 0.1, 12))
_n += drop("detail", lambda b: inside(b, 1061, -963, 1085, -957, 0.1, 10))                    # the old swing set
_n += drop("illus", lambda b: inside(b, 1061, -963, 1085, -957, 0.1, 10))
_n += drop("detail", lambda b: inside(b, 1127, -883, 1129, -881, 0.1, 21))                    # the light pole in the swing pit
flat_poly(_play, 0, 0.14, "bk_walk", side="bk_walk")
box(1060, -976, 0.14, 1102, -934, 0.18, "bk_sand", group="detail")
box(1108, -900, 0.14, 1144, -870, 0.18, "bk_sand", group="detail")
px0, py0 = M((-427, -272))
for dx, dy in ((0, 0), (8, 0), (8, 8)):
    x, y = px0 + dx, py0 + dy
    for ox, oy in ((0, 0), (5, 0), (5, 5), (0, 5)):
        prop(x + ox - .25, y + oy - .25, 0.18, x + ox + .25, y + oy + .25, 9, "bk_playgreen")
    prop(x, y, 4, x + 5, y + 5, 4.4, "bk_playred")
    pyramid(x - .6, y - .6, x + 5.6, y + 5.6, 9, 11.2, "bk_playteal")
    prop(x - .05, y + .5, 4.4, x + .05, y + 4.5, 6.5, "bk_playred")
prism([(px0 - 9, py0 + 1), (px0, py0 + 1), (px0, py0 + 4), (px0 - 9, py0 + 4)], [0.5, 3.7, 3.7, 0.5], [0.9, 4.1, 4.1, 0.9],
      "bk_playgreen", group="detail")
prism([(px0 + 13, py0 + 13), (px0 + 16, py0 + 13), (px0 + 16, py0 + 22), (px0 + 13, py0 + 22)], [3.7, 3.7, 0.5, 0.5],
      [4.1, 4.1, 0.9, 0.9], "bk_playgreen", group="detail")
sx_, sy_ = 1125.0, -897.0
for oy in (0, 11, 22):                                                           # the swing set along y
    for ox in (-2, 2):
        prop(sx_ + ox - .2, sy_ + oy - .2, 0.18, sx_ + ox + .2, sy_ + oy + .2, 9, "bk_leg")
    prop(sx_ - 2.2, sy_ + oy - .2, 8.8, sx_ + 2.2, sy_ + oy + .2, 9.2, "bk_leg")
prop(sx_ - .3, sy_ - .3, 9, sx_ + .3, sy_ + 22.3, 9.4, "bk_leg")
for oy in (2.5, 7.0, 13.5, 18.0):
    prop(sx_ - .7, sy_ + oy, 1.8, sx_ + .7, sy_ + oy + 2, 2.0, "bk_chairbk")
    prop(sx_ - .05, sy_ + oy + .9, 2.0, sx_ + .05, sy_ + oy + 1.0, 9, "bk_leg", group="illus")
prop(1127.75, -908.25, 0.14, 1128.25, -907.75, 7, "bk_playgreen")               # the tot-lot canopy
pyramid(1123, -913, 1133, -903, 7, 9, "bk_playteal")
prop(1165 - .25, -858 - .25, 0.14, 1165 + .25, -858 + .25, 20, "bk_steel")      # the light pole, on the lawn north-east
prop(1165 - .9, -858 - .9, 20, 1165 + .9, -858 + .9, 20.6, "bk_white")
# 9. benches and drinking fountains at their GIS spots
_n += drop("detail", lambda b: inside(b, 1114.4, -896, 1121.6, -894, 0.1, 3) or inside(b, 1074.4, -977, 1081.6, -975, 0.1, 3))
for _bx, _by, _f in ((1156, -892, "s"), (1098, -891, "s"), (1048, -959, "e")):
    _bench(_bx, _by, _f)
for _fx, _fy in ((978, -994), (1176, -948)):
    box(_fx - 1.5, _fy - 1.5, 0, _fx + 1.5, _fy + 1.5, 0.3, "bk_walk", group="detail")
    prop(_fx - .6, _fy - .6, 0.3, _fx + .6, _fy + .6, 3.0, "bk_steel")
# 8. the path from School House Rd across the lawn was invented; a walk leaves the shelter toward the cul-de-sac


def _near_path(b, path, r=5.0):
    cx_, cy_ = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
    for (ax_, ay_), (bx_, by_) in zip(path, path[1:]):
        L2 = (bx_ - ax_) ** 2 + (by_ - ay_) ** 2
        t = max(0, min(1, ((cx_ - ax_) * (bx_ - ax_) + (cy_ - ay_) * (by_ - ay_)) / L2))
        if math.hypot(cx_ - ax_ - t * (bx_ - ax_), cy_ - ay_ - t * (by_ - ay_)) < r:
            return True
    return False


_old_path = [M(q) for q in ((-430, -15), (-410, -120), (-415, -200))]
_n += drop("detail", lambda b: b[5] <= 0.13 and b[2] >= -0.01 and _near_path(b, _old_path) and b[3] - b[0] < 20 and b[4] - b[1] < 20)
ribbon([(1138, -962), (1165, -985), (1193, -1003)], 6, "bk_walk", z=0.12, side_tex="bk_walk", group="detail")
# 7. the park's south and south-east edges are the neighbours' back fences, not open lawn to the sound wall
box(924, -1096, 0, 1122, -1095.3, 6, "bk_blockgr", group="detail")
_fence = [(1122, -1096), (1196, -1052), (1190, -1038), (1189, -1022), (1193, -1007), (1209, -981)]
for (_ax, _ay), (_bx, _by) in zip(_fence, _fence[1:]):
    _L = math.hypot(_bx - _ax, _by - _ay)
    _nx, _ny = -(_by - _ay) / _L * 0.35, (_bx - _ax) / _L * 0.35
    prism(ccw([(_ax + _nx, _ay + _ny), (_bx + _nx, _by + _ny), (_bx - _nx, _by - _ny), (_ax - _nx, _ay - _ny)]), 0, 6, "bk_blockgr",
          side="bk_blockgr", group="detail")
for _k, _tx in enumerate(range(960, 1110, 36)):
    sprite_tree(_tx, -1101, 26, ("t2", "t3")[_k % 2])
# 10. the AMBERTON PARK monument sign on School House Rd (GIS 60646581)
prop(1011, -741, 0, 1023, -737, 1.2, "bk_walk")
prop(1012, -740.5, 1.2, 1022, -737.5, 4.5, "bk_btan", {"n": Fit("bk5_ambsign"), "s": Fit("bk5_ambsign")})
# 6. the park's trees are mostly tall cedars and pines, with two Italian cypresses: re-kind the sprite trees there
_pk = [k for k in ("pine", "cyp") if k in SPR_TREES]
_re = []
for _s in list(GROUPS["illus"]):
    if "{bk3_tree" in _s:
        _b = ft_bbox(_s)
        _cx, _cy = (_b[0] + _b[3]) / 2, (_b[1] + _b[4]) / 2
        if 780 < _cx < 1215 and -1100 < _cy < -700 and _b[4] - _b[1] < 0.2:          # the x-facing sprite of each pair
            _re.append((_cx, _cy, _b[5]))
if _pk:
    for _cx, _cy, _h in _re:
        GROUPS["illus"][:] = [s for s in GROUPS["illus"] if not ("{bk3_tree" in s and abs((ft_bbox(s)[0] + ft_bbox(s)[3]) / 2 - _cx) < 0.3
                                                                 and abs((ft_bbox(s)[1] + ft_bbox(s)[4]) / 2 - _cy) < 0.3)]
    for _k, (_cx, _cy, _h) in enumerate(_re):
        _kind = ("t1", _pk[0], "t3", _pk[-1], _pk[0], "t4")[_k % 6]
        sprite_tree(_cx, _cy, 55 if _kind == "pine" else 38 if _kind == "cyp" else _h, _kind)
    palm(1200, -820, h=30)
print("v5: park: shelter, play area, pads, benches, fences, %d trees re-kinded (%d old brushes dropped)" % (len(_re), _n))

# ============================================================================================== accuracy: Larry's warehouse (118/120 and the lot)
# (audit of the Street View gallery and the 2001 tape against make_bklan.py / make_bklan_v3.py / make_bklan_v4.py)
_n = 0
_CH = lambda nx, nz: Fit("{chain", (nx / 5.3, nz / 5.3))
# 1. the black steel-mesh security cage just inside the fence at the lot's street end (yaw45 / yaw90 panoramas)
if free(-136.4, 29.85, 5.8, 0.5, 9.5, half_y=5.6):
    for _px, _py in ((-141.8, 24.7), (-131.3, 24.7), (-141.8, 34.7), (-131.3, 34.7)):
        prop(_px, _py, 0, _px + 0.3, _py + 0.3, 8.0, "bk_leg")
    box(-141.8, 24.7, 0, -131.0, 24.8, 8.0, _CH(10.8, 8), group="fence")
    box(-141.8, 34.7, 0, -131.0, 34.8, 8.0, _CH(10.8, 8), group="fence")
    box(-141.8, 24.7, 0, -141.7, 35.0, 8.0, _CH(10.3, 8), group="fence")
    box(-131.1, 24.7, 0, -131.0, 35.0, 8.0, _CH(10.3, 8), group="fence")
    prop(-142.0, 24.5, 8.0, -130.8, 35.0, 8.6, "bk_chairbk")                      # the barrel-vault roof, in two steps
    prop(-141.3, 26.2, 8.6, -131.5, 33.3, 9.4, "bk_chairbk")
    prop(-139.5, 27.5, 0, -136.0, 30.0, 2.0, "bk_redwall")                        # the red things inside
    prop(-135.0, 31.0, 0, -132.5, 33.5, 1.5, "bk_redwall")
else:
    print("v5: no room for the security cage")
# 2. the canopy tents stand near the gate (aerial z20): the blue one 16 ft square at x -123, y 34, the white pyramid one at -117, 64
_n += drop("detail", lambda b: inside(b, -128.1, 104.9, -117.7, 115.3, -0.1, 8.1))
_n += drop("detail", lambda b: inside(b, -112.1, 69.9, -101.7, 80.3, -0.1, 8.1))
if free(-115, 42, 8.2, 0.5, 8.5):
    tent(-123, 34, "bk_tentblue", s=16)
else:
    print("v5: no room for the blue tent")
if free(-109, 72, 8.2, 0.5, 11):
    for _cx, _cy in ((-117, 64), (-101.2, 64), (-117, 80), (-101.2, 80)):
        prop(_cx, _cy, 0, _cx + .2, _cy + .2, 7.5, "bk_steel")
    pyramid(-117, 64, -101.0, 80.2, 7.5, 10.2, "bk_white")
else:
    print("v5: no room for the white tent")
# 3. the shopping cart sitting on the fascia over the BATERIAS sign (both panoramas)
for _wx, _wy in ((-217.8, 22.7), (-215.4, 22.7), (-217.8, 24.0), (-215.4, 24.0)):
    prop(_wx, _wy, PARA + 0.5, _wx + 0.4, _wy + 0.4, PARA + 0.9, "bk_chairbk")
    prop(_wx + .15, _wy + .15, PARA + 0.9, _wx + 0.25, _wy + 0.25, PARA + 1.7, "bk_leg")
box(-218, 22.6, PARA + 1.7, -215, 24.4, PARA + 3.3, _CH(3, 1.6), group="fence")
prop(-215.1, 22.5, PARA + 3.3, -214.9, 24.5, PARA + 3.5, "bk_leg")
# 4. the roof mast is an A-frame above the 120B piers (pitch25 panorama), not a pole over the 120A door; an HVAC box at the east end
_n += drop("detail", lambda b: inside(b, -196.5, 31.4, -189.5, 32.6, ROOF_TOP - 0.1, ROOF_TOP + 12.5))
for _k in range(10):
    _z0, _z1 = ROOF_TOP + _k * 0.9, ROOF_TOP + (_k + 1) * 0.9
    prop(-182 + _k * 0.4, 29.85, _z0, -181.7 + _k * 0.4, 30.15, _z1, "bk_steel")
    prop(-174.3 - _k * 0.4, 29.85, _z0, -174 - _k * 0.4, 30.15, _z1, "bk_steel")
prop(-180.3, 29.85, ROOF_TOP + 4, -175.7, 30.15, ROOF_TOP + 4.3, "bk_steel")
prop(-153, 28, ROOF_TOP, -147, 32, ROOF_TOP + 5, "bk_beige", {"t": "bk_steel"})
prop(-159, 29, ROOF_TOP, -155, 32, ROOF_TOP + 4.5, "bk_beige", {"t": "bk_steel"})
# 5. the lot's north end (tape 66-67 s): the block wall covers only the west part, then a steel post, an open chain-link gate,
# plain chain-link with barbed wire. The owner's walk-out gap at x -100..-88 (make_bklan_v4.py) stays.
_n += drop("world", lambda b: inside(b, -143.1, 186.9, -99.9, 187.8, -0.1, 8.1))
_n += drop("fence", lambda b: inside(b, -143.1, 187.1, -87.9, 187.5, 7.9, 14.1))
_n += drop("detail", lambda b: inside(b, -121, 187.0, -87, 187.6, 7.9, 14.6))
box(-143.0, 187.0, 0, -122.0, 187.67, 8.0, "bk_blockgr")
box(-143.0, 187.2, 8, -122.0, 187.4, 14, _CH(21, 6), group="fence")
prop(-122.3, 187.0, 0, -121.7, 187.7, 8.0, "bk_brown")                             # the rusty post at the wall's end
for _gz0, _gz1 in ((0, 0.2), (6.8, 7.0)):                                          # the gate leaf, swung open into the yard
    prop(-121.8, 187.7, _gz0, -121.6, 195.7, _gz1, "bk_brown")
prop(-121.8, 195.5, 0, -121.6, 195.7, 7.0, "bk_brown")
box(-121.75, 187.8, 0.2, -121.65, 195.5, 6.8, _CH(7.7, 6.6), group="fence")
box(-114.0, 187.3, 0, -100.0, 187.4, 7.0, _CH(14, 7), group="fence")
prop(-114.2, 187.2, 0, -113.8, 187.5, 7.6, "bk_steel")
prop(-107.2, 187.2, 0, -106.8, 187.5, 7.6, "bk_steel")
prop(-114.0, 187.3, 7.5, -100.0, 187.4, 7.6, "bk_steel")                           # the barbed wire strand
# 6. the 2026 front of 118/120 is bright white, not tan: white stucco and fascia on the street face only
_wh = 0
for _g in ("world", "detail"):
    for _i, _s in enumerate(GROUPS[_g]):
        if " bk_stucco " not in _s and " bk_fascia " not in _s:
            continue
        _b = ft_bbox(_s)
        if inside(_b, -231, 21.5, -142, 24.8, -0.1, 20.1) or inside(_b, -231, 23.9, -228.9, 30.1, 11.4, 20.1):
            GROUPS[_g][_i] = _s.replace(" bk_stucco ", " bk5_white ").replace(" bk_fascia ", " bk5_fascia ")
            _wh += 1
# 8. the 120B storefront rhythm (panels in facade units of 74 over the 86 ft front): blue | glass | door | red | white | blue |
# glass | red | door | white | blue; flush panels laid over the old faces
for _a, _b2, _t, _z1 in ((52, 54, "bk_bluep", 9), (54, 57, "bk4_win", 7.5), (57, 59.5, "bk_blkdoor", 7.5), (59.5, 61.5, "bk_redp", 9),
                         (61.5, 63, "bk5_white", 9), (63, 65, "bk_bluep", 9), (65, 68, "bk4_win", 7.5), (68, 70, "bk_redp", 9),
                         (70, 72.5, "bk_blkdoor", 7.5), (72.5, 73, "bk5_white", 9), (73, 74, "bk_bluep", 9)):
    prop(B76[0] + _a * sx, B76[1] - 0.1, 0, B76[0] + _b2 * sx, B76[1], _z1, "bk5_white", {"s": Fit(_t)})
# 10. the lime ORTIZ Auto Body banner on the fascia over BATERIAS (the 115 E 21st panorama)
prop(-221, 22.42, 13.5, -211, 22.5, 18.5, "bk_steel", {"s": Fit("bk5_ortiz")})
# 7. B45's E 21st face is all white with a round monogram near the corner and a dark open bay toward the west end, no red band
prop(-55.2, 22.85, 0, -44.8, 23.0, WALL_H, "bk5_white")
prop(-76.2, 22.85, 0, -74, 23.0, 7.2, "bk5_white")
prop(-74, 22.85, 0, -64, 23.0, 10, "bk_blkdoor", {"s": Fit("bk_blkdoor")})
prop(-44, 22.85, 13, -40, 23.0, 17, "bk5_white", {"s": Fit("bk5_cblogo")})
print("v5: Larry's: cage, tents moved, cart, A-frame, north fence, white front (%d brushes), 120B panels, ORTIZ, B45 face (%d old brushes)" % (_wh, _n))

# ============================================================================================== accuracy: 1608 Manning St
# (audit of the review video frames 154-219 s and the GIS against make_bklan_v2.py / v3)
_n = 0
# 5. the "1608" kerb sign stood in the driveway apron: onto the lawn north of the front walk
_n += drop("detail", lambda b: inside(b, 1603.3, -605.7, 1605.1, -602.5, -0.1, 10.1))
if "bk3_1608" in TEXSIZE:
    prop(1604.0, -577.3, 0, 1604.4, -576.9, 4.6, "bk_steel")
    prop(1603.9, -578.5, 4.6, 1604.5, -575.7, 6.2, "bk_steel", {"w": Fit("bk3_1608"), "e": Fit("bk3_1608")})
# 1. the driveway's light-blue pickup and grey Fit are back (v3 kept only the lime car), as exploding vehicles like the rest
ent("misc_vehicle_truck", 1622, -608, 0.2, angle=0)
ent("misc_vehicle_coupe", 1604.5, -606.5, 0.2, angle=0)
# 3. the palm stands between the walk and the driveway against the house, not in front of the north wing's windows
_n += drop("detail", lambda b: inside(b, 1618, -562, 1634, -546, -0.1, 24))
_n += drop("illus", lambda b: inside(b, 1618, -562, 1634, -546, -0.1, 24))
palm(1625, -590, h=18)
# 2. the big magnolia at the lot's street corner (culled by v3) and the tall sycamore by the walk
_n += drop("illus", lambda b: inside(b, 1600, -586, 1628, -558, 0.4, 25) and "{bk3_tree" in "x")
for _s in list(GROUPS["illus"]):
    if "{bk3_tree" in _s and inside(ft_bbox(_s), 1600, -586, 1628, -558, 0.4, 25):
        GROUPS["illus"].remove(_s)
        _n += 1
_n += drop("detail", lambda b: inside(b, 1613.4, -572.7, 1614.7, -571.3, -0.1, 8.1))
sprite_tree(1610, -557, 34, "t4")
sprite_tree(1614, -574, 40, "t1")
if free(1700, -560, 1.0, 0.5, 6):
    sprite_tree(1700, -560, 31, "t4")
# 6. the side-yard wood fence and gate flush with the garage front, the hedge along the driveway's south edge
prop(1631.6, -624, 0, 1632.0, -616, 6, "bk_wood")
prop(1631.4, -616.6, 0, 1632.2, -615.8, 7, "bk_white")
prop(1604, -617, 0, 1630, -614.5, 3, "bk_hedge")
prop(1624, -623, 0, 1630, -617.5, 5, "bk_hedge")
# 9. the yellow fire hydrant at the lawn edge between the walk and the mailbox
_hy = "bk_capriylw" if "bk_capriylw" in TEXSIZE else "bk_yline"
prop(1603.6, -587.3, 0, 1604.4, -586.5, 2.4, _hy)
prop(1603.8, -587.1, 2.4, 1604.2, -586.7, 2.8, _hy)
# 4. Club View Drive, the cross street east of Manning at y -800 (OSM 10431684; Street View 174 s): the east sidewalk
# broken for it, the road as far east as the first thing in its way, blade sign, the corner planter with two palms
_n += drop("detail", lambda b: inside(b, MAN_X + 17.9, YB - 0.1, MAN_X + 23.1, -39.9, -0.1, 0.6) and b[4] - b[1] > 900)
box(MAN_X + 18, YB, 0, MAN_X + 23, -823, WALKZ, "bk_walk", group="detail")
box(MAN_X + 18, -777, 0, MAN_X + 23, -40, WALKZ, "bk_walk", group="detail")
_cvx1 = XB - 8
for _sb in SOLIDS:
    _bx0, _by0, _bz0, _bx1, _by1, _bz1 = _sb[0] / U + OX, _sb[1] / U + OY, _sb[2] / U, _sb[3] / U + OX, _sb[4] / U + OY, _sb[5] / U
    if _bx0 > MAN_X + 30 and _by0 < -777 and _by1 > -823 and _bz0 < 3 and _bz1 > 1 and _bx0 < _cvx1:
        _cvx1 = _bx0 - 10
box(MAN_X + 18, -818, 0, _cvx1, -782, ROADZ, "bk_road", {"n": "bk_walk", "s": "bk_walk", "e": "bk_walk"}, group="detail")
box(MAN_X + 23, -823, 0, _cvx1, -818, WALKZ, "bk_walk", group="detail")
box(MAN_X + 23, -782, 0, _cvx1, -777, WALKZ, "bk_walk", group="detail")
prop(MAN_X + 24 - 0.2, -824.2, 0, MAN_X + 24 + 0.2, -823.8, 10, "bk_steel")
prop(MAN_X + 24 - 2.6, -824.15, 8.4, MAN_X + 24 + 2.6, -823.85, 9.8, "bk_steel", {"n": Fit("bk5_clubview"), "s": Fit("bk5_clubview")})
prop(1604, -834, 0, 1618, -824, 1.0, "bk_brick")
prop(1604.5, -833.5, 1.0, 1617.5, -824.5, 2.5, "bk_hedge")
palm(1607, -826.5, h=28)
palm(1614, -831.5, h=30)
print("v5: Club View Drive east to x %.0f" % _cvx1)
# 7. the neighbours show a white sectional garage door at the driveway, and are white stucco, not grey panels
_gd = 0
for _k, _w in enumerate(SITE_M["ways"]):
    if "building" not in _w["tags"] or not all(ZONE_M(q) for q in _w["pts"]) or _w["id"] == HERO:
        continue
    _fp = [M(q) for q in _w["pts"][:-1]]
    _xs, _ys = [p[0] for p in _fp], [p[1] for p in _fp]
    _bb = (min(_xs) - 0.1, min(_ys) - 0.1, max(_xs) + 0.1, max(_ys) + 0.1)
    if walls[_k % 4] == "bk_stucco":
        for _i, _s in enumerate(GROUPS["world"]):
            if " bk_stucco " in _s and inside(ft_bbox(_s), _bb[0], _bb[1], _bb[2], _bb[3], -0.1, 9.1):
                GROUPS["world"][_i] = _s.replace(" bk_stucco ", " bk5_white ")
    _cy = sum(_ys) / len(_ys) - 12
    for _side, _xw in (("w", min(_xs)), ("e", max(_xs))):
        if _side == "w" and not (abs(_xw - (MAN_X + 23)) < 60 and _xw > MAN_X):
            continue
        if _side == "e" and not (abs(_xw - (MAN_X - 23)) < 60 and _xw < MAN_X):
            continue
        _edge = any(abs(a[0] - _xw) < 1 and abs(b[0] - _xw) < 1 and min(a[1], b[1]) <= _cy - 8 and max(a[1], b[1]) >= _cy + 8
                    for a, b in zip(_fp, _fp[1:] + _fp[:1]))
        if _edge:
            if _side == "w":
                prop(_xw - 0.12, _cy - 8, 0, _xw, _cy + 8, 7, "bk_garage", {"w": Fit("bk_garage")})
            else:
                prop(_xw, _cy - 8, 0, _xw + 0.12, _cy + 8, 7, "bk_garage", {"e": Fit("bk_garage")})
            _gd += 1
# 8. the white motorhome nose-to-street in the driveway two lots south (aerials 197-215 s)
if free(1618, -742, 12.5, 0.5, 11, half_y=4.5):
    prop(1606, -746.1, 0.9, 1630, -737.9, 1.6, "bk_chairbk")
    prop(1606, -746, 1.6, 1630, -738, 10.5, "bk_white")
    prop(1605.9, -745.9, 5.0, 1606.0, -738.1, 7.5, "bk_glass")
    for _tx, _ty in ((1609, -746.2), (1609, -738.4), (1625, -746.2), (1625, -738.4)):
        prop(_tx, _ty, 0, _tx + 2.4, _ty + 0.6, 1.4, "bk_tire")
# 10. the parked sedan across the mouth of School House Rd
_n += _drop_ents(lambda c, x, y, z: c.startswith("misc_vehicle") and abs(x - 1567) < 4 and abs(y + 660) < 6)
# 11. the Italian cypresses along the west sidewalk opposite 1608 / 1612
if "cyp" in SPR_TREES:
    for _y in range(-548, -500, 9):
        sprite_tree(1554, _y, 35, "cyp")
# 12. the residential stretch of Manning has no centre line
_n += drop("illus", lambda b: inside(b, MAN_X - 0.3, -470.1, MAN_X + 0.3, -39.9, -0.1, 0.2))
lines_y(-250, SIL_Y0 - 6, MAN_X, "bk_yline")
print("v5: Manning: cars, trees, palm, Club View Dr, fence, hydrant, %d garage doors, RV (%d old brushes/ents)" % (_gd, _n))

V3_SPOTS += V5_SPOTS
