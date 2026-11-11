"""make_goldenwest.py — Generates out/maps/goldenwest.map: a 1:1 scale (12 Quake units/ft)
replica of Golden West Casino (1001 S Union Ave, Bakersfield, CA 93307) and its surrounding
S Union Ave (CA-99 BUS) / E Belle Terrace / Delaware St / Adams St neighborhood.

Backward-Compatibility Hook:
- When GW_SEG is set in the environment (used by build_bklan4.sh), delegates transparently
  to make_goldenwest_legacy.py so existing composite route builds remain 100% intact.

Modular Downtown Coordinate Alignment (for future combination with fox.map & downtown):
- Scale: U = 12 Quake units per foot (+X = East, +Y = North, +Z = Up).
- Local origin (0, 0) ft = (35.345186 N, -119.0037921 W), Golden West Casino center.
- Exact offset to Historic Bakersfield Fox Theater (20th & H St, fox.map):
  FOX_OFFSET_FT = (-1683.9, 11577.8) ft.

Usage: python make_goldenwest.py [out/maps/goldenwest.map]
"""
import json
import math
import os
import runpy
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

if os.environ.get("GW_SEG"):
    runpy.run_path(os.path.join(HERE, "make_goldenwest_legacy.py"), run_name="__main__")
    sys.exit(0)

OUT_MAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "maps", "goldenwest.map")

U = 12                              # 12 Quake units = 1 foot (BakersfieldQuake 1:1 standard)
OX, OY = 0.0, 0.0                   # Origin at (35.345186, -119.0037921)
FOX_OFFSET_FT = (-1683.9, 11577.8)  # 20th & H St (Fox Theater) relative to Golden West origin (ft)

HX0, HX1 = -490.0, 650.0
HY0, HY1 = -820.0, 750.0
SKY_Z = 142.0

sys.path.insert(0, HERE)
from goldenwest_neighborhood import build_goldenwest_neighborhood  # noqa: E402

WADS = ("bklan.wad", "bklan3.wad", "gw2.wad")
TEXSIZE = {}
for _wn in WADS:
    _wp = os.path.join(HERE, "out", "maps", _wn)
    with open(_wp, "rb") as _f:
        _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
        _f.seek(_ofs)
        _dirs = [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]
        for _pos, _, _, _, _, _, _name in _dirs:
            _f.seek(_pos)
            _nm, _w, _h = struct.unpack("<16s2I", _f.read(24))
            TEXSIZE[_name.split(b"\0")[0].decode()] = (_w, _h)


def u(v, o=0.0):
    return int(round((v - o) * U))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


class Fit:
    """Stretch texture across axis-aligned brush face (with optional tile repeat)."""
    def __init__(self, name, repeat=(1.0, 1.0)):
        self.name, self.repeat = name, repeat


def tspec(name, ft_per_tile=8.0):
    w, h = TEXSIZE[name]
    sx = (ft_per_tile * U) / w
    sy = (ft_per_tile * U) / h
    return f"{name} 0 0 0 {sx:.5f} {sy:.5f}"


def spec(t):
    if isinstance(t, Fit):
        return tspec(t.name, 6.0)
    return t if isinstance(t, str) and " " in t else f"{t} 0 0 0 1 1"


def texline(sp, side, lo, hi):
    if isinstance(sp, str) and " " in sp:
        return sp
    if not isinstance(sp, Fit):
        return f"{sp} 0 0 0 1 1"
    tw, th = TEXSIZE[sp.name]
    a0, a1 = (lo[1], hi[1]) if side in "ew" else (lo[0], hi[0])
    b0, b1 = (-hi[1], -lo[1]) if side in "tb" else (-hi[2], -lo[2])
    span_a = max(1, a1 - a0)
    span_b = max(1, b1 - b0)
    xs = span_a / (tw * sp.repeat[0])
    ys = span_b / (th * sp.repeat[1])
    if side in ("w", "n"):
        xs = -xs
        xo = -a1 / xs
    else:
        xo = -a0 / xs
    yo = -b0 / ys
    return f"{sp.name} {xo:.3f} {yo:.3f} 0 {xs:.5f} {ys:.5f}"


def face(p0, p1, p2, outward, tex):
    n = cross(sub(p0, p1), sub(p2, p1))
    if n[0] * outward[0] + n[1] * outward[1] + n[2] * outward[2] < 0:
        p0, p2 = p2, p0
    pts = " ".join(f"( {p[0]} {p[1]} {p[2]} )" for p in (p0, p1, p2))
    return f"{pts} {tex}\n"


GROUPS = {"world": [], "detail": [], "fence": [], "illus": []}
ENTS = []
SOLIDS = []
PLACED = []


def brush(faces_list, group="world", solid=True):
    GROUPS[group].append("{\n" + "".join(face(a, b, c, o, t) for a, b, c, o, t in faces_list) + "}\n")
    if solid and group not in ("illus", "fence"):
        pts = [p for f in faces_list for p in f[:3]]
        SOLIDS.append(tuple(min(p[i] for p in pts) for i in range(3)) + tuple(max(p[i] for p in pts) for i in range(3)))


def box(x1, y1, z1, x2, y2, z2, tex, faces=None, group="world", solid=None):
    faces = faces or {}
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
    is_solid = (tex not in ("sky_bk", "clip") and Z2 - Z1 > 2 and group not in ("illus", "fence")) if solid is None else solid
    if is_solid:
        SOLIDS.append((X1, Y1, Z1, X2, Y2, Z2))


def prop(x1, y1, z1, x2, y2, z2, tex, faces=None):
    box(x1, y1, z1, x2, y2, z2, tex, faces=faces, group="detail")


def prism(poly, bottom, top, tex, side=None, bot=None, group="detail", solid=False):
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
    for i in range(len(P)):
        a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            Q.append(b)
    P = Q
    m = len(P)
    if m < 3 or any(q[2] <= q[3] for q in P):
        return
    area2 = sum(P[i][0] * P[(i + 1) % m][1] - P[(i + 1) % m][0] * P[i][1] for i in range(m))
    if area2 < 0:
        P.reverse()
    s_top = spec(tex)
    s_side = spec(side or tex)
    s_bot = spec(bot or side or tex)
    fs = [
        ((P[0][0], P[0][1], P[0][2]), (P[1][0], P[1][1], P[1][2]), (P[2][0], P[2][1], P[2][2]), (0, 0, 1), s_top),
        ((P[0][0], P[0][1], P[0][3]), (P[2][0], P[2][1], P[2][3]), (P[1][0], P[1][1], P[1][3]), (0, 0, -1), s_bot),
    ]
    for i in range(m):
        a, b = P[i], P[(i + 1) % m]
        out = (b[1] - a[1], -(b[0] - a[0]), 0)
        fs.append(((a[0], a[1], a[3]), (b[0], b[1], b[3]), (a[0], a[1], a[2]), out, s_side))
    brush(fs, group=group, solid=solid)


def wall(axis, at, a0, a1, z0, z1, inside, outside, out_side, holes=(), thick=0.8, group="world"):
    """Axis-aligned structural wall with clean lintel/sill/pier subdivision around doorway & window holes."""
    if axis == "x":
        c0, c1 = (at, at + thick) if out_side == "s" else (at - thick, at)
    else:
        c0, c1 = (at, at + thick) if out_side == "w" else (at - thick, at)
    in_side = {"s": "n", "n": "s", "w": "e", "e": "w"}[out_side]
    fmap = {out_side: outside, in_side: inside}
    cuts = sorted(set([a0, a1] + [x for h in holes for x in (max(a0, h[0]), min(a1, h[1])) if a0 <= x <= a1]))
    for s0, s1 in zip(cuts[:-1], cuts[1:]):
        if s1 - s0 < 0.05:
            continue
        mid = (s0 + s1) * 0.5
        active = sorted([h for h in holes if h[0] <= mid <= h[1]], key=lambda h: h[2])
        zc = z0
        for _, _, hz0, hz1 in active:
            if hz0 > zc + 0.05:
                if axis == "x":
                    box(s0, c0, zc, s1, c1, hz0, outside, fmap, group=group)
                else:
                    box(c0, s0, zc, c1, s1, hz0, outside, fmap, group=group)
            zc = max(zc, hz1)
        if z1 > zc + 0.05:
            if axis == "x":
                box(s0, c0, zc, s1, c1, z1, outside, fmap, group=group)
            else:
                box(c0, s0, zc, c1, s1, z1, outside, fmap, group=group)


