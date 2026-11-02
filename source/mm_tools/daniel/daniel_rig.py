"""Photorealistic 360° Character Rigging, Real-Video Facial Expression Grafting,
Hands-Up 4AM Panic Pose, and 3D LAN Party Prop Compositor for Daniel & 4 AM Dad (BakersfieldQuake)."""

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
REF_DIR = TOOLS_DIR / "ref" / "daniel"
DAVID_DIR = TOOLS_DIR / "david_ojeda"

for p in (str(TOOLS_DIR), str(DAVID_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from paul_dennis_rig import (
    CANVAS_H,
    CANVAS_W,
    GROUND_Y,
    alpha_over,
    crop_normalize_view,
    extend_top_upward,
    key_magenta_studio,
    mirror_canvas_horiz,
    sample_run_profile,
    shade_rgba,
    warp_limb_3bone,
    warp_rigid_rgba,
)
from david_rig import (
    STAGE_CX,
    STAGE_GY,
    STAGE_H,
    STAGE_W,
    _auto_front_back_seams,
    draw_contact_shadow,
    paste_rgba_pil,
    place_char_on_stage,
    project_3d,
    render_adaptive_run_frame,
    resize_rgba_premul,
)


# ---------------------------------------------------------------------------
# 1. Clean Turnaround Extraction (Exact Col 3 / Col 4 Seam + Full Back Sleeves)
# ---------------------------------------------------------------------------

def _extract_clean_c3_c4(
    turn_rgba: np.ndarray,
    c3_ys: list[float],
    c3_xs: list[float],
    c4_cx: float,
    c4_arm_x: float,
    right_ext_px: int = 6,
) -> tuple[np.ndarray, np.ndarray]:
    """Separates Col 3 (135°) and Col 4 (180° back) cleanly along the exact forearm/sleeve
    contour and restores symmetric un-occluded back sleeves on Col 4."""
    H, W = turn_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]

    # 1) Col 3 (135° back-right)
    c3 = turn_rgba.copy()
    lim = np.interp(yg, c3_ys, c3_xs)
    w_c3 = np.clip((lim - xg.astype(np.float32) + 1.5) / 2.5, 0.0, 1.0)
    c3[..., 3] = np.round(c3[..., 3].astype(np.float32) * w_c3).astype(np.uint8)
    c3[xg < 496] = 0

    # 2) Col 4 (180° back) on right-padded canvas so outer right sleeve is never border-clipped
    pad_w = 32
    c4_pad = np.zeros((H, W + pad_w, 4), dtype=np.uint8)
    c4_pad[:, :W] = turn_rgba
    touch_ys = np.nonzero(turn_rgba[:, W - 1, 3] > 36)[0]
    if len(touch_ys) > 4 and right_ext_px > 0:
        y_mid = 0.5 * (touch_ys.min() + touch_ys.max())
        y_rad = max(10.0, 0.54 * (touch_ys.max() - touch_ys.min()))
        # Sample clean sleeve interior RGB 4px inside border so border compression never darkens edge
        edge_rgb = turn_rgba[:, max(0, W - 5), :3]
        for dx in range(1, right_ext_px + 2):
            for yy in touch_ys:
                norm_y = abs(yy - y_mid) / y_rad
                max_dx = float(right_ext_px) * max(0.0, 1.0 - norm_y ** 2)
                if dx <= max_dx:
                    c4_pad[yy, W - 1 + dx, :3] = edge_rgb[yy]
                    al = float(turn_rgba[yy, W - 1, 3]) * np.clip((max_dx - dx + 1.2) / 2.0, 0.0, 1.0)
                    c4_pad[yy, W - 1 + dx, 3] = int(round(al))

    yg_p, xg_p = np.mgrid[0:H, 0:W + pad_w]
    c4_torso_left = c4_cx - (c4_arm_x - c4_cx)
    mirror_src_x = np.round(2.0 * c4_cx - xg_p.astype(np.float32)).astype(np.int32)
    valid_m = (mirror_src_x >= 0) & (mirror_src_x < W + pad_w)
    mirrored = np.zeros_like(c4_pad)
    mirrored[valid_m] = c4_pad[yg_p[valid_m], mirror_src_x[valid_m]]

    w_mir_x = np.clip(((c4_torso_left + 5.0) - xg_p.astype(np.float32)) / 8.0, 0.0, 1.0)
    w_mir_y = (
        np.clip((yg_p.astype(np.float32) - 238.0) / 8.0, 0.0, 1.0)
        * np.clip((632.0 - yg_p.astype(np.float32)) / 8.0, 0.0, 1.0)
    )
    w_mir = (w_mir_x * w_mir_y)[..., None]

    c4_clean = np.round(
        c4_pad.astype(np.float32) * (1.0 - w_mir) + mirrored.astype(np.float32) * w_mir
    ).astype(np.uint8)
    c4_clean[xg_p < int(c4_cx - 172)] = 0
    return c3, c4_clean


# ---------------------------------------------------------------------------
# 2. Real-Video Facial Expression Grafting onto Normalized 480x640 Daniel
# ---------------------------------------------------------------------------

def apply_daniel_video_expression(base_480x640: np.ndarray, d_idx: int, mode: str) -> np.ndarray:
    """Grafts Daniel's real video facial expressions onto his normalized 480x640 studio views:
      - 'squint'     : Studio pursed-lip blind squint (Video 1 & Video 3)
      - 'ccc_clench' : Gum-baring squared teeth grin from v4_ccc_022.png
      - 'ccc_open'   : Open 'C!' rapid-chant mouth from v4_ccc_012.png
      - 'shaaa'      : Jaw-unhinged 'SHAAAAAAAA!' LAN scream from v2_shaaa_020.png
      - 'panic'      : Wide-eyed 'O'-mouth 'Sorry! Moving the table!' from v1_table4am_018.png
    """
    if mode == "squint" or d_idx in (3, 4, 5):
        return base_480x640.copy()

    out = base_480x640.copy()
    specs = {
        "ccc_clench": ("v4_ccc_022.png", [[255.0, 150.0], [385.0, 148.0], [318.0, 266.0]], [[225.0, 91.0], [254.0, 91.0], [239.5, 112.5]], False, (13.5, 8.8)),
        "ccc_open":   ("v4_ccc_012.png", [[238.0, 102.0], [366.0, 105.0], [298.0, 242.0]], [[225.0, 91.0], [254.0, 91.0], [239.5, 114.0]], False, (12.5, 10.5)),
        "shaaa":      ("v2_shaaa_020.png", [[175.0, 268.0], [235.0, 271.0], [205.0, 355.0]], [[225.0, 91.0], [254.0, 91.0], [239.5, 115.5]], False, (11.2, 11.8)),
        "panic":      ("v1_table4am_018.png", [[159.0, 122.0], [188.0, 122.0], [173.0, 144.0]], [[225.0, 91.0], [254.0, 91.0], [239.5, 113.0]], True,  (9.8, 8.8)),
    }
    fn, s_pts, d_pts, inc_eyes, (rx_m, ry_m) = specs[mode]
    src_im = Image.open(REF_DIR / "frames" / fn).convert("RGB")
    if mode == "panic":
        src_im = src_im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=140, threshold=2))
    src_arr = np.asarray(src_im, dtype=np.float32)

    if d_idx == 0:
        M = cv2.getAffineTransform(np.array(s_pts, dtype=np.float32), np.array(d_pts, dtype=np.float32))
        warped = cv2.warpAffine(src_arr, M, (CANVAS_W, CANVAS_H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

        yg, xg = np.mgrid[0:CANVAS_H, 0:CANVAS_W].astype(np.float32)
        cheek_m = (
            ((((xg - 219.0) / 7.5) ** 2 + ((yg - 101.0) / 8.0) ** 2 < 1.0)
             | (((xg - 260.0) / 7.5) ** 2 + ((yg - 101.0) / 8.0) ** 2 < 1.0))
            & (out[..., 3] > 220)
        )
        tgt_rgb = out[..., :3].astype(np.float32)
        warped_adj = warped.copy()
        for c in range(3):
            t_mu, t_sd = float(tgt_rgb[cheek_m, c].mean()), float(tgt_rgb[cheek_m, c].std() + 1e-4)
            s_mu, s_sd = float(warped[cheek_m, c].mean()), float(warped[cheek_m, c].std() + 1e-4)
            warped_adj[..., c] = np.clip((warped[..., c] - s_mu) * (0.72 * t_sd / s_sd + 0.28) + t_mu, 0.0, 255.0)

        ym_c = d_pts[2][1]
        inner_mouth = ((xg - 239.5) / (rx_m * 0.72)) ** 2 + ((yg - ym_c) / (ry_m * 0.72)) ** 2
        w_raw = np.clip(1.15 - inner_mouth, 0.0, 1.0)[..., None]
        raw_k = 0.70 if mode != "panic" else 0.55
        warped_final = warped_adj * (1.0 - raw_k * w_raw) + warped * (raw_k * w_raw)

        dy_m = yg - ym_c
        ry_eff = np.where(dy_m < 0.0, ry_m * 0.76, ry_m)
        mouth_oval = ((xg - 239.5) / rx_m) ** 2 + (dy_m / ry_eff) ** 2
        w_m = np.clip(1.30 - mouth_oval, 0.0, 1.0)
        if inc_eyes:
            eye_l = ((xg - 225.5) / 8.5) ** 2 + ((yg - 91.0) / 5.4) ** 2
            eye_r = ((xg - 253.5) / 8.5) ** 2 + ((yg - 91.0) / 5.4) ** 2
            w_e = np.clip(1.32 - np.minimum(eye_l, eye_r), 0.0, 1.0) * 0.94
        else:
            w_e = np.zeros_like(w_m)
        w_blend = cv2.GaussianBlur(np.maximum(w_m, w_e).astype(np.float32), (5, 5), 1.2)
        w_blend *= np.clip((130.5 - yg) / 3.0, 0.0, 1.0) * (out[..., 3].astype(np.float32) / 255.0)

        blended = tgt_rgb * (1.0 - w_blend[..., None]) + warped_final * w_blend[..., None]
        out[..., :3] = np.clip(np.round(blended), 0, 255).astype(np.uint8)
        return out

    # Foreshortened real-video mouth warp onto 45°/315° (d=1, 7) and 90°/270° (d=2, 6)!
    is_diag = d_idx in (1, 7)
    is_left = d_idx in (1, 2)
    xm_dst = (205.5 if is_diag else 202.0) if is_left else (CANVAS_W - (205.5 if is_diag else 202.0))
    ym_dst = d_pts[2][1]
    foreshort = 0.56 if is_diag else 0.34
    half_eye = 14.5 * foreshort
    d_pts_side = [
        [xm_dst - half_eye, 91.0],
        [xm_dst + half_eye, 91.0],
        [xm_dst, ym_dst],
    ]
    M_s = cv2.getAffineTransform(np.array(s_pts, dtype=np.float32), np.array(d_pts_side, dtype=np.float32))
    warped_s = cv2.warpAffine(src_arr, M_s, (CANVAS_W, CANVAS_H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

    yg, xg = np.mgrid[0:CANVAS_H, 0:CANVAS_W].astype(np.float32)
    tgt_rgb = out[..., :3].astype(np.float32)
    cheek_x = (xm_dst + 12.0) if is_left else (xm_dst - 12.0)
    cheek_m = (((xg - cheek_x) / 7.0) ** 2 + ((yg - 103.0) / 8.0) ** 2 < 1.0) & (out[..., 3] > 220)
    warped_s_adj = warped_s.copy()
    if np.sum(cheek_m) > 15:
        for c in range(3):
            t_mu, t_sd = float(tgt_rgb[cheek_m, c].mean()), float(tgt_rgb[cheek_m, c].std() + 1e-4)
            s_mu, s_sd = float(warped_s[cheek_m, c].mean()), float(warped_s[cheek_m, c].std() + 1e-4)
            warped_s_adj[..., c] = np.clip((warped_s[..., c] - s_mu) * (0.68 * t_sd / s_sd + 0.32) + t_mu, 0.0, 255.0)

    rx_s = max(3.6, rx_m * foreshort)
    ry_s = ry_m * (0.94 if is_diag else 0.88)
    inner_s = ((xg - xm_dst) / (rx_s * 0.72)) ** 2 + ((yg - ym_dst) / (ry_s * 0.72)) ** 2
    w_raw_s = np.clip(1.15 - inner_s, 0.0, 1.0)[..., None]
    warped_s_fin = warped_s_adj * (1.0 - 0.65 * w_raw_s) + warped_s * (0.65 * w_raw_s)

    dy_s = yg - ym_dst
    ry_s_eff = np.where(dy_s < 0.0, ry_s * 0.76, ry_s)
    m_oval_s = ((xg - xm_dst) / rx_s) ** 2 + (dy_s / ry_s_eff) ** 2
    w_ms = np.clip(1.28 - m_oval_s, 0.0, 1.0)
    if inc_eyes and is_diag:
        xe1 = 203.5 if is_left else (CANVAS_W - 203.5)
        xe2 = 220.0 if is_left else (CANVAS_W - 220.0)
        el_s = ((xg - xe1) / 5.5) ** 2 + ((yg - 91.0) / 4.8) ** 2
        er_s = ((xg - xe2) / 6.2) ** 2 + ((yg - 91.2) / 4.8) ** 2
        w_es = np.clip(1.28 - np.minimum(el_s, er_s), 0.0, 1.0) * 0.88
        w_ms = np.maximum(w_ms, w_es)

    w_bs = cv2.GaussianBlur(w_ms.astype(np.float32), (5, 5), 1.0)
    # Erode head alpha by 1px so profile mouth stays strictly inside lip silhouette
    head_in = cv2.erode(out[..., 3], np.ones((3, 3), np.uint8), iterations=1).astype(np.float32) / 255.0
    w_bs *= np.clip((130.0 - yg) / 3.0, 0.0, 1.0) * head_in

    blended_s = tgt_rgb * (1.0 - w_bs[..., None]) + warped_s_fin * w_bs[..., None]
    out[..., :3] = np.clip(np.round(blended_s), 0, 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------
# 3. Hands-Up "Sorry! I was just moving the table!" Sprint Pose (480x640)
# ---------------------------------------------------------------------------

def render_hands_up_run_frame(
    base_rgba: np.ndarray,
    d_idx: int,
    frame_idx: int,
    n_frames: int = 8,
) -> np.ndarray:
    """Renders Daniel sprinting with BOTH HANDS RAISED defensively ('Sorry! I was just moving
    the table!') by running legs at 1.22x speed and raising forearm bones on front/back/side."""
    # Start from adaptive fast-run frame for crisp lower-body & torso motion, then replace upper arms on d=0,4
    if d_idx not in (0, 4):
        # On diagonal/profile views, lean back slightly in startled defence while sprinting
        fr = render_adaptive_run_frame(base_rgba, d_idx, frame_idx, n_frames, speed_boost=1.20)
        return fr

    is_back = (d_idx == 4)
    H, W = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]
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
    speed_boost = 1.22
    s_l = math.cos(phase - 0.35) * speed_boost
    s_r = -s_l
    bob_dy = sample_run_profile(phase_01)[4] * 0.95 * speed_boost
    sway_dx = -4.0 * math.sin(phase) * speed_boost
    tilt_deg = 2.5 * math.sin(phase)
    wave = math.sin(phase * 2.0)

    def _pose_leg(leg_im, hx, kx, ax, side_sign, s_val):
        if s_val > 0.0:
            lift = min(1.38, s_val)
            return warp_limb_3bone(
                shade_rgba(leg_im, 1.0 if not is_back else 1.0 - 0.08 * lift),
                (hx, float(y_hip)), (kx, 468.0), (ax, 578.0),
                ang_upper=-side_sign * 3.8 * lift,
                ang_lower=side_sign * 4.6 * lift,
                sy_upper=1.0 - (0.26 if not is_back else 0.12) * lift,
                sy_lower=1.0 - (0.18 if not is_back else 0.36) * lift,
                dx=sway_dx, dy=bob_dy - 15.0 * lift,
            )
        p = min(1.38, -s_val)
        return warp_limb_3bone(
            leg_im, (hx, float(y_hip)), (kx, 468.0), (ax, 578.0),
            ang_upper=side_sign * 2.6 * p,
            ang_lower=-side_sign * 1.6 * p,
            dx=sway_dx, dy=max(0.0, bob_dy * 0.4),
        )

    # Raise BOTH arms outward & bend forearms upward into "Whoa, sorry! Hands up!" pose!
    arm_l_p = warp_limb_3bone(
        arm_l, (ls_x, 174.0), (le_x, 266.0), (lw_x, 344.0),
        ang_upper=52.0 + 7.0 * wave,
        ang_lower=86.0 + 8.0 * wave,
        sy_upper=0.90,
        sy_lower=0.92,
        dx=sway_dx, dy=bob_dy - 6.0,
    )
    arm_r_p = warp_limb_3bone(
        arm_r, (rs_x, 174.0), (re_x, 266.0), (rw_x, 344.0),
        ang_upper=-52.0 + 7.0 * wave,
        ang_lower=-86.0 + 8.0 * wave,
        sy_upper=0.90,
        sy_lower=0.92,
        dx=sway_dx, dy=bob_dy - 6.0,
    )
    leg_l_p = _pose_leg(leg_l, lx_h, lx_k, lx_a, -1.0, s_l)
    leg_r_p = _pose_leg(leg_r, rx_h, rx_k, rx_a, +1.0, s_r)
    torso_p = warp_rigid_rgba(torso, (240.0, 260.0), angle_deg=tilt_deg, dx=sway_dx, dy=bob_dy)

    out = np.zeros_like(base_rgba)
    out = alpha_over(alpha_over(out, leg_r_p), leg_l_p)
    if not is_back:
        out = alpha_over(alpha_over(alpha_over(out, torso_p), arm_l_p), arm_r_p)
    else:
        out = alpha_over(alpha_over(alpha_over(out, arm_l_p), arm_r_p), torso_p)
    return out


# ---------------------------------------------------------------------------
# 4. Load Studio Plates, Props, & Custom 2D/3D LAN Visual Elements
# ---------------------------------------------------------------------------

def _crop_prop(arr: np.ndarray, box: tuple[int, int, int, int], target_h: int, flip: bool = False) -> np.ndarray:
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


def make_ccc_glyph_rgba(size: int = 64) -> np.ndarray:
    """Renders a bold, beveled, glowing yellow Quake CCC-Gun 'C' projectile glyph."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    pad = 8
    # Outer warm amber glow
    dr.arc([pad - 3, pad - 3, size - pad + 3, size - pad + 3], start=42, end=318, fill=(255, 180, 0, 135), width=15)
    im = im.filter(ImageFilter.GaussianBlur(2.2))
    dr = ImageDraw.Draw(im)
    # Dark 3D bevel + bright yellow core 'C'
    dr.arc([pad + 2, pad + 3, size - pad + 2, size - pad + 3], start=45, end=315, fill=(120, 72, 0, 240), width=11)
    dr.arc([pad, pad, size - pad, size - pad], start=45, end=315, fill=(255, 232, 36, 255), width=10)
    dr.arc([pad + 2, pad + 2, size - pad - 2, size - pad - 2], start=52, end=308, fill=(255, 252, 185, 235), width=3)
    return np.asarray(im, dtype=np.uint8)


def build_crt_back_view(crt_front: np.ndarray) -> np.ndarray:
    """Synthesizes a convincing beige CRT rear housing (cooling vents + deeper tube back) from the studio CRT."""
    h, w = crt_front.shape[:2]
    im = Image.fromarray(crt_front, "RGBA")
    arr = np.asarray(im, dtype=np.float32)
    a = arr[..., 3] > 32
    # Recolor dark glass screen pixels into warm molded beige plastic rear shell
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    glass = a & (lum < 115.0)
    if np.any(glass):
        arr[glass, 0] = 178.0 + 0.22 * lum[glass]
        arr[glass, 1] = 171.0 + 0.21 * lum[glass]
        arr[glass, 2] = 152.0 + 0.19 * lum[glass]
    out = Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8), "RGBA")
    dr = ImageDraw.Draw(out)
    # Molded horizontal ventilation slots & power cord port on rear CRT shell
    for ry in range(int(h * 0.24), int(h * 0.62), 9):
        dr.line([(int(w * 0.28), ry), (int(w * 0.72), ry)], fill=(96, 92, 82, 210), width=3)
    dr.rounded_rectangle([int(w * 0.42), int(h * 0.68), int(w * 0.58), int(h * 0.79)], radius=3, fill=(52, 50, 48, 235))
    return np.asarray(out, dtype=np.uint8)


def load_all_daniel_assets() -> dict:
    # 1. Daniel 8-direction turnaround + 4 real-video expression sets
    dn_f = key_magenta_studio(Image.open(REF_DIR / "daniel_studio_front.jpg"))
    dn_t = key_magenta_studio(Image.open(REF_DIR / "daniel_studio_turn.jpg"))
    dn_c3, dn_c4 = _extract_clean_c3_c4(
        dn_t,
        [0, 260, 300, 340, 362, 366, 380, 420, 460, 500, 540, 575, 605, 630, 1024],
        [710, 700, 718, 730, 738, 720, 724, 730, 736, 740, 742, 745, 736, 720, 720],
        c4_cx=877.0,
        c4_arm_x=962.0,
        right_ext_px=6,
    )
    dn_5 = [
        crop_normalize_view(dn_f, (200, 60, 700, 1185), False),
        crop_normalize_view(dn_t, (8, 70, 297, 1005), True),
        crop_normalize_view(dn_t, (299, 70, 494, 1005), True),
        crop_normalize_view(dn_c3, (496, 70, 752, 1005), True),
        crop_normalize_view(dn_c4, (710, 70, dn_c4.shape[1], 1005), False),
    ]
    daniel_squint = [
        dn_5[0], dn_5[1], dn_5[2], dn_5[3], dn_5[4],
        mirror_canvas_horiz(dn_5[3]), mirror_canvas_horiz(dn_5[2]), mirror_canvas_horiz(dn_5[1]),
    ]
    daniel_ccc_clench = [apply_daniel_video_expression(daniel_squint[d], d, "ccc_clench") for d in range(8)]
    daniel_ccc_open = [apply_daniel_video_expression(daniel_squint[d], d, "ccc_open") for d in range(8)]
    daniel_shaaa = [apply_daniel_video_expression(daniel_squint[d], d, "shaaa") for d in range(8)]
    daniel_panic = [apply_daniel_video_expression(daniel_squint[d], d, "panic") for d in range(8)]

    # 2. Angry 4 AM Dad 8-direction turnaround (with full un-clipped cream thermal sleeves on d=4!)
    dd_f = key_magenta_studio(Image.open(REF_DIR / "dad_studio_front.jpg"))
    dd_t = key_magenta_studio(Image.open(REF_DIR / "dad_studio_turn.jpg"))
    dd_c3, dd_c4 = _extract_clean_c3_c4(
        dd_t,
        [0, 260, 300, 340, 380, 420, 460, 500, 540, 580, 615, 635, 1024],
        [706, 702, 716, 721, 725, 733, 738, 748, 753, 758, 750, 720, 720],
        c4_cx=884.5,
        c4_arm_x=968.0,
        right_ext_px=13,
    )
    dd_5 = [
        crop_normalize_view(dd_f, (200, 70, 695, 1185), False),
        crop_normalize_view(dd_t, (5, 70, 299, 1005), True),
        crop_normalize_view(dd_t, (301, 70, 494, 1005), True),
        crop_normalize_view(dd_c3, (496, 70, 764, 1005), True),
        crop_normalize_view(dd_c4, (710, 70, dd_c4.shape[1], 1005), False),
    ]
    dad_8 = [
        dd_5[0], dd_5[1], dd_5[2], dd_5[3], dd_5[4],
        mirror_canvas_horiz(dd_5[3]), mirror_canvas_horiz(dd_5[2]), mirror_canvas_horiz(dd_5[1]),
    ]

    # 3. 4 Studio LAN Props from lan_props_studio.jpg
    lp = key_magenta_studio(Image.open(REF_DIR / "lan_props_studio.jpg"))
    table_im = _crop_prop(lp, (25, 35, 490, 480), 205, False)
    table_flip = table_im[:, ::-1, :].copy()
    table_8 = [
        table_im,
        table_im,
        resize_rgba_premul(table_im, int(round(table_im.shape[1] * 0.84)), 205),
        table_flip,
        shade_rgba(table_flip, 0.94),
        table_im,
        resize_rgba_premul(table_flip, int(round(table_flip.shape[1] * 0.84)), 205),
        table_flip,
    ]

    kbd_im = _crop_prop(lp, (530, 115, 1005, 415), 96, False)
    kbd_flip = kbd_im[:, ::-1, :].copy()
    kbd_8 = [kbd_im, kbd_im, kbd_im, kbd_flip, shade_rgba(kbd_flip, 0.88), kbd_flip, kbd_flip, kbd_im]

    cam_im = _crop_prop(lp, (95, 550, 425, 985), 92, False)
    cam_flip = cam_im[:, ::-1, :].copy()
    cam_back = shade_rgba(cam_im, 0.82)
    cam_8 = [cam_im, cam_im, cam_im, cam_back, cam_back, cam_back, cam_flip, cam_flip]

    crt_front = _crop_prop(lp, (545, 550, 995, 985), 152, False)
    crt_back = build_crt_back_view(crt_front)
    crt_side_l = resize_rgba_premul(crt_front, int(round(crt_front.shape[1] * 0.86)), 152)
    crt_side_r = crt_side_l[:, ::-1, :].copy()
    crt_8 = [
        crt_front,
        crt_front,
        crt_side_l,
        resize_rgba_premul(crt_back, int(round(crt_back.shape[1] * 0.90)), 152),
        crt_back,
        resize_rgba_premul(crt_back[:, ::-1, :].copy(), int(round(crt_back.shape[1] * 0.90)), 152),
        crt_side_r,
        crt_front[:, ::-1, :].copy(),
    ]

    return {
        "daniel_squint": daniel_squint,
        "daniel_ccc_clench": daniel_ccc_clench,
        "daniel_ccc_open": daniel_ccc_open,
        "daniel_shaaa": daniel_shaaa,
        "daniel_panic": daniel_panic,
        "dad_8": dad_8,
        "table_8": table_8,
        "kbd_8": kbd_8,
        "cam_8": cam_8,
        "crt_8": crt_8,
        "ccc_glyph": make_ccc_glyph_rgba(64),
    }


# ---------------------------------------------------------------------------
# 5. Full 360° Scene Synthesizer for Daniel (344 frames) & 4 AM Dad (56 frames)
# ---------------------------------------------------------------------------

def build_all_daniel_animations(assets: dict, n_frames: int = 8) -> dict:
    ccc_glyph = assets["ccc_glyph"]

    def _compute_run_grid(char_8: list[np.ndarray], boost: float, hands_up: bool = False) -> list[list[np.ndarray]]:
        tasks = [(d, f) for d in range(8) for f in range(n_frames)]
        fn = (
            (lambda df: render_hands_up_run_frame(char_8[df[0]], df[0], df[1], n_frames))
            if hands_up
            else (lambda df: render_adaptive_run_frame(char_8[df[0]], df[0], df[1], n_frames, speed_boost=boost))
        )
        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
            flat = list(ex.map(fn, tasks))
        return [[flat[d * n_frames + f] for f in range(n_frames)] for d in range(8)]

    raw_run_squint = _compute_run_grid(assets["daniel_squint"], 1.15)
    raw_run_table = _compute_run_grid(assets["daniel_squint"], 1.05)
    raw_run_panic = _compute_run_grid(assets["daniel_panic"], 1.22, hands_up=True)
    raw_run_dad = _compute_run_grid(assets["dad_8"], 1.18)

    dn_idle = []
    dn_fast_run = []
    dn_table_move = []
    dn_ccc_barrage = []
    dn_shaaa_rage = []
    dn_webcam_squint = []
    dn_sorry_panic = []
    dn_lan_station = []

    for d in range(8):
        # 0) Idle
        st_idle = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        draw_contact_shadow(st_idle, STAGE_CX, STAGE_GY, rx=48, ry=10, alpha=84)
        place_char_on_stage(st_idle, assets["daniel_squint"][d], STAGE_CX, STAGE_GY, char_scale=0.74)
        dn_idle.append(np.asarray(st_idle, dtype=np.uint8))

        row_run = []
        row_tbl = []
        row_ccc = []
        row_sha = []
        row_cam = []
        row_pan = []
        row_lan = []

        fwd_screen_x = -math.sin(math.radians(d * 45.0))

        for f in range(n_frames):
            ph = f / float(n_frames)
            ang = 2.0 * math.pi * ph

            # 1) Clean Fast Run (mbox.qc compatible!)
            c_run = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_run, STAGE_CX, STAGE_GY, rx=46, ry=9, alpha=78)
            place_char_on_stage(c_run, raw_run_squint[d][f], STAGE_CX, STAGE_GY, char_scale=0.74)
            row_run.append(np.asarray(c_run, dtype=np.uint8))

            # 2) 4 AM Moving the Honey-Oak Table!
            c_tbl = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            dn_tx, dn_ty, dn_tdz, dn_tsc = project_3d(-24.0, 0.0, 0.0, d)
            tb_tx, tb_ty, tb_tdz, tb_tsc = project_3d(+46.0, 0.0, 0.0, d)
            tbl_jolt = 3.0 * math.sin(ang * 2.0)
            draw_contact_shadow(c_tbl, dn_tx, dn_ty, rx=44 * dn_tsc, ry=9 * dn_tsc, alpha=82)
            draw_contact_shadow(c_tbl, tb_tx, tb_ty, rx=58 * tb_tsc, ry=12 * tb_tsc, alpha=88)

            def _draw_sparks_tbl(c_tbl=c_tbl, tb_tx=tb_tx, tb_ty=tb_ty, f=f):
                dr_s = ImageDraw.Draw(c_tbl)
                for sp_i in range(4):
                    ox_s = tb_tx + (-38 if sp_i < 2 else 38) + ((f * 7 + sp_i * 11) % 14 - 7)
                    oy_s = tb_ty - 4 - (sp_i % 2) * 6
                    dr_s.line([(ox_s, oy_s), (ox_s - fwd_screen_x * 16 - 4, oy_s - 8)], fill=(255, 224, 92, 215), width=2)

            lean_tbl = fwd_screen_x * 7.0
            items_tbl = [
                (dn_tdz, lambda dn_tx=dn_tx, dn_ty=dn_ty, dn_tsc=dn_tsc, lean_tbl=lean_tbl, f=f: place_char_on_stage(
                    c_tbl, raw_run_table[d][f], dn_tx, dn_ty, char_scale=0.72 * dn_tsc, rot_deg=-lean_tbl
                )),
                (tb_tdz, lambda tb_tx=tb_tx, tb_ty=tb_ty, tb_tsc=tb_tsc, tbl_jolt=tbl_jolt: paste_rgba_pil(
                    c_tbl, assets["table_8"][d], tb_tx, tb_ty - abs(tbl_jolt),
                    scale_x=0.92 * tb_tsc, scale_y=0.92 * tb_tsc, rot_deg=tbl_jolt * 0.8, anchor_bottom=True,
                )),
                (tb_tdz - 3.0, _draw_sparks_tbl),
            ]
            for _, fn_t in sorted(items_tbl, key=lambda x: -x[0]):
                fn_t()
            row_tbl.append(np.asarray(c_tbl, dtype=np.uint8))

            # 3) "CCC! C-C-C-C!" Rapid-Chatter Grin Barrage + Orbiting Yellow 'C' Projectiles!
            c_ccc = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_ccc, STAGE_CX, STAGE_GY, rx=48, ry=10, alpha=84)
            ccc_face = assets["daniel_ccc_clench"][d] if (f % 2 == 0) else assets["daniel_ccc_open"][d]
            bounce_c = abs(math.sin(ang * 2.0)) * 9.0
            items_ccc = [
                (0.0, lambda ccc_face=ccc_face, bounce_c=bounce_c, ang=ang: place_char_on_stage(
                    c_ccc, ccc_face, STAGE_CX, STAGE_GY - bounce_c * 0.5,
                    char_scale=0.74, rot_deg=3.0 * math.sin(ang * 2.0),
                    squash_x=1.0 + 0.02 * math.cos(ang * 2.0), stretch_y=1.0 - 0.02 * math.cos(ang * 2.0),
                )),
            ]
            for g_i in range(6):
                g_ph = (ph + g_i / 6.0) % 1.0
                g_ang = g_ph * 2.0 * math.pi + g_i * 0.9
                rad_xy = 54.0 + 38.0 * g_ph
                gx3 = 22.0 + rad_xy * math.cos(g_ang)
                gy3 = rad_xy * math.sin(g_ang)
                gz3 = 185.0 + 95.0 * math.sin(g_ang * 1.5)
                gsx, gsy, gdz, gsc = project_3d(gx3, gy3, gz3, d)
                grot = (g_ph * 360.0 + g_i * 45.0) % 360.0
                gal = float(0.55 + 0.45 * math.sin(math.pi * g_ph))
                items_ccc.append((gdz, lambda gsx=gsx, gsy=gsy, gsc=gsc, grot=grot, gal=gal: paste_rgba_pil(
                    c_ccc, ccc_glyph, gsx, gsy, scale_x=0.72 * gsc, scale_y=0.72 * gsc, rot_deg=grot, alpha_mul=gal
                )))
            for _, fn_c in sorted(items_ccc, key=lambda x: -x[0]):
                fn_c()
            row_ccc.append(np.asarray(c_ccc, dtype=np.uint8))

            # 4) "SHAAAAAAAAAAAA!" Neon LAN Rage Scream (Glowing RGB Keyboard + Sonic Shockwave Rings!)
            c_sha = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            shake_s = (-3.5 if f % 2 == 0 else +3.5)
            # Neon green/cyan radial aura behind Daniel
            aura = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            dr_a = ImageDraw.Draw(aura)
            for r_i in range(2):
                r_ph = (ph + r_i * 0.5) % 1.0
                rr = int(55 + 145 * r_ph)
                al_r = int(165 * (1.0 - r_ph))
                col_r = (50, 255, 130, al_r) if r_i == 0 else (56, 220, 255, al_r)
                dr_a.ellipse([STAGE_CX - rr, STAGE_GY - 260 - int(rr * 0.85), STAGE_CX + rr, STAGE_GY - 260 + int(rr * 0.85)], outline=col_r, width=4)
            c_sha.alpha_composite(aura.filter(ImageFilter.GaussianBlur(1.2)))
            draw_contact_shadow(c_sha, STAGE_CX, STAGE_GY, rx=50, ry=10, alpha=84)

            kb_sx, kb_sy, kb_dz, kb_sc = project_3d(34.0, 0.0, 205.0 + 10.0 * math.sin(ang * 2.0), d)
            kb_rot = -14.0 + 10.0 * math.sin(ang * 2.0)
            items_sha = [
                (0.0, lambda shake_s=shake_s: place_char_on_stage(
                    c_sha, assets["daniel_shaaa"][d], STAGE_CX + shake_s, STAGE_GY,
                    char_scale=0.74, rot_deg=shake_s * 0.5, stretch_y=1.02,
                )),
                (kb_dz, lambda kb_sx=kb_sx, kb_sy=kb_sy, kb_sc=kb_sc, kb_rot=kb_rot: paste_rgba_pil(
                    c_sha, assets["kbd_8"][d], kb_sx, kb_sy, scale_x=0.88 * kb_sc, scale_y=0.88 * kb_sc, rot_deg=kb_rot
                )),
            ]
            for _, fn_s in sorted(items_sha, key=lambda x: -x[0]):
                fn_s()
            row_sha.append(np.asarray(c_sha, dtype=np.uint8))

            # 5) "Justin Berry's Webcam!" Blind Squint + Extended Eyeball QuickCam w/ Blinking Red LED!
            c_cam = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_cam, STAGE_CX, STAGE_GY, rx=48, ry=10, alpha=84)
            wc_sx, wc_sy, wc_dz, wc_sc = project_3d(42.0, -24.0, 238.0 + 7.0 * math.sin(ang), d)
            lean_cam = fwd_screen_x * 5.5

            def _draw_webcam_prop(c_cam=c_cam, wc_sx=wc_sx, wc_sy=wc_sy, wc_sc=wc_sc, f=f):
                paste_rgba_pil(c_cam, assets["cam_8"][d], wc_sx, wc_sy, scale_x=0.80 * wc_sc, scale_y=0.80 * wc_sc)
                if f % 2 == 0:
                    dr_w = ImageDraw.Draw(c_cam)
                    dr_w.ellipse([wc_sx - 4, wc_sy - 24, wc_sx + 4, wc_sy - 16], fill=(255, 42, 42, 235))

            items_cam = [
                (0.0, lambda lean_cam=lean_cam, ang=ang: place_char_on_stage(
                    c_cam, assets["daniel_squint"][d], STAGE_CX + fwd_screen_x * 4.0, STAGE_GY,
                    char_scale=0.74, rot_deg=-lean_cam + 2.0 * math.sin(ang),
                )),
                (wc_dz, _draw_webcam_prop),
            ]
            for _, fn_w in sorted(items_cam, key=lambda x: -x[0]):
                fn_w()
            row_cam.append(np.asarray(c_cam, dtype=np.uint8))

            # 6) Hands-Up "Sorry! I was just moving the table!" Panic Sprint!
            c_pan = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(c_pan, STAGE_CX, STAGE_GY, rx=48, ry=9, alpha=76)
            dr_p = ImageDraw.Draw(c_pan)
            for s_i in range(4):
                lz_s = 95.0 + s_i * 62.0
                ly_s = (-26.0 if s_i % 2 == 0 else 26.0)
                sx0, sy0, _, _ = project_3d(-18.0, ly_s, lz_s, d)
                sx1, sy1, _, _ = project_3d(-88.0 - 20.0 * ((f + s_i) % 3), ly_s, lz_s, d)
                dr_p.line([(sx0, sy0), (sx1, sy1)], fill=(185, 232, 255, 155 - s_i * 25), width=3)
            place_char_on_stage(c_pan, raw_run_panic[d][f], STAGE_CX, STAGE_GY, char_scale=0.74)
            # Flying panic sweat drops near temples
            for sw_i in range(2):
                sw_ph = (ph * 2.0 + sw_i * 0.5) % 1.0
                sw_x, sw_y, _, _ = project_3d(-8.0 - 28.0 * sw_ph, (-24.0 if sw_i == 0 else 24.0) * (1.0 + sw_ph), 342.0 + 18.0 * sw_ph - 26.0 * (sw_ph ** 2), d)
                al_sw = int(210 * (1.0 - sw_ph))
                dr_p.ellipse([sw_x - 3, sw_y - 5, sw_x + 3, sw_y + 5], fill=(125, 215, 255, al_sw))
            row_pan.append(np.asarray(c_pan, dtype=np.uint8))

            # 7) Full 360° Bakersfield LAN Station (Daniel + Honey-Oak Table + 19990 Quake CRT + RGB Keyboard + QuickCam!)
            c_lan = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            crt_view_idx = (d + 4) % 8  # CRT faces Daniel (-X) just like David's slot machine!
            dl_sx, dl_sy, dl_dz, dl_sc = project_3d(-38.0, -20.0, 0.0, d)
            tb_sx, tb_sy, tb_dz, tb_sc = project_3d(+38.0, +18.0, 0.0, d)
            mon_sx, mon_sy, mon_dz, mon_sc = project_3d(+44.0, +22.0, 156.0, d)
            kb2_sx, kb2_sy, kb2_dz, kb2_sc = project_3d(+16.0, +10.0, 158.0, d)
            cm2_sx, cm2_sy, cm2_dz, cm2_sc = project_3d(+44.0, +22.0, 278.0, d)

            draw_contact_shadow(c_lan, dl_sx, dl_sy, rx=42 * dl_sc, ry=9 * dl_sc, alpha=82)
            draw_contact_shadow(c_lan, tb_sx, tb_sy, rx=56 * tb_sc, ry=12 * tb_sc, alpha=90)

            # Cycle Daniel's LAN expression across the 8 frames (intense squint -> CCC grin -> SHAAA!)
            if f in (2, 3):
                lan_char = assets["daniel_ccc_clench"][d]
            elif f in (5, 6):
                lan_char = assets["daniel_shaaa"][d]
            else:
                lan_char = assets["daniel_squint"][d]
            lan_bob = 3.5 * abs(math.sin(ang * 2.0))

            items_lan = [
                (dl_dz, lambda lan_char=lan_char, dl_sx=dl_sx, dl_sy=dl_sy, dl_sc=dl_sc, lan_bob=lan_bob: place_char_on_stage(
                    c_lan, lan_char, dl_sx, dl_sy - lan_bob, char_scale=0.71 * dl_sc, rot_deg=-fwd_screen_x * 4.5
                )),
                (tb_dz + 2.0, lambda tb_sx=tb_sx, tb_sy=tb_sy, tb_sc=tb_sc: paste_rgba_pil(
                    c_lan, assets["table_8"][d], tb_sx, tb_sy, scale_x=0.86 * tb_sc, scale_y=0.82 * tb_sc, anchor_bottom=True
                )),
                (kb2_dz, lambda kb2_sx=kb2_sx, kb2_sy=kb2_sy, kb2_sc=kb2_sc: paste_rgba_pil(
                    c_lan, assets["kbd_8"][d], kb2_sx, kb2_sy, scale_x=0.68 * kb2_sc, scale_y=0.68 * kb2_sc
                )),
                (mon_dz, lambda mon_sx=mon_sx, mon_sy=mon_sy, mon_sc=mon_sc, crt_view_idx=crt_view_idx: paste_rgba_pil(
                    c_lan, assets["crt_8"][crt_view_idx], mon_sx, mon_sy, scale_x=0.84 * mon_sc, scale_y=0.84 * mon_sc, anchor_bottom=True
                )),
                (cm2_dz - 1.0, lambda cm2_sx=cm2_sx, cm2_sy=cm2_sy, cm2_sc=cm2_sc, crt_view_idx=crt_view_idx: paste_rgba_pil(
                    c_lan, assets["cam_8"][crt_view_idx], cm2_sx, cm2_sy, scale_x=0.44 * cm2_sc, scale_y=0.44 * cm2_sc, anchor_bottom=True
                )),
            ]
            for _, fn_l in sorted(items_lan, key=lambda x: -x[0]):
                fn_l()
            row_lan.append(np.asarray(c_lan, dtype=np.uint8))

        dn_fast_run.append(row_run)
        dn_table_move.append(row_tbl)
        dn_ccc_barrage.append(row_ccc)
        dn_shaaa_rage.append(row_sha)
        dn_webcam_squint.append(row_cam)
        dn_sorry_panic.append(row_pan)
        dn_lan_station.append(row_lan)

    # 8. Build Angry 4 AM Dad (8-dir Idle + 8-dir Angry Charge Run)
    dad_idle = []
    dad_run = []
    for d in range(8):
        st_di = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        draw_contact_shadow(st_di, STAGE_CX, STAGE_GY, rx=46, ry=10, alpha=84)
        place_char_on_stage(st_di, assets["dad_8"][d], STAGE_CX, STAGE_GY, char_scale=0.75)
        dad_idle.append(np.asarray(st_di, dtype=np.uint8))

        row_dr = []
        for f in range(n_frames):
            st_dr = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            draw_contact_shadow(st_dr, STAGE_CX, STAGE_GY, rx=46, ry=9, alpha=78)
            place_char_on_stage(st_dr, raw_run_dad[d][f], STAGE_CX, STAGE_GY, char_scale=0.75)
            row_dr.append(np.asarray(st_dr, dtype=np.uint8))
        dad_run.append(row_dr)

    return {
        "daniel": {
            "idle": dn_idle,
            "fast_run": dn_fast_run,
            "table_move": dn_table_move,
            "ccc_barrage": dn_ccc_barrage,
            "shaaa_rage": dn_shaaa_rage,
            "webcam_squint": dn_webcam_squint,
            "sorry_panic": dn_sorry_panic,
            "lan_station": dn_lan_station,
        },
        "dad": {
            "idle": dad_idle,
            "run": dad_run,
        },
    }
