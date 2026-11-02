"""spruce_lib.py — Valve-220 3D brush, oriented-architecture, roof, road-ribbon, tree, fence,
and vehicle geometry library for `make_spruce.py` (Spruce St / Westchester replica, 12 units/ft).
"""
import json
import math
import os
import random
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
U = 12.0                # 12 Quake units per foot
OX, OY = 80.0, -10.0    # Shifts [-820..+980, -860..+840] ft cleanly around (0, 0) in Quake units

WADS = ("bklan.wad", "bklan3.wad", "spruce.wad")
TEXSIZE = {}
for _wn in WADS:
    _wp = os.path.join(HERE, "out", "maps", _wn)
    if not os.path.exists(_wp):
        continue
    with open(_wp, "rb") as _f:
        _, _n, _ofs = struct.unpack("<4sii", _f.read(12))
        _f.seek(_ofs)
        _dirs = [struct.unpack("<3i2bh16s", _f.read(32)) for _ in range(_n)]
        for _pos, _, _, _, _, _, _name in _dirs:
            _f.seek(_pos)
            _nm, _w, _h = struct.unpack("<16s2I", _f.read(24))
            TEXSIZE[_name.split(b"\0")[0].decode()] = (_w, _h)

with open(os.path.join(HERE, "spruce_gis.json"), "r", encoding="utf-8") as _gf:
    GIS = json.load(_gf)

GROUPS = {"world": [], "detail": [], "phong": [], "fence": [], "illus": []}
ENTS = []
SOLIDS = []
PLACED = []


def u(v, o=0.0):
    return round((v - o) * U, 3)


def ui(v, o=0.0):
    return int(round((v - o) * U))


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def vnorm(a):
    L = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    if L < 1e-9:
        return (1.0, 0.0, 0.0)
    return (a[0] / L, a[1] / L, a[2] / L)


class Tile:
    """Tiled world texture where 1 full PNG tile spans `ft_u` x `ft_v` feet."""
    def __init__(self, name, ft_u=8.0, ft_v=None):
        self.name = name
        self.ft_u = ft_u
        self.ft_v = ft_u if ft_v is None else ft_v


class Fit:
    """Texture stretched cleanly across a brush face (`repeat=(ru, rv)`)."""
    def __init__(self, name, repeat=(1.0, 1.0)):
        self.name = name
        self.repeat = repeat


def tspec(name, ft_u=8.0, ft_v=None):
    return Tile(name, ft_u, ft_v)


def _default_axes(outward, u_hint=None):
    """Computes clean orthonormal Valve-220 (U_ax, V_ax) for any outward plane normal."""
    N = vnorm(outward)
    if u_hint is not None:
        # Project u_hint onto plane
        uh = vsub(u_hint, vmul(N, vdot(u_hint, N)))
        if vdot(uh, uh) > 1e-6:
            U_ax = vnorm(uh)
            # Make V_ax point downward along the face (-Z component >= 0 if sloped/vertical)
            V_ax = vnorm(vcross(U_ax, N))
            if V_ax[2] > 1e-5:
                V_ax = vmul(V_ax, -1.0)
            return U_ax, V_ax
    if abs(N[2]) < 0.98:
        # Vertical or sloped wall/roof: U_ax horizontal left-to-right from outside!
        U_ax = vnorm((-N[1], N[0], 0.0))
        V_ax = vnorm(vcross(U_ax, N))
        if V_ax[2] > 0:
            V_ax = vmul(V_ax, -1.0)
        return U_ax, V_ax
    # Flat horizontal top/bottom: U_ax = +X, V_ax = -Y (north-up plan!)
    return (1.0, 0.0, 0.0), (0.0, -1.0, 0.0)


def vface(p0, p1, p2, outward, tex, poly_pts=None, u_hint=None):
    """Formats a single Valve-220 brush plane with exact UVs."""
    # Quake plane convention: (p0 - p1) x (p2 - p1) points OUTWARD!
    n = vcross(vsub(p0, p1), vsub(p2, p1))
    if vdot(n, outward) < 0:
        p0, p2 = p2, p0
    U_ax, V_ax = _default_axes(outward, u_hint=u_hint)

    if isinstance(tex, Fit):
        tname = tex.name
        tw, th = TEXSIZE.get(tname, (64, 64))
        pts = poly_pts if poly_pts else (p0, p1, p2)
        us = [vdot(p, U_ax) for p in pts]
        vs = [vdot(p, V_ax) for p in pts]
        umin, umax = min(us), max(us)
        vmin, vmax = min(vs), max(vs)
        span_u = max(1.0, umax - umin)
        span_v = max(1.0, vmax - vmin)
        xs = span_u / (tw * tex.repeat[0])
        ys = span_v / (th * tex.repeat[1])
        uoff = -umin / xs
        voff = -vmin / ys
    elif isinstance(tex, Tile):
        tname = tex.name
        tw, th = TEXSIZE.get(tname, (64, 64))
        xs = (tex.ft_u * U) / tw
        ys = (tex.ft_v * U) / th
        uoff, voff = 0.0, 0.0
    else:
        tname = str(tex)
        xs, ys, uoff, voff = 1.0, 1.0, 0.0, 0.0

    def fp(p):
        return f"( {p[0]:.3f} {p[1]:.3f} {p[2]:.3f} )"

    return (
        f"{fp(p0)} {fp(p1)} {fp(p2)} {tname} "
        f"[ {U_ax[0]:.5f} {U_ax[1]:.5f} {U_ax[2]:.5f} {uoff:.3f} ] "
        f"[ {V_ax[0]:.5f} {V_ax[1]:.5f} {V_ax[2]:.5f} {voff:.3f} ] "
        f"0 {xs:.5f} {ys:.5f}\n"
    )


