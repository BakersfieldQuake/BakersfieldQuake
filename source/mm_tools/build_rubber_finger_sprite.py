"""100% 2D Digitized Live-Action Photographic Sprite Builder for the Crazy Floppy Worm Maniac!

Combines:
  1. Real live-action studio-photographed 360° 8-angle × 8-frame running human body (`quakeguy_sprite`)
     with shirt logo seamlessly inpainted into dark charcoal-heather 2-button henley knit.
  2. Real DSLR cutouts across all 8 angles (`0°..315°`):
     - `0°` (`d=0`) & `Forehead Bonk`: Our actor's real DSLR `upper_{ooo,twist,maniac}.png` seamlessly
       blended onto the dark charcoal torso (zero waist gap, forearm tucked cleanly under his henley sleeve!).
     - `45° / 315°` (`d=1, 7`): Our actor's real DSLR `head_front_{ooo,twist,maniac}.png` backed by real
       DSLR dark hair crown volume.
     - `90° / 270°` (`d=2, 6`): Real `1024x1024` DSLR `head_090.jpg` chroma-keyed and customized with our
       actor's thick real DSLR dark beard texture, open gasping/screaming mouth, and icy-blue wide shock eye!
     - `135° / 180° / 225°` (`d=3, 4, 5`): Real `1024x1024` DSLR `head_135.jpg` (with real dark cheek beard)
       and `head_180.jpg`!
  3. 2D supersampled piecewise-spline ribbon warper (`render_bent_worm_2d`) that bends the real
     photographed pale-peach segmented floppy worm (`worm_master_rgba.png`) into wild S-curves,
     wags, and across-the-forehead flops, clutched by his real photographed gripping hand (`hand_grip_rgba.png`).
"""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent.parent
ASSETS_2D = TOOLS_DIR / "ref" / "rubber_finger" / "assets_2d"
WHEEL_HEADS_DIR = TOOLS_DIR / "ref" / "wheelman_heads"
QG_DIR = ROOT_DIR / "quakeguy_sprite"
OUT_DIR = ROOT_DIR / "rubber_finger_sprite"
SPR_PREVIEW_DIR = OUT_DIR / "spr32"
PROGS_SPR32_PATH = ROOT_DIR / "progs" / "fr_finger.spr32"

sys.path.insert(0, str(TOOLS_DIR))
from rubber_finger_fx import (
    build_3d_sweat_specs,
    composite_3d_chaos_fx,
    draw_kinetic_star,
    draw_rubber_whoosh_arc,
    key_magenta_studio_safe,
    make_sweat_drop_rgba,
    resize_rgba_premul,
    warp_affine_premul,
)
from rubber_finger_viewer_html import render_rubber_finger_viewer_html

# Final stage dimensions (8:9 aspect ratio -> 128x144 in-game SPR32)
STAGE_W = 560
STAGE_H = 630
GROUND_Y = 590

SPR_W = 128
SPR_H = 144
SPR_OX = -(SPR_W // 2)
SPR_OY = round(GROUND_Y * SPR_H / STAGE_H)  # 135 px (feet-anchored!)
RUN_6_INDICES = [0, 1, 2, 4, 5, 6]

QG_SCALE = 0.88
QG_CX = 239.0
QG_GROUND_Y = 594.0


def load_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.uint8)


def qg_to_stage_xy(x_qg: float, y_qg: float) -> tuple[float, float]:
    sx = STAGE_W * 0.5 + (x_qg - QG_CX) * QG_SCALE
    sy = GROUND_Y + (y_qg - QG_GROUND_Y) * QG_SCALE
    return sx, sy


def make_ground_shadow_layer() -> Image.Image:
    """Soft studio contact shadow oval under the character's boots (matching `mrdiy_sprite`)."""
    im = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = STAGE_W // 2, GROUND_Y - 3
    d.ellipse((cx - 72, cy - 13, cx + 72, cy + 13), fill=(8, 10, 14, 88))
    d.ellipse((cx - 44, cy - 8, cx + 44, cy + 8), fill=(5, 7, 10, 115))
    return im.filter(ImageFilter.GaussianBlur(6.5))


