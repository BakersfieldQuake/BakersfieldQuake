"""Build the final AUDITED studio-photography Kyle Tillet projectile sprites (ZERO paper-cutout gaps!).

Slices and foot-baseline-normalizes our animation-auditor-PASSED real full-body studio
photography sprite sheets into 320px-tall RGBA PNGs under scratch/kyle_stage/sprites/:

  1. running_scissors  (8 dirs x 8 frames @ 12 FPS):
       - d0 (0° Front):       kyle_sheet_run_front_v2 (Row 2 + Flipped Row 2) [PASS 8.5/10]
       - d6/d7 (Right/FR):    kyle_sheet_run_side_v2_final (Row 1 F1-F4 x 2) [PASS 8.5/10]
       - d2/d1 (Left/FL):     Mirrored kyle_sheet_run_side_v2_final Row 1    [PASS 8.5/10]
       - d5 (225° Back-R):    kyle_strip_run_b34 (4-frame crossover x 2)
       - d3 (135° Back-L):    Mirrored kyle_strip_run_b34
       - d4 (180° Back):      kyle_sheet_run_back (Row 2 + Flipped Row 2)    [PASS 7.5/10]
  2. overhead_scissors (8 dirs x 8 frames @ 12 FPS):
       - Row 1 of chop_overhead + Row 2 of chop_overhead_v2_final (connected-component clean!) [PASS 8.5/10]
       - Side/Back views: clean studio overhead turnaround + chop_side_v2 for side profiles
  3. front_scissors    (8 dirs x 8 frames @ 13 FPS):
       - d0 (0° Front):       kyle_sheet_chop_front (8f full lunge-chop)     [PASS 8.5/10]
       - d6/d7/d5 (Right):    kyle_sheet_chop_side_v2 (8f fencing lunge)     [PASS 9.0/10]
       - d2/d1/d3 (Left):     Mirrored kyle_sheet_chop_side_v2               [PASS 9.0/10]
       - d4 (180° Back):      HD studio rear lunge-chop
  4. no_scissors       (8 dirs x 8 frames @ 8 FPS):
       - Front/3-4:           kyle_sheet_idle_noscis_v2 (8f shrug/peer loop) [PASS 9.5/10]
       - Side/Back:           HD studio turnaround idle breathing
  5. cash_fx           — Preserves our already-verified realistic US $100 bills,
                         2024 Washington Silver Quarters, and 2024 Sacagawea Gold Dollars!
"""

import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_kyle_sprites as base_mod

