r"""Builds the 'JESS-KART 3000' Funny 360° Sprite Pack + Quake SPR32 & MD3 Assets
from the 145-frame turntable clip (source/mm_tools/ref/jesskartpink.mp4).

Outputs (without modifying progs.dat or any active QuakeC files):
  1. Standalone 360° Funny Sprite Pack & Interactive Playground (jesskart_sprite/):
       - clean/jesskart_clean_00..23.png   24 calibrated 360° studio cutouts (0° = dead front, 15° steps)
       - jesskart_00..23.png               24-angle key turbo-kart funny sprites
       - anim/turbo_AA_fK.png              24 angles x 6 frames (144 frames) of Nitro Burnout + Spinning Tires + Bounce
       - anim/wheelie_AA_fK.png            24 angles x 6 frames (144 frames) of Chrome Torpedo Wheelie + Sparks
       - jesskart_sheet_6x4.png            6x4 360° turnaround sprite sheet
       - jesskart_arcade_sheet.png         8-direction x 4-state Arcade Kart Showcase Sheet
       - jesskart_turbo_360.gif            Animated 360° spinning & revving showcase GIF
       - jesskart_wheelie_loop.gif         Animated goofy wheelie + nitro bounce GIF
       - index.html                        Interactive 360° viewer + WASD playable Arena Drive mode + WebAudio horn/engine!

  2. Quake / DarkPlaces Sprite Assets:
       - progs/jesskart.spr32              56-frame DarkPlaces RGBA sprite (0..7 8-dir rev idle, 8..55 8-dir x 6-frame turbo drive)
       - progs/jesskart.md3                16-angle DarkPlaces billboard card model + progs/jesskart.md3_0..15.skin
       - progs/jesskart_00..15.png         16 directional views + progs/jesskart_f00..05.png & jesskart_r00..05.png animated frames
       - scripts/jesskart.shader           Two-sided alpha-tested DarkPlaces shaders with animated front & rear views

Usage:
    python3.13 source/mm_tools/build_jesskart_sprite.py [video_path] [mod_dir]
"""
import glob
import math
import os
import struct
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_VID = os.path.join(HERE, "ref", "jesskartpink.mp4")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import md3lib


# ---------------------------------------------------------------------------
# 1. Calibrated 360-degree Frame Selection (0 deg = dead front f=27)
# ---------------------------------------------------------------------------

def load_video_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    frames = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()
    if len(frames) < 120:
        raise RuntimeError(f"Expected ~145 turntable frames, got {len(frames)}")
    return frames


def build_calibrated_angle_map(frames):
    """Maps true turntable angle [0, 360) -> frame index.
    Verified cardinal landmarks:
      f=27  ->   0.0 deg (dead front, chrome torpedo pointing straight at viewer)
      f=60  ->  90.0 deg (dead left profile, facing screen-left)
      f=87  -> 180.0 deg (dead rear)
      f=116 -> 270.0 deg (dead right profile, facing screen-right)
      f=144 matches f=2 in lower-kart pose, wrapping seamlessly back to f=27.
    """
    def diff_roi(i, j, y0=200):
        g0 = cv2.cvtColor(frames[i][y0:1520, 100:1132], cv2.COLOR_RGB2GRAY).astype(np.float32)
        g1 = cv2.cvtColor(frames[j][y0:1520, 100:1132], cv2.COLOR_RGB2GRAY).astype(np.float32)
        return float(np.mean(np.abs(g1 - g0)))

    quads = [
        (0.0, 90.0, list(range(27, 61))),
        (90.0, 180.0, list(range(60, 88))),
        (180.0, 270.0, list(range(87, 117))),
        (270.0, 360.0, list(range(116, 145)) + list(range(3, 28))),
    ]
    angle_map = []
    for a0, a1, seq in quads:
        ds = [0.0]
        for fa, fb in zip(seq[:-1], seq[1:]):
            y_top = 760 if (fa == 144 and fb == 3) else 200
            ds.append(ds[-1] + diff_roi(fa, fb, y0=y_top))
        tot = max(ds[-1], 1e-6)
        for idx_q, f_idx in enumerate(seq[:-1]):
            ang = a0 + (a1 - a0) * (ds[idx_q] / tot)
            angle_map.append((ang, f_idx))
    return angle_map


def pick_frame(angle_map, target_deg):
    target_deg = target_deg % 360.0
    best_f = angle_map[0][1]
    best_err = 999.0
    for ang, f_idx in angle_map:
        err = min(abs(ang - target_deg), abs(ang + 360.0 - target_deg), abs(ang - 360.0 - target_deg))
        if err < best_err:
            best_err = err
            best_f = f_idx
    return best_f


# ---------------------------------------------------------------------------
# 2. Studio-Grade Foreground Matting + Wheel Hub Ellipse Extraction
# ---------------------------------------------------------------------------

def segment_kart_frame(rgb):
    """Returns (rgba_clean, fg_mask, wheel_ellipses) with:
      - 100% solid white wheel dish hubs (isolated strictly inside neutral-black rubber tires)
      - 100% open air-gaps between thighs, chrome axle, and chrome torpedo shaft
      - 100% intact platinum-blonde hair, white sneakers, chrome axle & chrome shaft
      - Zero floor shadows, zero watermark, subpixel anti-aliased & despilled edges
    """
    H, W = rgb.shape[:2]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)

    both = np.concatenate([lab[:, :24, :], lab[:, -24:, :]], axis=1)
    bg_L_edge = ndimage.gaussian_filter1d(np.percentile(both[..., 0], 85, axis=1), sigma=25.0)
    top_row_L = ndimage.gaussian_filter1d(lab[12, :, 0], sigma=40.0)
    vignette_x = top_row_L[None, :] - float(np.percentile(np.concatenate([top_row_L[:24], top_row_L[-24:]]), 85))
    bg_L = bg_L_edge[:, None] + vignette_x
    bg_a = ndimage.gaussian_filter1d(np.median(both[..., 1], axis=1), sigma=25.0)[:, None]
    bg_b = ndimage.gaussian_filter1d(np.median(both[..., 2], axis=1), sigma=25.0)[:, None]

    dl = lab[..., 0] - bg_L
    dab = np.hypot(lab[..., 1] - bg_a, lab[..., 2] - bg_b)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.hypot(gx, gy) / 4.0

    rows = np.arange(H)[:, None]
    cols = np.arange(W)[None, :]
    valid_zone = (rows < H - 35) & ~((rows > H - 140) & (cols > W - 140))

    # 1. Pure neutral-black tire rubber rings (excludes blue jeans where dab >= 10, so thigh-axle gaps are NEVER enclosed!)
    tire_rubber = (lab[..., 0] < 90.0) & (dab < 9.2) & (rows > 760) & valid_zone
    tire_rubber = ndimage.binary_closing(
        tire_rubber, structure=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)).astype(bool)
    )

    # Identify elliptical white wheel dish hubs strictly enclosed inside black tire rubber
    inv_tire = ~tire_rubber
    tlbl, tnum = ndimage.label(inv_tire)
    wheel_hubs = np.zeros((H, W), dtype=bool)
    wheel_ellipses = []  # list of (cx, cy, ra, rb, phi_rad)
    if tnum > 0:
        tsizes = ndimage.sum(inv_tire, tlbl, range(1, tnum + 1))
        t_bg = {tlbl[0, 0], tlbl[0, W - 1], tlbl[H - 1, 0]}
        for k_id, sz in enumerate(tsizes, start=1):
            if k_id in t_bg or sz < 500 or sz > 185000:
                continue
            hm = (tlbl == k_id)
            ys, xs = np.nonzero(hm)
            # Check convex hull solidity: white wheel rims are smooth ellipses (solidity > 0.80)
            pts = np.column_stack([xs, ys]).astype(np.int32)
            hull_area = max(cv2.contourArea(cv2.convexHull(pts)), 1.0)
            solidity = float(sz) / hull_area
            if solidity > 0.74 and float(np.mean(ys)) > 820:
                wheel_hubs |= hm
                if sz > 1100:
                    cx_w = float(np.mean(xs))
                    cy_w = float(np.mean(ys))
                    dx = xs - cx_w
                    dy = ys - cy_w
                    cov = np.array([[np.mean(dx * dx), np.mean(dx * dy)], [np.mean(dx * dy), np.mean(dy * dy)]])
                    vals, vecs = np.linalg.eigh(cov)
                    order = np.argsort(vals)[::-1]
                    vals = np.maximum(vals[order], 4.0)
                    vecs = vecs[:, order]
                    ra = 2.0 * math.sqrt(float(vals[0]))
                    rb = 2.0 * math.sqrt(float(vals[1]))
                    phi = math.atan2(float(vecs[1, 0]), float(vecs[0, 0]))
                    wheel_ellipses.append((cx_w, cy_w, ra, rb, phi))

    tires_solid = tire_rubber | wheel_hubs

    # 2. Rider + denim + pink top + blonde hair + dark metal/rubber
    body_and_dark = (
        (dab > 6.0)
        | ((dl < -55.0) & (rows < 1080))
        | ((dl < -102.0) & (rows >= 1080))
    ) & valid_zone

    # 3. Crisp Canny edges on lower rig (chrome axle, chrome torpedo shaft, white sneakers)
    edges = (cv2.Canny(rgb, 24, 64) > 0) & valid_zone & (rows > 860)

    rig_seed = body_and_dark | tires_solid | edges
    rig_closed = ndimage.binary_closing(
        rig_seed, structure=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)).astype(bool)
    )

    # Fill small interior patches inside white sneakers & chrome specular strips, NEVER filling neutral wall air-gaps
    inv = ~rig_closed
    ilbl, inum = ndimage.label(inv)
    filled_small = rig_closed.copy()
    if inum > 0:
        isizes = ndimage.sum(inv, ilbl, range(1, inum + 1))
        bg_lbls = {ilbl[0, 0], ilbl[0, W - 1], ilbl[H - 1, 0]}
        for k_id, sz in enumerate(isizes, start=1):
            if k_id in bg_lbls or sz >= 2800:
                continue
            hm = (ilbl == k_id)
            min_r = int(np.min(np.nonzero(hm)[0]))
            if min_r < 1030:
                if sz < 240:
                    filled_small[hm] = True
            else:
                # Below row 1030: white sneaker leather or chrome shaft specular strip!
                # Reject only if pure zero-chroma flat studio wall (dab < 1.8 and |dl| < 8 and grad_p90 < 4.5 and sz > 380)
                med_dab = float(np.median(dab[hm]))
                med_dl = float(np.median(dl[hm]))
                p90_g = float(np.percentile(grad[hm], 90))
                if not (med_dab < 1.8 and abs(med_dl) < 8.5 and p90_g < 4.5 and sz > 380):
                    filled_small[hm] = True

    mask = filled_small | tires_solid

    # 4. Peel outer morphological closing halo & soft floor shadows back to the crisp edge
    for _ in range(10):
        er = ndimage.binary_erosion(mask)
        rim = mask & ~er
        bad_rim = rim & ~tires_solid & (dab < 4.8) & (dl > -22.0) & (dl < 7.0) & (grad < 13.0)
        shadow_rim = rim & (rows > 1060) & (dab < 4.2) & (grad < 12.0) & (dl > -102.0)
        drop = bad_rim | shadow_rim
        if not np.any(drop):
            break
        mask[drop] = False

    lbl, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, lbl, range(1, n + 1))
        mask = (lbl == (1 + int(np.argmax(sizes))))

    # 5. Subpixel anti-aliased alpha + 2D studio background edge color decontamination
    dist_in = ndimage.distance_transform_edt(mask)
    dist_out = ndimage.distance_transform_edt(~mask)
    sdf = dist_in - dist_out
    alpha = np.clip((sdf - 0.55) / 1.35, 0.0, 1.0)

    top_rgb = cv2.GaussianBlur(rgb[:20, :, :].astype(np.float32), (0, 0), 35.0).mean(axis=0)[None, :, :]
    side_rgb = np.median(np.concatenate([rgb[:, :24, :], rgb[:, -24:, :]], axis=1), axis=1).astype(np.float32)[:, None, :]
    bg_rgb = np.clip(side_rgb + (top_rgb - np.median(top_rgb, axis=1, keepdims=True)), 0, 255)
    rgb_f = rgb.astype(np.float32)
    edge_band = (alpha > 0.02) & (alpha < 0.99)
    a_safe = np.maximum(alpha[..., None], 0.22)
    decontam = np.clip((rgb_f - (1.0 - alpha[..., None]) * bg_rgb) / a_safe, 0.0, 255.0)
    rgb_clean = np.where(edge_band[..., None], decontam, rgb_f).astype(np.uint8)

    rgba = np.dstack([rgb_clean, (alpha * 255.0).astype(np.uint8)])
    return rgba, mask, wheel_ellipses


