"""Procedural 3D MD3 Builder & Texture Generator for Go-Kart #4: "Mega Man Classic Bar-Racer".

Outputs (only owned files):
  - source/mm_tools/gokart_4.py (this script)
  - progs/gokart_4.md3
  - progs/gokart_4.md3_0.skin
  - progs/gk4_wheel.png
  - progs/gk4_chrome.png
  - progs/gk4_seat.png
  - progs/gk4_flame.png
  - source/mm_tools/out/gokart_4_meta.json

Coordinate system (Quake / DarkPlaces MD3 standard):
  +X = forward, +Y = left, +Z = up, ground contact plane at Z = 0.
"""
import argparse
import json
import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_DIR = os.path.join(REPO_ROOT, "progs")
OUT_DIR = os.path.join(HERE, "out")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib
from mmw_geometry import (
    MeshPart,
    basis_from_axis,
    rot_x,
    rot_y,
    rot_z,
    vadd,
    vcross,
    vdot,
    vlen,
    vlerp,
    vmul,
    vnorm,
    vsub,
)
from tank_geom_core import build_pneumatic_wheel
import tank_tex_gen
from tank_tex_gen import (
    UV_CHROME_BAR,
    UV_COTTER_YEL,
    UV_HEX_ZINC,
    UV_RUBBER_CAP,
    UV_STAINLESS,
    UV_VALVE_BLK,
    UV_VALVE_BRASS,
)

# ---------------------------------------------------------------------------
# Palette & Constants
# ---------------------------------------------------------------------------
PALETTE = ["#d8dce2", "#243452", "#94a3b8", "#1c1917"]

WHEEL_FRONT_X = 25.0
WHEEL_FRONT_Y = 25.5
WHEEL_FRONT_R = 9.5
WHEEL_FRONT_HW = 5.0

WHEEL_REAR_X = -25.0
WHEEL_REAR_Y = 26.0
WHEEL_REAR_R = 11.0
WHEEL_REAR_HW = 6.0

SEAT_POS = {"x": -9.0, "y": 0.0, "z": 9.5}
STEER_POS = {"x": 13.0, "y": 0.0, "z": 24.0}
EXHAUST_TIPS = [
    {"x": -44.5, "y":  7.5, "z": 15.4, "dx": -0.997, "dy": 0.0, "dz": 0.070},
    {"x": -44.5, "y": -7.5, "z": 15.4, "dx": -0.997, "dy": 0.0, "dz": 0.070},
]

SHADERS = {
    "chassis":     "progs/gk4_chrome",
    "front_bar":   "progs/gk4_chrome",
    "t_collar":    "progs/gk4_chrome",
    "seat":        "progs/gk4_seat",
    "steering":    "progs/gk4_chrome",
    "booster":     "progs/gk4_chrome",
    "wheel_fl":    "progs/gk4_wheel",
    "wheel_fr":    "progs/gk4_wheel",
    "wheel_rl":    "progs/gk4_wheel",
    "wheel_rr":    "progs/gk4_wheel",
    "wheel_fl_hw": "progs/gk4_chrome",
    "wheel_fr_hw": "progs/gk4_chrome",
    "wheel_rl_hw": "progs/gk4_chrome",
    "wheel_rr_hw": "progs/gk4_chrome",
    "flame_outer": "progs/gk4_flame",
    "flame_core":  "progs/gk4_flame",
    "shrapnel":    "progs/gk4_chrome",
}

# UV rects inside 1024x1024 seat & flame atlases
UV_Q1 = (0.02, 0.02, 0.48, 0.48)
UV_Q2 = (0.52, 0.02, 0.98, 0.48)
UV_Q3 = (0.02, 0.52, 0.48, 0.98)
UV_Q4 = (0.52, 0.52, 0.98, 0.98)

UV_SEAT_WHITE = UV_Q1
UV_SEAT_BLUE  = UV_Q2
UV_SEAT_SHELL = UV_Q3
UV_SEAT_CREST = UV_Q4

UV_FLAME_OUTER = UV_Q1
UV_FLAME_CORE  = UV_Q2
UV_BLAST_OUTER = UV_Q3
UV_BLAST_CORE  = UV_Q4


# ---------------------------------------------------------------------------
# Geometry Helpers
# ---------------------------------------------------------------------------
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


def add_tube_ex(part, pts, radii, segs=10, uv_rect=(0.0, 0.0, 1.0, 1.0), cap_start=True, cap_end=True, closed=False):
    """Sweeps circular/elliptical tube along polyline (supports scalar radius, per-point list, and closed loops)."""
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
        rad = radii[i] if isinstance(radii, list) else radii
        ry, rz = rad if isinstance(rad, tuple) else (rad, rad)
        r_base = len(part.verts)
        rings.append(r_base)
        tv = v0 + (v1 - v0) * (i / float(max(1, n - 1)))
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(segs))
            cth, sth = math.cos(th), math.sin(th)
            pos = vadd(pts[i], vadd(vmul(Y, cth * ry), vmul(Z, sth * rz)))
            nrm = vnorm(vadd(vmul(Y, cth / max(ry, 1e-5)), vmul(Z, sth / max(rz, 1e-5))))
            part.verts.append(pos)
            part.norms.append(nrm)
            part.st.append((u0 + (u1 - u0) * (j / float(segs)), tv))

    seg_count = n if closed else n - 1
    for i in range(seg_count):
        r0 = rings[i]
        r1 = rings[(i + 1) % n]
        for j in range(segs):
            a = r0 + j
            b = a + 1
            c = r1 + j
            d = c + 1
            part.tris += [(a, b, c), (b, d, c)]

    if not closed and cap_start:
        r0 = radii[0] if isinstance(radii, list) else radii
        if isinstance(r0, tuple):
            r0 = r0[0]
        ic = len(part.verts)
        part.verts.append(vsub(pts[0], vmul(tans[0], r0 * 0.25)))
        part.norms.append(vmul(tans[0], -1.0))
        part.st.append((0.5 * (u0 + u1), v0))
        for j in range(segs):
            part.tris.append((ic, rings[0] + j + 1, rings[0] + j))

    if not closed and cap_end:
        rn = radii[-1] if isinstance(radii, list) else radii
        if isinstance(rn, tuple):
            rn = rn[0]
        ic = len(part.verts)
        part.verts.append(vadd(pts[-1], vmul(tans[-1], rn * 0.25)))
        part.norms.append(tans[-1])
        part.st.append((0.5 * (u0 + u1), v1))
        for j in range(segs):
            part.tris.append((ic, rings[-1] + j, rings[-1] + j + 1))


def add_grid_patch(part, grid_pts, uv_rect=(0.0, 0.0, 1.0, 1.0), flip_n=False):
    """Builds a smooth vertex-grid patch from grid_pts[row][col] = (x,y,z) onto a MeshPart."""
    nr = len(grid_pts)
    nc = len(grid_pts[0])
    u0, v0, u1, v1 = uv_rect
    base = len(part.verts)
    acc = [[0.0, 0.0, 0.0] for _ in range(nr * nc)]
    tris = []
    for r in range(nr):
        tv = v0 + (v1 - v0) * (r / float(nr - 1))
        for c in range(nc):
            tu = u0 + (u1 - u0) * (c / float(nc - 1))
            part.verts.append(grid_pts[r][c])
            part.st.append((tu, tv))
    for r in range(nr - 1):
        for c in range(nc - 1):
            a = r * nc + c
            b = a + 1
            d = (r + 1) * nc + c
            e = d + 1
            pair = ((a, b, e), (a, e, d)) if not flip_n else ((a, e, b), (a, d, e))
            for t in pair:
                p0, p1, p2 = part.verts[base + t[0]], part.verts[base + t[1]], part.verts[base + t[2]]
                fn = vcross(vsub(p1, p0), vsub(p2, p0))
                tris.append((base + t[0], base + t[1], base + t[2]))
                for vi in t:
                    acc[vi][0] += fn[0]
                    acc[vi][1] += fn[1]
                    acc[vi][2] += fn[2]
    for n in acc:
        part.norms.append(vnorm(n))
    part.tris += tris


# ---------------------------------------------------------------------------
# Procedural & Calibrated Texture Generation
# ---------------------------------------------------------------------------
def _font(size, bold=True):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
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


def _tex_wheel_from_mmt(src_path, dst_path):
    """Reads read-only mmt_wheel.png and restores crisp off-white steel rim contrast for WebGL2."""
    arr = np.asarray(Image.open(src_path).convert("RGB"), dtype=np.float32)
    out = arr.copy()
    # Q1 & Q2: 5-ribbed black tire tread & molded sidewall
    out[:512, :, :] = np.clip(arr[:512, :, :] * 1.38, 12, 130)
    # Q3 & Q4: smooth concave off-white stamped steel dish rims
    out[512:, :, :] = np.clip(arr[512:, :, :] * 2.28, 18, 250)
    Image.fromarray(out.astype(np.uint8), mode="RGB").save(dst_path, "PNG", optimize=True)


