r"""Complete 360° Realistic Animation Engine for WHEELMAN (BakersfieldQuake).

Synthesizes all 9 requested animations in FULL 8-DIRECTION 360° (keeping full bare nudity):
  1. Running w/ Stuck Metal Bar & Wheels (8 dirs x 10 frames = 80 frames)
  2. Raising Hands in the Air & Kicking Legs w/ Stuck Bar & Wheels (8 dirs x 10 frames = 80 frames)
  3. Picking Up Bar & Wheels Like Heavy Weights — Squat Clean & Overhead Press (8 dirs x 12 frames = 96 frames)
  4. Winding Up & Throwing the Metal Bar & Wheels in 3D Space (8 dirs x 12 frames = 96 frames)
  5. Exuberant Barefoot Wheelman Disco/Jig Dance w/ Stuck Bar & Wheels (8 dirs x 12 frames = 96 frames)
  6. Running Completely Nude Holding Bar & Wheels Overhead (8 dirs x 10 frames = 80 frames)
  7. Spinning the Bar & Wheels Around in a 360° Cyclone (8 dirs x 12 frames = 96 frames)
  8. Exploding — Quake Gib & Fireball Detonation w/ Flying Limbs & Wheels (8 dirs x 12 frames = 96 frames)
  9. Turning Into a Robot — Nanotech Chrome/Titanium Mecha-Wheelman Transformation (8 dirs x 14 frames = 112 frames)

Total: 832 high-res (360x360) RGBA frames!
Outputs:
  - G:\Quake\Combat\BakersfieldQuake\progs\wheelman_actions.spr32  (DarkPlaces 32-bit sprite)
  - G:\Quake\Combat\BakersfieldQuake\wheelman_actions_sprite\      (PNG frames + diagnostic contact sheets)
  - G:\Quake\Combat\BakersfieldQuake\wheelman_animations.html      (Self-contained interactive 360° inspector)
"""
import glob
import math
import os
import shutil
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import wheelman_actions_core as core
import wheelman_extra_anims as extra
import wheelman_html_template as html_gen

MOD_DIR = core.MOD_DIR
BRAIN_DIR = r"C:\Users\qxdc\.gemini\antigravity\brain\b398f8e3-ce4c-44a3-a430-10a5ee081a6b"
REF_CACHE_DIR = os.path.join(HERE, "ref")
RIG3D_DIR = os.path.join(HERE, "rig3d")
SPRITE_OUT_DIR = os.path.join(MOD_DIR, "wheelman_actions_sprite")
PROGS_PATH = os.path.join(MOD_DIR, "progs", "wheelman_actions.spr32")
HTML_OUT_PATH = os.path.join(MOD_DIR, "wheelman_animations.html")

W_C, H_C = core.CANVAS_WH
GY = core.GROUND_Y


def resolve_plate_path(prefix):
    """Finds generated studio plate in REF_CACHE_DIR or BRAIN_DIR and caches a clean copy."""
    os.makedirs(REF_CACHE_DIR, exist_ok=True)
    cached = os.path.join(REF_CACHE_DIR, f"{prefix}.jpg")
    # Search BRAIN_DIR for newest matching prefix_<timestamp>.(jpg|png)
    candidates = []
    for ext in ("jpg", "png", "jpeg", "webp"):
        candidates.extend(glob.glob(os.path.join(BRAIN_DIR, f"{prefix}_*.{ext}")))
        candidates.extend(glob.glob(os.path.join(BRAIN_DIR, f"{prefix}.{ext}")))
    if candidates:
        best = max(candidates, key=os.path.getmtime)
        if not os.path.exists(cached) or os.path.getmtime(best) > os.path.getmtime(cached):
            Image.open(best).convert("RGB").save(cached, quality=95)
        return cached
    if os.path.exists(cached):
        return cached
    raise FileNotFoundError(f"Missing studio plate for prefix '{prefix}' in {BRAIN_DIR}")


def synthesize_run_180_plate():
    """Synthesizes studio-grade 180° direct-rear sprinting plate (ref/run_180.jpg) on pure #FF00FF
    from dance_180 (replacing raised sky-pointing right arm with an athletic forward-pumping sprint arm
    and mounting the gleaming 3D rear chrome exhaust cylinder at the center of the steel axle)."""
    os.makedirs(REF_CACHE_DIR, exist_ok=True)
    out_path = os.path.join(REF_CACHE_DIR, "run_180.jpg")
    d180_path = resolve_plate_path("dance_180")
    rgba = np.array(core.key_studio_magenta(Image.open(d180_path))).astype(np.float32)
    H, W = rgba.shape[:2]  # 1200 x 896
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    # 1) Extract clean left bent runner's arm (x in 190..356, y in 305..565) with zero inner-crook fringe
    arm_crop = rgba[305:565, 190:356].copy()
    ac_y, ac_x = np.mgrid[305:565, 190:356].astype(np.float32)
    rb_ac = arm_crop[..., 0] - arm_crop[..., 2]
    # Remove any tire pixels at bottom-left and any semi-transparent magenta-contaminated border pixels
    bad_ac = ((ac_y > 534) & (rb_ac < 17.0)) | (arm_crop[..., 3] < 225.0) | ((ac_x > 344) & (ac_y > 395))
    arm_crop[bad_ac, 3] = 0.0
    arm_crop[..., 3] = cv2.GaussianBlur(arm_crop[..., 3], (5, 5), 1.0)
    seam_w = np.clip((354.0 - ac_x) / 18.0, 0.0, 1.0)
    arm_crop[..., 3] *= seam_w
    arm_pil = Image.fromarray(np.clip(arm_crop, 0, 255).astype(np.uint8), "RGBA")
    r_arm_pil = ImageOps.mirror(arm_pil).rotate(14.0, resample=Image.BICUBIC, expand=True)

    # 2) Erase the raised disco right arm cleanly (including upper-right trap corner above y=305)
    erase_arm = (
        ((xg > 504.0) & (yg < 292.0))
        | ((xg > 516.0 + (yg - 292.0) * 0.36) & (yg >= 292.0) & (yg < 445.0))
    )
    erase_soft = cv2.GaussianBlur(erase_arm.astype(np.float32), (9, 9), 2.0)
    rgba[..., 3] *= (1.0 - erase_soft)

    base_pil = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")

    # 3) Composite forward-pumping right sprint arm behind right deltoid
    stage = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px_arm = int(round(512))
    py_arm = int(round(284))
    stage.alpha_composite(r_arm_pil, (px_arm, py_arm))
    stage.alpha_composite(base_pil)

    # 4) Mount gleaming 180° central chrome exhaust cylinder from rig3d/rig_d4_s0.png onto center of axle
    rig_rear_path = os.path.join(RIG3D_DIR, "rig_d4_s0.png")
    if os.path.exists(rig_rear_path):
        rig_r = np.array(Image.open(rig_rear_path).convert("RGBA"))
        rh, rw = rig_r.shape[:2]
        ryg, rxg = np.mgrid[0:rh, 0:rw].astype(np.float32)
        cyl_w = np.clip((rw * 0.14 - np.abs(rxg - rw * 0.5)) / 8.0, 0.0, 1.0)
        rig_r[..., 3] = (rig_r[..., 3].astype(np.float32) * cyl_w).astype(np.uint8)
        cyl_pil = Image.fromarray(rig_r, "RGBA")
        core.paste_rotated_rgba(stage, cyl_pil, cx=456.0, cy=692.0, angle_deg=-2.5, sx=1.18, sy=1.18)

    mag_bg = Image.new("RGB", (W, H), (255, 0, 255))
    mag_bg.paste(stage, (0, 0), stage)
    mag_bg.save(out_path, quality=96)
    return out_path


def load_cleaned_bare_plate(
    prefix,
    skin_samples,
    grain_hi,
    rel_box,
    has_attached_rig=True,
    is_rear=False,
    target_h=270.0,
    max_w=332.0,
    pre_mirror=False,
    view_kind=None,
    extra_protect_boxes=None,
):
    path = resolve_plate_path(prefix)
    raw_im = Image.open(path)
    if pre_mirror:
        raw_im = ImageOps.mirror(raw_im)
    rgba = core.key_studio_magenta(raw_im)
    rgba = core.diffuse_shorts_to_bare_skin(
        rgba,
        grain_hi=grain_hi,
        rel_box=rel_box,
        has_attached_rig=has_attached_rig,
        is_rear=is_rear,
        extra_protect_boxes=extra_protect_boxes,
        view_kind=view_kind,
    )
    rgba = core.calibrate_skin_to_ref(rgba, skin_samples, strength=0.50)
    norm = core.normalize_to_canvas(rgba, target_h=target_h, max_w=max_w, ground_y=GY, canvas_wh=core.CANVAS_WH)
    return norm


