"""The Pink Lady projectile as a bright, vivid 16-view sprite with animated glossy milk drips.

  progs/pinklady_00..15.png        16 clean, decontaminated, full-sRGB turnaround views (22.5 deg steps)
  progs/pinklady_v02..14_d0..5.png 6-frame continuous downward milk-drip animation for every side/rear view
  progs/pinklady_b00..59.png       60-frame ping-pong front bounce (<= Q3 64-frame animmap cap) with continuous
                                   downward-flowing milk rivulets & falling milk teardrops
  progs/pinklady.md3               single-sided card + .skin files 0..15 (cull none + blendfunc blend + rgbGen identity)
  scripts/pinklady.shader          fullbright self-lit alpha-blended shaders (never darkened by map shadows)
  source/mm_tools/out/pinklady/    sheet.png & bounce_check.png & closeup_check.png for visual verification

python3.13 build_pinklady_assets.py [turntable.mp4] [bounce.mp4] [BakersfieldQuake dir]"""
import glob
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

DEFAULT_TURN = r"G:\Downloads\grok-video-8161e23b-9165-4fcf-b5e5-1272a194ba13.mp4"
DEFAULT_BOUNCE = r"G:\Downloads\grok-video-8161e23b-9165-4fcf-b5e5-1272a194ba13 (1).mp4"

VIDEO = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TURN
BOUNCE = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BOUNCE
MOD = sys.argv[3] if len(sys.argv) > 3 else r"G:\Quake\Combat\BakersfieldQuake"

HERE = os.path.dirname(os.path.abspath(__file__))
PROGS = os.path.join(MOD, "progs")
NAME = "pinklady"

N = 16                  # 16 turnaround views (22.5 deg per step)
STEP = 9                # 144 frames per full 360 turn
CANVAS = 512            # texture resolution
HALF = 10.0             # 20x20 unit card centered on origin, facing -X, picture-left = +Y
ROOM = 0.72             # vertical room on card so bounce & falling milk drops fit cleanly
FRONT_VIEWS = (15, 0, 1)

# 31 bounce keyframes -> 31 forward + 29 reverse = 60 ping-pong frames (safely <= Q3's 64-frame animmap cap!)
BOUNCE_KEYFRAMES = 31
BOUNCE_PLAY_FPS = 10
SIDE_DRIP_FRAMES = 6
SIDE_DRIP_FPS = 8


def load_selected_frames(path, frame_indices):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Could not open video: %s" % path)
    wanted = set(frame_indices)
    mx = max(wanted)
    grabbed = {}
    idx = 0
    while idx <= mx:
        ret, bgr = cap.read()
        if not ret:
            break
        if idx in wanted:
            grabbed[idx] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        idx += 1
    cap.release()
    return [grabbed[i] for i in frame_indices]


