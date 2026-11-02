"""Synthesizes all high-resolution textures & real BakersfieldQuake ghostly sprite
holograms for the Mystery Box 3D Quake Weapon (`v_mysterybox.md3` & `proj_mysterybox.md3`).

Outputs both DarkPlaces-calibrated textures in `BakersfieldQuake/progs/` and
full-sRGB PBR staging textures in `source/mm_tools/out/mystery_box/textures/`:
  1. mbox_hand.png       (1024x1024 RGB)  Masculine right hand, extensor tendons, palm lines, male nails & Ranger wrist bracer
  2. mbox_glass.png      (1024x1024 RGBA) Diagonal rainbow crystal glass + frosted white polka-dots + crystal-ball lens alpha
  3. mbox_qmark.png      (1024x512  RGBA) Left: Chunky white '?' w/ electric cyan bevel border | Right: Smoky cosmic crystal core
  4. mbox_ghost_3d.png   (512x512   RGB)  8-row spectral hologram gradient & rim-scanline palette for the 8 real 3D game ghosts
  5. mbox_ghost_spr.png  (1024x512  RGB)  4x2 spectral ectoplasm hologram atlas from 8 REAL BakersfieldQuake sprites
  6. mbox_fx.png         (512x512   RGB)  4-quadrant additive VFX: levitation wisps, sparkles, Grab-Charge Supernova, Throw Comet
"""
import math
import os
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
STAGE_TEX = os.path.join(MM_TOOLS, "out", "mystery_box", "textures")


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = clamp01((x - e0) / (e1 - e0 + 1e-12))
    return t * t * (3.0 - 2.0 * t)


