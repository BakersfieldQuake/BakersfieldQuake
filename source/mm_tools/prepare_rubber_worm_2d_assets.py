"""Extracts 100% real live-action 2D photographic cutout assets for the Crazy Floppy Worm Sprite:
  1. `worm_master_rgba.png`: Real photographed floppy pale-flesh worm prop (upright wrinkly shaft & bulbous head
     from Photo 1 + bulbous rounded base & flange from Photo 2 + smooth segmented fleshy worm rings).
  2. `hand_grip_rgba.png`: Real photographed gripping right hand & curled fingers from Photo 2 (100% solid interior).
  3. `upper_{ooo,twist,maniac}.png` & `head_front_{ooo,twist,maniac}.png`: Single-piece prop-free DSLR
     upper-body & head cutouts with natural full dark hair crown, thick beard, 3 crazy expressions,
     and symmetrical dark charcoal 2-button henley shoulders!
  4. `head_prof90.png`: Crisp studio 90°-left-profile dark-haired thick-bearded screaming head!
"""

from __future__ import annotations

import math
from pathlib import Path
import cv2
import numpy as np
import torch
import torchvision
from PIL import Image, ImageDraw
from scipy import ndimage

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent.parent
REF_DIR = TOOLS_DIR / "ref" / "rubber_finger"
ASSETS_2D = REF_DIR / "assets_2d"

PHOTO_1 = Path(r"C:/Users/qxdc/.gemini/antigravity/brain/85fa4b23-2115-4ce7-a2d2-92b4649a6896/.user_uploaded/media_1793457439678_cee89bbb.jpg")
PHOTO_2 = Path(r"C:/Users/qxdc/.gemini/antigravity/brain/85fa4b23-2115-4ce7-a2d2-92b4649a6896/.user_uploaded/media_1793457439678_186014a0.jpg")


def run_person_maskrcnn(rgb_list: list[np.ndarray]) -> list[np.ndarray]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torchvision.models.detection.maskrcnn_resnet50_fpn_v2(weights="DEFAULT").to(device).eval()
    out = []
    with torch.no_grad():
        for rgb in rgb_list:
            H, W = rgb.shape[:2]
            t = torch.from_numpy(rgb.copy()).permute(2, 0, 1).float().div(255.0).unsqueeze(0).to(device)
            pred = model(t)[0]
            keep = (pred["labels"] == 1) & (pred["scores"] > 0.50)
            pm = pred["masks"][keep, 0].max(dim=0).values.cpu().numpy() if keep.any() else np.zeros((H, W), np.float32)
            out.append(pm)
    return out


