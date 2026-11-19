"""Procedural 3D MD3 Builder, High-Res Texture Generator & Animator for:
Go-Kart #2 ("Cyber-Nitro Aero GT" — Formula-E / Cyber Racer Kart).

Outputs (owned exclusively by kart-2):
  - progs/gk2_body.png        (1024x1024 RGB: midnight-carbon weave, cyan/amber stripes, Quake 'Q' nose decal)
  - progs/gk2_aero.png        (1024x1024 RGB: front/rear carbon wings, glowing cyan radiator intake slats, endplate graphics)
  - progs/gk2_seat.png        (1024x1024 RGB: carbon-kevlar shell, quilted cushion, electric-cyan bolsters & headrest)
  - progs/gk2_steer.png       (1024x1024 RGB: F1 butterfly yoke, OLED dash + glowing LED shift bar, cyan grips)
  - progs/gk2_thruster.png    (1024x1024 RGB: heat-blued titanium shroud, iris nozzle petals, cyan plasma stator ring)
  - progs/gk2_wheel.png       (1024x1024 RGB: racing slick tread, cyan-rimmed sidewall, 5-spoke gunmetal turbine alloy)
  - progs/gk2_flame.png       (512x512 RGBA: additive shock-diamond cyan/white-hot afterburner & explosion flash)
  - progs/gokart_2.md3        (64-frame IDP3 v15 model with 13 distinct surfaces)
  - progs/gokart_2.md3_0.skin (surface -> shader mapping)
  - source/mm_tools/out/gokart_2_meta.json

Usage:
  python source/mm_tools/gokart_2.py
"""
import argparse
import json
import math
import os
import struct
import sys

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
    rot_axis,
    rot_x,
    rot_y,
    rot_z,
    smoothstep,
    vadd,
    vcross,
    vdot,
    vlen,
    vlerp,
    vmul,
    vnorm,
    vsub,
)

# ---------------------------------------------------------------------------
# Constants & Shared Contract Coordinates
# ---------------------------------------------------------------------------
FRONT_WHEEL_X = 31.0
FRONT_WHEEL_Y = 24.5
FRONT_WHEEL_R = 9.0
FRONT_WHEEL_HW = 5.3

REAR_WHEEL_X = -31.0
REAR_WHEEL_Y = 26.5
REAR_WHEEL_R = 10.8
REAR_WHEEL_HW = 6.8

SEAT_POS = (-9.0, 0.0, 9.0)
STEER_POS = (13.0, 0.0, 24.0)

EXHAUST_TIPS = [
    {"x": -45.5, "y": +9.2, "z": 13.8, "dx": -0.994, "dy": +0.087, "dz": 0.070},
    {"x": -45.5, "y": -9.2, "z": 13.8, "dx": -0.994, "dy": -0.087, "dz": 0.070},
]

FRAME_NAMES = (
    [f"idle_{i:02d}" for i in range(12)]
    + [f"fast_{i:02d}" for i in range(16)]
    + [f"super_{i:02d}" for i in range(16)]
    + [f"explode_{i:02d}" for i in range(20)]
)
assert len(FRAME_NAMES) == 64

# Texture UV Sub-Rects (u0, v0, u1, v1) in quadrant layout
UV_Q1 = (0.02, 0.02, 0.48, 0.48)
UV_Q2 = (0.52, 0.02, 0.98, 0.48)
UV_Q3 = (0.02, 0.52, 0.48, 0.98)
UV_Q4 = (0.52, 0.52, 0.98, 0.98)

UV_Q4_A = (0.52, 0.52, 0.73, 0.73)
UV_Q4_B = (0.77, 0.52, 0.98, 0.73)
UV_Q4_C = (0.52, 0.77, 0.73, 0.98)
UV_Q4_D = (0.77, 0.77, 0.98, 0.98)


# ---------------------------------------------------------------------------
# Procedural Texture Synthesis (1024x1024 RGB + 512x512 RGBA Flame)
# ---------------------------------------------------------------------------
def _font(size, bold=True):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fbm(h, w, seed=42, octaves=(4, 8, 16, 32, 64)):
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


def _carbon_weave(h, w, scale=4, base_rgb=(32, 34, 38), hi_rgb=(44, 47, 52), noise=None):
    yy, xx = np.mgrid[0:h, 0:w]
    phase = (xx // scale + yy // scale) % 2
    sub_u = (xx % scale) / float(scale)
    sub_v = (yy % scale) / float(scale)
    sheen_a = np.sin(sub_u * math.pi) * 0.65 + 0.35
    sheen_b = np.sin(sub_v * math.pi) * 0.65 + 0.35
    w_fac = np.where(phase == 0, sheen_a, sheen_b * 0.85)
    out = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        out[..., c] = base_rgb[c] + (hi_rgb[c] - base_rgb[c]) * w_fac
    if noise is not None:
        out += noise[..., None] * 5.0
    return np.clip(out, 8, 255)


def _draw_quake_q(arr_q, cx, cy, radius, cyan=(195, 200, 208), amber=(168, 38, 38), rot90=False):
    """Draws a crisp brushed-steel Quake 'Q' emblem directly onto a numpy RGB quadrant."""
    h, w, _ = arr_q.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx0 = (xx - cx) / radius
    dy0 = (yy - cy) / radius
    if rot90:
        # Rotate so top horns point toward -U (cowl) and spear points toward +U (nose tip)
        dx, dy = -dy0, dx0
    else:
        dx, dy = dx0, dy0
    r = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)  # top is -pi/2, bottom is +pi/2

    # Outer cyan aura
    ring_dist = np.abs(r - 0.76)
    # Crescent gap at top (-pi/2 +/- 0.42 rad)
    top_gap = np.abs(((ang + math.pi * 0.5 + math.pi) % (2 * math.pi)) - math.pi)
    # Thickness tapers toward the top horns
    horn_taper = np.clip((top_gap - 0.34) / 0.45, 0.0, 1.0)
    ring_half_w = 0.16 * horn_taper + 0.03 * np.clip(1.0 - r * 0.3, 0.0, 1.0)
    ring_mask = np.clip(1.0 - (ring_dist - ring_half_w) / 0.045, 0.0, 1.0) * (top_gap > 0.30).astype(np.float32)

    # Vertical Quake spear (dx near 0, dy from -0.25 down to +1.18)
    spear_hw = 0.11 * np.clip(1.0 - (dy - 0.55) * 0.9, 0.18, 1.0)
    spear_mask = (
        np.clip(1.0 - (np.abs(dx) - spear_hw) / 0.035, 0.0, 1.0)
        * np.clip((dy + 0.18) / 0.12, 0.0, 1.0)
        * np.clip((1.16 - dy) / 0.12, 0.0, 1.0)
    )
    # Crossbar / anvil teeth near bottom of ring
    tooth_mask = (
        np.clip(1.0 - (np.abs(dx) - 0.24) / 0.03, 0.0, 1.0)
        * np.clip(1.0 - (np.abs(dy - 0.68) - 0.09) / 0.03, 0.0, 1.0)
    )

    q_mask = np.clip(np.maximum(ring_mask, np.maximum(spear_mask, tooth_mask)), 0.0, 1.0)

    # Subtle dark metallic rim halo (no neon glow)
    glow_ring = np.exp(-((ring_dist - ring_half_w * 0.8) ** 2) / 0.010) * (top_gap > 0.22)
    glow_spear = np.exp(-(dx * dx) / 0.020) * (dy > -0.25) * (dy < 1.25)
    glow = np.clip(np.maximum(glow_ring, glow_spear * 0.85), 0.0, 1.0) * 0.25

    # Metallic bevel inside Q
    bevel = np.clip(0.68 + 0.32 * (-dx * 0.5 - dy * 0.5), 0.35, 1.0)
    inner_edge = np.clip(1.0 - np.abs(q_mask - 0.65) * 3.0, 0.0, 1.0)

    for c in range(3):
        arr_q[..., c] = arr_q[..., c] * (1.0 - 0.35 * glow) + cyan[c] * glow * 0.35
        fill_c = 205.0 * bevel * (1.0 - 0.25 * inner_edge) + amber[c] * 0.25 * inner_edge
        arr_q[..., c] = arr_q[..., c] * (1.0 - q_mask) + fill_c * q_mask