def keyout_clean(rgb_arr):
    """Segment Pink Lady cleanly from the pale grey/white studio backdrop, purge enclosed backdrop
    pockets (between fanned-out hair and shoulders or inside tie-knot ribbons) while protecting her
    face/smile/eyes, and decontaminate outer silhouette RGB so zero grey studio fringe remains."""
    h, w, _ = rgb_arr.shape
    pad = 16
    corner_col = np.median(
        np.vstack([rgb_arr[0:6, 0:6].reshape(-1, 3), rgb_arr[0:6, -6:].reshape(-1, 3)]),
        axis=0,
    ).astype(np.uint8)
    big = np.empty((h + 2 * pad, w + 2 * pad, 3), dtype=np.uint8)
    big[:, :] = corner_col
    big[pad:pad + h, pad:pad + w] = rgb_arr

    bf = big.astype(np.float32)
    hi = bf.max(axis=2)
    lo = bf.min(axis=2)
    chroma = hi - lo
    sat_hsv = np.where(hi > 1.0, (chroma / np.maximum(hi, 1.0)) * 255.0, 0.0)

    # Studio wall & pedestal floor are neutral pale grey/white (low chroma & unsaturated)
    cand_bg = ((sat_hsv < 39.0) & (lo > 125.0)) | ((chroma < 16.0) & (lo > 110.0))
    labeled, _ = ndimage.label(cand_bg)
    border_labels = (
        set(np.unique(labeled[0, :]))
        | set(np.unique(labeled[-1, :]))
        | set(np.unique(labeled[:, 0]))
        | set(np.unique(labeled[:, -1]))
    )
    border_labels.discard(0)
    bg = np.isin(labeled, list(border_labels))

    bg_crop = bg[pad:pad + h, pad:pad + w]
    rf = rgb_arr.astype(np.float32)
    r_hi = rf.max(axis=2)
    r_lo = rf.min(axis=2)
    r_ch = r_hi - r_lo
    r_sat = np.where(r_hi > 1.0, (r_ch / np.maximum(r_hi, 1.0)) * 255.0, 0.0)

    # Detect enclosed pale neutral studio pockets (under flying hair strands or inside pink knot loops)
    # Protect her head/face region (eyes & smile teeth) around center-upper frame.
    yy, xx = np.ogrid[:h, :w]
    in_face_guard = (
        (xx >= int(0.40 * w))
        & (xx <= int(0.60 * w))
        & (yy >= int(0.16 * h))
        & (yy <= int(0.39 * h))
    )
    pale_neutral = (~bg_crop) & (~in_face_guard) & (
        ((r_ch < 22.0) & (r_lo > 168.0))
        | ((r_sat < 30.0) & (r_lo > 178.0))
    )
    # Remove tiny 1-2px specular glints from pocket candidates so only real studio pockets (>= 14px) open up
    plbl, pn = ndimage.label(pale_neutral)
    if pn > 0:
        psizes = ndimage.sum(pale_neutral, plbl, range(1, pn + 1))
        pocket_ids = [i + 1 for i, sz in enumerate(psizes) if sz >= 14]
        if pocket_ids:
            pockets = ndimage.binary_dilation(np.isin(plbl, pocket_ids), iterations=1) & (r_sat < 44.0)
            bg_crop = bg_crop | pockets

    fg_raw = ~bg_crop
    # Clean tiny isolated background/foreground specks
    fg_raw = ndimage.binary_opening(fg_raw, structure=np.ones((3, 3)))
    fg_lbl, fg_n = ndimage.label(fg_raw)
    if fg_n > 1:
        fgsz = ndimage.sum(fg_raw, fg_lbl, range(1, fg_n + 1))
        keep_ids = [i + 1 for i, sz in enumerate(fgsz) if sz >= 80]
        fg_raw = np.isin(fg_lbl, keep_ids)

    dist_in = ndimage.distance_transform_edt(fg_raw)
    dist_out = ndimage.distance_transform_edt(~fg_raw)
    sdf = dist_in - dist_out

    # Smooth anti-aliased silhouette slightly inset (0.85px) so mixed studio border pixels vanish
    alpha = np.clip((sdf - 0.85 + 0.70) / 1.40, 0.0, 1.0)
    # Extra suppression of residual pale-grey fringe on outer 3.5px rim
    rim_whiteness = np.clip((r_lo - 165.0) / 45.0, 0.0, 1.0) * np.clip((38.0 - r_sat) / 28.0, 0.0, 1.0)
    alpha = np.where((dist_in < 3.8) & (~in_face_guard), alpha * (1.0 - 0.88 * rim_whiteness), alpha)

    # Interior foreground RGB rim decontamination (propagate clean interior colors outward across outer 5px)
    pale_rim_px = (dist_in <= 5.5) & ((r_sat < 42.0) & (r_lo > 135.0)) & (~in_face_guard)
    clean_seed = (dist_in > 3.6) & (~pale_rim_px) & fg_raw
    if not np.any(clean_seed):
        clean_seed = (dist_in > 1.5) & fg_raw
    if np.any(clean_seed):
        _, idx = ndimage.distance_transform_edt(~clean_seed, return_indices=True)
        nearest_rgb = rf[idx[0], idx[1]]
        rim_w = np.clip((dist_in - 1.6) / 3.0, 0.0, 1.0)
        rim_w = np.where(pale_rim_px, 0.0, rim_w)[..., None]
        rgb_clean = rf * rim_w + nearest_rgb * (1.0 - rim_w)
    else:
        rgb_clean = rf.copy()

    return beautify_pinklady(rgb_clean, alpha)


