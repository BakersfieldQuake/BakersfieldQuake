"""Generates high-resolution 360° wrap-around PBR/photo textures for the
Crazy Rubber Finger Character & Giant Floppy Rubber Index Finger in BakersfieldQuake.

Textures written to source/mm_tools/ref/rubber_finger/tex/:
  - head_ooo.png            (Expression A: Wide Bug-Eyed 'OOO' Face from Photo 1)
  - head_twist.png          (Expression B: Bug-Eyed Sideways-Twisted Beard Mouth from Photo 2)
  - head_maniac.png         (Expression C: Unhinged Jaw-Dropped Maniac Scream + Pinpoint Bug Eyes)
  - henley_tex.png          (Real sampled Charcoal-Heather 2-Button Henley Shirt + Placket)
  - jeans_tex.png           (Dark Indigo Twill Jeans + Leather Belt + Stitched Back Pockets)
  - rubber_finger_tex.png   (Giant Molded Peach-Tan Rubber Index Finger w/ Fingernail & Knuckle Creases)
  - skin_arm_tex.png        (Warm Caucasian Male Forearm & Hand Skin Texture)
"""

from __future__ import annotations

import math
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(HERE, "ref", "rubber_finger")
TEX_DIR = os.path.join(REF_DIR, "tex")
os.makedirs(TEX_DIR, exist_ok=True)


