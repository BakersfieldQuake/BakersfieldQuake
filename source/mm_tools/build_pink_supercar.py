r"""Builds the Complete 3D Pink Exotic Supercar ("It's not pink") + Roof Webcam Suite:

Features:
  1. Sleek Mid-Engine Exotic Pink Supercar (z=0 ground contact, 194u length, 86u widebody haunches):
       - Broad sculpted front hood painted with the uploaded portrait + "Say no to drugs."
       - Articulated Lamborghini-style upward-swinging scissor doors with bold "It's not pink"
         street-racing livery reading left-to-right on BOTH Left (+Y) and Right (-Y) sides!
       - Heroic 3D Roof-Mounted PC Streamer Webcam: hinged desktop monitor-clip claw, chrome
         pan/tilt ball-joint neck, multi-coated optical glass lens barrel, stereo mic grilles,
         glowing green LIVE status LED, and gaffer-taped black USB cable + ferrite bead!
       - Full 3D Cockpit (quilted pink/black racing bucket seats, digital dash showing live
         roof-webcam status, flat-bottom racing wheel) & visible mid-mounted 6.5L V12 engine!
       - Carbon-fiber front splitter + dive canards, side-skirt blades, swan-neck GT rear wing,
         5-fin Venturi diffuser, quad titanium exhausts, "NOT PINK" license plate, and staggered
         concave 10-spoke forged wheels.

Outputs:
  - pink_supercar.glb                       (Standard glTF 2.0 PBR + Emissive + Glass + 4 Animations)
  - progs/pink_supercar.md3                 (64-frame Quake/DarkPlaces MD3 across 4 seamless clips)
  - progs/pink_supercar.md3_0.skin          (DarkPlaces skin mapping)
  - progs/pink_supercar_frames.txt          (Frame table documentation)
  - progs/pink_supercar_tex.png (+ _glow, _glass)
  - scripts/pink_supercar.shader            (Diffuse + additive LED/webcam glow + alpha glass)
  - source/mm_tools/out/pink_supercar/pink_supercar_parts.npz (Mesh & rig cache for WebGL2 viewer)
"""
import io
import json
import math
import os
import struct
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_DIR = os.path.join(MOD_DIR, "progs")
SCRIPTS_DIR = os.path.join(MOD_DIR, "scripts")
OUT_DIR = os.path.join(HERE, "out", "pink_supercar")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib
import pink_supercar_tex as ptex
from pink_supercar_tex import (
    CAR_SPEC,
    R_CARBON,
    R_CHROME,
    R_DASH,
    R_DUCT_TAPE,
    R_ENGINE,
    R_PINK_MET,
    R_SEAT,
    R_TREAD,
    R_TRIM_BLK,
    R_WEBCAM_F,
    R_WEBCAM_LENS,
    R_WHEEL,
    clamp01,
    front_uv,
    hood_uv,
    rear_uv,
    side_uv,
    top_uv,
    uv_in_rect,
)

GLTF_SCALE = 0.025  # 1 Quake unit = 0.025 m (194u -> 4.85m exotic supercar)

SWATCH_RECTS = {
    "carbon":    R_CARBON,
    "pink":      R_PINK_MET,
    "chrome":    R_CHROME,
    "trim":      R_TRIM_BLK,
    "tape":      R_DUCT_TAPE,
    "seat":      R_SEAT,
    "dash":      R_DASH,
    "engine":    R_ENGINE,
    "tread":     R_TREAD,
}

ANIM_CLIPS = [
    ("idle_scan",       0,  16, 10.0, "V12 Purr & Roof Webcam Pan/Tilt Surveillance"),
    ("cruise_drive",    16, 16, 16.0, "High-Speed Cruise, Spinning Forged Wheels & Road Scan"),
    ("scissor_showoff", 32, 16, 10.0, "Lamborghini Scissor Doors Swing Open + Hood Pop"),
    ("turbo_boost",     48, 16, 18.0, "Full-Throttle Squat, Wheel Spin & Webcam Whiplash"),
]
TOTAL_MD3_FRAMES = 64


# --------------------------------------------------------------------------- 3D Vector & Quaternion Math
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


def quat_from_axis_angle(axis, deg):
    r = math.radians(deg) * 0.5
    s = math.sin(r)
    ax = v_norm(axis)
    return np.array([ax[0] * s, ax[1] * s, ax[2] * s, math.cos(r)], dtype=np.float64)


def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ], dtype=np.float64)


def quat_euler_zyx(yaw_z=0.0, pitch_y=0.0, roll_x=0.0):
    qz = quat_from_axis_angle((0.0, 0.0, 1.0), yaw_z)
    qy = quat_from_axis_angle((0.0, 1.0, 0.0), pitch_y)
    qx = quat_from_axis_angle((1.0, 0.0, 0.0), roll_x)
    return quat_mul(qz, quat_mul(qy, qx))


def quat_to_mat3(q):
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz),       2.0 * (xz + wy)],
        [2.0 * (xy + wz),       1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy),       2.0 * (yz + wx),       1.0 - 2.0 * (xx + yy)],
    ], dtype=np.float64)


# --------------------------------------------------------------------------- Crease-Smoothed Mesh Builder
class MeshBuilder:
    """Accumulates triangles in WORLD Quake coordinates, then bakes crease-smoothed
    vertex normals and shifts vertices relative to a local articulation pivot."""
    def __init__(self, name, origin=(0.0, 0.0, 0.0)):
        self.name = name
        self.origin = tuple(float(c) for c in origin)
        self.tris_raw = []  # (p0, p1, p2, uv0, uv1, uv2, smooth_grp)

    def _project_uvs(self, pts, fn, region):
        if region in SWATCH_RECTS:
            rect = SWATCH_RECTS[region]
            up_r = (0.0, 0.0, 1.0) if abs(fn[2]) < 0.88 else (1.0, 0.0, 0.0)
            t1 = v_norm(v_cross(up_r, fn))
            t2 = v_norm(v_cross(fn, t1))
            us = [v_dot(p, t1) for p in pts]
            vs = [v_dot(p, t2) for p in pts]
            umin, umax = min(us), max(us)
            vmin, vmax = min(vs), max(vs)
            du = max(5.0, umax - umin)
            dv = max(5.0, vmax - vmin)
            return [uv_in_rect(rect, (u - umin) / du, 1.0 - (v - vmin) / dv, pad=5.0) for u, v in zip(us, vs)]

        if region == "hood":
            return [hood_uv(p[0], p[1]) for p in pts]
        if region == "side_l":
            return [side_uv(p[0], p[2], True) for p in pts]
        if region == "side_r":
            return [side_uv(p[0], p[2], False) for p in pts]
        if region == "front":
            return [front_uv(p[1], p[2]) for p in pts]
        if region == "rear":
            return [rear_uv(p[1], p[2]) for p in pts]
        if region == "top":
            return [top_uv(p[0], p[1]) for p in pts]
        if region == "glass":
            up_r = (0.0, 0.0, 1.0) if abs(fn[2]) < 0.88 else (1.0, 0.0, 0.0)
            t1 = v_norm(v_cross(up_r, fn))
            t2 = v_norm(v_cross(fn, t1))
            us = [v_dot(p, t1) for p in pts]
            vs = [v_dot(p, t2) for p in pts]
            du = max(4.0, max(us) - min(us))
            dv = max(4.0, max(vs) - min(vs))
            return [(round(0.08 + 0.84 * ((u - min(us)) / du), 5),
                     round(0.08 + 0.84 * (1.0 - (v - min(vs)) / dv), 5)) for u, v in zip(us, vs)]

        # Auto fallback by face normal
        ax, ay, az = abs(fn[0]), abs(fn[1]), abs(fn[2])
        if fn[0] > 0.62 and ax >= ay and ax >= az:
            return [front_uv(p[1], p[2]) for p in pts]
        if fn[0] < -0.62 and ax >= ay and ax >= az:
            return [rear_uv(p[1], p[2]) for p in pts]
        if fn[2] > 0.56 and az >= ay:
            c_x = sum(p[0] for p in pts) / len(pts)
            c_y = sum(abs(p[1]) for p in pts) / len(pts)
            if c_x > CAR_SPEC["x_hood_rear"] and c_y <= CAR_SPEC["y_hood_max"] + 1.0:
                return [hood_uv(p[0], p[1]) for p in pts]
            return [top_uv(p[0], p[1]) for p in pts]
        if fn[2] < -0.65:
            return [uv_in_rect(R_TRIM_BLK, (p[0] + 98.0) / 196.0, (p[1] + 43.0) / 86.0) for p in pts]
        return [side_uv(p[0], p[2], fn[1] >= 0.0) for p in pts]

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
            self.tris_raw.append((p0, p2, p1, uv_tri[0], uv_tri[2], uv_tri[1], smooth + 500 if smooth else 0))

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

    def add_cylinder(self, p_a, p_b, r0, r1=None, segs=16, region="chrome", cap_a=True, cap_b=True, smooth=2):
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
            if v_len(mid_dir) < 1e-5:
                mid_dir = v_sub(v_mul(v_add(ring1[i], ring1[j]), 0.5), p_b)
            self.add_quad(ring0[i], ring0[j], ring1[j], ring1[i], region=region, expect_n=mid_dir, smooth=smooth)
        if cap_a and r0 > 1e-4:
            for i in range(segs):
                j = (i + 1) % segs
                self.add_tri(p_a, ring0[j], ring0[i], region=region, expect_n=v_mul(d, -1.0), smooth=0)
        if cap_b and r1 > 1e-4:
            for i in range(segs):
                j = (i + 1) % segs
                self.add_tri(p_b, ring1[i], ring1[j], region=region, expect_n=d, smooth=0)

    def add_tube_path(self, pts, radius, segs=10, region="trim", smooth=4):
        """Sweeps a smooth circular tube along a 3D polyline (for USB cord, roll bars, struts)."""
        if len(pts) < 2:
            return
        rings = []
        prev_u = None
        for idx, p in enumerate(pts):
            if idx == 0:
                t_dir = v_norm(v_sub(pts[1], pts[0]))
            elif idx == len(pts) - 1:
                t_dir = v_norm(v_sub(pts[-1], pts[-2]))
            else:
                t_dir = v_norm(v_sub(pts[idx + 1], pts[idx - 1]))
            if prev_u is None:
                up = (0.0, 0.0, 1.0) if abs(t_dir[2]) < 0.88 else (1.0, 0.0, 0.0)
                u = v_norm(v_cross(t_dir, up))
            else:
                # Parallel-transport frame to avoid twist!
                u_proj = v_sub(prev_u, v_mul(t_dir, v_dot(prev_u, t_dir)))
                u = v_norm(u_proj) if v_len(u_proj) > 1e-4 else v_norm(v_cross(t_dir, (1.0, 0.0, 0.0)))
            prev_u = u
            w = v_norm(v_cross(t_dir, u))
            ring = []
            for s in range(segs):
                a = 2.0 * math.pi * s / segs
                rd = v_add(v_mul(u, math.cos(a)), v_mul(w, math.sin(a)))
                ring.append(v_add(p, v_mul(rd, radius)))
            rings.append((p, ring))
        for k in range(len(rings) - 1):
            p0, r0 = rings[k]
            _, r1 = rings[k + 1]
            for s in range(segs):
                sn = (s + 1) % segs
                n_out = v_sub(v_mul(v_add(r0[s], r0[sn]), 0.5), p0)
                self.add_quad(r0[s], r0[sn], r1[sn], r1[s], region=region, expect_n=n_out, smooth=smooth)

    def finalize(self, crease_deg=44.0):
        """Welds coincident (pos, uv, normal-crease) vertices and computes smooth normals,
        converting vertices to local space relative to self.origin."""
        cos_thresh = math.cos(math.radians(crease_deg))
        pos_groups = {}
        face_normals = []

        for ti, (p0, p1, p2, uv0, uv1, uv2, sgrp) in enumerate(self.tris_raw):
            fn = v_norm(v_cross(v_sub(p1, p0), v_sub(p2, p0)))
            face_normals.append(fn)
            if sgrp != 0:
                for p in (p0, p1, p2):
                    key = (round(p[0], 3), round(p[1], 3), round(p[2], 3), sgrp)
                    pos_groups.setdefault(key, []).append(ti)

        ox, oy, oz = self.origin
        vert_map = {}
        verts, norms, uvs, tris = [], [], [], []

        for ti, (p0, p1, p2, uv0, uv1, uv2, sgrp) in enumerate(self.tris_raw):
            fn = face_normals[ti]
            tri_idx = []
            for p, uv in ((p0, uv0), (p1, uv1), (p2, uv2)):
                if sgrp == 0:
                    vn = fn
                else:
                    key = (round(p[0], 3), round(p[1], 3), round(p[2], 3), sgrp)
                    nx, ny, nz = 0.0, 0.0, 0.0
                    for other_ti in pos_groups[key]:
                        ofn = face_normals[other_ti]
                        if v_dot(fn, ofn) >= cos_thresh:
                            nx += ofn[0]
                            ny += ofn[1]
                            nz += ofn[2]
                    vn = v_norm((nx, ny, nz))

                v_key = (
                    round(p[0], 3), round(p[1], 3), round(p[2], 3),
                    round(vn[0], 3), round(vn[1], 3), round(vn[2], 3),
                    round(uv[0], 4), round(uv[1], 4),
                )
                vi = vert_map.get(v_key)
                if vi is None:
                    vi = len(verts)
                    vert_map[v_key] = vi
                    verts.append((round(p[0] - ox, 4), round(p[1] - oy, 4), round(p[2] - oz, 4)))
                    norms.append((round(vn[0], 4), round(vn[1], 4), round(vn[2], 4)))
                    uvs.append((round(uv[0], 5), round(uv[1], 5)))
                tri_idx.append(vi)
            tris.append(tuple(tri_idx))

        return dict(
            name=self.name,
            origin=list(self.origin),
            verts=np.asarray(verts, dtype=np.float32),
            norms=np.asarray(norms, dtype=np.float32),
            uvs=np.asarray(uvs, dtype=np.float32),
            tris=np.asarray(tris, dtype=np.int32),
        )


