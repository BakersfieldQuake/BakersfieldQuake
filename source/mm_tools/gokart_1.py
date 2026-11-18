"""Procedural 3D MD3 Builder & Texture Generator for Go-Kart #1: "Bakersfield Tubular Classic".

Outputs (only owned files):
  - source/mm_tools/gokart_1.py (this script)
  - progs/gokart_1.md3
  - progs/gokart_1.md3_0.skin
  - progs/gk1_*.png
  - source/mm_tools/out/gokart_1_meta.json

Coordinate system (Quake / DarkPlaces MD3 standard):
  +X = forward, +Y = left, +Z = up, ground contact plane at Z = 0.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_DIR = os.path.join(REPO_ROOT, "progs")
OUT_DIR = os.path.join(HERE, "out")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib

# ---------------------------------------------------------------------------
# Palette & Constants
# ---------------------------------------------------------------------------
PALETTE = ["#c81e24", "#1d4ed8", "#d4a024", "#1c1917"]

WHEEL_FRONT_X = 25.0
WHEEL_FRONT_Y = 24.5
WHEEL_FRONT_R = 9.5
WHEEL_FRONT_HW = 5.0

WHEEL_REAR_X = -25.0
WHEEL_REAR_Y = 25.5
WHEEL_REAR_R = 11.0
WHEEL_REAR_HW = 6.5

SEAT_POS = {"x": -9.0, "y": 0.0, "z": 9.5}
STEER_POS = {"x": 13.0, "y": 0.0, "z": 24.0}
EXHAUST_TIP = {"x": -45.5, "y": -6.0, "z": 15.85, "dx": -1.0, "dy": 0.0, "dz": 0.05}

SHADERS = {
    "chassis":    "progs/gk1_frame",
    "seat":       "progs/gk1_seat",
    "steering":   "progs/gk1_steering",
    "engine":     "progs/gk1_engine",
    "exhaust":    "progs/gk1_exhaust",
    "nose_plate": "progs/gk1_nose",
    "wheel_fl":   "progs/gk1_wheel",
    "wheel_fr":   "progs/gk1_wheel",
    "wheel_rl":   "progs/gk1_wheel",
    "wheel_rr":   "progs/gk1_wheel",
    "flame_outer":"progs/gk1_flame",
    "flame_core": "progs/gk1_flame",
    "shrapnel":   "progs/gk1_engine",
}

# UV rects inside 1024x1024 atlases
UV_Q1 = (0.02, 0.02, 0.48, 0.48)
UV_Q2 = (0.52, 0.02, 0.98, 0.48)
UV_Q3 = (0.02, 0.52, 0.48, 0.98)
UV_Q4 = (0.52, 0.52, 0.98, 0.98)

# Frame sub-atlas rects (gk1_frame.png)
UV_FRAME_TUBE   = UV_Q1
UV_FRAME_ACCENT = UV_Q2
UV_FRAME_FLOOR  = UV_Q3
UV_FRAME_STEEL  = UV_Q4

# Seat sub-atlas rects (gk1_seat.png)
UV_SEAT_QUILT   = UV_Q1
UV_SEAT_BOLSTER = UV_Q2
UV_SEAT_CARBON  = UV_Q3
UV_SEAT_CREST   = UV_Q4

# Steering sub-atlas rects (gk1_steering.png)
UV_STEER_GRIP   = UV_Q1
UV_STEER_SPOKE  = UV_Q2
UV_STEER_HUB    = UV_Q3
UV_STEER_PEDAL  = UV_Q4

# Engine sub-atlas rects (gk1_engine.png)
UV_ENG_ALUM     = UV_Q1
UV_ENG_SHROUD   = UV_Q2
UV_ENG_TANK     = UV_Q3
UV_ENG_CHAIN    = UV_Q4

# Exhaust sub-atlas rects (gk1_exhaust.png)
UV_EXH_MUFFLER  = UV_Q1
UV_EXH_HEADER   = UV_Q2
UV_EXH_TIP      = UV_Q3
UV_EXH_CLAMP    = UV_Q4

# Wheel sub-atlas rects (gk1_wheel.png)
UV_WHL_TREAD    = (0.01, 0.01, 0.49, 0.49)
UV_WHL_SIDE     = (0.51, 0.01, 0.99, 0.49)
UV_WHL_DISH     = (0.01, 0.51, 0.49, 0.99)
UV_WHL_HARDWARE = (0.51, 0.51, 0.99, 0.99)

# Flame sub-atlas rects (gk1_flame.png)
UV_FLAME_OUTER  = UV_Q1
UV_FLAME_CORE   = UV_Q2
UV_BLAST_OUTER  = UV_Q3
UV_BLAST_CORE   = UV_Q4


# ---------------------------------------------------------------------------
# Vector & Transform Helpers
# ---------------------------------------------------------------------------
def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vlen(a):
    return math.sqrt(max(0.0, vdot(a, a)))


def vnorm(a):
    l = vlen(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-9 else (0.0, 0.0, 1.0)


def vlerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def rot_x(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p, deg):
    """+deg pitches +X up toward +Z."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)