def fbm_noise(h, w, scales=(4, 8, 16, 32, 64), weights=(0.34, 0.28, 0.19, 0.12, 0.07), seed=42):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    for sc, wt in zip(scales, weights):
        gh = max(2, h // sc)
        gw = max(2, w // sc)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        up = np.array(Image.fromarray(g).resize((w, h), Image.Resampling.BILINEAR), dtype=np.float32)
        acc += wt * up
    return (acc - acc.mean()) / (acc.std() + 1e-8)


def dp_calibrate(im_rgb, brightness=0.52, contrast=1.08):
    """Calibrates lightingDiffuse RGB textures for DarkPlaces ~2.3x overbright rendering."""
    out = ImageEnhance.Contrast(im_rgb).enhance(contrast)
    out = ImageEnhance.Brightness(out).enhance(brightness)
    return out


# ===========================================================================
# 1. MASCULINE MAN'S RIGHT HAND & RANGER WRIST BRACER (1024x1024 RGB)
# ===========================================================================
# UV Layout (matches 18-bone Masculine Right Hand rig):
#   v in [0.00 .. 0.15], u in [0.00 .. 0.86]: Dark stitched leather & gunmetal Quake Ranger wrist bracer
#   u in [0.00 .. 0.46], v in [0.15 .. 1.00]: Dorsal masculine forearm, veins, extensor tendons & weathered knuckles
#   u in [0.46 .. 0.86], v in [0.15 .. 1.00]: Masculine palmar skin, callused pads & deep flexion creases
#   u in [0.86 .. 1.00], v in [0.00 .. 1.00]: Short square-trimmed natural male fingernails
def build_mbox_hand():
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    pores = fbm_noise(S, S, scales=(2, 4, 10, 24), weights=(0.44, 0.28, 0.18, 0.10), seed=701)
    macro = fbm_noise(S, S, scales=(16, 36, 72), weights=(0.50, 0.32, 0.18), seed=702)

    # Warm rugged sunlit masculine tan skin palette
    c_dorsal = np.array([0.875, 0.668, 0.538], dtype=np.float32)
    c_palm = np.array([0.918, 0.722, 0.598], dtype=np.float32)

    is_palm = smoothstep(0.45, 0.47, u) * (1.0 - smoothstep(0.85, 0.87, u))
    col = c_dorsal * (1.0 - is_palm[..., None]) + c_palm * is_palm[..., None]
    col += pores[..., None] * np.array([0.020, 0.016, 0.013]) + macro[..., None] * np.array([0.018, 0.012, 0.009])

    # Subtle masculine dorsal extensor tendon highlights & inter-metacarpal shadow valleys (u in 0.06..0.40, v in 0.22..0.45)
    in_dors_hand = (1.0 - smoothstep(0.43, 0.46, u)) * smoothstep(0.18, 0.25, v) * (1.0 - smoothstep(0.43, 0.49, v))
    for tu in (0.09, 0.18, 0.27, 0.36):
        tendon = np.exp(-(((u - tu) / 0.018) ** 2)) * in_dors_hand
        valley = np.exp(-(((u - (tu + 0.045)) / 0.022) ** 2)) * in_dors_hand
        col += tendon[..., None] * np.array([0.042, 0.032, 0.024])
        col -= valley[..., None] * np.array([0.032, 0.026, 0.020])

    # Subtle subcutaneous dorsal veins on forearm/back of hand
    vein1 = np.exp(-(((u - (0.20 + 0.04 * np.sin(v * 9.0))) / 0.007) ** 2)) * smoothstep(0.16, 0.22, v) * (1.0 - smoothstep(0.38, 0.44, v))
    vein2 = np.exp(-(((u - (0.31 - 0.03 * np.cos(v * 7.5))) / 0.006) ** 2)) * smoothstep(0.16, 0.22, v) * (1.0 - smoothstep(0.36, 0.42, v))
    v_mask = clamp01(vein1 + 0.8 * vein2) * (1.0 - is_palm)
    col = col * (1.0 - 0.16 * v_mask[..., None]) + np.array([0.52, 0.47, 0.49]) * (0.16 * v_mask[..., None])

    # Warm blood-flow flush at knuckles & muscular fingertip pads
    flush = (
        np.exp(-(((v - 0.44) / 0.045) ** 2)) * (1.0 - is_palm) * 0.45
        + smoothstep(0.74, 0.94, v) * 0.55
    ) * (1.0 - smoothstep(0.85, 0.87, u))
    col = col * (1.0 - 0.20 * flush[..., None]) + np.array([0.84, 0.46, 0.39]) * (0.20 * flush[..., None])

    # --- Quake Ranger Stitched Saddle-Leather & Brass Wrist Bracer (v < 0.155, u < 0.86) ---
    is_cuff = (1.0 - smoothstep(0.145, 0.160, v)) * (1.0 - smoothstep(0.855, 0.865, u))
    leather_grain = fbm_noise(S, S, scales=(2, 5, 12), weights=(0.5, 0.3, 0.2), seed=709)
    c_leather = np.array([0.30, 0.195, 0.132], dtype=np.float32) + leather_grain[..., None] * 0.026
    # Brushed brass/gold trim bands at top (v ~ 0.135) and bottom (v ~ 0.025) of cuff
    trim_band = np.exp(-(((v - 0.136) / 0.009) ** 2)) + np.exp(-(((v - 0.025) / 0.010) ** 2))
    strap_band = smoothstep(0.062, 0.068, v) * (1.0 - smoothstep(0.095, 0.101, v))
    c_cuff = c_leather * (1.0 - 0.35 * strap_band[..., None]) + np.array([0.18, 0.115, 0.080]) * (0.35 * strap_band[..., None])
    c_cuff = c_cuff * (1.0 - clamp01(trim_band)[..., None] * 0.82) + np.array([0.68, 0.55, 0.34]) * (clamp01(trim_band)[..., None] * 0.82)
    # Ambient occlusion shadow right where leather cuff meets forearm skin
    cuff_ao = np.exp(-(((v - 0.158) / 0.012) ** 2)) * (1.0 - smoothstep(0.855, 0.865, u))
    col *= (1.0 - 0.32 * cuff_ao[..., None])
    col = col * (1.0 - is_cuff[..., None]) + c_cuff * is_cuff[..., None]

    # --- Short Square-Trimmed Male Fingernail Plate (u in [0.86 .. 1.00]) ---
    is_nail = smoothstep(0.858, 0.865, u)
    nu = (u - 0.93) / 0.065
    nv = v
    nail_col = np.broadcast_to(np.array([0.835, 0.628, 0.542], dtype=np.float32), (S, S, 3)).copy()
    nail_ridge = np.sin(nu * 42.0) * 0.006 + np.exp(-(((nu + 0.18) / 0.25) ** 2)) * 0.032
    nail_col += nail_ridge[..., None]
    lunula = 1.0 - smoothstep(0.78, 1.00, np.hypot(nu * 0.92, (nv - 0.03) / 0.15))
    nail_col = nail_col * (1.0 - 0.28 * lunula[..., None]) + np.array([0.90, 0.79, 0.73]) * (0.28 * lunula[..., None])
    free_arch = 0.89 - 0.03 * (1.0 - nu * nu)
    free_tip = smoothstep(free_arch - 0.018, free_arch + 0.012, nv)
    nail_col = nail_col * (1.0 - 0.55 * free_tip[..., None]) + np.array([0.89, 0.82, 0.74]) * (0.55 * free_tip[..., None])
    cuticle = 1.0 - smoothstep(0.0, 0.05, nv)
    nail_col *= (1.0 - 0.22 * cuticle[..., None])
    col = col * (1.0 - is_nail[..., None]) + nail_col * is_nail[..., None]

    im = Image.fromarray((clamp01(col) * 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im, "RGBA")

    # Rugged masculine dorsal knuckle creases
    CR_DARK = (132, 84, 60, 125)
    CR_HI = (228, 182, 150, 72)
    for fu in (0.09, 0.18, 0.27, 0.36, 0.42):
        cx = int(fu * S)
        for jv, rx, ry in ((0.44, 27, 10), (0.61, 24, 11), (0.78, 20, 8)):
            cy = int(jv * S)
            for k in (-6, -1, 4):
                dr.arc((cx - rx, cy + k - ry, cx + rx, cy + k + ry), 8, 172, fill=CR_DARK, width=2)
                dr.arc((cx - rx, cy + k - ry + 2, cx + rx, cy + k + ry + 2), 188, 352, fill=CR_HI, width=1)

    # Fine masculine forearm hairs on dorsal side (v in 0.17..0.38, u in 0.04..0.42)
    rng = np.random.default_rng(777)
    for _ in range(260):
        hx = int(rng.uniform(0.04, 0.42) * S)
        hy = int(rng.uniform(0.17, 0.39) * S)
        dx = int(rng.uniform(-4, 4))
        dy = int(rng.uniform(9, 17))
        dr.line([(hx, hy), (hx + dx, hy + dy)], fill=(78, 50, 36, 62), width=1)

    # Rivets along the Ranger wrist cuff strap
    for ru in np.linspace(0.06, 0.80, 9):
        rx_c = int(ru * S)
        ry_c = int(0.081 * S)
        dr.ellipse((rx_c - 6, ry_c - 6, rx_c + 6, ry_c + 6), fill=(150, 128, 96, 255), outline=(55, 42, 30, 230), width=2)
        dr.ellipse((rx_c - 2, ry_c - 3, rx_c + 1, ry_c), fill=(225, 205, 170, 210))

    # Natural subtle masculine palmar flexion lines
    PL = (162, 104, 80, 88)
    dr.line([(int(0.49 * S), int(0.39 * S)), (int(0.64 * S), int(0.37 * S)), (int(0.77 * S), int(0.42 * S))], fill=PL, width=4)
    dr.line([(int(0.80 * S), int(0.34 * S)), (int(0.66 * S), int(0.31 * S)), (int(0.52 * S), int(0.27 * S))], fill=PL, width=4)
    dr.arc((int(0.63 * S), int(0.16 * S), int(0.84 * S), int(0.38 * S)), 105, 265, fill=PL, width=4)
    for fu in (0.52, 0.60, 0.68, 0.76, 0.82):
        cx = int(fu * S)
        for jv in (0.45, 0.62, 0.78):
            cy = int(jv * S)
            dr.line([(cx - 20, cy), (cx + 20, cy)], fill=PL, width=3)
            dr.line([(cx - 17, cy + 5), (cx + 17, cy + 5)], fill=PL, width=2)

    im = im.filter(ImageFilter.GaussianBlur(0.85))
    im.save(os.path.join(STAGE_TEX, "mbox_hand_web.png"), "PNG", optimize=True)
    dp_im = dp_calibrate(im, brightness=0.54, contrast=1.08)
    dp_im.save(os.path.join(STAGE_TEX, "mbox_hand.png"), "PNG", optimize=True)
    dp_im.save(os.path.join(PROGS_DIR, "mbox_hand.png"), "PNG", optimize=True)
    print("  [OK] mbox_hand.png")


# ===========================================================================
# 2. RAINBOW POLKA-DOT CRYSTAL GLASS SHELL (`mbox_glass.png`, 1024x1024 RGBA)
# ===========================================================================
# Faithfully recreates the uploaded reference image:
#   - Smooth diagonal iridescent rainbow bands (hot magenta -> violet -> sky cyan -> mint green -> yellow -> orange -> coral)
#   - 7x7 grid of frosted pearlescent polka-dot bubbles per face (brighter near rounded bevel corners, softer toward center)
#   - Crystal-ball magnifying window alpha: ~0.22 in clear center lens -> ~0.68 along glossy rainbow bevel edges!
def rainbow_palette(t):
    """Smooth vibrant 6-stop periodic rainbow matching the uploaded Mystery Box image."""
    stops = np.array([
        [1.00, 0.16, 0.62],  # 0.00 Hot Magenta-Pink
        [0.52, 0.30, 1.00],  # 0.17 Royal Violet-Blue
        [0.10, 0.90, 1.00],  # 0.34 Electric Sky-Cyan
        [0.26, 1.00, 0.52],  # 0.50 Neon Mint-Green
        [1.00, 0.92, 0.20],  # 0.67 Sunny Lemon-Yellow
        [1.00, 0.50, 0.14],  # 0.84 Tangerine Coral-Orange
        [1.00, 0.16, 0.62],  # 1.00 Wrap
    ], dtype=np.float32)
    tf = (t % 1.0) * 6.0
    idx = np.floor(tf).astype(np.int32) % 6
    frac = tf - np.floor(tf)
    frac = frac * frac * (3.0 - 2.0 * frac)
    c0 = stops[idx]
    c1 = stops[idx + 1]
    return c0 + (c1 - c0) * frac[..., None]


def build_mbox_glass():
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S
    v = yy / S

    # Diagonal 45-degree rainbow wave with gentle glass refraction ripple
    diag = 0.72 * u + 0.64 * v + 0.03 * np.sin(u * 2.0 * math.pi) * np.cos(v * 2.0 * math.pi)
    rgb = rainbow_palette(diag)

    # 7x7 Polka-Dot Halftone Grid across each face (matching the reference cube's circular dot pattern!)
    n_dots = 7.0
    du = (u * n_dots) % 1.0 - 0.5
    dv = (v * n_dots) % 1.0 - 0.5
    dot_r = np.hypot(du, dv)
    dot_mask = 1.0 - smoothstep(0.24, 0.34, dot_r)

    # Distance from face center (0 at center lens, ~1 at face edges, ~1.41 at corners)
    su = 2.0 * u - 1.0
    sv = 2.0 * v - 1.0
    r_box = np.maximum(np.abs(su), np.abs(sv))
    r_rad = np.hypot(su, sv)

    # Just like the reference image: polka dots glow bright frosted white toward lower-left & bevels,
    # and soften cleanly over the central crystal-ball viewing portal!
    corner_boost = clamp01(0.35 + 0.55 * smoothstep(0.35, 1.05, r_rad) + 0.25 * clamp01(-0.5 * su + 0.5 * sv))
    dot_strength = dot_mask * corner_boost

    # Blend frosted white-pearl polka dots into the rainbow glass
    rgb = rgb * (1.0 - 0.68 * dot_strength[..., None]) + np.array([1.0, 0.99, 1.0]) * (0.68 * dot_strength[..., None])

    # Glossy rounded-bevel candy-glass specular edge highlight along all 4 face borders
    bevel_rim = smoothstep(0.76, 0.97, r_box)
    top_left_spec = smoothstep(0.68, 0.94, r_box) * clamp01(-0.45 * su - 0.55 * sv + 0.4)
    rgb = clamp01(rgb + bevel_rim[..., None] * 0.20 + top_left_spec[..., None] * 0.28)

    # Crystal-Ball Window Alpha:
    #   - Central crystal lens (r_rad < 0.55): alpha ~ 0.25 so ghostly 3D models & sprites inside shine right through!
    #   - Polka dots add crisp +0.20 frosted glass definition
    #   - Rounded rainbow bevels rise smoothly to alpha ~ 0.80 so the cube's 3D rainbow form is rich & unmistakable!
    alpha = (
        0.25
        + 0.48 * smoothstep(0.34, 0.95, r_box)
        + 0.20 * dot_strength
        + 0.12 * bevel_rim
    )
    alpha = clamp01(alpha)

    rgba = np.dstack([rgb, alpha])
    im = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
    im.save(os.path.join(STAGE_TEX, "mbox_glass.png"), "PNG", optimize=True)
    im.save(os.path.join(PROGS_DIR, "mbox_glass.png"), "PNG", optimize=True)
    print("  [OK] mbox_glass.png")


# ===========================================================================
# 3. CHUNKY CYAN-BORDERED WHITE '?' + SMOKY CRYSTAL CORE (`mbox_qmark.png`, 1024x512 RGBA)
# ===========================================================================
# Left Half  u in [0.0 .. 0.5]: Iconic Mario-Kart faceted chunky White '?' with vivid Electric Cyan-Blue outline!
# Right Half u in [0.5 .. 1.0]: Deep velvety Cosmic-Indigo Crystal-Ball Core Mist (ensures inner ghosts pop against any wall!)
def build_mbox_qmark():
    W, H = 1024, 512
    S = 512

    # --- Left 512x512: Chunky Faceted '?' Polygon with Cyan Bevel Border ---
    # Supersample at 1024x1024 for razor-sharp anti-aliased bevel edges!
    SS = 1024
    mask_outer = Image.new("L", (SS, SS), 0)
    dr_o = ImageDraw.Draw(mask_outer)

    # Chunky Mario-Kart angular '?' top hook + stem polygon (matching uploaded reference image!)
    hook_pts = [
        (235, 315),
        (205, 195),
        (330,  92),
        (695,  92),
        (825, 205),
        (810, 395),
        (615, 535),
        (605, 650),
        (405, 650),
        (412, 455),
        (582, 355),
        (592, 268),
        (430, 262),
        (395, 345),
    ]
    dot_pts = [
        (402, 718),
        (612, 718),
        (600, 912),
        (414, 912),
    ]
    dr_o.polygon(hook_pts, fill=255)
    dr_o.polygon(dot_pts, fill=255)

    arr_orig = np.array(mask_outer, dtype=np.float32) / 255.0
    # Dilate for thick electric-cyan outer border, erode for crisp pure-white inner face!
    dist_out = ndimage.distance_transform_edt(arr_orig < 0.5)
    dist_in = ndimage.distance_transform_edt(arr_orig >= 0.5)
    sdf = dist_in - dist_out  # > 0 inside white polygon, < 0 outside

    # Outer cyan border extends out to sdf = -44 px; white core begins at sdf = +8 px!
    in_total = smoothstep(-48.0, -40.0, sdf)
    in_white = smoothstep(4.0, 11.0, sdf)
    soft_glow = np.exp(-np.maximum(0.0, -sdf - 42.0) / 28.0) * 0.45

    yy_s, xx_s = np.mgrid[0:SS, 0:SS].astype(np.float32) / SS
    # Subtle faceted bevel shimmer on the cyan border (matches geometric facets in reference image!)
    facet = 0.5 + 0.5 * np.sin((xx_s * 5.0 - yy_s * 4.0) * math.pi)
    c_cyan = np.array([0.00, 0.72, 1.00], dtype=np.float32) * (1.0 - 0.35 * facet[..., None]) + np.array([0.22, 0.95, 1.00], dtype=np.float32) * (0.35 * facet[..., None])
    c_white = np.array([0.98, 0.995, 1.00], dtype=np.float32)

    q_rgb_ss = c_cyan * (1.0 - in_white[..., None]) + c_white * in_white[..., None]
    q_alpha_ss = clamp01(in_total * 0.88 + soft_glow * (1.0 - in_total))

    q_im = Image.fromarray((np.dstack([clamp01(q_rgb_ss), q_alpha_ss]) * 255).astype(np.uint8), "RGBA").resize((S, S), Image.Resampling.LANCZOS)

    # --- Right 512x512: Deep Velvety Cosmic Crystal-Ball Core Mist ---
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    su = (xx / S) * 2.0 - 1.0
    sv = (yy / S) * 2.0 - 1.0
    r = np.hypot(su, sv)
    ang = np.arctan2(sv, su)

    neb = fbm_noise(S, S, scales=(8, 18, 36, 72), weights=(0.20, 0.30, 0.30, 0.20), seed=808)
    swirl = 0.5 + 0.5 * np.sin(ang * 3.0 - r * 7.5 + neb * 1.6)

    # Deep midnight violet-indigo base with luminous crystal-ball inner rim so ghosts inside POP clearly!
    core_rgb = (
        np.array([0.025, 0.012, 0.085], dtype=np.float32)
        + swirl[..., None] * np.array([0.045, 0.085, 0.18], dtype=np.float32)
        + np.exp(-(((r - 0.78) / 0.11) ** 2))[..., None] * np.array([0.22, 0.55, 0.82], dtype=np.float32)
    )
    # Smooth spherical alpha falloff: 0.78 at crystal heart -> 0.0 at sphere rim
    core_alpha = clamp01((1.0 - smoothstep(0.42, 0.96, r)) * 0.78)
    core_im = Image.fromarray((np.dstack([clamp01(core_rgb), core_alpha]) * 255).astype(np.uint8), "RGBA")

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(q_im, (0, 0))
    out.paste(core_im, (S, 0))
    out.save(os.path.join(STAGE_TEX, "mbox_qmark.png"), "PNG", optimize=True)
    out.save(os.path.join(PROGS_DIR, "mbox_qmark.png"), "PNG", optimize=True)
    print("  [OK] mbox_qmark.png")


# ===========================================================================
# 4. 8-ROW SPECTRAL HOLOGRAM PALETTE FOR REAL 3D GAME GHOSTS (`mbox_ghost_3d.png`, 512x512 RGB)
# ===========================================================================
def build_mbox_ghost_3d():
    S = 512
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xx / S   # 0 = faint translucent ghost interior -> 1 = luminous hologram Fresnel silhouette rim!
    v = yy / S

    # 8 distinct magical crystal-ball apparition tints (one row per real 3D game model)
    tints = np.array([
        [0.22, 0.88, 1.00],  # 0: Mega Man Contraption (Electric Ice-Cyan)
        [0.72, 0.42, 1.00],  # 1: Suit Rider on Metal Bar & Wheels (Astral Violet)
        [1.00, 0.34, 0.80],  # 2: Pink Supercar (Phantom Neon Rose-Magenta)
        [0.28, 1.00, 0.68],  # 3: Squat Rider on Metal Bar & Wheels (Ectoplasm Mint-Emerald)
        [0.36, 1.00, 0.44],  # 4: NetSend 90s CRT PC (CRT Phosphor Green)
        [1.00, 0.78, 0.28],  # 5: Golden West Casino Horse (Astral Gold)
        [0.54, 0.72, 1.00],  # 6: Big-Ears 3D Sculpted Head (Celestial Periwinkle)
        [1.00, 0.56, 0.24],  # 7: Warehouse Forklift (Arcane Amber-Orange)
    ], dtype=np.float32)

    row_idx = np.clip((v * 8.0).astype(np.int32), 0, 7)
    local_v = (v * 8.0) % 1.0
    base_tint = tints[row_idx]

    # Fine crystal-ball hologram scanlines + luminous ghostly body & crisp rim so 3D silhouettes read at a glance!
    scan = 0.88 + 0.12 * np.sin(local_v * 28.0 * math.pi)
    rim_boost = (u ** 2.0)
    core_glow = 0.20 + 0.54 * (u ** 0.80)
    rgb = (base_tint * core_glow[..., None] + (0.45 * base_tint + 0.55) * (0.55 * rim_boost[..., None])) * scan[..., None]

    im = Image.fromarray((clamp01(rgb) * 255).astype(np.uint8), "RGB")
    im.save(os.path.join(STAGE_TEX, "mbox_ghost_3d.png"), "PNG", optimize=True)
    im.save(os.path.join(PROGS_DIR, "mbox_ghost_3d.png"), "PNG", optimize=True)
    print("  [OK] mbox_ghost_3d.png")


# ===========================================================================
# 5. REAL BAKERSFIELDQUAKE SPRITES -> GHOSTLY CRYSTAL-BALL ATLAS (`mbox_ghost_spr.png`, 1024x512 RGB)
# ===========================================================================
def _read_spr32_frame(spr_path, frame_idx=0):
    raw = open(spr_path, "rb").read()
    ident, ver, stype, rad, maxw, maxh, nf, synch, flags = struct.unpack("<4siifiiifi", raw[:36])
    assert ident == b"IDSP" and ver == 32
    ofs = 36
    for i in range(nf):
        ft, ox, oy, w, h = struct.unpack("<iiiii", raw[ofs:ofs + 20])
        ofs += 20
        nbytes = w * h * 4
        if i == min(frame_idx, nf - 1):
            return Image.frombytes("RGBA", (w, h), raw[ofs:ofs + nbytes])
        ofs += nbytes
    raise RuntimeError(spr_path)


def _stylize_ghost_tile(im_rgba, tint_rgb, tile_sz=256):
    """Transforms a real game RGBA sprite into an ethereal glowing crystal-ball apparition on pure black."""
    arr = np.array(im_rgba.convert("RGBA"), dtype=np.float32) / 255.0
    a = arr[..., 3]
    ys, xs = np.where(a > 0.06)
    if len(xs) > 4:
        pad = 4
        x0, x1 = max(0, xs.min() - pad), min(arr.shape[1], xs.max() + pad + 1)
        y0, y1 = max(0, ys.min() - pad), min(arr.shape[0], ys.max() + pad + 1)
        im_crop = im_rgba.crop((x0, y0, x1, y1))
    else:
        im_crop = im_rgba

    # Fit inside 74% of tile_sz so aura & crystal mist fade cleanly to zero before tile border!
    target = int(tile_sz * 0.74)
    cw, ch = im_crop.size
    sc = min(target / max(1, cw), target / max(1, ch))
    nw, nh = max(1, round(cw * sc)), max(1, round(ch * sc))
    resample = Image.Resampling.NEAREST if max(cw, ch) <= 128 else Image.Resampling.LANCZOS
    im_fit = im_crop.resize((nw, nh), resample)

    canvas = Image.new("RGBA", (tile_sz, tile_sz), (0, 0, 0, 0))
    canvas.paste(im_fit, ((tile_sz - nw) // 2, (tile_sz - nh) // 2))

    c_arr = np.array(canvas, dtype=np.float32) / 255.0
    rgb = c_arr[..., :3]
    alpha = c_arr[..., 3]

    # Luminance + edge detection for ghostly ectoplasm rim highlight
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    lum_boost = clamp01(0.22 + 1.05 * (lum ** 0.78))

    # Outer spectral aura + edge rim via Gaussian blur of alpha
    aura_wide = ndimage.gaussian_filter(alpha, sigma=9.0)
    aura_tight = ndimage.gaussian_filter(alpha, sigma=2.6)
    edge_rim = np.abs(alpha - ndimage.gaussian_filter(alpha, sigma=1.6)) * 2.4

    yy, xx = np.mgrid[0:tile_sz, 0:tile_sz].astype(np.float32)
    su = (xx / tile_sz) * 2.0 - 1.0
    sv = (yy / tile_sz) * 2.0 - 1.0
    r = np.hypot(su, sv)
    # Ghostly horizontal shimmer waves + radial crystal-ball vignette (strictly 0 at border!)
    shimmer = 0.88 + 0.12 * np.sin(yy * (2.0 * math.pi / 6.0))
    vignette = 1.0 - smoothstep(0.68, 0.96, r)

    tint = np.array(tint_rgb, dtype=np.float32)
    # Preserve 46% recognizable sprite colors + 54% luminous ghostly ectoplasm tint!
    ghost_body = (0.46 * rgb + 0.54 * lum_boost[..., None] * tint) * alpha[..., None] * 0.86
    ghost_halo = tint * (0.30 * aura_wide[..., None] + 0.24 * aura_tight[..., None])
    ghost_edge = (0.45 * tint + 0.55) * (0.55 * edge_rim[..., None])

    out_rgb = clamp01((ghost_body + ghost_halo + ghost_edge) * shimmer[..., None] * vignette[..., None])
    return Image.fromarray((out_rgb * 255).astype(np.uint8), "RGB")


def build_mbox_ghost_sprites():
    TILE = 256
    atlas = Image.new("RGB", (TILE * 4, TILE * 2), (0, 0, 0))

    sprite_specs = [
        # (col, row, loader, tint_rgb, label)
        (0, 0, ("png", "wheelman_sprite/wm_d0_f0.png"),   (0.28, 0.92, 1.00), "Wheelman (Front)"),
        (1, 0, ("png", "jesskart_sprite/jesskart_01.png"),(1.00, 0.45, 0.88), "JessKart Racer"),
        (2, 0, ("png", "scissor_sprite/scissor_01.png"),  (0.66, 0.48, 1.00), "Scissor Man"),
        (3, 0, ("png", "earhead_sprite/earhead_02.png"),  (0.35, 1.00, 0.74), "Earhead"),
        (0, 1, ("png", "progs/pickle_00.png"),            (0.36, 1.00, 0.42), "Pickle Surprise"),
        (1, 1, ("spr", "progs/fr_rob.spr32", 0),          (1.00, 0.80, 0.32), "Friend Rob"),
        (2, 1, ("spr", "progs/fr_johnhand.spr32", 0),     (0.32, 0.82, 1.00), "John Wave Hand"),
        (3, 1, ("png", "wheelman_sprite/wm_d2_f2.png"),   (0.95, 0.52, 1.00), "Wheelman (Rolling)"),
    ]

    for col_i, row_i, spec, tint, label in sprite_specs:
        if spec[0] == "png":
            im_src = Image.open(os.path.join(MOD_ROOT, spec[1])).convert("RGBA")
        else:
            im_src = _read_spr32_frame(os.path.join(MOD_ROOT, spec[1]), spec[2])
        tile_im = _stylize_ghost_tile(im_src, tint, TILE)
        atlas.paste(tile_im, (col_i * TILE, row_i * TILE))

    atlas.save(os.path.join(STAGE_TEX, "mbox_ghost_spr.png"), "PNG", optimize=True)
    atlas.save(os.path.join(PROGS_DIR, "mbox_ghost_spr.png"), "PNG", optimize=True)
    print("  [OK] mbox_ghost_spr.png (8 real BakersfieldQuake sprites stylized!)")


# ===========================================================================
# 6. 4-QUADRANT ADDITIVE MAGIC VFX ATLAS (`mbox_fx.png`, 512x512 RGB)
# ===========================================================================
# Q0 (Top-Left,     u 0..0.5, v 0..0.5): Telekinetic Levitation Wisps & Arcane Ring
# Q1 (Top-Right,    u 0.5..1, v 0..0.5): 8-Point Prismatic Starlight Sparkle Mote
# Q2 (Bottom-Left,  u 0..0.5, v 0.5..1): GRAB-CHARGE SUPERNOVA GLOW CORONA (intense rainbow-cyan-white blaze!)
# Q3 (Bottom-Right, u 0.5..1, v 0.5..1): Thrown Box Rainbow-Cyan Slipstream Comet Ribbon
def build_mbox_fx():
    Q = 256
    atlas = np.zeros((Q * 2, Q * 2, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:Q, 0:Q].astype(np.float32)
    u = xx / Q
    v = yy / Q
    su = u * 2.0 - 1.0
    sv = v * 2.0 - 1.0
    r = np.hypot(su, sv)
    ang = np.arctan2(sv, su)

    # Q0: Telekinetic Levitation Wisps (vertical rising rainbow-cyan plasma filaments)
    wisp1 = np.exp(-(((su - 0.24 * np.sin(v * 2.0 * math.pi)) / 0.18) ** 2))
    wisp2 = np.exp(-(((su + 0.22 * np.cos(v * 2.0 * math.pi)) / 0.16) ** 2))
    v_env = smoothstep(0.02, 0.24, v) * (1.0 - smoothstep(0.74, 0.98, v))
    q0_i = clamp01((0.65 * wisp1 + 0.55 * wisp2) * v_env) * (1.0 - smoothstep(0.75, 0.98, np.abs(su)))
    q0_col = rainbow_palette(v * 0.85 + 0.20) * 0.65 + np.array([0.25, 0.85, 1.0]) * 0.35
    atlas[0:Q, 0:Q] = clamp01(q0_col * q0_i[..., None] * 0.72)

    # Q1: Crisp 8-Point Magical Sparkle Star
    sp_main = np.exp(-((su / 0.08) ** 2)) * np.exp(-((sv / 0.68) ** 2)) + np.exp(-((sv / 0.08) ** 2)) * np.exp(-((su / 0.68) ** 2))
    sp_diag = (
        np.exp(-(((su + sv) * 0.707 / 0.07) ** 2)) * np.exp(-(((su - sv) * 0.707 / 0.46) ** 2))
        + np.exp(-(((su - sv) * 0.707 / 0.07) ** 2)) * np.exp(-(((su + sv) * 0.707 / 0.46) ** 2))
    )
    sp_core = np.exp(-((r / 0.22) ** 2))
    rad_fade = 1.0 - smoothstep(0.65, 0.97, r)
    q1_i = clamp01((0.85 * sp_main + 0.55 * sp_diag + 1.1 * sp_core) * rad_fade)
    q1_col = np.array([0.55, 0.92, 1.0]) * (1.0 - sp_core[..., None]) + np.array([1.0, 1.0, 1.0]) * sp_core[..., None]
    atlas[0:Q, Q:2 * Q] = clamp01(q1_col * q1_i[..., None])

    # Q2: GRAB-CHARGE SUPERNOVA GLOW CORONA (radiant outer starburst rays & prismatic ring around the box!)
    rays = np.maximum(0.0, np.cos(ang * 8.0)) ** 2.2 + 0.65 * (np.maximum(0.0, np.sin(ang * 5.0 + 0.5)) ** 3.0)
    halo_ring = np.exp(-(((r - 0.52) / 0.15) ** 2))
    inner_soft = np.exp(-((r / 0.42) ** 2)) * 0.42
    ray_burst = smoothstep(0.18, 0.42, r) * np.exp(-(((r - 0.48) / 0.32) ** 2)) * rays
    q2_fade = 1.0 - smoothstep(0.76, 0.98, r)
    q2_prism = rainbow_palette((ang / (2.0 * math.pi)) % 1.0)
    q2_rgb = (
        q2_prism * (0.78 * halo_ring[..., None] + 0.72 * ray_burst[..., None])
        + np.array([0.45, 0.95, 1.0]) * (0.75 * ray_burst[..., None])
        + np.array([0.92, 0.98, 1.0]) * inner_soft[..., None]
    ) * q2_fade[..., None]
    atlas[Q:2 * Q, 0:Q] = clamp01(q2_rgb)

    # Q3: Thrown Box Rainbow-Cyan Slipstream Comet Ribbon (u = 0 nose -> u = 1 trailing wake)
    long_env = smoothstep(0.01, 0.14, u) * (1.0 - smoothstep(0.35, 0.98, u))
    cross_wide = np.exp(-((sv / 0.48) ** 2))
    cross_core = np.exp(-((sv / 0.16) ** 2))
    c_rib = rainbow_palette(u * 1.15 + 0.15 * sv)
    q3_rgb = (c_rib * 0.62 * cross_wide[..., None] + np.array([0.78, 0.98, 1.0]) * 0.85 * cross_core[..., None]) * long_env[..., None]
    atlas[Q:2 * Q, Q:2 * Q] = clamp01(q3_rgb)

    im = Image.fromarray((clamp01(atlas) * 255).astype(np.uint8), "RGB")
    im.save(os.path.join(STAGE_TEX, "mbox_fx.png"), "PNG", optimize=True)
    im.save(os.path.join(PROGS_DIR, "mbox_fx.png"), "PNG", optimize=True)
    print("  [OK] mbox_fx.png")


def build_glb_alpha_variants():
    """Creates RGBA straight-alpha emissive textures for standard GLTF 2.0 / GLB viewers."""
    for base_fn in ("mbox_ghost_3d", "mbox_ghost_spr", "mbox_fx"):
        im_rgb = Image.open(os.path.join(STAGE_TEX, f"{base_fn}.png")).convert("RGB")
        arr = np.array(im_rgb, dtype=np.float32) / 255.0
        alpha = clamp01(np.max(arr, axis=2) * 1.45)
        safe_rgb = np.where(alpha[..., None] > 0.02, clamp01(arr / np.maximum(alpha[..., None], 0.18)), 0.0)
        rgba_u8 = (np.dstack([safe_rgb, alpha]) * 255).astype(np.uint8)
        Image.fromarray(rgba_u8, "RGBA").save(os.path.join(STAGE_TEX, f"{base_fn}_glb.png"), "PNG", optimize=True)
    print("  [OK] *_glb.png RGBA emissive variants")


def main():
    os.makedirs(STAGE_TEX, exist_ok=True)
    os.makedirs(PROGS_DIR, exist_ok=True)
    print("Generating Mystery Box textures & real game sprite ghostly atlas...")
    build_mbox_hand()
    build_mbox_glass()
    build_mbox_qmark()
    build_mbox_ghost_3d()
    build_mbox_ghost_sprites()
    build_mbox_fx()
    build_glb_alpha_variants()
    print("All Mystery Box textures generated successfully!")


if __name__ == "__main__":
    main()
