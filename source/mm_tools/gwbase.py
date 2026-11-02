"""Shared base of the S Union Ave maps (goldenwest, union2, union3): exec'd by make_goldenwest.py and make_union.py.
Golden West Casino, 1001 S Union Ave (CA-99 BUS), Bakersfield, and its block, as the map "goldenwest".
Frame: feet, x east, y north (the aerials are north-up and Union Ave runs north-south), origin = the centre of the
zoom-20 aerial (ref_sources/golden_west_gallery/008.jpg, 0.3995 ft per pixel at 35.345 N). 12 units per foot.
Sources: that aerial and the zoom-19 one (006.jpg) for every footprint, Street View of May 2024 (029-044.jpg: the pylon sign,
the stone-clad frontage wall with its green iron fence, the palms on the median, the red-tile roofs). Anything the photos do
not show (the inside, the wall detail on the sides never seen from the street) is generic and is listed in the report.
Build: sh build_goldenwest.sh   -> maps/goldenwest.bsp.   Helpers come from make_bklan.py / make_bklan_v2.py (same brush code).
usage: python make_goldenwest.py out/maps/goldenwest.map"""
import ast
import json
import math
import os
import random
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "make_bklan.py"), encoding="utf-8").read()
_cut = _src.index("OSM = json.load")
exec(compile(_src[:_cut], "make_bklan_helpers", "exec"), globals())            # box, face, prism, prop, ent, light, Fit, TEXSIZE, ...
OX, OY = 0, 0
# SCALE: the aerials were read with a ground scale 1.585 too small (checked twice against OpenStreetMap: Delaware St to Union Ave 325 ft
# vs 205 read; Mariposa to Trinity Ave 308 ft vs 194; three 12.9 ft lanes instead of 12.5 ft ones). All plan positions and big plan
# extents below are in "traced feet" and are multiplied by K when the brush is written; dimensions under 4 ft (walls, posts, hedges,
# stripes) and every height keep their real size. unscaled() switches this off for objects built round an already scaled centre.
K = 1.585
_K = [K]
_box0, _prism0, _ent0 = box, prism, ent


def _sc(a, b):
    k = _K[0]
    c, h = (a + b) / 2, abs(b - a) / 2
    return c * k - (h if 2 * h < 4 else h * k), c * k + (h if 2 * h < 4 else h * k)


def box(x1, y1, z1, x2, y2, z2, tex, faces=None, group="world"):
    xa, xb = _sc(*sorted((x1, x2)))
    ya, yb = _sc(*sorted((y1, y2)))
    _box0(xa, ya, z1, xb, yb, z2, tex, faces, group)


def prism(poly, bottom, top, tex, side=None, bot=None, group="world", solid=False):
    k = _K[0]
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    fx = 1.0 if max(xs) - min(xs) < 4 else k
    fy = 1.0 if max(ys) - min(ys) < 4 else k
    _prism0([(cx * k + (x - cx) * fx, cy * k + (y - cy) * fy) for x, y in poly], bottom, top, tex, side, bot, group, solid)


def ent(classname, x, y, z, **kv):
    _ent0(classname, x * _K[0], y * _K[0], z, **kv)


class unscaled:
    def __enter__(self):
        _K[0] = 1.0

    def __exit__(self, *a):
        _K[0] = K


def S(v):
    return v * K


WAD_BK = WAD
WAD_GW = os.path.join(HERE, "out", "maps", "goldenwest.wad").replace("\\", "/")


def _grab(path, names):
    s = open(os.path.join(HERE, path), encoding="utf-8").read()
    for node in ast.parse(s).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.get_source_segment(s, node), path, "exec"), globals())


ROADZ = 1 / U
WALKZ = 0.5
_grab("make_bklan.py", {"convex_parts", "tspec", "resample", "ribbon"})
_grab("make_bklan_v2.py", {"spec", "brush", "offset_convex", "ccw", "hiproof", "pyramid", "flat_poly", "lines_x", "lines_y", "palm"})
for _w in (WAD_GW, os.path.join(HERE, "out", "maps", "bklan3.wad")):
    with open(_w, "rb") as _f:
        _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
        _f.seek(_ofs)
        for _pos, _, _, _, _, _, _name in [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]:
            _f.seek(_pos)
            _nm, _w2, _h2 = struct.unpack("<16s2I", _f.read(24))
            TEXSIZE[_name.split(b"\0")[0].decode()] = (_w2, _h2)