def _tex_chrome_from_mmt(src_path, dst_path):
    """Reads read-only mmt_chrome_bar.png and restores mirror-chrome & stainless brilliance."""
    arr = np.asarray(Image.open(src_path).convert("RGB"), dtype=np.float32)
    out = arr.copy()
    # Q1 (mirror chrome bar) & Q2 (brushed stainless axle & TIG T-collar)
    out[:512, :, :] = np.clip(arr[:512, :, :] * 2.18, 18, 252)
    # Q3 (matte ribbed black rubber rear cap)
    out[512:, :512, :] = np.clip(arr[512:, :512, :] * 1.42, 14, 72)
    # Q4 hardware sub-swatches: zinc hex, yellow cotter pin, valve black rubber, brass valve
    out[512:768, 512:, :] = np.clip(arr[512:768, 512:, :] * 2.18, 20, 252)
    out[768:, 512:768, :] = np.clip(arr[768:, 512:768, :] * 1.35, 12, 68)
    out[768:, 768:, :] = np.clip(arr[768:, 768:, :] * 2.18, 20, 252)
    Image.fromarray(out.astype(np.uint8), mode="RGB").save(dst_path, "PNG", optimize=True)


def _tex_seat(path):
    """1024x1024: Off-white ribbed cushion, classic navy-slate bolsters, charcoal shell, #04 crest."""
    H = W = 1024
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=404, octaves=(4, 8, 16, 64))
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

    # Q1: Warm off-white ribbed racing cushion with horizontal stitched pleats & navy-slate side piping
    u = xx / 511.0
    v = yy / 511.0
    rib = np.sin(v * math.pi * 10.0)
    seam = np.exp(-((np.abs(np.sin(v * math.pi * 10.0))) ** 2) / 0.03)
    puff = 0.94 + 0.07 * np.abs(rib) - 0.14 * seam
    navy_pipe = np.exp(-((u - 0.07) ** 2) / 0.0005) + np.exp(-((u - 0.93) ** 2) / 0.0005)
    navy_pipe = np.clip(navy_pipe, 0.0, 1.0)
    w_r = 224.0 * puff + 3.5 * noise[:512, :512]
    w_g = 220.0 * puff + 3.5 * noise[:512, :512]
    w_b = 210.0 * puff + 4.0 * noise[:512, :512]
    arr[:512, :512, 0] = np.clip(w_r * (1.0 - navy_pipe) + 34.0 * navy_pipe, 18, 240)
    arr[:512, :512, 1] = np.clip(w_g * (1.0 - navy_pipe) + 48.0 * navy_pipe, 22, 238)
    arr[:512, :512, 2] = np.clip(w_b * (1.0 - navy_pipe) + 76.0 * navy_pipe, 30, 234)

    # Q2: Classic deep navy-slate bolsters with off-white edge piping
    pipe = np.exp(-((u - 0.08) ** 2) / 0.00045)
    arr[:512, 512:, 0] = np.clip(32.0 + 168.0 * pipe + 4.5 * noise[:512, 512:], 14, 225)
    arr[:512, 512:, 1] = np.clip(46.0 + 154.0 * pipe + 5.0 * noise[:512, 512:], 18, 225)
    arr[:512, 512:, 2] = np.clip(74.0 + 126.0 * pipe + 5.5 * noise[:512, 512:], 24, 225)

    # Q3: Satin dark charcoal-titanium bucket shell back with twin navy & off-white racing stripe
    stripe_w = np.exp(-((u - 0.50) ** 2) / 0.0035)
    stripe_b = np.exp(-((u - 0.42) ** 2) / 0.0012) + np.exp(-((u - 0.58) ** 2) / 0.0012)
    sh = 44.0 + 6.0 * np.sin(yy * 0.25) + 4.0 * noise[512:, :512]
    arr[512:, :512, 0] = np.clip(sh + 158.0 * stripe_w - 6.0 * stripe_b, 14, 225)
    arr[512:, :512, 1] = np.clip(sh + 156.0 * stripe_w + 8.0 * stripe_b, 16, 225)
    arr[512:, :512, 2] = np.clip(sh * 1.06 + 152.0 * stripe_w + 38.0 * stripe_b, 20, 225)

    # Q4: Classic Bar-Racer #04 crest
    arr[512:, 512:, 0] = 32.0
    arr[512:, 512:, 1] = 46.0
    arr[512:, 512:, 2] = 74.0
    im = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([548, 558, 988, 968], radius=38, fill=(26, 38, 62), outline=(215, 218, 224), width=8)
    f_big = _font(54, bold=True)
    f_sm = _font(34, bold=True)
    dr.text((768, 720), "CLASSIC", fill=(228, 232, 238), font=f_sm, anchor="mm")
    dr.text((768, 798), "BAR-RACER #04", fill=(182, 194, 212), font=f_big, anchor="mm")
    im.save(path, "PNG", optimize=True)


def _tex_flame(path):
    """512x512 RGBA: Fiery amber/orange rocket plume, white-gold inner core, fireball burst."""
    H = W = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    noise = _fbm(H, W, seed=844, octaves=(4, 8, 16, 32))
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    u = xx / 255.0
    v = yy / 255.0

    # Q1: Outer rocket exhaust plume (golden-amber-orange)
    edge_y = 1.0 - np.abs(2.0 * u - 1.0) ** 1.55
    streak = 0.78 + 0.22 * np.sin(u * 26.0 + v * 14.0 + noise[:256, :256] * 3.0)
    intensity = np.clip((1.0 - v * 0.76) * edge_y * streak, 0.0, 1.0)
    rgba[:256, :256, 0] = np.clip(255.0 * (intensity ** 0.42), 0, 255)
    rgba[:256, :256, 1] = np.clip(175.0 * (intensity ** 1.05), 0, 255)
    rgba[:256, :256, 2] = np.clip(60.0 * (intensity ** 1.9), 0, 255)
    rgba[:256, :256, 3] = np.clip(255.0 * (intensity ** 0.60), 0, 255)

    # Q2: Inner flame core (warm white-gold)
    core_e = np.exp(-(((2.0 * u - 1.0) * 1.32) ** 2)) * np.clip(1.0 - v * 0.70, 0.0, 1.0)
    core_i = np.clip(core_e * (0.88 + 0.12 * np.sin(v * 24.0)), 0.0, 1.0)
    rgba[:256, 256:, 0] = np.clip(255.0 * (core_i ** 0.35), 0, 255)
    rgba[:256, 256:, 1] = np.clip(242.0 * (core_i ** 0.50), 0, 255)
    rgba[:256, 256:, 2] = np.clip(188.0 * (core_i ** 0.95), 0, 255)
    rgba[:256, 256:, 3] = np.clip(255.0 * (core_i ** 0.48), 0, 255)

    # Q3 & Q4: Radial explosion fireball outer & white-gold blast core
    rx = (xx - 127.5) / 118.0
    ry = (yy - 127.5) / 118.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang = np.arctan2(ry, rx)
    turb = 1.0 + 0.20 * np.sin(ang * 7.0 + rr * 4.0) + 0.16 * noise[256:, :256]
    fb = np.clip((1.0 - rr * 0.92 / turb), 0.0, 1.0)
    rgba[256:, :256, 0] = np.clip(255.0 * (fb ** 0.40), 0, 255)
    rgba[256:, :256, 1] = np.clip(150.0 * (fb ** 1.15), 0, 255)
    rgba[256:, :256, 2] = np.clip(40.0 * (fb ** 2.2), 0, 255)
    rgba[256:, :256, 3] = np.clip(245.0 * (fb ** 0.68), 0, 255)

    fc = np.clip(1.0 - rr * 1.1, 0.0, 1.0)
    rgba[256:, 256:, 0] = 255.0
    rgba[256:, 256:, 1] = np.clip(250.0 * (fc ** 0.40), 0, 255)
    rgba[256:, 256:, 2] = np.clip(225.0 * (fc ** 0.72), 0, 255)
    rgba[256:, 256:, 3] = np.clip(255.0 * (fc ** 0.52), 0, 255)

    Image.fromarray(rgba.astype(np.uint8), mode="RGBA").save(path, "PNG", optimize=True)


def build_all_textures(progs_dir=PROGS_DIR):
    os.makedirs(progs_dir, exist_ok=True)
    src_wheel = os.path.join(progs_dir, "mmt_wheel.png")
    src_chrome = os.path.join(progs_dir, "mmt_chrome_bar.png")
    if os.path.isfile(src_wheel) and os.path.isfile(src_chrome):
        _tex_wheel_from_mmt(src_wheel, os.path.join(progs_dir, "gk4_wheel.png"))
        _tex_chrome_from_mmt(src_chrome, os.path.join(progs_dir, "gk4_chrome.png"))
    else:
        with tempfile.TemporaryDirectory() as tmp_mmt:
            p_wheel, _ = tank_tex_gen.build_wheel_textures(tmp_mmt)
            p_chrome, _ = tank_tex_gen.build_chrome_bar_textures(tmp_mmt)
            _tex_wheel_from_mmt(p_wheel, os.path.join(progs_dir, "gk4_wheel.png"))
            _tex_chrome_from_mmt(p_chrome, os.path.join(progs_dir, "gk4_chrome.png"))
    _tex_seat(os.path.join(progs_dir, "gk4_seat.png"))
    _tex_flame(os.path.join(progs_dir, "gk4_flame.png"))


