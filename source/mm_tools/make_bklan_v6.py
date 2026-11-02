"""bklan5 (make_bklan_v6.py): combines The Historic Bakersfield Fox Theater & Downtown Bakersfield (fox.map)
directly inside bklan4's south-central pocket (Box D: x = -420..+650, y = -1322..-340), connecting:
  - West: S Union Ave & Golden West Casino (Box C) via 20th St & 21st St
  - North: Larry's Warehouse, E 21st St, LMC plaza & Sonora St (Box A)
  - East: Buck Owens Blvd, Crystal Palace, Bakersfield Sign, Amberton Park & Manning St (Box B)

Exec'd by make_bklan5.py right after make_bklan_v5.py (without modifying make_bklan.py or bklan4).
"""
import bks_mapio as _mio  # noqa: E402

WAD3 = WAD3 + ";fox.wad;bklan6.wad"
for _wn in ("fox.wad", "bklan6.wad"):
    with open(os.path.join(HERE, "out", "maps", _wn), "rb") as _f:
        _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
        _f.seek(_ofs)
        _dirs = [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]
        for _pos, _, _, _, _, _, _name in _dirs:
            _f.seek(_pos)
            _nm, _w, _h = struct.unpack("<16s2I", _f.read(24))
            TEXSIZE.setdefault(_name.split(b"\0")[0].decode(), (_w, _h))
assert len(WAD + ";" + WAD3) < 127, ("wad key too long:", len(WAD + ";" + WAD3), WAD + ";" + WAD3)

V6_SPOTS = []

# ==============================================================================
# 1. BOX D HULL: OPEN THE SOUTH-CENTRAL + SE POCKET & SEAL WATERTIGHT AROUND FOX
# ==============================================================================
XD0, XD1, XD2 = -420.0, 650.0, 1192.0   # Main pocket (-420..650) + southern East-of-Chester wing (650..1192)
YD0, YD1 = -1518.0, -340.0              # South past 18th St (-1518) up to Box A south edge (-340)

# Remove the interior hull walls bounding the pocket (Box A south, Box C east, Box B west, Box B south x=650..1870):
_nd = 0
# 1) Box A south sky_bk, clip, and bk3_sw along y = -340, x = -420..650
_nd += drop("world", lambda b: inside(b, XD0 - 1.5, YD1 - 1.5, XD1 + 1.5, YD1 + 0.5, -3.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD0 - 5.0, YD1 - 0.5, XD1 + 0.5, YD1 + 4.5, -0.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD0 - 8.0, YD1 + 4.5, XD1 + 0.5, YD1 + 7.5, -0.5, 37.0) and (b[3] - b[0]) > 500)
# 2) Box C east sky_bk, clip, and bk3_sw along x = -420, y = -1000..-340
_nd += drop("world", lambda b: inside(b, XD0 - 1.5, YC0 - 1.5, XD0 + 1.5, YD1 + 0.5, -3.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD0 - 4.5, YC0 - 0.5, XD0 + 0.5, YD1 + 0.5, -0.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD0 - 7.5, YC0 + 4.5, XD0 - 4.5, YD1 + 7.5, -0.5, 37.0) and (b[4] - b[1]) > 400)
# 3) Box B west sky_bk, clip, and bk3_sw along x = 650, y = -1110..-340
_nd += drop("world", lambda b: inside(b, XD1 - 1.5, YB - 1.5, XD1 + 1.5, YD1 + 0.5, -3.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD1 - 0.5, YB - 0.5, XD1 + 4.5, YD1 + 0.5, -0.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD1 + 4.5, YB - 0.5, XD1 + 7.5, YD1 + 0.5, -0.5, 37.0) and (b[4] - b[1]) > 400)
# 4) Box B south sky_bk, clip, and bk3_sw along y = -1110, x = 650..1870 (re-emitted east of XD2 = 1192 below)
_nd += drop("world", lambda b: inside(b, XD1 - 1.5, YB - 1.5, XB + 1.5, YB + 0.5, -3.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD1 - 0.5, YB - 0.5, XB + 0.5, YB + 4.5, -0.5, SKY_Z + 0.5) and b[5] > 100)
_nd += drop("world", lambda b: inside(b, XD1 - 0.5, YB + 4.5, XB + 0.5, YB + 7.5, -0.5, 37.0) and (b[3] - b[0]) > 500)

# Re-seal Box B's south edge east of XD2 (x = 1192..1870) where Box D2 ends:
box(XD2 - 1, YB - 1, -3.0, XB + 1, YB, SKY_Z, "sky_bk")
box(XD2 - 4, YB, 0.0, XB, YB + 4, SKY_Z, "clip")
box(XD2 - 3, YB + 5, 0.0, XB, YB + 7, 36.0, tspec("bk3_sw", 8), {"t": "bk3_sw"})

# Fox coordinate mapping: fox local feet -> bklan4 map feet
FOX_SO = (220.0, -118.0)
FOX_DX, FOX_DY = -52.0, -684.0


def F(fx, fy):
    """Fox local feet -> bklan map feet."""
    return fx + FOX_DX, fy + FOX_DY


# Seal Box D1 + D2 floor (z = -15.0..-13.0 under BOTH the -3.5ft Orchestra Pit & -11.5ft Padre Basement Gym!)
# + watertight seam skirts up to z = -2.0 + 500-ft sky ceiling lids:
box(XD0 - 1, YD0 - 1, -15.0, XD1 + 1, YD1 + 1, -13.0, "bk_dirt")
box(XD1, YD0 - 1, -15.0, XD2 + 1, YB + 1, -13.0, "bk_dirt")
box(XD0 - 1, YC0 - 1, -15.0, XD0 + 1, YD1 + 1, -2.0, "bk_dirt")       # West seam skirt under Box C
box(XD0 - 1, YD1 - 1, -15.0, XD1 + 1, YD1 + 1, -2.0, "bk_dirt")       # North seam skirt under Box A
box(XD1 - 1, YB - 1, -15.0, XD1 + 1, YD1 + 1, -2.0, "bk_dirt")        # East D1 seam skirt under Box B
box(XD1 - 1, YB - 1, -15.0, XD2 + 1, YB + 1, -2.0, "bk_dirt")         # North D2 seam skirt under Box B
box(XD0 - 1, YD0 - 1, SKY_Z, XD1 + 1, YD1 + 1, SKY_Z + 1, "sky_bk")
box(XD1, YD0 - 1, SKY_Z, XD2 + 1, YB + 1, SKY_Z + 1, "sky_bk")

# Exterior sky walls for Box D1 + D2 (full south wall, west tail south of Box C, east D2 wall south of Box B):
box(XD0 - 1, YD0 - 1, -15.0, XD2 + 1, YD0, SKY_Z, "sky_bk")           # South sky wall (y = -1518, x = -421..1193)
box(XD0 - 1, YD0 - 1, -15.0, XD0, YC0 + 1, SKY_Z, "sky_bk")           # West tail sky wall (y = -1518..-1000)
box(XD2, YD0 - 1, -15.0, XD2 + 1, YB + 1, SKY_Z, "sky_bk")            # East D2 sky wall (x = 1192, y = -1518..-1110)

# Exterior clip walls & 36-ft bk3_sw perimeter sound walls along Box D's true outer edges:
for _cx0, _cy0, _cx1, _cy1 in (
    (XD0, YD0, XD2, YD0 + 4),
    (XD0, YD0, XD0 + 4, YC0 + 4),
    (XD2 - 4, YD0, XD2, YB + 4),
):
    box(_cx0, _cy0, 0.0, _cx1, _cy1, SKY_Z, "clip")