_seg = os.environ.get("GW_SEG", "goldenwest -520 3900").split()      # map name, then the y range of this segment (true feet, casino frame)
SEG_NAME, SEG_Y0, SEG_Y1 = _seg[0], float(_seg[1]), float(_seg[2])
OY = (SEG_Y0 + SEG_Y1) / 2                          # map origin: keeps every coordinate inside +-32768 units
HX0, HX1, HY0, HY1 = -1100.0, 1100.0, SEG_Y0, SEG_Y1
SKY_Z = 64
rng = random.Random(1001)
SPOTS = []


def poly_box(poly, z0, z1, tex, **kw):
    for part in convex_parts([tuple(p) for p in poly]):
        prism(part, z0, z1, tex, **kw)


def circle_s(cx, cy, r, n=16):
    """A circle in traced feet whose radius is also scaled (a round building)."""
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def circle(cx, cy, r, n=16):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def cone(cx, cy, r, z0, z1, tex, n=16, group="detail"):
    """A cone roof (apex at z1)."""
    cx, cy, r = cx * K, cy * K, r * K
    B = [(u(cx + r * math.cos(2 * math.pi * k / n), OX), u(cy + r * math.sin(2 * math.pi * k / n), OY)) for k in range(n)]
    Z0, Z1 = u(z0), u(z1)
    ax, ay = u(cx, OX), u(cy, OY)
    fs = [((B[0][0], B[0][1], Z0), (B[1][0], B[1][1], Z0), (B[2][0], B[2][1], Z0), (0, 0, -1), spec(tex))]
    for k in range(n):
        a, b = B[k], B[(k + 1) % n]
        fs.append(((a[0], a[1], Z0), (b[0], b[1], Z0), (ax, ay, Z1), (b[1] - a[1], -(b[0] - a[0]), 0), spec(tex)))
    brush(fs, group, solid=False)


def hip_rect(x0, y0, x1, y1, z0, tex, pitch=0.62, eave=1.8, ridge="auto", group="detail"):
    """A hip roof over a rectangle: four sloping planes meeting in a ridge (or a point). Returns the ridge height."""
    x0, x1 = _sc(x0, x1)
    y0, y1 = _sc(y0, y1)
    X0, Y0, X1, Y1 = x0 - eave, y0 - eave, x1 + eave, y1 + eave
    w, l = X1 - X0, Y1 - Y0
    along = ("y" if l >= w else "x") if ridge == "auto" else ridge
    short = min(w, l)
    rise = short / 2 * pitch
    if along == "y":
        c = (X0 + X1) / 2
        r0, r1 = (c, Y0 + short / 2), (c, Y1 - short / 2)
    else:
        c = (Y0 + Y1) / 2
        r0, r1 = (X0 + short / 2, c), (X1 - short / 2, c)
    P = lambda x, y, z: (u(x, OX), u(y, OY), u(z))
    A, B, C, D = P(X0, Y0, z0), P(X1, Y0, z0), P(X1, Y1, z0), P(X0, Y1, z0)
    R0, R1 = P(r0[0], r0[1], z0 + rise), P(r1[0], r1[1], z0 + rise)
    s = spec(tex)
    if along == "y":
        fs = [(A, B, R0, (0, -1, 0), s), (B, C, R1, (1, 0, 0), s), (C, D, R1, (0, 1, 0), s), (D, A, R0, (-1, 0, 0), s)]
        fs = [(A, B, R0, (0, -1, 0), s), (B, R0, R1, (1, 0, 0), s), (C, D, R1, (0, 1, 0), s), (D, R1, R0, (-1, 0, 0), s)]
    else:
        fs = [(A, B, R0, (0, -1, 0), s), (B, C, R1, (1, 0, 0), s), (C, D, R1, (0, 1, 0), s), (D, A, R0, (-1, 0, 0), s)]
        fs = [(A, R0, R1, (0, -1, 0), s), (B, C, R1, (1, 0, 0), s), (C, R1, R0, (0, 1, 0), s), (D, A, R0, (-1, 0, 0), s)]
    fs.append((A, B, C, (0, 0, -1), s))
    brush(fs, group, solid=False)
    return z0 + rise