# --------------------------------------------------------------------------- Supercar Parametric Surface Curves
def nose_planform_dx(y):
    """Aggressive Lamborghini-style V-wedge nose planform setback across Y."""
    ty = min(1.0, abs(y) / 41.4)
    return -7.2 * (ty ** 1.75)


def hood_surface_z(x, y):
    """Smoothly raked front hood surface (x=26.5..92.0, |y|<=27.5):
    z = 29.2 at windshield cowl (x=26.5) sweeping cleanly down to z = 14.8 at nose (x=92.0),
    with a subtle 1.1u center aerodynamic crown so light rolls across the hood mural!"""
    tx = clamp01((x - 26.5) / (92.0 - 26.5))
    z_center = 29.2 - 14.4 * (tx ** 1.08)
    ty = min(1.0, abs(y) / 27.5)
    # Subtle outer crease dip near |y|~25 before rising into outer front fenders!
    crown = 0.95 * (1.0 - ty * ty) - 0.35 * math.exp(-((ty - 0.88) ** 2) / 0.015)
    return z_center + crown * (1.0 - 0.35 * tx)


def half_width_at_x(x):
    """Widebody exotic supercar planform waist & flared front/rear haunches!"""
    if x >= 41.5:
        # Front wheel flare peaking around x=57 (hw=41.4), tapering slightly to nose (hw=39.2)
        if x <= 68.0:
            t = (x - 41.5) / 26.5
            return 39.2 + 2.2 * math.sin(math.pi * min(1.0, t * 0.88))
        t = clamp01((x - 68.0) / 26.0)
        return 41.1 - 2.3 * (t ** 1.3)
    if x >= -21.0:
        # Sleek pinched supercar scissor-door waist!
        return 39.2
    if x >= -76.0:
        # Aggressive widebody rear haunch flare over mid-engine intakes & rear wheels (hw=43.0!)
        t = clamp01((-21.0 - x) / 22.0)
        flare_in = 39.2 + 3.8 * (0.5 - 0.5 * math.cos(math.pi * t))
        if x < -62.0:
            tr = clamp01((-62.0 - x) / 32.0)
            return 43.0 - 2.2 * (tr ** 1.4)
        return flare_in
    tr = clamp01((-62.0 - x) / 32.0)
    return 43.0 - 2.6 * (tr ** 1.4)


def beltline_z_at_x(x):
    """Outer fender peak / door sill / rear haunch crest height along X."""
    if x >= 41.5:
        # Peaked exotic front fender arch over front wheel!
        arch_bump = 3.1 * math.exp(-(((x - 57.0) / 21.0) ** 2))
        tx = clamp01((x - 41.5) / (92.0 - 41.5))
        base = 29.4 - 14.2 * (tx ** 1.15)
        return base + arch_bump * (1.0 - 0.55 * tx)
    if x >= -21.0:
        # Sleek rising scissor-door beltline
        t = (41.5 - x) / 62.5
        return 29.4 + 1.8 * t
    if x >= -68.0:
        # Muscular rear widebody haunch over rear wheel!
        arch_bump = 3.2 * math.exp(-(((x + 52.0) / 22.0) ** 2))
        return 31.4 + 2.2 * clamp01((-21.0 - x) / 24.0) + arch_bump
    t = clamp01((-68.0 - x) / 26.0)
    return 35.0 - 1.2 * t


def wheel_arch_bottom_z(x):
    """Lower body sill height, curving cleanly UP over front (x=57) & rear (x=-55) wheels!"""
    z_sill = 7.4
    df = abs(x - CAR_SPEC["wheel_x_f"])
    if df < CAR_SPEC["arch_r_f"]:
        zf = CAR_SPEC["wheel_r_f"] + math.sqrt(max(0.0, CAR_SPEC["arch_r_f"] ** 2 - df * df)) - 1.2
        return max(z_sill, zf)
    dr = abs(x - CAR_SPEC["wheel_x_r"])
    if dr < CAR_SPEC["arch_r_r"]:
        zr = CAR_SPEC["wheel_r_r"] + math.sqrt(max(0.0, CAR_SPEC["arch_r_r"] ** 2 - dr * dr)) - 1.2
        return max(z_sill, zr)
    return z_sill


# --------------------------------------------------------------------------- 1. Articulated Front Hood ("Say no to drugs.")
def build_hood_part():
    """Smooth 16x14 curved 3D hood mesh mapped 100% cleanly via hood_uv(x, y)."""
    mb = MeshBuilder("hood", origin=(27.0, 0.0, 29.0))
    nx, ny = 16, 14
    xs = [26.8 + (91.8 - 26.8) * (i / float(nx)) for i in range(nx + 1)]
    ys = [-27.4 + 54.8 * (j / float(ny)) for j in range(ny + 1)]

    grid = []
    for i, x in enumerate(xs):
        row = []
        tx = i / float(nx)
        for y in ys:
            # Slight nose V-curve at very front tip (tx > 0.80) while keeping UV world-projected
            dx = nose_planform_dx(y) * 0.36 * (max(0.0, (tx - 0.65) / 0.35) ** 1.6)
            xw = x + dx
            zw = hood_surface_z(xw, y)
            row.append((xw, y, zw))
        grid.append(row)

    for i in range(nx):
        for j in range(ny):
            p00 = grid[i][j]
            p10 = grid[i + 1][j]
            p11 = grid[i + 1][j + 1]
            p01 = grid[i][j + 1]
            uvs = [hood_uv(p[0], p[1]) for p in (p00, p10, p11, p01)]
            mb.add_quad(p00, p10, p11, p01, region="hood", uvs=uvs, expect_n=(0.2, 0.0, 1.0), smooth=1)
            # Underside carbon reinforcement skin (1.1u below top skin so open hood has real thickness!)
            u00 = (p00[0], p00[1], p00[2] - 0.9)
            u10 = (p10[0], p10[1], p10[2] - 0.9)
            u11 = (p11[0], p11[1], p11[2] - 0.9)
            u01 = (p01[0], p01[1], p01[2] - 0.9)
            mb.add_quad(u00, u01, u11, u10, region="carbon", expect_n=(-0.2, 0.0, -1.0), smooth=2)

    # Perimeter thickness lip around hood edges
    for i in range(nx):
        for col, ny_sign in ((0, -1.0), (ny, 1.0)):
            pa, pb = grid[i][col], grid[i + 1][col]
            ua, ub = (pa[0], pa[1], pa[2] - 0.9), (pb[0], pb[1], pb[2] - 0.9)
            mb.add_quad(pa, pb, ub, ua, region="pink", expect_n=(0.0, ny_sign, 0.0), smooth=0)
    for j in range(ny):
        pa, pb = grid[nx][j], grid[nx][j + 1]
        ua, ub = (pa[0], pa[1], pa[2] - 0.9), (pb[0], pb[1], pb[2] - 0.9)
        mb.add_quad(pa, pb, ub, ua, region="pink", expect_n=(1.0, 0.0, 0.0), smooth=0)

    return mb.finalize()


# --------------------------------------------------------------------------- 2. Articulated Scissor Doors ("It's not pink")
def build_scissor_door_part(is_left):
    sgn = 1.0 if is_left else -1.0
    name = "door_l" if is_left else "door_r"
    reg = "side_l" if is_left else "side_r"
    pivot = (40.5, sgn * 38.8, 28.5)
    mb = MeshBuilder(name, origin=pivot)
    mg = MeshBuilder(f"{name}_glass", origin=pivot)

    nx, nz = 10, 6
    x0, x1 = CAR_SPEC["x_door_rear"], CAR_SPEC["x_door_front"]  # -21.0 .. +41.5
    xs = [x0 + (x1 - x0) * (i / float(nx)) for i in range(nx + 1)]

    outer_grid = []
    inner_grid = []
    for x in xs:
        z_bot = 7.9
        z_top = beltline_z_at_x(x)
        hw = half_width_at_x(x)
        col_o, col_i = [], []
        for k in range(nz + 1):
            tz = k / float(nz)
            z = z_bot + (z_top - z_bot) * tz
            # Sculpted supercar tumblehome & mid-door character curve (bulging +1.1u at mid-height!)
            bulge = 1.15 * math.sin(math.pi * tz) - 1.35 * (tz ** 2.4)
            y_out = sgn * (hw + bulge)
            y_in = sgn * (hw - 2.4)
            col_o.append((x, y_out, z))
            col_i.append((x, y_in, z))
        outer_grid.append(col_o)
        inner_grid.append(col_i)

    for i in range(nx):
        for k in range(nz):
            p00, p10 = outer_grid[i][k], outer_grid[i + 1][k]
            p11, p01 = outer_grid[i + 1][k + 1], outer_grid[i][k + 1]
            uvs = [side_uv(p[0], p[2], is_left) for p in (p00, p10, p11, p01)]
            mb.add_quad(p00, p10, p11, p01, region=reg, uvs=uvs, expect_n=(0.0, sgn, 0.08), smooth=1)

            q00, q10 = inner_grid[i][k], inner_grid[i + 1][k]
            q11, q01 = inner_grid[i + 1][k + 1], inner_grid[i][k + 1]
            in_reg = "seat" if (1 <= k <= 4 and 1 <= i <= nx - 2) else "carbon"
            mb.add_quad(q00, q01, q11, q10, region=in_reg, expect_n=(0.0, -sgn, 0.0), smooth=2)

    # Cap top windowsill, bottom sill, front & rear door jamb thickness!
    for i in range(nx):
        mb.add_quad(outer_grid[i][nz], outer_grid[i + 1][nz], inner_grid[i + 1][nz], inner_grid[i][nz],
                    region="pink", expect_n=(0.0, 0.0, 1.0), smooth=0)
        mb.add_quad(outer_grid[i][0], inner_grid[i][0], inner_grid[i + 1][0], outer_grid[i + 1][0],
                    region="carbon", expect_n=(0.0, 0.0, -1.0), smooth=0)
    for k in range(nz):
        mb.add_quad(outer_grid[0][k], inner_grid[0][k], inner_grid[0][k + 1], outer_grid[0][k + 1],
                    region="pink", expect_n=(-1.0, 0.0, 0.0), smooth=0)
        mb.add_quad(outer_grid[nx][k], outer_grid[nx][k + 1], inner_grid[nx][k + 1], inner_grid[nx][k],
                    region="pink", expect_n=(1.0, 0.0, 0.0), smooth=0)

    # Sculpted 3D Exotic Aero Wing Mirror on twin swept stalks!
    mx_base, my_base, mz_base = 28.0, sgn * 38.6, 29.8
    mx_head, my_head, mz_head = 25.0, sgn * 45.2, 33.4
    mb.add_cylinder((mx_base, my_base, mz_base), (mx_head + 1.2, my_head - sgn * 1.2, mz_head - 0.4),
                    0.75, 0.55, segs=8, region="carbon", cap_a=False, cap_b=False)
    # Aerodynamic teardrop mirror housing (candy pink cap + dark mirror face looking -X)
    mb.add_box(mx_head - 2.6, my_head - sgn * 2.4, mz_head - 1.6,
               mx_head + 2.8, my_head + sgn * 2.2, mz_head + 1.7,
               region="pink", face_regions={"-x": "chrome", "-z": "carbon"}, smooth=3)

    # Frameless Tinted Side Window Pane attached to the scissor door!
    w_bot_r = outer_grid[0][nz]
    w_bot_f = outer_grid[nx - 2][nz]
    w_top_r = (-19.5, sgn * 25.0, 44.6)
    w_top_m = (-1.5, sgn * 25.4, 44.8)
    mg.add_quad(w_bot_r, w_bot_f, w_top_m, w_top_r, region="glass", expect_n=(0.0, sgn, 0.45), smooth=1, double_sided=True)

    return mb.finalize(), mg.finalize()