for _sx0, _sy0, _sx1, _sy1 in (
    (XD0 + 1, YD0 + 2, XD2 - 1, YD0 + 4),       # South sound wall (y = -1516..-1514, clear of y = -1508!)
    (XD0 + 1, YD0 + 4, XD0 + 3, YC0 + 5),       # West tail sound wall, meeting Box C's south wall
    (XD0 - 6, YC0 + 5, XD0 + 3, YC0 + 7),       # Corner bridge closing x = -426..-417 at y = -995..-993
    (XD2 - 3, YD0 + 4, XD2 - 1, YB + 5),        # East D2 sound wall (x = 1189..1191, meeting Box B south wall at y = -1105)
):
    box(_sx0, _sy0, 0.0, _sx1, _sy1, 36.0, tspec("bk3_sw", 8), {"t": "bk3_sw"})

# Box D1 road-level ground slab (z = -13.0 .. 0.0) cut around BOTH Fox Orchestra Pit & Padre Basement 24-Hr Gym!
_PX0, _PY0 = F(-75.0, 136.5)
_PX1, _PY1 = F(-33.0, 148.0)
_GX0, _GY0 = F(-52.0, -658.0)
_GX1, _GY1 = F(-4.0, -604.0)
_SY = F(0.0, -200.0)[1]
_FOX_ROAD = tspec("bk_road", 16)
# North half of Box D1 (_SY .. YD1) around Fox Orchestra Pit:
box(XD0, _SY, -13.0, XD1, _PY0, 0.0, _FOX_ROAD)
box(XD0, _PY1, -13.0, XD1, YD1, 0.0, _FOX_ROAD)
box(XD0, _PY0, -13.0, _PX0, _PY1, 0.0, _FOX_ROAD)
box(_PX1, _PY0, -13.0, XD1, _PY1, 0.0, _FOX_ROAD)
# South half of Box D1 (YD0 .. _SY) around Padre Sub-Grade Basement Gym:
box(XD0, YD0, -13.0, XD1, _GY0, 0.0, _FOX_ROAD)
box(XD0, _GY1, -13.0, XD1, _SY, 0.0, _FOX_ROAD)
box(XD0, _GY0, -13.0, _GX0, _GY1, 0.0, _FOX_ROAD)
box(_GX1, _GY0, -13.0, XD1, _GY1, 0.0, _FOX_ROAD)
# Box D2 ground slab (east wing south of Amberton Park): road + flush park lawn extension north of Wall St East!
box(XD1, YD0, -13.0, XD2, -1194.0, 0.0, _FOX_ROAD)
box(XD1, -1194.0, -13.0, 763.0, YB, 0.0, _FOX_ROAD)
box(763.0, -1194.0, -13.0, XD2, YB, 0.0, "bk_lawn")
print("v6: Box D1+D2 hull opened & sealed (%d interior hull brushes removed)" % _nd)

# ==============================================================================
# 2. CUT & SHIFT FOX THEATER + PADRE HOTEL + DOWNTOWN FROM out/maps/fox.map
# ==============================================================================
# Always read the latest out/maps/fox.map (built from make_fox.py + padre_hotel.py + fox_neighborhood.py,
# including all 29 custom progs/fox/*.md3 models, murals, boutique wallpapers & {farm_sign alpha signage):
_FOX_MAP_PATH = os.path.join(HERE, "out", "maps", "fox.map")
if not os.path.exists(_FOX_MAP_PATH):
    _FOX_MAP_PATH = os.path.join(HERE, "out", "bk5", "fox.map")
_FX = _mio.read_map(_FOX_MAP_PATH)
_foff = (
    int(round(U * (FOX_SO[0] + FOX_DX - OX))),
    int(round(U * (FOX_SO[1] + FOX_DY - OY))),
    0,
)
_FTAG = {
    "worldspawn": "world",
    "func_detail": "detail",
    "func_wall": "fence",
    "func_detail_illusionary": "illus",
}


def _fx_box_ok(bx0, by0, bx1, by1):
    # 1) Main West-of-Chester Downtown (G St crosswalks to Chester Ave, south of 18th St up to 21st St)
    if -363.0 <= bx0 and bx1 <= 703.0 and -826.0 <= by0 and by1 <= 342.0:
        return True
    # 2) Southern East-of-Chester strip south of Amberton Park (Wall St East, The 18hundred, K St Garage, 18th St East)
    if -363.0 <= bx0 and bx1 <= 1235.0 and -826.0 <= by0 and by1 <= -518.5:
        return True
    # 3) Bakersfield Central Fire Station at NW 21st & H (inside empty Box A asphalt)
    if -130.0 <= bx0 and bx1 <= 20.0 and 330.0 <= by0 and by1 <= 416.5:
        return True
    return False


def _fx_in(fx, fy):
    return _fx_box_ok(fx, fy, fx, fy)


_fnb = _fne = 0
for _e in _FX:
    if _e.cls in _FTAG:
        for _b in _e.brushes:
            _bx0 = _b.lo[0] / U + FOX_SO[0]
            _by0 = _b.lo[1] / U + FOX_SO[1]
            _bx1 = _b.hi[0] / U + FOX_SO[0]
            _by1 = _b.hi[1] / U + FOX_SO[1]
            _bz0, _bz1 = _b.lo[2] / U, _b.hi[2] / U
            if "sky_bk" in _b.texs or ("clip" in _b.texs and _bz1 > 140.0):
                continue
            if not _fx_box_ok(_bx0, _by0, _bx1, _by1):
                continue
            # Skip fox.map's wide outer ground/hull slabs below 0 while keeping ALL Fox Orchestra Pit
            # and Padre Sub-Grade Basement 24-Hr Gym floors, walls, mirrors, stairs & gym machines!
            if _bz1 <= 0.0 and (_bx1 - _bx0) > 100.0:
                continue
            _mb = _b.moved(_foff)
            GROUPS[_FTAG[_e.cls]].append(_mb.text())
            if _FTAG[_e.cls] != "illus" and (_mb.hi[2] - _mb.lo[2]) > 2:
                SOLIDS.append(_mb.lo + _mb.hi)
            _fnb += 1
        continue
    if _e.cls in ("worldspawn", "info_player_start"):
        continue
    if _e.brushes:
        # Brush entities in fox.map: trigger_push (alley, clock tower, garage roof, Padre elevators & Prairie Fire)
        # & trigger_teleport (tp_tower_deck)
        _b0 = _e.brushes[0]
        _cx = (_b0.lo[0] + _b0.hi[0]) / (2 * U) + FOX_SO[0]
        _cy = (_b0.lo[1] + _b0.hi[1]) / (2 * U) + FOX_SO[1]
        if not _fx_in(_cx, _cy):
            continue
        ENTS.append(_e.text(_foff))
        if _e.cls == "trigger_push":
            PADS.append(F(_cx, _cy))
        _fne += 1
        continue
    _o = _e.origin()
    if _o is None:
        continue
    _fx_x, _fx_y, _fx_z = _o[0] / U + FOX_SO[0], _o[1] / U + FOX_SO[1], _o[2] / U
    if not _fx_in(_fx_x, _fx_y):
        continue
    # Nudge the pickup truck at (48, 222) on H St to the east curb (61.5, 222) so the H St northbound cruiser lane is clear!
    if _e.cls == "misc_vehicle_truck" and abs(_fx_x - 48.0) < 2.0 and abs(_fx_y - 222.0) < 2.0:
        ent("misc_vehicle_truck", *F(61.5, 222.0), _fx_z, angle=90)
        _fne += 1
        continue
    # Combat+ replaces weapon_nailgun with weapon_supernailgun + dmg=1 (avoids startup entity warning):
    if _e.cls == "weapon_nailgun":
        _e = _mio.Ent(dict(_e.kv, classname="weapon_supernailgun", dmg="1"), _e.brushes)
    if _e.cls.startswith(("info_player_", "item_", "weapon_")):
        PLACED.append((_e.cls, (_o[0] + _foff[0], _o[1] + _foff[1], _o[2] + _foff[2])))
    ENTS.append(_e.text(_foff))
    _fne += 1
print("v6: Fox Theater, Padre Hotel & Downtown merged: %d brushes, %d entities" % (_fnb, _fne))