def gable_roof(x0, y0, x1, y1, z0, roof_tex, end_tex, rise=7.0, eave=1.5, rake=1.0, along="y", group="detail"):
    X0, X1 = sorted((x0, x1))
    Y0, Y1 = sorted((y0, y1))
    P = lambda x, y, z: (u(x, OX), u(y, OY), u(z))
    sr, se = spec(roof_tex), spec(end_tex)
    if along == "y":
        xa, xb, ya, yb = X0 - eave, X1 + eave, Y0 - rake, Y1 + rake
        xm = (xa + xb) * 0.5
        a0, a1, b0, b1 = P(xa, ya, z0), P(xa, yb, z0), P(xb, ya, z0), P(xb, yb, z0)
        r0, r1 = P(xm, ya, z0 + rise), P(xm, yb, z0 + rise)
        fs = [
            (a0, a1, r1, (-1, 0, 0.6), sr),
            (b1, b0, r0, (1, 0, 0.6), sr),
            (a0, r0, b0, (0, -1, 0), se),
            (a1, b1, r1, (0, 1, 0), se),
            (a0, b0, a1, (0, 0, -1), sr),
        ]
    else:
        xa, xb, ya, yb = X0 - rake, X1 + rake, Y0 - eave, Y1 + eave
        ym = (ya + yb) * 0.5
        a0, a1, b0, b1 = P(xa, ya, z0), P(xb, ya, z0), P(xa, yb, z0), P(xb, yb, z0)
        r0, r1 = P(xa, ym, z0 + rise), P(xb, ym, z0 + rise)
        fs = [
            (a0, a1, r1, (0, -1, 0.6), sr),
            (b1, b0, r0, (0, 1, 0.6), sr),
            (a0, r0, b0, (-1, 0, 0), se),
            (a1, b1, r1, (1, 0, 0), se),
            (a0, a1, b0, (0, 0, -1), sr),
        ]
    brush(fs, group=group, solid=False)


def hip_roof(x0, y0, x1, y1, z0, roof_tex, rise=6.5, eave=1.6, group="detail"):
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    X0, X1, Y0, Y1 = xa - eave, xb + eave, ya - eave, yb + eave
    w, l = X1 - X0, Y1 - Y0
    P = lambda x, y, z: (u(x, OX), u(y, OY), u(z))
    A, B, C, D = P(X0, Y0, z0), P(X1, Y0, z0), P(X1, Y1, z0), P(X0, Y1, z0)
    s = spec(roof_tex)
    if l >= w:
        c = (X0 + X1) * 0.5
        inset = min(w * 0.48, l * 0.42)
        R0, R1 = P(c, Y0 + inset, z0 + rise), P(c, Y1 - inset, z0 + rise)
        fs = [
            (A, B, R0, (0, -1, 0.6), s),
            (B, C, R1, (1, 0, 0.6), s),
            (C, D, R1, (0, 1, 0.6), s),
            (D, A, R0, (-1, 0, 0.6), s),
            (A, B, C, (0, 0, -1), s),
        ]
    else:
        c = (Y0 + Y1) * 0.5
        inset = min(l * 0.48, w * 0.42)
        R0, R1 = P(X0 + inset, c, z0 + rise), P(X1 - inset, c, z0 + rise)
        fs = [
            (A, B, R0, (0, -1, 0.6), s),
            (B, C, R1, (1, 0, 0.6), s),
            (C, D, R0, (0, 1, 0.6), s),
            (D, A, R0, (-1, 0, 0.6), s),
            (A, B, C, (0, 0, -1), s),
        ]
    brush(fs, group=group, solid=False)


def cone_roof(cx, cy, r, z0, z1, tex, n=12, rot_deg=15.0, group="detail"):
    B = [
        (u(cx + r * math.cos(math.radians(rot_deg + 360.0 * k / n)), OX),
         u(cy + r * math.sin(math.radians(rot_deg + 360.0 * k / n)), OY))
        for k in range(n)
    ]
    Z0, Z1 = u(z0), u(z1)
    ax, ay = u(cx, OX), u(cy, OY)
    s = spec(tex)
    fs = [((B[0][0], B[0][1], Z0), (B[1][0], B[1][1], Z0), (B[2][0], B[2][1], Z0), (0, 0, -1), s)]
    for k in range(n):
        a, b = B[k], B[(k + 1) % n]
        fs.append(((a[0], a[1], Z0), (b[0], b[1], Z0), (ax, ay, Z1), (b[1] - a[1], -(b[0] - a[0]), 6), s))
    brush(fs, group=group, solid=False)


def ent(classname, x, y, z, **kv):
    s = f'{{\n"classname" "{classname}"\n"origin" "{u(x, OX)} {u(y, OY)} {u(z)}"\n'
    if classname.startswith(("info_player", "weapon_", "item_")):
        PLACED.append((classname, (u(x, OX), u(y, OY), u(z))))
    for k, v in kv.items():
        s += f'"{k}" "{v}"\n'
    ENTS.append(s + "}\n")


def light(x, y, z, val=220, color=None, **kv):
    if color:
        kv["_color"] = color
    ent("light", x, y, z, light=int(val), **kv)


def check_placed():
    bad = 0
    for cls, (x, y, z) in PLACED:
        if cls.startswith("info_player"):
            lo, hi = (x - 16, y - 16, z - 23), (x + 16, y + 16, z + 32)
        else:
            lo, hi = (x - 16, y - 16, z - 8), (x + 16, y + 16, z + 16)
        for b in SOLIDS:
            if all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)):
                print(f"BLOCKED {cls} at ({x}, {y}, {z}) by solid {b}")
                bad += 1
                break
    return bad


def palm(x, y, h=26.0, fronds=10):
    """Washingtonia California fan palm (photos 012, 018, 031)."""
    for z0, z1, r in ((0.0, h * 0.36, 0.62), (h * 0.36, h * 0.72, 0.50), (h * 0.72, h, 0.40)):
        prop(x - r, y - r, z0, x + r, y + r, z1, "bk_bark")
    poly_sk = [(x + 0.95 * math.cos(2 * math.pi * k / 8), y + 0.95 * math.sin(2 * math.pi * k / 8)) for k in range(8)]
    prism(poly_sk, h - 3.6, h - 0.2, "bk_drygrass", group="illus")
    for k in range(fronds):
        a = 2 * math.pi * k / fronds + (0.18 if k % 2 else 0.0)
        ln = 7.2 + (k % 3) * 0.8
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy * 0.68, dx * 0.68
        p0 = (x + dx * 0.7, y + dy * 0.7)
        p1 = (x + dx * ln, y + dy * ln)
        poly = [(p0[0] - px, p0[1] - py), (p1[0] - px * 1.5, p1[1] - py * 1.5),
                (p1[0] + px * 1.5, p1[1] + py * 1.5), (p0[0] + px, p0[1] + py)]
        top = [h + 0.7, h - 1.5, h - 1.5, h + 0.7]
        prism(poly, [t - 0.18 for t in top], top, "bk_leaf", group="illus")


def sprite_tree(x, y, height=26.0, kind="t2"):
    name, w, h = {"t1": ("{bk3_tree1", 86, 208), "t2": ("{bk3_tree2", 122, 208), "t3": ("{bk3_tree3", 109, 214)}[kind]
    wd = w * height / h
    f = Fit(name)
    box(x - wd / 2, y - 0.08, 0.4, x + wd / 2, y + 0.08, height, name, {"n": f, "s": f}, group="illus")
    box(x - 0.08, y - wd / 2, 0.4, x + 0.08, y + wd / 2, height, name, {"e": f, "w": f}, group="illus")
    prop(x - 0.42, y - 0.42, 0.0, x + 0.42, y + 0.42, min(8.0, height * 0.32), "bk_bark")


CARS = {"sedan": (17.0, 6.8, 5.3), "coupe": (16.0, 6.9, 4.3), "truck": (19.6, 8.2, 7.5), "van": (18.6, 7.7, 7.8)}


def parked(x, y, yaw, kind="sedan"):
    L, W, H = CARS[kind]
    ent("misc_model", x, y, 0.22, mdl=f"progs/veh_{kind}.md3", angles=f"0 {int(yaw)} 0", scale="1.0")
    hl, hw = (L / 2, W / 2) if yaw in (0, 180) else (W / 2, L / 2)
    box(x - hl, y - hw, 0.75, x + hl, y + hw, H, "clip", group="world")


def dash_y(x, y0, y1, tex="bk_wline", w=0.35, z=0.17, on=10.0, gap=24.0):
    y = y0
    while y + on <= y1:
        box(x - w / 2, y, z - 0.02, x + w / 2, y + on, z + 0.02, tex, group="illus")
        y += on + gap


def dash_x(y, x0, x1, tex="bk_wline", w=0.35, z=0.17, on=10.0, gap=24.0):
    x = x0
    while x + on <= x1:
        box(x, y - w / 2, z - 0.02, x + on, y + w / 2, z + 0.02, tex, group="illus")
        x += on + gap


# ==============================================================================
# 1. SEALED WORLD HULL, SKYBOX & DESERT GROUND BASE
# ==============================================================================
box(HX0 - 4.0, HY0 - 4.0, -4.0, HX1 + 4.0, HY1 + 4.0, -2.0, "bk_dirt", group="world")
box(HX0 - 4.0, HY0 - 4.0, SKY_Z, HX1 + 4.0, HY1 + 4.0, SKY_Z + 4.0, "sky_bk", group="world")
for sx0, sy0, sx1, sy1 in (
    (HX0 - 4.0, HY0 - 4.0, HX0, HY1 + 4.0),
    (HX1, HY0 - 4.0, HX1 + 4.0, HY1 + 4.0),
    (HX0, HY1, HX1, HY1 + 4.0),
    (HX0, HY0 - 4.0, HX1, HY0),
):
    box(sx0, sy0, -2.0, sx1, sy1, SKY_Z, "sky_bk", group="world")
