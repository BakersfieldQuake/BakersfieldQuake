"""Procedural 3D MD3 + high-res texture builder for Go-Kart #3:
  "Baja Dune Scrambler" (rugged off-road / industrial Bakersfield desert buggy-kart).

Outputs (ONLY Go-Kart #3 owned files):
  - progs/gk3_*.png                         (9 procedural 512/1024 textures)
  - progs/gokart_3.md3                      (64-frame multi-surface MD3)
  - progs/gokart_3.md3_0.skin               (surface -> shader skin mapping)
  - source/mm_tools/out/gokart_3_meta.json  (metadata & material table)

Coordinate contract (Quake / DarkPlaces):
  +X = forward, +Y = left, +Z = up, ground = Z=0.
  Overall length X in [-48, +50], track width Y in [-35, +35].
"""
import argparse
import json
import math
import os
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
# Shaders & Textures
# ---------------------------------------------------------------------------
SHADER_PREFIX = "progs/gk3_"
SURF_SHADERS = {
    "chassis_cage":  "progs/gk3_chassis",
    "skid_lights":   "progs/gk3_skid",
    "suspension":    "progs/gk3_susp",
    "seat":          "progs/gk3_seat",
    "steering":      "progs/gk3_steer",
    "engine_vtwin":  "progs/gk3_engine",
    "exhaust_dual":  "progs/gk3_exhaust",
    "wheel_fl":      "progs/gk3_wheel",
    "wheel_fr":      "progs/gk3_wheel",
    "wheel_rl":      "progs/gk3_wheel",
    "wheel_rr":      "progs/gk3_wheel",
    "flame_outer":   "progs/gk3_flame",
    "flame_core":    "progs/gk3_flame",
}

MATERIALS = {
    "progs/gk3_chassis": {"metallic": 0.45, "roughness": 0.35, "spec": 0.65},
    "progs/gk3_skid":    {"metallic": 0.72, "roughness": 0.28, "spec": 0.80},
    "progs/gk3_susp":    {"metallic": 0.55, "roughness": 0.28, "spec": 0.78},
    "progs/gk3_seat":    {"metallic": 0.05, "roughness": 0.80, "spec": 0.18},
    "progs/gk3_steer":   {"metallic": 0.35, "roughness": 0.48, "spec": 0.45},
    "progs/gk3_engine":  {"metallic": 0.78, "roughness": 0.26, "spec": 0.85},
    "progs/gk3_exhaust": {"metallic": 0.88, "roughness": 0.20, "spec": 0.92},
    "progs/gk3_wheel":   {"metallic": 0.22, "roughness": 0.68, "spec": 0.32},
    "progs/gk3_flame":   {"metallic": 0.00, "roughness": 1.00, "spec": 0.00, "unlit": True, "additive": True},
}

# UV atlas rects (u0, v0, u1, v1) with v=0 at top of PNG
UV_CHASSIS_LIME    = (0.02, 0.02, 0.48, 0.48)
UV_CHASSIS_GUN     = (0.52, 0.02, 0.98, 0.48)
UV_CHASSIS_FLOOR   = (0.02, 0.52, 0.48, 0.98)
UV_CHASSIS_DECAL   = (0.52, 0.52, 0.98, 0.98)

UV_SKID_PLATE      = (0.02, 0.02, 0.48, 0.48)
UV_SKID_BUMPER     = (0.52, 0.02, 0.98, 0.48)
UV_SKID_LAMP       = (0.02, 0.52, 0.48, 0.98)
UV_SKID_QBADGE     = (0.52, 0.52, 0.98, 0.98)

UV_SUSP_ORANGE     = (0.02, 0.02, 0.48, 0.48)
UV_SUSP_GUN        = (0.52, 0.02, 0.98, 0.48)
UV_SUSP_CHROME     = (0.02, 0.52, 0.48, 0.98)
UV_SUSP_HAZARD     = (0.52, 0.52, 0.98, 0.98)

UV_SEAT_TAN        = (0.02, 0.02, 0.48, 0.48)
UV_SEAT_CHARCOAL   = (0.52, 0.02, 0.98, 0.48)
UV_SEAT_HARNESS    = (0.02, 0.52, 0.48, 0.98)
UV_SEAT_BACK       = (0.52, 0.52, 0.98, 0.98)

UV_STEER_GRIP      = (0.02, 0.02, 0.48, 0.48)
UV_STEER_STRIPE    = (0.52, 0.02, 0.98, 0.48)
UV_STEER_SPOKE     = (0.02, 0.52, 0.48, 0.98)
UV_STEER_CAP       = (0.52, 0.52, 0.98, 0.98)

UV_ENG_BLOCK       = (0.02, 0.02, 0.48, 0.48)
UV_ENG_FILTER      = (0.52, 0.02, 0.98, 0.48)
UV_ENG_VALVE       = (0.02, 0.52, 0.48, 0.98)
UV_ENG_ACCENT      = (0.52, 0.52, 0.98, 0.98)

UV_EXH_WRAP        = (0.02, 0.02, 0.48, 0.98)
UV_EXH_CHROME      = (0.52, 0.02, 0.98, 0.48)
UV_EXH_BORE        = (0.52, 0.52, 0.98, 0.98)

UV_WHL_TREAD       = (0.02, 0.02, 0.48, 0.48)
UV_WHL_SIDE        = (0.52, 0.02, 0.98, 0.48)
UV_WHL_RIM         = (0.02, 0.52, 0.48, 0.98)
UV_WHL_HUB         = (0.52, 0.52, 0.98, 0.98)

UV_FLAME_OUTER     = (0.02, 0.02, 0.48, 0.98)
UV_FLAME_CORE      = (0.52, 0.02, 0.98, 0.98)


