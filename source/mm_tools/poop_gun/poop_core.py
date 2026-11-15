"""Core extraction, white-backdrop matting, rim decontamination, and reference asset
loader for the Poop Gun 3-concept prototype suite (`source/mm_tools/poop_gun/`).
"""
from __future__ import annotations

import math
import os
import wave
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage

REF_DIR = r"G:\Downloads\poop gun"
REF_HEAD_IMG = os.path.join(REF_DIR, "grok-image-2d184e26-aa05-4ebf-9724-dbbb5132860a.jpg")
REF_DANCE_MP4 = os.path.join(REF_DIR, "grok-video-2fdada98-1b70-42bb-87a0-a8b22cc799ae.mp4")
REF_TURN_MP4 = os.path.join(REF_DIR, "grok-video-2fdada98-1b70-42bb-87a0-a8b22cc799ae (1).mp4")

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(HERE, "work")


def to_premul(rgba: np.ndarray) -> np.ndarray:
    out = rgba.astype(np.float32)
    a = out[..., 3:4] / 255.0
    out[..., :3] *= a
    return out


def from_premul(pm: np.ndarray) -> np.ndarray:
    out = np.zeros_like(pm, dtype=np.uint8)
    a = np.clip(pm[..., 3], 0.0, 255.0)
    nz = a > 0.5
    rgb = np.zeros_like(pm[..., :3], dtype=np.float32)
    rgb[nz] = pm[..., :3][nz] * (255.0 / a[nz, None])
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return out


def resize_premul(rgba: np.ndarray, wh: Tuple[int, int]) -> np.ndarray:
    pm = to_premul(rgba)
    interp = cv2.INTER_AREA if (wh[0] < rgba.shape[1] and wh[1] < rgba.shape[0]) else cv2.INTER_LINEAR
    ds = cv2.resize(pm, wh, interpolation=interp)
    return from_premul(ds)


def key_white_studio_plate(rgb: np.ndarray, protect_box: Tuple[int, int, int, int] | None = None) -> np.ndarray:
    """Cleanly key a pure white (#FFFFFF) studio backdrop while preserving interior white clothing
    (the white horizontal band on the tricolor shorts, teeth, and eye sclera).

    Uses:
      1. Border-connected flood-fill of near-white low-saturation pixels.
      2. Pure-white trapped gap removal ONLY outside `protect_box` (armpit/leg gaps).
      3. White-backdrop un-premultiplication & nearest-interior RGB spill decontamination on the rim.
    """
    h, w = rgb.shape[:2]
    arr = rgb.astype(np.float32)
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    # Candidate background pixels: very bright and neutral white/light-grey
    cand = (lo > 228.0) & (sat < 0.09)
    # Border-connected flood fill
    lbl, n_lbl = ndimage.label(cand)
    border_ids = set(np.unique(lbl[0, :])) | set(np.unique(lbl[-1, :])) | set(np.unique(lbl[:, 0])) | set(np.unique(lbl[:, -1]))
    border_ids.discard(0)
    bg = np.isin(lbl, list(border_ids))

    # Trapped interior pure-white gaps (e.g. between raised arms/legs) if very large/pure white and outside shorts
    trapped = (lo > 246.0) & (sat < 0.045) & (~bg)
    if protect_box is not None:
        px0, py0, px1, py1 = protect_box
        trapped[py0:py1, px0:px1] = False
    t_lbl, t_n = ndimage.label(trapped)
    if t_n > 0:
        sizes = ndimage.sum(trapped, t_lbl, range(1, t_n + 1))
        for idx, sz in enumerate(sizes, start=1):
            if sz >= 160:
                bg[t_lbl == idx] = True

    fg = ~bg
    # Keep only largest foreground component (+ close small accessories)
    fg_lbl, fg_n = ndimage.label(fg)
    if fg_n > 1:
        sizes = ndimage.sum(fg, fg_lbl, range(1, fg_n + 1))
        main_id = 1 + int(np.argmax(sizes))
        fg = fg_lbl == main_id

    dist_in = ndimage.distance_transform_edt(fg)
    dist_out = ndimage.distance_transform_edt(~fg)
    sdf = dist_in - dist_out

    # Soft anti-aliased alpha along silhouette edge
    alpha = np.clip((sdf + 0.35) / 1.35, 0.0, 1.0)
    # Feather any bright fringe pixels right on the 3px rim
    rim_bright = fg & (dist_in <= 3.2) & (lo > 195.0) & (sat < 0.12)
    alpha[rim_bright] *= np.clip((248.0 - lum[rim_bright]) / 55.0, 0.0, 1.0)

    # Un-premultiply semi-transparent pixels against white (255,255,255)
    semi = (alpha > 0.04) & (alpha < 0.98)
    rgb_clean = arr.copy()
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.18)
    rgb_clean[semi] = np.clip((arr[semi] - inv[:, None] * 255.0) / denom[:, None], 0.0, 255.0)

    # Decontaminate outer 2.5px white bleed from deep interior pixels
    seed = fg & (dist_in > 3.2) & (lum < 238.0)
    if np.any(seed):
        _, idx = ndimage.distance_transform_edt(~seed, return_indices=True)
        nearest = rgb_clean[idx[0], idx[1]]
        w_rim = np.clip((dist_in - 0.8) / 2.4, 0.0, 1.0)
        w_rim = np.where((dist_in <= 2.6) & (lum > 180.0) & (sat < 0.18), w_rim * 0.35, w_rim)[..., None]
        rgb_clean = rgb_clean * w_rim + nearest * (1.0 - w_rim)

    a_u8 = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8)
    rgb_u8[a_u8 < 6] = 0
    a_u8[a_u8 < 6] = 0
    return np.dstack([rgb_u8, a_u8])