# ==============================================================================
# 3. SEAMLESS STREET & SIDEWALK CONNECTIONS ON WEST, EAST, SE & NORTH SEAMS
# ==============================================================================
# E-W Downtown street carriageways in bklan4 map feet (with FOX_DY = -684):
#   21st St: y = -400 .. -352 (center -376)
#   20th St: y = -748 .. -700 (center -724, main Fox Marquee street!)
#   19th St: y = -1084 .. -1036 (center -1060, Nile Theater & Ovation Theatre!)
#   Wall St: y = -1230 .. -1202 (center -1216)
#   18th St: y = -1412 .. -1364 (center -1388, Padre Hotel, Gear Mural & The 18hundred!)
#   G St:    x = -404 .. -356 (center -380)
#   H St:    x = -36 .. +16   (center -10)
#   Eye St:  x = +308 .. +356 (center +332)

# --- A. West Seam: Connect 21st St & 20th St directly into S Union Ave (UNX1 = -488) & Golden West Casino! ---
# Trim Box C's continuous east sidewalk (-488..-480, -995..-340) & hedge at 21st St, plus the 2 cars blocking 20th St:
drop("detail", lambda b: inside(b, -488.5, -996.0, -479.5, -339.5, -0.1, 0.7))
drop("detail", lambda b: inside(b, -479.5, -385.0, -476.0, -350.0, -0.1, 3.5))
_drop_ents(lambda c, x, y, z: c.startswith("misc_vehicle_") and -465 < x < -440 and -748 < y < -695)
_drop_brush_ents(lambda c, b: c == "trigger_push" and inside(b, -470, -366, -458, -354, 0, 6))
drop("detail", lambda b: inside(b, -470, -366, -458, -354, -0.1, 1.0))

# Rebuild S Union Ave's east sidewalk broken cleanly at 20th St (-748..-702) and 21st St (-400..-352):
for _sya, _syb in ((-995.0, -748.0), (-699.0, -400.0), (-352.0, -340.0)):
    box(UNX1, _sya, 0.0, UNX1 + 8.0, _syb, WALKZ, "bk_walk", group="detail")

# Paved 21st St & 20th St carriageways bridging S Union Ave (-488) <-> G St (-404):
for _ry0, _ry1, _ryc in ((-400.0, -352.0, -376.0), (-748.0, -700.0, -724.0)):
    box(UNX1, _ry0, -1 / U, -404.0, _ry1, ROADZ, "bk_road", group="detail")
    box(UNX1 + 6.0, _ryc - 0.5, 0.0, -406.0, _ryc - 0.15, 0.08, "bk_yline", group="illus")
    box(UNX1 + 6.0, _ryc + 0.15, 0.0, -406.0, _ryc + 0.5, 0.08, "bk_yline", group="illus")
    # Sidewalks flanking the connector streets & west side of G St (-420..-404)
    box(UNX1 + 8.0, _ry0 - 8.0, 0.0, -404.0, _ry0, WALKZ, "bk_walk", group="detail")
    box(UNX1 + 8.0, _ry1, 0.0, -404.0, _ry1 + 8.0, WALKZ, "bk_walk", group="detail")
# West sidewalk of G St (-418..-404), broken cleanly at 18th St, Wall St, 19th St, 20th St, and 21st St:
for _gya, _gyb in (
    (-1512.0, -1412.0),
    (-1364.0, -1230.0),
    (-1202.0, -1084.0),
    (-1036.0, -748.0),
    (-700.0, -400.0),
):
    box(-418.0, _gya, 0.0, -404.0, _gyb, WALKZ, "bk_walk", group="detail")
# Relocate the parked cars neatly along the curbed lot north of 20th St:
if free(-448.0, -672.0, 5.0, 1.0, 8.0, half_y=10.0):
    ent("misc_vehicle_sedan", -448.0, -672.0, 0.2, angle=90)
if free(-448.0, -772.0, 5.0, 1.0, 8.0, half_y=10.0):
    ent("misc_vehicle_coupe", -448.0, -772.0, 0.2, angle=90)

# --- B. East & SE Seam: Connect 21st/20th/19th/Wall/18th into Buck Owens Blvd & Amberton Park South! ---
# Split Buck Owens Blvd's west sidewalk (669..677, -1110..-40) at the Downtown street mouths & extend south to Wall St (-1202):
drop("detail", lambda b: inside(b, 668.5, -1110.5, 677.5, -39.5, -0.1, 0.6))
for _bya, _byb in ((-1202.0, -1084.0), (-1036.0, -748.0), (-700.0, -400.0), (-352.0, -40.0)):
    box(669.0, _bya, 0.0, 677.0, _byb, WALKZ, "bk_walk", group="detail")
    if _bya < -360.0:
        box(650.0, _bya, 0.0, 669.0, min(_byb, -340.0), WALKZ, "bk_walk", group="detail")

# Break Buck Owens Blvd's center median (715..725) at 20th St (-748..-700) and extend south to Wall St (-1196):
drop("detail", lambda b: inside(b, 714.5, -1110.5, 725.5, -109.5, -0.1, 0.6))
for _mya, _myb in ((-1196.0, -752.0), (-696.0, -110.0)):
    box(715.0, _mya, 0.0, 725.0, _myb, WALKZ, "bk_lawn", {"e": "bk_walk", "w": "bk_walk", "n": "bk_walk", "s": "bk_walk"}, group="detail")
# Remove any sprite tree right in the 20th & Buck Owens median gap (715..725, -756..-692):
drop("detail", lambda b: inside(b, 713.0, -756.0, 727.0, -692.0, -0.1, 12.0))
drop("illus", lambda b: inside(b, 705.0, -764.0, 735.0, -684.0, 0.2, 45.0))

# Extend Buck Owens Blvd carriageway (677..763) & east sidewalk (763..771) south from YB (-1110) into Wall St & Chester Ave South:
box(677.0, -1202.0, 0.0, 763.0, -1110.0, ROADZ, "bk_road", group="detail")
box(763.0, -1202.0, 0.0, 771.0, -1110.0, WALKZ, "bk_walk", group="detail")
# Curbed north sidewalk of Wall St East bordering Amberton Park South Lawn, plus east perimeter curb along XD2:
box(771.0, -1202.0, 0.0, 1184.0, -1194.0, WALKZ, "bk_walk", group="detail")
for _eya, _eyb in ((-1508.0, -1412.0), (-1364.0, -1230.0)):
    box(1182.0, _eya, 0.0, 1188.0, _eyb, WALKZ, "bk_walk", group="detail")

for _ry0, _ry1, _ryc in ((-400.0, -352.0, -376.0), (-748.0, -700.0, -724.0), (-1084.0, -1036.0, -1060.0)):
    box(650.0, _ry0, 0.0, 677.0, _ry1, ROADZ, "bk_road", group="detail")
    box(650.0, _ryc - 0.5, 0.0, 676.0, _ryc - 0.15, 0.08, "bk_yline", group="illus")
    box(650.0, _ryc + 0.15, 0.0, 676.0, _ryc + 0.5, 0.08, "bk_yline", group="illus")

# --- C. North Seam: Connect Box A (Larry's South Connector, Central Fire Station, H St & Sonora St) to 21st St! ---
# 1) Paved N-S street (x = -332..-294) from E 21st St (y = -21, opposite Larry's Warehouse!) straight south to Fox's 21st St (y = -352):
box(-332.0, -352.0, 0.0, -294.0, -21.0, ROADZ, "bk_road", group="detail")
lines_y(-348.0, -25.0, -313.35, "bk_yline", w=0.35)
lines_y(-348.0, -25.0, -312.65, "bk_yline", w=0.35)
box(-340.0, -265.0, 0.0, -332.0, -27.0, WALKZ, "bk_walk", group="detail")
box(-294.0, -340.0, 0.0, -286.0, -27.0, WALKZ, "bk_walk", group="detail")