# --------------------------------------------------------------------------- 3. Roof-Mounted 3D PC Streamer Webcam!
def build_webcam_parts():
    """Builds the unmistakable Roof-Mounted PC Webcam in two parts:
      - webcam_base : Bolted roof pad + hinged desktop monitor-clip claw + ball-joint neck
                      + 3D coiled black USB 2.0 cable + ferrite choke bead + gaffer tape strips!
      - webcam_head : Articulated pan/tilt wide rounded-pill streamer webcam housing +
                      protruding 3D multi-ring optical lens barrel + sapphire glass dome +
                      glowing green LIVE jewel LED + top snapshot button!"""
    cx, cy, cz = CAR_SPEC["cam_x"], CAR_SPEC["cam_y"], CAR_SPEC["cam_z_base"]  # (-2.0, 0.0, 46.0)
    piv_z = CAR_SPEC["cam_pivot_z"]  # 53.0

    b_base = MeshBuilder("webcam_base", origin=(0.0, 0.0, 0.0))

    # 1. Roof mounting riser bar (what the PC monitor-clip claw is clamped onto!)
    b_base.add_box(cx - 5.2, cy - 6.8, cz - 0.6, cx + 4.6, cy + 6.8, cz + 1.6, region="trim", smooth=0)
    # 4 chrome mounting bolts at corners of roof riser
    for bx in (cx - 4.2, cx + 3.6):
        for by in (-5.6, 5.6):
            b_base.add_cylinder((bx, by, cz + 1.5), (bx, by, cz + 2.1), 0.55, 0.55, segs=8, region="chrome")

    # 2. Iconic Hinged Desktop PC Monitor-Clip Claw gripping the roof riser!
    #    Front chin hook wrapping down over the front lip (+X) of the riser
    b_base.add_box(cx + 3.8, -4.6, cz + 0.2, cx + 5.3, 4.6, cz + 3.6, region="trim", smooth=0)
    #    Inclined main monitor-clip jaw arm sweeping up to hinge
    jaw_pts_l = [(cx + 4.8, 4.6, cz + 2.2), (cx - 4.8, 4.6, cz + 4.8), (cx - 4.4, 4.6, cz + 6.4), (cx + 5.1, 4.6, cz + 3.6)]
    jaw_pts_r = [(p[0], -4.6, p[2]) for p in jaw_pts_l]
    b_base.add_quad(jaw_pts_l[0], jaw_pts_l[1], jaw_pts_l[2], jaw_pts_l[3], region="trim", expect_n=(0, 1, 0), smooth=0)
    b_base.add_quad(jaw_pts_r[0], jaw_pts_r[3], jaw_pts_r[2], jaw_pts_r[1], region="trim", expect_n=(0, -1, 0), smooth=0)
    b_base.add_quad(jaw_pts_r[3], jaw_pts_l[3], jaw_pts_l[2], jaw_pts_r[2], region="carbon", expect_n=(0.2, 0, 1), smooth=0)
    b_base.add_quad(jaw_pts_r[0], jaw_pts_r[1], jaw_pts_l[1], jaw_pts_l[0], region="trim", expect_n=(-0.2, 0, -1), smooth=0)

    #    Rear hinged counterweight foot bracing back onto the roof!
    foot_l = [(cx - 4.4, 4.2, cz + 5.4), (cx - 10.2, 4.2, cz + 0.1), (cx - 8.4, 4.2, cz + 0.1), (cx - 3.2, 4.2, cz + 4.4)]
    foot_r = [(p[0], -4.2, p[2]) for p in foot_l]
    b_base.add_quad(foot_l[0], foot_l[1], foot_l[2], foot_l[3], region="trim", expect_n=(0, 1, 0), smooth=0)
    b_base.add_quad(foot_r[0], foot_r[3], foot_r[2], foot_r[1], region="trim", expect_n=(0, -1, 0), smooth=0)
    b_base.add_quad(foot_r[0], foot_r[1], foot_l[1], foot_l[0], region="carbon", expect_n=(-0.6, 0, 0.7), smooth=0)
    #    Side chrome hinge pins at rear knuckle
    b_base.add_cylinder((cx - 4.2, -5.0, cz + 5.2), (cx - 4.2, 5.0, cz + 5.2), 1.05, 1.05, segs=12, region="chrome")

    # 3. Chrome Ball-Joint Gimbal Stem rising to pivot (cx, 0, piv_z)
    b_base.add_cylinder((cx, 0.0, cz + 4.4), (cx, 0.0, piv_z - 0.8), 1.55, 1.25, segs=14, region="chrome")
    b_base.add_cylinder((cx, 0.0, piv_z - 1.2), (cx, 0.0, piv_z + 1.0), 2.1, 1.6, segs=14, region="chrome")

    # 4. 3D Black USB 2.0 Cable + Ferrite Bead + Silver Gaffer Tape Strips across the Pink Roof!
    usb_pts = [
        (cx - 5.2,  0.0, cz + 6.8),
        (cx - 8.2,  0.8, cz + 5.2),
        (cx - 10.6, 2.2, cz + 2.0),
        (cx - 12.8, 3.2, cz + 0.45),
        (cx - 15.8, 2.4, cz + 0.25),
        (cx - 18.8, -0.8, cz - 0.15),
        (cx - 21.5, -2.0, cz - 1.20),
        (cx - 23.8, -2.2, cz - 4.20),
    ]
    b_base.add_tube_path(usb_pts, radius=0.68, segs=10, region="trim", smooth=4)
    # Chunky cylindrical EMI Ferrite Choke Bead inline on the USB cord!
    b_base.add_cylinder((cx - 11.4, 2.55, cz + 1.45), (cx - 13.6, 3.15, cz + 0.48), 1.42, 1.42, segs=12, region="trim")
    # Two strips of silver gaffer tape taping the USB cord flat onto the candy-pink roof!
    b_base.add_box(cx - 16.8, -1.2, cz - 0.1, cx - 14.4, 5.8, cz + 0.95, region="tape", smooth=1)
    b_base.add_box(cx - 20.2, -5.0, cz - 0.4, cx - 17.8, 2.2, cz + 0.65, region="tape", smooth=1)

    # -----------------------------------------------------------------------
    # Articulated Pan/Tilt Webcam Head (`webcam_head`, pivot at (cx, 0, piv_z))
    b_head = MeshBuilder("webcam_head", origin=(cx, cy, piv_z))

    # Pill-shaped widescreen streamer webcam housing:
    # Spans y = -11.4 .. +11.4 (22.8u wide!), z = 53.0 .. 62.0 (9.0u tall!), x = cx - 4.4 .. cx + 4.4 (8.8u deep!)
    x_back = cx - 4.4
    x_front = cx + 4.4
    z_mid = piv_z + 4.5   # 57.5
    r_pill = 4.45         # half-height of rounded pill ends
    y_flat = 6.9          # half-span between left & right semicircle centers -> total width = 2*(6.9+4.45) = 22.7u!

    # Build smooth 24-segment rounded-pill perimeter in (Y, Z)
    pill_yz = []
    for k in range(13):
        ang = -0.5 * math.pi + math.pi * (k / 12.0)  # right/left endcap (+Y)
        pill_yz.append((y_flat + r_pill * math.cos(ang), z_mid + r_pill * math.sin(ang)))
    for k in range(13):
        ang = 0.5 * math.pi + math.pi * (k / 12.0)   # (-Y) endcap
        pill_yz.append((-y_flat + r_pill * math.cos(ang), z_mid + r_pill * math.sin(ang)))

    n_p = len(pill_yz)
    # Extrude housing with subtle front & rear bevels!
    rings_x = [
        (x_back,        0.86),
        (x_back + 1.1,  0.98),
        (x_front - 0.8, 1.00),
        (x_front,       0.95),
    ]
    ring_pts = []
    for x_pl, sc in rings_x:
        ring_pts.append([(x_pl, y * sc, z_mid + (z - z_mid) * sc) for (y, z) in pill_yz])

    for ri in range(len(ring_pts) - 1):
        ra, rb = ring_pts[ri], ring_pts[ri + 1]
        reg = "chrome" if ri == 2 else "carbon"
        for i in range(n_p):
            j = (i + 1) % n_p
            ym = 0.5 * (ra[i][1] + ra[j][1])
            zm = 0.5 * (ra[i][2] + ra[j][2]) - z_mid
            b_head.add_quad(ra[i], ra[j], rb[j], rb[i], region=reg, expect_n=(0.0, ym, zm), smooth=3)

    # Rear cap (x = x_back) + USB strain-relief boot
    c_back = (x_back, 0.0, z_mid)
    for i in range(n_p):
        j = (i + 1) % n_p
        b_head.add_tri(c_back, ring_pts[0][j], ring_pts[0][i], region="trim", expect_n=(-1.0, 0.0, 0.0), smooth=0)
    b_head.add_cylinder((x_back, 0.0, z_mid - 1.2), (x_back - 2.2, 0.0, z_mid - 1.8), 1.45, 0.85, segs=10, region="trim")

    # Front Faceplate mapped 1:1 to R_WEBCAM_F (stereo mic grilles, HD 1080p, LIVE LED)!
    c_front = (x_front, 0.0, z_mid)
    y_max_f = (y_flat + r_pill) * 0.95
    z_max_f = r_pill * 0.95

    def wf_uv(pt):
        # Viewer in front (+X looking -X): viewer-left = -Y (su=0), viewer-right = +Y (su=1)
        su = clamp01((pt[1] + y_max_f) / (2.0 * y_max_f))
        sv = clamp01(1.0 - (pt[2] - (z_mid - z_max_f)) / (2.0 * z_max_f))
        return uv_in_rect(R_WEBCAM_F, su, sv, pad=4.0)

    rf = ring_pts[-1]
    uv_cf = wf_uv(c_front)
    for i in range(n_p):
        j = (i + 1) % n_p
        b_head.add_tri(c_front, rf[i], rf[j], uvs=[uv_cf, wf_uv(rf[i]), wf_uv(rf[j])],
                       expect_n=(1.0, 0.0, 0.0), smooth=0)

    # Protruding 3D Multi-Stage Optical Camera Lens Barrel centered at (x_front, 0.0, z_mid)!
    # Stage 1: Outer knurled silver manual-focus ring (x_front -> x_front + 2.4, r = 4.55 -> 4.35)
    b_head.add_cylinder((x_front - 0.1, 0.0, z_mid), (x_front + 2.3, 0.0, z_mid),
                        4.55, 4.35, segs=24, region="chrome", cap_a=False, cap_b=False, smooth=5)
    # Stage 2: Stepped black inner baffle ring (x_front + 2.3 -> x_front + 3.4, r = 4.35 -> 3.65)
    b_head.add_cylinder((x_front + 2.3, 0.0, z_mid), (x_front + 3.3, 0.0, z_mid),
                        4.35, 3.65, segs=24, region="trim", cap_a=False, cap_b=False, smooth=0)
    # Stage 3: Recessed inner barrel wall down to convex coated optical glass dome!
    b_head.add_cylinder((x_front + 3.3, 0.0, z_mid), (x_front + 2.6, 0.0, z_mid),
                        3.65, 3.35, segs=24, region="trim", cap_a=False, cap_b=False, smooth=0)

    # Stage 4: 3D Convex Multi-Coated Optical Glass Lens Element (mapped 1:1 to R_WEBCAM_LENS!)
    r_lens = 3.45
    lens_segs = 24
    rings_dome = [
        (x_front + 2.55, 1.00),
        (x_front + 2.95, 0.72),
        (x_front + 3.22, 0.38),
    ]
    dome_pts = []
    for xd, rr in rings_dome:
        ring = []
        for s in range(lens_segs):
            a = 2.0 * math.pi * s / lens_segs
            ring.append((xd, r_lens * rr * math.cos(a), z_mid + r_lens * rr * math.sin(a)))
        dome_pts.append(ring)

    def lens_uv(pt):
        su = 0.5 + 0.48 * (pt[1] / r_lens)
        sv = 0.5 - 0.48 * ((pt[2] - z_mid) / r_lens)
        return uv_in_rect(R_WEBCAM_LENS, su, sv, pad=3.0)

    for dr in range(len(dome_pts) - 1):
        r0, r1 = dome_pts[dr], dome_pts[dr + 1]
        for s in range(lens_segs):
            sn = (s + 1) % lens_segs
            pts_q = [r0[s], r0[sn], r1[sn], r1[s]]
            b_head.add_quad(*pts_q, uvs=[lens_uv(p) for p in pts_q], expect_n=(1.0, 0.0, 0.0), smooth=6)
    apex = (x_front + 3.32, 0.0, z_mid)
    for s in range(lens_segs):
        sn = (s + 1) % lens_segs
        pts_t = [apex, dome_pts[-1][s], dome_pts[-1][sn]]
        b_head.add_tri(*pts_t, uvs=[lens_uv(p) for p in pts_t], expect_n=(1.0, 0.0, 0.0), smooth=6)

    # Top tactile "SNAPSHOT" button on top of webcam housing!
    b_head.add_cylinder((cx + 0.5, -5.2, z_mid + r_pill - 0.2), (cx + 0.5, -5.2, z_mid + r_pill + 0.85),
                        1.45, 1.30, segs=12, region="pink")

    return b_base.finalize(), b_head.finalize()