def rot_z(p, deg):
    """+deg yaws +X toward +Y."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def basis_from_axis(axis, up_hint=(0.0, 0.0, 1.0)):
    X = vnorm(axis)
    if abs(vdot(X, up_hint)) > 0.96:
        up_hint = (0.0, 1.0, 0.0) if abs(X[1]) < 0.9 else (1.0, 0.0, 0.0)
    Y = vnorm(vcross(up_hint, X))
    Z = vcross(X, Y)
    return X, Y, Z


def catmull_rom_chain(ctrl_pts, samples_per_seg=4):
    """Smooth Catmull-Rom spline interpolation preserving endpoints."""
    if len(ctrl_pts) < 3 or samples_per_seg <= 1:
        return list(ctrl_pts)
    ext = [ctrl_pts[0]] + list(ctrl_pts) + [ctrl_pts[-1]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n_s = samples_per_seg if i < len(ext) - 3 else samples_per_seg + 1
        for k in range(n_s):
            t = k / float(samples_per_seg)
            if i == len(ext) - 3 and k == samples_per_seg:
                t = 1.0
            t2, t3 = t * t, t * t * t
            pt = []
            for d in range(3):
                val = 0.5 * (
                    2.0 * p1[d]
                    + (-p0[d] + p2[d]) * t
                    + (2.0 * p0[d] - 5.0 * p1[d] + 4.0 * p2[d] - p3[d]) * t2
                    + (-p0[d] + 3.0 * p1[d] - 3.0 * p2[d] + p3[d]) * t3
                )
                pt.append(val)
            out.append((pt[0], pt[1], pt[2]))
    return out


# ---------------------------------------------------------------------------
# Procedural Mesh Builder
# ---------------------------------------------------------------------------
class MeshPart:
    def __init__(self, name):
        self.name = name
        self.verts = []
        self.norms = []
        self.st = []
        self.tris = []

    def append_part(self, other, offset=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, scale=1.0):
        base = len(self.verts)
        for p, n, uv in zip(other.verts, other.norms, other.st):
            q = vmul(p, scale)
            qn = n
            if rx:
                q, qn = rot_x(q, rx), rot_x(qn, rx)
            if ry:
                q, qn = rot_y(q, ry), rot_y(qn, ry)
            if rz:
                q, qn = rot_z(q, rz), rot_z(qn, rz)
            self.verts.append(vadd(q, offset))
            self.norms.append(vnorm(qn))
            self.st.append(uv)
        for a, b, c in other.tris:
            self.tris.append((a + base, b + base, c + base))

    def add_quad(self, p0, p1, p2, p3, uv0, uv1, uv2, uv3, nrm=None, two_sided=False):
        if nrm is None:
            nrm = vnorm(vcross(vsub(p1, p0), vsub(p2, p0)))
        w_n = vcross(vsub(p1, p0), vsub(p2, p0))
        b = len(self.verts)
        self.verts += [p0, p1, p2, p3]
        self.norms += [nrm, nrm, nrm, nrm]
        self.st += [uv0, uv1, uv2, uv3]
        if vdot(w_n, nrm) >= 0.0:
            self.tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        else:
            self.tris += [(b, b + 2, b + 1), (b, b + 3, b + 2)]
        if two_sided:
            b2 = len(self.verts)
            nr = vmul(nrm, -1.0)
            self.verts += [p0, p1, p2, p3]
            self.norms += [nr, nr, nr, nr]
            self.st += [uv0, uv1, uv2, uv3]
            if vdot(w_n, nrm) >= 0.0:
                self.tris += [(b2, b2 + 2, b2 + 1), (b2, b2 + 3, b2 + 2)]
            else:
                self.tris += [(b2, b2 + 1, b2 + 2), (b2, b2 + 2, b2 + 3)]

    def add_chamfer_box(self, x0, x1, y0, y1, z0, z1, ch=0.25, uv_rect=UV_Q1, top_uv=None):
        """Chamfered 8-facet box extruded along X with crisp facet normals."""
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        yc, yr = 0.5 * (y0 + y1), 0.5 * (y1 - y0)
        zc, zr = 0.5 * (z0 + z1), 0.5 * (z1 - z0)
        c = min(ch, 0.44 * min(max(yr, 1e-4), max(zr, 1e-4)))
        loop = [
            (yc + yr, zc - zr + c),
            (yc + yr, zc + zr - c),
            (yc + yr - c, zc + zr),
            (yc - yr + c, zc + zr),
            (yc - yr, zc + zr - c),
            (yc - yr, zc - zr + c),
            (yc - yr + c, zc - zr),
            (yc + yr - c, zc - zr),
        ]
        tu = top_uv if top_uv else uv_rect
        for i in range(8):
            ip = (i + 1) % 8
            p0 = (x0, loop[i][0], loop[i][1])
            p1 = (x1, loop[i][0], loop[i][1])
            p2 = (x1, loop[ip][0], loop[ip][1])
            p3 = (x0, loop[ip][0], loop[ip][1])
            t_loop = vadd(vsub(p3, p0), vsub(p2, p1))
            t_x = vadd(vsub(p1, p0), vsub(p2, p3))
            fn = vnorm(vcross(t_loop, t_x))
            u0, v0, u1, v1 = tu if abs(fn[2]) > 0.75 else uv_rect
            self.add_quad(p0, p1, p2, p3, (u0, v1), (u1, v1), (u1, v0), (u0, v0), nrm=fn)

        u0, v0, u1, v1 = uv_rect
        uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        for x_end, nx in ((x0, -1.0), (x1, +1.0)):
            b_idx = len(self.verts)
            self.verts.append((x_end, yc, zc))
            self.norms.append((nx, 0.0, 0.0))
            self.st.append((uc, vc))
            for ya, za in loop:
                uu = uc + 0.46 * (u1 - u0) * ((ya - yc) / max(yr, 1e-6))
                vv = vc - 0.46 * (v1 - v0) * ((za - zc) / max(zr, 1e-6))
                self.verts.append((x_end, ya, za))
                self.norms.append((nx, 0.0, 0.0))
                self.st.append((uu, vv))
            for i in range(8):
                i1 = b_idx + 1 + i
                i2 = b_idx + 1 + (i + 1) % 8
                self.tris.append((b_idx, i1, i2) if nx > 0 else (b_idx, i2, i1))

    def add_lathe(self, origin, axis, profile, segs=24, uv_mode="cyl", uv_rect=UV_Q1, up_hint=(0.0, 0.0, 1.0), phase_deg=0.0):
        """Revolves profile=[(x_along, r, tv[, rmax]), ...] around axis. Duplicate points create crisp hard creases."""
        X, Y, Z = basis_from_axis(axis, up_hint=up_hint)
        cols = segs + 1
        base = len(self.verts)
        u0, v0, u1, v1 = uv_rect
        xs = [pt[0] for pt in profile]
        xmin, xspan = min(xs), max(max(xs) - min(xs), 1e-6)
        ph_rad = math.radians(phase_deg)

        local_pts = []
        for item in profile:
            xp, rp = item[0], item[1]
            tv = item[2] if len(item) > 2 and item[2] is not None else (xp - xmin) / xspan
            for j in range(cols):
                th = ph_rad + 2.0 * math.pi * (j / float(segs))
                cth, sth = math.cos(th), math.sin(th)
                pos = vadd(origin, vadd(vmul(X, xp), vadd(vmul(Y, rp * cth), vmul(Z, rp * sth))))
                local_pts.append(pos)
                if uv_mode == "polar":
                    rmax = item[3] if len(item) > 3 else 1.0
                    uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
                    ru, rv = 0.5 * (u1 - u0), 0.5 * (v1 - v0)
                    rr_n = min(1.0, rp / max(rmax, 1e-6))
                    self.st.append((uc + ru * rr_n * cth, vc + rv * rr_n * sth))
                else:
                    uu = u0 + (u1 - u0) * (j / float(segs))
                    vv = v0 + (v1 - v0) * tv
                    self.st.append((uu, vv))

        ring_tris = []
        acc_n = [[0.0, 0.0, 0.0] for _ in local_pts]
        for i in range(len(profile) - 1):
            x_a, r_a = profile[i][0], profile[i][1]
            x_b, r_b = profile[i + 1][0], profile[i + 1][1]
            if abs(x_a - x_b) < 1e-7 and abs(r_a - r_b) < 1e-7:
                continue
            for j in range(segs):
                a = i * cols + j
                b = a + 1
                c = a + cols
                d = c + 1
                if r_a > 1e-6:
                    t1 = (a, b, c)
                    fn1 = vcross(vsub(local_pts[t1[1]], local_pts[t1[0]]), vsub(local_pts[t1[2]], local_pts[t1[0]]))
                    ring_tris.append(t1)
                    for vi in t1:
                        acc_n[vi][0] += fn1[0]
                        acc_n[vi][1] += fn1[1]
                        acc_n[vi][2] += fn1[2]
                if r_b > 1e-6:
                    t2 = (b, d, c)
                    fn2 = vcross(vsub(local_pts[t2[1]], local_pts[t2[0]]), vsub(local_pts[t2[2]], local_pts[t2[0]]))
                    ring_tris.append(t2)
                    for vi in t2:
                        acc_n[vi][0] += fn2[0]
                        acc_n[vi][1] += fn2[1]
                        acc_n[vi][2] += fn2[2]

        for i in range(len(profile)):
            i0 = i * cols
            i1 = i * cols + segs
            sn = vadd(acc_n[i0], acc_n[i1])
            acc_n[i0] = list(sn)
            acc_n[i1] = list(sn)

        self.verts += local_pts
        self.norms += [vnorm(n) for n in acc_n]
        self.tris += [(a + base, b + base, c + base) for (a, b, c) in ring_tris]

    def add_tube(self, pts, radii, segs=10, uv_rect=UV_Q1, cap_start=True, cap_end=True, closed=False):
        """Sweeps circular/elliptical tube along polyline using parallel transport."""
        n = len(pts)
        u0, v0, u1, v1 = uv_rect
        tans = []
        for i in range(n):
            if closed:
                p_prev = pts[(i - 1) % n]
                p_next = pts[(i + 1) % n]
            else:
                p_prev = pts[max(0, i - 1)]
                p_next = pts[min(n - 1, i + 1)]
            tans.append(vnorm(vsub(p_next, p_prev)))

        cols = segs + 1
        rings = []
        _, Y, Z = basis_from_axis(tans[0])
        for i in range(n):
            T = tans[i]
            Y_proj = vsub(Y, vmul(T, vdot(Y, T)))
            if vlen(Y_proj) < 1e-5:
                _, Y, Z = basis_from_axis(T)
            else:
                Y = vnorm(Y_proj)
                Z = vcross(T, Y)
            rad = radii[i] if isinstance(radii, (list, tuple)) and len(radii) == n else radii
            ry, rz = rad if isinstance(rad, tuple) else (rad, rad)
            r_base = len(self.verts)
            rings.append(r_base)
            tv = v0 + (v1 - v0) * (i / float(max(1, n - 1)))
            for j in range(cols):
                th = 2.0 * math.pi * (j / float(segs))
                cth, sth = math.cos(th), math.sin(th)
                pos = vadd(pts[i], vadd(vmul(Y, cth * ry), vmul(Z, sth * rz)))
                nrm = vnorm(vadd(vmul(Y, cth / max(ry, 1e-5)), vmul(Z, sth / max(rz, 1e-5))))
                self.verts.append(pos)
                self.norms.append(nrm)
                self.st.append((u0 + (u1 - u0) * (j / float(segs)), tv))

        seg_count = n if closed else n - 1
        for i in range(seg_count):
            r0 = rings[i]
            r1 = rings[(i + 1) % n]
            for j in range(segs):
                a = r0 + j
                b = a + 1
                c = r1 + j
                d = c + 1
                self.tris += [(a, b, c), (b, d, c)]

        if not closed and cap_start:
            r0 = radii[0][0] if isinstance(radii, (list, tuple)) and len(radii) == n and isinstance(radii[0], tuple) else (radii[0] if isinstance(radii, (list, tuple)) and len(radii) == n else radii)
            if isinstance(r0, tuple):
                r0 = r0[0]
            ic = len(self.verts)
            self.verts.append(vsub(pts[0], vmul(tans[0], r0 * 0.25)))
            self.norms.append(vmul(tans[0], -1.0))
            self.st.append((0.5 * (u0 + u1), v0))
            for j in range(segs):
                self.tris.append((ic, rings[0] + j + 1, rings[0] + j))

        if not closed and cap_end:
            rn = radii[-1] if isinstance(radii, (list, tuple)) and len(radii) == n else radii
            if isinstance(rn, tuple):
                rn = rn[0]
            ic = len(self.verts)
            self.verts.append(vadd(pts[-1], vmul(tans[-1], rn * 0.25)))
            self.norms.append(tans[-1])
            self.st.append((0.5 * (u0 + u1), v1))
            for j in range(segs):
                self.tris.append((ic, rings[-1] + j, rings[-1] + j + 1))

    def add_grid_patch(self, grid_pts, uv_rect=(0.0, 0.0, 1.0, 1.0), flip_n=False):
        """Builds a smooth vertex-grid patch from grid_pts[row][col] = (x,y,z)."""
        nr = len(grid_pts)
        nc = len(grid_pts[0])
        u0, v0, u1, v1 = uv_rect
        base = len(self.verts)
        acc = [[0.0, 0.0, 0.0] for _ in range(nr * nc)]
        tris = []
        for r in range(nr):
            tv = v0 + (v1 - v0) * (r / float(nr - 1))
            for c in range(nc):
                tu = u0 + (u1 - u0) * (c / float(nc - 1))
                self.verts.append(grid_pts[r][c])
                self.st.append((tu, tv))
        for r in range(nr - 1):
            for c in range(nc - 1):
                a = r * nc + c
                b = a + 1
                d = (r + 1) * nc + c
                e = d + 1
                pair = ((a, b, e), (a, e, d)) if not flip_n else ((a, e, b), (a, d, e))
                for t in pair:
                    p0, p1, p2 = self.verts[base + t[0]], self.verts[base + t[1]], self.verts[base + t[2]]
                    fn = vcross(vsub(p1, p0), vsub(p2, p0))
                    tris.append((base + t[0], base + t[1], base + t[2]))
                    for vi in t:
                        acc[vi][0] += fn[0]
                        acc[vi][1] += fn[1]
                        acc[vi][2] += fn[2]
        for n in acc:
            self.norms.append(vnorm(n))
        self.tris += tris


# ---------------------------------------------------------------------------
# Procedural Texture Synthesis (PIL + NumPy)
# ---------------------------------------------------------------------------
def _font(size, bold=True):
    candidates = ["arialbd.ttf", "consolab.ttf", "tahomabd.ttf"] if bold else ["arial.ttf", "consola.ttf"]
    for nm in candidates:
        p = os.path.join(r"C:\Windows\Fonts", nm)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _fbm(h, w, seed=42, octaves=(4, 8, 16, 32)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tw = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh, gw = max(2, h // freq), max(2, w // freq)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(g, mode="F").resize((w, h), Image.Resampling.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tw += amp
    return acc / max(tw, 1e-6)


def _tex_frame(path):
    """1024x1024: Crimson chromoly tubes, glossy brackets, diamond-plate floorpan, drilled brake rotor."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=101, octaves=(4, 8, 16, 32))
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

    # Q1: Crimson-red chromoly powdercoat tube with subtle TIG heat bands at ends
    ux = xx / 511.0
    vy = yy / 511.0
    sheen = 1.0 + 0.14 * np.sin(ux * math.pi)
    weld = np.exp(-((vy - 0.03) ** 2) / 0.0005) + np.exp(-((vy - 0.97) ** 2) / 0.0005)
    flake = 6.0 * noise[:512, :512]
    arr[:512, :512, 0] = np.clip(202.0 * sheen - 42.0 * weld + flake, 20, 245)
    arr[:512, :512, 1] = np.clip(28.0 * sheen + 10.0 * weld + flake * 0.4, 8, 90)
    arr[:512, :512, 2] = np.clip(34.0 * sheen + 18.0 * weld + flake * 0.4, 8, 100)

    # Q2: Deep crimson racing accent / caliper
    arr[:512, 512:, 0] = np.clip(188.0 + 18.0 * np.cos(ux * math.pi * 2.0) + 5.0 * noise[:512, 512:], 30, 235)
    arr[:512, 512:, 1] = np.clip(24.0 + 6.0 * noise[:512, 512:], 8, 70)
    arr[:512, 512:, 2] = np.clip(30.0 + 6.0 * noise[:512, 512:], 8, 75)

    # Q3: Dark anodized diamond-plate floorpan
    cell_x = (xx % 32.0) / 32.0 - 0.5
    cell_y = (yy % 32.0) / 32.0 - 0.5
    ang = ((xx // 32.0 + yy // 32.0) % 2.0) * (math.pi * 0.5) + math.pi * 0.25
    ca, sa = np.cos(ang), np.sin(ang)
    rx = cell_x * ca - cell_y * sa
    ry = cell_x * sa + cell_y * ca
    lug = np.exp(-((rx * 2.4) ** 4 + (ry * 7.5) ** 4) * 3.0)
    fl = 28.0 + 36.0 * lug + 4.0 * noise[512:, :512]
    arr[512:, :512, 0] = np.clip(fl * 1.02, 12, 110)
    arr[512:, :512, 1] = np.clip(fl * 0.99, 12, 110)
    arr[512:, :512, 2] = np.clip(fl * 0.96, 12, 110)

    # Q4: Machined steel / cross-drilled brake rotor
    r_x = (xx - 255.5) / 240.0
    r_y = (yy - 255.5) / 240.0
    rr = np.sqrt(r_x * r_x + r_y * r_y)
    ath = np.arctan2(r_y, r_x)
    brush = 185.0 + 18.0 * np.sin(rr * 110.0) + 12.0 * np.cos(ath * 2.0) + 5.0 * noise[512:, 512:]
    holes = np.zeros_like(rr)
    for k in range(12):
        ha = k * (2.0 * math.pi / 12.0)
        for hr in (0.52, 0.68, 0.84):
            ha2 = ha + (hr - 0.52) * 0.7
            dx = r_x - hr * math.cos(ha2)
            dy = r_y - hr * math.sin(ha2)
            holes += np.exp(-(dx * dx + dy * dy) / 0.00075)
    brush -= 130.0 * np.clip(holes, 0.0, 1.0)
    arr[512:, 512:, 0] = np.clip(brush * 0.98, 16, 235)
    arr[512:, 512:, 1] = np.clip(brush * 0.99, 16, 238)
    arr[512:, 512:, 2] = np.clip(brush * 1.03, 18, 245)

    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)


def _tex_seat(path):
    """1024x1024: Royal-blue quilted diamond-stitched racing pad, bolster leather, carbon shell back."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=202, octaves=(4, 8, 16, 64))
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

    # Q1: Quilted diamond-stitched royal blue pad
    u = (xx + yy) / 64.0
    v = (xx - yy) / 64.0
    du = np.abs(u - np.round(u))
    dv = np.abs(v - np.round(v))
    seam = np.exp(-((np.minimum(du, dv)) ** 2) / 0.0022)
    puff = 1.0 - 0.22 * ((0.5 - du) ** 2 + (0.5 - dv) ** 2)
    stitch_dot = (np.sin(u * 40.0) > 0.75) & (np.minimum(du, dv) < 0.04)
    r = 28.0 * puff - 14.0 * seam + 160.0 * stitch_dot + 4.0 * noise[:512, :512]
    g = 76.0 * puff - 36.0 * seam + 135.0 * stitch_dot + 5.0 * noise[:512, :512]
    b = 216.0 * puff - 85.0 * seam + 30.0 * stitch_dot + 6.0 * noise[:512, :512]
    arr[:512, :512, 0] = np.clip(r, 8, 245)
    arr[:512, :512, 1] = np.clip(g, 20, 240)
    arr[:512, :512, 2] = np.clip(b, 55, 250)

    # Q2: Smooth royal blue side bolster vinyl/suede with subtle gold piping band
    pipe = np.exp(-(((xx / 511.0) - 0.08) ** 2) / 0.0004)
    arr[:512, 512:, 0] = np.clip(26.0 + 185.0 * pipe + 5.0 * noise[:512, 512:], 10, 240)
    arr[:512, 512:, 1] = np.clip(70.0 + 130.0 * pipe + 6.0 * noise[:512, 512:], 24, 220)
    arr[:512, 512:, 2] = np.clip(204.0 - 140.0 * pipe + 7.0 * noise[:512, 512:], 40, 240)

    # Q3: 2x2 Twill carbon-fiber seat shell back
    tx = ((xx // 8.0) % 4.0)
    ty = ((yy // 8.0) % 4.0)
    diag = ((tx + ty) % 4.0) < 2.0
    cf = np.where(diag, 46.0 + 10.0 * np.sin((xx % 8.0) * 0.4), 24.0 + 8.0 * np.sin((yy % 8.0) * 0.4))
    cf += 3.0 * noise[512:, :512]
    arr[512:, :512, 0] = np.clip(cf, 10, 90)
    arr[512:, :512, 1] = np.clip(cf, 10, 92)
    arr[512:, :512, 2] = np.clip(cf * 1.05, 12, 98)

    # Q4: Embroidered headrest emblem patch
    arr[512:, 512:, 0] = 24.0
    arr[512:, 512:, 1] = 66.0
    arr[512:, 512:, 2] = 198.0
    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([552, 562, 984, 964], radius=36, fill=(22, 54, 165), outline=(212, 160, 36), width=8)
    f_big = _font(58, bold=True)
    f_sm = _font(36, bold=True)
    dr.text((768, 720), "BAKERSFIELD", fill=(242, 238, 226), font=f_sm, anchor="mm")
    dr.text((768, 800), "CLASSIC #01", fill=(218, 170, 44), font=f_big, anchor="mm")
    im.save(path, "PNG", optimize=True)


def _tex_steering(path):
    """1024x1024: Perforated black alcantara grip + crimson top band, brushed silver spokes, gold hub, pedals."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=303, octaves=(4, 8, 16, 32))
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

    # Q1: Perforated black grip with crimson/gold 12-o'clock center marker near v=0.25
    perf = (((xx % 12.0) - 6.0) ** 2 + ((yy % 12.0) - 6.0) ** 2) < 5.5
    grip = np.where(perf, 16.0, 34.0) + 4.0 * noise[:512, :512]
    band = np.exp(-(((yy / 511.0) - 0.25) ** 2) / 0.0005)
    arr[:512, :512, 0] = np.clip(grip * (1.0 - band) + 210.0 * band, 8, 235)
    arr[:512, :512, 1] = np.clip(grip * (1.0 - band) + 32.0 * band, 8, 100)
    arr[:512, :512, 2] = np.clip(grip * (1.0 - band) + 36.0 * band, 8, 100)

    # Q2: Brushed silver aluminum spokes & shaft
    sp = 178.0 + 18.0 * np.sin(xx * 0.22) + 8.0 * noise[:512, 512:]
    arr[:512, 512:, 0] = np.clip(sp * 0.96, 60, 230)
    arr[:512, 512:, 1] = np.clip(sp * 0.99, 60, 235)
    arr[:512, 512:, 2] = np.clip(sp * 1.04, 65, 245)

    # Q3: Brushed gold steering hub + black center
    r_x = (xx - 255.5) / 240.0
    r_y = (yy - 255.5) / 240.0
    rr = np.sqrt(r_x * r_x + r_y * r_y)
    gold = 1.0 + 0.14 * np.cos(np.arctan2(r_y, r_x) * 2.0) + 0.06 * noise[512:, :512]
    center = rr < 0.35
    arr[512:, :512, 0] = np.clip(np.where(center, 28.0, 212.0 * gold), 12, 248)
    arr[512:, :512, 1] = np.clip(np.where(center, 25.0, 160.0 * gold), 12, 210)
    arr[512:, :512, 2] = np.clip(np.where(center, 24.0, 42.0 * gold), 10, 95)

    # Q4: Ribbed rubber pedal pad
    rib = 24.0 + 26.0 * (np.sin(yy * 0.32) > 0.0).astype(np.float32) + 4.0 * noise[512:, 512:]
    arr[512:, 512:, :] = np.clip(rib[..., None], 10, 85)

    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)


