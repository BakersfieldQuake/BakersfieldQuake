"""Concept 2: "HUMAN BELLY-SLING" (Throwing an Entire Guy).

Generates all 60-FPS sprite assets for Design 2 in `work/c2_throwguy/`:
- First-person viewmodel (`420x360`):
  - `vm_idle_00..59.png` (60 frames): Armored gauntlets hoisting an entire squirming
    shirtless bloke in tricolor shorts across the lower/center screen, with oversized
    swapped comic heads bobbing/swaying/eye-darting, belly jiggling, arms waving,
    legs kicking, two mini tricolor flags fluttering from his waistband, and buzzing flies.
  - `vm_fire_00..19.png` (20 frames): Belly squeeze windup -> explosive green-brown fart
    blast & mud mist -> violent forward throw/yeet toward crosshair with open-hand
    gauntlet follow-through.
  - `vm_reload_00..17.png` (18 frames): Gauntlets dip down and snatch a fresh squirming
    bloke up from below with heavy overshoot bounce and belly-jiggle rebound.
- Projectile (`220x220`, 16 angles x 8 frames):
  - `proj_a00_f00.png` .. `proj_a15_f07.png`: Airborne cartwheeling/screaming thrown
    bloke (`turn_16` + `dance_48` + comic screaming heads) propelled by a brown fart/mud
    jet and chased by swarming flies.
- 3rd-Person Shooter (`360x380`):
  - `tp_idle_00..23.png` (24 frames), `tp_fire_00..15.png` (16 frames),
    `tp_reload_00..11.png` (12 frames): Enemy grunt hoisting and chucking the full-body
    bloke straight at the camera with waving waistband flags, flies, and fart-cloud burst.
- `manifest.json` + `contact_sheet_c2.png`.
"""
from __future__ import annotations

import glob
import json
import math
import os
from typing import Dict, List, Sequence, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from poop_core import (
    WORK_DIR,
    from_premul,
    key_white_studio_plate,
    resize_premul,
    to_premul,
)
from poop_fx import (
    alpha_over,
    render_fly_swarm,
    render_tricolor_flag,
    warp_rgba,
)

OUT_DIR = os.path.join(WORK_DIR, "c2_throwguy")
GAUNTLET_PLATE = (
    r"C:\Users\qxdc\.gemini\antigravity\brain"
    r"\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841\gauntlet_hands_c2_1794663557435.jpg"
)
ENEMY_BASE_PNG = os.path.join(WORK_DIR, "fx", "enemy_shooter_base.png")

VM_W, VM_H = 420, 360
PROJ_W, PROJ_H = 220, 220
TP_W, TP_H = 360, 380

# Cleanest front/quarter dance_48 frames (skipping 26-27 trapped-white artifacts)
CLEAN_IDLE_DANCE_INDICES: List[int] = (
    list(range(0, 10))
    + list(range(9, 0, -1))
    + list(range(28, 48))
    + list(range(46, 28, -1))
)


def _load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def _clean_trapped_white_arms(rgba: np.ndarray, x_left: int, x_right: int, y_max: int) -> np.ndarray:
    """Remove small trapped white background triangles in arm-hip gaps without
    touching the central white tricolor shorts band.
    """
    out = rgba.copy()
    arr = out[..., :3].astype(np.float32)
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    gap_zone = ((xx < x_left) | (xx > x_right)) & (yy < y_max)
    bad = gap_zone & (out[..., 3] > 0) & (lo > 218.0) & (sat < 0.085)
    if np.any(bad):
        out[bad] = 0
    return out


def _defringe_curly_hair(head_rgba: np.ndarray) -> np.ndarray:
    """Remove white/grey studio-backlight fringe and trapped bright pockets from
    the outer curly hair on video-extracted heads while preserving eyes/teeth/skin.
    """
    out = head_rgba.copy()
    h, w = out.shape[:2]
    arr = out[..., :3].astype(np.float32)
    a = out[..., 3].astype(np.float32)
    fg = a > 10
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    in_face_core = (((xx - w * 0.50) / (w * 0.26)) ** 2 + ((yy - h * 0.56) / (h * 0.29)) ** 2) < 1.0
    hair_zone = fg & (~in_face_core) & (yy < h * 0.58)

    white_pocket = hair_zone & (lo > 175.0) & (sat < 0.14)
    a[white_pocket] = 0.0

    fg2 = a > 10
    dist2 = ndimage.distance_transform_edt(fg2)
    rim = hair_zone & fg2 & (dist2 < 12.0) & (sat < 0.24)
    kill_alpha = rim & (dist2 < 4.5) & (lum > 115.0)
    a[kill_alpha] *= np.clip((155.0 - lum[kill_alpha]) / 45.0, 0.0, 1.0) * 0.25

    t_dark = np.where(rim & (lum > 72.0), np.clip((lum - 72.0) / 110.0, 0.0, 0.94), 0.0)
    target = np.array([22.0, 18.0, 16.0], dtype=np.float32)
    arr = arr * (1.0 - t_dark[..., None]) + target * t_dark[..., None]

    out[..., :3] = np.clip(np.round(arr), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a), 0, 255).astype(np.uint8)
    out[out[..., 3] < 10] = 0
    return out


def _clean_head_edge(rgba: np.ndarray, name: str) -> np.ndarray:
    """Trim stray finger/shoulder specks and defringe curly-hair studio halo."""
    out = rgba.copy()
    if name == "head_side_yell_l":
        out[:, :34] = 0
    elif name == "head_side_yell_r":
        out[:, 226:] = 0
    if name in ("head_scream_front", "head_laugh_tilt", "head_sky_gasp", "head_wide_grin"):
        out = _defringe_curly_hair(out)
    return out


def _erase_original_head(body_rgba: np.ndarray) -> np.ndarray:
    """Isolate and softly erase the small original head/hair in a `dance_48` body
    frame regardless of head sway while keeping both raised waving arms intact.
    """
    out = body_rgba.copy()
    h, w = out.shape[:2]

    # Above y=118 the head/hair component is completely disconnected from raised arms
    top = out[:118, :, 3] > 10
    lbl, n = ndimage.label(top)
    best_id, best_d, hx_mean = 0, 1e9, 168.0
    for cid in range(1, n + 1):
        ys, xs = np.nonzero(lbl == cid)
        if len(xs) < 100:
            continue
        xm = float(xs.mean())
        d = abs(xm - 168.0)
        if d < best_d:
            best_d = d
            best_id = cid
            hx_mean = xm

    head_mask = np.zeros((h, w), dtype=bool)
    if best_id > 0:
        head_mask[:118, :] = ndimage.binary_dilation(lbl == best_id, iterations=4)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ell = ((xx - hx_mean) / 40.0) ** 2 + ((yy - 94.0) / 36.0) ** 2
    clear_mask = head_mask | (ell < 1.0)
    dist = ndimage.distance_transform_edt(~clear_mask)
    keep = np.clip(dist / 2.5, 0.0, 1.0)
    out[..., 3] = np.clip(np.round(out[..., 3].astype(np.float32) * keep), 0, 255).astype(np.uint8)
    out[out[..., 3] < 4] = 0
    return out