# ---------------------------------------------------------------------------
# 3D Sub-Assembly Builders
# ---------------------------------------------------------------------------
def build_front_bar():
    """Prominent mirror-chrome Mega Man torpedo silver bar (X=+11..+54) + ribbed black rubber rear cap."""
    fb = MeshPart("chrome_bar")

    # Axis along +X at Y=0.0, Z=10.2 (passes right through the front cross-axle T-collar at X=+25)
    origin = (0.0, 0.0, 10.2)

    # 1) Ribbed matte-black rubber rear end-cap (X = +11.0 .. +16.6)
    fb.add_lathe(
        origin, (1.0, 0.0, 0.0),
        [
            (11.0, 0.00, 0.02),
            (11.0, 2.25, 0.12),
            (11.0, 2.25, 0.12),
            (11.6, 2.72, 0.22),
            (13.2, 2.72, 0.44),
            (13.4, 2.52, 0.52),
            (14.6, 2.52, 0.70),
            (14.8, 2.72, 0.78),
            (16.4, 2.72, 0.94),
            (16.4, 2.72, 0.94),
            (16.6, 2.42, 0.98),
        ],
        segs=26, uv_rect=UV_RUBBER_CAP,
    )

    # 2) Mirror-chrome central bar + clamp shoulder at X=+25 + ogive bullet nose to X=+54.0
    prof = [
        (16.6, 2.42, 0.04),
        (21.0, 2.42, 0.16),
        (22.4, 2.60, 0.24),
        (23.6, 2.95, 0.34),
        (25.0, 3.05, 0.42),
        (26.4, 2.95, 0.50),
        (27.6, 2.60, 0.58),
        (29.0, 2.42, 0.64),
        (41.5, 2.42, 0.80),
    ]
    for k in range(1, 10):
        t = k / 9.0
        xn = 41.5 + 12.5 * t
        rn = 2.42 * (math.cos(t * math.pi * 0.5) ** 0.76) if k < 9 else 0.0
        prof.append((xn, rn, 0.80 + 0.18 * t))
    fb.add_lathe(origin, (1.0, 0.0, 0.0), prof, segs=26, uv_rect=UV_CHROME_BAR)
    return fb


def build_t_collar():
    """TIG-welded stainless T-collar clamping front silver bar to front cross-axle & nose frame."""
    tc = MeshPart("chrome_bar")

    # 1) Transverse stainless T-collar sleeve around front cross-axle (X=25.0, Z=9.5)
    tc.add_lathe(
        (25.0, 0.0, 9.5), (0.0, 1.0, 0.0),
        [
            (-6.8, 1.25, 0.96),
            (-6.8, 2.25, 0.92),
            (-6.8, 2.25, 0.92),
            (-3.8, 2.55, 0.82),
            (0.0,  2.85, 0.72),
            (+3.8, 2.55, 0.82),
            (+6.8, 2.25, 0.92),
            (+6.8, 2.25, 0.92),
            (+6.8, 1.25, 0.96),
        ],
        segs=20, uv_rect=UV_STAINLESS,
    )
    # Twin zinc clamping retaining rings flanking the T-collar
    for sgn in (-1.0, +1.0):
        tc.add_lathe(
            (25.0, sgn * 8.0, 9.5), (0.0, sgn, 0.0),
            [
                (-1.0, 1.25, 0.08),
                (-1.0, 2.05, 0.18),
                (-1.0, 2.05, 0.18),
                (+1.0, 2.05, 0.82),
                (+1.0, 2.05, 0.82),
                (+1.0, 1.25, 0.92),
            ],
            segs=16, uv_rect=UV_HEX_ZINC,
        )

    # 2) Longitudinal TIG-welded saddle sleeve around front_bar (X=21.6..28.8, Z=10.2)
    tc.add_lathe(
        (0.0, 0.0, 10.2), (1.0, 0.0, 0.0),
        [
            (21.6, 2.40, 0.04),
            (21.6, 3.35, 0.14),
            (21.6, 3.35, 0.14),
            (23.5, 3.55, 0.35),
            (25.0, 3.72, 0.50),
            (26.5, 3.55, 0.65),
            (28.8, 3.35, 0.86),
            (28.8, 3.35, 0.86),
            (28.8, 2.40, 0.96),
        ],
        segs=22, uv_rect=UV_STAINLESS,
    )

    # 3) Top TIG clamp boss + hex fasteners + diagonal nose-frame gussets
    tc.add_chamfer_box(23.2, 26.8, -1.6, 1.6, 12.6, 14.2, ch=0.35, uv_rect=UV_HEX_ZINC)
    for sgn in (-1.0, +1.0):
        add_tube_ex(tc, [(25.0, sgn * 2.8, 11.4), (31.0, sgn * 7.8, 8.2)], 0.58, segs=8, uv_rect=UV_STAINLESS)
        add_tube_ex(tc, [(25.0, sgn * 5.2, 9.8), (24.0, sgn * 5.4, 15.8)], 0.52, segs=8, uv_rect=UV_STAINLESS)
    return tc