def add_brush(face_lines, bounds_pts=None, group="detail", solid=None, tex_check="", planes_2d=None):
    GROUPS[group].append("{\n" + "".join(face_lines) + "}\n")
    if solid is None:
        solid = (group != "illus" and tex_check not in ("sky_bk", "clip"))
    if solid and bounds_pts:
        xs = [p[0] for p in bounds_pts]
        ys = [p[1] for p in bounds_pts]
        zs = [p[2] for p in bounds_pts]
        if max(zs) - min(zs) > 2.0:
            SOLIDS.append((min(xs), min(ys), min(zs), max(xs), max(ys), max(zs), planes_2d))


def box(x1, y1, z1, x2, y2, z2, tex, faces=None, group="world", solid=None):
    """Axis-aligned box in feet."""
    faces = faces or {}
    X1, X2 = sorted((u(x1, OX), u(x2, OX)))
    Y1, Y2 = sorted((u(y1, OY), u(y2, OY)))
    Z1, Z2 = sorted((u(z1), u(z2)))
    if X2 - X1 < 0.2 or Y2 - Y1 < 0.2 or Z2 - Z1 < 0.2:
        return
    c000, c100, c110, c010 = (X1, Y1, Z1), (X2, Y1, Z1), (X2, Y2, Z1), (X1, Y2, Z1)
    c001, c101, c111, c011 = (X1, Y1, Z2), (X2, Y1, Z2), (X2, Y2, Z2), (X1, Y2, Z2)
    fl = [
        vface(c000, c010, c001, (-1, 0, 0), faces.get("w", tex), (c000, c010, c011, c001)),
        vface(c100, c101, c110, (1, 0, 0), faces.get("e", tex), (c100, c110, c111, c101)),
        vface(c000, c001, c100, (0, -1, 0), faces.get("s", tex), (c000, c100, c101, c001)),
        vface(c010, c110, c011, (0, 1, 0), faces.get("n", tex), (c010, c110, c111, c011)),
        vface(c000, c100, c010, (0, 0, -1), faces.get("b", tex), (c000, c100, c110, c010)),
        vface(c001, c011, c101, (0, 0, 1), faces.get("t", tex), (c001, c101, c111, c011)),
    ]
    tname = tex.name if hasattr(tex, "name") else str(tex)
    add_brush(fl, (c000, c111), group=group, solid=solid, tex_check=tname)


def prop(x1, y1, z1, x2, y2, z2, tex, faces=None, solid=None):
    box(x1, y1, z1, x2, y2, z2, tex, faces=faces, group="detail", solid=solid)


def obox(cx, cy, z1, z2, half_u, half_v, yaw_deg, tex, faces=None, group="detail", solid=None):
    """Oriented 3D box in feet!
    `yaw_deg` is the direction of the local +V ('front') normal in Quake degrees (0=+X East, 90=+Y North).
    When standing in front of the box looking AT its 'front' (+V) face:
      - `U` runs LEFT-TO-RIGHT (`u_dir = (sin yaw, -cos yaw, 0)`) over `-half_u .. +half_u`!
      - `V` runs BACK-TO-FRONT (`v_dir = (cos yaw, sin yaw, 0)`) over `-half_v .. +half_v`!
    `faces` keys: 'front' (+V), 'back' (-V), 'right' (+U), 'left' (-U), 't' (+Z), 'b' (-Z).
    """
    faces = faces or {}
    if half_u < 0.02 or half_v < 0.02 or abs(z2 - z1) < 0.02:
        return
    Z1, Z2 = sorted((u(z1), u(z2)))
    rad = math.radians(yaw_deg)
    vx, vy = math.cos(rad), math.sin(rad)       # +V = front outward normal
    ux, uy = math.sin(rad), -math.cos(rad)      # +U = left-to-right when facing front!
    CX, CY = u(cx, OX), u(cy, OY)
    HU, HV = half_u * U, half_v * U

    def pt(su, sv, z):
        return (CX + su * HU * ux + sv * HV * vx, CY + su * HU * uy + sv * HV * vy, z)

    # Bottom 4 & Top 4 corners
    b_fl, b_fr = pt(-1, 1, Z1), pt(1, 1, Z1)
    b_bl, b_br = pt(-1, -1, Z1), pt(1, -1, Z1)
    t_fl, t_fr = pt(-1, 1, Z2), pt(1, 1, Z2)
    t_bl, t_br = pt(-1, -1, Z2), pt(1, -1, Z2)

    fl = [
        vface(b_fl, b_fr, t_fl, (vx, vy, 0), faces.get("front", tex), (b_fl, b_fr, t_fr, t_fl)),
        vface(b_br, b_bl, t_br, (-vx, -vy, 0), faces.get("back", tex), (b_br, b_bl, t_bl, t_br)),
        vface(b_fr, b_br, t_fr, (ux, uy, 0), faces.get("right", tex), (b_fr, b_br, t_br, t_fr)),
        vface(b_bl, b_fl, t_bl, (-ux, -uy, 0), faces.get("left", tex), (b_bl, b_fl, t_fl, t_bl)),
        vface(b_bl, b_br, b_fl, (0, 0, -1), faces.get("b", tex), (b_bl, b_br, b_fr, b_fl), u_hint=(ux, uy, 0)),
        vface(t_fl, t_fr, t_bl, (0, 0, 1), faces.get("t", tex), (t_fl, t_fr, t_br, t_bl), u_hint=(ux, uy, 0)),
    ]
    tname = tex.name if hasattr(tex, "name") else str(tex)
    planes_2d = (
        (vx, vy, CX * vx + CY * vy + HV),
        (-vx, -vy, -CX * vx - CY * vy + HV),
        (ux, uy, CX * ux + CY * uy + HU),
        (-ux, -uy, -CX * ux - CY * uy + HU),
    )
    add_brush(fl, (b_fl, b_fr, b_bl, b_br, t_fl, t_fr, t_bl, t_br), group=group, solid=solid, tex_check=tname, planes_2d=planes_2d)


