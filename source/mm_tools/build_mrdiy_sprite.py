"""Builds the Full-Body Rob MR. D.I.Y. Dancing Sprite Pack & 8-Direction 360° Quake SPR32!

Features:
  1. Real 1080p video cutouts of Rob's hysterical MR. D.I.Y. double-fist pumping dance
     (MaskRCNN + GrabCut + SIFT clean-plate background pocket removal + rim decontamination).
  2. Full-length studio photographic black jeans + shoes across all turnaround angles,
     rigged with C1-smooth 3-bone skeletal warping (`warp_limb_3bone`) for energetic
     knee-popping, kicking, hip-swaying happy-feet dancing — showing complete legs & shoes
     in every single frame!
  3. Authentic MR. D.I.Y. storefront emblem halo, cartoon-eyed thumbs-up hammer mascots,
     gleaming Phillips logo screws, yellow MR. D.I.Y. shopping bags, and 'LOW PRICES!' bursts.

Outputs:
  1. G:/Quake/Combat/BakersfieldQuake/mrdiy_sprite/
       - mrdiy_00.png .. mrdiy_15.png        (16-frame seamless full-body Hero Dance RGBA PNGs)
       - mrdiy_d{0..7}_f{0..5}.png           (48 directional 360° turnaround dance/run RGBA PNGs)
       - mrdiy_sheet_4x4.png                 (4x4 transparent master sprite sheet of Hero Dance)
       - mrdiy_360_sheet_8x6.png             (8-angle x 6-frame transparent 360° sprite sheet)
       - mrdiy_dance.gif                     (transparent animated GIF of full-body Hero Dance)
       - mrdiy_showcase.gif                  (smooth AA dark-checker showcase GIF)
       - mrdiy_360_spin.gif                  (animated 360° spinning + dancing turnaround GIF)
       - index.html                          (interactive viewer w/ Hero Dance + 360° drag spin + real laugh audio)
  2. G:/Quake/Combat/BakersfieldQuake/progs/fr_mrdiy.spr32
       - 56-frame IDSP v32 SPR_VP_PARALLEL_UPRIGHT Quake sprite (0..7 idle, 8..55 8-dir x 6 run/dance,
         origin anchored at Rob's shoes).

Run with:
    python3.13 source/mm_tools/build_mrdiy_sprite.py
"""

import math
import os
import shutil
import struct
import sys
import cv2
import numpy as np
import torch
import torchvision
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

ROOT = r"G:\Quake\Combat\BakersfieldQuake"
BRAIN = r"C:\Users\qxdc\.gemini\antigravity\brain\e873d05a-e2f8-4a19-9760-d70257005519"
SCRATCH = os.path.join(BRAIN, "scratch")
VID_PATH = os.path.join(BRAIN, ".user_uploaded", "media_1793456101966_09c2482d.mp4")
ASSETS_DIR = os.path.join(ROOT, "source", "mm_tools", "out", "mrdiy", "assets")
OUT_DIR = os.path.join(ROOT, "mrdiy_sprite")
PROGS_DIR = os.path.join(ROOT, "progs")

sys.path.insert(0, os.path.join(ROOT, "source", "mm_tools"))
import mrdiy_props

CANVAS_W = 720
CANVAS_H = 780

N_HERO = 16
N_DIRS = 8
N_DIR_FRAMES = 6

DIR_LABELS = [
    "0° Front",
    "45° Front-Left",
    "90° Left Side",
    "135° Back-Left",
    "180° Back",
    "225° Back-Right",
    "270° Right Side",
    "315° Front-Right",
]

# Richard Williams 8-frame run/groove profile keyframes (facing LEFT = -X):
# (theta_hip_deg, theta_knee_deg, theta_foot_deg, sy_thigh, body_bob_dy)
RUN_8_PROFILE = [
    (+29.0,  -6.0, +12.0, 1.00, +3.0),
    (+14.0, -21.0,   0.0, 0.99, +7.0),
    ( -7.0, -13.0,  -9.0, 1.00, +1.0),
    (-27.0, -18.0, -20.0, 1.01, -5.0),
    (-21.0, -58.0, -16.0, 0.98, -7.0),
    ( +6.0, -64.0,  -8.0, 0.96, -2.0),
    (+32.0, -42.0,  +4.0, 0.95, -5.0),
    (+33.0, -16.0, +13.0, 0.98, -1.0),
]


# ---------------------------------------------------------------------------
# 1. Self-Contained Studio Keying & 3-Bone C1 Skeletal Limb Warping Helpers
# ---------------------------------------------------------------------------