# --------------------------------------------------------------------------- 4. Staggered 10-Spoke Forged Supercar Wheels
def build_wheel_part(name, wx, wy, wr, ww, is_left, dish_depth=3.0):
    mb = MeshBuilder(name, origin=(wx, wy, wr))
    sgn = 1.0 if is_left else -1.0
    y_out = wy + sgn * (ww * 0.5)
    y_in = wy - sgn * (ww * 0.5)
    segs = 28

    def w_uv(y_unused, x_loc, z_loc):
        # Map circle onto R_WHEEL (su=0..1, sv=0..1)
        su = 0.5 + 0.485 * (x_loc / wr) * (-1.0 if is_left else 1.0)
        sv = 0.5 - 0.485 * (z_loc / wr)
        return uv_in_rect(R_WHEEL, su, sv, pad=2.0)

    # Sculpted chamfered performance tire tread + rounded shoulders!
    prof = [
        (y_in,                wr * 0.72),
        (y_in,                wr * 0.95),
        (y_in + sgn * 1.1,    wr * 1.00),
        (y_out - sgn * 1.1,   wr * 1.00),
        (y_out,               wr * 0.95),
        (y_out,               wr * 0.70),
        (y_out - sgn * dish_depth, wr * 0.24),
    ]
    rings = []
    for yp, rp in prof:
        ring = []
        for s in range(segs):
            a = 2.0 * math.pi * s / segs
            ring.append((wx + rp * math.cos(a), yp, wr + rp * math.sin(a)))
        rings.append((yp, rp, ring))

    for ri in range(len(rings) - 1):
        _, _, r0 = rings[ri]
        _, _, r1 = rings[ri + 1]
        is_tread = (ri in (1, 2, 3))
        for s in range(segs):
            sn = (s + 1) % segs
            p00, p10, p11, p01 = r0[s], r0[sn], r1[sn], r1[s]
            if is_tread:
                u0, u1 = (ri - 1) / 3.0, ri / 3.0
                v0, v1 = (s / float(segs)) * 2.0 % 1.0, ((s + 1) / float(segs)) * 2.0 % 1.0
                if v1 < v0:
                    v1 = 1.0
                uvs = [
                    uv_in_rect(R_TREAD, u0, v0, pad=3.0),
                    uv_in_rect(R_TREAD, u0, v1, pad=3.0),
                    uv_in_rect(R_TREAD, u1, v1, pad=3.0),
                    uv_in_rect(R_TREAD, u1, v0, pad=3.0),
                ]
                n_exp = (0.5 * (p00[0] + p10[0]) - wx, 0.0, 0.5 * (p00[2] + p10[2]) - wr)
                mb.add_quad(p00, p10, p11, p01, uvs=uvs, expect_n=n_exp, smooth=7)
            else:
                pts_q = [p00, p10, p11, p01]
                uvs = [w_uv(p[1], p[0] - wx, p[2] - wr) for p in pts_q]
                ny_e = -sgn if ri == 0 else sgn
                mb.add_quad(*pts_q, uvs=uvs, expect_n=(0.0, ny_e, 0.0), smooth=8)

    # Center-lock anodized pink hex nut cap at dish center + inner wheel cap
    c_hub = (wx, y_out - sgn * (dish_depth - 0.6), wr)
    uv_c = w_uv(c_hub[1], 0.0, 0.0)
    r_hub = rings[-1][2]
    for s in range(segs):
        sn = (s + 1) % segs
        mb.add_tri(c_hub, r_hub[s], r_hub[sn],
                   uvs=[uv_c, w_uv(0, r_hub[s][0] - wx, r_hub[s][2] - wr), w_uv(0, r_hub[sn][0] - wx, r_hub[sn][2] - wr)],
                   expect_n=(0.0, sgn, 0.0), smooth=8)

    c_in = (wx, y_in, wr)
    r_in = rings[0][2]
    for s in range(segs):
        sn = (s + 1) % segs
        mb.add_tri(c_in, r_in[sn], r_in[s], region="trim", expect_n=(0.0, -sgn, 0.0), smooth=0)

    return mb.finalize()