# 2) Extend Sonora St (x = 460..496) & H St north approach (x = -36..+16) smoothly across y = -352..-340 into Fox's 21st St:
box(460.0, -352.0, 0.0, 496.0, -338.0, ROADZ, "bk_road", group="detail")
box(-36.0, -352.0, 0.0, 16.0, -205.0, ROADZ, "bk_road", group="detail")
lines_y(-348.0, -208.0, -10.35, "bk_yline", w=0.35)
lines_y(-348.0, -208.0, -9.65, "bk_yline", w=0.35)
box(-44.0, -340.0, 0.0, -36.0, -205.0, WALKZ, "bk_walk", group="detail")
box(16.0, -340.0, 0.0, 24.0, -205.0, WALKZ, "bk_walk", group="detail")

# 3) Curbed sidewalk apron framing Bakersfield Central Fire Station (-170..-44, -340..-272) at NW 21st & H:
box(-180.0, -340.0, 0.0, -170.0, -264.0, WALKZ, "bk_walk", group="detail")
box(-170.0, -272.0, 0.0, -44.0, -264.0, WALKZ, "bk_walk", group="detail")

# North sidewalk of Fox's 21st St (y = -352..-340), broken at Larry's Connector, H St, Eye St, and Sonora St:
for _nxa, _nxb in ((-404.0, -332.0), (-294.0, -36.0), (16.0, 308.0), (356.0, 460.0), (496.0, 650.0)):
    box(_nxa, -352.0, 0.0, _nxb, -340.0, WALKZ, "bk_walk", group="detail")
box(308.0, -352.0, 0.0, 356.0, -340.0, ROADZ, "bk_road", group="detail")

# ==============================================================================
# 4. INTEGRATED BAKERSFIELDQUAKE GAMEPLAY (TELEPORTS, LAUNCH PADS, VANS, CRUISERS, TVS)
# ==============================================================================
def tp_portal_signed(hx, hy, hz, dest, sign_tex, light_north=False):
    """Classic DM6 *teleport portal (as tp_portal) with an overhead destination sign board above its lintel."""
    fy = hy + 3.0
    box(hx - 2.0, fy - 1 / 6, hz, hx + 2.0, fy + 1 / 6, hz + 8.0, "*teleport", group="illus")
    brush_ent("trigger_teleport", hx - 2.0, fy - 0.7, hz, hx + 2.0, fy + 0.7, hz + 8.0, target="tp_" + dest)
    for sx_ in (-1, 1):
        prop(
            hx + sx_ * 2.0 - (0.0 if sx_ > 0 else 0.7),
            fy - 0.6,
            hz,
            hx + sx_ * 2.0 + (0.7 if sx_ > 0 else 0.0),
            fy + 0.6,
            hz + 8.6,
            "bk_steel",
        )
    prop(hx - 2.7, fy - 0.6, hz + 8.0, hx + 2.7, fy + 0.6, hz + 8.6, "bk_steel")
    prop(
        hx - 3.2,
        fy - 0.25,
        hz + 8.6,
        hx + 3.2,
        fy + 0.25,
        hz + 10.6,
        "bk_steel",
        {"n": Fit(sign_tex), "s": Fit(sign_tex)},
    )
    ly = fy + 2.5 if light_north else fy - 2.5
    ent("light", hx, ly, hz + 4.0, light=115, _color="170 140 255")


# --- A. Teleport Hub "F" (Fox Theater 20th & H Postcard Corner <-> All 4 Existing Hubs) ---
_fox_arr_x, _fox_arr_y = F(52.0, -52.0)   # (0.0, -736.0), facing NW (132 deg) right at the Fox Marquee & Clock Tower!
HUB_ARRIVE["F"] = (_fox_arr_x, _fox_arr_y, 0.0, 132)
ent("info_teleport_destination", _fox_arr_x, _fox_arr_y, 0.3, targetname="tp_F", angle=132)

# Three return portals on the wide SE 20th & H sidewalk (against PG&E's flat brick wall, y_fox = -80):
for _dest_k, _stex, _fx_hx in (
    ("L", HUBS["L"]["tex"], 112.0),
    ("C", "bk5_tpsign4", 126.0),
    ("S", HUBS["S"]["tex"], 140.0),
):
    _phx, _phy = F(_fx_hx, -81.2)         # fy = _phy + 3.0 = F_y(-78.2), 1.8 ft north of PG&E wall, 14.2 ft clear sidewalk!
    tp_portal_signed(_phx, _phy, 0.5, _dest_k, _stex, light_north=True)
    PADS.append((_phx, _phy + 3.0))

# Add "FOX THEATER" (tp_F, bk6_tpsign5) portal to:
# 1) Larry's Warehouse (behind the open roll-up at y = 78..90)
_wfx, _wfy = _lp_spot(-152.0, 79.0, half=4.0, board=False, gap=10.0)
tp_portal_signed(_wfx, _wfy, 0.0, "F", "bk6_tpsign5")
PADS.append((_wfx, _wfy))
# 2) Tall Office Roof (next to the Bakersfield Sign)
if _ox1 - 6 > _ocx + 12 and _oy0 + 8 < _ocy - 26:
    tp_portal_signed(_ocx + 12.0, _ocy - 26.0, _ROOF, "F", "bk6_tpsign5")
# 3) Golden West Casino North Lot
_cfx, _cfy = _lp_spot(-664.0, -556.0, half=4.5, board=False, gap=10.0)
tp_portal_signed(_cfx, _cfy, 0.0, "F", "bk6_tpsign5")
PADS.append((_cfx, _cfy))
# 4) Manning St Hub
_mfx, _mfy = _lp_spot(MAN_X + 16.0, -440.0, half=4.5, board=False, gap=9.0)
tp_portal_signed(_mfx, _mfy, 0.0, "F", "bk6_tpsign5")
PADS.append((_mfx, _mfy))
V6_SPOTS.append(("Fox Theater: 20th & H Postcard Corner", _fox_arr_x, _fox_arr_y, 5.0, 132))
V6_SPOTS.append(("Fox Theater: Teleport Hub (PG&E Sidewalk)", *F(126.0, -66.0), 3.0, 270))

# --- B. Violet Cross-Map Launch Pads ("TO FOX THEATER" & Return Arcs) ---
_pads6 = [
    launch_pad(-265.0, -34.0, (-8.0, -720.0), "bk6_lsign6", 195.0),         # E 21st opposite Larry's Warehouse -> Fox Theater Marquee!
    launch_pad(*F(172.0, -72.0), (-115.0, 48.0), "bk4_lsign4", 210.0),      # Fox 20th & H PG&E sidewalk -> Larry's B-LAN Courtyard!
    launch_pad(782.0, -385.0, (285.0, -724.0), "bk6_lsign6", 175.0),        # Buck Owens / Crystal Palace -> Fox 20th & Eye!
    launch_pad(*F(442.0, -72.0), (805.0, -75.0), "bk4_lsign1", 195.0),      # Fox 20th & Eye sidewalk -> Bakersfield Sign!
]
for _px, _py, (_tx, _ty), _over in [(a, b, t[:2], o) for a, b, t, o in _pads6]:
    _lx, _ly = _lp_spot(_tx, _ty, half=4.5, gap=20.0)
    PADS.append((_lx, _ly))
    _v = launch((_px, _py, 0.0), (_lx, _ly, 0.5), _over)
    assert max(abs(c) for c in _v) < 3900, ("launch speed > 3900:", _v)
    brush_ent(
        "trigger_push",
        _px - LP_H + 0.5,
        _py - LP_H + 0.5,
        0.4,
        _px + LP_H - 0.5,
        _py + LP_H - 0.5,
        5.0,
        **push_kv(_v),
    )
    V6_SPOTS.append(("Launch pad (%d, %d) -> (%d, %d)" % (_px, _py, _lx, _ly), _px - 18, _py, 2.5, 0))
    print("v6: launch pad (%.0f, %.0f) -> (%.0f, %.0f), v = %s" % (_px, _py, _lx, _ly, tuple(int(c) for c in _v)))

