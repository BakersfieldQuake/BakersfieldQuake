"""Writes bklan.map: the B-LAN party warehouse (2001) and the whole block round it on E 21st St, Bakersfield.

The site is real: building footprints (Bakersfield city GIS) and street centrelines from OpenStreetMap, turned into
this map's frame by bklan_osm.py (x along E 21st St to the east-south-east, y along Sacramento St to the
north-north-east, origin where they cross). The LAN unit (130A) is the north end of the building along Sacramento St
(OSM 45), its roll-up facing west onto the lot between it and the 118 / 120 E 21st St building (OSM 76) - where the
user pointed on the 3D view. Inside it is the hall and back room from bklan.wmv. Street side from the Street View
gallery (Feb 2026). Everything is in feet here and written at 12 Quake units per foot.

Covered: E 21st / W 21st St from Golden State Ave east past Sonora St, Sacramento St, Sumner St, Union Ave climbing
onto its overpass over Sumner St and the UP railroad, Golden State Ave, the Union Ave Loop ramp, every GIS building
in between (heights and walls guessed by type).
Guessed (no footage): the inside of 120A, the lot's tents and cars, building heights, parked cars along the streets.

python -I make_bklan.py <out.map>   then qbsp -> vis -> light (ericw-tools), textures from build_bklan_textures.py"""
import json
import math
import os
import struct
import sys
from contextlib import contextmanager

HERE = os.path.dirname(os.path.abspath(__file__))
WAD = os.path.join(HERE, "out", "maps", "bklan.wad").replace("\\", "/")
out = sys.argv[1]

U = 12                 # units per foot
OX, OY = -110, 225      # feet: this point is the map origin

# texture sizes, read back from the wad, for textures stretched to fit a face
TEXSIZE = {}
with open(WAD, "rb") as f:
    _, n, ofs = struct.unpack("<4sii", f.read(12))
    f.seek(ofs)
    dirs = [struct.unpack("<3i2bh16s", f.read(32)) for _ in range(n)]
    for pos, _, _, _, _, _, name in dirs:
        f.seek(pos)
        nm, w, h = struct.unpack("<16s2I", f.read(24))
        TEXSIZE[name.split(b"\0")[0].decode()] = (w, h)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def u(v, o=0):
    return int(round((v - o) * U))


class Fit:
    """A texture stretched (not tiled) over one face."""
    def __init__(self, name, repeat=(1, 1)):
        self.name, self.repeat = name, repeat


def texline(spec, side, lo, hi):
    """Texture name, offsets and scales for one face. lo/hi are the brush's min/max corners in units.
    Quake projects X-facing faces on (y, -z), Y-facing on (x, -z), floors on (x, -y)."""
    if isinstance(spec, str) and " " in spec:          # already a full spec (world-fit textures)
        return spec
    if not isinstance(spec, Fit):
        return "%s 0 0 0 1 1" % spec
    tw, th = TEXSIZE[spec.name]
    if side in "ew":
        a0, a1 = lo[1], hi[1]
    else:
        a0, a1 = lo[0], hi[0]
    if side in "tb":
        b0, b1 = -hi[1], -lo[1]          # t runs along -y
    else:
        b0, b1 = -hi[2], -lo[2]          # t runs along -z
    xs = (a1 - a0) / (tw * spec.repeat[0])
    ys = (b1 - b0) / (th * spec.repeat[1])
    flip = side in ("w", "n")            # seen from outside, s runs right-to-left on these faces
    if flip:
        xs, xo = -xs, a1 / xs
    else:
        xo = -a0 / xs
    yo = -b0 / ys
    return "%s %.3f %.3f 0 %.5f %.5f" % (spec.name, xo, yo, xs, ys)


def face(p0, p1, p2, outward, tex):
    n = cross(sub(p0, p1), sub(p2, p1))
    if sum(n[i] * outward[i] for i in range(3)) < 0:
        p0, p2 = p2, p0
    pts = " ".join("( %d %d %d )" % p for p in (p0, p1, p2))
    return "%s %s\n" % (pts, tex)


GROUPS = {"world": [], "detail": [], "fence": [], "illus": []}   # illus: seen, not solid (leaves, paint)


def box(x1, y1, z1, x2, y2, z2, tex, faces=None, group="world"):
    """Axis-aligned brush, corners in feet. faces: {'n','s','e','w','t','b'} -> texture name or Fit."""
    faces = faces or {}
    if XF:
        (x1, y1), (x2, y2) = _xf(x1, y1), _xf(x2, y2)
        if XF[0]:
            faces = {SWAP.get(k, k): v for k, v in faces.items()}
    X1, X2 = sorted((u(x1, OX), u(x2, OX)))
    Y1, Y2 = sorted((u(y1, OY), u(y2, OY)))
    Z1, Z2 = sorted((u(z1), u(z2)))
    if X1 == X2 or Y1 == Y2 or Z1 == Z2:
        return
    lo, hi = (X1, Y1, Z1), (X2, Y2, Z2)
    t = lambda k: texline(faces.get(k, tex), k, lo, hi)
    s = "{\n"
    s += face((X1, Y1, Z1), (X1, Y2, Z1), (X1, Y1, Z2), (-1, 0, 0), t("w"))
    s += face((X2, Y1, Z1), (X2, Y1, Z2), (X2, Y2, Z1), (1, 0, 0), t("e"))
    s += face((X1, Y1, Z1), (X1, Y1, Z2), (X2, Y1, Z1), (0, -1, 0), t("s"))
    s += face((X1, Y2, Z1), (X2, Y2, Z1), (X1, Y2, Z2), (0, 1, 0), t("n"))
    s += face((X1, Y1, Z1), (X2, Y1, Z1), (X1, Y2, Z1), (0, 0, -1), t("b"))
    s += face((X1, Y1, Z2), (X1, Y2, Z2), (X2, Y1, Z2), (0, 0, 1), t("t"))
    GROUPS[group].append(s + "}\n")
    if tex not in ("sky_bk", "clip") and Z2 - Z1 > 2 and group != "illus":
        SOLIDS.append((X1, Y1, Z1, X2, Y2, Z2))


XF = None              # (turned 180 degrees?, dx, dy): moves whole pieces of the old layout into place
SWAP = {"n": "s", "s": "n", "e": "w", "w": "e"}


def _xf(x, y):
    r, dx, dy = XF
    return (dx - x, dy - y) if r else (x + dx, y + dy)


@contextmanager
def placed(rot180, dx, dy):
    """Everything built inside lands at (dx - x, dy - y) if rot180, else (x + dx, y + dy)."""
    global XF
    XF = (rot180, dx, dy)
    try:
        yield
    finally:
        XF = None


def prism(poly, bottom, top, tex, side=None, bot=None, group="world", solid=False):
    """Vertical-sided brush over a convex polygon (feet). bottom / top: one height, or one per corner for a sloped face
    (the corners must be planar). tex / side / bot: texture name or full spec ("name xo yo rot sx sy")."""
    n = len(poly)
    tops = list(top) if isinstance(top, (list, tuple)) else [top] * n
    bots = list(bottom) if isinstance(bottom, (list, tuple)) else [bottom] * n
    P = []
    for (x, y), zt, zb in zip(poly, tops, bots):
        q = (u(x, OX), u(y, OY), u(zt), u(zb))
        if not P or (q[0], q[1]) != (P[-1][0], P[-1][1]):
            P.append(q)
    if len(P) > 1 and (P[0][0], P[0][1]) == (P[-1][0], P[-1][1]):
        P.pop()
    Q = []
    for i in range(len(P)):                                  # drop collinear corners
        a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            Q.append(b)
    P = Q
    m = len(P)
    if m < 3 or any(q[2] <= q[3] for q in P):
        return
    area = sum(P[i][0] * P[(i + 1) % m][1] - P[(i + 1) % m][0] * P[i][1] for i in range(m))
    if abs(area) < 8:
        return
    if area < 0:
        P.reverse()
    spec = lambda t: t if " " in t else "%s 0 0 0 1 1" % t
    s = "{\n"
    for i in range(m):
        a, b = P[i], P[(i + 1) % m]
        s += face((a[0], a[1], a[3]), (b[0], b[1], b[3]), (a[0], a[1], a[3] + 64), (b[1] - a[1], -(b[0] - a[0]), 0),
                  spec(side or tex))
    i1, i2 = max(1, m // 3), max(2, (2 * m) // 3)
    if i2 == i1:
        i2 = i1 + 1
    s += face((P[0][0], P[0][1], P[0][2]), (P[i1][0], P[i1][1], P[i1][2]), (P[i2][0], P[i2][1], P[i2][2]), (0, 0, 1),
              spec(tex))
    s += face((P[0][0], P[0][1], P[0][3]), (P[i1][0], P[i1][1], P[i1][3]), (P[i2][0], P[i2][1], P[i2][3]), (0, 0, -1),
              spec(bot or side or tex))
    GROUPS[group].append(s + "}\n")
    if solid:
        xs, ys = [q[0] for q in P], [q[1] for q in P]
        SOLIDS.append((min(xs), min(ys), min(q[3] for q in P), max(xs), max(ys), max(q[2] for q in P)))


def prop(*a, **k):
    k["group"] = "detail"
    box(*a, **k)


ENTS = []
SOLIDS = []            # every brush's bounds in units, to check spawns and items against
PLACED = []            # (classname, origin in units)


def check_placed():
    """Every spawn needs the player hull clear round it (-16..16, -16..16, -24..32), every item a 32 x 32 x 24 box
    from just under its origin (it drops to the floor). Prints the offenders, returns how many."""
    bad = 0
    for cls, (x, y, z) in PLACED:
        if cls.startswith("info_player"):
            lo, hi = (x - 16, y - 16, z - 23), (x + 16, y + 16, z + 32)
        else:
            lo, hi = (x - 16, y - 16, z - 8), (x + 16, y + 16, z + 16)
        for b in SOLIDS:
            if all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)):
                print("BLOCKED %s at %d %d %d by brush %s" % (cls, x, y, z, b))
                bad += 1
                break
    return bad


def ent(classname, x, y, z, **kv):
    if XF:
        x, y = _xf(x, y)
        if XF[0]:
            if "angle" in kv:
                kv["angle"] = (int(kv["angle"]) + 180) % 360
            if "angles" in kv:
                p, yw, r = kv["angles"].split()
                kv["angles"] = "%s %d %s" % (p, (int(float(yw)) + 180) % 360, r)
    s = '{\n"classname" "%s"\n"origin" "%d %d %d"\n' % (classname, u(x, OX), u(y, OY), u(z))
    if classname.startswith(("info_player", "weapon_", "item_")):
        PLACED.append((classname, (u(x, OX), u(y, OY), u(z))))
    for k, v in kv.items():
        s += '"%s" "%s"\n' % (k, v)
    ENTS.append(s + "}\n")


def light(x, y, z, val=220, color=None, **kv):
    if color:
        kv["_color"] = color
    ent("light", x, y, z, light=int(val * 1.1), **kv)       # x1.1: the rooms were dim (2026-11-01 "bright sunny day"); x1.4 whited the hall out