def _tex_engine(path):
    """1024x1024: Brushed aluminum block/fins, black blower shroud, red fuel tank/gold cap, chain/sprocket."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=404, octaves=(4, 8, 16, 32))
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

    # Q1: Brushed cast-aluminum block & machined cooling fins
    fin_stripe = 18.0 * np.sin(yy * 0.25)
    al = 186.0 + fin_stripe + 12.0 * noise[:512, :512]
    arr[:512, :512, 0] = np.clip(al * 0.99, 60, 238)
    arr[:512, :512, 1] = np.clip(al * 0.99, 60, 238)
    arr[:512, :512, 2] = np.clip(al * 1.02, 65, 244)

    # Q2: Black blower shroud + stamped vent louvers
    sh = 30.0 + 6.0 * noise[:512, 512:]
    r_x = (xx - 255.5) / 220.0
    r_y = (yy - 255.5) / 220.0
    rr = np.sqrt(r_x * r_x + r_y * r_y)
    ang = np.arctan2(r_y, r_x)
    louvers = ((rr > 0.32) & (rr < 0.78) & (np.sin(ang * 14.0) > 0.35)).astype(np.float32)
    sh = sh - 18.0 * louvers
    arr[:512, 512:, 0] = np.clip(sh, 6, 80)
    arr[:512, 512:, 1] = np.clip(sh, 6, 80)
    arr[:512, 512:, 2] = np.clip(sh, 8, 84)

    # Q3: Crimson fuel tank & knurled gold cap band
    cap_zone = (yy > 380)
    tk_r = np.where(cap_zone, 214.0, 185.0) + 10.0 * noise[512:, :512]
    tk_g = np.where(cap_zone, 162.0, 26.0) + 5.0 * noise[512:, :512]
    tk_b = np.where(cap_zone, 38.0, 32.0) + 5.0 * noise[512:, :512]
    arr[512:, :512, 0] = np.clip(tk_r, 15, 245)
    arr[512:, :512, 1] = np.clip(tk_g, 10, 210)
    arr[512:, :512, 2] = np.clip(tk_b, 10, 95)

    # Q4: Oiled steel chain / sprocket & gold intake stack
    gold_zone = (yy < 220)
    ch = 72.0 + 28.0 * np.sin(xx * 0.45) * np.sin(yy * 0.45) + 8.0 * noise[512:, 512:]
    arr[512:, 512:, 0] = np.clip(np.where(gold_zone, 212.0, ch), 20, 240)
    arr[512:, 512:, 1] = np.clip(np.where(gold_zone, 165.0, ch * 0.96), 20, 210)
    arr[512:, 512:, 2] = np.clip(np.where(gold_zone, 46.0, ch * 0.92), 15, 130)

    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)


def _tex_exhaust(path):
    """1024x1024: Copper/gold cylindrical muffler, heat-blued header, dark soot tip, stainless clamp."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=505, octaves=(4, 8, 16, 32))
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

    # Q1: Copper/gold muffler canister with subtle heat-blued inlet end
    vy = yy / 511.0
    ux = xx / 511.0
    brush = 1.0 + 0.08 * np.sin(ux * 140.0) + 0.05 * noise[:512, :512]
    heat_blue = np.exp(-((vy - 0.12) ** 2) / 0.012)
    r = (212.0 * (1.0 - 0.35 * heat_blue) + 95.0 * heat_blue) * brush
    g = (146.0 * (1.0 - 0.48 * heat_blue) + 80.0 * heat_blue) * brush
    b = (42.0 * (1.0 - 0.50 * heat_blue) + 150.0 * heat_blue) * brush
    arr[:512, :512, 0] = np.clip(r, 25, 248)
    arr[:512, :512, 1] = np.clip(g, 20, 215)
    arr[:512, :512, 2] = np.clip(b, 15, 210)

    # Q2: Heat-tempered titanium/copper header pipe
    vy2 = yy / 511.0
    hb = np.sin(vy2 * math.pi)
    arr[:512, 512:, 0] = np.clip(182.0 - 25.0 * hb + 10.0 * noise[:512, 512:], 40, 235)
    arr[:512, 512:, 1] = np.clip(134.0 - 30.0 * hb + 8.0 * noise[:512, 512:], 30, 200)
    arr[:512, 512:, 2] = np.clip(88.0 + 75.0 * hb + 8.0 * noise[:512, 512:], 25, 210)

    # Q3: Dark soot-blackened tailpipe tip
    soot = 24.0 + 12.0 * noise[512:, :512]
    arr[512:, :512, 0] = np.clip(soot * 1.1, 8, 65)
    arr[512:, :512, 1] = np.clip(soot * 0.98, 8, 55)
    arr[512:, :512, 2] = np.clip(soot * 0.90, 8, 50)

    # Q4: Stainless steel retaining strap
    st = 198.0 + 16.0 * np.cos(xx * 0.08) + 6.0 * noise[512:, 512:]
    arr[512:, 512:, 0] = np.clip(st * 0.98, 80, 240)
    arr[512:, 512:, 1] = np.clip(st * 0.99, 80, 242)
    arr[512:, 512:, 2] = np.clip(st * 1.03, 85, 248)

    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)


def _tex_nose(path):
    """1024x1024: Crimson front number plate with crisp Quake 'Q' emblem, #01 badge, gold/white stripes."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=606, octaves=(4, 8, 16, 32))

    # Rich metallic crimson background
    arr[:, :, 0] = np.clip(198.0 + 6.0 * noise, 20, 240)
    arr[:, :, 1] = np.clip(24.0 + 3.0 * noise, 8, 65)
    arr[:, :, 2] = np.clip(30.0 + 3.0 * noise, 8, 70)

    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)

    # Twin ivory-white & brushed-gold vertical racing stripes framing the emblem
    dr.rectangle([118, 0, 174, 1024], fill=(242, 236, 224))
    dr.rectangle([184, 0, 206, 1024], fill=(214, 164, 38))
    dr.rectangle([850, 0, 906, 1024], fill=(242, 236, 224))
    dr.rectangle([818, 0, 840, 1024], fill=(214, 164, 38))

    # Dark charcoal circular shield badge behind the Quake 'Q'
    cx, cy = 512, 540
    dr.ellipse([cx - 255, cy - 255, cx + 255, cy + 255], fill=(24, 22, 22), outline=(218, 168, 42), width=14)
    dr.ellipse([cx - 226, cy - 226, cx + 226, cy + 226], fill=(32, 28, 28), outline=(145, 24, 28), width=6)

    # Vector-rendered Quake 'Q' emblem (tapered horseshoe crescent + central piercing nail)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx - cx) / 185.0
    dy = (yy - cy) / 185.0
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)  # -pi..pi, -pi/2 is top (up)

    # Tapered Quake ring: thickest at bottom (+pi/2), opening at top (-pi/2)
    # Angular distance from top (-pi/2)
    ang_from_top = np.abs(np.arctan2(np.sin(ang + math.pi * 0.5), np.cos(ang + math.pi * 0.5)))
    # Open gap at top for ang_from_top < 0.36 rad; crescent thickens smoothly toward bottom
    ring_open = ang_from_top > 0.36
    # Outer radius ~ 0.94, inner radius shifts upward (crescent offset) & tapers to horns at top
    r_outer = 0.92 - 0.10 * np.exp(-((ang_from_top - 0.36) ** 2) / 0.14)
    r_inner_c = np.sqrt((dx * 1.04) ** 2 + ((dy + 0.14) * 1.02) ** 2)
    ring_mask = ring_open & (rr <= r_outer) & (r_inner_c >= 0.58)

    # Vertical Quake nail/blade piercing through bottom center
    nail_shaft = (np.abs(dx) <= np.where(dy > 0.25, np.maximum(0.035, 0.14 * (1.18 - dy) / 0.93), 0.14)) & (dy >= -0.06) & (dy <= 1.18)
    nail_head = (np.abs(dx) <= 0.24) & (dy >= -0.16) & (dy <= 0.05)
    nail_barb = (np.abs(dx) <= 0.19) & (dy >= 0.44) & (dy <= 0.62)
    q_mask = ring_mask | nail_shaft | nail_head | nail_barb

    # Beveled metallic gold shading across the 'Q'
    im_arr = np.asarray(im, dtype=np.float32)
    bevel = np.clip(0.88 + 0.22 * (-dx * 0.5 - dy * 0.6) + 0.08 * np.sin(rr * 22.0), 0.65, 1.18)
    # Dark outline around Q
    from PIL import ImageFilter
    q_img = Image.fromarray((q_mask.astype(np.uint8) * 255), mode="L")
    q_dil = np.asarray(q_img.filter(ImageFilter.MaxFilter(9)), dtype=np.float32) / 255.0
    q_shd = np.clip(q_dil - q_mask.astype(np.float32), 0.0, 1.0)

    im_arr[:, :, 0] = im_arr[:, :, 0] * (1.0 - 0.75 * q_shd)
    im_arr[:, :, 1] = im_arr[:, :, 1] * (1.0 - 0.75 * q_shd)
    im_arr[:, :, 2] = im_arr[:, :, 2] * (1.0 - 0.75 * q_shd)

    im_arr[q_mask, 0] = np.clip(236.0 * bevel[q_mask], 30, 255)
    im_arr[q_mask, 1] = np.clip(182.0 * bevel[q_mask], 20, 230)
    im_arr[q_mask, 2] = np.clip(48.0 * bevel[q_mask], 10, 110)

    im2 = Image.fromarray(im_arr.astype(np.uint8), mode="RGB")
    dr2 = ImageDraw.Draw(im2)
    f_num = _font(112, bold=True)
    f_sub = _font(44, bold=True)
    dr2.text((512, 170), "01", fill=(246, 240, 226), font=f_num, anchor="mm", stroke_width=5, stroke_fill=(24, 20, 20))
    dr2.text((512, 895), "BAKERSFIELD", fill=(242, 236, 222), font=f_sub, anchor="mm", stroke_width=3, stroke_fill=(20, 18, 18))
    im2.save(path, "PNG", optimize=True)


def _tex_wheel(path):
    """1024x1024: Racing slick rubber tread, sidewall w/ stencil, brushed-gold 5-bolt dish hub, chrome hardware."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=707, octaves=(4, 8, 16, 32))
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

    # Q1: Matte-black racing slick rubber tread with center mold line & track scrub grain
    ux = xx / 511.0
    mold_seam = np.exp(-((ux - 0.5) ** 2) / 0.00012)
    scrub = 8.0 * np.exp(-((ux - 0.5) ** 2) / 0.14)
    rub = 26.0 + scrub - 6.0 * mold_seam + 5.0 * noise[:512, :512]
    arr[:512, :512, 0] = np.clip(rub * 1.00, 10, 65)
    arr[:512, :512, 1] = np.clip(rub * 0.99, 10, 65)
    arr[:512, :512, 2] = np.clip(rub * 1.02, 10, 68)

    # Q2: Polar tire sidewall with subtle gold pin-stripe ring
    r_x = (xx - 255.5) / 245.0
    r_y = (yy - 255.5) / 245.0
    rr = np.sqrt(r_x * r_x + r_y * r_y)
    sw = 25.0 + 7.0 * np.exp(-((rr - 0.78) ** 2) / 0.01) + 3.5 * noise[:512, 512:]
    stripe = np.exp(-((rr - 0.77) ** 2) / 0.00025)
    arr[:512, 512:, 0] = np.clip(sw + 165.0 * stripe, 10, 215)
    arr[:512, 512:, 1] = np.clip(sw + 125.0 * stripe, 10, 175)
    arr[:512, 512:, 2] = np.clip(sw + 24.0 * stripe, 10, 80)

    # Q3: Brushed-gold 5-bolt dish hub (polar)
    ang = np.arctan2(r_y, r_x)
    aniso = 1.0 + 0.16 * np.cos(ang * 2.0 + 0.4) + 0.06 * np.sin(rr * 90.0) + 0.05 * noise[512:, :512]
    dish = 1.0 - 0.18 * np.exp(-((rr - 0.55) ** 2) / 0.06)
    lip_hi = np.exp(-((rr - 0.90) ** 2) / 0.0012)
    pockets = np.zeros_like(rr)
    for k in range(5):
        ba = k * (2.0 * math.pi / 5.0)
        dx = r_x - 0.42 * math.cos(ba)
        dy = r_y - 0.42 * math.sin(ba)
        pockets += np.exp(-(dx * dx + dy * dy) / 0.0045)
    pockets = np.clip(pockets, 0.0, 1.0)
    center_ring = np.exp(-((rr - 0.25) ** 2) / 0.0008)
    g_r = (214.0 * dish + 28.0 * lip_hi) * aniso * (1.0 - 0.55 * pockets) - 70.0 * center_ring
    g_g = (162.0 * dish + 24.0 * lip_hi) * aniso * (1.0 - 0.58 * pockets) - 55.0 * center_ring
    g_b = (42.0 * dish + 16.0 * lip_hi) * aniso * (1.0 - 0.60 * pockets) - 18.0 * center_ring
    arr[512:, :512, 0] = np.clip(g_r, 18, 252)
    arr[512:, :512, 1] = np.clip(g_g, 14, 215)
    arr[512:, :512, 2] = np.clip(g_b, 10, 95)

    # Q4: Satin gold inner rim barrel (left half) + bright silver lug hardware (right half)
    hw_mask = xx > 256
    gold_in = 175.0 + 12.0 * noise[512:, 512:]
    silv = 205.0 + 18.0 * np.sin(yy * 0.15) + 6.0 * noise[512:, 512:]
    arr[512:, 512:, 0] = np.clip(np.where(hw_mask, silv * 0.98, gold_in), 20, 248)
    arr[512:, 512:, 1] = np.clip(np.where(hw_mask, silv * 0.99, gold_in * 0.76), 20, 248)
    arr[512:, 512:, 2] = np.clip(np.where(hw_mask, silv * 1.03, gold_in * 0.22), 18, 252)

    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)


