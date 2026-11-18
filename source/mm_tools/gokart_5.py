"""Procedural 3D MD3 Builder, High-Res Texture Generator & Animator for:
Go-Kart #5 ("Mega Man Twin-Dish Interceptor" — Mega-Man-Blue & Chrome Front-Bar Interceptor).

Outputs (owned exclusively by kart-5):
  - progs/gk5_chrome.png      (1024x1024 RGB: mirror-chrome bar, TIG T-collar, stainless axles, rubber cap, hardware)
  - progs/gk5_wheel.png       (1024x1024 RGB: 5-ribbed pneumatic tire tread, molded sidewall, off-white steel dish rim)
  - progs/gk5_body.png        (1024x1024 RGB: Mega-Man cobalt-blue fairing pods, cyan trim, white racing stripes, carbon belly)
  - progs/gk5_seat.png        (1024x1024 RGB: Mega-Blue & crisp white quilted bucket seat, cyan piping, '05' crest)
  - progs/gk5_steer.png       (1024x1024 RGB: stainless butterfly steering yoke, OLED telemetry dash, Mega-Blue grips)
  - progs/gk5_exhaust.png     (1024x1024 RGB: Mega-Buster chrome & cobalt exhaust cannons, heat-blued rings, cyan core)
  - progs/gk5_flame.png       (512x512 RGBA: additive shock-diamond cyan/white-hot Mega-Buster plasma plumes)
  - progs/gokart_5.md3        (64-frame IDP3 v15 model with 17 distinct surfaces)
  - progs/gokart_5.md3_0.skin (surface -> shader mapping)
  - source/mm_tools/out/gokart_5_meta.json

Usage:
  python source/mm_tools/gokart_5.py
"""
import argparse
import json
import math
import os
import struct
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
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
    vmul,
    vnorm,
    vsub,
)
from tank_geom_core import (
    build_pneumatic_wheel,
    build_t_collar as core_build_t_collar,
    build_tank_silver_bar,
)
import tank_tex_gen
from tank_tex_gen import (
    UV_CHROME_BAR,
    UV_COTTER_YEL,
    UV_HEX_ZINC,
    UV_RUBBER_CAP,
    UV_STAINLESS,
)

# ---------------------------------------------------------------------------
# Shared Coordinate & Player-Fit Constants (Quake units, +X fwd, +Y left, +Z up)
# ---------------------------------------------------------------------------
FRONT_WHEEL_X = 31.0
FRONT_WHEEL_Y = 24.0
FRONT_WHEEL_R = 8.8
FRONT_WHEEL_HW = 4.2

REAR_WHEEL_X = -28.0
REAR_WHEEL_Y = 27.2
REAR_WHEEL_R = 13.5
REAR_WHEEL_HW = 6.2

SEAT_POS = (-9.0, 0.0, 9.0)
STEER_POS = (13.0, 0.0, 24.0)

BAR_POS = (32.2, 0.0, 15.0)
BAR_TILT_DEG = 3.0  # +3 deg pitches +X up toward +Z

# Twin Mega-Buster exhaust mount & muzzle geometry (splayed outward & tilted slightly upward)
EXHAUST_MOUNTS = [
    {"origin": (-29.0, +7.8, 15.6), "ry": -6.0, "rz": -5.0, "len": 16.8},
    {"origin": (-29.0, -7.8, 15.6), "ry": -6.0, "rz": +5.0, "len": 16.8},
]


def _compute_exhaust_tips():
    tips = []
    for em in EXHAUST_MOUNTS:
        local_tip = (-em["len"], 0.0, 0.0)
        local_dir = (-1.0, 0.0, 0.0)
        pt = rot_z(rot_y(local_tip, em["ry"]), em["rz"])
        dv = vnorm(rot_z(rot_y(local_dir, em["ry"]), em["rz"]))
        tip_w = vadd(em["origin"], pt)
        tips.append({
            "x": round(tip_w[0], 3),
            "y": round(tip_w[1], 3),
            "z": round(tip_w[2], 3),
            "dx": round(dv[0], 4),
            "dy": round(dv[1], 4),
            "dz": round(dv[2], 4),
        })
    return tips


EXHAUST_TIPS = _compute_exhaust_tips()

FRAME_NAMES = (
    [f"idle_{i:02d}" for i in range(12)]
    + [f"fast_{i:02d}" for i in range(16)]
    + [f"super_{i:02d}" for i in range(16)]
    + [f"explode_{i:02d}" for i in range(20)]
)
assert len(FRAME_NAMES) == 64

UV_Q1 = (0.02, 0.02, 0.48, 0.48)
UV_Q2 = (0.52, 0.02, 0.98, 0.48)
UV_Q3 = (0.02, 0.52, 0.48, 0.98)
UV_Q4 = (0.52, 0.52, 0.98, 0.98)

UV_Q4_A = (0.52, 0.52, 0.73, 0.73)
UV_Q4_B = (0.77, 0.52, 0.98, 0.73)
UV_Q4_C = (0.52, 0.77, 0.73, 0.98)
UV_Q4_D = (0.77, 0.77, 0.98, 0.98)


# ---------------------------------------------------------------------------
# Procedural Texture Synthesis & Mega-Man Contraption Reuse
# ---------------------------------------------------------------------------
def _font(size, bold=True):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fbm(h, w, seed=55, octaves=(4, 8, 16, 32, 64)):
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