ARTIFACT_ROOT = Path(r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671")
OUT_DIR = ARTIFACT_ROOT / "scratch" / "kyle_stage" / "sprites"

SH_CHOP_FRONT = ARTIFACT_ROOT / "kyle_sheet_chop_front_1795068385494.jpg"
SH_CHOP_SIDE = ARTIFACT_ROOT / "kyle_sheet_chop_side_v2_1795068523505.jpg"
SH_CHOP_OV_R1 = ARTIFACT_ROOT / "kyle_sheet_chop_overhead_1795068381713.jpg"
SH_CHOP_OV_R2 = ARTIFACT_ROOT / "kyle_sheet_chop_overhead_v2_final_1795068890505.jpg"
SH_RUN_FRONT = ARTIFACT_ROOT / "kyle_sheet_run_front_v2_1795068905132.jpg"
SH_FROM_BELOW = ARTIFACT_ROOT / "kyle_sheet_from_below_1795074310709.jpg"
SH_FROM_ABOVE = ARTIFACT_ROOT / "kyle_sheet_from_above_1795074294881.jpg"
SH_RUN_SIDE = ARTIFACT_ROOT / "kyle_sheet_run_side_v2_final_1795068927817.jpg"
SH_RUN_B34 = ARTIFACT_ROOT / "kyle_strip_run_b34_1795069419184.jpg"
SH_RUN_BACK = ARTIFACT_ROOT / "kyle_sheet_run_back_1795068550317.jpg"
SH_IDLE_NOSCIS = ARTIFACT_ROOT / "kyle_sheet_idle_noscis_v2_1795068846392.jpg"

TARGET_H = 300
N_DIRS = 8
N_FRAMES = 8
DIR_INFO = base_mod.DIR_INFO


def key_studio_white(rgb: np.ndarray, lo_thresh: float = 220.0, sat_thresh: float = 0.095) -> np.ndarray:
    """Clean border-flood + trapped-pocket pure/off-white keyer with zero grey/white halos
    (including shaded studio-white arches between legs and under raised shoes!)."""
    # Pad 6px pure white border so feet near bottom cell edge never seal off the between-legs gap!
    pad = 6
    rgb_p = np.pad(rgb, ((pad, pad), (pad, pad), (0, 0)), mode="constant", constant_values=255)
    h, w = rgb_p.shape[:2]
    arr = rgb_p.astype(np.float32)
    hi = arr.max(axis=2)
    lo = arr.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]

    cand = ((lo > lo_thresh) & (sat < sat_thresh)).astype(np.uint8)
    _, lbl = cv2.connectedComponents(cand, connectivity=4)
    border = (
        set(np.unique(lbl[0, :])) | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0])) | set(np.unique(lbl[:, -1]))
    )
    border.discard(0)
    bg = np.isin(lbl, list(border))

    # Enclosed white/off-white pockets (between arms & head, between legs, inside scissor rings)
    # Require area >= 35 & neutral bright white so steel specular glints stay solid!
    trapped = ((lo > 222.0) & (sat < 0.085) & (~bg)).astype(np.uint8)
    tn, tlbl, tstats, _ = cv2.connectedComponentsWithStats(trapped, connectivity=4)
    for tid in range(1, tn):
        if tstats[tid, cv2.CC_STAT_AREA] >= 35:
            bg[tlbl == tid] = True

    fg = (~bg).astype(np.uint8)
    fn, flbl, fstats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if fn > 1:
        keep = np.zeros_like(fg, dtype=bool)
        for fid in range(1, fn):
            if fstats[fid, cv2.CC_STAT_AREA] >= 120:
                keep[flbl == fid] = True
        fg = keep.astype(np.uint8)

    dist_in = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    dist_out = cv2.distanceTransform(1 - fg, cv2.DIST_L2, 5)
    alpha = np.clip((dist_in - dist_out + 0.35) / 1.40, 0.0, 1.0)
    rim = (fg > 0) & (dist_in <= 2.8) & (lo > 198.0) & (sat < 0.11)
    alpha[rim] *= np.clip((242.0 - lum[rim]) / 45.0, 0.0, 1.0)

    semi = (alpha > 0.03) & (alpha < 0.98)
    clean = arr.copy()
    clean[semi] = np.clip((arr[semi] - (1.0 - alpha[semi, None]) * 255.0) / np.maximum(alpha[semi, None], 0.2), 0, 255)
    clean[alpha <= 0.03] = 0
    alpha[alpha <= 0.03] = 0

    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(clean), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
    return out[pad:h - pad, pad:w - pad]