def _tex_flame(path):
    """512x512 RGBA: Outer flame plume, inner hot core, explosion fireball outer & core."""
    H = W = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    noise = _fbm(H, W, seed=808, octaves=(4, 8, 16, 32))
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    u = xx / 255.0
    v = yy / 255.0

    # Q1: Outer exhaust flame plume (base at v=0, tip at v=1)
    edge_y = 1.0 - np.abs(2.0 * u - 1.0) ** 1.6
    streak = 0.78 + 0.22 * np.sin(u * 26.0 + v * 14.0 + noise[:256, :256] * 3.0)
    intensity = np.clip((1.0 - v * 0.78) * edge_y * streak, 0.0, 1.0)
    rgba[:256, :256, 0] = np.clip(255.0 * (intensity ** 0.45), 0, 255)
    rgba[:256, :256, 1] = np.clip(165.0 * (intensity ** 1.15), 0, 255)
    rgba[:256, :256, 2] = np.clip(45.0 * (intensity ** 2.1), 0, 255)
    rgba[:256, :256, 3] = np.clip(255.0 * (intensity ** 0.65), 0, 255)

    # Q2: Inner plasma core (white-yellow-gold)
    core_e = np.exp(-(((2.0 * u - 1.0) * 1.35) ** 2)) * np.clip(1.0 - v * 0.72, 0.0, 1.0)
    core_i = np.clip(core_e * (0.88 + 0.12 * np.sin(v * 22.0)), 0.0, 1.0)
    rgba[:256, 256:, 0] = np.clip(255.0 * (core_i ** 0.35), 0, 255)
    rgba[:256, 256:, 1] = np.clip(245.0 * (core_i ** 0.55), 0, 255)
    rgba[:256, 256:, 2] = np.clip(195.0 * (core_i ** 1.1), 0, 255)
    rgba[:256, 256:, 3] = np.clip(255.0 * (core_i ** 0.50), 0, 255)

    # Q3 & Q4: Radial fireball outer & blast core
    rx = (xx - 127.5) / 118.0
    ry = (yy - 127.5) / 118.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang = np.arctan2(ry, rx)
    turb = 1.0 + 0.20 * np.sin(ang * 7.0 + rr * 4.0) + 0.16 * noise[256:, :256]
    fb = np.clip((1.0 - rr * 0.92 / turb), 0.0, 1.0)
    rgba[256:, :256, 0] = np.clip(255.0 * (fb ** 0.4), 0, 255)
    rgba[256:, :256, 1] = np.clip(145.0 * (fb ** 1.2), 0, 255)
    rgba[256:, :256, 2] = np.clip(35.0 * (fb ** 2.4), 0, 255)
    rgba[256:, :256, 3] = np.clip(245.0 * (fb ** 0.7), 0, 255)

    fc = np.clip(1.0 - rr * 1.1, 0.0, 1.0)
    rgba[256:, 256:, 0] = 255.0
    rgba[256:, 256:, 1] = np.clip(250.0 * (fc ** 0.4), 0, 255)
    rgba[256:, 256:, 2] = np.clip(210.0 * (fc ** 0.8), 0, 255)
    rgba[256:, 256:, 3] = np.clip(255.0 * (fc ** 0.55), 0, 255)

    Image.fromarray(rgba.astype(np.uint8), mode="RGBA").save(path, "PNG", optimize=True)


def build_all_textures():
    os.makedirs(PROGS_DIR, exist_ok=True)
    _tex_frame(os.path.join(PROGS_DIR, "gk1_frame.png"))
    _tex_seat(os.path.join(PROGS_DIR, "gk1_seat.png"))
    _tex_steering(os.path.join(PROGS_DIR, "gk1_steering.png"))
    _tex_engine(os.path.join(PROGS_DIR, "gk1_engine.png"))
    _tex_exhaust(os.path.join(PROGS_DIR, "gk1_exhaust.png"))
    _tex_nose(os.path.join(PROGS_DIR, "gk1_nose.png"))
    _tex_wheel(os.path.join(PROGS_DIR, "gk1_wheel.png"))
    _tex_flame(os.path.join(PROGS_DIR, "gk1_flame.png"))


# ---------------------------------------------------------------------------
# 3D Sub-Assembly Builders
# ---------------------------------------------------------------------------
def build_chassis():
    """Crimson chromoly tubular frame + curved double-rail side-pods + bumpers + axles + floorpan."""
    ch = MeshPart("chassis")

    # 1) Main longitudinal lower chassis rails (left & right, cockpit |Y| >= 13.5 clear!)
    for sgn in (-1.0, +1.0):
        main_ctrl = [
            (-40.5, sgn * 10.6, 6.4),
            (-33.5, sgn * 11.6, 5.6),
            (-25.0, sgn * 12.6, 5.6),
            (-13.5, sgn * 14.6, 5.6),
            (0.0,   sgn * 14.8, 5.6),
            (12.5,  sgn * 14.4, 5.6),
            (21.5,  sgn * 11.2, 6.2),
            (31.5,  sgn * 8.6,  7.0),
            (41.0,  sgn * 7.2,  7.6),
        ]
        ch.add_tube(catmull_rom_chain(main_ctrl, 3), 0.95, segs=10, uv_rect=UV_FRAME_TUBE)

    # 2) Front perimeter tubular bumper (dual-tier wrap-around loop + 4 vertical stanchions)
    front_low = [
        (33.5, -8.4, 7.1),
        (42.2, -7.0, 7.6),
        (45.8, -4.4, 8.1),
        (46.8,  0.0, 8.3),
        (45.8,  4.4, 8.1),
        (42.2,  7.0, 7.6),
        (33.5,  8.4, 7.1),
    ]
    front_hi = [
        (30.5, -9.2, 10.4),
        (40.2, -7.4, 11.3),
        (44.8, -4.4, 11.8),
        (45.9,  0.0, 12.0),
        (44.8,  4.4, 11.8),
        (40.2,  7.4, 11.3),
        (30.5,  9.2, 10.4),
    ]
    ch.add_tube(catmull_rom_chain(front_low, 3), 0.88, segs=10, uv_rect=UV_FRAME_TUBE)
    ch.add_tube(catmull_rom_chain(front_hi, 3), 0.82, segs=10, uv_rect=UV_FRAME_TUBE)
    for y_st, x_lo, x_hi, z_lo, z_hi in (
        (-7.2, 41.2, 40.0, 7.6, 11.3),
        (+7.2, 41.2, 40.0, 7.6, 11.3),
        (-3.2, 46.1, 45.2, 8.2, 11.9),
        (+3.2, 46.1, 45.2, 8.2, 11.9),
    ):
        ch.add_tube([(x_lo, y_st, z_lo), (x_hi, y_st, z_hi)], 0.68, segs=8, uv_rect=UV_FRAME_TUBE)

    # 3) Curved double-rail side-pod nerf bars (outside |Y| >= 14.5 so cockpit |Y| <= 13.5 is wide open)
    for sgn in (-1.0, +1.0):
        pod_low = [
            (12.2,  sgn * 14.4, 5.7),
            (9.5,   sgn * 20.4, 6.2),
            (2.0,   sgn * 22.4, 6.4),
            (-6.5,  sgn * 22.0, 6.4),
            (-11.5, sgn * 19.6, 6.2),
            (-13.5, sgn * 14.6, 5.7),
        ]
        pod_hi = [
            (11.4,  sgn * 14.6, 7.2),
            (8.8,   sgn * 21.0, 10.2),
            (1.0,   sgn * 23.0, 10.8),
            (-7.0,  sgn * 22.5, 10.5),
            (-11.5, sgn * 20.0, 9.8),
            (-13.2, sgn * 14.7, 7.0),
        ]
        ch.add_tube(catmull_rom_chain(pod_low, 3), 0.80, segs=10, uv_rect=UV_FRAME_TUBE)
        ch.add_tube(catmull_rom_chain(pod_hi, 3), 0.78, segs=10, uv_rect=UV_FRAME_TUBE)
        # Side-pod vertical standoffs
        for xp, yp, zlo, zhi in ((5.0, sgn * 22.0, 6.3, 10.6), (-4.0, sgn * 22.2, 6.4, 10.6)):
            ch.add_tube([(xp, yp, zlo), (xp, yp * 1.02, zhi)], 0.62, segs=8, uv_rect=UV_FRAME_TUBE)

    # 4) Rear tubular bumper guard + rear engine cradle crossbars
    rear_low = [
        (-35.5, -11.4, 5.8),
        (-42.5, -10.2, 6.8),
        (-44.6, -5.8,  7.4),
        (-45.0,  0.0,  7.6),
        (-44.6,  5.8,  7.4),
        (-42.5, 10.2,  6.8),
        (-35.5, 11.4,  5.8),
    ]
    rear_hi = [
        (-33.5, -11.8, 10.2),
        (-41.5, -10.8, 12.6),
        (-44.0, -6.0,  13.4),
        (-44.4,  0.0,  13.6),
        (-44.0,  6.0,  13.4),
        (-41.5, 10.8,  12.6),
        (-33.5, 11.8,  10.2),
    ]
    ch.add_tube(catmull_rom_chain(rear_low, 3), 0.85, segs=10, uv_rect=UV_FRAME_TUBE)
    ch.add_tube(catmull_rom_chain(rear_hi, 3), 0.78, segs=10, uv_rect=UV_FRAME_TUBE)
    for y_st in (-10.5, -5.2, 5.2, 10.5):
        x_lo = -42.4 if abs(y_st) > 8 else -44.6
        ch.add_tube([(x_lo, y_st, 7.1), (x_lo + 0.6, y_st, 13.0)], 0.64, segs=8, uv_rect=UV_FRAME_TUBE)

    # 5) Chassis crossmembers & front axle beam + spindles + steering hoop
    for x_cb, y_span, z_cb in ((-34.0, 11.5, 5.6), (-20.0, 13.5, 5.6), (-9.0, 14.5, 5.6), (8.0, 14.5, 5.6), (32.0, 8.6, 7.0)):
        ch.add_tube([(x_cb, -y_span, z_cb), (x_cb, y_span, z_cb)], 0.76, segs=8, uv_rect=UV_FRAME_TUBE)

    # Front axle crossbeam + kingpin yokes & wheel spindles
    front_beam = [
        (25.0, -18.5, 9.5),
        (25.0, -14.5, 7.8),
        (25.0, -9.8,  6.5),
        (25.0,  0.0,  6.5),
        (25.0,  9.8,  6.5),
        (25.0,  14.5, 7.8),
        (25.0,  18.5, 9.5),
    ]
    ch.add_tube(catmull_rom_chain(front_beam, 2), 0.85, segs=10, uv_rect=UV_FRAME_TUBE)
    for sgn in (-1.0, +1.0):
        # Kingpin C-bracket & front wheel stub axle
        ch.add_tube([(25.0, sgn * 18.2, 7.4), (25.0, sgn * 18.2, 11.6)], 0.82, segs=8, uv_rect=UV_FRAME_ACCENT)
        ch.add_tube([(25.0, sgn * 18.2, 9.5), (25.0, sgn * 23.5, 9.5)], 0.72, segs=8, uv_rect=UV_FRAME_STEEL)
        # Steering tie-rod
        ch.add_tube([(22.5, sgn * 1.2, 8.8), (23.3, sgn * 17.8, 9.5)], 0.36, segs=6, uv_rect=UV_FRAME_STEEL)

    # Steering A-frame hoop (open footwell below Z=14 for |Y| <= 9.5)
    hoop = [
        (24.5, -9.5,  6.8),
        (23.5, -5.2, 16.5),
        (17.5, -2.0, 20.8),
        (16.6,  0.0, 21.4),
        (17.5,  2.0, 20.8),
        (23.5,  5.2, 16.5),
        (24.5,  9.5,  6.8),
    ]
    ch.add_tube(catmull_rom_chain(hoop, 2), 0.76, segs=8, uv_rect=UV_FRAME_TUBE)

    # 6) Live rear axle shaft + 3 bearing hangers + cross-drilled brake rotor + caliper
    ch.add_tube([(-25.0, -25.0, 11.0), (-25.0, 25.0, 11.0)], 0.92, segs=12, uv_rect=UV_FRAME_STEEL)
    for yb in (-12.5, 0.0, 12.5):
        ch.add_tube([(-25.0, yb, 5.6), (-25.0, yb, 11.0)], 0.72, segs=8, uv_rect=UV_FRAME_ACCENT)
        ch.add_chamfer_box(-26.8, -23.2, yb - 0.9, yb + 0.9, 9.2, 12.8, ch=0.35, uv_rect=UV_FRAME_ACCENT)

    # Ventilated steel brake disc on rear axle (Y = +8.5)
    ch.add_lathe(
        (-25.0, 8.5, 11.0), (0.0, 1.0, 0.0),
        [(-0.35, 1.0, 0.0), (-0.35, 5.8, 0.95), (+0.35, 5.8, 0.95), (+0.35, 1.0, 0.0)],
        segs=20, uv_mode="polar", uv_rect=UV_FRAME_STEEL,
    )
    ch.add_chamfer_box(-30.5, -26.2, 7.1, 9.9, 9.2, 13.0, ch=0.35, uv_rect=UV_FRAME_ACCENT)

    # 7) Dark anodized aluminum floorpan (tapered chamfered plates under seat & footwell)
    ch.add_chamfer_box(-16.0, 13.5, -12.8, 12.8, 4.6, 5.2, ch=0.18, uv_rect=UV_FRAME_FLOOR)
    ch.add_chamfer_box(13.5, 29.0, -8.4, 8.4, 4.7, 5.3, ch=0.18, uv_rect=UV_FRAME_FLOOR)
    return ch