def _extract_gauntlets(plate_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Key left and right armored gauntlets separately so neither is dropped as a
    secondary connected component by `key_white_studio_plate`.
    """
    rgb = np.asarray(Image.open(plate_path).convert("RGB"))
    h, w = rgb.shape[:2]
    half = w // 2
    left_rgba = key_white_studio_plate(rgb[:, :half])
    right_rgba = key_white_studio_plate(rgb[:, half:])

    def _fit_crop(rgba: np.ndarray, target_h: int) -> np.ndarray:
        ys, xs = np.nonzero(rgba[..., 3] > 16)
        crop = rgba[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
        sc = target_h / float(crop.shape[0])
        nw = max(8, int(round(crop.shape[1] * sc)))
        nh = max(8, int(round(crop.shape[0] * sc)))
        return resize_premul(crop, (nw, nh))

    return _fit_crop(left_rgba, 228), _fit_crop(right_rgba, 228)


def _splay_gauntlet_open(hand_rgba: np.ndarray, is_left: bool, amount: float) -> np.ndarray:
    """Uncurl the gauntlet's fingers outward/upward for open-hand throw follow-through."""
    if amount <= 0.01:
        return hand_rgba
    h, w = hand_rgba.shape[:2]
    pad = 26
    padded = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)
    padded[pad:pad + h, pad:pad + w] = hand_rgba
    ph, pw = padded.shape[:2]
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)

    # Fingers sit in the upper ~46% of the gauntlet sprite
    top_weight = np.clip((pad + h * 0.48 - yy) / (h * 0.42), 0.0, 1.0) ** 1.4
    out_dir = -1.0 if is_left else 1.0
    dx = out_dir * (20.0 * amount) * top_weight
    dy = -(10.0 * amount) * top_weight

    pm = to_premul(padded)
    warped = cv2.remap(
        pm,
        (xx - dx).astype(np.float32),
        (yy - dy).astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )
    return from_premul(warped)


def _deform_body_comedy(
    body_rgba: np.ndarray,
    jiggle_x: float,
    jiggle_y: float,
    belly_squeeze: float,
    kick_phase: float,
    kick_amp: float = 1.0,
) -> np.ndarray:
    """Apply localized belly jiggle/squeeze and opposite-phase lower-leg kicking
    to a headless `dance_48` body sprite (`340x460`).
    """
    h, w = body_rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # 1. Big belly jiggle & gauntlet squeeze bulge around (168, 222)
    bx = (xx - 168.0) / 56.0
    by = (yy - 222.0) / 48.0
    belly_w = np.exp(-1.15 * (bx * bx + by * by))

    # Squeeze pulls sides inward horizontally while pushing belly mass up & out
    squeeze_dx = -belly_squeeze * 0.48 * (xx - 168.0) * belly_w
    squeeze_dy = -belly_squeeze * 14.0 * belly_w
    disp_x = belly_w * jiggle_x + squeeze_dx
    disp_y = belly_w * jiggle_y + squeeze_dy

    # 2. Frantic kicking legs below waistband (y > 325)
    leg_w = np.clip((yy - 320.0) / 95.0, 0.0, 1.0) ** 1.35
    # Smooth left/right split around x=169
    side_sign = np.tanh((xx - 169.0) / 14.0)
    k_l = math.sin(kick_phase)
    k_r = math.sin(kick_phase + math.pi)
    kick_mix = np.where(side_sign < 0.0, k_l, k_r)
    disp_x += leg_w * (13.5 * kick_amp * kick_mix + 4.5 * kick_amp * side_sign * abs(k_l))
    disp_y -= leg_w * (7.5 * kick_amp * np.abs(kick_mix))

    pm = to_premul(body_rgba)
    warped = cv2.remap(
        pm,
        (xx - disp_x).astype(np.float32),
        (yy - disp_y).astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )
    return from_premul(warped)


def _animate_head_eyes(
    head_rgba: np.ndarray,
    dart_x: float,
    dart_y: float,
    squint: float = 0.0,
) -> np.ndarray:
    """Subtle comical eye-bulge / squash-bob on a 256x256 comic head."""
    if abs(dart_x) < 0.2 and abs(dart_y) < 0.2 and abs(squint) < 0.01:
        return head_rgba
    h, w = head_rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Eye band sits around y = 0.42 * h, x = 0.34*w and 0.66*w
    e_l = np.exp(-(((xx - w * 0.36) / 26.0) ** 2 + ((yy - h * 0.43) / 20.0) ** 2))
    e_r = np.exp(-(((xx - w * 0.64) / 26.0) ** 2 + ((yy - h * 0.43) / 20.0) ** 2))
    eye_w = np.clip(e_l + e_r, 0.0, 1.0)
    dx = eye_w * dart_x
    dy = eye_w * dart_y + eye_w * squint * (yy - h * 0.43) * 0.22
    pm = to_premul(head_rgba)
    warped = cv2.remap(
        pm,
        (xx - dx).astype(np.float32),
        (yy - dy).astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )
    return from_premul(warped)