def make_seamless_beard_tile(patch_rgb: np.ndarray, out_h: int = 1024, out_w: int = 1024) -> np.ndarray:
    p = cv2.resize(patch_rgb, (256, 256), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    top = np.concatenate([p, p[:, ::-1, :]], axis=1)
    quad = np.concatenate([top, top[::-1, :, :]], axis=0)
    if (out_h, out_w) != (512, 512):
        quad = cv2.resize(quad, (out_w, out_h), interpolation=cv2.INTER_LINEAR)
    return quad


def build_bearded_dslr_side_heads(beard_patch: np.ndarray) -> dict[str, np.ndarray]:
    """Builds 100% real DSLR `90°`, `135°`, and `180°` bearded crazy head cutouts from `wheelman_heads/`
    customized with our actor's real DSLR dark beard texture, bushy brow, and icy-blue shock iris!
    """
    bt = make_seamless_beard_tile(beard_patch, 1024, 1024)
    out_heads: dict[str, np.ndarray] = {}

    for tag in ("090", "135", "180"):
        raw = key_magenta_studio_safe(Image.open(WHEEL_HEADS_DIR / f"head_{tag}.jpg"))
        f = raw.astype(np.float32)
        H, W = f.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
        rgb = f[..., :3]
        a = f[..., 3] / 255.0

        # Deepen hair slightly toward rich espresso-black
        lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
        warm = rgb[..., 0] - rgb[..., 2]
        hair_m = (a > 0.4) & (lum < 88.0) & (warm < 26.0)
        rgb = np.where(hair_m[..., None], rgb * 0.72, rgb)

        if tag == "090":
            # 1. Tint dark iris at `(x=368, y=444)` to our actor's bright icy-blue shock eye!
            r_iris = np.hypot((xg - 366.0) / 22.0, (yg - 442.0) / 24.0)
            r_pupil = np.hypot((xg - 362.0) / 9.5, (yg - 442.0) / 11.0)
            iris_ring = (r_iris < 1.0) & (r_pupil >= 1.0) & (lum < 95.0) & (a > 0.8)
            w_ir = cv2.GaussianBlur(iris_ring.astype(np.float32), (9, 9), 2.0)[..., None]
            icy_rgb = np.dstack([lum * 0.55 + 48.0, lum * 0.85 + 108.0, lum * 1.05 + 162.0])
            rgb = rgb * (1.0 - 0.82 * w_ir) + np.clip(icy_rgb, 0.0, 245.0) * (0.82 * w_ir)

            # 2. Graft real DSLR thick dark beard + mustache + sideburn onto jaw/chin/upper-lip,
            #    preserving ONLY his front open mouth & teeth (`x=168..242, y=696..758`)!
            poly_b = Image.new("L", (W, H), 0)
            db = ImageDraw.Draw(poly_b)
            db.polygon(
                [
                    (168, 608), (315, 615), (465, 595), (528, 455), (612, 462),
                    (606, 668), (562, 832), (445, 938), (242, 954), (176, 875),
                    (178, 764), (244, 756), (246, 696), (168, 686),
                ],
                fill=255,
            )
            bm = cv2.GaussianBlur(np.asarray(poly_b, dtype=np.float32) / 255.0, (51, 51), 14.0)
            jaw_shade = np.clip(lum / 160.0, 0.45, 1.12)[..., None]
            beard_col = np.clip(bt * jaw_shade * 0.72, 8.0, 88.0)
            w_b = np.clip(bm * 1.15, 0.0, 1.0)[..., None] * (a[..., None] > 0.12)
            rgb = rgb * (1.0 - 0.94 * w_b) + beard_col * (0.94 * w_b)

            # Lush full chin beard silhouette (`x=205..445, y=855..948`) with soft feathered edge!
            chin_tuft = np.clip(1.0 - (((xg - 310.0) / 118.0) ** 2 + ((yg - 882.0) / 64.0) ** 2), 0.0, 1.0)
            tuft_a = cv2.GaussianBlur(np.clip(chin_tuft * 1.8, 0.0, 1.0).astype(np.float32), (19, 19), 5.0)
            add_mask = (tuft_a > a) & (yg > 835.0)
            rgb = np.where(add_mask[..., None], bt * 0.62, rgb)
            a = np.maximum(a, tuft_a * (yg > 835.0))

        elif tag == "135":
            # Add thick dark DSLR beard along visible lower left cheek/jaw (`x=185..410, y=585..885`)
            poly_b = Image.new("L", (W, H), 0)
            ImageDraw.Draw(poly_b).polygon(
                [(185, 595), (345, 580), (398, 710), (372, 868), (225, 865), (185, 735)],
                fill=255,
            )
            bm = cv2.GaussianBlur(np.asarray(poly_b, dtype=np.float32) / 255.0, (35, 35), 9.0)
            jaw_shade = np.clip(lum / 150.0, 0.50, 1.15)[..., None]
            w_b = (bm * (a > 0.15))[..., None]
            rgb = rgb * (1.0 - 0.88 * w_b) + np.clip(bt * jaw_shade * 0.85, 10.0, 98.0) * (0.88 * w_b)

        # Smooth lower neck alpha taper (`y > 865`) so it blends seamlessly onto `quakeguy`'s neck/collar!
        neck_fade = 1.0 - np.clip((yg - 885.0) / 78.0, 0.0, 1.0)
        a = a * neck_fade

        # Downsample cleanly to `(220 x 220)` working asset for fast, crisp compositing
        full_u8 = np.dstack([
            np.clip(np.round(rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(a * 255.0), 0, 255).astype(np.uint8),
        ])
        out_heads[tag] = resize_rgba_premul(full_u8, 220, 220)

    return out_heads


# ---------------------------------------------------------------------------
# 1. 2D Piecewise-Spline Supersampled Ribbon Warper for the Real Floppy Worm
# ---------------------------------------------------------------------------

def render_bent_worm_2d(
    worm_rgba: np.ndarray,
    hand_rgba: np.ndarray | None,
    grip_xy: tuple[float, float],
    worm_len: float = 252.0,
    worm_width_scale: float = 0.44,
    base_ang_deg: float = 0.0,
    bend_mid_deg: float = 0.0,
    bend_tip_deg: float = 0.0,
    u_grip: float = 0.25,
    hand_mirror: bool = False,
    hand_scale: float = 0.35,
    worm_shade: float = 1.0,
) -> np.ndarray:
    """Bends `worm_master_rgba.png` smoothly along a continuous C2 curved 2D spine anchored at `grip_xy`
    using a `2x` supersampled 48-station triangle-strip ID buffer + single premultiplied `cv2.remap`.
    """
    hw_src, ww_src = worm_rgba.shape[:2]
    n_seg = 48
    us = np.linspace(0.0, 1.0, n_seg + 1, dtype=np.float32)

    s_above = np.clip((us - u_grip) / (1.0 - u_grip), 0.0, 1.0)
    ang_deg = (
        base_ang_deg
        + bend_mid_deg * (np.sin(s_above * math.pi * 0.5) ** 1.25)
        + bend_tip_deg * (s_above ** 2.15)
    )
    thetas = np.radians(ang_deg)

    ds = worm_len / float(n_seg)
    tx = np.sin(thetas)
    ty = -np.cos(thetas)
    nx = np.cos(thetas)
    ny = np.sin(thetas)

    idx_grip = int(round(u_grip * n_seg))
    px = np.zeros(n_seg + 1, dtype=np.float32)
    py = np.zeros(n_seg + 1, dtype=np.float32)
    px[idx_grip], py[idx_grip] = grip_xy
    for k in range(idx_grip + 1, n_seg + 1):
        px[k] = px[k - 1] + 0.5 * (tx[k - 1] + tx[k]) * ds
        py[k] = py[k - 1] + 0.5 * (ty[k - 1] + ty[k]) * ds
    for k in range(idx_grip - 1, -1, -1):
        px[k] = px[k + 1] - 0.5 * (tx[k + 1] + tx[k]) * ds
        py[k] = py[k + 1] - 0.5 * (ty[k + 1] + ty[k]) * ds

    half_w = (ww_src * 0.5) * worm_width_scale
    lx = px - nx * half_w
    ly = py - ny * half_w
    rx = px + nx * half_w
    ry = py + ny * half_w

    SS = 2
    W2, H2 = STAGE_W * SS, STAGE_H * SS
    tri_id = np.full((H2, W2), -1, dtype=np.int32)
    m_inv = np.zeros((2 * n_seg, 2, 3), dtype=np.float32)

    tid = 0
    for k in range(n_seg):
        sy0 = (1.0 - us[k]) * (hw_src - 1)
        sy1 = (1.0 - us[k + 1]) * (hw_src - 1)

        d_l0 = (lx[k] * SS, ly[k] * SS)
        d_r0 = (rx[k] * SS, ry[k] * SS)
        d_l1 = (lx[k + 1] * SS, ly[k + 1] * SS)
        d_r1 = (rx[k + 1] * SS, ry[k + 1] * SS)

        s_l0 = (0.0, sy0)
        s_r0 = (float(ww_src - 1), sy0)
        s_l1 = (0.0, sy1)
        s_r1 = (float(ww_src - 1), sy1)

        for dst_tri, src_tri in (
            ([d_l0, d_r0, d_l1], [s_l0, s_r0, s_l1]),
            ([d_r0, d_r1, d_l1], [s_r0, s_r1, s_l1]),
        ):
            dst_arr = np.array(dst_tri, dtype=np.float32)
            area2 = abs(
                (dst_arr[1, 0] - dst_arr[0, 0]) * (dst_arr[2, 1] - dst_arr[0, 1])
                - (dst_arr[2, 0] - dst_arr[0, 0]) * (dst_arr[1, 1] - dst_arr[0, 1])
            )
            if area2 > 0.5:
                src_arr = np.array(src_tri, dtype=np.float32)
                m_inv[tid] = cv2.getAffineTransform(dst_arr, src_arr)
                pts_i = np.round(dst_arr).astype(np.int32)
                cv2.fillConvexPoly(tri_id, pts_i, tid)
            tid += 1

    out_stage = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.uint8)
    ys_v, xs_v = np.nonzero(tri_id >= 0)
    if len(ys_v) > 0:
        y0_bb, y1_bb = max(0, int(ys_v.min()) - 2), min(H2, int(ys_v.max()) + 3)
        x0_bb, x1_bb = max(0, int(xs_v.min()) - 2), min(W2, int(xs_v.max()) + 3)
        y0_bb = (y0_bb // SS) * SS
        x0_bb = (x0_bb // SS) * SS
        y1_bb = min(H2, ((y1_bb + SS - 1) // SS) * SS)
        x1_bb = min(W2, ((x1_bb + SS - 1) // SS) * SS)

        sub_tid = tri_id[y0_bb:y1_bb, x0_bb:x1_bb]
        gy2, gx2 = np.mgrid[y0_bb:y1_bb, x0_bb:x1_bb].astype(np.float32)
        valid = sub_tid >= 0
        safe_tid = np.maximum(sub_tid, 0)
        mi = m_inv[safe_tid]

        map_x = np.where(valid, mi[..., 0, 0] * gx2 + mi[..., 0, 1] * gy2 + mi[..., 0, 2], -5.0).astype(np.float32)
        map_y = np.where(valid, mi[..., 1, 0] * gx2 + mi[..., 1, 1] * gy2 + mi[..., 1, 2], -5.0).astype(np.float32)

        wf = worm_rgba.astype(np.float32)
        if abs(worm_shade - 1.0) > 1e-3:
            wf[..., :3] = np.clip(wf[..., :3] * worm_shade, 0.0, 255.0)
        wa = wf[..., 3:4] / 255.0
        w_pm = np.concatenate([wf[..., :3] * wa, wf[..., 3:4]], axis=-1)

        remapped_pm = cv2.remap(w_pm, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        bh_out = (y1_bb - y0_bb) // SS
        bw_out = (x1_bb - x0_bb) // SS
        ds_pm = cv2.resize(remapped_pm, (bw_out, bh_out), interpolation=cv2.INTER_AREA)
        da = ds_pm[..., 3:4] / 255.0
        d_rgb = np.where(da > 1e-3, ds_pm[..., :3] / np.maximum(da, 1e-3), 0.0)
        d_u8 = np.dstack([
            np.clip(np.round(d_rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(ds_pm[..., 3]), 0, 255).astype(np.uint8),
        ])
        out_stage[y0_bb // SS:y1_bb // SS, x0_bb // SS:x1_bb // SS] = d_u8

    im_out = Image.fromarray(out_stage, "RGBA")

    if hand_rgba is not None:
        h_src = hand_rgba[:, ::-1, :].copy() if hand_mirror else hand_rgba.copy()
        if abs(worm_shade - 1.0) > 1e-3:
            hf = h_src.astype(np.float32)
            hf[..., :3] = np.clip(hf[..., :3] * worm_shade, 0.0, 255.0)
            h_src = hf.astype(np.uint8)
        hh, hw = h_src.shape[:2]
        nhw = max(4, int(round(hw * hand_scale)))
        nhh = max(4, int(round(hh * hand_scale)))
        h_scaled = resize_rgba_premul(h_src, nhw, nhh)

        pad = max(nhw, nhh)
        h_pad = np.zeros((nhh + pad * 2, nhw + pad * 2, 4), dtype=np.uint8)
        h_pad[pad:pad + nhh, pad:pad + nhw] = h_scaled
        piv_x = pad + (nhw - 102.0 * hand_scale if hand_mirror else 102.0 * hand_scale)
        piv_y = pad + 86.0 * hand_scale
        h_rot = warp_affine_premul(h_pad, (piv_x, piv_y), angle_deg=base_ang_deg)

        ox = int(round(grip_xy[0] - piv_x))
        oy = int(round(grip_xy[1] - piv_y))
        im_h = Image.fromarray(h_rot, "RGBA")
        dx0, dy0 = max(0, ox), max(0, oy)
        sx0, sy0 = max(0, -ox), max(0, -oy)
        sw = min(im_h.width - sx0, STAGE_W - dx0)
        sh = min(im_h.height - sy0, STAGE_H - dy0)
        if sw > 0 and sh > 0:
            im_out.alpha_composite(im_h, dest=(dx0, dy0), source=(sx0, sy0, sx0 + sw, sy0 + sh))

    return np.asarray(im_out, dtype=np.uint8)


# ---------------------------------------------------------------------------
# 2. Live-Action Quakeguy Shirt De-Logo, Charcoal Henley & Forearm Helpers
# ---------------------------------------------------------------------------

def clean_and_style_quakeguy_frame(qg_rgba: np.ndarray, dir_idx: int, henley_patch: np.ndarray) -> np.ndarray:
    """Removes the white chest print from `quakeguy_d{d}_f{f}.png` and styles the shirt into dark charcoal-heather knit."""
    arr = qg_rgba.astype(np.float32).copy()
    H, W = arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    warm = r - b

    in_shirt_zone = (yg >= 126.0) & (yg <= 326.0) & (a > 120.0)
    is_logo = in_shirt_zone & (lum > 60.0) & (np.abs(warm) < 17.0)
    if np.any(is_logo):
        logo_dil = ndimage.binary_dilation(is_logo, iterations=4) & in_shirt_zone & (warm < 18.0)
        dark_knit = in_shirt_zone & (~logo_dil) & (lum < 58.0) & (np.abs(warm) < 16.0)
        if np.any(dark_knit):
            w_k = dark_knit.astype(np.float32)
            num_rgb = cv2.GaussianBlur(arr[..., :3] * w_k[..., None], (31, 31), 9.0)
            den = cv2.GaussianBlur(w_k, (31, 31), 9.0)[..., None]
            fill_rgb = np.where(den > 1e-4, num_rgb / np.maximum(den, 1e-4), np.array([24.0, 26.0, 30.0]))
            blend = cv2.GaussianBlur(logo_dil.astype(np.float32), (7, 7), 1.6)[..., None]
            arr[..., :3] = arr[..., :3] * (1.0 - blend) + fill_rgb * blend

    lum2 = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    warm2 = arr[..., 0] - arr[..., 2]
    shirt_px = (yg >= 112.0) & (yg <= 325.0) & (a > 140.0) & (lum2 < 68.0) & (warm2 < 15.0)
    if np.any(shirt_px):
        ht = cv2.resize(henley_patch, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
        ht_delta = ht - ht.mean(axis=(0, 1), keepdims=True)
        w_s = cv2.GaussianBlur(shirt_px.astype(np.float32), (5, 5), 1.0)[..., None]
        charcoal = arr[..., :3] * 0.88 + np.array([15.0, 18.0, 22.0])[None, None, :] + ht_delta * 0.48
        arr[..., :3] = arr[..., :3] * (1.0 - w_s) + np.clip(charcoal, 12.0, 118.0) * w_s

    return np.clip(np.round(arr), 0, 255).astype(np.uint8)


def measure_qg_landmarks(qg_rgba: np.ndarray, dir_idx: int) -> dict[str, float]:
    a = qg_rgba[..., 3] > 128
    ys, xs = np.nonzero(a)
    y_top = float(ys.min())
    hy, hx = np.nonzero(a[int(y_top):int(y_top) + 78, :])
    head_cx = float(hx.mean()) if len(hx) else 239.0

    y_lo, y_hi = 148, 242
    sub = qg_rgba[y_lo:y_hi, :].astype(np.float32)
    skin = (sub[..., 3] > 128) & ((sub[..., 0] - sub[..., 2]) > 22.0) & (sub[..., 0] > 95.0)
    sy, sx = np.nonzero(skin)
    hand_x, hand_y = head_cx, 208.0
    has_ext_hand = False
    if len(sx) > 24:
        if dir_idx in (1, 2, 3):
            q = float(np.percentile(sx, 10))
            if q < head_cx - 42.0:
                sel = sx <= q + 12.0
                hand_x = float(sx[sel].mean())
                hand_y = float(y_lo + sy[sel].mean())
                has_ext_hand = True
        elif dir_idx in (5, 6, 7):
            q = float(np.percentile(sx, 90))
            if q > head_cx + 42.0:
                sel = sx >= q - 12.0
                hand_x = float(sx[sel].mean())
                hand_y = float(y_lo + sy[sel].mean())
                has_ext_hand = True

    return {
        "y_top": y_top,
        "head_cx": head_cx,
        "hand_x": hand_x,
        "hand_y": hand_y,
        "has_ext_hand": float(has_ext_hand),
    }


def draw_photographic_forearm_bridge(
    canvas: Image.Image,
    p_shoulder: tuple[float, float],
    p_hand: tuple[float, float],
    arm_tex_rgb: np.ndarray,
    width_arm: float = 22.0,
) -> None:
    """Draws a smooth round-capped muscular bare forearm from `p_shoulder` to `p_hand`
    (composited UNDER the henley sleeve so zero square cap ever protrudes!)."""
    dx = p_hand[0] - p_shoulder[0]
    dy = p_hand[1] - p_shoulder[1]
    dist = math.hypot(dx, dy)
    if dist < 6.0:
        return

    mx = 0.5 * (p_shoulder[0] + p_hand[0]) - (dy / dist) * 6.0
    my = 0.5 * (p_shoulder[1] + p_hand[1]) + abs(dx) * 0.18 + 9.0

    SS = 2
    over = Image.new("RGBA", (STAGE_W * SS, STAGE_H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)

    mean_skin = tuple(int(round(x)) for x in np.median(arm_tex_rgb.reshape(-1, 3), axis=0))
    dark_skin = (max(0, mean_skin[0] - 30), max(0, mean_skin[1] - 26), max(0, mean_skin[2] - 22), 255)
    mid_skin = (mean_skin[0], mean_skin[1], mean_skin[2], 255)
    hi_skin = (min(255, mean_skin[0] + 18), min(255, mean_skin[1] + 15), min(255, mean_skin[2] + 12), 255)

    pts = []
    for k in range(17):
        t = k / 16.0
        bx = (1 - t) ** 2 * p_shoulder[0] + 2 * (1 - t) * t * mx + t ** 2 * p_hand[0]
        by = (1 - t) ** 2 * p_shoulder[1] + 2 * (1 - t) * t * my + t ** 2 * p_hand[1]
        pts.append((bx * SS, by * SS))

    r_out = width_arm * 0.5 * SS
    for px, py in pts:
        d.ellipse((px - r_out - 2, py - r_out - 2, px + r_out + 2, py + r_out + 2), fill=dark_skin)
    for px, py in pts:
        d.ellipse((px - r_out + 1, py - r_out + 1, px + r_out - 1, py + r_out - 1), fill=mid_skin)
    for px, py in pts[5:]:
        d.ellipse((px - r_out * 0.4, py - r_out * 0.55, px + r_out * 0.4, py + r_out * 0.15), fill=hi_skin)

    canvas.alpha_composite(over.resize((STAGE_W, STAGE_H), Image.Resampling.LANCZOS))


def stage_quakeguy_body(qg_rgba: np.ndarray, erase_head_above_y: float | None = None) -> np.ndarray:
    """Places `(480x640)` `quakeguy` onto `(STAGE_W=560, STAGE_H=630)` with ground locked to `GROUND_Y=590`."""
    src = qg_rgba.copy()
    if erase_head_above_y is not None:
        keep_b = np.clip((np.arange(src.shape[0], dtype=np.float32) - erase_head_above_y) / 9.0, 0.0, 1.0)[:, None]
        src[..., 3] = np.round(src[..., 3].astype(np.float32) * keep_b).astype(np.uint8)

    h0, w0 = src.shape[:2]
    nw = int(round(w0 * QG_SCALE))
    nh = int(round(h0 * QG_SCALE))
    scaled = resize_rgba_premul(src, nw, nh)

    ox = int(round(STAGE_W * 0.5 - QG_CX * QG_SCALE))
    oy = int(round(GROUND_Y - QG_GROUND_Y * QG_SCALE))

    canvas = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
    im_s = Image.fromarray(scaled, "RGBA")
    dx0, dy0 = max(0, ox), max(0, oy)
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sw = min(nw - sx0, STAGE_W - dx0)
    sh = min(nh - sy0, STAGE_H - dy0)
    if sw > 0 and sh > 0:
        canvas.alpha_composite(im_s, dest=(dx0, dy0), source=(sx0, sy0, sx0 + sw, sy0 + sh))
    return np.array(canvas, dtype=np.uint8)


def feather_upper_torso_for_front(upper_rgba: np.ndarray) -> np.ndarray:
    """Matches charcoal shirt tone & feathers bottom waist hem of `upper_*.png` (`560x560`)
    so it blends with ZERO seam onto `quakeguy_d0`'s opaque dark charcoal shirt torso!"""
    out = upper_rgba.astype(np.float32).copy()
    H, W = out.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    # Tone DSLR henley fabric (`yg > 345`, cool charcoal `R - B < 12`) slightly deeper to match Quakeguy's dark charcoal torso!
    is_henley = (yg > 342.0) & ((out[..., 0] - out[..., 2]) < 12.0) & (out[..., 3] > 20.0)
    w_tone = cv2.GaussianBlur(is_henley.astype(np.float32), (15, 15), 4.0)[..., None] * np.clip((yg - 342.0) / 45.0, 0.0, 1.0)[..., None]
    out[..., :3] = out[..., :3] * (1.0 - 0.30 * w_tone)

    sh_env = np.clip((196.0 - np.abs(xg - 286.0)) / 26.0, 0.0, 1.0)
    w_sh = np.where(yg > 345.0, sh_env, 1.0)
    w_hem = 1.0 - np.clip((yg - 438.0) / 88.0, 0.0, 1.0)
    out[..., 3] = out[..., 3] * w_sh * w_hem
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# 3. Full 8-Angle × 8-Frame 2D Digitized Sprite Synthesizer + Forehead Bonk
# ---------------------------------------------------------------------------

def build_all_2d_frames() -> tuple[list[np.ndarray], list[list[np.ndarray]], list[np.ndarray]]:
    worm_rgba = load_rgba(ASSETS_2D / "worm_master_rgba.png")
    hand_rgba = load_rgba(ASSETS_2D / "hand_grip_rgba.png")
    uppers_raw = {m: load_rgba(ASSETS_2D / f"upper_{m}.png") for m in ("ooo", "twist", "maniac")}
    uppers = {m: feather_upper_torso_for_front(u) for m, u in uppers_raw.items()}
    heads_front = {m: load_rgba(ASSETS_2D / f"head_front_{m}.png") for m in ("ooo", "twist", "maniac")}

    henley_patch = uppers_raw["ooo"][390:500, 320:450, :3].copy()
    beard_patch = uppers_raw["ooo"][278:338, 218:264, :3].copy()
    arm_skin_patch = hand_rgba[40:120, 45:125, :3].copy()
    side_heads = build_bearded_dslr_side_heads(beard_patch)
    shadow_im = make_ground_shadow_layer()

    expr_cycle = ["ooo", "maniac", "maniac", "ooo", "ooo", "twist", "maniac", "twist"]

    run_raw: list[list[np.ndarray]] = [[] for _ in range(8)]
    idle_raw: list[np.ndarray] = []

    yg_s, xg_s = np.mgrid[0:STAGE_H, 0:STAGE_W].astype(np.float32)

    for d in range(8):
        for f in range(8):
            qg_orig = load_rgba(QG_DIR / f"quakeguy_d{d}_f{f}.png")
            lm = measure_qg_landmarks(qg_orig, d)
            qg_clean = clean_and_style_quakeguy_frame(qg_orig, d, henley_patch)

            phase = 2.0 * math.pi * f / 8.0
            expr = expr_cycle[f]
            head_stage_x, head_stage_y = qg_to_stage_xy(lm["head_cx"], lm["y_top"])

            if d == 0:
                # --- 0° FRONT: Opaque Charcoal Torso & Animated Legs + Seamless DSLR Head/Henley + Clear Face! ---
                # Erase ONLY Quakeguy's small head (`y_qg < y_top + 84`), keeping his entire dark shirt torso 100% OPAQUE!
                staged_body = stage_quakeguy_body(qg_clean, erase_head_above_y=lm["y_top"] + 82.0)
                # Erase ONLY Quakeguy's lower hanging right forearm (`xg_s < 235, 195 < yg_s < 345`) since his right arm is raised holding the worm!
                right_hang_arm = (xg_s < 236.0) & (yg_s > 190.0) & (yg_s < 412.0)
                w_erase_r = 1.0 - cv2.GaussianBlur(right_hang_arm.astype(np.float32), (11, 11), 2.8)
                staged_body[..., 3] = np.round(staged_body[..., 3].astype(np.float32) * w_erase_r).astype(np.uint8)

                canvas = shadow_im.copy()
                canvas.alpha_composite(Image.fromarray(staged_body, "RGBA"))

                sc_u = 0.375
                uw = int(round(560 * sc_u))
                uh = int(round(560 * sc_u))
                up_s = resize_rgba_premul(uppers[expr], uw, uh)
                tilt_deg = 3.8 * math.sin(phase)
                up_s = warp_affine_premul(up_s, (uw * 0.5, uh * 0.72), angle_deg=tilt_deg)

                ox_u = int(round(head_stage_x - 284.0 * sc_u))
                oy_u = int(round((head_stage_y - 6.0) - 52.0 * sc_u))

                # Gripping right hand positioned cleanly to viewer's left (`gx ~ 214..232`)
                # Draw bare forearm BEFORE `up_s` so the charcoal henley sleeve naturally overlaps the upper arm!
                gx = head_stage_x - 62.0 + 12.0 * math.sin(phase)
                gy = oy_u + uh * 0.78 + 5.0 * math.cos(2.0 * phase)
                sh_r = (head_stage_x - 46.0, oy_u + uh * 0.64)
                draw_photographic_forearm_bridge(canvas, sh_r, (gx, gy), arm_skin_patch, width_arm=23.0)

                # Composite feathered DSLR head + 2-button charcoal henley OVER the upper arm & opaque lower shirt!
                canvas.alpha_composite(Image.fromarray(up_s, "RGBA"), (ox_u, oy_u))

                # Whip giant floppy worm wildly on viewer's left (`-44° .. -8°`) so BOTH bugging blue eyes stay 100% visible!
                base_ang = -26.0 + 18.0 * math.sin(phase)
                bend_mid = 14.0 * math.sin(phase - 0.65)
                bend_tip = -32.0 * math.cos(phase)
                worm_layer = render_bent_worm_2d(
                    worm_rgba, hand_rgba, (gx, gy),
                    worm_len=252.0, worm_width_scale=0.44,
                    base_ang_deg=base_ang, bend_mid_deg=bend_mid, bend_tip_deg=bend_tip,
                    hand_mirror=False, hand_scale=0.35,
                )
                canvas.alpha_composite(Image.fromarray(worm_layer, "RGBA"))
                run_raw[d].append(np.asarray(canvas, dtype=np.uint8))

            elif d in (1, 7):
                # --- 45° / 315° FRONT-3/4: De-logoed Quakeguy Body + Real DSLR 3/4 Head + Forward Whipping Worm! ---
                is_left = (d == 1)
                sgn = -1.0 if is_left else 1.0
                staged_body = stage_quakeguy_body(qg_clean, erase_head_above_y=lm["y_top"] + 78.0)

                canvas = shadow_im.copy()
                if not lm["has_ext_hand"] > 0.5:
                    gx = head_stage_x + sgn * 66.0
                    gy = head_stage_y + 162.0 + 7.0 * math.sin(phase)
                    draw_photographic_forearm_bridge(canvas, (head_stage_x + sgn * 16.0, head_stage_y + 124.0), (gx, gy), arm_skin_patch, width_arm=21.0)
                else:
                    gx, gy = qg_to_stage_xy(lm["hand_x"], lm["hand_y"])

                canvas.alpha_composite(Image.fromarray(staged_body, "RGBA"))

                # Back cranium real DSLR dark hair from `side_heads["135"]` + front DSLR 3/4 crazy face!
                back_hd = side_heads["135"] if is_left else side_heads["135"][:, ::-1, :].copy()
                bh_s = resize_rgba_premul(back_hd, 108, 108)
                canvas.alpha_composite(
                    Image.fromarray(bh_s, "RGBA"),
                    (int(round(head_stage_x - sgn * 8.0 - 54)), int(round(head_stage_y - 12.0))),
                )

                sc_hx, sc_hy = 0.325, 0.365
                hw = int(round(300 * sc_hx))
                hh = int(round(360 * sc_hy))
                hd_s = resize_rgba_premul(heads_front[expr], hw, hh)
                hd_s = warp_affine_premul(hd_s, (hw * 0.5, hh * 0.78), angle_deg=3.2 * math.sin(phase))
                ox_h = int(round(head_stage_x + sgn * 8.0 - hw * 0.5))
                oy_h = int(round(head_stage_y - 10.0))
                canvas.alpha_composite(Image.fromarray(hd_s, "RGBA"), (ox_h, oy_h))

                # Keep worm whipping forward (`-46°..-10°` on d=1; `+10°..+46°` on d=7) clear of his crazy 3/4 face!
                base_ang = sgn * (28.0 + 18.0 * math.sin(phase))
                bend_mid = 14.0 * math.sin(phase - 0.6)
                bend_tip = -30.0 * math.cos(phase)
                worm_layer = render_bent_worm_2d(
                    worm_rgba, hand_rgba, (gx, gy),
                    worm_len=246.0, worm_width_scale=0.43,
                    base_ang_deg=base_ang, bend_mid_deg=bend_mid, bend_tip_deg=bend_tip,
                    hand_mirror=not is_left, hand_scale=0.33,
                )
                canvas.alpha_composite(Image.fromarray(worm_layer, "RGBA"))
                run_raw[d].append(np.asarray(canvas, dtype=np.uint8))

            elif d in (2, 6):
                # --- 90° LEFT / 270° RIGHT PROFILE: Real 1024x1024 DSLR Bearded Screaming Profile Head + Extended Arm! ---
                is_left = (d == 2)
                sgn = -1.0 if is_left else 1.0
                staged_body = stage_quakeguy_body(qg_clean, erase_head_above_y=lm["y_top"] + 78.0)

                canvas = shadow_im.copy()
                if lm["has_ext_hand"] > 0.5:
                    gx, gy = qg_to_stage_xy(lm["hand_x"], lm["hand_y"])
                else:
                    gx = head_stage_x + sgn * 72.0
                    gy = head_stage_y + 162.0
                    draw_photographic_forearm_bridge(canvas, (head_stage_x, head_stage_y + 124.0), (gx, gy), arm_skin_patch, width_arm=21.0)

                canvas.alpha_composite(Image.fromarray(staged_body, "RGBA"))

                prof_src = side_heads["090"] if is_left else side_heads["090"][:, ::-1, :].copy()
                ph_s = resize_rgba_premul(prof_src, 118, 118)
                ph_s = warp_affine_premul(ph_s, (59.0, 95.0), angle_deg=3.5 * math.sin(phase))
                ox_p = int(round(head_stage_x + sgn * 4.0 - 59.0))
                oy_p = int(round(head_stage_y - 16.0))
                canvas.alpha_composite(Image.fromarray(ph_s, "RGBA"), (ox_p, oy_p))

                # Angle worm cleanly forward (`-48°..-12°` on d=2, `+12°..+48°` on d=6) so profile face is 100% clear!
                base_ang = sgn * (30.0 + 18.0 * math.sin(phase))
                bend_mid = 15.0 * math.sin(phase - 0.65)
                bend_tip = -34.0 * math.cos(phase)
                worm_layer = render_bent_worm_2d(
                    worm_rgba, hand_rgba, (gx, gy),
                    worm_len=250.0, worm_width_scale=0.43,
                    base_ang_deg=base_ang, bend_mid_deg=bend_mid, bend_tip_deg=bend_tip,
                    hand_mirror=not is_left, hand_scale=0.33,
                )
                canvas.alpha_composite(Image.fromarray(worm_layer, "RGBA"))
                run_raw[d].append(np.asarray(canvas, dtype=np.uint8))

            else:
                # --- 135° / 180° / 225° REAR VIEWS (`d = 3, 4, 5`): Real DSLR Rear Heads + Z-Layered Worm Behind! ---
                staged_body = stage_quakeguy_body(qg_clean, erase_head_above_y=lm["y_top"] + 78.0)

                if d == 4:
                    rear_hd = resize_rgba_premul(side_heads["180"], 114, 114)
                    ox_r = int(round(head_stage_x - 57.0))
                    oy_r = int(round(head_stage_y - 14.0))
                    gx = STAGE_W * 0.5 - 30.0 * math.sin(phase)
                    gy = head_stage_y + 156.0
                    base_ang = -36.0 * math.sin(phase)
                    bend_mid = -14.0 * math.sin(phase - 0.6)
                    bend_tip = 32.0 * math.cos(phase)
                    show_hand = None
                    h_mir = False
                else:
                    is_left = (d == 3)
                    sgn = -1.0 if is_left else 1.0
                    r_src = side_heads["135"] if is_left else side_heads["135"][:, ::-1, :].copy()
                    rear_hd = resize_rgba_premul(r_src, 116, 116)
                    ox_r = int(round(head_stage_x - 58.0))
                    oy_r = int(round(head_stage_y - 15.0))
                    if lm["has_ext_hand"] > 0.5:
                        gx, gy = qg_to_stage_xy(lm["hand_x"], lm["hand_y"])
                    else:
                        gx = head_stage_x + sgn * 66.0
                        gy = head_stage_y + 162.0
                    base_ang = sgn * (28.0 + 18.0 * math.sin(phase))
                    bend_mid = 14.0 * math.sin(phase - 0.6)
                    bend_tip = -30.0 * math.cos(phase)
                    show_hand = hand_rgba
                    h_mir = not is_left

                worm_layer = render_bent_worm_2d(
                    worm_rgba, show_hand, (gx, gy),
                    worm_len=262.0, worm_width_scale=0.44,
                    base_ang_deg=base_ang, bend_mid_deg=bend_mid, bend_tip_deg=bend_tip,
                    hand_mirror=h_mir, hand_scale=0.32, worm_shade=0.93,
                )
                canvas = shadow_im.copy()
                canvas.alpha_composite(Image.fromarray(worm_layer, "RGBA"))
                canvas.alpha_composite(Image.fromarray(staged_body, "RGBA"))
                canvas.alpha_composite(Image.fromarray(rear_hd, "RGBA"), (ox_r, oy_r))
                run_raw[d].append(np.asarray(canvas, dtype=np.uint8))

        idle_raw.append(run_raw[d][0].copy())

    # --- 8-Frame Signature "FOREHEAD BONK!" Comedy Sequence (Photo 1 -> Whip -> Photo 2 Forehead Slap!) ---
    bonk_raw: list[np.ndarray] = []
    qg_stand = clean_and_style_quakeguy_frame(load_rgba(QG_DIR / "quakeguy_d0_f0.png"), 0, henley_patch)
    lm0 = measure_qg_landmarks(qg_stand, 0)
    hx0, hy0 = qg_to_stage_xy(lm0["head_cx"], lm0["y_top"])
    staged_legs = stage_quakeguy_body(qg_stand, erase_head_above_y=lm0["y_top"] + 82.0)
    right_hang_arm = (xg_s < 236.0) & (yg_s > 190.0) & (yg_s < 412.0)
    w_erase_r = 1.0 - cv2.GaussianBlur(right_hang_arm.astype(np.float32), (11, 11), 2.8)
    staged_legs[..., 3] = np.round(staged_legs[..., 3].astype(np.float32) * w_erase_r).astype(np.uint8)

    # Raised grip (`gy = oy_u + uh * 0.65`) so on frames 5 & 6 the bent worm slaps his UPPER FOREHEAD (`y ~ 115..148`)
    # leaving BOTH his bugging right eye AND sideways-twisted beard mouth 100% visible — IDENTICAL to Photo 2!!
    bonk_keys = [
        # f=0: Photo 1! Upright proud pale-flesh worm beside wide bug-eyed "OOO" face!
        ("ooo",     0.0,  0.0, -52.0,   0.0,   +8.0,   +2.0,   +2.0),
        # f=1: Fast windup left!
        ("maniac", +3.0, -2.0, -62.0,  -4.0,  -26.0,   -8.0,  +22.0),
        # f=2: Extreme left whip!
        ("maniac", +5.0, -4.0, -68.0,  -6.0,  -44.0,  -18.0,  +28.0),
        # f=3: Yanking fist back inward — big rubbery S-lag!
        ("maniac", +1.5, -1.0, -54.0,  -8.0,  -14.0,  -22.0,  -18.0),
        # f=4: Snapping upward toward forehead!
        ("ooo",    -2.0, +1.0, -48.0, -14.0,   +2.0,  +18.0,  +18.0),
        # f=5: *SMACK / BONK!* PHOTO 2 POSE! Worm curves across upper forehead while right eye & twisted mouth shine!
        ("twist",  -4.5, +5.0, -46.0, -18.0,   +2.0,  +38.0,  +42.0),
        # f=6: Peak squish & rubbery quiver across upper brow!
        ("twist",  -5.5, +7.0, -45.0, -17.0,   +4.0,  +42.0,  +44.0),
        # f=7: Boing rebound back toward Photo 1!
        ("ooo",    -1.5, +2.0, -50.0,  -6.0,   +6.0,  +12.0,  -16.0),
    ]

    for f, (b_expr, b_tilt, b_dy, gx_off, gy_off, b_ang, b_mid, b_tip) in enumerate(bonk_keys):
        canvas = shadow_im.copy()
        legs_f = warp_affine_premul(staged_legs, (STAGE_W * 0.5, GROUND_Y), sy=1.0 - b_dy * 0.002)
        canvas.alpha_composite(Image.fromarray(legs_f, "RGBA"))

        sc_u = 0.38
        uw = int(round(560 * sc_u))
        uh = int(round(560 * sc_u))
        up_s = resize_rgba_premul(uppers[b_expr], uw, uh)
        up_s = warp_affine_premul(up_s, (uw * 0.5, uh * 0.76), angle_deg=b_tilt)

        ox_u = int(round(hx0 - 284.0 * sc_u))
        oy_u = int(round((hy0 - 8.0 + b_dy) - 52.0 * sc_u))

        gx = hx0 + gx_off
        gy = oy_u + uh * 0.74 + gy_off
        sh_r = (hx0 - 46.0, oy_u + uh * 0.64)
        draw_photographic_forearm_bridge(canvas, sh_r, (gx, gy), arm_skin_patch, width_arm=23.0)
        canvas.alpha_composite(Image.fromarray(up_s, "RGBA"), (ox_u, oy_u))

        worm_layer = render_bent_worm_2d(
            worm_rgba, hand_rgba, (gx, gy),
            worm_len=242.0, worm_width_scale=0.44,
            base_ang_deg=b_ang, bend_mid_deg=b_mid, bend_tip_deg=b_tip,
            hand_mirror=False, hand_scale=0.35,
        )
        canvas.alpha_composite(Image.fromarray(worm_layer, "RGBA"))
        bonk_raw.append(np.asarray(canvas, dtype=np.uint8))

    return idle_raw, run_raw, bonk_raw


# ---------------------------------------------------------------------------
# 4. FX Polish, Sheet, Turntable GIF, Quake .SPR32 & Self-Contained HTML
# ---------------------------------------------------------------------------

def draw_forehead_bonk_fx(rgba: np.ndarray, f: int) -> np.ndarray:
    im = Image.fromarray(rgba, "RGBA")
    W, H = im.size
    back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    front = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    if f in (1, 2):
        draw_rubber_whoosh_arc(back, W * 0.40, H * 0.30, 128.0, 102.0, 220.0, 305.0, max_alpha=145, max_width=12.0)
        if f == 2:
            draw_kinetic_star(front, W * 0.17, H * 0.22, radius=22, angle_deg=16.0)
    elif f in (3, 4):
        draw_rubber_whoosh_arc(back, W * 0.45, H * 0.27, 118.0, 96.0, 195.0, 290.0, max_alpha=155, max_width=12.5)
    elif f in (5, 6):
        bx, by = W * 0.51, H * 0.16
        S = 2
        ring = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(ring)
        rad = (34 if f == 5 else 44) * S
        for deg in (-145, -115, -85, -52, -22, +12):
            ar = math.radians(deg)
            r0 = rad * 0.45
            r1 = rad * (1.16 if (deg % 2 == 0) else 0.96)
            p0 = (bx * S + math.cos(ar) * r0, by * S + math.sin(ar) * r0)
            p1 = (bx * S + math.cos(ar) * r1, by * S + math.sin(ar) * r1)
            d.line([p0, p1], fill=(255, 232, 95, 240 if f == 5 else 190), width=7)
        front = Image.alpha_composite(front, ring.resize((W, H), Image.Resampling.LANCZOS))
        draw_kinetic_star(front, bx + (48 if f == 5 else 56), by - 14, radius=24 if f == 5 else 19, angle_deg=22.0)
        draw_kinetic_star(front, bx - 48, by - 18, radius=18 if f == 5 else 23, angle_deg=-18.0, warm=False)
    elif f == 7:
        draw_rubber_whoosh_arc(back, W * 0.48, H * 0.25, 96.0, 82.0, 315.0, 235.0, max_alpha=125, max_width=10.0)

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(back)
    out.alpha_composite(im)
    out.alpha_composite(front)
    return np.asarray(out, dtype=np.uint8)


def boost_digitized_sprite_crispness(rgba: np.ndarray) -> np.ndarray:
    rgb = Image.fromarray(rgba[..., :3], "RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.07)
    rgb = ImageEnhance.Color(rgb).enhance(1.05)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.0, percent=48, threshold=3))
    return np.dstack([np.asarray(rgb, dtype=np.uint8), rgba[..., 3]])


def pretone_for_darkplaces_hdr(frames_rgba: list[np.ndarray], target_mean_lum: float = 62.0) -> list[np.ndarray]:
    boosted: list[np.ndarray] = []
    lums = []
    for fr in frames_rgba:
        rgb_im = Image.fromarray(fr[..., :3], "RGB")
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(1.15)
        rgb_im = ImageEnhance.Color(rgb_im).enhance(1.06)
        rgb = np.asarray(rgb_im, dtype=np.float32)
        mask = fr[..., 3] > 128
        if np.any(mask):
            lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
            lums.append(float(lum[mask].mean()))
        boosted.append(np.dstack([np.clip(np.round(rgb), 0, 255).astype(np.uint8), fr[..., 3]]))

    cur_mean = float(np.mean(lums)) if lums else 100.0
    gain = float(np.clip(target_mean_lum / max(1.0, cur_mean), 0.38, 0.92))
    out: list[np.ndarray] = []
    for fr in boosted:
        toned = fr.copy()
        toned[..., :3] = np.clip(np.round(toned[..., :3].astype(np.float32) * gain), 0, 255).astype(np.uint8)
        out.append(toned)
    return out


def write_spr32(path: Path, frames_rgba: list[np.ndarray], ox: int = SPR_OX, oy: int = SPR_OY) -> tuple[int, float]:
    path.parent.mkdir(parents=True, exist_ok=True)
    maxw = max(f.shape[1] for f in frames_rgba)
    maxh = max(f.shape[0] for f in frames_rgba)
    rad = math.sqrt((maxw / 2.0) ** 2 + float(maxh) ** 2)

    buf = bytearray()
    buf += b"IDSP"
    buf += struct.pack("<iifiiifi", 32, 0, rad, maxw, maxh, len(frames_rgba), 0.0, 0)

    lums = []
    for fr in frames_rgba:
        h, w = fr.shape[:2]
        buf += struct.pack("<i", 0)
        buf += struct.pack("<iiii", ox, oy, w, h)
        buf += fr.tobytes()
        m = fr[..., 3] > 128
        if np.any(m):
            rgb = fr[..., :3].astype(np.float32)
            lums.append(float((0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])[m].mean()))

    path.write_bytes(bytes(buf))
    return len(buf), (float(np.mean(lums)) if lums else 0.0)


def save_sheet_8x8(run_grid: list[list[np.ndarray]], out_path: Path, cell_w: int = 248, cell_h: int = 280) -> None:
    sheet = Image.new("RGBA", (cell_w * 8, cell_h * 8), (0, 0, 0, 0))
    for d in range(8):
        for f in range(8):
            cell = resize_rgba_premul(run_grid[d][f], cell_w, cell_h)
            sheet.paste(Image.fromarray(cell, "RGBA"), (f * cell_w, d * cell_h))
    sheet.save(out_path, optimize=True)


def save_turntable_gif(run_grid: list[list[np.ndarray]], bonk_frames: list[np.ndarray], out_path: Path) -> None:
    gw, gh = 300, 338
    yg, xg = np.mgrid[0:gh, 0:gw]
    chk = ((xg // 16 + yg // 16) % 2 == 0)
    bg_arr = np.where(chk[..., None], np.array([36, 41, 54], np.uint8), np.array([25, 29, 39], np.uint8))

    seq: list[Image.Image] = []
    for step in range(24):
        d = (step // 3) % 8
        f = step % 8
        cell = resize_rgba_premul(run_grid[d][f], gw, gh)
        im = Image.fromarray(bg_arr, "RGB").convert("RGBA")
        im.alpha_composite(Image.fromarray(cell, "RGBA"))
        seq.append(im.convert("P", palette=Image.Palette.ADAPTIVE, colors=255))

    for idx, bfr in enumerate(bonk_frames):
        cell = resize_rgba_premul(bfr, gw, gh)
        im = Image.fromarray(bg_arr, "RGB").convert("RGBA")
        im.alpha_composite(Image.fromarray(cell, "RGBA"))
        p_im = im.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        seq.append(p_im)
        if idx in (5, 6):
            seq.append(p_im)

    seq[0].save(
        out_path,
        save_all=True,
        append_images=seq[1:],
        duration=88,
        loop=0,
        optimize=True,
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPR_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    print("1/6 Synthesizing 80 Pure 2D Digitized Live-Action Sprite Frames...")
    idle_raw, run_raw, bonk_raw = build_all_2d_frames()

    sweat_specs = build_3d_sweat_specs(14)
    sweat_im = make_sweat_drop_rgba(36)

    print("2/6 Saving 8-Direction Crazed 2D Idle PNGs...")
    idle_final: list[np.ndarray] = []
    for d in range(8):
        fr = boost_digitized_sprite_crispness(idle_raw[d])
        idle_final.append(fr)
        Image.fromarray(fr, "RGBA").save(OUT_DIR / f"finger_idle_d{d}.png", optimize=True)

    print("3/6 Saving 8x8 360° Crazy Wag-Run Frames + Manic Sweat & Whoosh FX...")
    run_final: list[list[np.ndarray]] = [[] for _ in range(8)]
    for d in range(8):
        for f in range(8):
            fr = boost_digitized_sprite_crispness(run_raw[d][f])
            fx_frame = composite_3d_chaos_fx(
                fr,
                dir_idx=d,
                frame_idx=f,
                n_frames=8,
                sweat_specs=sweat_specs,
                sweat_drop_im=sweat_im,
            )
            run_final[d].append(fx_frame)
            Image.fromarray(fx_frame, "RGBA").save(OUT_DIR / f"finger_d{d}_f{f}.png", optimize=True)
            if d == 0:
                Image.fromarray(fx_frame, "RGBA").save(OUT_DIR / f"finger_{f:02d}.png", optimize=True)

    print("4/6 Saving 8-Frame Signature 'FOREHEAD BONK!' 2D Photographic Sequence...")
    bonk_final: list[np.ndarray] = []
    for f in range(8):
        fr = boost_digitized_sprite_crispness(bonk_raw[f])
        fr = draw_forehead_bonk_fx(fr, f)
        bonk_final.append(fr)
        Image.fromarray(fr, "RGBA").save(OUT_DIR / f"finger_bonk_{f:02d}.png", optimize=True)

    print("5/6 Saving 8x8 Master Sheet, 360° Animated GIF & Baking Quake progs/fr_finger.spr32...")
    save_sheet_8x8(run_final, OUT_DIR / "rubber_finger_360_sheet_8x8.png")
    save_turntable_gif(run_final, bonk_final, OUT_DIR / "rubber_finger_360_spin.gif")

    spr_raw_56: list[np.ndarray] = []
    for d in range(8):
        spr_raw_56.append(resize_rgba_premul(idle_final[d], SPR_W, SPR_H))
    for d in range(8):
        for rf in RUN_6_INDICES:
            spr_raw_56.append(resize_rgba_premul(run_final[d][rf], SPR_W, SPR_H))

    for idx, fr in enumerate(spr_raw_56):
        Image.fromarray(fr, "RGBA").save(SPR_PREVIEW_DIR / f"f_{idx:02d}.png", optimize=True)

    spr_toned_56 = pretone_for_darkplaces_hdr(spr_raw_56, target_mean_lum=62.0)
    nbytes, mean_lum = write_spr32(PROGS_SPR32_PATH, spr_toned_56, ox=SPR_OX, oy=SPR_OY)
    print(f"   -> Wrote {PROGS_SPR32_PATH} ({len(spr_toned_56)} frames, {nbytes:,} bytes, {SPR_W}x{SPR_H}, origin=({SPR_OX},{SPR_OY}), mean_lum={mean_lum:.1f})")

    print("6/6 Writing Interactive 360° HTML Viewers (Folder-Local + 100% Self-Contained Single-File)...")
    (OUT_DIR / "index.html").write_text(
        render_rubber_finger_viewer_html(".", sprite_dir=OUT_DIR, self_contained=False), encoding="utf-8"
    )
    (ROOT_DIR / "rubber_finger_sprite.html").write_text(
        render_rubber_finger_viewer_html(sprite_dir=OUT_DIR, self_contained=True), encoding="utf-8"
    )
    print("=== ALL DONE! ===")


if __name__ == "__main__":
    main()
