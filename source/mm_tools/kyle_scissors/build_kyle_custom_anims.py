"""Build custom high-FPS photorealistic Kyle Tillet projectile animations & actual US currency FX.

Replaces the old cartoony bobblehead row completely! Every Kyle animation is built from the
real HD 768x1152 360-degree studio turnaround videos at 320px tall, 12-16 frames/cycle @ 24 FPS:

  1. running_scissors/  (8 dirs x 16 frames @ 24 FPS) — Real Kyle sprinting with articulated
     2-leg C1-Bezier trousers + rigid pivoting brown loafers (near leg + depth-shaded far leg),
     forward sprint lean, stride bounce, AND actively chopping giant front scissors!
  2. overhead_scissors/ (8 dirs x 12 frames @ 24 FPS) — Full-body overhead scissor chomping
     with smooth rigid blade rotation, anticipation reach, power crunch & metallic glint!
  3. front_scissors/    (8 dirs x 12 frames @ 24 FPS) — Aggressive forward lunge-chopping
     with wide jaw snap, body lunge/flex & spark glint (used for Peripheral Latch & Register Raid).
  4. no_scissors/       (8 dirs x 12 frames @ 16 FPS) — Alive idle breathing, weight shift & head bob.
  5. cash_fx/           — Realistic US $100 bills (8 tumbling/fluttering frames from studio plate)
                          + Real 2024 US Silver Quarter (8 spinning 3D frames w/ reeded edge)
                          + Real 2024 US Sacagawea Gold Dollar (8 spinning 3D frames w/ brass edge).

Run:
    python source/mm_tools/kyle_scissors/build_kyle_custom_anims.py
"""

import json
import math
import os
import sys
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kyle_sprites as base_mod  # reuse proven key_studio_offwhite & video indices

ARTIFACT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
OUT_DIR = os.path.join(ARTIFACT_ROOT, "sprites")

US_BILLS_PLATE = os.path.join(ARTIFACT_ROOT, "us_bills_plate_1795067254667.jpg")
US_COINS_PLATE = os.path.join(ARTIFACT_ROOT, "us_coins_plate_1795067190686.jpg")

TARGET_H = 300
N_DIRS = 8
DIR_INFO = base_mod.DIR_INFO


# ===========================================================================
# Premultiplied RGBA & Smooth Geometry Helpers
# ===========================================================================
def to_pm(rgba: np.ndarray) -> np.ndarray:
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    out = np.empty(rgba.shape, dtype=np.float32)
    out[..., :3] = rgba[..., :3].astype(np.float32) * a
    out[..., 3:4] = a
    return out


def from_pm(pm: np.ndarray) -> np.ndarray:
    a = np.clip(pm[..., 3:4], 0.0, 1.0)
    rgb = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0.0)
    out = np.empty(pm.shape, dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a[..., 0] * 255.0), 0, 255).astype(np.uint8)
    return out


def over_pm(dst: np.ndarray, src: np.ndarray) -> np.ndarray:
    inv = 1.0 - src[..., 3:4]
    out = np.empty_like(dst)
    out[..., :3] = src[..., :3] + dst[..., :3] * inv
    out[..., 3:4] = src[..., 3:4] + dst[..., 3:4] * inv
    return out


def tint_pm(pm: np.ndarray, rgb_mult: Tuple[float, float, float]) -> np.ndarray:
    out = pm.copy()
    out[..., 0] *= rgb_mult[0]
    out[..., 1] *= rgb_mult[1]
    out[..., 2] *= rgb_mult[2]
    return out


