"""Anatomical 3D Turntable Human Rider Reconstructor & Part-Aware Cardinal Texture Baker.

Builds smooth, watertight, anatomically rounded 3D human meshes + crisp 1024x1024 photographic
textures for BakersfieldQuake (DarkPlaces engine):
  1. Suit Rider  ('vid1_suit')  -> mm_suit_human_uv.npz + progs/mm_suit_human.png
  2. Squat Rider ('vid2_squat') -> mm_squat_human_uv.npz + progs/mm_squat_human.png + progs/mm_squat_human_grin.png

Key visual-craft guarantees:
  - Smooth 3D Signed-Distance-Field (SDF) anatomical sculpts fitted to exact studio cardinal blueprints
    (eliminates boxy 45-deg visual-hull corners, swiss-cheese limb holes, and chopped shoes)
  - Rig-tire + hair-crown 4-DOF camera calibration + sub-pixel 2D head-silhouette lock
  - Strictly cardinal, semantic-part-aware photographic projection (Front 0 deg, Rear 180 deg, and
    occlusion-guarded Profile +-90 deg ONLY — zero oblique views -> zero ghost double-faces,
    zero collar-on-chin bleed, zero tire-on-pants bleed, and zero shoe-on-blazer bleed)
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mm_riders_rig as rig
import human_sculpt_3d as hs

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
REMESH_SCRIPT = os.path.join(HERE, "blender_remesh_uv.py")


# --------------------------------------------------------------------------- Turntable Angle & Camera Calibration
SUIT_LANDMARKS = [
    (16,  -42.0,  992.0, 650.0),
    (22,  -52.0, 1012.0, 658.0),
    (41,  -90.0, 1064.0, 662.0),
    (58, -133.0, 1004.0, 650.0),
    (76, -180.0,  984.0, 640.0),
    (98, -225.0,  922.0, 636.0),
    (120,   0.0,  978.0, 644.0),
]

SQUAT_LANDMARKS = [
    (0,   -10.0, 894.0, 692.0),
    (4,    -9.0, 890.0, 692.0),
    (18,    0.0, 864.0, 692.0),
    (34,  +38.0, 856.0, 698.0),
    (48,  +90.0, 782.0, 742.0),
    (75, +180.0, 878.0, 686.0),
    (98, +270.0, 924.0, 692.0),
    (144,  -5.0, 876.0, 690.0),
]


def interp_landmarks(landmarks, f):
    for fi, phi, cx, cy in landmarks:
        if fi == f:
            return phi, cx, cy
    lms = sorted(landmarks, key=lambda x: x[0])
    if f <= lms[0][0]:
        return lms[0][1], lms[0][2], lms[0][3]
    if f >= lms[-1][0]:
        return lms[-1][1], lms[-1][2], lms[-1][3]
    for (f0, p0, x0, y0), (f1, p1, x1, y1) in zip(lms, lms[1:]):
        if f0 <= f <= f1:
            t = (f - f0) / float(max(1, f1 - f0))
            return p0 + (p1 - p0) * t, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    return 0.0, 960.0, 640.0


def project_pts(X, Y, Z, phi_deg, elev_deg, f_px, d_cam, cx, cy, z_piv=18.0):
    phi = math.radians(phi_deg)
    el = math.radians(elev_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    ce, se = math.cos(el), math.sin(el)
    Zp = Z - z_piv
    x_cam = -X * sp + Y * cp
    y_up = -X * cp * se - Y * sp * se + Zp * ce
    depth = d_cam + (-X * cp * ce - Y * sp * ce - Zp * se)
    scale = f_px / np.maximum(depth, 10.0)
    u = cx + x_cam * scale
    v = cy - y_up * scale
    return u, v, depth


def normalized_y_up(X, Y, Z, phi_deg, elev_deg, f_px_base, d_cam, z_piv=18.0):
    phi = math.radians(phi_deg)
    el = math.radians(elev_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    ce, se = math.cos(el), math.sin(el)
    Zp = Z - z_piv
    y_up = -X * cp * se - Y * sp * se + Zp * ce
    depth = d_cam + (-X * cp * ce - Y * sp * ce - Zp * se)
    return f_px_base * (y_up / np.maximum(depth, 10.0))


def view_ray_into_scene(phi_deg, elev_deg):
    phi = math.radians(phi_deg)
    el = math.radians(elev_deg)
    return np.array([
        -math.cos(phi) * math.cos(el),
        -math.sin(phi) * math.cos(el),
        -math.sin(el),
    ], dtype=np.float32)


# --------------------------------------------------------------------------- Video Loading, Clean Masking & Halo-Free Bleed
def load_selected_frames(vid_path, frame_idxs):
    cap = cv2.VideoCapture(vid_path)
    wanted = set(frame_idxs)
    bg_samples = []
    frames = {}
    i = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        if i % 3 == 0:
            bg_samples.append(cv2.resize(rgb, (rgb.shape[1] // 2, rgb.shape[0] // 2)))
        if i in wanted:
            frames[i] = rgb
        i += 1
    cap.release()
    bg_half = np.percentile(np.stack(bg_samples, axis=0), 96, axis=0).astype(np.uint8)
    h, w, _ = next(iter(frames.values())).shape
    bg = cv2.resize(bg_half, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    return frames, bg


def segment_foreground(rgb, bg, kind):
    h, w, _ = rgb.shape
    rf = rgb.astype(np.float32)
    diff = np.max(np.abs(rf - bg), axis=2)
    lum = rf.mean(axis=2)
    sat = rf.max(axis=2) - rf.min(axis=2)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    bg_gray = bg.mean(axis=2)
    loc_rng = ndimage.maximum_filter(gray, size=9) - ndimage.minimum_filter(gray, size=9)
    bg_rng = ndimage.maximum_filter(bg_gray, size=9) - ndimage.minimum_filter(bg_gray, size=9)
    tex_diff = loc_rng - bg_rng

    yy = np.arange(h)[:, None]
    y_split = int(h * (0.60 if kind == "suit" else 0.61))
    upper_zone = yy <= y_split
    floor_zone = ~upper_zone

    fg_upper = upper_zone & ((diff > 10.5) | (tex_diff > 6.5) | (sat > 10.0) | (lum < 198.0))
    fg_lower = floor_zone & ((diff > 24.0) | (lum < 152.0) | (sat > 17.0))
    shadow = floor_zone & (sat < 16.0) & (lum > 104.0) & (diff < 120.0)
    if kind == "squat":
        spark_floor = (yy > int(h * 0.75)) & (lum > 180.0) & (diff < 72.0)
        shadow = shadow | spark_floor
    fg_lower = fg_lower & (~shadow)

    fg = fg_upper | fg_lower
    struct = ndimage.generate_binary_structure(2, 2)
    fg = ndimage.binary_closing(fg, structure=struct, iterations=4)

    holes = ndimage.binary_fill_holes(fg) & (~fg)
    hlbl, nh = ndimage.label(holes)
    if nh > 0:
        for hid in range(1, nh + 1):
            hm = (hlbl == hid)
            sz = int(hm.sum())
            hy, _ = np.nonzero(hm)
            if sz < 650:
                fg |= hm
            elif kind == "squat" and hy.max() < int(0.54 * h) and sz < 18000:
                fg |= hm
            elif hy.min() > int(0.50 * h):
                perim = ndimage.binary_dilation(hm, iterations=3) & (~hm) & fg
                if perim.any() and float(lum[perim].mean()) < 88.0:
                    fg |= hm

    fg = ndimage.binary_opening(fg, structure=struct, iterations=2)
    lbl, n_lbl = ndimage.label(fg)
    if n_lbl > 0:
        sizes = ndimage.sum(fg, lbl, range(1, n_lbl + 1))
        keep_lbls = [i + 1 for i, sz in enumerate(sizes) if sz > 4000]
        fg = np.isin(lbl, keep_lbls)
    return fg


def bleed_foreground_colors(rgb, fg_mask, erode_px=5):
    m_inner = ndimage.binary_erosion(fg_mask, iterations=erode_px)
    if not m_inner.any():
        m_inner = fg_mask
    _, (iy, ix) = ndimage.distance_transform_edt(~m_inner, return_indices=True)
    return rgb[iy, ix]


def bilinear_sample_rgb(img_float, u, v):
    H, W, _ = img_float.shape
    uc = np.clip(u, 0.0, W - 1.001)
    vc = np.clip(v, 0.0, H - 1.001)
    x0 = np.floor(uc).astype(np.int32)
    y0 = np.floor(vc).astype(np.int32)
    x1 = np.minimum(x0 + 1, W - 1)
    y1 = np.minimum(y0 + 1, H - 1)
    fx = (uc - x0)[:, None]
    fy = (vc - y0)[:, None]
    c00 = img_float[y0, x0]
    c10 = img_float[y0, x1]
    c01 = img_float[y1, x0]
    c11 = img_float[y1, x1]
    return (1.0 - fx) * (1.0 - fy) * c00 + fx * (1.0 - fy) * c10 + (1.0 - fx) * fy * c01 + fx * fy * c11


# --------------------------------------------------------------------------- Boundary Quads from 3D Voxel Grid
def voxel_boundary_quads(occ, X, Y, Z):
    p = np.pad(occ, 1, mode="constant", constant_values=False)
    NX, NY, NZ = p.shape
    dx = float(X[1] - X[0])
    dy = float(Y[1] - Y[0])
    dz = float(Z[1] - Z[0])

    quads = []
    axis_configs = [
        (0, (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        (1, (0, 1, 0), (0, 0, 1), (1, 0, 0)),
        (2, (0, 0, 1), (1, 0, 0), (0, 1, 0)),
    ]
    for axis, _, d_u, d_v in axis_configs:
        a = np.take(p, range(0, p.shape[axis] - 1), axis=axis)
        b = np.take(p, range(1, p.shape[axis]), axis=axis)
        f_pos = np.argwhere(a & (~b))
        if len(f_pos) > 0:
            base = f_pos.copy()
            base[:, axis] += 1
            quads.append(np.stack([base, base + d_u, base + d_u + d_v, base + d_v], axis=1))
        f_neg = np.argwhere((~a) & b)
        if len(f_neg) > 0:
            base = f_neg.copy()
            base[:, axis] += 1
            quads.append(np.stack([base, base + d_v, base + d_u + d_v, base + d_u], axis=1))

    quads = np.concatenate(quads, axis=0)
    corners = quads.reshape(-1, 3)
    key = (corners[:, 0].astype(np.int64) * (NY + 1) + corners[:, 1].astype(np.int64)) * (NZ + 1) + corners[:, 2].astype(np.int64)
    uk, inv = np.unique(key, return_inverse=True)
    rem, cz = np.divmod(uk, NZ + 1)
    cx, cy = np.divmod(rem, NY + 1)

    vx = (X[0] - 1.5 * dx) + cx * dx
    vy = (Y[0] - 1.5 * dy) + cy * dy
    vz = (Z[0] - 1.5 * dz) + cz * dz
    verts = np.stack([vx, vy, vz], axis=1).astype(np.float32)
    faces = inv.reshape(-1, 4).astype(np.int32)
    return verts, faces


# --------------------------------------------------------------------------- Exact Rig+Human Camera Calibration & Head Lock
def calibrate_frame_pose(rgb, fg_mask, phi_nom, sub_pts, f_px_base, d_cam, elev_deg):
    H, W, _ = rgb.shape
    ys, _ = np.nonzero(fg_mask)
    y_top = float(ys.min())

    lum = rgb.mean(axis=2)
    low_tire = fg_mask & (lum < 70.0) & (np.arange(H)[:, None] > int(0.70 * H))
    ty_low, tx_low = np.nonzero(low_tire)
    cx_tire = 0.5 * (float(tx_low.min()) + float(tx_low.max())) if len(tx_low) > 20 else 0.5 * W
    y_bot = float(np.percentile(ty_low, 99.5)) if len(ty_low) > 20 else float(ys.max())

    F_DS = 4
    hs_d, ws_d = H // F_DS, W // F_DS
    m_sm = cv2.resize(fg_mask.astype(np.uint8), (ws_d, hs_d), interpolation=cv2.INTER_NEAREST) > 0

    best_iou = -1.0
    best_pose = [phi_nom, cx_tire, H * 0.58, 1.0]

    for dp in (-2.0, -1.0, 0.0, +1.0, +2.0):
        phi = phi_nom + dp
        v0_all = normalized_y_up(sub_pts[:, 0], sub_pts[:, 1], sub_pts[:, 2], phi, elev_deg, f_px_base, d_cam)
        v0_top, v0_bot = float(v0_all.max()), float(v0_all.min())
        y_bot_eff = y_bot if y_bot < H - 8 else (H + 8.0)
        f_est = (y_bot_eff - y_top) / max(10.0, v0_top - v0_bot)

        for sm in (0.96, 0.98, 1.00, 1.02, 1.04):
            f_sc = float(np.clip(f_est * sm, 0.88, 1.16))
            cy_b = y_top + f_sc * v0_top
            u0, v0, _ = project_pts(sub_pts[:, 0], sub_pts[:, 1], sub_pts[:, 2], phi, elev_deg, f_px_base * f_sc, d_cam, cx_tire, cy_b)
            us = np.rint(u0 / F_DS).astype(np.int32)
            vs = np.rint(v0 / F_DS).astype(np.int32)
            ok = (us >= 0) & (us < ws_d) & (vs >= 0) & (vs < hs_d)
            pm = np.zeros((hs_d, ws_d), dtype=bool)
            pm[vs[ok], us[ok]] = True
            pm = ndimage.binary_closing(pm, iterations=3)

            for dy_s in range(-3, 4):
                ry = np.roll(pm, dy_s, axis=0)
                for dx_s in range(-14, 15):
                    sh = np.roll(ry, dx_s, axis=1)
                    inter = int(np.logical_and(sh, m_sm).sum())
                    uni = int(np.logical_or(sh, m_sm).sum())
                    iou = inter / float(max(1, uni))
                    if iou > best_iou:
                        best_iou = iou
                        best_pose = [phi, cx_tire + dx_s * F_DS, cy_b + dy_s * F_DS, f_sc]

    return best_pose, best_iou


def refine_head_2d_offset(rgb, fg_mask, head_pts, phi, cx, cy, f_eff, d_cam, elev_deg, max_du=8, max_dv=6):
    """Finds subtle pixel shift (du, dv) that locks 3D upper hair dome onto dark hair pixels."""
    H, W = fg_mask.shape
    hair_3d = head_pts[head_pts[:, 2] > 43.0]
    if len(hair_3d) < 50:
        return 0.0, 0.0
    uh, vh, _ = project_pts(hair_3d[:, 0], hair_3d[:, 1], hair_3d[:, 2], phi, elev_deg, f_eff, d_cam, cx, cy)
    v_cut = int(np.max(vh)) + 8
    yy = np.arange(H)[:, None]
    xx = np.arange(W)[None, :]
    u_mid = float(np.median(uh))
    lum = rgb.mean(axis=2)
    m_hair_2d = fg_mask & (lum < 82.0) & (yy <= v_cut) & (np.abs(xx - u_mid) <= (78 + max_du))
    if m_hair_2d.sum() < 200:
        return 0.0, 0.0

    pm = np.zeros((H, W), dtype=bool)
    ui = np.clip(np.rint(uh).astype(np.int32), 0, W - 1)
    vi = np.clip(np.rint(vh).astype(np.int32), 0, H - 1)
    pm[vi, ui] = True
    pm = ndimage.binary_closing(pm, iterations=3) & (yy <= v_cut)

    best_iou, best_du, best_dv = -1.0, 0.0, 0.0
    for dv in range(-max_dv, max_dv + 1, 2):
        ry = np.roll(pm, dv, axis=0)
        for du in range(-max_du, max_du + 1, 2):
            sh = np.roll(ry, du, axis=1)
            inter = int(np.logical_and(sh, m_hair_2d).sum())
            uni = int(np.logical_or(sh, m_hair_2d).sum())
            iou = inter / float(max(1, uni))
            if iou > best_iou:
                best_iou, best_du, best_dv = iou, float(du), float(dv)
    return best_du, best_dv


# --------------------------------------------------------------------------- Main Reconstruction & Part-Aware Baking
def reconstruct_rider(kind, vid_path, out_dir, progs_dir):
    print(f"\n==================== RECONSTRUCTING {kind.upper()} RIDER ====================")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(progs_dir, exist_ok=True)

    # 1. Build Smooth Watertight 3D Anatomical Human Sculpt + Blender 5.2 Remesh & Contiguous Smart UV
    uv_npz = os.path.join(out_dir, f"mm_{kind}_human_uv.npz")
    sculpt_mtime = os.path.getmtime(hs.__file__)
    if os.path.isfile(uv_npz) and os.path.getmtime(uv_npz) >= sculpt_mtime:
        print(f"  Using up-to-date {os.path.basename(uv_npz)}")
    else:
        occ, X, Y, Z = hs.build_human_sdf_occupancy(kind, vox_step=0.23)
        print(f"  Anatomical 3D SDF occupancy: {int(occ.sum()):,} voxels")

        b_verts, b_faces = voxel_boundary_quads(occ, X, Y, Z)
        raw_npz = os.path.join(out_dir, f"mm_{kind}_raw_quads.npz")
        np.savez_compressed(raw_npz, verts=b_verts, faces=b_faces)

        remesh_vox = 0.28
        tri_budget = 3450
        cmd = [BLENDER_EXE, "-b", "-P", REMESH_SCRIPT, "--", raw_npz, uv_npz, str(remesh_vox), str(tri_budget)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        for line in res.stdout.splitlines():
            if "BLENDER_REMESH_UV" in line:
                print(" ", line)

    mesh_uv = np.load(uv_npz)
    VP = mesh_uv["verts"]
    VN_SM = mesh_uv["norms_smooth"]
    TV = mesh_uv["tris"]
    TUV = mesh_uv["tri_uv"]

    # 2. Load Cardinal & Verification Frames + Calibrate Rig-Locked Cameras
    if kind == "suit":
        frame_nominals = {
            120:   0.0,   # Exact Front
            41:  -90.0,   # Exact Right Profile
            76: -180.0,   # Exact Rear
            22:  -52.0,   # Verification Oblique
            98: -225.0,   # Verification Left Oblique
        }
        f_px_base, d_cam, elev_deg = 5250.0, 295.0, 4.6
    else:
        frame_nominals = {
            18:    0.0,   # Exact Serious Front (Skin 0)
            0:   -10.0,   # Crisp Joyful Grin Front (Skin 1)
            48:  +90.0,   # Exact Port Profile
            75: +180.0,   # Exact Rear
            98: +270.0,   # Exact Starboard Profile
            34:  +38.0,   # Verification Oblique
        }
        f_px_base, d_cam, elev_deg = 5800.0, 295.0, 4.6

    needed_frames = sorted(frame_nominals.keys())
    frames_rgb, bg = load_selected_frames(vid_path, needed_frames)
    H, W, _ = next(iter(frames_rgb.values())).shape

    rig_pts = rig.sample_rig_zbuffer_points(kind)
    # Dense triangle surface samples on human mesh + rig for sub-pixel Z-buffering
    tri_A, tri_B, tri_C = VP[TV[:, 0]], VP[TV[:, 1]], VP[TV[:, 2]]
    h_dense = [VP, (tri_A + tri_B + tri_C) / 3.0, 0.5 * (tri_A + tri_B), 0.5 * (tri_B + tri_C), 0.5 * (tri_C + tri_A)]
    for u_b, v_b in ((0.2, 0.2), (0.6, 0.2), (0.2, 0.6), (0.33, 0.5), (0.5, 0.33)):
        h_dense.append((1.0 - u_b - v_b) * tri_A + u_b * tri_B + v_b * tri_C)
    h_dense_pts = np.vstack(h_dense)
    h_dense_pids = hs.classify_points_part_id(kind, h_dense_pts)

    calib_sub_pts = np.vstack([rig_pts[::4], h_dense_pts[::4]])
    head_dense_pts = h_dense_pts[h_dense_pids == hs.PART_HEAD]

    masks_fg = {}
    masks_inner = {}
    bled_rgb = {}
    cam_pose = {}
    head_shift = {}

    for fi in needed_frames:
        rgb_f = frames_rgb[fi]
        m = segment_foreground(rgb_f, bg, kind)
        masks_fg[fi] = m
        rf = rgb_f.astype(np.float32)
        diff_bg = np.max(np.abs(rf - bg), axis=2)
        lum_f = rf.mean(axis=2)
        sat_f = rf.max(axis=2) - rf.min(axis=2)
        gray_f = cv2.cvtColor(rgb_f, cv2.COLOR_RGB2GRAY).astype(np.float32)
        loc_rng = ndimage.maximum_filter(gray_f, size=7) - ndimage.minimum_filter(gray_f, size=7)
        cyc_wall = (diff_bg < 14.0) & (lum_f > 204.0) & (sat_f < 12.0) & (loc_rng < 10.0)
        deep_interior = ndimage.binary_erosion(m, iterations=7)
        m_in = ndimage.binary_erosion(m, iterations=2) & (~(cyc_wall & (~deep_interior)))
        masks_inner[fi] = m_in
        bled_rgb[fi] = bleed_foreground_colors(rgb_f, m_in, erode_px=3).astype(np.float32)

        pose, iou = calibrate_frame_pose(rgb_f, m, frame_nominals[fi], calib_sub_pts, f_px_base, d_cam, elev_deg)
        cam_pose[fi] = pose
        phi, cx, cy, f_sc = pose
        if kind == "squat" and fi == 0:
            du_h, dv_h = refine_head_2d_offset(rgb_f, m, head_dense_pts, 0.0, cx, cy, f_px_base * f_sc, d_cam, elev_deg, max_du=28, max_dv=10)
        elif fi in (120, 76, 18, 0, 75):
            du_h, dv_h = refine_head_2d_offset(rgb_f, m, head_dense_pts, phi, cx, cy, f_px_base * f_sc, d_cam, elev_deg)
        else:
            du_h, dv_h = 0.0, 0.0
        head_shift[fi] = (du_h, dv_h)
        print(f"  Calibrated f={fi:3d}: phi={phi:6.1f}, cx={cx:6.1f}, cy={cy:6.1f}, f_sc={f_sc:.3f}, IoU={iou:.3f}, head_shift=({du_h:+.0f},{dv_h:+.0f})")

    pose_json = os.path.join(out_dir, f"mm_{kind}_cam_poses.json")
    with open(pose_json, "w", encoding="ascii") as fh:
        json.dump({str(k): [round(float(x), 4) for x in v] for k, v in cam_pose.items()}, fh, indent=2)

    # 3. Rasterize 1024x1024 UV Texels -> 3D (P, N, PID)
    TS = 1024
    TUV_px = TUV * TS
    PP, NN, PX, PY = [], [], [], []
    for t in range(len(TV)):
        a, b, c = TUV_px[t]
        x0, y0 = int(math.floor(min(a[0], b[0], c[0]))) - 1, int(math.floor(min(a[1], b[1], c[1]))) - 1
        x1, y1 = int(math.ceil(max(a[0], b[0], c[0]))) + 1, int(math.ceil(max(a[1], b[1], c[1]))) + 1
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, TS), min(y1, TS)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        v0, v1 = b - a, c - a
        d00 = float(v0[0] * v0[0] + v0[1] * v0[1])
        d01 = float(v0[0] * v1[0] + v0[1] * v1[1])
        d11 = float(v1[0] * v1[0] + v1[1] * v1[1])
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-10:
            continue
        px_, py_ = gx - a[0], gy - a[1]
        d20 = px_ * v0[0] + py_ * v0[1]
        d21 = px_ * v1[0] + py_ * v1[1]
        l1 = (d11 * d20 - d01 * d21) / den
        l2 = (d00 * d21 - d01 * d20) / den
        l0 = 1.0 - l1 - l2
        ins = (l0 >= -0.04) & (l1 >= -0.04) & (l2 >= -0.04)
        if not ins.any():
            continue
        l0c, l1c, l2c = np.clip(l0[ins], 0.0, 1.0), np.clip(l1[ins], 0.0, 1.0), np.clip(l2[ins], 0.0, 1.0)
        ls = np.maximum(l0c + l1c + l2c, 1e-6)
        l0c, l1c, l2c = l0c / ls, l1c / ls, l2c / ls
        ia, ib, ic = TV[t]
        PP.append(l0c[:, None] * VP[ia] + l1c[:, None] * VP[ib] + l2c[:, None] * VP[ic])
        NN.append(l0c[:, None] * VN_SM[ia] + l1c[:, None] * VN_SM[ib] + l2c[:, None] * VN_SM[ic])
        PX.append(gx[ins].astype(np.int32))
        PY.append((TS - 1) - gy[ins].astype(np.int32))

    P = np.concatenate(PP, axis=0)
    N = np.concatenate(NN, axis=0)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    PX = np.concatenate(PX, axis=0)
    PY = np.concatenate(PY, axis=0)
    PID = hs.classify_points_part_id(kind, P)
    print(f"  Rasterized {len(P):,} UV texels across {len(np.unique(PID))} anatomical parts")

    # Helper to build 2D Z-buffer for any subset of 3D points in frame fi
    ZF = 3
    w_zb, h_zb = (W + ZF - 1) // ZF, (H + ZF - 1) // ZF

    def make_zbuf(pts_3d, fi, guard_cells=1):
        phi, cx, cy, f_sc = cam_pose[fi]
        us, vs, ds = project_pts(pts_3d[:, 0], pts_3d[:, 1], pts_3d[:, 2], phi, elev_deg, f_px_base * f_sc, d_cam, cx, cy)
        usi = (us / ZF).astype(np.int32)
        vsi = (vs / ZF).astype(np.int32)
        ok = (usi >= 0) & (usi < w_zb) & (vsi >= 0) & (vsi < h_zb)
        zb = np.full((h_zb, w_zb), 1e9, dtype=np.float32)
        np.minimum.at(zb, (vsi[ok], usi[ok]), ds[ok])
        if guard_cells > 0:
            zb = ndimage.minimum_filter(zb, size=2 * guard_cells + 1)
        return zb

    # 4. Part-Aware Cardinal Photographic Texture Baker
    def bake_cardinal_atlas(out_base_name, use_grin_head=False):
        acc = np.zeros((len(P), 3), dtype=np.float64)
        wsum = np.zeros(len(P), dtype=np.float64)

        Nx, Ny, Nz = N[:, 0], N[:, 1], N[:, 2]
        Px, Py, Pz = P[:, 0], P[:, 1], P[:, 2]

        def add_view_contrib(fi, mask_texels, weight_vec, P_query=None, block_zbs=(), lum_range=None, color_fn=None, apply_head_shift=False, phi_override=None):
            idx = np.nonzero(mask_texels & (weight_vec > 1e-5))[0]
            if len(idx) == 0:
                return
            phi, cx, cy, f_sc = cam_pose[fi]
            phi_eff = phi if phi_override is None else phi_override
            f_eff = f_px_base * f_sc
            pts = P[idx] if P_query is None else P_query[idx]
            ut, vt, dt = project_pts(pts[:, 0], pts[:, 1], pts[:, 2], phi_eff, elev_deg, f_eff, d_cam, cx, cy)
            if apply_head_shift:
                du_h, dv_h = head_shift[fi]
                ut = ut + du_h
                vt = vt + dv_h

            uti = np.clip(np.rint(ut).astype(np.int32), 0, W - 1)
            vti = np.clip(np.rint(vt).astype(np.int32), 0, H - 1)
            in_bounds = (ut >= 0.0) & (ut < W - 1) & (vt >= 0.0) & (vt < H - 1)
            vis = in_bounds & masks_inner[fi][vti, uti]

            uzb = np.clip((ut / ZF).astype(np.int32), 0, w_zb - 1)
            vzb = np.clip((vt / ZF).astype(np.int32), 0, h_zb - 1)
            for b_zb, tol in block_zbs:
                vis &= ~(b_zb[vzb, uzb] < (dt - tol))

            sampled = bilinear_sample_rgb(bled_rgb[fi], ut, vt)
            if lum_range is not None:
                slum = sampled.mean(axis=1)
                vis &= (slum >= lum_range[0]) & (slum <= lum_range[1])
            if color_fn is not None:
                vis &= color_fn(sampled)

            w = weight_vec[idx] * vis.astype(np.float64)
            acc[idx] += sampled.astype(np.float64) * w[:, None]
            wsum[idx] += w

        if kind == "suit":
            zb_rig_120 = make_zbuf(rig_pts, 120, guard_cells=1)
            zb_rig_76 = make_zbuf(rig_pts, 76, guard_cells=1)
            zb_rig_41 = make_zbuf(rig_pts, 41, guard_cells=2)

            legs_shoes_pts = h_dense_pts[np.isin(h_dense_pids, [hs.PART_LEG_R, hs.PART_LEG_L, hs.PART_SHOE_R, hs.PART_SHOE_L])]
            shoes_pts = h_dense_pts[np.isin(h_dense_pids, [hs.PART_SHOE_R, hs.PART_SHOE_L])]
            arm_r_pts = h_dense_pts[h_dense_pids == hs.PART_ARM_R]

            zb_legs_120 = make_zbuf(legs_shoes_pts, 120, guard_cells=2)
            zb_legs_76 = make_zbuf(legs_shoes_pts, 76, guard_cells=2)
            zb_shoes_120 = make_zbuf(shoes_pts, 120, guard_cells=2)
            zb_armr_41 = make_zbuf(arm_r_pts, 41, guard_cells=2)

            is_blazer_tan = lambda c: ((c[:, 0] - c[:, 2]) >= 18.0) & (c.mean(axis=1) >= 60.0) & (c.mean(axis=1) <= 190.0)
            is_warm_skin_fist = lambda c: ((c[:, 0] - c[:, 2]) >= 12.0) & (c.mean(axis=1) >= 68.0) & (c.mean(axis=1) <= 204.0)

            # A. PART_HEAD: Crisp screaming face/beard from f=120, back hair from f=76, upper side hair from f=41
            is_hd = (PID == hs.PART_HEAD)
            is_hd_hair = is_hd & ((Pz > 44.2) | ((Nx < 0.08) & (Pz > 40.2)))
            is_hd_face = is_hd & (~is_hd_hair)

            add_view_contrib(120, is_hd_hair, 6.0 * (np.clip(Nx + 0.25, 0.0, 1.25) ** 2.0), lum_range=(6.0, 88.0), apply_head_shift=True)
            add_view_contrib(76,  is_hd_hair, 6.0 * (np.clip(-Nx + 0.28, 0.0, 1.28) ** 2.0), lum_range=(6.0, 88.0), apply_head_shift=True)
            P_mir_y = np.column_stack([Px, -np.abs(Py), Pz])
            w_hd_side = 2.5 * (np.clip(np.abs(Ny) - 0.62, 0.0, 0.38) / 0.38) ** 1.8 * np.clip(0.20 - Nx, 0.0, 1.0)
            add_view_contrib(41, is_hd_hair & ((Pz > 43.2) | (Px < -7.6)), w_hd_side, P_query=P_mir_y, block_zbs=[(zb_armr_41, -0.5)], lum_range=(6.0, 88.0))

            add_view_contrib(120, is_hd_face, 6.5 * (np.clip(Nx + 0.28, 0.0, 1.28) ** 2.0), lum_range=(6.0, 212.0), apply_head_shift=True)
            add_view_contrib(76,  is_hd_face, 5.5 * (np.clip(-Nx + 0.25, 0.0, 1.25) ** 2.0), color_fn=is_warm_skin_fist, apply_head_shift=True)

            # B. PART_TORSO: Central shirt+tie V (f=120) + Tan khaki blazer lapels/shoulders/back/skirts (f=120, 76, 41)
            is_tr = (PID == hs.PART_TORSO)
            is_shirt_v = is_tr & (np.abs(Py + 0.15) < 3.45) & (Pz > 22.0) & (Nx > 0.22)
            is_blazer = is_tr & (~is_shirt_v)

            add_view_contrib(120, is_shirt_v, 6.0 * (np.clip(Nx + 0.20, 0.0, 1.20) ** 2.0), block_zbs=[(zb_legs_120, 0.6), (zb_rig_120, 0.6)], lum_range=(12.0, 246.0))
            add_view_contrib(120, is_blazer,  5.5 * (np.clip(Nx + 0.22, 0.0, 1.22) ** 2.0), block_zbs=[(zb_legs_120, 0.6), (zb_rig_120, 0.6)], color_fn=is_blazer_tan)
            add_view_contrib(76,  is_blazer,  5.5 * (np.clip(-Nx + 0.24, 0.0, 1.24) ** 2.0), block_zbs=[(zb_rig_76, 0.6), (zb_legs_76, 0.6)], color_fn=is_blazer_tan)
            add_view_contrib(41,  is_blazer,  4.2 * (np.clip(np.abs(Ny) - 0.35, 0.0, 0.65) ** 1.8), P_query=P_mir_y,
                             block_zbs=[(zb_rig_41, 0.6), (zb_armr_41, 0.6)], color_fn=is_blazer_tan)

            # C. PART_ARM_R & PART_ARM_L: Tan blazer sleeves + White shirt cuffs + Warm skin clenched fists!
            is_arm = np.isin(PID, [hs.PART_ARM_R, hs.PART_ARM_L])
            z_cuff_lo = np.where(PID == hs.PART_ARM_R, 37.85, 37.45)
            z_cuff_hi = np.where(PID == hs.PART_ARM_R, 38.75, 38.35)
            is_arm_sleeve = is_arm & (Pz < z_cuff_lo)
            is_arm_cuff = is_arm & (Pz >= z_cuff_lo) & (Pz <= z_cuff_hi)
            is_arm_fist = is_arm & (Pz > z_cuff_hi)

            add_view_contrib(120, is_arm_sleeve, 5.5 * (np.clip(Nx + 0.35, 0.0, 1.35) ** 1.8), color_fn=is_blazer_tan)
            add_view_contrib(76,  is_arm_sleeve, 5.5 * (np.clip(-Nx + 0.35, 0.0, 1.35) ** 1.8), color_fn=is_blazer_tan)
            add_view_contrib(41,  is_arm_sleeve & (Pz < 36.8), 2.2 * (np.clip(np.abs(Ny) - 0.45, 0.0, 0.55) ** 1.6), P_query=P_mir_y, color_fn=is_blazer_tan)

            add_view_contrib(120, is_arm_cuff, 5.5 * (np.clip(Nx + 0.35, 0.0, 1.35) ** 1.8), lum_range=(165.0, 245.0))
            add_view_contrib(76,  is_arm_cuff, 5.5 * (np.clip(-Nx + 0.35, 0.0, 1.35) ** 1.8), lum_range=(165.0, 245.0))

            add_view_contrib(120, is_arm_fist, 5.5 * (np.clip(Nx + 0.35, 0.0, 1.35) ** 1.8), color_fn=is_warm_skin_fist)
            add_view_contrib(76,  is_arm_fist, 5.5 * (np.clip(-Nx + 0.35, 0.0, 1.35) ** 1.8), color_fn=is_warm_skin_fist)

            # D. PART_LEG_R & PART_LEG_L: Black wool dress trousers (X < 19.3) + Charcoal-grey ribbed socks (X >= 19.3)
            is_leg = np.isin(PID, [hs.PART_LEG_R, hs.PART_LEG_L])
            is_trouser = is_leg & (Px < 19.3)
            is_sock = is_leg & (Px >= 19.3)
            P_leg_41 = P.copy()
            m_ll = (PID == hs.PART_LEG_L)
            P_leg_41[m_ll, 1] = -3.5 - 0.36 * np.clip(Px[m_ll] + 3.6, 0.0, 30.0)
            P_leg_41[m_ll, 2] = Pz[m_ll] + 0.8

            add_view_contrib(120, is_trouser, 5.0 * (np.clip(Nx + 0.25, 0.0, 1.25) ** 1.8), block_zbs=[(zb_shoes_120, 0.6), (zb_rig_120, 0.6)], lum_range=(8.0, 62.0))
            add_view_contrib(41,  is_trouser & (Pz > 21.3), 4.5 * (np.clip(np.abs(Ny) + 0.25, 0.0, 1.25) ** 1.8), P_query=P_leg_41, block_zbs=[(zb_rig_41, 0.6)], lum_range=(8.0, 62.0))

            add_view_contrib(41,  is_sock, 5.5 * np.ones(len(P)), P_query=P_leg_41, lum_range=(35.0, 112.0))
            add_view_contrib(120, is_sock, 2.5 * np.clip(Nx + 0.3, 0.0, 1.3), block_zbs=[(zb_shoes_120, 0.6)], lum_range=(35.0, 112.0))

            # E. PART_SHOE_R & PART_SHOE_L: Brown leather soles from f=120 + Laced Oxford leather uppers from f=41!
            is_shoe = np.isin(PID, [hs.PART_SHOE_R, hs.PART_SHOE_L])
            P_shoe_41 = P.copy()
            m_sl = (PID == hs.PART_SHOE_L)
            P_shoe_41[m_sl, 0] = Px[m_sl] - 0.30
            P_shoe_41[m_sl, 1] = Py[m_sl] - 17.20
            P_shoe_41[m_sl, 2] = Pz[m_sl] + 0.90

            add_view_contrib(120, is_shoe, 6.0 * (np.clip(Nx - 0.15, 0.0, 1.0) ** 1.6), lum_range=(12.0, 136.0))
            add_view_contrib(41,  is_shoe, 5.0 * (np.clip(1.15 - Nx, 0.0, 1.4) ** 1.6), P_query=P_shoe_41, lum_range=(12.0, 128.0))

            # Fine semantic sub-IDs for crease inpainting so hair/cuff/sleeve/sock never cross-bleed!
            SUB_ID = PID * 10
            SUB_ID[is_hd_hair] = 11
            SUB_ID[is_shirt_v] = 21
            SUB_ID[is_arm_cuff] = 31
            SUB_ID[is_arm_fist] = 32
            SUB_ID[is_sock] = 51
            # Fallback seed if white cuff has few direct pixels
            if int(( (wsum > 1e-6) & is_arm_cuff ).sum()) < 20:
                acc[is_arm_cuff] = np.array([224.0, 224.0, 226.0])
                wsum[is_arm_cuff] = 1.0

        else:
            # ---------------- SQUAT RIDER ----------------
            f_head_front = 0 if use_grin_head else 18
            zb_rig_18 = make_zbuf(rig_pts, 18, guard_cells=1)
            zb_rig_75 = make_zbuf(rig_pts, 75, guard_cells=1)

            legs_pts = h_dense_pts[np.isin(h_dense_pids, [hs.PART_LEG_R, hs.PART_LEG_L, hs.PART_SHOE_R, hs.PART_SHOE_L])]
            arms_pts = h_dense_pts[np.isin(h_dense_pids, [hs.PART_ARM_R, hs.PART_ARM_L])]
            zb_legs_18 = make_zbuf(legs_pts, 18, guard_cells=2)
            zb_legs_75 = make_zbuf(legs_pts, 75, guard_cells=2)
            zb_legs_48 = make_zbuf(legs_pts, 48, guard_cells=2)
            zb_legs_98 = make_zbuf(legs_pts, 98, guard_cells=2)
            zb_arms_48 = make_zbuf(arms_pts, 48, guard_cells=2)
            zb_arms_98 = make_zbuf(arms_pts, 98, guard_cells=2)

            is_plaid_fabric = lambda c: ((c[:, 0] - c[:, 2]) < 16.0) & ((c[:, 0] - c[:, 2]) > -6.0) & (c.mean(axis=1) >= 164.0) & (c.mean(axis=1) <= 242.0)
            is_pure_skin = lambda c: (
                ((c[:, 0] - c[:, 2]) >= 20.0)
                & ((c[:, 0] - c[:, 1]) >= 9.0)
                & ((c[:, 1] - c[:, 2]) >= 7.0)
                & (c[:, 2] <= 108.0)
                & (c.mean(axis=1) >= 62.0)
                & (c.mean(axis=1) <= 146.0)
            )
            is_skin_or_beard = lambda c: (((c[:, 0] - c[:, 2]) >= 16.0) & (c[:, 2] <= 116.0) & (c[:, 0] >= 1.22 * c[:, 2]) & (c.mean(axis=1) <= 156.0)) | (c.mean(axis=1) < 58.0)

            # A. PART_HEAD: Anatomically curved curly black hairline + T-zone features + pure brown cheek/jaw skin!
            is_hd = (PID == hs.PART_HEAD)
            z_hair_cut = np.where(
                Px > 0.4,
                44.35,
                np.where(Px > -2.0, 42.55 + 0.75 * (Px + 2.0), 40.15 + 1.2 * np.clip(Px + 4.0, 0.0, 2.0)),
            )
            is_hd_hair = is_hd & (Pz > z_hair_cut)
            is_hd_face = is_hd & (~is_hd_hair)

            phi_hd_front = 0.0 if use_grin_head else None
            add_view_contrib(f_head_front, is_hd_hair, 6.5 * (np.clip(Nx + 0.28, 0.0, 1.28) ** 2.0), lum_range=(5.0, 66.0), apply_head_shift=True, phi_override=phi_hd_front)
            add_view_contrib(75, is_hd_hair, 6.5 * (np.clip(-Nx + 0.30, 0.0, 1.30) ** 2.0), lum_range=(5.0, 66.0), apply_head_shift=True)
            w_hd_s = 2.6 * (np.clip(np.abs(Ny) - 0.62, 0.0, 0.38) / 0.38) ** 1.8 * np.clip(0.22 - Nx, 0.0, 1.0)
            add_view_contrib(48, is_hd_hair & (Ny >= 0.0), w_hd_s, lum_range=(5.0, 66.0))
            add_view_contrib(98, is_hd_hair & (Ny < 0.0),  w_hd_s, lum_range=(5.0, 66.0))

            # T-zone front facial features (wider mouth box when grinning in f=0, head looking straight at camera!)
            mouth_half_w = 1.48 if use_grin_head else 1.18
            w_face_tzone = 6.8 * (np.clip(Nx - 0.32, 0.0, 1.0) ** 1.6)
            w_face_cheek = 5.5 * (np.clip(Nx - 0.38, 0.0, 1.0) ** 1.8)
            is_grin_box = is_hd_face & (Nx > 0.56) & (np.abs(Py + 0.15) < 1.45) & (Pz > 38.2) & (Pz < 40.5)
            if use_grin_head:
                add_view_contrib(f_head_front, is_grin_box, w_face_tzone, lum_range=(12.0, 240.0), apply_head_shift=True, phi_override=phi_hd_front)
                rem_face = is_hd_face & (~is_grin_box)
            else:
                rem_face = is_hd_face
            in_eye_band = (Pz >= 41.1) & (Pz < 43.8) & (np.abs(Py + 0.15) < 1.90) & (Nx > 0.48)
            in_mouth_band = (Pz > 36.8) & (Pz < 41.1) & (np.abs(Py + 0.15) < mouth_half_w) & (Nx > 0.52)
            is_face_central = rem_face & (in_eye_band | in_mouth_band)
            is_face_outer = rem_face & (~is_face_central)

            add_view_contrib(f_head_front, is_face_central, w_face_tzone, color_fn=is_skin_or_beard, apply_head_shift=True, phi_override=phi_hd_front)
            add_view_contrib(f_head_front, is_face_outer,   w_face_cheek, color_fn=is_pure_skin, apply_head_shift=True, phi_override=phi_hd_front)
            add_view_contrib(75, is_hd_face, 5.5 * (np.clip(-Nx - 0.05, 0.0, 1.0) ** 1.8), color_fn=is_pure_skin, apply_head_shift=True)
            # Clean lateral cheek/ear/jaw skin (Px < 1.05) with strict golden-brown skin filter (rejects lips, beard, & collar!)
            w_cheek_s = 4.2 * (np.clip(np.abs(Ny) - 0.42, 0.0, 0.58) ** 1.6)
            add_view_contrib(48, is_face_outer & (Ny >= 0.0) & (Px < 1.05), w_cheek_s, color_fn=is_pure_skin)
            add_view_contrib(98, is_face_outer & (Ny < 0.0) & (Px < 1.05),  w_cheek_s, color_fn=is_pure_skin)

            # B. PART_TORSO: Cream windowpane-plaid short-sleeve shirt (Front f=18 + Rear f=75 wrap + guarded Profile f=48/98!)
            is_tr = (PID == hs.PART_TORSO)
            add_view_contrib(18, is_tr, 5.8 * (np.clip(Nx + 0.35, 0.0, 1.35) ** 1.7), block_zbs=[(zb_legs_18, 0.7), (zb_rig_18, 0.7)], color_fn=is_plaid_fabric)
            add_view_contrib(75, is_tr, 5.8 * (np.clip(-Nx + 0.35, 0.0, 1.35) ** 1.7), block_zbs=[(zb_legs_75, 0.7), (zb_rig_75, 0.7)], color_fn=is_plaid_fabric)
            w_tr_s = 3.8 * (np.clip(np.abs(Ny) - 0.48, 0.0, 0.52) ** 1.8)
            add_view_contrib(48, is_tr & (Ny >= 0.0) & (Pz > 21.5), w_tr_s, block_zbs=[(zb_arms_48, 0.8), (zb_legs_48, 0.8)], color_fn=is_plaid_fabric)
            add_view_contrib(98, is_tr & (Ny < 0.0) & (Pz > 21.5),  w_tr_s, block_zbs=[(zb_arms_98, 0.8), (zb_legs_98, 0.8)], color_fn=is_plaid_fabric)

            # C. PART_ARM_R & PART_ARM_L: Bare muscular forearms & hands gripping chrome handlebars
            is_arm = np.isin(PID, [hs.PART_ARM_R, hs.PART_ARM_L])
            add_view_contrib(18, is_arm, 5.5 * (np.clip(Nx + 0.38, 0.0, 1.38) ** 1.7), block_zbs=[(zb_rig_18, 0.5)], color_fn=is_pure_skin)
            add_view_contrib(75, is_arm, 5.5 * (np.clip(-Nx + 0.38, 0.0, 1.38) ** 1.7), block_zbs=[(zb_rig_75, 0.5)], color_fn=is_pure_skin)
            add_view_contrib(48, (PID == hs.PART_ARM_L) & (Pz > 24.8), 3.2 * np.clip(Ny - 0.45, 0.0, 0.55), color_fn=is_pure_skin)
            add_view_contrib(98, (PID == hs.PART_ARM_R) & (Pz > 24.8), 3.2 * np.clip(-Ny - 0.45, 0.0, 0.55), color_fn=is_pure_skin)

            # D. PART_LEG_R & PART_LEG_L: Olive-brown cargo pants (ONLY unoccluded Front f=18 & Rear f=75 -> ZERO tire bleed!)
            is_leg = np.isin(PID, [hs.PART_LEG_R, hs.PART_LEG_L])
            add_view_contrib(18, is_leg, 5.5 * (np.clip(Nx + 0.42, 0.0, 1.42) ** 1.7), block_zbs=[(zb_rig_18, 0.7)], lum_range=(28.0, 134.0))
            add_view_contrib(75, is_leg, 5.5 * (np.clip(-Nx + 0.42, 0.0, 1.42) ** 1.7), block_zbs=[(zb_rig_75, 0.7)], lum_range=(28.0, 134.0))

            # E. PART_SHOE_R & PART_SHOE_L: Tucked dark-brown suede shoes (Front f=18 & Rear f=75)
            is_shoe = np.isin(PID, [hs.PART_SHOE_R, hs.PART_SHOE_L])
            add_view_contrib(18, is_shoe, 5.5 * (np.clip(Nx + 0.42, 0.0, 1.42) ** 1.7), block_zbs=[(zb_rig_18, 0.6)], lum_range=(14.0, 104.0))
            add_view_contrib(75, is_shoe, 5.5 * (np.clip(-Nx + 0.42, 0.0, 1.42) ** 1.7), block_zbs=[(zb_rig_75, 0.6)], lum_range=(14.0, 104.0))

            SUB_ID = PID * 10
            SUB_ID[is_hd_hair] = 11

        # Sub-region-confined 3D k-NN inpainting for any hidden creases (hair->hair, blazer->blazer, cuff->cuff!)
        seen = wsum > 1e-6
        col = np.zeros((len(P), 3), dtype=np.float32)
        col[seen] = (acc[seen] / wsum[seen][:, None]).astype(np.float32)
        n_unseen = int((~seen).sum())
        print(f"  [{out_base_name}] seen={int(seen.sum()):,}, sub-part-inpainted creases={n_unseen:,}")

        if n_unseen > 0:
            for sid_val in np.unique(SUB_ID):
                m_u = (~seen) & (SUB_ID == sid_val)
                if not m_u.any():
                    continue
                m_s = seen & (SUB_ID == sid_val)
                if not m_s.any():
                    m_s = seen & (PID == (sid_val // 10))
                if not m_s.any():
                    m_s = seen
                tree = cKDTree(P[m_s])
                dists, idxs = tree.query(P[m_u], k=min(8, int(m_s.sum())))
                if dists.ndim == 1:
                    dists = dists[:, None]
                    idxs = idxs[:, None]
                kw = 1.0 / np.maximum(dists, 0.05)
                col[m_u] = np.sum(col[m_s][idxs] * kw[..., None], axis=1) / np.sum(kw, axis=1, keepdims=True)

        # Write 1024x1024 UV atlas with 12px seam dilation so mipmaps/linear filtering never show black seams
        tex = np.zeros((TS, TS, 3), dtype=np.float32)
        cov = np.zeros((TS, TS), dtype=bool)
        tex[PY, PX] = np.clip(col, 0.0, 255.0)
        cov[PY, PX] = True

        for _ in range(12):
            acc_b = np.zeros_like(tex)
            cnt_b = np.zeros((TS, TS), dtype=np.float32)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                s_cov = np.roll(np.roll(cov, dy, axis=0), dx, axis=1)
                s_tex = np.roll(np.roll(tex, dy, axis=0), dx, axis=1)
                acc_b += s_tex * s_cov[..., None]
                cnt_b += s_cov.astype(np.float32)
            grow = (~cov) & (cnt_b > 0)
            if not grow.any():
                break
            tex[grow] = acc_b[grow] / cnt_b[grow, None]
            cov |= grow

        if (~cov).any():
            tex[~cov] = col[seen].mean(axis=0)

        im_srgb = Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8), "RGB")
        im_srgb_sharp = ImageEnhance.Sharpness(im_srgb).enhance(1.18)
        im_srgb_sharp.save(os.path.join(out_dir, f"{out_base_name}_srgb.png"))

        im_dp = rig.dp_calibrate(im_srgb_sharp, brightness=0.62, contrast=1.10)
        im_dp.save(os.path.join(progs_dir, f"{out_base_name}.png"))
        print(f"  Saved {out_base_name}_srgb.png and progs/{out_base_name}.png")

    if kind == "suit":
        bake_cardinal_atlas("mm_suit_human", use_grin_head=False)
    else:
        bake_cardinal_atlas("mm_squat_human", use_grin_head=False)
        bake_cardinal_atlas("mm_squat_human_grin", use_grin_head=True)


if __name__ == "__main__":
    vid1 = r"C:\Users\qxdc\.gemini\antigravity\brain\c5cf8ed8-8a7a-43da-a12a-3541b638fe8f\.user_uploaded\media_1793428832508_e43c906a.mp4"
    vid2 = r"C:\Users\qxdc\.gemini\antigravity\brain\c5cf8ed8-8a7a-43da-a12a-3541b638fe8f\.user_uploaded\media_1793428832489_5c1853ec.mp4"
    out_d = os.path.join(HERE, "out", "mm_riders")
    progs_d = os.path.abspath(os.path.join(HERE, "..", "..", "progs"))

    rig.build_rig_textures(out_d, progs_d)
    reconstruct_rider("suit", vid1, out_d, progs_d)
    reconstruct_rider("squat", vid2, out_d, progs_d)