def build_profile_scissor_run_90(skin_samples, grain_hi, n_frames=10):
    """Builds a true 10-frame full-scissor bipedal profile sprint from run_090_a:
    - Both bare hairy legs genuinely cross & swap front-to-back around the hip socket hidden behind the big wheel!
    - Bottom-padded stage guarantees zero toe clipping during swing!
    - The photographic white-dish wheel + rubber tire physically spins 360° while bobbing with hip impact!"""
    path = resolve_plate_path("run_090_a")
    rgba = core.key_studio_magenta(Image.open(path))
    rgba = core.diffuse_shorts_to_bare_skin(
        rgba, grain_hi=grain_hi, rel_box=(0.20, 0.34, 0.78, 0.85), has_attached_rig=True, is_rear=False, view_kind="side"
    )
    rgba = core.calibrate_skin_to_ref(rgba, skin_samples, strength=0.50)
    arr0 = np.array(rgba).astype(np.float32)
    H0, W = arr0.shape[:2]  # 896 x 1200
    # Pad bottom by 150px so swinging bare feet never clip at y=896!
    H = H0 + 150
    arr = np.zeros((H, W, 4), dtype=np.float32)
    arr[:H0] = arr0
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    wcx, wcy, wrad = 660.0, 468.8, 149.5
    dist_w = np.hypot(xg - wcx, yg - wcy)

    # 1) Circular spinning wheel sprite
    w_alpha = np.clip((wrad + 1.5 - dist_w) / 2.5, 0.0, 1.0) * (arr[..., 3] / 255.0)
    ir = int(math.ceil(wrad + 4))
    wx0, wy0 = int(round(wcx)) - ir, int(round(wcy)) - ir
    wheel_crop = arr[wy0:wy0 + 2 * ir, wx0:wx0 + 2 * ir].copy()
    wheel_crop[..., 3] = w_alpha[wy0:wy0 + 2 * ir, wx0:wx0 + 2 * ir] * 255.0
    wheel_pil = Image.fromarray(np.clip(wheel_crop, 0, 255).astype(np.uint8), "RGBA")

    # 2) Horizontal gleaming chrome exhaust cylinder + black cap behind wheel
    pipe_m = (dist_w > wrad - 6.0) & (xg > 785.0) & (yg >= 365.0) & (yg <= 468.0) & (arr[..., 3] > 20.0)
    pipe_rgba = arr.copy()
    pipe_rgba[..., 3] = arr[..., 3] * cv2.GaussianBlur(pipe_m.astype(np.float32), (5, 5), 1.0)
    pipe_pil = Image.fromarray(np.clip(pipe_rgba, 0, 255).astype(np.uint8), "RGBA")

    # 3) Front bare leg & 4) Back bare leg
    fleg_m = (dist_w > wrad - 3.0) & (xg < 658.0) & (yg > 432.0) & (arr[..., 3] > 20.0)
    bleg_m = (dist_w > wrad - 3.0) & (xg >= 658.0) & (yg > 466.0) & (arr[..., 3] > 20.0)

    hip_x, hip_y = 652.0, 484.0
    thigh_color = np.array([208.0, 166.0, 138.0, 255.0], dtype=np.float32)
    skin_samp = arr[(yg > 480) & (yg < 565) & (xg > 420) & (xg < 500) & (arr[..., 3] > 220)]
    if len(skin_samp) > 50:
        thigh_color[:3] = np.median(skin_samp[:, :3], axis=0)

    def make_leg_layer(leg_mask, bridge_angle_deg):
        la = np.zeros_like(arr)
        soft = cv2.GaussianBlur(leg_mask.astype(np.float32), (5, 5), 1.0)
        la[..., :3] = arr[..., :3]
        la[..., 3] = arr[..., 3] * soft
        ang_r = math.radians(bridge_angle_deg)
        ux, uy = math.cos(ang_r), math.sin(ang_r)
        vx, vy = xg - hip_x, yg - hip_y
        proj = np.clip(vx * ux + vy * uy, 0.0, 155.0)
        perp = np.hypot(vx - proj * ux, vy - proj * uy)
        cap_a = np.clip((46.0 - perp) / 6.0, 0.0, 1.0) * (dist_w < wrad + 6.0)
        need = (cap_a * 255.0) > la[..., 3]
        la[need, :3] = thigh_color[:3]
        la[need, 3] = cap_a[need] * 255.0
        return la

    fleg_arr = make_leg_layer(fleg_m, 158.0)
    bleg_arr = make_leg_layer(bleg_m, 44.0)

    torso_m = (dist_w > wrad - 3.0) & (~pipe_m) & (~fleg_m) & (~bleg_m) & (arr[..., 3] > 15.0)
    torso_arr = arr.copy()
    torso_arr[..., 3] = arr[..., 3] * cv2.GaussianBlur(torso_m.astype(np.float32), (5, 5), 1.0)
    torso_cap = (np.hypot(xg - 605.0, yg - 430.0) < 62.0) & (dist_w < wrad + 4.0)
    need_t = torso_cap & (torso_arr[..., 3] < 200.0)
    torso_arr[need_t, :3] = thigh_color[:3]
    torso_arr[need_t, 3] = 255.0

    def xform_layer(layer_rgba, piv_x, piv_y, deg, tx=0.0, ty=0.0):
        rad = math.radians(deg)
        c, s_r = math.cos(-rad), math.sin(-rad)
        qx = xg - tx - piv_x
        qy = yg - ty - piv_y
        mx = (piv_x + qx * c - qy * s_r).astype(np.float32)
        my = (piv_y + qx * s_r + qy * c).astype(np.float32)
        return Image.fromarray(core.premul_remap(layer_rgba.astype(np.uint8), mx, my), "RGBA")

    scale_90 = 268.0 / (854.0 - 46.0)
    rw_c = int(round(W * scale_90))
    rh_c = int(round(H * scale_90))
    ox_fixed = int(round(W_C * 0.5 - 635.0 * scale_90))
    oy_base = int(round(GY - 854.0 * scale_90))

    out_frames = []
    for f in range(n_frames):
        ph = f / float(n_frames)
        s = math.cos(2.0 * math.pi * ph)
        u_opp = 0.5 * (1.0 - s)  # 0.0 at f=0 -> 1.0 at f=5 (full opposite stride!)
        u_half = (f % 5) / 5.0
        bounce_px = -6.0 * math.sin(math.pi * u_half) + 2.0 * math.cos(2.0 * math.pi * u_half)

        # Wide athletic scissor: fleg swings all the way back (-76 deg), bleg drives high forward (+62 deg, lifted to ground line!)
        fl_rot = xform_layer(fleg_arr, hip_x, hip_y, deg=-u_opp * 76.0, tx=u_opp * 24.0, ty=-u_opp * 28.0)
        bl_rot = xform_layer(bleg_arr, hip_x, hip_y, deg=+u_opp * 62.0, tx=-u_opp * 72.0, ty=-u_opp * 68.0)

        f_arm_w = np.clip((435.0 - xg) / 30.0, 0.0, 1.0) * np.clip((yg - 185.0) / 25.0, 0.0, 1.0)
        b_arm_w = np.clip((xg - 535.0) / 35.0, 0.0, 1.0) * np.clip((385.0 - yg) / 25.0, 0.0, 1.0)
        dy_arms = (-u_opp * 36.0 * f_arm_w) + (u_opp * 40.0 * b_arm_w)
        dx_arms = (u_opp * 44.0 * f_arm_w) - (u_opp * 48.0 * b_arm_w)
        torso_warped = Image.fromarray(
            core.premul_remap(torso_arr.astype(np.uint8), (xg - dx_arms).astype(np.float32), (yg - dy_arms).astype(np.float32)),
            "RGBA",
        )

        hi_stage = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if s >= 0:
            hi_stage.alpha_composite(bl_rot)
            hi_stage.alpha_composite(torso_warped)
            hi_stage.alpha_composite(fl_rot)
        else:
            hi_stage.alpha_composite(fl_rot)
            hi_stage.alpha_composite(torso_warped)
            hi_stage.alpha_composite(bl_rot)

        pipe_bob_y = int(round(5.0 * math.sin(4.0 * math.pi * ph - 0.7)))
        hi_stage.alpha_composite(pipe_pil, (0, pipe_bob_y))
        w_rot = wheel_pil.rotate(f * 36.0, resample=Image.BICUBIC, expand=False)
        hi_stage.alpha_composite(w_rot, (wx0, wy0 + int(round(pipe_bob_y * 0.65))))

        rsz = hi_stage.resize((rw_c, rh_c), Image.LANCZOS)
        canvas = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
        oy = int(round(oy_base + bounce_px))
        canvas.paste(rsz, (ox_fixed, oy), rsz)

        if (f % 5) in (0, 1):
            ov = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            puff_a = 95 if (f % 5) == 0 else 48
            px_d = W_C * 0.5 - 52.0
            for off_x, rad_p in ((-10, 8), (2, 11), (14, 8)):
                dr.ellipse([px_d + off_x - rad_p, GY - rad_p * 0.55, px_d + off_x + rad_p, GY + rad_p * 0.45], fill=(198, 184, 162, puff_a))
            ov = ov.filter(ImageFilter.GaussianBlur(radius=1.8))
            canvas.alpha_composite(ov)

        out_frames.append(canvas)
    return out_frames


