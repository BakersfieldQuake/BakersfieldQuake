"""Full 360° 8-Direction Monster Rigging, Expression Grafting, Cloth/Limb Warping,
and 5-Animation Synthesis Engine for the Pink Flamingo Bathrobe Monster ('Flamingo Fiend').

5 Hilarious Monster Animations:
  1. monster_idle       (8 dirs x 8 frames)  - Heavy feral crouch-breathing, glowing red eyes over
                                               Clubmaster sunglasses, 2 fanged pocket-flamingos snapping!
  2. berserker_charge   (8 dirs x 8 frames)  - Barefoot 3 AM berserker sprint, arms flung wide, roaring
                                               monster jaw, billowing pink robe hem, dust & pink feathers!
  3. robe_flash_laser   (8 dirs x 12 frames) - Whips pink flamingo robe wide like giant bat-wings to reveal
                                               yellow red-heart boxers + fires blinding hot-pink Chest-Hair
                                               Mega-Laser & expanding neon shockwave rings!
  4. flamingo_attack    (8 dirs x 12 frames) - Sloshes '#1 MONSTER' hot coffee mug while swinging a fanged
                                               plastic lawn flamingo & launching a laser-eyed flamingo missile!
  5. flamingo_gib_death (24 frames, 4-Act)   - Crooked-sunglasses shock swell -> Quake fireball + 48 pink
                                               feathers + meaty gibs + flying flamingos -> bouncing severed
                                               bearded head -> smoking crumpled pink bathrobe & sunglasses!
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

CUR_DIR = Path(__file__).resolve().parent
TOOLS_DIR = CUR_DIR.parent
MOD_DIR = TOOLS_DIR.parent.parent

for p in (str(CUR_DIR), str(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from paul_dennis_rig import (
    alpha_over,
    extend_top_upward,
    mirror_canvas_horiz,
    sample_run_profile,
    seg_dist_grid,
    shade_rgba,
    warp_limb_3bone,
    warp_rigid_rgba,
)
from wheelman_fx import (
    _blit_evolving_vfx_fireball,
    _draw_hdr_starburst,
    _load_vfx_fireball_rgba,
    _premul_remap,
)
from robeguy_keying import (
    CANVAS_H,
    CANVAS_W,
    GROUND_Y,
    STAGE_CX,
    STAGE_GY,
    STAGE_H,
    STAGE_W,
    TOP_Y,
    crop_normalize_robe,
    crop_tight_rgba,
    key_green_studio_robe,
    key_white_studio_robe,
    match_robe_color_grade,
    resize_rgba_premul,
    split_columns_auto,
)

REF_CHARS = TOOLS_DIR / "out" / "chars" / "ref"
REF_RG = TOOLS_DIR / "ref" / "robeguy"


# ---------------------------------------------------------------------------
# 1. Clean Chroma Keying & Extraction of Heads, Bodies, Flash-Wings & Props
# ---------------------------------------------------------------------------

def _key_green_crisp_no_slits(im_rgb: Image.Image, keep_multi: bool = False, min_area: int = 25) -> np.ndarray:
    """Chroma-keys #00FF00 plates that have NO interior green robe clovers (heads & props),
    opening even tiny 3px green slits behind sunglasses temples."""
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()
    g_ex = g - np.maximum(r, b)

    bg = (g_ex > 54.0) & (g > 95.0)
    dist = ndimage.distance_transform_edt(~bg)
    alpha = np.ones_like(g_ex, dtype=np.float32)
    alpha[bg] = 0.0

    edge = (~bg) & (dist <= 7.0)
    a_ramp = np.clip(1.0 - (g_ex - 10.0) / 46.0, 0.0, 1.0)
    use_r = edge & (g_ex > 10.0)
    alpha[use_r] = np.where(a_ramp[use_r] <= 0.06, 0.0, a_ramp[use_r])

    semi = (alpha > 0.0) & (alpha < 0.995)
    if np.any(semi):
        inv = 1.0 - alpha[semi]
        denom = np.maximum(alpha[semi], 0.25)
        r[semi] = np.clip(r[semi] / denom, 0.0, 255.0)
        g[semi] = np.clip((g[semi] - inv * 245.0) / denom, 0.0, 255.0)
        b[semi] = np.clip(b[semi] / denom, 0.0, 255.0)

    rgb = np.dstack([r, g, b])
    core = ndimage.minimum_filter((alpha > 0.98) & (g_ex < 12.0), size=3)
    if np.any(core):
        _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
        rim = (alpha > 0.0) & (~core) & (dist <= 5.5)
        rgb[rim] = rgb[iy[rim], ix[rim]]

    r2, g2, b2 = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    g_ex2 = g2 - np.maximum(r2, b2)
    spill = (alpha > 0.0) & (g_ex2 > 5.0)
    if np.any(spill):
        ex = g_ex2[spill] - 3.0
        g2[spill] = np.clip(g2[spill] - 0.92 * ex, 0.0, 255.0)
        r2[spill] = np.clip(r2[spill] + 0.14 * ex, 0.0, 255.0)
        b2[spill] = np.clip(b2[spill] + 0.14 * ex, 0.0, 255.0)

    alpha = np.clip((alpha - 0.06) / 0.94, 0.0, 1.0)
    out = np.dstack([
        np.clip(np.round(r2), 0, 255).astype(np.uint8),
        np.clip(np.round(g2), 0, 255).astype(np.uint8),
        np.clip(np.round(b2), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])

    mask = out[..., 3] > 22
    fl, fn = ndimage.label(mask)
    if fn > 0:
        fsz = ndimage.sum(mask, fl, range(1, fn + 1))
        if keep_multi:
            keep_ids = [i + 1 for i, sz in enumerate(fsz) if sz >= min_area]
            if not keep_ids:
                keep_ids = [1 + int(np.argmax(fsz))]
            keep = ndimage.binary_dilation(np.isin(fl, keep_ids), iterations=1)
        else:
            keep = ndimage.binary_dilation(fl == (1 + int(np.argmax(fsz))), iterations=1)
        out[~keep] = 0
    return out


def _extract_clean_monster_head(quad_rgb: Image.Image, cx_q: float, is_profile: bool = False) -> np.ndarray:
    """Extracts a 512x512 monster portrait cleanly WITHOUT any black t-shirt shoulder pixels."""
    rgba = _key_green_crisp_no_slits(quad_rgb, keep_multi=False)
    h, w = rgba.shape[:2]
    yg, xg = np.mgrid[0:h, 0:w].astype(np.float32)

    if not is_profile:
        # Above y=358: keep 100% of hair, ears, crooked sunglasses, face.
        # Below y=358: smoothly taper to the natural rounded beard contour centered at cx_q!
        t_y = np.clip((yg - 336.0) / 158.0, 0.0, 1.0)
        hw = 114.0 * np.sqrt(np.maximum(0.0, 1.0 - t_y * t_y))
        w_beard = np.where(yg <= 356.0, 1.0, np.clip((hw - np.abs(xg - cx_q)) / 9.0, 0.0, 1.0))
        # Also suppress pure black cotton shoulder pixels if any peek near y > 362 outside inner chin
        rgb = rgba[..., :3].astype(np.float32)
        lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
        sat = rgb.max(axis=-1) - rgb.min(axis=-1)
        shirt_px = (yg > 364.0) & (np.abs(xg - cx_q) > 84.0) & (lum < 38.0) & (sat < 14.0)
        w_beard = np.where(shirt_px, 0.0, w_beard)
        rgba[..., 3] = np.round(rgba[..., 3].astype(np.float32) * w_beard).astype(np.uint8)
    else:
        # 90° left profile: keep spiky hair, ear, sunglasses, roaring jaw & beard chin; cut black t-shirt neck base
        y_cut = 418.0 - 0.16 * np.maximum(0.0, xg - 215.0)
        chin_oval = ((xg - 178.0) / 68.0) ** 2 + ((yg - 392.0) / 84.0) ** 2
        w_prof = np.maximum(
            np.clip((y_cut - yg) / 10.0, 0.0, 1.0),
            np.clip((1.05 - chin_oval) / 0.16, 0.0, 1.0),
        )
        w_prof = np.where(xg > 425.0, np.clip((438.0 - xg) / 12.0, 0.0, 1.0) * w_prof, w_prof)
        rgba[..., 3] = np.round(rgba[..., 3].astype(np.float32) * w_prof).astype(np.uint8)

    return crop_tight_rgba(rgba, pad=4)


def load_all_robeguy_assets() -> dict:
    """Loads & normalizes all 8 turnaround views, 4 monster heads, flash-wings body, and 4 props."""
    f_raw = key_white_studio_robe(REF_CHARS / "robe_front.jpg")
    b_raw = key_white_studio_robe(REF_CHARS / "robe_back.jpg")
    n0 = crop_normalize_robe(f_raw)
    n4 = crop_normalize_robe(b_raw)

    turn_raw = key_green_studio_robe(REF_RG / "robe_turnaround_3views.jpg", keep_multi=True, min_comp_area=2000)
    cols = split_columns_auto(turn_raw, 3)
    n1 = match_robe_color_grade(crop_normalize_robe(cols[0]), n0)
    n2 = match_robe_color_grade(crop_normalize_robe(cols[1]), n0)
    n3 = match_robe_color_grade(crop_normalize_robe(cols[2]), n4)

    views_8 = {
        0: n0,
        1: n1,
        2: n2,
        3: n3,
        4: n4,
        5: mirror_canvas_horiz(n3),
        6: mirror_canvas_horiz(n2),
        7: mirror_canvas_horiz(n1),
    }

    # Monster expression portraits
    heads_im = Image.open(REF_RG / "robe_monster_heads_2x2.jpg").convert("RGB")
    hw, hh = heads_im.size
    mx, my = hw // 2, hh // 2
    heads = {
        "roar": _extract_clean_monster_head(heads_im.crop((0, 0, mx, my)), cx_q=253.0, is_profile=False),
        "grin": _extract_clean_monster_head(heads_im.crop((mx, 0, hw, my)), cx_q=260.0, is_profile=False),
        "shock": _extract_clean_monster_head(heads_im.crop((0, my, mx, hh)), cx_q=256.0, is_profile=False),
        "roar_side": _extract_clean_monster_head(heads_im.crop((mx, my, hw, hh)), cx_q=220.0, is_profile=True),
    }
    # Match head skin warmth slightly toward DSLR n0 face zone
    ref_face = n0[62:135, 206:274]
    for hk in list(heads.keys()):
        heads[hk] = match_robe_color_grade(heads[hk], ref_face)

    # Full-body Robe-Flash Bat-Wings plate (normalized to match standing height 548px onto STAGE_W x STAGE_H!)
    flash_raw = crop_tight_rgba(key_green_studio_robe(REF_RG / "robe_flash_open_plate.jpg", keep_multi=False), pad=2)
    flash_graded = match_robe_color_grade(flash_raw, n0)
    # Fit onto STAGE_W x STAGE_H anchored at STAGE_GY with generous wing margin (max width STAGE_W - 24 = 496)
    fh0, fw0 = flash_graded.shape[:2]
    sc_h = 468.0 / float(fh0)
    sc_w = (STAGE_W - 26.0) / float(fw0)
    sc_fl = min(sc_h, sc_w)
    fl_resized = resize_rgba_premul(flash_graded, int(round(fw0 * sc_fl)), int(round(fh0 * sc_fl)))
    flash_stage = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
    flash_stage.alpha_composite(
        Image.fromarray(fl_resized, "RGBA"),
        (int(round(STAGE_CX - fl_resized.shape[1] * 0.5)), int(round(STAGE_GY - fl_resized.shape[0]))),
    )
    flash_stage_rgba = np.asarray(flash_stage, dtype=np.uint8)

    # 4 Monster Props
    props_im = Image.open(REF_RG / "flamingo_monster_props_2x2.jpg").convert("RGB")
    pw, ph = props_im.size
    pmx, pmy = pw // 2, ph // 2
    props = {
        "feral_flam": crop_tight_rgba(_key_green_crisp_no_slits(props_im.crop((0, 0, pmx, pmy)), keep_multi=False), pad=3),
        "fly_flam": crop_tight_rgba(_key_green_crisp_no_slits(props_im.crop((pmx, 0, pw, pmy)), keep_multi=False), pad=3),
        "mug": crop_tight_rgba(_key_green_crisp_no_slits(props_im.crop((0, pmy, pmx, ph)), keep_multi=True, min_area=10), pad=3),
        "pile": crop_tight_rgba(_key_green_crisp_no_slits(props_im.crop((pmx, pmy, pw, ph)), keep_multi=False), pad=3),
    }

    # Build procedural hot-pink & coral flamingo feather sprites for particle bursts!
    feathers = _build_flamingo_feather_sprites()

    return {
        "views_8": views_8,
        "heads": heads,
        "flash_stage": flash_stage_rgba,
        "props": props,
        "feathers": feathers,
    }


def _build_flamingo_feather_sprites() -> list[Image.Image]:
    """Creates 4 crispshaded hot-pink / coral / light-pink flamingo feather RGBA sprites."""
    palette = [
        ((255, 68, 152), (255, 165, 212)),
        ((242, 42, 128), (255, 130, 190)),
        ((255, 105, 178), (255, 205, 232)),
        ((230, 52, 112), (255, 150, 185)),
    ]
    out: list[Image.Image] = []
    for base_c, tip_c in palette:
        w, h = 44, 20
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        # Curved feather vane + bright quill shaft
        dr.polygon([(5, 10), (14, 3), (30, 3), (41, 10), (30, 17), (14, 17)], fill=(*base_c, 242))
        dr.polygon([(18, 5), (32, 5), (39, 10), (32, 15), (18, 15)], fill=(*tip_c, 225))
        dr.line([(2, 11), (39, 10)], fill=(255, 240, 248, 245), width=2)
        out.append(im.filter(ImageFilter.GaussianBlur(0.45)))
    return out


# ---------------------------------------------------------------------------
# 2. Surgical Monster Head Replacement & Glowing Red Sunglasses Eyes
# ---------------------------------------------------------------------------

def graft_monster_head(
    body_480: np.ndarray,
    d_idx: int,
    heads: dict[str, np.ndarray],
    expr: str = "roar",
    head_tilt_deg: float = 0.0,
    red_eyes_glow: float = 0.0,
) -> np.ndarray:
    """Replaces the neutral studio head on `body_480` (480x640) with a monster portrait (`roar`, `grin`, `shock`)
    while preserving the pink flamingo bathrobe collar & hood seamlessly."""
    if d_idx in (3, 4, 5):
        out = body_480.copy()
        if abs(head_tilt_deg) > 0.2:
            # Subtle head bob/tilt on back angles above y=122
            yg, _ = np.mgrid[0:CANVAS_H, 0:CANVAS_W]
            hm = (yg < 118) & (out[..., 3] > 0)
            if np.any(hm):
                h_part = np.where(hm[..., None], out, 0)
                b_part = np.where((~hm)[..., None], out, 0)
                out = alpha_over(b_part, warp_rigid_rgba(h_part, (240.0, 114.0), angle_deg=head_tilt_deg))
        return out

    out = body_480.copy()
    yg, xg = np.mgrid[0:CANVAS_H, 0:CANVAS_W].astype(np.float32)
    rgb = out[..., :3].astype(np.float32)
    # Pink robe pixels have strong R - G > 42 and R > 175: NEVER erase pink collar or hood!
    is_pink_robe = ((rgb[..., 0] - rgb[..., 1]) > 40.0) & (rgb[..., 0] > 168.0)

    if d_idx in (0, 1, 7):
        cx_h = 240.0 if d_idx == 0 else (234.0 if d_idx == 1 else 246.0)
        # Erase original neutral head strictly above collar & outside pink lapels
        erase = (yg < 115.0) | ((yg < 142.0) & (np.abs(xg - cx_h) < 34.0) & (~is_pink_robe))
        w_keep = 1.0 - cv2.GaussianBlur(erase.astype(np.float32), (7, 7), 1.6)
        out[..., 3] = np.round(out[..., 3].astype(np.float32) * w_keep).astype(np.uint8)

        src_head = heads.get(expr, heads["roar"])
        if d_idx == 7:
            src_head = mirror_canvas_horiz(src_head)

        # Match authentic skull width (tw=74 on 0°, 70 on 45°/315°) & anchor crown at y=43
        # so crown height matches d=3,4,5 & flash_stage while roaring jaw drops onto chest!
        tw = 74 if d_idx == 0 else 70
        if expr == "shock":
            tw = int(round(tw * 1.03))
        th = int(round(src_head.shape[0] * (tw / float(src_head.shape[1]))))
        h_scaled = resize_rgba_premul(src_head, tw, th)

        paste_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        ox = int(round(cx_h - tw * 0.5))
        oy = 40 if expr == "shock" else 43
        paste_layer.alpha_composite(Image.fromarray(h_scaled, "RGBA"), (ox, oy))
        h_arr = np.asarray(paste_layer, dtype=np.uint8)
        if abs(head_tilt_deg) > 0.15:
            h_arr = warp_rigid_rgba(h_arr, (cx_h, 118.0), angle_deg=head_tilt_deg)
        out = alpha_over(out, h_arr)

        if red_eyes_glow > 0.02:
            ey_frac = 0.462 if expr == "shock" else (0.448 if expr == "grin" else 0.441)
            ey_pos = oy + th * ey_frac
            sp_pos = tw * 0.178
            out = _add_glowing_red_eyes(out, cx_h, ey_pos, spread=sp_pos, intensity=red_eyes_glow)
        return out

    # Profile angles d_idx in (2, 6)
    is_right = (d_idx == 6)
    cx_p = 244.0 if is_right else 236.0
    if not is_right:
        erase = (yg < 115.0) | ((yg < 142.0) & (xg < 248.0) & (~is_pink_robe))
    else:
        erase = (yg < 115.0) | ((yg < 142.0) & (xg > 232.0) & (~is_pink_robe))
    w_keep = 1.0 - cv2.GaussianBlur(erase.astype(np.float32), (7, 7), 1.6)
    out[..., 3] = np.round(out[..., 3].astype(np.float32) * w_keep).astype(np.uint8)

    prof_head = heads["roar_side"]
    if is_right:
        prof_head = mirror_canvas_horiz(prof_head)
    tw = 78
    th = int(round(prof_head.shape[0] * (tw / float(prof_head.shape[1]))))
    h_scaled = resize_rgba_premul(prof_head, tw, th)

    paste_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ox = int(round((234.0 if not is_right else 246.0) - tw * 0.5))
    oy = 44
    paste_layer.alpha_composite(Image.fromarray(h_scaled, "RGBA"), (ox, oy))
    h_arr = np.asarray(paste_layer, dtype=np.uint8)
    if abs(head_tilt_deg) > 0.15:
        h_arr = warp_rigid_rgba(h_arr, (cx_p, 118.0), angle_deg=head_tilt_deg)
    out = alpha_over(out, h_arr)

    if red_eyes_glow > 0.02:
        ex_p = ox + tw * (0.20 if not is_right else 0.80)
        ey_p = oy + th * 0.358
        out = _add_glowing_red_eyes(out, ex_p, ey_p, spread=0.0, intensity=red_eyes_glow)
    return out


def _add_glowing_red_eyes(rgba: np.ndarray, cx: float, ey: float, spread: float = 13.5, intensity: float = 1.0) -> np.ndarray:
    """Adds menacing crimson-magenta laser eye glints peeking right over his Clubmaster sunglasses."""
    im = Image.fromarray(rgba, "RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    pts = [(cx - spread, ey), (cx + spread, ey)] if spread > 1.0 else [(cx, ey)]
    a_outer = int(round(165 * min(1.2, intensity)))
    a_core = int(round(245 * min(1.0, intensity)))
    for px, py in pts:
        dr.ellipse([px - 7, py - 4.5, px + 7, py + 4.5], fill=(255, 20, 75, a_outer))
        dr.ellipse([px - 3.2, py - 2.2, px + 3.2, py + 2.2], fill=(255, 110, 155, a_core))
        dr.ellipse([px - 1.5, py - 1.2, px + 1.5, py + 1.2], fill=(255, 245, 250, a_core))
    ov_blur = ov.filter(ImageFilter.GaussianBlur(1.1))
    im.alpha_composite(ov_blur)
    im.alpha_composite(ov)
    return np.asarray(im, dtype=np.uint8)


# ---------------------------------------------------------------------------
# 3. 3D Stage Projection, Contact Shadow & Premultiplied Prop Pasting
# ---------------------------------------------------------------------------

def body_480_to_stage(rgba_480: np.ndarray, scale: float = 0.84, dx: float = 0.0, dy: float = 0.0) -> np.ndarray:
    """Places a 480x640 character frame onto STAGE_W x STAGE_H (520x585) anchored at STAGE_GY (532)."""
    nw = max(2, int(round(CANVAS_W * scale)))
    nh = max(2, int(round(CANVAS_H * scale)))
    resized = resize_rgba_premul(rgba_480, nw, nh)
    ox = int(round(STAGE_CX + dx - nw * 0.5))
    oy = int(round(STAGE_GY + dy - GROUND_Y * scale))
    st = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
    st.alpha_composite(Image.fromarray(resized, "RGBA"), (ox, oy))
    return np.asarray(st, dtype=np.uint8)


def project_3d_stage(lx: float, ly: float, lz: float, d_idx: int, cx: float = STAGE_CX, gy: float = STAGE_GY) -> tuple[float, float, float, float]:
    """Projects character-local 3D point (lx=forward, ly=left/right-hand-side, lz=up) to screen (sx, sy, dz, sc).
    Matches Quake d=0 Front, d=2 Left Profile (-X), d=4 Back, d=6 Right Profile (+X).
    dz < 0 => IN FRONT of character (closer to viewer); dz > 0 => BEHIND character.
    """
    phi = math.radians(d_idx * 45.0)
    sx = cx + (-lx * math.sin(phi) + ly * math.cos(phi))
    dz = -lx * math.cos(phi) - ly * math.sin(phi)
    sy = gy - lz + dz * 0.13
    sc = float(np.clip(1.0 - 0.0011 * dz, 0.80, 1.22))
    return sx, sy, dz, sc


def _safe_alpha_composite(canvas: Image.Image, src: Image.Image, ox: int, oy: int) -> None:
    """Boundary-safe RGBA alpha_composite supporting negative or overflowing coordinates."""
    x0_d = max(0, ox)
    y0_d = max(0, oy)
    x1_d = min(canvas.width, ox + src.width)
    y1_d = min(canvas.height, oy + src.height)
    if x1_d > x0_d and y1_d > y0_d:
        sx0 = x0_d - ox
        sy0 = y0_d - oy
        canvas.alpha_composite(src, dest=(x0_d, y0_d), source=(sx0, sy0, sx0 + (x1_d - x0_d), sy0 + (y1_d - y0_d)))


def _paste_rotated_rgba(
    stage_rgba: Image.Image,
    sprite_pil: Image.Image,
    cx: float,
    cy: float,
    angle_deg: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
    alpha_mul: float = 1.0,
    max_bottom_y: float | None = None,
) -> None:
    """Boundary-safe subpixel rotated + scaled RGBA blit with optional floor-contact clamp."""
    if alpha_mul <= 0.004:
        return
    w0, h0 = sprite_pil.size
    nw = max(2, int(round(w0 * sx)))
    nh = max(2, int(round(h0 * sy)))
    im = sprite_pil.resize((nw, nh), Image.Resampling.BICUBIC) if (nw != w0 or nh != h0) else sprite_pil
    if abs(angle_deg) > 0.05:
        im = im.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, expand=True)
    if alpha_mul < 0.999:
        arr = np.asarray(im, dtype=np.float32).copy()
        arr[..., 3] *= max(0.0, alpha_mul)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    px = int(round(cx - im.width * 0.5))
    py = int(round(cy - im.height * 0.5))
    if max_bottom_y is not None:
        bbox = im.getbbox()
        if bbox is not None:
            opaque_bot = py + bbox[3]
            if opaque_bot > max_bottom_y:
                py -= int(round(opaque_bot - max_bottom_y))
    _safe_alpha_composite(stage_rgba, im, px, py)


def paste_prop_rgba(
    canvas: Image.Image,
    prop_rgba: np.ndarray,
    cx: float,
    cy: float,
    scale: float = 1.0,
    rot_deg: float = 0.0,
    flip_x: bool = False,
    alpha_mul: float = 1.0,
) -> None:
    if alpha_mul <= 0.004:
        return
    arr = prop_rgba[:, ::-1, :].copy() if flip_x else prop_rgba
    if abs(scale - 1.0) > 0.01:
        arr = resize_rgba_premul(arr, max(2, int(round(arr.shape[1] * scale))), max(2, int(round(arr.shape[0] * scale))))
    if alpha_mul < 0.995:
        arr = arr.copy()
        arr[..., 3] = np.clip(np.round(arr[..., 3].astype(np.float32) * alpha_mul), 0, 255).astype(np.uint8)
    if abs(rot_deg) > 0.25:
        f = arr.astype(np.float32)
        a = f[..., 3:4] / 255.0
        pm = np.clip(np.round(np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)), 0, 255).astype(np.uint8)
        pm_r = np.asarray(Image.fromarray(pm, "RGBA").rotate(rot_deg, resample=Image.Resampling.BICUBIC, expand=True), dtype=np.float32)
        pa = pm_r[..., 3:4] / 255.0
        rgb = np.where(pa > 1e-3, pm_r[..., :3] / np.maximum(pa, 1e-3), 0.0)
        pil_im = Image.fromarray(np.dstack([
            np.clip(np.round(rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(pm_r[..., 3]), 0, 255).astype(np.uint8),
        ]), "RGBA")
    else:
        pil_im = Image.fromarray(arr, "RGBA")

    ox = int(round(cx - pil_im.width * 0.5))
    oy = int(round(cy - pil_im.height * 0.5))
    # Crisp dark silhouette drop-shadow so pink props pop off the pink bathrobe!
    sh_a = np.asarray(pil_im, dtype=np.uint8)[..., 3]
    if np.any(sh_a > 12):
        sh_rgba = np.zeros((pil_im.height + 8, pil_im.width + 8, 4), dtype=np.uint8)
        sh_rgba[4:4 + pil_im.height, 4:4 + pil_im.width, 3] = (sh_a.astype(np.float32) * 0.55).astype(np.uint8)
        sh_rgba[4:4 + pil_im.height, 4:4 + pil_im.width, :3] = (12, 8, 20)
        sh_blur = Image.fromarray(sh_rgba, "RGBA").filter(ImageFilter.GaussianBlur(2.4))
        _safe_alpha_composite(canvas, sh_blur, ox - 2, oy - 1)
    _safe_alpha_composite(canvas, pil_im, ox, oy)


def draw_ground_shadow(canvas: Image.Image, cx: float = STAGE_CX, gy: float = STAGE_GY, rx: float = 58.0, ry: float = 11.0, alpha: int = 86) -> None:
    w, h = int(rx * 2 + 28), int(ry * 2 + 20)
    sub = np.zeros((h, w, 4), dtype=np.uint8)
    cv2.ellipse(sub, (w // 2, h // 2), (int(rx), int(ry)), 0, 0, 360, (10, 8, 16, int(alpha)), -1, cv2.LINE_AA)
    sub = cv2.GaussianBlur(sub, (15, 15), 4.4)
    _safe_alpha_composite(canvas, Image.fromarray(sub, "RGBA"), int(round(cx - w * 0.5)), int(round(gy - h * 0.5)))


# ---------------------------------------------------------------------------
# 4. Bathrobe + Barefoot Skeletal Warper (Billowing Robe Skirt + Wild Arms!)
# ---------------------------------------------------------------------------

def _auto_robe_seams_fb(base_rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Finds left & right sleeve-to-robe seams on front/back 480x640 views."""
    H, W = base_rgba.shape[:2]
    a = base_rgba[..., 3] > 28
    l_pts_y, l_pts_x = [], []
    r_pts_y, r_pts_x = [], []
    for y in range(230, 375, 4):
        xs = np.nonzero(a[y])[0]
        if len(xs) < 12:
            continue
        for k in range(len(xs) - 1):
            if xs[k + 1] - xs[k] >= 2:
                gx = 0.5 * (xs[k] + xs[k + 1])
                if 130 <= gx <= 205:
                    l_pts_y.append(y)
                    l_pts_x.append(gx)
                elif 275 <= gx <= 350:
                    r_pts_y.append(y)
                    r_pts_x.append(gx)

    yg_1d = np.arange(H, dtype=np.float32)
    if len(l_pts_y) >= 2:
        xl = np.interp(yg_1d, l_pts_y, l_pts_x).astype(np.float32)
        xl[yg_1d < l_pts_y[0]] = float(l_pts_x[0]) + np.clip((l_pts_y[0] - yg_1d[yg_1d < l_pts_y[0]]) * 0.08, 0.0, 9.0)
    else:
        xl = np.full(H, 174.0, dtype=np.float32)

    if len(r_pts_y) >= 2:
        xr = np.interp(yg_1d, r_pts_y, r_pts_x).astype(np.float32)
        xr[yg_1d < r_pts_y[0]] = float(r_pts_x[0]) - np.clip((r_pts_y[0] - yg_1d[yg_1d < r_pts_y[0]]) * 0.08, 0.0, 9.0)
    else:
        xr = np.full(H, 306.0, dtype=np.float32)
    return xl[:, None], xr[:, None]