def build_seat():
    """Royal-blue contoured racing bucket seat with quilted pan, raised side bolsters & carbon shell."""
    st = MeshPart("seat")

    # Outer sculpted bucket shell + inner quilted royal-blue padded seat pan & backrest
    # Profile stations (s from front lip -> seat pan -> lumbar -> upper backrest)
    # Seat pan top sits cleanly at X = -9.0, Y = 0.0, Z = 9.5.
    # Inner clear width wi >= 11.3 keeps |Y| < 11.0 x Z=[11.0..38.0] torso box 100% clear,
    # while bolsters sit cleanly inside the |Y|=13.65 chassis rails!
    stations = [
        # (x, z_floor, bolster_h, half_w_inner, half_w_outer, tilt_x_back)
        (-2.0,   7.8, 1.4, 11.2, 12.6, 0.0),   # front thigh waterfall lip
        (-5.5,   9.4, 2.2, 11.3, 12.9, 0.0),   # front pan
        (-9.0,   9.5, 2.6, 11.4, 13.1, 0.0),   # center seat pan (X=-9, Z=9.5!)
        (-13.2,  9.5, 3.0, 11.4, 13.2, 0.0),   # rear pan / hip pocket
        (-16.6, 12.8, 3.4, 11.3, 13.2, 2.0),   # lower lumbar (behind X=-16.5!)
        (-18.6, 17.6, 3.6, 11.3, 13.2, 2.8),   # mid-back rib bolster
        (-20.4, 22.2, 2.8, 11.2, 12.9, 2.0),   # upper shoulder
        (-21.8, 25.8, 1.2, 9.6,  11.6, 0.6),   # top headrest lip (open overhead!)
    ]

    # Build inner royal-blue padded cushion grid (rows=stations, cols across Y)
    y_t = [-1.0, -0.78, -0.58, -0.30, 0.0, 0.30, 0.58, 0.78, 1.0]
    inner_grid = []
    outer_grid = []
    for x, z, bh, wi, wo, bx in stations:
        row_in = []
        row_out = []
        is_back = z > 11.0
        for t in y_t:
            at = abs(t)
            sgn = -1.0 if t < 0 else (1.0 if t > 0 else 0.0)
            if at <= 0.58:
                y = sgn * (at / 0.58) * wi
                dz = 0.0
                dx = 0.0
            else:
                bt = (at - 0.58) / 0.42
                y = sgn * (wi + bt * (wo - wi))
                dz = math.sin(bt * math.pi * 0.75) * bh * (0.35 if is_back else 1.0)
                dx = math.sin(bt * math.pi * 0.75) * (bx if is_back else 0.3)
            row_in.append((x + dx, y, z + dz))
            # Outer shell offset downward/backward (keeping outer Y <= 13.35 inside chassis rails)
            y_out = y + sgn * 0.18 if abs(y) > 0.1 else 0.0
            row_out.append((x + dx - (1.3 if is_back else 0.3), y_out, z + dz - (0.3 if is_back else 1.3)))
        inner_grid.append(row_in)
        outer_grid.append(row_out)

    st.add_grid_patch(inner_grid, uv_rect=UV_SEAT_QUILT, flip_n=False)
    st.add_grid_patch(outer_grid, uv_rect=UV_SEAT_CARBON, flip_n=True)

    # Stitch rim perimeter connecting inner_grid edge to outer_grid edge (bolster piping)
    nr, nc = len(stations), len(y_t)
    for r in range(nr - 1):
        # Left outer bolster rim (col = nc - 1, facing +Y/outward) & right outer bolster rim (col = 0, facing -Y/outward)
        st.add_quad(
            inner_grid[r][nc - 1], outer_grid[r][nc - 1],
            outer_grid[r + 1][nc - 1], inner_grid[r + 1][nc - 1],
            (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[1]), (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[1]),
            (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[3]), (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[3]),
        )
        st.add_quad(
            inner_grid[r][0], inner_grid[r + 1][0],
            outer_grid[r + 1][0], outer_grid[r][0],
            (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[1]), (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[1]),
            (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[3]), (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[3]),
        )
    # Front lip & top headrest closure
    for c in range(nc - 1):
        st.add_quad(
            inner_grid[0][c], inner_grid[0][c + 1], outer_grid[0][c + 1], outer_grid[0][c],
            (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[1]), (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[1]),
            (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[3]), (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[3]),
        )
        st.add_quad(
            inner_grid[nr - 1][c], outer_grid[nr - 1][c],
            outer_grid[nr - 1][c + 1], inner_grid[nr - 1][c + 1],
            (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[1]), (UV_SEAT_BOLSTER[0], UV_SEAT_BOLSTER[3]),
            (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[3]), (UV_SEAT_BOLSTER[2], UV_SEAT_BOLSTER[1]),
        )

    # Under-seat mounting struts to floorpan
    for sgn in (-1.0, +1.0):
        st.add_chamfer_box(-13.5, -5.0, sgn * 6.2 - 0.7, sgn * 6.2 + 0.7, 5.2, 8.8, ch=0.2, uv_rect=UV_SEAT_CARBON)
    return st


def build_steering():
    """Angled steering shaft + machined hub + 3-spoke black/silver racing wheel at (13, 0, 24)."""
    sw = MeshPart("steering")
    cx, cy, cz = STEER_POS["x"], STEER_POS["y"], STEER_POS["z"]
    base_pt = (23.0, 0.0, 9.2)
    top_pt = (cx, cy, cz)
    axis = vnorm(vsub(top_pt, base_pt))  # (-0.568, 0, +0.823) pointing toward driver

    # 1) Steering shaft + lower U-joint + upper bearing collar
    sw.add_tube([base_pt, top_pt], 0.70, segs=10, uv_rect=UV_STEER_SPOKE)
    sw.add_lathe(base_pt, axis, [(-1.0, 0.0, 0.0), (-1.0, 1.3, 0.2), (1.4, 1.3, 0.8), (1.4, 0.0, 1.0)], segs=12, uv_rect=UV_STEER_SPOKE)
    collar_pt = vlerp(base_pt, top_pt, 0.68)
    sw.add_lathe(collar_pt, axis, [(-1.2, 0.0, 0.0), (-1.2, 1.45, 0.2), (1.2, 1.45, 0.8), (1.2, 0.0, 1.0)], segs=14, uv_rect=UV_STEER_HUB)

    # 2) Steering wheel rim + 3 spokes + anodized gold hub in wheel-local frame aligned to axis
    X_w, Y_w, Z_w = basis_from_axis(axis, up_hint=(0.0, 0.0, 1.0))
    # Note: with axis=(-0.57, 0, +0.82), Y_w points along -Y (right), Z_w points upward/forward
    wheel_r = 6.3
    n_rim = 28
    rim_pts = []
    for i in range(n_rim):
        th = 2.0 * math.pi * (i / float(n_rim))
        p_rim = vadd(top_pt, vadd(vmul(Y_w, wheel_r * math.cos(th)), vmul(Z_w, wheel_r * math.sin(th))))
        rim_pts.append(p_rim)
    # Shift rim_pts so top 12-o'clock marker (Z_w) aligns with v ~ 0.25 on UV_STEER_GRIP
    sw.add_tube(rim_pts, 0.78, segs=10, uv_rect=UV_STEER_GRIP, closed=True)

    # 3 chamfered spokes (10-o'clock, 2-o'clock, 6-o'clock)
    for sp_deg in (25.0, 155.0, 270.0):
        sr = math.radians(sp_deg)
        dir_r = vadd(vmul(Y_w, math.cos(sr)), vmul(Z_w, math.sin(sr)))
        p_in = vadd(top_pt, vmul(dir_r, 1.4))
        p_out = vadd(top_pt, vmul(dir_r, wheel_r - 0.5))
        sw.add_tube([p_in, p_out], (0.62, 0.28), segs=6, uv_rect=UV_STEER_SPOKE)

    # Machined gold central hub & black horn cap
    sw.add_lathe(
        top_pt, axis,
        [
            (-1.2, 0.0, 0.0, 2.0),
            (-1.2, 1.85, 0.9, 2.0),
            (0.45, 2.05, 1.0, 2.05),
            (0.65, 1.80, 0.88, 2.05),
            (0.70, 0.0, 0.0, 2.05),
        ],
        segs=18, uv_mode="polar", uv_rect=UV_STEER_HUB,
    )
    return sw


def build_nose_plate():
    """Curved aerodynamic front number plate with crisp Quake 'Q' emblem + #01 racing stripes."""
    np_mesh = MeshPart("nose_plate")

    # 9 rows (top -> bottom) x 9 cols (-Y -> +Y) so curved fairing shades smoothly
    rows_xz = [
        (22.5, 20.6, 7.2, 1.2),
        (24.5, 19.5, 7.5, 1.4),
        (26.5, 18.3, 7.9, 1.5),
        (28.6, 17.0, 8.2, 1.7),
        (30.7, 15.6, 8.5, 1.7),
        (32.8, 14.2, 8.7, 1.6),
        (34.8, 12.9, 8.8, 1.4),
        (36.7, 11.6, 8.8, 1.2),
        (38.6, 10.3, 8.5, 0.9),
    ]
    cols_t = [-1.0, -0.75, -0.50, -0.25, 0.0, 0.25, 0.50, 0.75, 1.0]
    top_grid = []
    bot_grid = []
    for x, z, hw, crown in rows_xz:
        rt, rb = [], []
        for t in cols_t:
            y = t * hw
            arc_z = crown * (1.0 - t * t)
            arc_x = 0.8 * (1.0 - t * t)
            rt.append((x + arc_x, y, z + arc_z))
            rb.append((x + arc_x - 0.45, y * 0.97, z + arc_z - 0.55))
        top_grid.append(rt)
        bot_grid.append(rb)

    # Top face mapped full (0.02..0.98) to gk1_nose.png; normal points (+X, 0, +Z) -> flip_n=True gives +Z/+X
    np_mesh.add_grid_patch(top_grid, uv_rect=(0.02, 0.02, 0.98, 0.98), flip_n=True)
    # Underside mapped to solid crimson margin edge
    np_mesh.add_grid_patch(bot_grid, uv_rect=(0.01, 0.01, 0.08, 0.08), flip_n=False)

    # Side & end edge closures
    nr, nc = len(rows_xz), len(cols_t)
    edge_uv = (0.01, 0.01, 0.08, 0.08)
    for r in range(nr - 1):
        np_mesh.add_quad(top_grid[r][nc - 1], top_grid[r + 1][nc - 1], bot_grid[r + 1][nc - 1], bot_grid[r][nc - 1],
                         (edge_uv[0], edge_uv[1]), (edge_uv[2], edge_uv[1]), (edge_uv[2], edge_uv[3]), (edge_uv[0], edge_uv[3]))
        np_mesh.add_quad(bot_grid[r][0], bot_grid[r + 1][0], top_grid[r + 1][0], top_grid[r][0],
                         (edge_uv[0], edge_uv[1]), (edge_uv[2], edge_uv[1]), (edge_uv[2], edge_uv[3]), (edge_uv[0], edge_uv[3]))
    for c in range(nc - 1):
        np_mesh.add_quad(top_grid[0][c], bot_grid[0][c], bot_grid[0][c + 1], top_grid[0][c + 1],
                         (edge_uv[0], edge_uv[1]), (edge_uv[0], edge_uv[3]), (edge_uv[2], edge_uv[3]), (edge_uv[2], edge_uv[1]))
        np_mesh.add_quad(top_grid[nr - 1][c + 1], bot_grid[nr - 1][c + 1], bot_grid[nr - 1][c], top_grid[nr - 1][c],
                         (edge_uv[0], edge_uv[1]), (edge_uv[0], edge_uv[3]), (edge_uv[2], edge_uv[3]), (edge_uv[2], edge_uv[1]))
    return np_mesh