def beautify_pinklady(rgb_float, alpha_01):
    """Grade Pink Lady to be luminous, warm, vibrant, and crystal-clear in DarkPlaces full sRGB
    (vivid candy/hot-pink suit, radiant warm skin, bright golden-blonde hair, crisp facial contrast)."""
    x = np.clip(rgb_float / 255.0, 0.0, 1.0)

    # 1. Remove flat grey studio veil while lifting midtones brightly with soft highlight roll-off
    x = np.clip((x - 0.022) / 0.978, 0.0, 1.0)
    lifted = np.power(x, 0.82) * 1.12
    lifted = lifted / (1.0 + 0.13 * lifted * lifted)
    lifted = np.clip(lifted, 0.0, 1.0)

    r, g, b = lifted[..., 0], lifted[..., 1], lifted[..., 2]

    # 2. Selective hot-pink suit enhancement (rich vibrant rose-magenta instead of dull maroon)
    pink_amt = np.clip((r - g - 0.16) / 0.32, 0.0, 1.0) * np.clip((r - b + 0.10) / 0.25, 0.0, 1.0)
    # Boost pink brilliance & add subtle rosy-magenta richness + soft specular sheen on bright curves
    pink_sheen = pink_amt * np.clip((r - 0.68) / 0.28, 0.0, 1.0) ** 1.5
    r_p = np.clip(r * 1.10 + 0.05 * pink_amt + 0.08 * pink_sheen, 0.0, 1.0)
    g_p = np.clip(g * 0.86 + 0.11 * pink_sheen, 0.0, 1.0)
    b_p = np.clip(b * 1.14 + 0.07 * pink_amt + 0.10 * pink_sheen, 0.0, 1.0)

    r = r * (1.0 - pink_amt) + r_p * pink_amt
    g = g * (1.0 - pink_amt) + g_p * pink_amt
    b = b * (1.0 - pink_amt) + b_p * pink_amt

    # 3. Warm luminous skin & golden-blonde hair enhancement (eliminates washed-out grey cast)
    warm_amt = (1.0 - pink_amt) * np.clip((r - b) / 0.14, 0.0, 1.0)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    mean_c = (r + g + b) / 3.0
    # Gentle saturation boost + golden warmth on skin & hair
    r = mean_c + (r - mean_c) * (1.0 + 0.20 * warm_amt) + 0.028 * warm_amt
    g = mean_c + (g - mean_c) * (1.0 + 0.16 * warm_amt) + 0.010 * warm_amt
    b = mean_c + (b - mean_c) * (1.0 + 0.12 * warm_amt) - 0.014 * warm_amt

    # Keep dark eyelashes/smile/hair-roots crisp while keeping highlights silky
    shadow_protect = np.clip(lum / 0.25, 0.0, 1.0)
    out = np.dstack([r, g, b])
    out = np.clip(out * (0.94 + 0.06 * shadow_protect[..., None]), 0.0, 1.0)

    a_u8 = np.clip(np.round(alpha_01 * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(out * 255.0), 0, 255).astype(np.uint8)
    rgb_u8[a_u8 < 4] = 0
    a_u8[a_u8 < 4] = 0
    return np.dstack([rgb_u8, a_u8])


def resize_premul_rgba(rgba, new_w, new_h):
    """Premultiplied resize so silhouette edges never pick up dark or pale interpolation halos."""
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.dstack([f[..., :3] * a, f[..., 3:4]])
    interp = cv2.INTER_AREA if (new_w < rgba.shape[1]) else cv2.INTER_LANCZOS4
    pm_rs = cv2.resize(pm, (new_w, new_h), interpolation=interp)
    a_out = np.clip(pm_rs[..., 3], 0.0, 255.0)
    denom = np.maximum(a_out[..., None] / 255.0, 1e-4)
    rgb_out = np.clip(pm_rs[..., :3] / denom, 0.0, 255.0)
    a_u8 = np.round(a_out).astype(np.uint8)
    rgb_u8 = np.round(rgb_out).astype(np.uint8)
    rgb_u8[a_u8 < 4] = 0
    a_u8[a_u8 < 4] = 0
    return np.dstack([rgb_u8, a_u8])


def paste_on_canvas(canvas_rgba, patch_rgba, x0, y0):
    """Alpha-over paste with full bounds clipping."""
    H, W, _ = canvas_rgba.shape
    ph, pw, _ = patch_rgba.shape
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W, x0 + pw), min(H, y0 + ph)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    src = patch_rgba[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0].astype(np.float32)
    dst = canvas_rgba[cy0:cy1, cx0:cx1].astype(np.float32)
    sa = src[..., 3:4] / 255.0
    da = dst[..., 3:4] / 255.0
    oa = sa + da * (1.0 - sa)
    safe = np.maximum(oa, 1e-5)
    orgb = (src[..., :3] * sa + dst[..., :3] * da * (1.0 - sa)) / safe
    out = np.dstack([np.clip(np.round(orgb), 0, 255), np.clip(np.round(oa * 255.0), 0, 255)]).astype(np.uint8)
    canvas_rgba[cy0:cy1, cx0:cx1] = out