# ---------------------------------------------------------------------------------------------- walls with openings
T = 8 / U          # block wall thickness (8 in)
WALL_H = 16        # eaves / roof underside
ROOF_TOP = 17
PARA = 19          # parapet top (2 ft over the roof)


def wall(axis, at, a0, a1, z0, z1, inside, outside, out_side, holes=(), deco=(), thick=T, group="world"):
    """A straight wall. axis 'x': runs along x at y=at (thickness toward +y from at if out_side=='s', i.e. the outside
    faces -y). axis 'y': runs along y at x=at, outside on out_side ('w' or 'e').
    holes: (b0, b1, z0, z1) openings; deco: (b0, b1, z0, z1, tex) flush panels on the outside face (doors, signs)."""
    if axis == "x":
        c0, c1 = (at, at + thick) if out_side == "s" else (at - thick, at)
    else:
        c0, c1 = (at, at + thick) if out_side == "w" else (at - thick, at)
    in_side = {"s": "n", "n": "s", "w": "e", "e": "w"}[out_side]
    # cut the wall into vertical strips at every hole/deco edge, then each strip into z bands
    cuts = sorted({a0, a1} | {v for h in holes for v in h[:2]} | {v for d in deco for v in d[:2]})
    cuts = [c for c in cuts if a0 <= c <= a1]
    for b0, b1 in zip(cuts, cuts[1:]):
        mid = (b0 + b1) / 2
        hz = sorted({z0, z1} | {v for h in holes if h[0] <= mid <= h[1] for v in h[2:4]}
                    | {v for d in deco if d[0] <= mid <= d[1] for v in d[2:4]})
        hz = [z for z in hz if z0 <= z <= z1]
        for zz0, zz1 in zip(hz, hz[1:]):
            zm = (zz0 + zz1) / 2
            if any(h[0] <= mid <= h[1] and h[2] <= zm <= h[3] for h in holes):
                continue
            tex_out = outside
            for d in deco:
                if d[0] <= mid <= d[1] and d[2] <= zm <= d[3]:
                    tex_out = Fit(d[4]) if not isinstance(d[4], Fit) else d[4]
            faces = {out_side: tex_out, in_side: inside}
            if axis == "x":
                box(b0, c0, zz0, b1, c1, zz1, inside, faces, group)
            else:
                box(c0, b0, zz0, c1, b1, zz1, inside, faces, group)


def joists(x0, x1, y0, y1, step=4):
    """Steel joists under the roof deck, running east-west (from the roll-up wall to the back, as at 2162 s), and the
    dark ledger band along the top of the walls (122 s)."""
    y = y0 + step / 2
    while y < y1 - 0.5:
        prop(x0, y - 0.15, WALL_H - 1.2, x1, y + 0.15, WALL_H, "bk_steel")
        y += step
    for a in ((x0, y0, x1, y0 + 0.15), (x0, y1 - 0.15, x1, y1), (x0, y0, x0 + 0.15, y1), (x1 - 0.15, y0, x1, y1)):
        prop(a[0], a[1], WALL_H - 1.4, a[2], a[3], WALL_H, "bk_steel")


def tube_light(x, y, length=8, z=12, along="x", val=230):
    """Hanging two-tube fluorescent strip on two chains."""
    if along == "x":
        prop(x - length / 2, y - 0.4, z, x + length / 2, y + 0.4, z + 0.35, "bk_steel", {"b": "bk_tube"})
        for cx in (x - length / 2 + 0.5, x + length / 2 - 0.6):
            prop(cx, y - 0.05, z + 0.35, cx + 0.1, y + 0.05, WALL_H - 1.2, "bk_steel")
    else:
        prop(x - 0.4, y - length / 2, z, x + 0.4, y + length / 2, z + 0.35, "bk_steel", {"b": "bk_tube"})
        for cy in (y - length / 2 + 0.5, y + length / 2 - 0.6):
            prop(x - 0.05, cy, z + 0.35, x + 0.05, cy + 0.1, WALL_H - 1.2, "bk_steel")
    light(x, y, z - 1, val, "0.92 0.97 1")


# ---------------------------------------------------------------------------------------------- LAN props
_LAN_TBL_SEQ = [0]
_LAN_PC_SEQ = [0]
_LAN_CHR_SEQ = [0]
_LAN_SKIN_RING = (0, 1, 3, 4, 2, 0, 4, 1, 5, 3)   # Q3A (0,3), Counter-Strike (1,4), Windows 98 (2,5)


def _lan_solid_box(x1, y1, z1, x2, y2, z2):
    """Register spawn-time bounds of explodable 3D LAN props in SOLIDS so check_placed() keeps spawns/items clear."""
    if XF:
        (x1, y1), (x2, y2) = _xf(x1, y1), _xf(x2, y2)
    X1, X2 = sorted((u(x1, OX), u(x2, OX)))
    Y1, Y2 = sorted((u(y1, OY), u(y1 + (y2 - y1), OY)))
    Z1, Z2 = sorted((u(z1), u(z2)))
    SOLIDS.append((X1, Y1, Z1, X2, Y2, Z2))


def table(x, y, along="x", length=8, depth=2.5, top="bk_wood", z=None, variant=None):
    """Explodable 3D LAN table (misc_lan_table, 4 full-size 8-ft models + cnt=5 compact 5.8-ft desk). (x, y) = min corner."""
    zf = (1 / U) if z is None else z
    idx = _LAN_TBL_SEQ[0]
    _LAN_TBL_SEQ[0] = idx + 1
    if variant is not None:
        v = variant
    elif length < 7.0:
        v = 5
    else:
        v = (idx % 4) + 1
    if along == "x":
        cx, cy = x + length / 2.0, y + depth / 2.0
        yaw = 0 if (idx % 2 == 0) else 180
        _lan_solid_box(x, y, zf, x + length, y + depth, zf + 2.5)
    else:
        cx, cy = x + depth / 2.0, y + length / 2.0
        yaw = 90 if (idx % 2 == 0) else 270
        _lan_solid_box(x, y, zf, x + depth, y + length, zf + 2.5)
    ent("misc_lan_table", cx, cy, zf, angles="0 %d 0" % yaw, cnt=v)


def pc(x, y, facing, z=None, tower=True, kbd=True, mon_var=None, pc_var=None, skin=None):
    """Explodable 3D CRT monitor (playing Q3A / Counter-Strike / Windows 98, w/ 3D keyboard+mouse) + explodable 3D PC tower."""
    zf = (2.5 + 1 / U) if z is None else z
    idx = _LAN_PC_SEQ[0]
    _LAN_PC_SEQ[0] = idx + 1
    mv = mon_var if mon_var is not None else ((idx % 4) + 1)
    pv = pc_var if pc_var is not None else (((idx * 3 + 1) % 4) + 1)
    sk = skin if skin is not None else _LAN_SKIN_RING[idx % len(_LAN_SKIN_RING)]
    ang = "0 %d 0" % FACING_YAW[facing]
    if facing in "ns":
        mx = (x - 0.18) if tower else x
        ent("misc_lan_monitor", mx, y, zf, angles=ang, cnt=mv, skin=sk)
        if tower:
            ent("misc_lan_pc", x + 0.94, y, zf, angles=ang, cnt=pv)
    else:
        my = (y - 0.18) if tower else y
        ent("misc_lan_monitor", x, my, zf, angles=ang, cnt=mv, skin=sk)
        if tower:
            ent("misc_lan_pc", x, y + 0.94, zf, angles=ang, cnt=pv)


# SimReady props (simready_props.py writes progs/bklan/<name>.md3): yaw that turns each model to face +x
MODEL_YAW = {}
FACING_YAW = {"e": 0, "n": 90, "w": 180, "s": 270}


def model(name, x, y, z=0, facing="e", scale=None, clip=None):
    """A SimReady prop: the mod's misc_model, no collision of its own. clip = (half width ft, height ft) puts a
    player clip box round it."""
    kv = {"mdl": "progs/bklan/%s.md3" % name, "angles": "0 %d 0" % ((FACING_YAW[facing] + MODEL_YAW.get(name, 0)) % 360)}
    if scale:
        kv["scale"] = scale
    ent("misc_model", x, y, z, **kv)
    if clip:
        r, h = clip
        box(x - r, y - r, z, x + r, y + r, z + h, "clip")


def chair(x, y, facing, kind="fold", z=None, variant=None):
    """Explodable 3D LAN chair (misc_lan_chair, 4 unique models: banquet, executive rolling, steel folding, task).
    facing = the way the sitter looks."""
    zf = (1 / U) if z is None else z
    idx = _LAN_CHR_SEQ[0]
    _LAN_CHR_SEQ[0] = idx + 1
    if variant is not None:
        v = variant
    elif kind == "office":
        v = 2 if (idx % 2 == 0) else 4
    else:
        v = (3, 1, 3, 4)[idx % 4]
    _lan_solid_box(x - 0.85, y - 0.85, zf, x + 0.85, y + 0.85, zf + 3.0)
    ent("misc_lan_chair", x, y, zf, angles="0 %d 0" % FACING_YAW[facing], cnt=v)


def chair_brush(x, y, facing, kind="fold"):
    """Folding chair (blue seat) or office chair (black). facing = the way the sitter looks."""
    tex = "bk_chairbl" if kind == "fold" else "bk_chairbk"
    prop(x - .7, y - .7, 1.4, x + .7, y + .7, 1.55, tex)
    off = {"n": (0, -.7), "s": (0, .6), "e": (-.7, 0), "w": (.6, 0)}[facing]
    if facing in "ns":
        prop(x - .7, y + off[1], 1.55, x + .7, y + off[1] + .1, 3.0, tex)
    else:
        prop(x + off[0], y - .7, 1.55, x + off[0] + .1, y + .7, 3.0, tex)
    if kind == "fold":
        prop(x - .7, y - .65, 0, x - .6, y + .65, 1.4, "bk_steel")
        prop(x + .6, y - .65, 0, x + .7, y + .65, 1.4, "bk_steel")
    else:
        prop(x - .08, y - .08, .3, x + .08, y + .08, 1.4, "bk_steel")
        prop(x - .9, y - .1, 0, x + .9, y + .1, .3, "bk_chairbk")
        prop(x - .1, y - .9, 0, x + .1, y + .9, .3, "bk_chairbk")


CAR_AS_MODEL = None
if os.environ.get("BKLAN_V3"):                      # off unless asked (see make_bklan_v3.py)
    exec(open(os.path.join(HERE, "make_bklan_v3_cars.py")).read())


def car(x, y, along, body, length=16, width=6.2, pickup=False, cab_h=1.9):
    """Low-poly car / pickup. (x, y) = centre."""
    if CAR_AS_MODEL and CAR_AS_MODEL(x, y, along, body, length, pickup):     # bklan2: the vehicle models replace most cars
        return
    L, W = length / 2, width / 2
    def bx(a0, a1, b0, b1, z0, z1, tex, faces=None):
        if along == "x":
            prop(x + a0, y + b0, z0, x + a1, y + b1, z1, tex, faces)
        else:
            prop(x + b0, y + a0, z0, x + b1, y + a1, z1, tex, faces)
    bx(-L, L, -W, W, 1.2, 3.2, body)
    if pickup:
        bx(-L + 1.5, -L + 7.5, -W + .2, W - .2, 3.2, 3.2 + cab_h, body, {"e": "bk_glass", "w": "bk_glass"} if along == "x" else {"n": "bk_glass", "s": "bk_glass"})
        bx(-L + 7.5, L - .2, -W + .1, -W + .4, 3.2, 4.2, body)
        bx(-L + 7.5, L - .2, W - .4, W - .1, 3.2, 4.2, body)
        bx(L - .4, L - .1, -W + .4, W - .4, 3.2, 4.2, body)
    else:
        bx(-L + 3.5, L - 4.5, -W + .3, W - .3, 3.2, 3.2 + cab_h * .85, "bk_glass", {"t": body})
    for a in (-L + 2.6, L - 3.4):
        for b in (-W - .05, W - .75):
            bx(a, a + 2.2, b, b + .8, 0, 2.2, "bk_tire")


