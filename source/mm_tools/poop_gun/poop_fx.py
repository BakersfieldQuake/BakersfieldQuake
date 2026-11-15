"""Reusable comedy FX generators, premultiplied compositors, and extra head caching
for the Poop Gun 4-concept prototype suite (`source/mm_tools/poop_gun/`).
"""
from __future__ import annotations

import math
import os
from typing import Dict, Iterable, List, Sequence, Tuple

import cv2
import numpy as np
from PIL import Image

from poop_core import (
    WORK_DIR,
    from_premul,
    key_white_studio_plate,
    resize_premul,
    to_premul,
)

EXTRA_HEAD_SOURCES: Dict[str, Tuple[str, Tuple[float, float, float, float]]] = {
    "head_turban_grin": (
        r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841\head_turban_grin_1794663299689.jpg",
        # Protect turban white stripes, eyes, and wide teeth grin
        (0.24, 0.20, 0.76, 0.80),
    ),
    "head_oiled_yell": (
        r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841\head_oiled_yell_1794663316181.jpg",
        # Protect sclera and screaming teeth
        (0.26, 0.28, 0.78, 0.82),
    ),
    "head_turban_yell": (
        r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841\head_turban_yell_1794663574913.jpg",
        # Protect turban white band, bloodshot eyes, and screaming teeth
        (0.20, 0.22, 0.78, 0.86),
    ),
}

ENEMY_SHOOTER_SRC = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\bfacaf1b-4d8e-4a45-8a50-ab05a5d68841\enemy_shooter_base_1794663595737.jpg",
    (0.28, 0.06, 0.72, 0.90),
)


def alpha_over(
    dst_rgba: np.ndarray,
    src_rgba: np.ndarray,
    x: int | float = 0,
    y: int | float = 0,
    opacity: float = 1.0,
) -> np.ndarray:
    """Composite `src_rgba` onto a copy of `dst_rgba` at top-left `(x, y)` using
    premultiplied alpha-over blending with full bounds clipping.
    """
    out = dst_rgba.copy()
    if opacity <= 0.0:
        return out
    dh, dw = out.shape[:2]
    sh, sw = src_rgba.shape[:2]
    ix = int(round(x))
    iy = int(round(y))

    x0 = max(0, ix)
    y0 = max(0, iy)
    x1 = min(dw, ix + sw)
    y1 = min(dh, iy + sh)
    if x1 <= x0 or y1 <= y0:
        return out

    sx0 = x0 - ix
    sy0 = y0 - iy
    sx1 = sx0 + (x1 - x0)
    sy1 = sy0 + (y1 - y0)

    src_patch = src_rgba[sy0:sy1, sx0:sx1]
    if float(opacity) < 0.999:
        src_patch = src_patch.copy()
        src_patch[..., 3] = np.clip(
            np.round(src_patch[..., 3].astype(np.float32) * float(opacity)), 0, 255
        ).astype(np.uint8)

    src_pm = to_premul(src_patch)
    dst_pm = to_premul(out[y0:y1, x0:x1])
    src_a = src_pm[..., 3:4] / 255.0
    comp_pm = src_pm + dst_pm * (1.0 - src_a)
    out[y0:y1, x0:x1] = from_premul(comp_pm)
    return out


def warp_rgba(
    src_rgba: np.ndarray,
    angle_deg: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
    dx: float = 0.0,
    dy: float = 0.0,
    pivot: Tuple[float, float] | None = None,
    out_hw: Tuple[int, int] | None = None,
) -> np.ndarray:
    """Premultiplied affine warp around `pivot` (in `src_rgba` xy coordinates).

    Applies scaling `(sx, sy)`, rotation `angle_deg` (OpenCV CCW convention), and
    translation `(dx, dy)` such that `pivot` lands at `(pivot[0] + dx, pivot[1] + dy)`
    inside `out_hw = (out_h, out_w)`.
    """
    sh, sw = src_rgba.shape[:2]
    if pivot is None:
        px, py = sw * 0.5, sh * 0.5
    else:
        px, py = float(pivot[0]), float(pivot[1])

    if out_hw is None:
        oh, ow = sh, sw
    else:
        oh, ow = int(out_hw[0]), int(out_hw[1])

    rad = math.radians(float(angle_deg))
    c = math.cos(rad)
    s = math.sin(rad)

    # M = T(px + dx, py + dy) @ R_cv(angle_deg) @ S(sx, sy) @ T(-px, -py)
    a00 = c * float(sx)
    a01 = s * float(sy)
    a10 = -s * float(sx)
    a11 = c * float(sy)
    tx = (px + float(dx)) - (a00 * px + a01 * py)
    ty = (py + float(dy)) - (a10 * px + a11 * py)
    M = np.array([[a00, a01, tx], [a10, a11, ty]], dtype=np.float32)

    pm = to_premul(src_rgba)
    warped = cv2.warpAffine(
        pm,
        M,
        (ow, oh),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )
    return from_premul(warped)