for cx0, cy0, cx1, cy1 in (
    (HX0, HY0, HX0 + 3.0, HY1),
    (HX1 - 3.0, HY0, HX1, HY1),
    (HX0 + 3.0, HY1 - 3.0, HX1 - 3.0, HY1),
    (HX0 + 3.0, HY0, HX1 - 3.0, HY0 + 3.0),
):
    box(cx0, cy0, 0.0, cx1, cy1, SKY_Z, "clip", group="world")
# Continuous walkable Bakersfield sandy ground slab z = -2..0
box(HX0, HY0, -2.0, HX1, HY1, 0.0, tspec("gwc_dirt", 22.0), group="world")

# Build surrounding S Union Ave / E Belle Terrace / Delaware St / Adams St neighborhood
build_goldenwest_neighborhood({
    "box": box, "prop": prop, "prism": prism, "wall": wall,
    "gable_roof": gable_roof, "hip_roof": hip_roof,
    "ent": ent, "light": light, "tspec": tspec, "Fit": Fit,
    "palm": palm, "sprite_tree": sprite_tree, "parked": parked,
    "dash_y": dash_y, "dash_x": dash_x,
})


# ==============================================================================
# 2. GOLDEN WEST CASINO PARCEL PAVING, PERIMETER STONE/IRON WALL, GATES & PYLON
# ==============================================================================
STONE = tspec("gwc_stone", 6.0)
ISTONE = tspec("gwc_istone", 6.0)
SHINGLE = tspec("gwc_shingle", 6.5)
TPO = tspec("gwc_tpo", 12.0)
BEAM = tspec("gwc_beam", 4.0)
WOOD = tspec("gwc_wood", 4.0)
DADO = tspec("gwc_dado", 8.0)
WSTUC = tspec("gwc_wstucco", 8.0)
CARPET = tspec("gwc_carpet", 6.0)
TILEFLR = tspec("gwc_tileflr", 6.0)
CEIL = tspec("gwc_ceil", 6.0)
FLAG = tspec("gwc_flag", 6.0)
ASPH = tspec("gwc_asph", 14.0)
WALK = tspec("gwc_walk", 8.0)
GRASS = tspec("gwc_grass", 10.0)
PURP = tspec("gwc_purple", 6.0)
GRANITE = tspec("gwc_granite", 4.0)
LEATHER = tspec("gwc_leather", 4.0)

# Main Casino Asphalt Parking Parcel (x = -156..172, y = -274..304, GIS exact!)
box(-156.0, -274.0, 0.0, 172.0, 304.2, 0.14, ASPH, group="detail")

# S Union Ave Frontage Wall (x = 171.0): 2.0 ft cream rubble-stone base + 4.2 ft green iron fence (018, 026, 027)
# Broken at South Driveway (y = -100..-74) and North Driveway (y = +152..+178)!
for wy0, wy1 in ((-274.0, -100.0), (-74.0, 152.0), (178.0, 304.2)):
    box(170.2, wy0, 0.0, 172.0, wy1, 2.0, STONE, group="world")
    box(170.9, wy0, 2.0, 171.3, wy1, 6.2, Fit("{gwc_iron", ((wy1 - wy0) / 5.5, 1.0)), group="fence")
    box(170.6, wy0, 2.0, 171.6, wy1, 6.2, "clip", group="world")
    box(167.4, wy0 + 3.0, 0.14, 170.0, wy1 - 3.0, 2.8, tspec("bk_hedge", 6.0), group="detail")

# White rubble-stone Gate Pillars with glowing globe lamps at both Union Ave driveways (photo 026, 027)!
for gy in (-103.2, -74.0, 148.8, 178.0):
    box(169.4, gy, 0.0, 172.6, gy + 3.2, 7.4, tspec("gwc_stone", 3.5), group="world")
    prop(169.1, gy - 0.3, 7.4, 172.9, gy + 3.5, 7.9, WALK)
    prop(170.2, gy + 0.8, 7.9, 171.8, gy + 2.4, 9.5, "bk_white")
    light(171.0, gy + 1.6, 10.2, 145, "255 244 214")

# Tall Purple GOLDEN WEST CASINO Pylon Sign perpendicular to S Union Ave at (159.5, -52.0) (photos 018, 109, 118)
prop(158.0, -52.9, 0.14, 161.0, -51.1, 12.2, PURP)
# LED Tournament Readerboard ('MEMORIAL / DAY $3K / TOURNAMENT', z = 12.2..19.4, 12.5 ft wide E-W!)
prop(153.2, -53.1, 12.2, 165.8, -50.9, 19.4, PURP,
     {"n": Fit("gwc_pylled"), "s": Fit("gwc_pylled")})
# Rounded Top Gold-Script Cabinet ('Golden West CASINO', z = 19.4..28.8, 15.0 ft wide E-W!)
prop(152.0, -53.2, 19.4, 167.0, -50.8, 28.6, PURP,
     {"n": Fit("gwc_pyltop"), "s": Fit("gwc_pyltop")})
prop(153.8, -53.0, 28.6, 165.2, -51.0, 29.8, PURP)
light(159.5, -57.5, 22.0, 185, "255 224 196")
light(159.5, -46.5, 22.0, 185, "255 224 196")


# ==============================================================================
# 3. NE STAMPED-FLAGSTONE HORSE STATUE PLAZA, LAWN, FLAGS & SECURITY BOOTH
# ==============================================================================
# Stamped tan flagstone circular/courtyard plaza in NE corner (x = 43..116, y = -16..+68, photos 113, 114)
box(43.0, -16.0, 0.0, 116.0, 48.0, 0.24, FLAG, group="detail")
# Lush green turf lawn along North Wing east wall (x = 43..96, y = 32..72, photo 113, 114)
box(43.0, 32.0, 0.0, 96.0, 72.0, 0.25, GRASS, group="detail")
# Walkable flagstone path from North Wing side patio door (y = 40..47) to plaza
box(43.0, 38.0, 0.0, 68.0, 49.0, 0.26, FLAG, group="detail")

# Flush Circular Flower Bed + Bronze Rearing Horse & Cowboy Statue in NW Profile Pose at (80.0, 24.0) (photo 113)!
HCX, HCY = 80.0, 24.0
bed_outer = [(HCX + 9.2 * math.cos(2 * math.pi * k / 16), HCY + 9.2 * math.sin(2 * math.pi * k / 16)) for k in range(16)]
bed_inner = [(HCX + 8.3 * math.cos(2 * math.pi * k / 16), HCY + 8.3 * math.sin(2 * math.pi * k / 16)) for k in range(16)]
prism(bed_outer, 0.24, 0.56, tspec("gwc_brick", 4.0), side=STONE, group="detail", solid=True)
prism(bed_inner, 0.56, 0.67, tspec("gwc_mulch", 4.0), side=STONE, group="detail", solid=True)
# Decorative garden rocks & colorful flower shrubs inside circular bed (photo 113!)
for ga in (20, 85, 155, 225, 300):
    gx = HCX + 5.8 * math.cos(math.radians(ga))
    gy = HCY + 5.8 * math.sin(math.radians(ga))
    prop(gx - 0.9, gy - 0.9, 0.67, gx + 0.9, gy + 0.9, 1.38, STONE)
# Rearing Horse & Cowboy MD3 in iconic side-profile rearing right/NW (angle 132) matching photo 113!
# Origin z=0.75 ft (9 Quake units) sits 1 unit cleanly above sunlit bed_inner top (z=8 units) so DarkPlaces samples full sunlight!
ent("misc_model", HCX, HCY, 0.75, mdl="progs/gw_horse.md3", angles="0 132 0", scale="1.05")
box(HCX - 3.2, HCY - 3.2, 1.6, HCX + 3.2, HCY + 3.2, 11.5, "clip", group="world")
light(HCX + 5.0, HCY + 4.0, 6.0, 195, "255 236 198")

# Two US Flags mounted directly on the left & right eaves of the 45-degree Portico (photo 113!)
for fx, fy in ((50.2, 20.8), (68.8, 2.2)):
    prop(fx - 0.14, fy - 0.14, 11.4, fx + 0.14, fy + 0.14, 17.6, "bk_steel")
    box(fx + 0.14, fy - 0.08, 13.8, fx + 4.4, fy + 0.08, 16.8, "{gwc_usflag",
        {"n": Fit("{gwc_usflag"), "s": Fit("{gwc_usflag")}, group="illus")
