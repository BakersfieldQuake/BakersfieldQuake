"""Studio-Grade 3D Sculpted Mesh Generator for the Fiat Ducato / Ram ProMaster X290
L2H2 High-Roof Walk-In Commercial Cargo Van.

Pure Python + math (zero external runtime dependencies) so it can be imported directly
by headless Blender 5.2, build_vehicles_assets.py, and build_van_viewer_html.py.

Matched 1:1 to reference video frames (frame_001 .. frame_020):
  - Exact L2H2 cab-forward silhouette, curved planform nose, tumblehome & crowned H2 roof
  - Asymmetric body: Right (-Y) sliding door + 3D track rail + 2 handles; Left (+Y) blind panel + 1 handle
  - Dipping X290 cab door window sills, quarter glass mullions & twin-arm commercial mirrors
  - 50/50 split rear barn doors swung open 152 deg on 3D external strap hinges (with 0..180 deg viewer rig)
  - Full walk-in cargo interior: 3D ribbed white floor, matte-black lower wall liners, rounded
    radially-fluted white wheel arches, 3D perforated structural wall ribs & ceiling cross-bows,
    over-cab dark storage shelf, wire-mesh bulkhead, 3D bucket seats, Ducato dash & steering wheel
  - Translucent RGBA laminated cab glass + square wire-mesh bulkhead screen ('glass_cab')
"""
import math
import random

import promaster_van_tex as ptex
from promaster_van_tex import (
    VAN_SPEC,
    R_ARCH_WHITE,
    R_BARN_IN_L,
    R_BARN_IN_R,
    R_BARN_OUT_L,
    R_BARN_OUT_R,
    R_CARGO_FLOOR,
    R_CARGO_WALL,
    R_CEIL_WHITE,
    R_CHROME,
    R_DASH,
    R_EMBER,
    R_ENGINE,
    R_LINER_BLK,
    R_SEAT,
    R_TREAD,
    R_TRIM_BLK,
    R_WHEEL,
    R_WHITE_CLEAN,
    R_WRECK,
    front_uv_van,
    rear_frame_uv_van,
    side_uv_van,
    top_uv_van,
    uv_in_rect,
)

SWATCH_MAP = {
    "white":       R_WHITE_CLEAN,
    "trim":        R_TRIM_BLK,
    "chrome":      R_CHROME,
    "cargo_floor": R_CARGO_FLOOR,
    "cargo_wall":  R_CARGO_WALL,
    "liner_blk":   R_LINER_BLK,
    "arch_white":  R_ARCH_WHITE,
    "ceil_white":  R_CEIL_WHITE,
    "dash":        R_DASH,
    "seat":        R_SEAT,
    "engine":      R_ENGINE,
    "wreck":       R_WRECK,
    "ember":       R_EMBER,
    "tread":       R_TREAD,
}


# --------------------------------------------------------------------------- Minimal 3D Vector Math
def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def v_len(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def v_norm(a):
    ln = v_len(a)
    return (a[0] / ln, a[1] / ln, a[2] / ln) if ln > 1e-9 else (0.0, 0.0, 1.0)


def v_lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def rot_z_pt(p, pivot_xy, rad):
    px, py = pivot_xy
    dx, dy = p[0] - px, p[1] - py
    c, s = math.cos(rad), math.sin(rad)
    return (px + dx * c - dy * s, py + dx * s + dy * c, p[2])


# --------------------------------------------------------------------------- Exact X290 Parametric Surface Contours
def outer_half_width(z):
    """Exact cross-sectional half-width y(z) of the X290 Ducato / ProMaster L2H2 body."""
    if z < 13.6:
        # Subtle lower white rocker sill tuck-in (z=10.5 -> 41.6, z=13.6 -> 43.0)
        t = max(0.0, (z - 10.5) / 3.1)
        return 41.6 + 1.4 * math.sin(0.5 * math.pi * t)
    if z <= 47.5:
        return 43.0
    if z <= 83.5:
        # Smooth upper body tumblehome (43.0 -> 39.6)
        t = (z - 47.5) / 36.0
        return 43.0 - 3.4 * (t ** 1.28)
    if z <= 97.5:
        # H2 High-Roof side cap shoulder (39.6 -> 36.0)
        t = (z - 83.5) / 14.0
        return 39.6 - 3.6 * (t ** 1.35)
    # Rounded roof shoulder roll-in (97.5 -> 101.2: 36.0 -> 31.2)
    t = min(1.0, (z - 97.5) / 3.7)
    return 36.0 - 4.8 * (t ** 1.6)


# Measured side roof/forehead/windshield/hood top silhouette (x, z_center) from frame_015.png
_SILHOUETTE_XZ = [
    (-108.0, 100.8),
    (-103.5, 103.0),
    (-94.0,  103.8),
    (-30.0,  102.9),
    (18.0,   101.5),
    (25.5,   100.8),
    (31.5,    99.1),
    (36.8,    95.8),
    (42.2,    90.6),
    (48.5,    81.6),   # Top header of raked windshield
    (60.5,    72.8),
    (72.5,    62.2),
    (84.5,    50.8),   # Base of windshield / black wiper cowl
    (92.0,    46.8),
    (100.5,   41.6),
    (109.5,   34.5),   # Front tip of hood above grille
]


def roof_or_hood_z_at_x(x):
    if x <= _SILHOUETTE_XZ[0][0]:
        return _SILHOUETTE_XZ[0][1]
    for i in range(len(_SILHOUETTE_XZ) - 1):
        x0, z0 = _SILHOUETTE_XZ[i]
        x1, z1 = _SILHOUETTE_XZ[i + 1]
        if x <= x1:
            t = (x - x0) / max(1e-6, x1 - x0)
            return z0 + (z1 - z0) * t
    return _SILHOUETTE_XZ[-1][1]


def cab_window_sill_z(x):
    """Exact Fiat Ducato / ProMaster stepped dipping cab window beltline (frame_005 & frame_015!)."""
    if x <= 44.5:
        return 49.8
    if x >= 59.0:
        return 45.0
    t = (x - 44.5) / 14.5
    return 49.8 - 4.8 * (0.5 - 0.5 * math.cos(math.pi * t))


def cab_window_top_z(x):
    """Top edge of cab door window arch following cant-rail & raked A-pillar."""
    if x <= 48.0:
        t = max(0.0, (x - 35.5) / 12.5)
        return 78.2 - 0.5 * (1.0 - t)
    t = min(1.0, (x - 48.0) / 31.5)
    return 78.2 - 26.4 * (t ** 1.04)


def nose_planform_dx(y):
    """Planform rearward curvature of the front nose/bumper/headlights across width Y."""
    ty = min(1.0, abs(y) / 43.0)
    return -12.2 * (ty ** 2.05)


# --------------------------------------------------------------------------- Crease-Smoothed Triangle Mesh Accumulator
class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.tris_raw = []  # list of (p0, p1, p2, uv0, uv1, uv2, smooth_grp)

    def _project_uvs(self, pts, fn, region):
        if region in SWATCH_MAP:
            rect = SWATCH_MAP[region]
            up_r = (0.0, 0.0, 1.0) if abs(fn[2]) < 0.88 else (1.0, 0.0, 0.0)
            t1 = v_norm(v_cross(up_r, fn))
            t2 = v_norm(v_cross(fn, t1))
            us = [v_dot(p, t1) for p in pts]
            vs = [v_dot(p, t2) for p in pts]
            umin, umax = min(us), max(us)
            vmin, vmax = min(vs), max(vs)
            du = max(6.0, umax - umin)
            dv = max(6.0, vmax - vmin)
            return [uv_in_rect(rect, (u - umin) / du, 1.0 - (v - vmin) / dv, pad=4.0) for u, v in zip(us, vs)]

        if region == "side_l":
            return [side_uv_van(p[0], p[2], True) for p in pts]
        if region == "side_r":
            return [side_uv_van(p[0], p[2], False) for p in pts]
        if region == "front":
            return [front_uv_van(p[1], p[2]) for p in pts]
        if region == "rear_frame":
            return [rear_frame_uv_van(p[1], p[2]) for p in pts]
        if region == "top":
            return [top_uv_van(p[0], p[1]) for p in pts]
        if region == "glass_pane":
            # Left half of veh_van_glass.png (u: 0.03 .. 0.47)
            up_r = (0.0, 0.0, 1.0) if abs(fn[2]) < 0.88 else (1.0, 0.0, 0.0)
            t1 = v_norm(v_cross(up_r, fn))
            t2 = v_norm(v_cross(fn, t1))
            us = [v_dot(p, t1) for p in pts]
            vs = [v_dot(p, t2) for p in pts]
            du = max(4.0, max(us) - min(us))
            dv = max(4.0, max(vs) - min(vs))
            return [(round(0.03 + 0.44 * ((u - min(us)) / du), 5),
                     round(0.04 + 0.92 * (1.0 - (v - min(vs)) / dv), 5)) for u, v in zip(us, vs)]
        if region == "mesh_screen":
            # Right half of veh_van_glass.png (u: 0.52 .. 0.98)
            return [(round(0.52 + 0.46 * ptex.clamp01((p[1] + 34.0) / 68.0), 5),
                     round(0.04 + 0.92 * ptex.clamp01(1.0 - (p[2] - 50.5) / 30.0), 5)) for p in pts]

        # Auto region by dominant face normal
        ax, ay, az = abs(fn[0]), abs(fn[1]), abs(fn[2])
        if fn[0] > 0.60 and ax >= ay and ax >= az:
            return [front_uv_van(p[1], p[2]) for p in pts]
        if fn[0] < -0.60 and ax >= ay and ax >= az:
            return [rear_frame_uv_van(p[1], p[2]) for p in pts]
        if fn[2] > 0.55 and az >= ay:
            return [top_uv_van(p[0], p[1]) for p in pts]
        if fn[2] < -0.65:
            return [uv_in_rect(R_TRIM_BLK, (p[0] + 114.0) / 228.0, (p[1] + 43.0) / 86.0) for p in pts]
        return [side_uv_van(p[0], p[2], fn[1] >= 0.0) for p in pts]

    def add_tri(self, p0, p1, p2, region="auto", uvs=None, expect_n=None, smooth=1, double_sided=False):
        n_raw = v_cross(v_sub(p1, p0), v_sub(p2, p0))
        area2 = v_len(n_raw)
        if area2 < 1e-6:
            return
        if expect_n is not None and v_dot(n_raw, expect_n) < 0.0:
            p1, p2 = p2, p1
            if uvs is not None:
                uvs = [uvs[0], uvs[2], uvs[1]]
            n_raw = v_mul(n_raw, -1.0)
        fn = v_mul(n_raw, 1.0 / area2)
        uv_tri = uvs if uvs is not None else self._project_uvs([p0, p1, p2], fn, region)
        self.tris_raw.append((p0, p1, p2, uv_tri[0], uv_tri[1], uv_tri[2], smooth))
        if double_sided:
            self.tris_raw.append((p0, p2, p1, uv_tri[0], uv_tri[2], uv_tri[1], smooth + 1000 if smooth else 0))

    def add_quad(self, p0, p1, p2, p3, region="auto", uvs=None, expect_n=None, smooth=1, double_sided=False):
        n_raw = v_cross(v_sub(p1, p0), v_sub(p3, p0))
        if v_len(n_raw) < 1e-6:
            n_raw = v_cross(v_sub(p2, p1), v_sub(p3, p1))
        if v_len(n_raw) < 1e-6:
            return
        if expect_n is not None and v_dot(n_raw, expect_n) < 0.0:
            p0, p1, p2, p3 = p0, p3, p2, p1
            if uvs is not None:
                uvs = [uvs[0], uvs[3], uvs[2], uvs[1]]
            n_raw = v_mul(n_raw, -1.0)
        fn = v_norm(n_raw)
        uv_q = uvs if uvs is not None else self._project_uvs([p0, p1, p2, p3], fn, region)
        self.add_tri(p0, p1, p2, region=region, uvs=[uv_q[0], uv_q[1], uv_q[2]], smooth=smooth, double_sided=double_sided)
        self.add_tri(p0, p2, p3, region=region, uvs=[uv_q[0], uv_q[2], uv_q[3]], smooth=smooth, double_sided=double_sided)

    def add_box(self, x0, y0, z0, x1, y1, z1, region="trim", face_regions=None, smooth=0, skip_faces=()):
        xa, xb = min(x0, x1), max(x0, x1)
        ya, yb = min(y0, y1), max(y0, y1)
        za, zb = min(z0, z1), max(z0, z1)
        fr = face_regions or {}
        if "+x" not in skip_faces:
            self.add_quad((xb, ya, za), (xb, yb, za), (xb, yb, zb), (xb, ya, zb), fr.get("+x", region), expect_n=(1, 0, 0), smooth=smooth)
        if "-x" not in skip_faces:
            self.add_quad((xa, yb, za), (xa, ya, za), (xa, ya, zb), (xa, yb, zb), fr.get("-x", region), expect_n=(-1, 0, 0), smooth=smooth)
        if "+y" not in skip_faces:
            self.add_quad((xb, yb, za), (xa, yb, za), (xa, yb, zb), (xb, yb, zb), fr.get("+y", region), expect_n=(0, 1, 0), smooth=smooth)
        if "-y" not in skip_faces:
            self.add_quad((xa, ya, za), (xb, ya, za), (xb, ya, zb), (xa, ya, zb), fr.get("-y", region), expect_n=(0, -1, 0), smooth=smooth)
        if "+z" not in skip_faces:
            self.add_quad((xa, ya, zb), (xb, ya, zb), (xb, yb, zb), (xa, yb, zb), fr.get("+z", region), expect_n=(0, 0, 1), smooth=smooth)
        if "-z" not in skip_faces:
            self.add_quad((xa, yb, za), (xb, yb, za), (xb, ya, za), (xa, ya, za), fr.get("-z", region), expect_n=(0, 0, -1), smooth=smooth)

    def add_cylinder(self, p_a, p_b, r0, r1=None, segs=12, region="trim", cap=True, smooth=2):
        if r1 is None:
            r1 = r0
        axis = v_sub(p_b, p_a)
        if v_len(axis) < 1e-5:
            return
        d = v_norm(axis)
        up = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = v_norm(v_cross(d, up))
        v = v_norm(v_cross(d, u))
        ring0, ring1 = [], []
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            rad_dir = v_add(v_mul(u, math.cos(ang)), v_mul(v, math.sin(ang)))
            ring0.append(v_add(p_a, v_mul(rad_dir, r0)))
            ring1.append(v_add(p_b, v_mul(rad_dir, r1)))
        for i in range(segs):
            j = (i + 1) % segs
            mid_dir = v_sub(v_mul(v_add(ring0[i], ring0[j]), 0.5), p_a)
            self.add_quad(ring0[i], ring0[j], ring1[j], ring1[i], region=region, expect_n=mid_dir, smooth=smooth)
        if cap:
            for i in range(1, segs - 1):
                self.add_tri(ring0[0], ring0[i + 1], ring0[i], region=region, expect_n=v_mul(d, -1.0), smooth=0)
                self.add_tri(ring1[0], ring1[i], ring1[i + 1], region=region, expect_n=d, smooth=0)

    def add_loft(self, grid, region="auto", expect_n=None, smooth=1, uv_fn=None, double_sided=False):
        """grid[i][j] (ni x nj) lofted into smooth quads."""
        ni = len(grid)
        nj = len(grid[0])
        for i in range(ni - 1):
            for j in range(nj - 1):
                p00, p10, p11, p01 = grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]
                uvs = [uv_fn(p00, i, j), uv_fn(p10, i + 1, j), uv_fn(p11, i + 1, j + 1), uv_fn(p01, i, j + 1)] if uv_fn else None
                self.add_quad(p00, p10, p11, p01, region=region, uvs=uvs, expect_n=expect_n, smooth=smooth, double_sided=double_sided)

    def merge_from(self, other, rot_z=None, pivot_xy=(0.0, 0.0), translate=(0.0, 0.0, 0.0)):
        for p0, p1, p2, u0, u1, u2, sm in other.tris_raw:
            pts = [p0, p1, p2]
            if rot_z is not None:
                pts = [rot_z_pt(p, pivot_xy, rot_z) for p in pts]
            if translate != (0.0, 0.0, 0.0):
                pts = [v_add(p, translate) for p in pts]
            self.tris_raw.append((pts[0], pts[1], pts[2], u0, u1, u2, sm))

    def export_dict(self, custom_origin=None, hinge_pivot=None, crease_cos=0.62):
        if not self.tris_raw:
            return None

        # 1. Compute area-weighted face normals & group by quantized vertex position for crease smoothing
        face_normals = []
        pos_adj = {}
        for ti, (p0, p1, p2, _, _, _, sm) in enumerate(self.tris_raw):
            n_area = v_cross(v_sub(p1, p0), v_sub(p2, p0))
            fn = v_norm(n_area)
            face_normals.append((fn, n_area, sm))
            if sm > 0:
                for p in (p0, p1, p2):
                    pk = (round(p[0] * 20.0), round(p[1] * 20.0), round(p[2] * 20.0), sm)
                    pos_adj.setdefault(pk, []).append(ti)

        all_pts = [p for tri in self.tris_raw for p in tri[:3]]
        if custom_origin is not None:
            ctr = tuple(custom_origin)
        else:
            xs = [p[0] for p in all_pts]
            ys = [p[1] for p in all_pts]
            zs = [p[2] for p in all_pts]
            ctr = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * (min(zs) + max(zs)))

        v_map = {}
        verts, norms, uvs, tris = [], [], [], []
        for ti, (p0, p1, p2, u0, u1, u2, sm) in enumerate(self.tris_raw):
            fn, _, _ = face_normals[ti]
            tri_idx = []
            for p, uv in ((p0, u0), (p1, u1), (p2, u2)):
                if sm > 0:
                    pk = (round(p[0] * 20.0), round(p[1] * 20.0), round(p[2] * 20.0), sm)
                    acc = [0.0, 0.0, 0.0]
                    for nb_ti in pos_adj.get(pk, (ti,)):
                        nb_fn, nb_area, _ = face_normals[nb_ti]
                        if v_dot(fn, nb_fn) >= crease_cos:
                            acc[0] += nb_area[0]
                            acc[1] += nb_area[1]
                            acc[2] += nb_area[2]
                    vn = v_norm(acc) if v_len(acc) > 1e-8 else fn
                else:
                    vn = fn

                pr = (round(p[0] - ctr[0], 3), round(p[1] - ctr[1], 3), round(p[2] - ctr[2], 3))
                nr = (round(vn[0], 3), round(vn[1], 3), round(vn[2], 3))
                ur = (round(uv[0], 5), round(uv[1], 5))
                key = (pr, nr, ur)
                if key not in v_map:
                    v_map[key] = len(verts)
                    verts.append([pr[0], pr[1], pr[2]])
                    norms.append([nr[0], nr[1], nr[2]])
                    uvs.append([ur[0], ur[1]])
                tri_idx.append(v_map[key])
            tris.append(tri_idx)

        out = {
            "name": self.name,
            "origin": [round(ctr[0], 3), round(ctr[1], 3), round(ctr[2], 3)],
            "verts": verts,
            "norms": norms,
            "uvs": uvs,
            "tris": tris,
        }
        if hinge_pivot is not None:
            out["hinge"] = [round(x, 3) for x in hinge_pivot]
        return out


