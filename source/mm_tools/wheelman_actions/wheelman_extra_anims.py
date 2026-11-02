r"""4 Additional Photorealistic 360° (8-Direction) Animations for WHEELMAN:
  6. run_overhead : Running completely nude while holding the heavy bar & wheels over his head (8 dirs x 10 frames)
  7. spin_bar     : Spinning the bar & wheels around in a 360° whirlwind cyclone (8 dirs x 12 frames)
  8. explode      : Explosive Quake gib/fireball detonation w/ flying limbs, gore & bouncing wheels (8 dirs x 12 frames)
  9. turn_robot   : Nanotech liquid-chrome transformation from nude human into Cyber-Robot Wheelman (8 dirs x 14 frames)
"""
import math
import os
import cv2
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

import wheelman_actions_core as core

W_C, H_C = core.CANVAS_WH
GY = core.GROUND_Y
HERE = os.path.dirname(os.path.abspath(__file__))
RIG3D_DIR = os.path.join(HERE, "rig3d")


def _median_x_in_band(rgba_arr, y0, y1):
    sub = rgba_arr[max(0, int(y0)):min(rgba_arr.shape[0], int(y1)), :, 3] > 80
    xs = np.nonzero(sub)[1]
    return float(np.median(xs)) if len(xs) > 12 else rgba_arr.shape[1] * 0.5


# ===========================================================================
# ANIMATION 6: 360° NUDE SPRINT HOLDING BAR & WHEELS OVERHEAD (8 dirs x 10f)
# ===========================================================================
def build_anim_6_run_overhead(load_plate_fn, skin_samples, grain_hi):
    """Wheelman sprinting full-speed completely naked while holding the massive metal bar & wheels
    locked out over his head across all 8 angles (360°)!
    Uses unified lift_high_* bodies (zero waist seam!) with true rigid 2-layer hip-pivoted leg scissoring!"""
    hi_000 = load_plate_fn("lift_high_000", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=False, target_h=308.0, view_kind="front")
    hi_045 = load_plate_fn("lift_high_045", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=False, target_h=308.0, view_kind="front45")
    hi_090 = load_plate_fn("lift_high_090", skin_samples, grain_hi, rel_box=(0.15, 0.44, 0.85, 0.78), has_attached_rig=False, is_rear=False, target_h=308.0, view_kind="side")
    hi_135 = load_plate_fn("lift_high_135", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=True, target_h=308.0, view_kind="rear135")
    hi_180 = load_plate_fn("lift_high_180", skin_samples, grain_hi, rel_box=(0.20, 0.44, 0.80, 0.78), has_attached_rig=False, is_rear=True, target_h=308.0, view_kind="rear")

    bodies = [
        hi_000, hi_045, hi_090, hi_135, hi_180,
        ImageOps.mirror(hi_135), ImageOps.mirror(hi_090), ImageOps.mirror(hi_045),
    ]

    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    n_frames = 10
    frames_by_dir = []

    def rigid_xform(layer_u8, piv_x, piv_y, deg, tx=0.0, ty=0.0, sy_scale=1.0):
        rad = math.radians(deg)
        c, s_r = math.cos(-rad), math.sin(-rad)
        qx = xg - tx - piv_x
        qy = (yg - ty - piv_y) / max(0.35, sy_scale)
        mx = (piv_x + qx * c - qy * s_r).astype(np.float32)
        my = (piv_y + qx * s_r + qy * c).astype(np.float32)
        return Image.fromarray(core.premul_remap(layer_u8, mx, my), "RGBA")

    for d in range(8):
        arr = np.array(bodies[d]).astype(np.float32)
        hip_y = 224.0
        mid_x = _median_x_in_band(arr, 196, 232)

        # Sample authentic upper-thigh skin color to round off pivoted hip sockets seamlessly
        thigh_samp = arr[(yg >= 216) & (yg <= 248) & (arr[..., 3] > 220)]
        thigh_col = np.median(thigh_samp[:, :3], axis=0) if len(thigh_samp) > 25 else np.array([202.0, 158.0, 132.0])

        # Upper body + pelvis + groin/glutes + overhead arms & wheel-rig (100% unified single photograph above hip_y!)
        upper_arr = arr.copy()
        upper_keep = np.clip((hip_y + 8.0 - yg) / 14.0, 0.0, 1.0)
        # Keep central bare groin/gluteal fold intact down to y=236 while cutting outer thighs cleanly at hip_y
        groin_keep = np.exp(-((xg - mid_x) / 11.0) ** 2) * np.clip((238.0 - yg) / 10.0, 0.0, 1.0)
        upper_arr[..., 3] *= np.maximum(upper_keep, groin_keep)

        if d in (2, 6):
            # Profile (90° Left / 270° Right): duplicate clean profile bare leg into Far (shaded 0.88x) & Near leg layers!
            leg_m = (yg >= hip_y - 4.0) & (arr[..., 3] > 20.0)
            near_leg = np.zeros_like(arr)
            soft_l = cv2.GaussianBlur(leg_m.astype(np.float32), (5, 5), 1.0)
            near_leg[..., :3] = arr[..., :3]
            near_leg[..., 3] = arr[..., 3] * soft_l
            cap_n = (np.hypot(xg - mid_x, yg - hip_y) < 13.0) & (arr[..., 3] > 200.0) & (near_leg[..., 3] < 220.0)
            near_leg[cap_n, :3] = thigh_col
            near_leg[cap_n, 3] = 255.0

            far_leg = near_leg.copy()
            far_leg[..., :3] *= 0.87  # natural inner/far-leg depth shading!
            lx_piv = rx_piv = mid_x
        else:
            # Frontal / Rear / 3-Quarter: segment actual Left column leg (x < mid_x) and Right column leg (x >= mid_x)!
            l_mask = (yg >= hip_y - 4.0) & (xg < mid_x) & (arr[..., 3] > 20.0)
            r_mask = (yg >= hip_y - 4.0) & (xg >= mid_x) & (arr[..., 3] > 20.0)
            lxs = np.nonzero(l_mask & (yg < hip_y + 24.0))[1]
            rxs = np.nonzero(r_mask & (yg < hip_y + 24.0))[1]
            lx_piv = float(np.median(lxs)) if len(lxs) > 8 else mid_x - 13.0
            rx_piv = float(np.median(rxs)) if len(rxs) > 8 else mid_x + 13.0

            def build_col_leg(m_bool, px_c):
                la = np.zeros_like(arr)
                sm = cv2.GaussianBlur(m_bool.astype(np.float32), (5, 5), 1.0)
                la[..., :3] = arr[..., :3]
                la[..., 3] = arr[..., 3] * sm
                cap = (np.hypot(xg - px_c, yg - hip_y) < 11.5) & (arr[..., 3] > 200.0) & (la[..., 3] < 215.0)
                la[cap, :3] = thigh_col
                la[cap, 3] = 255.0
                return la

            far_leg = build_col_leg(l_mask, lx_piv)
            near_leg = build_col_leg(r_mask, rx_piv)

        az = math.radians(d * 45.0)
        fwd_sx = -math.sin(az)  # -1 facing left, +1 facing right, 0 front/back

        d_frames = []
        for f in range(n_frames):
            ph = f / float(n_frames)
            t = 2.0 * math.pi * ph
            u_half = (f % 5) / 5.0
            bounce_y = -6.5 * math.sin(math.pi * u_half) + 2.2 * math.cos(2.0 * math.pi * u_half)
            s_str = math.sin(t)  # -1..+1 full alternating bipedal stride!

            # Slight athletic forward sprint lean + heavy overhead barbell inertial tilt & flex!
            lean_deg = fwd_sx * 5.5 + 2.0 * math.sin(t)
            bar_w = np.clip((116.0 - yg) / 28.0, 0.0, 1.0)
            tilt_rad = math.radians(3.8 * s_str)
            cb, sb = math.cos(-tilt_rad), math.sin(-tilt_rad)
            dx_bar = (mid_x + (xg - mid_x) * cb - (yg - 60.0) * sb - xg) * bar_w
            dy_bar = (60.0 + (xg - mid_x) * sb + (yg - 60.0) * cb - yg + 4.0 * math.sin(2.0 * t - 0.7)) * bar_w

            up_w_u8 = core.premul_remap(upper_arr.astype(np.uint8), (xg - dx_bar).astype(np.float32), (yg - dy_bar).astype(np.float32))
            torso_im = rigid_xform(up_w_u8, mid_x, hip_y, deg=lean_deg, tx=0.0, ty=bounce_y)

            stage = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            if d in (0, 4):
                # Frontal / Rear sprint: vigorous alternating high-knee sprint drive & push-off!
                l_lift = max(0.0, s_str)
                r_lift = max(0.0, -s_str)
                l_im = rigid_xform(
                    far_leg.astype(np.uint8), lx_piv, hip_y,
                    deg=-6.0 * s_str, tx=-2.5 * l_lift, ty=bounce_y - 18.0 * l_lift, sy_scale=1.0 - 0.34 * l_lift
                )
                r_im = rigid_xform(
                    near_leg.astype(np.uint8), rx_piv, hip_y,
                    deg=-6.0 * s_str, tx=+2.5 * r_lift, ty=bounce_y - 18.0 * r_lift, sy_scale=1.0 - 0.34 * r_lift
                )
                if s_str >= 0:
                    stage.alpha_composite(r_im)
                    stage.alpha_composite(torso_im)
                    stage.alpha_composite(l_im)
                else:
                    stage.alpha_composite(l_im)
                    stage.alpha_composite(torso_im)
                    stage.alpha_composite(r_im)
            elif d in (2, 6):
                # Profile 90°/270° wide athletic sprint scissor!
                swing = 40.0 * s_str
                f_im = rigid_xform(far_leg.astype(np.uint8), lx_piv, hip_y, deg=-swing, tx=0.0, ty=bounce_y - 5.0 * abs(s_str))
                n_im = rigid_xform(near_leg.astype(np.uint8), rx_piv, hip_y, deg=+swing, tx=0.0, ty=bounce_y - 5.0 * abs(s_str))
                stage.alpha_composite(f_im)
                stage.alpha_composite(torso_im)
                stage.alpha_composite(n_im)
            else:
                # 3-Quarter (45°, 135°, 225°, 315°): wide rigid hip-pivoted diagonal sprint scissor!
                swing_d = 36.0 * s_str
                l_im = rigid_xform(
                    far_leg.astype(np.uint8), lx_piv, hip_y,
                    deg=+swing_d, tx=0.0, ty=bounce_y - 8.0 * max(0.0, s_str * (-fwd_sx)), sy_scale=1.0 - 0.12 * abs(s_str)
                )
                r_im = rigid_xform(
                    near_leg.astype(np.uint8), rx_piv, hip_y,
                    deg=-swing_d, tx=0.0, ty=bounce_y - 8.0 * max(0.0, -s_str * (-fwd_sx)), sy_scale=1.0 - 0.12 * abs(s_str)
                )
                if d in (1, 3):
                    # Facing left-ish: right column is nearer when swinging forward
                    if s_str >= 0:
                        stage.alpha_composite(r_im)
                        stage.alpha_composite(torso_im)
                        stage.alpha_composite(l_im)
                    else:
                        stage.alpha_composite(l_im)
                        stage.alpha_composite(torso_im)
                        stage.alpha_composite(r_im)
                else:
                    if s_str >= 0:
                        stage.alpha_composite(l_im)
                        stage.alpha_composite(torso_im)
                        stage.alpha_composite(r_im)
                    else:
                        stage.alpha_composite(r_im)
                        stage.alpha_composite(torso_im)
                        stage.alpha_composite(l_im)

            if (f % 5) in (1, 2):
                ov = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)
                pa_d = 92 if (f % 5) == 1 else 45
                px_d = mid_x + (-16 if f < 5 else 16)
                for ox_p, rp in ((-10, 8), (0, 11), (11, 8)):
                    dr.ellipse([px_d + ox_p - rp, GY - rp * 0.55, px_d + ox_p + rp, GY + rp * 0.45], fill=(198, 184, 162, pa_d))
                ov = ov.filter(ImageFilter.GaussianBlur(radius=1.8))
                stage.alpha_composite(ov)

            d_frames.append(stage)
        frames_by_dir.append(d_frames)
    return frames_by_dir