# ---------------------------------------------------------------------------
# 3. Perspective Photo Wheel Spinning + Goofy Kart Squash/Bounce/Wheelie
# ---------------------------------------------------------------------------

def premul_remap(rgba, map_x, map_y):
    """Remaps an RGBA uint8 image in premultiplied-alpha space so borders never halo."""
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, a * 255.0], axis=-1)
    warped = cv2.remap(pm, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    wa = warped[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, warped[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), np.clip(warped[..., 3], 0, 255).astype(np.uint8)])


def spin_wheels_in_canvas(rgba, ellipses, spin_phase_rad, speed_streaks=True):
    """Rotates each detected white wheel dish + inner tire ring in foreshortened 3D perspective!"""
    if not ellipses:
        return rgba
    H, W = rgba.shape[:2]
    out = rgba.copy()
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    for (cx, cy, ra, rb, phi) in ellipses:
        if rb < 5.0 or ra < 8.0:
            continue
        ra_e = ra * 1.24
        rb_e = rb * 1.24
        rmax = max(ra_e, rb_e) + 4.0
        x0 = max(0, int(cx - rmax))
        x1 = min(W, int(cx + rmax + 1))
        y0 = max(0, int(cy - rmax))
        y1 = min(H, int(cy + rmax + 1))
        if x1 <= x0 or y1 <= y0:
            continue

        cp, sp = math.cos(phi), math.sin(phi)
        lxg = xg[y0:y1, x0:x1]
        lyg = yg[y0:y1, x0:x1]
        dx = lxg - cx
        dy = lyg - cy
        u = (dx * cp + dy * sp) / ra_e
        v = (-dx * sp + dy * cp) / rb_e
        r2 = u * u + v * v
        inside = r2 < 1.0
        if not np.any(inside):
            continue

        blend = np.clip((1.0 - np.sqrt(np.minimum(r2, 1.0))) / 0.14, 0.0, 1.0)
        patch = out[y0:y1, x0:x1, :3].astype(np.float32)
        acc_rgb = np.zeros_like(patch)
        sub_angles = (-0.14, 0.0, 0.14) if speed_streaks else (0.0,)
        for da in sub_angles:
            th = spin_phase_rad + da
            ct, st = math.cos(th), math.sin(th)
            ur = u * ct - v * st
            vr = u * st + v * ct
            mx = np.where(inside, (cx - x0) + (ur * ra_e) * cp - (vr * rb_e) * sp, lxg - x0).astype(np.float32)
            my = np.where(inside, (cy - y0) + (ur * ra_e) * sp + (vr * rb_e) * cp, lyg - y0).astype(np.float32)
            samp = cv2.remap(patch, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            acc_rgb += samp / float(len(sub_angles))

        if speed_streaks:
            ang_uv = np.arctan2(v, u)
            r_uv = np.sqrt(np.minimum(r2, 1.0))
            arc1 = np.sin(3.0 * (ang_uv - spin_phase_rad * 1.3))
            ring_rim = np.exp(-((r_uv - 0.62) / 0.14) ** 2) * (arc1 > 0.72)
            ring_tire = np.exp(-((r_uv - 0.92) / 0.07) ** 2) * (np.sin(4.0 * (ang_uv - spin_phase_rad)) > 0.68)
            acc_rgb = np.clip(acc_rgb + ring_rim[..., None] * 26.0 + ring_tire[..., None] * 38.0, 0.0, 255.0)

        w = (blend * (out[y0:y1, x0:x1, 3] > 30))[..., None]
        out[y0:y1, x0:x1, :3] = np.clip(out[y0:y1, x0:x1, :3] * (1.0 - w) + acc_rgb * w, 0, 255).astype(np.uint8)
    return out


def deform_kart_physics(rgba, cx, y_ground, y_saddle, angle_deg, phase_01, mode="turbo"):
    """Applies goofy 2-stroke kart physics in premultiplied RGBA space:
      - Separate tire/axle squash-and-stretch vs lagged upper-body rider bounce
      - High-frequency 2-stroke engine buzz
      - In 'wheelie' mode: dramatic nose-up chrome-torpedo wheelie tilt + hop!
    """
    H, W = rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    t = 2.0 * math.pi * phase_01
    rad_ang = math.radians(angle_deg)

    if mode == "turbo":
        # Snappy 2-cycle per loop kart bounce + lagged rider follow-through
        chassis_hop = 7.5 * max(0.0, math.sin(t)) - 3.5 * max(0.0, -math.sin(t))
        squash = -0.048 * math.sin(t)  # positive when slamming down -> wider & shorter!
        rider_lag = 9.5 * math.sin(t - 1.15)  # 66-deg secondary bounce lag!
        buzz_x = 1.8 * math.sin(3.0 * t)
        tilt_deg = 2.4 * math.sin(t) * math.cos(rad_ang)  # playful chariot rock on front/back views
        wheelie_lift = 0.0
    elif mode == "wheelie":
        # Huge dramatic wheelie! Side views pitch nose skyward; front/back views lift shaft & rock!
        pulse = 0.82 + 0.18 * math.sin(t)
        side_factor = math.sin(rad_ang)  # +1 at 90 deg (facing left -> pitch CW +deg), -1 at 270 deg (facing right -> pitch CCW -deg)
        front_factor = math.cos(rad_ang)  # +1 at 0 deg (facing viewer), -1 at 180 deg
        tilt_deg = (25.5 * pulse) * side_factor + 5.0 * math.sin(t) * front_factor
        chassis_hop = 16.0 * (0.55 + 0.45 * math.sin(t))
        squash = -0.062 * math.cos(t)
        rider_lag = 12.5 * math.sin(t - 0.9)
        buzz_x = 2.0 * math.cos(2.0 * t)
        wheelie_lift = 22.0 * pulse * max(0.0, front_factor)
    elif mode == "idle":
        # Putt-putt 2-stroke lawnmower idle vibration
        chassis_hop = 2.0 * math.sin(t)
        squash = -0.022 * math.sin(t)
        rider_lag = 4.0 * math.sin(t - 1.0)
        buzz_x = 2.2 * math.sin(2.0 * t)
        tilt_deg = 1.2 * math.sin(t)
        wheelie_lift = 0.0
    else:
        return rgba

    # Inverse mapping: for each destination pixel (xg, yg), find source pixel (sx, sy)
    # 1. Undo rotation around ground-axle pivot (cx, y_ground - 36)
    piv_x = cx - 22.0 * math.sin(rad_ang) * (1.0 if mode == "wheelie" else 0.0)
    piv_y = y_ground - 36.0
    tr = math.radians(-tilt_deg)
    ct, st = math.cos(tr), math.sin(tr)
    dx = xg - piv_x - buzz_x
    dy = yg - piv_y + chassis_hop
    rx = piv_x + dx * ct - dy * st
    ry = piv_y + dx * st + dy * ct

    # 2. Undo ground-anchored squash & stretch + lagged upper-body rider bounce
    upper_w = np.clip((y_saddle - ry) / 140.0, 0.0, 1.0)
    # On front-view wheelie, lift central chrome torpedo column upward too!
    center_col_w = np.exp(-((rx - cx) / 52.0) ** 2) * np.clip((ry - (y_saddle - 20.0)) / 90.0, 0.0, 1.0)

    sx = cx + (rx - cx) / (1.0 + squash * (1.0 - 0.45 * upper_w))
    sy_from_ground = (y_ground - ry) / (1.0 - squash * 0.85)
    sy = y_ground - sy_from_ground + rider_lag * upper_w + wheelie_lift * center_col_w

    return premul_remap(rgba, sx.astype(np.float32), sy.astype(np.float32))


# ---------------------------------------------------------------------------
# 4. 3D-Angle-Sorted Arcade Exhaust Flames, Burnout Smoke, Sparks & Star-Glint
# ---------------------------------------------------------------------------

def composite_over(dst_rgba_f, layer_rgb_f, layer_a_f):
    """Alpha-composites (layer_rgb_f [0..255], layer_a_f [0..1]) over dst_rgba_f (H,W,4 float [0..255 / 0..1])."""
    la = np.clip(layer_a_f, 0.0, 1.0)[..., None]
    da = dst_rgba_f[..., 3:4]
    out_a = la + da * (1.0 - la)
    out_rgb = np.where(out_a > 1e-5, (layer_rgb_f * la + dst_rgba_f[..., :3] * da * (1.0 - la)) / np.maximum(out_a, 1e-5), 0.0)
    return np.concatenate([out_rgb, out_a], axis=-1)


def add_arcade_kart_fx(rgba, cx, y_ground, y_saddle, angle_deg, phase_01, mode="turbo"):
    """Draws 3D-angle-projected twin nitro flames, billowing burnout tire smoke, pavement sparks,
    and a signature anime specular 'TING!' glint on the giant chrome torpedo tip!"""
    if mode == "clean":
        return rgba

    H, W = rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = math.radians(angle_deg)
    # Kart 3D heading at angle_deg:
    #   angle=0   -> facing +Z (toward camera): fwd_2d = (0, +1 down), exhaust_2d = (0, -1 up/behind)
    #   angle=90  -> facing -X (screen left):   fwd_2d = (-1, 0),      exhaust_2d = (+1 right, 0)
    #   angle=180 -> facing -Z (away):          fwd_2d = (0, -1),      exhaust_2d = (0, +1 toward camera)
    #   angle=270 -> facing +X (screen right):  fwd_2d = (+1, 0),      exhaust_2d = (-1 left, 0)
    fwd_x = -math.sin(rad)
    fwd_z = math.cos(rad)   # +1 = toward viewer, -1 = away from viewer
    ex_x = -fwd_x           # exhaust shoots opposite forward direction!
    ex_y = -0.18 * fwd_z - (0.22 if mode == "wheelie" else 0.04)  # slight upward kick

    # Axle half-span in canvas pixels (~195 px at 0/180 deg)
    axle_half = 192.0
    lx_tire = cx - axle_half * math.cos(rad)
    rx_tire = cx + axle_half * math.cos(rad)
    tire_y = y_ground - 12.0

    # Prepare back (behind kart) and front (in front of kart) FX accumulators
    back_layer = np.zeros((H, W, 4), dtype=np.float32)
    front_layer = np.zeros((H, W, 4), dtype=np.float32)

    rng = np.random.default_rng(int(round(angle_deg * 10)) * 31 + int(round(phase_01 * 24)) + (700 if mode == "wheelie" else 100))
    t = 2.0 * math.pi * phase_01

    # --- A. Central Chrome Rocket-Pipe Afterburner (blasting out the rear end of the central chrome tube!) ---
    y_axle = y_ground - 96.0 - (14.0 if mode == "wheelie" else 4.0)
    if mode in ("turbo", "wheelie"):
        boost_scale = 1.32 if mode == "wheelie" else 1.0
        px0 = cx + ex_x * (54.0 if mode == "wheelie" else 42.0)
        py0 = y_axle + (16.0 * abs(ex_x) if mode == "wheelie" else 0.0)

        target = front_layer if fwd_z < -0.12 else back_layer

        # 1) Side / 3-4 / oblique jet plume shooting along (ex_x, slight down-pitch on wheelie!)
        jet_ux = ex_x
        jet_uy = (0.34 if mode == "wheelie" else 0.08) * abs(ex_x) + 0.28 * max(0.0, -fwd_z)
        jnorm = math.hypot(jet_ux, jet_uy)
        if jnorm > 0.14:
            ux, uy = jet_ux / jnorm, jet_uy / jnorm
            vx, vy = -uy, ux
            plen = (138.0 + 28.0 * math.sin(t * 2.0)) * boost_scale * min(1.15, jnorm * 1.15)
            pwid = (30.0 + 6.0 * math.cos(t * 2.0)) * boost_scale

            dx = xg - px0
            dy = yg - py0
            along = dx * ux + dy * uy
            perp = dx * vx + dy * vy
            wiggle = 6.0 * np.sin(along * 0.085 - t * 3.0) * np.clip(along / max(plen, 1.0), 0.0, 1.0)
            perp_w = perp + wiggle

            u01 = along / max(plen, 1.0)
            sin_env = np.maximum(0.0, np.sin(np.clip(u01, 0.0, 1.0) * math.pi))
            envelope = pwid * (sin_env ** 0.58) * (1.20 - 0.45 * np.clip(u01, 0.0, 1.0))
            in_band = (u01 > -0.04) & (u01 < 1.0)

            outer = np.clip(1.0 - np.abs(perp_w) / np.maximum(envelope, 1.0), 0.0, 1.0) * in_band
            mid = np.clip(1.0 - np.abs(perp_w) / np.maximum(envelope * 0.64, 1.0), 0.0, 1.0) * in_band * (u01 < 0.84)
            core = np.clip(1.0 - np.abs(perp_w) / np.maximum(envelope * 0.34, 1.0), 0.0, 1.0) * in_band * (u01 < 0.58)
            # Mach shock-diamonds inside the rocket plume!
            diamonds = (np.maximum(0.0, np.cos(u01 * 5.0 * math.pi - t * 2.0)) ** 3.0) * (np.abs(perp_w) < envelope * 0.42) * in_band * (u01 < 0.78)

            col_outer = np.broadcast_to(np.array([255.0, 24.0, 165.0], np.float32), (H, W, 3))
            col_mid = np.broadcast_to(np.array([255.0, 145.0, 15.0], np.float32), (H, W, 3))
            col_core = np.broadcast_to(np.array([255.0, 252.0, 205.0], np.float32), (H, W, 3))

            target[:] = composite_over(target, col_outer, (outer ** 0.72) * 0.90)
            target[:] = composite_over(target, col_mid, (mid ** 0.78) * 0.94)
            target[:] = composite_over(target, col_core, np.clip((core ** 0.82) * 0.96 + diamonds * 0.85, 0.0, 1.0))

        # 2) Direct Rear-Facing Rocket Nozzle Blast (when viewing her from behind: fwd_z < -0.35, blasting AT camera!)
        if fwd_z < -0.35:
            rear_w = min(1.0, (-fwd_z - 0.35) / 0.55) * boost_scale
            r_nozzle = (36.0 + 8.0 * math.sin(t * 2.0)) * rear_w
            dx_n = xg - cx
            dy_n = (yg - (y_axle + 6.0)) * 0.88
            rn = np.hypot(dx_n, dy_n)
            ang_n = np.arctan2(dy_n, dx_n)
            star_rays = 1.0 + 0.28 * np.sin(8.0 * ang_n + t * 2.0) + 0.16 * np.cos(5.0 * ang_n - t * 3.0)
            r_mod = rn / np.maximum(star_rays, 0.4)
            noz_outer = np.clip(1.0 - r_mod / max(r_nozzle * 1.45, 1.0), 0.0, 1.0)
            noz_mid = np.clip(1.0 - r_mod / max(r_nozzle * 0.95, 1.0), 0.0, 1.0)
            noz_core = np.clip(1.0 - rn / max(r_nozzle * 0.48, 1.0), 0.0, 1.0)
            col_outer = np.broadcast_to(np.array([255.0, 24.0, 165.0], np.float32), (H, W, 3))
            col_mid = np.broadcast_to(np.array([255.0, 152.0, 20.0], np.float32), (H, W, 3))
            col_core = np.broadcast_to(np.array([255.0, 255.0, 220.0], np.float32), (H, W, 3))
            front_layer[:] = composite_over(front_layer, col_outer, (noz_outer ** 0.75) * 0.88)
            front_layer[:] = composite_over(front_layer, col_mid, (noz_mid ** 0.8) * 0.94)
            front_layer[:] = composite_over(front_layer, col_core, (noz_core ** 0.85) * 0.98)

        # 3) Front-view warm Nitro Back-Glow behind the axle when hurtling straight AT the viewer!
        if fwd_z > 0.45:
            fw_w = min(1.0, (fwd_z - 0.45) / 0.50) * boost_scale
            dx_b = (xg - cx) / (115.0 * fw_w + 10.0)
            dy_b = (yg - (y_axle - 10.0)) / (44.0 * fw_w + 8.0)
            glow = np.exp(-(dx_b * dx_b + dy_b * dy_b)) * (0.58 + 0.16 * math.sin(t * 2.0))
            col_g = np.broadcast_to(np.array([255.0, 75.0, 175.0], np.float32), (H, W, 3))
            back_layer[:] = composite_over(back_layer, col_g, glow)

    # --- B. Billowing Cartoon Tire Burnout Smoke Puffs (fast local ROI) ---
    n_puffs = 4 if mode == "idle" else 9
    for w_idx, (wx, z_sign) in enumerate(((lx_tire, -math.sin(rad)), (rx_tire, math.sin(rad)))):
        for p_i in range(n_puffs):
            prog = ((p_i / float(n_puffs)) + phase_01) % 1.0
            drift_x = ex_x * (18.0 + 88.0 * prog) + (wx - cx) * 0.08 * prog + rng.uniform(-7.0, 7.0)
            drift_y = -6.0 - (38.0 if mode != "idle" else 16.0) * (prog ** 0.85) + rng.uniform(-4.0, 4.0)
            rad_p = (11.0 + (26.0 if mode != "idle" else 12.0) * (prog ** 0.7))
            px = wx + drift_x
            py = tire_y + drift_y
            x0 = max(0, int(px - rad_p - 5))
            x1 = min(W, int(px + rad_p + 6))
            y0 = max(0, int(py - rad_p - 5))
            y1 = min(H, int(py + rad_p + 6))
            if x1 <= x0 or y1 <= y0:
                continue
            lx_g = xg[y0:y1, x0:x1]
            ly_g = yg[y0:y1, x0:x1]
            dist = np.hypot(lx_g - px, ly_g - py)
            puff_a = np.clip((rad_p - dist) / 3.5, 0.0, 1.0) * ((1.0 - prog) ** 1.15) * (0.42 if mode == "idle" else 0.72)
            if not np.any(puff_a > 0.01):
                continue
            shade = np.clip(0.5 - 0.35 * (ly_g - py) / max(rad_p, 1.0), 0.0, 1.0)[..., None]
            c_top = np.array([248.0, 246.0, 252.0], np.float32)
            c_bot = np.array([212.0, 178.0, 218.0], np.float32)
            col_p = c_bot * (1.0 - shade) + c_top * shade
            target = front_layer if ((fwd_z < -0.25) or (z_sign > 0.55 and prog > 0.25)) else back_layer
            target[y0:y1, x0:x1] = composite_over(target[y0:y1, x0:x1], col_p, puff_a)

    # --- C. Titanium Pavement Sparks (fast local ROI on Turbo & Wheelie!) ---
    if mode in ("turbo", "wheelie"):
        n_sparks = 14 if mode == "wheelie" else 8
        for s_i in range(n_sparks):
            wx = lx_tire if (s_i % 2 == 0) else rx_tire
            prog = ((s_i * 0.17 + phase_01 * 1.5) % 1.0)
            sx0 = wx + ex_x * (10.0 + 95.0 * prog) + rng.uniform(-12.0, 12.0)
            sy0 = tire_y - (46.0 * prog * (1.0 - 0.65 * prog)) + rng.uniform(-6.0, 4.0)
            vx_s = ex_x * 16.0 + rng.uniform(-6.0, 6.0)
            vy_s = -10.0 + 18.0 * prog
            slen = max(math.hypot(vx_s, vy_s), 4.0)
            x0 = max(0, int(min(sx0, sx0 + vx_s) - 6))
            x1 = min(W, int(max(sx0, sx0 + vx_s) + 7))
            y0 = max(0, int(min(sy0, sy0 + vy_s) - 6))
            y1 = min(H, int(max(sy0, sy0 + vy_s) + 7))
            if x1 <= x0 or y1 <= y0:
                continue
            lx_g = xg[y0:y1, x0:x1]
            ly_g = yg[y0:y1, x0:x1]
            ux_s, uy_s = vx_s / slen, vy_s / slen
            dx_s, dy_s = lx_g - sx0, ly_g - sy0
            proj = np.clip(dx_s * ux_s + dy_s * uy_s, 0.0, slen)
            d_seg = np.hypot(dx_s - proj * ux_s, dy_s - proj * uy_s)
            sp_a = np.clip((2.4 - d_seg) / 1.4, 0.0, 1.0) * (1.0 - 0.7 * prog)
            if np.any(sp_a > 0.02):
                col_sp = np.broadcast_to(np.array([255.0, 232.0, 110.0], np.float32), sp_a.shape + (3,))
                front_layer[y0:y1, x0:x1] = composite_over(front_layer[y0:y1, x0:x1], col_sp, sp_a)

    # --- D. Signature Gag: Anime Chrome Torpedo Tip 'TING!' Starburst (when shaft faces viewer!) ---
    if fwd_z > 0.32 and mode in ("turbo", "wheelie"):
        # Pulse a 4-point chrome specular star right on the rounded nose of the chrome shaft!
        star_pulse = max(0.0, math.sin(t + 0.6)) ** 1.6
        if star_pulse > 0.08:
            # Locate bottom-most pixels near shaft column (cx + fwd_x * 95)
            shaft_x = cx + fwd_x * 105.0
            x_win = (np.abs(xg[0, :] - shaft_x) < 42.0)
            alpha_m = rgba[..., 3] > 140
            sub = alpha_m[:, x_win]
            if np.any(sub):
                ys_s, xs_s = np.nonzero(sub)
                idx_bot = int(np.argmax(ys_s))
                gx_s = float(np.nonzero(x_win)[0][xs_s[idx_bot]]) - 5.0 * fwd_x
                gy_s = float(ys_s[idx_bot]) - 16.0
                dx_g = xg - gx_s
                dy_g = yg - gy_s
                # Rotated 4-point star + soft halo
                r_g = np.hypot(dx_g, dy_g)
                ray_h = np.exp(-((dy_g / 2.2) ** 2)) * np.exp(-(np.abs(dx_g) / (26.0 * star_pulse + 4.0)))
                ray_v = np.exp(-((dx_g / 2.2) ** 2)) * np.exp(-(np.abs(dy_g) / (26.0 * star_pulse + 4.0)))
                halo = np.exp(-((r_g / (9.0 * star_pulse + 2.0)) ** 2))
                glint_a = np.clip((ray_h + ray_v + 0.75 * halo) * star_pulse, 0.0, 1.0)
                col_glint = np.broadcast_to(np.array([255.0, 252.0, 255.0], np.float32), (H, W, 3))
                front_layer[:] = composite_over(front_layer, col_glint, glint_a)

    # Composite: back_layer -> kart_rgba -> front_layer
    kart_f = np.concatenate([rgba[..., :3].astype(np.float32), rgba[..., 3:4].astype(np.float32) / 255.0], axis=-1)
    comp = composite_over(back_layer, kart_f[..., :3], kart_f[..., 3])
    comp = composite_over(comp, front_layer[..., :3], front_layer[..., 3])
    return np.dstack([np.clip(comp[..., :3], 0, 255).astype(np.uint8), np.clip(comp[..., 3] * 255.0, 0, 255).astype(np.uint8)])


# ---------------------------------------------------------------------------
# 5. Quake SPR32 + MD3 + Shader Exporters
# ---------------------------------------------------------------------------

def tone_for_darkplaces(im_rgba, dim=0.46, contrast=1.22):
    """DarkPlaces runs r_hdr_scenebrightness 2.5 in BakersfieldQuake: tone diffuse PNGs cleanly like pinklady/pickle."""
    rgb = im_rgba.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Brightness(rgb).enhance(dim)
    rgb.putalpha(im_rgba.getchannel("A"))
    return rgb


def write_quake_spr32(out_path, dir8_idle, dir8_drive):
    """Writes progs/jesskart.spr32 using the exact 56-frame Friend_Customize layout (build_friend_sprites.py):
         frames  0..7  : 8-direction revving idle (d = 0..7, 45*d deg)
         frames  8..55 : 8-direction x 6-frame turbo burnout drive (8 + d*6 + k)
       Origin is anchored at ground tire contact center (ox = -w//2, oy = h - bottom_pad).
    """
    frames_data = []
    target_h = 160  # crisp high-detail kart sprite (drawn at .scale 0.45..0.55 in DarkPlaces)
    all_src = list(dir8_idle) + [im for seq in dir8_drive for im in seq]
    src_w, src_h = all_src[0].size
    scale = target_h / float(src_h)
    target_w = max(1, round(src_w * scale))
    oy_feet = round(target_h * 0.90)  # ground contact sits at 90% down the frame
    ox_mid = -(target_w // 2)

    for im in all_src:
        toned = tone_for_darkplaces(im, dim=0.52, contrast=1.20)
        resized = toned.resize((target_w, target_h), Image.LANCZOS)
        frames_data.append((resized, ox_mid, oy_feet))

    rad = math.sqrt((target_w / 2.0) ** 2 + target_h ** 2)
    buf = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, 2, rad, target_w, target_h, len(frames_data), 0.0, 0))
    for im, ox, oy in frames_data:
        w, h = im.size
        buf += struct.pack("<i", 0) + struct.pack("<iiii", ox, oy, w, h) + im.tobytes()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(buf)
    print(f"wrote {out_path} ({len(frames_data)} frames, {target_w}x{target_h}, {len(buf)/1e6:.2f} MB)")