# Red 'PICK NFL GAME TIME' vertical banner mounted on plaza lamp post at (90.0, 40.0) (photos 018, 113)
prop(89.8, 39.8, 0.24, 90.2, 40.2, 18.0, "bk_steel")
prop(90.0, 38.6, 8.2, 90.3, 41.4, 14.5, "bk_red", {"e": Fit("gwc_nflban"), "w": Fit("gwc_nflban")})
# Trimmed green boxwood hedges along stone base flanking the NE entrance (photo 113!)
box(43.2, 18.5, 0.25, 45.8, 36.5, 2.6, tspec("bk_hedge", 5.0), group="detail")
box(61.5, -13.5, 0.24, 65.5, -6.5, 2.6, tspec("bk_hedge", 5.0), group="detail")

# Palms & shade trees framing the NE Courtyard (photos 018, 019, 113)
for px, py, ph in ((62.0, 58.0, 22.0), (92.0, 56.0, 25.0), (108.0, -4.0, 24.0)):
    palm(px, py, h=ph, fronds=10)
sprite_tree(106.0, 38.0, 26.0, "t2")

# Parked White Security Golf Cart near NE Plaza (photos 018, 019) + North Lot Security Booth (011.jpg)
prop(98.0, 44.0, 0.24, 102.5, 51.5, 2.8, "bk_white", {"t": LEATHER})
prop(98.2, 44.2, 2.8, 102.3, 51.3, 5.8, "bk_white")   # Golf cart canopy
box(84.0, 170.0, 0.14, 92.5, 179.5, 9.2, WSTUC,
    {"e": Fit("gwc_glass"), "s": Fit("gwc_glass"), "t": TPO}, group="world")
hip_roof(84.0, 170.0, 92.5, 179.5, 9.2, SHINGLE, rise=2.6, eave=0.8)


# ==============================================================================
# 4. OUTDOOR WHITE GAMING TENT IN NORTH PARKING LOT (Photo 190.jpg!)
# ==============================================================================
# Located in north lot at x = -52..+8, y = +194..+242 (walk-through open sides, pitched white vinyl canopy)
TX0, TY0, TX1, TY1 = -52.0, 194.0, 8.0, 242.0
gable_roof(TX0, TY0, TX1, TY1, 9.8, tspec("gwc_tent", 8.0), tspec("gwc_tent", 8.0),
           rise=6.2, eave=0.6, rake=0.6, along="x")
# Tent perimeter valence skirt (z = 8.6..9.8) & steel corner/mid posts
prop(TX0, TY0, 8.6, TX1, TY0 + 0.3, 9.8, tspec("gwc_tent", 6.0))
prop(TX0, TY1 - 0.3, 8.6, TX1, TY1, 9.8, tspec("gwc_tent", 6.0))
prop(TX0, TY0, 8.6, TX0 + 0.3, TY1, 9.8, tspec("gwc_tent", 6.0))
prop(TX1 - 0.3, TY0, 8.6, TX1, TY1, 9.8, tspec("gwc_tent", 6.0))
for px in (TX0 + 0.4, -22.0, TX1 - 0.4):
    for py in (TY0 + 0.4, TY1 - 0.4):
        prop(px - 0.25, py - 0.25, 0.14, px + 0.25, py + 0.25, 9.8, "bk_steel")


def card_table(cx, cy, zf, felt_tex="gwc_fpoker", oval=True, jackpot=False, placard=False):
    """Builds a clean, non-snagging California poker or blackjack/baccarat table with chairs."""
    if oval:
        # 8.0 x 4.2 ft oval/octagonal poker table (pedestal + leather rail + gold-emblem red felt)
        prop(cx - 2.2, cy - 1.0, zf, cx + 2.2, cy + 1.0, zf + 2.45, WOOD)
        prop(cx - 4.0, cy - 2.1, zf + 2.45, cx + 4.0, cy + 2.1, zf + 2.80, LEATHER,
             {"t": Fit(felt_tex)})
        # 4 tucked low-profile chairs along N/S long sides (kept tightly within y +/- 2.85 ft for wide aisles!)
        for sx in (-2.0, 2.0):
            for sy_s in (-1, 1):
                cy_c = cy + sy_s * 2.45
                prop(cx + sx - 0.75, cy_c - 0.35, zf, cx + sx + 0.75, cy_c + 0.35, zf + 1.65, LEATHER)
        if placard:
            prop(cx - 0.9, cy - 0.1, zf + 8.6, cx + 0.9, cy + 0.1, zf + 9.9, "bk_white",
                 {"n": Fit("gwc_tblnum"), "s": Fit("gwc_tblnum")})
    else:
        # 6.8 x 3.8 ft California Blackjack / EZ Baccarat / UTH table + pole-mounted jackpot LCD!
        prop(cx - 1.8, cy - 0.9, zf, cx + 1.8, cy + 0.9, zf + 2.45, WOOD)
        prop(cx - 3.4, cy - 1.9, zf + 2.45, cx + 3.4, cy + 1.9, zf + 2.80, LEATHER,
             {"t": Fit(felt_tex)})
        for sx in (-1.8, 0.0, 1.8):
            prop(cx + sx - 0.65, cy - 2.35, zf, cx + sx + 0.65, cy - 1.85, zf + 1.65, LEATHER)
        if jackpot:
            prop(cx + 2.7, cy + 1.4, zf + 2.80, cx + 2.9, cy + 1.6, zf + 5.2, "bk_steel")
            prop(cx + 1.6, cy + 1.35, zf + 4.5, cx + 3.8, cy + 1.65, zf + 5.9, "bk_dark",
                 {"n": Fit("gwc_jackpot"), "s": Fit("gwc_jackpot")})


# 6 Outdoor Gaming Tables under the White Tent + warm golden lights & floor-lamp poles (photo 190.jpg!)
for tx in (-38.0, -22.0, -6.0):
    for ty, ft in ((206.0, "gwc_fpoker"), (228.0, "gwc_fbj")):
        card_table(tx, ty, 0.14, felt_tex=ft, oval=(ft == "gwc_fpoker"), jackpot=(ft == "gwc_fbj"))
    light(tx, 217.0, 8.8, 235, "255 218 148")
for lpx in (-30.0, -14.0):
    prop(lpx - 0.18, 216.8, 0.14, lpx + 0.18, 217.2, 8.6, "bk_dark")
    prop(lpx - 0.65, 216.4, 8.2, lpx + 0.65, 217.6, 8.8, "bk_white", {"b": Fit("gwc_troffer")})

# Parking lot striping, landscaped islands, light poles & parked cars (aerials 008, 010, 011)
for cx in (-36.0, 14.0, 68.0):
    for k in range(11):
        sy = -108.0 - k * 14.0
        box(cx - 17.5, sy - 0.15, 0.14, cx + 17.5, sy + 0.15, 0.18, "bk_wline", group="illus")
    box(cx - 0.15, -248.0, 0.14, cx + 0.15, -108.0, 0.18, "bk_wline", group="illus")
    for iy in (-102.0, -254.0):
        box(cx - 12.0, iy - 2.5, 0.14, cx + 12.0, iy + 2.5, 0.48, WALK, {"t": GRASS}, group="detail")
    prop(cx - 0.35, -102.35, 0.48, cx + 0.35, -101.65, 28.0, "bk_steel")
    light(cx, -99.5, 26.5, 190, "255 240 212")

for k in range(12):
    nx = -118.0 + k * 15.0
    box(nx - 0.15, 118.0, 0.14, nx + 0.15, 152.0, 0.18, "bk_wline", group="illus")
    box(nx - 0.15, 256.0, 0.14, nx + 0.15, 294.0, 0.18, "bk_wline", group="illus")

for px, py, pyaw, pkind in (
    (-45.0, -128.0, 0, "sedan"), (-27.0, -156.0, 180, "coupe"), (-45.0, -198.0, 0, "truck"),
    (5.0, -142.0, 0, "sedan"), (23.0, -184.0, 180, "van"), (59.0, -142.0, 0, "coupe"),
    (77.0, -198.0, 180, "sedan"), (154.0, -135.0, 90, "sedan"), (154.0, -25.0, 90, "truck"),
    (154.0, 35.0, 90, "coupe"), (154.0, 95.0, 90, "sedan"), (-96.0, 134.0, 90, "sedan"),
    (-52.0, 134.0, 90, "truck"), (28.0, 134.0, 90, "coupe"), (-82.0, 274.0, 270, "van"),
):
    parked(px, py, pyaw, pkind)


# ==============================================================================
# 5. GOLDEN WEST CASINO BUILDING — EXACT GIS FOOTPRINT, ROOFS & INTERIORS
# ==============================================================================
ZF = 0.28   # Seamless 3.4-unit step from lot/plaza!

