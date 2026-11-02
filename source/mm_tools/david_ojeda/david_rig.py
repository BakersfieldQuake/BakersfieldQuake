"""Photorealistic 360° Rigging, Real-Video Facial Expression Compositing,
Adaptive 3-Bone Skeletal Running, Money-Bag Heist, and 3D Casino Slot Machine Engine
for David Ojeda & the 3 Running Pregnant Hispanic Women (BakersfieldQuake)."""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from paul_dennis_rig import (
    CANVAS_H,
    CANVAS_W,
    GROUND_Y,
    TOP_Y,
    alpha_over,
    crop_normalize_view,
    extend_top_upward,
    inpaint_fabric_region,
    key_magenta_studio,
    mirror_canvas_horiz,
    sample_run_profile,
    seg_dist_grid,
    shade_rgba,
    warp_limb_3bone,
    warp_rigid_rgba,
)

MOD_DIR = TOOLS_DIR.parent.parent
REF_DIR = TOOLS_DIR / "ref" / "david_ojeda"

# Stage dimensions for high-res showcase & 360° scenes (8:9 aspect -> 256x288 / 256x256 SPR32)
STAGE_W = 480
STAGE_H = 540
STAGE_CX = STAGE_W // 2
STAGE_GY = 492


# ---------------------------------------------------------------------------
# 1. Premultiplied Resizing & 3D Camera Projection Helpers
# ---------------------------------------------------------------------------

def resize_rgba_premul(rgba: np.ndarray, tw: int, th: int) -> np.ndarray:
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.clip(np.round(np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)), 0, 255).astype(np.uint8)
    pm_im = Image.fromarray(pm, "RGBA").resize((max(1, tw), max(1, th)), Image.Resampling.LANCZOS)
    p = np.asarray(pm_im, dtype=np.float32)
    pa = p[..., 3:4] / 255.0
    rgb = np.where(pa > 1e-3, p[..., :3] / np.maximum(pa, 1e-3), 0.0)
    a_out = np.where(p[..., 3] < 8.0, 0.0, p[..., 3])
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(a_out), 0, 255).astype(np.uint8),
    ])


def paste_rgba_pil(
    canvas: Image.Image,
    im_rgba: np.ndarray | Image.Image,
    cx: float,
    cy: float,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    rot_deg: float = 0.0,
    alpha_mul: float = 1.0,
    anchor_bottom: bool = False,
) -> None:
    arr = im_rgba if isinstance(im_rgba, np.ndarray) else np.asarray(im_rgba, dtype=np.uint8)
    if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
        nw = max(2, int(round(arr.shape[1] * scale_x)))
        nh = max(2, int(round(arr.shape[0] * scale_y)))
        arr = resize_rgba_premul(arr, nw, nh)
    if alpha_mul < 0.995:
        arr = arr.copy()
        arr[..., 3] = np.clip(np.round(arr[..., 3].astype(np.float32) * alpha_mul), 0, 255).astype(np.uint8)
    pil_im = Image.fromarray(arr, "RGBA")
    if abs(rot_deg) > 0.25:
        # Rotate via premultiplied alpha so edges stay dark-halo-free
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
    ox = int(round(cx - pil_im.width * 0.5))
    oy = int(round(cy - pil_im.height)) if anchor_bottom else int(round(cy - pil_im.height * 0.5))
    if ox >= canvas.width or oy >= canvas.height or ox + pil_im.width <= 0 or oy + pil_im.height <= 0:
        return
    canvas.alpha_composite(pil_im, (ox, oy))


def project_3d(lx: float, ly: float, lz: float, d_idx: int, cx: float = STAGE_CX, gy: float = STAGE_GY) -> tuple[float, float, float, float]:
    """Projects character-local 3D point (lx=forward, ly=left, lz=up) onto screen (sx, sy, dz, persp_scale)
    matching Quake SPR32 customizeentityforclient d_idx = 0..7:
      d=0: Front (0°)         d=2: Left Profile (90°, nose -X)    d=4: Back (180°)    d=6: Right Profile (270°, nose +X)
      dz < 0 => CLOSER to camera (in front of character)
      dz > 0 => FURTHER from camera (behind character)
    """
    phi = math.radians(d_idx * 45.0)
    sx = cx + (-lx * math.sin(phi) + ly * math.cos(phi))
    dz = -lx * cos_deg(d_idx * 45.0) - ly * math.sin(phi)
    sy = gy - lz + dz * 0.14
    sc = float(np.clip(1.0 - 0.0011 * dz, 0.80, 1.20))
    return sx, sy, dz, sc


def cos_deg(deg: float) -> float:
    return math.cos(math.radians(deg))


