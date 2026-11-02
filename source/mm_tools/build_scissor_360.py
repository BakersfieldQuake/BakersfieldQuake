"""Builds the Full 360-Degree 8-Direction Running & Snipping Evil Scissor Guy Sprite
with a True 3D (X, Y, Z) Flying $100 Cash Vortex!

Outputs:
  1. G:/Quake/Combat/BakersfieldQuake/scissor_sprite/
       - scissor_d{0..7}_f{0..7}.png   (8 angles around 360 deg x 8 run/snip frames = 64 RGBA PNGs)
       - scissor_360_sheet_8x8.png     (master 8-angle x 8-frame transparent sprite sheet)
       - scissor_360_spin.gif          (animated 360-degree spinning + running showcase GIF)
       - index.html                    (interactive 360 drag-to-turn + run/snip HTML sprite viewer)
  2. G:/Quake/Combat/BakersfieldQuake/progs/fr_scissors.spr32
       - 56-frame 8-direction Quake/DarkPlaces SPR32 sprite (matching friends.qc convention:
         frames 0..7 = 8 directions, frames 8..55 = 8 directions x 6 run frames, origin at feet).

Run with:
    python3.13 source/mm_tools/build_scissor_360.py
"""

import math
import os
import shutil
import struct
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = r"G:\Quake\Combat\BakersfieldQuake"
BRAIN = r"C:\Users\qxdc\.gemini\antigravity\brain\b00e11cf-659c-419a-a605-23ec106f1bc8"
RAW_DIR = os.path.join(ROOT, "source", "mm_tools", "out", "scissor_guy")
OUT_DIR = os.path.join(ROOT, "scissor_sprite")
PROGS_DIR = os.path.join(ROOT, "progs")

FILES = {
    "0_open": "raw_pose_open_1793429598089.jpg",
    "0_half": "raw_pose_snip_v3_1793429678583.jpg",
    "0_shut": "raw_pose_snip_v2_1793429651256.jpg",
    "45_s1_open": "scissor_guy_45_stride1_open_v17_1793432103283.jpg",
    "45_s2_shut": "scissor_guy_45_stride2_shut_v1_1793432140459.jpg",
    "90_s1_open": "scissor_guy_pose_a_lunge_stride_1793432014851.jpg",
    "90_s1_shut": "scissor_guy_pose_b_from_pose_a_1793432085665.jpg",
    "90_s2_shut": "scissor_guy_pose_b_stride2_shut_1793431701920.jpg",
    "135_open": "scissor_guy_135_open_v2_1793431583392.jpg",
    "135_shut": "scissor_guy_135_shut_v2_1793431665072.jpg",
    "180_open": "scissor_guy_180_open_1793431517994.jpg",
    "180_shut": "scissor_guy_180_shut_1793431618281.jpg",
}

N_DIRS = 8
N_RUN = 8
DIR_LABELS = [
    "0° Front",
    "45° Front-Left",
    "90° Left Side",
    "135° Back-Left",
    "180° Back",
    "225° Back-Right",
    "270° Right Side",
    "315° Front-Right",
]


# ---------------------------------------------------------------------------
# Fast Vectorized NumPy Chroma-Key + Magenta Despill
# ---------------------------------------------------------------------------
def key_magenta_fast(im_rgb):
    """Vectorized studio #FF00FF chroma key + unpremultiply + despill (preserves interior mouth/ears)."""
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    m = np.minimum(r, b) - g

    bg = (m > 68.0) & (r > 95.0) & (b > 95.0)
    dist = ndimage.distance_transform_edt(~bg)

    alpha = np.ones_like(m, dtype=np.float32)
    alpha[bg] = 0.0

    edge = (~bg) & (dist <= 8.0)
    # Soft ramp on boundary pixels
    a_ramp = np.clip(1.0 - (m - 8.0) / 62.0, 0.0, 1.0)
    use_ramp = edge & (m > 8.0)
    alpha[use_ramp] = np.where(a_ramp[use_ramp] <= 0.04, 0.0, a_ramp[use_ramp])

    # Un-premultiply #FF00FF background contribution on semi-transparent boundary pixels
    semi = (alpha > 0.0) & (alpha < 0.999)
    inv = 1.0 - alpha[semi]
    rf = np.maximum(0.0, (r[semi] - inv * 255.0) / alpha[semi])
    gf = np.maximum(0.0, g[semi] / alpha[semi])
    bf = np.maximum(0.0, (b[semi] - inv * 255.0) / alpha[semi])
    r[semi], g[semi], b[semi] = rf, gf, bf

    # Clamp any residual magenta tint on boundary (dist <= 6)
    despill = (alpha > 0.0) & (dist <= 6.0)
    excess = np.maximum(0.0, np.minimum(r[despill], b[despill]) - (g[despill] + 5.0))
    r[despill] = np.maximum(0.0, r[despill] - excess)
    b[despill] = np.maximum(0.0, b[despill] - excess)

    out = np.dstack([
        np.clip(np.round(r), 0, 255).astype(np.uint8),
        np.clip(np.round(g), 0, 255).astype(np.uint8),
        np.clip(np.round(b), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])
    return out


def largest_component_rgba(rgba_arr, also_return_islands=False):
    """Extracts the main character RGBA array on the full canvas, optionally returning smaller bill islands."""
    mask = rgba_arr[..., 3] > 20
    lbl, num = ndimage.label(mask)
    if num == 0:
        return Image.fromarray(rgba_arr, "RGBA"), []
    sizes = ndimage.sum(mask, lbl, range(1, num + 1))
    main_id = 1 + int(np.argmax(sizes))
    # Dilate main mask by 1px to keep AA alpha=1..20 halo
    main_keep = ndimage.binary_dilation(lbl == main_id, iterations=1)
    char_arr = rgba_arr.copy()
    char_arr[~main_keep] = 0

    islands = []
    if also_return_islands:
        order = np.argsort(sizes)[::-1]
        for idx in order[1:]:
            if sizes[idx] < 350:
                continue
            comp_id = int(idx) + 1
            cmask = ndimage.binary_dilation(lbl == comp_id, iterations=1)
            ys, xs = np.nonzero(cmask)
            sub = rgba_arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
            sub[~cmask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]] = 0
            islands.append(Image.fromarray(sub, "RGBA"))
    return Image.fromarray(char_arr, "RGBA"), islands