def build_engine():
    """Exposed rear brushed-aluminum air-cooled engine w/ cooling fins, fuel tank cap, blower, chain."""
    en = MeshPart("engine")

    # 1) Engine mount plate & cast aluminum crankcase (offset slightly right at Y=-3.2)
    en.add_chamfer_box(-36.5, -26.5, -8.5, 2.2, 5.8, 6.6, ch=0.18, uv_rect=UV_ENG_ALUM)
    en.add_chamfer_box(-35.2, -27.5, -7.2, 1.2, 6.6, 12.2, ch=0.65, uv_rect=UV_ENG_ALUM)

    # 2) Inclined air-cooled cylinder barrel + 7 crisp cooling fins + cylinder head + spark plug
    cyl_base = (-30.8, -3.0, 12.0)
    cyl_axis = vnorm((-0.22, 0.0, 0.975))
    # Core cylinder barrel
    en.add_lathe(cyl_base, cyl_axis, [(0.0, 0.0, 0.0), (0.0, 2.9, 0.1), (6.2, 2.9, 0.9), (6.2, 0.0, 1.0)], segs=18, uv_rect=UV_ENG_ALUM)
    # 7 cooling fins
    for i in range(7):
        z_f = 0.8 + i * 0.78
        rf = 4.0 + 0.18 * (i % 2)
        p_f = vadd(cyl_base, vmul(cyl_axis, z_f))
        en.add_lathe(p_f, cyl_axis, [(0.0, 2.8, 0.0), (0.0, rf, 0.2), (0.34, rf, 0.8), (0.34, 2.8, 1.0)], segs=16, uv_rect=UV_ENG_ALUM)
    # Spark plug & red boot on top of head
    head_top = vadd(cyl_base, vmul(cyl_axis, 6.2))
    en.add_lathe(head_top, cyl_axis, [(0.0, 0.85, 0.0), (1.3, 0.85, 0.5), (1.3, 0.55, 0.8), (2.2, 0.55, 1.0)], segs=8, uv_rect=UV_ENG_TANK)

    # 3) Side black blower cooling shroud & recoil starter cup (Y=-7.2..-9.2)
    en.add_lathe(
        (-31.4, -7.2, 9.6), (0.0, -1.0, 0.0),
        [(0.0, 0.0, 0.0, 4.2), (0.0, 4.1, 0.95, 4.2), (1.8, 3.8, 0.85, 4.2), (2.2, 2.1, 0.45, 4.2), (2.3, 0.0, 0.0, 4.2)],
        segs=18, uv_mode="polar", uv_rect=UV_ENG_SHROUD,
    )

    # 4) Carburetor + gold brass velocity stack intake trumpet facing forward (+X)
    en.add_lathe(
        (-28.0, -2.8, 16.5), (1.0, 0.0, 0.0),
        [(0.0, 0.8, 0.0), (2.0, 0.95, 0.4), (3.4, 1.85, 0.9), (3.4, 1.55, 0.95), (2.4, 0.7, 1.0)],
        segs=14, uv_rect=UV_ENG_CHAIN,
    )

    # 5) Rear drive sprocket & chain loop connecting clutch (-31.5, -7.0, 9.5) to rear axle (-25.0, -7.0, 11.0)
    en.add_lathe((-25.0, -7.0, 11.0), (0.0, 1.0, 0.0), [(-0.28, 1.0, 0.0), (-0.28, 5.2, 0.95), (0.28, 5.2, 0.95), (0.28, 1.0, 0.0)], segs=20, uv_mode="polar", uv_rect=UV_ENG_CHAIN)
    chain_pts = [
        (-32.2, -7.0, 7.6), (-25.0, -7.0, 6.2), (-20.2, -7.0, 11.0),
        (-25.0, -7.0, 15.8), (-32.2, -7.0, 11.4),
    ]
    en.add_tube(chain_pts, (0.32, 0.45), segs=6, uv_rect=UV_ENG_CHAIN, closed=True)

    # 6) Cylindrical fuel tank (left bay Y=+7.0) + machined gold vented fuel cap + fuel line
    en.add_lathe(
        (-35.5, 7.0, 10.6), (1.0, 0.0, 0.0),
        [(0.0, 0.0, 0.0), (0.4, 3.6, 0.1), (1.2, 4.1, 0.2), (8.8, 4.1, 0.75), (9.6, 3.6, 0.85), (10.0, 0.0, 0.92)],
        segs=18, uv_rect=UV_ENG_TANK,
    )
    # Gold fuel tank cap on top (Z=14.7..15.8)
    en.add_lathe(
        (-29.5, 7.0, 14.5), (0.0, 0.0, 1.0),
        [(0.0, 1.35, 0.82), (0.85, 1.35, 0.90), (1.15, 1.15, 0.95), (1.15, 0.0, 0.99)],
        segs=14, uv_rect=UV_ENG_TANK,
    )
    en.add_tube([(-29.0, 4.2, 11.5), (-28.5, 1.2, 13.8), (-28.0, -2.4, 16.0)], 0.28, segs=6, uv_rect=UV_ENG_SHROUD)
    return en


def build_exhaust():
    """Curved mandrel-bent header pipe + copper/gold cylindrical muffler pointing backward."""
    ex = MeshPart("exhaust")

    # 1) Curved exhaust header pipe from cylinder rear port (-32.2, -3.0, 16.4) -> muffler inlet (-38.8, -6.0, 15.55)
    hdr_pts = catmull_rom_chain([
        (-32.2, -3.0, 16.4),
        (-34.8, -3.6, 16.6),
        (-36.8, -4.9, 16.1),
        (-38.8, -6.0, 15.55),
    ], 3)
    ex.add_tube(hdr_pts, 1.02, segs=12, uv_rect=UV_EXH_HEADER)

    # 2) Copper/gold cylindrical muffler canister along (-1.0, 0.0, +0.05) ending at tip (-45.5, -6.0, 15.85)
    tip_pos = (EXHAUST_TIP["x"], EXHAUST_TIP["y"], EXHAUST_TIP["z"])
    tip_dir = vnorm((EXHAUST_TIP["dx"], EXHAUST_TIP["dy"], EXHAUST_TIP["dz"]))
    can_origin = vsub(tip_pos, vmul(tip_dir, 6.8))
    ex.add_lathe(
        can_origin, tip_dir,
        [
            (0.0, 1.05, 0.02),
            (0.9, 2.65, 0.14),
            (0.9, 2.65, 0.14),
            (5.4, 2.65, 0.82),
            (5.4, 2.65, 0.82),
            (6.0, 1.30, 0.90),
            (6.0, 1.30, 0.90),
            (6.8, 1.25, 0.98),
        ],
        segs=20, uv_rect=UV_EXH_MUFFLER,
    )
    # Dark interior exhaust bore lip at tip
    ex.add_lathe(
        vsub(tip_pos, vmul(tip_dir, 0.9)), tip_dir,
        [(0.0, 0.0, 0.1), (0.0, 1.0, 0.4), (0.9, 1.0, 0.8), (0.9, 1.25, 0.95)],
        segs=16, uv_rect=UV_EXH_TIP,
    )
    # Stainless retaining clamp strap around muffler
    strap_pos = vadd(can_origin, vmul(tip_dir, 3.1))
    ex.add_lathe(
        strap_pos, tip_dir,
        [(-0.35, 2.66, 0.05), (-0.35, 2.82, 0.15), (0.35, 2.82, 0.85), (0.35, 2.66, 0.95)],
        segs=20, uv_rect=UV_EXH_CLAMP,
    )
    return ex


def build_wheel(radius, half_width, side_sign, segs=32):
    """Chunky wide black racing slick on brushed-gold 5-bolt dish hub centered at (0,0,0).
    Phase-aligned so bottom tread vertices sit at exact z = -radius.
    """
    wp = MeshPart("wheel")
    axis = (0.0, float(side_sign), 0.0)
    up_h = (0.0, 0.0, 1.0)
    # Ensure one vertex lands at exact -Z: basis_from_axis((0,+-1,0)) has Z_w=(0,0,1),
    # so th = -90 deg lands at -Z. phase_deg=-90 puts j=0 at exact bottom -Z!
    phase = -90.0

    r_rim = radius * 0.56
    r_sh = radius * 0.95
    hw = half_width

    # 1) Inner gold rim barrel + inner bore
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-0.78 * hw, 0.00, 0.00, r_rim),
            (-0.78 * hw, 0.30 * r_rim, 0.25, r_rim),
            (-0.62 * hw, 0.84 * r_rim, 0.84, r_rim),
            (-0.82 * hw, 1.00 * r_rim, 1.00, r_rim),
        ],
        segs=segs, uv_mode="cyl", uv_rect=(UV_WHL_HARDWARE[0], UV_WHL_HARDWARE[1], UV_WHL_HARDWARE[0] + 0.22, UV_WHL_HARDWARE[3]),
        up_hint=up_h, phase_deg=phase,
    )

    # 2) Inner rubber sidewall
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-0.82 * hw, r_rim, 0.56, radius),
            (-0.98 * hw, 0.74 * radius, 0.74, radius),
            (-1.00 * hw, 0.86 * radius, 0.86, radius),
            (-0.90 * hw, r_sh, 0.95, radius),
        ],
        segs=segs, uv_mode="polar", uv_rect=UV_WHL_SIDE, up_hint=up_h, phase_deg=phase,
    )

    # 3) Wide flat-crowned racing slick tread
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-0.90 * hw, r_sh, 0.02),
            (-0.78 * hw, 0.992 * radius, 0.12),
            (-0.55 * hw, 1.000 * radius, 0.24),
            ( 0.00 * hw, 1.000 * radius, 0.50),
            (+0.55 * hw, 1.000 * radius, 0.76),
            (+0.78 * hw, 0.992 * radius, 0.88),
            (+0.90 * hw, r_sh, 0.98),
        ],
        segs=segs, uv_mode="cyl", uv_rect=UV_WHL_TREAD, up_hint=up_h, phase_deg=phase,
    )

    # 4) Outer rubber sidewall
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.90 * hw, r_sh, 0.95, radius),
            (+1.00 * hw, 0.86 * radius, 0.86, radius),
            (+0.98 * hw, 0.74 * radius, 0.74, radius),
            (+0.82 * hw, r_rim, 0.56, radius),
        ],
        segs=segs, uv_mode="polar", uv_rect=UV_WHL_SIDE, up_hint=up_h, phase_deg=phase,
    )

    # 5) Outer brushed-gold concave 5-bolt dish hub
    wp.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+0.82 * hw, 1.00 * r_rim, 1.00, r_rim),
            (+0.92 * hw, 0.94 * r_rim, 0.94, r_rim),
            (+0.50 * hw, 0.72 * r_rim, 0.72, r_rim),
            (+0.42 * hw, 0.36 * r_rim, 0.36, r_rim),
            (+0.62 * hw, 0.25 * r_rim, 0.25, r_rim),
            (+0.62 * hw, 0.00 * r_rim, 0.00, r_rim),
        ],
        segs=segs, uv_mode="polar", uv_rect=UV_WHL_DISH, up_hint=up_h, phase_deg=phase,
    )

    # 6) 5 3D chrome/steel lug nuts + center spindle nut + brass valve stem
    X_w, Y_w, Z_w = basis_from_axis(axis, up_hint=up_h)
    hw_uv = (UV_WHL_HARDWARE[0] + 0.26, UV_WHL_HARDWARE[1], UV_WHL_HARDWARE[2], UV_WHL_HARDWARE[3])
    for k in range(5):
        ba = math.radians(k * 72.0)
        bpos = vadd(vmul(X_w, 0.43 * hw), vadd(vmul(Y_w, 0.42 * r_rim * math.cos(ba)), vmul(Z_w, 0.42 * r_rim * math.sin(ba))))
        wp.add_lathe(bpos, axis, [(0.0, 0.42, 0.1), (0.48, 0.42, 0.8), (0.48, 0.0, 0.98)], segs=6, uv_rect=hw_uv, up_hint=up_h)
    # Center spindle hex nut
    wp.add_lathe(vmul(X_w, 0.62 * hw), axis, [(0.0, 0.78, 0.1), (0.65, 0.78, 0.8), (0.65, 0.0, 0.98)], segs=6, uv_rect=hw_uv, up_hint=up_h)
    return wp


def build_shrapnel():
    """Pedals (throttle & brake) + rear chain guard + hardware pieces that stay attached then scatter."""
    sh = MeshPart("shrapnel")
    # Throttle (right Y=-5.2) and Brake (left Y=+5.2) pedals at X=+24.2
    for sgn in (-1.0, +1.0):
        sh.add_chamfer_box(23.6, 25.0, sgn * 5.2 - 1.1, sgn * 5.2 + 1.1, 6.2, 11.4, ch=0.18, uv_rect=UV_STEER_PEDAL)
    # Rear anodized chain guard cover
    sh.add_chamfer_box(-33.0, -23.0, -7.8, -6.2, 13.8, 16.2, ch=0.2, uv_rect=UV_ENG_SHROUD)
    return sh