# ---------------------------------------------------------------------------
# Procedural Texture Synthesis (PIL + NumPy)
# ---------------------------------------------------------------------------
def _fbm(h, w, seed=101, octaves=(4, 8, 16, 32, 64)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    tw = 0.0
    for i, freq in enumerate(octaves):
        amp = 0.5 ** i
        gh = max(2, h // freq)
        gw = max(2, w // freq)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        im_g = Image.fromarray(g, mode="F").resize((w, h), Image.Resampling.BICUBIC)
        acc += np.asarray(im_g, dtype=np.float32) * amp
        tw += amp
    return acc / max(tw, 1e-6)


def _font(size, bold=True):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _save_png(arr_f, path, mode="RGB"):
    u8 = np.clip(np.round(arr_f), 0, 255).astype(np.uint8)
    Image.fromarray(u8, mode=mode).save(path, "PNG", optimize=True)


def _draw_quake_q(draw, cx, cy, r, fill_col, rim_col, shadow_col):
    """Draws a crisp recognizable Quake 'Q' emblem centered at (cx, cy)."""
    # Crescent outer ring (open at top)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=shadow_col)
    draw.ellipse((cx - r * 0.92, cy - r * 0.92, cx + r * 0.92, cy + r * 0.92), fill=rim_col)
    draw.ellipse((cx - r * 0.84, cy - r * 0.84, cx + r * 0.84, cy + r * 0.84), fill=fill_col)
    # Inner cutout shifted slightly up so bottom is thicker
    ir = r * 0.58
    draw.ellipse((cx - ir, cy - ir * 1.12, cx + ir, cy + ir * 0.88), fill=shadow_col)
    # Top gap notch
    draw.polygon([
        (cx - r * 0.42, cy - r * 1.05),
        (cx + r * 0.42, cy - r * 1.05),
        (cx + r * 0.24, cy - r * 0.42),
        (cx - r * 0.24, cy - r * 0.42),
    ], fill=shadow_col)
    # Central Quake spike piercing down through bottom ring
    draw.polygon([
        (cx - r * 0.14, cy - r * 0.42),
        (cx + r * 0.14, cy - r * 0.42),
        (cx + r * 0.08, cy + r * 1.18),
        (cx, cy + r * 1.30),
        (cx - r * 0.08, cy + r * 1.18),
    ], fill=rim_col)
    draw.polygon([
        (cx - r * 0.09, cy - r * 0.38),
        (cx + r * 0.09, cy - r * 0.38),
        (cx + r * 0.04, cy + r * 1.12),
        (cx - r * 0.04, cy + r * 1.12),
    ], fill=fill_col)


def generate_all_textures(progs_dir=PROGS):
    os.makedirs(progs_dir, exist_ok=True)
    paths = {}
    W = H = 1024
    half = 512

    # -----------------------------------------------------------------------
    # 1. gk3_chassis.png (Lime powder-coat, Matte gunmetal, Diamond plate, Decal)
    # -----------------------------------------------------------------------
    nf = _fbm(H, W, seed=301)
    rng = np.random.default_rng(302)
    flake = rng.uniform(-0.04, 0.04, (H, W)).astype(np.float32)
    arr = np.zeros((H, W, 3), dtype=np.float32)

    u = np.linspace(0.0, 2.0 * math.pi, half, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, half, dtype=np.float32)[:, None]

    # Q1: Matte olive-drab / desert-sage powder-coat
    sheen = 0.88 + 0.14 * np.cos(u - 0.8) + 0.05 * nf[:half, :half] + flake[:half, :half]
    weld_band = 1.0 - 0.18 * np.exp(-((v - 0.06) ** 2) / 0.0012) - 0.18 * np.exp(-((v - 0.94) ** 2) / 0.0012)
    arr[:half, :half, 0] = np.clip(92.0 * sheen * weld_band, 22, 145)
    arr[:half, :half, 1] = np.clip(98.0 * sheen * weld_band, 24, 152)
    arr[:half, :half, 2] = np.clip(70.0 * sheen * weld_band, 18, 118)

    # Q2: Matte gunmetal steel
    gun = 0.86 + 0.10 * np.cos(u - 0.5) + 0.06 * nf[:half, half:] + 0.015 * np.sin(v * 280.0)
    arr[:half, half:, 0] = np.clip(54.0 * gun, 18, 95)
    arr[:half, half:, 1] = np.clip(58.0 * gun, 20, 102)
    arr[:half, half:, 2] = np.clip(66.0 * gun, 24, 115)

    # Q3: Gunmetal diamond-plate floorboard with desert dust
    yy, xx = np.mgrid[0:half, 0:half].astype(np.float32)
    cell = 28.0
    gx = (xx % cell) / cell - 0.5
    gy = (yy % cell) / cell - 0.5
    alt = ((np.floor(xx / cell) + np.floor(yy / cell)) % 2) == 0
    rx = np.where(alt, (gx + gy) * 0.707, (gx - gy) * 0.707)
    ry = np.where(alt, (-gx + gy) * 0.707, (gx + gy) * 0.707)
    lug = np.exp(-((rx / 0.28) ** 4 + (ry / 0.10) ** 4))
    dust = np.clip(0.35 + 0.45 * nf[half:, :half], 0.0, 0.7) * (1.0 - lug)
    base_dp = 46.0 + 42.0 * lug + 8.0 * nf[half:, :half]
    arr[half:, :half, 0] = np.clip(base_dp + dust * 46.0, 18, 160)
    arr[half:, :half, 1] = np.clip(base_dp * 1.02 + dust * 34.0, 18, 150)
    arr[half:, :half, 2] = np.clip(base_dp * 1.08 + dust * 16.0, 20, 140)

    # Q4: Desert Baja stencil plate (draw cleanly inside [512..1024, 512..1024])
    arr[half:, half:, 0] = 36.0 + 6.0 * nf[half:, half:]
    arr[half:, half:, 1] = 40.0 + 6.0 * nf[half:, half:]
    arr[half:, half:, 2] = 44.0 + 6.0 * nf[half:, half:]
    im_ch = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    im_q4 = Image.new("RGB", (half, half), (34, 36, 38))
    dr_q4 = ImageDraw.Draw(im_q4)
    for k in range(-2, 10):
        x0 = k * 72
        dr_q4.polygon([(x0, 8), (x0 + 36, 8), (x0 - 44, 108), (x0 - 80, 108)], fill=(154, 134, 92))
    dr_q4.rectangle((20, 124, 492, 492), fill=(30, 32, 34), outline=(140, 146, 120), width=8)
    dr_q4.text((98, 168), "BAJA", font=_font(96), fill=(214, 208, 192))
    dr_q4.text((133, 283), "03", font=_font(168), fill=(176, 152, 106))
    im_ch.paste(im_q4, (half, half))
    p_ch = os.path.join(progs_dir, "gk3_chassis.png")
    im_ch.save(p_ch, "PNG", optimize=True)
    paths["progs/gk3_chassis"] = "progs/gk3_chassis.png"

    # -----------------------------------------------------------------------
    # 2. gk3_skid.png (Riveted brushed steel, bumper/mesh, amber lamp, Q badge)
    # -----------------------------------------------------------------------
    nf2 = _fbm(H, W, seed=303)
    arr2 = np.zeros((H, W, 3), dtype=np.float32)

    # Q1: Riveted brushed steel skid plate with natural rock-scrape scratches
    brush = 0.84 + 0.08 * np.sin(np.linspace(0, 420, half)[None, :]) + 0.08 * nf2[:half, :half]
    yy_s, xx_s = np.mgrid[0:half, 0:half].astype(np.float32)
    scrape = np.zeros((half, half), dtype=np.float32)
    for sx0, sy0, dx_s, dy_s, w_s in [
        (110.0, 90.0, 0.25, 0.96, 3.2),
        (260.0, 140.0, -0.18, 0.98, 2.5),
        (370.0, 210.0, 0.12, 0.99, 2.8),
        (185.0, 290.0, -0.32, 0.94, 2.2),
    ]:
        dist = np.abs((xx_s - sx0) * dy_s - (yy_s - sy0) * dx_s)
        along = (xx_s - sx0) * dx_s + (yy_s - sy0) * dy_s
        mask_a = np.exp(-((along - 65.0) ** 2) / 3600.0)
        scrape += np.exp(-(dist ** 2) / (w_s * w_s)) * mask_a
    steel_v = 162.0 * brush + 42.0 * np.clip(scrape, 0.0, 1.2)
    arr2[:half, :half, 0] = np.clip(steel_v * 1.01, 45, 235)
    arr2[:half, :half, 1] = np.clip(steel_v * 1.00, 45, 235)
    arr2[:half, :half, 2] = np.clip(steel_v * 0.98, 45, 232)

    # Q2: Gunmetal bull-bar & honeycomb grille
    arr2[:half, half:, 0] = np.clip(42.0 + 7.0 * nf2[:half, half:], 16, 75)
    arr2[:half, half:, 1] = np.clip(44.0 + 7.0 * nf2[:half, half:], 16, 78)
    arr2[:half, half:, 2] = np.clip(48.0 + 7.0 * nf2[:half, half:], 18, 84)

    # Q3: Amber/yellow off-road rally fog lamp Fresnel lens
    yy2, xx2 = np.mgrid[0:half, 0:half].astype(np.float32)
    dx2 = (xx2 - 256.0) / 230.0
    dy2 = (yy2 - 256.0) / 230.0
    rr2 = np.sqrt(dx2 * dx2 + dy2 * dy2)
    fresnel = 0.85 + 0.15 * np.cos(rr2 * 44.0) + 0.07 * np.cos(xx2 * 0.25)
    core_glow = np.exp(-(rr2 ** 2) / 0.34)
    lens = (0.55 + 0.45 * core_glow) * fresnel * (rr2 < 0.92)
    bezel = (rr2 >= 0.92) & (rr2 < 1.04)
    arr2[half:, :half, 0] = np.clip(252.0 * lens + 55.0 * bezel, 20, 255)
    arr2[half:, :half, 1] = np.clip((175.0 + 65.0 * core_glow) * lens + 55.0 * bezel, 18, 245)
    arr2[half:, :half, 2] = np.clip((22.0 + 95.0 * (core_glow ** 2)) * lens + 58.0 * bezel, 14, 180)

    # Q4: Dark grille backing for Quake 'Q' badge
    arr2[half:, half:, 0] = 28.0 + 5.0 * nf2[half:, half:]
    arr2[half:, half:, 1] = 30.0 + 5.0 * nf2[half:, half:]
    arr2[half:, half:, 2] = 34.0 + 5.0 * nf2[half:, half:]

    im_sk = Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8), mode="RGB")
    dr2 = ImageDraw.Draw(im_sk)
    # Rivets along skid plate borders
    for rx in range(36, 480, 56):
        for ry in (36, 476):
            dr2.ellipse((rx - 9, ry - 9, rx + 9, ry + 9), fill=(90, 92, 95))
            dr2.ellipse((rx - 6, ry - 6, rx + 6, ry + 6), fill=(215, 218, 222))
    # Quake 'Q' grille badge in Q4
    dr2.rounded_rectangle((536, 536, 1000, 1000), radius=36, fill=(24, 26, 30), outline=(156, 160, 166), width=10)
    _draw_quake_q(dr2, 768, 768, 158, fill_col=(182, 148, 84), rim_col=(218, 222, 226), shadow_col=(18, 20, 24))
    p_sk = os.path.join(progs_dir, "gk3_skid.png")
    im_sk.save(p_sk, "PNG", optimize=True)
    paths["progs/gk3_skid"] = "progs/gk3_skid.png"

    # -----------------------------------------------------------------------
    # 3. gk3_susp.png (Satin steel springs, anodized gunmetal, chrome, muted tan stripe)
    # -----------------------------------------------------------------------
    nf3 = _fbm(H, W, seed=304)
    arr3 = np.zeros((H, W, 3), dtype=np.float32)
    # Q1: Satin gunmetal-steel spring coat
    sh3 = 0.88 + 0.14 * np.cos(u - 0.7) + 0.03 * nf3[:half, :half]
    arr3[:half, :half, 0] = np.clip(124.0 * sh3, 30, 175)
    arr3[:half, :half, 1] = np.clip(126.0 * sh3, 30, 178)
    arr3[:half, :half, 2] = np.clip(130.0 * sh3, 32, 184)
    # Q2: Anodized gunmetal / dark bronze damper & A-arm
    gm3 = 0.86 + 0.12 * np.cos(u - 0.5) + 0.05 * nf3[:half, half:]
    arr3[:half, half:, 0] = np.clip(74.0 * gm3, 20, 115)
    arr3[:half, half:, 1] = np.clip(70.0 * gm3, 20, 110)
    arr3[:half, half:, 2] = np.clip(66.0 * gm3, 20, 105)
    # Q3: Polished chrome shock shaft
    cr3 = 0.68 + 0.25 * np.cos(u - 0.9) + 0.10 * np.cos(2.0 * u) + 0.02 * nf3[half:, :half]
    arr3[half:, :half, 0] = np.clip(228.0 * cr3, 45, 255)
    arr3[half:, :half, 1] = np.clip(232.0 * cr3, 45, 255)
    arr3[half:, :half, 2] = np.clip(240.0 * cr3, 50, 255)
    # Q4: Muted desert-tan / charcoal diagonal stripes
    im_sp = Image.fromarray(np.clip(arr3, 0, 255).astype(np.uint8), mode="RGB")
    dr3 = ImageDraw.Draw(im_sp)
    dr3.rectangle((512, 512, 1024, 1024), fill=(32, 34, 36))
    for k in range(-4, 14):
        x0 = 512 + k * 64
        dr3.polygon([(x0, 512), (x0 + 32, 512), (x0 - 160, 1024), (x0 - 192, 1024)], fill=(154, 134, 92))
    p_sp = os.path.join(progs_dir, "gk3_susp.png")
    im_sp.save(p_sp, "PNG", optimize=True)
    paths["progs/gk3_susp"] = "progs/gk3_susp.png"

    # -----------------------------------------------------------------------
    # 4. gk3_seat.png (Stitched tan cordura, charcoal bolster, harness, carbon back)
    # -----------------------------------------------------------------------
    nf4 = _fbm(H, W, seed=305)
    arr4 = np.zeros((H, W, 3), dtype=np.float32)
    weave_x = np.sin(np.linspace(0, 220, half)[None, :])
    weave_y = np.sin(np.linspace(0, 220, half)[:, None])
    weave = 1.0 + 0.035 * weave_x * weave_y + 0.06 * nf4[:half, :half]
    # Ribbed seat cushion panels in Q1 (tan leather/cordura)
    ribs4 = 0.90 + 0.10 * np.cos(np.linspace(0, 6.0 * math.pi, half)[:, None])
    arr4[:half, :half, 0] = np.clip(192.0 * weave * ribs4, 50, 232)
    arr4[:half, :half, 1] = np.clip(146.0 * weave * ribs4, 38, 185)
    arr4[:half, :half, 2] = np.clip(92.0 * weave * ribs4, 24, 128)
    # Q2: Charcoal suede bolster
    suede = 1.0 + 0.04 * weave_x * weave_y + 0.08 * nf4[:half, half:]
    arr4[:half, half:, 0] = np.clip(42.0 * suede, 16, 72)
    arr4[:half, half:, 1] = np.clip(44.0 * suede, 16, 75)
    arr4[:half, half:, 2] = np.clip(48.0 * suede, 18, 82)
    # Q3: Harness webbing (charcoal w/ hazard orange edge stripes)
    arr4[half:, :half, 0] = 36.0 + 4.0 * nf4[half:, :half]
    arr4[half:, :half, 1] = 38.0 + 4.0 * nf4[half:, :half]
    arr4[half:, :half, 2] = 42.0 + 4.0 * nf4[half:, :half]
    # Q4: Composite seat shell
    arr4[half:, half:, 0] = 28.0 + 5.0 * nf4[half:, half:]
    arr4[half:, half:, 1] = 30.0 + 5.0 * nf4[half:, half:]
    arr4[half:, half:, 2] = 33.0 + 5.0 * nf4[half:, half:]

    im_st = Image.fromarray(np.clip(arr4, 0, 255).astype(np.uint8), mode="RGB")
    dr4 = ImageDraw.Draw(im_st)
    # Double stitched seams on tan & charcoal panels
    for y_seam in range(85, 480, 85):
        for x_dash in range(16, 496, 20):
            dr4.line((x_dash, y_seam, x_dash + 10, y_seam), fill=(112, 84, 52), width=3)
    for x_seam in (544, 992):
        for y_dash in range(16, 496, 18):
            dr4.line((x_seam, y_dash, x_seam, y_dash + 9), fill=(185, 152, 108), width=3)
    # Harness stripe bands in Q3 (muted khaki/olive)
    dr4.rectangle((60, 512, 110, 1024), fill=(138, 126, 86))
    dr4.rectangle((402, 512, 452, 1024), fill=(138, 126, 86))
    p_st = os.path.join(progs_dir, "gk3_seat.png")
    im_st.save(p_st, "PNG", optimize=True)
    paths["progs/gk3_seat"] = "progs/gk3_seat.png"

    # -----------------------------------------------------------------------
    # 5. gk3_steer.png (Knurled rubber grip, saddle-tan band, brushed spoke, cap)
    # -----------------------------------------------------------------------
    nf5 = _fbm(H, W, seed=306)
    arr5 = np.zeros((H, W, 3), dtype=np.float32)
    knurl = 0.5 + 0.5 * np.sin((xx + yy) * 0.45) * np.sin((xx - yy) * 0.45)
    # Q1: Knurled black rubber grip
    gr5 = 30.0 + 18.0 * knurl + 4.0 * nf5[:half, :half]
    arr5[:half, :half, 0] = gr5
    arr5[:half, :half, 1] = gr5 + 1.0
    arr5[:half, :half, 2] = gr5 + 4.0
    # Q2: Saddle-tan leather 12-o'clock band
    arr5[:half, half:, 0] = 152.0 + 6.0 * nf5[:half, half:]
    arr5[:half, half:, 1] = 112.0 + 6.0 * nf5[:half, half:]
    arr5[:half, half:, 2] = 66.0 + 4.0 * nf5[:half, half:]
    # Q3: Brushed silver/gunmetal spoke
    sp5 = 148.0 + 18.0 * np.cos(u) + 8.0 * nf5[half:, :half]
    arr5[half:, :half, 0] = sp5
    arr5[half:, :half, 1] = sp5 + 2.0
    arr5[half:, :half, 2] = sp5 + 6.0
    # Q4: Center horn cap
    arr5[half:, half:, 0] = 32.0
    arr5[half:, half:, 1] = 34.0
    arr5[half:, half:, 2] = 38.0
    im_sw = Image.fromarray(np.clip(arr5, 0, 255).astype(np.uint8), mode="RGB")
    dr5 = ImageDraw.Draw(im_sw)
    _draw_quake_q(dr5, 768, 768, 130, fill_col=(186, 174, 148), rim_col=(216, 220, 224), shadow_col=(22, 24, 28))
    p_sw = os.path.join(progs_dir, "gk3_steer.png")
    im_sw.save(p_sw, "PNG", optimize=True)
    paths["progs/gk3_steer"] = "progs/gk3_steer.png"

    # -----------------------------------------------------------------------
    # 6. gk3_engine.png (Cast block/fins, gold/brass pleated filter, valve, fuel)
    # -----------------------------------------------------------------------
    nf6 = _fbm(H, W, seed=307)
    arr6 = np.zeros((H, W, 3), dtype=np.float32)
    # Q1: Cast magnesium-aluminum block
    blk = 132.0 + 22.0 * np.cos(u) + 12.0 * nf6[:half, :half]
    arr6[:half, :half, 0] = np.clip(blk * 0.98, 40, 210)
    arr6[:half, :half, 1] = np.clip(blk * 1.00, 42, 214)
    arr6[:half, :half, 2] = np.clip(blk * 1.04, 46, 222)
    # Q2: Muted brass pleated air filter cone
    pleat = 0.72 + 0.28 * np.cos(np.linspace(0, 44.0 * math.pi, half)[None, :])
    mesh = 0.90 + 0.10 * np.sin(np.linspace(0, 120.0, half)[:, None])
    brs = pleat * mesh + 0.05 * nf6[:half, half:]
    arr6[:half, half:, 0] = np.clip(186.0 * brs, 55, 220)
    arr6[:half, half:, 1] = np.clip(154.0 * brs, 45, 190)
    arr6[:half, half:, 2] = np.clip(84.0 * brs, 24, 120)
    # Q3: Crinkle-black valve cover
    crk = 34.0 + 10.0 * nf6[half:, :half]
    arr6[half:, :half, 0] = np.clip(crk, 14, 70)
    arr6[half:, :half, 1] = np.clip(crk + 1.0, 14, 72)
    arr6[half:, :half, 2] = np.clip(crk + 3.0, 16, 76)
    # Q4: Muted brass / bronze accent (plug boots & fuel cap)
    arr6[half:, half:, 0] = np.clip(148.0 + 8.0 * nf6[half:, half:], 60, 195)
    arr6[half:, half:, 1] = np.clip(122.0 + 8.0 * nf6[half:, half:], 50, 165)
    arr6[half:, half:, 2] = 68.0
    p_en = os.path.join(progs_dir, "gk3_engine.png")
    _save_png(arr6, p_en)
    paths["progs/gk3_engine"] = "progs/gk3_engine.png"

    # -----------------------------------------------------------------------
    # 7. gk3_exhaust.png (Diagonal fiberglass heat-wrap + heat-blued chrome + soot)
    # -----------------------------------------------------------------------
    nf7 = _fbm(H, W, seed=308)
    arr7 = np.zeros((H, W, 3), dtype=np.float32)
    # Left half: fiberglass heat wrap (tan/titanium diagonal overlapping tape)
    yy_w, xx_w = np.mgrid[0:H, 0:half].astype(np.float32)
    diag = (yy_w + xx_w * 0.55) % 44.0
    tape_seam = 1.0 - 0.34 * np.exp(-((diag - 2.0) ** 2) / 3.5)
    fib_weave = 1.0 + 0.06 * np.sin(xx_w * 0.8) * np.sin(yy_w * 0.8) + 0.08 * nf7[:, :half]
    arr7[:, :half, 0] = np.clip(182.0 * tape_seam * fib_weave, 45, 225)
    arr7[:, :half, 1] = np.clip(164.0 * tape_seam * fib_weave, 40, 208)
    arr7[:, :half, 2] = np.clip(134.0 * tape_seam * fib_weave, 32, 178)
    # Q2: Mirror chrome megaphone w/ heat-bluing collar
    chr7 = 0.68 + 0.24 * np.cos(u - 0.8) + 0.12 * np.cos(2.0 * u) + 0.02 * nf7[:half, half:]
    straw = np.exp(-((v - 0.22) ** 2) / 0.008)
    blue = np.exp(-((v - 0.36) ** 2) / 0.006)
    arr7[:half, half:, 0] = np.clip(chr7 * 224.0 + straw * 38.0 - blue * 32.0, 35, 255)
    arr7[:half, half:, 1] = np.clip(chr7 * 226.0 + straw * 16.0 - blue * 14.0, 35, 255)
    arr7[:half, half:, 2] = np.clip(chr7 * 234.0 - straw * 26.0 + blue * 42.0, 38, 255)
    # Q4: Soot-black inner bore
    soot = 18.0 + 6.0 * nf7[half:, half:]
    arr7[half:, half:, 0] = np.clip(soot, 8, 36)
    arr7[half:, half:, 1] = np.clip(soot, 8, 36)
    arr7[half:, half:, 2] = np.clip(soot + 2.0, 10, 40)
    p_ex = os.path.join(progs_dir, "gk3_exhaust.png")
    _save_png(arr7, p_ex)
    paths["progs/gk3_exhaust"] = "progs/gk3_exhaust.png"

    # -----------------------------------------------------------------------
    # 8. gk3_wheel.png (Knobby dusty rubber, sidewall, bronze/gunmetal beadlock rim, hub)
    # -----------------------------------------------------------------------
    nf8 = _fbm(H, W, seed=309)
    arr8 = np.zeros((H, W, 3), dtype=np.float32)
    # Q1: Dusty desert knobby tread rubber
    rub8 = 36.0 + 8.0 * nf8[:half, :half]
    dust8 = np.clip(0.20 + 0.35 * nf8[:half, :half], 0.0, 0.55)
    arr8[:half, :half, 0] = np.clip(rub8 + dust8 * 70.0, 18, 128)
    arr8[:half, :half, 1] = np.clip(rub8 + dust8 * 54.0, 18, 114)
    arr8[:half, :half, 2] = np.clip(rub8 + dust8 * 28.0, 20, 96)

    # Q2: Polar tire sidewall (radial ribs + desert dust band)
    yy8, xx8 = np.mgrid[0:half, 0:half].astype(np.float32)
    dx_s = (xx8 - 256.0) / 245.0
    dy_s = (yy8 - 256.0) / 245.0
    rr_s = np.sqrt(dx_s * dx_s + dy_s * dy_s)
    ang_s = np.arctan2(dy_s, dx_s)
    side_rib = 0.5 + 0.5 * np.cos(ang_s * 24.0) * (rr_s > 0.72) * (rr_s < 0.94)
    side_ring = np.exp(-((rr_s - 0.78) ** 2) / 0.0025)
    sw_v = 34.0 + 14.0 * side_rib + 18.0 * side_ring + 6.0 * nf8[:half, half:]
    arr8[:half, half:, 0] = np.clip(sw_v + 18.0 * (rr_s > 0.82), 18, 115)
    arr8[:half, half:, 1] = np.clip(sw_v + 13.0 * (rr_s > 0.82), 18, 105)
    arr8[:half, half:, 2] = np.clip(sw_v + 6.0 * (rr_s > 0.82), 20, 92)

    # Q3: Polar Bronze & Gunmetal Beadlock Rim
    bead_ring = (rr_s > 0.78) & (rr_s <= 1.00)
    lip_hi = np.exp(-((rr_s - 0.80) ** 2) / 0.0008)
    spoke_mask = np.cos(ang_s * 5.0) > 0.15
    dish_shade = 0.76 + 0.24 * spoke_mask + 0.10 * np.cos(ang_s * 2.0)
    # Matte gunmetal inner dish + warm desert-bronze beadlock outer ring
    rim_r = np.where(bead_ring, 184.0 * (0.85 + 0.15 * np.cos(ang_s * 2.0)), 62.0 * dish_shade) + 36.0 * lip_hi
    rim_g = np.where(bead_ring, 134.0 * (0.85 + 0.15 * np.cos(ang_s * 2.0)), 65.0 * dish_shade) + 30.0 * lip_hi
    rim_b = np.where(bead_ring, 68.0 * (0.85 + 0.15 * np.cos(ang_s * 2.0)), 72.0 * dish_shade) + 22.0 * lip_hi
    arr8[half:, :half, 0] = np.clip(rim_r + 6.0 * nf8[half:, :half], 18, 245)
    arr8[half:, :half, 1] = np.clip(rim_g + 6.0 * nf8[half:, :half], 18, 225)
    arr8[half:, :half, 2] = np.clip(rim_b + 6.0 * nf8[half:, :half], 20, 195)

    # Q4: Bronze/chrome lug hardware
    arr8[half:, half:, 0] = np.clip(188.0 + 12.0 * nf8[half:, half:], 40, 240)
    arr8[half:, half:, 1] = np.clip(142.0 + 10.0 * nf8[half:, half:], 32, 195)
    arr8[half:, half:, 2] = np.clip(74.0 + 8.0 * nf8[half:, half:], 20, 125)
    p_wh = os.path.join(progs_dir, "gk3_wheel.png")
    _save_png(arr8, p_wh)
    paths["progs/gk3_wheel"] = "progs/gk3_wheel.png"

    # -----------------------------------------------------------------------
    # 9. gk3_flame.png (512x512 RGBA additive nitro backfire flame texture)
    # -----------------------------------------------------------------------
    FW = FH = 512
    nf9 = _fbm(FH, FW, seed=310, octaves=(4, 8, 16, 32))
    arr9 = np.zeros((FH, FW, 4), dtype=np.float32)
    yy9, xx9 = np.mgrid[0:FH, 0:FW].astype(np.float32)
    # Left half: roaring orange-red outer flame (v=0 base at pipe -> v=1 tip)
    u_o = (xx9[:, :256] / 255.0)
    v_o = (yy9[:, :256] / 511.0)
    edge_o = np.maximum(0.0, np.sin(math.pi * u_o)) ** 0.7
    streaks_o = 0.78 + 0.22 * np.sin(u_o * 26.0 + v_o * 12.0 + nf9[:, :256] * 4.5)
    axial_o = np.clip((1.0 - v_o) ** 0.65 * (1.0 - np.exp(-v_o * 18.0)), 0.0, 1.0)
    int_o = np.clip(edge_o * streaks_o * axial_o * 1.25, 0.0, 1.0)
    arr9[:, :256, 0] = 255.0 * (int_o ** 0.55)
    arr9[:, :256, 1] = 215.0 * (int_o ** 1.15) * (1.0 - 0.55 * v_o)
    arr9[:, :256, 2] = 75.0 * (int_o ** 2.2) * np.exp(-v_o * 3.0)
    arr9[:, :256, 3] = 255.0 * int_o

    # Right half: white-hot inner nitro core + shock diamonds
    u_c = (xx9[:, 256:] - 256.0) / 255.0
    v_c = (yy9[:, 256:] / 511.0)
    edge_c = np.maximum(0.0, np.sin(math.pi * u_c)) ** 0.9
    diamonds = 0.72 + 0.38 * (np.cos(v_c * 24.0) ** 2)
    axial_c = np.clip((1.0 - v_c) ** 0.85 * (1.0 - np.exp(-v_c * 22.0)), 0.0, 1.0)
    int_c = np.clip(edge_c * diamonds * axial_c * 1.35, 0.0, 1.0)
    arr9[:, 256:, 0] = 255.0 * (int_c ** 0.45)
    arr9[:, 256:, 1] = 248.0 * (int_c ** 0.65)
    arr9[:, 256:, 2] = 195.0 * (int_c ** 1.15) * (1.0 - 0.45 * v_c)
    arr9[:, 256:, 3] = 255.0 * int_c

    p_fl = os.path.join(progs_dir, "gk3_flame.png")
    _save_png(arr9, p_fl, mode="RGBA")
    paths["progs/gk3_flame"] = "progs/gk3_flame.png"
    return paths


# ---------------------------------------------------------------------------
# Geometry Helpers
# ---------------------------------------------------------------------------
def add_helical_spring(part, p0, p1, coil_r=1.6, wire_r=0.35, turns=7.0, pts_per_turn=10, segs=6, uv_rect=UV_SUSP_ORANGE):
    """Sweeps a true 3D helical coil spring between p0 and p1."""
    axis = vsub(p1, p0)
    L = vlen(axis)
    X, Y, Z = basis_from_axis(axis)
    n_pts = max(8, int(round(turns * pts_per_turn)))
    pts = []
    for i in range(n_pts + 1):
        t = i / float(n_pts)
        # Taper coil radius slightly at the very ends so it seats neatly on spring perches
        env = 1.0
        if t < 0.08:
            env = 0.85 + 0.15 * (t / 0.08)
        elif t > 0.92:
            env = 0.85 + 0.15 * ((1.0 - t) / 0.08)
        th = 2.0 * math.pi * turns * t
        c = vadd(p0, vmul(X, t * L))
        pts.append(vadd(c, vadd(vmul(Y, coil_r * env * math.cos(th)), vmul(Z, coil_r * env * math.sin(th)))))
    part.add_tube(pts, [wire_r] * len(pts), segs=segs, uv_rect=uv_rect, cap_start=True, cap_end=True)


def add_strake_box(part, pts8, uv_rect, side_uv=None, top_uv=None):
    """Adds a crisp 6-quad hexahedron given 8 corners:
    [b00, b10, b11, b01, t00, t10, t11, t01]
    """
    b00, b10, b11, b01, t00, t10, t11, t01 = pts8
    u0, v0, u1, v1 = uv_rect
    su = side_uv if side_uv else uv_rect
    tu = top_uv if top_uv else uv_rect
    # Bottom
    part.add_quad(b00, b01, b11, b10, (u0, v0), (u0, v1), (u1, v1), (u1, v0))
    # Top
    part.add_quad(t00, t10, t11, t01, (tu[0], tu[1]), (tu[2], tu[1]), (tu[2], tu[3]), (tu[0], tu[3]))
    # Sides
    part.add_quad(b00, b10, t10, t00, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))
    part.add_quad(b10, b11, t11, t10, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))
    part.add_quad(b11, b01, t01, t11, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))
    part.add_quad(b01, b00, t00, t01, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))