# --------------------------------------------------------------------------- 1. Commercial 16" Steelie Wheel Builder
def _build_commercial_wheel(name, cx, cy, cz, is_left):
    m = MeshBuilder(name)
    sgn = 1.0 if is_left else -1.0
    r_out = VAN_SPEC["wheel_r"]       # 15.2
    hw_w = VAN_SPEC["wheel_w"] * 0.5  # 4.8
    r_sh = r_out * 0.92               # Rounded tire shoulder
    r_rim = r_out * 0.64              # 9.73 silver steel rim lip
    r_dish = r_out * 0.50             # Concave vent-hole dish ring
    r_hub = r_out * 0.30              # Raised 5-lug center hub
    r_cap = r_out * 0.12              # Center spindle cap

    # Synced 1:1 with R_WHEEL in promaster_van_tex.py (cx=208, cy=1568, r_tire=178 in 2048x2048)
    ucx = 208.0 / 2048.0
    ucy = 1568.0 / 2048.0
    urad = 178.0 / 2048.0

    def w_uv(ang, r_cur):
        rr = (r_cur / r_out) * urad
        return (round(ucx + math.cos(ang) * rr, 5), round(ucy - math.sin(ang) * rr, 5))

    y_tread_out = cy + sgn * (hw_w * 0.78)
    y_tread_in  = cy - sgn * (hw_w * 0.78)
    y_bulge_out = cy + sgn * hw_w
    y_bulge_in  = cy - sgn * hw_w
    y_rim_lip   = cy + sgn * (hw_w * 0.86)
    y_dish      = cy + sgn * (hw_w * 0.44)   # Concave steelie dish recessed inward!
    y_hub       = cy + sgn * (hw_w * 0.78)   # Raised stepped 5-lug hub!
    y_cap       = cy + sgn * (hw_w * 0.86)
    y_back_rim  = cy - sgn * (hw_w * 0.76)

    segs = 32
    tx0, ty0, tx1, ty1 = R_TREAD
    u_tr0, u_tr1 = (tx0 + 8) / 2048.0, (tx1 - 8) / 2048.0
    v_tr0, v_tr1 = (ty0 + 8) / 2048.0, (ty1 - 8) / 2048.0

    for i in range(segs):
        j = (i + 1) % segs
        a0 = 2.0 * math.pi * i / segs
        a1 = 2.0 * math.pi * j / segs
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)

        def pt(c, s, r, yv):
            return (cx + c * r, yv, cz + s * r)

        rad_n = (0.5 * (c0 + c1), 0.0, 0.5 * (s0 + s1))
        out_n = (0.0, sgn, 0.0)
        in_n  = (0.0, -sgn, 0.0)

        # 1. Crowned radial tire tread band
        vt0 = v_tr0 + (v_tr1 - v_tr0) * ((i % 8) / 8.0)
        vt1 = v_tr0 + (v_tr1 - v_tr0) * (((i % 8) + 1) / 8.0)
        m.add_quad(
            pt(c0, s0, r_out, y_tread_in), pt(c0, s0, r_out, y_tread_out),
            pt(c1, s1, r_out, y_tread_out), pt(c1, s1, r_out, y_tread_in),
            uvs=[(u_tr0, vt0), (u_tr1, vt0), (u_tr1, vt1), (u_tr0, vt1)],
            expect_n=rad_n, smooth=4,
        )

        # 2. Rounded outer tire shoulder -> sidewall bulge -> rim lip -> concave dish -> raised 5-lug hub -> center cap
        rings_out = [
            (r_out,  y_tread_out, (rad_n[0], sgn * 0.5, rad_n[2])),
            (r_sh,   y_bulge_out, out_n),
            (r_rim,  y_rim_lip,   out_n),
            (r_dish, y_dish,      out_n),
            (r_hub,  y_hub,       out_n),
            (r_cap,  y_cap,       out_n),
        ]
        for k in range(len(rings_out) - 1):
            ra, ya, _ = rings_out[k]
            rb, yb, nb = rings_out[k + 1]
            m.add_quad(
                pt(c0, s0, ra, ya), pt(c1, s1, ra, ya),
                pt(c1, s1, rb, yb), pt(c0, s0, rb, yb),
                uvs=[w_uv(a0, ra), w_uv(a1, ra), w_uv(a1, rb), w_uv(a0, rb)],
                expect_n=nb, smooth=5 if k < 2 else 6,
            )

        # Center hub cap fan
        m.add_tri(
            (cx, y_cap + sgn * 0.15, cz),
            pt(c0, s0, r_cap, y_cap),
            pt(c1, s1, r_cap, y_cap),
            uvs=[(ucx, ucy), w_uv(a0, r_cap), w_uv(a1, r_cap)],
            expect_n=out_n, smooth=6,
        )

        # 3. Inner tire shoulder, back sidewall & dark brake drum (watertight from underneath!)
        m.add_quad(
            pt(c0, s0, r_out, y_tread_in), pt(c1, s1, r_out, y_tread_in),
            pt(c1, s1, r_sh, y_bulge_in),  pt(c0, s0, r_sh, y_bulge_in),
            uvs=[w_uv(a0, r_out), w_uv(a1, r_out), w_uv(a1, r_sh), w_uv(a0, r_sh)],
            expect_n=(rad_n[0], -sgn * 0.6, rad_n[2]), smooth=4,
        )
        m.add_quad(
            pt(c0, s0, r_sh, y_bulge_in), pt(c1, s1, r_sh, y_bulge_in),
            pt(c1, s1, r_rim, y_back_rim), pt(c0, s0, r_rim, y_back_rim),
            uvs=[w_uv(a0, r_sh), w_uv(a1, r_sh), w_uv(a1, r_rim), w_uv(a0, r_rim)],
            expect_n=in_n, smooth=4,
        )
        m.add_tri(
            (cx, y_back_rim, cz),
            pt(c1, s1, r_rim, y_back_rim),
            pt(c0, s0, r_rim, y_back_rim),
            region="trim", expect_n=in_n, smooth=0,
        )

    return m.export_dict(custom_origin=(cx, cy, cz))