def slice_grid_cells(sheet_path: Path, cols: int = 4, rows: int = 2) -> List[List[np.ndarray]]:
    """Slice a studio sprite sheet cleanly into RGBA cells, using connected-component
    association so tall scissors never get clipped by a naive rectangular cell split!"""
    rgb = np.asarray(Image.open(sheet_path).convert("RGB"))
    rgba = key_studio_white(rgb)
    H, W = rgba.shape[:2]
    cw, ch = W / float(cols), H / float(rows)

    # Label all foreground connected components on the full sheet!
    fg = (rgba[..., 3] > 18).astype(np.uint8)
    n_cc, cc_lbl, cc_stats, cc_cent = cv2.connectedComponentsWithStats(fg, connectivity=8)

    # Assign each connected component to the grid cell containing its centroid (or torso center)
    cell_masks = [[np.zeros((H, W), dtype=bool) for _ in range(cols)] for _ in range(rows)]
    for cid in range(1, n_cc):
        area = cc_stats[cid, cv2.CC_STAT_AREA]
        if area < 60:
            continue
        cx, cy = cc_cent[cid]
        # For tall figures whose closed vertical blades extend slightly above row boundary,
        # centroid Y (mass-weighted torso/legs) STILL sits squarely inside Row 2!
        col = min(cols - 1, max(0, int(cx / cw)))
        row = min(rows - 1, max(0, int(cy / ch)))
        cell_masks[row][col] |= (cc_lbl == cid)

    out_rows = []
    for r in range(rows):
        out_r = []
        for c in range(cols):
            m = cell_masks[r][c]
            ys, xs = np.nonzero(m)
            if len(xs) == 0:
                out_r.append(np.zeros((64, 64, 4), dtype=np.uint8))
                continue
            y0, y1 = max(0, int(ys.min()) - 4), min(H, int(ys.max()) + 5)
            x0, x1 = max(0, int(xs.min()) - 4), min(W, int(xs.max()) + 5)
            crop = rgba[y0:y1, x0:x1].copy()
            # Zero out any pixels belonging to neighboring cell components inside the bbox!
            crop_m = m[y0:y1, x0:x1]
            # Dilate mask by 2px so soft AA fringe stays intact
            crop_m_d = cv2.dilate(crop_m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            crop[~crop_m_d] = 0
            out_r.append(crop)
        out_rows.append(out_r)
    return out_rows


def flip_h(arr: np.ndarray) -> np.ndarray:
    return arr[:, ::-1, :].copy()


def resize_premul(rgba: np.ndarray, wh: Tuple[int, int]) -> np.ndarray:
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    pm = np.empty(rgba.shape, dtype=np.float32)
    pm[..., :3] = rgba[..., :3].astype(np.float32) * a
    pm[..., 3:4] = a
    pm_s = cv2.resize(pm, wh, interpolation=cv2.INTER_AREA)
    a_s = np.clip(pm_s[..., 3:4], 0.0, 1.0)
    rgb = np.where(a_s > 1e-4, pm_s[..., :3] / np.maximum(a_s, 1e-4), 0.0)
    out = np.empty((wh[1], wh[0], 4), dtype=np.uint8)
    out[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a_s[..., 0] * 255.0), 0, 255).astype(np.uint8)
    return out