def affine_pm(pm: np.ndarray, piv: Tuple[float, float], deg: float,
              dx: float = 0.0, dy: float = 0.0, sx: float = 1.0, sy: float = 1.0) -> np.ndarray:
    """Rotate & scale premultiplied RGBA around piv then translate by (dx, dy)."""
    h, w = pm.shape[:2]
    rad = math.radians(deg)
    ca, sa = math.cos(rad), math.sin(rad)
    px, py = piv
    # Forward: x' = px + dx + (x - px)*sx*ca - (y - py)*sy*sa
    #          y' = py + dy + (x - px)*sx*sa + (y - py)*sy*ca
    M = np.array([
        [sx * ca, -sy * sa, px + dx - px * sx * ca + py * sy * sa],
        [sx * sa,  sy * ca, py + dy - px * sx * sa - py * sy * ca],
    ], dtype=np.float32)
    return cv2.warpAffine(pm, M, (w, h), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def draw_glint_pm(pm: np.ndarray, center: Tuple[float, float], radius: float, intensity: float) -> np.ndarray:
    if intensity <= 0.05:
        return pm
    h, w = pm.shape[:2]
    cx, cy = int(round(center[0])), int(round(center[1]))
    rad = int(round(radius))
    patch = np.zeros((rad * 2 + 1, rad * 2 + 1, 4), dtype=np.float32)
    yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
    r = np.hypot(xx, yy) / max(1.0, radius)
    core = np.exp(-(r ** 2) * 14.0)
    sp1 = np.exp(-((np.abs(yy) * 8.0) ** 2 + (r * 1.1) ** 2))
    sp2 = np.exp(-((np.abs(xx) * 8.0) ** 2 + (r * 1.1) ** 2))
    diag1 = np.exp(-((np.abs(xx - yy) * 7.5) ** 2 + (r * 1.55) ** 2)) * 0.55
    diag2 = np.exp(-((np.abs(xx + yy) * 7.5) ** 2 + (r * 1.55) ** 2)) * 0.55
    val = np.clip((core + 0.85 * (sp1 + sp2) + diag1 + diag2) * intensity, 0.0, 1.0)
    patch[..., 0] = val * 255.0
    patch[..., 1] = val * 250.0
    patch[..., 2] = val * 225.0
    patch[..., 3] = val

    out = pm.copy()
    x0, y0 = cx - rad, cy - rad
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    cw = min(patch.shape[1] - sx0, w - dx0)
    ch = min(patch.shape[0] - sy0, h - dy0)
    if cw > 0 and ch > 0:
        out[dy0:dy0 + ch, dx0:dx0 + cw] = over_pm(
            out[dy0:dy0 + ch, dx0:dx0 + cw],
            patch[sy0:sy0 + ch, sx0:sx0 + cw],
        )
    return out


# ===========================================================================
# C1-Continuous Quadratic Bezier Limb Skinning (Trouser Tube + Smooth Knee!)
# ===========================================================================
def warp_limb_bezier(src_pm: np.ndarray,
                     src_pts: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]],
                     dst_pts: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]],
                     half_width: float = 95.0,
                     n_samples: int = 80,
                     scale_w: float = 1.0) -> np.ndarray:
    """Deform a limb (hip -> knee -> ankle) cleanly along a C1-smooth quadratic Bezier curve.
    Exact 1.0x photo thickness (or perspective-scaled by scale_w), zero jagged knee seams!
    """
    h, w = src_pm.shape[:2]
    A0, C0, B0 = [np.array(p, np.float32) for p in src_pts]
    A1, C1, B1 = [np.array(p, np.float32) for p in dst_pts]

    ts = np.linspace(-0.08, 1.08, n_samples, dtype=np.float32)

    def eval_curve(P0, P1, P2, t_arr):
        mt = 1.0 - t_arr
        pts = (mt * mt)[:, None] * P0 + (2.0 * mt * t_arr)[:, None] * P1 + (t_arr * t_arr)[:, None] * P2
        tang = (2.0 * mt)[:, None] * (P1 - P0) + (2.0 * t_arr)[:, None] * (P2 - P1)
        tnorm = np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-4)
        tang /= tnorm
        norm = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
        return pts, tang, norm

    dst_p, dst_t, dst_n = eval_curve(A1, C1, B1, ts)
    src_p, _, src_n = eval_curve(A0, C0, B0, ts)

    pad = int(half_width * max(1.0, scale_w)) + 20
    x0 = max(0, int(np.floor(dst_p[:, 0].min())) - pad)
    x1 = min(w, int(np.ceil(dst_p[:, 0].max())) + pad)
    y0 = max(0, int(np.floor(dst_p[:, 1].min())) - pad)
    y1 = min(h, int(np.ceil(dst_p[:, 1].max())) + pad)
    if x1 <= x0 or y1 <= y0:
        return np.zeros_like(src_pm)

    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = xx[..., None] - dst_p[None, None, :, 0]
    dy = yy[..., None] - dst_p[None, None, :, 1]
    d2 = dx * dx + dy * dy
    idx = np.argmin(d2, axis=2)

    px_c = dst_p[idx, 0]
    py_c = dst_p[idx, 1]
    tx_c = dst_t[idx, 0]
    ty_c = dst_t[idx, 1]
    nx_c = dst_n[idx, 0]
    ny_c = dst_n[idx, 1]

    rx = xx - px_c
    ry = yy - py_c
    along = rx * tx_c + ry * ty_c
    signed_d = rx * nx_c + ry * ny_c

    seg_len = np.hypot(np.diff(dst_p[:, 0]), np.diff(dst_p[:, 1]))
    seg_len = np.append(seg_len, seg_len[-1])
    dt_step = (ts[1] - ts[0]) / np.maximum(seg_len[idx], 1e-3)
    t_est = np.clip(ts[idx] + along * dt_step, -0.06, 1.06)

    mt = 1.0 - t_est
    sp_x = mt * mt * A0[0] + 2.0 * mt * t_est * C0[0] + t_est * t_est * B0[0]
    sp_y = mt * mt * A0[1] + 2.0 * mt * t_est * C0[1] + t_est * t_est * B0[1]
    st_x = 2.0 * mt * (C0[0] - A0[0]) + 2.0 * t_est * (B0[0] - C0[0])
    st_y = 2.0 * mt * (C0[1] - A0[1]) + 2.0 * t_est * (B0[1] - C0[1])
    st_n = np.maximum(np.hypot(st_x, st_y), 1e-4)
    sn_x = -st_y / st_n
    sn_y = st_x / st_n

    inv_w = 1.0 / max(0.35, scale_w)
    map_x = (sp_x + (signed_d * inv_w) * sn_x).astype(np.float32)
    map_y = (sp_y + (signed_d * inv_w) * sn_y).astype(np.float32)

    valid = (t_est >= -0.04) & (t_est <= 1.04) & (np.abs(signed_d) <= half_width * scale_w)
    patch = cv2.remap(src_pm, map_x, map_y, cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    patch[~valid] = 0.0

    # Smooth end-fade right past hip/ankle caps
    end_fade = np.clip(np.minimum((t_est + 0.04) / 0.06, (1.04 - t_est) / 0.06), 0.0, 1.0)
    patch *= end_fade[..., None]

    out = np.zeros_like(src_pm)
    out[y0:y1, x0:x1] = patch
    return out


# ===========================================================================
# Shared Canvas Normalization (keeps every frame crisp & feet-grounded!)
# ===========================================================================
def normalize_grid(grid_rgba: List[List[np.ndarray]], target_h: int = TARGET_H,
                   pad_px: int = 8) -> Tuple[List[List[Image.Image]], Tuple[int, int]]:
    """Compute one unified tight bounding box across all directions & frames so Kyle's scale
    and foot baseline never jump between angles or animation frames, then downsample cleanly."""
    min_x, min_y = 10**9, 10**9
    max_x, max_y = -1, -1
    for row in grid_rgba:
        for arr in row:
            ys, xs = np.nonzero(arr[..., 3] > 16)
            if len(xs) == 0:
                continue
            min_x = min(min_x, int(xs.min()))
            max_x = max(max_x, int(xs.max()))
            min_y = min(min_y, int(ys.min()))
            max_y = max(max_y, int(ys.max()))

    src_h, src_w = grid_rgba[0][0].shape[:2]
    # Center horizontally around midpoint of union bbox so spinning turntable stays centered
    cx = 0.5 * (min_x + max_x)
    half_w = max(cx - min_x, max_x - cx) + 18
    x0 = int(math.floor(cx - half_w))
    x1 = int(math.ceil(cx + half_w))
    y0 = max(0, min_y - 16)
    y1 = min(src_h, max_y + 12)
    cw, ch = x1 - x0, y1 - y0

    inner_h = target_h - 2 * pad_px
    scale = inner_h / max(1.0, float(ch))
    out_w = int(round(cw * scale)) + 2 * pad_px
    # Make even width
    out_w += out_w % 2
    out_h = target_h

    out_grid = []
    for row in grid_rgba:
        out_row = []
        for arr in row:
            crop = np.zeros((ch, cw, 4), dtype=np.uint8)
            sx0, sy0 = max(0, x0), max(0, y0)
            sx1, sy1 = min(src_w, x1), min(src_h, y1)
            dx0, dy0 = sx0 - x0, sy0 - y0
            crop[dy0:dy0 + (sy1 - sy0), dx0:dx0 + (sx1 - sx0)] = arr[sy0:sy1, sx0:sx1]
            # Premultiplied Lanczos downsample to avoid dark halos
            pm = to_pm(crop)
            dw = out_w - 2 * pad_px
            dh = inner_h
            pm_s = cv2.resize(pm, (dw, dh), interpolation=cv2.INTER_AREA)
            rgba_s = from_pm(pm_s)
            canvas = np.zeros((out_h, out_w, 4), dtype=np.uint8)
            canvas[pad_px:pad_px + dh, pad_px:pad_px + dw] = rgba_s
            out_row.append(Image.fromarray(canvas, "RGBA"))
        out_grid.append(out_row)
    return out_grid, (out_w, out_h)


# ===========================================================================
# Helper: Extract Front Scissors Upper/Lower Blades per Direction
# ===========================================================================
FRONT_DIR_SPECS = {
    0: ("right", 468.0, 560.0),
    1: ("right", 448.0, 560.0),
    2: ("side",  345.0, 560.0),
    3: ("left",  320.0, 560.0),
    4: ("left",  292.0, 560.0),
    5: ("left",  318.0, 560.0),
    6: ("side",  435.0, 560.0),
    7: ("right", 482.0, 560.0),
}


def segment_front_blades(arr: np.ndarray, d: int) -> Dict:
    """Cleanly separate protruding front scissor upper & lower blades from Kyle's body."""
    H, W = arr.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    mode, split_x, py_approx = FRONT_DIR_SPECS[d]
    rb_diff = arr[..., 0].astype(np.int16) - arr[..., 2].astype(np.int16)
    not_khaki = rb_diff < 28

    if mode in ("right", "left"):
        protrude = (xx >= split_x) if mode == "right" else (xx <= split_x)
        blade_mask = (arr[..., 3] > 20) & protrude & not_khaki & (yy >= 465) & (yy <= 740)
        nb, blbl, bstats, _ = cv2.connectedComponentsWithStats(blade_mask.astype(np.uint8), connectivity=8)
        clean_blade = np.zeros_like(blade_mask)
        for bid in range(1, nb):
            if bstats[bid, cv2.CC_STAT_AREA] >= 60:
                clean_blade |= blbl == bid
        blade_mask = clean_blade

        cols = np.nonzero(np.any(blade_mask, axis=0))[0]
        upper_mask = np.zeros_like(blade_mask)
        lower_mask = np.zeros_like(blade_mask)
        root_ys_u, root_ys_l = [], []
        for cx in cols:
            ys_c = np.nonzero(blade_mask[:, cx])[0]
            if len(ys_c) < 2:
                continue
            diffs = np.diff(ys_c)
            if len(diffs) > 0 and np.max(diffs) >= 4:
                g_idx = int(np.argmax(diffs))
                mid_y = 0.5 * (ys_c[g_idx] + ys_c[g_idx + 1])
            else:
                mid_y = py_approx + (cx - split_x) * (0.08 if mode == "right" else -0.08)
            um = blade_mask[:, cx] & (yy[:, cx] <= mid_y)
            lm = blade_mask[:, cx] & (yy[:, cx] > mid_y)
            upper_mask[:, cx] = um
            lower_mask[:, cx] = lm
            if abs(cx - split_x) <= 20:
                if np.any(um):
                    root_ys_u.append(float(np.mean(np.nonzero(um)[0])))
                if np.any(lm):
                    root_ys_l.append(float(np.mean(np.nonzero(lm)[0])))

        piv_x = split_x + (-6.0 if mode == "right" else 6.0)
        piv_yu = float(np.mean(root_ys_u)) if root_ys_u else py_approx - 10.0
        piv_yl = float(np.mean(root_ys_l)) if root_ys_l else py_approx + 12.0
        piv_ym = 0.5 * (piv_yu + piv_yl)

        up_arr = np.zeros_like(arr)
        up_arr[upper_mask] = arr[upper_mask]
        lo_arr = np.zeros_like(arr)
        lo_arr[lower_mask] = arr[lower_mask]
        body_arr = arr.copy()
        body_arr[blade_mask] = 0
        sgn = 1.0 if mode == "right" else -1.0
        return {
            "mode": mode, "sgn": sgn, "piv": (piv_x, piv_ym),
            "body_pm": to_pm(body_arr),
            "up_pm": to_pm(up_arr),
            "lo_pm": to_pm(lo_arr),
            "blade_mask": blade_mask,
        }
    else:
        # Side views (d2 = facing left, d6 = facing right): scissors held right at front waist
        sgn = -1.0 if d == 2 else 1.0
        piv = (split_x, 575.0)
        # Extract protruding front steel tip in front of the hip/hand
        protrude = (xx <= split_x + 12) if d == 2 else (xx >= split_x - 12)
        blade_mask = (arr[..., 3] > 20) & protrude & not_khaki & (yy >= 490) & (yy <= 695)
        body_arr = arr.copy()
        body_arr[blade_mask] = 0
        up_m = blade_mask & (yy <= 582)
        lo_m = blade_mask & (yy > 582)
        up_arr = np.zeros_like(arr); up_arr[up_m] = arr[up_m]
        lo_arr = np.zeros_like(arr); lo_arr[lo_m] = arr[lo_m]
        return {
            "mode": "side", "sgn": sgn, "piv": piv,
            "body_pm": to_pm(body_arr),
            "up_pm": to_pm(up_arr),
            "lo_pm": to_pm(lo_arr),
            "blade_mask": blade_mask,
        }


# ===========================================================================
# 1. CUSTOM PHOTOREALISTIC RUNNING WITH SCISSORS (8 dirs x 16 frames @ 24 FPS)
# ===========================================================================
def extract_leg_parts(noscis_arr: np.ndarray, d: int) -> Dict:
    """From unobstructed HD no_scissors frame, extract:
      - pelvis_pm: hip/belt cap (y=490..615) so crotch/hips stay 100% solid during wide strides
      - leg_L / leg_R (each split into trouser_pm [hip..ankle] + shoe_pm [ankle..sole] + anchor coords!)
    """
    H, W = noscis_arr.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    a = noscis_arr[..., 3] > 20
    # Find waist center X & ankle Y
    waist_xs = np.nonzero(a[505:560])[1]
    cx = float(np.median(waist_xs)) if len(waist_xs) > 0 else 384.0
    foot_ys = np.nonzero(a)[0]
    sole_y = float(foot_ys.max()) if len(foot_ys) > 0 else 1105.0
    hip_y = 545.0
    knee_y = 805.0
    ankle_y = sole_y - 82.0  # right above brown loafer collar

    # Pelvis cap (soft feather bottom from 580..625, top from 490..515)
    pelvis_w = np.clip((yy - 492.0) / 14.0, 0.0, 1.0) * np.clip((622.0 - yy) / 36.0, 0.0, 1.0)
    pelvis_arr = noscis_arr.copy()
    pelvis_arr[..., 3] = np.clip(pelvis_arr[..., 3].astype(np.float32) * pelvis_w, 0, 255).astype(np.uint8)
    pelvis_pm = to_pm(pelvis_arr)

    def make_single_leg(mask_bool: np.ndarray, side_x: float) -> Dict:
        # Trouser tube: from y=525 down to ankle_y + 18 (soft overlap into shoe collar)
        t_w = (mask_bool.astype(np.float32)
               * np.clip((yy - 515.0) / 16.0, 0.0, 1.0)
               * np.clip((ankle_y + 22.0 - yy) / 18.0, 0.0, 1.0))
        t_arr = noscis_arr.copy()
        t_arr[..., 3] = np.clip(t_arr[..., 3].astype(np.float32) * t_w, 0, 255).astype(np.uint8)
        t_arr[t_arr[..., 3] == 0] = 0

        # Rigid loafer shoe: from ankle_y - 10 down to bottom
        # Keep ONLY the largest connected shoe component so a tiny overlapping toe tip
        # from the other foot in 3/4 views NEVER detaches and floats!
        s_w = mask_bool.astype(np.float32) * np.clip((yy - (ankle_y - 12.0)) / 14.0, 0.0, 1.0)
        s_arr = noscis_arr.copy()
        s_arr[..., 3] = np.clip(s_arr[..., 3].astype(np.float32) * s_w, 0, 255).astype(np.uint8)
        sn, slbl, sstats, _ = cv2.connectedComponentsWithStats((s_arr[..., 3] > 20).astype(np.uint8), connectivity=8)
        if sn > 2:
            best_sid = 1 + int(np.argmax(sstats[1:, cv2.CC_STAT_AREA]))
            s_arr[slbl != best_sid] = 0
        s_arr[s_arr[..., 3] == 0] = 0

        # Measure real centroid of thigh/knee/ankle for this leg
        def col_med(y0, y1, fallback):
            sub = mask_bool[int(y0):int(y1)] & a[int(y0):int(y1)]
            xs = np.nonzero(sub)[1]
            return float(np.median(xs)) if len(xs) > 15 else fallback

        hx = col_med(hip_y - 10, hip_y + 45, side_x)
        kx = col_med(knee_y - 25, knee_y + 25, hx)
        ax = col_med(ankle_y - 25, ankle_y + 10, kx)
        return {
            "trouser_pm": to_pm(t_arr),
            "shoe_pm": to_pm(s_arr),
            "hip": (hx, hip_y),
            "knee": (kx, knee_y),
            "ankle": (ax, ankle_y),
        }

    if d in (2, 6):
        # Pure side profile: the single clean side leg IS both near & far leg!
        full_leg = a & (yy >= 510)
        leg_main = make_single_leg(full_leg, cx)
        return {"mode": "side", "cx": cx, "pelvis_pm": pelvis_pm,
                "leg_a": leg_main, "leg_b": leg_main}
    else:
        # Find exact vertical inner-thigh split seam between Left and Right legs (y=680..1040)
        # Look for column with minimum alpha or darkest luminance seam near cx
        seam_x = np.full(H, cx, dtype=np.float32)
        gray = cv2.cvtColor(noscis_arr[..., :3], cv2.COLOR_RGB2GRAY).astype(np.float32)
        for y in range(620, min(H, int(sole_y) + 1)):
            row_a = np.nonzero(a[y])[0]
            if len(row_a) < 20:
                continue
            lo_x, hi_x = int(row_a[0]), int(row_a[-1])
            mid_lo = max(lo_x + 12, int(cx - 42))
            mid_hi = min(hi_x - 12, int(cx + 42))
            if mid_hi <= mid_lo:
                continue
            # Prefer transparent gap between legs; otherwise darkest crease
            sub_a = noscis_arr[y, mid_lo:mid_hi, 3]
            gaps = np.nonzero(sub_a < 40)[0]
            if len(gaps) > 0:
                seam_x[y] = mid_lo + float(np.mean(gaps))
            else:
                sub_g = gray[y, mid_lo:mid_hi]
                seam_x[y] = mid_lo + float(np.argmin(sub_g))
        # Smooth seam_x vertically so the cut is silky straight
        seam_x[620:] = cv2.GaussianBlur(seam_x[620:, None], (1, 31), 0)[:, 0]
        seam_x[:620] = seam_x[620]

        mask_l = a & (yy >= 510) & (xx <= seam_x[:, None] + 3)
        mask_r = a & (yy >= 510) & (xx >= seam_x[:, None] - 3)
        leg_l = make_single_leg(mask_l, cx - 32.0)
        leg_r = make_single_leg(mask_r, cx + 32.0)
        return {"mode": "split", "cx": cx, "pelvis_pm": pelvis_pm,
                "leg_l": leg_l, "leg_r": leg_r}


def build_running_scissors(out_dir: str, n_frames: int = 16) -> Tuple[Dict, Tuple[int, int]]:
    """Build 8 dirs x 16 frames of REAL photorealistic Kyle sprinting + chopping giant scissors!"""
    front_bgrs = base_mod.read_video_frames(base_mod.VID_FRONT, base_mod.FRONT_FRAME_IDXS)
    noscis_bgrs = base_mod.read_video_frames(base_mod.VID_NO_SCISSORS, base_mod.NO_SCIS_FRAME_IDXS)

    # Expand working canvas horizontally (+180 each side) so wide athletic running strides never clip!
    PAD_X = 180
    PAD_Y = 70

    def pad_arr(arr: np.ndarray) -> np.ndarray:
        h, w = arr.shape[:2]
        out = np.zeros((h + PAD_Y * 2, w + PAD_X * 2, 4), dtype=np.uint8)
        out[PAD_Y:PAD_Y + h, PAD_X:PAD_X + w] = arr
        return out

    grid_rgba = []
    for d in range(N_DIRS):
        f_arr = pad_arr(np.array(base_mod.key_studio_offwhite(front_bgrs[d], True)))
        n_arr = pad_arr(np.array(base_mod.key_studio_offwhite(noscis_bgrs[d], True)))
        H, W = f_arr.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]

        # 1) Upper body + giant front scissors from VID_FRONT (padded coords)
        # Shift split_x by PAD_X inside padded frame
        orig_spec = FRONT_DIR_SPECS[d]
        FRONT_DIR_SPECS[d] = (orig_spec[0], orig_spec[1] + PAD_X, orig_spec[2] + PAD_Y)
        scis_seg = segment_front_blades(f_arr, d)
        FRONT_DIR_SPECS[d] = orig_spec

        # Keep upper torso + head + arms + hands/scissor-handles from VID_FRONT (down to belt y=525+PAD_Y,
        # plus any hands/handles/silver steel extending down to y=660+PAD_Y!)
        rb = f_arr[..., 0].astype(np.int16) - f_arr[..., 2].astype(np.int16)
        is_steel_or_hand = (rb < 26) | (yy < 548 + PAD_Y)
        # Belt sits around y=512+PAD_Y; keep upper body cleanly down to belt + scissor handles in front!
        upper_m = (yy <= 526 + PAD_Y) | ((yy <= 650 + PAD_Y) & (rb < 24) & (f_arr[..., 3] > 20))
        # Also keep Kyle's wrists/hands gripping the scissor rings (skin right around y=510..580)
        if d in (0, 1, 7):
            upper_m |= (yy <= 585 + PAD_Y) & (xx >= 260 + PAD_X) & (xx <= 530 + PAD_X) & (rb > 26) & (f_arr[..., 0] > 140)
        upper_w = cv2.GaussianBlur(upper_m.astype(np.float32), (7, 7), 1.8)
        upper_pm = scis_seg["body_pm"].copy()
        upper_pm *= upper_w[..., None]

        # 2) Clean articulated legs from VID_NO_SCISSORS (padded coords)
        # Adjust extract_leg_parts offsets cleanly by running on unpadded then shifting coords + padding!
        n_unpadded = n_arr[PAD_Y:H - PAD_Y, PAD_X:W - PAD_X]
        legs_raw = extract_leg_parts(n_unpadded, d)

        def pad_pm(pm):
            oh, ow = pm.shape[:2]
            out = np.zeros((oh + PAD_Y * 2, ow + PAD_X * 2, 4), dtype=np.float32)
            out[PAD_Y:PAD_Y + oh, PAD_X:PAD_X + ow] = pm
            return out

        def pad_leg(L):
            return {
                "trouser_pm": pad_pm(L["trouser_pm"]),
                "shoe_pm": pad_pm(L["shoe_pm"]),
                "hip": (L["hip"][0] + PAD_X, L["hip"][1] + PAD_Y),
                "knee": (L["knee"][0] + PAD_X, L["knee"][1] + PAD_Y),
                "ankle": (L["ankle"][0] + PAD_X, L["ankle"][1] + PAD_Y),
            }

        pelvis_pm = pad_pm(legs_raw["pelvis_pm"])
        cx = legs_raw["cx"] + PAD_X
        hip_piv = (cx, 535.0 + PAD_Y)

        if legs_raw["mode"] == "side":
            leg_near = pad_leg(legs_raw["leg_a"])
            leg_far = leg_near
        else:
            leg_l = pad_leg(legs_raw["leg_l"])
            leg_r = pad_leg(legs_raw["leg_r"])

        # Yaw angle in radians: 0=Front(toward cam), 90=Facing Left(-X), 180=Back, 270=Facing Right(+X)
        yaw_deg = d * 45.0
        yaw_rad = math.radians(yaw_deg)
        # Forward horizontal screen vector for this facing direction:
        # d2 (90 deg Left) -> Kyle faces LEFT (-1), d6 (270 deg Right) -> Kyle faces RIGHT (+1)!
        fwd_x = -math.sin(yaw_rad)  # d0: 0, d1: -0.71, d2: -1, d3: -0.71, d4: 0, d5: +0.71, d6: +1, d7: +0.71
        fwd_z = math.cos(yaw_rad)   # d0: +1 (toward cam), d4: -1 (away from cam)

        def render_leg_pose(L: Dict, phase: float, is_far: bool, bounce_y: float) -> np.ndarray:
            """Compute realistic 3D sprint gait projected onto this yaw angle and skin with Bezier + rigid shoe."""
            hx0, hy0 = L["hip"]
            kx0, ky0 = L["knee"]
            ax0, ay0 = L["ankle"]
            thigh_len = math.hypot(kx0 - hx0, ky0 - hy0)
            shin_len = math.hypot(ax0 - kx0, ay0 - ky0)

            # Biomechanical 2D sagittal-plane sprint cycle (angle 0 = straight down, + = forward):
            # Thigh swings +40 deg forward (knee drive) to -32 deg backward (push-off)
            th_ang = math.radians(38.0 * math.sin(phase) + 5.0)
            # Knee flexes 14 deg at front strike up to 74 deg kicking heel back during swing!
            kn_flex = math.radians(16.0 + 58.0 * (0.5 - 0.5 * math.cos(phase + 0.55)))
            sh_ang = th_ang - kn_flex

            # Sagittal coordinates relative to hip (s_fwd > 0 is in front of runner, s_down > 0 is down)
            k_fwd = thigh_len * math.sin(th_ang)
            k_down = thigh_len * math.cos(th_ang)
            a_fwd = k_fwd + shin_len * math.sin(sh_ang)
            a_down = k_down + shin_len * math.cos(sh_ang)

            # Project sagittal forward displacement onto screen X (side/3-4) and perspective depth Z (front/back)
            hx = hx0 + fwd_x * (-6.0 if is_far else 4.0)
            hy = hy0 + bounce_y
            kx = hx + k_fwd * fwd_x
            # In front/back views, forward knee drive lifts higher visually; also add subtle perspective scale
            z_k = k_fwd * fwd_z / max(1.0, thigh_len)  # >0 closer to camera
            z_a = a_fwd * fwd_z / max(1.0, thigh_len + shin_len)
            ky = hy + k_down - abs(fwd_z) * max(0.0, k_fwd) * 0.14
            ax = hx + a_fwd * fwd_x
            ay = hy + a_down - abs(fwd_z) * max(0.0, a_fwd) * 0.12

            # Smooth quadratic Bezier control point right at the knee (pushed slightly outward to keep knee round)
            cx_k = kx + (kx - 0.5 * (hx + ax)) * 0.18
            cy_k = ky + (ky - 0.5 * (hy + ay)) * 0.18

            leg_scale = 1.0 + 0.08 * z_k
            trouser_w = warp_limb_bezier(
                L["trouser_pm"],
                (L["hip"], L["knee"], L["ankle"]),
                ((hx, hy), (cx_k, cy_k), (ax, ay)),
                half_width=92.0,
                scale_w=leg_scale,
            )

            # Rigid brown loafer attached at exact ankle endpoint (ax, ay) with natural foot pitch!
            shoe_pitch_sag = math.degrees(sh_ang) * 0.72 + 12.0 * math.cos(phase)
            shoe_deg = -shoe_pitch_sag * fwd_x  # image rotation matches facing direction
            shoe_sc = 1.0 + 0.11 * z_a
            shoe_w = affine_pm(
                L["shoe_pm"], L["ankle"], shoe_deg,
                dx=(ax - ax0), dy=(ay - ay0),
                sx=shoe_sc, sy=shoe_sc,
            )

            leg_pm = over_pm(trouser_w, shoe_w)
            # Authentic depth shading: far leg or backward-swinging leg is subtly darker
            shade = 0.80 if is_far else (1.0 - 0.12 * max(0.0, -z_a))
            if shade < 0.99:
                leg_pm = tint_pm(leg_pm, (shade, shade, min(1.0, shade * 1.03)))
            return leg_pm

        row = []
        for fi in range(n_frames):
            phase = 2.0 * math.pi * (fi / n_frames)
            # Double-frequency athletic stride bounce (peaks during airborne float twice per cycle)
            bounce_y = -24.0 * abs(math.sin(phase)) + 8.0

            # Forward sprint torso lean: +deg rotates CW (top moves RIGHT/+X), matching fwd_x!
            torso_lean = +9.0 * fwd_x + 2.5 * math.sin(phase) * (1.0 - abs(fwd_x))
            torso_dx = fwd_x * (6.0 + 5.0 * math.cos(2.0 * phase))
            torso_dy = bounce_y + 4.0 * math.sin(2.0 * phase)

            # Render legs in correct Z-order
            comp = np.zeros((H, W, 4), dtype=np.float32)
            if legs_raw["mode"] == "side":
                p_far = render_leg_pose(leg_far, phase + math.pi, is_far=True, bounce_y=bounce_y)
                p_near = render_leg_pose(leg_near, phase, is_far=False, bounce_y=bounce_y)
                pelv_s = affine_pm(pelvis_pm, hip_piv, torso_lean * 0.45, dx=torso_dx * 0.35, dy=bounce_y)
                comp = over_pm(comp, p_far)
                comp = over_pm(comp, pelv_s)
                comp = over_pm(comp, p_near)
            else:
                # Split legs: left runs at `phase`, right runs at `phase + pi`
                # Draw whichever leg is swung further away from camera FIRST!
                z_l = math.sin(phase) * fwd_z
                z_r = math.sin(phase + math.pi) * fwd_z
                p_l = render_leg_pose(leg_l, phase, is_far=(z_l < z_r and abs(fwd_z) > 0.2), bounce_y=bounce_y)
                p_r = render_leg_pose(leg_r, phase + math.pi, is_far=(z_r < z_l and abs(fwd_z) > 0.2), bounce_y=bounce_y)
                pelv_s = affine_pm(pelvis_pm, hip_piv, torso_lean * 0.45, dx=torso_dx * 0.35, dy=bounce_y)
                if z_l < z_r:
                    comp = over_pm(comp, p_l)
                    comp = over_pm(comp, pelv_s)
                    comp = over_pm(comp, p_r)
                else:
                    comp = over_pm(comp, p_r)
                    comp = over_pm(comp, pelv_s)
                    comp = over_pm(comp, p_l)

            # Active scissor chopping WHILE sprinting (2 snappy chomps per 16-frame stride cycle!)
            chop_t = (fi % 8) / 8.0
            # Snappy jaw curve: wide open -> fast slam shut at chop_t=0.5 -> rebound
            chop_u = 0.5 - 0.5 * math.cos(2.0 * math.pi * chop_t)
            chop_u = chop_u ** 1.6  # crisp snap!
            sgn = scis_seg["sgn"]
            piv = scis_seg["piv"]
            # Compute rotated pivot position after torso lean
            rad_l = math.radians(torso_lean)
            rx, ry = piv[0] - hip_piv[0], piv[1] - hip_piv[1]
            piv_dx = torso_dx + (rx * math.cos(rad_l) - ry * math.sin(rad_l) - rx)
            piv_dy = torso_dy + (rx * math.sin(rad_l) + ry * math.cos(rad_l) - ry)

            au = (-14.0 + 24.0 * chop_u) * sgn
            al = (14.0 - 30.0 * chop_u) * sgn
            bl_u = affine_pm(scis_seg["up_pm"], piv, au + torso_lean, dx=piv_dx, dy=piv_dy)
            bl_l = affine_pm(scis_seg["lo_pm"], piv, al + torso_lean, dx=piv_dx, dy=piv_dy)
            up_body = affine_pm(upper_pm, hip_piv, torso_lean, dx=torso_dx, dy=torso_dy)

            comp = over_pm(comp, bl_u)
            comp = over_pm(comp, bl_l)
            comp = over_pm(comp, up_body)

            if chop_u > 0.90:
                glint_pt = (piv[0] + piv_dx + 145.0 * sgn, piv[1] + piv_dy + 6.0)
                comp = draw_glint_pm(comp, glint_pt, radius=32.0, intensity=(chop_u - 0.85) * 6.0)

            row.append(from_pm(comp))
        grid_rgba.append(row)

    grid_im, frame_size = normalize_grid(grid_rgba, target_h=TARGET_H)
    os.makedirs(out_dir, exist_ok=True)
    # Remove any old stale PNGs first
    for old in os.listdir(out_dir):
        if old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(n_frames):
            rel = f"running_scissors/d{d}_f{f}.png"
            grid_im[d][f].save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, frame_size