# --------------------------------------------------------------------------- 2. Open 50/50 Rear Barn Door Builder
def _build_single_barn_door(is_left):
    """Builds one sculpted rear barn door in CLOSED local coordinates (x ~ -108.0),
    ready to be rotated around its external strap-hinge axis (-108.6, ±34.8)."""
    sgn = 1.0 if is_left else -1.0
    m = MeshBuilder("barn_door_l" if is_left else "barn_door_r")

    rect_in  = R_BARN_IN_L if is_left else R_BARN_IN_R
    rect_out = R_BARN_OUT_L if is_left else R_BARN_OUT_R

    # Door spans y from outer jamb (±33.4) to center split (±0.25), z from 19.2 to 96.8
    y_hinge_edge = sgn * 33.4
    y_latch_edge = sgn * 0.25
    z_bot = 19.2
    z_top = 96.8

    # Subtle vertical rear D-pillar rake matching van rear profile
    def x_outer_z(z):
        t = max(0.0, (z - 55.0) / 42.0)
        return -108.2 + 2.2 * (t ** 1.6)

    thick = 1.85

    def uv_in(y, z):
        # Viewing inner face when door is swung open ~152 deg:
        # Left door (+Y): latch edge (+0.25) is on outer left (su=0), hinge edge (+33.4) is on inner right (su=1)
        # Right door (-Y): hinge edge (-33.4) is on inner left (su=0), latch edge (-0.25) is on outer right (su=1)
        if is_left:
            su = (abs(y) - 0.25) / 33.15
        else:
            su = 1.0 - (abs(y) - 0.25) / 33.15
        sv = 1.0 - (z - z_bot) / (z_top - z_bot)
        return uv_in_rect(rect_in, su, sv, pad=4.0)

    def uv_out(y, z):
        # Viewing closed rear from -X looking +X: +Y is left (su=0 on left door), -Y is right (su=1 on right door)
        if is_left:
            su = (33.4 - y) / 33.15
        else:
            su = (0.25 - y) / 33.15
        sv = 1.0 - (z - z_bot) / (z_top - z_bot)
        return uv_in_rect(rect_out, su, sv, pad=4.0)

    zs = [19.2, 33.5, 46.5, 62.0, 76.0, 88.0, 96.8]
    ys = [y_hinge_edge + (y_latch_edge - y_hinge_edge) * (k / 4.0) for k in range(5)]

    # 1. Outer curved painted skin (with lower black cladding in R_BARN_OUT_*)
    out_grid = [[(x_outer_z(z), y, z) for y in ys] for z in zs]
    m.add_loft(out_grid, expect_n=(-1.0, 0.0, 0.0), smooth=2, uv_fn=lambda p, i, j: uv_out(p[1], p[2]))

    # 2. Inner stamped white steel face (with 3D relief depth on upper oval pockets!)
    def x_inner_yz(y, z):
        xb = x_outer_z(z) + thick
        ay_f = (abs(y) - 0.25) / 33.15
        zf = (z - z_bot) / (z_top - z_bot)
        # Upper 2 stamped oval pockets recess 1.0u deeper into door shell!
        if 0.13 < ay_f < 0.87 and ((0.84 < zf < 0.93) or (0.72 < zf < 0.81)):
            return xb - 0.95
        # Middle blind-window stamped recess 0.55u deeper
        if 0.14 < ay_f < 0.86 and (0.41 < zf < 0.67):
            return xb - 0.55
        return xb

    zs_in = [19.2, 23.0, 44.5, 50.8, 69.5, 73.5, 76.5, 81.8, 84.2, 90.8, 94.0, 96.8]
    ys_in = [y_hinge_edge + (y_latch_edge - y_hinge_edge) * (k / 6.0) for k in range(7)]
    in_grid = [[(x_inner_yz(y, z), y, z) for y in ys_in] for z in zs_in]
    m.add_loft(in_grid, expect_n=(1.0, 0.0, 0.0), smooth=2, uv_fn=lambda p, i, j: uv_in(p[1], p[2]))

    # 3. Perimeter painted Alpine White door edges (no thick black block edge!)
    for iz in range(len(zs) - 1):
        z0, z1 = zs[iz], zs[iz + 1]
        xo0, xo1 = x_outer_z(z0), x_outer_z(z1)
        m.add_quad((xo0, y_hinge_edge, z0), (xo0 + thick, y_hinge_edge, z0),
                   (xo1 + thick, y_hinge_edge, z1), (xo1, y_hinge_edge, z1),
                   region="white", expect_n=(0.0, sgn, 0.0), smooth=0)
        edge_reg = "trim" if z1 <= 33.6 else "white"
        m.add_quad((xo0, y_latch_edge, z0), (xo0 + thick, y_latch_edge, z0),
                   (xo1 + thick, y_latch_edge, z1), (xo1, y_latch_edge, z1),
                   region=edge_reg, expect_n=(0.0, -sgn, 0.0), smooth=0)
    xo_b, xo_t = x_outer_z(z_bot), x_outer_z(z_top)
    m.add_quad((xo_t, y_hinge_edge, z_top), (xo_t + thick, y_hinge_edge, z_top),
               (xo_t + thick, y_latch_edge, z_top), (xo_t, y_latch_edge, z_top),
               region="white", expect_n=(0.0, 0.0, 1.0), smooth=0)
    m.add_quad((xo_b, y_hinge_edge, z_bot), (xo_b + thick, y_hinge_edge, z_bot),
               (xo_b + thick, y_latch_edge, z_bot), (xo_b, y_latch_edge, z_bot),
               region="trim", expect_n=(0.0, 0.0, -1.0), smooth=0)

    # 4. 3D Raised Lower Dark-Charcoal ABS Trim Card + Right-Door 3D Black Pull Latch Handle!
    y_card0 = sgn * 3.5
    y_card1 = sgn * 30.0
    m.add_box(x_outer_z(33.0) + thick, y_card0, 23.8, x_outer_z(33.0) + thick + 0.45, y_card1, 45.2,
              region="liner_blk", skip_faces=("-x",))

    if not is_left:
        # Prominent 3D black rectangular pull/release handle on Right inner door (frame_001 & frame_020!)
        xh = x_outer_z(48.5) + thick
        m.add_box(xh, -15.5, 46.8, xh + 1.15, -22.2, 50.6, region="trim", skip_faces=("-x",))
    else:
        # 3D Black License-Plate Lamp Garnish + Raised EU Plate + Vertical Handle on Left outer door (frame_015!)
        xp = x_outer_z(38.0)
        m.add_box(xp - 0.85, 6.5, 41.2, xp, 27.5, 43.0, region="trim", skip_faces=("+x",))
        # Raised EU plate face mapped directly from R_BARN_OUT_L
        p_uv00 = uv_out(27.0, 35.8)
        p_uv10 = uv_out(7.0,  35.8)
        p_uv11 = uv_out(7.0,  41.2)
        p_uv01 = uv_out(27.0, 41.2)
        m.add_quad((xp - 0.45, 27.0, 35.8), (xp - 0.45, 7.0, 35.8),
                   (xp - 0.45, 7.0, 41.2),  (xp - 0.45, 27.0, 41.2),
                   uvs=[p_uv00, p_uv10, p_uv11, p_uv01], expect_n=(-1.0, 0.0, 0.0), smooth=0)
        # Exterior vertical pull handle near center seam
        m.add_box(xp - 0.95, 2.2, 41.5, xp, 4.6, 48.5, region="trim", skip_faces=("+x",))

    # 5. Two Sculpted 3D White External Strap Hinges (z = 35.5 and z = 80.5, frame_001 & frame_005!)
    for zh in (35.5, 80.5):
        xh_o = x_outer_z(zh)
        m.add_box(xh_o - 1.3, sgn * 29.8, zh - 1.6, xh_o + 0.4, sgn * 35.2, zh + 1.6, region="white")
        m.add_cylinder((xh_o - 0.6, sgn * 34.8, zh - 2.3), (xh_o - 0.6, sgn * 34.8, zh + 2.3), 0.95, segs=8, region="white")

    # Lower door check-strap arm near bottom hinge
    m.add_box(xo_b + thick, sgn * 27.5, 20.0, xo_b + thick + 1.4, sgn * 33.4, 21.4, region="trim")

    return m, (-108.6, sgn * 34.8, 55.0)


