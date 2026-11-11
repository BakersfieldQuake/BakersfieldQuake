"""Core Chroma-Keying, Premultiplied-Alpha Compositing, Optical-Flow 16-Angle Synthesis,
and 60 FPS Mechanical Tire/Pipe VFX primitives for the Digitized Green-Suit Wheelman Monster.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

# Super-sampled working canvas & final output canvas sizes
SS_W = 384
SS_H = 384
SS_CX = 192
SS_GROUND = 338

OUT_W = 260
OUT_H = 260
OUT_CX = 130
OUT_GROUND = 229

SPR_W = 240
SPR_H = 240
SPR_GROUND = 211

N_DIRS = 16
ANGLES_DEG = [d * 22.5 for d in range(N_DIRS)]


# ---------------------------------------------------------------------------
# 1. Exact Zero-Spill #FF00FF Magenta Chroma Keyer & Foreground Color Unmixer
# ---------------------------------------------------------------------------

def key_magenta_plate(
    img_path: str,
    low_thresh: float = 32.0,
    high_thresh: float = 195.0,
    erode_px: float = 0.65,
) -> np.ndarray:
    """Extracts a razor-sharp RGBA cutout from a #FF00FF studio plate with ZERO purple halo.

    Uses `mag_score = min(R, B) - G`, which is ~255 on pure #FF00FF background, <= 5 on warm
    human skin/mouth/tongue, ~0 on black rubber/white rims/chrome steel, and ~-170 on the
    neon lime-green spandex morphsuit. Boundary pixels inherit uncontaminated interior RGB
    via Euclidean nearest-interior-pixel propagation while preserving smooth anti-aliased alpha.
    """
    pil_im = Image.open(img_path).convert("RGB")
    rgb = np.asarray(pil_im, dtype=np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    mag_score = np.minimum(r, b) - g
    raw_alpha = 1.0 - np.clip((mag_score - low_thresh) / (high_thresh - low_thresh), 0.0, 1.0)

    # Remove tiny isolated dust specks in background (< 64 px)
    fg_hard = raw_alpha > 0.15
    lbl, n_cc = ndimage.label(fg_hard)
    if n_cc > 1:
        sizes = ndimage.sum(fg_hard, lbl, range(1, n_cc + 1))
        max_sz = max(sizes) if len(sizes) else 0
        keep = np.zeros(n_cc + 1, dtype=bool)
        for idx, sz in enumerate(sizes, start=1):
            if sz >= max(64, max_sz * 0.008):
                keep[idx] = True
        mask_keep = keep[lbl]
        raw_alpha = np.where(mask_keep | (ndimage.binary_dilation(mask_keep, iterations=2) & (raw_alpha > 0.02)), raw_alpha, 0.0)

    # Slight sub-pixel inward trim + Gaussian AA feather so JPEG ringing never survives
    if erode_px > 0:
        dist_in = ndimage.distance_transform_edt(raw_alpha > 0.5)
        dist_out = ndimage.distance_transform_edt(raw_alpha <= 0.5)
        sdf = dist_in - dist_out - erode_px
        aa_alpha = np.clip(sdf / 1.35 + 0.5, 0.0, 1.0)
        alpha = np.minimum(raw_alpha, aa_alpha)
    else:
        alpha = raw_alpha

    # Propagate clean interior RGB (`mag_score < 22` and `alpha > 0.96`) outward into boundary band
    clean_core = (alpha > 0.95) & (mag_score < 24.0)
    if np.any(clean_core):
        _, nearest_idx = ndimage.distance_transform_edt(~clean_core, return_indices=True)
        clean_rgb = rgb[nearest_idx[0], nearest_idx[1]]
        # Blend toward clean interior RGB wherever mag_score shows any magenta contamination
        spill_w = np.clip((mag_score - 12.0) / 38.0, 0.0, 1.0)[..., None]
        edge_w = np.clip((0.98 - alpha) / 0.35, 0.0, 1.0)[..., None]
        w = np.maximum(spill_w, edge_w)
        despilled = rgb * (1.0 - w) + clean_rgb * w
        # Extra clamp: on green suit edges, never let R or B exceed interior R, B
        despilled[..., 0] = np.where(mag_score > 18.0, np.minimum(despilled[..., 0], clean_rgb[..., 0]), despilled[..., 0])
        despilled[..., 2] = np.where(mag_score > 18.0, np.minimum(despilled[..., 2], clean_rgb[..., 2]), despilled[..., 2])
    else:
        despilled = rgb

    alpha_u8 = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(despilled), 0, 255).astype(np.uint8)
    rgb_u8[alpha_u8 == 0] = 0
    return np.dstack([rgb_u8, alpha_u8])


# ---------------------------------------------------------------------------
# 2. Premultiplied Alpha Resize, Affine/Warp & Compositing Helpers
# ---------------------------------------------------------------------------

def to_premul_f32(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    rgb_p = rgba[..., :3].astype(np.float32) * a
    return np.concatenate([rgb_p, a * 255.0], axis=-1)


def from_premul_f32(premul: np.ndarray) -> np.ndarray:
    a255 = np.clip(premul[..., 3:4], 0.0, 255.0)
    a01 = a255 / 255.0
    rgb = np.where(a01 > 1e-4, premul[..., :3] / np.maximum(a01, 1e-4), 0.0)
    out = np.concatenate([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(a255), 0, 255).astype(np.uint8),
    ], axis=-1)
    out[out[..., 3] < 2] = 0
    return out


def resize_rgba_premul(rgba: np.ndarray, new_w: int, new_h: int) -> np.ndarray:
    if rgba.shape[1] == new_w and rgba.shape[0] == new_h:
        return rgba.copy()
    pm = to_premul_f32(rgba)
    interp = cv2.INTER_AREA if (new_w < rgba.shape[1] or new_h < rgba.shape[0]) else cv2.INTER_LANCZOS4
    pm_rs = cv2.resize(pm, (new_w, new_h), interpolation=interp)
    return from_premul_f32(pm_rs)


def alpha_over(dst: np.ndarray, src: np.ndarray) -> np.ndarray:
    if src is None or not np.any(src[..., 3] > 0):
        return dst
    sa = src[..., 3:4].astype(np.float32) / 255.0
    da = dst[..., 3:4].astype(np.float32) / 255.0
    oa = sa + da * (1.0 - sa)
    s_rgb = src[..., :3].astype(np.float32)
    d_rgb = dst[..., :3].astype(np.float32)
    o_rgb = np.where(oa > 1e-5, (s_rgb * sa + d_rgb * da * (1.0 - sa)) / np.maximum(oa, 1e-5), 0.0)
    return np.concatenate([
        np.clip(np.round(o_rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(oa * 255.0), 0, 255).astype(np.uint8),
    ], axis=-1)


def flip_rgba_h(rgba: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(rgba[:, ::-1, :])


def bbox_of_rgba(rgba: np.ndarray, alpha_min: int = 16) -> Tuple[int, int, int, int]:
    ys, xs = np.where(rgba[..., 3] >= alpha_min)
    if len(xs) == 0:
        return (0, 0, rgba.shape[1], rgba.shape[0])
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def normalize_on_ss_canvas(
    rgba: np.ndarray,
    target_h: int,
    ground_y: int = SS_GROUND,
    cx_offset: int = 0,
    max_w: int = 346,
) -> np.ndarray:
    """Crops subject tight, scales to `target_h` (clamping width to `max_w` if very wide like plank),
    centers horizontally on `SS_CX + cx_offset` by alpha mass/bbox, and plants bottom at `ground_y`.
    """
    x0, y0, x1, y1 = bbox_of_rgba(rgba, alpha_min=20)
    crop = rgba[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    scale = target_h / max(ch, 1)
    if cw * scale > max_w:
        scale = max_w / max(cw, 1)
    nw = max(4, int(round(cw * scale)))
    nh = max(4, int(round(ch * scale)))
    scaled = resize_rgba_premul(crop, nw, nh)

    # Compute robust horizontal center (blending bbox midpoint and centroid so extended limbs stay balanced)
    a_mass = scaled[..., 3].astype(np.float32)
    xs_grid = np.arange(nw, dtype=np.float32)[None, :]
    cx_mass = float(np.sum(a_mass * xs_grid) / max(float(np.sum(a_mass)), 1.0))
    cx_mid = 0.5 * nw
    anchor_x = 0.45 * cx_mass + 0.55 * cx_mid

    canvas = np.zeros((SS_H, SS_W, 4), dtype=np.uint8)
    px = int(round(SS_CX + cx_offset - anchor_x))
    py = int(round(ground_y - nh))

    # Safe clip blit
    sx0 = max(0, -px)
    sy0 = max(0, -py)
    dx0 = max(0, px)
    dy0 = max(0, py)
    bw = min(nw - sx0, SS_W - dx0)
    bh = min(nh - sy0, SS_H - dy0)
    if bw > 0 and bh > 0:
        canvas[dy0:dy0 + bh, dx0:dx0 + bw] = scaled[sy0:sy0 + bh, sx0:sx0 + bw]
    return canvas


def harmonize_green_suit_and_contrast(rgba: np.ndarray, ref_green_luma: float = 186.0) -> np.ndarray:
    """Locks green morphsuit brightness/saturation across all studio plates so 360° rotation never flickers."""
    out = rgba.copy()
    a = out[..., 3] > 140
    if not np.any(a):
        return out
    rgb = out[..., :3].astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # Detect green spandex pixels: strong green dominance over red and blue
    suit_mask = a & (g > r * 1.18) & (g > b * 1.45) & (g > 75.0)
    if np.sum(suit_mask) > 200:
        med_g = float(np.median(g[suit_mask]))
        gain = np.clip(ref_green_luma / max(med_g, 1.0), 0.86, 1.16)
        # Apply gentle luminance normalization globally to foreground so shadows/skin stay cohesive
        soft_gain = 1.0 + 0.65 * (gain - 1.0)
        rgb = np.clip(rgb * soft_gain, 0.0, 255.0)
        out[..., :3] = np.round(rgb).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------
# 3. Sharp Flow-Guided Midpoint View Synthesis (for Odd 22.5° Steps!)
# ---------------------------------------------------------------------------

def synthesize_midpoint_view(im_a: np.ndarray, im_b: np.ndarray, t: float = 0.5) -> np.ndarray:
    """Synthesizes an ultra-crisp intermediate 22.5° view between two adjacent 45° studio plates
    WITHOUT ghosted double-edges!

    Method:
      1. Computes bidirectional Dense Inverse Search (DIS) optical flow on silhouette-guided luminance +
         row-scanline horizontal contour correspondence for the outer silhouette.
      2. Advects BOTH `im_a` forward by `t` and `im_b` backward by `1-t` in premultiplied RGBA space.
      3. Uses Signed-Distance-Field (SDF) contour interpolation for a razor-sharp single silhouette,
         and frequency-selective detail fusion (preserving sharp high-frequency detail from the better-aligned
         source where local pixel disagreement is high, preventing double-feature ghosting).
    """
    h, w = im_a.shape[:2]
    aa = im_a[..., 3].astype(np.float32) / 255.0
    ab = im_b[..., 3].astype(np.float32) / 255.0

    # 1. Row-wise horizontal span correspondence (captures bulk 22.5° yaw rotation cleanly!)
    grid_x, grid_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    row_shift_ab = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        xa = np.where(aa[y] > 0.25)[0]
        xb = np.where(ab[y] > 0.25)[0]
        if len(xa) >= 4 and len(xb) >= 4:
            la, ra = float(xa[0]), float(xa[-1])
            lb, rb = float(xb[0]), float(xb[-1])
            wa = max(ra - la, 4.0)
            u = np.clip((grid_x[y] - la) / wa, -0.3, 1.3)
            mapped_x = lb + u * (rb - lb)
            row_shift_ab[y] = np.clip(mapped_x - grid_x[y], -44.0, 44.0)
    row_shift_ab = cv2.GaussianBlur(row_shift_ab, (0, 0), sigmaX=9.0, sigmaY=7.0)

    # 2. Dense DIS optical flow on dark-composited grayscale for fine internal features (face, rims, pipe)
    ga = cv2.cvtColor(im_a[..., :3], cv2.COLOR_RGB2GRAY).astype(np.float32) * aa
    gb = cv2.cvtColor(im_b[..., :3], cv2.COLOR_RGB2GRAY).astype(np.float32) * ab
    ga_u8 = np.clip(ga, 0, 255).astype(np.uint8)
    gb_u8 = np.clip(gb, 0, 255).astype(np.uint8)

    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dis.setFinestScale(1)
    dis.setPatchSize(12)
    dis.setPatchStride(4)
    flow_ab = dis.calc(ga_u8, gb_u8, None)
    flow_ba = dis.calc(gb_u8, ga_u8, None)

    # Blend smooth row correspondence with clamped optical flow
    fx_ab = 0.55 * np.clip(flow_ab[..., 0], -42.0, 42.0) + 0.45 * row_shift_ab
    fy_ab = 0.65 * np.clip(flow_ab[..., 1], -26.0, 26.0)
    fx_ba = 0.55 * np.clip(flow_ba[..., 0], -42.0, 42.0) - 0.45 * row_shift_ab
    fy_ba = 0.65 * np.clip(flow_ba[..., 1], -26.0, 26.0)

    fx_ab = cv2.GaussianBlur(fx_ab, (0, 0), 3.2)
    fy_ab = cv2.GaussianBlur(fy_ab, (0, 0), 3.2)
    fx_ba = cv2.GaussianBlur(fx_ba, (0, 0), 3.2)
    fy_ba = cv2.GaussianBlur(fy_ba, (0, 0), 3.2)

    pm_a = to_premul_f32(im_a)
    pm_b = to_premul_f32(im_b)

    # Inverse-pull coordinates at midpoint: pixel at p samples A at `p + (t)*flow_ba_approx` = `p - t*flow_ab`
    map_ax = (grid_x - t * fx_ab).astype(np.float32)
    map_ay = (grid_y - t * fy_ab).astype(np.float32)
    map_bx = (grid_x - (1.0 - t) * fx_ba).astype(np.float32)
    map_by = (grid_y - (1.0 - t) * fy_ba).astype(np.float32)

    wa_pm = cv2.remap(pm_a, map_ax, map_ay, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    wb_pm = cv2.remap(pm_b, map_bx, map_by, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    wa_rgba = from_premul_f32(wa_pm)
    wb_rgba = from_premul_f32(wb_pm)

    # 3. Crisp SDF silhouette interpolation so edges are 100% solid (never half-transparent ghosts!)
    wa_bin = wa_rgba[..., 3] > 110
    wb_bin = wb_rgba[..., 3] > 110
    sdf_a = ndimage.distance_transform_edt(wa_bin) - ndimage.distance_transform_edt(~wa_bin)
    sdf_b = ndimage.distance_transform_edt(wb_bin) - ndimage.distance_transform_edt(~wb_bin)
    sdf_mid = (1.0 - t) * sdf_a + t * sdf_b
    mid_alpha = np.clip(sdf_mid / 1.30 + 0.5, 0.0, 1.0)

    # 4. Anti-ghosting RGB fusion: where both warped views exist, blend low-freq smoothly but favor sharper/consistent side
    ca = wa_rgba[..., :3].astype(np.float32)
    cb = wb_rgba[..., :3].astype(np.float32)
    va = (wa_rgba[..., 3].astype(np.float32) / 255.0)[..., None]
    vb = (wb_rgba[..., 3].astype(np.float32) / 255.0)[..., None]

    # Propagate nearest valid RGB inside each warped image so silhouette edge never mixes black
    if np.any(wa_bin):
        _, ia = ndimage.distance_transform_edt(~wa_bin, return_indices=True)
        ca_fill = ca[ia[0], ia[1]]
    else:
        ca_fill = ca
    if np.any(wb_bin):
        _, ib = ndimage.distance_transform_edt(~wb_bin, return_indices=True)
        cb_fill = cb[ib[0], ib[1]]
    else:
        cb_fill = cb

    diff = np.mean(np.abs(ca_fill - cb_fill), axis=-1, keepdims=True)
    # Where pixels strongly disagree (e.g. occluded tire vs green leg), sharpen blend weight toward dominant alpha/SDF side
    sharp_w = np.clip(0.5 + (sdf_b - sdf_a)[..., None] * 0.16, 0.0, 1.0)
    agree_w = np.clip(1.0 - (diff - 22.0) / 48.0, 0.0, 1.0)
    w_b = agree_w * t + (1.0 - agree_w) * np.where(sharp_w >= 0.5, 0.88, 0.12)
    # Also respect valid alpha support
    only_a = (va > 0.35) & (vb < 0.12)
    only_b = (vb > 0.35) & (va < 0.12)
    w_b = np.where(only_a, 0.0, np.where(only_b, 1.0, w_b))

    rgb_mid = ca_fill * (1.0 - w_b) + cb_fill * w_b
    # Subtle unsharp micro-detail restore so midpoint frames match native plate crispness
    blur_mid = cv2.GaussianBlur(rgb_mid, (0, 0), 1.05)
    rgb_crisp = np.clip(rgb_mid + 0.28 * (rgb_mid - blur_mid), 0.0, 255.0)

    a_u8 = np.clip(np.round(mid_alpha * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.round(rgb_crisp).astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return np.dstack([rgb_u8, a_u8])


# ---------------------------------------------------------------------------
# 4. 60 FPS Tire-Tread Spin, Valve-Stem Rotation, Sparks & Ground Shadow FX
# ---------------------------------------------------------------------------

def detect_tire_regions_and_spin(
    rgba: np.ndarray,
    d_idx: int,
    spin_angle_rad: float,
    tread_strength: float = 1.0,
) -> np.ndarray:
    """Animates realistic 60 FPS rotational tire-tread lugs, white-rim specular sweep, and hub rotation
    directly on the real photographic black pneumatic tires across all 16 compass angles!
    """
    out = rgba.copy()
    alpha = out[..., 3] > 150
    if not np.any(alpha):
        return out

    rgb = out[..., :3].astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)

    # Black pneumatic rubber pixels: low luma (< 68), low chroma saturation (< 32), below upper torso
    yy, xx = np.indices(rgba.shape[:2], dtype=np.float32)
    x0, y0, x1, y1 = bbox_of_rgba(rgba)
    mid_y = y0 + 0.30 * (y1 - y0)
    tire_mask = alpha & (luma < 72.0) & (sat < 34.0) & (yy > mid_y)
    # Clean small regions (e.g. beard/mouth shadow) by keeping only connected components in lower wheel zone
    lbl, n_cc = ndimage.label(tire_mask)
    if n_cc == 0:
        return out

    ang_deg = d_idx * 22.5
    ang_rad = math.radians(ang_deg)
    # Near side profile (around 90° left or 270° right): circular rotational lugs around wheel hub!
    side_ness = abs(math.sin(ang_rad))  # 1.0 at 90°/270°, 0.0 at 0°/180°
    roll_dir = 1.0 if math.cos(ang_rad) >= 0.0 else -1.0
    side_sign = -1.0 if math.sin(ang_rad) >= 0.0 else 1.0

    for cc_id in range(1, n_cc + 1):
        m = lbl == cc_id
        area = int(np.sum(m))
        if area < 220:
            continue
        ys_c, xs_c = np.where(m)
        cy = float(np.mean(ys_c))
        cx = float(np.mean(xs_c))
        # Skip dark mouth/beard if high up near head center
        if cy < y0 + 0.36 * (y1 - y0) and abs(cx - SS_CX) < 48:
            continue
        rx = max(8.0, 0.5 * float(xs_c.max() - xs_c.min()))
        ry = max(14.0, 0.5 * float(ys_c.max() - ys_c.min()))

        du = (xx - cx) / rx
        dv = (yy - cy) / ry
        theta_polar = np.arctan2(dv, du) - side_sign * spin_angle_rad
        r_polar = np.hypot(du, dv)

        # Circumferential + transverse lug wave for foreshortened views
        theta_cyl = np.arcsin(np.clip(dv, -0.98, 0.98))
        lug_cyl = np.sin(11.0 * theta_cyl - roll_dir * spin_angle_rad * 2.0) * np.cos(theta_cyl)
        scuff_cyl = np.cos(3.0 * theta_cyl - roll_dir * spin_angle_rad) * np.cos(theta_cyl)

        # Polar radial tread lugs for side-facing views
        lug_side = np.sin(14.0 * theta_polar) * np.clip((r_polar - 0.45) / 0.25, 0.0, 1.0)
        scuff_side = np.cos(2.0 * theta_polar + 0.6) * np.clip((r_polar - 0.40) / 0.30, 0.0, 1.0)

        delta = (
            side_ness * (lug_side * 12.5 + scuff_side * 9.0)
            + (1.0 - side_ness) * (lug_cyl * 13.0 + scuff_cyl * 8.5)
        ) * tread_strength

        rgb[m] = np.clip(rgb[m] + delta[m, None], 4.0, 118.0)

    out[..., :3] = np.round(rgb).astype(np.uint8)
    return out


def make_contact_shadow(
    width_px: float,
    depth_px: float,
    cx: float = SS_CX,
    ground_y: float = SS_GROUND,
    opacity: float = 0.42,
) -> np.ndarray:
    """Renders a soft elliptical ground-contact shadow under the tires/feet so the sprite feels grounded."""
    layer = np.zeros((SS_H, SS_W, 4), dtype=np.uint8)
    if opacity <= 0.01:
        return layer
    yy, xx = np.indices((SS_H, SS_W), dtype=np.float32)
    u = (xx - cx) / max(width_px * 0.5, 4.0)
    v = (yy - ground_y) / max(depth_px * 0.5, 3.0)
    r2 = u * u + v * v
    a = np.clip(1.0 - r2, 0.0, 1.0) ** 1.75 * opacity
    layer[..., 3] = np.clip(np.round(a * 255.0), 0, 255).astype(np.uint8)
    return layer


def draw_sparks_and_dust(
    canvas: np.ndarray,
    origins: List[Tuple[float, float]],
    phase_01: float,
    vel_bias: Tuple[float, float] = (0.0, -1.0),
    intensity: float = 1.0,
    seed: int = 7,
    include_ring: bool = False,
) -> np.ndarray:
    """Draws crisp hot-orange/gold/white chrome-pipe & tire friction sparks at 60 FPS."""
    if intensity <= 0.02:
        return canvas
    pil = Image.fromarray(canvas, "RGBA")
    overlay = Image.new("RGBA", (SS_W, SS_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    rng = np.random.RandomState(seed)

    if include_ring and origins:
        ox, oy = origins[0]
        rr = 14.0 + phase_01 * 96.0
        ry = rr * 0.30
        ring_a = int(round(max(0.0, 1.0 - phase_01 * 1.25) * 215 * min(intensity, 1.3)))
        if ring_a > 8:
            dr.ellipse([ox - rr, oy - ry, ox + rr, oy + ry], outline=(255, 226, 110, ring_a), width=4)
            dr.ellipse([ox - rr * 0.72, oy - ry * 0.72, ox + rr * 0.72, oy + ry * 0.72], outline=(160, 255, 110, ring_a // 2), width=2)

    n_sparks = int(round(14 * intensity))
    for ox, oy in origins:
        for i in range(n_sparks):
            p_local = (phase_01 * 2.4 + i / max(n_sparks, 1) * 0.83) % 1.0
            ang = rng.uniform(-2.65, -0.45)
            spd = rng.uniform(34.0, 118.0) * (0.7 + 0.5 * intensity)
            vx = math.cos(ang) * spd + vel_bias[0] * 48.0
            vy = math.sin(ang) * spd + vel_bias[1] * 26.0
            sx0 = ox + vx * p_local
            sy0 = oy + vy * p_local + 105.0 * (p_local ** 2)
            p_prev = max(0.0, p_local - 0.085)
            sx1 = ox + vx * p_prev
            sy1 = oy + vy * p_prev + 105.0 * (p_prev ** 2)
            fade = max(0.0, 1.0 - p_local * 1.08)
            a_val = int(round(255 * fade * min(1.0, intensity)))
            if a_val < 14:
                continue
            col = (255, 245, 190, a_val) if i % 3 == 0 else (255, 172, 42, a_val)
            dr.line([(sx1, sy1), (sx0, sy0)], fill=col, width=2 if i % 2 == 0 else 3)
            dr.ellipse([sx0 - 1.8, sy0 - 1.8, sx0 + 1.8, sy0 + 1.8], fill=(255, 255, 235, a_val))

    pil.alpha_composite(overlay)
    return np.asarray(pil, dtype=np.uint8)