# --- C. Downtown Skyline Rooftop Jump Pads (Padre Hotel 102.5ft, AT&T 54ft, 2000 H Overlook 19.5ft) ---
# 1) 8-Story Padre Hotel Skyline Roof (z = 102.5 ft): pad on H St east sidewalk -> soaring over 106.3ft parapet onto 8th-floor roof!
_pad_padre_x, _pad_padre_y = F(74.0, -598.0)
_tgt_padre_x, _tgt_padre_y = F(-18.0, -598.0)
box(_pad_padre_x - 4, _pad_padre_y - 4, 0.5, _pad_padre_x + 4, _pad_padre_y + 4, 0.9, "bk_steel", {"t": Fit("bk3_jump")}, group="detail")
_vp = launch((_pad_padre_x, _pad_padre_y, 0.9), (_tgt_padre_x, _tgt_padre_y, 103.5), over=18.0)
brush_ent("trigger_push", _pad_padre_x - 3.5, _pad_padre_y - 3.5, 0.9, _pad_padre_x + 3.5, _pad_padre_y + 3.5, 5.5, **push_kv(_vp))
light(_pad_padre_x, _pad_padre_y, 3.5, 95, "255 210 60")
PADS.append((_pad_padre_x, _pad_padre_y))
# padre_hotel.py already places rooftop spawn (-22,-644,104.8), armor2 (-22,-636,104) & rockets (-28,-636,104); add LG + cells!
ent("weapon_lightning", *F(-20.0, -610.0), 104.0)
ent("item_cells", *F(-28.0, -610.0), 104.0)

# 2) 4-Story AT&T Central Office Roof (z = 54.0 ft): pad on Eye St east sidewalk -> AT&T roof!
_pad_att_x, _pad_att_y = F(416.0, 118.0)
_tgt_att_x, _tgt_att_y = F(440.0, 118.0)
box(_pad_att_x - 4, _pad_att_y - 4, 0.5, _pad_att_x + 4, _pad_att_y + 4, 0.9, "bk_steel", {"t": Fit("bk3_jump")}, group="detail")
_va = launch((_pad_att_x, _pad_att_y, 0.9), (_tgt_att_x, _tgt_att_y, 55.0), over=18.0)
brush_ent("trigger_push", _pad_att_x - 3.5, _pad_att_y - 3.5, 0.9, _pad_att_x + 3.5, _pad_att_y + 3.5, 5.5, **push_kv(_va))
light(_pad_att_x, _pad_att_y, 3.5, 95, "255 210 60")
PADS.append((_pad_att_x, _pad_att_y))
ent("weapon_rocketlauncher", *F(442.0, 134.0), 55.8)
ent("item_armor2", *F(442.0, 102.0), 55.8)
ent("item_rockets", *F(442.0, 150.0), 55.8)

# 3) 2000 H St Rooftop Overlook (z = 19.5 ft, right across from the Fox Marquee & cursive Fox neon sign!):
_pad_2k_x, _pad_2k_y = F(74.0, 74.0)
_tgt_2k_x, _tgt_2k_y = F(100.0, 74.0)
box(_pad_2k_x - 3.5, _pad_2k_y - 3.5, 0.5, _pad_2k_x + 3.5, _pad_2k_y + 3.5, 0.9, "bk_steel", {"t": Fit("bk3_jump")}, group="detail")
_v2 = launch((_pad_2k_x, _pad_2k_y, 0.9), (_tgt_2k_x, _tgt_2k_y, 20.6), over=14.0)
brush_ent("trigger_push", _pad_2k_x - 3.0, _pad_2k_y - 3.0, 0.9, _pad_2k_x + 3.0, _pad_2k_y + 3.0, 5.5, **push_kv(_v2))
light(_pad_2k_x, _pad_2k_y, 3.5, 90, "255 210 60")
PADS.append((_pad_2k_x, _pad_2k_y))
ent("weapon_grenadelauncher", *F(104.0, 54.0), 21.2)
ent("item_armor1", *F(104.0, 36.0), 21.2)
ent("item_rockets", *F(120.0, 54.0), 21.2)

# --- D. Extended Cruiser Drive Loop (Pink Supercar & Podracer Now Cruise Right Past the Fox Marquee!) ---
_n_rt = _drop_ents(lambda c, x, y, z: c in ("bk_route", "bk_cruiser"))
_UNB6 = [(-575, 2), (-538, -121), (-531, -146), (-521, -193), (-507, -260), (-507, -345)]
ROUTE6 = (
    [(x + 8, y, 1.0) for x, y in _UNB6]
    + [
        (-499, -960, 0.8),
        (-515, -960, 0.5),
        (-515, -732, 0.8),       # Turn east from Golden West Casino onto 20th Street!
        (-2, -732, 0.9),         # Cruise right past the Fox Theater Marquee & Clock Tower (20th & H)!
        (-2, -376, 1.0),         # North up H Street past Spanish Storefronts & Today Cleaners to 21st St!
        (332, -376, 1.0),        # East along 21st St to Eye St!
        (332, -732, 1.0),        # South down Eye St past AT&T & Jones Building to 20th St!
        (724, -732, 1.0),        # East along 20th St straight onto Buck Owens Blvd!
        (724, -8.5, 1.0),        # North up Buck Owens Blvd to Sillect Ave!
        (1552, -8.5, 1.0),       # East under the Bakersfield Sign to Manning St!
        (1552, -685, 1.0),       # South down Manning St past 1608!
        (1250, -685, 1.0),
        (1250, -930, 0.6),
        (1160, -990, 0.4),       # Amberton Park loop!
        (1185, -900, 0.4),
        (1090, -850, 0.4),
        (880, -818, 0.4),
        (830, -784, 0.6),
        (712, -700, 1.0),        # North up Buck Owens Blvd all the way to Sumner St!
        (712, 392, 1.0),
        (0, 392, 1.0),           # West on Sumner to Sacramento St!
        (0, 1, 1.0),             # South on Sacramento St to E 21st St!
        (-567, 1, 1.0),          # West past Larry's Warehouse back to S Union Ave!
    ]
)
for _i, (_rx, _ry, _rs) in enumerate(ROUTE6):
    ent(
        "bk_route",
        _rx,
        _ry,
        ROADZ + 0.05,
        targetname="rt%d" % _i,
        target="rt%d" % ((_i + 1) % len(ROUTE6)),
        speed="%.2f" % _rs,
    )
ent("bk_cruiser", ROUTE6[9][0], ROUTE6[9][1], ROADZ + 0.05, cnt=1, target="rt10")   # Hot pink supercar right at Fox 20th & H!
ent("bk_cruiser", ROUTE6[25][0], ROUTE6[25][1], ROADZ + 0.05, cnt=2, target="rt26") # Podracer on Sumner/Sacramento!
print("v6: extended cruiser loop of %d points (%d old route ents replaced)" % (len(ROUTE6), _n_rt))

# --- E. Drivable ProMaster Vans in Fox Downtown ---
_fvans = 0
for _fvx, _fvy, _fyaw in (
    (*F(-115.0, -48.0), 0),      # 20th St west of HOPE Street Clock, aimed straight at Fox Marquee!
    (*F(285.0, 145.0), 180),     # 21st & Eye open lot
    (*F(155.0, -532.0), 0),      # Wall St right outside the playable 5-story 18th & Eye Parking Garage ramp!
    (*F(835.0, -692.0), 180),    # 18th St outside The 18hundred, aimed west toward Padre Hotel & Clover Ballroom!
    (-313.0, -180.0, 270),       # New Larry's South Connector street heading into Fox Downtown!
):
    _hx, _hy = (11.0, 5.0) if _fyaw in (0, 180) else (5.0, 11.0)
    if free(_fvx, _fvy, _hx, 1.0, 8.0, half_y=_hy):
        ent("misc_vehicle_van", _fvx, _fvy, 0.2, angle=_fyaw)
        _fvans += 1
    else:
        print("v6: van spot busy at", _fvx, _fvy)
print("v6: %d drivable vans added in Fox Downtown" % _fvans)