# ===========================================================================
# 2. OVERHEAD SCISSORS CHOPPING (8 dirs x 12 frames @ 24 FPS)
# ===========================================================================
def build_overhead_scissors(out_dir: str, n_frames: int = 12) -> Tuple[Dict, Tuple[int, int]]:
    bgrs = base_mod.read_video_frames(base_mod.VID_OVERHEAD, base_mod.OVERHEAD_FRAME_IDXS)
    grid_rgba = []

    for d, bgr in enumerate(bgrs):
        arr = np.array(base_mod.key_studio_offwhite(bgr, True))
        H, W = arr.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]

        # Locate exact scissor pivot right above Kyle's raised hands (y=120..360)
        a = arr[..., 3] > 20
        rb = arr[..., 0].astype(np.int16) - arr[..., 2].astype(np.int16)
        steel = a & (yy < 360) & (rb < 24)
        # Find narrowest waist (pivot screw) of steel blades between y=130..280
        best_y, best_w, best_cx = 215.0, 9999, 384.0
        for y in range(135, 285):
            xs = np.nonzero(steel[y])[0]
            if len(xs) < 6:
                continue
            span = int(xs[-1] - xs[0])
            if 10 <= span < best_w:
                best_w = span
                best_y = float(y)
                best_cx = 0.5 * (xs[0] + xs[-1])
        px, py = best_cx, best_y

        blades_zone = steel & (yy <= py + 34)
        body_arr = arr.copy()
        body_arr[blades_zone] = 0
        body_pm = to_pm(body_arr)
        hub_dist = np.hypot(xx - px, yy - py)

        if d in (2, 6):
            # Side profile: two overlapping blades scissoring apart/shut in sagittal plane
            b_arr = np.zeros_like(arr); b_arr[blades_zone] = arr[blades_zone]
            b_pm = to_pm(b_arr)
            row = []
            for fi in range(n_frames):
                u = 0.5 - 0.5 * math.cos(2.0 * math.pi * fi / n_frames)
                u_snap = u ** 1.8  # snappy close!
                spread = 22.0 * (1.0 - u_snap)
                bdy = -8.0 * (1.0 - u_snap) + 12.0 * u_snap
                scy = 1.0 + 0.012 * (1.0 - u_snap) - 0.018 * u_snap
                body_s = affine_pm(body_pm, (384.0, 1110.0), 0.0, dy=bdy, sy=scy)
                b_far = tint_pm(affine_pm(b_pm, (px, py), -spread, dy=bdy), (0.85, 0.85, 0.88))
                b_near = affine_pm(b_pm, (px, py), +spread, dy=bdy)
                comp = over_pm(over_pm(b_far, b_near), body_s)
                if u_snap > 0.90:
                    comp = draw_glint_pm(comp, (px, max(24.0, py - 115.0 + bdy)), 32.0, (u_snap - 0.85) * 6.0)
                row.append(from_pm(comp))
            grid_rgba.append(row)
        else:
            top_band = blades_zone & (yy < py - 35)
            l_mask = blades_zone & ((xx < px) | (hub_dist <= 11))
            r_mask = blades_zone & ((xx >= px) | (hub_dist <= 11))

            def blade_angle(mask):
                ys_m, xs_m = np.nonzero(mask & top_band)
                if len(xs_m) < 10:
                    return 0.0
                return math.degrees(math.atan2(float(np.mean(xs_m) - px), max(10.0, float(py - np.mean(ys_m)))))

            ang_l = blade_angle(l_mask)
            ang_r = blade_angle(r_mask)
            # In affine_pm: positive deg rotates CW in image coords (top moves RIGHT -> +x!)
            # So left blade (ang_l < 0) needs POSITIVE deg to close toward vertical; right blade needs NEGATIVE deg!
            close_l = -ang_l * 0.94
            close_r = -ang_r * 0.94

            l_arr = np.zeros_like(arr); l_arr[l_mask] = arr[l_mask]
            r_arr = np.zeros_like(arr); r_arr[r_mask] = arr[r_mask]
            l_pm, r_pm = to_pm(l_arr), to_pm(r_arr)

            row = []
            for fi in range(n_frames):
                u = 0.5 - 0.5 * math.cos(2.0 * math.pi * fi / n_frames)
                u_snap = u ** 1.75
                # Range from -0.35 (extra-wide anticipation!) to +1.0 (SLAM SHUT!)
                tc = -0.35 + 1.35 * u_snap
                bdy = -9.0 * (1.0 - u_snap) + 12.0 * u_snap
                scy = 1.012 * (1.0 - u_snap) + 0.980 * u_snap
                scx = 0.992 * (1.0 - u_snap) + 1.016 * u_snap

                body_s = affine_pm(body_pm, (384.0, 1110.0), 0.0, dy=bdy, sx=scx, sy=scy)
                bl_l = affine_pm(l_pm, (px, py), close_l * tc, dy=bdy)
                bl_r = affine_pm(r_pm, (px, py), close_r * tc, dy=bdy)
                comp = over_pm(over_pm(body_s, bl_l), bl_r)
                if u_snap > 0.90:
                    comp = draw_glint_pm(comp, (px, max(24.0, py - 125.0 + bdy)), 36.0, (u_snap - 0.85) * 6.2)
                row.append(from_pm(comp))
            grid_rgba.append(row)

    grid_im, frame_size = normalize_grid(grid_rgba, target_h=TARGET_H)
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(n_frames):
            rel = f"overhead_scissors/d{d}_f{f}.png"
            grid_im[d][f].save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, frame_size


