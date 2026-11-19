"""Builds the 4 HD 8-direction Kyle Tillet projectile sprite sets, cash FX sprites,
clean studio portrait cutouts, and sprites/manifest.json.

Outputs to:
  C:\\Users\\qxdc\\.gemini\\antigravity\\brain\\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671\\scratch\\kyle_stage\\sprites\\

Sets produced:
  1. running_scissors/  (8 dirs x 6 frames = 48 RGBA PNGs, 192px tall)
  2. overhead_scissors/ (8 dirs x 4 snipping frames = 32 RGBA PNGs, 192px tall)
  3. front_scissors/    (8 dirs x 4 forward chop frames = 32 RGBA PNGs, 192px tall)
  4. no_scissors/       (8 dirs x 2 idle/look frames = 16 RGBA PNGs, 192px tall)
  5. cash_fx/           (4 dollar bill PNGs + 4 spinning gold coin PNGs)
  6. portraits/         (kyle_portrait_rgba.png, kyle_head_rgba.png, kyle_fullbody_rgba.png)
  7. manifest.json      (all states, directions, frame paths, timings)

Run with:
    python source/mm_tools/kyle_scissors/build_kyle_sprites.py
"""

import json
import math
import os
import struct
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PK3_PATH = os.path.join(REPO_ROOT, "bakersfield.pk3")
UPLOAD_DIR = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671\.user_uploaded"
)
OUT_DIR = (
    r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671"
    r"\scratch\kyle_stage\sprites"
)

VID_OVERHEAD = os.path.join(UPLOAD_DIR, "media_1795056597277_fa6b997e.mp4")
VID_FRONT = os.path.join(UPLOAD_DIR, "media_1795056597277_2a827670.mp4")
VID_NO_SCISSORS = os.path.join(UPLOAD_DIR, "media_1795056597278_66b2c783.mp4")
IMG_PORTRAIT = os.path.join(UPLOAD_DIR, "media_1795056507412_c9227b8c.jpg")
IMG_FULLBODY = os.path.join(UPLOAD_DIR, "media_1795056611778_b8a1f6c9.jpg")

TARGET_H = 192
N_DIRS = 8
DIR_INFO = [
    {"dir": 0, "angle_deg": 0, "label": "0° Front"},
    {"dir": 1, "angle_deg": 45, "label": "45° Front-Left"},
    {"dir": 2, "angle_deg": 90, "label": "90° Left Side"},
    {"dir": 3, "angle_deg": 135, "label": "135° Back-Left"},
    {"dir": 4, "angle_deg": 180, "label": "180° Back"},
    {"dir": 5, "angle_deg": 225, "label": "225° Back-Right"},
    {"dir": 6, "angle_deg": 270, "label": "270° Right Side"},
    {"dir": 7, "angle_deg": 315, "label": "315° Front-Right"},
]

# Empirically calibrated turnaround frame indices for 8 evenly spaced yaw directions
OVERHEAD_FRAME_IDXS = [0, 20, 38, 55, 72, 90, 104, 123]
FRONT_FRAME_IDXS = [0, 21, 36, 54, 72, 89, 103, 121]
NO_SCIS_FRAME_IDXS = [0, 16, 31, 49, 67, 85, 103, 121]


# ---------------------------------------------------------------------------
# Studio Off-White Background Keying + Despill
# ---------------------------------------------------------------------------
def key_studio_offwhite(bgr, is_fullbody=True):
    """Keys neutral off-white studio backdrop using Lab distance, border flood-fill,
    enclosed pocket detection, floor-shadow cleanup, and edge un-premultiply despill.
    """
    H, W = bgr.shape[:2]
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab).astype(np.float32)

    border_pts = np.concatenate(
        [
            lab[:24, :, :].reshape(-1, 3),
            lab[:, :16, :].reshape(-1, 3),
            lab[:, -16:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    neutral_border = border_pts[
        (border_pts[:, 0] > 195)
        & (np.hypot(border_pts[:, 1] - 128.0, border_pts[:, 2] - 128.0) < 10.0)
    ]
    global_bg = (
        np.median(neutral_border, axis=0)
        if len(neutral_border) > 50
        else np.array([224.0, 128.0, 131.0], np.float32)
    )

    if is_fullbody:
        margin = np.concatenate([lab[:, :18, :], lab[:, -18:, :]], axis=1)
        m_neutral = (margin[..., 0] > 185) & (
            np.hypot(margin[..., 1] - global_bg[1], margin[..., 2] - global_bg[2]) < 8.0
        )
        bg_row = np.repeat(global_bg[None, :], H, axis=0)
        for y in range(H):
            pts = margin[y][m_neutral[y]]
            if len(pts) >= 4:
                bg_row[y] = np.median(pts, axis=0)
        bg_row = cv2.GaussianBlur(bg_row[:, None, :], (1, 35), 0)[:, 0, :]
    else:
        bg_row = np.repeat(global_bg[None, :], H, axis=0)

    diff = lab - bg_row[:, None, :]
    d_l = np.abs(diff[..., 0])
    d_ab = np.hypot(diff[..., 1], diff[..., 2])
    d_lab = np.sqrt((d_l * 0.55) ** 2 + (d_ab * 1.8) ** 2)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.hypot(gx, gy)

    cand = (d_lab < 9.5) & (lab[..., 0] > 192) & (grad < 45.0)
    if is_fullbody:
        floor_zone = np.zeros((H, W), dtype=bool)
        floor_zone[int(H * 0.90) :, :] = True
        cand |= floor_zone & (d_ab < 5.5) & (lab[..., 0] > 165) & (d_l < 52.0) & (grad < 50.0)
        # Catch bright floor reflection slivers right along brown loafer soles
        cand |= floor_zone & (d_ab < 4.5) & (lab[..., 0] > 188)

    num_lbl, lbl, stats, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=8)
    border_lbls = (
        set(np.unique(lbl[0, :]))
        | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0]))
        | set(np.unique(lbl[:, -1]))
    )
    border_lbls.discard(0)
    bg_mask = np.isin(lbl, list(border_lbls))

    # Enclosed studio pockets (between arms & head, scissor rings, between legs, arm-hip gap)
    # Require area >= 450 so small bright specular highlights on steel blades stay solid!
    for lid in range(1, num_lbl):
        if lid in border_lbls or lid == 0:
            continue
        area = stats[lid, cv2.CC_STAT_AREA]
        if area < 450:
            continue
        comp = lbl == lid
        mean_l = float(np.mean(lab[comp, 0]))
        mean_dab = float(np.mean(d_ab[comp]))
        mean_dlab = float(np.mean(d_lab[comp]))
        if mean_l > 210 and mean_dab < 3.8 and mean_dlab < 8.5:
            bg_mask |= comp

    fg_raw = ~bg_mask
    n_fg, flbl, fstats, _ = cv2.connectedComponentsWithStats(fg_raw.astype(np.uint8), connectivity=8)
    if n_fg > 1:
        areas = fstats[1:, cv2.CC_STAT_AREA]
        main_fg = 1 + int(np.argmax(areas))
        fg_mask = flbl == main_fg
    else:
        fg_mask = fg_raw

    # Fill tiny (<55px) interior specular pinholes on steel blades
    inv_fg = (~fg_mask).astype(np.uint8)
    n_h, hlbl, hstats, _ = cv2.connectedComponentsWithStats(inv_fg, connectivity=8)
    for hid in range(1, n_h):
        if hstats[hid, cv2.CC_STAT_AREA] < 55:
            fg_mask[hlbl == hid] = True

    dist = cv2.distanceTransform(fg_mask.astype(np.uint8), cv2.DIST_L2, 3)
    alpha = np.where(fg_mask, 1.0, 0.0).astype(np.float32)

    edge = fg_mask & (dist <= 2.2)
    ramp = np.clip((d_lab - 5.5) / 10.0, 0.0, 1.0)
    alpha[edge] = np.minimum(1.0, np.where(dist[edge] <= 1.1, ramp[edge], 0.6 + 0.4 * ramp[edge]))
    alpha[alpha < 0.06] = 0.0

    bg_bgr = cv2.cvtColor(np.clip(bg_row[:, None, :], 0, 255).astype(np.uint8), cv2.COLOR_Lab2BGR).astype(
        np.float32
    )
    bgr_f = bgr.astype(np.float32)
    semi = (alpha > 0.0) & (alpha < 0.98) & (dist <= 2.5)
    a_s = np.maximum(0.20, alpha[semi])[:, None]
    bg_b = np.broadcast_to(bg_bgr, bgr_f.shape)[semi]
    bgr_f[semi] = np.clip((bgr_f[semi] - (1.0 - a_s) * bg_b) / a_s, 0, 255)

    rgb = bgr_f[..., ::-1]
    rgba = np.dstack(
        [
            np.clip(np.round(rgb[..., 0]), 0, 255).astype(np.uint8),
            np.clip(np.round(rgb[..., 1]), 0, 255).astype(np.uint8),
            np.clip(np.round(rgb[..., 2]), 0, 255).astype(np.uint8),
            np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
        ]
    )
    return Image.fromarray(rgba, "RGBA")