def ogable(cx, cy, z_eave, z_ridge, half_u, half_v, yaw_deg, roof_tex, gable_tex, eave=1.0, group="detail"):
    """Oriented pitched gable roof! Ridge runs along V (front-to-back) so triangular gable faces 'front' (+V) and 'back' (-V)."""
    rad = math.radians(yaw_deg)
    vx, vy = math.cos(rad), math.sin(rad)
    ux, uy = math.sin(rad), -math.cos(rad)
    CX, CY = u(cx, OX), u(cy, OY)
    HU, HV = (half_u + eave) * U, (half_v + eave) * U
    Z0, Z1 = u(z_eave), u(z_ridge)
    if Z1 - Z0 < 1.0:
        return

    def pt(su, sv, z):
        return (CX + su * HU * ux + sv * HV * vx, CY + su * HU * uy + sv * HV * vy, z)

    fl_l, fl_r, fl_top = pt(-1, 1, Z0), pt(1, 1, Z0), pt(0, 1, Z1)
    bk_l, bk_r, bk_top = pt(-1, -1, Z0), pt(1, -1, Z0), pt(0, -1, Z1)
    rise = Z1 - Z0
    n_left = vnorm((-rise * ux, -rise * uy, HU))
    n_right = vnorm((rise * ux, rise * uy, HU))
    fl = [
        vface(fl_l, fl_r, fl_top, (vx, vy, 0), gable_tex, (fl_l, fl_r, fl_top)),
        vface(bk_r, bk_l, bk_top, (-vx, -vy, 0), gable_tex, (bk_r, bk_l, bk_top)),
        vface(bk_l, fl_l, bk_top, n_left, roof_tex, (bk_l, fl_l, fl_top, bk_top), u_hint=(vx, vy, 0)),
        vface(fl_r, bk_r, fl_top, n_right, roof_tex, (fl_r, bk_r, bk_top, fl_top), u_hint=(-vx, -vy, 0)),
        vface(bk_l, bk_r, fl_l, (0, 0, -1), gable_tex, (bk_l, bk_r, fl_r, fl_l), u_hint=(ux, uy, 0)),
    ]
    add_brush(fl, (fl_l, fl_r, bk_l, bk_r, fl_top, bk_top), group=group, solid=False)


def osloped_panel(cx, cy, z_low, z_high, half_u, half_v, yaw_deg, tex, thick=0.25, group="detail"):
    """Oriented sloped rooftop solar panel array (`+V` edge at `z_low` eave, `-V` edge at `z_high` up-slope!)."""
    rad = math.radians(yaw_deg)
    vx, vy = math.cos(rad), math.sin(rad)
    ux, uy = math.sin(rad), -math.cos(rad)
    CX, CY = u(cx, OX), u(cy, OY)
    HU, HV = half_u * U, half_v * U
    ZL, ZH, TH = u(z_low), u(z_high), thick * U

    def pt(su, sv, z):
        return (CX + su * HU * ux + sv * HV * vx, CY + su * HU * uy + sv * HV * vy, z)

    t_fl, t_fr = pt(-1, 1, ZL + TH), pt(1, 1, ZL + TH)
    t_bl, t_br = pt(-1, -1, ZH + TH), pt(1, -1, ZH + TH)
    b_fl, b_fr = pt(-1, 1, ZL), pt(1, 1, ZL)
    b_bl, b_br = pt(-1, -1, ZH), pt(1, -1, ZH)
    dz = ZH - ZL
    n_top = vnorm((dz * vx, dz * vy, 2 * HV))
    n_bot = vmul(n_top, -1.0)
    fl = [
        vface(t_bl, t_br, t_fl, n_top, tex, (t_bl, t_br, t_fr, t_fl), u_hint=(ux, uy, 0)),
        vface(b_fl, b_fr, b_bl, n_bot, "sp_wt_green", (b_fl, b_fr, b_br, b_bl), u_hint=(ux, uy, 0)),
        vface(b_fl, b_fr, t_fl, (vx, vy, 0), "sp_wt_green"),
        vface(b_br, b_bl, t_br, (-vx, -vy, 0), "sp_wt_green"),
        vface(b_fr, b_br, t_fr, (ux, uy, 0), "sp_wt_green"),
        vface(b_bl, b_fl, t_bl, (-ux, -uy, 0), "sp_wt_green"),
    ]
    add_brush(fl, None, group=group, solid=False)


