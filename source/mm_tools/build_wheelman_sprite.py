r"""Builds the complete 360-degree rolling Wheelman monster sprite for BakersfieldQuake (DarkPlaces).

Sources (source/mm_tools/ref/):
  - wheelman_body.jpg            Authentic front body/axle/chrome-cylinder/wheels photo
  - wheelman_face.png / face2.png Shocked face & spiky hair references
  - wheelman_views/view_*.jpg    Photorealistic 360° turnaround & limb-completion studio plates

Game Contract (matches source/mm_tools/wheelman.qc Wheelman_Customize, impulse 18):
  - progs/wheelman.spr32         DarkPlaces IDSP v32, type 0 (SPR_VP_PARALLEL_UPRIGHT),
                                 320x304 canvas, origin (-160, 288) anchored at wheel ground contact.
  - 56 frames total:
      0..7                       8-direction idle (d = 0..7)
      8 + d*6 + k                8-direction rolling (d = 0..7, k = 0..5)
      d=0 Front (0°), d=1 Front-Left (45°), d=2 Screen-Left Profile (90°),
      d=3 Back-Left (135°), d=4 Back (180°), d=5 Back-Right (225°),
      d=6 Screen-Right Profile (270°), d=7 Front-Right (315°).
  - Toned for r_hdr_scenebrightness 2.5 (contrast 1.20, brightness 0.50).
  - Interactive 360° drag-to-turn & rolling viewer written to wheelman_sprite/index.html.
"""
import base64
import io
import json
import math
import os
import struct
import sys
import cv2
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import wheelman_fx as fx
import wheelman_boom360 as b360
import wheelman_stunts as stunts
from wheelman_viewer_html import VIEWER_HTML

MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
REF_DIR = os.path.join(HERE, "ref")
VIEWS_DIR = os.path.join(REF_DIR, "wheelman_views")
PROGS_DIR = os.path.join(MOD_DIR, "progs")
STAGED_PROGS_DIR = os.path.abspath(os.path.join(MOD_DIR, "..", "_bakersfield_dev", "staged_assets", "progs"))
OUT_DIR = os.path.join(HERE, "out", "wheelman")
VIEWER_DIR = os.path.join(MOD_DIR, "wheelman_sprite")

CANVAS = (320, 304)
GROUND = 288
WIDE_CANVAS = (480, 340)
WIDE_GROUND = 308
SPR_CANVAS = (144, 102)   # 0.30x of WIDE_CANVAS=(480,340) (0.48x of 300x212); paired with WC_SCALE = 1.0417 in wcannon_defs.qc
SPR_GROUND = 92           # round(308 * 0.30)

N_DIR = 8
N_ANIM = 12               # 12 smooth high-FPS rolling/driving frames per direction (96 total)
N_SCREAM = 12             # 12 high-FPS screaming frames per direction (96 total; 6 per dir in SPR32)
N_EXPLODE_SPR_STEPS = 14  # 4 tiers x 8 directions x 14 steps = 448 directional 360° explosion frames in SPR32!


# ---------------------------------------------------------------------------
# 1. Geometry, Chroma-Keying & Seamless Skin Diffusion Helpers
# ---------------------------------------------------------------------------

def seg_dist_grid(xg, yg, x0, y0, x1, y1):
    vx, vy = x1 - x0, y1 - y0
    l2 = max(vx * vx + vy * vy, 1e-6)
    t = np.clip(((xg - x0) * vx + (yg - y0) * vy) / l2, 0.0, 1.0)
    return np.hypot(xg - (x0 + t * vx), yg - (y0 + t * vy))


def rot_ell_grid(xg, yg, cx, cy, rx, ry, ang_deg):
    rad = math.radians(ang_deg)
    ca, sa = math.cos(rad), math.sin(rad)
    dx, dy = xg - cx, yg - cy
    u = (dx * ca + dy * sa) / max(rx, 1e-4)
    v = (-dx * sa + dy * ca) / max(ry, 1e-4)
    return u * u + v * v