def extract_turn360_sprites(out_dir: str, n_angles: int = 16, canvas_wh: Tuple[int, int] = (320, 460)) -> List[np.ndarray]:
    """Extract evenly-distributed 360-degree turnaround sprites from the turnaround MP4."""
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(REF_TURN_MP4)
    raw_frames: List[np.ndarray] = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        raw_frames.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    cap.release()

    # Exact turnaround cycle: 0 (0 deg) -> 60 (90 deg) -> 107 (180 deg) -> 154 (270 deg) -> 215 (360 deg)
    # Piecewise linear interpolation across the 4 quarter-turns gives true uniform angular spacing!
    anchors = [(0.0, 0.0), (90.0, 60.0), (180.0, 107.0), (270.0, 154.0), (360.0, 215.0)]
    ang_xs = [a[0] for a in anchors]
    frm_ys = [a[1] for a in anchors]

    sprites: List[np.ndarray] = []
    for k in range(n_angles):
        deg = 360.0 * k / float(n_angles)
        fidx = int(round(np.interp(deg, ang_xs, frm_ys))) % len(raw_frames)
        rgb = raw_frames[fidx]
        # Protect shorts band (middle lower half) from any interior white gap punch-out
        h, w = rgb.shape[:2]
        rgba = key_white_studio_plate(rgb, protect_box=(int(w * 0.22), int(h * 0.48), int(w * 0.78), int(h * 0.80)))
        # Crop tightly around foreground and place centered with foot anchor at bottom-16
        ys, xs = np.nonzero(rgba[..., 3] > 20)
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        crop = rgba[y0:y1, x0:x1]
        # Scale consistently by height (feet-to-crown ~92% of canvas height)
        cw, ch = canvas_wh
        target_h = int(ch * 0.90)
        sc = target_h / float(crop.shape[0])
        nw = max(4, int(round(crop.shape[1] * sc)))
        nh = max(4, int(round(crop.shape[0] * sc)))
        rs = resize_premul(crop, (nw, nh))
        canvas = np.zeros((ch, cw, 4), dtype=np.uint8)
        ox = (cw - nw) // 2
        oy = ch - 14 - nh
        canvas[oy:oy + nh, ox:ox + nw] = rs
        Image.fromarray(canvas, "RGBA").save(os.path.join(out_dir, f"turn_{k:02d}.png"), optimize=True)
        sprites.append(canvas)
    return sprites