def seg_dist_grid(xg: np.ndarray, yg: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    vx, vy = x1 - x0, y1 - y0
    l2 = max(vx * vx + vy * vy, 1e-6)
    t = np.clip(((xg - x0) * vx + (yg - y0) * vy) / l2, 0.0, 1.0)
    return np.hypot(xg - (x0 + t * vx), yg - (y0 + t * vy))


def key_magenta_studio(im_rgb: Image.Image) -> np.ndarray:
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()
    m = np.minimum(r, b) - g

    bg = (m > 62.0) & (r > 95.0) & (b > 95.0)
    dist = ndimage.distance_transform_edt(~bg)

    alpha = np.ones_like(m, dtype=np.float32)
    alpha[bg] = 0.0
    edge = (~bg) & (dist <= 9.0)
    a_ramp = np.clip(1.0 - (m - 10.0) / 54.0, 0.0, 1.0)
    use_r = edge & (m > 10.0)
    alpha[use_r] = np.where(a_ramp[use_r] <= 0.05, 0.0, a_ramp[use_r])

    semi = (alpha > 0.0) & (alpha < 0.995)
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.25)
    r[semi] = np.clip((r[semi] - inv * 255.0) / denom, 0.0, 255.0)
    g[semi] = np.clip(g[semi] / denom, 0.0, 255.0)
    b[semi] = np.clip((b[semi] - inv * 255.0) / denom, 0.0, 255.0)

    rgb = np.dstack([r, g, b])
    core = ndimage.minimum_filter((alpha > 0.98) & (m < 8.0), size=3)
    if np.any(core):
        _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
        rim = (alpha > 0.0) & (~core) & (dist <= 7.0)
        rgb[rim] = rgb[iy[rim], ix[rim]]

    r2, g2, b2 = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m2 = np.minimum(r2, b2) - g2
    cool_bounce = (alpha > 0.0) & (dist <= 22.0) & (m2 > 5.0) & ((r2 - b2) < 26.0)
    if np.any(cool_bounce):
        excess = m2[cool_bounce] - 3.0
        r2[cool_bounce] = np.clip(r2[cool_bounce] - 0.72 * excess, 0.0, 255.0)
        b2[cool_bounce] = np.clip(b2[cool_bounce] - 0.78 * excess, 0.0, 255.0)
        g2[cool_bounce] = np.clip(g2[cool_bounce] + 0.18 * excess, 0.0, 255.0)

    alpha = np.clip((alpha - 0.06) / 0.94, 0.0, 1.0)
    return np.dstack([
        np.clip(np.round(r2), 0, 255).astype(np.uint8),
        np.clip(np.round(g2), 0, 255).astype(np.uint8),
        np.clip(np.round(b2), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])


def crop_normalize_studio(rgba: np.ndarray, box: tuple[int, int, int, int], mirror: bool = False) -> np.ndarray:
    cw, ch, top_y, ground_y = 480, 640, 44, 596
    x0, y0, x1, y1 = box
    sub = rgba[y0:y1, x0:x1].copy()
    if mirror:
        sub = sub[:, ::-1, :].copy()

    mask = sub[..., 3] > 28
    lbl, num = ndimage.label(mask)
    if num > 1:
        sizes = ndimage.sum(mask, lbl, range(1, num + 1))
        keep = ndimage.binary_dilation(lbl == (1 + int(np.argmax(sizes))), iterations=2)
        sub[~keep] = 0
        mask = sub[..., 3] > 28

    ys, xs = np.nonzero(mask)
    sub = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h0, w0 = sub.shape[:2]
    tgt_h = ground_y - top_y
    sc = tgt_h / float(h0)
    nw = max(1, int(round(w0 * sc)))
    im = Image.fromarray(sub, "RGBA").resize((nw, tgt_h), Image.Resampling.LANCZOS)

    a_np = np.asarray(im)[..., 3].astype(np.float32)
    torso_a = a_np[int(tgt_h * 0.18):int(tgt_h * 0.56), :]
    cx_local = float((torso_a.sum(axis=0) * np.arange(nw)).sum() / max(1.0, torso_a.sum()))
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ox = int(round(cw / 2.0 - cx_local))
    canvas.alpha_composite(im, (ox, top_y))
    return np.asarray(canvas, dtype=np.uint8)


def inpaint_fabric_region(rgba: np.ndarray, hole_mask: np.ndarray) -> np.ndarray:
    out = rgba.astype(np.float32).copy()
    rgb = out[..., :3]
    a = out[..., 3] / 255.0
    hole = ndimage.binary_dilation(hole_mask, iterations=3) & (a > 0.25)
    if not np.any(hole):
        return rgba

    rg = np.abs(rgb[..., 0] - rgb[..., 1]) + np.abs(rgb[..., 1] - rgb[..., 2])
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    known = (~hole) & (a > 0.88) & (lum < 110.0) & (rg < 42.0)
    if np.sum(known) < 50:
        known = (~hole) & (a > 0.85)

    seed_rgb = np.where(known[..., None], rgb, 0.0)
    seed_w = known.astype(np.float32)
    filled = np.zeros_like(rgb)
    conf = np.zeros_like(seed_w)
    for sigma in (48.0, 24.0, 12.0, 5.0):
        ks = int(sigma * 4) | 1
        ns = cv2.GaussianBlur(seed_rgb, (ks, ks), sigma)
        ds = cv2.GaussianBlur(seed_w, (ks, ks), sigma)
        layer = np.where((ds > 1e-5)[..., None], ns / np.maximum(ds[..., None], 1e-5), 0.0)
        wt = np.clip(ds * 12.0, 0.0, 1.0)
        filled = np.where(conf[..., None] == 0, layer, filled * (1.0 - wt[..., None]) + layer * wt[..., None])
        conf = np.maximum(conf, wt)

    bw = cv2.GaussianBlur(hole.astype(np.float32), (9, 9), 2.2) * (a > 0.10)
    out[..., :3] = np.clip(rgb * (1.0 - bw[..., None]) + filled * bw[..., None], 0.0, 255.0)
    return out.astype(np.uint8)


def extend_top_upward(rgba: np.ndarray, y_top: int, up_px: int = 30) -> np.ndarray:
    out = rgba.copy()
    H, W = out.shape[:2]
    for x in range(W):
        col = out[y_top:min(H, y_top + 60), x, 3]
        nz = np.nonzero(col > 180)[0]
        if len(nz):
            ty = y_top + int(nz[0])
            sample = out[min(H - 1, ty + 3), x].copy()
            for yy in range(max(0, ty - up_px), ty):
                if out[yy, x, 3] == 0:
                    out[yy, x] = sample
    return out


def shade_rgba(rgba: np.ndarray, factor: float) -> np.ndarray:
    if abs(factor - 1.0) < 1e-3:
        return rgba.copy()
    out = rgba.copy()
    out[..., :3] = np.clip(np.round(out[..., :3].astype(np.float32) * factor), 0, 255).astype(np.uint8)
    return out


def alpha_over(dst: np.ndarray, src: np.ndarray) -> np.ndarray:
    sa = src[..., 3:4].astype(np.float32) / 255.0
    da = dst[..., 3:4].astype(np.float32) / 255.0
    oa = sa + da * (1.0 - sa)
    s_rgb = src[..., :3].astype(np.float32)
    d_rgb = dst[..., :3].astype(np.float32)
    o_rgb = np.where(oa > 1e-5, (s_rgb * sa + d_rgb * da * (1.0 - sa)) / np.maximum(oa, 1e-5), 0.0)
    return np.dstack([
        np.clip(np.round(o_rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(oa[..., 0] * 255.0), 0, 255).astype(np.uint8),
    ])


def _rot2d(deg: float) -> np.ndarray:
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    return np.array([[c, -s], [s, c]], dtype=np.float32)


def _smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / max(1e-5, e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def warp_rigid_rgba(
    rgba: np.ndarray,
    pivot: tuple[float, float],
    angle_deg: float = 0.0,
    dx: float = 0.0,
    dy: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
) -> np.ndarray:
    H, W = rgba.shape[:2]
    px, py = pivot
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    M = np.array([
        [c * sx, -s * sy, px + dx - (c * sx * px - s * sy * py)],
        [s * sx,  c * sy, py + dy - (s * sx * px + c * sy * py)],
    ], dtype=np.float32)
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)
    pm_w = cv2.warpAffine(pm, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wa = pm_w[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, pm_w[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(pm_w[..., 3]), 0, 255).astype(np.uint8),
    ])


def warp_limb_3bone(
    rgba: np.ndarray,
    j_root: tuple[float, float],
    j_mid: tuple[float, float],
    j_end: tuple[float, float],
    ang_upper: float = 0.0,
    ang_lower: float = 0.0,
    ang_tip: float = 0.0,
    sy_upper: float = 1.0,
    sy_lower: float = 1.0,
    scale_all: float = 1.0,
    dx: float = 0.0,
    dy: float = 0.0,
    band_mid: float = 20.0,
    band_end: float = 12.0,
) -> np.ndarray:
    if not np.any(rgba[..., 3] > 4):
        return rgba.copy()

    H, W = rgba.shape[:2]
    rx, ry = j_root
    mx, my = j_mid
    ex, ey = j_end

    R1 = _rot2d(ang_upper) * scale_all
    R2 = _rot2d(ang_upper + ang_lower) * scale_all
    R3 = _rot2d(ang_upper + ang_lower + ang_tip) * scale_all

    root_p = np.array([rx + dx, ry + dy], dtype=np.float32)
    mid_p = root_p + R1 @ np.array([mx - rx, (my - ry) * sy_upper], dtype=np.float32)
    end_p = mid_p + R2 @ np.array([ex - mx, (ey - my) * sy_lower], dtype=np.float32)

    ys_nz, xs_nz = np.nonzero(rgba[..., 3] > 2)
    x0 = max(0, int(xs_nz.min()) - 14)
    x1 = min(W - 1, int(xs_nz.max()) + 14)
    y0 = max(0, int(ys_nz.min()) - 14)
    y1 = min(H - 1, int(ys_nz.max()) + 14)

    nx, ny = 10, 22
    gx = np.linspace(x0, x1, nx, dtype=np.float32)
    gy = np.linspace(y0, y1, ny, dtype=np.float32)
    GX, GY = np.meshgrid(gx, gy)
    pts = np.stack([GX, GY], axis=-1)

    d_root = np.stack([pts[..., 0] - rx, (pts[..., 1] - ry) * sy_upper], axis=-1)
    p1 = root_p + np.einsum("ij,...j->...i", R1, d_root)
    d_mid = np.stack([pts[..., 0] - mx, (pts[..., 1] - my) * sy_lower], axis=-1)
    p2 = mid_p + np.einsum("ij,...j->...i", R2, d_mid)
    d_end = np.stack([pts[..., 0] - ex, pts[..., 1] - ey], axis=-1)
    p3 = end_p + np.einsum("ij,...j->...i", R3, d_end)

    w12 = _smoothstep(my - band_mid, my + band_mid, pts[..., 1])[..., None]
    w23 = _smoothstep(ey - band_end, ey + band_end, pts[..., 1])[..., None]
    dst_pts = p1 * (1.0 - w12) + p2 * w12
    dst_pts = dst_pts * (1.0 - w23) + p3 * w23

    map_x = np.full((H, W), -1.0, dtype=np.float32)
    map_y = np.full((H, W), -1.0, dtype=np.float32)

    for iy in range(ny - 1):
        for ix in range(nx - 1):
            s_quad = np.array([
                [GX[iy, ix], GY[iy, ix]],
                [GX[iy, ix + 1], GY[iy, ix + 1]],
                [GX[iy + 1, ix + 1], GY[iy + 1, ix + 1]],
                [GX[iy + 1, ix], GY[iy + 1, ix]],
            ], dtype=np.float32)
            sx0 = max(0, int(s_quad[:, 0].min()) - 1)
            sx1 = min(W, int(s_quad[:, 0].max()) + 2)
            sy0 = max(0, int(s_quad[:, 1].min()) - 1)
            sy1 = min(H, int(s_quad[:, 1].max()) + 2)
            if not np.any(rgba[sy0:sy1, sx0:sx1, 3] > 1):
                continue

            d_quad = np.array([
                dst_pts[iy, ix],
                dst_pts[iy, ix + 1],
                dst_pts[iy + 1, ix + 1],
                dst_pts[iy + 1, ix],
            ], dtype=np.float32)

            for tri_idx in ((0, 1, 2), (0, 2, 3)):
                st = s_quad[list(tri_idx)]
                dt = d_quad[list(tri_idx)]
                bx0 = max(0, int(math.floor(dt[:, 0].min())))
                bx1 = min(W - 1, int(math.ceil(dt[:, 0].max())))
                by0 = max(0, int(math.floor(dt[:, 1].min())))
                by1 = min(H - 1, int(math.ceil(dt[:, 1].max())))
                if bx1 < bx0 or by1 < by0:
                    continue
                den = (dt[2, 0] - dt[0, 0]) * (dt[1, 1] - dt[0, 1]) - (dt[1, 0] - dt[0, 0]) * (dt[2, 1] - dt[0, 1])
                if abs(den) < 1e-2:
                    continue
                M_inv = cv2.getAffineTransform(dt, st)
                px_g, py_g = np.meshgrid(
                    np.arange(bx0, bx1 + 1, dtype=np.float32),
                    np.arange(by0, by1 + 1, dtype=np.float32),
                )
                v0 = dt[2] - dt[0]
                v1 = dt[1] - dt[0]
                v2x = px_g - dt[0, 0]
                v2y = py_g - dt[0, 1]
                inv_d = 1.0 / den
                u = (v2x * v1[1] - v1[0] * v2y) * inv_d
                v = (v0[0] * v2y - v2x * v0[1]) * inv_d
                inside = (u >= -1e-4) & (v >= -1e-4) & (u + v <= 1.0 + 2e-4)
                if not np.any(inside):
                    continue
                map_x[by0:by1 + 1, bx0:bx1 + 1][inside] = (M_inv[0, 0] * px_g + M_inv[0, 1] * py_g + M_inv[0, 2])[inside]
                map_y[by0:by1 + 1, bx0:bx1 + 1][inside] = (M_inv[1, 0] * px_g + M_inv[1, 1] * py_g + M_inv[1, 2])[inside]

    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm_src = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)
    pm_dst = cv2.remap(pm_src, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wa = pm_dst[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, pm_dst[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(pm_dst[..., 3]), 0, 255).astype(np.uint8),
    ])


# ---------------------------------------------------------------------------
# 2. Photographic Black Jeans + Shoes Multi-Angle Rig (Zero Hand Stub!)
# ---------------------------------------------------------------------------

def _hand_inpaint_mask(base_rgba: np.ndarray, sh: tuple[float, float], el: tuple[float, float], wr: tuple[float, float], r_sh: float, r_wr: float) -> np.ndarray:
    H, W = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    d_upper = seg_dist_grid(xg, yg, sh[0], sh[1], el[0], el[1])
    d_lower = seg_dist_grid(xg, yg, el[0], el[1], wr[0], wr[1])
    d_hand = np.hypot(xg - wr[0], (yg - (wr[1] + 10.0)) / 1.35)
    t_y = np.clip((yg - sh[1]) / max(1.0, wr[1] - sh[1]), 0.0, 1.0)
    rad = r_sh * (1.0 - t_y) + r_wr * t_y
    d_min = np.minimum(np.minimum(d_upper, d_lower), d_hand * 0.95)
    return (d_min <= rad + 3.0) & (yg >= el[1] + 24.0) & (yg <= wr[1] + 36.0)


def build_black_jeans_legs() -> dict[int, np.ndarray]:
    """Loads 0°, 45°, 90°, 135°, 180° studio trousers + shoes, removes ALL resting hand/thumb
    pixels near the hips, and tone-grades the trousers to Rob's deep black-charcoal jeans."""
    im_front = Image.open(os.path.join(ROOT, "source", "mm_tools", "ref", "paul_dennis", "paul_studio_front.jpg"))
    im_turn = Image.open(os.path.join(ROOT, "source", "mm_tools", "ref", "paul_dennis", "paul_studio_turn.jpg"))

    kf = key_magenta_studio(im_front)
    kt = key_magenta_studio(im_turn)

    views_raw = {
        0: crop_normalize_studio(kf, (260, 60, 640, 1180), mirror=False),
        45: crop_normalize_studio(kt, (20, 30, 308, 970), mirror=True),
        90: crop_normalize_studio(kt, (318, 30, 506, 970), mirror=True),
        135: crop_normalize_studio(kt, (508, 30, 712, 970), mirror=False),
        180: crop_normalize_studio(kt, (718, 30, 1008, 970), mirror=False),
    }

    graded = {}
    for deg, rgba in views_raw.items():
        H, W = rgba.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

        # Remove any warm skin pixels (resting thumbs/fingers at y=320..410) BEFORE grading!
        rf0 = rgba[..., :3].astype(np.float32)
        skin_px = (yg >= 320) & (yg <= 410) & ((rf0[..., 0] - rf0[..., 2]) > 15.0) & (rf0[..., 0] > 68.0)
        clean_src = inpaint_fabric_region(rgba, skin_px)

        out = clean_src.astype(np.float32)
        w_pants = 1.0 - np.clip((yg - 548.0) / 14.0, 0.0, 1.0)
        rgb = out[..., :3]
        lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
        dark_lum = 11.5 + 0.44 * np.maximum(0.0, lum - 14.0) + 0.0018 * np.maximum(0.0, lum - 50.0) ** 2
        scale = np.where(lum > 2.0, dark_lum / np.maximum(lum, 1.0), 0.5)
        pants_rgb = np.zeros_like(rgb)
        pants_rgb[..., 0] = rgb[..., 0] * scale * 0.96
        pants_rgb[..., 1] = rgb[..., 1] * scale * 0.98
        pants_rgb[..., 2] = rgb[..., 2] * scale * 1.05
        out[..., :3] = np.clip(rgb * (1.0 - w_pants[..., None]) + pants_rgb * w_pants[..., None], 0.0, 255.0)
        graded[deg] = np.round(out).astype(np.uint8)

    return graded


def pose_dance_legs(
    graded_views: dict[int, np.ndarray],
    view_deg: int,
    phase_01: float,
    hero_kick: bool = False,
) -> tuple[np.ndarray, float, float]:
    """Synthesizes full-length black jeans + shoes dancing/kicking/running in 480x640 studio space.
    Returns (legs_rgba, sway_dx, bob_dy)."""
    base_rgba = graded_views[view_deg]
    H, W = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]
    ang = 2.0 * math.pi * phase_01

    if view_deg in (0, 180):
        is_back = (view_deg == 180)
        # Start extraction at y=370 and exclude resting hands/fingertips all the way down to y=418!
        x_cut_l = 192.0
        x_cut_r = 288.0
        arm_m = ((xg < x_cut_l) | (xg > x_cut_r)) & (yg >= 164) & (yg <= 418)
        leg_zone = (yg >= 370) & (~arm_m) & (base_rgba[..., 3] > 0)
        leg_l_raw = np.where((leg_zone & (xg < 240))[..., None], base_rgba, 0)
        leg_r_raw = np.where((leg_zone & (xg >= 240))[..., None], base_rgba, 0)

        leg_l = extend_top_upward(leg_l_raw, 370, up_px=42)
        leg_r = extend_top_upward(leg_r_raw, 370, up_px=42)

        # Compact elliptical pelvis bridge strictly narrower than Rob's untucked shirt!
        pelvis = np.zeros_like(base_rgba)
        pr2 = ((xg.astype(np.float32) - 240.0) / 26.0) ** 2 + ((yg.astype(np.float32) - 354.0) / 18.0) ** 2
        pel_a = np.clip((1.0 - np.sqrt(pr2)) * 4.0, 0.0, 1.0)
        pelvis[..., 0] = 20
        pelvis[..., 1] = 21
        pelvis[..., 2] = 24
        pelvis[..., 3] = np.round(pel_a * 255.0).astype(np.uint8)

        if hero_kick:
            # Exuberant 2-beat MR. D.I.Y. happy-feet dance!
            # Beat 1 (phase 0..0.5): Left leg pops high & kicks out while fists pump!
            # Beat 2 (phase 0.5..1.0): Right leg pops high & kicks out while fists pump!
            bounce = -7.5 * abs(math.sin(ang)) + 4.0 * math.cos(2.0 * ang)
            sway_dx = 9.0 * math.sin(ang)
            s_l = math.sin(ang)
            s_r = -math.sin(ang)
            kick_gain = 1.0
        else:
            bounce = -4.5 * abs(math.sin(ang)) + 2.5 * math.cos(2.0 * ang)
            sway_dx = 5.5 * math.sin(ang)
            s_l = math.cos(ang - 0.3)
            s_r = -s_l
            kick_gain = 0.72

        def dance_leg_fb(leg_im: np.ndarray, side_sign: float, s_val: float) -> np.ndarray:
            hx = 213.0 if side_sign < 0 else 267.0
            kx = 210.0 if side_sign < 0 else 270.0
            ax = 204.0 if side_sign < 0 else 276.0
            if s_val > 0.0:
                lift = (s_val ** 0.82) * kick_gain
                if not is_back:
                    return warp_limb_3bone(
                        leg_im, (hx, 344.0), (kx, 464.0), (ax, 576.0),
                        ang_upper=side_sign * 19.5 * lift,     # lively outward knee flare!
                        ang_lower=-side_sign * 32.0 * lift,    # playful happy-feet shin kick!
                        ang_tip=side_sign * 13.0 * lift,       # toe pop!
                        sy_upper=1.0 - 0.27 * lift,
                        sy_lower=1.0 - 0.14 * lift,
                        scale_all=1.0 + 0.045 * lift,
                        dx=sway_dx,
                        dy=bounce - 24.0 * lift,
                    )
                else:
                    return warp_limb_3bone(
                        shade_rgba(leg_im, 1.0 - 0.08 * lift),
                        (hx, 344.0), (kx, 464.0), (ax, 576.0),
                        ang_upper=side_sign * 12.0 * lift,
                        ang_lower=-side_sign * 20.0 * lift,
                        sy_upper=1.0 - 0.14 * lift,
                        sy_lower=1.0 - 0.32 * lift,
                        scale_all=1.0 - 0.03 * lift,
                        dx=sway_dx,
                        dy=bounce - 18.0 * lift,
                    )
            else:
                p = ((-s_val) ** 0.88) * kick_gain
                return warp_limb_3bone(
                    leg_im, (hx, 344.0), (kx, 464.0), (ax, 576.0),
                    ang_upper=-side_sign * 6.5 * p,
                    ang_lower=side_sign * 11.0 * p,
                    ang_tip=-side_sign * 5.0 * p,
                    sy_upper=1.0 - 0.05 * p,
                    sy_lower=1.0 - 0.03 * p,
                    dx=sway_dx,
                    dy=max(-2.5, bounce * 0.45),
                )

        pel_p = warp_rigid_rgba(pelvis, (240.0, 350.0), angle_deg=-3.0 * math.sin(ang), dx=sway_dx, dy=bounce)
        ll_p = dance_leg_fb(leg_l, -1.0, s_l)
        lr_p = dance_leg_fb(leg_r, +1.0, s_r)
        out = pel_p
        if (s_l >= s_r) != is_back:
            out = alpha_over(alpha_over(out, lr_p), ll_p)
        else:
            out = alpha_over(alpha_over(out, ll_p), lr_p)
        return out, sway_dx, bounce

        # 45°, 90°, 135° views: also start trouser extraction cleanly at y=368 below jacket hem!
    if view_deg == 90:
        hh = _hand_inpaint_mask(base_rgba, (244.0, 180.0), (249.0, 266.0), (241.0, 344.0), 18.5, 14.5)
        body_clean = inpaint_fabric_region(base_rgba, hh)
        near_leg = np.zeros_like(base_rgba)
        near_leg[yg >= 368] = body_clean[yg >= 368]
        near_leg = extend_top_upward(near_leg, 368, up_px=52)
        far_leg = shade_rgba(near_leg, 0.80)
        hip_pt, knee_pt, ankle_pt = (242.0, 342.0), (242.0, 464.0), (244.0, 574.0)
        far_dx, stride_scale = -6.0, 0.94
    elif view_deg == 45:
        far_arm_m = (xg < 196) & (yg >= 170) & (yg <= 382) & (base_rgba[..., 3] > 0)
        hh = _hand_inpaint_mask(base_rgba, (278.0, 178.0), (288.0, 266.0), (284.0, 344.0), 20.0, 15.0)
        body_clean = inpaint_fabric_region(base_rgba, hh)
        near_hand_outer = (xg > 274) & (yg >= 330) & (yg <= 386)
        leg_zone = (yg >= 368) & (~far_arm_m) & (~near_hand_outer) & (body_clean[..., 3] > 0)
        near_raw = np.where((leg_zone & (xg >= 235))[..., None], body_clean, 0)
        seam_band = (yg >= 368) & (yg <= 425) & (xg >= 235) & (xg <= 243)
        if np.any(seam_band):
            w_seam = np.clip((xg.astype(np.float32) - 235.0) / 7.0, 0.0, 1.0)
            near_raw[seam_band, 3] = np.round(near_raw[seam_band, 3].astype(np.float32) * w_seam[seam_band]).astype(np.uint8)
        near_leg = extend_top_upward(near_raw, 368, up_px=52)
        far_leg = shade_rgba(warp_rigid_rgba(near_leg, (254.0, 342.0), dx=-28.0, dy=-2.0), 0.84)
        hip_pt, knee_pt, ankle_pt = (254.0, 342.0), (255.0, 464.0), (256.0, 574.0)
        far_dx, stride_scale = -28.0, 0.84
    else:  # 135
        hh = _hand_inpaint_mask(base_rgba, (204.0, 180.0), (198.0, 266.0), (194.0, 344.0), 17.0, 13.5)
        body_clean = inpaint_fabric_region(base_rgba, hh)
        near_leg = np.zeros_like(base_rgba)
        near_leg[yg >= 368] = body_clean[yg >= 368]
        near_leg = extend_top_upward(near_leg, 368, up_px=52)
        far_leg = shade_rgba(near_leg, 0.80)
        hip_pt, knee_pt, ankle_pt = (246.0, 342.0), (248.0, 464.0), (250.0, 574.0)
        far_dx, stride_scale = -8.0, 0.84

    f_pos = (phase_01 * 8.0) % 8.0
    i0 = int(math.floor(f_pos)) % 8
    i1 = (i0 + 1) % 8
    frac = f_pos - math.floor(f_pos)
    kf_near = tuple(RUN_8_PROFILE[i0][j] * (1.0 - frac) + RUN_8_PROFILE[i1][j] * frac for j in range(5))

    f_far = (f_pos + 4.0) % 8.0
    j0 = int(math.floor(f_far)) % 8
    j1 = (j0 + 1) % 8
    jfrac = f_far - math.floor(f_far)
    kf_far = tuple(RUN_8_PROFILE[j0][j] * (1.0 - jfrac) + RUN_8_PROFILE[j1][j] * jfrac for j in range(5))

    bob_dy = kf_near[4]
    far_hip = (hip_pt[0] + far_dx, hip_pt[1])
    far_knee = (knee_pt[0] + far_dx, knee_pt[1])
    far_ank = (ankle_pt[0] + far_dx, ankle_pt[1])

    pelvis = np.zeros_like(base_rgba)
    cx_p = 0.5 * (hip_pt[0] + far_hip[0])
    rx_p = max(18.0, 0.5 * abs(far_dx) + 16.0)
    pr2 = ((xg.astype(np.float32) - cx_p) / rx_p) ** 2 + ((yg.astype(np.float32) - 354.0) / 18.0) ** 2
    pel_a = np.clip((1.0 - np.sqrt(pr2)) * 4.0, 0.0, 1.0)
    pelvis[..., :3] = [20, 21, 24]
    pelvis[..., 3] = np.round(pel_a * 255.0).astype(np.uint8)
    pel_p = warp_rigid_rgba(pelvis, hip_pt, dy=bob_dy)

    near_p = warp_limb_3bone(
        near_leg, hip_pt, knee_pt, ankle_pt,
        ang_upper=kf_near[0] * stride_scale,
        ang_lower=kf_near[1] * stride_scale,
        ang_tip=kf_near[2] * stride_scale,
        sy_upper=kf_near[3],
        dy=bob_dy,
    )
    far_p = warp_limb_3bone(
        far_leg, far_hip, far_knee, far_ank,
        ang_upper=kf_far[0] * stride_scale,
        ang_lower=kf_far[1] * stride_scale,
        ang_tip=kf_far[2] * stride_scale,
        sy_upper=kf_far[3],
        dy=bob_dy,
    )
    out = alpha_over(alpha_over(pel_p, far_p), near_p)
    return out, 0.0, bob_dy