def _draw_tricolor_flat(fw: int, fh: int) -> np.ndarray:
    """Draw a crisp 2x-friendly flat tricolor cloth texture with 24-spoked navy wheel."""
    tex = np.zeros((fh, fw, 4), dtype=np.uint8)
    tex[..., 3] = 255

    y1 = fh // 3
    y2 = (2 * fh) // 3
    # Saffron (#FF9933), White (#FFFFFF), Green (#138808)
    tex[:y1, :, :3] = (255, 153, 51)
    tex[y1:y2, :, :3] = (255, 255, 255)
    tex[y2:, :, :3] = (19, 136, 8)

    # Subtle woven cloth texture & stitched border hem
    yy, xx = np.mgrid[0:fh, 0:fw]
    weave = (((xx // 2 + yy // 2) % 2) * 2 - 1).astype(np.float32) * 3.0
    rgb_f = tex[..., :3].astype(np.float32) + weave[..., None]
    hem = max(2, min(fw, fh) // 36)
    edge_mask = (xx < hem) | (xx >= fw - hem) | (yy < hem) | (yy >= fh - hem)
    rgb_f[edge_mask] *= 0.90
    tex[..., :3] = np.clip(np.round(rgb_f), 0, 255).astype(np.uint8)

    # Centered navy (#000080) 24-spoked wheel on the white band
    cx = int(round(fw * 0.5))
    cy = (y1 + y2) // 2
    band_h = max(6, y2 - y1)
    radius = max(4, int(round(band_h * 0.39)))
    navy = (0, 0, 128, 255)

    ring_t = max(2, int(round(radius * 0.14)))
    spoke_t = max(1, int(round(radius * 0.065)))
    hub_r = max(2, int(round(radius * 0.19)))

    # cv2 draws in-place on contiguous uint8 arrays
    cv2.circle(tex, (cx, cy), radius, navy, thickness=ring_t, lineType=cv2.LINE_AA)
    cv2.circle(tex, (cx, cy), hub_r, navy, thickness=-1, lineType=cv2.LINE_AA)

    inner_r = max(1.0, radius - ring_t * 0.5)
    for k in range(24):
        ang = (2.0 * math.pi * k) / 24.0
        x_end = int(round(cx + math.cos(ang) * inner_r))
        y_end = int(round(cy + math.sin(ang) * inner_r))
        cv2.line(tex, (cx, cy), (x_end, y_end), navy, thickness=spoke_t, lineType=cv2.LINE_AA)

        # Tiny scalloped node between spokes along the inner rim
        ang_mid = (2.0 * math.pi * (k + 0.5)) / 24.0
        nx = int(round(cx + math.cos(ang_mid) * (inner_r - ring_t * 0.35)))
        ny = int(round(cy + math.sin(ang_mid) * (inner_r - ring_t * 0.35)))
        cv2.circle(tex, (nx, ny), max(1, spoke_t), navy, thickness=-1, lineType=cv2.LINE_AA)

    return tex


def render_tricolor_flag(
    w: int,
    h: int,
    phase: float,
    pole_left: bool = True,
    amp: float = 1.0,
) -> np.ndarray:
    """Render an animated waving saffron/white/green tricolor flag with centered
    24-spoked navy wheel, cloth fold shading, and travelling sine-wave ripple.

    Args:
        w, h: Output RGBA dimensions.
        phase: Wave phase in `[0, 2*pi)`.
        pole_left: True if the pole anchors the left edge; False if right edge.
        amp: Ripple amplitude multiplier (1.0 = lively wind wave).
    """
    ss = 2
    sw, sh = max(16, int(w) * ss), max(16, int(h) * ss)

    # Vertical & horizontal padding inside canvas so full wave never clips
    pad_y = max(4, int(round(sh * 0.19)))
    pad_x = max(2, int(round(sw * 0.04)))
    fw = max(8, sw - 2 * pad_x)
    fh = max(12, sh - 2 * pad_y)

    flat = _draw_tricolor_flat(fw, fh)
    padded = np.zeros((sh, sw, 4), dtype=np.uint8)
    padded[pad_y:pad_y + fh, pad_x:pad_x + fw] = flat

    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    if pole_left:
        u = np.clip((xx - pad_x) / float(fw), 0.0, 1.0)
    else:
        u = np.clip(((pad_x + fw) - xx) / float(fw), 0.0, 1.0)
    v = np.clip((yy - pad_y) / float(fh), 0.0, 1.0)

    # Pinned at pole (u=0 -> env=0), whipping vigorously toward free tip (u=1)
    env = np.power(u, 0.78)
    k1 = 2.0 * math.pi * 1.45
    k2 = 2.0 * math.pi * 2.80

    # Travelling ripple wave + secondary flutter + slight downward drape
    w1 = np.sin(k1 * u - float(phase) + 0.22 * (v - 0.5))
    w2 = np.sin(k2 * u - 2.0 * float(phase) + 0.65 * v)
    wave_y = float(amp) * (0.115 * sh * env * w1 + 0.032 * sh * env * u * w2)
    drape_y = 0.025 * sh * env * float(amp)
    disp_y = wave_y + drape_y

    # Subtle horizontal foreshortening when cloth folds curve away from viewer
    fold_compress = 0.042 * sw * env * float(amp) * (0.5 + 0.5 * np.cos(2.0 * k1 * u - 2.0 * float(phase)))
    disp_x = -fold_compress if pole_left else fold_compress

    map_x = (xx - disp_x).astype(np.float32)
    map_y = (yy - disp_y).astype(np.float32)

    pm = to_premul(padded)
    warped_pm = cv2.remap(
        pm,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )
    warped = from_premul(warped_pm)

    # Surface-slope cloth fold shading (crests bright, troughs shadowed)
    dz_du = env * (
        k1 * np.cos(k1 * u - float(phase) + 0.22 * (v - 0.5))
        + 0.35 * k2 * u * np.cos(k2 * u - 2.0 * float(phase) + 0.65 * v)
    )
    # Normalize derivative into readable contrast range
    slope = np.tanh(dz_du * 0.16 * max(0.35, float(amp)))
    shade = np.clip(1.0 + 0.30 * slope - 0.06 * np.abs(w2) * env, 0.52, 1.26)

    out_f = warped.astype(np.float32)
    fg = out_f[..., 3] > 2.0
    out_f[fg, :3] *= shade[fg, None]
    # Add soft cloth sheen on forward-facing crests
    crest = np.clip(slope, 0.0, 1.0) ** 2 * 18.0
    out_f[fg, :3] += crest[fg, None]
    warped[..., :3] = np.clip(np.round(out_f[..., :3]), 0, 255).astype(np.uint8)

    return resize_premul(warped, (int(w), int(h)))


def _draw_single_fly(scale: float, wing_flap: float) -> np.ndarray:
    """Draw a glossy iridescent fly facing +X (rightward) in a local RGBA patch."""
    ss = 2
    s = max(0.35, float(scale)) * ss
    pw = max(16, int(math.ceil(24 * s)))
    ph = max(16, int(math.ceil(22 * s)))
    if pw % 2:
        pw += 1
    if ph % 2:
        ph += 1
    patch = np.zeros((ph, pw, 4), dtype=np.uint8)
    cx, cy = pw * 0.5, ph * 0.5

    # 1. Tiny dark legs
    leg_col = (24, 20, 18, 220)
    lt = max(1, int(round(0.65 * s)))
    for side in (-1.0, 1.0):
        for lx_off, ly_out in [(-1.5, 4.2), (0.8, 4.8), (2.4, 3.8)]:
            p0 = (int(round(cx + lx_off * s)), int(round(cy + side * 1.2 * s)))
            p1 = (int(round(cx + (lx_off - 0.8) * s)), int(round(cy + side * ly_out * s)))
            cv2.line(patch, p0, p1, leg_col, thickness=lt, lineType=cv2.LINE_AA)

    # 2. Glossy iridescent abdomen (back/left) + thorax (middle)
    abd_c = (int(round(cx - 2.6 * s)), int(round(cy)))
    abd_ax = (max(2, int(round(3.6 * s))), max(2, int(round(2.3 * s))))
    cv2.ellipse(patch, abd_c, abd_ax, 0.0, 0, 360, (22, 54, 44, 255), -1, cv2.LINE_AA)
    # Metallic green-teal sheen stripe + bright highlight dot
    cv2.ellipse(
        patch,
        (int(round(cx - 2.8 * s)), int(round(cy - 0.5 * s))),
        (max(1, int(round(2.4 * s))), max(1, int(round(1.1 * s)))),
        0.0,
        0,
        360,
        (56, 138, 102, 255),
        -1,
        cv2.LINE_AA,
    )
    cv2.circle(
        patch,
        (int(round(cx - 3.3 * s)), int(round(cy - 0.9 * s))),
        max(1, int(round(0.75 * s))),
        (170, 245, 200, 255),
        -1,
        cv2.LINE_AA,
    )

    thx_c = (int(round(cx + 1.2 * s)), int(round(cy)))
    cv2.ellipse(
        patch,
        thx_c,
        (max(2, int(round(2.0 * s))), max(2, int(round(1.9 * s)))),
        0.0,
        0,
        360,
        (30, 28, 34, 255),
        -1,
        cv2.LINE_AA,
    )

    # 3. Head + bright crimson compound eyes (front/right)
    hd_c = (int(round(cx + 3.4 * s)), int(round(cy)))
    cv2.circle(patch, hd_c, max(1, int(round(1.5 * s))), (24, 22, 24, 255), -1, cv2.LINE_AA)
    eye_r = max(1, int(round(1.05 * s)))
    for side in (-1.0, 1.0):
        ec = (int(round(cx + 3.9 * s)), int(round(cy + side * 1.15 * s)))
        cv2.circle(patch, ec, eye_r, (220, 28, 34, 255), -1, cv2.LINE_AA)
        cv2.circle(
            patch,
            (int(round(ec[0] + 0.3 * s)), int(round(ec[1] - 0.3 * s))),
            max(1, int(round(0.35 * s))),
            (255, 215, 215, 255),
            -1,
            cv2.LINE_AA,
        )

    # 4. Translucent fluttering wings layered on top via premul blend
    wing_layer = np.zeros_like(patch)
    # wing_flap in [-1, 1] -> sweep angle between 24 and 66 degrees
    sweep = 43.0 + 22.0 * float(wing_flap)
    w_len = max(3, int(round(5.4 * s)))
    w_wid = max(2, int(round(2.1 * s)))
    for side in (-1.0, 1.0):
        ang = side * (180.0 - sweep)
        rad = math.radians(ang)
        wx = int(round(cx + 0.7 * s + math.cos(rad) * (w_len * 0.76)))
        wy = int(round(cy + math.sin(rad) * (w_len * 0.76)))
        cv2.ellipse(
            wing_layer,
            (wx, wy),
            (w_len, w_wid),
            ang,
            0,
            360,
            (235, 248, 255, 175),
            -1,
            cv2.LINE_AA,
        )
        cv2.ellipse(
            wing_layer,
            (wx, wy),
            (w_len, w_wid),
            ang,
            0,
            360,
            (95, 125, 150, 210),
            max(1, int(round(0.65 * s))),
            cv2.LINE_AA,
        )

    patch = alpha_over(patch, wing_layer, 0, 0)
    return resize_premul(patch, (pw // ss, ph // ss))


def render_fly_swarm(
    canvas_rgba: np.ndarray,
    centers: Sequence[Tuple[float, float]] | Tuple[float, float],
    t_norm: float,
    n_flies: int = 12,
    scale: float = 1.0,
    calm: bool = False,
    orbit_rx: Tuple[float, float] | None = None,
    orbit_ry: Tuple[float, float] | None = None,
) -> np.ndarray:
    """Draw animated glossy flies with red eyes and fluttering translucent wings
    orbiting `centers` along continuous periodic paths.

    Args:
        canvas_rgba: Destination RGBA uint8 image (not mutated).
        centers: List of `(cx, cy)` orbit centers (or single `(cx, cy)` tuple).
        t_norm: Normalized animation time in `[0, 1)` (loops seamlessly).
        n_flies: Number of flies to draw.
        scale: Base size & orbit radius multiplier.
        calm: When True, flies cruise in a slow, smooth tilted orbit with no jitter.
        orbit_rx: Optional `(min_rx, max_rx)` horizontal orbit radius bounds.
        orbit_ry: Optional `(min_ry, max_ry)` vertical orbit radius bounds.
    """
    out = canvas_rgba.copy()
    if n_flies <= 0 or not centers:
        return out

    if isinstance(centers[0], (int, float)):
        center_list = [(float(centers[0]), float(centers[1]))]
    else:
        center_list = [(float(c[0]), float(c[1])) for c in centers]

    tau = 2.0 * math.pi
    t = float(t_norm) % 1.0
    dt = 0.004

    rx0, rx1 = orbit_rx if orbit_rx is not None else (16.0 * float(scale), 44.0 * float(scale))
    ry0, ry1 = orbit_ry if orbit_ry is not None else (10.0 * float(scale), 28.0 * float(scale))

    flies_draw: List[Tuple[float, float, float, float, float, float]] = []
    for i in range(int(n_flies)):
        cx, cy = center_list[i % len(center_list)]
        # Deterministic quasi-random harmonics per fly index
        h1 = ((i * 0.61803398875) % 1.0)
        h2 = ((i * 0.38196601125 + 0.17) % 1.0)
        h3 = ((i * 0.75487766625 + 0.43) % 1.0)
        h4 = ((i * 0.56984029099 + 0.71) % 1.0)

        rx = rx0 + (rx1 - rx0) * h1
        ry = ry0 + (ry1 - ry0) * h2
        if calm:
            dir_s = -1.0 if (i % 2 == 1) else 1.0
            px = tau * (i / float(max(1, n_flies))) + 0.4 * h3
            tilt_ang = (h4 - 0.5) * 0.85

            def _pos(tt: float) -> Tuple[float, float, float]:
                ang = dir_s * tau * tt + px
                lx = rx * math.cos(ang)
                ly = ry * math.sin(ang)
                x = cx + lx * math.cos(tilt_ang) - ly * math.sin(tilt_ang)
                y = cy + lx * math.sin(tilt_ang) + ly * math.cos(tilt_ang) + 3.0 * math.sin(tau * tt + px)
                z = math.sin(ang)
                return x, y, z
        else:
            fx = 1 + (i % 3)
            fy = 2 + ((i + 1) % 3)
            px = tau * h3
            py = tau * h4
            j_amp = 4.5 * float(scale)

            def _pos(tt: float) -> Tuple[float, float, float]:
                ang_x = tau * fx * tt + px
                ang_y = tau * fy * tt + py
                x = cx + rx * math.sin(ang_x) + j_amp * math.sin(tau * 5 * tt + py)
                y = cy + ry * math.sin(ang_y) + j_amp * math.cos(tau * 4 * tt + px)
                z = math.cos(ang_x + 0.7)
                return x, y, z

        x0, y0, z0 = _pos(t)
        x1, y1, _ = _pos(t + dt)
        vx, vy = x1 - x0, y1 - y0
        heading_deg = -math.degrees(math.atan2(vy, vx)) if (vx * vx + vy * vy) > 1e-6 else 0.0
        fly_sc = float(scale) * (0.84 + 0.22 * z0)
        flap = math.sin(tau * (8.0 + (i % 3) if calm else (14.0 + (i % 5))) * t + i * 1.9)
        flies_draw.append((z0, x0, y0, heading_deg, fly_sc, flap))

    # Draw far-to-near for natural 3D orbiting depth
    flies_draw.sort(key=lambda item: item[0])
    for _, x, y, ang_deg, fly_sc, flap in flies_draw:
        sprite = _draw_single_fly(fly_sc, flap)
        sh, sw = sprite.shape[:2]
        pad = int(math.ceil(max(sw, sh) * 0.6))
        oh, ow = sh + 2 * pad, sw + 2 * pad
        rot = warp_rgba(
            sprite,
            angle_deg=ang_deg,
            sx=1.0,
            sy=1.0,
            dx=pad,
            dy=pad,
            pivot=(sw * 0.5, sh * 0.5),
            out_hw=(oh, ow),
        )
        out = alpha_over(out, rot, x - ow * 0.5, y - oh * 0.5)

    return out


def _shade_mud_blob(
    mask_sdf: np.ndarray,
    rng: np.random.Generator,
    base_rgb: Tuple[int, int, int],
    dark_rgb: Tuple[int, int, int],
    hi_rgb: Tuple[int, int, int],
) -> np.ndarray:
    """Shade a signed-distance mud shape into a glossy wet 3D comic mud RGBA."""
    h, w = mask_sdf.shape
    alpha = np.clip((mask_sdf + 0.8) / 1.6, 0.0, 1.0)

    # Smooth heightfield inside blob using Gaussian-smoothed distance to avoid creases
    raw_depth = np.clip(mask_sdf, 0.0, 26.0)
    smooth_depth = cv2.GaussianBlur(raw_depth, (0, 0), 2.6)
    bump = cv2.GaussianBlur(rng.normal(0.0, 1.0, (h, w)).astype(np.float32), (0, 0), 2.4)
    height = np.sqrt(np.clip(smooth_depth / 18.0, 0.0, 1.4)) * 7.5 + bump * 1.1
    gy, gx = np.gradient(height)
    nx, ny, nz = -gx, -gy, np.ones_like(gx) * 1.45
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    nx /= norm
    ny /= norm
    nz /= norm

    # Upper-left key light
    lx, ly, lz = -0.52, -0.58, 0.63
    diff = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)
    hx, hy, hz = -0.30, -0.35, 0.89
    spec = np.power(np.clip(nx * hx + ny * hy + nz * hz, 0.0, 1.0), 18.0)

    # Organic chunky flecks & darker mud swirls
    noise = rng.normal(0.0, 1.0, (h, w)).astype(np.float32)
    chunk_n = cv2.GaussianBlur(noise, (0, 0), 1.8)

    b_arr = np.array(base_rgb, dtype=np.float32)
    d_arr = np.array(dark_rgb, dtype=np.float32)
    h_arr = np.array(hi_rgb, dtype=np.float32)

    t_lit = np.clip(0.22 + 0.88 * diff + 0.18 * chunk_n, 0.0, 1.0)[..., None]
    rgb = d_arr * (1.0 - t_lit) + b_arr * t_lit
    # Highlight + wet glossy shine
    rgb = rgb + (h_arr - rgb) * np.clip(spec * 1.2, 0.0, 0.95)[..., None]
    # Dark wet rim along silhouette edge
    rim = np.exp(-np.clip(mask_sdf, 0.0, 10.0) * 0.55)
    rgb = rgb * (1.0 - 0.42 * rim[..., None]) + d_arr * (0.42 * rim[..., None])

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    out[out[..., 3] < 4] = 0
    return out


def render_mud_splatter_sprites(out_dir: str) -> Dict[str, np.ndarray]:
    """Generate crisp glossy mud globs (`mud_glob_00..03.png`) and splatter decals
    (`splat_00..03.png`) in `out_dir`, returning `{name: rgba}`.
    """
    os.makedirs(out_dir, exist_ok=True)
    sprites: Dict[str, np.ndarray] = {}

    # 1. Chunky lumpy mud globs (96x96)
    for k in range(4):
        rng = np.random.default_rng(1000 + k * 77)
        sz = 96
        yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32)
        cx, cy = sz * 0.5, sz * 0.5
        field = np.zeros((sz, sz), dtype=np.float32)
        # Main asymmetric lumpy body + protruding chunks
        n_lobes = 9 + k * 2
        for i in range(n_lobes):
            ang = 2.0 * math.pi * i / n_lobes + rng.uniform(-0.45, 0.45)
            dist = rng.uniform(8.0, 22.0) if i > 0 else rng.uniform(0.0, 4.0)
            lx = cx + math.cos(ang) * dist
            ly = cy + math.sin(ang) * dist
            rx = rng.uniform(8.0, 17.0) if i > 0 else rng.uniform(14.0, 19.0)
            ry = rng.uniform(7.0, 15.0) if i > 0 else rng.uniform(12.0, 17.0)
            d2 = ((xx - lx) / rx) ** 2 + ((yy - ly) / ry) ** 2
            field += np.exp(-1.55 * d2)
        # Micro-droplet satellite crumbs around the glob
        for _ in range(4):
            ang = rng.uniform(0.0, 2.0 * math.pi)
            dist = rng.uniform(26.0, 36.0)
            lx = cx + math.cos(ang) * dist
            ly = cy + math.sin(ang) * dist
            r = rng.uniform(3.0, 5.5)
            field += 0.95 * np.exp(-1.8 * (((xx - lx) ** 2 + (yy - ly) ** 2) / (r * r)))

        sdf = (field - 0.78) * 20.0
        rgba = _shade_mud_blob(
            sdf,
            rng,
            base_rgb=(106, 64, 26),
            dark_rgb=(46, 24, 10),
            hi_rgb=(224, 198, 146),
        )
        name = f"mud_glob_{k:02d}"
        Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, f"{name}.png"), optimize=True)
        sprites[name] = rgba

    # 2. Organic metaball-puddle mud splatter decals (192x192)
    for k in range(4):
        rng = np.random.default_rng(2000 + k * 91)
        sz = 192
        yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32)
        cx, cy = sz * 0.5, sz * 0.5
        field = np.zeros((sz, sz), dtype=np.float32)

        # Irregular multi-lobed puddle core (no star crease!)
        for i in range(9):
            ang = 2.0 * math.pi * i / 9.0 + rng.uniform(-0.4, 0.4)
            dist = rng.uniform(4.0, 24.0) if i > 0 else 0.0
            lx = cx + math.cos(ang) * dist
            ly = cy + math.sin(ang) * dist
            r = rng.uniform(18.0, 32.0) if i > 0 else 32.0
            field += np.exp(-1.45 * (((xx - lx) ** 2 + (yy - ly) ** 2) / (r * r)))

        # Radiating mud splash arms built from tapered metaball beads
        n_arms = 10 + k * 2
        for i in range(n_arms):
            ang = 2.0 * math.pi * i / n_arms + rng.uniform(-0.22, 0.22)
            arm_len = rng.uniform(44.0, 82.0)
            n_beads = 5
            for b in range(n_beads):
                t = (b + 1) / float(n_beads)
                dist = 20.0 + t * (arm_len - 20.0)
                wobble = rng.uniform(-0.08, 0.08) * t
                bx = cx + math.cos(ang + wobble) * dist
                by = cy + math.sin(ang + wobble) * dist
                br = (1.0 - 0.65 * t) * rng.uniform(8.5, 13.5)
                field += 0.85 * np.exp(-1.6 * (((xx - bx) ** 2 + (yy - by) ** 2) / (br * br)))
            # Tip splash droplet just past the arm
            if rng.random() < 0.85:
                td = arm_len + rng.uniform(6.0, 14.0)
                tx = cx + math.cos(ang) * td
                ty = cy + math.sin(ang) * td
                tr = rng.uniform(3.0, 6.2)
                field += 0.92 * np.exp(-1.7 * (((xx - tx) ** 2 + (yy - ty) ** 2) / (tr * tr)))

        # Extra scattered micro-droplets
        for _ in range(14):
            d_ang = rng.uniform(0.0, 2.0 * math.pi)
            d_dist = rng.uniform(48.0, 88.0)
            dr = rng.uniform(2.5, 5.5)
            mx = cx + math.cos(d_ang) * d_dist
            my = cy + math.sin(d_ang) * d_dist
            field += 0.92 * np.exp(-1.7 * (((xx - mx) ** 2 + (yy - my) ** 2) / (dr * dr)))

        sdf = (field - 0.72) * 18.0
        rgba = _shade_mud_blob(
            sdf,
            rng,
            base_rgb=(98, 58, 24),
            dark_rgb=(44, 23, 9),
            hi_rgb=(215, 186, 136),
        )
        name = f"splat_{k:02d}"
        Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, f"{name}.png"), optimize=True)
        sprites[name] = rgba

    return sprites