# --- 5A. WEST FLAT-ROOF TOURNAMENT & CASHIER WING (x = -54..-20, y = -68..+76) + NORTH PENTHOUSE
box(-54.0, -68.0, 0.0, -20.0, 52.0, ZF, CARPET, group="world")
box(-54.0, 52.0, 0.0, -20.0, 76.0, ZF, TILEFLR, group="world")
box(-54.0, -68.0, 12.6, -20.0, 76.0, 15.0, CEIL, {"t": TPO}, group="world")
# North mechanical penthouse block (x = -43.5..+6.0, y = 70.5..89.2, z = 0..20.5, aerial 011.jpg!)
box(-43.5, 76.0, 0.0, 6.0, 89.2, 20.5, WSTUC, {"t": TPO}, group="world")
box(-20.0, 70.5, 0.0, 6.0, 76.0, 20.5, WSTUC, {"t": TPO}, group="world")
# West Wing Parapet (z = 15..17) + Rooftop HVAC Units & Silver Ductwork (aerial 011.jpg!)
prop(-54.4, -68.4, 15.0, -53.2, 76.4, 17.0, WSTUC)
prop(-54.4, -68.4, 15.0, -20.0, -67.2, 17.0, WSTUC)
for hx, hy in ((-44.0, -48.0), (-42.0, -14.0), (-44.0, 20.0), (-38.0, 52.0), (-28.0, 80.0)):
    hz = 20.5 if hy > 75.0 else 15.0
    prop(hx, hy, hz, hx + 6.5, hy + 5.0, hz + 3.6, "bk_beige", {"t": "bk_steel"})
prop(-37.5, -45.0, 15.0, -35.5, 54.0, 16.6, "bk_duct")

# West Wing Exterior & Interior Walls (3 Venetian-blinded West windows + West lot door, photo 166.jpg!)
wall("y", -54.0, -68.0, 76.0, ZF, 12.6, DADO, WSTUC, "w",
     holes=[(-48.0, -36.0, 3.4, 8.6), (-18.0, -6.0, 3.4, 8.6),
            (12.0, 24.0, 3.4, 8.6), (40.0, 47.0, ZF, 8.6)])
for wy0, wy1 in ((-48.0, -36.0), (-18.0, -6.0), (12.0, 24.0)):
    prop(-53.9, wy0, 3.4, -53.3, wy1, 8.6, WSTUC, {"w": Fit("gwc_glass"), "e": Fit("gwc_blind")})
# Exterior stone base course along West & South walls
prop(-54.5, -68.4, 0.0, -54.0, 39.5, 3.2, STONE)
prop(-54.5, 47.5, 0.0, -54.0, 76.4, 3.2, STONE)
wall("x", -68.0, -54.0, -20.0, ZF, 12.6, DADO, STONE, "s")
wall("x", 76.0, -54.0, -20.0, ZF, 12.6, DADO, WSTUC, "n")

# Illuminated CASHIER • CAGE at north end of West Wing (y = 74.8, photos 152, 153)
prop(-46.0, 74.2, 3.4, -28.0, 75.2, 10.6, DADO, {"s": Fit("gwc_cashier")})
prop(-47.0, 71.8, ZF, -27.0, 74.6, 3.4, WOOD, {"t": GRANITE})

# Partition Wall between West Wing and Main Poker Hall (x = -20.0): TWO 10-ft wide open portals!
wall("y", -20.0, -68.0, 70.5, ZF, 12.6, ISTONE, DADO, "w",
     holes=[(-44.0, -34.0, ZF, 9.2), (12.0, 22.0, ZF, 9.2)])
box(-20.8, -71.5, 12.6, -19.2, 70.5, 15.8, ISTONE, {"w": WSTUC}, group="world")

# West Tournament Room Tables, Glowing Troffers, TVs & Posters (photo 166.jpg)
for ty in (-54.0, -28.0, -2.0, 26.0):
    card_table(-37.5, ty, ZF, felt_tex="gwc_fpoker", oval=True, placard=True)
    prop(-40.5, ty - 2.0, 12.45, -34.5, ty + 2.0, 12.6, "bk_white", {"b": Fit("gwc_troffer")})
    light(-37.5, ty, 11.2, 265, "255 244 222")
light(-37.5, 62.0, 11.2, 265, "255 242 214")
light(-27.0, -14.0, 11.0, 200, "255 242 216")
for tvy in (-31.0, -1.0, 29.0):
    prop(-53.2, tvy - 3.2, 8.8, -52.7, tvy + 3.2, 11.8, "bk_dark", {"e": Fit("gwc_tvsport")})
for py in (-58.0, 54.0):
    prop(-21.2, py - 2.2, 4.2, -20.8, py + 2.2, 9.2, WOOD, {"w": Fit("gwc_poster1")})


# --- 5B. CENTRAL N-S GABLED MAIN POKER HALL + NORTH WING + SE WHITE STONE WING
# Floor & Ceiling Slabs covering:
#   Main Hall & North Wing: x = -20..+43, y = -71.5..+70.5
#   SE White Stone VIP Wing: x = +43..+55, y = -71.5..-48.0
#   East Turret Link & NE Diagonal Vestibule: x = +43..+60, y = -36.0..+13.0
box(-20.0, -71.5, 0.0, 43.0, 70.5, ZF, CARPET, group="world")
box(43.0, -71.5, 0.0, 55.0, -36.0, ZF, CARPET, group="world")
box(43.0, -36.0, 0.0, 59.0, -5.0, ZF, CARPET, group="world")
prism([(43.0, -5.0), (61.0, -5.0), (43.0, 13.0)], 0.0, ZF, TILEFLR, group="world", solid=True)

# Sealed Structural Ceilings above Main Hall (z = 15.6), North Wing (z = 14.2), SE Wing (z = 14.2), Link (z = 14.5)
# Overlapped up to z = 16.4 (except flat SE roof z = 15.6) with zero gaps so VIS completely isolates the interior!
box(-20.0, -71.5, 15.6, 20.0, 42.0, 16.4, CEIL, group="world")
box(20.0, -48.0, 14.5, 43.0, 13.0, 16.4, CEIL, group="world")
box(20.0, 13.0, 14.2, 43.0, 42.0, 16.4, CEIL, group="world")
box(-20.0, 42.0, 14.2, 43.0, 70.5, 16.4, CEIL, group="world")
box(20.0, -71.5, 14.2, 55.0, -48.0, 15.6, CEIL, {"t": TPO}, group="world")
box(43.0, -48.0, 14.2, 55.0, -36.0, 15.6, CEIL, {"t": TPO}, group="world")
box(43.0, -36.0, 14.5, 61.0, 13.0, 16.4, CEIL, group="world")

# Exterior Roof Masses matching Aerial 011.jpg & Entrance Photo 113.jpg!
# 1) Steep N-S Gable over Main Hall (x = -20..+20, y = -71.5..+42, dark espresso timber gable ends!)
gable_roof(-20.0, -71.5, 20.0, 42.0, 16.2, SHINGLE, BEAM, rise=11.0, eave=1.6, rake=1.2, along="y")
# 2) Steep North Wing Shingle Roof (x = -12..+43, y = 13..70.5 — tall reddish-brown slope on right of photo 113!)
hip_roof(-12.0, 13.0, 43.0, 70.5, 14.4, SHINGLE, rise=11.2, eave=1.8)
# 3) Steep East Cross-Gable with Dark-Timber Lattice Peak behind left of Portico (photo 113!) + Turret Link
gable_roof(18.0, -22.0, 58.0, 8.0, 15.6, SHINGLE, BEAM, rise=10.8, eave=1.4, rake=1.0, along="x")
hip_roof(18.0, -42.0, 62.0, -14.0, 15.4, SHINGLE, rise=7.2, eave=1.4)
# 4) SE White Stone Wing Flat TPO Parapet & Rooftop Screen (x = 20..55.5, y = -72..-48, photos 011, 026!)
prop(20.0, -72.0, 15.6, 55.6, -70.8, 17.2, STONE)
prop(54.4, -72.0, 15.6, 55.6, -36.0, 17.2, STONE)
prop(30.0, -64.0, 15.6, 46.0, -55.0, 18.4, "bk_beige", {"t": "bk_steel"})

# Main Hall South Wall (y = -71.5): South Walk-In Doorway (x = -4.5..+2.5) w/ Green-and-White Striped Awning (018.jpg)
# plus the 2 South Windows on the SE White Stone Wing (x = 26..34, 40..48, photo 026.jpg)!
wall("x", -71.5, -20.0, 20.0, ZF, 15.6, ISTONE, STONE, "s",
     holes=[(-4.5, 2.5, ZF, 8.6), (8.0, 15.0, 3.4, 8.4)])
prop(8.0, -71.4, 3.4, 15.0, -70.8, 8.4, STONE, {"s": Fit("gwc_glass"), "n": Fit("gwc_blind")})
# Green & white striped south door awning (photo 018.jpg)
prism([(-6.5, -76.5), (4.5, -76.5), (4.5, -71.5), (-6.5, -71.5)],
      [8.6, 8.6, 8.6, 8.6], [9.0, 9.0, 11.4, 11.4], Fit("gwc_awning", (2.0, 1.0)), group="detail")

wall("x", -71.5, 20.0, 55.0, ZF, 14.2, ISTONE, STONE, "s",
     holes=[(26.0, 34.0, 3.6, 8.4), (40.0, 48.0, 3.6, 8.4)])
