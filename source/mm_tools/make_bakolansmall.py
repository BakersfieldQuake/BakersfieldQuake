"""bakolansmall: Golden West Casino and the B-LAN warehouse block on one short stretch of S Union Ave (a deathmatch map for 4-5 players).

Nothing is redrawn: the two source generators are run as they are (make_goldenwest.py with GW_FAST=1, make_bklan.py with BKLAN_V3=1),
their .map output is read back (bks_mapio.py), the wanted pieces are cut out by a window, moved (planes and texture offsets) and merged
with new geometry made here: the ground, the sky box (very tall), the Union Ave segment with its red-brick median, E 21st St, the plaza
fill, the gameplay (spawns, items, teleports, jump pads). Final frame = true feet, x east, y north, origin of the casino parcel's map.
Layout (see docs/BAKOLANSMALL_NOTES.md):  casino (west of Union, south) | plaza | ORCOM hall (west, north)
                                       Union Ave        Bakersfield Sign + Crystal Palace (east, middle) | B-LAN warehouse block (east, north)
usage: python make_bakolansmall.py out/maps/bakolansmall.map          (BKS_REUSE=1: do not run the two generators again)"""
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.environ["GW_SEG"] = "bks 0 0"                                   # gwbase.py: the frame only (its OY is overridden below)
exec(compile(open(os.path.join(HERE, "gwbase.py"), encoding="utf-8").read(), "gwbase.py", "exec"), globals())   # box, prism, ent, palm, lines_y, ...
sys.path.insert(0, HERE)
import bks_mapio as mio

with open(os.path.join(HERE, "out", "maps", "gwcasino.wad"), "rb") as _f:                    # sizes of the casino textures (gwbase.py only reads two wads)
    _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
    _f.seek(_ofs)
    for _pos, _, _, _, _, _, _name in [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]:
        _f.seek(_pos)
        _nm, _w2, _h2 = struct.unpack("<16s2I", _f.read(24))
        TEXSIZE[_name.split(bytes([0]))[0].decode()] = (_w2, _h2)

# ============================================================================================ frame
OXF, OYF = 260, 520                    # map origin in final feet: keeps everything inside +-32768 units
OX, OY = OXF, OYF
SKY_Z = 2500                           # feet: a very tall sky box (the jetpack goes high); 2500 ft = 30000 units
WALL_H = 36                            # the sound wall round the map
YE = 980                               # E 21st St (centre line) in final feet
rng = random.Random(2001)
SPOTS = []
WALL_TEX = "bk3_sw"

# --- hull rectangles (final feet): x0 y0 x1 y1 and the ground under each
ZONES = [
    ("cas", (-140, -250, 150, 420), "gw_dirt"),            # Golden West parcel
    ("plz", (-60, 420, 150, 800), "gw_dirt"),              # the plaza west of Union, between the two places
    ("orc", (-60, 800, 150, 1130), "bk_asphalt"),          # ORCOM lot
    ("uni", (150, -250, 268, 1300), "bk_asphalt"),         # S Union Ave
    ("eas", (268, 150, 560, 800), "bk_asphalt"),           # Bakersfield Sign, Crystal Palace and the plaza east of Union
    ("bln", (268, 790, 655, 1300), "bk_asphalt"),          # the B-LAN block
]
SOLID_MIN_TOP = 8                      # units: a brush must reach this high to count as an obstacle for spawn / item checks

# ============================================================================================ run the two generators
BK = os.path.join(HERE, "out", "bks")
os.makedirs(BK, exist_ok=True)
GW_MAP, BL_MAP = os.path.join(BK, "gw.map"), os.path.join(BK, "bl.map")
if not os.environ.get("BKS_REUSE"):
    env = dict(os.environ, GW_SEG="gw -130 400", GW_FAST="1")
    env.pop("BKLAN_V3", None)
    subprocess.run([sys.executable, os.path.join(HERE, "make_goldenwest.py"), GW_MAP], env=env, cwd=HERE)   # exits 1 on its own item check; the map is written first
    env = dict(os.environ, BKLAN_V3="1")
    env.pop("GW_SEG", None)
    env.pop("GW_FAST", None)
    r = subprocess.run([sys.executable, os.path.join(HERE, "make_bklan.py"), BL_MAP], env=env, cwd=HERE)
    if r.returncode:
        sys.exit("make_bklan.py failed")