# --------------------------------------------------------------------------- 5. Main Exotic Supercar Chassis, Interior, V12 & Aero Wing
def build_chassis_and_canopy():
    mb = MeshBuilder("chassis", origin=(0.0, 0.0, 0.0))
    mg = MeshBuilder("glass", origin=(0.0, 0.0, 0.0))

    # --- A. Front Outer Power-Peaked Fenders (x = 26.8 .. 92.0, |y| = 27.4 .. hw) ---
    nx_f = 14
    xs_f = [26.8 + (92.0 - 26.8) * (i / float(nx_f)) for i in range(nx_f + 1)]
    for sgn in (1.0, -1.0):
        s_reg = "side_l" if sgn > 0 else "side_r"
        f_strips = []
        for i, x in enumerate(xs_f):
            tx = i / float(nx_f)
            dx_in = nose_planform_dx(27.4) * 0.36 * (max(0.0, (tx - 0.65) / 0.35) ** 1.6)
            dx_out = nose_planform_dx(half_width_at_x(x)) * (max(0.0, (tx - 0.55) / 0.45) ** 1.5)
            x_in = x + dx_in
            x_out = x + dx_out
            hw = half_width_at_x(x)
            z_in = hood_surface_z(x_in, sgn * 27.4)
            z_peak = beltline_z_at_x(x)
            z_bot = wheel_arch_bottom_z(x_out)
            # Cross-section from inner hood seam -> peaked fender crest -> outer flank -> lower sill
            f_strips.append([
                (x_in,  sgn * 27.4, z_in),
                (0.5 * (x_in + x_out), sgn * (0.5 * (27.4 + hw)), z_peak + 0.9),
                (x_out, sgn * (hw - 0.4), z_peak - 1.2),
                (x_out, sgn * (hw + 0.5), 0.5 * (z_peak + z_bot)),
                (x_out, sgn * (hw - 0.8), z_bot),
            ])
        for i in range(nx_f):
            c0, c1 = f_strips[i], f_strips[i + 1]
            # Keep entire peaked front fender top smooth seamless candy-pink!
            mb.add_quad(c0[0], c1[0], c1[1], c0[1], region="pink", expect_n=(0.15, sgn * 0.2, 1.0), smooth=1)
            mb.add_quad(c0[1], c1[1], c1[2], c0[2], region="pink", expect_n=(0.15, sgn * 0.6, 0.8), smooth=1)
            # Outer front fender flank: mapped to side_l / side_r!
            mb.add_quad(c0[2], c1[2], c1[3], c0[3], region=s_reg, expect_n=(0.0, sgn, 0.1), smooth=1)
            mb.add_quad(c0[3], c1[3], c1[4], c0[4], region=s_reg, expect_n=(0.0, sgn, -0.1), smooth=1)

        # Sleek 3D Swept Supercar Headlight Pod flush on outer front fender slope (x = 74..89.5)!
        hl_p0 = (74.5, sgn * 28.6, hood_surface_z(74.5, 27.4) + 0.45)
        hl_p1 = (88.5 + nose_planform_dx(29.0) * 0.4, sgn * 28.4, 15.8)
        hl_p2 = (88.5 + nose_planform_dx(37.5) * 0.8, sgn * 37.6, 15.0)
        hl_p3 = (75.5, sgn * 37.8, beltline_z_at_x(75.5) - 0.15)
        # Map cleanly onto the Y-blade LED housing region of R_FRONT!
        u_in = 0.34 if sgn < 0 else 0.66
        u_out = 0.06 if sgn < 0 else 0.94
        hl_uvs = [
            uv_in_rect(ptex.R_FRONT, u_in,  0.14, pad=4.0),
            uv_in_rect(ptex.R_FRONT, u_in,  0.40, pad=4.0),
            uv_in_rect(ptex.R_FRONT, u_out, 0.40, pad=4.0),
            uv_in_rect(ptex.R_FRONT, u_out, 0.14, pad=4.0),
        ]
        mb.add_quad(hl_p0, hl_p1, hl_p2, hl_p3, uvs=hl_uvs, expect_n=(0.35, sgn * 0.25, 0.9), smooth=1)

    # --- B. Front Fascia, Honeycomb Intakes, Carbon Splitter & Aero Dive Canards ---
    ny_nose = 14
    ys_n = [-39.0 + 78.0 * (j / float(ny_nose)) for j in range(ny_nose + 1)]
    nose_top, nose_mid, nose_bot, split_tip = [], [], [], []
    for y in ys_n:
        dx = nose_planform_dx(y)
        xf = 92.2 + dx
        zt = hood_surface_z(91.8, y) if abs(y) <= 27.4 else (16.2 - 1.2 * ((abs(y) - 27.4) / 12.0))
        nose_top.append((xf - 0.4, y, zt))
        nose_mid.append((xf + 2.2, y, 10.6))
        nose_bot.append((xf + 0.8, y, 6.2))
        split_tip.append((xf + 5.6, y * 1.03, 5.0))

    for j in range(ny_nose):
        mb.add_quad(nose_top[j], nose_top[j + 1], nose_mid[j + 1], nose_mid[j], region="front", expect_n=(1.0, 0.0, 0.25), smooth=1)
        mb.add_quad(nose_mid[j], nose_mid[j + 1], nose_bot[j + 1], nose_bot[j], region="front", expect_n=(1.0, 0.0, -0.15), smooth=1)
        # Extended 3D Carbon-Fiber Front Splitter Blade!
        mb.add_quad(nose_bot[j], nose_bot[j + 1], split_tip[j + 1], split_tip[j], region="carbon", expect_n=(0.2, 0.0, 1.0), smooth=0)
        b0 = (nose_bot[j][0], nose_bot[j][1], 4.6)
        b1 = (nose_bot[j + 1][0], nose_bot[j + 1][1], 4.6)
        t0 = (split_tip[j][0], split_tip[j][1], 4.6)
        t1 = (split_tip[j + 1][0], split_tip[j + 1][1], 4.6)
        mb.add_quad(split_tip[j], split_tip[j + 1], t1, t0, region="pink", expect_n=(1.0, 0.0, 0.0), smooth=0)
        mb.add_quad(b0, t0, t1, b1, region="carbon", expect_n=(0.0, 0.0, -1.0), smooth=0)

    # Twin Front Carbon Aero Canards / Dive Planes on front bumper cheeks
    for sgn in (1.0, -1.0):
        mb.add_quad((84.5, sgn * 38.2, 9.2), (90.5, sgn * 36.8, 7.8),
                    (91.2, sgn * 41.2, 8.6), (84.8, sgn * 41.8, 10.4),
                    region="carbon", expect_n=(0.0, sgn * 0.3, 1.0), smooth=0, double_sided=True)

    # Frunk Tub under the articulated hood (so opening hood reveals dark carbon bay)
    mb.add_box(27.5, -26.5, 11.5, 87.5, 26.5, 14.2, region="carbon", skip_faces=("-z",))

    # --- C. Rear Widebody Haunches, 3D Side Air Intakes, Slotted V12 Deck & Flying Buttresses ---
    xs_r = [-21.0, -24.5, -31.0, -39.0, -47.0, -55.0, -63.0, -72.0, -82.0, -92.5]
    for sgn in (1.0, -1.0):
        s_reg = "side_l" if sgn > 0 else "side_r"
        r_strips = []
        for x in xs_r:
            hw = half_width_at_x(x)
            zt = beltline_z_at_x(x)
            zb = wheel_arch_bottom_z(x)
            # Deep 3D mid-engine intake pocket right behind door (x = -24.5 .. -36)
            scoop_indent = 3.6 if (-35.0 <= x <= -23.0) else 0.0
            y_deck_in = 22.0 if x > -78.0 else 28.0
            z_deck_in = 35.8 - 2.2 * clamp01((-21.0 - x) / 70.0)
            r_strips.append([
                (x, sgn * y_deck_in, z_deck_in),
                (x, sgn * (hw - 1.2), zt),
                (x, sgn * (hw + 0.5 - scoop_indent), 0.56 * zt + 0.44 * zb),
                (x, sgn * (hw - 0.8), zb),
            ])
        for i in range(len(xs_r) - 1):
            c0, c1 = r_strips[i], r_strips[i + 1]
            mb.add_quad(c0[0], c1[0], c1[1], c0[1], region="pink", expect_n=(0.0, sgn * 0.25, 1.0), smooth=1)
            mb.add_quad(c0[1], c1[1], c1[2], c0[2], region=s_reg, expect_n=(0.0, sgn, 0.15), smooth=1)
            mb.add_quad(c0[2], c1[2], c1[3], c0[3], region=s_reg, expect_n=(0.0, sgn, -0.15), smooth=1)

        # Dark honeycomb mesh throat + 3 horizontal pink strakes inside the 3D mid-engine scoop!
        mb.add_quad((-22.0, sgn * 36.2, 12.0), (-22.0, sgn * 39.2, 12.0),
                    (-22.0, sgn * 39.0, 29.8), (-22.0, sgn * 35.8, 29.8),
                    region="trim", expect_n=(1.0, 0.0, 0.0), smooth=0)
        for sz in (16.5, 21.2, 25.8):
            mb.add_box(-35.0, sgn * 36.5, sz - 0.45, -21.8, sgn * 40.4, sz + 0.45, region="pink", smooth=0)

        # Swept 3D Flying-Buttress C-Pillars arching from roof rear (-21.0, z=45.6) to rear haunch (-76.0, z=35.0)!
        butt_pts = [
            (-20.5, sgn * 23.5, 45.6),
            (-38.0, sgn * 24.8, 42.4),
            (-58.0, sgn * 25.5, 38.5),
            (-76.0, sgn * 25.8, 35.0),
        ]
        for k in range(len(butt_pts) - 1):
            pa, pb = butt_pts[k], butt_pts[k + 1]
            mb.add_quad(
                (pa[0], pa[1] - sgn * 2.2, pa[2]),
                (pb[0], pb[1] - sgn * 2.2, pb[2]),
                (pb[0], pb[1] + sgn * 2.0, pb[2] - 1.2),
                (pa[0], pa[1] + sgn * 2.0, pa[2] - 1.2),
                region="pink", expect_n=(0.0, sgn * 0.3, 1.0), smooth=2, double_sided=True,
            )

    # --- D. Lower Rocker Sills, Carbon Side-Skirt Aero Blades & Flat Sealed Underbody ---
    mb.add_box(-92.0, -37.5, 4.6, 89.0, 37.5, 8.2, region="trim", face_regions={"-z": "carbon"})
    for sgn in (1.0, -1.0):
        # Protruding carbon side-skirt blade beneath the scissor doors!
        mb.add_box(-37.5, sgn * 37.5, 4.6, 41.8, sgn * 41.2, 7.6, region="carbon", smooth=0)
        # Vertical aero shark-fin winglet at rear of side skirt (x = -37.5 .. -33.0)
        mb.add_box(-37.8, sgn * 40.6, 5.0, -33.0, sgn * 41.5, 13.5, region="carbon",
                   face_regions={"+y" if sgn > 0 else "-y": "pink"}, smooth=0)

    # 4 Sealed 3D Inner Wheelhouse Arch Tubs (tucked strictly inside fender skin so they NEVER poke out!)
    for wx, wy_abs, wr_w, ww_tub in (
        (CAR_SPEC["wheel_x_f"], CAR_SPEC["wheel_y_f"], CAR_SPEC["wheel_r_f"], 11.2),
        (CAR_SPEC["wheel_x_r"], CAR_SPEC["wheel_y_r"], CAR_SPEC["wheel_r_r"], 13.6),
    ):
        zc = wr_w
        ar_in = wr_w + 1.15
        for sgn in (1.0, -1.0):
            y_outer = sgn * (wy_abs + ww_tub * 0.28)
            y_inner = sgn * (wy_abs - ww_tub * 0.68)
            arch_pts = []
            for k in range(13):
                ang = math.pi * (k / 12.0)
                px_a = wx + ar_in * math.cos(ang)
                pz_a = min(zc + ar_in * math.sin(ang), beltline_z_at_x(px_a) - 2.2)
                arch_pts.append((px_a, pz_a))
            for k in range(12):
                x_a, z_a = arch_pts[k]
                x_b, z_b = arch_pts[k + 1]
                mb.add_quad((x_a, y_inner, z_a), (x_b, y_inner, z_b), (x_b, y_outer, z_b), (x_a, y_outer, z_a),
                            region="trim", expect_n=(wx - 0.5 * (x_a + x_b), 0.0, zc - 0.5 * (z_a + z_b)), smooth=0, double_sided=True)
            # Inner flat splash wall closing wheel well
            for k in range(11):
                mb.add_tri((wx, y_inner, zc - 4.0),
                           (arch_pts[k][0], y_inner, arch_pts[k][1]),
                           (arch_pts[k + 1][0], y_inner, arch_pts[k + 1][1]),
                           region="trim", expect_n=(0.0, sgn, 0.0), smooth=0)

    # --- E. Greenhouse Roof, A-Pillars, Translucent Windshield & Slotted V12 Engine Bay ---
    # Crowned Metallic-Pink Roof Panel (x = -21.5 .. -1.2, y = -24.5 .. +24.5, z = 44.8 .. 46.2)
    nx_rf, ny_rf = 6, 8
    rf_grid = []
    for i in range(nx_rf + 1):
        xr = -21.5 + (-1.2 - (-21.5)) * (i / float(nx_rf))
        row = []
        for j in range(ny_rf + 1):
            ty = -1.0 + 2.0 * (j / float(ny_rf))
            yr = 24.4 * ty
            zr = 46.15 - 1.35 * (ty * ty) - 0.25 * (((i / float(nx_rf)) - 0.5) ** 2)
            row.append((xr, yr, zr))
        rf_grid.append(row)
    for i in range(nx_rf):
        for j in range(ny_rf):
            p00, p10 = rf_grid[i][j], rf_grid[i + 1][j]
            p11, p01 = rf_grid[i + 1][j + 1], rf_grid[i][j + 1]
            mb.add_quad(p00, p10, p11, p01, region="pink", expect_n=(0.0, 0.0, 1.0), smooth=1)
            # Dark Alcantara headliner inside cabin
            mb.add_quad((p00[0], p00[1], p00[2] - 1.1), (p01[0], p01[1], p01[2] - 1.1),
                        (p11[0], p11[1], p11[2] - 1.1), (p10[0], p10[1], p10[2] - 1.1),
                        region="trim", expect_n=(0.0, 0.0, -1.0), smooth=0)

    # Swept 3D Body-Colored A-Pillars (x = 26.8, y = ±31.0, z = 29.2 -> x = -1.2, y = ±24.4, z = 44.8)
    for sgn in (1.0, -1.0):
        mb.add_cylinder((26.8, sgn * 31.2, 29.0), (-1.2, sgn * 24.4, 44.8), 1.45, 1.25, segs=8, region="pink")

    # Panoramic Raked Curved Windshield Glass (`glass` surface!)
    ws_ny = 8
    ws_bot, ws_top = [], []
    for j in range(ws_ny + 1):
        ty = -1.0 + 2.0 * (j / float(ws_ny))
        ws_bot.append((26.8 - 2.2 * (ty * ty), 30.8 * ty, 29.2 - 0.6 * (ty * ty)))
        ws_top.append((-1.2 - 0.8 * (ty * ty), 24.0 * ty, 45.8 - 1.2 * (ty * ty)))
    for j in range(ws_ny):
        mg.add_quad(ws_bot[j], ws_bot[j + 1], ws_top[j + 1], ws_top[j],
                    region="glass", expect_n=(0.55, 0.0, 0.85), smooth=2, double_sided=True)

    # Rear Cabin Bulkhead + Mid-Mounted 6.5L V12 Engine Bay + Transparent Engine Glass Cover!
    mb.add_box(-22.2, -26.0, 9.0, -20.5, 26.0, 44.5, region="carbon")
    # Engine bay tub (-78 .. -22, y = -22 .. +22)
    mb.add_box(-78.0, -22.5, 14.0, -22.0, 22.5, 22.0, region="trim")
    # 3D V12 Engine Block + Twin Pink Anodized Valve Covers + 12 Velocity Stacks + Carbon X-Brace!
    mb.add_box(-64.0, -13.5, 21.5, -28.0, -3.5, 29.2, region="engine", face_regions={"+z": "engine"})
    mb.add_box(-64.0,  3.5,  21.5, -28.0, 13.5, 29.2, region="engine", face_regions={"+z": "engine"})
    mb.add_box(-62.0, -4.2,  23.0, -30.0,  4.2, 31.4, region="carbon")
    for k in range(6):
        sx = -33.0 - k * 5.2
        mb.add_cylinder((sx, -5.8, 28.5), (sx, -3.2, 32.8), 1.35, 1.55, segs=10, region="chrome")
        mb.add_cylinder((sx,  5.8, 28.5), (sx,  3.2, 32.8), 1.35, 1.55, segs=10, region="chrome")
    # Diagonal Carbon X-Brace over V12 engine!
    mb.add_cylinder((-24.0, -20.0, 35.2), (-72.0,  20.0, 33.4), 0.85, 0.85, segs=8, region="carbon")
    mb.add_cylinder((-24.0,  20.0, 35.2), (-72.0, -20.0, 33.4), 0.85, 0.85, segs=8, region="carbon")

    # Rear deck frame around V12 glass + 3 Slotted Supercar Glass Louver Panes!
    mb.add_box(-92.5, -28.0, 32.8, -75.0, 28.0, 34.8, region="pink", face_regions={"+z": "top"})
    for li in range(3):
        lx0 = -24.0 - li * 16.5
        lx1 = lx0 - 13.8
        z0_l = 41.5 - li * 2.4
        z1_l = z0_l - 1.6
        mg.add_quad((lx1, -19.5, z1_l), (lx0, -19.5, z0_l), (lx0, 19.5, z0_l), (lx1, 19.5, z1_l),
                    region="glass", expect_n=(-0.2, 0.0, 1.0), smooth=1, double_sided=True)

    # --- F. Detailed 2-Seat Cockpit Interior (Quilted Pink/Black Bucket Seats, Dash, Wheel) ---
    # Center carbon console tunnel
    mb.add_box(-20.5, -5.2, 9.0, 25.0, 5.2, 18.8, region="carbon")
    # Red flip-cover V12 Start Button on center console!
    mb.add_cylinder((6.0, 0.0, 18.8), (6.0, 0.0, 19.8), 1.2, 1.0, segs=10, region="pink")
    # Sculpted Supercar Dashboard Binnacle mapped to R_DASH ("199" + "ROOF WEBCAM LIVE")
    mb.add_box(14.5, -31.5, 18.0, 26.8, 31.5, 28.8, region="carbon", face_regions={"-x": "dash"})

    # Two 3D Bolstered Racing Bucket Seats (Driver +Y & Passenger -Y)
    for sy in (14.5, -14.5):
        # Seat cushion + side thigh bolsters
        mb.add_box(-15.5, sy - 7.8, 10.2, 3.5, sy + 7.8, 14.5, region="seat")
        mb.add_box(-15.5, sy - 8.6, 12.0, 2.5, sy - 6.4, 17.5, region="pink")
        mb.add_box(-15.5, sy + 6.4, 12.0, 2.5, sy + 8.6, 17.5, region="pink")
        # Reclined high-back racing shell + integrated headrest!
        mb.add_quad((-14.0, sy - 7.6, 14.0), (-14.0, sy + 7.6, 14.0),
                    (-19.5, sy + 6.2, 38.5), (-19.5, sy - 6.2, 38.5),
                    region="seat", expect_n=(0.95, 0.0, 0.22), smooth=1, double_sided=True)
        mb.add_box(-18.5, sy - 8.4, 15.0, -14.5, sy - 6.2, 31.0, region="pink")
        mb.add_box(-18.5, sy + 6.2, 15.0, -14.5, sy + 8.4, 31.0, region="pink")

    # 3D Flat-Bottom Supercar Steering Wheel on Driver (+Y) side!
    sw_c = (11.2, 14.5, 25.2)
    mb.add_cylinder((16.5, 14.5, 23.5), sw_c, 1.35, 1.15, segs=10, region="carbon")
    sw_pts = []
    for s in range(16):
        a = 2.0 * math.pi * s / 16.0
        rz = 5.2 * math.sin(a)
        if rz < -3.6:
            rz = -3.6  # Authentic flat-bottom supercar wheel!
        ry = 5.4 * math.cos(a)
        sw_pts.append((sw_c[0] - 0.32 * rz, sw_c[1] + ry, sw_c[2] + rz))
    sw_pts.append(sw_pts[0])
    mb.add_tube_path(sw_pts, radius=0.68, segs=8, region="pink", smooth=5)
    mb.add_cylinder((sw_c[0] + 0.5, sw_c[1], sw_c[2]), (sw_c[0] - 0.5, sw_c[1], sw_c[2]), 1.8, 1.8, segs=12, region="carbon")

    # --- G. Rear Supercar Fascia ("NOT PINK" Plate), Quad Exhausts, 5-Fin Diffuser & Swan-Neck Wing ---
    mb.add_quad((-92.8, 40.2, 8.2), (-92.8, -40.2, 8.2), (-92.2, -39.5, 34.2), (-92.2, 39.5, 34.2),
                region="rear", expect_n=(-1.0, 0.0, 0.05), smooth=0)
    # Opaque inner carbon backing wall at x=-91.6 so rear plate never shows backward from inside engine bay!
    mb.add_quad((-91.6, -39.0, 8.4), (-91.6, 39.0, 8.4), (-91.4, 38.8, 34.0), (-91.4, -38.8, 34.0),
                region="carbon", expect_n=(1.0, 0.0, 0.0), smooth=0)
    # Rear Carbon Diffuser Ramp + 5 Aggressive 3D Vertical Venturi Strake Fins!
    mb.add_quad((-86.0, -37.5, 4.6), (-86.0, 37.5, 4.6), (-95.5, 36.8, 9.8), (-95.5, -36.8, 9.8),
                region="carbon", expect_n=(-0.45, 0.0, -0.88), smooth=0, double_sided=True)
    for fy in (-26.0, -13.5, 0.0, 13.5, 26.0):
        mb.add_box(-96.2, fy - 0.65, 4.8, -86.5, fy + 0.65, 11.8, region="carbon",
                   face_regions={"-x": "pink"}, smooth=0)

    # Quad Center-Exit Hollow Titanium Exhaust Tailpipes!
    for ey in (-11.2, -4.0, 4.0, 11.2):
        mb.add_cylinder((-89.5, ey, 12.8), (-96.4, ey, 12.8), 2.45, 2.55, segs=16, region="chrome", cap_a=False, cap_b=False)
        mb.add_cylinder((-96.4, ey, 12.8), (-93.2, ey, 12.8), 2.05, 1.95, segs=16, region="trim", cap_a=False, cap_b=True)

    # High-Mount Swan-Neck Carbon-Fiber GT Rear Wing (z = 49.4, span y = -41 .. +41)!
    # Twin curved swan-neck pylons at y = ±17.5 arching up and forward over top of airfoil
    for py in (-17.5, 17.5):
        pylon_pts = [
            (-79.5, py, 34.2),
            (-83.5, py, 42.5),
            (-86.2, py, 50.2),
            (-89.8, py, 49.2),
        ]
        for k in range(len(pylon_pts) - 1):
            pa, pb = pylon_pts[k], pylon_pts[k + 1]
            mb.add_box(min(pa[0], pb[0]) - 1.6, py - 0.75, min(pa[2], pb[2]) - 0.8,
                       max(pa[0], pb[0]) + 1.6, py + 0.75, max(pa[2], pb[2]) + 0.8,
                       region="carbon", smooth=0)

    # Sculpted Cambered Carbon-Fiber GT Wing Airfoil (x = -83.5 .. -94.8, y = -40.5 .. +40.5)
    ny_w = 10
    ys_w = [-40.5 + 81.0 * (j / float(ny_w)) for j in range(ny_w + 1)]
    for j in range(ny_w):
        ya, yb = ys_w[j], ys_w[j + 1]
        z_arch_a = 48.4 + 0.8 * (1.0 - (ya / 40.5) ** 2)
        z_arch_b = 48.4 + 0.8 * (1.0 - (yb / 40.5) ** 2)
        le_a, le_b = (-83.5, ya, z_arch_a - 0.6), (-83.5, yb, z_arch_b - 0.6)
        mid_top_a, mid_top_b = (-89.0, ya, z_arch_a + 0.8), (-89.0, yb, z_arch_b + 0.8)
        te_a, te_b = (-95.0, ya, z_arch_a + 2.1), (-95.0, yb, z_arch_b + 2.1)
        mid_bot_a, mid_bot_b = (-89.0, ya, z_arch_a - 0.7), (-89.0, yb, z_arch_b - 0.7)
        mb.add_quad(le_a, le_b, mid_top_b, mid_top_a, region="carbon", expect_n=(0.15, 0.0, 1.0), smooth=2)
        mb.add_quad(mid_top_a, mid_top_b, te_b, te_a, region="carbon", expect_n=(-0.2, 0.0, 1.0), smooth=2)
        mb.add_quad(le_a, mid_bot_a, mid_bot_b, le_b, region="carbon", expect_n=(0.1, 0.0, -1.0), smooth=2)
        mb.add_quad(mid_bot_a, te_a, te_b, mid_bot_b, region="carbon", expect_n=(-0.2, 0.0, -1.0), smooth=2)

    # Swept Candy-Pink 3D Rear Wing Endplates at y = ±40.8!
    for sgn in (1.0, -1.0):
        ep = [
            (-81.8, sgn * 40.8, 45.2),
            (-95.8, sgn * 40.8, 46.2),
            (-96.8, sgn * 40.8, 52.4),
            (-83.2, sgn * 40.8, 50.6),
        ]
        ep_in = [(p[0], sgn * 40.0, p[2]) for p in ep]
        mb.add_quad(*ep, region="pink", expect_n=(0.0, sgn, 0.0), smooth=0)
        mb.add_quad(ep_in[0], ep_in[3], ep_in[2], ep_in[1], region="carbon", expect_n=(0.0, -sgn, 0.0), smooth=0)
        for k in range(4):
            kn = (k + 1) % 4
            mb.add_quad(ep[k], ep[kn], ep_in[kn], ep_in[k], region="pink", smooth=0)

    return mb.finalize(), mg.finalize()