def spin_dark_tire_treads(rgba_arr, phase_01, d_idx, y_band=(130, 336)):
    """Adds subtle 3D traveling rubber tread lug motion to dark tire pixels in y_band."""
    out = rgba_arr.copy().astype(np.float32)
    H, W = out.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    pa = out[..., 3] > 90
    rb = out[..., 0] - out[..., 2]
    lum = 0.299 * out[..., 0] + 0.587 * out[..., 1] + 0.114 * out[..., 2]
    in_y = (yg >= y_band[0]) & (yg <= y_band[1])
    # Dark non-skin rubber pixels on outer wheels (or profile central wheel)
    if d_idx in (2, 6):
        in_x = np.abs(xg - W * 0.5) < 95.0
    else:
        in_x = (xg < W * 0.36) | (xg > W * 0.64)
    is_tire = pa & in_y & in_x & (rb < 14.0) & (lum < 74.0) & (lum > 8.0)
    if not np.any(is_tire):
        return rgba_arr
    roll_sign = -1.0 if d_idx in (1, 2, 3) else +1.0
    yc = 0.5 * (y_band[0] + y_band[1])
    theta = (yg - yc) / 36.0
    wave = np.sin(8.5 * theta - roll_sign * phase_01 * 2.0 * math.pi * 2.0) * 11.5
    out[..., :3] = np.clip(out[..., :3] + (wave * is_tire)[..., None], 0.0, 255.0)
    return out.astype(np.uint8)


# ===========================================================================
# ANIMATION 1: 360° RUNNING WITH STUCK BAR & WHEELS (8 dirs x 10 frames)
# ===========================================================================
def build_anim_1_running(skin_samples, grain_hi):
    """Synthesizes a 10-frame high-energy upright sprint cycle across all 8 angles (360°)
    while the metal bar + chrome cylinder + dual wheels stay wedged/stuck in his behind!"""
    synthesize_run_180_plate()

    h_map = {0: 274.0, 1: 274.0, 2: 268.0, 3: 274.0, 4: 274.0}
    r000_a = load_cleaned_bare_plate(
        "run_000",
        skin_samples,
        grain_hi,
        rel_box=(0.24, 0.36, 0.76, 0.78),
        has_attached_rig=True,
        is_rear=False,
        target_h=h_map[0],
        view_kind="front",
        extra_protect_boxes=[(0.438, 0.566, 0.552, 0.742)],
    )
    r000_b = ImageOps.mirror(r000_a)

    r045_a = load_cleaned_bare_plate("run_045_a", skin_samples, grain_hi, rel_box=(0.20, 0.36, 0.76, 0.78), has_attached_rig=True, is_rear=False, target_h=h_map[1], view_kind="front45")
    r045_b = load_cleaned_bare_plate("run_045_b", skin_samples, grain_hi, rel_box=(0.20, 0.36, 0.76, 0.78), has_attached_rig=True, is_rear=False, target_h=h_map[1], view_kind="front45")

    # True full-scissor articulated 90° profile sprint (and mirrored 270° profile sprint!)
    prof_090_frames = build_profile_scissor_run_90(skin_samples, grain_hi, n_frames=10)
    prof_270_frames = [ImageOps.mirror(im) for im in prof_090_frames]

    r135_a = load_cleaned_bare_plate("run_135_a", skin_samples, grain_hi, rel_box=(0.24, 0.36, 0.74, 0.78), has_attached_rig=True, is_rear=True, target_h=h_map[3], view_kind="rear135")
    # Raw run_135_b faces Back-Right (225°); pre_mirror=True aligns it to Back-Left (135°) with opposite leg stride!
    r135_b = load_cleaned_bare_plate("run_135_b", skin_samples, grain_hi, rel_box=(0.24, 0.36, 0.74, 0.78), has_attached_rig=True, is_rear=True, target_h=h_map[3], pre_mirror=True, view_kind="rear135")

    r180_a = load_cleaned_bare_plate("run_180", skin_samples, grain_hi, rel_box=(0.26, 0.36, 0.74, 0.78), has_attached_rig=True, is_rear=True, target_h=h_map[4], view_kind="rear")
    r180_b = ImageOps.mirror(r180_a)

    dir_strides = [
        (r000_a, r000_b),
        (r045_a, r045_b),
        None,  # d=2 uses prof_090_frames
        (r135_a, r135_b),
        (r180_a, r180_b),
        (ImageOps.mirror(r135_a), ImageOps.mirror(r135_b)),
        None,  # d=6 uses prof_270_frames
        (ImageOps.mirror(r045_a), ImageOps.mirror(r045_b)),
    ]

    n_frames = 10
    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    frames_by_dir = []

    for d in range(8):
        if d == 2:
            frames_by_dir.append(prof_090_frames)
            continue
        if d == 6:
            frames_by_dir.append(prof_270_frames)
            continue

        sa_im, sb_im = dir_strides[d]
        sa_arr = np.array(sa_im)
        sb_arr = np.array(sb_im)
        d_frames = []

        for f in range(n_frames):
            # f=0..4 uses Stride A; f=5..9 uses Stride B (zero alpha ghosting!)
            half_f = f % 5
            u = half_f / 5.0  # 0.0, 0.2, 0.4, 0.6, 0.8 within half-stride
            src = sa_arr if f < 5 else sb_arr
            sign_stride = +1.0 if f < 5 else -1.0

            stride_ext = math.sin(math.pi * (u + 0.10))
            bounce_y = -6.5 * math.sin(math.pi * u) + 2.5 * math.cos(2.0 * math.pi * u)

            # Inertial lag & tilt wobble on the heavy stuck wheel-bar assembly at hip level (y ~ 170..265)
            rig_band = np.exp(-((yg - 212.0) / 36.0) ** 2) * ((xg < cx - 32.0) | (xg > cx + 32.0) | (np.abs(yg - 216.0) < 18.0))
            rig_lag_dy = 4.8 * math.sin(2.0 * math.pi * u - 0.85) * rig_band
            rig_tilt_ang = math.radians(3.6 * sign_stride * math.sin(math.pi * u))
            ct_r, st_r = math.cos(-rig_tilt_ang), math.sin(-rig_tilt_ang)
            dx_rig = (cx + (xg - cx) * ct_r - (yg - 212.0) * st_r - xg) * rig_band
            dy_rig = (212.0 + (xg - cx) * st_r + (yg - 212.0) * ct_r - yg) * rig_band + rig_lag_dy

            leg_w = np.clip((yg - 210.0) / 28.0, 0.0, 1.0)
            l_side = np.where(xg < cx, -1.0, +1.0)
            dx_leg = l_side * (stride_ext - 0.62) * 3.8 * leg_w
            dy_leg = l_side * sign_stride * (stride_ext - 0.62) * 5.2 * leg_w

            head_w = np.clip((132.0 - yg) / 24.0, 0.0, 1.0)
            dx_head = 2.2 * sign_stride * math.sin(math.pi * u) * head_w
            dy_head = -1.8 * math.sin(2.0 * math.pi * u) * head_w

            arm_w = np.clip((195.0 - yg) / 24.0, 0.0, 1.0) * np.clip((yg - 108.0) / 20.0, 0.0, 1.0) * (np.abs(xg - cx) > 28.0)
            dy_arm = np.where(xg < cx, -1.0, 1.0) * sign_stride * math.sin(math.pi * u) * 4.5 * arm_w

            mx = (xg - (dx_rig + dx_leg + dx_head)).astype(np.float32)
            my = (yg - (bounce_y + dy_rig + dy_leg + dy_head + dy_arm)).astype(np.float32)
            warped = core.premul_remap(src, mx, my)
            warped = spin_dark_tire_treads(warped, f / float(n_frames), d, y_band=(155, 290))

            im_out = Image.fromarray(warped, "RGBA")
            if half_f in (1, 2):
                ov = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)
                puff_a = 95 if half_f == 1 else 48
                px_d = cx + (-18 if f < 5 else 18)
                for off_x, rad_p in ((-12, 9), (0, 12), (13, 8)):
                    dr.ellipse([px_d + off_x - rad_p, GY - rad_p * 0.55, px_d + off_x + rad_p, GY + rad_p * 0.45], fill=(198, 184, 162, puff_a))
                ov = ov.filter(ImageFilter.GaussianBlur(radius=1.8))
                im_out.alpha_composite(ov)

            d_frames.append(im_out)
        frames_by_dir.append(d_frames)
    return frames_by_dir