# --------------------------------------------------------------------------- 3. Twin-Arm Mirror & Cab Door Builder
def _build_cab_door(is_left):
    sgn = 1.0 if is_left else -1.0
    reg_side = "side_l" if is_left else "side_r"
    m = MeshBuilder("door_l" if is_left else "door_r")

    xs = [33.6, 41.5, 48.0, 56.8, 61.5, 66.5, 71.5, 76.5, 81.4]

    def door_bot_z(x):
        # Curves cleanly around the front wheel arch flare (cx=80.0, cz=14.2, r=23.2) for x > 56.8!
        dx = 80.0 - x
        if abs(dx) < 23.2:
            return max(11.2, 14.2 + math.sqrt(max(0.0, 23.2 * 23.2 - dx * dx)))
        return 11.2

    # 1. Lower sculpted painted door skin + 3D black lower cladding strip (zero wheel occlusion!)
    for ix in range(len(xs) - 1):
        x0, x1 = xs[ix], xs[ix + 1]
        sill0 = cab_window_sill_z(x0)
        sill1 = cab_window_sill_z(x1)
        b0 = door_bot_z(x0)
        b1 = door_bot_z(x1)
        if x1 <= 57.0:
            row_z0 = [11.2, 13.6, 23.8, 34.0, sill0]
            row_z1 = [11.2, 13.6, 23.8, 34.0, sill1]
        else:
            row_z0 = [b0, 0.5 * (b0 + sill0), sill0]
            row_z1 = [b1, 0.5 * (b1 + sill1), sill1]

        for iz in range(len(row_z0) - 1):
            za0, za1 = row_z0[iz], row_z0[iz + 1]
            zb0, zb1 = row_z1[iz], row_z1[iz + 1]
            pad_y = 0.48 if (x1 <= 57.0 and iz == 1) else 0.0
            ya0 = sgn * (outer_half_width(za0) + pad_y)
            ya1 = sgn * (outer_half_width(za1) + pad_y)
            yb0 = sgn * (outer_half_width(zb0) + pad_y)
            yb1 = sgn * (outer_half_width(zb1) + pad_y)
            m.add_quad((x0, ya0, za0), (x1, yb0, zb0), (x1, yb1, zb1), (x0, ya1, za1),
                       region=reg_side, expect_n=(0.0, sgn, 0.0), smooth=2)

    # Inner charcoal door trim card + sculpted armrest (stays above wheel arch!)
    y_in = sgn * 39.8
    m.add_quad((34.2, y_in, 19.5), (57.5, y_in, 19.5), (57.5, y_in, 45.0), (34.2, y_in, 49.0),
               region="liner_blk", expect_n=(0.0, -sgn, 0.0), smooth=0)
    m.add_quad((57.5, y_in, 37.5), (80.5, y_in, 37.5), (80.5, y_in, 44.8), (57.5, y_in, 45.0),
               region="liner_blk", expect_n=(0.0, -sgn, 0.0), smooth=0)
    m.add_box(40.0, sgn * 37.2, 34.5, 62.0, y_in, 38.2, region="trim")

    # Door jamb edges (rear B-pillar edge & bottom forward sill)
    m.add_box(33.6, sgn * 39.8, 12.0, 34.4, sgn * 42.9, 49.5, region="white")
    m.add_box(34.0, sgn * 39.8, 11.2, 56.8, sgn * 41.8, 12.2, region="white")

    # 3D Recessed Vertical Black Cab Door Handle (x = 38.2, z = 39.6 .. 47.6)
    yh = sgn * 43.0
    m.add_box(36.4, yh - sgn * 0.4, 39.8, 40.0, yh + sgn * 0.45, 47.4, region="trim")

    # 2. Upper Matte-Black Cab Window Frame, Dipping Sill Moulding & Quarter-Window Divider (x = 67.5)
    win_xs = [34.0, 41.5, 48.0, 54.5, 61.0, 67.5, 74.0, 79.8]
    for ix in range(len(win_xs) - 1):
        xa, xb = win_xs[ix], win_xs[ix + 1]
        sb_a, sb_b = cab_window_sill_z(xa), cab_window_sill_z(xb)
        st_a, st_b = cab_window_top_z(xa), cab_window_top_z(xb)
        # Black rubber sill strip along dipping beltline
        m.add_quad(
            (xa, sgn * outer_half_width(sb_a), sb_a - 0.6),
            (xb, sgn * outer_half_width(sb_b), sb_b - 0.6),
            (xb, sgn * (outer_half_width(sb_b) - 0.4), sb_b + 1.1),
            (xa, sgn * (outer_half_width(sb_a) - 0.4), sb_a + 1.1),
            region="trim", expect_n=(0.0, sgn, 0.1), smooth=1,
        )
        # Upper black window arch frame
        m.add_quad(
            (xa, sgn * (outer_half_width(st_a) - 0.35), st_a - 1.5),
            (xb, sgn * (outer_half_width(st_b) - 0.35), st_b - 1.5),
            (xb, sgn * outer_half_width(st_b + 1.2), st_b + 1.2),
            (xa, sgn * outer_half_width(st_a + 1.2), st_a + 1.2),
            region="trim", expect_n=(0.0, sgn, 0.15), smooth=1,
        )

    # Rear vertical window frame strip (x = 33.6 .. 35.8) & Quarter-glass vertical divider post (x = 67.0 .. 68.4)
    for x_post0, x_post1 in [(33.6, 35.8), (66.9, 68.3)]:
        zp0 = cab_window_sill_z(0.5 * (x_post0 + x_post1))
        zp1 = cab_window_top_z(0.5 * (x_post0 + x_post1))
        yp0 = sgn * (outer_half_width(zp0) - 0.25)
        yp1 = sgn * (outer_half_width(zp1) - 0.25)
        m.add_quad((x_post0, yp0, zp0), (x_post1, yp0, zp0), (x_post1, yp1, zp1), (x_post0, yp1, zp1),
                   region="trim", expect_n=(0.0, sgn, 0.0), smooth=0)
        m.add_quad((x_post0, yp0 - sgn * 0.8, zp0), (x_post1, yp0 - sgn * 0.8, zp0),
                   (x_post1, yp1 - sgn * 0.8, zp1), (x_post0, yp1 - sgn * 0.8, zp1),
                   region="trim", expect_n=(0.0, -sgn, 0.0), smooth=0)

    # Triangular front mirror sail mount (x = 74.5 .. 80.8, z = 45.0 .. 55.2)
    ys_sail = sgn * 42.8
    m.add_tri((74.2, ys_sail, 45.0), (80.8, ys_sail, 45.2), (79.5, ys_sail - sgn * 0.9, 55.5),
              region="trim", expect_n=(0.0, sgn, 0.0), smooth=0, double_sided=True)

    # 3. Sculpted Rounded-Shell 3D Twin-Arm Commercial Wing Mirror (frame_001, 005, 009, 010, 015!)
    # Upper & Lower twin horizontal support arms (leaving open daylight slot between them!)
    m.add_box(75.6, sgn * 42.0, 57.2, 78.0, sgn * 47.0, 59.2, region="trim", smooth=2)
    m.add_box(75.6, sgn * 42.2, 48.4, 78.0, sgn * 47.0, 50.4, region="trim", smooth=2)

    # Contoured aerodynamic OEM mirror housing (smoothly rounded top/bottom & outer shoulder like frame_010!)
    mir_zs = [46.6, 48.0, 54.4, 60.8, 62.2]
    mir_front_grid = []
    mir_back_grid = []
    for iz_m, zm in enumerate(mir_zs):
        end_taper = 1.0 if iz_m in (0, 4) else (0.25 if iz_m in (1, 3) else 0.0)
        y_in_m = sgn * (46.8 + 0.5 * end_taper)
        y_out_m = sgn * (52.7 - 1.1 * end_taper)
        row_f, row_b = [], []
        for uf in (0.0, 0.35, 0.72, 1.0):
            ym = y_in_m + (y_out_m - y_in_m) * uf
            arch_x = math.sin(math.pi * uf) * (1.35 - 0.55 * end_taper)
            xf = 77.6 + arch_x - 0.7 * end_taper
            row_f.append((xf, ym, zm))
            row_b.append((74.05, ym, zm))
        mir_front_grid.append(row_f)
        mir_back_grid.append(row_b)

    m.add_loft(mir_front_grid, region="trim", expect_n=(1.0, 0.0, 0.0), smooth=3)
    m.add_loft(mir_back_grid, region="trim", expect_n=(-1.0, 0.0, 0.0), smooth=1)
    # Stitch perimeter band around mirror housing
    for k in range(len(mir_zs) - 1):
        m.add_quad(mir_front_grid[k][0], mir_back_grid[k][0], mir_back_grid[k + 1][0], mir_front_grid[k + 1][0],
                   region="trim", expect_n=(0.0, -sgn, 0.0), smooth=2)
        m.add_quad(mir_front_grid[k][-1], mir_front_grid[k + 1][-1], mir_back_grid[k + 1][-1], mir_back_grid[k][-1],
                   region="trim", expect_n=(0.0, sgn, 0.0), smooth=3)
    for idx_cap, nz_cap in ((0, -1.0), (-1, 1.0)):
        for j in range(3):
            m.add_quad(mir_front_grid[idx_cap][j], mir_front_grid[idx_cap][j + 1],
                       mir_back_grid[idx_cap][j + 1], mir_back_grid[idx_cap][j],
                       region="trim", expect_n=(0.0, 0.0, nz_cap), smooth=2)

    # Dual-split reflective glass on rear (-X) face: upper flat main mirror + lower convex blind-spot mirror!
    m.add_quad((73.92, sgn * 52.0, 51.8), (73.92, sgn * 47.2, 51.8),
               (73.92, sgn * 47.2, 60.9), (73.92, sgn * 52.0, 60.9),
               region="chrome", expect_n=(-1.0, 0.0, 0.0), smooth=0)
    m.add_quad((73.92, sgn * 51.8, 47.5), (73.92, sgn * 47.2, 47.5),
               (73.92, sgn * 47.2, 51.1), (73.92, sgn * 51.8, 51.1),
               region="chrome", expect_n=(-1.0, 0.0, 0.0), smooth=0)
    # Outer vertical clear/amber turn-signal repeater lens (visible in frame_005, frame_009, frame_015!)
    yt_out = sgn * 52.82
    m.add_box(75.0, yt_out - sgn * 0.25, 49.6, 78.1, yt_out, 54.0, region="chrome")

    return m.export_dict(hinge_pivot=(81.0, sgn * 42.5, 34.0))


# --------------------------------------------------------------------------- 4. Translucent Cab Glass & Wire-Mesh Bulkhead
def _build_glass_and_mesh():
    g = MeshBuilder("glass_cab")

    # 1. Curved Panoramic Laminated Windshield (x = 85.2 -> 48.5, z = 50.8 -> 81.6, y = -35.8 .. +35.8)
    ny_ws = 9
    nu_ws = 5
    ws_grid = []
    for iu in range(nu_ws):
        tf = iu / (nu_ws - 1)   # 0 = bottom cowl, 1 = top roof header
        row = []
        for iy in range(ny_ws):
            yf = -1.0 + 2.0 * iy / (ny_ws - 1)
            w_half = 36.2 * (1.0 - 0.065 * tf)
            y = yf * w_half
            # Authentic lateral windshield crown curvature (center bows forward +2.6u)
            crown_x = 2.6 * (1.0 - yf * yf)
            x_base = (85.2 - 36.4 * tf) + crown_x - 3.2 * (yf * yf)
            z_base = 50.8 + 30.8 * tf - 0.6 * (yf * yf)
            row.append((x_base, y, z_base))
        ws_grid.append(row)

    def ws_uv(p, iu, iy):
        su = 0.03 + 0.44 * (iy / (ny_ws - 1))
        sv = 0.96 - 0.92 * (iu / (nu_ws - 1))
        return (round(su, 5), round(sv, 5))

    g.add_loft(ws_grid, expect_n=(0.64, 0.0, 0.76), smooth=3, uv_fn=ws_uv, double_sided=True)

    # 2. Left & Right Dipping Cab Door Windows + Front Quarter Windows
    for sgn in (1.0, -1.0):
        # Main roll-down cab window (x = 35.8 .. 66.9) & Quarter window (x = 68.3 .. 79.2)
        for x_segs in ([35.8, 44.5, 52.0, 59.5, 66.9], [68.3, 74.0, 79.2]):
            nx = len(x_segs)
            win_g = []
            for iz, vf in enumerate((0.0, 0.5, 1.0)):
                row = []
                for x in x_segs:
                    zb = cab_window_sill_z(x) + 0.8
                    zt = cab_window_top_z(x) - 1.2
                    z = zb + (zt - zb) * vf
                    y = sgn * (outer_half_width(z) - 0.55)
                    row.append((x, y, z))
                win_g.append(row)

            def side_win_uv(p, iz, ix, _nx=nx):
                su = 0.04 + 0.42 * (ix / max(1, _nx - 1))
                sv = 0.95 - 0.90 * (iz / 2.0)
                return (round(su, 5), round(sv, 5))

            g.add_loft(win_g, expect_n=(0.0, sgn, 0.08), smooth=2, uv_fn=side_win_uv, double_sided=True)

    # 3. Full-Width Cab Bulkhead Square Steel Wire-Mesh Safety Screen (x = 31.6, frame_020!)
    # Mapped to right half of veh_van_glass.png (u: 0.52 .. 0.98)
    g.add_quad(
        (31.6, 33.8, 50.6), (31.6, -33.8, 50.6),
        (31.6, -33.8, 80.4), (31.6, 33.8, 80.4),
        region="mesh_screen", expect_n=(-1.0, 0.0, 0.0), smooth=0, double_sided=True,
    )

    return g.export_dict()