def paint_glossy_milk_drips(canvas_rgba, phase_01, seed_offset=0):
    """Composite organic, 3D-shaded pearlescent creamy-white milk glaze, curved rivulets, rim beads,
    and animated falling milk teardrops pooling naturally at the lowest gravity points of her pink pods
    and hanging tie-ribbon."""
    H, W, _ = canvas_rgba.shape
    rgb = canvas_rgba[..., :3].astype(np.float32)
    alpha = canvas_rgba[..., 3].astype(np.float32) / 255.0

    # Detect her hot-pink suit pixels on the 512x512 card
    pink = (alpha > 0.55) & ((rgb[..., 0] - rgb[..., 1]) > 55.0) & (rgb[..., 0] > 120.0)
    ys_all, xs_all = np.nonzero(pink)
    if len(xs_all) < 200:
        return canvas_rgba

    y_top_suit = int(np.percentile(ys_all, 15))
    y_bot_suit = int(ys_all.max())
    pod_y_min = int(y_top_suit + 0.36 * (y_bot_suit - y_top_suit))
    pod_mask = pink.copy()
    pod_mask[:pod_y_min, :] = False

    # Separate round globe mass from the narrow hanging tie-knot & ribbons using a 35px elliptical opening
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
    globe_mask = cv2.morphologyEx(pod_mask.astype(np.uint8), cv2.MORPH_OPEN, kern) > 0
    if int(globe_mask.sum()) < 200:
        kern2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))
        globe_mask = cv2.morphologyEx(pod_mask.astype(np.uint8), cv2.MORPH_OPEN, kern2) > 0
    if int(globe_mask.sum()) < 150:
        globe_mask = pod_mask

    col_has = np.any(globe_mask, axis=0)
    valid_xs = np.nonzero(col_has)[0]
    if len(valid_xs) < 24:
        return canvas_rgba

    x_left, x_right = int(valid_xs.min()), int(valid_xs.max())
    pod_w = float(x_right - x_left)
    cx_mid = 0.5 * (x_left + x_right)

    bot_y = np.zeros(W, dtype=np.float32)
    top_y = np.zeros(W, dtype=np.float32)
    col_thick = np.zeros(W, dtype=np.float32)
    for x in range(x_left, x_right + 1):
        ys = np.nonzero(globe_mask[:, x])[0]
        if len(ys):
            top_y[x] = float(ys[0])
            bot_y[x] = float(ys[-1])
            col_thick[x] = float(len(ys))

    # Fill any tiny interior empty columns before smoothing bottom contour
    raw_by = bot_y[x_left:x_right + 1].copy()
    nz = np.nonzero(raw_by > 0)[0]
    if len(nz) >= 2:
        raw_by = np.interp(np.arange(len(raw_by)), nz, raw_by[nz]).astype(np.float32)
    smooth_by = ndimage.gaussian_filter1d(raw_by, sigma=4.0, mode="nearest")
    bot_y[x_left:x_right + 1] = smooth_by

    milk_cov = np.zeros((H, W), dtype=np.float32)
    milk_h = np.zeros((H, W), dtype=np.float32)

    def stamp_capsule(x0, y0, x1, y1, r0, r1, strength=1.0, s0=None, clip_inside=False):
        pad_r = int(math.ceil(max(r0, r1) + 2.5))
        bx0 = max(0, int(math.floor(min(x0, x1))) - pad_r)
        bx1 = min(W, int(math.ceil(max(x0, x1))) + pad_r + 1)
        by0 = max(0, int(math.floor(min(y0, y1))) - pad_r)
        by1 = min(H, int(math.ceil(max(y0, y1))) + pad_r + 1)
        if bx0 >= bx1 or by0 >= by1:
            return
        gy, gx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
        dx, dy = x1 - x0, y1 - y0
        seg_l2 = dx * dx + dy * dy
        if seg_l2 < 1e-4:
            t = np.zeros_like(gx)
        else:
            t = np.clip(((gx - x0) * dx + (gy - y0) * dy) / seg_l2, 0.0, 1.0)
        px = x0 + t * dx
        py = y0 + t * dy
        rad = np.maximum(r0 + t * (r1 - r0), 0.35)
        st_cur = strength if s0 is None else (s0 + t * (strength - s0))
        dist = np.hypot(gx - px, gy - py)
        cov = np.clip((rad + 0.70 - dist) / 1.30, 0.0, 1.0) * st_cur
        if clip_inside:
            cov = cov * alpha[by0:by1, bx0:bx1]
        prof = np.sqrt(np.clip(1.0 - (dist / np.maximum(rad + 0.5, 0.5)) ** 2, 0.0, 1.0)) * st_cur
        if clip_inside:
            prof = prof * (alpha[by0:by1, bx0:bx1] > 0.25)
        milk_cov[by0:by1, bx0:bx1] = np.maximum(milk_cov[by0:by1, bx0:bx1], cov)
        milk_h[by0:by1, bx0:bx1] = np.maximum(milk_h[by0:by1, bx0:bx1], prof * np.clip(rad / 3.0, 0.45, 1.30))

    def stamp_teardrop(cx, cy, r_bulb, tail_len, strength=1.0, s_tail=None, clip_inside=False):
        s_top = (0.35 * strength) if s_tail is None else s_tail
        stamp_capsule(cx, cy - tail_len, cx, cy, max(0.50, r_bulb * 0.24), r_bulb, strength=strength, s0=s_top, clip_inside=clip_inside)

    # Distribute organic gravity drip anchors across the full breadth of BOTH globes (or the single profile belly)
    anchors = []  # (x_drip, y_drip, phase_off, scale_sz, curve_dx, is_ribbon)
    if pod_w >= 115.0:
        # Wide two-globe view (front, 3/4, rear): lush drips across left globe belly & right globe belly
        globe_specs = [
            (0.18, 0.11, 0.88, -2.2),
            (0.29, 0.47, 1.16, -0.8),
            (0.39, 0.79, 0.84, 1.2),
            (0.61, 0.26, 0.86, -1.2),
            (0.71, 0.63, 1.18, 0.8),
            (0.82, 0.91, 0.86, 2.2),
        ]
    else:
        # Side profile view: drips across the big round globe belly
        globe_specs = [
            (0.24, 0.16, 0.88, -1.6),
            (0.42, 0.54, 1.18, -0.5),
            (0.60, 0.83, 1.02, 0.7),
            (0.77, 0.35, 0.82, 1.8),
        ]

    for u_pos, ph0, sz, cdx in globe_specs:
        ax_c = max(x_left + 5, min(x_right - 5, int(round(x_left + u_pos * pod_w))))
        if col_thick[ax_c] >= 12:
            anchors.append((float(ax_c), float(bot_y[ax_c]), ph0, sz, cdx, False))

    # Also detect the hanging pink tie-ribbon tip(s) extending below the globes
    ribbon_only = pod_mask & (~globe_mask)
    ry_s, rx_s = np.nonzero(ribbon_only)
    if len(ry_s) >= 14 and int(ry_s.max()) > float(bot_y[int(round(cx_mid))]) + 6.0:
        idx_tip = int(np.argmax(ry_s))
        rtip_x, rtip_y = float(rx_s[idx_tip]), float(ry_s[idx_tip])
        rtop_y = max(float(np.percentile(ry_s, 25)), rtip_y - 20.0)
        stamp_capsule(rtip_x, rtop_y, rtip_x, rtip_y - 0.8, 0.85, 2.05, strength=0.92, s0=0.20, clip_inside=True)
        anchors.append((rtip_x, rtip_y, 0.04, 1.08, 0.0, True))

    # Paint soft scalloped rim glaze, dewy surface milk droplets, and animated gravity drips
    for idx_a, (ax, ay, ph0, sz, cdx, is_rib) in enumerate(anchors):
        ix = int(round(ax))
        span = max(16.0, ay - top_y[max(0, min(W - 1, ix))])
        cyc = (phase_01 + ph0 + 0.09 * seed_offset) % 1.0

        if not is_rib:
            # 1) Soft scalloped creamy meniscus hugging the round bottom rim around ax
            lobe_hw = max(6, int(round(9.0 * sz)))
            for dx_m in range(-lobe_hw, lobe_hw + 1, 2):
                xm = max(x_left + 3, min(x_right - 3, ix + dx_m))
                if col_thick[xm] > 8:
                    w_m = math.cos(0.5 * math.pi * (dx_m / float(lobe_hw + 1))) ** 1.5
                    ym = bot_y[xm] - 0.8
                    glaze_h = (2.2 + 4.2 * w_m) * sz
                    stamp_capsule(xm, ym - glaze_h, xm, ym, 1.1 + 1.1 * w_m, 1.6 + 1.8 * w_m, strength=0.88 * w_m, s0=0.12 * w_m, clip_inside=True)

            # 2) Short, softly tapered wet milk run feeding into the bottom bead (fades smoothly from thin glaze at top)
            run_h = min(span * (0.14 + 0.05 * (idx_a % 3)), 15.0) * sz
            stamp_capsule(ax + cdx, ay - run_h, ax, ay - 0.8, 0.65 * sz, 2.25 * sz, strength=0.94, s0=0.14, clip_inside=True)

            # 3) Occasional dewy milk droplet higher on the pink globe swell
            if idx_a % 2 == 1 and span > 45.0:
                bx = ax + cdx * 1.4 + (3.0 if (idx_a % 4 == 1) else -3.0)
                by = ay - run_h - (8.0 + 4.0 * (idx_a % 3)) + 3.5 * cyc
                stamp_teardrop(bx, by, 1.75 * sz, 4.8 * sz, strength=0.86, s_tail=0.12, clip_inside=True)

        # 4) Animated vertical gravity drip cycle hanging & falling below (ax, ay)!
        if cyc < 0.44:
            u = cyc / 0.44
            hang = (2.0 + 14.5 * (u ** 1.45)) * sz
            bulb_r = (2.10 + 1.25 * math.sin(u * math.pi * 0.85)) * sz
            neck_r = max(0.72, (1.60 - 0.65 * u) * sz)
            stamp_capsule(ax, ay - 1.2, ax, ay + hang, 1.80 * sz, neck_r, strength=0.96)
            stamp_teardrop(ax, ay + hang + bulb_r * 0.42, bulb_r, bulb_r * 1.45, strength=0.99, s_tail=0.75)
        else:
            u = (cyc - 0.44) / 0.56
            recoil_hang = (4.2 * (1.0 - min(1.0, u * 2.4)) + 1.6) * sz
            stamp_capsule(ax, ay - 1.2, ax, ay + recoil_hang, 1.85 * sz, 2.10 * sz, strength=0.95)

            fall_dist = (15.5 + 48.0 * (u ** 1.55)) * sz
            drop_fade = float(np.clip(1.0 - max(0.0, u - 0.58) / 0.42, 0.0, 1.0))
            if drop_fade > 0.04:
                bulb_r = (2.80 - 0.45 * u) * sz
                stamp_teardrop(ax, ay + fall_dist, bulb_r, (5.2 + 4.2 * u) * sz, strength=0.99 * drop_fade, s_tail=0.45 * drop_fade)
                if u > 0.12 and sz > 0.84:
                    sat_y = ay + fall_dist * 0.58
                    stamp_teardrop(ax, sat_y, 1.40 * sz, 2.4 * sz, strength=0.88 * drop_fade, s_tail=0.40 * drop_fade)

    if np.max(milk_cov) <= 1e-3:
        return canvas_rgba

    # 3D pearlescent liquid milk normal shading
    gx_h = cv2.Sobel(milk_h, cv2.CV_32F, 1, 0, ksize=3) * 0.35
    gy_h = cv2.Sobel(milk_h, cv2.CV_32F, 0, 1, ksize=3) * 0.35
    spec = np.clip(-0.55 * gx_h - 0.65 * gy_h + 0.38 * milk_h, 0.0, 1.0)
    glint = np.power(spec, 2.5)
    rim_shade = np.clip(milk_h * 1.25, 0.0, 1.0)

    mr = np.clip(238.0 + 13.0 * rim_shade + 16.0 * glint, 0.0, 255.0)
    mg = np.clip(241.0 + 11.0 * rim_shade + 14.0 * glint, 0.0, 255.0)
    mb = np.clip(236.0 + 13.0 * rim_shade + 18.0 * glint, 0.0, 255.0)
    milk_rgb = np.dstack([mr, mg, mb])

    shadow = np.clip(cv2.GaussianBlur(milk_cov, (5, 5), 1.2) * 0.14, 0.0, 0.14) * (1.0 - milk_cov * 0.85)
    shaded_base = rgb * (1.0 - shadow[..., None])

    ma = np.clip(milk_cov * 0.96, 0.0, 1.0)[..., None]
    ba = alpha[..., None]
    out_a = ma + ba * (1.0 - ma)
    safe_a = np.maximum(out_a, 1e-5)
    out_rgb = (milk_rgb * ma + shaded_base * ba * (1.0 - ma)) / safe_a

    a_u8 = np.clip(np.round(out_a[..., 0] * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(out_rgb), 0, 255).astype(np.uint8)
    rgb_u8[a_u8 < 4] = 0
    a_u8[a_u8 < 4] = 0
    return np.dstack([rgb_u8, a_u8])


def alpha_bbox(rgba):
    ys, xs = np.nonzero(rgba[..., 3] >= 32)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def mass_stats(rgba):
    m = (rgba[..., 3] >= 128).astype(np.float64)
    area = float(m.sum())
    ys, xs = np.nonzero(m > 0)
    return area, float(xs.mean()), float(ys.mean())


def build_turnaround_cuts():
    # Frame 144 for view 0 (matching studio floor/lighting), then frames 9, 18 .. 135
    indices = [144] + [k * STEP for k in range(1, N)]
    raw_frames = load_selected_frames(VIDEO, indices)
    return [keyout_clean(fr) for fr in raw_frames]


def build_bounce_cuts():
    # Frames 24..72 (1.00s..3.00s at 24fps): 3 full crisp front-facing bounces with hands cleanly inside frame!
    indices = [int(round(x)) for x in np.linspace(24, 72, BOUNCE_KEYFRAMES)]
    raw_frames = load_selected_frames(BOUNCE, indices)
    return [keyout_clean(fr) for fr in raw_frames]


def write_turnaround_textures(cuts):
    for old in glob.glob(os.path.join(PROGS, "%s_v*_d*.png" % NAME)):
        os.remove(old)

    boxes = [alpha_bbox(c) for c in cuts]
    top = max(b[3] - b[1] for b in boxes)
    wide = max(b[2] - b[0] for b in boxes)
    scale = (CANVAS - 16) * ROOM / float(max(top, wide))
    cx = sum((b[0] + b[2]) / 2.0 for b in boxes) / float(len(boxes))
    cy = sum((b[1] + b[3]) / 2.0 for b in boxes) / float(len(boxes))

    sheet = Image.new("RGBA", (N * 160, 160), (46, 48, 54, 255))
    base_canvases = []

    for i, c in enumerate(cuts):
        h, w, _ = c.shape
        rs = resize_premul_rgba(c, round(w * scale), round(h * scale))
        canvas = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
        paste_on_canvas(canvas, rs, round(CANVAS / 2 - cx * scale), round(CANVAS / 2 - cy * scale))
        base_canvases.append(canvas)

        # Base snapshot progs/pinklady_00..15.png (with glossy milk drips)
        snap = paint_glossy_milk_drips(canvas, phase_01=0.18, seed_offset=i)
        Image.fromarray(snap, "RGBA").save(os.path.join(PROGS, "%s_%02d.png" % (NAME, i)))

        # Side & rear views (2..14): 6-frame continuous downward milk-drip loop!
        if i not in FRONT_VIEWS:
            for d in range(SIDE_DRIP_FRAMES):
                dripped = paint_glossy_milk_drips(canvas, phase_01=d / float(SIDE_DRIP_FRAMES), seed_offset=i)
                Image.fromarray(dripped, "RGBA").save(
                    os.path.join(PROGS, "%s_v%02d_d%d.png" % (NAME, i, d))
                )

        small = Image.fromarray(snap, "RGBA").resize((160, 160), Image.LANCZOS)
        sheet.paste(small, (i * 160, 0), small)

    out_dir = os.path.join(HERE, "out", NAME)
    os.makedirs(out_dir, exist_ok=True)
    sheet.save(os.path.join(out_dir, "sheet.png"))
    return scale, cx, cy, base_canvases[0]


def write_bounce_textures(bcuts, front_cut, scale):
    for old in glob.glob(os.path.join(PROGS, NAME + "_b*.png")):
        os.remove(old)

    fb = alpha_bbox(front_cut)
    boxes = [alpha_bbox(c) for c in bcuts]
    k = (fb[3] - fb[1]) / (sum(b[3] - b[1] for b in boxes) / float(len(boxes)))
    bx = sum((b[0] + b[2]) / 2.0 for b in boxes) / float(len(boxes))
    by = sum((b[1] + b[3]) / 2.0 for b in boxes) / float(len(boxes))
    s = scale * k
    fit = min((CANVAS / 2 - 8) / (s * max(max(bx - b[0], b[2] - bx, by - b[1], b[3] - by) for b in boxes)), 1.0)
    s = s * fit * 0.97

    stats = [mass_stats(c) for c in bcuts]
    mean_area = sum(a for a, _, _ in stats) / float(len(stats))
    mean_cy = sum(y for _, _, y in stats) / float(len(stats))

    # Pre-position the 31 clean bounce frames on 512x512 cards
    key_cards = []
    for i, c in enumerate(bcuts):
        area, mx, my = stats[i]
        si = s * (mean_area / area) ** 0.5
        h, w, _ = c.shape
        rs = resize_premul_rgba(c, round(w * si), round(h * si))
        canvas = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
        bob = 0.5 * (my - mean_cy) * si
        paste_on_canvas(canvas, rs, round(CANVAS / 2 - mx * si), round(CANVAS / 2 - my * si + bob))
        key_cards.append(canvas)

    # Ping-pong body bounce (0..30 then 29..1 = 60 frames <= Q3 64-frame animmap cap),
    # while milk drips advance monotonically 0 -> 1 (3 full drip cycles) so milk ALWAYS drips downward!
    ping = list(range(len(key_cards))) + list(range(len(key_cards) - 2, 0, -1))
    assert len(ping) <= 64, "animmap frame count %d exceeds Q3 64-frame limit" % len(ping)

    out_frames = []
    for f_idx, src_k in enumerate(ping):
        drip_phase = (3.0 * f_idx / float(len(ping))) % 1.0
        dripped = paint_glossy_milk_drips(key_cards[src_k], phase_01=drip_phase, seed_offset=0)
        Image.fromarray(dripped, "RGBA").save(os.path.join(PROGS, "%s_b%02d.png" % (NAME, f_idx)))
        out_frames.append(dripped)

    # Save visual check strips
    out_dir = os.path.join(HERE, "out", NAME)
    picks = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    strip = Image.new("RGBA", (len(picks) * 160, 160), (46, 48, 54, 255))
    for j, fi in enumerate(picks):
        sm = Image.fromarray(out_frames[fi], "RGBA").resize((160, 160), Image.LANCZOS)
        strip.paste(sm, (j * 160, 0), sm)
    strip.save(os.path.join(out_dir, "bounce_check.png"))

    # Full-res 512x512 closeup strip (front bounce + 3/4 + side + back) on dark & mid-tone checkerboard
    close_cards = [
        out_frames[4],
        out_frames[18],
        Image.open(os.path.join(PROGS, "%s_v02_d2.png" % NAME)).convert("RGBA"),
        Image.open(os.path.join(PROGS, "%s_v04_d3.png" % NAME)).convert("RGBA"),
        Image.open(os.path.join(PROGS, "%s_v08_d4.png" % NAME)).convert("RGBA"),
    ]
    close_im = Image.new("RGBA", (len(close_cards) * CANVAS, CANVAS), (38, 40, 46, 255))
    for j, cc in enumerate(close_cards):
        im_c = cc if isinstance(cc, Image.Image) else Image.fromarray(cc, "RGBA")
        close_im.paste(im_c, (j * CANVAS, 0), im_c)
    close_im.save(os.path.join(out_dir, "closeup_check.png"))

    print("bounce: %d keyframes -> %d loop frames (<=64 cap), scale %.3f" % (len(key_cards), len(ping), s / scale))
    return len(ping)


def write_shaders(n_loop):
    os.makedirs(os.path.join(MOD, "scripts"), exist_ok=True)
    with open(os.path.join(MOD, "scripts", NAME + ".shader"), "w", newline="\n") as f:
        f.write("// written by mm_tools/build_pinklady_assets.py\n")
        for k in range(N):
            if k in FRONT_VIEWS and k != 0:
                continue
            if k == 0:
                frames_str = " ".join("progs/%s_b%02d" % (NAME, i) for i in range(n_loop))
                f.write(
                    "progs/%s_v%02d\n{\n\tcull none\n\tnopicmip\n\t{\n\t\tanimmap %d %s\n\t\tblendfunc blend\n\t\trgbGen identity\n\t}\n}\n"
                    % (NAME, k, BOUNCE_PLAY_FPS, frames_str)
                )
            else:
                frames_str = " ".join("progs/%s_v%02d_d%d" % (NAME, k, d) for d in range(SIDE_DRIP_FRAMES))
                f.write(
                    "progs/%s_v%02d\n{\n\tcull none\n\tnopicmip\n\t{\n\t\tanimmap %d %s\n\t\tblendfunc blend\n\t\trgbGen identity\n\t}\n}\n"
                    % (NAME, k, SIDE_DRIP_FPS, frames_str)
                )


def write_model():
    """Single-sided card with `cull none` in shader so `blendfunc blend` never double-draws backfaces."""
    card = [(0.0, HALF, -HALF), (0.0, HALF, HALF), (0.0, -HALF, HALF), (0.0, -HALF, -HALF)]
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    surf = dict(name="card", shader="progs/%s_v00" % NAME, tris=tris, st=st, frames=[(card, [(-1.0, 0.0, 0.0)] * 4)])
    md3lib.write(os.path.join(PROGS, NAME + ".md3"), dict(name=NAME, surfaces=[surf], nframes=1))
    for old in glob.glob(os.path.join(PROGS, NAME + "*.skin")):
        os.remove(old)
    for k in range(N):
        shader = "progs/%s_v%02d" % (NAME, 0 if k in FRONT_VIEWS else k)
        with open(os.path.join(PROGS, "%s.md3_%d.skin" % (NAME, k)), "w", newline="\n") as sk:
            sk.write("card,%s\n" % shader)


def main():
    os.makedirs(PROGS, exist_ok=True)
    cuts = build_turnaround_cuts()
    scale, cx, cy, _ = write_turnaround_textures(cuts)
    n_loop = write_bounce_textures(build_bounce_cuts(), cuts[0], scale)
    write_shaders(n_loop)
    write_model()
    print(
        "wrote progs/%s.md3 (%d views, %d-frame front bounce + %d-frame side drips), scripts/%s.shader"
        % (NAME, N, n_loop, SIDE_DRIP_FRAMES, NAME)
    )


if __name__ == "__main__":
    main()