def palm(x, y, h=24):
    """A fan palm (Washingtonia, as on the median in photos 037-040): tapering trunk, a ball of old fronds, 14 drooping fronds."""
    for z0, z1, r in ((0, h * 0.35, 0.65), (h * 0.35, h * 0.7, 0.52), (h * 0.7, h, 0.42)):
        prop(x - r, y - r, z0, x + r, y + r, z1, "bk_bark")
    prism(circle(x, y, 1.05, 8), h - 4.0, h - 0.2, "bk_drygrass", group="illus")                         # the skirt of dead fronds
    box(x - 0.8, y - 0.8, h - 0.6, x + 0.8, y + 0.8, h + 0.5, "bk_leaf", group="illus")
    n = 14
    for k in range(n):
        a_ = 2 * math.pi * k / n + (0.2 if k % 2 else 0)
        ln = 7.5 + (k % 3) * 0.9
        dx, dy = math.cos(a_), math.sin(a_)
        px_, py_ = -dy * 0.7, dx * 0.7
        p0 = (x + dx * 0.8, y + dy * 0.8)
        p1 = (x + dx * ln, y + dy * ln)
        poly = [(p0[0] - px_, p0[1] - py_), (p1[0] - px_ * 1.6, p1[1] - py_ * 1.6), (p1[0] + px_ * 1.6, p1[1] + py_ * 1.6), (p0[0] + px_, p0[1] + py_)]
        top = [h + 0.7, h - 1.6, h - 1.6, h + 0.7]
        prism(poly, [t - 0.18 for t in top], top, "bk_leaf", group="illus")


def gable_rect(x0, y0, x1, y1, z0, roof, end, pitch=0.9, eave=1.6, rake=0.6, group="detail"):
    """A gable roof, ridge along y, vertical timber-clad ends (the brown gable of photo 036)."""
    x0, x1 = _sc(x0, x1)
    y0, y1 = _sc(y0, y1)
    X0, X1, Y0, Y1 = x0 - eave, x1 + eave, y0 - rake, y1 + rake
    c = (X0 + X1) / 2
    rise = (X1 - X0) / 2 * pitch
    P = lambda x, y, z: (u(x, OX), u(y, OY), u(z))
    a0, a1, b0, b1 = P(X0, Y0, z0), P(X0, Y1, z0), P(X1, Y0, z0), P(X1, Y1, z0)
    r0, r1 = P(c, Y0, z0 + rise), P(c, Y1, z0 + rise)
    fs = [(a0, a1, r1, (-1, 0, 0.6), spec(roof)), (b1, b0, r0, (1, 0, 0.6), spec(roof)), (a0, r0, b0, (0, -1, 0), spec(end)),
          (a1, b1, r1, (0, 1, 0), spec(end)), (a0, b0, a1, (0, 0, -1), spec(roof))]
    brush(fs, group, solid=False)
    return z0 + rise


def extrude_x(poly_yz, x0, x1, tex, group="detail"):
    """A convex outline in the y-z plane (feet, counter-clockwise seen from +x) extruded along x; the broad faces carry `tex`
    stretched over the outline's bounds (the rounded Golden West sign body)."""
    P = [(u(y, OY), u(z)) for y, z in poly_yz]
    X0, X1 = u(x0, OX), u(x1, OX)
    lo = (X0, min(p[0] for p in P), min(p[1] for p in P))
    hi = (X1, max(p[0] for p in P), max(p[1] for p in P))
    fs = [((X1, P[0][0], P[0][1]), (X1, P[1][0], P[1][1]), (X1, P[2][0], P[2][1]), (1, 0, 0), texline(Fit(tex), "e", lo, hi)),
          ((X0, P[0][0], P[0][1]), (X0, P[1][0], P[1][1]), (X0, P[2][0], P[2][1]), (-1, 0, 0), texline(Fit(tex), "w", lo, hi))]
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        ey, ez = b[0] - a[0], b[1] - a[1]
        fs.append(((X0, a[0], a[1]), (X1, a[0], a[1]), (X0, b[0], b[1]), (0, ez, -ey), spec("gw_trim")))
    brush(fs, group, solid=False)