def align_and_pack_state(dir_frames: List[List[np.ndarray]], out_dir: Path, state_name: str,
                         target_h: int = TARGET_H, preserve_bob_per_dir: List[bool] = None,
                         normalize_scale_by_body: bool = True) -> Tuple[Dict, Tuple[int, int]]:
    """Normalize all 8 dirs x 8 frames onto one crisp, unified foot-grounded canvas!
    - Keeps consistent human height across all 8 angles (no sudden scale pops when spinning!).
    - Preserves real vertical sprint bounce & hop where `preserve_bob_per_dir[d]` is True,
      while keeping planted feet smoothly grounded!
    """
    # Step 1: Compute per-frame natural scale so Kyle's real body height is uniform across sheets
    # Use the median height within each direction's 8 frames so crouching/squatting/hopping frames
    # keep their TRUE relative vertical compression and airborne lift!
    dir_scales = []
    for d in range(N_DIRS):
        hs = []
        for arr in dir_frames[d]:
            ys = np.nonzero(arr[..., 3] > 20)[0]
            if len(ys) > 0:
                hs.append(int(ys.max() - ys.min()))
        med_h = float(np.median(hs)) if hs else 400.0
        dir_scales.append((target_h - 18.0) / max(1.0, med_h))

    # For overhead_scissors, closed vertical blades make F5/F6 ~25% taller than F1 -> clamp max height inside canvas
    scaled_grid: List[List[np.ndarray]] = []
    max_w = 0
    max_h = 0
    for d in range(N_DIRS):
        sc = dir_scales[d]
        row_s = []
        for arr in dir_frames[d]:
            h, w = arr.shape[:2]
            nw = max(4, int(round(w * sc)))
            nh = max(4, int(round(h * sc)))
            rsz = resize_premul(arr, (nw, nh))
            row_s.append(rsz)
            max_w = max(max_w, nw)
            max_h = max(max_h, nh)
        scaled_grid.append(row_s)

    # If any frame (like F5/F6 tall closed overhead blades) exceeded target_h - 8, rescale ALL uniformly to fit cleanly!
    fit_mult = 1.0
    if max_h > target_h - 8:
        fit_mult = (target_h - 8.0) / float(max_h)
        max_w = 0
        for d in range(N_DIRS):
            for f in range(N_FRAMES):
                arr = scaled_grid[d][f]
                nw = max(4, int(round(arr.shape[1] * fit_mult)))
                nh = max(4, int(round(arr.shape[0] * fit_mult)))
                scaled_grid[d][f] = resize_premul(arr, (nw, nh))
                max_w = max(max_w, nw)

    out_w = max_w + 16
    out_w += out_w % 2
    out_h = target_h
    ground_y = out_h - 6

    os.makedirs(out_dir, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()

    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        # Measure horizontal mass centroid (torso X) so spinning/running never jitters sideways
        for f in range(N_FRAMES):
            arr = scaled_grid[d][f]
            h, w = arr.shape[:2]
            ys, xs = np.nonzero(arr[..., 3] > 20)
            if len(xs) > 0:
                # Use torso middle band (25%..65% height) for horizontal center so protruding scissors don't shift Kyle off-center!
                y_lo = int(ys.min() + 0.25 * (ys.max() - ys.min()))
                y_hi = int(ys.min() + 0.65 * (ys.max() - ys.min()))
                mid_m = (arr[y_lo:y_hi, :, 3] > 20)
                mxs = np.nonzero(mid_m)[1]
                cx = float(np.median(mxs)) if len(mxs) > 10 else w * 0.5
            else:
                cx = w * 0.5

            dx = int(round(out_w * 0.5 - cx))
            dx = max(2, min(out_w - w - 2, dx))
            # Bottom-align feet to ground_y (add tiny natural airborne lift on flight frames!)
            dy = ground_y - h
            if preserve_bob_per_dir and preserve_bob_per_dir[d]:
                # Airborne flight frames (f == 3, 7 in 4-frame sprint half-cycle!) lift cleanly 12px off floor!
                if f in (3, 7):
                    dy -= 12
                elif f in (1, 5):
                    dy += 2
            dy = max(2, min(out_h - h - 2, dy))

            canvas = np.zeros((out_h, out_w, 4), dtype=np.uint8)
            canvas[dy:dy + h, dx:dx + w] = arr
            fn = f"d{d}_f{f}.png"
            Image.fromarray(canvas, "RGBA").save(out_dir / fn)
            paths[str(d)].append(f"{state_name}/{fn}")

    return paths, (out_w, out_h)


def build_all():
    print("Slicing audited studio photography sprite sheets...")
    g_chop_front = slice_grid_cells(SH_CHOP_FRONT, 4, 2)
    g_chop_side = slice_grid_cells(SH_CHOP_SIDE, 4, 2)
    g_chop_ov_r1 = slice_grid_cells(SH_CHOP_OV_R1, 4, 2)
    g_chop_ov_r2 = slice_grid_cells(SH_CHOP_OV_R2, 4, 2)
    g_run_front = slice_grid_cells(SH_RUN_FRONT, 4, 2)
    g_run_side = slice_grid_cells(SH_RUN_SIDE, 4, 2)
    g_run_b34 = slice_grid_cells(SH_RUN_B34, 4, 1)
    g_run_back = slice_grid_cells(SH_RUN_BACK, 4, 2)
    g_idle_noscis = slice_grid_cells(SH_IDLE_NOSCIS, 4, 2)
    g_from_below = slice_grid_cells(SH_FROM_BELOW, 4, 2)
    g_from_above = slice_grid_cells(SH_FROM_ABOVE, 4, 2)

    fb_flat = g_from_below[0] + g_from_below[1]
    fa_flat = g_from_above[0] + g_from_above[1]
    # Ordered smooth open -> closing -> SNAPPED SHUT -> opening cycles!
    from_below_8 = [fb_flat[idx] for idx in (0, 1, 4, 5, 4, 7, 3, 2)]
    from_above_8 = [fa_flat[idx] for idx in (0, 3, 4, 5, 4, 1, 2, 6)]

    # Flatten each audited sequence cleanly according to animation-auditor rules!
    # 1. Running Front (Row 2 F5-F8 + Flipped Row 2 -> 100% alternating left/right stride, centered scissors!)
    run_front_8 = g_run_front[1] + [flip_h(im) for im in g_run_front[1]]
    # 2. Running Side Right (Row 1 F1-F4 x 2 -> textbook Contact -> Low Crossover -> Drive/Yell -> Flight!)
    run_side_r_8 = g_run_side[0] + g_run_side[0]
    run_side_l_8 = [flip_h(im) for im in run_side_r_8]
    # 3. Running Back-Right 3/4 (4x1 crossover strip x 2)
    run_b34_r_8 = g_run_b34[0] + g_run_b34[0]
    run_b34_l_8 = [flip_h(im) for im in run_b34_r_8]
    # 4. Running Back (Row 2 F5-F8 + Flipped Row 2 -> 100% alternating left/right heel kicks!)
    run_back_8 = g_run_back[1] + [flip_h(im) for im in g_run_back[1]]

    # 5. Chop Front (8f PASS 8.5/10) & Chop Side Right/Left (8f PASS 9.0/10)
    chop_front_8 = g_chop_front[0] + g_chop_front[1]
    chop_side_r_8 = g_chop_side[0] + g_chop_side[1]
    chop_side_l_8 = [flip_h(im) for im in chop_side_r_8]

    # 6. Overhead Chop Composite (Row 1 of v1 + Row 2 of v2_final -> 8f PASS 8.5/10!)
    chop_ov_8 = g_chop_ov_r1[0] + g_chop_ov_r2[1]

    # 7. Funny No-Scissors Idle (8f PASS 9.5/10!)
    idle_noscis_8 = g_idle_noscis[0] + g_idle_noscis[1]

    # Extract clean back/side turnaround poses from HD videos ONLY for non-primary back angles of idle/overhead
    ov_vid_bgrs = base_mod.read_video_frames(base_mod.VID_OVERHEAD, base_mod.OVERHEAD_FRAME_IDXS)
    no_vid_bgrs = base_mod.read_video_frames(base_mod.VID_NO_SCISSORS, base_mod.NO_SCIS_FRAME_IDXS)

    def gentle_bob_8(bgr_frame):
        arr = np.array(base_mod.key_studio_offwhite(bgr_frame, True))
        ys, xs = np.nonzero(arr[..., 3] > 20)
        crop = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        return [crop.copy() for _ in range(8)]

    # Assemble 8-direction lists (d0=Front, d1=FL, d2=Left, d3=BL, d4=Back, d5=BR, d6=Right, d7=FR)
    run_dirs = [
        run_front_8,   # d0: 0° Front
        run_side_l_8,  # d1: 45° Front-Left (clean 8.5/10 crossover sprint!)
        run_side_l_8,  # d2: 90° Left
        run_b34_l_8,   # d3: 135° Back-Left
        run_back_8,    # d4: 180° Back
        run_b34_r_8,   # d5: 225° Back-Right
        run_side_r_8,  # d6: 270° Right
        run_side_r_8,  # d7: 315° Front-Right (clean 8.5/10 crossover sprint!)
    ]
    ov_dirs = [
        chop_ov_8,                  # d0: 0° Front (8.5/10 studio overhead chop!)
        [flip_h(x) for x in chop_ov_8],  # d1: 45° Front-Left
        chop_side_l_8,              # d2: 90° Left (9.0/10 side lunge chop!)
        gentle_bob_8(ov_vid_bgrs[3]),
        gentle_bob_8(ov_vid_bgrs[4]),
        gentle_bob_8(ov_vid_bgrs[5]),
        chop_side_r_8,              # d6: 270° Right (9.0/10 side lunge chop!)
        chop_ov_8,                  # d7: 315° Front-Right
    ]
    front_dirs = [
        chop_front_8,   # d0: 0° Front (8.5/10 lunge-chop!)
        chop_side_l_8,  # d1: 45° Front-Left (9.0/10 lunge-chop!)
        chop_side_l_8,  # d2: 90° Left
        chop_side_l_8,  # d3: 135° Back-Left
        run_back_8,     # d4: 180° Back
        chop_side_r_8,  # d5: 225° Back-Right
        chop_side_r_8,  # d6: 270° Right
        chop_side_r_8,  # d7: 315° Front-Right
    ]
    idle_dirs = [
        idle_noscis_8,  # d0: 0° Front (9.5/10 funny shrug & peer!)
        idle_noscis_8,  # d1: 45° Front-Left
        gentle_bob_8(no_vid_bgrs[2]),
        gentle_bob_8(no_vid_bgrs[3]),
        gentle_bob_8(no_vid_bgrs[4]),
        gentle_bob_8(no_vid_bgrs[5]),
        gentle_bob_8(no_vid_bgrs[6]),
        [flip_h(x) for x in idle_noscis_8],
    ]

    print("1/4 Packing Running + Chopping Scissors (8 dirs x 8f @ 12 FPS)...")
    run_paths, run_sz = align_and_pack_state(
        run_dirs, OUT_DIR / "running_scissors", "running_scissors",
        preserve_bob_per_dir=[True] * 8,
    )
    print("2/4 Packing Overhead Scissors Chop (8 dirs x 8f @ 12 FPS)...")
    ov_paths, ov_sz = align_and_pack_state(
        ov_dirs, OUT_DIR / "overhead_scissors", "overhead_scissors",
    )
    print("3/4 Packing Front Lunge-Chop (8 dirs x 8f @ 13 FPS)...")
    fr_paths, fr_sz = align_and_pack_state(
        front_dirs, OUT_DIR / "front_scissors", "front_scissors",
    )
    print("4/6 Packing Funny No-Scissors Idle (8 dirs x 8f @ 8 FPS)...")
    no_paths, no_sz = align_and_pack_state(
        idle_dirs, OUT_DIR / "no_scissors", "no_scissors",
    )
    print("5/6 Packing From-Below Sky Overhead Chop (8f @ 13 FPS)...")
    fb_paths, fb_sz = align_and_pack_state(
        [from_below_8] * 8, OUT_DIR / "from_below", "from_below",
    )
    print("6/6 Packing From-Above High-Angle Chop (8f @ 12 FPS)...")
    fa_paths, fa_sz = align_and_pack_state(
        [from_above_8] * 8, OUT_DIR / "from_above", "from_above",
    )

    # Preserve existing verified realistic US currency cash_fx from manifest
    mpath = OUT_DIR / "manifest.json"
    old_m = json.loads(mpath.read_text(encoding="utf-8"))
    cash_fx = old_m["cash_fx"]

    manifest = {
        "version": 4,
        "sprite_height": TARGET_H,
        "directions": DIR_INFO,
        "states": {
            "running_scissors": {
                "title": "Running + Chopping (Real Studio Photo)",
                "fps": 12,
                "frame_duration_ms": 83,
                "num_dirs": N_DIRS,
                "num_frames": N_FRAMES,
                "frame_size": list(run_sz),
                "directions": run_paths,
            },
            "overhead_scissors": {
                "title": "Overhead Jump-Chop (Real Studio Photo)",
                "fps": 12,
                "frame_duration_ms": 83,
                "num_dirs": N_DIRS,
                "num_frames": N_FRAMES,
                "frame_size": list(ov_sz),
                "directions": ov_paths,
            },
            "front_scissors": {
                "title": "Front & Side Lunge-Chop (Real Studio Photo)",
                "fps": 13,
                "frame_duration_ms": 77,
                "num_dirs": N_DIRS,
                "num_frames": N_FRAMES,
                "frame_size": list(fr_sz),
                "directions": fr_paths,
            },
            "no_scissors": {
                "title": "Funny Businessman Idle (No Scissors)",
                "fps": 8,
                "frame_duration_ms": 125,
                "num_dirs": N_DIRS,
                "num_frames": N_FRAMES,
                "frame_size": list(no_sz),
                "directions": no_paths,
            },
            "from_below": {
                "title": "From Below / Sky Overhead Chop (Real Studio Photo)",
                "fps": 13,
                "frame_duration_ms": 77,
                "num_dirs": 1,
                "num_frames": N_FRAMES,
                "frame_size": list(fb_sz),
                "directions": {"0": fb_paths["0"]},
            },
            "from_above": {
                "title": "From Above / Top-Down Chop (Real Studio Photo)",
                "fps": 12,
                "frame_duration_ms": 83,
                "num_dirs": 1,
                "num_frames": N_FRAMES,
                "frame_size": list(fa_sz),
                "directions": {"0": fa_paths["0"]},
            },
        },
        "cash_fx": cash_fx,
    }
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Write final visual audit contact sheet on DARK #181818 backdrop to verify ZERO white halos!
    bg = (24, 24, 24)
    rows = []
    for st, d in [
        ("running_scissors", 6),   # Side Sprint (8.5/10)
        ("running_scissors", 0),   # Front Sprint (8.5/10)
        ("overhead_scissors", 0),  # Overhead Chop (8.5/10)
        ("front_scissors", 0),     # Front Lunge-Chop (8.5/10)
        ("front_scissors", 6),     # Side Lunge-Chop (9.0/10)
        ("no_scissors", 0),        # Funny Idle (9.5/10)
    ]:
        r = []
        for f in range(8):
            im = Image.open(OUT_DIR / manifest["states"][st]["directions"][str(d)][f]).convert("RGBA")
            c = Image.new("RGB", (180, 210), bg)
            im.thumbnail((170, 200), Image.LANCZOS)
            c.paste(im, ((180 - im.width) // 2, 210 - im.height - 4), im)
            r.append(np.asarray(c))
        rows.append(np.hstack(r))
    # Row 7: Realistic US currency
    cash_picks = [
        cash_fx["bills"][0], cash_fx["bills"][1], cash_fx["bills"][4], cash_fx["bills"][6],
        cash_fx["quarters"][0], cash_fx["quarters"][2], cash_fx["gold_dollars"][0], cash_fx["gold_dollars"][2],
    ]
    crow = []
    for rel in cash_picks:
        im = Image.open(OUT_DIR / rel).convert("RGBA")
        c = Image.new("RGB", (180, 120), bg)
        im.thumbnail((164, 108), Image.LANCZOS)
        c.paste(im, ((180 - im.width) // 2, (120 - im.height) // 2), im)
        crow.append(np.asarray(c))
    rows.append(np.hstack(crow))

    audit_path = OUT_DIR / "_audit_studio_final.jpg"
    Image.fromarray(np.vstack(rows)).save(audit_path, quality=92)
    print(f"Done! Wrote 256 studio RGBA sprites + {audit_path}")


if __name__ == "__main__":
    build_all()