def render_mud_mist_sprites(out_dir: str) -> Dict[str, np.ndarray]:
    """Generate billowing brown & sickly-green stink-mist puffs (`mist_00..05.png`)
    in `out_dir`, returning `{name: rgba}`.
    """
    os.makedirs(out_dir, exist_ok=True)
    sprites: Dict[str, np.ndarray] = {}
    sz = 160
    yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32)
    cx, cy = sz * 0.5, sz * 0.5

    palettes = [
        ((108, 72, 32), (56, 34, 14), (156, 122, 68)),   # earthy brown puff
        ((122, 120, 40), (62, 58, 18), (176, 186, 70)),  # toxic fart green-brown
        ((94, 58, 26), (46, 28, 10), (144, 104, 54)),    # dark mud smoke
        ((110, 124, 42), (54, 62, 18), (168, 190, 76)),  # stink cloud
        ((114, 78, 36), (60, 38, 16), (162, 128, 74)),   # dusty brown
        ((126, 132, 46), (64, 66, 20), (182, 198, 82)),  # pungent sulfur-fart
    ]

    for k in range(6):
        rng = np.random.default_rng(3000 + k * 113)
        density = np.zeros((sz, sz), dtype=np.float32)
        # Asymmetric billowing lobes (clustered puffs + smaller outer curls)
        n_puffs = 16
        for i in range(n_puffs):
            ang = 2.0 * math.pi * i / n_puffs + rng.uniform(-0.35, 0.35)
            dist = rng.uniform(14.0, 38.0) if i > 2 else rng.uniform(0.0, 12.0)
            px = cx + math.cos(ang) * dist
            py = cy + math.sin(ang) * dist
            sig = rng.uniform(10.0, 20.0) if i > 2 else rng.uniform(18.0, 25.0)
            w_p = rng.uniform(0.55, 1.05)
            density += w_p * np.exp(-0.5 * (((xx - px) ** 2 + (yy - py) ** 2) / (sig * sig)))

        # Crisp wispy cloud turbulence + soft feathered outer curls
        n1 = cv2.GaussianBlur(rng.normal(0.0, 1.0, (sz, sz)).astype(np.float32), (0, 0), 5.0)
        n2 = cv2.GaussianBlur(rng.normal(0.0, 1.0, (sz, sz)).astype(np.float32), (0, 0), 2.0)
        turb = 1.0 + 0.50 * np.tanh(n1 * 2.8) + 0.25 * np.tanh(n2 * 3.0)
        alpha = np.clip((density * turb - 0.38) / 1.10, 0.0, 0.90)

        r_edge = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (sz * 0.48)
        alpha *= np.clip(1.0 - np.power(r_edge, 4.0), 0.0, 1.0)

        # Compute cloud surface normal from density for puffy 3D billowing shading
        sm_dens = cv2.GaussianBlur(density * turb, (0, 0), 3.0)
        gy, gx = np.gradient(sm_dens)
        mid_c, dark_c, hi_c = palettes[k]
        billow_t = np.clip(
            0.52 - 0.55 * gx - 0.70 * gy + 0.22 * n1,
            0.0,
            1.0,
        )
        rgb = np.zeros((sz, sz, 3), dtype=np.float32)
        for ch in range(3):
            low = dark_c[ch] * (1.0 - billow_t) + mid_c[ch] * billow_t
            hi_mix = np.clip((billow_t - 0.45) * 1.6, 0.0, 1.0)
            rgb[..., ch] = low * (1.0 - hi_mix) + hi_c[ch] * hi_mix

        rgba = np.zeros((sz, sz, 4), dtype=np.uint8)
        rgba[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
        rgba[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
        rgba[rgba[..., 3] < 3] = 0

        name = f"mist_{k:02d}"
        Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, f"{name}.png"), optimize=True)
        sprites[name] = rgba

    return sprites