SRC = {"gw": mio.read_map(GW_MAP), "bl": mio.read_map(BL_MAP)}
SRC_ORIGIN = {"gw": (0, 135), "bl": (-110, 225)}                     # feet: the origin each generator wrote its map around

# source window (feet, source frame) -> shift (feet): the pieces cut out of the two maps
PIECES = [
    dict(name="casino", src="gw", win=(-135, -175, 156, 410), d=(0, 0)),
    dict(name="blan", src="bl", win=(-332, -190, 41, 262), d=(607, YE + 3)),             # E 21st St, 118/120 + Larry's, the LAN lot, 130A, J Appliances, #105
    dict(name="sign", src="bl", win=(745, -300, 1060, 175), d=(-465, 450)),                # Bakersfield Sign, Crystal Palace, the tall office
    dict(name="orcom", src="bl", win=(336, 282, 462, 352), d=(-308, 670)),                 # ORCOM CONNECT LAN PARTY hall
]
DROP = ("info_player", "weapon_", "item_", "info_teleport", "trigger_teleport")        # gameplay is placed again below
TAG = {"worldspawn": "world", "func_detail": "detail", "func_wall": "fence", "func_detail_illusionary": "illus"}
SOLIDS_IN = []                                                                           # obstacle boxes of everything cut out (units)


def src_to_final(piece, x, y):
    return x + piece["d"][0], y + piece["d"][1]