def add_rounded_tube_chain(part, waypoints, radius, segs=8, uv_rect=UV_CHASSIS_LIME, bevel_r=1.8):
    """Subdivides sharp polyline corners slightly for smooth tubular frame bends."""
    if len(waypoints) <= 2:
        part.add_tube(waypoints, [radius] * len(waypoints), segs=segs, uv_rect=uv_rect)
        return
    pts = [waypoints[0]]
    for i in range(1, len(waypoints) - 1):
        p_prev = waypoints[i - 1]
        p_cur = waypoints[i]
        p_next = waypoints[i + 1]
        d1 = vsub(p_cur, p_prev)
        d2 = vsub(p_next, p_cur)
        l1, l2 = vlen(d1), vlen(d2)
        b = min(bevel_r, 0.35 * l1, 0.35 * l2)
        if b > 0.15:
            q1 = vsub(p_cur, vmul(vnorm(d1), b))
            q2 = vadd(p_cur, vmul(vnorm(d2), b))
            qm = vlerp(vlerp(q1, p_cur, 0.5), vlerp(p_cur, q2, 0.5), 0.5)
            pts.extend([q1, qm, q2])
        else:
            pts.append(p_cur)
    pts.append(waypoints[-1])
    part.add_tube(pts, [radius] * len(pts), segs=segs, uv_rect=uv_rect)