def read_video_frames(path, indices):
    """Reads specified frame indices from an mp4 video as BGR arrays."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    out = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError(f"Failed reading frame {idx} from {path}")
        out.append(frame)
    cap.release()
    return out


# ---------------------------------------------------------------------------
# Geometric Helpers for Articulation & Alignment
# ---------------------------------------------------------------------------
def rotate_layer_around_pivot(im, pivot_xy, angle_deg, dx=0.0, dy=0.0):
    """Rotates an RGBA image around pivot_xy by angle_deg (CCW in image space) + shift."""
    w, h = im.size
    px, py = pivot_xy
    rad = math.radians(angle_deg)
    ca, sa = math.cos(rad), math.sin(rad)
    tx, ty = px + dx, py + dy
    a, b = ca, sa
    c = px - a * tx - b * ty
    d, e = -sa, ca
    f = py - d * tx - e * ty
    return im.transform((w, h), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)


def draw_snip_glint(canvas_im, center_xy, radius=26, intensity=1.0):
    """Draws a crisp metallic scissor-clash star glint on an RGBA canvas."""
    cx, cy = int(round(center_xy[0])), int(round(center_xy[1]))
    ov = Image.new("RGBA", canvas_im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    r1 = int(round(radius * 1.1))
    r2 = int(round(radius * 0.35))
    a_core = int(round(235 * intensity))
    a_glow = int(round(145 * intensity))
    # 4-point star polygon
    pts = [
        (cx, cy - r1),
        (cx + r2 // 2, cy - r2 // 2),
        (cx + r1, cy),
        (cx + r2 // 2, cy + r2 // 2),
        (cx, cy + r1),
        (cx - r2 // 2, cy + r2 // 2),
        (cx - r1, cy),
        (cx - r2 // 2, cy - r2 // 2),
    ]
    dr.polygon(pts, fill=(220, 245, 255, a_glow))
    pts_inner = [
        (cx, cy - r1 * 0.65),
        (cx + r2 // 3, cy - r2 // 3),
        (cx + r1 * 0.65, cy),
        (cx + r2 // 3, cy + r2 // 3),
        (cx, cy + r1 * 0.65),
        (cx - r2 // 3, cy + r2 // 3),
        (cx - r1 * 0.65, cy),
        (cx - r2 // 3, cy - r2 // 3),
    ]
    dr.polygon(pts_inner, fill=(255, 255, 255, a_core))
    return Image.alpha_composite(canvas_im, ov)


def normalize_and_resize_sequence(frames_grid, target_h=TARGET_H, pad_x=10, pad_top=6, pad_bot=6):
    """Finds shared tight bbox across all (dir, frame) images in a state, anchors bottom,
    and resizes every frame uniformly to (target_w, target_h) preserving aspect ratio.
    """
    x0, y0, x1, y1 = 10**9, 10**9, 0, 0
    for row in frames_grid:
        for im in row:
            arr = np.array(im)
            ys, xs = np.nonzero(arr[..., 3] > 20)
            if len(xs) == 0:
                continue
            x0 = min(x0, int(xs.min()))
            y0 = min(y0, int(ys.min()))
            x1 = max(x1, int(xs.max()))
            y1 = max(y1, int(ys.max()))
    src_w, src_h = frames_grid[0][0].size
    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_top)
    x1 = min(src_w, x1 + pad_x + 1)
    y1 = min(src_h, y1 + pad_bot + 1)

    cw, ch = x1 - x0, y1 - y0
    target_w = max(2, int(round(cw * (target_h / float(ch)))))
    if target_w % 2:
        target_w += 1

    out_grid = []
    for row in frames_grid:
        out_row = []
        for im in row:
            cropped = im.crop((x0, y0, x1, y1)).resize((target_w, target_h), Image.LANCZOS)
            out_row.append(cropped)
        out_grid.append(out_row)
    return out_grid, (target_w, target_h)


# ---------------------------------------------------------------------------
# 1. Running Scissors (from bakersfield.pk3 progs/fr_scissors.spr32)
# ---------------------------------------------------------------------------
def build_running_scissors(out_dir):
    """Extracts 8-dir x 6-frame running-with-scissors animation from bakersfield.pk3
    progs/fr_scissors.spr32 (frames 8..55), anchors feet uniformly, and resizes to 192px tall.
    """
    with zipfile.ZipFile(PK3_PATH, "r") as zf:
        data = zf.read("progs/fr_scissors.spr32")
    if data[:4] != b"IDSP":
        raise RuntimeError("Invalid SPR32 magic in progs/fr_scissors.spr32")

    pos = 36
    raw_frames = []
    nframes = struct.unpack("<i", data[24:28])[0]
    for _ in range(nframes):
        ox, oy, fw, fh = struct.unpack("<iiii", data[pos + 4 : pos + 20])
        pos += 20
        rgba = data[pos : pos + fw * fh * 4]
        pos += fw * fh * 4
        raw_frames.append((ox, oy, fw, fh, Image.frombytes("RGBA", (fw, fh), rgba)))

    run_frames = raw_frames[8:56]
    min_x = min(ox for ox, _, _, _, _ in run_frames)
    max_x = max(ox + fw for ox, _, fw, _, _ in run_frames)
    max_top = max(oy for _, oy, _, _, _ in run_frames)
    max_bot = max(fh - oy for _, oy, _, fh, _ in run_frames)

    canv_w = (max_x - min_x) + 8
    canv_h = (max_top + max_bot) + 8
    target_w = max(2, int(round(canv_w * (TARGET_H / float(canv_h)))))
    if target_w % 2:
        target_w += 1

    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(6):
            ox, oy, fw, fh, fim = run_frames[d * 6 + f]
            canvas = Image.new("RGBA", (canv_w, canv_h), (0, 0, 0, 0))
            px = (ox - min_x) + 4
            py = (max_top - oy) + 4
            canvas.paste(fim, (px, py))
            resized = canvas.resize((target_w, TARGET_H), Image.LANCZOS)
            rel = f"running_scissors/d{d}_f{f}.png"
            resized.save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, (target_w, TARGET_H)


# ---------------------------------------------------------------------------
# 2. Overhead Scissors (8 dirs x 4 snipping frames)
# ---------------------------------------------------------------------------
def find_overhead_pivot(arr):
    """Locates the scissor pivot (px, py) in the overhead region (y=130..255)."""
    alpha = arr[..., 3] > 30
    best_y, best_x, best_w = 188, 384, 999
    for y in range(135, 245):
        xs = np.nonzero(alpha[y, 260:520])[0]
        if len(xs) < 12:
            continue
        # Look for single narrow merged waist of the scissor X (around pivot bolt)
        span = int(xs[-1] - xs[0])
        # Check if contiguous (no big background gap inside [xs[0], xs[-1]])
        row_seg = alpha[y, 260 + xs[0] : 260 + xs[-1] + 1]
        if np.mean(row_seg) > 0.72 and span < best_w:
            best_w = span
            best_y = y
            best_x = 260 + int(round((xs[0] + xs[-1]) * 0.5))
    return float(best_x), float(best_y)


def build_overhead_scissors(out_dir):
    """Slices 8 directions from overhead turnaround mp4 and articulates 4 overhead snip frames."""
    bgr_list = read_video_frames(VID_OVERHEAD, OVERHEAD_FRAME_IDXS)
    grid_raw = []

    for d, bgr in enumerate(bgr_list):
        base_im = key_studio_offwhite(bgr, is_fullbody=True)
        arr = np.array(base_im)
        H, W = arr.shape[:2]
        px, py = find_overhead_pivot(arr)

        # Split above pivot into blades (y < py + 4) and body+hands below (y >= py - 6)
        blade_cutoff_y = int(round(py)) + 4
        # Body mask (keep everything below pivot + circular bolt hub)
        yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        hub_dist = np.hypot(xx - px, yy - py)
        body_mask = (yy >= int(round(py)) - 2) & (arr[..., 3] > 0)
        body_arr = np.zeros_like(arr)
        body_arr[body_mask] = arr[body_mask]
        body_im = Image.fromarray(body_arr, "RGBA")

        # Left & right blade masks above pivot (plus small hub overlap)
        blades_zone = (yy < blade_cutoff_y) & (arr[..., 3] > 0)

        # Detect whether the two blades are side-by-side or edge-on (d=2, d=6)
        is_side_profile = d in (2, 6)
        if is_side_profile:
            # In side profile, blades overlap edge-on; clone blade for near/far shearing
            blade_arr = np.zeros_like(arr)
            blade_arr[blades_zone] = arr[blades_zone]
            blade_im = Image.fromarray(blade_arr, "RGBA")
            blade_dark_arr = blade_arr.copy()
            blade_dark_arr[..., :3] = np.clip(blade_dark_arr[..., :3].astype(np.float32) * 0.80, 0, 255).astype(
                np.uint8
            )
            blade_dark_im = Image.fromarray(blade_dark_arr, "RGBA")
            configs = [
                # (angle_L, angle_R, body_dy, scale_y, glint)
                (-16.0, 16.0, -3.0, 1.006, 0.0),
                (-7.0, 7.0, 0.0, 1.000, 0.0),
                (0.0, 0.0, 4.0, 0.992, 1.0),
                (-9.0, 9.0, 1.0, 0.998, 0.0),
            ]
            row = []
            for a_l, a_r, bdy, scy, glint in configs:
                comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                b_far = rotate_layer_around_pivot(blade_dark_im, (px, py), a_r, dy=bdy)
                b_near = rotate_layer_around_pivot(blade_im, (px, py), a_l, dy=bdy)
                body_shifted = body_im.transform(
                    (W, H), Image.AFFINE, (1, 0, 0, 0, 1.0 / scy, -bdy - (H - H / scy)), resample=Image.BICUBIC
                )
                comp.alpha_composite(b_far)
                comp.alpha_composite(b_near)
                comp.alpha_composite(body_shifted)
                if glint > 0:
                    comp = draw_snip_glint(comp, (px, max(16.0, py - 115.0)), radius=28, intensity=glint)
                row.append(comp)
            grid_raw.append(row)
        else:
            # Measure average X offset of left & right blade tips from pivot to compute exact closure angle
            top_band = blades_zone & (yy < py - 45)
            l_mask = blades_zone & ((xx < px) | (hub_dist <= 10))
            r_mask = blades_zone & ((xx >= px) | (hub_dist <= 10))

            def blade_angle(mask):
                pts_y, pts_x = np.nonzero(mask & top_band)
                if len(pts_x) < 10:
                    return 0.0
                dx_m = float(np.mean(pts_x) - px)
                dy_m = float(py - np.mean(pts_y))
                return math.degrees(math.atan2(dx_m, max(10.0, dy_m)))

            ang_l = blade_angle(l_mask)  # negative (left of vertical)
            ang_r = blade_angle(r_mask)  # positive (right of vertical)

            # Rotate CCW in image space: positive angle rotates counter-clockwise (right blade goes toward vertical!)
            # Wait: check sign in rotate_layer_around_pivot:
            # a=cos, b=sin, d=-sin, e=cos -> x' = x*cos - y*sin? Actually inverse map: x = x'*cos + y'*sin -> forward x' = x*cos - y*sin!
            # Wait: for y' = -dy (above pivot, y - py < 0), forward x' = -(-dy)*sin = +dy*sin!
            # So positive angle_deg moves points ABOVE pivot to the RIGHT (+x), negative moves them LEFT (-x)!
            close_l = -ang_l * 0.92  # ang_l < 0 -> positive angle moves left blade RIGHT toward vertical!
            close_r = -ang_r * 0.92  # ang_r > 0 -> negative angle moves right blade LEFT toward vertical!

            left_arr = np.zeros_like(arr)
            left_arr[l_mask] = arr[l_mask]
            right_arr = np.zeros_like(arr)
            right_arr[r_mask] = arr[r_mask]
            left_im = Image.fromarray(left_arr, "RGBA")
            right_im = Image.fromarray(right_arr, "RGBA")

            # Keep Kyle's entire head, arms, torso & legs solid (unsplit!) with subtle bounce/crunch
            # so no seam/tear ever cuts through his head or hair.
            configs = [
                # (t_close, body_dy, scale_y, glint)
                (-0.42, -3.0, 1.006, 0.0),  # f0: wide open anticipation
                (0.05, 0.0, 1.000, 0.0),     # f1: closing
                (1.00, 4.0, 0.992, 1.0),     # f2: SLAM SHUT!
                (0.32, 1.0, 0.998, 0.0),     # f3: rebound
            ]
            row = []
            for tc, bdy, scy, glint in configs:
                comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                body_s = body_im.transform(
                    (W, H),
                    Image.AFFINE,
                    (1, 0, 0, 0, 1.0 / scy, -bdy - (H - H / scy)),
                    resample=Image.BICUBIC,
                )
                bl_l = rotate_layer_around_pivot(left_im, (px, py), close_l * tc, dx=0.0, dy=bdy)
                bl_r = rotate_layer_around_pivot(right_im, (px, py), close_r * tc, dx=0.0, dy=bdy)

                comp.alpha_composite(body_s)
                comp.alpha_composite(bl_l)
                comp.alpha_composite(bl_r)
                if glint > 0:
                    comp = draw_snip_glint(comp, (px, max(16.0, py - 125.0)), radius=30, intensity=glint)
                row.append(comp)
            grid_raw.append(row)

    grid_final, frame_size = normalize_and_resize_sequence(grid_raw, target_h=TARGET_H)
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(4):
            rel = f"overhead_scissors/d{d}_f{f}.png"
            grid_final[d][f].save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, frame_size


# ---------------------------------------------------------------------------
# 3. Front Scissors (8 dirs x 4 forward chopping snip frames)
# ---------------------------------------------------------------------------
def build_front_scissors(out_dir):
    """Slices 8 directions from front-scissors mp4 and articulates 4 forward chopping snip frames."""
    bgr_list = read_video_frames(VID_FRONT, FRONT_FRAME_IDXS)
    grid_raw = []

    # Per-direction protruding blade exit line (outside hip/hand silhouette)
    dir_specs = {
        0: ("right", 468.0, 560.0),
        1: ("right", 448.0, 560.0),
        2: ("side", 345.0, 560.0),
        3: ("left", 320.0, 560.0),
        4: ("left", 292.0, 560.0),
        5: ("back_right", 318.0, 560.0),
        6: ("side", 435.0, 560.0),
        7: ("right", 482.0, 560.0),
    }

    ankle_piv = (384.0, 1080.0)

    def lean_offset(pt_xy, lean_deg):
        rad = math.radians(lean_deg)
        ca, sa = math.cos(rad), math.sin(rad)
        rx, ry = pt_xy[0] - ankle_piv[0], pt_xy[1] - ankle_piv[1]
        # Inverse map in rotate_layer_around_pivot: forward x' = px + rx*ca - ry*sa, y' = py + rx*sa + ry*ca
        nx = ankle_piv[0] + rx * ca - ry * sa
        ny = ankle_piv[1] + rx * sa + ry * ca
        return nx - pt_xy[0], ny - pt_xy[1]

    for d, bgr in enumerate(bgr_list):
        base_im = key_studio_offwhite(bgr, is_fullbody=True)
        arr = np.array(base_im)
        H, W = arr.shape[:2]
        yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        mode, split_x, py_approx = dir_specs[d]
        rb_diff = arr[..., 0].astype(np.int16) - arr[..., 2].astype(np.int16)
        not_khaki = rb_diff < 30

        if mode in ("right", "left"):
            protrude = (xx >= split_x) if mode == "right" else (xx <= split_x)
            blade_mask = (arr[..., 3] > 20) & protrude & not_khaki & (yy >= 470) & (yy <= 735)
            # Keep only real blade components (>= 60 px) so stray edge specks stay with body
            nb, blbl, bstats, _ = cv2.connectedComponentsWithStats(blade_mask.astype(np.uint8), connectivity=8)
            clean_blade = np.zeros_like(blade_mask)
            for bid in range(1, nb):
                if bstats[bid, cv2.CC_STAT_AREA] >= 60:
                    clean_blade |= blbl == bid
            blade_mask = clean_blade

            body_mask = (arr[..., 3] > 0) & (~blade_mask)
            body_arr = np.zeros_like(arr)
            body_arr[body_mask] = arr[body_mask]
            body_im = Image.fromarray(body_arr, "RGBA")

            cols = np.nonzero(np.any(blade_mask, axis=0))[0]
            upper_mask = np.zeros_like(blade_mask)
            lower_mask = np.zeros_like(blade_mask)
            root_ys_u, root_ys_l = [], []
            for cx in cols:
                ys_c = np.nonzero(blade_mask[:, cx])[0]
                if len(ys_c) < 2:
                    continue
                diffs = np.diff(ys_c)
                if len(diffs) > 0 and np.max(diffs) >= 4:
                    g_idx = int(np.argmax(diffs))
                    mid_y = 0.5 * (ys_c[g_idx] + ys_c[g_idx + 1])
                else:
                    mid_y = py_approx + (cx - split_x) * (0.08 if mode == "right" else -0.08)
                um = blade_mask[:, cx] & (yy[:, cx] <= mid_y)
                lm = blade_mask[:, cx] & (yy[:, cx] > mid_y)
                upper_mask[:, cx] = um
                lower_mask[:, cx] = lm
                if abs(cx - split_x) <= 18:
                    if np.any(um):
                        root_ys_u.append(float(np.mean(np.nonzero(um)[0])))
                    if np.any(lm):
                        root_ys_l.append(float(np.mean(np.nonzero(lm)[0])))

            piv_x = split_x + (-6.0 if mode == "right" else 6.0)
            piv_yu = float(np.mean(root_ys_u)) if root_ys_u else py_approx - 10.0
            piv_yl = float(np.mean(root_ys_l)) if root_ys_l else py_approx + 12.0
            piv_ym = 0.5 * (piv_yu + piv_yl)

            up_blade_arr = np.zeros_like(arr)
            up_blade_arr[upper_mask] = arr[upper_mask]
            lo_blade_arr = np.zeros_like(arr)
            lo_blade_arr[lower_mask] = arr[lower_mask]
            up_b_im = Image.fromarray(up_blade_arr, "RGBA")
            lo_b_im = Image.fromarray(lo_blade_arr, "RGBA")

            sgn = 1.0 if mode == "right" else -1.0
            configs = [
                # (upper_deg, lower_deg, lean_deg, glint)
                (-11.0 * sgn, 11.0 * sgn, -0.8 * sgn, 0.0),   # f0: wide open jaws
                (2.0 * sgn, -3.0 * sgn, 0.3 * sgn, 0.0),      # f1: closing fast
                (9.0 * sgn, -16.0 * sgn, 1.5 * sgn, 1.0),     # f2: CHOP SHUT + lean!
                (-3.0 * sgn, 4.0 * sgn, 0.4 * sgn, 0.0),      # f3: rebound
            ]
            row = []
            for au, al, lean_deg, glint in configs:
                comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                body_s = rotate_layer_around_pivot(body_im, ankle_piv, lean_deg)
                ldx, ldy = lean_offset((piv_x, piv_ym), lean_deg)
                tuck = -3.0 * sgn
                bl_u = rotate_layer_around_pivot(up_b_im, (piv_x, piv_ym), au + lean_deg, dx=ldx + tuck, dy=ldy)
                bl_l = rotate_layer_around_pivot(lo_b_im, (piv_x, piv_ym), al + lean_deg, dx=ldx + tuck, dy=ldy)
                comp.alpha_composite(bl_u)
                comp.alpha_composite(bl_l)
                comp.alpha_composite(body_s)
                if glint > 0:
                    gx_p = piv_x + 150.0 * sgn + ldx
                    gy_p = piv_ym + 8.0 + ldy
                    comp = draw_snip_glint(comp, (gx_p, gy_p), radius=30, intensity=glint)
                row.append(comp)
            grid_raw.append(row)

        elif mode == "back_right":
            # d5: protruding steel blade tips on left (x <= 318) and steel handle rings on right (x >= 468)
            tip_mask = (arr[..., 3] > 20) & (xx <= split_x) & not_khaki & (yy >= 490) & (yy <= 620)
            ring_mask = (arr[..., 3] > 20) & (xx >= 468) & not_khaki & (yy >= 480) & (yy <= 700)
            body_mask = (arr[..., 3] > 0) & (~tip_mask) & (~ring_mask)

            tip_arr = np.zeros_like(arr)
            tip_arr[tip_mask] = arr[tip_mask]
            ring_arr = np.zeros_like(arr)
            ring_arr[ring_mask] = arr[ring_mask]
            body_arr = np.zeros_like(arr)
            body_arr[body_mask] = arr[body_mask]

            tip_im = Image.fromarray(tip_arr, "RGBA")
            ring_im = Image.fromarray(ring_arr, "RGBA")
            body_im = Image.fromarray(body_arr, "RGBA")

            configs = [
                (14.0, -10.0, 0.8, 0.0),
                (4.0, -3.0, -0.3, 0.0),
                (-12.0, 10.0, -1.4, 1.0),
                (5.0, -4.0, -0.4, 0.0),
            ]
            row = []
            for at, ar, lean_deg, glint in configs:
                comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                body_s = rotate_layer_around_pivot(body_im, ankle_piv, lean_deg)
                dx_t, dy_t = lean_offset((split_x + 6.0, 550.0), lean_deg)
                dx_r, dy_r = lean_offset((465.0, 575.0), lean_deg)
                t_im = rotate_layer_around_pivot(tip_im, (split_x + 6.0, 550.0), at + lean_deg, dx=dx_t, dy=dy_t)
                r_im = rotate_layer_around_pivot(ring_im, (465.0, 575.0), ar + lean_deg, dx=dx_r, dy=dy_r)
                comp.alpha_composite(t_im)
                comp.alpha_composite(r_im)
                comp.alpha_composite(body_s)
                if glint > 0:
                    comp = draw_snip_glint(comp, (305.0 + dx_t, 550.0 + dy_t), radius=24, intensity=glint)
                row.append(comp)
            grid_raw.append(row)

        else:
            # Side profile (d2 Left, d6 Right): ankle-pivoted whole-body forward chop lean + glint (zero seam!)
            sgn = -1.0 if d == 2 else 1.0
            configs = [
                (-0.9 * sgn, 0.0),   # f0: wind-up lean back
                (0.4 * sgn, 0.0),    # f1: driving forward
                (1.6 * sgn, 1.0),    # f2: CHOP LUNGE + steel glint!
                (0.5 * sgn, 0.0),    # f3: rebound
            ]
            row = []
            for lean_deg, glint in configs:
                comp = rotate_layer_around_pivot(base_im, ankle_piv, lean_deg)
                if glint > 0:
                    ldx, ldy = lean_offset((318.0 if d == 2 else 452.0, 568.0), lean_deg)
                    gx_p = (318.0 if d == 2 else 452.0) + ldx
                    gy_p = 568.0 + ldy
                    comp = draw_snip_glint(comp, (gx_p, gy_p), radius=28, intensity=glint)
                row.append(comp)
            grid_raw.append(row)

    grid_final, frame_size = normalize_and_resize_sequence(grid_raw, target_h=TARGET_H)
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(4):
            rel = f"front_scissors/d{d}_f{f}.png"
            grid_final[d][f].save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, frame_size


# ---------------------------------------------------------------------------
# 4. No Scissors (8 dirs x 2 idle/look frames)
# ---------------------------------------------------------------------------
def build_no_scissors(out_dir):
    """Slices 8 directions from no-scissors mp4 and creates 2 subtle idle/look frames per dir."""
    bgr_list = read_video_frames(VID_NO_SCISSORS, NO_SCIS_FRAME_IDXS)
    grid_raw = []

    for d, bgr in enumerate(bgr_list):
        f0 = key_studio_offwhite(bgr, is_fullbody=True)
        arr = np.array(f0)
        H, W = arr.shape[:2]
        yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")

        # Frame 1: subtle breathing chest/shoulder lift + slight attentive head-tilt look
        legs_mask = (yy >= 540) & (arr[..., 3] > 0)
        # Extend torso behind waist down to y=565 so breathing lift never opens a belt seam!
        torso_mask = (yy >= 235) & (yy < 565) & (arr[..., 3] > 0)
        head_mask = (yy < 245) & (arr[..., 3] > 0)

        legs_arr = np.zeros_like(arr)
        legs_arr[legs_mask] = arr[legs_mask]
        torso_arr = np.zeros_like(arr)
        torso_arr[torso_mask] = arr[torso_mask]
        head_arr = np.zeros_like(arr)
        head_arr[head_mask] = arr[head_mask]

        legs_im = Image.fromarray(legs_arr, "RGBA")
        torso_im = Image.fromarray(torso_arr, "RGBA")
        head_im = Image.fromarray(head_arr, "RGBA")

        # Find head center x for clean neck pivot
        hy, hx = np.nonzero(head_arr[..., 3] > 30)
        head_px = float(np.mean(hx)) if len(hx) else 384.0
        look_deg = 3.2 if (d % 2 == 0) else -3.2
        look_dx = 3.0 if (d % 2 == 0) else -3.0

        f1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        torso_s = torso_im.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, 5.0), resample=Image.BICUBIC)
        head_s = rotate_layer_around_pivot(head_im, (head_px, 235.0), look_deg, dx=look_dx, dy=-5.0)
        f1.alpha_composite(legs_im)
        f1.alpha_composite(torso_s)
        f1.alpha_composite(head_s)

        grid_raw.append([f0, f1])

    grid_final, frame_size = normalize_and_resize_sequence(grid_raw, target_h=TARGET_H)
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for d in range(N_DIRS):
        paths[str(d)] = []
        for f in range(2):
            rel = f"no_scissors/d{d}_f{f}.png"
            grid_final[d][f].save(os.path.join(out_dir, f"d{d}_f{f}.png"))
            paths[str(d)].append(rel)
    return paths, frame_size


# ---------------------------------------------------------------------------
# 5. Cash FX: Dollar Bills (Front / Back / Bent1 / Bent2) & Gold Coin (4 spins)
# ---------------------------------------------------------------------------
def paint_flat_bill(is_back=False):
    """Paints a crisp 320x160 supersampled US-style $100 Bakersfield bill."""
    W, H = 320, 160
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)

    # Outer parchment paper rect with crisp 2px rounded border
    dr.rounded_rectangle((4, 4, W - 5, H - 5), radius=8, fill=(214, 230, 200, 255), outline=(28, 72, 42, 255), width=4)
    dr.rounded_rectangle((12, 12, W - 13, H - 13), radius=4, fill=(224, 237, 212, 255), outline=(34, 96, 54, 255), width=3)
    dr.rectangle((20, 20, W - 21, H - 21), outline=(70, 130, 86, 255), width=2)

    # Fine guilloche engraving lines
    for x in range(26, W - 26, 8):
        dr.line([(x, 22), (x, H - 23)], fill=(182, 208, 174, 255), width=1)
    for y in range(26, H - 26, 8):
        dr.line([(22, y), (W - 23, y)], fill=(192, 216, 184, 180), width=1)

    font_big = ImageFont.load_default(size=24)
    font_med = ImageFont.load_default(size=15)
    font_sm = ImageFont.load_default(size=10)

    if not is_back:
        # Four corners "100"
        for cx, cy in ((26, 20), (W - 68, 20), (26, H - 46), (W - 68, H - 46)):
            dr.text((cx, cy), "100", fill=(22, 76, 40, 255), font=font_big)
        # Center portrait oval with stylized "$"
        dr.ellipse((112, 26, 208, 134), fill=(198, 220, 188, 255), outline=(24, 82, 44, 255), width=4)
        dr.ellipse((120, 34, 200, 126), outline=(56, 118, 72, 255), width=2)
        dr.text((144, 46), "$", fill=(20, 74, 38, 255), font=ImageFont.load_default(size=56))
        dr.text((222, 68), "BK-50%", fill=(32, 92, 50, 255), font=font_med)
        dr.text((34, 70), "50% CUT", fill=(32, 92, 50, 255), font=font_med)
    else:
        for cx, cy in ((26, 20), (W - 68, 20), (26, H - 46), (W - 68, H - 46)):
            dr.text((cx, cy), "100", fill=(26, 84, 44, 255), font=font_big)
        dr.rounded_rectangle((78, 38, W - 79, H - 39), radius=10, fill=(188, 214, 178, 255), outline=(26, 82, 44, 255), width=3)
        dr.text((104, 48), "BAKERSFIELD", fill=(20, 72, 36, 255), font=font_med)
        dr.text((100, 70), "$100 NOTE", fill=(20, 72, 36, 255), font=font_big)
        dr.text((116, 102), "SCISSOR FUND", fill=(38, 96, 56, 255), font=font_sm)

    return im.resize((160, 80), Image.LANCZOS)


def warp_bent_bill(flat_im, phase=0.0, amp=11.0, tilt_deg=8.0):
    """Warps a flat dollar bill with sinusoidal flutter + 3D paper shading."""
    src = np.array(flat_im)
    H, W = src.shape[:2]
    pad_y = 22
    out_h = H + pad_y * 2
    out = np.zeros((out_h, W, 4), dtype=np.uint8)

    xs = np.arange(W, dtype=np.float32)
    u = xs / max(1.0, W - 1.0)
    # Smooth S-curve vertical flutter + subtle perspective pinch
    wave = amp * np.sin(u * math.pi * 2.0 + phase)
    slope = amp * (2.0 * math.pi / W) * np.cos(u * math.pi * 2.0 + phase)
    shade = np.clip(1.0 + slope * 1.15, 0.72, 1.18)

    for x in range(W):
        dy = float(wave[x]) + pad_y
        s = float(shade[x])
        for y in range(H):
            oy = int(round(y + dy))
            if 0 <= oy < out_h and src[y, x, 3] > 0:
                px = src[y, x].astype(np.float32)
                px[:3] = np.clip(px[:3] * s, 0, 255)
                out[oy, x] = px.astype(np.uint8)

    # Fill any 1px vertical interpolation gap via light vertical morphological close on non-zero rows
    im = Image.fromarray(out, "RGBA")
    if tilt_deg != 0.0:
        im = im.rotate(tilt_deg, resample=Image.BICUBIC, expand=False)
    return im.resize((160, 96), Image.LANCZOS)


def paint_gold_coin(angle_deg):
    """Renders a gleaming 96x96 RGBA spinning gold coin at yaw angle_deg (0, 45, 82, 135)."""
    S = 192  # 2x supersampled -> 96x96
    rad = math.radians(angle_deg)
    cos_a = abs(math.cos(rad))
    sin_a = math.sin(rad)

    cx, cy = S * 0.5, S * 0.5
    R = 76.0
    rx = max(4.0, R * cos_a)
    ry = R
    thick = 14.0 * abs(sin_a)

    yy, xx = np.meshgrid(np.arange(S, dtype=np.float32), np.arange(S, dtype=np.float32), indexing="ij")
    rgba = np.zeros((S, S, 4), dtype=np.float32)

    # 1. Extruded 3D reeded rim behind front face
    if thick > 0.8:
        side_dir = 1.0 if math.cos(rad) >= 0 else -1.0
        n_steps = max(4, int(math.ceil(thick * 2)))
        for st in np.linspace(thick, 0.0, n_steps):
            dx = side_dir * st
            nx = (xx - (cx + dx)) / rx
            ny = (yy - cy) / ry
            d = np.hypot(nx, ny)
            inside = d <= 1.0
            # Vertical reeding grooves along rim
            reed = 0.85 + 0.15 * np.sin((yy - cy) * 0.9)
            rim_shade = (0.58 + 0.35 * (1.0 - np.abs(ny) * 0.55)) * reed
            col = np.stack([242.0 * rim_shade, 178.0 * rim_shade, 36.0 * rim_shade], axis=-1)
            rgba[inside, :3] = col[inside]
            rgba[inside, 3] = 255.0

    # 2. Front coin face ellipse
    nx = (xx - cx) / rx
    ny = (yy - cy) / ry
    d = np.hypot(nx, ny)
    face = d <= 1.0

    # Specular metallic gold lighting
    ang_pos = np.arctan2(ny, nx)
    spec = np.exp(-(((nx + 0.35) ** 2 + (ny + 0.35) ** 2) * 2.8)) * 0.55
    sheen = 0.82 + 0.18 * np.cos(ang_pos * 2.0 + 0.8) + spec
    # Outer raised rim (0.82 <= d <= 1.0)
    is_rim = face & (d >= 0.82)
    is_ring = face & (d >= 0.74) & (d < 0.82)

    gold_r = np.clip(252.0 * sheen, 0, 255)
    gold_g = np.clip(206.0 * sheen, 0, 255)
    gold_b = np.clip(58.0 * (sheen * 0.85 + spec * 1.1), 0, 255)

    gold_r[is_rim] = np.clip(gold_r[is_rim] * 1.08, 0, 255)
    gold_g[is_rim] = np.clip(gold_g[is_rim] * 1.03, 0, 255)
    gold_r[is_ring] *= 0.74
    gold_g[is_ring] *= 0.70
    gold_b[is_ring] *= 0.60

    # Soft AA on outer ellipse edge
    edge_a = np.clip((1.0 - d) * min(rx, ry) * 0.8, 0.0, 1.0) * 255.0
    face_soft = d <= 1.03
    # Blend front face over extruded rim
    rgba[face, 0] = gold_r[face]
    rgba[face, 1] = gold_g[face]
    rgba[face, 2] = gold_b[face]
    rgba[face, 3] = np.maximum(rgba[face, 3], edge_a[face])

    base_im = Image.fromarray(np.clip(np.round(rgba), 0, 255).astype(np.uint8), "RGBA")

    # Emboss crisp "$" emblem on face (squashed horizontally by cos_a!)
    if cos_a > 0.22:
        sym = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        dr = ImageDraw.Draw(sym)
        fnt = ImageFont.load_default(size=96)
        dr.text((68, 36), "$", fill=(168, 108, 12, 230), font=fnt)
        dr.text((66, 34), "$", fill=(255, 240, 145, 245), font=fnt)
        squashed_w = max(8, int(round(S * cos_a)))
        sym_sq = sym.resize((squashed_w, S), Image.LANCZOS)
        sym_canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        sym_canvas.paste(sym_sq, ((S - squashed_w) // 2, 0))
        base_im = Image.alpha_composite(base_im, sym_canvas)

    return base_im.resize((96, 96), Image.LANCZOS)


def build_cash_fx(out_dir):
    """Builds transparent RGBA PNGs for dollar bills and spinning gold coins."""
    os.makedirs(out_dir, exist_ok=True)
    bill_front = paint_flat_bill(is_back=False)
    bill_back = paint_flat_bill(is_back=True)
    bill_bent1 = warp_bent_bill(bill_front, phase=0.4, amp=11.0, tilt_deg=7.0)
    bill_bent2 = warp_bent_bill(bill_back, phase=2.6, amp=12.0, tilt_deg=-8.0)

    bill_front.save(os.path.join(out_dir, "bill_front.png"))
    bill_back.save(os.path.join(out_dir, "bill_back.png"))
    bill_bent1.save(os.path.join(out_dir, "bill_bent1.png"))
    bill_bent2.save(os.path.join(out_dir, "bill_bent2.png"))

    coin_angles = [0.0, 45.0, 80.0, 135.0]
    coin_paths = []
    for i, ang in enumerate(coin_angles):
        cim = paint_gold_coin(ang)
        cim.save(os.path.join(out_dir, f"coin_{i}.png"))
        coin_paths.append(f"cash_fx/coin_{i}.png")

    return {
        "dollar_bill": {
            "fps": 8,
            "frame_duration_ms": 125,
            "variants": {
                "front": "cash_fx/bill_front.png",
                "back": "cash_fx/bill_back.png",
                "bent1": "cash_fx/bill_bent1.png",
                "bent2": "cash_fx/bill_bent2.png",
            },
            "frames": [
                "cash_fx/bill_front.png",
                "cash_fx/bill_bent1.png",
                "cash_fx/bill_back.png",
                "cash_fx/bill_bent2.png",
            ],
        },
        "gold_coin": {
            "fps": 10,
            "frame_duration_ms": 100,
            "frames": coin_paths,
        },
    }


# ---------------------------------------------------------------------------
# 6. Clean Studio Portrait / Head / Full-Body Cutouts
# ---------------------------------------------------------------------------
def build_portraits(out_dir):
    """Generates clean transparent RGBA cutouts from uploaded portrait & fullbody photos."""
    os.makedirs(out_dir, exist_ok=True)

    p_bgr = cv2.imread(IMG_PORTRAIT)
    p_rgba = key_studio_offwhite(p_bgr, is_fullbody=False)
    p_rgba.save(os.path.join(out_dir, "kyle_portrait_rgba.png"))

    # Head-only cutout (dilate blue-shirt mask by 4px so zero collar edge halo survives!)
    arr = np.array(p_rgba).copy()
    H, W = arr.shape[:2]
    r = arr[..., 0].astype(np.int16)
    g = arr[..., 1].astype(np.int16)
    b = arr[..., 2].astype(np.int16)
    is_blue = ((arr[..., 3] > 0) & ((b - r) > 22) & ((b - g) > 10)).astype(np.uint8)
    is_blue_dil = cv2.dilate(is_blue, np.ones((9, 9), np.uint8), iterations=1) > 0
    arr[is_blue_dil] = 0
    # Keep only largest connected component (head+neck)
    fg_h = (arr[..., 3] > 20).astype(np.uint8)
    nh, hlbl, hstats, _ = cv2.connectedComponentsWithStats(fg_h, connectivity=8)
    if nh > 1:
        main_h = 1 + int(np.argmax(hstats[1:, cv2.CC_STAT_AREA]))
        arr[hlbl != main_h] = 0
    ys, xs = np.nonzero(arr[..., 3] > 15)
    head_im = Image.fromarray(arr, "RGBA").crop(
        (max(0, int(xs.min()) - 8), max(0, int(ys.min()) - 8), min(W, int(xs.max()) + 9), min(H, int(ys.max()) + 9))
    )
    head_im.save(os.path.join(out_dir, "kyle_head_rgba.png"))

    # Full-body cutout
    fb_bgr = cv2.imread(IMG_FULLBODY)
    fb_rgba = key_studio_offwhite(fb_bgr, is_fullbody=True)
    fb_arr = np.array(fb_rgba)
    ys, xs = np.nonzero(fb_arr[..., 3] > 15)
    fb_crop = fb_rgba.crop(
        (
            max(0, int(xs.min()) - 10),
            max(0, int(ys.min()) - 10),
            min(fb_rgba.width, int(xs.max()) + 11),
            min(fb_rgba.height, int(ys.max()) + 11),
        )
    )
    fb_crop.save(os.path.join(out_dir, "kyle_fullbody_rgba.png"))

    return {
        "portrait": "portraits/kyle_portrait_rgba.png",
        "head": "portraits/kyle_head_rgba.png",
        "fullbody": "portraits/kyle_fullbody_rgba.png",
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("1/5 Building running_scissors (8 dirs x 6 frames)...")
    run_paths, run_size = build_running_scissors(os.path.join(OUT_DIR, "running_scissors"))

    print("2/5 Building overhead_scissors (8 dirs x 4 snip frames)...")
    over_paths, over_size = build_overhead_scissors(os.path.join(OUT_DIR, "overhead_scissors"))

    print("3/5 Building front_scissors (8 dirs x 4 chop frames)...")
    front_paths, front_size = build_front_scissors(os.path.join(OUT_DIR, "front_scissors"))

    print("4/5 Building no_scissors (8 dirs x 2 idle/look frames)...")
    idle_paths, idle_size = build_no_scissors(os.path.join(OUT_DIR, "no_scissors"))

    print("5/5 Painting cash_fx & portrait cutouts + writing manifest.json...")
    cash_info = build_cash_fx(os.path.join(OUT_DIR, "cash_fx"))
    portrait_info = build_portraits(os.path.join(OUT_DIR, "portraits"))

    manifest = {
        "version": 1,
        "sprite_height": TARGET_H,
        "directions": DIR_INFO,
        "states": {
            "running_scissors": {
                "title": "Running w/ Scissors",
                "fps": 12,
                "frame_duration_ms": 83,
                "num_dirs": N_DIRS,
                "num_frames": 6,
                "frame_size": list(run_size),
                "directions": run_paths,
            },
            "overhead_scissors": {
                "title": "Overhead Scissors Chop",
                "fps": 10,
                "frame_duration_ms": 100,
                "num_dirs": N_DIRS,
                "num_frames": 4,
                "frame_size": list(over_size),
                "directions": over_paths,
            },
            "front_scissors": {
                "title": "Front Scissors Chop",
                "fps": 10,
                "frame_duration_ms": 100,
                "num_dirs": N_DIRS,
                "num_frames": 4,
                "frame_size": list(front_size),
                "directions": front_paths,
            },
            "no_scissors": {
                "title": "No Scissors Idle / Wander",
                "fps": 3,
                "frame_duration_ms": 333,
                "num_dirs": N_DIRS,
                "num_frames": 2,
                "frame_size": list(idle_size),
                "directions": idle_paths,
            },
        },
        "cash_fx": cash_info,
        "portraits": portrait_info,
    }

    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)
    print(f"Done! Manifest -> {manifest_path}")


if __name__ == "__main__":
    main()