# --------------------------------------------------------------------------- 5. Sculpted Hood, Front & Rear Bumpers, Detail
def _build_hood():
    m = MeshBuilder("hood")
    ny = 9
    nx = 5
    grid = []
    for ix in range(nx):
        tf = ix / (nx - 1)   # 0 = cowl (x=84.5), 1 = nose above grille/headlights
        row = []
        for iy in range(ny):
            yf = -1.0 + 2.0 * iy / (ny - 1)
            y = yf * (41.0 - 0.2 * tf)
            ay = abs(y)
            # Front edge of hood follows exact X290 grille top (z=34.4 for |y|<=21.8) & swept headlight top (z=42.8 at |y|=40.8)!
            if ay <= 21.8:
                z_front = 34.4 + 0.3 * ((ay / 21.8) ** 2)
                x_front = 110.2 + nose_planform_dx(y) * 0.52
            else:
                th = min(1.0, (ay - 21.8) / 19.0)
                z_front = 34.7 + 8.1 * (th ** 0.85)
                x_front = 107.6 - 11.6 * th
            x_rear = 84.5 - 2.3 * (yf * yf)
            z_rear = 50.7 - 0.25 * (yf * yf)
            x = x_rear + (x_front - x_rear) * tf
            z = z_rear + (z_front - z_rear) * (tf ** 1.06) + 1.15 * math.sin(math.pi * tf) * (1.0 - 0.35 * yf * yf)
            row.append((x, y, z))
        grid.append(row)

    m.add_loft(grid, region="white", expect_n=(0.45, 0.0, 0.88), smooth=3)
    # Painted white side return lips so hood-to-fender seam never shows a dark gap!
    for idx_y, sgn_y in ((0, -1.0), (ny - 1, 1.0)):
        for ix in range(nx - 1):
            p0, p1 = grid[ix][idx_y], grid[ix + 1][idx_y]
            m.add_quad(
                p0, p1,
                (p1[0] - 0.4, p1[1] - sgn_y * 0.3, p1[2] - 1.1),
                (p0[0] - 0.4, p0[1] - sgn_y * 0.3, p0[2] - 1.1),
                region="white", expect_n=(0.0, sgn_y, 0.0), smooth=2,
            )
    bot_grid = [[(p[0] - 0.5, p[1] * 0.96, p[2] - 1.1) for p in row] for row in grid]
    m.add_loft(bot_grid, region="trim", expect_n=(-0.45, 0.0, -0.88), smooth=0)
    return m.export_dict(hinge_pivot=(84.5, 0.0, 50.7))


def _build_front_bumper_and_fascia():
    m = MeshBuilder("bumper_f")
    ys_f = [-1.0, -0.92, -0.72, -0.55, -0.43, 0.0, 0.43, 0.55, 0.72, 0.92, 1.0]
    zs_bull = [
        (11.8, -3.20),
        (16.0, -0.55),
        (23.2, +1.20),
        (31.2, +0.45),
        (36.8, -1.85),
    ]

    # 1. Curved Planform + Bull-Nose Side-Profile Wraparound Front Bumper (matches frame_005, 009, 010, 015!)
    grid = []
    for z, dx_b in zs_bull:
        chin_w = 43.0 if z >= 22.0 else (38.0 + 5.0 * ((z - 11.8) / 10.2) ** 0.75)
        row = []
        for yf in ys_f:
            y = yf * chin_w
            ay = abs(y)
            xb = 113.5 + dx_b + nose_planform_dx(yf * 43.0)
            if 23.0 <= z <= 34.4 and ay <= 19.0:
                xb -= 1.35
            elif 23.0 <= z <= 34.4 and 24.0 <= ay <= 39.0:
                xb -= 0.70
            row.append((xb, y, z))
        grid.append(row)

    m.add_loft(grid, region="front", expect_n=(1.0, 0.0, 0.0), smooth=3)

    # 2. Swept Crystalline Cat-Eye Headlight Lenses (bridging z=34.2..42.8 seamlessly between bumper & hood!)
    for sgn in (-1.0, 1.0):
        idx_c = -1 if sgn > 0 else 0
        p_bump_top = grid[4][idx_c]
        hl_pts = [
            (109.8, sgn * 21.8, 34.2),
            (100.6, sgn * 41.4, 36.8),
            (96.0,  sgn * 40.8, 42.8),
            (107.0, sgn * 23.6, 38.4),
        ]
        m.add_quad(*hl_pts, region="front", expect_n=(0.82, sgn * 0.42, 0.38), smooth=3)
        # Outer wrap-around corner of headlight lens meeting bumper top & front fender seamlessly
        m.add_tri(
            (100.6, sgn * 41.4, 36.8),
            p_bump_top,
            (96.0,  sgn * 40.8, 42.8),
            region="white",
            expect_n=(0.25, sgn * 0.92, 0.25), smooth=3,
        )

    # 3. True 3D Hollow Chrome Ring Emblem + Horizontal Bar (smooth circular chrome UVs - zero radial stripes!)
    r_in_b, r_out_b = 2.45, 3.35
    x_em = 113.65
    n_em = 24
    for i in range(n_em):
        a0 = 2.0 * math.pi * i / n_em
        a1 = 2.0 * math.pi * ((i + 1) % n_em) / n_em
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        uv0_i = uv_in_rect(R_CHROME, 0.5 + 0.26 * c0, 0.5 - 0.26 * s0)
        uv0_o = uv_in_rect(R_CHROME, 0.5 + 0.38 * c0, 0.5 - 0.38 * s0)
        uv1_o = uv_in_rect(R_CHROME, 0.5 + 0.38 * c1, 0.5 - 0.38 * s1)
        uv1_i = uv_in_rect(R_CHROME, 0.5 + 0.26 * c1, 0.5 - 0.26 * s1)
        m.add_quad(
            (x_em, c0 * r_in_b, 28.8 + s0 * r_in_b),
            (x_em, c0 * r_out_b, 28.8 + s0 * r_out_b),
            (x_em, c1 * r_out_b, 28.8 + s1 * r_out_b),
            (x_em, c1 * r_in_b, 28.8 + s1 * r_in_b),
            uvs=[uv0_i, uv0_o, uv1_o, uv1_i],
            expect_n=(1.0, 0.0, 0.0), smooth=3,
        )
    m.add_box(x_em - 0.5, -3.35, 28.35, x_em + 0.2, 3.35, 29.25, region="chrome")

    # 4. Left & Right Bumper Wraparound Side Wings Stitched Directly to Front Wheel Arch Flare (cx=80, cz=14.2, r=23.2)!
    for sgn in (-1.0, 1.0):
        idx_c = -1 if sgn > 0 else 0
        wing_grid = []
        for iz_w, (z, _) in enumerate(zs_bull):
            p_front = grid[iz_w][idx_c]
            dz_a = min(22.8, max(-2.5, z - 14.2))
            x_arch = 80.0 + math.sqrt(max(0.0, 23.2 * 23.2 - dz_a * dz_a))
            y_arch = sgn * (43.05 if z >= 22.0 else (38.5 + 4.55 * ((z - 11.8) / 10.2) ** 0.75))
            p_rear = (x_arch, y_arch, z)
            p_mid = (0.52 * p_front[0] + 0.48 * p_rear[0] + 0.7, sgn * (0.5 * (abs(p_front[1]) + abs(y_arch))), z)
            if sgn > 0:
                wing_grid.append([p_rear, p_mid, p_front])
            else:
                wing_grid.append([p_front, p_mid, p_rear])
        m.add_loft(wing_grid, region="trim", expect_n=(0.2, sgn, 0.0), smooth=3)

    # Bottom splash pan stitched directly to grid[0]
    m.add_quad(
        (96.0, -37.5, 11.8), grid[0][2], grid[0][-3], (96.0, 37.5, 11.8),
        region="trim", expect_n=(0.0, 0.0, -1.0), smooth=0,
    )

    return m.export_dict()


def _build_rear_step_bumper():
    m = MeshBuilder("bumper_r")
    # 1. Center Walk-In Non-Slip Step Bumper (z = 13.2 .. 16.6 <= 18u Quake step, exposing lower rear tires like frame_020!)
    m.add_box(-113.0, -34.2, 13.2, -107.6, 34.2, 16.6, region="trim")
    # 2. Left & Right Matte-Black Rear Corner Bumper Blocks beneath D-pillar taillights (tapered bottom z=13.2)
    for sgn in (-1.0, 1.0):
        reg_s = "side_l" if sgn > 0 else "side_r"
        m.add_box(
            -112.8, sgn * 33.4, 13.2, -84.2, sgn * 43.1, 33.5,
            region="trim",
            face_regions={"+y" if sgn > 0 else "-y": reg_s, "-x": "rear_frame"},
        )
    return m.export_dict()


def _build_detail_vib():
    m = MeshBuilder("detail_vib")
    # 1. Center Roof Forehead Teardrop Antenna Base + Whip Rod (exact match to frame_009 & frame_010!)
    m.add_box(37.6, -0.75, 88.2, 39.8, 0.75, 89.8, region="trim")
    m.add_cylinder((38.6, 0.0, 89.5), (35.8, 0.0, 104.2), 0.26, 0.12, segs=6, region="trim", smooth=2)
    # 2. Rear Underbody Steel Exhaust / Tow Loop tucked right beneath z=13.2 step bumper (frame_001 & frame_020!)
    m.add_cylinder((-92.0, -21.5, 12.2), (-109.5, -22.5, 12.0), 1.05, 1.05, segs=10, region="chrome", smooth=2)
    return m.export_dict()