def _draw_flag_pole(canvas: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    """Draw a crisp mini brass-tipped wooden pole tucked into the bloke's waistband."""
    out = canvas.copy()
    p0 = (int(round(x0)), int(round(y0)))
    p1 = (int(round(x1)), int(round(y1)))
    cv2.line(out, p0, p1, (76, 48, 22, 255), thickness=4, lineType=cv2.LINE_AA)
    cv2.line(out, p0, p1, (152, 108, 52, 255), thickness=2, lineType=cv2.LINE_AA)
    cv2.circle(out, p1, 3, (232, 192, 72, 255), -1, cv2.LINE_AA)
    return out


def _compose_squirming_bloke(
    assets: Dict[str, object],
    body_idx: int,
    head_name: str,
    t_norm: float,
    jiggle_x: float,
    jiggle_y: float,
    belly_squeeze: float,
    kick_phase: float,
    kick_amp: float,
    head_bob_x: float,
    head_bob_y: float,
    head_tilt: float,
    head_scale: float,
    eye_dart: Tuple[float, float],
    flag_phase: float,
    flag_amp: float = 1.0,
) -> np.ndarray:
    """Compose the full-body shirtless bloke (`340x460` base padded to `420x480`)
    with headless animated body, jiggling belly, kicking legs, two fluttering
    waistband tricolor flags, and oversized swapped expressive head.
    """
    bodies: List[np.ndarray] = assets["dance_headless"]  # type: ignore[assignment]
    heads: Dict[str, np.ndarray] = assets["heads"]  # type: ignore[assignment]

    raw_body = bodies[body_idx % len(bodies)]
    deformed = _deform_body_comedy(
        raw_body,
        jiggle_x=jiggle_x,
        jiggle_y=jiggle_y,
        belly_squeeze=belly_squeeze,
        kick_phase=kick_phase,
        kick_amp=kick_amp,
    )

    cw, ch = 420, 480
    ox, oy = 40, 14
    canvas = np.zeros((ch, cw, 4), dtype=np.uint8)

    # 1. Two mini tricolor flags tucked into left & right waistband hips, angled high enough
    # to clear the hoisting gauntlets cleanly
    fl = render_tricolor_flag(82, 50, phase=flag_phase, pole_left=False, amp=flag_amp)
    fr = render_tricolor_flag(82, 50, phase=flag_phase + 1.15, pole_left=True, amp=flag_amp)

    fl_rot = warp_rgba(
        fl,
        angle_deg=28.0 + 4.0 * math.sin(flag_phase),
        pivot=(fl.shape[1] - 4.0, fl.shape[0] * 0.5),
        out_hw=(102, 116),
    )
    fr_rot = warp_rgba(
        fr,
        angle_deg=-28.0 + 4.0 * math.cos(flag_phase),
        pivot=(4.0, fr.shape[0] * 0.5),
        out_hw=(102, 116),
    )

    # Pole roots inside left & right waistband (118, 268) and (220, 268) angled upward
    lx0, ly0 = ox + 118.0, oy + 268.0
    lx1, ly1 = ox + 58.0, oy + 194.0
    rx0, ry0 = ox + 220.0, oy + 268.0
    rx1, ry1 = ox + 280.0, oy + 194.0

    canvas = _draw_flag_pole(canvas, lx0, ly0, lx1, ly1)
    canvas = _draw_flag_pole(canvas, rx0, ry0, rx1, ry1)
    canvas = alpha_over(canvas, fl_rot, lx1 - 84.0, ly1 - 20.0)
    canvas = alpha_over(canvas, fr_rot, rx1 - 14.0, ry1 - 20.0)

    # 2. Deformed full body on top of pole roots
    canvas = alpha_over(canvas, deformed, ox, oy)

    # 3. Oversized expressive swapped head at neck (168, 90)
    head_src = _animate_head_eyes(
        heads[head_name],
        dart_x=eye_dart[0],
        dart_y=eye_dart[1],
        squint=0.12 * math.sin(2.0 * math.pi * 3.0 * t_norm),
    )
    h_sz = int(round(136.0 * head_scale))
    head_rs = resize_premul(head_src, (h_sz, h_sz))
    pad = 24
    h_pad = np.zeros((h_sz + pad * 2, h_sz + pad * 2, 4), dtype=np.uint8)
    h_pad[pad:pad + h_sz, pad:pad + h_sz] = head_rs
    head_rot = warp_rgba(
        h_pad,
        angle_deg=head_tilt,
        dx=head_bob_x,
        dy=head_bob_y,
        pivot=(h_pad.shape[1] * 0.5, h_pad.shape[0] * 0.58),
    )
    hx = ox + 168.0 - head_rot.shape[1] * 0.5
    hy = oy + 86.0 - head_rot.shape[0] * 0.52
    canvas = alpha_over(canvas, head_rot, hx, hy)
    return canvas


def _add_fart_blast(
    canvas: np.ndarray,
    mists: List[np.ndarray],
    globs: List[np.ndarray],
    cx: float,
    cy: float,
    progress: float,
    strength: float = 1.0,
) -> np.ndarray:
    """Layer billowing green-brown fart plumes, noxious stink glow, and mud globs."""
    out = canvas.copy()
    if progress <= 0.0 or progress >= 1.0:
        return out

    fade = math.sin(math.pi * progress) ** 0.75 * strength
    # Subtle green-brown fart flash halo behind shorts
    h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rad = 48.0 + 110.0 * progress
    glow = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (rad * rad))) * 0.65 * fade
    glow_layer = np.zeros((h, w, 4), dtype=np.uint8)
    glow_layer[..., 0] = 132
    glow_layer[..., 1] = 158
    glow_layer[..., 2] = 44
    glow_layer[..., 3] = np.clip(np.round(glow * 255.0), 0, 255).astype(np.uint8)
    out = alpha_over(out, glow_layer, 0, 0)

    # Billowing green-brown mist puffs (indices 1, 3, 5 are toxic fart green-brown; 0, 2 brown)
    puff_specs = [
        (1, -28.0, 12.0, 0.85, 0.95),
        (3, 30.0, 8.0, 0.90, 0.90),
        (5, 0.0, -18.0, 1.10, 1.00),
        (0, -12.0, 24.0, 0.78, 0.80),
        (2, 16.0, -6.0, 0.82, 0.85),
    ]
    for idx, ox, oy, sc_mul, op_mul in puff_specs:
        mist = mists[idx % len(mists)]
        sc = (0.65 + 1.15 * progress) * sc_mul * strength
        nw = max(12, int(round(mist.shape[1] * sc)))
        nh = max(12, int(round(mist.shape[0] * sc)))
        m_rs = resize_premul(mist, (nw, nh))
        px = cx + ox * (0.5 + 1.3 * progress) - nw * 0.5
        py = cy + oy * (0.5 + 1.1 * progress) - 18.0 * progress - nh * 0.5
        out = alpha_over(out, m_rs, px, py, opacity=min(1.0, fade * op_mul))

    # Flying mud globs sprayed out by the fart blast
    for i in range(6):
        ang = -math.pi * 0.85 + (math.pi * 0.70) * (i / 5.0) + 0.25 * math.sin(i * 2.1)
        dist = (18.0 + 115.0 * (progress ** 0.75)) * (0.8 + 0.12 * (i % 3)) * strength
        gx = cx + math.cos(ang) * dist
        gy = cy + math.sin(ang) * dist * 0.75 + 22.0 * progress * progress
        g_src = globs[i % len(globs)]
        g_sc = (0.28 + 0.16 * (i % 2)) * (1.0 - 0.35 * progress)
        gsz = max(8, int(round(g_src.shape[0] * g_sc)))
        g_rs = resize_premul(g_src, (gsz, gsz))
        out = alpha_over(out, g_rs, gx - gsz * 0.5, gy - gsz * 0.5, opacity=min(1.0, fade * 1.1))

    return out


def _compose_vm_frame(
    assets: Dict[str, object],
    bloke_rgba: np.ndarray,
    bloke_cx: float,
    bloke_cy: float,
    bloke_scale: float,
    bloke_angle: float,
    hand_dx_in: float,
    hand_dy: float,
    hand_scale: float,
    hand_splay: float,
    hand_rot: float,
    fart_prog: float,
    fart_cx: float,
    fart_cy: float,
    fly_t: float,
    fly_centers: Sequence[Tuple[float, float]],
    n_flies: int = 12,
    fart_behind: bool = True,
) -> np.ndarray:
    """Assemble a single 420x360 first-person viewmodel frame."""
    canvas = np.zeros((VM_H, VM_W, 4), dtype=np.uint8)
    mists: List[np.ndarray] = assets["mists"]  # type: ignore[assignment]
    globs: List[np.ndarray] = assets["globs"]  # type: ignore[assignment]

    if fart_behind and fart_prog > 0.0:
        canvas = _add_fart_blast(canvas, mists, globs, fart_cx, fart_cy, fart_prog, strength=1.40)

    # Layer full-body squirming bloke
    if bloke_scale > 0.02:
        bw = max(8, int(round(bloke_rgba.shape[1] * bloke_scale)))
        bh = max(8, int(round(bloke_rgba.shape[0] * bloke_scale)))
        b_rs = resize_premul(bloke_rgba, (bw, bh))
        pad = 40
        b_pad = np.zeros((bh + pad * 2, bw + pad * 2, 4), dtype=np.uint8)
        b_pad[pad:pad + bh, pad:pad + bw] = b_rs
        b_rot = warp_rgba(
            b_pad,
            angle_deg=bloke_angle,
            pivot=(b_pad.shape[1] * 0.5, b_pad.shape[0] * 0.5),
        )
        canvas = alpha_over(
            canvas,
            b_rot,
            bloke_cx - b_rot.shape[1] * 0.5,
            bloke_cy - b_rot.shape[0] * 0.5,
        )

    if (not fart_behind) and fart_prog > 0.0:
        canvas = _add_fart_blast(canvas, mists, globs, fart_cx, fart_cy, fart_prog, strength=0.95)

    # Layer left & right armored gauntlets gripping his waist/belly (or splayed open)
    gl = _splay_gauntlet_open(assets["gauntlet_l"], True, hand_splay)  # type: ignore[arg-type]
    gr = _splay_gauntlet_open(assets["gauntlet_r"], False, hand_splay)  # type: ignore[arg-type]

    pad_g = 40
    gl_hw = (gl.shape[0] + pad_g * 2, gl.shape[1] + pad_g * 2)
    gr_hw = (gr.shape[0] + pad_g * 2, gr.shape[1] + pad_g * 2)
    gl_w = warp_rgba(
        gl,
        angle_deg=-hand_rot,
        sx=hand_scale,
        sy=hand_scale,
        dx=pad_g,
        dy=pad_g,
        pivot=(gl.shape[1] * 0.35, gl.shape[0] * 0.98),
        out_hw=gl_hw,
    )
    gr_w = warp_rgba(
        gr,
        angle_deg=hand_rot,
        sx=hand_scale,
        sy=hand_scale,
        dx=pad_g,
        dy=pad_g,
        pivot=(gr.shape[1] * 0.65, gr.shape[0] * 0.98),
        out_hw=gr_hw,
    )

    # Positioned so cupped fingers grip the bloke's flanks; bottom stays anchored below VM_H
    lx = 16.0 - pad_g + hand_dx_in
    rx = VM_W - 16.0 + pad_g - gr_w.shape[1] - hand_dx_in
    ly = VM_H - gl.shape[0] - pad_g + 24.0 + max(-6.0, hand_dy)
    ry = VM_H - gr.shape[0] - pad_g + 24.0 + max(-6.0, hand_dy)

    canvas = alpha_over(canvas, gl_w, lx, ly)
    canvas = alpha_over(canvas, gr_w, rx, ry)

    # Layer animated flies orbiting shorts & oversized head
    canvas = render_fly_swarm(canvas, fly_centers, t_norm=fly_t, n_flies=n_flies, scale=0.95)
    return canvas