def prism(poly, bottom, top, tex, side=None, bot=None, group="detail", solid=False, u_hint=None):
    """Vertical-sided convex polygon prism in feet."""
    n = len(poly)
    tops = list(top) if isinstance(top, (list, tuple)) else [top] * n
    bots = list(bottom) if isinstance(bottom, (list, tuple)) else [bottom] * n
    P = []
    for (x, y), zt, zb in zip(poly, tops, bots):
        q = (u(x, OX), u(y, OY), u(zt), u(zb))
        if not P or math.hypot(q[0] - P[-1][0], q[1] - P[-1][1]) > 0.5:
            P.append(q)
    if len(P) > 1 and math.hypot(P[0][0] - P[-1][0], P[0][1] - P[-1][1]) <= 0.5:
        P.pop()
    Q = []
    for i in range(len(P)):
        a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1.0:
            Q.append(b)
    P = Q
    m = len(P)
    if m < 3 or any(q[2] <= q[3] + 0.1 for q in P):
        return
    area = sum(P[i][0] * P[(i + 1) % m][1] - P[(i + 1) % m][0] * P[i][1] for i in range(m))
    if abs(area) < 8.0:
        return
    if area < 0:
        P.reverse()
    fl = []
    stex = side if side is not None else tex
    btex = bot if bot is not None else stex
    for i in range(m):
        a, b = P[i], P[(i + 1) % m]
        p0, p1, p2, p3 = (a[0], a[1], a[3]), (b[0], b[1], b[3]), (b[0], b[1], b[2]), (a[0], a[1], a[2])
        fl.append(vface(p0, p1, p3, (b[1] - a[1], -(b[0] - a[0]), 0.0), stex, (p0, p1, p2, p3)))
    i1, i2 = max(1, m // 3), max(2, (2 * m) // 3)
    if i2 == i1:
        i2 = i1 + 1
    top_pts = [(q[0], q[1], q[2]) for q in P]
    bot_pts = [(q[0], q[1], q[3]) for q in P]
    fl.append(vface(top_pts[0], top_pts[i1], top_pts[i2], (0, 0, 1), tex, top_pts, u_hint=u_hint))
    fl.append(vface(bot_pts[0], bot_pts[i2], bot_pts[i1], (0, 0, -1), btex, bot_pts, u_hint=u_hint))
    add_brush(fl, top_pts + bot_pts, group=group, solid=solid)


def ccw(poly):
    a = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if a > 0 else poly[::-1]


def convex_parts(poly):
    """Splits any simple GIS footprint polygon into clean convex pieces."""
    def area(p):
        return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2.0

    def is_convex(p):
        n = len(p)
        sgn = 0
        for i in range(n):
            a, b, c = p[i], p[(i + 1) % n], p[(i + 2) % n]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cr) < 1e-4:
                continue
            if sgn == 0:
                sgn = 1 if cr > 0 else -1
            elif (cr > 0) != (sgn > 0):
                return False
        return True

    p = [tuple(q) for q in poly]
    if len(p) > 1 and p[0] == p[-1]:
        p = p[:-1]
    if len(p) < 3:
        return []
    if area(p) < 0:
        p.reverse()
    if is_convex(p):
        return [p]
    tris, v = [], p[:]
    guard = 0
    while len(v) > 3 and guard < 400:
        guard += 1
        cut = False
        for i in range(len(v)):
            a, b, c = v[i - 1], v[i], v[(i + 1) % len(v)]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-5:
                continue
            inside = False
            for q in v:
                if q in (a, b, c):
                    continue
                d1 = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
                d2 = (c[0] - b[0]) * (q[1] - b[1]) - (c[1] - b[1]) * (q[0] - b[0])
                d3 = (a[0] - c[0]) * (q[1] - c[1]) - (a[1] - c[1]) * (q[0] - c[0])
                if d1 >= -1e-4 and d2 >= -1e-4 and d3 >= -1e-4:
                    inside = True
                    break
            if not inside:
                tris.append([a, b, c])
                del v[i]
                cut = True
                break
        if not cut:
            break
    if len(v) >= 3:
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
                        M = A[: ia + 1] + [B[(ib + 2 + k) % len(B)] for k in range(len(B) - 2)] + A[ia + 1 :]
                        if is_convex(M):
                            parts[i] = M
                            del parts[j]
                            merged = True
                        break
                if merged:
                    break
            if merged:
                break
    return parts


def offset_convex(poly, d):
    n = len(poly)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = (by - ay) / L, -(bx - ax) / L
        lines.append(((ax + nx * d, ay + ny * d), (bx - ax, by - ay), (nx, ny)))
    out = []
    max_disp = max(0.4, abs(d) * 1.55)
    for i in range(n):
        vx, vy = poly[i]
        (p, r, n0), (q, s_, n1) = lines[i - 1], lines[i]
        den = r[0] * s_[1] - r[1] * s_[0]
        if abs(den) < 1e-7:
            ix, iy = q
        else:
            t_ = ((q[0] - p[0]) * s_[1] - (q[1] - p[1]) * s_[0]) / den
            ix, iy = p[0] + r[0] * t_, p[1] + r[1] * t_
        dx, dy = ix - vx, iy - vy
        dist = math.hypot(dx, dy)
        if dist > max_disp and dist > 1e-6:
            ix = vx + dx * (max_disp / dist)
            iy = vy + dy * (max_disp / dist)
        out.append((ix, iy))
    return out