for wx0, wx1 in ((26.0, 34.0), (40.0, 48.0)):
    prop(wx0, -71.4, 3.6, wx1, -70.8, 8.4, STONE, {"s": Fit("gwc_glass"), "n": Fit("gwc_blind")})

# SE White Stone Wing East Wall (x = 55.0, y = -71.5..-36.0)
wall("y", 55.0, -71.5, -36.0, ZF, 14.2, ISTONE, STONE, "e")

# Golden Laughing Buddha Stone Alcove at (48.0, -43.0) facing West (-X) into Main Hall (photos 165, 171)!
prop(46.0, -49.0, ZF, 54.0, -47.5, 11.0, ISTONE)
prop(46.0, -38.5, ZF, 54.0, -37.0, 11.0, ISTONE)
prop(52.5, -47.5, ZF, 54.2, -38.5, 11.0, ISTONE)
prop(45.6, -49.0, 9.6, 54.2, -37.0, 11.5, BEAM)
ent("misc_model", 50.2, -43.0, ZF, mdl="progs/gw_buddha.md3", angles="0 180 0", scale="1.08")
# Two gleaming golden offering bowls flanking the Laughing Buddha's pedestal (photo 165.jpg!)
for by_b in (-45.6, -40.4):
    prop(47.8, by_b - 0.85, ZF, 49.4, by_b + 0.85, ZF + 1.45, WOOD)
    prop(47.6, by_b - 1.05, ZF + 1.45, 49.6, by_b + 1.05, ZF + 2.35, "bk_capriylw")
box(47.6, -46.6, ZF + 0.5, 51.8, -39.4, 6.2, "clip", group="world")
light(45.5, -43.0, 8.8, 270, "255 224 148")

# North Wing North Wall (y = 70.5) & East Stone Wall facing Horse-Statue Lawn (x = 43.0, y = 13.0..70.5, photo 114!)
wall("x", 70.5, 6.0, 43.0, ZF, 14.2, ISTONE, STONE, "n",
     holes=[(16.0, 32.0, 3.6, 8.6)])
prop(16.0, 69.8, 3.6, 32.0, 70.4, 8.6, STONE, {"n": Fit("gwc_glass"), "s": Fit("gwc_blind")})

wall("y", 43.0, 13.0, 70.5, ZF, 14.2, ISTONE, STONE, "e",
     holes=[(20.0, 30.0, 3.6, 8.6), (40.0, 46.5, ZF, 8.6), (52.0, 62.0, 3.6, 8.6)])
for wy0, wy1 in ((20.0, 30.0), (52.0, 62.0)):
    prop(42.3, wy0, 3.6, 42.9, wy1, 8.6, STONE, {"e": Fit("gwc_glass"), "w": Fit("gwc_blind")})

# --- 5C. ICONIC 45-DEGREE NE GLAZED GABLE ENTRANCE PORTICO (x + y = 56.0, photos 113, 114!)
# Diagonal line runs from (43.0, 13.0) [NW] to (61.0, -5.0) [SE], facing exact NE (+1, +1) toward Horse Statue!
# Left/SE stone pier: (56.0, 0.0)..(61.0, -5.0); Right/NW stone pier: (43.0, 13.0)..(48.0, 8.0)
# Center 11.3-ft wide Grand Entrance Opening: (48.0, 8.0)..(56.0, 0.0), clear height z = ZF..8.8 ft!
prism([(42.2, 12.2), (43.0, 13.0), (48.0, 8.0), (47.2, 7.2)], ZF, 14.5, STONE, side=STONE, group="world", solid=True)
prism([(55.2, -0.8), (56.0, 0.0), (61.0, -5.0), (60.2, -5.8)], ZF, 14.5, STONE, side=STONE, group="world", solid=True)
# Lintel & Triangular Glazed Gable Wall rising from z = 8.8 to peak z = 20.8 ft!
prism([(42.4, 12.4), (43.0, 13.0), (61.0, -5.0), (60.4, -5.6)], 8.8, 14.5, Fit("gwc_glass"), side=Fit("gwc_glass"), group="world", solid=True)
# Projecting 45-degree Pitched Shingle Portico Roof + Glazed Triangular Gable Front (photos 113, 114!)
# NE direction u_ne = (1, 1), SE-NW across direction u_across: center = (52.0, 4.0)
# Projecting 8 ft NE to (60.0, 12.0)!
P_NW_IN, P_SE_IN = (42.0, 14.0), (62.0, -6.0)
P_NW_OUT, P_SE_OUT = (49.5, 21.5), (69.5, 1.5)
P_MID_IN, P_MID_OUT = (52.0, 4.0), (59.5, 11.5)
# NW roof slope & SE roof slope of 45-degree portico (z = 11.2 eaves -> z = 20.6 ridge!)
prism([P_NW_IN, P_MID_IN, P_MID_OUT, P_NW_OUT],
      [11.2, 20.2, 20.2, 11.2], [12.0, 21.0, 21.0, 12.0], SHINGLE, side=BEAM, group="detail")
prism([P_MID_IN, P_SE_IN, P_SE_OUT, P_MID_OUT],
      [20.2, 11.2, 11.2, 20.2], [21.0, 12.0, 12.0, 21.0], SHINGLE, side=BEAM, group="detail")
# Glazed triangular gable face + dark timber collar/king-post mullions on portico front!
prism([(49.0, 21.0), (69.0, 1.0), (68.5, 0.5), (48.5, 20.5)],
      [11.2, 11.2, 11.2, 11.2], [12.0, 12.0, 12.0, 12.0], BEAM, side=BEAM, group="detail")
prism([(53.5, 16.5), (64.5, 5.5), (64.1, 5.1), (53.1, 16.1)],
      [11.8, 11.8, 11.8, 11.8], [16.2, 16.2, 16.2, 16.2], Fit("gwc_glass"), side=Fit("gwc_glass"), group="detail")
prism([(56.5, 13.5), (61.5, 8.5), (61.1, 8.1), (56.1, 13.1)],
      [16.2, 16.2, 16.2, 16.2], [19.8, 19.8, 19.8, 19.8], Fit("gwc_glass"), side=Fit("gwc_glass"), group="detail")
# Stone portico support columns at outer corners (49.2, 20.8) & (68.8, 1.2) — 19.6 ft apart, wide clear plaza approach!
box(48.2, 19.6, 0.24, 50.4, 21.8, 11.2, STONE, group="world")
box(67.6, 0.2, 0.24, 69.8, 2.4, 11.2, STONE, group="world")
light(57.5, 9.5, 10.6, 235, "255 240 208")
light(47.5, 0.5, 12.2, 225, "255 240 208")

# Exposed Dark-Wood Tie Beams, King-Posts, Overhead Aisle TVs & Wainscot Dado in Main Hall (photos 167, 171)
for by in (-58.0, -38.0, -18.0, 2.0, 22.0, 42.0):
    prop(-19.5, by - 0.45, 13.4, 42.2 if by > -36.0 else 54.0, by + 0.45, 14.4, BEAM)
    if by < 38.0:
        prop(8.5, by - 0.45, 14.4, 9.5, by + 0.45, 15.6, BEAM)
# Center aisle ceiling-hung sports TV monitor box (photo 167.jpg!)
prop(6.0, -19.2, 10.4, 12.0, -16.8, 13.4, "bk_dark",
     {"n": Fit("gwc_tvsport"), "s": Fit("gwc_tvsport")})
# Cream dado + mahogany chair rail along Main Hall interior walls (167, 171) — split around South Exit Door (-4.5..+2.5)!
prop(-19.2, -70.6, ZF, -4.8, -70.2, 3.4, DADO, {"t": WOOD})
prop(2.8, -70.6, ZF, 42.2, -70.2, 3.4, DADO, {"t": WOOD})
prop(42.0, 13.5, ZF, 42.4, 39.5, 3.4, DADO, {"t": WOOD})
prop(42.0, 47.0, ZF, 42.4, 69.8, 3.4, DADO, {"t": WOOD})

# 8 Oval Red-Felt Poker Tables in Main Hall & North Wing + Host Registration Podium (photos 167, 171)
MAIN_POKER_TABLES = [
    (-4.0, -54.0), (22.0, -54.0),
    (-4.0, -28.0), (22.0, -28.0),
    (-4.0, -2.0),  (22.0, -2.0),
    (12.0, 26.0),  (12.0, 52.0),
]
for px, py in MAIN_POKER_TABLES:
    card_table(px, py, ZF, felt_tex="gwc_fpoker", oval=True, placard=True)
    cz = 15.6 if (px < 20.0 and py < 42.0) else (14.5 if (-48.0 < py < 13.0) else 14.2)
    prop(px - 3.0, py - 2.0, cz - 0.25, px + 3.0, py + 2.0, cz,
         "bk_white", {"b": Fit("gwc_troffer")})
    light(px, py, 12.6, 285, "255 242 216")
for ay in (-54.0, -28.0, -2.0, 26.0):
    light(9.0, ay, 13.0, 205, "255 240 212")