def cut_piece(p):
    so = SRC_ORIGIN[p["src"]]
    off = (int(round(12 * (so[0] + p["d"][0] - OXF))), int(round(12 * (so[1] + p["d"][1] - OYF))), 0)
    x0, y0, x1, y1 = p["win"]
    nb = ne = 0

    def inwin(b):
        return (b.lo[0] / 12 + so[0] >= x0 and b.hi[0] / 12 + so[0] <= x1 and b.lo[1] / 12 + so[1] >= y0 and b.hi[1] / 12 + so[1] <= y1)

    for e in SRC[p["src"]]:
        if e.cls in TAG:
            for b in e.brushes:
                if inwin(b) and "sky_bk" not in b.texs:
                    nb += 1
                    mb = b.moved(off)
                    GROUPS[TAG[e.cls]].append(mb.text())
                    if TAG[e.cls] != "illus" and "clip" not in b.texs or "clip" in b.texs:
                        if mb.hi[2] > SOLID_MIN_TOP and mb.hi[2] - mb.lo[2] > 2:
                            SOLIDS_IN.append(mb.lo + mb.hi)
            continue
        if e.cls.startswith(DROP):
            continue
        o = e.origin()
        if o is None and e.brushes:
            b = e.brushes[0]
            o = tuple((b.lo[i] + b.hi[i]) // 2 for i in range(3))
        if o is None or not (x0 <= o[0] / 12 + so[0] <= x1 and y0 <= o[1] / 12 + so[1] <= y1):
            continue
        ENTS.append(e.text(off))
        ne += 1
    print("piece %-7s %5d brushes %4d entities" % (p["name"], nb, ne))


for _p in PIECES:
    cut_piece(_p)
SOLIDS.extend(SOLIDS_IN)


# ============================================================================================ ground, sky, walls (new geometry, true feet)
def cells():
    xs = sorted({v for _, r, _ in ZONES for v in (r[0], r[2])})
    ys = sorted({v for _, r, _ in ZONES for v in (r[1], r[3])})
    out = []
    for xa, xb in zip(xs, xs[1:]):
        for ya, yb in zip(ys, ys[1:]):
            cx, cy = (xa + xb) / 2, (ya + yb) / 2
            z = next((t for _, r, t in ZONES if r[0] < cx < r[2] and r[1] < cy < r[3]), None)
            out.append((xa, ya, xb, yb, z))
    return xs, ys, out


XS, YS, CELLS = cells()
_inside = {(c[0], c[1]): c[4] for c in CELLS if c[4]}


def is_in(x, y):
    return any(r[0] <= x < r[2] and r[1] <= y < r[3] for _, r, _ in ZONES)


with unscaled():
    M = 8                                                                                  # margin ring of sky round the bounding box
    bx0, by0, bx1, by1 = XS[0], YS[0], XS[-1], YS[-1]
    box(bx0 - M, by0 - M, -23, bx1 + M, by0, SKY_Z + 4, "sky_bk")
    box(bx0 - M, by1, -23, bx1 + M, by1 + M, SKY_Z + 4, "sky_bk")
    box(bx0 - M, by0, -23, bx0, by1, SKY_Z + 4, "sky_bk")
    box(bx1, by0, -23, bx1 + M, by1, SKY_Z + 4, "sky_bk")
    box(bx0, by0, SKY_Z, bx1, by1, SKY_Z + 4, "sky_bk")                                    # the lid
    for xa, ya, xb, yb, z in CELLS:
        if z is None:
            box(xa, ya, -23, xb, yb, SKY_Z, "sky_bk")                                       # the solid outside of the L-shaped hull
            continue
        box(xa, ya, -23, xb, yb, -2, "bk_dirt")
        if z == "gw_dirt":
            box(xa, ya, -2, xb, yb, 0, "gw_dirt", {"t": tspec("gw_dirt", 24)})
        else:
            box(xa, ya, -2, xb, yb, 0, z)
        for dx, dy, side in ((-1, 0, "w"), (1, 0, "e"), (0, -1, "s"), (0, 1, "n")):             # sound wall + clip column along the hull edge
            nx, ny = (xa if dx < 0 else xb) + dx * 0.5, (ya if dy < 0 else yb) + dy * 0.5
            if dx:
                ny = (ya + yb) / 2
            else:
                nx = (xa + xb) / 2
            if is_in(nx, ny):
                continue
            t = 2.0
            if side == "w":
                wb = (xa, ya, xa + t, yb)
            elif side == "e":
                wb = (xb - t, ya, xb, yb)
            elif side == "s":
                wb = (xa, ya, xb, ya + t)
            else:
                wb = (xa, yb - t, xb, yb)
            box(wb[0], wb[1], 0, wb[2], wb[3], WALL_H, tspec(WALL_TEX, 8), {"t": WALL_TEX})
            box(wb[0] - (2 if side in "ew" else 0), wb[1] - (2 if side in "sn" else 0), WALL_H, wb[2] + (2 if side in "ew" else 0), wb[3] + (2 if side in "sn" else 0),
                SKY_Z, "clip")
    box(bx0, by0, SKY_Z - 6, bx1, by1, SKY_Z, "clip")                                       # nobody walks on the sky lid


# ============================================================================================ S Union Ave and E 21st St
UW = (150.6, 159.3)           # west sidewalk
UWC = (159.3, 198.1)          # west carriageway: 3 lanes of 12.9 ft
UMC = (198.1, 199.7)          # median curb
UMB = (199.7, 217.9)          # the red-brick median
UEC = (219.5, 258.3)          # east carriageway
UE = (258.3, 267.0)           # east sidewalk
UY0, UY1 = -245.0, 1295.0
MEDX = (UMB[0] + UMB[1]) / 2
E21 = [(-21, -13.4, "bk_road"), (-13.4, -13.1, "bk_wline"), (-13.1, -3.35, "bk_road"), (-3.35, -3.0, "bk_yline"),
       (-3.0, -2.6, "bk_road"), (-2.6, -2.25, "bk_yline"), (-2.25, 7.1, "bk_road"), (7.1, 7.4, "bk_wline"), (7.4, 15, "bk_road")]


def solid_free(x, y, half, z0=0.6, z1=7.0):
    lo = (u(x - half, OX), u(y - half, OY), u(z0))
    hi = (u(x + half, OX), u(y + half, OY), u(z1))
    return not any(all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)) for b in SOLIDS)


