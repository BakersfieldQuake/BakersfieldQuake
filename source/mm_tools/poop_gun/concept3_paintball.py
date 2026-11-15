"""Design 3: "THE POOP PAINTBALL HOPPER GUN" (Face-Tube Marker) sprite & viewmodel generator.

Generates all 60-FPS animated assets for Concept 3 in `source/mm_tools/poop_gun/work/c3_paintball/`:
  - First-person viewmodel (420x360 RGBA):
      * 60 idle frames (`vm_idle_00..59.png`)
      * 18 rapid-fire recoil frames (`vm_fire_00..17.png`)
      * 18 hopper-shake reload frames (`vm_reload_00..17.png`)
  - Projectile (220x220 RGBA):
      * 24 rapid-spinning mud-drenched yelling face paintball orb frames (`proj_00..23.png`)
  - 3rd-person enemy shooter (420x440 RGBA):
      * 24 idle aim frames (`tp_idle_00..23.png`)
      * 16 firing burst frames (`tp_fire_00..15.png`)
      * 16 hopper-shake reload frames (`tp_reload_00..15.png`)
  - `manifest.json` and `_contact_sheet.png` for HTML5 simulator packing & visual QA.

Run:
    py -3.13 source/mm_tools/poop_gun/concept3_paintball.py
"""
from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

from poop_core import WORK_DIR, from_premul, resize_premul, to_premul
from poop_fx import (
    alpha_over,
    render_fly_swarm,
    render_tricolor_flag,
    warp_rgba,
)

PAINTBALL_PLATE_PATH = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841"
    r"\paintball_gun_c3_1794663536726.jpg"
)
OUT_DIR = os.path.join(WORK_DIR, "c3_paintball")

VM_W, VM_H = 420, 360
PROJ_SZ = 220
TP_W, TP_H = 420, 440

# Head roster packed into the clear gravity-feed hopper tube (back-to-front draw order)
HEAD_ORDER = [
    "head_scream_front",  # top-right back pocket
    "head_sky_gasp",      # mid-back gasping up
    "head_oiled_yell",    # upper-middle yelling
    "head_wide_grin",     # upper-right pressed against lid
    "head_turban_grin",   # center grinning bloke
    "head_turban_yell",   # lower-mid turban yelling
    "head_cross",         # bottom-left feed-neck cross-eyed bloke
]


def _load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def _crop_alpha_tight(rgba: np.ndarray, pad: int = 2) -> np.ndarray:
    ys, xs = np.nonzero(rgba[..., 3] > 12)
    if len(xs) == 0:
        return rgba
    h, w = rgba.shape[:2]
    x0 = max(0, int(xs.min()) - pad)
    y0 = max(0, int(ys.min()) - pad)
    x1 = min(w, int(xs.max()) + 1 + pad)
    y1 = min(h, int(ys.max()) + 1 + pad)
    return rgba[y0:y1, x0:x1].copy()


def _clean_head_edge(rgba: np.ndarray) -> np.ndarray:
    """Remove any faint white chin-fade spill from video-extracted heads."""
    out = rgba.copy()
    arr = out.astype(np.float32)
    a = arr[..., 3] / 255.0
    # Un-premultiply semi-transparent edges against white where alpha < 0.92
    semi = (a > 0.04) & (a < 0.92)
    if np.any(semi):
        inv = 1.0 - a[semi]
        denom = np.maximum(a[semi], 0.25)
        arr[..., :3][semi] = np.clip((arr[..., :3][semi] - inv[:, None] * 255.0) / denom[:, None], 0.0, 255.0)
    # Sharpen soft outer alpha fade so chin bottom never shows milky halo
    a_sharp = np.clip((a - 0.35) / 0.50, 0.0, 1.0)
    out[..., :3] = np.clip(np.round(arr[..., :3]), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a_sharp * 255.0), 0, 255).astype(np.uint8)
    out[out[..., 3] < 8] = 0
    return out


def _load_heads() -> Dict[str, np.ndarray]:
    heads_dir = os.path.join(WORK_DIR, "heads")
    out: Dict[str, np.ndarray] = {}
    for name in HEAD_ORDER:
        p = os.path.join(heads_dir, f"{name}.png")
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Missing cached head sprite: {p}")
        im = _clean_head_edge(_load_rgba(p))
        im = _crop_alpha_tight(im, pad=2)
        out[name] = im
    return out


def _load_fx_bank() -> Dict[str, List[np.ndarray]]:
    fx_dir = os.path.join(WORK_DIR, "fx")
    globs = [_load_rgba(os.path.join(fx_dir, f"mud_glob_{i:02d}.png")) for i in range(4)]
    splats = [_load_rgba(os.path.join(fx_dir, f"splat_{i:02d}.png")) for i in range(4)]
    mists = [_load_rgba(os.path.join(fx_dir, f"mist_{i:02d}.png")) for i in range(6)]
    enemy = _load_rgba(os.path.join(fx_dir, "enemy_shooter_base.png"))
    return {"globs": globs, "splats": splats, "mists": mists, "enemy": enemy}