# VIP Card Table in SE Wing Alcove (35.0, -58.0) + Poker Brush / Host Desk near NE Entrance (34.0, 16.0)
card_table(36.5, -58.0, ZF, felt_tex="gwc_fbacc", oval=False, jackpot=True)
light(36.5, -56.0, 12.5, 205, "255 238 208")
prop(31.5, 12.5, ZF, 36.5, 19.5, 3.6, WOOD, {"t": GRANITE})
prop(-19.1, -16.0, 4.5, -18.7, -8.0, 9.2, WOOD, {"e": Fit("gwc_poster2")})
prop(-19.1, 28.0, 4.5, -18.7, 36.0, 9.2, WOOD, {"e": Fit("gwc_poster2")})
for tvx, tvy, tface in ((-19.1, -56.0, "e"), (41.8, 34.0, "w")):
    prop(tvx, tvy - 3.0, 9.2, tvx + 0.5, tvy + 3.0, 12.2, "bk_dark", {tface: Fit("gwc_tvsport")})


# --- 5D. EAST 12-SIDED CONICAL TURRET = THE BLACKJACK LOUNGE ROTUNDA (Photos 108, 111, 160, 169, 173!)
TCX, TCY = 79.0, -25.0
R_IN, R_OUT = 21.0, 23.0
N_TUR = 12
tur_in = [
    (TCX + R_IN * math.cos(math.radians(15.0 + 30.0 * k)),
     TCY + R_IN * math.sin(math.radians(15.0 + 30.0 * k)))
    for k in range(N_TUR)
]
tur_out = [
    (TCX + R_OUT * math.cos(math.radians(15.0 + 30.0 * k)),
     TCY + R_OUT * math.sin(math.radians(15.0 + 30.0 * k)))
    for k in range(N_TUR)
]

# Rotunda carpet floor + sealed ceiling slab + steep 12-sided conical reddish-brown shingle roof (z = 14.5..35.4 ft)!
prism(tur_out, 0.0, ZF, CARPET, side=STONE, group="world", solid=True)
prism(tur_out, 14.5, 15.6, CEIL, side=BEAM, bot=CEIL, group="world", solid=True)
cone_roof(TCX, TCY, 24.8, 14.5, 35.4, SHINGLE, n=12, rot_deg=15.0)
prop(TCX - 0.6, TCY - 0.6, 35.2, TCX + 0.6, TCY + 0.6, 38.6, "bk_steel")  # Turret roof spire finial!

# 12 Turret Facets: facets k = 4, 5, 6 (135..225 deg, facing West into Main Hall Link) form the grand open portal;
# remaining 9 facets are solid rubble-stone masonry!
for k in range(N_TUR):
    if k in (4, 5, 6):
        continue
    a_in, b_in = tur_in[k], tur_in[(k + 1) % N_TUR]
    a_out, b_out = tur_out[k], tur_out[(k + 1) % N_TUR]
    prism([a_in, b_in, b_out, a_out], ZF, 14.5, STONE, side=STONE, group="world", solid=True)
    # Interior buff-stone veneer lining
    ai2 = (TCX + (R_IN - 0.35) * math.cos(math.radians(15.0 + 30.0 * k)),
           TCY + (R_IN - 0.35) * math.sin(math.radians(15.0 + 30.0 * k)))
    bi2 = (TCX + (R_IN - 0.35) * math.cos(math.radians(15.0 + 30.0 * (k + 1))),
           TCY + (R_IN - 0.35) * math.sin(math.radians(15.0 + 30.0 * (k + 1))))
    prism([ai2, bi2, b_in, a_in], ZF, 14.5, ISTONE, side=ISTONE, group="detail")
    # Exterior dark-framed turret windows on N/NE & S/SW facets (photos 108, 111)
    if k in (1, 2, 7, 8):
        mx = (a_out[0] + b_out[0]) * 0.5
        my = (a_out[1] + b_out[1]) * 0.5
        ang = math.radians(30.0 + 30.0 * k)
        nx, ny = math.cos(ang), math.sin(ang)
        tx, ty = -ny * 3.2, nx * 3.2
        wpoly = [
            (mx - tx, my - ty), (mx + tx, my + ty),
            (mx + tx + nx * 0.35, my + ty + ny * 0.35), (mx - tx + nx * 0.35, my - ty + ny * 0.35),
        ]
        prism(wpoly, 3.6, 9.2, Fit("gwc_glass"), side=Fit("gwc_glass"), group="detail")

# Seal small wedge shoulders connecting Link (x = 43..61) cleanly to Turret facets k=3 (NW) & k=7 (SW)
box(54.5, -45.0, ZF, 63.0, -35.5, 14.5, STONE, {"w": ISTONE, "n": ISTONE}, group="world")
box(58.5, -9.5, ZF, 66.5, -3.5, 14.5, STONE, {"w": ISTONE, "s": ISTONE}, group="world")

# 12 Radial Dark-Wood Laminated Arch Ribs rising to Central Rotunda Octagon (photo 169.jpg!)
oct_hub = [
    (TCX + 6.5 * math.cos(math.radians(15.0 + 30.0 * k)),
     TCY + 6.5 * math.sin(math.radians(15.0 + 30.0 * k)))
    for k in range(N_TUR)
]
prism(oct_hub, 14.1, 14.5, CEIL, side=BEAM, bot=CEIL, group="detail")
for k in range(N_TUR):
    ang = math.radians(15.0 + 30.0 * k)
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy * 0.42, dx * 0.42
    r0 = (TCX + dx * 6.5, TCY + dy * 6.5)
    r1 = (TCX + dx * 20.5, TCY + dy * 20.5)
    prism([(r0[0] - px, r0[1] - py), (r1[0] - px, r1[1] - py),
           (r1[0] + px, r1[1] + py), (r0[0] + px, r0[1] + py)],
          [13.6, 9.8, 9.8, 13.6], [14.4, 11.2, 11.2, 14.4], BEAM, side=BEAM, group="detail")
    if k not in (4, 5, 6, 7):
        # Vertical wood pilaster column under each arch rib
        prop(r1[0] - 0.5, r1[1] - 0.5, ZF, r1[0] + 0.5, r1[1] + 0.5, 9.8, BEAM)

# --- THE BLACKJACK LOUNGE BAR along East Arc of Rotunda (x ~ 88..98, y = -36..-14, photo 169.jpg!)
# Lit Mahogany Liquor Back-Bar + Drink Specials Chalkboard + Draft Taps
prop(95.2, -33.5, ZF, 98.2, -16.5, 3.6, WOOD, {"t": GRANITE})
prop(96.0, -32.5, 3.6, 98.2, -26.5, 9.2, WOOD, {"w": Fit("gwc_barshelf")})
prop(96.4, -26.5, 4.2, 98.2, -23.5, 8.8, WOOD, {"w": Fit("gwc_chalk")})
prop(96.0, -23.5, 3.6, 98.2, -17.5, 9.2, WOOD, {"w": Fit("gwc_barshelf")})
# Iconic Glowing Cursive Blue Neon 'Blackjack' (left/north) & 'Lounge' (right/south) Signs + Flanking TVs (photo 169!)
box(95.0, -21.0, 9.6, 95.3, -13.5, 12.2, "{gwc_bjneon",
    {"w": Fit("{gwc_bjneon"), "e": Fit("{gwc_bjneon")}, group="fence")
box(95.0, -36.5, 9.6, 95.3, -29.0, 12.2, "{gwc_lgneon",
    {"w": Fit("{gwc_lgneon"), "e": Fit("{gwc_lgneon")}, group="fence")
# Flanking sports TVs tucked cleanly inside the diagonal rotunda stone wall (zero exterior poke-through!)
prop(91.6, -15.2, 6.4, 92.2, -10.8, 9.0, "bk_dark", {"w": Fit("gwc_tvsport")})
prop(91.6, -39.2, 6.4, 92.2, -34.8, 9.0, "bk_dark", {"w": Fit("gwc_tvsport")})

# Faceted Black Granite Bar Counter + 6 Black Leather Bar Stools (photo 169.jpg)
prop(89.5, -34.0, ZF, 92.2, -16.0, 3.65, WOOD, {"t": GRANITE})
prop(89.5, -34.0, ZF, 95.2, -32.0, 3.65, WOOD, {"t": GRANITE})
prop(89.5, -18.0, ZF, 95.2, -16.0, 3.65, WOOD, {"t": GRANITE})
for sy in (-32.2, -29.2, -26.2, -23.2, -20.2, -17.2):
    prop(87.6, sy - 0.18, ZF, 88.0, sy + 0.18, 2.35, "bk_steel")
    prop(87.1, sy - 0.65, 2.35, 88.5, sy + 0.65, 2.70, LEATHER)

# 4 California Table-Game Tables in Blackjack Lounge Rotunda + Pit Boss Podium (photos 160, 169, 173)
card_table(68.0, -16.0, ZF, felt_tex="gwc_fbj", oval=False, jackpot=True)
card_table(68.0, -34.0, ZF, felt_tex="gwc_fbj", oval=False, jackpot=True)
card_table(79.5, -14.5, ZF, felt_tex="gwc_fbacc", oval=False, jackpot=True)
card_table(79.5, -35.5, ZF, felt_tex="gwc_futh", oval=False, jackpot=True)
# Wooden Pit Podium at center-west of Rotunda (photo 169.jpg)
prop(73.2, -26.2, ZF, 75.4, -23.8, 3.8, WOOD, {"t": GRANITE})