# ---------------------------------------------------------------------------
# 1. Surface Builders (Static Local Coordinates)
# ---------------------------------------------------------------------------
def build_chassis_cage():
    """Acid-lime green & matte gunmetal tubular exoskeleton + diamond floor + pedals."""
    p = MeshPart("chassis_cage")

    # Acid-lime main outer lower frame rails (L/R)
    for sy in (+1.0, -1.0):
        add_rounded_tube_chain(p, [
            (-42.5, sy * 11.2, 11.0),
            (-23.0, sy * 14.8, 6.2),
            (+23.0, sy * 14.6, 5.8),
            (+39.5, sy * 10.2, 11.2),
        ], 1.32, segs=8, uv_rect=UV_CHASSIS_LIME)

        # Acid-lime upper side-pod hip / nerf rails (cockpit clear inside |Y|<=13)
        add_rounded_tube_chain(p, [
            (-20.0, sy * 15.2, 15.8),
            (-8.0,  sy * 16.0, 15.8),
            (+13.5, sy * 15.4, 15.6),
            (+27.5, sy * 12.2, 16.2),
            (+40.0, sy * 9.5,  15.5),
        ], 1.28, segs=8, uv_rect=UV_CHASSIS_LIME)

        # Side nerf vertical/angled rock-slider struts
        for sx_b, sy_b, sz_b, sx_t, sy_t, sz_t in [
            (-19.5, 14.8, 6.2, -19.5, 15.2, 15.8),
            (+1.5,  14.7, 5.9, +1.5,  15.8, 15.7),
            (+18.0, 14.6, 5.9, +17.5, 14.5, 15.8),
            (+36.5, 11.0, 10.2, +37.5, 10.0, 15.6),
        ]:
            p.add_tube([(sx_b, sy * sy_b, sz_b), (sx_t, sy * sy_t, sz_t)], [1.05, 1.05], segs=7, uv_rect=UV_CHASSIS_LIME)

        # Front hood nose-sloped rails from dash arch to front bulkhead
        add_rounded_tube_chain(p, [
            (+17.8, sy * 13.5, 16.2),
            (+17.5, sy * 10.0, 23.2),
            (+39.5, sy * 8.2,  15.5),
        ], 1.15, segs=8, uv_rect=UV_CHASSIS_LIME)

    # Dash cowl crossbar at X=+17.5, Z=23.2 (cleanly ahead of knees)
    p.add_tube([(+17.5, -10.5, 23.2), (+17.5, +10.5, 23.2)], [1.18, 1.18], segs=8, uv_rect=UV_CHASSIS_GUN)

    # Rear Baja Roll-Bar Hoop (strictly behind X <= -19.5 so overhead above seat is open!)
    add_rounded_tube_chain(p, [
        (-20.0, -15.2, 15.8),
        (-21.2, -14.2, 26.5),
        (-22.8, -11.5, 34.5),
        (-23.2,   0.0, 35.6),
        (-22.8, +11.5, 34.5),
        (-21.2, +14.2, 26.5),
        (-20.0, +15.2, 15.8),
    ], 1.38, segs=8, uv_rect=UV_CHASSIS_LIME, bevel_r=2.2)

    # Rear K-braces & rear engine guard bumper hoop
    for sy in (+1.0, -1.0):
        add_rounded_tube_chain(p, [
            (-22.8, sy * 11.5, 34.0),
            (-34.0, sy * 12.2, 25.5),
            (-43.2, sy * 11.2, 14.5),
            (-42.5, sy * 11.2, 11.0),
        ], 1.15, segs=8, uv_rect=UV_CHASSIS_LIME)
        # Diagonal gusset down to rear engine cradle
        p.add_tube([(-21.0, sy * 14.2, 26.0), (-33.0, sy * 11.8, 12.0)], [0.98, 0.98], segs=7, uv_rect=UV_CHASSIS_GUN)

    # Rear bumper crossbar + baja number plate tab on roll hoop
    add_rounded_tube_chain(p, [
        (-43.2, -11.2, 14.5),
        (-45.2,  -6.5, 14.2),
        (-45.2,  +6.5, 14.2),
        (-43.2, +11.2, 14.5),
    ], 1.25, segs=8, uv_rect=UV_CHASSIS_GUN)
    p.add_tube([(-42.5, -11.2, 11.0), (-42.5, +11.2, 11.0)], [1.10, 1.10], segs=7, uv_rect=UV_CHASSIS_GUN)

    # Roll-bar top Baja decal plate
    p.add_chamfer_box(-24.2, -21.8, -8.5, +8.5, 32.2, 35.2, ch=0.25, uv_rect=UV_CHASSIS_DECAL, top_uv=UV_CHASSIS_DECAL)

    # Matte gunmetal structural cross-members & engine cradle rails
    for cx in (-38.0, -25.0, -16.0, -3.0, +10.0, +23.5, +35.0):
        w_y = 14.2 if -22.0 <= cx <= +23.0 else 10.4
        cz = 5.6 if -22.0 <= cx <= +23.0 else 10.2
        p.add_tube([(cx, -w_y, cz), (cx, +w_y, cz)], [0.95, 0.95], segs=7, uv_rect=UV_CHASSIS_GUN)

    # Longitudinal engine cradle sub-rails
    for sy in (+1.0, -1.0):
        p.add_tube([(-39.0, sy * 6.8, 10.0), (-22.0, sy * 6.8, 6.2)], [0.95, 0.95], segs=7, uv_rect=UV_CHASSIS_GUN)

    # Gunmetal diamond-plate floor pan (X in [-18, +26], Z = 4.6..5.4)
    p.add_chamfer_box(-18.0, +26.0, -13.6, +13.6, 4.5, 5.4, ch=0.18, uv_rect=UV_CHASSIS_GUN, top_uv=UV_CHASSIS_FLOOR)

    # Footwell Pedals (Throttle right Y=-4.5, Brake left Y=+4.5)
    for sy in (+1.0, -1.0):
        p.add_tube([(+26.0, sy * 4.5, 5.5), (+27.5, sy * 4.5, 10.8)], [0.42, 0.42], segs=6, uv_rect=UV_CHASSIS_GUN)
        p.add_chamfer_box(+26.2, +27.6, sy * 4.5 - 1.5, sy * 4.5 + 1.5, 7.6, 11.4, ch=0.14, uv_rect=UV_CHASSIS_FLOOR)

    # Front shock tower hoop (where front coil-overs anchor)
    for sy in (+1.0, -1.0):
        add_rounded_tube_chain(p, [
            (+24.0, sy * 11.8, 12.5),
            (+27.5, sy * 12.5, 22.0),
            (+31.5, sy * 11.0, 14.5),
        ], 1.05, segs=7, uv_rect=UV_CHASSIS_GUN)

    return p


def build_skid_lights():
    """Riveted brushed-steel front skid plate, bull-bar bumper, twin amber fog lamps, Quake 'Q' badge."""
    p = MeshPart("skid_lights")

    # 1) Riveted brushed-steel front skid plate (sloped belly -> nose)
    skid_secs = [
        (+25.0, 0.0, 10.8, 4.9, 0.55, 0.2),
        (+34.5, 0.0, 10.6, 6.4, 0.55, 0.2),
        (+45.2, 0.0, 9.6, 13.8, 0.55, 0.2),
    ]
    p.add_loft(skid_secs, uv_rect=UV_SKID_PLATE, side_uv=UV_SKID_PLATE, top_uv=UV_SKID_PLATE)

    # 2) Heavy bull-bar tubular front bumper + stinger hoop
    add_rounded_tube_chain(p, [
        (+40.5, -13.5, 10.0),
        (+46.8, -12.2, 10.2),
        (+48.0,  -6.2, 10.8),
        (+48.0,  +6.2, 10.8),
        (+46.8, +12.2, 10.2),
        (+40.5, +13.5, 10.0),
    ], 1.25, segs=8, uv_rect=UV_SKID_BUMPER)

    # Upper bull-bar stinger hoop
    add_rounded_tube_chain(p, [
        (+45.0, -9.5, 10.6),
        (+47.6, -7.0, 16.4),
        (+47.6, +7.0, 16.4),
        (+45.0, +9.5, 10.6),
    ], 1.05, segs=8, uv_rect=UV_SKID_BUMPER)

    # Twin bull-bar uprights
    for sy in (+1.0, -1.0):
        p.add_tube([(+47.7, sy * 6.2, 10.6), (+47.4, sy * 6.2, 16.4)], [0.85, 0.85], segs=7, uv_rect=UV_SKID_BUMPER)

    # 3) Tilted nose honeycomb grille + Quake 'Q' Grille Badge
    # Nose grille plate tilted back from (+44.6, Z=11.5) to (+41.2, Z=16.8)
    add_strake_box(p, [
        (+43.8, -7.8, 11.4), (+44.6, -7.8, 11.4), (+44.6, +7.8, 11.4), (+43.8, +7.8, 11.4),
        (+40.4, -7.4, 16.6), (+41.2, -7.4, 16.6), (+41.2, +7.4, 16.6), (+40.4, +7.4, 16.6),
    ], uv_rect=UV_SKID_BUMPER, top_uv=UV_SKID_BUMPER)

    # Crisp Quake 'Q' emblem badge mounted proud on nose grille face (facing +X/+Z)
    p.add_quad(
        (+44.5, +3.2, 11.7),
        (+44.5, -3.2, 11.7),
        (+41.6, -3.2, 16.4),
        (+41.6, +3.2, 16.4),
        (UV_SKID_QBADGE[0], UV_SKID_QBADGE[3]),
        (UV_SKID_QBADGE[2], UV_SKID_QBADGE[3]),
        (UV_SKID_QBADGE[2], UV_SKID_QBADGE[1]),
        (UV_SKID_QBADGE[0], UV_SKID_QBADGE[1]),
    )

    # 4) Twin round amber/yellow off-road rally fog lamps
    for sy in (+1.0, -1.0):
        lc = (+43.2, sy * 6.8, 18.6)
        # Mounting stalk
        p.add_tube([(+42.8, sy * 6.8, 15.6), (+43.0, sy * 6.8, 17.0)], [0.65, 0.65], segs=6, uv_rect=UV_SKID_BUMPER)
        # Housing cup (axis along +X)
        p.add_lathe(lc, (+1.0, 0.0, 0.0), [
            (-2.4, 0.00, 0.0),
            (-2.2, 1.95, 0.25),
            (-1.0, 2.75, 0.55),
            (+0.6, 2.95, 0.85),
            (+1.0, 2.95, 0.95),
            (+1.0, 2.55, 1.00),
        ], segs=18, uv_rect=UV_SKID_BUMPER)
        # Glowing amber Fresnel glass lens
        p.add_lathe(lc, (+1.0, 0.0, 0.0), [
            (+0.9, 2.55, 1.00, 2.55),
            (+1.25, 1.85, 0.72, 2.55),
            (+1.42, 0.95, 0.36, 2.55),
            (+1.48, 0.00, 0.00, 2.55),
        ], segs=18, uv_mode="polar", uv_rect=UV_SKID_LAMP)

    return p