def crate(x, y, z, s=3):
    prop(x, y, z, x + s, y + s, z + s, "bk_crate")


def cone(x, y):
    prop(x - .25, y - .25, 0, x + .25, y + .25, 3.3, "bk_cone",
         {"n": Fit("bk_conestr"), "s": Fit("bk_conestr"), "e": Fit("bk_conestr"), "w": Fit("bk_conestr"), "t": "bk_cone"})


def boxfan(x, y, facing):
    """Pedestal fan (SimReady); the footage shows pedestal fans and box fans."""
    model("fan_pedestal", x, y, 0, facing, clip=(0.8, 3))


def boxfan_brush(x, y, facing):
    if facing in "ns":
        prop(x - .9, y - .25, 0, x + .9, y + .25, 1.8, "bk_white", {facing: "bk_chairbk"})
    else:
        prop(x - .25, y - .9, 0, x + .25, y + .9, 1.8, "bk_white", {facing: "bk_chairbk"})



# ================================================================================================= the site (OSM)
# Footprints and street centrelines from OpenStreetMap (bklan_osm.py; the footprints are Bakersfield city GIS).
OSM = json.load(open(os.path.join(HERE, "bklan_osm.json")))
X0, X1, Y0, Y1 = -820, 650, -340, 790     # the old block (box A)
XB, YB = 1870, -1110                        # box B, east of it: Sillect Ave, the Bakersfield Sign, the Crystal Palace,
                                            # Manning St and Amberton Park (make_bklan_v2.py)
SKY_Z = 500 if os.environ.get("BKLAN_V4") else 64     # bklan3: "the skybox needs to be much higher"
ROADZ = 1 / U                      # road surfaces sit one unit above the lots
WALKZ = 0.5                        # sidewalks: a 6 in curb


def tspec(tex, bay_ft):
    """Texture spec for world-projected faces: one texture repeat = bay_ft feet."""
    th = TEXSIZE[tex][1]
    s = bay_ft * U / th
    return "%s 0 0 0 %.5f %.5f" % (tex, s, s)


# the hull is L-shaped: box A (X0..X1, Y0..Y1) and box B (X1..XB, YB..Y1)
for x0, y0, x1, y1 in ((X0, Y0, X1, Y1), (X1, YB, XB, Y1)):
    box(x0 - 1, y0 - 1, -3, x1 + 1, y1 + 1, -2, "bk_dirt")                     # hull floor
    box(x0 - 1, y0 - 1, SKY_Z, x1 + 1, y1 + 1, SKY_Z + 1, "sky_bk")
box(X0, Y0, -2, X1, Y1, 0, "bk_asphalt")                                       # the lots: one big slab
box(X1, -460, -2, XB, Y1, 0, "bk_asphalt")                                     # box B: lots north of Manning St's zone
box(X1, YB, -2, XB, -460, 0, "bk_lawn")                                        # ... and the yards round Manning St
for x0, y0, x1, y1 in ((X0 - 1, Y0 - 1, X0, Y1 + 1), (XB, YB - 1, XB + 1, Y1 + 1), (X0, Y1, XB, Y1 + 1),
                       (X0, Y0 - 1, X1, Y0), (X1, YB - 1, XB, YB), (X1 - 1, YB, X1, Y0)):
    box(x0, y0, -3, x1, y1, SKY_Z, "sky_bk")
for x0, y0, x1, y1 in ((X0, Y0, X0 + 4, Y1), (XB - 4, YB, XB, Y1), (X0, Y1 - 4, XB, Y1), (X0, Y0, X1, Y0 + 4),
                       (X1, YB, XB, YB + 4), (X1, YB, X1 + 4, Y0)):
    box(x0, y0, 0, x1, y1, SKY_Z, "clip")                                      # keep players off the sky


# ---------------------------------------------------------------------------------------------- streets
def resample(pts, step):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L // step))
        for k in range(1, n + 1):
            out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return out


def ribbon(pts, width, tex, z=ROADZ, zprof=None, ext=None, offset=0.0, side_tex="bk_walk", deck=None, walls=None,
           group="world", skip=None):
    """A strip along a polyline (feet): road, sidewalk, ballast, barrier. zprof(x, y) -> surface height for ramps.
    deck: thickness of a bridge slab where the surface is higher than 15 ft (else solid down to the ground).
    skip(x, y) -> True leaves that piece out (crossings)."""
    if zprof:
        pts = resample(pts, 12)
    ext = width * 0.3 if ext is None and not zprof else (ext or 0)
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 0.5:
            continue
        dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -dy, dx
        ax, ay = a[0] - dx * ext + nx * offset, a[1] - dy * ext + ny * offset
        bx_, by_ = b[0] + dx * ext + nx * offset, b[1] + dy * ext + ny * offset
        if skip and skip((ax + bx_) / 2, (ay + by_) / 2):
            continue
        h = width / 2
        poly = [(ax - nx * h, ay - ny * h), (bx_ - nx * h, by_ - ny * h), (bx_ + nx * h, by_ + ny * h), (ax + nx * h, ay + ny * h)]
        za = zprof(*a) if zprof else z
        zb = zprof(*b) if zprof else z
        tops = [za, zb, zb, za]
        if deck and min(za, zb) > 15:
            bottoms = [t - deck for t in tops]
        else:
            bottoms = 0 if not walls else [t - walls for t in tops]
        prism(poly, bottoms, tops, tex, side=side_tex, group=group)


def union_z(x, y):
    """Union Ave climbs onto its overpass (OSM bridge from y 530) over Sumner St and the railroad."""
    if y <= 330:
        return ROADZ
    if y <= 527:
        return ROADZ + 18 * (y - 330) / 197
    if y <= 640:
        return 18 + 4 * (y - 527) / 113
    return 22


def road(name_pts, width, **k):
    ribbon(name_pts, width, "bk_road", **k)


# E 21st St: straight in this frame, built in strips so the paint lines sit flush. Curbs at y 15 / -21.
E21 = [(-21, -13.4, "bk_road"), (-13.4, -13.1, "bk_wline"), (-13.1, -3.35, "bk_road"), (-3.35, -3.0, "bk_yline"),
       (-3.0, -2.6, "bk_road"), (-2.6, -2.25, "bk_yline"), (-2.25, 7.1, "bk_road"), (7.1, 7.4, "bk_wline"), (7.4, 15, "bk_road")]
for y0, y1, tex in E21:
    box(-560, y0, 0, X1, y1, ROADZ, tex, {"n": "bk_walk", "s": "bk_walk"}, group="detail")
road([(-552, -3), (-575, -1), (-642, -34), (-701, -51), (-731, -60), (-830, -88)], 36, group="detail")  # bending into W 21st St
# north sidewalk (to the building line, y 23) and south sidewalk, broken at the side streets
for xa, xb in ((-555, -18), (18, 460), (496, X1)):
    box(xa, 15, 0, xb, 23, WALKZ, "bk_walk", group="detail")
for xa, xb in ((-500, 460), (496, X1)):
    box(xa, -27, 0, xb, -21, WALKZ, "bk_walk", group="detail")
# Sacramento St (curbs x +-18), north from E 21st through Sumner to the railroad; sidewalks both sides
box(-18, 15, 0, 18, 378, ROADZ, "bk_road", group="detail")
for xa, xb in ((-33, -18), (18, 30)):
    box(xa, 23, 0, xb, 372, WALKZ, "bk_walk", group="detail")
# Sonora St (x 478)
box(460, Y0, 0, 496, -21, ROADZ, "bk_road", group="detail")
box(460, 15, 0, 496, 375, ROADZ, "bk_road", group="detail")
for xa, xb in ((448, 460), (496, 508)):
    box(xa, 23, 0, xb, 372, WALKZ, "bk_walk", group="detail")
# Sumner St, from Union Ave's overpass east past Sonora; sidewalks both sides
SUMNER = [(-830, 632), (-733, 656), (-630, 662), (-569, 656), (-512, 643), (-485, 634), (-437, 614), (-391, 589),
          (-232, 487), (-191, 461), (-145, 437), (-96, 418), (-54, 407), (3, 397), (52, 394), (482, 390), (690, 389)]
road(SUMNER, 40, group="detail")
crossing = lambda x, y: abs(x) < 30 or abs(x - 478) < 30 or x < -560
ribbon(SUMNER, 8, "bk_walk", z=WALKZ, offset=24, skip=crossing, group="detail")
ribbon(SUMNER, 8, "bk_walk", z=WALKZ, offset=-24, skip=crossing, group="detail")
# Union Ave: two one-way carriageways (OSM), rising onto the overpass; the Union Ave Loop ramp; Golden State Ave
UNION_NB = [(-507, -345), (-507, -260), (-521, -193), (-531, -146), (-538, -121), (-575, 2), (-584, 47), (-599, 118),
            (-614, 198), (-622, 256), (-653, 531), (-671, 667), (-687, Y1 + 10)]
UNION_SB = [(-739, Y1 + 10), (-731, 740), (-696, 527), (-687, 450), (-677, 348), (-657, 86), (-660, 67), (-679, 10),
            (-701, -51)]
for line in (UNION_NB, UNION_SB):
    ribbon(line, 38, "bk_road", zprof=union_z, deck=2.5, side_tex="bk_walk")
    for off in (-18.5, 18.5):                                                  # jersey barriers up on the ramp
        ribbon([p for p in line if p[1] > 340], 1.2, "bk_walk", zprof=lambda x, y: union_z(x, y) + 3, deck=3.0,
               offset=off, walls=3.0, group="detail")
    for p in resample([p for p in line if p[1] > 540], 60)[1:-1]:             # piers under the deck
        z = union_z(*p)
        if z > 15:
            prism([(p[0] - 2, p[1] - 2), (p[0] + 2, p[1] - 2), (p[0] + 2, p[1] + 2), (p[0] - 2, p[1] + 2)], 0,
                  z - 2.5, "bk_walk", side="bk_walk")
road([(-599, 118), (-581, 142), (-564, 214), (-540, 608), (-532, 628), (-512, 643)], 20, group="detail")  # Union Ave Loop
road([(-483, -345), (-507, -260), (-555, -176), (-590, -117), (-642, -34), (-679, 10), (-703, 39), (-754, 101),
      (-830, 190)], 38, group="detail")                                                                   # Golden State Ave
road([(-830, 110), (-800, 75), (-740, -2), (-701, -51), (-653, -127), (-622, -181), (-610, -207), (-579, -269),
      (-543, -345)], 38, group="detail")