# ===========================================================================
# ANIMATION 2: 360° HANDS IN AIR & KICKING LEGS (8 dirs x 10 frames)
# ===========================================================================
def build_anim_2_hands_up_kick(skin_samples, grain_hi):
    """Wheelman balanced on his stuck bar & wheels, throwing BOTH HANDS HIGH IN THE AIR
    and kicking his bare legs wildly across all 8 angles (360°)!"""
    p000 = load_cleaned_bare_plate("hands_000", skin_samples, grain_hi, rel_box=(0.24, 0.42, 0.76, 0.82), has_attached_rig=True, is_rear=False, target_h=274.0, view_kind="front")
    p045 = load_cleaned_bare_plate("hands_045", skin_samples, grain_hi, rel_box=(0.22, 0.40, 0.78, 0.82), has_attached_rig=True, is_rear=False, target_h=274.0, view_kind="front45")
    # Raw hands_090 faces Right (270°); pre_mirror=True aligns d=2 to Left Profile (90°)!
    p090 = load_cleaned_bare_plate("hands_090", skin_samples, grain_hi, rel_box=(0.20, 0.38, 0.82, 0.82), has_attached_rig=True, is_rear=False, target_h=268.0, pre_mirror=True, view_kind="side")
    p135 = load_cleaned_bare_plate("hands_135", skin_samples, grain_hi, rel_box=(0.22, 0.40, 0.78, 0.82), has_attached_rig=True, is_rear=True, target_h=274.0, view_kind="rear135")
    p180 = load_cleaned_bare_plate("hands_180", skin_samples, grain_hi, rel_box=(0.24, 0.42, 0.76, 0.82), has_attached_rig=True, is_rear=True, target_h=274.0, view_kind="rear")

    bases = [
        p000, p045, p090, p135, p180,
        ImageOps.mirror(p135), ImageOps.mirror(p090), ImageOps.mirror(p045),
    ]

    n_frames = 10
    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    frames_by_dir = []

    for d in range(8):
        base_arr = np.array(bases[d])
        d_frames = []
        for f in range(n_frames):
            ph = f / float(n_frames)
            t = 2.0 * math.pi * ph

            # Keep grounded tires planted at GY=332 (y > 245 locked vertically, tiny rocking x-roll!)
            wheel_lock = np.clip((yg - 242.0) / 22.0, 0.0, 1.0)
            free_upper = 1.0 - wheel_lock

            # Joyful/frantic rocking on the axle
            rock_x = 3.2 * math.sin(t) * (1.0 - np.clip((yg - 305.0) / 24.0, 0.0, 1.0))
            bob_y = 2.6 * math.sin(2.0 * t) * free_upper

            # Protect central head silhouette (around x ~ head_x, y ~ 95..165) while waving raised hands & kicking legs!
            head_x_est = {0: cx, 1: cx + 22, 2: cx + 38, 3: cx + 24, 4: cx, 5: cx - 24, 6: cx - 38, 7: cx - 22}[d]
            head_guard = np.exp(-(((xg - head_x_est) / 30.0) ** 2 + ((yg - 132.0) / 36.0) ** 2))

            # 1) Raised hands & arms high in the air (y < 175) waving side-to-side & pumping up!
            arm_zone = np.clip((178.0 - yg) / 26.0, 0.0, 1.0) * (1.0 - head_guard * 0.88) * free_upper
            l_arm = arm_zone * np.clip((head_x_est - 8.0 - xg) / 24.0, 0.0, 1.0)
            r_arm = arm_zone * np.clip((xg - (head_x_est + 8.0)) / 24.0, 0.0, 1.0)
            if d in (2, 6):
                # Profile: wave both raised arms forward/back & pump vertically!
                ang_a = math.radians(10.5 * math.sin(t))
                piv_ax, piv_ay = head_x_est, 168.0
                ca_a, sa_a = math.cos(-ang_a), math.sin(-ang_a)
                dx_arm = (piv_ax + (xg - piv_ax) * ca_a - (yg - piv_ay) * sa_a - xg) * arm_zone
                dy_arm = (piv_ay + (xg - piv_ax) * sa_a + (yg - piv_ay) * ca_a - yg - 5.5 * math.sin(2.0 * t)) * arm_zone
            else:
                ang_la = math.radians(11.5 * math.sin(t))
                ang_ra = math.radians(-11.5 * math.sin(t + 0.6))
                piv_lx, piv_ly = head_x_est - 26.0, 168.0
                piv_rx, piv_ry = head_x_est + 26.0, 168.0
                cla, sla = math.cos(-ang_la), math.sin(-ang_la)
                cra, sra = math.cos(-ang_ra), math.sin(-ang_ra)
                dx_arm = (
                    (piv_lx + (xg - piv_lx) * cla - (yg - piv_ly) * sla - xg) * l_arm
                    + (piv_rx + (xg - piv_rx) * cra - (yg - piv_ry) * sra - xg) * r_arm
                )
                dy_arm = (
                    (piv_ly + (xg - piv_lx) * sla + (yg - piv_ly) * cla - yg - 5.0 * (0.5 + 0.5 * math.sin(t))) * l_arm
                    + (piv_ry + (xg - piv_rx) * sra + (yg - piv_ry) * cra - yg - 5.0 * (0.5 + 0.5 * math.cos(t))) * r_arm
                )

            # 2) Vigorous Alternating Bare-Leg Kicks!
            if d in (2, 6):
                fwd_s = -1.0 if d == 2 else +1.0
                leg_zone = np.clip((fwd_s * (xg - cx) + 8.0) / 28.0, 0.0, 1.0) * np.clip((242.0 - yg) / 24.0, 0.0, 1.0) * np.clip((yg - 110.0) / 22.0, 0.0, 1.0) * free_upper
                ang_k = math.radians(11.0 * math.sin(t) * fwd_s)
                pkx, pky = cx + fwd_s * 6.0, 224.0
                ck, sk = math.cos(-ang_k), math.sin(-ang_k)
                dx_kick = (pkx + (xg - pkx) * ck - (yg - pky) * sk - xg) * leg_zone
                dy_kick = (pky + (xg - pkx) * sk + (yg - pky) * ck - yg) * leg_zone
            else:
                # Outer V-legs (left bare leg x < cx - 34, right bare leg x > cx + 34, y in 150..245)
                leg_band_y = np.clip((244.0 - yg) / 22.0, 0.0, 1.0) * np.clip((yg - 142.0) / 24.0, 0.0, 1.0) * (1.0 - arm_zone) * free_upper
                l_leg = leg_band_y * np.clip(((cx - 32.0) - xg) / 26.0, 0.0, 1.0)
                r_leg = leg_band_y * np.clip((xg - (cx + 32.0)) / 26.0, 0.0, 1.0)
                ang_lk = math.radians(11.5 * math.sin(t))
                ang_rk = math.radians(11.5 * math.sin(t + math.pi))  # true alternating scissor kicks!
                plx, ply = cx - 28.0, 228.0
                prx, pry = cx + 28.0, 228.0
                clk, slk = math.cos(-ang_lk), math.sin(-ang_lk)
                crk, srk = math.cos(-ang_rk), math.sin(-ang_rk)
                dx_kick = (
                    (plx + (xg - plx) * clk - (yg - ply) * slk - xg) * l_leg
                    + (prx + (xg - prx) * crk - (yg - pry) * srk - xg) * r_leg
                )
                dy_kick = (
                    (ply + (xg - plx) * slk + (yg - ply) * clk - yg) * l_leg
                    + (pry + (xg - prx) * srk + (yg - pry) * crk - yg) * r_leg
                )

            mx = (xg - (rock_x + dx_arm + dx_kick)).astype(np.float32)
            my = (yg - (bob_y + dy_arm + dy_kick)).astype(np.float32)
            warped = core.premul_remap(base_arr, mx, my)
            warped = spin_dark_tire_treads(warped, math.sin(t) * 0.25, d, y_band=(215, 336))
            d_frames.append(Image.fromarray(warped, "RGBA"))

        frames_by_dir.append(d_frames)
    return frames_by_dir