def build_suspension():
    """Front A-arm wishbones, hazard-orange coil-over shock springs, rear trailing arms & axle."""
    p = MeshPart("suspension")

    # 1) Front Double A-Arm Wishbones + Knuckles + Coil-Over Shocks
    for sy in (+1.0, -1.0):
        # Lower A-arm
        p.add_tube([(+21.5, sy * 11.2, 7.6), (+28.0, sy * 22.4, 8.2)], [0.80, 0.75], segs=7, uv_rect=UV_SUSP_GUN)
        p.add_tube([(+34.5, sy * 10.6, 8.2), (+28.0, sy * 22.4, 8.2)], [0.80, 0.75], segs=7, uv_rect=UV_SUSP_GUN)
        # Upper A-arm
        p.add_tube([(+22.8, sy * 11.4, 13.4), (+28.0, sy * 22.0, 13.6)], [0.68, 0.65], segs=7, uv_rect=UV_SUSP_GUN)
        p.add_tube([(+33.2, sy * 10.8, 13.6), (+28.0, sy * 22.0, 13.6)], [0.68, 0.65], segs=7, uv_rect=UV_SUSP_GUN)
        # Steering knuckle / spindle upright + tie rod
        p.add_tube([(+28.0, sy * 22.4, 7.6), (+28.0, sy * 22.0, 14.2)], [0.88, 0.88], segs=8, uv_rect=UV_SUSP_GUN)
        p.add_tube([(+28.0, sy * 22.2, 10.5), (+28.0, sy * 25.5, 10.5)], [0.95, 0.95], segs=8, uv_rect=UV_SUSP_CHROME)
        p.add_tube([(+25.2, sy * 9.5, 10.2), (+25.8, sy * 22.2, 10.2)], [0.44, 0.44], segs=6, uv_rect=UV_SUSP_CHROME)

        # Front Coil-Over Shock (from lower A-arm tab up to front shock tower)
        sh_bot = (+28.0, sy * 19.2, 8.8)
        sh_top = (+27.5, sy * 12.6, 21.4)
        sh_mid = vlerp(sh_bot, sh_top, 0.46)
        p.add_tube([sh_bot, sh_mid], [0.52, 0.52], segs=7, uv_rect=UV_SUSP_CHROME)
        p.add_tube([sh_mid, sh_top], [0.95, 0.95], segs=8, uv_rect=UV_SUSP_GUN)
        # Hazard-orange helical spring
        sp_a = vlerp(sh_bot, sh_top, 0.14)
        sp_b = vlerp(sh_bot, sh_top, 0.84)
        add_helical_spring(p, sp_a, sp_b, coil_r=1.55, wire_r=0.34, turns=6.5, pts_per_turn=9, segs=6, uv_rect=UV_SUSP_ORANGE)

    # 2) Rear Trailing Arms, Solid Axle Carrier & Long-Travel Coil-Over Shocks
    # Solid rear axle housing
    p.add_tube([(-30.5, -24.5, 12.0), (-30.5, +24.5, 12.0)], [1.15, 1.15], segs=10, uv_rect=UV_SUSP_CHROME)
    # Rear center brake rotor & drive sprocket disc
    p.add_lathe((-30.5, -2.5, 12.0), (0.0, 1.0, 0.0), [
        (0.0, 1.15, 0.0), (0.0, 4.2, 0.5), (0.55, 4.2, 0.7), (0.55, 1.15, 1.0),
    ], segs=16, uv_rect=UV_SUSP_GUN)
    p.add_lathe((-30.5, +2.5, 12.0), (0.0, 1.0, 0.0), [
        (0.0, 1.15, 0.0), (0.0, 4.8, 0.5), (0.55, 4.8, 0.7), (0.55, 1.15, 1.0),
    ], segs=16, uv_rect=UV_SUSP_HAZARD)

    for sy in (+1.0, -1.0):
        # Boxed/tubular rear trailing arm
        p.add_tube([(-18.5, sy * 15.2, 8.0), (-30.5, sy * 22.8, 12.0)], [1.10, 1.05], segs=7, uv_rect=UV_SUSP_GUN)
        p.add_tube([(-18.5, sy * 15.2, 11.2), (-30.5, sy * 22.8, 12.0)], [0.85, 0.85], segs=7, uv_rect=UV_SUSP_GUN)

        # Rear Long-Travel Coil-Over Shock
        r_bot = (-30.5, sy * 21.8, 12.8)
        r_top = (-22.0, sy * 14.0, 25.8)
        r_mid = vlerp(r_bot, r_top, 0.44)
        p.add_tube([r_bot, r_mid], [0.58, 0.58], segs=7, uv_rect=UV_SUSP_CHROME)
        p.add_tube([r_mid, r_top], [1.05, 1.05], segs=8, uv_rect=UV_SUSP_GUN)
        # Piggyback reservoir cylinder
        pb_a = vadd(r_top, (-2.6, 0.0, -0.6))
        pb_b = vadd(pb_a, (-1.8, 0.0, -4.5))
        p.add_tube([pb_a, pb_b], [0.92, 0.92], segs=8, uv_rect=UV_SUSP_HAZARD)
        # Hazard-orange helical spring
        rsp_a = vlerp(r_bot, r_top, 0.14)
        rsp_b = vlerp(r_bot, r_top, 0.84)
        add_helical_spring(p, rsp_a, rsp_b, coil_r=1.75, wire_r=0.38, turns=7.0, pts_per_turn=9, segs=6, uv_rect=UV_SUSP_ORANGE)

    return p


def build_seat():
    """Rugged stitched tan/charcoal bolstered off-road Baja bucket seat.
    Carefully respects player-fit clearance:
      - Seat pan top at X=-9.0, Y=0.0, Z=10.0
      - Side bolsters outside |Y| >= 11.4 (clear of 22u torso box |Y| <= 11.0)
      - Backrest behind X <= -16.2 (clear of seated torso)
    """
    p = MeshPart("seat")

    # Seat base pan: top at Z=10.0 under X in [-16.5, -2.5], subtle thigh lip at X=-1.0
    p.add_loft([
        (-16.5, 0.0, 11.3, 8.2, 1.75, 0.45),
        (-9.0,  0.0, 11.3, 8.3, 1.70, 0.45),
        (-2.5,  0.0, 11.3, 8.4, 1.65, 0.45),
        (+0.5,  0.0, 11.0, 8.9, 1.60, 0.55),
    ], uv_rect=UV_SEAT_CHARCOAL, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_TAN)

    # Raised charcoal side hip bolsters (strictly at |Y| = 11.4..14.0 -> outside |Y|<=11!)
    for sy in (+1.0, -1.0):
        p.add_loft([
            (-16.8, sy * 12.7, 1.30, 11.8, 3.8, 0.45),
            (-9.0,  sy * 12.7, 1.30, 11.4, 3.2, 0.45),
            (-1.2,  sy * 12.6, 1.25, 10.6, 2.2, 0.45),
        ], uv_rect=UV_SEAT_CHARCOAL, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_CHARCOAL)

    # Sloped contoured Baja seatback (front face at X <= -16.5!)
    # Loft along X slices from bottom (-16.6) up to top (-22.0)
    # Build via stacked strakes so back shell = UV_SEAT_BACK and front cushion = UV_SEAT_TAN
    back_levels = [
        (-16.6, -19.2, 10.5, 9.2, 14.5),
        (-17.8, -20.4, 10.6, 14.5, 20.5),
        (-19.2, -21.8, 10.4, 20.5, 26.8),
        (-20.4, -22.8,  8.6, 26.8, 31.2),
    ]
    for x_f, x_b, hw, z0, z1 in back_levels:
        p.add_chamfer_box(x_b, x_f, -hw, +hw, z0, z1, ch=0.4, uv_rect=UV_SEAT_TAN, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_CHARCOAL)

    # Backrest side shoulder bolsters (|Y| = 11.4..13.8)
    for sy in (+1.0, -1.0):
        add_strake_box(p, [
            (-18.8, sy * 11.4, 13.0), (-15.8, sy * 11.4, 13.0), (-15.8, sy * 13.8, 13.0), (-18.8, sy * 13.8, 13.0),
            (-22.2, sy * 11.4, 28.5), (-19.2, sy * 11.4, 28.5), (-19.2, sy * 13.6, 28.5), (-22.2, sy * 13.6, 28.5),
        ], uv_rect=UV_SEAT_CHARCOAL, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_CHARCOAL)

    # Contoured desert headrest cushion (X <= -19.8)
    p.add_chamfer_box(-23.4, -20.0, -5.2, +5.2, 28.5, 33.8, ch=0.7, uv_rect=UV_SEAT_TAN, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_CHARCOAL)

    # 4-point racing harness straps draped on seatback front (kept at X <= -16.2)
    for sy in (+1.0, -1.0):
        p.add_tube([
            (-20.2, sy * 5.2, 28.2),
            (-18.6, sy * 5.5, 21.0),
            (-16.4, sy * 5.8, 13.0),
        ], [0.55, 0.55, 0.55], segs=6, uv_rect=UV_SEAT_HARNESS)

    return p


def build_steering():
    """Angled steering column + chunky knurled 3-spoke rally steering wheel at (13.0, 0.0, 24.5)."""
    p = MeshPart("steering")
    hub = (13.0, 0.0, 24.5)
    # Normal vector pointing back & slightly up toward driver (tilted 26 deg from horizontal)
    tilt = math.radians(26.0)
    axis = (-math.cos(tilt), 0.0, math.sin(tilt))
    X, Y, Z = basis_from_axis(axis, up_hint=(0.0, 0.0, 1.0))

    # Steering column shaft + dash collar
    col_bot = (25.0, 0.0, 11.5)
    col_mid = (18.2, 0.0, 19.2)
    p.add_tube([col_bot, col_mid, hub], [0.75, 0.85, 1.05], segs=8, uv_rect=UV_STEER_SPOKE)
    p.add_lathe(col_mid, vsub(hub, col_bot), [
        (-1.2, 1.35, 0.0), (+1.2, 1.35, 1.0),
    ], segs=10, uv_rect=UV_STEER_SPOKE)

    # Dish center hub & Quake horn cap
    p.add_lathe(hub, axis, [
        (-1.4, 0.0, 0.0),
        (-1.4, 1.65, 0.25),
        (+0.6, 1.95, 0.65),
        (+0.9, 1.85, 0.90),
        (+0.9, 0.0, 1.0),
    ], segs=14, uv_mode="polar", uv_rect=UV_STEER_CAP)

    # Chunky knurled torus wheel rim (R = 5.4u, thick grip r = 0.82u)
    rim_r = 5.4
    grip_r = 0.82
    n_ring = 28
    # Build main rim + hazard-orange 12-o'clock centering band at top (theta near pi/2 around Z)
    rim_pts = []
    for i in range(n_ring + 1):
        th = 2.0 * math.pi * (i / float(n_ring))
        # Center of wheel tube in local (Y, Z) plane; note Z is "up" on the wheel!
        rim_pts.append(vadd(hub, vadd(vmul(X, 1.6), vadd(vmul(Y, rim_r * math.cos(th)), vmul(Z, rim_r * math.sin(th))))))
    p.add_tube(rim_pts, [grip_r] * len(rim_pts), segs=8, uv_rect=UV_STEER_GRIP, cap_start=False, cap_end=False)

    # Hazard-orange 12-o'clock band over top arc (78 deg .. 102 deg)
    band_pts = []
    for k in range(5):
        th = math.radians(76.0 + 7.0 * k)
        band_pts.append(vadd(hub, vadd(vmul(X, 1.6), vadd(vmul(Y, rim_r * math.cos(th)), vmul(Z, rim_r * math.sin(th))))))
    p.add_tube(band_pts, [grip_r * 1.06] * len(band_pts), segs=8, uv_rect=UV_STEER_STRIPE, cap_start=True, cap_end=True)

    # 3 Rally Spokes (Left, Right, Bottom)
    for ang_deg in (195.0, 345.0, 270.0):
        a = math.radians(ang_deg)
        dir_sp = vadd(vmul(Y, math.cos(a)), vmul(Z, math.sin(a)))
        sp_in = vadd(hub, vadd(vmul(X, 0.2), vmul(dir_sp, 1.5)))
        sp_out = vadd(hub, vadd(vmul(X, 1.6), vmul(dir_sp, rim_r - 0.3)))
        p.add_tube([sp_in, sp_out], [0.56, 0.42], segs=6, uv_rect=UV_STEER_SPOKE)

    return p