def generate_vm_sequences(assets: Dict[str, object]) -> Dict[str, List[str]]:
    """Bake 60 idle, 20 fire/yeet, and 18 reload/snatch viewmodel frames."""
    idle_heads = [
        "head_cross",
        "head_scream_front",
        "head_turban_grin",
        "head_sky_gasp",
        "head_wide_grin",
    ]
    n_dance = len(CLEAN_IDLE_DANCE_INDICES)

    # 1. Idle (60 frames, seamless 60fps loop)
    idle_files: List[str] = []
    for f in range(60):
        t = f / 60.0
        tau = 2.0 * math.pi
        body_idx = int(round(t * n_dance)) % n_dance

        # Cycle comic expression cleanly every 12 frames with a playful pop bounce
        slot = (f // 12) % len(idle_heads)
        local_f = f % 12
        pop = 1.0 + (0.10 * math.sin(math.pi * local_f / 4.0) if local_f < 4 else 0.0)

        head_bob_x = 9.0 * math.sin(tau * 2.0 * t)
        head_bob_y = 6.5 * math.sin(tau * 4.0 * t + 0.5)
        head_tilt = 11.0 * math.sin(tau * 2.0 * t + 0.35)
        eye_dart = (5.0 * math.sin(tau * 3.0 * t), 3.0 * math.cos(tau * 5.0 * t))

        bloke = _compose_squirming_bloke(
            assets,
            body_idx=body_idx,
            head_name=idle_heads[slot],
            t_norm=t,
            jiggle_x=8.5 * math.sin(tau * 3.0 * t),
            jiggle_y=7.5 * math.cos(tau * 4.0 * t),
            belly_squeeze=0.04 * (1.0 + math.sin(tau * 2.0 * t)),
            kick_phase=tau * 3.0 * t,
            kick_amp=1.15,
            head_bob_x=head_bob_x,
            head_bob_y=head_bob_y,
            head_tilt=head_tilt,
            head_scale=1.06 * pop,
            eye_dart=eye_dart,
            flag_phase=tau * 2.0 * t,
            flag_amp=1.15,
        )

        # Gentle breathing hoist motion for gauntlets & held bloke
        hoist_y = 6.0 * math.sin(tau * 1.0 * t)
        hoist_x = 4.5 * math.cos(tau * 1.0 * t)
        tilt = 3.8 * math.sin(tau * 1.0 * t + 0.4)

        frame = _compose_vm_frame(
            assets,
            bloke_rgba=bloke,
            bloke_cx=210.0 + hoist_x,
            bloke_cy=194.0 + hoist_y,
            bloke_scale=0.74,
            bloke_angle=tilt,
            hand_dx_in=4.0 + 3.0 * math.sin(tau * 2.0 * t),
            hand_dy=4.0 + hoist_y * 0.75,
            hand_scale=1.0,
            hand_splay=0.0,
            hand_rot=1.5 * math.sin(tau * 1.0 * t),
            fart_prog=0.0,
            fart_cx=210.0,
            fart_cy=240.0,
            fly_t=t,
            fly_centers=[(210.0 + hoist_x, 86.0 + hoist_y), (210.0 + hoist_x, 232.0 + hoist_y)],
            n_flies=13,
        )
        fname = f"vm_idle_{f:02d}.png"
        Image.fromarray(frame, "RGBA").save(os.path.join(OUT_DIR, fname), optimize=True)
        idle_files.append(fname)

    # 2. Fire / Throw / Yeet (20 frames)
    fire_files: List[str] = []
    for f in range(20):
        t = f / 19.0
        tau = 2.0 * math.pi
        body_idx = (f * 2) % n_dance

        if f <= 4:
            # Windup belly squeeze!
            p = f / 4.0
            squeeze = 0.72 * (p ** 0.8)
            bloke_scale = 0.74 + 0.04 * p
            bloke_cx = 210.0
            bloke_cy = 196.0 + 14.0 * p
            bloke_ang = -4.0 * p
            hand_dx_in = 4.0 + 18.0 * p
            hand_dy = 4.0 + 12.0 * p
            hand_scale = 1.0 + 0.04 * p
            hand_splay = 0.0
            hand_rot = -4.0 * p
            fart_prog = 0.22 * p
            head_name = "head_sky_gasp" if f < 3 else "head_turban_yell"
            head_sc = 1.10 + 0.12 * p
        elif f <= 12:
            # BIG FART blast + violent throw toward crosshair!
            p = (f - 4) / 8.0
            ease = p ** 1.30
            squeeze = -0.25 * (1.0 - p)
            bloke_scale = 0.78 * (1.0 - 0.84 * ease)
            bloke_cx = 210.0 + 12.0 * math.sin(p * math.pi)
            bloke_cy = 210.0 - 88.0 * ease
            bloke_ang = 240.0 * ease
            # Gauntlets snap outward & splay open in follow-through (never overlapping!)
            thrust = math.sin(min(1.0, p * 1.45) * math.pi * 0.5)
            hand_dx_in = 14.0 * (1.0 - min(1.0, p * 3.0)) - 44.0 * thrust
            hand_dy = 14.0 - 18.0 * thrust
            hand_scale = 1.04 + 0.10 * thrust
            hand_splay = min(1.0, p * 2.2)
            hand_rot = 14.0 * thrust
            fart_prog = min(0.98, 0.24 + 0.74 * p)
            head_name = "head_oiled_yell" if (f % 2 == 0) else "head_turban_yell"
            head_sc = 1.18
        else:
            # Disappears into crosshair, lingering fart smoke & open hands recover
            p = (f - 12) / 7.0
            bloke_scale = max(0.0, 0.12 * (1.0 - p * 1.3))
            bloke_cx = 210.0
            bloke_cy = 122.0 - 10.0 * p
            bloke_ang = 240.0 + 110.0 * p
            squeeze = 0.0
            hand_dx_in = -30.0 * (1.0 - p) + 4.0 * p
            hand_dy = -4.0 * (1.0 - p) + 22.0 * p
            hand_scale = 1.14 * (1.0 - p) + 1.0 * p
            hand_splay = 1.0 * (1.0 - p)
            hand_rot = 14.0 * (1.0 - p)
            fart_prog = min(0.99, 0.72 + 0.27 * p) if p < 0.85 else 0.0
            head_name = "head_oiled_yell"
            head_sc = 1.10

        bloke = _compose_squirming_bloke(
            assets,
            body_idx=body_idx,
            head_name=head_name,
            t_norm=t,
            jiggle_x=11.0 * math.sin(tau * 6.0 * t),
            jiggle_y=9.0 * math.cos(tau * 6.0 * t),
            belly_squeeze=squeeze,
            kick_phase=tau * 6.0 * t,
            kick_amp=1.5,
            head_bob_x=6.0 * math.sin(tau * 5.0 * t),
            head_bob_y=-8.0 * math.sin(tau * 4.0 * t),
            head_tilt=14.0 * math.sin(tau * 4.0 * t),
            head_scale=head_sc,
            eye_dart=(6.0 * math.sin(tau * 7.0 * t), -4.0),
            flag_phase=tau * 4.0 * t,
            flag_amp=1.45,
        )

        # Scatter flies outward on blast
        fly_spread = 1.0 + (1.2 * math.sin(math.pi * min(1.0, max(0.0, (f - 4) / 10.0))))
        frame = _compose_vm_frame(
            assets,
            bloke_rgba=bloke,
            bloke_cx=bloke_cx,
            bloke_cy=bloke_cy,
            bloke_scale=bloke_scale,
            bloke_angle=bloke_ang,
            hand_dx_in=hand_dx_in,
            hand_dy=hand_dy,
            hand_scale=hand_scale,
            hand_splay=hand_splay,
            hand_rot=hand_rot,
            fart_prog=fart_prog,
            fart_cx=210.0,
            fart_cy=220.0 if f <= 5 else 185.0,
            fly_t=t,
            fly_centers=[
                (210.0 - 25.0 * fly_spread, 145.0),
                (210.0 + 25.0 * fly_spread, 225.0),
            ],
            n_flies=14,
            fart_behind=(f <= 6),
        )
        fname = f"vm_fire_{f:02d}.png"
        Image.fromarray(frame, "RGBA").save(os.path.join(OUT_DIR, fname), optimize=True)
        fire_files.append(fname)

    # 3. Reload / Snatch fresh guy from below (18 frames)
    reload_files: List[str] = []
    for f in range(18):
        t = f / 17.0
        tau = 2.0 * math.pi
        body_idx = (f * 3) % n_dance

        if f < 4:
            # Hands plunge down out of frame to snatch fresh guy
            p = f / 3.0
            bloke_scale = 0.0
            bloke_cx = 210.0
            bloke_cy = 440.0
            bloke_ang = 0.0
            hand_dx_in = 4.0 - 10.0 * p
            hand_dy = 28.0 + 95.0 * p
            hand_splay = 0.5 * (1.0 - p)
            hand_rot = -6.0 * p
            jiggle_y = 0.0
            squeeze = 0.0
            head_name = "head_turban_grin"
        elif f < 12:
            # Violent upward haul with overshoot!
            p = (f - 4) / 7.0
            # Overshoots to y=170 (higher than resting 194) before settling
            haul = math.sin(p * math.pi * 0.68) / math.sin(0.68 * math.pi)
            bloke_scale = 0.74
            bloke_cx = 210.0 - 12.0 * (1.0 - p) * math.sin(p * math.pi)
            bloke_cy = 420.0 - 248.0 * haul
            bloke_ang = -10.0 * (1.0 - p) + 5.0 * math.sin(p * math.pi)
            hand_dx_in = -6.0 + 16.0 * min(1.0, p * 1.4)
            hand_dy = 120.0 - 134.0 * haul
            hand_splay = 0.0
            hand_rot = -5.0 * (1.0 - p)
            jiggle_y = -16.0 * math.sin(p * math.pi)
            squeeze = 0.18 * math.sin(p * math.pi)
            head_name = "head_turban_grin" if f < 9 else "head_cross"
        else:
            # Heavy belly-jiggle rebound settle back to idle pose
            p = (f - 12) / 5.0
            damp = math.exp(-3.2 * p) * math.cos(2.0 * math.pi * 1.5 * p)
            bloke_scale = 0.74
            bloke_cx = 210.0
            bloke_cy = 194.0 - 20.0 * damp
            bloke_ang = 4.0 * damp
            hand_dx_in = 4.0 + 6.0 * damp
            hand_dy = 4.0 - 15.0 * damp
            hand_splay = 0.0
            hand_rot = 2.0 * damp
            jiggle_y = 14.0 * damp
            squeeze = 0.08 * abs(damp)
            head_name = "head_cross"

        bloke = _compose_squirming_bloke(
            assets,
            body_idx=body_idx,
            head_name=head_name,
            t_norm=t,
            jiggle_x=10.0 * math.sin(tau * 3.0 * t),
            jiggle_y=jiggle_y,
            belly_squeeze=squeeze,
            kick_phase=tau * 4.5 * t,
            kick_amp=1.35,
            head_bob_x=8.0 * math.sin(tau * 3.0 * t),
            head_bob_y=8.0 * math.cos(tau * 4.0 * t),
            head_tilt=12.0 * math.sin(tau * 2.5 * t),
            head_scale=1.08,
            eye_dart=(4.5 * math.sin(tau * 4.0 * t), 2.5 * math.cos(tau * 5.0 * t)),
            flag_phase=tau * 3.0 * t,
            flag_amp=1.35,
        )

        frame = _compose_vm_frame(
            assets,
            bloke_rgba=bloke,
            bloke_cx=bloke_cx,
            bloke_cy=bloke_cy,
            bloke_scale=bloke_scale,
            bloke_angle=bloke_ang,
            hand_dx_in=hand_dx_in,
            hand_dy=hand_dy,
            hand_scale=1.0,
            hand_splay=hand_splay,
            hand_rot=hand_rot,
            fart_prog=0.0,
            fart_cx=210.0,
            fart_cy=240.0,
            fly_t=t,
            fly_centers=[(bloke_cx, max(60.0, bloke_cy - 105.0)), (bloke_cx, min(330.0, bloke_cy + 35.0))],
            n_flies=12,
        )
        fname = f"vm_reload_{f:02d}.png"
        Image.fromarray(frame, "RGBA").save(os.path.join(OUT_DIR, fname), optimize=True)
        reload_files.append(fname)

    return {"vm_idle": idle_files, "vm_fire": fire_files, "vm_reload": reload_files}


def generate_projectiles(assets: Dict[str, object]) -> List[List[str]]:
    """Bake 16-angle x 8-frame airborne cartwheeling/screaming thrown bloke (`220x220`)
    propelled by a brown fart/mud jet and chased by swarming flies.
    """
    turn_16: List[np.ndarray] = assets["turn_16"]  # type: ignore[assignment]
    heads: Dict[str, np.ndarray] = assets["heads"]  # type: ignore[assignment]
    mists: List[np.ndarray] = assets["mists"]  # type: ignore[assignment]
    globs: List[np.ndarray] = assets["globs"]  # type: ignore[assignment]

    files_grid: List[List[str]] = []
    for a in range(16):
        ang_files: List[str] = []
        base_turn = turn_16[a]
        # Front-ish angles get an oversized screaming head layered on top
        is_front = a in (0, 1, 2, 14, 15)
        is_side_r = a in (3, 4, 5)
        is_side_l = a in (11, 12, 13)

        for f in range(8):
            t = f / 8.0
            tau = 2.0 * math.pi
            canvas = np.zeros((PROJ_H, PROJ_W, 4), dtype=np.uint8)
            cx, cy = PROJ_W * 0.5, PROJ_H * 0.5

            # Build spinning bloke sprite (~132px tall)
            bloke_base = resize_premul(base_turn, (98, 140))

            # Overlay screaming face at front/side angles so his panic reads from afar
            if is_front or is_side_r or is_side_l:
                h_key = "head_oiled_yell" if is_front else ("head_side_yell_r" if is_side_r else "head_side_yell_l")
                h_im = resize_premul(heads[h_key], (42, 42))
                bloke_base = alpha_over(bloke_base, h_im, 28, -2)

            # Add mini fluttering flag tucked in his shorts
            fl = render_tricolor_flag(32, 20, phase=tau * t, pole_left=True, amp=1.35)
            bloke_base = alpha_over(bloke_base, fl, 60, 68)

            # Pad for clean full 360-degree cartwheel rotation without clipping
            pad = 40
            b_pad = np.zeros((bloke_base.shape[0] + pad * 2, bloke_base.shape[1] + pad * 2, 4), dtype=np.uint8)
            b_pad[pad:pad + bloke_base.shape[0], pad:pad + bloke_base.shape[1]] = bloke_base

            # Cartwheel spin direction depends on viewing yaw
            spin_dir = -1.0 if a <= 8 else 1.0
            cartwheel_deg = spin_dir * (360.0 * t)
            squash = 1.0 + 0.08 * math.sin(tau * 2.0 * t)
            b_spin = warp_rgba(
                b_pad,
                angle_deg=cartwheel_deg,
                sx=squash,
                sy=2.0 - squash,
                pivot=(b_pad.shape[1] * 0.5, b_pad.shape[0] * 0.5),
            )

            # Brown fart/mud propulsion jet trailing from shorts center along spin arc
            jet_ang = math.radians(-cartwheel_deg + 90.0)
            jet_x = cx + math.cos(jet_ang) * 28.0
            jet_y = cy + math.sin(jet_ang) * 28.0

            m1 = resize_premul(mists[(f + a) % len(mists)], (72, 72))
            m2 = resize_premul(mists[(f + a + 2) % len(mists)], (54, 54))
            canvas = alpha_over(canvas, m1, jet_x - 36.0, jet_y - 36.0, opacity=0.82)
            canvas = alpha_over(canvas, m2, cx - 27.0, cy - 27.0, opacity=0.58)

            # Mud droplets streaking off his spinning silhouette
            for d in range(3):
                da = jet_ang + (d - 1) * 0.45
                dd = 38.0 + 16.0 * ((f + d) % 3)
                g_im = resize_premul(globs[(a + f + d) % len(globs)], (22, 22))
                canvas = alpha_over(canvas, g_im, cx + math.cos(da) * dd - 11.0, cy + math.sin(da) * dd - 11.0, opacity=0.9)

            # Spinning bloke on top of fart jet
            canvas = alpha_over(canvas, b_spin, cx - b_spin.shape[1] * 0.5, cy - b_spin.shape[0] * 0.5)

            # Chasing flies orbiting the spinning guy
            canvas = render_fly_swarm(canvas, [(cx, cy), (jet_x, jet_y)], t_norm=t, n_flies=6, scale=0.72)

            fname = f"proj_a{a:02d}_f{f:02d}.png"
            Image.fromarray(canvas, "RGBA").save(os.path.join(OUT_DIR, fname), optimize=True)
            ang_files.append(fname)
        files_grid.append(ang_files)
    return files_grid


def _extract_enemy_hands(enemy_rgba: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Extract the 3rd-person enemy shooter's left & right gripping gauntlets so
    they layer naturally around the squirming guy he's holding.
    """
    h, w = enemy_rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # Left hand/forearm region: x in [66..144], y in [120..186]
    l_mask = np.clip(1.0 - np.maximum(0.0, (xx - 134.0) / 10.0), 0.0, 1.0)
    l_mask *= np.clip((yy - 118.0) / 8.0, 0.0, 1.0) * np.clip((188.0 - yy) / 8.0, 0.0, 1.0)
    l_hand = enemy_rgba.copy()
    l_hand[..., 3] = np.clip(np.round(l_hand[..., 3].astype(np.float32) * l_mask), 0, 255).astype(np.uint8)

    # Right hand/forearm region: x in [242..318], y in [126..206]
    r_mask = np.clip((xx - 244.0) / 10.0, 0.0, 1.0)
    r_mask *= np.clip((yy - 122.0) / 8.0, 0.0, 1.0) * np.clip((208.0 - yy) / 8.0, 0.0, 1.0)
    r_hand = enemy_rgba.copy()
    r_hand[..., 3] = np.clip(np.round(r_hand[..., 3].astype(np.float32) * r_mask), 0, 255).astype(np.uint8)
    return l_hand, r_hand


def generate_tp_sequences(assets: Dict[str, object]) -> Dict[str, List[str]]:
    """Bake 3rd-person enemy shooter sequences (`360x380`):
    enemy holding & chucking the full-body bloke straight at the camera!
    """
    enemy_raw = resize_premul(assets["enemy_base"], (344, 360))  # type: ignore[arg-type]
    # Pad enemy into 360x380 bottom-aligned
    enemy_base = np.zeros((TP_H, TP_W, 4), dtype=np.uint8)
    enemy_base[TP_H - 360:TP_H, (TP_W - 344) // 2:(TP_W - 344) // 2 + 344] = enemy_raw
    hand_l, hand_r = _extract_enemy_hands(enemy_base)

    mists: List[np.ndarray] = assets["mists"]  # type: ignore[assignment]
    globs: List[np.ndarray] = assets["globs"]  # type: ignore[assignment]
    n_dance = len(CLEAN_IDLE_DANCE_INDICES)

    def _compose_tp(
        enemy_dy: float,
        enemy_sc: float,
        bloke_rgba: np.ndarray | None,
        bloke_cx: float,
        bloke_cy: float,
        bloke_sc: float,
        bloke_ang: float,
        hands_over_bloke: bool,
        hand_dx: float,
        hand_dy: float,
        fart_prog: float,
        fly_t: float,
        fly_centers: Sequence[Tuple[float, float]],
    ) -> np.ndarray:
        canvas = np.zeros((TP_H, TP_W, 4), dtype=np.uint8)
        e_w = warp_rgba(
            enemy_base,
            sx=enemy_sc,
            sy=enemy_sc,
            dy=enemy_dy,
            pivot=(TP_W * 0.5, TP_H * 0.92),
        )
        canvas = alpha_over(canvas, e_w, 0, 0)

        if fart_prog > 0.0:
            canvas = _add_fart_blast(canvas, mists, globs, TP_W * 0.5, 165.0, fart_prog, strength=0.95)

        if bloke_rgba is not None and bloke_sc > 0.02:
            bw = max(8, int(round(bloke_rgba.shape[1] * bloke_sc)))
            bh = max(8, int(round(bloke_rgba.shape[0] * bloke_sc)))
            b_rs = resize_premul(bloke_rgba, (bw, bh))
            pad = 36
            b_pad = np.zeros((bh + pad * 2, bw + pad * 2, 4), dtype=np.uint8)
            b_pad[pad:pad + bh, pad:pad + bw] = b_rs
            b_rot = warp_rgba(
                b_pad,
                angle_deg=bloke_ang,
                pivot=(b_pad.shape[1] * 0.5, b_pad.shape[0] * 0.5),
            )
            canvas = alpha_over(
                canvas,
                b_rot,
                bloke_cx - b_rot.shape[1] * 0.5,
                bloke_cy - b_rot.shape[0] * 0.5,
            )

        if hands_over_bloke:
            hl = warp_rgba(hand_l, dx=-hand_dx, dy=enemy_dy + hand_dy, pivot=(TP_W * 0.5, 160.0))
            hr = warp_rgba(hand_r, dx=hand_dx, dy=enemy_dy + hand_dy, pivot=(TP_W * 0.5, 160.0))
            canvas = alpha_over(canvas, hl, 0, 0)
            canvas = alpha_over(canvas, hr, 0, 0)

        canvas = render_fly_swarm(canvas, fly_centers, t_norm=fly_t, n_flies=9, scale=0.78)
        return canvas

    # 1. TP Idle (24 frames)
    tp_idle: List[str] = []
    for f in range(24):
        t = f / 24.0
        tau = 2.0 * math.pi
        bloke = _compose_squirming_bloke(
            assets,
            body_idx=(f * 2) % n_dance,
            head_name="head_cross" if (f // 12) % 2 == 0 else "head_scream_front",
            t_norm=t,
            jiggle_x=7.0 * math.sin(tau * 2.0 * t),
            jiggle_y=6.0 * math.cos(tau * 3.0 * t),
            belly_squeeze=0.05,
            kick_phase=tau * 2.0 * t,
            kick_amp=1.1,
            head_bob_x=6.0 * math.sin(tau * 2.0 * t),
            head_bob_y=5.0 * math.cos(tau * 3.0 * t),
            head_tilt=10.0 * math.sin(tau * 2.0 * t),
            head_scale=1.12,
            eye_dart=(4.0 * math.sin(tau * 3.0 * t), 2.0 * math.cos(tau * 4.0 * t)),
            flag_phase=tau * 2.0 * t,
            flag_amp=1.2,
        )
        bob = 3.5 * math.sin(tau * t)
        frame = _compose_tp(
            enemy_dy=bob,
            enemy_sc=1.0,
            bloke_rgba=bloke,
            bloke_cx=178.0 + 3.0 * math.cos(tau * t),
            bloke_cy=162.0 + bob,
            bloke_sc=0.45,
            bloke_ang=-38.0 + 5.0 * math.sin(tau * t),
            hands_over_bloke=True,
            hand_dx=0.0,
            hand_dy=0.0,
            fart_prog=0.0,
            fly_t=t,
            fly_centers=[(162.0, 128.0 + bob), (195.0, 184.0 + bob)],
        )
        fname = f"tp_idle_{f:02d}.png"
        Image.fromarray(frame, "RGBA").save(os.path.join(OUT_DIR, fname), optimize=True)
        tp_idle.append(fname)

    # 2. TP Fire: Enemy squeezes & chucks the full-body bloke straight at the camera! (16 frames)
    tp_fire: List[str] = []
    for f in range(16):
        t = f / 15.0
        tau = 2.0 * math.pi
        if f <= 3:
            p = f / 3.0
            e_dy = 10.0 * p
            e_sc = 1.0 - 0.03 * p
            b_sc = 0.45
            b_cx, b_cy = 178.0, 164.0 + 10.0 * p
            b_ang = -38.0 - 8.0 * p
            hands_over = True
            h_dx, h_dy = 0.0, 0.0
            fart_prog = 0.22 * p
            head_name = "head_sky_gasp"
        elif f <= 11:
            p = (f - 3) / 8.0
            e_dy = 10.0 - 16.0 * math.sin(min(1.0, p * 1.4) * math.pi * 0.5)
            e_sc = 0.97 + 0.08 * math.sin(p * math.pi)
            # Guy hurtles STRAIGHT AT THE CAMERA getting huge!
            b_sc = 0.45 + 0.79 * (p ** 1.15)
            b_cx = 178.0 + 10.0 * math.sin(p * math.pi)
            b_cy = 174.0 + 24.0 * p
            b_ang = -46.0 + 250.0 * p
            hands_over = False
            h_dx, h_dy = 0.0, 0.0
            fart_prog = min(0.98, 0.25 + 0.73 * p)
            head_name = "head_oiled_yell" if (f % 2 == 0) else "head_turban_yell"
        else:
            p = (f - 11) / 4.0
            e_dy = -6.0 * (1.0 - p)
            e_sc = 1.0
            b_sc = 0.0
            b_cx, b_cy = 180.0, 200.0
            b_ang = 0.0
            hands_over = False
            h_dx, h_dy = 18.0 * (1.0 - p), 0.0
            fart_prog = 0.98 * (1.0 - p) if p < 0.75 else 0.0
            head_name = "head_oiled_yell"

        bloke = _compose_squirming_bloke(
            assets,
            body_idx=(f * 3) % n_dance,
            head_name=head_name,
            t_norm=t,
            jiggle_x=9.0 * math.sin(tau * 5.0 * t),
            jiggle_y=8.0 * math.cos(tau * 5.0 * t),
            belly_squeeze=0.45 if f <= 3 else -0.1,
            kick_phase=tau * 5.0 * t,
            kick_amp=1.4,
            head_bob_x=6.0 * math.sin(tau * 4.0 * t),
            head_bob_y=6.0 * math.cos(tau * 4.0 * t),
            head_tilt=12.0 * math.sin(tau * 3.0 * t),
            head_scale=1.18,
            eye_dart=(5.0, -3.0),
            flag_phase=tau * 4.0 * t,
            flag_amp=1.45,
        )
        frame = _compose_tp(
            enemy_dy=e_dy,
            enemy_sc=e_sc,
            bloke_rgba=bloke if b_sc > 0.02 else None,
            bloke_cx=b_cx,
            bloke_cy=b_cy,
            bloke_sc=b_sc,
            bloke_ang=b_ang,
            hands_over_bloke=hands_over,
            hand_dx=h_dx,
            hand_dy=h_dy,
            fart_prog=fart_prog,
            fly_t=t,
            fly_centers=[(b_cx, b_cy - 30.0), (180.0, 170.0)],
        )
        fname = f"tp_fire_{f:02d}.png"
        Image.fromarray(frame, "RGBA").save(os.path.join(OUT_DIR, fname), optimize=True)
        tp_fire.append(fname)

    # 3. TP Reload: Enemy snatches a fresh squirming guy up into cradle (12 frames)
    tp_reload: List[str] = []
    for f in range(12):
        t = f / 11.0
        tau = 2.0 * math.pi
        p = f / 11.0
        haul = math.sin(min(1.0, p * 1.15) * math.pi * 0.5)
        e_dy = 16.0 * (1.0 - haul)
        b_cy = 290.0 - 124.0 * haul
        bloke = _compose_squirming_bloke(
            assets,
            body_idx=(f * 2) % n_dance,
            head_name="head_turban_grin" if f < 7 else "head_cross",
            t_norm=t,
            jiggle_x=7.0 * math.sin(tau * 3.0 * t),
            jiggle_y=-10.0 * math.sin(p * math.pi),
            belly_squeeze=0.12 * math.sin(p * math.pi),
            kick_phase=tau * 3.0 * t,
            kick_amp=1.25,
            head_bob_x=5.0 * math.sin(tau * 2.0 * t),
            head_bob_y=5.0 * math.cos(tau * 3.0 * t),
            head_tilt=8.0 * math.sin(tau * 2.0 * t),
            head_scale=1.14,
            eye_dart=(3.0 * math.sin(tau * 3.0 * t), 2.0),
            flag_phase=tau * 2.5 * t,
            flag_amp=1.25,
        )
        frame = _compose_tp(
            enemy_dy=e_dy,
            enemy_sc=1.0,
            bloke_rgba=bloke if f >= 2 else None,
            bloke_cx=178.0,
            bloke_cy=b_cy,
            bloke_sc=0.45,
            bloke_ang=-38.0 + 20.0 * (1.0 - haul),
            hands_over_bloke=(f >= 4),
            hand_dx=0.0,
            hand_dy=0.0,
            fart_prog=0.0,
            fly_t=t,
            fly_centers=[(168.0, min(280.0, b_cy - 20.0)), (192.0, min(300.0, b_cy + 16.0))],
        )
        fname = f"tp_reload_{f:02d}.png"
        Image.fromarray(frame, "RGBA").save(os.path.join(OUT_DIR, fname), optimize=True)
        tp_reload.append(fname)

    return {"tp_idle": tp_idle, "tp_fire": tp_fire, "tp_reload": tp_reload}


def _build_contact_sheet() -> str:
    """Create a visual verification contact sheet across vm_idle, vm_fire, vm_reload,
    proj (angles & spin), tp_idle, and tp_fire on a dark slate checker backdrop.
    """
    picks = [
        ("vm_idle_00", "vm_idle_00.png"),
        ("vm_idle_18", "vm_idle_18.png"),
        ("vm_idle_36", "vm_idle_36.png"),
        ("vm_idle_50", "vm_idle_50.png"),
        ("vm_fire_03 (squeeze)", "vm_fire_03.png"),
        ("vm_fire_06 (FART!)", "vm_fire_06.png"),
        ("vm_fire_09 (yeet)", "vm_fire_09.png"),
        ("vm_fire_13 (follow)", "vm_fire_13.png"),
        ("vm_reload_05 (snatch)", "vm_reload_05.png"),
        ("vm_reload_10 (bounce)", "vm_reload_10.png"),
        ("proj_a00_f01", "proj_a00_f01.png"),
        ("proj_a04_f03", "proj_a04_f03.png"),
        ("proj_a08_f05", "proj_a08_f05.png"),
        ("proj_a12_f06", "proj_a12_f06.png"),
        ("tp_idle_00", "tp_idle_00.png"),
        ("tp_fire_02 (squeeze)", "tp_fire_02.png"),
        ("tp_fire_06 (chuck!)", "tp_fire_06.png"),
        ("tp_fire_09 (at cam)", "tp_fire_09.png"),
        ("tp_reload_06", "tp_reload_06.png"),
        ("tp_idle_12", "tp_idle_12.png"),
    ]
    cols, rows = 5, 4
    cw, ch = 220, 200
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (34, 38, 46, 255))
    draw = ImageDraw.Draw(sheet)

    for idx, (label, fname) in enumerate(picks):
        r, c = divmod(idx, cols)
        x0, y0 = c * cw, r * ch
        im = Image.open(os.path.join(OUT_DIR, fname)).convert("RGBA")
        sc = min((cw - 12) / im.width, (ch - 26) / im.height)
        nw, nh = max(4, int(round(im.width * sc))), max(4, int(round(im.height * sc)))
        rs = im.resize((nw, nh), Image.Resampling.LANCZOS)
        sheet.alpha_composite(rs, (x0 + (cw - nw) // 2, y0 + (ch - 20 - nh) // 2))
        draw.text((x0 + 6, y0 + ch - 18), label, fill=(255, 220, 90, 255))

    out_path = os.path.join(OUT_DIR, "contact_sheet_c2.png")
    sheet.save(out_path, optimize=True)
    return out_path


def load_assets() -> Dict[str, object]:
    """Load and prepare all keyed sprites, heads, gauntlets, enemy base, and FX."""
    dance_paths = sorted(glob.glob(os.path.join(WORK_DIR, "dance_48", "dance_*.png")))
    dance_raw = [
        _clean_trapped_white_arms(_load_rgba(dance_paths[i]), 96, 244, 280)
        for i in CLEAN_IDLE_DANCE_INDICES
    ]
    dance_headless = [_erase_original_head(d) for d in dance_raw]

    turn_paths = sorted(glob.glob(os.path.join(WORK_DIR, "turn_16", "turn_*.png")))
    turn_16 = [
        _clean_trapped_white_arms(_load_rgba(p), 102, 218, 265)
        for p in turn_paths
    ]

    heads: Dict[str, np.ndarray] = {}
    for p in sorted(glob.glob(os.path.join(WORK_DIR, "heads", "*.png"))):
        name = os.path.splitext(os.path.basename(p))[0]
        heads[name] = _clean_head_edge(_load_rgba(p), name)

    mists = [_load_rgba(p) for p in sorted(glob.glob(os.path.join(WORK_DIR, "fx", "mist_*.png")))]
    globs = [_load_rgba(p) for p in sorted(glob.glob(os.path.join(WORK_DIR, "fx", "mud_glob_*.png")))]

    gauntlet_l, gauntlet_r = _extract_gauntlets(GAUNTLET_PLATE)
    enemy_base = _load_rgba(ENEMY_BASE_PNG)

    return {
        "dance_headless": dance_headless,
        "turn_16": turn_16,
        "heads": heads,
        "mists": mists,
        "globs": globs,
        "gauntlet_l": gauntlet_l,
        "gauntlet_r": gauntlet_r,
        "enemy_base": enemy_base,
    }


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("[concept2_throwguy] Loading assets...")
    assets = load_assets()

    print("[concept2_throwguy] Baking viewmodel (60 idle, 20 fire, 18 reload)...")
    vm_meta = generate_vm_sequences(assets)

    print("[concept2_throwguy] Baking 16x8 cartwheeling projectile sprites...")
    proj_grid = generate_projectiles(assets)

    print("[concept2_throwguy] Baking 3rd-person shooter sprites (24 idle, 16 fire, 12 reload)...")
    tp_meta = generate_tp_sequences(assets)

    manifest = {
        "id": "c2_throwguy",
        "title": "HUMAN BELLY-SLING",
        "tagline": "Hoist an entire squirming bloke, squeeze his belly for a fart boost, and YEET him!",
        "fps": 60,
        "muzzle_norm": [0.5, 0.36],
        "vm_size": [VM_W, VM_H],
        "vm_idle": vm_meta["vm_idle"],
        "vm_fire": vm_meta["vm_fire"],
        "vm_reload": vm_meta["vm_reload"],
        "proj": {
            "angles": 16,
            "frames_per_angle": 8,
            "size": [PROJ_W, PROJ_H],
            "files": proj_grid,
        },
        "tp_size": [TP_W, TP_H],
        "tp_idle": tp_meta["tp_idle"],
        "tp_fire": tp_meta["tp_fire"],
        "tp_reload": tp_meta["tp_reload"],
    }
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    sheet_path = _build_contact_sheet()
    total_png = (
        len(vm_meta["vm_idle"])
        + len(vm_meta["vm_fire"])
        + len(vm_meta["vm_reload"])
        + 16 * 8
        + len(tp_meta["tp_idle"])
        + len(tp_meta["tp_fire"])
        + len(tp_meta["tp_reload"])
    )
    print(f"[concept2_throwguy] Done! {total_png} sprites + manifest -> {OUT_DIR}")
    print(f"[concept2_throwguy] Contact sheet -> {sheet_path}")


if __name__ == "__main__":
    main()