def write_quake_md3_and_shaders(mod_dir, views16_anim):
    """Writes 16-angle DarkPlaces billboard card MD3 + skins + animated shaders (matching pinklady.md3):
         - progs/jesskart.md3 (24x24 card, z=0..24 ground-anchored or centered)
         - progs/jesskart.md3_0.skin .. 15.skin
         - progs/jesskart_00..15.png + animated front (jesskart_f00..05.png) & rear (jesskart_r00..05.png)
         - scripts/jesskart.shader
    """
    progs_dir = os.path.join(mod_dir, "progs")
    scripts_dir = os.path.join(mod_dir, "scripts")
    os.makedirs(progs_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    tex_sz = 512
    for k in range(16):
        # Save key turbo frame for all 16 directions
        im_sq = Image.new("RGBA", (tex_sz, tex_sz), (0, 0, 0, 0))
        src = tone_for_darkplaces(views16_anim[k][1], dim=0.46, contrast=1.24)
        s = min(tex_sz / float(src.width), tex_sz / float(src.height))
        rw, rh = round(src.width * s), round(src.height * s)
        im_sq.paste(src.resize((rw, rh), Image.LANCZOS), ((tex_sz - rw) // 2, (tex_sz - rh) // 2))
        im_sq.save(os.path.join(progs_dir, f"jesskart_{k:02d}.png"))

    # Save 6-frame animated loops for front (view 0) and rear (view 8) so chasing or fleeing looks alive even via static skin!
    for prefix, v_idx in (("f", 0), ("r", 8)):
        for f_i, frame_im in enumerate(views16_anim[v_idx]):
            im_sq = Image.new("RGBA", (tex_sz, tex_sz), (0, 0, 0, 0))
            src = tone_for_darkplaces(frame_im, dim=0.46, contrast=1.24)
            s = min(tex_sz / float(src.width), tex_sz / float(src.height))
            rw, rh = round(src.width * s), round(src.height * s)
            im_sq.paste(src.resize((rw, rh), Image.LANCZOS), ((tex_sz - rw) // 2, (tex_sz - rh) // 2))
            im_sq.save(os.path.join(progs_dir, f"jesskart_{prefix}{f_i:02d}.png"))

    # Write scripts/jesskart.shader
    shader_lines = ["// written by source/mm_tools/build_jesskart_sprite.py\n"]
    for k in range(16):
        if k in (15, 0, 1) and k != 0:
            continue
        if k in (7, 8, 9) and k != 8:
            continue
        shader_lines.append(f"progs/jesskart_v{k:02d}\n{{\n\tcull none\n\t{{\n")
        if k == 0:
            seq = " ".join(f"progs/jesskart_f{i:02d}" for i in range(6))
            shader_lines.append(f"\t\tanimmap 10 {seq}\n")
        elif k == 8:
            seq = " ".join(f"progs/jesskart_r{i:02d}" for i in range(6))
            shader_lines.append(f"\t\tanimmap 10 {seq}\n")
        else:
            shader_lines.append(f"\t\tmap progs/jesskart_{k:02d}\n")
        shader_lines.append("\t\talphafunc GE128\n\t}\n}\n")

    shader_path = os.path.join(scripts_dir, "jesskart.shader")
    with open(shader_path, "w", encoding="utf-8") as f:
        f.write("".join(shader_lines))

    # Write 1-card 1-frame MD3 + 16 instant-swap .skin files (prevents DarkPlaces frame-lerp pulsing!)
    half = 14.0
    card = [(0.0, half, -half), (0.0, half, half), (0.0, -half, half), (0.0, -half, -half)]
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]
    surf = dict(name="card", shader="progs/jesskart_v00", tris=tris, st=st, frames=[(card, [(-1.0, 0.0, 0.0)] * 4)])
    md3_path = os.path.join(progs_dir, "jesskart.md3")
    md3lib.write(md3_path, dict(name="jesskart", surfaces=[surf], nframes=1))

    for old in glob.glob(os.path.join(progs_dir, "jesskart.md3_*.skin")):
        os.remove(old)
    for k in range(16):
        sh_idx = 0 if k in (15, 0, 1) else (8 if k in (7, 8, 9) else k)
        with open(os.path.join(progs_dir, f"jesskart.md3_{k}.skin"), "w", encoding="utf-8") as f:
            f.write(f"card,progs/jesskart_v{sh_idx:02d}\n")
    print(f"wrote {md3_path} (16 views + skins) and {shader_path}")


# ---------------------------------------------------------------------------
# 6. Interactive HTML Playground ('JESS-KART 3000')
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JESS-KART 3000 — Funny 360° Arcade Sprite</title>
<style>
  :root {
    --bg: #15171c;
    --panel: #21252e;
    --panel2: #2b303c;
    --ink: #f3f4f8;
    --dim: #9da3b4;
    --pink: #ff2ca8;
    --orange: #ff8c24;
    --cyan: #38e8ff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: radial-gradient(circle at 50% 15%, #261b2e 0%, var(--bg) 65%);
    color: var(--ink); font: 14px/1.45 system-ui, -apple-system, Segoe UI, sans-serif;
    display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 18px; min-height: 100vh;
  }
  header { text-align: center; max-width: 960px; }
  h1 {
    margin: 0; font-size: 24px; font-weight: 900; letter-spacing: 0.04em; text-transform: uppercase;
    background: linear-gradient(90deg, var(--pink), var(--orange), #ffe566);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .sub { color: var(--dim); margin: 4px 0 0; font-size: 13px; }
  #arena-wrap {
    position: relative; width: min(100%, 940px); aspect-ratio: 16 / 10;
    border-radius: 14px; overflow: hidden; border: 2px solid #353b4a;
    box-shadow: 0 18px 48px rgba(0,0,0,0.55);
    background: repeating-conic-gradient(#262a34 0% 25%, #1e212a 0% 50%) 0 0 / 28px 28px;
    cursor: grab; touch-action: none; user-select: none;
  }
  #arena-wrap.drag { cursor: grabbing; }
  canvas#stage { width: 100%; height: 100%; display: block; }
  .hud-badge {
    position: absolute; top: 12px; left: 12px; display: flex; gap: 8px; flex-wrap: wrap; pointer-events: none;
  }
  .pill {
    background: rgba(18, 20, 26, 0.84); border: 1px solid rgba(255, 44, 168, 0.45);
    padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; color: #ffd9f0;
    backdrop-filter: blur(6px);
  }
  .hud-help {
    position: absolute; bottom: 10px; left: 12px; right: 12px; display: flex; justify-content: space-between;
    pointer-events: none; font-size: 12px; color: rgba(240,242,250,0.82);
    text-shadow: 0 1px 4px rgba(0,0,0,0.9);
  }
  .bar {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center;
    width: min(100%, 940px); background: var(--panel); border: 1px solid #313746;
    border-radius: 12px; padding: 10px 14px;
  }
  button {
    background: var(--panel2); color: var(--ink); border: 1px solid #3e4558;
    border-radius: 8px; padding: 7px 13px; font: inherit; font-weight: 700; cursor: pointer;
    transition: transform 0.08s, background 0.15s, border-color 0.15s;
  }
  button:hover { border-color: var(--pink); }
  button:active { transform: translateY(1px); }
  button.active {
    background: linear-gradient(135deg, var(--pink), #d81b8a); color: #fff; border-color: #ff8bd2;
    box-shadow: 0 0 16px rgba(255,44,168,0.4);
  }
  button.honk {
    background: linear-gradient(135deg, var(--orange), #ff4800); color: #fff; border-color: #ffc278;
  }
  label { color: var(--dim); display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; }
  input[type=range] { accent-color: var(--pink); cursor: pointer; }
  .sep { width: 1px; height: 24px; background: #363c4d; margin: 0 4px; }
  #strip {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
    gap: 6px; width: min(100%, 940px);
  }
  #strip button {
    padding: 2px; background: var(--panel); border: 2px solid transparent; border-radius: 8px;
    aspect-ratio: 1 / 1; overflow: hidden; display: flex; align-items: center; justify-content: center;
  }
  #strip button.on { border-color: var(--pink); background: #2d1f30; }
  #strip img { width: 100%; height: 100%; object-fit: contain; display: block; }
</style>
</head>
<body>
  <header>
    <h1>🏎️ JESS-KART 3000 — 360° Funny Arcade Sprite</h1>
    <p class="sub">24-Angle Calibrated Photo Cutouts • Perspective-Spinning Wheels • 2-Stroke Bounce • Chrome Torpedo Wheelie • Quake SPR32 &amp; MD3 Ready</p>
  </header>

  <div id="arena-wrap">
    <canvas id="stage" width="940" height="588"></canvas>
    <div class="hud-badge">
      <span class="pill" id="mode-pill">🔥 NITRO BURNOUT</span>
      <span class="pill" id="angle-pill">Angle 00 (0°)</span>
      <span class="pill" id="speed-pill" style="display:none">0 MPH</span>
    </div>
    <div class="hud-help">
      <span id="hint-left">🖱️ Drag horizontally to spin 360° • Left/Right arrows step angles</span>
      <span id="hint-right">SPACE = Pop Wheelie • H = Clown Air-Horn</span>
    </div>
  </div>

  <div class="bar">
    <button class="mode-btn active" data-mode="turbo">🔥 Nitro Burnout</button>
    <button class="mode-btn" data-mode="wheelie">🚀 Chrome Wheelie</button>
    <button class="mode-btn" data-mode="clean">✨ Clean 360° Cutout</button>
    <button class="mode-btn" data-mode="drive">🎮 Drive in Arena (WASD)</button>
    <div class="sep"></div>
    <button id="spin-toggle">⏸ Pause Spin</button>
    <button class="honk" id="honk-btn">📢 HONK! (H)</button>
    <label>Turn <input id="turn-fps" type="range" min="0" max="20" value="6" style="width:85px"></label>
    <label>Bg
      <select id="bg-sel" style="background:#2b303c;color:#fff;border:1px solid #454d63;border-radius:6px;padding:4px 6px;font:inherit">
        <option value="grid">Neon Race Grid</option>
        <option value="checker">Alpha Checker</option>
        <option value="quake">Bakersfield Asphalt</option>
      </select>
    </label>
  </div>

  <div id="strip"></div>

<script>
const N_ANGLES = 24;
const N_FRAMES = 6;
const pad2 = n => String(n).padStart(2, "0");

// Preload all 24 clean + 24x6 turbo + 24x6 wheelie frames
const imgs = { clean: [], turbo: [], wheelie: [] };
for (let a = 0; a < N_ANGLES; a++) {
  const ic = new Image(); ic.src = `clean/jesskart_clean_${pad2(a)}.png`;
  imgs.clean.push([ic]);
  const ft = [], fw = [];
  for (let f = 0; f < N_FRAMES; f++) {
    const it = new Image(); it.src = `anim/turbo_${pad2(a)}_f${f}.png`; ft.push(it);
    const iw = new Image(); iw.src = `anim/wheelie_${pad2(a)}_f${f}.png`; fw.push(iw);
  }
  imgs.turbo.push(ft);
  imgs.wheelie.push(fw);
}

const canvas = document.getElementById("stage");
const ctx = canvas.getContext("2d");
const wrap = document.getElementById("arena-wrap");
const strip = document.getElementById("strip");
const modePill = document.getElementById("mode-pill");
const anglePill = document.getElementById("angle-pill");
const speedPill = document.getElementById("speed-pill");
const spinBtn = document.getElementById("spin-toggle");
const turnFpsEl = document.getElementById("turn-fps");
const bgSel = document.getElementById("bg-sel");

let mode = "turbo";
let curAngle = 0;
let autoSpin = true;
let animFrame = 0;
let spaceWheelie = false;
let honkPop = 0;

// Playable Drive-Mode state
const kart = { x: 470, y: 340, heading: 90, speed: 0, wheelie: 0, skid: [] };
const keys = {};

// Build 24-angle thumbnail strip
const thumbs = [];
for (let a = 0; a < N_ANGLES; a++) {
  const b = document.createElement("button");
  b.title = `Angle ${a} (${a * 15}°)`;
  const im = document.createElement("img");
  im.src = `jesskart_${pad2(a)}.png`;
  b.appendChild(im);
  b.onclick = () => {
    curAngle = a;
    if (mode !== "drive") { autoSpin = false; syncButtons(); }
    syncThumbs();
  };
  strip.appendChild(b);
  thumbs.push(b);
}
function syncThumbs() {
  thumbs.forEach((b, i) => b.classList.toggle("on", i === curAngle));
  anglePill.textContent = `Angle ${pad2(curAngle)} (${curAngle * 15}°)`;
}
syncThumbs();

// WebAudio goofy clown air-horn + revving 2-stroke pop!
let audioCtx = null;
function playGoofyHorn() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const now = audioCtx.currentTime;
    // Two-note "AWOO-GA / HONK-HONK!" reed horn
    [[0.0, 310, 390, 0.14], [0.16, 390, 520, 0.24]].forEach(([t0, f1, f2, dur]) => {
      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc1.type = "sawtooth"; osc2.type = "triangle";
      osc1.frequency.setValueAtTime(f1, now + t0);
      osc1.frequency.exponentialRampToValueAtTime(f2, now + t0 + dur * 0.7);
      osc2.frequency.setValueAtTime(f1 * 1.498, now + t0);
      osc2.frequency.exponentialRampToValueAtTime(f2 * 1.498, now + t0 + dur * 0.7);
      gain.gain.setValueAtTime(0.001, now + t0);
      gain.gain.exponentialRampToValueAtTime(0.16, now + t0 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + t0 + dur);
      osc1.connect(gain); osc2.connect(gain); gain.connect(audioCtx.destination);
      osc1.start(now + t0); osc2.start(now + t0);
      osc1.stop(now + t0 + dur + 0.02); osc2.stop(now + t0 + dur + 0.02);
    });
  } catch (e) {}
  honkPop = 1.0;
}

document.getElementById("honk-btn").onclick = playGoofyHorn;

function syncButtons() {
  document.querySelectorAll(".mode-btn").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
  spinBtn.textContent = autoSpin ? "⏸ Pause Spin" : "▶ Auto-Spin 360°";
  spinBtn.style.display = mode === "drive" ? "none" : "";
  speedPill.style.display = mode === "drive" ? "" : "none";
  const labels = {
    turbo: "🔥 NITRO BURNOUT",
    wheelie: "🚀 CHROME WHEELIE",
    clean: "✨ CLEAN 360° CUTOUT",
    drive: "🎮 ARENA DRIVE (WASD / ARROWS)"
  };
  modePill.textContent = labels[mode];
  document.getElementById("hint-left").textContent = mode === "drive"
    ? "⌨️ W/S or Up/Down = Throttle/Reverse • A/D or Left/Right = Steer"
    : "🖱️ Drag horizontally to spin 360° • Left/Right arrows step angles";
}

document.querySelectorAll(".mode-btn").forEach(b => {
  b.onclick = () => {
    mode = b.dataset.mode;
    syncButtons();
  };
});
spinBtn.onclick = () => { autoSpin = !autoSpin; syncButtons(); };

addEventListener("keydown", e => {
  keys[e.code] = true;
  if (e.code === "KeyH") playGoofyHorn();
  if (e.code === "Space") { e.preventDefault(); spaceWheelie = true; }
  if (mode !== "drive") {
    if (e.code === "ArrowRight") { autoSpin = false; curAngle = (curAngle + 1) % N_ANGLES; syncThumbs(); syncButtons(); }
    if (e.code === "ArrowLeft")  { autoSpin = false; curAngle = (curAngle + N_ANGLES - 1) % N_ANGLES; syncThumbs(); syncButtons(); }
  } else if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(e.code)) {
    e.preventDefault();
  }
});
addEventListener("keyup", e => {
  keys[e.code] = false;
  if (e.code === "Space") spaceWheelie = false;
});

// Pointer drag 360 scrub
let dragStartX = null, dragStartAng = 0;
wrap.addEventListener("pointerdown", e => {
  if (mode === "drive") return;
  dragStartX = e.clientX; dragStartAng = curAngle;
  autoSpin = false; syncButtons();
  wrap.classList.add("drag"); wrap.setPointerCapture(e.pointerId);
});
wrap.addEventListener("pointermove", e => {
  if (dragStartX === null) return;
  const delta = Math.round((e.clientX - dragStartX) / 16);
  curAngle = ((dragStartAng - delta) % N_ANGLES + N_ANGLES) % N_ANGLES;
  syncThumbs();
});
const endDrag = () => { dragStartX = null; wrap.classList.remove("drag"); };
wrap.addEventListener("pointerup", endDrag);
wrap.addEventListener("pointercancel", endDrag);

function drawBackground(tSec) {
  const style = bgSel.value;
  const W = canvas.width, H = canvas.height;
  if (style === "checker") {
    ctx.clearRect(0, 0, W, H);
    return;
  }
  if (style === "quake") {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#1c1722"); g.addColorStop(0.45, "#2f2433");
    g.addColorStop(0.46, "#2c2d34"); g.addColorStop(1, "#18191e");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // Curb stripes
    for (let i = 0; i < 16; i++) {
      ctx.fillStyle = i % 2 === 0 ? "#ff2ca8" : "#f4f4f8";
      ctx.fillRect(i * 64 - ((tSec * 90) % 128), H * 0.455, 64, 6);
    }
    return;
  }
  // Neon synthwave race horizon
  const sky = ctx.createLinearGradient(0, 0, 0, H * 0.48);
  sky.addColorStop(0, "#12091c"); sky.addColorStop(1, "#3b1345");
  ctx.fillStyle = sky; ctx.fillRect(0, 0, W, H * 0.48);

  const floor = ctx.createLinearGradient(0, H * 0.48, 0, H);
  floor.addColorStop(0, "#231230"); floor.addColorStop(1, "#110d19");
  ctx.fillStyle = floor; ctx.fillRect(0, H * 0.48, W, H * 0.52);

  ctx.strokeStyle = "rgba(255, 44, 168, 0.28)";
  ctx.lineWidth = 1.5;
  const hz = H * 0.48;
  for (let i = -10; i <= 10; i++) {
    ctx.beginPath();
    ctx.moveTo(W / 2 + i * 28, hz);
    ctx.lineTo(W / 2 + i * 190, H);
    ctx.stroke();
  }
  const scroll = (tSec * 1.4) % 1;
  for (let r = 0; r < 8; r++) {
    const p = Math.pow((r + scroll) / 8, 1.8);
    const y = hz + p * (H - hz);
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }
}

let lastTurnT = 0, lastAnimT = 0, lastDtT = performance.now();
function loop(now) {
  const dt = Math.min(0.05, (now - lastDtT) / 1000);
  lastDtT = now;
  const tSec = now / 1000;

  if (now - lastAnimT > 75) {
    lastAnimT = now;
    animFrame = (animFrame + 1) % N_FRAMES;
  }
  if (honkPop > 0) honkPop = Math.max(0, honkPop - dt * 3.2);

  drawBackground(tSec);

  if (mode === "drive") {
    // 2D Arcade Kart physics!
    const throttle = (keys["KeyW"] || keys["ArrowUp"] ? 1 : 0) - (keys["KeyS"] || keys["ArrowDown"] ? 0.65 : 0);
    const steer = (keys["KeyD"] || keys["ArrowRight"] ? 1 : 0) - (keys["KeyA"] || keys["ArrowLeft"] ? 1 : 0);
    const boost = (keys["ShiftLeft"] || keys["ShiftRight"]) ? 1.45 : 1.0;

    kart.speed += throttle * 520 * boost * dt;
    kart.speed *= Math.pow(0.22, dt);
    if (Math.abs(kart.speed) > 8) {
      const dirSign = kart.speed >= 0 ? 1 : -1;
      kart.heading = (kart.heading + steer * 155 * dirSign * dt + 360) % 360;
    }
    const rad = kart.heading * Math.PI / 180;
    // Screen coords: heading 0 = Down (+Y, toward viewer), 90 = Left (-X), 180 = Up (-Y), 270 = Right (+X)!
    const vx = -Math.sin(rad) * kart.speed;
    const vy =  Math.cos(rad) * kart.speed * 0.62;
    kart.x += vx * dt;
    kart.y += vy * dt;
    if (kart.x < 70) kart.x = 870;
    if (kart.x > 870) kart.x = 70;
    kart.y = Math.max(210, Math.min(525, kart.y));

    if (Math.abs(kart.speed) > 120 && (Math.abs(steer) > 0 || spaceWheelie)) {
      kart.skid.push({ x: kart.x - 24, y: kart.y + 18, life: 1.0 });
      kart.skid.push({ x: kart.x + 24, y: kart.y + 18, life: 1.0 });
      if (kart.skid.length > 160) kart.skid.splice(0, 2);
    }
    // Draw tire skid marks
    for (let i = kart.skid.length - 1; i >= 0; i--) {
      const s = kart.skid[i];
      s.life -= dt * 0.45;
      if (s.life <= 0) { kart.skid.splice(i, 1); continue; }
      ctx.fillStyle = `rgba(20, 18, 24, ${s.life * 0.55})`;
      ctx.beginPath(); ctx.ellipse(s.x, s.y, 7, 3.5, 0, 0, Math.PI * 2); ctx.fill();
    }

    curAngle = Math.round(kart.heading / 15) % N_ANGLES;
    syncThumbs();
    speedPill.textContent = `${Math.round(Math.abs(kart.speed) * 0.18)} MPH`;

    const bank = spaceWheelie ? imgs.wheelie : (Math.abs(kart.speed) > 25 ? imgs.turbo : imgs.clean);
    const seq = bank[curAngle];
    const im = seq[animFrame % seq.length];
    const depthScale = 0.46 + 0.36 * ((kart.y - 210) / 315);
    if (im && im.complete) {
      const dw = im.naturalWidth * depthScale * (1 + 0.08 * honkPop);
      const dh = im.naturalHeight * depthScale * (1 - 0.06 * honkPop);
      // Ground shadow oval
      ctx.fillStyle = "rgba(0,0,0,0.38)";
      ctx.beginPath(); ctx.ellipse(kart.x, kart.y + 18 * depthScale, dw * 0.34, dh * 0.07, 0, 0, Math.PI * 2); ctx.fill();
      ctx.drawImage(im, kart.x - dw / 2, kart.y - dh * 0.84, dw, dh);
    }
  } else {
    const turnFps = +turnFpsEl.value;
    if (autoSpin && turnFps > 0 && now - lastTurnT > 1000 / turnFps) {
      lastTurnT = now;
      curAngle = (curAngle + 1) % N_ANGLES;
      syncThumbs();
    }
    const activeMode = spaceWheelie ? "wheelie" : mode;
    const seq = imgs[activeMode][curAngle];
    const im = seq[animFrame % seq.length];
    if (im && im.complete) {
      const scale = Math.min((canvas.width * 0.78) / im.naturalWidth, (canvas.height * 0.90) / im.naturalHeight);
      const dw = im.naturalWidth * scale * (1 + 0.07 * honkPop);
      const dh = im.naturalHeight * scale * (1 - 0.05 * honkPop);
      const cx = canvas.width / 2, cy = canvas.height * 0.53;
      ctx.fillStyle = "rgba(0,0,0,0.35)";
      ctx.beginPath(); ctx.ellipse(cx, cy + dh * 0.37, dw * 0.34, dh * 0.065, 0, 0, Math.PI * 2); ctx.fill();
      ctx.drawImage(im, cx - dw / 2, cy - dh / 2, dw, dh);
    }
  }

  if (honkPop > 0.15) {
    ctx.save();
    ctx.font = "900 32px system-ui, sans-serif";
    ctx.fillStyle = "#ffe548";
    ctx.strokeStyle = "#ff1e9a";
    ctx.lineWidth = 5;
    const hx = mode === "drive" ? kart.x + 48 : canvas.width * 0.64;
    const hy = (mode === "drive" ? kart.y - 110 : canvas.height * 0.22) - (1 - honkPop) * 24;
    ctx.strokeText("HONK! 📢", hx, hy);
    ctx.fillText("HONK! 📢", hx, hy);
    ctx.restore();
  }

  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 7. Main Orchestration Pipeline
# ---------------------------------------------------------------------------

def main():
    vid_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VID
    mod_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MOD
    sprite_dir = os.path.join(mod_dir, "jesskart_sprite")
    os.makedirs(os.path.join(sprite_dir, "clean"), exist_ok=True)
    os.makedirs(os.path.join(sprite_dir, "anim"), exist_ok=True)

    print(f"[1/6] Loading turntable video: {vid_path}")
    frames = load_video_frames(vid_path)
    angle_map = build_calibrated_angle_map(frames)

    # Extract 24 angles (15 deg steps) + any extra frames needed for 16 angles (22.5 deg steps)
    unique_f = {}
    angles_24 = [i * 15.0 for i in range(24)]
    angles_16 = [i * 22.5 for i in range(16)]
    for ang in angles_24 + angles_16:
        f_idx = pick_frame(angle_map, ang)
        if f_idx not in unique_f:
            unique_f[f_idx] = None

    print(f"[2/6] Segmenting {len(unique_f)} unique studio turntable frames + wheel hub ellipses...")
    for f_idx in sorted(unique_f.keys()):
        unique_f[f_idx] = segment_kart_frame(frames[f_idx])

    # Compute smooth global framing across the 24 angles so ground contact & rotation axis never jitter
    bboxes = []
    for ang in angles_24:
        rgba, mask, _ = unique_f[pick_frame(angle_map, ang)]
        ys, xs = np.nonzero(mask)
        bboxes.append((float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())))

    max_span_x = max(b[2] - b[0] for b in bboxes)
    max_span_y = max(b[3] - b[1] for b in bboxes)
    mean_cx = sum(0.5 * (b[0] + b[2]) for b in bboxes) / len(bboxes)
    mean_y_ground = sum(b[3] for b in bboxes) / len(bboxes)

    # Working sprite canvas (640 x 720: generous room above head for wheelie & behind tires for nitro/smoke!)
    OUT_W, OUT_H = 640, 720
    scale = min((OUT_W * 0.74) / max_span_x, (OUT_H * 0.74) / max_span_y)
    dst_cx = OUT_W * 0.5
    dst_y_ground = OUT_H * 0.89
    dst_y_saddle = dst_y_ground - 255.0 * scale

    def place_on_canvas(f_idx):
        rgba, mask, ellipses = unique_f[f_idx]
        ys, xs = np.nonzero(mask)
        # Keep subtle per-frame bottom tire contact locked smoothly to dst_y_ground
        f_y_bot = 0.65 * float(ys.max()) + 0.35 * mean_y_ground
        f_cx = 0.35 * (0.5 * float(xs.min() + xs.max())) + 0.65 * mean_cx

        rw, rh = round(rgba.shape[1] * scale), round(rgba.shape[0] * scale)
        im_res = Image.fromarray(rgba, "RGBA").resize((rw, rh), Image.LANCZOS)
        ox = round(dst_cx - f_cx * scale)
        oy = round(dst_y_ground - f_y_bot * scale)

        canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
        canvas.paste(im_res, (ox, oy), im_res)
        c_arr = np.array(canvas, dtype=np.uint8)
        c_ellipses = [
            (cx_w * scale + ox, cy_w * scale + oy, ra * scale, rb * scale, phi)
            for (cx_w, cy_w, ra, rb, phi) in ellipses
        ]
        return c_arr, c_ellipses

    print("[3/6] Synthesizing 24x6 Nitro Burnout + 24x6 Chrome Wheelie + Clean 360° Sprite Frames...")
    N_ANIM = 6
    clean_24_pil = []
    key_turbo_24_pil = []
    turbo_24_seqs = []
    wheelie_24_seqs = []

    for a_idx, ang in enumerate(angles_24):
        f_idx = pick_frame(angle_map, ang)
        base_rgba, c_ellipses = place_on_canvas(f_idx)
        im_clean = Image.fromarray(base_rgba, "RGBA")
        im_clean.save(os.path.join(sprite_dir, "clean", f"jesskart_clean_{a_idx:02d}.png"))
        clean_24_pil.append(im_clean)

        # Spin direction sign from viewing angle: at 90 deg (facing left), forward wheel rotation is CCW (-1); at 270 deg (facing right), CW (+1)
        spin_dir = -1.0 if math.sin(math.radians(ang)) >= 0 else 1.0

        t_seq = []
        w_seq = []
        for k in range(N_ANIM):
            ph = k / float(N_ANIM)
            spin_rad = spin_dir * ph * (2.0 * math.pi)

            # 1) Nitro Burnout frame
            spun_t = spin_wheels_in_canvas(base_rgba, c_ellipses, spin_rad, speed_streaks=True)
            def_t = deform_kart_physics(spun_t, dst_cx, dst_y_ground, dst_y_saddle, ang, ph, mode="turbo")
            fx_t = add_arcade_kart_fx(def_t, dst_cx, dst_y_ground, dst_y_saddle, ang, ph, mode="turbo")
            im_t = Image.fromarray(fx_t, "RGBA")
            im_t.save(os.path.join(sprite_dir, "anim", f"turbo_{a_idx:02d}_f{k}.png"))
            t_seq.append(im_t)

            # 2) Chrome Torpedo Wheelie frame
            spun_w = spin_wheels_in_canvas(base_rgba, c_ellipses, spin_rad * 1.5, speed_streaks=True)
            def_w = deform_kart_physics(spun_w, dst_cx, dst_y_ground, dst_y_saddle, ang, ph, mode="wheelie")
            fx_w = add_arcade_kart_fx(def_w, dst_cx, dst_y_ground, dst_y_saddle, ang, ph, mode="wheelie")
            im_w = Image.fromarray(fx_w, "RGBA")
            im_w.save(os.path.join(sprite_dir, "anim", f"wheelie_{a_idx:02d}_f{k}.png"))
            w_seq.append(im_w)

        # Save hero funny frame per angle as jesskart_00..23.png
        t_seq[1].save(os.path.join(sprite_dir, f"jesskart_{a_idx:02d}.png"))
        key_turbo_24_pil.append(t_seq[1])
        turbo_24_seqs.append(t_seq)
        wheelie_24_seqs.append(w_seq)

    print("[4/6] Building Sprite Sheets, Animated GIFs & Interactive HTML Playground...")
    # 6x4 Turnaround Sheet (matching earhead_sheet_6x4.png style)
    cell_w, cell_h = 320, 360
    sheet_6x4 = Image.new("RGBA", (6 * cell_w, 4 * cell_h), (0, 0, 0, 0))
    for i, im in enumerate(key_turbo_24_pil):
        c, r = i % 6, i // 6
        sheet_6x4.paste(im.resize((cell_w, cell_h), Image.LANCZOS), (c * cell_w, r * cell_h))
    sheet_6x4.save(os.path.join(sprite_dir, "jesskart_sheet_6x4.png"))

    # 8-Direction x 4-State Arcade Showcase Sheet (Clean, Nitro Frame A, Nitro Frame B, Chrome Wheelie!)
    arc_w, arc_h = 240, 270
    arcade_sheet = Image.new("RGB", (8 * arc_w, 4 * arc_h + 52), (24, 22, 32))
    dr = ImageDraw.Draw(arcade_sheet)
    dr.rectangle([0, 0, 8 * arc_w, 48], fill=(38, 22, 48))
    dr.text((18, 15), "JESS-KART 3000  |  8-DIRECTION ARCADE SPRITE SHEET  (ROW 1: CLEAN  |  ROW 2-3: NITRO BURNOUT  |  ROW 4: CHROME WHEELIE)", fill=(255, 165, 225))
    dir8_indices_in_24 = [0, 3, 6, 9, 12, 15, 18, 21]  # 0, 45, 90, 135, 180, 225, 270, 315 deg!
    for col_i, idx24 in enumerate(dir8_indices_in_24):
        rows_im = [
            clean_24_pil[idx24],
            turbo_24_seqs[idx24][0],
            turbo_24_seqs[idx24][3],
            wheelie_24_seqs[idx24][1],
        ]
        for row_i, src_im in enumerate(rows_im):
            tile = Image.new("RGBA", (arc_w, arc_h), (30 + 6 * ((col_i + row_i) % 2), 28, 38, 255))
            rsz = src_im.resize((arc_w, arc_h), Image.LANCZOS)
            tile.alpha_composite(rsz)
            arcade_sheet.paste(tile.convert("RGB"), (col_i * arc_w, 52 + row_i * arc_h))
        dr.text((col_i * arc_w + 8, 56), f"{col_i*45}°", fill=(255, 220, 110))
    arcade_sheet.save(os.path.join(sprite_dir, "jesskart_arcade_sheet.png"))

    # Animated GIF 1: 360° Turbo Spin + Wheelie Finale!
    def make_arcade_gif_frame(im_rgba, label_txt):
        gw, gh = 440, 495
        bg = Image.new("RGBA", (gw, gh), (26, 20, 36, 255))
        d = ImageDraw.Draw(bg)
        # Subtle synthwave floor stripes
        d.rectangle([0, int(gh * 0.74), gw, gh], fill=(36, 24, 48, 255))
        d.line([(0, int(gh * 0.74)), (gw, int(gh * 0.74))], fill=(255, 44, 168, 180), width=2)
        d.ellipse([gw * 0.22, gh * 0.84, gw * 0.78, gh * 0.92], fill=(10, 8, 16, 150))
        fg = im_rgba.resize((gw, gh), Image.LANCZOS)
        bg.alpha_composite(fg)
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle([12, 12, 235, 38], radius=12, fill=(18, 14, 26, 215), outline=(255, 44, 168, 200))
        d.text((22, 18), label_txt, fill=(255, 215, 242, 255))
        return bg.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT)

    gif_360 = []
    for i in range(24):
        seq = wheelie_24_seqs[i] if (4 <= i <= 9 or 16 <= i <= 20) else turbo_24_seqs[i]
        tag = f"CHROME WHEELIE  {i*15:3d}°" if (4 <= i <= 9 or 16 <= i <= 20) else f"NITRO BURNOUT   {i*15:3d}°"
        gif_360.append(make_arcade_gif_frame(seq[i % N_ANIM], tag))
    gif_360[0].save(
        os.path.join(sprite_dir, "jesskart_turbo_360.gif"),
        save_all=True, append_images=gif_360[1:], duration=90, loop=0
    )

    # Animated GIF 2: Side-profile Nitro -> Pop-a-Wheelie -> Front Torpedo Glint showcase!
    gif_wheelie = []
    for angle_i, title in ((3, "3/4 TURBO REV!"), (5, "POP A WHEELIE!!"), (6, "FULL SEND!!"), (21, "CHROME TORPEDO!")):
        seq = wheelie_24_seqs[angle_i] if angle_i in (5, 6) else turbo_24_seqs[angle_i]
        for k in range(N_ANIM):
            gif_wheelie.append(make_arcade_gif_frame(seq[k], title))
    gif_wheelie[0].save(
        os.path.join(sprite_dir, "jesskart_wheelie_loop.gif"),
        save_all=True, append_images=gif_wheelie[1:], duration=80, loop=0
    )

    with open(os.path.join(sprite_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE)

    print("[5/6] Exporting Quake DarkPlaces progs/jesskart.spr32 (56 frames, 8-dir idle + 8-dir x 6 drive)...")
    dir8_idle = []
    dir8_drive = []
    for idx24 in dir8_indices_in_24:
        ang = angles_24[idx24]
        f_idx = pick_frame(angle_map, ang)
        base_rgba, c_ellipses = place_on_canvas(f_idx)
        idle_def = deform_kart_physics(base_rgba, dst_cx, dst_y_ground, dst_y_saddle, ang, 0.25, mode="idle")
        idle_fx = add_arcade_kart_fx(idle_def, dst_cx, dst_y_ground, dst_y_saddle, ang, 0.25, mode="idle")
        dir8_idle.append(Image.fromarray(idle_fx, "RGBA"))
        # Mix wheelie pop on frame 2-3 of run cycle for maximum in-game comedy!
        drive_frames = [
            turbo_24_seqs[idx24][0],
            turbo_24_seqs[idx24][1],
            wheelie_24_seqs[idx24][2],
            wheelie_24_seqs[idx24][3],
            turbo_24_seqs[idx24][4],
            turbo_24_seqs[idx24][5],
        ]
        dir8_drive.append(drive_frames)
    write_quake_spr32(os.path.join(mod_dir, "progs", "jesskart.spr32"), dir8_idle, dir8_drive)

    print("[6/6] Exporting Quake DarkPlaces 16-angle progs/jesskart.md3 + skins + scripts/jesskart.shader...")
    views16_anim = []
    for k16, ang16 in enumerate(angles_16):
        f_idx = pick_frame(angle_map, ang16)
        base_rgba, c_ellipses = place_on_canvas(f_idx)
        spin_dir = -1.0 if math.sin(math.radians(ang16)) >= 0 else 1.0
        seq16 = []
        for f_k in range(N_ANIM):
            ph = f_k / float(N_ANIM)
            spun = spin_wheels_in_canvas(base_rgba, c_ellipses, spin_dir * ph * 2.0 * math.pi, speed_streaks=True)
            use_mode = "wheelie" if f_k in (2, 3) else "turbo"
            deformed = deform_kart_physics(spun, dst_cx, dst_y_ground, dst_y_saddle, ang16, ph, mode=use_mode)
            fx = add_arcade_kart_fx(deformed, dst_cx, dst_y_ground, dst_y_saddle, ang16, ph, mode=use_mode)
            seq16.append(Image.fromarray(fx, "RGBA"))
        views16_anim.append(seq16)
    write_quake_md3_and_shaders(mod_dir, views16_anim)
    print("DONE! All JESS-KART 3000 funny sprite assets built successfully.")


if __name__ == "__main__":
    main()
