#!/usr/bin/env python3
"""Build Variant 1: "Classic Quake Munition" (v1_classic) for the Rocket Rider vote studio.

Faithful, high-detail upscaled 1996 Quake `progs/missile.mdl`-inspired warhead rocket
with the canonical Quake 1 Ranger straddling on top like a bronco / Dr. Strangelove
rider — gripping a heavy bolted steel U-hoop tightly across all 100 animation frames
while a roaring molten exhaust plume blasts out of the glowing cast-iron bell nozzle.

Pure Python 3.12 + numpy + Pillow (no scipy, deterministic seeded RNG, CI-reproducible).

Outputs under `source/mm_tools/out/rocket_rider/`:
  - v1_classic.md3
  - v1_classic.md3_0.skin
  - scripts/v1_classic.shader
  - v1_classic_meta.json
  - v1_rocket.png       (1024x1024 weathered Quake munition UV texture)
  - v1_rocket_glow.png  (1024x1024 inner nozzle throat emissive glow, pure black elsewhere)
  - v1_flame.png        (512x512 classic molten orange-amber additive flame atlas)
  - ranger_skin.png     (592x388 canonical Quake 1 Ranger skin)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import common as C  # noqa: E402

VARIANT_ID = "v1_classic"
SHORT_LABEL = "V1"
TITLE = "Classic Quake Munition"
SUBTITLE = "1996 id1 Missile Warhead · Bolted U-Hoop Bronco Ride · Glowing Single-Bell Exhaust"
ACCENT = "#ff7b29"

FUSE_RADIUS = 13.5
GRIP_L = np.array([17.0, +6.5, 21.0], dtype=np.float64)
GRIP_R = np.array([17.0, -6.5, 21.0], dtype=np.float64)
NOZZLE_EXIT_LOCAL = np.array([-53.5, 0.0, 0.0], dtype=np.float32)
NOZZLE_DIR_LOCAL = np.array([-1.0, 0.0, 0.0], dtype=np.float32)

# UV atlas regions (1024x1024, non-overlapping with >= 2% padding):
#   Region A (u 0.00..1.00, v 0.00..0.54): Main fuselage + stepped hazard warhead + brass fuse
#   Region B (u 0.02..0.48, v 0.56..0.98): Cast-iron nozzle bell (outer <=0.852, glowing inner >=0.868)
#   Region C (u 0.52..0.75, v 0.56..0.78): Swept X-configuration tail fins & tip skids
#   Region D1 (u 0.77..0.98, v 0.56..0.665): Forged gunmetal collars, bolts, grab hoop, foot-pegs
#   Region D2 (u 0.77..0.98, v 0.68..0.78): Riveted quilted leather/canvas saddle pad
#   Region E1 (u 0.52..0.75, v 0.80..0.98): Burnished oxidized copper external fuel lines
#   Region E2 (u 0.77..0.98, v 0.80..0.98): Brass pipe clamps & knurled rubber handle grips
UV_NOZZLE_U = (0.03, 0.47)
UV_NOZZLE_V = (0.565, 0.975)
UV_FIN = (0.525, 0.565, 0.745, 0.775)
UV_STEEL = (0.775, 0.565, 0.975, 0.662)
UV_SADDLE = (0.775, 0.682, 0.975, 0.775)
UV_COPPER = (0.525, 0.805, 0.745, 0.975)
UV_BRASS = (0.775, 0.805, 0.875, 0.975)
UV_GRIP = (0.885, 0.805, 0.975, 0.975)


# ===========================================================================
# DETERMINISTIC PROCEDURAL 5x7 MILITARY STENCIL FONT (OS-INDEPENDENT)
# ===========================================================================

_STENCIL_FONT_5X7: dict[str, list[str]] = {
    "I": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111",
    ],
    "D": [
        "11100",
        "10010",
        "10001",
        "10001",
        "10001",
        "10010",
        "11100",
    ],
    "1": [
        "00100",
        "01100",
        "00100",
        "00100",
        "00100",
        "00100",
        "01110",
    ],
    "0": [
        "01110",
        "10001",
        "10011",
        "10101",
        "11001",
        "10001",
        "01110",
    ],
    "B": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10001",
        "10001",
        "11110",
    ],
    "A": [
        "01110",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "K": [
        "10001",
        "10010",
        "10100",
        "11000",
        "10100",
        "10010",
        "10001",
    ],
    "O": [
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "/": [
        "00001",
        "00010",
        "00010",
        "00100",
        "01000",
        "01000",
        "10000",
    ],
    "-": [
        "00000",
        "00000",
        "00000",
        "11111",
        "00000",
        "00000",
        "00000",
    ],
    " ": [
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
        "00000",
    ],
    "M": [
        "10001",
        "11011",
        "10101",
        "10101",
        "10001",
        "10001",
        "10001",
    ],
    "W": [
        "10001",
        "10001",
        "10001",
        "10101",
        "10101",
        "11011",
        "10001",
    ],
    "R": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ],
    "H": [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "E": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ],
}


def _render_stencil_mask(text: str, px_scale_x: int = 3, px_scale_y: int = 4, letter_gap: int = 2) -> np.ndarray:
    """Render an upright boolean stencil mask (H_txt, W_txt), row 0 = TOP of letters, col 0 = LEFT."""
    glyph_w = 5
    glyph_h = 7
    total_cols = len(text) * (glyph_w + letter_gap) - letter_gap
    base = np.zeros((glyph_h, max(1, total_cols)), dtype=np.float32)
    x_cur = 0
    for ch in text:
        g = _STENCIL_FONT_5X7.get(ch, _STENCIL_FONT_5X7[" "])
        for r, row_s in enumerate(g):
            for c, bit in enumerate(row_s):
                if bit == "1":
                    base[r, x_cur + c] = 1.0
        x_cur += glyph_w + letter_gap

    # Upscale cleanly and add slight anti-aliased military stencil softness
    up = np.repeat(np.repeat(base, px_scale_y, axis=0), px_scale_x, axis=1)
    # 1px soft blur via deterministic 3x3 average (pure numpy)
    p = np.pad(up, 1, mode="constant")
    soft = (
        4.0 * up
        + p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        + 0.5 * (p[:-2, :-2] + p[:-2, 2:] + p[2:, :-2] + p[2:, 2:])
    ) / 10.0
    return np.clip(soft * 1.18, 0.0, 1.0).astype(np.float32)


def _fbm_2d(h: int, w: int, rng: np.random.Generator, octaves=((8, 8, 0.50), (20, 20, 0.30), (52, 52, 0.20))) -> np.ndarray:
    acc = np.zeros((h, w), dtype=np.float32)
    wsum = 0.0
    for gy, gx, wt in octaves:
        acc += wt * C._value_noise_2d(h, w, gy, gx, rng)
        wsum += wt
    return (acc / max(1e-6, wsum)).astype(np.float32)


def _stamp_rivet_row(
    img: np.ndarray,
    xs: np.ndarray,
    ys: np.ndarray,
    radius: float = 3.2,
    metal_col=(0.46, 0.48, 0.46),
) -> None:
    """Stamp crisp shaded 3D dome rivets with dark AO ring & bright top-left specular highlight."""
    H, W, _ = img.shape
    rad_i = int(math.ceil(radius + 2.5))
    dy, dx = np.mgrid[-rad_i : rad_i + 1, -rad_i : rad_i + 1].astype(np.float32)
    dist = np.hypot(dx, dy)
    ao = np.exp(-((dist / (radius * 1.48)) ** 2)) * 0.58
    dome = np.clip(1.0 - (dist / radius) ** 2, 0.0, 1.0)
    mask = dist <= radius
    # Bevel lighting from upper-left
    nx = np.clip(-dx / max(1e-4, radius), -1.0, 1.0)
    ny = np.clip(-dy / max(1e-4, radius), -1.0, 1.0)
    nz = np.sqrt(np.maximum(0.0, 1.0 - np.minimum(1.0, (dist / radius) ** 2)))
    lit = np.clip(0.45 + 0.55 * (0.52 * nx + 0.52 * ny + 0.68 * nz), 0.15, 1.25)
    spec = np.clip((0.52 * nx + 0.52 * ny + 0.68 * nz) ** 8, 0.0, 1.0) * 0.45
    mc = np.asarray(metal_col, dtype=np.float32)

    for cx, cy in zip(xs, ys):
        ix, iy = int(round(float(cx))), int(round(float(cy)))
        y0, y1 = max(0, iy - rad_i), min(H, iy + rad_i + 1)
        x0, x1 = max(0, ix - rad_i), min(W, ix + rad_i + 1)
        if y1 <= y0 or x1 <= x0:
            continue
        sy0, sy1 = y0 - (iy - rad_i), y1 - (iy - rad_i)
        sx0, sx1 = x0 - (ix - rad_i), x1 - (ix - rad_i)

        patch = img[y0:y1, x0:x1]
        ao_p = ao[sy0:sy1, sx0:sx1, None]
        patch *= (1.0 - ao_p)
        m_p = mask[sy0:sy1, sx0:sx1]
        if np.any(m_p):
            lit_p = lit[sy0:sy1, sx0:sx1, None]
            sp_p = spec[sy0:sy1, sx0:sx1, None]
            r_col = mc[None, None, :] * lit_p + sp_p
            alpha = np.clip(dome[sy0:sy1, sx0:sx1] * 2.2, 0.0, 1.0)[..., None]
            patch[:] = patch * (1.0 - alpha) + r_col * alpha


def _stamp_flank_stencil(
    img: np.ndarray,
    text: str,
    u_center: float,
    v_center: float,
    flank: str,
    color=(0.88, 0.84, 0.72),
    px_scale_x: int = 3,
    px_scale_y: int = 4,
    wear_noise: np.ndarray | None = None,
) -> None:
    """Stamp readable upright stencil text onto Region A port (+Y) or starboard (-Y) flank.

    Coordinate mapping for `add_lathe_axis((0,0,0), (1,0,0), ..., up_hint=(0,1,0))`:
      - u=0.0 bottom (-Z), u=0.25 port (+Y), u=0.50 top (+Z), u=0.75 starboard (-Y)
      - v increases from tail (-X) to nose (+X)
      - Port (+Y, viewed from +Y): screen-right = -X (decreasing v), screen-up = +Z (increasing u)
      - Starboard (-Y, viewed from -Y): screen-right = +X (increasing v), screen-up = +Z (decreasing u)
    """
    H, W, _ = img.shape
    # mask shape: (H_txt, W_txt) where row 0 = TOP of text, col 0 = LEFT of text
    mask = _render_stencil_mask(text, px_scale_x=px_scale_x, px_scale_y=px_scale_y, letter_gap=2)
    ht, wt = mask.shape

    # Map (text_row, text_col) into image patch (y_v, x_u):
    # We want text_col (left -> right) along the v axis (image rows y),
    # and text_row (top -> bottom) along the u axis (image cols x).
    if flank == "port":
        # Port (+Y): left->right = decreasing y (v), top->bottom = decreasing x (u)
        # Transpose -> shape (wt, ht): axis 0 is text_col (0=left -> highest y), axis 1 is text_row (0=top -> highest x)
        patch_m = mask.T[::-1, ::-1]
    elif flank == "starboard":
        # Starboard (-Y): left->right = increasing y (v), top->bottom = increasing x (u)
        patch_m = mask.T
    else:
        raise ValueError(f"Unknown flank: {flank}")

    ph, pw = patch_m.shape
    cy = int(round(v_center * H))
    cx = int(round(u_center * W))
    y0, x0 = cy - ph // 2, cx - pw // 2
    y1, x1 = y0 + ph, x0 + pw
    if y0 < 0 or x0 < 0 or y1 > H or x1 > W:
        raise ValueError(f"Stencil '{text}' out of atlas bounds at ({x0}:{x1}, {y0}:{y1})")

    alpha = patch_m * 0.88
    if wear_noise is not None:
        wn = wear_noise[y0:y1, x0:x1]
        # Subtle paint chipping through stencil letters
        chip = C._smoothstep(0.68, 0.86, wn)
        alpha = alpha * (1.0 - 0.55 * chip)

    col = np.asarray(color, dtype=np.float32)[None, None, :]
    # Subtle dark spray halo / edge grime for Quake grit
    sub = img[y0:y1, x0:x1]
    sub[:] = sub * (1.0 - alpha[..., None]) + col * alpha[..., None]


def build_v1_textures(out_dir: Path) -> tuple[Path, Path]:
    """Generate deterministic 1024x1024 `v1_rocket.png` and `v1_rocket_glow.png`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_path = out_dir / "v1_rocket.png"
    glow_path = out_dir / "v1_rocket_glow.png"

    H = W = 1024
    rng = np.random.default_rng(19960101)

    img = np.zeros((H, W, 3), dtype=np.float32)
    glow = np.zeros((H, W, 3), dtype=np.float32)

    # Multi-scale deterministic noise textures
    n_macro = _fbm_2d(H, W, rng, octaves=((6, 6, 0.55), (14, 14, 0.30), (32, 32, 0.15)))
    n_fine = _fbm_2d(H, W, rng, octaves=((36, 36, 0.45), (84, 84, 0.35), (180, 180, 0.20)))
    n_brush_x = C._value_noise_2d(H, W, 16, 220, rng)   # streaks along v (axial)
    n_brush_u = C._value_noise_2d(H, W, 220, 16, rng)   # streaks along u (lathe-turned)
    n_rust = _fbm_2d(H, W, rng, octaves=((12, 18, 0.5), (34, 48, 0.35), (96, 128, 0.15)))
    n_scratch = C._value_noise_2d(H, W, 90, 260, rng)

    yy, xx = np.meshgrid(
        np.linspace(0.0, 1.0, H, endpoint=False, dtype=np.float32),
        np.linspace(0.0, 1.0, W, endpoint=False, dtype=np.float32),
        indexing="ij",
    )

    # =====================================================================
    # REGION A: Main Fuselage + Stepped Hazard Collar + Warhead + Brass Fuse
    # (u: 0.00..1.00, v: 0.00..0.545 -> y: 0..558)
    # =====================================================================
    yA = int(round(0.548 * H))
    vvA = yy[:yA, :]
    uuA = xx[:yA, :]

    # Base weathered military olive-drab & dark gunmetal steel panels
    olive_a = np.array([0.285, 0.315, 0.205], dtype=np.float32)   # Quake military olive-drab
    olive_b = np.array([0.235, 0.260, 0.178], dtype=np.float32)   # darker olive panel
    gunmetal = np.array([0.225, 0.238, 0.248], dtype=np.float32)  # dark steel gunmetal
    bright_steel = np.array([0.56, 0.59, 0.61], dtype=np.float32)
    rust_col = np.array([0.36, 0.165, 0.075], dtype=np.float32)
    soot_col = np.array([0.075, 0.070, 0.068], dtype=np.float32)

    # Alternating panel tones (seams at u = 0.0, 0.125, 0.375, 0.625, 0.875 so flanks at 0.25/0.75 sit on clean plates!)
    panel_u_idx = np.floor(((uuA + 0.125) % 1.0) * 4.0).astype(np.int32)
    panel_v_idx = np.digitize(vvA, [0.120, 0.335, 0.365])
    # Top/bottom plates are slightly darker gunmetal-olive, flanks are richer military olive-drab
    is_flank_plate = (panel_u_idx == 1) | (panel_u_idx == 3)
    baseA = np.where(is_flank_plate[..., None], olive_a, olive_b)
    # Subtle gunmetal tint on aft propulsion bay (v < 0.125)
    aft_bay = C._smoothstep(0.130, 0.105, vvA)
    baseA = baseA * (1.0 - 0.55 * aft_bay[..., None]) + gunmetal * (0.55 * aft_bay[..., None])
    # Subtle panel-to-panel tonal variation
    panel_var = 0.92 + 0.14 * (((panel_u_idx * 3 + panel_v_idx * 5) % 4) / 3.0)
    baseA = baseA * panel_var[..., None]

    # Modulate with mottled wear + brushed grain
    wear_mod = 0.82 + 0.26 * n_macro[:yA] + 0.10 * n_fine[:yA] + 0.06 * (n_brush_x[:yA] - 0.5)
    baseA = baseA * wear_mod[..., None]

    # Subtle rust streaks weeping around seams & lower belly
    rust_mask = C._smoothstep(0.60, 0.82, n_rust[:yA]) * (0.42 + 0.38 * (1.0 - np.abs(uuA - 0.5) * 0.4))
    rust_mask *= (1.0 - C._smoothstep(0.46, 0.50, vvA))
    baseA = baseA * (1.0 - 0.52 * rust_mask[..., None]) + rust_col * (0.52 * rust_mask[..., None])

    # Crisp panel seam grooves + metallic edge highlight + painted rivets
    # Wide clean central armor bay (v=0.120..0.335) frames the "ID1 // BAKO-01" stencil cleanly!
    seam_u_pos = [0.0, 0.125, 0.375, 0.625, 0.875]
    seam_v_pos = [0.120, 0.335, 0.365]
    seam_ao = np.zeros((yA, W), dtype=np.float32)
    seam_hi = np.zeros((yA, W), dtype=np.float32)
    for su in seam_u_pos:
        du = np.minimum(np.abs(uuA - su), 1.0 - np.abs(uuA - su))
        seam_ao = np.maximum(seam_ao, np.exp(-((du / 0.0024) ** 2)) * 0.68)
        du_hi = np.minimum(np.abs(uuA - (su + 0.0028)), 1.0 - np.abs(uuA - (su + 0.0028)))
        seam_hi = np.maximum(seam_hi, np.exp(-((du_hi / 0.0018) ** 2)) * 0.22)
    for sv in seam_v_pos:
        dv = np.abs(vvA - sv)
        seam_ao = np.maximum(seam_ao, np.exp(-((dv / 0.0022) ** 2)) * 0.72)
        seam_hi = np.maximum(seam_hi, np.exp(-((np.abs(vvA - (sv + 0.0026)) / 0.0018) ** 2)) * 0.25)

    # Confine fuselage panel seams to v < 0.368
    fuse_only = (vvA < 0.368).astype(np.float32)
    baseA = baseA * (1.0 - seam_ao[..., None] * fuse_only[..., None])
    baseA = baseA + bright_steel * (seam_hi * fuse_only * (0.45 + 0.55 * n_fine[:yA]))[..., None]

    # Fine scratched paint exposing bright steel edges
    chip_mask = C._smoothstep(0.79, 0.90, n_scratch[:yA] * 0.6 + n_fine[:yA] * 0.4) * fuse_only
    baseA = baseA * (1.0 - 0.55 * chip_mask[..., None]) + bright_steel * (0.55 * chip_mask[..., None])

    # Tail soot & exhaust heat-scorch band (v = 0.00..0.115)
    soot_edge = 0.088 + 0.036 * n_macro[:yA] + 0.014 * np.sin(uuA * 2.0 * math.pi * 8.0 + n_fine[:yA] * 3.0)
    soot_w = (1.0 - C._smoothstep(0.015, soot_edge, vvA)) ** 1.15
    baseA = baseA * (1.0 - 0.86 * soot_w[..., None]) + soot_col * (0.86 * soot_w[..., None])

    # Crisp yellow/black diagonal hazard stripes around the warhead collar (v = 0.368..0.425)
    haz_band = (vvA >= 0.368) & (vvA <= 0.426)
    haz_inner = (vvA >= 0.374) & (vvA <= 0.419)
    # 16 diagonal stripes seamlessly wrapping u = 0..1
    diag_phase = (uuA * 16.0 + (vvA - 0.374) * 28.0) % 1.0
    # Crisp anti-aliased stripe mask
    s_edge = 0.025
    is_yellow = C._smoothstep(0.0, s_edge, diag_phase) * (1.0 - C._smoothstep(0.50 - s_edge, 0.50 + s_edge, diag_phase))
    haz_yellow = np.array([0.89, 0.64, 0.10], dtype=np.float32)
    haz_black = np.array([0.095, 0.095, 0.102], dtype=np.float32)
    haz_steel = np.array([0.19, 0.20, 0.21], dtype=np.float32)
    haz_col = haz_black * (1.0 - is_yellow[..., None]) + haz_yellow * is_yellow[..., None]
    # Weather & chip hazard stripes so they feel authentic 1996 Quake industrial, not plastic!
    haz_grime = 0.82 + 0.24 * n_macro[:yA] - 0.16 * C._smoothstep(0.62, 0.85, n_rust[:yA])
    haz_col = haz_col * haz_grime[..., None]
    haz_chip = C._smoothstep(0.80, 0.90, n_fine[:yA] * 0.55 + n_scratch[:yA] * 0.45)
    haz_col = haz_col * (1.0 - 0.65 * haz_chip[..., None]) + bright_steel * (0.65 * haz_chip[..., None])
    # Dark steel border trim framing the hazard collar
    baseA = np.where(haz_band[..., None], haz_steel * (0.85 + 0.25 * n_fine[:yA, :, None]), baseA)
    baseA = np.where(haz_inner[..., None], haz_col, baseA)

    # Stepped warhead ogive armor cone (v = 0.426..0.494)
    ogive_m = (vvA > 0.426) & (vvA <= 0.494)
    ogive_base = np.array([0.23, 0.245, 0.225], dtype=np.float32)  # heavy cast dark olive-iron
    # Subtle red-oxide munition ring right behind brass fuse (v = 0.478..0.491)
    oxide_ring = C._smoothstep(0.476, 0.479, vvA) * (1.0 - C._smoothstep(0.489, 0.493, vvA))
    oxide_col = np.array([0.46, 0.155, 0.095], dtype=np.float32)
    ogive_col = ogive_base * (1.0 - 0.78 * oxide_ring[..., None]) + oxide_col * (0.78 * oxide_ring[..., None])
    # 8 radial cast armor seams on nosecone
    rad_seam = np.abs(((uuA * 8.0) % 1.0) - 0.5)
    ogive_seam_ao = np.exp(-(((0.5 - rad_seam) / 0.022) ** 2)) * 0.55
    ogive_col = ogive_col * (0.82 + 0.24 * n_macro[:yA, :, None] + 0.12 * n_brush_u[:yA, :, None])
    ogive_col *= (1.0 - ogive_seam_ao[..., None])
    ogive_chip = C._smoothstep(0.80, 0.90, n_fine[:yA])
    ogive_col = ogive_col * (1.0 - 0.42 * ogive_chip[..., None]) + bright_steel * (0.42 * ogive_chip[..., None])
    baseA = np.where(ogive_m[..., None], ogive_col, baseA)

    # Heavy machined brass & copper impact fuse tip (v = 0.494..0.548)
    fuse_m = vvA > 0.494
    brass_hi = np.array([0.82, 0.64, 0.30], dtype=np.float32)
    brass_dk = np.array([0.46, 0.31, 0.13], dtype=np.float32)
    copper_mid = np.array([0.68, 0.38, 0.20], dtype=np.float32)
    # Lathe-turned bands + knurled diamond grip around v = 0.498..0.514
    lathe_wave = 0.5 + 0.5 * np.sin((vvA - 0.494) * 2.0 * math.pi * 65.0)
    knurl_band = C._smoothstep(0.497, 0.500, vvA) * (1.0 - C._smoothstep(0.512, 0.515, vvA))
    knurl_pat = (
        0.5 + 0.5 * np.sin((uuA * 44.0 + vvA * 180.0) * 2.0 * math.pi)
        * np.sin((uuA * 44.0 - vvA * 180.0) * 2.0 * math.pi)
    )
    fuse_col = brass_dk * (1.0 - lathe_wave[..., None]) + brass_hi * lathe_wave[..., None]
    # Warm copper collar transition
    cop_w = C._smoothstep(0.515, 0.522, vvA) * (1.0 - C._smoothstep(0.530, 0.535, vvA))
    fuse_col = fuse_col * (1.0 - 0.65 * cop_w[..., None]) + copper_mid * (0.65 * cop_w[..., None])
    fuse_col *= (1.0 - 0.34 * knurl_band[..., None] * (1.0 - knurl_pat[..., None]))
    fuse_col *= (0.86 + 0.22 * n_brush_u[:yA, :, None])
    # Dark steel impact striker pin at tip (v > 0.534)
    pin_w = C._smoothstep(0.532, 0.536, vvA)
    fuse_col = fuse_col * (1.0 - 0.72 * pin_w[..., None]) + np.array([0.22, 0.23, 0.25], dtype=np.float32) * (0.72 * pin_w[..., None])
    baseA = np.where(fuse_m[..., None], fuse_col, baseA)

    img[:yA, :] = baseA

    # Stamp crisp double rivet rows along circumferential fuselage panel seams
    riv_u = np.linspace(0.015, 0.985, 32)
    for sv in (0.120, 0.335, 0.365):
        for dv_off in (-0.0085, +0.0085):
            if sv == 0.365 and dv_off > 0:
                continue
            _stamp_rivet_row(
                img,
                riv_u * W,
                np.full_like(riv_u, (sv + dv_off) * H),
                radius=2.9,
                metal_col=(0.48, 0.50, 0.47),
            )
    # Stamp longitudinal seam rivets along seam_u_pos
    riv_v = np.linspace(0.135, 0.320, 10)
    for su in (0.125, 0.375, 0.625, 0.875):
        for du_off in (-0.009, +0.009):
            _stamp_rivet_row(
                img,
                np.full_like(riv_v, (su + du_off) * W),
                riv_v * H,
                radius=2.6,
                metal_col=(0.45, 0.47, 0.44),
            )

    # Stamp crisp upright stenciled "ID1 // BAKO-01" on BOTH port (+Y, u=0.25) and starboard (-Y, u=0.75) flanks!
    # Positioned slightly forward-center (v_center=0.242, u=0.245/0.755) cleanly clear of Ranger's straddling boot!
    for flank, u_ctr, u_sub in (("port", 0.246, 0.194), ("starboard", 0.754, 0.806)):
        # Main bold stencil: "ID1 // BAKO-01"
        _stamp_flank_stencil(
            img,
            "ID1 // BAKO-01",
            u_center=u_ctr,
            v_center=0.242,
            flank=flank,
            color=(0.94, 0.90, 0.77),
            px_scale_x=2,
            px_scale_y=4,
            wear_noise=n_fine,
        )
        # Subtle secondary stencil line right underneath: "MK-1 WARHEAD"
        _stamp_flank_stencil(
            img,
            "MK-1 WARHEAD",
            u_center=u_sub,
            v_center=0.242,
            flank=flank,
            color=(0.92, 0.60, 0.20),
            px_scale_x=1,
            px_scale_y=2,
            wear_noise=n_fine,
        )
        # Thin stenciled military stripe brackets above/below lettering
        y_b0, y_b1 = int(0.156 * H), int(0.326 * H)
        for u_bar in (u_ctr + (0.040 if flank == "port" else -0.040), u_sub + (-0.020 if flank == "port" else 0.020)):
            xb = int(round(u_bar * W))
            bar_w = 0.74 * (1.0 - 0.35 * C._smoothstep(0.68, 0.88, n_fine[y_b0:y_b1, xb - 2 : xb + 2]))
            img[y_b0:y_b1, xb - 2 : xb + 2] = (
                img[y_b0:y_b1, xb - 2 : xb + 2] * (1.0 - bar_w[..., None])
                + np.array([0.88, 0.82, 0.66], dtype=np.float32) * bar_w[..., None]
            )

    # =====================================================================
    # REGION B: Cast-Iron Exhaust Bell Nozzle + Glowing Red-Orange Throat!
    # (u: 0.02..0.48, v: 0.56..0.985)
    # =====================================================================
    bx0, bx1 = int(0.015 * W), int(0.490 * W)
    by0, by1 = int(0.555 * H), int(0.988 * H)
    vvB = (yy[by0:by1, bx0:bx1] - UV_NOZZLE_V[0]) / (UV_NOZZLE_V[1] - UV_NOZZLE_V[0])
    uuB = (xx[by0:by1, bx0:bx1] - UV_NOZZLE_U[0]) / (UV_NOZZLE_U[1] - UV_NOZZLE_U[0])

    # Exterior bell (v_frac <= 0.71): heavy soot-darkened pitted cast iron + heat-blued rim
    cast_iron = np.array([0.155, 0.152, 0.162], dtype=np.float32)
    rib_steel = np.array([0.33, 0.34, 0.36], dtype=np.float32)
    heat_blue = np.array([0.24, 0.16, 0.22], dtype=np.float32)
    heat_amber = np.array([0.34, 0.18, 0.09], dtype=np.float32)

    pitted = 0.72 + 0.34 * n_fine[by0:by1, bx0:bx1] + 0.16 * n_macro[by0:by1, bx0:bx1]
    noz_ext = cast_iron * pitted[..., None]
    # Longitudinal cast-iron flute ribs along bell
    flutes = 0.5 + 0.5 * np.cos(uuB * 2.0 * math.pi * 16.0)
    noz_ext *= (0.86 + 0.22 * flutes[..., None])
    # Metallic highlight on exterior reinforcing hoop rib (v_frac ~ 0.46..0.55)
    rib_w = np.exp(-(((vvB - 0.50) / 0.045) ** 2))
    noz_ext = noz_ext * (1.0 - 0.55 * rib_w[..., None]) + rib_steel * (0.55 * rib_w[..., None])
    # Heat-tempering rainbow sheen near outer nozzle lip (v_frac ~ 0.58..0.70)
    hb_w = np.exp(-(((vvB - 0.62) / 0.055) ** 2))
    ha_w = np.exp(-(((vvB - 0.68) / 0.045) ** 2))
    noz_ext = noz_ext * (1.0 - 0.45 * hb_w[..., None]) + heat_blue * (0.45 * hb_w[..., None])
    noz_ext = noz_ext * (1.0 - 0.45 * ha_w[..., None]) + heat_amber * (0.45 * ha_w[..., None])

    # Glowing molten inner throat (v_frac >= 0.735 -> 1.00)
    # Keep outer rim strictly <= 0.715 completely dark so ZERO glow bleeds outside the bell!
    inner_t = C._smoothstep(0.730, 0.985, vvB)
    inner_turb = 0.88 + 0.18 * n_fine[by0:by1, bx0:bx1] + 0.08 * np.sin(uuB * 2.0 * math.pi * 10.0)
    g_val = np.clip(inner_t * inner_turb, 0.0, 1.0)
    c_cherry = np.array([0.85, 0.12, 0.02], dtype=np.float32)
    c_orange = np.array([1.00, 0.46, 0.05], dtype=np.float32)
    c_white_hot = np.array([1.00, 0.92, 0.58], dtype=np.float32)

    w_or = C._smoothstep(0.15, 0.68, g_val)
    w_wh = C._smoothstep(0.58, 0.98, g_val)
    throat_col = c_cherry * (1.0 - w_or[..., None]) + c_orange * w_or[..., None]
    throat_col = throat_col * (1.0 - w_wh[..., None]) + c_white_hot * w_wh[..., None]

    inner_blend = C._smoothstep(0.720, 0.765, vvB)
    img[by0:by1, bx0:bx1] = noz_ext * (1.0 - inner_blend[..., None]) + throat_col * inner_blend[..., None]

    # Emissive glow map: strictly ONLY inside the recessed nozzle throat (v_frac >= 0.74)!
    # Pure black (0, 0, 0) everywhere else across the entire 1024x1024 image!
    glow_mask = C._smoothstep(0.742, 0.810, vvB) * (
        C._smoothstep(0.015, 0.030, xx[by0:by1, bx0:bx1])
        * (1.0 - C._smoothstep(0.470, 0.485, xx[by0:by1, bx0:bx1]))
        * (1.0 - C._smoothstep(0.976, 0.986, yy[by0:by1, bx0:bx1]))
    )
    glow_intensity = glow_mask * (0.45 + 0.55 * g_val)
    glow[by0:by1, bx0:bx1] = throat_col * glow_intensity[..., None]

    # =====================================================================
    # REGION C: Swept Cruciform Tail Fins (u: 0.52..0.75, v: 0.56..0.78)
    # u=0 trailing edge -> u=1 leading edge; v=0 root -> v=1 fin tip
    # =====================================================================
    cx0, cx1 = int(0.515 * W), int(0.755 * W)
    cy0, cy1 = int(0.555 * H), int(0.785 * H)
    uC = np.clip((xx[cy0:cy1, cx0:cx1] - UV_FIN[0]) / (UV_FIN[2] - UV_FIN[0]), 0.0, 1.0)
    vC = np.clip((yy[cy0:cy1, cx0:cx1] - UV_FIN[1]) / (UV_FIN[3] - UV_FIN[1]), 0.0, 1.0)

    fin_col = np.array([0.23, 0.25, 0.21], dtype=np.float32) * (0.84 + 0.26 * n_macro[cy0:cy1, cx0:cx1, None] + 0.10 * n_fine[cy0:cy1, cx0:cx1, None])
    # Chamfered metallic leading-edge wear (uC > 0.84)
    le_wear = C._smoothstep(0.80, 0.94, uC)
    fin_col = fin_col * (1.0 - 0.55 * le_wear[..., None]) + bright_steel * (0.55 * le_wear[..., None])
    # Bold painted burnt-orange / hazard-yellow tip band (vC 0.78..0.91)
    tip_band = C._smoothstep(0.76, 0.785, vC) * (1.0 - C._smoothstep(0.895, 0.920, vC))
    tip_orange = np.array([0.86, 0.44, 0.09], dtype=np.float32) * (0.86 + 0.22 * n_fine[cy0:cy1, cx0:cx1, None])
    fin_col = fin_col * (1.0 - 0.85 * tip_band[..., None]) + tip_orange * (0.85 * tip_band[..., None])
    # Heavy exhaust soot on trailing edge (uC < 0.28)
    te_soot = (1.0 - C._smoothstep(0.02, 0.34, uC)) * (0.65 + 0.35 * n_macro[cy0:cy1, cx0:cx1])
    fin_col = fin_col * (1.0 - 0.75 * te_soot[..., None]) + soot_col * (0.75 * te_soot[..., None])
    # Dark armor seam mid-fin
    mid_seam = np.exp(-(((vC - 0.44) / 0.016) ** 2)) * 0.62
    fin_col *= (1.0 - mid_seam[..., None])
    img[cy0:cy1, cx0:cx1] = fin_col

    # Rivets along fin root and mid-spar
    for vf in (0.10, 0.40, 0.48):
        rx = np.linspace(UV_FIN[0] + 0.025, UV_FIN[2] - 0.025, 7) * W
        ry = np.full_like(rx, (UV_FIN[1] + vf * (UV_FIN[3] - UV_FIN[1])) * H)
        _stamp_rivet_row(img, rx, ry, radius=2.5, metal_col=(0.50, 0.52, 0.50))

    # =====================================================================
    # REGION D1: Forged Gunmetal Steel Hardware (collars, U-hoop, foot-pegs)
    # =====================================================================
    dx0, dx1 = int(0.765 * W), int(0.985 * W)
    dy0, dy1 = int(0.555 * H), int(0.672 * H)
    steel_base = np.array([0.28, 0.30, 0.32], dtype=np.float32)
    st_grain = 0.78 + 0.24 * n_brush_u[dy0:dy1, dx0:dx1] + 0.14 * n_fine[dy0:dy1, dx0:dx1]
    st_col = steel_base * st_grain[..., None]
    # Subtle oil darkening + metallic edge scratches
    st_rust = C._smoothstep(0.68, 0.88, n_rust[dy0:dy1, dx0:dx1])
    st_col = st_col * (1.0 - 0.35 * st_rust[..., None]) + rust_col * (0.35 * st_rust[..., None])
    st_hi = C._smoothstep(0.76, 0.89, n_scratch[dy0:dy1, dx0:dx1])
    st_col = st_col * (1.0 - 0.45 * st_hi[..., None]) + bright_steel * (0.45 * st_hi[..., None])
    img[dy0:dy1, dx0:dx1] = st_col

    # =====================================================================
    # REGION D2: Riveted Distressed Leather / Canvas Saddle Pad
    # =====================================================================
    sy0, sy1 = int(0.675 * H), int(0.785 * H)
    uS = (xx[sy0:sy1, dx0:dx1] - UV_SADDLE[0]) / (UV_SADDLE[2] - UV_SADDLE[0])
    vS = (yy[sy0:sy1, dx0:dx1] - UV_SADDLE[1]) / (UV_SADDLE[3] - UV_SADDLE[1])
    leather_dk = np.array([0.22, 0.14, 0.085], dtype=np.float32)
    leather_worn = np.array([0.36, 0.24, 0.14], dtype=np.float32)
    # Diamond quilted cushion shading
    q1 = np.abs(np.sin((uS * 5.0 + vS * 5.0) * math.pi))
    q2 = np.abs(np.sin((uS * 5.0 - vS * 5.0) * math.pi))
    quilt_puff = (q1 * q2) ** 0.38
    center_wear = np.exp(-(((uS - 0.5) / 0.34) ** 2 + ((vS - 0.5) / 0.36) ** 2))
    sad_col = leather_dk * (1.0 - 0.55 * center_wear[..., None]) + leather_worn * (0.55 * center_wear[..., None])
    sad_col *= (0.68 + 0.38 * quilt_puff[..., None] + 0.12 * n_fine[sy0:sy1, dx0:dx1, None])
    # Dark leather border welt
    edge_dist = np.minimum(np.minimum(uS, 1.0 - uS), np.minimum(vS, 1.0 - vS))
    sad_col *= (0.58 + 0.42 * C._smoothstep(0.02, 0.10, edge_dist))[..., None]
    img[sy0:sy1, dx0:dx1] = sad_col

    # Brass saddle rivets around pad perimeter
    srx = np.linspace(UV_SADDLE[0] + 0.02, UV_SADDLE[2] - 0.02, 6) * W
    for sv_e in (UV_SADDLE[1] + 0.012, UV_SADDLE[3] - 0.012):
        _stamp_rivet_row(img, srx, np.full_like(srx, sv_e * H), radius=2.7, metal_col=(0.78, 0.60, 0.28))

    # =====================================================================
    # REGION E1: External Burnished Oxidized Copper Fuel Line
    # =====================================================================
    ex0, ex1 = int(0.515 * W), int(0.755 * W)
    ey0, ey1 = int(0.795 * H), int(0.985 * H)
    uE = (xx[ey0:ey1, ex0:ex1] - UV_COPPER[0]) / (UV_COPPER[2] - UV_COPPER[0])
    vE = (yy[ey0:ey1, ex0:ex1] - UV_COPPER[1]) / (UV_COPPER[3] - UV_COPPER[1])
    cop_hi = np.array([0.84, 0.50, 0.28], dtype=np.float32)
    cop_dk = np.array([0.44, 0.22, 0.11], dtype=np.float32)
    verdigris = np.array([0.28, 0.44, 0.37], dtype=np.float32)

    spec_stripe = 0.5 + 0.5 * np.sin(uE * 2.0 * math.pi * 2.0)
    cop_col = cop_dk * (1.0 - spec_stripe[..., None]) + cop_hi * spec_stripe[..., None]
    # Pipe coupling rings along length (vE)
    rings = np.exp(-(((vE * 6.0 % 1.0 - 0.5) / 0.06) ** 2))
    cop_col *= (1.0 - 0.38 * rings[..., None])
    verd_m = rings * C._smoothstep(0.42, 0.72, n_macro[ey0:ey1, ex0:ex1])
    cop_col = cop_col * (1.0 - 0.48 * verd_m[..., None]) + verdigris * (0.48 * verd_m[..., None])
    cop_col *= (0.86 + 0.20 * n_fine[ey0:ey1, ex0:ex1, None])
    img[ey0:ey1, ex0:ex1] = cop_col

    # =====================================================================
    # REGION E2: Brass Clamp Fittings (left) & Knurled Handle Grip (right)
    # =====================================================================
    fx0, fx1 = int(0.765 * W), int(0.880 * W)
    img[ey0:ey1, fx0:fx1] = (
        np.array([0.66, 0.50, 0.23], dtype=np.float32)
        * (0.78 + 0.28 * n_brush_u[ey0:ey1, fx0:fx1, None] + 0.12 * n_fine[ey0:ey1, fx0:fx1, None])
    )
    gx0, gx1 = int(0.880 * W), int(0.985 * W)
    uG = (xx[ey0:ey1, gx0:gx1] - UV_GRIP[0]) / (UV_GRIP[2] - UV_GRIP[0])
    vG = (yy[ey0:ey1, gx0:gx1] - UV_GRIP[1]) / (UV_GRIP[3] - UV_GRIP[1])
    rib_g = 0.5 + 0.5 * np.sin((vG * 18.0 + uG * 4.0) * 2.0 * math.pi)
    grip_col = np.array([0.16, 0.145, 0.135], dtype=np.float32) * (0.70 + 0.48 * rib_g[..., None])
    img[ey0:ey1, gx0:gx1] = grip_col

    # Save 1024x1024 RGB textures (deterministic)
    rgb_u8 = np.clip(np.rint(img * 255.0), 0, 255).astype(np.uint8)
    glow_u8 = np.clip(np.rint(glow * 255.0), 0, 255).astype(np.uint8)

    # Sanity verify glow map is strictly pure black outside Region B nozzle throat
    assert glow_u8[:by0, :].max() == 0, "Glow leak into Region A!"
    assert glow_u8[:, bx1:].max() == 0, "Glow leak into Regions C/D/E!"
    assert glow_u8[by0:by1, bx0:bx1].max() > 220, "Nozzle throat glow too dim!"

    Image.fromarray(rgb_u8, mode="RGB").save(tex_path, "PNG", optimize=True)
    Image.fromarray(glow_u8, mode="RGB").save(glow_path, "PNG", optimize=True)
    return tex_path, glow_path


