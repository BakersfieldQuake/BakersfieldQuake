"""Shared rig extraction, animation & FX helpers for the 4 escalating
forward-aiming Dookie Bazooka variants (MK-I through MK-IV).
"""
from __future__ import annotations

import glob
import math
import os
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from poop_core import WORK_DIR, from_premul, key_white_studio_plate, resize_premul, to_premul
from poop_fx import alpha_over, render_fly_swarm, render_tricolor_flag, warp_rgba

VM_WH = (420, 360)
PROJ_WH = (160, 180)
TP_WH = (320, 320)

DANCE_ANGLE_BANK: List[List[int]] = [
    [3, 5, 22, 30, 36, 40, 42, 44],
    [6, 8, 23, 25, 29, 31, 41, 45],
    [8, 9, 10, 24, 9, 10, 8, 24],
    [10, 11, 12, 11, 10, 11, 12, 11],
    [11, 12, 13, 12, 11, 12, 13, 12],
    [12, 13, 12, 11, 12, 13, 12, 13],
    [13, 14, 15, 14, 13, 14, 15, 14],
    [14, 15, 16, 15, 14, 15, 16, 15],
    [15, 16, 14, 15, 16, 14, 15, 16],
    [16, 15, 14, 16, 15, 14, 16, 15],
    [16, 19, 20, 19, 16, 19, 20, 19],
    [19, 20, 21, 20, 19, 20, 21, 20],
    [19, 20, 19, 21, 19, 20, 19, 21],
    [20, 21, 22, 21, 20, 21, 22, 21],
    [21, 22, 24, 25, 28, 32, 38, 42],
    [0, 2, 4, 22, 32, 34, 38, 46],
]


def load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def save_rgba(rgba: np.ndarray, path: str) -> None:
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def make_contact_sheet(
    frames: Sequence[np.ndarray],
    cols: int,
    cell_wh: Tuple[int, int],
    labels: Sequence[str] | None = None,
    bg_rgb: Tuple[int, int, int] = (34, 36, 42),
) -> np.ndarray:
    cw, ch = cell_wh
    rows = max(1, (len(frames) + cols - 1) // cols)
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (*bg_rgb, 255))
    draw = ImageDraw.Draw(sheet)
    for idx, fr in enumerate(frames):
        r, c = divmod(idx, cols)
        x0, y0 = c * cw, r * ch
        rs = resize_premul(fr, (cw, ch))
        pil_rs = Image.fromarray(rs, "RGBA")
        sheet.paste(pil_rs, (x0, y0), pil_rs)
        lbl = labels[idx] if labels is not None else str(idx)
        draw.text((x0 + 4, y0 + 3), lbl, fill=(255, 230, 80, 255))
    return np.asarray(sheet)


def load_shared_assets() -> Dict[str, Any]:
    """Load extracted cast heads, FX sprites, turnaround, dance loop, and enemy base."""
    heads: Dict[str, np.ndarray] = {}
    for p in sorted(glob.glob(os.path.join(WORK_DIR, "heads", "*.png"))):
        heads[os.path.splitext(os.path.basename(p))[0]] = load_rgba(p)

    fx: Dict[str, np.ndarray] = {}
    for p in sorted(glob.glob(os.path.join(WORK_DIR, "fx", "*.png"))):
        name = os.path.splitext(os.path.basename(p))[0]
        if not name.startswith("_verify"):
            fx[name] = load_rgba(p)

    turn_16 = [load_rgba(p) for p in sorted(glob.glob(os.path.join(WORK_DIR, "turn_16", "turn_*.png")))]
    dance_48 = [load_rgba(p) for p in sorted(glob.glob(os.path.join(WORK_DIR, "dance_48", "dance_*.png")))]
    enemy_base = load_rgba(os.path.join(WORK_DIR, "fx", "enemy_shooter_base.png"))

    torp_path = os.path.join(WORK_DIR, "fx", "poop_torpedo.png")
    torp_jpg = r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841\poop_torpedo_1794663387920.jpg"
    if os.path.exists(torp_path):
        torpedo = load_rgba(torp_path)
    elif os.path.exists(torp_jpg):
        torpedo = key_white_studio_plate(np.asarray(Image.open(torp_jpg).convert("RGB")))
    else:
        torpedo = fx["mud_glob_00"]

    return {
        "heads": heads,
        "fx": fx,
        "turn_16": turn_16,
        "dance_48": dance_48,
        "enemy_base": enemy_base,
        "torpedo": torpedo,
    }


