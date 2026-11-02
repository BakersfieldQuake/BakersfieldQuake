"""Box C of bklan: the changes from the owner's feedback video of 2026-10-31 09:36 (exec'd by make_bklan.py, only when
BKLAN_V3=1, so it builds as its own map "bklan3" while another agent keeps changing bklan itself; merge = set the env
var in the normal build). Everything here only ADDS brushes / entities, or drops specific old brushes by position
(drop()), so it does not depend on the other generator files changing.

What the video asked for (times are video seconds; positions are the dev-overlay readings, map feet):
  6-14    Larry's warehouse clearly identified, most detail there            -> signs on the unit, roof and a pylon
  22-33   the Sacramento St iron gate (BODY SHOP yard, x -33, y 184..206) must be open -> gate opened
  42-46   roll-up doors of the units on the LAN lot: should be able to go inside -> open_units()
  48-94   jump pads (or pothole pads) on every intersection corner, jetpacks, high enough -> corner_pads()
  95-134  tall office building + the Bakersfield Sign: jump pads up onto them, items on top -> roof_pads()
  137-157 empty streets / nothing: walls round everything                        -> perimeter wall + filler
  158-172 trees: download sprites, fewer of them; Manning St must be identified   -> sprite trees, Manning signs
  177-183 the white van needs far more detail                                    -> van3()
  185-217 teleports between Manning St, the Bakersfield Sign and Larry's         -> teleport hubs
  218-226 empty space needs elements (streets, buildings)                        -> filler blocks
"""
import re as _re

WAD3 = "bklan3.wad"            # relative: worldspawn "wad" values are limited to 127 characters (qbsp runs in out/maps)
with open(os.path.join(HERE, "out", "maps", WAD3), "rb") as _f:
    _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
    _f.seek(_ofs)
    _dirs = [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]
    for _pos, _, _, _, _, _, _name in _dirs:
        _f.seek(_pos)
        _nm, _w, _h = struct.unpack("<16s2I", _f.read(24))
        TEXSIZE[_name.split(b"\0")[0].decode()] = (_w, _h)

V3_SPOTS = []
G_UNITS = 800.0                      # sv_gravity
_NUM = _re.compile(r"\(\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*\)")


# ---------------------------------------------------------------------------------------------- helpers
def ft_bbox(s):
    """Bounds of a brush's text, in feet: (x0, y0, z0, x1, y1, z1)."""
    pts = [tuple(int(v) for v in m) for m in _NUM.findall(s)]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return (lo[0] / U + OX, lo[1] / U + OY, lo[2] / U, hi[0] / U + OX, hi[1] / U + OY, hi[2] / U)


def drop(group, pred):
    """Remove old brushes whose foot-bounds satisfy pred(bbox); returns how many (and clears them from SOLIDS)."""
    keep, n = [], 0
    for s in GROUPS[group]:
        if pred(ft_bbox(s)):
            n += 1
        else:
            keep.append(s)
    GROUPS[group][:] = keep
    SOLIDS[:] = [b for b in SOLIDS if not pred((b[0] / U + OX, b[1] / U + OY, b[2] / U, b[3] / U + OX, b[4] / U + OY, b[5] / U))]
    return n


def inside(b, x0, y0, x1, y1, z0=-99, z1=99):
    return b[0] >= x0 and b[3] <= x1 and b[1] >= y0 and b[4] <= y1 and b[2] >= z0 and b[5] <= z1


def brush_ent(cls, x1, y1, z1, x2, y2, z2, tex="bk_dirt", **kv):
    """A brush entity (trigger_push, trigger_teleport) over a box, feet."""
    GROUPS["_t"] = []
    n = len(SOLIDS)
    box(x1, y1, z1, x2, y2, z2, tex, group="_t")
    del SOLIDS[n:]
    ENTS.append('{\n"classname" "%s"\n' % cls + "".join('"%s" "%s"\n' % kv_ for kv_ in kv.items()) + GROUPS.pop("_t")[0] + "}\n")


def launch(p0, p1, over=12.0):
    """Velocity (units/s) that flies a player from foot point p0 to p1 (feet), peaking `over` ft above the higher one."""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    zt = max(z0, z1) + over
    vz = math.sqrt(2 * G_UNITS * (zt - z0) * U)
    t = vz / G_UNITS + math.sqrt(2 * (zt - z1) * U / G_UNITS)
    return ((x1 - x0) * U / t, (y1 - y0) * U / t, vz)


def push_kv(v):
    sp = math.sqrt(sum(c * c for c in v))
    pitch = -math.degrees(math.asin(v[2] / sp))                  # QuakeC makevectors: negative pitch is up
    yaw = math.degrees(math.atan2(v[1], v[0]))
    return {"angles": "%.1f %.1f 0" % (pitch, yaw), "speed": "%.1f" % (sp / 10)}


PADS = []                                                       # (x, y) of every jump pad, to keep them apart


def free(x, y, half=5.0, z0=1.0, z1=8.0, half_y=None):
    """True when nothing solid stands in the box round (x, y) (feet), z0..z1 (curbs and sidewalks are ignored)."""
    hy = half if half_y is None else half_y
    lo = (u(x - half, OX), u(y - hy, OY), u(z0))
    hi = (u(x + half, OX), u(y + hy, OY), u(z1))
    if any(all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)) for b in SOLIDS):
        return False
    return not any(lo[0] - 24 < px < hi[0] + 24 and lo[1] - 24 < py < hi[1] + 24 for _, (px, py, _pz) in PLACED)   # spawns, items


PAD_GAP = 30.0 if os.environ.get("BKLAN_V4") else 0.0     # bklan3: "there should never be this many jump pads close"