def build_all_parts():
    chassis, glass_main = build_chassis_and_canopy()
    hood = build_hood_part()
    door_l, door_l_glass = build_scissor_door_part(is_left=True)
    door_r, door_r_glass = build_scissor_door_part(is_left=False)
    webcam_base, webcam_head = build_webcam_parts()

    wheel_fl = build_wheel_part("wheel_fl", CAR_SPEC["wheel_x_f"],  CAR_SPEC["wheel_y_f"], CAR_SPEC["wheel_r_f"], CAR_SPEC["wheel_w_f"], True,  dish_depth=2.4)
    wheel_fr = build_wheel_part("wheel_fr", CAR_SPEC["wheel_x_f"], -CAR_SPEC["wheel_y_f"], CAR_SPEC["wheel_r_f"], CAR_SPEC["wheel_w_f"], False, dish_depth=2.4)
    wheel_rl = build_wheel_part("wheel_rl", CAR_SPEC["wheel_x_r"],  CAR_SPEC["wheel_y_r"], CAR_SPEC["wheel_r_r"], CAR_SPEC["wheel_w_r"], True,  dish_depth=3.6)
    wheel_rr = build_wheel_part("wheel_rr", CAR_SPEC["wheel_x_r"], -CAR_SPEC["wheel_y_r"], CAR_SPEC["wheel_r_r"], CAR_SPEC["wheel_w_r"], False, dish_depth=3.6)

    parts = {
        "chassis":      chassis,
        "hood":         hood,
        "door_l":       door_l,
        "door_r":       door_r,
        "webcam_base":  webcam_base,
        "webcam_head":  webcam_head,
        "wheel_fl":     wheel_fl,
        "wheel_fr":     wheel_fr,
        "wheel_rl":     wheel_rl,
        "wheel_rr":     wheel_rr,
        "glass":        glass_main,
        "door_l_glass": door_l_glass,
        "door_r_glass": door_r_glass,
    }
    return parts