def extract_dance_frames(out_dir: str, sample_indices: List[int], canvas_wh: Tuple[int, int] = (340, 460)) -> List[np.ndarray]:
    """Extract clean keyed frames from the waving/screaming/spinning performance video."""
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(REF_DANCE_MP4)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cw, ch = canvas_wh
    out_list: List[np.ndarray] = []

    # Fixed uniform scale based on standing height at frame 0 so character doesn't shrink when arms raise
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ok, f0 = cap.read()
    f0_rgb = cv2.cvtColor(f0, cv2.COLOR_BGR2RGB)
    f0_rgba = key_white_studio_plate(f0_rgb, protect_box=(160, 560, 608, 920))
    ys0 = np.nonzero(f0_rgba[..., 3] > 20)[0]
    base_h = float(ys0.max() - ys0.min())
    base_y_bot = float(ys0.max())
    scale_ref = (ch * 0.84) / max(base_h, 1.0)

    for k, fidx in enumerate(sample_indices):
        idx = max(0, min(total - 1, fidx))
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        rgba = key_white_studio_plate(rgb, protect_box=(int(w * 0.22), int(h * 0.50), int(w * 0.78), int(h * 0.84)))
        ys, xs = np.nonzero(rgba[..., 3] > 20)
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        crop = rgba[y0:y1, x0:x1]
        nw = max(4, int(round(crop.shape[1] * scale_ref)))
        nh = max(4, int(round(crop.shape[0] * scale_ref)))
        if nw > cw - 8:
            fit = (cw - 8) / float(nw)
            nw = cw - 8
            nh = max(4, int(round(nh * fit)))
        rs = resize_premul(crop, (nw, nh))
        canvas = np.zeros((ch, cw, 4), dtype=np.uint8)
        ox = (cw - nw) // 2
        # Anchor feet consistently
        oy = max(2, min(ch - nh - 2, ch - 14 - nh))
        canvas[oy:oy + nh, ox:ox + nw] = rs
        Image.fromarray(canvas, "RGBA").save(os.path.join(out_dir, f"dance_{k:02d}.png"), optimize=True)
        out_list.append(canvas)
    cap.release()
    return out_list