def build_engine_vtwin():
    """Exposed rear air-cooled V-twin engine with finned cylinders, gold/brass air filter cone, & fuel cell."""
    p = MeshPart("engine_vtwin")

    # 1) Crankcase + Gearbox Block
    p.add_chamfer_box(-35.5, -26.5, -6.5, +6.5, 9.8, 16.5, ch=0.55, uv_rect=UV_ENG_BLOCK)
    # Left/Right circular crankcase side covers
    for sy in (+1.0, -1.0):
        p.add_lathe((-31.0, sy * 6.5, 13.0), (0.0, sy, 0.0), [
            (0.0, 0.0, 0.0), (0.0, 3.6, 0.4), (1.1, 3.4, 0.8), (1.1, 0.0, 1.0),
        ], segs=14, uv_rect=UV_ENG_VALVE)

    # 2) Two Finned V-Twin Cylinders (splayed +/-34 deg in Y-Z and staggered in X)
    for sy, cx_off in ((+1.0, -29.4), (-1.0, -32.2)):
        cyl_base = (cx_off, sy * 2.2, 15.2)
        cyl_axis = vnorm((0.0, sy * 0.56, 0.83))
        # Cylinder sleeve
        p.add_lathe(cyl_base, cyl_axis, [
            (0.0, 2.75, 0.0), (6.5, 2.75, 0.6), (6.5, 3.25, 0.7), (9.0, 3.25, 0.9), (9.0, 0.0, 1.0),
        ], segs=12, uv_rect=UV_ENG_BLOCK)
        # 6 Stacked Cooling Fins
        for fi in range(6):
            fh = 1.4 + fi * 0.95
            fr = 3.85 + (0.28 if fi >= 4 else 0.0)
            p.add_lathe(cyl_base, cyl_axis, [
                (fh, 2.7, 0.0), (fh, fr, 0.4), (fh + 0.34, fr, 0.6), (fh + 0.34, 2.7, 1.0),
            ], segs=12, uv_rect=UV_ENG_BLOCK)
        # Crinkle-black OHV Valve Rocker Cover on top of cylinder head
        top_pt = vadd(cyl_base, vmul(cyl_axis, 8.8))
        p.add_lathe(top_pt, cyl_axis, [
            (0.0, 0.0, 0.0), (0.0, 3.35, 0.2), (1.5, 3.15, 0.65), (1.9, 2.2, 0.85), (1.9, 0.0, 1.0),
        ], segs=10, uv_rect=UV_ENG_VALVE)
        # Orange spark plug boot
        sp_a = vadd(cyl_base, vadd((1.8, sy * 1.4, 0.0), vmul(cyl_axis, 6.2)))
        sp_b = vadd(sp_a, (1.0, sy * 1.1, 1.4))
        p.add_tube([sp_a, sp_b], [0.46, 0.34], segs=6, uv_rect=UV_ENG_ACCENT)

    # 3) Intake Plenum + Prominent Gold/Brass Pleated Air Filter Cone
    p.add_tube([(-30.8, 0.0, 16.5), (-30.8, 0.0, 23.0), (-33.0, 0.0, 25.0)], [1.4, 1.6, 1.8], segs=8, uv_rect=UV_ENG_BLOCK)
    # Pleated gold/brass cone pointing back-up
    cone_origin = (-32.8, 0.0, 24.8)
    cone_axis = vnorm((-0.92, 0.0, 0.39))
    p.add_lathe(cone_origin, cone_axis, [
        (0.0, 0.0, 0.0),
        (0.0, 2.2, 0.05),
        (0.6, 3.4, 0.15),
        (6.4, 2.35, 0.85),
        (6.6, 2.35, 0.90),
        (7.2, 1.85, 0.95),
        (7.2, 0.0, 1.00),
    ], segs=18, uv_rect=UV_ENG_FILTER)

    # 4) Rear Baja Fuel Cell (tucked cleanly behind seatback at X = -24..-21)
    p.add_chamfer_box(-26.0, -21.8, -6.2, +6.2, 11.0, 19.5, ch=0.65, uv_rect=UV_ENG_VALVE, top_uv=UV_ENG_ACCENT)
    p.add_lathe((-23.8, +2.8, 19.5), (0.0, 0.0, 1.0), [
        (0.0, 1.4, 0.0), (1.1, 1.4, 0.7), (1.1, 0.0, 1.0),
    ], segs=10, uv_rect=UV_ENG_FILTER)

    return p


def build_exhaust_dual():
    """Dual swept-up chrome megaphone exhaust pipes with fiberglass heat-wrap headers."""
    p = MeshPart("exhaust_dual")

    for sy in (+1.0, -1.0):
        cx_port = -29.4 if sy > 0 else -32.2
        # Heat-wrapped curved header pipe from V-twin port to megaphone collector
        hdr_pts = [
            (cx_port - 1.2, sy * 5.8, 18.8),
            (-34.2, sy * 8.2, 16.5),
            (-37.8, sy * 9.8, 17.5),
        ]
        p.add_tube(hdr_pts, [1.22, 1.28, 1.25], segs=10, uv_rect=UV_EXH_WRAP, cap_start=True, cap_end=False)

        # Swept-up flared Chrome Megaphone Cone ending at (-46.5, +/-10.5, 20.5)
        mega_start = (-37.6, sy * 9.8, 17.4)
        mega_end = (-46.5, sy * 10.5, 20.5)
        mega_axis = vsub(mega_end, mega_start)
        L_m = vlen(mega_axis)
        p.add_lathe(mega_start, mega_axis, [
            (0.0, 1.20, 0.05),
            (1.6, 1.32, 0.22),
            (L_m - 0.3, 2.35, 0.88),
            (L_m, 2.45, 0.96),
            (L_m, 2.05, 0.99),
        ], segs=16, uv_rect=UV_EXH_CHROME)
        # Deep soot-blackened inner megaphone bore cone
        p.add_lathe(mega_start, mega_axis, [
            (L_m, 2.05, 0.0),
            (L_m - 4.2, 0.90, 0.85),
            (L_m - 4.2, 0.00, 1.00),
        ], segs=12, uv_rect=UV_EXH_BORE)

    return p


def build_offroad_wheel(side_sign, radius=10.5, half_width=4.3, n_lugs=24):
    """Builds one wide, beefy knobby-treaded off-road wheel at local origin (0, 0, 0).
    Outer face points along (0, side_sign, 0).
    3 staggered rows of 24 modeled 3D tread lugs -> at ANY rotation angle, bottom is within 0.03u of -radius!
    """
    p = MeshPart("wheel")
    axis = (0.0, float(side_sign), 0.0)
    up_h = (0.0, 0.0, 1.0)
    X_w, Y_w, Z_w = basis_from_axis(axis, up_hint=up_h)

    lug_h = 0.85 if radius < 11.2 else 1.00
    r_carcass = radius - lug_h
    r_rim = radius * 0.56
    hw = half_width

    # 1) Tire Carcass + Sidewalls (hard-edge break at rim bead r_rim)
    p.add_lathe((0.0, 0.0, 0.0), axis, [
        (-hw * 0.78, r_rim, 0.45, radius),
        (-hw * 0.98, r_rim + (r_carcass - r_rim) * 0.35, 0.65, radius),
        (-hw * 1.02, r_rim + (r_carcass - r_rim) * 0.72, 0.82, radius),
        (-hw * 0.86, r_carcass, 0.94, radius),
    ], segs=24, uv_mode="polar", uv_rect=UV_WHL_SIDE, up_hint=up_h)

    # Crown rubber base cylinder
    p.add_lathe((0.0, 0.0, 0.0), axis, [
        (-hw * 0.86, r_carcass, 0.02),
        (-hw * 0.40, r_carcass + 0.08, 0.25),
        (+0.00,      r_carcass + 0.12, 0.50),
        (+hw * 0.40, r_carcass + 0.08, 0.75),
        (+hw * 0.86, r_carcass, 0.98),
    ], segs=24, uv_rect=UV_WHL_TREAD, up_hint=up_h)

    p.add_lathe((0.0, 0.0, 0.0), axis, [
        (+hw * 0.86, r_carcass, 0.94, radius),
        (+hw * 1.02, r_rim + (r_carcass - r_rim) * 0.72, 0.82, radius),
        (+hw * 0.98, r_rim + (r_carcass - r_rim) * 0.35, 0.65, radius),
        (+hw * 0.78, r_rim, 0.45, radius),
    ], segs=24, uv_mode="polar", uv_rect=UV_WHL_SIDE, up_hint=up_h)

    # 2) Bronze/Gunmetal Beadlock Rim (inner + deep concave outer dish + beadlock ring)
    p.add_lathe((0.0, 0.0, 0.0), axis, [
        (-hw * 0.78, 0.0, 0.0, r_rim),
        (-hw * 0.78, r_rim * 0.45, 0.45, r_rim),
        (-hw * 0.62, r_rim * 0.85, 0.85, r_rim),
        (-hw * 0.78, r_rim, 1.00, r_rim),
    ], segs=20, uv_mode="polar", uv_rect=UV_WHL_RIM, up_hint=up_h)

    p.add_lathe((0.0, 0.0, 0.0), axis, [
        (+hw * 0.78, r_rim, 1.00, r_rim),
        (+hw * 0.90, r_rim * 0.95, 0.95, r_rim),  # bronze beadlock outer ring lip
        (+hw * 0.88, r_rim * 0.80, 0.80, r_rim),
        (+hw * 0.44, r_rim * 0.74, 0.74, r_rim),  # deep dish recess
        (+hw * 0.32, r_rim * 0.34, 0.34, r_rim),
        (+hw * 0.56, r_rim * 0.28, 0.28, r_rim),
        (+hw * 0.56, 0.0, 0.0, r_rim),
    ], segs=24, uv_mode="polar", uv_rect=UV_WHL_RIM, up_hint=up_h)

    # 5 Raised Bronze/Gunmetal Spokes + 10 Beadlock Hex Bolts + Center Axle Nut
    for k in range(5):
        ang = 2.0 * math.pi * k / 5.0
        r_dir = vadd(vmul(Y_w, math.cos(ang)), vmul(Z_w, math.sin(ang)))
        sp_a = vadd(vmul(X_w, hw * 0.52), vmul(r_dir, r_rim * 0.28))
        sp_b = vadd(vmul(X_w, hw * 0.68), vmul(r_dir, r_rim * 0.78))
        p.add_tube([sp_a, sp_b], [0.68, 0.56], segs=5, uv_rect=UV_WHL_HUB)

    for k in range(10):
        ang = 2.0 * math.pi * k / 10.0
        r_dir = vadd(vmul(Y_w, math.cos(ang)), vmul(Z_w, math.sin(ang)))
        b0 = vadd(vmul(X_w, hw * 0.84), vmul(r_dir, r_rim * 0.88))
        b1 = vadd(vmul(X_w, hw * 0.96), vmul(r_dir, r_rim * 0.88))
        p.add_tube([b0, b1], [0.28, 0.26], segs=6, uv_rect=UV_WHL_HUB)

    p.add_lathe((0.0, 0.0, 0.0), axis, [
        (+hw * 0.54, 0.0, 0.0),
        (+hw * 0.54, 1.35, 0.25),
        (+hw * 0.94, 1.25, 0.80),
        (+hw * 0.94, 0.0, 1.00),
    ], segs=6, uv_rect=UV_WHL_HUB, up_hint=up_h)

    # 3) Modeled 3D Knobby Tread Lugs (24 staggered lugs in 2 rows: left/right shoulder + center)
    # Using crisp 6-quad tapered lug blocks (24 * 2 rows = 48 lugs -> 48 * 24 = 1152 verts!)
    # Staggered by half-pitch (7.5 deg) so angular pitch is 7.5 deg -> bottom clearance <= 0.026u!
    row_specs = [
        (-hw * 0.52, -hw * 0.06, 0.0),
        (+hw * 0.06, +hw * 0.52, 0.5),
    ]
    dth = 2.0 * math.pi / float(n_lugs)
    half_arc = dth * 0.24
    r_in = r_carcass - 0.15
    r_out = radius  # EXACT outer radius so tips hit Z=0.0!

    for ax0, ax1, phase in row_specs:
        ax_m0 = ax0 + 0.12 * (ax1 - ax0)
        ax_m1 = ax1 - 0.12 * (ax1 - ax0)
        for i in range(n_lugs):
            th_c = (i + phase) * dth
            t0_b, t1_b = th_c - half_arc, th_c + half_arc
            t0_t, t1_t = th_c - half_arc * 0.76, th_c + half_arc * 0.76

            def pt(ax_v, r_v, ang_v):
                return vadd(vmul(X_w, ax_v), vadd(vmul(Y_w, r_v * math.cos(ang_v)), vmul(Z_w, r_v * math.sin(ang_v))))

            b00 = pt(ax0, r_in, t0_b)
            b10 = pt(ax1, r_in, t0_b)
            b11 = pt(ax1, r_in, t1_b)
            b01 = pt(ax0, r_in, t1_b)
            t00 = pt(ax_m0, r_out, t0_t)
            t10 = pt(ax_m1, r_out, t0_t)
            t11 = pt(ax_m1, r_out, t1_t)
            t01 = pt(ax_m0, r_out, t1_t)
            add_strake_box(p, [b00, b10, b11, b01, t00, t10, t11, t01], uv_rect=UV_WHL_TREAD)

    return p