# --------------------------------------------------------------------------- 6. Main Body Shell, Cargo Bay & Cockpit ('chassis')
def _build_chassis_and_interior():
    m = MeshBuilder("chassis")

    # ---- A. EXTERIOR LEFT (+Y) & RIGHT (-Y) CARGO BODY + CAB FENDERS ----
    # Exact continuous roof-shoulder curve shared 1:1 by cargo walls, cab cant-rail & crowned roof!
    def z_roof_sh(x):
        zc = roof_or_hood_z_at_x(x)
        t_fh = max(0.0, min(1.0, (x - 18.0) / 30.5))
        return zc - (2.3 - 0.9 * t_fh)

    def cargo_z_profile(x):
        zsh = z_roof_sh(x)
        return [
            10.5, 13.6, 23.8, 33.5, 47.5, 66.0, 83.5,
            83.5 + 0.50 * (zsh - 83.5),
            83.5 + 0.82 * (zsh - 83.5),
            zsh,
        ]

    x_cargo = [-108.0, -96.0, -84.2, -68.0, -51.8, -36.0, -24.0, 4.0, 18.0, 26.0, 33.6]

    for sgn in (1.0, -1.0):
        reg_s = "side_l" if sgn > 0 else "side_r"
        for ix in range(len(x_cargo) - 1):
            xa, xb = x_cargo[ix], x_cargo[ix + 1]
            xm = 0.5 * (xa + xb)
            in_rear_arch = (-86.0 < xm < -50.0)
            zla = cargo_z_profile(xa)
            zlb = cargo_z_profile(xb)
            for iz in range(len(zla) - 1):
                za0, za1 = zla[iz], zla[iz + 1]
                zb0, zb1 = zlb[iz], zlb[iz + 1]
                zm = 0.5 * (za0 + za1)
                # Leave clean wheel-arch cutout over rear axle (-68.0, z < 33.5)
                if in_rear_arch and zm < 33.2:
                    continue
                # Slight 3D step-out for lower black rub-strip cladding (z = 13.6 .. 23.8)
                pad_y = 0.48 if (iz == 1 and xm > -50.0) else 0.0
                # Slight rear D-pillar forward rake above z = 55
                dxa0 = 2.0 * (((max(0.0, za0 - 55.0)) / 46.2) ** 1.6) if xa <= -107.9 else 0.0
                dxb0 = 2.0 * (((max(0.0, zb0 - 55.0)) / 46.2) ** 1.6) if xb <= -107.9 else 0.0
                dxa1 = 2.0 * (((max(0.0, za1 - 55.0)) / 46.2) ** 1.6) if xa <= -107.9 else 0.0
                dxb1 = 2.0 * (((max(0.0, zb1 - 55.0)) / 46.2) ** 1.6) if xb <= -107.9 else 0.0

                ya0 = sgn * (outer_half_width(za0) + pad_y)
                ya1 = sgn * (outer_half_width(za1) + pad_y)
                yb0 = sgn * (outer_half_width(zb0) + pad_y)
                yb1 = sgn * (outer_half_width(zb1) + pad_y)
                m.add_quad(
                    (xa + dxa0, ya0, za0),
                    (xb + dxb0, yb0, zb0),
                    (xb + dxb1, yb1, zb1),
                    (xa + dxa1, ya1, za1),
                    region=reg_s, expect_n=(0.0, sgn, 0.14 if za0 > 83 else 0.0), smooth=2,
                )

        # Passenger (-Y) Side 3D Sliding Door Track Rail + Handle (frame_005 & frame_009!)
        if sgn < 0:
            yr = -43.0
            m.add_box(-80.5, yr - 0.55, 45.6, -24.0, yr, 47.9, region="chrome")
            m.add_box(-80.8, yr - 0.65, 45.5, -78.2, yr, 48.0, region="trim")
            m.add_box(-26.5, yr - 0.65, 45.5, -23.8, yr, 48.0, region="trim")
            m.add_box(25.2, yr - 0.45, 39.8, 28.8, yr + 0.35, 47.4, region="trim")

        # Watertight Sculpted Front Cab Fender Bridging Wheel Arch Flare, Cab Door, Headlight & Hood!
        fend_bot = [
            (80.0,  sgn * 43.05, 37.4),
            (85.5,  sgn * 43.05, 36.7),
            (91.0,  sgn * 43.05, 34.6),
            (95.4,  sgn * 43.05, 31.6),
            (100.6, sgn * 41.40, 36.8),
        ]
        fend_top = [
            (80.0,  sgn * 42.20, 51.0),
            (84.5,  sgn * 40.80, 50.6),
            (90.5,  sgn * 40.80, 46.5),
            (96.0,  sgn * 40.80, 42.8),
            (100.6, sgn * 41.40, 36.8),
        ]
        for kf in range(len(fend_bot) - 1):
            if kf < len(fend_bot) - 2:
                m.add_quad(
                    fend_bot[kf], fend_bot[kf + 1], fend_top[kf + 1], fend_top[kf],
                    region="white", expect_n=(0.15, sgn, 0.22), smooth=3,
                )
            else:
                m.add_tri(
                    fend_bot[kf], fend_bot[kf + 1], fend_top[kf],
                    region="white", expect_n=(0.20, sgn, 0.22), smooth=3,
                )

        # Sculpted 3D White A-Pillar (x = 84.5 -> 48.5, z = 50.8 -> 81.6)
        ap_steps = 6
        for k in range(ap_steps):
            t0, t1 = k / ap_steps, (k + 1) / ap_steps
            xa0, za0 = 84.5 - 36.0 * t0, 50.8 + 30.8 * t0
            xa1, za1 = 84.5 - 36.0 * t1, 50.8 + 30.8 * t1
            yo0, yo1 = sgn * outer_half_width(za0), sgn * outer_half_width(za1)
            yi0, yi1 = sgn * (36.2 * (1.0 - 0.065 * t0)), sgn * (36.2 * (1.0 - 0.065 * t1))
            # Front-facing A-pillar surface
            m.add_quad(
                (xa0 - 2.4, yo0, za0), (xa0 + 1.8, yi0, za0),
                (xa1 + 1.8, yi1, za1), (xa1 - 2.4, yo1, za1),
                region="white", expect_n=(0.55, sgn * 0.55, 0.62), smooth=3,
            )
            # Side-facing A-pillar cheek bridging down to cab window arch!
            z_win0 = cab_window_top_z(max(48.0, xa0 - 4.0))
            z_win1 = cab_window_top_z(max(48.0, xa1 - 4.0))
            m.add_quad(
                (xa0 - 4.5, sgn * outer_half_width(z_win0), z_win0),
                (xa0 - 2.4, yo0, za0),
                (xa1 - 2.4, yo1, za1),
                (xa1 - 4.5, sgn * outer_half_width(z_win1), z_win1),
                region="white", expect_n=(0.05, sgn, 0.15), smooth=3,
            )

        # Cab Upper Cant-Rail & Forehead Side Cheek (stitched 1:1 to z_roof_sh(x) - ZERO roof ears!)
        cx_pts = [33.6, 38.5, 43.5, 48.5]
        for k in range(len(cx_pts) - 1):
            xa, xb = cx_pts[k], cx_pts[k + 1]
            zba, zbb = cab_window_top_z(xa) + 0.6, cab_window_top_z(xb) + 0.6
            zta, ztb = z_roof_sh(xa), z_roof_sh(xb)
            m.add_quad(
                (xa, sgn * outer_half_width(zba), zba),
                (xb, sgn * outer_half_width(zbb), zbb),
                (xb, sgn * outer_half_width(ztb), ztb),
                (xa, sgn * outer_half_width(zta), zta),
                region="white", expect_n=(0.18, sgn, 0.32), smooth=3,
            )

        # 3D Matte-Black Wheel Arch Flares + Semicircular Sealed Wheelhouse Drums (ZERO cargo arch poke!)
        for wx in (-68.0, 80.0):
            r_in = 16.0
            r_fl = 23.2
            n_ar = 16
            yf_out = sgn * 44.1
            yf_body = sgn * 43.05
            yf_deep = sgn * 32.8
            for k in range(n_ar):
                a0 = math.pi * k / n_ar
                a1 = math.pi * (k + 1) / n_ar
                x_i0, z_i0 = wx - math.cos(a0) * r_in, 14.2 + math.sin(a0) * r_in
                x_i1, z_i1 = wx - math.cos(a1) * r_in, 14.2 + math.sin(a1) * r_in
                x_o0, z_o0 = wx - math.cos(a0) * r_fl, 14.2 + math.sin(a0) * r_fl
                x_o1, z_o1 = wx - math.cos(a1) * r_fl, 14.2 + math.sin(a1) * r_fl
                # Outer sculpted black plastic arch flare face
                m.add_quad((x_i0, yf_out, z_i0), (x_o0, yf_body, z_o0),
                           (x_o1, yf_body, z_o1), (x_i1, yf_out, z_i1),
                           region="trim", expect_n=(0.0, sgn, 0.1), smooth=2)
                # Inner wheelhouse arch drum (blocks all light leaks behind wheels!)
                m.add_quad((x_i0, yf_out, z_i0), (x_i1, yf_out, z_i1),
                           (x_i1, yf_deep, z_i1), (x_i0, yf_deep, z_i0),
                           region="trim", expect_n=(math.cos(a0), 0.0, -math.sin(a0)), smooth=1)
                # Semicircular back wall of wheelhouse drum (stays strictly inside white rounded cargo arch!)
                m.add_tri(
                    (wx, yf_deep, 14.2), (x_i0, yf_deep, z_i0), (x_i1, yf_deep, z_i1),
                    region="trim", expect_n=(0.0, sgn, 0.0), smooth=0, double_sided=True,
                )

    # ---- B. CROWNED H2 HIGH-ROOF & AERODYNAMIC FOREHEAD ABOVE WINDSHIELD ----
    roof_xs = [-106.0, -96.0, -68.0, -24.0, 4.0, 18.0, 26.0, 33.6, 38.5, 43.5, 48.5]
    roof_yf = [-1.0, -0.86, -0.60, -0.28, 0.0, 0.28, 0.60, 0.86, 1.0]
    roof_grid = []
    for x in roof_xs:
        zc = roof_or_hood_z_at_x(x)
        z_sh = z_roof_sh(x)
        y_span = outer_half_width(z_sh)
        t_fh = max(0.0, min(1.0, (x - 22.0) / 26.5))
        row = []
        for yf in roof_yf:
            y = yf * y_span
            z = zc - (zc - z_sh) * (yf * yf)
            # Bow center forehead slightly forward (+1.2u) while outer edges stay pinned at exact x!
            dx = 1.2 * (1.0 - yf * yf) * math.sin(math.pi * t_fh)
            row.append((x + dx, y, z))
        roof_grid.append(row)
    m.add_loft(roof_grid, region="top", expect_n=(0.18, 0.0, 0.98), smooth=3)

    # Black Windshield Wiper Cowl Plenum + Two 3D Articulated Wipers (frame_009 & frame_010!)
    m.add_box(82.5, -38.5, 49.6, 86.2, 38.5, 51.2, region="trim")
    for wy0, wy1, wx_tip, wz_tip in [(31.0, 4.0, 80.5, 54.5), (2.0, -28.0, 81.2, 54.0)]:
        m.add_cylinder((84.8, wy0, 51.3), (wx_tip, wy1, wz_tip), 0.38, 0.25, segs=6, region="trim", smooth=1)
        m.add_box(wx_tip - 0.6, wy1 - 7.5, wz_tip - 0.3, wx_tip + 0.5, wy1 + 7.5, wz_tip + 0.4, region="trim")

    # Engine Bay Under Hood (visible when hood pops in CatchFire / Viewer!)
    m.add_box(82.0, -34.0, 15.0, 104.0, 34.0, 33.5, region="engine")

    # ---- C. REAR APERTURE FRAME, D-PILLAR 3D TAILLIGHTS & 3RD BRAKE LIGHT ----
    for sgn in (1.0, -1.0):
        # Lower D-pillar & 3D Ruby-Red Vertical Taillight Housing (z = 33.5 .. 59.5, frame_001 & frame_020!)
        for za, zb in [(33.5, 47.5), (47.5, 59.5), (59.5, 83.5), (83.5, 97.0)]:
            yo_a, yo_b = sgn * outer_half_width(za), sgn * outer_half_width(zb)
            yi = sgn * 33.2
            xa = -108.0 + 2.0 * (((max(0.0, za - 55.0)) / 46.2) ** 1.6)
            xb = -108.0 + 2.0 * (((max(0.0, zb - 55.0)) / 46.2) ** 1.6)
            # Bulge taillight lens 0.7u rearward for crisp 3D catchlight!
            bulge = -0.65 if za < 59.0 else 0.0
            m.add_quad((xa + bulge, yo_a, za), (xa, yi, za), (xb, yi, zb), (xb + bulge, yo_b, zb),
                       region="rear_frame", expect_n=(-1.0, 0.0, 0.0), smooth=2)
            # Inner doorway vertical jamb flange
            m.add_quad((xa, yi, za), (xa + 2.5, yi, za), (xb + 2.5, yi, zb), (xb, yi, zb),
                       region="white", expect_n=(0.0, -sgn, 0.0), smooth=0)

    # Rear Roof Header Bar + 3D Red High-Mount 3rd Brake Light (z = 96.8 .. 101.2, frame_001 & frame_020!)
    m.add_quad((-106.0, 36.2, 96.8), (-106.0, -36.2, 96.8), (-105.6, -31.5, 101.2), (-105.6, 31.5, 101.2),
               region="rear_frame", expect_n=(-1.0, 0.0, 0.1), smooth=2)
    m.add_box(-106.5, -6.8, 98.1, -105.5, 6.8, 100.7, region="rear_frame", skip_faces=("+x",))
    # Rear doorway threshold riser (z = 16.4 .. 19.5)
    m.add_quad((-108.0, 33.4, 16.4), (-108.0, -33.4, 16.4), (-108.0, -33.4, 19.5), (-108.0, 33.4, 19.5),
               region="white", expect_n=(-1.0, 0.0, 0.0), smooth=0)

    # ---- D. UNDERCARRIAGE CHASSIS FRAME RAILS & SOLID REAR AXLE ----
    m.add_box(-92.0, -26.5, 14.8, 84.0, 26.5, 18.8, region="trim", skip_faces=("+z",))
    m.add_cylinder((-68.0, -35.5, 15.2), (-68.0, 35.5, 15.2), 1.45, 1.45, segs=8, region="trim")
    m.add_cylinder((80.0, -35.5, 15.2),  (80.0, 35.5, 15.2),  1.35, 1.35, segs=8, region="trim")

    # ---- E. WALK-IN CARGO HOLD INTERIOR (frame_001 & frame_020!) ----
    # 1. Bright White/Silver Corrugated Cargo Floor (z = 19.5) + Raised 3D Anti-Skid Ribs!
    m.add_quad((-108.0, 39.6, 19.5), (-108.0, -39.6, 19.5), (32.0, -39.6, 19.5), (32.0, 39.6, 19.5),
               region="cargo_floor", expect_n=(0.0, 0.0, 1.0), smooth=0)
    for ry in (-25.0, -18.8, -12.5, -6.2, 0.0, 6.2, 12.5, 18.8, 25.0):
        m.add_box(-105.5, ry - 1.2, 19.5, 31.0, ry + 1.2, 20.05, region="cargo_floor", skip_faces=("-z",))
    # Brushed steel rear doorway scuff plate
    m.add_box(-108.0, -33.2, 19.45, -104.2, 33.2, 19.75, region="chrome", skip_faces=("-z",))

    # 2. Matte-Black Lower Cargo Wall Liners (z = 19.5 .. 47.0) + Upper White Stamped Cargo Walls (z = 47.0 .. 96.8)
    for sgn in (1.0, -1.0):
        yi_low = sgn * 39.6
        yi_mid = sgn * 38.8
        yi_top = sgn * 34.8
        m.add_quad((-107.0, yi_low, 19.5), (31.8, yi_low, 19.5), (31.8, yi_mid, 47.0), (-107.0, yi_mid, 47.0),
                   region="liner_blk", expect_n=(0.0, -sgn, 0.0), smooth=0)
        m.add_quad((-106.5, yi_mid, 47.0), (31.8, yi_mid, 47.0), (31.8, yi_top, 96.8), (-105.8, yi_top, 96.8),
                   region="cargo_wall", expect_n=(0.0, -sgn, -0.08), smooth=1)

        # 3D Horizontal Mid-Height Perforated Box-Rail (z = 68.8 .. 73.6, strictly inside tumblehome!)
        y_mr_out = sgn * (outer_half_width(73.6) - 1.1)
        y_mr_in  = sgn * (outer_half_width(73.6) - 2.9)
        m.add_box(-105.5, y_mr_in, 68.8, 31.2, y_mr_out, 73.6, region="cargo_wall")

        # 4 Curved Vertical 3D White Stamped Cargo Wall Pillars per side (follows tumblehome so ZERO exterior poke!)
        for px in (-93.0, -64.0, -31.0, 1.5):
            pz_s = [47.0, 68.8, 83.5, 95.8]
            for kz in range(len(pz_s) - 1):
                za_p, zb_p = pz_s[kz], pz_s[kz + 1]
                yo_a, yo_b = sgn * (outer_half_width(za_p) - 1.0), sgn * (outer_half_width(zb_p) - 1.0)
                yi_a, yi_b = sgn * (outer_half_width(za_p) - 2.8), sgn * (outer_half_width(zb_p) - 2.8)
                # Inner face & front/rear flange faces of pillar
                m.add_quad((px - 2.0, yi_a, za_p), (px + 2.0, yi_a, za_p),
                           (px + 2.0, yi_b, zb_p), (px - 2.0, yi_b, zb_p),
                           region="cargo_wall", expect_n=(0.0, -sgn, 0.0), smooth=1)
                m.add_quad((px + 2.0, yi_a, za_p), (px + 2.0, yo_a, za_p),
                           (px + 2.0, yo_b, zb_p), (px + 2.0, yi_b, zb_p),
                           region="cargo_wall", expect_n=(1.0, 0.0, 0.0), smooth=0)
                m.add_quad((px - 2.0, yo_a, za_p), (px - 2.0, yi_a, za_p),
                           (px - 2.0, yi_b, zb_p), (px - 2.0, yo_b, zb_p),
                           region="cargo_wall", expect_n=(-1.0, 0.0, 0.0), smooth=0)

        # 3. Watertight Sculpted 3D Rounded White Radially-Fluted Wheel Arch Housing (x = -85.2 .. -50.8, frame_001!)
        arch_segs = 16
        y_arch_wall = sgn * 39.6
        y_arch_bev  = sgn * 31.4
        y_arch_in   = sgn * 29.2
        for k in range(arch_segs):
            a0 = math.pi * k / arch_segs
            a1 = math.pi * (k + 1) / arch_segs
            xa0, za0 = -68.0 - math.cos(a0) * 17.2, 19.5 + math.sin(a0) * 18.6
            xa1, za1 = -68.0 - math.cos(a1) * 17.2, 19.5 + math.sin(a1) * 18.6
            xb0, zb0 = -68.0 - math.cos(a0) * 16.2, 19.5 + math.sin(a0) * 16.6
            xb1, zb1 = -68.0 - math.cos(a1) * 16.2, 19.5 + math.sin(a1) * 16.6

            su0, su1 = k / arch_segs, (k + 1) / arch_segs
            m.add_quad(
                (xa0, y_arch_wall, za0), (xa1, y_arch_wall, za1),
                (xa1, y_arch_bev,  za1), (xa0, y_arch_bev,  za0),
                uvs=[uv_in_rect(R_ARCH_WHITE, su0, 0.08), uv_in_rect(R_ARCH_WHITE, su1, 0.08),
                     uv_in_rect(R_ARCH_WHITE, su1, 0.44), uv_in_rect(R_ARCH_WHITE, su0, 0.44)],
                expect_n=(-math.cos(a0), -sgn * 0.25, math.sin(a0)), smooth=3,
            )
            m.add_quad(
                (xa0, y_arch_bev, za0), (xa1, y_arch_bev, za1),
                (xb1, y_arch_in,  zb1), (xb0, y_arch_in,  zb0),
                uvs=[uv_in_rect(R_ARCH_WHITE, su0, 0.44), uv_in_rect(R_ARCH_WHITE, su1, 0.44),
                     uv_in_rect(R_ARCH_WHITE, su1, 0.70), uv_in_rect(R_ARCH_WHITE, su0, 0.70)],
                expect_n=(-math.cos(a0) * 0.5, -sgn * 0.8, math.sin(a0) * 0.5), smooth=3,
            )
            m.add_tri(
                (-68.0, y_arch_in, 19.5), (xb0, y_arch_in, zb0), (xb1, y_arch_in, zb1),
                uvs=[uv_in_rect(R_ARCH_WHITE, 0.5, 0.95), uv_in_rect(R_ARCH_WHITE, su0, 0.35), uv_in_rect(R_ARCH_WHITE, su1, 0.35)],
                expect_n=(0.0, -sgn, 0.0), smooth=3,
            )

    # 4. Curved White Cargo Ceiling + 6 Perforated 3D Ceiling Cross-Bows (strictly inside roof crown!)
    ceil_ys = [-32.5, -18.5, 0.0, 18.5, 32.5]
    ceil_zs = [96.5, 98.2, 99.0, 98.2, 96.5]
    for k in range(len(ceil_ys) - 1):
        m.add_quad(
            (-105.5, ceil_ys[k], ceil_zs[k]), (31.8, ceil_ys[k], ceil_zs[k]),
            (31.8, ceil_ys[k + 1], ceil_zs[k + 1]), (-105.5, ceil_ys[k + 1], ceil_zs[k + 1]),
            region="ceil_white", expect_n=(0.0, 0.0, -1.0), smooth=2,
        )
    for bx in (-96.0, -74.0, -50.0, -26.0, -2.0, 20.0):
        for k in range(len(ceil_ys) - 1):
            m.add_box(bx - 1.8, ceil_ys[k], ceil_zs[k] - 1.5, bx + 1.8, ceil_ys[k + 1], ceil_zs[k + 1] - 0.1,
                      region="ceil_white")

    # 5. Tucked Over-Cab Dark Storage Shelf Recess (strictly inside sloped H2 forehead - ZERO poke!)
    m.add_quad((31.8, -33.5, 80.6), (46.5, -31.0, 80.6), (46.5, 31.0, 80.6), (31.8, 33.5, 80.6),
               region="liner_blk", expect_n=(0.0, 0.0, 1.0), smooth=0)
    m.add_quad((46.5, -31.0, 80.6), (31.8, -32.0, 95.8), (31.8, 32.0, 95.8), (46.5, 31.0, 80.6),
               region="liner_blk", expect_n=(-0.7, 0.0, -0.7), smooth=1)
    # Small white center roof latch tab above over-cab shelf (exact detail in frame_020!)
    m.add_box(31.2, -2.4, 95.0, 32.6, 2.4, 96.5, region="white")

    # Lower Bulkhead Partition: white corrugated lower kick-base (z = 19.5..24.2) + dark molded lower bulkhead (z = 24.2..50.6)
    # Matches frame_020 1:1 while Quake/Viewer collision keeps central 32u aisle walkable!
    m.add_box(31.2, -39.2, 19.5, 32.2, 39.2, 24.2, region="cargo_wall")
    m.add_box(31.2, -39.2, 24.2, 32.4, 39.2, 50.6, region="liner_blk")
    # Dark outer B-pillar window borders (|y| = 31.5 .. 38.0, leaving full 63u window open so BOTH seats & headrests show!)
    for sgn in (1.0, -1.0):
        m.add_box(31.2, sgn * 31.5, 50.6, 32.6, sgn * 37.8, 80.4, region="trim")
    m.add_box(31.2, -34.6, 49.6, 32.4, 34.6, 51.2, region="trim")
    m.add_box(31.2, -34.6, 79.8, 32.4, 34.6, 81.0, region="trim")

    # ---- F. FULL CAB COCKPIT: SEATS, HEADRESTS, DASHBOARD, SHIFTER, STEERING WHEEL & MIRROR ----
    m.add_box(32.4, -39.0, 19.2, 84.5, 39.0, 20.2, region="trim", skip_faces=("-z",))

    # Two Sculpted Commercial Charcoal Cloth Bucket Seats + Contoured Headrests (y = +19.2 Driver, -19.2 Passenger)
    for sy in (19.2, -19.2):
        # Black steel seat riser pedestal
        m.add_box(42.0, sy - 8.5, 20.2, 55.5, sy + 8.5, 29.2, region="trim")
        # Bolstered seat squab cushion
        m.add_box(41.5, sy - 10.6, 29.2, 58.5, sy + 10.6, 34.5, region="seat", smooth=2)
        m.add_box(42.0, sy - 11.4, 30.2, 57.5, sy - 8.6,  36.0, region="seat", smooth=2)
        m.add_box(42.0, sy + 8.6,  30.2, 57.5, sy + 11.4, 36.0, region="seat", smooth=2)
        # Reclined contoured backrest (x = 42.5 -> 36.8, z = 34.0 -> 61.2)
        bk_grid = [
            [(42.8, sy - 10.4, 34.0), (43.4, sy, 34.0), (42.8, sy + 10.4, 34.0)],
            [(40.2, sy - 10.2, 48.0), (40.8, sy, 48.0), (40.2, sy + 10.2, 48.0)],
            [(37.6, sy - 8.6,  60.8), (38.0, sy, 61.2), (37.6, sy + 8.6,  60.8)],
        ]
        m.add_loft(bk_grid, region="seat", expect_n=(1.0, 0.0, 0.15), smooth=3)
        bk_back = [[(p[0] - 3.6, p[1], p[2]) for p in row] for row in bk_grid]
        m.add_loft(bk_back, region="seat", expect_n=(-1.0, 0.0, 0.12), smooth=3)
        for s_side, n_side in ((0, -1.0), (2, 1.0)):
            for k in range(2):
                m.add_quad(bk_grid[k][s_side], bk_back[k][s_side], bk_back[k + 1][s_side], bk_grid[k + 1][s_side],
                           region="seat", expect_n=(0.0, n_side, 0.0), smooth=2)
        # Twin chrome headrest posts + Rounded Trapezoid Commercial Headrest (frame_010 & frame_020!)
        for py_off in (-3.2, 3.2):
            m.add_cylinder((36.2, sy + py_off, 60.5), (35.8, sy + py_off, 63.8), 0.45, segs=6, region="chrome")
        hr_f = [
            [(37.2, sy - 5.8, 63.0), (37.5, sy, 63.0), (37.2, sy + 5.8, 63.0)],
            [(36.9, sy - 5.5, 67.5), (37.2, sy, 67.5), (36.9, sy + 5.5, 67.5)],
            [(36.5, sy - 4.4, 71.2), (36.8, sy, 71.5), (36.5, sy + 4.4, 71.2)],
        ]
        hr_b = [[(p[0] - 2.8, p[1], p[2]) for p in row] for row in hr_f]
        m.add_loft(hr_f, region="seat", expect_n=(1.0, 0.0, 0.0), smooth=3)
        m.add_loft(hr_b, region="seat", expect_n=(-1.0, 0.0, 0.0), smooth=3)
        m.add_quad(hr_f[2][0], hr_f[2][2], hr_b[2][2], hr_b[2][0], region="seat", expect_n=(0.0, 0.0, 1.0), smooth=3)
        m.add_quad(hr_f[0][0], hr_b[0][0], hr_f[2][0], hr_b[2][0], region="seat", expect_n=(0.0, -1.0, 0.0), smooth=2)
        m.add_quad(hr_f[0][2], hr_b[0][2], hr_b[2][2], hr_f[2][2], region="seat", expect_n=(0.0, 1.0, 0.0), smooth=2)

    # Wraparound Fiat Ducato / ProMaster Dashboard + Gauge Binnacle + Dash-Mounted 6-Speed Shifter!
    m.add_box(68.0, -38.5, 31.5, 84.0, 38.5, 49.8, region="trim", face_regions={"-x": "dash"})
    # Hooded driver instrument binnacle (y = +12.5 .. +29.5)
    m.add_box(66.5, 12.5, 49.5, 78.5, 29.5, 53.5, region="trim", smooth=2)
    # Dash-mounted 6-speed shifter pod & angled chrome/black gearstick (signature Ducato feature!)
    m.add_box(63.5, 5.5, 36.5, 68.5, 12.0, 42.5, region="trim")
    m.add_cylinder((64.5, 8.8, 42.2), (61.2, 9.2, 46.8), 0.45, 0.55, segs=8, region="chrome")
    m.add_box(60.4, 8.2, 46.4, 62.2, 10.2, 48.2, region="trim", smooth=2)

    # 3D Driver Pedals (clutch, brake, accelerator)
    for py_ped in (26.0, 21.5, 17.0):
        m.add_box(76.0, py_ped - 1.3, 22.5, 77.5, py_ped + 1.3, 26.5, region="trim")

    # Steering Column + Stalks + Continuous Stitched 3D Torus Steering Wheel (peeking cleanly above binnacle in frame_010!)
    sw_c = (62.2, 20.6, 49.8)
    tilt = math.radians(28.0)   # Wheel normal points (-cos 28, 0, +sin 28) toward driver's chest/head
    sw_n = (-math.cos(tilt), 0.0, math.sin(tilt))
    sw_u = (0.0, 1.0, 0.0)
    sw_v = v_norm(v_cross(sw_u, sw_n))
    m.add_cylinder((70.5, 20.6, 46.2), sw_c, 2.0, 1.6, segs=10, region="trim")
    # Center airbag hub + 3 spokes (at 4, 8, and 6 o'clock so top arc is 100% unobstructed!)
    m.add_cylinder(v_sub(sw_c, v_mul(sw_n, 1.1)), v_add(sw_c, v_mul(sw_n, 0.7)), 2.5, 2.2, segs=12, region="trim")
    r_wheel_sw = 6.8
    r_tube_sw = 0.62
    for spk_deg in (-15.0, -165.0, -90.0):
        sr = math.radians(spk_deg)
        p_rim = v_add(sw_c, v_mul(v_add(v_mul(sw_u, math.cos(sr)), v_mul(sw_v, math.sin(sr))), r_wheel_sw - 0.4))
        m.add_cylinder(sw_c, p_rim, 0.65, 0.50, segs=6, region="trim")
    n_sw = 24
    n_tb = 6
    for i in range(n_sw):
        a0 = 2.0 * math.pi * i / n_sw
        a1 = 2.0 * math.pi * ((i + 1) % n_sw) / n_sw
        rdir0 = v_add(v_mul(sw_u, math.cos(a0)), v_mul(sw_v, math.sin(a0)))
        rdir1 = v_add(v_mul(sw_u, math.cos(a1)), v_mul(sw_v, math.sin(a1)))
        c_p0 = v_add(sw_c, v_mul(rdir0, r_wheel_sw))
        c_p1 = v_add(sw_c, v_mul(rdir1, r_wheel_sw))
        for j in range(n_tb):
            b0 = 2.0 * math.pi * j / n_tb
            b1 = 2.0 * math.pi * ((j + 1) % n_tb) / n_tb
            n00 = v_add(v_mul(rdir0, math.cos(b0)), v_mul(sw_n, math.sin(b0)))
            n01 = v_add(v_mul(rdir0, math.cos(b1)), v_mul(sw_n, math.sin(b1)))
            n10 = v_add(v_mul(rdir1, math.cos(b0)), v_mul(sw_n, math.sin(b0)))
            n11 = v_add(v_mul(rdir1, math.cos(b1)), v_mul(sw_n, math.sin(b1)))
            m.add_quad(
                v_add(c_p0, v_mul(n00, r_tube_sw)),
                v_add(c_p1, v_mul(n10, r_tube_sw)),
                v_add(c_p1, v_mul(n11, r_tube_sw)),
                v_add(c_p0, v_mul(n01, r_tube_sw)),
                region="trim", expect_n=n00, smooth=3,
            )

    # Interior Center Rearview Mirror + Black Sensor Mount & Tucked Sun Visors (visible in frame_010 & frame_020!)
    m.add_box(49.5, -4.2, 79.4, 52.8, 4.2, 81.4, region="trim")
    m.add_cylinder((51.5, 0.0, 79.5), (53.2, 0.0, 76.4), 0.38, segs=6, region="trim")
    m.add_box(52.6, -5.2, 75.0, 53.9, 5.2, 77.3, region="trim", face_regions={"-x": "chrome"})
    for vy_s in (19.0, -19.0):
        m.add_box(46.0, vy_s - 8.5, 81.0, 50.2, vy_s + 8.5, 81.8, region="trim")

    return m.export_dict()


