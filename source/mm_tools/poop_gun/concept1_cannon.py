"""Design 1: "THE DOOKIE BAZOOKA" (The Poop Cannon) asset & animation baker.

Generates 60-FPS sprite sequences and manifest for `build_poop_concepts_html.py`:
  - First-person viewmodel (`420x360`): 60 idle, 20 fire/recoil, 18 reload frames
    (`work/c1_cannon/vm_idle_*.png`, `vm_fire_*.png`, `vm_reload_*.png`).
  - Projectile (`160x180`): 16-angle x 8-frame fast-sprinting fat bloke with
    waving arms from `dance_48` + leg-pumping bounce on `turn_16` + mud & flies
    (`work/c1_cannon/proj_a*_f*.png`).
  - Third-person enemy shooter (`280x320`): 60 idle, 20 fire, 18 reload frames
    (`work/c1_cannon/tp_idle_*.png`, `tp_fire_*.png`, `tp_reload_*.png`).
  - Contact sheets (`sheet_*.png`) and `manifest.json`.
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

CANNON_SRC_JPG = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841"
    r"\cannon_body_c1_1794663337260.jpg"
)
ENEMY_SRC_JPG = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841"
    r"\enemy_shooter_base_1794663595737.jpg"
)

OUT_DIR = os.path.join(WORK_DIR, "c1_cannon")
VM_WH = (420, 360)
PROJ_WH = (160, 180)
TP_WH = (320, 320)

# Glass chamber quadrilateral in 1024x1024 cannon_body_c1 coordinates
GLASS_QUAD = np.array(
    [(553, 305), (722, 332), (703, 454), (534, 424)], dtype=np.int32
)
PSI_CENTER = (410, 300)
PSI_RADIUS = 43


def _load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def _save_rgba(rgba: np.ndarray, path: str) -> None:
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def _make_contact_sheet(
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
        sheet.paste(Image.fromarray(rs, "RGBA"), (x0, y0), Image.fromarray(rs, "RGBA"))
        lbl = labels[idx] if labels is not None else str(idx)
        draw.text((x0 + 4, y0 + 3), lbl, fill=(255, 230, 80, 255))
    return np.asarray(sheet)


def _load_assets() -> Dict[str, object]:
    heads: Dict[str, np.ndarray] = {}
    for p in sorted(glob.glob(os.path.join(WORK_DIR, "heads", "*.png"))):
        name = os.path.splitext(os.path.basename(p))[0]
        heads[name] = _load_rgba(p)

    fx: Dict[str, np.ndarray] = {}
    for p in sorted(glob.glob(os.path.join(WORK_DIR, "fx", "*.png"))):
        name = os.path.splitext(os.path.basename(p))[0]
        if not name.startswith("_verify"):
            fx[name] = _load_rgba(p)

    turn_16 = [
        _load_rgba(p)
        for p in sorted(glob.glob(os.path.join(WORK_DIR, "turn_16", "turn_*.png")))
    ]
    dance_48 = [
        _load_rgba(p)
        for p in sorted(glob.glob(os.path.join(WORK_DIR, "dance_48", "dance_*.png")))
    ]

    enemy_path = os.path.join(WORK_DIR, "fx", "enemy_shooter_base.png")
    if os.path.exists(enemy_path):
        enemy_base = _load_rgba(enemy_path)
    else:
        rgb = np.asarray(Image.open(ENEMY_SRC_JPG).convert("RGB"))
        enemy_base = key_white_studio_plate(rgb, protect_box=(180, 120, 840, 880))

    return {
        "heads": heads,
        "fx": fx,
        "turn_16": turn_16,
        "dance_48": dance_48,
        "enemy_base": enemy_base,
    }


def _build_cannon_rig() -> Dict[str, np.ndarray]:
    """Key `cannon_body_c1`, remove static PSI needle, extract glass cavity + specular,
    and split the red plunger cup for independent compression squash-and-stretch.
    """
    rgb = np.asarray(Image.open(CANNON_SRC_JPG).convert("RGB"))
    h, w = rgb.shape[:2]

    # Protect the cream PSI gauge dial from white punchout
    rgba = key_white_studio_plate(rgb, protect_box=(340, 230, 485, 375))

    # Also clean shaded near-white studio pockets trapped inside pipe loops (foregrip loop & rear U-bend)
    arr_f = rgb.astype(np.float32)
    hi_p = arr_f.max(axis=2)
    lo_p = arr_f.min(axis=2)
    sat_p = (hi_p - lo_p) / np.maximum(hi_p, 1.0)
    yy_p, xx_p = np.mgrid[0:h, 0:w]
    in_psi = (xx_p >= 335) & (xx_p <= 490) & (yy_p >= 225) & (yy_p <= 380)
    trapped_loop = (~in_psi) & (rgba[..., 3] > 0) & (lo_p > 214.0) & (sat_p < 0.11)
    if np.any(trapped_loop):
        from scipy import ndimage
        tlbl, tn = ndimage.label(trapped_loop)
        sizes = ndimage.sum(trapped_loop, tlbl, range(1, tn + 1))
        for tidx, sz in enumerate(sizes, start=1):
            if sz >= 140:
                rgba[tlbl == tidx] = 0

    # 1. Remove static PSI needle cleanly via localized Telea inpainting inside dial face
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = PSI_CENTER
    dist_c = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    # Line segment from (373, 336) through (410, 300) to (426, 284)
    p0 = np.array([371.0, 338.0], dtype=np.float32)
    p1 = np.array([428.0, 282.0], dtype=np.float32)
    seg = p1 - p0
    seg_len2 = float(np.dot(seg, seg))
    t_proj = np.clip(
        ((xx - p0[0]) * seg[0] + (yy - p0[1]) * seg[1]) / seg_len2, 0.0, 1.0
    )
    proj_x = p0[0] + t_proj * seg[0]
    proj_y = p0[1] + t_proj * seg[1]
    dist_line = np.sqrt((xx - proj_x) ** 2 + (yy - proj_y) ** 2)

    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    is_red_tip = (rgb[..., 0].astype(np.float32) - rgb[..., 2].astype(np.float32)) > 42.0
    needle_mask = (
        (dist_c <= PSI_RADIUS - 3)
        & (
            (dist_c <= 8.5)
            | ((dist_line <= 6.2) & ((lum < 145.0) | is_red_tip))
        )
    ).astype(np.uint8) * 255
    needle_mask = cv2.dilate(needle_mask, np.ones((3, 3), np.uint8), iterations=1)
    # Keep "DANGER" red text above y=282 untouched
    needle_mask[:282, :] = 0
    inpainted_bgr = cv2.inpaint(
        cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2BGR),
        needle_mask,
        inpaintRadius=4,
        flags=cv2.INPAINT_TELEA,
    )
    rgba[..., :3] = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)

    # 2. Extract glass chamber mask & glass highlight/scratch overlay
    glass_mask_u8 = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(glass_mask_u8, [GLASS_QUAD], 255)
    glass_mask_f = cv2.GaussianBlur(glass_mask_u8.astype(np.float32) / 255.0, (5, 5), 1.2)

    # Build translucent glass reflection + scratch overlay from original plate
    glass_overlay = np.zeros((h, w, 4), dtype=np.uint8)
    inside = glass_mask_f > 0.08
    # Scratches & dark inner cylinder rim
    scratch_a = np.clip((218.0 - lum) * 1.15, 0.0, 145.0)
    # Bright white specular band across upper tube
    spec_a = np.clip((lum - 244.0) * 10.0, 0.0, 105.0)

    # Curved cylinder highlight along tube axis (~+9.5 deg)
    ang = math.radians(9.5)
    ca, sa = math.cos(ang), math.sin(ang)
    ty = -(xx - 630.0) * sa + (yy - 380.0) * ca  # transverse across tube height (~-60..+60)
    cyl_glare = np.exp(-0.5 * ((ty + 20.0) / 11.0) ** 2) * 85.0
    cyl_rim_bot = np.exp(-0.5 * ((ty - 50.0) / 7.0) ** 2) * 55.0

    ov_rgb = np.zeros((h, w, 3), dtype=np.float32)
    ov_a = np.zeros((h, w), dtype=np.float32)

    # Dark scratches
    sc_w = np.clip(scratch_a / 145.0, 0.0, 1.0)
    ov_rgb += sc_w[..., None] * np.array([42.0, 38.0, 32.0])
    # Specular white glare
    hi_w = np.clip((spec_a + cyl_glare + cyl_rim_bot) / 140.0, 0.0, 1.0) * (1.0 - 0.65 * sc_w)
    ov_rgb += hi_w[..., None] * np.array([245.0, 252.0, 255.0])
    ov_a = np.clip((scratch_a + 0.65 * spec_a + cyl_glare + cyl_rim_bot) * glass_mask_f, 0.0, 185.0)

    glass_overlay[..., :3] = np.clip(np.round(ov_rgb), 0, 255).astype(np.uint8)
    glass_overlay[..., 3] = np.clip(np.round(ov_a), 0, 255).astype(np.uint8)
    glass_overlay[~inside] = 0

    # Punch clear glass window out of main cannon body so chamber + heads sit cleanly inside
    rgba_body = rgba.copy()
    rgba_body[..., 3] = np.clip(
        np.round(rgba_body[..., 3].astype(np.float32) * (1.0 - glass_mask_f)), 0, 255
    ).astype(np.uint8)
    rgba_body[rgba_body[..., 3] < 4] = 0

    # 3. Separate red rubber plunger cup so it can compress & snap on fire
    # Collar boundary line at x ~ 282 - 0.12*(y - 400), y < 550
    bound_x = 282.0 - 0.12 * (yy - 400.0)
    plunger_w = np.clip((bound_x + 4.0 - xx) / 8.0, 0.0, 1.0) * (yy < 550.0).astype(np.float32)
    plunger_rgba = rgba_body.copy()
    plunger_rgba[..., 3] = np.clip(
        np.round(plunger_rgba[..., 3].astype(np.float32) * plunger_w), 0, 255
    ).astype(np.uint8)
    plunger_rgba[plunger_rgba[..., 3] < 4] = 0

    body_no_plunger = rgba_body.copy()
    # Keep slight overlap under plunger neck so squash never reveals a gap
    body_keep = np.clip((xx - (bound_x - 10.0)) / 8.0, 0.0, 1.0)
    body_keep = np.where(yy >= 550.0, 1.0, body_keep)
    body_no_plunger[..., 3] = np.clip(
        np.round(body_no_plunger[..., 3].astype(np.float32) * body_keep), 0, 255
    ).astype(np.uint8)
    body_no_plunger[body_no_plunger[..., 3] < 4] = 0

    return {
        "body": body_no_plunger,
        "full_body": rgba_body,
        "plunger": plunger_rgba,
        "glass_mask": glass_mask_f,
        "glass_overlay": glass_overlay,
    }


def _draw_psi_needle(canvas: np.ndarray, angle_deg: float) -> np.ndarray:
    """Draw sharp animated PSI gauge needle pivoting from `PSI_CENTER`.
    `angle_deg = 0` points straight UP; negative = counter-clockwise toward EMPTY (-135),
    positive = clockwise toward DANGER (+125).
    """
    out = canvas.copy()
    cx, cy = PSI_CENTER
    rad = math.radians(angle_deg - 90.0)
    ca, sa = math.cos(rad), math.sin(rad)
    px, py = -sa, ca

    tip_len = 36.0
    tail_len = 13.0
    tip = (int(round(cx + ca * tip_len)), int(round(cy + sa * tip_len)))
    mid = (int(round(cx + ca * (tip_len * 0.62))), int(round(cy + sa * (tip_len * 0.62))))
    tail = (int(round(cx - ca * tail_len)), int(round(cy - sa * tail_len)))

    # Subtle drop shadow on dial face
    sh_pts = np.array(
        [
            [cx + px * 3.0 + 2, cy + py * 3.0 + 2],
            [cx - px * 3.0 + 2, cy - py * 3.0 + 2],
            [tip[0] + 2, tip[1] + 2],
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(out, sh_pts, (40, 35, 25, 110), lineType=cv2.LINE_AA)

    # Tapered black needle body
    body_pts = np.array(
        [
            [int(round(cx + px * 3.2 - ca * tail_len)), int(round(cy + py * 3.2 - sa * tail_len))],
            [int(round(cx - px * 3.2 - ca * tail_len)), int(round(cy - py * 3.2 - sa * tail_len))],
            [int(round(mid[0] - px * 1.4)), int(round(mid[1] - py * 1.4))],
            [int(round(mid[0] + px * 1.4)), int(round(mid[1] + py * 1.4))],
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(out, body_pts, (24, 24, 26, 255), lineType=cv2.LINE_AA)

    # Red danger tip
    tip_pts = np.array(
        [
            [int(round(mid[0] + px * 1.8)), int(round(mid[1] + py * 1.8))],
            [int(round(mid[0] - px * 1.8)), int(round(mid[1] - py * 1.8))],
            [tip[0], tip[1]],
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(out, tip_pts, (205, 28, 22, 255), lineType=cv2.LINE_AA)

    # Brass/steel center hub rivet
    cv2.circle(out, (cx, cy), 6, (45, 44, 42, 255), -1, cv2.LINE_AA)
    cv2.circle(out, (cx, cy), 4, (158, 152, 138, 255), -1, cv2.LINE_AA)
    cv2.circle(out, (cx - 1, cy - 1), 1, (230, 225, 210, 255), -1, cv2.LINE_AA)
    return out


def _render_glass_heads_chamber(
    rig: Dict[str, np.ndarray],
    heads: Dict[str, np.ndarray],
    mode: str,
    f_idx: int,
    n_frames: int,
) -> np.ndarray:
    """Render the murky glass chamber with 4 expressive animated heads arguing/panicking."""
    glass_mask = rig["glass_mask"]
    h, w = glass_mask.shape
    chamber = np.zeros((h, w, 4), dtype=np.uint8)

    # Local ROI bounding the glass tube for fast compositing
    ys, xs = np.nonzero(glass_mask > 0.02)
    x0, x1 = max(0, int(xs.min()) - 4), min(w, int(xs.max()) + 5)
    y0, y1 = max(0, int(ys.min()) - 4), min(h, int(ys.max()) + 5)
    rh, rw = y1 - y0, x1 - x0

    roi = np.zeros((rh, rw, 4), dtype=np.uint8)
    # Murky green-brown poop-sludge glass interior backdrop
    yy, xx = np.mgrid[0:rh, 0:rw].astype(np.float32)
    grad_v = np.clip(yy / max(1.0, float(rh)), 0.0, 1.0)
    bg_r = 78.0 - 38.0 * grad_v
    bg_g = 76.0 - 36.0 * grad_v
    bg_b = 34.0 - 18.0 * grad_v
    roi[..., 0] = np.clip(bg_r, 0, 255).astype(np.uint8)
    roi[..., 1] = np.clip(bg_g, 0, 255).astype(np.uint8)
    roi[..., 2] = np.clip(bg_b, 0, 255).astype(np.uint8)
    roi[..., 3] = 225

    t_norm = f_idx / float(max(1, n_frames))
    tau = 2.0 * math.pi

    # Rising stink bubbles behind the heads
    for b in range(10):
        bx = 16.0 + ((b * 37) % max(20, rw - 32))
        by_cycle = (b * 0.13 + t_norm * (1.0 + (b % 2))) % 1.0
        by = rh - 8.0 - by_cycle * (rh - 16.0)
        br = 3 + (b % 4)
        cv2.circle(roi, (int(bx), int(by)), br, (132, 148, 62, 140), -1, cv2.LINE_AA)
        cv2.circle(roi, (int(bx - 1), int(by - 1)), max(1, br // 2), (205, 224, 128, 175), -1, cv2.LINE_AA)

    # 4 distinct expressive heads inside the tube:
    # Slot 0: Cross-eyed snarler
    # Slot 1: Turbaned big-grin (swaps with turban yell when shouting!)
    # Slot 2: Oiled-hair yelling
    # Slot 3: Video screaming head (cycles open/shut mouth & side-looks!)
    turban_alt = heads.get("head_turban_yell", heads.get("head_laugh_tilt", heads["head_turban_grin"]))
    head_slots = [
        {
            "cx": 566.0 - x0,
            "cy": 365.0 - y0,
            "size": 76,
            "phase": 0.0,
            "imgs": [heads["head_cross"], heads.get("head_side_yell_r", heads["head_cross"])],
            "panic": heads["head_cross"],
            "base_tilt": -7.0,
        },
        {
            "cx": 608.0 - x0,
            "cy": 374.0 - y0,
            "size": 84,
            "phase": 1.65,
            "imgs": [heads["head_turban_grin"], turban_alt],
            "panic": turban_alt,
            "base_tilt": 5.0,
        },
        {
            "cx": 649.0 - x0,
            "cy": 382.0 - y0,
            "size": 78,
            "phase": 3.25,
            "imgs": [heads["head_oiled_yell"], heads.get("head_laugh_tilt", heads["head_oiled_yell"])],
            "panic": heads["head_oiled_yell"],
            "base_tilt": 9.0,
        },
        {
            "cx": 688.0 - x0,
            "cy": 391.0 - y0,
            "size": 76,
            "phase": 4.80,
            "imgs": [
                heads.get("head_scream_front", heads["head_cross"]),
                heads.get("head_wide_grin", heads["head_cross"]),
                heads.get("head_side_yell_l", heads["head_cross"]),
                heads.get("head_sky_gasp", heads["head_cross"]),
            ],
            "panic": heads.get("head_sky_gasp", heads.get("head_scream_front", heads["head_cross"])),
            "base_tilt": -10.0,
        },
    ]

    for idx, slot in enumerate(head_slots):
        ph = slot["phase"]
        if mode == "idle":
            # Bob back & forth, sway side to side, tilt like arguing, squash/stretch, open/shut!
            bob_x = 5.5 * math.sin(tau * 2.0 * t_norm + ph)
            bob_y = 7.5 * math.sin(tau * 3.0 * t_norm + ph * 1.3)
            tilt = slot["base_tilt"] + 13.0 * math.sin(tau * 2.0 * t_norm + ph * 0.8)
            chomp = max(0.0, math.sin(tau * 5.0 * t_norm + ph * 1.7))
            sx = 1.0 + 0.08 * math.sin(tau * 4.0 * t_norm + ph) - 0.07 * chomp
            sy = (1.0 / max(0.75, sx)) * (1.0 + 0.14 * chomp)
            # Argument mouth open/shut face swap
            sw_idx = int((t_norm * 6.0 + idx * 0.45)) % len(slot["imgs"])
            h_img = slot["imgs"][sw_idx]
            sc_mul = 1.0
        elif mode == "fire":
            # Panic scramble! Slam against tube wall, vibrate violently, wide screams
            p = f_idx / float(max(1, n_frames - 1))
            panic_env = math.sin(math.pi * min(1.0, p * 1.15))
            bob_x = 8.0 * panic_env + 3.8 * math.sin(f_idx * 2.7 + idx * 1.9)
            bob_y = -9.0 * panic_env + 4.5 * math.cos(f_idx * 3.1 + idx * 2.3)
            tilt = slot["base_tilt"] + 22.0 * math.sin(f_idx * 2.4 + ph)
            sx = 0.90 + 0.12 * math.sin(f_idx * 3.3 + idx)
            sy = 1.16 + 0.10 * math.cos(f_idx * 2.9 + idx)
            h_img = slot["panic"] if f_idx < 14 else slot["imgs"][0]
            sc_mul = 1.04
        else:  # reload: chamber vents, fresh angry head bounces in from the right!
            p = f_idx / float(max(1, n_frames - 1))
            if idx == 3:
                # Fresh angry head bounces in at reload frames 4..17!
                if f_idx < 4:
                    h_img = slot["imgs"][0]
                    bob_x = 34.0
                    bob_y = -18.0
                    tilt = -25.0
                    sx, sy = 0.65, 1.25
                    sc_mul = max(0.05, 0.35 - f_idx * 0.08)
                else:
                    u = (f_idx - 4) / float(max(1, n_frames - 5))
                    # Elastic bounce-in overshoot
                    bounce = 1.0 - math.exp(-5.0 * u) * math.cos(u * math.pi * 3.2)
                    bob_x = (1.0 - bounce) * 42.0
                    bob_y = -abs(math.sin(u * math.pi * 2.5)) * (1.0 - u) * 18.0
                    tilt = (1.0 - u) * 28.0 * math.sin(u * math.pi * 3.0)
                    sx = 1.0 + 0.18 * (1.0 - u) * math.sin(u * math.pi * 4.0)
                    sy = 1.0 / max(0.75, sx)
                    h_img = heads["head_oiled_yell"] if (f_idx % 4 < 2) else heads["head_cross"]
                    sc_mul = 0.45 + 0.60 * bounce
            else:
                bob_x = -8.0 * math.sin(math.pi * p) + 3.0 * math.sin(f_idx * 1.4 + ph)
                bob_y = 6.0 * math.sin(math.pi * p) + 4.0 * math.cos(f_idx * 1.6 + ph)
                tilt = slot["base_tilt"] + 10.0 * math.sin(f_idx * 1.2 + ph)
                sx, sy = 1.0 + 0.06 * math.sin(f_idx + ph), 1.0 - 0.05 * math.sin(f_idx + ph)
                h_img = slot["imgs"][f_idx % len(slot["imgs"])]
                sc_mul = 1.0

        sz = max(20, int(round(slot["size"] * sc_mul)))
        h_rs = resize_premul(h_img, (sz, sz))
        pad = int(math.ceil(sz * 0.45))
        oh, ow = sz + 2 * pad, sz + 2 * pad
        h_pad = np.zeros((oh, ow, 4), dtype=np.uint8)
        h_pad[pad:pad + sz, pad:pad + sz] = h_rs

        warped = warp_rgba(
            h_pad,
            angle_deg=tilt,
            sx=sx,
            sy=sy,
            dx=0.0,
            dy=0.0,
            pivot=(ow * 0.5, oh * 0.5),
            out_hw=(oh, ow),
        )
        px = slot["cx"] + bob_x - ow * 0.5
        py = slot["cy"] + bob_y - oh * 0.5
        roi = alpha_over(roi, warped, px, py)

    # Clip strictly to glass_mask ROI
    roi_mask = glass_mask[y0:y1, x0:x1]
    roi[..., 3] = np.clip(
        np.round(roi[..., 3].astype(np.float32) * roi_mask), 0, 255
    ).astype(np.uint8)
    roi[roi[..., 3] < 3] = 0
    chamber[y0:y1, x0:x1] = roi
    return chamber


def _draw_brass_flagpole(
    canvas: np.ndarray,
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    thickness: int = 8,
) -> np.ndarray:
    """Draw a metallic shaded brass flagpole with bolted collar and top finial ball."""
    out = canvas.copy()
    x0, y0 = int(round(p0[0])), int(round(p0[1]))
    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    # Dark outline + mid brass + highlight ridge
    cv2.line(out, (x0, y0), (x1, y1), (36, 26, 12, 255), thickness + 4, cv2.LINE_AA)
    cv2.line(out, (x0, y0), (x1, y1), (168, 134, 58, 255), thickness, cv2.LINE_AA)
    cv2.line(out, (x0 - 1, y0), (x1 - 1, y1), (235, 206, 118, 255), max(2, thickness // 3), cv2.LINE_AA)
    # Mounting bracket at p0
    cv2.circle(out, (x0, y0), thickness + 2, (36, 26, 12, 255), -1, cv2.LINE_AA)
    cv2.circle(out, (x0, y0), thickness, (148, 118, 52, 255), -1, cv2.LINE_AA)
    # Gold sphere finial at top p1
    cv2.circle(out, (x1, y1), thickness + 3, (36, 26, 12, 255), -1, cv2.LINE_AA)
    cv2.circle(out, (x1, y1), thickness + 1, (206, 168, 68, 255), -1, cv2.LINE_AA)
    cv2.circle(out, (x1 - 2, y1 - 2), max(2, thickness // 2), (255, 240, 170, 255), -1, cv2.LINE_AA)
    return out


def render_vm_sequence(
    rig: Dict[str, np.ndarray],
    assets: Dict[str, object],
    mode: str,
    n_frames: int,
) -> List[np.ndarray]:
    """Render first-person viewmodel frames at `420x360` (2x supersampled internal rig)."""
    heads: Dict[str, np.ndarray] = assets["heads"]  # type: ignore[assignment]
    fx: Dict[str, np.ndarray] = assets["fx"]        # type: ignore[assignment]
    tau = 2.0 * math.pi

    # 2x supersampled canvas (840x720 -> 420x360) for razor-sharp cannon + flags + gauge
    SS_W, SS_H = VM_WH[0] * 2, VM_WH[1] * 2
    scale_gun = 0.71
    # Position cannon in 840x720 so right gauntlet anchors to bottom-right and BOTH flags stay unclipped
    base_ox, base_oy = 96.0, 166.0

    # Sticky mud globs clinging to the gun in 1024-space
    gun_globs = [
        (resize_premul(fx["mud_glob_00"], (64, 64)), (135, 395)),
        (resize_premul(fx["mud_glob_02"], (54, 54)), (215, 270)),
        (resize_premul(fx["mud_glob_03"], (50, 50)), (520, 445)),
    ]

    frames: List[np.ndarray] = []
    for f_idx in range(n_frames):
        t_norm = f_idx / float(max(1, n_frames))

        # --- Motion envelopes per mode ---
        if mode == "idle":
            recoil_dx = 3.0 * math.sin(tau * t_norm)
            recoil_dy = 5.5 * math.sin(tau * 2.0 * t_norm)
            recoil_rot = 1.1 * math.sin(tau * t_norm + 0.5)
            plunger_sx, plunger_sy = 1.0 + 0.015 * math.sin(tau * 2.0 * t_norm), 1.0
            psi_ang = 52.0 + 18.0 * math.sin(tau * t_norm) + 8.5 * math.sin(tau * 11.0 * t_norm)
            flag_amp = 1.05 + 0.12 * math.sin(tau * t_norm)
            flag_phase = tau * 2.0 * t_norm
        elif mode == "fire":
            p = f_idx / float(max(1, n_frames - 1))
            if f_idx < 2:
                # Anticipation squeeze before massive fart blast
                recoil_dx = -4.0 * (f_idx + 1)
                recoil_dy = 2.0 * (f_idx + 1)
                recoil_rot = 2.0 * (f_idx + 1)
                plunger_sx, plunger_sy = 0.74, 1.15
                psi_ang = 115.0 + 12.0 * f_idx
            else:
                k = (f_idx - 2) / float(max(1, n_frames - 3))
                kick = math.exp(-4.2 * k) * math.sin(min(math.pi * 0.5, k * 4.5 + 0.5))
                kick = math.exp(-3.6 * k)
                recoil_dx = 54.0 * kick
                recoil_dy = 42.0 * kick
                recoil_rot = -9.5 * kick
                # Plunger snaps forward then oscillates elastically
                snap = math.exp(-5.0 * k) * math.cos(k * math.pi * 3.5)
                plunger_sx = 1.0 + 0.22 * snap
                plunger_sy = 1.0 - 0.10 * snap
                psi_ang = 128.0 * (1.0 - min(1.0, k * 1.4)) - 122.0 * min(1.0, k * 1.4)
            flag_amp = 1.55 if f_idx < 10 else 1.20
            flag_phase = tau * (1.2 + 2.4 * p)
        else:  # reload
            p = f_idx / float(max(1, n_frames - 1))
            lift = math.sin(math.pi * p)
            recoil_dx = 22.0 * lift
            recoil_dy = 26.0 * lift
            recoil_rot = -11.5 * lift
            plunger_sx = 1.0 - 0.08 * math.sin(math.pi * 3.0 * p)
            plunger_sy = 1.0 + 0.05 * math.sin(math.pi * 3.0 * p)
            # 3 ratchet pressure surges back up to DANGER
            psi_ang = -118.0 + 170.0 * (p ** 0.75) + 14.0 * math.sin(p * math.pi * 6.0)
            flag_amp = 1.25
            flag_phase = tau * 2.0 * p

        # 1. Assemble 1024x1024 cannon interior + body + gauge + plunger + mud globs
        gun_1024 = _render_glass_heads_chamber(rig, heads, mode, f_idx, n_frames)
        gun_1024 = alpha_over(gun_1024, rig["body"], 0, 0)

        # Compress/extend plunger cup around neck pivot (278, 405)
        plunger_warped = warp_rgba(
            rig["plunger"],
            angle_deg=0.0,
            sx=plunger_sx,
            sy=plunger_sy,
            dx=0.0,
            dy=0.0,
            pivot=(278.0, 405.0),
            out_hw=(1024, 1024),
        )
        gun_1024 = alpha_over(gun_1024, plunger_warped, 0, 0)
        gun_1024 = alpha_over(gun_1024, rig["glass_overlay"], 0, 0)
        gun_1024 = _draw_psi_needle(gun_1024, psi_ang)

        for glob_im, (gx, gy) in gun_globs:
            # Slightly wobble leftmost glob with plunger
            jx = gx + (plunger_sx - 1.0) * -90.0 if gx < 180 else gx
            gun_1024 = alpha_over(gun_1024, glob_im, jx, gy)

        # Scale & recoil-warp gun into 840x720 supersampled canvas
        gw = int(round(1024 * scale_gun))
        gh = int(round(1024 * scale_gun))
        gun_rs = resize_premul(gun_1024, (gw, gh))

        # Place on 840x720 canvas & apply recoil warp around trigger grip (620, 620)
        gun_ss = np.zeros((SS_H, SS_W, 4), dtype=np.uint8)
        gun_ss = alpha_over(gun_ss, gun_rs, base_ox, base_oy)
        pivot_ss = (base_ox + 680.0 * scale_gun, base_oy + 760.0 * scale_gun)
        gun_ss = warp_rgba(
            gun_ss,
            angle_deg=recoil_rot,
            sx=1.0,
            sy=1.0,
            dx=recoil_dx,
            dy=recoil_dy,
            pivot=pivot_ss,
            out_hw=(SS_H, SS_W),
        )

        # Helper to transform 1024-cannon coordinates to 840x720 warped coords
        rad_r = math.radians(-recoil_rot)  # inverse of OpenCV CCW convention for point transform
        cr, sr = math.cos(rad_r), math.sin(rad_r)

        def _gun_pt(x1024: float, y1024: float) -> Tuple[float, float]:
            px0 = base_ox + x1024 * scale_gun
            py0 = base_oy + y1024 * scale_gun
            vx = px0 - pivot_ss[0]
            vy = py0 - pivot_ss[1]
            return (
                pivot_ss[0] + vx * cr - vy * sr + recoil_dx,
                pivot_ss[1] + vx * sr + vy * cr + recoil_dy,
            )

        # 2. Add TWO LARGE waving saffron-white-green tricolor flags on brass poles
        # Left flag: pole mounts on front barrel collar, angles up-left, flag flies LEFT
        lf_base = _gun_pt(272.0, 385.0)
        lf_top = (lf_base[0] - 46.0, lf_base[1] - 252.0)
        # Right flag: pole mounts on rear glass/breech collar, angles slightly up-left/vertical so cloth flies RIGHT cleanly inside 420x360!
        rf_base = _gun_pt(718.0, 342.0)
        rf_top = (rf_base[0] - 12.0, rf_base[1] - 246.0)

        # Render flags behind poles & cannon upper collar for natural mounting depth
        canvas_ss = np.zeros((SS_H, SS_W, 4), dtype=np.uint8)

        # Left waving tricolor flag (244x152 in 2x space -> 122x76 in 420x360!)
        flag_l = render_tricolor_flag(244, 152, phase=flag_phase, pole_left=False, amp=flag_amp)
        flag_l_rot = warp_rgba(
            flag_l,
            angle_deg=10.0,
            sx=1.0,
            sy=1.0,
            dx=0.0,
            dy=0.0,
            pivot=(234.0, 36.0),
            out_hw=(196, 272),
        )
        canvas_ss = _draw_brass_flagpole(canvas_ss, lf_base, lf_top, thickness=8)
        canvas_ss = alpha_over(canvas_ss, flag_l_rot, lf_top[0] - 230.0, lf_top[1] - 24.0)

        # Right waving tricolor flag (216x136 in 2x space -> 108x68 in 420x360!)
        flag_r = render_tricolor_flag(216, 136, phase=flag_phase + 1.25, pole_left=True, amp=flag_amp)
        flag_r_rot = warp_rgba(
            flag_r,
            angle_deg=-6.0,
            sx=1.0,
            sy=1.0,
            dx=0.0,
            dy=0.0,
            pivot=(10.0, 34.0),
            out_hw=(180, 244),
        )
        canvas_ss = _draw_brass_flagpole(canvas_ss, rf_base, rf_top, thickness=8)
        canvas_ss = alpha_over(canvas_ss, flag_r_rot, rf_top[0] - 10.0, rf_top[1] - 22.0)

        # Composite cannon body over the flagpoles so brackets look bolted behind/into collars
        canvas_ss = alpha_over(canvas_ss, gun_ss, 0, 0)

        # Downsample 840x720 -> 420x360 cleanly
        frame = resize_premul(canvas_ss, VM_WH)

        # 3. Muzzle green/brown fart blast & mud puff (in native 420x360 space)
        muzzle_ss = _gun_pt(85.0, 375.0)
        muzzle_vm = (muzzle_ss[0] * 0.5, muzzle_ss[1] * 0.5)
        tube_ss = _gun_pt(630.0, 375.0)
        tube_vm = (tube_ss[0] * 0.5, tube_ss[1] * 0.5)

        if mode == "fire" and 2 <= f_idx <= 16:
            bf = (f_idx - 2) / 14.0
            # Expanding toxic green-brown fart cloud + mud splatter burst
            m1 = fx[f"mist_0{(f_idx % 3) * 2 + 1}"]  # green-brown fart mists 01, 03, 05
            m2 = fx[f"mist_0{(f_idx % 3) * 2}"]      # earthy brown mud mists 00, 02, 04
            m_sz1 = int(round(92 + 115 * bf))
            m_sz2 = int(round(72 + 88 * bf))
            op = max(0.0, 1.0 - bf * 0.92)
            frame = alpha_over(
                frame,
                resize_premul(m1, (m_sz1, m_sz1)),
                muzzle_vm[0] - m_sz1 * 0.62 - 22.0 * bf,
                muzzle_vm[1] - m_sz1 * 0.54 - 8.0 * bf,
                opacity=op,
            )
            frame = alpha_over(
                frame,
                resize_premul(m2, (m_sz2, m_sz2)),
                muzzle_vm[0] - m_sz2 * 0.48 - 10.0 * bf,
                muzzle_vm[1] - m_sz2 * 0.46 + 4.0 * bf,
                opacity=op * 0.9,
            )
            if f_idx <= 9:
                sp = fx[f"splat_0{f_idx % 4}"]
                sp_sz = int(round(58 + 75 * (f_idx - 2) / 7.0))
                frame = alpha_over(
                    frame,
                    resize_premul(sp, (sp_sz, sp_sz)),
                    muzzle_vm[0] - sp_sz * 0.58,
                    muzzle_vm[1] - sp_sz * 0.52,
                    opacity=max(0.0, 1.0 - (f_idx - 2) / 8.0),
                )
            # Flying mud chunks blasting out toward top-left crosshair
            for g in range(4):
                gp = (f_idx - 2) / 14.0
                ang = math.radians(190.0 + (g - 1.5) * 18.0)
                dist = (18.0 + g * 12.0) + gp * (75.0 + g * 18.0)
                gx = muzzle_vm[0] + math.cos(ang) * dist
                gy = muzzle_vm[1] + math.sin(ang) * dist + 24.0 * gp * gp
                gim = resize_premul(fx[f"mud_glob_0{g}"], (22, 22))
                frame = alpha_over(frame, gim, gx - 11, gy - 11, opacity=max(0.0, 1.0 - gp))

        elif mode == "reload" and 2 <= f_idx <= 10:
            # Venting stink steam puff from rear glass collar
            vp = (f_idx - 2) / 8.0
            vm_puff = resize_premul(fx["mist_01"], (int(44 + 40 * vp), int(44 + 40 * vp)))
            frame = alpha_over(
                frame,
                vm_puff,
                tube_vm[0] + 15.0 - vm_puff.shape[1] * 0.5,
                tube_vm[1] - 28.0 - 24.0 * vp - vm_puff.shape[0] * 0.5,
                opacity=0.65 * (1.0 - vp),
            )

        # 4. 14 buzzing flies orbiting the muzzle and glass head tube!
        fly_scale = 0.92 if mode != "fire" else 1.05
        fly_t = (f_idx / float(max(1, n_frames))) if mode == "idle" else (f_idx / 24.0) % 1.0
        frame = render_fly_swarm(
            frame,
            centers=[
                (muzzle_vm[0] + 6.0, muzzle_vm[1] - 4.0),
                (tube_vm[0] - 8.0, tube_vm[1] - 6.0),
            ],
            t_norm=fly_t,
            n_flies=14,
            scale=fly_scale,
        )
        frames.append(frame)

    return frames


def _clean_arm_hip_white_gaps(rgba: np.ndarray) -> np.ndarray:
    """Remove any trapped white triangles between hanging arms and tricolor shorts in `turn_16`."""
    out = rgba.copy()
    h, w = out.shape[:2]
    rgb = out[..., :3].astype(np.float32)
    a = out[..., 3]
    hi = rgb.max(axis=2)
    lo = rgb.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)

    # Trapped studio white gaps sit near the outer left/right edges of the torso/shorts
    # (x < 0.34*w or x > 0.66*w) in the mid-body band (0.44*h .. 0.78*h)
    yy, xx = np.mgrid[0:h, 0:w]
    side_band = ((xx < int(w * 0.36)) | (xx > int(w * 0.64))) & (yy > int(h * 0.42)) & (yy < int(h * 0.80))
    gap = (a > 10) & side_band & (lo > 226.0) & (sat < 0.08)

    # Also remove small bright white isolated fringe islands touching alpha==0 in that band
    if np.any(gap):
        from scipy import ndimage
        lbl, n = ndimage.label(gap)
        bg_dil = ndimage.binary_dilation(a < 20, iterations=3)
        for idx in range(1, n + 1):
            comp = lbl == idx
            if np.any(comp & bg_dil):
                # Soft-feather 1.5px around cleared gap
                out[comp] = 0
    return out


# Angle-matched dance_48 frame sequences for 16 turnaround angles (0=front, 4=left, 8=back, 12=right)
DANCE_ANGLE_BANK: List[List[int]] = [
    [1, 3, 5, 22, 30, 33, 36, 40],      # a00: front
    [6, 7, 8, 23, 24, 29, 31, 41],      # a01: front-left-ish
    [8, 9, 10, 9, 8, 9, 10, 9],         # a02: front-left 3/4
    [10, 11, 10, 11, 10, 11, 10, 11],   # a03: left-ish
    [11, 12, 11, 12, 11, 12, 11, 12],   # a04: left profile
    [12, 13, 12, 13, 12, 13, 12, 13],   # a05: back-left 3/4
    [13, 14, 13, 14, 13, 14, 13, 14],   # a06: back-left
    [14, 15, 16, 15, 14, 15, 16, 15],   # a07: back-ish
    [15, 16, 14, 15, 16, 15, 14, 15],   # a08: straight back
    [16, 17, 16, 17, 16, 17, 16, 17],   # a09: back-right
    [17, 18, 17, 18, 17, 18, 17, 18],   # a10: back-right 3/4
    [18, 19, 18, 19, 18, 19, 18, 19],   # a11: right profile
    [19, 20, 19, 20, 19, 20, 19, 20],   # a12: right-ish
    [20, 21, 20, 21, 20, 21, 20, 21],   # a13: front-right 3/4
    [21, 22, 24, 25, 21, 22, 24, 25],   # a14: front-right-ish
    [0, 2, 4, 6, 32, 35, 38, 43],       # a15: front
]


def _build_sprinting_bloke_frame(
    turn_rgba: np.ndarray,
    dance_rgba: np.ndarray,
    angle_idx: int,
    f_idx: int,
    n_frames: int,
    fx: Dict[str, np.ndarray],
) -> np.ndarray:
    """Composite a 16-angle x 8-frame fast-sprinting fat bloke using `turn_16` lower body
    with alternating high-knee leg-pump + `dance_48` raised waving arms/screaming upper
    + forward sprinting lean + mud splatters + swarming flies.
    """
    th, tw = turn_rgba.shape[:2]  # 460x320
    dh, dw = dance_rgba.shape[:2]  # 460x340

    t_clean = _clean_arm_hip_white_gaps(turn_rgba)
    # Find shorts-top waist row (~y=205) and shorts-hem row (~y=335) on turn_16
    # Detect orange saffron waistband: high R, medium G, low B
    trgb = t_clean[..., :3].astype(np.float32)
    ta = t_clean[..., 3] > 30
    orange = ta & (trgb[..., 0] > 165) & (trgb[..., 1] > 60) & (trgb[..., 1] < 145) & (trgb[..., 2] < 75)
    oy = np.nonzero(orange)[0]
    waist_y = int(np.percentile(oy, 10)) if len(oy) > 20 else 210
    hem_y = 338

    # Split lower body into: shorts/hips (waist_y .. hem_y) and left/right legs (hem_y .. th)
    # Center of mass x and half-width for shorts using symmetric torso midpoint right above waist
    ox = np.nonzero(orange)[1]
    t_mid_y0 = max(0, waist_y - 65)
    t_mid_y1 = max(t_mid_y0 + 10, waist_y)
    _, tm_x = np.nonzero(ta[t_mid_y0:t_mid_y1, :])
    if len(ox) > 20:
        shorts_hw = float(np.percentile(ox, 96) - np.percentile(ox, 4)) * 0.52
        cx_body = 0.5 * float(np.percentile(tm_x, 4) + np.percentile(tm_x, 96)) if len(tm_x) > 40 else 0.5 * float(np.percentile(ox, 4) + np.percentile(ox, 96))
    else:
        cx_body = tw * 0.5
        shorts_hw = 66.0

    # Align dance_48 upper body by matching its shorts (orange|green) waistband center AND width to turn_16!
    drgb = dance_rgba[..., :3].astype(np.float32)
    da = dance_rgba[..., 3] > 30
    d_orange = da & (drgb[..., 0] > 165) & (drgb[..., 1] > 60) & (drgb[..., 1] < 145) & (drgb[..., 2] < 75)
    d_green = da & (drgb[..., 1] > 80) & (drgb[..., 1] > drgb[..., 0] + 15) & (drgb[..., 1] > drgb[..., 2] + 20)
    d_shorts = d_orange | d_green
    doy = np.nonzero(d_shorts)[0]
    dox = np.nonzero(d_shorts)[1]
    d_shorts_hw = float(np.percentile(dox, 96) - np.percentile(dox, 4)) * 0.52 if len(dox) > 40 else shorts_hw
    d_scale = float(np.clip(shorts_hw / max(20.0, d_shorts_hw), 0.96, 1.14))
    if abs(d_scale - 1.0) > 0.015:
        dance_scaled = resize_premul(dance_rgba, (int(round(dw * d_scale)), int(round(dh * d_scale))))
    else:
        dance_scaled = dance_rgba
    dh, dw = dance_scaled.shape[:2]
    drgb = dance_scaled[..., :3].astype(np.float32)
    da = dance_scaled[..., 3] > 30
    d_orange = da & (drgb[..., 0] > 165) & (drgb[..., 1] > 60) & (drgb[..., 1] < 145) & (drgb[..., 2] < 75)
    d_green = da & (drgb[..., 1] > 80) & (drgb[..., 1] > drgb[..., 0] + 15) & (drgb[..., 1] > drgb[..., 2] + 20)
    d_shorts = d_orange | d_green
    doy = np.nonzero(d_shorts)[0]
    dox = np.nonzero(d_shorts)[1]
    d_waist_y = int(np.percentile(doy, 4)) if len(doy) > 40 else int(225 * d_scale)
    # Use upper-waist / mid-torso horizontal center so asymmetric shorts folds never skew alignment
    mid_y0 = max(0, d_waist_y - 70)
    mid_y1 = max(mid_y0 + 10, d_waist_y)
    _, mtx = np.nonzero(da[mid_y0:mid_y1, :])
    if len(mtx) > 40:
        d_cx = 0.5 * float(np.percentile(mtx, 4) + np.percentile(mtx, 96))
    elif len(dox) > 40:
        d_cx = 0.5 * float(np.percentile(dox, 4) + np.percentile(dox, 96))
    else:
        d_cx = dw * 0.5

    # Work on a spacious 380x480 intermediate canvas before downsampling to 160x180
    CW, CH = 380, 480
    phase = 2.0 * math.pi * (f_idx / float(n_frames))
    stride = math.sin(phase)
    stride_opp = math.sin(phase + math.pi)
    bounce_y = -abs(math.sin(phase)) * 22.0

    # Facing direction horizontal component for sprinting lean
    ang_rad = 2.0 * math.pi * angle_idx / 16.0
    # a04 (90 deg) faces left (-1), a12 (270 deg) faces right (+1)
    face_x = -math.sin(ang_rad)
    lean_deg = -11.5 * face_x - 3.5 * math.cos(phase)

    # 1. Lower legs (left & right split) + clean shorts core (strip turn_16 dangling arms!)
    yy_t, xx_t = np.mgrid[0:th, 0:tw]
    leg_mask_l = (yy_t >= hem_y - 12) & (xx_t < cx_body)
    leg_mask_r = (yy_t >= hem_y - 12) & (xx_t >= cx_body)

    def _extract_masked(src: np.ndarray, mask: np.ndarray) -> np.ndarray:
        out = src.copy()
        out[~mask] = 0
        return out

    leg_l = _extract_masked(t_clean, leg_mask_l)
    leg_r = _extract_masked(t_clean, leg_mask_r)
    # Keep shorts core strictly from waist_y down so upper torso from dance_48 blends smoothly over top edge
    shorts_core = _extract_masked(
        t_clean,
        (yy_t >= waist_y - 4)
        & (yy_t < hem_y + 6)
        & (np.abs(xx_t - cx_body) <= max(46.0, shorts_hw * 0.96)),
    )

    hip_y = float(hem_y - 6)
    leg_l_pad = np.zeros((CH, CW, 4), dtype=np.uint8)
    leg_r_pad = np.zeros((CH, CW, 4), dtype=np.uint8)
    shorts_pad = np.zeros((CH, CW, 4), dtype=np.uint8)
    off_x = int(round(CW * 0.5 - cx_body))
    off_y = 14
    leg_l_pad[off_y:off_y + th, off_x:off_x + tw] = leg_l
    leg_r_pad[off_y:off_y + th, off_x:off_x + tw] = leg_r
    shorts_pad[off_y:off_y + th, off_x:off_x + tw] = shorts_core

    hip_px = CW * 0.5
    hip_py = off_y + hip_y

    # Left & right legs pump up/down and kick forward/back out of phase
    l_kick_rot = stride * (26.0 * abs(face_x) + 12.0)
    r_kick_rot = stride_opp * (26.0 * abs(face_x) + 12.0)
    l_lift_y = -max(0.0, stride) * 32.0 + max(0.0, -stride) * 6.0
    r_lift_y = -max(0.0, stride_opp) * 32.0 + max(0.0, -stride_opp) * 6.0
    l_sy = 1.0 - 0.18 * max(0.0, stride)
    r_sy = 1.0 - 0.18 * max(0.0, stride_opp)

    leg_l_w = warp_rgba(leg_l_pad, angle_deg=l_kick_rot, sx=1.0, sy=l_sy, dx=stride * 12.0 * face_x, dy=l_lift_y, pivot=(hip_px - 22, hip_py), out_hw=(CH, CW))
    leg_r_w = warp_rgba(leg_r_pad, angle_deg=r_kick_rot, sx=1.0, sy=r_sy, dx=stride_opp * 12.0 * face_x, dy=r_lift_y, pivot=(hip_px + 22, hip_py), out_hw=(CH, CW))

    # 2. Upper torso + raised waving arms + screaming face from dance_48!
    # For back angles (5..11), stop upper torso right at d_waist_y + 2 so dance_48's solid-green back shorts never show above turn_16's tricolor shorts!
    dy_g, dx_g = np.mgrid[0:dh, 0:dw].astype(np.float32)
    if 5 <= angle_idx <= 11:
        upper_w = np.clip((float(d_waist_y + 2) - dy_g) / 14.0, 0.0, 1.0)
    else:
        upper_w = np.clip((float(d_waist_y + 18) - dy_g) / 24.0, 0.0, 1.0)
    upper = dance_scaled.copy()
    upper[..., 3] = np.clip(np.round(upper[..., 3].astype(np.float32) * upper_w), 0, 255).astype(np.uint8)
    upper[upper[..., 3] < 4] = 0

    upper_pad = np.zeros((CH, CW, 4), dtype=np.uint8)
    u_ox = int(round(CW * 0.5 - d_cx))
    u_oy = int(round(off_y + waist_y - d_waist_y))
    sx0 = max(0, -u_ox)
    sy0 = max(0, -u_oy)
    dx0 = max(0, u_ox)
    dy0 = max(0, u_oy)
    cw_p = min(dw - sx0, CW - dx0)
    ch_p = min(dh - sy0, CH - dy0)
    if cw_p > 0 and ch_p > 0:
        upper_pad[dy0:dy0 + ch_p, dx0:dx0 + cw_p] = upper[sy0:sy0 + ch_p, sx0:sx0 + cw_p]

    # Keep upper torso anchored cleanly at waist (no vertical detachment); back angles tuck cleanly behind shorts!
    upper_w = warp_rgba(
        upper_pad,
        angle_deg=0.0,
        sx=1.0 + 0.03 * math.sin(phase * 2.0),
        sy=1.0 - 0.02 * math.sin(phase * 2.0),
        dx=0.0,
        dy=0.0,
        pivot=(CW * 0.5, off_y + waist_y),
        out_hw=(CH, CW),
    )

    # Combine legs -> shorts -> upper waving torso (for back angles 5..11, shorts overlap cleanly over lower back)
    body = np.zeros((CH, CW, 4), dtype=np.uint8)
    body = alpha_over(body, leg_l_w, 0, 0)
    body = alpha_over(body, leg_r_w, 0, 0)
    if 5 <= angle_idx <= 11:
        body = alpha_over(body, upper_w, 0, 0)
        body = alpha_over(body, shorts_pad, 0, 0)
    else:
        body = alpha_over(body, shorts_pad, 0, 0)
        body = alpha_over(body, upper_w, 0, 0)

    # Apply sprinting forward lean + vertical running bounce!
    body = warp_rgba(
        body,
        angle_deg=lean_deg,
        sx=1.0,
        sy=1.0,
        dx=10.0 * face_x,
        dy=bounce_y,
        pivot=(CW * 0.5, CH * 0.55),
        out_hw=(CH, CW),
    )

    # Downsample to PROJ_WH (160x180)
    proj = resize_premul(body, PROJ_WH)

    # 3. Add mud splatters on belly/feet + kicking mud trail + 6 swarming flies
    mud_belly = resize_premul(fx[f"mud_glob_0{(angle_idx + f_idx) % 4}"], (22, 22))
    proj = alpha_over(proj, mud_belly, int(PROJ_WH[0] * 0.44), int(PROJ_WH[1] * 0.44), opacity=0.85)

    # Trailing mud splat & glob behind sprinting feet
    trail_x = PROJ_WH[0] * 0.5 - face_x * (28.0 + 10.0 * (f_idx % 2))
    trail_y = PROJ_WH[1] * 0.80 - 6.0 * (f_idx % 3)
    trail_glob = resize_premul(fx[f"mud_glob_0{f_idx % 4}"], (24, 24))
    proj = alpha_over(proj, trail_glob, trail_x - 12, trail_y - 12, opacity=0.88)

    # Swarming flies orbiting the sprinting fat bloke
    proj = render_fly_swarm(
        proj,
        centers=[(PROJ_WH[0] * 0.5, PROJ_WH[1] * 0.36), (PROJ_WH[0] * 0.5, PROJ_WH[1] * 0.65)],
        t_norm=f_idx / float(n_frames),
        n_flies=6,
        scale=0.68,
    )
    return proj


def render_projectile_sequence(
    assets: Dict[str, object],
) -> Tuple[List[List[np.ndarray]], List[str]]:
    """Render 16-angle x 8-frame sprinting fat bloke projectile sprites."""
    turn_16: List[np.ndarray] = assets["turn_16"]    # type: ignore[assignment]
    dance_48: List[np.ndarray] = assets["dance_48"]  # type: ignore[assignment]
    fx: Dict[str, np.ndarray] = assets["fx"]          # type: ignore[assignment]

    grid: List[List[np.ndarray]] = []
    files_flat: List[str] = []
    n_angles = len(turn_16)
    n_frames = 8
    for a in range(n_angles):
        row: List[np.ndarray] = []
        d_choices = DANCE_ANGLE_BANK[a]
        for f in range(n_frames):
            d_idx = d_choices[f % len(d_choices)]
            spr = _build_sprinting_bloke_frame(
                turn_16[a], dance_48[d_idx], a, f, n_frames, fx
            )
            fname = f"proj_a{a:02d}_f{f:02d}.png"
            _save_rgba(spr, os.path.join(OUT_DIR, fname))
            row.append(spr)
            files_flat.append(fname)
        grid.append(row)
    return grid, files_flat


def _build_3p_aimed_cannon(
    rig: Dict[str, np.ndarray],
    heads: Dict[str, np.ndarray],
    mode: str,
    f_idx: int,
    n_frames: int,
    plunger_sx: float,
) -> np.ndarray:
    """Build a front-three-quarter aimed Poop Cannon for the 3rd-person shooter."""
    gun = _render_glass_heads_chamber(rig, heads, mode, f_idx, n_frames)
    gun = alpha_over(gun, rig["body"], 0, 0)
    plunger_w = warp_rgba(
        rig["plunger"],
        angle_deg=0.0,
        sx=plunger_sx,
        sy=1.0 + (1.0 - plunger_sx) * 0.45,
        dx=0.0,
        dy=0.0,
        pivot=(278.0, 405.0),
        out_hw=(1024, 1024),
    )
    gun = alpha_over(gun, plunger_w, 0, 0)
    gun = alpha_over(gun, rig["glass_overlay"], 0, 0)
    psi_ang = 55.0 if mode == "idle" else (120.0 if f_idx < 8 else -100.0)
    gun = _draw_psi_needle(gun, psi_ang)

    # Crop tight around the weapon hardware (exclude lower first-person gauntlets!)
    crop = gun[210:645, 40:945].copy()
    # Smoothly fade out lower first-person gloves/forearms without creating a hard horizontal cut line
    cy_g, cx_g = np.mgrid[0:crop.shape[0], 0:crop.shape[1]].astype(np.float32)
    cut_y = np.where(cx_g < 520.0, 392.0, 378.0)
    keep_g = np.clip((cut_y - cy_g) / 24.0, 0.0, 1.0)
    crop[..., 3] = np.clip(np.round(crop[..., 3].astype(np.float32) * keep_g), 0, 255).astype(np.uint8)
    crop[crop[..., 3] < 4] = 0

    # Perspective-foreshorten so the big red plunger aims forward-left at the camera
    ch, cw = crop.shape[:2]
    src_pts = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]])
    dst_pts = np.float32(
        [
            [18, 36],
            [cw * 0.72, 8],
            [cw * 0.74, ch * 0.88],
            [0, ch * 1.04],
        ]
    )
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    pm = to_premul(crop)
    persp = cv2.warpPerspective(
        pm,
        M,
        (int(cw * 0.78), int(ch * 1.08)),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )
    return resize_premul(from_premul(persp), (210, 128))


def render_tp_sequence(
    rig: Dict[str, np.ndarray],
    assets: Dict[str, object],
    mode: str,
    n_frames: int,
) -> List[np.ndarray]:
    """Render 3rd-person enemy shooter holding the Poop Cannon aimed at the viewer (`320x320`)."""
    enemy_full: np.ndarray = assets["enemy_base"]  # type: ignore[assignment]
    heads: Dict[str, np.ndarray] = assets["heads"]  # type: ignore[assignment]
    fx: Dict[str, np.ndarray] = assets["fx"]        # type: ignore[assignment]

    # Scale enemy_base (420x440) to ~226x236 centered in 320x320
    enemy_rs = resize_premul(enemy_full, (226, 236))
    # Extract tight skin-palm+fingers masks so his hands wrap cleanly around the cannon without dark armor rings
    eh, ew = enemy_rs.shape[:2]
    yy_e, xx_e = np.mgrid[0:eh, 0:ew].astype(np.float32)
    er = enemy_rs[..., 0].astype(np.float32)
    eb = enemy_rs[..., 2].astype(np.float32)
    is_skin = (er - eb) > 16.0
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
            flag_amp = 1.05
            flag_phase = tau * 2.0 * t_norm
        elif mode == "fire":
            p = f_idx / float(max(1, n_frames - 1))
            kick = math.exp(-3.8 * p) if f_idx >= 2 else -0.25
            bob_y = 6.0 * kick
            sway_x = 4.0 * kick
            gun_dy = 8.0 * kick
            gun_rot = -8.0 * kick
            plunger_sx = 0.76 if f_idx < 2 else (1.0 + 0.20 * math.exp(-4.5 * p) * math.cos(p * math.pi * 3.0))
            flag_amp = 1.50
            flag_phase = tau * (1.0 + 2.2 * p)
        else:  # reload
            p = f_idx / float(max(1, n_frames - 1))
            lift = math.sin(math.pi * p)
            bob_y = 4.0 * lift
            sway_x = 3.0 * lift
            gun_dy = -8.0 * lift
            gun_rot = -12.0 * lift
            plunger_sx = 0.94
            flag_amp = 1.20
            flag_phase = tau * 2.0 * p

        canvas = np.zeros((TP_WH[1], TP_WH[0], 4), dtype=np.uint8)
        ex = (TP_WH[0] - ew) * 0.5 + sway_x
        ey = TP_WH[1] - eh - 6 + bob_y

        # 1. Two waving tricolor flags on brass poles flanking the shooter/cannon (unclipped inside 320x320!)
        pole_l0 = (ex + 62, ey + 96)
        pole_l1 = (ex + 44, ey - 42)
        pole_r0 = (ex + 168, ey + 92)
        pole_r1 = (ex + 182, ey - 38)
        canvas = _draw_brass_flagpole(canvas, pole_l0, pole_l1, thickness=3)
        canvas = _draw_brass_flagpole(canvas, pole_r0, pole_r1, thickness=3)

        fl_l = render_tricolor_flag(84, 52, phase=flag_phase, pole_left=False, amp=flag_amp)
        fl_r = render_tricolor_flag(84, 52, phase=flag_phase + 1.1, pole_left=True, amp=flag_amp)
        canvas = alpha_over(canvas, fl_l, pole_l1[0] - 78, pole_l1[1] - 4)
        canvas = alpha_over(canvas, fl_r, pole_r1[0] - 6, pole_r1[1] - 4)

        # 2. Enemy marine body
        canvas = alpha_over(canvas, enemy_rs, ex, ey)

        # 3. Aimed Poop Cannon held across torso right between his left & right hands!
        gun_3p = _build_3p_aimed_cannon(rig, heads, mode, f_idx, n_frames, plunger_sx)
        gun_3p = warp_rgba(
            gun_3p,
            angle_deg=gun_rot - 6.0,
            sx=1.0,
            sy=1.0,
            dx=0.0,
            dy=0.0,
            pivot=(gun_3p.shape[1] * 0.5, gun_3p.shape[0] * 0.5),
            out_hw=gun_3p.shape[:2],
        )
        gx = ex + 10 + sway_x * 0.5
        gy = ey + 28 + gun_dy
        canvas = alpha_over(canvas, gun_3p, gx, gy)

        # Overlay his armored hands gripping the cannon
        canvas = alpha_over(canvas, hands_fg, ex, ey)

        # 4. Fire blast straight toward the camera from the plunger muzzle!
        muzzle_tp = (gx + 24.0, gy + 54.0)
        if mode == "fire" and 2 <= f_idx <= 16:
            bf = (f_idx - 2) / 14.0
            m_puff = resize_premul(fx[f"mist_0{(f_idx % 3) * 2 + 1}"], (int(68 + 110 * bf), int(68 + 110 * bf)))
            canvas = alpha_over(
                canvas,
                m_puff,
                muzzle_tp[0] - m_puff.shape[1] * 0.5 - 12.0 * bf,
                muzzle_tp[1] - m_puff.shape[0] * 0.5 + 10.0 * bf,
                opacity=max(0.0, 1.0 - bf * 0.88),
            )
            if f_idx <= 10:
                sp = resize_premul(fx[f"splat_0{f_idx % 4}"], (int(48 + 78 * bf), int(48 + 78 * bf)))
                canvas = alpha_over(
                    canvas,
                    sp,
                    muzzle_tp[0] - sp.shape[1] * 0.5,
                    muzzle_tp[1] - sp.shape[0] * 0.5,
                    opacity=max(0.0, 1.0 - (f_idx - 2) / 9.0),
                )

        # 5. Buzzing flies orbiting the muzzle & shooter
        canvas = render_fly_swarm(
            canvas,
            centers=[muzzle_tp, (ex + ew * 0.5, ey + 55.0)],
            t_norm=(f_idx / float(max(1, n_frames))) if mode == "idle" else (f_idx / 24.0) % 1.0,
            n_flies=12,
            scale=0.80,
        )
        frames.append(canvas)
    return frames


def bake_all() -> Dict[str, object]:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("[concept1_cannon] Loading cached heads, fx, turn_16, dance_48, enemy_base...")
    assets = _load_assets()
    print("[concept1_cannon] Extracting layered cannon rig...")
    rig = _build_cannon_rig()

    print("[concept1_cannon] Rendering VM idle (60), fire (20), reload (18) at 420x360...")
    vm_idle = render_vm_sequence(rig, assets, "idle", 60)
    vm_fire = render_vm_sequence(rig, assets, "fire", 20)
    vm_reload = render_vm_sequence(rig, assets, "reload", 18)

    vm_idle_files = [f"vm_idle_{i:02d}.png" for i in range(len(vm_idle))]
    vm_fire_files = [f"vm_fire_{i:02d}.png" for i in range(len(vm_fire))]
    vm_reload_files = [f"vm_reload_{i:02d}.png" for i in range(len(vm_reload))]
    for fn, fr in zip(vm_idle_files, vm_idle):
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
    for fn, fr in zip(vm_fire_files, vm_fire):
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
    for fn, fr in zip(vm_reload_files, vm_reload):
        _save_rgba(fr, os.path.join(OUT_DIR, fn))

    print("[concept1_cannon] Rendering 16x8 sprinting fat bloke projectile...")
    proj_grid, _ = render_projectile_sequence(assets)
    proj_files = [[f"proj_a{a:02d}_f{f:02d}.png" for f in range(8)] for a in range(16)]

    print("[concept1_cannon] Rendering 3rd-person shooter idle (60), fire (20), reload (18)...")
    tp_idle = render_tp_sequence(rig, assets, "idle", 60)
    tp_fire = render_tp_sequence(rig, assets, "fire", 20)
    tp_reload = render_tp_sequence(rig, assets, "reload", 18)

    tp_idle_files = [f"tp_idle_{i:02d}.png" for i in range(len(tp_idle))]
    tp_fire_files = [f"tp_fire_{i:02d}.png" for i in range(len(tp_fire))]
    tp_reload_files = [f"tp_reload_{i:02d}.png" for i in range(len(tp_reload))]
    for fn, fr in zip(tp_idle_files, tp_idle):
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
    for fn, fr in zip(tp_fire_files, tp_fire):
        _save_rgba(fr, os.path.join(OUT_DIR, fn))
    for fn, fr in zip(tp_reload_files, tp_reload):
        _save_rgba(fr, os.path.join(OUT_DIR, fn))

    print("[concept1_cannon] Generating contact sheets & manifest.json...")
    _save_rgba(
        _make_contact_sheet(vm_idle[::3], 5, (210, 180), [f"idle_{i*3:02d}" for i in range(20)]),
        os.path.join(OUT_DIR, "sheet_vm_idle.png"),
    )
    _save_rgba(
        _make_contact_sheet(vm_fire, 5, (210, 180), [f"fire_{i:02d}" for i in range(20)]),
        os.path.join(OUT_DIR, "sheet_vm_fire.png"),
    )
    _save_rgba(
        _make_contact_sheet(vm_reload, 6, (210, 180), [f"rel_{i:02d}" for i in range(18)]),
        os.path.join(OUT_DIR, "sheet_vm_reload.png"),
    )
    flat_proj = [proj_grid[a][f] for a in range(0, 16, 2) for f in range(8)]
    proj_lbls = [f"a{a:02d}f{f}" for a in range(0, 16, 2) for f in range(8)]
    _save_rgba(
        _make_contact_sheet(flat_proj, 8, (120, 135), proj_lbls),
        os.path.join(OUT_DIR, "sheet_proj.png"),
    )
    tp_sample = tp_idle[::12] + tp_fire[::2] + tp_reload[::3]
    tp_lbls = (
        [f"ti_{i*12:02d}" for i in range(5)]
        + [f"tf_{i*2:02d}" for i in range(10)]
        + [f"tr_{i*3:02d}" for i in range(6)]
    )
    _save_rgba(
        _make_contact_sheet(tp_sample, 7, (160, 160), tp_lbls),
        os.path.join(OUT_DIR, "sheet_tp.png"),
    )

    manifest = {
        "id": "c1_cannon",
        "title": "THE DOOKIE BAZOOKA",
        "tagline": "Poop Plunger Cannon with 4 Arguing Heads, Tricolor Flags & 14 Flies",
        "fps": 60,
        "vm_size": list(VM_WH),
        "proj_size": list(PROJ_WH),
        "tp_size": list(TP_WH),
        "muzzle_norm": [round(96.0 + 85.0 * 0.71, 1) / 840.0, round(166.0 + 375.0 * 0.71, 1) / 720.0],
        "vm_idle": vm_idle_files,
        "vm_fire": vm_fire_files,
        "vm_reload": vm_reload_files,
        "proj": {
            "angles": 16,
            "frames_per_angle": 8,
            "files": proj_files,
        },
        "tp_idle": tp_idle_files,
        "tp_fire": tp_fire_files,
        "tp_reload": tp_reload_files,
    }
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)

    print(f"[concept1_cannon] Done! Baked to {OUT_DIR}")
    return manifest


if __name__ == "__main__":
    bake_all()