def extract_paintball_layers() -> Dict[str, np.ndarray]:
    """Key `paintball_gun_c3_1794663536726.jpg` cleanly into layered RGBA plates:
    - `gun_body`: opaque marker, hand/gauntlet, CO2 tank, feed clamp, barrel (with tube cleared)
    - `hopper_back`: subtle translucent acrylic rear wall behind the packed faces
    - `hopper_front`: glossy acrylic front wall, refraction rims, lid ellipse & specular sheen
    - `tube_clip`: uint8 mask (0..255) defining the smooth interior cylinder where faces live
    - `bolt_patch`: extracted brass/steel side-gear & bolt assembly for firing recoil animation
    """
    if not os.path.isfile(PAINTBALL_PLATE_PATH):
        raise FileNotFoundError(f"Missing paintball plate: {PAINTBALL_PLATE_PATH}")

    rgb = np.asarray(Image.open(PAINTBALL_PLATE_PATH).convert("RGB"))
    h, w = rgb.shape[:2]
    arr = rgb.astype(np.float32)
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    # 1. Border-connected exterior white flood-fill.
    # Use slight morphological closing on dark boundary so the thin acrylic top rim blocks flood-fill.
    cand_bg = (lo > 236.0) & (sat < 0.075)
    barrier = ~cand_bg
    barrier_closed = cv2.morphologyEx(
        barrier.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)
    ) > 0
    ext_cand = ~barrier_closed
    lbl, _ = ndimage.label(ext_cand)
    border_ids = (
        set(np.unique(lbl[0, :]))
        | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0]))
        | set(np.unique(lbl[:, -1]))
    )
    border_ids.discard(0)
    ext_bg = np.isin(lbl, list(border_ids))
    # Dilate exterior back into raw white pixels only (never eating dark rims)
    ext_bg = ext_bg | (ndimage.binary_dilation(ext_bg, iterations=2) & (lo > 241.0) & (sat < 0.06))
    fg = ~ext_bg

    # Keep main connected component
    fg_lbl, fg_n = ndimage.label(fg)
    if fg_n > 1:
        sizes = ndimage.sum(fg, fg_lbl, range(1, fg_n + 1))
        fg = fg_lbl == (1 + int(np.argmax(sizes)))

    # 2. Geometric & pixel mask of the clear acrylic hopper tube (y <= 376, x in 262..725)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Feed-neck clamp starts at y ~ 368..374; keep neck glass visible down to clamp top (y=368)
    tube_region = fg & (yy < 372.0) & (xx > 260.0) & (xx < 726.0)

    # Interior clipping cylinder for faces inside the acrylic tube:
    # Tube cylinder axis runs from back center (306, 274) to front lid center (626, 189)
    # plus vertical feed neck drop around (384, 330..366).
    ax_dx, ax_dy = 626.0 - 306.0, 189.0 - 274.0
    ax_len = math.hypot(ax_dx, ax_dy)
    ux, uy = ax_dx / ax_len, ax_dy / ax_len
    nx, ny = -uy, ux  # perpendicular upward-ish normal

    rel_x = xx - 306.0
    rel_y = yy - 274.0
    proj_u = rel_x * ux + rel_y * uy
    proj_v = rel_x * nx + rel_y * ny

    # Tube half-height tapers slightly toward back end (perspective!): ~86px at back, ~122px at front lid
    t_u = np.clip(proj_u / ax_len, 0.0, 1.0)
    half_r = 84.0 + 36.0 * t_u
    in_cyl = (proj_u >= -12.0) & (proj_u <= ax_len + 64.0) & (np.abs(proj_v) <= half_r)
    # Front lid elliptical cap at (626, 189), rx=80, ry=122, tilted slightly
    lid_ell = (((xx - 624.0) / 80.0) ** 2 + ((yy - 189.0) / 122.0) ** 2) <= 1.0
    # Back end rounded cap at (314, 274)
    back_ell = (((xx - 316.0) / 48.0) ** 2 + ((yy - 274.0) / 82.0) ** 2) <= 1.0
    # Feed neck window dropping down into black clamp
    neck_box = (xx >= 358.0) & (xx <= 410.0) & (yy >= 310.0) & (yy <= 368.0)

    # Restrict clip strictly inside detected acrylic silhouette eroded by 8px so faces never poke outside glass!
    tube_filled = ndimage.binary_fill_holes(tube_region)
    tube_inner_safe = ndimage.binary_erosion(tube_filled, iterations=7)
    clip_raw = ((in_cyl | lid_ell | back_ell | neck_box) & tube_inner_safe).astype(np.float32)
    # Soft 2px anti-aliased wall clip
    clip_soft = cv2.GaussianBlur(clip_raw, (0, 0), 1.4)
    tube_clip_u8 = np.clip(np.round(clip_soft * 255.0), 0, 255).astype(np.uint8)

    # 3. Clean alpha-keyed gun body (below y=368, excluding tube region)
    dist_in = ndimage.distance_transform_edt(fg)
    dist_out = ndimage.distance_transform_edt(~fg)
    sdf = dist_in - dist_out
    base_alpha = np.clip((sdf + 0.35) / 1.35, 0.0, 1.0)

    # Rim feather & white-backdrop un-premul ONLY on opaque non-tube gun parts
    body_mask = fg & (~tube_region)
    rim_bright = body_mask & (dist_in <= 3.0) & (lo > 195.0) & (sat < 0.12)
    base_alpha[rim_bright] *= np.clip((248.0 - lum[rim_bright]) / 55.0, 0.0, 1.0)

    semi = body_mask & (base_alpha > 0.04) & (base_alpha < 0.98)
    rgb_clean = arr.copy()
    inv = 1.0 - base_alpha[semi]
    denom = np.maximum(base_alpha[semi], 0.18)
    rgb_clean[semi] = np.clip((arr[semi] - inv[:, None] * 255.0) / denom[:, None], 0.0, 255.0)

    seed = body_mask & (dist_in > 3.2) & (lum < 236.0)
    if np.any(seed):
        _, idx = ndimage.distance_transform_edt(~seed, return_indices=True)
        nearest = rgb_clean[idx[0], idx[1]]
        w_rim = np.clip((dist_in - 0.8) / 2.4, 0.0, 1.0)
        w_rim = np.where(body_mask & (dist_in <= 2.6) & (lum > 180.0) & (sat < 0.18), w_rim * 0.35, w_rim)[..., None]
        rgb_clean = np.where(body_mask[..., None], rgb_clean * w_rim + nearest * (1.0 - w_rim), rgb_clean)

    # Build opaque `gun_body` (zero out tube_region so back/front glass handle it cleanly)
    gun_body = np.zeros((h, w, 4), dtype=np.uint8)
    body_a = np.where(tube_region, 0.0, base_alpha)
    gun_body[..., :3] = np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8)
    gun_body[..., 3] = np.clip(np.round(body_a * 255.0), 0, 255).astype(np.uint8)
    gun_body[gun_body[..., 3] < 6] = 0

    # 4. Build `hopper_back` (cool tinted acrylic back-wall behind faces)
    hopper_back = np.zeros((h, w, 4), dtype=np.uint8)
    tb = tube_filled.astype(np.float32)
    back_a = tb * np.where(tube_inner_safe, 42.0, 85.0)
    hopper_back[..., :3] = (178, 200, 212)
    hopper_back[..., 3] = np.clip(np.round(back_a), 0, 255).astype(np.uint8)

    # 5. Build `hopper_front` (acrylic glass rims, front lid bevel, & specular shine over faces)
    # Darkness relative to studio white measures acrylic thickness & refraction!
    darkness = np.clip(252.0 - lum, 0.0, 140.0)
    # Outer rim & lid border get crisper visibility; flat clear center stays airy (~12..35 alpha)
    edge_boost = np.where(tube_inner_safe, 0.72, 1.75)
    glass_alpha = np.where(tube_region, np.clip(darkness * edge_boost * 1.45, 10.0, 215.0), 0.0)
    # Add curved longitudinal acrylic specular highlight streak along upper front wall
    spec_band = np.exp(-((proj_v - half_r * 0.52) / 14.0) ** 2) * np.where(
        (proj_u > 15.0) & (proj_u < ax_len + 25.0), 1.0, 0.0
    )
    spec_band2 = np.exp(-((proj_v + half_r * 0.68) / 9.0) ** 2) * np.where(
        (proj_u > 30.0) & (proj_u < ax_len + 15.0), 0.55, 0.0
    )
    spec_total = np.clip(spec_band + spec_band2, 0.0, 1.0) * tb

    # Glass color: cool silver-cyan acrylic mixed with bright white specular streaks
    g_rgb = np.zeros((h, w, 3), dtype=np.float32)
    g_rgb[..., 0] = 192.0
    g_rgb[..., 1] = 212.0
    g_rgb[..., 2] = 224.0
    # Darken very dark rim lines slightly for crisp definition
    dark_rim = np.clip((darkness - 45.0) / 80.0, 0.0, 1.0)[..., None]
    g_rgb = g_rgb * (1.0 - 0.55 * dark_rim) + np.array([62.0, 74.0, 82.0]) * (0.55 * dark_rim)
    # Mix bright white specular reflection
    g_rgb = g_rgb * (1.0 - 0.85 * spec_total[..., None]) + 255.0 * (0.85 * spec_total[..., None])
    front_a = np.clip(glass_alpha + spec_total * 78.0, 0.0, 225.0) * tb
    # Soft outer edge feather on tube silhouette
    front_a *= np.clip((sdf + 0.5) / 1.5, 0.0, 1.0)

    hopper_front = np.zeros((h, w, 4), dtype=np.uint8)
    hopper_front[..., :3] = np.clip(np.round(g_rgb), 0, 255).astype(np.uint8)
    hopper_front[..., 3] = np.clip(np.round(front_a), 0, 255).astype(np.uint8)
    hopper_front[hopper_front[..., 3] < 4] = 0

    # 6. Extract side-gear / pneumatic bolt patch for dynamic recoil snap on fire
    bolt_patch = np.zeros((h, w, 4), dtype=np.uint8)
    bx0, by0, bx1, by1 = 225, 480, 358, 708
    bolt_patch[by0:by1, bx0:bx1] = gun_body[by0:by1, bx0:bx1]

    return {
        "gun_body": gun_body,
        "hopper_back": hopper_back,
        "hopper_front": hopper_front,
        "tube_clip": tube_clip_u8,
        "bolt_patch": bolt_patch,
    }