# --------------------------------------------------------------------------- Articulation & 4-Clip Pose Engine
def evaluate_pose(parts, clip_name, phase01):
    """Returns dict[part_name] -> (world_pos_vec3, world_quat_xyzw) in Quake coordinates.
    All 4 wheels stay grounded at z=0 during idle/showoff, spin smoothly in cruise/boost,
    the roof webcam pans & tilts like a live streamer cam, and scissor doors swing high!"""
    tau = 2.0 * math.pi * phase01

    body_dz = 0.0
    body_pitch = 0.0   # +pitch_y lifts +X nose UP
    body_roll = 0.0
    hood_open = 0.0    # deg (pivots nose down / rear or front open; hinged at cowl x=27 -> -pitch lifts +X nose UP!)
    door_deg = 0.0     # Lamborghini scissor door upward swing!
    steer_deg = 0.0
    wheel_spin = 0.0   # forward roll around +Y -> +pitch_y!
    cam_yaw = 0.0
    cam_pitch = 0.0

    if clip_name == "idle_scan":
        # Subtle V12 engine idle rumble + sentient roof webcam panning left/right & nodding!
        body_dz = 0.22 * math.sin(tau * 2.0)
        body_roll = 0.35 * math.sin(tau * 3.0)
        cam_yaw = 28.0 * math.sin(tau)
        cam_pitch = -5.0 + 7.5 * math.sin(tau * 2.0)
    elif clip_name == "cruise_drive":
        # High-speed cruise: 2 full wheel revolutions per loop, slight road suspension bob, active webcam tracking!
        body_dz = 0.45 * math.sin(tau * 2.0)
        body_pitch = 0.65 * math.sin(tau)
        steer_deg = 5.5 * math.sin(tau)
        wheel_spin = 720.0 * phase01
        cam_yaw = 16.0 * math.sin(tau)
        cam_pitch = -3.0 + 4.0 * math.cos(tau * 2.0)
    elif clip_name == "scissor_showoff":
        # Smoothly swings BOTH Lamborghini scissor doors UP 58 deg + pops hood slightly + webcam looks around proudly!
        s = 0.5 - 0.5 * math.cos(tau)  # smooth 0 -> 1 -> 0 bell curve!
        s_hold = min(1.0, s * 1.35)
        s_hold = s_hold * s_hold * (3.0 - 2.0 * s_hold)
        door_deg = 58.0 * s_hold
        hood_open = 18.0 * s_hold
        cam_yaw = 38.0 * math.sin(tau) * s_hold
        cam_pitch = 8.0 * s_hold
    elif clip_name == "turbo_boost":
        # Full-throttle V12 launch squat! Nose lifts, rear squats onto wide tires, 4x wheel spin, webcam pinned back!
        pulse = 0.5 - 0.5 * math.cos(tau)
        body_pitch = -2.4 * (0.4 + 0.6 * pulse)  # wait: in rot_y, let's check sign!
        body_dz = 0.35 * math.sin(tau * 4.0)
        wheel_spin = 1440.0 * phase01
        cam_yaw = 8.0 * math.sin(tau * 3.0)
        cam_pitch = -14.0 * (0.5 + 0.5 * pulse)

    # Note on quat_from_axis_angle((0,1,0), deg):
    # Right-hand rule around +Y: thumb along +Y (left) -> fingers curl from +Z toward +X!
    # Wait: (0,1,0) x (0,0,1) = (+1, 0, 0), and (0,1,0) x (1,0,0) = (0, 0, -1)!
    # So +deg around +Y rotates +X DOWNWARD toward -Z (forward wheel roll!!),
    # and -deg around +Y rotates +X UPWARD toward +Z (lifting front hood / scissor doors / nose-up wheelie!!)!
    if clip_name == "turbo_boost":
        pulse = 0.5 - 0.5 * math.cos(tau)
        body_pitch = -2.2 * (0.45 + 0.55 * pulse)  # negative around +Y lifts +X nose UP!

    q_body = quat_euler_zyx(0.0, body_pitch, body_roll)
    R_body = quat_to_mat3(q_body)
    p_body = np.array([0.0, 0.0, body_dz], dtype=np.float64)

    def body_child_trs(local_pivot, q_local):
        piv = np.asarray(local_pivot, dtype=np.float64)
        w_pos = p_body + (R_body @ piv)
        w_quat = quat_mul(q_body, q_local)
        return w_pos, w_quat

    q_ident = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    poses = {}
    poses["chassis"] = (p_body, q_body)
    poses["glass"] = (p_body, q_body)
    poses["webcam_base"] = (p_body, q_body)

    # Hood hinged at cowl (27.0, 0.0, 29.0): +X extends forward, so -hood_open around +Y lifts front of hood UP!
    q_hood_loc = quat_euler_zyx(0.0, -hood_open, 0.0)
    poses["hood"] = body_child_trs(parts["hood"]["origin"], q_hood_loc)

    # Scissor doors hinged near front A-pillar (40.5, ±38.8, 28.5):
    # Door extends rearward (-X from pivot!). Around +Y, -deg moves -X DOWN, +deg moves -X UPWARD!
    # Let's verify: (0,1,0) x (-1,0,0) = (0, 0, +1) -> +door_deg around +Y lifts the rear of the scissor door UP into the air!
    # Plus slight outward flare (yaw_z = +10 deg on left +Y door, -10 deg on right -Y door) to clear the A-pillar!
    flare_deg = 11.0 * (door_deg / 58.0) if door_deg > 0.0 else 0.0
    q_dl = quat_euler_zyx(flare_deg, door_deg, 0.0)
    q_dr = quat_euler_zyx(-flare_deg, door_deg, 0.0)
    poses["door_l"] = body_child_trs(parts["door_l"]["origin"], q_dl)
    poses["door_l_glass"] = poses["door_l"]
    poses["door_r"] = body_child_trs(parts["door_r"]["origin"], q_dr)
    poses["door_r_glass"] = poses["door_r"]

    # Roof Webcam pan (yaw_z) & tilt (pitch_y: -deg tilts +X lens UP, +deg tilts +X lens DOWN)
    q_cam = quat_euler_zyx(cam_yaw, -cam_pitch, 0.0)
    poses["webcam_head"] = body_child_trs(parts["webcam_head"]["origin"], q_cam)

    # 4 Wheels stay planted on z=0 ground (spin around +Y = +wheel_spin!)
    for wnm in ("wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"):
        wp = np.asarray(parts[wnm]["origin"], dtype=np.float64)
        st = steer_deg if wnm in ("wheel_fl", "wheel_fr") else 0.0
        qw = quat_euler_zyx(st, wheel_spin, 0.0)
        poses[wnm] = (wp, qw)

    return poses


# --------------------------------------------------------------------------- Export glTF 2.0 Binary (.glb)
def export_glb(parts, tex_dict, out_glb_path):
    bin_blob = bytearray()
    buffer_views = []
    accessors = []

    def pad4():
        while len(bin_blob) % 4 != 0:
            bin_blob.append(0)

    def add_bv(raw_bytes, target=None):
        pad4()
        off = len(bin_blob)
        bin_blob.extend(raw_bytes)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw_bytes)}
        if target is not None:
            bv["target"] = target
        idx = len(buffer_views)
        buffer_views.append(bv)
        return idx

    def add_acc(arr, comp_type, acc_type, target=None):
        arr = np.ascontiguousarray(arr)
        bv_idx = add_bv(arr.tobytes(), target=target)
        acc = {
            "bufferView": bv_idx,
            "componentType": comp_type,
            "count": int(len(arr)),
            "type": acc_type,
        }
        if acc_type == "SCALAR":
            acc["min"] = [float(arr.min())]
            acc["max"] = [float(arr.max())]
        else:
            acc["min"] = [float(x) for x in arr.min(axis=0)]
            acc["max"] = [float(x) for x in arr.max(axis=0)]
        idx = accessors.__len__()
        accessors.append(acc)
        return idx

    def embed_png(pil_im):
        buf = io.BytesIO()
        pil_im.save(buf, format="PNG", optimize=True)
        return add_bv(buf.getvalue())

    bv_base = embed_png(tex_dict["atlas"])
    bv_orm  = embed_png(tex_dict["orm"])
    bv_glow = embed_png(tex_dict["glow"])
    bv_glas = embed_png(tex_dict["glass"])

    ordered_names = [
        "chassis", "hood", "door_l", "door_r",
        "webcam_base", "webcam_head",
        "wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr",
        "glass", "door_l_glass", "door_r_glass",
    ]
    glass_set = {"glass", "door_l_glass", "door_r_glass"}

    meshes_gltf = []
    nodes_gltf = []
    node_map = {}

    rest_poses = evaluate_pose(parts, "idle_scan", 0.0)

    for nm in ordered_names:
        p = parts[nm]
        vq = p["verts"]
        nq = p["norms"]
        uv = p["uvs"]
        tr = p["tris"].astype(np.uint16).reshape(-1)

        # Even cyclic permutation (X_q, Y_q, Z_q) -> (Y_q, Z_q, X_q) * GLTF_SCALE
        vg = np.column_stack([vq[:, 1], vq[:, 2], vq[:, 0]]).astype(np.float32) * GLTF_SCALE
        ng = np.column_stack([nq[:, 1], nq[:, 2], nq[:, 0]]).astype(np.float32)
        ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-8)

        acc_p = add_acc(vg, 5126, "VEC3", target=34962)
        acc_n = add_acc(ng, 5126, "VEC3", target=34962)
        acc_u = add_acc(uv.astype(np.float32), 5126, "VEC2", target=34962)
        acc_i = add_acc(tr, 5123, "SCALAR", target=34963)

        mat_idx = 1 if nm in glass_set else 0
        mesh_idx = len(meshes_gltf)
        meshes_gltf.append({
            "name": f"pink_supercar_{nm}",
            "primitives": [{
                "attributes": {"POSITION": acc_p, "NORMAL": acc_n, "TEXCOORD_0": acc_u},
                "indices": acc_i,
                "material": mat_idx,
            }],
        })

        rp, rq = rest_poses[nm]
        node_idx = len(nodes_gltf)
        node_map[nm] = node_idx
        nodes_gltf.append({
            "name": nm,
            "mesh": mesh_idx,
            "translation": [float(rp[1] * GLTF_SCALE), float(rp[2] * GLTF_SCALE), float(rp[0] * GLTF_SCALE)],
            "rotation": [float(rq[1]), float(rq[2]), float(rq[0]), float(rq[3])],
        })

    root_idx = len(nodes_gltf)
    nodes_gltf.append({"name": "Pink_Supercar_Root", "children": list(node_map.values())})

    # Export 4 rich 60 FPS glTF animation clips!
    animations_gltf = []
    gltf_clip_specs = [
        ("Idle_WebcamScan",      "idle_scan",       120, 60.0),
        ("Cruise_Drive",         "cruise_drive",    120, 60.0),
        ("ScissorDoors_Showoff", "scissor_showoff", 180, 60.0),
        ("Turbo_Boost",          "turbo_boost",     120, 60.0),
    ]
    for gltf_cname, mode_key, nf_c, fps_c in gltf_clip_specs:
        times = (np.arange(nf_c + 1, dtype=np.float32) / float(fps_c))
        t_acc = add_acc(times, 5126, "SCALAR")
        pos_tr = {nm: np.zeros((nf_c + 1, 3), dtype=np.float32) for nm in ordered_names}
        rot_tr = {nm: np.zeros((nf_c + 1, 4), dtype=np.float32) for nm in ordered_names}

        for fi in range(nf_c + 1):
            ph = (fi / float(nf_c)) % 1.0
            pose = evaluate_pose(parts, mode_key, ph)
            for nm in ordered_names:
                pq, rq = pose[nm]
                pos_tr[nm][fi] = [pq[1] * GLTF_SCALE, pq[2] * GLTF_SCALE, pq[0] * GLTF_SCALE]
                rot_tr[nm][fi] = [rq[1], rq[2], rq[0], rq[3]]

        # Quaternion sign continuity so LINEAR slerp never flips across 360 deg wheel rotations!
        for nm in ordered_names:
            r_arr = rot_tr[nm]
            for fi in range(1, len(r_arr)):
                if np.dot(r_arr[fi - 1], r_arr[fi]) < 0.0:
                    r_arr[fi] = -r_arr[fi]

        samplers, channels = [], []
        for nm in ordered_names:
            ni = node_map[nm]
            acc_t = add_acc(pos_tr[nm], 5126, "VEC3")
            acc_r = add_acc(rot_tr[nm], 5126, "VEC4")
            st_i = len(samplers); samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": acc_t})
            sr_i = len(samplers); samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": acc_r})
            channels.append({"sampler": st_i, "target": {"node": ni, "path": "translation"}})
            channels.append({"sampler": sr_i, "target": {"node": ni, "path": "rotation"}})

        animations_gltf.append({"name": gltf_cname, "samplers": samplers, "channels": channels})

    gltf_doc = {
        "asset": {"version": "2.0", "generator": "BakersfieldQuake Pink Supercar + Roof Webcam Builder"},
        "scene": 0,
        "scenes": [{"name": "PinkSupercarScene", "nodes": [root_idx]}],
        "nodes": nodes_gltf,
        "meshes": meshes_gltf,
        "animations": animations_gltf,
        "materials": [
            {
                "name": "PinkSupercar_Atlas_PBR",
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0},
                    "metallicRoughnessTexture": {"index": 1},
                    "metallicFactor": 1.0,
                    "roughnessFactor": 1.0,
                },
                "occlusionTexture": {"index": 1},
                "emissiveTexture": {"index": 2},
                "emissiveFactor": [1.0, 1.0, 1.0],
                "doubleSided": True,
            },
            {
                "name": "PinkSupercar_CanopyGlass",
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 3},
                    "metallicFactor": 0.10,
                    "roughnessFactor": 0.08,
                },
                "alphaMode": "BLEND",
                "doubleSided": True,
            },
        ],
        "textures": [
            {"sampler": 0, "source": 0},
            {"sampler": 0, "source": 1},
            {"sampler": 0, "source": 2},
            {"sampler": 0, "source": 3},
        ],
        "images": [
            {"bufferView": bv_base, "mimeType": "image/png", "name": "pink_supercar_atlas_2k"},
            {"bufferView": bv_orm,  "mimeType": "image/png", "name": "pink_supercar_orm_2k"},
            {"bufferView": bv_glow, "mimeType": "image/png", "name": "pink_supercar_glow_2k"},
            {"bufferView": bv_glas, "mimeType": "image/png", "name": "pink_supercar_glass"},
        ],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "bufferViews": buffer_views,
        "accessors": accessors,
        "buffers": [{"byteLength": len(bin_blob)}],
    }

    json_bytes = json.dumps(gltf_doc, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4 != 0:
        json_bytes += b" "
    pad4()

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    with open(out_glb_path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total_len))
        f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
        f.write(json_bytes)
        f.write(struct.pack("<II", len(bin_blob), 0x004E4942))
        f.write(bin_blob)


