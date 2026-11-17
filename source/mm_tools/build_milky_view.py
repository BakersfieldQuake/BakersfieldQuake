"""The Milky Gun's held model: the user's three Grok videos of a giant hand holding the Pink Lady, driven per-frame by .skin files.

  progs/v_milky.md3             one card; its SKIN (progs/v_milky.md3_0..247.skin) selects the exact animation frame in Milky_ViewFrame
  progs/mvm_a_00..95.png        idle A (video 1: native 24 fps frames 0..95), skins 0..95, ping-ponged in QuakeC
  progs/mvm_b_00..95.png        idle B (video 2: native 24 fps frames 0..95), skins 96..191, ping-ponged in QuakeC
  progs/mvm_f_00..55.png        the shot (video 3): skins 192..247:
                                  00..35 = windup & fingers uncurling to open-palm launch (MILKY_WIND = 0.50 s, 72 fps)
                                  36..55 = empty open hand following through & dropping away (MILKY_FLYOUT = 0.30 s, 67 fps)
                                Motion-interpolated with forward-splatted optical flow for crisp ghost-free fingers.
  scripts/milkyvm.shader        static per-frame shaders (avoids Q3 animmap 64-frame cap and global shader clock drift)

python3.13 build_milky_view.py <idle_a.mp4> <idle_b.mp4> <shot.mp4> [BakersfieldQuake dir]"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage

DEFAULT_VID_A = r"G:\Downloads\grok-video-8161e23b-9165-4fcf-b5e5-1272a194ba13 (2).mp4"
DEFAULT_VID_B = r"G:\Downloads\grok-video-8161e23b-9165-4fcf-b5e5-1272a194ba13 (3).mp4"
DEFAULT_VID_F = r"G:\Downloads\grok-video-8161e23b-9165-4fcf-b5e5-1272a194ba13 (4).mp4"

VID_A = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VID_A
VID_B = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_VID_B
VID_F = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VID_F
MOD = sys.argv[4] if len(sys.argv) > 4 else r"G:\Quake\Combat\BakersfieldQuake"
PROGS = os.path.join(MOD, "progs")
HERE = os.path.dirname(os.path.abspath(__file__))

IDLE_FRAMES = 96          # skins 0..95 (idle A) and 96..191 (idle B), native 24 fps
SHOT_WIND_FRAMES = 36     # skins 192..227 (mvm_f_00..35: windup + palm opening, 0.50 s)
SHOT_FOLLOW_FRAMES = 20   # skins 228..247 (mvm_f_36..55: empty open hand follow-through, 0.30 s)

TEX_W = 384
DIM = 0.60                # balanced viewmodel brightness under rgbGen lightingDiffuse + HDR 1.25..1.45
VIEW_H = 27.0             # card height in view units; screen is about +/-27.8 wide and +/-15.6 high at x = 14
VIEW_X = 14.0
VIEW_RIGHT = -29.0        # right edge (past the screen's right edge: the arm runs off the corner)
VIEW_TOP = 8.0


def load_video_rgb(path, max_frame=None):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Could not open video: %s" % path)
    out = []
    idx = 0
    while True:
        if max_frame is not None and idx > max_frame:
            break
        ret, frame = cap.read()
        if not ret:
            break
        out.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += 1
    cap.release()
    return out


def clean_keyout(rgb_arr, hand_only=False):
    """Key out the white studio backdrop with interior RGB color decontamination so silhouette edges have zero
    white halo even under alphafunc GE128. Seed flood-fill from top, left, and right borders so outstretched arms
    touching the frame edge never trap white pockets underneath them."""
    h, w, _ = rgb_arr.shape
    pad = 12
    big = np.pad(rgb_arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    bh, bw, _ = big.shape

    lo = big.min(axis=2).astype(np.float32)
    hi = big.max(axis=2).astype(np.float32)
    cand = (lo > 216).astype(np.uint8)
    labeled, _ = ndimage.label(cand)

    # Seed background from all white pixels along top, left, and right borders
    bg_labels = (
        set(np.unique(labeled[0, :]))
        | set(np.unique(labeled[:, 0]))
        | set(np.unique(labeled[:, bw - 1]))
    )
    bg_labels.discard(0)
    edge_bg = np.isin(labeled, list(bg_labels)) if bg_labels else np.zeros_like(cand, dtype=bool)

    # Interior backdrop gaps (between fingers, arms, and waist) while protecting eyes/teeth inside her face box
    yy, xx = np.ogrid[:bh, :bw]
    in_face = (yy < int(bh * 0.24)) & (xx > int(bw * 0.34)) & (xx < int(bw * 0.66))
    wide_bg = ndimage.binary_opening(lo > 234, structure=np.ones((9, 9)))
    finger_gaps = ndimage.binary_opening((lo > 218) & ((hi - lo) < 15.0) & (~in_face), structure=np.ones((3, 3)))
    bg = edge_bg | wide_bg | finger_gaps

    dist_fg = ndimage.distance_transform_edt(~bg)
    alpha = np.clip((dist_fg - 1.8) / 1.5, 0.0, 1.0)
    whiteness = np.clip((lo - 205.0) / 35.0, 0.0, 1.0)
    alpha = np.where(dist_fg < 4.5, alpha * (1.0 - 0.90 * whiteness), alpha)

    dist_crop = dist_fg[pad:pad + h, pad:pad + w]
    alpha = alpha[pad:pad + h, pad:pad + w]

    if hand_only:
        fg_bin = alpha > 0.05
        lbl, _ = ndimage.label(fg_bin)
        keep = set(np.unique(lbl[-4:, :])) | set(np.unique(lbl[h // 2:, -4:]))
        keep.discard(0)
        if keep:
            hand_mask = np.isin(lbl, list(keep)).astype(np.float32)
            alpha = alpha * cv2.GaussianBlur(hand_mask, (5, 5), 1.0)
        else:
            alpha[:] = 0.0

    # Decontaminate outer 4.5px rim using deep interior foreground RGB so no white rim survives
    deep_solid = (dist_crop > 4.8) & (alpha > 0.95)
    if np.any(deep_solid):
        _, indices = ndimage.distance_transform_edt(~deep_solid, return_indices=True)
        decontam_rgb = rgb_arr[indices[0], indices[1]]
        rim_w = np.clip((dist_crop - 2.0) / 3.0, 0.0, 1.0)[..., None]
        clean_rgb = (rgb_arr.astype(np.float32) * rim_w + decontam_rgb.astype(np.float32) * (1.0 - rim_w)).astype(np.uint8)
    else:
        clean_rgb = rgb_arr.copy()

    a_u8 = (np.clip(alpha, 0.0, 1.0) * 255.0).round().astype(np.uint8)
    clean_rgb[a_u8 == 0] = 0
    return np.dstack([clean_rgb, a_u8])


def flow_interp_rgba(rgba0, rgba1, t):
    """Symmetric optical-flow warp using forward displacement evaluated at intermediate coordinates to prevent ghosting."""
    if t <= 1e-4:
        return rgba0.copy()
    if t >= 1.0 - 1e-4:
        return rgba1.copy()

    def to_gray(rgba):
        a = rgba[..., 3:4].astype(np.float32) / 255.0
        comp = rgba[..., :3].astype(np.float32) * a + 128.0 * (1.0 - a)
        return cv2.cvtColor(comp.astype(np.uint8), cv2.COLOR_RGB2GRAY)

    g0, g1 = to_gray(rgba0), to_gray(rgba1)
    # flow01(y, x) = (dx, dy) from frame 0 to frame 1
    flow01 = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 4, 23, 4, 5, 1.2, 0)
    flow10 = cv2.calcOpticalFlowFarneback(g1, g0, None, 0.5, 4, 23, 4, 5, 1.2, 0)

    h, w = g0.shape
    grid_x, grid_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))

    # Forward-splat flow01 to intermediate time t so fast-moving fingers land at their true intermediate pixel!
    vel_x = 0.5 * (flow01[..., 0] - flow10[..., 0])
    vel_y = 0.5 * (flow01[..., 1] - flow10[..., 1])
    # Refine intermediate velocity by one fixed-point step
    mid_vx = cv2.remap(vel_x, grid_x - (t - 0.5) * vel_x, grid_y - (t - 0.5) * vel_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mid_vy = cv2.remap(vel_y, grid_x - (t - 0.5) * vel_x, grid_y - (t - 0.5) * vel_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # Sample frame 0 at (X - t*V) and frame 1 at (X + (1-t)*V)
    map0_x = grid_x - t * mid_vx
    map0_y = grid_y - t * mid_vy
    map1_x = grid_x + (1.0 - t) * mid_vx
    map1_y = grid_y + (1.0 - t) * mid_vy

    f0 = rgba0.astype(np.float32)
    f1 = rgba1.astype(np.float32)
    p0 = np.dstack([f0[..., :3] * (f0[..., 3:4] / 255.0), f0[..., 3:4]])
    p1 = np.dstack([f1[..., :3] * (f1[..., 3:4] / 255.0), f1[..., 3:4]])

    w0 = cv2.remap(p0, map0_x, map0_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    w1 = cv2.remap(p1, map1_x, map1_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

    pm = (1.0 - t) * w0 + t * w1
    alpha = np.clip(pm[..., 3], 0.0, 255.0)
    denom = np.maximum(alpha[..., None] / 255.0, 1e-4)
    rgb = np.clip(pm[..., :3] / denom, 0.0, 255.0)
    # Sharpen alpha around the 128 threshold so warped silhouettes never split into faint double-alpha ghosts
    a_sharp = np.clip((alpha - 110.0) * (255.0 / 36.0), 0.0, 255.0)
    a_u8 = a_sharp.round().astype(np.uint8)
    rgb_u8 = rgb.round().astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return np.dstack([rgb_u8, a_u8])


def resample_sequence(rgba_list, positions):
    out = []
    n = len(rgba_list)
    for pos in positions:
        pos = float(np.clip(pos, 0.0, n - 1))
        i0 = int(np.floor(pos))
        i1 = min(i0 + 1, n - 1)
        out.append(flow_interp_rgba(rgba_list[i0], rgba_list[i1], pos - i0))
    return out


def tone_and_resize(rgba_arr, box, target_w, target_h):
    crop = rgba_arr[box[1]:box[3], box[0]:box[2]].astype(np.float32)
    a_c = crop[..., 3:4] / 255.0
    pm = np.dstack([crop[..., :3] * a_c, crop[..., 3:4]])
    pm_rs = cv2.resize(pm, (target_w, target_h), interpolation=cv2.INTER_AREA)
    alpha_f = np.clip(pm_rs[..., 3], 0.0, 255.0)
    rgb_f = np.clip(pm_rs[..., :3] / np.maximum(alpha_f[..., None] / 255.0, 1e-4), 0.0, 255.0)

    # Vivid, bright grading matching the Pink Lady projectile (rich hot-pink top, warm luminous skin)
    x = np.clip(rgb_f / 255.0, 0.0, 1.0)
    x = np.clip((x - 0.018) / 0.982, 0.0, 1.0)
    lifted = np.power(x, 0.88) * 1.06
    lifted = lifted / (1.0 + 0.08 * lifted * lifted)
    lifted = np.clip(lifted * DIM, 0.0, 1.0)
    r, g, b = lifted[..., 0], lifted[..., 1], lifted[..., 2]
    pink_amt = np.clip((r - g - 0.16) / 0.32, 0.0, 1.0) * np.clip((r - b + 0.10) / 0.25, 0.0, 1.0)
    r = np.clip(r * (1.0 + 0.08 * pink_amt) + 0.03 * pink_amt, 0.0, 1.0)
    g = np.clip(g * (1.0 - 0.10 * pink_amt), 0.0, 1.0)
    b = np.clip(b * (1.0 + 0.10 * pink_amt) + 0.05 * pink_amt, 0.0, 1.0)

    rgb_arr = np.clip(np.round(np.dstack([r, g, b]) * 255.0), 0, 255).astype(np.uint8)
    alpha = np.where(alpha_f < 8, 0, np.round(alpha_f)).astype(np.uint8)
    rgb_arr[alpha == 0] = 0
    return np.dstack([rgb_arr, alpha])


def main():
    print("Loading source videos...")
    raw_a = load_video_rgb(VID_A, max_frame=IDLE_FRAMES)
    raw_b = load_video_rgb(VID_B, max_frame=IDLE_FRAMES)
    raw_f = load_video_rgb(VID_F, max_frame=104)

    print("Keying out native 24 fps Idle A (0..95) and Idle B (0..95)...")
    key_a = [clean_keyout(raw_a[i], hand_only=False) for i in range(IDLE_FRAMES)]
    key_b = [clean_keyout(raw_b[i], hand_only=False) for i in range(IDLE_FRAMES)]

    print("Keying out Shot windup (54..83) and open-hand follow-through (91..102)...")
    key_f_wind = [clean_keyout(raw_f[i], hand_only=False) for i in range(54, 84)]   # 30 frames: 54..83 (full head unclipped)
    key_f_hand = [clean_keyout(raw_f[i], hand_only=True) for i in range(91, 103)]   # 12 frames: 91..102

    xs0, ys0, xs1, ys1 = [], [], [], []
    for seq in (key_a, key_b, key_f_wind, key_f_hand):
        for arr in seq:
            ys, xs = np.nonzero(arr[..., 3] > 16)
            if len(xs):
                xs0.append(int(xs.min()))
                ys0.append(int(ys.min()))
                xs1.append(int(xs.max()) + 1)
                ys1.append(int(ys.max()) + 1)
    box = (min(xs0), min(ys0), max(xs1), max(ys1))
    aspect = (box[2] - box[0]) / float(box[3] - box[1])
    tex_h = round(TEX_W / aspect)

    seq_a = [tone_and_resize(a, box, TEX_W, tex_h) for a in key_a]
    seq_b = [tone_and_resize(b, box, TEX_W, tex_h) for b in key_b]
    crop_fw = [tone_and_resize(f, box, TEX_W, tex_h) for f in key_f_wind]
    crop_fh = [tone_and_resize(f, box, TEX_W, tex_h) for f in key_f_hand]

    print("Motion-interpolating high-FPS shot sequence...")
    # 14 brisk frames for initial excitement (f054..f074) + 22 ultra-smooth frames for finger uncurl & open-palm toss (f075..f083)
    pos_w1 = np.linspace(0.0, 21.0, 14, endpoint=False)
    pos_w2 = np.linspace(21.0, 29.0, 22, endpoint=True)
    seq_f_wind = resample_sequence(crop_fw, np.concatenate([pos_w1, pos_w2]))
    seq_f_hand = resample_sequence(crop_fh, np.linspace(0.0, len(crop_fh) - 1, SHOT_FOLLOW_FRAMES))
    seq_f = seq_f_wind + seq_f_hand

    sets = {"a": seq_a, "b": seq_b, "f": seq_f}

    os.makedirs(PROGS, exist_ok=True)
    for old in glob.glob(os.path.join(PROGS, "mvm_*.png")):
        os.remove(old)

    total_bytes = 0
    for k, fs in sets.items():
        for i, arr in enumerate(fs):
            out_path = os.path.join(PROGS, "mvm_%s_%02d.png" % (k, i))
            Image.fromarray(arr, "RGBA").save(out_path, compress_level=3)
            total_bytes += os.path.getsize(out_path)

    # Write static per-frame shaders and consecutive .skin files (0..247)
    os.makedirs(os.path.join(MOD, "scripts"), exist_ok=True)
    for old in glob.glob(os.path.join(PROGS, "v_milky*.skin")):
        os.remove(old)

    skin_idx = 0
    with open(os.path.join(MOD, "scripts", "milkyvm.shader"), "w", newline="\n") as sh:
        sh.write("// written by mm_tools/build_milky_view.py\n")
        for k in ("a", "b", "f"):
            for i in range(len(sets[k])):
                sh_name = "progs/mvm_%s_%02d" % (k, i)
                sh.write("%s\n{\n\tcull none\n\tnomipmaps\n\t{\n\t\tclampmap %s\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}\n}\n" % (sh_name, sh_name))
                with open(os.path.join(PROGS, "v_milky.md3_%d.skin" % skin_idx), "w", newline="\n") as sk:
                    sk.write("card,%s\n" % sh_name)
                skin_idx += 1

    vh = VIEW_H
    vw = vh * aspect
    dy = VIEW_RIGHT + vw / 2.0
    dz = VIEW_TOP - vh / 2.0
    hw, hh = vw / 2.0, vh / 2.0
    card = [(VIEW_X, dy + hw, dz - hh), (VIEW_X, dy + hw, dz + hh), (VIEW_X, dy - hw, dz + hh), (VIEW_X, dy - hw, dz - hh)]
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    surf = dict(name="card", shader="progs/mvm_a_00", tris=tris, st=st, frames=[(card, [(-1.0, 0.0, 0.0)] * 4)])
    md3lib.write(os.path.join(PROGS, "v_milky.md3"), dict(name="v_milky", surfaces=[surf], nframes=1))

    print("frames: a=%d (skins 0..%d), b=%d (skins %d..%d), f=%d (skins %d..%d) | total skins=%d" % (
        len(seq_a), len(seq_a) - 1,
        len(seq_b), len(seq_a), len(seq_a) + len(seq_b) - 1,
        len(seq_f), len(seq_a) + len(seq_b), skin_idx - 1,
        skin_idx,
    ))
    print("crop %s | texture %dx%d | %.2f MB of RGBA png" % (box, TEX_W, tex_h, total_bytes / 1e6))

    out_dir = os.path.join(HERE, "out", "milky")
    os.makedirs(out_dir, exist_ok=True)
    picks = [
        ("a", 0), ("a", 48), ("a", 95),
        ("b", 0), ("b", 48), ("b", 95),
        ("f", 0), ("f", 7), ("f", 14), ("f", 23), ("f", 30), ("f", 35),
        ("f", 36), ("f", 40), ("f", 45), ("f", 50), ("f", 53), ("f", 55),
    ]
    cols = 6
    rows = (len(picks) + cols - 1) // cols
    cell_w = 200
    cell_h = round(cell_w * tex_h / TEX_W)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (70, 80, 70))
    for idx, (k, n) in enumerate(picks):
        im = Image.open(os.path.join(PROGS, "mvm_%s_%02d.png" % (k, n))).convert("RGBA").resize((cell_w, cell_h), Image.LANCZOS)
        sheet.paste(im, ((idx % cols) * cell_w, (idx // cols) * cell_h), im)
    sheet.save(os.path.join(out_dir, "view_sheet.png"))
    print("Saved contact sheet:", os.path.join(out_dir, "view_sheet.png"))


if __name__ == "__main__":
    main()