# --------------------------------------------------------------------------- 7. Wreck Hulk & Shrapnel Chunks
def _build_wreck_and_shrapnel(chassis_dict):
    rng = random.Random(2026)
    wm = MeshBuilder("wreck_chassis")
    # Build scorched crumpled van shell for Quake post-explosion state
    wm.add_box(-102.0, -40.0, 8.5, 96.0, 40.0, 44.0, region="wreck")
    wm.add_box(-98.0, -35.0, 44.0, 32.0, 35.0, 72.0, region="wreck")
    wm.add_box(52.0, -28.0, 18.0, 92.0, 28.0, 36.0, region="ember")
    wreck_dict = wm.export_dict()

    shraps = {}
    for si in range(10):
        sm = MeshBuilder(f"shrap_{si}")
        sx = rng.uniform(5.0, 11.0)
        sy = rng.uniform(4.0, 9.5)
        sz = rng.uniform(0.8, 2.2)
        ox = rng.uniform(-75.0, 75.0)
        oy = rng.uniform(-32.0, 32.0)
        oz = rng.uniform(22.0, 74.0)
        reg = "ember" if si % 3 == 0 else "wreck"
        sm.add_box(ox - sx, oy - sy, oz - sz, ox + sx, oy + sy, oz + sz, region=reg)
        shraps[f"shrap_{si}"] = sm.export_dict()

    return wreck_dict, shraps