def key_forward_cannon_rig(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Key a 1024x1024 forward-aiming cannon plate with surgical protection for PSI
    dials and porcelain, punch clear glass panes while retaining brass cage bars,
    inpaint static gauge needles, and separate the plunger muzzle for recoil squash.
    """
    rgb = np.asarray(Image.open(cfg["src_jpg"]).convert("RGB"))
    h, w = rgb.shape[:2]
    arr_f = rgb.astype(np.float32)
    hi = arr_f.max(axis=2)
    lo = arr_f.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr_f[..., 0] + 0.587 * arr_f[..., 1] + 0.114 * arr_f[..., 2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # 1. Outer background floodfill from corners (safe for white porcelain in Mk-III)
    bg_cand = ((lo > 224.0) & (sat < 0.085)) | (lum > 240.0)
    lbl, _ = ndimage.label(bg_cand)
    corner_labels = {
        int(lbl[0, 0]),
        int(lbl[0, w - 1]),
        int(lbl[h - 1, 0]),
        int(lbl[h - 1, w - 1]),
    } - {0}
    outer_bg = np.isin(lbl, list(corner_labels))
    outer_silhouette_bg = outer_bg.copy()

    # Knock out trapped studio holes only in allowed hole zones (excluding dials & porcelain)
    glass_poly = np.array(cfg["glass_poly"], dtype=np.int32)
    glass_poly_u8 = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(glass_poly_u8, [glass_poly], 255)
    glass_zone = glass_poly_u8 > 0

    protect = np.zeros((h, w), dtype=bool)
    for d in cfg["psi_dials"]:
        cx, cy = d["center"]
        r = d["radius"] + 6
        protect |= ((xx - cx) ** 2 + (yy - cy) ** 2) <= (r * r)
    for x0, y0, x1, y1 in cfg.get("protect_boxes", []):
        protect |= (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)

    trapped_bg = (~outer_bg) & (~protect) & (lo > 218.0) & (sat < 0.085)
    # Remove trapped bright islands >= 85 px (trigger guard, filigree crown loops, glass panes)
    t_lbl, t_n = ndimage.label(trapped_bg)
    if t_n > 0:
        sizes = ndimage.sum(trapped_bg, t_lbl, range(1, t_n + 1))
        for tidx, sz in enumerate(sizes, start=1):
            if sz >= 85:
                comp = t_lbl == tidx
                outer_bg |= comp

    # Anti-aliased soft alpha edge around removed studio background
    dist_fg = ndimage.distance_transform_edt(~outer_bg)
    alpha = np.clip((dist_fg - 0.15) * 180.0, 0.0, 255.0)
    # Softly clean 1px bright fringe next to keyed background
    fringe = (~outer_bg) & (dist_fg <= 1.6) & (lum > 205.0) & (sat < 0.14)
    alpha = np.where(fringe, np.minimum(alpha, (248.0 - lum) * 3.8), alpha)

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = np.clip(np.round(alpha), 0, 255).astype(np.uint8)
    rgba[rgba[..., 3] < 4] = 0

    # 2. Optional Mk-I left forearm nudge up onto the copper foregrip bar
    if cfg.get("nudge_left_arm"):
        dx_a, dy_a = cfg["nudge_left_arm"]
        la_mask = (xx < 462.0) & (yy > 532.0) & ((yy - 532.0) > (462.0 - xx) * -0.45)
        arm_only = np.zeros_like(rgba)
        arm_only[la_mask] = rgba[la_mask]
        rgba[la_mask] = 0
        # Shift arm cleanly + stretch bottom 40px edge down-left to cover bottom border seam
        arm_shifted = warp_rgba(arm_only, angle_deg=0.0, sx=1.0, sy=1.0, dx=dx_a, dy=dy_a, pivot=(200, 800), out_hw=(h, w))
        rgba = alpha_over(rgba, arm_shifted, 0, 0)

    # 3. Clean Telea inpaint of static gauge needles inside PSI dials
    bgr = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2BGR)
    for d in cfg["psi_dials"]:
        cx, cy = d["center"]
        rad = d["radius"]
        p0 = np.array(d["seg"][0], dtype=np.float32)
        p1 = np.array(d["seg"][1], dtype=np.float32)
        seg = p1 - p0
        seg_l2 = max(1.0, float(np.dot(seg, seg)))
        t_proj = np.clip(((xx - p0[0]) * seg[0] + (yy - p0[1]) * seg[1]) / seg_l2, 0.0, 1.0)
        dist_line = np.sqrt((xx - (p0[0] + t_proj * seg[0])) ** 2 + (yy - (p0[1] + t_proj * seg[1])) ** 2)
        dist_c = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        is_red = (arr_f[..., 0] - arr_f[..., 2]) > 38.0
        n_mask = (
            (dist_c <= rad - 3)
            & ((dist_c <= 6.5) | ((dist_line <= 5.5) & ((lum < 155.0) | is_red)))
        ).astype(np.uint8) * 255
        # Keep text labels above/below needle center untouched where clear of needle line
        n_mask = cv2.dilate(n_mask, np.ones((3, 3), np.uint8), iterations=1)
        bgr = cv2.inpaint(bgr, n_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    rgba[..., :3] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # 4. Build glass pane mask & translucent glare overlay INSIDE glass_zone (keeping brass bars!)
    glass_pane_raw = glass_zone & ((outer_bg & (~protect)) | ((lo > 205.0) & (sat < 0.14)))
    # Smooth pane mask slightly so glare highlights hug inside the brass rings
    glass_mask_f = cv2.GaussianBlur(glass_pane_raw.astype(np.float32), (5, 5), 1.0)
    # Remove any lingering semi-opaque bright haze on body inside glass panes
    rgba[..., 3] = np.clip(
        np.round(rgba[..., 3].astype(np.float32) * np.clip(1.0 - glass_mask_f * 1.15, 0.0, 1.0)),
        0,
        255,
    ).astype(np.uint8)
    rgba[rgba[..., 3] < 4] = 0

    # Curved cylinder specular highlight overlay drawn IN FRONT of heads
    gx0, gx1 = int(np.min(glass_poly[:, 0])), int(np.max(glass_poly[:, 0]))
    gy0, gy1 = int(np.min(glass_poly[:, 1])), int(np.max(glass_poly[:, 1]))
    gcx, gcy = 0.5 * (gx0 + gx1), 0.5 * (gy0 + gy1)
    ang = math.radians(24.0)
    ca, sa = math.cos(ang), math.sin(ang)
    ty = -(xx - gcx) * sa + (yy - gcy) * ca
    cyl_glare = np.exp(-0.5 * ((ty + 48.0) / 14.0) ** 2) * 92.0
    cyl_bot = np.exp(-0.5 * ((ty - 62.0) / 9.0) ** 2) * 52.0
    glass_overlay = np.zeros((h, w, 4), dtype=np.uint8)
    glass_overlay[..., 0] = 228
    glass_overlay[..., 1] = 244
    glass_overlay[..., 2] = 255
    glass_overlay[..., 3] = np.clip(np.round((cyl_glare + cyl_bot + 16.0) * glass_mask_f), 0, 145).astype(np.uint8)

    # Full glass fill polygon mask (includes behind cage bars so heads render naturally behind brass bars,
    # while clipped strictly inside outer gun silhouette so zero tank tint leaks outside the cylinder!)
    inside_gun = ndimage.binary_erosion(~outer_silhouette_bg, iterations=2)
    glass_poly_clipped = np.where(inside_gun, glass_poly_u8, 0).astype(np.uint8)
    glass_fill_f = cv2.GaussianBlur(glass_poly_clipped.astype(np.float32) / 255.0, (5, 5), 1.0)

    # 5. Segment red plunger muzzle cup for independent squash & stretch
    px_max, py_max, slope, y_off, x_cut = cfg["plunger_cut"]
    bound_x = x_cut + slope * (yy - y_off)
    plunger_w = np.clip((bound_x + 4.0 - xx) / 8.0, 0.0, 1.0) * ((xx < px_max) & (yy < py_max)).astype(np.float32)
    plunger_rgba = rgba.copy()
    plunger_rgba[..., 3] = np.clip(np.round(plunger_rgba[..., 3].astype(np.float32) * plunger_w), 0, 255).astype(np.uint8)
    plunger_rgba[plunger_rgba[..., 3] < 4] = 0

    body_no_plunger = rgba.copy()
    body_keep = np.clip((xx - (bound_x - 10.0)) / 8.0, 0.0, 1.0)
    body_keep = np.where((xx >= px_max) | (yy >= py_max), 1.0, body_keep)
    body_no_plunger[..., 3] = np.clip(np.round(body_no_plunger[..., 3].astype(np.float32) * body_keep), 0, 255).astype(np.uint8)
    body_no_plunger[body_no_plunger[..., 3] < 4] = 0

    return {
        "body": body_no_plunger,
        "full_body": rgba,
        "plunger": plunger_rgba,
        "glass_fill": glass_fill_f,
        "glass_overlay": glass_overlay,
        "glass_bbox": (gx0, gy0, gx1, gy1),
    }


def draw_psi_needles(canvas: np.ndarray, dials: List[Dict[str, Any]], angle_deg: float) -> np.ndarray:
    out = canvas.copy()
    for idx, d in enumerate(dials):
        cx, cy = d["center"]
        rad = float(d["radius"])
        ang = angle_deg + (16.0 if idx > 0 else 0.0)
        rad_a = math.radians(ang - 90.0)
        ca, sa = math.cos(rad_a), math.sin(rad_a)
        px, py = -sa, ca
        tip_len = rad * 0.78
        tail_len = rad * 0.28
        tip = (int(round(cx + ca * tip_len)), int(round(cy + sa * tip_len)))
        mid = (int(round(cx + ca * tip_len * 0.58)), int(round(cy + sa * tip_len * 0.58)))

        sh = np.array([[cx + px * 2.5 + 2, cy + py * 2.5 + 2], [cx - px * 2.5 + 2, cy - py * 2.5 + 2], [tip[0] + 2, tip[1] + 2]], dtype=np.int32)
        cv2.fillConvexPoly(out, sh, (35, 30, 20, 110), lineType=cv2.LINE_AA)

        body = np.array([
            [int(round(cx + px * 2.8 - ca * tail_len)), int(round(cy + py * 2.8 - sa * tail_len))],
            [int(round(cx - px * 2.8 - ca * tail_len)), int(round(cy - py * 2.8 - sa * tail_len))],
            [int(round(mid[0] - px * 1.3)), int(round(mid[1] - py * 1.3))],
            [int(round(mid[0] + px * 1.3)), int(round(mid[1] + py * 1.3))],
        ], dtype=np.int32)
        cv2.fillConvexPoly(out, body, (26, 26, 28, 255), lineType=cv2.LINE_AA)
        t_pts = np.array([
            [int(round(mid[0] - px * 2.2)), int(round(mid[1] - py * 2.2))],
            [int(round(mid[0] + px * 2.2)), int(round(mid[1] + py * 2.2))],
            tip,
        ], dtype=np.int32)
        cv2.fillConvexPoly(out, t_pts, (220, 42, 32, 255), lineType=cv2.LINE_AA)
        cv2.circle(out, (int(round(cx)), int(round(cy))), 5, (38, 34, 28, 255), -1, cv2.LINE_AA)
        cv2.circle(out, (int(round(cx)), int(round(cy))), 2, (205, 178, 95, 255), -1, cv2.LINE_AA)
    return out


def draw_brass_flagpole(canvas: np.ndarray, p0: Tuple[float, float], p1: Tuple[float, float], thickness: int = 7) -> np.ndarray:
    out = canvas.copy()
    x0, y0 = int(round(p0[0])), int(round(p0[1]))
    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    cv2.line(out, (x0, y0), (x1, y1), (32, 24, 12, 255), thickness + 4, cv2.LINE_AA)
    cv2.line(out, (x0, y0), (x1, y1), (172, 136, 56, 255), thickness, cv2.LINE_AA)
    cv2.line(out, (x0 - 1, y0), (x1 - 1, y1), (240, 212, 125, 255), max(2, thickness // 3), cv2.LINE_AA)
    cv2.circle(out, (x1, y1), thickness + 3, (32, 24, 12, 255), -1, cv2.LINE_AA)
    cv2.circle(out, (x1, y1), thickness + 1, (214, 174, 70, 255), -1, cv2.LINE_AA)
    return out


def render_tank_interior(
    rig: Dict[str, Any],
    cfg: Dict[str, Any],
    heads: Dict[str, np.ndarray],
    mode: str,
    f_idx: int,
    n_frames: int,
) -> np.ndarray:
    """Render translucent stink-liquid/reactor soup + N bouncing arguing heads inside `glass_bbox`."""
    glass_fill = rig["glass_fill"]
    x0, y0, x1, y1 = rig["glass_bbox"]
    h, w = glass_fill.shape
    chamber = np.zeros((h, w, 4), dtype=np.uint8)
    rw, rh = x1 - x0, y1 - y0
    roi = np.zeros((rh, rw, 4), dtype=np.uint8)

    t_norm = f_idx / float(max(1, n_frames))
    tau = 2.0 * math.pi

    # Stink fluid backdrop inside cylinder
    bg_rgb = cfg.get("tank_tint", (102, 122, 54))
    bg_a = cfg.get("tank_alpha", 118)
    roi[..., :3] = bg_rgb
    roi[..., 3] = bg_a

    # Sloshing green-brown poop soup wave (smooth slow slosh)
    slosh_amp = cfg.get("slosh_amp", 14.0)
    ry_g, rx_g = np.mgrid[0:rh, 0:rw].astype(np.float32)
    wave_ang = tau * (t_norm * 1.0 if mode == "idle" else f_idx * 0.25)
    liquid_line = rh * cfg.get("slosh_level", 0.62) + slosh_amp * np.sin(rx_g * 0.025 + wave_ang)
    if mode == "fire":
        liquid_line -= 26.0 * math.sin(math.pi * min(1.0, f_idx / 12.0))
    in_soup = ry_g >= liquid_line
    soup_col = cfg.get("soup_rgb", (92, 68, 24))
    soup_a = cfg.get("soup_alpha", 165)
    roi[in_soup, :3] = soup_col
    roi[in_soup, 3] = soup_a

    # Rising stink/reactor bubbles
    n_bub = cfg.get("n_bubbles", 14)
    bub_col = cfg.get("bubble_rgb", (185, 220, 96, 175))
    for b in range(n_bub):
        bx = 22.0 + ((b * 47) % max(24, rw - 44))
        by_cyc = (b * 0.13 + t_norm * (1.0 + (b % 2))) % 1.0
        by = rh - 10.0 - by_cyc * (rh - 20.0)
        br = 4 + (b % 5)
        cv2.circle(roi, (int(bx), int(by)), br, bub_col, -1, cv2.LINE_AA)

    # Render packed heads (calm, well-spaced, readable bobbing)
    head_slots = cfg["head_slots"]
    spin_crazy = cfg.get("head_spin", False)
    for idx, slot in enumerate(head_slots):
        ph = idx * 1.45
        imgs = [heads[k] for k in slot["keys"] if k in heads] or [heads["head_cross"]]
        if mode == "idle":
            bx = slot.get("amp_x", 6.0) * math.sin(tau * 1.0 * t_norm + ph)
            by = slot.get("amp_y", 7.0) * math.sin(tau * 1.0 * t_norm + ph * 1.3 + 0.6)
            tilt = (16.0 * math.sin(tau * 1.0 * t_norm + ph) if spin_crazy else slot.get("tilt", 0.0) * 0.6 + 8.5 * math.sin(tau * 1.0 * t_norm + ph))
            sx = 1.0 + 0.04 * math.sin(tau * 1.0 * t_norm + ph)
            sy = 1.0 / max(0.88, sx)
            h_im = imgs[int((t_norm * 2.0 + idx * 0.45)) % len(imgs)]
            sc_mul = 1.0
        elif mode == "fire":
            p = f_idx / float(max(1, n_frames - 1))
            env = math.sin(math.pi * min(1.0, p * 1.15))
            bx = 14.0 * env + 5.5 * math.sin(f_idx * 2.9 + idx * 2.1)
            by = -14.0 * env + 6.5 * math.cos(f_idx * 3.1 + idx * 2.4)
            tilt = (f_idx * (28.0 if idx % 2 == 0 else -28.0) if spin_crazy else 26.0 * math.sin(f_idx * 2.4 + ph))
            sx = 0.88 + 0.15 * math.sin(f_idx * 3.4 + idx)
            sy = 1.18 + 0.12 * math.cos(f_idx * 2.8 + idx)
            h_im = imgs[-1] if f_idx < 14 else imgs[0]
            sc_mul = 1.05
        else:  # reload: chamber vents & fresh angry head pops/bounces in
            p = f_idx / float(max(1, n_frames - 1))
            if idx == len(head_slots) - 1:
                u = max(0.0, (f_idx - 3) / float(max(1, n_frames - 4)))
                bounce = 1.0 - math.exp(-5.0 * u) * math.cos(u * math.pi * 3.0)
                bx = (1.0 - bounce) * 55.0
                by = -abs(math.sin(u * math.pi * 2.5)) * (1.0 - u) * 24.0
                tilt = (1.0 - u) * 32.0 * math.sin(u * math.pi * 3.0)
                sx = 1.0 + 0.18 * (1.0 - u) * math.sin(u * math.pi * 4.0)
                sy = 1.0 / max(0.75, sx)
                h_im = imgs[-1]
                sc_mul = 0.35 + 0.70 * bounce
            else:
                bx = -10.0 * math.sin(math.pi * p) + 4.0 * math.sin(f_idx * 1.5 + ph)
                by = 7.0 * math.sin(math.pi * p) + 5.0 * math.cos(f_idx * 1.7 + ph)
                tilt = 12.0 * math.sin(f_idx * 1.3 + ph)
                sx, sy = 1.0 + 0.06 * math.sin(f_idx + ph), 1.0 - 0.05 * math.sin(f_idx + ph)
                h_im = imgs[f_idx % len(imgs)]
                sc_mul = 1.0

        sz = max(28, int(round(slot["size"] * sc_mul)))
        h_rs = resize_premul(h_im, (sz, sz))
        pad = int(math.ceil(sz * 0.45))
        oh, ow = sz + 2 * pad, sz + 2 * pad
        h_pad = np.zeros((oh, ow, 4), dtype=np.uint8)
        h_pad[pad:pad + sz, pad:pad + sz] = h_rs
        warped = warp_rgba(h_pad, angle_deg=tilt, sx=sx, sy=sy, dx=0.0, dy=0.0, pivot=(ow * 0.5, oh * 0.5), out_hw=(oh, ow))
        roi = alpha_over(roi, warped, (slot["cx"] - x0) + bx - ow * 0.5, (slot["cy"] - y0) + by - oh * 0.5)

    roi_mask = glass_fill[y0:y1, x0:x1]
    roi[..., 3] = np.clip(np.round(roi[..., 3].astype(np.float32) * roi_mask), 0, 255).astype(np.uint8)
    roi[roi[..., 3] < 3] = 0
    chamber[y0:y1, x0:x1] = roi
    return chamber


def render_vm_sequence(
    rig: Dict[str, Any],
    cfg: Dict[str, Any],
    assets: Dict[str, Any],
    mode: str,
    n_frames: int,
) -> List[np.ndarray]:
    heads: Dict[str, np.ndarray] = assets["heads"]
    fx: Dict[str, np.ndarray] = assets["fx"]
    tau = 2.0 * math.pi
    SS_W, SS_H = VM_WH[0] * 2, VM_WH[1] * 2
    scale_gun = cfg.get("vm_scale", 0.72)
    base_ox, base_oy = cfg.get("vm_offset", (86.0, 48.0))
    plunger_piv = cfg["plunger_pivot"]
    recoil_mult = cfg.get("recoil_mult", 1.0)
    chakra = fx.get("chakra")

    frames: List[np.ndarray] = []
    for f_idx in range(n_frames):
        t_norm = f_idx / float(max(1, n_frames))

        if mode == "idle":
            recoil_dx = 3.0 * math.sin(tau * t_norm)
            recoil_dy = 4.5 * math.sin(tau * 1.0 * t_norm + 0.3)
            recoil_rot = 1.0 * math.sin(tau * t_norm + 0.4)
            plunger_sx, plunger_sy = 1.0 + 0.015 * math.sin(tau * 1.0 * t_norm), 1.0
            psi_ang = 78.0 + 18.0 * math.sin(tau * t_norm) + 6.0 * math.sin(tau * 4.0 * t_norm)
            flag_amp = 1.05 + 0.12 * math.sin(tau * t_norm)
            flag_phase = tau * 1.0 * t_norm
        elif mode == "fire":
            p = f_idx / float(max(1, n_frames - 1))
            if f_idx < 2:
                recoil_dx = -5.0 * (f_idx + 1)
                recoil_dy = 3.0 * (f_idx + 1)
                recoil_rot = 2.0 * (f_idx + 1)
                plunger_sx, plunger_sy = 0.74, 1.18
                psi_ang = 122.0 + 10.0 * f_idx
            else:
                k = (f_idx - 2) / float(max(1, n_frames - 3))
                kick = math.exp(-3.5 * k) * recoil_mult
                recoil_dx = 46.0 * kick
                recoil_dy = 34.0 * kick
                recoil_rot = -6.0 * kick
                snap = math.exp(-4.8 * k) * math.cos(k * math.pi * 3.5)
                plunger_sx = 1.0 + 0.24 * snap
                plunger_sy = 1.0 - 0.12 * snap
                psi_ang = 128.0 * (1.0 - min(1.0, k * 1.4)) - 118.0 * min(1.0, k * 1.4)
            flag_amp = 1.60 if f_idx < 10 else 1.24
            flag_phase = tau * (1.2 + 2.6 * p)
        else:  # reload
            p = f_idx / float(max(1, n_frames - 1))
            lift = math.sin(math.pi * p)
            recoil_dx = 18.0 * lift
            recoil_dy = 22.0 * lift
            recoil_rot = -6.5 * lift
            plunger_sx = 1.0 - 0.08 * math.sin(math.pi * 3.0 * p)
            plunger_sy = 1.0 + 0.06 * math.sin(math.pi * 3.0 * p)
            psi_ang = -118.0 + 185.0 * (p ** 0.75) + 15.0 * math.sin(p * math.pi * 6.0)
            flag_amp = 1.28
            flag_phase = tau * 2.0 * p

        # 1. Assemble 1024x1024 gun: tank interior -> stowaway/props -> body (incl cage bars) -> plunger -> glare -> PSI -> extras
        gun = render_tank_interior(rig, cfg, heads, mode, f_idx, n_frames)
        gun = alpha_over(gun, rig["body"], 0, 0)

        # Mk-III bonus: panicked stowaway bloke popping out of the open porcelain toilet bowl!
        if cfg.get("toilet_stowaway"):
            tx, ty, tsz = cfg["toilet_stowaway"]
            st_key = "head_sky_gasp" if (mode == "fire" and f_idx < 12) else ("head_side_yell_l" if int(t_norm * 4) % 2 else "head_oiled_yell")
            st_im = resize_premul(heads.get(st_key, heads["head_cross"]), (tsz, tsz))
            # Softly taper bottom edge so torso/neck sits inside toilet seat rim
            sy_g, _ = np.mgrid[0:tsz, 0:tsz].astype(np.float32)
            seat_fade = np.clip((tsz * 0.86 - sy_g) / (tsz * 0.16), 0.0, 1.0)
            st_im[..., 3] = np.clip(np.round(st_im[..., 3].astype(np.float32) * seat_fade), 0, 255).astype(np.uint8)
            st_dy = 14.0 * math.sin(math.pi * (f_idx / 12.0)) if mode == "fire" and f_idx < 12 else 6.0 * math.sin(tau * 3.0 * t_norm)
            st_rot = 15.0 * math.sin(tau * 2.0 * t_norm)
            st_w = warp_rgba(st_im, angle_deg=st_rot, sx=1.0, sy=1.0, dx=0.0, dy=0.0, pivot=(tsz * 0.5, tsz * 0.5), out_hw=(tsz, tsz))
            gun = alpha_over(gun, st_w, tx - tsz * 0.5, ty + st_dy - tsz * 0.5)

        plunger_w = warp_rgba(
            rig["plunger"],
            angle_deg=0.0,
            sx=plunger_sx,
            sy=plunger_sy,
            dx=0.0,
            dy=0.0,
            pivot=plunger_piv,
            out_hw=(1024, 1024),
        )
        gun = alpha_over(gun, plunger_w, 0, 0)
        gun = alpha_over(gun, rig["glass_overlay"], 0, 0)
        gun = draw_psi_needles(gun, cfg["psi_dials"], psi_ang)

        # Mk-IV spinning Navy Chakra wheel turbine on side of reactor!
        if cfg.get("chakra_wheel") and chakra is not None:
            wx, wy, wsz = cfg["chakra_wheel"]
            rot_deg = -(f_idx / float(max(1, n_frames))) * 360.0 * (1.0 if mode == "idle" else 2.5)
            wh_rs = resize_premul(chakra, (wsz, wsz))
            wh_w = warp_rgba(wh_rs, angle_deg=rot_deg, sx=1.0, sy=1.0, dx=0.0, dy=0.0, pivot=(wsz * 0.5, wsz * 0.5), out_hw=(wsz, wsz))
            gun = alpha_over(gun, wh_w, wx - wsz * 0.5, wy - wsz * 0.5, opacity=0.92)

        # Mk-IV pulsing toxic neon plasma glow overlay
        if cfg.get("neon_pulse"):
            pulse = 0.48 + 0.30 * math.sin(tau * 1.0 * t_norm)
            for gx, gy, gr in cfg["neon_pulse"]:
                glow = np.zeros((gr * 2, gr * 2, 4), dtype=np.uint8)
                cv2.circle(glow, (gr, gr), int(gr * 0.85), (120, 255, 70, int(140 * pulse)), -1, cv2.LINE_AA)
                glow = cv2.GaussianBlur(glow, (25, 25), 9.0)
                gun = alpha_over(gun, glow, gx - gr, gy - gr)

        # Sticky mud globs
        for g_idx, (gx, gy, gsz) in enumerate(cfg.get("mud_globs", [])):
            gim = resize_premul(fx[f"mud_glob_0{g_idx % 4}"], (gsz, gsz))
            gun = alpha_over(gun, gim, gx - gsz * 0.5, gy - gsz * 0.5, opacity=0.92)

        # Scale & recoil-warp into 840x720 supersampled canvas
        gw = int(round(1024 * scale_gun))
        gh = int(round(1024 * scale_gun))
        gun_rs = resize_premul(gun, (gw, gh))
        gun_ss = np.zeros((SS_H, SS_W, 4), dtype=np.uint8)
        gun_ss = alpha_over(gun_ss, gun_rs, base_ox, base_oy)
        pivot_ss = (SS_W * 0.45, SS_H * 1.12)
        gun_ss = warp_rgba(gun_ss, angle_deg=recoil_rot, sx=1.0, sy=1.0, dx=recoil_dx, dy=recoil_dy, pivot=pivot_ss, out_hw=(SS_H, SS_W))

        rad_r = math.radians(-recoil_rot)
        cr, sr = math.cos(rad_r), math.sin(rad_r)

        def _pt(x1024: float, y1024: float) -> Tuple[float, float]:
            px0 = base_ox + x1024 * scale_gun
            py0 = base_oy + y1024 * scale_gun
            vx, vy = px0 - pivot_ss[0], py0 - pivot_ss[1]
            return (
                pivot_ss[0] + vx * cr - vy * sr + recoil_dx,
                pivot_ss[1] + vx * sr + vy * cr + recoil_dy,
            )

        # 2. Render 2..4 waving saffron-white-green tricolor flags cleanly anchored & unclipped inside 840x720
        canvas_ss = np.zeros((SS_H, SS_W, 4), dtype=np.uint8)
        for fi, fl_spec in enumerate(cfg["flags"]):
            p0 = _pt(*fl_spec["anchor"])
            dx_p, dy_p = fl_spec["pole_vec"]
            p1 = (p0[0] + dx_p, p0[1] + dy_p)
            fw, fh = fl_spec["size"]
            pole_left = fl_spec["pole_left"]
            canvas_ss = draw_brass_flagpole(canvas_ss, p0, p1, thickness=fl_spec.get("thick", 7))
            fl = render_tricolor_flag(fw, fh, phase=flag_phase + fi * 1.15, pole_left=pole_left, amp=flag_amp)
            ang_f = fl_spec.get("angle", -5.0 if pole_left else 8.0)
            piv = (8.0, fh * 0.45) if pole_left else (fw - 8.0, fh * 0.45)
            pad_w, pad_h = fw + 32, fh + 44
            fl_r = warp_rgba(fl, angle_deg=ang_f, sx=1.0, sy=1.0, dx=0.0, dy=0.0, pivot=piv, out_hw=(pad_h, pad_w))
            fx_off = p1[0] - (8.0 if pole_left else fw + 22.0)
            fy_off = p1[1] - fh * 0.42
            canvas_ss = alpha_over(canvas_ss, fl_r, fx_off, fy_off)

        canvas_ss = alpha_over(canvas_ss, gun_ss, 0, 0)
        frame = resize_premul(canvas_ss, VM_WH)

        # 3. Muzzle fart blast & swarming flies (in 420x360 space)
        mz_ss = _pt(*cfg["muzzle_pt"])
        mz_vm = (mz_ss[0] * 0.5, mz_ss[1] * 0.5)
        gx0, gy0, gx1, gy1 = rig["glass_bbox"]
        tk_ss = _pt(0.5 * (gx0 + gx1), 0.5 * (gy0 + gy1))
        tk_vm = (tk_ss[0] * 0.5, tk_ss[1] * 0.5)

        if mode == "fire" and 2 <= f_idx <= 16:
            bf = (f_idx - 2) / 14.0
            b_mult = cfg.get("blast_mult", 1.0)
            m1 = fx[f"mist_0{(f_idx % 3) * 2 + 1}"]
            m2 = fx[f"mist_0{(f_idx % 3) * 2}"]
            s1 = int(round((88 + 115 * bf) * b_mult))
            s2 = int(round((68 + 86 * bf) * b_mult))
            op = max(0.0, 1.0 - bf * 0.90)
            frame = alpha_over(frame, resize_premul(m1, (s1, s1)), mz_vm[0] - s1 * 0.58 - 18.0 * bf, mz_vm[1] - s1 * 0.54 - 10.0 * bf, opacity=op)
            frame = alpha_over(frame, resize_premul(m2, (s2, s2)), mz_vm[0] - s2 * 0.48 - 8.0 * bf, mz_vm[1] - s2 * 0.46, opacity=op * 0.9)
            if f_idx <= 9:
                sp = fx[f"splat_0{f_idx % 4}"]
                sps = int(round((54 + 74 * (f_idx - 2) / 7.0) * b_mult))
                frame = alpha_over(frame, resize_premul(sp, (sps, sps)), mz_vm[0] - sps * 0.55, mz_vm[1] - sps * 0.50, opacity=max(0.0, 1.0 - (f_idx - 2) / 8.0))
            for g in range(4):
                gp = (f_idx - 2) / 14.0
                ang = math.radians(205.0 + (g - 1.5) * 20.0)
                dist = (14.0 + g * 10.0) + gp * (72.0 + g * 16.0)
                gx_p = mz_vm[0] + math.cos(ang) * dist
                gy_p = mz_vm[1] + math.sin(ang) * dist + 20.0 * gp * gp
                frame = alpha_over(frame, resize_premul(fx[f"mud_glob_0{g}"], (22, 22)), gx_p - 11, gy_p - 11, opacity=max(0.0, 1.0 - gp))

        fly_t = t_norm if mode == "idle" else (f_idx / 48.0) % 1.0
        frame = render_fly_swarm(
            frame,
            centers=[tk_vm],
            t_norm=fly_t,
            n_flies=cfg["n_flies"],
            scale=cfg.get("fly_scale", 0.92),
            calm=True,
            orbit_rx=(56.0, 92.0),
            orbit_ry=(34.0, 56.0),
        )
        frames.append(frame)
    return frames


def _clean_arm_hip_white_gaps(rgba: np.ndarray) -> np.ndarray:
    out = rgba.copy()
    h, w = out.shape[:2]
    rgb = out[..., :3].astype(np.float32)
    a = out[..., 3]
    hi, lo = rgb.max(axis=2), rgb.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    yy, xx = np.mgrid[0:h, 0:w]
    side_band = ((xx < int(w * 0.36)) | (xx > int(w * 0.64))) & (yy > int(h * 0.42)) & (yy < int(h * 0.80))
    gap = (a > 10) & side_band & (lo > 226.0) & (sat < 0.08)
    if np.any(gap):
        lbl, n = ndimage.label(gap)
        bg_dil = ndimage.binary_dilation(a < 20, iterations=3)
        for idx in range(1, n + 1):
            comp = lbl == idx
            if np.any(comp & bg_dil):
                out[comp] = 0
    return out


def _single_sprinting_bloke(turn_rgba: np.ndarray, dance_rgba: np.ndarray, angle_idx: int, f_idx: int, n_frames: int, spin_extra: float = 0.0) -> np.ndarray:
    th, tw = turn_rgba.shape[:2]
    dh, dw = dance_rgba.shape[:2]
    t_clean = _clean_arm_hip_white_gaps(turn_rgba)
    trgb = t_clean[..., :3].astype(np.float32)
    ta = t_clean[..., 3] > 30
    orange = ta & (trgb[..., 0] > 165) & (trgb[..., 1] > 60) & (trgb[..., 1] < 145) & (trgb[..., 2] < 75)
    oy = np.nonzero(orange)[0]
    waist_y = int(np.percentile(oy, 10)) if len(oy) > 20 else 210
    hem_y = 338
    ox = np.nonzero(orange)[1]
    t_mid_y0, t_mid_y1 = max(0, waist_y - 65), max(max(0, waist_y - 65) + 10, waist_y)
    _, tm_x = np.nonzero(ta[t_mid_y0:t_mid_y1, :])
    shorts_hw = float(np.percentile(ox, 96) - np.percentile(ox, 4)) * 0.52 if len(ox) > 20 else 66.0
    cx_body = 0.5 * float(np.percentile(tm_x, 4) + np.percentile(tm_x, 96)) if len(tm_x) > 40 else (0.5 * float(np.percentile(ox, 4) + np.percentile(ox, 96)) if len(ox) > 20 else tw * 0.5)

    drgb = dance_rgba[..., :3].astype(np.float32)
    da = dance_rgba[..., 3] > 30
    d_shorts = da & (((drgb[..., 0] > 165) & (drgb[..., 1] > 60) & (drgb[..., 1] < 145) & (drgb[..., 2] < 75)) | ((drgb[..., 1] > 80) & (drgb[..., 1] > drgb[..., 0] + 15) & (drgb[..., 1] > drgb[..., 2] + 20)))
    dox = np.nonzero(d_shorts)[1]
    d_hw = float(np.percentile(dox, 96) - np.percentile(dox, 4)) * 0.52 if len(dox) > 40 else shorts_hw
    d_scale = float(np.clip(shorts_hw / max(20.0, d_hw), 0.96, 1.14))
    dance_scaled = resize_premul(dance_rgba, (int(round(dw * d_scale)), int(round(dh * d_scale)))) if abs(d_scale - 1.0) > 0.015 else dance_rgba
    dh, dw = dance_scaled.shape[:2]
    drgb = dance_scaled[..., :3].astype(np.float32)
    da = dance_scaled[..., 3] > 30
    d_shorts = da & (((drgb[..., 0] > 165) & (drgb[..., 1] > 60) & (drgb[..., 1] < 145) & (drgb[..., 2] < 75)) | ((drgb[..., 1] > 80) & (drgb[..., 1] > drgb[..., 0] + 15) & (drgb[..., 1] > drgb[..., 2] + 20)))
    doy, dox = np.nonzero(d_shorts)
    d_waist_y = int(np.percentile(doy, 4)) if len(doy) > 40 else int(225 * d_scale)
    mid_y0, mid_y1 = max(0, d_waist_y - 70), max(max(0, d_waist_y - 70) + 10, d_waist_y)
    _, mtx = np.nonzero(da[mid_y0:mid_y1, :])
    d_cx = 0.5 * float(np.percentile(mtx, 4) + np.percentile(mtx, 96)) if len(mtx) > 40 else (0.5 * float(np.percentile(dox, 4) + np.percentile(dox, 96)) if len(dox) > 40 else dw * 0.5)

    CW, CH = 380, 480
    phase = 2.0 * math.pi * (f_idx / float(n_frames))
    stride, stride_opp = math.sin(phase), math.sin(phase + math.pi)
    bounce_y = -abs(math.sin(phase)) * 22.0
    ang_rad = 2.0 * math.pi * angle_idx / 16.0
    face_x = -math.sin(ang_rad)
    lean_deg = -10.5 * face_x - 3.5 * math.cos(phase) + spin_extra

    # Side-profile poses have overlapping legs along X, so keep the full unified dance_scaled silhouette cleanly.
    if (3 <= angle_idx <= 5) or (11 <= angle_idx <= 13):
        full_pad = np.zeros((CH, CW, 4), dtype=np.uint8)
        u_ox, u_oy = int(round(CW * 0.5 - d_cx)), int(round(14 + waist_y - d_waist_y))
        sx0, sy0 = max(0, -u_ox), max(0, -u_oy)
        dx0, dy0 = max(0, u_ox), max(0, u_oy)
        cw_p, ch_p = min(dw - sx0, CW - dx0), min(dh - sy0, CH - dy0)
        if cw_p > 0 and ch_p > 0:
            full_pad[dy0:dy0 + ch_p, dx0:dx0 + cw_p] = dance_scaled[sy0:sy0 + ch_p, sx0:sx0 + cw_p]
        side_lean = lean_deg + 8.0 * stride
        return warp_rgba(
            full_pad,
            angle_deg=side_lean,
            sx=1.0 + 0.04 * math.sin(phase),
            sy=1.0 - 0.04 * abs(math.cos(phase)),
            dx=10.0 * face_x + 4.0 * math.cos(phase),
            dy=bounce_y,
            pivot=(CW * 0.5, CH * 0.55),
            out_hw=(CH, CW),
        )

    yy_t, xx_t = np.mgrid[0:th, 0:tw]
    def _mask(src: np.ndarray, m: np.ndarray) -> np.ndarray:
        out = src.copy(); out[~m] = 0; return out

    leg_l = _mask(t_clean, (yy_t >= hem_y - 4) & (xx_t < cx_body))
    leg_r = _mask(t_clean, (yy_t >= hem_y - 4) & (xx_t >= cx_body))
    shorts_core = _mask(t_clean, (yy_t >= waist_y - 4) & (yy_t < hem_y + 2) & (np.abs(xx_t - cx_body) <= max(46.0, shorts_hw * 1.15)))

    leg_l_p, leg_r_p, sh_p = np.zeros((CH, CW, 4), dtype=np.uint8), np.zeros((CH, CW, 4), dtype=np.uint8), np.zeros((CH, CW, 4), dtype=np.uint8)
    ox_p, oy_p = int(round(CW * 0.5 - cx_body)), 14
    leg_l_p[oy_p:oy_p + th, ox_p:ox_p + tw] = leg_l
    leg_r_p[oy_p:oy_p + th, ox_p:ox_p + tw] = leg_r
    sh_p[oy_p:oy_p + th, ox_p:ox_p + tw] = shorts_core
    hip_px, hip_py = CW * 0.5, oy_p + float(hem_y - 4)

    leg_l_w = warp_rgba(leg_l_p, angle_deg=stride * (22.0 * abs(face_x) + 10.0), sx=1.0, sy=1.0 - 0.16 * max(0.0, stride), dx=stride * 10.0 * face_x, dy=-max(0.0, stride) * 28.0 + max(0.0, -stride) * 5.0, pivot=(hip_px - 22, hip_py), out_hw=(CH, CW))
    leg_r_w = warp_rgba(leg_r_p, angle_deg=stride_opp * (22.0 * abs(face_x) + 10.0), sx=1.0, sy=1.0 - 0.16 * max(0.0, stride_opp), dx=stride_opp * 10.0 * face_x, dy=-max(0.0, stride_opp) * 28.0 + max(0.0, -stride_opp) * 5.0, pivot=(hip_px + 22, hip_py), out_hw=(CH, CW))

    dy_g, _ = np.mgrid[0:dh, 0:dw].astype(np.float32)
    upper_w = np.clip((float(d_waist_y + (2 if 5 <= angle_idx <= 11 else 16)) - dy_g) / (14.0 if 5 <= angle_idx <= 11 else 22.0), 0.0, 1.0)
    upper = dance_scaled.copy()
    upper[..., 3] = np.clip(np.round(upper[..., 3].astype(np.float32) * upper_w), 0, 255).astype(np.uint8)
    upper[upper[..., 3] < 4] = 0

    up_pad = np.zeros((CH, CW, 4), dtype=np.uint8)
    u_ox, u_oy = int(round(CW * 0.5 - d_cx)), int(round(oy_p + waist_y - d_waist_y))
    sx0, sy0 = max(0, -u_ox), max(0, -u_oy)
    dx0, dy0 = max(0, u_ox), max(0, u_oy)
    cw_p, ch_p = min(dw - sx0, CW - dx0), min(dh - sy0, CH - dy0)
    if cw_p > 0 and ch_p > 0:
        up_pad[dy0:dy0 + ch_p, dx0:dx0 + cw_p] = upper[sy0:sy0 + ch_p, sx0:sx0 + cw_p]

    up_w = warp_rgba(up_pad, angle_deg=2.5 * math.sin(phase), sx=1.0 + 0.04 * math.sin(phase * 2.0), sy=1.0 - 0.02 * math.sin(phase * 2.0), dx=0.0, dy=0.0, pivot=(CW * 0.5, oy_p + waist_y), out_hw=(CH, CW))
    body = np.zeros((CH, CW, 4), dtype=np.uint8)
    body = alpha_over(body, leg_l_w, 0, 0)
    body = alpha_over(body, leg_r_w, 0, 0)
    if 5 <= angle_idx <= 11:
        body = alpha_over(body, up_w, 0, 0); body = alpha_over(body, sh_p, 0, 0)
    else:
        body = alpha_over(body, sh_p, 0, 0); body = alpha_over(body, up_w, 0, 0)
    return warp_rgba(body, angle_deg=lean_deg, sx=1.0, sy=1.0, dx=10.0 * face_x, dy=bounce_y, pivot=(CW * 0.5, CH * 0.55), out_hw=(CH, CW))


def render_proj_sequence(assets: Dict[str, Any], variant_kind: str, out_dir: str) -> List[List[str]]:
    """Render escalating 16-angle x 8-frame projectiles per Dookie Bazooka tier."""
    turn_16: List[np.ndarray] = assets["turn_16"]
    dance_48: List[np.ndarray] = assets["dance_48"]
    fx: Dict[str, np.ndarray] = assets["fx"]
    torp = assets["torpedo"]
    chakra = fx.get("chakra")

    n_angles, n_frames = len(turn_16), 8
    files: List[List[str]] = []
    for a in range(n_angles):
        row_files: List[str] = []
        d_choices = DANCE_ANGLE_BANK[a]
        ang_rad = 2.0 * math.pi * a / 16.0
        face_x = -math.sin(ang_rad)
        for f in range(n_frames):
            d_idx = d_choices[f % len(d_choices)]
            ph = 2.0 * math.pi * f / n_frames

            if variant_kind == "sprint":
                body = _single_sprinting_bloke(turn_16[a], dance_48[d_idx], a, f, n_frames)
                proj = resize_premul(body, PROJ_WH)
                proj = alpha_over(proj, resize_premul(fx[f"mud_glob_0{(a+f)%4}"], (24, 24)), PROJ_WH[0] * 0.45, PROJ_WH[1] * 0.44, opacity=0.88)
                proj = render_fly_swarm(proj, [(PROJ_WH[0] * 0.5, PROJ_WH[1] * 0.36)], t_norm=f / 8.0, n_flies=4, scale=0.32, calm=True, orbit_rx=(24.0, 42.0), orbit_ry=(16.0, 28.0))

            elif variant_kind == "turbo":
                # Crazier: ONE wide-waving mud-splattered bloke with billowing tricolor flag
                body = _single_sprinting_bloke(turn_16[a], dance_48[d_idx], a, f, n_frames, spin_extra=10.0 * math.sin(ph))
                proj = resize_premul(body, PROJ_WH)
                fl = render_tricolor_flag(46, 28, phase=ph, pole_left=True, amp=1.25)
                proj = alpha_over(proj, fl, PROJ_WH[0] * 0.52, PROJ_WH[1] * 0.44)
                proj = alpha_over(proj, resize_premul(fx[f"mud_glob_0{f%4}"], (28, 28)), PROJ_WH[0] * 0.5 - 14 - face_x * 16, PROJ_WH[1] * 0.62, opacity=0.85)
                proj = render_fly_swarm(proj, [(PROJ_WH[0] * 0.5, PROJ_WH[1] * 0.36)], t_norm=f / 8.0, n_flies=4, scale=0.34, calm=True, orbit_rx=(24.0, 42.0), orbit_ry=(16.0, 28.0))

            elif variant_kind == "torpedo":
                # Craziest #3: ONE wildly-waving fat guy trailing royal tricolor banner + mud splashes
                body = _single_sprinting_bloke(turn_16[a], dance_48[d_idx], a, f, n_frames, spin_extra=8.0 * math.cos(ph))
                fl = render_tricolor_flag(52, 32, phase=ph, pole_left=False, amp=1.3)
                proj = resize_premul(body, PROJ_WH)
                proj = alpha_over(proj, fl, 14, 24 + 4.0 * math.sin(ph), opacity=0.92)
                proj = alpha_over(proj, resize_premul(fx[f"splat_0{f%4}"], (44, 44)), PROJ_WH[0] * 0.46, PROJ_WH[1] * 0.68, opacity=0.78)
                proj = render_fly_swarm(proj, [(PROJ_WH[0] * 0.5, PROJ_WH[1] * 0.35)], t_norm=f / 8.0, n_flies=5, scale=0.35, calm=True, orbit_rx=(24.0, 42.0), orbit_ry=(16.0, 28.0))

            else:  # "cyclone": ONE mega-waving screaming fat guy with toxic stink halo, tricolor cape & tracking flies!
                proj = np.zeros((PROJ_WH[1], PROJ_WH[0], 4), dtype=np.uint8)
                glow = np.zeros((140, 140, 4), dtype=np.uint8)
                cv2.circle(glow, (70, 70), 50, (115, 225, 48, 130), -1, cv2.LINE_AA)
                glow = cv2.GaussianBlur(glow, (23, 23), 9.0)
                proj = alpha_over(proj, glow, PROJ_WH[0] * 0.5 - 70, PROJ_WH[1] * 0.5 - 70)
                fl = render_tricolor_flag(52, 32, phase=ph, pole_left=(face_x >= 0), amp=1.3)
                proj = alpha_over(proj, fl, PROJ_WH[0] * 0.5 - 26 - face_x * 20, 26 + 4.0 * math.sin(ph), opacity=0.90)
                body = _single_sprinting_bloke(turn_16[a], dance_48[d_idx], a, f, n_frames, spin_extra=12.0 * math.sin(ph))
                proj = alpha_over(proj, resize_premul(body, PROJ_WH), 0, 0)
                proj = alpha_over(proj, resize_premul(fx[f"mud_glob_0{(a+f)%4}"], (26, 26)), PROJ_WH[0] * 0.46, PROJ_WH[1] * 0.58, opacity=0.86)
                proj = render_fly_swarm(proj, [(PROJ_WH[0] * 0.5, PROJ_WH[1] * 0.34)], t_norm=f / 8.0, n_flies=5, scale=0.36, calm=True, orbit_rx=(24.0, 42.0), orbit_ry=(16.0, 28.0))

            fname = f"proj_a{a:02d}_f{f:02d}.png"
            save_rgba(proj, os.path.join(out_dir, fname))
            row_files.append(fname)
        files.append(row_files)
    return files


def render_tp_sequence(
    rig: Dict[str, Any],
    cfg: Dict[str, Any],
    assets: Dict[str, Any],
    mode: str,
    n_frames: int,
) -> List[np.ndarray]:
    """Render 3rd-person enemy shooter holding the redesigned forward oversized-tank cannon."""
    enemy_full: np.ndarray = assets["enemy_base"]
    heads: Dict[str, np.ndarray] = assets["heads"]
    fx: Dict[str, np.ndarray] = assets["fx"]
    chakra = fx.get("chakra")

    enemy_rs = resize_premul(enemy_full, (226, 236))
    eh, ew = enemy_rs.shape[:2]
    yy_e, xx_e = np.mgrid[0:eh, 0:ew].astype(np.float32)
    is_skin = (enemy_rs[..., 0].astype(np.float32) - enemy_rs[..., 2].astype(np.float32)) > 16.0
    d_l = np.sqrt(((xx_e - 52.0) / 18.0) ** 2 + ((yy_e - 81.0) / 16.0) ** 2)
    d_r = np.sqrt(((xx_e - 148.0) / 17.0) ** 2 + ((yy_e - 93.0) / 16.0) ** 2)
    w_hands = np.clip(1.35 - np.minimum(d_l, d_r), 0.0, 1.0) * is_skin.astype(np.float32)
    hands_fg = enemy_rs.copy()
    hands_fg[..., 3] = np.clip(np.round(hands_fg[..., 3].astype(np.float32) * w_hands), 0, 255).astype(np.uint8)
    hands_fg[hands_fg[..., 3] < 4] = 0

    tau = 2.0 * math.pi
    frames: List[np.ndarray] = []
    for f_idx in range(n_frames):
        t_norm = f_idx / float(max(1, n_frames))
        if mode == "idle":
            bob_y = 3.0 * math.sin(tau * 2.0 * t_norm)
            sway_x = 2.5 * math.sin(tau * t_norm)
            gun_dy = 3.5 * math.sin(tau * 2.0 * t_norm + 0.4)
            gun_rot = 1.5 * math.sin(tau * t_norm)
            plunger_sx = 1.0
            flag_amp, flag_phase = 1.08, tau * 2.0 * t_norm
        elif mode == "fire":
            p = f_idx / float(max(1, n_frames - 1))
            kick = math.exp(-3.8 * p) if f_idx >= 2 else -0.25
            bob_y, sway_x = 6.0 * kick, 4.0 * kick
            gun_dy, gun_rot = 8.0 * kick, -8.5 * kick
            plunger_sx = 0.76 if f_idx < 2 else (1.0 + 0.22 * math.exp(-4.5 * p) * math.cos(p * math.pi * 3.0))
            flag_amp, flag_phase = 1.55, tau * (1.0 + 2.4 * p)
        else:
            p = f_idx / float(max(1, n_frames - 1))
            lift = math.sin(math.pi * p)
            bob_y, sway_x = 4.0 * lift, 3.0 * lift
            gun_dy, gun_rot = -8.0 * lift, -11.5 * lift
            plunger_sx = 0.94
            flag_amp, flag_phase = 1.25, tau * 2.0 * p

        # Build the variant's own cannon + big crowded heads tank (excluding bottom-right 1P arms!)
        gun_raw = render_tank_interior(rig, cfg, heads, mode, f_idx, n_frames)
        if cfg.get("toilet_stowaway"):
            tx, ty, tsz = cfg["toilet_stowaway"]
            gun_raw = alpha_over(gun_raw, resize_premul(heads["head_oiled_yell"], (tsz, tsz)), tx - tsz * 0.5, ty - tsz * 0.5)
        gun_raw = alpha_over(gun_raw, rig["body"], 0, 0)
        pl_w = warp_rgba(rig["plunger"], angle_deg=0.0, sx=plunger_sx, sy=1.0 + (1.0 - plunger_sx) * 0.4, dx=0.0, dy=0.0, pivot=cfg["plunger_pivot"], out_hw=(1024, 1024))
        gun_raw = alpha_over(gun_raw, pl_w, 0, 0)
        gun_raw = alpha_over(gun_raw, rig["glass_overlay"], 0, 0)
        gun_raw = draw_psi_needles(gun_raw, cfg["psi_dials"], 75.0 if mode == "idle" else 120.0)
        if cfg.get("chakra_wheel") and chakra is not None:
            wx, wy, wsz = cfg["chakra_wheel"]
            cw = warp_rgba(resize_premul(chakra, (wsz, wsz)), angle_deg=-f_idx * 15.0, sx=1.0, sy=1.0, dx=0.0, dy=0.0, pivot=(wsz * 0.5, wsz * 0.5), out_hw=(wsz, wsz))
            gun_raw = alpha_over(gun_raw, cw, wx - wsz * 0.5, wy - wsz * 0.5)

        # Crop out bottom 1P gauntlets cleanly via diagonal fade
        gy_g, gx_g = np.mgrid[0:1024, 0:1024].astype(np.float32)
        keep_gun = np.clip((635.0 - (gy_g - (gx_g - 500.0) * 0.35)) / 36.0, 0.0, 1.0)
        # On Mk-III preserve porcelain toilet bowl cleanly, tapering pedestal bottom above knees!
        if cfg.get("keep_toilet_3p"):
            bowl_fade = np.clip((685.0 - gy_g) / 60.0, 0.0, 1.0)
            in_bowl = (gx_g >= 80) & (gx_g <= 560) & (gy_g <= 695)
            keep_gun = np.where(in_bowl & (gx_g > 210), np.maximum(keep_gun, bowl_fade), keep_gun)
            keep_gun = np.where((gx_g < 360) & (gy_g > 640), 0.0, keep_gun)
        gun_raw[..., 3] = np.clip(np.round(gun_raw[..., 3].astype(np.float32) * keep_gun), 0, 255).astype(np.uint8)
        gun_raw[gun_raw[..., 3] < 4] = 0
        crop = gun_raw[35:935, 30:1005]
        # Foreshorten into enemy's hands pointing down-left toward camera!
        ch, cw = crop.shape[:2]
        src_pts = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]])
        dst_pts = np.float32([[0, 26], [cw * 0.72, 0], [cw * 0.76, ch * 0.90], [18, ch * 1.04]])
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        persp = cv2.warpPerspective(to_premul(crop), M, (int(cw * 0.78), int(ch * 1.06)), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        gun_3p = resize_premul(from_premul(persp), (225, 165))
        gun_3p = warp_rgba(gun_3p, angle_deg=gun_rot - 4.0, sx=1.0, sy=1.0, dx=0.0, dy=0.0, pivot=(112, 82), out_hw=(165, 225))

        canvas = np.zeros((TP_WH[1], TP_WH[0], 4), dtype=np.uint8)
        ex = (TP_WH[0] - ew) * 0.5 + sway_x
        ey = TP_WH[1] - eh - 6 + bob_y

        # Escalating 2..4 tricolor flags flanking enemy!
        n_tp_flags = min(4, len(cfg["flags"]))
        flag_spots = [
            ((ex + 62, ey + 96), (ex + 42, ey - 42), False, (84, 52)),
            ((ex + 168, ey + 92), (ex + 184, ey - 38), True, (84, 52)),
            ((ex + 92, ey + 82), (ex + 96, ey - 58), True, (68, 42)),
            ((ex + 138, ey + 84), (ex + 136, ey - 56), False, (68, 42)),
        ]
        for fi in range(n_tp_flags):
            p0, p1, p_left, (fw, fh) = flag_spots[fi]
            canvas = draw_brass_flagpole(canvas, p0, p1, thickness=3)
            fl = render_tricolor_flag(fw, fh, phase=flag_phase + fi * 1.1, pole_left=p_left, amp=flag_amp)
            canvas = alpha_over(canvas, fl, p1[0] - (6 if p_left else fw - 6), p1[1] - 4)

        canvas = alpha_over(canvas, enemy_rs, ex, ey)
        gx, gy = ex + 4 + sway_x * 0.5, ey + 14 + gun_dy
        canvas = alpha_over(canvas, gun_3p, gx, gy)
        canvas = alpha_over(canvas, hands_fg, ex, ey)

        muzzle_tp = (gx + 34.0, gy + 44.0)
        if mode == "fire" and 2 <= f_idx <= 16:
            bf = (f_idx - 2) / 14.0
            m_puff = resize_premul(fx[f"mist_0{(f_idx % 3) * 2 + 1}"], (int(72 + 115 * bf), int(72 + 115 * bf)))
            canvas = alpha_over(canvas, m_puff, muzzle_tp[0] - m_puff.shape[1] * 0.5 - 10 * bf, muzzle_tp[1] - m_puff.shape[0] * 0.5 + 8 * bf, opacity=max(0.0, 1.0 - bf * 0.88))
            if f_idx <= 10:
                sp = resize_premul(fx[f"splat_0{f_idx % 4}"], (int(50 + 82 * bf), int(50 + 82 * bf)))
                canvas = alpha_over(canvas, sp, muzzle_tp[0] - sp.shape[1] * 0.5, muzzle_tp[1] - sp.shape[0] * 0.5, opacity=max(0.0, 1.0 - (f_idx - 2) / 9.0))

        canvas = render_fly_swarm(
            canvas,
            centers=[(ex + ew * 0.56, ey + 66.0)],
            t_norm=t_norm if mode == "idle" else (f_idx / 48.0) % 1.0,
            n_flies=min(7, max(4, cfg["n_flies"])),
            scale=0.80,
            calm=True,
            orbit_rx=(42.0, 68.0),
            orbit_ry=(28.0, 44.0),
        )
        frames.append(canvas)
    return frames
