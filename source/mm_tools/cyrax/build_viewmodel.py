#!/usr/bin/env python3
"""Build the Cyrax Net Launcher 1st-person viewmodel (v_cyrax.md3 + 56 skin frames).

Reads the base yellow/black robotic blaster image, keys the white studio
background cleanly with anti-aliased alpha edges and RGB edge bleeding (zero
white halo), and deterministically synthesizes 56 RGBA skin frames into
source/mm_tools/cyrax/assets/tex/cyrax_vm_00.png .. cyrax_vm_55.png:
  -  0..7   (8f): Idle (robotic breathing + pulsing amber/green LEDs)
  -  8..31 (24f): Charge buildup (energy core glow, hot orange->green vents,
                  escalating mechanical shake, swirling green barrel plasma)
  - 32..43 (12f): Fire blast + recoil (32..36 pixelated neon-green muzzle flash,
                  37..43 heavy kickback recoil + barrel smoke return-to-battery)
  - 44..49  (6f): Draw / raise pop-up
  - 50..55  (6f): Cooldown / venting state

Uses only Python stdlib + numpy + Pillow + md3lib (reproducible, zero OpenCV).
"""
from __future__ import annotations

import argparse
import math
import sys
from collections import deque
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
MM_TOOLS = HERE.parent
TEX_DIR = HERE / "assets" / "tex"

if str(MM_TOOLS) not in sys.path:
    sys.path.insert(0, str(MM_TOOLS))
import md3lib  # noqa: E402

DEFAULT_SRC_GUN = Path(
    "/home/computer/.gemini/antigravity/brain/c7c79a0e-f4b1-42bb-8730-fe3878e1c7bd/"
    ".user_uploaded/media_1795677499739_0bb792dc.jpg"
)

# 16:9 screen crop (x0, y0, x1, y1) in 1024x576 source coordinates.
# Leaves generous headroom on the left & top for swirling plasma + muzzle flash,
# and anchors directly to the bottom-right corner of the 16:9 viewplane.
CROP_BOX = (260, 110, 1024, 576)  # 764 x 466
OUT_SIZE = (640, 390)             # crisp game texture resolution (~same aspect)
SRC_W, SRC_H = 1024, 576

# DarkPlaces 16:9 viewplane mapping at VIEW_X = 14.0 (matches build_netsend_disk_view.py)
VIEW_X = 14.0
HALF_W = 27.8
HALF_H = 15.6

# Landmarks in 1024x576 source coordinates
MUZZLE_XY = (566.0, 322.0)
BARREL_DIR = (-0.905, -0.425)     # unit vector pointing out of the barrel
SIDE_LED_XY = (668.0, 405.0)
TOP_LED_XY = (784.0, 394.0)
VENT_SLOTS = (
    (603.0, 358.0, 11.0, 22.0, -24.0),   # front side barrel slot
    (626.0, 372.0, 11.0, 22.0, -24.0),   # rear side barrel slot
    (676.0, 326.0, 24.0, 10.0, 24.0),    # top rib vent 1
    (706.0, 342.0, 24.0, 10.0, 24.0),    # top rib vent 2
)

GUN_DIM = 0.78  # baked dimming for DarkPlaces rgbGen lightingDiffuse + HDR


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


def _flood_border_bg(cand: np.ndarray) -> np.ndarray:
    """4-connected flood-fill from image borders on boolean mask `cand` (pure NumPy/Python)."""
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
    return bg