def jump_pad(x, y, z=0.0, target=None, apex=70.0, size=8.0, over=12.0):
    """A glowing pad with a trigger_push over it. target=None: straight up (apex ft); else a (x, y, z) to land on."""
    h = size / 2
    if any(math.hypot(x - px_, y - py_) < PAD_GAP for px_, py_ in PADS):
        return False
    if not free(x, y, h + 0.5, z + 1.0, z + 8.0):
        return False
    box(x - h, y - h, z, x + h, y + h, z + 0.4, "bk_steel", {"t": Fit("bk3_jump")}, group="detail")
    if target is None:
        v = (0.0, 0.0, math.sqrt(2 * G_UNITS * apex * U))
        kv = {"angles": "-90 0 0", "speed": "%.1f" % (v[2] / 10)}
    else:
        v = launch((x, y, z), target, over)
        kv = push_kv(v)
    brush_ent("trigger_push", x - h + 0.5, y - h + 0.5, z + 0.4, x + h - 0.5, y + h - 0.5, z + 5, **kv)
    light(x, y, z + 3, 90, "255 210 60")
    PADS.append((x, y))
    return True


def poly_centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


# ---------------------------------------------------------------------------------------------- perimeter wall
# The hull is L-shaped (box A + box B); a 36 ft sound wall just inside the clip border, so the map never ends in void.
PW_H, PW_T, PW_IN = 36, 2.0, 5.0
_edges = [((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, YB)), ((X1, YB), (XB, YB)), ((XB, YB), (XB, Y1)), ((XB, Y1), (X0, Y1)),
          ((X0, Y1), (X0, Y0))]
for (ax, ay), (bx_, by_) in _edges:
    x0, x1 = sorted((ax, bx_))
    y0, y1 = sorted((ay, by_))
    if ax == bx_:                                    # a vertical (north-south) edge: the wall goes inward
        sgn = 1 if ax == X0 else -1
        if ax == X1:
            sgn = 1                                  # the inner notch edge: wall on the box-B side
        xa = ax + sgn * PW_IN
        box(min(xa, xa + sgn * PW_T), y0, 0, max(xa, xa + sgn * PW_T), y1, PW_H, tspec("bk3_sw", 8), {"t": "bk3_sw"})
    else:
        sgn = 1 if ay == Y0 else -1
        if ay == YB:
            sgn = 1
        ya = ay + sgn * PW_IN
        box(x0, min(ya, ya + sgn * PW_T), 0, x1, max(ya, ya + sgn * PW_T), PW_H, tspec("bk3_sw", 8), {"t": "bk3_sw"})

# ---------------------------------------------------------------------------------------------- the BODY SHOP gate
# (video 0:22-0:32, flying over x -26, y 189: "you should be able to walk back here, this should be open")
_n = drop("fence", lambda b: inside(b, B45[2] - 0.5, 183.5, B45[2] + 0.3, 206.5, 0, 8))
gx = B45[2] - 0.3
box(gx, 184, 0, gx + 0.3, 189, 6.8, Fit("{iron", (5 / 5.3, 1)), group="fence")          # fixed panels either side
box(gx, 201, 0, gx + 0.3, 206, 6.8, Fit("{iron", (5 / 5.3, 1)), group="fence")
box(gx - 0.8, 189.5, 0, gx - 0.5, 200.5, 6.8, Fit("{iron", (11 / 5.3, 1)), group="fence")  # the leaf slid back inside, clear of the opening
for py in (189, 201):
    prop(gx - 0.1, py - 0.2, 0, gx + 0.4, py + 0.2, 7.3, "bk_steel")
print("v3: gate opened (%d old fence brushes dropped)" % _n)

# ---------------------------------------------------------------------------------------------- Larry's Warehouse signs
# (video 6-14: "make sure Larry's warehouse is clearly identified"; 34-40: "there should be a sign over here")
LY0, LY1 = 157.0, 181.0                                      # 24 ft long, over the 130A roll-up on the lot side
prop(B45[0] - 0.55, LY0, 12.3, B45[0], LY1, 16.3, "bk_fascia", {"w": Fit("bk3_larry"), "t": "bk_fascia"})
# a big two-sided board on the roof, readable from Sacramento St and from the lot
prop(-62.3, 124, PARA, -61.8, 154, PARA + 4.5, "bk_steel", {"w": Fit("bk3_larry"), "e": Fit("bk3_larry")})
for ry in (125, 139, 153):
    prop(-62.1, ry - 0.2, ROOF_TOP, -61.9, ry + 0.2, PARA + 0.1, "bk_steel")
# a pylon at the lot gate on E 21st St: poles, a double-sided board facing the street
for px in (-118.6, -112.4):
    prop(px - 0.3, 30.3, 0, px + 0.3, 30.9, 17, "bk_steel")
prop(-121, 30.3, 14.5, -110, 30.9, 24.5, "bk_steel", {"n": Fit("bk3_pylon"), "s": Fit("bk3_pylon")})
light(-115, 36, 12, 140, "255 240 200")

# ---------------------------------------------------------------------------------------------- teleport hubs
# Larry's lot <-> the Bakersfield Sign <-> Manning St (video 185-217: "two or three teleports")
HUBS = {
    "L": dict(name="Larry's Warehouse", at=(-112.0, 100.0), arrive=(-112.0, 118.0, 90), tex="bk3_tpsign1"),
    "S": dict(name="the Bakersfield Sign", at=(815.0, -3.0), arrive=(833.0, -3.0, 0), tex="bk3_tpsign2"),
    "M": dict(name="Manning St", at=(MAN_X - 3.0, -440.0), arrive=(MAN_X - 3.0, -422.0, 90), tex="bk3_tpsign3"),
}
_order = ["L", "S", "M"]