def pose_berserker_robe_480(
    base_480: np.ndarray,
    d_idx: int,
    frame_idx: int,
    n_frames: int = 8,
    berserk_arms: float = 1.0,
) -> np.ndarray:
    """Animates Pink Flamingo Bathrobe Guy running berserk across all 8 angles (0..7):
    - Bare hairy calves & bare feet (`y = 446..596`) run with high-cadence strides
    - Knee-length pink flamingo robe skirt (`y = 285..458`) flares & ripples dynamically
    - Pink-sleeved arms (`arm_l`, `arm_r`) fling wide & pump like a 3 AM bathrobe monster!"""
    if d_idx in (5, 6, 7):
        canon_d = 8 - d_idx
        canon_base = mirror_canvas_horiz(base_480)
        canon_fr = pose_berserker_robe_480(canon_base, canon_d, (frame_idx + n_frames // 2) % n_frames, n_frames, berserk_arms)
        return mirror_canvas_horiz(canon_fr)

    H, W = base_480.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]
    phase_01 = (frame_idx % n_frames) / float(n_frames)
    ph = 2.0 * math.pi * phase_01

    if d_idx in (0, 4):
        is_back = (d_idx == 4)
        xl, xr = _auto_robe_seams_fb(base_480)
        arm_l_m = (xg < xl) & (yg >= 156) & (yg <= 398) & (base_480[..., 3] > 0)
        arm_r_m = (xg > xr) & (yg >= 156) & (yg <= 398) & (base_480[..., 3] > 0)

        y_hem = 446
        leg_zone = (yg >= y_hem) & (~arm_l_m) & (~arm_r_m)
        leg_l_m = leg_zone & (xg < 240) & (base_480[..., 3] > 0)
        leg_r_m = leg_zone & (xg >= 240) & (base_480[..., 3] > 0)
        torso_m = (base_480[..., 3] > 0) & (~arm_l_m) & (~arm_r_m) & (yg < y_hem + 8)

        arm_l = extend_top_upward(np.where(arm_l_m[..., None], base_480, 0), 156, up_px=16)
        arm_r = extend_top_upward(np.where(arm_r_m[..., None], base_480, 0), 156, up_px=16)
        leg_l = extend_top_upward(np.where(leg_l_m[..., None], base_480, 0), y_hem, up_px=34)
        leg_r = extend_top_upward(np.where(leg_r_m[..., None], base_480, 0), y_hem, up_px=34)
        torso = np.where(torso_m[..., None], base_480, 0)

        s_l = math.cos(ph - 0.35)
        s_r = -s_l
        bob_dy = -6.5 * abs(math.sin(ph)) + 2.0
        sway_dx = -5.2 * math.sin(ph)
        tilt_deg = 3.6 * math.sin(ph)

        # Billow & flare the pink bathrobe skirt dynamically with stride!
        ty, tx = np.mgrid[0:H, 0:W].astype(np.float32)
        w_skirt = np.clip((ty - 280.0) / 170.0, 0.0, 1.0)
        flare = 1.0 + (0.08 + 0.04 * abs(math.cos(ph))) * w_skirt
        wave_x = 5.5 * np.sin(ph + ty * 0.045) * (w_skirt ** 1.4)
        src_tx = 240.0 + (tx - 240.0 - wave_x) / flare
        torso_billow = _premul_remap(torso, src_tx.astype(np.float32), ty.astype(np.float32))
        torso_p = warp_rigid_rgba(torso_billow, (240.0, 260.0), angle_deg=tilt_deg, dx=sway_dx, dy=bob_dy)

        def _pose_calf_fb(leg_im: np.ndarray, hx: float, side_sign: float, s_val: float) -> np.ndarray:
            if s_val > 0:
                u = s_val
                return warp_limb_3bone(
                    shade_rgba(leg_im, 1.0 + (0.04 if not is_back else -0.10) * u),
                    (hx, float(y_hem)), (hx, 512.0), (hx, 580.0),
                    ang_upper=-side_sign * 9.0 * u,
                    ang_lower=side_sign * 7.0 * u,
                    sy_upper=1.0 - 0.24 * u,
                    sy_lower=1.0 - (0.18 if not is_back else 0.36) * u,
                    scale_all=1.0 + (0.06 if not is_back else -0.04) * u,
                    dx=sway_dx, dy=bob_dy - 22.0 * u,
                )
            p = -s_val
            return warp_limb_3bone(
                leg_im, (hx, float(y_hem)), (hx, 512.0), (hx, 580.0),
                ang_upper=side_sign * 5.0 * p,
                ang_lower=-side_sign * 3.0 * p,
                dx=sway_dx, dy=max(-2.0, bob_dy * 0.35),
            )

        # Wild monster arms flung out & pumping dramatically!
        def _pose_berserk_arm(arm_im: np.ndarray, sx0: float, side_sign: float, s_arm: float) -> np.ndarray:
            # side_sign = -1 for left-of-screen arm (x < 240), +1 for right-of-screen arm (x > 240)
            # Note: in warp_limb_3bone, positive angle rotates clockwise -> swings left arm OUTWARD-UP and right arm INWARD!
            # Wait: let's verify _rot2d(deg): [[c, -s], [s, c]] on downward vector (0, +L) gives (-L*sin(deg), L*cos(deg))!
            # So for downward-hanging arm (dy > 0):
            #   deg > 0 moves tip toward -X (LEFT of screen = OUTWARD for left arm!)
            #   deg < 0 moves tip toward +X (RIGHT of screen = OUTWARD for right arm!)
            out_sign = -side_sign  # +1 for left-screen arm (moves -X), -1 for right-screen arm (moves +X)!
            flap_deg = (48.0 + 28.0 * s_arm) * berserk_arms
            fore_deg = (24.0 + 22.0 * max(0.0, s_arm)) * berserk_arms
            return warp_limb_3bone(
                shade_rgba(arm_im, 1.0 + 0.04 * s_arm),
                (sx0, 172.0), (sx0 + side_sign * 6.0, 268.0), (sx0 + side_sign * 8.0, 348.0),
                ang_upper=out_sign * flap_deg,
                ang_lower=out_sign * fore_deg,
                sy_upper=0.95,
                sy_lower=0.92,
                dx=sway_dx, dy=bob_dy - 6.0 * max(0.0, s_arm),
            )

        leg_l_p = _pose_calf_fb(leg_l, 198.0, -1.0, s_l)
        leg_r_p = _pose_calf_fb(leg_r, 282.0, +1.0, s_r)
        arm_l_p = _pose_berserk_arm(arm_l, 172.0, -1.0, s_r)
        arm_r_p = _pose_berserk_arm(arm_r, 308.0, +1.0, s_l)

        out = np.zeros_like(base_480)
        if (s_l >= s_r) != is_back:
            out = alpha_over(alpha_over(out, leg_r_p), leg_l_p)
        else:
            out = alpha_over(alpha_over(out, leg_l_p), leg_r_p)
        out = alpha_over(out, torso_p)
        out = alpha_over(alpha_over(out, arm_l_p), arm_r_p)
        return out

    # Diagonal 3/4 views (d_idx = 1 -> 45° Front-Left, d_idx = 3 -> 135° Back-Left, both facing -X!)
    # IMPORTANT: Both legs AND both outer sleeves are already separated on 45° / 135° turnaround plates!
    if d_idx in (1, 3):
        y_hem = 446
        a_fg = base_480[..., 3] > 30
        xl, xr = _auto_robe_seams_fb(base_480)
        xl = np.minimum(xl, 179.0)
        xr = np.maximum(xr, 296.0)

        arm_l_m = (xg < xl) & (yg >= 164) & (yg <= 368) & a_fg
        arm_r_m = (xg > xr) & (yg >= 164) & (yg <= 368) & a_fg
        leg_zone = (yg >= y_hem) & (~arm_l_m) & (~arm_r_m) & a_fg
        split_x = 244 if d_idx == 1 else 248
        leg_l_m = leg_zone & (xg < split_x)
        leg_r_m = leg_zone & (xg >= split_x)
        torso_m = a_fg & (~arm_l_m) & (~arm_r_m) & (yg < y_hem + 8)

        arm_l = extend_top_upward(np.where(arm_l_m[..., None], base_480, 0), 164, up_px=16)
        arm_r = extend_top_upward(np.where(arm_r_m[..., None], base_480, 0), 164, up_px=16)
        leg_l = extend_top_upward(np.where(leg_l_m[..., None], base_480, 0), y_hem, up_px=36)
        leg_r = extend_top_upward(np.where(leg_r_m[..., None], base_480, 0), y_hem, up_px=36)
        torso = np.where(torso_m[..., None], base_480, 0)

        th_a, kn_a, ft_a, _, bob_a = sample_run_profile(phase_01)
        th_b, kn_b, ft_b, _, _ = sample_run_profile((phase_01 + 0.5) % 1.0)
        bob_dy = bob_a * 0.90
        lean_deg = 5.2 + 2.0 * math.sin(ph)

        ty, tx = np.mgrid[0:H, 0:W].astype(np.float32)
        w_sk = np.clip((ty - 275.0) / 175.0, 0.0, 1.0)
        trail_x = (6.5 + 5.0 * np.sin(ph + ty * 0.05)) * (w_sk ** 1.35)
        flare_s = 1.0 + 0.09 * w_sk
        torso_billow = _premul_remap(torso, (240.0 + (tx - 240.0 - trail_x) / flare_s).astype(np.float32), ty.astype(np.float32))
        torso_p = warp_rigid_rgba(torso_billow, (240.0, 285.0), angle_deg=lean_deg, dy=bob_dy)

        def _pose_diag_leg(leg_im: np.ndarray, hx0: float, th_d: float, kn_d: float, ft_d: float, sh_f: float) -> np.ndarray:
            return warp_limb_3bone(
                shade_rgba(leg_im, sh_f),
                (hx0, float(y_hem)), (hx0 + 2.0, 514.0), (hx0 - 5.0, 580.0),
                ang_upper=th_d * 0.85,
                ang_lower=kn_d * 0.72,
                ang_tip=ft_d * 0.55,
                dx=-th_d * 0.22,
                dy=bob_dy - max(0.0, -kn_d * 0.14),
            )

        # Left-of-screen leg (xg < split_x) vs Right-of-screen leg (xg >= split_x): ALWAYS 2 legs!
        leg_l_p = _pose_diag_leg(leg_l, 210.0, th_b, kn_b, ft_b, 0.90 if d_idx == 1 else 1.02)
        leg_r_p = _pose_diag_leg(leg_r, 276.0, th_a, kn_a, ft_a, 1.02 if d_idx == 1 else 0.90)

        s_arm = math.sin(ph)
        arm_l_p = warp_limb_3bone(
            arm_l, (176.0, 174.0), (170.0, 266.0), (166.0, 344.0),
            ang_upper=(46.0 + 26.0 * s_arm) * berserk_arms,
            ang_lower=(24.0 + 16.0 * max(0.0, s_arm)) * berserk_arms,
            dy=bob_dy,
        )
        arm_r_p = warp_limb_3bone(
            arm_r, (300.0, 174.0), (306.0, 266.0), (310.0, 344.0),
            ang_upper=-(38.0 - 28.0 * s_arm) * berserk_arms,
            ang_lower=-(18.0 + 16.0 * max(0.0, -s_arm)) * berserk_arms,
            dy=bob_dy,
        )

        out = alpha_over(leg_l_p, leg_r_p) if d_idx == 1 else alpha_over(leg_r_p, leg_l_p)
        out = alpha_over(out, arm_l_p if d_idx == 1 else arm_r_p)
        out = alpha_over(out, torso_p)
        out = alpha_over(out, arm_r_p if d_idx == 1 else arm_l_p)
        return out

    # Pure 90° Left Profile (d_idx == 2, mirrored automatically for d_idx == 6):
    y_hem = 446
    a_fg = base_480[..., 3] > 30
    leg_mask = (yg >= y_hem) & a_fg
    leg_base = extend_top_upward(np.where(leg_mask[..., None], base_480, 0), y_hem, up_px=38)
    upper_base = np.where(((yg < y_hem + 8) & a_fg)[..., None], base_480, 0).copy()

    cx_arm = 236.0
    d_arm = seg_dist_grid(xg.astype(np.float32), yg.astype(np.float32), cx_arm, 174.0, cx_arm, 360.0)
    arm_m = (d_arm < 24.0) & (yg >= 166) & (yg <= 382) & a_fg
    arm_near = extend_top_upward(np.where(arm_m[..., None], base_480, 0), 166, up_px=12)
    # Inpaint bare hand / watch below sleeve cuff on upper_base with adjacent pink robe texture so no duplicate hand dangles!
    hand_ghost = arm_m & (yg >= 312)
    if np.any(hand_ghost):
        src_robe_x = np.clip(xg - 28, 0, W - 1)
        upper_base[hand_ghost] = upper_base[yg[hand_ghost], src_robe_x[hand_ghost]]

    th_a, kn_a, ft_a, _, bob_a = sample_run_profile(phase_01)
    th_b, kn_b, ft_b, _, _ = sample_run_profile((phase_01 + 0.5) % 1.0)
    bob_dy = bob_a * 0.95
    lean_deg = 6.5 + 2.2 * math.sin(ph)

    ty, tx = np.mgrid[0:H, 0:W].astype(np.float32)
    w_sk = np.clip((ty - 275.0) / 175.0, 0.0, 1.0)
    trail_x = (8.0 + 5.5 * np.sin(ph + ty * 0.05)) * (w_sk ** 1.35)
    flare_s = 1.0 + 0.10 * w_sk
    upper_billow = _premul_remap(upper_base, (240.0 + (tx - 240.0 - trail_x) / flare_s).astype(np.float32), ty.astype(np.float32))
    upper_p = warp_rigid_rgba(upper_billow, (238.0, 290.0), angle_deg=lean_deg, dy=bob_dy)

    hx_leg = float(np.median(np.nonzero(leg_base[y_hem:y_hem + 35, :, 3] > 40)[1])) if np.any(leg_base[y_hem:y_hem + 35, :, 3] > 40) else 252.0

    def _pose_calf_side(th_d: float, kn_d: float, ft_d: float, shade_f: float) -> np.ndarray:
        return warp_limb_3bone(
            shade_rgba(leg_base, shade_f),
            (hx_leg, float(y_hem)), (hx_leg + 2.0, 514.0), (hx_leg - 6.0, 582.0),
            ang_upper=th_d * 1.15,
            ang_lower=kn_d * 0.88,
            ang_tip=ft_d * 0.65,
            dx=-th_d * 0.32,
            dy=bob_dy - max(0.0, -kn_d * 0.16),
        )

    far_leg = _pose_calf_side(th_b, kn_b, ft_b, 0.82)
    near_leg = _pose_calf_side(th_a, kn_a, ft_a, 1.02)

    arm_swing = (52.0 + 34.0 * math.sin(ph)) * berserk_arms
    arm_p = warp_limb_3bone(
        arm_near,
        (cx_arm, 176.0), (cx_arm, 268.0), (cx_arm - 4.0, 344.0),
        ang_upper=arm_swing,
        ang_lower=28.0 * berserk_arms,
        dy=bob_dy,
    )

    out = alpha_over(alpha_over(far_leg, near_leg), upper_p)
    out = alpha_over(out, arm_p)
    return out


# ---------------------------------------------------------------------------
# 5. Master Builders for All 5 Hilarious Monster Animations
# ---------------------------------------------------------------------------

def build_anim1_monster_idle(assets: dict, n_frames: int = 8) -> list[list[np.ndarray]]:
    """Animation 1: 'Unhinged 3 AM Flamingo Whisperer' (8 dirs x 8 frames).
    Feral crouch-breathing sway, glowing red eyes over Clubmaster sunglasses, maniacal grin,
    and TWO fanged pocket/shoulder flamingos bobbing & snapping beaks across 360°!"""
    views_8 = assets["views_8"]
    heads = assets["heads"]
    feral_flam = assets["props"]["feral_flam"]
    feathers = assets["feathers"]

    grid: list[list[np.ndarray]] = []
    for d in range(8):
        row: list[np.ndarray] = []
        base_grin = graft_monster_head(views_8[d], d, heads, expr="grin", red_eyes_glow=0.0)
        for f in range(n_frames):
            ph = 2.0 * math.pi * f / float(n_frames)
            glow = 0.62 + 0.38 * (0.5 + 0.5 * math.sin(ph * 2.0))
            tilt = 2.2 * math.sin(ph)
            cur_480 = graft_monster_head(base_grin if d in (3, 4, 5) else views_8[d], d, heads, expr="grin", head_tilt_deg=tilt, red_eyes_glow=glow)

            # Heavy feral breathing crouch & chest heave on 480x640
            H, W = cur_480.shape[:2]
            yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
            breathe = math.sin(ph)
            sy = 1.0 - 0.026 * breathe
            sx_chest = 1.0 + 0.032 * max(0.0, -breathe) * np.exp(-((yg - 215.0) / 75.0) ** 2)
            sway_x = 3.5 * math.sin(ph) * (1.0 - np.clip((yg - 450.0) / 145.0, 0.0, 1.0))
            map_y = GROUND_Y - (GROUND_Y - yg) / sy
            map_x = 240.0 + (xg - 240.0 - sway_x) / sx_chest
            posed_480 = _premul_remap(cur_480, map_x.astype(np.float32), map_y.astype(np.float32))

            st_im = Image.fromarray(np.zeros((STAGE_H, STAGE_W, 4), dtype=np.uint8), "RGBA")
            draw_ground_shadow(st_im, STAGE_CX, STAGE_GY, rx=56.0 + 3.0 * breathe, ry=11.0)
            body_st = Image.fromarray(body_480_to_stage(posed_480, scale=0.84), "RGBA")

            # Two pocket/hip fanged flamingos peeking out wide left & right of his pink robe!
            flam_items = []
            for side_i, ly_off in enumerate((-56.0, +56.0)):
                bob_f = 9.0 * math.sin(ph * 2.0 + side_i * 2.1)
                lx_off = 22.0 + 6.0 * math.cos(ph + side_i * 1.7)
                lz_off = 232.0 + bob_f
                sx_f, sy_f, dz_f, sc_f = project_3d_stage(lx_off, ly_off, lz_off, d)
                fwd_x, _, _, _ = project_3d_stage(lx_off + 20.0, ly_off * 1.35, lz_off, d)
                flip_fl = (fwd_x > sx_f)
                rot_fl = (15.0 if not flip_fl else -15.0) * math.sin(ph * 2.0 + side_i)
                flam_items.append((dz_f, sx_f, sy_f, 0.25 * sc_f, rot_fl, flip_fl))

            # Render behind-body flamingos (dz >= 0), then body, then front flamingos (dz < 0)
            for dz_f, sx_f, sy_f, sc_f, rot_fl, flip_fl in [it for it in flam_items if it[0] >= 0]:
                paste_prop_rgba(st_im, feral_flam, sx_f, sy_f, scale=sc_f, rot_deg=rot_fl, flip_x=flip_fl)
            st_im.alpha_composite(body_st)
            for dz_f, sx_f, sy_f, sc_f, rot_fl, flip_fl in [it for it in flam_items if it[0] < 0]:
                paste_prop_rgba(st_im, feral_flam, sx_f, sy_f, scale=sc_f, rot_deg=rot_fl, flip_x=flip_fl)

            # Subtle drifting pink flamingo feather ambiance
            for fi in range(2):
                fp = ((f / float(n_frames)) + fi * 0.5) % 1.0
                fx = STAGE_CX + (-58.0 if fi == 0 else 58.0) + 12.0 * math.sin(fp * 2 * math.pi)
                fy = STAGE_GY - 310.0 + fp * 145.0
                fa = math.sin(math.pi * fp) * 0.85
                _paste_rotated_rgba(st_im, feathers[fi], fx, fy, angle_deg=fp * 180.0, sx=0.62, sy=0.62, alpha_mul=fa)

            row.append(np.asarray(st_im, dtype=np.uint8))
        grid.append(row)
    return grid


def build_anim2_berserker_charge(assets: dict, n_frames: int = 8) -> list[list[np.ndarray]]:
    """Animation 2: 'STAY OFF MY LAWN! Barefoot Bathrobe Berserker' (8 dirs x 8 frames).
    Full 360° high-speed barefoot charge, arms flung wide, roaring monster jaw, dust & pink feathers!"""
    views_8 = assets["views_8"]
    heads = assets["heads"]
    feathers = assets["feathers"]

    grid: list[list[np.ndarray]] = []
    for d in range(8):
        roar_base = graft_monster_head(views_8[d], d, heads, expr="roar", red_eyes_glow=0.95)
        row: list[np.ndarray] = []
        for f in range(n_frames):
            posed_480 = pose_berserker_robe_480(roar_base, d, f, n_frames=n_frames, berserk_arms=1.0)
            st_im = Image.fromarray(np.zeros((STAGE_H, STAGE_W, 4), dtype=np.uint8), "RGBA")
            ph = 2.0 * math.pi * f / float(n_frames)
            draw_ground_shadow(st_im, STAGE_CX, STAGE_GY, rx=62.0, ry=11.0, alpha=78)

            # Trailing kinetic speed lines & pink feathers behind his 3D back (-lx)!
            ov_fx = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            dr_fx = ImageDraw.Draw(ov_fx)
            for si, lz_s in enumerate((120.0, 210.0, 300.0, 380.0)):
                p0_x, p0_y, dz_s, _ = project_3d_stage(-36.0, (si % 2 - 0.5) * 28.0, lz_s, d)
                p1_x, p1_y, _, _ = project_3d_stage(-98.0 - 22.0 * ((f + si) % 3), (si % 2 - 0.5) * 32.0, lz_s - 6.0, d)
                if abs(p1_x - p0_x) > 8.0 or abs(p1_y - p0_y) > 4.0:
                    dr_fx.line([(p0_x, p0_y), (p1_x, p1_y)], fill=(255, 120, 195, 135), width=3)

            # Barefoot ground dust puffs on strike frames
            for step_k in (0, 4):
                age = ((f - step_k) % n_frames) / float(n_frames)
                if age < 0.45:
                    u = age / 0.45
                    dx_p, dy_p, _, _ = project_3d_stage(-18.0 - 45.0 * u, 0.0, 10.0 + 18.0 * u, d)
                    r_p = int(10 + 18 * u)
                    a_p = int(145 * (1.0 - u))
                    dr_fx.ellipse([dx_p - r_p, dy_p - r_p * 0.65, dx_p + r_p, dy_p + r_p * 0.65], fill=(225, 212, 205, a_p))

            st_im.alpha_composite(ov_fx.filter(ImageFilter.GaussianBlur(1.0)))
            st_im.alpha_composite(Image.fromarray(body_480_to_stage(posed_480, scale=0.84), "RGBA"))

            # Bursting hot-pink flamingo feathers trailing off his flapping robe!
            for fi in range(4):
                u_f = ((f / float(n_frames)) + fi * 0.25) % 1.0
                fx_x, fx_y, _, sc_f = project_3d_stage(
                    -28.0 - 88.0 * u_f,
                    (-32.0 if fi % 2 == 0 else 32.0) + 14.0 * math.sin(ph + fi),
                    155.0 + fi * 52.0 - 38.0 * u_f,
                    d,
                )
                _paste_rotated_rgba(
                    st_im, feathers[fi % len(feathers)], fx_x, fx_y,
                    angle_deg=u_f * 320.0 + fi * 55.0,
                    sx=0.72 * sc_f, sy=0.72 * sc_f,
                    alpha_mul=math.sin(math.pi * u_f) * 0.95,
                )

            row.append(np.asarray(st_im, dtype=np.uint8))
        grid.append(row)
    return grid


def _draw_chest_laser_vfx(
    canvas: Image.Image,
    d_idx: int,
    beam_u: float,
    chest_sx: float,
    chest_sy: float,
    behind_pass: bool = False,
) -> None:
    """Draws blinding volumetric Hot-Pink / White Care-Bear-From-Hell Chest-Hair Laser +
    expanding neon shockwave rings along the monster's 3D forward vector!"""
    # Check whether forward beam (+lx) goes toward viewer (dz < 0 -> front pass) or away (dz >= 0 -> behind pass)
    end_sx, end_sy, dz_end, _ = project_3d_stage(260.0, 0.0, 295.0, d_idx)
    is_away = (d_idx in (3, 4, 5))
    if behind_pass != is_away:
        return

    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    pulse = 0.82 + 0.18 * math.sin(beam_u * math.pi * 6.0)
    env = math.sin(math.pi * np.clip(beam_u, 0.0, 1.0)) ** 0.45

    if d_idx == 0:
        # 0° Direct camera blast: compact blinding pectoral star-core + radial laser rays + hollow shockwave rings
        # so his hilarious yellow red-heart boxer shorts stay 100% visible below!
        r_core = (19.0 + 11.0 * pulse) * env
        for ray_i in range(10):
            ra_ang = ray_i * (math.pi / 5.0) + beam_u * 2.2
            rl = (52.0 + 38.0 * ((ray_i % 2) + 0.5) * pulse) * env
            dr.line(
                [(chest_sx, chest_sy), (chest_sx + math.cos(ra_ang) * rl, chest_sy + math.sin(ra_ang) * rl)],
                fill=(255, 185, 232, int(205 * env)),
                width=3,
            )
        dr.ellipse([chest_sx - r_core * 1.7, chest_sy - r_core * 1.7, chest_sx + r_core * 1.7, chest_sy + r_core * 1.7], fill=(255, 25, 145, int(130 * env)))
        dr.ellipse([chest_sx - r_core, chest_sy - r_core, chest_sx + r_core, chest_sy + r_core], fill=(255, 120, 205, int(215 * env)))
        dr.ellipse([chest_sx - r_core * 0.52, chest_sy - r_core * 0.52, chest_sx + r_core * 0.52, chest_sy + r_core * 0.52], fill=(255, 248, 252, int(252 * env)))

        for ri in range(3):
            ru = ((beam_u * 2.2 + ri / 3.0) % 1.0)
            rr_x = 26.0 + 185.0 * ru
            rr_y = 22.0 + 150.0 * ru
            ra = int(225 * (1.0 - ru) * env)
            if ra > 8:
                dr.ellipse(
                    [chest_sx - rr_x, chest_sy - rr_y, chest_sx + rr_x, chest_sy + rr_y],
                    outline=(255, 75, 185, ra),
                    width=max(2, int(5 * (1.0 - ru))),
                )
                dr.ellipse(
                    [chest_sx - rr_x * 0.96, chest_sy - rr_y * 0.96, chest_sx + rr_x * 0.96, chest_sy + rr_y * 0.96],
                    outline=(255, 235, 250, int(ra * 0.8)),
                    width=max(1, int(2.2 * (1.0 - ru))),
                )
    elif d_idx == 4:
        # 180° Back view: massive hot-pink aura & shockwave halo blasting forward from behind his chest!
        r_glow = 95.0 * env * pulse
        dr.ellipse([chest_sx - r_glow * 1.4, chest_sy - r_glow, chest_sx + r_glow * 1.4, chest_sy + r_glow], fill=(255, 35, 150, int(165 * env)))
        for ri in range(3):
            ru = ((beam_u * 2.0 + ri / 3.0) % 1.0)
            rr = 45.0 + 170.0 * ru
            dr.ellipse([chest_sx - rr, chest_sy - rr * 0.78, chest_sx + rr, chest_sy + rr * 0.78], outline=(255, 110, 205, int(200 * (1.0 - ru) * env)), width=4)
    else:
        # Angled & profile 3D mega-beam cone blasting from chest_sx, chest_sy -> end_sx, end_sy!
        vx, vy = end_sx - chest_sx, end_sy - chest_sy
        ln = max(1.0, math.hypot(vx, vy))
        nx, ny = -vy / ln, vx / ln
        # Clamp beam endpoint inside stage margin so SPR32 bounds stay crisp while looking huge!
        t_max = min(1.0, 215.0 / ln)
        bx = chest_sx + vx * t_max
        by = chest_sy + vy * t_max

        for w0, w1, col in [
            (18.0 * env, 56.0 * env * pulse, (255, 22, 138, int(135 * env))),
            (10.0 * env, 32.0 * env * pulse, (255, 115, 205, int(215 * env))),
            (4.5 * env, 13.0 * env * pulse, (255, 248, 255, int(252 * env))),
        ]:
            poly = [
                (chest_sx + nx * w0, chest_sy + ny * w0),
                (bx + nx * w1, by + ny * w1),
                (bx - nx * w1, by - ny * w1),
                (chest_sx - nx * w0, chest_sy - ny * w0),
            ]
            dr.polygon(poly, fill=col)

        dr.ellipse([chest_sx - 24 * env, chest_sy - 24 * env, chest_sx + 24 * env, chest_sy + 24 * env], fill=(255, 240, 250, int(245 * env)))
        # Coaxial shockwave rings normal to the 3D beam!
        for ri in range(3):
            ru = ((beam_u * 2.2 + ri / 3.0) % 1.0)
            rx_c = chest_sx + (bx - chest_sx) * (0.18 + 0.76 * ru)
            ry_c = chest_sy + (by - chest_sy) * (0.18 + 0.76 * ru)
            rad_r = (16.0 + 36.0 * ru) * env
            ra = int(225 * (1.0 - ru) * env)
            ring_im = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
            rdr = ImageDraw.Draw(ring_im)
            rdr.ellipse([60 - 11, 60 - rad_r, 60 + 11, 60 + rad_r], outline=(255, 225, 248, ra), width=3)
            ang_b = math.degrees(math.atan2(by - chest_sy, bx - chest_sx))
            _paste_rotated_rgba(ov, ring_im, rx_c, ry_c, angle_deg=ang_b)

    ov_blur = ov.filter(ImageFilter.GaussianBlur(2.2))
    canvas.alpha_composite(ov_blur)
    canvas.alpha_composite(ov)


def build_anim3_robe_flash_laser(assets: dict, n_frames: int = 12) -> list[list[np.ndarray]]:
    """Animation 3: 'The MY EYES!! Heart-Boxers Chest-Hair Laser' (8 dirs x 12 frames).
    Whips his pink flamingo bathrobe wide open like giant bat-wings revealing yellow red-heart
    boxer shorts & fires a blinding volumetric hot-pink Chest-Hair Mega-Laser!"""
    views_8 = assets["views_8"]
    heads = assets["heads"]
    flash_stage = assets["flash_stage"]
    feathers = assets["feathers"]

    grid: list[list[np.ndarray]] = []
    for d in range(8):
        roar_480 = graft_monster_head(views_8[d], d, heads, expr="roar", head_tilt_deg=-3.5, red_eyes_glow=1.0)
        grin_480 = graft_monster_head(views_8[d], d, heads, expr="grin", red_eyes_glow=0.8)
        row: list[np.ndarray] = []

        for f in range(n_frames):
            st_im = Image.fromarray(np.zeros((STAGE_H, STAGE_W, 4), dtype=np.uint8), "RGBA")
            draw_ground_shadow(st_im, STAGE_CX, STAGE_GY, rx=68.0 if 2 <= f <= 9 else 56.0, ry=12.0)

            if f in (0, 1):
                # Wind-up crouch clutching belt before whipping robe open!
                u = (f + 1) / 2.0
                H, W = roar_480.shape[:2]
                yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
                sy = 1.0 - 0.08 * u
                sx = 1.0 - 0.05 * u * np.exp(-((yg - 280.0) / 95.0) ** 2)
                coiled = _premul_remap(roar_480, (240.0 + (xg - 240.0) / sx).astype(np.float32), (GROUND_Y - (GROUND_Y - yg) / sy).astype(np.float32))
                st_im.alpha_composite(Image.fromarray(body_480_to_stage(coiled, scale=0.84), "RGBA"))

            elif 2 <= f <= 9:
                beam_u = (f - 2) / 7.0
                flutter = math.sin(beam_u * math.pi * 4.0)

                if d in (0, 1, 7):
                    # Use the authentic winged Heart-Boxers Flash Plate!
                    # Foreshorten slightly on 45°/315° and animate dynamic bat-wing flutter!
                    hy, hx = np.mgrid[0:STAGE_H, 0:STAGE_W].astype(np.float32)
                    wing_dist = np.abs(hx - STAGE_CX) / 190.0
                    open_env = min(1.0, (f - 1.2) / 1.5) * min(1.0, (9.8 - f) / 1.4)
                    sx_angle = (1.0 if d == 0 else 0.84) * (0.68 + 0.34 * open_env + 0.03 * flutter)
                    # Shear slightly on d=1 (-X) or d=7 (+X) for true 45° 3D perspective!
                    persp_dx = (-14.0 if d == 1 else (14.0 if d == 7 else 0.0)) * ((STAGE_GY - hy) / 420.0)
                    wing_wave_y = 9.5 * np.sin(beam_u * math.pi * 4.0 + wing_dist * 2.4) * (wing_dist ** 1.3)
                    src_x = STAGE_CX + (hx - STAGE_CX - persp_dx) / max(0.35, sx_angle)
                    src_y = hy - wing_wave_y
                    fl_posed = _premul_remap(flash_stage, src_x.astype(np.float32), src_y.astype(np.float32))

                    chest_sx = STAGE_CX + (-12.0 if d == 1 else (12.0 if d == 7 else 0.0))
                    chest_sy = STAGE_GY - 336.0
                    _draw_chest_laser_vfx(st_im, d, beam_u, chest_sx, chest_sy, behind_pass=True)
                    st_im.alpha_composite(Image.fromarray(fl_posed, "RGBA"))
                    _draw_chest_laser_vfx(st_im, d, beam_u, chest_sx, chest_sy, behind_pass=False)
                else:
                    # Side & Back views (d=2,3,4,5,6): Planted wide power-stance + billowing Dracula pink robe bat-cape!
                    H, W = roar_480.shape[:2]
                    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
                    open_env = min(1.0, (f - 1.2) / 1.5) * min(1.0, (9.8 - f) / 1.4)
                    cape_w = np.exp(-((yg - 285.0) / 115.0) ** 2)
                    stance_w = np.clip((yg - 435.0) / 155.0, 0.0, 1.0)
                    sx_cape = 1.0 + ((0.44 if d == 4 else (0.34 if d in (3, 5) else 0.22)) * open_env + 0.04 * flutter) * cape_w + (0.18 if d in (3, 4, 5) else 0.06) * stance_w
                    lift_arm_y = 14.0 * open_env * (np.abs(xg - 240.0) / 120.0) ** 1.2 * cape_w
                    flared_480 = _premul_remap(
                        roar_480,
                        (240.0 + (xg - 240.0) / sx_cape).astype(np.float32),
                        (yg + lift_arm_y).astype(np.float32),
                    )

                    chest_sx, chest_sy, _, _ = project_3d_stage(18.0, 0.0, 328.0, d)
                    _draw_chest_laser_vfx(st_im, d, beam_u, chest_sx, chest_sy, behind_pass=True)
                    st_im.alpha_composite(Image.fromarray(body_480_to_stage(flared_480, scale=0.84), "RGBA"))
                    _draw_chest_laser_vfx(st_im, d, beam_u, chest_sx, chest_sy, behind_pass=False)

                # Flying feathers blown outward by the sonic chest blast!
                for fi in range(4):
                    ang_f = beam_u * 2.4 + fi * (math.pi * 0.5) + 0.4
                    fx = STAGE_CX + math.cos(ang_f) * (55.0 + 135.0 * beam_u)
                    fy = (STAGE_GY - 295.0) + math.sin(ang_f) * (45.0 + 95.0 * beam_u)
                    _paste_rotated_rgba(st_im, feathers[fi], fx, fy, angle_deg=math.degrees(ang_f) * 2.0, sx=0.75, sy=0.75, alpha_mul=1.0 - 0.65 * beam_u)

            else:
                # Frames 10..11: Snaps robe shut with a smug maniac grin & rising chest smoke wisp!
                st_im.alpha_composite(Image.fromarray(body_480_to_stage(grin_480, scale=0.84), "RGBA"))
                ov_s = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
                drs = ImageDraw.Draw(ov_s)
                u_s = (f - 9.5) / 2.5
                sx_c, sy_c, _, _ = project_3d_stage(14.0, 0.0, 325.0 + 28.0 * u_s, d)
                drs.ellipse([sx_c - 16, sy_c - 12, sx_c + 16, sy_c + 12], fill=(255, 195, 230, int(145 * (1.0 - u_s * 0.5))))
                st_im.alpha_composite(ov_s.filter(ImageFilter.GaussianBlur(3.2)))

            row.append(np.asarray(st_im, dtype=np.uint8))
        grid.append(row)
    return grid


def build_anim4_flamingo_attack(assets: dict, n_frames: int = 12) -> list[list[np.ndarray]]:
    """Animation 4: 'Dual Fanged Lawn-Flamingo & Hot-Coffee Rampage' (8 dirs x 12 frames).
    Sloshes '#1 MONSTER' hot coffee mug in one hand while swinging a fanged plastic lawn
    flamingo club & launching a laser-eyed torpedo flamingo missile across 360°!"""
    views_8 = assets["views_8"]
    heads = assets["heads"]
    feral_flam = assets["props"]["feral_flam"]
    fly_flam = assets["props"]["fly_flam"]
    mug = assets["props"]["mug"]
    feathers = assets["feathers"]

    grid: list[list[np.ndarray]] = []
    for d in range(8):
        roar_480 = graft_monster_head(views_8[d], d, heads, expr="roar", red_eyes_glow=0.92)
        grin_480 = graft_monster_head(views_8[d], d, heads, expr="grin", red_eyes_glow=0.85)
        row: list[np.ndarray] = []

        for f in range(n_frames):
            u = f / float(n_frames)
            ph = 2.0 * math.pi * u
            base_cur = roar_480 if 2 <= f <= 8 else grin_480
            posed_480 = pose_berserker_robe_480(base_cur, d, f % 8, n_frames=8, berserk_arms=0.85 + 0.45 * math.sin(math.pi * u))

            st_im = Image.fromarray(np.zeros((STAGE_H, STAGE_W, 4), dtype=np.uint8), "RGBA")
            draw_ground_shadow(st_im, STAGE_CX, STAGE_GY, rx=58.0, ry=11.0)
            body_st = Image.fromarray(body_480_to_stage(posed_480, scale=0.84), "RGBA")

            prop_queue = []

            # 1) Left hand (ly = +48 in character right/left): sloshing '#1 MONSTER' Coffee Mug!
            mug_lx = 34.0 + 12.0 * math.sin(ph)
            mug_ly = -48.0
            mug_lz = 265.0 + 24.0 * math.sin(ph + 0.6)
            mx_s, my_s, mdz, msc = project_3d_stage(mug_lx, mug_ly, mug_lz, d)
            mug_rot = 18.0 * math.sin(ph * 2.0)
            prop_queue.append((mdz, "mug", mx_s, my_s, 0.22 * msc, mug_rot, False, 1.0))

            # 2) Right hand (ly = +52): Swinging Fanged Monster Lawn-Flamingo Club!
            swing_ang = -65.0 + 155.0 * (0.5 - 0.5 * math.cos(ph))
            club_lx = 42.0 * math.cos(math.radians(swing_ang * 0.6)) + 18.0
            club_ly = +52.0
            club_lz = 290.0 - 52.0 * math.sin(math.radians(swing_ang * 0.7))
            cx_s, cy_s, cdz, csc = project_3d_stage(club_lx, club_ly, club_lz, d)
            fwd_cx, _, _, _ = project_3d_stage(club_lx + 35.0, club_ly, club_lz, d)
            flip_club = (fwd_cx > cx_s)
            rot_club = (-swing_ang * 0.65) if not flip_club else (swing_ang * 0.65)
            prop_queue.append((cdz - 4.0, "club", cx_s, cy_s, 0.30 * csc, rot_club, flip_club, 1.0))

            # 3) Frames 3..11: Launched Laser-Eyed Torpedo Pink Flamingo Missile!
            missile_info = None
            if f >= 3:
                mu = (f - 3) / 8.5  # 0..1 flight
                mlx = 48.0 + 175.0 * mu
                mly = 12.0 * math.sin(mu * math.pi * 2.0)
                mlz = 285.0 + 16.0 * math.sin(mu * math.pi)
                msx, msy, mdz_m, msc_m = project_3d_stage(mlx, mly, mlz, d)
                msx2, msy2, _, _ = project_3d_stage(mlx + 30.0, mly, mlz, d)
                flip_m = (msx2 > msx)
                ang_m = math.degrees(math.atan2(-(msy2 - msy), abs(msx2 - msx) + 1e-3))
                if flip_m:
                    ang_m = -ang_m
                alpha_m = 1.0 if mu < 0.78 else max(0.0, (1.0 - mu) / 0.22)
                missile_info = (mdz_m - 12.0, msx, msy, 0.31 * msc_m, ang_m, flip_m, alpha_m, mu)

            def _draw_queued(behind: bool) -> None:
                for dz_i, kind, px, py, sc_i, rot_i, fl_i, al_i in prop_queue:
                    if (dz_i >= 0) == behind:
                        im_p = mug if kind == "mug" else feral_flam
                        paste_prop_rgba(st_im, im_p, px, py, scale=sc_i, rot_deg=rot_i, flip_x=fl_i, alpha_mul=al_i)
                if missile_info is not None:
                    mdz_m, msx, msy, msc_m, ang_m, flip_m, alpha_m, mu = missile_info
                    if (mdz_m >= 0) == behind and alpha_m > 0.03:
                        # Hot-pink contrail & whoosh behind torpedo flamingo
                        ov_m = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
                        drm = ImageDraw.Draw(ov_m)
                        tx0, ty0, _, _ = project_3d_stage(max(25.0, 48.0 + 175.0 * max(0.0, mu - 0.30)), 0.0, 285.0, d)
                        drm.line([(tx0, ty0), (msx, msy)], fill=(255, 65, 175, int(195 * alpha_m)), width=8)
                        drm.line([(tx0, ty0), (msx, msy)], fill=(255, 230, 248, int(230 * alpha_m)), width=3)
                        st_im.alpha_composite(ov_m.filter(ImageFilter.GaussianBlur(1.4)))
                        paste_prop_rgba(st_im, fly_flam, msx, msy, scale=msc_m, rot_deg=ang_m, flip_x=flip_m, alpha_mul=alpha_m)

            _draw_queued(behind=True)
            st_im.alpha_composite(body_st)

            # Melee swing whoosh crescent on peak swing frames f=2..5
            if 2 <= f <= 5:
                ov_w = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
                drw = ImageDraw.Draw(ov_w)
                pts_arc = []
                for ak in range(7):
                    au = ak / 6.0
                    ax, ay, _, _ = project_3d_stage(35.0 + 55.0 * math.sin(math.pi * au), 52.0 - 40.0 * au, 335.0 - 115.0 * au, d)
                    pts_arc.append((ax, ay))
                drw.line(pts_arc, fill=(255, 95, 185, 175), width=10)
                drw.line(pts_arc, fill=(255, 235, 250, 210), width=4)
                st_im.alpha_composite(ov_w.filter(ImageFilter.GaussianBlur(1.5)))

            _draw_queued(behind=False)

            # Spilling dark coffee droplets + pink feathers!
            ov_sp = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            drsp = ImageDraw.Draw(ov_sp)
            for di in range(4):
                du = ((u * 2.0 + di * 0.25) % 1.0)
                drop_x = mx_s + (-16.0 + di * 11.0) * du * 2.2
                drop_y = my_s - 18.0 - 22.0 * du + 58.0 * (du * du)
                drsp.ellipse([drop_x - 3.5, drop_y - 3.5, drop_x + 3.5, drop_y + 3.5], fill=(72, 36, 16, int(225 * (1.0 - du))))
            st_im.alpha_composite(ov_sp)

            for fi in range(3):
                fu = ((u + fi * 0.33) % 1.0)
                fx_p, fy_p, _, sc_p = project_3d_stage(30.0 + 120.0 * fu, 28.0 * math.sin(ph + fi * 2.0), 270.0 + 40.0 * math.cos(ph + fi), d)
                _paste_rotated_rgba(st_im, feathers[fi], fx_p, fy_p, angle_deg=fu * 360.0, sx=0.70 * sc_p, sy=0.70 * sc_p, alpha_mul=math.sin(math.pi * fu))

            row.append(np.asarray(st_im, dtype=np.uint8))
        grid.append(row)
    return grid


def _make_quake_meat_gibs(rng: np.random.Generator, count: int = 14) -> list[Image.Image]:
    """Generates glossy 3D-lit Quake meat & rib-bone gib sprites."""
    gibs: list[Image.Image] = []
    for gi in range(count):
        sz = int(rng.integers(24, 40))
        gy, gx = np.mgrid[0:sz, 0:sz].astype(np.float32)
        c = sz * 0.5
        ang = np.arctan2(gy - c, gx - c)
        rad = (sz * 0.34) * (1.0 + 0.24 * np.sin(3.0 * ang + gi) + 0.16 * np.cos(5.0 * ang + gi * 1.7))
        dist = np.hypot(gx - c, gy - c)
        inside = dist <= rad
        nx_g = (gx - c) / np.maximum(rad, 1.0)
        ny_g = (gy - c) / np.maximum(rad, 1.0)
        lit = np.clip(0.66 - 0.38 * nx_g - 0.42 * ny_g, 0.18, 1.15)
        spec = np.exp(-(((nx_g + 0.32) / 0.24) ** 2 + ((ny_g + 0.32) / 0.24) ** 2)) * 0.65
        gim = np.zeros((sz, sz, 4), dtype=np.uint8)
        gim[inside, 0] = np.clip(186.0 * lit[inside] + 75.0 * spec[inside], 0, 255).astype(np.uint8)
        gim[inside, 1] = np.clip(18.0 * lit[inside] + 55.0 * spec[inside], 0, 255).astype(np.uint8)
        gim[inside, 2] = np.clip(24.0 * lit[inside] + 55.0 * spec[inside], 0, 255).astype(np.uint8)
        gim[inside, 3] = 255
        if gi % 3 == 0:
            bone = (np.abs(gy - c + (gx - c) * 0.38) < 2.2) & (gx > c - rad * 0.55) & (gx < c + rad * 0.92)
            gim[bone, :3] = [242, 232, 218]
            gim[bone, 3] = 255
        gibs.append(Image.fromarray(gim, "RGBA"))
    return gibs


def build_anim5_flamingo_gib_death(assets: dict, n_frames: int = 24) -> list[np.ndarray]:
    """Animation 5: 'Catastrophic Flamingo Feather & Gib Explosion' (24-frame 4-Act Death).
      Act 1 (0..4)  : Crooked-sunglasses Shock 'O' face + pink pressure-cooker balloon swell & arcs
      Act 2 (5..11) : Quake VFX fireball + HDR starburst + 48 hot-pink flamingo feathers + 14 meaty gibs
                      + flying bare legs/sleeves + flying coffee mug + 2 panicked flying flamingos!
      Act 3 (12..18): Severed bearded shock-head plummets from top & double-bounces on floor!
      Act 4 (19..23): Settles into smoking crumpled Pink Flamingo Bathrobe Pile w/ crooked sunglasses!
    """
    n0 = assets["views_8"][0]
    heads = assets["heads"]
    fly_flam = assets["props"]["fly_flam"]
    mug = assets["props"]["mug"]
    pile = assets["props"]["pile"]
    feathers = assets["feathers"]
    vfx_fb = _load_vfx_fireball_rgba()

    shock_480 = graft_monster_head(n0, 0, heads, expr="shock", red_eyes_glow=0.0)
    shock_posed = pose_berserker_robe_480(shock_480, 0, 0, n_frames=8, berserk_arms=1.15)
    shock_stage = body_480_to_stage(shock_posed, scale=0.84)

    # Severed head sprite (scaled cleanly to match character head size ~76px wide)
    sev_head_arr = resize_rgba_premul(heads["shock"], 78, int(round(heads["shock"].shape[0] * (78.0 / heads["shock"].shape[1]))))
    sev_head_pil = Image.fromarray(sev_head_arr, "RGBA")

    # Flying limbs cut from n0
    l_sleeve = Image.fromarray(resize_rgba_premul(crop_tight_rgba(n0[165:370, 136:194]), 38, 125), "RGBA")
    r_sleeve = Image.fromarray(resize_rgba_premul(crop_tight_rgba(n0[165:370, 286:344]), 38, 125), "RGBA")
    l_foot = Image.fromarray(resize_rgba_premul(crop_tight_rgba(n0[452:596, 170:232]), 40, 112), "RGBA")
    r_foot = Image.fromarray(resize_rgba_premul(crop_tight_rgba(n0[452:596, 248:310]), 40, 112), "RGBA")
    mug_pil = Image.fromarray(resize_rgba_premul(mug, 62, 68), "RGBA")
    flam_l_pil = Image.fromarray(resize_rgba_premul(fly_flam, 128, 65), "RGBA")
    flam_r_pil = Image.fromarray(resize_rgba_premul(fly_flam[:, ::-1, :].copy(), 128, 65), "RGBA")
    pile_arr = resize_rgba_premul(pile, 232, int(round(pile.shape[0] * (232.0 / pile.shape[1]))))
    pile_pil = Image.fromarray(pile_arr, "RGBA")

    rng = np.random.default_rng(20261101)
    gibs_pil = _make_quake_meat_gibs(rng, 14)

    DET_F = 5
    dt = 1.0 / 16.0
    GRAV = 1280.0
    gy = float(STAGE_GY)
    cx = float(STAGE_CX)

    gibs = []
    for gi, gim in enumerate(gibs_pil):
        ang_g = math.radians(-162.0 + (gi / 13.0) * 144.0 + rng.uniform(-7.0, 7.0))
        spd = rng.uniform(190.0, 440.0)
        gibs.append(dict(
            img=gim, x=cx + rng.uniform(-18, 18), y=gy - rng.uniform(160, 310),
            vx=math.cos(ang_g) * spd * 0.72, vy=math.sin(ang_g) * spd,
            ang=rng.uniform(0, 360), omg=rng.uniform(-780, 780),
            rad=gim.height * 0.35, bounce=rng.uniform(0.30, 0.46),
        ))

    bodies = [
        dict(name="lsleeve", img=l_sleeve, x=cx - 56, y=gy - 285, vx=-235.0, vy=-325.0, ang=-22.0, omg=-720.0, rad=22.0, bounce=0.35),
        dict(name="rsleeve", img=r_sleeve, x=cx + 56, y=gy - 285, vx=+245.0, vy=-285.0, ang=+22.0, omg=+660.0, rad=22.0, bounce=0.35),
        dict(name="lfoot",   img=l_foot,   x=cx - 34, y=gy - 115, vx=-195.0, vy=-295.0, ang=-18.0, omg=-560.0, rad=22.0, bounce=0.34),
        dict(name="rfoot",   img=r_foot,   x=cx + 34, y=gy - 115, vx=+180.0, vy=-255.0, ang=+18.0, omg=+480.0, rad=22.0, bounce=0.34),
        # Mug bounces off to the left floor while severed head bounces off to the right floor, framing the robe pile!
        dict(name="mug",     img=mug_pil,  x=cx - 28, y=gy - 290, vx=-168.0, vy=-380.0, ang=0.0,   omg=-940.0, rad=24.0, bounce=0.38),
        dict(name="head",    img=sev_head_pil, x=cx + 18.0, y=gy - 375.0, vx=+96.0, vy=-345.0, ang=0.0, omg=+480.0, rad=34.0, bounce=0.42),
    ]

    feather_parts = []
    for fi in range(48):
        ang_f = rng.uniform(0.0, 2.0 * math.pi)
        spd_f = rng.uniform(85.0, 390.0)
        feather_parts.append(dict(
            img=feathers[fi % len(feathers)],
            x=cx + rng.uniform(-22, 22),
            y=gy - rng.uniform(150, 340),
            vx=math.cos(ang_f) * spd_f * 0.85,
            vy=math.sin(ang_f) * spd_f - rng.uniform(40, 150),
            ang=rng.uniform(0, 360),
            omg=rng.uniform(-420, 420),
            phase=rng.uniform(0, 6.28),
            scale=rng.uniform(0.62, 1.08),
        ))

    frames_out: list[np.ndarray] = []
    hy, hx = np.mgrid[0:STAGE_H, 0:STAGE_W].astype(np.float32)

    for f in range(n_frames):
        stage = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))

        # ACT 1 (0..4): Hit Shock & Pink Flamingo Balloon Overload!
        if f < DET_F:
            ov = (f + 1) / float(DET_F)
            draw_ground_shadow(stage, cx, gy, rx=58.0 + 14.0 * ov, ry=11.0)
            core_x, core_y = cx, gy - 265.0
            rc = np.sqrt(((hx - core_x) / 68.0) ** 2 + ((hy - core_y) / 108.0) ** 2)
            bloat = np.exp(-(rc ** 2)) * (0.30 * (ov ** 1.35) + 0.05 * math.sin(f * 3.4))
            arr = _premul_remap(shock_stage, (hx - (hx - core_x) * bloat).astype(np.float32), (hy - (hy - core_y) * bloat).astype(np.float32)).astype(np.float32)

            glow = np.exp(-(((hx - core_x) / (46.0 + 42.0 * ov)) ** 2 + ((hy - core_y) / (68.0 + 55.0 * ov)) ** 2)) * (arr[..., 3] > 50)
            arr[..., 0] = np.clip(arr[..., 0] + glow * 250.0 * ov, 0, 255)
            arr[..., 1] = np.clip(arr[..., 1] + glow * 85.0 * (ov ** 1.5), 0, 255)
            arr[..., 2] = np.clip(arr[..., 2] + glow * 195.0 * ov, 0, 255)

            jx = int(round(math.sin(f * 4.5) * (2.0 + 6.5 * ov)))
            jy = int(round(math.cos(f * 5.2) * (1.5 + 4.0 * ov)))
            _safe_alpha_composite(stage, Image.fromarray(arr.astype(np.uint8), "RGBA"), jx, jy)

            if f >= 2:
                arc_im = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
                dra = ImageDraw.Draw(arc_im)
                for _ in range(4 + int(6 * ov)):
                    ang_b = rng.uniform(0, 2 * math.pi)
                    pts = [(core_x + jx, core_y + jy)]
                    bx_c, by_c = float(core_x + jx), float(core_y + jy)
                    for _ in range(4):
                        ang_b += rng.uniform(-0.65, 0.65)
                        sl = rng.uniform(16.0, 36.0) * (0.5 + 0.7 * ov)
                        bx_c += math.cos(ang_b) * sl
                        by_c += math.sin(ang_b) * sl
                        pts.append((bx_c, by_c))
                    dra.line(pts, fill=(255, 55, 175, int(230 * ov)), width=5)
                    dra.line(pts, fill=(255, 245, 252, int(252 * ov)), width=2)
                stage.alpha_composite(arc_im)

            frames_out.append(np.asarray(stage, dtype=np.uint8))
            continue

        # ACT 2..4 (f >= DET_F): Scorch crater + Crumpled Pink Bathrobe Heap settling + Gibs + Feathers!
        ef = f - DET_F  # 0..18
        u_post = ef / float(n_frames - 1 - DET_F)

        # Floor scorch & crimson splatter
        fl_im = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        fdr = ImageDraw.Draw(fl_im)
        fdr.ellipse([cx - 102, gy - 14, cx + 102, gy + 14], fill=(24, 18, 22, 210))
        fdr.ellipse([cx - 64, gy - 8, cx + 64, gy + 10], fill=(138, 14, 24, 218))
        stage.alpha_composite(fl_im.filter(ImageFilter.GaussianBlur(1.4)))

        # Defeated Crumpled Pink Flamingo Bathrobe & Crooked Sunglasses Pile (materializes cleanly out of the fireball!)
        if ef >= 3:
            pile_u = min(1.0, (ef - 2.0) / 5.0)
            drop_dy = -38.0 * ((1.0 - pile_u) ** 2)
            # Subtle comical flamingo-head twitch on the final frames!
            twitch_deg = 2.2 * math.sin(ef * 2.4) if ef >= 12 else 0.0
            _paste_rotated_rgba(stage, pile_pil, cx, gy - pile_pil.height * 0.42 + drop_dy, angle_deg=twitch_deg, alpha_mul=min(1.0, pile_u * 1.25))

        # Evolving Quake VFX Fireball + Hot-Pink Shockwave Ring!
        if ef < 12:
            fb_u = ef / 12.0
            fb_pad = Image.new("RGBA", (STAGE_W + 240, STAGE_H + 240), (0, 0, 0, 0))
            _blit_evolving_vfx_fireball(fb_pad, vfx_fb, cx + 120.0, gy - 215.0 + 120.0, fb_u, max_diam=335.0, rot_deg=ef * 6.0)
            _safe_alpha_composite(stage, fb_pad, -120, -120)
        if ef <= 3:
            sb_im = _draw_hdr_starburst((STAGE_W, STAGE_H), cx, gy - 230.0, radius=135.0, intensity=max(0.0, 1.0 - ef / 3.6))
            stage.alpha_composite(sb_im)

        # Rising dark smoke wisps over the crumpled bathrobe pile in Acts 3..4
        if ef >= 6:
            sm_im = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            smd = ImageDraw.Draw(sm_im)
            for si in range(5):
                su = ((ef - 6 + si * 2.3) % 11.0) / 11.0
                sx_s = cx + (-45.0 + si * 22.0) + 12.0 * math.sin(su * 6.0 + si)
                sy_s = gy - 42.0 - 135.0 * su
                sr_s = 12.0 + 24.0 * su
                sa_s = int(115 * math.sin(math.pi * su))
                smd.ellipse([sx_s - sr_s, sy_s - sr_s * 0.8, sx_s + sr_s, sy_s + sr_s * 0.8], fill=(54, 48, 56, sa_s))
            stage.alpha_composite(sm_im.filter(ImageFilter.GaussianBlur(3.2)))

        # Two panicked Flying Pink Flamingos rocketing off left & right!
        if ef < 10:
            flu = ef / 9.5
            fl_a = 1.0 if flu < 0.65 else max(0.0, (1.0 - flu) / 0.35)
            flap_w = 14.0 * math.sin(ef * 2.2)
            _paste_rotated_rgba(stage, flam_l_pil, cx - 64.0 - 210.0 * flu, gy - 265.0 - 105.0 * flu, angle_deg=24.0 + flap_w, sx=0.88, sy=0.88, alpha_mul=fl_a)
            _paste_rotated_rgba(stage, flam_r_pil, cx + 64.0 + 210.0 * flu, gy - 250.0 - 115.0 * flu, angle_deg=-24.0 - flap_w, sx=0.88, sy=0.88, alpha_mul=fl_a)

        # 14 Quake Meat & Bone Gibs
        fade_gibs = 1.0 if ef < 14 else max(0.0, 1.0 - (ef - 14) / 5.0)
        for gb in gibs:
            if ef > 0:
                gb["vy"] += GRAV * dt
                gb["x"] += gb["vx"] * dt
                gb["y"] += gb["vy"] * dt
                gb["ang"] += gb["omg"] * dt
                if gb["y"] >= gy - gb["rad"]:
                    gb["y"] = gy - gb["rad"]
                    gb["vy"] = -abs(gb["vy"]) * gb["bounce"] if abs(gb["vy"]) > 65.0 else 0.0
                    gb["vx"] *= 0.62
                    gb["omg"] *= 0.55
                gb["x"] = float(np.clip(gb["x"], 24.0, STAGE_W - 24.0))
            if fade_gibs > 0.04:
                _paste_rotated_rgba(stage, gb["img"], gb["x"], gb["y"], gb["ang"], alpha_mul=fade_gibs, max_bottom_y=gy + 4)

        # Flying Limbs, Coffee Mug & Double-Bouncing Severed Bearded Sunglasses Head!
        for bd in bodies:
            if ef > 0:
                bd["vy"] += GRAV * dt
                bd["x"] += bd["vx"] * dt
                bd["y"] += bd["vy"] * dt
                bd["ang"] += bd["omg"] * dt
                # Keep severed head inside top margin so it never clips!
                if bd["name"] == "head" and bd["y"] < 54.0:
                    bd["y"] = 54.0
                    bd["vy"] = abs(bd["vy"]) * 0.35
                if bd["y"] >= gy - bd["rad"]:
                    bd["y"] = gy - bd["rad"]
                    if abs(bd["vy"]) > 60.0:
                        bd["vy"] = -abs(bd["vy"]) * bd["bounce"]
                        bd["vx"] *= 0.65
                        bd["omg"] *= 0.52
                    else:
                        bd["vy"] = 0.0
                        bd["vx"] *= 0.60
                        bd["omg"] *= 0.35
                bd["x"] = float(np.clip(bd["x"], 36.0, STAGE_W - 36.0))
            b_alpha = 1.0 if bd["name"] in ("head", "mug") else fade_gibs
            if b_alpha > 0.04:
                _paste_rotated_rgba(stage, bd["img"], bd["x"], bd["y"], bd["ang"], alpha_mul=b_alpha, max_bottom_y=gy + 5)

        # 48 Fluttering Hot-Pink Flamingo Feathers with aerodynamic drag & gentle descent!
        for fp in feather_parts:
            if ef > 0:
                fp["vx"] = fp["vx"] * 0.88 + 26.0 * math.sin(ef * 0.55 + fp["phase"])
                fp["vy"] = min(92.0, fp["vy"] * 0.86 + 210.0 * dt)
                fp["x"] += fp["vx"] * dt
                fp["y"] = min(gy - 4.0, fp["y"] + fp["vy"] * dt)
                fp["ang"] += fp["omg"] * dt * 0.45 + 12.0 * math.cos(ef * 0.6 + fp["phase"])
            if 10.0 <= fp["x"] <= STAGE_W - 10.0 and 8.0 <= fp["y"] <= gy + 4.0:
                f_al = 1.0 if ef < 15 else max(0.25, 1.0 - (ef - 15) * 0.14)
                _paste_rotated_rgba(stage, fp["img"], fp["x"], fp["y"], fp["ang"], sx=fp["scale"], sy=fp["scale"], alpha_mul=f_al)

        frames_out.append(np.asarray(stage, dtype=np.uint8))

    return frames_out


def synthesize_all_5_animations(assets: dict | None = None) -> dict:
    if assets is None:
        assets = load_all_robeguy_assets()
    with ThreadPoolExecutor(max_workers=5) as ex:
        f1 = ex.submit(build_anim1_monster_idle, assets, 8)
        f2 = ex.submit(build_anim2_berserker_charge, assets, 8)
        f3 = ex.submit(build_anim3_robe_flash_laser, assets, 12)
        f4 = ex.submit(build_anim4_flamingo_attack, assets, 12)
        f5 = ex.submit(build_anim5_flamingo_gib_death, assets, 24)
        return {
            "monster_idle": f1.result(),
            "berserker_charge": f2.result(),
            "robe_flash_laser": f3.result(),
            "flamingo_attack": f4.result(),
            "flamingo_gib_death": f5.result(),
        }