# the UP Fresno Subdivision: two tracks on ballast, under the overpass
for trk in ([(-830, 761), (-650, 734), (-559, 720), (-479, 708), (-414, 698), (-352, 690), (-287, 682), (-225, 674),
             (-161, 666), (-89, 658), (-10, 648), (67, 640), (300, 618), (XB + 10, 532)],
            [(-830, 774), (-639, 745), (-490, 723), (-418, 714), (-353, 704), (-278, 695), (-214, 686), (-139, 677),
             (-43, 666), (65, 654), (139, 646), (206, 640), (400, 628), (XB + 10, 548)]):
    notsac = lambda x, y: abs(x) < 22
    ribbon(trk, 9, "bk_gravel", z=0.8, side_tex="bk_gravel", skip=notsac, group="detail")
    for off in (-2.35, 2.35):
        ribbon(resample(trk, 40), 0.25, "bk_steel", z=1.3, offset=off, side_tex="bk_steel", group="detail")

# power poles and wires along the north side of E 21st, and down Sacramento
for px in range(-540, X1, 110):
    if abs(px) < 25 or abs(px - 478) < 25:
        continue
    prop(px - .4, 18.6, 0, px + .4, 19.4, 32, "bk_pole")
    prop(px - 4, 18.7, 29, px + 4, 19.3, 29.6, "bk_pole")
for wy in (18.8, 19.2):
    for wz in (29.6, 31):
        prop(-540, wy - .03, wz, X1, wy + .03, wz + .06, "bk_leg")
for py in range(60, 380, 110):
    prop(-26.4, py - .4, 0, -25.6, py + .4, 32, "bk_pole")


# ---------------------------------------------------------------------------------------------- buildings (GIS)
def convex_parts(poly):
    """Splits a simple polygon into convex pieces: ear-clip, then merge neighbours while they stay convex."""
    def area(p):
        return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2

    def convex(p):
        n = len(p)
        sgn = 0
        for i in range(n):
            a, b, c = p[i], p[(i + 1) % n], p[(i + 2) % n]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cr) < 1e-6:
                continue
            if sgn == 0:
                sgn = 1 if cr > 0 else -1
            elif (cr > 0) != (sgn > 0):
                return False
        return True

    p = [tuple(q) for q in poly]
    if p[0] == p[-1]:
        p = p[:-1]
    if area(p) < 0:
        p.reverse()
    if convex(p):
        return [p]
    tris, v = [], p[:]
    guard = 0
    while len(v) > 3 and guard < 500:
        guard += 1
        for i in range(len(v)):
            a, b, c = v[i - 1], v[i], v[(i + 1) % len(v)]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 0:
                continue
            inside = False
            for q in v:
                if q in (a, b, c):
                    continue
                d1 = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
                d2 = (c[0] - b[0]) * (q[1] - b[1]) - (c[1] - b[1]) * (q[0] - b[0])
                d3 = (a[0] - c[0]) * (q[1] - c[1]) - (a[1] - c[1]) * (q[0] - c[0])
                if d1 >= 0 and d2 >= 0 and d3 >= 0:
                    inside = True
                    break
            if not inside:
                tris.append([a, b, c])
                del v[i]
                break
    tris.append(v)
    parts = tris
    merged = True
    while merged:
        merged = False
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                A, B = parts[i], parts[j]
                for ia in range(len(A)):
                    e0, e1 = A[ia], A[(ia + 1) % len(A)]
                    if e1 in B and e0 in B and B[(B.index(e1) + 1) % len(B)] == e0:
                        ib = B.index(e1)
                        M = A[:ia + 1] + [B[(ib + 2 + k) % len(B)] for k in range(len(B) - 2)] + A[ia + 1:]
                        if convex(M):
                            parts[i] = M
                            del parts[j]
                            merged = True
                        break
                if merged:
                    break
            if merged:
                break
    return parts


HEROES = {1, 2, 45, 76, 105}       # built by hand below (Street View Feb 2026 + bklan.wmv)
HEIGHT = {"INDUSTRIAL": 20, "COMMERCIAL": 16, "RESIDENTIAL": 11, "GOVERNMENT": 18, "UNKNOWN": 14}
SPECIAL = {69: (26, "bk_lmc", 26), 0: (24, "bk_unitwall", 20), 7: (20, "bk_motel", 20), 88: (22, "bk_unitwall", 20),
           74: (20, "bk_lmc", 20), 47: (18, "bk_lmc", 20)}
for i, b in enumerate(OSM["buildings"]):
    pts = [tuple(p) for p in b["pts"]]
    if i in HEROES or not all(X0 + 6 < x < X1 - 6 and Y0 + 6 < y < Y1 - 6 for x, y in pts):
        continue
    kind = b["tags"].get("bak:fac_type1", "")
    if i in SPECIAL:
        h, wtex, bay = SPECIAL[i]
    else:
        h = HEIGHT.get(kind, 16)
        wtex, bay = {"INDUSTRIAL": ("bk_unitwall", 20), "RESIDENTIAL": ("bk_stucco", 10)}.get(kind, ("bk_shopwall", 20))
    for part in convex_parts(pts):
        prism(part, 0, h, "bk_roof", side=tspec(wtex, bay), solid=True)

# --- #105 Performance Driveline (bright red corrugated metal + black sloped awning) & #1 121 E. 21st breeze-block wall ---
# Street View Feb 2026: sv-front-118e21st-yaw135.jpg, yaw180.jpg
box(-143.6, -180.5, 0, -96.2, -28.0, 17.5, tspec("bk_redcorr", 18), {"t": "bk_roof"})
prop(-142.0, -31.8, 7.6, -104.0, -28.0, 8.2, "bk_chairbk")                        # black sloped front awning
prism([(-142.0, -31.8), (-104.0, -31.8), (-104.0, -28.0), (-142.0, -28.0)], [8.2, 8.2, 8.2, 8.2],
      [8.2, 8.2, 10.4, 10.4], "bk_chairbk", group="detail")
prop(-125.5, -28.12, 0, -121.8, -28.0, 7.2, "bk_blkdoor", {"n": Fit("bk_blkdoor")})
for wx0, wx1 in ((-138, -130), (-118, -108)):
    prop(wx0, -28.12, 2.8, wx1, -28.0, 7.0, "bk_darkwin", {"n": Fit("bk_darkwin")})
prop(-128.0, -28.15, 11.2, -119.5, -28.0, 15.6, "bk_redcorr", {"n": Fit("bk_pdsign")})
# 121 E. 21st: open dirt collision/salvage yard (OSM #1 warehouse demolished), decorative tan breeze-block wall ({lattice)
box(-280, -180, 0, -143.8, -27.2, ROADZ, "bk_dirt", group="detail")
for bx0 in range(-194, -144, 7):                                                   # 7 bays of 10.5 ft quatrefoil lattice
    bx1 = min(bx0 + 6.6, -144.2)
    box(bx0 + 0.35, -27.55, 0, bx1, -27.25, 10.5, Fit("{lattice", ((bx1 - bx0) / 5.3, 10.5 / 5.3)), group="fence")
    prop(bx0, -27.65, 0, bx0 + 0.35, -27.15, 10.8, "bk_brown")
prop(-194, -27.65, 10.5, -144, -27.15, 10.8, "bk_brown")
prop(-193.2, -27.25, 8.9, -187.8, -27.12, 10.1, "bk_white", {"n": Fit("bk_121sign")})
box(-202, -27.1, 0, -180, -26.85, 6.2, Fit("{iron", (22 / 5.3, 1)), group="fence")  # brown/iron gate slid across west bays
# Grey modular office trailer set back in 121 E. 21st's dirt yard + salvage cars + red utility pickup at curb (yaw180)
box(-238, -112, 0, -192, -90, 11.2, tspec("bk_lmc", 14), {"t": "bk_roof"})
for dx_ in (-228, -202):
    prop(dx_, -90.12, 1.5, dx_ + 3.2, -90.0, 8.2, "bk_blkdoor", {"n": Fit("bk_blkdoor")})
    prop(dx_ - 0.5, -93.0, 0, dx_ + 4.0, -90.0, 1.5, "bk_steel")
car(-224, -76, "y", "bk_white", 15.2)
car(-210, -76, "y", "bk_chairbk", 15.6)
car(-196, -74, "y", "bk_chairbk", 17.5, 6.6, pickup=True)
car(-184, -17, "x", "bk_red", 18.5, 6.5, pickup=True)                              # red utility pickup at curb (yaw135/180)
for rx_ in (-191, -176):                                                           # black ladder rack over pickup bed
    prop(rx_, -19.9, 4.2, rx_ + 0.2, -14.1, 6.4, "bk_leg")
for ry_ in (-19.9, -14.3):
    prop(-191, ry_, 6.2, -175.8, ry_ + 0.2, 6.4, "bk_leg")
box(-354, -27.5, 0, -266, -27.2, 6.0, Fit("{iron", (88 / 5.3, 1)), group="fence")

# --- #2 110 E 21st St (J Appliances) & GCI Equipment Rental Yard (sv-west-110e21st-yaw0.jpg, rev2 118 s) ---
box(-330.0, 26.0, 0, -288.0, 192.0, 15.5, tspec("bk_110tan", 16), {"t": "bk_roof"})
box(-330.6, 25.0, 11.5, -287.4, 26.8, 17.6, "bk_fascia", {"b": "bk_fascia"})
prop(-321.5, 24.88, 12.0, -304.5, 25.0, 17.2, "bk_fascia", {"s": Fit("bk_110sale")})
prop(-318.0, 25.88, 0, -314.5, 26.0, 7.2, "bk_blkdoor", {"s": Fit("bk_blkdoor")})
for wx0, wx1 in ((-325.0, -318.5), (-314.0, -307.5), (-298.0, -291.5)):
    prop(wx0, 25.88, 2.5, wx1, 26.0, 7.2, "bk_darkwin", {"s": Fit("bk_darkwin")})
prop(-306.5, 23.8, 0, -304.2, 25.8, 1.8, "bk_playgreen")                           # mint planter + yucca at 110 E 21st
box(-306.2, 24.0, 1.8, -304.5, 25.6, 4.2, "bk_leaf", group="illus")
box(-302.5, 23.2, 0, -288.0, 23.5, 5.2, Fit("{iron", (14.5 / 5.3, 1)), group="fence")
# GCI yard west of 110 E 21st: grass parkway, black wrought-iron fence, GCI pylon sign & lavender floral utility cabinet
box(-486, 15.0, 0, -332, 18.4, WALKZ + 0.04, "bk_lawn", group="detail")
box(-490, 22.8, 0, -330.2, 23.1, 6.4, Fit("{iron", (160 / 5.3, 1)), group="fence")
box(-490.3, 22.8, 0, -490.0, 185.0, 6.4, Fit("{iron", (162 / 5.3, 1)), group="fence")
for px_ in (-487.5, -481.5):
    prop(px_, 27.5, 0, px_ + 0.8, 28.3, 16.5, "oc_blue")
