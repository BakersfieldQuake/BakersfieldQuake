"""Generates photorealistic + comedic 1024x1024 Head & Body UV textures for the 4 Random People NPCs:
  1. npc_randguy   — Random Guy with 6 Random Comedy Shirts (_0.._5) + 64oz Mega Gulp Cup
  2. npc_afroguy   — Black Guy with Giant 70s Afro, Gold Afro Pick, Funk Polo & Chrome Boombox
  3. npc_randlady  — Scandalized Neighborhood Lady with High Bun, 3 Funny Tops (_0.._2), Purse & Phone
  4. npc_fatguy    — Really Big Fat Guy with Too-Short Stained Shirt, Bare Belly & XXL Foil Burrito

Outputs:
  - Full-sRGB textures in `source/mm_tools/out/random_npcs/tex_srgb/` (for .glb & HTML WebGL showcase)
  - DarkPlaces-calibrated diffuse textures in `progs/` (overbright-compensated to match player.mdl & john_bird_head)
"""
from __future__ import annotations

import math
import os
from typing import Dict, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
REF_DIR = os.path.join(HERE, "ref")
OUT_ROOT = os.path.join(MM_TOOLS, "out", "random_npcs")
SRGB_DIR = os.path.join(OUT_ROOT, "tex_srgb")
PROGS_DIR = os.path.join(MOD_ROOT, "progs")

os.makedirs(SRGB_DIR, exist_ok=True)
os.makedirs(PROGS_DIR, exist_ok=True)

# DarkPlaces applies ~2x overbright lighting on `rgbGen lightingDiffuse` models;
# ~0.52 gain with subtle gamma lift matches `john_bird_head.png` and `veh_gtcar_tex.png`.
DP_GAIN = 0.52


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            r"C:\Windows\Fonts\impact.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
            r"C:\Windows\Fonts\verdanab.ttf",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
        ]
    )
    for fp in candidates:
        if os.path.isfile(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def save_pair(im_rgb: Image.Image, base_name: str) -> Tuple[str, str]:
    """Saves both vibrant sRGB (for GLB/HTML) and DarkPlaces-calibrated `progs/<base_name>.png`."""
    srgb_path = os.path.join(SRGB_DIR, f"{base_name}.png")
    im_rgb.convert("RGB").save(srgb_path, "PNG", optimize=True)

    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32) / 255.0
    # Slight midtone richness curve + DarkPlaces overbright scale
    dp = np.clip((arr ** 1.06) * DP_GAIN, 0.0, 1.0)
    dp_im = Image.fromarray(np.round(dp * 255.0).astype(np.uint8), "RGB")
    dp_path = os.path.join(PROGS_DIR, f"{base_name}.png")
    dp_im.save(dp_path, "PNG", optimize=True)
    return srgb_path, dp_path


def despill_portrait(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Chroma-keys #00FF00 background and removes green edge spill, returning (rgb_float, alpha_float)."""
    im = Image.open(path).convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
    arr = np.asarray(im, dtype=np.float32)
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()
    g_ex = g - np.maximum(r, b)

    bg = (g_ex > 36.0) & (g > 85.0)
    alpha = np.clip(1.0 - (g_ex - 8.0) / 30.0, 0.0, 1.0)
    alpha[bg] = 0.0

    # Despill green fringe
    spill = g_ex > 3.0
    if np.any(spill):
        ex = g_ex[spill] - 2.0
        g[spill] = np.clip(g[spill] - 0.94 * ex, 0.0, 255.0)
        r[spill] = np.clip(r[spill] + 0.12 * ex, 0.0, 255.0)
        b[spill] = np.clip(b[spill] + 0.10 * ex, 0.0, 255.0)

    rgb = np.dstack([r, g, b])
    core = ndimage.binary_erosion((alpha > 0.96) & (g_ex < 8.0), iterations=3)
    if np.any(core):
        _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
        bleed_zone = alpha < 0.96
        rgb[bleed_zone] = rgb[iy[bleed_zone], ix[bleed_zone]]
    return rgb, alpha


def make_skin_patch(w: int, h: int, skin_rgb: Tuple[float, float, float], seed: int, hairy: float = 0.0) -> np.ndarray:
    """Synthesizes realistic human skin texture with subtle pores, subsurface warmth, and optional body hair."""
    rng = np.random.default_rng(seed)
    base = np.zeros((h, w, 3), dtype=np.float32)
    base[...] = skin_rgb

    # Multi-scale organic skin variation + fine pore grain
    macro = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=18.0) * 14.0
    med = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=3.2) * 5.5
    pores = rng.standard_normal((h, w)).astype(np.float32) * 2.4

    warm = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=9.0)
    base[..., 0] += macro + med + pores + warm * 4.5
    base[..., 1] += (macro + med + pores) * 0.84 - warm * 1.2
    base[..., 2] += (macro + med + pores) * 0.74 - warm * 2.2

    if hairy > 0.0:
        # Short dark arm/belly hairs
        hair_layer = rng.uniform(0.0, 1.0, (h, w)).astype(np.float32)
        streaks = ndimage.gaussian_filter((hair_layer > (1.0 - 0.035 * hairy)).astype(np.float32), sigma=(2.6, 0.65))
        darken = np.clip(streaks * 68.0 * hairy, 0.0, 42.0)
        base -= darken[..., None]

    return np.clip(base, 0.0, 255.0)