# ---------------------------------------------------------------------------
# 2. Flame Plume Dynamic Builders (Per-Frame Geometry)
# ---------------------------------------------------------------------------
def build_flame_template():
    """Builds fixed-topology flame_outer and flame_core MeshParts."""
    fo = MeshPart("flame_outer")
    fc = MeshPart("flame_core")

    # Two plumes (L/R), each built from 1 conical tube (6 rings x 8 segs) + 2 cross-fin ribbons (4 quads each)
    def init_plume(mp, uv_rect, n_rings=7, n_segs=8):
        u0, v0, u1, v1 = uv_rect
        for _side in range(2):
            base = len(mp.verts)
            cols = n_segs + 1
            for ri in range(n_rings):
                tv = v0 + (v1 - v0) * (ri / float(n_rings - 1))
                for j in range(cols):
                    mp.verts.append((0.0, 0.0, 0.0))
                    mp.norms.append((0.0, 0.0, 1.0))
                    mp.st.append((u0 + (u1 - u0) * (j / float(n_segs)), tv))
            for ri in range(n_rings - 1):
                for j in range(n_segs):
                    a = base + ri * cols + j
                    b = a + 1
                    c = a + cols
                    d = c + 1
                    mp.tris += [(a, b, c), (b, d, c)]
            # 2 cross-fin flame ribbons (two-sided)
            for _fin in range(2):
                f_base = len(mp.verts)
                for ri in range(n_rings):
                    tv = v0 + (v1 - v0) * (ri / float(n_rings - 1))
                    for k in range(2):
                        mp.verts.append((0.0, 0.0, 0.0))
                        mp.norms.append((0.0, 0.0, 1.0))
                        mp.st.append((u0 + (u1 - u0) * float(k), tv))
                for ri in range(n_rings - 1):
                    a = f_base + ri * 2
                    b = a + 1
                    c = a + 2
                    d = a + 3
                    mp.tris += [(a, b, c), (b, d, c), (a, c, b), (b, c, d)]

    init_plume(fo, UV_FLAME_OUTER, n_rings=7, n_segs=8)
    init_plume(fc, UV_FLAME_CORE, n_rings=7, n_segs=8)
    return fo, fc


def eval_flame_frame(template_part, mode, frame_local, is_core=False, chassis_pitch=0.0, chassis_dz=0.0):
    """Computes vertex positions & normals for flame_outer / flame_core on a single frame."""
    nv = len(template_part.verts)
    n_rings = 7
    n_segs = 8
    cols = n_segs + 1
    per_plume = n_rings * cols + 2 * (n_rings * 2)
    assert nv == 2 * per_plume

    vv = [(0.0, 0.0, 0.0)] * nv
    nn = [(0.0, 0.0, 1.0)] * nv

    # Hidden collapsed state (idle/fast & post-explosion)
    if mode in ("idle", "fast") or (mode == "explode" and frame_local >= 7):
        anchor = (-31.0, 0.0, 14.0) if mode in ("idle", "fast") else (-10.0, 0.0, 2.0)
        for i in range(nv):
            ang = (i % 7) * 0.9
            vv[i] = (anchor[0] + 0.02 * math.cos(ang), anchor[1] + 0.02 * math.sin(ang), anchor[2] + 0.02)
            nn[i] = (0.0, 0.0, 1.0)
        return vv, nn

    if mode == "explode":
        # Big fireball flash at frames 44..49 (frame_local 0..5), rapidly shrinking by 50
        t = frame_local
        fade = 1.0 if t <= 3 else max(0.02, 1.0 - (t - 3) / 3.5)
        length = (26.0 if is_core else 36.0) * fade
        max_r = (7.5 if is_core else 12.5) * fade
        origins = [(-18.0, +4.0, 15.0), (-22.0, -4.0, 16.0)]
        dirs = [vnorm((-0.7, +0.4, 0.55)), vnorm((-0.7, -0.4, 0.55))]
        phase = t * 1.3
    else:
        # Super speed roaring dual megaphone backfire plumes (trailing ~26..34u behind tips!)
        t = frame_local
        pulse = 0.92 + 0.12 * math.sin(t * 1.9 + (0.7 if is_core else 0.0)) + 0.06 * math.cos(t * 3.1)
        length = (24.5 if is_core else 33.5) * pulse
        max_r = (1.75 if is_core else 3.35) * (0.92 + 0.12 * math.sin(t * 2.4))
        pivot = (-30.5, 0.0, 12.0)
        origins, dirs = [], []
        for sy in (+1.0, -1.0):
            tip = (-46.5, sy * 10.5, 20.5)
            # Apply chassis pitch/bob around rear axle pivot
            q = rot_y(vsub(tip, pivot), chassis_pitch)
            origins.append((q[0] + pivot[0], q[1] + pivot[1], q[2] + pivot[2] + chassis_dz))
            d_base = vnorm((-0.946, sy * 0.074, 0.315))
            dirs.append(vnorm(rot_y(d_base, chassis_pitch)))
        phase = t * 1.5

    for pi in range(2):
        base = pi * per_plume
        orig = origins[pi]
        axis = dirs[pi]
        X, Y, Z = basis_from_axis(axis)

        # Conical plume
        for ri in range(n_rings):
            s = ri / float(n_rings - 1)
            # Expand immediately at nozzle, taper to sharp jagged flame tip
            env = math.sin(math.pi * (s ** 0.55)) * (1.0 - 0.35 * s)
            if ri == 0:
                env = 0.45
            if ri == n_rings - 1:
                env = 0.02
            wob_y = 0.6 * s * math.sin(phase + s * 6.0 + pi * 2.1)
            wob_z = 0.5 * s * math.cos(phase * 1.3 + s * 5.0 + pi * 1.4)
            center = vadd(orig, vadd(vmul(X, s * length), vadd(vmul(Y, wob_y), vmul(Z, wob_z))))
            for j in range(cols):
                th = 2.0 * math.pi * (j / float(n_segs))
                jag = 1.0 + 0.26 * math.sin(th * 3.0 + phase + s * 5.0)
                rr = max_r * env * jag
                pos = vadd(center, vadd(vmul(Y, rr * math.cos(th)), vmul(Z, rr * math.sin(th))))
                nrm = vnorm(vadd(vmul(Y, math.cos(th)), vmul(Z, math.sin(th))))
                idx = base + ri * cols + j
                vv[idx] = pos
                nn[idx] = nrm

        # 2 Cross-fin flame ribbons
        fin_base = base + n_rings * cols
        for fi in range(2):
            ang_f = (0.35 + fi * 0.5 * math.pi) + 0.25 * math.sin(phase + pi)
            f_dir = vadd(vmul(Y, math.cos(ang_f)), vmul(Z, math.sin(ang_f)))
            f_nrm = vadd(vmul(Y, -math.sin(ang_f)), vmul(Z, math.cos(ang_f)))
            for ri in range(n_rings):
                s = ri / float(n_rings - 1)
                w = max_r * 1.25 * math.sin(math.pi * (s ** 0.5)) * (1.0 + 0.2 * math.sin(phase * 1.7 + s * 7.0))
                if ri == n_rings - 1:
                    w = 0.02
                c = vadd(orig, vmul(X, s * length * 1.04))
                idx0 = fin_base + fi * (n_rings * 2) + ri * 2
                vv[idx0] = vsub(c, vmul(f_dir, w))
                vv[idx0 + 1] = vadd(c, vmul(f_dir, w))
                nn[idx0] = f_nrm
                nn[idx0 + 1] = f_nrm

    return vv, nn


# ---------------------------------------------------------------------------
# 3. Rigid-Body Transform & Ballistic Explosion Helpers
# ---------------------------------------------------------------------------
def xform_part(part, offset=(0.0, 0.0, 0.0), rx=0.0, ry=0.0, rz=0.0, pivot=(0.0, 0.0, 0.0), min_z_clamp=None):
    """Transforms a MeshPart around pivot without mutating topology."""
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
    if min_z_clamp is not None and vv:
        zmin = min(v[2] for v in vv)
        if zmin < min_z_clamp:
            lift = min_z_clamp - zmin
            vv = [(v[0], v[1], v[2] + lift) for v in vv]
    return vv, nn


def part_centroid(part):
    n = max(1, len(part.verts))
    sx = sum(v[0] for v in part.verts) / n
    sy = sum(v[1] for v in part.verts) / n
    sz = sum(v[2] for v in part.verts) / n
    return (sx, sy, sz)


def ballistic_step(t, v0, grav=140.0, bounce_z=0.5, restitution=0.52):
    """Simulates a 3D ballistic arc with ground bounce at bounce_z."""
    dt = 0.025
    steps = int(round(t / dt))
    x, y, z = 0.0, 0.0, 0.0
    vx, vy, vz = v0
    for _ in range(steps):
        x += vx * dt
        y += vy * dt
        vz -= grav * dt
        z += vz * dt
        if z < 0.0:
            z = -z * restitution
            vz = abs(vz) * restitution
            vx *= 0.85
            vy *= 0.85
    return (x, y, max(0.0, z))