prop(-489.5, 27.0, 16.5, -479.0, 28.8, 22.8, "oc_blue", {"e": Fit("bk_gcisign"), "w": Fit("bk_gcisign")})
prop(-483.5, 19.2, WALKZ, -480.8, 21.6, 5.2, "bk_white", {"w": Fit("bk_floralbox"), "e": Fit("bk_floralbox"), "s": Fit("bk_floralbox")})

# --- #7 Capri Motel details: NW corner salmon monument wall, yellow marquee, iron fence, 2nd-floor balcony & signal ---
box(-472, -27.5, 0, -354, -27.2, 6.0, Fit("{iron", (118 / 5.3, 1)), group="fence")
box(-444, -62.5, 9.8, -388, -57.5, 10.4, "bk_brown", group="detail")               # 2nd-floor exterior walkway
box(-444, -57.8, 10.4, -388, -57.5, 13.4, Fit("{iron", (56 / 5.3, 0.5)), group="fence")
box(-494.5, -32.5, 0, -475.5, -29.8, 23.5, "bk_motel", {"n": Fit("bk_capriwall"), "w": "bk_motel"})
prop(-499.5, -45.5, 10.2, -488.5, -44.2, 14.4, "bk_chairbk", {"n": Fit("bk_capriylw"), "s": Fit("bk_capriylw")})
prop(-494.5, -45.1, 0, -493.7, -44.5, 10.2, "bk_steel")
prop(-495.0, -29.8, 0, -475.5, -26.8, 1.8, "bk_brick")
prop(-494.2, -29.3, 1.8, -476.3, -27.2, 3.0, "bk_hedge")
# Traffic signal mast arm at Capri Motel NW corner (rev2 118 s)
prop(-474.5, -24.5, 0, -473.6, -23.6, 25.0, "bk_steel")
prop(-474.2, -24.2, 18.5, -473.9, 2.0, 19.1, "bk_steel")
for sy_ in (-14.0, -4.0):
    prop(-474.6, sy_ - 0.5, 15.2, -473.5, sy_ + 0.5, 18.5, "bk_leg")


# ---------------------------------------------------------------------------------------------- 76: 118 / 120 E 21st St
# x -229..-143, y 24..187. Front on E 21st (Street View, Feb 2026), the lot sides as in the tape (40-42 s).
B76 = (-229, 24, -143, 187)
sx = (B76[2] - B76[0]) / 74                                                    # the 2026 facade, laid out on 74 ft
front_deco = [(9, 13, 6.5, 10, "bk_baterias"), (14, 17, 0, 7, "bk_blkdoor"), (21, 29, 3, 7.5, "bk_darkwin"),
              (36, 43, 3, 7.5, "bk_darkwin"), (47, 50, 7.5, 9, "bk_sign120b"),
              (52, 54, 0, 9, "bk_bluep"), (54, 57.5, 0, 7.5, "bk_darkwin"), (58, 60, 0, 9, "bk_redp"),
              (61, 63, 0, 9, "bk_bluep"), (64, 66, 0, 9, "bk_redp"), (66, 69, 0, 7.5, "bk_blkdoor"),
              (70, 72, 0, 9, "bk_bluep")]
front_deco = [(B76[0] + a * sx, B76[0] + b * sx, z0, z1, t) for a, b, z0, z1, t in front_deco]
door120 = (B76[0] + 31 * sx, B76[0] + 31 * sx + 3.5)
wall("x", B76[1], B76[0], B76[2], 0, 11.5, "bk_wall", "bk_stucco", "s", holes=[door120 + (0, 7.5)],
     deco=front_deco + [door120 + (7.5, 8.7, "bk_door120")])
box(B76[0], B76[1], 11.5, B76[2], B76[1] + T, WALL_H, "bk_wall")
box(B76[0] - 1.5, B76[1] - 1.5, 11.5, B76[2] + 0.5, B76[1], PARA + 0.5, "bk_fascia", {"b": "bk_fascia"})   # tall blank parapet
box(B76[0] - 1.5, B76[1], 11.5, B76[0], B76[1] + 6, PARA + 0.5, "bk_fascia")
lot_units = [(y, y + 12, 0, 12, "bk_rollupx") for y in range(34, 180, 22)] + \
            [(y + 14, y + 17, 0, 7, "bk_blkdoor") for y in range(34, 160, 44)]
wall("y", B76[2], B76[1], B76[3], 0, WALL_H, "bk_wall", "bk_extwall", "e", deco=lot_units)
wall("y", B76[0], B76[1], B76[3], 0, WALL_H, "bk_wall", "bk_extwall", "w", deco=lot_units)
wall("x", B76[3], B76[0], B76[2], 0, WALL_H, "bk_wall", "bk_extwall", "n")
box(B76[0], B76[1], WALL_H, B76[2], B76[3], ROOF_TOP, "bk_roof", {"b": "bk_deck"})
for x0, y0, x1, y1 in ((B76[0], B76[1], B76[0] + T, B76[3]), (B76[2] - T, B76[1], B76[2], B76[3]),
                       (B76[0], B76[3] - T, B76[2], B76[3])):
    box(x0, y0, ROOF_TOP, x1, y1, PARA, "bk_extwall", {"t": "bk_roof"})
# 120A inside (guessed): the old room, moved here as it was
R120 = (B76[0] + T, B76[1] + T, B76[0] + 45, B76[1] + 36)
box(R120[2] + T, B76[1] + T, 0, B76[2] - T, B76[3] - T, WALL_H, "bk_wall")                       # closed units
box(B76[0] + T, R120[3] + T, 0, R120[2] + T, B76[3] - T, WALL_H, "bk_wall")
with placed(False, B76[0], B76[1]):
    box(T, T, 0, 45, 36, ROADZ, "bk_floor")
    wall("x", 36, 0, 45 + T, 0, WALL_H, "bk_wall", "bk_wall", "s")
    wall("y", 45, T, 36, 0, WALL_H, "bk_wall", "bk_wall", "w")
    joists(T, 45, T, 36)
    tube_light(14, 12, val=260)
    tube_light(14, 26, val=260)
    tube_light(34, 18, val=260)
    prop(20, 9, 0, 34, 11.5, 3.5, "bk_wood", {"s": "bk_white", "n": "bk_white"})   # counter
    pc(24.0, 10.2, "s", z=3.5 + ROADZ, mon_var=4, pc_var=1, skin=2)                 # 120A shop counter CRT + ATX PC
    chair(24.0, 6.8, "n", "office")
    prop(T, 14, 0, T + 2, 34, 7, "bk_steel")                                        # battery racks
    for z in (0.4, 2.6, 4.8):
        for by in range(15, 33, 2):
            prop(T + .2, by, z, T + 1.8, by + 1.4, z + 1, "bk_tire")
    for tz in range(5):
        prop(38, 26, tz * .8, 41, 29, tz * .8 + .75, "bk_tire")                      # tire stack
    car(26, 25, "x", "bk_blue", 15)
    # roof: AC units, vents, the A-frame / antenna mast seen over the parapet
    for ax, ay in ((15, 20), (55, 25), (20, 80), (50, 95), (30, 130)):
        prop(ax, ay, ROOF_TOP, ax + 4, ay + 3, ROOF_TOP + 3.5, "bk_beige", {"t": "bk_steel"})
    for vx, vy in ((35, 50), (60, 70), (10, 110), (64, 120), (40, 140)):
        prop(vx, vy, ROOF_TOP, vx + 1.5, vy + 1.5, ROOF_TOP + 1.5, "bk_steel")
    prop(36, 8, ROOF_TOP, 36.3, 8.3, ROOF_TOP + 12, "bk_steel")
    prop(33, 8, ROOF_TOP + 9, 39.3, 8.3, ROOF_TOP + 9.3, "bk_steel")

# ---------------------------------------------------------------------------------------------- 45: Celebrity Bodyworks bldg
# x -88..-33, y 23..184 along Sacramento St. The LAN unit (130A) is its north end, the roll-up facing west onto the
# lot (where the user pointed on the 3D view). Sacramento side (yaw225, yaw270): white south corner + sidewalk canopy,
# green unit, white unit, bright red CELEBRITY BODYWORKS north half to the NE corner; "Celebrity" sign on the white north wall!
B45 = (-88, 23, -33, 184)
units45 = [(y, y + 12, 0, 12, "bk_rollupx") for y in (30, 52, 74, 96, 118)] + \
          [(y + 14, y + 17, 0, 7, "bk_blkdoor") for y in (30, 74, 118)]
wall("y", B45[0], B45[1], 153.33, 0, WALL_H, "bk_wall", "bk_extwall", "w", deco=units45)
wall("y", B45[2], B45[1], 153.33, 0, WALL_H, "bk_wall", "bk_stucco", "e",
     deco=[(33, 38, 0, 10, "bk_redwall"), (40, 43, 0, 7, "bk_blkdoor"),
           (62, 88, 0, WALL_H, "bk_greenwall"), (73, 76, 0, 7, "bk_blkdoor"),
           (98, 101, 0, 7, "bk_blkdoor"),
           (116, 153.33, 0, WALL_H, "bk_redwall"), (132, 135, 0, 7, "bk_blkdoor"), (138, 141, 0, 7, "bk_blkdoor"),
           (131, 142, 8.5, 13.0, "bk_sign120b")])
wall("x", B45[1], B45[0], B45[2], 0, WALL_H, "bk_wall", "bk_stucco", "s",
     deco=[(-45, -33, 0, WALL_H, "bk_stucco"), (-55, -45, 0, WALL_H, "bk_redwall"), (-76, -68, 0, 7, "bk_blkdoor")])
# Projecting white corner canopy at SE corner of Building 45 (yaw225, yaw135) & west-lot mid-building canopy (bklan 1324 s)
prop(-33, 21.0, 10.5, -24.5, 36.0, 12.6, "bk_fascia", {"b": "bk_fascia"})
prop(-46.0, 20.0, 10.5, -33.0, 23.0, 12.6, "bk_fascia", {"b": "bk_fascia"})
prop(B45[0] - 7.5, 84.0, 11.4, B45[0], 102.0, 13.8, "bk_fascia", {"b": "bk_fascia"})
# Silver fire hydrants & red curb (Sacramento St yaw225 + LAN lot west wall bklan 1396 s)
prop(-19.6, 150.0, WALKZ, -18.8, 150.8, WALKZ + 2.4, "bk_white", {"t": "bk_steel"})
box(-18.6, 144.0, 0, -18.0, 168.0, WALKZ + 0.02, "bk_redwall", group="detail")
prop(B45[0] - 2.2, 78.0, 0, B45[0] - 1.4, 78.8, 2.4, "bk_white", {"t": "bk_steel"})
box(B45[0] + T, B45[1] + T, 0, B45[2] - T, 153.33, WALL_H, "bk_wall")                             # closed units
box(B45[0], B45[1], WALL_H, B45[2], B45[3], ROOF_TOP, "bk_roof", {"b": "bk_deck"})
for x0, y0, x1, y1 in ((B45[0], B45[1], B45[0] + T, B45[3]), (B45[2] - T, B45[1], B45[2], B45[3]),
                       (B45[0], B45[3] - T, B45[2], B45[3]), (B45[0], B45[1], B45[2], B45[1] + T)):
    box(x0, y0, ROOF_TOP, x1, y1, PARA, "bk_extwall", {"t": "bk_roof"})