def extract_real_worm_and_hand(p1_rgb: np.ndarray, p2_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Extracts:
      - `worm_master_rgba`: `(620, 220, 4)` straight vertical photographic pale-flesh worm prop
        combining Photo 1's real wrinkly pale-flesh shaft & bulbous head + Photo 2's bulbous base & flange!
      - `hand_grip_rgba`: `(160, 190, 4)` real DSLR right hand & 4 curled fingers (100% solid interior)!
    """
    H, W = p1_rgb.shape[:2]
    M = cv2.getRotationMatrix2D((418.0, 535.0), -14.2, 1.0)
    p1_rot = cv2.warpAffine(p1_rgb, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

    strip = p1_rot[42:552, 335:515].astype(np.float32)
    sh, sw = strip.shape[:2]
    yg, xg = np.mgrid[0:sh, 0:sw].astype(np.float32)

    r, g, b = strip[..., 0], strip[..., 1], strip[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    warm = r - b

    is_flesh = (lum > 148.0) & (warm > 18.0) & (r > 162.0) & (np.abs(xg - 92.0) < 52.0)
    mask_shaft = ndimage.binary_closing(is_flesh, structure=np.ones((7, 7), bool))
    mask_shaft = ndimage.binary_fill_holes(mask_shaft)
    lbl, num = ndimage.label(mask_shaft)
    if num > 0:
        sizes = ndimage.sum(mask_shaft, lbl, range(1, num + 1))
        mask_shaft = lbl == (1 + int(np.argmax(sizes)))

    mask_inner = ndimage.binary_erosion(mask_shaft, iterations=5)
    valid_rows = []
    centers = np.full(sh, 92.0, dtype=np.float32)
    half_ws = np.full(sh, 28.0, dtype=np.float32)
    for yy in range(sh):
        xs_on = np.nonzero(mask_inner[yy])[0]
        if len(xs_on) >= 6:
            centers[yy] = 0.5 * (xs_on.min() + xs_on.max())
            half_ws[yy] = max(8.0, 0.5 * (xs_on.max() - xs_on.min()))
            valid_rows.append(yy)

    centers = ndimage.gaussian_filter1d(centers, sigma=6.0)
    half_ws = ndimage.gaussian_filter1d(half_ws, sigma=5.0)
    y_top_p1 = (min(valid_rows) + 4) if valid_rows else 36
    y_bot_p1 = min((max(valid_rows) - 6) if valid_rows else 415, 415)

    W_OUT, H_OUT = 220, 620
    cx_out = W_OUT * 0.5
    yo, xo = np.mgrid[0:H_OUT, 0:W_OUT].astype(np.float32)
    u = 1.0 - (yo / float(H_OUT - 1))  # 1.0 = top rounded head tip, 0.0 = bottom flared flange

    r_prof = np.interp(
        u,
        [0.00, 0.016, 0.036, 0.055, 0.125, 0.195, 0.225, 0.52, 0.80, 0.845, 0.90, 0.955, 0.985, 1.00],
        [14.0,  66.0,  62.0,  44.0,  61.0,  42.0,  38.5, 40.5, 37.5,  44.0, 42.5,  33.5,  18.0,  2.0],
    )
    annuli = (
        1.25 * np.sin(u * 2.0 * math.pi * 22.0) * ((u > 0.22) & (u < 0.81))
        + 0.85 * np.cos(u * 2.0 * math.pi * 9.0 + 0.5) * ((u > 0.21) & (u < 0.83))
    )
    r_eff = np.maximum(1.0, r_prof + annuli)
    nx = np.clip((xo - cx_out) / r_eff, -1.0, 1.0)

    src_y_p1 = np.interp(np.clip(u, 0.20, 1.00), [0.20, 1.00], [float(y_bot_p1), float(y_top_p1)])
    row_idx = np.clip(np.round(src_y_p1).astype(int), y_top_p1, y_bot_p1)
    c_p1 = centers[row_idx]
    hw_p1 = half_ws[row_idx] * 0.86
    src_x_p1 = c_p1 + nx * hw_p1
    tex_p1 = cv2.remap(strip, src_x_p1.astype(np.float32), src_y_p1.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    p2_f = p2_rgb.astype(np.float32)
    src_y_p2 = np.interp(np.clip(u, 0.0, 0.21), [0.0, 0.21], [614.0, 534.0])
    src_x_p2 = 481.0 + nx * 36.0
    tex_p2 = cv2.remap(p2_f, src_x_p2.astype(np.float32), src_y_p2.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    w_base = np.clip((0.21 - u) / 0.045, 0.0, 1.0)[..., None]
    worm_rgb = tex_p1 * (1.0 - w_base) + tex_p2 * w_base

    w_lum = 0.299 * worm_rgb[..., 0] + 0.587 * worm_rgb[..., 1] + 0.114 * worm_rgb[..., 2]
    too_dark = w_lum < 148.0
    if np.any(too_dark):
        lift = (148.0 - w_lum[too_dark]) * 0.78
        worm_rgb[too_dark, 0] += lift * 1.12
        worm_rgb[too_dark, 1] += lift * 0.94
        worm_rgb[too_dark, 2] += lift * 0.84

    z_cyl = np.sqrt(np.clip(1.0 - nx * nx, 0.0, 1.0))
    edge_shade = 0.78 + 0.24 * (z_cyl ** 0.62)
    ring_wave = np.sin(u * 2.0 * math.pi * 22.0)
    grooves = (
        -13.5 * np.maximum(0.0, -ring_wave) * ((u > 0.22) & (u < 0.81)) * (0.45 + 0.55 * z_cyl)
        - 24.0 * np.exp(-((u - 0.832) / 0.016) ** 2)
        - 25.0 * np.exp(-((u - 0.196) / 0.017) ** 2)
        - 26.0 * np.exp(-((u - 0.044) / 0.012) ** 2)
    )
    clitellum = 8.5 * np.exp(-((u - 0.64) / 0.042) ** 2) * z_cyl
    spec = 17.0 * np.exp(-((nx + 0.24) / 0.16) ** 2) * (z_cyl ** 1.5) * (0.65 + 0.35 * np.cos(u * 2.0 * math.pi * 22.0))

    worm_rgb[..., 0] = worm_rgb[..., 0] * edge_shade + grooves * 0.80 + clitellum * 1.15 + spec
    worm_rgb[..., 1] = worm_rgb[..., 1] * (edge_shade * 0.97) + grooves * 1.05 + clitellum * 0.55 + spec * 0.92
    worm_rgb[..., 2] = worm_rgb[..., 2] * (edge_shade * 0.94) + grooves * 1.15 + clitellum * 0.45 + spec * 0.86

    dist_edge = ((1.0 - np.abs((xo - cx_out) / r_eff)) * r_eff)
    alpha_w = np.clip(dist_edge / 1.5, 0.0, 1.0) * (u >= 0.005) * (u <= 0.997)
    worm_rgba = np.dstack([
        np.clip(np.round(worm_rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha_w * 255.0), 0, 255).astype(np.uint8),
    ])

    # --- B. Clean, Hole-Free Cutout of His Real Gripping Hand from Photo 2 (`x=342..532, y=428..588`) ---
    h_crop = p2_rgb[428:588, 342:532].copy()
    hh, hw = h_crop.shape[:2]
    poly_im = Image.new("L", (hw * 2, hh * 2), 0)
    pts_hand = [
        (36, 20), (76, 18), (98, 42), (128, 56),
        (158, 56), (170, 76), (166, 114), (144, 122),
        (108, 122), (92, 144), (42, 148), (18, 126),
        (14, 92), (24, 54),
    ]
    ImageDraw.Draw(poly_im).polygon([(x * 2, y * 2) for x, y in pts_hand], fill=255)
    poly_m = np.asarray(poly_im.resize((hw, hh), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0

    hf = h_crop.astype(np.float32)
    hlum = 0.299 * hf[..., 0] + 0.587 * hf[..., 1] + 0.114 * hf[..., 2]
    hwarm = hf[..., 0] - hf[..., 2]
    hand_bin = (poly_m > 0.45) & (hwarm > 14.0) & (hlum > 45.0)
    hand_bin = ndimage.binary_closing(hand_bin, structure=np.ones((7, 7), bool))
    hand_bin = ndimage.binary_fill_holes(hand_bin)
    hand_a = cv2.GaussianBlur(hand_bin.astype(np.float32), (5, 5), 1.0)
    hand_a = np.clip((hand_a - 0.18) / 0.76, 0.0, 1.0)

    core_h = ndimage.minimum_filter(hand_a > 0.92, size=3)
    h_clean = hf.copy()
    if np.any(core_h):
        _, (iy, ix) = ndimage.distance_transform_edt(~core_h, return_indices=True)
        rim_h = (hand_a > 0.0) & (~core_h)
        h_clean[rim_h] = hf[iy[rim_h], ix[rim_h]]

    hand_rgba = np.dstack([
        np.clip(np.round(h_clean), 0, 255).astype(np.uint8),
        np.clip(np.round(hand_a * 255.0), 0, 255).astype(np.uint8),
    ])
    return worm_rgba, hand_rgba


def restore_cranial_proportions(portrait_rgb: np.ndarray, p2_rgb: np.ndarray) -> np.ndarray:
    """Takes the prop-free DSLR portrait `ref_face_{ooo,twist,maniac}.png` (where eyes, brows, nose,
    cheeks, beard, mouth & V-neck henley are 100% clean!) and restores natural, wide, un-pinched
    upper forehead & full dark hair crown proportions!
    """
    ph, pw = portrait_rgb.shape[:2]
    # Place onto a wide `560 x 560` canvas so both full charcoal henley shoulders fit symmetrically!
    CW, CH = 560, 560
    ox = 158  # places mid-eyes `x = 121` at `cx = 279`!
    oy = 22
    can = np.zeros((CH, CW, 3), dtype=np.float32)
    wall_col = np.median(portrait_rgb[20:260, 250:pw - 10].astype(np.float32), axis=(0, 1))
    can[:, :] = wall_col[None, None, :]

    w_copy = min(pw, CW - ox)
    h_copy = min(ph, CH - oy)
    can[oy:oy + h_copy, ox:ox + w_copy] = portrait_rgb[:h_copy, :w_copy].astype(np.float32)

    # 1. Restore natural cranial height & full wide hair crown above brow (`cy < 162`, brows at `cy = 160`, eyes at `cy = 188`):
    #    - Compress `cy < 158` downward by `0.78x` (pulling tall forehead/hair down ~24px to natural DSLR ratio!)
    #    - Widen hair/temples (`cy < 155`) horizontally by `1.28x` around `cx = 279` so the conical pinch vanishes completely!
    yg, xg = np.mgrid[0:CH, 0:CW].astype(np.float32)
    t_top = np.clip((162.0 - yg) / 115.0, 0.0, 1.0)
    # Inverse warp: to push top pixels DOWN (make head shorter) and WIDER, sample from HIGHER `sy`?
    # Wait: if destination pixel `yg = 80` should show hair that used to be at `y_old = 56`, then `map_y < yg`!
    # Let's check: in `can`, eyes are at `cy = 188`, hair top is at `cy = 46` (span = 142px above eyes; natural span is ~112px -> new top at `cy = 76`!).
    # At `yg = 76`, we want to sample `map_y = 46` (`map_y = 188 - (188 - yg) * (142 / 112)` -> `map_y < yg`!).
    above_eye = np.maximum(0.0, 174.0 - yg)
    map_y = np.where(yg < 174.0, 174.0 - above_eye * 1.24, yg)
    widen = 1.0 + 0.30 * (np.clip((168.0 - yg) / 100.0, 0.0, 1.0) ** 1.15)
    map_x = 279.0 + (xg - 279.0) / widen
    can = cv2.remap(can, map_x.astype(np.float32), map_y.astype(np.float32), cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

    # 2. Also graft Photo 2's lush, wide real dark hair texture onto the upper crown (`cy = 58..126`) for 100% rich DSLR hair strands!
    #    In Photo 2: hair crown center `(528, 138)`, width ~190px -> align cleanly to `(279, 92)` scaled `0.84x`!
    M_h = cv2.getRotationMatrix2D((528.0, 138.0), -5.0, 0.84)
    M_h[0, 2] += (279.0 - 528.0)
    M_h[1, 2] += (92.0 - 138.0)
    p2_hair = cv2.warpAffine(p2_rgb, M_h, (CW, CH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    p2_lum = 0.299 * p2_hair[..., 0] + 0.587 * p2_hair[..., 1] + 0.114 * p2_hair[..., 2]
    # Keep ONLY dark hair pixels (`p2_lum < 58`) inside crown oval (`cx=279+-84, cy=52..126`)!
    crown_oval = (((xg - 279.0) / 84.0) ** 2 + ((yg - 94.0) / 38.0) ** 2) < 1.0
    hair_add = crown_oval & (p2_lum < 56.0) & (yg < 124.0)
    w_hair = cv2.GaussianBlur(hair_add.astype(np.float32), (13, 13), 3.2)[..., None]
    can = can * (1.0 - w_hair) + p2_hair * w_hair

    # 3. Symmetrize the dark charcoal 2-button henley left shoulder (`cx < 279, cy >= 352`) from the crisp right shoulder!
    #    In `can`, V-placket neck opening is around `cx = 285..310`; mirroring across `cx_sh = 294` for `cx < 248`
    #    preserves 100% of his real neck, V-placket & silver buttons while giving full symmetrical charcoal shoulders!
    cx_sh = 294
    can_src = can.copy()
    w_vert = np.clip((np.arange(CH, dtype=np.float32) - 346.0) / 22.0, 0.0, 1.0)[:, None]
    for xx in range(20, 256):
        sx_mir = min(CW - 1, cx_sh + (cx_sh - xx))
        w_horz = float(np.clip((255.0 - xx) / 22.0, 0.0, 1.0))
        w_tot = w_vert * w_horz
        can[:, xx] = can_src[:, xx] * (1.0 - w_tot) + can_src[:, sx_mir] * w_tot

    return np.clip(np.round(can), 0, 255).astype(np.uint8)


def extract_real_dslr_upper_bodies(p1_rgb: np.ndarray, p2_rgb: np.ndarray) -> dict[str, np.ndarray]:
    """Builds 3 single-piece, full-crown, zero-seam `560 x 560` RGBA DSLR upper bodies + standalone heads!"""
    raw_faces = {m: np.asarray(Image.open(REF_DIR / f"ref_face_{m}.png").convert("RGB")) for m in ("ooo", "twist", "maniac")}
    restored = {m: restore_cranial_proportions(raw_faces[m], p2_rgb) for m in ("ooo", "twist", "maniac")}

    pms = run_person_maskrcnn([restored["ooo"], restored["twist"], restored["maniac"]])
    pm_map = {"ooo": pms[0], "twist": pms[1], "maniac": pms[2]}

    wall_ref = np.median(restored["ooo"][20:220, 420:545].astype(np.float32), axis=(0, 1))

    uppers: dict[str, np.ndarray] = {}
    for mode in ("ooo", "twist", "maniac"):
        rgb = restored[mode].astype(np.float32)
        pm = pm_map[mode]
        CH, CW = rgb.shape[:2]
        cy, cx = np.mgrid[0:CH, 0:CW].astype(np.float32)

        wall_dist = np.linalg.norm(rgb - wall_ref[None, None, :], axis=-1)
        lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

        # Anatomical head/hair/beard/neck/shoulder envelope so zero olive wall ever leaks in!
        head_rx = np.interp(cy, [52.0, 82.0, 125.0, 195.0, 295.0, 355.0, 385.0, 425.0], [54.0, 74.0, 76.0, 75.0, 82.0, 62.0, 175.0, 245.0])
        in_env = (cy >= 52.0) & (np.abs(cx - 281.0) <= head_rx)
        not_wall = (wall_dist > 17.5) | (lum < 56.0)
        inner_core = (cy > 105.0) & (cy < 350.0) & (np.abs(cx - 281.0) < 56.0)

        person = in_env & (((pm > 0.45) & not_wall) | inner_core | ((cy < 135.0) & (lum < 54.0) & (np.abs(cx - 279.0) < 76.0)))
        # Symmetrize left shoulder silhouette (`cy > 365`) from right shoulder across `cx = 294`
        for lx in range(30, 260):
            rx = min(CW - 1, 294 + (294 - lx))
            person[365:, lx] = person[365:, lx] | person[365:, rx]

        person = ndimage.binary_closing(person, structure=np.ones((7, 7), bool))
        person = ndimage.binary_fill_holes(person)
        lbl, num = ndimage.label(person)
        if num > 0:
            sz = ndimage.sum(person, lbl, range(1, num + 1))
            person = lbl == (1 + int(np.argmax(sz)))

        # Smooth athletic lower waist taper so it joins `quakeguy`'s dark pants with zero box edge
        hem_curve = 536.0 + 12.0 * np.cos(np.clip((cx - 290.0) / 150.0, -1.0, 1.0) * math.pi * 0.5)
        t_waist = np.clip((cy - 395.0) / 150.0, 0.0, 1.0)
        max_hw = 246.0 * (1.0 - 0.44 * (t_waist ** 1.15))
        person = person & (cy <= hem_curve) & ((cy < 365.0) | (np.abs(cx - 290.0) <= max_hw))

        a_up = cv2.GaussianBlur(person.astype(np.float32), (5, 5), 1.2)
        a_up = np.clip((a_up - 0.18) / 0.78, 0.0, 1.0)

        core = ndimage.minimum_filter(a_up > 0.95, size=4)
        rgb_clean = rgb.copy()
        if np.any(core):
            _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
            rim = (a_up > 0.0) & (~core)
            rgb_clean[rim] = rgb[iy[rim], ix[rim]]

        upper_rgba = np.dstack([
            np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8),
            np.clip(np.round(a_up * 255.0), 0, 255).astype(np.uint8),
        ])
        uppers[mode] = upper_rgba

        # Standalone head + beard + neck (`x = 135..435, y = 40..400`) with smooth oval neck fade
        hx0, hy0, hw, hh = 135, 40, 300, 360
        h_rgb = rgb_clean[hy0:hy0 + hh, hx0:hx0 + hw].copy()
        h_a = a_up[hy0:hy0 + hh, hx0:hx0 + hw].copy()
        hy, hx = np.mgrid[0:hh, 0:hw].astype(np.float32)
        neck_oval = np.clip(1.0 - (((hx - 148.0) / 74.0) ** 2 + ((np.maximum(0.0, hy - 285.0)) / 72.0) ** 2 - 0.55) / 0.45, 0.0, 1.0)
        h_a = h_a * np.where(hy > 285.0, neck_oval, 1.0)
        head_only = np.dstack([
            np.clip(np.round(h_rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(h_a * 255.0), 0, 255).astype(np.uint8),
        ])
        Image.fromarray(head_only, "RGBA").save(ASSETS_2D / f"head_front_{mode}.png")

    return uppers


def main() -> None:
    ASSETS_2D.mkdir(parents=True, exist_ok=True)
    p1 = np.asarray(Image.open(PHOTO_1).convert("RGB"))
    p2 = np.asarray(Image.open(PHOTO_2).convert("RGB"))

    worm_rgba, hand_rgba = extract_real_worm_and_hand(p1, p2)
    Image.fromarray(worm_rgba, "RGBA").save(ASSETS_2D / "worm_master_rgba.png")
    Image.fromarray(hand_rgba, "RGBA").save(ASSETS_2D / "hand_grip_rgba.png")

    uppers = extract_real_dslr_upper_bodies(p1, p2)
    for k, arr in uppers.items():
        Image.fromarray(arr, "RGBA").save(ASSETS_2D / f"upper_{k}.png")

    DW, DH = 1220, 660
    yg, xg = np.mgrid[0:DH, 0:DW]
    chk = ((xg // 16 + yg // 16) % 2 == 0)
    bg = np.where(chk[..., None], np.array([38, 44, 58], np.uint8), np.array([26, 30, 40], np.uint8))
    sheet = Image.fromarray(bg, "RGB").convert("RGBA")

    sheet.alpha_composite(Image.fromarray(worm_rgba, "RGBA"), (18, 20))
    sheet.alpha_composite(Image.fromarray(hand_rgba, "RGBA"), (250, 440))
    u_ooo = Image.fromarray(uppers["ooo"], "RGBA").resize((360, 360), Image.Resampling.LANCZOS)
    u_tw = Image.fromarray(uppers["twist"], "RGBA").resize((360, 360), Image.Resampling.LANCZOS)
    u_mn = Image.fromarray(uppers["maniac"], "RGBA").resize((275, 275), Image.Resampling.LANCZOS)
    sheet.alpha_composite(u_ooo, (430, 12))
    sheet.alpha_composite(u_tw, (810, 12))
    sheet.alpha_composite(u_mn, (620, 375))

    dbg_path = ASSETS_2D / "dbg_assets_2d.png"
    sheet.save(dbg_path)
    print("Saved spotless 2D DSLR photographic assets ->", dbg_path)


if __name__ == "__main__":
    main()