# ===========================================================================
# ROCKET GEOMETRY BUILDER (`rocket_body`, budget <= 3500v / 7000t)
# ===========================================================================

def _add_curved_saddle_pad(
    sb: C.SurfBuilder,
    x0: float = -16.5,
    x1: float = 5.5,
    r_inner: float = 13.15,
    r_outer: float = 14.95,
    ang_half_deg: float = 34.0,
    n_arc: int = 10,
    n_len: int = 6,
    uv_rect=UV_SADDLE,
) -> None:
    """Build a solid curved riveted saddle pad hugging the top arc of the cylindrical fuselage."""
    u0, v0, u1, v1 = uv_rect
    # Grid of top surface + bottom inner arc, stitched solidly on all 4 sides
    angs = np.linspace(math.radians(90.0 - ang_half_deg), math.radians(90.0 + ang_half_deg), n_arc + 1)
    xs = np.linspace(x0, x1, n_len + 1)

    verts: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []

    def _r_top_at(ix: int, ia: int) -> float:
        fx = ix / float(n_len)
        fa = abs((ia / float(n_arc)) - 0.5) * 2.0  # 0 at top center, 1 at side edge
        # Slight cushioned crown + raised aft cantle lip (x near x0) to cradle Ranger pelvis
        cantle = 1.65 * max(0.0, 1.0 - fx / 0.24) ** 1.7
        taper_side = 1.0 - 0.35 * (fa ** 2.2)
        taper_front = 1.0 - 0.45 * max(0.0, (fx - 0.80) / 0.20) ** 1.5
        return r_inner + (r_outer - r_inner) * taper_side * taper_front + cantle * (1.0 - 0.5 * fa * fa)

    # Layer 0: top shell, Layer 1: bottom inner shell (embedded inside hull)
    for layer in range(2):
        for ix, xv in enumerate(xs):
            fx = ix / float(n_len)
            vv = v0 + (v1 - v0) * fx
            for ia, ang in enumerate(angs):
                fa = ia / float(n_arc)
                uu = u0 + (u1 - u0) * fa
                rr = _r_top_at(ix, ia) if layer == 0 else r_inner
                verts.append((float(xv), float(rr * math.cos(ang)), float(rr * math.sin(ang))))
                uvs.append((uu, vv))

    stride_x = n_arc + 1
    layer_sz = (n_len + 1) * stride_x
    tris: list[tuple[int, int, int]] = []

    # Top face (+Z outward)
    for ix in range(n_len):
        for ia in range(n_arc):
            a = ix * stride_x + ia
            b = a + 1
            c = a + stride_x + 1
            d = a + stride_x
            tris.append((a, b, c))
            tris.append((a, c, d))

    # Bottom face (-Z)
    for ix in range(n_len):
        for ia in range(n_arc):
            a = layer_sz + ix * stride_x + ia
            b = a + 1
            c = a + stride_x + 1
            d = a + stride_x
            tris.append((a, c, b))
            tris.append((a, d, c))

    # Side walls (ia=0 and ia=n_arc)
    for ix in range(n_len):
        for ia, flip in ((0, True), (n_arc, False)):
            t0 = ix * stride_x + ia
            t1 = (ix + 1) * stride_x + ia
            b0 = layer_sz + t0
            b1 = layer_sz + t1
            if flip:
                tris.append((t0, t1, b1))
                tris.append((t0, b1, b0))
            else:
                tris.append((t0, b1, t1))
                tris.append((t0, b0, b1))

    # Front (ix=n_len) & Rear (ix=0) caps
    for ia in range(n_arc):
        # Rear (ix=0)
        t0, t1 = ia, ia + 1
        b0, b1 = layer_sz + t0, layer_sz + t1
        tris.append((t0, b1, t1))
        tris.append((t0, b0, b1))
        # Front (ix=n_len)
        base = n_len * stride_x
        t0, t1 = base + ia, base + ia + 1
        b0, b1 = layer_sz + t0, layer_sz + t1
        tris.append((t0, t1, b1))
        tris.append((t0, b1, b0))

    ctr = (0.5 * (x0 + x1), 0.0, 0.5 * (r_inner + r_outer))
    sb.add_mesh(verts, tris, uvs, verify_center=ctr)