# ===========================================================================
# ANIMATION 7: 360° SPINNING THE BAR & WHEELS AROUND (8 dirs x 12 frames)
# ===========================================================================
def build_anim_7_spin_around(load_plate_fn, skin_samples, grain_hi):
    """Berserker Olympic Hammer-Throw / Cyclone Spin!
    Nude Wheelman grips the heavy metal bar & wheels and spins a full 360° whirlwind
    with real 3D perspective foreshortening, motion-blur vortex rings & centrifugal sparks!"""
    r000 = load_plate_fn("throw_release_000", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.82, 0.80), has_attached_rig=False, is_rear=False, target_h=268.0, view_kind="front")
    r045 = load_plate_fn("throw_release_045", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.88, 0.80), has_attached_rig=False, is_rear=False, target_h=266.0, view_kind="front45")
    r090 = load_plate_fn("throw_release_090", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.90, 0.80), has_attached_rig=False, is_rear=False, target_h=262.0, view_kind="side")
    r135 = load_plate_fn("throw_release_135", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.88, 0.80), has_attached_rig=False, is_rear=True, target_h=266.0, view_kind="rear135")
    r180 = load_plate_fn("throw_release_180", skin_samples, grain_hi, rel_box=(0.18, 0.34, 0.82, 0.80), has_attached_rig=False, is_rear=True, target_h=268.0, view_kind="rear")

    body_8 = [
        r000, r045, r090, r135, r180,
        ImageOps.mirror(r135), ImageOps.mirror(r090), ImageOps.mirror(r045),
    ]
    rig_sprites = {
        rd: [Image.open(os.path.join(RIG3D_DIR, f"rig_d{rd}_s{s}.png")).convert("RGBA") for s in range(8)]
        for rd in range(8)
    }

    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    n_frames = 12
    frames_by_dir = []

    for d in range(8):
        d_frames = []
        for f in range(n_frames):
            # Full 360° cyclone spin starting at viewing angle d*45°!
            az_deg = (d * 45.0 + f * 30.0) % 360.0
            az = math.radians(az_deg)
            d_eff = int(round(az_deg / 45.0)) % 8

            # Screen-space radial vector of where his outstretched hands swing the wheel-barbell:
            dir_sx = -math.sin(az)
            dir_sz = math.cos(az)  # +1 toward camera, -1 behind Wheelman

            # Counter-balance lean away from the heavy swinging wheels!
            foot_w = np.clip((GY - yg) / 30.0, 0.0, 1.0)
            lean_dx = -dir_sx * 9.0 * foot_w
            bob_dy = -3.5 * abs(math.sin(az * 2.0)) * foot_w
            src_body = np.array(body_8[d_eff])
            ch_im = Image.fromarray(core.premul_remap(src_body, (xg - lean_dx).astype(np.float32), (yg - bob_dy).astype(np.float32)), "RGBA")

            # 3D Orbiting Wheel-Barbell coordinates & perspective scale
            rig_x = cx + dir_sx * 74.0
            rig_y = 166.0 + dir_sz * 22.0
            persp = 0.62 * (1.0 + 0.36 * dir_sz)
            rig_d_idx = (d_eff + 2) % 8  # perpendicular barbell alignment to outstretched arms!
            rig_im = rig_sprites[rig_d_idx][(f * 2) % 8]
            cant_deg = -dir_sx * 18.0 + 8.0 * math.sin(az)

            # 3D Cyclone Vortex Motion Arcs & Centrifugal Sparks!
            vortex_back = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            vortex_front = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            db = ImageDraw.Draw(vortex_back)
            df = ImageDraw.Draw(vortex_front)

            # Draw swept 3D elliptical motion trail behind the whirling barbell
            for step_i in range(1, 14):
                prev_az = az - math.radians(step_i * 7.5)
                next_az = az - math.radians((step_i - 1) * 7.5)
                x0_v = cx - math.sin(prev_az) * 92.0
                y0_v = 166.0 + math.cos(prev_az) * 26.0
                x1_v = cx - math.sin(next_az) * 92.0
                y1_v = 166.0 + math.cos(next_az) * 26.0
                al_v = int(max(0, 145 - step_i * 10))
                target_dr = df if math.cos(prev_az) >= 0 else db
                target_dr.line([(x0_v, y0_v), (x1_v, y1_v)], fill=(205, 232, 255, al_v), width=max(1, 6 - step_i // 3))
                target_dr.line([(x0_v, y0_v - 10), (x1_v, y1_v - 10)], fill=(255, 220, 130, al_v // 2), width=2)

            # Centrifugal sparks flying tangentially off the whirling tires!
            rng = np.random.default_rng(700 + d * 30 + f)
            for _ in range(7):
                sp_a = az - rng.uniform(0.05, 0.55)
                sp_r = rng.uniform(86.0, 122.0)
                sx0 = cx - math.sin(sp_a) * sp_r
                sy0 = 166.0 + math.cos(sp_a) * 28.0 + rng.uniform(-12, 12)
                tx = -math.cos(sp_a) * 14.0
                ty = -math.sin(sp_a) * 5.0
                tdr = df if math.cos(sp_a) >= 0 else db
                tdr.line([(sx0, sy0), (sx0 + tx, sy0 + ty)], fill=(255, 225, 110, 210), width=2)

            # Barefoot pivot dust ring at GY
            dust = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            ddr = ImageDraw.Draw(dust)
            ddr.arc([cx - 48, GY - 12, cx + 48, GY + 8], start=int(az_deg), end=int(az_deg + 210), fill=(195, 180, 158, 95), width=5)
            dust = dust.filter(ImageFilter.GaussianBlur(radius=1.8))

            stage = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            stage.alpha_composite(dust)
            stage.alpha_composite(vortex_back)
            if dir_sz < 0.0:
                # Wheel-rig swings BEHIND nude Wheelman!
                core.paste_rotated_rgba(stage, rig_im, rig_x, rig_y, angle_deg=cant_deg, sx=persp, sy=persp)
                stage.alpha_composite(ch_im)
                stage.alpha_composite(vortex_front)
            else:
                # Wheel-rig swings IN FRONT OF nude Wheelman!
                stage.alpha_composite(ch_im)
                core.paste_rotated_rgba(stage, rig_im, rig_x, rig_y, angle_deg=cant_deg, sx=persp, sy=persp)
                stage.alpha_composite(vortex_front)

            d_frames.append(stage)
        frames_by_dir.append(d_frames)
    return frames_by_dir


# ===========================================================================
# ANIMATION 8: 360° WHEELMAN EXPLODES! (Quake Gib & Fireball Detonation, 12f)
# ===========================================================================
def _extract_body_chunk(arr_rgba, region_mask, cut_side="bottom"):
    """Extracts an organic photographic limb/head/meat gib with ragged torn-muscle & bone stump (zero straight box lines!)."""
    ys, xs = np.nonzero(region_mask & (arr_rgba[..., 3] > 35))
    if len(xs) < 15:
        return None, 180.0, 180.0
    x0, x1 = max(0, int(xs.min()) - 4), min(arr_rgba.shape[1], int(xs.max()) + 5)
    y0, y1 = max(0, int(ys.min()) - 4), min(arr_rgba.shape[0], int(ys.max()) + 5)
    sub = arr_rgba[y0:y1, x0:x1].copy().astype(np.float32)
    m_sub = region_mask[y0:y1, x0:x1].astype(np.float32)
    m_soft = cv2.GaussianBlur(m_sub, (5, 5), 1.1)
    orig_sil = arr_rgba[y0:y1, x0:x1, 3] > 180
    # Identify severed interior cut boundary (where region_mask ends INSIDE the character silhouette!)
    dil_sil = ndimage.binary_erosion(orig_sil, iterations=2)
    cut_zone = dil_sil & (m_soft > 0.08) & (m_soft < 0.94)
    deep_gore = ndimage.binary_dilation(cut_zone, iterations=2) & (m_soft > 0.20)
    sh, sw = sub.shape[:2]
    syg, sxg = np.mgrid[0:sh, 0:sw].astype(np.float32)
    tex = 0.5 + 0.5 * np.sin(sxg * 0.65 + syg * 0.45)
    sub[deep_gore, 0] = np.clip(115.0 + 65.0 * tex[deep_gore], 0, 255)
    sub[deep_gore, 1] = np.clip(10.0 + 16.0 * tex[deep_gore], 0, 255)
    sub[deep_gore, 2] = np.clip(14.0 + 16.0 * tex[deep_gore], 0, 255)
    # Tiny white severed bone glint in center of cut_zone
    cy_s, cx_s = np.nonzero(cut_zone)
    if len(cx_s) > 6:
        bx_m, by_m = float(np.median(cx_s)), float(np.median(cy_s))
        bone = (np.hypot(sxg - bx_m, syg - by_m) < 3.2) & deep_gore
        sub[bone, :3] = [235.0, 224.0, 208.0]
    sub[..., 3] = np.clip(sub[..., 3] * m_soft, 0, 255)
    return Image.fromarray(sub.astype(np.uint8), "RGBA"), 0.5 * (x0 + x1), 0.5 * (y0 + y1)


def build_anim_8_explode(base_stuck_dirs):
    """Over-the-top realistic Quake Gib & Fireball Detonation across all 8 angles (360°)!
    f=0..2: Internal pressure buildup, naked body swelling + glowing magma cracks & butt-pipe steam!
    f=3..11: Blinding fireball shockwave, real photographic head/limbs/meat chunks & both wheels blasting outward,
             bouncing off the floor with sparks & spreading crimson gore puddle!"""
    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    rig_sprites = {
        rd: [Image.open(os.path.join(RIG3D_DIR, f"rig_d{rd}_s{s}.png")).convert("RGBA") for s in range(8)]
        for rd in range(8)
    }

    frames_by_dir = []
    for d in range(8):
        base_im = base_stuck_dirs[d][0]
        base_arr = np.array(base_im)
        bf = base_arr.astype(np.float32)
        az = math.radians(d * 45.0)
        dir_sx = -math.sin(az)

        # Distinguish organic flesh/hair from black rubber tires & steel bar so leg gibs never carry stuck wheels!
        rb = bf[..., 0] - bf[..., 2]
        lum = 0.299 * bf[..., 0] + 0.587 * bf[..., 1] + 0.114 * bf[..., 2]
        is_flesh = (bf[..., 3] > 40) & ((rb > 15.0) | (yg < 118.0)) & (~((lum < 68.0) & (yg > 140.0)))

        # Organic multi-frequency jagged tear offsets (zero straight ruler cuts!)
        jag_y = 7.5 * np.sin(xg * 0.23 + d) + 4.0 * np.cos(xg * 0.51)
        jag_x = 7.5 * np.sin(yg * 0.21 + d) + 4.0 * np.cos(yg * 0.47)

        h_cx_d = _median_x_in_band(base_arr, 62, 112)
        head_m = is_flesh & (yg < 115.0 + jag_y * 0.5) & (np.abs(xg - h_cx_d) < 30.0 + jag_x * 0.3)
        larm_m = is_flesh & (yg >= 82.0) & (yg < 186.0 + jag_y) & (xg < h_cx_d - 22.0 + jag_x * 0.5) & (~head_m)
        rarm_m = is_flesh & (yg >= 82.0) & (yg < 186.0 + jag_y) & (xg > h_cx_d + 22.0 + jag_x * 0.5) & (~head_m)
        # Organic elliptical torn ribcage/chest meat chunk
        rib_ell = (((xg - h_cx_d + jag_x * 0.45) / 26.0) ** 2 + ((yg - 152.0 + jag_y * 0.45) / 30.0) ** 2) <= 1.0
        rib_m = is_flesh & rib_ell & (~head_m)
        lleg_m = is_flesh & (yg >= 218.0 + jag_y * 0.6) & (xg < cx + jag_x * 0.3)
        rleg_m = is_flesh & (yg >= 218.0 + jag_y * 0.6) & (xg >= cx + jag_x * 0.3)

        head_im, hcx, hcy = _extract_body_chunk(base_arr, head_m)
        larm_im, lacx, lacy = _extract_body_chunk(base_arr, larm_m)
        rarm_im, racx, racy = _extract_body_chunk(base_arr, rarm_m)
        rib_im, rbcx, rbcy = _extract_body_chunk(base_arr, rib_m)
        lleg_im, llcx, llcy = _extract_body_chunk(base_arr, lleg_m)
        rleg_im, rlcx, rlcy = _extract_body_chunk(base_arr, rleg_m)

        # Crop standalone 3D wheels & genuine central mirror-chrome exhaust cylinder!
        r_front = rig_sprites[0][0]
        rw0, rh0 = r_front.size
        r_dir = rig_sprites[d][0]
        wheel_shrap_l = r_dir.crop((0, 0, int(rw0 * 0.40), rh0))
        wheel_shrap_r = r_dir.crop((int(rw0 * 0.60), 0, rw0, rh0))
        pipe_shrap = r_front.crop((int(rw0 * 0.42), int(rh0 * 0.24), int(rw0 * 0.58), int(rh0 * 0.78)))

        d_frames = []
        rng_base = 900 + d * 50

        for f in range(12):
            if f <= 2:
                # Pre-explosion pressure buildup & magma cracking!
                swell = {0: 0.02, 1: 0.14, 2: 0.28}[f]
                rx_d = xg - cx
                ry_d = yg - 188.0
                rad = np.hypot(rx_d, ry_d)
                bulge = swell * np.exp(-((rad / 92.0) ** 2))
                shudder_x = (2.5 if f == 1 else -4.0 if f == 2 else 0.0)
                mx = (xg - rx_d * bulge - shudder_x).astype(np.float32)
                my = (yg - ry_d * bulge * 0.75).astype(np.float32)
                warped = core.premul_remap(base_arr, mx, my).astype(np.float32)

                pa = warped[..., 3] > 60
                if f >= 1:
                    # Hot internal crimson/orange pressure glow centered on torso/pelvis!
                    core_heat = np.exp(-(((xg - cx) / 56.0) ** 2 + ((yg - 186.0) / 68.0) ** 2)) * (0.45 if f == 1 else 0.95)
                    warped[..., 0] = np.clip(warped[..., 0] + pa * core_heat * 135.0, 0, 255)
                    warped[..., 1] = np.clip(warped[..., 1] + pa * core_heat * (35.0 if f == 1 else 85.0) - pa * (1.0 - core_heat) * 18.0 * swell, 0, 255)
                    warped[..., 2] = np.clip(warped[..., 2] - pa * 35.0 * swell, 0, 255)

                im_f = Image.fromarray(np.clip(warped, 0, 255).astype(np.uint8), "RGBA")
                if f == 2:
                    # Glowing white-orange magma fissures cracking across his bulging torso & pelvis!
                    crk = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
                    cdr = ImageDraw.Draw(crk)
                    rng_c = np.random.default_rng(rng_base)
                    for _ in range(14):
                        ang_c = rng_c.uniform(0, 2 * math.pi)
                        r1 = rng_c.uniform(22.0, 62.0)
                        x_mid = cx + math.cos(ang_c) * r1 * 0.45 + rng_c.uniform(-6, 6)
                        y_mid = 186.0 + math.sin(ang_c) * r1 * 0.55 + rng_c.uniform(-6, 6)
                        x_end = cx + math.cos(ang_c) * r1
                        y_end = 186.0 + math.sin(ang_c) * r1 * 1.1
                        cdr.line([(cx, 188), (x_mid, y_mid), (x_end, y_end)], fill=(255, 210, 70, 230), width=3)
                        cdr.line([(cx, 188), (x_mid, y_mid), (x_end, y_end)], fill=(255, 255, 220, 245), width=1)
                    # Clip cracks strictly inside character alpha!
                    crk_arr = np.array(crk, dtype=np.float32)
                    crk_arr[..., 3] *= (warped[..., 3] / 255.0)
                    im_f.alpha_composite(Image.fromarray(crk_arr.astype(np.uint8), "RGBA"))
                d_frames.append(im_f)
                continue

            # Frames 3..11: FULL DETONATION, VOLUMETRIC FIREBALL, BLOOD MIST, TUMBLING GIBS & BOUNCING WHEELS!
            kt = f - 3  # 0..8
            stage = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))

            # 1) Expanding Quake Blood Puddle on Dungeon Floor (kt >= 1)
            if kt >= 1:
                pud = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
                pdr = ImageDraw.Draw(pud)
                pw_r = min(128.0, 32.0 + kt * 14.5)
                ph_r = min(15.0, 5.0 + kt * 1.5)
                pdr.ellipse([cx - pw_r, GY - ph_r, cx + pw_r, GY + ph_r * 0.7], fill=(115, 10, 14, 215))
                pdr.ellipse([cx - pw_r * 0.65, GY - ph_r * 0.65, cx + pw_r * 0.65, GY + ph_r * 0.45], fill=(165, 18, 22, 235))
                stage.alpha_composite(pud.filter(ImageFilter.GaussianBlur(radius=1.2)))

            # 2) Volumetric Fireball & Dark Smoke Plume (fades & rises across kt=0..8)
            fb = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            fdr = ImageDraw.Draw(fb)
            rng_p = np.random.default_rng(rng_base + 7)
            if kt <= 6:
                smoke_prog = kt / 6.0
                for pi in range(18):
                    ang_p = rng_p.uniform(0, 2 * math.pi)
                    dist_p = rng_p.uniform(8.0, 96.0) * (0.35 + 0.85 * smoke_prog)
                    px_s = cx + math.cos(ang_p) * dist_p
                    py_s = 186.0 + math.sin(ang_p) * dist_p * 0.82 - kt * 7.5
                    rad_s = rng_p.uniform(18.0, 38.0) * (0.65 + 0.55 * smoke_prog)
                    if kt == 0:
                        col_s = (255, 235, 150, 235)
                    elif kt == 1:
                        col_s = (255, 145, 35, 215) if pi % 2 == 0 else (185, 32, 24, 210)
                    elif kt <= 3:
                        col_s = (72, 58, 56, int(195 * (1.0 - smoke_prog * 0.45))) if pi % 3 != 0 else (215, 78, 22, 165)
                    else:
                        col_s = (48, 44, 46, int(155 * (1.0 - (kt - 3) / 4.2)))
                    fdr.ellipse([px_s - rad_s, py_s - rad_s, px_s + rad_s, py_s + rad_s], fill=col_s)

            # Blinding multi-ray white-hot detonation core on kt=0,1 (no geometric ring outline!)
            if kt == 0:
                for ri in range(14):
                    ra = (ri / 14.0) * 2.0 * math.pi + 0.2 * d
                    rl = 88.0 + 36.0 * ((ri * 7) % 3)
                    fdr.polygon(
                        [
                            (cx + math.cos(ra - 0.14) * 26, 186 + math.sin(ra - 0.14) * 26),
                            (cx + math.cos(ra) * rl, 186 + math.sin(ra) * rl),
                            (cx + math.cos(ra + 0.14) * 26, 186 + math.sin(ra + 0.14) * 26),
                        ],
                        fill=(255, 195, 55, 225),
                    )
                fdr.ellipse([cx - 64, 186 - 64, cx + 64, 186 + 64], fill=(255, 165, 35, 245))
                fdr.ellipse([cx - 38, 186 - 38, cx + 38, 186 + 38], fill=(255, 255, 230, 255))
            elif kt == 1:
                fdr.ellipse([cx - 58, 182 - 54, cx + 58, 182 + 54], fill=(255, 115, 25, 195))

            fb = fb.filter(ImageFilter.GaussianBlur(radius=3.6 if kt >= 2 else 2.8))
            stage.alpha_composite(fb)

            # 3) Ballistic Crimson Gore Chunks & Blood Droplets!
            gore_ov = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            gdr = ImageDraw.Draw(gore_ov)
            rng_g = np.random.default_rng(rng_base + 19)
            for gi in range(28):
                vx = rng_g.uniform(-24.0, 24.0)
                vy = rng_g.uniform(-30.0, -4.0)
                gx0 = cx + rng_g.uniform(-18, 18)
                gy0 = 186.0 + rng_g.uniform(-28, 24)
                t_g = kt + 0.65
                gx = gx0 + vx * t_g
                gy = gy0 + vy * t_g + 0.5 * 8.2 * (t_g ** 2)
                if gy > GY - 3.0:
                    gy = GY - 2.0
                    gx = gx0 + vx * min(t_g, 4.8)
                gr = rng_g.uniform(2.5, 6.2)
                c_g = (178, 16, 20, 235) if gi % 2 == 0 else (122, 10, 14, 225)
                gdr.ellipse([gx - gr, gy - gr * 0.8, gx + gr, gy + gr * 0.8], fill=c_g)
            stage.alpha_composite(gore_ov)

            # 4) Ballistic Real Photographic Body Parts & Detached 3D Wheels + Chrome Pipe!
            def fly_part(part_im, x0, y0, vx, vy, spin_spd, bounce_elast=0.35, radius_pad=14.0, scale_p=1.0):
                if part_im is None:
                    return
                t_p = kt + 0.55
                grav = 8.4
                # Check first ground impact time
                # y0 + vy*t + 0.5*g*t^2 = GY - radius_pad
                disc = vy * vy + 2.0 * grav * max(0.0, (GY - radius_pad) - y0)
                t_hit = (-vy + math.sqrt(disc)) / grav if disc >= 0 else 99.0
                if t_p <= t_hit:
                    px_f = x0 + vx * t_p
                    py_f = y0 + vy * t_p + 0.5 * grav * (t_p ** 2)
                    ang_f = spin_spd * t_p
                else:
                    dt_b = t_p - t_hit
                    x_hit = x0 + vx * t_hit
                    vy_impact = vy + grav * t_hit
                    vy_b = -vy_impact * bounce_elast
                    px_f = x_hit + vx * 0.55 * dt_b
                    py_f = (GY - radius_pad) + vy_b * dt_b + 0.5 * grav * (dt_b ** 2)
                    if py_f > GY - radius_pad:
                        py_f = GY - radius_pad
                    ang_f = spin_spd * (t_hit + dt_b * 0.35)
                px_f = max(18.0, min(W_C - 18.0, px_f))
                core.paste_rotated_rgba(stage, part_im, px_f, py_f, angle_deg=ang_f, sx=scale_p, sy=scale_p)
                return px_f, py_f, ( abs(t_p - t_hit) < 0.65 )

            # Detached Wheels & Chrome Pipe Blast Outward w/ Floor Bounce Sparks!
            wl_res = fly_part(wheel_shrap_l, cx - 36, 212, -22.0 + dir_sx * 5.0, -18.0, -48.0, bounce_elast=0.52, radius_pad=24.0, scale_p=0.68)
            wr_res = fly_part(wheel_shrap_r, cx + 36, 212, +22.0 + dir_sx * 5.0, -16.0, +52.0, bounce_elast=0.52, radius_pad=24.0, scale_p=0.68)
            fly_part(pipe_shrap, cx, 210, -dir_sx * 24.0 + 6.0, -25.0, 68.0, bounce_elast=0.40, radius_pad=10.0, scale_p=0.72)

            # Flying Screaming Head & Bare Limbs!
            fly_part(lleg_im, llcx, llcy, -15.5, -14.0, -38.0, bounce_elast=0.22, radius_pad=14.0)
            fly_part(rleg_im, rlcx, rlcy, +16.5, -13.0, +41.0, bounce_elast=0.22, radius_pad=14.0)
            fly_part(larm_im, lacx, lacy, -19.5, -22.0, -55.0, bounce_elast=0.25, radius_pad=10.0)
            fly_part(rarm_im, racx, racy, +19.0, -21.0, +58.0, bounce_elast=0.25, radius_pad=10.0)
            fly_part(rib_im, rbcx, rbcy, dir_sx * 8.0, -19.0, 32.0, bounce_elast=0.18, radius_pad=12.0)
            fly_part(head_im, hcx, hcy, dir_sx * 11.0 - 4.0, -27.5, -42.0, bounce_elast=0.32, radius_pad=18.0)

            # Metallic sparks when detached wheels slam into the dungeon floor!
            spk = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
            sdr = ImageDraw.Draw(spk)
            for w_info in (wl_res, wr_res):
                if w_info and w_info[2]:
                    wx_h, wy_h, _ = w_info
                    for si in range(8):
                        sa = -math.pi * (0.12 + 0.76 * (si / 7.0))
                        sdr.line([(wx_h, GY - 2), (wx_h + math.cos(sa) * 18, GY - 2 + math.sin(sa) * 18)], fill=(255, 225, 95, 230), width=2)
            stage.alpha_composite(spk)

            d_frames.append(stage)
        frames_by_dir.append(d_frames)
    return frames_by_dir


# ===========================================================================
# ANIMATION 9: 360° WHEELMAN TURNS INTO A ROBOT! (T-1000 / Cyber-Mecha, 14f)
# ===========================================================================
def synthesize_cyber_robot_frame(human_rgba_arr, d_idx, glow_boost=1.0, fire_thruster=False):
    """Transforms real photographic Wheelman RGBA into a hyper-realistic Chrome/Titanium Cyber-Robot:
    - 3D surface-normal metallic studio environment reflection shader on all organic skin/hair
    - Beveled dark-gunmetal robotic armor segmentation seams & servo rings
    - Blazing red Terminator optical visor + glowing chest fusion reactor + LED wheel rims + plasma jet!"""
    arr = human_rgba_arr.astype(np.float32)
    H, W = arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    pa = alpha > 24

    # 1) Estimate smooth 3D surface normals (nx, ny, nz) from photographic luminance!
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    lum_s = cv2.GaussianBlur(lum, (7, 7), 1.6)
    gx = cv2.Sobel(lum_s, cv2.CV_32F, 1, 0, ksize=3) / 95.0
    gy = cv2.Sobel(lum_s, cv2.CV_32F, 0, 1, ksize=3) / 95.0
    # Add silhouette cylinder normal so limbs/torso curve authentically in 3D!
    dist_sil = ndimage.distance_transform_edt(pa)
    sil_gx = cv2.Sobel(np.clip(dist_sil, 0, 28).astype(np.float32), cv2.CV_32F, 1, 0, ksize=5) / 48.0
    sil_gy = cv2.Sobel(np.clip(dist_sil, 0, 28).astype(np.float32), cv2.CV_32F, 0, 1, ksize=5) / 48.0
    nx = -0.65 * gx - 0.55 * sil_gx
    ny = -0.65 * gy - 0.55 * sil_gy
    nz = np.ones_like(nx)
    n_len = np.maximum(1e-4, np.sqrt(nx * nx + ny * ny + nz * nz))
    nx, ny, nz = nx / n_len, ny / n_len, nz / n_len

    # 2) Anisotropic Brushed-Titanium & Mirror-Chrome Studio Reflection Curve!
    # Reflection elevation angle r_y drives classic studio chrome horizon bands!
    refl_v = np.clip(-ny * 1.35 + 0.18 * nx, -1.0, 1.0)
    # Multi-band studio reflection: cool silver-blue sky -> razor white key-light -> dark gunmetal horizon -> warm steel bounce
    sky_w = np.clip((refl_v + 0.15) / 0.65, 0.0, 1.0)
    spec_band = np.exp(-((refl_v - 0.42) / 0.16) ** 2) + 0.55 * np.exp(-((refl_v + 0.36) / 0.14) ** 2)
    horizon_dip = np.exp(-((refl_v - 0.02) / 0.18) ** 2)
    rim_fresnel = np.clip(1.0 - nz, 0.0, 1.0) ** 1.6

    # Preserve rubber tires (keep dark rubber dark, upgrade rims with chrome & red LED!)
    rb = rgb[..., 0] - rgb[..., 2]
    is_rubber = pa & (rb < 14.0) & (lum < 68.0) & ((xg < W * 0.36) | (xg > W * 0.64) | (d_idx in (2, 6))) & (yg > 145.0)

    base_ti = (
        np.array([42.0, 50.0, 64.0])[None, None, :] * (1.0 - sky_w[..., None])
        + np.array([154.0, 172.0, 196.0])[None, None, :] * sky_w[..., None]
    )
    chrome_rgb = (
        base_ti * (1.0 - 0.62 * horizon_dip[..., None])
        + np.array([245.0, 250.0, 255.0])[None, None, :] * (spec_band * 0.54)[..., None]
        + np.array([105.0, 175.0, 250.0])[None, None, :] * (rim_fresnel * 0.44)[..., None]
    )
    # Keep micro-detail modulation from original muscle/rib luminance
    hi_freq = np.clip((lum - lum_s) * 1.35, -32.0, 32.0)[..., None]
    chrome_rgb = np.clip(chrome_rgb + hi_freq, 0.0, 255.0)

    # 3) Etch 3D Beveled Mechanical Armor Seams & Joint Servo Rings!
    ys_a, xs_a = np.nonzero(pa)
    if len(xs_a) > 50:
        by0, by1 = float(ys_a.min()), float(ys_a.max())
        bh = max(40.0, by1 - by0)
        mid_cx = _median_x_in_band(arr, by0 + 0.25 * bh, by0 + 0.55 * bh)

        # Horizontal segmented armor & joint rings (neck, chest, abs1, abs2, waist, knees, ankles)
        seam_fracs = (0.21, 0.31, 0.39, 0.45, 0.52, 0.74, 0.89)
        seam_dark = np.zeros((H, W), dtype=np.float32)
        seam_hi = np.zeros((H, W), dtype=np.float32)
        for sf in seam_fracs:
            sy_line = by0 + sf * bh + 5.0 * np.cos((xg - mid_cx) / 28.0)
            seam_dark = np.maximum(seam_dark, np.exp(-((yg - sy_line) / 1.35) ** 2))
            seam_hi = np.maximum(seam_hi, np.exp(-((yg - (sy_line + 2.0)) / 1.2) ** 2))

        # Sternum / dorsal spine vertical seam!
        vert_seam = np.exp(-((xg - mid_cx) / 1.4) ** 2) * ((yg > by0 + 0.22 * bh) & (yg < by0 + 0.58 * bh))
        seam_dark = np.maximum(seam_dark, vert_seam)

        chrome_rgb = chrome_rgb * (1.0 - 0.68 * seam_dark[..., None]) + 85.0 * seam_hi[..., None]

        # Blend: keep original dark tire rubber on tires, chrome/titanium everywhere else!
        out_rgb = np.where(is_rubber[..., None], rgb * 0.92, np.clip(chrome_rgb, 0.0, 255.0))

        # 4) Glowing Red Terminator Visor + Chest Fusion Core / Dorsal Spine Cores!
        # Find head center in top 22% of silhouette
        head_band = pa & (yg >= by0) & (yg <= by0 + 0.20 * bh)
        hys, hxs = np.nonzero(head_band)
        if len(hxs) > 20:
            h_cx = float(np.median(hxs))
            h_cy = by0 + 0.095 * bh
            if d_idx in (0, 1, 2, 6, 7):
                # Glowing Red Cyber-Visor shifted toward facing direction!
                face_off = {0: 0.0, 1: -7.0, 2: -12.0, 6: 12.0, 7: 7.0}[d_idx]
                vw = {0: 15.0, 1: 12.0, 2: 8.5, 6: 8.5, 7: 12.0}[d_idx]
                vx_c = h_cx + face_off
                visor_core = np.exp(-(((xg - vx_c) / vw) ** 2 + ((yg - h_cy) / 3.2) ** 2)) * pa
                visor_flare = np.exp(-(((xg - vx_c) / (vw * 2.4)) ** 2 + ((yg - h_cy) / 6.5) ** 2)) * glow_boost
                out_rgb[..., 0] = np.clip(out_rgb[..., 0] + visor_flare * 220.0 + visor_core * 255.0, 0, 255)
                out_rgb[..., 1] = np.clip(out_rgb[..., 1] + visor_core * 145.0 + visor_flare * 25.0, 0, 255)
                out_rgb[..., 2] = np.clip(out_rgb[..., 2] + visor_core * 95.0, 0, 255)

        # Chest Arc Reactor (front/3-quarter) or Glowing Red Spine Nodes (rear)
        rc_y = by0 + 0.30 * bh
        if d_idx in (0, 1, 7):
            rc_x = mid_cx + ({0: 0.0, 1: -8.0, 7: 8.0}[d_idx])
            r_dist = np.hypot(xg - rc_x, yg - rc_y)
            c_glow = np.exp(-((r_dist / 13.0) ** 2)) * glow_boost * pa
            c_hot = np.exp(-((r_dist / 5.5) ** 2)) * pa
            out_rgb[..., 0] = np.clip(out_rgb[..., 0] + c_glow * 235.0 + c_hot * 255.0, 0, 255)
            out_rgb[..., 1] = np.clip(out_rgb[..., 1] + c_hot * 180.0 + c_glow * 38.0, 0, 255)
            out_rgb[..., 2] = np.clip(out_rgb[..., 2] + c_hot * 140.0, 0, 255)
        elif d_idx in (3, 4, 5):
            for ni in range(3):
                ny_n = by0 + (0.26 + ni * 0.075) * bh
                nd = np.hypot(xg - mid_cx, yg - ny_n)
                ng = np.exp(-((nd / 6.5) ** 2)) * glow_boost * pa
                out_rgb[..., 0] = np.clip(out_rgb[..., 0] + ng * 240.0, 0, 255)
                out_rgb[..., 1] = np.clip(out_rgb[..., 1] + ng * 65.0, 0, 255)

        # Glowing Red Cyber-Rim LEDs on white wheel dishes!
        white_rim = pa & (lum > 180.0) & (np.abs(rgb[..., 0] - rgb[..., 2]) < 26.0) & (yg > by0 + 0.42 * bh)
        rim_edge = ndimage.binary_dilation(white_rim, iterations=2) & (~ndimage.binary_erosion(white_rim, iterations=2)) & pa
        rim_glow = cv2.GaussianBlur(rim_edge.astype(np.float32), (7, 7), 1.8) * glow_boost
        out_rgb[..., 0] = np.clip(out_rgb[..., 0] + rim_glow * 255.0, 0, 255)
        out_rgb[..., 1] = np.clip(out_rgb[..., 1] + rim_glow * 45.0, 0, 255)
    else:
        out_rgb = chrome_rgb

    robo_im = Image.fromarray(np.dstack([np.clip(out_rgb, 0, 255).astype(np.uint8), alpha.astype(np.uint8)]), "RGBA")

    # Optional Blue-White Plasma Thruster Jet firing from his butt-pipe!
    if fire_thruster and d_idx in (1, 2, 3, 4, 5, 6, 7):
        jet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        jdr = ImageDraw.Draw(jet)
        if d_idx == 2:
            jdr.polygon([(275, 200), (348, 192), (348, 212)], fill=(70, 200, 255, 195))
            jdr.polygon([(275, 201), (322, 197), (322, 207)], fill=(230, 252, 255, 240))
        elif d_idx == 6:
            jdr.polygon([(85, 200), (12, 192), (12, 212)], fill=(70, 200, 255, 195))
            jdr.polygon([(85, 201), (38, 197), (38, 207)], fill=(230, 252, 255, 240))
        else:
            jx = W * 0.5 + ({1: 22, 3: 18, 4: 0, 5: -18, 7: -22}[d_idx])
            jdr.ellipse([jx - 16, 206, jx + 16, 238], fill=(70, 205, 255, 195))
            jdr.ellipse([jx - 8, 212, jx + 8, 228], fill=(235, 253, 255, 245))
        jet = jet.filter(ImageFilter.GaussianBlur(radius=2.2))
        stage = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        stage.alpha_composite(jet)
        stage.alpha_composite(robo_im)
        return stage

    return robo_im


def build_anim_9_turn_into_robot(base_stuck_dirs):
    """14-Frame Photorealistic Nanotech Cyber-Robot Transformation across all 8 angles (360°):
    f=0: Fully naked human Wheelman w/ stuck bar & wheels
    f=1..7: Sizzling cyan-white nanotech plasma wave expands from his butt-mounted chrome rig across his naked body,
            converting flesh into gleaming beveled titanium/chrome Mecha-Wheelman w/ blazing red visor & chest reactor!
    f=8..13: Full Robot Online — hydraulic steam vents, quantized servo power-stomp & plasma butt-thruster burn!"""
    yg, xg = np.mgrid[0:H_C, 0:W_C].astype(np.float32)
    cx = W_C * 0.5
    n_frames = 14
    frames_by_dir = []

    for d in range(8):
        human_im = base_stuck_dirs[d][0]
        human_arr = np.array(human_im)
        robo_base_im = synthesize_cyber_robot_frame(human_arr, d, glow_boost=1.15, fire_thruster=False)
        robo_thruster_im = synthesize_cyber_robot_frame(human_arr, d, glow_boost=1.45, fire_thruster=True)
        robo_arr = np.array(robo_base_im).astype(np.float32)
        hum_f = human_arr.astype(np.float32)

        d_frames = []
        for f in range(n_frames):
            if f == 0:
                d_frames.append(human_im.copy())
                continue

            if f <= 7:
                # Advancing Radial + Hexagonal Nanotech Liquid-Chrome Wave from Pelvis Rig (cx, 208)!
                prog = f / 7.0  # 0.14 -> 1.0
                r_origin = np.hypot((xg - cx) * 1.05, (yg - 208.0) * 0.88)
                # Subtle hexagonal / cellular perturbation along wavefront
                hex_rip = 7.5 * np.sin(xg * 0.22) * np.cos(yg * 0.22)
                r_front = prog * 215.0
                # 1.0 inside transformed robot zone, 0.0 in still-naked human zone
                w_robo = np.clip((r_front - (r_origin + hex_rip) + 8.0) / 14.0, 0.0, 1.0)
                # Sizzling cyan-white plasma assimilation frontier band!
                band = np.exp(-(((r_origin + hex_rip) - r_front) / 7.5) ** 2) * (hum_f[..., 3] > 35)

                mix_rgb = hum_f[..., :3] * (1.0 - w_robo[..., None]) + robo_arr[..., :3] * w_robo[..., None]
                mix_rgb[..., 0] = np.clip(mix_rgb[..., 0] + band * 135.0, 0, 255)
                mix_rgb[..., 1] = np.clip(mix_rgb[..., 1] + band * 235.0, 0, 255)
                mix_rgb[..., 2] = np.clip(mix_rgb[..., 2] + band * 255.0, 0, 255)

                # Slight electric shudder during transformation
                shud_x = (2.0 if f % 2 == 0 else -2.0) * np.clip((GY - yg) / 35.0, 0.0, 1.0)
                mixed = np.dstack([mix_rgb.astype(np.uint8), human_arr[..., 3]])
                warped = core.premul_remap(mixed, (xg - shud_x).astype(np.float32), yg)
                im_out = Image.fromarray(warped, "RGBA")

                # Crackling electric lightning arcs jumping across the wavefront!
                arc_ov = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
                adr = ImageDraw.Draw(arc_ov)
                rng_a = np.random.default_rng(1200 + d * 40 + f)
                bys, bxs = np.nonzero(band > 0.45)
                if len(bxs) > 12:
                    for _ in range(6):
                        idx_p = int(rng_a.integers(0, len(bxs)))
                        ax0, ay0 = float(bxs[idx_p]), float(bys[idx_p])
                        pts = [(ax0, ay0)]
                        for _s in range(4):
                            ax0 += rng_a.uniform(-14, 14)
                            ay0 += rng_a.uniform(-14, 14)
                            pts.append((ax0, ay0))
                        adr.line(pts, fill=(110, 230, 255, 225), width=2)
                        adr.line(pts, fill=(255, 255, 255, 240), width=1)
                im_out.alpha_composite(arc_ov)
                d_frames.append(im_out)
            else:
                # Frames 8..13: 100% MECHA-WHEELMAN ONLINE — Servo Power-Crouch, Steam Vents & Plasma Burn!
                rf = f - 8  # 0..5
                use_jet = rf in (1, 2, 3, 4)
                src_r = np.array(robo_thruster_im if use_jet else robo_base_im)

                # Robotic quantized hydraulic crouch-and-rise + mechanical arm/shoulder flex!
                foot_w = np.clip((GY - yg) / 28.0, 0.0, 1.0)
                crouch_dy = {0: -3.0, 1: 7.5, 2: 9.0, 3: -4.5, 4: -2.0, 5: 0.0}[rf] * foot_w
                # Mechanical upper-arm outward servo pump
                arm_z = np.clip((195.0 - yg) / 25.0, 0.0, 1.0) * np.clip((yg - 90.0) / 20.0, 0.0, 1.0) * (np.abs(xg - cx) > 22.0)
                flex_amp = {0: 0.5, 1: 1.0, 2: 1.2, 3: 0.9, 4: 0.5, 5: 0.2}[rf]
                dx_servo = np.sign(xg - cx) * flex_amp * 5.5 * arm_z
                dy_servo = -flex_amp * 6.5 * arm_z

                warped_r = core.premul_remap(src_r, (xg - dx_servo).astype(np.float32), (yg - (crouch_dy + dy_servo)).astype(np.float32))
                warped_r = core.spin_dark_tire_treads(warped_r, rf / 6.0, d) if hasattr(core, "spin_dark_tire_treads") else warped_r
                im_out = Image.fromarray(warped_r, "RGBA")

                # Pressurized white hydraulic steam vents from shoulders & knees on lock-in frames rf=0,1!
                if rf in (0, 1):
                    stm = Image.new("RGBA", (W_C, H_C), (0, 0, 0, 0))
                    sdr = ImageDraw.Draw(stm)
                    sa_v = 165 if rf == 0 else 95
                    span_v = 14 if rf == 0 else 26
                    for sx_v, sy_v, dx_v in ((cx - 38, 122, -span_v), (cx + 38, 122, span_v), (cx - 28, 258, -span_v), (cx + 28, 258, span_v)):
                        sdr.polygon([(sx_v, sy_v), (sx_v + dx_v, sy_v - 9), (sx_v + dx_v, sy_v + 7)], fill=(230, 242, 255, sa_v))
                    stm = stm.filter(ImageFilter.GaussianBlur(radius=2.2))
                    im_out.alpha_composite(stm)

                d_frames.append(im_out)

        frames_by_dir.append(d_frames)
    return frames_by_dir
