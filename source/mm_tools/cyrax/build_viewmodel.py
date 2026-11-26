#!/usr/bin/env python3
"""Build the Cyrax Net Launcher 1st-person 4K viewmodel (v_cyrax.md3 + 68 skin frames).

Reads 5 aligned (1376, 768) 4K articulated cybernetic keyframes from
source/mm_tools/cyrax/assets/src_keyframes/:
  - idle.jpg         : closed 4K brushed gold/black cybernetic blaster
  - charge_half.jpg  : top shroud lifted on hydraulic struts, rails forward glowing green
  - charge_full.jpg  : side & top cowlings hinged wide open exposing blazing green core
  - recoil.jpg       : barrel slammed back on recoil pistons, top breech popped open
  - catch.jpg        : side robotic stabilizer wings/clamps flared wide open

Keys white studio backdrop + enclosed piston gaps cleanly with anti-aliased alpha
and RGB edge bleeding (zero white halo), scales to ~0.76x tucked bottom-right at
crisp 896x546 resolution, and smoothly cross-blends & animates 68 skins (0..67):
  -  0..7   (8f): Idle (subtle breathing + glowing amber/green LEDs)
  -  8..31 (24f): Charge buildup (idle -> charge_half -> charge_full + plasma + heat + shake)
  - 32..43 (12f): Fire + Recoil (32..36 charge_full->recoil + neon-green muzzle flash,
                  37..43 recoil->idle return-to-battery + barrel/breech smoke)
  - 44..49  (6f): Draw / raise pop-up + power-on LED sweep
  - 50..55  (6f): Cooldown / venting (charge_half -> idle closing + steam plumes)
  - 56..67 (12f): Dopamine Capture celebration (idle -> flared-wing catch + cyan/green/gold
                  energy arcs -> settle back toward idle)

Uses only Python stdlib + numpy + Pillow + md3lib (reproducible, zero OpenCV).
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from collections import deque
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
TEX_DIR = HERE / "assets" / "tex"
KEYFRAME_DIR = HERE / "assets" / "src_keyframes"

if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
import md3lib  # noqa: E402

# Native 1376x768 16:9 keyframe space, cropped to bottom-right 896x546 card
SRC_W, SRC_H = 1376, 768
CROP_BOX = (480, 222, 1376, 768)  # 896 x 546 (1:1 sharp 4K crop!)
OUT_SIZE = (896, 546)

# DarkPlaces 16:9 viewplane mapping at VIEW_X = 14.0 (matches build_netsend_disk_view.py)
VIEW_X = 14.0
HALF_W = 27.8
HALF_H = 15.6

# Scale gun to ~0.76x of original size and tuck cleanly into bottom-right
GUN_SCALE = 0.76
GUN_ANCHOR_SRC = (920.0, 768.0)
GUN_ANCHOR_DST = (1050.0, 784.0)  # +16px below y=768 so tilts/pumps never expose a cut bottom

# Landmarks in 1376x768 source coordinates -> transformed into tucked canvas coordinates
_RAW_MUZZLE_XY = (760.0, 426.0)
_RAW_SIDE_LED_XY = (915.0, 558.0)
_RAW_TOP_LED_XY = (1082.0, 535.0)
_RAW_BREECH_XY = (1040.0, 455.0)
_RAW_VENT_SLOTS = (
    (810.0, 475.0, 15.0, 28.0),
    (842.0, 494.0, 15.0, 28.0),
    (906.0, 434.0, 30.0, 14.0),
    (946.0, 456.0, 30.0, 14.0),
)


def _tuck_pt(x: float, y: float) -> Tuple[float, float]:
    return (
        GUN_ANCHOR_DST[0] + (x - GUN_ANCHOR_SRC[0]) * GUN_SCALE,
        GUN_ANCHOR_DST[1] + (y - GUN_ANCHOR_SRC[1]) * GUN_SCALE,
    )


MUZZLE_XY = _tuck_pt(*_RAW_MUZZLE_XY)
BARREL_DIR = (-0.905, -0.425)
SIDE_LED_XY = _tuck_pt(*_RAW_SIDE_LED_XY)
TOP_LED_XY = _tuck_pt(*_RAW_TOP_LED_XY)
BREECH_XY = _tuck_pt(*_RAW_BREECH_XY)
VENT_SLOTS = tuple(
    (*_tuck_pt(vx, vy), rx * GUN_SCALE, ry * GUN_SCALE)
    for vx, vy, rx, ry in _RAW_VENT_SLOTS
)

GUN_DIM = 0.80  # balanced for DarkPlaces rgbGen lightingDiffuse + HDR


def _box_sum_3x3_edge(arr: np.ndarray) -> np.ndarray:
    p = np.pad(arr, ((1, 1), (1, 1)), mode="edge")
    h, w = arr.shape
    return (
        p[0:h, 0:w] + p[0:h, 1:w + 1] + p[0:h, 2:w + 2]
        + p[1:h + 1, 0:w] + p[1:h + 1, 1:w + 1] + p[1:h + 1, 2:w + 2]
        + p[2:h + 2, 0:w] + p[2:h + 2, 1:w + 1] + p[2:h + 2, 2:w + 2]
    )


def bleed_rgb_edges(rgba: np.ndarray, passes: int = 4) -> np.ndarray:
    """Propagate foreground RGB into alpha==0 neighbors so bilinear sampling never shows halos."""
    out = rgba.copy()
    mask = out[..., 3] >= 24
    if not np.any(mask):
        return out
    rgb = out[..., :3].astype(np.float32)
    valid = mask.astype(np.float32)
    for _ in range(passes):
        w_sum = _box_sum_3x3_edge(valid)
        need = (valid < 0.5) & (w_sum > 0.5)
        if not np.any(need):
            break
        for c in range(3):
            c_sum = _box_sum_3x3_edge(rgb[..., c] * valid)
            rgb[..., c][need] = c_sum[need] / w_sum[need]
        valid[need] = 1.0
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    return out


def _flood_components_4(cand: np.ndarray) -> Tuple[np.ndarray, int]:
    """Pure-Python/NumPy 4-connected component labeling for trapped-white hole keying."""
    h, w = cand.shape
    lbl = np.zeros((h, w), dtype=np.int32)
    cid = 0
    ys, xs = np.nonzero(cand)
    for idx in range(len(ys)):
        sy, sx = int(ys[idx]), int(xs[idx])
        if lbl[sy, sx] != 0:
            continue
        cid += 1
        lbl[sy, sx] = cid
        q = deque([(sy, sx)])
        while q:
            y, x = q.popleft()
            if y > 0 and cand[y - 1, x] and lbl[y - 1, x] == 0:
                lbl[y - 1, x] = cid
                q.append((y - 1, x))
            if y + 1 < h and cand[y + 1, x] and lbl[y + 1, x] == 0:
                lbl[y + 1, x] = cid
                q.append((y + 1, x))
            if x > 0 and cand[y, x - 1] and lbl[y, x - 1] == 0:
                lbl[y, x - 1] = cid
                q.append((y, x - 1))
            if x + 1 < w and cand[y, x + 1] and lbl[y, x + 1] == 0:
                lbl[y, x + 1] = cid
                q.append((y, x + 1))
    return lbl, cid


def key_white_gun(rgb: np.ndarray) -> np.ndarray:
    """Clean white-backdrop keying (border + enclosed piston/strut gaps) with AA & un-premultiplication."""
    arr = rgb.astype(np.float32)
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    # Border-connected white studio backdrop
    cand = (lo > 224.0) & (sat < 0.085)
    # Seed border BFS
    h, w = cand.shape
    bg = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        if cand[0, x] and not bg[0, x]:
            bg[0, x] = True
            q.append((0, x))
        if cand[h - 1, x] and not bg[h - 1, x]:
            bg[h - 1, x] = True
            q.append((h - 1, x))
    for y in range(h):
        if cand[y, 0] and not bg[y, 0]:
            bg[y, 0] = True
            q.append((y, 0))
        if cand[y, w - 1] and not bg[y, w - 1]:
            bg[y, w - 1] = True
            q.append((y, w - 1))
    while q:
        y, x = q.popleft()
        if y > 0 and cand[y - 1, x] and not bg[y - 1, x]:
            bg[y - 1, x] = True
            q.append((y - 1, x))
        if y + 1 < h and cand[y + 1, x] and not bg[y + 1, x]:
            bg[y + 1, x] = True
            q.append((y + 1, x))
        if x > 0 and cand[y, x - 1] and not bg[y, x - 1]:
            bg[y, x - 1] = True
            q.append((y, x - 1))
        if x + 1 < w and cand[y, x + 1] and not bg[y, x + 1]:
            bg[y, x + 1] = True
            q.append((y, x + 1))

    # Trapped white gaps inside flared hydraulic piston struts & open cowlings
    trapped_cand = (lo > 234.0) & (sat < 0.065) & (~bg)
    if np.any(trapped_cand):
        tlbl, n_comp = _flood_components_4(trapped_cand)
        if n_comp > 0:
            areas = np.bincount(tlbl.ravel())
            keep_bg = np.zeros(len(areas), dtype=bool)
            keep_bg[1:] = areas[1:] >= 25
            bg = bg | keep_bg[tlbl]

    fg = (~bg).astype(np.uint8)
    fg_img = Image.fromarray(fg * 255, mode="L")
    soft = np.asarray(fg_img.filter(ImageFilter.GaussianBlur(radius=0.85)), dtype=np.float32) / 255.0

    alpha = np.where(bg, np.clip((soft - 0.12) / 0.88, 0.0, 1.0), np.clip(soft * 1.28, 0.0, 1.0))
    bg_dil = np.asarray(Image.fromarray(bg.astype(np.uint8) * 255, mode="L").filter(ImageFilter.MaxFilter(5))) > 0
    alpha = np.where(~bg_dil, 1.0, alpha)

    rim = (~bg) & bg_dil & (lo > 192.0) & (sat < 0.13)
    alpha[rim] *= np.clip((248.0 - lum[rim]) / 56.0, 0.0, 1.0)
    alpha[alpha < 0.04] = 0.0

    semi = (alpha > 0.04) & (alpha < 0.98)
    rgb_clean = arr.copy()
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.20)
    rgb_clean[semi] = np.clip((arr[semi] - inv[:, None] * 255.0) / denom[:, None], 0.0, 255.0)
    rgb_clean[alpha <= 0.04] = 0.0

    rgb_clean *= GUN_DIM
    rgb_clean[alpha <= 0.04] = 0.0

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    return out


def _blend_premul_rgba(a_rgba: np.ndarray, b_rgba: np.ndarray, t: float) -> np.ndarray:
    """Smooth premultiplied cross-dissolve between two aligned RGBA keyframes."""
    if t <= 0.001:
        return a_rgba
    if t >= 0.999:
        return b_rgba
    aa = a_rgba[..., 3:4].astype(np.float32) / 255.0
    ab = b_rgba[..., 3:4].astype(np.float32) / 255.0
    pm = (a_rgba[..., :3].astype(np.float32) * aa) * (1.0 - t) + (b_rgba[..., :3].astype(np.float32) * ab) * t
    a = aa * (1.0 - t) + ab * t
    nz = a[..., 0] > 1e-3
    out = np.zeros_like(a_rgba)
    rgb = np.zeros_like(pm)
    rgb[nz] = pm[nz] / a[nz]
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a[..., 0] * 255.0), 0, 255).astype(np.uint8)
    return out


def _warp_premul_rgba(
    rgba: np.ndarray,
    src_pivot: Tuple[float, float],
    dst_pivot: Tuple[float, float],
    scale: float,
    angle_deg: float,
    dx: float = 0.0,
    dy: float = 0.0,
) -> np.ndarray:
    """Premultiplied affine warp mapping src_pivot -> dst_pivot + (dx, dy) with scale & rotation."""
    h, w = rgba.shape[:2]
    a = rgba[..., 3].astype(np.float32) / 255.0
    pm = rgba[..., :3].astype(np.float32) * a[..., None]

    rad = math.radians(-angle_deg)
    ca, sa = math.cos(rad) / scale, math.sin(rad) / scale
    sx, sy = src_pivot
    ox, oy = dst_pivot[0] + dx, dst_pivot[1] + dy
    tx = sx - ca * ox + sa * oy
    ty = sy - sa * ox - ca * oy
    mat = (ca, -sa, tx, sa, ca, ty)

    a_im = Image.fromarray(a, mode="F").transform((w, h), Image.Transform.AFFINE, mat, resample=Image.Resampling.BILINEAR)
    a_out = np.clip(np.asarray(a_im, dtype=np.float32), 0.0, 1.0)
    nz = a_out > 1e-3
    denom = np.where(nz, a_out, 1.0)

    out = np.zeros((h, w, 4), dtype=np.uint8)
    for c in range(3):
        ch_im = Image.fromarray(pm[..., c], mode="F").transform((w, h), Image.Transform.AFFINE, mat, resample=Image.Resampling.BILINEAR)
        ch = np.asarray(ch_im, dtype=np.float32)
        val = np.where(nz, ch / denom, 0.0)
        out[..., c] = np.clip(np.round(val), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a_out * 255.0), 0, 255).astype(np.uint8)
    return out


def _add_glow_layer(base_rgba: np.ndarray, glow_rgb: np.ndarray, glow_alpha: np.ndarray) -> np.ndarray:
    out = base_rgba.astype(np.float32)
    ga = np.clip(glow_alpha, 0.0, 1.0)
    out[..., :3] = np.clip(out[..., :3] + glow_rgb * ga[..., None], 0.0, 255.0)
    ba = out[..., 3] / 255.0
    na = np.clip(ba + ga * (1.0 - ba), 0.0, 1.0)
    out[..., 3] = na * 255.0
    out[out[..., 3] < 2.0] = 0.0
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def _draw_radial_glow(
    glow_rgb: np.ndarray,
    glow_a: np.ndarray,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    color: Tuple[float, float, float],
    strength: float,
    power: float = 2.0,
) -> None:
    if strength <= 0.0:
        return
    h, w = glow_a.shape
    x0 = max(0, int(math.floor(cx - rx * 1.4)))
    x1 = min(w, int(math.ceil(cx + rx * 1.4)))
    y0 = max(0, int(math.floor(cy - ry * 1.4)))
    y1 = min(h, int(math.ceil(cy + ry * 1.4)))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    fall = np.clip(1.0 - d, 0.0, 1.0) ** power * strength
    glow_rgb[y0:y1, x0:x1, 0] += color[0] * fall
    glow_rgb[y0:y1, x0:x1, 1] += color[1] * fall
    glow_rgb[y0:y1, x0:x1, 2] += color[2] * fall
    glow_a[y0:y1, x0:x1] = np.clip(glow_a[y0:y1, x0:x1] + fall, 0.0, 1.0)


def _pixelate_block(arr: np.ndarray, block: int = 3) -> np.ndarray:
    if block <= 1:
        return arr
    h, w = arr.shape[:2]
    im = Image.fromarray(arr)
    sw = max(1, w // block)
    sh = max(1, h // block)
    small = im.resize((sw, sh), Image.Resampling.BOX)
    return np.asarray(small.resize((w, h), Image.Resampling.NEAREST))


def _paint_pixel_burst(
    canvas_shape: Tuple[int, int],
    cx: float,
    cy: float,
    radius: float,
    seed: int,
    n_rays: int = 18,
    n_sparks: int = 56,
    block: int = 3,
    intensity: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Synthesize a crisp, chunky pixelated neon-green MK3 plasma/muzzle blast overlay."""
    h, w = canvas_shape
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    drw = ImageDraw.Draw(im)

    bx, by = BARREL_DIR
    base_ang = math.atan2(by, bx)

    for k in range(n_rays):
        ang = base_ang + (k / float(n_rays)) * 2.0 * math.pi + rng.uniform(-0.14, 0.14)
        fwd_dot = max(0.0, math.cos(ang - base_ang))
        r_len = radius * (0.45 + 0.85 * (fwd_dot ** 1.4)) * rng.uniform(0.70, 1.25)
        w_ang = rng.uniform(0.06, 0.16)
        p0 = (cx, cy)
        p1 = (cx + math.cos(ang - w_ang) * r_len * 0.48, cy + math.sin(ang - w_ang) * r_len * 0.48)
        p2 = (cx + math.cos(ang) * r_len, cy + math.sin(ang) * r_len)
        p3 = (cx + math.cos(ang + w_ang) * r_len * 0.48, cy + math.sin(ang + w_ang) * r_len * 0.48)
        col = (40, 255, 75, int(min(255, 225 * intensity)))
        drw.polygon([p0, p1, p2, p3], fill=col)

    for k in range(max(8, n_rays // 2)):
        ang = base_ang + (k / float(max(8, n_rays // 2))) * 2.0 * math.pi + 0.2
        r_len = radius * 0.56 * rng.uniform(0.75, 1.15)
        p1 = (cx + math.cos(ang - 0.14) * r_len * 0.35, cy + math.sin(ang - 0.14) * r_len * 0.35)
        p2 = (cx + math.cos(ang) * r_len, cy + math.sin(ang) * r_len)
        p3 = (cx + math.cos(ang + 0.14) * r_len * 0.35, cy + math.sin(ang + 0.14) * r_len * 0.35)
        drw.polygon([(cx, cy), p1, p2, p3], fill=(175, 255, 165, int(min(255, 245 * intensity))))

    cr = max(6.0, radius * 0.22)
    drw.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(235, 255, 235, 255))

    for _ in range(n_sparks):
        ang = base_ang + rng.normal(0.0, 0.72)
        dist = radius * rng.uniform(0.35, 1.45)
        sx = cx + math.cos(ang) * dist
        sy = cy + math.sin(ang) * dist
        sz = int(rng.integers(2, 5))
        tone = int(rng.choice([0, 1, 2]))
        scol = [(60, 255, 90, 240), (160, 255, 140, 255), (20, 220, 60, 210)][tone]
        drw.rectangle((sx - sz, sy - sz, sx + sz, sy + sz), fill=scol)

    arr = _pixelate_block(np.asarray(im, dtype=np.uint8), block=block)
    rgb = arr[..., :3].astype(np.float32) * intensity
    alpha = (arr[..., 3].astype(np.float32) / 255.0) * min(1.0, intensity)
    return rgb, alpha


def _paint_swirl_plasma(
    canvas_shape: Tuple[int, int],
    cx: float,
    cy: float,
    phase: float,
    charge: float,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Swirling neon-green barrel plasma vortex + converging pixel embers during charge (8..31)."""
    h, w = canvas_shape
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    drw = ImageDraw.Draw(im)

    max_r = (18.0 + 58.0 * charge) * 0.85
    n_arms = 4
    for arm in range(n_arms):
        base_a = phase * 2.0 * math.pi + arm * (2.0 * math.pi / n_arms)
        steps = 12
        for s in range(steps):
            u = s / float(steps - 1)
            r = (1.0 - u) * max_r + 2.0
            a = base_a + u * 2.8
            px = cx + math.cos(a) * r
            py = cy + math.sin(a) * r * 0.88
            sz = max(2.0, (1.0 - u * 0.5) * (2.5 + 3.0 * charge))
            g = int(200 + 55 * u)
            rc = int(35 + 165 * (u ** 2))
            al = int(min(255, (75 + 180 * charge) * (0.35 + 0.65 * u)))
            drw.rectangle((px - sz, py - sz, px + sz, py + sz), fill=(rc, g, rc, al))

    n_embers = int(8 + 20 * charge)
    for k in range(n_embers):
        a = rng.uniform(0, 2 * math.pi) + phase * 1.4
        r = rng.uniform(0.35, 1.35) * (22.0 + 62.0 * charge)
        ex = cx + math.cos(a) * r
        ey = cy + math.sin(a) * r
        sz = 2.0 if k % 3 else 3.0
        drw.rectangle((ex - sz, ey - sz, ex + sz, ey + sz), fill=(110, 255, 130, int(145 + 110 * charge)))

    cr = 4.5 + 13.0 * charge
    drw.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(140, 255, 150, int(130 + 125 * charge)))
    cr2 = max(2.0, cr * 0.52)
    drw.ellipse((cx - cr2, cy - cr2, cx + cr2, cy + cr2), fill=(235, 255, 235, int(160 + 95 * charge)))

    arr = _pixelate_block(np.asarray(im, dtype=np.uint8), block=3)
    return arr[..., :3].astype(np.float32), arr[..., 3].astype(np.float32) / 255.0


def _paint_smoke_plume(
    canvas_shape: Tuple[int, int],
    cx: float,
    cy: float,
    progress: float,
    seed: int,
    tint_green: float = 0.65,
) -> Tuple[np.ndarray, np.ndarray]:
    """Pixelated neon-mint/white cooling steam & smoke billowing from muzzle/breech/vents."""
    h, w = canvas_shape
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    drw = ImageDraw.Draw(im)

    fade = max(0.0, 1.0 - 0.82 * progress)
    for k in range(20):
        drift_t = (progress * 1.15 + k * 0.04) % 1.0
        px = cx + BARREL_DIR[0] * (10.0 + 78.0 * progress) + rng.normal(0.0, 12.0 + 20.0 * progress)
        py = cy - (12.0 + 76.0 * progress) + rng.normal(0.0, 9.5 + 13.0 * progress)
        rad = 5.0 + 14.0 * drift_t + rng.uniform(0.0, 5.0)
        g = int(225 + 30 * tint_green)
        r = int(165 - 45 * tint_green)
        b = int(170 - 40 * tint_green)
        al = int(max(0, min(220, (175 * fade) * rng.uniform(0.60, 1.0))))
        drw.ellipse((px - rad, py - rad, px + rad, py + rad), fill=(r, g, b, al))

    arr = _pixelate_block(np.asarray(im, dtype=np.uint8), block=3)
    return arr[..., :3].astype(np.float32), arr[..., 3].astype(np.float32) / 255.0


def _paint_catch_arcs(
    canvas_shape: Tuple[int, int],
    cx: float,
    cy: float,
    dx: float,
    dy: float,
    progress: float,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Crackling green-gold-cyan electric energy arcs & celebratory spark burst around blaster (frames 56..67)."""
    h, w = canvas_shape
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    drw = ImageDraw.Draw(im)

    fade = math.sin(min(1.0, progress) * math.pi) * 0.85 + 0.35 * (1.0 - progress)
    fade = max(0.2, min(1.0, fade))

    pts_anchor = [
        (MUZZLE_XY[0] + dx, MUZZLE_XY[1] + dy),
        (SIDE_LED_XY[0] + dx, SIDE_LED_XY[1] + dy),
        (TOP_LED_XY[0] + dx, TOP_LED_XY[1] + dy),
    ]
    palette = [
        (75, 255, 115, int(245 * fade)),
        (255, 225, 65, int(245 * fade)),
        (70, 240, 255, int(245 * fade)),
    ]

    for b_idx in range(7):
        col = palette[b_idx % len(palette)]
        if b_idx < 3:
            p0 = pts_anchor[b_idx % 2]
            p1 = pts_anchor[(b_idx + 1) % 3]
        elif b_idx == 3:
            # Left flared wing -> right flared wing arc across the barrel!
            p0 = (MUZZLE_XY[0] + dx - 110.0, MUZZLE_XY[1] + dy + 65.0)
            p1 = (TOP_LED_XY[0] + dx + 135.0, TOP_LED_XY[1] + dy + 25.0)
        else:
            ang = rng.uniform(0, 2 * math.pi)
            rad = rng.uniform(55.0, 130.0) * (0.7 + 0.4 * (1.0 - progress))
            p0 = (cx, cy)
            p1 = (cx + math.cos(ang) * rad, cy + math.sin(ang) * rad)

        segs = 6
        poly = [p0]
        for s in range(1, segs):
            u = s / float(segs)
            jx = float(rng.normal(0.0, 12.0))
            jy = float(rng.normal(0.0, 12.0))
            poly.append((p0[0] + (p1[0] - p0[0]) * u + jx, p0[1] + (p1[1] - p0[1]) * u + jy))
        poly.append(p1)
        drw.line(poly, fill=col, width=4)
        drw.line(poly, fill=(240, 255, 240, int(255 * fade)), width=1)

    ring_r = 16.0 + 82.0 * progress
    ring_col = (110, 255, 140, int(215 * (1.0 - progress * 0.8)))
    drw.ellipse((cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r), outline=ring_col, width=4)

    for k in range(32):
        ang = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(18.0, 136.0) * (0.4 + 0.7 * progress)
        sx = cx + math.cos(ang) * dist
        sy = cy + math.sin(ang) * dist
        sz = 3 if k % 3 else 4
        drw.rectangle((sx - sz, sy - sz, sx + sz, sy + sz), fill=palette[k % len(palette)])

    arr = _pixelate_block(np.asarray(im, dtype=np.uint8), block=3)
    return arr[..., :3].astype(np.float32), arr[..., 3].astype(np.float32) / 255.0


def _apply_vents_and_leds(
    glow_rgb: np.ndarray,
    glow_a: np.ndarray,
    dx: float,
    dy: float,
    led_col: Tuple[float, float, float],
    led_strength: float,
    vent_col: Tuple[float, float, float],
    vent_strength: float,
    core_green: float,
    spill_col: Tuple[float, float, float] = (40, 255, 95),
) -> None:
    _draw_radial_glow(glow_rgb, glow_a, SIDE_LED_XY[0] + dx, SIDE_LED_XY[1] + dy, 26 * GUN_SCALE, 26 * GUN_SCALE, led_col, led_strength, power=1.8)
    _draw_radial_glow(glow_rgb, glow_a, SIDE_LED_XY[0] + dx, SIDE_LED_XY[1] + dy, 12 * GUN_SCALE, 12 * GUN_SCALE, (255, 255, 220), led_strength * 0.65, power=2.2)

    _draw_radial_glow(glow_rgb, glow_a, TOP_LED_XY[0] + dx, TOP_LED_XY[1] + dy, 28 * GUN_SCALE, 20 * GUN_SCALE, led_col, led_strength * 0.95, power=1.8)
    _draw_radial_glow(glow_rgb, glow_a, TOP_LED_XY[0] + dx, TOP_LED_XY[1] + dy, 13 * GUN_SCALE, 10 * GUN_SCALE, (255, 255, 220), led_strength * 0.60, power=2.2)

    if vent_strength > 0.01:
        for vx, vy, rx, ry in VENT_SLOTS:
            _draw_radial_glow(glow_rgb, glow_a, vx + dx, vy + dy, rx * 1.5, ry * 1.5, vent_col, vent_strength, power=1.7)
            _draw_radial_glow(glow_rgb, glow_a, vx + dx, vy + dy, rx * 0.75, ry * 0.75, (235, 255, 220), vent_strength * 0.55, power=2.2)

    if core_green > 0.01:
        _draw_radial_glow(
            glow_rgb, glow_a,
            MUZZLE_XY[0] + dx + 30, MUZZLE_XY[1] + dy + 18,
            82 * GUN_SCALE, 56 * GUN_SCALE, spill_col, core_green * 0.50, power=1.6,
        )


def _crop_and_resize(rgba: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = CROP_BOX
    cropped = rgba[y0:y1, x0:x1]
    if (cropped.shape[1], cropped.shape[0]) == OUT_SIZE:
        return bleed_rgb_edges(cropped, passes=4)
    a = cropped[..., 3].astype(np.float32) / 255.0
    a_rsz = np.asarray(Image.fromarray(a, mode="F").resize(OUT_SIZE, Image.Resampling.BOX), dtype=np.float32)
    a_rsz = np.clip(a_rsz, 0.0, 1.0)
    nz = a_rsz > 1e-4
    denom = np.where(nz, a_rsz, 1.0)
    out = np.empty((OUT_SIZE[1], OUT_SIZE[0], 4), dtype=np.uint8)
    for c in range(3):
        pm = cropped[..., c].astype(np.float32) * a
        pm_rsz = np.asarray(Image.fromarray(pm, mode="F").resize(OUT_SIZE, Image.Resampling.BOX), dtype=np.float32)
        ch = np.where(nz, pm_rsz / denom, 0.0)
        out[..., c] = np.clip(np.round(ch), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a_rsz * 255.0), 0, 255).astype(np.uint8)
    return bleed_rgb_edges(out, passes=4)


def build_v_cyrax_md3_bytes() -> bytes:
    """Build the 1-frame flat sprite-card MD3 matching the bottom-right 16:9 viewplane crop."""
    x0, y0, x1, y1 = CROP_BOX
    yl = HALF_W * (1.0 - 2.0 * x0 / float(SRC_W))
    yr = HALF_W * (1.0 - 2.0 * x1 / float(SRC_W))
    zt = HALF_H * (1.0 - 2.0 * y0 / float(SRC_H))
    zb = HALF_H * (1.0 - 2.0 * y1 / float(SRC_H))

    card = [(VIEW_X, yl, zb), (VIEW_X, yl, zt), (VIEW_X, yr, zt), (VIEW_X, yr, zb)]
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    surf = dict(
        name="card",
        shader="progs/cyrax_vm_00",
        tris=[(0, 1, 2), (0, 2, 3)],
        st=st,
        frames=[(card, [(-1.0, 0.0, 0.0)] * 4)],
    )
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "v_cyrax.md3"
        md3lib.write(str(p), dict(name="v_cyrax", surfaces=[surf], nframes=1))
        return p.read_bytes()


def _load_keyed_poses(kf_dir: Path) -> Dict[str, np.ndarray]:
    poses: Dict[str, np.ndarray] = {}
    for name in ("idle", "charge_half", "charge_full", "recoil", "catch"):
        p = kf_dir / f"{name}.jpg"
        if not p.is_file():
            raise FileNotFoundError(f"Missing 4K keyframe: {p}")
        rgb = np.asarray(Image.open(p).convert("RGB"))
        poses[name] = key_white_gun(rgb)
    return poses


def generate_viewmodel_frames(kf_dir: Path = KEYFRAME_DIR, out_dir: Path = TEX_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    poses = _load_keyed_poses(kf_dir)
    h, w = poses["idle"].shape[:2]

    written: list[Path] = []
    for idx in range(68):
        dx = 0.0
        dy = 0.0
        ang = 0.0

        glow_rgb = np.zeros((h, w, 3), dtype=np.float32)
        glow_a = np.zeros((h, w), dtype=np.float32)
        extra_overlays: list[Tuple[np.ndarray, np.ndarray]] = []

        if 0 <= idx <= 7:
            # Idle: closed cybernetic blaster with subtle breathing + pulsing amber/green LEDs
            pose_rgba = poses["idle"]
            t = idx / 8.0
            dx = 1.4 * math.cos(2.0 * math.pi * t)
            dy = 2.6 * math.sin(2.0 * math.pi * t)
            ang = 0.22 * math.sin(2.0 * math.pi * t)
            pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * t)
            led_col = (
                255.0 * (1.0 - 0.72 * pulse),
                150.0 + 105.0 * pulse,
                20.0 + 85.0 * pulse,
            )
            _apply_vents_and_leds(glow_rgb, glow_a, dx, dy, led_col, 0.42 + 0.35 * pulse, (0, 0, 0), 0.0, 0.08 * pulse)

        elif 8 <= idx <= 31:
            # Charge buildup (24f): articulates idle -> charge_half (f18) -> charge_full (f28..31)
            p = (idx - 8) / 23.0
            if p <= 0.45:
                u = p / 0.45
                s = u * u * (3.0 - 2.0 * u)
                pose_rgba = _blend_premul_rgba(poses["idle"], poses["charge_half"], s)
            else:
                u = min(1.0, (p - 0.45) / 0.42)
                s = u * u * (3.0 - 2.0 * u)
                pose_rgba = _blend_premul_rgba(poses["charge_half"], poses["charge_full"], s)

            rng = np.random.default_rng(1000 + idx)
            shake = 0.6 + 5.2 * (p ** 1.6)
            dx = 8.0 * p + float(rng.uniform(-shake, shake))
            dy = 4.5 * p + float(rng.uniform(-shake * 0.85, shake * 0.85))
            ang = -1.1 * p + float(rng.uniform(-0.6, 0.6)) * p

            g_mix = max(0.0, min(1.0, (p - 0.18) / 0.65))
            vent_col = (
                255.0 * (1.0 - 0.78 * g_mix),
                115.0 + 140.0 * g_mix,
                20.0 + 85.0 * g_mix,
            )
            led_col = (
                120.0 * (1.0 - p) + 50.0 * p,
                220.0 + 35.0 * p,
                60.0 + 80.0 * p,
            )
            _apply_vents_and_leds(
                glow_rgb, glow_a, dx, dy,
                led_col, 0.55 + 0.65 * p,
                vent_col, 0.50 + 0.85 * p,
                0.22 + 0.85 * p,
            )
            sw_rgb, sw_a = _paint_swirl_plasma(
                (h, w),
                MUZZLE_XY[0] + dx - 8.0,
                MUZZLE_XY[1] + dy - 4.0,
                phase=(idx - 8) / 6.0,
                charge=p,
                seed=2000 + idx,
            )
            extra_overlays.append((sw_rgb, sw_a))

        elif 32 <= idx <= 43:
            # Fire blast + Recoil (12f)
            if idx <= 36:
                # 32..36: charge_full -> recoil snap + neon-green muzzle flash burst
                fp = (idx - 32) / 4.0
                pose_rgba = _blend_premul_rgba(poses["charge_full"], poses["recoil"], min(1.0, fp * 1.15))
                dx = 14.0 + 14.0 * fp
                dy = 8.0 + 9.0 * fp
                ang = -1.8 - 1.8 * fp
                flash_str = [1.15, 1.25, 1.05, 0.85, 0.62][idx - 32]
                flash_rad = [145.0, 175.0, 150.0, 120.0, 92.0][idx - 32]
                _apply_vents_and_leds(
                    glow_rgb, glow_a, dx, dy,
                    (90, 255, 120), 1.10 * flash_str,
                    (85, 255, 105), 1.00 * flash_str,
                    1.05 * flash_str,
                )
                _draw_radial_glow(
                    glow_rgb, glow_a,
                    MUZZLE_XY[0] + dx - 16, MUZZLE_XY[1] + dy - 8,
                    120, 88, (75, 255, 105), 0.70 * flash_str, power=1.5,
                )
                fb_rgb, fb_a = _paint_pixel_burst(
                    (h, w),
                    MUZZLE_XY[0] + dx - 14.0,
                    MUZZLE_XY[1] + dy - 6.0,
                    radius=flash_rad,
                    seed=3200 + idx,
                    n_rays=18,
                    n_sparks=56,
                    block=3,
                    intensity=flash_str,
                )
                extra_overlays.append((fb_rgb, fb_a))
            else:
                # 37..43: recoil returning smoothly to idle + barrel & popped-breech smoke
                rp = (idx - 37) / 6.0
                smooth = rp * rp * (3.0 - 2.0 * rp)
                pose_rgba = _blend_premul_rgba(poses["recoil"], poses["idle"], smooth)
                ease = 1.0 - smooth
                dx = 26.0 * ease
                dy = 16.0 * ease
                ang = -3.6 * ease
                cool = 1.0 - rp
                _apply_vents_and_leds(
                    glow_rgb, glow_a, dx, dy,
                    (255.0 * rp + 60.0 * cool, 160.0 * rp + 255.0 * cool, 30.0 + 70.0 * cool),
                    0.50 + 0.45 * cool,
                    (255.0 * rp + 75.0 * cool, 130.0 * rp + 255.0 * cool, 25.0 + 80.0 * cool),
                    0.70 * cool,
                    0.35 * cool,
                )
                for sx, sy in (MUZZLE_XY, BREECH_XY):
                    sm_rgb, sm_a = _paint_smoke_plume(
                        (h, w),
                        sx + dx - 10.0,
                        sy + dy - 10.0,
                        progress=0.12 + 0.85 * rp,
                        seed=3700 + idx + int(sx),
                        tint_green=0.70 * cool + 0.25,
                    )
                    extra_overlays.append((sm_rgb, sm_a))

        elif 44 <= idx <= 49:
            # Draw / raise pop-up (6f) + power-on LED sweep
            pose_rgba = poses["idle"]
            dp = (idx - 44) / 5.0
            rise_offsets = [150.0, 88.0, 40.0, 13.0, -4.0, 0.0]
            rot_offsets = [-6.0, -3.8, -1.8, -0.5, 0.3, 0.0]
            dy = rise_offsets[idx - 44]
            dx = dy * 0.25
            ang = rot_offsets[idx - 44]
            boot_flicker = 1.0 if idx in (46, 48, 49) else 0.35
            led_col = (55, 255, 95) if idx >= 47 else (255, 165, 25)
            _apply_vents_and_leds(glow_rgb, glow_a, dx, dy, led_col, 0.65 * boot_flicker, (0, 0, 0), 0.0, 0.12 * dp)

        elif 50 <= idx <= 55:
            # Cooldown / venting (6f): charge_half closing smoothly back into idle + steam plumes
            vp = (idx - 50) / 5.0
            smooth = vp * vp * (3.0 - 2.0 * vp)
            pose_rgba = _blend_premul_rgba(poses["charge_half"], poses["idle"], smooth)
            cool = 1.0 - vp
            dx = 3.0 * cool * math.sin(idx * 2.2)
            dy = 3.5 * cool
            ang = -0.6 * cool
            vent_col = (
                255.0 * vp + 70.0 * cool,
                110.0 * vp + 255.0 * cool,
                20.0 + 75.0 * cool,
            )
            _apply_vents_and_leds(
                glow_rgb, glow_a, dx, dy,
                (255.0 * vp + 65.0 * cool, 165.0 + 90.0 * cool, 25.0 + 65.0 * cool),
                0.55 + 0.35 * cool,
                vent_col,
                0.70 * cool,
                0.25 * cool,
            )
            for vx, vy in (VENT_SLOTS[0][:2], VENT_SLOTS[2][:2], MUZZLE_XY):
                sm_rgb, sm_a = _paint_smoke_plume(
                    (h, w),
                    vx + dx,
                    vy + dy,
                    progress=0.15 + 0.80 * vp,
                    seed=5000 + idx * 17 + int(vx),
                    tint_green=0.55 * cool + 0.20,
                )
                extra_overlays.append((sm_rgb, sm_a))

        else:
            # 56..67 (12f): Dopamine Capture celebration!
            # Snaps idle -> flared-wing catch pose (57..62) then smoothly settles back toward idle (63..67)
            k = idx - 56
            cp = k / 11.0
            catch_weights = [0.45, 0.92, 1.00, 1.00, 1.00, 1.00, 0.95, 0.80, 0.58, 0.36, 0.16, 0.0]
            cw = catch_weights[k]
            pose_rgba = _blend_premul_rgba(poses["idle"], poses["catch"], cw)

            pump_dx = [-4.0, -9.0, -11.0, -8.0, -9.5, -10.5, -8.0, -5.5, -3.5, -2.0, -0.8, 0.0]
            pump_dy = [-2.5, -5.5, -6.5, -4.0, -5.5, -6.0, -4.0, -2.8, -1.8, -1.0, -0.4, 0.0]
            pump_ang = [1.0, 2.2, 2.6, 1.6, 2.0, 2.3, 1.5, 1.0, 0.6, 0.3, 0.1, 0.0]
            dx = pump_dx[k]
            dy = pump_dy[k]
            ang = pump_ang[k]

            strobe = (
                (55.0, 245.0, 255.0),
                (70.0, 255.0, 100.0),
                (255.0, 220.0, 50.0),
            )[k % 3]
            fade = 1.0 - 0.55 * (cp ** 1.5)
            _apply_vents_and_leds(
                glow_rgb, glow_a, dx, dy,
                strobe, 1.15 * fade,
                strobe, 0.95 * fade,
                0.85 * fade,
                spill_col=strobe,
            )
            arc_rgb, arc_a = _paint_catch_arcs(
                (h, w),
                MUZZLE_XY[0] + dx - 8.0,
                MUZZLE_XY[1] + dy - 5.0,
                dx, dy,
                progress=cp,
                seed=5600 + idx,
            )
            extra_overlays.append((arc_rgb, arc_a))

        frame_rgba = _warp_premul_rgba(
            pose_rgba,
            src_pivot=GUN_ANCHOR_SRC,
            dst_pivot=GUN_ANCHOR_DST,
            scale=GUN_SCALE,
            angle_deg=ang,
            dx=dx,
            dy=dy,
        )
        gun_mask = np.clip(frame_rgba[..., 3].astype(np.float32) / 255.0 + 0.15, 0.0, 1.0)
        frame_rgba = _add_glow_layer(frame_rgba, glow_rgb, glow_a * gun_mask)
        for ov_rgb, ov_a in extra_overlays:
            frame_rgba = _add_glow_layer(frame_rgba, ov_rgb, ov_a)

        final_rgba = _crop_and_resize(frame_rgba)
        out_path = out_dir / f"cyrax_vm_{idx:02d}.png"
        Image.fromarray(final_rgba, "RGBA").save(out_path, format="PNG", compress_level=9, optimize=False)
        written.append(out_path)

    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kf-dir", type=Path, default=KEYFRAME_DIR, help="Directory with 5 4K keyframes")
    ap.add_argument("--out-dir", type=Path, default=TEX_DIR, help="Output directory for 68 PNG frames")
    args = ap.parse_args()
    paths = generate_viewmodel_frames(args.kf_dir, args.out_dir)
    print(f"Generated {len(paths)} 4K viewmodel frames in {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