def hiproof(poly, z0, tex, eave=1.2, pitch=5.2 / 12.0, fascia_tex=None, group="detail"):
    """Realistic California hipped shingle roof over a convex polygon footprint."""
    base = offset_convex(ccw([tuple(p) for p in poly]), eave)
    # Thin eave fascia band so roof overhang has crisp thickness
    prism(base, z0 - 0.35, z0, tex, side=fascia_tex or tex, group=group, solid=False)
    cx = sum(p[0] for p in base) / len(base)
    cy = sum(p[1] for p in base) / len(base)
    dmin = 1e9
    for i in range(len(base)):
        (ax, ay), (bx, by) = base[i], base[(i + 1) % len(base)]
        L = math.hypot(bx - ax, by - ay) or 1.0
        dmin = min(dmin, abs((bx - ax) * (ay - cy) - (by - ay) * (ax - cx)) / L)
    k = 0.90
    rise = max(3.6, min(8.6, dmin * k * pitch))
    topp = [(cx + (x - cx) * (1.0 - k), cy + (y - cy) * (1.0 - k)) for x, y in base]
    B = [(u(x, OX), u(y, OY), u(z0)) for x, y in base]
    Tp = [(u(x, OX), u(y, OY), u(z0 + rise)) for x, y in topp]
    fl = []
    n = len(B)
    for i in range(n):
        a, b = B[i], B[(i + 1) % n]
        ta, tb = Tp[i], Tp[(i + 1) % n]
        out_n = vcross(vsub(b, a), vsub(ta, a))
        fl.append(vface(a, b, ta, out_n, tex, (a, b, tb, ta), u_hint=vsub(b, a)))
    i1, i2 = max(1, n // 3), max(2, (2 * n) // 3)
    if i2 == i1:
        i2 = i1 + 1
    fl.append(vface(B[0], B[i2], B[i1], (0, 0, -1), fascia_tex or tex, B))
    fl.append(vface(Tp[0], Tp[i1], Tp[i2], (0, 0, 1), tex, Tp))
    add_brush(fl, B + Tp, group=group, solid=False)
    return z0 + rise


def frustum_ring(cx, cy, r0, r1, z0, z1, tex, sides=20, side_tex=None, group="detail", solid=False):
    """Smooth N-sided cylindrical/conical/domed frustum ring (for the Water Tower!)."""
    CX, CY = u(cx, OX), u(cy, OY)
    Z0, Z1 = sorted((u(z0), u(z1)))
    if Z1 - Z0 < 0.2:
        return
    R0, R1 = max(0.3, r0 * U), max(0.3, r1 * U)
    B0 = [(CX + R0 * math.cos(math.tau * k / sides), CY + R0 * math.sin(math.tau * k / sides), Z0) for k in range(sides)]
    B1 = [(CX + R1 * math.cos(math.tau * k / sides), CY + R1 * math.sin(math.tau * k / sides), Z1) for k in range(sides)]
    fl = [
        vface(B0[0], B0[2 * sides // 3], B0[sides // 3], (0, 0, -1), tex, B0),
        vface(B1[0], B1[sides // 3], B1[2 * sides // 3], (0, 0, 1), tex, B1),
    ]
    stex = side_tex if side_tex is not None else tex
    for k in range(sides):
        a0, b0 = B0[k], B0[(k + 1) % sides]
        a1, b1 = B1[k], B1[(k + 1) % sides]
        ang = math.tau * (k + 0.5) / sides
        dz = Z1 - Z0
        dr = R0 - R1
        out_n = (math.cos(ang) * dz, math.sin(ang) * dz, dr)
        fl.append(vface(a0, b0, a1, out_n, stex, (a0, b0, b1, a1), u_hint=vsub(b0, a0)))
    add_brush(fl, B0 + B1, group=group, solid=solid)


def strut_3d(p0, p1, radius_ft, tex, group="detail", solid=False):
    """True 3D square structural steel leg or cross-arm from `p0=(x0,y0,z0)` to `p1=(x1,y1,z1)` in feet!"""
    P0 = (u(p0[0], OX), u(p0[1], OY), u(p0[2]))
    P1 = (u(p1[0], OX), u(p1[1], OY), u(p1[2]))
    D = vsub(P1, P0)
    L = math.sqrt(vdot(D, D))
    if L < 1.0:
        return
    W = vnorm(D)
    ref = (1.0, 0.0, 0.0) if abs(W[0]) < 0.85 else (0.0, 1.0, 0.0)
    A = vnorm(vcross(W, ref))
    B = vnorm(vcross(W, A))
    R = radius_ft * U

    def c(t_end, sa, sb):
        base = P1 if t_end else P0
        return vadd(base, vadd(vmul(A, sa * R), vmul(B, sb * R)))

    b00, b10, b11, b01 = c(0, -1, -1), c(0, 1, -1), c(0, 1, 1), c(0, -1, 1)
    t00, t10, t11, t01 = c(1, -1, -1), c(1, 1, -1), c(1, 1, 1), c(1, -1, 1)
    fl = [
        vface(b00, b10, b01, vmul(W, -1), tex),
        vface(t00, t01, t10, W, tex),
        vface(b00, b10, t00, vmul(B, -1), tex, u_hint=A),
        vface(b11, b01, t11, B, tex, u_hint=vmul(A, -1)),
        vface(b10, b11, t10, A, tex, u_hint=B),
        vface(b01, b00, t01, vmul(A, -1), tex, u_hint=vmul(B, -1)),
    ]
    add_brush(fl, (b00, b11, t00, t11), group=group, solid=solid)


def smooth_curve(pts, subdiv=4):
    """Catmull-Rom spline smoothing for curved residential streets."""
    if len(pts) < 3 or subdiv <= 1:
        return list(pts)
    ext = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(subdiv):
            t = k / subdiv
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def road_ribbon(pts, width, tex, z_bot=-0.2, z_top=0.12, curbs=True, curb_w=0.65, curb_h=0.46, sidewalks=False, sw_w=4.8):
    """Builds a smooth road or alley ribbon with optional raised concrete curbs & sidewalks!"""
    ext = width * 0.22
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 0.8:
            continue
        dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -dy, dx
        ax, ay = a[0] - dx * ext, a[1] - dy * ext
        bx, by = b[0] + dx * ext, b[1] + dy * ext
        hw = width / 2.0
        poly = [(ax - nx * hw, ay - ny * hw), (bx - nx * hw, by - ny * hw), (bx + nx * hw, by + ny * hw), (ax + nx * hw, ay + ny * hw)]
        prism(poly, z_bot, z_top, tex, side="sp_conc", group="detail", solid=True)
        if curbs:
            c_ext = 0.35
            cax, cay = a[0] - dx * c_ext, a[1] - dy * c_ext
            cbx, cby = b[0] + dx * c_ext, b[1] + dy * c_ext
            for sgn in (-1.0, 1.0):
                r0 = hw
                r1 = hw + curb_w
                cpoly = [
                    (cax + sgn * nx * r0, cay + sgn * ny * r0),
                    (cbx + sgn * nx * r0, cby + sgn * ny * r0),
                    (cbx + sgn * nx * r1, cby + sgn * ny * r1),
                    (cax + sgn * nx * r1, cay + sgn * ny * r1),
                ]
                prism(cpoly, 0.0, curb_h, tspec("sp_conc", 6), group="detail", solid=True)
                if sidewalks:
                    s0 = r1
                    s1 = r1 + sw_w
                    spoly = [
                        (cax + sgn * nx * s0, cay + sgn * ny * s0),
                        (cbx + sgn * nx * s0, cby + sgn * ny * s0),
                        (cbx + sgn * nx * s1, cby + sgn * ny * s1),
                        (cax + sgn * nx * s1, cay + sgn * ny * s1),
                    ]
                    prism(spoly, 0.0, curb_h - 0.02, tspec("sp_conc", 8), group="detail", solid=True)


def fence_line(pts, z0, z1, tex, thick=0.22, group="fence", fit_len=8.0):
    """Follows a polyline `(x, y)` with crisp subdivided fence panels (`<= 12 ft` so AABBs stay tight!)."""
    tname = tex.name if hasattr(tex, "name") else str(tex)
    for a, b in zip(pts, pts[1:]):
        dx_tot, dy_tot = b[0] - a[0], b[1] - a[1]
        L_tot = math.hypot(dx_tot, dy_tot)
        if L_tot < 0.4:
            continue
        nsub = max(1, int(math.ceil(L_tot / 12.0)))
        yaw = math.degrees(math.atan2(dx_tot, -dy_tot))
        seg_L = L_tot / nsub
        for k in range(nsub):
            t0, t1 = k / nsub, (k + 1) / nsub
            mx = a[0] + dx_tot * ((t0 + t1) * 0.5)
            my = a[1] + dy_tot * ((t0 + t1) * 0.5)
            if tname.startswith("{"):
                ft = Fit(tname, (max(1.0, round(seg_L / fit_len, 2)), 1.0))
                obox(mx, my, z0, z1, seg_L / 2.0, thick / 2.0, yaw, "{sp_invis",
                     {"front": ft, "back": ft}, group=group, solid=(group != "illus"))
            else:
                ft = tspec(tname, fit_len, z1 - z0)
                obox(mx, my, z0, z1, seg_L / 2.0, thick / 2.0, yaw, ft, group="detail", solid=True)


def road_stencil(cx, cy, tex_name, yaw_deg, w=11.0, d=4.2, z=0.14):
    """Painted white asphalt street stencil oriented at `yaw_deg` (readable when looking in `-V` or `+V`!)."""
    obox(cx, cy, z, z + 0.04, w / 2.0, d / 2.0, yaw_deg, "{sp_rd_spruc",
         {"t": Fit(tex_name)}, group="illus", solid=False)


# ============================================================================== TREES, PALMS & YARD PROPS
def eucalyptus_tree(x, y, h=60.0, r_crown=11.5, seed=1):
    """Tall California eucalyptus tree (peeling pale trunk + multi-branch crown + feathery `{sp_euc` cards!)."""
    rng = random.Random(seed)
    bark = tspec("sp_eucbark", 3.0, 6.0)
    frustum_ring(x, y, 1.05, 0.68, 0.0, h * 0.44, bark, sides=7, group="detail", solid=True)
    for k in range(3):
        ang = rng.uniform(0, math.tau) + k * 2.1
        bx = x + math.cos(ang) * (r_crown * 0.36)
        by = y + math.sin(ang) * (r_crown * 0.36)
        strut_3d((x, y, h * 0.38), (bx, by, h * 0.68), 0.42, bark, group="detail", solid=False)
        for c_yaw in (15 + k * 25, 75 + k * 25, 135 + k * 25):
            obox(bx, by, h * 0.42, h * (0.94 + 0.05 * (k % 2)), r_crown * 0.82, 0.06, c_yaw,
                 "{sp_invis", {"front": Fit("{sp_euc"), "back": Fit("{sp_euc")}, group="illus", solid=False)
    for c_yaw in (0, 60, 120):
        obox(x, y, h * 0.48, h, r_crown * 0.94, 0.06, c_yaw,
             "{sp_invis", {"front": Fit("{sp_euc"), "back": Fit("{sp_euc")}, group="illus", solid=False)


def shade_tree(x, y, h=30.0, r_crown=11.0, leaf_tex="{sp_leaf", z_clear=10.5, seed=2):
    """Spreading deciduous California shade tree (oak/ash/elm/weeping/autumn)."""
    rng = random.Random(seed)
    bark = tspec("sp_bark", 3.0, 6.0)
    frustum_ring(x, y, 0.98, 0.65, 0.0, z_clear, bark, sides=7, group="detail", solid=True)
    for k in range(4):
        ang = k * (math.tau / 4) + rng.uniform(-0.3, 0.3)
        bx = x + math.cos(ang) * (r_crown * 0.42)
        by = y + math.sin(ang) * (r_crown * 0.42)
        strut_3d((x, y, z_clear - 1.2), (bx, by, h * 0.66), 0.38, bark, group="detail", solid=False)
        for c_yaw in (k * 45 + 10, k * 45 + 100):
            obox(bx, by, z_clear, h * 0.92, r_crown * 0.72, 0.06, c_yaw,
                 "{sp_invis", {"front": Fit(leaf_tex), "back": Fit(leaf_tex)}, group="illus", solid=False)
    for c_yaw in (20, 80, 140):
        obox(x, y, z_clear + 1.2, h, r_crown * 0.94, 0.06, c_yaw,
             "{sp_invis", {"front": Fit(leaf_tex), "back": Fit(leaf_tex)}, group="illus", solid=False)


def cedar_tree(x, y, h=44.0, r_base=14.0):
    """Giant layered Deodar Cedar evergreen (3013 Spruce St hero tree in img_081!)."""
    bark = tspec("sp_bark", 3.0, 6.0)
    frustum_ring(x, y, 1.35, 0.58, 0.0, h * 0.74, bark, sides=8, group="detail", solid=True)
    for tier, (zf0, zf1, rf) in enumerate(((0.18, 0.46, 1.0), (0.34, 0.64, 0.86), (0.52, 0.82, 0.68), (0.70, 1.0, 0.44))):
        for c_yaw in (tier * 22, tier * 22 + 45, tier * 22 + 90, tier * 22 + 135):
            obox(x, y, h * zf0, h * zf1, r_base * rf, 0.06, c_yaw,
                 "{sp_invis", {"front": Fit("{sp_cedar"), "back": Fit("{sp_cedar")}, group="illus", solid=False)


def palm_tree(x, y, h=38.0):
    """California fan palm (Smart & Final lot, Jacaranda Dr skyline, Westchester)."""
    bark = tspec("sp_bark", 2.5, 5.0)
    frustum_ring(x, y, 0.78, 0.52, 0.0, h - 3.5, bark, sides=7, group="detail", solid=True)
    frustum_ring(x, y, 1.2, 0.8, h - 5.5, h - 2.5, tspec("sp_mulch", 3), sides=7, group="detail", solid=False)
    for c_yaw in (0, 45, 90, 135):
        obox(x, y, h - 6.0, h + 3.5, 5.8, 0.06, c_yaw,
             "{sp_invis", {"front": Fit("{sp_weep"), "back": Fit("{sp_weep")}, group="illus", solid=False)


def trash_bin(x, y, yaw_deg, col_tex="sp_bin_blu", lid_tex=None, z0=0.0):
    """Curbside or alley Bakersfield wheeled rollout trash cart (`3035` bins in North Alley!)."""
    obox(x, y, z0, z0 + 3.1, 1.05, 1.15, yaw_deg, col_tex, group="detail", solid=True)
    top_f = {"t": Fit(lid_tex), "front": Fit(lid_tex)} if lid_tex else {}
    obox(x, y, z0 + 3.1, z0 + 3.45, 1.12, 1.22, yaw_deg, col_tex, faces=top_f, group="detail", solid=True)


def utility_pole(x, y, yaw_deg=0.0, h=31.0, crossarm=True):
    """Wooden Bakersfield alley/street PG&E utility pole with crossarm & insulators."""
    bark = tspec("sp_bark", 2.0, 6.0)
    frustum_ring(x, y, 0.44, 0.30, 0.0, h, bark, sides=6, group="detail", solid=True)
    if crossarm:
        obox(x, y, h - 2.4, h - 1.9, 3.8, 0.25, yaw_deg, bark, group="detail", solid=False)


def wire_span(p0, p1, z0, z1, sag=1.2):
    """Overhead black utility wire between two utility poles."""
    mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
    zm = (z0 + z1) / 2.0 - sag
    strut_3d((p0[0], p0[1], z0), (mx, my, zm), 0.05, "sp_roof_drk", group="illus", solid=False)
    strut_3d((mx, my, zm), (p1[0], p1[1], z1), 0.05, "sp_roof_drk", group="illus", solid=False)


def ceiling_fan(cx, cy, z_ceil, blade_tex="sp_woodfnc", hub_tex="sp_stuc_wht", yaw_deg=0.0):
    """5-blade interior ceiling fan + downrod + light globe for 3003 Spruce St rooms (img2_034, 037, 039, 040, 041)."""
    obox(cx, cy, z_ceil - 0.55, z_ceil - 0.02, 0.16, 0.16, yaw_deg, hub_tex, group="illus", solid=False)
    obox(cx, cy, z_ceil - 0.85, z_ceil - 0.50, 0.52, 0.52, yaw_deg, hub_tex, group="illus", solid=False)
    obox(cx, cy, z_ceil - 1.25, z_ceil - 0.85, 0.36, 0.36, yaw_deg, "sp_fluor", group="illus", solid=False)
    for k in range(5):
        ang = yaw_deg + k * 72.0
        rad = math.radians(ang)
        bx = cx + 1.35 * math.cos(rad)
        by = cy + 1.35 * math.sin(rad)
        obox(bx, by, z_ceil - 0.72, z_ceil - 0.64, 0.24, 1.05, ang, blade_tex, group="illus", solid=False)


def brush_vehicle(cx, cy, yaw_deg, body_tex="sp_stuc_wht", kind="sedan", z0=0.12):
    """Spawns a live shootable / explodable 3D BakersfieldQuake vehicle (`misc_vehicle_*`)!
    Replaces every parked car in the neighborhood with an interactive destructible MD3 vehicle:
      - `misc_vehicle_truck`: Cobalt Blue & Silver 4x4 Pickup (300 HP)
      - `misc_vehicle_sedan`: Metallic Emerald Green 4-Door Sedan (230 HP)
      - `misc_vehicle_van`:   Fleet Oxford White Cargo Van (280 HP, also drivable with H!)
      - `misc_vehicle_coupe`: Milano Red 2-Door Sport Coupe (210 HP)
    `yaw_deg` points toward the FRONT bumper (+X at yaw 0).
    """
    if kind == "pickup":
        cls, hl, hw, ht = "misc_vehicle_truck", 116.0, 46.0, 84.0
    elif kind in ("van", "boxtruck", "suv_4runner"):
        cls, hl, hw, ht = "misc_vehicle_van", 110.0, 44.0, 89.0
    elif kind == "coupe" or body_tex == "sp_redstep":
        cls, hl, hw, ht = "misc_vehicle_coupe", 94.0, 38.0, 52.0
    else:
        cls, hl, hw, ht = "misc_vehicle_sedan", 98.0, 39.0, 55.0

    ang = int(round(yaw_deg)) % 360
    ent(cls, cx, cy, z0 + 0.20, angle=ang)

    # Register exact rotated vehicle SOLID_BBOX in SOLIDS so player spawns/items never overlap cars
    rad = math.radians(ang)
    vx, vy = math.cos(rad), math.sin(rad)
    ux, uy = math.sin(rad), -math.cos(rad)
    CX, CY, Z1 = u(cx, OX), u(cy, OY), u(z0)
    hx = abs(vx) * hl + abs(ux) * hw
    hy = abs(vy) * hl + abs(uy) * hw
    planes_2d = (
        (vx, vy, CX * vx + CY * vy + hl),
        (-vx, -vy, -CX * vx - CY * vy + hl),
        (ux, uy, CX * ux + CY * uy + hw),
        (-ux, -uy, -CX * ux - CY * uy + hw),
    )
    SOLIDS.append((CX - hx, CY - hy, Z1, CX + hx, CY + hy, Z1 + ht, planes_2d))


# ============================================================================== ENTITIES & PLACEMENT CHECK
def ent(classname, x, y, z, **kv):
    X, Y, Z = ui(x, OX), ui(y, OY), ui(z)
    if classname.startswith(("info_player", "weapon_", "item_")):
        PLACED.append((classname, (X, Y, Z)))
    lines = [f'"classname" "{classname}"', f'"origin" "{X} {Y} {Z}"']
    for k, v in kv.items():
        lines.append(f'"{k}" "{v}"')
    ENTS.append("{\n" + "\n".join(lines) + "\n}\n")


def light(x, y, z, val=180, color="255 242 216", **kv):
    ent("light", x, y, z, light=val, _color=color, **kv)


def brush_ent(classname, x1, y1, z1, x2, y2, z2, tex="sp_wt_green", **kv):
    X1, X2 = sorted((u(x1, OX), u(x2, OX)))
    Y1, Y2 = sorted((u(y1, OY), u(y2, OY)))
    Z1, Z2 = sorted((u(z1), u(z2)))
    c000, c100, c110, c010 = (X1, Y1, Z1), (X2, Y1, Z1), (X2, Y2, Z1), (X1, Y2, Z1)
    c001, c101, c111, c011 = (X1, Y1, Z2), (X2, Y1, Z2), (X2, Y2, Z2), (X1, Y2, Z2)
    fl = [
        vface(c000, c010, c001, (-1, 0, 0), tex),
        vface(c100, c101, c110, (1, 0, 0), tex),
        vface(c000, c001, c100, (0, -1, 0), tex),
        vface(c010, c110, c011, (0, 1, 0), tex),
        vface(c000, c100, c010, (0, 0, -1), tex),
        vface(c001, c011, c101, (0, 0, 1), tex),
    ]
    s = "{\n" + f'"classname" "{classname}"\n'
    for k, v in kv.items():
        s += f'"{k}" "{v}"\n'
    s += "{\n" + "".join(fl) + "}\n}\n"
    ENTS.append(s)


def check_placed():
    bad = 0
    for cls, (x, y, z) in PLACED:
        if cls.startswith("info_player"):
            lo, hi = (x - 16, y - 16, z - 23), (x + 16, y + 16, z + 32)
        else:
            lo, hi = (x - 16, y - 16, z - 8), (x + 16, y + 16, z + 16)
        for b in SOLIDS:
            if not all(lo[i] < b[i + 3] and hi[i] > b[i] for i in range(3)):
                continue
            planes_2d = b[6] if len(b) > 6 else None
            if planes_2d and any(nx * x + ny * y - 16.0 * (abs(nx) + abs(ny)) >= d - 0.1 for nx, ny, d in planes_2d):
                continue
            print(f"BLOCKED {cls} at ({x}, {y}, {z}) by brush {b[:6]}")
            bad += 1
            break
    return bad