def build_chassis():
    """Stainless steel front & rear cross-axles + swept twin perimeter side rails + steering hoop + floorpan."""
    ch = MeshPart("chrome_bar")

    # 1) Front cross-axle (X=25.0, Z=9.5) + kingpin yokes & stub axles
    ch.add_lathe(
        (25.0, 0.0, 9.5), (0.0, 1.0, 0.0),
        [
            (-24.8, 0.0,  0.02),
            (-24.8, 1.55, 0.04),
            (-19.5, 1.55, 0.10),
            (-19.2, 1.22, 0.12),
            (+19.2, 1.22, 0.88),
            (+19.5, 1.55, 0.90),
            (+24.8, 1.55, 0.96),
            (+24.8, 0.0,  0.98),
        ],
        segs=16, uv_rect=UV_STAINLESS,
    )
    for sgn in (-1.0, +1.0):
        add_tube_ex(ch, [(25.0, sgn * 18.8, 7.2), (25.0, sgn * 18.8, 11.8)], 0.86, segs=8, uv_rect=UV_HEX_ZINC)
        add_tube_ex(ch, [(22.4, sgn * 1.4, 8.6), (23.2, sgn * 18.4, 9.5)], 0.36, segs=6, uv_rect=UV_STAINLESS)

    # 2) Rear live cross-axle (X=-25.0, Z=11.0) + bearing hangers + brake rotor & drive sprocket
    ch.add_lathe(
        (-25.0, 0.0, 11.0), (0.0, 1.0, 0.0),
        [
            (-25.2, 0.0,  0.02),
            (-25.2, 1.75, 0.04),
            (-19.0, 1.75, 0.10),
            (-18.6, 1.35, 0.12),
            (+18.6, 1.35, 0.88),
            (+19.0, 1.75, 0.90),
            (+25.2, 1.75, 0.96),
            (+25.2, 0.0,  0.98),
        ],
        segs=16, uv_rect=UV_STAINLESS,
    )
    for yb in (-13.2, 0.0, 13.2):
        add_tube_ex(ch, [(-25.0, yb, 5.6), (-25.0, yb, 11.0)], 0.72, segs=8, uv_rect=UV_STAINLESS)
        ch.add_chamfer_box(-26.8, -23.2, yb - 0.95, yb + 0.95, 9.2, 12.8, ch=0.35, uv_rect=UV_HEX_ZINC)
    # Rear brake disc (Y=+10.5) & drive sprocket (Y=-10.5)
    ch.add_lathe(
        (-25.0, 10.5, 11.0), (0.0, 1.0, 0.0),
        [(-0.32, 1.3, 0.05), (-0.32, 5.4, 0.45), (+0.32, 5.4, 0.55), (+0.32, 1.3, 0.95)],
        segs=20, uv_rect=UV_CHROME_BAR,
    )
    ch.add_chamfer_box(-30.0, -26.2, 9.2, 11.8, 9.4, 12.8, ch=0.3, uv_rect=UV_HEX_ZINC)
    ch.add_lathe(
        (-25.0, -10.5, 11.0), (0.0, 1.0, 0.0),
        [(-0.30, 1.3, 0.05), (-0.30, 4.8, 0.45), (+0.30, 4.8, 0.55), (+0.30, 1.3, 0.95)],
        segs=20, uv_rect=UV_HEX_ZINC,
    )

    # 3) Swept stainless tubular twin perimeter side rails (outside |Y| >= 14.5 through cockpit)
    for sgn in (-1.0, +1.0):
        rail_lo = [
            (-42.5, sgn * 10.6, 6.4),
            (-34.0, sgn * 11.6, 5.6),
            (-25.0, sgn * 13.0, 5.6),
            (-13.5, sgn * 14.8, 5.6),
            (0.0,   sgn * 15.0, 5.6),
            (12.5,  sgn * 14.6, 5.6),
            (21.5,  sgn * 11.4, 6.4),
            (29.5,  sgn * 8.4,  7.2),
            (36.5,  sgn * 6.2,  7.8),
        ]
        add_tube_ex(ch, catmull_rom_chain(rail_lo, 3), 0.92, segs=10, uv_rect=UV_STAINLESS)

        # Swept twin outer nerf bar rails (lower & upper) outside |Y| >= 14.6
        pod_lo = [
            (12.2,  sgn * 14.6, 5.7),
            (9.5,   sgn * 20.6, 6.2),
            (2.0,   sgn * 22.6, 6.4),
            (-6.5,  sgn * 22.2, 6.4),
            (-11.5, sgn * 19.8, 6.2),
            (-13.5, sgn * 14.8, 5.7),
        ]
        pod_hi = [
            (11.4,  sgn * 14.8, 7.2),
            (8.8,   sgn * 21.2, 10.2),
            (1.0,   sgn * 23.2, 10.8),
            (-7.0,  sgn * 22.7, 10.5),
            (-11.5, sgn * 20.2, 9.8),
            (-13.2, sgn * 14.9, 7.0),
        ]
        add_tube_ex(ch, catmull_rom_chain(pod_lo, 3), 0.78, segs=10, uv_rect=UV_STAINLESS)
        add_tube_ex(ch, catmull_rom_chain(pod_hi, 3), 0.76, segs=10, uv_rect=UV_STAINLESS)
        for xp, yp, zlo, zhi in ((5.0, sgn * 22.2, 6.3, 10.6), (-4.0, sgn * 22.4, 6.4, 10.6)):
            add_tube_ex(ch, [(xp, yp, zlo), (xp, yp * 1.02, zhi)], 0.60, segs=8, uv_rect=UV_STAINLESS)

        # Front axle outrigger brace from main rail to kingpin
        add_tube_ex(ch, [(21.5, sgn * 11.4, 6.4), (25.0, sgn * 18.6, 9.2)], 0.72, segs=8, uv_rect=UV_STAINLESS)

    # 4) Front nose underslung tubular loop (passes cleanly beneath front_bar at Z=6.4, leaving front_bar proud!)
    front_loop = [
        (31.0, -8.2, 7.4),
        (36.8, -6.0, 6.6),
        (38.6,  0.0, 6.2),
        (36.8,  6.0, 6.6),
        (31.0,  8.2, 7.4),
    ]
    add_tube_ex(ch, catmull_rom_chain(front_loop, 3), 0.82, segs=10, uv_rect=UV_STAINLESS)
    # Front rubberized bumper sleeve at tip of nose loop (below front_bar)
    add_tube_ex(ch, [(38.4, -3.5, 6.3), (38.9, 0.0, 6.2), (38.4, 3.5, 6.3)], 1.05, segs=10, uv_rect=UV_RUBBER_CAP)

    # 5) Rear tubular bumper guard behind twin boosters
    rear_lo = [
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
        (-41.5, -10.8, 12.2),
        (-44.0, -5.8,  12.6),
        (-44.4,  0.0,  12.8),
        (-44.0,  5.8,  12.6),
        (-41.5, 10.8,  12.2),
        (-33.5, 11.8,  10.2),
    ]
    add_tube_ex(ch, catmull_rom_chain(rear_lo, 3), 0.82, segs=10, uv_rect=UV_STAINLESS)
    add_tube_ex(ch, catmull_rom_chain(rear_hi, 3), 0.76, segs=10, uv_rect=UV_STAINLESS)
    for y_st in (-10.5, -4.5, 4.5, 10.5):
        x_lo = -42.4 if abs(y_st) > 8 else -44.6
        add_tube_ex(ch, [(x_lo, y_st, 7.1), (x_lo + 0.6, y_st, 12.4)], 0.62, segs=8, uv_rect=UV_STAINLESS)

    # 6) Chassis crossmembers & Steering A-frame hoop (open footwell below Z=14)
    for x_cb, y_span, z_cb in ((-34.0, 11.6, 5.6), (-20.0, 13.6, 5.6), (-9.0, 14.8, 5.6), (8.0, 14.6, 5.6), (31.5, 8.0, 7.2)):
        add_tube_ex(ch, [(x_cb, -y_span, z_cb), (x_cb, y_span, z_cb)], 0.74, segs=8, uv_rect=UV_STAINLESS)

    hoop = [
        (24.5, -9.5,  6.8),
        (23.5, -5.2, 16.5),
        (17.5, -2.0, 20.8),
        (16.6,  0.0, 21.4),
        (17.5,  2.0, 20.8),
        (23.5,  5.2, 16.5),
        (24.5,  9.5,  6.8),
    ]
    add_tube_ex(ch, catmull_rom_chain(hoop, 2), 0.76, segs=8, uv_rect=UV_STAINLESS)

    # 7) Matte dark rubberized/anodized floorpan tray (below Z=5.2, clear of pedals/bar)
    ch.add_chamfer_box(-16.0, 13.5, -13.0, 13.0, 4.5, 5.1, ch=0.18, uv_rect=UV_RUBBER_CAP)
    ch.add_chamfer_box(13.5, 29.0, -8.5, 8.5, 4.6, 5.2, ch=0.18, uv_rect=UV_RUBBER_CAP)
    return ch


def build_seat():
    """Classic off-white & Mega-Man-cobalt-blue ribbed racing seat, 100% clear of 22x28u torso box."""
    st = MeshPart("seat")
    stations = [
        (-2.0,   7.8, 1.4, 11.2, 12.6, 0.0),
        (-5.5,   9.4, 2.2, 11.3, 12.9, 0.0),
        (-9.0,   9.5, 2.6, 11.4, 13.1, 0.0),
        (-13.2,  9.5, 3.0, 11.4, 13.2, 0.0),
        (-16.6, 12.8, 3.4, 11.3, 13.2, 2.0),
        (-18.6, 17.6, 3.6, 11.3, 13.2, 2.8),
        (-20.4, 22.2, 2.8, 11.2, 12.9, 2.0),
        (-21.8, 25.8, 1.2,  9.6, 11.6, 0.6),
    ]
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
            y_out = y + sgn * 0.18 if abs(y) > 0.1 else 0.0
            row_out.append((x + dx - (1.3 if is_back else 0.3), y_out, z + dz - (0.3 if is_back else 1.3)))
        inner_grid.append(row_in)
        outer_grid.append(row_out)

    add_grid_patch(st, inner_grid, uv_rect=UV_SEAT_WHITE, flip_n=False)
    add_grid_patch(st, outer_grid, uv_rect=UV_SEAT_SHELL, flip_n=True)

    nr, nc = len(stations), len(y_t)
    for r in range(nr - 1):
        st.add_quad(
            inner_grid[r][nc - 1], outer_grid[r][nc - 1],
            outer_grid[r + 1][nc - 1], inner_grid[r + 1][nc - 1],
            (UV_SEAT_BLUE[0], UV_SEAT_BLUE[1]), (UV_SEAT_BLUE[2], UV_SEAT_BLUE[1]),
            (UV_SEAT_BLUE[2], UV_SEAT_BLUE[3]), (UV_SEAT_BLUE[0], UV_SEAT_BLUE[3]),
        )
        st.add_quad(
            inner_grid[r][0], inner_grid[r + 1][0],
            outer_grid[r + 1][0], outer_grid[r][0],
            (UV_SEAT_BLUE[0], UV_SEAT_BLUE[1]), (UV_SEAT_BLUE[2], UV_SEAT_BLUE[1]),
            (UV_SEAT_BLUE[2], UV_SEAT_BLUE[3]), (UV_SEAT_BLUE[0], UV_SEAT_BLUE[3]),
        )
    for c in range(nc - 1):
        st.add_quad(
            inner_grid[0][c], inner_grid[0][c + 1], outer_grid[0][c + 1], outer_grid[0][c],
            (UV_SEAT_BLUE[0], UV_SEAT_BLUE[1]), (UV_SEAT_BLUE[2], UV_SEAT_BLUE[1]),
            (UV_SEAT_BLUE[2], UV_SEAT_BLUE[3]), (UV_SEAT_BLUE[0], UV_SEAT_BLUE[3]),
        )
        st.add_quad(
            inner_grid[nr - 1][c], outer_grid[nr - 1][c],
            outer_grid[nr - 1][c + 1], inner_grid[nr - 1][c + 1],
            (UV_SEAT_CREST[0], UV_SEAT_CREST[1]), (UV_SEAT_CREST[0], UV_SEAT_CREST[3]),
            (UV_SEAT_CREST[2], UV_SEAT_CREST[3]), (UV_SEAT_CREST[2], UV_SEAT_CREST[1]),
        )

    # Embroidered cobalt-blue headrest crest plate on upper backrest
    st.add_chamfer_box(-22.2, -20.8, -6.5, 6.5, 22.0, 25.4, ch=0.25, uv_rect=UV_SEAT_CREST)
    # Cobalt-blue outer side-bolster trim bars & under-seat rails
    for sgn in (-1.0, +1.0):
        st.add_chamfer_box(-13.5, -5.0, sgn * 6.2 - 0.7, sgn * 6.2 + 0.7, 5.1, 8.8, ch=0.2, uv_rect=UV_SEAT_SHELL)
        st.add_chamfer_box(-13.0, -3.5, sgn * 12.8 - 0.45, sgn * 12.8 + 0.45, 9.6, 12.2, ch=0.2, uv_rect=UV_SEAT_BLUE)
    return st