def tp_portal(hx, hy, hz, dest):
    """A classic Quake teleporter (owner 2026-11-01: "traditional Quake teleports like in DM6"): the upright field of id's
    "*teleport" texture, 4 ft wide, 8 ft tall and 4 units thin (DM6's are 48 x 96 x 4 units), standing in a plain frame. The
    field itself is scenery (an illusionary brush, so it has no collision); the invisible trigger_teleport around it is a
    little thicker, so nobody can step through without touching it. The field is centred on (hx, hy + 3) and faces +/- y;
    hz = the floor."""
    fy = hy + 3.0
    box(hx - 2, fy - 1 / 6, hz, hx + 2, fy + 1 / 6, hz + 8, "*teleport", group="illus")
    brush_ent("trigger_teleport", hx - 2, fy - 0.7, hz, hx + 2, fy + 0.7, hz + 8, target="tp_" + dest)
    for sx in (-1, 1):                                                       # two pillars and a lintel round the field
        prop(hx + sx * 2.0 - (0.0 if sx > 0 else 0.7), fy - 0.6, hz, hx + sx * 2.0 + (0.7 if sx > 0 else 0.0), fy + 0.6, hz + 8.6, "bk_steel")
    prop(hx - 2.7, fy - 0.6, hz + 8.0, hx + 2.7, fy + 0.6, hz + 8.6, "bk_steel")
    ent("light", hx, fy - 2.5, hz + 4, light=110, _color="170 140 255")       # a violet glow on the floor in front


def tp_pad(hx, hy, dest, label_tex, along):
    """One teleporter on the ground (the pads of the hubs): a classic Quake portal to destination `dest`."""
    tp_portal(hx, hy, 0, dest)


for key in ([] if os.environ.get("BKLAN_V4") else _order):      # bklan3 places its own (make_bklan_v4.py)
    h = HUBS[key]
    ax, ay, ayaw = h["arrive"]
    ent("info_teleport_destination", ax, ay, 0.3, targetname="tp_" + key, angle=ayaw)
    V3_SPOTS.append(("Teleport hub: " + h["name"], h["at"][0], h["at"][1] - 14, 2.2, 90))
    others = [k for k in _order if k != key]
    for n_, ok in enumerate(others):
        hx, hy = h["at"][0] + (n_ * 2 - 1) * 8, h["at"][1]
        tp_pad(hx, hy, ok, HUBS[ok]["tex"], "x")
print("v3: 3 teleport hubs, 6 pads")

# ---------------------------------------------------------------------------------------------- jump pads on every corner
# (video 48-94). Intersections of the streets that exist in the map; a pad on each sidewalk corner, a yellow armor
# (which brings a jetpack with it) on the first corner. Straight up, ~70 ft: enough to clear the buildings.
CROSSINGS = [("E 21st at Sacramento", -1, -5, 20, 20), ("E 21st at Sonora", 478, -10, 20, 20),
             ("E 21st at Union Ave", -575, 2, 20, 20), ("Sumner at Sacramento", 3, 397, 20, 20),
             ("Sumner at Sonora", 482, 390, 20, 20), ("Buck Owens at Sillect", 720, -3, 43, 31),
             ("Manning at Sillect", MAN_X, -3, 18, 31)]
for name, cx, cy, hwx, hwy in CROSSINGS:
    corners = [(cx + sx_ * (hwx + 8), cy + sy_ * (hwy + 8)) for sx_ in (-1, 1) for sy_ in (-1, 1)]
    for k, (px_, py_) in enumerate(corners):
        if any(abs(px_ - qx) < 9 and abs(py_ - qy) < 9 for qx, qy in PADS):
            continue
        if k == 0:
            if free(px_, py_, 3, 1, 5):
                ent("item_armor2", px_, py_, 1.8)
        else:
            jump_pad(px_, py_, 0.0, apex=70)
    V3_SPOTS.append(("Jump pads: " + name, cx - hwx - 20, cy, 2.2, 0))
print("v3: %d corner jump pads" % len(PADS))


# ---------------------------------------------------------------------------------------------- roofs: pads up, items on top
# (video 72-80 and 95-134: "you should be able to jump on top of all the buildings", "there should be something" up
# there). A pad beside every sizeable building throws the player onto its roof; each roof gets an item and some
# rooftop equipment. Roof heights are the ones the generator used (HEIGHT / SPECIAL / ROOF_TOP).
def _poly_has(poly, x, y):
    c = False
    for (ax, ay), (bx_, by_) in zip(poly, poly[1:] + poly[:1]):
        if (ay > y) != (by_ > y) and x < (bx_ - ax) * (y - ay) / (by_ - ay) + ax:
            c = not c
    return c


ROOFS = []
for _i, _b in enumerate(OSM["buildings"]):
    _pts = [tuple(p) for p in _b["pts"]]
    if _i in HEROES or not all(X0 + 6 < x < X1 - 6 and Y0 + 6 < y < Y1 - 6 for x, y in _pts):
        continue
    _kind = _b["tags"].get("bak:fac_type1", "")
    _h = SPECIAL[_i][0] if _i in SPECIAL else HEIGHT.get(_kind, 16)
    ROOFS.append((_pts, _h))