def key_studio_magenta(im_rgb):
    """High-precision #FF00FF chroma key with un-premultiply and warm-safe magenta-excess despill."""
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()
    m = np.minimum(r, b) - g

    bg_strict = (m > 62.0) & (r > 100.0) & (b > 100.0)
    dist = ndimage.distance_transform_edt(~bg_strict)

    alpha = np.ones_like(m, dtype=np.float32)
    alpha[bg_strict] = 0.0
    edge = (~bg_strict) & (dist <= 8.0)
    a_ramp = np.clip(1.0 - (m - 12.0) / 52.0, 0.0, 1.0)
    use_ramp = edge & (m > 12.0)
    alpha[use_ramp] = np.where(a_ramp[use_ramp] <= 0.05, 0.0, a_ramp[use_ramp])

    semi = (alpha > 0.0) & (alpha < 0.995)
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.25)
    r[semi] = np.clip((r[semi] - inv * 255.0) / denom, 0.0, 255.0)
    g[semi] = np.clip(g[semi] / denom, 0.0, 255.0)
    b[semi] = np.clip((b[semi] - inv * 255.0) / denom, 0.0, 255.0)

    dsp = (alpha > 0.0) & (dist <= 7.0)
    spill = np.maximum(0.0, b[dsp] - g[dsp])
    is_mag = (r[dsp] - g[dsp]) > 8.0
    b[dsp] = np.where(is_mag, b[dsp] - spill, b[dsp])
    r[dsp] = np.where(is_mag, np.maximum(g[dsp], r[dsp] - 0.62 * spill), r[dsp])

    lbl, num = ndimage.label(alpha > 0.08)
    if num > 1:
        sizes = ndimage.sum(alpha > 0.08, lbl, range(1, num + 1))
        main_id = 1 + int(np.argmax(sizes))
        keep = ndimage.binary_dilation(lbl == main_id, iterations=5)
        alpha[~keep] = 0.0

    rgba = np.dstack([
        np.clip(np.round(r), 0, 255).astype(np.uint8),
        np.clip(np.round(g), 0, 255).astype(np.uint8),
        np.clip(np.round(b), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])
    return Image.fromarray(rgba, "RGBA")


def calibrate_skin_to_ref(rgba_im, ref_skin_samples, strength=0.60):
    """Aligns warm skin tone of turnaround views to wheelman_body.jpg chest/thigh skin."""
    arr = np.array(rgba_im).astype(np.float32)
    rgb = arr[..., :3]
    a = arr[..., 3] / 255.0
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    rg = rgb[..., 0] - rgb[..., 1]
    rb = rgb[..., 0] - rgb[..., 2]
    skin_m = (a > 0.85) & (rb > 18.0) & (rg > 12.0) & (lum > 65.0) & (lum < 215.0)
    if np.sum(skin_m) < 200:
        return rgba_im
    src_mean = rgb[skin_m].mean(axis=0)
    tgt_mean = ref_skin_samples.astype(np.float32).mean(axis=0)
    gain = np.clip(tgt_mean / np.maximum(src_mean, 1.0), 0.82, 1.25)
    w_s = (np.clip((rb - 12.0) / 16.0, 0.0, 1.0) * np.clip((lum - 42.0) / 28.0, 0.0, 1.0) * strength)[..., None]
    scaled = np.clip(rgb * gain[None, None, :], 0.0, 255.0)
    arr[..., :3] = rgb * (1.0 - w_s) + scaled * w_s
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def warp_rgba_similarity(rgba_src, src_pt, dst_pt, scale, angle_cw_deg, out_wh):
    rad = math.radians(angle_cw_deg)
    ca, sa = math.cos(rad) * scale, math.sin(rad) * scale
    sx, sy = src_pt
    dx, dy = dst_pt
    M = np.array([
        [ca, -sa, dx - (ca * sx - sa * sy)],
        [sa,  ca, dy - (sa * sx + ca * sy)],
    ], dtype=np.float32)
    sf = rgba_src.astype(np.float32)
    sa_f = sf[..., 3:4] / 255.0
    pm = np.concatenate([sf[..., :3] * sa_f, sf[..., 3:4]], axis=-1)
    W_o, H_o = out_wh
    pm_w = cv2.warpAffine(pm, M, (W_o, H_o), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT)
    wa = pm_w[..., 3:4] / 255.0
    wrgb = np.where(wa > 1e-4, pm_w[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([np.clip(wrgb, 0, 255).astype(np.uint8), np.clip(pm_w[..., 3], 0, 255).astype(np.uint8)])


def match_patch_skin(patch_rgba, src_mask, tgt_rgb_samples):
    out = patch_rgba.astype(np.float32).copy()
    rgb = out[..., :3]
    a = out[..., 3] / 255.0
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    rb = rgb[..., 0] - rgb[..., 2]
    skin_px = src_mask & (a > 0.85) & (rb > 16.0) & (lum > 70.0) & (lum < 225.0)
    if np.sum(skin_px) < 80:
        return patch_rgba
    s_mean = rgb[skin_px].mean(axis=0)
    t_mean = tgt_rgb_samples.astype(np.float32).mean(axis=0)
    gain = np.clip(t_mean / np.maximum(s_mean, 1.0), 0.78, 1.28)
    mapped = rgb * gain[None, None, :]
    w_skin = np.clip((rb - 10.0) / 14.0, 0.0, 1.0) * np.clip((lum - 44.0) / 24.0, 0.0, 1.0)
    out[..., :3] = np.clip(rgb * (1.0 - w_skin[..., None]) + mapped * w_skin[..., None], 0.0, 255.0)
    return out.astype(np.uint8)


def inpaint_region_with_surrounding_skin(rgba_im, hole_mask, cleft_x=None, grain_src_box=None):
    """Multi-scale normalized Gaussian pull-push diffusion from surrounding bare skin pixels.
    Produces zero-seam skin continuity across hip/back regions with real pore/freckle grain."""
    arr = np.array(rgba_im).astype(np.float32)
    rgb = arr[..., :3]
    a = arr[..., 3] / 255.0
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

    hole = ndimage.binary_dilation(hole_mask, iterations=5) & (a > 0.15)
    if np.sum(hole) < 15:
        return rgba_im

    known = (~hole) & (a > 0.85) & ((rgb[..., 0] - rgb[..., 2]) > 17.0) & (lum > 68.0) & (lum < 235.0)
    seed_rgb = np.where(known[..., None], rgb, 0.0)
    seed_w = known.astype(np.float32)

    filled = np.zeros_like(rgb)
    total_conf = np.zeros_like(seed_w)
    for sigma in (96.0, 48.0, 24.0, 11.0, 4.8):
        ksize = int(sigma * 4) | 1
        num_s = cv2.GaussianBlur(seed_rgb, (ksize, ksize), sigma)
        den_s = cv2.GaussianBlur(seed_w, (ksize, ksize), sigma)
        valid = den_s > 1e-5
        layer = np.where(valid[..., None], num_s / np.maximum(den_s[..., None], 1e-5), 0.0)
        w_take = np.clip(den_s * 14.0, 0.0, 1.0)
        filled = np.where(total_conf[..., None] == 0, layer, filled * (1.0 - w_take[..., None]) + layer * w_take[..., None])
        total_conf = np.maximum(total_conf, w_take)

    dist_sil = ndimage.distance_transform_edt(a > 0.5)
    sil_shade = 0.83 + 0.17 * np.clip(dist_sil / 32.0, 0.0, 1.0)
    filled = filled * sil_shade[..., None]

    H, W = a.shape
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    if grain_src_box is not None:
        gx0, gy0, gx1, gy1 = grain_src_box
        g_patch = rgb[gy0:gy1, gx0:gx1]
        g_hi = g_patch - cv2.GaussianBlur(g_patch, (15, 15), 3.8)
        gh, gw = g_hi.shape[:2]
        tiled = np.tile(g_hi, (H // gh + 2, W // gw + 2, 1))[:H, :W]
        filled = filled + tiled * 0.72

    if cleft_x is not None:
        cleft = np.exp(-((xg - cleft_x) / 10.5) ** 2) * np.clip((yg - 675.0) / 55.0, 0.0, 1.0) * 0.20
        filled = filled * (1.0 - cleft[..., None])

    blend_w = cv2.GaussianBlur(hole.astype(np.float32), (11, 11), 2.6) * (a > 0.10)
    arr[..., :3] = np.clip(rgb * (1.0 - blend_w[..., None]) + filled * blend_w[..., None], 0.0, 255.0)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------------------
# 2. Authentic Front Photo Extraction + Seamless 360° Master View Assembly
# ---------------------------------------------------------------------------

def extract_clean_body_photo(body_path):
    """Segments wheelman_body.jpg preserving 100% solid wheels, white axle spacers, steel axle,
    chrome cylinder + fluted cap, bare torso & V-thighs, leveled -6.0 deg CW."""
    rgb = np.array(Image.open(body_path).convert("RGB"))
    H, W = rgb.shape[:2]
    rf = rgb.astype(np.float32)
    r, g, b = rf[..., 0], rf[..., 1], rf[..., 2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    sheet_blue = (b - r >= 4.5) & (gray > 42.0) & (gray < 186.0)
    ff = (sheet_blue.astype(np.uint8)) * 255
    fmask = np.zeros((H + 2, W + 2), np.uint8)
    seeds = [
        (2, 350), (W - 3, 220), (W // 2, H - 3), (2, H - 3), (W - 3, H - 3),
        (650, 40), (260, 40), (450, 720), (880, 720), (380, 610), (840, 540),
        (480, 655), (840, 625), (740, 790),
    ]
    for sx, sy in seeds:
        if ff[sy, sx] == 255:
            cv2.floodFill(ff, fmask, (sx, sy), 128)
    bg_sheet = (ff == 128)

    skin = (r - b > 13.0) & (r > 65.0) & (gray > 42.0)
    top_right_corner = (xg > 1175) & (yg < 180) & (~skin)
    old_neck_curls = (yg < 76) & ((xg < 426) | (xg > 562)) & (xg > 335) & (xg < 635)
    butt_axle_gap = (yg > 565) & (yg < 658) & (xg > 335) & (xg < 995) & (gray < 68.0) & ((r - b) < 13.0)
    bg_def = bg_sheet | top_right_corner | old_neck_curls | butt_axle_gap

    m_lwheel = rot_ell_grid(xg, yg, 203.0, 660.0, 89.0, 283.0, -4.5) <= 1.0
    m_lnut = (xg >= 75) & (xg <= 122) & (yg >= 652) & (yg <= 724) & (~bg_sheet)
    m_lspacer = (xg >= 268) & (xg <= 338) & (yg >= 635) & (yg <= 692) & (~bg_sheet)

    m_rwheel = rot_ell_grid(xg, yg, 1115.0, 554.0, 139.0, 272.0, -6.5) <= 1.0
    m_rspacer = (xg >= 992) & (xg <= 1088) & (yg >= 550) & (yg <= 614) & (~bg_sheet)

    d_ax_l = seg_dist_grid(xg, yg, 330.0, 656.5, 608.0, 628.0)
    d_ax_r = seg_dist_grid(xg, yg, 682.0, 618.0, 998.0, 585.0)
    m_axle = (d_ax_l <= 7.2) | (d_ax_r <= 7.2)

    vx_c, vy_c = 733.0 - 614.0, 716.0 - 536.0
    tc = np.clip(((xg - 614.0) * vx_c + (yg - 536.0) * vy_c) / (vx_c * vx_c + vy_c * vy_c), 0.0, 1.0)
    dc = np.hypot(xg - (614.0 + tc * vx_c), yg - (536.0 + tc * vy_c))
    rc = 39.5 + 8.5 * tc
    m_cyl = (dc <= rc) | (rot_ell_grid(xg, yg, 733.0, 716.0, 49.0, 47.0, -12.0) <= 1.0)

    mech_fg = m_lwheel | m_lnut | m_lspacer | m_rwheel | m_rspacer | m_axle | m_cyl

    gc = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
    gc[bg_def & (~mech_fg)] = cv2.GC_BGD
    near_skin = ndimage.binary_dilation(skin, iterations=7) & (~bg_def)
    gc[near_skin] = cv2.GC_PR_FGD
    gc[skin & (~old_neck_curls)] = cv2.GC_FGD
    gc[mech_fg] = cv2.GC_FGD

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(rgb, gc, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    mask = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD) | mech_fg) & (~old_neck_curls) & (~top_right_corner) & (~(butt_axle_gap & (~mech_fg)))

    for _ in range(10):
        er = ndimage.binary_erosion(mask)
        rim = mask & (~er) & (~mech_fg)
        bad = rim & ((b - r >= 3.5) | ((r - b < 9.0) & (gray > 66.0) & (gray < 148.0)))
        if not np.any(bad):
            break
        mask[bad] = False

    lbl, num = ndimage.label(mask)
    if num > 1:
        sizes = ndimage.sum(mask, lbl, range(1, num + 1))
        mask = (lbl == (1 + int(np.argmax(sizes))))

    pad_top, pad_side, pad_bot = 420, 260, 60
    Hc, Wc = H + pad_top + pad_bot, W + 2 * pad_side
    stage_rgb = np.zeros((Hc, Wc, 3), dtype=np.float32)
    stage_m = np.zeros((Hc, Wc), dtype=bool)
    stage_rgb[pad_top:pad_top + H, pad_side:pad_side + W] = rf
    stage_m[pad_top:pad_top + H, pad_side:pad_side + W] = mask

    dist_in = ndimage.distance_transform_edt(stage_m)
    dist_out = ndimage.distance_transform_edt(~stage_m)
    alpha = np.clip((dist_in - dist_out + 0.20) / 1.35, 0.0, 1.0)

    sheet_col = np.array([102.0, 122.0, 130.0], dtype=np.float32)
    edge = (alpha > 0.02) & (alpha < 0.98)
    a_s = np.maximum(alpha[..., None], 0.30)
    decontam = np.clip((stage_rgb - (1.0 - alpha[..., None]) * sheet_col) / a_s, 0.0, 255.0)
    was_bluish = (stage_rgb[..., 2] > stage_rgb[..., 0] - 2.0) & edge
    clean_rgb = np.where(was_bluish[..., None], decontam, stage_rgb)
    stage_rgba = np.dstack([np.clip(clean_rgb, 0, 255).astype(np.uint8), np.clip(alpha * 255.0, 0, 255).astype(np.uint8)])

    piv = (640.0 + pad_side, 618.0 + pad_top)
    M = cv2.getRotationMatrix2D(piv, -6.00, 1.0)
    sf = stage_rgba.astype(np.float32)
    sa_f = sf[..., 3:4] / 255.0
    pm = np.concatenate([sf[..., :3] * sa_f, sf[..., 3:4]], axis=-1)
    pm_rot = cv2.warpAffine(pm, M, (Wc, Hc), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    ra = pm_rot[..., 3:4] / 255.0
    rrgb = np.where(ra > 1e-4, pm_rot[..., :3] / np.maximum(ra, 1e-4), 0.0)
    return np.dstack([np.clip(rrgb, 0, 255).astype(np.uint8), np.clip(pm_rot[..., 3], 0, 255).astype(np.uint8)])


def build_front_d0(body_path, ai0_path):
    """Assembles d=0 Front from authentic wheelman_body.jpg + seamless anatomical neck/head + complete knees/calves/feet."""
    base_rgba = extract_clean_body_photo(body_path)
    Hc, Wc = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:Hc, 0:Wc].astype(np.float32)

    ai0 = np.array(key_studio_magenta(Image.open(ai0_path)))
    Ha, Wa = ai0.shape[:2]
    yga, xga = np.mgrid[0:Ha, 0:Wa].astype(np.float32)

    out = base_rgba.astype(np.float32).copy()

    # 1) Seamless Shocked Head + Creased Neck + Collarbone Graft onto Upper Chest
    head_src = ai0.copy()
    bib_r = np.sqrt(((xga - 614.0) / 106.0) ** 2 + ((np.maximum(0.0, yga - 332.0)) / 54.0) ** 2)
    bib_w = np.where(
        yga <= 332.0,
        np.clip((108.0 - np.abs(xga - 614.0)) / 18.0, 0.0, 1.0),
        np.clip((1.0 - bib_r) / 0.38, 0.0, 1.0),
    )
    head_src[..., 3] = np.clip(head_src[..., 3].astype(np.float32) * bib_w, 0, 255).astype(np.uint8)

    chest_tgt_mask = (base_rgba[..., 3] > 220) & (xg >= 735) & (xg <= 940) & (yg >= 495) & (yg <= 542)
    chest_tgt_samples = base_rgba[..., :3][chest_tgt_mask]
    chest_src_mask = (yga >= 305) & (yga <= 380) & (xga >= 535) & (xga <= 695)
    head_matched = match_patch_skin(head_src, chest_src_mask, chest_tgt_samples)

    head_warped = warp_rgba_similarity(head_matched, (614.0, 342.0), (832.0, 502.0), 1.40, +2.5, (Wc, Hc)).astype(np.float32)

    stump_trim = np.where((xg > 720) & (xg < 920), np.clip((yg - 474.0) / 10.0, 0.0, 1.0), 1.0)
    base_a = (out[..., 3] / 255.0) * stump_trim

    hw_a = head_warped[..., 3] / 255.0
    hw_a = np.where(yg > 498.0, np.minimum(hw_a, base_a), hw_a)
    comb_a = hw_a + base_a * (1.0 - hw_a)
    out[..., :3] = np.where(
        comb_a[..., None] > 1e-4,
        (head_warped[..., :3] * hw_a[..., None] + out[..., :3] * base_a[..., None] * (1.0 - hw_a[..., None])) / np.maximum(comb_a[..., None], 1e-4),
        0.0,
    )
    out[..., 3] = np.clip(comb_a * 255.0, 0.0, 255.0)

    # 2) Knee-Level Graft of Bent Knees + Hairy Calves + Rounded Bare Feet
    ai_r, ai_g, ai_b = ai0[..., 0].astype(np.float32), ai0[..., 1].astype(np.float32), ai0[..., 2].astype(np.float32)
    ai_lum = 0.299 * ai_r + 0.587 * ai_g + 0.114 * ai_b
    dark_non_skin = ((ai_r - ai_b) < 16.5) & (ai_lum < 95.0)

    # Left knee+calf+foot (keep 100% of calf, ankle & rounded heel; exclude arm below calf xga > 295 & yga > 382)
    l_keep = (
        (ai0[..., 3] > 45)
        & (xga <= 382)
        & ((xga <= 356) | (yga <= 332))
        & (yga <= 485)
        & (~((xga > 292) & (yga > 382)))
        & (~(dark_non_skin & ((yga > 395) | (xga > 280))))
    )
    lbl_l, nl = ndimage.label(l_keep)
    if nl > 1:
        l_keep = lbl_l == (1 + int(np.argmax(ndimage.sum(l_keep, lbl_l, range(1, nl + 1)))))
    l_keep = ndimage.binary_erosion(l_keep, iterations=1)
    l_splice_fade = np.clip((374.0 - xga) / 40.0, 0.0, 1.0)
    l_alpha = cv2.GaussianBlur(l_keep.astype(np.float32), (3, 3), 0.8) * l_splice_fade
    lleg_src = ai0.copy()
    lleg_src[..., 3] = np.clip(lleg_src[..., 3].astype(np.float32) * l_alpha, 0, 255).astype(np.uint8)

    l_tgt_samples = base_rgba[..., :3][(base_rgba[..., 3] > 220) & (xg >= 425) & (xg <= 545) & (yg >= 485) & (yg <= 610)]
    l_src_m = l_keep & (xga >= 260) & (xga <= 370) & (yga >= 210) & (yga <= 355)
    lleg_matched = match_patch_skin(lleg_src, l_src_m, l_tgt_samples)

    # Right knee+calf+foot (keep 100% of calf, ankle & rounded heel; exclude right arm below calf xga < 908 & yga > 380!)
    r_keep = (
        (ai0[..., 3] > 45)
        & (xga >= 798)
        & ((xga >= 826) | (yga <= 328))
        & (yga <= 489)
        & (~((xga < 912) & (yga > 378)))
        & (~(dark_non_skin & ((yga > 395) | (xga < 890))))
    )
    lbl_r, nr = ndimage.label(r_keep)
    if nr > 1:
        r_keep = lbl_r == (1 + int(np.argmax(ndimage.sum(r_keep, lbl_r, range(1, nr + 1)))))
    r_keep = ndimage.binary_erosion(r_keep, iterations=1)
    r_splice_fade = np.clip((xga - 804.0) / 40.0, 0.0, 1.0)
    r_alpha = cv2.GaussianBlur(r_keep.astype(np.float32), (3, 3), 0.8) * r_splice_fade
    rleg_src = ai0.copy()
    rleg_src[..., 3] = np.clip(rleg_src[..., 3].astype(np.float32) * r_alpha, 0, 255).astype(np.uint8)

    r_tgt_samples = base_rgba[..., :3][(base_rgba[..., 3] > 220) & (xg >= 1230) & (xg <= 1355) & (yg >= 505) & (yg <= 625)]
    r_src_m = r_keep & (xga >= 795) & (xga <= 915) & (yga >= 200) & (yga <= 350)
    rleg_matched = match_patch_skin(rleg_src, r_src_m, r_tgt_samples)

    l_warped = warp_rgba_similarity(lleg_matched, (318.0, 285.0), (454.0, 510.0), 1.18, +8.0, (Wc, Hc)).astype(np.float32)
    r_warped = warp_rgba_similarity(rleg_matched, (852.0, 275.0), (1324.0, 534.0), 1.18, -10.0, (Wc, Hc)).astype(np.float32)

    trim_L = np.where((xg < 472.0) & (yg < 595.0), np.clip((xg - 426.0) / 36.0, 0.0, 1.0), 1.0)
    trim_R = np.where((xg > 1302.0) & (yg < 615.0), np.clip((1350.0 - xg) / 36.0, 0.0, 1.0), 1.0)

    base_a2 = (out[..., 3] / 255.0) * trim_L * trim_R
    for leg_w in (l_warped, r_warped):
        la = leg_w[..., 3] / 255.0
        comb_a = la + base_a2 * (1.0 - la)
        out[..., :3] = np.where(
            comb_a[..., None] > 1e-4,
            (leg_w[..., :3] * la[..., None] + out[..., :3] * base_a2[..., None] * (1.0 - la[..., None])) / np.maximum(comb_a[..., None], 1e-4),
            0.0,
        )
        base_a2 = comb_a
    out[..., 3] = np.clip(base_a2 * 255.0, 0.0, 255.0)

    wheels_d0 = [
        dict(cx=468.0, cy=1040.0, rx=89.0, ry=283.0, ang=1.5, protect_skin=False),
        dict(cx=1369.0, cy=1029.0, rx=139.0, ry=272.0, ang=-0.5, dish_cx=1312.0, dish_cy=1035.0, dish_rx=54.0, dish_ry=162.0, spacer_dir=-1, protect_skin=False),
    ]
    return Image.fromarray(out.astype(np.uint8), "RGBA"), wheels_d0, chest_tgt_samples


def complete_v045_bottom_wheel(v045_im):
    """Completes the cropped bottom cap of the foreground wheel in view_045.jpg seamlessly from its
    clean arm-free lower rows (y=815..892), curving the white dish & ribbed rubber tire smoothly around the bottom."""
    arr = np.array(v045_im)
    H, W = arr.shape[:2]
    pad_b = 88
    ext = np.zeros((H + pad_b, W, 4), dtype=np.uint8)
    ext[:H] = arr

    cy, ry, rx = 742.0, 236.0, 189.0  # bottom at y=978; at y=892, half_w = 189 * sqrt(1 - (150/236)^2) = 146
    yg, xg = np.mgrid[0:H + pad_b, 0:W].astype(np.float32)

    dy = yg - cy
    inside_y = (yg >= H - 10) & (dy < ry)
    # Match exact measured chord at y=892: xL=758, xR=1068 (mid=913.0, half=155.0)
    t_bot = np.clip((yg - 892.0) / (cy + ry - 892.0), 0.0, 1.0)
    half_w = 155.0 * np.sqrt(np.maximum(0.0, 1.0 - t_bot ** 2))
    mid_x = 913.0 - 8.0 * t_bot

    u_norm = (xg - mid_x) / np.maximum(half_w, 1e-3)
    need_fill = inside_y & (np.abs(u_norm) <= 1.01)

    # Sample from clean arm-free rows y_src = 892 -> 816 (mirroring smoothly away from seam y=892!)
    sy_f = np.clip(892.0 - np.abs(yg - 892.0) * 0.85, 816.0, 892.0)
    # At sy_f in [816..892], chord goes linearly from (mid=921, half=170) at 816 to (mid=913, half=155) at 892:
    s_frac = (892.0 - sy_f) / 76.0
    src_mid = 913.0 + 8.0 * s_frac
    src_half = 155.0 + 15.0 * s_frac

    # Taper white dish cleanly inside bottom tire rubber for t_bot > 0.58 so black rubber wraps around bottom!
    # At y=892, white dish sits at u_norm in [+0.12, +0.75]; for t_bot > 0.55, remap dish u into black tread (-0.35)!
    dish_bot_curve = 0.62 * np.sqrt(np.maximum(0.0, 1.0 - ((u_norm - 0.43) / 0.36) ** 2))
    past_dish = (u_norm > 0.08) & (u_norm < 0.80) & (t_bot > dish_bot_curve)
    u_lookup = np.where(past_dish, -0.35 - 0.25 * (u_norm - 0.43), u_norm)
    sx_f = np.clip(src_mid + u_lookup * src_half, 752.0, 1088.0)

    ref_px = cv2.remap(ext[:H].astype(np.float32), sx_f.astype(np.float32), sy_f.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    shade = 1.0 - 0.24 * t_bot
    ref_px[..., :3] *= shade[..., None]
    rim_a = np.clip((1.005 - np.abs(u_norm)) / 0.035, 0.0, 1.0) * np.clip((1.0 - t_bot) / 0.04, 0.0, 1.0)
    ref_px[..., 3] = rim_a * 255.0

    w_seam = np.clip((yg - (H - 10.0)) / 8.0, 0.0, 1.0)[..., None]
    cur = ext.astype(np.float32)
    blended = np.where(yg[..., None] < H, cur * (1.0 - w_seam) + ref_px * w_seam, ref_px)
    ext = np.where(need_fill[..., None], np.clip(blended, 0, 255), cur).astype(np.uint8)
    return Image.fromarray(ext, "RGBA")


def mirror_wheel_specs(specs, width):
    out = []
    for ws in specs:
        m = dict(ws)
        m["cx"] = width - ws["cx"]
        m["ang"] = -ws["ang"]
        if "dish_cx" in ws:
            m["dish_cx"] = width - ws["dish_cx"]
        if "spacer_dir" in ws:
            m["spacer_dir"] = -ws["spacer_dir"]
        out.append(m)
    return out


def build_master_8_views():
    """Returns list of 8 (clean_rgba_pil, wheel_specs_in_src) for d = 0..7."""
    d0_im, w_d0, ref_skin = build_front_d0(
        os.path.join(REF_DIR, "wheelman_body.jpg"),
        os.path.join(VIEWS_DIR, "view_000_ai.jpg"),
    )

    # --- d=1 (45° Front-Left) ---
    v045 = key_studio_magenta(Image.open(os.path.join(VIEWS_DIR, "view_045.jpg")))
    a45 = np.array(v045).astype(np.float32)
    H, W = a45.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    lum45 = 0.299 * a45[..., 0] + 0.587 * a45[..., 1] + 0.114 * a45[..., 2]
    m_sh45 = (xg >= 564) & (xg <= 606) & (yg >= 598) & (yg <= 674) & (lum45 < 62.0) & ((a45[..., 0] - a45[..., 2]) < 14.0)
    v045 = inpaint_region_with_surrounding_skin(v045, m_sh45, grain_src_box=(610, 460, 710, 560))
    v045 = calibrate_skin_to_ref(v045, ref_skin, strength=0.60)
    v045 = complete_v045_bottom_wheel(v045)
    w_d1 = [
        dict(cx=168.0, cy=588.0, rx=138.0, ry=170.0, ang=-8.0, dish_cx=190.0, dish_cy=592.0, dish_rx=84.0, dish_ry=104.0, protect_skin=True),
        dict(cx=925.0, cy=742.0, rx=185.0, ry=250.0, ang=6.5, dish_cx=985.0, dish_cy=760.0, dish_rx=72.0, dish_ry=152.0, protect_skin=True),
    ]

    # --- d=2 (90° Screen-Left Profile) ---
    orig90_im = key_studio_magenta(Image.open(os.path.join(VIEWS_DIR, "view_090.jpg")))
    a90 = np.array(orig90_im).astype(np.float32)
    r_tire90 = rot_ell_grid(xg, yg, 602.0, 622.0, 232.0, 234.0, 0.0)
    m_sh90 = (
        (r_tire90 > 1.01)
        & (xg >= 490) & (xg <= 830)
        & (yg >= 335) & (yg <= 595)
        & (((a90[..., 0] - a90[..., 2]) < 18.0) | ((xg >= 650) & (xg <= 686) & (yg >= 420) & (yg <= 456)))
    )
    m_sh90 = ndimage.binary_closing(m_sh90, iterations=3) & (r_tire90 > 1.01)
    v090 = inpaint_region_with_surrounding_skin(orig90_im, m_sh90, grain_src_box=(760, 415, 860, 505))
    orig90_arr = np.array(orig90_im)
    cur90 = np.array(v090)
    cur90[r_tire90 <= 1.015] = orig90_arr[r_tire90 <= 1.015]
    v090 = calibrate_skin_to_ref(Image.fromarray(cur90, "RGBA"), ref_skin, strength=0.60)
    w_d2 = [
        dict(cx=602.0, cy=622.0, rx=230.0, ry=232.0, ang=0.0, dish_cx=602.0, dish_cy=622.0, dish_rx=145.0, dish_ry=144.0, protect_skin=True),
    ]

    # --- d=5 (225° Back-Right) & d=3 (135° Back-Left) ---
    orig225_im = key_studio_magenta(Image.open(os.path.join(VIEWS_DIR, "view_225_raw.jpg")))
    a225 = np.array(orig225_im).astype(np.float32)
    lum225 = 0.299 * a225[..., 0] + 0.587 * a225[..., 1] + 0.114 * a225[..., 2]
    is_dark_cloth225 = ((a225[..., 0] - a225[..., 2]) < 18.0) & (lum225 < 112.0)

    r_rw225 = rot_ell_grid(xg, yg, 840.0, 736.0, 82.0, 156.0, 3.0)
    r_lw225 = rot_ell_grid(xg, yg, 224.0, 682.0, 102.0, 148.0, -8.0)
    d_ax225 = seg_dist_grid(xg, yg, 240.0, 668.0, 768.0, 706.0)
    mech225 = (r_rw225 <= 1.05) | (r_lw225 <= 1.05) | ((d_ax225 <= 13.0) & ((xg < 405) | (xg > 635) | (lum225 > 74.0)))

    y_under_thigh = 528.0 + (755.0 - xg) * (160.0 / 150.0) + 18.0 * np.sin(np.clip((755.0 - xg) / 150.0, 0.0, 1.0) * math.pi)
    boxy_overhang_r = is_dark_cloth225 & (~mech225) & (xg > 605) & (xg < 795) & (yg > y_under_thigh) & (yg < 690)
    # Smooth rounded parabolic groin saddle (zero sharp corner!)
    crotch_saddle = is_dark_cloth225 & (~mech225) & (np.abs(xg - 595.0) < 42.0) & (yg < 488.0 - 0.032 * (xg - 595.0) ** 2)
    trim225 = boxy_overhang_r | crotch_saddle
    keep225 = (a225[..., 3] > 20) & (~trim225)
    dist_in225 = ndimage.distance_transform_edt(keep225)
    a225[..., 3] = np.where(trim225, 0.0, np.minimum(a225[..., 3], np.clip(dist_in225 / 2.0, 0.0, 1.0) * 255.0))
    v225 = Image.fromarray(a225.astype(np.uint8), "RGBA")

    m_sh225 = (xg >= 375) & (xg <= 785) & (yg >= 420) & (yg <= 732) & is_dark_cloth225 & (~mech225) & (~trim225)
    v225 = inpaint_region_with_surrounding_skin(v225, m_sh225, grain_src_box=(260, 410, 380, 530))
    orig225_arr = np.array(orig225_im)
    cur225 = np.array(v225)
    cur225[mech225] = orig225_arr[mech225]
    v225 = calibrate_skin_to_ref(Image.fromarray(cur225, "RGBA"), ref_skin, strength=0.60)
    w_d5 = [
        dict(cx=224.0, cy=682.0, rx=100.0, ry=146.0, ang=-8.0, dish_cx=240.0, dish_cy=682.0, dish_rx=50.0, dish_ry=84.0, protect_skin=True),
        dict(cx=840.0, cy=736.0, rx=80.0, ry=154.0, ang=3.0, dish_cx=868.0, dish_cy=738.0, dish_rx=38.0, dish_ry=96.0, protect_skin=True),
    ]
    v135 = ImageOps.mirror(v225)
    w_d3 = mirror_wheel_specs(w_d5, v225.width)

    # --- d=4 (180° Direct Back) ---
    orig180_im = key_studio_magenta(Image.open(os.path.join(VIEWS_DIR, "view_180.jpg")))
    a180 = np.array(orig180_im).astype(np.float32)
    lum180 = 0.299 * a180[..., 0] + 0.587 * a180[..., 1] + 0.114 * a180[..., 2]
    is_sh180 = (xg >= 415) & (xg <= 788) & (yg >= 628) & (yg <= 804) & ((a180[..., 0] - a180[..., 2]) < 18.0) & (lum180 < 108.0)
    hip_curve_w = 152.0 - 38.0 * np.clip((yg - 680.0) / 110.0, 0.0, 1.0) ** 1.6
    puff180 = is_sh180 & (np.abs(xg - 600.0) > hip_curve_w) & (yg > 685.0)
    keep180 = (a180[..., 3] > 20) & (~puff180)
    dist_in180 = ndimage.distance_transform_edt(keep180)
    a180[..., 3] = np.where(puff180, 0.0, np.minimum(a180[..., 3], np.clip(dist_in180 / 1.8, 0.0, 1.0) * 255.0))
    v180 = Image.fromarray(np.clip(a180, 0, 255).astype(np.uint8), "RGBA")

    # Unified single-pass skin diffusion across mid-back steel bar + lower-back shorts (zero horizontal seam!)
    mid_bar180 = (xg >= 445) & (xg <= 757) & (yg >= 588) & (yg <= 646) & (~(((xg < 450) | (xg > 752)) & ((a180[..., 0] - a180[..., 2]) > 22.0) & (a180[..., 0] > 160.0)))
    hole180 = mid_bar180 | (is_sh180 & (~puff180))
    v180 = inpaint_region_with_surrounding_skin(v180, hole180, cleft_x=600.0, grain_src_box=(490, 485, 710, 575))
    v180 = calibrate_skin_to_ref(v180, ref_skin, strength=0.60)
    w_d4 = [
        dict(cx=176.0, cy=612.0, rx=102.0, ry=224.0, ang=2.0, dish_cx=232.0, dish_cy=616.0, dish_rx=26.0, dish_ry=126.0, protect_skin=False),
        dict(cx=1026.0, cy=614.0, rx=102.0, ry=224.0, ang=-2.0, dish_cx=970.0, dish_cy=618.0, dish_rx=26.0, dish_ry=126.0, protect_skin=False),
    ]

    v270 = ImageOps.mirror(v090)
    w_d6 = mirror_wheel_specs(w_d2, v090.width)

    v315 = ImageOps.mirror(v045)
    w_d7 = mirror_wheel_specs(w_d1, v045.width)

    return [
        (d0_im, w_d0),
        (v045, w_d1),
        (v090, w_d2),
        (v135, w_d3),
        (v180, w_d4),
        (v225, w_d5),
        (v270, w_d6),
        (v315, w_d7),
    ], ref_skin


# ---------------------------------------------------------------------------
# 3. Normalization onto 320x304 Canvas + Articulated Rolling & Wheel Spin
# ---------------------------------------------------------------------------

def place_view_on_canvas(im_rgba, wheel_specs, d_idx):
    """Places cleaned master view onto CANVAS=(320,304) with lowest wheel tire planted at GROUND=288
    and transforms wheel_specs into canvas coordinates."""
    W_c, H_c = CANVAS
    arr = np.array(im_rgba)
    ys, xs = np.nonzero(arr[..., 3] > 24)
    x0, x1 = float(xs.min()), float(xs.max())
    y0 = float(ys.min())
    # Exact lowest tire contact point from wheel_specs (or alpha bottom)
    y_tire_bot = max(ws["cy"] + ws["ry"] for ws in wheel_specs)
    y_bot = min(float(ys.max()) + 2.0, max(float(ys.max()), y_tire_bot * 0.5 + float(ys.max()) * 0.5))

    span_w = x1 - x0
    span_h = y_bot - y0

    # Harmonized target height per view so head/torso/wheel sizes feel physically consistent around 360°
    target_h_map = {0: 236.0, 1: 242.0, 2: 224.0, 3: 244.0, 4: 244.0, 5: 244.0, 6: 224.0, 7: 242.0}
    want_h = target_h_map[d_idx]
    scale = min((W_c - 16.0) / span_w, want_h / span_h, (GROUND - 14.0) / span_h)

    rw = max(2, int(round(im_rgba.width * scale)))
    rh = max(2, int(round(im_rgba.height * scale)))
    rsz = im_rgba.resize((rw, rh), Image.LANCZOS)

    # Center horizontally on monster midpoint (for profile d=2,6, wheel hub sits naturally near 160!)
    src_cx = 0.5 * (x0 + x1)
    ox = int(round(W_c * 0.5 - src_cx * scale))
    oy = int(round(GROUND - y_bot * scale))

    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(rsz, (ox, oy), rsz)

    c_specs = []
    for ws in wheel_specs:
        cs = dict(ws)
        cs["cx"] = ws["cx"] * scale + ox
        cs["cy"] = ws["cy"] * scale + oy
        cs["rx"] = ws["rx"] * scale
        cs["ry"] = ws["ry"] * scale
        if "dish_cx" in ws:
            cs["dish_cx"] = ws["dish_cx"] * scale + ox
            cs["dish_cy"] = ws["dish_cy"] * scale + oy
            cs["dish_rx"] = ws["dish_rx"] * scale
            cs["dish_ry"] = ws["dish_ry"] * scale
        c_specs.append(cs)

    return canvas, c_specs


def premul_remap(rgba, map_x, map_y):
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, a * 255.0], axis=-1)
    warped = cv2.remap(pm, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    wa = warped[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, warped[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), np.clip(warped[..., 3], 0, 255).astype(np.uint8)])


def animate_wheelman_frame(base_rgba, d_idx, phase_01, wheel_specs, mode="roll"):
    """Generates one animated frame with:
      - Articulated counter-pumping bare V-legs & feet
      - Reactive head/neck wobble
      - Snappy axle suspension bounce (while tires stay 100% locked on axle & GROUND=288!)
      - Foreshortened 3D wheel rim rotation (spinning cleanly BEHIND any overlapping arm/foot!)
        + traveling 3D rubber tire tread lugs.
    """
    rgba = np.array(base_rgba).copy()
    H, W = rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    t = 2.0 * math.pi * phase_01
    cx = W * 0.5
    y_axle = sum(ws["cy"] for ws in wheel_specs) / len(wheel_specs)

    if mode == "idle":
        return Image.fromarray(rgba, "RGBA")

    amp_leg = 4.8
    amp_bob = 2.2
    amp_head = 2.3

    # 1) Protect wheels & steel axle so wheels stay 100% round and planted on GROUND!
    wheel_lock = np.zeros((H, W), dtype=np.float32)
    for ws in wheel_specs:
        wcx, wcy = ws["cx"], ws["cy"]
        wrx, wry = ws["rx"] + 5.0, ws["ry"] + 5.0
        wang = math.radians(ws["ang"])
        ca, sa = math.cos(wang), math.sin(wang)
        du = ((xg - wcx) * ca + (yg - wcy) * sa) / max(wrx, 1.0)
        dv = (-(xg - wcx) * sa + (yg - wcy) * ca) / max(wry, 1.0)
        w_m = np.clip((1.18 - np.sqrt(du * du + dv * dv)) / 0.22, 0.0, 1.0)
        wheel_lock = np.maximum(wheel_lock, w_m)

    axle_lock = np.exp(-((yg - y_axle) / 8.5) ** 2) * (yg > y_axle - 9.0)
    mech_lock = np.clip(np.maximum(wheel_lock, axle_lock * 0.88), 0.0, 1.0)
    free_w = 1.0 - mech_lock

    bob_dy = amp_bob * math.sin(t) * free_w * np.clip((GROUND - 20.0 - yg) / 42.0, 0.0, 1.0)

    if d_idx in (2, 6):
        fwd_s = -1.0 if d_idx == 2 else 1.0
        side_leg_w = np.clip((fwd_s * (xg - cx) + 10.0) / 30.0, 0.0, 1.0) * np.clip(((y_axle - 16.0) - yg) / 26.0, 0.0, 1.0) * free_w
        ang_s = math.radians(amp_leg * 1.15 * math.sin(t) * fwd_s)
        px_s, py_s = cx + fwd_s * 6.0, y_axle - 22.0
        ca_s, sa_s = math.cos(-ang_s), math.sin(-ang_s)
        dx_l = (px_s + (xg - px_s) * ca_s - (yg - py_s) * sa_s - xg) * side_leg_w
        dy_l = (py_s + (xg - px_s) * sa_s + (yg - py_s) * ca_s - yg) * side_leg_w
    else:
        hnx_map = {0: 150.0, 1: 232.0, 2: 272.0, 3: 244.0, 4: 160.0, 5: 76.0, 6: 48.0, 7: 88.0}
        hnx = hnx_map[d_idx]
        head_guard = 1.0 - np.clip((76.0 - np.abs(xg - hnx)) / 14.0, 0.0, 1.0) * np.clip((132.0 - yg) / 16.0, 0.0, 1.0)
        l_leg_w = np.clip(((cx - 22.0) - xg) / 28.0, 0.0, 1.0) * np.clip(((y_axle - 8.0) - yg) / 26.0, 0.0, 1.0) * head_guard * free_w
        r_leg_w = np.clip((xg - (cx + 22.0)) / 28.0, 0.0, 1.0) * np.clip(((y_axle - 8.0) - yg) / 26.0, 0.0, 1.0) * head_guard * free_w
        ang_L = math.radians(+amp_leg * math.sin(t))
        ang_R = math.radians(-amp_leg * math.sin(t))
        pxL, pyL = cx - 24.0, y_axle - 18.0
        pxR, pyR = cx + 24.0, y_axle - 18.0
        cL, sL = math.cos(-ang_L), math.sin(-ang_L)
        cR, sR = math.cos(-ang_R), math.sin(-ang_R)
        dx_l = (pxL + (xg - pxL) * cL - (yg - pyL) * sL - xg) * l_leg_w + (pxR + (xg - pxR) * cR - (yg - pyR) * sR - xg) * r_leg_w
        dy_l = (pyL + (xg - pxL) * sL + (yg - pyL) * cL - yg) * l_leg_w + (pyR + (xg - pxR) * sR + (yg - pyR) * cR - yg) * r_leg_w

    # Head/neck wobble (estimated head x-center per direction)
    head_cx_map = {0: cx, 1: cx + 44.0, 2: cx + 82.0, 3: cx + 52.0, 4: cx, 5: cx - 52.0, 6: cx - 82.0, 7: cx - 44.0}
    hcx = head_cx_map[d_idx]
    y_neck_est = 108.0
    head_w = np.clip((y_neck_est + 6.0 - yg) / 22.0, 0.0, 1.0) * np.exp(-((xg - hcx) / 38.0) ** 2) * free_w
    ang_h = math.radians(amp_head * math.sin(t - 0.9))
    ch, sh = math.cos(-ang_h), math.sin(-ang_h)
    dx_h = (hcx + (xg - hcx) * ch - (yg - y_neck_est) * sh - xg) * head_w
    dy_h = (y_neck_est + (xg - hcx) * sh + (yg - y_neck_est) * ch - yg - 1.2 * math.cos(t)) * head_w

    rgba = premul_remap(rgba, (xg + dx_l + dx_h).astype(np.float32), (yg + bob_dy + dy_l + dy_h).astype(np.float32))

    # 2) Foreshortened 3D Wheel Dish Rotation + Traveling Rubber Tire Treads!
    for ws in wheel_specs:
        wcx, wcy, wrx, wry, wang_deg = ws["cx"], ws["cy"], ws["rx"], ws["ry"], ws["ang"]
        ang = math.radians(wang_deg)
        ca, sa = math.cos(ang), math.sin(ang)

        pad = max(wrx, wry) + 5
        x0, x1 = max(0, int(wcx - pad)), min(W, int(wcx + pad + 1))
        y0, y1 = max(0, int(wcy - pad)), min(H, int(wcy + pad + 1))
        if x1 <= x0 or y1 <= y0:
            continue

        lxg, lyg = xg[y0:y1, x0:x1], yg[y0:y1, x0:x1]
        du = ((lxg - wcx) * ca + (lyg - wcy) * sa) / max(wrx, 1.0)
        dv = (-(lxg - wcx) * sa + (lyg - wcy) * ca) / max(wry, 1.0)
        r_ell = np.sqrt(du * du + dv * dv)
        patch = rgba[y0:y1, x0:x1].copy()
        pa = patch[..., 3] > 80

        # Protect overlapping bare skin (arm/hand gripping axle in d=2,6 or heel/forearm in d=1,3,5,7)!
        skin_occl = np.zeros_like(pa)
        plate_occl = np.zeros_like(pa)
        if ws.get("protect_skin", False):
            pr, pg, pb = patch[..., 0].astype(np.float32), patch[..., 1].astype(np.float32), patch[..., 2].astype(np.float32)
            raw_sk = pa & ((pr - pb) > 15.0) & ((pr - pg) > 8.0) & (pr > 82.0)
            skin_occl = ndimage.binary_dilation(raw_sk, iterations=1)
            plate_occl = ndimage.binary_dilation(raw_sk, iterations=6)

        # Spin direction: CCW (-1) when rolling left (d=1,2,3), CW (+1) when rolling right (d=5,6,7) or front/back
        spin_dir = -1.0 if d_idx in (1, 2, 3) else +1.0
        th_spin = spin_dir * phase_01 * 2.0 * math.pi

        # A) Rotate inner white steel dish via 2D remap when full circular rim is unoccluded (wrx/wry > 0.85, i.e. d=2,6),
        #    and use clean 3D elliptical lug/valve-stem travel on foreshortened deep-dish crescents (d=0,1,3,4,5,7)!
        if "dish_rx" in ws and (ws["dish_rx"] / max(ws["dish_ry"], 1.0) > 0.85):
            dcx, dcy = ws["dish_cx"], ws["dish_cy"]
            drx, dry = ws["dish_rx"], ws["dish_ry"]
            ddu = ((lxg - dcx) * ca + (lyg - dcy) * sa) / max(drx, 1.0)
            ddv = (-(lxg - dcx) * sa + (lyg - dcy) * ca) / max(dry, 1.0)
            rr_d = np.sqrt(ddu * ddu + ddv * ddv)

            sp_side = ws.get("spacer_dir", 0)
            on_spacer = np.zeros_like(pa)
            if sp_side != 0:
                on_spacer = (np.abs(lyg - dcy) < dry * 0.22) & ((lxg - dcx) * sp_side > -drx * 0.15)

            # Build clean arm-free wheel plate by filling plate_occl from diametrically opposite wheel sector!
            plate_rgb = patch[..., :3].astype(np.float32).copy()
            if np.any(plate_occl):
                opp_x = np.clip(np.round(2.0 * (dcx - x0) - (lxg - x0)), 0, patch.shape[1] - 1).astype(np.int32)
                opp_y = np.clip(np.round(2.0 * (dcy - y0) - (lyg - y0)), 0, patch.shape[0] - 1).astype(np.int32)
                plate_rgb[plate_occl] = plate_rgb[opp_y, opp_x][plate_occl]

            w_dish = (
                np.clip((1.0 - rr_d) / 0.14, 0.0, 1.0)
                * np.clip((rr_d - 0.24) / 0.10, 0.0, 1.0)
                * (~on_spacer)
                * (~skin_occl)
                * pa
            )
            if np.any(w_dish > 0.02):
                ct, st = math.cos(th_spin), math.sin(th_spin)
                ur = ddu * ct - ddv * st
                vr = ddu * st + ddv * ct
                mx_d = ((dcx - x0) + (ur * drx) * ca - (vr * dry) * sa).astype(np.float32)
                my_d = ((dcy - y0) + (ur * drx) * sa + (vr * dry) * ca).astype(np.float32)
                rot_rgb = cv2.remap(plate_rgb, mx_d, my_d, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                patch[..., :3] = np.clip(patch[..., :3] * (1.0 - w_dish[..., None]) + rot_rgb * w_dish[..., None], 0, 255).astype(np.uint8)
        elif "dish_rx" in ws:
            # Narrow foreshortened dish sliver (d=0 right wheel, d=4 inner slivers): subtle traveling valve-stem & lug glint!
            dcx, dcy, drx, dry = ws["dish_cx"], ws["dish_cy"], ws["dish_rx"], ws["dish_ry"]
            ddu = ((lxg - dcx) * ca + (lyg - dcy) * sa) / max(drx, 1.0)
            ddv = (-(lxg - dcx) * sa + (lyg - dcy) * ca) / max(dry, 1.0)
            rr_d = np.sqrt(ddu * ddu + ddv * ddv)
            sp_side = ws.get("spacer_dir", 0)
            on_spacer = (np.abs(lyg - dcy) < dry * 0.20) & ((lxg - dcx) * sp_side > -drx * 0.20) if sp_side != 0 else np.zeros_like(pa)
            roll_s = +1.0 if d_idx in (0, 1, 7) else -1.0
            th_v = np.arcsin(np.clip(ddv, -0.98, 0.98))
            valve_dot = np.exp(-((rr_d - 0.72) / 0.18) ** 2) * np.exp(-(((th_v - roll_s * phase_01 * 2.0 * math.pi + math.pi) % (2.0 * math.pi) - math.pi) / 0.32) ** 2)
            mask_sliver = (rr_d < 0.96) & (rr_d > 0.25) & (~on_spacer) & (~skin_occl) & pa
            patch[..., :3] = np.clip(patch[..., :3].astype(np.float32) - (valve_dot * mask_sliver)[..., None] * 65.0, 0, 255).astype(np.uint8)

        # B) Traveling 3D rubber tire tread lugs along the black rubber tire!
        p_lum = patch[..., :3].mean(axis=2)
        is_black_tire = pa & (~skin_occl) & (p_lum < 78.0) & (r_ell <= 1.03)
        if wrx / max(wry, 1.0) > 0.72:
            ang_t = np.arctan2(dv, du) - th_spin
            tread_wave = np.sin(10.0 * ang_t)
            scuff_wave = np.cos(3.0 * ang_t + 0.7)
            ring_t = np.clip((r_ell - 0.58) / 0.10, 0.0, 1.0) * is_black_tire
            delta = (tread_wave * 13.5 + np.maximum(0.0, scuff_wave) * 14.0) * ring_t
        else:
            roll_sign = +1.0 if d_idx in (0, 1, 7) else -1.0
            theta_v = np.arcsin(np.clip(dv, -0.98, 0.98))
            tread_wave = np.sin(9.0 * theta_v - roll_sign * phase_01 * 2.0 * math.pi * 2.0)
            scuff_wave = np.cos(3.0 * theta_v - roll_sign * phase_01 * 2.0 * math.pi)
            vis_cyl = np.cos(theta_v)
            delta = (tread_wave * 14.0 + np.maximum(0.0, scuff_wave) * 14.0) * vis_cyl * is_black_tire

        patch[..., :3] = np.clip(patch[..., :3].astype(np.float32) + delta[..., None], 0, 255).astype(np.uint8)
        rgba[y0:y1, x0:x1] = patch

    return Image.fromarray(rgba, "RGBA")


# ---------------------------------------------------------------------------
# 4. DarkPlaces SPR32 Writer, Sheets, GIFs & Interactive 360° HTML Viewer
# ---------------------------------------------------------------------------

def tone_for_darkplaces(im_rgba):
    """Tones full-bright sprite RGBA for DarkPlaces r_hdr_scenebrightness 2.5 (matches jesskart)."""
    rgb = ImageEnhance.Contrast(im_rgba.convert("RGB")).enhance(1.20)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.50)
    rgb.putalpha(im_rgba.getchannel("A"))
    return rgb


def to_spr32_toned(im_rgba):
    """Places 320x304 or 480x340 frame onto unified 360x255 SPR32 canvas (ox=-180, oy=231) and tones for DarkPlaces."""
    if im_rgba.size == WIDE_CANVAS:
        wide = im_rgba
    else:
        wide = Image.new("RGBA", WIDE_CANVAS, (0, 0, 0, 0))
        ox_w = (WIDE_CANVAS[0] - im_rgba.width) // 2
        oy_w = WIDE_GROUND - GROUND
        wide.alpha_composite(im_rgba, (ox_w, oy_w))
    scaled = wide.resize(SPR_CANVAS, Image.LANCZOS)
    return tone_for_darkplaces(scaled)


def _tight_crop_and_bleed_rgba(rgba: np.ndarray, base_ox: int, base_oy: int):
    h, w, _ = rgba.shape
    ys, xs = np.nonzero(rgba[:, :, 3] > 2)
    if len(xs) == 0:
        empty = np.zeros((2, 2, 4), dtype=np.uint8)
        return -1, 1, 2, 2, empty.tobytes()
    x0 = max(0, int(xs.min()) - 1)
    y0 = max(0, int(ys.min()) - 1)
    x1 = min(w, int(xs.max()) + 2)
    y1 = min(h, int(ys.max()) + 2)
    cropped = rgba[y0:y1, x0:x1].copy()
    pad_l = 1 if x0 == int(xs.min()) else 0
    pad_t = 1 if y0 == int(ys.min()) else 0
    pad_r = 1 if x1 == int(xs.max()) + 1 else 0
    pad_b = 1 if y1 == int(ys.max()) + 1 else 0
    if pad_l or pad_t or pad_r or pad_b:
        cropped = np.pad(cropped, ((pad_t, pad_b), (pad_l, pad_r), (0, 0)), mode="constant", constant_values=0)
        x0 -= pad_l
        y0 -= pad_t
    fg = cropped[:, :, 3] >= 32
    if not np.any(fg):
        fg = cropped[:, :, 3] > 0
    if np.any(fg):
        tr = cropped[:, :, 3] == 0
        if np.any(tr):
            _, (iy, ix) = ndimage.distance_transform_edt(~fg, return_indices=True)
            cropped[tr, :3] = cropped[iy[tr], ix[tr], :3]
    cw, ch = cropped.shape[1], cropped.shape[0]
    return int(base_ox + x0), int(base_oy - y0), cw, ch, cropped.tobytes()


def write_spr32(path, frames, ground_y=SPR_GROUND, sprite_type=2, center_indices=None):
    """Writes tight-cropped DarkPlaces IDSP v32 sprite, type 2 (SPR_VP_PARALLEL) by default,
    with centered origins (ox=-w//2, oy=h//2) on overhead frame indices and ground_y elsewhere."""
    w, h = frames[0].size
    base_ox = -(w // 2)
    base_oy = ground_y
    center_set = set(center_indices) if center_indices is not None else set()
    packed = []
    for idx, im in enumerate(frames):
        fox, foy, cw, ch, raw = _tight_crop_and_bleed_rgba(np.asarray(im.convert("RGBA"), dtype=np.uint8), base_ox, base_oy)
        if idx in center_set:
            fox = -(cw // 2)
            foy = ch // 2
        packed.append((fox, foy, cw, ch, raw))
    max_cw = max(f[2] for f in packed)
    max_ch = max(f[3] for f in packed)
    rad = 0.5 * math.hypot(max_cw, max_ch)
    buf = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, sprite_type, rad, max_cw, max_ch, len(packed), 0.0, 0))
    for fox, foy, cw, ch, raw in packed:
        buf += struct.pack("<iiiii", 0, fox, foy, cw, ch) + raw
    targets = [path]
    if os.path.isdir(os.path.dirname(STAGED_PROGS_DIR)):
        stg_p = os.path.join(STAGED_PROGS_DIR, os.path.basename(path))
        if os.path.normcase(stg_p) != os.path.normcase(path):
            targets.append(stg_p)
    for dst in targets:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            f.write(buf)
        os.replace(tmp, dst)
    print(f"wrote {path} ({len(packed)} frames, type={sprite_type}, tight max={max_cw}x{max_ch} from {w}x{h}, base_ox={base_ox}, base_oy={base_oy}, centered={len(center_set)}, {len(buf)/1048576:.2f} MiB)")


def save_gif_helper(frames_list, out_path, bg_rgb=(28, 30, 36), duration_ms=42):
    gif_frames = []
    for fr in frames_list:
        bg = Image.new("RGBA", fr.size, (*bg_rgb, 255))
        bg.alpha_composite(fr)
        gif_frames.append(bg.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    gif_frames[0].save(out_path, save_all=True, append_images=gif_frames[1:], duration=duration_ms, loop=0)


def write_sheets_and_gifs(idle_frames, roll_grid, scream_grid, vert_dict, sim_hists, parts_360, stunt_kit, norm_views, vfx_plates, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cell_w, cell_h = 160, 152
    sheet = Image.new("RGBA", (cell_w * N_DIR, cell_h * N_ANIM), (28, 30, 36, 255))
    draw = ImageDraw.Draw(sheet)
    for d in range(N_DIR):
        for k in range(N_ANIM):
            fr = roll_grid[d][k].resize((cell_w, cell_h), Image.LANCZOS)
            cell = Image.new("RGBA", (cell_w, cell_h), (28 + 4 * ((d + k) % 2), 30, 36, 255))
            cell.alpha_composite(fr)
            sheet.alpha_composite(cell, (d * cell_w, k * cell_h))
            draw.text((d * cell_w + 5, k * cell_h + 3), f"d{d}:f{k}", fill=(255, 224, 64, 255))
    sheet_path = os.path.join(out_dir, "sheet.jpg")
    sheet.convert("RGB").save(sheet_path, quality=90)

    tw, th = CANVAS
    turn_card = Image.new("RGB", (tw * 4, th * 2), (26, 29, 36))
    tdr = ImageDraw.Draw(turn_card)
    dir_names = ["0° Front", "45° Front-Left", "90° Left Profile", "135° Back-Left",
                 "180° Back", "225° Back-Right", "270° Right Profile", "315° Front-Right"]
    for d in range(N_DIR):
        col, row = d % 4, d // 4
        tile = Image.new("RGBA", (tw, th), (26, 29, 36, 255))
        tile.alpha_composite(idle_frames[d])
        turn_card.paste(tile.convert("RGB"), (col * tw, row * th))
        tdr.text((col * tw + 8, row * th + 6), dir_names[d], fill=(120, 240, 160))
    turn_card.save(os.path.join(out_dir, "turnaround_8dir.jpg"), quality=92)

    # Vertical Above & Below 2x2 showcase card
    ab_card = Image.new("RGB", (tw * 2, th * 2), (24, 27, 34))
    adr = ImageDraw.Draw(ab_card)
    for idx, (pk, lbl) in enumerate([
        ("above90", "+90° Directly Above Him"),
        ("above45", "+45° High-Angle Above"),
        ("below45", "-45° Worm's-Eye Below"),
        ("below90", "-90° Directly Below Him"),
    ]):
        c, r = idx % 2, idx // 2
        tile = Image.new("RGBA", (tw, th), (24, 27, 34, 255))
        tile.alpha_composite(vert_dict[pk]["roll"][0])
        ab_card.paste(tile.convert("RGB"), (c * tw, r * th))
        adr.text((c * tw + 8, r * th + 6), lbl, fill=(90, 220, 255))
    ab_card.save(os.path.join(out_dir, "above_below_card.jpg"), quality=92)

    # 4-Row x 5-Angle Escalating 360° Explosions Showcase Card!
    cw, ch = 320, 226
    bcard = Image.new("RGB", (cw * 5, ch * 4), (18, 20, 26))
    bdr = ImageDraw.Draw(bcard)
    card_specs = {
        1: [(24, 1), (31, 0), (44, 2), (54, 4), (72, 6)],
        2: [(22, 2), (34, 0), (50, 2), (62, 4), (86, 6)],
        3: [(20, 0), (35, 1), (58, 2), (76, 4), (97, 6)],
        4: [(32, 7), (41, 0), (68, 2), (92, 4), (153, 6)],
    }
    for tier in (1, 2, 3, 4):
        for col, (fi, cd) in enumerate(card_specs[tier]):
            im = b360.render_3d_explosion_frame(tier, sim_hists[tier][fi], cd, parts_360, scream_grid, norm_views, vfx_plates)
            tile = Image.new("RGBA", (cw, ch), (20, 18, 22, 255))
            tile.alpha_composite(im.resize((cw, ch), Image.LANCZOS))
            bcard.paste(tile.convert("RGB"), (col * cw, (tier - 1) * ch))
            bdr.text((col * cw + 6, (tier - 1) * ch + 5), f"Boom {tier} | f={fi} | {cd*45}°", fill=(255, 228, 88))
    bcard.save(os.path.join(out_dir, "four_booms_360_card.jpg"), quality=92)

    # High-FPS GIFs (including all 4 Escalating Explosions + 360° Live Orbit Explosion GIF!)
    save_gif_helper(roll_grid[0], os.path.join(out_dir, "roll.gif"), duration_ms=42)
    save_gif_helper(scream_grid[0], os.path.join(out_dir, "scream.gif"), duration_ms=42)

    gif_names = {
        1: "explode_1_classic.gif",
        2: "explode_2_napalm.gif",
        3: "explode_3_plasma_tornado.gif",
        4: "explode_4_thermonuclear.gif",
    }
    for tier, gname in gif_names.items():
        # Sample every 2nd frame for snappy compact showcase GIFs while orbiting 360° onexplode_360_orbit!
        seq = [
            b360.render_3d_explosion_frame(tier, sim_hists[tier][f], 0, parts_360, scream_grid, norm_views, vfx_plates).resize((360, 255), Image.BICUBIC)
            for f in range(0, len(sim_hists[tier]), 2)
        ]
        save_gif_helper(seq, os.path.join(out_dir, gname), bg_rgb=(24, 18, 18), duration_ms=65)
        if tier == 1:
            save_gif_helper(seq, os.path.join(out_dir, "explode_gibs.gif"), bg_rgb=(24, 18, 18), duration_ms=65)

    orbit_seq = [
        b360.render_3d_explosion_frame(4, sim_hists[4][f], (f // 6) % 8, parts_360, scream_grid, norm_views, vfx_plates).resize((360, 255), Image.BICUBIC)
        for f in range(0, len(sim_hists[4]), 2)
    ]
    save_gif_helper(orbit_seq, os.path.join(out_dir, "explode_360_orbit.gif"), bg_rgb=(24, 18, 18), duration_ms=65)

    turn_seq = [roll_grid[(step // 3) % N_DIR][step % N_ANIM] for step in range(N_DIR * 3)]
    save_gif_helper(turn_seq, os.path.join(out_dir, "turn.gif"), duration_ms=55)

    # 3-Row x 5-Angle 360° Stunts Showcase Card (Fire-Wheels, Super-Long Bar & Wheels, Jetpack Hover + Spinning Bar)!
    scard = Image.new("RGB", (cw * 5, ch * 3), (18, 20, 26))
    sdr = ImageDraw.Draw(scard)
    st_dirs = [0, 1, 2, 4, 6]
    for col, cd in enumerate(st_dirs):
        b_im, c_sp = norm_views[cd]
        im_f = stunts.render_fire_wheels_frame(b_im, c_sp, cd, 0.35, animate_wheelman_frame, vfx_plates)
        im_l = stunts.render_super_long_bar_frame(cd, 0.50, stunt_kit, parts_360)
        im_j = stunts.render_jetpack_hover_frame(cd, 0.28, stunt_kit, parts_360, vfx_plates)
        for r_i, (st_lbl, st_im) in enumerate([("Fire-Wheels", im_f), ("Super-Long Bar", im_l), ("Jetpack+Spin", im_j)]):
            tile = Image.new("RGBA", (cw, ch), (20, 18, 24, 255))
            tile.alpha_composite(st_im.resize((cw, ch), Image.LANCZOS))
            scard.paste(tile.convert("RGB"), (col * cw, r_i * ch))
            sdr.text((col * cw + 6, r_i * ch + 5), f"{st_lbl} | {cd*45}°", fill=(120, 245, 190))
    scard.save(os.path.join(out_dir, "stunts_360_card.jpg"), quality=92)

    # Animated 360°-Orbiting GIFs for all 3 new stunts!
    fire_seq = [
        stunts.render_fire_wheels_frame(norm_views[(i // 3) % 8][0], norm_views[(i // 3) % 8][1], (i // 3) % 8, (i % 12) / 12.0, animate_wheelman_frame, vfx_plates).resize((360, 255), Image.BICUBIC)
        for i in range(24)
    ]
    save_gif_helper(fire_seq, os.path.join(out_dir, "fire_wheels.gif"), bg_rgb=(24, 18, 16), duration_ms=50)

    long_seq = [
        stunts.render_super_long_bar_frame((i // 3) % 8, i / 24.0, stunt_kit, parts_360).resize((360, 255), Image.BICUBIC)
        for i in range(24)
    ]
    save_gif_helper(long_seq, os.path.join(out_dir, "long_bar_wheels.gif"), bg_rgb=(20, 22, 28), duration_ms=55)

    jp_seq = [
        stunts.render_jetpack_hover_frame((i // 3) % 8, (i % 12) / 12.0, stunt_kit, parts_360, vfx_plates).resize((360, 255), Image.BICUBIC)
        for i in range(24)
    ]
    save_gif_helper(jp_seq, os.path.join(out_dir, "jetpack_hover.gif"), bg_rgb=(18, 22, 30), duration_ms=50)

    print(f"wrote {sheet_path}, turnaround_8dir.jpg, above_below_card.jpg, four_booms_360_card.jpg, stunts_360_card.jpg, and all explosion + stunt GIFs!")


def pil_to_webp_uri(im, quality=88):
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=quality, method=4)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def write_viewer(idle_frames, roll_grid, scream_grid, vert_dict, parts_360, stunt_kit, norm_views, vfx_plates, viewer_dir):
    os.makedirs(viewer_dir, exist_ok=True)
    for d in range(N_DIR):
        idle_frames[d].save(os.path.join(viewer_dir, f"wm_idle_d{d}.png"))

    idle_uris = [pil_to_webp_uri(im, quality=90) for im in idle_frames]
    roll_uris = [[pil_to_webp_uri(im, quality=88) for im in row] for row in roll_grid]
    scream_uris = [[pil_to_webp_uri(im, quality=88) for im in row] for row in scream_grid]

    above90_uris = dict(
        roll=[pil_to_webp_uri(im, quality=89) for im in vert_dict["above90"]["roll"]],
        scream=[pil_to_webp_uri(im, quality=89) for im in vert_dict["above90"]["scream"]],
    )
    above45_uris = dict(
        roll=[pil_to_webp_uri(im, quality=89) for im in vert_dict["above45"]["roll"]],
        scream=[pil_to_webp_uri(im, quality=89) for im in vert_dict["above45"]["scream"]],
    )
    below45_uris = dict(
        roll=[pil_to_webp_uri(im, quality=89) for im in vert_dict["below45"]["roll"]],
        scream=[pil_to_webp_uri(im, quality=89) for im in vert_dict["below45"]["scream"]],
    )
    below90_uris = dict(
        roll=[pil_to_webp_uri(im, quality=89) for im in vert_dict["below90"]["roll"]],
    )

    parts_uris = dict(
        heads=[pil_to_webp_uri(im, quality=90) for im in parts_360["heads"]],
        wheels=[pil_to_webp_uri(im, quality=90) for im in parts_360["wheels"]],
        bars=[pil_to_webp_uri(im, quality=90) for im in parts_360["bars"]],
        llegs=[pil_to_webp_uri(im, quality=89) for im in parts_360["llegs"]],
        rlegs=[pil_to_webp_uri(im, quality=89) for im in parts_360["rlegs"]],
        xrays=[pil_to_webp_uri(im, quality=88) for im in parts_360["xrays"]],
        xray_above90=pil_to_webp_uri(parts_360["xray_above90"], quality=88),
        gibs=[pil_to_webp_uri(im, quality=90) for im in parts_360["gibs"]],
        shrap_cap=pil_to_webp_uri(parts_360["shrap_cap"], quality=90),
        shrap_nut=pil_to_webp_uri(parts_360["shrap_nut"], quality=90),
    )
    vfx_uris = {k: pil_to_webp_uri(im, quality=88) for k, im in vfx_plates.items() if im is not None}
    stunts_uris = dict(
        body_only=[pil_to_webp_uri(im, quality=89) for im in stunt_kit["body_only"]],
        body_above90=pil_to_webp_uri(stunt_kit["body_above90"], quality=89),
        body_below90=pil_to_webp_uri(stunt_kit["body_below90"], quality=89),
        jetpacks=[pil_to_webp_uri(im, quality=90) for im in stunt_kit["jetpacks"]],
        jetpack_above=pil_to_webp_uri(stunt_kit["jetpack_above"], quality=90),
        jetpack_below=pil_to_webp_uri(stunt_kit["jetpack_below"], quality=90),
        c_specs=[
            [dict(cx=round(ws["cx"], 1), cy=round(ws["cy"], 1), rx=round(ws["rx"], 1), ry=round(ws["ry"], 1), ang=round(ws["ang"], 1)) for ws in norm_views[d][1]]
            for d in range(N_DIR)
        ],
    )

    self_contained_html = (
        VIEWER_HTML
        .replace("__IDLE_JSON__", json.dumps(idle_uris))
        .replace("__ROLL_JSON__", json.dumps(roll_uris))
        .replace("__SCREAM_JSON__", json.dumps(scream_uris))
        .replace("__ABOVE90_JSON__", json.dumps(above90_uris))
        .replace("__ABOVE45_JSON__", json.dumps(above45_uris))
        .replace("__BELOW45_JSON__", json.dumps(below45_uris))
        .replace("__BELOW90_JSON__", json.dumps(below90_uris))
        .replace("__PARTS360_JSON__", json.dumps(parts_uris))
        .replace("__VFX_JSON__", json.dumps(vfx_uris))
        .replace("__STUNTS_JSON__", json.dumps(stunts_uris))
    )
    html_path = os.path.join(viewer_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(self_contained_html)
    print(f"wrote 100% self-contained {html_path} ({len(self_contained_html)/1e6:.2f} MB)")


def _spr_keyframes_for_tier(tier):
    """Selects 14 dramatic evenly-paced keyframes for SPR32 with s=5 pinned at primary detonation!"""
    return {
        1: [0, 7, 14, 20, 26, 30, 34, 39, 44, 51, 58, 65, 73, 83],
        2: [0, 7, 14, 20, 26, 30, 35, 41, 50, 58, 68, 79, 91, 107],
        3: [0, 8, 16, 22, 29, 34, 42, 54, 68, 82, 96, 106, 118, 131],
        4: [0, 9, 18, 26, 33, 38, 46, 58, 72, 88, 106, 128, 152, 167],
    }[tier]


def main():
    print("[1/6] Assembling 8 photorealistic 360° eye-level master views...")
    master_views, ref_skin = build_master_8_views()
    norm_views = [place_view_on_canvas(im, ws, d) for d, (im, ws) in enumerate(master_views)]

    print("[2/6] Building & skin-matching Above (+90°, +45°) & Below (-45°, -90°) vertical pitch views...")
    vert_raw = fx.build_vertical_pitch_views(
        VIEWS_DIR, ref_skin, key_studio_magenta, inpaint_region_with_surrounding_skin, calibrate_skin_to_ref, rot_ell_grid
    )
    vert_norm = {pk: fx.normalize_vertical_view(im, pk, CANVAS) for pk, im in vert_raw.items()}

    print("[3/6] Synthesizing high-FPS (12-phase) 360° Rolling, Screaming & Above/Below animations...")
    idle_frames = []
    roll_grid = []
    scream_grid = []
    for d in range(N_DIR):
        base_im, c_specs = norm_views[d]
        idle_frames.append(animate_wheelman_frame(base_im, d, 0.0, c_specs, mode="idle"))
        d_roll = []
        d_scream = []
        for k in range(N_ANIM):
            ph = k / float(N_ANIM)
            r_im = animate_wheelman_frame(base_im, d, ph, c_specs, mode="roll")
            d_roll.append(r_im)
            s_im = fx.apply_scream_face_and_body(r_im, d, ph, c_specs, ground_y=GROUND, intensity=1.08, sound_waves=True)
            d_scream.append(s_im)
        roll_grid.append(d_roll)
        scream_grid.append(d_scream)

    vert_dict = {}
    for pk in ("above90", "above45", "below45", "below90"):
        v_roll = [fx.animate_vertical_pitch_frame(vert_norm[pk], pk, k / float(N_ANIM), scream=False) for k in range(N_ANIM)]
        v_scream = [fx.animate_vertical_pitch_frame(vert_norm[pk], pk, k / float(N_ANIM), scream=True) for k in range(N_ANIM)] if pk != "below90" else []
        vert_dict[pk] = dict(roll=v_roll, scream=v_scream)

    spr32_only = ("--spr32-only" in sys.argv)
    print("[4/6] Extracting 8-angle 360° parts, stunt kit & VFX plates...")
    parts_360 = b360.extract_all_360_parts(norm_views, scream_grid, vert_norm)
    vfx_plates = b360.build_vfx_plates_dict(VIEWS_DIR)
    stunt_kit = stunts.extract_stunt_sprite_kit(norm_views, vert_norm, parts_360)
    sim_hists = {} if spr32_only else {tier: b360.simulate_3d_explosion_tier(tier) for tier in (1, 2, 3, 4)}

    print("[5/6] Packing 224-frame tight-cropped DarkPlaces progs/wheelman.spr32 (type 2 SPR_VP_PARALLEL)...")
    # 224-frame contract (matches wcannon.qc, wheelman.qc, mbox.qc, intro_director*.qc):
    #   0..7     (8)  : idle          (d = 0..7)
    #   8..55    (48) : driving       (8 + d*6 + k, k = 0..5)
    #   56..87   (32) : screaming     (56 + d*4 + k, k = 0..3)
    #   88..111  (24) : above90       (88 + d*3 + k, k = 0..2, centered origin)
    #   112..135 (24) : below90       (112 + d*3 + k, k = 0..2)
    #   136..167 (32) : fire-wheels   (136 + d*4 + k, k = 0..3)
    #   168..199 (32) : long-bar      (168 + d*4 + k, k = 0..3)
    #   200..223 (24) : above45       (200 + d*3 + k, k = 0..2, centered origin)
    above45_8dir = fx.build_above45_8dir_roll(
        VIEWS_DIR, ref_skin, key_studio_magenta, inpaint_region_with_surrounding_skin, calibrate_skin_to_ref, rot_ell_grid,
        vert_dict["above45"]["roll"], CANVAS,
    )
    toned_frames = []
    for d in range(N_DIR):
        toned_frames.append(to_spr32_toned(idle_frames[d]))
    for d in range(N_DIR):
        for k in range(6):
            toned_frames.append(to_spr32_toned(roll_grid[d][k * 2]))
    for d in range(N_DIR):
        for k in range(4):
            toned_frames.append(to_spr32_toned(scream_grid[d][k * 3]))
    for d in range(N_DIR):
        for k in range(3):
            rot_ab = vert_dict["above90"]["roll"][k * 4].rotate(-d * 45.0, resample=Image.BICUBIC, expand=False)
            toned_frames.append(to_spr32_toned(rot_ab))
    for d in range(N_DIR):
        for k in range(3):
            rot_bl = vert_dict["below90"]["roll"][k * 4].rotate(+d * 45.0, resample=Image.BICUBIC, expand=False)
            toned_frames.append(to_spr32_toned(rot_bl))
    for d in range(N_DIR):
        b_im, c_sp = norm_views[d]
        for k in range(4):
            fr_fw = stunts.render_fire_wheels_frame(b_im, c_sp, d, k / 4.0, animate_wheelman_frame, vfx_plates)
            toned_frames.append(to_spr32_toned(fr_fw))
    for d in range(N_DIR):
        for k in range(4):
            fr_lb = stunts.render_super_long_bar_frame(d, k / 4.0, stunt_kit, parts_360)
            toned_frames.append(to_spr32_toned(fr_lb))
    for d in range(N_DIR):
        for k in range(3):
            toned_frames.append(to_spr32_toned(above45_8dir[d][k]))

    assert len(toned_frames) == 224, f"Expected 224 SPR32 frames, got {len(toned_frames)}"
    overhead_indices = set(range(88, 112)) | set(range(200, 224))
    write_spr32(os.path.join(PROGS_DIR, "wheelman.spr32"), toned_frames, ground_y=SPR_GROUND, sprite_type=2, center_indices=overhead_indices)

    os.makedirs(OUT_DIR, exist_ok=True)
    # Audit contact sheet for above90 (88..111) + above45 (200..223)
    cw_a, ch_a = 150, 118
    audit = Image.new("RGB", (cw_a * 8, ch_a * 6), (26, 29, 36))
    adr = ImageDraw.Draw(audit)
    for row_blk, (lbl, base_idx) in enumerate([("above90", 88), ("above45", 200)]):
        for d in range(N_DIR):
            for k in range(3):
                r = row_blk * 3 + k
                fr = toned_frames[base_idx + d * 3 + k]
                tile = Image.new("RGBA", (cw_a, ch_a), (30 + 5 * ((r + d) % 2), 33, 40, 255))
                tile.alpha_composite(fr, ((cw_a - fr.width) // 2, (ch_a - fr.height) // 2))
                audit.paste(tile.convert("RGB"), (d * cw_a, r * ch_a))
                adr.text((d * cw_a + 4, r * ch_a + 3), f"{lbl} f{base_idx+d*3+k} d{d}k{k}", fill=(120, 240, 180))
    audit_path = os.path.join(OUT_DIR, "audit_overhead_sheet.png")
    audit.save(audit_path)
    print(f"wrote {audit_path}")

    if not spr32_only:
        print("[6/6] Writing showcase sheets, explosion + stunt GIFs, and self-contained wheelman_sprite/index.html...")
        write_sheets_and_gifs(idle_frames, roll_grid, scream_grid, vert_dict, sim_hists, parts_360, stunt_kit, norm_views, vfx_plates, OUT_DIR)
        write_viewer(idle_frames, roll_grid, scream_grid, vert_dict, parts_360, stunt_kit, norm_views, vfx_plates, VIEWER_DIR)
    print("ALL DONE!")


if __name__ == "__main__":
    main()