def build_steering():
    """Stainless T-steering column + 3-spoke brushed stainless wheel with black rubber grip at (13, 0, 24)."""
    sw = MeshPart("chrome_bar")
    cx, cy, cz = STEER_POS["x"], STEER_POS["y"], STEER_POS["z"]
    base_pt = (23.0, 0.0, 9.2)
    top_pt = (cx, cy, cz)
    axis = vnorm(vsub(top_pt, base_pt))

    # 1) Stainless steering shaft + lower U-joint + T-steering cross-brace collar
    add_tube_ex(sw, [base_pt, top_pt], 0.72, segs=10, uv_rect=UV_STAINLESS)
    sw.add_lathe(base_pt, axis, [(-1.0, 0.0, 0.0), (-1.0, 1.3, 0.2), (1.4, 1.3, 0.8), (1.4, 0.0, 1.0)], segs=12, uv_rect=UV_HEX_ZINC)
    collar_pt = vlerp(base_pt, top_pt, 0.68)
    sw.add_lathe(collar_pt, axis, [(-1.2, 0.0, 0.0), (-1.2, 1.45, 0.2), (1.2, 1.45, 0.8), (1.2, 0.0, 1.0)], segs=14, uv_rect=UV_STAINLESS)
    # Transverse T-column brace bar tying shaft to steering hoop
    add_tube_ex(sw, [(collar_pt[0], -3.8, collar_pt[2]), (collar_pt[0], +3.8, collar_pt[2])], 0.56, segs=8, uv_rect=UV_STAINLESS)

    # 2) Steering wheel rim (ribbed black rubber) + 3 stainless spokes + mirror-chrome central boss
    X_w, Y_w, Z_w = basis_from_axis(axis, up_hint=(0.0, 0.0, 1.0))
    wheel_r = 6.2
    n_rim = 28
    rim_pts = [
        vadd(top_pt, vadd(vmul(Y_w, wheel_r * math.cos(2.0 * math.pi * i / n_rim)),
                          vmul(Z_w, wheel_r * math.sin(2.0 * math.pi * i / n_rim))))
        for i in range(n_rim)
    ]
    add_tube_ex(sw, rim_pts, 0.78, segs=10, uv_rect=UV_RUBBER_CAP, closed=True)

    for sp_deg in (25.0, 155.0, 270.0):
        sr = math.radians(sp_deg)
        dir_r = vadd(vmul(Y_w, math.cos(sr)), vmul(Z_w, math.sin(sr)))
        p_in = vadd(top_pt, vmul(dir_r, 1.4))
        p_out = vadd(top_pt, vmul(dir_r, wheel_r - 0.5))
        add_tube_ex(sw, [p_in, p_out], (0.62, 0.28), segs=6, uv_rect=UV_STAINLESS)

    sw.add_lathe(
        top_pt, axis,
        [
            (-1.2, 0.0,  0.05),
            (-1.2, 1.85, 0.25),
            (0.45, 2.05, 0.65),
            (0.65, 1.80, 0.85),
            (0.70, 0.0,  0.96),
        ],
        segs=18, uv_rect=UV_CHROME_BAR,
    )
    return sw


def build_booster():
    """Rear twin mirror-chrome booster canisters, TIG clamp bands & flared exhaust nozzles."""
    bs = MeshPart("chrome_bar")

    for tip in EXHAUST_TIPS:
        y_off = tip["y"]
        tip_pos = (tip["x"], tip["y"], tip["z"])
        tip_dir = vnorm((tip["dx"], tip["dy"], tip["dz"]))  # points backward (-X, +Z)
        fwd_dir = vmul(tip_dir, -1.0)

        # Exhaust nozzle throat starts 6.0u forward from tip_pos; canister runs 13.0u forward from there
        nozzle_start = vsub(tip_pos, vmul(tip_dir, 6.0))
        can_front = vsub(tip_pos, vmul(tip_dir, 18.8))

        # 1) Mirror-chrome booster pressure cylinder with hemispherical nose dome
        bs.add_lathe(
            can_front, tip_dir,
            [
                (0.0,  0.00, 0.04),
                (0.4,  1.65, 0.10),
                (1.2,  2.75, 0.18),
                (2.2,  3.10, 0.28),
                (11.6, 3.10, 0.78),
                (12.8, 2.35, 0.90),
                (13.0, 1.80, 0.96),
            ],
            segs=22, uv_rect=UV_CHROME_BAR,
        )

        # 2) Twin brushed-stainless retaining clamp bands & chassis mounting struts
        for d_band in (4.2, 9.8):
            bp = vadd(can_front, vmul(tip_dir, d_band))
            bs.add_lathe(
                bp, tip_dir,
                [(-0.45, 3.10, 0.08), (-0.45, 3.35, 0.20), (+0.45, 3.35, 0.80), (+0.45, 3.10, 0.92)],
                segs=20, uv_rect=UV_STAINLESS,
            )
        add_tube_ex(bs, [(can_front[0] - 4.0, y_off, 14.5), (-32.0, y_off * 1.15, 6.0)], 0.62, segs=8, uv_rect=UV_STAINLESS)
        add_tube_ex(bs, [(-36.5, y_off, 14.8), (-39.5, y_off * 1.15, 6.8)], 0.56, segs=8, uv_rect=UV_STAINLESS)

        # 3) Flared convergent-divergent stainless exhaust bell nozzle ending at tip_pos
        bs.add_lathe(
            nozzle_start, tip_dir,
            [
                (0.0, 1.80, 0.04),
                (1.4, 1.55, 0.22),
                (3.4, 2.15, 0.52),
                (5.6, 2.75, 0.86),
                (6.0, 2.80, 0.94),
                (6.0, 2.40, 0.98),
            ],
            segs=20, uv_rect=UV_STAINLESS,
        )
        # Dark interior nozzle throat bore
        bs.add_lathe(
            vsub(tip_pos, vmul(tip_dir, 1.8)), tip_dir,
            [(0.0, 0.0, 0.1), (0.0, 1.45, 0.4), (1.8, 2.40, 0.95)],
            segs=16, uv_rect=UV_RUBBER_CAP,
        )

    # Transverse stainless fuel-balance manifold linking left & right canisters
    add_tube_ex(bs, [(-27.2, -7.5, 14.3), (-27.2, +7.5, 14.3)], 0.65, segs=8, uv_rect=UV_HEX_ZINC)
    add_tube_ex(bs, [(-34.0, -7.5, 14.8), (-34.0, +7.5, 14.8)], 0.58, segs=8, uv_rect=UV_STAINLESS)
    return bs


def build_shrapnel():
    """Throttle/brake foot pedals (clear of central front_bar) + chain guard + front collar brackets."""
    sh = MeshPart("chrome_bar")
    # Foot pedals at X=+24.2, Y=+/-6.2 (|Y|=5.1..7.3, cleanly outside central front_bar |Y|<=2.9)
    for sgn in (-1.0, +1.0):
        sh.add_chamfer_box(23.6, 25.0, sgn * 6.2 - 1.1, sgn * 6.2 + 1.1, 6.0, 11.0, ch=0.18, uv_rect=UV_RUBBER_CAP)
    # Billet rear drive-chain guard cover (Y=-10.5)
    sh.add_chamfer_box(-31.5, -22.5, -11.4, -9.8, 13.6, 16.0, ch=0.22, uv_rect=UV_HEX_ZINC)
    # Twin front clamp gusset plates flanking the T-collar
    for sgn in (-1.0, +1.0):
        sh.add_chamfer_box(28.5, 33.0, sgn * 5.2 - 0.6, sgn * 5.2 + 0.6, 11.2, 12.6, ch=0.18, uv_rect=UV_STAINLESS)
    return sh