def hubs_clear(y):
    """True when y is outside the E 21st crossing (the cross street's mouth in the Union sidewalks and the median)."""
    return not (YE - 24 < y < YE + 24)


with unscaled():
    road = lambda x0, x1, y0, y1, **k: box(x0, y0, 0, x1, y1, ROADZ, "gw_road", {"t": tspec("gw_road", 15)}, group="detail")
    # carriageways run the whole stretch; E 21st opens into the east one
    road(*UWC, UY0, UY1)
    box(UEC[0], UY0, 0, UEC[1], UY1, ROADZ, "gw_road", {"t": tspec("gw_road", 15)}, group="detail")
    box(UMC[0], UY0, 0, UMC[1], UY1, WALKZ, "bk_walk", group="detail")
    box(UMB[1], UY0, 0, UEC[0], UY1, WALKZ, "bk_walk", group="detail")
    box(UMB[0], UY0, 0, UMB[1], UY1, WALKZ, "gw_brick", {"t": tspec("gw_brick", 4)}, group="detail")
    box(UW[0], UY0, 0, UW[1], UY1, WALKZ, "bk_walk", group="detail")
    # east sidewalk, broken where E 21st leaves (and where the Sign plaza opens: it is all paved there)
    for ya, yb in ((UY0, YE - 18), (YE + 18, UY1)):
        box(UE[0], ya, 0, UE[1], yb, WALKZ, "bk_walk", group="detail")
    for lx in (UWC[0] + 12.93, UWC[0] + 25.87, UEC[0] + 12.93, UEC[0] + 25.87):                  # lane lines
        lines_y(UY0, UY1, lx, "bk_wline", w=0.35, dash=(10, 30))
    for lx, tex in ((UWC[0] + 0.7, "bk_wline"), (UMC[0] - 0.7, "bk_yline"), (UEC[0] + 0.7, "bk_yline"), (UEC[1] - 0.7, "bk_wline")):
        lines_y(UY0, UY1, lx, tex, w=0.4)
    # E 21st St: from the east sidewalk of Union to the east end of the block, y = YE - 21 .. YE + 15 (the strips of make_bklan.py)
    for ya, yb, tex in E21:
        box(UEC[1], YE + ya, 0, 655, YE + yb, ROADZ, tex, {"n": "bk_walk", "s": "bk_walk"}, group="detail")
    box(UEC[1], YE + 15, 0, UE[0], YE + 23, WALKZ, "bk_walk", group="detail")
    box(268, YE + 15, 0, 655, YE + 23, WALKZ, "bk_walk", group="detail")
    box(268, YE - 27, 0, 655, YE - 21, WALKZ, "bk_walk", group="detail")
    # a Sacramento St stub north of E 21st exists in the cut piece; palms and lamps on the median, hedge beds between them
    for y in range(int(UY0) + 14, int(UY1) - 10, 30):
        if abs(y - YE) < 30:
            continue
        palm(MEDX, y, h=24 + (y // 30) % 3 * 3)
    for y0_ in range(int(UY0) + 4, int(UY1) - 20, 60):
        if abs(y0_ + 16 - YE) < 34:
            continue
        box(MEDX - 5.5, y0_ + 6, WALKZ, MEDX + 5.5, y0_ + 24, 3.0, "bk_hedge", group="detail")
    for y in range(int(UY0) + 40, int(UY1), 90):                                                 # cobra-head lamps on the median curb, as in goldenwest
        if abs(y - YE) < 40:
            continue
        prop(MEDX - 0.3, y - 0.3, 0, MEDX + 0.3, y + 0.3, 30, "bk_steel")
        prop(MEDX - 9.5, y - 0.3, 30, MEDX + 0.3, y + 0.3, 30.6, "bk_steel")
        prop(MEDX - 0.3, y - 0.3, 30, MEDX + 9.5, y + 0.3, 30.6, "bk_steel")
        ent("light", MEDX - 8, y, 28, light=210, _color="255 240 210")
        ent("light", MEDX + 8, y, 28, light=210, _color="255 240 210")

    # traffic signals at the E 21st crossing: a mast and arm on each of the four corners, three lamps on a box
    def signal(x, y, toward):
        prop(x - 0.4, y - 0.4, 0, x + 0.4, y + 0.4, 20, "bk_steel")
        ax, ay = x + toward[0] * 14, y + toward[1] * 14
        prop(min(x, ax) - (0.3 if toward[1] else 0), min(y, ay) - (0.3 if toward[0] else 0), 19.4,
             max(x, ax) + (0.3 if toward[1] else 0), max(y, ay) + (0.3 if toward[0] else 0), 20.0, "bk_steel")
        bx_, by_ = ax - 0.8, ay - 0.8
        prop(bx_, by_, 14.4, bx_ + 1.6, by_ + 1.6, 19.4, "bk_chairbk")
        prop(bx_ + 0.3, by_ + 0.3, 17.8, bx_ + 1.3, by_ + 1.3, 18.9, "bk_red")
        prop(bx_ + 0.3, by_ + 0.3, 16.5, bx_ + 1.3, by_ + 1.3, 17.6, "bk_yline")
        prop(bx_ + 0.3, by_ + 0.3, 15.2, bx_ + 1.3, by_ + 1.3, 16.3, "bk_playgreen")

    signal(UW[0] + 1.0, YE - 24, (1, 0))
    signal(UW[0] + 1.0, YE + 24, (1, 0))
    signal(UE[1] - 1.0, YE + 24, (-1, 0))
    signal(UEC[1] + 3, YE - 24, (-1, 0))


# ============================================================================================ cars, cover, plaza
CARS = {"sedan": (17.0, 6.8, 5.3), "coupe": (16.0, 6.9, 4.3), "truck": (19.6, 8.2, 7.5), "van": (18.6, 7.7, 7.8)}


def car_at(x, y, yaw, kind):
    L, W, H = CARS[kind]
    hl, hw = (L / 2, W / 2) if yaw in (0, 180) else (W / 2, L / 2)
    if not solid_free(x, y, max(hl, hw) + 0.5):
        return False
    ent("misc_model", x, y, 0.2, mdl="progs/veh_%s.md3" % kind, angles="0 %d 0" % yaw, scale="1.0")
    box(x - hl, y - hw, 0.7, x + hl, y + hw, H, "clip")
    SOLIDS.append((u(x - hl, OX), u(y - hw, OY), u(0.7), u(x + hl, OX), u(y + hw, OY), u(H)))
    return True


with unscaled():
    # abandoned cars in the Union lanes (cover for the street fights), never across the E 21st crossing
    kinds = ("sedan", "coupe", "van", "truck")
    n = 0
    for y in range(-200, 1280, 55):
        if abs(y - YE) < 45:
            continue
        for lane_x, yaw in ((UWC[0] + 6.5, 90), (UWC[0] + 19.4, 90), (UEC[0] + 6.5, 270), (UEC[0] + 32.5, 270), (UEC[0] + 19.4, 270)):
            if rng.random() < 0.13:
                n += car_at(lane_x, y + rng.uniform(-8, 8), yaw, rng.choice(kinds))
    print("street cars:", n)

    def planter(x, y, w, d, hedge=True):
        box(x - w / 2, y - d / 2, 0, x + w / 2, y + d / 2, 2.0, "bk_walk")
        if hedge:
            box(x - w / 2 + 0.5, y - d / 2 + 0.5, 2.0, x + w / 2 - 0.5, y + d / 2 - 0.5, 4.2, "bk_hedge", group="detail")

    def cover_field(x0, y0, x1, y1, seed, walls=7, planters=5, cars=3):
        """Low walls, hedge planters, palms and a few cars scattered over a paved area, each tried until nothing is in the way."""
        r = random.Random(seed)
        for _ in range(walls * 6):
            if walls <= 0:
                break
            along_x = r.random() < 0.5
            L, T = r.uniform(14, 26), 1.2
            x, y = r.uniform(x0 + 15, x1 - 15), r.uniform(y0 + 15, y1 - 15)
            w, d = (L, T) if along_x else (T, L)
            if solid_free(x, y, max(w, d) / 2 + 3, 0.2, 7.0):
                box(x - w / 2, y - d / 2, 0, x + w / 2, y + d / 2, 4.5, tspec("bk_extwall", 8), {"t": "bk_roof"})
                walls -= 1
        for _ in range(planters * 6):
            if planters <= 0:
                break
            x, y = r.uniform(x0 + 10, x1 - 10), r.uniform(y0 + 10, y1 - 10)
            if solid_free(x, y, 8, 0.2, 9.0):
                planter(x, y, 10, 6)
                palm(x, y, h=20 + r.randint(0, 6))
                SOLIDS.append((u(x - 5, OX), u(y - 3, OY), 0, u(x + 5, OX), u(y + 3, OY), u(4.2)))
                planters -= 1
        for _ in range(cars * 8):
            if cars <= 0:
                break
            x, y = r.uniform(x0 + 10, x1 - 10), r.uniform(y0 + 10, y1 - 10)
            if car_at(x, y, r.choice((0, 90, 180, 270)), r.choice(kinds)):
                cars -= 1

    cover_field(-60, 430, 150, 790, 11, walls=8, planters=7, cars=5)               # the plaza west of Union
    cover_field(268, 640, 560, 790, 12, walls=7, planters=6, cars=4)               # east of Union between the Sign and the block
    cover_field(150, -245, 268, 130, 13, walls=0, planters=0, cars=0)
    cover_field(-140, -250, -60, -170, 14, walls=2, planters=0, cars=2)
    cover_field(-60, 1000 - 4, 0, 1130, 15, walls=3, planters=2, cars=2)
    cover_field(268, 150, 285, 160, 16, walls=0, planters=0, cars=0)


# ============================================================================================ gameplay
def blk(cls, x1, y1, z1, x2, y2, z2, tex="bk_dirt", **kv):
    """A brush entity (trigger_push, trigger_teleport) over a box, feet."""
    GROUPS["_t"] = []
    n = len(SOLIDS)
    box(x1, y1, z1, x2, y2, z2, tex, group="_t")
    del SOLIDS[n:]
    ENTS.append('{\n"classname" "%s"\n' % cls + "".join('"%s" "%s"\n' % kv_ for kv_ in kv.items()) + GROUPS.pop("_t")[0] + "}\n")


G_UNITS = 800.0


def launch(p0, p1, over=12.0):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    zt = max(z0, z1) + over
    vz = math.sqrt(2 * G_UNITS * (zt - z0) * U)
    t = vz / G_UNITS + math.sqrt(2 * (zt - z1) * U / G_UNITS)
    return ((x1 - x0) * U / t, (y1 - y0) * U / t, vz)


def push_kv(v):
    sp = math.sqrt(sum(c * c for c in v))
    return {"angles": "%.1f %.1f 0" % (-math.degrees(math.asin(v[2] / sp)), math.degrees(math.atan2(v[1], v[0]))), "speed": "%.1f" % (sp / 10)}


def jump_pad(x, y, target=None, apex=120.0, size=8.0, z=0.0):
    h = size / 2
    box(x - h, y - h, z, x + h, y + h, z + 0.4, "bk_steel", {"t": Fit("bk3_jump")}, group="detail")
    if target is None:
        v = (0.0, 0.0, math.sqrt(2 * G_UNITS * apex * U))
        kv = {"angles": "-90 0 0", "speed": "%.1f" % (v[2] / 10)}
    else:
        kv = push_kv(launch((x, y, z), target))
    blk("trigger_push", x - h + 0.5, y - h + 0.5, z + 0.4, x + h - 0.5, y + h - 0.5, z + 5, **kv)
    ent("light", x, y, z + 3, light=90, _color="255 210 60")


def tp_pad(x, y, dest, board, along="x"):
    """A glowing pad, a board on two posts and a trigger_teleport to the info_teleport_destination `dest`."""
    box(x - 4, y - 4, 0, x + 4, y + 4, 0.5, "bk_steel", {"t": Fit("bk3_tp")}, group="detail")
    blk("trigger_teleport", x - 3.5, y - 3.5, 0.5, x + 3.5, y + 3.5, 8, target=dest)
    ent("light", x, y, 4, light=140, _color="60 230 255")
    for bx_ in (x - 5.2, x + 5.2):
        prop(bx_ - .2, y + 4.6, 0, bx_ + .2, y + 5.0, 8, "bk_steel")
    prop(x - 5.5, y + 4.7, 4.8, x + 5.5, y + 4.9, 8.0, "bk_steel", {"s": Fit(board), "n": Fit(board)})


def ok_spot(x, y, z, hull=1.5):
    lo, hi = (u(x - hull, OX), u(y - hull, OY), u(z + 0.3)), (u(x + hull, OX), u(y + hull, OY), u(z + 4.6))
    return not any(all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)) for b in SOLIDS)