def build_body_texture(progs_dir):
    W = H = 1024
    nf = _fbm(H, W, seed=201, octaves=(4, 8, 16, 32))
    arr = _carbon_weave(H, W, scale=4, base_rgb=(36, 39, 44), hi_rgb=(46, 50, 56), noise=nf)

    # Q1: Wedge Nose Top Deck + Subtle Silver/Crimson Aero Livery + Quake 'Q' Decal
    q1 = arr[:512, :512].copy()
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    u = xx / 511.0  # nose length +X (0 = cowl, 1 = nose tip)
    v = (yy - 255.5) / 255.5  # -1..+1 across width
    chevron_y = 0.72 * (1.0 - 0.68 * u)
    silver_stripe = np.exp(-((np.abs(v) - chevron_y) ** 2) / 0.0018)
    red_stripe = np.exp(-((np.abs(v) - (chevron_y - 0.08)) ** 2) / 0.00055)
    center_line = np.exp(-((np.abs(v)) ** 2) / 0.00040) * (u > 0.58)
    for c, sv, rd in ((0, 178, 154), (1, 182, 34), (2, 188, 36)):
        q1[..., c] = np.clip(
            q1[..., c] * (1.0 - 0.75 * silver_stripe) + sv * silver_stripe * 0.85
            + rd * (red_stripe * 0.85 + 0.5 * center_line),
            10, 225,
        )
    _draw_quake_q(q1, cx=245.0, cy=255.5, radius=105.0, rot90=True)
    arr[:512, :512] = q1

    # Q2: Satin Dark Graphite Monocoque Flank, Cockpit Rim & Spine (clean seam & rivets, no wrapped text)
    q2 = _carbon_weave(512, 512, scale=4, base_rgb=(42, 46, 52), hi_rgb=(54, 58, 65), noise=nf[:512, 512:])
    yy2, xx2 = np.mgrid[0:512, 0:512].astype(np.float32)
    v2 = yy2 / 511.0
    u2 = xx2 / 511.0
    seam = np.exp(-((u2 - 0.50) ** 2) / 0.00004) + np.exp(-((v2 - 0.72) ** 2) / 0.00004)
    q2 = np.clip(q2 * (1.0 - 0.45 * seam[..., None]), 12, 180)
    im_q2 = Image.fromarray(q2.astype(np.uint8), mode="RGB")
    dr2 = ImageDraw.Draw(im_q2)
    for rx in range(48, 480, 64):
        dr2.ellipse((rx - 4, 348, rx + 4, 356), fill=(115, 120, 128), outline=(24, 26, 30))
    arr[:512, 512:] = np.asarray(im_q2, dtype=np.float32)

    # Q3: Undertray / Venturi Diffuser & Wishbone Structural Charcoal Matte
    q3 = _carbon_weave(512, 512, scale=4, base_rgb=(24, 26, 30), hi_rgb=(32, 35, 40), noise=nf[512:, :512])
    im_q3 = Image.fromarray(q3.astype(np.uint8), mode="RGB")
    dr3 = ImageDraw.Draw(im_q3)
    for yk in range(32, 512, 64):
        dr3.line((0, yk, 512, yk), fill=(36, 40, 46), width=2)
    dr3.rectangle((16, 420, 496, 444), fill=(72, 76, 82))
    arr[512:, :512] = np.asarray(im_q3, dtype=np.float32)

    # Q4: Footwell Knurled Floor, Brushed Pedals, Red FIA Rain Light
    q4a = _carbon_weave(256, 256, scale=10, base_rgb=(22, 24, 28), hi_rgb=(44, 48, 54), noise=nf[512:768, 512:768])
    arr[512:768, 512:768] = q4a
    u_p = np.linspace(0, 1, 256, dtype=np.float32)[None, :]
    ped = 155.0 + 25.0 * np.sin(u_p * 42.0) + 8.0 * nf[512:768, 768:]
    arr[512:768, 768:, 0] = np.clip(ped * 0.98, 40, 225)
    arr[512:768, 768:, 1] = np.clip(ped * 0.99, 40, 228)
    arr[512:768, 768:, 2] = np.clip(ped * 1.02, 45, 232)
    arr[768:, 512:768] = 95.0 + 12.0 * nf[768:, 512:768, None]
    # Q4_D: Deep Red FIA LED Rain Light array
    im_rl = Image.new("RGB", (256, 256), (18, 18, 22))
    dr_rl = ImageDraw.Draw(im_rl)
    for row in range(30, 226, 36):
        for col in range(30, 226, 36):
            dr_rl.ellipse((col, row, col + 22, row + 22), fill=(182, 24, 24), outline=(228, 120, 110))
    arr[768:, 768:] = np.asarray(im_rl, dtype=np.float32)

    out_path = os.path.join(progs_dir, "gk2_body.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_aero_texture(progs_dir):
    W = H = 1024
    nf = _fbm(H, W, seed=202, octaves=(4, 8, 16, 32))
    arr = _carbon_weave(H, W, scale=4, base_rgb=(40, 44, 50), hi_rgb=(52, 56, 64), noise=nf)

    # Q1: Satin Racing Gunmetal-Silver Aero Shell (sidepods, front wing, DRS flap - clean without wrap rings)
    q1 = _carbon_weave(512, 512, scale=4, base_rgb=(88, 93, 100), hi_rgb=(102, 108, 116), noise=nf[:512, :512])
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    u = xx / 511.0
    v = yy / 511.0
    # Subtle satin panel highlight and fine seam line
    sheen = 0.94 + 0.08 * np.sin(u * math.pi)
    seam = np.exp(-((v - 0.50) ** 2) / 0.00012)
    q1 = np.clip(q1 * sheen[..., None] * (1.0 - 0.25 * seam[..., None]), 20, 185)
    arr[:512, :512] = q1

    # Q2: Dark Gunmetal Aluminum Radiator Intake Slats + Heat Exchanger Fins
    im_rad = Image.new("RGB", (512, 512), (20, 22, 26))
    dr_rad = ImageDraw.Draw(im_rad)
    for xk in range(4, 512, 8):
        dr_rad.line((xk, 0, xk, 512), fill=(34, 38, 44), width=2)
    for yk in range(48, 480, 92):
        dr_rad.rectangle((12, yk - 14, 500, yk + 14), fill=(58, 62, 68))
        dr_rad.rectangle((12, yk - 6, 500, yk + 6), fill=(96, 102, 110))
        dr_rad.rectangle((12, yk - 2, 500, yk + 2), fill=(128, 134, 142))
    dr_rad.rectangle((0, 0, 511, 18), fill=(48, 52, 58))
    dr_rad.rectangle((0, 494, 511, 511), fill=(48, 52, 58))
    arr[:512, 512:] = np.asarray(im_rad, dtype=np.float32)

    # Q3: Wing Endplates (Dark Graphite w/ Muted Red & Silver Accent)
    im_ep = Image.fromarray(arr[512:, :512].astype(np.uint8), mode="RGB")
    dr_ep = ImageDraw.Draw(im_ep)
    dr_ep.polygon([(20, 460), (120, 460), (440, 40), (360, 40)], fill=(142, 34, 34))
    dr_ep.polygon([(135, 460), (175, 460), (475, 55), (455, 40)], fill=(186, 190, 196))
    dr_ep.text((38, 48), "02", fill=(216, 220, 226), font=_font(84))
    dr_ep.rectangle((0, 485, 511, 511), fill=(72, 76, 84))
    arr[512:, :512] = np.asarray(im_ep, dtype=np.float32)

    # Q4: Split Rear Wing Mainplane (Dark Graphite w/ Clean Silver & Muted Red Edge Trim)
    im_rw = Image.fromarray(arr[512:, 512:].astype(np.uint8), mode="RGB")
    dr_rw = ImageDraw.Draw(im_rw)
    dr_rw.rectangle((0, 40, 511, 66), fill=(176, 180, 186))
    dr_rw.rectangle((0, 74, 511, 90), fill=(142, 34, 34))
    dr_rw.rectangle((0, 424, 511, 440), fill=(142, 34, 34))
    dr_rw.rectangle((0, 448, 511, 474), fill=(176, 180, 186))
    arr[512:, 512:] = np.asarray(im_rw, dtype=np.float32)

    out_path = os.path.join(progs_dir, "gk2_aero.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_seat_texture(progs_dir):
    W = H = 1024
    nf = _fbm(H, W, seed=203, octaves=(4, 8, 16, 32))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    # Q1: Dark Carbon Composite Seat Shell
    yy, xx = np.mgrid[0:512, 0:512]
    phase = (xx // 6 + yy // 6) % 2
    sub_u = np.sin(((xx % 6) / 6.0) * math.pi)
    sub_v = np.sin(((yy % 6) / 6.0) * math.pi)
    for c, kc, cc in ((0, 44, 28), (1, 46, 30), (2, 50, 34)):
        arr[:512, :512, c] = np.where(phase == 0, kc * (0.55 + 0.45 * sub_u), cc * (0.55 + 0.45 * sub_v)) + nf[:512, :512] * 4.5

    # Q2: Quilted Charcoal Alcantara Center Cushion w/ Silver-Grey Stitch
    q2 = np.full((512, 512, 3), 30.0, dtype=np.float32) + nf[:512, 512:, None] * 4.5
    im_q2 = Image.fromarray(np.clip(q2, 14, 75).astype(np.uint8), mode="RGB")
    dr2 = ImageDraw.Draw(im_q2)
    for k in range(-512, 1024, 64):
        dr2.line((k, 0, k + 512, 512), fill=(96, 100, 108), width=2)
        dr2.line((k, 512, k + 512, 0), fill=(96, 100, 108), width=2)
    arr[:512, 512:] = np.asarray(im_q2, dtype=np.float32)

    # Q3: Matte Charcoal-Slate Side Bolsters + Subtle Muted Crimson Piping
    q3 = np.zeros((512, 512, 3), dtype=np.float32)
    q3[..., 0] = 36.0 + nf[512:, :512] * 5.0
    q3[..., 1] = 38.0 + nf[512:, :512] * 5.0
    q3[..., 2] = 42.0 + nf[512:, :512] * 5.5
    im_q3 = Image.fromarray(np.clip(q3, 12, 95).astype(np.uint8), mode="RGB")
    dr3 = ImageDraw.Draw(im_q3)
    for yk in range(40, 480, 56):
        dr3.line((0, yk, 512, yk), fill=(26, 28, 32), width=6)
    dr3.rectangle((0, 0, 511, 16), fill=(142, 36, 36))
    dr3.rectangle((0, 496, 511, 511), fill=(142, 36, 36))
    arr[512:, :512] = np.asarray(im_q3, dtype=np.float32)

    # Q4: Charcoal Headrest Pad with Brushed-Silver Quake 'Q' Crest
    q4 = q3.copy()
    _draw_quake_q(q4, cx=256.0, cy=256.0, radius=115.0, cyan=(185, 190, 198), amber=(148, 38, 38))
    arr[512:, 512:] = q4

    out_path = os.path.join(progs_dir, "gk2_seat.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_steer_texture(progs_dir):
    W = H = 1024
    nf = _fbm(H, W, seed=204, octaves=(4, 8, 16, 32))
    arr = _carbon_weave(H, W, scale=4, base_rgb=(28, 30, 34), hi_rgb=(42, 46, 52), noise=nf)

    # Q1: Butterfly Yoke Faceplate + Rotary Dials + Buttons
    im1 = Image.fromarray(arr[:512, :512].astype(np.uint8), mode="RGB")
    dr1 = ImageDraw.Draw(im1)
    for cx, cy, col, lbl in [
        (135, 170, (168, 42, 42), "BOOST"),
        (375, 170, (168, 172, 178), "DRS"),
        (165, 355, (108, 114, 122), "MAP"),
        (345, 355, (152, 112, 42), "PWR"),
    ]:
        dr1.ellipse((cx - 46, cy - 46, cx + 46, cy + 46), fill=(22, 24, 28), outline=col, width=5)
        dr1.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=col)
        dr1.text((cx - 32, cy + 54), lbl, fill=(195, 200, 206), font=_font(24))
    arr[:512, :512] = np.asarray(im1, dtype=np.float32)

    # Q2: Clean Motorsport LCD Telemetry Display & Shift-Light Bar
    im2 = Image.new("RGB", (512, 512), (14, 16, 20))
    dr2 = ImageDraw.Draw(im2)
    for i in range(15):
        lx = 26 + i * 31
        col = (64, 156, 72) if i < 6 else ((192, 148, 42) if i < 11 else (182, 42, 42))
        dr2.ellipse((lx, 26, lx + 22, 68), fill=col, outline=(90, 95, 102))
    dr2.rectangle((24, 96, 488, 468), fill=(18, 22, 28), outline=(120, 126, 134), width=4)
    dr2.text((52, 126), "196 KM/H", fill=(220, 224, 228), font=_font(72))
    dr2.text((56, 238), "RPM 11400", fill=(196, 152, 52), font=_font(52))
    dr2.text((56, 338), "GEAR 6  +0.42", fill=(185, 190, 198), font=_font(44))
    arr[:512, 512:] = np.asarray(im2, dtype=np.float32)

    # Q3: Matte Black Alcantara Grips
    q3 = np.zeros((512, 512, 3), dtype=np.float32)
    q3[..., 0] = 28.0 + nf[512:, :512] * 5.0
    q3[..., 1] = 30.0 + nf[512:, :512] * 5.0
    q3[..., 2] = 33.0 + nf[512:, :512] * 5.5
    arr[512:, :512] = np.clip(q3, 12, 75)

    # Q4: Anodized Titanium Column
    u_c = np.linspace(0, 2 * math.pi, 512, dtype=np.float32)[None, :]
    ti = 105.0 + 30.0 * np.cos(u_c) + 10.0 * nf[512:, 512:]
    arr[512:, 512:, 0] = np.clip(ti * 0.96, 24, 200)
    arr[512:, 512:, 1] = np.clip(ti * 0.98, 24, 204)
    arr[512:, 512:, 2] = np.clip(ti * 1.03, 28, 212)

    out_path = os.path.join(progs_dir, "gk2_steer.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_thruster_texture(progs_dir):
    W = H = 1024
    nf = _fbm(H, W, seed=205, octaves=(4, 8, 16, 32))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    # Q1: Brushed Stainless / Heat-Tempered Titanium Exhaust Shroud
    u = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]
    refl = 0.58 + 0.22 * np.cos(u - 0.8) + 0.12 * np.cos(2.0 * u) + 0.03 * nf[:512, :512]
    heat_straw = np.exp(-((v - 0.72) ** 2) / 0.025)
    bands = 1.0 - 0.16 * np.exp(-((v - 0.30) ** 2) / 0.0012) - 0.16 * np.exp(-((v - 0.65) ** 2) / 0.0012)
    arr[:512, :512, 0] = np.clip((refl * 165.0 + heat_straw * 24.0) * bands, 24, 228)
    arr[:512, :512, 1] = np.clip((refl * 164.0 + heat_straw * 10.0) * bands, 24, 224)
    arr[:512, :512, 2] = np.clip((refl * 168.0 - heat_straw * 18.0) * bands, 24, 224)

    # Q2: Dark Carbon-Titanium Iris Nozzle Petals w/ Subtle Brushed Steel Rim
    q2 = np.full((512, 512, 3), 38.0, dtype=np.float32) + nf[:512, 512:, None] * 6.0
    v2 = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]
    edge_rim = np.exp(-((v2 - 0.92) ** 2) / 0.004)
    q2[..., 0] += edge_rim * 55.0
    q2[..., 1] += edge_rim * 56.0
    q2[..., 2] += edge_rim * 60.0
    arr[:512, 512:] = np.clip(q2, 14, 150)

    # Q3: Dark Metallic Turbine Baffle Core & Exhaust Cone
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    rx = (xx - 255.5) / 245.0
    ry = (yy - 255.5) / 245.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang = np.arctan2(ry, rx)
    ring = np.exp(-((rr - 0.72) ** 2) / 0.014) + 0.85 * np.exp(-((rr - 0.35) ** 2) / 0.012)
    vanes = 0.5 + 0.5 * np.cos(ang * 12.0)
    core = np.clip(ring * (0.65 + 0.35 * vanes), 0.0, 1.0)
    arr[512:, :512, 0] = np.clip(28.0 + 68.0 * core + 5.0 * nf[512:, :512], 12, 130)
    arr[512:, :512, 1] = np.clip(29.0 + 70.0 * core + 5.0 * nf[512:, :512], 12, 134)
    arr[512:, :512, 2] = np.clip(32.0 + 74.0 * core + 5.0 * nf[512:, :512], 14, 140)

    # Q4: Satin Dark Gunmetal Nozzle Trim Band
    arr[512:, 512:, 0] = 62.0 + nf[512:, 512:] * 6.0
    arr[512:, 512:, 1] = 65.0 + nf[512:, 512:] * 6.0
    arr[512:, 512:, 2] = 70.0 + nf[512:, 512:] * 6.0

    out_path = os.path.join(progs_dir, "gk2_thruster.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_wheel_texture(progs_dir):
    W = H = 1024
    nf = _fbm(H, W, seed=206, octaves=(4, 8, 16, 32))
    arr = np.zeros((H, W, 3), dtype=np.float32)

    # Q1: Low-Profile Wide Racing Slick Tread (clean matte dark rubber)
    ux = np.linspace(0.0, 1.0, 512, dtype=np.float32)[None, :]
    vy = np.linspace(0.0, 2.0 * math.pi, 512, dtype=np.float32)[:, None]
    shoulder = 1.0 - 0.22 * ((2.0 * ux - 1.0) ** 4)
    grooves = np.exp(-((ux - 0.24) ** 2) / 0.00045) + np.exp(-((ux - 0.76) ** 2) / 0.00045)
    rub = (38.0 - 14.0 * grooves) * shoulder + 4.0 * nf[:512, :512] + 2.5 * np.sin(vy * 3.0)
    arr[:512, :512, 0] = np.clip(rub * 0.99, 10, 85)
    arr[:512, :512, 1] = np.clip(rub * 1.00, 10, 85)
    arr[:512, :512, 2] = np.clip(rub * 1.03, 12, 88)

    # Q2: Polar Sidewall + Satin Silver Alloy Rim Lip
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    rx = (xx - 255.5) / 245.0
    ry = (yy - 255.5) / 245.0
    rr = np.sqrt(rx * rx + ry * ry)
    ang = np.arctan2(ry, rx)
    sw = 34.0 + 8.0 * np.exp(-((rr - 0.78) ** 2) / 0.008) + 4.0 * nf[:512, 512:]
    rim_lip = np.exp(-((rr - 0.56) ** 2) / 0.00085)
    rib_ticks = np.exp(-((rr - 0.84) ** 2) / 0.0003) * (np.cos(ang * 5.0) > 0.75)
    arr[:512, 512:, 0] = np.clip(sw + 105.0 * rim_lip + 24.0 * rib_ticks, 12, 185)
    arr[:512, 512:, 1] = np.clip(sw + 108.0 * rim_lip + 24.0 * rib_ticks, 12, 188)
    arr[:512, 512:, 2] = np.clip(sw + 112.0 * rim_lip + 26.0 * rib_ticks, 14, 192)

    # Q3: 5-Spoke Turbine Satin Gunmetal Alloy
    u3 = np.linspace(0, 1, 512, dtype=np.float32)[None, :]
    v3 = np.linspace(0, 1, 512, dtype=np.float32)[:, None]
    alloy = 108.0 + 28.0 * np.sin(u3 * math.pi) + 7.0 * nf[512:, :512]
    edge_c = np.exp(-((v3 - 0.90) ** 2) / 0.004) + np.exp(-((v3 - 0.10) ** 2) / 0.004)
    arr[512:, :512, 0] = np.clip(alloy * 0.96 + 32.0 * edge_c, 22, 195)
    arr[512:, :512, 1] = np.clip(alloy * 0.98 + 34.0 * edge_c, 22, 198)
    arr[512:, :512, 2] = np.clip(alloy * 1.03 + 38.0 * edge_c, 26, 205)

    # Q4: Center-Lock Steel Nut & Carbon Brake Rotor
    yy4, xx4 = np.mgrid[0:256, 0:256].astype(np.float32)
    r4 = np.sqrt(((xx4 - 127.5) / 120.0) ** 2 + ((yy4 - 127.5) / 120.0) ** 2)
    a4 = np.arctan2(yy4 - 127.5, xx4 - 127.5)
    rot_m = 82.0 + 18.0 * np.sin(r4 * 45.0) + 10.0 * np.cos(a4 * 10.0)
    arr[512:768, 512:768] = np.clip(rot_m[..., None] * np.array([0.96, 0.98, 1.02]), 18, 165)
    # Q4_B: Brushed Steel / Dark Gunmetal Center-Lock Nut
    arr[512:768, 768:] = np.array([128.0, 132.0, 138.0])
    # Q4_C: Muted Dark Red Brake Caliper
    arr[768:, 512:768] = np.array([142.0, 34.0, 34.0])
    # Q4_D: Inner Dark Barrel
    arr[768:, 768:] = 30.0 + 5.0 * nf[768:, 768:, None]

    out_path = os.path.join(progs_dir, "gk2_wheel.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(out_path, "PNG", optimize=True)
    return out_path


def build_flame_texture(progs_dir):
    """512x512 RGBA additive warm orange-amber / white-hot exhaust afterburner & explosion flash.
    Seamlessly wraps around U for 3D cylindrical plume sleeves and fades cleanly to 0 at V=1 tail.
    """
    W = H = 512
    rgba = np.zeros((H, W, 4), dtype=np.float32)

    yy, xx = np.mgrid[0:512, 0:256].astype(np.float32)
    u_wrap = (xx / 255.0) * 2.0 * math.pi  # seamless 0..2pi around tube
    v_n = yy / 511.0  # 0 at nozzle -> 1 at tail tip

    # Left half (u: 0..0.5, v: 0..1): Warm orange-amber outer exhaust plume
    mach = 0.52 + 0.48 * (np.cos(v_n * 2.0 * math.pi * 3.5) ** 2)
    streak = 0.86 + 0.14 * np.cos(u_wrap * 4.0 + v_n * 6.0)
    tail_fade = np.clip(1.0 - v_n ** 1.15, 0.0, 1.0) * np.clip(v_n / 0.04, 0.0, 1.0)
    intensity = np.clip(streak * tail_fade * (0.62 + 0.55 * mach), 0.0, 1.0)
    rgba[:, :256, 0] = np.clip(intensity * 255.0, 0, 255)
    rgba[:, :256, 1] = np.clip(intensity * (140.0 + 65.0 * intensity), 0, 255)
    rgba[:, :256, 2] = np.clip(intensity * (32.0 + 95.0 * (intensity ** 2.2)), 0, 255)
    rgba[:, :256, 3] = np.clip(intensity * 255.0, 0, 255)

    # Right half (u: 0.5..1.0, v: 0..1): White-gold inner core & explosion burst
    core_mach = 0.58 + 0.42 * (np.cos(v_n * 2.0 * math.pi * 4.5) ** 2)
    core_streak = 0.90 + 0.10 * np.cos(u_wrap * 3.0 - v_n * 8.0)
    core_i = np.clip(core_streak * np.clip(1.0 - v_n ** 1.05, 0.0, 1.0) * np.clip(v_n / 0.03, 0.0, 1.0) * core_mach, 0.0, 1.0)
    rgba[:, 256:, 0] = np.clip(core_i * 255.0, 0, 255)
    rgba[:, 256:, 1] = np.clip(core_i * 238.0, 0, 255)
    rgba[:, 256:, 2] = np.clip(core_i * 185.0, 0, 255)
    rgba[:, 256:, 3] = np.clip(core_i * 255.0, 0, 255)

    out_path = os.path.join(progs_dir, "gk2_flame.png")
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA").save(out_path, "PNG", optimize=True)
    return out_path


def build_all_textures(progs_dir):
    os.makedirs(progs_dir, exist_ok=True)
    return {
        "progs/gk2_body": build_body_texture(progs_dir),
        "progs/gk2_aero": build_aero_texture(progs_dir),
        "progs/gk2_seat": build_seat_texture(progs_dir),
        "progs/gk2_steer": build_steer_texture(progs_dir),
        "progs/gk2_thruster": build_thruster_texture(progs_dir),
        "progs/gk2_wheel": build_wheel_texture(progs_dir),
        "progs/gk2_flame": build_flame_texture(progs_dir),
    }


# ---------------------------------------------------------------------------
# Custom Procedural Mesh Helpers
# ---------------------------------------------------------------------------
class KartMesh(MeshPart):
    """Extends MeshPart with smooth closed-loop lofts, solid extruded polygons, and swept airfoils."""

    def add_loop_loft(self, rings, uv_rect=UV_Q1, cap_start=True, cap_end=True, smooth=False):
        """Lofts a sequence of 3D closed cross-section loops (each loop has N points ordered CCW around the loft axis).
        Produces crisp per-quad outward normals (or averaged smooth normals if smooth=True) and clean capped ends.
        """
        n_rings = len(rings)
        n_pts = len(rings[0])
        assert all(len(r) == n_pts for r in rings), "All loft rings must have equal point count"
        u0, v0, u1, v1 = uv_rect

        if not smooth:
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
        else:
            # Smooth vertex-averaged grid
            base = len(self.verts)
            cols = n_pts + 1
            pts_grid = []
            for ri in range(n_rings):
                vr = v0 + (v1 - v0) * (ri / float(n_rings - 1))
                for j in range(cols):
                    jj = j % n_pts
                    pts_grid.append(rings[ri][jj])
                    self.st.append((u0 + (u1 - u0) * (j / float(n_pts)), vr))
            acc_n = [[0.0, 0.0, 0.0] for _ in pts_grid]
            tris = []
            for ri in range(n_rings - 1):
                for j in range(n_pts):
                    a = ri * cols + j
                    b = (ri + 1) * cols + j
                    c = b + 1
                    d = a + 1
                    # Outward winding: compare with (t_loop x t_along)
                    t_loop = vsub(pts_grid[d], pts_grid[a])
                    t_along = vsub(pts_grid[b], pts_grid[a])
                    out_n = vcross(t_loop, t_along)
                    w_n = vcross(vsub(pts_grid[b], pts_grid[a]), vsub(pts_grid[c], pts_grid[a]))
                    quad_tris = ((a, b, c), (a, c, d)) if vdot(w_n, out_n) >= 0 else ((a, c, b), (a, d, c))
                    for tri in quad_tris:
                        fn = vcross(vsub(pts_grid[tri[1]], pts_grid[tri[0]]), vsub(pts_grid[tri[2]], pts_grid[tri[0]]))
                        tris.append(tri)
                        for vi in tri:
                            acc_n[vi][0] += fn[0]
                            acc_n[vi][1] += fn[1]
                            acc_n[vi][2] += fn[2]
            for ri in range(n_rings):
                i0, i1 = ri * cols, ri * cols + n_pts
                sn = vadd(acc_n[i0], acc_n[i1])
                acc_n[i0], acc_n[i1] = list(sn), list(sn)
            self.verts += pts_grid
            self.norms += [vnorm(n) for n in acc_n]
            self.tris += [(a + base, b + base, c + base) for (a, b, c) in tris]

        # End caps
        uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        for do_cap, ring_idx, nxt_idx, flip in ((cap_start, 0, 1, True), (cap_end, -1, -2, False)):
            if not do_cap:
                continue
            r_cur = rings[ring_idx]
            r_nxt = rings[nxt_idx]
            cx = sum(p[0] for p in r_cur) / n_pts
            cy = sum(p[1] for p in r_cur) / n_pts
            cz = sum(p[2] for p in r_cur) / n_pts
            ctr = (cx, cy, cz)
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
        """Adds a chamfered box centered at origin then rotated & translated to center."""
        hx, hy, hz = size_xyz[0] * 0.5, size_xyz[1] * 0.5, size_xyz[2] * 0.5
        tmp = KartMesh(self.mat)
        tmp.add_chamfer_box(-hx, +hx, -hy, +hy, -hz, +hz, ch=ch, uv_rect=uv_rect)
        self.append_part(tmp, offset=center, rx=rx, ry=ry, rz=rz)

    def add_airfoil_span(self, span_samples, uv_rect=UV_Q1, cap_ends=True):
        """Sweeps a clean 10-point cambered aero wing section across Y span.
        span_samples = [(y, x_le, x_te, z_c, thickness, camber_z, twist_deg), ...]
        """
        # Normalized airfoil loop (CCW in XZ plane looking from +Y -> actually ordered around chord)
        prof_norm = [
            (0.00, +0.10),  # LE
            (0.14, +0.88),
            (0.38, +1.00),
            (0.70, +0.62),
            (1.00, +0.16),  # TE top
            (1.00, -0.16),  # TE bottom
            (0.68, -0.45),
            (0.34, -0.60),
            (0.10, -0.48),
        ]
        rings = []
        for y, x_le, x_te, z_c, th, cam, tw in span_samples:
            chord = x_le - x_te
            mid_x = 0.5 * (x_le + x_te)
            ring = []
            for s, tz in prof_norm:
                px = x_le - s * chord
                pz = z_c + tz * th * 0.5 + cam * math.sin(s * math.pi)
                if tw:
                    rel = rot_y((px - mid_x, 0.0, pz - z_c), tw)
                    px, pz = mid_x + rel[0], z_c + rel[2]
                ring.append((px, y, pz))
            rings.append(ring)
        self.add_loop_loft(rings, uv_rect=uv_rect, cap_start=cap_ends, cap_end=cap_ends, smooth=False)


# ---------------------------------------------------------------------------
# Surface Builders (Static Local Frame 0 Geometry)
# ---------------------------------------------------------------------------
def build_body_shell():
    """Sculpted wedge-nose aero monocoque, undertray, Venturi diffuser, wishbones,
    footwell pedals, dorsal roll-hoop & shark-fin spine.
    """
    m = KartMesh("body")

    # 1) Sculpted Wedge Nose Cone (X = +14.0 .. +45.5, clear of footwell at X = +14..+26.5)
    # Upper nose cowling deck sits ABOVE the footwell (Z = 11.5..17.5 at cowl, tapering down to Z=6.2..8.5 at X=45.5)
    nose_specs = [
        # (x,   yc,  y_half, z_bot, z_top, bevel)
        (14.0, 0.0, 12.6, 13.8, 17.8, 0.9),
        (19.5, 0.0, 11.8, 12.2, 16.5, 0.9),
        (25.5, 0.0, 10.6, 9.8, 14.5, 0.8),
        (32.5, 0.0, 8.6, 5.4, 11.8, 0.8),
        (39.5, 0.0, 6.2, 4.6, 9.6, 0.7),
        (45.5, 0.0, 3.8, 4.6, 7.6, 0.6),
    ]
    nose_rings = []
    for x, yc, yh, zb, zt, bv in nose_specs:
        # 8-point sculpted octagonal nose section
        nose_rings.append([
            (x, yc + yh, zb + bv),
            (x, yc + yh * 0.88, zt - bv),
            (x, yc + yh * 0.45, zt),
            (x, yc - yh * 0.45, zt),
            (x, yc - yh * 0.88, zt - bv),
            (x, yc - yh, zb + bv),
            (x, yc - yh * 0.75, zb),
            (x, yc + yh * 0.75, zb),
        ])
    m.add_loop_loft(nose_rings, uv_rect=UV_Q2, cap_start=True, cap_end=True, smooth=False)

    # Dedicated Top Nose Decal Panel (X = +22 .. +44) mapped directly to Q1 (Quake 'Q' + cyan/amber livery!)
    decal_xs = [22.0, 27.5, 33.5, 39.5, 44.2]
    decal_ys = [8.2, 7.2, 5.9, 4.4, 2.8]
    decal_zs = [15.55, 13.75, 11.55, 9.65, 7.95]
    for i in range(len(decal_xs) - 1):
        xa, xb = decal_xs[i], decal_xs[i + 1]
        ya, yb = decal_ys[i], decal_ys[i + 1]
        za, zb = decal_zs[i], decal_zs[i + 1]
        ua = 0.03 + 0.44 * (i / float(len(decal_xs) - 1))
        ub = 0.03 + 0.44 * ((i + 1) / float(len(decal_xs) - 1))
        # Left half & right half slightly cambered for crisp specular highlight
        p_al = (xa, +ya, za - 0.15)
        p_ac = (xa, 0.0, za + 0.18)
        p_ar = (xa, -ya, za - 0.15)
        p_bl = (xb, +yb, zb - 0.12)
        p_bc = (xb, 0.0, zb + 0.12)
        p_br = (xb, -yb, zb - 0.12)
        n_l = vnorm(vcross(vsub(p_bl, p_ac), vsub(p_al, p_ac)))
        n_r = vnorm(vcross(vsub(p_ar, p_ac), vsub(p_bc, p_ac)))
        if n_l[2] < 0:
            n_l = vmul(n_l, -1.0)
        if n_r[2] < 0:
            n_r = vmul(n_r, -1.0)
        m.add_quad(p_ac, p_bc, p_bl, p_al, (ua, 0.25), (ub, 0.25), (ub, 0.47), (ua, 0.47), nrm=n_l)
        m.add_quad(p_ar, p_br, p_bc, p_ac, (ua, 0.03), (ub, 0.03), (ub, 0.25), (ua, 0.25), nrm=n_r)

    # 2) Flat Carbon Undertray Floor (X = -41 .. +43, Z = 2.6 .. 4.0)
    # Narrower between wheels, wider between axles (-20..+20)
    m.add_chamfer_box(-22.0, +24.0, -14.8, +14.8, 2.6, 4.0, ch=0.25, uv_rect=UV_Q3)
    m.add_chamfer_box(+24.0, +42.0, -9.8, +9.8, 2.6, 4.0, ch=0.25, uv_rect=UV_Q3)
    m.add_chamfer_box(-41.5, -22.0, -14.2, +14.2, 2.6, 4.0, ch=0.25, uv_rect=UV_Q3)

    # 3) Left & Right Monocoque Cockpit Tub Coaming Walls (strictly |Y| >= 13.2 so |Y| <= 13.0 is wide open!)
    for sy in (+1.0, -1.0):
        tub_rings = []
        tub_secs = [
            # (x,   y_in,  y_out, z_bot, z_top)
            (-24.0, 12.2, 14.8, 4.0, 15.8),
            (-16.0, 13.3, 15.2, 4.0, 14.8),
            (-2.0,  13.3, 15.2, 4.0, 13.6),
            (+11.0, 13.2, 15.0, 4.0, 15.2),
            (+16.5, 11.4, 13.8, 4.0, 16.5),
            (+24.5, 9.8,  12.0, 4.0, 13.8),
        ]
        for x, yi, yo, zb, zt in tub_secs:
            ya, yb = sy * yi, sy * yo
            y_lo, y_hi = min(ya, yb), max(ya, yb)
            tub_rings.append([
                (x, y_hi, zb + 0.3),
                (x, y_hi, zt - 0.5),
                (x, 0.5 * (y_lo + y_hi) + 0.3 * (y_hi - y_lo), zt),
                (x, 0.5 * (y_lo + y_hi) - 0.3 * (y_hi - y_lo), zt),
                (x, y_lo, zt - 0.5),
                (x, y_lo, zb + 0.3),
                (x, y_lo + 0.3, zb),
                (x, y_hi - 0.3, zb),
            ])
        m.add_loop_loft(tub_rings, uv_rect=UV_Q2, cap_start=True, cap_end=True)

    # 4) Footwell Floor Plate & Machined Twin Pedals (X = +14..+26, |Y| <= 9.5, Z = 4.0..10.5)
    m.add_chamfer_box(+14.0, +27.0, -9.5, +9.5, 4.0, 4.5, ch=0.12, uv_rect=UV_Q4_A)
    for py in (+4.0, -4.0):
        # Pedal arm
        m.add_tube([(26.8, py, 5.2), (25.2, py, 9.6)], [0.48, 0.44], segs=8, uv_rect=UV_Q4_C)
        # Brushed aluminum pedal pad
        m.add_box_oriented((24.8, py, 9.2), (0.6, 2.8, 3.6), ry=18.0, ch=0.12, uv_rect=UV_Q4_B)

    # 5) Front Wishbone Suspension Arms & Pushrods (connecting bulkhead to front wheel hubs)
    for sy in (+1.0, -1.0):
        hub = (FRONT_WHEEL_X, sy * (FRONT_WHEEL_Y - 2.6), FRONT_WHEEL_R)
        # Upper wishbone A-arm
        m.add_tube([(FRONT_WHEEL_X + 4.5, sy * 8.2, 11.4), (hub[0], hub[1], hub[2] + 1.8)], [0.55, 0.45], segs=8, uv_rect=UV_Q3)
        m.add_tube([(FRONT_WHEEL_X - 5.5, sy * 9.5, 11.6), (hub[0], hub[1], hub[2] + 1.8)], [0.55, 0.45], segs=8, uv_rect=UV_Q3)
        # Lower wishbone A-arm
        m.add_tube([(FRONT_WHEEL_X + 4.2, sy * 8.6, 5.2), (hub[0], hub[1], hub[2] - 2.0)], [0.62, 0.48], segs=8, uv_rect=UV_Q3)
        m.add_tube([(FRONT_WHEEL_X - 5.8, sy * 9.8, 5.4), (hub[0], hub[1], hub[2] - 2.0)], [0.62, 0.48], segs=8, uv_rect=UV_Q3)
        # Angled pushrod damper strut
        m.add_tube([(FRONT_WHEEL_X - 1.5, sy * 7.8, 12.8), (hub[0], hub[1], hub[2] - 1.4)], [0.46, 0.42], segs=8, uv_rect=UV_Q4_C)
        # Upright hub carrier
        m.add_chamfer_box(hub[0] - 1.8, hub[0] + 1.8, min(hub[1], hub[1] - sy * 1.4), max(hub[1], hub[1] - sy * 1.4), hub[2] - 2.6, hub[2] + 2.6, ch=0.25, uv_rect=UV_Q4_C)

    # 6) Rear Engine/Battery Spine & Roll Hoop Fairing (strictly behind X = -22.0!)
    spine_rings = []
    spine_secs = [
        (-22.5, 11.5, 4.0, 18.0),
        (-26.5, 10.2, 4.0, 22.5),
        (-32.5, 8.2, 4.0, 23.0),
        (-38.5, 6.4, 4.2, 18.5),
        (-43.5, 4.5, 5.0, 12.0),
    ]
    for x, yh, zb, zt in spine_secs:
        spine_rings.append([
            (x, +yh, zb + 0.5),
            (x, +yh * 0.72, zt - 1.4),
            (x, +yh * 0.25, zt),
            (x, -yh * 0.25, zt),
            (x, -yh * 0.72, zt - 1.4),
            (x, -yh, zb + 0.5),
            (x, -yh * 0.8, zb),
            (x, +yh * 0.8, zb),
        ])
    m.add_loop_loft(spine_rings, uv_rect=UV_Q2, cap_start=True, cap_end=True)

    # Dorsal Aero Shark-Fin & Roll Hoop Scoop (X = -24.5 .. -41.5, |Y| <= 1.8, Z = 21 .. 31)
    fin_rings = [
        [(-24.5, +1.8, 21.0), (-24.5, +1.2, 30.8), (-24.5, -1.2, 30.8), (-24.5, -1.8, 21.0)],
        [(-31.0, +1.4, 21.0), (-31.0, +0.9, 29.8), (-31.0, -0.9, 29.8), (-31.0, -1.4, 21.0)],
        [(-38.0, +0.9, 17.5), (-38.0, +0.6, 26.5), (-38.0, -0.6, 26.5), (-38.0, -0.9, 17.5)],
        [(-42.0, +0.6, 11.5), (-42.0, +0.4, 21.0), (-42.0, -0.4, 21.0), (-42.0, -0.6, 11.5)],
    ]
    m.add_loop_loft(fin_rings, uv_rect=UV_Q2, cap_start=True, cap_end=True)

    # FIA Cyan Rain/Telemetry Tail Light Pod (X = -43.5 .. -45.2, |Y| <= 1.9, Z = 7.0..10.5)
    m.add_chamfer_box(-45.2, -43.0, -1.9, +1.9, 7.0, 10.4, ch=0.25, uv_rect=UV_Q4_D)

    # 7) Rear Suspension Axle Housing, Rear Wishbones & Multi-Strake Venturi Diffuser
    m.add_tube([(REAR_WHEEL_X, -23.5, REAR_WHEEL_R), (REAR_WHEEL_X, +23.5, REAR_WHEEL_R)], [1.15, 1.15], segs=12, uv_rect=UV_Q4_C)
    for sy in (+1.0, -1.0):
        rhub = (REAR_WHEEL_X, sy * (REAR_WHEEL_Y - 3.4), REAR_WHEEL_R)
        m.add_tube([(REAR_WHEEL_X + 6.5, sy * 9.5, 6.2), (rhub[0], rhub[1], rhub[2] - 2.0)], [0.65, 0.52], segs=8, uv_rect=UV_Q3)
        m.add_tube([(REAR_WHEEL_X - 4.5, sy * 9.0, 12.2), (rhub[0], rhub[1], rhub[2] + 1.8)], [0.60, 0.48], segs=8, uv_rect=UV_Q3)

    # Rear Venturi Diffuser Ramp + 5 Vertical Aero Strakes (X = -32 .. -45.0)
    diff_rings = [
        [(-32.0, +14.5, 2.7), (-32.0, +14.5, 4.0), (-32.0, -14.5, 4.0), (-32.0, -14.5, 2.7)],
        [(-38.5, +15.8, 4.4), (-38.5, +15.8, 5.8), (-38.5, -15.8, 5.8), (-38.5, -15.8, 4.4)],
        [(-45.0, +16.8, 6.8), (-45.0, +16.8, 8.2), (-45.0, -16.8, 8.2), (-45.0, -16.8, 6.8)],
    ]
    m.add_loop_loft(diff_rings, uv_rect=UV_Q3, cap_start=True, cap_end=True)
    for y_strake in (-14.5, -7.2, 0.0, +7.2, +14.5):
        m.add_loop_loft([
            [(-33.5, y_strake + 0.35, 2.7), (-33.5, y_strake + 0.35, 4.2), (-33.5, y_strake - 0.35, 4.2), (-33.5, y_strake - 0.35, 2.7)],
            [(-44.8, y_strake + 0.35, 3.2), (-44.8, y_strake + 0.35, 7.6), (-44.8, y_strake - 0.35, 7.6), (-44.8, y_strake - 0.35, 3.2)],
        ], uv_rect=UV_Q3, cap_start=True, cap_end=True)

    return m


def build_front_wing():
    """Low-drag F1 multi-element splitter wing + twin curved endplates + diveplanes."""
    m = KartMesh("aero")

    # Mainplane lower splitter (Y = -28.0 .. +28.0, swept nose X=+49.2 at center -> +45.5 at tips)
    main_spans = [
        (-28.0, 45.5, 39.5, 3.6, 1.0, 0.25, -4.0),
        (-19.0, 47.2, 40.5, 3.3, 1.1, 0.30, -2.5),
        (-9.0,  48.6, 41.5, 3.2, 1.1, 0.25, -1.0),
        (0.0,   49.2, 42.0, 3.2, 1.2, 0.20,  0.0),
        (+9.0,  48.6, 41.5, 3.2, 1.1, 0.25, -1.0),
        (+19.0, 47.2, 40.5, 3.3, 1.1, 0.30, -2.5),
        (+28.0, 45.5, 39.5, 3.6, 1.0, 0.25, -4.0),
    ]
    m.add_airfoil_span(main_spans, uv_rect=UV_Q1, cap_ends=False)

    # Upper cascade aero flaps (split left & right, outboard of nose cone |Y| = 7.0 .. 27.8)
    for sy in (+1.0, -1.0):
        ys = sorted([sy * 7.2, sy * 14.5, sy * 22.0, sy * 27.8])
        flap_spans = []
        for y in ys:
            ay = abs(y)
            t = (ay - 7.2) / 20.6
            flap_spans.append((y, 44.5 - 2.0 * t, 39.8 - 1.5 * t, 5.2 + 1.4 * t, 0.85, 0.45, -14.0))
        m.add_airfoil_span(flap_spans, uv_rect=UV_Q1, cap_ends=True)

    # Twin sculpted curved F1 Endplates (at Y = +-28.2) + outer aero diveplane flicks
    for sy in (+1.0, -1.0):
        y_in = sy * 27.6
        y_out = sy * 28.6
        y0, y1 = min(y_in, y_out), max(y_in, y_out)
        ep_rings = [
            [(46.5, y1, 2.8), (46.5, y1, 7.2), (46.5, y0, 7.2), (46.5, y0, 2.8)],
            [(43.0, y1 + sy * 0.4, 2.8), (43.0, y1 + sy * 0.4, 9.6), (43.0, y0 + sy * 0.4, 9.6), (43.0, y0 + sy * 0.4, 2.8)],
            [(39.0, y1 + sy * 0.8, 3.2), (39.0, y1 + sy * 0.8, 10.6), (39.0, y0 + sy * 0.8, 10.6), (39.0, y0 + sy * 0.8, 3.2)],
        ]
        m.add_loop_loft(ep_rings, uv_rect=UV_Q3, cap_start=True, cap_end=True)

        # Outer wingtip diveplane canard
        dp_ys = sorted([sy * 28.4, sy * 30.8])
        m.add_airfoil_span([
            (dp_ys[0], 45.2, 40.5, 6.4, 0.65, 0.25, -18.0),
            (dp_ys[1], 44.0, 40.2, 7.2, 0.55, 0.20, -22.0),
        ], uv_rect=UV_Q1, cap_ends=True)

    # Twin nose-cone pylons connecting wing to wedge nose
    for py in (+3.4, -3.4):
        m.add_chamfer_box(40.2, 44.8, py - 0.5, py + 0.5, 3.4, 7.4, ch=0.14, uv_rect=UV_Q1)

    return m


def build_sidepods():
    """Sculpted aero sidepods with dramatic undercut & glowing cyan radiator intake slats.
    Strictly outside |Y| >= 13.3 so |Y| <= 13.0 cockpit remains wide open!
    """
    m = KartMesh("aero")

    for sy in (+1.0, -1.0):
        # Outer aerodynamic sidepod body (X = -24.5 .. +14.0, |Y| = 13.3 .. 23.6)
        secs = [
            # (x,   y_in, y_out_bot, y_out_top, z_bot, z_mid, z_top)
            (-24.5, 13.4, 15.0, 15.8, 4.2, 7.8, 12.2),
            (-17.5, 13.5, 17.8, 19.6, 3.8, 8.5, 15.0),
            (-8.0,  13.5, 20.6, 23.4, 3.5, 9.2, 16.6),
            (+3.0,  13.5, 21.4, 23.8, 3.4, 9.6, 17.0),
            (+10.5, 13.5, 19.8, 22.8, 3.8, 9.8, 16.4),
            (+14.0, 13.5, 17.5, 21.2, 4.6, 10.0, 15.2),
        ]
        rings = []
        for x, yi, yob, yot, zb, zm, zt in secs:
            y_in = sy * yi
            y_ob = sy * yob
            y_ot = sy * yot
            y_om = sy * (0.5 * (yob + yot) + 0.6)
            ring = [
                (x, y_in, zb),
                (x, y_ob, zb + 0.6),  # undercut corner
                (x, y_om, zm),        # outer shoulder bulge
                (x, y_ot, zt - 1.4),
                (x, sy * (0.55 * yi + 0.45 * yot), zt),
                (x, y_in, zt - 0.5),
            ]
            if sy < 0:
                ring = list(reversed(ring))
            rings.append(ring)
        m.add_loop_loft(rings, uv_rect=UV_Q1, cap_start=True, cap_end=True)

        # Forward-facing Glowing Cyan Radiator Intake Slat Assembly (X = +10.8 .. +14.8, |Y| = 14.5 .. 21.2)
        y_lo, y_hi = sorted([sy * 14.6, sy * 21.2])
        # Intake shroud frame
        m.add_chamfer_box(+13.2, +15.0, y_lo, y_hi, 14.4, 15.4, ch=0.18, uv_rect=UV_Q1)
        m.add_chamfer_box(+13.2, +15.0, y_lo, y_hi, 4.6, 5.5, ch=0.18, uv_rect=UV_Q1)
        m.add_chamfer_box(+13.2, +15.0, sy * 21.0 - 0.5, sy * 21.0 + 0.5, 4.6, 15.4, ch=0.18, uv_rect=UV_Q1)
        # Glowing radiator louver core face mapped directly to Q2 (cyan glowing slats!)
        m.add_chamfer_box(+13.0, +14.2, y_lo + 0.3, y_hi - 0.3, 5.4, 14.5, ch=0.10, uv_rect=UV_Q2)
        # 4 physical angled 3D cyan intake splitter slats protruding cleanly at the mouth
        for sz in (6.8, 8.8, 10.8, 12.8):
            m.add_box_oriented((14.4, sy * 17.9, sz), (2.4, 6.2, 0.42), ry=16.0, ch=0.08, uv_rect=UV_Q2)

        # Sidepod ground-effect bargeboard / aero flick ahead of intake (X = +15.2..+20.5, |Y| = 14.5..18.5)
        b_y0, b_y1 = sorted([sy * 17.5, sy * 18.4])
        m.add_chamfer_box(+15.0, +20.2, b_y0, b_y1, 3.6, 11.2, ch=0.14, uv_rect=UV_Q3)

    return m


def build_rear_wing():
    """Split carbon dual-tier rear wing + twin swan-neck pylons + slotted F1 endplates.
    Mounted strictly behind X <= -24 (at X = -32 .. -47) so cockpit overhead is 100% open.
    """
    m = KartMesh("aero")

    # Twin swan-neck pylons rising from rear spine (X = -30 .. -40, Y = +-7.5, Z = 16.5 .. 32.5)
    for sy in (+1.0, -1.0):
        py = sy * 7.5
        pylon_rings = [
            [(-30.0, py + 0.6, 17.0), (-30.0, py + 0.6, 22.0), (-30.0, py - 0.6, 22.0), (-30.0, py - 0.6, 17.0)],
            [(-35.0, py + 0.55, 25.0), (-35.0, py + 0.55, 29.5), (-35.0, py - 0.55, 29.5), (-35.0, py - 0.55, 25.0)],
            [(-39.5, py + 0.5, 31.0), (-39.5, py + 0.5, 34.0), (-39.5, py - 0.5, 34.0), (-39.5, py - 0.5, 31.0)],
        ]
        m.add_loop_loft(pylon_rings, uv_rect=UV_Q1, cap_start=True, cap_end=True)

    # Lower Beam Wing (spanning across rear above thrusters, X = -36..-43, Z = 22.0..23.5)
    m.add_airfoil_span([
        (-23.8, -36.5, -42.5, 22.2, 0.85, 0.35, -12.0),
        (-10.0, -35.8, -41.8, 22.0, 0.90, 0.40, -12.0),
        (0.0,   -35.5, -41.5, 22.2, 0.90, 0.40, -12.0),
        (+10.0, -35.8, -41.8, 22.0, 0.90, 0.40, -12.0),
        (+23.8, -36.5, -42.5, 22.2, 0.85, 0.35, -12.0),
    ], uv_rect=UV_Q4, cap_ends=False)

    # Split Carbon Upper Mainplanes (Left & Right wings separated by central V-slot around |Y| <= 3.2!)
    for sy in (+1.0, -1.0):
        ys = sorted([sy * 3.2, sy * 10.5, sy * 18.0, sy * 24.0])
        main_sp = []
        drs_sp = []
        for y in ys:
            ay = abs(y)
            t = (ay - 3.2) / 20.8
            # Dramatic swept gull-wing / split aero profile
            main_sp.append((y, -33.5 - 2.0 * t, -43.5 - 0.5 * t, 29.8 + 1.4 * t, 1.35, 0.65, -14.0))
            drs_sp.append((y, -41.8 - 0.8 * t, -47.2, 32.8 + 1.4 * t, 0.95, 0.45, -26.0))
        m.add_airfoil_span(main_sp, uv_rect=UV_Q4, cap_ends=True)
        m.add_airfoil_span(drs_sp, uv_rect=UV_Q1, cap_ends=True)

    # Twin Slotted Rear Wing Endplates (Y = +-24.2, X = -33.0 .. -47.2, Z = 20.5 .. 35.5)
    for sy in (+1.0, -1.0):
        y0, y1 = sorted([sy * 23.6, sy * 24.8])
        ep_rings = [
            [(-33.5, y1, 23.5), (-33.5, y1, 34.5), (-33.5, y0, 34.5), (-33.5, y0, 23.5)],
            [(-40.5, y1, 20.5), (-40.5, y1, 35.2), (-40.5, y0, 35.2), (-40.5, y0, 20.5)],
            [(-47.2, y1, 21.5), (-47.2, y1, 35.8), (-47.2, y0, 35.8), (-47.2, y0, 21.5)],
        ]
        m.add_loop_loft(ep_rings, uv_rect=UV_Q3, cap_start=True, cap_end=True)

    return m


def build_seat():
    """Contoured carbon-kevlar racing seat with electric-cyan side bolsters & headrest pad.
    Seat pan top sits at SEAT_POS = (-9.0, 0.0, 9.0).
    Strictly keeps the 22u-wide (|Y|<=11) x 28u-tall (Z=9.2..37.2) seated torso clearance box clear!
    """
    m = KartMesh("seat")

    # 1) Seat Pan (bottom Z=4.6, cushion top Z=9.0, X = -16.8 .. -1.2, |Y| <= 10.6)
    m.add_chamfer_box(-16.8, -1.2, -10.6, +10.6, 4.6, 8.2, ch=0.45, uv_rect=UV_Q1)
    # Quilted Alcantara top seat pad (top surface strictly at Z = 9.0!)
    m.add_chamfer_box(-16.2, -1.8, -10.0, +10.0, 8.0, 9.0, ch=0.22, uv_rect=UV_Q2)

    # 2) Reclined Carbon-Kevlar Backrest Shell + Cushion (strictly behind X = -16.6!)
    back_rings = []
    back_secs = [
        # (x_front, x_back, y_half, z)
        (-16.8, -19.0, 10.6, 8.2),
        (-18.2, -20.5, 10.4, 14.5),
        (-20.0, -22.2, 10.0, 20.5),
        (-21.8, -23.8, 8.6,  26.0),
    ]
    for xf, xb, yh, z in back_secs:
        back_rings.append([
            (xf, +yh, z),
            (xb, +yh * 0.92, z),
            (xb, -yh * 0.92, z),
            (xf, -yh, z),
        ])
    m.add_loop_loft(back_rings, uv_rect=UV_Q1, cap_start=True, cap_end=True)

    # Quilted backrest center pad (just in front of shell, still behind X <= -16.5!)
    pad_rings = [
        [(-16.6, +9.0, 9.2), (-17.1, +9.0, 9.2), (-17.1, -9.0, 9.2), (-16.6, -9.0, 9.2)],
        [(-17.9, +8.8, 15.0), (-18.5, +8.8, 15.0), (-18.5, -8.8, 15.0), (-17.9, -8.8, 15.0)],
        [(-19.7, +8.2, 21.0), (-20.3, +8.2, 21.0), (-20.3, -8.2, 21.0), (-19.7, -8.2, 21.0)],
        [(-21.2, +6.8, 25.0), (-21.9, +6.8, 25.0), (-21.9, -6.8, 25.0), (-21.2, -6.8, 25.0)],
    ]
    m.add_loop_loft(pad_rings, uv_rect=UV_Q2, cap_start=True, cap_end=True)

    # 3) Electric-Cyan Side Bolsters (thigh & shoulder bolsters, strictly |Y| >= 11.2!)
    for sy in (+1.0, -1.0):
        # Hip/thigh bolster
        y0, y1 = sorted([sy * 11.2, sy * 13.1])
        m.add_chamfer_box(-16.6, -2.5, y0, y1, 6.2, 13.8, ch=0.45, uv_rect=UV_Q3)
        # Rib/shoulder bolster curving back along backrest
        sh_rings = [
            [(-15.8, y1, 12.2), (-18.6, y1, 12.2), (-18.6, y0, 12.2), (-15.8, y0, 12.2)],
            [(-17.2, y1, 18.2), (-20.4, y1, 18.2), (-20.4, y0, 18.2), (-17.2, y0, 18.2)],
            [(-19.2, y1 - sy * 0.4, 24.2), (-22.6, y1 - sy * 0.4, 24.2), (-22.6, y0, 24.2), (-19.2, y0, 24.2)],
        ]
        if sy < 0:
            sh_rings = [list(reversed(r)) for r in sh_rings]
        m.add_loop_loft(sh_rings, uv_rect=UV_Q3, cap_start=True, cap_end=True)

    # 4) Electric-Cyan Headrest Pad (X = -23.8 .. -19.8, |Y| <= 4.4, Z = 25.5 .. 31.2)
    m.add_box_oriented((-21.6, 0.0, 28.4), (3.4, 8.8, 5.6), ry=-16.0, ch=0.55, uv_rect=UV_Q4)

    return m


def build_steering():
    """F1-style butterfly steering yoke with glowing telemetry LED bar on a sculpted column.
    Yoke center at STEER_POS = (13.0, 0.0, 24.0), tilted 22 deg toward driver.
    """
    m = KartMesh("steer")
    sx, sy, sz = STEER_POS

    # 1) Sculpted Steering Column (going forward & down into the nose cowl, X=+13..+22)
    m.add_tube([(sx + 0.8, 0.0, sz - 0.3), (sx + 8.8, 0.0, sz - 7.5)], [1.35, 1.55], segs=12, uv_rect=UV_Q4)
    # Quick-release anodized hub collar behind yoke
    m.add_tube([(sx + 0.2, 0.0, sz), (sx + 1.5, 0.0, sz - 1.1)], [1.75, 1.65], segs=12, uv_rect=UV_Q3)

    # 2) Build Butterfly Yoke in local yoke plane (face normal along -X, tilted +22 deg around Y)
    yoke = KartMesh("steer")
    # Center carbon faceplate
    yoke.add_chamfer_box(-0.55, +0.55, -4.6, +4.6, -2.8, +2.8, ch=0.22, uv_rect=UV_Q1)
    # Upper glowing OLED telemetry display & 15-LED shift-light bar (mapped to Q2!)
    yoke.add_chamfer_box(-0.75, +0.35, -3.4, +3.4, +1.0, +4.0, ch=0.14, uv_rect=UV_Q2)
    # Bottom yoke bridge bar
    yoke.add_chamfer_box(-0.45, +0.45, -4.2, +4.2, -3.6, -2.5, ch=0.15, uv_rect=UV_Q1)

    # Ergonomic Left & Right Butterfly Grips (cyan Alcantara, |Y| = 4.6 .. 6.9)
    for side in (+1.0, -1.0):
        # Upper horn + lower horn curving into sculpted vertical handle
        grip_pts = [
            (0.0, side * 3.8, +3.2),
            (-0.2, side * 5.8, +2.6),
            (-0.3, side * 6.5, +0.4),
            (-0.2, side * 6.2, -1.8),
            (0.0, side * 4.4, -3.0),
        ]
        yoke.add_tube(grip_pts, [0.58, 0.82, 0.92, 0.82, 0.56], segs=10, uv_rect=UV_Q3)
        # Carbon paddle shifter behind yoke
        yoke.add_chamfer_box(+0.85, +1.25, min(side * 3.4, side * 5.4), max(side * 3.4, side * 5.4), -1.1, +1.1, ch=0.08, uv_rect=UV_Q4)

    # Tilt yoke toward driver (+22 deg around Y rotates top -Z? Wait: rot_y(+22) pitches +X up toward +Z,
    # so top (+Z) tilts toward -X (driver), and normal (-X) tilts upward toward +Z (driver's eyes)! Let's verify:
    # rot_y((-1,0,0), +22) = (-cos22, 0, -sin22) -> wait: rot_y(p, deg): x'=x*cos-z*sin, z'=x*sin+z*cos!
    # With deg=-22: for top (0,0,+4), x' = -4*sin(-22) = +1.5 (+X forward!), and for (-1,0,0), z' = -1*sin(-22) = +0.37 (+Z up!).
    # Yes! deg = -22 tilts top slightly forward away from chest and face normal (-X) upward toward driver's eyes!
    m.append_part(yoke, offset=STEER_POS, ry=-22.0)

    return m


def build_thrusters():
    """Twin angled rear titanium turbo-jet thruster pods with variable-geometry iris petals & cyan plasma ring."""
    m = KartMesh("thruster")

    for sy in (+1.0, -1.0):
        pod = KartMesh("thruster")
        # Build along -X (exhaust pointing backward) in pod-local space
        # Outer heat-blued titanium shroud
        pod.add_lathe(
            (0.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
            [
                (0.0, 0.0, 0.0),
                (0.0, 3.8, 0.05),
                (1.2, 4.3, 0.14),
                (9.5, 4.5, 0.62),
                (12.8, 4.2, 0.82),
                (13.6, 3.6, 0.88),
                (13.6, 3.2, 0.92),  # inner nozzle wall lip
                (9.0, 2.7, 0.98),
                (9.0, 0.0, 1.00),
            ],
            segs=20, uv_rect=UV_Q1,
        )
        # Neon-amber hazard band ring near mid-shroud
        pod.add_lathe(
            (0.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
            [(5.4, 4.45, 0.05), (5.4, 4.72, 0.15), (6.8, 4.72, 0.85), (6.8, 4.45, 0.95)],
            segs=20, uv_rect=UV_Q4,
        )
        # 10 Variable-Geometry Iris Nozzle Petals extending from X=-12.8 to -16.8 along exhaust axis
        n_petals = 10
        for pi in range(n_petals):
            ang = 2.0 * math.pi * (pi / float(n_petals))
            petal = KartMesh("thruster")
            petal.add_chamfer_box(-4.0, +0.2, -0.95, +0.95, -0.18, +0.18, ch=0.05, uv_rect=UV_Q2)
            # Tilt petal inward slightly at rear tip (-10 deg) and place around ring R=3.55
            py = 3.55 * math.cos(ang)
            pz = 3.55 * math.sin(ang)
            # Rotate around local X by ang, after slight inward cant
            p_tilted = KartMesh("thruster")
            p_tilted.append_part(petal, offset=(0.0, 0.0, 3.55), ry=11.0)
            pod.append_part(p_tilted, offset=(-12.6, 0.0, 0.0), rx=math.degrees(ang) - 90.0)

        # Glowing cyan plasma afterburner ring & central stator cone inside nozzle
        pod.add_lathe(
            (-12.2, 0.0, 0.0), (-1.0, 0.0, 0.0),
            [
                (0.0, 0.0, 0.00, 3.1),
                (1.4, 1.2, 0.35, 3.1),
                (0.3, 2.2, 0.70, 3.1),
                (0.3, 3.1, 1.00, 3.1),
            ],
            segs=16, uv_mode="polar", uv_rect=UV_Q3,
        )

        # Mount at rear cowling: X=-29.0, Y=+-8.2, Z=12.6, angled slightly outward (+-5 deg yaw) and up (+4 deg pitch)
        m.append_part(pod, offset=(-29.2, sy * 8.1, 12.6), ry=-4.0, rz=sy * 5.0)

    return m


def build_turbine_wheel(side_sign, radius, half_width):
    """Builds one wide low-profile racing slick + cyan-rimmed alloy barrel + 5 twisted 3D turbine spokes
    + drilled carbon brake rotor + center-lock anodized nut, centered at (0,0,0).
    """
    m = KartMesh("wheel")
    axis = (0.0, float(side_sign), 0.0)
    up_h = (0.0, 0.0, 1.0)

    r_rim = radius * 0.64  # low-profile racing slick (large alloy rim!)
    r_sh = radius * 0.965
    hw = half_width

    # 1) Inner Alloy Barrel + Inner Tire Sidewall
    m.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-hw * 0.75, 0.0, 0.0, r_rim),
            (-hw * 0.75, r_rim * 0.35, 0.35, r_rim),
            (-hw * 0.60, r_rim * 0.88, 0.88, r_rim),
            (-hw * 0.88, r_rim, 1.0, r_rim),
        ],
        segs=32, uv_mode="polar", uv_rect=UV_Q4_D, up_hint=up_h,
    )
    m.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (-hw * 0.88, r_rim, 0.56, radius),
            (-hw * 1.00, r_rim + (radius - r_rim) * 0.45, 0.76, radius),
            (-hw * 0.96, r_sh, 0.95, radius),
        ],
        segs=32, uv_mode="polar", uv_rect=UV_Q2, up_hint=up_h,
    )

    # 2) Wide Low-Profile Racing Slick Tread Crown (32 segments for ultra-smooth Z=0 ground roll)
    X_w, Y_w, Z_w = basis_from_axis(axis, up_hint=up_h)
    tread_prof = [
        (-hw * 0.96, r_sh, 0.02),
        (-hw * 0.86, radius, 0.10),
        (-hw * 0.52, radius, 0.28),
        (-hw * 0.44, radius * 0.988, 0.34),  # subtle slick groove
        (-hw * 0.36, radius, 0.40),
        (+hw * 0.36, radius, 0.60),
        (+hw * 0.44, radius * 0.988, 0.66),  # subtle slick groove
        (+hw * 0.52, radius, 0.72),
        (+hw * 0.86, radius, 0.90),
        (+hw * 0.96, r_sh, 0.98),
    ]
    segs = 32
    cols = segs + 1
    b_tr = len(m.verts)
    tr_pts = []
    for sp, rp, ut in tread_prof:
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(segs))
            cth, sth = math.cos(th), math.sin(th)
            pos = vadd(vmul(X_w, sp), vadd(vmul(Y_w, rp * cth), vmul(Z_w, rp * sth)))
            tr_pts.append(pos)
            m.st.append((0.02 + 0.46 * ut, 0.02 + 0.46 * (j / float(segs))))
    tr_acc = [[0.0, 0.0, 0.0] for _ in tr_pts]
    tr_tris = []
    for i in range(len(tread_prof) - 1):
        for j in range(segs):
            a = i * cols + j
            b = a + 1
            c = a + cols
            d = c + 1
            for t_tri in ((a, b, c), (b, d, c)):
                fn = vcross(vsub(tr_pts[t_tri[1]], tr_pts[t_tri[0]]), vsub(tr_pts[t_tri[2]], tr_pts[t_tri[0]]))
                tr_tris.append(t_tri)
                for vi in t_tri:
                    tr_acc[vi][0] += fn[0]
                    tr_acc[vi][1] += fn[1]
                    tr_acc[vi][2] += fn[2]
    for i in range(len(tread_prof)):
        i0, i1 = i * cols, i * cols + segs
        sn = vadd(tr_acc[i0], tr_acc[i1])
        tr_acc[i0], tr_acc[i1] = list(sn), list(sn)
    m.verts += tr_pts
    m.norms += [vnorm(n) for n in tr_acc]
    m.tris += [(a + b_tr, b + b_tr, c + b_tr) for (a, b, c) in tr_tris]

    # 3) Outer Sidewall + Cyan Rim Lip
    m.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+hw * 0.96, r_sh, 0.95, radius),
            (+hw * 1.00, r_rim + (radius - r_rim) * 0.45, 0.76, radius),
            (+hw * 0.90, r_rim, 0.56, radius),
            (+hw * 0.94, r_rim * 0.92, 0.52, radius),
        ],
        segs=32, uv_mode="polar", uv_rect=UV_Q2, up_hint=up_h,
    )

    # 4) Recessed Drilled Carbon Brake Rotor + Neon-Amber Caliper inside barrel
    m.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+hw * 0.05, 0.0, 0.0, r_rim * 0.78),
            (+hw * 0.05, r_rim * 0.78, 1.0, r_rim * 0.78),
            (+hw * 0.05, r_rim * 0.78, 1.0, r_rim * 0.78),
            (-hw * 0.15, r_rim * 0.78, 0.95, r_rim * 0.78),
            (-hw * 0.15, 0.0, 0.0, r_rim * 0.78),
        ],
        segs=20, uv_mode="polar", uv_rect=UV_Q4_A, up_hint=up_h,
    )
    # Caliper block on rear/top quadrant
    cal_x = -r_rim * 0.58
    cal_z = +r_rim * 0.35
    m.add_box_oriented((cal_x, side_sign * hw * 0.10, cal_z), (r_rim * 0.42, hw * 0.48, r_rim * 0.56), ry=-28.0, ch=0.18, uv_rect=UV_Q4_C)

    # 5) 5 Twisted 3D Turbine Alloy Spokes radiating from hub to rim lip
    for k in range(5):
        ang0 = math.radians(k * 72.0)
        # Swept curved turbine blade (4 stations from hub r=1.4 to outer rim r=r_rim*0.92)
        spoke_rings = []
        for si in range(4):
            t = si / 3.0
            rr = 1.4 + t * (r_rim * 0.93 - 1.4)
            ang = ang0 + side_sign * t * 0.34  # turbine twist sweep
            y_c = side_sign * hw * (0.44 + 0.44 * t)
            w_rad = 1.05 - 0.30 * t
            # Tangent & radial directions in XZ plane
            cx, cz = rr * math.cos(ang), rr * math.sin(ang)
            tx, tz = -math.sin(ang), math.cos(ang)
            # Blade canted 24 deg for turbine aero look
            yo = side_sign * 0.48
            ring = [
                (cx - tx * w_rad, y_c - yo * 0.4, cz - tz * w_rad),
                (cx + tx * w_rad, y_c + yo * 0.8, cz + tz * w_rad),
                (cx + tx * w_rad, y_c + yo * 0.1, cz + tz * w_rad),
                (cx - tx * w_rad, y_c - yo * 1.1, cz - tz * w_rad),
            ]
            if side_sign < 0:
                ring = list(reversed(ring))
            spoke_rings.append(ring)
        m.add_loop_loft(spoke_rings, uv_rect=UV_Q3, cap_start=True, cap_end=True)

    # 6) Center-Lock Anodized Cyan Hex Locknut & Hub Boss
    m.add_lathe(
        (0.0, 0.0, 0.0), axis,
        [
            (+hw * 0.10, 0.0, 0.0),
            (+hw * 0.10, 2.2, 0.1),
            (+hw * 0.58, 2.2, 0.45),
            (+hw * 0.58, 1.45, 0.52),
            (+hw * 0.58, 1.45, 0.52),
            (+hw * 0.92, 1.25, 0.88),
            (+hw * 0.92, 0.0, 1.00),
        ],
        segs=6, uv_rect=UV_Q4_B, up_hint=up_h,
    )

    return m