# --- F. B-LAN TVs Inside the Fox Theater (Eva's Lounge & Backstage Green Room) ---
# 1) Eva's East Lobby Lounge (north wall y_fox = 75.0 -> TV mounted at y_fox = 73.4 facing south over the lounge stage!)
tv(*F(-7.2, 73.4), 7.6, "s", 1.1, "Fox Theater: Eva's Lounge")
# 2) Backstage Green Room (north wall y_fox = 175.2 -> TV mounted at y_fox = 174.4 facing south toward Chesterfield sofa!)
tv(*F(-8.0, 174.4), 8.6, "s", 0.9, "Fox Theater: Green Room")

# Place Downtown's 38-ft Golden Empire Transit ('GET bus') coach & green bicycle rack on 18th St near Padre Hotel
# (in standalone fox.map those 2 models sat on Chester Ave north of 20th St, where Buck Owens Blvd takes over here):
ent("misc_model", 235.0, -1400.0, 0.06, mdl="progs/fox/get_bus.md3", angles="0 0 0")
box(216.0, -1404.2, 0.6, 254.0, -1395.8, 10.2, "clip")
ent("misc_model", -92.0, -1362.0, 0.60, mdl="progs/fox/bvm_bikerack.md3", angles="0 0 0")
box(-95.2, -1362.5, 0.85, -88.8, -1361.5, 3.3, "clip")

# Add key Fox Theater, Padre Hotel (all 15 updated iGUIDE/MD3 spots!) & Downtown viewpoints to SPOTS:
def _fspot(name, qx, qy, qz, yaw, pitch=0):
    return (name, round(qx / 12.0 + 168.0, 2), round(qy / 12.0 - 802.0, 2), round(qz / 12.0, 2), yaw, pitch)

V6_SPOTS += [
    ("Fox Theater: Under Marquee & Box Office", *F(4.0, 17.5), 4.8, 180),
    ("Fox Theater: Main Lobby & Concessions", *F(-76.0, 16.0), 5.0, 6, -8),
    ("Fox Theater: Mezzanine Promenade", *F(-18.8, 29.6), 26.0, 184),
    ("Fox Theater: Auditorium & Sunburst Proscenium", *F(-54.0, 62.0), 6.2, 90, -5),
    ("Fox Theater: Center Stage & Recessed Pit", *F(-54.0, 154.0), 8.2, 270),
    _fspot("Padre Hotel: SE Corner 18th & H", -1968, -7248, 66, 132, -22),
    _fspot("Padre Hotel: 18th St Front & Farmacy Sign", -3456, -7200, 66, 82, -16),
    _fspot("Padre Hotel: West Courtyard & Clover Wing", -4152, -6672, 62, 128, -8),
    _fspot("Padre Hotel: Grand Lobby, Drum Chandeliers & Cowgirl Mural", -3378, -6240, 62, 90, -2),
    _fspot("Padre Hotel: Brimstone Bar, Sofas & Pool Table", -3024, -6360, 62, 42, -2),
    _fspot("Padre Hotel: Sub-Grade 24-Hr Basement Gym", -3048, -6000, -74, 315, 4),
    _fspot("Padre Hotel: Clover 1 & 2 Ballroom & Banquet Sets", -5256, -6192, 62, 0, -2),
    _fspot("Padre Hotel: Floor 2 Upper Lobby & Horseshoe Wall", -3072, -6120, 258, 148, -2),
    _fspot("Padre Hotel: Floor 2 Conference Room Yellow Chairs", -3408, -6258, 258, 265, 6),
    _fspot("Padre Hotel: Floor 2 Prairie Fire Rooftop Bar -> Fox", -3744, -5856, 258, 72, -10),
    _fspot("Padre Hotel: Floor 4 Room 406 Two Queens & Barn Door", -3648, -6312, 570, 225, 4),
    _fspot("Padre Hotel: Floor 6 Room 608 Sheer-Curtain Shower", -3840, -6096, 858, 0, 2),
    _fspot("Padre Hotel: Floor 6 Oil Baron Suite Jacuzzi", -3384, -6312, 858, 220, 4),
    _fspot("Padre Hotel: Floor 6 Farmer's Daughter Suite -> Fox", -2820, -5952, 858, 88, -2),
    _fspot("Padre Hotel: Floor 8 Skyline Rooftop & Neon Sign", -3192, -6336, 1290, 38, -8),
    ("Nile Theater & Front Porch Music (19th St)", *F(-155.0, -372.0), 5.0, 255),
    ("Ovation Theatre & Zama (1622 19th St)", *F(195.0, -380.0), 5.0, 90),
    ("Central Academy Gear Mural & GET Bus (18th St)", 202.0, -1382.0, 3.8, 340, -4),
    ("The 18hundred & K St Garage (East 18th)", *F(835.0, -700.0), 5.0, 85),
    ("Bakersfield Central Fire Station (21st & H)", *F(-55.0, 310.0), 5.0, 90),
    ("18th & Eye 5-Story Parking Garage", *F(215.0, -576.0), 16.2, 90),
    ("20th St at S Union Ave (Casino <-> Fox)", -480.0, -724.0, 4.0, 0),
    ("20th St at Buck Owens Blvd (Fox <-> Park)", 690.0, -724.0, 4.0, 180),
]

# ==============================================================================
# 5. DANIEL MEME POSTERS, 3D PROPS & VIDEO TVS NEAR LARRY'S WAREHOUSE & LAN HALLS
# ==============================================================================
def daniel_wall_frame(x, y, z, facing, tex, w_ft=3.8, h_ft=3.8, spot_light=True):
    """Framed Daniel meme poster mounted flush on a wall at (x, y, z) facing `facing` ('n','s','e','w')."""
    dx, dy = _DIR[facing]
    hw, hh = w_ft * 0.5, h_ft * 0.5
    fh = 0.14
    if dx:
        x0, x1 = (x, x + dx * fh) if dx > 0 else (x + dx * fh, x)
        prop(x0 - (0.02 if dx < 0 else 0.0), y - hw - 0.16, z - hh - 0.16,
             x1 + (0.02 if dx > 0 else 0.0), y + hw + 0.16, z + hh + 0.16, "bk_dark")
        art_x0, art_x1 = (x + 0.03, x + dx * (fh + 0.03)) if dx > 0 else (x + dx * (fh + 0.03), x - 0.03)
        prop(art_x0, y - hw, z - hh, art_x1, y + hw, z + hh, "bk_dark", {facing: Fit(tex)})
    else:
        y0, y1 = (y, y + dy * fh) if dy > 0 else (y + dy * fh, y)
        prop(x - hw - 0.16, y0 - (0.02 if dy < 0 else 0.0), z - hh - 0.16,
             x + hw + 0.16, y1 + (0.02 if dy > 0 else 0.0), z + hh + 0.16, "bk_dark")
        art_y0, art_y1 = (y + 0.03, y + dy * (fh + 0.03)) if dy > 0 else (y + dy * (fh + 0.03), y - 0.03)
        prop(x - hw, art_y0, z - hh, x + hw, art_y1, z + hh, "bk_dark", {facing: Fit(tex)})
    if spot_light:
        light(x + dx * 2.4, y + dy * 2.4, z + 0.6, 68, "255 232 192")


def tv_daniel(x, y, z, facing, clip_id, scale=1.25, label=""):
    """B-LAN TV screen dedicated to cycling the 4 Daniel meme videos (cnt = 8..11)."""
    dx, dy = _DIR[facing]
    hw, hh = 2.0 * scale + 0.22, 1.5 * scale + 0.22
    bx, by = x - dx * 0.56, y - dy * 0.56
    fx, fy = x - dx * 0.06, y - dy * 0.06
    if dx:
        prop(min(bx, fx), y - hw, z - hh, max(bx, fx), y + hw, z + hh, "bk_dark")
    else:
        prop(x - hw, min(by, fy), z - hh, x + hw, max(by, fy), z + hh, "bk_dark")
    ent("bk_tv", x, y, z, angle=(0, 90, 180, 270)[("e", "n", "w", "s").index(facing)], scale=scale, cnt=clip_id)
    light(x + dx * 2.6, y + dy * 2.6, z, int(52 + 28 * scale), "120 220 255")
    if label:
        V6_SPOTS.append(("Daniel TV: " + label, x + dx * 9.5, y + dy * 9.5, 2.8, {"e": 180, "n": 270, "w": 0, "s": 90}[facing]))