# ===========================================================================
# 3. FRONT SCISSORS AGGRESSIVE LUNGE-CHOP (8 dirs x 12 frames @ 24 FPS)
# ===========================================================================
def build_front_scissors(out_dir: str, n_frames: int = 12) -> Tuple[Dict, Tuple[int, int]]:
    bgrs = base_mod.read_video_frames(base_mod.VID_FRONT, base_mod.FRONT_FRAME_IDXS)
    grid_rgba = []
    ankle_piv = (384.0, 1085.0)

    for d, bgr in enumerate(bgrs):
        arr = np.array(base_mod.key_studio_offwhite(bgr, True))
        seg = segment_front_blades(arr, d)
        sgn = seg["sgn"]
        piv = seg["piv"]

        row = []
        for fi in range(n_frames):
            u = 0.5 - 0.5 * math.cos(2.0 * math.pi * fi / n_frames)
            u_snap = u ** 1.85  # snappy metallic chop!
            lean_deg = (-1.6 + 4.8 * u_snap) * sgn
            scy = 1.008 * (1.0 - u_snap) + 0.976 * u_snap
            scx = 0.995 * (1.0 - u_snap) + 1.018 * u_snap
            bdy = -5.0 * (1.0 - u_snap) + 11.0 * u_snap

            rad = math.radians(lean_deg)
            rx, ry = piv[0] - ankle_piv[0], piv[1] - ankle_piv[1]
            ldx = rx * scx * math.cos(rad) - ry * scy * math.sin(rad) - rx
            ldy = rx * scx * math.sin(rad) + ry * scy * math.cos(rad) - ry + bdy

            au = (-15.0 + 25.0 * u_snap) * sgn
            al = (15.0 - 32.0 * u_snap) * sgn
            tuck = -3.0 * sgn

            body_s = affine_pm(seg["body_pm"], ankle_piv, lean_deg, dy=bdy, sx=scx, sy=scy)
            bl_u = affine_pm(seg["up_pm"], piv, au + lean_deg, dx=ldx + tuck, dy=ldy)
            bl_l = affine_pm(seg["lo_pm"], piv, al + lean_deg, dx=ldx + tuck, dy=ldy)
            comp = over_pm(over_pm(bl_u, bl_l), body_s)

            if u_snap > 0.90:
                glint_pt = (piv[0] + ldx + 150.0 * sgn, piv[1] + ldy + 8.0)
                comp = draw_glint_pm(comp, glint_pt, 36.0, (u_snap - 0.85) * 6.5)
            row.append(from_pm(comp))
        grid_rgba.append(row)

    grid_im, frame_size = normalize_grid(grid_rgba, target_h=TARGET_H)
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(n_frames):
            rel = f"front_scissors/d{d}_f{f}.png"
            grid_im[d][f].save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, frame_size