def _carbon_weave(h, w, scale=8, base_rgb=(16, 22, 34), hi_rgb=(36, 48, 68), noise=None):
    yy, xx = np.mgrid[0:h, 0:w]
    phase = (xx // scale + yy // scale) % 2
    sub_u = (xx % scale) / float(scale)
    sub_v = (yy % scale) / float(scale)
    sheen_a = np.sin(sub_u * math.pi) * 0.85 + 0.15
    sheen_b = np.sin(sub_v * math.pi) * 0.85 + 0.15
    w_fac = np.where(phase == 0, sheen_a, sheen_b * 0.75)
    out = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        out[..., c] = base_rgb[c] + (hi_rgb[c] - base_rgb[c]) * w_fac
    if noise is not None:
        out += noise[..., None] * 6.0
    return np.clip(out, 4, 255)


def _copy_mmt_textures(progs_dir):
    """Copies read-only progs/mmt_wheel.png and progs/mmt_chrome_bar.png to progs/gk5_*.png
    so scripts/gokart.shader never collides with scripts/mm_tank.shader.
    """
    src_wheel = os.path.join(progs_dir, "mmt_wheel.png")
    src_chrome = os.path.join(progs_dir, "mmt_chrome_bar.png")
    dst_wheel = os.path.join(progs_dir, "gk5_wheel.png")
    dst_chrome = os.path.join(progs_dir, "gk5_chrome.png")

    if os.path.isfile(src_wheel) and os.path.isfile(src_chrome):
        Image.open(src_wheel).convert("RGB").save(dst_wheel, "PNG", optimize=True)
        Image.open(src_chrome).convert("RGB").save(dst_chrome, "PNG", optimize=True)
    else:
        with tempfile.TemporaryDirectory() as tmp_mmt:
            p_wheel, _ = tank_tex_gen.build_wheel_textures(tmp_mmt)
            p_chrome, _ = tank_tex_gen.build_chrome_bar_textures(tmp_mmt)
            Image.open(p_wheel).convert("RGB").save(dst_wheel, "PNG", optimize=True)
            Image.open(p_chrome).convert("RGB").save(dst_chrome, "PNG", optimize=True)
    return dst_wheel, dst_chrome


def build_body_texture(progs_dir):
    """1024x1024 RGB: Mega-Man cobalt-blue metallic bodywork, cyan trim, white racing stripes,
    carbon-slate undertray, glowing cyan radiator slats, and '05' Interceptor markings.
    """
    W = H = 1024
    nf = _fbm(H, W, seed=501, octaves=(4, 8, 16, 32))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    # Q1: Sculpted Mega-Man Cobalt-Blue Nose Cowl & White/Cyan Racing Stripes
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    u = xx / 511.0
    v = yy / 511.0
    sheen = 0.88 + 0.12 * np.sin(v * math.pi) + 0.04 * nf[:512, :512]
    q1 = np.zeros((512, 512, 3), dtype=np.float32)
    q1[..., 0] = 16.0 * sheen
    q1[..., 1] = 82.0 * sheen
    q1[..., 2] = 212.0 * sheen
    # Crisp white center-double racing stripe + electric-cyan trim pinstripe
    white_band = np.exp(-((np.abs(v - 0.5) - 0.13) ** 2) / 0.0014)
    cyan_edge = np.exp(-((np.abs(v - 0.5) - 0.21) ** 2) / 0.0005)
    q1[..., 0] = np.clip(q1[..., 0] * (1.0 - white_band) + 236.0 * white_band + 0.0 * cyan_edge, 0, 255)
    q1[..., 1] = np.clip(q1[..., 1] * (1.0 - white_band) + 242.0 * white_band + 215.0 * cyan_edge, 0, 255)
    q1[..., 2] = np.clip(q1[..., 2] * (1.0 - white_band) + 250.0 * white_band + 255.0 * cyan_edge, 0, 255)
    im1 = Image.fromarray(q1.astype(np.uint8), mode="RGB")
    dr1 = ImageDraw.Draw(im1)
    dr1.text((38, 34), "MM-05", fill=(238, 245, 255), font=_font(44))
    dr1.text((38, 86), "INTERCEPTOR", fill=(0, 224, 255), font=_font(26))
    arr[:512, :512] = np.asarray(im1, dtype=np.float32)

    # Q2: Mega-Blue Side Fairing Pods w/ Crisp White Side Stripe & Electric Cyan Trim
    q2 = np.zeros((512, 512, 3), dtype=np.float32)
    q2[..., 0] = 14.0 * sheen
    q2[..., 1] = 74.0 * sheen
    q2[..., 2] = 202.0 * sheen
    # Diagonal racing stripe & cyan lower trim
    stripe_w = np.exp(-((v - (0.36 + 0.14 * u)) ** 2) / 0.0028)
    stripe_c = np.exp(-((v - (0.48 + 0.14 * u)) ** 2) / 0.0007) + np.exp(-((v - 0.84) ** 2) / 0.0012)
    for ch, wb, cb in ((0, 238, 0), (1, 244, 222), (2, 252, 255)):
        q2[..., ch] = np.clip(q2[..., ch] * (1.0 - stripe_w) + wb * stripe_w + cb * stripe_c, 0, 255)
    im2 = Image.fromarray(q2.astype(np.uint8), mode="RGB")
    dr2 = ImageDraw.Draw(im2)
    dr2.text((40, 32), "TWIN-DISH 05", fill=(238, 246, 255), font=_font(38))
    dr2.text((42, 78), "MEGA INTERCEPTOR", fill=(0, 228, 255), font=_font(22))
    for rx in range(44, 480, 62):
        dr2.ellipse((rx - 4, 466, rx + 4, 474), fill=(195, 212, 232), outline=(10, 35, 90))
    arr[:512, 512:] = np.asarray(im2, dtype=np.float32)

    # Q3: Dark Carbon-Slate Belly Pan & Venturi Diffuser
    q3 = _carbon_weave(512, 512, scale=8, base_rgb=(15, 21, 32), hi_rgb=(32, 44, 64), noise=nf[512:, :512])
    im3 = Image.fromarray(q3.astype(np.uint8), mode="RGB")
    dr3 = ImageDraw.Draw(im3)
    for yk in range(32, 512, 64):
        dr3.line((0, yk, 512, yk), fill=(26, 38, 58), width=2)
    dr3.rectangle((12, 438, 500, 468), fill=(0, 190, 245))
    arr[512:, :512] = np.asarray(im3, dtype=np.float32)

    # Q4_A: Cyan-Glow Radiator Intake Louvers
    im_rad = Image.new("RGB", (256, 256), (12, 18, 28))
    dr_rad = ImageDraw.Draw(im_rad)
    for xk in range(4, 256, 8):
        dr_rad.line((xk, 0, xk, 256), fill=(24, 34, 52), width=2)
    for yk in range(32, 236, 52):
        dr_rad.rectangle((10, yk - 10, 246, yk + 10), fill=(0, 145, 220))
        dr_rad.rectangle((10, yk - 4, 246, yk + 4), fill=(0, 238, 255))
        dr_rad.rectangle((10, yk - 1, 246, yk + 1), fill=(220, 255, 255))
    arr[512:768, 512:768] = np.asarray(im_rad, dtype=np.float32)

    # Q4_B: Pure Crisp Racing White Accent Trim
    arr[512:768, 768:] = 236.0 + nf[512:768, 768:, None] * 6.0

    # Q4_C: Electric-Cyan Dorsal Fin & Trim Accent
    arr[768:, 512:768, 0] = 6.0
    arr[768:, 512:768, 1] = 212.0 + nf[768:, 512:768] * 10.0
    arr[768:, 512:768, 2] = 252.0

    # Q4_D: Glowing Cyan LED Tail Light Matrix
    im_tl = Image.new("RGB", (256, 256), (10, 18, 34))
    dr_tl = ImageDraw.Draw(im_tl)
    for row in range(28, 228, 40):
        for col in range(28, 228, 40):
            dr_tl.ellipse((col, row, col + 26, row + 26), fill=(0, 235, 255), outline=(215, 255, 255))
    arr[768:, 768:] = np.asarray(im_tl, dtype=np.float32)

    out_path = os.path.join(progs_dir, "gk5_body.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_seat_texture(progs_dir):
    """1024x1024 RGB: Mega-Blue bucket shell, crisp white quilted cushion, cyan piping, '05' headrest."""
    W = H = 1024
    nf = _fbm(H, W, seed=502, octaves=(4, 8, 16, 32))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    # Q1: Deep Cobalt-Blue Bucket Seat Shell
    arr[:512, :512, 0] = np.clip(16.0 + nf[:512, :512] * 8.0, 8, 42)
    arr[:512, :512, 1] = np.clip(76.0 + nf[:512, :512] * 14.0, 40, 120)
    arr[:512, :512, 2] = np.clip(198.0 + nf[:512, :512] * 18.0, 140, 240)

    # Q2: Crisp Off-White Diamond-Quilted Seat Cushion w/ Cobalt Stitch
    q2 = np.full((512, 512, 3), 236.0, dtype=np.float32) + nf[:512, 512:, None] * 6.0
    im2 = Image.fromarray(np.clip(q2, 195, 252).astype(np.uint8), mode="RGB")
    dr2 = ImageDraw.Draw(im2)
    for k in range(-512, 1024, 64):
        dr2.line((k, 0, k + 512, 512), fill=(18, 92, 210), width=3)
        dr2.line((k, 512, k + 512, 0), fill=(18, 92, 210), width=3)
    dr2.rectangle((0, 0, 511, 20), fill=(0, 218, 255))
    dr2.rectangle((0, 492, 511, 511), fill=(0, 218, 255))
    arr[:512, 512:] = np.asarray(im2, dtype=np.float32)

    # Q3: Mega-Blue Side Bolsters + White & Cyan Piping
    q3 = np.zeros((512, 512, 3), dtype=np.float32)
    q3[..., 0] = 18.0 + nf[512:, :512] * 8.0
    q3[..., 1] = 104.0 + nf[512:, :512] * 12.0
    q3[..., 2] = 228.0 + nf[512:, :512] * 14.0
    im3 = Image.fromarray(np.clip(q3, 0, 255).astype(np.uint8), mode="RGB")
    dr3 = ImageDraw.Draw(im3)
    for yk in range(54, 460, 68):
        dr3.line((0, yk, 512, yk), fill=(10, 60, 165), width=6)
    dr3.rectangle((0, 0, 511, 22), fill=(240, 246, 255))
    dr3.rectangle((0, 488, 511, 511), fill=(0, 224, 255))
    arr[512:, :512] = np.asarray(im3, dtype=np.float32)

    # Q4: White & Mega-Blue Headrest Crest ("05")
    im4 = Image.new("RGB", (512, 512), (235, 242, 252))
    dr4 = ImageDraw.Draw(im4)
    dr4.rectangle((0, 0, 511, 96), fill=(16, 86, 215))
    dr4.rectangle((0, 416, 511, 511), fill=(16, 86, 215))
    dr4.rectangle((0, 96, 511, 118), fill=(0, 224, 255))
    dr4.rectangle((0, 394, 511, 416), fill=(0, 224, 255))
    dr4.ellipse((146, 146, 366, 366), fill=(14, 78, 205), outline=(0, 224, 255), width=10)
    dr4.text((196, 202), "05", fill=(242, 248, 255), font=_font(104))
    arr[512:, 512:] = np.asarray(im4, dtype=np.float32)

    out_path = os.path.join(progs_dir, "gk5_seat.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_steer_texture(progs_dir):
    """1024x1024 RGB: Brushed stainless butterfly yoke, glowing cyan OLED dash, Mega-Blue grips."""
    W = H = 1024
    nf = _fbm(H, W, seed=503, octaves=(4, 8, 16, 32))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    # Q1: Brushed Stainless Butterfly Faceplate + Anodized Dials
    u_s = np.linspace(0, 2 * math.pi, 512, dtype=np.float32)[None, :]
    st_m = 162.0 + 36.0 * np.cos(u_s) + 10.0 * nf[:512, :512]
    q1 = np.stack([st_m * 0.94, st_m * 0.98, st_m * 1.06], axis=-1)
    im1 = Image.fromarray(np.clip(q1, 30, 245).astype(np.uint8), mode="RGB")
    dr1 = ImageDraw.Draw(im1)
    for cx, cy, col, lbl in [
        (135, 175, (0, 225, 255), "BUSTER"),
        (375, 175, (20, 105, 245), "BOOST"),
        (165, 360, (0, 195, 255), "SYNC"),
        (345, 360, (240, 246, 255), "MODE"),
    ]:
        dr1.ellipse((cx - 46, cy - 46, cx + 46, cy + 46), fill=(18, 28, 44), outline=col, width=5)
        dr1.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=col)
        dr1.text((cx - 38, cy + 54), lbl, fill=(14, 30, 60), font=_font(22))
    arr[:512, :512] = np.asarray(im1, dtype=np.float32)

    # Q2: Glowing Cyan OLED Telemetry Dash & Shift Light Bar
    im2 = Image.new("RGB", (512, 512), (8, 14, 26))
    dr2 = ImageDraw.Draw(im2)
    for i in range(14):
        lx = 30 + i * 32
        col = (0, 238, 255) if i < 7 else ((240, 248, 255) if i < 11 else (30, 125, 255))
        dr2.ellipse((lx, 24, lx + 24, 66), fill=col, outline=(220, 250, 255))
    dr2.rectangle((22, 92, 490, 470), fill=(10, 24, 48), outline=(0, 224, 255), width=5)
    dr2.text((46, 124), "288 KM/H", fill=(0, 242, 255), font=_font(72))
    dr2.text((52, 236), "BUSTER MAX", fill=(238, 248, 255), font=_font(52))
    dr2.text((52, 338), "TWIN-DISH 05", fill=(85, 200, 255), font=_font(44))
    arr[:512, 512:] = np.asarray(im2, dtype=np.float32)

    # Q3: Mega-Man Cobalt-Blue Grips
    arr[512:, :512, 0] = np.clip(18.0 + nf[512:, :512] * 10.0, 8, 50)
    arr[512:, :512, 1] = np.clip(98.0 + nf[512:, :512] * 14.0, 50, 145)
    arr[512:, :512, 2] = np.clip(226.0 + nf[512:, :512] * 16.0, 175, 255)

    # Q4: Mirror-Polished Stainless Column
    arr[512:, 512:] = np.clip(q1, 30, 245)

    out_path = os.path.join(progs_dir, "gk5_steer.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_exhaust_texture(progs_dir):
    """1024x1024 RGB: Chrome Mega-Buster cannon barrel, cobalt-blue collector housing, cyan emitter core."""
    W = H = 1024
    nf = _fbm(H, W, seed=504, octaves=(4, 8, 16, 32))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    u = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]

    # Q1: Gleaming Chrome Mega-Buster Barrel w/ Heat-Blued Muzzle Tip
    refl = 0.64 + 0.24 * np.cos(u - 0.8) + 0.14 * np.cos(2.0 * u) + 0.02 * nf[:512, :512]
    heat_blue = np.exp(-((v - 0.88) ** 2) / 0.015)
    band_dark = 1.0 - 0.18 * np.exp(-((v - 0.52) ** 2) / 0.0014)
    arr[:512, :512, 0] = np.clip((refl * 208.0 - heat_blue * 60.0) * band_dark, 20, 248)
    arr[:512, :512, 1] = np.clip((refl * 214.0 + heat_blue * 18.0) * band_dark, 22, 250)
    arr[:512, :512, 2] = np.clip((refl * 228.0 + heat_blue * 48.0) * band_dark, 26, 255)

    # Q2: Mega-Blue Collector Cowl & White Accent Band
    q2 = np.zeros((512, 512, 3), dtype=np.float32)
    w_band = np.exp(-((v - 0.25) ** 2) / 0.0025)
    c_band = np.exp(-((v - 0.82) ** 2) / 0.0018)
    q2[..., 0] = np.clip(16.0 * refl + 225.0 * w_band, 8, 252)
    q2[..., 1] = np.clip(92.0 * refl + 150.0 * w_band + 155.0 * c_band, 30, 255)
    q2[..., 2] = np.clip(225.0 * refl + 30.0 * w_band + 30.0 * c_band, 120, 255)
    arr[:512, 512:] = q2

    # Q3: Glowing Electric-Cyan Mega-Buster Plasma Emitter Core
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    rx = (xx - 255.5) / 245.0
    ry = (yy - 255.5) / 245.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang = np.arctan2(ry, rx)
    ring = np.exp(-((rr - 0.68) ** 2) / 0.018) + 0.95 * np.exp(-((rr - 0.24) ** 2) / 0.016)
    vanes = 0.65 + 0.35 * np.cos(ang * 10.0)
    core = np.clip(ring * vanes, 0.0, 1.3)
    arr[512:, :512, 0] = np.clip(24.0 + 210.0 * (core ** 2.0), 0, 255)
    arr[512:, :512, 1] = np.clip(75.0 + 200.0 * core, 0, 255)
    arr[512:, :512, 2] = np.clip(125.0 + 180.0 * core, 0, 255)

    # Q4: Crisp White-Stripe & Stainless Mount Collar
    arr[512:, 512:] = np.clip(refl[..., None] * np.array([224.0, 232.0, 242.0]), 30, 250)

    out_path = os.path.join(progs_dir, "gk5_exhaust.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_flame_texture(progs_dir):
    """512x512 RGBA additive Mega-Buster cyan/white-hot shock-diamond plasma plume."""
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)

    yy, xx = np.mgrid[0:512, 0:256].astype(np.float32)
    u_wrap = (xx / 255.0) * 2.0 * math.pi
    v_n = yy / 511.0

    # Left half: Electric-cyan/cobalt outer Mega-Buster plasma plume
    mach = 0.54 + 0.46 * (np.cos(v_n * 2.0 * math.pi * 3.5) ** 2)
    streak = 0.86 + 0.14 * np.cos(u_wrap * 4.0 + v_n * 6.0)
    tail_fade = np.clip(1.0 - v_n ** 1.15, 0.0, 1.0) * np.clip(v_n / 0.04, 0.0, 1.0)
    intensity = np.clip(streak * tail_fade * (0.62 + 0.55 * mach), 0.0, 1.0)
    rgba[:, :256, 0] = np.clip(intensity * (15.0 + 180.0 * (intensity ** 2.2)), 0, 255)
    rgba[:, :256, 1] = np.clip(intensity * (185.0 + 70.0 * intensity), 0, 255)
    rgba[:, :256, 2] = np.clip(intensity * 255.0, 0, 255)
    rgba[:, :256, 3] = np.clip(intensity * 255.0, 0, 255)

    # Right half: White-hot inner Mach-diamond plasma core
    core_mach = 0.58 + 0.42 * (np.cos(v_n * 2.0 * math.pi * 4.5) ** 2)
    core_streak = 0.90 + 0.10 * np.cos(u_wrap * 3.0 - v_n * 8.0)
    core_i = np.clip(core_streak * np.clip(1.0 - v_n ** 1.05, 0.0, 1.0) * np.clip(v_n / 0.03, 0.0, 1.0) * core_mach, 0.0, 1.0)
    rgba[:, 256:, 0] = np.clip(core_i * 225.0, 0, 255)
    rgba[:, 256:, 1] = np.clip(core_i * 250.0, 0, 255)
    rgba[:, 256:, 2] = np.clip(core_i * 255.0, 0, 255)
    rgba[:, 256:, 3] = np.clip(core_i * 255.0, 0, 255)

    out_path = os.path.join(progs_dir, "gk5_flame.png")
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(out_path, "PNG", optimize=True)
    return out_path


def build_all_textures(progs_dir):
    os.makedirs(progs_dir, exist_ok=True)
    p_wheel, p_chrome = _copy_mmt_textures(progs_dir)
    return {
        "progs/gk5_chrome": p_chrome,
        "progs/gk5_wheel": p_wheel,
        "progs/gk5_body": build_body_texture(progs_dir),
        "progs/gk5_seat": build_seat_texture(progs_dir),
        "progs/gk5_steer": build_steer_texture(progs_dir),
        "progs/gk5_exhaust": build_exhaust_texture(progs_dir),
        "progs/gk5_flame": build_flame_texture(progs_dir),
    }


# ---------------------------------------------------------------------------
# Custom Mesh Helper
# ---------------------------------------------------------------------------
class KartMesh(MeshPart):
    """Extends MeshPart with smooth closed-loop lofts and oriented chamfered boxes."""

    def add_loop_loft(self, rings, uv_rect=UV_Q1, cap_start=True, cap_end=True):
        n_rings = len(rings)
        n_pts = len(rings[0])
        assert all(len(r) == n_pts for r in rings), "All loft rings must have equal point count"
        u0, v0, u1, v1 = uv_rect

        for ri in range(n_rings - 1):
            ra, rb = rings[ri], rings[ri + 1]
            va = v0 + (v1 - v0) * (ri / float(n_rings - 1))
            vb = v0 + (v1 - v0) * ((ri + 1) / float(n_rings - 1))
            for i in range(n_pts):
                ip = (i + 1) % n_pts
                p0, p1, p2, p3 = ra[i], rb[i], rb[ip], ra[ip]
                t_loop = vadd(vsub(p3, p0), vsub(p2, p1))
                t_along = vadd(vsub(p1, p0), vsub(p2, p3))
                fn = vnorm(vcross(t_loop, t_along))
                ua = u0 + (u1 - u0) * (i / float(n_pts))
                ub = u0 + (u1 - u0) * ((i + 1) / float(n_pts))
                self.add_quad(p0, p1, p2, p3, (ua, va), (ua, vb), (ub, vb), (ub, va), nrm=fn)

        uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        for do_cap, ring_idx, nxt_idx, flip in ((cap_start, 0, 1, True), (cap_end, -1, -2, False)):
            if not do_cap:
                continue
            r_cur = rings[ring_idx]
            r_nxt = rings[nxt_idx]
            ctr = (
                sum(p[0] for p in r_cur) / n_pts,
                sum(p[1] for p in r_cur) / n_pts,
                sum(p[2] for p in r_cur) / n_pts,
            )
            nxt_ctr = (
                sum(p[0] for p in r_nxt) / n_pts,
                sum(p[1] for p in r_nxt) / n_pts,
                sum(p[2] for p in r_nxt) / n_pts,
            )
            cap_n = vnorm(vsub(ctr, nxt_ctr))
            ic = len(self.verts)
            self.verts.append(ctr)
            self.norms.append(cap_n)
            self.st.append((uc, vc))
            for i in range(n_pts):
                p = r_cur[i]
                self.verts.append(p)
                self.norms.append(cap_n)
                self.st.append((u0 + (u1 - u0) * (i / float(n_pts)), v0 if flip else v1))
            for i in range(n_pts):
                i1 = ic + 1 + i
                i2 = ic + 1 + ((i + 1) % n_pts)
                wn = vcross(vsub(self.verts[i1], ctr), vsub(self.verts[i2], ctr))
                if vdot(wn, cap_n) >= 0:
                    self.tris.append((ic, i1, i2))
                else:
                    self.tris.append((ic, i2, i1))

    def add_box_oriented(self, center, size_xyz, rx=0.0, ry=0.0, rz=0.0, ch=0.15, uv_rect=UV_Q1):
        hx, hy, hz = size_xyz[0] * 0.5, size_xyz[1] * 0.5, size_xyz[2] * 0.5
        tmp = KartMesh(self.mat)
        tmp.add_chamfer_box(-hx, +hx, -hy, +hy, -hz, +hz, ch=ch, uv_rect=uv_rect)
        self.append_part(tmp, offset=center, rx=rx, ry=ry, rz=rz)


# ---------------------------------------------------------------------------
# Surface Builders (Static Local Frame 0 Geometry)
# ---------------------------------------------------------------------------
def build_chassis():
    """Underslung stainless front & rear cross-axles, swept chrome perimeter rails,
    footwell pedals, axle carriers, and rear reactor cradle.
    """
    m = KartMesh("chrome")

    # 1) Underslung Front Stainless Cross-Axle (X = +31.0, Z = 8.8, Y = -24 .. +24)
    m.add_lathe(
        (FRONT_WHEEL_X, 0.0, FRONT_WHEEL_R), (0.0, 1.0, 0.0),
        [
            (-24.0, 0.0, 0.02),
            (-24.0, 2.2, 0.05),
            (-19.5, 2.2, 0.14),
            (-19.2, 1.65, 0.16),
            (+19.2, 1.65, 0.84),
            (+19.5, 2.2, 0.86),
            (+24.0, 2.2, 0.95),
            (+24.0, 0.0, 0.98),
        ],
        segs=18, uv_rect=UV_STAINLESS,
    )
    # Front axle retaining collars & pillow blocks
    for sy in (+1.0, -1.0):
        m.add_lathe(
            (FRONT_WHEEL_X, sy * 15.5, FRONT_WHEEL_R), (0.0, sy, 0.0),
            [(-1.2, 1.65, 0.1), (-1.2, 2.55, 0.2), (+1.2, 2.55, 0.8), (+1.2, 1.65, 0.9)],
            segs=14, uv_rect=UV_HEX_ZINC,
        )
        m.add_box_oriented((FRONT_WHEEL_X, sy * 11.2, 6.8), (3.4, 2.2, 4.4), ch=0.25, uv_rect=UV_STAINLESS)

    # 2) Underslung Rear Stainless Cross-Axle (X = -28.0, Z = 13.5, Y = -27.2 .. +27.2)
    m.add_lathe(
        (REAR_WHEEL_X, 0.0, REAR_WHEEL_R), (0.0, 1.0, 0.0),
        [
            (-27.2, 0.0, 0.02),
            (-27.2, 2.9, 0.05),
            (-21.0, 2.9, 0.15),
            (-20.6, 2.15, 0.17),
            (+20.6, 2.15, 0.83),
            (+21.0, 2.9, 0.85),
            (+27.2, 2.9, 0.95),
            (+27.2, 0.0, 0.98),
        ],
        segs=18, uv_rect=UV_STAINLESS,
    )
    for sy in (+1.0, -1.0):
        m.add_lathe(
            (REAR_WHEEL_X, sy * 16.5, REAR_WHEEL_R), (0.0, sy, 0.0),
            [(-1.5, 2.15, 0.1), (-1.5, 3.25, 0.2), (+1.5, 3.25, 0.8), (+1.5, 2.15, 0.9)],
            segs=14, uv_rect=UV_HEX_ZINC,
        )
        # Underslung rear axle drop-carrier & diagonal radius strut down to chassis rail
        m.add_tube([(REAR_WHEEL_X, sy * 14.5, REAR_WHEEL_R), (REAR_WHEEL_X, sy * 13.2, 4.8)], [1.35, 1.20], segs=10, uv_rect=UV_STAINLESS)
        m.add_tube([(REAR_WHEEL_X, sy * 14.5, REAR_WHEEL_R), (-17.5, sy * 13.5, 4.6)], [0.95, 0.95], segs=10, uv_rect=UV_CHROME_BAR)

    # 3) Swept Chrome Twin Perimeter Chassis Frame Rails (strictly |Y| >= 12.8 in cockpit!)
    for sy in (+1.0, -1.0):
        rail_pts = [
            (31.8, sy * 9.8, 5.2),
            (25.0, sy * 11.4, 4.4),
            (15.5, sy * 13.2, 4.2),
            (0.0,  sy * 13.5, 4.2),
            (-15.5, sy * 13.4, 4.4),
            (-28.0, sy * 12.6, 4.8),
            (-36.5, sy * 10.6, 6.2),
            (-40.5, sy * 7.8, 7.2),
        ]
        m.add_tube(rail_pts, [1.05] * len(rail_pts), segs=10, uv_rect=UV_CHROME_BAR)

        # Sidepod lower chrome rub nerf-bar outside sidepods
        nerf_pts = [
            (15.5, sy * 13.5, 4.4),
            (11.0, sy * 22.8, 4.8),
            (-8.5, sy * 23.0, 4.8),
            (-14.5, sy * 14.2, 4.6),
        ]
        m.add_tube(nerf_pts, [0.85] * len(nerf_pts), segs=8, uv_rect=UV_CHROME_BAR)

        # Front axle wishbone radius arms
        m.add_tube([(24.0, sy * 11.2, 4.8), (FRONT_WHEEL_X, sy * 17.5, FRONT_WHEEL_R - 0.8)], [0.75, 0.65], segs=8, uv_rect=UV_STAINLESS)
        m.add_tube([(28.5, sy * 10.5, 9.8), (FRONT_WHEEL_X, sy * 17.5, FRONT_WHEEL_R + 0.8)], [0.68, 0.60], segs=8, uv_rect=UV_STAINLESS)

    # Transverse chrome cross-members (ahead of seat, front bulkhead, rear bumper)
    m.add_tube([(31.8, -10.5, 5.2), (31.8, +10.5, 5.2)], [1.10, 1.10], segs=10, uv_rect=UV_CHROME_BAR)
    m.add_tube([(14.0, -13.2, 4.2), (14.0, +13.2, 4.2)], [0.95, 0.95], segs=10, uv_rect=UV_STAINLESS)
    m.add_tube([(-17.0, -13.4, 4.4), (-17.0, +13.4, 4.4)], [0.95, 0.95], segs=10, uv_rect=UV_STAINLESS)
    m.add_tube([(-40.5, -8.0, 7.2), (-40.5, +8.0, 7.2)], [1.05, 1.05], segs=10, uv_rect=UV_CHROME_BAR)

    # 4) Footwell Floor Plate & Machined Stainless Pedals (X = +14..+26, |Y| <= 9.5, Z = 3.5..9.8)
    m.add_chamfer_box(14.5, 26.8, -9.2, +9.2, 3.6, 4.3, ch=0.14, uv_rect=UV_RUBBER_CAP)
    for py in (+4.2, -4.2):
        m.add_tube([(26.2, py, 4.6), (24.6, py, 9.4)], [0.48, 0.44], segs=8, uv_rect=UV_STAINLESS)
        m.add_box_oriented((24.2, py, 8.8), (0.55, 2.7, 3.4), ry=18.0, ch=0.12, uv_rect=UV_CHROME_BAR)

    # 5) Rear Mega-Reactor Capacitor Drum & Stainless Manifold Frame (behind X <= -21)
    m.add_lathe(
        (-28.0, 0.0, 8.8), (0.0, 1.0, 0.0),
        [(-8.2, 0.0, 0.05), (-8.2, 3.4, 0.12), (-7.0, 3.8, 0.25), (+7.0, 3.8, 0.75), (+8.2, 3.4, 0.88), (+8.2, 0.0, 0.95)],
        segs=16, uv_rect=UV_STAINLESS,
    )
    for sy in (+1.0, -1.0):
        m.add_tube([(-21.5, sy * 9.0, 5.2), (-29.5, sy * 7.8, 15.6)], [0.90, 0.85], segs=8, uv_rect=UV_CHROME_BAR)
        m.add_tube([(-36.5, sy * 10.0, 6.4), (-32.0, sy * 8.1, 15.8)], [0.85, 0.80], segs=8, uv_rect=UV_CHROME_BAR)

    return m


def build_body_pods():
    """Sculpted Mega-Man cobalt-blue + cyan-trim side fairing pods with white racing stripes,
    recessed nose cowl deck, belly pan, and twin rear dorsal stabilizer fins.
    Strictly keeps seated torso clearance box (22u x 28u above seat_pos) 100% clear!
    """
    m = KartMesh("body")

    # 1) Carbon-Slate Belly Pan (Z = 2.8 .. 3.7, strictly above ground!)
    m.add_chamfer_box(-22.0, +24.0, -12.6, +12.6, 2.8, 3.7, ch=0.22, uv_rect=UV_Q3)
    m.add_chamfer_box(+24.0, +31.5, -9.2, +9.2, 2.8, 3.7, ch=0.22, uv_rect=UV_Q3)
    m.add_chamfer_box(-39.5, -22.0, -11.4, +11.4, 2.8, 3.7, ch=0.22, uv_rect=UV_Q3)

    # 2) Sculpted Mega-Man Cobalt-Blue Nose Cowl w/ Recessed Center Channel for Silver Bar
    # Left & right sculpted pontoon cowls (|Y| = 4.2 .. 12.6, X = +14.2 .. +29.5) + low center bridge (Z = 9.8..11.2)
    m.add_chamfer_box(14.5, 29.0, -4.4, +4.4, 9.8, 11.1, ch=0.25, uv_rect=UV_Q3)
    for sy in (+1.0, -1.0):
        cowl_secs = [
            # (x, y_in, y_out, z_bot, z_top)
            (14.2, 4.0, 12.6, 10.0, 14.2),
            (19.5, 3.9, 11.8, 9.8, 13.6),
            (24.5, 3.8, 10.4, 9.2, 12.4),
            (29.5, 3.8, 8.6,  8.6, 11.0),
        ]
        c_rings = []
        for x, yi, yo, zb, zt in cowl_secs:
            ya, yb = sy * yi, sy * yo
            ylo, yhi = min(ya, yb), max(ya, yb)
            c_rings.append([
                (x, yhi, zb + 0.4),
                (x, yhi - 0.5 * sy, zt - 0.6),
                (x, 0.5 * (ylo + yhi) + 1.8 * sy, zt),
                (x, ylo, zt - 0.4),
                (x, ylo, zb + 0.3),
                (x, 0.5 * (ylo + yhi), zb),
            ])
            if sy < 0:
                c_rings[-1] = list(reversed(c_rings[-1]))
        m.add_loop_loft(c_rings, uv_rect=UV_Q1, cap_start=True, cap_end=True)

        # Cockpit side coaming wall bridging cowl to sidepods (strictly |Y| >= 13.2!)
        coam_y0, coam_y1 = sorted([sy * 13.2, sy * 14.8])
        m.add_chamfer_box(-16.0, +15.0, coam_y0, coam_y1, 4.2, 12.8, ch=0.35, uv_rect=UV_Q1)

    # 3) Sculpted Mega-Man Cobalt-Blue & Cyan-Trim Side Fairing Pods w/ White Stripes
    for sy in (+1.0, -1.0):
        pod_secs = [
            # (x,   y_in, y_ob, y_ot, z_bot, z_mid, z_top)
            (-14.2, 13.4, 15.8, 16.4, 4.4, 9.2, 13.2),
            (-8.0,  13.4, 20.6, 22.8, 4.2, 9.8, 15.8),
            (+3.0,  13.4, 21.4, 23.2, 4.2, 10.2, 16.2),
            (+11.5, 13.4, 19.6, 22.0, 4.5, 10.4, 15.6),
            (+16.2, 13.4, 17.2, 19.8, 5.2, 10.4, 14.6),
        ]
        rings = []
        for x, yi, yob, yot, zb, zm, zt in pod_secs:
            y_in = sy * yi
            y_ob = sy * yob
            y_ot = sy * yot
            y_om = sy * (0.5 * (yob + yot) + 0.6)
            ring = [
                (x, y_in, zb),
                (x, y_ob, zb + 0.6),
                (x, y_om, zm),
                (x, y_ot, zt - 1.3),
                (x, sy * (0.55 * yi + 0.45 * yot), zt),
                (x, y_in, zt - 0.5),
            ]
            if sy < 0:
                ring = list(reversed(ring))
            rings.append(ring)
        m.add_loop_loft(rings, uv_rect=UV_Q2, cap_start=True, cap_end=True)

        # Crisp white racing shoulder trim band along top edge of sidepod
        y0, y1 = sorted([sy * 14.2, sy * 18.8])
        m.add_chamfer_box(-11.5, +13.0, y0, y1, 15.4, 16.5, ch=0.22, uv_rect=UV_Q4_B)

        # Forward-facing Cyan Radiator Scoop & Louvers (X = +15.0 .. +17.8, |Y| = 14.4 .. 19.8)
        sy0, sy1 = sorted([sy * 14.4, sy * 19.8])
        m.add_chamfer_box(15.2, 17.4, sy0 + 0.2, sy1 - 0.2, 5.4, 14.2, ch=0.14, uv_rect=UV_Q4_A)
        for sz in (7.0, 9.2, 11.4):
            m.add_box_oriented((17.0, sy * 17.1, sz), (1.8, 4.8, 0.42), ry=14.0, ch=0.08, uv_rect=UV_Q4_C)

    # 4) Rear Cobalt-Blue Reactor Spine & Twin Mega-Man Dorsal Fins (strictly behind X <= -19.2!)
    spine_secs = [
        (-19.5, 11.4, 13.0, 21.5),
        (-24.5, 10.2, 13.2, 22.8),
        (-31.5, 8.2,  13.0, 21.8),
        (-38.0, 6.2,  11.0, 17.8),
        (-41.5, 4.4,  9.5,  14.2),
    ]
    sp_rings = []
    for x, yh, zb, zt in spine_secs:
        sp_rings.append([
            (x, +yh, zb + 0.5),
            (x, +yh * 0.75, zt - 1.2),
            (x, +yh * 0.28, zt),
            (x, -yh * 0.28, zt),
            (x, -yh * 0.75, zt - 1.2),
            (x, -yh, zb + 0.5),
            (x, -yh * 0.75, zb),
            (x, +yh * 0.75, zb),
        ])
    m.add_loop_loft(sp_rings, uv_rect=UV_Q1, cap_start=True, cap_end=True)

    # Twin swept Mega-Man helmet-style dorsal stabilizer fins (Y = +-6.0, X = -22 .. -38, Z = 20 .. 28.5)
    for sy in (+1.0, -1.0):
        fy0, fy1 = sorted([sy * 5.2, sy * 6.8])
        fin_rings = [
            [(-22.0, fy1, 20.5), (-22.0, fy1, 27.5), (-22.0, fy0, 27.5), (-22.0, fy0, 20.5)],
            [(-29.5, fy1, 20.0), (-29.5, fy1, 28.8), (-29.5, fy0, 28.8), (-29.5, fy0, 20.0)],
            [(-37.5, fy1, 16.5), (-37.5, fy1, 24.5), (-37.5, fy0, 24.5), (-37.5, fy0, 16.5)],
        ]
        m.add_loop_loft(fin_rings, uv_rect=UV_Q4_C, cap_start=True, cap_end=True)

    # Glowing Cyan LED Tail Light Bar (X = -41.2 .. -42.4)
    m.add_chamfer_box(-42.4, -40.8, -3.4, +3.4, 10.6, 13.4, ch=0.20, uv_rect=UV_Q4_D)

    return m


def build_front_bar():
    """Prominent mirror-chrome bullet-nosed Mega Man silver torpedo bar + ribbed black rubber rear cap
    placed at X ~ +10.2 .. +56.2, tilted +3 deg up pointing forward (+X).
    """
    m = KartMesh("chrome")
    bar_local = build_tank_silver_bar(length_scale=0.50, radius_scale=0.52, segs=28)
    m.append_part(bar_local, offset=BAR_POS, ry=BAR_TILT_DEG)
    return m


def build_t_collar():
    """Visible stainless TIG T-collar gimbal clamping the front silver bar on twin chrome struts
    right ahead of the nose cowl.
    """
    m = KartMesh("chrome")

    # 1) Transverse TIG-welded stainless T-collar saddle underneath the bar bulge
    tc = core_build_t_collar(radius_scale=0.60, length_scale=0.56)
    m.append_part(tc, offset=(BAR_POS[0], 0.0, BAR_POS[2] - 2.6), ry=BAR_TILT_DEG)

    # 2) Upper split machined clamp ring hugging the bar's central collar bulge
    clamp = KartMesh("chrome")
    clamp.add_lathe(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        [
            (-2.4, 3.35, 0.08),
            (-2.4, 4.15, 0.16),
            (+2.4, 4.15, 0.84),
            (+2.4, 3.35, 0.92),
        ],
        segs=20, uv_rect=UV_STAINLESS,
    )
    # 4 zinc hex clamping bolts on the upper T-collar ears
    for sy in (+1.0, -1.0):
        for sx in (-1.2, +1.2):
            clamp.add_lathe(
                (sx, sy * 4.05, 1.4), (0.0, 0.0, 1.0),
                [(0.0, 0.0, 0.1), (0.0, 0.65, 0.2), (0.95, 0.65, 0.8), (0.95, 0.0, 0.95)],
                segs=6, uv_rect=UV_HEX_ZINC,
            )
    m.append_part(clamp, offset=BAR_POS, ry=BAR_TILT_DEG)

    # 3) Twin elevated mirror-chrome gimbal struts from front cross-axle up to T-collar
    for sy in (+1.0, -1.0):
        # Primary vertical-angled strut from cross-axle collar to T-collar end
        m.add_tube(
            [(FRONT_WHEEL_X, sy * 9.8, FRONT_WHEEL_R), (BAR_POS[0], sy * 5.8, BAR_POS[2] - 2.4)],
            [0.98, 0.92], segs=10, uv_rect=UV_CHROME_BAR,
        )
        # Rear triangulation brace strut to front nose cowl mounting lug
        m.add_tube(
            [(26.0, sy * 7.2, 10.8), (BAR_POS[0] - 0.5, sy * 5.4, BAR_POS[2] - 2.2)],
            [0.82, 0.78], segs=10, uv_rect=UV_STAINLESS,
        )
        # Clevis knuckle collar on front axle
        m.add_lathe(
            (FRONT_WHEEL_X, sy * 9.8, FRONT_WHEEL_R), (0.0, sy, 0.0),
            [(-1.2, 1.65, 0.1), (-1.2, 2.50, 0.2), (+1.2, 2.50, 0.8), (+1.2, 1.65, 0.9)],
            segs=12, uv_rect=UV_HEX_ZINC,
        )

    return m


def build_seat():
    """Contoured Mega-Blue & crisp white quilted bucket seat.
    Seat pan top at SEAT_POS = (-9.0, 0.0, 9.0).
    Strictly keeps the 22u-wide (|Y| < 11.0) x 28u-tall (Z in [10.5, 37.0]) torso clearance box clear!
    """
    m = KartMesh("seat")

    # 1) Bucket seat pan (bottom Z=4.2, quilted white top strictly at Z=9.0!)
    m.add_chamfer_box(-16.8, -1.4, -10.8, +10.8, 4.2, 8.1, ch=0.42, uv_rect=UV_Q1)
    m.add_chamfer_box(-16.2, -1.8, -10.2, +10.2, 8.0, 9.0, ch=0.22, uv_rect=UV_Q2)

    # 2) Reclined Mega-Blue Backrest Shell & White Quilted Pad (strictly behind X <= -16.8!)
    back_secs = [
        (-16.8, -19.0, 10.6, 8.2),
        (-18.2, -20.5, 10.4, 14.5),
        (-20.0, -22.2, 9.8,  20.5),
        (-21.6, -23.6, 8.4,  25.8),
    ]
    back_rings = []
    for xf, xb, yh, z in back_secs:
        back_rings.append([(xf, +yh, z), (xb, +yh * 0.92, z), (xb, -yh * 0.92, z), (xf, -yh, z)])
    m.add_loop_loft(back_rings, uv_rect=UV_Q1, cap_start=True, cap_end=True)

    pad_rings = [
        [(-16.6, +9.0, 9.2), (-17.2, +9.0, 9.2), (-17.2, -9.0, 9.2), (-16.6, -9.0, 9.2)],
        [(-17.9, +8.6, 15.0), (-18.6, +8.6, 15.0), (-18.6, -8.6, 15.0), (-17.9, -8.6, 15.0)],
        [(-19.6, +8.0, 21.0), (-20.3, +8.0, 21.0), (-20.3, -8.0, 21.0), (-19.6, -8.0, 21.0)],
        [(-21.1, +6.6, 25.0), (-21.8, +6.6, 25.0), (-21.8, -6.6, 25.0), (-21.1, -6.6, 25.0)],
    ]
    m.add_loop_loft(pad_rings, uv_rect=UV_Q2, cap_start=True, cap_end=True)

    # 3) Mega-Blue & White-Piped Side Bolsters (strictly |Y| >= 11.4!)
    for sy in (+1.0, -1.0):
        y0, y1 = sorted([sy * 11.4, sy * 13.2])
        m.add_chamfer_box(-16.6, -2.2, y0, y1, 6.0, 14.2, ch=0.45, uv_rect=UV_Q3)
        sh_rings = [
            [(-16.8, y1, 12.4), (-19.2, y1, 12.4), (-19.2, y0, 12.4), (-16.8, y0, 12.4)],
            [(-17.8, y1, 18.2), (-20.6, y1, 18.2), (-20.6, y0, 18.2), (-17.8, y0, 18.2)],
            [(-19.4, y1 - sy * 0.4, 24.2), (-22.6, y1 - sy * 0.4, 24.2), (-22.6, y0, 24.2), (-19.4, y0, 24.2)],
        ]
        if sy < 0:
            sh_rings = [list(reversed(r)) for r in sh_rings]
        m.add_loop_loft(sh_rings, uv_rect=UV_Q3, cap_start=True, cap_end=True)

    # 4) Contoured White & Mega-Blue '05' Headrest Pad (X = -23.5 .. -19.8, |Y| <= 4.5, Z = 25.8 .. 31.2)
    m.add_box_oriented((-21.5, 0.0, 28.5), (3.4, 9.0, 5.4), ry=-16.0, ch=0.55, uv_rect=UV_Q4)

    return m


def build_steering():
    """Stainless butterfly steering yoke with glowing cyan OLED telemetry dash & twin-arch
    steering column bridge straddling the front silver bar cleanly.
    Yoke center at STEER_POS = (13.0, 0.0, 24.0), tilted 22 deg toward driver.
    """
    m = KartMesh("steer")
    sx, _, sz = STEER_POS

    # 1) Twin-Arch Stainless Column Bridge (descends from yoke hub down to nose cowl pontoons at |Y|=5.4,
    #    completely straddling the silver bar at |Y| <= 3.3!)
    m.add_tube([(sx + 0.4, 0.0, sz - 0.2), (sx + 3.8, 0.0, sz - 2.6)], [1.45, 1.55], segs=12, uv_rect=UV_Q4)
    for sy in (+1.0, -1.0):
        m.add_tube(
            [(sx + 3.6, 0.0, sz - 2.5), (sx + 5.8, sy * 4.6, sz - 5.2), (21.2, sy * 5.6, 13.0)],
            [1.05, 0.95, 0.90], segs=10, uv_rect=UV_Q4,
        )

    # 2) Stainless Butterfly Steering Yoke
    yoke = KartMesh("steer")
    yoke.add_chamfer_box(-0.52, +0.52, -4.6, +4.6, -2.7, +2.7, ch=0.22, uv_rect=UV_Q1)
    yoke.add_chamfer_box(-0.72, +0.35, -3.3, +3.3, +0.9, +3.9, ch=0.14, uv_rect=UV_Q2)
    yoke.add_chamfer_box(-0.42, +0.42, -4.2, +4.2, -3.5, -2.4, ch=0.15, uv_rect=UV_Q1)

    for side in (+1.0, -1.0):
        grip_pts = [
            (0.0, side * 3.8, +3.1),
            (-0.2, side * 5.8, +2.5),
            (-0.3, side * 6.5, +0.4),
            (-0.2, side * 6.2, -1.8),
            (0.0, side * 4.4, -2.9),
        ]
        yoke.add_tube(grip_pts, [0.58, 0.82, 0.92, 0.82, 0.56], segs=10, uv_rect=UV_Q3)
        yoke.add_chamfer_box(+0.85, +1.25, min(side * 3.4, side * 5.4), max(side * 3.4, side * 5.4), -1.0, +1.0, ch=0.08, uv_rect=UV_Q4)

    m.append_part(yoke, offset=STEER_POS, ry=-22.0)
    return m


def build_exhaust():
    """Twin angled chrome Mega-Buster exhaust cannons behind the rear axle."""
    m = KartMesh("exhaust")

    for em in EXHAUST_MOUNTS:
        pod = KartMesh("exhaust")
        L = em["len"]

        # Rear cobalt-blue collector cowl (x = 0 .. 5.8 along -X)
        pod.add_lathe(
            (0.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
            [
                (0.0, 0.0, 0.0),
                (0.0, 3.0, 0.06),
                (1.0, 3.4, 0.16),
                (5.4, 3.5, 0.78),
                (5.8, 3.2, 0.90),
            ],
            segs=20, uv_rect=UV_Q2,
        )

        # Iconic stepped chrome Mega-Buster cannon barrel & flared muzzle lip (x = 5.6 .. L)
        pod.add_lathe(
            (0.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
            [
                (5.6,  3.2, 0.02),
                (5.6,  4.1, 0.06),
                (6.4,  4.4, 0.14),
                (12.2, 4.4, 0.56),
                (12.8, 3.8, 0.62),
                (15.2, 3.9, 0.78),
                (L,    4.45, 0.88),
                (L,    3.65, 0.92),
                (L - 3.6, 2.75, 0.98),
                (L - 3.6, 0.0, 1.00),
            ],
            segs=22, uv_rect=UV_Q1,
        )

        # Crisp white Mega-Man stripe collar ring mid-cannon
        pod.add_lathe(
            (0.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
            [(8.6, 4.38, 0.05), (8.6, 4.65, 0.2), (10.0, 4.65, 0.8), (10.0, 4.38, 0.95)],
            segs=20, uv_rect=UV_Q4,
        )

        # Glowing electric-cyan plasma emitter core inside muzzle
        pod.add_lathe(
            (-(L - 3.0), 0.0, 0.0), (-1.0, 0.0, 0.0),
            [
                (0.0, 0.0, 0.00, 2.8),
                (1.2, 1.1, 0.35, 2.8),
                (0.2, 2.0, 0.70, 2.8),
                (0.2, 2.8, 1.00, 2.8),
            ],
            segs=16, uv_mode="polar", uv_rect=UV_Q3,
        )

        m.append_part(pod, offset=em["origin"], ry=em["ry"], rz=em["rz"])

    return m


def build_flame_surface(is_core=False):
    """Builds fixed-topology flame plume template spanning both Mega-Buster exhaust tips."""
    m = MeshPart("flame")
    uv_rect = (0.53, 0.03, 0.97, 0.97) if is_core else (0.03, 0.03, 0.47, 0.97)
    n_seg = 10
    n_rings = 7 if not is_core else 6

    meta = []
    for ti in (0, 1):
        cols = n_seg + 1
        base = len(m.verts)
        for ri in range(n_rings):
            t = ri / float(n_rings - 1)
            pinch = 1.0 - 0.22 * math.sin(t * math.pi * 3.0) ** 2
            base_r = (1.7 if is_core else 3.1) * (1.0 - 0.85 * (t ** 1.2)) * pinch
            for j in range(cols):
                th = 2.0 * math.pi * (j / float(n_seg))
                m.verts.append((0.0, 0.0, 0.0))
                m.norms.append((0.0, 0.0, 1.0))
                uu = uv_rect[0] + (uv_rect[2] - uv_rect[0]) * (j / float(n_seg))
                vv = uv_rect[1] + (uv_rect[3] - uv_rect[1]) * t
                m.st.append((uu, vv))
                meta.append(("plume", ti, t, th, base_r))
        for ri in range(n_rings - 1):
            for j in range(n_seg):
                a = base + ri * cols + j
                b = a + 1
                c = a + cols
                d = c + 1
                m.tris += [(a, c, b), (b, c, d)]

        # 3 Shock-Diamond Mach Discs
        for di in range(3):
            dt = 0.18 + di * 0.24
            r_disc = (1.45 if is_core else 2.75) * (1.0 - 0.55 * dt)
            b_d = len(m.verts)
            m.verts.append((0.0, 0.0, 0.0))
            m.norms.append((-1.0, 0.0, 0.0))
            m.st.append((0.5 * (uv_rect[0] + uv_rect[2]), uv_rect[1] + (uv_rect[3] - uv_rect[1]) * dt))
            meta.append(("diamond", ti, dt + 0.06, 0.0, 0.0))
            for j in range(8):
                th = 2.0 * math.pi * (j / 8.0)
                m.verts.append((0.0, 0.0, 0.0))
                m.norms.append((0.0, math.cos(th), math.sin(th)))
                m.st.append((uv_rect[0] + (uv_rect[2] - uv_rect[0]) * 0.5, uv_rect[1] + (uv_rect[3] - uv_rect[1]) * dt))
                meta.append(("diamond", ti, dt, th, r_disc))
            for j in range(8):
                jn = (j + 1) % 8
                m.tris.append((b_d, b_d + 1 + j, b_d + 1 + jn))

    return m, meta


# ---------------------------------------------------------------------------
# Per-Frame Animation & Explosion Physics
# ---------------------------------------------------------------------------
def _xform_part(part, offset=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, pivot=(0.0, 0.0, 0.0)):
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
    n = max(1, len(part.verts))
    return (
        sum(p[0] for p in part.verts) / n,
        sum(p[1] for p in part.verts) / n,
        sum(p[2] for p in part.verts) / n,
    )


def _ballistic_pose(c0, vel, omega, radius_est, dt_idx):
    """Computes ballistic displacement (dx, dy, dz) and Euler spin (rx, ry, rz) with elastic bounce."""
    t = dt_idx * 0.055
    g = 240.0
    z0 = c0[2]
    vz = vel[2]
    z_cur = z0
    t_rem = t
    floor_z = max(radius_est, 1.5) + 0.5
    bounces = 0
    while t_rem > 1e-5 and bounces < 3:
        a_q = -0.5 * g
        b_q = vz
        c_q = z_cur - floor_z
        disc = b_q * b_q - 4.0 * a_q * c_q
        if disc >= 0.0:
            tb = (-b_q - math.sqrt(disc)) / (2.0 * a_q)
            if 1e-4 < tb <= t_rem:
                z_cur = floor_z
                vz = -(vz - g * tb) * 0.56
                t_rem -= tb
                bounces += 1
                continue
        z_cur = z_cur + vz * t_rem - 0.5 * g * t_rem * t_rem
        break

    dx = vel[0] * t * (0.85 ** bounces)
    dy = vel[1] * t * (0.85 ** bounces)
    dz = z_cur - z0
    return (dx, dy, dz), (omega[0] * t, omega[1] * t, omega[2] * t)


def _animate_explosion_part(part_in_world, vel, omega, radius_est, dt_idx):
    c0 = _part_centroid(part_in_world)
    dpos, rot = _ballistic_pose(c0, vel, omega, radius_est, dt_idx)
    vv, nn = _xform_part(part_in_world, offset=dpos, rx=rot[0], ry=rot[1], rz=rot[2], pivot=c0)
    min_z = min(p[2] for p in vv)
    if min_z < 0.5:
        lift = 0.5 - min_z
        vv = [(p[0], p[1], p[2] + lift) for p in vv]
    return vv, nn


def _animate_wheel_and_hub(w_world, h_world, w_center, vel, omega, radius_w, dt_idx):
    """Keeps wheel and its hub hardware (hex nut, cotter pin, Schrader valve) locked on one rigid body."""
    dpos, rot = _ballistic_pose(w_center, vel, omega, radius_w, dt_idx)
    w_vv, w_nn = _xform_part(w_world, offset=dpos, rx=rot[0], ry=rot[1], rz=rot[2], pivot=w_center)
    h_vv, h_nn = _xform_part(h_world, offset=dpos, rx=rot[0], ry=rot[1], rz=rot[2], pivot=w_center)
    min_z = min(min(p[2] for p in w_vv), min(p[2] for p in h_vv))
    if min_z < 0.55:
        lift = 0.55 - min_z
        w_vv = [(p[0], p[1], p[2] + lift) for p in w_vv]
        h_vv = [(p[0], p[1], p[2] + lift) for p in h_vv]
    return (w_vv, w_nn), (h_vv, h_nn)


def _animate_flame_frame(meta, fi, is_core, chassis_ry, chassis_dz):
    vv, nn = [], []
    tips = [
        ((t["x"], t["y"], t["z"]), (t["dx"], t["dy"], t["dz"]))
        for t in EXHAUST_TIPS
    ]

    if fi < 28:
        # Idle & Fast: collapsed to tiny <0.02u degenerate point inside opaque rear spine
        for _, _, t, th, _ in meta:
            vv.append((-30.0 + 0.003 * t, 0.002 * math.cos(th), 15.0 + 0.002 * math.sin(th)))
            nn.append((-1.0, 0.0, 0.0))
        return vv, nn

    if 28 <= fi <= 43:
        # Super Speed: roaring cyan/white-hot Mega-Buster shock-diamond plumes (>24u long!)
        sf = fi - 28
        ph = 2.0 * math.pi * (sf / 16.0)
        length_base = 34.0 if not is_core else 24.5
        for _, ti, t, th, br in meta:
            tip, dir_v = tips[ti]
            p_tip = vsub(tip, (REAR_WHEEL_X, 0.0, REAR_WHEEL_R))
            p_tip = rot_y(p_tip, chassis_ry)
            tip_w = vadd(p_tip, (REAR_WHEEL_X, 0.0, REAR_WHEEL_R + chassis_dz))
            d_w = vnorm(rot_y(dir_v, chassis_ry))
            _, Y_f, Z_f = basis_from_axis(d_w)

            flicker = 1.0 + 0.14 * math.sin(ph * 3.0 + ti * 1.7 + t * 5.0)
            L = length_base * (1.0 + 0.09 * math.sin(ph * 2.0 + ti * 2.1))
            r_wave = br * flicker * (1.0 + 0.15 * math.sin(ph * 4.0 - t * 9.0 + th * 2.0))
            dist = t * L
            pos = vadd(tip_w, vadd(vmul(d_w, dist), vadd(vmul(Y_f, r_wave * math.cos(th)), vmul(Z_f, r_wave * math.sin(th)))))
            nrm = vnorm(vadd(vmul(Y_f, math.cos(th)), vmul(Z_f, math.sin(th)))) if br > 1e-4 else d_w
            vv.append(pos)
            nn.append(nrm)
        return vv, nn

    # Explosion frames 44..63: flash big 44..47, collapse cleanly by frame 50
    ef = fi - 44
    if ef <= 5:
        flash_env = [0.65, 1.35, 1.55, 1.25, 0.65, 0.20][ef]
        scale_r = 4.2 * flash_env * (0.75 if is_core else 1.0)
        scale_l = 22.0 * flash_env
        for _, ti, t, th, br in meta:
            ang_lat = th + ti * 1.9 + ef * 0.4
            ang_elev = (t - 0.35) * 1.8
            r_cur = max(0.2, br * scale_r + t * scale_l * 0.45)
            cx = -16.0 + (-1.0 if ti == 0 else -0.5) * t * scale_l * 0.6 + r_cur * math.cos(ang_lat) * 0.7
            cy = (6.0 if ti == 0 else -6.0) + r_cur * math.sin(ang_lat)
            cz = max(0.8, 14.0 + r_cur * math.sin(ang_elev) + ef * 2.2)
            vv.append((cx, cy, cz))
            nn.append(vnorm((math.cos(ang_lat), math.sin(ang_lat), 0.3)))
    else:
        for _ in meta:
            vv.append((0.0, 0.0, 2.0))
            nn.append((0.0, 0.0, 1.0))
    return vv, nn


# ---------------------------------------------------------------------------
# Master Model Assembly & Verification
# ---------------------------------------------------------------------------
def build_gokart_5(progs_dir=PROGS, meta_dir=OUT_DIR):
    print("1. Generating & syncing PNG textures (progs/gk5_*.png)...", flush=True)
    build_all_textures(progs_dir)

    print("2. Building 3D procedural surfaces for Mega Man Twin-Dish Interceptor...", flush=True)
    p_chassis = build_chassis()
    p_pods = build_body_pods()
    p_bar = build_front_bar()
    p_collar = build_t_collar()
    p_seat = build_seat()
    p_steer = build_steering()
    p_exhaust = build_exhaust()

    w_fl, h_fl = build_pneumatic_wheel(+1, FRONT_WHEEL_R, FRONT_WHEEL_HW, segs=32)
    w_fr, h_fr = build_pneumatic_wheel(-1, FRONT_WHEEL_R, FRONT_WHEEL_HW, segs=32)
    w_rl, h_rl = build_pneumatic_wheel(+1, REAR_WHEEL_R, REAR_WHEEL_HW, segs=32)
    w_rr, h_rr = build_pneumatic_wheel(-1, REAR_WHEEL_R, REAR_WHEEL_HW, segs=32)

    p_flame_out, meta_flame_out = build_flame_surface(is_core=False)
    p_flame_core, meta_flame_core = build_flame_surface(is_core=True)

    # Verify player-fit torso clearance box in Frame 0 static pose!
    # 22u-wide (|Y| < 11.0) x 28u-tall (Z in [seat_z+1.5, seat_z+28.0] = [10.5, 37.0])
    static_parts = [
        ("chassis", p_chassis),
        ("body_pods", p_pods),
        ("front_bar", p_bar),
        ("t_collar", p_collar),
        ("seat", p_seat),
        ("steering", p_steer),
        ("exhaust", p_exhaust),
    ]
    for sname, sp in static_parts:
        for vx, vy, vz in sp.verts:
            if -16.0 <= vx <= +5.0 and abs(vy) < 11.0 and 9.2 <= vz <= 37.5:
                raise AssertionError(f"Player-fit torso clearance violation in {sname} at ({vx:.2f}, {vy:.2f}, {vz:.2f})")
    print("   [OK] Player-fit torso clearance box (22u x 28u above seat_pos) has ZERO clipping.", flush=True)

    wheel_defs = [
        ("wheel_fl", "hub_fl", w_fl, h_fl, (FRONT_WHEEL_X, +FRONT_WHEEL_Y, FRONT_WHEEL_R), FRONT_WHEEL_R, (+88.0, +72.0, +96.0), (190.0, 420.0, 260.0)),
        ("wheel_fr", "hub_fr", w_fr, h_fr, (FRONT_WHEEL_X, -FRONT_WHEEL_Y, FRONT_WHEEL_R), FRONT_WHEEL_R, (+94.0, -76.0, +90.0), (-210.0, 390.0, -240.0)),
        ("wheel_rl", "hub_rl", w_rl, h_rl, (REAR_WHEEL_X, +REAR_WHEEL_Y, REAR_WHEEL_R), REAR_WHEEL_R, (-86.0, +84.0, +82.0), (165.0, -380.0, 290.0)),
        ("wheel_rr", "hub_rr", w_rr, h_rr, (REAR_WHEEL_X, -REAR_WHEEL_Y, REAR_WHEEL_R), REAR_WHEEL_R, (-82.0, -88.0, +88.0), (-195.0, -410.0, -270.0)),
    ]

    chassis_defs = [
        ("chassis",   "progs/gk5_chrome",  p_chassis, (-10.0, +14.0, +56.0), (45.0, -60.0, 35.0), 8.0),
        ("body_pods", "progs/gk5_body",    p_pods,    (+14.0, -44.0, +74.0), (260.0, 140.0, 190.0), 7.5),
        ("front_bar", "progs/gk5_chrome",  p_bar,     (+112.0, +24.0, +104.0), (180.0, 320.0, -160.0), 4.5),
        ("t_collar",  "progs/gk5_chrome",  p_collar,  (+76.0, -36.0, +122.0), (310.0, -240.0, 220.0), 4.0),
        ("seat",      "progs/gk5_seat",    p_seat,    (-14.0, -24.0, +128.0), (140.0, -280.0, 220.0), 6.0),
        ("steering",  "progs/gk5_steer",   p_steer,   (+48.0, +38.0, +134.0), (380.0, 240.0, -310.0), 4.0),
        ("exhaust",   "progs/gk5_exhaust", p_exhaust, (-106.0, -26.0, +92.0), (-155.0, 290.0, -260.0), 5.0),
    ]

    surf_frames = {name: [] for name, *_ in chassis_defs}
    for wn, hn, *_ in wheel_defs:
        surf_frames[wn] = []
        surf_frames[hn] = []
    surf_frames["flame_outer"] = []
    surf_frames["flame_core"] = []

    rear_pivot = (REAR_WHEEL_X, 0.0, REAR_WHEEL_R)

    print("3. Computing 64 animation frames (idle, fast 4*pi, super 8*pi + flames, explosion)...", flush=True)
    for fi in range(64):
        if fi < 12:
            # Idle: subtle engine / T-collar gimbal micro-hum; wheels static at Z=0
            ph = 2.0 * math.pi * (fi / 12.0)
            dz = 0.14 * math.sin(ph * 2.0)
            ry = 0.18 * math.sin(ph)
            for sname, _, part, *_ in chassis_defs:
                bar_extra_ry = 0.35 * math.sin(ph) if sname == "front_bar" else 0.0
                surf_frames[sname].append(_xform_part(part, offset=(0.0, 0.0, dz), ry=ry + bar_extra_ry, pivot=rear_pivot))
            for wn, hn, wp, hp, woff, *_ in wheel_defs:
                surf_frames[wn].append(_xform_part(wp, offset=woff))
                surf_frames[hn].append(_xform_part(hp, offset=woff))
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, ry, dz))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, ry, dz))

        elif fi < 28:
            # Fast: 4*pi forward wheel spin across 16 frames + subtle aero chatter
            sf = fi - 12
            ph = 2.0 * math.pi * (sf / 16.0)
            spin_deg = -720.0 * (sf / 16.0)  # 4*pi forward roll
            dz = 0.22 * math.sin(ph * 2.0)
            ry = 0.35 * math.sin(ph * 2.0)
            rx = 0.28 * math.sin(ph)
            for sname, _, part, *_ in chassis_defs:
                surf_frames[sname].append(_xform_part(part, offset=(0.0, 0.0, dz), rx=rx, ry=ry, pivot=rear_pivot))
            for wn, hn, wp, hp, woff, *_ in wheel_defs:
                surf_frames[wn].append(_xform_part(wp, offset=woff, ry=spin_deg))
                surf_frames[hn].append(_xform_part(hp, offset=woff, ry=spin_deg))
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, ry, dz))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, ry, dz))

        elif fi < 44:
            # Super Speed + Flames: 2x wheel spin (8*pi across 16 frames), ~2 deg rear squat, roaring flames!
            sf = fi - 28
            ph = 2.0 * math.pi * (sf / 16.0)
            spin_deg = -1440.0 * (sf / 16.0)  # 8*pi forward roll (2x fast!)
            dz = 0.24 * math.sin(ph * 3.0)
            ry = +2.0 + 0.32 * math.sin(ph * 3.0)
            rx = 0.36 * math.sin(ph * 2.0)
            for sname, _, part, *_ in chassis_defs:
                surf_frames[sname].append(_xform_part(part, offset=(0.0, 0.0, dz), rx=rx, ry=ry, pivot=rear_pivot))
            for wn, hn, wp, hp, woff, *_ in wheel_defs:
                surf_frames[wn].append(_xform_part(wp, offset=woff, ry=spin_deg))
                surf_frames[hn].append(_xform_part(hp, offset=woff, ry=spin_deg))
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, ry, dz))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, ry, dz))

        else:
            # Catastrophic Explosion: ballistic 3D trajectories + tumble + elastic ground bounce (z >= 0.5)
            ef = fi - 44
            for sname, _, part, vel, omega, rad_est in chassis_defs:
                surf_frames[sname].append(_animate_explosion_part(part, vel, omega, rad_est, ef))
            for wn, hn, wp, hp, woff, rad_w, vel, omega in wheel_defs:
                w_world = MeshPart("wheel")
                w_world.append_part(wp, offset=woff)
                h_world = MeshPart("chrome")
                h_world.append_part(hp, offset=woff)
                w_fr, h_fr = _animate_wheel_and_hub(w_world, h_world, woff, vel, omega, rad_w, ef)
                surf_frames[wn].append(w_fr)
                surf_frames[hn].append(h_fr)
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, 0.0, 0.0))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, 0.0, 0.0))

    # Assemble MD3 surface dicts
    surfaces = []
    for sname, shader, part, *_ in chassis_defs:
        surfaces.append(dict(name=sname, shader=shader, tris=list(part.tris), st=list(part.st), frames=surf_frames[sname]))
    for wn, hn, wp, hp, *_ in wheel_defs:
        surfaces.append(dict(name=wn, shader="progs/gk5_wheel", tris=list(wp.tris), st=list(wp.st), frames=surf_frames[wn]))
        surfaces.append(dict(name=hn, shader="progs/gk5_chrome", tris=list(hp.tris), st=list(hp.st), frames=surf_frames[hn]))
    surfaces.append(dict(name="flame_outer", shader="progs/gk5_flame", tris=list(p_flame_out.tris), st=list(p_flame_out.st), frames=surf_frames["flame_outer"]))
    surfaces.append(dict(name="flame_core", shader="progs/gk5_flame", tris=list(p_flame_core.tris), st=list(p_flame_core.st), frames=surf_frames["flame_core"]))

    # Validate MD3 limits pre-write
    for s in surfaces:
        nv, nt = len(s["st"]), len(s["tris"])
        assert 0 < nv <= 4096, f"{s['name']} nv={nv} > 4096"
        assert 0 < nt <= 8192, f"{s['name']} nt={nt} > 8192"
        assert len(s["frames"]) == 64
        all_v = np.asarray([fr[0] for fr in s["frames"]], dtype=np.float32)
        all_n = np.asarray([fr[1] for fr in s["frames"]], dtype=np.float32)
        assert np.isfinite(all_v).all() and np.isfinite(all_n).all(), f"NaN/Inf in {s['name']}"
        assert np.max(np.abs(all_v)) < 511.5, f"MD3 int16 overflow in {s['name']}"

    md3_path = os.path.join(progs_dir, "gokart_5.md3")
    md3lib.write(md3_path, dict(name="progs/gokart_5.md3", surfaces=surfaces, nframes=64, frame_names=FRAME_NAMES))

    skin_path = md3_path + "_0.skin"
    with open(skin_path, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(f"{s['name']},{s['shader']}" for s in surfaces) + "\n")

    # Round-trip md3lib.read() verification
    with open(md3_path, "rb") as f:
        ident, ver = struct.unpack("<4si", f.read(8))
    assert ident == b"IDP3" and ver == 15
    rt = md3lib.read(md3_path)
    assert rt["nframes"] == 64 and len(rt["surfaces"]) == len(surfaces)

    # Ground contact Z=0 for frames 0..43
    for fi in range(44):
        pts_f = np.vstack([np.asarray(s["frames"][fi][0], dtype=np.float32) for s in rt["surfaces"]])
        z_min = float(pts_f[:, 2].min())
        assert abs(z_min) < 0.10, f"Frame {fi} ground contact z_min={z_min:.3f} (expected 0.0)"

    # Flame collapse in 0..27 & 50..63, and >15u extension in 28..43
    for s in rt["surfaces"]:
        if s["name"] in ("flame_outer", "flame_core"):
            for fi in range(28):
                pts = np.asarray(s["frames"][fi][0], dtype=np.float32)
                span = float(np.linalg.norm(pts.max(axis=0) - pts.min(axis=0)))
                assert span < 0.05, f"{s['name']} not collapsed at frame {fi} (span={span:.3f})"
            for fi in range(28, 44):
                pts = np.asarray(s["frames"][fi][0], dtype=np.float32)
                x_span = float(pts.max(axis=0)[0] - pts.min(axis=0)[0])
                assert x_span > 18.0, f"{s['name']} too short at super frame {fi} (x_span={x_span:.2f})"
            for fi in range(50, 64):
                pts = np.asarray(s["frames"][fi][0], dtype=np.float32)
                span = float(np.linalg.norm(pts.max(axis=0) - pts.min(axis=0)))
                assert span < 0.05, f"{s['name']} not collapsed after flash at frame {fi} (span={span:.3f})"

    # Explosion separation (frame 44 vs frame 63) & ground bounce z >= 0.45
    max_disp = 0.0
    for s in rt["surfaces"]:
        if s["name"].startswith("flame_"):
            continue
        c44 = np.asarray(s["frames"][44][0], dtype=np.float32).mean(axis=0)
        c63 = np.asarray(s["frames"][63][0], dtype=np.float32).mean(axis=0)
        disp = float(np.linalg.norm(c63 - c44))
        max_disp = max(max_disp, disp)
        assert disp > 15.0, f"{s['name']} did not fly apart during explosion (disp={disp:.1f})"
        for fi in range(44, 64):
            zmin_e = float(np.asarray(s["frames"][fi][0], dtype=np.float32)[:, 2].min())
            assert zmin_e >= 0.45, f"{s['name']} clipped below ground at frame {fi} (zmin={zmin_e:.2f})"

    # Write shared metadata JSON
    meta_path = None
    if meta_dir is not None:
        os.makedirs(meta_dir, exist_ok=True)
        meta_path = os.path.join(meta_dir, "gokart_5_meta.json")
        meta_doc = {
            "id": "kart5",
            "name": "Mega Man Twin-Dish Interceptor",
            "tagline": "Mega-Blue Sidepods, Giant Rear Dish Tires & Elevated T-Collar Silver Bar",
            "palette": ["#1052d4", "#00dcff", "#eef2f6", "#22262d"],
            "description": (
                "Sleek low-slung Mega-Man-Blue and mirror-chrome interceptor go-kart built on "
                "authentic Mega Man contraption hardware: giant 13.5u rear 5-ribbed pneumatic tires "
                "and nimble 8.8u front wheels on off-white stamped steel dish rims with zinc hex nuts, "
                "yellow cotter pins, and brass Schrader valves; underslung stainless cross-axles; "
                "cobalt-blue and cyan-trim side fairing pods with crisp white racing stripes; a "
                "prominent +3 deg mirror-chrome bullet-nosed silver torpedo bar clamped in an elevated "
                "stainless TIG T-collar gimbal ahead of the nose cowl; quilted blue/white bucket seat; "
                "stainless butterfly steering yoke; and twin angled Mega-Buster exhaust cannons."
            ),
            "highlights": [
                ["Twin-Dish Stance", "Giant R=13.5u rear & R=8.8u front Mega Man 5-ribbed dish wheels w/ hex/cotter/valve"],
                ["Elevated Gimbal Bar", "Mirror-chrome torpedo bar (X=+10..+56, +3 deg) in elevated TIG T-collar on twin struts"],
                ["Mega-Buster Twin", "Angled chrome Mega-Buster exhaust cannons w/ cyan/white-hot shock-diamond plumes"],
            ],
            "seat_pos": {"x": SEAT_POS[0], "y": SEAT_POS[1], "z": SEAT_POS[2]},
            "steer_pos": {"x": STEER_POS[0], "y": STEER_POS[1], "z": STEER_POS[2]},
            "exhaust_tips": EXHAUST_TIPS,
            "textures": {
                "progs/gk5_chrome": "progs/gk5_chrome.png",
                "progs/gk5_wheel": "progs/gk5_wheel.png",
                "progs/gk5_body": "progs/gk5_body.png",
                "progs/gk5_seat": "progs/gk5_seat.png",
                "progs/gk5_steer": "progs/gk5_steer.png",
                "progs/gk5_exhaust": "progs/gk5_exhaust.png",
                "progs/gk5_flame": "progs/gk5_flame.png",
            },
            "materials": {
                "progs/gk5_chrome": {"metallic": 0.92, "roughness": 0.14, "spec": 1.50},
                "progs/gk5_wheel": {"metallic": 0.25, "roughness": 0.48, "spec": 0.55},
                "progs/gk5_body": {"metallic": 0.62, "roughness": 0.22, "spec": 1.05},
                "progs/gk5_seat": {"metallic": 0.10, "roughness": 0.60, "spec": 0.35},
                "progs/gk5_steer": {"metallic": 0.58, "roughness": 0.24, "spec": 0.95},
                "progs/gk5_exhaust": {"metallic": 0.88, "roughness": 0.18, "spec": 1.40},
                "progs/gk5_flame": {"metallic": 0.0, "roughness": 1.0, "spec": 0.0, "unlit": True, "additive": True},
            },
        }
        with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta_doc, f, indent=2)

    tot_v = sum(len(s["st"]) for s in rt["surfaces"])
    tot_t = sum(len(s["tris"]) for s in rt["surfaces"])
    pts0 = np.vstack([np.asarray(s["frames"][0][0], dtype=np.float32) for s in rt["surfaces"]])
    bmin, bmax = pts0.min(axis=0), pts0.max(axis=0)
    print(f"4. [PASS] {md3_path} | 64f | {len(rt['surfaces'])} surfs | {tot_v}v / {tot_t}t")
    print(f"   Frame 0 bbox: ({bmin[0]:+.1f}, {bmin[1]:+.1f}, {bmin[2]:+.1f}) .. ({bmax[0]:+.1f}, {bmax[1]:+.1f}, {bmax[2]:+.1f})")
    print(f"   Max explosion separation: {max_disp:.1f}u | Metadata: {meta_path}")
    for s in rt["surfaces"]:
        print(f"     - {s['name']:12s}: {len(s['st']):4d}v / {len(s['tris']):4d}t | {s['shader']}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build Go-Kart #5 MD3, skin, and textures.")
    p.add_argument("--out-dir", default=None, help="Output directory for MD3, skin, and PNGs")
    p.add_argument("--meta-dir", default=None, help="Optional directory for gokart_5_meta.json")
    args = p.parse_args()
    progs_dir = args.out_dir if args.out_dir is not None else PROGS
    meta_dir = args.meta_dir if args.meta_dir is not None else (OUT_DIR if args.out_dir is None else None)
    build_gokart_5(progs_dir=progs_dir, meta_dir=meta_dir)