# ---------------------------------------------------------------------------
# Dynamic Flame Plume & Explosion Fireball (Fixed Topology)
# ---------------------------------------------------------------------------
def _make_flame_frame(is_core, phase_01, plume_len, plume_rad, blast_rad, tip_pos, tip_dir, blast_center):
    """Builds one fixed-topology frame for either flame_outer or flame_core.
    Contains both:
      - Sub-mesh A: Trailing exhaust plume (active in super frames 28..43, collapsed otherwise)
      - Sub-mesh B: Explosion fireball burst (active in explode frames 44..49, collapsed otherwise)
    """
    fp = MeshPart("flame_core" if is_core else "flame_outer")
    uv_plume = UV_FLAME_CORE if is_core else UV_FLAME_OUTER
    uv_blast = UV_BLAST_CORE if is_core else UV_BLAST_OUTER
    X, Y, Z = basis_from_axis(tip_dir, up_hint=(0.0, 0.0, 1.0))

    # --- Sub-mesh A: 14-ring turbulent flame cone + 2 crossed flame fins ---
    n_rings = 14
    segs = 10
    cols = segs + 1
    u0, v0, u1, v1 = uv_plume
    active_p = plume_len > 0.05

    ring_bases = []
    for i in range(n_rings):
        t = i / float(n_rings - 1)
        if active_p:
            # Taper profile: expand quickly near nozzle then taper to sharp flickering tail
            env = math.sin(min(1.0, t * 2.2) * math.pi * 0.5) * ((1.0 - t) ** 0.72)
            pulse = 1.0 + 0.24 * math.sin(t * 11.0 - phase_01 * 2.0 * math.pi * 2.0)
            if is_core:
                pulse += 0.20 * math.cos(t * 18.0 - phase_01 * 2.0 * math.pi * 3.0)
            r_ring = max(0.08, plume_rad * env * pulse)
            whip_y = (1.6 if not is_core else 0.7) * (t ** 1.3) * math.sin(t * 7.5 - phase_01 * 2.0 * math.pi * 2.0)
            whip_z = (1.4 if not is_core else 0.6) * (t ** 1.3) * math.cos(t * 6.5 - phase_01 * 2.0 * math.pi * 2.0)
            c_pt = vadd(tip_pos, vadd(vmul(X, t * plume_len), vadd(vmul(Y, whip_y), vmul(Z, whip_z))))
        else:
            r_ring = 0.002
            c_pt = vadd(tip_pos, vmul(X, -1.0 + t * 0.004))

        rb = len(fp.verts)
        ring_bases.append(rb)
        tv = v0 + (v1 - v0) * t
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(segs))
            cth, sth = math.cos(th), math.sin(th)
            jag = (1.0 + 0.18 * math.sin(th * 3.0 + t * 8.0 - phase_01 * 2.0 * math.pi)) if active_p else 1.0
            pos = vadd(c_pt, vadd(vmul(Y, cth * r_ring * jag), vmul(Z, sth * r_ring * jag)))
            nrm = vnorm(vadd(vmul(Y, cth), vmul(Z, sth)))
            fp.verts.append(pos)
            fp.norms.append(nrm)
            fp.st.append((u0 + (u1 - u0) * (j / float(segs)), tv))

    for i in range(n_rings - 1):
        for j in range(segs):
            a = ring_bases[i] + j
            b = a + 1
            c = ring_bases[i + 1] + j
            d = c + 1
            fp.tris += [(a, b, c), (b, d, c)]

    # 2 crossed longitudinal ribbons for extra volumetric flare from top/side
    n_fin = 10
    for axis_a, axis_b in ((Y, Z), (Z, Y)):
        prev_l = prev_r = None
        for i in range(n_fin):
            t = i / float(n_fin - 1)
            if active_p:
                env = math.sin(min(1.0, t * 2.5) * math.pi * 0.5) * ((1.0 - t) ** 0.65)
                w = max(0.08, plume_rad * 1.25 * env * (1.0 + 0.25 * math.sin(t * 9.0 - phase_01 * 4.0 * math.pi)))
                whip = 1.2 * (t ** 1.3) * math.sin(t * 7.0 - phase_01 * 4.0 * math.pi)
                c_pt = vadd(tip_pos, vadd(vmul(X, t * plume_len * 1.04), vmul(axis_a, whip)))
            else:
                w = 0.002
                c_pt = vadd(tip_pos, vmul(X, -1.0 + t * 0.004))
            tv = v0 + (v1 - v0) * t
            il = len(fp.verts)
            fp.verts += [vsub(c_pt, vmul(axis_a, w)), vadd(c_pt, vmul(axis_a, w))]
            n_fin_v = vnorm(axis_b)
            fp.norms += [n_fin_v, n_fin_v]
            fp.st += [(u0, tv), (u1, tv)]
            if prev_l is not None:
                fp.tris += [(prev_l, prev_r, il + 1), (prev_l, il + 1, il),
                            (prev_l, il + 1, prev_r), (prev_l, il, il + 1)]
            prev_l, prev_r = il, il + 1

    # --- Sub-mesh B: Explosion fireball starburst (8x12 uv-sphere with spiky lobes) ---
    bu0, bv0, bu1, bv1 = uv_blast
    n_lat, n_lon = 8, 12
    b_cols = n_lon + 1
    b_base = len(fp.verts)
    active_b = blast_rad > 0.05
    r_use = blast_rad if active_b else 0.002
    c_use = blast_center if active_b else vsub(tip_pos, tip_dir)

    for i in range(n_lat + 1):
        phi = math.pi * (i / float(n_lat))
        sp, cp = math.sin(phi), math.cos(phi)
        tv = bv0 + (bv1 - bv0) * (i / float(n_lat))
        for j in range(b_cols):
            th = 2.0 * math.pi * (j / float(n_lon))
            ct, st = math.cos(th), math.sin(th)
            dir_v = (sp * ct, sp * st, cp)
            spike = (1.0 + 0.34 * math.sin(th * 5.0 + phase_01 * 6.0) * math.sin(phi * 4.0)) if active_b else 1.0
            pos = vadd(c_use, vmul(dir_v, r_use * spike))
            # Keep fireball above ground Z >= 0.5
            if active_b and pos[2] < 0.5:
                pos = (pos[0], pos[1], 0.5)
            fp.verts.append(pos)
            fp.norms.append(vnorm(dir_v))
            fp.st.append((bu0 + (bu1 - bu0) * (j / float(n_lon)), tv))

    for i in range(n_lat):
        for j in range(n_lon):
            a = b_base + i * b_cols + j
            b = a + 1
            c = a + b_cols
            d = c + 1
            fp.tris += [(a, c, b), (b, c, d)]

    return fp.verts, fp.norms, fp.tris, fp.st


# ---------------------------------------------------------------------------
# Animation & Ballistic Explosion Pipeline (64 Frames)
# ---------------------------------------------------------------------------
def _xform_vn(part, offset=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, pivot=(0.0, 0.0, 0.0)):
    vv, nn = [], []
    px, py, pz = pivot
    ox, oy, oz = offset
    for p, n in zip(part.verts, part.norms):
        q = (p[0] - px, p[1] - py, p[2] - pz)
        qn = n
        if rx:
            q, qn = rot_x(q, rx), rot_x(qn, rx)
        if ry:
            q, qn = rot_y(q, ry), rot_y(qn, ry)
        if rz:
            q, qn = rot_z(q, rz), rot_z(qn, rz)
        vv.append((q[0] + px + ox, q[1] + py + oy, q[2] + pz + oz))
        nn.append(vnorm(qn))
    return vv, nn


def _part_centroid(part):
    n = len(part.verts)
    sx = sum(p[0] for p in part.verts) / n
    sy = sum(p[1] for p in part.verts) / n
    sz = sum(p[2] for p in part.verts) / n
    return (sx, sy, sz)


def _simulate_explosion(part, init_pos_offset, init_ry, init_pivot, vel0, ang_vel0, n_frames=20):
    """20-frame rigid-body ballistic trajectory with tumbling rotation and ground bounce (z >= 0.5)."""
    # Compute base pose at frame 43 (end of super speed)
    base_vv, base_nn = _xform_vn(part, offset=init_pos_offset, ry=init_ry, pivot=init_pivot)
    n = len(base_vv)
    c0 = (
        sum(p[0] for p in base_vv) / n,
        sum(p[1] for p in base_vv) / n,
        sum(p[2] for p in base_vv) / n,
    )
    rel_v = [(p[0] - c0[0], p[1] - c0[1], p[2] - c0[2]) for p in base_vv]

    pos = list(c0)
    vel = list(vel0)
    ang = [0.0, 0.0, 0.0]
    w = list(ang_vel0)
    dt = 0.085
    grav = -145.0
    frames = []

    for k in range(n_frames):
        # Advance physics (start with small initial burst step on frame 0 so impact is immediate)
        step_dt = dt * (0.45 if k == 0 else 1.0)
        vel[2] += grav * step_dt
        pos[0] += vel[0] * step_dt
        pos[1] += vel[1] * step_dt
        pos[2] += vel[2] * step_dt
        ang[0] += w[0] * step_dt
        ang[1] += w[1] * step_dt
        ang[2] += w[2] * step_dt

        # Rotate around piece centroid
        vv_r, nn_r = [], []
        min_z = 1e9
        for q, qn in zip(rel_v, base_nn):
            q = rot_x(q, ang[0])
            q = rot_y(q, ang[1])
            q = rot_z(q, ang[2])
            qn = rot_x(qn, ang[0])
            qn = rot_y(qn, ang[1])
            qn = rot_z(qn, ang[2])
            vz = pos[2] + q[2]
            if vz < min_z:
                min_z = vz
            vv_r.append((pos[0] + q[0], pos[1] + q[1], vz))
            nn_r.append(vnorm(qn))

        # Ground bounce / floor clamp at Z >= 0.5
        if min_z < 0.5:
            shift = 0.5 - min_z
            pos[2] += shift
            vv_r = [(p[0], p[1], p[2] + shift) for p in vv_r]
            if vel[2] < 0.0:
                vel[2] = -0.52 * vel[2]
                vel[0] *= 0.80
                vel[1] *= 0.80
                w[0] *= 0.72
                w[1] *= 0.72
                w[2] *= 0.72

        frames.append((vv_r, nn_r))
    return frames


