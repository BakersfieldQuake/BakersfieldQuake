"""Procedural 3D MD3 + high-res texture builder for Mega Man Go-Kart #6:
  "Mega Man Heavy Fat-Tire Rammer" (rugged heavy-caliber industrial Mega Man contraption kart).

Outputs (ONLY Go-Kart #6 owned files):
  - progs/gk6_*.png                         (7 procedural 512/1024 textures)
  - progs/gokart_6.md3                      (64-frame multi-surface MD3)
  - progs/gokart_6.md3_0.skin               (surface -> shader skin mapping)
  - source/mm_tools/out/gokart_6_meta.json  (metadata & material table)

Coordinate contract (Quake / DarkPlaces):
  +X = forward, +Y = left, +Z = up, ground = Z=0.
  Overall length X in [-47, +58], track width Y in [-36, +36].
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
    UV_HEX_ZINC,
    UV_RUBBER_CAP,
    UV_STAINLESS,
    UV_VALVE_BRASS,
)

# ---------------------------------------------------------------------------
# Shaders & Materials (progs/gk6_* namespace, no collision with mm_tank.shader)
# ---------------------------------------------------------------------------
SURF_SHADERS = {
    "chassis":     "progs/gk6_frame",
    "front_bar":   "progs/gk6_chrome",
    "t_collar":    "progs/gk6_chrome",
    "seat":        "progs/gk6_seat",
    "steering":    "progs/gk6_steer",
    "engine":      "progs/gk6_engine",
    "exhaust":     "progs/gk6_chrome",
    "wheel_fl":    "progs/gk6_wheel",
    "wheel_fr":    "progs/gk6_wheel",
    "wheel_rl":    "progs/gk6_wheel",
    "wheel_rr":    "progs/gk6_wheel",
    "flame_outer": "progs/gk6_flame",
    "flame_core":  "progs/gk6_flame",
}

MATERIALS = {
    "progs/gk6_frame":  {"metallic": 0.76, "roughness": 0.28, "spec": 0.84},
    "progs/gk6_chrome": {"metallic": 0.94, "roughness": 0.14, "spec": 0.96},
    "progs/gk6_seat":   {"metallic": 0.06, "roughness": 0.78, "spec": 0.20},
    "progs/gk6_steer":  {"metallic": 0.38, "roughness": 0.44, "spec": 0.48},
    "progs/gk6_engine": {"metallic": 0.82, "roughness": 0.24, "spec": 0.88},
    "progs/gk6_wheel":  {"metallic": 0.28, "roughness": 0.62, "spec": 0.42},
    "progs/gk6_flame":  {"metallic": 0.00, "roughness": 1.00, "spec": 0.00, "unlit": True, "additive": True},
}

# UV rects inside gk6_frame.png
UV_FRM_STAINLESS = (0.02, 0.02, 0.48, 0.48)
UV_FRM_GUNMETAL  = (0.52, 0.02, 0.98, 0.48)
UV_FRM_FLOOR     = (0.02, 0.52, 0.48, 0.98)
UV_FRM_PLATE     = (0.52, 0.52, 0.98, 0.98)

# UV rects inside gk6_seat.png
UV_SEAT_CHARCOAL = (0.02, 0.02, 0.48, 0.48)
UV_SEAT_OFFWHITE = (0.52, 0.02, 0.98, 0.48)
UV_SEAT_HARNESS  = (0.02, 0.52, 0.48, 0.98)
UV_SEAT_SHELL    = (0.52, 0.52, 0.98, 0.98)

# UV rects inside gk6_steer.png
UV_STR_GRIP      = (0.02, 0.02, 0.48, 0.48)
UV_STR_BAND      = (0.52, 0.02, 0.98, 0.48)
UV_STR_SPOKE     = (0.02, 0.52, 0.48, 0.98)
UV_STR_CAP       = (0.52, 0.52, 0.98, 0.98)

# UV rects inside gk6_engine.png
UV_ENG_BLOCK     = (0.02, 0.02, 0.48, 0.48)
UV_ENG_BRASS     = (0.52, 0.02, 0.98, 0.48)
UV_ENG_STEEL     = (0.02, 0.52, 0.48, 0.98)
UV_ENG_HAZARD    = (0.52, 0.52, 0.98, 0.98)

# UV rects inside gk6_flame.png
UV_FLAME_OUTER   = (0.02, 0.02, 0.48, 0.98)
UV_FLAME_CORE    = (0.52, 0.02, 0.98, 0.98)


# ---------------------------------------------------------------------------
# Procedural Texture Synthesis (reusing read-only mmt_wheel & mmt_chrome_bar)
# ---------------------------------------------------------------------------
def _fbm(h, w, seed=601, octaves=(4, 8, 16, 32, 64)):
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
    """Draws a crisp Quake 'Q' emblem centered at (cx, cy)."""
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=shadow_col)
    draw.ellipse((cx - r * 0.92, cy - r * 0.92, cx + r * 0.92, cy + r * 0.92), fill=rim_col)
    draw.ellipse((cx - r * 0.84, cy - r * 0.84, cx + r * 0.84, cy + r * 0.84), fill=fill_col)
    ir = r * 0.58
    draw.ellipse((cx - ir, cy - ir * 1.12, cx + ir, cy + ir * 0.88), fill=shadow_col)
    draw.polygon([
        (cx - r * 0.42, cy - r * 1.05),
        (cx + r * 0.42, cy - r * 1.05),
        (cx + r * 0.24, cy - r * 0.42),
        (cx - r * 0.24, cy - r * 0.42),
    ], fill=shadow_col)
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


def _lift_mmt_albedo(arr_u8, mult=2.12):
    """Restores sRGB contrast from Zircon-calibrated mmt_* textures while keeping rubber dark."""
    f = arr_u8.astype(np.float32) * mult
    return np.clip(np.round(f), 12, 250).astype(np.uint8)


def generate_all_textures(progs_dir=PROGS):
    os.makedirs(progs_dir, exist_ok=True)
    paths = {}
    W = H = 1024
    half = 512

    # -----------------------------------------------------------------------
    # 1. gk6_chrome.png (from read-only progs/mmt_chrome_bar.png, lifted for PBR/viewer)
    # -----------------------------------------------------------------------
    src_chrome = os.path.join(progs_dir, "mmt_chrome_bar.png")
    src_wheel = os.path.join(progs_dir, "mmt_wheel.png")
    if os.path.isfile(src_chrome) and os.path.isfile(src_wheel):
        im_mc = Image.open(src_chrome).convert("RGB")
        im_mw = Image.open(src_wheel).convert("RGB")
    else:
        with tempfile.TemporaryDirectory() as tmp_mmt:
            p_wheel, _ = tank_tex_gen.build_wheel_textures(tmp_mmt)
            p_chrome, _ = tank_tex_gen.build_chrome_bar_textures(tmp_mmt)
            im_mc = Image.open(p_chrome).convert("RGB")
            im_mc.load()
            im_mw = Image.open(p_wheel).convert("RGB")
            im_mw.load()
    arr_mc = _lift_mmt_albedo(np.asarray(im_mc), mult=2.15)
    # Keep Q3 rubber cap dark matte charcoal
    arr_mc[half:, :half] = np.clip(np.asarray(im_mc)[half:, :half].astype(np.float32) * 1.25, 16, 78).astype(np.uint8)
    p_chr = os.path.join(progs_dir, "gk6_chrome.png")
    Image.fromarray(arr_mc, mode="RGB").save(p_chr, "PNG", optimize=True)
    paths["progs/gk6_chrome"] = "progs/gk6_chrome.png"

    # -----------------------------------------------------------------------
    # 2. gk6_wheel.png (left 75% = mmt_wheel.png, right 25% = mmt_chrome_bar.png Q2+Q4)
    # -----------------------------------------------------------------------
    arr_mw = np.asarray(im_mw).astype(np.float32)
    # Lift rim quadrants (bottom half) to crisp off-white steel, keep tire tread/sidewall rich dark rubber
    lifted_mw = np.empty_like(arr_mw)
    lifted_mw[:half, :] = np.clip(arr_mw[:half, :] * 1.38, 16, 118)
    lifted_mw[half:, :] = np.clip(arr_mw[half:, :] * 2.25, 20, 242)
    im_mw_l = Image.fromarray(lifted_mw.astype(np.uint8), mode="RGB").resize((768, 1024), Image.Resampling.LANCZOS)

    # Right half of mmt_chrome_bar.png (contains UV_STAINLESS, UV_HEX_ZINC, UV_COTTER_YEL, UV_VALVE_BLK, UV_VALVE_BRASS)
    im_hw_r = Image.fromarray(arr_mc[:, half:], mode="RGB").resize((256, 1024), Image.Resampling.LANCZOS)
    im_wh = Image.new("RGB", (1024, 1024))
    im_wh.paste(im_mw_l, (0, 0))
    im_wh.paste(im_hw_r, (768, 0))
    p_wh = os.path.join(progs_dir, "gk6_wheel.png")
    im_wh.save(p_wh, "PNG", optimize=True)
    paths["progs/gk6_wheel"] = "progs/gk6_wheel.png"

    # -----------------------------------------------------------------------
    # 3. gk6_frame.png (Brushed Stainless Cage, Dark Gunmetal Gussets, Stainless Floor, MM-06 Plate)
    # -----------------------------------------------------------------------
    nf = _fbm(H, W, seed=602)
    arr = np.zeros((H, W, 3), dtype=np.float32)
    u = np.linspace(0.0, 2.0 * math.pi, half, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, half, dtype=np.float32)[:, None]

    # Q1: Brushed Stainless Steel Tubing + TIG Weld Heat Tint
    st = 0.68 + 0.18 * np.cos(u - 0.7) + 0.09 * np.cos(2.0 * u) + 0.04 * nf[:half, :half] + 0.02 * np.sin(v * 340.0)
    weld = 1.0 - 0.22 * np.exp(-((v - 0.05) ** 2) / 0.001) - 0.22 * np.exp(-((v - 0.95) ** 2) / 0.001)
    straw = np.exp(-((v - 0.09) ** 2) / 0.002) + np.exp(-((v - 0.91) ** 2) / 0.002)
    arr[:half, :half, 0] = np.clip(st * weld * 212.0 + straw * 26.0, 28, 248)
    arr[:half, :half, 1] = np.clip(st * weld * 216.0 + straw * 10.0, 30, 248)
    arr[:half, :half, 2] = np.clip(st * weld * 224.0 - straw * 16.0, 34, 252)

    # Q2: Heavy Industrial Gunmetal Gusset Steel
    gun = 0.85 + 0.12 * np.cos(u - 0.5) + 0.08 * nf[:half, half:] + 0.02 * np.sin(v * 260.0)
    arr[:half, half:, 0] = np.clip(62.0 * gun, 22, 112)
    arr[:half, half:, 1] = np.clip(66.0 * gun, 24, 118)
    arr[:half, half:, 2] = np.clip(74.0 * gun, 28, 128)

    # Q3: Brushed Stainless Anti-Slip Floorpan w/ Diamond Lugs & Hex Rivets
    yy, xx = np.mgrid[0:half, 0:half].astype(np.float32)
    cell = 30.0
    gx = (xx % cell) / cell - 0.5
    gy = (yy % cell) / cell - 0.5
    alt = ((np.floor(xx / cell) + np.floor(yy / cell)) % 2) == 0
    rx = np.where(alt, (gx + gy) * 0.707, (gx - gy) * 0.707)
    ry = np.where(alt, (-gx + gy) * 0.707, (gx + gy) * 0.707)
    lug = np.exp(-((rx / 0.27) ** 4 + (ry / 0.09) ** 4))
    brush = 0.035 * np.sin(yy * 1.4) + 0.05 * nf[half:, :half]
    fp = 128.0 + 68.0 * lug + 24.0 * brush
    arr[half:, :half, 0] = np.clip(fp * 0.96, 40, 232)
    arr[half:, :half, 1] = np.clip(fp * 0.99, 42, 236)
    arr[half:, :half, 2] = np.clip(fp * 1.04, 46, 242)

    # Q4: Industrial Mega Man "MM-06" Hazard Nameplate
    im_fr = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
    im_q4 = Image.new("RGB", (half, half), (34, 36, 40))
    dr_q4 = ImageDraw.Draw(im_q4)
    for k in range(-2, 10):
        x0 = k * 68
        dr_q4.polygon([(x0, 10), (x0 + 34, 10), (x0 - 40, 96), (x0 - 74, 96)], fill=(238, 192, 32))
    dr_q4.rectangle((18, 114, 494, 494), fill=(26, 28, 32), outline=(210, 216, 224), width=8)
    dr_q4.text((46, 146), "MEGA-RAM", font=_font(76), fill=(232, 236, 242))
    dr_q4.text((130, 250), "06", font=_font(174), fill=(242, 196, 36))
    _draw_quake_q(dr_q4, 422, 365, 48, (238, 188, 36), (252, 224, 120), (22, 24, 28))
    im_fr.paste(im_q4, (half, half))
    p_fr = os.path.join(progs_dir, "gk6_frame.png")
    im_fr.save(p_fr, "PNG", optimize=True)
    paths["progs/gk6_frame"] = "progs/gk6_frame.png"

    # -----------------------------------------------------------------------
    # 4. gk6_seat.png (Charcoal Ribbed Vinyl, Off-White Bolsters, Yellow/Black Harness, Shell)
    # -----------------------------------------------------------------------
    nf4 = _fbm(H, W, seed=603)
    arr4 = np.zeros((H, W, 3), dtype=np.float32)
    yy4, xx4 = np.mgrid[0:half, 0:half].astype(np.float32)
    pleat = 0.5 + 0.5 * np.cos(xx4 * 0.24)
    grain4 = 6.0 * nf4[:half, :half]
    # Q1: Industrial charcoal stitched bolster cushion
    ch_v = 44.0 + 18.0 * pleat + grain4
    arr4[:half, :half, 0] = np.clip(ch_v * 0.96, 18, 92)
    arr4[:half, :half, 1] = np.clip(ch_v * 0.98, 18, 95)
    arr4[:half, :half, 2] = np.clip(ch_v * 1.04, 22, 102)
    # Q2: Off-white industrial vinyl center insert (matching wheel rim tone)
    ow_v = 204.0 + 22.0 * pleat + 7.0 * nf4[:half, half:]
    arr4[:half, half:, 0] = np.clip(ow_v * 0.99, 130, 242)
    arr4[:half, half:, 1] = np.clip(ow_v * 0.98, 128, 240)
    arr4[:half, half:, 2] = np.clip(ow_v * 0.94, 120, 232)
    # Q3: Yellow-stripe industrial harness webbing
    rib_h = 0.82 + 0.18 * np.sin(yy4 * 0.9)
    stripe_m = (np.abs(xx4 - 256.0) < 42.0).astype(np.float32)
    arr4[half:, :half, 0] = np.clip((38.0 + 196.0 * stripe_m) * rib_h, 16, 246)
    arr4[half:, :half, 1] = np.clip((40.0 + 152.0 * stripe_m) * rib_h, 16, 210)
    arr4[half:, :half, 2] = np.clip((44.0 - 12.0 * stripe_m) * rib_h, 16, 80)
    # Q4: Stamped gunmetal seat backplate
    sh_v = 56.0 + 10.0 * nf4[half:, half:]
    arr4[half:, half:, 0] = np.clip(sh_v * 0.95, 22, 100)
    arr4[half:, half:, 1] = np.clip(sh_v * 0.98, 24, 104)
    arr4[half:, half:, 2] = np.clip(sh_v * 1.05, 26, 112)
    p_st = os.path.join(progs_dir, "gk6_seat.png")
    _save_png(arr4, p_st)
    paths["progs/gk6_seat"] = "progs/gk6_seat.png"

    # -----------------------------------------------------------------------
    # 5. gk6_steer.png (Knurled Rubber Grip, Yellow Center Band, Steel Spokes, Horn Cap)
    # -----------------------------------------------------------------------
    nf5 = _fbm(H, W, seed=604)
    arr5 = np.zeros((H, W, 3), dtype=np.float32)
    knurl = 0.5 + 0.5 * np.sin(xx4 * 0.7) * np.sin(yy4 * 0.7)
    arr5[:half, :half] = np.clip((34.0 + 14.0 * knurl + 4.0 * nf5[:half, :half])[..., None], 16, 78)
    arr5[:half, half:, 0] = np.clip(242.0 + 10.0 * nf5[:half, half:], 180, 252)
    arr5[:half, half:, 1] = np.clip(196.0 + 10.0 * nf5[:half, half:], 140, 220)
    arr5[:half, half:, 2] = np.clip(32.0 + 6.0 * nf5[:half, half:], 16, 70)
    sp_v = 178.0 + 20.0 * np.cos(u - 0.5) + 12.0 * nf5[half:, :half]
    arr5[half:, :half, 0] = np.clip(sp_v * 0.96, 60, 232)
    arr5[half:, :half, 1] = np.clip(sp_v * 0.99, 64, 236)
    arr5[half:, :half, 2] = np.clip(sp_v * 1.04, 70, 244)
    im_str = Image.fromarray(np.clip(arr5, 0, 255).astype(np.uint8), mode="RGB")
    im_cap = Image.new("RGB", (half, half), (46, 50, 56))
    dr_cap = ImageDraw.Draw(im_cap)
    dr_cap.ellipse((24, 24, 488, 488), fill=(36, 38, 44), outline=(210, 214, 222), width=14)
    _draw_quake_q(dr_cap, 256, 256, 128, (238, 192, 36), (252, 226, 125), (34, 36, 42))
    im_str.paste(im_cap, (half, half))
    p_str = os.path.join(progs_dir, "gk6_steer.png")
    im_str.save(p_str, "PNG", optimize=True)
    paths["progs/gk6_steer"] = "progs/gk6_steer.png"

    # -----------------------------------------------------------------------
    # 6. gk6_engine.png (Cast Block, Machined Brass, Stainless Steel, Hazard Tank)
    # -----------------------------------------------------------------------
    nf6 = _fbm(H, W, seed=605)
    arr6 = np.zeros((H, W, 3), dtype=np.float32)
    # Q1: Finned cast-aluminum & charcoal engine block
    fin_sh = 0.65 + 0.35 * np.sin(v * 64.0)
    blk = (128.0 + 34.0 * np.cos(u - 0.6)) * fin_sh + 10.0 * nf6[:half, :half]
    arr6[:half, :half, 0] = np.clip(blk * 0.96, 36, 210)
    arr6[:half, :half, 1] = np.clip(blk * 0.99, 38, 215)
    arr6[:half, :half, 2] = np.clip(blk * 1.04, 42, 222)
    # Q2: Machined Brass Valve Covers & Fittings
    brs = 0.78 + 0.20 * np.cos(u - 0.5) + 0.08 * np.sin(v * 180.0) + 0.05 * nf6[:half, half:]
    arr6[:half, half:, 0] = np.clip(228.0 * brs, 80, 250)
    arr6[:half, half:, 1] = np.clip(182.0 * brs, 60, 218)
    arr6[:half, half:, 2] = np.clip(72.0 * brs, 24, 120)
    # Q3: Brushed Stainless Crankcase Plates
    stl = 0.74 + 0.18 * np.cos(u - 0.7) + 0.05 * nf6[half:, :half]
    arr6[half:, :half, 0] = np.clip(208.0 * stl, 65, 240)
    arr6[half:, :half, 1] = np.clip(214.0 * stl, 68, 244)
    arr6[half:, :half, 2] = np.clip(224.0 * stl, 72, 250)
    # Q4: Industrial yellow/charcoal hazard fuel cell
    im_eng = Image.fromarray(np.clip(arr6, 0, 255).astype(np.uint8), mode="RGB")
    im_hz = Image.new("RGB", (half, half), (42, 44, 48))
    dr_hz = ImageDraw.Draw(im_hz)
    for k in range(-2, 10):
        x0 = k * 74
        dr_hz.polygon([(x0, 24), (x0 + 36, 24), (x0 - 48, 124), (x0 - 84, 124)], fill=(238, 188, 32))
    dr_hz.rectangle((28, 152, 484, 484), fill=(52, 54, 60), outline=(228, 182, 72), width=10)
    dr_hz.text((78, 220), "HEAVY", font=_font(104), fill=(236, 238, 244))
    dr_hz.text((70, 336), "FUEL", font=_font(118), fill=(240, 192, 36))
    im_eng.paste(im_hz, (half, half))
    p_eng = os.path.join(progs_dir, "gk6_engine.png")
    im_eng.save(p_eng, "PNG", optimize=True)
    paths["progs/gk6_engine"] = "progs/gk6_engine.png"

    # -----------------------------------------------------------------------
    # 7. gk6_flame.png (512x512 RGBA fiery orange-gold outer + white-gold core)
    # -----------------------------------------------------------------------
    FW = FH = 512
    nf7 = _fbm(FH, FW, seed=606, octaves=(4, 8, 16, 32))
    arr7 = np.zeros((FH, FW, 4), dtype=np.float32)
    yy7, xx7 = np.mgrid[0:FH, 0:FW].astype(np.float32)

    u_o = xx7[:, :256] / 255.0
    v_o = yy7[:, :256] / 511.0
    edge_o = np.maximum(0.0, np.sin(math.pi * u_o)) ** 0.72
    streaks_o = 0.78 + 0.22 * np.sin(u_o * 24.0 + v_o * 11.0 + nf7[:, :256] * 4.2)
    axial_o = np.clip((1.0 - v_o) ** 0.62 * (1.0 - np.exp(-v_o * 18.0)), 0.0, 1.0)
    int_o = np.clip(edge_o * streaks_o * axial_o * 1.28, 0.0, 1.0)
    arr7[:, :256, 0] = 255.0 * (int_o ** 0.50)
    arr7[:, :256, 1] = 198.0 * (int_o ** 1.05) * (1.0 - 0.50 * v_o)
    arr7[:, :256, 2] = 52.0 * (int_o ** 2.10) * np.exp(-v_o * 3.0)
    arr7[:, :256, 3] = 255.0 * int_o

    u_c = (xx7[:, 256:] - 256.0) / 255.0
    v_c = yy7[:, 256:] / 511.0
    edge_c = np.maximum(0.0, np.sin(math.pi * u_c)) ** 0.90
    diamonds = 0.74 + 0.36 * (np.cos(v_c * 24.0) ** 2)
    axial_c = np.clip((1.0 - v_c) ** 0.82 * (1.0 - np.exp(-v_c * 22.0)), 0.0, 1.0)
    int_c = np.clip(edge_c * diamonds * axial_c * 1.35, 0.0, 1.0)
    arr7[:, 256:, 0] = 255.0 * (int_c ** 0.42)
    arr7[:, 256:, 1] = 242.0 * (int_c ** 0.62)
    arr7[:, 256:, 2] = 165.0 * (int_c ** 1.15) * (1.0 - 0.45 * v_c)
    arr7[:, 256:, 3] = 255.0 * int_c

    p_fl = os.path.join(progs_dir, "gk6_flame.png")
    _save_png(arr7, p_fl, mode="RGBA")
    paths["progs/gk6_flame"] = "progs/gk6_flame.png"
    return paths


# ---------------------------------------------------------------------------
# Geometry Helpers
# ---------------------------------------------------------------------------
def add_rounded_tube_chain(part, waypoints, radius, segs=8, uv_rect=UV_FRM_STAINLESS, bevel_r=1.8):
    if len(waypoints) <= 2:
        part.add_tube(waypoints, [radius] * len(waypoints), segs=segs, uv_rect=uv_rect)
        return
    pts = [waypoints[0]]
    for i in range(1, len(waypoints) - 1):
        p_prev, p_cur, p_next = waypoints[i - 1], waypoints[i], waypoints[i + 1]
        d1, d2 = vsub(p_cur, p_prev), vsub(p_next, p_cur)
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


def add_strake_box(part, pts8, uv_rect, side_uv=None, top_uv=None):
    b00, b10, b11, b01, t00, t10, t11, t01 = pts8
    u0, v0, u1, v1 = uv_rect
    su = side_uv if side_uv else uv_rect
    tu = top_uv if top_uv else uv_rect
    part.add_quad(b00, b01, b11, b10, (u0, v0), (u0, v1), (u1, v1), (u1, v0))
    part.add_quad(t00, t10, t11, t01, (tu[0], tu[1]), (tu[2], tu[1]), (tu[2], tu[3]), (tu[0], tu[3]))
    part.add_quad(b00, b10, t10, t00, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))
    part.add_quad(b10, b11, t11, t10, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))
    part.add_quad(b11, b01, t01, t11, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))
    part.add_quad(b01, b00, t00, t01, (su[0], su[3]), (su[2], su[3]), (su[2], su[1]), (su[0], su[1]))


# ---------------------------------------------------------------------------
# 1. Surface Builders
# ---------------------------------------------------------------------------
def build_chassis():
    """Double-decker stainless tubular cage rails (strictly outside |Y|>=13.5, rear roll bar X<=-18),
    brushed stainless floorpan, footwell pedals, front & rear cross-axles + heavy axle gussets.
    """
    p = MeshPart("chassis")

    # 1) Double-decker stainless steel tubular cage rails (L/R)
    for sy in (+1.0, -1.0):
        # Lower main heavy rail (|Y| >= 14.2 along cockpit)
        add_rounded_tube_chain(p, [
            (-42.0, sy * 12.2, 12.5),
            (-30.0, sy * 14.8, 7.8),
            (-18.0, sy * 15.2, 6.2),
            (+22.0, sy * 15.2, 6.2),
            (+28.5, sy * 14.4, 10.8),
            (+34.0, sy * 11.5, 10.8),
        ], 1.42, segs=8, uv_rect=UV_FRM_STAINLESS)

        # Upper decker stainless cage rail (|Y| >= 14.2, ~10u above lower rail)
        add_rounded_tube_chain(p, [
            (-19.5, sy * 15.6, 16.5),
            (+14.0, sy * 15.6, 16.5),
            (+24.5, sy * 14.4, 16.5),
            (+33.5, sy * 11.5, 13.8),
        ], 1.35, segs=8, uv_rect=UV_FRM_STAINLESS)

        # Vertical & diagonal cage truss rungs between lower & upper rails
        for rx_b, rx_t in [(-18.5, -19.5), (-4.0, -4.0), (+9.5, +9.5), (+21.5, +21.5), (+28.5, +24.5)]:
            p.add_tube([(rx_b, sy * 15.2, 6.2), (rx_t, sy * 15.6, 16.5)], [1.10, 1.10], segs=7, uv_rect=UV_FRM_STAINLESS)
        p.add_tube([(-18.5, sy * 15.2, 6.2), (-4.0, sy * 15.6, 16.5)], [0.95, 0.95], segs=7, uv_rect=UV_FRM_STAINLESS)
        p.add_tube([(+9.5, sy * 15.2, 6.2), (+21.5, sy * 15.6, 16.5)], [0.95, 0.95], segs=7, uv_rect=UV_FRM_STAINLESS)

        # Forward cowling rail connecting upper rail to steering dash arch (ahead of knees)
        add_rounded_tube_chain(p, [
            (+21.5, sy * 15.0, 16.5),
            (+20.5, sy * 10.5, 22.8),
        ], 1.15, segs=8, uv_rect=UV_FRM_STAINLESS)

        # Heavy gunmetal rear axle gussets + bearing carrier blocks tying frame to rear axle (X=-30.0, Z=12.5)
        add_strake_box(p, [
            (-33.5, sy * 12.8, 7.6), (-26.5, sy * 12.8, 7.6), (-26.5, sy * 16.2, 7.6), (-33.5, sy * 16.2, 7.6),
            (-32.8, sy * 12.8, 15.6), (-27.2, sy * 12.8, 15.6), (-27.2, sy * 16.2, 15.6), (-32.8, sy * 16.2, 15.6),
        ], uv_rect=UV_FRM_GUNMETAL)
        p.add_tube([(-19.5, sy * 15.4, 16.5), (-30.0, sy * 15.0, 12.5)], [1.15, 1.15], segs=7, uv_rect=UV_FRM_STAINLESS)
        p.add_tube([(-30.0, sy * 15.0, 12.5), (-42.0, sy * 12.2, 12.5)], [1.15, 1.15], segs=7, uv_rect=UV_FRM_STAINLESS)

        # Front axle gussets tying frame rails into front cross-axle (X=+26.5, Z=11.0)
        add_strake_box(p, [
            (+24.2, sy * 13.0, 7.8), (+28.8, sy * 13.0, 7.8), (+28.8, sy * 16.2, 7.8), (+24.2, sy * 16.2, 7.8),
            (+24.6, sy * 13.0, 15.8), (+28.4, sy * 13.0, 15.8), (+28.4, sy * 16.2, 15.8), (+24.6, sy * 16.2, 15.8),
        ], uv_rect=UV_FRM_GUNMETAL)

    # Dash crossbar at X=+20.5, Z=22.8 (cleanly ahead of driver knees & clear of torso box)
    p.add_tube([(+20.5, -10.8, 22.8), (+20.5, +10.8, 22.8)], [1.18, 1.18], segs=8, uv_rect=UV_FRM_STAINLESS)

    # 2) Rear Roll-Bar Hoop (strictly behind X <= -18.5 so overhead & torso box stay 100% open!)
    add_rounded_tube_chain(p, [
        (-19.5, -15.6, 16.5),
        (-21.2, -14.8, 27.2),
        (-23.2, -11.4, 35.6),
        (-23.8,   0.0, 36.8),
        (-23.2, +11.4, 35.6),
        (-21.2, +14.8, 27.2),
        (-19.5, +15.6, 16.5),
    ], 1.48, segs=8, uv_rect=UV_FRM_STAINLESS, bevel_r=2.2)

    # Rear roll-bar K-braces & rear engine guard hoop
    for sy in (+1.0, -1.0):
        add_rounded_tube_chain(p, [
            (-23.2, sy * 11.4, 35.2),
            (-34.5, sy * 12.5, 25.0),
            (-42.5, sy * 12.2, 15.5),
            (-42.0, sy * 12.2, 12.5),
        ], 1.22, segs=8, uv_rect=UV_FRM_STAINLESS)
    p.add_tube([(-42.0, -12.2, 12.5), (-42.0, +12.2, 12.5)], [1.28, 1.28], segs=8, uv_rect=UV_FRM_STAINLESS)
    p.add_tube([(-42.5, -12.2, 15.5), (-42.5, +12.2, 15.5)], [1.15, 1.15], segs=8, uv_rect=UV_FRM_GUNMETAL)

    # Industrial "MEGA-RAM 06" roll-bar plate
    p.add_chamfer_box(-24.8, -22.4, -8.5, +8.5, 33.2, 36.4, ch=0.25, uv_rect=UV_FRM_PLATE, top_uv=UV_FRM_PLATE)

    # 3) Cross-members, Brushed Stainless Floorpan, & Pedals
    for cx in (-39.0, -25.0, -16.5, -3.5, +9.5, +22.0, +33.5):
        wy = 14.8 if -20.0 <= cx <= +24.0 else 11.5
        cz = 5.4 if -20.0 <= cx <= +24.0 else 10.6
        p.add_tube([(cx, -wy, cz), (cx, +wy, cz)], [1.05, 1.05], segs=7, uv_rect=UV_FRM_GUNMETAL)

    # Brushed stainless floorpan (X in [-18.5, +26.5], Y in [-13.8, +13.8], Z = 4.6..5.4)
    p.add_chamfer_box(-18.5, +26.5, -13.8, +13.8, 4.6, 5.4, ch=0.18, uv_rect=UV_FRM_GUNMETAL, top_uv=UV_FRM_FLOOR)

    # Footwell pedals (placed cleanly flanking the central silver bar at |Y| = 6.8)
    for sy in (+1.0, -1.0):
        p.add_tube([(+25.0, sy * 6.8, 5.5), (+26.5, sy * 6.8, 10.8)], [0.45, 0.45], segs=6, uv_rect=UV_FRM_GUNMETAL)
        p.add_chamfer_box(+25.2, +26.6, sy * 6.8 - 1.7, sy * 6.8 + 1.7, 7.2, 11.2, ch=0.15, uv_rect=UV_FRM_FLOOR)

    # 4) Heavy Solid Front Cross-Axle (X=+26.5, Z=11.0) & Rear Solid Cross-Axle (X=-30.0, Z=12.5)
    p.add_lathe((+26.5, 0.0, 11.0), (0.0, 1.0, 0.0), [
        (-24.0, 0.0, 0.02),
        (-24.0, 2.05, 0.05),
        (+24.0, 2.05, 0.95),
        (+24.0, 0.0, 0.98),
    ], segs=18, uv_rect=UV_FRM_STAINLESS)
    p.add_lathe((-30.0, 0.0, 12.5), (0.0, 1.0, 0.0), [
        (-25.5, 0.0, 0.02),
        (-25.5, 2.25, 0.05),
        (+25.5, 2.25, 0.95),
        (+25.5, 0.0, 0.98),
    ], segs=18, uv_rect=UV_FRM_STAINLESS)

    # Rear axle center brake rotor & heavy sprocket disc
    p.add_lathe((-30.0, -3.2, 12.5), (0.0, 1.0, 0.0), [
        (0.0, 2.25, 0.0), (0.0, 5.2, 0.5), (0.65, 5.2, 0.7), (0.65, 2.25, 1.0),
    ], segs=16, uv_rect=UV_FRM_GUNMETAL)
    p.add_lathe((-30.0, +3.2, 12.5), (0.0, 1.0, 0.0), [
        (0.0, 2.25, 0.0), (0.0, 5.8, 0.5), (0.65, 5.8, 0.7), (0.65, 2.25, 1.0),
    ], segs=16, uv_rect=UV_FRM_STAINLESS)

    return p


def build_front_bar():
    """Colossal mirror-chrome bullet-nosed silver torpedo bar (R~3.6u, X~+7..+58)
    with ribbed black rubber rear cap at X~+7.
    """
    p = MeshPart("front_bar")
    bar_center = (0.0, 0.0, 11.0)

    # 1) Ribbed Matte-Black Rubber Rear Cap (X = +6.8 .. +12.5)
    p.add_lathe(bar_center, (1.0, 0.0, 0.0), [
        (+6.8,  0.00, 0.02),
        (+6.8,  3.15, 0.12),
        (+6.8,  3.15, 0.12),
        (+7.3,  3.85, 0.22),
        (+8.8,  3.85, 0.42),
        (+9.1,  3.58, 0.50),
        (+10.3, 3.58, 0.68),
        (+10.6, 3.85, 0.76),
        (+12.3, 3.85, 0.94),
        (+12.3, 3.85, 0.94),
        (+12.5, 3.55, 0.98),
    ], segs=28, uv_rect=UV_RUBBER_CAP)

    # 2) Mirror-Chrome Heavy-Caliber Torpedo Bar + Ogive Bullet Nose (X = +12.5 .. +58.0)
    prof = [
        (+12.5, 3.55, 0.02),
        (+21.5, 3.55, 0.22),
        (+24.2, 3.75, 0.28),
        (+26.5, 4.10, 0.34),
        (+28.8, 3.75, 0.40),
        (+31.5, 3.55, 0.46),
        (+43.8, 3.55, 0.72),
        (+44.2, 3.38, 0.74),
        (+44.6, 3.55, 0.76),
    ]
    for k in range(1, 11):
        t = k / 10.0
        xn = 44.6 + 13.4 * t
        rn = 3.55 * (math.cos(t * math.pi * 0.5) ** 0.76) if k < 10 else 0.0
        prof.append((xn, rn, 0.76 + 0.22 * t))
    p.add_lathe(bar_center, (1.0, 0.0, 0.0), prof, segs=30, uv_rect=UV_CHROME_BAR)
    return p


def build_t_collar():
    """Beefy TIG-welded stainless T-collar + twin retaining rings + twin diagonal stainless stabilizer struts
    clamping onto the front cross-axle (X=+26.5, Z=11.0).
    """
    p = MeshPart("t_collar")
    cx, cz = 26.5, 11.0

    # 1) Longitudinal T-Collar Sleeve clamping the Silver Bar (X = +20.8 .. +32.2)
    p.add_lathe((0.0, 0.0, cz), (1.0, 0.0, 0.0), [
        (+20.8, 3.50, 0.96),
        (+20.8, 4.65, 0.90),
        (+20.8, 4.65, 0.90),
        (+23.5, 4.85, 0.78),
        (+26.5, 5.15, 0.65),
        (+29.5, 4.85, 0.78),
        (+32.2, 4.65, 0.90),
        (+32.2, 4.65, 0.90),
        (+32.2, 3.50, 0.96),
    ], segs=22, uv_rect=UV_STAINLESS)

    # 2) Transverse T-Junction Sleeve wrapping the Front Cross-Axle (Y = -9.2 .. +9.2)
    p.add_lathe((cx, 0.0, cz), (0.0, 1.0, 0.0), [
        (-9.2, 2.02, 0.96),
        (-9.2, 3.95, 0.90),
        (-9.2, 3.95, 0.90),
        (-5.2, 4.55, 0.80),
        (0.0,  5.10, 0.72),
        (+5.2, 4.55, 0.80),
        (+9.2, 3.95, 0.90),
        (+9.2, 3.95, 0.90),
        (+9.2, 2.02, 0.96),
    ], segs=20, uv_rect=UV_STAINLESS)

    # 3) Forward Clamp Band around Silver Bar (X = +39.2 .. +42.2)
    p.add_lathe((0.0, 0.0, cz), (1.0, 0.0, 0.0), [
        (+39.2, 3.52, 0.92),
        (+39.2, 4.35, 0.86),
        (+39.2, 4.35, 0.86),
        (+42.2, 4.35, 0.14),
        (+42.2, 4.35, 0.14),
        (+42.2, 3.52, 0.08),
    ], segs=20, uv_rect=UV_STAINLESS)

    # 4) Twin Zinc Retaining Collars on Front Cross-Axle + Twin Diagonal Stainless Stabilizer Struts
    for sgn in (-1.0, +1.0):
        p.add_lathe((cx, sgn * 13.5, cz), (0.0, sgn, 0.0), [
            (-1.6, 2.02, 0.08),
            (-1.6, 3.65, 0.16),
            (-1.6, 3.65, 0.16),
            (+1.6, 3.65, 0.84),
            (+1.6, 3.65, 0.84),
            (+1.6, 2.02, 0.92),
        ], segs=16, uv_rect=UV_HEX_ZINC)

        # Diagonal stainless stabilizer strut from axle collar forward to bar clamp band
        p.add_tube([(cx, sgn * 13.5, cz), (+40.7, sgn * 3.6, cz)], [1.05, 0.95], segs=8, uv_rect=UV_STAINLESS)

        # Twin zinc pinch bolts on top of T-collar
        for bx in (23.2, 29.8):
            p.add_lathe((bx, sgn * 2.6, cz + 4.4), (0.0, 0.0, 1.0), [
                (0.0, 0.72, 0.1), (1.05, 0.72, 0.85), (1.05, 0.0, 0.98),
            ], segs=6, uv_rect=UV_HEX_ZINC)

    return p


def build_seat():
    """Industrial charcoal & off-white bolstered bucket seat.
    Respects player-fit clearance:
      - Seat pan top at Z=10.0
      - Side bolsters strictly at |Y| >= 11.4
      - Backrest strictly behind X <= -16.5
    """
    p = MeshPart("seat")

    # Seat pan cushion (top at Z=10.0)
    p.add_loft([
        (-16.5, 0.0, 11.2, 8.2, 1.75, 0.45),
        (-9.0,  0.0, 11.2, 8.2, 1.75, 0.45),
        (-2.2,  0.0, 11.2, 8.3, 1.65, 0.45),
        (+0.5,  0.0, 10.9, 8.8, 1.60, 0.55),
    ], uv_rect=UV_SEAT_CHARCOAL, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_OFFWHITE)

    # Charcoal side hip bolsters (strictly outside |Y| < 11.0!)
    for sy in (+1.0, -1.0):
        p.add_loft([
            (-16.8, sy * 12.6, 1.25, 11.8, 3.8, 0.45),
            (-9.0,  sy * 12.6, 1.25, 11.4, 3.2, 0.45),
            (-1.2,  sy * 12.5, 1.20, 10.6, 2.2, 0.45),
        ], uv_rect=UV_SEAT_CHARCOAL, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_CHARCOAL)

    # Sloped industrial backrest (front face at X <= -16.6)
    for x_f, x_b, hw, z0, z1 in [
        (-16.6, -19.2, 10.4,  9.2, 14.5),
        (-17.8, -20.4, 10.5, 14.5, 20.5),
        (-19.2, -21.8, 10.3, 20.5, 26.8),
        (-20.4, -22.8,  8.5, 26.8, 31.2),
    ]:
        p.add_chamfer_box(x_b, x_f, -hw, +hw, z0, z1, ch=0.4, uv_rect=UV_SEAT_OFFWHITE, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_SHELL)

    # Backrest shoulder bolsters (|Y| = 11.4..13.8)
    for sy in (+1.0, -1.0):
        add_strake_box(p, [
            (-18.8, sy * 11.4, 13.0), (-15.8, sy * 11.4, 13.0), (-15.8, sy * 13.8, 13.0), (-18.8, sy * 13.8, 13.0),
            (-22.2, sy * 11.4, 28.5), (-19.2, sy * 11.4, 28.5), (-19.2, sy * 13.6, 28.5), (-22.2, sy * 13.6, 28.5),
        ], uv_rect=UV_SEAT_CHARCOAL, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_CHARCOAL)

    # Headrest cushion (X <= -19.8)
    p.add_chamfer_box(-23.4, -20.0, -5.2, +5.2, 28.5, 33.8, ch=0.7, uv_rect=UV_SEAT_OFFWHITE, side_uv=UV_SEAT_CHARCOAL, top_uv=UV_SEAT_CHARCOAL)

    # Yellow-striped industrial shoulder harness straps (X <= -16.4)
    for sy in (+1.0, -1.0):
        p.add_tube([
            (-20.2, sy * 5.2, 28.2),
            (-18.6, sy * 5.5, 21.0),
            (-16.4, sy * 5.8, 13.0),
        ], [0.55, 0.55, 0.55], segs=6, uv_rect=UV_SEAT_HARNESS)

    return p


def build_steering():
    """3-spoke steel rally wheel centered at steer_pos=(13.0, 0.0, 24.5) + angled steering shaft."""
    p = MeshPart("steering")
    hub = (13.0, 0.0, 24.5)
    tilt = math.radians(26.0)
    axis = (-math.cos(tilt), 0.0, math.sin(tilt))
    X, Y, Z = basis_from_axis(axis, up_hint=(0.0, 0.0, 1.0))

    # Steering column shaft connecting down to dash crossbar (20.5, 0, 22.8) & lower cowl (22.8, 0, 15.6)
    col_bot = (22.8, 0.0, 15.6)
    col_mid = (18.5, 0.0, 19.6)
    p.add_tube([col_bot, col_mid, hub], [0.80, 0.90, 1.10], segs=8, uv_rect=UV_STR_SPOKE)
    p.add_lathe(col_mid, vsub(hub, col_bot), [(-1.2, 1.4, 0.0), (+1.2, 1.4, 1.0)], segs=10, uv_rect=UV_STR_SPOKE)

    # Dish hub & Quake horn cap
    p.add_lathe(hub, axis, [
        (-1.4, 0.0, 0.0), (-1.4, 1.65, 0.25), (+0.6, 1.95, 0.65), (+0.9, 1.85, 0.90), (+0.9, 0.0, 1.0),
    ], segs=14, uv_mode="polar", uv_rect=UV_STR_CAP)

    # Thick rubberized rally rim (R=5.3u) + yellow 12-o'clock band
    rim_r, grip_r, n_ring = 5.3, 0.84, 28
    rim_pts = []
    for i in range(n_ring + 1):
        th = 2.0 * math.pi * (i / float(n_ring))
        rim_pts.append(vadd(hub, vadd(vmul(X, 1.6), vadd(vmul(Y, rim_r * math.cos(th)), vmul(Z, rim_r * math.sin(th))))))
    p.add_tube(rim_pts, [grip_r] * len(rim_pts), segs=8, uv_rect=UV_STR_GRIP, cap_start=False, cap_end=False)

    band_pts = []
    for k in range(5):
        th = math.radians(76.0 + 7.0 * k)
        band_pts.append(vadd(hub, vadd(vmul(X, 1.6), vadd(vmul(Y, rim_r * math.cos(th)), vmul(Z, rim_r * math.sin(th))))))
    p.add_tube(band_pts, [grip_r * 1.06] * len(band_pts), segs=8, uv_rect=UV_STR_BAND, cap_start=True, cap_end=True)

    # 3 brushed steel spokes
    for ang_deg in (195.0, 345.0, 270.0):
        a = math.radians(ang_deg)
        dir_sp = vadd(vmul(Y, math.cos(a)), vmul(Z, math.sin(a)))
        p.add_tube([
            vadd(hub, vadd(vmul(X, 0.2), vmul(dir_sp, 1.5))),
            vadd(hub, vadd(vmul(X, 1.6), vmul(dir_sp, rim_r - 0.3))),
        ], [0.60, 0.44], segs=6, uv_rect=UV_STR_SPOKE)

    return p


def build_engine():
    """Rear exposed chrome/brass Mega-Engine block with cooling fins, brass rocker covers,
    pressure regulator cylinder & hazard fuel cell.
    """
    p = MeshPart("engine")

    # 1) Heavy Crankcase Block over rear axle
    p.add_chamfer_box(-36.2, -26.2, -6.8, +6.8, 10.6, 17.5, ch=0.55, uv_rect=UV_ENG_BLOCK)
    for sy in (+1.0, -1.0):
        p.add_lathe((-31.2, sy * 6.8, 13.8), (0.0, sy, 0.0), [
            (0.0, 0.0, 0.0), (0.0, 3.8, 0.4), (1.3, 3.5, 0.8), (1.3, 0.0, 1.0),
        ], segs=14, uv_rect=UV_ENG_STEEL)

    # 2) Twin Heavy Splayed Cylinders with Cooling Fins & Brass Valve Covers
    for sy, cx_off in ((+1.0, -29.2), (-1.0, -32.6)):
        cyl_base = (cx_off, sy * 2.2, 16.0)
        cyl_axis = vnorm((0.0, sy * 0.50, 0.866))
        p.add_lathe(cyl_base, cyl_axis, [
            (0.0, 2.95, 0.0), (6.4, 2.95, 0.6), (6.4, 3.45, 0.7), (9.0, 3.45, 0.9), (9.0, 0.0, 1.0),
        ], segs=12, uv_rect=UV_ENG_BLOCK)
        for fi in range(6):
            fh = 1.3 + fi * 0.95
            fr = 4.05 + (0.28 if fi >= 4 else 0.0)
            p.add_lathe(cyl_base, cyl_axis, [
                (fh, 2.9, 0.0), (fh, fr, 0.4), (fh + 0.34, fr, 0.6), (fh + 0.34, 2.9, 1.0),
            ], segs=12, uv_rect=UV_ENG_STEEL)
        top_pt = vadd(cyl_base, vmul(cyl_axis, 8.8))
        p.add_lathe(top_pt, cyl_axis, [
            (0.0, 0.0, 0.0), (0.0, 3.5, 0.2), (1.6, 3.25, 0.65), (2.1, 2.3, 0.85), (2.1, 0.0, 1.0),
        ], segs=10, uv_rect=UV_ENG_BRASS)

    # 3) Center Brass Super-Plenum + Twin Velocity-Stack Air Horns
    p.add_tube([(-31.0, 0.0, 17.2), (-31.0, 0.0, 23.6), (-33.5, 0.0, 25.5)], [1.55, 1.75, 1.95], segs=8, uv_rect=UV_ENG_STEEL)
    p.add_lathe((-33.2, 0.0, 25.4), vnorm((-0.92, 0.0, 0.39)), [
        (0.0, 0.0, 0.0), (0.0, 2.2, 0.1), (1.0, 3.5, 0.3), (6.5, 2.6, 0.85), (7.2, 3.2, 0.96), (7.2, 0.0, 1.0),
    ], segs=16, uv_rect=UV_ENG_BRASS)

    # 4) Rear Hazard Fuel Cell tucked cleanly behind seatback (X in [-25.8, -21.6])
    p.add_chamfer_box(-25.8, -21.6, -6.5, +6.5, 11.2, 19.6, ch=0.65, uv_rect=UV_ENG_BLOCK, top_uv=UV_ENG_HAZARD)
    p.add_lathe((-23.6, +3.0, 19.6), (0.0, 0.0, 1.0), [
        (0.0, 1.5, 0.0), (1.2, 1.5, 0.7), (1.2, 0.0, 1.0),
    ], segs=10, uv_rect=UV_ENG_BRASS)

    return p


def build_exhaust():
    """Dual swept-up mirror-chrome exhaust pipes with brass clamp collars & dark inner bores."""
    p = MeshPart("exhaust")
    for sy in (+1.0, -1.0):
        cx_port = -29.2 if sy > 0 else -32.6
        # Curved stainless/chrome header tube
        p.add_tube([
            (cx_port - 1.2, sy * 5.8, 19.2),
            (-34.6, sy * 8.4, 17.2),
            (-38.2, sy * 9.8, 18.2),
        ], [1.28, 1.32, 1.30], segs=10, uv_rect=UV_STAINLESS, cap_start=True, cap_end=False)

        # Brass collector clamp collar
        p.add_lathe((-38.0, sy * 9.8, 18.2), (-0.946, sy * 0.074, 0.315), [
            (-0.6, 1.25, 0.05), (-0.6, 1.65, 0.2), (+0.8, 1.65, 0.8), (+0.8, 1.25, 0.95),
        ], segs=12, uv_rect=UV_VALVE_BRASS)

        # Swept-up flared Chrome Megaphone ending at (-45.8, +/-10.5, 21.8)
        mega_start = (-38.0, sy * 9.8, 18.2)
        mega_end = (-45.8, sy * 10.5, 21.8)
        mega_axis = vsub(mega_end, mega_start)
        L_m = vlen(mega_axis)
        p.add_lathe(mega_start, mega_axis, [
            (0.0, 1.28, 0.05),
            (1.6, 1.42, 0.22),
            (L_m - 0.3, 2.45, 0.88),
            (L_m, 2.55, 0.96),
            (L_m, 2.10, 0.99),
        ], segs=18, uv_rect=UV_CHROME_BAR)

        # Dark soot-blackened inner megaphone bore
        p.add_lathe(mega_start, mega_axis, [
            (L_m, 2.10, 0.0),
            (L_m - 4.4, 0.92, 0.85),
            (L_m - 4.4, 0.00, 1.00),
        ], segs=14, uv_rect=UV_RUBBER_CAP)
    return p


def build_fat_mm_wheel(side_sign, radius, half_width=6.2):
    """Reuses tank_geom_core.build_pneumatic_wheel & remaps UVs cleanly into gk6_wheel.png."""
    wp, hp = build_pneumatic_wheel(side_sign=side_sign, radius=radius, half_width=half_width, segs=32)
    out = MeshPart("wheel")
    wp.st = [(u * 0.75, v) for (u, v) in wp.st]
    hp.st = [(0.75 + (u - 0.50) * 0.50, v) for (u, v) in hp.st]
    out.append_part(wp)
    out.append_part(hp)
    return out


# ---------------------------------------------------------------------------
# 2. Flame Plume Dynamic Builders (Per-Frame Geometry)
# ---------------------------------------------------------------------------
def build_flame_template():
    fo = MeshPart("flame_outer")
    fc = MeshPart("flame_core")

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
                    b, c, d = a + 1, a + cols, a + cols + 1
                    mp.tris += [(a, b, c), (b, d, c)]
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
                    b, c, d = a + 1, a + 2, a + 3
                    mp.tris += [(a, b, c), (b, d, c), (a, c, b), (b, c, d)]

    init_plume(fo, UV_FLAME_OUTER)
    init_plume(fc, UV_FLAME_CORE)
    return fo, fc


def eval_flame_frame(template_part, mode, frame_local, is_core=False, chassis_pitch=0.0, chassis_dz=0.0):
    nv = len(template_part.verts)
    n_rings, n_segs = 7, 8
    cols = n_segs + 1
    per_plume = n_rings * cols + 2 * (n_rings * 2)
    vv = [(0.0, 0.0, 0.0)] * nv
    nn = [(0.0, 0.0, 1.0)] * nv

    # Collapsed (<0.05u) during idle (0..11), fast (12..27), and explosion fadeout (50..63, frame_local >= 6)
    if mode in ("idle", "fast") or (mode == "explode" and frame_local >= 6):
        anchor = (-31.0, 0.0, 15.0) if mode in ("idle", "fast") else (-10.0, 0.0, 2.0)
        for i in range(nv):
            ang = (i % 7) * 0.9
            vv[i] = (anchor[0] + 0.012 * math.cos(ang), anchor[1] + 0.012 * math.sin(ang), anchor[2] + 0.012)
            nn[i] = (0.0, 0.0, 1.0)
        return vv, nn

    if mode == "explode":
        t = frame_local
        fade = 1.0 if t <= 3 else max(0.02, 1.0 - (t - 3) / 2.5)
        length = (26.0 if is_core else 36.0) * fade
        max_r = (7.5 if is_core else 12.5) * fade
        origins = [(-18.0, +4.0, 15.0), (-22.0, -4.0, 16.0)]
        dirs = [vnorm((-0.7, +0.4, 0.55)), vnorm((-0.7, -0.4, 0.55))]
        phase = t * 1.3
    else:
        t = frame_local
        pulse = 0.92 + 0.12 * math.sin(t * 1.9 + (0.7 if is_core else 0.0)) + 0.06 * math.cos(t * 3.1)
        length = (24.0 if is_core else 33.0) * pulse
        max_r = (1.80 if is_core else 3.45) * (0.92 + 0.12 * math.sin(t * 2.4))
        pivot = (-30.0, 0.0, 12.5)
        origins, dirs = [], []
        for sy in (+1.0, -1.0):
            tip = (-45.8, sy * 10.5, 21.8)
            q = rot_y(vsub(tip, pivot), chassis_pitch)
            origins.append((q[0] + pivot[0], q[1] + pivot[1], q[2] + pivot[2] + chassis_dz))
            d_base = vnorm((-0.946, sy * 0.074, 0.315))
            dirs.append(vnorm(rot_y(d_base, chassis_pitch)))
        phase = t * 1.5

    for pi in range(2):
        base = pi * per_plume
        orig = origins[pi]
        X, Y, Z = basis_from_axis(dirs[pi])
        for ri in range(n_rings):
            s = ri / float(n_rings - 1)
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
                idx = base + ri * cols + j
                vv[idx] = vadd(center, vadd(vmul(Y, rr * math.cos(th)), vmul(Z, rr * math.sin(th))))
                nn[idx] = vnorm(vadd(vmul(Y, math.cos(th)), vmul(Z, math.sin(th))))

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
    return (
        sum(v[0] for v in part.verts) / n,
        sum(v[1] for v in part.verts) / n,
        sum(v[2] for v in part.verts) / n,
    )


def ballistic_step(t, v0, grav=140.0, restitution=0.52):
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
def build_gokart_6(progs_dir=PROGS, meta_dir=OUT_DIR):
    print("1. Generating Go-Kart #6 ('Mega Man Heavy Fat-Tire Rammer') textures...", flush=True)
    tex_paths = generate_all_textures(progs_dir=progs_dir)

    print("2. Building high-detail 3D surfaces...", flush=True)
    parts = {
        "chassis":   build_chassis(),
        "front_bar": build_front_bar(),
        "t_collar":  build_t_collar(),
        "seat":      build_seat(),
        "steering":  build_steering(),
        "engine":    build_engine(),
        "exhaust":   build_exhaust(),
        "wheel_fl":  build_fat_mm_wheel(+1, radius=11.0, half_width=6.2),
        "wheel_fr":  build_fat_mm_wheel(-1, radius=11.0, half_width=6.2),
        "wheel_rl":  build_fat_mm_wheel(+1, radius=12.5, half_width=6.2),
        "wheel_rr":  build_fat_mm_wheel(-1, radius=12.5, half_width=6.2),
    }
    wheel_centers = {
        "wheel_fl": (+26.5, +27.5, 11.0),
        "wheel_fr": (+26.5, -27.5, 11.0),
        "wheel_rl": (-30.0, +29.0, 12.5),
        "wheel_rr": (-30.0, -29.0, 12.5),
    }
    for wname, wc in wheel_centers.items():
        wp = parts[wname]
        wp.verts = [vadd(v, wc) for v in wp.verts]

    flame_outer_tpl, flame_core_tpl = build_flame_template()

    explode_params = {
        "chassis":   ((+4.0,  -4.0, +40.0), (+16.0, -22.0, +28.0)),
        "front_bar": ((+78.0, +10.0, +54.0), (-45.0, +95.0, +35.0)),
        "t_collar":  ((+42.0, -22.0, +48.0), (+85.0, +70.0, -90.0)),
        "seat":      ((-8.0,  -16.0, +68.0), (+95.0, -45.0, +85.0)),
        "steering":  ((+26.0, +20.0, +76.0), (-110.0, +70.0, +125.0)),
        "engine":    ((-36.0,  +8.0, +58.0), (+65.0, -90.0, -45.0)),
        "exhaust":   ((-54.0, -22.0, +64.0), (-85.0, +115.0, +90.0)),
        "wheel_fl":  ((+44.0, +56.0, +52.0), (+90.0, -140.0, +110.0)),
        "wheel_fr":  ((+46.0, -58.0, +48.0), (-95.0, -135.0, -105.0)),
        "wheel_rl":  ((-42.0, +62.0, +46.0), (+85.0, +130.0, -95.0)),
        "wheel_rr":  ((-44.0, -60.0, +54.0), (-80.0, +145.0, +100.0)),
    }

    frame_names = (
        [f"idle_{i:02d}" for i in range(12)]
        + [f"fast_{i:02d}" for i in range(16)]
        + [f"super_{i:02d}" for i in range(16)]
        + [f"explode_{i:02d}" for i in range(20)]
    )
    assert len(frame_names) == 64

    sprung_names = ["chassis", "front_bar", "t_collar", "seat", "steering", "engine", "exhaust"]
    surf_frames = {name: [] for name in list(parts.keys()) + ["flame_outer", "flame_core"]}
    rear_pivot = (-30.0, 0.0, 12.5)

    print("3. Baking 64 animation frames (idle, fast, super+flames, explosion)...", flush=True)
    for fi in range(64):
        if fi < 12:
            th = 2.0 * math.pi * (fi / 12.0)
            bob_z = 0.26 * math.sin(th)
            pitch = 0.32 * math.cos(th)
            eng_th = 2.0 * math.pi * ((fi * 2) / 12.0)
            eng_dz = 0.40 * math.sin(eng_th)
            eng_rx = 1.5 * math.cos(eng_th)

            for sname in sprung_names:
                if sname in ("engine", "exhaust"):
                    vv, nn = xform_part(
                        parts[sname],
                        offset=(0.0, 0.14 * math.sin(eng_th), bob_z + eng_dz),
                        rx=eng_rx, ry=pitch, pivot=(-31.0, 0.0, 14.5),
                    )
                elif sname in ("front_bar", "t_collar"):
                    bar_dz = 0.22 * math.sin(eng_th + 0.6)
                    vv, nn = xform_part(
                        parts[sname],
                        offset=(0.0, 0.0, bob_z + bar_dz),
                        ry=pitch, pivot=(0.0, 0.0, 11.0),
                    )
                else:
                    vv, nn = xform_part(parts[sname], offset=(0.0, 0.0, bob_z), ry=pitch, pivot=(0.0, 0.0, 10.0))
                surf_frames[sname].append((vv, nn))

            for wname in wheel_centers:
                surf_frames[wname].append((list(parts[wname].verts), [vnorm(n) for n in parts[wname].norms]))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "idle", fi, is_core=False))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "idle", fi, is_core=True))

        elif fi < 28:
            fl = fi - 12
            th = 2.0 * math.pi * (fl / 16.0)
            bob_z = 0.36 * math.sin(th * 2.0)
            pitch = 0.45 * math.cos(th * 2.0)
            roll = 0.40 * math.sin(th)
            w_deg = -360.0 * (fl / 16.0)

            for sname in sprung_names:
                extra_z = 0.24 * math.sin(th * 4.0) if sname in ("engine", "exhaust", "front_bar") else 0.0
                vv, nn = xform_part(parts[sname], offset=(0.0, 0.0, bob_z + extra_z), rx=roll, ry=pitch, pivot=(0.0, 0.0, 10.0))
                surf_frames[sname].append((vv, nn))

            for wname, wc in wheel_centers.items():
                vv, nn = xform_part(parts[wname], ry=w_deg, pivot=wc)
                surf_frames[wname].append((vv, nn))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "fast", fl, is_core=False))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "fast", fl, is_core=True))

        elif fi < 44:
            fl = fi - 28
            th = 2.0 * math.pi * (fl / 16.0)
            pitch = +2.0 + 0.35 * math.sin(th * 2.0)
            bob_z = 0.30 * math.cos(th * 2.0)
            w_deg = -720.0 * (fl / 16.0)

            for sname in sprung_names:
                extra_z = 0.28 * math.sin(th * 4.0) if sname in ("engine", "exhaust") else 0.0
                vv, nn = xform_part(parts[sname], offset=(0.0, 0.0, bob_z + extra_z), ry=pitch, pivot=rear_pivot)
                surf_frames[sname].append((vv, nn))

            for wname, wc in wheel_centers.items():
                vv, nn = xform_part(parts[wname], ry=w_deg, pivot=wc)
                surf_frames[wname].append((vv, nn))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "super", fl, is_core=False, chassis_pitch=pitch, chassis_dz=bob_z))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "super", fl, is_core=True, chassis_pitch=pitch, chassis_dz=bob_z))

        else:
            fl = fi - 44
            t_sec = (fl / 19.0) * 1.45
            for sname, part in parts.items():
                v0, omega = explode_params[sname]
                disp = ballistic_step(t_sec, v0)
                piv = wheel_centers[sname] if sname in wheel_centers else part_centroid(part)
                vv, nn = xform_part(
                    part, offset=disp,
                    rx=omega[0] * t_sec, ry=omega[1] * t_sec, rz=omega[2] * t_sec,
                    pivot=piv, min_z_clamp=0.5,
                )
                surf_frames[sname].append((vv, nn))

            surf_frames["flame_outer"].append(eval_flame_frame(flame_outer_tpl, "explode", fl, is_core=False))
            surf_frames["flame_core"].append(eval_flame_frame(flame_core_tpl, "explode", fl, is_core=True))

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

    md3_path = os.path.join(progs_dir, "gokart_6.md3")
    md3lib.write(md3_path, dict(name="progs/gokart_6.md3", frame_names=frame_names, surfaces=md3_surfaces))

    skin_path = os.path.join(progs_dir, "gokart_6.md3_0.skin")
    with open(skin_path, "w", encoding="ascii", newline="\n") as f:
        for s in md3_surfaces:
            f.write(f"{s['name']},{s['shader']}\n")

    exhaust_tips = [
        {"x": -45.8, "y": +10.5, "z": 21.8, "dx": -0.946, "dy": +0.074, "dz": +0.315},
        {"x": -45.8, "y": -10.5, "z": 21.8, "dx": -0.946, "dy": -0.074, "dz": +0.315},
    ]

    meta = {
        "id": "kart6",
        "name": "Mega Man Heavy Fat-Tire Rammer",
        "tagline": "Heavy-Caliber Mirror-Chrome Torpedo Bar & Fat 5-Ribbed Mega Man Tires",
        "palette": ["#e2e8f0", "#334155", "#eab308", "#1c1917"],
        "description": (
            "Unmistakable heavy-caliber Mega Man industrial contraption kart built on 4 extra-wide "
            "5-ribbed pneumatic tires (R=11u/12.5u, hw=6.2u) with deep-dish off-white stamped steel rims, "
            "zinc hex nuts, yellow cotter pins and brass Schrader valves. Features double-decker stainless "
            "tubular cage rails, brushed stainless floorpan, an industrial charcoal/off-white bucket seat, "
            "rear chrome/brass Mega-Engine with swept-up megaphones, and a colossal front mirror-chrome "
            "bullet-nosed torpedo bar clamped in a TIG-welded stainless T-collar."
        ),
        "highlights": [
            ["Rammer Bar", "Colossal R=3.55u mirror-chrome bullet-nosed torpedo bar (X=+7..+58) in TIG T-collar & diagonal struts"],
            ["Fat Tires", "4 extra-wide (hw=6.2u) 5-ribbed Mega Man tires on off-white stamped steel rims w/ cotter pins & valves"],
            ["Chassis", "Double-decker brushed stainless tubular cage (|Y|>=14.2), diamond floorpan & rear axle gussets"],
            ["Powertrain", "Exposed chrome/brass finned Mega-Engine block, velocity stack & dual swept-up chrome megaphones"],
            ["Player Fit", "Open overhead cockpit (22u wide torso box 100% clear), seat (-9, 0, 10), wheel (+13, 0, 24.5)"],
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
        meta_path = os.path.join(meta_dir, "gokart_6_meta.json")
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

    zmins_drive = []
    for fi in range(44):
        zmin = min(p[2] for s in m["surfaces"] for p in s["frames"][fi][0])
        zmins_drive.append(zmin)
        assert -0.1 <= zmin <= 0.1, f"Frame {fi} z_min={zmin:.4f} out of [-0.1, 0.1]"
    f0_pts = [p for s in m["surfaces"] if not s["name"].startswith("flame") for p in s["frames"][0][0]]
    xs = [p[0] for p in f0_pts]
    ys = [p[1] for p in f0_pts]
    zs = [p[2] for p in f0_pts]
    assert -47.0 <= min(xs) and max(xs) <= 58.01, f"X bounds out of [-47, 58]: {min(xs):.2f}..{max(xs):.2f}"
    assert -36.0 <= min(ys) and max(ys) <= 36.0, f"Y bounds out of [-36, 36]: {min(ys):.2f}..{max(ys):.2f}"

    # Flame collapse (<0.05u) in 0..27 & 50..63, roar (>15u) in 28..43
    for fn in ("flame_outer", "flame_core"):
        fs = next(s for s in m["surfaces"] if s["name"] == fn)
        for fi in list(range(28)) + list(range(50, 64)):
            pts = fs["frames"][fi][0]
            span = max(max(p[k] for p in pts) - min(p[k] for p in pts) for k in range(3))
            assert span < 0.05, f"{fn} frame {fi} span={span:.4f} >= 0.05!"
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

    # Explosion separation & ground bounce z>=0.5
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
    p = argparse.ArgumentParser(description="Build Go-Kart #6 MD3, skin, and textures.")
    p.add_argument("--out-dir", default=None, help="Output directory for MD3, skin, and PNGs")
    p.add_argument("--meta-dir", default=None, help="Optional directory for gokart_6_meta.json")
    args = p.parse_args()
    progs_dir = args.out_dir if args.out_dir is not None else PROGS
    meta_dir = args.meta_dir if args.meta_dir is not None else (OUT_DIR if args.out_dir is None else None)
    build_gokart_6(progs_dir=progs_dir, meta_dir=meta_dir)