def extract_head_cutout_from_frame(rgba_body: np.ndarray, head_box: Tuple[int, int, int, int], out_wh: Tuple[int, int] = (256, 256)) -> np.ndarray:
    """Cleanly isolate and oval-feather a floating head from a keyed full-body video frame."""
    x0, y0, x1, y1 = head_box
    crop = rgba_body[y0:y1, x0:x1].copy()
    ch, cw = crop.shape[:2]
    yg, xg = np.mgrid[0:ch, 0:cw].astype(np.float32)
    cx = cw * 0.5
    cy = ch * 0.46
    rx = cw * 0.48
    ry = ch * 0.50
    ell = ((xg - cx) / rx) ** 2 + ((yg - cy) / ry) ** 2
    # Soft feather only at the bottom chin/neck cut so hair & ears remain crisp
    neck_mask = np.clip((1.12 - ell) / 0.18, 0.0, 1.0)
    bottom_t = np.clip((yg - ch * 0.72) / (ch * 0.25), 0.0, 1.0)
    keep = np.where(yg > ch * 0.68, neck_mask * (1.0 - bottom_t * 0.85), 1.0)
    crop[..., 3] = np.clip(np.round(crop[..., 3].astype(np.float32) * keep), 0, 255).astype(np.uint8)
    # Trim & center on out_wh
    ys, xs = np.nonzero(crop[..., 3] > 16)
    tc = crop[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
    sc = min((out_wh[0] - 16) / tc.shape[1], (out_wh[1] - 16) / tc.shape[0])
    nw, nh = max(4, int(round(tc.shape[1] * sc))), max(4, int(round(tc.shape[0] * sc)))
    rs = resize_premul(tc, (nw, nh))
    out = np.zeros((out_wh[1], out_wh[0], 4), dtype=np.uint8)
    ox = (out_wh[0] - nw) // 2
    oy = (out_wh[1] - nh) // 2
    out[oy:oy + nh, ox:ox + nw] = rs
    return out


def extract_cross_eyed_head(out_wh: Tuple[int, int] = (256, 256)) -> np.ndarray:
    im = Image.open(REF_HEAD_IMG).convert("RGB")
    rgb = np.asarray(im)
    h, w = rgb.shape[:2]
    # Protect eyes & teeth center region from white punchout!
    rgba = key_white_studio_plate(rgb, protect_box=(int(w * 0.22), int(h * 0.28), int(w * 0.78), int(h * 0.72)))
    ys, xs = np.nonzero(rgba[..., 3] > 16)
    crop = rgba[int(ys.min()):int(ys.max()) + 1, int(xs.min()):int(xs.max()) + 1]
    sc = min((out_wh[0] - 16) / crop.shape[1], (out_wh[1] - 16) / crop.shape[0])
    nw, nh = max(4, int(round(crop.shape[1] * sc))), max(4, int(round(crop.shape[0] * sc)))
    rs = resize_premul(crop, (nw, nh))
    out = np.zeros((out_wh[1], out_wh[0], 4), dtype=np.uint8)
    ox = (out_wh[0] - nw) // 2
    oy = (out_wh[1] - nh) // 2
    out[oy:oy + nh, ox:ox + nw] = rs
    return out


def prepare_reference_bank() -> Dict[str, object]:
    """Extract and cache all clean keyed reference sprites, heads, and audio clips in work/."""
    os.makedirs(WORK_DIR, exist_ok=True)
    turn_dir = os.path.join(WORK_DIR, "turn_16")
    dance_dir = os.path.join(WORK_DIR, "dance_48")
    heads_dir = os.path.join(WORK_DIR, "heads")
    os.makedirs(heads_dir, exist_ok=True)

    print("[poop_core] Extracting 16-angle 360° turnaround sprites...")
    turn_16 = extract_turn360_sprites(turn_dir, n_angles=16, canvas_wh=(320, 460))

    print("[poop_core] Extracting 48 dance/scream/spin sprites...")
    # Sample f18..f236 (full ecstatic screaming, spinning, waving, laughing sequence!)
    dance_idx = [int(round(x)) for x in np.linspace(18, 236, 48)]
    dance_48 = extract_dance_frames(dance_dir, dance_idx, canvas_wh=(340, 460))

    print("[poop_core] Extracting floating expressive heads...")
    head_cross = extract_cross_eyed_head((256, 256))
    Image.fromarray(head_cross, "RGBA").save(os.path.join(heads_dir, "head_cross.png"), optimize=True)

    # Extract several expressive heads from raw dance video frames for razor-sharp resolution
    cap = cv2.VideoCapture(REF_DANCE_MP4)
    head_specs = [
        ("head_scream_front", 31, (280, 12, 488, 210)),
        ("head_laugh_tilt", 41, (290, 18, 496, 212)),
        ("head_side_yell_r", 104, (330, 14, 520, 200)),
        ("head_side_yell_l", 62, (235, 16, 425, 202)),
        ("head_sky_gasp", 166, (285, 10, 490, 205)),
        ("head_wide_grin", 198, (285, 16, 495, 210)),
    ]
    extracted_heads = {"head_cross": head_cross}
    for hname, fidx, box in head_specs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
        ok, fr = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        rgba = key_white_studio_plate(rgb, protect_box=(160, 560, 608, 920))
        h_im = extract_head_cutout_from_frame(rgba, box, (256, 256))
        Image.fromarray(h_im, "RGBA").save(os.path.join(heads_dir, f"{hname}.png"), optimize=True)
        extracted_heads[hname] = h_im
    cap.release()

    return {"turn_16": turn_16, "dance_48": dance_48, "heads": extracted_heads}


if __name__ == "__main__":
    bank = prepare_reference_bank()
    print(
        f"Done: turn_16={len(bank['turn_16'])}, dance_48={len(bank['dance_48'])}, "
        f"heads={list(bank['heads'].keys())}"
    )