def build_flame_surface(is_core=False):
    """Builds the topological template for `flame_outer` or `flame_core` spanning BOTH rear thrusters.
    Vertices are positioned cleanly in local thruster-flame space (t=0 at nozzle -> t=1 at tail tip)
    and morphed per-frame by `animate_flame()` so idle/fast collapse inside nozzles and super erupts!
    """
    m = KartMesh("flame")
    uv_rect = (0.53, 0.03, 0.97, 0.97) if is_core else (0.03, 0.03, 0.47, 0.97)
    n_seg = 10
    n_rings = 7 if not is_core else 6

    # We tag each vertex with (thruster_idx, ring_t, angle, base_r) in metadata lists returned alongside m
    meta = []
    for ti in (0, 1):
        # 1) Sculpted longitudinal plasma plume sleeve
        cols = n_seg + 1
        base = len(m.verts)
        for ri in range(n_rings):
            t = ri / float(n_rings - 1)
            # Tapered nozzle-to-tip envelope with shock-diamond pinch
            pinch = 1.0 - 0.22 * math.sin(t * math.pi * 3.0) ** 2
            base_r = (1.6 if is_core else 2.9) * (1.0 - 0.85 * (t ** 1.2)) * pinch
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

        # 2) 3 Shock-Diamond Mach Discs (crossed fins/cones) for crisp 3D depth from every angle
        for di in range(3):
            dt = 0.18 + di * 0.24
            r_disc = (1.35 if is_core else 2.55) * (1.0 - 0.55 * dt)
            b_d = len(m.verts)
            # Center apex + 8 perimeter vertices
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


