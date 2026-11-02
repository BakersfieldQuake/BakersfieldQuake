"""make_fox.py — Generates out/maps/fox.map: a 1:1 scale (12 Quake units/ft) architectural replica
of The Historic Bakersfield Fox Theater (2001 H Street, corner of 20th Street & H Street, Bakersfield, CA).

Sources integrated:
- Bakersfield City GIS / OpenStreetMap Way 59516616 & intersection geometry (20th St, H St, West Alley,
  Today Cleaners 2027 H St drive-thru, DB & Co, downtown commercial context).
- Exterior photography (SoCal Landmarks / John Bare 2022 & bakersfieldlive.com): Spanish Colonial Revival
  cream stucco, Churrigueresque terracotta reliefs & 5 east parapet finials, 20th St 3-story gable with
  3 terracotta finials + chimney + curved rooftop HVAC duct, H St 5-bay Spanish tile storefronts, bronze
  'HOPE' street post clock, palms, Walk of Stars plaques, 1953 wrap-around 'Fox' neon marquee ('DANCE NATION /
  JUNE 10 & 11'), island Ticket Booth, rainbow terrazzo vestibule, 116-ft Clock Tower with 3D 'FOX' letters,
  4 navy-blue clocks, ribbed silver-blue dome & bronze spire finial.
- Official 2026 Production Pack PDF & Seating Chart (bakersfieldlive.com): 48'x27' proscenium, 27'x48' stage,
  60' fly grid, 11'6"x42'x4' curved orchestra pit, 40' FOH truss 16' DS, balcony rail 77'4" DS with 18 Leko
  ports, Touring FOH mix booth 90' DS, 3 orchestra seating sections + 2 balcony tiers + vomitoria + projection
  booth, Stage Left Green Room (guitars), Upstairs Dressing Rooms (Hollywood vanities), 8'x13'6" alley load-in
  door, Lobby sloping stenciled concrete raker beams, 1953 Skouras concession stand, California tapestry, and
  Eva's East Lobby Lounge.

Usage: python make_fox.py out/maps/fox.map
"""
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MAP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "maps", "fox.map")

U = 12                  # 12 Quake units per foot (BakersfieldQuake standard)
OX, OY = 220.0, -118.0  # Shift expanded 1:1 neighborhood center near (0, 0) in Quake units
CL = -54.0              # Auditorium & Stage centerline (x = -94 .. -14 -> width 80 ft, center -54)

sys.path.insert(0, HERE)
from fox_neighborhood import build_neighborhood  # noqa: E402
from padre_hotel import PADRE_SUB_X0, PADRE_SUB_X1, PADRE_SUB_Y0, PADRE_SUB_Y1  # noqa: E402

WADS = ("bklan.wad", "bklan3.wad", "goldenwest.wad", "fox.wad")
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
    """Stretch texture over brush face (with optional repeat count)."""
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