# ---------------------------------------------------------------------------
# 4. Build Full 64-Frame Model, Verify Contracts, Write MD3 + Skin + Meta
# ---------------------------------------------------------------------------
def build_gokart_3(progs_dir=PROGS, meta_dir=OUT_DIR):
    print("1. Generating Go-Kart #3 ('Baja Dune Scrambler') procedural textures...", flush=True)
    tex_paths = generate_all_textures(progs_dir=progs_dir)

    print("2. Building high-detail 3D surfaces...", flush=True)
    parts = {
        "chassis_cage":  build_chassis_cage(),
        "skid_lights":   build_skid_lights(),
        "suspension":    build_suspension(),
        "seat":          build_seat(),
        "steering":      build_steering(),
        "engine_vtwin":  build_engine_vtwin(),
        "exhaust_dual":  build_exhaust_dual(),
        "wheel_fl":      build_offroad_wheel(+1, radius=10.5, half_width=4.3),
        "wheel_fr":      build_offroad_wheel(-1, radius=10.5, half_width=4.3),
        "wheel_rl":      build_offroad_wheel(+1, radius=12.0, half_width=5.4),
        "wheel_rr":      build_offroad_wheel(-1, radius=12.0, half_width=5.4),
    }
    wheel_centers = {
        "wheel_fl": (+28.0, +27.5, 10.5),
        "wheel_fr": (+28.0, -27.5, 10.5),
        "wheel_rl": (-30.5, +29.0, 12.0),
        "wheel_rr": (-30.5, -29.0, 12.0),
    }
    # Place each wheel at its resting axle center so local transforms pivot cleanly around (0,0,0) -> world
    for wname, wc in wheel_centers.items():
        wp = parts[wname]
        wp.verts = [vadd(v, wc) for v in wp.verts]

    flame_outer_tpl, flame_core_tpl = build_flame_template()

    # Ballistic explosion parameters per surface (unique 3D trajectories + tumble spins)
    explode_params = {
        "chassis_cage": ((+4.0,  -3.0, +42.0), (+18.0, -24.0, +32.0)),
        "skid_lights":  ((+56.0, +14.0, +48.0), (-65.0, +85.0, +50.0)),
        "suspension":   ((-12.0, +24.0, +38.0), (+40.0, +52.0, -70.0)),
        "seat":         ((-6.0,  -16.0, +68.0), (+95.0, -45.0, +85.0)),
        "steering":     ((+28.0, -18.0, +76.0), (-110.0, +70.0, +125.0)),
        "engine_vtwin": ((-38.0,  +8.0, +56.0), (+65.0, -90.0, -45.0)),
        "exhaust_dual": ((-52.0, -22.0, +64.0), (-85.0, +115.0, +90.0)),
        "wheel_fl":     ((+44.0, +56.0, +52.0), (+90.0, -140.0, +110.0)),
        "wheel_fr":     ((+46.0, -58.0, +48.0), (-95.0, -135.0, -105.0)),
        "wheel_rl":     ((-42.0, +62.0, +46.0), (+85.0, +130.0, -95.0)),
        "wheel_rr":     ((-44.0, -60.0, +54.0), (-80.0, +145.0, +100.0)),
    }

    frame_names = (
        [f"idle_{i:02d}" for i in range(12)]
        + [f"fast_{i:02d}" for i in range(16)]
        + [f"super_{i:02d}" for i in range(16)]
        + [f"explode_{i:02d}" for i in range(20)]
    )
    assert len(frame_names) == 64

    sprung_names = ["chassis_cage", "skid_lights", "suspension", "seat", "steering", "engine_vtwin", "exhaust_dual"]
    surf_frames = {name: [] for name in list(parts.keys()) + ["flame_outer", "flame_core"]}

    rear_pivot = (-30.5, 0.0, 12.0)

    print("3. Baking 64 animation frames (idle, fast, super+flames, explosion)...", flush=True)
    for fi in range(64):
        if fi < 12:
            # IDLE (0..11): Heavy V-twin thump & subtle suspension bob, wheels static at Z=0
            th = 2.0 * math.pi * (fi / 12.0)
            bob_z = 0.28 * math.sin(th)
            pitch = 0.35 * math.cos(th)
            eng_th = 2.0 * math.pi * ((fi * 2) / 12.0)  # 2x firing thump
            eng_dz = 0.42 * math.sin(eng_th)
            eng_rx = 1.6 * math.cos(eng_th)

            for sname in sprung_names:
                if sname in ("engine_vtwin", "exhaust_dual"):
                    vv, nn = xform_part(
                        parts[sname],
                        offset=(0.0, 0.16 * math.sin(eng_th), bob_z + eng_dz),
                        rx=eng_rx, ry=pitch, pivot=(-31.0, 0.0, 14.0),
                    )
                else:
                    vv, nn = xform_part(parts[sname], offset=(0.0, 0.0, bob_z), ry=pitch, pivot=(0.0, 0.0, 10.0))
                surf_frames[sname].append((vv, nn))

            for wname in wheel_centers:
                surf_frames[wname].append((list(parts[wname].verts), [vnorm(n) for n in parts[wname].norms]))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "idle", fi, is_core=False))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "idle", fi, is_core=True))

        elif fi < 28:
            # FAST (12..27): Wheels spin smoothly forward (2*pi = -360 deg across 16 frames), suspension chatter
            fl = fi - 12
            th = 2.0 * math.pi * (fl / 16.0)
            bob_z = 0.38 * math.sin(th * 2.0)
            pitch = 0.48 * math.cos(th * 2.0)
            roll = 0.42 * math.sin(th)
            w_deg = -360.0 * (fl / 16.0)  # negative ry rotates top toward +X!

            for sname in sprung_names:
                extra_z = 0.25 * math.sin(th * 4.0) if sname in ("engine_vtwin", "exhaust_dual") else 0.0
                vv, nn = xform_part(parts[sname], offset=(0.0, 0.0, bob_z + extra_z), rx=roll, ry=pitch, pivot=(0.0, 0.0, 10.0))
                surf_frames[sname].append((vv, nn))

            for wname, wc in wheel_centers.items():
                vv, nn = xform_part(parts[wname], ry=w_deg, pivot=wc)
                surf_frames[wname].append((vv, nn))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "fast", fl, is_core=False))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "fast", fl, is_core=True))

        elif fi < 44:
            # SUPER SPEED (28..43): Wheels spin 2x faster (-720 deg across 16 frames), chassis squats back +2.0 deg, roaring flames!
            fl = fi - 28
            th = 2.0 * math.pi * (fl / 16.0)
            pitch = +2.0 + 0.35 * math.sin(th * 2.0)  # +ry pitches nose +X UP toward +Z!
            bob_z = 0.32 * math.cos(th * 2.0)
            w_deg = -720.0 * (fl / 16.0)

            for sname in sprung_names:
                extra_z = 0.30 * math.sin(th * 4.0) if sname in ("engine_vtwin", "exhaust_dual") else 0.0
                vv, nn = xform_part(parts[sname], offset=(0.0, 0.0, bob_z + extra_z), ry=pitch, pivot=rear_pivot)
                surf_frames[sname].append((vv, nn))

            for wname, wc in wheel_centers.items():
                vv, nn = xform_part(parts[wname], ry=w_deg, pivot=wc)
                surf_frames[wname].append((vv, nn))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "super", fl, is_core=False, chassis_pitch=pitch, chassis_dz=bob_z))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "super", fl, is_core=True, chassis_pitch=pitch, chassis_dz=bob_z))

        else:
            # EXPLOSION (44..63): All 11 physical pieces fly outward with tumble & ground bounce (z >= 0.5)!
            fl = fi - 44
            t_sec = (fl / 19.0) * 1.45  # 1.45 seconds of explosive dispersal
            for sname, part in parts.items():
                v0, omega = explode_params[sname]
                disp = ballistic_step(t_sec, v0)
                piv = wheel_centers[sname] if sname in wheel_centers else part_centroid(part)
                rx = omega[0] * t_sec
                ry = omega[1] * t_sec
                rz = omega[2] * t_sec
                vv, nn = xform_part(part, offset=disp, rx=rx, ry=ry, rz=rz, pivot=piv, min_z_clamp=0.5)
                surf_frames[sname].append((vv, nn))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "explode", fl, is_core=False))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "explode", fl, is_core=True))

    # Build MD3 model dict
    md3_surfaces = []
    for sname in list(parts.keys()) + ["flame_outer", "flame_core"]:
        tpl = parts[sname] if sname in parts else (flame_outer_tpl if sname == "flame_outer" else flame_core_tpl)
        nv, nt = len(tpl.verts), len(tpl.tris)
        assert 0 < nv <= 4096, f"{sname} nv={nv} > 4096!"
        assert 0 < nt <= 8192, f"{sname} nt={nt} > 8192!"
        md3_surfaces.append(dict(
            name=sname,
            shader=SURF_SHADERS[sname],
            tris=list(tpl.tris),
            st=list(tpl.st),
            frames=surf_frames[sname],
        ))

    md3_path = os.path.join(progs_dir, "gokart_3.md3")
    md3lib.write(md3_path, dict(name="progs/gokart_3.md3", frame_names=frame_names, surfaces=md3_surfaces))

    skin_path = os.path.join(progs_dir, "gokart_3.md3_0.skin")
    with open(skin_path, "w", encoding="ascii", newline="\n") as f:
        for s in md3_surfaces:
            f.write(f"{s['name']},{s['shader']}\n")

    # Exhaust tips metadata matching actual geometry
    exhaust_tips = [
        {"x": -46.5, "y": +10.5, "z": 20.5, "dx": -0.946, "dy": +0.074, "dz": +0.315},
        {"x": -46.5, "y": -10.5, "z": 20.5, "dx": -0.946, "dy": -0.074, "dz": +0.315},
    ]

    meta = {
        "id": "kart3",
        "name": "Baja Dune Scrambler",
        "tagline": "Acid-Lime Desert Buggy-Kart with Long-Travel Coil-Overs & V-Twin",
        "palette": ["#5c6246", "#27272a", "#9a865c", "#7c8088"],
        "description": (
            "Rugged Bakersfield desert buggy-kart built around an acid-lime & matte gunmetal "
            "tubular exoskeleton, riveted brushed-steel skid plate, bull-bar with twin amber "
            "rally fog lamps, Quake 'Q' grille badge, long-travel hazard-orange coil-over shocks, "
            "knobby beadlock off-road tires, and an exposed rear V-twin firing dual swept-up chrome megaphones."
        ),
        "highlights": [
            ["Chassis", "Acid-lime & gunmetal tubular sand-rail cage, diamond floor, bull-bar & riveted skid plate"],
            ["Suspension", "Front double A-arms + 4 hazard-orange helical coil-over shocks, high desert clearance"],
            ["Tires", "4 wide knobby-treaded off-road tires (48 3D lugs each) on bronze/gunmetal beadlock rims"],
            ["Powertrain", "Finned rear V-twin, gold pleated air cone, heat-wrapped dual chrome megaphones"],
            ["Player Fit", "Open overhead cockpit (|Y|<=13 clear), seat at (-9, 0, 10), wheel at (+13, 0, 24.5)"],
        ],
        "seat_pos": {"x": -9.0, "y": 0.0, "z": 10.0},
        "steer_pos": {"x": 13.0, "y": 0.0, "z": 24.5},
        "exhaust_tips": exhaust_tips,
        "textures": tex_paths,
        "materials": MATERIALS,
    }
    meta_path = None
    if meta_dir is not None:
        os.makedirs(meta_dir, exist_ok=True)
        meta_path = os.path.join(meta_dir, "gokart_3_meta.json")
        with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)

    # -----------------------------------------------------------------------
    # 5. Self-Verification Round-Trip & Contract Checks
    # -----------------------------------------------------------------------
    print("4. Running md3lib.read() round-trip & contract verification...", flush=True)
    m = md3lib.read(md3_path)
    assert m["nframes"] == 64
    tot_v, tot_t = 0, 0
    for s in m["surfaces"]:
        nv, nt = len(s["st"]), len(s["tris"])
        tot_v += nv
        tot_t += nt
        assert nv <= 4096 and nt <= 8192
        for fi, (vv, nn) in enumerate(s["frames"]):
            for p in vv:
                assert all(math.isfinite(c) and abs(c) < 511.5 for c in p), f"OOB in {s['name']} f{fi}: {p}"
            for n in nn:
                assert all(math.isfinite(c) for c in n)
        print(f"   {s['name']:14s} | verts={nv:4d} tris={nt:4d} shader={s['shader']}")

    # Ground contact check frames 0..43 & overall dimensions on frame 0
    zmins_drive = []
    for fi in range(44):
        zmin = min(p[2] for s in m["surfaces"] for p in s["frames"][fi][0])
        zmins_drive.append(zmin)
        assert -0.1 <= zmin <= 0.1, f"Frame {fi} z_min={zmin:.4f} out of [-0.1, 0.1]"
    f0_pts = [p for s in m["surfaces"] if not s["name"].startswith("flame") for p in s["frames"][0][0]]
    xs = [p[0] for p in f0_pts]
    ys = [p[1] for p in f0_pts]
    zs = [p[2] for p in f0_pts]
    assert -48.0 <= min(xs) and max(xs) <= 50.0, f"X bounds out of [-48, 50]: {min(xs):.2f}..{max(xs):.2f}"
    assert -35.0 <= min(ys) and max(ys) <= 35.0, f"Y bounds out of [-35, 35]: {min(ys):.2f}..{max(ys):.2f}"

    # Flame collapse (0..27) and expansion (28..43)
    for fn in ("flame_outer", "flame_core"):
        fs = next(s for s in m["surfaces"] if s["name"] == fn)
        for fi in range(28):
            pts = fs["frames"][fi][0]
            span = max(max(p[k] for p in pts) - min(p[k] for p in pts) for k in range(3))
            assert span < 2.0, f"{fn} frame {fi} span={span:.3f} >= 2.0!"
        for fi in range(28, 44):
            pts = fs["frames"][fi][0]
            x_span = max(p[0] for p in pts) - min(p[0] for p in pts)
            assert x_span > 15.0, f"{fn} frame {fi} x_span={x_span:.3f} <= 15.0!"

    # Player-fit torso clearance box check (22u wide x 28u tall above seat_pos)
    sx, sy, sz = meta["seat_pos"]["x"], meta["seat_pos"]["y"], meta["seat_pos"]["z"]
    clips = []
    for s in m["surfaces"]:
        if s["name"].startswith("flame") or s["name"] == "driver":
            continue
        for p in s["frames"][0][0]:
            if (sx - 5.5 <= p[0] <= sx + 5.5) and (-11.0 <= p[1] <= 11.0) and (sz + 0.25 <= p[2] <= sz + 28.0):
                clips.append((s["name"], p))
    assert not clips, f"Player-fit torso clearance violation: {clips[:5]}"

    # Explosion separation check (frame 44 vs frame 63) & ground bounce z>=0.48
    seps = []
    for s in m["surfaces"]:
        if s["name"].startswith("flame") or s["name"] == "driver":
            continue
        p44 = s["frames"][44][0]
        p63 = s["frames"][63][0]
        c44 = tuple(sum(p[k] for p in p44) / len(p44) for k in range(3))
        c63 = tuple(sum(p[k] for p in p63) / len(p63) for k in range(3))
        seps.append((s["name"], vlen(vsub(c63, c44))))
        for fi in range(44, 64):
            zmin_e = min(p[2] for p in s["frames"][fi][0])
            assert zmin_e >= 0.45, f"Explosion {s['name']} f{fi} zmin={zmin_e:.3f} < 0.5"

    print(f"5. VERIFIED! Total: {tot_v} verts, {tot_t} tris across {len(m['surfaces'])} surfaces.")
    print(f"   Frame 0 bbox: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
    print(f"   Driving z_min (frames 0..43): [{min(zmins_drive):.4f}, {max(zmins_drive):.4f}]")
    print(f"   Min/Max explosion displacement: {min(d for _, d in seps):.1f}u .. {max(d for _, d in seps):.1f}u")
    print(f"   Wrote {md3_path}, {skin_path}, {meta_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build Go-Kart #3 MD3, skin, and textures.")
    p.add_argument("--out-dir", default=None, help="Output directory for MD3, skin, and PNGs")
    p.add_argument("--meta-dir", default=None, help="Optional directory for gokart_3_meta.json")
    args = p.parse_args()
    progs_dir = args.out_dir if args.out_dir is not None else PROGS
    meta_dir = args.meta_dir if args.meta_dir is not None else (OUT_DIR if args.out_dir is None else None)
    build_gokart_3(progs_dir=progs_dir, meta_dir=meta_dir)