def key_white_gun(rgb: np.ndarray) -> np.ndarray:
    """Clean white-backdrop keying with anti-aliased edge feathering and white un-premultiplication."""
    arr = rgb.astype(np.float32)
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    # Candidate white studio pixels connected to the image border
    cand = (lo > 224.0) & (sat < 0.085)
    bg = _flood_border_bg(cand)
    fg = (~bg).astype(np.uint8)

    # Anti-aliased alpha along the silhouette rim via Pillow Gaussian blur of the binary fg mask
    fg_img = Image.fromarray(fg * 255, mode="L")
    soft = np.asarray(fg_img.filter(ImageFilter.GaussianBlur(radius=0.85)), dtype=np.float32) / 255.0

    # Pure interior stays 1.0, pure exterior stays 0.0, 1.5px rim gets crisp AA
    # Also suppress pale near-white JPEG compression fringe on the outer rim
    alpha = np.where(bg, np.clip((soft - 0.12) / 0.88, 0.0, 1.0), np.clip(soft * 1.28, 0.0, 1.0))
    # Guarantee solid interior away from bg
    bg_dil = np.asarray(Image.fromarray(bg.astype(np.uint8) * 255, mode="L").filter(ImageFilter.MaxFilter(5))) > 0
    alpha = np.where(~bg_dil, 1.0, alpha)

    rim = (~bg) & bg_dil & (lo > 192.0) & (sat < 0.13)
    alpha[rim] *= np.clip((248.0 - lum[rim]) / 56.0, 0.0, 1.0)
    alpha[alpha < 0.04] = 0.0

    # Un-premultiply white studio spill on semi-transparent rim pixels
    semi = (alpha > 0.04) & (alpha < 0.98)
    rgb_clean = arr.copy()
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.20)
    rgb_clean[semi] = np.clip((arr[semi] - inv[:, None] * 255.0) / denom[:, None], 0.0, 255.0)
    rgb_clean[alpha <= 0.04] = 0.0

    # Bake GUN_DIM on the gun body for DarkPlaces HDR / lightingDiffuse
    rgb_clean *= GUN_DIM
    rgb_clean[alpha <= 0.04] = 0.0

    out = np.zeros((*rgb.shape[:2], 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    return out


def _shift_gun_rgba(
    rgba: np.ndarray,
    dx: float,
    dy: float,
    angle_deg: float = 0.0,
    scale: float = 1.025,
    pivot: Tuple[float, float] = (860.0, 576.0),
) -> np.ndarray:
    """Premultiplied affine transform anchored near bottom-right so breathing never exposes a cut bottom edge."""
    h, w = rgba.shape[:2]
    a = rgba[..., 3].astype(np.float32) / 255.0
    pm = rgba[..., :3].astype(np.float32) * a[..., None]

    # Inverse affine matrix (dst -> src) for PIL Image.transform(AFFINE)
    rad = math.radians(-angle_deg)
    ca, sa = math.cos(rad) / scale, math.sin(rad) / scale
    px, py = pivot
    # x_dst = px + scale * (cos*(x_src-px) - sin*(y_src-py)) + dx
    # Invert:
    tx = px - ca * (px + dx) + sa * (py + dy)
    ty = py - sa * (px + dx) - ca * (py + dy)
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
    """Screen/additive composite of glowing plasma/LEDs onto an RGBA canvas, updating alpha where needed."""
    out = base_rgba.astype(np.float32)
    ga = np.clip(glow_alpha, 0.0, 1.0)
    # Add light onto RGB
    out[..., :3] = np.clip(out[..., :3] + glow_rgb * ga[..., None], 0.0, 255.0)
    # Increase alpha smoothly so glowing plasma/flash outside the gun silhouette is visible!
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
    """Quantize a floating or uint8 overlay onto crisp chunky pixel blocks for MK3 arcade vibe."""
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
    n_rays: int = 16,
    n_sparks: int = 40,
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

    # 1. Outer shockwave ring / jagged plasma corona
    for k in range(n_rays):
        ang = base_ang + (k / float(n_rays)) * 2.0 * math.pi + rng.uniform(-0.14, 0.14)
        # Bias forward along barrel direction
        fwd_dot = max(0.0, math.cos(ang - base_ang))
        r_len = radius * (0.45 + 0.85 * (fwd_dot ** 1.4)) * rng.uniform(0.70, 1.25)
        w_ang = rng.uniform(0.06, 0.16)
        p0 = (cx, cy)
        p1 = (cx + math.cos(ang - w_ang) * r_len * 0.48, cy + math.sin(ang - w_ang) * r_len * 0.48)
        p2 = (cx + math.cos(ang) * r_len, cy + math.sin(ang) * r_len)
        p3 = (cx + math.cos(ang + w_ang) * r_len * 0.48, cy + math.sin(ang + w_ang) * r_len * 0.48)
        col = (40, 255, 75, int(min(255, 220 * intensity)))
        drw.polygon([p0, p1, p2, p3], fill=col)

    # 2. Inner electric-lime star core
    for k in range(max(8, n_rays // 2)):
        ang = base_ang + (k / float(max(8, n_rays // 2))) * 2.0 * math.pi + 0.2
        r_len = radius * 0.56 * rng.uniform(0.75, 1.15)
        p1 = (cx + math.cos(ang - 0.14) * r_len * 0.35, cy + math.sin(ang - 0.14) * r_len * 0.35)
        p2 = (cx + math.cos(ang) * r_len, cy + math.sin(ang) * r_len)
        p3 = (cx + math.cos(ang + 0.14) * r_len * 0.35, cy + math.sin(ang + 0.14) * r_len * 0.35)
        drw.polygon([(cx, cy), p1, p2, p3], fill=(175, 255, 165, int(min(255, 245 * intensity))))

    # 3. White-hot center orb
    cr = max(5.0, radius * 0.22)
    drw.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(235, 255, 235, 255))

    # 4. Chunky pixelated plasma droplets / sparks flying outward
    for _ in range(n_sparks):
        ang = base_ang + rng.normal(0.0, 0.72)
        dist = radius * rng.uniform(0.35, 1.45)
        sx = cx + math.cos(ang) * dist
        sy = cy + math.sin(ang) * dist
        sz = rng.integers(2, 6)
        tone = rng.choice([0, 1, 2])
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

    max_r = 16.0 + 48.0 * charge
    n_arms = 4
    for arm in range(n_arms):
        base_a = phase * 2.0 * math.pi + arm * (2.0 * math.pi / n_arms)
        pts = []
        steps = 12
        for s in range(steps):
            u = s / float(steps - 1)
            r = (1.0 - u) * max_r + 2.0
            a = base_a + u * 2.8
            px = cx + math.cos(a) * r
            py = cy + math.sin(a) * r * 0.88
            pts.append((px, py))
            sz = max(1.5, (1.0 - u * 0.5) * (2.2 + 2.8 * charge))
            g = int(200 + 55 * u)
            rc = int(35 + 165 * (u ** 2))
            al = int(min(255, (70 + 185 * charge) * (0.35 + 0.65 * u)))
            drw.rectangle((px - sz, py - sz, px + sz, py + sz), fill=(rc, g, rc, al))

    # Converging energy sparks pulled inward toward muzzle
    n_embers = int(6 + 18 * charge)
    for k in range(n_embers):
        a = rng.uniform(0, 2 * math.pi) + phase * 1.4
        r = rng.uniform(0.35, 1.35) * (22.0 + 58.0 * charge)
        ex = cx + math.cos(a) * r
        ey = cy + math.sin(a) * r
        sz = 2 if k % 3 else 3
        drw.rectangle((ex - sz, ey - sz, ex + sz, ey + sz), fill=(110, 255, 130, int(140 + 115 * charge)))

    # Bright core at barrel mouth
    cr = 4.0 + 13.0 * charge
    drw.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(140, 255, 150, int(130 + 125 * charge)))
    cr2 = max(2.0, cr * 0.52)
    drw.ellipse((cx - cr2, cy - cr2, cx + cr2, cy + cr2), fill=(235, 255, 235, int(160 + 95 * charge)))

    arr = _pixelate_block(np.asarray(im, dtype=np.uint8), block=2)
    return arr[..., :3].astype(np.float32), arr[..., 3].astype(np.float32) / 255.0


def _paint_smoke_plume(
    canvas_shape: Tuple[int, int],
    cx: float,
    cy: float,
    progress: float,
    seed: int,
    tint_green: float = 0.65,
) -> Tuple[np.ndarray, np.ndarray]:
    """Pixelated neon-mint/white cooling steam & smoke billowing from muzzle/vents."""
    h, w = canvas_shape
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    drw = ImageDraw.Draw(im)

    fade = max(0.0, 1.0 - 0.82 * progress)
    for k in range(20):
        drift_t = (progress * 1.15 + k * 0.04) % 1.0
        px = cx + BARREL_DIR[0] * (10.0 + 76.0 * progress) + rng.normal(0.0, 12.0 + 18.0 * progress)
        py = cy - (12.0 + 74.0 * progress) + rng.normal(0.0, 9.0 + 11.0 * progress)
        rad = 5.0 + 13.0 * drift_t + rng.uniform(0.0, 5.0)
        g = int(225 + 30 * tint_green)
        r = int(165 - 45 * tint_green)
        b = int(170 - 40 * tint_green)
        al = int(max(0, min(220, (175 * fade) * rng.uniform(0.60, 1.0))))
        drw.ellipse((px - rad, py - rad, px + rad, py + rad), fill=(r, g, b, al))

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
) -> None:
    """Paint glowing LEDs, heated barrel vents, and green housing spill at shifted gun landmarks."""
    # Side core LED & Top rear LED
    _draw_radial_glow(glow_rgb, glow_a, SIDE_LED_XY[0] + dx, SIDE_LED_XY[1] + dy, 22, 22, led_col, led_strength, power=1.8)
    _draw_radial_glow(glow_rgb, glow_a, SIDE_LED_XY[0] + dx, SIDE_LED_XY[1] + dy, 10, 10, (255, 255, 220), led_strength * 0.65, power=2.2)

    _draw_radial_glow(glow_rgb, glow_a, TOP_LED_XY[0] + dx, TOP_LED_XY[1] + dy, 24, 16, led_col, led_strength * 0.95, power=1.8)
    _draw_radial_glow(glow_rgb, glow_a, TOP_LED_XY[0] + dx, TOP_LED_XY[1] + dy, 11, 8, (255, 255, 220), led_strength * 0.60, power=2.2)

    # Heated vents along the barrel
    if vent_strength > 0.01:
        for vx, vy, rx, ry, _ in VENT_SLOTS:
            _draw_radial_glow(glow_rgb, glow_a, vx + dx, vy + dy, rx * 1.45, ry * 1.45, vent_col, vent_strength, power=1.7)
            _draw_radial_glow(glow_rgb, glow_a, vx + dx, vy + dy, rx * 0.7, ry * 0.7, (235, 255, 220), vent_strength * 0.55, power=2.2)

    # Ambient neon-green plasma bounce on the front yellow barrel & upper housing
    if core_green > 0.01:
        _draw_radial_glow(
            glow_rgb, glow_a,
            MUZZLE_XY[0] + dx + 38, MUZZLE_XY[1] + dy + 22,
            68, 48, (40, 255, 95), core_green * 0.55, power=1.6,
        )


def _crop_and_resize(rgba: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = CROP_BOX
    cropped = rgba[y0:y1, x0:x1]
    # Premultiplied resize via Pillow for crisp downscale without dark borders
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
    """Build the 1-frame flat sprite-card MD3 matching the 16:9 viewplane crop."""
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
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "v_cyrax.md3"
        md3lib.write(str(p), dict(name="v_cyrax", surfaces=[surf], nframes=1))
        return p.read_bytes()


def generate_viewmodel_frames(src_gun: Path = DEFAULT_SRC_GUN, out_dir: Path = TEX_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_rgb = np.asarray(Image.open(src_gun).convert("RGB"))
    keyed = key_white_gun(raw_rgb)
    h, w = keyed.shape[:2]

    written: list[Path] = []
    for idx in range(56):
        dx = 0.0
        dy = 0.0
        ang = 0.0
        scale = 1.028

        glow_rgb = np.zeros((h, w, 3), dtype=np.float32)
        glow_a = np.zeros((h, w), dtype=np.float32)
        extra_overlays: list[Tuple[np.ndarray, np.ndarray]] = []

        if 0 <= idx <= 7:
            # Idle: subtle robotic breathing + pulsing amber/green LEDs
            t = idx / 8.0
            dx = 1.2 * math.cos(2.0 * math.pi * t)
            dy = 2.4 * math.sin(2.0 * math.pi * t)
            ang = 0.25 * math.sin(2.0 * math.pi * t)
            pulse = 0.5 + 0.5 * math.sin(2.0 * math.pi * t)
            # Blend warm amber -> cyber green
            led_col = (
                255.0 * (1.0 - 0.72 * pulse),
                150.0 + 105.0 * pulse,
                20.0 + 85.0 * pulse,
            )
            _apply_vents_and_leds(glow_rgb, glow_a, dx, dy, led_col, 0.45 + 0.35 * pulse, (0, 0, 0), 0.0, 0.08 * pulse)

        elif 8 <= idx <= 31:
            # Charge buildup (24f): hot orange -> neon green vents, core glow, shake, swirling plasma
            p = (idx - 8) / 23.0
            rng = np.random.default_rng(1000 + idx)
            shake = 0.5 + 4.8 * (p ** 1.6)
            dx = 7.0 * p + float(rng.uniform(-shake, shake))
            dy = 4.0 * p + float(rng.uniform(-shake * 0.85, shake * 0.85))
            ang = -1.2 * p + float(rng.uniform(-0.7, 0.7)) * p

            # Heated vents: hot orange (p=0..0.45) -> blazing neon green (p=0.45..1.0)
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
                vent_col, 0.52 + 0.90 * p,
                0.22 + 0.88 * p,
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
            # Fire blast + recoil (12f)
            if idx <= 36:
                # 32..36: crazy pixelated neon-green muzzle flash + kickback ramp
                fp = (idx - 32) / 4.0
                dx = 16.0 + 16.0 * fp
                dy = 9.0 + 10.0 * fp
                ang = -2.2 - 2.3 * fp
                flash_str = [1.15, 1.25, 1.05, 0.85, 0.62][idx - 32]
                flash_rad = [148.0, 175.0, 152.0, 124.0, 96.0][idx - 32]
                _apply_vents_and_leds(
                    glow_rgb, glow_a, dx, dy,
                    (90, 255, 120), 1.15 * flash_str,
                    (85, 255, 105), 1.05 * flash_str,
                    1.15 * flash_str,
                )
                # Broad green muzzle light wash over front of gun
                _draw_radial_glow(
                    glow_rgb, glow_a,
                    MUZZLE_XY[0] + dx - 20, MUZZLE_XY[1] + dy - 10,
                    130, 95, (75, 255, 105), 0.72 * flash_str, power=1.5,
                )
                fb_rgb, fb_a = _paint_pixel_burst(
                    (h, w),
                    MUZZLE_XY[0] + dx - 18.0,
                    MUZZLE_XY[1] + dy - 8.0,
                    radius=flash_rad,
                    seed=3200 + idx,
                    n_rays=18,
                    n_sparks=52,
                    block=3,
                    intensity=flash_str,
                )
                extra_overlays.append((fb_rgb, fb_a))
            else:
                # 37..43: heavy kickback recoil -> smooth mechanical return-to-battery + barrel smoke
                rp = (idx - 37) / 6.0
                ease = 1.0 - (3.0 * rp * rp - 2.0 * rp * rp * rp)
                dx = 30.0 * ease
                dy = 18.0 * ease
                ang = -4.5 * ease
                cool = 1.0 - rp
                _apply_vents_and_leds(
                    glow_rgb, glow_a, dx, dy,
                    (255.0 * rp + 60.0 * cool, 160.0 * rp + 255.0 * cool, 30.0 + 70.0 * cool),
                    0.50 + 0.45 * cool,
                    (255.0 * rp + 75.0 * cool, 130.0 * rp + 255.0 * cool, 25.0 + 80.0 * cool),
                    0.75 * cool,
                    0.35 * cool,
                )
                sm_rgb, sm_a = _paint_smoke_plume(
                    (h, w),
                    MUZZLE_XY[0] + dx - 12.0,
                    MUZZLE_XY[1] + dy - 12.0,
                    progress=0.12 + 0.85 * rp,
                    seed=3700 + idx,
                    tint_green=0.70 * cool + 0.25,
                )
                extra_overlays.append((sm_rgb, sm_a))

        elif 44 <= idx <= 49:
            # Draw / raise pop-up (6f)
            dp = (idx - 44) / 5.0
            rise_offsets = [155.0, 92.0, 44.0, 14.0, -5.0, 0.0]
            rot_offsets = [-9.0, -5.5, -2.5, -0.8, 0.4, 0.0]
            dy = rise_offsets[idx - 44]
            dx = dy * 0.28
            ang = rot_offsets[idx - 44]
            boot_flicker = 1.0 if idx in (46, 48, 49) else 0.35
            led_col = (55, 255, 95) if idx >= 47 else (255, 165, 25)
            _apply_vents_and_leds(glow_rgb, glow_a, dx, dy, led_col, 0.65 * boot_flicker, (0, 0, 0), 0.0, 0.12 * dp)

        else:
            # 50..55 (6f): Cooldown / venting state
            vp = (idx - 50) / 5.0
            cool = 1.0 - vp
            dx = 3.0 * cool * math.sin(idx * 2.2)
            dy = 4.0 * cool
            ang = -0.8 * cool
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
            # Venting steam from both side vents and muzzle
            for vx, vy in ((612.0, 360.0), (690.0, 332.0), (566.0, 322.0)):
                sm_rgb, sm_a = _paint_smoke_plume(
                    (h, w),
                    vx + dx,
                    vy + dy,
                    progress=0.15 + 0.80 * vp,
                    seed=5000 + idx * 17 + int(vx),
                    tint_green=0.55 * cool + 0.20,
                )
                extra_overlays.append((sm_rgb, sm_a))

        frame_rgba = _shift_gun_rgba(keyed, dx=dx, dy=dy, angle_deg=ang, scale=scale)
        # Mask vent/LED glow slightly on pure exterior so gun silhouette stays crisp, while allowing plasma/smoke outside
        gun_mask = np.clip(frame_rgba[..., 3].astype(np.float32) / 255.0 + 0.15, 0.0, 1.0)
        # Apply glow inside gun + near muzzle
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
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC_GUN, help="Source gun JPG/PNG")
    ap.add_argument("--out-dir", type=Path, default=TEX_DIR, help="Output directory for 56 PNG frames")
    args = ap.parse_args()
    paths = generate_viewmodel_frames(args.src, args.out_dir)
    print(f"Generated {len(paths)} viewmodel frames in {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
