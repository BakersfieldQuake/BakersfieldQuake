"""Concept 4: "THE PORCELAIN POOP-TUBA" (Toilet Mortar & Strangelove Torpedo).

Generates all sprites, contact sheets, and `manifest.json` under `work/c4_tuba/`:
- First-person viewmodel (`420x360`):
    - `vm_idle_00..59.png` (60 frames, 60 FPS seamless loop)
    - `vm_fire_00..19.png` (20 frames: flush chain yank, guy ducks, tuba-fart shockwave & mud geyser)
    - `vm_reload_00..17.png` (18 frames: flush swirl, wheel turbo-spin, guy bounces back up)
- Projectile (`220x220`, 16 angles x 6 frames = 96 frames):
    - `proj_a00_f00.png` .. `proj_a15_f05.png`: Dr. Strangelove-style fat bloke cowboy-riding
      the `poop_torpedo` across 16 yaw/pitch angles with sputtering fuse sparks, mud exhaust,
      and chasing flies!
- 3rd-person shooter (`320x360`):
    - `tp_idle_00..15.png` (16 frames)
    - `tp_fire_00..11.png` (12 frames: enemy firing the Poop-Tuba + Strangelove rider at viewer)
    - `tp_reload_00..11.png` (12 frames)
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

BRAIN_DIR = r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841"
TUBA_PLATE_PATH = os.path.join(BRAIN_DIR, "tuba_mortar_c3_1794663367370.jpg")
TORPEDO_PLATE_PATH = os.path.join(BRAIN_DIR, "poop_torpedo_1794663387920.jpg")
ENEMY_PLATE_PATH = os.path.join(BRAIN_DIR, "enemy_shooter_base_1794663595737.jpg")
TURBAN_YELL_PATH = os.path.join(BRAIN_DIR, "head_turban_yell_1794663574913.jpg")

OUT_DIR = os.path.join(WORK_DIR, "c4_tuba")
VM_WH = (420, 360)
PROJ_WH = (220, 220)
TP_WH = (320, 360)

# Padding around the 1024x1024 tuba_mortar plate so tall flags & cranking guy have headroom
# 1428 / 1224 == 420 / 360 (exact 7:6 aspect ratio)
PAD_L, PAD_T, PAD_R, PAD_B = 140, 200, 264, 0
PADDED_WH = (1024 + PAD_L + PAD_R, 1024 + PAD_T + PAD_B)  # (1428, 1224)


def _pad_xy(x: float, y: float) -> Tuple[float, float]:
    return x + PAD_L, y + PAD_T


def _load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def _save_rgba(rgba: np.ndarray, path: str) -> None:
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def _key_studio_grey_tuba(rgb: np.ndarray) -> np.ndarray:
    """Edge-barrier studio keying tailored to `tuba_mortar_c3_1794663367370.jpg`,
    which has a neutral gray studio backdrop (~210-235) matching porcelain brightness.
    """
    h, w = rgb.shape[:2]
    arr = rgb.astype(np.float32)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.hypot(gx, gy) / 4.0

    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    bg_cand = (sat < 0.048) & (lum > 145.0) & (grad < 3.0)
    lbl, _ = ndimage.label(bg_cand)
    border_ids = (
        set(np.unique(lbl[0, :]))
        | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0]))
        | set(np.unique(lbl[:, -1]))
    )
    border_ids.discard(0)
    bg0 = np.isin(lbl, list(border_ids))

    # Enclosed background pockets inside the brass tubing loops & navy wheel spokes
    enclosed = (sat < 0.05) & (lum > 180.0) & (grad < 5.0) & (~bg0)
    elbl, en = ndimage.label(enclosed)
    pocket_mask = np.zeros_like(bg0)
    pocket_mask[570:705, 380:528] = True
    pocket_mask[235:400, 795:940] = True
    for i in range(1, en + 1):
        comp = elbl == i
        if 30 <= int(comp.sum()) <= 5000 and np.all(pocket_mask[comp]):
            bg0 |= comp

    fg = ~bg0
    fg_closed = ndimage.binary_fill_holes(fg)
    fg = np.where(pocket_mask & bg0, False, fg_closed)

    # Keep main body (>1500 px) plus thin chain/handle links in x=845..900, y=340..710
    chain_zone = np.zeros_like(fg)
    chain_zone[340:710, 845:900] = True
    fg_lbl, fn = ndimage.label(fg)
    sizes = ndimage.sum(fg, fg_lbl, range(1, fn + 1))
    keep = np.zeros_like(fg)
    for i, s in enumerate(sizes, 1):
        comp = fg_lbl == i
        if s > 1500 or (s > 35 and np.any(comp & chain_zone)):
            keep |= comp
    fg = keep

    # Clean bottom-left table shadow sliver under left gauntlet (x=345..470, y=895..985)
    bot_left_shadow = (sat < 0.055) & (lum > 140.0)
    sh_mask = np.zeros_like(fg)
    sh_mask[895:985, 345:470] = bot_left_shadow[895:985, 345:470]
    fg &= ~sh_mask

    dist_in = ndimage.distance_transform_edt(fg)
    dist_out = ndimage.distance_transform_edt(~fg)
    sdf = dist_in - dist_out
    alpha = np.clip((sdf - 0.15) / 1.25, 0.0, 1.0)

    rgb_clean = arr.copy()
    semi = (alpha > 0.04) & (alpha < 0.96)
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.2)
    rgb_clean[semi] = np.clip((arr[semi] - inv[:, None] * 225.0) / denom[:, None], 0.0, 255.0)

    # Decontaminate 2px outer rim from neutral studio gray
    seed = fg & (dist_in > 2.5)
    if np.any(seed):
        _, idx = ndimage.distance_transform_edt(~seed, return_indices=True)
        nearest = rgb_clean[idx[0], idx[1]]
        w_rim = np.clip((dist_in - 0.6) / 1.9, 0.0, 1.0)[..., None]
        rgb_clean = rgb_clean * w_rim + nearest * (1.0 - w_rim)

    a_u8 = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8)
    rgb_u8[a_u8 < 6] = 0
    a_u8[a_u8 < 6] = 0
    return np.dstack([rgb_u8, a_u8])


def _clean_trapped_arm_gap(rgba: np.ndarray) -> np.ndarray:
    """Remove small trapped pure-white background triangles between arms and shorts in turn_16."""
    out = rgba.copy()
    h, w = out.shape[:2]
    arr = out[..., :3].astype(np.float32)
    lo = arr.min(axis=2)
    hi = arr.max(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    # Near-white pixels inside the shorts-band protect_box outside central ashoka chakra
    white_cand = (out[..., 3] > 20) & (lo > 232.0) & (sat < 0.06)
    yy, xx = np.mgrid[0:h, 0:w]
    # Keep central horizontal shorts band (middle 38% of width); punch only outer edge wedges
    inner_shorts = (np.abs(xx - w * 0.5) < w * 0.14) & (yy > h * 0.45) & (yy < h * 0.72)
    edge_white = white_cand & (~inner_shorts)
    lbl, n = ndimage.label(edge_white)
    if n > 0:
        for i in range(1, n + 1):
            comp = lbl == i
            # Only remove wedges touching the outer transparent boundary of the sprite
            dil = ndimage.binary_dilation(out[..., 3] == 0, iterations=2)
            if np.any(comp & dil) and int(comp.sum()) < 2200:
                out[comp] = 0
    return out


def _load_assets() -> Dict[str, object]:
    """Load cached heads, FX sprites, turnaround, dance frames, and key any missing plates."""
    heads: Dict[str, np.ndarray] = {}
    for hp in sorted(glob.glob(os.path.join(WORK_DIR, "heads", "*.png"))):
        name = os.path.splitext(os.path.basename(hp))[0]
        heads[name] = _load_rgba(hp)

    if "head_turban_yell" not in heads and os.path.exists(TURBAN_YELL_PATH):
        rgb = np.asarray(Image.open(TURBAN_YELL_PATH).convert("RGB"))
        h, w = rgb.shape[:2]
        rgba = key_white_studio_plate(rgb, protect_box=(int(w * 0.20), int(h * 0.12), int(w * 0.80), int(h * 0.88)))
        ys, xs = np.nonzero(rgba[..., 3] > 16)
        crop = rgba[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
        sc = min(240 / crop.shape[1], 240 / crop.shape[0])
        rs = resize_premul(crop, (max(4, int(round(crop.shape[1] * sc))), max(4, int(round(crop.shape[0] * sc)))))
        canv = np.zeros((256, 256, 4), dtype=np.uint8)
        ox, oy = (256 - rs.shape[1]) // 2, (256 - rs.shape[0]) // 2
        canv[oy:oy + rs.shape[0], ox:ox + rs.shape[1]] = rs
        heads["head_turban_yell"] = canv

    fx_dir = os.path.join(WORK_DIR, "fx")
    mud_globs = [_load_rgba(p) for p in sorted(glob.glob(os.path.join(fx_dir, "mud_glob_*.png")))]
    splats = [_load_rgba(p) for p in sorted(glob.glob(os.path.join(fx_dir, "splat_*.png")))]
    mists = [_load_rgba(p) for p in sorted(glob.glob(os.path.join(fx_dir, "mist_*.png")))]

    enemy_path = os.path.join(fx_dir, "enemy_shooter_base.png")
    if os.path.exists(enemy_path):
        enemy_rgba = _load_rgba(enemy_path)
    else:
        eraw = np.asarray(Image.open(ENEMY_PLATE_PATH).convert("RGB"))
        eh, ew = eraw.shape[:2]
        enemy_rgba = key_white_studio_plate(eraw, protect_box=(int(ew * 0.22), int(eh * 0.08), int(ew * 0.78), int(eh * 0.90)))

    turn_16 = [_clean_trapped_arm_gap(_load_rgba(p)) for p in sorted(glob.glob(os.path.join(WORK_DIR, "turn_16", "turn_*.png")))]
    dance_48 = [_load_rgba(p) for p in sorted(glob.glob(os.path.join(WORK_DIR, "dance_48", "dance_*.png")))]

    tuba_rgb = np.asarray(Image.open(TUBA_PLATE_PATH).convert("RGB"))
    tuba_rgba = _key_studio_grey_tuba(tuba_rgb)

    torpedo_rgb = np.asarray(Image.open(TORPEDO_PLATE_PATH).convert("RGB"))
    torpedo_rgba = key_white_studio_plate(torpedo_rgb, protect_box=(40, 310, 860, 690))

    return {
        "heads": heads,
        "mud_globs": mud_globs,
        "splats": splats,
        "mists": mists,
        "enemy": enemy_rgba,
        "turn_16": turn_16,
        "dance_48": dance_48,
        "tuba": tuba_rgba,
        "torpedo": torpedo_rgba,
    }


def _decompose_tuba(tuba_rgba: np.ndarray) -> Dict[str, object]:
    """Split keyed `tuba_mortar` into back body, front seat lip, spinning navy wheel,
    pullable flush chain/handle, and bowl interior geometry.
    """
    h, w = tuba_rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # 1. Isolate Navy Crank Wheel centered at (872, 315), radius ~79
    wx, wy, wr = 872.0, 315.0, 79.0
    r_wheel = np.hypot(xx - wx, yy - wy)
    arr = tuba_rgba[..., :3].astype(np.float32)
    # Navy wheel is strongly blue-dark compared to white porcelain tank & silver chain
    is_navy = (arr[..., 2] > arr[..., 0] + 12.0) & (arr[..., 2] > arr[..., 1] + 6.0) & (arr[..., 0] < 115.0)
    wheel_mask = (r_wheel < wr) & (tuba_rgba[..., 3] > 20) & (is_navy | (r_wheel < 18.0))
    # Exclude the grey chain crossing vertically at x=870..883 below the hub (y > 332)
    chain_cut = (xx >= 868.0) & (xx <= 885.0) & (yy > 330.0) & (~is_navy)
    wheel_mask &= ~chain_cut
    wheel_mask = ndimage.binary_closing(wheel_mask, iterations=1)

    wheel_crop_sz = 180
    x0, y0 = int(wx - wheel_crop_sz // 2), int(wy - wheel_crop_sz // 2)
    wheel_patch = np.zeros((wheel_crop_sz, wheel_crop_sz, 4), dtype=np.uint8)
    wm_sub = wheel_mask[y0:y0 + wheel_crop_sz, x0:x0 + wheel_crop_sz]
    wheel_patch[wm_sub] = tuba_rgba[y0:y0 + wheel_crop_sz, x0:x0 + wheel_crop_sz][wm_sub]
    # Clean wheel center hub with dark navy bolt
    cv2.circle(wheel_patch, (wheel_crop_sz // 2, wheel_crop_sz // 2), 9, (34, 50, 88, 255), -1, cv2.LINE_AA)

    # 2. Isolate Flush Chain & Porcelain Handle (x=850..892, y=335..700)
    chain_mask = np.zeros((h, w), dtype=bool)
    chain_mask[335:700, 850:894] = (tuba_rgba[335:700, 850:894, 3] > 20) & (~wheel_mask[335:700, 850:894])
    # Extract chain patch anchored at top (x=845..898, y=332..702)
    chain_box = (845, 332, 898, 702)
    cx0, cy0, cx1, cy1 = chain_box
    chain_patch = np.zeros((cy1 - cy0, cx1 - cx0, 4), dtype=np.uint8)
    cm_sub = chain_mask[cy0:cy1, cx0:cx1]
    chain_patch[cm_sub] = tuba_rgba[cy0:cy1, cx0:cx1][cm_sub]
    # Remove any bright studio-gray strip trapped along the chain links (above handle y < 622)
    cp_arr = chain_patch[..., :3].astype(np.float32)
    cp_lum = 0.299 * cp_arr[..., 0] + 0.587 * cp_arr[..., 1] + 0.114 * cp_arr[..., 2]
    cp_sat = (cp_arr.max(axis=2) - cp_arr.min(axis=2)) / np.maximum(cp_arr.max(axis=2), 1.0)
    link_rows = np.arange(cy1 - cy0)[:, None] < (622 - cy0)
    studio_strip = link_rows & (cp_lum > 188.0) & (cp_sat < 0.05)
    chain_patch[studio_strip] = 0

    # 3. Clean base body (remove wheel & chain completely; only inpaint tank behind wheel)
    base = tuba_rgba.copy()
    tank_bg = (xx < 845.0) & (yy > 180.0) & (yy < 430.0) & (xx < 818.0 + (yy - 180.0) * 0.08)
    wheel_in_tank = (wheel_mask & tank_bg).astype(np.uint8) * 255
    inpaint_rgb = cv2.inpaint(base[..., :3], wheel_in_tank, 5, cv2.INPAINT_TELEA)
    base[wheel_mask & tank_bg, :3] = inpaint_rgb[wheel_mask & tank_bg]
    # Completely erase wheel outside tank AND completely erase the hanging chain/handle + any halo
    chain_clear = (yy >= 396.0) & (yy <= 715.0) & (xx >= 850.0) & (xx <= 915.0)
    erase_mask = (wheel_mask & (~tank_bg)) | chain_mask | chain_clear
    base[erase_mask] = 0

    # 4. Bowl Cavity Mask (strictly inside the white porcelain inner seat lip!)
    # Open hole center (600, 304), rx=49, ry=134, angle=-5 deg so bottom/left seat rim overlaps sludge!
    ang = math.radians(-5.0)
    ca, sa = math.cos(ang), math.sin(ang)
    dx = xx - 600.0
    dy = yy - 304.0
    rx_rot = dx * ca + dy * sa
    ry_rot = -dx * sa + dy * ca
    bowl_ell = (rx_rot / 49.0) ** 2 + (ry_rot / 134.0) ** 2

    bowl_inner_mask = bowl_ell < 0.96
    front_lip_mask = (~bowl_inner_mask) & (base[..., 3] > 20)

    return {
        "base": base,
        "wheel_patch": wheel_patch,
        "wheel_center": (wx, wy),
        "chain_patch": chain_patch,
        "chain_pos": (cx0, cy0),
        "bowl_inner_mask": bowl_inner_mask,
        "front_lip_mask": front_lip_mask,
        "gauge_center": (688.0, 578.0),
        "bell_center": (308.0, 428.0),
    }


def _draw_brass_pole(canvas: np.ndarray, p0: Tuple[float, float], p1: Tuple[float, float], thick: int = 8) -> np.ndarray:
    """Draw a gleaming shaded brass flagpole with finial sphere at p1."""
    out = canvas.copy()
    x0, y0 = int(round(p0[0])), int(round(p0[1]))
    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    cv2.line(out, (x0, y0), (x1, y1), (78, 56, 20, 255), thick + 2, cv2.LINE_AA)
    cv2.line(out, (x0, y0), (x1, y1), (188, 154, 68, 255), thick, cv2.LINE_AA)
    cv2.line(out, (x0 - 1, y0), (x1 - 1, y1), (240, 214, 128, 255), max(2, thick // 3), cv2.LINE_AA)
    cv2.circle(out, (x1, y1), thick, (168, 134, 52, 255), -1, cv2.LINE_AA)
    cv2.circle(out, (x1 - 2, y1 - 2), max(2, thick // 2), (248, 226, 150, 255), -1, cv2.LINE_AA)
    return out


def _render_sludge_and_bubbles(
    w: int, h: int, bowl_mask: np.ndarray, t_norm: float, flush_swirl: float = 0.0
) -> np.ndarray:
    """Render churning bubbling brown poop-sludge inside the toilet bowl cavity."""
    sludge = np.zeros((h, w, 4), dtype=np.uint8)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    tau = 2.0 * math.pi
    bx0, by0 = _pad_xy(600.0, 352.0)
    # Surface wave line across the bowl
    wave = (
        6.5 * np.sin((xx - bx0) * 0.08 + tau * t_norm * 2.0)
        + 4.0 * np.cos((xx - bx0) * 0.15 - tau * t_norm * 3.0)
    )
    surf_y = by0 + wave + flush_swirl * 38.0
    in_mud = bowl_mask & (yy >= surf_y)
    if not np.any(in_mud):
        return sludge

    depth = np.clip((yy - surf_y) / 140.0, 0.0, 1.0)
    swirl_n = np.sin((xx - bx0) * 0.09 + (yy - by0) * 0.07 + tau * t_norm * 2.0) * 0.5 + 0.5
    r = 98.0 * (1.0 - 0.35 * depth) + 28.0 * swirl_n
    g = 60.0 * (1.0 - 0.42 * depth) + 18.0 * swirl_n
    b = 24.0 * (1.0 - 0.48 * depth) + 8.0 * swirl_n
    # Bright glossy mud meniscus along top surface
    meniscus = np.exp(-((yy - surf_y) / 5.5) ** 2)
    r += 48.0 * meniscus
    g += 36.0 * meniscus
    b += 16.0 * meniscus

    sludge[in_mud, 0] = np.clip(r[in_mud], 0, 255).astype(np.uint8)
    sludge[in_mud, 1] = np.clip(g[in_mud], 0, 255).astype(np.uint8)
    sludge[in_mud, 2] = np.clip(b[in_mud], 0, 255).astype(np.uint8)
    sludge[in_mud, 3] = 245

    # Draw popping glossy mud bubbles inside the bowl surface
    b_layer = np.zeros((h, w, 4), dtype=np.uint8)
    for i in range(9):
        phase = (t_norm * (1.0 + (i % 2)) + i * 0.137) % 1.0
        ox = bx0 + math.sin(i * 2.3 + phase * 3.0) * 44.0
        oy = by0 + 18.0 + (i % 5) * 20.0 - phase * 18.0
        rad = int(round(4.0 + 7.5 * math.sin(phase * math.pi)))
        if rad > 2 and 0 <= int(oy) < h and 0 <= int(ox) < w and bowl_mask[int(oy), int(ox)]:
            cv2.circle(b_layer, (int(ox), int(oy)), rad, (132, 86, 38, 235), -1, cv2.LINE_AA)
            cv2.circle(b_layer, (int(ox), int(oy)), rad, (54, 30, 12, 235), 2, cv2.LINE_AA)
            cv2.circle(b_layer, (int(ox - rad * 0.3), int(oy - rad * 0.3)), max(1, rad // 3), (225, 200, 145, 220), -1, cv2.LINE_AA)
    return alpha_over(sludge, b_layer, 0, 0)


def _draw_stink_fumes(canvas: np.ndarray, origin: Tuple[float, float], t_norm: float, strength: float = 1.0) -> np.ndarray:
    """Draw rising wavy green-brown cartoon stink fume tendrils."""
    out = canvas.copy()
    h, w = out.shape[:2]
    fume = np.zeros((h, w, 4), dtype=np.uint8)
    ox, oy = origin
    tau = 2.0 * math.pi
    for k in range(3):
        pts = []
        x_off = (k - 1) * 28.0
        for s in range(16):
            u = s / 15.0
            px = ox + x_off + math.sin(u * 5.0 - tau * t_norm * 2.0 + k * 2.1) * (12.0 + 10.0 * u)
            py = oy - u * 125.0 * strength
            pts.append((int(round(px)), int(round(py))))
        for s in range(len(pts) - 1):
            u = s / float(len(pts) - 1)
            alpha_l = int(round(135 * strength * math.sin(u * math.pi)))
            col = (128, 154, 56, alpha_l) if k % 2 == 0 else (142, 118, 48, alpha_l)
            cv2.line(fume, pts[s], pts[s + 1], col, max(2, int(round(8 * (1.0 - 0.5 * u)))), cv2.LINE_AA)
    fume = cv2.GaussianBlur(fume, (7, 7), 1.8)
    return alpha_over(out, fume, 0, 0)


def _draw_brass_valve_jack(
    canvas: np.ndarray,
    head_rgba: np.ndarray,
    base_xy: Tuple[float, float],
    valve_angle_deg: float,
    pop_t: float,
    head_tilt_deg: float,
    flip_head: bool = False,
) -> np.ndarray:
    """Draw a brass side-valve cylinder with coiled spring, hinged lid, and a smaller
    yelling/arguing head popping in & out like a jack-in-the-box!
    """
    bx, by = base_xy
    pw, ph = 240, 260
    patch = np.zeros((ph, pw, 4), dtype=np.uint8)
    cx, cy = pw // 2, ph - 52  # valve mouth center inside local patch

    # 1. Brass coiled spring extending up with pop_t in [0..1]
    ext = 12.0 + 58.0 * pop_t
    if ext > 14.0:
        n_coils = 5
        pts = []
        for i in range(n_coils * 2 + 1):
            u = i / float(n_coils * 2)
            sx = cx + (14 if i % 2 == 0 else -14) * (0.45 if i in (0, n_coils * 2) else 1.0)
            sy = cy - u * ext
            pts.append((int(round(sx)), int(round(sy))))
        for i in range(len(pts) - 1):
            cv2.line(patch, pts[i], pts[i + 1], (90, 70, 25, 255), 6, cv2.LINE_AA)
            cv2.line(patch, pts[i], pts[i + 1], (218, 184, 88, 255), 3, cv2.LINE_AA)

    # 2. Pop-up yelling/arguing head at top of spring
    h_im = head_rgba
    if flip_head:
        h_im = np.fliplr(h_im).copy()
    # Scale smaller (~108px) so two heads fit hilariously in the side-valves
    h_sc = 112.0 / float(h_im.shape[0])
    hw = max(8, int(round(h_im.shape[1] * h_sc)))
    hh = max(8, int(round(h_im.shape[0] * h_sc)))
    h_small = resize_premul(h_im, (hw, hh))
    # Squash/stretch as it pops out
    sq_x = 1.0 + 0.08 * math.sin(pop_t * math.pi)
    sq_y = 1.0 / sq_x
    h_warp = warp_rgba(
        h_small,
        angle_deg=head_tilt_deg,
        sx=sq_x,
        sy=sq_y,
        dx=0,
        dy=0,
        pivot=(hw * 0.5, hh * 0.5),
        out_hw=(hh + 36, hw + 36),
    )
    hx = cx - h_warp.shape[1] * 0.5
    hy = (cy - ext) - h_warp.shape[0] * 0.62
    patch = alpha_over(patch, h_warp, hx, hy)

    # Clip head below the brass valve cylinder lip so it cleanly emerges FROM inside the pipe!
    patch[cy + 6:, :] = 0

    # 3. Brass side-valve cylinder body & flared rim (drawn OVER bottom of spring/neck)
    cyl = np.zeros_like(patch)
    # Metallic brass vertical gradient across cylinder
    for dx_i in range(-28, 29):
        t = (dx_i + 28) / 56.0
        shade = 0.55 + 0.55 * math.sin(t * math.pi) - 0.18 * (t - 0.35)
        col = (
            int(np.clip(182 * shade, 40, 255)),
            int(np.clip(146 * shade, 30, 240)),
            int(np.clip(58 * shade, 15, 160)),
            255,
        )
        cv2.line(cyl, (cx + dx_i, cy), (cx + dx_i, cy + 44), col, 1)
    cv2.rectangle(cyl, (cx - 28, cy), (cx + 28, cy + 44), (62, 44, 16, 255), 2, cv2.LINE_AA)
    # Top flared brass collar & dark interior bore
    cv2.ellipse(cyl, (cx, cy), (34, 11), 0, 0, 360, (196, 158, 66, 255), -1, cv2.LINE_AA)
    cv2.ellipse(cyl, (cx, cy), (34, 11), 0, 0, 360, (70, 50, 18, 255), 2, cv2.LINE_AA)
    cv2.ellipse(cyl, (cx, cy), (26, 7), 0, 0, 360, (38, 26, 12, 255), -1, cv2.LINE_AA)
    # Hinged brass flapper lid swung open proportional to pop_t
    lid_ang = -15.0 - 95.0 * min(1.0, pop_t * 1.35)
    lx1 = cx - 32 + int(round(math.cos(math.radians(lid_ang)) * 54))
    ly1 = cy - 4 + int(round(math.sin(math.radians(lid_ang)) * 54))
    cv2.line(cyl, (cx - 32, cy - 4), (lx1, ly1), (78, 56, 20, 255), 9, cv2.LINE_AA)
    cv2.line(cyl, (cx - 32, cy - 4), (lx1, ly1), (222, 184, 86, 255), 5, cv2.LINE_AA)
    cv2.circle(cyl, (cx - 32, cy - 4), 5, (140, 106, 38, 255), -1, cv2.LINE_AA)

    # Re-composite head upper portion ABOVE cylinder rim? Wait: cylinder mouth should be IN FRONT of neck,
    # while head emerges out of mouth! That's already handled because we only want cyl below cy+2 overlapping neck!
    # Actually: draw back rim & interior bore behind head, then head, then front lower lip & body of cylinder!
    cyl_front = cyl.copy()
    cyl_front[:cy + 1, :] = 0  # keep front half-lip & barrel below cy+1
    # Keep hinged lid on top-left
    patch = alpha_over(patch, cyl_front, 0, 0)
    # Draw hinged lid on top
    lid_layer = np.zeros_like(patch)
    cv2.line(lid_layer, (cx - 32, cy - 4), (lx1, ly1), (78, 56, 20, 255), 9, cv2.LINE_AA)
    cv2.line(lid_layer, (cx - 32, cy - 4), (lx1, ly1), (222, 184, 86, 255), 5, cv2.LINE_AA)
    cv2.circle(lid_layer, (cx - 32, cy - 4), 5, (140, 106, 38, 255), -1, cv2.LINE_AA)
    patch = alpha_over(patch, lid_layer, 0, 0)

    rot = warp_rgba(patch, angle_deg=valve_angle_deg, pivot=(cx, cy + 20), out_hw=(ph, pw))
    return alpha_over(canvas, rot, bx - cx, by - (cy + 20))


def _draw_gauge_needle(canvas: np.ndarray, center: Tuple[float, float], norm_val: float) -> np.ndarray:
    """Draw animated trembling PSI needle onto the brass pressure gauge."""
    out = canvas.copy()
    cx, cy = int(round(center[0])), int(round(center[1]))
    # Gauge sweeps from -215 deg (low) to +35 deg (redline!)
    ang = math.radians(-215.0 + 250.0 * np.clip(norm_val, 0.0, 1.12))
    x1 = cx + int(round(math.cos(ang) * 30.0))
    y1 = cy + int(round(math.sin(ang) * 30.0))
    col = (210, 28, 22, 255) if norm_val > 0.78 else (28, 24, 22, 255)
    cv2.line(out, (cx, cy), (x1, y1), col, 4, cv2.LINE_AA)
    cv2.circle(out, (cx, cy), 6, (58, 44, 22, 255), -1, cv2.LINE_AA)
    return out


def _draw_tuba_shockwave_and_geyser(
    canvas: np.ndarray,
    bell_xy: Tuple[float, float],
    fire_t: float,
    mists: List[np.ndarray],
    mud_globs: List[np.ndarray],
    splats: List[np.ndarray],
) -> np.ndarray:
    """Render expanding tuba-fart sonic shockwave rings & erupting brown mud geyser."""
    out = canvas.copy()
    h, w = out.shape[:2]
    bx, by = bell_xy
    # Tuba bell aims up-left around -156 deg (dx=-0.91, dy=-0.41)
    dir_x, dir_y = -0.92, -0.39

    # 1. Sonic fart shockwave rings (greenish-brown translucent rings expanding out)
    ring_layer = np.zeros((h, w, 4), dtype=np.uint8)
    for k in range(3):
        rt = (fire_t * 1.4 - k * 0.14)
        if 0.0 < rt < 0.85:
            dist = 40.0 + rt * 320.0
            rx = int(round(bx + dir_x * dist))
            ry = int(round(by + dir_y * dist))
            rad_major = int(round(65 + rt * 185))
            rad_minor = int(round(32 + rt * 95))
            al = int(round(210 * (1.0 - rt / 0.85)))
            col = (144, 178, 52, al) if k != 1 else (128, 96, 36, al)
            cv2.ellipse(ring_layer, (rx, ry), (rad_minor, rad_major), -23.0, 0, 360, col, max(4, int(18 * (1.0 - rt))), cv2.LINE_AA)
    ring_layer = cv2.GaussianBlur(ring_layer, (9, 9), 2.5)
    out = alpha_over(out, ring_layer, 0, 0)

    # 2. Billowing brown/green fart mist puffs blasting out of the bell
    for k in range(5):
        mt = fire_t * 1.35 - k * 0.07
        if 0.0 < mt < 0.95:
            m_im = mists[(k * 2) % len(mists)]
            sc = 0.65 + mt * 1.85
            nw, nh = max(16, int(round(m_im.shape[1] * sc))), max(16, int(round(m_im.shape[0] * sc)))
            m_rs = resize_premul(m_im, (nw, nh))
            dist = 20.0 + mt * (240.0 + k * 28.0)
            perp = (k - 2) * 26.0 * mt
            mx = bx + dir_x * dist - dir_y * perp - nw * 0.5
            my = by + dir_y * dist + dir_x * perp - nh * 0.5
            op = max(0.0, 1.0 - mt / 0.95) * 0.88
            out = alpha_over(out, m_rs, mx, my, opacity=op)

    # 3. Mud geyser splats & flying chunky globs
    if fire_t < 0.72:
        sp = splats[int(fire_t * 10) % len(splats)]
        sc = 0.65 + fire_t * 1.5
        nw, nh = max(16, int(round(sp.shape[1] * sc))), max(16, int(round(sp.shape[0] * sc)))
        sp_rs = resize_premul(sp, (nw, nh))
        out = alpha_over(
            out,
            sp_rs,
            bx + dir_x * (60 + fire_t * 160) - nw * 0.5,
            by + dir_y * (60 + fire_t * 160) - nh * 0.5,
            opacity=max(0.0, 1.0 - fire_t / 0.72),
        )

    for g in range(10):
        gt = fire_t * 1.5 - (g % 3) * 0.06
        if 0.0 < gt < 0.92:
            glob_im = mud_globs[g % len(mud_globs)]
            g_sc = 0.45 + 0.35 * ((g % 4) / 3.0)
            gw = max(10, int(round(glob_im.shape[1] * g_sc)))
            gh = max(10, int(round(glob_im.shape[0] * g_sc)))
            g_rs = resize_premul(glob_im, (gw, gh))
            ang_spread = (g - 4.5) * 0.14
            ca, sa = math.cos(ang_spread), math.sin(ang_spread)
            vx = dir_x * ca - dir_y * sa
            vy = dir_x * sa + dir_y * ca
            dist = 35.0 + gt * (310.0 + (g % 3) * 55.0)
            gx = bx + vx * dist - gw * 0.5
            gy = by + vy * dist + 75.0 * gt * gt - gh * 0.5
            out = alpha_over(out, g_rs, gx, gy, opacity=max(0.0, 1.0 - gt / 0.92))

    return out


def _build_viewmodel_frame(
    decomp: Dict[str, object],
    assets: Dict[str, object],
    t_norm: float,
    mode: str,
    phase_t: float,
) -> np.ndarray:
    """Render one full-res padded frame then downsample cleanly to 420x360."""
    pw, ph = PADDED_WH
    canvas = np.zeros((ph, pw, 4), dtype=np.uint8)
    tau = 2.0 * math.pi

    base = decomp["base"]
    wheel_patch = decomp["wheel_patch"]
    wx, wy = _pad_xy(*decomp["wheel_center"])
    chain_patch = decomp["chain_patch"]
    cx0, cy0 = _pad_xy(*decomp["chain_pos"])
    bowl_mask_orig = decomp["bowl_inner_mask"]
    front_lip_orig = decomp["front_lip_mask"]
    gx, gy = _pad_xy(*decomp["gauge_center"])
    bx, by = _pad_xy(*decomp["bell_center"])

    # Padded masks
    bowl_mask = np.zeros((ph, pw), dtype=bool)
    bowl_mask[PAD_T:PAD_T + 1024, PAD_L:PAD_L + 1024] = bowl_mask_orig
    front_lip = np.zeros((ph, pw), dtype=bool)
    front_lip[PAD_T:PAD_T + 1024, PAD_L:PAD_L + 1024] = front_lip_orig

    # Recoil, flush chain pull, bloke duck/bounce, wheel speed, flag whip
    recoil_x, recoil_y, recoil_rot = 0.0, 0.0, 0.0
    chain_pull_y = 0.0
    bloke_duck_y = 0.0
    wheel_deg = t_norm * 360.0
    flag_amp = 1.05
    gauge_val = 0.72 + 0.09 * math.sin(tau * t_norm * 7.0)
    flush_swirl = 0.0

    if mode == "fire":
        # 0..0.20: yank flush chain & bloke ducks; 0.15..0.55: huge recoil & eruption; 0.55..1.0: settle
        chain_pull_y = 44.0 * math.sin(min(1.0, phase_t / 0.45) * math.pi)
        duck_env = math.sin(min(1.0, phase_t / 0.85) * math.pi)
        bloke_duck_y = 115.0 * duck_env
        kick = math.sin(min(1.0, max(0.0, phase_t - 0.12) / 0.65) * math.pi)
        recoil_x = 46.0 * kick
        recoil_y = 28.0 * kick
        recoil_rot = -5.5 * kick
        wheel_deg = phase_t * 1080.0
        flag_amp = 1.45
        gauge_val = 0.82 + 0.28 * kick
    elif mode == "reload":
        chain_pull_y = 52.0 * math.sin(min(1.0, phase_t / 0.6) * math.pi)
        flush_swirl = math.sin(phase_t * math.pi)
        # Guy pops up with joyful spring bounce after half-way
        bounce = -34.0 * math.sin(max(0.0, (phase_t - 0.35) / 0.65) * math.pi)
        bloke_duck_y = 75.0 * max(0.0, 1.0 - phase_t * 2.1) + bounce
        recoil_y = 14.0 * math.sin(phase_t * tau)
        wheel_deg = -phase_t * 900.0
        flag_amp = 1.25
        gauge_val = 0.35 + 0.45 * phase_t

    # --- LAYER 0: Two Tall Waving Tricolor Flags Behind the Tank ---
    p1_0 = _pad_xy(735.0, 210.0)
    p1_1 = _pad_xy(655.0, -145.0)
    p2_0 = _pad_xy(840.0, 210.0)
    p2_1 = _pad_xy(935.0, -140.0)
    canvas = _draw_brass_pole(canvas, p1_0, p1_1, thick=8)
    canvas = _draw_brass_pole(canvas, p2_0, p2_1, thick=8)

    # Left flag (poles at right edge or left edge flying outward!)
    f1 = render_tricolor_flag(255, 165, phase=(tau * t_norm * 2.0) % tau, pole_left=False, amp=flag_amp)
    f1_rot = warp_rgba(f1, angle_deg=11.0, pivot=(245.0, 25.0), out_hw=(240, 310))
    canvas = alpha_over(canvas, f1_rot, p1_1[0] - 245.0, p1_1[1] - 10.0)

    # Right flag flying rightward
    f2 = render_tricolor_flag(255, 165, phase=(tau * t_norm * 2.0 + 1.4) % tau, pole_left=True, amp=flag_amp)
    f2_rot = warp_rgba(f2, angle_deg=-12.0, pivot=(12.0, 25.0), out_hw=(240, 310))
    canvas = alpha_over(canvas, f2_rot, p2_1[0] - 12.0, p2_1[1] - 8.0)

    # --- LAYER 1: Back Toilet Basin (full base behind guy inside bowl) ---
    base_pad = np.zeros((ph, pw, 4), dtype=np.uint8)
    base_pad[PAD_T:PAD_T + 1024, PAD_L:PAD_L + 1024] = base
    canvas = alpha_over(canvas, base_pad, 0, 0)

    # --- LAYER 2: Heavy-set Bloke Waist-Deep in Bowl + Bubbling Brown Sludge ---
    dance_frames: List[np.ndarray] = assets["dance_48"]  # type: ignore
    heads: Dict[str, np.ndarray] = assets["heads"]  # type: ignore
    # Smooth ping-pong over clean front-facing waving poses [30..47]
    ping = list(range(30, 48)) + list(range(46, 30, -1))
    d_idx = ping[int(round((t_norm * 2.0 % 1.0) * (len(ping) - 1)))]
    guy = dance_frames[d_idx]
    # Crop upper torso + raised arms (above shorts y<270) and erase original head so we replace cleanly
    guy_upper = guy[:270, :].copy()
    # Erase original head region (center x=126..214, y=42..135) while keeping raised hands on sides!
    guy_upper[42:135, 128:212] = 0
    # Slight brown mud splash tint near lower belly (y > 215)
    guy_upper[215:, :, 0] = np.clip(guy_upper[215:, :, 0].astype(np.int32) - 45, 0, 255).astype(np.uint8)
    guy_upper[215:, :, 1] = np.clip(guy_upper[215:, :, 1].astype(np.int32) - 65, 0, 255).astype(np.uint8)
    guy_upper[215:, :, 2] = np.clip(guy_upper[215:, :, 2].astype(np.int32) - 85, 0, 255).astype(np.uint8)

    g_sc = 0.88
    gw, gh = int(round(guy_upper.shape[1] * g_sc)), int(round(guy_upper.shape[0] * g_sc))
    guy_rs = resize_premul(guy_upper, (gw, gh))

    # Expressive animated head bobbing cleanly on his shoulders
    head_cycle = ["head_cross", "head_scream_front", "head_laugh_tilt", "head_wide_grin", "head_sky_gasp"]
    if mode == "fire":
        h_key = "head_sky_gasp"
    elif mode == "reload":
        h_key = "head_wide_grin"
    else:
        h_key = head_cycle[int(t_norm * len(head_cycle) * 2.0) % len(head_cycle)]
    h_im = heads.get(h_key, heads["head_cross"])
    h_rs = resize_premul(h_im, (108, 108))
    head_bob_x = math.sin(tau * t_norm * 4.0) * 6.0
    head_bob_y = abs(math.sin(tau * t_norm * 6.0)) * -6.0
    head_ang = math.sin(tau * t_norm * 3.0) * 14.0
    h_rot = warp_rgba(h_rs, angle_deg=head_ang, pivot=(54, 54), out_hw=(130, 130))

    # Place guy inside bowl center (602, 345) padded, with cranking sway
    crank_x = math.sin(tau * t_norm * 4.0) * 12.0
    crank_y = abs(math.cos(tau * t_norm * 4.0)) * -10.0 + bloke_duck_y
    guy_x = _pad_xy(602.0, 0)[0] - gw * 0.5 + crank_x
    guy_y = _pad_xy(0, 210.0)[1] + crank_y

    # Mask guy so he stays inside the bowl on the right/bottom (cannot bleed past outer seat right x>670 or below y>465)
    guy_layer = np.zeros((ph, pw, 4), dtype=np.uint8)
    guy_layer = alpha_over(guy_layer, guy_rs, guy_x, guy_y)
    # Place expressive head directly on top of his neck/shoulders (at ~y + 22 px inside guy_rs)
    guy_layer = alpha_over(guy_layer, h_rot, guy_x + gw * 0.5 - 65.0 + head_bob_x, guy_y + 22.0 + head_bob_y)
    # Clip guy's lower waist cleanly at the mud surface & right side of bowl
    mud_clip_y = int(_pad_xy(0, 385.0)[1])
    guy_layer[mud_clip_y:, :] = 0
    rx_clip = int(_pad_xy(670.0, 0)[0])
    ry_clip = int(_pad_xy(0, 240.0)[1])
    guy_layer[ry_clip:, rx_clip:] = 0

    canvas = alpha_over(canvas, guy_layer, 0, 0)

    # Bubbling Brown Sludge inside bowl (in front of his waist!)
    sludge = _render_sludge_and_bubbles(pw, ph, bowl_mask, t_norm, flush_swirl=flush_swirl)
    canvas = alpha_over(canvas, sludge, 0, 0)

    # --- LAYER 3: Front Porcelain Seat Lip + Animated Wheel, Chain, Gauge ---
    front_pad = np.zeros((ph, pw, 4), dtype=np.uint8)
    front_pad[PAD_T:PAD_T + 1024, PAD_L:PAD_L + 1024][front_lip_orig] = base[front_lip_orig]
    canvas = alpha_over(canvas, front_pad, 0, 0)

    # Spinning Navy Spoked Crank-Wheel
    w_rot = warp_rgba(wheel_patch, angle_deg=-wheel_deg, pivot=(wheel_patch.shape[1] * 0.5, wheel_patch.shape[0] * 0.5))
    canvas = alpha_over(canvas, w_rot, wx - wheel_patch.shape[1] * 0.5, wy - wheel_patch.shape[0] * 0.5)

    # Pullable Porcelain Flush Chain & Handle (with gentle sway or fire yank!)
    chain_sway = math.sin(tau * t_norm * 2.0) * 2.2
    ch_rot = warp_rgba(chain_patch, angle_deg=chain_sway, pivot=(chain_patch.shape[1] * 0.5, 4.0), out_hw=(chain_patch.shape[0] + 24, chain_patch.shape[1] + 24))
    canvas = alpha_over(canvas, ch_rot, cx0, cy0 + chain_pull_y)

    # Animated Pressure Gauge Needle
    canvas = _draw_gauge_needle(canvas, (gx, gy), gauge_val)

    # --- LAYER 4: TWO Brass Side-Valves with Pop-Up Arguing/Yelling Jack-in-the-Box Heads! ---
    # Left brass valve mounted on tuba upper port (458, 368), right valve on upper tank edge (748, 222)
    pop1 = 0.5 + 0.5 * math.sin(tau * t_norm * 3.0)
    pop2 = 0.5 + 0.5 * math.sin(tau * t_norm * 3.0 + math.pi * 0.85)
    if mode == "fire":
        pop1, pop2 = 1.0, 1.0
    elif mode == "reload":
        pop1 = 0.25 + 0.75 * phase_t
        pop2 = 0.25 + 0.75 * phase_t

    h_left = heads.get("head_turban_yell", heads["head_turban_grin"])
    h_right = heads.get("head_oiled_yell", heads["head_side_yell_l"])
    tilt1 = -12.0 + 10.0 * math.sin(tau * t_norm * 6.0)
    tilt2 = 12.0 - 10.0 * math.cos(tau * t_norm * 6.0)

    canvas = _draw_brass_valve_jack(
        canvas,
        h_left,
        _pad_xy(458.0, 368.0),
        valve_angle_deg=-14.0,
        pop_t=pop1,
        head_tilt_deg=tilt1,
        flip_head=False,
    )
    canvas = _draw_brass_valve_jack(
        canvas,
        h_right,
        _pad_xy(748.0, 215.0),
        valve_angle_deg=12.0,
        pop_t=pop2,
        head_tilt_deg=tilt2,
        flip_head=True,  # face left toward the left valve head so they're yelling at each other!
    )

    # Apply subtle weapon idle breathe / fire recoil while keeping gauntlets anchored to bottom!
    breathe_x = math.sin(tau * t_norm) * 7.0
    breathe_y = abs(math.sin(tau * t_norm * 2.0)) * 5.0
    recoil_sc = 1.04 if mode == "fire" else 1.02
    canvas = warp_rgba(
        canvas,
        angle_deg=recoil_rot * 0.65,
        sx=recoil_sc,
        sy=recoil_sc,
        dx=recoil_x * 0.65 + breathe_x,
        dy=recoil_y * 0.45 + breathe_y + 12.0,
        pivot=(pw * 0.58, ph - 10.0),
    )

    # --- LAYER 5: Stink Fumes, Tuba-Fart Shockwave & Mud Geyser, and 14 Buzzing Flies ---
    canvas = _draw_stink_fumes(canvas, _pad_xy(588.0, 165.0), t_norm, strength=0.9)
    if mode == "fire" and phase_t >= 0.08:
        fire_u = min(1.0, (phase_t - 0.08) / 0.88)
        canvas = _draw_tuba_shockwave_and_geyser(
            canvas,
            (bx + recoil_x, by + recoil_y),
            fire_u,
            assets["mists"],  # type: ignore
            assets["mud_globs"],  # type: ignore
            assets["splats"],  # type: ignore
        )

    # 14 Buzzing Flies orbiting BOTH the open toilet bowl and the flared brass tuba bell!
    fly_centers = [
        _pad_xy(590.0, 290.0),  # open toilet bowl
        _pad_xy(305.0, 415.0),  # flared brass tuba bell
    ]
    canvas = render_fly_swarm(canvas, fly_centers, t_norm, n_flies=14, scale=2.7)

    return resize_premul(canvas, VM_WH)


def _build_torpedo_angle(
    torpedo_rgba: np.ndarray,
    turn_16: List[np.ndarray],
    dance_48: List[np.ndarray],
    heads: Dict[str, np.ndarray],
    mists: List[np.ndarray],
    mud_globs: List[np.ndarray],
    angle_idx: int,
    frame_idx: int,
    n_angles: int = 16,
    n_frames: int = 6,
) -> np.ndarray:
    """Build Dr. Strangelove-style fat bloke cowboy-riding the `poop_torpedo` at angle `angle_idx`
    (0=toward camera, 4=flying left, 8=flying away, 12=flying right) and animation frame `frame_idx`.
    """
    sz = 360
    canvas = np.zeros((sz, sz, 4), dtype=np.uint8)
    cx, cy = sz * 0.5, sz * 0.56
    t_anim = frame_idx / float(n_frames)
    tau = 2.0 * math.pi

    # Clean static spark plume off torpedo (x > 842 in 1024x1024)
    torp = torpedo_rgba.copy()
    torp[:, 848:, :] = 0
    # Crop tightly around torpedo (40..848, 320..680)
    ys, xs = np.nonzero(torp[..., 3] > 20)
    torp_crop = torp[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]

    # Yaw convention matching turn_16:
    # a=0 -> front (coming straight at viewer), a=4 -> facing left, a=8 -> away, a=12 -> facing right
    yaw_rad = tau * angle_idx / float(n_angles)
    sin_y = math.sin(yaw_rad)  # +1 at a=4 (left), -1 at a=12 (right), 0 at a=0/8
    cos_y = math.cos(yaw_rad)  # +1 at a=0 (front), -1 at a=8 (back)

    # Pitch tilt wobble across animation frames
    pitch_deg = 6.0 * math.sin(tau * t_anim) * (1.0 if sin_y >= 0 else -1.0)

    # 1. Draw the 3D-oriented Poop-Torpedo body
    # When |sin_y| is small (head-on or rear-on), render concentric poop swirl / brass nozzle + 4 fins,
    # blended cleanly with foreshortened side torpedo!
    horiz_scale = max(0.24, abs(sin_y))
    torp_w = max(48, int(round(240 * horiz_scale)))
    torp_h = 104
    t_src = torp_crop if sin_y >= 0 else np.fliplr(torp_crop).copy()
    t_rs = resize_premul(t_src, (torp_w, torp_h))

    # Draw 4 brass tail fins & concentric front/rear discs when strongly foreshortened (|cos_y| > 0.55)
    torp_layer = np.zeros((sz, sz, 4), dtype=np.uint8)
    if abs(cos_y) > 0.45:
        # Nose-on (cos_y > 0) or tail-on (cos_y < 0)
        fin_col = (128, 102, 46, 255)
        fin_hi = (176, 144, 72, 255)
        fin_r = int(round(62 * abs(cos_y)))
        for fang in [0, 90, 180, 270]:
            rad = math.radians(fang + 45)
            fx = int(round(cx + math.cos(rad) * fin_r))
            fy = int(round(cy + math.sin(rad) * fin_r))
            cv2.line(torp_layer, (int(cx), int(cy)), (fx, fy), (64, 48, 20, 255), 11, cv2.LINE_AA)
            cv2.line(torp_layer, (int(cx), int(cy)), (fx, fy), fin_col, 7, cv2.LINE_AA)
            cv2.line(torp_layer, (int(cx), int(cy)), (fx, fy), fin_hi, 3, cv2.LINE_AA)

        if cos_y > 0:
            # Head-on: brass collar + stacked glossy brown poop coils + pointed tip!
            torp_layer = alpha_over(torp_layer, t_rs, cx - torp_w * 0.5, cy - torp_h * 0.5)
            for ring_i, (rr, col) in enumerate([(44, (86, 48, 20, 255)), (34, (108, 62, 26, 255)), (23, (124, 74, 32, 255)), (12, (142, 88, 40, 255))]):
                ox = int(round(cx - sin_y * (ring_i * 6)))
                cv2.circle(torp_layer, (ox, int(cy)), rr, (52, 26, 10, 255), -1, cv2.LINE_AA)
                cv2.circle(torp_layer, (ox, int(cy)), max(2, rr - 2), col, -1, cv2.LINE_AA)
                cv2.circle(torp_layer, (ox - rr // 3, int(cy - rr // 3)), max(2, rr // 4), (218, 184, 134, 210), -1, cv2.LINE_AA)
        else:
            # Tail-on: poop silhouette + riveted brass nozzle ring!
            torp_layer = alpha_over(torp_layer, t_rs, cx - torp_w * 0.5, cy - torp_h * 0.5)
            cv2.circle(torp_layer, (int(cx), int(cy)), 42, (62, 46, 20, 255), -1, cv2.LINE_AA)
            cv2.circle(torp_layer, (int(cx), int(cy)), 36, (122, 96, 44, 255), -1, cv2.LINE_AA)
            cv2.circle(torp_layer, (int(cx), int(cy)), 20, (34, 26, 16, 255), -1, cv2.LINE_AA)
    else:
        torp_layer = alpha_over(torp_layer, t_rs, cx - torp_w * 0.5, cy - torp_h * 0.5)

    # 2. Dr. Strangelove-style Fat Bloke Cowboy-Riding / Straddling the Torpedo!
    guy = turn_16[angle_idx % len(turn_16)]
    # Resize guy proportionally
    g_sc = 0.43
    gw, gh = int(round(guy.shape[1] * g_sc)), int(round(guy.shape[0] * g_sc))
    g_rs = resize_premul(guy, (gw, gh))

    # Split at waist/hip (y ~ 58% of height) so legs straddle AROUND the rocket cylinder!
    split_y = int(round(gh * 0.54))
    upper = g_rs[:split_y, :].copy()
    legs = g_rs[split_y:, :].copy()

    # Straddle legs: spread left/right if head-on/away, or bend knee forward if side-on
    saddle_x = cx - sin_y * 16.0
    saddle_y = cy - 28.0
    if abs(cos_y) > 0.6:
        lw = legs.shape[1] // 2
        leg_l = warp_rgba(legs[:, :lw], angle_deg=-26.0, pivot=(lw * 0.8, 4.0), out_hw=(legs.shape[0] + 24, lw + 36))
        leg_r = warp_rgba(legs[:, lw:], angle_deg=26.0, pivot=(lw * 0.2, 4.0), out_hw=(legs.shape[0] + 24, lw + 36))
        canvas = alpha_over(canvas, torp_layer, 0, 0)
        canvas = alpha_over(canvas, leg_l, saddle_x - lw - 8, saddle_y + 16)
        canvas = alpha_over(canvas, leg_r, saddle_x - 4, saddle_y + 16)
    else:
        leg_ang = -32.0 if sin_y >= 0 else 32.0
        leg_bent = warp_rgba(legs, angle_deg=leg_ang, sy=0.72, pivot=(legs.shape[1] * 0.5, 4.0), out_hw=(legs.shape[0] + 30, legs.shape[1] + 40))
        canvas = alpha_over(canvas, torp_layer, 0, 0)
        canvas = alpha_over(canvas, leg_bent, saddle_x - leg_bent.shape[1] * 0.5, saddle_y + 14)

    # On front/side-front angles, erase original small head on `upper` and swap expressive cheering head
    replace_head = cos_y > -0.25
    head_anchor_local = None
    if replace_head:
        hys, hxs = np.nonzero(upper[: int(upper.shape[0] * 0.42), :, 3] > 20)
        if len(hxs) > 0:
            head_anchor_local = (float(hxs.mean()), float(hys.mean()))
            upper[: int(upper.shape[0] * 0.36), :] = 0

    lean_deg = -14.0 * sin_y
    bounce_y = -4.0 * abs(math.sin(tau * t_anim))
    upper_rot = warp_rgba(upper, angle_deg=lean_deg, pivot=(upper.shape[1] * 0.5, upper.shape[0] - 8.0), out_hw=(upper.shape[0] + 36, upper.shape[1] + 40))
    ux = saddle_x - upper_rot.shape[1] * 0.5
    uy = saddle_y - upper_rot.shape[0] + 32.0 + bounce_y
    canvas = alpha_over(canvas, upper_rot, ux, uy)

    # Overlay waving cowboy arm (from dance_48[36] raised right arm) pumping "YEEHAW!"
    if cos_y > -0.45:
        arm_src = dance_48[36]
        arm_crop = arm_src[38:178, 4:108].copy()
        a_rs = resize_premul(arm_crop, (44, 60))
        pump_ang = -22.0 + 38.0 * math.sin(tau * t_anim)
        if sin_y < 0:
            a_rs = np.fliplr(a_rs).copy()
            pump_ang = -pump_ang
        a_rot = warp_rgba(a_rs, angle_deg=pump_ang, pivot=(36 if sin_y >= 0 else 8, 52), out_hw=(92, 92))
        canvas = alpha_over(canvas, a_rot, saddle_x - (56 if sin_y >= 0 else 36), uy - 24)

    if replace_head and head_anchor_local is not None:
        h_name = "head_sky_gasp" if frame_idx % 2 == 0 else "head_laugh_tilt"
        h_im = heads.get(h_name, heads["head_cross"])
        if sin_y < -0.2:
            h_im = np.fliplr(h_im).copy()
        h_rs = resize_premul(h_im, (46, 46))
        h_rot = warp_rgba(h_rs, angle_deg=lean_deg * 0.6 + 8.0 * math.sin(tau * t_anim), pivot=(23, 23), out_hw=(62, 62))
        # Rotate head_anchor_local around upper's pivot so head lands squarely on the neck!
        px, py = upper.shape[1] * 0.5, upper.shape[0] - 8.0
        rad_l = math.radians(-lean_deg)
        dx_h, dy_h = head_anchor_local[0] - px, head_anchor_local[1] - py
        hx_c = ux + (upper_rot.shape[1] - upper.shape[1]) * 0.5 + px + dx_h * math.cos(rad_l) - dy_h * math.sin(rad_l)
        hy_c = uy + (upper_rot.shape[0] - upper.shape[0]) * 0.5 + py + dx_h * math.sin(rad_l) + dy_h * math.cos(rad_l)
        canvas = alpha_over(canvas, h_rot, hx_c - 31.0, hy_c - 31.0)

    # 3. Sputtering Fuse Sparks + Mud Exhaust at rocket tail (hidden behind torso on head-on cos_y > 0.65)!
    tail_x = cx + sin_y * (torp_w * 0.48)
    tail_y = cy
    if cos_y < 0.72:
        m_im = mists[frame_idx % len(mists)]
        m_rs = resize_premul(m_im, (68, 68))
        canvas = alpha_over(canvas, m_rs, tail_x - 34 + sin_y * 20.0, tail_y - 34, opacity=0.78)
        g_im = mud_globs[frame_idx % len(mud_globs)]
        g_rs = resize_premul(g_im, (24, 24))
        canvas = alpha_over(canvas, g_rs, tail_x - 12 + sin_y * 28.0, tail_y + 4)

        sparks = np.zeros((sz, sz, 4), dtype=np.uint8)
        fx_c = int(round(tail_x + sin_y * 16.0))
        fy_c = int(round(tail_y - 4.0))
        cv2.circle(sparks, (fx_c, fy_c), 7, (255, 165, 30, 240), -1, cv2.LINE_AA)
        cv2.circle(sparks, (fx_c, fy_c), 3, (255, 250, 210, 255), -1, cv2.LINE_AA)
        for sp_i in range(7):
            ang_sp = tau * (sp_i / 7.0 + t_anim * 1.3)
            dist_sp = 8.0 + ((sp_i * 5 + frame_idx * 4) % 16)
            sx0 = int(round(fx_c + math.cos(ang_sp) * 4.0))
            sy0 = int(round(fy_c + math.sin(ang_sp) * 4.0))
            sx1 = int(round(fx_c + math.cos(ang_sp) * dist_sp))
            sy1 = int(round(fy_c + math.sin(ang_sp) * dist_sp))
            col_sp = (255, 220, 90, 240) if sp_i % 2 == 0 else (255, 120, 20, 220)
            cv2.line(sparks, (sx0, sy0), (sx1, sy1), col_sp, 2, cv2.LINE_AA)
        canvas = alpha_over(canvas, sparks, 0, 0)

    # Pitch-tilt whole torpedo+rider slightly
    canvas = warp_rgba(canvas, angle_deg=pitch_deg, pivot=(cx, cy))

    # 4. Chasing Flies buzzing around the poop warhead!
    nose_x = cx - sin_y * (torp_w * 0.36)
    canvas = render_fly_swarm(canvas, [(nose_x, cy - 10.0)], t_anim, n_flies=4, scale=1.15)

    return resize_premul(canvas, PROJ_WH)


def _draw_front_tuba_weapon(
    w: int,
    h: int,
    t_norm: float,
    tuba_rgba: np.ndarray,
    wheel_patch: np.ndarray,
    heads: Dict[str, np.ndarray],
    recoil_sc: float = 1.0,
) -> np.ndarray:
    """Build a crisp 3rd-person forward-aimed Porcelain Poop-Tuba cradle to overlay onto
    `enemy_shooter_base`, featuring the forward-facing flared brass bell, open toilet bowl
    with tiny yelling guy + sludge, spinning navy wheel, and TWO tall waving tricolor flags!
    """
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    tau = 2.0 * math.pi

    # Extract & foreshorten the porcelain tank/bowl + brass tuba from tuba_mortar
    # Crop just the weapon without the first-person gauntlets (y: 70..695, x: 205..945)
    weap = tuba_rgba[70:695, 205:945].copy()
    # Cleanly remove bottom gauntlets & brass grip with a smooth diagonal/curved cut so no square edges appear
    wy_g, wx_g = np.mgrid[0:weap.shape[0], 0:weap.shape[1]]
    gauntlet_cut = (wy_g > 455 + (wx_g - 200) * 0.22) & (wx_g < 630)
    weap[gauntlet_cut] = 0

    # Scale weapon neatly across enemy chest/hip aimed forward-left toward viewer
    sc = 0.265 * recoil_sc
    ww, wh = max(16, int(round(weap.shape[1] * sc))), max(16, int(round(weap.shape[0] * sc)))
    w_rs = resize_premul(weap, (ww, wh))
    wx_off, wy_off = 114, 134

    # Two waving tricolor flags mounted solidly into the top of the porcelain tank
    pole1 = ((wx_off + int(ww * 0.72), wy_off + int(wh * 0.20)), (wx_off + int(ww * 0.56), wy_off - 54))
    pole2 = ((wx_off + int(ww * 0.84), wy_off + int(wh * 0.22)), (wx_off + int(ww * 0.94), wy_off - 50))
    layer = _draw_brass_pole(layer, pole1[0], pole1[1], thick=3)
    layer = _draw_brass_pole(layer, pole2[0], pole2[1], thick=3)
    f1 = render_tricolor_flag(74, 48, phase=(tau * t_norm) % tau, pole_left=False, amp=1.1)
    f2 = render_tricolor_flag(74, 48, phase=(tau * t_norm + 1.5) % tau, pole_left=True, amp=1.1)
    layer = alpha_over(layer, f1, pole1[1][0] - 70, pole1[1][1] - 6)
    layer = alpha_over(layer, f2, pole2[1][0] - 4, pole2[1][1] - 6)

    layer = alpha_over(layer, w_rs, wx_off, wy_off)

    # Tiny screaming bloke head peeking out of the open toilet bowl
    h_mini = resize_premul(heads["head_scream_front"], (32, 32))
    hy_bob = math.sin(tau * t_norm * 3.0) * 4.0
    layer = alpha_over(layer, h_mini, wx_off + int(ww * 0.49) - 16, wy_off + int(wh * 0.30) - 16 + hy_bob)

    # Spinning navy wheel on right side of tank
    wh_s = resize_premul(wheel_patch, (int(round(wheel_patch.shape[1] * sc)), int(round(wheel_patch.shape[0] * sc))))
    wh_rot = warp_rgba(wh_s, angle_deg=-t_norm * 360.0)
    layer = alpha_over(layer, wh_rot, wx_off + int(ww * 0.88) - wh_rot.shape[1] // 2, wy_off + int(wh * 0.40) - wh_rot.shape[0] // 2)

    # Forward-facing dark circular tuba bell bore aimed right at the viewer!
    bell_cx = wx_off + int(ww * 0.14)
    bell_cy = wy_off + int(wh * 0.56)
    cv2.ellipse(layer, (bell_cx, bell_cy), (34, 38), 0, 0, 360, (148, 120, 48, 255), -1, cv2.LINE_AA)
    cv2.ellipse(layer, (bell_cx, bell_cy), (34, 38), 0, 0, 360, (220, 190, 96, 255), 3, cv2.LINE_AA)
    cv2.ellipse(layer, (bell_cx, bell_cy), (24, 28), 0, 0, 360, (42, 30, 14, 255), -1, cv2.LINE_AA)

    return layer


def _build_third_person_frame(
    decomp: Dict[str, object],
    assets: Dict[str, object],
    proj_front: np.ndarray,
    mode: str,
    idx: int,
    total: int,
) -> np.ndarray:
    """Render 3rd-person Quake enemy aiming the Porcelain Poop-Tuba toward the viewer."""
    tw, th = TP_WH
    t_norm = idx / float(total)
    tau = 2.0 * math.pi

    enemy: np.ndarray = assets["enemy"]  # type: ignore
    ys, xs = np.nonzero(enemy[..., 3] > 20)
    e_crop = enemy[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
    sc = (th - 24) / float(e_crop.shape[0])
    ew, eh = int(round(e_crop.shape[1] * sc)), int(round(e_crop.shape[0] * sc))
    e_rs = resize_premul(e_crop, (ew, eh))

    # Build base 374x420 working canvas (exact 320:360 aspect ratio -> zero distortion!)
    cw, ch = 374, 420
    canvas = np.zeros((ch, cw, 4), dtype=np.uint8)

    bob_y = math.sin(tau * t_norm * 2.0) * 4.0
    recoil_y, recoil_sc = 0.0, 1.0
    if mode == "fire":
        kick = math.sin(min(1.0, idx / float(max(1, total - 1))) * math.pi)
        recoil_y = 10.0 * kick
        recoil_sc = 1.0 + 0.10 * kick
    elif mode == "reload":
        bob_y = math.sin(tau * t_norm * 3.0) * 7.0

    # Place armored marine centered at bottom
    ex = (cw - ew) // 2 - 22
    ey = ch - 12 - eh + bob_y * 0.5 + recoil_y * 0.4
    canvas = alpha_over(canvas, e_rs, ex, ey)

    # Overlay foreshortened forward-aimed Porcelain Poop-Tuba across his hands
    weap_layer = _draw_front_tuba_weapon(
        cw,
        ch,
        t_norm,
        assets["tuba"],  # type: ignore
        decomp["wheel_patch"],  # type: ignore
        assets["heads"],  # type: ignore
        recoil_sc=recoil_sc,
    )
    canvas = alpha_over(canvas, weap_layer, 0, bob_y + recoil_y)

    bell_cx, bell_cy = 141, int(round(227 + bob_y + recoil_y))

    # On fire: massive tuba-fart shockwave & Strangelove poop-torpedo rider rocketing AT the camera!
    if mode == "fire":
        ft = idx / float(max(1, total - 1))
        # Fart shockwave ring expanding out of bell
        ring = np.zeros((ch, cw, 4), dtype=np.uint8)
        r_rad = int(round(24 + ft * 115))
        al = int(round(220 * (1.0 - ft)))
        cv2.circle(ring, (bell_cx, bell_cy), r_rad, (148, 178, 54, al), max(3, int(14 * (1.0 - ft))), cv2.LINE_AA)
        ring = cv2.GaussianBlur(ring, (7, 7), 2.0)
        canvas = alpha_over(canvas, ring, 0, 0)

        # Mist puff
        mists: List[np.ndarray] = assets["mists"]  # type: ignore
        m_im = resize_premul(mists[idx % len(mists)], (int(70 + ft * 120), int(70 + ft * 120)))
        canvas = alpha_over(canvas, m_im, bell_cx - m_im.shape[1] // 2, bell_cy - m_im.shape[0] // 2, opacity=max(0.0, 0.9 * (1.0 - ft)))

        # Mini Strangelove poop-torpedo rider launching straight toward the viewer!
        p_sz = int(round(48 + ft * 135))
        p_rs = resize_premul(proj_front, (p_sz, p_sz))
        px = bell_cx - p_sz // 2 - int(round(ft * 12))
        py = bell_cy - p_sz // 2 + int(round(ft * 26))
        canvas = alpha_over(canvas, p_rs, px, py)

    # Buzzing flies around shooter & bell
    canvas = render_fly_swarm(canvas, [(bell_cx, bell_cy), (255, 165)], t_norm, n_flies=10, scale=1.3)

    return resize_premul(canvas, TP_WH)


def _make_contact_sheet(paths: List[str], out_path: str, cols: int, thumb_wh: Tuple[int, int]) -> None:
    tw, th = thumb_wh
    rows = max(1, math.ceil(len(paths) / float(cols)))
    sheet = Image.new("RGBA", (cols * tw, rows * th), (30, 32, 38, 255))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGBA").resize((tw, th), Image.Resampling.BILINEAR)
        x = (i % cols) * tw
        y = (i // cols) * th
        sheet.paste(im, (x, y), im)
        draw.text((x + 3, y + 3), os.path.basename(p).replace(".png", ""), fill=(255, 235, 90, 255))
    sheet.save(out_path, optimize=True)


def build_all() -> Dict[str, object]:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("[concept4_tuba] Loading assets & decomposing tuba plate...")
    assets = _load_assets()
    decomp = _decompose_tuba(assets["tuba"])  # type: ignore

    # 1. First-person viewmodel (60 idle, 20 fire, 18 reload)
    vm_idle_files: List[str] = []
    vm_fire_files: List[str] = []
    vm_reload_files: List[str] = []

    print("[concept4_tuba] Rendering 60 vm_idle frames...")
    for i in range(60):
        fn = f"vm_idle_{i:02d}.png"
        fr = _build_viewmodel_frame(decomp, assets, i / 60.0, "idle", i / 60.0)
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
        vm_idle_files.append(fn)

    print("[concept4_tuba] Rendering 20 vm_fire frames...")
    for i in range(20):
        fn = f"vm_fire_{i:02d}.png"
        fr = _build_viewmodel_frame(decomp, assets, i / 20.0, "fire", i / 19.0)
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
        vm_fire_files.append(fn)

    print("[concept4_tuba] Rendering 18 vm_reload frames...")
    for i in range(18):
        fn = f"vm_reload_{i:02d}.png"
        fr = _build_viewmodel_frame(decomp, assets, i / 18.0, "reload", i / 17.0)
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
        vm_reload_files.append(fn)

    # 2. Projectile: 16 angles x 6 frames = 96 frames (Strangelove Poop-Torpedo Rider)
    print("[concept4_tuba] Rendering 16x6 Strangelove Poop-Torpedo projectile frames...")
    proj_files: List[List[str]] = []
    proj_front_frame = None
    for a in range(16):
        row_files: List[str] = []
        for f in range(6):
            fn = f"proj_a{a:02d}_f{f:02d}.png"
            fr = _build_torpedo_angle(
                assets["torpedo"],  # type: ignore
                assets["turn_16"],  # type: ignore
                assets["dance_48"],  # type: ignore
                assets["heads"],  # type: ignore
                assets["mists"],  # type: ignore
                assets["mud_globs"],  # type: ignore
                a,
                f,
                n_angles=16,
                n_frames=6,
            )
            _save_rgba(fr, os.path.join(OUT_DIR, fn))
            row_files.append(fn)
            if a == 0 and f == 0:
                proj_front_frame = fr
        proj_files.append(row_files)

    # 3. 3rd-person shooter: 16 idle, 12 fire, 12 reload
    print("[concept4_tuba] Rendering 3rd-person shooter sprites (tp_idle/fire/reload)...")
    tp_idle_files: List[str] = []
    tp_fire_files: List[str] = []
    tp_reload_files: List[str] = []

    for i in range(16):
        fn = f"tp_idle_{i:02d}.png"
        fr = _build_third_person_frame(decomp, assets, proj_front_frame, "idle", i, 16)
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
        tp_idle_files.append(fn)

    for i in range(12):
        fn = f"tp_fire_{i:02d}.png"
        fr = _build_third_person_frame(decomp, assets, proj_front_frame, "fire", i, 12)
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
        tp_fire_files.append(fn)

    for i in range(12):
        fn = f"tp_reload_{i:02d}.png"
        fr = _build_third_person_frame(decomp, assets, proj_front_frame, "reload", i, 12)
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
        tp_reload_files.append(fn)

    # 4. Contact sheets for fast visual QA
    vm_sample = [os.path.join(OUT_DIR, vm_idle_files[i]) for i in range(0, 60, 10)]
    vm_sample += [os.path.join(OUT_DIR, vm_fire_files[i]) for i in range(0, 20, 4)]
    vm_sample += [os.path.join(OUT_DIR, vm_reload_files[i]) for i in range(0, 18, 3)]
    _make_contact_sheet(vm_sample, os.path.join(OUT_DIR, "contact_vm.png"), cols=6, thumb_wh=(210, 180))

    proj_sample = [os.path.join(OUT_DIR, proj_files[a][0]) for a in range(16)]
    _make_contact_sheet(proj_sample, os.path.join(OUT_DIR, "contact_proj.png"), cols=4, thumb_wh=(160, 160))

    tp_sample = [os.path.join(OUT_DIR, tp_idle_files[i]) for i in range(0, 16, 4)]
    tp_sample += [os.path.join(OUT_DIR, tp_fire_files[i]) for i in range(0, 12, 2)]
    tp_sample += [os.path.join(OUT_DIR, tp_reload_files[i]) for i in range(0, 12, 3)]
    _make_contact_sheet(tp_sample, os.path.join(OUT_DIR, "contact_tp.png"), cols=5, thumb_wh=(160, 180))

    # 5. Manifest matching @html-sim spec
    bx, by = _pad_xy(*decomp["bell_center"])
    muzzle_norm = [round(bx / float(PADDED_WH[0]), 4), round(by / float(PADDED_WH[1]), 4)]
    manifest = {
        "title": "The Porcelain Poop-Tuba",
        "tagline": "Toilet Mortar & Strangelove Torpedo",
        "fps": 60,
        "muzzle_norm": muzzle_norm,
        "vm_wh": list(VM_WH),
        "proj_wh": list(PROJ_WH),
        "tp_wh": list(TP_WH),
        "vm_idle": vm_idle_files,
        "vm_fire": vm_fire_files,
        "vm_reload": vm_reload_files,
        "proj": {
            "angles": 16,
            "frames_per_angle": 6,
            "files": proj_files,
        },
        "tp_idle": tp_idle_files,
        "tp_fire": tp_fire_files,
        "tp_reload": tp_reload_files,
    }
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(
        f"[concept4_tuba] Done -> {OUT_DIR}: "
        f"vm_idle={len(vm_idle_files)}, vm_fire={len(vm_fire_files)}, vm_reload={len(vm_reload_files)}, "
        f"proj=16x6, tp_idle={len(tp_idle_files)}, tp_fire={len(tp_fire_files)}, tp_reload={len(tp_reload_files)}"
    )
    return manifest


if __name__ == "__main__":
    build_all()