ROOFS.append(([(B45[0], B45[1]), (B45[2], B45[1]), (B45[2], B45[3]), (B45[0], B45[3])], ROOF_TOP))
ROOFS.append(([(B76[0], B76[1]), (B76[2], B76[1]), (B76[2], B76[3]), (B76[0], B76[3])], ROOF_TOP))
ROOF_ITEMS = ["item_health", "item_shells", "item_rockets", "item_spikes", "item_cells", "item_armor1", "item_health"]
_n_roof = 0
for _pts, _h in ROOFS:
    _xs, _ys = [p[0] for p in _pts], [p[1] for p in _pts]
    _w, _d = max(_xs) - min(_xs), max(_ys) - min(_ys)
    if min(_w, _d) < 22 or _w * _d < 1800 or _h < 11:
        continue
    _c = poly_centroid(_pts)
    _edges = sorted(zip(_pts, _pts[1:] + _pts[:1]), key=lambda e: -math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
    for (ax, ay), (bx_, by_) in _edges[:6]:
        L = math.hypot(bx_ - ax, by_ - ay)
        if L < 22:
            break
        mx, my = (ax + bx_) / 2, (ay + by_) / 2
        nx, ny = (by_ - ay) / L, -(bx_ - ax) / L
        if _poly_has(_pts, mx + nx * 2, my + ny * 2):
            nx, ny = -nx, -ny                                       # outward
        px_, py_ = mx + nx * 7.5, my + ny * 7.5
        if any(abs(px_ - qx) < 10 and abs(py_ - qy) < 10 for qx, qy in PADS):
            continue
        tx_, ty_ = mx - nx * 10, my - ny * 10
        if not _poly_has(_pts, tx_, ty_):
            continue
        if jump_pad(px_, py_, 0.0, target=(tx_, ty_, _h + 0.5)):
            ent(ROOF_ITEMS[_n_roof % len(ROOF_ITEMS)], tx_ + ny * 5, ty_ - nx * 5, _h + 1)
            for k, (ox_, oy_) in enumerate(((-6, 4), (7, -5))):          # rooftop equipment
                qx, qy = _c[0] + ox_ * (k + 1) * 2, _c[1] + oy_ * (k + 1) * 2
                if _poly_has(_pts, qx, qy) and _poly_has(_pts, qx + 4, qy + 3):
                    prop(qx, qy, _h, qx + 4, qy + 3, _h + 3.2, "bk_beige", {"t": "bk_steel"})
            _n_roof += 1
            break
print("v3: %d building roofs with a pad and an item" % _n_roof)

# the tall office north of the sign (video 101-110: "I love this tall building ... a jump pad for sure")
_off = [P(q) for q in site_way(SITE_P, "59589538")["pts"][:-1]]
_ox0, _ox1 = min(q[0] for q in _off), max(q[0] for q in _off)
_oy0, _oy1 = min(q[1] for q in _off), max(q[1] for q in _off)
_ocx, _ocy = (_ox0 + _ox1) / 2, (_oy0 + _oy1) / 2
for _sy in (-1, 1):
    _py = (_oy0 - 9) if _sy < 0 else (_oy1 + 9)
    if os.environ.get("BKLAN_V4"):          # bklan3: "high enough to land on top of this building": a higher arc, further in
        # aim just inside the roof edge: a steep throw clears the wall (9 ft away) before it gets there
        jump_pad(_ocx + _sy * 20, _py, 0.0, target=(_ocx + _sy * 20, (_oy0 + 7) if _sy < 0 else (_oy1 - 7), 55.5), size=9, over=20.0)
    elif jump_pad(_ocx + _sy * 20, _py, 0.0, target=(_ocx + _sy * 20, _ocy + _sy * (-12), 55.5), size=9):
        pass
ent("weapon_rocketlauncher", _ocx, _ocy, 56.5)
ent("item_armor2", _ocx + 12, _ocy + 6, 56.5)
ent("item_cells", _ocx - 12, _ocy - 6, 56.5)
V3_SPOTS.append(("Tall office (jump pad)", _ocx, _oy0 - 25, 2.2, 90))

# the Bakersfield Sign: pads up onto each tower's roof, a pad on each roof that hops to the other, items on top
# (video 114-133: "a jump pad right here that allows you to go on top, and then another ... up here, some items")
for _ty, _sy in ((-3 - BS.HALF, -1), (-3 + BS.HALF, 1)):
    jump_pad(SIGN_X - 12, _ty + _sy * 14, 0.0, target=(SIGN_X, _ty, 31.2), size=8)
    jump_pad(SIGN_X + 12, _ty + _sy * 14, 0.0, target=(SIGN_X, _ty, 31.2), size=8)
    _oty = -3 + (BS.HALF if _sy < 0 else -BS.HALF)
    box(SIGN_X - 3, _ty - 3, 30.5, SIGN_X + 3, _ty + 3, 30.9, "bk_steel", {"t": Fit("bk3_jump")}, group="detail")
    _v = launch((SIGN_X, _ty, 31.0), (SIGN_X, _oty, 31.2), over=26)
    brush_ent("trigger_push", SIGN_X - 2.5, _ty - 2.5, 30.9, SIGN_X + 2.5, _ty + 2.5, 36, **push_kv(_v))
    light(SIGN_X, _ty, 34, 100, "255 210 60")
    ent("item_armor2" if _sy < 0 else "item_health", SIGN_X + 5.5, _ty + (4 if _sy < 0 else -4), 31.4)
    ent("item_rockets" if _sy < 0 else "item_shells", SIGN_X - 5.5, _ty + (-4 if _sy < 0 else 4), 31.4)
V3_SPOTS.append(("Jump pad up the Bakersfield Sign", SIGN_X - 12, -3 - BS.HALF - 20, 2.2, 90))


# ---------------------------------------------------------------------------------------------- sprite trees
# (video 158-172: "download some sprites for trees", "way too many trees"). Kenney's CC0 Foliage Pack, drawn as two
# crossed see-through quads (non-solid) on a solid trunk. The old box trees are removed, one in two kept.
import random as _rnd

SPR_TREES = {"t1": ("{bk3_tree1", 86, 208), "t2": ("{bk3_tree2", 122, 208), "t3": ("{bk3_tree3", 109, 214),
             "t4": ("{bk3_tree4", 151, 211), "cyp": ("{bk3_cyp", 68, 235), "pine": ("{bk3_pine", 102, 287)}


def sprite_tree(x, y, height, kind="t3"):
    name, w, h = SPR_TREES[kind]
    wd = w * height / h
    f = Fit(name)
    box(x - wd / 2, y - 0.06, 0.5, x + wd / 2, y + 0.06, height, name, {"n": f, "s": f}, group="illus")
    box(x - 0.06, y - wd / 2, 0.5, x + 0.06, y + wd / 2, height, name, {"e": f, "w": f}, group="illus")
    prop(x - 0.4, y - 0.4, 0, x + 0.4, y + 0.4, min(7.0, height * 0.35), "bk_bark")


_trees = []
for _s in list(GROUPS["detail"]):
    _b = ft_bbox(_s)
    if "bk_bark" in _s and 1.05 < _b[3] - _b[0] < 1.35 and 1.05 < _b[4] - _b[1] < 1.35 and _b[5] >= 5:
        _trees.append([(_b[0] + _b[3]) / 2, (_b[1] + _b[4]) / 2, _b[5], 0.0, _s])
_gone = 0
for _t in _trees:
    _lv = [s for s in GROUPS["illus"] if "bk_leaf" in s]
    for s in _lv:
        b = ft_bbox(s)
        cx_, cy_ = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
        if abs(cx_ - _t[0]) < 0.6 and abs(cy_ - _t[1]) < 0.6 and b[2] >= _t[2] - 1.5:
            _t[3] = max(_t[3], (b[3] - b[0]) / 2)
            GROUPS["illus"].remove(s)
    GROUPS["detail"].remove(_t[4])
    SOLIDS[:] = [q for q in SOLIDS if not (abs((q[0] + q[3]) / 24 + OX - _t[0]) < 0.3 and abs((q[1] + q[4]) / 24 + OY - _t[1]) < 0.3 and q[5] <= (_t[2] + 0.1) * U and q[2] == 0)]
    _gone += 1
_kept = 0
for _k, (_x, _y, _h, _r, _) in enumerate(_trees):
    if _y < -460 and _k % 2:                                  # the park and Manning St: far too many (video 170)
        continue
    sprite_tree(_x, _y, _h + 1.5 * (_r or 6.0), ("t1", "t2", "t3", "t4", "t3", "t2")[_k % 6])
    _kept += 1
print("v3: %d box trees replaced by %d sprite trees" % (_gone, _kept))

# ---------------------------------------------------------------------------------------------- Manning St signs
# (video 165-170: "this is Manning, this needs to be identified as such")
def blade(x, y, facing):
    """A green street-name blade on a pole. facing: the direction the board looks (e/w/n/s)."""
    prop(x - 0.2, y - 0.2, 0, x + 0.2, y + 0.2, 10, "bk_steel")
    if facing in "ns":
        prop(x - 2.6, y - 0.15, 8.4, x + 2.6, y + 0.15, 9.8, "bk_steel", {facing: Fit("bk3_manning"), "s" if facing == "n" else "n": Fit("bk3_manning")})
    else:
        prop(x - 0.15, y - 2.6, 8.4, x + 0.15, y + 2.6, 9.8, "bk_steel", {facing: Fit("bk3_manning"), "w" if facing == "e" else "e": Fit("bk3_manning")})


for _bx, _by, _bf in ((MAN_X + 23.5, -47.5, "n"), (MAN_X - 23.5, -47.5, "n"), (MAN_X + 24, M((0, 29))[1] + 20, "w"),
                      (MAN_X - 24, M((0, 29))[1] - 20, "e"), (MAN_X + 24, -300, "w"), (MAN_X - 24, -300, "e")):
    if free(_bx, _by, 1.5, 1, 9):
        blade(_bx, _by, _bf)
# the entry board at the corner of Sillect, two posts, readable from Sillect and from Manning
for _px in (MAN_X + 31, MAN_X + 53):
    prop(_px - 0.3, -62.3, 0, _px + 0.3, -61.7, 11, "bk_steel")
prop(MAN_X + 30, -62.2, 6, MAN_X + 54, -61.8, 12, "bk_steel", {"n": Fit("bk3_manboard"), "s": Fit("bk3_manboard")})
light(MAN_X + 42, -55, 10, 120, "255 245 220")
# the house number on a post at the kerb in front of 1608
prop(MAN_X + 24.0, -604.3, 0, MAN_X + 24.4, -603.9, 5.2, "bk_steel")
prop(MAN_X + 23.7, -605.5, 3.2, MAN_X + 23.9, -602.7, 5.2, "bk_steel", {"w": Fit("bk3_1608"), "e": Fit("bk3_1608")})
V3_SPOTS.append(("Manning St entry board", MAN_X + 42, -90, 2.2, 90))

# ---------------------------------------------------------------------------------------------- the white van, in detail
# (video 177-183). The ProMaster the other generator parks on the north lawn curb gets wheels, arches, mirrors, handles,
# sliding-door seams, headlights, wipers, a plate and a roof vent on top of the body it already has.
VX, VY = M((93.5, 0))[0], M((0, 126))[1]


def vb(a0, a1, b0, b1, z0, z1, tex, faces=None):
    """van box: a along the van (+ = nose, north), b across (+ = east)"""
    prop(VX + b0, VY + a0, z0, VX + b1, VY + a1, z1, tex, faces)


for _a in (6.6, -5.6):
    for _sg in (-1, 1):
        bo, bi = (3.55, 3.0) if _sg > 0 else (-3.0, -3.55)
        for ha, hz in ((1.45, 0.6), (1.0, 1.0), (0.6, 1.45)):                # a round-ish tyre from three boxes
            vb(_a - ha, _a + ha, bi, bo, 1.45 - hz, 1.45 + hz, "bk_tire")
        vb(_a - 0.7, _a + 0.7, (3.5 if _sg > 0 else -3.68), (3.68 if _sg > 0 else -3.5), 1.0, 1.9, "bk_steel")   # hub
        vb(_a - 1.9, _a + 1.9, (3.45 if _sg > 0 else -3.62), (3.62 if _sg > 0 else -3.45), 2.9, 3.2, "bk_chairbk")  # arch flare
for _sg in (-1, 1):
    s0, s1 = (3.45, 4.35) if _sg > 0 else (-4.35, -3.45)
    vb(4.6, 5.0, s0, s1, 5.7, 5.85, "bk_chairbk")                                     # mirror arm
    vb(4.55, 5.35, (4.1 if _sg > 0 else -4.45), (4.45 if _sg > 0 else -4.1), 5.2, 6.7, "bk_chairbk")   # mirror housing
    vb(3.9, 4.3, (3.45 if _sg > 0 else -3.55), (3.55 if _sg > 0 else -3.45), 4.1, 4.5, "bk_chairbk")   # door handle
    vb(-1.5, -1.4, (3.45 if _sg > 0 else -3.52), (3.52 if _sg > 0 else -3.45), 2.0, 7.9, "bk_dark")     # sliding door seams
    vb(1.7, 1.8, (3.45 if _sg > 0 else -3.52), (3.52 if _sg > 0 else -3.45), 2.0, 7.9, "bk_dark")
    vb(-1.4, 1.7, (3.45 if _sg > 0 else -3.52), (3.52 if _sg > 0 else -3.45), 4.12, 4.2, "bk_dark")    # the crease
    vb(9.9, 10.28, (1.9 if _sg > 0 else -3.0), (3.0 if _sg > 0 else -1.9), 2.5, 3.1, "bk_white")        # headlights
vb(-10.3, -10.15, -1.2, 1.2, 1.2, 1.75, "bk_steel", {"s": Fit("bk3_plate")})                            # plate (rear)
vb(-3.4, -2.1, -0.65, 0.65, 8.5, 8.9, "bk_white", {"t": "bk_steel"})                                    # roof vent
for _b0 in (-2.2, 0.1):
    vb(7.0, 7.12, _b0, _b0 + 1.9, 5.0, 5.12, "bk_chairbk")                                              # wipers
print("v3: van detail added at %.0f, %.0f" % (VX, VY))


# ---------------------------------------------------------------------------------------------- filler: streets and blocks
# (video 94-101, 137-157, 218-226: "I don't want this empty space ... some buildings", "these need to look more like
# streets", "everything's walled off"). The big paved areas east of Buck Owens and between Sonora and Buck Owens got
# a street grid and street-lined commercial / light-industrial blocks. These are NOT real buildings: generic Bakersfield
# fabric (the city GIS footprints cover only the two real sites), so they carry no signs or names.
def st_ns(x, ya, yb, w=36):
    box(x - w / 2, ya, 0, x + w / 2, yb, ROADZ, "bk_road", group="detail")
    box(x - 0.4, ya, 0, x - 0.1, yb, 1.5 / U, "bk_yline", group="detail")
    box(x + 0.1, ya, 0, x + 0.4, yb, 1.5 / U, "bk_yline", group="detail")


def st_ew(y, xa, xb, w=36):
    box(xa, y - w / 2, 0, xb, y + w / 2, ROADZ, "bk_road", group="detail")
    box(xa, y - 0.4, 0, xb, y - 0.1, 1.5 / U, "bk_yline", group="detail")
    box(xa, y + 0.1, 0, xb, y + 0.4, 1.5 / U, "bk_yline", group="detail")


FILL_WALLS = (("bk_shopwall", 20), ("bk_unitwall", 20), ("bk_lmc", 20), ("bk_stucco", 10), ("bk_110tan", 16))
FILL_DECALS = (("bk_darkwin", 8, 3.0, 7.4), ("bk_blkdoor", 3.5, 0, 7.2), ("bk_rollupx", 12, 0, 12), ("bk_darkwin", 8, 3.0, 7.4))
FILLER_ROOFS = []
_n_fill = 0


def shop(x0, y0, x1, y1, h, face, k):
    global _n_fill
    wt, bay = FILL_WALLS[k % len(FILL_WALLS)]
    box(x0, y0, 0, x1, y1, h, tspec(wt, bay), {"t": "bk_roof"})
    for ax_, ay_, bx_, by_ in ((x0, y0, x1, y0 + 0.7), (x0, y1 - 0.7, x1, y1), (x0, y0, x0 + 0.7, y1), (x1 - 0.7, y0, x1, y1)):
        prop(ax_, ay_, h, bx_, by_, h + 1.8, "bk_extwall", {"t": "bk_roof"})                    # parapet
    along = (x1 - x0) if face in "sn" else (y1 - y0)
    pos, n = 6.0, 0
    while pos + 4 < along:
        tex, w, z0, z1 = FILL_DECALS[(n + k) % len(FILL_DECALS)]
        if pos + w > along - 3:
            break
        if face == "s":
            prop(x0 + pos, y0 - 0.12, z0, x0 + pos + w, y0, z1, tex, {"s": Fit(tex)})
        elif face == "n":
            prop(x0 + pos, y1, z0, x0 + pos + w, y1 + 0.12, z1, tex, {"n": Fit(tex)})
        elif face == "w":
            prop(x0 - 0.12, y0 + pos, z0, x0, y0 + pos + w, z1, tex, {"w": Fit(tex)})
        else:
            prop(x1, y0 + pos, z0, x1 + 0.12, y0 + pos + w, z1, tex, {"e": Fit(tex)})
        pos += w + 7
        n += 1
    if face in "sn":
        prop(x0 - 0.5, (y0 - 1.5 if face == "s" else y1 - 0.1), 10.5, x1 + 0.5, (y0 + 0.1 if face == "s" else y1 + 1.5), 12.0, "bk_fascia")   # canopy band
    for q in range(1 + (k % 2)):
        ax_, ay_ = x0 + (x1 - x0) * (0.3 + 0.35 * q), y0 + (y1 - y0) * 0.5
        prop(ax_, ay_, h, ax_ + 4, ay_ + 3, h + 3.2, "bk_beige", {"t": "bk_steel"})
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    FILLER_ROOFS.append((pts, h))
    _n_fill += 1


def strip(xa, xb, ya, yb, face, seed):
    """Buildings along a strip (feet); the facade is on the `face` side of the strip."""
    r = _rnd.Random(seed)
    horiz = face in "sn"
    a0, a1 = (xa, xb) if horiz else (ya, yb)
    pos = a0 + r.uniform(0, 14)
    while pos + 40 < a1:
        L = min(r.uniform(55, 105), a1 - pos)
        d = r.uniform(38, 54)
        h = r.choice((14, 16, 18, 20, 22))
        if horiz:
            y0_ = ya if face == "s" else yb - d
            rect = (pos, y0_, pos + L, y0_ + d)
        else:
            x0_ = xa if face == "w" else xb - d
            rect = (x0_, pos, x0_ + d, pos + L)
        cx_, cy_ = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
        if free(cx_, cy_, (rect[2] - rect[0]) / 2 + 2, 1, 14, half_y=(rect[3] - rect[1]) / 2 + 2):
            shop(*rect, h, face, r.randint(0, 9))
        pos += L + r.uniform(8, 18)


def lot_cars(xa, xb, ya, yb, seed):
    """Parked cars in two rows down the middle of a block."""
    r = _rnd.Random(seed)
    for yy in (ya + (yb - ya) * 0.4, ya + (yb - ya) * 0.6):
        x = xa + 8
        while x < xb - 8:
            if r.random() < 0.18 and free(x, yy, 9, 1, 5, half_y=4.2):
                car(x, yy, "x", ("bk_white", "bk_red", "bk_blue", "bk_chairbk")[r.randint(0, 3)], 15)
            x += 19


def block(x0, y0, x1, y1, seed):
    """A city block (interior x0..x1, y0..y1): 6 ft sidewalks round it, buildings on the long sides, cars between."""
    for a_, b_, c_, d_ in ((x0 - 6, y0 - 6, x1 + 6, y0), (x0 - 6, y1, x1 + 6, y1 + 6), (x0 - 6, y0, x0, y1), (x1, y0, x1 + 6, y1)):
        box(a_, b_, 0, c_, d_, WALKZ, "bk_walk", group="detail")
    box(x0, y0, 0, x1, y1, ROADZ * 0.5, "bk_asphalt", group="detail")
    dep = 54
    if (y1 - y0) >= 2 * dep + 30:
        strip(x0, x1, y0, y0 + dep, "s", seed)
        strip(x0, x1, y1 - dep, y1, "n", seed + 1)
        lot_cars(x0, x1, y0 + dep, y1 - dep, seed + 2)
    else:
        strip(x0, x1, y0, y1, "s", seed)
    for tx in range(int(x0 + 20), int(x1 - 10), 55):                    # street trees on the sidewalk
        for ty in (y0 - 3, y1 + 3):
            if free(tx, ty, 2, 1, 6):
                sprite_tree(tx, ty, 17 + (tx % 5), ("t1", "t2", "t3", "t4")[(tx // 55) % 4])


# east of Buck Owens, north of Sillect: streets at x 1150 and Manning's line, y 340 and 600
for _x in (1150, MAN_X):
    st_ns(_x, 36, Y1 - 6)
for _y in (340, 600):
    st_ew(_y, 772, XB - 6)
_n = 0
for _r_, (_ya, _yb) in enumerate(((52, 316), (364, 576), (624, 780))):
    for _c_, (_xa, _xb) in enumerate(((790, 1126), (1174, MAN_X - 24), (MAN_X + 24, XB - 14))):
        block(_xa, _ya, _xb, _yb, 100 + _r_ * 7 + _c_)
        _n += 1
# south of Sillect, east of the palace: street at x 1150 and y -250
st_ns(1150, -446, -40)
st_ew(-250, 1132, XB - 6)
for _r_, (_ya, _yb) in enumerate(((-226, -56), (-430, -274))):
    for _c_, (_xa, _xb) in enumerate(((1174, MAN_X - 24), (MAN_X + 24, XB - 14))):
        block(_xa, _ya, _xb, _yb, 200 + _r_ * 7 + _c_)
        _n += 1
# between Sonora and Buck Owens
block(514, 52, 664, 370, 300)
block(514, -330, 664, -52, 301)
print("v3: filler: %d blocks, %d new buildings" % (_n + 2, _n_fill))

# pads on the corners of the new intersections, and up onto the filler roofs
for _cx, _cy in ((1150, 340), (1150, 600), (MAN_X, 340), (MAN_X, 600), (1150, -250), (MAN_X, -250)):
    _ok = 0
    for _sx_ in (-1, 1):
        for _sy_ in (-1, 1):
            if _ok < 3 and jump_pad(_cx + _sx_ * 28, _cy + _sy_ * 28, 0.0, apex=70):
                _ok += 1
    V3_SPOTS.append(("Jump pads: new street at %d, %d" % (_cx, _cy), _cx - 40, _cy, 2.2, 0))
for _pts, _h in FILLER_ROOFS[::2]:
    _c = poly_centroid(_pts)
    _y0, _y1 = min(p[1] for p in _pts), max(p[1] for p in _pts)
    for _py_, _ty_ in ((_y0 - 7.5, _y0 + 10), (_y1 + 7.5, _y1 - 10)):
        if jump_pad(_c[0], _py_, 0.0, target=(_c[0], _ty_, _h + 0.5)):
            ent(ROOF_ITEMS[_n_roof % len(ROOF_ITEMS)], _c[0] + 6, _ty_ + (3 if _ty_ > _py_ else -3), _h + 1)
            _n_roof += 1
            break
print("v3: %d pads in all, %d roof items" % (len(PADS), _n_roof))
print("v3 pads:", [(round(x), round(y)) for x, y in PADS[:12]])


# ---------------------------------------------------------------------------------------------- the units: go inside
# (video 42-46, looking at the roll-up wall of 118/120 from the LAN lot: "I should be able to go inside of this").
# The old generator filled the units with solid blocks behind painted roll-ups. Here the roll-ups on the lot side are
# rolled up (open) and each leads into a room. The insides are NOT from the tape (only 130A and 120A were filmed):
# plain light-industrial units with racks, crates, benches, tyres and a car, lit by tube lights.
_r = _rnd.Random(77)


def unit_room(x0, x1, ya, yb, door_side, seed):
    """One unit between partition walls: floor, joists, light, racks/crates/bench by the walls (feet)."""
    r = _rnd.Random(seed)
    box(x0, ya, 0, x1, yb, ROADZ, "bk_floor", group="detail")
    joists(x0, x1, ya, yb)
    xm, ym = (x0 + x1) / 2, (ya + yb) / 2
    tube_light(xm, ym - 5, 8, 12, "x", 230)
    tube_light(xm, ym + 5, 8, 12, "x", 230)
    far = x0 if door_side == "e" else x1
    sgn = 1 if far == x0 else -1
    prop(far, ya + 1, 0, far + sgn * 2.0, yb - 1, 7, "bk_steel")                                   # racks on the back wall
    for z in (1.5, 3.5, 5.5):
        prop(far, ya + 1, z, far + sgn * 2.4, yb - 1, z + 0.2, "bk_wood")
        for cy in range(int(ya + 2), int(yb - 4), 5):
            if r.random() < 0.7:
                prop(far + sgn * 0.3, cy, z + 0.2, far + sgn * 2.1, cy + 3, z + 1.8, "bk_crate")
    pick = r.randint(0, 3)
    if pick == 0:                                                                                  # workbench + vise
        prop(xm - 3, yb - 3.5, 0, xm + 3, yb - 1, 3, "bk_wood")
        prop(xm - 3, yb - 3.5, 3, xm + 3, yb - 1, 3.15, "bk_steel")
        prop(xm - 0.5, yb - 3.2, 3.15, xm + 0.5, yb - 2.2, 3.9, "bk_chairbk")
    elif pick == 1:                                                                                # tyre stacks
        for tx_ in (xm - 2, xm + 2):
            for tz in range(4):
                prop(tx_ - 1.5, ya + 3, tz * 0.8, tx_ + 1.5, ya + 6, tz * 0.8 + 0.75, "bk_tire")
    elif pick == 2:                                                                                # a car on a lift
        car(xm, ym, "x", ("bk_white", "bk_red", "bk_blue", "bk_chairbk")[r.randint(0, 3)], 15)
    else:                                                                                          # crates in the middle
        for k in range(3):
            crate(xm - 2 + k * 3, ym + r.uniform(-4, 4), 0, 3)
    for k in range(r.randint(1, 2)):                                                               # a drum or two
        prop(near := (far + sgn * 4.0), ya + 2 + k * 2.2, 0, near + 1.8, ya + 3.8 + k * 2.2, 3, "bk_blue")


# --- 118 / 120 E 21st (B76): seven roll-ups on the lot side (east wall), rooms behind them
_n1 = drop("world", lambda b: inside(b, B76[2] - 0.9, B76[1] - 0.1, B76[2] + 0.1, B76[3] + 0.1, -1, WALL_H + 0.1))
_n2 = drop("world", lambda b: inside(b, B76[2] - 40.5, B76[1] + 0.4, B76[2] - 0.5, B76[3] - 0.4, -1, WALL_H + 0.1))
_holes = [(y, y + 12, 0, 12) for y in range(34, 180, 22)]
wall("y", B76[2], B76[1], B76[3], 0, WALL_H, "bk_wall", "bk_extwall", "e", holes=_holes,
     deco=[(y + 14, y + 17, 0, 7, "bk_blkdoor") for y in range(34, 160, 44)])
for y0_, y1_, _, _ in _holes:
    prop(B76[2] - 0.9, y0_ - 0.4, 12, B76[2] + 0.15, y1_ + 0.4, 13.6, "bk_rollup")                 # the door, rolled up on its drum
_cuts = [29 + 22 * k for k in range(8)]                                                           # partitions between the units
xi0, xi1 = B76[2] - 40, B76[2] - T
for yc in _cuts:
    box(xi0, yc - 0.33, 0, xi1, yc + 0.33, WALL_H, "bk_wall")
box(xi0 - 0.67, B76[1] + T, 0, xi0, B76[3] - T, WALL_H, "bk_wall")                               # back wall of the units
for k in range(7):
    unit_room(xi0, xi1, _cuts[k] + 0.33, _cuts[k + 1] - 0.33, "e", 500 + k)
# --- Celebrity Bodyworks / 130A building (B45): five roll-ups on the lot side (west wall), rooms behind them
_n3 = drop("world", lambda b: inside(b, B45[0] - 0.1, B45[1] - 0.1, B45[0] + 0.9, 153.5, -1, WALL_H + 0.1))
_n4 = drop("world", lambda b: inside(b, B45[0] + 0.4, B45[1] + 0.4, B45[2] - 0.4, 153.5, -1, WALL_H + 0.1))
_holes = [(y, y + 12, 0, 12) for y in (30, 52, 74, 96, 118)]
wall("y", B45[0], B45[1], 153.33, 0, WALL_H, "bk_wall", "bk_extwall", "w", holes=_holes,
     deco=[(y + 14, y + 17, 0, 7, "bk_blkdoor") for y in (30, 74, 118)])
for y0_, y1_, _, _ in _holes:
    prop(B45[0] - 0.15, y0_ - 0.4, 12, B45[0] + 0.9, y1_ + 0.4, 13.6, "bk_rollup")
_cuts = [25, 47, 69, 91, 113, 153.33]
xi0, xi1 = B45[0] + T, B45[0] + 44
for yc in _cuts[:-1]:
    box(xi0, yc - 0.33, 0, xi1, yc + 0.33, WALL_H, "bk_wall")
box(xi1, B45[1] + T, 0, xi1 + 0.67, 153.33, WALL_H, "bk_wall")
box(xi1 + 0.67, B45[1] + T, 0, B45[2] - T, 153.33, WALL_H, "bk_wall")                            # the east strip stays solid
for k in range(5):
    unit_room(xi0, xi1, _cuts[k] + 0.33, _cuts[k + 1] - 0.33, "w", 600 + k)
print("v3: units opened (%d + %d old wall/fill brushes dropped)" % (_n1 + _n3, _n2 + _n4))
V3_SPOTS.append(("Inside the lot-side units", -128, 40, 2.2, 0))
V3_SPOTS.append(("Inside Celebrity Bodyworks units", -100, 58, 2.2, 180))