def put(cls, x, y, z=0.0, hull=1.5, **kv):
    """Place a spawn / item at (x, y) final feet standing on floor level z; moved over a few offsets until the hull fits."""
    for dx, dy in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3), (6, 3), (-6, -3), (6, -6), (-6, 6), (10, 0), (-10, 0), (0, 10), (0, -10)):
        if ok_spot(x + dx, y + dy, z, hull):
            ent(cls, x + dx, y + dy, z + (2.2 if cls.startswith("info_player") else 1.0), **kv)
            return True
    print("NOT PLACED", cls, x, y, z)
    return False


A = lambda x, y: (x + 607, y + YE + 3)               # B-LAN frame -> final feet
C = lambda x, y: (x - 465, y + 450)                  # Sign / Palace
O = lambda x, y: (x - 308, y + 670)                  # ORCOM

with unscaled():
    # ---- 10 deathmatch spawns, spread over both places and the street
    for (x, y), ang in (((-30, 103), 0), ((62, 24), 90), ((-45, -95), 90), ((180, 40), 90), (A(-125, 170), 0), (A(-115, 60), 90),
                        (A(-185, -10), 0), (O(365, 303), 0), (C(855, -3), 90), ((234, 640), 90)):
        put("info_player_deathmatch", x, y, 0.0, angle=ang)
    if not os.environ.get("BKS_START"):
        ent("info_player_start", 180, 20, 2.2, angle=90)
    if os.environ.get("BKS_START"):                                                       # test views: BKS_START="x y z yaw [pitch]" (final feet)
        _v = [float(v) for v in os.environ["BKS_START"].split()]
        if _v[2] > 10:                                                                    # high up: a small platform to stand on (the start drops to the floor)
            box(_v[0] - 3.5, _v[1] - 3.5, _v[2] - 4, _v[0] + 3.5, _v[1] + 3.5, _v[2], "bk_steel")
        ent("info_player_start", _v[0], _v[1], _v[2] + 2.5, angles="%d %d 0" % (_v[4] if len(_v) > 4 else 0, _v[3]))

    # ---- weapons: one of each (not twenty); armour / jetpacks; health; ammo
    for cls, (x, y), z in (("weapon_supershotgun", (6, 130), 0), ("weapon_nailgun", A(-115, 80), 0), ("weapon_grenadelauncher", O(426, 320), 0),
                           ("weapon_rocketlauncher", C(915, -3), 0), ("weapon_lightning", A(-108, 162), 0),
                           ("weapon_supernailgun", (205, 600), 0)):
        put(cls, x, y, z)
    for cls, (x, y), z in (("item_armor2", (46, 26), 0), ("item_armor2", C(920, -48), 30), ("item_armor2", A(-100, 176), 0), ("item_armor2", O(440, 323), 0),
                           ("item_armor1", (235, 300), 0)):
        put(cls, x, y, z)
    for x, y in ((21, 56), (62, 30), (143, -95), (-30, 222), (A(-115, 30)), (O(380, 320)), (C(840, -80)), (A(0, 150)), (240, 880)):
        put("item_health", x, y, 0)
    put("item_health", *C(920, 42), 30, spawnflags=2)                                            # the mega health on the Sign
    for cls, (x, y) in (("item_shells", (-30, 56)), ("item_shells", A(-112, 150)), ("item_shells", O(366, 336)), ("item_spikes", (81, -95)),
                        ("item_spikes", A(-110, 170)), ("item_rockets", (80, 24)), ("item_rockets", O(398, 303)), ("item_cells", C(910, 50)),
                        ("item_rockets", (190, 760))):
        put(cls, x, y, 0)
    # roofs reached by the jump pads of make_bklan_v3.py (kept with the cut piece): a rocket launcher pack and cells on the LAN building roof
    for cls, (x, y) in (("item_rockets", A(-40, 60)), ("item_cells", A(-153, 100))):
        put(cls, x, y, 17.0)

    # ---- teleports between the halves: casino <-> Larry's lot, and the Sign <-> the ORCOM hall (and a one-way sky pad below)
    ent("info_teleport_destination", 120, 330, 0.3, targetname="tp_casino", angle=0)
    ent("info_teleport_destination", *A(-112, 118), 0.3, targetname="tp_larry", angle=90)
    ent("info_teleport_destination", *C(833, -3), 0.3, targetname="tp_sign", angle=0)
    ent("info_teleport_destination", *O(448, 312), 0.3, targetname="tp_orcom", angle=0)
    tp_pad(100, 300, "tp_larry", "bk3_tpsign1")
    tp_pad(*A(-112, 100), "tp_casino", "gw_1001")
    tp_pad(*C(815, -3), "tp_orcom", "bk3_tpsign1")
    tp_pad(*O(452, 330), "tp_sign", "bk3_tpsign2")
    # ---- jump pads: Union median -> up onto the Bakersfield Sign (one corner of the cut piece is reached already), and sky launchers
    jump_pad(MEDX, 120, target=(*C(920, -48), 30.0))
    jump_pad(MEDX, 760, apex=300.0)                                                               # straight up: the jetpack and the tall sky
    jump_pad(-100, -100, apex=200.0)

SPOTS = [("Casino lot", -45, -95, 2.2, 90), ("Casino lobby", 62, 24, 2.2, 90), ("Union Ave south", 180, 40, 2.2, 90), ("Union Ave middle", 234, 640, 2.2, 90)]
json.dump([{"name": n_, "pos": [u(x, OX), u(y, OY), u(z)], "yaw": a} for n_, x, y, z, a in SPOTS],
          open(os.path.join(os.path.dirname(os.path.abspath(OUT)), "bakolansmall.spots.json"), "w"))

# ============================================================================================ write
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w") as f:
    f.write('{\n"classname" "worldspawn"\n"wad" "bklan.wad;goldenwest.wad;bklan3.wad;gwcasino.wad"\n"message" "bakolansmall - Golden West and B-LAN on S Union Ave"\n')
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
print("wrote", OUT, len(GROUPS["world"]), "world +", len(GROUPS["detail"]), "detail +", len(GROUPS["fence"]), "fence +", len(GROUPS["illus"]), "illus,", len(ENTS), "entities")