def is_blue_polo_mask(rgba_arr):
    r = rgba_arr[..., 0].astype(np.int16)
    g = rgba_arr[..., 1].astype(np.int16)
    b = rgba_arr[..., 2].astype(np.int16)
    a = rgba_arr[..., 3]
    return (a > 15) & ((b - r) > 26) & ((b - g) > 10)


def extend_belt_upward(lower_arr, y_start, y_end, x0, x1, up_px=18):
    """Extends topmost opaque belt/pants pixels upward behind the polo shirt hem so bounce/tilt never opens a gap."""
    out = lower_arr.copy()
    H, W = out.shape[:2]
    for x in range(max(0, x0), min(W, x1)):
        col_a = out[y_start:y_end, x, 3]
        nz = np.nonzero(col_a > 180)[0]
        if len(nz):
            top_y = y_start + int(nz[0])
            sample = out[min(H - 1, top_y + 2), x].copy()
            for yy in range(max(y_start - up_px, top_y - up_px), top_y):
                if out[yy, x, 3] == 0:
                    out[yy, x] = sample
    return out


def split_upper_lower_generic(char_im, waist_y_min, waist_x0, waist_x1, belt_x0, belt_x1, legs_y_min=650):
    """Splits character cleanly into Upper (head + blue polo + arms + scissors) and Lower (belt + khakis + pocket bills + legs)."""
    arr = np.array(char_im)
    H, W = arr.shape[:2]
    polo = is_blue_polo_mask(arr)

    region = np.zeros((H, W), dtype=bool)
    region[waist_y_min:legs_y_min, waist_x0:waist_x1] = True
    region[legs_y_min:H, :] = True
    lower_mask = region & (arr[..., 3] > 0) & (~polo)

    upper_arr = arr.copy()
    upper_arr[lower_mask] = 0

    lower_arr = np.zeros_like(arr)
    lower_arr[lower_mask] = arr[lower_mask]
    lower_arr = extend_belt_upward(lower_arr, waist_y_min, min(H, waist_y_min + 115), belt_x0, belt_x1, up_px=18)

    return Image.fromarray(upper_arr, "RGBA"), Image.fromarray(lower_arr, "RGBA")


def mirror_horiz_around_x(im, mid_x):
    arr = np.array(im)
    H, W = arr.shape[:2]
    out = np.zeros_like(arr)
    xs = np.arange(W)
    src_xs = 2 * int(round(mid_x)) - xs
    valid = (src_xs >= 0) & (src_xs < W)
    out[:, xs[valid]] = arr[:, src_xs[valid]]
    return Image.fromarray(out, "RGBA")


def transform_around_pivot(im, pivot, scale_x=1.0, scale_y=1.0, angle_deg=0.0, dx=0.0, dy=0.0, out_size=None):
    w, h = out_size if out_size else im.size
    px0, py0 = pivot
    rad = math.radians(angle_deg)
    ca, sa = math.cos(rad), math.sin(rad)
    tx = px0 + dx
    ty = py0 + dy
    a = ca / scale_x
    b = sa / scale_x
    c = px0 - a * tx - b * ty
    d = -sa / scale_y
    e = ca / scale_y
    f = py0 - d * tx - e * ty
    return im.transform((w, h), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)


def add_far_scissor_to_90_profile(upper_90_im):
    """Adds the second (far-hand) giant steel scissor peeking ahead/above in 90-deg side profile (steel metal only, zero skin!)."""
    arr = np.array(upper_90_im)
    rgb_i = arr[..., :3].astype(np.int16)
    chroma_span = np.max(rgb_i, axis=-1) - np.min(rgb_i, axis=-1)
    # Keep only low-saturation chrome/steel scissor pixels in x < 345, y < 560 (excludes warm skin hands/wrists!)
    sc_mask = np.zeros(arr.shape[:2], dtype=bool)
    sc_mask[:560, :345] = (arr[:560, :345, 3] > 30) & (chroma_span[:560, :345] < 26)
    sc_mask = ndimage.binary_opening(sc_mask, structure=np.ones((2, 2), bool))
    far_arr = np.zeros_like(arr)
    far_arr[sc_mask] = arr[sc_mask]
    far_rgb = np.clip(far_arr[..., :3].astype(np.float32) * 0.82, 0, 255).astype(np.uint8)
    far_im = Image.fromarray(np.dstack([far_rgb, far_arr[..., 3]]), "RGBA")
    far_shifted = transform_around_pivot(far_im, pivot=(240.0, 410.0), scale_x=0.95, scale_y=0.95, angle_deg=8.0, dx=22.0, dy=-42.0)
    comp = Image.new("RGBA", upper_90_im.size, (0, 0, 0, 0))
    comp.alpha_composite(far_shifted)
    comp.alpha_composite(upper_90_im)
    return comp


def build_135_opposite_legs(lower_135_im):
    """Constructs Stride 2 for 135-deg rear-3/4 view by scissoring Left & Right legs around their hip sockets
    under the pocketed khaki seat block so he cleanly alternates legs while running upper-left!"""
    arr = np.array(lower_135_im)
    H, W = arr.shape[:2]

    # Hip/seat/pockets cap (stays anchored under the belt to cover hip joints seamlessly)
    hip_cap = np.zeros_like(arr)
    hip_cap[:705, :] = arr[:705, :]
    # Feather bottom of hip cap (y=685..705) for invisible blend
    for y in range(685, 705):
        t = 1.0 - (y - 685) / 20.0
        hip_cap[y, :, 3] = (hip_cap[y, :, 3].astype(np.float32) * t).astype(np.uint8)

    # Split Left Leg vs Right Leg along the anatomical crotch seam
    ys, xs = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    crotch_x = 482.0 - np.maximum(0.0, ys - 680.0) * 0.14
    leg_zone = ys >= 655
    left_mask = leg_zone & (xs < crotch_x) & (arr[..., 3] > 0)
    right_mask = leg_zone & (xs >= crotch_x) & (arr[..., 3] > 0)

    left_arr = np.zeros_like(arr)
    left_arr[left_mask] = arr[left_mask]
    right_arr = np.zeros_like(arr)
    right_arr[right_mask] = arr[right_mask]

    left_im = Image.fromarray(left_arr, "RGBA")
    right_im = Image.fromarray(right_arr, "RGBA")
    cap_im = Image.fromarray(hip_cap, "RGBA")

    # Swing right leg forward/down (+34 deg CW) to become the planted leg,
    # and swing left leg back/up (-32 deg CCW) to kick up behind him!
    right_planted = transform_around_pivot(right_im, pivot=(525.0, 665.0), scale_x=0.96, scale_y=1.02, angle_deg=34.0, dx=-42.0, dy=28.0)
    left_kicked = transform_around_pivot(left_im, pivot=(418.0, 665.0), scale_x=0.96, scale_y=0.92, angle_deg=-34.0, dx=26.0, dy=-28.0)

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(right_planted)
    out.alpha_composite(left_kicked)
    out.alpha_composite(cap_im)
    return out