light(TCX, TCY, 13.0, 210, "255 240 212")
light(87.0, -25.0, 9.6, 205, "255 236 204")
light(93.0, -25.0, 11.2, 195, "195 225 255")
light(66.0, -25.0, 12.5, 215, "255 238 208")


# ==============================================================================
# 6. PLAYER SPAWNS, DEATHMATCH ITEMS & AUDIT / BROWSER CAMERA SPOTS
# ==============================================================================
if os.environ.get("GW_START"):
    _vals = [float(v) for v in os.environ["GW_START"].split()]
    if len(_vals) >= 5:
        ent("info_player_start", _vals[0], _vals[1], _vals[2], angles=f"{_vals[4]:.1f} {_vals[3]:.1f} 0")
    else:
        ent("info_player_start", _vals[0], _vals[1], _vals[2], angle=int(_vals[3]))
else:
    # Default spawn: NE Flagstone Plaza looking SW across the Bronze Horse Statue into the Glazed Gable Entrance!
    ent("info_player_start", 104.0, 36.0, 2.8, angle=215)

DM_SPAWNS = [
    (104.0, 36.0, 2.8, 215),        # NE Horse Statue Plaza facing Glazed Gable Entrance
    (194.0, -20.0, 2.8, 195),       # S Union Ave facing Casino Turret & Purple Pylon Sign
    (79.0, -25.0, 2.8, 0),          # Inside Blackjack Lounge Rotunda facing Neon Bar
    (9.0, -15.0, 2.8, 90),          # Inside Main Timber-Beamed Poker Hall
    (-37.5, 12.0, 2.8, 90),         # Inside West Tournament Room facing Cashier Cage
    (-22.0, 217.0, 2.8, 180),       # Inside Outdoor White Gaming Tent (North Lot)
    (227.5, 515.0, 3.0, 90),        # S Union Ave Brick Median approaching E Belle Terrace signals
    (124.0, 636.0, 2.8, 180),       # Inside Carnitas Birria Menudo Diner
    (318.0, 66.0, 2.8, 90),         # Inside Star-Liter Motor Motel Office
    (-62.0, -308.0, 2.8, 0),        # Inside Ramos Tires & Service Bay
    (320.0, -634.0, 2.8, 0),        # Inside Playfair Market Convenience Store
    (92.0, -606.0, 2.8, 180),       # Inside Super 8 by Wyndham Lobby
]
for sx, sy, sz, sang in DM_SPAWNS:
    ent("info_player_deathmatch", sx, sy, sz, angle=sang)

ITEMS = [
    ("weapon_rocketlauncher", 81.0, -25.0, 2.0),        # Center of Blackjack Lounge Rotunda
    ("weapon_lightning", 9.0, -42.0, 2.0),              # Main Poker Hall in front of Golden Buddha
    ("weapon_supernailgun", -37.5, 60.0, 2.0),          # In front of Cashier Cage
    ("weapon_grenadelauncher", -22.0, 217.0, 1.8),      # Outdoor White Gaming Tent
    ("weapon_supershotgun", -62.0, -316.0, 1.8),        # Ramos Tires Service Bay
    ("weapon_nailgun", 322.0, -638.0, 1.8),             # Playfair Market
    ("item_armorInv", 66.0, 10.0, 2.0),                 # Red Armor at NE Plaza Portico
    ("item_armor2", 96.0, -606.0, 1.8),                 # Yellow Armor in Super 8 Lobby
    ("item_armor1", 126.0, 636.0, 1.8),                 # Green Armor in Carnitas Birria Menudo
    ("item_health", 9.0, 12.0, 1.8),
    ("item_health", 62.0, -25.0, 1.8),
    ("item_rockets", 84.0, -20.0, 1.8),
    ("item_cells", 9.0, -36.0, 1.8),
    ("item_spikes", -37.5, 44.0, 1.8),
]
for iname, ix, iy, iz in ITEMS:
    ent(iname, ix, iy, iz)

# Named Audit & Browser-Viewer Jump-To Spots matching key Reference Gallery Photos!
SPOTS = [
    ("01 NE Horse Statue & Glazed Gable Entrance (113)", 98.0, 38.0, 4.4, 222, -4),
    ("02 S Union Ave -> Casino Turret & Wall (018)", 202.0, -8.0, 4.4, 198, -3),
    ("03 Purple Golden West Pylon Sign (109/118)", 192.0, -76.0, 4.4, 132, -12),
    ("04 South Gate Pillars & SE Stone Wing (026)", 194.0, -96.0, 4.4, 162, -3),
    ("05 Turret Conical Roof & Stone Facets (108/111)", 122.0, -34.0, 4.4, 166, -10),
    ("06 Blackjack Lounge Rotunda & Neon Bar (169)", 64.0, -25.0, 4.4, 0, -2),
    ("07 Rotunda Card Pit & Jackpot Screens (160/173)", 84.5, -25.0, 4.4, 180, 4),
    ("08 Main Timber-Beamed Poker Hall (167)", 9.0, 24.0, 4.4, 270, -2),
    ("09 Golden Laughing Buddha Stone Alcove (165/171)", 36.0, -43.0, 4.4, 0, -2),
    ("10 West Tournament Room & Cashier Cage (152/166)", -37.5, -14.0, 4.4, 90, -2),
    ("11 Outdoor White Gaming Tent North Lot (190)", -22.0, 184.0, 4.4, 90, -2),
    ("12 S Union Ave Brick Median & Star-Liter Motel (012/086)", 227.5, 45.0, 4.6, 58, -3),
    ("13 E Belle Terrace Signals & Carnitas Menudo (033)", 212.0, 606.0, 4.6, 205, -3),
    ("14 Ramos Tires & Best DEAL Auto Lot (065/066)", 58.0, -356.0, 4.4, 152, -3),
    ("15 Playfair Market Storefront Mural & Adams St (046)", 256.0, -622.0, 4.4, 345, -3),
    ("16 Super 8 by Wyndham Hotel & Pylon (050)", 196.0, -648.0, 4.4, 178, -5),
    ("17 Country Inn Motel Courtyard (063)", 265.0, -456.0, 4.4, 8, -3),
    ("18 Trinity Ave & Delaware St Ranch Houses (076)", -122.0, -146.0, 4.4, 185, -2),
]

os.makedirs(os.path.dirname(os.path.abspath(OUT_MAP)), exist_ok=True)
spots_path = os.path.splitext(os.path.abspath(OUT_MAP))[0] + ".spots.json"
with open(spots_path, "w", encoding="utf-8") as sf:
    json.dump(
        [{"name": s[0], "pos": [u(s[1], OX), u(s[2], OY), u(s[3])], "yaw": s[4], "pitch": s[5]}
         for s in SPOTS],
        sf, indent=2,
    )

wad_str = ";".join(WADS)
with open(OUT_MAP, "w", encoding="utf-8") as f:
    f.write('{\n"classname" "worldspawn"\n')
    f.write(f'"wad" "{wad_str}"\n')
    f.write('"message" "Golden West Casino (1001 S Union Ave) - Bakersfield, CA"\n')
    f.write('"skyname" "bklan_"\n')
    # Bright sunny Bakersfield day: direct warm sun from high ENE (mangle 212 -58 0) illuminates
    # the NE Horse-Statue Plaza, 45-deg Glazed Gable Entrance, Conical Turret, Union Ave frontage,
    # and E Belle Terrace, while sky-dome _sunlight2 178 fills west/south streets cleanly!
    f.write(
        '"_minlight" "34"\n'
        '"_sunlight" "215"\n'
        '"_sunlight_mangle" "212 -58 0"\n'
        '"_sunlight_color" "1 0.96 0.87"\n'
        '"_sunlight2" "178"\n'
        '"_sunlight2_color" "0.78 0.88 1"\n'
        '"_sunlight_penumbra" "2.5"\n'
        '"_dirt" "1"\n'
        '"_dirtscale" "0.38"\n'
    )
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    if GROUPS["detail"]:
        f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    if GROUPS["fence"]:
        f.write('{\n"classname" "func_wall"\n"_shadow" "0"\n"_minlight" "80"\n' + "".join(GROUPS["fence"]) + "}\n")
    if GROUPS["illus"]:
        f.write('{\n"classname" "func_detail_illusionary"\n"_shadow" "0"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))

if check_placed():
    sys.exit("ERROR: spawns or items blocked by solid brushes!")

print(
    f"wrote {OUT_MAP}: {len(GROUPS['world'])} world + {len(GROUPS['detail'])} detail + "
    f"{len(GROUPS['fence'])} fence + {len(GROUPS['illus'])} illus brushes, {len(ENTS)} entities"
)