def brush(faces, group="world", solid=True):
    GROUPS[group].append("{\n" + "".join(face(a, b, c, o, t) for a, b, c, o, t in faces) + "}\n")
    if solid and group != "illus":
        pts = [p for f in faces for p in f[:3]]
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
    is_solid = (tex not in ("sky_bk", "clip") and Z2 - Z1 > 2 and group != "illus") if solid is None else solid
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
    area = sum(P[i][0] * P[(i + 1) % m][1] - P[(i + 1) % m][0] * P[i][1] for i in range(m))
    if abs(area) < 8:
        return
    if area < 0:
        P.reverse()
    s = "{\n"
    for i in range(m):
        a, b = P[i], P[(i + 1) % m]
        s += face((a[0], a[1], a[3]), (b[0], b[1], b[3]), (a[0], a[1], a[3] + 64),
                  (b[1] - a[1], -(b[0] - a[0]), 0), spec(side or tex))
    i1, i2 = max(1, m // 3), max(2, (2 * m) // 3)
    if i2 == i1:
        i2 = i1 + 1
    s += face((P[0][0], P[0][1], P[0][2]), (P[i1][0], P[i1][1], P[i1][2]), (P[i2][0], P[i2][1], P[i2][2]),
              (0, 0, 1), spec(tex))
    s += face((P[0][0], P[0][1], P[0][3]), (P[i1][0], P[i1][1], P[i1][3]), (P[i2][0], P[i2][1], P[i2][3]),
              (0, 0, -1), spec(bot or side or tex))
    GROUPS[group].append(s + "}\n")
    if solid and group != "illus":
        xs, ys = [q[0] for q in P], [q[1] for q in P]
        SOLIDS.append((min(xs), min(ys), min(q[3] for q in P), max(xs), max(ys), max(q[2] for q in P)))


def frustum_ring(cx, cy, r0, r1, z0, z1, tex, sides=16, group="detail"):
    """Convex frustum ring (for smooth curved cupola dome & urn finials)."""
    CX, CY = u(cx, OX), u(cy, OY)
    Z0, Z1 = u(z0), u(z1)
    B0 = [(int(round(CX + r0 * U * math.cos(2 * math.pi * k / sides))),
           int(round(CY + r0 * U * math.sin(2 * math.pi * k / sides))), Z0) for k in range(sides)]
    B1 = [(int(round(CX + r1 * U * math.cos(2 * math.pi * k / sides))),
           int(round(CY + r1 * U * math.sin(2 * math.pi * k / sides))), Z1) for k in range(sides)]
    fs = [
        (B0[0], B0[sides // 3], B0[2 * sides // 3], (0, 0, -1), spec(tex)),
        (B1[0], B1[sides // 3], B1[2 * sides // 3], (0, 0, 1), spec(tex)),
    ]
    for k in range(sides):
        a0, b0 = B0[k], B0[(k + 1) % sides]
        a1 = B1[k]
        ang = 2 * math.pi * (k + 0.5) / sides
        fs.append((a0, b0, a1, (math.cos(ang), math.sin(ang), 0.25), spec(tex)))
    brush(fs, group=group, solid=False)


def circle_poly(cx, cy, r, n=12, rot=0.0):
    return [(cx + r * math.cos(2 * math.pi * k / n + rot), cy + r * math.sin(2 * math.pi * k / n + rot)) for k in range(n)]


def wall_x(x0, x1, y, th, z0, z1, tex, faces=None, holes=(), group="world"):
    """Wall along X (y .. y+th) with rectangular doorway/window openings (xa, xb, zbot, ztop)."""
    cur = x0
    for xa, xb, zb, zt in sorted(holes):
        if xa > cur:
            box(cur, y, z0, xa, y + th, z1, tex, faces, group=group)
        if zb > z0:
            box(xa, y, z0, xb, y + th, zb, tex, faces, group=group)
        if z1 > zt:
            box(xa, y, zt, xb, y + th, z1, tex, faces, group=group)
        cur = xb
    if x1 > cur:
        box(cur, y, z0, x1, y + th, z1, tex, faces, group=group)


def wall_y(x, th, y0, y1, z0, z1, tex, faces=None, holes=(), group="world"):
    """Wall along Y (x .. x+th) with rectangular doorway/window openings (ya, yb, zbot, ztop)."""
    cur = y0
    for ya, yb, zb, zt in sorted(holes):
        if ya > cur:
            box(x, cur, z0, x + th, ya, z1, tex, faces, group=group)
        if zb > z0:
            box(x, ya, z0, x + th, yb, zb, tex, faces, group=group)
        if z1 > zt:
            box(x, ya, zt, x + th, yb, z1, tex, faces, group=group)
        cur = yb
    if y1 > cur:
        box(x, cur, z0, x + th, y1, z1, tex, faces, group=group)


def ent(classname, x, y, z, **kv):
    X, Y, Z = u(x, OX), u(y, OY), u(z)
    if classname.startswith(("info_player", "weapon_", "item_")):
        PLACED.append((classname, (X, Y, Z)))
    lines = [f'"classname" "{classname}"', f'"origin" "{X} {Y} {Z}"']
    for k, v in kv.items():
        lines.append(f'"{k}" "{v}"')
    ENTS.append("{\n" + "\n".join(lines) + "\n}\n")


def light(x, y, z, val=200, color="255 240 212", **kv):
    ent("light", x, y, z, light=val, _color=color, **kv)


def fox_model(name, x, y, z, yaw=0, z_off=0.08, clip_box=None):
    """Place a smooth-shaded custom MD3 prop (with positive yaw 0..359 and optional player-clip bounds)."""
    yaw_i = int(round(yaw)) % 360
    ent("misc_model", x, y, z + z_off, mdl=f"progs/fox/{name}.md3", angles=f"0 {yaw_i} 0")
    if clip_box is not None:
        box(*clip_box, "clip", solid=True)


def brush_ent(classname, x1, y1, z1, x2, y2, z2, tex="bk_dirt", **kv):
    X1, X2 = sorted((u(x1, OX), u(x2, OX)))
    Y1, Y2 = sorted((u(y1, OY), u(y2, OY)))
    Z1, Z2 = sorted((u(z1), u(z2)))
    s = "{\n" + f'"classname" "{classname}"\n'
    for k, v in kv.items():
        s += f'"{k}" "{v}"\n'
    s += "{\n"
    s += face((X1, Y1, Z1), (X1, Y2, Z1), (X1, Y1, Z2), (-1, 0, 0), spec(tex))
    s += face((X2, Y1, Z1), (X2, Y1, Z2), (X2, Y2, Z1), (1, 0, 0), spec(tex))
    s += face((X1, Y1, Z1), (X1, Y1, Z2), (X2, Y1, Z1), (0, -1, 0), spec(tex))
    s += face((X1, Y2, Z1), (X2, Y2, Z1), (X1, Y2, Z2), (0, 1, 0), spec(tex))
    s += face((X1, Y1, Z1), (X2, Y1, Z1), (X1, Y2, Z1), (0, 0, -1), spec(tex))
    s += face((X1, Y1, Z2), (X1, Y2, Z2), (X2, Y1, Z2), (0, 0, 1), spec(tex))
    s += "}\n}\n"
    ENTS.append(s)


def check_placed():
    bad = 0
    for cls, (x, y, z) in PLACED:
        if cls.startswith("info_player"):
            lo, hi = (x - 16, y - 16, z - 23), (x + 16, y + 16, z + 32)
        else:
            lo, hi = (x - 16, y - 16, z - 8), (x + 16, y + 16, z + 16)
        for b in SOLIDS:
            if all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)):
                print(f"BLOCKED {cls} at ({x}, {y}, {z}) by brush {b}")
                bad += 1
                break
    return bad


STUCCO = tspec("fx_stucco", 12)
STUCCO_DK = tspec("fx_stucco_dk", 10)
TERRA = tspec("fx_terra", 6)
PEACH = tspec("fx_peach", 6)
TILE = tspec("fx_tile", 6)
CARPET = tspec("fx_lobcarp", 4.2)
TERRAZZO = tspec("fx_terrazzo", 5.5)
LOBWALL = tspec("fx_lobwall", 10)
LOBCEIL = tspec("fx_lobceil", 16)

# ============================================================================== 1. SEALED WORLD HULL & 1:1 NEIGHBORHOOD
HX0, HX1, HY0, HY1, SKY_Z = -424.0, 1240.0, -830.0, 422.0, 210.0
SUB_Z = -13.0
ROAD_TILE = tspec("bk_road", 16)
ASPH_TILE = tspec("bk_asphalt", 16)

# Outer sky box & base sub-slab (with void-free sub-base at z = -15..-13 under both Fox Pit and Padre Basement Gym!)
box(HX0 - 2, HY0 - 2, -15.0, HX1 + 2, HY1 + 2, SUB_Z, ASPH_TILE)
box(HX0 - 2, HY0 - 2, SKY_Z, HX1 + 2, HY1 + 2, SKY_Z + 2, "sky_bk")
box(HX0 - 2, HY0 - 2, SUB_Z, HX0, HY1 + 2, SKY_Z, "sky_bk")
box(HX1, HY0 - 2, SUB_Z, HX1 + 2, HY1 + 2, SKY_Z, "sky_bk")
box(HX0, HY0 - 2, SUB_Z, HX1, HY0, SKY_Z, "sky_bk")
box(HX0, HY1, SUB_Z, HX1, HY1 + 2, SKY_Z, "sky_bk")
for cx0, cy0, cx1, cy1 in ((HX0, HY0, HX0 + 3, HY1), (HX1 - 3, HY0, HX1, HY1), (HX0, HY0, HX1, HY0 + 3), (HX0, HY1 - 3, HX1, HY1)):
    box(cx0, cy0, 0, cx1, cy1, SKY_Z, "clip")

# North half ground slab (y = -200..HY1, z = SUB_Z..0) around recessed Fox Orchestra Pit (-75..-33, 136.5..148)
PIT_X0, PIT_X1, PIT_Y0, PIT_Y1 = -75.0, -33.0, 136.5, 148.0
SPLIT_Y = -200.0
box(HX0, SPLIT_Y, SUB_Z, HX1, PIT_Y0, 0.0, ROAD_TILE)
box(HX0, PIT_Y1, SUB_Z, HX1, HY1, 0.0, ROAD_TILE)
box(HX0, PIT_Y0, SUB_Z, PIT_X0, PIT_Y1, 0.0, ROAD_TILE)
box(PIT_X1, PIT_Y0, SUB_Z, HX1, PIT_Y1, 0.0, ROAD_TILE)
box(PIT_X0, PIT_Y0, SUB_Z, PIT_X1, PIT_Y1, -3.5, "fx_stageflr")     # Orchestra pit floor at z = -3.5 ft

# South half ground slab (y = HY0..-200, z = SUB_Z..0) around Padre Hotel Basement Gym (-52..-4, -658..-604)
box(HX0, HY0, SUB_Z, HX1, PADRE_SUB_Y0, 0.0, ROAD_TILE)
box(HX0, PADRE_SUB_Y1, SUB_Z, HX1, SPLIT_Y, 0.0, ROAD_TILE)
box(HX0, PADRE_SUB_Y0, SUB_Z, PADRE_SUB_X0, PADRE_SUB_Y1, 0.0, ROAD_TILE)
box(PADRE_SUB_X1, PADRE_SUB_Y0, SUB_Z, HX1, PADRE_SUB_Y1, 0.0, ROAD_TILE)
box(PADRE_SUB_X0, PADRE_SUB_Y0, SUB_Z, PADRE_SUB_X1, PADRE_SUB_Y1, -11.5, "bk_white")


# ============================================================================== 2. STREET FURNITURE HELPERS & NEIGHBORHOOD
def fan_palm(x, y, h=26.0):
    """California fan palm (Washingtonia filifera) smooth-shaded MD3 prop with ringed trunk, shag skirt & arched fronds."""
    mdl_name = "fox_palm" if h >= 19.0 else "fox_palm_sm"
    z_base = 0.72 if (abs(x + 10.0) < 0.5 and abs(y - 270.0) < 0.5) else 0.52
    yaw = int(abs(x * 37.0 + y * 53.0)) % 360
    fox_model(mdl_name, x, y, z_base, yaw=yaw, z_off=0.06,
              clip_box=(x - 0.52, y - 0.52, z_base + 0.35, x + 0.52, y + 0.52, min(h - 3.0, 16.0)))


def double_globe_lamp(x, y, along="x"):
    """Downtown Bakersfield vintage twin-acorn ornamental cast-iron streetlamp MD3 prop."""
    yaw = 90 if along == "x" else 0
    fox_model("fox_streetlamp", x, y, 0.52, yaw=yaw, z_off=0.06,
              clip_box=(x - 0.35, y - 0.35, 0.85, x + 0.35, y + 0.35, 12.0))
    light(x, y, 14.5, 135, "255 236 196")


# Build the complete 1:1 surrounding Downtown Bakersfield neighborhood (G St -> Chester Ave, Wall St -> 21st St)!
build_neighborhood({
    "box": box, "prop": prop, "prism": prism, "frustum_ring": frustum_ring, "circle_poly": circle_poly,
    "wall_x": wall_x, "wall_y": wall_y, "ent": ent, "light": light, "brush_ent": brush_ent,
    "tspec": tspec, "Fit": Fit, "fan_palm": fan_palm, "double_globe_lamp": double_globe_lamp,
    "fox_model": fox_model,
})

# Bakersfield Fox "Walk of Stars" plaques & green-diamond sidewalk terrazzo apron around the Fox!
box(-26.0, -10.0, 0.5, 11.0, 0.0, 0.54, TERRAZZO, group="illus")
box(0.0, 0.0, 0.5, 11.0, 154.0, 0.54, TERRAZZO, group="illus")
for sx in (-36, -52, -68, -84):
    box(sx - 1.5, -9.5, 0.54, sx + 1.5, -6.5, 0.58, Fit("fx_walkstar"), group="illus")
for sy in (34, 58, 82, 106, 130):
    box(6.5, sy - 1.5, 0.54, 9.5, sy + 1.5, 0.58, Fit("fx_walkstar"), group="illus")

# Palms & twin-globe streetlamps directly bordering the Fox Theater (gal_018..024, gal_042)
for px, py, ph in ((-42, -9.5, 29), (-58, -11.0, 23), (-75, -10.0, 22), (-92, -10.5, 21),
                   (12.0, 84.0, 27), (12.0, 140.0, 25)):
    fan_palm(px, py, ph)
for lx in (-31, -67, -99):
    double_globe_lamp(lx, -13.5, "x")
for ly in (46, 98, 152, 192):
    double_globe_lamp(13.5, ly, "y")
# Historic 4-dial bronze 'HOPE' street clock outside the Fox Theater on 20th St (gal_019/042.jpg)!
fox_model("fox_clockpost", -46.5, -11.5, 0.52, yaw=0, z_off=0.06,
          clip_box=(-47.4, -12.4, 0.85, -45.6, -10.6, 13.5))
light(-46.5, -11.5, 16.5, 145, "255 228 176")

# Parked / Driveable Vehicles along 20th St & H St outside the Fox (gal_020 & gal_042!)
for vx, vy, vyaw, vkind in (
    (-34, -22.5, 220, "sedan"), (-62, -22.5, 220, "coupe"), (-88, -22.5, 220, "sedan"),
    (21.5, 14, 90, "truck"), (32.0, 6, 90, "sedan"),
):
    ent("misc_vehicle_" + vkind, vx, vy, 0.2, angle=vyaw)


# ============================================================================== 3. OUTER TERRAZZO VESTIBULE, MARQUEE & CLOCK TOWER
# Outer Terrazzo Floor (x = -26 .. 0, y = 0 .. 28, z = 0 .. 0.52) — completely open & walkable under marquee (gal_020/110)!
box(-26, 0, 0.0, 0, 28, 0.52, TERRAZZO, {"t": TERRAZZO})

# South Vestibule Return (x = -20.8 .. -14, y = 0 .. 9.6) with Landscape Bronze Poster Case ('ALI SIDDIQ', gal_020.jpg!)
box(-20.8, 0, 0.52, -14, 9.6, 22.0, STUCCO, {"s": Fit("fx_shopwin"), "w": LOBWALL})
box(-14.0, 0.0, 0.52, -1.8, 2.2, 12.0, STUCCO)
prop(-13.2, 2.2, 0.52, -2.6, 2.6, 1.8, "fx_foxside")                                            # Maroon baseboard kickplate
prop(-12.6, 2.2, 2.4, -3.2, 2.8, 8.2, "fx_bronze", {"n": Fit("fx_post26")})                     # South landscape poster case!
prop(-13.2, 2.2, 8.4, -2.6, 3.2, 9.2, TERRA)                                                    # Molded poster cornice

# Slender SE & NE Stucco Marquee Corner Piers + North Vestibule Wall (gal_020.jpg & gal_110.jpg!)
box(-1.8, 0.0, 0.52, 0.0, 2.2, 12.0, STUCCO)
prop(-1.8, 25.0, 0.52, 0.0, 28.0, 12.0, STUCCO)
box(-14.0, 25.4, 0.52, 0.0, 28.0, 22.0, STUCCO)                                                 # North wall of outer vestibule
prop(-13.2, 25.0, 0.52, -2.6, 25.4, 1.8, "fx_foxside")
prop(-12.6, 24.8, 2.4, -3.2, 25.4, 8.2, "fx_bronze", {"s": Fit("fx_post26")})                   # North landscape poster case!
prop(-13.2, 24.4, 8.4, -2.6, 25.4, 9.2, TERRA)

# Entrance Wall between Outer Vestibule (x > -14) and Wide East Foyer (x = -23 .. -15.2) — Feb 2026 configuration (gal_020.jpg!):
# Two wide open walk-in double-door bays (y = 10.0..15.2 & y = 19.8..25.0, each 5.2 ft wide x 8.4 ft tall)
# flanking the Central Built-In Box Office Window with Crimson-Red Valance (y = 15.2..19.8)!
wall_y(-15.2, 1.2, 9.6, 28.0, 0.52, 22.0, STUCCO,
       faces={"w": LOBWALL, "e": STUCCO},
       holes=[(10.0, 15.2, 0.52, 8.9), (19.8, 25.0, 0.52, 8.9)])
prop(-14.0, 15.3, 0.52, -13.5, 19.7, 8.6, "fx_bronze", {"e": Fit("fx_boxval")})                 # Central Box Office + red valance!
prop(-14.0, 15.0, 8.6, -13.0, 20.0, 9.5, TERRA)                                                 # Sculpted Box Office eyebrow
for dy0, dy1 in ((10.0, 15.2), (19.8, 25.0)):
    prop(-14.8, dy0, 8.9, -14.2, dy1, 11.4, "bk_darkwin")                                       # Glass transom
    # Outward-swinging bronze exit doors leaving full 5.0ft clear width & 100% open interior foyer!
    prop(-14.0, dy0 + 0.05, 0.52, -12.2, dy0 + 0.22, 8.6, "fx_bronze", {"n": Fit("fx_entrydr"), "s": Fit("fx_entrydr")})
    prop(-14.0, dy1 - 0.22, 0.52, -12.2, dy1 - 0.05, 8.6, "fx_bronze", {"n": Fit("fx_entrydr"), "s": Fit("fx_entrydr")})

# Vestibule / Tower-Base ceiling slab at z = 12.0 .. 22.0 (x = -15.2 .. 0 so East Foyer & Stairs x < -15.2 have full 28-35ft headroom!)
box(-15.2, 0.0, 12.0, 0.0, 28.0, 22.0, STUCCO, {"b": tspec("fx_mqsoffit", 6)})
box(-22.0, 0.0, 20.8, -15.2, 28.0, 22.0, STUCCO, {"b": LOBCEIL})

# --- THE WRAP-AROUND FOX MARQUEE (Feb 2026 Street View Match: gal_018..024, gal_042) ---
MQ_SOUTH = [(-26.0, -9.5), (-6.0, -9.5), (4.2, -0.6), (0.0, 4.0), (-26.0, 4.0)]
MQ_EAST = [(0.0, 0.0), (4.2, -0.6), (9.5, 4.0), (9.5, 53.0), (0.0, 53.0)]
for mp in (MQ_SOUTH, MQ_EAST):
    prism(mp, 11.5, 12.2, "bk_roof", side="fx_terra", bot=tspec("fx_mqsoffit", 6), group="detail", solid=True)
prop(-0.4, 51.4, 0.52, 0.7, 53.0, 11.5, STUCCO)                                                  # Slender North marquee end pier (gal_020/023!)

# Marquee Readerboards (z = 12.2 .. 17.2):
# 1) South wing along 20th St (blank white milk-glass tracks in gal_042.jpg!)
prop(-26.0, -9.6, 12.2, -6.0, -8.8, 17.2, TERRA, {"s": Fit("fx_mqblank")})
# 2) Extended 49-ft East wing along H St ('BABY BASH MC / MAGIC LIL ROB / FEB 15' & 'CARLOS MENCIA / FEB 20', gal_020/023!)
prop(8.8, 4.0, 12.2, 9.6, 53.0, 17.2, TERRA, {"e": Fit("fx_mqside")})


def angled_panel_se(x0, y0, x1, y1, z0, z1, front_tex, back_tex="fx_terra", th=0.9, group="detail", solid=True):
    """Vertical panel facing SE from (x0, y0) to (x1, y1) with dx > dy so qbsp projects UVs along X cleanly."""
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = (y1 - y0) / L, -(x1 - x0) / L
    P0, P1 = (x0, y0), (x1, y1)
    B0, B1 = (x0 - nx * th, y0 - ny * th), (x1 - nx * th, y1 - ny * th)
    X0, X1 = u(x0, OX), u(x1, OX)
    Z0, Z1 = u(z0), u(z1)
    ft = texline(Fit(front_tex), "s", (X0, 0, Z0), (X1, 0, Z1))
    bt = ft if front_tex.startswith("{") else spec(back_tex)
    et = f"{front_tex} 0 0 0 1000 1000" if front_tex.startswith("{") else spec(back_tex)
    Q = lambda p, z: (u(p[0], OX), u(p[1], OY), u(z))
    fs = [
        (Q(P0, z0), Q(P1, z0), Q(P0, z1), (nx, ny, 0), ft),
        (Q(B0, z0), Q(B0, z1), Q(B1, z0), (-nx, -ny, 0), bt),
        (Q(B0, z0), Q(P0, z0), Q(B0, z1), (-(x1 - x0), -(y1 - y0), 0), et),
        (Q(P1, z0), Q(B1, z0), Q(P1, z1), (x1 - x0, y1 - y0, 0), et),
        (Q(P0, z1), Q(P1, z1), Q(B0, z1), (0, 0, 1), et),
        (Q(P0, z0), Q(B0, z0), Q(P1, z0), (0, 0, -1), et),
    ]
    brush(fs, group=group, solid=solid)


# 3) Center SE Corner Readerboard: 'ALI SIDDIQ / IN THE SHADOWS TOUR / FEB 14' (gal_020/021!)
angled_panel_se(-6.0, -9.5, 9.5, 4.0, 12.2, 17.2, "fx_mqfront", "fx_terra", th=0.9)

# 4) Upper Art Deco Valence: Red/Gold/Olive Chevrons on Wings (9 chevron bays on H St!) + Gold/Olive Horizontal Ribs at Center!
prop(-25.5, -9.0, 17.2, -5.8, -8.0, 21.2, TERRA, {"s": Fit("fx_mqwing", (2, 1))})
prop(8.0, 3.8, 17.2, 9.0, 52.8, 21.2, TERRA, {"e": Fit("fx_mqwing", (2.25, 1))})
angled_panel_se(-5.8, -9.0, 9.0, 3.8, 17.2, 22.8, "fx_mqgold", "fx_terra", th=0.9)

# 5) Alpha-Cutout Rooftop Cursive 'Fox' Channel-Letter Sign + Top Neon Bar centered on the SE Corner (no tan rectangle, gal_020/023!)
angled_panel_se(-4.4, -7.8, 8.0, 2.2, 18.0, 27.6, "{fx_foxscr", "{fx_foxscr", th=0.25, group="fence", solid=False)
for mx, my in ((-18, -5), (2, -5), (5, 14), (5, 26), (5, 38), (5, 49)):
    light(mx, my, 10.5, 165, "255 232 188")
for vx, vy in ((-9.5, 13.5), (-9.5, 21.5), (-13.5, 6.0)):
    light(vx, vy, 10.8, 215, "255 234 194")
light(4.0, -4.0, 22.5, 185, "255 180 172")


# --- THE ICONIC CORNER CLOCK TOWER (cx = -12.0, cy = +13.0, rising z = 22.0 .. 116.5 ft!) ---
TCX, TCY = -12.0, 13.0
# Main shaft core (20 ft x 20 ft: x = -22 .. -2, y = 3 .. 23, z = 22 .. 71.5)
box(-22.0, 3.0, 22.0, -2.0, 23.0, 71.5, STUCCO, group="world")
# Corner stepped pilasters (give the authentic chamfered/buttressed Spanish tower silhouette!)
for px0, px1 in ((-22.6, -18.5), (-5.5, -1.4)):
    for py0, py1 in ((2.4, 6.5), (19.5, 23.6)):
        prop(px0, py0, 22.0, px1, py1, 70.5, STUCCO)

# Churrigueresque cast-stone & terracotta relief cartouches above the marquee (z = 23.5 .. 31.8)
prop(-16.2, 2.1, 23.5, -7.8, 3.0, 31.8, TERRA, {"s": Fit("fx_crest")})
prop(-2.0, 8.8, 23.5, -1.1, 17.2, 31.8, TERRA, {"e": Fit("fx_crest")})

# Tall twin-lancet windows with center cream mullions on all 4 faces (z = 32.5 .. 56.5)
# Built as recessed window frames around the shaft!
for side_ang in ("s", "e", "n", "w"):
    if side_ang == "s":
        prop(-15.4, 2.2, 32.5, -8.6, 3.0, 56.5, STUCCO_DK, {"s": Fit("fx_lancet")})
        prop(-12.3, 2.0, 32.5, -11.7, 3.0, 56.5, STUCCO)                                       # Center vertical mullion
    elif side_ang == "e":
        prop(-2.0, 9.6, 32.5, -1.2, 16.4, 56.5, STUCCO_DK, {"e": Fit("fx_lancet")})
        prop(-2.0, 12.7, 32.5, -1.0, 13.3, 56.5, STUCCO)
    elif side_ang == "n":
        prop(-15.4, 23.0, 32.5, -8.6, 23.8, 56.5, STUCCO_DK, {"n": Fit("fx_lancet")})
        prop(-12.3, 23.0, 32.5, -11.7, 24.0, 56.5, STUCCO)
    else:
        prop(-22.8, 9.6, 32.5, -22.0, 16.4, 56.5, STUCCO_DK, {"w": Fit("fx_lancet")})
        prop(-23.0, 12.7, 32.5, -22.0, 13.3, 56.5, STUCCO)


# Giant 3D Crimson "FOX" Channel Letters on ALL 4 Faces (z = 58.0 .. 68.8 ft)!
def fox_3d_letters(face_dir):
    """Builds true 3D brushwork 'F' 'O' 'X' letters standing 0.9 ft proud of the tower shaft."""
    z0, z1 = 58.0, 68.6
    th = 0.95
    fmap = {face_dir: "fx_foxred"}

    def stroke(u0, u1, za, zb):
        """u runs left-to-right across the 18.6 ft span (-9.3 .. +9.3) as seen from outside face_dir."""
        if face_dir == "s":      # looking +y: left->right is +x (centered at TCX=-12), projects -y from y=2.6
            prop(TCX + u0, 2.6 - th, za, TCX + u1, 2.6, zb, "fx_foxside", fmap)
        elif face_dir == "e":    # looking -x: left->right is +y (centered at TCY=13), projects +x from x=-1.6
            prop(-1.6, TCY + u0, za, -1.6 + th, TCY + u1, zb, "fx_foxside", fmap)
        elif face_dir == "n":    # looking -y: left->right is -x, projects +y from y=23.4
            prop(TCX - u1, 23.4, za, TCX - u0, 23.4 + th, zb, "fx_foxside", fmap)
        else:                    # looking +x: left->right is -y, projects -x from x=-22.4
            prop(-22.4 - th, TCY - u1, za, -22.4, TCY - u0, zb, "fx_foxside", fmap)

    def diag_x(ua0, ua1, ub0, ub1, za, zb):
        """Diagonal 3D bar for letter 'X' from bottom (ua0..ua1, za) to top (ub0..ub1, zb)."""
        def pt(u_val, out_d, z_val):
            if face_dir == "s":
                return (u(TCX + u_val, OX), u(2.6 - out_d, OY), u(z_val))
            if face_dir == "e":
                return (u(-1.6 + out_d, OX), u(TCY + u_val, OY), u(z_val))
            if face_dir == "n":
                return (u(TCX - u_val, OX), u(23.4 + out_d, OY), u(z_val))
            return (u(-22.4 - out_d, OX), u(TCY - u_val, OY), u(z_val))

        out_n = {"s": (0, -1, 0), "e": (1, 0, 0), "n": (0, 1, 0), "w": (-1, 0, 0)}[face_dir]
        rgt_n = {"s": (1, 0, 0), "e": (0, 1, 0), "n": (-1, 0, 0), "w": (0, -1, 0)}[face_dir]
        in_n = (-out_n[0], -out_n[1], 0)
        F0, F1, F2, F3 = pt(ua0, th, za), pt(ua1, th, za), pt(ub1, th, zb), pt(ub0, th, zb)
        B0, B1, B2, B3 = pt(ua0, 0, za), pt(ua1, 0, za), pt(ub1, 0, zb), pt(ub0, 0, zb)
        du, dz = ub0 - ua0, zb - za
        ln_n = (-rgt_n[0] * dz, -rgt_n[1] * dz, du)
        rn_n = (rgt_n[0] * dz, rgt_n[1] * dz, -du)
        fs = [
            (F0, F1, F2, out_n, spec("fx_foxred")),
            (B0, B2, B1, in_n, spec("fx_foxside")),
            (B0, F0, B3, ln_n, spec("fx_foxside")),
            (F1, B1, F2, rn_n, spec("fx_foxside")),
            (F3, F2, B2, (0, 0, 1), spec("fx_foxside")),
            (B0, B1, F1, (0, 0, -1), spec("fx_foxside")),
        ]
        brush(fs, group="detail", solid=False)

    # Letter 'F' (-9.0 .. -3.8)
    stroke(-9.0, -7.5, z0, z1)
    stroke(-7.5, -3.8, z1 - 1.7, z1)
    stroke(-7.5, -4.6, (z0 + z1) / 2 - 0.7, (z0 + z1) / 2 + 0.9)
    # Letter 'O' (-2.5 .. +2.5)
    stroke(-2.5, -1.0, z0, z1)
    stroke(1.0, 2.5, z0, z1)
    stroke(-1.0, 1.0, z1 - 1.7, z1)
    stroke(-1.0, 1.0, z0, z0 + 1.7)
    # Letter 'X' (+3.8 .. +9.0) — two crisp crossing diagonal 3D prisms!
    diag_x(3.8, 5.4, 7.4, 9.0, z0, z1)
    diag_x(7.4, 9.0, 3.8, 5.4, z0, z1)


for _fd in ("s", "e", "n", "w"):
    fox_3d_letters(_fd)

# Projecting molded cornice above FOX shaft (z = 70.5 .. 73.8)
prop(-23.6, 1.4, 70.5, -0.4, 24.6, 72.2, TERRA)
prop(-24.2, 0.8, 72.2, 0.2, 25.2, 73.8, STUCCO)

# Clock Belfry Stage (16.8 ft x 16.8 ft: x = -20.4 .. -3.6, y = 4.6 .. 21.4, z = 73.8 .. 89.5)
box(-20.4, 4.6, 73.8, -3.6, 21.4, 89.5, STUCCO, group="world")
for px0, px1 in ((-21.0, -17.8), (-6.2, -3.0)):
    for py0, py1 in ((4.0, 7.2), (18.8, 22.0)):
        prop(px0, py0, 73.8, px1, py1, 89.5, TERRA)

# 4 Navy-Blue Illuminated Clock Faces (z = 75.8 .. 86.8)
prop(-17.4, 4.0, 75.8, -6.6, 4.6, 86.8, TERRA, {"s": Fit("fx_clock")})
prop(-3.6, 7.6, 75.8, -3.0, 18.4, 86.8, TERRA, {"e": Fit("fx_clock")})
prop(-17.4, 21.4, 75.8, -6.6, 22.0, 86.8, TERRA, {"n": Fit("fx_clock")})
prop(-21.0, 7.6, 75.8, -20.4, 18.4, 86.8, TERRA, {"w": Fit("fx_clock")})

# Upper Churrigueresque Crown Cornice + 8 Corner Urn Finials (z = 89.5 .. 92.2)
prop(-21.4, 3.6, 89.5, -2.6, 22.4, 91.5, TERRA)
for ux in (-20.4, -3.6):
    for uy in (4.6, 21.4):
        prop(ux - 0.9, uy - 0.9, 91.5, ux + 0.9, uy + 0.9, 94.2, TERRA)
        frustum_ring(ux, uy, 0.7, 0.15, 94.2, 96.2, STUCCO, sides=8)

# Octagonal Drum + Smooth 16-Sided Ribbed Silver-Blue Cupola Dome (z = 91.5 .. 103.8)
frustum_ring(TCX, TCY, 8.2, 8.0, 91.5, 94.0, STUCCO, sides=16)
dome_profile = [(94.0, 7.8), (96.0, 7.3), (98.0, 6.4), (99.8, 5.1), (101.4, 3.5), (102.8, 1.8), (103.8, 0.9)]
for (za, ra), (zb, rb) in zip(dome_profile, dome_profile[1:]):
    frustum_ring(TCX, TCY, ra, rb, za, zb, "fx_dome", sides=16)

# Bronze Lantern, Orb & Tall Spire Finial (z = 103.8 .. 116.5 ft!)
frustum_ring(TCX, TCY, 1.05, 0.85, 103.8, 106.4, TERRA, sides=8)
frustum_ring(TCX, TCY, 0.95, 0.95, 106.4, 107.8, "fx_goldleaf", sides=12)
frustum_ring(TCX, TCY, 0.45, 0.08, 107.8, 116.5, "fx_bronze", sides=8)
prop(TCX - 1.2, TCY - 0.08, 114.2, TCX + 1.2, TCY + 0.08, 114.5, "fx_bronze")


# ============================================================================== 4.PINNACLE HELPER & EXTERIOR FACADES (20TH ST & H ST)
def pinnacle(cx, cy, z0, h=6.5, cap_tex=STUCCO, body_tex=None):
    """Sculpted Spanish Churrigueresque rooftop pinnacle / finial."""
    btex = body_tex or STUCCO
    prop(cx - 0.95, cy - 0.95, z0, cx + 0.95, cy + 0.95, z0 + h * 0.36, btex)
    prop(cx - 1.15, cy - 1.15, z0 + h * 0.36, cx + 1.15, cy + 1.15, z0 + h * 0.46, cap_tex)
    frustum_ring(cx, cy, 0.85, 0.42, z0 + h * 0.46, z0 + h * 0.78, cap_tex, sides=8)
    frustum_ring(cx, cy, 0.42, 0.08, z0 + h * 0.78, z0 + h, btex, sides=8)


def awning_x(x0, x1, y_wall, z0=9.4, z1=11.8, proj=3.8, tex_name="fx_awnred"):
    """Angled terracotta-red storefront canvas awning along a South-facing wall (y = y_wall, gal_042.jpg)."""
    poly = [(x0, y_wall - proj), (x1, y_wall - proj), (x1, y_wall), (x0, y_wall)]
    prism(poly, [z0, z0, z1 - 0.3, z1 - 0.3], [z0 + 0.35, z0 + 0.35, z1, z1], tspec(tex_name, 4), group="detail", solid=False)


def awning_y(x_wall, y0, y1, z0=9.4, z1=11.8, proj=3.8, tex_name="fx_awnred"):
    """Angled terracotta-red storefront canvas awning along an East-facing wall (x = x_wall, gal_019/023.jpg)."""
    poly = [(x_wall, y0), (x_wall + proj, y0), (x_wall + proj, y1), (x_wall, y1)]
    prism(poly, [z1 - 0.3, z0, z0, z1 - 0.3], [z1, z0 + 0.35, z0 + 0.35, z1], tspec(tex_name, 4), group="detail", solid=False)


# --- SOUTH FACADE ALONG 20TH STREET (x = -112 .. -22, y = 0, gal_042.jpg & gal_043.jpg) ---
# 1) Connector Section (x = -46 .. -20.8, y = 0 .. 8.2, z = 0.5 .. 28.5) + Red Tile Roof + Curved Sheet-Metal HVAC Duct!
box(-46.0, 0.0, 0.5, -20.8, 1.2, 28.5, STUCCO, {"n": LOBWALL})
box(-46.0, 1.2, 27.5, -20.8, 8.2, 28.5, STUCCO, {"b": LOBCEIL})                                 # Lower foyer ceiling under tile roof
box(-46.0, 7.0, 28.5, -20.8, 8.2, 38.0, STUCCO, {"n": LOBWALL})                                 # Setback wall rising to 38ft foyer roof
prism([(-46.0, -1.2), (-22.0, -1.2), (-22.0, 7.5), (-46.0, 7.5)],
      [28.2, 28.2, 31.2, 31.2], [28.8, 28.8, 31.8, 31.8], TILE, group="detail")
prop(-46.0, -0.25, 11.8, -22.0, 0.05, 12.6, PEACH)                                              # Salmon-peach horizontal frieze band (gal_042)
prop(-37.0, -0.2, 1.0, -27.0, 0.1, 8.8, "fx_bronze", {"s": Fit("fx_shopwin")})
awning_x(-38.5, -25.5, 0.0)
prop(-35.5, -0.3, 13.8, -30.5, 0.1, 21.0, STUCCO_DK, {"s": Fit("fx_lancet")})
box(-36.2, -1.6, 13.4, -29.8, 0.0, 13.9, STUCCO, group="detail")
box(-36.0, -1.5, 13.9, -30.0, -1.35, 16.8, Fit("{fx_iron", (2, 1)), group="fence")

# Iconic Exposed Beige Sheet-Metal HVAC Supply Duct curving over the 2nd-story tile roof into the Auditorium!
duct_segs = [
    (-35.5, -28.0, 1.8, 7.6, 30.8, 40.5),
    (-35.5, -28.0, 7.6, 13.8, 37.5, 45.2),
    (-35.5, -28.0, 13.8, 22.0, 41.2, 46.8),
    (-35.5, -28.0, 22.0, 38.0, 41.5, 46.8),
]
for dx0, dx1, dy0, dy1, dz0, dz1 in duct_segs:
    prop(dx0, dy0, dz0, dx1, dy1, dz1, tspec("fx_duct", 5))
# Spanish Red Clay Tile Skirt behind East Marquee Wing (prominent in gal_020/023 right below East FOX shaft!)
prism([(-2.2, 22.5), (2.4, 22.5), (2.4, 36.5), (-2.2, 36.5)],
      [23.2, 21.6, 21.6, 23.2], [23.9, 22.3, 22.3, 23.9], TILE, group="detail")
prop(-31.2, 15.0, 46.2, -30.9, 15.3, 52.5, "bk_steel")
prop(-35.0, 15.1, 51.8, -27.0, 15.25, 52.0, "bk_steel")

# 2) Three-Story Spanish Churrigueresque Pavilion (x = -86 .. -46, y = 0 .. 1.2, z = 0.5 .. 38.0 + Gable to 47.0)
wall_x(-86.0, -46.0, 0.0, 1.2, 0.5, 38.0, STUCCO, faces={"n": LOBWALL, "s": STUCCO},
       holes=[(-57.5, -51.5, 0.5, 8.6)])                                                        # Wide 6.0ft South exit/entry doorway!
awning_x(-58.5, -50.5, 0.0)                                                                     # Red awning over 20th St side door (gal_042)
box(-86.0, 0.0, 24.5, -84.8, 20.8, 38.0, STUCCO, {"e": LOBWALL})
box(-86.0, 19.5, 30.8, -84.8, 38.0, 38.0, STUCCO, {"e": LOBWALL})
box(-47.2, 0.0, 28.0, -46.0, 8.2, 38.0, STUCCO, {"w": LOBWALL})
prop(-57.5, -1.2, 0.5, -51.5, 0.2, 0.55, TERRAZZO)
prop(-86.0, -0.25, 11.8, -46.0, 0.05, 12.6, PEACH)
# Stepped Mission Gable + Terracotta Shell Niche + 3 Peach/Terracotta-Capped Pinnacles!
prop(-72.0, -0.2, 38.0, -54.0, 1.4, 42.5, STUCCO)
prop(-67.5, -0.3, 42.5, -58.5, 1.4, 46.8, STUCCO)
prop(-66.0, -0.5, 36.8, -60.0, 0.2, 43.8, PEACH, {"s": Fit("fx_crest")})
pinnacle(-84.5, 0.5, 38.0, 6.2, PEACH)
pinnacle(-63.0, 0.5, 46.8, 6.5, PEACH)
pinnacle(-47.5, 0.5, 38.0, 6.2, PEACH)
prop(-53.5, 2.5, 35.0, -49.5, 6.5, 49.5, STUCCO)
prop(-54.0, 2.0, 49.5, -49.0, 7.0, 50.4, STUCCO_DK)
prop(-66.0, -0.4, 25.0, -60.0, 0.2, 34.5, PEACH, {"s": Fit("fx_lancet")})
prop(-68.0, -2.4, 23.6, -58.0, 0.0, 24.6, STUCCO)
for cx in (-66.8, -63.0, -59.2):
    prop(cx - 0.4, -2.0, 21.8, cx + 0.4, 0.0, 23.6, PEACH)
box(-67.8, -2.3, 24.6, -58.2, -2.15, 27.6, Fit("{fx_iron", (3, 1)), group="fence")
for wx in (-77.0, -55.0):
    prop(wx, -0.3, 13.5, wx + 4.4, 0.1, 20.2, STUCCO_DK, {"s": Fit("fx_lancet")})
    box(wx - 0.4, -1.2, 13.5, wx + 4.8, -1.05, 16.2, Fit("{fx_iron", (1.5, 1)), group="fence")
prop(-80.0, -0.3, 2.2, -65.0, 0.1, 8.8, "fx_bronze", {"s": Fit("fx_shopwin")})
awning_x(-81.0, -64.0, 0.0)

# 3) Far-West Two-Story Annex along 20th Street (x = -112 .. -86, y = 0 .. 38, z = 0.5 .. 25.0) + Enclosed West Stair Hall!
box(-112.0, 0.0, 0.5, -103.5, 38.0, 25.0, STUCCO)
box(-105.0, 19.5, 24.5, -103.5, 38.0, 31.5, STUCCO, {"e": LOBWALL})
box(-103.5, 0.0, 0.5, -86.0, 1.5, 25.0, STUCCO, {"n": LOBWALL})
box(-105.0, 35.5, 0.5, -94.0, 38.0, 31.5, STUCCO, {"s": LOBWALL})
box(-105.0, 0.0, 23.8, -84.8, 20.8, 25.0, STUCCO, {"b": LOBCEIL})                                # West Lobby Alcove 24ft ceiling
box(-105.0, 19.5, 23.8, -84.8, 20.8, 31.5, STUCCO, {"n": LOBWALL, "s": STUCCO})                  # Hidden setback step-up for West Mezzanine
box(-105.0, 19.5, 30.2, -84.8, 38.0, 31.5, STUCCO, {"b": LOBCEIL})                               # West Stair & Mezzanine 30.2ft ceiling
prop(-112.5, -0.5, 24.2, -86.0, 0.2, 25.4, PEACH)                                                # Exterior-only 20th St cornice (never through West Stair!)
prop(-112.5, -0.5, 24.2, -111.8, 38.4, 25.4, PEACH)
for wx in (-108.0, -100.0, -92.0):
    prop(wx, -0.3, 13.8, wx + 4.0, 0.1, 19.5, STUCCO_DK, {"s": Fit("fx_lancet")})
prop(-109.0, -0.3, 2.2, -88.0, 0.1, 8.8, "fx_bronze", {"s": Fit("fx_shopwin")})
awning_x(-110.0, -87.0, 0.0)


# --- EAST FACADE ALONG H STREET: 3 WIDE RED-AWNING BAYS NORTH OF MARQUEE & EVA'S LOUNGE (x = -13 .. 0, y = 28 .. 154, gal_020/023!) ---
wall_y(-1.0, 1.0, 28.0, 76.0, 0.5, 15.5, STUCCO, faces={"w": LOBWALL, "e": STUCCO},
       holes=[(31.0, 50.0, 2.0, 9.0), (54.5, 60.8, 0.5, 8.6), (62.2, 74.0, 2.0, 9.0)])         # Wide 6.3ft street door to Eva's at y = 54.5..60.8!
for wy0, wy1 in ((31.0, 50.0), (62.2, 74.0)):
    prop(-0.8, wy0, 2.0, -0.2, wy1, 9.0, "fx_bronze", {"e": Fit("fx_shopwin")})
    prop(-0.2, wy0, 0.5, 0.3, wy1, 2.0, PEACH)
box(-13.0, 75.0, 0.5, 0.0, 76.0, 15.5, STUCCO, {"s": LOBWALL})
box(-13.0, 28.0, 14.5, 0.0, 76.0, 16.0, STUCCO, {"b": LOBWALL})
box(-13.0, 28.0, 0.0, 0.0, 76.0, 0.52, "fx_stageflr")

# Eva's Lounge Interior (small stage, bar counter & lounge tables, per bakersfieldlive.com/rental-information!)
prop(-12.5, 65.0, 0.52, -2.0, 74.5, 2.0, "fx_stageflr")
prop(-12.5, 74.0, 2.0, -2.0, 74.8, 13.5, "fx_drapered")
prop(-12.2, 38.0, 0.52, -9.2, 54.0, 3.8, TERRA, {"e": Fit("fx_concess")})
prop(-12.8, 41.0, 6.2, -12.3, 51.0, 9.0, "fx_bronze", {"e": Fit("fx_evasign")})
for ly in (36.0, 52.0, 68.0):
    light(-6.5, ly, 12.8, 135, "255 214 168")

# 3 Wide Spanish Storefront Bays North of Marquee (y = 53.5 .. 154.0) + Divided Arched Transoms + Shrub Planters (gal_023.jpg!)
box(-13.0, 76.0, 0.5, 0.0, 154.0, 16.0, STUCCO)
prop(-0.2, 76.5, 2.0, 0.3, 85.0, 9.0, "fx_bronze", {"e": Fit("fx_shopwin")})
prop(-0.2, 76.5, 0.5, 0.35, 85.0, 2.0, PEACH)
# White rectangular sign panel centered above Bay 1's divided clerestory transom (exact match to gal_020.jpg & gal_023.jpg!)
prop(-0.1, 63.0, 14.3, 0.55, 77.5, 16.0, "fx_bronze", {"e": "bk_white"})
for by0 in (53.8, 87.0, 120.2):
    prop(-0.3, by0 - 1.2, 0.5, 0.7, by0 + 1.2, 16.8, STUCCO)                                    # Cream storefront bay pier
    prop(-0.4, by0 - 1.4, 15.6, 0.9, by0 + 1.4, 17.2, PEACH)                                    # Peach/green Churrigueresque capital
    if by0 >= 86.0:
        prop(-0.2, by0 + 2.2, 2.0, 0.3, by0 + 30.8, 9.0, "fx_bronze", {"e": Fit("fx_shopwin")})
        prop(-0.2, by0 + 2.2, 0.5, 0.35, by0 + 30.8, 2.0, PEACH)                                # Salmon-peach storefront kickplate!
    # Divided arched clerestory transom above each of the 3 wide red awnings (gal_020 & gal_023!)
    prop(-0.1, by0 + 2.2, 11.6, 0.4, by0 + 30.8, 14.4, STUCCO, {"e": Fit("fx_transom", (1.4, 1))})
    awning_y(0.0, by0 + 1.6, by0 + 31.4, z0=9.2, z1=11.6)
    # Brick planter box with trimmed green shrub at storefront piers (leaving 13ft clear sidewalk!)
    if by0 >= 86.0:
        prop(0.7, by0 - 1.8, 0.54, 2.6, by0 + 1.8, 1.6, PEACH)
        prop(0.9, by0 - 1.4, 1.6, 2.4, by0 + 1.4, 3.8, "bk_hedge")
prop(-0.3, 152.8, 0.5, 0.7, 154.5, 16.8, STUCCO)

# Continuous Pitched Red Spanish Clay Tile Pent Roof over the 3 H-Street Storefront Bays North of Marquee (y = 53 .. 154)!
prism([(-3.5, 53.0), (1.4, 53.0), (1.4, 154.0), (-3.5, 154.0)],
      [17.0, 14.8, 14.8, 17.0], [17.7, 15.5, 15.5, 17.7], TILE, group="detail")


# ============================================================================== 5. MAIN LOBBY, CONCESSIONS, STAIRS & MEZZANINE
# Lobby / Foyer Shell (x = -104.5 .. -13, y = 1.2 .. 37.0)
box(-104.5, 1.2, 0.0, -34.0, 37.0, 0.52, CARPET)
box(-34.0, 1.2, 0.0, -13.0, 37.0, 0.52, TERRAZZO)
# Stepped Lobby Roof Slabs with Photo-Matched Sky-Blue & Rose-Medallion Frescoed Ceiling (LOBCEIL, gal_114 & gal_115!):
box(-86.0, 1.2, 35.0, -46.0, 26.0, 38.0, STUCCO, {"b": LOBCEIL})
box(-46.0, 8.0, 35.0, -20.8, 26.0, 38.0, STUCCO, {"b": LOBCEIL})
box(-38.0, 26.0, 35.0, -17.0, 38.0, 38.0, STUCCO, {"b": LOBCEIL})
box(-22.0, 1.2, 20.8, -20.8, 26.5, 38.0, STUCCO, {"w": LOBWALL})                                # East upper wall South of Mezzanine alcove
box(-22.0, 26.0, 20.8, -17.0, 26.8, 38.0, STUCCO, {"n": LOBWALL})                               # South wall of East Mezzanine alcove
box(-18.2, 26.5, 20.8, -17.0, 38.0, 38.0, STUCCO, {"w": LOBWALL})                               # East wall of East Mezzanine alcove
box(-22.0, 36.8, 20.8, -17.0, 38.0, 38.0, STUCCO, {"s": LOBWALL})                               # North wall of East Mezzanine alcove
box(-22.0, 28.0, 14.5, -13.0, 37.0, 20.8, STUCCO, {"b": LOBWALL})                               # East Foyer ceiling before Eva's
# Connection archway from East Lobby into Eva's Lounge (x = -14 .. -13, y = 29.5 .. 35.5, z = 0.52 .. 9.5)
wall_y(-14.0, 1.0, 28.0, 37.0, 0.52, 16.0, LOBWALL, holes=[(29.5, 35.5, 0.52, 9.5)])

# 1953 Streamlined Skouras Concession Stand (South Lobby wall: x = -50 .. -32, y = 2.0 .. 9.5 — clear of both 20th St door & East Stair!)
prop(-50.0, 6.8, 0.52, -32.0, 9.6, 3.6, TERRA, {"n": Fit("fx_concess", (2, 1)), "t": "fx_goldleaf"})
prop(-49.5, 1.4, 5.2, -33.0, 2.2, 10.5, "fx_bronze", {"n": Fit("fx_concmenu")})
prop(-50.5, 1.4, 11.2, -31.5, 10.2, 12.2, TERRA, {"b": tspec("fx_mqsoffit", 5)})
light(-41.0, 8.0, 10.2, 230, "255 228 188")

# West Lobby Wall & Enclosed West Stair Hall Partition (x = -95.8 .. -94.8, leaving full unobstructed Tapestry sightline!)
wall_y(-95.8, 1.0, 1.5, 35.5, 0.52, 30.2, LOBWALL,
       faces={"e": LOBWALL, "w": LOBWALL},
       holes=[(2.0, 7.2, 0.52, 9.8), (29.2, 35.0, 20.8, 29.0)])
prop(-94.8, 1.6, 0.52, -94.3, 2.0, 10.4, TERRA)
prop(-94.8, 7.4, 0.52, -94.3, 7.8, 10.4, TERRA)
prop(-94.8, 1.6, 9.8, -94.2, 7.8, 10.6, TERRA)
prop(-94.7, 2.0, 8.8, -94.4, 7.4, 9.8, "fx_drapered")

# West Lobby California Exploration Tapestry Alcove, Pilasters, Sconces & Velvet Sofa (matching site_img_13.png!)
prop(-94.8, 7.8, 0.52, -93.2, 9.0, 23.8, LOBWALL)
prop(-94.8, 21.8, 0.52, -93.2, 23.2, 19.8, LOBWALL)
prop(-94.8, 7.8, 15.0, -93.2, 23.2, 19.8, LOBWALL)
prop(-94.8, 9.5, 4.6, -94.2, 21.3, 13.5, "fx_bronze", {"e": Fit("fx_tapestry")})
fox_model("pad_sofa_red", -92.4, 15.4, 0.52, yaw=0,
          clip_box=(-93.8, 11.9, 0.85, -91.0, 18.9, 2.5))
for sc_y in (8.3, 22.5):
    prop(-93.2, sc_y - 0.3, 7.6, -92.6, sc_y + 0.3, 9.4, "fx_bronze")
    prop(-92.8, sc_y - 0.35, 9.4, -92.4, sc_y - 0.1, 10.2, "bk_white")
    prop(-92.8, sc_y + 0.1, 9.4, -92.4, sc_y + 0.35, 10.2, "bk_white")
    light(-89.5, sc_y, 10.0, 230, "255 226 178")
light(-88.0, 15.4, 18.5, 235, "255 230 186")
for sc_x in (-76.0, -54.0, -32.0):
    prop(sc_x - 0.35, 36.5, 7.8, sc_x + 0.35, 37.0, 9.5, "fx_bronze")
    prop(sc_x - 0.3, 36.3, 9.5, sc_x + 0.3, 36.6, 10.3, "bk_white")
    light(sc_x, 34.5, 9.8, 195, "255 224 176")

# Sloping Stenciled Concrete Balcony-Support Raker Beams Overhead (site_img_02.png, site_img_13.png & gal_116.jpg!)
for rx in (-74.0, -54.0, -34.0):
    prism([(rx - 1.2, 2.0), (rx + 1.2, 2.0), (rx + 1.2, 23.0), (rx - 1.2, 23.0)],
          [29.5, 29.5, 20.0, 20.0], [35.0, 35.0, 22.5, 22.5], tspec("fx_raker", 6), group="detail")

# Hanging Wrought-Iron & Gold Spanish Lobby Chandeliers centered in the frescoed ceiling bays between raker beams (gal_115.jpg!)
for cx, cy in ((-83.5, 13.5), (-64.0, 13.5), (-44.0, 13.5)):
    prop(cx - 0.08, cy - 0.08, 30.2, cx + 0.08, cy + 0.08, 35.0, "fx_bronze")
    fox_model("fox_chandelier", cx, cy, 25.0, yaw=15, z_off=0.0)
    light(cx, cy, 24.2, 325, "255 232 188")

# --- Upper Mezzanine Promenade & Spanish Arched Colonnade (gal_114..117, floor z = 19.8 .. 20.8 ft) ---
box(-94.8, 23.0, 19.8, -22.0, 37.0, 20.8, CARPET, {"b": LOBWALL, "s": "fx_goldleaf"})
box(-22.0, 26.5, 19.8, -18.0, 37.0, 20.8, CARPET, {"b": LOBWALL})                               # East Mezzanine Restroom Alcove landing!
box(-103.5, 29.0, 19.8, -94.8, 35.5, 20.8, CARPET, {"b": LOBWALL})                              # West Stair 6.5ft deep top landing!
# Antique Gold Wrought-Iron Mezzanine Balustrade + White Plaster Spanish Arched Colonnade Piers & Gold Scroll Corbels (gal_114/116)!
box(-94.6, 23.0, 20.8, -30.8, 23.2, 24.2, Fit("{fx_irongld", (13, 1)), group="fence")
prop(-94.8, 22.9, 24.1, -30.6, 23.3, 24.4, "fx_bronze")
# Arched colonnade piers spaced 15.8 ft apart (14.3 ft clear openings x 9.6 ft clear height, clear of East Grand Stair!)
prop(-94.8, 22.6, 30.4, -30.6, 24.0, 35.0, LOBWALL)                                              # Continuous colonnade upper header
prop(-94.8, 22.5, 34.0, -30.6, 24.2, 34.6, "fx_goldleaf")                                        # Gilded upper frieze molding
for post_x in (-94.0, -78.2, -62.4, -46.6, -31.2):
    prop(post_x - 0.75, 22.6, 20.8, post_x + 0.75, 24.0, 30.4, LOBWALL)                          # White plaster colonnade pier
    prop(post_x - 0.85, 22.5, 26.8, post_x + 0.85, 24.1, 27.6, "fx_goldleaf")                    # Gilded gold pier collar (gal_116!)
    prop(post_x - 0.90, 23.8, 33.2, post_x + 0.90, 25.4, 35.0, "fx_goldleaf")                    # Sculpted gold ceiling scroll corbel!
for arch_x0, arch_x1 in ((-93.25, -78.95), (-77.45, -63.15), (-61.65, -47.35), (-45.85, -31.95)):
    # Stepped arch haunches leaving full 9.6 ft center height & 14.3 ft width!
    prop(arch_x0, 22.65, 28.8, arch_x0 + 1.6, 23.95, 30.4, LOBWALL)
    prop(arch_x1 - 1.6, 22.65, 28.8, arch_x1, 23.95, 30.4, LOBWALL)

# East Mezzanine 'MEN' Restroom Vestibule, Soffit Beam, Gold Scroll Corbel & Double Gold Frieze (exact 1:1 match to gal_114.jpg!)
prop(-38.0, 33.8, 30.2, -18.2, 37.0, 35.0, LOBWALL)                                              # Cream plaster North soffit beam (gal_114 top-right!)
prop(-29.0, 33.4, 29.4, -27.2, 34.4, 30.2, "fx_goldleaf")                                        # Sculpted gold scroll corbel under soffit!
for fz in (28.3, 29.1):
    prop(-66.0, 36.75, fz, -35.5, 37.0, fz + 0.28, "fx_goldleaf")                                # Double gilded frieze along Mezzanine North wall!
for msc_x in (-58.0, -43.0):
    prop(msc_x - 0.4, 36.45, 28.5, msc_x + 0.4, 36.85, 29.1, "bk_white")
    light(msc_x, 34.8, 28.8, 195, "255 228 182")
wall_x(-26.8, -18.2, 32.6, 0.4, 20.8, 30.2, LOBWALL, holes=[(-25.8, -21.8, 20.8, 28.4)])         # Spacious 4.0ft x 7.6ft walk-in Men's Restroom doorway!
prop(-26.8, 32.6, 20.8, -26.3, 36.8, 30.2, LOBWALL)
prop(-26.95, 33.4, 24.0, -26.8, 34.4, 27.6, "fx_drapered")                                       # Red fire-hose drape on corner pier (gal_114!)
box(-26.3, 33.0, 20.8, -18.2, 36.8, 20.84, TILE, group="illus")                                  # Terracotta tile floor inside Men's Restroom!
box(-26.3, 36.6, 20.84, -18.2, 36.8, 21.4, "fx_drapeblk", group="illus")                         # Dark cove baseboard inside doorway (gal_114!)
prop(-25.6, 32.2, 28.5, -22.2, 32.62, 29.7, "fx_goldleaf", {"s": Fit("fx_mensign")})             # Gold-mounted 'MEN' blade sign over doorway!
light(-23.8, 34.9, 28.4, 185, "255 236 198")
light(-20.5, 29.8, 29.5, 255, "255 232 190")

# Mezzanine Museum Display: Original 1930 Carbon-Arc Followspot & Vintage Wooden 'FOX' Chairs tucked by railing (gal_114 & gal_116!)
prop(-55.2, 23.8, 20.8, -52.8, 25.6, 24.2, "fx_bronze")
prop(-54.8, 23.5, 24.2, -53.2, 26.0, 25.8, "bk_steel")
for chx in (-60.0, -48.0):
    prop(chx - 1.0, 23.8, 20.8, chx + 1.0, 25.4, 23.6, "fx_seatback")
# Mezzanine Ornate Spanish Chandelier centered in the Sky-Blue Frescoed Ceiling Field (y = 29.5, z = 25.6..30.8, gal_114.jpg!)
fox_model("fox_chandelier", -50.0, 29.5, 25.6, yaw=30, z_off=0.0)
light(-50.0, 29.5, 25.0, 295, "255 234 192")

# Dual Grand Staircases:
# 1) Enclosed West Stair Hall (x = -103.5 .. -95.8, y = 7.2 -> 29.0) & 2) Open East Grand Staircase (x = -30.5 .. -22.5, y = 5.6 -> 23.0)!
# Horizontal treads (riser <= 0.72 ft = 8.7 Quake units <= 18 max step; normal.z = 1.0 so players & bots never slide!)
N_LOB_STEPS = 30
for st_idx in range(N_LOB_STEPS):
    wsy0 = 7.2 + st_idx * (21.8 / N_LOB_STEPS)
    wsy1 = 7.2 + (st_idx + 1) * (21.8 / N_LOB_STEPS)
    sz = 0.52 + (st_idx + 1) * ((20.8 - 0.52) / N_LOB_STEPS)
    prop(-103.5, wsy0, 0.52, -95.8, wsy1, sz, CARPET)
N_EAST_STEPS = 28
for st_idx in range(N_EAST_STEPS):
    esy0 = 5.6 + st_idx * (17.4 / N_EAST_STEPS)
    esy1 = 5.6 + (st_idx + 1) * (17.4 / N_EAST_STEPS)
    sz = 0.52 + (st_idx + 1) * ((20.8 - 0.52) / N_EAST_STEPS)
    prop(-30.2, esy0, 0.52, -22.5, esy1, sz, CARPET, {"w": LOBWALL, "s": LOBWALL})
# Enclose East Foyer side of East Grand Staircase with plaster spandrel wall so Foyer (x = -22.5 .. -15.2 = 7.3ft wide!) is clean
prop(-22.5, 5.6, 0.52, -22.0, 23.0, 20.8, LOBWALL)
for wly, wlz in ((5.5, 11.5), (17.5, 19.5), (31.0, 27.5)):
    light(-99.6, wly, wlz, 185, "255 226 180")
# Stepped Antique-Gold Wrought-Iron Stair Balustrade & Sloped Handrail on Open East Grand Staircase (gal_116)!
N_RAIL_SEGS = 8
for r_i in range(N_RAIL_SEGS):
    ry0 = 5.8 + r_i * (17.2 / N_RAIL_SEGS)
    ry1 = 5.8 + (r_i + 1) * (17.2 / N_RAIL_SEGS)
    rz_bot = 0.52 + (r_i + 0.5) * ((20.8 - 0.52) / N_RAIL_SEGS)
    rz_top = rz_bot + 3.2
    box(-30.38, ry0, rz_bot, -30.2, ry1, rz_top, Fit("{fx_irongld", (0.8, 1)), group="fence")
prism([(-30.48, 5.8), (-30.08, 5.8), (-30.08, 23.0), (-30.48, 23.0)],
      [3.8, 3.8, 23.9, 23.9], [4.15, 4.15, 24.25, 24.25], "fx_bronze", group="detail")
prop(-30.63, 5.4, 0.52, -29.93, 6.1, 4.5, TERRA)
for mx in (-88.0, -70.0, -54.0, -34.0):
    light(mx, 28.5, 28.8, 275, "255 232 188")
    light(mx, 31.0, 17.5, 220, "255 228 184")


# ============================================================================== 6. THE 1,500-SEAT SKOURAS / ATMOSPHERIC AUDITORIUM
# Auditorium Shell: x = -94 .. -14 (80 ft clear width, CL = -54), y = 38 .. 152 (114 ft to Plaster Line), z = 0 .. 51 ft!
# Outer Structural Walls (West x = -96..-94, East x = -14..-12.5, Roof z = 49..51)
box(-96.0, 37.0, 0.5, -94.0, 152.0, 51.0, STUCCO, {"e": "fx_drapered"})
box(-14.0, 37.0, 16.0, -12.5, 152.0, 51.0, STUCCO, {"w": "fx_drapered"})
box(-14.0, 37.0, 0.5, -13.0, 152.0, 16.0, "fx_drapered")
box(-96.0, 37.0, 49.0, -12.5, 152.0, 51.0, "bk_roof", {"b": tspec("fx_skyceil", 22)})

# East Auditorium Exterior Wall Pilasters & THE EIGHT SALMON-PEACH CHURRIGUERESQUE FINIALS (gal_023.jpg & gal_038.jpg)!
prop(-13.2, 37.0, 51.0, -11.8, 152.0, 52.0, TILE)                                                # Dark terracotta East parapet coping (gal_023)
prop(-96.2, 37.0, 51.0, -94.8, 152.0, 52.0, STUCCO)
# Low 2nd-story cream parapet + red Spanish clay tile ridge flush behind the extended H St Marquee (y = 22.5 .. 55.5, gal_023.jpg!)
prop(-13.0, 22.5, 16.0, 0.2, 55.5, 25.5, STUCCO)
prop(-13.2, 22.5, 25.5, 0.6, 55.8, 26.3, TILE)
for py in (34.5, 50.7, 66.9, 83.1, 99.3, 115.5, 131.7, 148.0):
    pz0 = 26.3 if py < 56.0 else 16.0
    prop(-12.5, py - 1.1, pz0, -11.2, py + 1.1, 52.0, PEACH)                                     # Salmon-peach vertical pilaster (gal_023)
    pinnacle(-12.0, py, 52.0, 6.2, PEACH, body_tex=PEACH)                                        # Salmon-peach sculpted finial!

# Rear Orchestra / Balcony Partition Wall at y = 37.0 .. 38.2:
# - Ground level (z = 0.52 .. 15.0): 4 symmetrical walk-through Orchestra Double-Doors (6.0ft wide x 9.5ft tall)
# - Mezzanine level (z = 20.8 .. 30.0): 2 wide Balcony Vomitory Portals (x = -80..-73 & x = -35..-28)!
# - Booth level (z = 32.0 .. 49.0): Projection Booth window ports + Upper Balcony aisle door at x = -72.0..-66.8!
wall_x(-94.0, -14.0, 37.0, 1.2, 0.52, 19.8, LOBWALL,
       faces={"s": LOBWALL, "n": STUCCO_DK},
       holes=[(-91.0, -85.0, 0.52, 10.2), (-68.5, -62.5, 0.52, 10.2),
              (-45.5, -39.5, 0.52, 10.2), (-23.0, -17.0, 0.52, 10.2)])
wall_x(-94.0, -14.0, 37.0, 1.2, 19.8, 32.0, STUCCO,
       faces={"s": LOBWALL, "n": STUCCO_DK},
       holes=[(-80.0, -73.0, 20.8, 29.5), (-35.0, -28.0, 20.8, 29.5)])
wall_x(-94.0, -14.0, 37.0, 1.2, 32.0, 49.0, STUCCO,
       faces={"s": STUCCO, "n": STUCCO_DK},
       holes=[(-64.5, -40.0, 34.5, 38.0), (-72.0, -66.8, 32.0, 40.5)])                          # Projection Booth portholes + West aisle door!

# Glowing EXIT signs over all 4 Rear Orchestra Double-Doors (site_img_25.png)
for ex_x in (-88.0, -65.5, -42.5, -20.0):
    prop(ex_x - 1.1, 38.2, 10.4, ex_x + 1.1, 38.4, 11.4, "fx_bronze", {"n": Fit("fx_exit")})

# --- Smooth Doorway Threshold Steps (z = 0.52 -> 2.02 ft, 3 x 0.50ft = 6u risers) + Sloped Orchestra Rake ---
for door_x0, door_x1 in ((-91.0, -85.0), (-68.5, -62.5), (-45.5, -39.5), (-23.0, -17.0)):
    prop(door_x0, 37.0, 0.0, door_x1, 37.9, 1.02, CARPET)
    prop(door_x0, 37.9, 0.0, door_x1, 38.8, 1.52, CARPET)
box(-94.0, 38.2, 0.0, -91.0, 39.7, 2.02, CARPET)
box(-85.0, 38.2, 0.0, -68.5, 39.7, 2.02, CARPET)
box(-62.5, 38.2, 0.0, -45.5, 39.7, 2.02, CARPET)
box(-39.5, 38.2, 0.0, -23.0, 39.7, 2.02, CARPET)
box(-17.0, 38.2, 0.0, -14.0, 39.7, 2.02, CARPET)
for door_x0, door_x1 in ((-91.0, -85.0), (-68.5, -62.5), (-45.5, -39.5), (-23.0, -17.0)):
    prop(door_x0, 38.8, 0.0, door_x1, 39.7, 2.02, CARPET)
box(-94.0, 39.7, 0.0, -14.0, 46.0, 2.02, CARPET)                                                # Rear cross-aisle promenade (z = 2.02 ft)
for r_step in range(10):
    ry0 = 46.0 + r_step * 9.05
    ry1 = 46.0 + (r_step + 1) * 9.05
    rz = 2.02 - (r_step + 1) * 0.15
    box(-94.0, ry0, 0.0, -14.0, ry1, max(0.52, rz), CARPET, group="detail", solid=True)
box(-94.0, 38.2, 0.0, -14.0, 136.5, 0.52, CARPET)                                               # Base structural orchestra slab
box(-94.0, 136.5, -4.5, -71.0, 152.0, 0.52, CARPET)                                             # Front-West Orchestra slab flanking Pit!
box(-37.0, 136.5, -4.5, -14.0, 152.0, 0.52, CARPET)                                             # Front-East Orchestra slab flanking Pit!

# Orchestra Seating Rows: 3 Sections (C: -87.8..-69.2, B: -61.8..-46.2, A: -38.8..-20.2) separated by 4 wide (5.2ft-7ft) carpeted aisles!
# Notice Section B rear (y = 46..54) is left open for the Touring FOH Mix Booth (90' from DS edge y=148 -> y=58!!)!
SEAT_FACES = {"n": tspec("fx_seatback", 5.5), "s": tspec("fx_seatback", 5.5), "e": Fit("fx_seatarm"), "w": Fit("fx_seatarm")}
for row_i in range(21):
    ry = 55.0 + row_i * 3.75
    rz_base = max(0.52, 2.02 - int((ry - 46.0) / 9.05 + 1) * 0.15)
    taper = max(0.0, (ry - 115.0) * 0.22)                                                       # Front rows taper inward per seating_chart.png!
    # Section B (Center Orchestra)
    prop(-61.8 + taper * 0.4, ry, rz_base, -46.2 - taper * 0.4, ry + 1.5, rz_base + 2.7, "fx_drapered", SEAT_FACES)
    prop(-61.8 + taper * 0.4, ry + 1.5, rz_base, -46.2 - taper * 0.4, ry + 2.4, rz_base + 1.45, "fx_drapered")
    # Section C (West) & Section A (East)
    if -87.8 + taper < -69.2:
        prop(-87.8 + taper, ry, rz_base, -69.2, ry + 1.5, rz_base + 2.7, "fx_drapered", SEAT_FACES)
        prop(-87.8 + taper, ry + 1.5, rz_base, -69.2, ry + 2.4, rz_base + 1.45, "fx_drapered")
    if -38.8 < -20.2 - taper:
        prop(-38.8, ry, rz_base, -20.2 - taper, ry + 1.5, rz_base + 2.7, "fx_drapered", SEAT_FACES)
        prop(-38.8, ry + 1.5, rz_base, -20.2 - taper, ry + 2.4, rz_base + 1.45, "fx_drapered")

# Touring FOH Sound & Lighting Mix Booth (90' from DS stage edge: x = -62..-46, y = 46..54, Production Pack Page 16!)
prop(-62.0, 53.4, 1.85, -46.0, 54.0, 5.0, "fx_bronze")                                          # Retaining wall
prop(-62.0, 46.5, 1.85, -61.4, 54.0, 5.0, "fx_bronze")
prop(-46.6, 46.5, 1.85, -46.0, 54.0, 5.0, "fx_bronze")
prop(-60.0, 50.2, 1.85, -48.0, 53.2, 4.6, "fx_drapeblk", {"t": Fit("fx_console", (2, 1))})      # Glowing Midas M32 + Avolites Sapphire!

# --- Cantilevered Balcony (y = 38.2 .. 70.7 — exactly 77'4" from DS edge y=148, Production Pack Page 15!) ---
# Balcony underside soffit + 4 Art Deco saucer dome lights (site_img_25.png)
box(-94.0, 38.2, 15.2, -14.0, 70.7, 16.5, STUCCO_DK, {"b": STUCCO})
for sx in (-82.0, -63.0, -45.0, -26.0):
    frustum_ring(sx, 58.0, 1.8, 0.5, 14.5, 15.2, "fx_goldleaf", sides=8)
    light(sx, 58.0, 13.6, 130, "255 228 186")

# Gently-curved Ivory Art Moderne Balcony Front Fascia with 18 Leko Spotlight Ports (z = 15.6 .. 19.4, site_img_25.png)
for seg_x0, seg_x1, seg_y in ((-94.0, -72.0, 71.2), (-72.0, -36.0, 70.6), (-36.0, -14.0, 71.2)):
    prop(seg_x0, seg_y - 0.8, 15.6, seg_x1, seg_y, 19.4, STUCCO, {"n": Fit("fx_balcfasc", (4, 1)), "t": "fx_goldleaf"})

# Lower Balcony / Loge (4 stepped tiers y = 54.5 .. 66.5 + 3.5ft walkable front rail promenade y = 66.5 .. 70.0, z = 17.3 -> 21.8!)
box(-94.0, 66.5, 16.5, -14.0, 70.0, 17.3, CARPET, group="detail", solid=True)                   # 3.5ft walkable front balcony overlook!
for b_i in range(4):
    by0 = 66.5 - (b_i + 1) * 3.0
    by1 = 66.5 - b_i * 3.0
    bz_top = 18.2 + b_i * 0.90
    box(-94.0, by0, 16.5, -14.0, by1, bz_top, CARPET, group="detail", solid=True)
    # Intermediate aisle half-steps (riser = 0.45 ft = 5.4 Quake units!) along all 4 aisles
    for ax0, ax1 in ((-94.0, -89.0), (-69.0, -62.0), (-46.0, -39.0), (-19.0, -14.0)):
        prop(ax0, by1, 16.5, ax1, by1 + 0.9, bz_top - 0.45, CARPET)
    for bx0, bx1 in ((-89.0, -69.0), (-62.0, -46.0), (-39.0, -19.0)):
        prop(bx0, by0 + 0.4, bz_top, bx1, by0 + 1.8, bz_top + 2.5, "fx_drapered", SEAT_FACES)

# Balcony Cross-Aisle (y = 50.0 .. 54.5, z = 21.8 ft) + Vomitory Ramps from Mezzanine (z = 20.8 -> 21.8)!
box(-94.0, 50.0, 16.5, -14.0, 54.5, 21.8, CARPET, group="detail", solid=True)
for vx0, vx1 in ((-80.0, -73.0), (-35.0, -28.0)):
    prism([(vx0, 38.2), (vx1, 38.2), (vx1, 50.0), (vx0, 50.0)],
          [16.5, 16.5, 16.5, 16.5], [20.8, 20.8, 21.8, 21.8], CARPET, group="detail", solid=True)
    # Vomitory flanking walls so Upper Balcony steps don't spill into vomitory tunnels!
    prop(vx0 - 0.8, 38.2, 20.8, vx0, 50.0, 31.0, STUCCO_DK, {"w": "fx_drapered", "e": LOBWALL})
    prop(vx1, 38.2, 20.8, vx1 + 0.8, 50.0, 31.0, STUCCO_DK, {"e": "fx_drapered", "w": LOBWALL})

# Upper Balcony (6 tiers, y = 38.2 .. 50.0, z = 22.5 -> 29.35 ft, with 5.2ft-wide aisles + 0.68ft intermediate aisle steps!)
for u_i in range(6):
    uy0 = 50.0 - (u_i + 1) * 1.95
    uy1 = 50.0 - u_i * 1.95
    uz = 22.5 + u_i * 1.37
    for ux0, ux1 in ((-94.0, -80.8), (-72.2, -35.8), (-27.2, -14.0)):
        box(ux0, uy0, 16.5, ux1, uy1, uz, CARPET, group="detail", solid=True)
    for ax0, ax1 in ((-72.2, -67.0), (-41.0, -35.8)):
        prop(ax0, uy1, 16.5, ax1, uy1 + 0.95, uz - 0.68, CARPET)
    for sx0, sx1 in ((-67.0, -41.0), (-26.0, -16.0), (-92.5, -82.0)):
        if u_i < 5:
            prop(sx0, uy0 + 0.3, uz, sx1, uy0 + 1.4, uz + 2.4, "fx_drapered", SEAT_FACES)
# 4 smooth steps at top of West Upper Balcony Aisle (x = -72.2..-67.0, y = 37.8..40.2) + LOBWALL-faced threshold sill (no carpet bleed on y=37!)
for ub_s in range(4):
    prop(-72.2, 40.2 - (ub_s + 1) * 0.6, 29.35, -67.0, 40.2 - ub_s * 0.6, 29.35 + (ub_s + 1) * 0.6625, CARPET)
prop(-72.2, 37.0, 30.8, -66.8, 37.8, 32.0, CARPET, {"s": LOBWALL, "b": LOBWALL})

# Projection & Followspot Booth Room behind Upper Balcony (x = -85 .. -38, y = 26 .. 37, floor z = 32.0, ceiling z = 41.0)
# Underside y = 26.0..33.8 uses painted Sky-Blue Fresco (LOBCEIL), while y = 33.8..37.0 forms the cream plaster North soffit beam (gal_114)!
box(-79.6, 26.0, 30.8, -38.0, 33.8, 32.0, "fx_stageflr", {"b": LOBCEIL})
box(-79.6, 33.8, 30.2, -38.0, 37.0, 32.0, "fx_stageflr", {"b": LOBWALL, "s": LOBWALL})
box(-85.0, 32.6, 30.8, -79.6, 37.0, 32.0, "fx_stageflr", {"b": LOBCEIL})
for pb_s in range(16):
    sy0 = 27.4 + pb_s * (5.2 / 16)
    sz_top = 20.8 + (pb_s + 1) * (11.2 / 16)
    prop(-84.7, sy0, max(20.8, sz_top - 1.5), -79.7, sy0 + (5.2 / 16), sz_top, "fx_stageflr")
box(-86.0, 25.0, 41.0, -37.0, 38.2, 42.5, STUCCO, {"b": LOBWALL})
box(-79.6, 25.0, 30.8, -38.0, 26.0, 41.0, STUCCO, {"n": LOBWALL, "s": STUCCO})
box(-86.0, 25.0, 35.0, -79.6, 26.0, 41.0, STUCCO, {"n": LOBWALL, "s": STUCCO})                   # Full 14ft headroom over stairwell entry!
box(-86.0, 25.0, 30.8, -84.8, 37.0, 41.0, STUCCO, {"e": LOBWALL})
box(-38.0, 25.0, 30.8, -37.0, 37.0, 41.0, STUCCO, {"w": LOBWALL, "e": LOBWALL})
# Mullions between Projection & Spot Booth portholes (site_img_25.png) + Christie CP4220 Projector & Lycian Followspots!
for pmx in (-61.0, -56.5, -52.5, -48.5, -44.0):
    prop(pmx - 0.4, 37.0, 34.5, pmx + 0.4, 38.2, 38.0, STUCCO_DK)
prop(-55.5, 31.0, 32.0, -51.5, 35.8, 36.2, "bk_steel")                                          # Christie CP4220 22k projector
for spx in (-63.0, -58.8, -46.5, -42.0):
    prop(spx - 0.6, 33.5, 32.0, spx + 0.6, 36.2, 35.8, "fx_bronze")                             # 4 Lycian Super Star 2.5 followspots!
light(-54.0, 32.0, 39.5, 145, "200 220 255")

# --- 1953 Carl Moeller / Charles Skouras Gilded Side Murals, Champagne-Gold Splay Drapes & Atmospheric Sky Ceiling ---
for side_x, face_in, sgn in ((-94.0, "e", 1.0), (-14.0, "w", -1.0)):
    # Two grand Skouras Gold Rococo Scroll + Crimson Diamond-Tufted Trellis Bays (y = 56..90 & 92..126)
    for my0, my1 in ((56.0, 90.0), (92.0, 126.0)):
        x_lo, x_hi = sorted((side_x, side_x + sgn * 0.6))
        prop(x_lo, my0, 5.0, x_hi, my1, 43.0, "fx_drapered", {face_in: Fit("fx_skscroll")})
        # 3D sculpted gold-leaf scroll pilasters framing the bays (1.0ft proud so outer aisles are 5.2ft wide!)
        px_lo, px_hi = sorted((side_x, side_x + sgn * 1.0))
        prop(px_lo, my0 - 1.2, 3.0, px_hi, my0 + 1.2, 43.5, "fx_goldleaf")
    # Splayed Champagne-Gold Proscenium Flanking Curtain Walls (converging from x=-94/-14 at y=126 to x=-78/-30 at y=151!)
    x_pros = -78.0 if sgn > 0 else -30.0
    poly_splay = [(side_x, 126.0), (side_x + sgn * 1.5, 126.0), (x_pros, 151.0), (x_pros - sgn * 1.5, 151.0)]
    prism(poly_splay, 0.52, 44.0, tspec("fx_drapegld", 6), side=tspec("fx_drapegld", 6), group="detail", solid=True)
    # Crimson Velvet Scalloped Upper Festoon Swags along Splay Walls (swooping z = 43.2 down to 26.8, matching site_img_35.png!)
    for f_bay in range(2):
        for f_sub, z_dip in ((0, 29.8), (1, 26.8), (2, 29.8)):
            t0 = (f_bay * 3 + f_sub) / 6.0
            t1 = (f_bay * 3 + f_sub + 1) / 6.0
            ya, yb = 126.0 + 25.0 * t0, 126.0 + 25.0 * t1
            xa = side_x + (x_pros - side_x - sgn * 1.5) * t0 + sgn * 1.5
            xb = side_x + (x_pros - side_x - sgn * 1.5) * t1 + sgn * 1.5
            f_poly = [(xa, ya), (xa + sgn * 0.65, ya), (xb + sgn * 0.65, yb), (xb, yb)]
            prism(f_poly, z_dip, 43.4, tspec("fx_drapered", 5), side=tspec("fx_drapered", 5), group="detail", solid=False)
    # Gold Cove Cornice following the splayed wall angle right up to the Proscenium!
    c_poly = [(side_x, 126.0), (side_x + sgn * 2.4, 126.0), (x_pros + sgn * 0.9, 151.0), (x_pros - sgn * 1.5, 151.0)]
    prism(c_poly, 43.2, 44.8, "fx_goldleaf", side="fx_goldleaf", group="detail", solid=False)
    # Recessed EXIT sign portals near front of auditorium (matching site_img_35.png!)
    ex_x0, ex_x1 = sorted((side_x + sgn * 3.0, side_x + sgn * 4.5))
    prop(ex_x0, 131.5, 8.8, ex_x1, 133.5, 9.8, "fx_bronze", {face_in: Fit("fx_exit")})

# Gold Cove-Lit Cornice & Vaulted Indigo Starlit Atmospheric Ceiling (z = 43.5 .. 49.0, site_img_35.png!)
prop(-94.0, 38.2, 43.2, -91.5, 126.0, 44.8, "fx_goldleaf")
prop(-16.5, 38.2, 43.2, -14.0, 126.0, 44.8, "fx_goldleaf")
prop(-94.0, 38.2, 43.2, -14.0, 40.5, 44.8, "fx_goldleaf")
prop(-79.5, 149.2, 43.2, -28.5, 151.0, 44.8, "fx_goldleaf")
# Royal-blue perimeter atmospheric sky cove + warm house lights!
for ay in (52.0, 78.0, 104.0, 128.0, 144.0):
    cove_x_off = 32.0 if ay < 126.0 else 21.0
    light(-54.0 - cove_x_off, ay, 46.2, 195, "110 126 255")                                     # West royal-blue sky cove wash
    light(-54.0 + cove_x_off, ay, 46.2, 195, "110 126 255")                                     # East royal-blue sky cove wash
    light(-54.0, ay, 46.5, 175, "128 142 255")                                                  # Center atmospheric indigo sky glow
for ay in (58.0, 82.0, 108.0, 130.0):
    light(-88.5, ay, 25.0, 165, "255 208 142")                                                  # Warm gold Skouras scroll uplights
    light(-19.5, ay, 25.0, 165, "255 208 142")
# Warm Auditorium House Downlights over Orchestra Aisles & Balcony Rows (makes plush red seats & floral carpet glow like site_img_35!)
for hy in (64.0, 84.0, 104.0, 124.0):
    light(-65.5, hy, 22.0, 265, "255 232 192")
    light(-42.5, hy, 22.0, 265, "255 232 192")
    light(-65.5, hy, 9.5, 165, "255 224 178")
    light(-42.5, hy, 9.5, 165, "255 224 178")
    if hy > 72.0:
        light(-54.0, hy, 18.0, 185, "255 226 184")
for by in (47.0, 62.0):
    light(-66.0, by, 36.0, 220, "255 230 192")
    light(-42.0, by, 36.0, 220, "255 230 192")


# ============================================================================== 7. PROSCENIUM, PIT, 60' FLY STAGE, GREEN ROOM & DRESSING ROOMS
# Stagehouse Exterior Shell: x = -96 .. -14, y = 152 .. 196, z = 0.5 .. 66.0 ft (60' interior grid height!)
wall_y(-96.0, 2.0, 152.0, 196.0, 0.5, 66.0, STUCCO, faces={"e": STUCCO_DK, "w": STUCCO},
       holes=[(162.0, 170.0, 3.8, 17.3), (178.5, 184.5, 0.5, 9.5)])                             # 8'x13'6" Alley Loading Door + 6'x9' Stage Door!
box(-96.0, 194.0, 0.5, -14.0, 196.0, 66.0, STUCCO, {"s": STUCCO_DK})
box(-15.5, 152.0, 29.0, -14.0, 196.0, 66.0, STUCCO, {"w": STUCCO_DK, "e": STUCCO})
box(-96.0, 150.0, 51.0, -14.0, 152.5, 66.0, STUCCO)
box(-96.0, 150.0, 64.5, -14.0, 196.0, 66.5, "bk_roof", {"b": "bk_steel"})

# Alley Loading Roll-Up Door (8' W x 13'6" H, Production Pack Page 4) + Walk-in Stage Door + Shore Power!
prop(-95.8, 162.0, 3.8, -94.8, 170.0, 17.3, "bk_steel", {"w": tspec("fx_rollup", 6), "e": tspec("fx_rollup", 6)})
prop(-96.3, 173.0, 4.0, -95.9, 174.5, 5.8, "bk_steel")                                          # 50A Shore Power box (Page 5)
# Interior 6ft-wide steps inside Stage Door (y = 178.5..184.5) rising z = 0.5 -> 3.8 ft onto Stage Right (riser = 0.66ft = 7.9u)!
for sd_i in range(5):
    prop(-94.0 + sd_i * 1.2, 178.5, 0.5, -94.0 + (sd_i + 1) * 1.2, 184.5, 0.5 + (sd_i + 1) * 0.66, "fx_stageflr")

# Proscenium Arch Wall at y = 151.0 .. 153.0: 48' W x 27' H opening (x = -78 .. -30, z = 3.8 .. 30.8)!
wall_x(-94.0, -14.0, 151.0, 2.0, 0.5, 49.0, STUCCO_DK,
       faces={"s": tspec("fx_drapegld", 6), "n": STUCCO_DK},
       holes=[(-78.0, -30.0, 3.8, 30.8)])
# 5 Scalloped Crimson-over-Champagne-Gold Grand Valance Swags across the Proscenium (site_img_35.png)!
for sw_i in range(5):
    sx0 = -78.0 + sw_i * 9.6
    for sub_k, (dz_r, dz_g) in enumerate(((1.4, 1.4), (0.0, 0.0), (1.4, 1.4))):
        xa = sx0 + sub_k * 3.2
        xb = xa + 3.2
        prop(xa, 150.0, 26.2 + dz_r, xb, 151.0, 31.4, tspec("fx_drapered", 5))
        prop(xa + 0.15, 150.4, 24.0 + dz_g, xb - 0.15, 151.2, 26.8 + dz_r, tspec("fx_drapeblk" if False else "fx_drapegld", 5))

# THE MONUMENTAL 9-PLUME GILDED GOLD SUNBURST PROSCENIUM CROWN (site_img_35.png, z = 31.2 .. 45.4)!
prop(-61.5, 149.1, 31.2, -46.5, 150.6, 34.6, "fx_goldleaf")                                     # Sculpted central shell base
plume_heights = [36.2, 38.4, 40.8, 43.2, 45.4, 42.8, 40.4, 38.2, 36.0]
for p_i, ph in enumerate(plume_heights):
    px0 = -65.2 + p_i * 2.5
    prop(px0, 149.3, 31.2, px0 + 2.3, 150.8, ph, "fx_goldleaf")
# Dedicated warm golden spotlights illuminating the 9-plume Sunburst Crown & Grand Valance!
light(-59.5, 145.5, 39.0, 275, "255 214 118")
light(-48.5, 145.5, 39.0, 275, "255 214 118")

# --- Recessed Orchestra Pit (x = -71 .. -37, y = 136.5 .. 148.5, floor z = -3.5) ---
# Includes solid Pit floor slab + two 5.5ft-wide Main-Aisle walk-in staircases (x = -68.5..-63.0 & -45.0..-39.5)!
box(-71.2, 136.0, -4.5, -36.8, 152.0, -3.5, "fx_stageflr")                                        # Solid Orchestra Pit floor slab!
prop(-63.0, 136.5, -3.5, -45.0, 137.3, 1.9, "fx_bronze")                                          # Center Pit bronze parapet wall
prop(-71.0, 136.5, -3.5, -68.5, 137.3, 1.9, "fx_bronze")
prop(-39.5, 136.5, -3.5, -37.0, 137.3, 1.9, "fx_bronze")
prop(-71.0, 136.5, -3.5, -70.2, 148.5, 1.9, "fx_bronze")
prop(-37.8, 136.5, -3.5, -37.0, 148.5, 1.9, "fx_bronze")
# 2 L'Acoustics KS28 Subwoofers in the pit (Production Pack Page 19) + 5.5ft-wide Main-Aisle Pit stairs (riser = 0.67ft = 8u)!
for sub_x in (-59.0, -49.0):
    prop(sub_x - 1.8, 145.2, -3.5, sub_x + 1.8, 147.4, -1.0, "fx_drapeblk")
for st_k in range(6):
    # Steps descend North from y = 136.5 (z = 0.52) into Pit at y = 142.5 (z = -3.5) along Left (-68.5..-63) & Right (-45..-39.5) Main Aisles!
    sy0 = 136.5 + st_k * 1.0
    sz_top = 0.52 - (st_k + 1) * (4.02 / 6)
    if sz_top > -3.45:
        prop(-68.5, sy0, -3.5, -63.0, sy0 + 1.0, sz_top, "fx_stageflr")
        prop(-45.0, sy0, -3.5, -39.5, sy0 + 1.0, sz_top, "fx_stageflr")

# --- Stage Deck (z = 3.8 ft, with Stage Door Stairwell Notch at x = -94..-88, y = 178.2..184.8 so Stage Door walks straight up!) ---
box(-94.0, 152.0, 0.0, -88.0, 178.2, 3.8, tspec("fx_stageflr", 8))
box(-94.0, 184.8, 0.0, -88.0, 194.0, 3.8, tspec("fx_stageflr", 8))
box(-88.0, 152.0, 0.0, -15.5, 194.0, 3.8, tspec("fx_stageflr", 8))
box(-94.0, 178.2, 0.0, -88.0, 184.8, 0.5, tspec("fx_stageflr", 8))                                # Sub-landing under Stage Door steps
prism([(-78.0, 152.0), (-77.5, 148.5), (-62.0, 147.8), (-46.0, 147.8), (-30.5, 148.5), (-30.0, 152.0)],
      -3.5, 3.8, tspec("fx_stageflr", 8), side="fx_bronze", group="detail", solid=True)
# Wide 5.7ft Stage Apron Stairs inside Proscenium width (x = -77.5..-71.8 & -36.2..-30.5, y = 141.3 -> 148.5, riser = 0.55ft = 6.6u)!
for s_k in range(6):
    sy0 = 141.3 + s_k * 1.2
    sz = 0.52 + (s_k + 1) * (3.28 / 6)
    prop(-77.5, sy0, 0.52, -71.8, sy0 + 1.2, sz, "fx_stageflr")
    prop(-36.2, sy0, 0.52, -30.5, sy0 + 1.2, sz, "fx_stageflr")

# Flown L'Acoustics Kara II Line-Array Speaker Hangs (Production Pack Page 19)
for pa_x in (-76.5, -31.5):
    prop(pa_x - 1.2, 148.5, 17.5, pa_x + 1.2, 150.5, 25.5, "fx_drapeblk")

# 40' Aluminum Downstage Box Lighting Truss hung 16' south of DS edge (y = 132, z = 33.5..35.2, Page 14 & 15)!
box(-74.0, 131.5, 33.5, -34.0, 131.7, 35.2, Fit("{fx_truss", (8, 1)), group="fence")
box(-74.0, 132.8, 33.5, -34.0, 133.0, 35.2, Fit("{fx_truss", (8, 1)), group="fence")
for mot_x in (-68.0, -40.0):
    prop(mot_x - 0.12, 132.1, 35.2, mot_x + 0.12, 132.35, 49.0, "bk_steel")                     # 1-ton chain hoist cables

# Black Theatrical Legs, Borders & 21' x 46' Silver Cinema Screen (Production Pack Pages 11 & 23)!
for leg_y in (159.0, 167.0, 175.0):
    prop(-81.0, leg_y, 3.8, -76.5, leg_y + 0.5, 34.0, tspec("fx_drapeblk", 6))
    prop(-31.5, leg_y, 3.8, -27.0, leg_y + 0.5, 34.0, tspec("fx_drapeblk", 6))
    prop(-81.0, leg_y, 30.5, -27.0, leg_y + 0.5, 35.5, tspec("fx_drapeblk", 6))
# 21' H x 46' W Cinema Screen at y = 180.0 framed by black traveler backdrop!
prop(-82.0, 180.6, 3.8, -26.0, 181.4, 34.0, tspec("fx_drapeblk", 6))
prop(-77.0, 180.0, 6.8, -31.0, 180.6, 27.8, "fx_drapeblk", {"s": Fit("fx_screen")})
# 60' Steel Fly Gridiron Beams at z = 63.0
for gx in range(-90, -18, 12):
    prop(gx, 153.0, 62.8, gx + 0.8, 193.0, 63.8, "bk_steel")
for sx in (-68.0, -54.0, -40.0):
    light(sx, 158.0, 29.0, 210, "255 242 215")
    light(sx, 172.0, 26.0, 175, "215 228 255")

# --- Stage Left Wing: Green Room (Stage Level, 12'x20') & Upstairs Dressing Rooms (x = -15.5 .. 0, y = 152 .. 196, gal_038.jpg!) ---
# Exterior H St wall & South Spanish-Gabled Storefront Bay (y = 154..174) + North Dressing Wing (y = 174..196) matching gal_038.jpg!
box(-15.5, 152.0, 0.5, 0.0, 154.0, 29.2, STUCCO)
box(-1.0, 154.0, 0.5, 0.0, 196.0, 29.0, STUCCO)
box(-15.5, 194.5, 0.5, 0.0, 196.0, 29.0, STUCCO)
box(-15.5, 154.0, 28.0, 0.0, 196.0, 29.2, STUCCO, {"t": "bk_roof"})
# Stepped Spanish Gable Parapet + Red Tile Coping + Red Awning on South Half of Stage-Left Wing (gal_038.jpg!)
prop(-1.2, 155.0, 29.2, 0.5, 173.0, 31.2, STUCCO)
prop(-1.3, 160.0, 31.2, 0.6, 168.0, 32.8, STUCCO)
prop(-1.4, 154.8, 31.2, 0.7, 160.2, 31.8, TILE)
prop(-1.4, 167.8, 31.2, 0.7, 173.2, 31.8, TILE)
prop(-1.5, 159.8, 32.8, 0.8, 168.2, 33.4, TILE)
prop(-0.2, 156.5, 2.0, 0.3, 171.5, 9.0, "fx_bronze", {"e": Fit("fx_shopwin")})
prop(-0.2, 156.5, 0.5, 0.35, 171.5, 2.0, PEACH)
awning_y(0.0, 156.0, 172.0, z0=9.2, z1=11.6)
for wy in (157.0, 162.5, 168.0):
    prop(-0.2, wy, 17.5, 0.3, wy + 3.2, 24.5, STUCCO_DK, {"e": Fit("fx_lancet")})
for wy in (178.0, 187.0):
    prop(-0.2, wy, 17.8, 0.25, wy + 3.8, 23.2, STUCCO_DK, {"e": Fit("fx_lancet")})
# Partition between Stage Left Wing and Green Room / Backstage Stair (x = -15.5 .. -14.5)
wall_y(-15.5, 1.0, 154.0, 194.5, 3.8, 28.0, STUCCO_DK,
       holes=[(162.0, 168.0, 3.8, 12.0), (188.5, 194.2, 3.8, 12.0)])                            # Wide 5.7ft doors to Green Room & Backstage Stair!
box(-14.5, 154.0, 0.0, -1.0, 194.5, 3.8, "fx_stageflr")
box(-14.5, 154.0, 15.2, -1.0, 176.0, 16.2, "fx_stageflr", {"b": LOBWALL})                       # Upstairs Dressing Room floor!
box(-14.5, 175.2, 3.8, -1.0, 176.0, 15.2, "fx_greenrm")

# Green Room Interior (x = -14.5 .. -1.0, y = 154 .. 175.2, z = 3.8 .. 15.2 — guitars & Chesterfield sofa, Page 11!)
prop(-1.5, 155.5, 4.5, -1.0, 174.0, 13.8, "fx_greenrm", {"w": Fit("fx_greenrm", (2, 1))})
prop(-14.2, 154.5, 4.5, -1.5, 155.0, 13.8, "fx_greenrm", {"n": Fit("fx_greenrm", (1.4, 1))})
fox_model("pad_sofa_leather", -3.0, 160.2, 3.8, yaw=180,
          clip_box=(-4.3, 156.8, 4.2, -1.7, 163.6, 5.8))
fox_model("fox_guitar", -11.5, 156.2, 3.8, yaw=75)
fox_model("fox_guitar", -8.5, 156.0, 3.8, yaw=95)
fox_model("fox_guitar", -2.8, 172.8, 3.8, yaw=215)
light(-7.8, 159.5, 13.8, 235, "250 242 222")
light(-7.8, 170.0, 13.8, 225, "250 242 222")

# Backstage Stair (y = 176.0 .. 188.5, spacious 13.5x6.0ft bottom landing at y = 188.5..194.5, 12ft-wide steps rising z = 3.8 -> 16.2)!
for dr_k in range(18):
    sy0 = 188.5 - (dr_k + 1) * (12.5 / 18)
    prop(-13.5, sy0, 3.8, -1.5, sy0 + (12.5 / 18), 3.8 + (dr_k + 1) * (12.4 / 18), "fx_stageflr")
# Upstairs Stage-Left Dressing Rooms (z = 16.2 .. 28.0 — Hollywood vanity mirrors with warm vertical sconces, Page 10!)
prop(-1.6, 156.0, 19.5, -1.0, 173.0, 24.2, TERRA, {"w": Fit("fx_vanity", (2, 1))})
prop(-3.4, 156.0, 16.2, -1.0, 173.0, 18.8, TERRA)                                               # Marble makeup counter
light(-7.5, 159.5, 26.2, 245, "255 228 194")
light(-7.5, 170.0, 26.2, 235, "255 228 194")


# ============================================================================== 8. ROOF / TOWER JUMP PADS, LIFT & GAMEPLAY ENTITIES
# Discreet jump pads in the West Alley & Auditorium Roof + Stagehand Tower Lift so players can battle up to the Clock Tower!
prop(-103.0, 136.0, 0.5, -98.0, 141.0, 0.9, "fx_goldleaf")
brush_ent("trigger_push", -103.0, 136.0, 0.9, -98.0, 141.0, 5.0, angles="-78 0 0", speed="1180")
prop(-28.0, 30.0, 51.0, -23.0, 35.0, 51.4, "fx_goldleaf")
brush_ent("trigger_push", -28.0, 30.0, 51.4, -23.0, 35.0, 55.0, angles="-76 110 0", speed="920")
# Stage-Right Backstage Service Lift to Auditorium Roof & Clock Tower Deck:
prop(-93.2, 189.0, 3.8, -89.2, 193.0, 4.15, "fx_goldleaf")
brush_ent("trigger_teleport", -93.0, 189.2, 4.15, -89.4, 192.8, 10.5, target="tp_tower_deck")
ent("info_teleport_destination", -20.0, 33.0, 52.5, targetname="tp_tower_deck", angle=120)

# Player Start: exact postcard camera viewpoint across 20th St & H St looking NW at the Clock Tower & Fox Marquee!
if os.environ.get("FOX_START"):
    _vals = [float(v) for v in os.environ["FOX_START"].split()]
    if len(_vals) >= 5:
        ent("info_player_start", _vals[0], _vals[1], _vals[2], angles=f"{_vals[4]:.1f} {_vals[3]:.1f} 0")
    else:
        ent("info_player_start", _vals[0], _vals[1], _vals[2], angle=int(_vals[3]))
else:
    ent("info_player_start", 44.0, -52.0, 2.5, angle=132)

# 12 Deathmatch Spawns across exterior streets, lobby, mezzanine, orchestra, stage, balcony & backstage!
DM_SPAWNS = [
    (44.0, -52.0, 2.5, 132),        # 20th & H St postcard corner
    (-72.0, -36.0, 2.5, 45),        # 20th St near HOPE street clock
    (42.0, 96.0, 2.5, 220),         # H St in front of Spanish storefronts
    (-8.5, 18.0, 2.8, 180),         # Under the Marquee (Terrazzo Vestibule)
    (-56.0, 15.0, 2.8, 0),          # Main Lobby in front of 1953 Concession Stand
    (-54.0, 32.5, 23.2, 90),        # Upper Mezzanine Promenade
    (-65.5, 84.0, 3.8, 90),         # Orchestra Left Main Aisle
    (-42.5, 84.0, 3.8, 90),         # Orchestra Right Main Aisle
    (-54.0, 164.0, 6.2, 270),       # Center Stage looking out at Auditorium!
    (-54.0, 52.5, 24.2, 90),        # Balcony Cross-Aisle overlooking Stage!
    (-8.0, 166.0, 6.2, 180),        # Stage Left Green Room
    (-114.0, 166.0, 2.5, 0),        # West Alley by Stage Door
]
for sx, sy, sz, sang in DM_SPAWNS:
    ent("info_player_deathmatch", sx, sy, sz, angle=sang)

# Weapons, Armor (including Yellow Armor = Jetpack in BakersfieldQuake!) & Pickups
ITEMS = [
    ("weapon_rocketlauncher", -54.0, 156.0, 5.2),       # Center Stage!
    ("weapon_lightning", -54.0, 44.0, 3.3),             # Rear Orchestra behind FOH Mix Booth
    ("weapon_supernailgun", -38.0, 16.0, 2.0),          # Main Lobby in front of Concessions
    ("weapon_grenadelauncher", -54.0, 142.0, -2.0),     # Recessed Orchestra Pit!
    ("weapon_supershotgun", -6.5, 50.0, 2.0),           # Eva's East Lobby Lounge
    ("weapon_nailgun", -112.0, 150.0, 1.5),             # West Alley Load-In
    ("item_armor2", -96.0, -5.5, 1.8),                  # Yellow Armor (Jetpack!) on 20th St sidewalk near HOPE Clock
    ("item_armor1", -54.0, 52.2, 23.0),                 # Green Armor on Balcony Cross-Aisle
    ("item_armorInv", -54.0, 29.5, 33.2),               # Red Armor up in the Projection Booth!
    ("item_armor2", -42.0, 29.8, 22.0),                 # Yellow Armor (Jetpack!) on spacious Mezzanine Promenade
    ("item_health", -65.5, 112.0, 2.0),
    ("item_health", -42.5, 112.0, 2.0),
    ("item_health", -8.0, 170.0, 5.2),
    ("item_health", -8.0, 168.0, 17.5),
    ("item_shells", -6.5, 58.0, 2.0),
    ("item_spikes", -70.0, 15.0, 2.0),
    ("item_rockets", -68.0, 164.0, 5.2),
    ("item_rockets", -40.0, 164.0, 5.2),
    ("item_cells", -65.5, 62.0, 2.8),
    ("item_cells", -42.5, 62.0, 2.8),
]
for iname, ix, iy, iz in ITEMS:
    ent(iname, ix, iy, iz)
ent("item_health", -54.0, 172.0, 5.2, spawnflags=2)     # Megahealth Upstage Center!

# Named Camera / Teleport Spots (Gallery Audit Viewpoints: Fox + Padre Hotel + G..K / 18th..21st!)
# Quake yaw = (90 - StreetView_compass_heading) % 360; negative pitch looks UP.
SPOTS = [
    ("01 Postcard 20th & H Corner", 52.0, -56.0, 5.2, 134, -10),
    ("02 Fox Front H St Marquee Up (fblk_020)", 44.0, 6.0, 5.2, 162, -18),
    ("03 Padre Hotel SE Corner 18th & H (padre_052/173)", 56.0, -722.0, 5.5, 132, -22),
    ("04 Padre 18th St Front 1702 & Farmacy (padre_028)", -68.0, -718.0, 5.5, 82, -16),
    ("05 Padre West Courtyard & Clover Ballroom", -126.0, -674.0, 5.2, 128, -8),
    ("06 Padre Grand Lobby & Cowgirl Mural (padre_171)", -61.5, -638.0, 5.2, 90, -2),
    ("07 Padre Brimstone Bar & Lounge (padre_188)", -32.0, -648.0, 5.2, 42, -2),
    ("08 Padre Sub-Grade 24-Hr Gym (padre_190)", -34.0, -618.0, -6.2, 315, 4),
    ("09 Padre Clover 1 & 2 Ballroom", -218.0, -634.0, 5.2, 0, -2),
    ("10 Padre Upper Lobby Mat & Horseshoe Wall", -36.0, -628.0, 21.5, 148, -2),
    ("11 Padre Conference Room Yellow Chairs", -64.0, -639.5, 21.5, 265, 6),
    ("12 Padre Prairie Fire Terrace -> Fox Tower", -92.0, -606.0, 21.5, 72, -10),
    ("13 Padre Room 406 Two Queens & Barn Door", -84.0, -644.0, 47.5, 225, 4),
    ("14 Padre Room 608 Sheer-Curtain Shower", -100.0, -626.0, 71.5, 0, 2),
    ("15 Padre Oil Baron Suite Jacuzzi", -62.0, -644.0, 71.5, 220, 4),
    ("16 Padre Farmer's Daughter Suite -> Fox View", -15.0, -614.0, 71.5, 88, -2),
    ("17 Padre 8th-Floor Rooftop & Neon Sign", -46.0, -646.0, 107.5, 38, -8),
    ("18 Nile Theater 19th St Marquee (fblk_133)", -178.0, -362.0, 5.5, 270, -8),
    ("19 Ovation Theatre & Tegeler 19th St (fblk_137)", 172.0, -388.0, 5.5, 78, -6),
    ("20 21st & H Central Fire & Today Cleaners", 44.0, 308.0, 5.5, 205, -6),
    ("21 18th & H Gear Mural SE Corner (fblk_343)", 32.0, -704.0, 5.5, 322, -6),
    ("22 Buena Vista Museum & GET Bus Chester (fblk_163)", 708.0, 112.0, 5.5, 48, -4),
    ("23 Woolworth's & S.H. Kress 19th & K (fblk_169)", 1074.0, -384.0, 5.5, 142, -8),
    ("24 The Mint Bar & Mi Casa East of K St", 1152.0, -366.0, 5.5, 255, -4),
    ("25 Auditorium Orchestra & 9-Plume Sunburst", -54.0, 44.5, 6.2, 90, -5),
    ("26 Main Lobby, Fresco Ceiling & Concessions", -76.0, 16.0, 5.0, 6, -8),
]

os.makedirs(os.path.dirname(os.path.abspath(OUT_MAP)), exist_ok=True)
spots_path = os.path.splitext(os.path.abspath(OUT_MAP))[0] + ".spots.json"
with open(spots_path, "w", encoding="utf-8") as sf:
    json.dump(
        [{"name": s[0], "pos": [u(s[1], OX), u(s[2], OY), u(s[3])], "yaw": s[4], "pitch": s[5] if len(s) > 5 else 0}
         for s in SPOTS],
        sf, indent=2
    )

wad_str = ";".join(WADS)
with open(OUT_MAP, "w", encoding="utf-8") as f:
    f.write('{\n"classname" "worldspawn"\n')
    f.write(f'"wad" "{wad_str}"\n')
    f.write('"message" "Historic Fox Theater & The Padre Hotel - Downtown Bakersfield"\n')
    f.write('"skyname" "bklan_"\n')
    # Sunny California midday sun from the South-East (rays travel NW: yaw 134, pitch -48) + strong California sky fill (_sunlight2 148)!
    f.write('"_minlight" "24"\n"_sunlight" "215"\n"_sunlight_mangle" "134 -48 0"\n'
            '"_sunlight_color" "1 0.96 0.86"\n"_sunlight2" "148"\n"_sunlight2_color" "0.70 0.84 1"\n'
            '"_sunlight_penumbra" "2"\n"_dirt" "1"\n"_dirtscale" "0.52"\n')
    f.write("".join(GROUPS["world"]))
    f.write("}\n")
    if GROUPS["detail"]:
        f.write('{\n"classname" "func_detail"\n' + "".join(GROUPS["detail"]) + "}\n")
    if GROUPS["fence"]:
        f.write('{\n"classname" "func_wall"\n"_shadow" "0"\n"_minlight" "58"\n' + "".join(GROUPS["fence"]) + "}\n")
    if GROUPS["illus"]:
        f.write('{\n"classname" "func_detail_illusionary"\n"_shadow" "0"\n' + "".join(GROUPS["illus"]) + "}\n")
    f.write("".join(ENTS))

if check_placed():
    sys.exit("ERROR: spawns or items blocked by solid brushes!")

print(f"wrote {OUT_MAP}: {len(GROUPS['world'])} world + {len(GROUPS['detail'])} detail + "
      f"{len(GROUPS['fence'])} fence + {len(GROUPS['illus'])} illus brushes, {len(ENTS)} entities")