# ---------------------------------------------------------------------------
# Dynamic Twin Flame Plumes & Explosion Fireball (Fixed Topology)
# ---------------------------------------------------------------------------
def _make_flame_frame(is_core, phase_01, plume_len, plume_rad, blast_rad, tip_specs, blast_center):
    """Fixed-topology frame for flame_outer or flame_core across BOTH twin exhaust tips + blast sphere."""
    fp = MeshPart("flame_core" if is_core else "flame_outer")
    uv_plume = UV_FLAME_CORE if is_core else UV_FLAME_OUTER
    uv_blast = UV_BLAST_CORE if is_core else UV_BLAST_OUTER
    u0, v0, u1, v1 = uv_plume
    active_p = plume_len > 0.05
    active_b = blast_rad > 0.05
    park_pt = blast_center if active_b else (-38.0, 0.0, 15.0)

    n_rings = 14
    segs = 10
    cols = segs + 1

    # --- Sub-mesh A: Twin exhaust plumes ---
    for tip_idx, (tip_pos, tip_dir) in enumerate(tip_specs):
        X, Y, Z = basis_from_axis(tip_dir, up_hint=(0.0, 0.0, 1.0))
        ph_shift = tip_idx * 1.4
        ring_bases = []
        for i in range(n_rings):
            t = i / float(n_rings - 1)
            if active_p:
                env = math.sin(min(1.0, t * 2.2) * math.pi * 0.5) * ((1.0 - t) ** 0.72)
                pulse = 1.0 + 0.24 * math.sin(t * 11.0 - phase_01 * 4.0 * math.pi + ph_shift)
                if is_core:
                    pulse += 0.20 * math.cos(t * 18.0 - phase_01 * 6.0 * math.pi + ph_shift)
                r_ring = max(0.08, plume_rad * env * pulse)
                whip_y = (1.5 if not is_core else 0.65) * (t ** 1.3) * math.sin(t * 7.5 - phase_01 * 4.0 * math.pi + ph_shift)
                whip_z = (1.3 if not is_core else 0.55) * (t ** 1.3) * math.cos(t * 6.5 - phase_01 * 4.0 * math.pi + ph_shift)
                c_pt = vadd(tip_pos, vadd(vmul(X, t * plume_len), vadd(vmul(Y, whip_y), vmul(Z, whip_z))))
            else:
                r_ring = 0.002
                c_pt = vadd(park_pt, vmul(X, t * 0.004))

            rb = len(fp.verts)
            ring_bases.append(rb)
            tv = v0 + (v1 - v0) * t
            for j in range(cols):
                th = 2.0 * math.pi * (j / float(segs))
                cth, sth = math.cos(th), math.sin(th)
                jag = (1.0 + 0.18 * math.sin(th * 3.0 + t * 8.0 - phase_01 * 2.0 * math.pi + ph_shift)) if active_p else 1.0
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

        # 2 crossed volumetric flame ribbons per nozzle
        n_fin = 10
        for axis_a, axis_b in ((Y, Z), (Z, Y)):
            prev_l = prev_r = None
            for i in range(n_fin):
                t = i / float(n_fin - 1)
                if active_p:
                    env = math.sin(min(1.0, t * 2.5) * math.pi * 0.5) * ((1.0 - t) ** 0.65)
                    w = max(0.08, plume_rad * 1.25 * env * (1.0 + 0.25 * math.sin(t * 9.0 - phase_01 * 4.0 * math.pi + ph_shift)))
                    whip = 1.1 * (t ** 1.3) * math.sin(t * 7.0 - phase_01 * 4.0 * math.pi + ph_shift)
                    c_pt = vadd(tip_pos, vadd(vmul(X, t * plume_len * 1.04), vmul(axis_a, whip)))
                else:
                    w = 0.002
                    c_pt = vadd(park_pt, vmul(X, t * 0.004))
                tv = v0 + (v1 - v0) * t
                il = len(fp.verts)
                fp.verts += [vsub(c_pt, vmul(axis_a, w)), vadd(c_pt, vmul(axis_a, w))]
                n_fin_v = vnorm(axis_b)
                fp.norms += [n_fin_v, n_fin_v]
                fp.st += [(u0, tv), (u1, tv)]
                if prev_l is not None:
                    fp.tris += [
                        (prev_l, prev_r, il + 1), (prev_l, il + 1, il),
                        (prev_l, il + 1, prev_r), (prev_l, il, il + 1),
                    ]
                prev_l, prev_r = il, il + 1

    # --- Sub-mesh B: Explosion fireball starburst ---
    bu0, bv0, bu1, bv1 = uv_blast
    n_lat, n_lon = 8, 12
    b_cols = n_lon + 1
    b_base = len(fp.verts)
    r_use = blast_rad if active_b else 0.002
    ref_tip_pos, ref_tip_dir = tip_specs[0]
    c_use = blast_center if active_b else (vsub(ref_tip_pos, ref_tip_dir) if active_p else park_pt)

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


def _simulate_explosion_group(parts, init_pos_offset, init_ry, init_pivot, vel0, ang_vel0, n_frames=20, shared_c0=None):
    """20-frame rigid-body ballistic trajectory for one or more co-moving parts with ground bounce (z >= 0.5)."""
    bases = [_xform_vn(p, offset=init_pos_offset, ry=init_ry, pivot=init_pivot) for p in parts]
    if shared_c0 is not None:
        c0 = shared_c0
    else:
        all_p = [pt for vv, _ in bases for pt in vv]
        n = len(all_p)
        c0 = (sum(p[0] for p in all_p) / n, sum(p[1] for p in all_p) / n, sum(p[2] for p in all_p) / n)
    rels = [[(p[0] - c0[0], p[1] - c0[1], p[2] - c0[2]) for p in vv] for vv, _ in bases]

    pos = list(c0)
    vel = list(vel0)
    ang = [0.0, 0.0, 0.0]
    w = list(ang_vel0)
    dt = 0.085
    grav = -145.0
    out_per_part = [[] for _ in parts]

    for k in range(n_frames):
        step_dt = dt * (0.45 if k == 0 else 1.0)
        vel[2] += grav * step_dt
        pos[0] += vel[0] * step_dt
        pos[1] += vel[1] * step_dt
        pos[2] += vel[2] * step_dt
        ang[0] += w[0] * step_dt
        ang[1] += w[1] * step_dt
        ang[2] += w[2] * step_dt

        step_vv = []
        step_nn = []
        min_z = 1e9
        for rel_v, (_, base_nn) in zip(rels, bases):
            vv_r, nn_r = [], []
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
            step_vv.append(vv_r)
            step_nn.append(nn_r)

        if min_z < 0.5:
            shift = 0.5 - min_z
            pos[2] += shift
            step_vv = [[(p[0], p[1], p[2] + shift) for p in vv_r] for vv_r in step_vv]
            if vel[2] < 0.0:
                vel[2] = -0.52 * vel[2]
                vel[0] *= 0.80
                vel[1] *= 0.80
                w[0] *= 0.72
                w[1] *= 0.72
                w[2] *= 0.72

        for idx in range(len(parts)):
            out_per_part[idx].append((step_vv[idx], step_nn[idx]))
    return out_per_part