# ===========================================================================
# 4. ALIVE NO-SCISSORS IDLE / WANDER (8 dirs x 12 frames @ 16 FPS)
# ===========================================================================
def build_no_scissors(out_dir: str, n_frames: int = 12) -> Tuple[Dict, Tuple[int, int]]:
    bgrs = base_mod.read_video_frames(base_mod.VID_NO_SCISSORS, base_mod.NO_SCIS_FRAME_IDXS)
    grid_rgba = []
    ankle_piv = (384.0, 1095.0)

    for d, bgr in enumerate(bgrs):
        arr = np.array(base_mod.key_studio_offwhite(bgr, True))
        pm = to_pm(arr)
        row = []
        for fi in range(n_frames):
            ph = 2.0 * math.pi * (fi / n_frames)
            sway = 1.6 * math.sin(ph)
            breath_y = 1.0 + 0.011 * math.sin(2.0 * ph)
            breath_x = 1.0 - 0.006 * math.sin(2.0 * ph)
            dx = 4.0 * math.sin(ph)
            out_pm = affine_pm(pm, ankle_piv, sway, dx=dx, sx=breath_x, sy=breath_y)
            row.append(from_pm(out_pm))
        grid_rgba.append(row)

    grid_im, frame_size = normalize_grid(grid_rgba, target_h=TARGET_H)
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(n_frames):
            rel = f"no_scissors/d{d}_f{f}.png"
            grid_im[d][f].save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, frame_size


