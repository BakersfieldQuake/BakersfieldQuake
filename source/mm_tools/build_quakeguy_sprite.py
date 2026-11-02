"""Reproducible builder for QuakeGuy ('QUAKE Shirt Ranger') character game sprites in BakersfieldQuake
(graphics only — does not touch QC or .dat files).

Outputs:
  - progs/fr_quakeguy.spr32        (56-frame DarkPlaces SPR32: 0..7 idle, 8..55 8-dir x 6 run)
  - quakeguy_sprite/               (idle PNGs, 8x8 run PNGs, 8-frame launch PNGs, sheet, GIF, HTML)

Run with:
  python3.13 source/mm_tools/build_quakeguy_sprite.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent.parent
REF_DIR = TOOLS_DIR / "ref" / "quakeguy"

sys.path.insert(0, str(TOOLS_DIR))
from build_paul_dennis_sprites import (
    CANVAS_H,
    CANVAS_W,
    GROUND_Y,
    RUN_6_INDICES,
    SPR_H,
    SPR_OX,
    SPR_OY,
    SPR_W,
    TOP_Y,
    resize_rgba_premul,
    save_turntable_gif,
    write_spr32,
)
from paul_dennis_rig import mirror_canvas_horiz
from paul_dennis_viewer_html import build_character_viewer_html

# Frame plan across the 361-frame 360° studio turnaround video
IDLE_8_FRAMES = [0, 88, 128, 150, 175, 203, 219, 255]

# Each entry in a direction's 8-frame run list is (video_frame_idx, mirror_horiz)
RUN_8_PLAN: dict[int, list[tuple[int, bool]]] = {
    0: [(f, False) for f in [307, 309, 312, 314, 317, 319, 321, 324]],  # 0° Front
    1: [(f, False) for f in [87, 89, 91, 93, 95, 96, 98, 100]],         # 45° Front-Left
    2: [(f, False) for f in [126, 128, 130, 132, 134, 135, 137, 139]],  # 90° Left Profile
    3: [(f, False) for f in [148, 150, 152, 154]] + [(f, True) for f in [199, 201, 203, 205]],   # 135° Back-Left (zero yaw drift!)
    4: [(f, False) for f in [166, 168, 170, 172, 174, 177, 179, 181]],  # 180° Back
    5: [(f, False) for f in [199, 201, 203, 205]] + [(f, True) for f in [148, 150, 152, 154]],   # 225° Back-Right (zero yaw drift!)
    6: [(f, False) for f in [212, 214, 216, 218, 220, 221, 223, 225]],  # 270° Right Profile
    7: [(f, False) for f in [245, 247, 249, 251, 253, 254, 256, 258]],  # 315° Front-Right (unmirrored QUAKE logo!)
}

# 8-frame Idle-to-Sprint combat launch sequence (0° Front)
LAUNCH_8_FRAMES = [0, 14, 20, 26, 32, 38, 44, 50]


def key_white_studio_quakeguy(rgb: np.ndarray) -> np.ndarray:
    """High-precision alpha matting for QuakeGuy on a neutral white studio cyclorama:
    - Preserves the bright white QUAKE crescent & lettering on his black t-shirt
    - Punches out all arm-waist, elbow-back, knee-calf, and cargo-strap background holes
    - Eliminates grey cast floor shadows below his black combat boots
    - Decontaminates outer 3px boundary RGB from clean interior pixels."""
    f = rgb.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    chroma = cmax - cmin
    warmth = r - b

    H, W = rgb.shape[:2]
    yg, _ = np.mgrid[0:H, 0:W]

    is_dark_fg = (lum < 122.0) & (~((yg > 890) & (lum > 86.0) & (chroma < 11.5)))
    is_skin_fg = (warmth > 13.0) & (chroma > 14.0) & (lum < 242.0) & (yg < 820)
    fg_seed = is_dark_fg | is_skin_fg
    fg_closed = ndimage.binary_closing(fg_seed, structure=np.ones((3, 3), bool))

    # Inspect enclosed bright regions: keep ONLY holes on upper chest (y=225..465) whose outer ring
    # (2..4 px past the 1px grey AA print edge) is solid black cotton and NOT adjacent to skin!
    fg_all = ndimage.binary_fill_holes(fg_closed)
    holes = fg_all & (~fg_closed)
    h_lbl, h_num = ndimage.label(holes)
    fg_mask = fg_closed.copy()
    if h_num > 0:
        black_shirt = (lum < 75.0) & (chroma < 26.0)
        for hid in range(1, h_num + 1):
            hm = h_lbl == hid
            ys_h, _ = np.nonzero(hm)
            ym = float(ys_h.mean())
            if 225.0 <= ym <= 465.0 and len(ys_h) < 9500:
                rim_outer = ndimage.binary_dilation(hm, iterations=4) & (~ndimage.binary_dilation(hm, iterations=1))
                if np.any(rim_outer):
                    if float(black_shirt[rim_outer].mean()) >= 0.78 and float(np.percentile(warmth[rim_outer], 92)) < 16.0:
                        fg_mask |= hm

    lbl, num = ndimage.label(fg_mask)
    if num > 1:
        sizes = ndimage.sum(fg_mask, lbl, range(1, num + 1))
        fg_mask = lbl == (1 + int(np.argmax(sizes)))

    dist_in = ndimage.distance_transform_edt(fg_mask)
    dist_out = ndimage.distance_transform_edt(~fg_mask)
    signed = dist_in - dist_out

    bg_ring = (dist_out >= 2.5) & (dist_out <= 16.0)
    bg_seed = np.where(bg_ring, lum, 0.0)
    bg_w = bg_ring.astype(np.float32)
    bg_lum = cv2.GaussianBlur(bg_seed, (35, 35), 10.0) / np.maximum(cv2.GaussianBlur(bg_w, (35, 35), 10.0), 1e-4)
    bg_lum = np.where(bg_lum < 155.0, 236.0, bg_lum)

    alpha = np.clip((signed + 0.55) / 1.70, 0.0, 1.0)
    boundary = (dist_in <= 3.2) & (dist_out <= 2.0)
    dark_opac = np.clip((bg_lum - lum - 10.0) / np.maximum(bg_lum - 45.0, 40.0), 0.0, 1.0)
    skin_opac = np.clip((warmth - 6.5) / 19.0, 0.0, 1.0)
    edge_opac = np.maximum(dark_opac, np.where(yg < 820, skin_opac, 0.0))
    alpha = np.where(boundary, np.minimum(alpha, np.clip(edge_opac * 1.15, 0.0, 1.0)), alpha)
    alpha[alpha < 0.05] = 0.0

    rgb_clean = f.copy()
    core = dist_in >= 3.0
    if np.any(core):
        _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
        rim = (alpha > 0.0) & (~core)
        rgb_clean[rim] = 0.88 * f[iy[rim], ix[rim]] + 0.12 * f[rim]

    return np.dstack([
        np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])


def pretone_quakeguy_spr32(frames_rgba: list[np.ndarray]) -> list[np.ndarray]:
    """Tones QuakeGuy's SPR32 frames for DarkPlaces r_hdr_scenebrightness 2.5 so skin & white QUAKE logo
    never clip in HDR lighting while black cargo trousers retain crisp pocket/strap fold detail."""
    out: list[np.ndarray] = []
    for fr in frames_rgba:
        rgb_im = Image.fromarray(fr[..., :3], "RGB")
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(1.12)
        rgb = np.asarray(rgb_im, dtype=np.float32)
        # Soft-knee highlight roll-off (scales bright skin/white logo to ~0.78x while lifting dark black folds slightly)
        norm = rgb / 255.0
        toned = np.power(np.clip(norm, 0.0, 1.0), 0.92) * 204.0
        out.append(np.dstack([
            np.clip(np.round(toned), 0, 255).astype(np.uint8),
            fr[..., 3],
        ]))
    return out


def main() -> None:
    print("=== Building QUAKEGUY ('QUAKE Logo Ranger') ===")
    out_dir = ROOT_DIR / "quakeguy_sprite"
    spr_dir = out_dir / "spr32"
    spr_dir.mkdir(parents=True, exist_ok=True)

    meta = json.loads((REF_DIR / "quakeguy_meta.json").read_text(encoding="utf-8"))
    frame_cache: dict[int, np.ndarray] = {}

    def get_normalized(fi: int) -> np.ndarray:
        if fi in frame_cache:
            return frame_cache[fi]
        info = meta["frames"][str(fi)]
        rgb = np.asarray(Image.open(REF_DIR / info["file"]).convert("RGB"))
        rgba = key_white_studio_quakeguy(rgb)

        char_h = max(400.0, float(info["floor_y"] - info["head_y"]))
        sc = (GROUND_Y - TOP_Y) / char_h
        nw = max(1, int(round(rgba.shape[1] * sc)))
        nh = max(1, int(round(rgba.shape[0] * sc)))
        scaled = Image.fromarray(resize_rgba_premul(rgba, nw, nh), "RGBA")

        ox = int(round(CANVAS_W / 2.0 - float(info["cx"]) * sc))
        oy = int(round(GROUND_Y - float(info["floor_y"]) * sc))
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        canvas.alpha_composite(scaled, (ox, oy))
        arr = np.asarray(canvas, dtype=np.uint8)
        frame_cache[fi] = arr
        return arr

    # 1. 8-Direction Standing Idle
    idle_8: list[np.ndarray] = []
    for d, fi in enumerate(IDLE_8_FRAMES):
        im = get_normalized(fi)
        idle_8.append(im)
        Image.fromarray(im, "RGBA").save(out_dir / f"quakeguy_idle_d{d}.png", compress_level=6)

    # 2. 8-Direction x 8-Frame 360° Run Cycle
    run_8: list[list[np.ndarray]] = []
    for d in range(8):
        row: list[np.ndarray] = []
        for f_idx, (fi, do_mirror) in enumerate(RUN_8_PLAN[d]):
            im = get_normalized(fi)
            if do_mirror:
                im = mirror_canvas_horiz(im)
            row.append(im)
            Image.fromarray(im, "RGBA").save(out_dir / f"quakeguy_d{d}_f{f_idx}.png", compress_level=6)
        run_8.append(row)

    # 3. 8-Frame Idle-to-Sprint Launch Sequence
    launch_8: list[np.ndarray] = []
    for i, fi in enumerate(LAUNCH_8_FRAMES):
        im = get_normalized(fi)
        launch_8.append(im)
        Image.fromarray(im, "RGBA").save(out_dir / f"quakeguy_launch_{i:02d}.png", compress_level=6)

    # 4. 56-Frame DarkPlaces .SPR32 (progs/fr_quakeguy.spr32) + spr32/f_00..55.png
    spr_display: list[np.ndarray] = []
    for d in range(8):
        spr_display.append(resize_rgba_premul(idle_8[d], SPR_W, SPR_H))
    for d in range(8):
        for k in RUN_6_INDICES:
            spr_display.append(resize_rgba_premul(run_8[d][k], SPR_W, SPR_H))

    for idx, sfr in enumerate(spr_display):
        Image.fromarray(sfr, "RGBA").save(spr_dir / f"f_{idx:02d}.png", compress_level=6)

    spr_toned = pretone_quakeguy_spr32(spr_display)
    spr_path = ROOT_DIR / "progs" / "fr_quakeguy.spr32"
    nbytes, mlum = write_spr32(spr_path, spr_toned, ox=SPR_OX, oy=SPR_OY)
    print(f"  Wrote {spr_path} ({len(spr_toned)} frames, {nbytes / 1e6:.2f} MB, mean_lum={mlum:.1f})")

    # 5. 8x8 Transparent Contact Sheet + 360° Turntable GIF + Interactive HTML Viewer
    cell_w, cell_h = 240, 320
    sheet = Image.new("RGBA", (cell_w * 8, cell_h * 8), (0, 0, 0, 0))
    for d in range(8):
        for f in range(8):
            cell = resize_rgba_premul(run_8[d][f], cell_w, cell_h)
            sheet.paste(Image.fromarray(cell, "RGBA"), (f * cell_w, d * cell_h))
    sheet.save(out_dir / "quakeguy_360_sheet_8x8.png", compress_level=6)

    save_turntable_gif(run_8, launch_8, out_dir / "quakeguy_360_spin.gif")

    (out_dir / "index.html").write_text(
        build_character_viewer_html(
            char_key="quakeguy",
            title="QUAKEGUY — Quake Shirt Combat Sprite",
            subtitle="8-Direction 360° Live-Action Run & Idle · Unmirrored QUAKE Logo · DarkPlaces .SPR32",
            action_tab_label="⚡ Idle-to-Sprint Launch (8f)",
            action_prefix="quakeguy_launch",
            n_dirs=8,
            n_run=8,
            n_action=8,
            canvas_w=CANVAS_W,
            canvas_h=CANVAS_H,
            ground_y=GROUND_Y,
            spr_w=SPR_W,
            spr_h=SPR_H,
            accent="#f59e0b",
        ),
        encoding="utf-8",
    )
    print(f"=== Wrote full pack & viewer to {out_dir} ===")


if __name__ == "__main__":
    main()