def _animate_explosion_part(part_in_world, vel, omega, radius_est, dt_idx):
    """Simulates 3D ballistic trajectory + tumbling + elastic ground bounce (z >= 0.5) at explode frame dt_idx (0..19)."""
    t = dt_idx * 0.055  # 0.0 .. 1.045s
    g = 240.0
    c0 = _part_centroid(part_in_world)

    # Integrate 1D vertical trajectory with exact analytical ground bounce
    z0 = c0[2]
    vz = vel[2]
    z_cur = z0
    t_rem = t
    floor_z = max(radius_est, 1.5) + 0.5
    bounces = 0
    while t_rem > 1e-5 and bounces < 3:
        # Time to hit floor_z: z_cur + vz*tb - 0.5*g*tb^2 = floor_z
        a_q = -0.5 * g
        b_q = vz
        c_q = z_cur - floor_z
        disc = b_q * b_q - 4.0 * a_q * c_q
        if disc >= 0.0:
            tb = (-b_q - math.sqrt(disc)) / (2.0 * a_q)  # downward crossing root
            if 1e-4 < tb <= t_rem:
                z_cur = floor_z
                vz = -(vz - g * tb) * 0.56  # elastic bounce damping
                t_rem -= tb
                bounces += 1
                continue
        z_cur = z_cur + vz * t_rem - 0.5 * g * t_rem * t_rem
        break

    dx = vel[0] * t * (0.85 ** bounces)
    dy = vel[1] * t * (0.85 ** bounces)
    dz = z_cur - z0

    rx = omega[0] * t
    ry = omega[1] * t
    rz = omega[2] * t

    vv, nn = _xform_part(part_in_world, offset=(dx, dy, dz), rx=rx, ry=ry, rz=rz, pivot=c0)
    # Strict safety clamp so no rotated corner ever dips below z = 0.5
    min_z = min(p[2] for p in vv)
    if min_z < 0.5:
        lift = 0.5 - min_z
        vv = [(p[0], p[1], p[2] + lift) for p in vv]
    return vv, nn