# ---------------------------------------------------------------------------
# 3. Clean-Plate + MaskRCNN v4 Video Upper-Body Matting & 180° Back Synthesis
# ---------------------------------------------------------------------------

class RobVideoMatter:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = torchvision.models.detection.maskrcnn_resnet50_fpn_v2(weights="DEFAULT").to(self.device).eval()
        cache = np.load(os.path.join(SCRATCH, "video_seg_cache.npz"))
        self.homographies = cache["homographies"]
        self.clean_bg = cv2.cvtColor(cv2.imread(os.path.join(SCRATCH, "clean_bg_patched.png")), cv2.COLOR_BGR2RGB).astype(np.float32)

        cap = cv2.VideoCapture(VID_PATH)
        self.frames_bgr = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            self.frames_bgr.append(f)
        cap.release()
        self._cache: dict[int, tuple[np.ndarray, tuple[float, float, float]]] = {}

    def matte_upper_body(self, idx: int, neutralize_bag_text: bool = False) -> tuple[np.ndarray, tuple[float, float, float]]:
        key = (idx, neutralize_bag_text)
        if key in self._cache:
            return self._cache[key]

        bgr = self.frames_bgr[idx]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rf = rgb.astype(np.float32)
        H, W = rgb.shape[:2]

        with torch.no_grad():
            t = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255.0).unsqueeze(0).to(self.device)
            pred = self.model(t)[0]
            keep = (pred["labels"] == 1) & (pred["scores"] > 0.65)
            pmask = pred["masks"][keep, 0].max(dim=0).values.cpu().numpy() if keep.any() else np.zeros((H, W), np.float32)

        H_inv = np.linalg.inv(self.homographies[idx])
        bg_warp = cv2.warpPerspective(self.clean_bg, H_inv, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        bg_diff = np.max(np.abs(rf - bg_warp), axis=-1)

        r, g, b = rf[..., 0], rf[..., 1], rf[..., 2]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        br, _, bb = bg_warp[..., 0], bg_warp[..., 1], bg_warp[..., 2]

        is_sign_ry = ((r > 140) & (b < 82) & ((r - b) > 80)) & ((br > 125) & (bb < 98))
        span = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
        is_slat = (span < 25.0) & (lum > 64.0) & ((r - b) < 23.5)

        gc_mask = np.full((H, W), cv2.GC_BGD, dtype=np.uint8)
        prob_fg = (pmask > 0.18) & (~((pmask < 0.76) & (is_sign_ry | is_slat)))
        sure_fg = (pmask > 0.88) & ((bg_diff > 20.0) | (lum < 50.0)) & (~is_slat)
        sure_bg = (pmask < 0.04)
        gc_mask[~sure_bg] = cv2.GC_PR_BGD
        gc_mask[prob_fg] = cv2.GC_PR_FGD
        gc_mask[sure_fg] = cv2.GC_FGD

        ys_p, xs_p = np.nonzero(pmask > 0.1)
        x0, x1 = max(0, xs_p.min() - 40), min(W, xs_p.max() + 40)
        y0, y1 = max(0, ys_p.min() - 40), min(H, ys_p.max() + 20)
        bgd_m = np.zeros((1, 65), np.float64)
        fgd_m = np.zeros((1, 65), np.float64)
        sub_gc = gc_mask[y0:y1, x0:x1].copy()
        cv2.grabCut(bgr[y0:y1, x0:x1], sub_gc, None, bgd_m, fgd_m, 2, cv2.GC_INIT_WITH_MASK)
        raw_fg = np.zeros((H, W), dtype=bool)
        raw_fg[y0:y1, x0:x1] = (sub_gc == cv2.GC_FGD) | (sub_gc == cv2.GC_PR_FGD)

        yg, xg = np.mgrid[0:H, 0:W]
        dist_raw = ndimage.distance_transform_edt(raw_fg)

        # v5 Precision Cleanout:
        # 1. Enclosed background pockets ONLY below head/ears (yg >= 398) so face/temples/eyes NEVER get pinholes!
        warm_skin = ((r - b) > 25.0) & (r > 92.0) & (bg_diff > 15.0)
        yellow_smiley = (r > 125.0) & (g > 96.0) & (b < 75.0) & ((r + g - 2.0 * b) > 95.0)
        bg_pocket = (yg >= 398) & (bg_diff < 25.0) & (lum > 56.0) & (~warm_skin) & (~yellow_smiley)

        # 2. Neutral beige/grey vertical slat strips along forearms/chest (below face yg >= 405, dist <= 26px)
        slat_strip = (yg >= 405) & (dist_raw <= 26.0) & (lum > 62.0) & ((r - b) < 23.5) & (~yellow_smiley)

        # 3. Storefront red/orange sign rim slivers on outer arm boundary (yg >= 395, dist <= 20px)
        orange_sign_rim = (yg >= 395) & (dist_raw <= 20.0) & (r > 135.0) & ((r - g) > 42.0) & (b < 88.0)

        fg = raw_fg & (~bg_pocket) & (~slat_strip) & (~orange_sign_rim)
        fg = ndimage.binary_opening(fg, structure=np.ones((3, 3), bool))
        lbl, num = ndimage.label(fg)
        if num > 0:
            sizes = ndimage.sum(fg, lbl, range(1, num + 1))
            fg = (lbl == (1 + int(np.argmax(sizes))))

        # Fill tiny interior specular pinholes (< 150px) while keeping real arm-body air gaps open!
        inv_fg = ~fg
        hlbl, hnum = ndimage.label(inv_fg)
        if hnum > 1:
            hsizes = ndimage.sum(inv_fg, hlbl, range(1, hnum + 1))
            for hi, hs in enumerate(hsizes, start=1):
                if hs < 150:
                    fg[hlbl == hi] = True

        alpha = cv2.GaussianBlur(fg.astype(np.float32), (5, 5), 1.0)
        alpha = np.clip((alpha - 0.12) / 0.82, 0.0, 1.0)

        dist_in = ndimage.distance_transform_edt(alpha > 0.92)
        core = (dist_in >= 4.5) & (~is_sign_ry) & (~slat_strip)
        out_rgb = rf.copy()
        if np.any(core):
            _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
            rim = (alpha > 0.0) & (dist_in < 5.0)
            out_rgb[rim] = rf[iy[rim], ix[rim]]

        if neutralize_bag_text:
            # Gently inpaint tiny grey 'arctic hunter' wordmark on dark bag/strap when mirroring
            dark_bag = (alpha > 0.9) & (yg >= 480) & (yg <= 920) & (lum < 58.0) & (span < 16.0)
            near_bag = ndimage.binary_dilation(dark_bag, iterations=6)
            bag_txt = near_bag & (lum >= 58.0) & (lum <= 165.0) & (span < 22.0) & (~yellow_smiley)
            if np.any(bag_txt):
                m_u8 = (ndimage.binary_dilation(bag_txt, iterations=2)).astype(np.uint8) * 255
                inp = cv2.inpaint(np.clip(out_rgb, 0, 255).astype(np.uint8), m_u8, 4, cv2.INPAINT_TELEA)
                out_rgb = inp.astype(np.float32)

        shirt_yellow = fg & (yg >= 700) & (yg <= 1045) & yellow_smiley
        if np.sum(shirt_yellow) > 80:
            hem_y = float(np.percentile(yg[shirt_yellow], 97.5)) + 16.0
        else:
            hem_y = 995.0
        hem_y = float(np.clip(hem_y, 955.0, 1020.0))

        hip_band = fg & (yg >= int(hem_y - 70)) & (yg <= int(hem_y))
        hxs = xg[hip_band]
        hip_cx = float(0.5 * (np.percentile(hxs, 4) + np.percentile(hxs, 96)))
        hip_w = float(np.percentile(hxs, 97) - np.percentile(hxs, 3))

        # Smoothly taper & feather clipped video pants stub below Rob's real untucked shirt hem
        below = yg > hem_y
        v_fade = 1.0 - np.clip((yg.astype(np.float32) - hem_y) / 32.0, 0.0, 1.0)
        half_stub = max(36.0, 0.36 * hip_w)
        h_taper = 1.0 - np.clip((np.abs(xg.astype(np.float32) - hip_cx) - half_stub) / 14.0, 0.0, 1.0)
        alpha = alpha * np.where(below, v_fade * h_taper, 1.0)

        rgba = np.dstack([
            np.clip(np.round(out_rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
        ])
        res = (rgba, (hip_cx, hem_y, hip_w))
        self._cache[key] = res
        return res

    def build_back_180_upper(self, pump_phase_01: float) -> tuple[np.ndarray, tuple[float, float, float]]:
        """Synthesizes a 100% photographic 180° dead-back upper body of Rob using:
        - Studio photographic 180° back-of-head hair, ears & neck graded to Rob's dark espresso hair,
        - Pure unoccluded 1:1 yellow-smiley black shirt fabric from Rob's real back in f=176,
        - Rob's real arctic hunter crossbody sling bag across his lower back."""
        if not hasattr(self, "_back180_base"):
            front_rgba, (fcx, fhem_y, fhw) = self.matte_upper_body(38, neutralize_bag_text=True)
            back_src, (bcx, _, _) = self.matte_upper_body(176, neutralize_bag_text=True)
            H, W = front_rgba.shape[:2]
            yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
            cx_i = int(round(fcx))

            # Clean broad-shouldered short-sleeve back torso silhouette (y = 408..fhem_y+32), zero arm holes!
            t_sh = np.clip((yg - 425.0) / 215.0, 0.0, 1.0)
            t_w = np.clip((yg - 640.0) / 360.0, 0.0, 1.0)
            half_w = np.where(yg < 412.0, 0.0, (195.0 + 68.0 * np.sin(math.pi * t_sh)) * (1.0 - 0.22 * t_w))
            # Rounded shoulder caps from y=412..475
            sh_cap = np.clip((yg - 412.0) / 52.0, 0.0, 1.0) ** 0.55
            half_w = half_w * np.where(yg < 464.0, 0.42 + 0.58 * sh_cap, 1.0)
            torso_sil = (yg >= 412.0) & (yg <= fhem_y + 32.0) & (np.abs(xg - fcx) <= half_w)
            a_torso = cv2.GaussianBlur(torso_sil.astype(np.float32), (7, 7), 1.6)
            a_torso = np.clip((a_torso - 0.12) / 0.80, 0.0, 1.0)
            below = yg > fhem_y
            v_fade = 1.0 - np.clip((yg - fhem_y) / 30.0, 0.0, 1.0)
            h_taper = 1.0 - np.clip((np.abs(xg - fcx) - max(36.0, 0.36 * fhw)) / 14.0, 0.0, 1.0)
            a_torso = a_torso * np.where(below, v_fade * h_taper, 1.0)

            # Pure unoccluded 1:1 yellow-smiley black shirt patch from f=176 (zero skin, zero red sign!)
            p0 = back_src[458:638, max(0, int(bcx - 86)):min(W, int(bcx + 76)), :3].astype(np.float32)
            # Make seamless 2x2 mirror-quilted tile with soft seam blend
            p_lr = np.hstack([p0, p0[:, ::-1, :]])
            p_quad = np.vstack([p_lr, p_lr[::-1, :, :]])
            tiled = np.tile(p_quad, (3, 3, 1))[:680, :580].copy()
            # Subtle 3D cylindrical back-of-shoulders shading
            tx0 = max(0, cx_i - 290)
            tx1 = min(W, tx0 + 580)
            canvas_rgb = np.zeros((H, W, 3), dtype=np.float32)
            canvas_rgb[400:1080, tx0:tx1] = tiled[:, :tx1 - tx0]
            cyl_shade = 1.04 - 0.22 * ((xg - fcx) / 245.0) ** 2
            canvas_rgb *= np.clip(cyl_shade, 0.76, 1.05)[..., None]

            torso_rgba = np.dstack([
                np.clip(np.round(canvas_rgb), 0, 255).astype(np.uint8),
                np.clip(np.round(a_torso * 255.0), 0, 255).astype(np.uint8),
            ])

            # Extract studio photographic 180° back-of-head + ears + neck from paul_studio_turn.jpg comp 4
            # and grade silver-grey hair to Rob's rich dark espresso-brown short hair!
            im_turn = Image.open(os.path.join(ROOT, "source", "mm_tools", "ref", "paul_dennis", "paul_studio_turn.jpg"))
            kt = key_magenta_studio(im_turn)
            st180 = crop_normalize_studio(kt, (718, 30, 1008, 970), mirror=False)
            head_crop = st180[36:162, 185:295].copy().astype(np.float32)
            hrgb = head_crop[..., :3]
            hlum = 0.299 * hrgb[..., 0] + 0.587 * hrgb[..., 1] + 0.114 * hrgb[..., 2]
            # Skin (ears & nape) has r - b > 18; silver hair has r - b <= 16!
            is_hair = ((hrgb[..., 0] - hrgb[..., 2]) < 17.0)
            w_hair = cv2.GaussianBlur(is_hair.astype(np.float32), (5, 5), 1.2)
            dark_h = 12.0 + 0.24 * np.maximum(0.0, hlum - 20.0)
            espresso = np.dstack([dark_h * 1.16, dark_h * 0.96, dark_h * 0.82])
            head_crop[..., :3] = np.clip(hrgb * (1.0 - w_hair[..., None]) + espresso * w_hair[..., None], 0.0, 255.0)
            # Feather neck bottom (rows 108..126) so it tucks cleanly into shirt collar at y=418
            hy_l = np.arange(head_crop.shape[0], dtype=np.float32)[:, None]
            head_crop[..., 3] *= np.clip((123.0 - hy_l) / 12.0, 0.0, 1.0)
            # Scale head 2.38x to match Rob's exact 1080p head scale (~260px tall, ~195px wide)
            head_u8 = np.round(head_crop).astype(np.uint8)
            hw_d, hh_d = int(round(head_u8.shape[1] * 2.38)), int(round(head_u8.shape[0] * 2.38))
            head_big = np.asarray(Image.fromarray(head_u8, "RGBA").resize((hw_d, hh_d), Image.Resampling.LANCZOS), dtype=np.uint8)
            head_layer = np.zeros_like(torso_rgba)
            hx0 = cx_i - hw_d // 2
            hy0 = 152  # lands nape right at y=448 behind collar y=412!
            head_layer[hy0:hy0 + hh_d, hx0:hx0 + hw_d] = head_big

            # Place head behind shirt collar (collar y=415..455 overlaps lower nape naturally!), with ears/hair above!
            base_180 = alpha_over(head_layer, torso_rgba)

            # Graft Rob's real 'arctic hunter' crossbody bag + diagonal strap across his back!
            bag_crop = back_src[645:885, max(0, int(bcx - 195)):min(W, int(bcx + 65))].copy()
            bh, bw_c = bag_crop.shape[:2]
            by_g, bx_g = np.mgrid[0:bh, 0:bw_c].astype(np.float32)
            bag_lum = 0.299 * bag_crop[..., 0] + 0.587 * bag_crop[..., 1] + 0.114 * bag_crop[..., 2]
            is_dark_pouch = (bag_crop[..., 3] > 200) & (bag_lum < 68.0)
            pouch_m = ndimage.binary_opening(is_dark_pouch, structure=np.ones((5, 5), bool))
            pouch_a = cv2.GaussianBlur(pouch_m.astype(np.float32), (9, 9), 2.2)
            edge_f = (
                np.clip(bx_g / 14.0, 0.0, 1.0)
                * np.clip((bw_c - 1.0 - bx_g) / 18.0, 0.0, 1.0)
                * np.clip(by_g / 16.0, 0.0, 1.0)
                * np.clip((bh - 1.0 - by_g) / 16.0, 0.0, 1.0)
            )
            bag_crop[..., 3] = np.round(bag_crop[..., 3].astype(np.float32) * pouch_a * edge_f).astype(np.uint8)
            bag_layer = np.zeros_like(base_180)
            bx_dst = int(round(fcx - bw_c * 0.50))
            by_dst = 668
            bag_layer[by_dst:by_dst + bh, bx_dst:bx_dst + bw_c] = bag_crop
            bag_layer[..., 3] = np.minimum(bag_layer[..., 3], torso_rgba[..., 3])

            # Diagonal black strap from left-upper shoulder (fcx-105, 430) down to bag (fcx+55, 735)
            strap_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(strap_im)
            sd.line([(int(fcx - 108), 426), (int(fcx + 48), 735)], fill=(22, 24, 28, 245), width=36)
            sd.line([(int(fcx - 104), 426), (int(fcx + 52), 735)], fill=(38, 41, 47, 150), width=8)
            strap_np = np.asarray(strap_im.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.uint8).copy()
            strap_np[..., 3] = np.minimum(strap_np[..., 3], torso_rgba[..., 3])

            base_180 = alpha_over(alpha_over(base_180, strap_np), bag_layer)
            self._back180_base = (base_180, (fcx, fhem_y, fhw))

        base_180, (fcx, fhem_y, fhw) = self._back180_base
        rock = 2.8 * math.sin(2.0 * math.pi * pump_phase_01)
        bob = -8.0 * abs(math.sin(math.pi * pump_phase_01))
        out = warp_rigid_rgba(base_180, (fcx, fhem_y), angle_deg=rock, dy=bob)
        return out, (fcx, fhem_y, fhw)


# ---------------------------------------------------------------------------
# 4. Full-Body Compositor + MR. D.I.Y. Emblem Halo & 3D Hardware Vortex
# ---------------------------------------------------------------------------

def composite_fullbody_character(
    upper_rgba_1080: np.ndarray,
    hip_info: tuple[float, float, float],
    legs_rgba_480: np.ndarray,
    leg_sway_dx: float,
    leg_bob_dy: float,
    mirror_upper: bool = False,
    mirror_legs: bool = False,
    upper_tilt_deg: float = 0.0,
) -> tuple[np.ndarray, tuple[float, float]]:
    """Composites Rob's real 1080p upper body + untucked smiley shirt OVER full-length
    animated black jeans + shoes on a 720x780 RGBA canvas.
    Returns (char_rgba, (fist_cx, fist_cy))."""
    CW, CH = CANVAS_W, CANVAS_H
    hip_cx, hem_y, _ = hip_info

    u_src = upper_rgba_1080
    if mirror_upper:
        u_src = u_src[:, ::-1, :].copy()
        hip_cx = (u_src.shape[1] - 1.0) - hip_cx

    sc_u = 0.352
    uh, uw = u_src.shape[:2]
    nuw, nuh = int(round(uw * sc_u)), int(round(uh * sc_u))
    u_np = np.asarray(Image.fromarray(u_src, "RGBA").resize((nuw, nuh), Image.Resampling.LANCZOS), dtype=np.uint8)

    l_src = legs_rgba_480[:, ::-1, :].copy() if mirror_legs else legs_rgba_480
    if mirror_legs:
        leg_sway_dx = -leg_sway_dx
    sc_l = 1.24
    lh, lw = l_src.shape[:2]
    nlw, nlh = int(round(lw * sc_l)), int(round(lh * sc_l))
    l_np = np.asarray(Image.fromarray(l_src, "RGBA").resize((nlw, nlh), Image.Resampling.LANCZOS), dtype=np.uint8)

    # Anchor Rob so crown ~ y=96, untucked shirt hem ~ y=392, shoe soles ~ y=697 (83px bottom margin & 96px top margin!)
    base_hem_y = 392.0
    target_cx = CW * 0.5 + leg_sway_dx * sc_l
    target_hem_y = base_hem_y + leg_bob_dy * sc_l

    canvas = np.zeros((CH, CW, 4), dtype=np.uint8)

    # 1. Blit full-length animated black jeans + shoes (studio hip 342 -> y=381, soles 596 -> y=696!)
    leg_ox = int(round(CW * 0.5 - 240.0 * sc_l))
    leg_oy = int(round((base_hem_y - 11.0) - 342.0 * sc_l))
    lx0, ly0 = max(0, leg_ox), max(0, leg_oy)
    lx1, ly1 = min(CW, leg_ox + nlw), min(CH, leg_oy + nlh)
    if lx1 > lx0 and ly1 > ly0:
        canvas[ly0:ly1, lx0:lx1] = l_np[ly0 - leg_oy:ly1 - leg_oy, lx0 - leg_ox:lx1 - leg_ox]

    # 2. Place Rob's upper body aligned on (target_cx, target_hem_y)
    upper_canvas = np.zeros((CH, CW, 4), dtype=np.uint8)
    u_ox = int(round(target_cx - hip_cx * sc_u))
    u_oy = int(round(target_hem_y - hem_y * sc_u))
    ux0, uy0 = max(0, u_ox), max(0, u_oy)
    ux1, uy1 = min(CW, u_ox + nuw), min(CH, u_oy + nuh)
    if ux1 > ux0 and uy1 > uy0:
        upper_canvas[uy0:uy1, ux0:ux1] = u_np[uy0 - u_oy:uy1 - u_oy, ux0 - u_ox:ux1 - u_ox]

    if abs(upper_tilt_deg) > 0.05:
        upper_canvas = warp_rigid_rgba(upper_canvas, (target_cx, target_hem_y), angle_deg=upper_tilt_deg)

    # 3. Soft shirt-hem drop shadow onto top of jeans
    u_alpha = upper_canvas[..., 3].astype(np.float32) / 255.0
    sh = np.zeros_like(u_alpha)
    sh[6:, :] = u_alpha[:-6, :]
    sh = cv2.GaussianBlur(sh, (15, 15), 4.5)
    yg_c = np.arange(CH, dtype=np.float32)[:, None]
    hem_zone = np.clip(1.0 - np.abs(yg_c - (target_hem_y + 8.0)) / 28.0, 0.0, 1.0)
    shadow_mult = 1.0 - 0.42 * sh * hem_zone * (canvas[..., 3] > 20)
    canvas[..., :3] = np.clip(np.round(canvas[..., :3].astype(np.float32) * shadow_mult[..., None]), 0, 255).astype(np.uint8)

    out = alpha_over(canvas, upper_canvas)

    # Automatically locate Rob's actual raised outer pumping fist (so sparkles sit OUTSIDE his fists, never on his face!)
    ur, ug_c, ub, ua = upper_canvas[..., 0], upper_canvas[..., 1], upper_canvas[..., 2], upper_canvas[..., 3]
    yy_u, xx_u = np.mgrid[0:CH, 0:CW]
    hand_cand = (
        (ua > 180)
        & (yy_u >= int(target_hem_y - 265))
        & (yy_u <= int(target_hem_y - 110))
        & ((ur.astype(np.int16) - ub.astype(np.int16)) > 26)
        & (ur > 95)
        & (np.abs(xx_u - target_cx) > 46)
    )
    if np.sum(hand_cand) > 60:
        hxs_c = xx_u[hand_cand].astype(np.float32)
        hys_c = yy_u[hand_cand].astype(np.float32)
        # Pick the side with more raised-hand pixels and offset 24px outward away from Rob's face!
        if np.sum(hxs_c < target_cx) >= np.sum(hxs_c > target_cx):
            fist_x = float(np.percentile(hxs_c[hxs_c < target_cx], 12)) - 22.0
            fist_y = float(np.percentile(hys_c[hxs_c < target_cx], 25))
        else:
            fist_x = float(np.percentile(hxs_c[hxs_c > target_cx], 88)) + 22.0
            fist_y = float(np.percentile(hys_c[hxs_c > target_cx], 25))
    else:
        fist_x, fist_y = -999.0, -999.0
    return out, (fist_x, fist_y)


class MrDiyVortexRenderer:
    def __init__(self):
        self.emblem = Image.open(os.path.join(ASSETS_DIR, "mrdiy_emblem_rgba.png")).convert("RGBA")
        self.hammer = Image.open(os.path.join(ASSETS_DIR, "mrdiy_hammer_mascot_rgba.png")).convert("RGBA")
        self.screw = mrdiy_props.make_screw_rgba(size=96)
        self.bag = mrdiy_props.make_mrdiy_bag_rgba(size=112)
        self.burst = mrdiy_props.make_price_burst_rgba("LOW PRICES!", size=116)

        # Deterministic 10-particle 3D hardware & bargain vortex orbiting Rob!
        # (kind, radius_px, base_y, y_bob_amp, theta0_deg, orbits_per_loop, spin_dir, base_scale)
        self.particles = [
            ("bag",    248.0, 290.0, 22.0,   18.0, 1, +1, 0.72),
            ("screw",  235.0, 195.0, 18.0,   58.0, 1, -1, 0.68),
            ("hammer", 256.0, 385.0, 24.0,  102.0, 1, +1, 0.34),
            ("screw",  242.0, 485.0, 20.0,  144.0, 1, +1, 0.64),
            ("burst",  262.0, 240.0, 18.0,  188.0, 1, -1, 0.68),
            ("bag",    246.0, 445.0, 22.0,  226.0, 1, -1, 0.68),
            ("screw",  232.0, 330.0, 20.0,  268.0, 1, +1, 0.66),
            ("hammer", 255.0, 215.0, 22.0,  308.0, 1, -1, 0.32),
            ("screw",  240.0, 535.0, 16.0,  342.0, 1, -1, 0.60),
            ("burst",  258.0, 365.0, 20.0,   80.0, 1, +1, 0.64),
        ]

    def _get_sprite(self, kind: str) -> Image.Image:
        if kind == "bag":
            return self.bag
        if kind == "screw":
            return self.screw
        if kind == "hammer":
            return self.hammer
        return self.burst

    def render_scene(
        self,
        char_rgba: np.ndarray,
        phase_01: float,
        cam_yaw_deg: float = 0.0,
        show_big_emblem: bool = True,
        pump_sparkle_pos: tuple[float, float] | None = None,
        pump_strength: float = 0.0,
    ) -> Image.Image:
        CW, CH = CANVAS_W, CANVAS_H
        scene = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        ang = 2.0 * math.pi * phase_01
        cam_rad = math.radians(cam_yaw_deg)

        # 1. Background MR. D.I.Y. Circular Storefront Emblem Halo behind Rob's shoulders (z < 0)!
        if show_big_emblem:
            pulse = 1.0 + 0.055 * abs(math.sin(ang))
            rock_deg = 4.8 * math.sin(ang)
            ew = int(round(292 * pulse))
            eh = int(round(ew * self.emblem.height / float(self.emblem.width)))
            emb_s = self.emblem.resize((ew, eh), Image.Resampling.LANCZOS).rotate(rock_deg, resample=Image.Resampling.BICUBIC, expand=True)

            # Soft warm golden halo behind emblem
            glow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gx, gy = CW // 2, 226
            gr = int(146 * pulse)
            gd.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=(255, 208, 24, 58))
            glow = glow.filter(ImageFilter.GaussianBlur(18))
            scene = Image.alpha_composite(scene, glow)
            scene.alpha_composite(emb_s, (gx - emb_s.width // 2, gy - emb_s.height // 2))
        else:
            # Compact floating MR. D.I.Y. badge halo for 360° directional frames so silhouette stays compact for Quake!
            pulse = 1.0 + 0.05 * math.sin(2.0 * ang)
            ew = int(round(196 * pulse))
            eh = int(round(ew * self.emblem.height / float(self.emblem.width)))
            emb_s = self.emblem.resize((ew, eh), Image.Resampling.LANCZOS)
            # Slightly dim emblem to 90% opacity behind Rob in 360 mode
            ea = np.asarray(emb_s, dtype=np.float32).copy()
            ea[..., 3] *= 0.90
            emb_s = Image.fromarray(np.round(ea).astype(np.uint8), "RGBA")
            scene.alpha_composite(emb_s, (CW // 2 - emb_s.width // 2, 212 - emb_s.height // 2))

        # 2. Compute 3D (X, Y, Z) positions of orbiting MR. D.I.Y. props!
        back_items = []
        front_items = []
        for idx_p, (kind, rad_orb, base_y, y_amp, th0, n_orb, sdir, bscale) in enumerate(self.particles):
            th = math.radians(th0) + n_orb * ang - cam_rad
            wx = rad_orb * math.sin(th)
            wz = rad_orb * math.cos(th)
            wy = base_y + y_amp * math.sin(2.0 * ang + idx_p * 0.9)

            # Keep front-passing props strictly outside Rob's central body/face/legs corridor (|x| >= 158px)
            # by routing props behind Rob whenever |wx| < 158, OR pushing side-passing props cleanly outward!
            if wz >= 0.0 and abs(wx) < 162.0:
                # Smoothly tuck behind Rob's shoulders/legs instead of covering his face, smiley shirt, or dancing legs!
                wz = -abs(wz) - 20.0

            persp = 1.0 + 0.18 * (wz / max(1.0, rad_orb))
            sc = bscale * persp
            src_im = self._get_sprite(kind)
            pw = max(12, int(round(src_im.width * sc)))
            ph = max(12, int(round(src_im.height * sc)))
            prop = src_im.resize((pw, ph), Image.Resampling.LANCZOS)

            if kind == "screw":
                rot = sdir * (math.degrees(ang) + idx_p * 37.0)
            elif kind == "hammer":
                rot = 18.0 * math.sin(2.0 * ang + idx_p)
            else:
                rot = 14.0 * math.sin(ang + idx_p * 1.3)
            prop = prop.rotate(rot, resample=Image.Resampling.BICUBIC, expand=True)

            if wz < 0.0:
                # Subtle depth atmospheric dim on background props
                pa = np.asarray(prop, dtype=np.float32).copy()
                pa[..., :3] *= 0.88
                pa[..., 3] *= 0.90
                prop = Image.fromarray(np.round(pa).astype(np.uint8), "RGBA")
                back_items.append((wz, prop, int(round(CW * 0.5 + wx - prop.width * 0.5)), int(round(wy - prop.height * 0.5))))
            else:
                front_items.append((wz, prop, int(round(CW * 0.5 + wx - prop.width * 0.5)), int(round(wy - prop.height * 0.5))))

        back_items.sort(key=lambda it: it[0])
        front_items.sort(key=lambda it: it[0])

        for _, pim, px, py in back_items:
            scene.alpha_composite(pim, (px, py))

        # 3. Soft ground contact shadow right under Rob's dancing shoes (y ~ 696)
        sh_im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh_im)
        sd.ellipse((CW // 2 - 96, 682, CW // 2 + 96, 712), fill=(0, 0, 0, 92))
        sh_im = sh_im.filter(ImageFilter.GaussianBlur(10))
        scene = Image.alpha_composite(scene, sh_im)

        # 4. Full-body Rob (head + smiley shirt + crossbody bag + animated black jeans + shoes)!
        scene = Image.alpha_composite(scene, Image.fromarray(char_rgba, "RGBA"))

        # 5. Golden MR. D.I.Y. fist-pump sparkles OUTSIDE Rob's pumping hands at peak beat!
        if pump_sparkle_pos is not None and pump_strength > 0.15 and pump_sparkle_pos[0] > 0:
            fx, fy = pump_sparkle_pos
            out_dir_x = -1.0 if fx < CW * 0.5 else 1.0
            r_glint = int(round(14 + 18 * pump_strength))
            mrdiy_props.draw_pump_glint(scene, fx, fy, radius=r_glint, angle_deg=22.0 * math.sin(2.0 * ang))
            mrdiy_props.draw_pump_glint(scene, fx + out_dir_x * 26.0, fy - 24.0, radius=max(9, int(r_glint * 0.65)), angle_deg=-18.0)

        # 6. Side-orbiting foreground hardware/bargain props (never overlapping Rob's center!)
        for _, pim, px, py in front_items:
            scene.alpha_composite(pim, (px, py))

        return scene


# ---------------------------------------------------------------------------
# 5. GIF, Contact Sheet, Quake SPR32 & Interactive HTML Builders
# ---------------------------------------------------------------------------

def save_transparent_gif(frames_rgba: list[Image.Image], path: str, duration_ms: int = 75):
    gif_frames = []
    for im in frames_rgba:
        arr = np.asarray(im)
        a = arr[..., 3]
        rgb = Image.fromarray(arr[..., :3], "RGB")
        pal = rgb.quantize(colors=255, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        p_np = np.asarray(pal).copy()
        p_np[a < 110] = 255
        p_im = Image.fromarray(p_np, "P")
        palette = pal.getpalette()[:255 * 3] + [0, 0, 0]
        p_im.putpalette(palette)
        p_im.info["transparency"] = 255
        gif_frames.append(p_im)
    gif_frames[0].save(
        path,
        save_all=True,
        append_images=gif_frames[1:],
        loop=0,
        duration=duration_ms,
        disposal=2,
        transparency=255,
    )


def save_checker_showcase_gif(frames_rgba: list[Image.Image], path: str, duration_ms: int = 75, scale: float = 0.68):
    w0, h0 = frames_rgba[0].size
    nw, nh = int(round(w0 * scale)), int(round(h0 * scale))
    yy, xx = np.mgrid[0:nh, 0:nw]
    chk = np.where(((xx // 18) + (yy // 18)) % 2 == 0, 34, 46).astype(np.uint8)
    bg = Image.fromarray(np.dstack([chk, chk + 3, chk + 9]), "RGB")

    out_frames = []
    for im in frames_rgba:
        sm = im.resize((nw, nh), Image.Resampling.LANCZOS)
        comp = bg.copy()
        comp.paste(sm, (0, 0), sm)
        out_frames.append(comp.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG))
    out_frames[0].save(path, save_all=True, append_images=out_frames[1:], loop=0, duration=duration_ms, disposal=1)


def write_quake_spr32(dir_frames: list[list[Image.Image]], out_path: str, height_px: int = 128):
    """Writes 56-frame IDSP v32 SPR_VP_PARALLEL_UPRIGHT Quake sprite:
    frames 0..7 = 8-direction idle, frames 8..55 = 8 directions x 6 dance/run frames,
    origin anchored at Rob's shoe soles (y = 696 in 720x780 canvas)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Crop tight consistent box across all 48 frames so Rob fills the 128px Quake sprite cleanly!
    # In 720x780: x = 110..610 (500px wide), y = 64..716 (652px tall), shoe sole ground at y = 696!
    cx0, cy0, cx1, cy1 = 110, 64, 610, 716
    foot_y_in_crop = 696 - cy0
    crop_w, crop_h = cx1 - cx0, cy1 - cy0
    sc = height_px / float(crop_h)
    w_out = max(1, int(round(crop_w * sc)))
    ox = -(w_out // 2)
    oy = int(round(foot_y_in_crop * sc))

    def prep(im: Image.Image) -> tuple[Image.Image, int, int]:
        c = im.crop((cx0, cy0, cx1, cy1)).resize((w_out, height_px), Image.Resampling.LANCZOS)
        return c, ox, oy

    frames = []
    for d in range(8):
        frames.append(prep(dir_frames[d][0]))
    for d in range(8):
        for k in range(6):
            frames.append(prep(dir_frames[d][k]))

    rad = math.sqrt((w_out / 2.0) ** 2 + height_px ** 2)
    # type=0 = SPR_VP_PARALLEL_UPRIGHT
    blob = b"IDSP" + struct.pack("<iifiiifi", 32, 0, rad, w_out, height_px, len(frames), 0.0, 0)
    for im, fox, foy in frames:
        w, h = im.size
        blob += struct.pack("<i", 0) + struct.pack("<iiii", fox, foy, w, h) + im.tobytes()

    with open(out_path, "wb") as f:
        f.write(blob)
    print(f"Wrote Quake SPR32: {out_path} ({len(frames)} frames, {w_out}x{height_px}, {len(blob)/1e6:.2f} MB)")


def write_interactive_html(out_dir: str):
    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rob's MR. D.I.Y. Full-Body Dance &amp; 360° Sprite</title>
<style>
  :root { --bg:#14161b; --panel:#21252e; --ink:#f3f5f8; --dim:#9ea6b4; --diy:#ffd217; --red:#e11d24; --accent:#38bdf8; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, -apple-system, sans-serif; display:flex; flex-direction:column; align-items:center; gap:12px; padding:16px; min-height:100vh; }
  h1 { font-size:21px; margin:2px 0 0; font-weight:800; letter-spacing:-0.01em; display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:center; }
  .tag { background:var(--diy); color:#1b1305; border:2px solid var(--red); border-radius:7px; padding:2px 9px; font-size:13px; font-weight:900; letter-spacing:0.03em; }
  .tabs { display:flex; gap:8px; flex-wrap:wrap; justify-content:center; }
  .tabs button { background:#2c313d; color:var(--dim); border:2px solid transparent; border-radius:8px; padding:8px 15px; font:inherit; font-weight:700; cursor:pointer; }
  .tabs button.active { background:#2a2412; color:var(--diy); border-color:var(--diy); }
  #stage { width:min(100%, 760px); aspect-ratio:720/780; max-height:64vh; border-radius:14px; display:flex; align-items:center; justify-content:center; overflow:hidden; border:1px solid #353b48; position:relative; cursor:grab; touch-action:none; user-select:none; }
  #stage.drag { cursor:grabbing; }
  #stage.checker { background:repeating-conic-gradient(#2b2f3a 0% 25%, #20242c 0% 50%) 0 0/24px 24px; }
  #stage.store { background:radial-gradient(circle at 50% 42%, #4a3f28 0%, #231e16 68%, #12100d 100%); }
  #stage.quake { background:radial-gradient(circle at 50% 62%, #3d2e22 0%, #1c1510 72%, #0e0b09 100%); }
  #stage.green { background:#00b140; }
  #stage img { width:100%; height:100%; object-fit:contain; pointer-events:none; }
  #badge { position:absolute; top:12px; left:14px; background:rgba(15,18,24,0.85); border:1px solid #3d4352; border-radius:8px; padding:5px 11px; font-size:13px; font-weight:700; color:var(--diy); pointer-events:none; backdrop-filter:blur(6px); }
  #draghint { position:absolute; bottom:10px; right:14px; background:rgba(15,18,24,0.78); border-radius:6px; padding:4px 10px; font-size:12px; color:var(--dim); pointer-events:none; }
  .row { display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:center; width:min(100%,760px); background:var(--panel); border-radius:10px; padding:11px 14px; }
  input[type=range] { flex:1 1 130px; accent-color:var(--diy); }
  button.ctrl { background:var(--diy); color:#1a1204; border:0; border-radius:7px; padding:8px 13px; font:inherit; font-weight:800; cursor:pointer; }
  button.laugh { background:var(--red); color:#fff; border:2px solid var(--diy); }
  button.spin { background:var(--accent); color:#082f49; }
  button.alt { background:#383e4c; color:var(--ink); font-weight:600; }
  label { color:var(--dim); display:flex; gap:6px; align-items:center; font-size:14px; }
  #info { color:var(--dim); min-width:16ch; text-align:right; font-variant-numeric:tabular-nums; font-size:13px; }
  #strip { display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%,760px); }
  @media (max-width:680px) { #strip { grid-template-columns:repeat(4, 1fr); } }
  #strip button { padding:4px 4px 2px; background:var(--panel); border:2px solid transparent; border-radius:8px; display:flex; flex-direction:column; align-items:center; gap:2px; overflow:hidden; color:var(--dim); font-size:11px; font-weight:700; cursor:pointer; }
  #strip button.on { border-color:var(--diy); color:var(--ink); background:#2d3240; }
  #strip img { width:100%; aspect-ratio:720/780; object-fit:contain; display:block; }
  p.hint { color:var(--dim); margin:0; font-size:13px; text-align:center; }
</style>
</head>
<body>
  <h1><span class="tag">MR. D.I.Y.</span> Rob's Full-Body Dancing Sprite</h1>
  <div class="tabs">
    <button id="tabHero" class="active">Hero 16-Frame Dance (Full Body)</button>
    <button id="tab360">Interactive 360&deg; Turnaround (8 Angles)</button>
  </div>
  <div id="stage" class="checker">
    <div id="badge">Hero MR. D.I.Y. Dance</div>
    <img id="view" alt="Rob MR. D.I.Y. sprite frame">
    <div id="draghint">Full-Body 16-Frame Loop</div>
  </div>
  <div class="row">
    <button class="ctrl" id="play">Pause</button>
    <button class="ctrl laugh" id="laughBtn">&#x1F50A; Play Rob's Laugh</button>
    <button class="ctrl spin" id="orbit" style="display:none">Auto-Spin 360&deg;: ON</button>
    <label id="scrubWrap">Frame <input id="scrub" type="range" min="0" max="15" value="0" style="flex:0 0 130px"></label>
    <label id="angWrap" style="display:none">Angle <input id="ang" type="range" min="0" max="7" value="0" style="flex:0 0 120px"></label>
    <label>FPS <input id="fps" type="range" min="4" max="24" value="13" style="flex:0 0 90px"></label>
    <button class="ctrl alt" id="bgbtn">BG: Checker</button>
    <span id="info">Frame 0/15</span>
  </div>
  <p class="hint">Space pauses &bull; Left/Right steps frames (or rotates 360&deg; in Turnaround mode) &bull; Audio from Rob's real MR. D.I.Y. clip</p>
  <div id="strip"></div>
  <audio id="laughAudio" src="mrdiy_laugh.mp3" preload="auto"></audio>
<script>
const HERO_N = 16, DIRS = 8, DIR_N = 6;
const LABELS = ["0° Front", "45° Front-Left", "90° Left Side", "135° Back-Left", "180° Back", "225° Back-Right", "270° Right Side", "315° Front-Right"];
const heroSrc = f => `mrdiy_${String(f).padStart(2, "0")}.png`;
const dirSrc = (d, f) => `mrdiy_d${d}_f${f}.png`;

const view = document.getElementById("view"), badge = document.getElementById("badge"),
      draghint = document.getElementById("draghint"), info = document.getElementById("info"),
      playBtn = document.getElementById("play"), laughBtn = document.getElementById("laughBtn"),
      orbitBtn = document.getElementById("orbit"), scrubEl = document.getElementById("scrub"),
      scrubWrap = document.getElementById("scrubWrap"), angEl = document.getElementById("ang"),
      angWrap = document.getElementById("angWrap"), fpsEl = document.getElementById("fps"),
      stage = document.getElementById("stage"), strip = document.getElementById("strip"),
      bgbtn = document.getElementById("bgbtn"), tabHero = document.getElementById("tabHero"),
      tab360 = document.getElementById("tab360"), audio = document.getElementById("laughAudio");

let mode = "hero", curHero = 0, curDir = 0, curDirF = 0, running = true, autoSpin = true;
let lastStep = 0, lastSpin = 0, laughLoop = false;
const bgs = ["checker", "store", "quake", "green"], bgNames = ["Checker", "Storefront Warm", "Quake Dungeon", "Chroma Green"];
let bgi = 0;

for (let i = 0; i < HERO_N; i++) { const im = new Image(); im.src = heroSrc(i); }
for (let d = 0; d < DIRS; d++) for (let f = 0; f < DIR_N; f++) { const im = new Image(); im.src = dirSrc(d, f); }

let thumbs = [], thumbImgs = [];
function rebuildStrip() {
  strip.innerHTML = ""; thumbs = []; thumbImgs = [];
  if (mode === "hero") {
    for (let k = 0; k < 8; k++) {
      const f = k * 2;
      const b = document.createElement("button");
      const im = document.createElement("img"); im.src = heroSrc(f);
      const sp = document.createElement("span"); sp.textContent = "#" + String(f).padStart(2, "0");
      b.appendChild(im); b.appendChild(sp);
      b.onclick = () => { running = false; syncUI(); curHero = f; render(); };
      strip.appendChild(b); thumbs.push(b); thumbImgs.push(im);
    }
  } else {
    for (let d = 0; d < DIRS; d++) {
      const b = document.createElement("button");
      const im = document.createElement("img"); im.src = dirSrc(d, curDirF);
      const sp = document.createElement("span"); sp.textContent = (d * 45) + "°";
      b.appendChild(im); b.appendChild(sp);
      b.onclick = () => { autoSpin = false; syncUI(); curDir = d; render(); };
      strip.appendChild(b); thumbs.push(b); thumbImgs.push(im);
    }
  }
}

function render() {
  if (mode === "hero") {
    curHero = ((curHero % HERO_N) + HERO_N) % HERO_N;
    view.src = heroSrc(curHero);
    badge.textContent = "Hero MR. D.I.Y. Dance (Full Legs & Shoes)";
    draghint.textContent = "↔ Drag to scrub frames";
    scrubEl.value = curHero;
    info.textContent = `Frame ${curHero}/${HERO_N - 1}`;
    thumbs.forEach((t, k) => t.classList.toggle("on", Math.floor(curHero / 2) === k));
  } else {
    curDir = ((curDir % DIRS) + DIRS) % DIRS;
    curDirF = ((curDirF % DIR_N) + DIR_N) % DIR_N;
    view.src = dirSrc(curDir, curDirF);
    badge.textContent = LABELS[curDir];
    draghint.textContent = "↔ Drag anywhere to spin 360°";
    angEl.value = curDir;
    info.textContent = `${curDir * 45}° • Frame ${curDirF}/${DIR_N - 1}`;
    thumbs.forEach((t, k) => t.classList.toggle("on", k === curDir));
    thumbImgs.forEach((im, k) => { im.src = dirSrc(k, curDirF); });
  }
}

function syncUI() {
  tabHero.classList.toggle("active", mode === "hero");
  tab360.classList.toggle("active", mode === "360");
  orbitBtn.style.display = mode === "360" ? "" : "none";
  angWrap.style.display = mode === "360" ? "" : "none";
  scrubWrap.style.display = mode === "hero" ? "" : "none";
  playBtn.textContent = running ? "Pause" : "Play";
  orbitBtn.textContent = "Auto-Spin 360°: " + (autoSpin ? "ON" : "OFF");
  orbitBtn.className = "ctrl " + (autoSpin ? "spin" : "alt");
}

tabHero.onclick = () => { mode = "hero"; rebuildStrip(); syncUI(); render(); };
tab360.onclick = () => { mode = "360"; rebuildStrip(); syncUI(); render(); };
playBtn.onclick = () => { running = !running; syncUI(); };
orbitBtn.onclick = () => { autoSpin = !autoSpin; syncUI(); };
scrubEl.oninput = () => { running = false; syncUI(); curHero = +scrubEl.value; render(); };
angEl.oninput = () => { autoSpin = false; syncUI(); curDir = +angEl.value; render(); };
bgbtn.onclick = () => {
  stage.classList.remove(bgs[bgi]);
  bgi = (bgi + 1) % bgs.length;
  stage.classList.add(bgs[bgi]);
  bgbtn.textContent = "BG: " + bgNames[bgi];
};
laughBtn.onclick = () => {
  laughLoop = !laughLoop;
  audio.loop = laughLoop;
  if (laughLoop) { audio.currentTime = 0; audio.play(); laughBtn.textContent = "🔇 Stop Laugh"; }
  else { audio.pause(); laughBtn.textContent = "🔊 Play Rob's Laugh"; }
};

let dragX = null, dragStart = 0;
stage.addEventListener("pointerdown", e => {
  dragX = e.clientX;
  dragStart = mode === "hero" ? curHero : curDir;
  if (mode === "360") autoSpin = false; else running = false;
  syncUI();
  stage.classList.add("drag");
  stage.setPointerCapture(e.pointerId);
});
stage.addEventListener("pointermove", e => {
  if (dragX === null) return;
  const steps = Math.round((e.clientX - dragX) / 34);
  if (mode === "hero") curHero = dragStart + steps;
  else curDir = dragStart - steps;
  render();
});
const endDrag = () => { dragX = null; stage.classList.remove("drag"); };
stage.addEventListener("pointerup", endDrag);
stage.addEventListener("pointercancel", endDrag);

addEventListener("keydown", e => {
  if (e.code === "Space") { e.preventDefault(); running = !running; syncUI(); }
  else if (e.code === "ArrowRight") { e.preventDefault(); if (mode === "hero") { running = false; curHero++; } else { autoSpin = false; curDir++; } syncUI(); render(); }
  else if (e.code === "ArrowLeft")  { e.preventDefault(); if (mode === "hero") { running = false; curHero--; } else { autoSpin = false; curDir--; } syncUI(); render(); }
});

function tick(t) {
  const interval = 1000 / (+fpsEl.value);
  let dirty = false;
  if (running && t - lastStep > interval) {
    lastStep = t;
    if (mode === "hero") curHero = (curHero + 1) % HERO_N;
    else curDirF = (curDirF + 1) % DIR_N;
    dirty = true;
  }
  if (mode === "360" && autoSpin && t - lastSpin > interval * 3.0) {
    lastSpin = t;
    curDir = (curDir + 1) % DIRS;
    dirty = true;
  }
  if (dirty) render();
  requestAnimationFrame(tick);
}
rebuildStrip(); syncUI(); render();
requestAnimationFrame(tick);
</script>
</body>
</html>
"""
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("1/5 Building photographic black-jeans + shoes multi-angle rig...")
    graded_legs = build_black_jeans_legs()

    print("2/5 Initializing GPU MaskRCNN + Clean-Plate Video Matter...")
    matter = RobVideoMatter()
    vortex = MrDiyVortexRenderer()

    # -----------------------------------------------------------------------
    # Part A: 16-Frame Seamless Full-Body Hero MR. D.I.Y. Dance (mrdiy_00..15)
    # -----------------------------------------------------------------------
    # Beat 1 (0..7): Cheeky camera-stare grin double-fist pump (f=8..34) + Left-leg dance kick!
    # Beat 2 (8..15): Hysterical eyes-crinkled laughing double-fist pump (f=120..142) + Right-leg dance kick!
    hero_vid_idxs = [8, 12, 17, 20, 24, 28, 31, 34, 120, 123, 126, 130, 133, 136, 139, 142]
    print("3/5 Rendering 16-frame Full-Body Hero MR. D.I.Y. Dance...")
    hero_frames: list[Image.Image] = []
    for k, vidx in enumerate(hero_vid_idxs):
        ph = k / float(N_HERO)
        u_rgba, hip_info = matter.matte_upper_body(vidx, neutralize_bag_text=False)
        legs_rgba, sdx, bdy = pose_dance_legs(graded_legs, view_deg=0, phase_01=ph, hero_kick=True)
        tilt = -2.2 * math.sin(2.0 * math.pi * ph)
        char_rgba, fist_pos = composite_fullbody_character(
            u_rgba, hip_info, legs_rgba, sdx, bdy,
            mirror_upper=False, mirror_legs=False, upper_tilt_deg=tilt,
        )
        # Peak fist-pump sparkle around frames 2..5 and 10..13!
        pump_str = max(0.0, math.sin(math.pi * ((k % 8) / 7.0)) ** 2 - 0.35) / 0.65
        frame_im = vortex.render_scene(
            char_rgba, phase_01=ph, cam_yaw_deg=0.0,
            show_big_emblem=True, pump_sparkle_pos=fist_pos, pump_strength=pump_str,
        )
        frame_im.save(os.path.join(OUT_DIR, f"mrdiy_{k:02d}.png"))
        hero_frames.append(frame_im)

    # 4x4 Master Sprite Sheet for Hero Dance
    sheet_4x4 = Image.new("RGBA", (CANVAS_W * 4, CANVAS_H * 4), (0, 0, 0, 0))
    for k, im in enumerate(hero_frames):
        sheet_4x4.alpha_composite(im, ((k % 4) * CANVAS_W, (k // 4) * CANVAS_H))
    sheet_4x4.save(os.path.join(OUT_DIR, "mrdiy_sheet_4x4.png"))

    save_transparent_gif(hero_frames, os.path.join(OUT_DIR, "mrdiy_dance.gif"), duration_ms=76)
    save_checker_showcase_gif(hero_frames, os.path.join(OUT_DIR, "mrdiy_showcase.gif"), duration_ms=76, scale=0.68)
    print("    Saved mrdiy_00..15.png, mrdiy_sheet_4x4.png, mrdiy_dance.gif, mrdiy_showcase.gif")

    # -----------------------------------------------------------------------
    # Part B: 8-Direction x 6-Frame Full 360° Turnaround Dance + Quake SPR32
    # -----------------------------------------------------------------------
    print("4/5 Rendering 48-frame (8 angles x 6 frames) 360° Full-Body Turnaround...")
    # Direction specs: (vid_frame_list_or_None_for_180, mirror_upper, neutralize_txt, leg_view_deg, mirror_legs)
    dir_specs = {
        0: ([36, 8, 18, 22, 28, 34],         False, False,   0, False),  # 0° Front
        1: ([120, 124, 129, 133, 137, 141],  False, False,  45, False),  # 45° Front-Left
        2: ([68, 72, 76, 80, 83, 73],        True,  True,   90, False),  # 90° Left Side (head-back pump!)
        3: ([171, 174, 177, 179, 176, 173],  True,  True,  135, False),  # 135° Back-Left
        4: (None,                            False, True,  180, False),  # 180° Back
        5: ([171, 174, 177, 179, 176, 173],  False, False, 135, True),   # 225° Back-Right (real unflipped!)
        6: ([68, 72, 76, 80, 83, 73],        False, False,  90, True),   # 270° Right Side (real unflipped!)
        7: ([120, 124, 129, 133, 137, 141],  True,  True,   45, True),   # 315° Front-Right
    }

    dir_frames: list[list[Image.Image]] = []
    sheet_360 = Image.new("RGBA", (CANVAS_W * N_DIR_FRAMES, CANVAS_H * N_DIRS), (0, 0, 0, 0))

    for d in range(N_DIRS):
        vlist, mir_u, neut_txt, leg_deg, mir_l = dir_specs[d]
        row_ims: list[Image.Image] = []
        cam_yaw = d * 45.0
        for f in range(N_DIR_FRAMES):
            ph = f / float(N_DIR_FRAMES)
            if vlist is None:
                u_rgba, hip_info = matter.build_back_180_upper(ph)
            else:
                u_rgba, hip_info = matter.matte_upper_body(vlist[f], neutralize_bag_text=neut_txt)

            legs_rgba, sdx, bdy = pose_dance_legs(graded_legs, view_deg=leg_deg, phase_01=ph, hero_kick=(leg_deg == 0))
            char_rgba, fist_pos = composite_fullbody_character(
                u_rgba, hip_info, legs_rgba, sdx, bdy,
                mirror_upper=mir_u, mirror_legs=mir_l,
            )
            p_str = 0.65 if (f in (2, 3) and d != 4) else 0.0
            im = vortex.render_scene(
                char_rgba, phase_01=ph, cam_yaw_deg=cam_yaw,
                show_big_emblem=False, pump_sparkle_pos=fist_pos if d != 4 else None, pump_strength=p_str,
            )
            im.save(os.path.join(OUT_DIR, f"mrdiy_d{d}_f{f}.png"))
            sheet_360.alpha_composite(im, (f * CANVAS_W, d * CANVAS_H))
            row_ims.append(im)
        dir_frames.append(row_ims)

    sheet_360.save(os.path.join(OUT_DIR, "mrdiy_360_sheet_8x6.png"))

    # Build 24-frame 360° spinning + dancing showcase GIF (3 dance frames per angle around all 8 angles)
    spin_frames = []
    for step in range(24):
        d = (step // 3) % 8
        f = step % N_DIR_FRAMES
        spin_frames.append(dir_frames[d][f])
    save_checker_showcase_gif(spin_frames, os.path.join(OUT_DIR, "mrdiy_360_spin.gif"), duration_ms=85, scale=0.64)

    print("5/5 Exporting Quake SPR32 & interactive HTML viewer...")
    write_quake_spr32(dir_frames, os.path.join(PROGS_DIR, "fr_mrdiy.spr32"), height_px=128)
    write_interactive_html(OUT_DIR)

    # Also render a crisp visual audit contact sheet in scratch/ to inspect every Hero & 360° angle!
    audit_hero = Image.new("RGB", (CANVAS_W * 4 // 2, CANVAS_H * 4 // 2), (42, 45, 54))
    for k, im in enumerate(hero_frames):
        sm = im.resize((CANVAS_W // 2, CANVAS_H // 2), Image.Resampling.LANCZOS)
        audit_hero.paste(sm, ((k % 4) * (CANVAS_W // 2), (k // 4) * (CANVAS_H // 2)), sm)
    audit_hero.save(os.path.join(SCRATCH, "audit_hero_4x4.jpg"), quality=92)

    audit_360 = Image.new("RGB", (CANVAS_W * 4 // 2, CANVAS_H * 2 // 2), (42, 45, 54))
    for d in range(8):
        sm = dir_frames[d][2].resize((CANVAS_W // 2, CANVAS_H // 2), Image.Resampling.LANCZOS)
        audit_360.paste(sm, ((d % 4) * (CANVAS_W // 2), (d // 4) * (CANVAS_H // 2)), sm)
    audit_360.save(os.path.join(SCRATCH, "audit_360_8dirs.jpg"), quality=92)
    print("ALL DONE! Sprite pack ready in:", OUT_DIR)


if __name__ == "__main__":
    main()