# crate stack up the lot side onto the roof (shifted south of the tan commercial dumpster outside 130A, bklan 58 s)
for k in range(6):
    prop(B45[0] - 3, 110 + k * 3, 0, B45[0], 113 + k * 3, 3 * (k + 1), "bk_crate")
# Tan/mustard commercial metal dumpster with curved black plastic lid right outside 130A (bklan.wmv 58 s, 1110 s)
prop(B45[0] - 4.4, 146.5, 0, B45[0] - 0.3, 152.5, 4.3, "bk_dumpster")
prop(B45[0] - 4.5, 146.4, 4.3, B45[0] - 0.2, 152.6, 4.85, "bk_chairbk")

# the LAN unit: the hall and back room from the tape, built in the old layout and turned 180 degrees into place
LAN = (True, -14, 220)                    # new = (-14 - old x, 220 - old y)
with placed(*LAN):
    BW = 74
    box(19 + T, 36 + T, 0, BW - T, 66, ROADZ, "bk_floor", group="detail")
    wall("y", BW, 36, 66, 0, WALL_H, "bk_wall", "bk_extwall", "e", holes=[(41, 44.5, 0, 7.5), (52.5, 64.5, 0, 8)],
         deco=[(52.5, 64.5, 8, 12, "bk_rollupx"), (37, 40, 0, 7, "bk_130a"), (41, 44.5, 7.5, 9.5, "bk_glass")])
    # B-LAN / 130A / ENTER -> cardboard-and-foil sign mounted on a tall striped delineator cone outside 130A (bklan 1334 s)
    cone(BW + 1.6, 48.0)
    prop(BW + 1.85, 46.8, 2.3, BW + 2.0, 49.2, 4.1, "bk_crate", {"e": Fit("bk_blansign"), "w": "bk_crate"})
    prop(BW + 1.75, 47.3, 3.9, BW + 2.05, 48.7, 4.25, "bk_duct")                     # aluminum foil wrap at top of sign
    # North wall of Building 45 (faces north into the BODY SHOP yard): white painted block with "Celebrity" sign (yaw270)
    wall("x", 36, 19, BW, 0, WALL_H, "bk_wall", "bk_extwall", "s", deco=[(36, 52, 11.2, 15.2, "bk_celeb")])
    wall("x", 66, 19, BW, 0, WALL_H, "bk_wall", "bk_wall", "s")                   # to the rest of the building
    wall("y", 37, 36 + T, 66, 0, WALL_H, "bk_wall", "bk_wall", "w", holes=[(44, 47.5, 0, 7.5)])   # spine, back door
    wall("y", 19, 36, 66 + T, 0, WALL_H, "bk_wall", "bk_redwall", "w")              # back wall, on Sacramento St (red north end)
    H = WALL_H
    HX0, HX1, HY0, HY1 = 37 + T, BW - T, 36 + T, 66        # inside faces
    joists(HX0, HX1, HY0, HY1)
    for tx in (42, 51, 60):                                  # strips run parallel to the back wall (122, 2024 s)
        tube_light(tx, 51, along="y", val=290)
    # pendant high-bay in the middle, the galvanized duct along the front with its drop, the unit heater by the door
    prop(53, 50.2, 13.2, 69, 51.8, 14.6, "bk_duct")           # supply duct from the heater side to the middle
    prop(54.3, 50.3, 11.6, 55.7, 51.7, 13.2, "bk_duct")       # its drop (138 s) ...
    prop(53.9, 49.9, 10.9, 56.1, 52.1, 11.6, "bk_duct")       # ... ending in a flared diffuser (122, 150 s)
    y = 42.5                                                  # branch to the drop by the office box (2032 s)
    while y < 50:
        model("duct", 68, y, 12.8, "n")
        y += 43 / U
    model("duct_bend", 68, 39.2, 12.8, "s")
    prop(67.2, 38.4, 9, 68.8, 40, 12.8, "bk_duct")
    model("heater", 71.3, 59, 12.2, "w", scale=2.2)          # unit heater hung by the roll-up (2032, 2162 s)
    prop(71.2, 58.8, 14.6, 71.4, 59.2, H - 1.2, "bk_steel")
    # office box: front-right of the roll-up seen from inside, ~9 ft tall, its door facing the room
    OB_X, OB_Y = 63, 47
    wall("y", OB_X, HY0, OB_Y, 0, 10, "bk_trim", "bk_trim", "w", holes=[(40, 43.5, 0, 7)], deco=[], thick=0.33)
    wall("x", OB_Y, OB_X, HX1, 0, 10, "bk_trim", "bk_trim", "n", thick=0.33)
    box(OB_X, HY0, 10, HX1, OB_Y, 10.33, "bk_trim")
    prop(OB_X - 0.15, 44.2, 3, OB_X, 46.4, 5.4, "bk_green")   # the dark green board on the box (1622 s)
    prop(OB_X - .05, 42.2, 0, OB_X - 1.4, 42.3, 7, "bk_trim", {"e": Fit("bk_door"), "w": Fit("bk_door")})  # door swung open
    table(66.2, 44.0, "x", 5.83)                                                      # office desk + PC (explodable)
    pc(69.1, 45.2, "s", tower=True, mon_var=2, pc_var=2, skin=5)
    chair(69.1, 42.5, "n", "office")
    light(68, 42, 8, 120)
    # breaker panel on the pier between the office box and the roll-up (cover off, 84-90 s), conduit down from it
    prop(HX1 - .15, 49, 4, HX1, 50.4, 7.2, "bk_steel", {"w": Fit("bk_panel")})
    prop(HX1 - .12, 49.6, 0, HX1, 49.8, 4, "bk_steel")
    prop(HX1 - .12, 49.6, 7.2, HX1, 49.8, H, "bk_steel")
    # roll-up door, rolled up on its drum, tracks down the jambs
    prop(HX1 - 2, 52.5, 12.2, HX1, 64.5, 14, "bk_rollup")
    prop(HX1 - .1, 52.5, 8, HX1, 64.5, 12.2, "bk_rollup")     # the door itself, run down to ~8 ft (1622 s)
    for jy in (52.3, 64.5):
        prop(HX1 - .5, jy, 0, HX1, jy + .2, 12.2, "bk_steel")

    # tables. North wall row: PCs facing the wall; south wall row: mostly empty (1916 s); centre island back to back.
    for tx in (38, 46, 54):
        table(tx, HY1 - 2.5, "x")
        for k, px in enumerate((tx + 1.35, tx + 3.9, tx + 6.45)):
            if not (tx == 54 and k == 2):
                pc(px, HY1 - 1.5, "s")
                chair(px, HY1 - 4, "n", "office" if k == 1 else "fold")
    for tx in (38, 46, 54):
        table(tx, HY0, "x")
    for px in (39.5, 42.8, 47.3, 50.2, 55.4, 58.2):               # the south row was full earlier (1026, 1104 s)
        pc(px, HY0 + 1, "n", tower=px != 50.2)
        chair(px, HY0 + 3.6, "s", "office" if px == 47.3 else "fold")
    prop(58.4, 49.6, 0, 60.4, 51.4, 4.5, "bk_wood")             # tall wooden podium at the island's end (2020 s)
    prop(62.2, HY0 + .3, 0, 62.9, HY0 + 2.8, 0.7, "bk_green")                        # rolled sleeping bag by office wall
    prop(38.1, 51.0, 0, 39.9, 52.8, 1.8, "bk_beige", {"e": Fit("bk_mbox"), "n": Fit("bk_mbox")})  # empty monitor boxes by spine wall
    prop(38.2, 51.1, 1.8, 39.9, 52.8, 3.6, "bk_beige", {"e": Fit("bk_mbox"), "s": Fit("bk_mbox")})
    for tx in (42, 50):
        table(tx, 47.5, "x")
        table(tx, 50, "x")
        for k, px in enumerate((tx + 1.35, tx + 3.9, tx + 6.45)):
            pc(px, 48.6, "s", kbd=True)
            pc(px, 51.4, "n", tower=k != 1)
            chair(px, 45.6, "n", "office" if k == 0 else "fold")
            chair(px, 54.6, "s", "fold")
    # drinks table just inside the door (Coke bottles, a green bottle)
    table(64.5, 48, "y", 8)
    for by in (49, 49.6, 50.3, 53):                           # 2-litre sodas (SimReady bottle, scaled up)
        model("soda_bottle", 65.4, by, 2.5 + 1 / U, "w", scale=1.8)
    model("soda_bottle", 65.45, 51.65, 2.5 + 1 / U, "e", scale=1.5)  # extra bottle (drops cleanly if table explodes)
    for cx, cy in ((65.6, 54.2), (66.2, 55), (65.2, 55.6)):
        model("cup", cx, cy, 2.5 + 1 / U)
    # cans and fast-food cups round the stations
    for k, (cx, cy) in enumerate(((39.5, 64.3), (44, 64.6), (49.5, 64.2), (57.5, 64.4), (43.8, 47.8), (49, 52.4),
                                 (53.5, 47.9), (57.2, 52.3), (41, 37.4), (47.3, 37.2))):
        model("soda_can" if k % 3 else "cup", cx, cy, 2.5 + 1 / U, "e")
    # the rack with the magenta neon tube and the plush cow, right of the back door (2286 s)
    prop(HX0, 48, 0, HX0 + 2, 50, 5.5, "bk_steel")
    for z in (1, 2.5, 4):
        prop(HX0 + .1, 48.1, z, HX0 + 1.9, 49.9, z + 1, "bk_beige")
    prop(HX0 + .9, 48.1, 5.5, HX0 + 1.1, 49.9, 5.7, "bk_neon")
    light(HX0 + 1, 49, 6.5, 90, "1 0.25 0.85")
    # folded tables leaning on the back wall, whiteboard, box fans, cones, trash can
    for k in range(3):
        prop(HX0 + .1 + k * .25, 55, 0, HX0 + .3 + k * .25, 63, 2.5, "bk_wood")
    prop(36.8, 52, 2.5, 37, 56, 8.5, "bk_white")                                    # whiteboard (back room side of the spine)
    boxfan(62.5, 56.5, "w")
    boxfan(45, 44.5, "n")
    cone(66.5, 52)
    cone(70, 63.5)
    # Two silver-and-red Razor kick scooters on the floor near the roll-up door (bklan.wmv 2484 s - 2494 s)
    for sx0, sy0, dx_ in ((67.2, 58.2, 2.0), (69.0, 59.8, 2.0)):
        box(sx0, sy0, 0.14, sx0 + dx_, sy0 + 0.35, 0.24, "bk_steel", group="illus")                 # aluminum deck
        box(sx0 - 0.12, sy0 + 0.08, 0, sx0 + 0.14, sy0 + 0.27, 0.28, "bk_redwall", group="illus")   # front red wheel
        box(sx0 + dx_ - 0.14, sy0 + 0.08, 0, sx0 + dx_ + 0.12, sy0 + 0.27, 0.28, "bk_redwall", group="illus")
        box(sx0 + 0.04, sy0 + 0.13, 0.24, sx0 + 0.16, sy0 + 0.22, 2.65, "bk_steel", group="illus")  # steering column
        box(sx0 + 0.02, sy0 - 0.35, 2.65, sx0 + 0.18, sy0 + 0.70, 2.76, "bk_steel", group="illus")  # T-bar
        box(sx0 + 0.0, sy0 - 0.45, 2.63, sx0 + 0.20, sy0 - 0.12, 2.78, "bk_redwall", group="illus") # red foam grips
        box(sx0 + 0.0, sy0 + 0.47, 2.63, sx0 + 0.20, sy0 + 0.80, 2.78, "bk_redwall", group="illus")
    model("trashcan", 62.6, 60.1, 0, "w", clip=(0.7, 2))     # the white bin full of cans (140 s)
    for cx, cy in ((62.2, 60.5), (62.9, 59.8)):
        model("soda_can", cx, cy, 1.75)
    model("extinguisher", 60.4, 37.6, 2.5 + 1 / U, "n")       # two extinguishers on the table by the box (2653 s)
    model("extinguisher", 61.3, 37.6, 2.5 + 1 / U, "n")
    model("box_large", 39.5, 59, 0, "e", clip=(1.9, 1.8))     # empty boxes by the back wall
    model("box_large", 39.3, 59.2, 1.75, "n")
    model("cord_reel", 38.2, 41, 0, "e")
    # hanging drop cords
    for cx, cy in ((46, 49), (54, 49), (46, 63), (54, 37)):
        prop(cx - .03, cy - .03, 3, cx + .03, cy + .03, H - 1.2, "bk_leg")
    joists(19 + T, 37, 36 + T, 66)
    # the painted sky wall (1952 s): the back room's north wall
    box(19 + T, 66 - 0.05, 0, 37, 66, H - 1.2, "bk_mural", {"s": Fit("bk_mural", (2, 1))})
    tube_light(28, 44, along="y", val=230)
    tube_light(28, 58, along="y", val=230)
    table(20.1, 59.0, "x", 5.83)                                                      # corner desks (explodable)
    table(20.0, 53.0, "y", 5.83)
    pc(23.0, 60.2, "s", tower=True, mon_var=3, pc_var=4, skin=1)
    pc(21.25, 55.6, "e")
    chair(23.0, 57.5, "n", "office")
    chair(24.5, 55.6, "w", "office")
    boxfan(34, 63, "s")
    prop(30, 37, 0, 36.5, 39.5, 1.5, "bk_chairbl")                                   # sleeping bag on the floor
    # Enclosed back-room corner bathroom, open white door, toilet, 2 striped cones & folded metal cot frames (2710-2714 s)
    wall("x", 44.4, 19 + T, 25.13, 0, 9.2, "bk_wall", "bk_wall", "n", thick=0.33)
    wall("y", 24.8, 36 + T, 44.4, 0, 9.2, "bk_wall", "bk_wall", "e", holes=[(40.6, 43.8, 0, 7.0)], thick=0.33)
    box(19 + T, 36 + T, 9.2, 25.13, 44.73, 9.5, "bk_trim")
    prop(22.3, 43.65, 0, 24.8, 43.8, 7.0, "bk_trim", {"n": Fit("bk_door"), "s": Fit("bk_door")})   # bathroom door open inward
    prop(19.8, 40.4, 1.3, 20.5, 42.0, 2.7, "bk_white")                                              # porcelain tank
    prop(20.5, 40.55, 0, 22.1, 41.85, 1.4, "bk_white")                                              # porcelain bowl
    prop(21.2, 39.3, 0, 21.6, 39.7, 0.42, "bk_white")                                               # toilet paper rolls (2712 s)
    prop(21.7, 39.4, 0, 22.1, 39.8, 0.42, "bk_white")
    light(22.5, 40.5, 8.2, 90, "0.96 1 0.92")
    cone(25.1, 44.9)                                                                                # 2 striped cones outside door
    cone(25.1, 46.0)
    # Folded dark-metal tubular bed/cot frames leaning flat against the cream back wall (2711 s)
    for fk, fx_ in enumerate((19.75, 20.05)):
        y0_, y1_ = 46.6 + fk * 0.2, 53.0 + fk * 0.1
        for fy_ in (y0_, y0_ + 2.1, y0_ + 4.2, y1_ - 0.15):
            prop(fx_, fy_, 0, fx_ + 0.12, fy_ + 0.14, 4.1, "bk_leg")
        for fz_ in (0.25, 1.5, 2.75, 3.95):
            prop(fx_, y0_, fz_, fx_ + 0.12, y1_, fz_ + 0.12, "bk_leg")
    prop(21.2, 50.8, 0, 22.2, 51.8, 1.15, "bk_white")                                               # small white bucket by cot
    # the door, swung into the back room
    prop(37 - 3.2, 47.4, 0, 37, 47.5, 7.2, "bk_trim", {"n": Fit("bk_door"), "s": Fit("bk_door")})