# ===========================================================================
# ANIMATION 3: 360° PICKING UP BAR & WHEELS LIKE WEIGHTS (8 dirs x 12 frames)
# ===========================================================================
def build_anim_3_weightlift(skin_samples, grain_hi):
    """Olympic Deadlift -> Clean Pull -> Overhead Barbell Press -> Controlled Lower
    across all 8 directions (360°) with heavy muscular strain & zero ghosting!"""
    low_000 = load_cleaned_bare_plate("lift_low_000", skin_samples, grain_hi, rel_box=(0.22, 0.32, 0.78, 0.74), has_attached_rig=True, is_rear=False, target_h=242.0, view_kind="front")
    low_045 = load_cleaned_bare_plate("lift_low_045", skin_samples, grain_hi, rel_box=(0.20, 0.32, 0.78, 0.74), has_attached_rig=True, is_rear=False, target_h=244.0, view_kind="front45")
    low_090 = load_cleaned_bare_plate("lift_low_090", skin_samples, grain_hi, rel_box=(0.28, 0.32, 0.90, 0.74), has_attached_rig=True, is_rear=False, target_h=244.0, view_kind="side")
    low_135 = load_cleaned_bare_plate("lift_low_135", skin_samples, grain_hi, rel_box=(0.22, 0.32, 0.78, 0.74), has_attached_rig=True, is_rear=True, target_h=244.0, view_kind="rear135")
    low_180 = load_cleaned_bare_plate("lift_low_180", skin_samples, grain_hi, rel_box=(0.22, 0.32, 0.78, 0.74), has_attached_rig=True, is_rear=True, target_h=242.0, view_kind="rear")

    hi_000 = load_cleaned_bare_plate("lift_high_000", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=False, target_h=308.0, view_kind="front")
    hi_045 = load_cleaned_bare_plate("lift_high_045", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=False, target_h=308.0, view_kind="front45")
    hi_090 = load_cleaned_bare_plate("lift_high_090", skin_samples, grain_hi, rel_box=(0.16, 0.44, 0.84, 0.78), has_attached_rig=False, is_rear=False, target_h=308.0, view_kind="side")
    hi_135 = load_cleaned_bare_plate("lift_high_135", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=True, target_h=308.0, view_kind="rear135")
    hi_180 = load_cleaned_bare_plate("lift_high_180", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=True, target_h=308.0, view_kind="rear")

    pairs = [
        (low_000, hi_000),
        (low_045, hi_045),
        (low_090, hi_090),
        (low_135, hi_135),
        (low_180, hi_180),
        (ImageOps.mirror(low_135), ImageOps.mirror(hi_135)),
        (ImageOps.mirror(low_090), ImageOps.mirror(hi_090)),
        (ImageOps.mirror(low_045), ImageOps.mirror(hi_045)),
    ]

    # 12-frame weightlifting state table:
    # (pose_type, pull_or_press_progress, tremor_amp, strain_redness)
    schedule = [
        ("low",  0.00, 0.0, 0.20),  # f=0: Deep deadlift set gripping the axle
        ("low",  0.42, 0.8, 0.55),  # f=1: Heavy deadlift pull off floor past shins
        ("low",  0.92, 1.2, 0.80),  # f=2: High pull up to waist/hips
        ("high", 0.35, 1.0, 0.85),  # f=3: Clean catch & dip at shoulder/crown level
        ("high", 0.75, 1.4, 0.95),  # f=4: Explosive overhead press drive
        ("high", 1.04, 1.8, 1.00),  # f=5: Lockout overshoot & bar flex!
        ("high", 1.00, 2.0, 0.90),  # f=6: Full overhead press hold (heavy tremor)
        ("high", 1.01, 1.8, 0.85),  # f=7: Full overhead press hold (tremor opposite)
        ("high", 0.98, 1.4, 0.75),  # f=8: Preparing to lower
        ("high", 0.45, 0.8, 0.65),  # f=9: Lowering barbell down toward shoulders
        ("low",  0.62, 0.6, 0.45),  # f=10: Controlled eccentric squat descent
        ("low",  0.14, 0.0, 0.25),  # f=11: Cushioning barbell back to bottom set
    ]

    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    frames_by_dir = []

    for d in range(8):
        low_arr = np.array(pairs[d][0])
        hi_arr = np.array(pairs[d][1])
        d_frames = []

        for f, (mode, prog, trem, strain) in enumerate(schedule):
            foot_anchor = np.clip((GY - yg) / 28.0, 0.0, 1.0)  # 0 at feet (GY=332) -> 1 above ankles!
            trem_x = trem * (1.0 if f % 2 == 0 else -1.0) * np.clip((260.0 - yg) / 120.0, 0.0, 1.0)

            if mode == "low":
                # Extend squat body upward from ankles while lifting the barbell & hands faster upward!
                torso_lift = prog * 26.0 * foot_anchor
                # Barbell + hands sit in y=215..328 in low_arr; lift them up by up to 44px during clean pull!
                bar_zone = np.clip((yg - 185.0) / 30.0, 0.0, 1.0) * ((np.abs(xg - cx) > 48.0) | (np.abs(yg - 268.0) < 28.0))
                dy = -(torso_lift + prog * 22.0 * bar_zone)
                # Slight vertical stretch of torso as back straightens out of squat
                my = yg - dy
                mx = xg - trem_x
                warped = core.premul_remap(low_arr, mx.astype(np.float32), my.astype(np.float32))
            else:
                # Overhead press: prog=1.0 is full tall lockout; prog=0.35 dips knees & lowers overhead bar + arms toward crown!
                dip = 1.0 - prog  # positive when compressed/lowered, slightly negative at lockout overshoot!
                knee_dip_dy = dip * 18.0 * foot_anchor
                # Compress upper arms & overhead barbell (y < 175) downward toward shoulders when dip > 0!
                upper_press_zone = np.clip((185.0 - yg) / 55.0, 0.0, 1.0)
                bar_drop_dy = dip * 38.0 * upper_press_zone
                # Subtle heavy barbell end-flex at lockout (f=5)
                wing_flex = (prog - 1.0) * 55.0 * ((np.abs(xg - cx) / 140.0) ** 2) * (yg < 115.0)
                my = yg - (knee_dip_dy + bar_drop_dy + wing_flex)
                mx = xg - trem_x
                warped = core.premul_remap(hi_arr, mx.astype(np.float32), my.astype(np.float32))

            # Add realistic muscular exertion crimson flush on bare skin during peak lift!
            wf = warped.astype(np.float32)
            is_skin = (wf[..., 3] > 140) & ((wf[..., 0] - wf[..., 2]) > 16.0) & (wf[..., 0] > 80.0)
            upper_skin = is_skin & (yg < 220.0)
            wf[..., 0] = np.clip(wf[..., 0] + upper_skin * 20.0 * strain, 0, 255)
            wf[..., 1] = np.clip(wf[..., 1] - upper_skin * 5.0 * strain, 0, 255)
            wf[..., 2] = np.clip(wf[..., 2] - upper_skin * 6.0 * strain, 0, 255)

            d_frames.append(Image.fromarray(wf.astype(np.uint8), "RGBA"))
        frames_by_dir.append(d_frames)
    return frames_by_dir