# ---------------------------------------------------------------------------
# Snip Glints & True 3D (X, Y, Z) Flying $100 Cash Storm
# ---------------------------------------------------------------------------
def split_bill_halves(bill_im):
    w, h = bill_im.size
    left_h = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    right_h = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = bill_im.load()
    lpx, rpx = left_h.load(), right_h.load()
    for y in range(h):
        cut_x = int(w * 0.5 + (y - h * 0.5) * 0.18)
        for x in range(w):
            c = px[x, y]
            if c[3] == 0:
                continue
            if x < cut_x:
                lpx[x, y] = c
            elif x == cut_x:
                lpx[x, y] = (235, 242, 225, c[3])
                rpx[x, y] = (235, 242, 225, c[3])
            else:
                rpx[x, y] = c
    return left_h, right_h


def draw_snip_glint(canvas, cx, cy, radius=36, angle_deg=18.0):
    sz = radius * 2 + 8
    star = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    mid = sz // 2
    glow = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((mid - radius // 2, mid - radius // 2, mid + radius // 2, mid + radius // 2), fill=(255, 252, 210, 125))
    star = Image.alpha_composite(star, glow.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(star)
    d.polygon([
        (mid, mid - radius), (mid + 5, mid - 5), (mid + radius, mid), (mid + 5, mid + 5),
        (mid, mid + radius), (mid - 5, mid + 5), (mid - radius, mid), (mid - 5, mid - 5),
    ], fill=(255, 255, 245, 240))
    r2 = int(radius * 0.48)
    d.polygon([
        (mid - r2, mid - r2), (mid, mid - 3), (mid + r2, mid - r2), (mid + 3, mid),
        (mid + r2, mid + r2), (mid, mid + 3), (mid - r2, mid + r2), (mid - 3, mid),
    ], fill=(255, 248, 200, 205))
    star = star.rotate(angle_deg, resample=Image.BICUBIC)
    canvas.alpha_composite(star, (int(cx - mid), int(cy - mid)))


def warp_bill(bill_im, scale, flutter_phase, spin_deg, alpha_mult=1.0):
    bw, bh = bill_im.size
    squeeze = 0.42 + 0.58 * abs(math.cos(flutter_phase))
    nw = max(8, int(round(bw * scale)))
    nh = max(6, int(round(bh * scale * squeeze)))
    resized = bill_im.resize((nw, nh), Image.LANCZOS)
    shade = 0.88 + 0.20 * math.sin(flutter_phase)
    rgb = ImageEnhance.Brightness(resized.convert("RGB")).enhance(shade)
    r, g, b = rgb.split()
    a = resized.getchannel("A")
    if alpha_mult < 0.999:
        a = a.point(lambda v: int(round(v * alpha_mult)))
    return Image.merge("RGBA", (r, g, b, a)).rotate(spin_deg, resample=Image.BICUBIC, expand=True)


def build_3d_money_specs(num_bills=36):
    """3D character-local cash trajectories!
    Character-local coords around waist center (0, 0, 0):
      +X = character's physical left (viewer-right at 0 deg Front)
      +Y = downward in screen pixels
      +Z = character's forward running direction (toward camera at 0 deg Front, away at 180 deg Back)
    """
    specs = []
    golden = 2.399963229728653
    for i in range(num_bills):
        az = (i * golden) % (2.0 * math.pi)
        # Emit from left/right/back hip pockets & waist, bursting outward & trailing backward (-Z) as he sprints!
        ux = math.cos(az)
        uz = math.sin(az) - 0.55  # strong backward wake trail (-Z) as he runs forward (+Z)!
        norm_xz = math.hypot(ux, uz) + 1e-5
        ux, uz = ux / norm_xz, uz / norm_xz

        # Vertical velocity: mix of upward fountain bursts (-Y) and mid/low waist sprays (+Y)
        uy = -0.65 + (i % 7) * 0.22

        # Keep front (+Z) bills away from his face/chest center so 0° Front keeps his evil grin unobstructed!
        if uz > 0.25 and abs(ux) < 0.65 and uy < 0.15:
            ux = -0.85 if (i % 2 == 0) else 0.85
            uz = 0.20

        emit_x = (92.0 if ux >= 0 else -92.0) * (0.65 + 0.35 * abs(ux))
        emit_y = 25.0 + ((i % 5) - 2) * 22.0
        emit_z = -35.0 + uz * 30.0

        travel = 235.0 + (i % 6) * 42.0
        gravity = 82.0 + (i % 4) * 22.0
        phase0 = (i * 0.61803398875) % 1.0
        cycles = 1 if (i % 3 != 0) else 2  # integer cycles per 8-frame loop -> 100% seamless!
        specs.append({
            "emit": (emit_x, emit_y, emit_z),
            "vel": (ux, uy, uz),
            "travel": travel,
            "gravity": gravity,
            "phase0": phase0,
            "cycles": cycles,
            "spin0": (i * 53.0) % 360.0,
            "spin_dir": 1 if (i % 2 == 0) else -1,
            "scale0": 0.66 + (i % 5) * 0.12,
            "bill_idx": i,
        })
    return specs


def project_3d_point(x3, y3, z3, dir_idx, center_x, waist_y):
    """Projects character-local (x3, y3, z3) into screen (sx, sy, cam_z, persp) for camera yaw = dir_idx * 45 deg.
    Convention verification:
      - dir 0 (0° Front):   camera in front (+Z), sees +X on screen-right, +Z comes toward viewer (cam_z > 0).
      - dir 1 (45° F-Left): character runs toward bottom-left (screen -X, +Z).
      - dir 2 (90° Left):   character runs horizontally toward screen-left (-X)!
      - dir 4 (180° Back):  character runs away (-Z toward camera -> wake trail flies AT camera!).
    """
    yaw = math.radians(dir_idx * 45.0)
    cy, sy_ang = math.cos(yaw), math.sin(yaw)
    # Rotate around vertical Y axis:
    # At yaw=0:   x_cam = +x3, z_cam = +z3
    # At yaw=90:  z3=+1 (forward) maps to x_cam = -1 (screen-left!), x3=+1 (char left) maps to z_cam = +1 (toward viewer!)
    x_cam = x3 * cy - z3 * sy_ang
    z_cam = x3 * sy_ang + z3 * cy
    persp = 1.0 / max(0.55, 1.0 - z_cam * 0.00085)
    sx = center_x + x_cam * persp
    sy = waist_y + y3 * persp - z_cam * 0.06  # slight 3D camera elevation tilt
    return sx, sy, z_cam, persp


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROGS_DIR, exist_ok=True)

    print("1/5 Keying all canonical 360° turnaround renders...")
    keyed = {}
    for k, fn in FILES.items():
        p = os.path.join(BRAIN, fn)
        shutil.copy(p, os.path.join(RAW_DIR, f"{k}.jpg"))
        keyed[k] = key_magenta_fast(Image.open(p))

    # Extract clean characters & photorealistic $100 bills
    c0_open, bills_open = largest_component_rgba(keyed["0_open"], also_return_islands=True)
    c0_half, _ = largest_component_rgba(keyed["0_half"])
    c0_shut, bills_shut = largest_component_rgba(keyed["0_shut"], also_return_islands=True)
    bills = ([bills_shut[0]] if bills_shut else []) + bills_open
    half_bill_l, half_bill_r = split_bill_halves(bills[0])
    print(f"    Extracted {len(bills)} photorealistic $100 bill cutouts!")

    c45_s1, _ = largest_component_rgba(keyed["45_s1_open"])
    c45_s2, _ = largest_component_rgba(keyed["45_s2_shut"])

    c90_s1_open, _ = largest_component_rgba(keyed["90_s1_open"])
    c90_s1_shut, _ = largest_component_rgba(keyed["90_s1_shut"])
    c90_s2_shut, _ = largest_component_rgba(keyed["90_s2_shut"])

    c135_open, _ = largest_component_rgba(keyed["135_open"])
    c135_shut, _ = largest_component_rgba(keyed["135_shut"])

    c180_open, _ = largest_component_rgba(keyed["180_open"])
    c180_shut, _ = largest_component_rgba(keyed["180_shut"])

    print("2/5 Rigging upper/lower body parts & normalizing 360° turntable axis...")
    # --- 0° FRONT ---
    up0_open, low0_s1 = split_upper_lower_generic(c0_open, 600, 275, 650, 385, 535, legs_y_min=665)
    up0_half, _ = split_upper_lower_generic(c0_half, 600, 275, 650, 385, 535, legs_y_min=665)
    up0_shut, _ = split_upper_lower_generic(c0_shut, 600, 275, 650, 385, 535, legs_y_min=665)
    low0_s2 = mirror_horiz_around_x(low0_s1, 460)

    # --- 45° FRONT-LEFT ---
    up45_open, low45_s1 = split_upper_lower_generic(c45_s1, 575, 405, 680, 435, 625, legs_y_min=640)
    up45_shut, low45_s2 = split_upper_lower_generic(c45_s2, 575, 405, 680, 435, 625, legs_y_min=640)

    # --- 90° LEFT SIDE PROFILE (with dual offset giant scissors!) ---
    up90_open_raw, low90_s1 = split_upper_lower_generic(c90_s1_open, 595, 435, 690, 460, 595, legs_y_min=655)
    up90_shut_raw, _ = split_upper_lower_generic(c90_s1_shut, 595, 435, 690, 460, 595, legs_y_min=655)
    _, low90_s2_raw = split_upper_lower_generic(c90_s2_shut, 585, 475, 690, 500, 630, legs_y_min=645)
    # Lock 90_s2 belt directly under 90_s1 polo hem (dx=-42, dy=+16)
    low90_s2 = transform_around_pivot(low90_s2_raw, pivot=(540.0, 650.0), scale_x=0.96, scale_y=0.96, dx=-42.0, dy=16.0)
    up90_open = add_far_scissor_to_90_profile(up90_open_raw)
    up90_shut = add_far_scissor_to_90_profile(up90_shut_raw)

    # --- 135° BACK-LEFT ---
    up135_open, low135_s1 = split_upper_lower_generic(c135_open, 570, 310, 625, 395, 555, legs_y_min=645)
    up135_shut, _ = split_upper_lower_generic(c135_shut, 570, 310, 625, 395, 555, legs_y_min=645)
    low135_s2 = build_135_opposite_legs(low135_s1)

    # --- 180° DIRECT BACK ---
    up180_open, low180_s1 = split_upper_lower_generic(c180_open, 575, 290, 620, 375, 530, legs_y_min=650)
    up180_shut, _ = split_upper_lower_generic(c180_shut, 575, 290, 620, 375, 530, legs_y_min=650)
    low180_s2 = mirror_horiz_around_x(low180_s1, 450)

    # Canonical angle rig dictionary:
    # Align every angle so torso spine sits cleanly at CANVAS_CX and head crown sits at y ~ 85 on (1300 x 1400) stage!
    STAGE_W, STAGE_H = 1300, 1400
    STAGE_CX = STAGE_W // 2  # 640
    WAIST_STAGE_Y = 675.0

    # Per-canonical-angle normalization (src_spine_x, src_waist_y, base_scale, blade_tips_shut)
    RIGS = {
        0: {
            "up_open": up0_open, "up_half": up0_half, "up_shut": up0_shut,
            "low_s1": low0_s1, "low_s2": low0_s2,
            "spine_x": 460.0, "waist_y": 640.0, "scale": 1.00,
            "blades": [(168.0, 292.0, -1), (750.0, 292.0, 1)],
        },
        1: {
            "up_open": up45_open, "up_half": None, "up_shut": up45_shut,
            "low_s1": low45_s1, "low_s2": low45_s2,
            "spine_x": 521.0, "waist_y": 612.0, "scale": 1.02,
            "blades": [(155.0, 315.0, -1), (165.0, 488.0, -1)],
        },
        2: {
            "up_open": up90_open, "up_half": None, "up_shut": up90_shut,
            "low_s1": low90_s1, "low_s2": low90_s2,
            "spine_x": 498.0, "waist_y": 648.0, "scale": 1.03,
            "blades": [(135.0, 275.0, -1), (162.0, 232.0, -1)],
        },
        3: {
            "up_open": up135_open, "up_half": None, "up_shut": up135_shut,
            "low_s1": low135_s1, "low_s2": low135_s2,
            "spine_x": 444.0, "waist_y": 612.0, "scale": 1.00,
            "blades": [(142.0, 265.0, -1), (822.0, 265.0, 1)],
        },
        4: {
            "up_open": up180_open, "up_half": None, "up_shut": up180_shut,
            "low_s1": low180_s1, "low_s2": low180_s2,
            "spine_x": 450.0, "waist_y": 625.0, "scale": 1.00,
            "blades": [(170.0, 265.0, -1), (812.0, 265.0, 1)],
        },
    }

    # 8-frame run & snip cycle per direction (2 brisk footstrikes + 2 giant scissor SNIPs per 8-frame loop):
    #   f % 4 == 0: Drive / Reach     | Scissors WIDE OPEN  | Stride knee rising
    #   f % 4 == 1: High-Knee Peak    | Scissors LUNGING    | Airborne bounce up (-14px)
    #   f % 4 == 2: *SNIP!* IMPACT!   | Scissors SLAM SHUT! | Lunge forward/down (+9px) + metallic glint + sliced bill!
    #   f % 4 == 3: Passing Push-Off  | Scissors OPENING    | Legs scissoring to opposite stride (-5px)
    body_dys = [-2.0, -14.0, 9.0, -5.0]
    upper_lunge = [0.995, 1.02, 1.048, 1.01]
    upper_tilt = [-2.4, -1.0, 1.2, 1.6]
    lower_sy = [0.97, 1.01, 0.96, 0.90]
    lower_sx = [1.00, 1.025, 1.01, 0.97]
    lower_tilt = [1.8, 3.0, 1.8, -1.0]

    def render_canonical_body(canon_dir, f_phase):
        """Renders ONLY the character + scissor glints + sliced bills onto a (STAGE_W, STAGE_H) RGBA canvas."""
        rig = RIGS[canon_dir]
        half_idx = 0 if (f_phase < 4) else 1
        s = f_phase % 4
        side = 1.0 if half_idx == 0 else -1.0

        # Choose lower stride (Stride 1 on frames 0..3, Stride 2 on frames 4..7)
        low_src = rig["low_s1"] if half_idx == 0 else rig["low_s2"]

        # Choose upper scissor state
        if s == 0:
            up_src = rig["up_open"]
        elif s == 1:
            up_src = rig["up_half"] if rig["up_half"] is not None else rig["up_open"]
        elif s == 2:
            up_src = rig["up_shut"]
        else:
            up_src = rig["up_half"] if rig["up_half"] is not None else rig["up_shut"]

        bsc = rig["scale"]
        sp_x, wy = rig["spine_x"], rig["waist_y"]
        base_dx = STAGE_CX - sp_x
        base_dy = WAIST_STAGE_Y - wy

        # For side/diagonal views, lean slightly into running direction (-X) on chop beat!
        run_lean_x = (-8.0 if s == 2 else (4.0 if s == 0 else 0.0)) if canon_dir in (1, 2, 3) else (-5.0 * side if s == 1 else 0.0)
        dy = body_dys[s]

        # Place source onto stage first around (sp_x, wy) -> (STAGE_CX, WAIST_STAGE_Y)
        stage_low = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        stage_up = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        pad_x = int(round(base_dx))
        pad_y = int(round(base_dy))
        stage_low.paste(low_src, (pad_x, pad_y))
        stage_up.paste(up_src, (pad_x, pad_y))

        tilt_factor = side if canon_dir in (0, 4) else (1.0 if s in (1, 2) else -0.6)
        w_low = transform_around_pivot(
            stage_low,
            pivot=(STAGE_CX, WAIST_STAGE_Y),
            scale_x=bsc * lower_sx[s],
            scale_y=bsc * lower_sy[s],
            angle_deg=lower_tilt[s] * tilt_factor * (1.0 if canon_dir in (0, 4) else 0.55),
            dx=run_lean_x,
            dy=dy,
        )
        w_up = transform_around_pivot(
            stage_up,
            pivot=(STAGE_CX, WAIST_STAGE_Y - 15.0),
            scale_x=bsc * upper_lunge[s],
            scale_y=bsc * upper_lunge[s],
            angle_deg=upper_tilt[s] * tilt_factor * (1.0 if canon_dir in (0, 4) else 0.65),
            dx=run_lean_x,
            dy=dy,
        )

        char_layer = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        char_layer.alpha_composite(w_low)
        char_layer.alpha_composite(w_up)

        # Add gleaming metallic *SNIP!* glint + sliced $100 bill halves flying off scissor tips on s == 2, 3!
        if s in (2, 3):
            snip_age = (s - 2) * 0.48
            fade = 1.0 - snip_age * 0.85
            usc = bsc * upper_lunge[s]
            for bx_raw, by_raw, dsign in rig["blades"]:
                bcx = STAGE_CX + (bx_raw - sp_x) * usc + run_lean_x
                bcy = (WAIST_STAGE_Y - 15.0) + (by_raw - (wy - 15.0)) * usc + dy
                spread = 16.0 + 78.0 * snip_age
                drop = 34.0 * (snip_age ** 1.4)
                hl = warp_bill(half_bill_l, 0.56, snip_age * 2.4, -28.0 - 70.0 * snip_age, fade)
                hr = warp_bill(half_bill_r, 0.56, snip_age * 2.4 + 0.6, 25.0 + 70.0 * snip_age, fade)
                char_layer.alpha_composite(hl, (int(bcx - spread - hl.width // 2), int(bcy + drop - hl.height // 2)))
                char_layer.alpha_composite(hr, (int(bcx + spread - hr.width // 2), int(bcy + drop + 8 - hr.height // 2)))
                if s == 2:
                    draw_snip_glint(char_layer, bcx, bcy - 26, radius=36, angle_deg=18.0 * dsign)

        return char_layer

    print("3/5 Compositing all 8 directions x 8 frames (64 frames) with 3D-projected flying cash...")
    money_specs = build_3d_money_specs(num_bills=36)

    # Mirror map for directions 5 (225°), 6 (270°), 7 (315°):
    # Shift phase by +4 frames (half cycle) when mirroring so physical left/right legs stay locked across all 360°!
    DIR_MAP = {
        0: (0, False, 0),
        1: (1, False, 0),
        2: (2, False, 0),
        3: (3, False, 0),
        4: (4, False, 0),
        5: (3, True, 4),   # 225° = mirror of 135°
        6: (2, True, 4),   # 270° = mirror of 90°
        7: (1, True, 4),   # 315° = mirror of 45°
    }

    grid_raw = [[None] * N_RUN for _ in range(N_DIRS)]
    union_box = None

    for d in range(N_DIRS):
        canon_d, do_flip, phase_shift = DIR_MAP[d]
        for f in range(N_RUN):
            t_norm = f / float(N_RUN)
            char_im = render_canonical_body(canon_d, (f + phase_shift) % N_RUN)
            if do_flip:
                char_im = ImageOps.mirror(char_im)

            back_money = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            front_money = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))

            for sp in money_specs:
                p = (t_norm * sp["cycles"] + sp["phase0"]) % 1.0
                if p < 0.12:
                    alpha_m = p / 0.12
                elif p > 0.78:
                    alpha_m = (1.0 - p) / 0.22
                else:
                    alpha_m = 1.0

                dist = sp["travel"] * (0.12 + 0.88 * (1.0 - (1.0 - p) ** 1.55))
                sway = 20.0 * math.sin(2.0 * math.pi * p + sp["phase0"] * 6.0)
                vx, vy, vz = sp["vel"]
                ex, ey, ez = sp["emit"]

                x3 = ex + vx * dist + sway * (-vz)
                y3 = ey + vy * dist + sp["gravity"] * (p * p)
                z3 = ez + vz * dist + sway * vx

                sx, sy, z_cam, persp = project_3d_point(x3, y3, z3, d, STAGE_CX, WAIST_STAGE_Y)

                # Keep front-facing angles (0, 1, 7) from placing foreground bills over his hilarious evil face!
                is_front_layer = z_cam > 45.0
                if d in (0, 1, 7) and is_front_layer and sy < WAIST_STAGE_Y - 40.0:
                    is_front_layer = False

                flutter = 2.0 * math.pi * (p * 2.0 + sp["phase0"]) + math.radians(d * 45.0) * 0.5
                spin = sp["spin0"] + sp["spin_dir"] * p * 360.0
                sc = sp["scale0"] * persp * (0.78 + 0.30 * p)
                wb = warp_bill(bills[sp["bill_idx"] % len(bills)], sc, flutter, spin, alpha_m)

                target = front_money if is_front_layer else back_money
                target.alpha_composite(wb, (int(round(sx - wb.width / 2)), int(round(sy - wb.height / 2))))

            full = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
            full.alpha_composite(back_money)
            full.alpha_composite(char_im)
            full.alpha_composite(front_money)
            grid_raw[d][f] = full

            bb = full.getbbox()
            if bb:
                if union_box is None:
                    union_box = list(bb)
                else:
                    union_box[0] = min(union_box[0], bb[0])
                    union_box[1] = min(union_box[1], bb[1])
                    union_box[2] = max(union_box[2], bb[2])
                    union_box[3] = max(union_box[3], bb[3])

    # Symmetric crop around STAGE_CX so spinning 360° stays dead-centered on the vertical axis!
    half_span_x = max(STAGE_CX - union_box[0], union_box[2] - STAGE_CX) + 14
    cx0 = max(0, STAGE_CX - half_span_x)
    cx1 = min(STAGE_W, STAGE_CX + half_span_x)
    cy0 = max(0, union_box[1] - 14)
    cy1 = min(STAGE_H, union_box[3] + 14)
    if (cx1 - cx0) % 2:
        cx1 += 1
    if (cy1 - cy0) % 2:
        cy1 += 1

    target_h = 680
    target_w = int(round((cx1 - cx0) * (target_h / float(cy1 - cy0))))
    if target_w % 2:
        target_w += 1

    print(f"4/5 Saving 64 transparent PNG frames ({target_w}x{target_h}), 8x8 sheet, 360° GIF, and SPR32...")
    grid_final = [[None] * N_RUN for _ in range(N_DIRS)]
    for d in range(N_DIRS):
        for f in range(N_RUN):
            cropped = grid_raw[d][f].crop((cx0, cy0, cx1, cy1)).resize((target_w, target_h), Image.LANCZOS)
            grid_final[d][f] = cropped
            cropped.save(os.path.join(OUT_DIR, f"scissor_d{d}_f{f}.png"))

    # Also keep scissor_00..07 aliases for d=0 compatibility
    for f in range(N_RUN):
        shutil.copy(os.path.join(OUT_DIR, f"scissor_d0_f{f}.png"), os.path.join(OUT_DIR, f"scissor_{f:02d}.png"))

    # Save 8x8 master sprite sheet (half-res per cell so sheet is crisp 2720x2720 instead of 150MB!)
    cell_w, cell_h = target_w // 2, target_h // 2
    sheet = Image.new("RGBA", (cell_w * N_RUN, cell_h * N_DIRS), (0, 0, 0, 0))
    preview_sheet = Image.new("RGB", (cell_w * N_RUN, cell_h * N_DIRS), (32, 35, 42))
    for d in range(N_DIRS):
        for f in range(N_RUN):
            sm = grid_final[d][f].resize((cell_w, cell_h), Image.LANCZOS)
            sheet.paste(sm, (f * cell_w, d * cell_h))
            bg_c = Image.new("RGBA", (cell_w, cell_h), (32, 35, 42, 255))
            bg_c.alpha_composite(sm)
            preview_sheet.paste(bg_c.convert("RGB"), (f * cell_w, d * cell_h))

    sheet_path = os.path.join(OUT_DIR, "scissor_360_sheet_8x8.png")
    sheet.save(sheet_path)
    preview_turnaround_brain = os.path.join(BRAIN, "scissor_360_turnaround_sheet.png")
    # Save a compact 8-angle strip (1 column per angle) for crisp artifact preview!
    strip_8 = Image.new("RGB", (cell_w * 4, cell_h * 2), (32, 35, 42))
    for d in range(N_DIRS):
        c, r = d % 4, d // 4
        bg_c = Image.new("RGBA", (cell_w, cell_h), (32, 35, 42, 255))
        bg_c.alpha_composite(grid_final[d][(d * 2) % N_RUN].resize((cell_w, cell_h), Image.LANCZOS))
        strip_8.paste(bg_c.convert("RGB"), (c * cell_w, r * cell_h))
    strip_8.save(preview_turnaround_brain)

    # Build 360-degree spinning + running showcase GIF (24 frames = 3 steps per angle x 8 angles!)
    gif_w, gif_h = int(round(target_w * 0.58)), int(round(target_h * 0.58))
    tile = 20
    bg_check = Image.new("RGBA", (gif_w, gif_h), (34, 37, 43, 255))
    bd = ImageDraw.Draw(bg_check)
    for yy in range(0, gif_h, tile):
        for xx in range(0, gif_w, tile):
            if ((xx // tile) + (yy // tile)) % 2 == 0:
                bd.rectangle((xx, yy, xx + tile - 1, yy + tile - 1), fill=(44, 48, 56, 255))

    spin_gif_frames = []
    for step in range(24):
        d = (step // 3) % N_DIRS
        f = step % N_RUN
        comp = bg_check.copy()
        comp.alpha_composite(grid_final[d][f].resize((gif_w, gif_h), Image.LANCZOS))
        spin_gif_frames.append(comp.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG))

    gif_brain = os.path.join(BRAIN, "scissor_360_spin.gif")
    spin_gif_frames[0].save(gif_brain, save_all=True, append_images=spin_gif_frames[1:], duration=90, loop=0)
    shutil.copy(gif_brain, os.path.join(OUT_DIR, "scissor_360_spin.gif"))

    # Bake 56-frame 8-direction Quake SPR32 (progs/fr_scissors.spr32) matching build_friend_sprites.py:
    #   frames 0..7:   1 idle/ready frame per direction (d=0..7)
    #   frames 8..55:  6 run+snip frames per direction (d=0..7)
    spr_h = 152
    spr_w = max(2, int(round(target_w * (spr_h / float(target_h)))))
    if spr_w % 2:
        spr_w += 1
    foot_oy = int(round(spr_h * 0.94))
    rad = math.hypot(spr_w / 2.0, spr_h)
    spr_frames = []
    for d in range(N_DIRS):
        spr_frames.append(grid_final[d][0].resize((spr_w, spr_h), Image.LANCZOS))
    for d in range(N_DIRS):
        for k in range(6):
            fi = min(N_RUN - 1, int(round(k * N_RUN / 6.0)) % N_RUN)
            spr_frames.append(grid_final[d][fi].resize((spr_w, spr_h), Image.LANCZOS))

    spr_bytes = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, 0, rad, spr_w, spr_h, len(spr_frames), 0.0, 0))
    for sim in spr_frames:
        spr_bytes += struct.pack("<i", 0) + struct.pack("<iiii", -spr_w // 2, foot_oy, spr_w, spr_h) + sim.tobytes()
    spr_path = os.path.join(PROGS_DIR, "fr_scissors.spr32")
    with open(spr_path, "wb") as fp:
        fp.write(spr_bytes)
    print(f"    Wrote 56-frame 360° Quake SPR32 -> {spr_path} ({spr_w}x{spr_h}, {len(spr_bytes)/1e6:.2f} MB)")

    print("5/5 Writing interactive 360° HTML turntable + run viewer...")
    labels_js = "[" + ", ".join(f'"{lbl}"' for lbl in DIR_LABELS) + "]"
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evil Scissor Runner — Full 360° Sprite</title>
<style>
  :root {{ --bg:#16181d; --panel:#23262e; --ink:#eef0f4; --dim:#9aa0ac; --accent:#4ade80; --accent2:#38bdf8; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif; display:flex; flex-direction:column; align-items:center; gap:12px; padding:16px; min-height:100vh; }}
  h1 {{ font-size:20px; margin:2px 0 0; font-weight:700; letter-spacing:-0.01em; }}
  #stage {{ width:min(100%, 780px); aspect-ratio:{target_w}/{target_h}; max-height:64vh; border-radius:12px; display:flex; align-items:center; justify-content:center; overflow:hidden; border:1px solid #343844; position:relative; cursor:grab; touch-action:none; user-select:none; }}
  #stage.drag {{ cursor:grabbing; }}
  #stage.checker {{ background:repeating-conic-gradient(#2c303a 0% 25%, #22252d 0% 50%) 0 0/24px 24px; }}
  #stage.quake {{ background:radial-gradient(circle at 50% 62%, #3d2e22 0%, #1c1510 72%, #0e0b09 100%); }}
  #stage.green {{ background:#0f172a; }}
  #stage img {{ width:100%; height:100%; object-fit:contain; pointer-events:none; }}
  #badge {{ position:absolute; top:12px; left:14px; background:rgba(15,18,24,0.82); border:1px solid #383d4a; border-radius:8px; padding:5px 11px; font-size:13px; font-weight:600; color:var(--accent); pointer-events:none; backdrop-filter:blur(6px); }}
  #draghint {{ position:absolute; bottom:10px; right:14px; background:rgba(15,18,24,0.75); border-radius:6px; padding:4px 9px; font-size:12px; color:var(--dim); pointer-events:none; }}
  .row {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:center; width:min(100%,780px); background:var(--panel); border-radius:10px; padding:11px 14px; }}
  input[type=range] {{ flex:1 1 160px; accent-color:var(--accent); }}
  button {{ background:var(--accent); color:#0f172a; border:0; border-radius:6px; padding:8px 13px; font:inherit; font-weight:700; cursor:pointer; }}
  button.spin {{ background:var(--accent2); color:#082f49; }}
  button.alt {{ background:#3a3f4b; color:var(--ink); font-weight:600; }}
  label {{ color:var(--dim); display:flex; gap:6px; align-items:center; font-size:14px; }}
  #info {{ color:var(--dim); min-width:16ch; text-align:right; font-variant-numeric:tabular-nums; font-size:13px; }}
  #strip {{ display:grid; grid-template-columns:repeat(8, 1fr); gap:6px; width:min(100%,780px); }}
  @media (max-width:680px) {{ #strip {{ grid-template-columns:repeat(4, 1fr); }} }}
  #strip button {{ padding:4px 4px 2px; background:var(--panel); border:2px solid transparent; border-radius:8px; display:flex; flex-direction:column; align-items:center; gap:2px; overflow:hidden; color:var(--dim); font-size:11px; font-weight:600; }}
  #strip button.on {{ border-color:var(--accent); color:var(--ink); background:#2c313d; }}
  #strip img {{ width:100%; aspect-ratio:{target_w}/{target_h}; object-fit:contain; display:block; }}
  p.hint {{ color:var(--dim); margin:0; font-size:13px; text-align:center; }}
</style>
</head>
<body>
  <h1>Evil Scissor Runner &mdash; Full 360&deg; Turnaround Sprite</h1>
  <div id="stage" class="checker">
    <div id="badge">0&deg; Front</div>
    <img id="view" alt="360 sprite frame">
    <div id="draghint">&#x2194; Drag anywhere to spin 360&deg;</div>
  </div>
  <div class="row">
    <button id="play">Pause Run</button>
    <button class="spin" id="orbit">Auto-Spin 360&deg;: ON</button>
    <label>Angle <input id="ang" type="range" min="0" max="7" value="0" style="flex:0 0 130px"></label>
    <label>FPS <input id="fps" type="range" min="4" max="20" value="11" style="flex:0 0 90px"></label>
    <button class="alt" id="bgbtn">BG: Checker</button>
    <span id="info">0&deg; &bull; Frame 0/7</span>
  </div>
  <p class="hint">Drag left/right on the sprite or press <b>Left/Right Arrows</b> to turn 360&deg; &bull; <b>Up/Down Arrows</b> step run frames &bull; <b>Space</b> pauses</p>
  <div id="strip"></div>
<script>
const DIRS = {N_DIRS}, FRAMES = {N_RUN};
const LABELS = {labels_js};
const src = (d, f) => `scissor_d${{d}}_f${{f}}.png`;
const view = document.getElementById("view"), badge = document.getElementById("badge"),
      info = document.getElementById("info"), playBtn = document.getElementById("play"),
      orbitBtn = document.getElementById("orbit"), angEl = document.getElementById("ang"),
      fpsEl = document.getElementById("fps"), stage = document.getElementById("stage"),
      strip = document.getElementById("strip"), bgbtn = document.getElementById("bgbtn");

let curDir = 0, curFrame = 0, running = true, autoSpin = true;
let lastRun = 0, lastSpin = 0;
const bgs = ["checker", "quake", "green"], bgNames = ["Checker", "Quake Dungeon", "Dark Slate"];
let bgi = 0;

// Preload all 64 frames for instant zero-flicker 360 scrubbing!
for (let d = 0; d < DIRS; d++) {{
  for (let f = 0; f < FRAMES; f++) {{
    const im = new Image();
    im.src = src(d, f);
  }}
}}

const thumbs = [], thumbImgs = [];
for (let d = 0; d < DIRS; d++) {{
  const b = document.createElement("button");
  b.title = LABELS[d];
  const im = document.createElement("img");
  im.src = src(d, 0);
  const sp = document.createElement("span");
  sp.textContent = (d * 45) + "°";
  b.appendChild(im);
  b.appendChild(sp);
  b.onclick = () => {{ autoSpin = false; syncButtons(); setView(d, curFrame); }};
  strip.appendChild(b);
  thumbs.push(b);
  thumbImgs.push(im);
}}

function setView(d, f) {{
  curDir = ((d % DIRS) + DIRS) % DIRS;
  curFrame = ((f % FRAMES) + FRAMES) % FRAMES;
  view.src = src(curDir, curFrame);
  badge.textContent = LABELS[curDir];
  angEl.value = curDir;
  info.textContent = (curDir * 45) + "° • Frame " + curFrame + "/" + (FRAMES - 1);
  thumbs.forEach((t, k) => t.classList.toggle("on", k === curDir));
  thumbImgs.forEach((im, k) => {{ im.src = src(k, curFrame); }});
}}

function syncButtons() {{
  playBtn.textContent = running ? "Pause Run" : "Play Run";
  orbitBtn.textContent = "Auto-Spin 360°: " + (autoSpin ? "ON" : "OFF");
  orbitBtn.className = autoSpin ? "spin" : "alt";
}}

playBtn.onclick = () => {{ running = !running; syncButtons(); }};
orbitBtn.onclick = () => {{ autoSpin = !autoSpin; syncButtons(); }};
angEl.oninput = () => {{ autoSpin = false; syncButtons(); setView(+angEl.value, curFrame); }};
bgbtn.onclick = () => {{
  stage.classList.remove(bgs[bgi]);
  bgi = (bgi + 1) % bgs.length;
  stage.classList.add(bgs[bgi]);
  bgbtn.textContent = "BG: " + bgNames[bgi];
}};

addEventListener("keydown", e => {{
  if (e.code === "Space") {{ e.preventDefault(); running = !running; syncButtons(); }}
  else if (e.code === "ArrowRight") {{ e.preventDefault(); autoSpin = false; syncButtons(); setView(curDir + 1, curFrame); }}
  else if (e.code === "ArrowLeft")  {{ e.preventDefault(); autoSpin = false; syncButtons(); setView(curDir - 1, curFrame); }}
  else if (e.code === "ArrowUp")    {{ e.preventDefault(); running = false; syncButtons(); setView(curDir, curFrame + 1); }}
  else if (e.code === "ArrowDown")  {{ e.preventDefault(); running = false; syncButtons(); setView(curDir, curFrame - 1); }}
}});

let dragX = null, dragStartDir = 0;
stage.addEventListener("pointerdown", e => {{
  dragX = e.clientX;
  dragStartDir = curDir;
  autoSpin = false;
  syncButtons();
  stage.classList.add("drag");
  stage.setPointerCapture(e.pointerId);
}});
stage.addEventListener("pointermove", e => {{
  if (dragX === null) return;
  const steps = Math.round((e.clientX - dragX) / 38);
  setView(dragStartDir - steps, curFrame);
}});
const endDrag = () => {{ dragX = null; stage.classList.remove("drag"); }};
stage.addEventListener("pointerup", endDrag);
stage.addEventListener("pointercancel", endDrag);

function tick(t) {{
  const runInterval = 1000 / (+fpsEl.value);
  let changed = false, nextD = curDir, nextF = curFrame;
  if (running && t - lastRun > runInterval) {{
    lastRun = t;
    nextF = (curFrame + 1) % FRAMES;
    changed = true;
  }}
  if (autoSpin && t - lastSpin > runInterval * 3.0) {{
    lastSpin = t;
    nextD = (curDir + 1) % DIRS;
    changed = true;
  }}
  if (changed) setView(nextD, nextF);
  requestAnimationFrame(tick);
}}
setView(0, 0);
requestAnimationFrame(tick);
</script>
</body>
</html>
"""
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fp:
        fp.write(html)
    print("Done! Open ->", os.path.join(OUT_DIR, "index.html"))


if __name__ == "__main__":
    main()