# ===========================================================================
# 5. REALISTIC US MONEY & COINS (from photorealistic studio plates!)
# ===========================================================================
def key_pure_white(rgb: np.ndarray, thresh: float = 240.0) -> np.ndarray:
    """Clean border-flood white keyer with soft AA edge for studio money/coin plates."""
    h, w = rgb.shape[:2]
    arr = rgb.astype(np.float32)
    lo = arr.min(axis=2)
    hi = arr.max(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    cand = ((lo > thresh) & (sat < 0.06)).astype(np.uint8)
    _, lbl = cv2.connectedComponents(cand, connectivity=4)
    border = set(np.unique(lbl[0, :])) | set(np.unique(lbl[-1, :])) | set(np.unique(lbl[:, 0])) | set(np.unique(lbl[:, -1]))
    border.discard(0)
    bg = np.isin(lbl, list(border))
    fg = (~bg).astype(np.uint8)
    dist_in = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    dist_out = cv2.distanceTransform(1 - fg, cv2.DIST_L2, 5)
    alpha = np.clip((dist_in - dist_out + 0.4) / 1.5, 0.0, 1.0)
    # Decontaminate white fringe
    semi = (alpha > 0.03) & (alpha < 0.98)
    clean = arr.copy()
    clean[semi] = np.clip((arr[semi] - (1.0 - alpha[semi, None]) * 255.0) / np.maximum(alpha[semi, None], 0.2), 0, 255)
    clean[alpha <= 0.03] = 0
    alpha[alpha <= 0.03] = 0
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(clean), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    return out


def tight_crop(rgba: np.ndarray, pad: int = 4) -> np.ndarray:
    ys, xs = np.nonzero(rgba[..., 3] > 20)
    if len(xs) == 0:
        return rgba
    y0, y1 = max(0, int(ys.min()) - pad), min(rgba.shape[0], int(ys.max()) + pad + 1)
    x0, x1 = max(0, int(xs.min()) - pad), min(rgba.shape[1], int(xs.max()) + pad + 1)
    return rgba[y0:y1, x0:x1]


def make_flutter_bill(flat_rgba: np.ndarray, phase: float, flip_y: float = 1.0,
                      out_wh: Tuple[int, int] = (200, 112)) -> Image.Image:
    """Warp a real photographic US bill into a smooth 3D fluttering S-wave with paper lighting."""
    src = cv2.resize(flat_rgba, (176, 76), interpolation=cv2.INTER_AREA)
    sh, sw = src.shape[:2]
    ow, oh = out_wh
    # Build inverse map on output canvas
    yy, xx = np.mgrid[0:oh, 0:ow].astype(np.float32)
    cx, cy = ow * 0.5, oh * 0.5
    nx = (xx - cx) / (sw * 0.5)  # -1..1 across bill width
    # 3D S-wave vertical displacement + perspective height squash when flipping
    amp = 13.0 * math.sin(phase)
    wave_y = amp * np.sin(nx * math.pi * 1.15 + phase * 1.5)
    scale_y = max(0.24, abs(flip_y))
    u = (xx - cx) + sw * 0.5
    v = ((yy - cy - wave_y) / scale_y) + sh * 0.5

    pm = to_pm(src)
    warped = cv2.remap(pm, u.astype(np.float32), v.astype(np.float32),
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    # Add realistic directional paper-fold shading based on wave slope!
    slope = amp * math.pi * 1.15 * np.cos(nx * math.pi * 1.15 + phase * 1.5) / (sw * 0.5)
    shade = np.clip(1.0 - slope * 0.55 - (1.0 - scale_y) * 0.22, 0.72, 1.16)
    warped[..., :3] = np.clip(warped[..., :3] * shade[..., None], 0.0, 255.0)
    return Image.fromarray(from_pm(warped), "RGBA")


def make_spinning_coin_frames(coin_rgba: np.ndarray, edge_rgb: Tuple[int, int, int],
                              size: int = 128, n_frames: int = 8) -> List[Image.Image]:
    """Build realistic 3D spinning US coin frames with visible metallic edge thickness & glint."""
    # Ensure square tight-cropped coin face
    sq = cv2.resize(coin_rgba, (size - 16, size - 16), interpolation=cv2.INTER_AREA)
    ch, cw = sq.shape[:2]
    R = cw * 0.5
    out_list = []

    for i in range(n_frames):
        ang = (i / n_frames) * math.pi  # 0..pi full flip loop (0=face, pi/2=edge-on!)
        cos_a = math.cos(ang)
        vis_w = max(2, int(round(abs(cos_a) * cw)))
        # Edge rim thickness visible as coin turns sideways (sin_a * 11px)
        edge_thick = int(round(abs(math.sin(ang)) * 12.0))

        canvas = np.zeros((size, size, 4), dtype=np.float32)
        cy = size // 2
        cx = size // 2

        # 1) Draw true ELLIPTICAL reeded metallic coin rim behind the tilted face (ZERO box artifacts!)
        y0 = cy - ch // 2
        y1 = y0 + ch
        if edge_thick > 0:
            # Resize coin alpha silhouette to (vis_w, ch) so edge rim strictly follows the circular rim!
            sil_alpha = cv2.resize(sq[..., 3].astype(np.float32) / 255.0, (vis_w, ch), interpolation=cv2.INTER_AREA)
            yy_col = np.arange(y0, y1, dtype=np.float32)
            dy = (yy_col - cy) / R
            reed = 0.88 + 0.12 * np.sin(yy_col * 1.9)
            cyl = 0.52 + 0.56 * np.sqrt(np.maximum(0.0, 1.0 - np.clip(dy * dy, 0.0, 1.0)))
            edge_dir = 1 if cos_a >= 0 else -1
            for step in range(edge_thick, 0, -1):
                ox = int(round(cx + edge_dir * (step - edge_thick * 0.5)))
                x0_e = ox - vis_w // 2
                x1_e = x0_e + vis_w
                sx0 = max(0, -x0_e)
                sx1 = min(vis_w, size - x0_e)
                dx0 = max(0, x0_e)
                dx1 = dx0 + (sx1 - sx0)
                if dx1 <= dx0:
                    continue
                depth_sh = 0.68 + 0.32 * (1.0 - step / max(1.0, float(edge_thick)))
                shade_col = (cyl * reed * depth_sh)[:, None]
                a_slice = sil_alpha[:, sx0:sx1]
                rim_pm = np.zeros((ch, dx1 - dx0, 4), dtype=np.float32)
                rim_pm[..., 0] = np.clip(edge_rgb[0] * shade_col, 0, 255) * a_slice
                rim_pm[..., 1] = np.clip(edge_rgb[1] * shade_col, 0, 255) * a_slice
                rim_pm[..., 2] = np.clip(edge_rgb[2] * shade_col, 0, 255) * a_slice
                rim_pm[..., 3] = a_slice
                canvas[y0:y1, dx0:dx1] = over_pm(canvas[y0:y1, dx0:dx1], rim_pm)

        # 2) Draw foreshortened photographic coin face with dynamic metallic specular sweep!
        if vis_w >= 4:
            face = sq if cos_a >= 0 else cv2.flip(sq, 1)
            face_pm = to_pm(face)
            face_s = cv2.resize(face_pm, (vis_w, ch), interpolation=cv2.INTER_AREA)
            fx = np.linspace(-1.0, 1.0, vis_w, dtype=np.float32)
            fy = np.linspace(-1.0, 1.0, ch, dtype=np.float32)
            FXX, FYY = np.meshgrid(fx, fy)
            spec_pos = math.sin(ang * 2.0) * 0.7
            spec = np.exp(-((FXX + FYY * 0.45 - spec_pos) ** 2) * 5.5) * 0.32
            dim = 0.72 + 0.28 * abs(cos_a)
            face_s[..., :3] = np.clip(face_s[..., :3] * dim + spec[..., None] * 255.0 * face_s[..., 3:4], 0, 255)

            x0 = cx - vis_w // 2
            canvas[y0:y1, x0:x0 + vis_w] = over_pm(canvas[y0:y1, x0:x0 + vis_w], face_s)

        out_list.append(Image.fromarray(from_pm(canvas), "RGBA"))
    return out_list


def build_realistic_cash_fx(out_dir: str) -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))

    # --- A. US $100 BILLS (from 2x2 studio plate) ---
    b_rgb = np.asarray(Image.open(US_BILLS_PLATE).convert("RGB"))
    bh, bw = b_rgb.shape[:2]
    b_rgba = key_pure_white(b_rgb, thresh=238.0)

    # Extract all 4 quadrants cleanly
    q_front = tight_crop(b_rgba[:bh // 2, :bw // 2], pad=2)
    q_wave = tight_crop(b_rgba[:bh // 2, bw // 2:], pad=4)
    q_back = tight_crop(b_rgba[bh // 2:, :bw // 2], pad=2)
    q_fold = tight_crop(b_rgba[bh // 2:, bw // 2:], pad=4)

    def fit_box(arr: np.ndarray, box_wh: Tuple[int, int] = (200, 112)) -> Image.Image:
        im = Image.fromarray(arr, "RGBA")
        im.thumbnail((box_wh[0] - 8, box_wh[1] - 8), Image.LANCZOS)
        c = Image.new("RGBA", box_wh, (0, 0, 0, 0))
        c.paste(im, ((box_wh[0] - im.width) // 2, (box_wh[1] - im.height) // 2), im)
        return c

    bill_imgs = [
        ("bill_0_front.png",  fit_box(q_front)),
        ("bill_1_wave_a.png", fit_box(q_wave)),
        ("bill_2_wave_b.png", make_flutter_bill(q_front, phase=1.2, flip_y=0.86)),
        ("bill_3_flip_a.png", make_flutter_bill(q_front, phase=2.1, flip_y=0.45)),
        ("bill_4_back.png",   fit_box(q_back)),
        ("bill_5_back_w.png", make_flutter_bill(q_back,  phase=0.9, flip_y=0.88)),
        ("bill_6_folded.png", fit_box(q_fold)),
        ("bill_7_flip_b.png", make_flutter_bill(q_back,  phase=2.4, flip_y=0.50)),
    ]
    bill_paths = []
    for fn, im in bill_imgs:
        im.save(os.path.join(out_dir, fn))
        bill_paths.append(f"cash_fx/{fn}")
    # Also save backwards-compatible names used by Pocket Kyle viewmodel throw (`bill_front.png`, `bill_bent1.png`)!
    bill_imgs[0][1].save(os.path.join(out_dir, "bill_front.png"))
    bill_imgs[1][1].save(os.path.join(out_dir, "bill_bent1.png"))
    bill_imgs[5][1].save(os.path.join(out_dir, "bill_bent2.png"))
    bill_imgs[4][1].save(os.path.join(out_dir, "bill_back.png"))

    # --- B. REAL 2024 US SILVER QUARTER & SACAGAWEA GOLD DOLLAR ---
    c_rgb = np.asarray(Image.open(US_COINS_PLATE).convert("RGB"))
    ch, cw = c_rgb.shape[:2]
    c_rgba = key_pure_white(c_rgb, thresh=238.0)

    q_silver = tight_crop(c_rgba[:, :cw // 2], pad=2)
    q_gold = tight_crop(c_rgba[:, cw // 2:], pad=2)

    quarter_frames = make_spinning_coin_frames(q_silver, edge_rgb=(176, 178, 184), size=128, n_frames=8)
    gold_frames = make_spinning_coin_frames(q_gold, edge_rgb=(196, 152, 68), size=128, n_frames=8)

    quarter_paths, gold_paths = [], []
    for i, im in enumerate(quarter_frames):
        fn = f"quarter_{i}.png"
        im.save(os.path.join(out_dir, fn))
        quarter_paths.append(f"cash_fx/{fn}")
    for i, im in enumerate(gold_frames):
        fn = f"gold_dollar_{i}.png"
        im.save(os.path.join(out_dir, fn))
        gold_paths.append(f"cash_fx/{fn}")
    # Backwards-compat coin_0..3 pointing to real Sacagawea gold dollar!
    for i in range(4):
        gold_frames[i * 2].save(os.path.join(out_dir, f"coin_{i}.png"))

    return {
        "bills": bill_paths,
        "quarters": quarter_paths,
        "gold_dollars": gold_paths,
    }


# ===========================================================================
# Audit Sheet Generator (visual verification before showcase build!)
# ===========================================================================
def write_audits(manifest: Dict):
    bg = (42, 38, 35)
    # 1) 8-dir overview + realistic US currency row
    rows = []
    for st in ("running_scissors", "overhead_scissors", "front_scissors", "no_scissors"):
        row = []
        for d in range(8):
            # Pick mid-stride / mid-chop expressive frame!
            f_idx = 3 if st == "running_scissors" else (5 if "scissors" in st else 0)
            p = os.path.join(OUT_DIR, manifest["states"][st]["directions"][str(d)][f_idx])
            im = Image.open(p).convert("RGBA")
            c = Image.new("RGB", (180, 210), bg)
            im.thumbnail((170, 200), Image.LANCZOS)
            c.paste(im, ((180 - im.width) // 2, 210 - im.height - 4), im)
            row.append(np.asarray(c))
        rows.append(np.hstack(row))

    # Row 5: Realistic US $100 bills (4) + Silver Quarter (2) + Gold Dollar (2)
    cash_picks = [
        manifest["cash_fx"]["bills"][0],
        manifest["cash_fx"]["bills"][1],
        manifest["cash_fx"]["bills"][4],
        manifest["cash_fx"]["bills"][6],
        manifest["cash_fx"]["quarters"][0],
        manifest["cash_fx"]["quarters"][2],
        manifest["cash_fx"]["gold_dollars"][0],
        manifest["cash_fx"]["gold_dollars"][2],
    ]
    crow = []
    for rel in cash_picks:
        im = Image.open(os.path.join(OUT_DIR, rel)).convert("RGBA")
        c = Image.new("RGB", (180, 130), bg)
        im.thumbnail((164, 114), Image.LANCZOS)
        c.paste(im, ((180 - im.width) // 2, (130 - im.height) // 2), im)
        crow.append(np.asarray(c))
    rows.append(np.hstack(crow))
    Image.fromarray(np.vstack(rows)).save(os.path.join(OUT_DIR, "_audit_custom_overview.jpg"), quality=92)

    # 2) Frame-by-frame motion audit for Running (side d2, 3/4 d1, front d0) + Overhead (d0) + Front Chop (d0)
    arows = []
    for st, d, picks in [
        ("running_scissors", 2, [0, 2, 4, 6, 8, 10, 12, 14]),
        ("running_scissors", 1, [0, 2, 4, 6, 8, 10, 12, 14]),
        ("running_scissors", 0, [0, 2, 4, 6, 8, 10, 12, 14]),
        ("overhead_scissors", 0, [0, 2, 4, 5, 6, 7, 9, 11]),
        ("front_scissors", 0, [0, 2, 4, 5, 6, 7, 9, 11]),
    ]:
        r = []
        for fi in picks:
            p = os.path.join(OUT_DIR, manifest["states"][st]["directions"][str(d)][fi])
            im = Image.open(p).convert("RGBA")
            c = Image.new("RGB", (180, 210), bg)
            im.thumbnail((170, 200), Image.LANCZOS)
            c.paste(im, ((180 - im.width) // 2, 210 - im.height - 4), im)
            r.append(np.asarray(c))
        arows.append(np.hstack(r))
    Image.fromarray(np.vstack(arows)).save(os.path.join(OUT_DIR, "_audit_custom_motion.jpg"), quality=92)
    print("Wrote _audit_custom_overview.jpg and _audit_custom_motion.jpg")


def main():
    print("1/5 Building realistic US $100 bills + US Silver Quarter + Sacagawea Gold Dollar...")
    cash_fx = build_realistic_cash_fx(os.path.join(OUT_DIR, "cash_fx"))

    print("2/5 Building custom photorealistic Running w/ Scissors (8 dirs x 16f @ 24 FPS)...")
    run_paths, run_sz = build_running_scissors(os.path.join(OUT_DIR, "running_scissors"), n_frames=16)

    print("3/5 Building Overhead Scissors Chopping (8 dirs x 12f @ 24 FPS)...")
    ov_paths, ov_sz = build_overhead_scissors(os.path.join(OUT_DIR, "overhead_scissors"), n_frames=12)

    print("4/5 Building Front Scissors Lunge-Chop (8 dirs x 12f @ 24 FPS)...")
    fr_paths, fr_sz = build_front_scissors(os.path.join(OUT_DIR, "front_scissors"), n_frames=12)

    print("5/5 Building Alive No-Scissors Idle (8 dirs x 12f @ 16 FPS)...")
    no_paths, no_sz = build_no_scissors(os.path.join(OUT_DIR, "no_scissors"), n_frames=12)

    manifest = {
        "version": 2,
        "sprite_height": TARGET_H,
        "directions": DIR_INFO,
        "states": {
            "running_scissors": {
                "title": "Running w/ Chopping Scissors",
                "fps": 24,
                "frame_duration_ms": 42,
                "num_dirs": N_DIRS,
                "num_frames": 16,
                "frame_size": list(run_sz),
                "directions": run_paths,
            },
            "overhead_scissors": {
                "title": "Overhead Scissors Chop",
                "fps": 24,
                "frame_duration_ms": 42,
                "num_dirs": N_DIRS,
                "num_frames": 12,
                "frame_size": list(ov_sz),
                "directions": ov_paths,
            },
            "front_scissors": {
                "title": "Front Lunge-Chop",
                "fps": 24,
                "frame_duration_ms": 42,
                "num_dirs": N_DIRS,
                "num_frames": 12,
                "frame_size": list(fr_sz),
                "directions": fr_paths,
            },
            "no_scissors": {
                "title": "No Scissors Idle",
                "fps": 16,
                "frame_duration_ms": 62,
                "num_dirs": N_DIRS,
                "num_frames": 12,
                "frame_size": list(no_sz),
                "directions": no_paths,
            },
        },
        "cash_fx": cash_fx,
    }
    mpath = os.path.join(OUT_DIR, "manifest.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    write_audits(manifest)
    total = 8 * (16 + 12 + 12 + 12) + 8 + 8 + 8
    print(f"Done! Built {total} HD RGBA sprites + manifest.json in {OUT_DIR}")


if __name__ == "__main__":
    main()