def build_model():
    chassis = build_chassis()
    seat = build_seat()
    steering = build_steering()
    engine = build_engine()
    exhaust = build_exhaust()
    nose_plate = build_nose_plate()
    shrapnel = build_shrapnel()

    w_fl_local = build_wheel(WHEEL_FRONT_R, WHEEL_FRONT_HW, +1, segs=32)
    w_fr_local = build_wheel(WHEEL_FRONT_R, WHEEL_FRONT_HW, -1, segs=32)
    w_rl_local = build_wheel(WHEEL_REAR_R,  WHEEL_REAR_HW,  +1, segs=32)
    w_rr_local = build_wheel(WHEEL_REAR_R,  WHEEL_REAR_HW,  -1, segs=32)

    wheel_specs = {
        "wheel_fl": (w_fl_local, (WHEEL_FRONT_X, +WHEEL_FRONT_Y, WHEEL_FRONT_R)),
        "wheel_fr": (w_fr_local, (WHEEL_FRONT_X, -WHEEL_FRONT_Y, WHEEL_FRONT_R)),
        "wheel_rl": (w_rl_local, (WHEEL_REAR_X,  +WHEEL_REAR_Y,  WHEEL_REAR_R)),
        "wheel_rr": (w_rr_local, (WHEEL_REAR_X,  -WHEEL_REAR_Y,  WHEEL_REAR_R)),
    }

    body_parts = {
        "chassis": chassis,
        "seat": seat,
        "steering": steering,
        "engine": engine,
        "exhaust": exhaust,
        "nose_plate": nose_plate,
        "shrapnel": shrapnel,
    }

    surf_frames = {name: [] for name in list(body_parts.keys()) + list(wheel_specs.keys()) + ["flame_outer", "flame_core"]}
    frame_names = []
    squat_pivot = (WHEEL_REAR_X, 0.0, WHEEL_REAR_R)
    tip_base = (EXHAUST_TIP["x"], EXHAUST_TIP["y"], EXHAUST_TIP["z"])
    dir_base = vnorm((EXHAUST_TIP["dx"], EXHAUST_TIP["dy"], EXHAUST_TIP["dz"]))

    # --- Frames 0..11: idle_00..idle_11 ---
    for k in range(12):
        frame_names.append(f"idle_{k:02d}")
        ph = 2.0 * math.pi * (k / 12.0)
        dz_ch = 0.16 * math.sin(ph * 2.0)
        dz_eng = 0.28 * math.sin(ph * 3.0) + 0.08 * math.cos(ph)
        dx_eng = 0.08 * math.cos(ph * 2.0)
        for name, part in body_parts.items():
            off = (dx_eng, 0.0, dz_eng) if name in ("engine", "exhaust") else (0.0, 0.0, dz_ch)
            surf_frames[name].append(_xform_vn(part, offset=off))
        for wname, (wpart, wpos) in wheel_specs.items():
            surf_frames[wname].append(_xform_vn(wpart, offset=wpos))
        tp = vadd(tip_base, (dx_eng, 0.0, dz_eng))
        fo_v, fo_n, fo_t, fo_st = _make_flame_frame(False, k / 12.0, 0.0, 0.0, 0.0, tp, dir_base, (0.0, 0.0, 14.0))
        fc_v, fc_n, fc_t, fc_st = _make_flame_frame(True,  k / 12.0, 0.0, 0.0, 0.0, tp, dir_base, (0.0, 0.0, 14.0))
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))
        if k == 0:
            flame_outer_topo = (fo_t, fo_st)
            flame_core_topo = (fc_t, fc_st)

    # --- Frames 12..27: fast_00..fast_15 (wheels spin 2*pi = 360 deg forward) ---
    for k in range(16):
        frame_names.append(f"fast_{k:02d}")
        ph = 2.0 * math.pi * (k / 16.0)
        dz_ch = 0.34 * math.sin(ph * 2.0) + 0.14 * math.cos(ph * 4.0)
        ry_ch = 0.25 * math.sin(ph * 2.0)
        rx_ch = 0.18 * math.cos(ph)
        for name, part in body_parts.items():
            dz_extra = 0.18 * math.sin(ph * 4.0) if name in ("engine", "exhaust") else 0.0
            surf_frames[name].append(_xform_vn(part, offset=(0.0, 0.0, dz_ch + dz_extra), rx=rx_ch, ry=ry_ch, pivot=(0.0, 0.0, 8.0)))
        spin_deg = -360.0 * (k / 16.0)
        for wname, (wpart, wpos) in wheel_specs.items():
            surf_frames[wname].append(_xform_vn(wpart, offset=wpos, ry=spin_deg))
        tp = vadd(tip_base, (0.0, 0.0, dz_ch))
        fo_v, fo_n, _, _ = _make_flame_frame(False, k / 16.0, 0.0, 0.0, 0.0, tp, dir_base, (0.0, 0.0, 14.0))
        fc_v, fc_n, _, _ = _make_flame_frame(True,  k / 16.0, 0.0, 0.0, 0.0, tp, dir_base, (0.0, 0.0, 14.0))
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))

    # --- Frames 28..43: super_00..super_15 (wheels spin 4*pi = 720 deg, +1.8 deg squat, roaring flames!) ---
    for k in range(16):
        frame_names.append(f"super_{k:02d}")
        ph = 2.0 * math.pi * (k / 16.0)
        dz_ch = 0.26 * math.sin(ph * 4.0)
        squat_ry = 1.8 + 0.20 * math.sin(ph * 2.0)  # +ry pitches +X nose UP, squats rear back!
        for name, part in body_parts.items():
            dz_extra = 0.22 * math.sin(ph * 6.0) if name in ("engine", "exhaust") else 0.0
            surf_frames[name].append(_xform_vn(part, offset=(0.0, 0.0, dz_ch + dz_extra), ry=squat_ry, pivot=squat_pivot))
        spin_deg = -720.0 * (k / 16.0)
        for wname, (wpart, wpos) in wheel_specs.items():
            surf_frames[wname].append(_xform_vn(wpart, offset=wpos, ry=spin_deg))

        # Transform exhaust tip & direction by the same super squat so flame stays locked in tailpipe
        tp_rel = vsub(tip_base, squat_pivot)
        tp_sq = vadd(rot_y(tp_rel, squat_ry), vadd(squat_pivot, (0.0, 0.0, dz_ch)))
        dir_sq = vnorm(rot_y(dir_base, squat_ry))

        len_out = 29.0 + 4.2 * math.sin(ph * 2.0) + 1.4 * math.cos(ph * 4.0)  # 24..34u!
        len_cor = 17.5 + 2.8 * math.cos(ph * 3.0)
        fo_v, fo_n, _, _ = _make_flame_frame(False, k / 16.0, len_out, 3.8, 0.0, tp_sq, dir_sq, (0.0, 0.0, 14.0))
        fc_v, fc_n, _, _ = _make_flame_frame(True,  k / 16.0, len_cor, 1.9, 0.0, tp_sq, dir_sq, (0.0, 0.0, 14.0))
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))

    # --- Frames 44..63: explode_00..explode_19 (catastrophic explosion with ballistic trajectories & bounce) ---
    trajectories = {
        "chassis":    ((  -8.0,   4.0,  78.0), ( 110.0,  -85.0,  160.0)),
        "seat":       (( -18.0,  14.0, 132.0), ( 220.0,  160.0, -140.0)),
        "steering":   ((  38.0, -24.0, 148.0), (-260.0,  190.0,  280.0)),
        "engine":     (( -62.0, -34.0, 118.0), ( 180.0, -240.0,  150.0)),
        "exhaust":    (( -92.0, -52.0, 128.0), (-310.0,  210.0, -260.0)),
        "nose_plate": ((  96.0,  18.0, 138.0), ( 280.0,  140.0,  310.0)),
        "shrapnel":   ((  48.0,  46.0, 165.0), ( 340.0, -280.0,  360.0)),
        "wheel_fl":   ((  64.0,  88.0, 108.0), ( 260.0,  320.0,  190.0)),
        "wheel_fr":   ((  68.0, -92.0, 114.0), (-240.0,  340.0, -210.0)),
        "wheel_rl":   (( -72.0,  95.0, 102.0), ( 290.0, -280.0,  220.0)),
        "wheel_rr":   (( -76.0, -94.0, 106.0), (-270.0, -310.0, -240.0)),
    }
    for k in range(20):
        frame_names.append(f"explode_{k:02d}")
    for name, part in body_parts.items():
        v0, w0 = trajectories[name]
        surf_frames[name] += _simulate_explosion(part, (0.0, 0.0, 0.0), 1.8, squat_pivot, v0, w0, n_frames=20)
    for wname, (wpart, wpos) in wheel_specs.items():
        v0, w0 = trajectories[wname]
        surf_frames[wname] += _simulate_explosion(wpart, wpos, 0.0, (0.0, 0.0, 0.0), v0, w0, n_frames=20)

    # Fireball flashes BIG at frames 44..47 (k=0..3), shrinks at 48..49 (k=4..5), gone by 50 (k>=6)
    blast_outer_radii = [22.0, 34.0, 37.0, 30.0, 15.0, 5.5] + [0.0] * 14
    blast_core_radii  = [16.0, 25.0, 23.0, 16.0,  7.0, 2.0] + [0.0] * 14
    for k in range(20):
        c_blast = (0.0, 0.0, 14.0 + k * 2.5)
        fo_v, fo_n, _, _ = _make_flame_frame(False, k / 20.0, 0.0, 0.0, blast_outer_radii[k], tip_base, dir_base, c_blast)
        fc_v, fc_n, _, _ = _make_flame_frame(True,  k / 20.0, 0.0, 0.0, blast_core_radii[k],  tip_base, dir_base, c_blast)
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))

    # Assemble MD3 surface dicts
    surfaces = []
    for name, part in body_parts.items():
        surfaces.append(dict(name=name, shader=SHADERS[name], tris=part.tris, st=part.st, frames=surf_frames[name]))
    for wname, (wpart, _) in wheel_specs.items():
        surfaces.append(dict(name=wname, shader=SHADERS[wname], tris=wpart.tris, st=wpart.st, frames=surf_frames[wname]))
    surfaces.append(dict(name="flame_outer", shader=SHADERS["flame_outer"], tris=flame_outer_topo[0], st=flame_outer_topo[1], frames=surf_frames["flame_outer"]))
    surfaces.append(dict(name="flame_core",  shader=SHADERS["flame_core"],  tris=flame_core_topo[0],  st=flame_core_topo[1],  frames=surf_frames["flame_core"]))

    return dict(name="gokart_1", frame_names=frame_names, surfaces=surfaces)


# ---------------------------------------------------------------------------
# Metadata, Skin, Export & Verification
# ---------------------------------------------------------------------------
def write_skin_and_meta(model):
    skin_path = os.path.join(PROGS_DIR, "gokart_1.md3_0.skin")
    with open(skin_path, "w", encoding="ascii") as f:
        for s in model["surfaces"]:
            f.write(f"{s['name']},{s['shader']}\n")

    os.makedirs(OUT_DIR, exist_ok=True)
    meta = {
        "id": "kart1",
        "name": "Bakersfield Tubular Classic",
        "tagline": "Crimson chromoly rails, brushed-gold 5-bolt hubs & air-cooled Bakersfield fury",
        "palette": PALETTE,
        "description": (
            "Classic tubular-frame racing kart forged from swept crimson-red chromoly tubing "
            "with curved double-rail side-pods, a royal-blue quilted bucket seat, crisp Quake 'Q' "
            "nose cowl, wide slick tires on brushed-gold 5-bolt dish hubs, and an exposed rear "
            "air-cooled engine feeding a copper-gold cylindrical muffler."
        ),
        "highlights": [
            ["Frame", "Swept crimson chromoly perimeter bumper & curved double-rail side-pods"],
            ["Engine", "Exposed finned air-cooled block, gold fuel cap & copper-gold muffler"],
            ["Player Fit", "27u clear open cockpit, seat pan at Z=9.5, 3-spoke tilted wheel at Z=24"],
        ],
        "seat_pos": SEAT_POS,
        "steer_pos": STEER_POS,
        "exhaust_tips": [EXHAUST_TIP],
        "textures": {
            "progs/gk1_frame":    "progs/gk1_frame.png",
            "progs/gk1_seat":     "progs/gk1_seat.png",
            "progs/gk1_steering": "progs/gk1_steering.png",
            "progs/gk1_engine":   "progs/gk1_engine.png",
            "progs/gk1_exhaust":  "progs/gk1_exhaust.png",
            "progs/gk1_nose":     "progs/gk1_nose.png",
            "progs/gk1_wheel":    "progs/gk1_wheel.png",
            "progs/gk1_flame":    "progs/gk1_flame.png",
        },
        "materials": {
            "progs/gk1_frame":    {"metallic": 0.75, "roughness": 0.25, "spec": 0.80},
            "progs/gk1_seat":     {"metallic": 0.05, "roughness": 0.72, "spec": 0.22},
            "progs/gk1_steering": {"metallic": 0.45, "roughness": 0.45, "spec": 0.55},
            "progs/gk1_engine":   {"metallic": 0.85, "roughness": 0.30, "spec": 0.85},
            "progs/gk1_exhaust":  {"metallic": 0.88, "roughness": 0.22, "spec": 0.90},
            "progs/gk1_nose":     {"metallic": 0.40, "roughness": 0.22, "spec": 0.75},
            "progs/gk1_wheel":    {"metallic": 0.35, "roughness": 0.55, "spec": 0.45},
            "progs/gk1_flame":    {"metallic": 0.00, "roughness": 1.00, "spec": 0.00, "emissive": 1.0, "additive": True},
        },
    }
    meta_path = os.path.join(OUT_DIR, "gokart_1_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def verify_md3(md3_path):
    m = md3lib.read(md3_path)
    assert m["nframes"] == 64, f"Expected 64 frames, got {m['nframes']}"
    expected_surfs = {
        "chassis", "seat", "steering", "engine", "exhaust", "nose_plate",
        "wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr", "flame_outer", "flame_core", "shrapnel",
    }
    got_surfs = {s["name"] for s in m["surfaces"]}
    assert expected_surfs.issubset(got_surfs), f"Missing surfaces: {expected_surfs - got_surfs}"

    # Verify per-surface limits & normals & coords
    for s in m["surfaces"]:
        nv = len(s["st"])
        nt = len(s["tris"])
        assert 0 < nv <= 4096, f"{s['name']} nv={nv} > 4096"
        assert 0 < nt <= 8192, f"{s['name']} nt={nt} > 8192"
        assert s["shader"].startswith("progs/gk1_"), f"Bad shader {s['shader']}"
        for fi, (vv, nn) in enumerate(s["frames"]):
            for p, n in zip(vv, nn):
                assert all(math.isfinite(c) and abs(c) < 511.5 for c in p), f"Coord limit hit on {s['name']} f={fi}: {p}"
                assert all(math.isfinite(c) for c in n), f"Non-finite normal on {s['name']} f={fi}"

    # Verify global ground contact in frames 0..43 and >= 0.5 in frames 44..63
    for fi in range(64):
        all_z = [p[2] for s in m["surfaces"] for p in s["frames"][fi][0]]
        z_min = min(all_z)
        if fi <= 43:
            assert abs(z_min) <= 0.1, f"Frame {fi} z_min={z_min:.4f} != 0.0 +/- 0.1"
        else:
            assert z_min >= 0.48, f"Explosion frame {fi} z_min={z_min:.4f} < 0.5"

    # Verify frame 0 overall kart bounds & cockpit clearance
    f0_pts = [p for s in m["surfaces"] if not s["name"].startswith("flame_") for p in s["frames"][0][0]]
    xs = [p[0] for p in f0_pts]
    ys = [p[1] for p in f0_pts]
    zs = [p[2] for p in f0_pts]
    assert min(xs) >= -46.0 and max(xs) <= 48.0, f"X out of [-46, 48]: [{min(xs):.2f}, {max(xs):.2f}]"
    assert min(ys) >= -32.0 and max(ys) <= 32.0, f"Y out of [-32, 32]: [{min(ys):.2f}, {max(ys):.2f}]"

    # Verify flame collapse in idle/fast (0..27), eruption in super (28..43), flash in 44..47, collapse by 50
    fo_s = next(s for s in m["surfaces"] if s["name"] == "flame_outer")
    for fi in range(64):
        pts = fo_s["frames"][fi][0]
        fxs = [p[0] for p in pts]
        fys = [p[1] for p in pts]
        fzs = [p[2] for p in pts]
        span_x = max(fxs) - min(fxs)
        span_r = max(max(fys) - min(fys), max(fzs) - min(fzs))
        if fi <= 27 or fi >= 50:
            assert max(span_x, span_r) < 0.05, f"Flame not collapsed at frame {fi}: span=({span_x:.3f}, {span_r:.3f})"
        elif 28 <= fi <= 43:
            assert 24.0 <= span_x <= 36.0, f"Super flame length out of 24..34u range at frame {fi}: {span_x:.2f}"
        elif 44 <= fi <= 47:
            assert max(span_x, span_r) >= 35.0, f"Explosion fireball too small at frame {fi}: {max(span_x, span_r):.2f}"

    # Verify cockpit lateral clearance (|Y| <= 13 clear between side rails/pods)
    ch_s = next(s for s in m["surfaces"] if s["name"] == "chassis")
    cockpit_intruders = [p for p in ch_s["frames"][0][0] if -12.0 <= p[0] <= 12.0 and abs(p[1]) < 13.0 and p[2] > 5.5]
    assert not cockpit_intruders, f"Chassis intrudes into cockpit |Y|<13: {cockpit_intruders[:3]}"

    # Verify 22u-wide x 28u-tall seated torso clearance box above seat_pos (-9, 0, 9.5)
    torso_intruders = [
        (s["name"], p)
        for s in m["surfaces"]
        if not s["name"].startswith("flame_") and s["name"] != "driver"
        for p in s["frames"][0][0]
        if -16.0 <= p[0] <= -2.0 and abs(p[1]) < 11.0 and (SEAT_POS["z"] + 1.5) <= p[2] <= (SEAT_POS["z"] + 28.0)
    ]
    assert not torso_intruders, f"Geometry inside 22x28u torso box: {torso_intruders[:5]}"

    print(f"Verified {md3_path}: {m['nframes']} frames, {len(m['surfaces'])} surfaces")
    print(f"Frame 0 bounds: X=[{min(xs):.2f}, {max(xs):.2f}] Y=[{min(ys):.2f}, {max(ys):.2f}] Z=[{min(zs):.2f}, {max(zs):.2f}]")
    for s in m["surfaces"]:
        print(f"  {s['name']:12s} shader={s['shader']:18s} verts={len(s['st']):4d} tris={len(s['tris']):4d}")


def main():
    build_all_textures()
    model = build_model()
    md3_path = os.path.join(PROGS_DIR, "gokart_1.md3")
    md3lib.write(md3_path, model)
    write_skin_and_meta(model)
    verify_md3(md3_path)


if __name__ == "__main__":
    main()