# ---------------------------------------------------------------------------------------------- the LAN lot
# Between 76 (x -143) and 45 (x -88), from the E 21st gate north to the block wall at the salvage yard (tape 64-68 s).
# 2001: pickups parked nose-in along 76's roll-ups, a pole light, the dumpster and a drum by the wall, delineators.
# 2026 (3D view / Street View): the iron gate on E 21st, a white and a blue canopy tent among the cars.
LX0, LX1 = B76[2], B45[0]
box(LX0, 187, 0, LX1, 187.67, 8, "bk_blockgr")
box(LX1, 184, 0, LX1 + T, 187.67, 8, "bk_blockgr")                                     # block wall + chain-link
box(LX0, 187.2, 8, LX1, 187.4, 14, Fit("{chain", ((LX1 - LX0) / 5.3, 6 / 5.3)), group="fence")
for fx in range(int(LX0), int(LX1) + 1, 10):
    prop(fx, 187.1, 8, fx + .25, 187.5, 14.5, "bk_steel")
box(LX0, 22.7, 0, LX0 + 14, 23, 6, Fit("{iron", (14 / 5.3, 1)), group="fence")     # E 21st gate, rolled open
box(LX1 - 16, 22.7, 0, LX1, 23, 6, Fit("{iron", (16 / 5.3, 1)), group="fence")
box(LX0 + 0.5, 23.6, 0, LX0 + 24.5, 23.9, 6, Fit("{iron", (24 / 5.3, 1)), group="fence")   # slid back behind the fixed panel
for sy in range(40, 180, 10):
    prop(LX0, sy, 0, LX0 + 15, sy + .35, 0.09, "bk_wline")
car(LX0 + 8, 45, "x", "bk_blue", 18, 6.6, pickup=True, cab_h=2.2)                 # light-blue F-150
car(LX0 + 8, 65, "x", "bk_white", 16, 6.2, pickup=True)                           # white Toyota pickup
car(LX0 + 8, 95, "x", "bk_red", 17, 6.4, pickup=True)
car(LX0 + 8, 125, "x", "bk_white", 15.5)
car(LX0 + 8, 145, "x", "bk_chairbk", 16, 6.4, cab_h=2.3)
car(-104, 50, "y", "bk_white", 15.5)
prop(LX0 + 2, 178, 0, LX0 + 8, 183, 4.5, "bk_green")                              # dumpster
model("drum", -100, 184, 0, "e", scale=1.6, clip=(1.3, 3))
# Red octagonal STOP sign & green UNION AVE -> street sign at north end of LAN lot (bklan.wmv 1325 s)
prop(-105.6, 185.6, 0, -105.4, 185.8, 7.6, "bk_steel")
prop(-106.7, 185.45, 5.4, -104.3, 185.6, 7.8, "bk_redwall", {"s": Fit("bk_stop")})
prop(-102.6, 185.6, 0, -102.4, 185.8, 8.2, "bk_steel")
prop(-104.0, 185.45, 7.3, -101.0, 185.6, 8.2, "bk_green", {"s": Fit("bk_unionsn")})
for dy in (150, 158, 180):
    cone(B45[0] - 2, dy)
prop(-116, 100, 0, -115.4, 100.6, 26, "bk_steel")                                  # pole light
prop(-117.5, 99.5, 26, -114, 101.5, 27, "bk_steel")
light(-115.7, 100.5, 25, 300)


def tent(x, y, tex, s=10):
    for cx, cy in ((x, y), (x + s, y), (x, y + s), (x + s, y + s)):
        prop(cx, cy, 0, cx + .2, cy + .2, 7.5, "bk_steel")
    prop(x, y, 7.5, x + s + .2, y + s + .2, 8, tex)


tent(-128, 105, "bk_white")
tent(-112, 70, "bk_tentblue")

# ---------------------------------------------------------------------------------------------- the salvage yard
# North of the lot's wall: TNT Automotive's yard of junk cars (the tape at 66 s; the 3D view), a tree, block walls.
box(-185, 189, 0, -96, 368, ROADZ, "bk_dirt", group="detail")
for jx, jy, c in ((-170, 205, "bk_red"), (-150, 210, "bk_blue"), (-130, 215, "bk_white"), (-170, 240, "bk_white"),
                  (-150, 245, "bk_red"), (-125, 248, "bk_blue"), (-165, 280, "bk_blue"), (-140, 300, "bk_red"),
                  (-120, 330, "bk_white"), (-170, 340, "bk_red")):
    car(jx, jy, "x" if (jx + jy) % 2 else "y", c, 15)
prop(-112, 270, 0, -110, 272, 14, "bk_pole")                                       # the tree
prop(-120, 262, 12, -102, 280, 24, "bk_green")
box(-185, 405, 0, -96, 405.3, 8, Fit("{chain", (89 / 5.3, 8 / 5.3)), group="fence")   # chain-link on Sumner
# the BODY SHOP yard and gate on Sacramento St: south half black wrought iron, north half white slatted fence (yaw270)
box(B45[2] - 0.3, 184, 0, B45[2], 206, 6.8, Fit("{iron", (22 / 5.3, 1)), group="fence")
prop(B45[2] - 0.36, 187.5, 4.4, B45[2] - 0.05, 190.5, 5.6, "bk_green", {"e": Fit("bk_unionsn")})
prop(-39.1, 206.0, 0, -38.7, 230.2, 7.2, "bk_white")                                # white slatted privacy fence (yaw270)
car(-48, 198, "x", "bk_chairbk", 18.0, 6.6, pickup=True)                            # black pickup inside gate (yaw270)
car(-27, 218, "x", "bk_btan", 18.0, 6.5, pickup=True)                               # gold/tan pickup at #74 (yaw270)

# ---------------------------------------------------------------------------------------------- the other lots
# west lot between 2 and 76, with its gate; the GCI equipment rental yard west of 2 (rev2 118 s, sv-west-110e21st)
box(-288, 22.7, 0, -270, 23, 6, Fit("{iron", (18 / 5.3, 1)), group="fence")
box(-250, 22.7, 0, -229, 23, 6, Fit("{iron", (21 / 5.3, 1)), group="fence")
for k, cy in enumerate(range(45, 180, 22)):
    car(-280, cy, "x", ("bk_white", "bk_red", "bk_chairbk", "bk_blue")[k % 4], 16)