def _add_collar_bolts(
    sb: C.SurfBuilder,
    x_center: float,
    radius: float,
    n_bolts: int = 8,
    size_x: float = 1.15,
    size_t: float = 1.05,
    height: float = 0.95,
    uv_rect=UV_STEEL,
    phase_deg: float = 22.5,
) -> None:
    """Add crisp, budget-friendly bolted steel hex/block lugs evenly around a collar ring."""
    for k in range(n_bolts):
        ang_deg = phase_deg + 360.0 * (k / float(n_bolts))
        ang = math.radians(ang_deg)
        # Box centered at origin rotated around X so +Y points radially outward at angle ang_deg
        R = C.rot_x_mat(ang_deg)
        pos = (x_center, (radius + height * 0.35) * math.cos(ang), (radius + height * 0.35) * math.sin(ang))
        # Wait: rot_x_mat maps (0,1,0) -> (0, cos(ang), sin(ang))!
        sb.add_box(
            -size_x * 0.5, size_x * 0.5,
            -height * 0.6, height * 0.6,
            -size_t * 0.5, size_t * 0.5,
            uv_rect=uv_rect,
            R=R,
            offset=pos,
        )


def build_v1_rocket_mesh() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Construct the iconic V1 Classic Quake Munition mesh in local space (+X fwd, +Y left, +Z up)."""
    sb = C.SurfBuilder("rocket_body", f"progs/rr_{VARIANT_ID}_rocket", max_verts=3500, max_tris=7000)

    # 1. Main cylindrical fuselage + stepped warhead collar + ogive + heavy brass/copper fuse tip
    #    Use up_hint=(0,1,0) so UV seam is hidden on the bottom (-Z), leaving port (+Y, u=0.25),
    #    top (+Z, u=0.50), and starboard (-Y, u=0.75) 100% seam-free for crisp stencils!
    hull_profile = [
        (-44.0,  0.00, 0.010),
        (-44.0, 10.60, 0.018),
        (-42.8, 11.75, 0.032),
        (-38.0, 13.10, 0.068),
        (-34.0, 13.50, 0.095),
        (-22.0, 13.50, 0.155),
        ( -6.0, 13.50, 0.235),
        ( 10.0, 13.50, 0.312),
        ( 22.0, 13.50, 0.358),
        # Stepped warhead shoulder & hazard-striped collar (X = +25.5..+34.8)
        ( 25.5, 13.50, 0.370),
        ( 26.2, 14.15, 0.376),
        ( 33.8, 14.05, 0.419),
        ( 34.8, 12.60, 0.426),
        # Stepped ogive warhead armor cone (X = +34.8..+48.8)
        ( 38.6, 11.35, 0.448),
        ( 43.2,  9.05, 0.470),
        ( 47.4,  6.25, 0.488),
        ( 48.6,  5.10, 0.494),
        # Heavy knurled brass & copper impact fuse tip (X = +48.6..+56.0)
        ( 49.2,  5.55, 0.499),
        ( 51.4,  4.65, 0.511),
        ( 53.6,  3.10, 0.524),
        ( 55.2,  1.45, 0.533),
        ( 56.0,  0.00, 0.539),
    ]
    sb.add_lathe_axis(
        origin=(0.0, 0.0, 0.0),
        axis_dir=(1.0, 0.0, 0.0),
        profile=hull_profile,
        n_seg=28,
        u_range=(0.00, 1.00),
        v_range=(0.00, 1.00),  # profile v_frac directly specifies atlas v (0.010..0.539)
        check_winding=True,
        up_hint=(0.0, 1.0, 0.0),
    )

    # 2. Cast-iron converging-diverging exhaust bell nozzle (X = -42..-56) with hollow glowing throat!
    #    s=0 -> X=-42.0 (embedded cleanly into fuselage), s=14 -> X=-56.0 (exit lip)
    nozzle_profile = [
        ( 0.0,  0.00, 0.00),
        ( 0.0,  9.60, 0.04),
        ( 2.2,  9.85, 0.14),
        ( 3.6,  7.25, 0.24),   # converging pinch
        ( 4.8,  7.00, 0.32),   # throat neck
        ( 7.6,  9.35, 0.45),
        ( 8.3, 10.15, 0.50),   # cast-iron reinforcing exterior hoop rib
        ( 9.3,  9.95, 0.55),
        (12.6, 11.40, 0.65),
        (14.0, 11.75, 0.70),   # machined outer lip (v_frac=0.70 -> strictly non-glowing!)
        (14.0, 10.15, 0.74),   # inner lip bevel
        (10.0,  8.15, 0.85),   # glowing recessed inner wall
        ( 5.0,  5.55, 0.95),   # incandescent throat
        ( 4.5,  0.00, 1.00),   # glowing inner chamber plug
    ]
    sb.add_lathe_axis(
        origin=(-42.0, 0.0, 0.0),
        axis_dir=(-1.0, 0.0, 0.0),
        profile=nozzle_profile,
        n_seg=24,
        u_range=UV_NOZZLE_U,
        v_range=UV_NOZZLE_V,
        check_winding=True,
    )

    # 3. Four bold Quake-authentic swept cruciform tail fins (+-45 deg X-configuration: 45, 135, 225, 315)
    #    Bottom two double as wide sturdy landing skids on idle_ground; top two clear Ranger's back!
    for ang_deg in (45.0, 135.0, 225.0, 315.0):
        sb.add_fin(
            root_x0=-43.5,
            root_x1=-19.0,
            tip_x0=-52.5,
            tip_x1=-35.0,
            r_root=11.0,
            span=16.6,
            angle_deg=ang_deg,
            thickness_root=2.4,
            thickness_tip=0.95,
            uv_rect=UV_FIN,
            sweep_stations=4,
        )
        # Armored fin-tip stiffener rail / landing skid shoe along each fin tip edge
        ang = math.radians(ang_deg)
        r_tip = 11.0 + 16.6
        R_fin = C.rot_x_mat(ang_deg)
        sb.add_box(
            -52.8, -34.6,
            r_tip - 0.6, r_tip + 0.9,
            -0.75, 0.75,
            uv_rect=UV_STEEL,
            R=R_fin,
        )

    # 4. Bolted steel collar rings with 3D hex-lug bolts
    sb.add_ring_band(x_center=25.8, radius=13.75, width=2.8, height=0.85, n_seg=24, uv_rect=UV_STEEL, rivets=0)
    _add_collar_bolts(sb, x_center=25.8, radius=14.60, n_bolts=8, uv_rect=UV_STEEL, phase_deg=22.5)

    sb.add_ring_band(x_center=-34.2, radius=13.45, width=3.0, height=0.85, n_seg=24, uv_rect=UV_STEEL, rivets=0)
    _add_collar_bolts(sb, x_center=-34.2, radius=14.30, n_bolts=8, uv_rect=UV_STEEL, phase_deg=22.5)

    sb.add_ring_band(x_center=-16.5, radius=13.50, width=2.4, height=0.65, n_seg=22, uv_rect=UV_STEEL, rivets=0)
    sb.add_ring_band(x_center=34.8, radius=12.60, width=1.8, height=0.65, n_seg=22, uv_rect=UV_STEEL, rivets=0)

    # 5. External oxidized copper fuel lines along port (+Y) and starboard (-Y) lower flanks
    #    Positioned cleanly at ~-35 deg / -145 deg (well below Ranger's boots & foot-pegs!) with brass clamp blocks
    for sign in (+1.0, -1.0):
        y_pipe = sign * 11.95
        z_pipe = -8.20
        pipe_pts = [
            (-42.5, sign * 9.0, -6.2),   # dives into rear engine bulkhead
            (-39.5, y_pipe, z_pipe),
            (-26.0, y_pipe, z_pipe),
            (-10.0, y_pipe, z_pipe),
            (  8.0, y_pipe, z_pipe),
            ( 22.0, y_pipe, z_pipe),
            ( 25.0, sign * 9.8, -6.6),   # enters warhead feed manifold
        ]
        sb.add_tube(pipe_pts, radii=1.15, n_seg=8, uv_rect=UV_COPPER, cap_ends=True)

        # 3 brass pipe mounting clamps per flank
        clamp_ang = -34.5 if sign > 0 else -(180.0 - 34.5)
        R_cl = C.rot_x_mat(clamp_ang)
        for xc in (-28.0, -6.0, 14.0):
            sb.add_box(xc - 1.3, xc + 1.3, 12.9, 15.8, -1.5, 1.5, uv_rect=UV_BRASS, R=R_cl)

    # 6. Riveted curved saddle pad on top (X = -16.5..+5.5, Z = +13.5..+15.0) + side bolt rails
    _add_curved_saddle_pad(sb, x0=-16.5, x1=5.5, r_inner=13.15, r_outer=14.95, ang_half_deg=34.0)
    for sign in (+1.0, -1.0):
        ang_rail = 90.0 - sign * 35.0
        R_rail = C.rot_x_mat(ang_rail)
        sb.add_box(-16.0, 5.0, 13.0, 14.4, -0.75, 0.75, uv_rect=UV_STEEL, R=R_rail)

    # 7. Heavy U-shaped bolted steel grab hoop/handle (X=+14..+20, Z=+13..+22)
    #    Centerline passes squarely through GRIP_L=(17, +6.5, 21) and GRIP_R=(17, -6.5, 21)!
    hoop_pts = [
        (16.0, +9.2,  9.6),   # bolted deep into port hull
        (16.2, +9.6, 13.2),
        (16.6, +9.3, 17.5),
        (16.9, +8.3, 20.1),
        (17.0, +6.5, 21.0),   # <-- EXACT LEFT HAND GRIP
        (17.2, +3.2, 21.3),
        (17.3,  0.0, 21.4),
        (17.2, -3.2, 21.3),
        (17.0, -6.5, 21.0),   # <-- EXACT RIGHT HAND GRIP
        (16.9, -8.3, 20.1),
        (16.6, -9.3, 17.5),
        (16.2, -9.6, 13.2),
        (16.0, -9.2,  9.6),   # bolted deep into starboard hull
    ]
    hoop_rads = [1.20, 1.15, 1.15, 1.15, 1.28, 1.18, 1.18, 1.18, 1.28, 1.15, 1.15, 1.15, 1.20]
    sb.add_tube(hoop_pts, radii=hoop_rads, n_seg=10, uv_rect=UV_STEEL, cap_ends=True)

    # Knurled rubber grip sleeves right where Ranger's hands clamp on (Y = +-4.5..+-8.0)
    for sign in (+1.0, -1.0):
        sleeve_pts = [
            (17.15, sign * 4.4, 21.22),
            (17.00, sign * 6.5, 21.00),
            (16.92, sign * 8.1, 20.22),
        ]
        sb.add_tube(sleeve_pts, radii=1.42, n_seg=10, uv_rect=UV_GRIP, cap_ends=True)

    # Heavy bolted base mounting plates & forward diagonal gusset struts anchoring the U-hoop
    for sign in (+1.0, -1.0):
        ang_bp = 90.0 - sign * 40.0
        R_bp = C.rot_x_mat(ang_bp)
        sb.add_box(13.8, 20.2, 12.6, 14.3, -2.0, 2.0, uv_rect=UV_STEEL, R=R_bp)
        # Forward diagonal gusset bar bracing the hoop against hard G-pull
        gusset_pts = [
            (19.4, sign * 8.9, 10.6),
            (18.0, sign * 9.3, 14.2),
            (16.6, sign * 9.3, 17.4),
        ]
        sb.add_tube(gusset_pts, radii=0.78, n_seg=8, uv_rect=UV_STEEL, cap_ends=True)

    # 8. Rear foot-peg brackets right ahead of the fin roots (X=-14.5..-9.5, Y=+-13.0..+-19.8, Z=-5.4..-2.4)
    for sign in (+1.0, -1.0):
        # Bolted steel mounting gusset on flank
        y0, y1 = (11.8, 14.2) if sign > 0 else (-14.2, -11.8)
        sb.add_box(-14.2, -9.2, y0, y1, -5.4, -2.0, uv_rect=UV_STEEL)
        # Stout horizontal steel foot-peg bar extending out cleanly for Ranger's boot
        peg_pts = [
            (-11.2, sign * 12.6, -3.7),
            (-11.2, sign * 16.4, -3.7),
            (-11.2, sign * 19.6, -3.7),
        ]
        sb.add_tube(peg_pts, radii=[1.10, 1.05, 1.05], n_seg=8, uv_rect=UV_GRIP, cap_ends=True)
        # Outer raised boot-stop flange at peg tip
        sb.add_box(-12.6, -9.8, sign * 19.2 - 0.5, sign * 19.2 + 0.5, -4.9, -1.8, uv_rect=UV_STEEL)

    verts, norms, uvs, tris = sb.finalize()
    vol = C.signed_mesh_volume(verts, tris)
    assert vol > 15000.0, f"V1 rocket_body signed volume too low/inverted: {vol:.1f}"
    print(f"  [mesh] rocket_body: {len(verts)}v / {len(tris)}t (vol=+{vol:.0f})", flush=True)
    return verts, norms, uvs, tris


# ===========================================================================
# 7-CLIP (100-FRAME) EXPRESSIVE ANIMATION CHOREOGRAPHY
# ===========================================================================

def _eval_frame_params(clip_id: str, ph: float) -> dict[str, Any]:
    """Return vehicle transform, Ranger pose kwargs, and main nozzle flame spec for one frame."""
    s1, c1 = math.sin(ph), math.cos(ph)
    s2, c2 = math.sin(2.0 * ph), math.cos(2.0 * ph)
    s3, c3 = math.sin(3.0 * ph), math.cos(3.0 * ph)
    s4, c4 = math.sin(4.0 * ph), math.cos(4.0 * ph)
    s5 = math.sin(5.0 * ph)

    # Default hands: ALWAYS locked firmly onto the U-shaped bolted steel grab hoop!
    grip_l = GRIP_L.copy()
    grip_r = GRIP_R.copy()

    if clip_id == "fly_cruise":
        veh = dict(
            offset=(0.0, 0.0, 34.0 + 2.2 * s1),
            pitch_deg=1.8 * c1,
            yaw_deg=1.2 * s1,
            roll_deg=5.0 * s1,
        )
        rider = dict(
            hip_pos=(-4.5, 0.0, 16.6 + 0.35 * c1),
            torso_pitch=24.0 + 2.2 * c1,
            torso_yaw=1.5 * s1,
            torso_roll=-2.4 * s1,
            head_pitch=-7.5 + 2.0 * c1,
            head_yaw=11.0 * s1,
            head_roll=-1.5 * s1,
            l_hand=grip_l,
            r_hand=grip_r,
            l_elbow_hint=(4.8, 14.5 + 0.5 * s1, 22.0 + 0.4 * c1),
            r_elbow_hint=(4.8, -14.5 + 0.5 * s1, 22.0 + 0.4 * c1),
            l_knee=(5.6, 17.8, 9.2),
            r_knee=(5.6, -17.8, 9.2),
            l_foot=(-9.8, 18.4, -2.0),
            r_foot=(-9.8, -18.4, -2.0),
            lean_x=1.5,
        )
        flame = dict(
            length=62.0 + 6.0 * s2,
            radius=10.5 + 0.45 * c2,
            intensity=0.95,
            ribbons_alpha=0.0,
        )

    elif clip_id == "fly_boost":
        veh = dict(
            offset=(0.0, 0.0, 34.0 + 1.1 * s1 + 0.55 * s4),
            pitch_deg=5.0 + 1.4 * s2 + 0.55 * c4,
            yaw_deg=0.8 * s2,
            roll_deg=3.0 * s1 + 1.1 * c4,
        )
        rider = dict(
            hip_pos=(-6.2, 0.0, 16.6 + 0.28 * s4),
            torso_pitch=12.0 + 2.4 * s2,
            torso_yaw=0.8 * s1,
            torso_roll=-1.8 * s1 - 0.6 * c4,
            head_pitch=-5.0 + 1.5 * s2,
            head_yaw=3.2 * s1,
            head_roll=-1.0 * s1,
            l_hand=grip_l,
            r_hand=grip_r,
            l_elbow_hint=(3.4, 13.6, 23.4 + 0.4 * s2),
            r_elbow_hint=(3.4, -13.6, 23.4 + 0.4 * s2),
            l_knee=(5.2, 18.0, 9.2),
            r_knee=(5.2, -18.0, 9.2),
            l_foot=(-10.2, 18.5, -2.0),
            r_foot=(-10.2, -18.5, -2.0),
            lean_x=-1.1 - 0.4 * s2,
        )
        flame = dict(
            length=107.0 + 9.0 * s2,
            radius=13.5 + 0.7 * c2,
            intensity=1.25,
            ribbons_alpha=0.65,
        )

    elif clip_id == "fly_hover":
        veh = dict(
            offset=(0.0, 0.0, 37.5 + 3.2 * s1),
            pitch_deg=26.0 + 2.4 * c1,
            yaw_deg=1.5 * c1,
            roll_deg=2.8 * s1,
        )
        rider = dict(
            hip_pos=(-5.5, 0.0, 16.9 + 0.45 * s1),
            torso_pitch=6.0 - 2.2 * c1,
            torso_yaw=1.2 * c1,
            torso_roll=-1.8 * s1,
            head_pitch=9.0 - 2.0 * c1,
            head_yaw=9.5 * s1,
            head_roll=-1.2 * s1,
            l_hand=grip_l,
            r_hand=grip_r,
            l_elbow_hint=(3.5, 14.3, 24.2 + 0.45 * s1),
            r_elbow_hint=(3.5, -14.3, 24.2 + 0.45 * s1),
            l_knee=(5.5, 17.8, 9.6),
            r_knee=(5.5, -17.8, 9.6),
            l_foot=(-9.8, 18.4, -1.8),
            r_foot=(-9.8, -18.4, -1.8),
            lean_x=0.0,
        )
        flame = dict(
            length=55.0 + 7.0 * s2,
            radius=12.0 + 0.6 * c2,
            intensity=0.95,
            ribbons_alpha=0.0,
        )

    elif clip_id == "swoop_dive":
        veh = dict(
            offset=(0.0, 0.0, 34.0 + 1.6 * c1),
            pitch_deg=-28.0 + 1.8 * s1,
            yaw_deg=1.0 * s1,
            roll_deg=4.2 * s1,
        )
        rider = dict(
            hip_pos=(-4.0, 0.0, 16.95 + 0.25 * c1),
            torso_pitch=42.0 + 2.0 * c1,
            torso_yaw=0.8 * s1,
            torso_roll=-2.0 * s1,
            head_pitch=-21.0 + 1.6 * s1,
            head_yaw=4.0 * s1,
            head_roll=-1.2 * s1,
            l_hand=grip_l,
            r_hand=grip_r,
            l_elbow_hint=(8.8, 15.2, 20.4 + 0.3 * c1),
            r_elbow_hint=(8.8, -15.2, 20.4 + 0.3 * c1),
            l_knee=(6.0, 18.2, 9.6),
            r_knee=(6.0, -18.2, 9.6),
            l_foot=(-9.8, 18.6, -1.8),
            r_foot=(-9.8, -18.6, -1.8),
            lean_x=2.6,
        )
        flame = dict(
            length=73.0 + 5.0 * s2,
            radius=9.5 + 0.35 * c2,
            intensity=1.0,
            ribbons_alpha=0.35,
        )

    elif clip_id == "idle_ground":
        # Firmly parked on bottom X-fin skids pitched slightly nose-up (+6 deg);
        # auto_ground_idle=True snaps exact z_min == 0.00 across all 12 frames.
        veh = dict(
            offset=(0.0, 0.0, 26.0),
            pitch_deg=6.0,
            yaw_deg=0.0,
            roll_deg=0.0,
        )
        rider = dict(
            hip_pos=(-4.8, 0.0, 16.55 + 0.35 * s1),
            torso_pitch=16.5 + 2.2 * s1,
            torso_yaw=1.8 * s1,
            torso_roll=0.6 * c1,
            head_pitch=-3.0 + 2.2 * c1,
            head_yaw=14.5 * s1,
            head_roll=1.5 * s1,
            l_hand=grip_l,
            r_hand=grip_r,
            l_elbow_hint=(4.6, 14.2, 22.5 + 0.45 * s1),
            r_elbow_hint=(4.6, -14.2, 22.5 + 0.45 * s1),
            l_knee=(5.6, 17.8, 9.2),
            r_knee=(5.6, -17.8, 9.2),
            l_foot=(-9.8, 18.4, -2.0),
            r_foot=(-9.8, -18.4, -2.0),
            lean_x=0.5,
        )
        flame = dict(
            length=19.0 + 3.0 * s2,
            radius=4.5 + 0.35 * c3,
            intensity=0.45,
            ribbons_alpha=0.0,
        )

    elif clip_id == "hit_flail":
        # Violent bucking-bronco damage wobble! Hips & boots bounce +4..7u off the fuselage
        # while BOTH hands stay locked white-knuckled onto the steel U-hoop!
        veh = dict(
            offset=(0.0, 0.0, 34.0 + 3.4 * s2 + 1.3 * c4),
            pitch_deg=9.5 * c2 + 2.2 * s3,
            yaw_deg=6.0 * s2,
            roll_deg=17.5 * s1 + 3.2 * c3,
        )
        hop = 3.8 + 3.1 * (0.5 - 0.5 * c2)  # bounces smoothly between +3.8u and +6.9u above saddle!
        boot_kick_l = 0.85 * hop + 1.2 * s1
        boot_kick_r = 0.85 * hop - 1.2 * s1
        rider = dict(
            hip_pos=(-5.8 - 0.8 * c2, -1.4 * s1, 16.5 + hop),
            torso_pitch=22.0 + 9.0 * c2,
            torso_yaw=-8.5 * s1,
            torso_roll=-13.5 * s1,
            head_pitch=-7.0 + 8.0 * s2,
            head_yaw=-15.0 * s1,
            head_roll=12.0 * c1,
            l_hand=grip_l,
            r_hand=grip_r,
            l_elbow_hint=(5.0, 15.2 + 0.8 * s1, 25.0 + 0.55 * hop),
            r_elbow_hint=(5.0, -15.2 + 0.8 * s1, 25.0 + 0.55 * hop),
            l_knee=(5.0, 18.4 + 0.8 * s1, 9.6 + 0.80 * hop),
            r_knee=(5.0, -18.4 + 0.8 * s1, 9.6 + 0.80 * hop),
            l_foot=(-10.8, 19.2 + 1.1 * s1, -1.8 + boot_kick_l),
            r_foot=(-10.8, -19.2 + 1.1 * s1, -1.8 + boot_kick_r),
            lean_x=-0.8 * c2,
        )
        # Erratic sputtering/choking flame harmonics (length 28..88, radius 7..14, intensity 0.5..1.2)
        sput = max(0.0, min(1.0, 0.50 + 0.34 * s2 + 0.24 * c3 - 0.16 * s5))
        flame = dict(
            length=28.0 + 60.0 * sput,
            radius=7.0 + 7.0 * sput,
            intensity=0.50 + 0.70 * sput,
            ribbons_alpha=0.0,
        )

    elif clip_id == "skypad_hyper":
        # Supersonic blast: intense micro-jitter, Ranger pinned back hard (-13.5 deg) clinging for dear life!
        veh = dict(
            offset=(0.0, 0.0, 35.0 + 1.2 * s1 + 0.85 * s4),
            pitch_deg=7.5 + 1.5 * s2 + 0.8 * c4,
            yaw_deg=1.4 * s4,
            roll_deg=4.2 * s2 + 1.6 * c4,
        )
        rider = dict(
            hip_pos=(-6.6, 0.0, 16.8 + 0.42 * s4),
            torso_pitch=-13.5 - 2.0 * s2,
            torso_yaw=2.2 * c2,
            torso_roll=-5.0 * s2,
            head_pitch=-9.0 - 2.2 * s2,
            head_yaw=5.5 * c2,
            head_roll=-3.0 * s2,
            l_hand=grip_l,
            r_hand=grip_r,
            l_elbow_hint=(2.6, 12.6, 25.8 + 0.5 * s4),
            r_elbow_hint=(2.6, -12.6, 25.8 + 0.5 * s4),
            l_knee=(5.4, 18.9, 9.4),
            r_knee=(5.4, -18.9, 9.4),
            l_foot=(-10.2, 19.2, -1.8),
            r_foot=(-10.2, -19.2, -1.8),
            lean_x=-1.8 - 0.35 * c2,
        )
        flame = dict(
            length=154.0 + 12.0 * s2,
            radius=16.5 + 1.0 * c2,
            intensity=1.50,
            ribbons_alpha=1.0,
        )

    else:
        raise KeyError(f"Unexpected clip_id: {clip_id}")

    return dict(veh=veh, rider=rider, flame=flame)


# ===========================================================================
# MAIN BUILD & VERIFICATION
# ===========================================================================

def build_v1_classic(out_dir: Path | str = C.OUT_DIR) -> dict[str, Any]:
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    print(f"=== Building {VARIANT_ID} ({TITLE}) -> {out_root} ===", flush=True)

    # 1. Ensure Ranger texture, build V1 rocket diffuse + emissive glow textures, and classic flame atlas
    ranger_tex = C.ensure_ranger_texture(out_root / "ranger_skin.png")
    rocket_tex, rocket_glow_tex = build_v1_textures(out_root)
    flame_tex = C.make_flame_texture(out_root / "v1_flame.png", style="classic", size=512)
    print(
        f"  [tex] {rocket_tex.name} ({rocket_tex.stat().st_size:,} B), "
        f"{rocket_glow_tex.name} ({rocket_glow_tex.stat().st_size:,} B), "
        f"{flame_tex.name} ({flame_tex.stat().st_size:,} B), "
        f"{ranger_tex.name} ({ranger_tex.stat().st_size:,} B)",
        flush=True,
    )

    # 2. Build static local-space rocket geometry + load canonical Quake 1 Ranger rig
    rb_v, rb_n, rb_u, rb_t = build_v1_rocket_mesh()
    rig = C.QuakeRangerRig()

    # 3. Evaluate all 100 frames (rocket, Ranger, and main exhaust plume transformed identically!)
    rocket_frames: list[tuple[np.ndarray, np.ndarray]] = []
    ranger_frames: list[np.ndarray] = []
    flame_nozzles: list[list[dict[str, Any]]] = []

    max_hand_err = 0.0
    min_ranger_r = 999.0
    min_ranger_vol = 1e18
    max_ranger_edge = 0.0
    e_pairs = np.vstack([rig.tris[:, [0, 1]], rig.tris[:, [1, 2]], rig.tris[:, [2, 0]]])

    for fi, clip, k, u, ph, _fname in C.iter_clip_frames():
        params = _eval_frame_params(clip["id"], ph)
        veh = params["veh"]
        ofs = np.asarray(veh["offset"], dtype=np.float32)
        pitch = float(veh["pitch_deg"])
        yaw = float(veh["yaw_deg"])
        roll = float(veh["roll_deg"])

        R_v = C.euler_mat(pitch_deg=pitch, yaw_deg=yaw, roll_deg=roll)

        # Rocket body (preserve crisp per-part normals by rotating precomputed normals)
        rv = C.apply_vehicle_xform(rb_v, offset=ofs, pitch_deg=pitch, yaw_deg=yaw, roll_deg=roll)
        rn = (rb_n @ R_v.T).astype(np.float32)
        rocket_frames.append((rv, rn))

        # Ranger posed in rocket local space, verified, then transformed identically
        r_loc = rig.pose_frame(scale=1.18, **params["rider"])
        lh_err = float(np.linalg.norm(rig.hand_centroid(r_loc, "l_arm") - GRIP_L))
        rh_err = float(np.linalg.norm(rig.hand_centroid(r_loc, "r_arm") - GRIP_R))
        max_hand_err = max(max_hand_err, lh_err, rh_err)

        # Check radial clearance against cylindrical fuselage (X = -44..+26, R = 13.5)
        in_fuse_x = (r_loc[:, 0] >= -44.0) & (r_loc[:, 0] <= 26.0)
        rad_loc = np.hypot(r_loc[in_fuse_x, 1], r_loc[in_fuse_x, 2])
        min_ranger_r = min(min_ranger_r, float(rad_loc.min()))

        r_vol = C.signed_mesh_volume(r_loc, rig.tris)
        min_ranger_vol = min(min_ranger_vol, r_vol)

        cur_max_e = float(np.linalg.norm(r_loc[e_pairs[:, 0]] - r_loc[e_pairs[:, 1]], axis=1).max())
        max_ranger_edge = max(max_ranger_edge, cur_max_e)

        r_world = C.apply_vehicle_xform(r_loc, offset=ofs, pitch_deg=pitch, yaw_deg=yaw, roll_deg=roll)
        ranger_frames.append(r_world)

        # Exhaust nozzle origin & direction transformed identically so flame stays welded inside bell!
        noz_org = (NOZZLE_EXIT_LOCAL @ R_v.T) + ofs
        noz_dir = NOZZLE_DIR_LOCAL @ R_v.T
        fl = params["flame"]
        flame_nozzles.append([
            dict(
                origin=noz_org,
                dir=noz_dir,
                length=fl["length"],
                radius=fl["radius"],
                flicker_phase=ph,
                intensity=fl["intensity"],
                ribbons_alpha=fl["ribbons_alpha"],
            )
        ])

    # Strict geometric quality assertions across ALL 100 frames
    assert max_hand_err < 1.0, f"Ranger hand detached from grab hoop: max_hand_err={max_hand_err:.2f}u"
    assert min_ranger_r >= FUSE_RADIUS - 0.05, (
        f"Ranger leg/body clips into r={FUSE_RADIUS}u fuselage: min_r={min_ranger_r:.2f}u"
    )
    assert min_ranger_vol > 6000.0, f"Ranger signed volume degraded: min_vol={min_ranger_vol:.1f}"
    assert max_ranger_edge < 25.0, f"Ranger mesh over-stretched: max_edge={max_ranger_edge:.2f}u"

    print(
        f"  [rig]  100f verified: max_hand_err={max_hand_err:.2f}u (<1.0u), "
        f"min_hull_r={min_ranger_r:.2f}u (>=13.5u), min_vol=+{min_ranger_vol:.0f}, "
        f"max_edge={max_ranger_edge:.2f}u",
        flush=True,
    )

    # 4. Build roaring additive flame surface (`flame_fx`)
    flame_surf = C.make_animated_flame_surface(
        flame_nozzles,
        surface_name="flame_fx",
        shader_name=f"progs/rr_{VARIANT_ID}_flame",
        tex_filename="v1_flame.png",
        n_seg=14,
        n_rings=8,
        n_cards=4,
        n_ribbons=6,
    )
    print(
        f"  [fx]   flame_fx: {len(flame_surf['uvs'])}v / {len(flame_surf['tris'])}t (100f classic molten plume)",
        flush=True,
    )

    # 5. Export unified MD3 + skin + shader + meta.json with round-trip verification
    surfaces = [
        {
            "name": "rocket_body",
            "shader": f"progs/rr_{VARIANT_ID}_rocket",
            "tex": "v1_rocket.png",
            "glowTex": "v1_rocket_glow.png",
            "tris": rb_t,
            "uvs": rb_u,
            "frames": rocket_frames,
            "metallic": 0.44,
            "roughness": 0.38,
            "spec": 0.62,
            "role": "rocket",
        },
        {
            "name": "ranger_body",
            "shader": f"progs/rr_{VARIANT_ID}_ranger",
            "tex": "ranger_skin.png",
            "tris": rig.tris,
            "uvs": rig.uvs,
            "frames": ranger_frames,
            "metallic": 0.08,
            "roughness": 0.68,
            "spec": 0.22,
            "role": "rider",
        },
        flame_surf,
    ]

    mix_chips = [
        "V1 Quake Warhead Hull",
        "V1 Hazard Collar & Brass Fuse",
        "V1 Bolted Steel U-Hoop",
        "V1 Glowing Cast-Iron Nozzle",
        "V1 Molten Classic Flame",
    ]
    notes = [
        [
            "Silhouette & Quake DNA",
            "Upscaled 1996 id1 `progs/missile.mdl` warhead (112u long, r=13.5u): stepped yellow/black hazard collar, heavy brass/copper impact fuse, riveted olive-drab & gunmetal armor plates stenciled `ID1 // BAKO-01`, copper flank fuel conduits, and 4 swept X-fins whose lower tips double as parked landing skids.",
        ],
        [
            "Bronco Ride & Grab Hoop",
            "Canonical Quake 1 Ranger (`scale=1.18`) straddles a curved riveted saddle pad with boots braced on knurled steel foot-pegs ahead of the fin roots and both hands locked within 0.35u of the bolted U-shaped steel grab hoop across all 100 frames — bouncing +4..7u off the saddle on `hit_flail` and pinned back `-12 deg` on `skypad_hyper`.",
        ],
        [
            "Glowing Bell & Exhaust Plume",
            "Hollow converging-diverging cast-iron bell with emissive red-orange furnace throat (`v1_rocket_glow.png`, pure black elsewhere) driving a single roaring classic molten orange-amber plume (`16u` idle pilot -> `62u` cruise -> `116u` boost -> `166u` SkyPad hyper + slipstream speed ribbons).",
        ],
    ]

    meta = C.export_variant(
        variant_id=VARIANT_ID,
        short_label=SHORT_LABEL,
        title=TITLE,
        subtitle=SUBTITLE,
        accent=ACCENT,
        surfaces=surfaces,
        mix_chips=mix_chips,
        notes=notes,
        cam_defaults={"yaw": -36, "pitch": 17, "dist": 208, "target": [-10, 0, 44]},
        out_dir=out_root,
        auto_ground_idle=True,
    )
    return meta


if __name__ == "__main__":
    build_v1_classic()