def make_hair_swatch(w: int, h: int, hair_rgb: Tuple[float, float, float], curly: bool, seed: int) -> np.ndarray:
    """Synthesizes either rich coiled Afro curls or multi-toned directional hair strands."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w, 3), dtype=np.float32)
    out[...] = hair_rgb
    if curly:
        # Tight 3D coiled ringlets + specular sheen highlights
        n1 = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=2.2)
        n2 = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=5.5)
        rings = np.sin(n1 * 9.5 + n2 * 4.0)
        shade = rings * 16.0 + n2 * 18.0
        out[..., 0] += shade * 1.05
        out[..., 1] += shade * 1.00
        out[..., 2] += shade * 0.95
    else:
        # Flowing vertical/diagonal hair strands with natural highlights & lowlights
        raw = rng.standard_normal((h, w)).astype(np.float32)
        strands = ndimage.gaussian_filter(raw, sigma=(9.5, 1.1)) * 42.0
        clumps = ndimage.gaussian_filter(raw, sigma=(22.0, 4.0)) * 26.0
        sh = strands + clumps
        out[..., 0] += sh * 1.15
        out[..., 1] += sh * 0.92
        out[..., 2] += sh * 0.68
    return np.clip(out, 0.0, 255.0)


# ==============================================================================
# 1. HEAD + HAIR + ACCESSORY 1024x1024 ATLASES
# ==============================================================================

HEAD_SPECS: Dict[str, Dict] = {
    "randguy": dict(
        portrait="randguy_portrait.png",
        cx=512.0, rx_face=208.0,
        y_crown=105.0, y_eyes=385.0, y_chin=642.0, y_neck=745.0,
        skin_rgb=(210.0, 152.0, 120.0),
        hair_rgb=(58.0, 44.0, 30.0),
        hair_back_t=0.56,   # Back hairline drops down to nape (t=0.56)
        curly=False,
        accent_kind="cap_none",
    ),
    "afroguy": dict(
        portrait="afroguy_portrait.png",
        cx=512.0, rx_face=172.0,
        y_crown=270.0, y_eyes=450.0, y_chin=724.0, y_neck=785.0,
        skin_rgb=(156.0, 92.0, 62.0),
        hair_rgb=(32.0, 29.0, 26.0),
        hair_back_t=0.60,
        curly=True,
        accent_kind="afro_gold",
    ),
    "lady": dict(
        portrait="lady_portrait.png",
        cx=516.0, rx_face=222.0,
        y_crown=180.0, y_eyes=445.0, y_chin=770.0, y_neck=835.0,
        skin_rgb=(218.0, 162.0, 132.0),
        hair_rgb=(88.0, 56.0, 35.0),
        hair_back_t=0.62,
        curly=False,
        accent_kind="lady_glam",
    ),
    "fatguy": dict(
        portrait="fatguy_portrait.png",
        cx=512.0, rx_face=244.0,
        y_crown=98.0, y_eyes=380.0, y_chin=735.0, y_neck=770.0,
        skin_rgb=(226.0, 172.0, 154.0),
        hair_rgb=(54.0, 40.0, 25.0),
        hair_back_t=0.50,
        curly=False,
        accent_kind="fat_sweat",
    ),
}


def build_head_atlas(key: str) -> None:
    sp = HEAD_SPECS[key]
    port_rgb, port_a = despill_portrait(os.path.join(REF_DIR, sp["portrait"]))

    W, H = 1024, 1024
    # t in [0.00..0.86] -> seamless 360° head+neck wrap (rows 0..880)
    # t in [0.88..1.00] -> 3D hair/afro/bun swatch & gold/sunglasses accents (rows 900..1024)
    WRAP_H = 880
    skin_bg = make_skin_patch(W, WRAP_H, sp["skin_rgb"], seed=100 + hash(key) % 997)
    hair_bg = make_hair_swatch(W, WRAP_H, sp["hair_rgb"], curly=sp["curly"], seed=200 + hash(key) % 997)

    ug = (np.arange(W, dtype=np.float32)[None, :] + 0.5) / W      # 0..1 around head (0.5 = +X nose)
    tg = (np.arange(WRAP_H, dtype=np.float32)[:, None] + 0.5) / WRAP_H  # 0=crown, 0.82=chin, 1.0=neck base

    theta = (ug - 0.5) * (2.0 * math.pi)  # -pi..+pi, 0 = front (+X)
    abs_th = np.abs(theta)

    # Procedural hairline on sides & back of skull so 360° turnaround looks completely natural
    # Front forehead is open; sides (temples/sideburns) & back skull are covered in realistic hair down to nape!
    front_open = np.exp(-((theta / 1.12) ** 2))  # 1 at front, ~0 at back
    hairline_t = sp["hair_back_t"] * (1.0 - 0.72 * front_open)  # e.g. ~0.16 at front crown, ~0.56 at back nape
    # Sideburn dip around ears (|theta| ~ 1.35 rad)
    ear_zone = np.exp(-(((abs_th - 1.48) / 0.22) ** 2)) * np.exp(-(((tg - 0.48) / 0.13) ** 2))
    w_back_hair = np.clip((hairline_t - tg) / 0.055, 0.0, 1.0) * (1.0 - 0.85 * ear_zone)

    canvas_wrap = skin_bg * (1.0 - w_back_hair[..., None]) + hair_bg * w_back_hair[..., None]

    # Subtle anatomical neck & under-chin shadow around wrap
    neck_shade = 1.0 - 0.14 * np.clip((tg - 0.76) / 0.14, 0.0, 1.0)
    canvas_wrap *= neck_shade[..., None]

    # Subtle sculpted ear shading at u=0.25 and u=0.75, tg~0.48
    ear_fold = np.sin((abs_th - 1.48) * 26.0) * ear_zone * 14.0
    canvas_wrap[..., 0] = np.clip(canvas_wrap[..., 0] + ear_fold + 8.0 * ear_zone, 0.0, 255.0)
    canvas_wrap[..., 1] = np.clip(canvas_wrap[..., 1] + ear_fold * 0.7, 0.0, 255.0)
    canvas_wrap[..., 2] = np.clip(canvas_wrap[..., 2] + ear_fold * 0.6, 0.0, 255.0)

    # Project photorealistic front portrait across front hemisphere (|theta| < ~82 deg) using orthographic sin(theta)!
    px_map = np.broadcast_to(sp["cx"] + np.sin(np.clip(theta, -1.45, 1.45)) * sp["rx_face"], (WRAP_H, W))
    # Piece-wise smooth vertical calibration: crown(tg=0.04)->eyes(tg=0.42)->chin(tg=0.80)->neck(tg=0.96)
    t_knots = np.array([0.00, 0.06, 0.42, 0.80, 1.00], dtype=np.float32)
    y_knots = np.array([
        max(10.0, sp["y_crown"] - 28.0),
        sp["y_crown"],
        sp["y_eyes"],
        sp["y_chin"],
        sp["y_neck"],
    ], dtype=np.float32)
    py_map = np.interp(tg[:, 0], t_knots, y_knots)[:, None] * np.ones((1, W), dtype=np.float32)

    coords = np.array([np.clip(py_map, 0, 1023), np.clip(px_map, 0, 1023)])
    sampled = np.stack(
        [ndimage.map_coordinates(port_rgb[..., c], coords, order=1, mode="nearest") for c in range(3)],
        axis=-1,
    )
    samp_a = ndimage.map_coordinates(port_a, coords, order=1, mode="nearest")

    # Feather smoothly past temples and taper along jawline so zero 2D portrait shirt-collar/bg hair bleeds onto neck!
    jaw_taper = np.clip((tg - 0.50) / 0.34, 0.0, 1.0)
    max_th = (1.36 if key != "afroguy" else 1.08) * (1.0 - 0.36 * jaw_taper)
    ang_w = np.clip((max_th - abs_th) / 0.28, 0.0, 1.0)
    ang_w = ang_w * ang_w * (3.0 - 2.0 * ang_w)
    bot_cutoff = 0.81 if key in ("afroguy", "fatguy") else 0.86
    bot_w = np.clip((bot_cutoff - tg) / 0.08, 0.0, 1.0)
    blend_w = ang_w * bot_w * np.clip(samp_a * 1.15, 0.0, 1.0)

    canvas_wrap = canvas_wrap * (1.0 - blend_w[..., None]) + sampled * blend_w[..., None]

    # Assemble full 1024x1024 atlas
    full = np.zeros((H, W, 3), dtype=np.uint8)
    full[:WRAP_H] = np.clip(np.round(canvas_wrap), 0, 255).astype(np.uint8)
    # Pad transition rows 880..900 with neck base color
    full[WRAP_H:900] = full[WRAP_H - 1 : WRAP_H]

    # Bottom strip [900..1024]:
    #   x=[0..512]: High-detail 3D hair/afro/bun swatch
    #   x=[512..768]: Gold metal (hoops / afro pick handle / chain)
    #   x=[768..1024]: Dark glossy sunglasses / cap / dark accent
    hair_strip = make_hair_swatch(512, 124, sp["hair_rgb"], curly=sp["curly"], seed=500 + hash(key) % 997)
    full[900:, 0:512] = np.round(hair_strip).astype(np.uint8)

    im = Image.fromarray(full, "RGB")
    dr = ImageDraw.Draw(im)
    # Brushed gold swatch (x=512..768, y=900..1024)
    for y in range(900, 1024):
        sh = int(22 * math.sin((y - 900) * 0.14))
        col = (min(255, 232 + sh), min(255, 188 + sh), max(0, 58 + sh // 2))
        dr.line([(512, y), (767, y)], fill=col)
    # Dark glossy tortoise/aviator lens & frame swatch (x=768..1024, y=900..1024)
    for y in range(900, 1024):
        sh = int(16 * math.cos((y - 900) * 0.11))
        col = (max(12, 34 + sh), max(12, 30 + sh), max(16, 40 + sh))
        dr.line([(768, y), (1023, y)], fill=col)

    out_name = {
        "randguy": "npc_randguy_head",
        "afroguy": "npc_afroguy_head",
        "lady": "npc_randlady_head",
        "fatguy": "npc_fatguy_head",
    }[key]
    save_pair(im, out_name)
    print(f"  built head atlas: {out_name}.png")


# ==============================================================================
# 2. BODY + CLOTHES + SHOES + FUNNY PROPS 1024x1024 ATLASES
# ==============================================================================
# UV Quadrant Convention (1024x1024, t=0 at y=0 top, t=1 at y=1024 bottom):
#   Q0 Top-Left  [x=0..512,   y=0..512]   : Torso Shirt Front (x=0..256) & Back (x=256..512), collar y=16 -> hem y=496
#   Q1 Top-Right [x=512..1024,y=0..512]   : Pants/Shorts (y=12..330) + Footwear & Socks (y=340..508)
#   Q2 Bot-Left  [x=0..512,   y=512..1024]: Bare Skin (arms, forearms, hands, calves)
#   Q3 Bot-Right [x=512..1024,y=512..1024]: Character Funny Props (Mega Gulp / Boombox & Gold Chain / Purse & Phone / XXL Burrito)

def _add_fabric_weave(im: Image.Image, box: Tuple[int, int, int, int], strength: float = 8.0, seed: int = 7) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    rng = np.random.default_rng(seed)
    arr = np.asarray(im.crop(box), dtype=np.float32)
    yg, xg = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = (np.sin(xg * 1.6) * np.cos(yg * 1.6)) * (strength * 0.45)
    folds = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), sigma=(6.0, 22.0)) * (strength * 2.4)
    ao_side = 1.0 - 0.16 * ((np.abs((xg % 256.0) - 128.0) / 128.0) ** 2.2)
    arr = (arr + weave[..., None] + folds[..., None]) * ao_side[..., None]
    im.paste(Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8), "RGB"), (x0, y0))


def _draw_centered_lines(dr: ImageDraw.ImageDraw, cx: int, y_start: int, lines: list[Tuple[str, int, Tuple[int, int, int]]], stroke_col=(15, 15, 18), stroke_w: int = 3) -> None:
    y = y_start
    for txt, fsz, col in lines:
        fnt = _load_font(fsz, bold=True)
        bb = dr.textbbox((0, 0), txt, font=fnt, stroke_width=stroke_w)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        dr.text((cx - tw // 2, y), txt, font=fnt, fill=col, stroke_width=stroke_w, stroke_fill=stroke_col)
        y += th + 8


def _paint_pants_and_shoes(
    im: Image.Image,
    pants_col: Tuple[int, int, int],
    pants_kind: str,
    shoe_col: Tuple[int, int, int],
    sock_col: Tuple[int, int, int],
    seed: int,
) -> None:
    dr = ImageDraw.Draw(im)
    # Pants region x=512..1024, y=0..336
    dr.rectangle([512, 0, 1023, 336], fill=pants_col)
    # Leather belt at top of pants (y=0..28)
    dr.rectangle([512, 0, 1023, 28], fill=(42, 30, 22))
    dr.rectangle([620, 3, 660, 25], outline=(215, 185, 78), width=4)  # Belt buckle

    if pants_kind == "cargo_khaki":
        # Side cargo pockets + stitching
        for px in (548, 795):
            dr.rectangle([px, 115, px + 95, 235], fill=(166, 146, 112), outline=(112, 95, 68), width=2)
            dr.rectangle([px - 2, 110, px + 97, 138], fill=(176, 156, 120), outline=(112, 95, 68), width=2)
    elif pants_kind == "denim":
        # Indigo denim seams, pockets & golden contrast stitching
        for sx in (524, 640, 768, 896, 1012):
            dr.line([(sx, 28), (sx, 334)], fill=(198, 152, 68), width=2)
        for px in (560, 815):
            dr.polygon([(px, 55), (px + 74, 55), (px + 74, 122), (px + 37, 142), (px, 122)], outline=(198, 152, 68), width=2)
    elif pants_kind == "capri":
        # Sleek dark charcoal/plum stretch yoga capris with side stripe
        for sx in (638, 894):
            dr.line([(sx, 28), (sx, 334)], fill=(235, 95, 165), width=5)

    _add_fabric_weave(im, (512, 28, 1024, 336), strength=9.0, seed=seed)

    # Footwear region x=512..1024, y=336..512
    # Left half x=512..768: Shoe upper + laces + rubber midsole
    dr.rectangle([512, 336, 768, 511], fill=shoe_col)
    dr.rectangle([512, 476, 768, 511], fill=(236, 236, 232))  # Crisp white/cream rubber sole
    dr.line([(512, 476), (768, 476)], fill=(45, 45, 50), width=3)
    # Sneaker tongue & laces near center x=615..665
    dr.rectangle([612, 355, 668, 445], fill=(40, 42, 48))
    for ly in range(366, 440, 15):
        dr.line([(608, ly), (672, ly)], fill=(242, 242, 245), width=4)
    # Sport side stripe
    dr.line([(530, 455), (600, 395)], fill=(240, 240, 245), width=7)
    dr.line([(680, 395), (750, 455)], fill=(240, 240, 245), width=7)

    # Right half x=768..1024: Ribbed crew socks (y=336..450) + Dark rubber outsole tread (y=450..512)
    dr.rectangle([768, 336, 1023, 450], fill=sock_col)
    for rx in range(774, 1020, 8):
        dr.line([(rx, 336), (rx, 448)], fill=(max(0, sock_col[0] - 18), max(0, sock_col[1] - 18), max(0, sock_col[2] - 18)), width=2)
    # Classic athletic sock stripes at top
    dr.rectangle([768, 344, 1023, 354], fill=(210, 42, 42))
    dr.rectangle([768, 360, 1023, 368], fill=(38, 78, 185))
    dr.rectangle([768, 450, 1023, 511], fill=(34, 34, 38))


def build_randguy_bodies() -> None:
    """Builds 6 hilarious random-shirt body atlases (`npc_randguy_body_0` .. `_5`)."""
    skin = make_skin_patch(512, 512, HEAD_SPECS["randguy"]["skin_rgb"], seed=301, hairy=0.55)
    shirts = [
        dict(
            bg=(28, 128, 138), collar=(18, 92, 102), style="tee",
            front=[("I SURVIVED", 34, (250, 245, 215)), ("OILDALE", 44, (255, 205, 52))],
            back=[("BARELY.", 42, (255, 215, 65))],
        ),
        dict(
            bg=(22, 86, 148), collar=(18, 68, 120), style="hawaiian",
            front=[], back=[],
        ),
        dict(
            bg=(232, 182, 48), collar=(145, 34, 28), style="ringer",
            front=[("FORKLIFT", 38, (150, 26, 22)), ("CERTIFIED", 38, (24, 28, 36)), ("LADIES PLEASE", 22, (150, 26, 22))],
            back=[("STAND BACK", 34, (150, 26, 22)), ("50 FEET", 42, (24, 28, 36))],
        ),
        dict(
            bg=(214, 68, 58), collar=(165, 42, 36), style="tee",
            front=[("WORLD'S", 34, (252, 248, 240)), ("OKAYEST", 42, (255, 228, 72)), ("GUY", 46, (252, 248, 240))],
            back=[("#47 IN", 32, (252, 248, 240)), ("BAKERSFIELD", 30, (255, 228, 72))],
        ),
        dict(
            bg=(120, 60, 190), collar=(65, 30, 110), style="tiedye",
            front=[("GAS STATION", 30, (255, 255, 255)), ("SUSHI CLUB", 34, (255, 235, 60))],
            back=[("NO REGRETS", 34, (255, 255, 255))],
        ),
        dict(
            bg=(28, 30, 36), collar=(195, 38, 28), style="flames",
            front=[("WELCOME TO", 24, (255, 220, 75)), ("FLAVOR ZONE", 34, (255, 95, 28))],
            back=[("BOWLING", 34, (255, 210, 60)), ("ALTERNATE", 28, (245, 245, 245))],
        ),
    ]

    for idx, sh in enumerate(shirts):
        im = Image.new("RGB", (1024, 1024), (128, 128, 128))
        # Q2 Bare skin
        im.paste(Image.fromarray(np.round(skin).astype(np.uint8), "RGB"), (0, 512))
        # Q1 Khaki cargo shorts + classic grey/navy dad New-Balance sneakers + white crew socks!
        _paint_pants_and_shoes(im, pants_col=(178, 158, 122), pants_kind="cargo_khaki", shoe_col=(152, 158, 168), sock_col=(238, 238, 236), seed=400 + idx)

        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 511, 511], fill=sh["bg"])

        if sh["style"] == "hawaiian":
            rng = np.random.default_rng(99 + idx)
            for _ in range(55):
                hx, hy = int(rng.integers(18, 494)), int(rng.integers(24, 490))
                col = [(248, 86, 112), (255, 206, 56), (68, 214, 142), (252, 138, 48)][int(rng.integers(0, 4))]
                for a in range(5):
                    ang = a * 2 * math.pi / 5
                    dr.ellipse([hx + int(13 * math.cos(ang)) - 9, hy + int(13 * math.sin(ang)) - 9, hx + int(13 * math.cos(ang)) + 9, hy + int(13 * math.sin(ang)) + 9], fill=col)
                dr.ellipse([hx - 5, hy - 5, hx + 5, hy + 5], fill=(255, 245, 160))
            # Button placket down front center x=128
            dr.rectangle([122, 24, 134, 505], fill=(18, 72, 126))
            for by in range(60, 480, 55):
                dr.ellipse([124, by - 4, 132, by + 4], fill=(240, 235, 215))
        elif sh["style"] == "tiedye":
            arr_td = np.zeros((512, 512, 3), dtype=np.float32)
            yg, xg = np.mgrid[0:512, 0:512].astype(np.float32)
            cx_t = np.where(xg < 256, 128.0, 384.0)
            dx, dy = xg - cx_t, yg - 240.0
            rad = np.sqrt(dx * dx + dy * dy)
            ang = np.arctan2(dy, dx) + rad * 0.045
            arr_td[..., 0] = 155 + 95 * np.sin(ang * 3.0)
            arr_td[..., 1] = 145 + 95 * np.sin(ang * 3.0 + 2.1)
            arr_td[..., 2] = 165 + 88 * np.sin(ang * 3.0 + 4.2)
            im.paste(Image.fromarray(np.clip(arr_td, 0, 255).astype(np.uint8), "RGB"), (0, 0))
            dr = ImageDraw.Draw(im)
        elif sh["style"] == "flames":
            # Vertical red bowling panels + hot-rod flames rising from bottom hem!
            for px in (48, 192, 304, 448):
                dr.rectangle([px, 0, px + 18, 511], fill=(185, 34, 28))
            for fx in range(8, 504, 26):
                fh = 115 + int(48 * math.sin(fx * 0.23))
                dr.polygon([(fx, 511), (fx + 13, 511 - fh), (fx + 26, 511)], fill=(238, 78, 22))
                dr.polygon([(fx + 4, 511), (fx + 13, 511 - int(fh * 0.62)), (fx + 22, 511)], fill=(255, 198, 38))

        # Collar trim
        dr.rectangle([0, 0, 511, 24], fill=sh["collar"])
        if sh["front"]:
            _draw_centered_lines(dr, 128, 130, sh["front"])
        if sh["back"]:
            _draw_centered_lines(dr, 384, 145, sh["back"])
        _add_fabric_weave(im, (0, 0, 512, 512), strength=7.5, seed=500 + idx)

        # Q3 Props: 64oz MEGA GULP cup (x=520..770, y=520..880), Lid+Straw (x=780..1016, y=520..730), Belt Phone Clip (x=780..1016, y=740..1016)
        dr = ImageDraw.Draw(im)
        dr.rectangle([512, 512, 776, 890], fill=(244, 244, 248))
        dr.rectangle([512, 590, 776, 785], fill=(218, 38, 42))
        dr.rectangle([512, 608, 776, 626], fill=(28, 108, 205))
        _draw_centered_lines(dr, 644, 645, [("MEGA", 34, (255, 255, 255)), ("GULP 64oz", 26, (255, 228, 65))], stroke_w=2)
        # Lid & striped straw
        dr.rectangle([778, 512, 1023, 625], fill=(232, 236, 242))
        dr.rectangle([778, 626, 1023, 735], fill=(248, 248, 250))
        for sy in range(630, 732, 16):
            dr.rectangle([778, sy, 1023, sy + 7], fill=(228, 36, 42))
        # Dad clip-on phone holster
        dr.rectangle([778, 740, 1023, 1023], fill=(28, 30, 34))
        dr.rectangle([805, 770, 995, 990], outline=(72, 76, 84), width=3)

        save_pair(im, f"npc_randguy_body_{idx}")
        if idx == 0:
            save_pair(im, "npc_randguy_body")
    print("  built 6 random-shirt body atlases: npc_randguy_body_0..5.png")


def build_afroguy_body() -> None:
    """Builds funky 70s orange/gold chevron open-collar polo, flared indigo jeans, red high-tops, gold chain & chrome boombox."""
    im = Image.new("RGB", (1024, 1024), (128, 128, 128))
    skin = make_skin_patch(512, 512, HEAD_SPECS["afroguy"]["skin_rgb"], seed=302, hairy=0.0)
    im.paste(Image.fromarray(np.round(skin).astype(np.uint8), "RGB"), (0, 512))
    _paint_pants_and_shoes(im, pants_col=(36, 64, 118), pants_kind="denim", shoe_col=(204, 38, 38), sock_col=(244, 244, 244), seed=410)

    dr = ImageDraw.Draw(im)
    # Funky warm burnt-orange polo with gold & espresso retro horizontal/chevron stripes!
    dr.rectangle([0, 0, 511, 511], fill=(214, 96, 28))
    for sy, col, h in ((115, (248, 196, 48), 26), (150, (68, 34, 18), 18), (176, (248, 236, 205), 14), (200, (248, 196, 48), 24)):
        dr.rectangle([0, sy, 511, sy + h], fill=col)
    # Open disco V-neck collar on front chest (x=128) showing warm brown chest + gold chain!
    dr.polygon([(86, 0), (170, 0), (128, 138)], fill=tuple(int(v) for v in HEAD_SPECS["afroguy"]["skin_rgb"]))
    dr.line([(82, 0), (128, 142), (174, 0)], fill=(248, 236, 205), width=10)
    # Gold chain & medallion painted on chest + also available in Q3 for 3D medallion
    dr.arc([94, -22, 162, 135], start=20, end=160, fill=(245, 204, 64), width=6)
    dr.ellipse([114, 102, 142, 130], fill=(250, 210, 70), outline=(160, 115, 20), width=2)
    _add_fabric_weave(im, (0, 0, 512, 512), strength=7.5, seed=510)

    # Q3 Props: Retro Chrome Boombox (x=512..850, y=512..860), Gold Chain/Medallion (x=852..1023, y=512..860), Afro Pick (y=862..1023)
    dr = ImageDraw.Draw(im)
    dr.rectangle([512, 512, 850, 860], fill=(182, 188, 198))
    dr.rectangle([524, 535, 838, 605], fill=(38, 42, 48))  # Tuner dial & red LED VU meters
    for vx in range(540, 825, 18):
        dr.rectangle([vx, 558, vx + 11, 592], fill=(240, 58, 38) if vx % 36 == 0 else (58, 220, 95))
    # Twin round black woofer speakers with chrome dust caps
    for wx in (592, 770):
        dr.ellipse([wx - 64, 645, wx + 64, 773], fill=(24, 26, 30), outline=(228, 232, 240), width=6)
        dr.ellipse([wx - 22, 687, wx + 22, 731], fill=(215, 220, 230))
    # Center cassette deck
    dr.rectangle([662, 665, 700, 755], fill=(48, 52, 60), outline=(225, 228, 235), width=3)
    # Gold swatch & Afro pick teeth
    dr.rectangle([852, 512, 1023, 860], fill=(242, 198, 58))
    dr.rectangle([512, 862, 760, 1023], fill=(224, 42, 42))   # Classic red/gold fist pick handle
    dr.rectangle([761, 862, 1023, 1023], fill=(225, 230, 238)) # Steel pick tines

    save_pair(im, "npc_afroguy_body")
    print("  built body atlas: npc_afroguy_body.png")


def build_lady_bodies() -> None:
    """Builds 3 hilarious neighborhood shopping-lady tops (`npc_randlady_body_0..2`) + yoga capris + quilted purse + phone."""
    skin = make_skin_patch(512, 512, HEAD_SPECS["lady"]["skin_rgb"], seed=303, hairy=0.0)
    tops = [
        dict(
            style="cardigan", bg=(208, 48, 122), inner=(248, 242, 245),
            front=[("LIVE", 34, (208, 48, 122)), ("LAUGH", 34, (208, 48, 122)), ("FRAG", 42, (32, 28, 36))],
            back=[("SPEAK TO THE", 28, (255, 245, 250)), ("MANAGER", 38, (255, 228, 82))],
        ),
        dict(
            style="leopard", bg=(206, 154, 92), inner=(32, 26, 24),
            front=[], back=[],
        ),
        dict(
            style="blouse", bg=(34, 158, 148), inner=(250, 248, 242),
            front=[("HOA BOARD", 34, (255, 255, 255)), ("ENFORCER", 36, (255, 224, 72))],
            back=[("FINE: $250", 36, (255, 224, 72))],
        ),
    ]

    for idx, tp in enumerate(tops):
        im = Image.new("RGB", (1024, 1024), (128, 128, 128))
        im.paste(Image.fromarray(np.round(skin).astype(np.uint8), "RGB"), (0, 512))
        _paint_pants_and_shoes(im, pants_col=(44, 42, 54), pants_kind="capri", shoe_col=(224, 82, 138), sock_col=(245, 240, 244), seed=420 + idx)

        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 511, 511], fill=tp["bg"])
        if tp["style"] == "leopard":
            rng = np.random.default_rng(777)
            for _ in range(150):
                lx, ly = int(rng.integers(8, 504)), int(rng.integers(12, 500))
                dr.ellipse([lx - 13, ly - 9, lx + 13, ly + 9], fill=(138, 82, 34))
                dr.arc([lx - 15, ly - 11, lx + 15, ly + 11], start=30, end=310, fill=(36, 22, 14), width=5)
        elif tp["style"] == "cardigan":
            # White graphic tee panel down center of front chest (x=68..188) framed by open magenta cardigan!
            dr.rectangle([66, 24, 190, 511], fill=tp["inner"])
            _draw_centered_lines(dr, 128, 120, tp["front"], stroke_col=(255, 255, 255), stroke_w=1)
            _draw_centered_lines(dr, 384, 150, tp["back"])
        else:
            _draw_centered_lines(dr, 128, 140, tp["front"])
            _draw_centered_lines(dr, 384, 155, tp["back"])

        # Scoop neckline skin crescent at top of front chest
        dr.pieslice([82, -36, 174, 52], start=0, end=180, fill=tuple(int(v) for v in HEAD_SPECS["lady"]["skin_rgb"]))
        _add_fabric_weave(im, (0, 0, 512, 512), strength=7.0, seed=520 + idx)

        # Q3 Props: Quilted faux-designer Handbag (x=512..820, y=512..880) + Pink Smartphone (x=822..1023, y=512..880)
        dr = ImageDraw.Draw(im)
        dr.rectangle([512, 512, 820, 880], fill=(118, 52, 36))
        for q in range(-360, 380, 36):
            dr.line([(512, 512 + q), (820, 820 + q)], fill=(86, 36, 24), width=2)
            dr.line([(820, 512 + q), (512, 820 + q)], fill=(86, 36, 24), width=2)
        dr.ellipse([636, 655, 696, 715], fill=(242, 198, 66), outline=(140, 102, 22), width=3)  # Gold clasp
        # Smartphone screen + pink glitter case
        dr.rectangle([822, 512, 1023, 880], fill=(238, 105, 175))
        dr.rectangle([842, 540, 1004, 845], fill=(38, 168, 235))
        # Leather purse strap (y=882..1023)
        dr.rectangle([512, 882, 1023, 1023], fill=(92, 40, 28))

        save_pair(im, f"npc_randlady_body_{idx}")
        if idx == 0:
            save_pair(im, "npc_randlady_body")
    print("  built 3 lady outfit atlases: npc_randlady_body_0..2.png")


def build_fatguy_body() -> None:
    """Builds Fat Guy's stretched stained 'CARDIO TOMORROW' shirt riding up over bare hairy belly + jorts + XXL foil burrito!"""
    im = Image.new("RGB", (1024, 1024), (128, 128, 128))
    skin = make_skin_patch(512, 512, HEAD_SPECS["fatguy"]["skin_rgb"], seed=304, hairy=0.85)
    im.paste(Image.fromarray(np.round(skin).astype(np.uint8), "RGB"), (0, 512))
    # Faded blue denim jorts + navy slides over white athletic socks!
    _paint_pants_and_shoes(im, pants_col=(72, 108, 156), pants_kind="denim", shoe_col=(32, 48, 86), sock_col=(242, 240, 236), seed=430)

    # Q0 Torso: Top 72% (y=0..366) is stretched mustard-gold tee; Bottom 28% (y=366..512) on FRONT is bare hairy overhanging belly + navel!
    belly_skin = make_skin_patch(512, 512, HEAD_SPECS["fatguy"]["skin_rgb"], seed=399, hairy=1.15)
    im.paste(Image.fromarray(np.round(belly_skin).astype(np.uint8), "RGB"), (0, 0))

    dr = ImageDraw.Draw(im)
    # Shirt covers back down to y=470, but rides UP on the giant front gut at y=348 in an arched curve!
    shirt_col = (238, 186, 46)
    dr.rectangle([256, 0, 511, 475], fill=shirt_col)
    dr.rectangle([0, 0, 255, 345], fill=shirt_col)
    # Curved front hem riding up over the round gut (center arches up to y=332, sides down to y=395)
    hem_pts = [(0, 340)] + [(x, int(392 - 58 * math.sin(math.pi * x / 255.0))) for x in range(0, 256, 8)] + [(255, 340), (255, 0), (0, 0)]
    dr.polygon(hem_pts, fill=shirt_col)
    dr.line([(x, int(392 - 58 * math.sin(math.pi * x / 255.0))) for x in range(0, 256, 6)], fill=(182, 136, 26), width=5)

    # Collar + hilarious chest slogan + ketchup & salsa drips!
    dr.rectangle([0, 0, 511, 24], fill=(196, 142, 28))
    _draw_centered_lines(dr, 128, 105, [("CARDIO", 42, (175, 28, 26)), ("TOMORROW", 32, (32, 32, 38))], stroke_col=(255, 248, 220), stroke_w=2)
    _draw_centered_lines(dr, 384, 140, [("ALL YOU CAN", 30, (175, 28, 26)), ("EAT MVP", 40, (32, 32, 38))], stroke_col=(255, 248, 220), stroke_w=2)

    # Funny ketchup, taco-sauce & grease stains on front of shirt
    dr.ellipse([86, 232, 108, 268], fill=(188, 32, 22))
    dr.ellipse([94, 262, 104, 292], fill=(188, 32, 22))
    dr.ellipse([156, 248, 178, 272], fill=(198, 118, 18))

    # Deep 3D-shaded belly button on exposed lower gut (x=128, y=426) + happy trail!
    dr.ellipse([116, 415, 140, 437], fill=(142, 92, 78))
    dr.ellipse([121, 419, 135, 432], fill=(96, 56, 46))
    _add_fabric_weave(im, (0, 0, 512, 332), strength=7.0, seed=530)

    # Q3 Prop: Bakersfield XXL Foil-Wrapped Monster Burrito!
    # x=512..820, y=512..740: Toasted flour tortilla with brown grill blisters
    # x=512..820, y=740..1023: Shiny crinkled aluminum foil bottom wrap
    # x=822..1023, y=512..1023: Open bitten burrito top cross-section (carne asada, melted cheddar, guac, salsa, rice!)
    dr = ImageDraw.Draw(im)
    dr.rectangle([512, 512, 820, 742], fill=(238, 206, 152))
    rng = np.random.default_rng(888)
    for _ in range(42):
        bx, by = int(rng.integers(524, 808)), int(rng.integers(522, 732))
        dr.ellipse([bx - 12, by - 5, bx + 12, by + 5], fill=(158, 104, 52))
    # Crinkled silver foil
    for fy in range(742, 1024):
        sh = int(28 * math.sin(fy * 0.24) + 16 * math.cos(fy * 0.61))
        c = max(140, min(252, 206 + sh))
        dr.line([(512, fy), (820, fy)], fill=(c, c, min(255, c + 6)))
    # Delicious burrito filling end-cap (centered at 922, 712)
    dr.rectangle([822, 512, 1023, 1023], fill=(232, 198, 144))
    dr.ellipse([838, 628, 1006, 796], fill=(118, 62, 36))    # Carne asada beef
    dr.pieslice([848, 638, 996, 786], 20, 135, fill=(98, 186, 62))   # Guacamole
    dr.pieslice([848, 638, 996, 786], 145, 255, fill=(248, 188, 38)) # Melted cheddar
    dr.pieslice([848, 638, 996, 786], 265, 355, fill=(212, 44, 32))  # Red salsa

    save_pair(im, "npc_fatguy_body")
    print("  built body atlas: npc_fatguy_body.png")


def main() -> None:
    for k in ("randguy", "afroguy", "lady", "fatguy"):
        build_head_atlas(k)
    build_randguy_bodies()
    build_afroguy_body()
    build_lady_bodies()
    build_fatguy_body()
    print("ALL NPC TEXTURES GENERATED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