def _animate_flame_frame(meta, fi, is_core, chassis_ry, chassis_dz):
    """Generates (verts, norms) for flame_outer / flame_core at frame fi (0..63)."""
    vv, nn = [], []
    tips = [
        ((-44.6, +9.1, 13.5), (-0.994, +0.087, 0.070)),
        ((-44.6, -9.1, 13.5), (-0.994, -0.087, 0.070)),
    ]

    # Mode determination
    if fi < 28:
        # Idle & Fast: collapsed to tiny <0.02u degenerate point inside opaque rear spine
        for kind, ti, t, th, br in meta:
            vv.append((-36.0 + 0.003 * t, 0.002 * math.cos(th), 13.0 + 0.002 * math.sin(th)))
            nn.append((-1.0, 0.0, 0.0))
        return vv, nn

    if 28 <= fi <= 43:
        # Super Speed: twin roaring cyan/white-hot shock-diamond plasma plumes (26..35u long!)
        sf = fi - 28
        ph = 2.0 * math.pi * (sf / 16.0)
        length_base = 33.5 if not is_core else 24.5
        for kind, ti, t, th, br in meta:
            tip, dir_v = tips[ti]
            # Transform tip & direction with chassis squat around rear axle
            p_tip = vsub(tip, (REAR_WHEEL_X, 0.0, REAR_WHEEL_R))
            p_tip = rot_y(p_tip, chassis_ry)
            tip_w = vadd(p_tip, (REAR_WHEEL_X, 0.0, REAR_WHEEL_R + chassis_dz))
            d_w = vnorm(rot_y(dir_v, chassis_ry))
            _, Y_f, Z_f = basis_from_axis(d_w)

            # Flickering shock-diamond pulse & spiral wave
            flicker = 1.0 + 0.14 * math.sin(ph * 3.0 + ti * 1.7 + t * 5.0)
            L = length_base * (1.0 + 0.09 * math.sin(ph * 2.0 + ti * 2.1))
            r_wave = br * flicker * (1.0 + 0.15 * math.sin(ph * 4.0 - t * 9.0 + th * 2.0))
            dist = t * L
            pos = vadd(tip_w, vadd(vmul(d_w, dist), vadd(vmul(Y_f, r_wave * math.cos(th)), vmul(Z_f, r_wave * math.sin(th)))))
            nrm = vnorm(vadd(vmul(Y_f, math.cos(th)), vmul(Z_f, math.sin(th)))) if br > 1e-4 else d_w
            vv.append(pos)
            nn.append(nrm)
        return vv, nn

    # Explosion frames 44..63
    ef = fi - 44
    if ef <= 5:
        # Flash big at frames 44..47 (ef 0..3), shrink away by frame 50 (ef=6)
        flash_env = [0.65, 1.35, 1.55, 1.25, 0.65, 0.20][ef]
        scale_r = 4.2 * flash_env * (0.75 if is_core else 1.0)
        scale_l = 22.0 * flash_env
        for kind, ti, t, th, br in meta:
            ang_lat = th + ti * 1.9 + ef * 0.4
            ang_elev = (t - 0.35) * 1.8
            r_cur = max(0.2, br * scale_r + t * scale_l * 0.45)
            cx = -15.0 + (-1.0 if ti == 0 else -0.5) * t * scale_l * 0.6 + r_cur * math.cos(ang_lat) * 0.7
            cy = (6.0 if ti == 0 else -6.0) + r_cur * math.sin(ang_lat)
            cz = max(0.8, 13.0 + r_cur * math.sin(ang_elev) + ef * 2.2)
            vv.append((cx, cy, cz))
            nn.append(vnorm((math.cos(ang_lat), math.sin(ang_lat), 0.3)))
    else:
        # Collapsed cleanly at ground core
        for _ in meta:
            vv.append((0.0, 0.0, 2.0))
            nn.append((0.0, 0.0, 1.0))
    return vv, nn