# --------------------------------------------------------------------------- Export DarkPlaces MD3, Skin, Shader & Frames
def export_darkplaces_md3(parts):
    os.makedirs(PROGS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)

    frame_schedule = []
    for cname, f_start, f_count, _fps, _desc in ANIM_CLIPS:
        for i in range(f_count):
            frame_schedule.append((cname, i / float(f_count)))
    assert len(frame_schedule) == TOTAL_MD3_FRAMES

    all_poses = [evaluate_pose(parts, ck, ph) for ck, ph in frame_schedule]

    def build_md3_surfaces_chunked(surf_prefix, shader_name, part_names, max_v=3600, max_t=7200):
        """Packs parts (slicing triangles cleanly if a part exceeds MD3's 4096-vert cap)
        into one or more MD3-compliant surfaces."""
        # Flatten into world-indexed sub-batches <= max_v
        out_surfs = []
        chunk_idx = 0

        for pnm in part_names:
            p = parts[pnm]
            tris_all = p["tris"].tolist()
            uvs_all = p["uvs"]
            verts_all = p["verts"].astype(np.float64)
            norms_all = p["norms"].astype(np.float64)

            t_cursor = 0
            while t_cursor < len(tris_all):
                remap = {}
                sub_tris = []
                sub_v_idx = []
                while t_cursor < len(tris_all) and len(sub_Tris_next := sub_tris) < max_t:
                    a, b, c = tris_all[t_cursor]
                    needed = sum(1 for vi in {a, b, c} if vi not in remap)
                    if len(sub_v_idx) + needed > max_v:
                        break
                    nt = []
                    for vi in (a, b, c):
                        if vi not in remap:
                            remap[vi] = len(sub_v_idx)
                            sub_v_idx.append(vi)
                        nt.append(remap[vi])
                    sub_tris.append(tuple(nt))
                    t_cursor += 1

                idx_arr = np.asarray(sub_v_idx, dtype=np.int32)
                va = verts_all[idx_arr]
                na = norms_all[idx_arr]
                st_sub = list(map(tuple, uvs_all[idx_arr].tolist()))

                frames_out = []
                for pose in all_poses:
                    w_pos, w_quat = pose[pnm]
                    Rm = quat_to_mat3(w_quat)
                    vp = (va @ Rm.T) + w_pos
                    np_r = na @ Rm.T
                    frames_out.append((list(map(tuple, vp.tolist())), list(map(tuple, np_r.tolist()))))

                sname = surf_prefix if chunk_idx == 0 else f"{surf_prefix}_{chunk_idx}"
                chunk_idx += 1
                out_surfs.append(dict(name=sname, shader=shader_name, tris=sub_tris, st=st_sub, frames=frames_out))

        return out_surfs

    sh_body = "progs/pink_supercar_tex"
    sh_glass = "progs/pink_supercar_glass"
    surfaces = (
        build_md3_surfaces_chunked("car_body",   sh_body,  ["chassis"])
        + build_md3_surfaces_chunked("car_hood", sh_body,  ["hood", "door_l", "door_r"])
        + build_md3_surfaces_chunked("webcam",   sh_body,  ["webcam_base", "webcam_head"])
        + build_md3_surfaces_chunked("wheels",   sh_body,  ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"])
        + build_md3_surfaces_chunked("glass",    sh_glass, ["glass", "door_l_glass", "door_r_glass"])
    )
    assert len(surfaces) <= 32, f"Too many MD3 surfaces: {len(surfaces)}"

    md3_path = os.path.join(PROGS_DIR, "pink_supercar.md3")
    md3lib.write(md3_path, dict(name="pink_supercar", surfaces=surfaces))

    skin_path = os.path.join(PROGS_DIR, "pink_supercar.md3_0.skin")
    with open(skin_path, "w", encoding="ascii", newline="\n") as sf:
        for s in surfaces:
            sf.write(f"{s['name']},{s['shader']}\n")

    shader_path = os.path.join(SCRIPTS_DIR, "pink_supercar.shader")
    shader_txt = (
        "// written by source/mm_tools/build_pink_supercar.py\n\n"
        f"{sh_body}\n{{\n\tcull none\n"
        f"\t{{\n\t\tmap {sh_body}\n\t\trgbGen lightingDiffuse\n\t}}\n"
        f"\t{{\n\t\tmap {sh_body}_glow\n\t\tblendfunc add\n\t\trgbGen identity\n\t}}\n}}\n\n"
        f"{sh_glass}\n{{\n\tcull none\n\t{{\n\t\tmap {sh_glass}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
    )
    with open(shader_path, "w", encoding="utf-8", newline="\n") as shf:
        shf.write(shader_txt)

    frames_txt_path = os.path.join(PROGS_DIR, "pink_supercar_frames.txt")
    with open(frames_txt_path, "w", encoding="utf-8", newline="\n") as ff:
        ff.write("# Pink Exotic Supercar ('It's not pink') + Roof Webcam — 64-Frame MD3 Table\n")
        for cname, f0, fn, fps, desc in ANIM_CLIPS:
            ff.write(f"{cname:18s} : frames {f0:2d}..{f0 + fn - 1:2d} ({fn:2d}f @ {fps:4.1f} fps) — {desc}\n")

    return md3_path


def save_parts_cache(parts, out_npz):
    payload = {}
    for nm, p in parts.items():
        payload[f"{nm}_origin"] = np.asarray(p["origin"], dtype=np.float32)
        payload[f"{nm}_verts"]  = p["verts"]
        payload[f"{nm}_norms"]  = p["norms"]
        payload[f"{nm}_uvs"]    = p["uvs"]
        payload[f"{nm}_tris"]   = p["tris"]
    np.savez_compressed(out_npz, **payload)


def validate_outputs(glb_path, md3_path, parts):
    assert os.path.isfile(glb_path), f"Missing GLB: {glb_path}"
    assert os.path.isfile(md3_path), f"Missing MD3: {md3_path}"
    m = md3lib.read(md3_path)
    assert m["nframes"] == TOTAL_MD3_FRAMES
    solid_z0 = []
    for s in m["surfaces"]:
        assert 0 < len(s["st"]) <= 4096
        assert 0 < len(s["tris"]) <= 8192
        v0 = np.asarray(s["frames"][0][0], dtype=np.float32)
        solid_z0.append(float(v0[:, 2].min()))
    z_min = min(solid_z0)
    assert abs(z_min) < 0.05, f"Tire ground contact error: z_min={z_min:.4f} (expected 0.0)!"

    tot_v = sum(len(p["verts"]) for p in parts.values())
    tot_t = sum(len(p["tris"]) for p in parts.values())
    print(f"  [OK] Mesh stats      : {len(parts)} articulated parts, {tot_v:,} verts, {tot_t:,} tris")
    print(f"  [OK] GLB exported    : {glb_path} ({os.path.getsize(glb_path) / 1e6:.2f} MB, 4 animations)")
    print(f"  [OK] MD3 exported    : {md3_path} ({os.path.getsize(md3_path) / 1e6:.2f} MB, {m['nframes']}f, z_min={z_min:.3f})")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("1. Painting 2048x2048 studio textures, hood mural, 'It's not pink' doors & webcam optics...")
    tex_dict = ptex.generate_all_textures(OUT_DIR, PROGS_DIR)

    print("2. Sculpting 3D Pink Exotic Supercar + Articulated Scissor Doors + Roof Webcam...")
    parts = build_all_parts()
    save_parts_cache(parts, os.path.join(OUT_DIR, "pink_supercar_parts.npz"))

    glb_path = os.path.join(MOD_DIR, "pink_supercar.glb")
    print("3. Exporting glTF 2.0 binary (pink_supercar.glb) & DarkPlaces MD3 (progs/pink_supercar.md3)...")
    export_glb(parts, tex_dict, glb_path)
    md3_path = export_darkplaces_md3(parts)
    validate_outputs(glb_path, md3_path, parts)


if __name__ == "__main__":
    main()