def make_seamless_tile(patch_rgb: np.ndarray, out_h: int = 512, out_w: int = 512) -> np.ndarray:
    """Creates a 100% seamless tileable texture from a real photo swatch via mirror-blending."""
    p = cv2.resize(patch_rgb, (256, 256), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    # 2x2 mirrored tile eliminates harsh edges, then soft cross-blend with shifted copy removes symmetry
    top = np.concatenate([p, p[:, ::-1, :]], axis=1)
    quad = np.concatenate([top, top[::-1, :, :]], axis=0)  # 512x512 seamless!
    shifted = np.roll(np.roll(quad, 128, axis=0), 128, axis=1)
    yg, xg = np.mgrid[0:512, 0:512].astype(np.float32)
    wx = 0.5 - 0.5 * np.cos(2.0 * math.pi * xg / 512.0)
    wy = 0.5 - 0.5 * np.cos(2.0 * math.pi * yg / 512.0)
    w = np.clip(wx * wy * 0.65, 0.0, 1.0)[..., None]
    blended = quad * (1.0 - w) + shifted * w
    if (out_h, out_w) != (512, 512):
        blended = cv2.resize(blended, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    return np.clip(np.round(blended), 0, 255).astype(np.uint8)


def synthesize_maniac_scream_portrait(ooo_rgb: np.ndarray) -> np.ndarray:
    """Builds Expression C ('UNHINGED MANIAC SCREAM'): drops his bearded lower jaw & opens his 'OOO' mouth wide
    while bulging both icy-blue eyes 20% wider for maximum manic energy!"""
    H, W = ooo_rgb.shape[:2]
    out = ooo_rgb.astype(np.float32).copy()
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    # 1. Bulge both blue eyes slightly outward from their iris centers (84, 166) and (158, 165)
    map_x = xg.copy()
    map_y = yg.copy()
    for ex, ey in ((84.0, 166.0), (158.0, 165.0)):
        dx = xg - ex
        dy = yg - ey
        r = np.hypot(dx / 24.0, dy / 18.0)
        bulge = np.clip(1.0 - r, 0.0, 1.0) ** 1.5
        # Inverse map < 1 magnifies eye!
        scale = 1.0 - 0.24 * bulge
        map_x = np.where(r < 1.0, ex + dx * scale, map_x)
        map_y = np.where(r < 1.0, ey + dy * scale, map_y)

    # Arch eyebrows slightly upward in manic shock (y ~ 138)
    brow_zone = np.exp(-(((xg - 121.0) / 72.0) ** 2 + ((yg - 134.0) / 18.0) ** 2))
    map_y += 6.5 * brow_zone

    # 2. Stretch open his mouth & drop lower beard jaw (mouth center ~ (146, 268))
    jaw_w = np.exp(-((xg - 136.0) / 56.0) ** 2) * (1.0 / (1.0 + np.exp(-(yg - 262.0) / 8.0))) * (1.0 / (1.0 + np.exp((yg - 368.0) / 14.0)))
    map_y -= 22.0 * jaw_w

    warped = cv2.remap(out, map_x, map_y, interpolation=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

    # Deepen dark oral cavity slightly inside expanded mouth (natural, no synthetic line)
    mouth_dark = np.exp(-(((xg - 145.0) / 18.0) ** 2 + ((yg - 280.0) / 16.0) ** 2))
    warped = warped * (1.0 - 0.45 * mouth_dark[..., None]) + np.array([24.0, 11.0, 13.0])[None, None, :] * (0.45 * mouth_dark[..., None])

    return np.clip(np.round(warped), 0, 255).astype(np.uint8)


def build_head_atlas(portrait_rgb: np.ndarray, out_path: str) -> None:
    """Builds a 1024x1024 cylindrical wrap-around head texture:
      u in [0, 1]: azimuth phi = (u - 0.5) * 2*pi  (u=0.5 is 0° Front face, u=0.25 Left ear, u=0.75 Right ear, u=0/1 Back)
      v in [0, 1]: v=0 is bottom of neck/beard base (y_src=392), v=1 is top of hair crown (y_src=24)
                   Note: PIL image row 0 is TOP (v=1), row 1023 is BOTTOM (v=0)!
    """
    S = 1024
    row_g, col_g = np.mgrid[0:S, 0:S].astype(np.float32)
    u = col_g / float(S - 1)                # 0 .. 1 around head
    v = 1.0 - row_g / float(S - 1)          # 1 at top crown, 0 at neck bottom
    phi = (u - 0.5) * 2.0 * math.pi         # -pi .. +pi (0 = Front)

    # 1. Base background layers from 100% pure interior DSLR swatches (ZERO olive wall!):
    #    - Pure dark hair core [50:76, 100:150] + vertical strand grain
    hair_core = make_seamless_tile(portrait_rgb[50:76, 100:150], S, S).astype(np.float32)
    rng_h = np.random.default_rng(19)
    strand = cv2.GaussianBlur(rng_h.normal(0.0, 1.0, (S // 4, S)).astype(np.float32), (3, 21), 0.0)
    strand = cv2.resize(strand, (S, S), interpolation=cv2.INTER_LINEAR)
    hair_tile = np.clip(hair_core * 0.85 + strand[..., None] * 6.5, 10.0, 82.0)

    beard_tile = make_seamless_tile(portrait_rgb[262:338, 62:122], S, S).astype(np.float32)
    skin_patch = portrait_rgb[88:124, 96:158].astype(np.float32)
    skin_mean = np.median(skin_patch.reshape(-1, 3), axis=0)
    skin_tile = make_seamless_tile(portrait_rgb[88:124, 96:158], S, S).astype(np.float32)
    skin_tile = skin_tile * 0.30 + skin_mean[None, None, :] * 0.70

    abs_deg = np.abs(np.degrees(phi))
    hair_bot_v = np.interp(abs_deg, [0.0, 52.0, 82.0, 108.0, 145.0, 180.0], [0.85, 0.78, 0.54, 0.32, 0.19, 0.17])
    w_hair = np.clip((v - hair_bot_v) / 0.055, 0.0, 1.0)[..., None]

    beard_top_v = np.interp(abs_deg, [0.0, 45.0, 78.0, 96.0, 110.0], [0.44, 0.45, 0.54, 0.56, 0.0])
    w_beard_phi = np.clip((98.0 - abs_deg) / 10.0, 0.0, 1.0)
    w_beard_v = np.clip((beard_top_v - v) / 0.05, 0.0, 1.0) * np.clip((v - 0.08) / 0.05, 0.0, 1.0)
    w_beard = (w_beard_phi * w_beard_v)[..., None]

    ear_d = np.hypot((abs_deg - 94.0) / 9.5, (v - 0.50) / 0.085)
    ear_concha = np.clip(1.0 - np.hypot((abs_deg - 95.0) / 4.8, (v - 0.49) / 0.045), 0.0, 1.0)
    ear_rim = np.clip(1.0 - np.abs(ear_d - 0.85) / 0.22, 0.0, 1.0) * (ear_d <= 1.1)

    base = skin_tile.copy()
    neck_shade = 0.82 + 0.18 * np.clip(v / 0.16, 0.0, 1.0)
    base *= neck_shade[..., None]
    base = base * (1.0 - 0.28 * ear_concha[..., None]) + (base * 1.10) * (0.18 * ear_rim[..., None])
    base = base * (1.0 - w_beard) + beard_tile * w_beard
    base = base * (1.0 - w_hair) + hair_tile * w_hair

    # 2. Project crisp front DSLR portrait ONLY inside the portrait's real head/hair/beard silhouette (never olive wall!)
    ph, pw = portrait_rgb.shape[:2]
    py_g, px_g = np.mgrid[0:ph, 0:pw].astype(np.float32)
    wall_ref = np.median(portrait_rgb[20:320, 260:400], axis=(0, 1)).astype(np.float32)
    wall_dist = np.linalg.norm(portrait_rgb.astype(np.float32) - wall_ref[None, None, :], axis=-1)
    # Tight anatomical head half-width envelope in portrait pixels so wall outside temples/crown is 100% excluded
    env_rx = np.interp(py_g, [24.0, 55.0, 95.0, 165.0, 285.0, 355.0, 400.0], [34.0, 52.0, 64.0, 72.0, 77.0, 68.0, 62.0])
    in_env = np.clip((env_rx - np.abs(px_g - 122.0)) / 9.0, 0.0, 1.0)
    not_wall = np.clip((wall_dist - 14.0) / 14.0, 0.0, 1.0)
    # Inside core face (abs(x-122) < env_rx - 12 and y > 72), keep 100% even if shadow matches wall tone
    core_face = (np.abs(px_g - 122.0) < (env_rx - 10.0)) & (py_g > 68.0)
    p_valid = cv2.GaussianBlur(np.where(core_face, 1.0, in_env * not_wall).astype(np.float32), (11, 11), 2.5)

    sin_p = np.sin(np.clip(phi, -math.pi * 0.5, math.pi * 0.5))
    horiz_t = 0.68 * sin_p + 0.32 * (phi / (math.pi * 0.5))
    src_x = (122.0 + horiz_t * 76.0).astype(np.float32)
    src_y = (24.0 + (1.0 - v) * (392.0 - 24.0)).astype(np.float32)

    front_proj = cv2.remap(portrait_rgb.astype(np.float32), src_x, src_y, interpolation=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    proj_valid = cv2.remap(p_valid, src_x, src_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    max_phi_deg = np.interp(v, [0.0, 0.15, 0.78, 0.94, 1.0], [54.0, 72.0, 74.0, 46.0, 34.0])
    w_front = np.clip((max_phi_deg - abs_deg) / 16.0, 0.0, 1.0)
    w_front = ((0.5 - 0.5 * np.cos(math.pi * w_front)) * proj_valid)[..., None]

    atlas = base * (1.0 - w_front) + front_proj * w_front
    Image.fromarray(np.clip(np.round(atlas), 0, 255).astype(np.uint8), "RGB").save(out_path)


def build_henley_texture(ooo_rgb: np.ndarray, out_path: str, sleeve_out_path: str | None = None) -> None:
    """Builds a 1024x1024 dark charcoal-heather 2-button henley shirt texture using real sampled knit from Photo 1,
    plus a matching placket-free sleeve texture with ribbed forearm cuffs!"""
    S = 1024
    knit = make_seamless_tile(ooo_rgb[430:540, 210:345], S, S).astype(np.float32)
    blur = cv2.GaussianBlur(knit, (0, 0), 36.0)
    mean_col = knit.mean(axis=(0, 1), keepdims=True)
    knit = np.clip((knit - blur + mean_col * 0.80) * 0.86, 14.0, 145.0)

    if sleeve_out_path is not None:
        slv_im = Image.fromarray(knit.astype(np.uint8), "RGB")
        sd = ImageDraw.Draw(slv_im)
        sd.rectangle((0, S - 56, S, S), fill=(30, 33, 37))
        for xx in range(0, S, 8):
            sd.line([(xx, S - 56), (xx, S)], fill=(22, 24, 28), width=3)
        slv_im.save(sleeve_out_path)

    im = Image.fromarray(knit.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)

    cx = S // 2
    d.rectangle((0, 0, S, 42), fill=(30, 33, 37))
    for xx in range(0, S, 6):
        d.line([(xx, 0), (xx, 42)], fill=(22, 24, 28), width=2)

    d.rounded_rectangle((cx - 26, 0, cx + 26, 335), radius=8, fill=(26, 29, 33), outline=(18, 20, 24), width=4)
    d.polygon([(cx - 18, 0), (cx + 18, 0), (cx + 4, 115), (cx - 4, 115)], fill=(112, 82, 68))
    d.rectangle((cx - 16, 112, cx + 20, 332), fill=(33, 36, 41), outline=(20, 22, 26), width=3)
    for by in (175, 265):
        d.ellipse((cx - 8, by - 8, cx + 8, by + 8), fill=(182, 188, 194), outline=(48, 52, 58), width=2)
        d.ellipse((cx - 4, by - 4, cx + 4, by + 4), outline=(135, 142, 148), width=1)

    im.save(out_path)


def build_jeans_texture(out_path: str) -> None:
    """Builds a 1024x1024 realistic dark slate-indigo denim twill texture with leather belt, seams & back pockets."""
    S = 1024
    rng = np.random.default_rng(42)
    yg, xg = np.mgrid[0:S, 0:S].astype(np.float32)

    twill = 0.5 + 0.5 * np.sin((xg * 1.4 + yg * 1.4) * 0.9)
    slub_v = cv2.GaussianBlur(rng.normal(0.0, 1.0, (S, S // 4)).astype(np.float32), (3, 19), 0.0)
    slub_v = cv2.resize(slub_v, (S, S), interpolation=cv2.INTER_LINEAR)

    base = np.zeros((S, S, 3), dtype=np.float32)
    base[..., 0] = 24.0 + 7.0 * twill + 4.5 * slub_v
    base[..., 1] = 32.0 + 8.5 * twill + 5.5 * slub_v
    base[..., 2] = 48.0 + 11.0 * twill + 7.0 * slub_v

    u = xg / float(S - 1)
    v = 1.0 - yg / float(S - 1)
    fade = np.exp(-(((u - 0.5) / 0.20) ** 2 + ((v - 0.55) / 0.22) ** 2))
    base += fade[..., None] * np.array([11.0, 14.0, 18.0])[None, None, :]

    im = Image.fromarray(np.clip(np.round(base), 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)

    d.rectangle((0, 0, S, 74), fill=(32, 22, 15), outline=(16, 11, 8), width=4)
    cx = S // 2
    d.rounded_rectangle((cx - 38, 8, cx + 38, 66), radius=7, outline=(145, 150, 158), width=7)

    stitch_col = (118, 86, 42)
    d.line([(cx, 76), (cx, 240)], fill=(16, 22, 34), width=4)
    d.arc((cx - 28, 76, cx + 28, 250), start=0, end=92, fill=stitch_col, width=2)
    for sx in (S // 4, 3 * S // 4):
        d.line([(sx, 76), (sx, S)], fill=stitch_col, width=2)

    for px in (int(S * 0.12), int(S * 0.88)):
        py = 148
        pw, ph = 70, 112
        pts = [(px - pw, py), (px + pw, py), (px + int(pw * 0.86), py + ph - 24), (px, py + ph), (px - int(pw * 0.86), py + ph - 24)]
        d.polygon(pts, fill=(22, 30, 45), outline=stitch_col, width=3)
        d.line([(px - pw + 10, py + 46), (px, py + 62), (px + pw - 10, py + 46)], fill=stitch_col, width=2)

    im.save(out_path)


def build_rubber_finger_texture(out_path: str) -> None:
    """Builds a 1024x1024 rich, high-contrast Novelty Giant Flesh-Tan Rubber Index Finger texture
    calibrated so fingernail, lunula, knuckle folds & grip rings read crystal-clear under studio 3D lighting!"""
    S = 1024
    rng = np.random.default_rng(7)
    yg, xg = np.mgrid[0:S, 0:S].astype(np.float32)
    u = xg / float(S - 1)           # 0.5 = dorsal (nail & knuckles), 0/1 = palmar
    v = 1.0 - yg / float(S - 1)     # 0 = grip base, 1 = fingertip

    grain = cv2.GaussianBlur(rng.normal(0.0, 1.0, (S // 2, S // 2)).astype(np.float32), (5, 5), 1.1)
    grain = cv2.resize(grain, (S, S), interpolation=cv2.INTER_CUBIC)

    r = np.full((S, S), 214.0, dtype=np.float32) + grain * 3.0
    g = np.full((S, S), 160.0, dtype=np.float32) + grain * 2.5
    b = np.full((S, S), 132.0, dtype=np.float32) + grain * 2.2

    for kv, kw in ((0.42, 0.070), (0.69, 0.060)):
        blush = np.exp(-(((u - 0.5) / 0.25) ** 2 + ((v - kv) / kw) ** 2))
        r += 6.0 * blush
        g -= 18.0 * blush
        b -= 20.0 * blush

    tip_blush = np.clip((v - 0.83) / 0.15, 0.0, 1.0)
    r += 4.0 * tip_blush
    g -= 14.0 * tip_blush
    b -= 16.0 * tip_blush

    palmar_w = np.clip(1.0 - np.minimum(u, 1.0 - u) / 0.26, 0.0, 1.0)
    r += 8.0 * palmar_w
    g += 7.0 * palmar_w
    b += 6.0 * palmar_w

    for su in (0.25, 0.75):
        seam = np.exp(-((u - su) / 0.005) ** 2) * (v > 0.12) * (v < 0.96)
        r -= 24.0 * seam
        g -= 24.0 * seam
        b -= 22.0 * seam

    rgb = np.dstack([r, g, b])
    im = Image.fromarray(np.clip(np.round(rgb), 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)

    cx = S // 2
    for kv, rx_px, n_folds in ((0.42, 178, 4), (0.69, 156, 3)):
        ky = int(round((1.0 - kv) * S))
        for fi in range(-n_folds // 2, n_folds // 2 + 1):
            fy = ky + fi * 14
            ry_arc = 20 + abs(fi) * 8
            w_px = int(rx_px * (1.0 - 0.11 * abs(fi)))
            d.arc((cx - w_px, fy - ry_arc, cx + w_px, fy + ry_arc), start=192, end=348, fill=(128, 82, 64), width=7)
            d.arc((cx - w_px, fy - ry_arc + 6, cx + w_px, fy + ry_arc + 6), start=198, end=342, fill=(236, 188, 160), width=4)
            d.arc((cx - w_px, fy - ry_arc, cx + w_px, fy + ry_arc), start=12, end=168, fill=(134, 86, 68), width=6)

    for kv in (0.42, 0.69):
        ky = int(round((1.0 - kv) * S))
        for dy_c, col in ((-6, (126, 80, 62)), (0, (234, 186, 158)), (7, (132, 86, 68))):
            d.line([(0, ky + dy_c), (int(S * 0.19), ky + dy_c + 9)], fill=col, width=6)
            d.line([(int(S * 0.81), ky + dy_c + 9), (S, ky + dy_c)], fill=col, width=6)

    nx0, nx1 = cx - 132, cx + 132
    ny0 = int(round((1.0 - 0.968) * S))
    ny1 = int(round((1.0 - 0.778) * S))
    d.rounded_rectangle((nx0 - 10, ny0 - 8, nx1 + 10, ny1 + 10), radius=56, fill=(124, 78, 62))
    d.rounded_rectangle((nx0, ny0, nx1, ny1), radius=50, fill=(236, 194, 178), outline=(148, 98, 80), width=6)
    d.pieslice((nx0 + 24, ny1 - 62, nx1 - 24, ny1 + 38), start=180, end=360, fill=(250, 234, 224))
    d.arc((nx0 - 6, ny1 - 68, nx1 + 6, ny1 + 8), start=10, end=170, fill=(122, 76, 60), width=9)
    d.arc((nx0 + 4, ny0 + 2, nx1 - 4, ny0 + 82), start=192, end=348, fill=(252, 240, 228), width=16)
    d.rounded_rectangle((cx - 58, ny0 + 20, cx - 28, ny1 - 24), radius=12, fill=(255, 245, 238))

    by0 = int(round((1.0 - 0.14) * S))
    d.rectangle((0, by0, S, S), fill=(192, 142, 116))
    for ry in range(by0 + 10, S - 8, 22):
        d.line([(0, ry), (S, ry)], fill=(128, 86, 68), width=7)
        d.line([(0, ry + 7), (S, ry + 7)], fill=(230, 182, 154), width=4)

    im = im.filter(ImageFilter.SMOOTH_MORE)
    im.save(out_path)


def build_arm_skin_texture(ooo_rgb: np.ndarray, out_path: str) -> None:
    S = 512
    skin_patch = ooo_rgb[88:124, 96:158].astype(np.float32) * 0.86
    med = np.median(skin_patch.reshape(-1, 3), axis=0)
    tile = make_seamless_tile(ooo_rgb[88:124, 96:158], S, S).astype(np.float32) * 0.86
    tile = np.clip(tile * 0.28 + med[None, None, :] * 0.72, 0, 255).astype(np.uint8)
    Image.fromarray(tile, "RGB").save(out_path)


def main() -> None:
    ooo = np.array(Image.open(os.path.join(REF_DIR, "ref_face_ooo.png")).convert("RGB"))
    tws = np.array(Image.open(os.path.join(REF_DIR, "ref_face_twist.png")).convert("RGB"))
    man = synthesize_maniac_scream_portrait(ooo)
    Image.fromarray(man, "RGB").save(os.path.join(REF_DIR, "ref_face_maniac.png"))

    build_head_atlas(ooo, os.path.join(TEX_DIR, "head_ooo.png"))
    build_head_atlas(tws, os.path.join(TEX_DIR, "head_twist.png"))
    build_head_atlas(man, os.path.join(TEX_DIR, "head_maniac.png"))
    build_henley_texture(
        ooo,
        os.path.join(TEX_DIR, "henley_tex.png"),
        sleeve_out_path=os.path.join(TEX_DIR, "henley_sleeve_tex.png"),
    )
    build_jeans_texture(os.path.join(TEX_DIR, "jeans_tex.png"))
    build_rubber_finger_texture(os.path.join(TEX_DIR, "rubber_finger_tex.png"))
    build_arm_skin_texture(ooo, os.path.join(TEX_DIR, "skin_arm_tex.png"))
    print("Generated all PBR/photo wrap textures in:", TEX_DIR)


if __name__ == "__main__":
    main()