def key_and_cache_extra_heads(
    out_dir: str | None = None,
    out_wh: Tuple[int, int] = (256, 256),
) -> Dict[str, np.ndarray]:
    """Key generated head portraits against white studio backdrop and cache in `work/heads/`."""
    heads_dir = out_dir or os.path.join(WORK_DIR, "heads")
    os.makedirs(heads_dir, exist_ok=True)
    cached: Dict[str, np.ndarray] = {}

    for name, (src_path, box_norm) in EXTRA_HEAD_SOURCES.items():
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Missing head source image: {src_path}")
        rgb = np.asarray(Image.open(src_path).convert("RGB"))
        h, w = rgb.shape[:2]
        pbox = (
            int(w * box_norm[0]),
            int(h * box_norm[1]),
            int(w * box_norm[2]),
            int(h * box_norm[3]),
        )
        rgba = key_white_studio_plate(rgb, protect_box=pbox)
        ys, xs = np.nonzero(rgba[..., 3] > 16)
        crop = rgba[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
        sc = min((out_wh[0] - 16) / crop.shape[1], (out_wh[1] - 16) / crop.shape[0])
        nw = max(4, int(round(crop.shape[1] * sc)))
        nh = max(4, int(round(crop.shape[0] * sc)))
        rs = resize_premul(crop, (nw, nh))
        canvas = np.zeros((out_wh[1], out_wh[0], 4), dtype=np.uint8)
        ox = (out_wh[0] - nw) // 2
        oy = (out_wh[1] - nh) // 2
        canvas[oy:oy + nh, ox:ox + nw] = rs
        Image.fromarray(canvas, "RGBA").save(os.path.join(heads_dir, f"{name}.png"), optimize=True)
        cached[name] = canvas

    return cached


def key_and_cache_enemy_shooter(
    out_path: str | None = None,
    out_wh: Tuple[int, int] = (420, 440),
) -> np.ndarray:
    """Key the front-facing 3rd-person Quake enemy shooter base and cache in `work/fx/`."""
    src_path, box_norm = ENEMY_SHOOTER_SRC
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Missing enemy shooter plate: {src_path}")
    dest = out_path or os.path.join(WORK_DIR, "fx", "enemy_shooter_base.png")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    rgb = np.asarray(Image.open(src_path).convert("RGB"))
    h, w = rgb.shape[:2]
    pbox = (
        int(w * box_norm[0]),
        int(h * box_norm[1]),
        int(w * box_norm[2]),
        int(h * box_norm[3]),
    )
    rgba = key_white_studio_plate(rgb, protect_box=pbox)
    ys, xs = np.nonzero(rgba[..., 3] > 16)
    crop = rgba[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
    sc = min((out_wh[0] - 16) / crop.shape[1], (out_wh[1] - 16) / crop.shape[0])
    nw = max(4, int(round(crop.shape[1] * sc)))
    nh = max(4, int(round(crop.shape[0] * sc)))
    rs = resize_premul(crop, (nw, nh))
    canvas = np.zeros((out_wh[1], out_wh[0], 4), dtype=np.uint8)
    ox = (out_wh[0] - nw) // 2
    oy = out_wh[1] - 8 - nh
    canvas[oy:oy + nh, ox:ox + nw] = rs
    Image.fromarray(canvas, "RGBA").save(dest, optimize=True)
    return canvas


if __name__ == "__main__":
    fx_dir = os.path.join(WORK_DIR, "fx")
    splats = render_mud_splatter_sprites(fx_dir)
    mists = render_mud_mist_sprites(fx_dir)
    heads = key_and_cache_extra_heads()
    enemy = key_and_cache_enemy_shooter()
    print(
        f"[poop_fx] Generated fx: {len(splats)} splat/glob sprites, "
        f"{len(mists)} mist sprites -> {fx_dir}; cached heads={list(heads.keys())}; "
        f"enemy_shooter_base={enemy.shape}"
    )