# Upgrade the existing Larry's Warehouse & LAN Courtyard bk_tv entities so they play the Daniel video rotation too:
_drop_ents(lambda c, x, y, z: c == "bk_tv" and (abs(x - (-172.0)) < 1.5 or abs(y - 69.0) < 1.5))
ent("bk_tv", -172.0, WY1 - 0.56, 6.6, angle=270, scale=1.6, cnt=8)               # Clip 8: 4 AM Moving the Table
ent("bk_tv", B45[0] - 0.56, 69.0, 7.0, angle=180, scale=1.4, cnt=9)              # Clip 9: SHAAAAAAAAAAAA!

# 1) Larry's Warehouse Hall (118 / 120 E 21st St):
daniel_wall_frame(-182.0, WY1, 6.6, "s", "dan_4am", 4.2, 4.2)                    # North wall flanking big Warehouse TV
daniel_wall_frame(-162.0, WY1, 6.6, "s", "dan_ccc", 4.2, 4.2)
tv_daniel(-162.0, WY0 + 0.56, 6.5, "n", 9, 1.35, "Larry's Warehouse South")     # South wall Daniel TV + posters
daniel_wall_frame(-171.5, WY0, 6.5, "n", "dan_shaaa", 3.8, 3.8)
daniel_wall_frame(-152.5, WY0, 6.5, "n", "dan_webcam", 3.8, 3.8)
daniel_wall_frame(BED_X1, 31.5, 6.0, "e", "dan_4am", 3.4, 3.4)                  # Bedroom partition facing Warehouse SE bay
daniel_wall_frame(BED_X1, 37.5, 6.0, "e", "dan_ccc", 3.4, 3.4)
ent("prop_daniel_table", -176.5, 29.0, 0.25, angle=90)                           # 4 AM honey-oak table + QuickCam prop!
ent("prop_daniel_webcam", -176.5, 29.0, 2.75, angle=0)
ent("monster_daniel", -178.5, 53.5, 0.25, angle=0, spawnflags=1)                 # Harmless 360° LAN Station Daniel!

# 2) Larry's LAN Courtyard / Lot (between 118/120 Warehouse & Unit 130A):
tv_daniel(B76[2] + 0.56, 161.0, 7.2, "e", 10, 1.35, "LAN Courtyard (130A Entrance)")
daniel_wall_frame(B76[2], 117.0, 6.6, "e", "dan_shaaa", 4.0, 4.0)               # Solid piers between courtyard roll-ups
daniel_wall_frame(B76[2], 73.0, 6.6, "e", "dan_4am", 4.0, 4.0)

# 3) Unit 130A Main B-LAN Hall (inside the iconic CRT LAN room):
tv_daniel(-65.0, 154.56, 7.4, "n", 11, 1.20, "Unit 130A B-LAN Hall")
daniel_wall_frame(-72.0, 154.0, 7.4, "n", "dan_webcam", 3.5, 3.5)
daniel_wall_frame(-58.0, 154.0, 7.4, "n", "dan_ccc", 3.5, 3.5)
daniel_wall_frame(-65.0, 183.33, 7.8, "s", "dan_4am", 3.4, 3.4, spot_light=False)
daniel_wall_frame(-72.5, 183.33, 7.8, "s", "dan_shaaa", 3.4, 3.4, spot_light=False)
ent("prop_daniel_webcam", -73.4, 169.5, 4.6, angle=180)                          # Eyeball QuickCam on center LAN podium!

# 4) ORCOM Connect LAN Party Hall (Sonora St banquet LAN room):
tv_daniel(376.0, 346.44, 7.4, "s", 8, 1.25, "ORCOM LAN Party Hall")
daniel_wall_frame(369.0, 347.0, 7.4, "s", "dan_ccc", 3.5, 3.5)
daniel_wall_frame(383.0, 347.0, 7.4, "s", "dan_4am", 3.5, 3.5)
daniel_wall_frame(360.0, 325.0, 6.4, "e", "dan_shaaa", 3.5, 3.5)
daniel_wall_frame(360.0, 331.5, 6.4, "e", "dan_webcam", 3.5, 3.5)
ent("prop_daniel_webcam", 396.0, 339.5, 2.6, angle=270)
print("v6: Daniel meme wall posters, 3D props, LAN station & 6 Daniel video TVs placed across Warehouse & LAN halls")

# ==============================================================================
# 6. REPLACE PARKED CARS WITH NEW WILD VEHICLES (HD DUALLY, SCHOOL BUS, GT MUSCLE)
# ==============================================================================
# Exact target coordinates (x_ft, y_ft) -> new vehicle classname:
_WILD_SWAPS = [
    # Type-C Yellow School Buses ("BAKERSFIELD UNIFIED • BUS 42", 6 wheels):
    (-78.0, 11.0, "misc_vehicle_schoolbus"),        # E 21st St right outside Larry's LAN Courtyard Gate!
    (296.0, 11.0, "misc_vehicle_schoolbus"),        # E 21st St east toward Sonora / ORCOM!
    (-14.0, 290.0, "misc_vehicle_schoolbus"),       # Sacramento St north of Unit 130A!
    (-452.0, -880.0, "misc_vehicle_schoolbus"),     # Golden West Casino / S Union Ave charter bay!
    (-4.0, -1004.0, "misc_vehicle_schoolbus"),      # Fox Downtown H St near 19th St!
    (1567.0, -730.0, "misc_vehicle_schoolbus"),     # Manning St by Amberton Park!
    # 6.7TD Heavy-Duty Dually Trucks (6 wheels):
    (-135.0, 45.0, "misc_vehicle_hdtruck"),         # Inside Larry's LAN Courtyard!
    (-184.0, -17.0, "misc_vehicle_hdtruck"),        # E 21st St right in front of Larry's Warehouse!
    (70.0, -17.0, "misc_vehicle_hdtruck"),          # E 21st St east of Sacramento!
    (-48.0, 198.0, "misc_vehicle_hdtruck"),         # BODY SHOP gate behind 130A!
    (-408.0, 37.0, "misc_vehicle_hdtruck"),         # GCI Rental Yard!
    (-535.0, 150.0, "misc_vehicle_hdtruck"),        # West E 21st industrial lot!
    (-14.0, 50.0, "misc_vehicle_hdtruck"),          # Sacramento St beside Building 45!
    (-742.2, -882.8, "misc_vehicle_hdtruck"),       # Golden West Casino west lot!
    (-544.1, -846.3, "misc_vehicle_hdtruck"),       # Golden West Casino front row!
    (-16.0, -434.0, "misc_vehicle_hdtruck"),        # Fox Downtown H St north of 20th!
    (213.0, -1216.0, "misc_vehicle_hdtruck"),       # Downtown Wall St!
    (1315.0, -347.2, "misc_vehicle_hdtruck"),       # Buck Owens Blvd / Crystal Palace!
    (1622.0, -608.0, "misc_vehicle_hdtruck"),       # 1608 Manning St driveway!
    (-196.0, -74.0, "misc_vehicle_hdtruck"),        # South of E 21st opposite Larry's!
    # 5.0L V8 Supercharged Muscle Cars (4 wide twin-spoke wheels):
    (-214.0, 11.0, "misc_vehicle_gtcar"),           # E 21st St right outside 120A Mega Man room!
    (-44.0, 11.0, "misc_vehicle_gtcar"),            # E 21st St outside Celebrity Bodyworks!
    (-135.0, 145.0, "misc_vehicle_gtcar"),          # Inside Larry's LAN Courtyard near 130A!
    (-114.0, -706.5, "misc_vehicle_gtcar"),         # Fox Theater 20th St angled parking right at Marquee!
    (-110.0, -1372.0, "misc_vehicle_gtcar"),        # 18th St right outside The Padre Hotel!
    (-230.0, -1076.0, "misc_vehicle_gtcar"),        # 19th St outside Nile Theater!
    (216.0, -860.0, "misc_vehicle_gtcar"),          # Eye St in Fox Downtown!
    (-448.0, -772.0, "misc_vehicle_gtcar"),         # S Union & 20th St connector!
    (-682.0, -811.5, "misc_vehicle_gtcar"),         # Golden West Casino lot!
    (-544.1, -673.6, "misc_vehicle_gtcar"),         # Golden West Casino north row!
    (-14.0, 200.0, "misc_vehicle_gtcar"),           # Sacramento St outside 130A!
    (60.0, 112.0, "misc_vehicle_gtcar"),            # Dealership lot!
    (240.0, 58.0, "misc_vehicle_gtcar"),            # East dealership lot!
    (360.0, 404.0, "misc_vehicle_gtcar"),           # Sumner St near ORCOM!
    (1239.0, -356.8, "misc_vehicle_gtcar"),         # Crystal Palace / Bakersfield Sign!
    (1669.0, -134.8, "misc_vehicle_gtcar"),         # Sillect Ave!
    (1604.5, -606.5, "misc_vehicle_gtcar"),         # 1608 Manning St!
    (168.0, -1262.0, "misc_vehicle_gtcar"),         # 18th & Eye Parking Garage entrance!
]
_wild_counts = {"misc_vehicle_schoolbus": 0, "misc_vehicle_hdtruck": 0, "misc_vehicle_gtcar": 0}
for _idx_e, _es in enumerate(ENTS):
    _mc = re.search(r'"classname" "(misc_vehicle_(?:sedan|coupe|truck))"', _es)
    _mo = re.search(r'"origin" "(-?\d+) (-?\d+) (-?\d+)"', _es)
    if not (_mc and _mo):
        continue
    _ex = int(_mo.group(1)) / U + OX
    _ey = int(_mo.group(2)) / U + OY
    for _tx, _ty, _new_cls in _WILD_SWAPS:
        if math.hypot(_ex - _tx, _ey - _ty) < 3.0:
            ENTS[_idx_e] = _es.replace('"' + _mc.group(1) + '"', '"' + _new_cls + '"', 1)
            _wild_counts[_new_cls] += 1
            break