def boom_lift(lx, ly, h_mast=18.5, col="bk_lift"):
    prop(lx - 3.6, ly - 2.1, 0, lx + 3.6, ly + 2.1, 2.8, col)
    for wx in (lx - 3.6, lx + 2.6):
        for wy in (ly - 2.6, ly + 2.1):
            prop(wx, wy, 0, wx + 1.0, wy + .55, 1.55, "bk_tire")
    prop(lx - 1.1, ly - 1.1, 2.8, lx + 1.1, ly + 1.1, 5.2, col)
    # angled boom + upper work basket rising above the fence line (rev2 118 s)
    prop(lx - 0.45, ly - 0.45, 5.2, lx + 0.45, ly + 0.45, h_mast, col)
    prop(lx - 0.35, ly - 3.2, h_mast - 2.2, lx + 0.35, ly + 0.4, h_mast - 1.3, col)
    prop(lx - 1.6, ly - 5.2, h_mast - 2.6, lx + 1.6, ly - 2.8, h_mast + 1.1, col, {"t": "bk_steel"})


for lx, ly in ((-245, 120), (-245, 150)):
    boom_lift(lx, ly, 17.5)
# GCI yard (x = -486..-336): row of white service pickups behind fence + dense fleet of blue Genie boom lifts & telehandlers
prop(-476.5, 16.5, 0, -475.6, 17.4, 28.0, "bk_steel")                               # tall silver street-light pole (118 s)
prop(-476.2, 11.0, 27.4, -475.9, 17.2, 28.0, "bk_steel")
for tx_ in range(-456, -342, 16):
    car(tx_, 37, "y", "bk_white", 17.5, 6.4, pickup=True)
for bx_ in (-480, -464):
    boom_lift(bx_, 44, 15.5, col="bk_crate")                                        # tan/ochre telehandlers at west end
for ly_, hm in ((60, 19.5), (82, 21.0), (106, 18.5), (132, 20.0)):
    for lx_ in range(-478, -338, 18):
        boom_lift(lx_, ly_, hm + ((lx_ + ly_) % 3) * 1.4, col="bk_lift")
for row, cx in enumerate((-535, -510)):
    for k, cy in enumerate(range(40, 200, 22)):
        car(cx, cy, "x", ("bk_white", "bk_red", "bk_blue", "bk_chairbk")[(row + k) % 4], 17, 6.5, pickup=bool(k % 2))
# parked along E 21st (both curbs), Sacramento and Sumner, as in Street View
for k, cx in enumerate(range(-520, 440, 34)):
    if abs(cx) < 30 or -150 < cx < -80:
        continue
    car(cx, 11, "x", ("bk_white", "bk_chairbk", "bk_red", "bk_blue", "bk_white")[k % 5], 15.5 + (k % 3), 6.3)
    if k % 2 and cx > -220:
        car(cx + 12, -17, "x", ("bk_white", "bk_blue", "bk_chairbk")[k % 3], 16, 6.3, pickup=bool(k % 4 == 1))
for k, cy in enumerate(range(50, 360, 30)):
    car(-14, cy, "y", ("bk_white", "bk_chairbk", "bk_red")[k % 3], 16, 6.3, pickup=k % 2 == 0)
for k, cx in enumerate(range(80, 440, 40)):
    car(cx, 404, "x", ("bk_white", "bk_red", "bk_chairbk")[k % 3], 16)
# east of Sacramento: the old dealership lots
for row, cx in enumerate((60, 90, 240, 270)):
    for k, cy in enumerate(range(40, 130, 18)):
        car(cx, cy, "x", ("bk_white", "bk_red", "bk_blue", "bk_chairbk")[(row + k) % 4], 16)

exec(open(os.path.join(HERE, "make_bklan_v2.py")).read())          # box B: the 2026-10-30 22:56 additions
# Pitched roofs on #7 Capri Motel (brown shingle, 118 s) and #74 Sacramento St north warehouse (tan metal, yaw270)
for part in convex_parts([tuple(p) for p in OSM["buildings"][7]["pts"]]):
    hiproof(part, 20, "bk_cpshingle", eave=1.2, pitch=4 / 12)
for part in convex_parts([tuple(p) for p in OSM["buildings"][74]["pts"]]):
    hiproof(part, 20, "bk_roof", eave=0.8, pitch=2.2 / 12)
prop(-67.2, 285.0, 24.5, -66.9, 285.3, 33.5, "bk_steel")           # roof vent/antenna pipe on #74 (yaw270)
exec(open(os.path.join(HERE, "make_bklan_orcom.py")).read())       # ORCOM CONNECT LAN PARTY merged room/building on Sonora St
exec(open(os.path.join(HERE, "make_bklan_simready.py")).read())    # SimReady yard/shop clutter (sr_<asset>.md3 from simready_props.py --all)
if os.environ.get("BKLAN_V3"):                                     # off unless asked: builds as map "bklan3" (feedback 2026-10-31 09:36)
    exec(open(os.path.join(HERE, "make_bklan_v3.py")).read())
if os.environ.get("BKLAN_V4"):                                     # off unless asked: bklan3, the review of bklan2 (2026-10-31 16:03)
    exec(open(os.path.join(HERE, "make_bklan_v4.py")).read())
if os.environ.get("BKLAN_V5"):                                     # off unless asked: bklan4, the casino + the accuracy pass (2026-10-31 night)
    exec(open(os.path.join(HERE, "make_bklan_v5.py")).read())

# ================================================================================================= gameplay
def lan(x, y):
    """old LAN-layout feet -> map feet"""
    return LAN[1] - x, LAN[2] - y


spawns = [lan(49, 42.6) + (180,), lan(59, 58.5) + (0,), lan(30, 44) + (315,), (-207, 42, 90), (-115, 60, 90),
          (-115, 140, 270), (-125, 175, 0), (-258, 80, 90), (-258, 165, 270), (-185, -5, 90), (0, -5, 180),
          (300, -5, 180), (0, 250, 270), (-300, 531, 330), (478, 200, 270), (-140, 260, 0), (-430, -8, 90),
          (150, 220, 180), (-560, 300, 90), (250, 470, 180)]
for x, y, a in spawns:
    ent("info_player_deathmatch", x, y, 2.2, angle=a)
ent("info_player_deathmatch", -60, 100, ROOF_TOP + 2.2, angle=0)                    # the roof of 45
ent("info_player_deathmatch", -667, 640, 22 + 2.2, angle=270)                       # up on the Union Ave overpass
if os.environ.get("BKLAN_START"):                         # test views: BKLAN_START="x y z angle" (feet)
    sx_, sy_, sz_, sa_ = (float(v) for v in os.environ["BKLAN_START"].split())
    ent("info_player_start", sx_, sy_, sz_, angle=int(sa_))
else:
    ent("info_player_start", -185, -10, 2.2, angle=90)    # on E 21st St, facing 118 / 120
items = [("weapon_supershotgun",) + lan(55, 42.6), ("weapon_nailgun", -115, 80), ("weapon_supernailgun", -150, 320),
         ("weapon_grenadelauncher", -258, 120), ("weapon_rocketlauncher", -60, 140, ROOF_TOP),
         ("weapon_lightning",) + lan(28, 46), ("item_armor2",) + lan(32, 52), ("item_armor1", -220, 35),
         ("item_armorInv", -662, 700, 22), ("item_health",) + lan(66, 40), ("item_health", -115, 30),
         ("item_health", 0, 150), ("item_health", -300, 520), ("item_health", 478, 100), ("item_health", -430, 5),
         ("item_shells",) + lan(43.5, 58.3), ("item_shells", -258, 100), ("item_spikes", -110, 170),
         ("item_spikes", 300, -10), ("item_rockets", -40, 60, ROOF_TOP), ("item_rockets", -470, 30),
         ("item_cells", -125, 330), ("item_cells", 200, 195)]
for it in items:
    name, x, y = it[:3]
    z = it[3] if len(it) > 3 else 0
    ent(name, x, y, z + 1)
ent("item_health", -170, 290, 1, spawnflags=2)                                      # megahealth in the salvage yard

# teleport spots for the web viewer (feet; written next to the map)
SPOTS = [("Street, facing 118 / 120", -185, -10, 2.2, 90), ("E 21st at Sacramento", 30, -40, 2.2, 135),
         ("The LAN lot gate", -115, 10, 2.2, 90), ("Unit 130A from the lot", -125, 170, 2.2, 0),
         ("LAN hall",) + lan(70, 58) + (2.2, 0), ("Back of the hall",) + lan(39.5, 43) + (2.2, 195),
         ("Drinks table",) + lan(69, 51) + (2.2, 340), ("Back room",) + lan(34, 43) + (2.2, 315),
         ("120A battery shop", -207, 42, 2.2, 70), ("Salvage yard", -140, 330, 2.2, 270),
         ("Sacramento St, BODY SHOP gate", 10, 210, 2.2, 180), ("Sumner St", -100, 440, 2.2, 0),
         ("Union Ave overpass", -667, 620, 24.2, 90), ("Roof of the LAN building", -60, 120, ROOF_TOP + 2.2, 0),
         ("Capri Motel", -430, -8, 2.2, 270), ("Sonora St", 478, 100, 2.2, 180), ("The railroad", -300, 720, 2.2, 0)]
SPOTS += V2_SPOTS
SPOTS += ORCOM_SPOTS
SPOTS += globals().get("V3_SPOTS", [])
json.dump([{"name": n, "pos": [u(x, OX), u(y, OY), u(z)], "yaw": a} for n, x, y, z, a in SPOTS],
          open(os.path.join(os.path.dirname(os.path.abspath(out)), os.path.splitext(os.path.basename(out))[0] + ".spots.json"), "w"))

# ================================================================================================= write
with open(out, "w") as f:
    f.write('{\n"classname" "worldspawn"\n"wad" "%s"\n"message" "B-LAN 2001 - E 21st St, Bakersfield"\n' % (WAD + (";" + WAD3 if globals().get("WAD3") else "")))
    f.write('"skyname" "bklan_"\n')        # DarkPlaces skybox gfx/env/bklan_{rt,bk,lf,ft,up,dn}.png (name is a prefix)
    # sun from the south-west (the front faces SW): the mangle is the way the light travels
    # warm California sunny day matching DM3 lightmap range: golden sun, neutral-warm sky dome + warm pavement bounce + radiosity
    f.write('"_minlight" "42"\n"_minlight_color" "255 245 228"\n'
            '"_sunlight" "300"\n"_sunlight_mangle" "60 -52 0"\n'
            '"_sunlight_color" "1 0.94 0.78"\n'
            '"_sunlight2" "140"\n"_sunlight2_color" "0.90 0.92 1"\n'
            '"_sunlight3" "55"\n"_sunlight3_color" "1 0.90 0.72"\n'
            '"_sunlight_penumbra" "2"\n'
            '"_bounce" "1"\n"_bouncescale" "0.75"\n'
            '"_dirt" "1"\n"_dirtscale" "0.42"\n'
            '"_sunlight_dirt" "0.4"\n"_sunlight2_dirt" "0.5"\n')
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    f.write('{\n"classname" "func_wall"\n' + "".join(GROUPS["fence"]) + "}\n")
    f.write('{\n"classname" "func_detail_illusionary"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))
if check_placed():
    sys.exit("spawns / items inside brushes")
print("wrote", out, len(GROUPS["world"]), "world +", len(GROUPS["detail"]), "detail +", len(GROUPS["fence"]),
      "fence brushes,", len(ENTS), "entities")