# ---------------------------------------------------------------------------
# Master Model Assembly & Export
# ---------------------------------------------------------------------------
def build_gokart_2(progs_dir=PROGS, meta_dir=OUT_DIR):
    print("1. Generating high-res procedural PNG textures (progs/gk2_*.png)...", flush=True)
    tex_map = build_all_textures(progs_dir)

    print("2. Building 3D procedural surfaces for Cyber-Nitro Aero GT...", flush=True)
    p_body = build_body_shell()
    p_fwing = build_front_wing()
    p_pods = build_sidepods()
    p_rwing = build_rear_wing()
    p_seat = build_seat()
    p_steer = build_steering()
    p_thrust = build_thrusters()

    w_fl_local = build_turbine_wheel(+1, FRONT_WHEEL_R, FRONT_WHEEL_HW)
    w_fr_local = build_turbine_wheel(-1, FRONT_WHEEL_R, FRONT_WHEEL_HW)
    w_rl_local = build_turbine_wheel(+1, REAR_WHEEL_R, REAR_WHEEL_HW)
    w_rr_local = build_turbine_wheel(-1, REAR_WHEEL_R, REAR_WHEEL_HW)

    p_flame_out, meta_flame_out = build_flame_surface(is_core=False)
    p_flame_core, meta_flame_core = build_flame_surface(is_core=True)

    # Verify player-fit torso clearance box in Frame 0 static pose!
    # Seated torso box: 22u-wide (|Y| <= 11.0) x 28u-tall (Z in [9.2, 37.2]) centered above seat_pos (-9, 0, 9.0)
    # Using X in [-16.0, +4.0] (covering torso + chest lean toward wheel!)
    static_parts = [
        ("body_shell", p_body),
        ("front_wing", p_fwing),
        ("sidepods", p_pods),
        ("rear_wing", p_rwing),
        ("seat", p_seat),
        ("steering", p_steer),
        ("thrusters", p_thrust),
    ]
    for sname, sp in static_parts:
        for vx, vy, vz in sp.verts:
            if -16.0 <= vx <= +4.0 and -11.0 <= vy <= +11.0 and 9.2 <= vz <= 37.2:
                raise AssertionError(f"Player-fit torso clearance violation in {sname} at ({vx:.2f}, {vy:.2f}, {vz:.2f})")
    print("   [OK] Player-fit torso clearance box (22u x 28u above seat_pos) has ZERO clipping.", flush=True)

    # Wheel world offsets
    wheel_defs = [
        ("wheel_fl", w_fl_local, (FRONT_WHEEL_X, +FRONT_WHEEL_Y, FRONT_WHEEL_R), FRONT_WHEEL_R, (+85.0, +72.0, +95.0), (180.0, 420.0, 260.0)),
        ("wheel_fr", w_fr_local, (FRONT_WHEEL_X, -FRONT_WHEEL_Y, FRONT_WHEEL_R), FRONT_WHEEL_R, (+92.0, -78.0, +88.0), (-210.0, 390.0, -240.0)),
        ("wheel_rl", w_rl_local, (REAR_WHEEL_X, +REAR_WHEEL_Y, REAR_WHEEL_R), REAR_WHEEL_R, (-88.0, +82.0, +82.0), (160.0, -380.0, 290.0)),
        ("wheel_rr", w_rr_local, (REAR_WHEEL_X, -REAR_WHEEL_Y, REAR_WHEEL_R), REAR_WHEEL_R, (-82.0, -86.0, +90.0), (-195.0, -410.0, -270.0)),
    ]

    # Explosion ballistic configs for chassis parts: (vel, omega, radius_est)
    chassis_defs = [
        ("body_shell", "progs/gk2_body", p_body, (-8.0, +12.0, +58.0), (45.0, -65.0, 35.0), 8.5),
        ("front_wing", "progs/gk2_aero", p_fwing, (+95.0, -18.0, +86.0), (220.0, 310.0, -140.0), 5.0),
        ("sidepods", "progs/gk2_aero", p_pods, (+15.0, +52.0, +74.0), (340.0, 120.0, 210.0), 6.5),
        ("rear_wing", "progs/gk2_aero", p_rwing, (-96.0, +24.0, +112.0), (-190.0, -360.0, 180.0), 7.0),
        ("seat", "progs/gk2_seat", p_seat, (-12.0, -22.0, +126.0), (140.0, -280.0, 220.0), 6.0),
        ("steering", "progs/gk2_steer", p_steer, (+48.0, +36.0, +134.0), (380.0, 240.0, -310.0), 4.0),
        ("thrusters", "progs/gk2_thruster", p_thrust, (-105.0, -28.0, +88.0), (-150.0, 290.0, -260.0), 5.0),
    ]

    surf_frames = {name: [] for name, *_ in chassis_defs}
    for wn, *_ in wheel_defs:
        surf_frames[wn] = []
    surf_frames["flame_outer"] = []
    surf_frames["flame_core"] = []

    rear_pivot = (REAR_WHEEL_X, 0.0, REAR_WHEEL_R)

    print("3. Computing 64 animation frames (idle, fast, super+flames, explosion)...", flush=True)
    for fi in range(64):
        if fi < 12:
            # Idle: subtle high-tech turbine hum
            ph = 2.0 * math.pi * (fi / 12.0)
            dz = 0.14 * math.sin(ph * 2.0)
            ry = 0.18 * math.sin(ph)
            w_spin_f = 0.0
            w_spin_r = 0.0
            for sname, _, part, *_ in chassis_defs:
                surf_frames[sname].append(_xform_part(part, offset=(0.0, 0.0, dz), ry=ry, pivot=rear_pivot))
            for wn, wpart, woff, *_ in wheel_defs:
                surf_frames[wn].append(_xform_part(wpart, offset=woff))
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, ry, dz))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, ry, dz))

        elif fi < 28:
            # Fast: 2*pi forward wheel spin across 16 frames + subtle aero chatter
            sf = fi - 12
            ph = 2.0 * math.pi * (sf / 16.0)
            spin_deg = -360.0 * (sf / 16.0)  # negative ry rolls top toward +X
            dz = 0.22 * math.sin(ph * 2.0)
            ry = 0.35 * math.sin(ph * 2.0)
            rx = 0.30 * math.sin(ph)
            for sname, _, part, *_ in chassis_defs:
                surf_frames[sname].append(_xform_part(part, offset=(0.0, 0.0, dz), rx=rx, ry=ry, pivot=rear_pivot))
            for wn, wpart, woff, *_ in wheel_defs:
                surf_frames[wn].append(_xform_part(wpart, offset=woff, ry=spin_deg))
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, ry, dz))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, ry, dz))

        elif fi < 44:
            # Super Speed + Flames: 4*pi wheel spin (2x faster), ~2 deg rear squat, roaring twin flames!
            sf = fi - 28
            ph = 2.0 * math.pi * (sf / 16.0)
            spin_deg = -720.0 * (sf / 16.0)
            dz = 0.25 * math.sin(ph * 3.0)
            # Squat back ~2 deg: +X nose lifts, tail squats slightly around rear axle
            ry = +2.0 + 0.35 * math.sin(ph * 3.0)
            rx = 0.40 * math.sin(ph * 2.0)
            for sname, _, part, *_ in chassis_defs:
                surf_frames[sname].append(_xform_part(part, offset=(0.0, 0.0, dz), rx=rx, ry=ry, pivot=rear_pivot))
            for wn, wpart, woff, *_ in wheel_defs:
                surf_frames[wn].append(_xform_part(wpart, offset=woff, ry=spin_deg))
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, ry, dz))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, ry, dz))

        else:
            # Catastrophic Explosion: every piece flies along unique 3D ballistic trajectory + tumble + bounce!
            ef = fi - 44
            for sname, _, part, vel, omega, rad_est in chassis_defs:
                surf_frames[sname].append(_animate_explosion_part(part, vel, omega, rad_est, ef))
            for wn, wpart, woff, rad_w, vel, omega in wheel_defs:
                w_world = KartMesh("wheel")
                w_world.append_part(wpart, offset=woff)
                surf_frames[wn].append(_animate_explosion_part(w_world, vel, omega, rad_w, ef))
            surf_frames["flame_outer"].append(_animate_flame_frame(meta_flame_out, fi, False, 0.0, 0.0))
            surf_frames["flame_core"].append(_animate_flame_frame(meta_flame_core, fi, True, 0.0, 0.0))

    # Assemble MD3 surface dicts
    surfaces = []
    for sname, shader, part, *_ in chassis_defs:
        surfaces.append(dict(
            name=sname, shader=shader, tris=list(part.tris), st=list(part.st), frames=surf_frames[sname]
        ))
    for wn, wpart, *_ in wheel_defs:
        surfaces.append(dict(
            name=wn, shader="progs/gk2_wheel", tris=list(wpart.tris), st=list(wpart.st), frames=surf_frames[wn]
        ))
    surfaces.append(dict(
        name="flame_outer", shader="progs/gk2_flame", tris=list(p_flame_out.tris), st=list(p_flame_out.st), frames=surf_frames["flame_outer"]
    ))
    surfaces.append(dict(
        name="flame_core", shader="progs/gk2_flame", tris=list(p_flame_core.tris), st=list(p_flame_core.st), frames=surf_frames["flame_core"]
    ))

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

    md3_path = os.path.join(progs_dir, "gokart_2.md3")
    md3lib.write(md3_path, dict(name="progs/gokart_2.md3", surfaces=surfaces, nframes=64, frame_names=FRAME_NAMES))

    skin_path = md3_path + "_0.skin"
    with open(skin_path, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(f"{s['name']},{s['shader']}" for s in surfaces) + "\n")

    # Round-trip md3lib.read() verification
    with open(md3_path, "rb") as f:
        ident, ver = struct.unpack("<4si", f.read(8))
    assert ident == b"IDP3" and ver == 15
    rt = md3lib.read(md3_path)
    assert rt["nframes"] == 64 and len(rt["surfaces"]) == len(surfaces)

    # Verify ground contact Z=0 for frames 0..43
    for fi in range(44):
        pts_f = np.vstack([np.asarray(s["frames"][fi][0], dtype=np.float32) for s in rt["surfaces"]])
        z_min = float(pts_f[:, 2].min())
        assert abs(z_min) < 0.15, f"Frame {fi} ground contact z_min={z_min:.3f} (expected 0.0)"

    # Verify flame collapse in 0..27 and extension in 28..43
    for s in rt["surfaces"]:
        if s["name"] in ("flame_outer", "flame_core"):
            for fi in range(28):
                pts = np.asarray(s["frames"][fi][0], dtype=np.float32)
                span = float(np.linalg.norm(pts.max(axis=0) - pts.min(axis=0)))
                assert span < 1.0, f"{s['name']} not collapsed at frame {fi} (span={span:.2f})"
            for fi in range(28, 44):
                pts = np.asarray(s["frames"][fi][0], dtype=np.float32)
                x_span = float(pts.max(axis=0)[0] - pts.min(axis=0)[0])
                assert x_span > 18.0, f"{s['name']} too short at super frame {fi} (x_span={x_span:.2f})"

    # Verify explosion separation (frame 44 vs frame 63) & ground bounce z >= 0.45 (accounting for 1/64 quantization)
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
        meta_path = os.path.join(meta_dir, "gokart_2_meta.json")
        meta_doc = {
            "id": "kart2",
            "name": "Cyber-Nitro Aero GT",
            "tagline": "Formula-E Monocoque, Cyan Slats & Twin Turbo-Jet Afterburners",
            "palette": ["#26292e", "#5c626b", "#962424", "#b8bcc4"],
            "description": (
                "Sleek futuristic Formula-E cyber racer featuring a sculpted midnight-carbon wedge-nose "
                "monocoque with Quake 'Q' nose decal, low-drag F1 front splitter wing, glowing cyan "
                "radiator intake slats, carbon-kevlar racing seat, butterfly telemetry yoke, 5-spoke "
                "turbine alloy slicks, split carbon rear wing, and twin angled titanium turbo-jet thrusters."
            ),
            "highlights": [
                ["Aero Body", "Midnight-carbon wedge monocoque, F1 splitter, cyan intake slats & split rear wing"],
                ["Thrusters", "Twin angled titanium iris-nozzle turbo jets w/ shock-diamond cyan plasma plumes"],
                ["Player Fit", "26u open cockpit, seat (-9, 0, 9), yoke (13, 0, 24), clear footwell & open overhead"],
            ],
            "seat_pos": {"x": SEAT_POS[0], "y": SEAT_POS[1], "z": SEAT_POS[2]},
            "steer_pos": {"x": STEER_POS[0], "y": STEER_POS[1], "z": STEER_POS[2]},
            "exhaust_tips": EXHAUST_TIPS,
            "textures": {
                "progs/gk2_body": "progs/gk2_body.png",
                "progs/gk2_aero": "progs/gk2_aero.png",
                "progs/gk2_seat": "progs/gk2_seat.png",
                "progs/gk2_steer": "progs/gk2_steer.png",
                "progs/gk2_thruster": "progs/gk2_thruster.png",
                "progs/gk2_wheel": "progs/gk2_wheel.png",
                "progs/gk2_flame": "progs/gk2_flame.png",
            },
            "materials": {
                "progs/gk2_body": {"metallic": 0.55, "roughness": 0.24, "spec": 0.95},
                "progs/gk2_aero": {"metallic": 0.45, "roughness": 0.28, "spec": 0.85},
                "progs/gk2_seat": {"metallic": 0.12, "roughness": 0.58, "spec": 0.35},
                "progs/gk2_steer": {"metallic": 0.42, "roughness": 0.32, "spec": 0.75},
                "progs/gk2_thruster": {"metallic": 0.88, "roughness": 0.18, "spec": 1.35},
                "progs/gk2_wheel": {"metallic": 0.35, "roughness": 0.42, "spec": 0.65},
                "progs/gk2_flame": {"metallic": 0.0, "roughness": 1.0, "spec": 0.0, "unlit": True, "additive": True},
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
    p = argparse.ArgumentParser(description="Build Go-Kart #2 MD3, skin, and textures.")
    p.add_argument("--out-dir", default=None, help="Output directory for MD3, skin, and PNGs")
    p.add_argument("--meta-dir", default=None, help="Optional directory for gokart_2_meta.json")
    args = p.parse_args()
    progs_dir = args.out_dir if args.out_dir is not None else PROGS
    meta_dir = args.meta_dir if args.meta_dir is not None else (OUT_DIR if args.out_dir is None else None)
    build_gokart_2(progs_dir=progs_dir, meta_dir=meta_dir)