# --------------------------------------------------------------------------- Master Van Builder Entry Point
def build_promaster_van_data(barn_open_deg=126.0):
    """Returns full Quake/GLB/Viewer vehicle dictionary for 'van', including:
       - standard 24 'parts' required by build_vehicles_assets.py & veh_physics_sim.py
       - 'glass_cab' translucent RGBA part
       - 'viewer_rig' closed-pose barn doors & hinge axes for smooth 0..180 deg HTML slider control!"""
    parts = {}
    parts["chassis"] = _build_chassis_and_interior()
    parts["hood"] = _build_hood()
    parts["door_l"] = _build_cab_door(is_left=True)
    parts["door_r"] = _build_cab_door(is_left=False)
    parts["bumper_f"] = _build_front_bumper_and_fascia()
    parts["bumper_r"] = _build_rear_step_bumper()
    parts["detail_vib"] = _build_detail_vib()
    parts["glass_cab"] = _build_glass_and_mesh()

    # Build sculpted 50/50 split rear barn doors (closed mesh + rotated 152 deg studio open pose!)
    bd_l_mesh, hinge_l = _build_single_barn_door(is_left=True)
    bd_r_mesh, hinge_r = _build_single_barn_door(is_left=False)

    extra_m = MeshBuilder("extra_part")
    rad_open = math.radians(barn_open_deg)
    extra_m.merge_from(bd_l_mesh, rot_z=-rad_open, pivot_xy=(hinge_l[0], hinge_l[1]))
    extra_m.merge_from(bd_r_mesh, rot_z=+rad_open, pivot_xy=(hinge_r[0], hinge_r[1]))
    parts["extra_part"] = extra_m.export_dict()

    # 4 Commercial 16" Steelie Wheels
    wf_x, wr_x = VAN_SPEC["wheel_x_f"], VAN_SPEC["wheel_x_r"]
    wy, wr = VAN_SPEC["wheel_y"], VAN_SPEC["wheel_r"]
    parts["wheel_fl"] = _build_commercial_wheel("wheel_fl", wf_x, +wy, wr, True)
    parts["wheel_fr"] = _build_commercial_wheel("wheel_fr", wf_x, -wy, wr, False)
    parts["wheel_rl"] = _build_commercial_wheel("wheel_rl", wr_x, +wy, wr, True)
    parts["wheel_rr"] = _build_commercial_wheel("wheel_rr", wr_x, -wy, wr, False)

    wreck_dict, shraps = _build_wreck_and_shrapnel(parts["chassis"])
    parts["wreck_chassis"] = wreck_dict
    parts.update(shraps)

    return {
        "kind": "van",
        "spec": VAN_SPEC,
        "parts": parts,
        "viewer_rig": {
            "default_barn_deg": barn_open_deg,
            "barn_door_l_closed": bd_l_mesh.export_dict(custom_origin=hinge_l, hinge_pivot=hinge_l),
            "barn_door_r_closed": bd_r_mesh.export_dict(custom_origin=hinge_r, hinge_pivot=hinge_r),
        },
    }


if __name__ == "__main__":
    data = build_promaster_van_data()
    tot_v = sum(len(p["verts"]) for p in data["parts"].values())
    tot_t = sum(len(p["tris"]) for p in data["parts"].values())
    print(f"Built ProMaster L2H2 Van: {len(data['parts'])} parts, {tot_v} verts, {tot_t} tris")
    for k, p in data["parts"].items():
        if not k.startswith("shrap_"):
            print(f"  {k:15s}: {len(p['verts']):4d} verts, {len(p['tris']):4d} tris, origin={p['origin']}")