def build_model():
    chassis = build_chassis()
    front_bar = build_front_bar()
    t_collar = build_t_collar()
    seat = build_seat()
    steering = build_steering()
    booster = build_booster()
    shrapnel = build_shrapnel()

    w_fl_wp, w_fl_hp = build_pneumatic_wheel(+1, WHEEL_FRONT_R, WHEEL_FRONT_HW, segs=32)
    w_fr_wp, w_fr_hp = build_pneumatic_wheel(-1, WHEEL_FRONT_R, WHEEL_FRONT_HW, segs=32)
    w_rl_wp, w_rl_hp = build_pneumatic_wheel(+1, WHEEL_REAR_R,  WHEEL_REAR_HW,  segs=32)
    w_rr_wp, w_rr_hp = build_pneumatic_wheel(-1, WHEEL_REAR_R,  WHEEL_REAR_HW,  segs=32)

    wheel_specs = {
        "wheel_fl": (w_fl_wp, w_fl_hp, "wheel_fl_hw", (WHEEL_FRONT_X, +WHEEL_FRONT_Y, WHEEL_FRONT_R)),
        "wheel_fr": (w_fr_wp, w_fr_hp, "wheel_fr_hw", (WHEEL_FRONT_X, -WHEEL_FRONT_Y, WHEEL_FRONT_R)),
        "wheel_rl": (w_rl_wp, w_rl_hp, "wheel_rl_hw", (WHEEL_REAR_X,  +WHEEL_REAR_Y,  WHEEL_REAR_R)),
        "wheel_rr": (w_rr_wp, w_rr_hp, "wheel_rr_hw", (WHEEL_REAR_X,  -WHEEL_REAR_Y,  WHEEL_REAR_R)),
    }

    body_parts = {
        "chassis": chassis,
        "front_bar": front_bar,
        "t_collar": t_collar,
        "seat": seat,
        "steering": steering,
        "booster": booster,
        "shrapnel": shrapnel,
    }

    all_names = (
        list(body_parts.keys())
        + list(wheel_specs.keys())
        + [spec[2] for spec in wheel_specs.values()]
        + ["flame_outer", "flame_core"]
    )
    surf_frames = {name: [] for name in all_names}
    frame_names = []
    squat_pivot = (WHEEL_REAR_X, 0.0, WHEEL_REAR_R)
    tips_base = [
        ((t["x"], t["y"], t["z"]), vnorm((t["dx"], t["dy"], t["dz"])))
        for t in EXHAUST_TIPS
    ]

    # --- Frames 0..11: idle_00..idle_11 ---
    for k in range(12):
        frame_names.append(f"idle_{k:02d}")
        ph = 2.0 * math.pi * (k / 12.0)
        dz_ch = 0.14 * math.sin(ph * 2.0)
        dz_bst = 0.28 * math.sin(ph * 3.0) + 0.08 * math.cos(ph)
        dx_bar = 0.09 * math.cos(ph * 2.0)
        for name, part in body_parts.items():
            if name == "booster":
                off = (-0.06 * math.cos(ph * 2.0), 0.0, dz_bst)
            elif name == "front_bar":
                off = (dx_bar, 0.0, dz_ch + 0.08 * math.sin(ph * 3.0))
            else:
                off = (0.0, 0.0, dz_ch)
            surf_frames[name].append(_xform_vn(part, offset=off))
        for wname, (wpart, hpart, hwname, wpos) in wheel_specs.items():
            surf_frames[wname].append(_xform_vn(wpart, offset=wpos))
            surf_frames[hwname].append(_xform_vn(hpart, offset=wpos))
        tips_cur = [(vadd(tp, (-0.06 * math.cos(ph * 2.0), 0.0, dz_bst)), td) for tp, td in tips_base]
        fo_v, fo_n, fo_t, fo_st = _make_flame_frame(False, k / 12.0, 0.0, 0.0, 0.0, tips_cur, (0.0, 0.0, 14.0))
        fc_v, fc_n, fc_t, fc_st = _make_flame_frame(True,  k / 12.0, 0.0, 0.0, 0.0, tips_cur, (0.0, 0.0, 14.0))
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))
        if k == 0:
            flame_outer_topo = (fo_t, fo_st)
            flame_core_topo = (fc_t, fc_st)

    # --- Frames 12..27: fast_00..fast_15 (wheels spin 2*pi = 360 deg forward) ---
    for k in range(16):
        frame_names.append(f"fast_{k:02d}")
        ph = 2.0 * math.pi * (k / 16.0)
        dz_ch = 0.32 * math.sin(ph * 2.0) + 0.14 * math.cos(ph * 4.0)
        ry_ch = 0.24 * math.sin(ph * 2.0)
        rx_ch = 0.18 * math.cos(ph)
        for name, part in body_parts.items():
            dz_extra = 0.18 * math.sin(ph * 4.0) if name in ("booster", "front_bar") else 0.0
            surf_frames[name].append(_xform_vn(part, offset=(0.0, 0.0, dz_ch + dz_extra), rx=rx_ch, ry=ry_ch, pivot=(0.0, 0.0, 8.0)))
        spin_deg = -360.0 * (k / 16.0)
        for wname, (wpart, hpart, hwname, wpos) in wheel_specs.items():
            surf_frames[wname].append(_xform_vn(wpart, offset=wpos, ry=spin_deg))
            surf_frames[hwname].append(_xform_vn(hpart, offset=wpos, ry=spin_deg))
        tips_cur = [(vadd(tp, (0.0, 0.0, dz_ch)), td) for tp, td in tips_base]
        fo_v, fo_n, _, _ = _make_flame_frame(False, k / 16.0, 0.0, 0.0, 0.0, tips_cur, (0.0, 0.0, 14.0))
        fc_v, fc_n, _, _ = _make_flame_frame(True,  k / 16.0, 0.0, 0.0, 0.0, tips_cur, (0.0, 0.0, 14.0))
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))

    # --- Frames 28..43: super_00..super_15 (wheels spin 4*pi = 720 deg, +1.8 deg rear squat / nose lift, roaring twin flames!) ---
    for k in range(16):
        frame_names.append(f"super_{k:02d}")
        ph = 2.0 * math.pi * (k / 16.0)
        dz_ch = 0.24 * math.sin(ph * 4.0)
        squat_ry = 1.8 + 0.20 * math.sin(ph * 2.0)  # +ry lifts +X nose & silver bar UP!
        for name, part in body_parts.items():
            dz_extra = 0.20 * math.sin(ph * 6.0) if name == "booster" else 0.0
            surf_frames[name].append(_xform_vn(part, offset=(0.0, 0.0, dz_ch + dz_extra), ry=squat_ry, pivot=squat_pivot))
        spin_deg = -720.0 * (k / 16.0)
        for wname, (wpart, hpart, hwname, wpos) in wheel_specs.items():
            surf_frames[wname].append(_xform_vn(wpart, offset=wpos, ry=spin_deg))
            surf_frames[hwname].append(_xform_vn(hpart, offset=wpos, ry=spin_deg))

        tips_sq = []
        for tp, td in tips_base:
            tp_rel = vsub(tp, squat_pivot)
            tp_sq = vadd(rot_y(tp_rel, squat_ry), vadd(squat_pivot, (0.0, 0.0, dz_ch)))
            td_sq = vnorm(rot_y(td, squat_ry))
            tips_sq.append((tp_sq, td_sq))

        len_out = 28.0 + 4.0 * math.sin(ph * 2.0) + 1.5 * math.cos(ph * 4.0)  # 23..33u (>15u!)
        len_cor = 17.0 + 2.6 * math.cos(ph * 3.0)
        fo_v, fo_n, _, _ = _make_flame_frame(False, k / 16.0, len_out, 2.75, 0.0, tips_sq, (0.0, 0.0, 14.0))
        fc_v, fc_n, _, _ = _make_flame_frame(True,  k / 16.0, len_cor, 1.45, 0.0, tips_sq, (0.0, 0.0, 14.0))
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))

    # --- Frames 44..63: explode_00..explode_19 (catastrophic explosion w/ tumbling & ground bounce) ---
    trajectories = {
        "chassis":   ((  -8.0,   4.0,  78.0), ( 110.0,  -85.0,  160.0)),
        "front_bar": (( 112.0,   8.0, 142.0), ( 240.0,  120.0,  280.0)),
        "t_collar":  ((  58.0, -34.0, 162.0), (-310.0,  260.0,  340.0)),
        "seat":      (( -18.0,  14.0, 132.0), ( 220.0,  160.0, -140.0)),
        "steering":  ((  38.0, -24.0, 148.0), (-260.0,  190.0,  280.0)),
        "booster":   (( -92.0, -22.0, 128.0), (-290.0,  220.0, -240.0)),
        "shrapnel":  ((  48.0,  46.0, 168.0), ( 340.0, -280.0,  360.0)),
        "wheel_fl":  ((  64.0,  88.0, 108.0), ( 260.0,  320.0,  190.0)),
        "wheel_fr":  ((  68.0, -92.0, 114.0), (-240.0,  340.0, -210.0)),
        "wheel_rl":  (( -72.0,  95.0, 102.0), ( 290.0, -280.0,  220.0)),
        "wheel_rr":  (( -76.0, -94.0, 106.0), (-270.0, -310.0, -240.0)),
    }
    for k in range(20):
        frame_names.append(f"explode_{k:02d}")
    for name, part in body_parts.items():
        v0, w0 = trajectories[name]
        surf_frames[name] += _simulate_explosion_group([part], (0.0, 0.0, 0.0), 1.8, squat_pivot, v0, w0, n_frames=20)[0]
    for wname, (wpart, hpart, hwname, wpos) in wheel_specs.items():
        v0, w0 = trajectories[wname]
        w_frames, hw_frames = _simulate_explosion_group([wpart, hpart], wpos, 0.0, (0.0, 0.0, 0.0), v0, w0, n_frames=20, shared_c0=wpos)
        surf_frames[wname] += w_frames
        surf_frames[hwname] += hw_frames

    # Fireball flashes BIG at frames 44..47 (k=0..3), shrinks 48..49, collapsed (<0.05u) by 50 (k>=6)
    blast_outer_radii = [22.0, 34.0, 37.0, 30.0, 15.0, 5.5] + [0.0] * 14
    blast_core_radii  = [16.0, 25.0, 23.0, 16.0,  7.0, 2.0] + [0.0] * 14
    for k in range(20):
        c_blast = (0.0, 0.0, 14.0 + k * 2.5)
        fo_v, fo_n, _, _ = _make_flame_frame(False, k / 20.0, 0.0, 0.0, blast_outer_radii[k], tips_base, c_blast)
        fc_v, fc_n, _, _ = _make_flame_frame(True,  k / 20.0, 0.0, 0.0, blast_core_radii[k],  tips_base, c_blast)
        surf_frames["flame_outer"].append((fo_v, fo_n))
        surf_frames["flame_core"].append((fc_v, fc_n))

    # Assemble MD3 surface dicts
    surfaces = []
    for name, part in body_parts.items():
        surfaces.append(dict(name=name, shader=SHADERS[name], tris=part.tris, st=part.st, frames=surf_frames[name]))
    for wname, (wpart, hpart, hwname, _) in wheel_specs.items():
        surfaces.append(dict(name=wname,  shader=SHADERS[wname],  tris=wpart.tris, st=wpart.st, frames=surf_frames[wname]))
        surfaces.append(dict(name=hwname, shader=SHADERS[hwname], tris=hpart.tris, st=hpart.st, frames=surf_frames[hwname]))
    surfaces.append(dict(name="flame_outer", shader=SHADERS["flame_outer"], tris=flame_outer_topo[0], st=flame_outer_topo[1], frames=surf_frames["flame_outer"]))
    surfaces.append(dict(name="flame_core",  shader=SHADERS["flame_core"],  tris=flame_core_topo[0],  st=flame_core_topo[1],  frames=surf_frames["flame_core"]))

    return dict(name="gokart_4", frame_names=frame_names, surfaces=surfaces)