def draw_contact_shadow(canvas: Image.Image, cx: float, gy: float, rx: float = 52.0, ry: float = 11.0, alpha: int = 88) -> None:
    w = max(12, int(rx * 2 + 24))
    h = max(8, int(ry * 2 + 18))
    sub = np.zeros((h, w, 4), dtype=np.uint8)
    cv2.ellipse(sub, (w // 2, h // 2), (int(rx), int(ry)), 0, 0, 360, (8, 10, 15, int(alpha)), -1, cv2.LINE_AA)
    sub = cv2.GaussianBlur(sub, (15, 15), 4.2)
    canvas.alpha_composite(Image.fromarray(sub, "RGBA"), (int(round(cx - w * 0.5)), int(round(gy - h * 0.5))))


# ---------------------------------------------------------------------------
# 2. David Ojeda Real-Video Expression Grafting (Shock "O" & Big Casino Grin)
# ---------------------------------------------------------------------------

def apply_david_video_expression(base_480x640: np.ndarray, d_idx: int, mode: str) -> np.ndarray:
    """Applies David Ojeda's real video facial expressions ('shock' wide-eyed O-mouth from v1_run,
    or 'grin' beaming toothy smile from v2_robe) using exact sub-pixel 3-point landmark affine
    registration onto the normalized 480x640 studio portrait!"""
    if mode == "neutral" or d_idx in (3, 4, 5):
        return base_480x640.copy()

    out = base_480x640.copy()
    if d_idx == 0:
        # Exact sub-pixel landmarks measured on normalized 480x640 studio front (`n0`):
        #   left pupil = (225.0, 79.0), right pupil = (254.0, 79.0), mouth center = (240.0, 104.0)
        dst_tri = np.array([[225.0, 79.0], [254.0, 79.0], [240.0, 104.5]], dtype=np.float32)

        if mode == "shock":
            src_im = Image.open(REF_DIR / "david_head_shock_solo.png").convert("RGB")
            # Measured on 390x420 david_head_shock_solo.png (automatically corrects 5.5° head tilt!):
            src_tri = np.array([[225.0, 174.0], [308.0, 182.0], [258.0, 276.0]], dtype=np.float32)
        else:  # "grin"
            src_im = Image.open(REF_DIR / "david_grin_tight.png").convert("RGB")
            # Measured on 160x170 david_grin_tight.png:
            src_tri = np.array([[75.0, 74.0], [104.0, 75.0], [89.5, 101.0]], dtype=np.float32)

        src_arr = np.asarray(src_im, dtype=np.float32)
        M = cv2.getAffineTransform(src_tri, dst_tri)
        warped = cv2.warpAffine(src_arr, M, (CANVAS_W, CANVAS_H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

        # Match skin/beard luminance & chroma inside the cheek/brow zone so lighting is 100% seamless!
        yg, xg = np.mgrid[0:CANVAS_H, 0:CANVAS_W].astype(np.float32)
        cx_f, y_eye, y_mouth = 240.0, 79.0, 104.5
        oval = ((xg - cx_f) / 26.0) ** 2 + ((yg - 90.0) / 25.0) ** 2
        stat_m = (oval < 0.85) & (out[..., 3] > 220)
        if np.sum(stat_m) > 40:
            tgt_rgb = out[..., :3].astype(np.float32)
            for c in range(3):
                t_mu, t_sd = float(tgt_rgb[stat_m, c].mean()), float(tgt_rgb[stat_m, c].std() + 1e-4)
                s_mu, s_sd = float(warped[stat_m, c].mean()), float(warped[stat_m, c].std() + 1e-4)
                warped[..., c] = np.clip((warped[..., c] - s_mu) * (0.80 * t_sd / s_sd + 0.20) + t_mu, 0.0, 255.0)

        # Soft-feathered expression mask strictly over mouth/mustache interior + subtle brow/eye expression
        mouth_oval = ((xg - cx_f) / 11.5) ** 2 + ((yg - (y_mouth + 0.5)) / 9.5) ** 2
        w_m = np.clip(1.30 - mouth_oval, 0.0, 1.0)
        if mode == "shock":
            eye_oval = ((xg - cx_f) / 21.0) ** 2 + ((yg - (y_eye - 1.5)) / 9.5) ** 2
            w_e = np.clip(1.15 - eye_oval, 0.0, 1.0) * 0.72
        else:
            w_e = np.zeros_like(w_m)
        w_blend = cv2.GaussianBlur(np.maximum(w_m, w_e).astype(np.float32), (7, 7), 1.8)
        w_blend *= (out[..., 3].astype(np.float32) / 255.0)

        blended = out[..., :3].astype(np.float32) * (1.0 - w_blend[..., None]) + warped * w_blend[..., None]
        out[..., :3] = np.clip(np.round(blended), 0, 255).astype(np.uint8)
        return out

    # Exact measured lip-line coordinates on 45°/315° (`n1`: 213, 104) and 90°/270° (`n2`: 202, 105),
    # blended softly inside the alpha silhouette so it looks 100% organic!
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    if d_idx in (1, 7):
        x_m = 213.0 if d_idx == 1 else (CANVAS_W - 213.0)
        y_m = 104.0
        if mode == "shock":
            dr.ellipse([x_m - 4.2, y_m - 4.8, x_m + 4.2, y_m + 5.2], fill=(32, 14, 16, 235), outline=(22, 16, 16, 220), width=1)
            dr.ellipse([x_m - 2.6, y_m + 0.8, x_m + 2.6, y_m + 3.8], fill=(162, 78, 78, 215))
        else:
            dr.chord([x_m - 6.0, y_m - 3.8, x_m + 6.0, y_m + 4.5], start=0, end=180, fill=(235, 232, 226, 225), outline=(42, 26, 26, 195))
    elif d_idx in (2, 6):
        x_m = 203.0 if d_idx == 2 else (CANVAS_W - 203.0)
        y_m = 105.0
        if mode == "shock":
            dr.ellipse([x_m - 2.8, y_m - 4.0, x_m + 2.8, y_m + 4.2], fill=(32, 14, 16, 225))
        else:
            dr.ellipse([x_m - 3.2, y_m - 2.0, x_m + 3.2, y_m + 2.4], fill=(228, 225, 220, 210))

    ov_arr = np.asarray(overlay.filter(ImageFilter.GaussianBlur(0.65)), dtype=np.float32)
    # Clip strictly to existing head alpha so nothing ever sticks outside the profile contour!
    ov_a = (ov_arr[..., 3:4] / 255.0) * (out[..., 3:4].astype(np.float32) / 255.0)
    out[..., :3] = np.clip(np.round(out[..., :3].astype(np.float32) * (1.0 - ov_a) + ov_arr[..., :3] * ov_a), 0, 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------
# 3. Body-Adaptive 3-Bone Skeletal Running Rig (Works for Stocky David & 3 Pregnant Women!)
# ---------------------------------------------------------------------------

def _auto_front_back_seams(base_rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    """Automatically traces left & right arm-to-torso air-gap valleys and crotch/hip split row
    on any normalized 480x640 front or back character plate!"""
    H, W = base_rgba.shape[:2]
    a = base_rgba[..., 3] > 28
    cx = 240

    # Find left gap (130..215) and right gap (265..350) across rows y = 245..365
    l_pts_y, l_pts_x = [], []
    r_pts_y, r_pts_x = [], []
    for y in range(245, 368, 4):
        xs = np.nonzero(a[y])[0]
        if len(xs) < 10:
            continue
        for k in range(len(xs) - 1):
            if xs[k + 1] - xs[k] >= 2:
                gx = 0.5 * (xs[k] + xs[k + 1])
                if 135 <= gx <= 212:
                    l_pts_y.append(y)
                    l_pts_x.append(gx)
                elif 268 <= gx <= 345:
                    r_pts_y.append(y)
                    r_pts_x.append(gx)

    yg_1d = np.arange(H, dtype=np.float32)
    if len(l_pts_y) >= 3:
        x_cut_l = np.interp(yg_1d, l_pts_y, l_pts_x).astype(np.float32)
        # Slope slightly outward up toward shoulder armpit above first gap
        y0_l, x0_l = float(l_pts_y[0]), float(l_pts_x[0])
        above = yg_1d < y0_l
        x_cut_l[above] = x0_l + np.clip((y0_l - yg_1d[above]) * 0.08, 0.0, 8.0)
    else:
        x_cut_l = np.full(H, 174.0, dtype=np.float32)

    if len(r_pts_y) >= 3:
        x_cut_r = np.interp(yg_1d, r_pts_y, r_pts_x).astype(np.float32)
        y0_r, x0_r = float(r_pts_y[0]), float(r_pts_x[0])
        above = yg_1d < y0_r
        x_cut_r[above] = x0_r - np.clip((y0_r - yg_1d[above]) * 0.08, 0.0, 8.0)
    else:
        x_cut_r = np.full(H, 306.0, dtype=np.float32)

    # Detect inseam air gap between thighs (x = 225..255, y = 335..440) to place hip split cleanly above crotch!
    y_crotch = 368
    for y in range(340, 445):
        mid_empty = np.sum(~a[y, 232:249])
        if mid_empty >= 3 and np.any(a[y, 185:232]) and np.any(a[y, 249:295]):
            y_crotch = y
            break
    y_hip = max(336, min(366, y_crotch - 18))
    return x_cut_l[:, None], x_cut_r[:, None], y_hip


def render_adaptive_run_frame(
    base_rgba: np.ndarray,
    d_idx: int,
    frame_idx: int,
    n_frames: int = 8,
    speed_boost: float = 1.0,
) -> np.ndarray:
    """Synthesizes frame `frame_idx` of an `n_frames` running cycle at direction `d_idx` (0..7)
    adaptively preserving stocky torsos AND prominent pregnant belly bumps across all 8 angles!"""
    if d_idx in (5, 6, 7):
        canon_d = 8 - d_idx  # 5->3 (135°), 6->2 (90°), 7->1 (45°)
        canon_base = mirror_canvas_horiz(base_rgba)
        # Shift phase by half-cycle so left/right legs stay world-consistent across mirror!
        canon_fr = render_adaptive_run_frame(canon_base, canon_d, (frame_idx + n_frames // 2) % n_frames, n_frames, speed_boost)
        return mirror_canvas_horiz(canon_fr)

    H, W = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]

    if d_idx in (0, 4):
        is_back = (d_idx == 4)
        x_cut_l, x_cut_r, y_hip = _auto_front_back_seams(base_rgba)
        arm_l_mask = (xg < x_cut_l) & (yg >= 160) & (yg <= 405) & (base_rgba[..., 3] > 0)
        arm_r_mask = (xg > x_cut_r) & (yg >= 160) & (yg <= 405) & (base_rgba[..., 3] > 0)

        overlap = 9.0 * (1.0 - np.clip((yg.astype(np.float32) - 235.0) / 55.0, 0.0, 1.0))
        torso_l = x_cut_l - overlap
        torso_r = x_cut_r + overlap

        leg_zone = (yg >= y_hip) & (~arm_l_mask) & (~arm_r_mask)
        leg_l_mask = leg_zone & (xg < 240) & (base_rgba[..., 3] > 0)
        leg_r_mask = leg_zone & (xg >= 240) & (base_rgba[..., 3] > 0)
        torso_mask = (base_rgba[..., 3] > 0) & (yg < y_hip + 6) & (
            (yg < 160) | ((xg >= torso_l) & (xg <= torso_r))
        )

        arm_l = extend_top_upward(np.where(arm_l_mask[..., None], base_rgba, 0), 160, up_px=14)
        arm_r = extend_top_upward(np.where(arm_r_mask[..., None], base_rgba, 0), 160, up_px=14)
        torso = np.where(torso_mask[..., None], base_rgba, 0)
        for yy in range(y_hip + 1, y_hip + 6):
            torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((y_hip + 6 - yy) / 5.0)).astype(np.uint8)

        leg_l = extend_top_upward(np.where(leg_l_mask[..., None], base_rgba, 0), y_hip, up_px=26)
        leg_r = extend_top_upward(np.where(leg_r_mask[..., None], base_rgba, 0), y_hip, up_px=26)

        # Measure actual arm & leg X centroids for exact joint placement
        def _cx_band(arr_m, y0, y1, fallback):
            sub_x = np.nonzero(arr_m[y0:y1, :, 3] > 40)[1]
            return float(np.median(sub_x)) if len(sub_x) else fallback

        lx_h = _cx_band(leg_l, y_hip, y_hip + 45, 208.0)
        lx_k = _cx_band(leg_l, 450, 485, 206.0)
        lx_a = _cx_band(leg_l, 555, 590, 204.0)
        rx_h = _cx_band(leg_r, y_hip, y_hip + 45, 272.0)
        rx_k = _cx_band(leg_r, 450, 485, 274.0)
        rx_a = _cx_band(leg_r, 555, 590, 276.0)

        ls_x = _cx_band(arm_l, 165, 210, float(x_cut_l[180, 0]) - 10.0)
        le_x = _cx_band(arm_l, 250, 285, ls_x - 6.0)
        lw_x = _cx_band(arm_l, 325, 365, le_x - 2.0)
        rs_x = _cx_band(arm_r, 165, 210, float(x_cut_r[180, 0]) + 10.0)
        re_x = _cx_band(arm_r, 250, 285, rs_x + 6.0)
        rw_x = _cx_band(arm_r, 325, 365, re_x + 2.0)

        phase_01 = (frame_idx % n_frames) / float(n_frames)
        phase = 2.0 * math.pi * phase_01
        s_l = math.cos(phase - 0.35) * speed_boost
        s_r = -s_l
        bob_dy = sample_run_profile(phase_01)[4] * 0.95 * speed_boost
        sway_dx = -4.2 * math.sin(phase) * speed_boost
        tilt_deg = 2.4 * math.sin(phase) * speed_boost

        def pose_leg_fb(leg_im, hx, kx, ax, side_sign, s_val):
            if s_val > 0.0:
                lift = min(1.35, s_val)
                if not is_back:
                    return warp_limb_3bone(
                        leg_im, (hx, float(y_hip)), (kx, 468.0), (ax, 578.0),
                        ang_upper=-side_sign * 4.0 * lift,
                        ang_lower=side_sign * 5.0 * lift,
                        sy_upper=1.0 - 0.27 * lift,
                        sy_lower=1.0 - 0.18 * lift,
                        scale_all=1.0 + 0.05 * lift,
                        dx=sway_dx, dy=bob_dy - 16.0 * lift,
                    )
                return warp_limb_3bone(
                    shade_rgba(leg_im, 1.0 - 0.09 * lift),
                    (hx, float(y_hip)), (kx, 468.0), (ax, 578.0),
                    ang_upper=-side_sign * 3.0 * lift,
                    ang_lower=side_sign * 3.5 * lift,
                    sy_upper=1.0 - 0.12 * lift,
                    sy_lower=1.0 - 0.38 * lift,
                    scale_all=1.0 - 0.03 * lift,
                    dx=sway_dx, dy=bob_dy - 12.0 * lift,
                )
            p = min(1.35, -s_val)
            return warp_limb_3bone(
                leg_im, (hx, float(y_hip)), (kx, 468.0), (ax, 578.0),
                ang_upper=side_sign * 2.8 * p,
                ang_lower=-side_sign * 1.8 * p,
                sy_upper=1.0 + 0.02 * p,
                sy_lower=1.0 + 0.02 * p,
                dx=sway_dx, dy=max(0.0, bob_dy * 0.4),
            )

        def pose_arm_fb(arm_im, sx0, ex0, wx0, side_sign, arm_swing):
            if arm_swing > 0.0:
                u = min(1.35, arm_swing)
                im_s = shade_rgba(arm_im, 1.0 + 0.04 * u if not is_back else 1.0 - 0.09 * u)
                return warp_limb_3bone(
                    im_s, (sx0, 174.0), (ex0, 266.0), (wx0, 344.0),
                    ang_upper=side_sign * 9.0 * u,
                    ang_lower=-side_sign * 26.0 * u,
                    sy_upper=1.0 - 0.12 * u,
                    sy_lower=1.0 - 0.32 * u,
                    dx=sway_dx, dy=bob_dy - 10.0 * u,
                )
            b = min(1.35, -arm_swing)
            im_s = shade_rgba(arm_im, 1.0 - 0.10 * b if not is_back else 1.0 + 0.04 * b)
            return warp_limb_3bone(
                im_s, (sx0, 174.0), (ex0, 266.0), (wx0, 344.0),
                ang_upper=-side_sign * 9.0 * b,
                ang_lower=-side_sign * 12.0 * b,
                sy_upper=1.0 - 0.13 * b,
                sy_lower=1.0 - 0.20 * b,
                dx=sway_dx, dy=bob_dy - 6.0 * b,
            )

        leg_l_p = pose_leg_fb(leg_l, lx_h, lx_k, lx_a, -1.0, s_l)
        leg_r_p = pose_leg_fb(leg_r, rx_h, rx_k, rx_a, +1.0, s_r)
        torso_p = warp_rigid_rgba(torso, (240.0, 260.0), angle_deg=tilt_deg, dx=sway_dx, dy=bob_dy)
        arm_l_p = pose_arm_fb(arm_l, ls_x, le_x, lw_x, -1.0, s_r)
        arm_r_p = pose_arm_fb(arm_r, rs_x, re_x, rw_x, +1.0, s_l)

        out = np.zeros_like(base_rgba)
        if (s_l >= s_r) != is_back:
            out = alpha_over(alpha_over(out, leg_r_p), leg_l_p)
        else:
            out = alpha_over(alpha_over(out, leg_l_p), leg_r_p)
        if (s_r >= s_l) != is_back:
            out = alpha_over(alpha_over(alpha_over(out, arm_r_p), torso_p), arm_l_p)
        else:
            out = alpha_over(alpha_over(alpha_over(out, arm_l_p), torso_p), arm_r_p)
        return out

    # Side & diagonal canonical views (d_idx = 1 -> 45°, 2 -> 90°, 3 -> 135°, all facing screen-LEFT -X!)
    view_deg = d_idx * 45
    y_hip = 354  # Safely below full round pregnant belly & t-shirt hem so belly bump stays 100% intact!
    a_fg = base_rgba[..., 3] > 35

    def _med_x(y0, y1, fallback):
        xs = np.nonzero(a_fg[y0:y1])[1]
        return float(np.median(xs)) if len(xs) else fallback

    def _contour_edge(is_right: bool) -> np.ndarray:
        pts_y, pts_x = [], []
        for yy in range(170, 365, 4):
            xs = np.nonzero(a_fg[yy])[0]
            if len(xs) >= 4:
                pts_y.append(yy)
                pts_x.append(float(xs.max() if is_right else xs.min()))
        yg_1d = np.arange(H, dtype=np.float32)
        if len(pts_y) >= 3:
            return np.interp(yg_1d, pts_y, pts_x).astype(np.float32)
        return np.full(H, 285.0 if is_right else 195.0, dtype=np.float32)

    if view_deg == 90:
        cx_sh = _med_x(168, 205, 246.0) + 5.0
        sh_pt, el_pt, wr_pt = (cx_sh, 178.0), (cx_sh + 4.0, 262.0), (cx_sh - 1.0, 332.0)
        d_u = seg_dist_grid(xg.astype(np.float32), yg.astype(np.float32), sh_pt[0], sh_pt[1], el_pt[0], el_pt[1])
        d_l = seg_dist_grid(xg.astype(np.float32), yg.astype(np.float32), el_pt[0], el_pt[1], wr_pt[0], wr_pt[1])
        d_h = np.hypot((xg - wr_pt[0]), (yg - (wr_pt[1] + 7.0)) / 1.25)
        t_y = np.clip((yg.astype(np.float32) - sh_pt[1]) / max(1.0, wr_pt[1] - sh_pt[1]), 0.0, 1.0)
        rad = 17.5 * (1.0 - t_y) + 12.0 * t_y
        d_min = np.minimum(np.minimum(d_u, d_l), d_h)
        w_arm = np.clip((rad + 1.5 - d_min) / 3.0, 0.0, 1.0) * (yg >= 168.0) * (yg <= 346.0)
        near_arm = base_rgba.copy()
        near_arm[..., 3] = np.clip(np.round(near_arm[..., 3].astype(np.float32) * w_arm), 0, 255).astype(np.uint8)
        far_arm = shade_rgba(near_arm, 0.78)
        hand_hole = (d_min <= rad + 2.5) & (yg >= 275.0) & (yg <= 350.0)
        body_clean = inpaint_fabric_region(base_rgba, hand_hole)

        torso = np.zeros_like(base_rgba)
        torso[yg < y_hip + 5] = body_clean[yg < y_hip + 5]
        for yy in range(y_hip, y_hip + 5):
            torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((y_hip + 5 - yy) / 5.0)).astype(np.uint8)

        near_leg = np.zeros_like(base_rgba)
        near_leg[yg >= y_hip - 2] = body_clean[yg >= y_hip - 2]
        near_leg = extend_top_upward(near_leg, y_hip - 2, up_px=28)
        far_leg = shade_rgba(near_leg, 0.82)

        hx0 = _med_x(y_hip, y_hip + 40, 244.0)
        kx0 = _med_x(455, 485, hx0)
        ax0 = _med_x(555, 588, kx0)
        hip_pt, knee_pt, ankle_pt = (hx0, float(y_hip)), (kx0, 468.0), (ax0, 576.0)
        stride_scale = min(1.12, 1.00 * speed_boost)
        lean_deg = min(6.2, 5.5 * speed_boost)
        far_dx = -6.0
        far_sh, far_el, far_wr = (sh_pt[0] - 8.0, sh_pt[1]), (el_pt[0] - 8.0, el_pt[1]), (wr_pt[0] - 8.0, wr_pt[1])

    elif view_deg == 45:
        # Trace actual outer-right arm contour row-by-row so bowed maternity arms & stocky arms extract cleanly!
        x_rmax = _contour_edge(is_right=True)[:, None]
        sh_pt = (float(x_rmax[182, 0]) - 13.0, 178.0)
        el_pt = (float(x_rmax[266, 0]) - 11.0, 266.0)
        wr_pt = (float(x_rmax[336, 0]) - 9.0, 336.0)

        w_arm = np.clip((xg.astype(np.float32) - (x_rmax - 23.0)) / 3.5, 0.0, 1.0) * (yg >= 168.0) * (yg <= 354.0)
        near_arm = extend_top_upward(
            np.dstack([base_rgba[..., :3], np.clip(np.round(base_rgba[..., 3].astype(np.float32) * w_arm), 0, 255).astype(np.uint8)]),
            168, up_px=12,
        )
        # Also trim any resting far hand/arm sticking out past front-left hip, and create clean tucked far arm!
        x_lmin = _contour_edge(is_right=False)[:, None]
        chest_min_x = float(np.min(x_lmin[215:325, 0]))
        far_arm_dx = (chest_min_x + 8.0) - sh_pt[0]
        far_arm = shade_rgba(warp_rigid_rgba(near_arm, sh_pt, dx=far_arm_dx, dy=2.0), 0.78)

        # Cleanly remove outer right arm from torso (`xg <= rib_r`) while keeping 100% of pregnant belly bump on left!
        t_rib = np.clip((yg.astype(np.float32) - 184.0) / 38.0, 0.0, 1.0)
        rib_r = x_rmax - 19.0 * t_rib
        # Also trim any resting far-left forearm below chest if separated from belly
        torso_m = (yg < y_hip + 5) & (base_rgba[..., 3] > 0) & ((yg < 176) | (xg <= rib_r))
        torso = np.where(torso_m[..., None], base_rgba, 0)
        for yy in range(y_hip, y_hip + 5):
            torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((y_hip + 5 - yy) / 5.0)).astype(np.uint8)

        leg_zone = (yg >= y_hip - 2) & (xg <= rib_r + 5.0) & (base_rgba[..., 3] > 0)
        mid_leg_x = _med_x(y_hip + 12, 460, 240.0)
        near_raw = np.where((leg_zone & (xg >= mid_leg_x - 5.0))[..., None], base_rgba, 0)
        seam_b = (yg >= y_hip - 2) & (yg <= 435) & (xg >= mid_leg_x - 5.0) & (xg <= mid_leg_x + 3.0)
        if np.any(seam_b):
            ws = np.clip((xg.astype(np.float32) - (mid_leg_x - 5.0)) / 8.0, 0.0, 1.0)
            near_raw[seam_b, 3] = np.round(near_raw[seam_b, 3].astype(np.float32) * ws[seam_b]).astype(np.uint8)
        near_leg = extend_top_upward(near_raw, y_hip - 2, up_px=28)
        far_leg = shade_rgba(warp_rigid_rgba(near_leg, (mid_leg_x + 14.0, float(y_hip)), dx=-26.0, dy=-2.0), 0.84)

        hip_pt, knee_pt, ankle_pt = (mid_leg_x + 14.0, float(y_hip)), (mid_leg_x + 14.0, 468.0), (mid_leg_x + 15.0, 576.0)
        stride_scale = min(0.92, 0.82 * speed_boost)
        lean_deg = min(5.4, 4.6 * speed_boost)
        far_dx = -26.0
        far_sh, far_el, far_wr = (sh_pt[0] + far_arm_dx, sh_pt[1] + 2.0), (el_pt[0] + far_arm_dx, el_pt[1] + 2.0), (wr_pt[0] + far_arm_dx, wr_pt[1] + 2.0)

    else:  # view_deg == 135 (back-left, facing screen-LEFT)
        # Near (left) arm sits along outer-LEFT contour `x_lmin` — trim it cleanly off torso so ZERO ghost arm remains!
        x_lmin = _contour_edge(is_right=False)[:, None]
        x_rmax = _contour_edge(is_right=True)[:, None]
        sh_pt = (float(x_lmin[182, 0]) + 13.0, 178.0)
        el_pt = (float(x_lmin[266, 0]) + 11.0, 266.0)
        wr_pt = (float(x_lmin[336, 0]) + 9.0, 336.0)

        w_arm = np.clip(((x_lmin + 22.0) - xg.astype(np.float32)) / 3.5, 0.0, 1.0) * (yg >= 168.0) * (yg <= 354.0)
        near_arm = extend_top_upward(
            np.dstack([base_rgba[..., :3], np.clip(np.round(base_rgba[..., 3].astype(np.float32) * w_arm), 0, 255).astype(np.uint8)]),
            168, up_px=12,
        )
        rib_max_x = float(np.percentile(x_rmax[200:315, 0], 75))
        far_arm_dx = (rib_max_x - 12.0) - sh_pt[0]
        far_arm = shade_rgba(warp_rigid_rgba(near_arm, sh_pt, dx=far_arm_dx, dy=0.0), 0.78)

        t_rib = np.clip((yg.astype(np.float32) - 184.0) / 38.0, 0.0, 1.0)
        rib_l = x_lmin + 18.0 * t_rib
        rib_r = x_rmax - 10.0 * t_rib
        torso_m = (yg < y_hip + 5) & (base_rgba[..., 3] > 0) & ((yg < 176) | ((xg >= rib_l) & (xg <= rib_r)))
        torso = np.where(torso_m[..., None], base_rgba, 0)
        for yy in range(y_hip, y_hip + 5):
            torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((y_hip + 5 - yy) / 5.0)).astype(np.uint8)

        mid_leg_x = _med_x(y_hip + 12, 460, 240.0)
        leg_zone = (yg >= y_hip - 2) & (xg >= rib_l - 4.0) & (base_rgba[..., 3] > 0)
        near_raw = np.where((leg_zone & (xg <= mid_leg_x + 5.0))[..., None], base_rgba, 0)
        near_leg = extend_top_upward(near_raw, y_hip - 2, up_px=28)
        far_leg = shade_rgba(warp_rigid_rgba(near_leg, (mid_leg_x - 14.0, float(y_hip)), dx=+24.0, dy=-2.0), 0.84)

        hip_pt, knee_pt, ankle_pt = (mid_leg_x - 14.0, float(y_hip)), (mid_leg_x - 14.0, 468.0), (mid_leg_x - 14.0, 576.0)
        stride_scale = min(0.90, 0.80 * speed_boost)
        lean_deg = min(5.2, 4.5 * speed_boost)
        far_dx = +24.0
        far_sh, far_el, far_wr = (sh_pt[0] + far_arm_dx, sh_pt[1]), (el_pt[0] + far_arm_dx, el_pt[1]), (wr_pt[0] + far_arm_dx, wr_pt[1])

    # Pose near & far legs and natural bent-elbow counter-swinging arms!
    ph_near = (frame_idx % n_frames) / float(n_frames)
    ph_far = ((frame_idx + n_frames // 2) % n_frames) / float(n_frames)
    th_n, kn_n, ft_n, sy_n, bob_dy = sample_run_profile(ph_near)
    th_f, kn_f, ft_f, sy_f, _ = sample_run_profile(ph_far)
    bob_dy *= 0.90 * min(1.12, speed_boost)

    near_leg_p = warp_limb_3bone(
        near_leg, hip_pt, knee_pt, ankle_pt,
        ang_upper=th_n * stride_scale,
        ang_lower=kn_n * stride_scale,
        ang_tip=ft_n * 0.7,
        sy_upper=sy_n,
        dy=bob_dy,
    )
    far_hip = (hip_pt[0] + far_dx, hip_pt[1] - 2.0)
    far_knee = (knee_pt[0] + far_dx, knee_pt[1] - 2.0)
    far_ankle = (ankle_pt[0] + far_dx, ankle_pt[1] - 2.0)
    far_leg_p = warp_limb_3bone(
        far_leg, far_hip, far_knee, far_ankle,
        ang_upper=th_f * stride_scale,
        ang_lower=kn_f * stride_scale,
        ang_tip=ft_f * 0.7,
        sy_upper=sy_f,
        dy=bob_dy,
    )

    # Natural athletic counter-swinging arms (shoulder swing ±20°, elbow bend +22° -> max +42°, NEVER horizontal!)
    swing_near = -math.cos(2.0 * math.pi * ph_near - 0.25)
    swing_far = -swing_near
    arm_amp = 20.0 * stride_scale
    elbow_bend = 22.0 * stride_scale

    near_arm_p = warp_limb_3bone(
        near_arm, sh_pt, el_pt, wr_pt,
        ang_upper=arm_amp * swing_near,
        ang_lower=elbow_bend,
        sy_lower=0.92,
        dx=-2.0, dy=bob_dy,
    )
    far_arm_p = warp_limb_3bone(
        far_arm, far_sh, far_el, far_wr,
        ang_upper=0.75 * arm_amp * swing_far,
        ang_lower=0.85 * elbow_bend,
        sy_lower=0.90,
        dx=-4.0, dy=bob_dy,
    )
    torso_p = warp_rigid_rgba(torso, (240.0, 310.0), angle_deg=-lean_deg, dy=bob_dy)

    out = np.zeros_like(base_rgba)
    out = alpha_over(out, far_arm_p)
    out = alpha_over(out, far_leg_p)
    out = alpha_over(out, torso_p)
    out = alpha_over(out, near_leg_p)
    out = alpha_over(out, near_arm_p)
    return out


# ---------------------------------------------------------------------------
# 4. Load All Normalized 8-Angle Rigs & 360° Props (David, 3 Pregnant Runners, Money Bag, Slot Machine)
# ---------------------------------------------------------------------------

def load_all_studio_assets() -> dict:
    # 1. David Ojeda
    dv_f = key_magenta_studio(Image.open(REF_DIR / "david_studio_front.jpg"))
    dv_b = key_magenta_studio(Image.open(REF_DIR / "david_studio_back.jpg"))
    dv_t = key_magenta_studio(Image.open(REF_DIR / "david_studio_turn.jpg"))
    # Clean exact outer arm contour on Col 3 (135°)
    H, W = dv_t.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]
    c3_clean = dv_t.copy()
    x_lim = np.interp(yg, [0, 300, 360, 450, 540, 610, 1024], [722, 722, 725, 741, 748, 749, 760])
    c3_clean[xg > x_lim] = 0

    dv_5 = [
        crop_normalize_view(dv_f, (200, 70, 700, 1190), False),
        crop_normalize_view(dv_t, (10, 70, 304, 1010), True),
        crop_normalize_view(dv_t, (306, 70, 503, 1010), True),
        crop_normalize_view(c3_clean, (504, 70, 760, 1010), True),
        crop_normalize_view(dv_b, (200, 70, 700, 1190), False),
    ]
    david_8_neutral = [
        dv_5[0], dv_5[1], dv_5[2], dv_5[3], dv_5[4],
        mirror_canvas_horiz(dv_5[3]), mirror_canvas_horiz(dv_5[2]), mirror_canvas_horiz(dv_5[1]),
    ]
    david_8_shock = [apply_david_video_expression(david_8_neutral[d], d, "shock") for d in range(8)]
    david_8_grin = [apply_david_video_expression(david_8_neutral[d], d, "grin") for d in range(8)]

    # 2. Three Pregnant Hispanic Runners
    def _load_runner(front_fn, turn_fn, boxes_and_mirrors):
        rf = key_magenta_studio(Image.open(REF_DIR / front_fn))
        rt = key_magenta_studio(Image.open(REF_DIR / turn_fn))
        v5 = [crop_normalize_view(rf, boxes_and_mirrors[0][0], boxes_and_mirrors[0][1])]
        for bx, mir in boxes_and_mirrors[1:]:
            v5.append(crop_normalize_view(rt, bx, mir))
        return [
            v5[0], v5[1], v5[2], v5[3], v5[4],
            mirror_canvas_horiz(v5[3]), mirror_canvas_horiz(v5[2]), mirror_canvas_horiz(v5[1]),
        ]

    preg1_8 = _load_runner("preg1_studio_front.jpg", "preg1_studio_turn.jpg", [
        ((220, 50, 670, 1190), False),
        ((30, 30, 302, 975), True),
        ((304, 30, 513, 975), True),
        ((514, 30, 726, 975), False),
        ((730, 30, 1008, 975), False),
    ])
    preg2_8 = _load_runner("preg2_studio_front.jpg", "preg2_studio_turn.jpg", [
        ((200, 50, 700, 1190), False),
        ((30, 35, 306, 970), True),
        ((308, 35, 513, 970), True),
        ((514, 35, 725, 970), False),
        ((728, 35, 1008, 970), False),
    ])
    preg3_8 = _load_runner("preg3_studio_front.jpg", "preg3_studio_turn.jpg", [
        ((230, 35, 660, 1185), False),
        ((25, 45, 280, 1000), True),
        ((282, 45, 495, 1000), False),
        ((510, 45, 746, 1000), True),
        ((748, 45, 1015, 1000), False),
    ])

    # 3. 8-Direction Money Bag (tight-cropped & scaled uniformly to 136px tall)
    mb_raw = key_magenta_studio(Image.open(REF_DIR / "money_bag_turn.jpg"))
    def _crop_prop(arr, box, target_h, flip=False):
        sub = arr[box[1]:box[3], box[0]:box[2]].copy()
        if flip:
            sub = sub[:, ::-1, :].copy()
        m = sub[..., 3] > 28
        lbl, n = ndimage.label(m)
        if n > 1:
            sz = ndimage.sum(m, lbl, range(1, n + 1))
            sub[~ndimage.binary_dilation(lbl == (1 + int(np.argmax(sz))), iterations=2)] = 0
        ys, xs = np.nonzero(sub[..., 3] > 24)
        tight = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        sc = target_h / float(tight.shape[0])
        return resize_rgba_premul(tight, max(4, int(round(tight.shape[1] * sc))), target_h)

    mb_0 = _crop_prop(mb_raw, (40, 20, 480, 485), 132, False)
    mb_45_l = _crop_prop(mb_raw, (540, 20, 995, 485), 132, True)   # '$' angled left
    mb_90_l = _crop_prop(mb_raw, (40, 500, 480, 998), 132, False)
    mb_180 = _crop_prop(mb_raw, (540, 500, 995, 998), 132, False)
    mb_135_l = _crop_prop(mb_raw, (540, 500, 995, 998), 128, True)
    money_bag_8 = [
        mb_0, mb_45_l, mb_90_l, mb_135_l, mb_180,
        mb_135_l[:, ::-1, :].copy(), mb_90_l[:, ::-1, :].copy(), mb_45_l[:, ::-1, :].copy(),
    ]

    # 4. 8-Direction Casino Slot Machine (scaled to 340px tall — authentic chest/eye-level Vegas cabinet!)
    sm_raw = key_magenta_studio(Image.open(REF_DIR / "slot_machine_turn.jpg"))
    sm_0 = _crop_prop(sm_raw, (45, 50, 322, 850), 342, False)       # Front of slot machine ('JACKPOT' + 7-7-7)
    sm_45_l = _crop_prop(sm_raw, (326, 50, 622, 850), 342, False)   # Front-Left 45°
    sm_90_l = _crop_prop(sm_raw, (642, 50, 870, 850), 342, False)   # Left Side Profile (screen facing left)
    sm_180 = _crop_prop(sm_raw, (892, 50, 1162, 850), 342, False)   # Back of cabinet
    # Build 135° rear-three-quarter from 180° + side depth trim
    sm_135_l = resize_rgba_premul(sm_180, int(round(sm_180.shape[1] * 0.88)), 342)
    slot_8 = [
        sm_0, sm_45_l, sm_90_l, sm_135_l, sm_180,
        sm_135_l[:, ::-1, :].copy(), sm_90_l[:, ::-1, :].copy(), sm_45_l[:, ::-1, :].copy(),
    ]

    return {
        "david_neutral": david_8_neutral,
        "david_shock": david_8_shock,
        "david_grin": david_8_grin,
        "preg1": preg1_8,
        "preg2": preg2_8,
        "preg3": preg3_8,
        "money_bag_8": money_bag_8,
        "slot_8": slot_8,
    }


# ---------------------------------------------------------------------------
# 5. Procedural Crisp $100 Bills, Gold Coins & Dynamic Slot Reel / Marquee FX
# ---------------------------------------------------------------------------

def make_hundred_bill_rgba() -> np.ndarray:
    im = Image.new("RGBA", (52, 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 50, 24], radius=3, fill=(182, 212, 172, 255), outline=(44, 88, 52, 255), width=2)
    d.rectangle([5, 4, 46, 21], outline=(72, 128, 80, 235), width=1)
    d.ellipse([19, 5, 32, 20], fill=(142, 178, 138, 255), outline=(52, 96, 58, 255), width=1)
    # Gold $100 security ribbon!
    d.line([(34, 3), (34, 22)], fill=(218, 178, 58, 240), width=2)
    return np.asarray(im, dtype=np.uint8)


def make_gold_coin_rgba() -> np.ndarray:
    im = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 22, 22], fill=(255, 208, 42, 255), outline=(176, 112, 12, 255), width=2)
    d.ellipse([4, 4, 19, 19], fill=(255, 232, 98, 255), outline=(212, 148, 20, 255), width=1)
    d.line([(12, 6), (12, 17)], fill=(168, 104, 10, 255), width=2)
    return np.asarray(im, dtype=np.uint8)


def customize_slot_cabinet_frame(slot_rgba: np.ndarray, slot_view_idx: int, anim_kind: str, f_idx: int, n_frames: int) -> np.ndarray:
    """Animates the Vegas Slot Machine's 3 mechanical reels, double-sided illuminated 777 topper,
    chasing marquee bulbs, and cranking red-ball side lever across all 8 views (`slot_view_idx` 0..7)!"""
    # Give extra horizontal canvas margin for the side-mounted chrome lever & red ball knob
    src_pil = Image.fromarray(slot_rgba, "RGBA")
    pad_x = 24
    im = Image.new("RGBA", (src_pil.width + pad_x * 2, src_pil.height), (0, 0, 0, 0))
    im.alpha_composite(src_pil, (pad_x, 0))
    dr = ImageDraw.Draw(im)
    W0, H = src_pil.size
    ox = pad_x
    ph = f_idx / float(n_frames)

    # 1) Front & Front-3/4 views (`slot_view_idx` in 0, 1, 7): live animated 3-reel window!
    if slot_view_idx in (0, 1, 7):
        if slot_view_idx == 0:
            rx0, ry0, rx1, ry1 = ox + int(W0 * 0.13), int(H * 0.425), ox + int(W0 * 0.80), int(H * 0.535)
        elif slot_view_idx == 1:
            rx0, ry0, rx1, ry1 = ox + int(W0 * 0.12), int(H * 0.425), ox + int(W0 * 0.72), int(H * 0.535)
        else:  # 7
            rx0, ry0, rx1, ry1 = ox + int(W0 * 0.28), int(H * 0.425), ox + int(W0 * 0.88), int(H * 0.535)

        rw_tot = max(12, rx1 - rx0)
        rh_tot = max(10, ry1 - ry0)
        col_w = rw_tot / 3.0

        if anim_kind == "spin":
            reel_cols = [(235, 58, 32), (242, 188, 38), (38, 178, 88), (42, 42, 48)]
            for c in range(3):
                cx0 = int(rx0 + c * col_w + 2)
                cx1 = int(rx0 + (c + 1) * col_w - 2)
                dr.rectangle([cx0, ry0, cx1, ry1], fill=(246, 244, 236, 255))
                for s in range(4):
                    yy = ry0 + int(((s * 0.27 + ph * (3 + c) * 1.35) % 1.0) * (rh_tot - 5))
                    col = reel_cols[(s + c + f_idx) % len(reel_cols)]
                    dr.rounded_rectangle([cx0 + 3, yy, cx1 - 3, min(ry1 - 1, yy + 6)], radius=2, fill=(*col, 230))
                dr.line([(int(0.5 * (cx0 + cx1)), ry0 + 1), (int(0.5 * (cx0 + cx1)), ry1 - 1)], fill=(255, 255, 255, 130), width=2)

        elif anim_kind == "jackpot":
            flash = (f_idx % 2 == 0)
            bg_c = (255, 248, 190, 255) if flash else (255, 255, 255, 255)
            for c in range(3):
                cx0 = int(rx0 + c * col_w + 2)
                cx1 = int(rx0 + (c + 1) * col_w - 2)
                dr.rectangle([cx0, ry0, cx1, ry1], fill=bg_c, outline=(235, 175, 25, 255), width=1)
                mx, my = int(0.5 * (cx0 + cx1)), int(0.5 * (ry0 + ry1))
                dr.line([(cx0 + 4, my - 8), (cx1 - 4, my - 8), (mx - 2, my + 9)], fill=(228, 36, 20, 255), width=4)
            if flash:
                dr.rounded_rectangle([ox + int(W0 * 0.08), int(H * 0.01), ox + int(W0 * 0.86), int(H * 0.16)], radius=10,
                                     outline=(255, 232, 85, 225), width=3)

        elif anim_kind == "bust":
            flash_r = (f_idx % 2 == 0)
            for c in range(3):
                cx0 = int(rx0 + c * col_w + 2)
                cx1 = int(rx0 + (c + 1) * col_w - 2)
                dr.rectangle([cx0, ry0, cx1, ry1], fill=(255, 222, 218, 255) if flash_r else (244, 240, 238, 255))
                mx, my = int(0.5 * (cx0 + cx1)), int(0.5 * (ry0 + ry1))
                if c == 0:
                    dr.line([(cx0 + 4, my - 7), (cx1 - 4, my - 7), (mx - 1, my + 8)], fill=(215, 38, 22, 255), width=3)
                elif c == 1:
                    dr.rectangle([cx0 + 3, my - 4, cx1 - 3, my + 4], fill=(28, 28, 32, 255))
                else:
                    dr.line([(cx0 + 4, my - 7), (cx1 - 4, my + 7)], fill=(225, 24, 24, 255), width=3)
                    dr.line([(cx1 - 4, my - 7), (cx0 + 4, my + 7)], fill=(225, 24, 24, 255), width=3)
            if flash_r:
                dr.rectangle([ox + int(W0 * 0.14), int(H * 0.19), ox + int(W0 * 0.78), int(H * 0.29)], fill=(215, 28, 24, 185))

    # 2) Rear & Rear-3/4 views (`slot_view_idx` in 3, 4, 5): double-sided Vegas `777` neon topper + brass trim
    #    + animated red-ball side lever so the slot machine is 100% iconic even when viewed from behind!
    elif slot_view_idx in (3, 4, 5):
        flash = (f_idx % 2 == 0)
        tx0, ty0, tx1, ty1 = ox + int(W0 * 0.14), int(H * 0.02), ox + int(W0 * 0.86), int(H * 0.16)
        top_bg = (24, 72, 46, 245) if anim_kind != "bust" else ((145, 22, 22, 245) if flash else (68, 20, 22, 245))
        top_bdr = (252, 212, 62, 255) if (anim_kind != "bust" or not flash) else (255, 75, 58, 255)
        dr.rounded_rectangle([tx0, ty0, tx1, ty1], radius=9, fill=top_bg, outline=top_bdr, width=3)
        # Draw bold '7 7 7' neon sign on the double-sided casino topper!
        tw = max(18, tx1 - tx0)
        my_t = int(0.5 * (ty0 + ty1))
        for k7 in range(3):
            sx7 = tx0 + int(tw * (0.20 + k7 * 0.26))
            c7 = (255, 232, 75, 255) if (anim_kind == "jackpot" and flash) else ((242, 62, 38, 255) if anim_kind != "bust" else (255, 190, 180, 240))
            dr.line([(sx7 - 6, my_t - 9), (sx7 + 6, my_t - 9), (sx7 - 1, my_t + 9)], fill=c7, width=3)

        # Warm brass casino cabinet frame & illuminated rear status badge (replaces dull plain metal back!)
        bx0, by0, bx1, by1 = ox + int(W0 * 0.14), int(H * 0.24), ox + int(W0 * 0.86), int(H * 0.56)
        dr.rounded_rectangle([bx0, by0, bx1, by1], radius=6, outline=(198, 152, 54, 215), width=2)
        # Illuminated Vegas neon accent bars on rear panel
        bar_col = (46, 198, 108, 215) if anim_kind == "spin" else ((255, 218, 58, 240) if anim_kind == "jackpot" else (235, 45, 38, 225))
        if anim_kind == "spin":
            bar_y = by0 + 10 + int(((ph * 2.0) % 1.0) * max(8, (by1 - by0 - 28)))
            dr.rounded_rectangle([bx0 + 10, bar_y, bx1 - 10, bar_y + 10], radius=3, fill=bar_col)
        elif anim_kind == "jackpot":
            dr.rounded_rectangle([bx0 + 10, by0 + 12, bx1 - 10, by1 - 12], radius=4,
                                 fill=(255, 234, 92, 165 if flash else 85), outline=(255, 212, 48, 235), width=2)
        else:
            if flash:
                dr.rounded_rectangle([bx0 + 10, by0 + 14, bx1 - 10, by0 + 38], radius=4, fill=(225, 32, 28, 215))

        # Animated side-mounted chrome lever + glossy red ball (on left edge when viewed from rear: David's right hand!)
        lx_base = ox + int(W0 * 0.10)
        ly_piv = int(H * 0.48)
        pull_t = math.sin(math.pi * min(1.0, f_idx / 3.0)) if anim_kind == "spin" and f_idx <= 3 else (0.15 * math.sin(ph * 2 * math.pi))
        ly_knob = int(ly_piv - 58 * (1.0 - 1.55 * pull_t))
        lx_knob = lx_base - 11
        dr.ellipse([lx_base - 5, ly_piv - 8, lx_base + 6, ly_piv + 8], fill=(175, 180, 188, 255), outline=(70, 74, 80, 255))
        dr.line([(lx_base - 2, ly_piv), (lx_knob, ly_knob)], fill=(215, 222, 232, 255), width=4)
        dr.ellipse([lx_knob - 8, ly_knob - 8, lx_knob + 8, ly_knob + 8], fill=(228, 32, 28, 255), outline=(110, 14, 14, 255), width=1)
        dr.ellipse([lx_knob - 4, ly_knob - 5, lx_knob - 1, ly_knob - 2], fill=(255, 185, 180, 235))

    # 3) Chasing marquee/topper light bulbs visible from ALL 8 angles!
    n_bulbs = 7
    for b in range(n_bulbs):
        bx = ox + int(W0 * (0.18 + 0.64 * (b / max(1, n_bulbs - 1))))
        by = int(H * 0.04)
        active = ((b + f_idx) % 2 == 0) if anim_kind != "bust" else (f_idx % 2 == 0)
        if active:
            col = (255, 238, 95, 240) if anim_kind != "bust" else (255, 62, 48, 240)
            dr.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=col)

    return np.asarray(im, dtype=np.uint8)


# ---------------------------------------------------------------------------
# 6. Full 360° Scene Compositors for All David Ojeda & Pregnant Runner Animations
# ---------------------------------------------------------------------------

def place_char_on_stage(
    canvas: Image.Image,
    char_480x640: np.ndarray,
    cx: float = STAGE_CX,
    gy: float = STAGE_GY,
    char_scale: float = 0.74,
    rot_deg: float = 0.0,
    squash_x: float = 1.0,
    stretch_y: float = 1.0,
) -> None:
    """Places a 480x640 character (feet at GROUND_Y=596) cleanly onto `480x540` stage anchored at `(cx, gy)`."""
    # Crop below y=612 so GROUND_Y=596 aligns right near bottom of character sprite
    cropped = char_480x640[:606, :, :]
    foot_from_bottom = (606 - GROUND_Y) * char_scale * stretch_y
    paste_rgba_pil(
        canvas,
        cropped,
        cx=cx,
        cy=gy + foot_from_bottom,
        scale_x=char_scale * squash_x,
        scale_y=char_scale * stretch_y,
        rot_deg=rot_deg,
        anchor_bottom=True,
    )


def build_all_character_animations(assets: dict, n_frames: int = 8) -> dict:
    """Generates full 8-direction x `n_frames` high-res (480x540) RGBA sequences for:
      - David Ojeda: idle, fast_run, turbo_sprint, money_hold, money_run, slot_spin, slot_jackpot, slot_bust
      - Pregnant Runners 1, 2, 3: idle, run
    """
    bill_im = make_hundred_bill_rgba()
    coin_im = make_gold_coin_rgba()

    # 1. David Standing Idle (8 dirs) & Clean Fast Run (8 dirs x n_frames)
    david_idle_stage = []
    david_fast_run = []
    david_turbo_sprint = []
    david_money_hold = []
    david_money_run = []
    david_slot_spin = []
    david_slot_jackpot = []
    david_slot_bust = []

    from concurrent.futures import ThreadPoolExecutor

    def _compute_run_grid(char_8: list[np.ndarray], boost: float) -> list[list[np.ndarray]]:
        tasks = [(d, f) for d in range(8) for f in range(n_frames)]
        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
            flat = list(ex.map(lambda df: render_adaptive_run_frame(char_8[df[0]], df[0], df[1], n_frames, speed_boost=boost), tasks))
        return [[flat[d * n_frames + f] for f in range(n_frames)] for d in range(8)]

    # Precompute David base run frames in 480x640 for shock & grin faces in parallel!
    raw_run_shock = _compute_run_grid(assets["david_shock"], 1.18)
    raw_run_grin = _compute_run_grid(assets["david_grin"], 1.12)

    for d in range(8):
        # --- Idle ---
        st_idle = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        draw_contact_shadow(st_idle, STAGE_CX, STAGE_GY, rx=48, ry=10, alpha=84)
        place_char_on_stage(st_idle, assets["david_neutral"][d], STAGE_CX, STAGE_GY, char_scale=0.74)
        david_idle_stage.append(np.asarray(st_idle, dtype=np.uint8))

        # --- Fast Run (clean 360° sprint with shocked face!) ---
        row_run = []
        row_turbo = []
        row_mhold = []
        row_mrun = []
        row_sspin = []
        row_sjack = []
        row_sbust = []

        fwd_screen_x = -math.sin(math.radians(d * 45.0))  # <0 when facing left (d=1,2,3), >0 when facing right (d=5,6,7)

        for f in range(n_frames):
            ph = f / float(n_frames)
            ang = 2.0 * math.pi * ph
            rng = np.random.default_rng(7000 + d * 97 + f * 31)

            # 1) Clean Fast Run
            c_run = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_run, STAGE_CX, STAGE_GY, rx=46, ry=9, alpha=78)
            place_char_on_stage(c_run, raw_run_shock[d][f], STAGE_CX, STAGE_GY, char_scale=0.74)
            row_run.append(np.asarray(c_run, dtype=np.uint8))

            # 2) Turbo Speed-Burst Run (extra forward tilt + speed wind-streaks + boot dust puffs!)
            c_tur = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_tur, STAGE_CX, STAGE_GY, rx=50, ry=9, alpha=72)
            # Behind-character speed streaks & trailing dust puffs in 3D (-lx behind David!)
            dr_t = ImageDraw.Draw(c_tur)
            for s_i in range(5):
                lz_s = 75.0 + s_i * 58.0 + 12.0 * math.sin(ang + s_i)
                ly_s = (-28.0 if s_i % 2 == 0 else 28.0)
                sx0, sy0, _, _ = project_3d(-18.0, ly_s, lz_s, d)
                sx1, sy1, _, _ = project_3d(-92.0 - 24.0 * ((f + s_i) % 3), ly_s, lz_s, d)
                dr_t.line([(sx0, sy0), (sx1, sy1)], fill=(195, 238, 255, 155 - s_i * 22), width=3)
            # Dust puffs behind heels
            for p_i in range(3):
                p_age = ((ph * 2.0 + p_i * 0.33) % 1.0)
                dx_p, dy_p, _, sc_p = project_3d(-24.0 - 68.0 * p_age, (p_i - 1) * 14.0, 10.0 + 22.0 * p_age, d)
                rad = (9.0 + 16.0 * p_age) * sc_p
                al = int(145 * (1.0 - p_age))
                if al > 10:
                    dr_t.ellipse([dx_p - rad, dy_p - rad * 0.7, dx_p + rad, dy_p + rad * 0.7], fill=(212, 202, 186, al))

            lean_scr = fwd_screen_x * 6.5  # leans forward in direction of travel!
            place_char_on_stage(c_tur, raw_run_shock[d][f], STAGE_CX + fwd_screen_x * 6.0, STAGE_GY, char_scale=0.74, rot_deg=-lean_scr)
            row_turbo.append(np.asarray(c_tur, dtype=np.uint8))

            # 3) Holding & Flexing Bag of Money (360°!)
            c_mh = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            bounce_z = abs(math.sin(ang)) * 12.0
            bob_bag = math.sin(ang * 2.0) * 7.0
            draw_contact_shadow(c_mh, STAGE_CX, STAGE_GY, rx=50, ry=10, alpha=84)

            # Money bag cradled at David's front-right chest/hip (lx=+26, ly=-34 right) so even from 180° rear
            # the bulging '$' cash sack & overflowing green bills peek clearly out at his right side!
            mb_sx, mb_sy, mb_dz, mb_sc = project_3d(26.0, -34.0, 174.0 + bounce_z + bob_bag, d)
            bag_im = assets["money_bag_8"][d]
            bag_tilt = 8.0 * math.sin(ang)

            def _draw_david_mhold():
                sq_x = 1.0 + 0.025 * math.cos(ang * 2.0)
                st_y = 1.0 - 0.020 * math.cos(ang * 2.0)
                place_char_on_stage(
                    c_mh, assets["david_grin"][d],
                    STAGE_CX, STAGE_GY - bounce_z * 0.45,
                    char_scale=0.74, rot_deg=2.5 * math.sin(ang),
                    squash_x=sq_x, stretch_y=st_y,
                )

            def _draw_bag_mhold():
                paste_rgba_pil(c_mh, bag_im, mb_sx, mb_sy, scale_x=0.88 * mb_sc, scale_y=0.88 * mb_sc, rot_deg=bag_tilt)

            # Fluttering $100 bills orbiting around the money bag at David's front-right side!
            items_mh = [(0.0, _draw_david_mhold), (mb_dz, _draw_bag_mhold)]
            for b_i in range(5):
                b_ph = (ph + b_i * 0.20) % 1.0
                b_ang = b_ph * 2.0 * math.pi + b_i * 1.1
                bx3 = 26.0 + 34.0 * math.cos(b_ang)
                by3 = -36.0 + 34.0 * math.sin(b_ang)
                bz3 = 252.0 - 135.0 * b_ph + 12.0 * math.sin(b_ang * 2.0)
                bsx, bsy, bdz, bsc = project_3d(bx3, by3, bz3, d)
                brot = (b_ph * 360.0 + b_i * 42.0) % 360.0
                bal = float(np.sin(math.pi * b_ph))
                items_mh.append((bdz, lambda bsx=bsx, bsy=bsy, bsc=bsc, brot=brot, bal=bal: paste_rgba_pil(
                    c_mh, bill_im, bsx, bsy, scale_x=0.80 * bsc, scale_y=0.80 * bsc, rot_deg=brot, alpha_mul=0.95 * bal
                )))

            for _, fn in sorted(items_mh, key=lambda x: -x[0]):
                fn()
            row_mhold.append(np.asarray(c_mh, dtype=np.uint8))

            # 4) Fast Heist Sprint Holding Bag of Money (360°!)
            c_mr = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_mr, STAGE_CX, STAGE_GY, rx=48, ry=9, alpha=80)
            mr_sx, mr_sy, mr_dz, mr_sc = project_3d(28.0, -32.0, 178.0 + 8.0 * math.sin(ang * 2.0), d)
            lean_mr = fwd_screen_x * 4.5
            items_mr = [
                (0.0, lambda: place_char_on_stage(c_mr, raw_run_grin[d][f], STAGE_CX, STAGE_GY, char_scale=0.74, rot_deg=-lean_mr)),
                (mr_dz, lambda: paste_rgba_pil(c_mr, bag_im, mr_sx, mr_sy, scale_x=0.84 * mr_sc, scale_y=0.84 * mr_sc, rot_deg=-lean_mr + 7.0 * math.sin(ang))),
            ]
            # Trailing $100 bills flying out of the sack behind sprinting David!
            for b_i in range(4):
                b_age = (ph + b_i * 0.25) % 1.0
                bx3 = 22.0 - 118.0 * b_age
                by3 = -32.0 + 26.0 * math.sin(b_age * 5.0 + b_i)
                bz3 = 218.0 - 52.0 * b_age + 12.0 * math.cos(b_age * 5.0)
                bsx, bsy, bdz, bsc = project_3d(bx3, by3, bz3, d)
                brot = b_age * 280.0 + b_i * 55.0
                bal = 1.0 - 0.72 * b_age
                items_mr.append((bdz, lambda bsx=bsx, bsy=bsy, bsc=bsc, brot=brot, bal=bal: paste_rgba_pil(
                    c_mr, bill_im, bsx, bsy, scale_x=0.78 * bsc, scale_y=0.78 * bsc, rot_deg=brot, alpha_mul=bal
                )))
            for _, fn in sorted(items_mr, key=lambda x: -x[0]):
                fn()
            row_mrun.append(np.asarray(c_mr, dtype=np.uint8))

            # 5, 6, 7) Playing on a Casino Slot Machine (360°: Spin, Jackpot 777, Bust/Tilt!)
            # Geometry: David stands at local (lx = -42, ly = -24) facing +X;
            # Vegas Slot Machine stands at local (lx = +44, ly = +26) facing -X (`slot_view_idx = (d + 4) % 8`)!
            # The 50px lateral offset + chest-high 0.79 cabinet scale ensures BOTH David's expressive face/glasses
            # AND the illuminated 777 slot machine + cranking red-ball lever stay 100% readable across ALL 8 angles!
            slot_view_idx = (d + 4) % 8
            dv_sx, dv_sy, dv_dz, dv_sc = project_3d(-42.0, -24.0, 0.0, d)
            sm_sx, sm_sy, sm_dz, sm_sc = project_3d(+44.0, +26.0, 0.0, d)
            cab_scale = 0.79

            # --- 5) Slot Spin (Lever Pull & Button Mash) ---
            c_sp = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_sp, dv_sx, dv_sy, rx=42 * dv_sc, ry=9 * dv_sc, alpha=82)
            draw_contact_shadow(c_sp, sm_sx, sm_sy, rx=42 * sm_sc, ry=10 * sm_sc, alpha=92)
            sm_spin_im = customize_slot_cabinet_frame(assets["slot_8"][slot_view_idx], slot_view_idx, "spin", f, n_frames)
            eager_lean = fwd_screen_x * (6.5 if f < 3 else 3.0 + 2.0 * math.sin(ang * 2))
            dv_bob = 4.0 * abs(math.sin(ang * 2))
            items_sp = [
                (dv_dz, lambda: place_char_on_stage(c_sp, assets["david_shock"][d], dv_sx, dv_sy - dv_bob, char_scale=0.72 * dv_sc, rot_deg=-eager_lean)),
                (sm_dz, lambda: paste_rgba_pil(c_sp, sm_spin_im, sm_sx, sm_sy, scale_x=cab_scale * sm_sc, scale_y=cab_scale * sm_sc, anchor_bottom=True)),
            ]
            for _, fn in sorted(items_sp, key=lambda x: -x[0]):
                fn()
            row_sspin.append(np.asarray(c_sp, dtype=np.uint8))

            # --- 6) Slot 7-7-7 JACKPOT Celebration! ---
            c_jp = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_jp, dv_sx, dv_sy, rx=42 * dv_sc, ry=9 * dv_sc, alpha=80)
            draw_contact_shadow(c_jp, sm_sx, sm_sy, rx=44 * sm_sc, ry=10 * sm_sc, alpha=94)
            sm_jp_im = customize_slot_cabinet_frame(assets["slot_8"][slot_view_idx], slot_view_idx, "jackpot", f, n_frames)
            jump_z = abs(math.sin(ang)) * 22.0
            if f % 2 == 0:
                glow = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
                ImageDraw.Draw(glow).ellipse([sm_sx - 88, sm_sy - 280, sm_sx + 88, sm_sy - 80], fill=(255, 215, 55, 58))
                c_jp.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14.0)))

            items_jp = [
                (dv_dz, lambda: place_char_on_stage(
                    c_jp, assets["david_grin"][d], dv_sx, dv_sy - jump_z,
                    char_scale=0.72 * dv_sc, rot_deg=4.0 * math.sin(ang * 2),
                    squash_x=1.0 - 0.03 * (jump_z / 22.0), stretch_y=1.0 + 0.04 * (jump_z / 22.0),
                )),
                (sm_dz, lambda: paste_rgba_pil(c_jp, sm_jp_im, sm_sx, sm_sy, scale_x=cab_scale * sm_sc, scale_y=cab_scale * sm_sc, anchor_bottom=True)),
            ]
            # 3D Fountain of gold coins & crisp $100 bills erupting from the slot machine!
            for k_c in range(10):
                c_ph = (ph + k_c * 0.10) % 1.0
                vx = -48.0 + (k_c % 5 - 2.0) * 24.0
                vy = (k_c % 3 - 1.0) * 32.0
                px3 = 44.0 + vx * c_ph
                py3 = 26.0 + vy * c_ph
                pz3 = 128.0 + 205.0 * c_ph - 215.0 * (c_ph ** 2)
                csx, csy, cdz, csc = project_3d(px3, py3, max(12.0, pz3), d)
                is_bill = (k_c % 3 == 0)
                prop_p = bill_im if is_bill else coin_im
                psc = (0.76 if is_bill else 0.72) * csc
                prot = (c_ph * 420.0 + k_c * 37.0) % 360.0
                items_jp.append((cdz - 4.0, lambda prop_p=prop_p, csx=csx, csy=csy, psc=psc, prot=prot: paste_rgba_pil(
                    c_jp, prop_p, csx, csy, scale_x=psc, scale_y=psc, rot_deg=prot
                )))
            for _, fn in sorted(items_jp, key=lambda x: -x[0]):
                fn()
            row_sjack.append(np.asarray(c_jp, dtype=np.uint8))

            # --- 7) Slot Near-Miss BUST & Tilt Shake! ---
            c_bu = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            shake_x = (-5.0 if f % 2 == 0 else +5.0)
            tilt_cab = (-3.2 if f % 2 == 0 else +3.2)
            draw_contact_shadow(c_bu, dv_sx, dv_sy, rx=42 * dv_sc, ry=9 * dv_sc, alpha=82)
            draw_contact_shadow(c_bu, sm_sx + shake_x * 0.5, sm_sy, rx=42 * sm_sc, ry=10 * sm_sc, alpha=92)
            sm_bu_im = customize_slot_cabinet_frame(assets["slot_8"][slot_view_idx], slot_view_idx, "bust", f, n_frames)

            dv_bu_sx, dv_bu_sy, dv_bu_dz, dv_bu_sc = project_3d(-26.0, -22.0, 0.0, d)
            items_bu = [
                (dv_bu_dz, lambda: place_char_on_stage(
                    c_bu, assets["david_shock"][d], dv_bu_sx - shake_x * 0.6, dv_bu_sy,
                    char_scale=0.72 * dv_bu_sc, rot_deg=-fwd_screen_x * 7.5 + shake_x * 0.4,
                )),
                (sm_dz, lambda: paste_rgba_pil(
                    c_bu, sm_bu_im, sm_sx + shake_x, sm_sy,
                    scale_x=cab_scale * sm_sc, scale_y=cab_scale * sm_sc, rot_deg=tilt_cab, anchor_bottom=True,
                )),
            ]
            # Angry smoke puffs rising strictly from the top of the overheated slot machine (never covering David's face!)
            for s_k in range(3):
                s_age = (ph + s_k * 0.33) % 1.0
                ssx, ssy, sdz, ssc = project_3d(46.0, 28.0 + (s_k - 1) * 12.0, 268.0 + 72.0 * s_age, d)
                rad = (9.0 + 15.0 * s_age) * ssc
                al = int(118 * (1.0 - s_age))
                def _smoke(ssx=ssx, ssy=ssy, rad=rad, al=al):
                    if al > 8:
                        ImageDraw.Draw(c_bu).ellipse([ssx - rad, ssy - rad * 0.8, ssx + rad, ssy + rad * 0.8], fill=(74, 70, 78, al))
                items_bu.append((sm_dz - 2.0, _smoke))
            for _, fn in sorted(items_bu, key=lambda x: -x[0]):
                fn()
            row_sbust.append(np.asarray(c_bu, dtype=np.uint8))

        david_fast_run.append(row_run)
        david_turbo_sprint.append(row_turbo)
        david_money_hold.append(row_mhold)
        david_money_run.append(row_mrun)
        david_slot_spin.append(row_sspin)
        david_slot_jackpot.append(row_sjack)
        david_slot_bust.append(row_sbust)

    # 2. Build 8-direction Idle + 8-direction Running for all 3 Pregnant Hispanic Women in parallel!
    runners = {}
    for key in ("preg1", "preg2", "preg3"):
        raw_grid = _compute_run_grid(assets[key], 1.08)
        r_idle = []
        r_run = []
        for d in range(8):
            st_i = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(st_i, STAGE_CX, STAGE_GY, rx=42, ry=9, alpha=80)
            place_char_on_stage(st_i, assets[key][d], STAGE_CX, STAGE_GY, char_scale=0.74)
            r_idle.append(np.asarray(st_i, dtype=np.uint8))

            row_r = []
            for f in range(n_frames):
                st_r = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
                draw_contact_shadow(st_r, STAGE_CX, STAGE_GY, rx=42, ry=9, alpha=76)
                place_char_on_stage(st_r, raw_grid[d][f], STAGE_CX, STAGE_GY, char_scale=0.74)
                row_r.append(np.asarray(st_r, dtype=np.uint8))
            r_run.append(row_r)
        runners[key] = {"idle": r_idle, "run": r_run}

    return {
        "david": {
            "idle": david_idle_stage,
            "fast_run": david_fast_run,
            "turbo_sprint": david_turbo_sprint,
            "money_hold": david_money_hold,
            "money_run": david_money_run,
            "slot_spin": david_slot_spin,
            "slot_jackpot": david_slot_jackpot,
            "slot_bust": david_slot_bust,
        },
        "preg1": runners["preg1"],
        "preg2": runners["preg2"],
        "preg3": runners["preg3"],
    }