# Plus add a signature Bakersfield Unified Bus 42 right outside Central Academy Gear Mural on 18th St!
if free(120.0, -1372.0, 14.5, 1.0, 9.5, half_y=4.4):
    ent("misc_vehicle_schoolbus", 120.0, -1372.0, 0.2, angle=180)
    _wild_counts["misc_vehicle_schoolbus"] += 1
print("v6: Wild Vehicles placed:", _wild_counts)

# ==============================================================================
# 7. HARMLESS, SHOOTABLE ROAMING NPCS (WHEELMAN, FLAMINGO FIEND, DAVID + LADIES)
# ==============================================================================
# 1) Green-Suit Wheelman (harmless, drives around & does wheel stunts, gibs when shot):
ent("npc_greensuit_wheelman", -2.0, -685.0, 0.3, angle=270, target="rt9")         # Cruising Fox Marquee & Downtown loop!
ent("npc_greensuit_wheelman", -155.0, -3.0, 0.3, angle=0)                         # Cruising E 21st outside Larry's Warehouse!
V6_SPOTS.append(("NPC: Green-Suit Wheelman (Fox 20th & H)", -2.0, -708.0, 3.5, 90))
V6_SPOTS.append(("NPC: Green-Suit Wheelman (Larry's E 21st)", -178.0, -3.0, 3.5, 0))

# 2) The Flamingo Fiend / robeguy (harmless, roams around with dual flamingos, 24-frame feather gib on death):
ent("npc_robeguy", 18.0, -765.0, 0.3, angle=135)                                  # Roaming 20th & H Fox Theater Plaza!
ent("npc_robeguy", -115.0, 162.0, 0.3, angle=270)                                 # Roaming Larry's LAN Courtyard outside 130A!
V6_SPOTS.append(("NPC: The Flamingo Fiend (Fox Plaza)", 4.0, -752.0, 3.5, 315))
V6_SPOTS.append(("NPC: The Flamingo Fiend (LAN Courtyard)", -128.0, 162.0, 3.5, 0))

# 3) David Ojeda fleeing the 3 Running Pregnant Women (harmless, flexes money & spins slots, shootable):
ent("npc_david_squad", -605.0, -585.0, 0.3, angle=0)                              # Golden West Casino North Porte-Cochere Plaza!
V6_SPOTS.append(("NPC: David Ojeda & Pregnant Squad (Casino)", -575.0, -585.0, 3.8, 180))

# 4) Flyable Winged Breezy-Hair John vehicles (misc_vehicle_johnbird — 500 HP / 5 rockets, Press H to fly!):
ENTS.append('{\n"classname" "misc_vehicle_johnbird"\n"origin" "1210 -11412 12"\n"angle" "312"\n}')
ENTS.append('{\n"classname" "misc_vehicle_johnbird"\n"origin" "360 -18490 1242"\n"angle" "90"\n}')
ENTS.append('{\n"classname" "misc_vehicle_johnbird"\n"origin" "-120 -1180 12"\n"angle" "90"\n}')
print("v6: placed harmless shootable Green-Suit Wheelman x2, Flamingo Fiend x2, David squad, and 3x Winged Breezy-Hair John vehicles")

# ==============================================================================
# 8. SOFT NON-BLOWN-OUT LIGHT CALIBRATION & SUBTLE ACCENT POOLS
# ==============================================================================
# Scale point lights across the map by 0.56x into DarkPlaces's 4x-overbright sweet spot (so cream Padre/Fox stucco,
# marble lobby floors, and LAN halls never clip to #FFFFFF white):
for _idx_e, _es in enumerate(ENTS):
    if '"classname" "light"' not in _es:
        continue
    _ml = re.search(r'"light" "(\d+(?:\.\d+)?)"', _es)
    if _ml:
        _old_v = float(_ml.group(1))
        _new_v = max(28, int(round(_old_v * 0.56)))
        ENTS[_idx_e] = _es.replace(_ml.group(0), '"light" "%d"' % _new_v, 1)

# Subtle warm marquee, hotel & LAN accent pools (calibrated for DarkPlaces 4x overbright, zero blowout):
for _lx, _ly, _lz, _lv, _lc in (
    # Fox Theater Marquee warm canopy glow & subtle neon blade tint:
    (*F(12.0, -24.0), 14.0, 95, "255 208 132"),
    (*F(-14.0, -24.0), 14.0, 88, "255 206 128"),
    (*F(34.0, -8.0), 22.0, 78, "255 95 140"),
    (*F(34.0, 26.0), 28.0, 72, "115 210 255"),
    # Padre Hotel 18th & H warm architectural uplights:
    (*F(18.0, -688.0), 14.0, 82, "255 204 132"),
    (*F(-30.0, -688.0), 14.0, 78, "255 204 132"),
    # Larry's Warehouse & LAN Courtyard gentle warm sodium pools:
    (-186.0, 16.0, 13.5, 82, "255 206 138"),
    (-115.0, 156.0, 11.5, 78, "255 212 148"),
    # Unit 130A LAN Hall subtle RGB CRT bounce:
    (-69.0, 170.0, 5.5, 62, "105 235 182"),
    (-80.0, 162.0, 5.5, 58, "255 112 215"),
    # Golden West Casino Porte-Cochere warm gold wash over David Ojeda's plaza:
    (-605.0, -585.0, 15.0, 98, "255 212 124"),
):
    light(_lx, _ly, _lz, _lv, _lc)

V3_SPOTS += V5_SPOTS + V6_SPOTS