# ---------------------------------------------------------------------------
# Metadata, Skin, Export & Verification
# ---------------------------------------------------------------------------
def write_skin_and_meta(model, progs_dir=PROGS_DIR, meta_dir=OUT_DIR):
    skin_path = os.path.join(progs_dir, "gokart_4.md3_0.skin")
    with open(skin_path, "w", encoding="ascii", newline="\n") as f:
        for s in model["surfaces"]:
            f.write(f"{s['name']},{s['shader']}\n")

    if meta_dir is None:
        return
    os.makedirs(meta_dir, exist_ok=True)
    meta = {
        "id": "kart4",
        "name": "Mega Man Classic Bar-Racer",
        "tagline": "Mirror-chrome front torpedo bar, TIG T-collar, 5-ribbed dish wheels & twin boosters",
        "palette": PALETTE,
        "description": (
            "Faithful 4-wheel go-kart evolution of the iconic BakersfieldQuake Mega Man contraption: "
            "a gleaming mirror-chrome bullet-nosed front silver torpedo bar (with ribbed black rubber rear cap) "
            "clamped by a TIG-welded stainless T-collar to the front cross-axle, swept stainless twin perimeter "
            "rails, 4 iconic 5-ribbed pneumatic tires on concave off-white steel dish rims with zinc hex nuts, "
            "yellow cotter pins & brass Schrader valves, an off-white & Mega-Man-cobalt-blue ribbed seat, "
            "stainless T-steering column, and twin rear chrome rocket boosters."
        ),
        "highlights": [
            ["Front Bar", "Mirror-chrome bullet-nosed torpedo bar (X=+11..+54) w/ rubber cap & TIG T-collar"],
            ["Wheels & Axles", "5-ribbed pneumatic tires on off-white dish rims w/ hex nuts, cotter pins & valves"],
            ["Booster & Fit", "Twin chrome rocket nozzles, 22x28u clear seated torso box & open footwell"],
        ],
        "seat_pos": SEAT_POS,
        "steer_pos": STEER_POS,
        "exhaust_tips": EXHAUST_TIPS,
        "textures": {
            "progs/gk4_chrome": "progs/gk4_chrome.png",
            "progs/gk4_wheel":  "progs/gk4_wheel.png",
            "progs/gk4_seat":   "progs/gk4_seat.png",
            "progs/gk4_flame":  "progs/gk4_flame.png",
        },
        "materials": {
            "progs/gk4_chrome": {"metallic": 0.90, "roughness": 0.14, "spec": 1.30},
            "progs/gk4_wheel":  {"metallic": 0.25, "roughness": 0.58, "spec": 0.42},
            "progs/gk4_seat":   {"metallic": 0.08, "roughness": 0.65, "spec": 0.28},
            "progs/gk4_flame":  {"metallic": 0.00, "roughness": 1.00, "spec": 0.00, "unlit": True, "additive": True},
        },
    }
    meta_path = os.path.join(meta_dir, "gokart_4_meta.json")
    with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)


def verify_md3(md3_path):
    m = md3lib.read(md3_path)
    assert m["nframes"] == 64, f"Expected 64 frames, got {m['nframes']}"
    expected_surfs = {
        "chassis", "front_bar", "t_collar", "seat", "steering", "booster",
        "wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr",
        "flame_outer", "flame_core", "shrapnel",
    }
    got_surfs = {s["name"] for s in m["surfaces"]}
    assert expected_surfs.issubset(got_surfs), f"Missing surfaces: {expected_surfs - got_surfs}"

    for s in m["surfaces"]:
        nv = len(s["st"])
        nt = len(s["tris"])
        assert 0 < nv <= 4096, f"{s['name']} nv={nv} > 4096"
        assert 0 < nt <= 8192, f"{s['name']} nt={nt} > 8192"
        assert s["shader"].startswith("progs/gk4_"), f"Bad shader {s['shader']}"
        for fi, (vv, nn) in enumerate(s["frames"]):
            for p, n in zip(vv, nn):
                assert all(math.isfinite(c) and abs(c) < 511.5 for c in p), f"Coord limit hit on {s['name']} f={fi}: {p}"
                assert all(math.isfinite(c) for c in n), f"Non-finite normal on {s['name']} f={fi}"

    for fi in range(64):
        all_z = [p[2] for s in m["surfaces"] for p in s["frames"][fi][0]]
        z_min = min(all_z)
        if fi <= 43:
            assert abs(z_min) <= 0.1, f"Frame {fi} z_min={z_min:.4f} != 0.0 +/- 0.1"
        else:
            assert z_min >= 0.48, f"Explosion frame {fi} z_min={z_min:.4f} < 0.5"

    f0_pts = [p for s in m["surfaces"] if not s["name"].startswith("flame_") for p in s["frames"][0][0]]
    xs = [p[0] for p in f0_pts]
    ys = [p[1] for p in f0_pts]
    zs = [p[2] for p in f0_pts]
    assert min(xs) >= -46.0 and max(xs) <= 55.0, f"X out of [-46, 55]: [{min(xs):.2f}, {max(xs):.2f}]"
    assert min(ys) >= -33.0 and max(ys) <= 33.0, f"Y out of [-33, 33]: [{min(ys):.2f}, {max(ys):.2f}]"

    fb_s = next(s for s in m["surfaces"] if s["name"] == "front_bar")
    fb_xs = [p[0] for p in fb_s["frames"][0][0]]
    assert max(fb_xs) > 42.0, f"front_bar max_x={max(fb_xs):.2f} <= 42"

    for fname in ("flame_outer", "flame_core"):
        fs = next(s for s in m["surfaces"] if s["name"] == fname)
        for fi in range(64):
            pts = fs["frames"][fi][0]
            fxs = [p[0] for p in pts]
            fys = [p[1] for p in pts]
            fzs = [p[2] for p in pts]
            span_x = max(fxs) - min(fxs)
            span_r = max(max(fys) - min(fys), max(fzs) - min(fzs))
            if fi <= 27 or fi >= 50:
                assert max(span_x, span_r) < 0.05, f"{fname} not collapsed at frame {fi}: span=({span_x:.3f}, {span_r:.3f})"
            elif 28 <= fi <= 43:
                assert span_x > 15.0, f"{fname} super plume too short at frame {fi}: {span_x:.2f}"
            elif 44 <= fi <= 47 and fname == "flame_outer":
                assert max(span_x, span_r) >= 35.0, f"Explosion fireball too small at frame {fi}: {max(span_x, span_r):.2f}"

    ch_s = next(s for s in m["surfaces"] if s["name"] == "chassis")
    cockpit_intruders = [p for p in ch_s["frames"][0][0] if -12.0 <= p[0] <= 12.0 and abs(p[1]) < 13.0 and p[2] > 5.5]
    assert not cockpit_intruders, f"Chassis intrudes into cockpit |Y|<13: {cockpit_intruders[:3]}"

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
    print(f"Front bar X=[{min(fb_xs):.2f}, {max(fb_xs):.2f}]")
    for s in m["surfaces"]:
        print(f"  {s['name']:12s} shader={s['shader']:18s} verts={len(s['st']):4d} tris={len(s['tris']):4d}")


def main(progs_dir=PROGS_DIR, meta_dir=OUT_DIR):
    build_all_textures(progs_dir=progs_dir)
    model = build_model()
    md3_path = os.path.join(progs_dir, "gokart_4.md3")
    md3lib.write(md3_path, model)
    write_skin_and_meta(model, progs_dir=progs_dir, meta_dir=meta_dir)
    verify_md3(md3_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build Go-Kart #4 MD3, skin, and textures.")
    p.add_argument("--out-dir", default=None, help="Output directory for MD3, skin, and PNGs")
    p.add_argument("--meta-dir", default=None, help="Optional directory for gokart_4_meta.json")
    args = p.parse_args()
    progs_dir = args.out_dir if args.out_dir is not None else PROGS_DIR
    meta_dir = args.meta_dir if args.meta_dir is not None else (OUT_DIR if args.out_dir is None else None)
    main(progs_dir=progs_dir, meta_dir=meta_dir)