# ===========================================================================
# ANIMATION 4: 360° THROWING THE BAR & WHEELS IN 3D (8 dirs x 12 frames)
# ===========================================================================
def build_anim_4_throw(skin_samples, grain_hi):
    """Wheelman coils back with the heavy wheel-barbell and HURLS IT through 3D space
    with real perspective scaling, 3D PBR tumbling wheels/chrome, whoosh arcs & ground sparks!"""
    wu_000 = load_cleaned_bare_plate("throw_windup_000", skin_samples, grain_hi, rel_box=(0.20, 0.40, 0.80, 0.78), has_attached_rig=True, is_rear=False, target_h=282.0, view_kind="front")
    wu_045 = load_cleaned_bare_plate("throw_windup_045", skin_samples, grain_hi, rel_box=(0.18, 0.40, 0.82, 0.78), has_attached_rig=True, is_rear=False, target_h=282.0, view_kind="front45")
    wu_090 = load_cleaned_bare_plate("throw_windup_090", skin_samples, grain_hi, rel_box=(0.16, 0.40, 0.84, 0.78), has_attached_rig=True, is_rear=False, target_h=282.0, view_kind="side")
    wu_135 = load_cleaned_bare_plate("throw_windup_135", skin_samples, grain_hi, rel_box=(0.18, 0.40, 0.82, 0.78), has_attached_rig=True, is_rear=True, target_h=282.0, view_kind="rear135")
    wu_180 = load_cleaned_bare_plate("throw_windup_180", skin_samples, grain_hi, rel_box=(0.20, 0.40, 0.80, 0.78), has_attached_rig=True, is_rear=True, target_h=282.0, view_kind="rear")

    rel_000 = load_cleaned_bare_plate("throw_release_000", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.82, 0.80), has_attached_rig=False, is_rear=False, target_h=268.0, view_kind="front")
    rel_045 = load_cleaned_bare_plate("throw_release_045", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.88, 0.80), has_attached_rig=False, is_rear=False, target_h=268.0, view_kind="front45")
    rel_090 = load_cleaned_bare_plate("throw_release_090", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.90, 0.80), has_attached_rig=False, is_rear=False, target_h=262.0, view_kind="side")
    rel_135 = load_cleaned_bare_plate("throw_release_135", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.88, 0.80), has_attached_rig=False, is_rear=True, target_h=268.0, view_kind="rear135")
    rel_180 = load_cleaned_bare_plate("throw_release_180", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.82, 0.80), has_attached_rig=False, is_rear=True, target_h=268.0, view_kind="rear")

    wu_list = [wu_000, wu_045, wu_090, wu_135, wu_180, ImageOps.mirror(wu_135), ImageOps.mirror(wu_090), ImageOps.mirror(wu_045)]
    rel_list = [rel_000, rel_045, rel_090, rel_135, rel_180, ImageOps.mirror(rel_135), ImageOps.mirror(rel_090), ImageOps.mirror(rel_045)]

    # Load Blender 5.2 3D PBR tumbling wheel-rig sprites (8 dirs x 8 spin steps)
    rig_sprites = {}
    for d in range(8):
        rig_sprites[d] = [Image.open(os.path.join(RIG3D_DIR, f"rig_d{d}_s{s}.png")).convert("RGBA") for s in range(8)]

    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    frames_by_dir = []

    for d in range(8):
        wu_arr = np.array(wu_list[d])
        rel_arr = np.array(rel_list[d])
        az = math.radians(d * 45.0)
        # Screen-space facing unit vector: d=0 -> (0,0,+1 toward cam), d=2 -> (-1 left, 0), d=4 -> (0,0,-1 away), d=6 -> (+1 right, 0)
        dir_sx = -math.sin(az)
        dir_sz = math.cos(az)

        d_frames = []
        for f in range(12):
            foot_w = np.clip((GY - yg) / 30.0, 0.0, 1.0)
            stage = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))

            if f < 4:
                # Frames 0..3: Athletic Coil-Back Wind-Up -> Surge Forward into Launch!
                coil = {0: 0.0, 1: 0.65, 2: 1.0, 3: -0.45}[f]
                lean_dx = -dir_sx * coil * 12.0 * foot_w
                lean_dy = abs(coil) * 5.0 * foot_w
                rot_ang = math.radians(coil * 4.5 * (-dir_sx if abs(dir_sx) > 0.2 else 1.0))
                cr, sr = math.cos(-rot_ang), math.sin(-rot_ang)
                piv_x, piv_y = cx, GY - 8.0
                mx = piv_x + (xg - piv_x - lean_dx) * cr - (yg - piv_y - lean_dy) * sr
                my = piv_y + (xg - piv_x - lean_dx) * sr + (yg - piv_y - lean_dy) * cr
                ch_im = Image.fromarray(core.premul_remap(wu_arr, mx.astype(np.float32), my.astype(np.float32)), "RGBA")
                stage.alpha_composite(ch_im)
            else:
                # Frames 4..11: Explosive Empty-Handed Follow-Through Lunge & Recovery + Flying 3D Wheel-Rig!
                kf = f - 4  # 0..7
                lunge = {0: 1.15, 1: 1.0, 2: 0.80, 3: 0.55, 4: 0.35, 5: 0.20, 6: 0.10, 7: 0.0}[kf]
                dx_rel = dir_sx * lunge * 11.0 * foot_w
                dy_rel = (lunge - 0.5) * 4.5 * foot_w
                mx = (xg - dx_rel).astype(np.float32)
                my = (yg - dy_rel).astype(np.float32)
                ch_im = Image.fromarray(core.premul_remap(rel_arr, mx, my), "RGBA")

                # Compute 3D ballistic trajectory of the thrown Metal Bar & Wheels Rig!
                # Launch starts near chest/hands at kf=0 and arcs forward + bounces at kf=4!
                t_fly = kf / 7.0  # 0.0 -> 1.0
                px = cx + dir_sx * (28.0 + kf * 21.0)
                # Parabolic arc hitting ground GY-26 at kf=4, then bouncing up at kf=5..6!
                if kf <= 4:
                    u_arc = kf / 4.0
                    py = 152.0 - 38.0 * math.sin(math.pi * u_arc) + (GY - 26.0 - 152.0) * (u_arc ** 1.45)
                else:
                    u_b = (kf - 4) / 3.0
                    py = (GY - 26.0) - 44.0 * math.sin(math.pi * u_b)

                # Perspective scale: grows large as it rockets AT camera (d=0,7,1), shrinks as it flies AWAY (d=3,4,5)!
                persp = 0.58 * (1.0 + 0.52 * dir_sz * min(1.0, kf / 5.5))
                persp = max(0.30, min(1.05, persp))
                alpha_rig = 1.0 if kf < 6 else (0.82 if kf == 6 else 0.55)
                spin_idx = (kf * 2) % 8
                rig_im = rig_sprites[d][spin_idx]
                tilt_2d = dir_sx * kf * 16.0

                # Kinetic air-whoosh streaks behind the flying wheel-barbell!
                fx_layer = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
                fdr = ImageDraw.Draw(fx_layer)
                if kf <= 3:
                    for si in range(3):
                        al_w = int((1.0 - kf / 4.0) * (135 - si * 30))
                        off_y = (si - 1) * 14
                        x_tail = cx + dir_sx * 12.0
                        fdr.line([(x_tail, 154 + off_y), (px, py + off_y * 0.5)], fill=(220, 238, 255, max(0, al_w)), width=3 - si // 2)

                # Bright metallic ground-impact sparks when the heavy wheels/bar slam & bounce at kf=4,5!
                if kf in (4, 5):
                    rng = np.random.default_rng(400 + d * 20 + kf)
                    for _ in range(16 if kf == 4 else 8):
                        ang_s = rng.uniform(-math.pi * 0.92, -math.pi * 0.08)
                        len_s = rng.uniform(12.0, 34.0) * (1.0 if kf == 4 else 0.65)
                        sx1 = px + math.cos(ang_s) * len_s
                        sy1 = (GY - 4.0) + math.sin(ang_s) * len_s
                        fdr.line([(px, GY - 4.0), (sx1, sy1)], fill=(255, 215, 90, 235), width=2)
                        fdr.ellipse([sx1 - 2, sy1 - 2, sx1 + 2, sy1 + 2], fill=(255, 252, 220, 245))

                # Depth-order properly: if thrown AWAY from camera (dir_sz < 0, i.e. rear views d=3,4,5), draw projectile BEHIND Wheelman!
                if dir_sz < -0.1:
                    stage.alpha_composite(fx_layer)
                    core.paste_rotated_rgba(stage, rig_im, px, py, angle_deg=tilt_2d, sx=persp, sy=persp, alpha_mul=alpha_rig)
                    stage.alpha_composite(ch_im)
                else:
                    stage.alpha_composite(ch_im)
                    stage.alpha_composite(fx_layer)
                    core.paste_rotated_rgba(stage, rig_im, px, py, angle_deg=tilt_2d, sx=persp, sy=persp, alpha_mul=alpha_rig)

            d_frames.append(stage)
        frames_by_dir.append(d_frames)
    return frames_by_dir


# ===========================================================================
# ANIMATION 5: 360° EXUBERANT BAREFOOT DISCO/JIG DANCE (8 dirs x 12 frames)
# ===========================================================================
def build_anim_5_dance(skin_samples, grain_hi):
    """Wheelman dancing his heart out barefoot across all 8 angles (360°) —
    disco sky-points, alternating side-to-side hip thrusts, high knee kicks,
    and rhythmic twerking/wagging of the metal bar & wheels stuck in his behind!"""
    d000 = load_cleaned_bare_plate("dance_000", skin_samples, grain_hi, rel_box=(0.24, 0.38, 0.76, 0.76), has_attached_rig=True, is_rear=False, target_h=298.0, view_kind="front")
    d045 = load_cleaned_bare_plate("dance_045", skin_samples, grain_hi, rel_box=(0.22, 0.38, 0.76, 0.76), has_attached_rig=True, is_rear=False, target_h=296.0, view_kind="front45")
    d090 = load_cleaned_bare_plate("dance_090", skin_samples, grain_hi, rel_box=(0.20, 0.38, 0.80, 0.76), has_attached_rig=True, is_rear=False, target_h=292.0, view_kind="side")
    # Raw dance_135 faces Back-Right (225°); pre_mirror=True aligns d135 to Back-Left (135°)!
    d135 = load_cleaned_bare_plate("dance_135", skin_samples, grain_hi, rel_box=(0.24, 0.38, 0.76, 0.76), has_attached_rig=True, is_rear=True, target_h=296.0, pre_mirror=True, view_kind="rear135")
    d180 = load_cleaned_bare_plate("dance_180", skin_samples, grain_hi, rel_box=(0.26, 0.38, 0.74, 0.76), has_attached_rig=True, is_rear=True, target_h=298.0, view_kind="rear")

    bases_a = [
        d000, d045, d090, d135, d180,
        ImageOps.mirror(d135), ImageOps.mirror(d090), ImageOps.mirror(d045),
    ]
    # On 0° Front and 180° Back, mirror swaps Right-Hand-Point+Left-Knee-Kick <-> Left-Hand-Point+Right-Knee-Kick!
    bases_b = [
        ImageOps.mirror(d000), d045, d090, d135, ImageOps.mirror(d180),
        ImageOps.mirror(d135), ImageOps.mirror(d090), ImageOps.mirror(d045),
    ]

    n_frames = 12
    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    frames_by_dir = []

    for d in range(8):
        arr_a = np.array(bases_a[d])
        arr_b = np.array(bases_b[d])
        d_frames = []

        for f in range(n_frames):
            ph = f / float(n_frames)
            t = 2.0 * math.pi * ph
            src = arr_a if f < 6 else arr_b

            # Keep lowest planted standing bare foot anchored at GY=332 while whole body grooves!
            foot_free = np.clip((GY - 4.0 - yg) / 28.0, 0.0, 1.0)

            # 2-beat bouncy dance groove + side-to-side funky hip sway!
            beat_bounce = -abs(math.sin(2.0 * t)) * 8.5 * foot_free
            hip_sway_w = np.exp(-((yg - 196.0) / 52.0) ** 2) * foot_free
            hip_dx = 8.5 * math.sin(2.0 * t) * hip_sway_w

            # Stuck metal bar & dual wheels wag/tilt dramatically with every hip thrust!
            rig_zone = np.exp(-((yg - 204.0) / 40.0) ** 2) * ((np.abs(xg - cx) > 34.0) | (np.abs(yg - 210.0) < 18.0)) * foot_free
            wag_ang = math.radians(6.8 * math.sin(2.0 * t - 0.35))
            cw_a, sw_a = math.cos(-wag_ang), math.sin(-wag_ang)
            dx_wag = (cx + (xg - cx) * cw_a - (yg - 204.0) * sw_a - xg) * rig_zone
            dy_wag = (204.0 + (xg - cx) * sw_a + (yg - 204.0) * cw_a - yg) * rig_zone

            # High disco arm sky-pump (y < 140) + happy head bob!
            sky_arm_w = np.clip((138.0 - yg) / 28.0, 0.0, 1.0)
            dy_pump = -7.5 * (0.5 + 0.5 * math.sin(4.0 * t)) * sky_arm_w
            dx_pump = 4.5 * math.cos(2.0 * t) * sky_arm_w

            # Lifted knee / kicking foot jig tap (y in 205..305, off-axis from standing ankle)
            kick_foot_w = np.clip((yg - 205.0) / 25.0, 0.0, 1.0) * np.clip((306.0 - yg) / 18.0, 0.0, 1.0)
            dy_jig = -7.0 * math.sin(4.0 * t) * kick_foot_w

            mx = (xg - (hip_dx + dx_wag + dx_pump)).astype(np.float32)
            my = (yg - (beat_bounce + dy_wag + dy_pump + dy_jig)).astype(np.float32)
            warped = core.premul_remap(src, mx, my)
            warped = spin_dark_tire_treads(warped, math.sin(2.0 * t) * 0.35, d, y_band=(150, 275))
            d_frames.append(Image.fromarray(warped, "RGBA"))

        frames_by_dir.append(d_frames)
    return frames_by_dir


def write_diagnostic_sheets(anims_list, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    # 10x8 master overview sheet (both Phase A f=0 and Phase B f=mid of each animation across all 8 angles)
    tw, th = 165, 165
    overview = Image.new("RGB", (tw * 8, th * len(anims_list) * 2), (24, 27, 34))
    dr = ImageDraw.Draw(overview)
    for idx, a in enumerate(anims_list):
        nf = len(a["frames_by_dir"][0])
        for sub_i, fi in enumerate((0, nf // 2)):
            row = idx * 2 + sub_i
            for d in range(8):
                fr = a["frames_by_dir"][d][fi].resize((tw, th), Image.LANCZOS)
                tile = Image.new("RGBA", (tw, th), (28 + 5 * ((row + d) % 2), 30, 38, 255))
                tile.alpha_composite(fr)
                overview.paste(tile.convert("RGB"), (d * tw, row * th))
                dr.text((d * tw + 5, row * th + 4), f"{a['key']} d{d}:f{fi}", fill=(110, 240, 160))
    ov_path = os.path.join(out_dir, "diagnostic_5anims_8dirs.jpg")
    overview.save(ov_path, quality=92)
    print(f"Wrote diagnostic overview: {ov_path}")

    # Full frame-by-frame motion strips for key angles across all 9 animations
    strips = [
        (0, 0, "run_stuck d0 (0° front nude)"),
        (0, 2, "run_stuck d2 (90° scissor)"),
        (0, 4, "run_stuck d4 (180° back nude)"),
        (1, 0, "hands_up_kick d0 (0°)"),
        (2, 0, "weightlift d0 (0° nude)"),
        (3, 1, "throw_rig d1 (45°)"),
        (4, 0, "dance d0 (0° nude)"),
        (5, 0, "run_overhead d0 (0° front nude)"),
        (5, 1, "run_overhead d1 (45° nude)"),
        (5, 4, "run_overhead d4 (180° back nude)"),
        (6, 0, "spin_bar d0 (360° cyclone)"),
        (7, 0, "explode d0 (Quake gibs & fireball)"),
        (8, 0, "turn_robot d0 (0° front mecha)"),
        (8, 2, "turn_robot d2 (90° profile thruster)"),
    ]
    sw, sh = 140, 145
    max_nf = max(len(anims_list[a_i]["frames_by_dir"][d_i]) for a_i, d_i, _ in strips)
    msheet = Image.new("RGB", (sw * max_nf, sh * len(strips)), (22, 24, 30))
    mdr = ImageDraw.Draw(msheet)
    for r_i, (a_i, d_i, lbl) in enumerate(strips):
        frs = anims_list[a_i]["frames_by_dir"][d_i]
        for fi, im in enumerate(frs):
            fr = im.resize((sw, sw), Image.LANCZOS)
            tile = Image.new("RGBA", (sw, sh), (28 + 4 * ((r_i + fi) % 2), 30, 38, 255))
            tile.alpha_composite(fr, (0, 5))
            msheet.paste(tile.convert("RGB"), (fi * sw, r_i * sh))
            mdr.text((fi * sw + 4, r_i * sh + 2), f"f{fi}", fill=(250, 210, 90))
        mdr.text((6, r_i * sh + sh - 16), lbl, fill=(110, 240, 160))
    m_path = os.path.join(out_dir, "diagnostic_motion_strips.jpg")
    msheet.save(m_path, quality=92)
    print(f"Wrote motion strips: {m_path}")


def main():
    print("[1/10] Loading authentic Wheelman skin tone, groin anatomy & pore grain from wheelman_body.jpg...")
    skin_samples, grain_hi = core.load_authentic_skin_ref()

    print("[2/10] Building Anim 1: 360° Running w/ Stuck Metal Bar & Wheels (8x10 = 80 frames)...")
    f_run = build_anim_1_running(skin_samples, grain_hi)

    print("[3/10] Building Anim 2: 360° Hands in Air & Kicking Legs w/ Stuck Rig (8x10 = 80 frames)...")
    f_hands = build_anim_2_hands_up_kick(skin_samples, grain_hi)

    print("[4/10] Building Anim 3: 360° Picking Up Bar & Wheels Like Weights (8x12 = 96 frames)...")
    f_lift = build_anim_3_weightlift(skin_samples, grain_hi)

    print("[5/10] Building Anim 4: 360° Throwing Bar & Wheels + Anim 5: 360° Dancing (2 x 96 = 192 frames)...")
    f_throw = build_anim_4_throw(skin_samples, grain_hi)
    f_dance = build_anim_5_dance(skin_samples, grain_hi)

    print("[6/10] Building Anim 6: 360° Running Overhead w/ Bar & Wheels (8x10 = 80 frames)...")
    f_run_oh = extra.build_anim_6_run_overhead(load_cleaned_bare_plate, skin_samples, grain_hi)

    print("[7/10] Building Anim 7: 360° Spinning Bar & Wheels Around (8x12 = 96 frames)...")
    f_spin = extra.build_anim_7_spin_around(load_cleaned_bare_plate, skin_samples, grain_hi)

    print("[8/10] Building Anim 8: 360° Exploding — Quake Gibs & Fireball (8x12 = 96 frames)...")
    f_explode = extra.build_anim_8_explode(f_run)

    print("[9/10] Building Anim 9: 360° Turning Into a Cyber-Robot (8x14 = 112 frames)...")
    f_robot = extra.build_anim_9_turn_into_robot(f_run)

    anims_list = [
        dict(
            key="run_stuck",
            short_title="Running (Stuck Rig 360°)",
            subtitle="Nude sprint w/ bar & wheels in behind",
            title="360° Nude Upright Sprint w/ Metal Bar & Wheels Stuck in Behind",
            description="Full 8-direction (0°–315°) bare-nude bipedal sprint cycle: pumping arms, alternating barefoot leg strides with impact dust puffs, while the steel axle, gleaming central chrome cylinder, and spinning tires remain wedged & bouncing in his behind.",
            frames_by_dir=f_run,
        ),
        dict(
            key="hands_up_kick",
            short_title="Hands Up & Kicking",
            subtitle="Arms waving overhead & legs kicking w/ rig in",
            title="360° Raising Both Hands in the Air & Kicking Bare Legs",
            description="Balanced naked on the grounded dual wheels & chrome cylinder connected to his behind, throwing both open hands high overhead waving wildly while scissor-kicking both bare hairy legs across all 8 angles.",
            frames_by_dir=f_hands,
        ),
        dict(
            key="weightlift",
            short_title="Lifting Like Weights",
            subtitle="Nude deadlift, clean & overhead barbell press",
            title="360° Picking Up the Bar & Wheels Like Heavy Olympic Weights",
            description="Detached wheel-axle assembly lifted completely naked like a massive barbell: deep barefoot deadlift squat, explosive clean pull, catch dip, and full overhead lockout press with heavy muscular strain flush & bar flex.",
            frames_by_dir=f_lift,
        ),
        dict(
            key="throw_rig",
            short_title="Throwing Bar & Wheels",
            subtitle="Athletic wind-up & 3D tumbling rig hurl",
            title="360° Winding Up & Hurling the Metal Bar & Wheels Assembly",
            description="Coils back naked holding the heavy two-wheel chrome bar behind his shoulder, then lunges forward hurling the 3D PBR wheel-barbell through true 3D perspective space with motion trails & ground-impact sparks.",
            frames_by_dir=f_throw,
        ),
        dict(
            key="dance",
            short_title="Wheelman Dancing",
            subtitle="Nude disco sky-points, hip-shakes & jig",
            title="360° Exuberant Barefoot Nude Disco & Jig Dance w/ Stuck Wheels",
            description="Manic buck-toothed grin, Saturday-Night-Fever sky-pointing arm pumps, high-stepping bare-foot jig kicks, and rhythmic side-to-side hip thrusts that make the stuck wheel-bar wag & bounce to the beat.",
            frames_by_dir=f_dance,
        ),
        dict(
            key="run_overhead",
            short_title="Running Overhead Bar",
            subtitle="Full-speed nude sprint holding rig overhead",
            title="360° Running Completely Nude While Holding Bar & Wheels Overhead",
            description="Charging full-tilt completely bare naked across all 8 angles while pressing and balancing the heavy two-wheel steel axle & chrome cylinder locked high over his head with heavy barbell inertia & dust puffs.",
            frames_by_dir=f_run_oh,
        ),
        dict(
            key="spin_bar",
            short_title="Spinning Bar Around",
            subtitle="360° berserker hammer-throw cyclone spin",
            title="360° Spinning the Metal Bar & Wheels Around in a Whirlwind",
            description="Gripping the detached steel axle & wheels with outstretched arms and whirling in a full 360° berserker hammer-throw cyclone with real 3D perspective depth-sorting, vortex air-trails, and centrifugal sparks.",
            frames_by_dir=f_spin,
        ),
        dict(
            key="explode",
            short_title="Wheelman Explodes",
            subtitle="Magma swell -> Quake fireball, gibs & wheels",
            title="360° Internal Pressure Swell & Explosive Quake Gib Detonation",
            description="Naked torso & pelvis swell with glowing internal magma fissures before detonating in a blinding Quake fireball shockwave—blasting real photographic limbs, screaming head, crimson gore chunks, and bouncing spark-showering wheels.",
            frames_by_dir=f_explode,
        ),
        dict(
            key="turn_robot",
            short_title="Turns Into a Robot",
            subtitle="Nanotech chrome wave -> Mecha-Wheelman",
            title="360° Nanotech Liquid-Chrome Transformation Into Cyber-Robot Wheelman",
            description="A crackling cyan-white nanotech plasma wave erupts from his butt-mounted rig across his naked flesh, assimilating him into a gleaming beveled Chrome/Titanium Cyber-Robot with blazing red Terminator visor, chest arc-reactor, LED rims, steam vents & plasma butt-thruster.",
            frames_by_dir=f_robot,
        ),
    ]

    print("[10/10] Exporting DarkPlaces progs/wheelman_actions.spr32, PNGs, diagnostic sheets & wheelman_animations.html...")
    os.makedirs(SPRITE_OUT_DIR, exist_ok=True)
    all_toned = []
    for a in anims_list:
        for d in range(8):
            for fi, im in enumerate(a["frames_by_dir"][d]):
                all_toned.append(core.tone_for_darkplaces(im))
                if fi in (0, len(a["frames_by_dir"][d]) // 2):
                    im.save(os.path.join(SPRITE_OUT_DIR, f"{a['key']}_d{d}_f{fi}.png"))

    core.write_spr32(PROGS_PATH, all_toned, ground_y=GY)
    write_diagnostic_sheets(anims_list, SPRITE_OUT_DIR)
    html_gen.build_self_contained_html(HTML_OUT_PATH, anims_list, core.CANVAS_WH, GY)
    print(f"ALL {len(anims_list)} WHEELMAN 360° ANIMATIONS ({len(all_toned)} FRAMES) COMPLETE!")


if __name__ == "__main__":
    main()