def _paint_eyelid_blink(head_rgba: np.ndarray, blink_amt: float) -> np.ndarray:
    """Paint comic upper-eyelid squint/blink over the upper-middle eye band of a head."""
    if blink_amt <= 0.05:
        return head_rgba
    out = head_rgba.copy()
    hh, hw = out.shape[:2]
    # Sample warm cheek skin tone (below eyes, avoiding white sclera/teeth)
    cy0, cy1 = int(hh * 0.54), int(hh * 0.67)
    cx0, cx1 = int(hw * 0.28), int(hw * 0.44)
    patch = out[cy0:cy1, cx0:cx1]
    lum_p = 0.299 * patch[..., 0] + 0.587 * patch[..., 1] + 0.114 * patch[..., 2]
    valid = patch[(patch[..., 3] > 200) & (lum_p < 190.0) & (lum_p > 55.0)]
    if len(valid) > 10:
        skin = np.median(valid[:, :3], axis=0).astype(np.uint8)
    else:
        skin = np.array([162, 110, 74], dtype=np.uint8)
    lid_col = (int(skin[0] * 0.92), int(skin[1] * 0.90), int(skin[2] * 0.88), 255)
    lash_col = (28, 18, 14, 255)

    ey = int(round(hh * 0.41))
    ex_l = int(round(hw * 0.37))
    ex_r = int(round(hw * 0.63))
    erx = max(4, int(round(hw * 0.095)))
    ery = max(2, int(round(hh * 0.055 * blink_amt)))
    for ex in (ex_l, ex_r):
        cv2.ellipse(out, (ex, ey), (erx, ery), 0, 0, 360, lid_col, -1, cv2.LINE_AA)
        cv2.ellipse(
            out, (ex, ey + max(1, ery // 2)), (erx, max(1, ery // 2)), 0, 15, 165, lash_col, max(1, hw // 90), cv2.LINE_AA
        )
    # Restore original alpha silhouette
    out[..., 3] = np.minimum(out[..., 3], head_rgba[..., 3])
    return out


def _draw_psi_gauge(
    pressure_01: float,
    needle_jitter_deg: float,
    diameter: int = 86,
) -> np.ndarray:
    """Draw a brass-rimmed CO2 Fart-Canister PSI pressure gauge with shivering needle."""
    ss = 2
    sz = diameter * ss
    gauge = np.zeros((sz, sz, 4), dtype=np.uint8)
    c = sz // 2
    r_outer = sz // 2 - 4

    # Brass housing + bezel shadow
    cv2.circle(gauge, (c + 2, c + 3), r_outer, (28, 22, 12, 155), -1, cv2.LINE_AA)
    cv2.circle(gauge, (c, c), r_outer, (148, 118, 54, 255), -1, cv2.LINE_AA)
    cv2.circle(gauge, (c, c), int(r_outer * 0.90), (208, 178, 96, 255), -1, cv2.LINE_AA)
    cv2.circle(gauge, (c, c), int(r_outer * 0.80), (242, 236, 214, 255), -1, cv2.LINE_AA)

    # Green -> Yellow -> Red danger arc (135 deg to 405 deg in CV angle coords)
    r_arc = int(r_outer * 0.65)
    t_arc = max(4, sz // 18)
    cv2.ellipse(gauge, (c, c), (r_arc, r_arc), 0, 135, 240, (44, 156, 52, 255), t_arc, cv2.LINE_AA)
    cv2.ellipse(gauge, (c, c), (r_arc, r_arc), 0, 240, 325, (234, 184, 30, 255), t_arc, cv2.LINE_AA)
    cv2.ellipse(gauge, (c, c), (r_arc, r_arc), 0, 325, 405, (218, 36, 28, 255), t_arc, cv2.LINE_AA)

    # Dial tick marks
    for k in range(9):
        ang = math.radians(135.0 + k * (270.0 / 8.0))
        p0 = (int(round(c + math.cos(ang) * (r_outer * 0.56))), int(round(c + math.sin(ang) * (r_outer * 0.56))))
        p1 = (int(round(c + math.cos(ang) * (r_outer * 0.74))), int(round(c + math.sin(ang) * (r_outer * 0.74))))
        cv2.line(gauge, p0, p1, (36, 30, 24, 255), max(2, sz // 55), cv2.LINE_AA)

    # Shivering red needle
    ang_deg = 135.0 + float(np.clip(pressure_01, 0.02, 1.05)) * 270.0 + float(needle_jitter_deg)
    ang_rad = math.radians(ang_deg)
    tip = (int(round(c + math.cos(ang_rad) * (r_outer * 0.66))), int(round(c + math.sin(ang_rad) * (r_outer * 0.66))))
    tail = (int(round(c - math.cos(ang_rad) * (r_outer * 0.18))), int(round(c - math.sin(ang_rad) * (r_outer * 0.18))))
    cv2.line(gauge, tail, tip, (215, 26, 22, 255), max(3, sz // 30), cv2.LINE_AA)
    cv2.circle(gauge, (c, c), max(4, sz // 14), (48, 42, 34, 255), -1, cv2.LINE_AA)
    cv2.circle(gauge, (c, c), max(2, sz // 24), (186, 152, 76, 255), -1, cv2.LINE_AA)

    # Subtle glass glint
    cv2.ellipse(
        gauge,
        (int(c - r_outer * 0.22), int(c - r_outer * 0.26)),
        (int(r_outer * 0.34), int(r_outer * 0.14)),
        -32,
        0,
        360,
        (255, 255, 255, 95),
        -1,
        cv2.LINE_AA,
    )
    return resize_premul(gauge, (diameter, diameter))


def _draw_mud_drip(length_px: int, width_px: int, stretch: float) -> np.ndarray:
    """Render a glossy wet brown mud droplet hanging down by `length_px * stretch`."""
    lh = max(12, int(round(length_px * stretch)))
    lw = max(8, width_px)
    canvas = np.zeros((lh + 6, lw + 6, 4), dtype=np.uint8)
    cx = (lw + 6) // 2
    pts = []
    # Teardrop neck to bulb
    for i in range(18):
        t = i / 17.0
        y = 3 + t * lh
        if t < 0.62:
            r = lw * (0.28 - 0.13 * math.sin(t * math.pi / 0.62))
        else:
            u = (t - 0.62) / 0.38
            r = lw * (0.20 + 0.26 * math.sin(u * math.pi))
        pts.append((cx - r, y))
    for i in range(17, -1, -1):
        t = i / 17.0
        y = 3 + t * lh
        if t < 0.62:
            r = lw * (0.28 - 0.13 * math.sin(t * math.pi / 0.62))
        else:
            u = (t - 0.62) / 0.38
            r = lw * (0.20 + 0.26 * math.sin(u * math.pi))
        pts.append((cx + r, y))
    poly = np.array(pts, dtype=np.int32)
    cv2.fillPoly(canvas, [poly], (88, 52, 20, 245), cv2.LINE_AA)
    cv2.polylines(canvas, [poly], True, (42, 22, 9, 255), 1, cv2.LINE_AA)
    # Wet specular highlight near bulb bottom
    cv2.ellipse(
        canvas,
        (int(cx - lw * 0.12), int(3 + lh * 0.78)),
        (max(1, lw // 7), max(2, lh // 10)),
        -12,
        0,
        360,
        (218, 190, 140, 210),
        -1,
        cv2.LINE_AA,
    )
    return canvas


def _compose_hopper_faces(
    tube_shape: Tuple[int, int],
    tube_clip_u8: np.ndarray,
    heads: Dict[str, np.ndarray],
    splats: List[np.ndarray],
    mode: str,
    t_norm: float,
    frame_idx: int,
) -> Tuple[np.ndarray, np.ndarray | None]:
    """Pack and animate all 7 squished cartoon bloke faces inside the clear hopper tube.

    Returns `(hopper_faces_rgba, ejected_face_ball_or_None)`.
    """
    h, w = tube_shape
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    tau = 2.0 * math.pi

    # 7 slot positions along the tilted hopper cylinder (1024x1024 plate space):
    # Slot 6 = bottom feed-neck entry (head_cross), descending back-to-front!
    slots = [
        # (name, cx, cy, target_w, base_rot_deg, is_turban)
        ("head_scream_front", 575.0, 152.0, 118, 14.0, False),
        ("head_sky_gasp", 482.0, 186.0, 118, -11.0, False),
        ("head_oiled_yell", 554.0, 226.0, 122, -16.0, False),
        ("head_wide_grin", 636.0, 208.0, 116, 12.0, False),
        ("head_turban_grin", 464.0, 254.0, 134, -8.0, True),
        ("head_turban_yell", 386.0, 240.0, 132, 16.0, True),
        ("head_cross", 374.0, 304.0, 116, -6.0, False),
    ]

    ejected_ball: np.ndarray | None = None

    # Compute drop-one-notch offset on fire!
    drop_t = 0.0
    wild_amp = 0.0
    if mode == "fire":
        # Frames 0..4: bottom face drops into breach while stack slides down 1 notch & rebounds
        if frame_idx <= 4:
            drop_t = math.sin((frame_idx / 4.0) * math.pi * 0.5)
        else:
            # Smooth damped spring bounce back to settled positions by frame 17
            rem = (frame_idx - 4) / 13.0
            drop_t = max(0.0, (1.0 - rem) * math.cos(rem * math.pi * 2.2))
        wild_amp = max(0.0, 1.0 - frame_idx / 16.0)
    elif mode == "reload":
        # Vigorous slosh inside hopper as player shakes the gun
        wild_amp = math.sin(t_norm * math.pi)

    for idx, (hname, sx_pos, sy_pos, target_w, base_rot, is_turban) in enumerate(slots):
        head = heads[hname]
        # Scale proportionally to target_w (turbaned heads get taller vertical allowance)
        hh, hw = head.shape[:2]
        sc = target_w / float(hw)
        nh = max(16, int(round(hh * sc)))
        nw = max(16, int(round(hw * sc)))
        h_rs = resize_premul(head, (nw, nh))

        # Per-face independent comic animation
        ph = idx * 1.37
        if mode == "idle":
            # Bouncing, rattling, turning side-to-side, squishing & arguing!
            bob_x = 4.5 * math.sin(tau * 2.0 * t_norm + ph) + 2.2 * math.sin(tau * 5.0 * t_norm + ph * 1.7)
            bob_y = 6.0 * abs(math.sin(tau * 2.0 * t_norm + ph * 0.8)) - 3.0
            tilt = base_rot + 11.0 * math.sin(tau * 1.0 * t_norm + ph * 1.3)
            # Argument turn-around / yaw squash (periodically glances left/right toward neighbors!)
            yaw = math.cos(tau * 1.0 * t_norm + ph * 0.9)
            flip_x = (idx in (1, 3, 5)) and (yaw < -0.35)
            if flip_x:
                h_rs = np.ascontiguousarray(h_rs[:, ::-1, :])
            sq = 0.08 * math.sin(tau * 3.0 * t_norm + ph * 2.1)
            sx_sc = (1.0 + sq) * (0.90 + 0.10 * abs(yaw))
            sy_sc = 1.0 - sq * 0.85

            # Staggered comic blinking on select faces
            blink = 0.0
            if idx in (2, 4, 6):
                b_cyc = (t_norm + idx * 0.29) % 1.0
                if b_cyc < 0.07:
                    blink = math.sin((b_cyc / 0.07) * math.pi)
            h_rs = _paint_eyelid_blink(h_rs, blink)
        elif mode == "fire":
            # Drop one notch toward feed neck `(384, 345)` and bounce wildly!
            if idx == 6:
                # Bottom face plunges down the feed neck!
                bob_x = 12.0 * drop_t
                bob_y = 44.0 * drop_t
                sx_sc = 1.0 - 0.18 * drop_t + 0.14 * wild_amp * math.sin(frame_idx * 2.3)
                sy_sc = 1.0 + 0.22 * drop_t - 0.14 * wild_amp * math.sin(frame_idx * 2.3)
            else:
                nxt = slots[min(len(slots) - 1, idx + 1)]
                bob_x = (nxt[1] - sx_pos) * 0.52 * drop_t + 9.0 * wild_amp * math.sin(frame_idx * 2.6 + ph)
                bob_y = (nxt[2] - sy_pos) * 0.52 * drop_t - 15.0 * wild_amp * abs(math.sin(frame_idx * 2.1 + ph))
                sx_sc = 1.0 + 0.16 * wild_amp * math.sin(frame_idx * 2.7 + ph)
                sy_sc = 1.0 - 0.14 * wild_amp * math.sin(frame_idx * 2.7 + ph)
            tilt = base_rot + 24.0 * wild_amp * math.sin(frame_idx * 2.4 + ph)
        else:
            # Reload: vigorous hopper shake sloshing all 7 faces wildly inside the tube!
            slosh = math.sin(tau * 2.5 * t_norm + ph * 0.7)
            bob_x = 18.0 * wild_amp * slosh
            bob_y = -18.0 * wild_amp * abs(math.cos(tau * 3.0 * t_norm + ph))
            tilt = base_rot + 28.0 * wild_amp * math.cos(tau * 2.5 * t_norm + ph)
            sx_sc = 1.0 + 0.14 * wild_amp * slosh
            sy_sc = 1.0 - 0.12 * wild_amp * slosh
            if slosh < -0.45 and idx % 2 == 1:
                h_rs = np.ascontiguousarray(h_rs[:, ::-1, :])

        # Add a tiny mud smudge on alternating faces so they look steeped in poop paintballs!
        if idx in (0, 2, 5):
            smudge = resize_premul(splats[idx % len(splats)], (max(12, nw // 3), max(12, nh // 3)))
            smudge[..., 3] = (smudge[..., 3].astype(np.float32) * 0.55).astype(np.uint8)
            h_rs = alpha_over(h_rs, smudge, nw * 0.45, nh * 0.48)

        # Pad and warp around center
        pad = 36
        pw, ph_box = nw + 2 * pad, nh + 2 * pad
        padded = np.zeros((ph_box, pw, 4), dtype=np.uint8)
        padded[pad:pad + nh, pad:pad + nw] = h_rs
        warped = warp_rgba(
            padded,
            angle_deg=tilt,
            sx=sx_sc,
            sy=sy_sc,
            dx=0.0,
            dy=0.0,
            pivot=(pw * 0.5, ph_box * 0.5),
            out_hw=(ph_box, pw),
        )
        # Subtle contact shadow behind each face for depth inside the crowded tube
        sh_alpha = (warped[..., 3].astype(np.float32) * 0.28).astype(np.uint8)
        shadow = np.zeros_like(warped)
        shadow[..., :3] = (32, 22, 12)
        shadow[..., 3] = sh_alpha
        px = sx_pos + bob_x - pw * 0.5
        py = sy_pos + bob_y - ph_box * 0.5
        layer = alpha_over(layer, shadow, px + 3, py + 4)
        layer = alpha_over(layer, warped, px, py)

    # Clip cleanly inside the acrylic inner glass wall!
    clip_f = tube_clip_u8.astype(np.float32) / 255.0
    layer[..., 3] = np.clip(np.round(layer[..., 3].astype(np.float32) * clip_f), 0, 255).astype(np.uint8)
    layer[layer[..., 3] < 4] = 0

    # On fire frames 1..7, create a mud-drenched yelling face paintball blasting out of the muzzle!
    if mode == "fire" and 1 <= frame_idx <= 7:
        ej = resize_premul(heads["head_turban_yell"], (82, 92))
        mud_overlay = resize_premul(splats[1], (74, 74))
        mud_overlay[..., 3] = (mud_overlay[..., 3].astype(np.float32) * 0.65).astype(np.uint8)
        ej = alpha_over(ej, mud_overlay, 6, 14)
        pad = 18
        eb = np.zeros((92 + 2 * pad, 82 + 2 * pad, 4), dtype=np.uint8)
        eb[pad:pad + 92, pad:pad + 82] = ej
        ejected_ball = warp_rgba(
            eb,
            angle_deg=frame_idx * 48.0,
            sx=1.0,
            sy=0.92,
            pivot=(eb.shape[1] * 0.5, eb.shape[0] * 0.5),
            out_hw=eb.shape[:2],
        )

    return layer, ejected_ball


def _render_viewmodel_frame(
    layers: Dict[str, np.ndarray],
    heads: Dict[str, np.ndarray],
    fx: Dict[str, List[np.ndarray]],
    mode: str,
    frame_idx: int,
    n_frames: int,
) -> np.ndarray:
    """Compose one 420x360 first-person viewmodel frame for Design 3."""
    t_norm = frame_idx / float(max(1, n_frames))
    tau = 2.0 * math.pi
    h, w = layers["gun_body"].shape[:2]  # 1024x1024 studio working plate

    # 1. Start with opaque gun body, animate pneumatic bolt/gear slam on fire
    comp = layers["gun_body"].copy()
    if mode == "fire":
        # Pneumatic bolt + side gear snaps forward (-x) on frames 0..3 and returns
        if frame_idx <= 3:
            bolt_kick = math.sin((frame_idx / 3.0) * math.pi * 0.5)
        else:
            bolt_kick = max(0.0, 1.0 - (frame_idx - 3) / 9.0)
        comp = alpha_over(comp, layers["bolt_patch"], -18.0 * bolt_kick, 3.0 * bolt_kick)

    # 2. Clear acrylic back-wall -> 7 animated squished faces -> acrylic front glass sheen
    comp = alpha_over(comp, layers["hopper_back"], 0, 0)
    faces_layer, ejected_ball = _compose_hopper_faces(
        (h, w), layers["tube_clip"], heads, fx["splats"], mode, t_norm, frame_idx
    )
    comp = alpha_over(comp, faces_layer, 0, 0)
    comp = alpha_over(comp, layers["hopper_front"], 0, 0)

    # 3. Mud splatters & dripping wet globs stuck onto the barrel shroud, clamp & CO2 tank
    splat0 = resize_premul(fx["splats"][0], (94, 94))
    splat1 = resize_premul(fx["splats"][2], (76, 76))
    splat2 = resize_premul(fx["splats"][3], (84, 84))
    splat0[..., 3] = (splat0[..., 3].astype(np.float32) * 0.82).astype(np.uint8)
    splat1[..., 3] = (splat1[..., 3].astype(np.float32) * 0.78).astype(np.uint8)
    splat2[..., 3] = (splat2[..., 3].astype(np.float32) * 0.80).astype(np.uint8)
    comp = alpha_over(comp, splat0, 198, 430)   # barrel shroud mud splat
    comp = alpha_over(comp, splat1, 355, 368)   # hopper feed clamp mud splat
    comp = alpha_over(comp, splat2, 745, 620)   # CO2 canister mud splat

    drip_stretch = 1.0 + 0.18 * math.sin(tau * 2.0 * t_norm)
    drip1 = _draw_mud_drip(44, 18, drip_stretch)
    drip2 = _draw_mud_drip(34, 14, 1.0 + 0.16 * math.cos(tau * 2.0 * t_norm + 1.4))
    comp = alpha_over(comp, drip1, 212, 492)    # dripping off barrel shroud
    comp = alpha_over(comp, drip2, 608, 318)    # dripping off front hopper lip

    # 4. Tricolor cloth flags fluttering off the barrel shroud & rear receiver!
    # Flag pole 1 on front barrel shroud (x~196, y~428 up to y~270, clear of hopper faces)
    pole_col = (118, 92, 44, 255)
    cv2.line(comp, (196, 434), (190, 272), pole_col, 6, cv2.LINE_AA)
    cv2.circle(comp, (190, 270), 7, (210, 174, 78, 255), -1, cv2.LINE_AA)
    wind_amp = 1.0 if mode == "idle" else 1.45
    flag1 = render_tricolor_flag(140, 86, phase=tau * 2.0 * t_norm, pole_left=True, amp=wind_amp)
    comp = alpha_over(comp, flag1, 190, 272)

    # Flag pole 2 smaller pennant off rear receiver / CO2 valve (x~675, y~530 up to y~412)
    cv2.line(comp, (674, 535), (692, 412), pole_col, 5, cv2.LINE_AA)
    cv2.circle(comp, (692, 410), 6, (210, 174, 78, 255), -1, cv2.LINE_AA)
    flag2 = render_tricolor_flag(106, 66, phase=tau * 2.0 * t_norm + 1.3, pole_left=True, amp=wind_amp * 1.1)
    comp = alpha_over(comp, flag2, 692, 412)

    # 5. CO2 Fart-Canister PSI Pressure Gauge mounted on the brass receiver!
    if mode == "idle":
        psi_val = 0.68 + 0.05 * math.sin(tau * 2.0 * t_norm)
        jitter = 3.5 * math.sin(tau * 11.0 * t_norm) + 2.0 * math.cos(tau * 17.0 * t_norm)
    elif mode == "fire":
        # Spikes into RED on frame 1, vents pressure down, rebounds!
        if frame_idx <= 2:
            psi_val = 0.96
        elif frame_idx <= 8:
            psi_val = 0.96 - 0.58 * ((frame_idx - 2) / 6.0)
        else:
            psi_val = 0.38 + 0.30 * ((frame_idx - 8) / 9.0)
        jitter = 12.0 * math.sin(frame_idx * 3.1)
    else:
        psi_val = 0.52 + 0.24 * math.sin(tau * 2.0 * t_norm)
        jitter = 9.0 * math.sin(frame_idx * 2.8)
    gauge = _draw_psi_gauge(psi_val, jitter, diameter=94)
    comp = alpha_over(comp, gauge, 560, 502)

    # 6. Firing fart-pop mist + mud spray + ejected mini-bloke paintball at muzzle (126, 458)
    if mode == "fire":
        if frame_idx <= 7:
            prog = frame_idx / 7.0
            mist = fx["mists"][(frame_idx * 2) % len(fx["mists"])]
            m_sz = int(round(120 + 170 * prog))
            m_rs = resize_premul(mist, (m_sz, m_sz))
            m_rs[..., 3] = (m_rs[..., 3].astype(np.float32) * (1.0 - 0.72 * prog)).astype(np.uint8)
            comp = alpha_over(comp, m_rs, 126 - m_sz * 0.65 - prog * 55, 458 - m_sz * 0.52 - prog * 18)

            gl = resize_premul(fx["globs"][frame_idx % 4], (64, 64))
            comp = alpha_over(comp, gl, 118 - prog * 110, 442 - prog * 28)

        if ejected_ball is not None:
            t_ej = (frame_idx - 1) / 6.0
            ex = 110 - t_ej * 145
            ey = 415 - t_ej * 42
            comp = alpha_over(comp, ejected_ball, ex, ey)

    # 7. Scale down cleanly to 420x360 FPS viewmodel frame with recoil/shake motion!
    sc = 0.370
    sw = int(round(w * sc))
    sh = int(round(h * sc))
    vm_gun = resize_premul(comp, (sw, sh))

    # Base anchor: bottom-right hand & CO2 canister bleed flush to (420, 360)
    base_x, base_y = 48.0, -10.0
    if mode == "idle":
        dx = 2.2 * math.sin(tau * t_norm)
        dy = 3.0 * math.sin(tau * 2.0 * t_norm)
        ang = 0.7 * math.sin(tau * t_norm + 0.6)
    elif mode == "fire":
        # Crisp pneumatic kick back-right and up, then settle
        kick = math.sin(min(1.0, frame_idx / 6.0) * math.pi) if frame_idx <= 6 else -0.18 * math.sin(((frame_idx - 6) / 11.0) * math.pi)
        dx = 15.0 * kick
        dy = 11.0 * kick
        ang = -5.5 * kick
    else:
        # Hopper-shake reload: vigorous side-to-side & vertical rattle!
        sh_env = math.sin(t_norm * math.pi)
        dx = 14.0 * sh_env * math.sin(tau * 3.0 * t_norm)
        dy = -12.0 * sh_env * math.cos(tau * 4.0 * t_norm)
        ang = 7.5 * sh_env * math.sin(tau * 3.0 * t_norm + 0.5)

    canvas = np.zeros((VM_H, VM_W, 4), dtype=np.uint8)
    placed = alpha_over(canvas, vm_gun, base_x, base_y)
    # Pivot near lower-right grip so recoil rotates barrel naturally
    vm_frame = warp_rgba(
        placed,
        angle_deg=ang,
        sx=1.0,
        sy=1.0,
        dx=dx,
        dy=dy,
        pivot=(300.0, 290.0),
        out_hw=(VM_H, VM_W),
    )

    # 8. Buzzing flies orbiting the hopper lid & muzzle in crisp 420x360 space!
    lid_center = (48.0 + 625.0 * sc + dx, -10.0 + 165.0 * sc + dy)
    muz_center = (48.0 + 135.0 * sc + dx, -10.0 + 448.0 * sc + dy)
    vm_frame = render_fly_swarm(
        vm_frame,
        centers=[lid_center, muz_center],
        t_norm=t_norm,
        n_flies=12,
        scale=0.82,
    )
    return vm_frame


def _render_projectile_frames(
    heads: Dict[str, np.ndarray],
    fx: Dict[str, List[np.ndarray]],
    n_frames: int = 24,
) -> List[np.ndarray]:
    """Build 24 rapid-spinning mud-coated yelling head / mini-bloke paintball orb frames."""
    sz = PROJ_SZ
    c = sz * 0.5
    r_orb = 58.0
    yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32)
    dx = xx - c
    dy = yy - c
    r2 = dx * dx + dy * dy
    in_sph = r2 <= r_orb * r_orb
    nz = np.sqrt(np.maximum(0.0, r_orb * r_orb - r2)) / r_orb
    nx = dx / r_orb
    ny = dy / r_orb

    # Precompute glossy wet mud-orb shading
    lx, ly, lz = -0.48, -0.52, 0.70
    diff = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)
    hx, hy, hz = -0.28, -0.32, 0.90
    spec = np.power(np.clip(nx * hx + ny * hy + nz * hz, 0.0, 1.0), 22.0)

    face_cycle = [
        resize_premul(heads["head_turban_yell"], (108, 122)),
        resize_premul(heads["head_oiled_yell"], (106, 118)),
        resize_premul(heads["head_cross"], (104, 114)),
        resize_premul(heads["head_sky_gasp"], (106, 114)),
    ]

    # Spherize mapping so face curves around the paintball sphere!
    sph_dist = np.sqrt(r2) / r_orb
    sph_scale = np.where(in_sph, 0.78 + 0.30 * sph_dist, 1.0)
    sph_map_x = (c + dx * sph_scale).astype(np.float32)
    sph_map_y = (c + dy * sph_scale).astype(np.float32)

    frames: List[np.ndarray] = []
    tau = 2.0 * math.pi
    for k in range(n_frames):
        t = k / float(n_frames)
        # Base glossy mud-paintball sphere
        orb = np.zeros((sz, sz, 4), dtype=np.uint8)
        base_col = np.array([104.0, 62.0, 24.0]) * (0.35 + 0.85 * diff[..., None])
        # Swirl lime-green stink-slime highlight across shell
        swirl = 0.5 + 0.5 * np.sin(nx * 4.5 + ny * 3.0 + t * tau * 2.0)
        slime_col = np.array([138.0, 154.0, 48.0]) * (0.4 + 0.7 * diff[..., None])
        orb_rgb = base_col * (1.0 - 0.30 * swirl[..., None]) + slime_col * (0.30 * swirl[..., None])
        orb_rgb += np.array([235.0, 220.0, 175.0]) * (spec[..., None] * 0.75)

        dist_edge = r_orb - np.sqrt(r2)
        sph_a = np.clip((dist_edge + 0.8) / 1.6, 0.0, 1.0)
        orb[..., :3] = np.clip(np.round(orb_rgb), 0, 255).astype(np.uint8)
        orb[..., 3] = np.clip(np.round(sph_a * 255.0), 0, 255).astype(np.uint8)

        # Wrap spinning yelling bloke face onto front hemisphere!
        spin_phase = (t * 2.0) % 1.0  # 2 face-flips per 24 frames
        f_idx = int(t * len(face_cycle)) % len(face_cycle)
        face = face_cycle[f_idx]
        # Horizontal perspective squash as face rotates across sphere front
        yaw_ang = (spin_phase * 2.0 - 1.0) * math.pi * 0.5
        x_slide = math.sin(yaw_ang) * 34.0
        horiz_sq = max(0.32, math.cos(yaw_ang * 0.75))

        face_canvas = np.zeros((sz, sz, 4), dtype=np.uint8)
        face_canvas = alpha_over(face_canvas, face, c - face.shape[1] * 0.5, c - face.shape[0] * 0.5)
        face_rot = warp_rgba(
            face_canvas,
            angle_deg=t * 360.0,
            sx=horiz_sq,
            sy=0.95,
            dx=x_slide,
            dy=0.0,
            pivot=(c, c),
            out_hw=(sz, sz),
        )
        # Spherize & clip face inside the orb silhouette
        face_pm = to_premul(face_rot)
        face_sph = from_premul(
            cv2.remap(face_pm, sph_map_x, sph_map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        )
        face_sph[..., 3] = np.minimum(face_sph[..., 3], orb[..., 3])
        # Blend mud sheen over face so it looks genuinely coated in mud!
        face_sph[..., :3] = np.clip(
            face_sph[..., :3].astype(np.float32) * (0.72 + 0.35 * diff[..., None]) + spec[..., None] * 65.0,
            0,
            255,
        ).astype(np.uint8)
        orb = alpha_over(orb, face_sph, 0, 0)

        # Add chunky mud splats spinning around the orb rim
        splat = resize_premul(fx["splats"][k % 4], (120, 120))
        splat[..., 3] = (splat[..., 3].astype(np.float32) * 0.72).astype(np.uint8)
        orb = alpha_over(orb, splat, c - 60 + 10 * math.cos(tau * t), c - 60 + 10 * math.sin(tau * t))

        # Orbiting trailing chunky mud globs
        for g in range(3):
            ga = tau * (t + g / 3.0)
            gr = r_orb + 18.0 + 8.0 * math.sin(tau * 2.0 * t + g)
            gx = c + math.cos(ga) * gr
            gy = c + math.sin(ga) * gr
            gl = resize_premul(fx["globs"][(k + g) % 4], (34, 34))
            orb = alpha_over(orb, gl, gx - 17, gy - 17)

        # 5 buzzing flies orbiting the spinning paintball orb
        orb = render_fly_swarm(orb, centers=(c, c), t_norm=t, n_flies=5, scale=0.85)
        frames.append(orb)
    return frames


def _build_3p_paintball_marker(
    layers: Dict[str, np.ndarray],
    heads: Dict[str, np.ndarray],
    fx: Dict[str, List[np.ndarray]],
    mode: str,
    t_norm: float,
    frame_idx: int,
) -> np.ndarray:
    """Create a clean 3rd-person Poop Paintball Marker (1P hand/arm removed) for the enemy."""
    tau = 2.0 * math.pi
    h, w = layers["gun_body"].shape[:2]

    # Strip the 1st-person gloved hand & forearm cleanly below the brass receiver & CO2 tank
    body_clean = layers["gun_body"].copy()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Keep front barrel/gear up to y=725 for x<365; for x>=365 slice cleanly below receiver/CO2 bottle
    cut_y = np.where(xx < 365.0, 728.0, 646.0 + (xx - 365.0) * 0.25)
    keep_gun = (yy <= cut_y) & (xx <= 815.0)
    # Round off rear CO2 cylinder cap around x=805 so there's no hard vertical cut
    rear_fade = np.clip((815.0 - xx) / 14.0, 0.0, 1.0)
    bot_fade = np.clip((cut_y - yy) / 6.0, 0.0, 1.0)
    body_clean[..., 3] = np.where(
        keep_gun,
        np.clip(np.round(body_clean[..., 3].astype(np.float32) * rear_fade * bot_fade), 0, 255).astype(np.uint8),
        0,
    )

    gun = body_clean
    gun = alpha_over(gun, layers["hopper_back"], 0, 0)
    faces_layer, _ = _compose_hopper_faces(
        (h, w), layers["tube_clip"], heads, fx["splats"], mode, t_norm, frame_idx
    )
    gun = alpha_over(gun, faces_layer, 0, 0)
    gun = alpha_over(gun, layers["hopper_front"], 0, 0)

    # Mud splat + PSI gauge + bold tricolor flag on barrel shroud
    sp = resize_premul(fx["splats"][0], (96, 96))
    gun = alpha_over(gun, sp, 196, 432)
    gauge = _draw_psi_gauge(0.74, 3.0 * math.sin(tau * 8.0 * t_norm), diameter=84)
    gun = alpha_over(gun, gauge, 560, 502)

    cv2.line(gun, (196, 434), (190, 240), (118, 92, 44, 255), 8, cv2.LINE_AA)
    flag = render_tricolor_flag(180, 110, phase=tau * 2.0 * t_norm, pole_left=True, amp=1.2)
    gun = alpha_over(gun, flag, 190, 240)

    # Crop tightly around the gun with full vertical margin so CO2 tank bottom never clips
    crop = gun[40:790, 90:825]
    marker = resize_premul(crop, (235, 198))
    return marker


def _extract_feathered_hand_mask(
    enemy_base: np.ndarray,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
) -> np.ndarray:
    """Extract only the enemy's fingers/knuckles using a tight soft elliptical mask."""
    eh, ew = enemy_base.shape[:2]
    yy, xx = np.mgrid[0:eh, 0:ew].astype(np.float32)
    ell = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    w_mask = np.clip((1.0 - ell) / 0.45, 0.0, 1.0)
    out = enemy_base.copy()
    out[..., 3] = np.clip(np.round(out[..., 3].astype(np.float32) * w_mask), 0, 255).astype(np.uint8)
    out[out[..., 3] < 6] = 0
    return out


def _render_3p_frames(
    layers: Dict[str, np.ndarray],
    heads: Dict[str, np.ndarray],
    fx: Dict[str, List[np.ndarray]],
) -> Tuple[List[np.ndarray], List[np.ndarray], List[np.ndarray]]:
    """Render 3rd-person `tp_idle` (24), `tp_fire` (16), and `tp_reload` (16) at 420x440."""
    enemy_base = fx["enemy"]  # 420x440 RGBA
    tau = 2.0 * math.pi

    # Tight elliptical masks on his real hands so his fingers wrap in front of the gun without moving
    r_hand = _extract_feathered_hand_mask(enemy_base, cx=105.0, cy=158.0, rx=16.0, ry=15.0)
    l_hand = _extract_feathered_hand_mask(enemy_base, cx=278.0, cy=173.0, rx=18.0, ry=16.0)

    def make_seq(mode: str, count: int) -> List[np.ndarray]:
        out_frames: List[np.ndarray] = []
        for k in range(count):
            t_norm = k / float(count)
            # Subtle enemy stance bob / recoil / shake
            if mode == "idle":
                e_dx = 2.0 * math.sin(tau * t_norm)
                e_dy = 2.5 * abs(math.cos(tau * t_norm))
                g_dx, g_dy, g_ang = e_dx, e_dy, 1.5 * math.sin(tau * t_norm)
            elif mode == "fire":
                kick = math.sin(min(1.0, k / 5.0) * math.pi) if k <= 5 else 0.0
                e_dx = 3.0 * kick
                e_dy = 5.0 * kick
                g_dx = 6.0 * kick
                g_dy = -4.0 * kick
                g_ang = -7.0 * kick
            else:
                sh = math.sin(t_norm * math.pi)
                e_dx = 6.0 * sh * math.sin(tau * 3.0 * t_norm)
                e_dy = 3.0 * sh * math.cos(tau * 4.0 * t_norm)
                g_dx = 12.0 * sh * math.sin(tau * 3.0 * t_norm)
                g_dy = -10.0 * sh * math.cos(tau * 3.0 * t_norm)
                g_ang = 11.0 * sh * math.sin(tau * 3.0 * t_norm)

            frame = warp_rgba(
                enemy_base,
                angle_deg=0.0,
                sx=1.0,
                sy=1.0,
                dx=e_dx,
                dy=e_dy,
                pivot=(210.0, 420.0),
                out_hw=(TP_H, TP_W),
            )
            marker = _build_3p_paintball_marker(layers, heads, fx, mode, t_norm, k)
            marker_w = warp_rgba(
                marker,
                angle_deg=g_ang - 6.0,
                sx=1.0,
                sy=1.0,
                dx=0.0,
                dy=0.0,
                pivot=(117.0, 110.0),
                out_hw=marker.shape[:2],
            )
            # Place gun right between his two real hands (barrel passes his right hand, CO2 meets left hand)
            frame = alpha_over(frame, marker_w, 82.0 + g_dx, 56.0 + g_dy)

            # Layer his real fingers in front of the gun (zero offset -> seamless arm connection!)
            frame = alpha_over(frame, r_hand, e_dx, e_dy)
            frame = alpha_over(frame, l_hand, e_dx, e_dy)

            # On fire: explosive mud-splat & green fart mist erupting straight toward camera!
            if mode == "fire" and k <= 9:
                prog = k / 9.0
                mist = fx["mists"][k % len(fx["mists"])]
                msz = int(round(86 + 100 * prog))
                mrs = resize_premul(mist, (msz, msz))
                mrs[..., 3] = (mrs[..., 3].astype(np.float32) * (1.0 - 0.65 * prog)).astype(np.uint8)
                frame = alpha_over(frame, mrs, 102 - msz * 0.55 - prog * 30, 174 - msz * 0.5)

                if k <= 5:
                    gl = resize_premul(fx["globs"][k % 4], (48, 48))
                    frame = alpha_over(frame, gl, 90 - prog * 48, 162 - prog * 14)

            # Buzzing flies orbiting the enemy's hopper & muzzle
            frame = render_fly_swarm(
                frame,
                centers=[(220.0 + g_dx, 94.0 + g_dy), (104.0 + g_dx, 172.0 + g_dy)],
                t_norm=t_norm,
                n_flies=10,
                scale=0.72,
            )
            out_frames.append(frame)
        return out_frames

    return (
        make_seq("idle", 24),
        make_seq("fire", 16),
        make_seq("reload", 16),
    )


def _save_seq(frames: Sequence[np.ndarray], out_dir: str, prefix: str) -> List[str]:
    names: List[str] = []
    for idx, arr in enumerate(frames):
        fname = f"{prefix}_{idx:02d}.png"
        Image.fromarray(arr, "RGBA").save(os.path.join(out_dir, fname), optimize=True)
        names.append(fname)
    return names


def _build_contact_sheet(
    vm_idle: List[np.ndarray],
    vm_fire: List[np.ndarray],
    vm_reload: List[np.ndarray],
    proj: List[np.ndarray],
    tp_idle: List[np.ndarray],
    tp_fire: List[np.ndarray],
    tp_reload: List[np.ndarray],
    out_path: str,
) -> None:
    """Create a checkerboard-backed visual QA sheet showing key frames across all sequences."""
    picks: List[Tuple[str, np.ndarray]] = [
        ("vm_idle_00", vm_idle[0]),
        ("vm_idle_20", vm_idle[20]),
        ("vm_idle_40", vm_idle[40]),
        ("vm_fire_01", vm_fire[1]),
        ("vm_fire_04", vm_fire[4]),
        ("vm_reload_04", vm_reload[4]),
        ("vm_reload_10", vm_reload[10]),
        ("proj_00", proj[0]),
        ("proj_08", proj[8]),
        ("proj_16", proj[16]),
        ("tp_idle_00", tp_idle[0]),
        ("tp_fire_02", tp_fire[2]),
        ("tp_reload_06", tp_reload[6]),
    ]
    cell_w, cell_h = 240, 220
    cols = 4
    rows = math.ceil(len(picks) / cols)
    sheet = np.zeros((rows * cell_h, cols * cell_w, 4), dtype=np.uint8)
    # Dark checkerboard background to expose any alpha halo!
    yy, xx = np.mgrid[0:sheet.shape[0], 0:sheet.shape[1]]
    chk = ((xx // 16 + yy // 16) % 2) == 0
    sheet[chk] = (54, 58, 66, 255)
    sheet[~chk] = (40, 44, 50, 255)

    for idx, (label, img) in enumerate(picks):
        r, c = divmod(idx, cols)
        ih, iw = img.shape[:2]
        sc = min((cell_w - 16) / float(iw), (cell_h - 32) / float(ih))
        rs = resize_premul(img, (max(4, int(round(iw * sc))), max(4, int(round(ih * sc)))))
        ox = c * cell_w + (cell_w - rs.shape[1]) // 2
        oy = r * cell_h + 24 + (cell_h - 28 - rs.shape[0]) // 2
        sheet = alpha_over(sheet, rs, ox, oy)
        cv2.putText(
            sheet,
            label,
            (c * cell_w + 8, r * cell_h + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 224, 96, 255),
            1,
            cv2.LINE_AA,
        )

    Image.fromarray(sheet, "RGBA").save(out_path, optimize=True)


def build_concept3(out_dir: str = OUT_DIR) -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    print("[c3_paintball] Extracting paintball marker + acrylic glass hopper layers...")
    layers = extract_paintball_layers()
    heads = _load_heads()
    fx = _load_fx_bank()

    print("[c3_paintball] Rendering 60 vm_idle frames...")
    vm_idle = [_render_viewmodel_frame(layers, heads, fx, "idle", i, 60) for i in range(60)]
    print("[c3_paintball] Rendering 18 vm_fire frames...")
    vm_fire = [_render_viewmodel_frame(layers, heads, fx, "fire", i, 18) for i in range(18)]
    print("[c3_paintball] Rendering 18 vm_reload frames...")
    vm_reload = [_render_viewmodel_frame(layers, heads, fx, "reload", i, 18) for i in range(18)]

    print("[c3_paintball] Rendering 24 spinning mud-face projectile frames...")
    proj = _render_projectile_frames(heads, fx, n_frames=24)

    print("[c3_paintball] Rendering 3rd-person enemy shooter frames (tp_idle/tp_fire/tp_reload)...")
    tp_idle, tp_fire, tp_reload = _render_3p_frames(layers, heads, fx)

    vm_idle_files = _save_seq(vm_idle, out_dir, "vm_idle")
    vm_fire_files = _save_seq(vm_fire, out_dir, "vm_fire")
    vm_reload_files = _save_seq(vm_reload, out_dir, "vm_reload")
    proj_files = _save_seq(proj, out_dir, "proj")
    tp_idle_files = _save_seq(tp_idle, out_dir, "tp_idle")
    tp_fire_files = _save_seq(tp_fire, out_dir, "tp_fire")
    tp_reload_files = _save_seq(tp_reload, out_dir, "tp_reload")

    manifest = {
        "id": "c3_paintball",
        "title": "POOP PAINTBALL HOPPER",
        "subtitle": "Face-Tube Marker",
        "tagline": (
            "Clear acrylic gravity-feed hopper packed with 7 squished rattling faces, "
            "tricolor flags, shivering PSI gauge & rapid-spin mud-face paintball orbs."
        ),
        "fps": 60,
        "muzzle_norm": [0.36, 0.45],
        "tp_muzzle_norm": [0.28, 0.48],
        "vm_idle": vm_idle_files,
        "vm_fire": vm_fire_files,
        "vm_reload": vm_reload_files,
        "proj": {
            "angles": 1,
            "frames_per_angle": len(proj_files),
            "files": proj_files,
        },
        "tp_idle": tp_idle_files,
        "tp_fire": tp_fire_files,
        "tp_reload": tp_reload_files,
    }
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    sheet_path = os.path.join(out_dir, "_contact_sheet.png")
    _build_contact_sheet(
        vm_idle, vm_fire, vm_reload, proj, tp_idle, tp_fire, tp_reload, sheet_path
    )
    print(
        f"[c3_paintball] Done -> {out_dir} | "
        f"vm=({len(vm_idle_files)}+{len(vm_fire_files)}+{len(vm_reload_files)}), "
        f"proj={len(proj_files)}, "
        f"tp=({len(tp_idle_files)}+{len(tp_fire_files)}+{len(tp_reload_files)})"
    )
    return manifest


if __name__ == "__main__":
    build_concept3()
