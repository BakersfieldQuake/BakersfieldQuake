"""High-FPS Screaming, Driving, and 84-Frame Multi-Stage Explosion + Flying Wheels/Bar + Quake Gibs
animation engine for the BakersfieldQuake Wheelman monster sprite."""
import math
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _premul_remap(rgba, map_x, map_y):
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, a * 255.0], axis=-1)
    warped = cv2.remap(pm, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    wa = warped[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, warped[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), np.clip(warped[..., 3], 0, 255).astype(np.uint8)])


def _paste_rotated_rgba(stage_rgba, sprite_pil, cx, cy, angle_deg=0.0, sx=1.0, sy=1.0, alpha_mul=1.0, max_bottom_y=None):
    """Subpixel-clean rotated + scaled RGBA blit onto stage_rgba with optional floor-contact clamp."""
    w0, h0 = sprite_pil.size
    nw = max(2, int(round(w0 * sx)))
    nh = max(2, int(round(h0 * sy)))
    im = sprite_pil.resize((nw, nh), Image.BICUBIC) if (nw != w0 or nh != h0) else sprite_pil
    if abs(angle_deg) > 0.05:
        im = im.rotate(-angle_deg, resample=Image.BICUBIC, expand=True)
    if alpha_mul < 0.999:
        arr = np.array(im, dtype=np.float32)
        arr[..., 3] *= max(0.0, alpha_mul)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    px = int(round(cx - im.width * 0.5))
    py = int(round(cy - im.height * 0.5))
    if max_bottom_y is not None:
        bbox = im.getbbox()
        if bbox is not None:
            opaque_bot = py + bbox[3]
            if opaque_bot > max_bottom_y:
                py -= int(round(opaque_bot - max_bottom_y))
    stage_rgba.alpha_composite(im, (px, py))


# Exact measured facial landmarks on normalized 320x304 canvas (verified on norm_face_grid.jpg & test_scream_strip.jpg)
FACE_SPECS_320 = {
    0: dict(mx=150.0, my=104.5, jx=150.0, jy=112.5, jrx=11.5, jry=10.5, mrx=6.2, eyes=[(143.0, 84.0), (157.0, 84.0)], nx=150.0, ny=120.0, prof=0.0),
    1: dict(mx=226.5, my=95.5,  jx=227.5, jy=103.5, jrx=10.5, jry=9.5,  mrx=5.0, eyes=[(220.0, 72.0), (234.0, 72.0)], nx=232.0, ny=110.0, prof=-0.55),
    2: dict(mx=251.5, my=114.5, jx=254.5, jy=123.5, jrx=10.5, jry=9.5,  mrx=4.2, eyes=[(259.0, 93.0)],               nx=272.0, ny=126.0, prof=-1.0),
    3: dict(nx=244.0, ny=108.0, hx=246.0, hy=72.0, prof=-0.75),
    4: dict(nx=160.0, ny=138.0, hx=160.0, hy=104.0, prof=0.0),
    5: dict(nx=76.0,  ny=108.0, hx=74.0,  hy=72.0,  prof=+0.75),
    6: dict(mx=68.5,  my=114.5, jx=65.5,  jy=123.5, jrx=10.5, jry=9.5,  mrx=4.2, eyes=[(61.0, 93.0)],                nx=48.0,  ny=126.0, prof=+1.0),
    7: dict(mx=93.5,  my=95.5,  jx=92.5,  jy=103.5, jrx=10.5, jry=9.5,  mrx=5.0, eyes=[(86.0, 72.0), (100.0, 72.0)],  nx=88.0,  ny=110.0, prof=+0.55),
}


def apply_scream_face_and_body(base_rgba, d_idx, phase_01, wheel_specs, ground_y=288, intensity=1.0, sound_waves=True):
    """Deforms a 320x304 Wheelman view into a frantic blood-curdling SCREAM:
      - Biomechanical lower-jaw drop + photorealistic dark-crimson oral cavity, tongue & bright buck teeth
      - Bugged-out wide eyes + arched eyebrows + red strain flush across cheeks/forehead/neck
      - Rigid-top high-frequency vibrato head tremor + ribcage heave + frantic splayed bare V-leg kicking
      - Clean outward-radiating acoustic scream wave arcs (strictly outside face silhouette!)
    """
    rgba = np.array(base_rgba).copy()
    H, W = rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    t = 2.0 * math.pi * phase_01
    cx = W * 0.5
    spec = FACE_SPECS_320[d_idx]
    nx, ny = spec["nx"], spec["ny"]
    y_axle = sum(ws["cy"] for ws in wheel_specs) / len(wheel_specs)

    # Sustain wide-open scream with rapid 3-harmonic vocal tremor
    scream_env = (0.70 + 0.30 * (0.5 - 0.5 * math.cos(t)) + 0.09 * math.sin(3.0 * t)) * intensity
    scream_env = max(0.0, min(1.25, scream_env))

    # Lock wheels & axle on ground
    wheel_lock = np.zeros((H, W), dtype=np.float32)
    for ws in wheel_specs:
        wcx, wcy = ws["cx"], ws["cy"]
        wrx, wry = ws["rx"] + 4.0, ws["ry"] + 4.0
        wang = math.radians(ws["ang"])
        ca, sa = math.cos(wang), math.sin(wang)
        du = ((xg - wcx) * ca + (yg - wcy) * sa) / max(wrx, 1.0)
        dv = (-(xg - wcx) * sa + (yg - wcy) * ca) / max(wry, 1.0)
        wheel_lock = np.maximum(wheel_lock, np.clip((1.16 - np.sqrt(du * du + dv * dv)) / 0.20, 0.0, 1.0))
    free_w = 1.0 - np.clip(np.maximum(wheel_lock, np.exp(-((yg - y_axle) / 8.0) ** 2) * 0.88), 0.0, 1.0)

    dx_tot = np.zeros((H, W), dtype=np.float32)
    dy_tot = np.zeros((H, W), dtype=np.float32)

    # 1) Jaw drop + eye bulge + brow lift
    jaw_drop = 6.6 * scream_env
    if "mx" in spec:
        mx, my = spec["mx"], spec["my"]
        jx, jy, jrx, jry = spec["jx"], spec["jy"], spec["jrx"], spec["jry"]
        jw = np.exp(-(((xg - jx) / (jrx * 1.25)) ** 2 + ((yg - (jy + jaw_drop * 0.45)) / (jry * 1.35)) ** 2))
        jw *= 1.0 / (1.0 + np.exp(-(yg - (my + 1.2)) / 1.4))
        dy_tot -= jaw_drop * jw * free_w

        for ex, ey in spec["eyes"]:
            rex = xg - ex
            rey = yg - ey
            r2 = (rex / 8.5) ** 2 + (rey / 7.5) ** 2
            ew = np.exp(-r2) * 0.22 * scream_env
            dx_tot -= rex * ew
            dy_tot -= rey * ew
            bw = np.exp(-(((xg - ex) / 8.0) ** 2 + ((yg - (ey - 6.5)) / 3.8) ** 2))
            dy_tot += 2.2 * scream_env * bw

    # 2) Rigid flat-topped head tremor (zero hair/ear shear!) + ribcage heave
    horiz_head = np.clip((64.0 - np.abs(xg - nx)) / 20.0, 0.0, 1.0)
    head_w = np.clip((ny + 4.0 - yg) / 20.0, 0.0, 1.0) * horiz_head * free_w
    vib_x = 1.35 * math.sin(4.0 * t) * min(1.0, intensity)
    vib_y = -1.8 * scream_env + 0.9 * math.cos(3.0 * t) * min(1.0, intensity)
    dx_tot += (-vib_x) * head_w
    dy_tot += (-vib_y) * head_w

    chest_cy = ny + 26.0
    cw_m = np.exp(-(((xg - nx) / 34.0) ** 2 + ((yg - chest_cy) / 24.0) ** 2)) * free_w
    dx_tot -= (xg - nx) * 0.055 * scream_env * cw_m
    dy_tot -= (yg - chest_cy) * 0.045 * scream_env * cw_m

    # 3) Frantic panicked V-leg thrashing
    if d_idx in (2, 6):
        fwd_s = -1.0 if d_idx == 2 else 1.0
        s_leg_w = np.clip((fwd_s * (xg - cx) + 10.0) / 30.0, 0.0, 1.0) * np.clip(((y_axle - 16.0) - yg) / 26.0, 0.0, 1.0) * free_w
        ang_s = math.radians((5.5 * math.sin(2.0 * t) + 3.5 * scream_env) * fwd_s)
        px_s, py_s = cx + fwd_s * 6.0, y_axle - 22.0
        ca_s, sa_s = math.cos(-ang_s), math.sin(-ang_s)
        dx_tot += (px_s + (xg - px_s) * ca_s - (yg - py_s) * sa_s - xg) * s_leg_w
        dy_tot += (py_s + (xg - px_s) * sa_s + (yg - py_s) * ca_s - yg) * s_leg_w
    else:
        head_guard = 1.0 - np.clip((76.0 - np.abs(xg - nx)) / 14.0, 0.0, 1.0) * np.clip((ny + 22.0 - yg) / 16.0, 0.0, 1.0)
        l_leg_w = np.clip(((cx - 22.0) - xg) / 28.0, 0.0, 1.0) * np.clip(((y_axle - 8.0) - yg) / 26.0, 0.0, 1.0) * head_guard * free_w
        r_leg_w = np.clip((xg - (cx + 22.0)) / 28.0, 0.0, 1.0) * np.clip(((y_axle - 8.0) - yg) / 26.0, 0.0, 1.0) * head_guard * free_w
        ang_L = math.radians((-4.2 * scream_env + 5.8 * math.sin(2.0 * t)) * min(1.1, intensity))
        ang_R = math.radians((+4.2 * scream_env + 5.8 * math.sin(2.0 * t + 2.4)) * min(1.1, intensity))
        pxL, pyL = cx - 24.0, y_axle - 18.0
        pxR, pyR = cx + 24.0, y_axle - 18.0
        cL, sL = math.cos(-ang_L), math.sin(-ang_L)
        cR, sR = math.cos(-ang_R), math.sin(-ang_R)
        dx_tot += (pxL + (xg - pxL) * cL - (yg - pyL) * sL - xg) * l_leg_w + (pxR + (xg - pxR) * cR - (yg - pyR) * sR - xg) * r_leg_w
        dy_tot += (pyL + (xg - pxL) * sL + (yg - pyL) * cL - yg) * l_leg_w + (pyR + (xg - pxR) * sR + (yg - pyR) * cR - yg) * r_leg_w

    rgba = _premul_remap(rgba, (xg + dx_tot).astype(np.float32), (yg + dy_tot).astype(np.float32))

    # 4) Crimson facial strain flush + Photorealistic Open Screaming Mouth Cavity & Buck Teeth
    rf = rgba.astype(np.float32)
    a_m = rf[..., 3] > 140
    face_zone = np.exp(-(((xg - nx) / 24.0) ** 2 + ((yg - (ny - 24.0)) / 28.0) ** 2))
    is_skin = a_m & ((rf[..., 0] - rf[..., 2]) > 14.0) & (rf[..., 0] > 80.0)
    flush = (face_zone * is_skin * 0.48 * scream_env)[..., None]
    rf[..., 0] = np.clip(rf[..., 0] + flush[..., 0] * 38.0, 0.0, 255.0)
    rf[..., 1] = np.clip(rf[..., 1] - flush[..., 0] * 10.0, 0.0, 255.0)
    rf[..., 2] = np.clip(rf[..., 2] - flush[..., 0] * 12.0, 0.0, 255.0)

    if "mx" in spec and jaw_drop > 1.2:
        mx_s = spec["mx"] + vib_x
        my_s = spec["my"] + vib_y
        mrx = spec["mrx"]
        prof = spec["prof"]
        cav_cy = my_s + 1.5 + jaw_drop * 0.44
        cav_ry = max(1.8, 1.4 + jaw_drop * 0.46)
        cav_cx = mx_s + prof * 1.1
        du_m = (xg - cav_cx) / mrx
        dv_m = (yg - cav_cy) / cav_ry
        r_m = np.sqrt(du_m * du_m + dv_m * dv_m)
        mouth_w = np.clip((1.0 - r_m) / 0.24, 0.0, 1.0) * a_m

        cav_rgb = np.zeros((H, W, 3), dtype=np.float32)
        cav_rgb[..., 0] = 44.0
        cav_rgb[..., 1] = 8.0
        cav_rgb[..., 2] = 12.0

        tongue_w = np.clip((dv_m - 0.18) / 0.45, 0.0, 1.0) * np.exp(-(du_m * 1.25) ** 2)
        cav_rgb[..., 0] += tongue_w * 128.0
        cav_rgb[..., 1] += tongue_w * 44.0
        cav_rgb[..., 2] += tongue_w * 52.0

        teeth_w = np.clip((-0.44 - dv_m) / 0.28, 0.0, 1.0) * (np.abs(du_m) < 0.58)
        gap = 1.0 - 0.55 * np.exp(-(du_m / 0.09) ** 2)
        tw_f = teeth_w * gap
        cav_rgb[..., 0] = cav_rgb[..., 0] * (1.0 - tw_f) + 242.0 * tw_f
        cav_rgb[..., 1] = cav_rgb[..., 1] * (1.0 - tw_f) + 236.0 * tw_f
        cav_rgb[..., 2] = cav_rgb[..., 2] * (1.0 - tw_f) + 216.0 * tw_f

        lteeth_w = np.clip((dv_m - 0.68) / 0.22, 0.0, 1.0) * (np.abs(du_m) < 0.52) * 0.70
        cav_rgb[..., 0] = cav_rgb[..., 0] * (1.0 - lteeth_w) + 220.0 * lteeth_w
        cav_rgb[..., 1] = cav_rgb[..., 1] * (1.0 - lteeth_w) + 212.0 * lteeth_w
        cav_rgb[..., 2] = cav_rgb[..., 2] * (1.0 - lteeth_w) + 195.0 * lteeth_w

        rf[..., :3] = rf[..., :3] * (1.0 - mouth_w[..., None]) + cav_rgb * mouth_w[..., None]

    out_im = Image.fromarray(np.clip(rf, 0, 255).astype(np.uint8), "RGBA")

    # 5) Clean acoustic scream wave arcs starting strictly OUTSIDE the head silhouette!
    if sound_waves and intensity > 0.35:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(overlay)
        prof = spec.get("prof", 0.0)
        ox_w = spec.get("mx", spec.get("hx", nx)) + vib_x + prof * 6.0
        oy_w = spec.get("my", spec.get("hy", ny - 26.0)) + vib_y
        min_r = 29.0 if abs(prof) < 0.25 else 20.0
        for ring_i in range(3):
            prog = (phase_01 * 2.0 + ring_i / 3.0) % 1.0
            rad_r = min_r + prog * 42.0
            a_ring = int(round((1.0 - prog) * 165.0 * min(1.0, intensity)))
            if a_ring < 12:
                continue
            col_r = (255, int(235 - 70 * prog), int(140 - 90 * prog), a_ring)
            bbox_r = [ox_w - rad_r, oy_w - rad_r * 0.80, ox_w + rad_r, oy_w + rad_r * 0.80]
            if prof < -0.25:
                dr.arc(bbox_r, start=138, end=222, fill=col_r, width=2)
            elif prof > 0.25:
                dr.arc(bbox_r, start=-42, end=42, fill=col_r, width=2)
            else:
                dr.arc(bbox_r, start=145, end=215, fill=col_r, width=2)
                dr.arc(bbox_r, start=-35, end=35, fill=col_r, width=2)
        out_im.alpha_composite(overlay)

    return out_im


# ---------------------------------------------------------------------------
# Super-Long 84-Frame Multi-Stage Scream -> Overload -> Explosion -> Flying Wheels & Bar -> Gibs!
# ---------------------------------------------------------------------------

def _extract_d0_anatomical_and_mech_parts(base_d0_pil, wheel_specs_d0):
    """Slices clean, authentic photographic rigid-body parts from the 320x304 d=0 Front Wheelman."""
    scream_d0 = apply_scream_face_and_body(base_d0_pil, 0, 0.5, wheel_specs_d0, intensity=1.12, sound_waves=False)
    arr_s = np.array(scream_d0)
    arr_0 = np.array(base_d0_pil)
    H, W = arr_0.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    def paint_ragged_stump(part_arr, cx_s, cy_s, rx_s, ry_s, seed=1):
        rng = np.random.default_rng(seed)
        ph, pw = part_arr.shape[:2]
        pyg, pxg = np.mgrid[0:ph, 0:pw].astype(np.float32)
        ang = np.arctan2(pyg - cy_s, pxg - cx_s)
        jag = 1.0 + 0.18 * np.sin(5.0 * ang + rng.uniform(0, 6)) + 0.12 * np.cos(9.0 * ang)
        r = np.sqrt(((pxg - cx_s) / rx_s) ** 2 + ((pyg - cy_s) / ry_s) ** 2) / jag
        stump = r <= 1.0
        shade = np.clip(1.15 - 0.65 * r, 0.35, 1.0)
        part_arr[stump, 0] = np.clip(158.0 * shade[stump], 0, 255).astype(np.uint8)
        part_arr[stump, 1] = np.clip(18.0 * shade[stump], 0, 255).astype(np.uint8)
        part_arr[stump, 2] = np.clip(22.0 * shade[stump], 0, 255).astype(np.uint8)
        part_arr[stump, 3] = 255
        bone = r <= 0.34
        part_arr[bone, :3] = [232, 222, 208]
        return part_arr

    # 1) Screaming Head (x=122..178, y=56..126)
    head_crop = arr_s[56:128, 122:178].copy()
    hy, hx = np.mgrid[0:head_crop.shape[0], 0:head_crop.shape[1]].astype(np.float32)
    neck_cut = hy > (62.0 + 3.0 * np.sin(hx * 0.45))
    head_crop[neck_cut, 3] = 0
    head_crop = paint_ragged_stump(head_crop, 28.0, 60.0, 10.5, 4.5, seed=11)
    part_head = Image.fromarray(head_crop, "RGBA")

    # Mask out any warm hand/leg skin touching the wheel rims
    warm_skin_0 = ((arr_0[..., 0].astype(np.float32) - arr_0[..., 2].astype(np.float32)) > 16.0) & (arr_0[..., 0] > 92)

    # 2) Left Wheel (x=54..106, y=176..290)
    lw_mask = ((((xg - 77.5) / 21.0) ** 2 + ((yg - 236.0) / 55.0) ** 2 <= 1.06) | ((xg >= 54) & (xg <= 105) & (yg >= 224) & (yg <= 244))) & (~warm_skin_0)
    lw_arr = arr_0.copy()
    lw_arr[~lw_mask, 3] = 0
    part_lwheel = Image.fromarray(lw_arr[176:291, 54:106], "RGBA")

    # 3) Right Wheel (x=218..276, y=176..290)
    rw_mask = ((((xg - 248.0) / 27.0) ** 2 + ((yg - 233.0) / 54.0) ** 2 <= 1.06) | ((xg >= 218) & (xg <= 246) & (yg >= 222) & (yg >= 242))) & (~warm_skin_0)
    rw_arr = arr_0.copy()
    rw_arr[~rw_mask, 3] = 0
    part_rwheel = Image.fromarray(rw_arr[176:290, 218:276], "RGBA")

    # 4) Steel Axle Bar + Gleaming Central Chrome Cylinder + Fluted Cap (148 x 58)
    bar_w, bar_h = 148, 58
    bar_im = Image.new("RGBA", (bar_w, bar_h), (0, 0, 0, 0))
    bdr = ImageDraw.Draw(bar_im)
    bdr.rounded_rectangle([4, 21, bar_w - 5, 31], radius=4, fill=(92, 98, 106, 255), outline=(42, 46, 52, 255))
    bdr.line([(6, 24), (bar_w - 7, 24)], fill=(224, 232, 242, 255), width=2)
    bdr.line([(6, 29), (bar_w - 7, 29)], fill=(52, 56, 62, 255), width=2)
    bdr.rectangle([4, 18, 18, 34], fill=(232, 236, 240, 255), outline=(105, 110, 118, 255))
    bdr.rectangle([bar_w - 19, 18, bar_w - 5, 34], fill=(232, 236, 240, 255), outline=(105, 110, 118, 255))
    cyl_src = arr_0[212:266, 150:196].copy()
    is_metal = ((cyl_src[..., 0].astype(np.float32) - cyl_src[..., 2].astype(np.float32)) < 16.0) & (cyl_src[..., 3] > 80)
    cyl_src[~is_metal, 3] = 0
    bar_im.alpha_composite(Image.fromarray(cyl_src, "RGBA"), (52, 2))

    # 5) Chrome Fluted End-Cap & Steel Hub Nut Shrapnel (for secondary mid-air bar blast!)
    shrap_cap = Image.fromarray(cyl_src[24:54, 14:44].copy(), "RGBA")
    nut_im = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    ndr = ImageDraw.Draw(nut_im)
    ndr.regular_polygon((9, 9, 7), n_sides=6, rotation=15, fill=(225, 230, 238, 255), outline=(70, 75, 84, 255))
    ndr.ellipse([6, 6, 12, 12], fill=(60, 64, 72, 255))

    # 6) Left Bare Leg + Bent Knee + Hairy Calf + Bare Foot (strictly excluding chest/armpit!)
    ll_arr = arr_s.copy()
    ll_keep = (xg <= 110) & (yg <= 190) & (~lw_mask) & ((xg + yg * 0.55) <= 195.0) & (~((xg > 80) & (yg < 142)))
    ll_arr[~ll_keep, 3] = 0
    ll_crop = ll_arr[82:192, 2:114].copy()
    ll_crop = paint_ragged_stump(ll_crop, 96.0, 86.0, 10.5, 8.0, seed=22)
    part_lleg = Image.fromarray(ll_crop, "RGBA")

    # 7) Right Bare Leg + Bent Knee + Hairy Calf + Bare Foot (strictly excluding chest/armpit!)
    rl_arr = arr_s.copy()
    rl_keep = (xg >= 200) & (yg <= 190) & (~rw_mask) & (((320.0 - xg) + yg * 0.55) <= 202.0) & (~((xg < 236) & (yg < 142)))
    rl_arr[~rl_keep, 3] = 0
    rl_crop = rl_arr[82:192, 200:318].copy()
    rl_crop = paint_ragged_stump(rl_crop, 16.0, 88.0, 10.5, 8.0, seed=33)
    part_rleg = Image.fromarray(rl_crop, "RGBA")

    # 8) 20 Glossy Wet 3D-Shaded Quake Meat & Rib-Bone Gibs
    gib_sprites = []
    rng = np.random.default_rng(1337)
    for gi in range(20):
        sz = int(rng.integers(19, 36))
        gim = np.zeros((sz, sz, 4), dtype=np.uint8)
        gy, gx = np.mgrid[0:sz, 0:sz].astype(np.float32)
        c = sz * 0.5
        ang = np.arctan2(gy - c, gx - c)
        rad = (sz * 0.34) * (1.0 + 0.24 * np.sin(3.0 * ang + gi) + 0.16 * np.cos(5.0 * ang + gi * 1.7))
        dist = np.hypot(gx - c, gy - c)
        inside = dist <= rad
        nx_g = (gx - c) / np.maximum(rad, 1.0)
        ny_g = (gy - c) / np.maximum(rad, 1.0)
        lit = np.clip(0.65 - 0.38 * nx_g - 0.42 * ny_g, 0.18, 1.15)
        spec_g = np.exp(-(((nx_g + 0.32) / 0.24) ** 2 + ((ny_g + 0.32) / 0.24) ** 2)) * 0.65
        gim[inside, 0] = np.clip(178.0 * lit[inside] + 75.0 * spec_g[inside], 0, 255).astype(np.uint8)
        gim[inside, 1] = np.clip(18.0 * lit[inside] + 55.0 * spec_g[inside], 0, 255).astype(np.uint8)
        gim[inside, 2] = np.clip(22.0 * lit[inside] + 55.0 * spec_g[inside], 0, 255).astype(np.uint8)
        gim[inside, 3] = 255
        if gi % 3 == 0:
            bone_m = (np.abs(gy - c + (gx - c) * 0.4) < 2.2) & (gx > c - rad * 0.6) & (gx < c + rad * 0.95)
            gim[bone_m, :3] = [238, 228, 210]
            gim[bone_m, 3] = 255
        gib_sprites.append(Image.fromarray(gim, "RGBA"))

    return dict(
        head=part_head,
        lwheel=part_lwheel,
        rwheel=part_rwheel,
        bar=bar_im,
        shrap_cap=shrap_cap,
        shrap_nut=nut_im,
        lleg=part_lleg,
        rleg=part_rleg,
        gibs=gib_sprites,
    )


def _draw_hdr_starburst(stage_wh, cx, cy, radius, intensity=1.0, n_rays=14, seed=7):
    """Renders a soft HDR radial plasma bloom + spiky golden-white detonation rays (zero flat disc edge!)."""
    W_s, H_s = stage_wh
    yg, xg = np.mgrid[0:H_s, 0:W_s].astype(np.float32)
    dx = xg - cx
    dy = yg - cy
    r = np.hypot(dx, dy) / max(radius, 1.0)
    ang = np.arctan2(dy, dx)

    rng = np.random.default_rng(seed)
    ray_field = np.zeros_like(r)
    for _ in range(n_rays):
        a0 = rng.uniform(-math.pi, math.pi)
        w_a = rng.uniform(0.045, 0.11)
        len_m = rng.uniform(0.85, 1.55)
        da = (ang - a0 + math.pi) % (2.0 * math.pi) - math.pi
        ray_field = np.maximum(ray_field, np.exp(-((da / w_a) ** 2)) * np.clip(1.0 - r / len_m, 0.0, 1.0) ** 1.6)

    core = np.exp(-(r * 1.65) ** 2)
    halo = np.exp(-(r * 0.92) ** 2) * 0.65
    val = np.clip((core * 1.15 + halo + ray_field * 0.78) * intensity, 0.0, 1.35)

    out = np.zeros((H_s, W_s, 4), dtype=np.uint8)
    out[..., 0] = np.clip(val * 255.0 + 40.0 * core, 0, 255).astype(np.uint8)
    out[..., 1] = np.clip((val ** 1.18) * 245.0, 0, 255).astype(np.uint8)
    out[..., 2] = np.clip((val ** 1.85) * 215.0, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(val * 248.0, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _load_vfx_fireball_rgba():
    fb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref", "wheelman_views", "fx_fireball_blast.jpg")
    if not os.path.exists(fb_path):
        return None
    rgb = np.asarray(Image.open(fb_path).convert("RGB"), dtype=np.float32)
    # Extract clean RGBA from black studio plate: bright flame & warm smoke tendrils get crisp alpha
    mx = np.max(rgb, axis=-1) / 255.0
    alpha = np.clip((mx - 0.035) / 0.36, 0.0, 1.0) ** 0.78
    # Un-premultiply dark fringes cleanly so charcoal smoke edges stay rich, not muddy
    denom = np.maximum(alpha[..., None], 0.18)
    clean_rgb = np.clip(rgb / denom, 0.0, 255.0)
    rgba = np.dstack([clean_rgb.astype(np.uint8), np.clip(alpha * 255.0, 0, 255).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def _blit_evolving_vfx_fireball(stage, fb_rgba, cx, cy, prog_01, max_diam=280.0, rot_deg=0.0):
    """Animates the photorealistic VFX fireball from blinding incandescent core (prog=0) ->
    churning orange-amber flame cloud (prog=0.35) -> rising dark charcoal smoke plume (prog=1.0)."""
    if fb_rgba is None or prog_01 < 0.0 or prog_01 >= 1.0:
        return
    scale_f = 0.42 + 0.72 * (prog_01 ** 0.52)
    diam = max(16, int(round(max_diam * scale_f)))
    im = fb_rgba.resize((diam, diam), Image.BICUBIC)
    if abs(rot_deg) > 0.1:
        im = im.rotate(rot_deg, resample=Image.BICUBIC, expand=True)
    arr = np.array(im, dtype=np.float32)
    # Cool flame into billowing charcoal smoke for prog_01 > 0.35
    if prog_01 < 0.22:
        boost = 1.0 + (1.0 - prog_01 / 0.22) * 0.55
        arr[..., :3] = np.clip(arr[..., :3] * boost, 0.0, 255.0)
    elif prog_01 > 0.36:
        cool = min(1.0, (prog_01 - 0.36) / 0.48)
        lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
        charcoal = np.clip(lum * 0.28 + 18.0, 18.0, 72.0)[..., None]
        arr[..., :3] = arr[..., :3] * (1.0 - cool) + charcoal * cool
    fade = 1.0 if prog_01 < 0.45 else max(0.0, 1.0 - ((prog_01 - 0.45) / 0.55) ** 1.25)
    arr[..., 3] *= fade * 0.94
    im_out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    lift_y = cy - prog_01 * (max_diam * 0.22)
    px = int(round(cx - im_out.width * 0.5))
    py = int(round(lift_y - im_out.height * 0.5))
    stage.alpha_composite(im_out, (px, py))


def build_explosion_gib_sequence(base_d0_pil, wheel_specs_d0, n_frames=84, stage_wh=(480, 340), ground_y=308):
    """Synthesizes an 84-frame (3.50s @ 24 FPS) 5-Act Mega Explosion & Gibs sequence:
         Frames  0..17 : Act 1 - Frantic Blood-Curdling Panic Scream & Bare-Leg Thrashing
         Frames 18..31 : Act 2 - Critical Chrome-Cylinder Pressure Overload, Steam Jets, Plasma Cracks & Torso Bloat
         Frames 32..38 : Act 3 - Blinding Starburst Core Detonation, Supersonic Shockwaves & 20-Gib Arterial Eruption
         Frames 39..61 : Act 4 - Flying Bouncing Wheels, Cartwheeling Axle+Chrome Bar (+ Secondary Mid-Air Explosion at f=44
                                 blasting off chrome cap & hex nuts!), Pinwheeling Bare Legs & Persistent Blood Pools
         Frames 62..83 : Act 5 - Screaming Severed Head Plummets from the Sky, Bounces Twice in the Gore & Rolls Upright!
    """
    W_s, H_s = stage_wh
    cx_s = W_s * 0.5
    ox_d0 = int(round(cx_s - base_d0_pil.width * 0.5))
    oy_d0 = int(round(ground_y - 288))

    parts = _extract_d0_anatomical_and_mech_parts(base_d0_pil, wheel_specs_d0)
    vfx_fb = _load_vfx_fireball_rgba()
    sec_blast_xy = [cx_s, ground_y - 120.0]
    rng = np.random.default_rng(20261031)
    dt = 1.0 / 24.0
    ACT2_F = 18
    DET_F = 32     # Primary core detonation
    SEC_F = 44     # Secondary mid-air chrome-bar explosion!

    bodies = [
        dict(name="lwheel", img=parts["lwheel"], x=cx_s - 82.0, y=ground_y - 54.0, vx=-164.0, vy=-285.0, ang=0.0, omg=-680.0, half_l=0.0, rad=48.0, bounce=0.60, fric=0.88, squash=0.0, active=True),
        dict(name="rwheel", img=parts["rwheel"], x=cx_s + 88.0, y=ground_y - 55.0, vx=+170.0, vy=-310.0, ang=0.0, omg=+740.0, half_l=0.0, rad=48.0, bounce=0.62, fric=0.88, squash=0.0, active=True),
        # Elongated steel axle + chrome cylinder bar (half_l=64 gives authentic angle-dependent ground clatter -> flat settle!)
        dict(name="bar",    img=parts["bar"],    x=cx_s + 4.0,  y=ground_y - 58.0, vx=+72.0,  vy=-368.0, ang=-8.0, omg=+1080.0, half_l=64.0, rad=14.0, bounce=0.48, fric=0.76, squash=0.0, active=True),
        dict(name="lleg",   img=parts["lleg"],   x=cx_s - 94.0, y=ground_y - 148.0, vx=-128.0, vy=-285.0, ang=0.0, omg=-520.0, half_l=36.0, rad=24.0, bounce=0.36, fric=0.68, squash=0.0, active=True),
        dict(name="rleg",   img=parts["rleg"],   x=cx_s + 96.0, y=ground_y - 148.0, vx=+134.0, vy=-270.0, ang=0.0, omg=+490.0, half_l=36.0, rad=24.0, bounce=0.36, fric=0.68, squash=0.0, active=True),
        # Screaming severed head rockets skyward at f=32 (vy=-545 -> 1.26s hang time -> lands dramatically at f=62!)
        dict(name="head",   img=parts["head"],   x=cx_s - 8.0,  y=ground_y - 196.0, vx=+14.0,  vy=-535.0, ang=0.0, omg=+560.0, half_l=0.0, rad=25.0, bounce=0.50, fric=0.68, squash=0.0, active=True),
        # Secondary shrapnel spawned at SEC_F (f=44) when the chrome bar detonates mid-air!
        dict(name="cap",    img=parts["shrap_cap"], x=0.0, y=0.0, vx=+185.0, vy=-210.0, ang=0.0, omg=+1350.0, half_l=0.0, rad=11.0, bounce=0.55, fric=0.80, squash=0.0, active=False),
        dict(name="nutL",   img=parts["shrap_nut"], x=0.0, y=0.0, vx=-215.0, vy=-180.0, ang=0.0, omg=-1600.0, half_l=0.0, rad=8.0,  bounce=0.62, fric=0.82, squash=0.0, active=False),
        dict(name="nutR",   img=parts["shrap_nut"], x=0.0, y=0.0, vx=+145.0, vy=-265.0, ang=0.0, omg=+1550.0, half_l=0.0, rad=8.0,  bounce=0.62, fric=0.82, squash=0.0, active=False),
    ]

    gibs = []
    for gi, gim in enumerate(parts["gibs"]):
        ang_g = math.radians(-164.0 + (gi / 19.0) * 148.0 + rng.uniform(-6.0, 6.0))
        spd = rng.uniform(165.0, 420.0)
        gibs.append(dict(
            img=gim,
            x=cx_s + rng.uniform(-24.0, 24.0),
            y=ground_y - rng.uniform(85.0, 158.0),
            vx=math.cos(ang_g) * spd * 0.72,
            vy=math.sin(ang_g) * spd,
            ang=rng.uniform(0, 360),
            omg=rng.uniform(-780.0, 780.0),
            rad=gim.height * 0.34,
            bounce=rng.uniform(0.26, 0.46),
            splatted=False,
        ))

    blood_drops = []
    sparks = []
    smoke_puffs = []
    floor_stains = []

    def spawn_sparks(sx, sy, count, speed_lo=90.0, speed_hi=340.0, upward_bias=-110.0):
        for _ in range(count):
            a = rng.uniform(0.0, 2.0 * math.pi)
            sp = rng.uniform(speed_lo, speed_hi)
            sparks.append(dict(
                x=float(sx), y=float(sy),
                vx=math.cos(a) * sp, vy=math.sin(a) * sp + upward_bias,
                life=1.0, decay=rng.uniform(1.5, 3.0),
                size=rng.uniform(1.6, 3.4),
            ))

    def spawn_blood_burst(bx, by, count, speed_lo=60.0, speed_hi=320.0):
        for _ in range(count):
            a = rng.uniform(-math.pi * 0.96, -math.pi * 0.04)
            sp = rng.uniform(speed_lo, speed_hi)
            blood_drops.append(dict(
                x=float(bx + rng.uniform(-14, 14)),
                y=float(by + rng.uniform(-18, 18)),
                vx=math.cos(a) * sp * 0.78,
                vy=math.sin(a) * sp - rng.uniform(20.0, 95.0),
                r=rng.uniform(2.0, 5.2),
                alive=True,
            ))

    def spawn_fireball_cluster(fx, fy, count, scale_r=1.0):
        for _ in range(count):
            a = rng.uniform(0.0, 2.0 * math.pi)
            sp = rng.uniform(15.0, 150.0) * scale_r
            smoke_puffs.append(dict(
                x=float(fx + rng.uniform(-16, 16) * scale_r),
                y=float(fy + rng.uniform(-16, 16) * scale_r),
                vx=math.cos(a) * sp * 0.85,
                vy=math.sin(a) * sp * 0.65 - rng.uniform(28.0, 84.0),
                r=rng.uniform(18.0, 42.0) * scale_r,
                age=0.0,
                max_age=rng.uniform(0.60, 1.55),
            ))

    frames_out = []
    GRAV = 880.0

    for f in range(n_frames):
        stage = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))

        # --- ACT 1 & ACT 2: Pre-Detonation Panic Scream & Critical Core Overload (f = 0 .. DET_F-1) ---
        if f < DET_F:
            ph_s = (f * 0.125) % 1.0
            ramp = min(1.0, (f + 1) / 8.0)
            wm_im = apply_scream_face_and_body(base_d0_pil, 0, ph_s, wheel_specs_d0, intensity=0.55 + 0.65 * ramp, sound_waves=True)

            shake_x, shake_y = 0, 0
            if f >= ACT2_F:
                ov = (f - (ACT2_F - 1)) / float(DET_F - (ACT2_F - 1))
                wm_arr = np.array(wm_im).astype(np.float32)
                hy, hx = np.mgrid[0:wm_arr.shape[0], 0:wm_arr.shape[1]].astype(np.float32)
                core_x, core_y = 160.0, 198.0
                rc = np.sqrt(((hx - core_x) / 68.0) ** 2 + ((hy - core_y) / 76.0) ** 2)
                bloat = np.exp(-(rc ** 2)) * (0.24 * (ov ** 1.45) + 0.045 * math.sin(f * 2.6))
                mx_b = (hx - (hx - core_x) * bloat).astype(np.float32)
                my_b = (hy - (hy - core_y) * bloat).astype(np.float32)
                wm_arr = _premul_remap(wm_arr.astype(np.uint8), mx_b, my_b).astype(np.float32)

                glow = np.exp(-(((hx - 164.0) / (46.0 + 38.0 * ov)) ** 2 + ((hy - 216.0) / (48.0 + 40.0 * ov)) ** 2)) * (wm_arr[..., 3] > 60)
                wm_arr[..., 0] = np.clip(wm_arr[..., 0] + glow * 240.0 * ov, 0, 255)
                wm_arr[..., 1] = np.clip(wm_arr[..., 1] + glow * 160.0 * (ov ** 1.3), 0, 255)
                wm_arr[..., 2] = np.clip(wm_arr[..., 2] + glow * 70.0 * (ov ** 2.0), 0, 255)
                wm_im = Image.fromarray(wm_arr.astype(np.uint8), "RGBA")

                shake_amp = 1.5 + 5.2 * ov
                shake_x = int(round(math.sin(f * 3.9) * shake_amp))
                shake_y = int(round(math.cos(f * 5.1) * shake_amp * 0.6))

            stage.alpha_composite(wm_im, (ox_d0 + shake_x, oy_d0 + shake_y))

            if f >= ACT2_F + 1:
                ov = (f - ACT2_F) / float(DET_F - ACT2_F)
                fx_ov = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
                dr_o = ImageDraw.Draw(fx_ov)
                core_sx, core_sy = cx_s + 4 + shake_x, ground_y - 68 + shake_y
                for jx, jy, jvx, jvy in ((core_sx + 18, core_sy + 28, 24, 34), (cx_s - 82, ground_y - 52, -38, -14), (cx_s + 88, ground_y - 54, 38, -14)):
                    for s_i in range(4):
                        fr_s = (s_i + (f % 3) * 0.33) / 4.0
                        dr_o.ellipse([
                            jx + jvx * fr_s - 6 - 8 * fr_s, jy + jvy * fr_s - 6 - 8 * fr_s,
                            jx + jvx * fr_s + 6 + 8 * fr_s, jy + jvy * fr_s + 6 + 8 * fr_s,
                        ], fill=(255, 242, 220, int(160 * ov * (1.0 - fr_s))))
                n_bolts = 3 + int(6 * ov)
                for _ in range(n_bolts):
                    ang_b = rng.uniform(0, 2 * math.pi)
                    pts = [(core_sx, core_sy)]
                    bx_c, by_c = float(core_sx), float(core_sy)
                    for _ in range(4):
                        ang_b += rng.uniform(-0.55, 0.55)
                        step_l = rng.uniform(12.0, 28.0) * (0.5 + 0.7 * ov)
                        bx_c += math.cos(ang_b) * step_l
                        by_c += math.sin(ang_b) * step_l
                        pts.append((bx_c, by_c))
                    dr_o.line(pts, fill=(255, 175, 45, int(215 * ov)), width=4)
                    dr_o.line(pts, fill=(255, 255, 220, int(248 * ov)), width=2)
                stage.alpha_composite(fx_ov)

            frames_out.append(stage)
            continue

        # --- TRIGGER PRIMARY DETONATION AT f == DET_F ---
        if f == DET_F:
            floor_stains.append(dict(x=cx_s, y=ground_y + 2.0, rx=72.0, ry=10.5, col=(24, 20, 20, 220)))
            floor_stains.append(dict(x=cx_s, y=ground_y + 1.0, rx=45.0, ry=6.5, col=(128, 12, 16, 228)))
            spawn_fireball_cluster(cx_s, ground_y - 96.0, 34, scale_r=1.22)
            spawn_blood_burst(cx_s, ground_y - 108.0, 76, speed_lo=75.0, speed_hi=355.0)
            spawn_sparks(cx_s, ground_y - 84.0, 72, speed_lo=120.0, speed_hi=420.0, upward_bias=-135.0)

        # --- TRIGGER SECONDARY MID-AIR CHROME-BAR DETONATION AT f == SEC_F ---
        bar_body = bodies[2]
        if f == SEC_F:
            sec_blast_xy[0], sec_blast_xy[1] = bar_body["x"], bar_body["y"]
            spawn_fireball_cluster(bar_body["x"], bar_body["y"], 16, scale_r=0.72)
            spawn_sparks(bar_body["x"], bar_body["y"], 48, speed_lo=95.0, speed_hi=340.0, upward_bias=-65.0)
            bar_body["vx"] = -115.0
            bar_body["vy"] = -125.0
            bar_body["omg"] = -1320.0
            for sh_b in bodies[6:]:
                sh_b["active"] = True
                sh_b["x"] = bar_body["x"]
                sh_b["y"] = bar_body["y"]

        # 1) Persistent scorch crater & wet crimson blood pools
        floor_layer = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        fdr = ImageDraw.Draw(floor_layer)
        for st in floor_stains:
            fdr.ellipse([st["x"] - st["rx"], st["y"] - st["ry"], st["x"] + st["rx"], st["y"] + st["ry"]], fill=st["col"])
        stage.alpha_composite(floor_layer)

        # 1b) Photorealistic VFX Gasoline Fireball Plumes (Primary & Secondary Mid-Air Blast!)
        if DET_F <= f < DET_F + 26:
            _blit_evolving_vfx_fireball(stage, vfx_fb, cx_s, ground_y - 98.0, (f - DET_F) / 26.0, max_diam=288.0, rot_deg=(f - DET_F) * 3.5)
        if SEC_F <= f < SEC_F + 18:
            _blit_evolving_vfx_fireball(stage, vfx_fb, sec_blast_xy[0], sec_blast_xy[1], (f - SEC_F) / 18.0, max_diam=165.0, rot_deg=110.0 - (f - SEC_F) * 5.0)

        # 2) Billowing fireball -> cooling dark charcoal smoke
        smoke_layer = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        sdr = ImageDraw.Draw(smoke_layer)
        for sp in smoke_puffs:
            if sp["age"] >= sp["max_age"]:
                continue
            u = sp["age"] / sp["max_age"]
            rad = sp["r"] * (0.65 + 0.95 * (u ** 0.6))
            if u < 0.18:
                k = u / 0.18
                col = (255, int(252 - 42 * k), int(210 - 155 * k), int(245 - 25 * k))
            elif u < 0.42:
                k = (u - 0.18) / 0.24
                col = (int(255 - 95 * k), int(185 - 125 * k), int(48 - 22 * k), int(220 - 55 * k))
            else:
                k = (u - 0.42) / 0.58
                g_v = int(56 - 24 * k)
                col = (g_v + 6, g_v, g_v, int(165 * ((1.0 - k) ** 1.35)))
            sdr.ellipse([sp["x"] - rad, sp["y"] - rad * 0.88, sp["x"] + rad, sp["y"] + rad * 0.88], fill=col)
            sp["x"] += sp["vx"] * dt
            sp["y"] += sp["vy"] * dt
            sp["vx"] *= 0.92
            sp["vy"] = sp["vy"] * 0.93 - 14.0 * dt
            sp["age"] += dt
        smoke_layer = smoke_layer.filter(ImageFilter.GaussianBlur(radius=1.8))
        stage.alpha_composite(smoke_layer)

        # 3) 20 Chunky Quake Meat & Rib-Bone Gibs
        for gb in gibs:
            if f > DET_F:
                gb["vy"] += GRAV * dt
                gb["x"] += gb["vx"] * dt
                gb["y"] += gb["vy"] * dt
                gb["ang"] += gb["omg"] * dt
                if gb["y"] >= ground_y - gb["rad"]:
                    gb["y"] = ground_y - gb["rad"]
                    if abs(gb["vy"]) > 55.0:
                        gb["vy"] = -abs(gb["vy"]) * gb["bounce"]
                        gb["vx"] *= 0.62
                        gb["omg"] *= 0.55
                        if not gb["splatted"]:
                            gb["splatted"] = True
                            floor_stains.append(dict(
                                x=gb["x"], y=ground_y + rng.uniform(-2.0, 4.0),
                                rx=rng.uniform(10.0, 22.0), ry=rng.uniform(2.5, 5.0),
                                col=(int(rng.integers(115, 165)), 10, 14, 215),
                            ))
                            spawn_blood_burst(gb["x"], ground_y - 4.0, 5, speed_lo=35.0, speed_hi=110.0)
                    else:
                        gb["vy"] = 0.0
                        gb["vx"] *= 0.70
                        gb["omg"] *= 0.50
                if gb["x"] < 18.0:
                    gb["x"] = 18.0
                    gb["vx"] = abs(gb["vx"]) * 0.55
                elif gb["x"] > W_s - 18.0:
                    gb["x"] = W_s - 18.0
                    gb["vx"] = -abs(gb["vx"]) * 0.55
            _paste_rotated_rgba(stage, gb["img"], gb["x"], gb["y"], gb["ang"], max_bottom_y=ground_y + 4)

        # 4) Hero Photographic Rigid Bodies (Wheels, Axle+Chrome Bar, Shrapnel, Bare Legs, Screaming Head)
        for bd in bodies:
            if not bd["active"]:
                continue
            if f > DET_F:
                bd["vy"] += GRAV * dt
                bd["x"] += bd["vx"] * dt
                bd["y"] += bd["vy"] * dt
                bd["ang"] += bd["omg"] * dt
                bd["squash"] *= 0.52

                if bd["name"] in ("lwheel", "rwheel", "bar") and f < 64 and (f % 2 == 0) and bd["y"] < ground_y - 30:
                    smoke_puffs.append(dict(
                        x=bd["x"], y=bd["y"], vx=rng.uniform(-12, 12), vy=-24.0,
                        r=11.0 if bd["name"] == "bar" else 15.0, age=0.44, max_age=0.95,
                    ))
                if bd["name"] == "head" and bd["y"] < ground_y - 35 and (f % 2 == 0):
                    blood_drops.append(dict(x=bd["x"], y=bd["y"] + 14, vx=rng.uniform(-24, 24), vy=18.0, r=3.2, alive=True))

                # Angle-aware vertical half-extent so elongated steel bar & legs clatter flat onto ground_y!
                rad_a = math.radians(bd["ang"])
                eff_ry = bd["rad"] + bd["half_l"] * abs(math.sin(rad_a)) * 0.65

                if bd["y"] >= ground_y - eff_ry:
                    bd["y"] = ground_y - eff_ry
                    # Gravity torque tips elongated bar/legs toward horizontal on ground contact!
                    if bd["half_l"] > 0.0:
                        sin2 = math.sin(2.0 * rad_a)
                        bd["omg"] = bd["omg"] * 0.45 - sin2 * 420.0
                        # Gently relax angle toward nearest horizontal (0 or 180 deg) when nearly settled
                        if abs(bd["vy"]) <= 52.0:
                            rem = ((bd["ang"] + 90.0) % 180.0) - 90.0
                            bd["ang"] -= rem * 0.42
                            bd["omg"] *= 0.30

                    if abs(bd["vy"]) > 48.0:
                        bd["vy"] = -abs(bd["vy"]) * bd["bounce"]
                        bd["vx"] *= bd["fric"]
                        if bd["half_l"] == 0.0:
                            bd["omg"] *= 0.65
                        bd["squash"] = 0.24
                        if bd["name"] in ("lwheel", "rwheel", "bar", "cap", "nutL", "nutR"):
                            spawn_sparks(bd["x"], ground_y - 2.0, 18 if bd["name"] == "bar" else 10, speed_lo=60.0, speed_hi=215.0, upward_bias=-85.0)
                        else:
                            floor_stains.append(dict(x=bd["x"], y=ground_y + 2.0, rx=22.0, ry=4.4, col=(145, 12, 16, 228)))
                            spawn_blood_burst(bd["x"], ground_y - 4.0, 11, speed_lo=45.0, speed_hi=155.0)
                    else:
                        bd["vy"] = 0.0
                        bd["vx"] *= 0.72
                        if bd["name"] == "head":
                            bd["omg"] = 0.0
                            rem_h = ((bd["ang"] + 180.0) % 360.0) - 180.0
                            bd["ang"] = rem_h * 0.48
                        elif bd["half_l"] == 0.0:
                            bd["omg"] *= 0.74

                margin = 36.0
                if bd["x"] < margin:
                    bd["x"] = margin
                    bd["vx"] = abs(bd["vx"]) * 0.52
                elif bd["x"] > W_s - margin:
                    bd["x"] = W_s - margin
                    bd["vx"] = -abs(bd["vx"]) * 0.52

            sx_b = 1.0 + bd["squash"]
            sy_b = 1.0 - bd["squash"] * 0.78
            _paste_rotated_rgba(stage, bd["img"], bd["x"], bd["y"], bd["ang"], sx=sx_b, sy=sy_b, max_bottom_y=ground_y + 5)

        # 5) Arterial blood droplets + hot metal sparks + shockwaves + HDR starburst flash!
        fx_front = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        xdr = ImageDraw.Draw(fx_front)

        for dp in blood_drops:
            if not dp["alive"]:
                continue
            x0_b, y0_b = dp["x"], dp["y"]
            dp["vy"] += GRAV * 0.92 * dt
            dp["x"] += dp["vx"] * dt
            dp["y"] += dp["vy"] * dt
            if dp["y"] >= ground_y:
                dp["alive"] = False
                floor_stains.append(dict(x=dp["x"], y=ground_y + rng.uniform(-1.5, 3.5), rx=dp["r"] * 2.2, ry=dp["r"] * 0.65, col=(135, 11, 15, 200)))
                continue
            r_b = dp["r"]
            xdr.line([(x0_b, y0_b), (dp["x"], dp["y"])], fill=(185, 16, 22, 225), width=max(2, int(round(r_b * 1.3))))
            xdr.ellipse([dp["x"] - r_b, dp["y"] - r_b, dp["x"] + r_b, dp["y"] + r_b], fill=(212, 24, 30, 240))

        for spk in sparks:
            if spk["life"] <= 0.0:
                continue
            x0_s, y0_s = spk["x"], spk["y"]
            spk["vy"] += GRAV * 0.55 * dt
            spk["x"] += spk["vx"] * dt
            spk["y"] += spk["vy"] * dt
            if spk["y"] >= ground_y:
                spk["y"] = ground_y
                spk["vy"] = -abs(spk["vy"]) * 0.45
                spk["vx"] *= 0.75
            spk["life"] -= spk["decay"] * dt
            al = int(round(max(0.0, min(1.0, spk["life"])) * 255.0))
            if al > 8:
                xdr.line([(x0_s, y0_s), (spk["x"], spk["y"])], fill=(255, int(150 + 100 * max(0, spk["life"])), 60, al), width=max(1, int(round(spk["size"]))))
                xdr.ellipse([spk["x"] - 1.5, spk["y"] - 1.5, spk["x"] + 1.5, spk["y"] + 1.5], fill=(255, 250, 210, al))

        if DET_F <= f <= DET_F + 6:
            k_sh = (f - DET_F) / 6.0
            r_sh = 30.0 + k_sh * 205.0
            a_sh = int(round((1.0 - k_sh) * 235.0))
            cy_sh = ground_y - 96.0
            xdr.ellipse([cx_s - r_sh, cy_sh - r_sh * 0.72, cx_s + r_sh, cy_sh + r_sh * 0.72], outline=(255, 242, 185, a_sh), width=max(2, int(round(7 * (1.0 - k_sh)))))

        if SEC_F <= f <= SEC_F + 4:
            k2 = (f - SEC_F) / 4.0
            r2 = 16.0 + k2 * 98.0
            a2 = int(round((1.0 - k2) * 215.0))
            bx2, by2 = bar_body["x"], bar_body["y"]
            xdr.ellipse([bx2 - r2, by2 - r2, bx2 + r2, by2 + r2], outline=(255, 225, 130, a2), width=max(2, int(round(4 * (1.0 - k2)))))

        if f >= 58 and (f % 3 == 0):
            smoke_puffs.append(dict(x=bar_body["x"] + rng.uniform(-16, 16), y=ground_y - 8.0, vx=rng.uniform(-6, 6), vy=-26.0, r=9.5, age=0.52, max_age=1.18))

        stage.alpha_composite(fx_front)

        # HDR starburst flash on DET_F..DET_F+2 and SEC_F..SEC_F+1
        if DET_F <= f <= DET_F + 2:
            k_fl = (f - DET_F) / 3.0
            sb_im = _draw_hdr_starburst(stage_wh, cx_s, ground_y - 96.0, radius=135.0 * (1.0 - 0.25 * k_fl), intensity=1.15 * (1.0 - k_fl), n_rays=16, seed=32 + f)
            stage.alpha_composite(sb_im)
        elif SEC_F <= f <= SEC_F + 1:
            k_fl2 = (f - SEC_F) / 2.0
            sb_im2 = _draw_hdr_starburst(stage_wh, bar_body["x"], bar_body["y"], radius=68.0 * (1.0 - 0.25 * k_fl2), intensity=0.95 * (1.0 - k_fl2), n_rays=10, seed=90 + f)
            stage.alpha_composite(sb_im2)

        frames_out.append(stage)

    return frames_out


# ---------------------------------------------------------------------------
# Spherical Vertical Pitch Views: +90° Above, +45° Above, -45° Below, -90° Below
# ---------------------------------------------------------------------------

def build_vertical_pitch_views(views_dir, ref_skin, key_fn, inpaint_fn, cal_fn, rot_ell_fn):
    """Builds and skin-calibrates the 4 photorealistic vertical elevation views:
         - above90 : +90° Pure Top-Down Overhead Plan View (360° Z-rotatable!)
         - above45 : +45° Steep High-Angle Above View
         - below45 : -45° Steep Worm's-Eye Below View
         - below90 : -90° Pure Glass-Floor Underneath View (360° Z-rotatable!)
    """
    from scipy import ndimage

    # 1) +90° Directly Above
    im_a90 = key_fn(Image.open(os.path.join(views_dir, "view_above_90.jpg")))
    arr = np.array(im_a90).astype(np.float32)
    H, W = arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    dark_sh = (arr[..., 3] > 40) & (yg >= 345) & (yg <= 452) & (xg >= 395) & (xg <= 810) & ((arr[..., 0] - arr[..., 2]) < 16.0) & (lum < 85.0)
    im_a90 = cal_fn(inpaint_fn(im_a90, dark_sh, grain_src_box=(365, 235, 455, 315)), ref_skin, strength=0.55)

    # 2) +45° High-Angle Above
    im_a45 = key_fn(Image.open(os.path.join(views_dir, "view_above_45.jpg")))
    arr = np.array(im_a45).astype(np.float32)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    dark_sh = (arr[..., 3] > 40) & (yg >= 400) & (yg <= 470) & (xg >= 510) & (xg <= 690) & ((arr[..., 0] - arr[..., 2]) < 14.0) & (lum < 68.0)
    im_a45 = cal_fn(inpaint_fn(im_a45, dark_sh, grain_src_box=(390, 250, 480, 330)), ref_skin, strength=0.55)

    # 3) -45° Worm's-Eye Below
    orig_b45 = key_fn(Image.open(os.path.join(views_dir, "view_below_45.jpg")))
    arr = np.array(orig_b45).astype(np.float32)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    mech_cyl = ((xg >= 502) & (xg <= 696) & (yg >= 330)) | (rot_ell_fn(xg, yg, 598.0, 646.0, 98.0, 112.0, 0.0) <= 1.08)
    mech_axle = (yg >= 538) & (yg <= 592) & ((xg <= 515) | (xg >= 682)) & (lum > 45.0)
    mech_wheels = (xg <= 290) | (xg >= 915)
    mech = mech_cyl | mech_axle | mech_wheels
    is_shorts = (arr[..., 3] > 30) & (~mech) & (xg >= 385) & (xg <= 815) & (yg >= 440) & (yg <= 710) & ((arr[..., 0] - arr[..., 2]) < 18.0) & (lum < 105.0)
    baggy_under = is_shorts & (yg > 588)
    keep = (arr[..., 3] > 20) & (~baggy_under)
    dist_in = ndimage.distance_transform_edt(keep)
    arr[..., 3] = np.where(baggy_under, 0.0, np.minimum(arr[..., 3], np.clip(dist_in / 1.8, 0.0, 1.0) * 255.0))
    im_b45 = inpaint_fn(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), is_shorts & (~baggy_under), grain_src_box=(445, 360, 535, 450))
    cur = np.array(im_b45)
    cur[mech] = np.array(orig_b45)[mech]
    im_b45 = cal_fn(Image.fromarray(cur, "RGBA"), ref_skin, strength=0.55)

    # 4) -90° Directly Below (Pure Glass-Floor Underneath View, seamless bare hips/back + clean nut & axle!)
    orig_b90 = key_fn(Image.open(os.path.join(views_dir, "view_below_90.jpg")))
    arr = np.array(orig_b90).astype(np.float32)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    mech_cyl90 = (
        ((xg >= 544) & (xg <= 658) & (yg >= 50) & (yg <= 508) & (((arr[..., 0] - arr[..., 2]) < 18.0) | (yg < 495)))
        | ((xg >= 578) & (xg <= 622) & (yg >= 506) & (yg <= 572) & (lum > 40.0))
    )
    mech_axle90 = (yg >= 506) & (yg <= 538) & (xg >= 205) & (xg <= 995) & (~((xg > 288) & (xg < 402))) & (~((xg > 802) & (xg < 916)))
    mech_wheels90 = (xg <= 282) | (xg >= 920)
    mech90 = mech_cyl90 | mech_axle90 | mech_wheels90

    is_shorts90 = (arr[..., 3] > 30) & (~mech90) & (xg >= 355) & (xg <= 845) & (yg >= 420) & (yg <= 765) & ((arr[..., 0] - arr[..., 2]) < 18.0) & (lum < 114.0)
    hip_hw = 210.0 - 28.0 * np.clip((yg - 540.0) / 190.0, 0.0, 1.0) ** 1.4
    puff90 = is_shorts90 & (np.abs(xg - 600.0) > hip_hw)
    keep90 = (arr[..., 3] > 20) & (~puff90)
    dist_in90 = ndimage.distance_transform_edt(keep90)
    arr[..., 3] = np.where(puff90, 0.0, np.minimum(arr[..., 3], np.clip(dist_in90 / 1.8, 0.0, 1.0) * 255.0))
    im_b90 = inpaint_fn(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), is_shorts90 & (~puff90), cleft_x=600.0, grain_src_box=(435, 290, 520, 385))
    cur90 = np.array(im_b90)
    cur90[mech90] = np.array(orig_b90)[mech90]
    im_b90 = cal_fn(Image.fromarray(cur90, "RGBA"), ref_skin, strength=0.55)

    return dict(above90=im_a90, above45=im_a45, below45=im_b45, below90=im_b90)


def normalize_vertical_view(im_rgba, pitch_key, canvas_wh=(320, 304)):
    """Places vertical pitch view cleanly onto 320x304:
       - above90 & below90 are centered at (160, 152) with max span 214px so full 360° Z-rotation never clips!
       - above45 & below45 fill 256px width nicely anchored near ground/center."""
    W_c, H_c = canvas_wh
    arr = np.array(im_rgba)
    ys, xs = np.nonzero(arr[..., 3] > 24)
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = float(ys.min()), float(ys.max())
    sw, sh = x1 - x0, y1 - y0
    if pitch_key in ("above90", "below90"):
        scale = min(214.0 / sw, 206.0 / sh)
    else:
        scale = min(286.0 / sw, 246.0 / sh)
    rw, rh = max(2, int(round(im_rgba.width * scale))), max(2, int(round(im_rgba.height * scale)))
    rsz = im_rgba.resize((rw, rh), Image.LANCZOS)
    cx_src, cy_src = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    ox = int(round(W_c * 0.5 - cx_src * scale))
    oy = int(round(H_c * 0.5 - cy_src * scale)) if pitch_key in ("above90", "below90") else int(round(284.0 - y1 * scale))
    out = Image.new("RGBA", canvas_wh, (0, 0, 0, 0))
    out.paste(rsz, (ox, oy), rsz)
    return out


def animate_vertical_pitch_frame(norm_im, pitch_key, phase_01, scream=False):
    """Synthesizes high-FPS rolling tire treads + leg kicks (+ scream waves/flush) for Above & Below views!"""
    rgba = np.array(norm_im).copy()
    H, W = rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    t = 2.0 * math.pi * phase_01
    cx, cy = W * 0.5, H * 0.5

    # Lock outer left & right wheels + central axle bar while letting bare legs kick & torso bob
    if pitch_key in ("above90", "below90"):
        tire_zone = (xg < 96.0) | (xg > W - 96.0)
        axle_y = 152.0 if pitch_key == "above90" else 166.0
    else:
        tire_zone = (xg < 84.0) | (xg > W - 84.0)
        axle_y = 196.0 if pitch_key == "above45" else 202.0

    free_w = (~tire_zone).astype(np.float32) * (1.0 - 0.85 * np.exp(-((yg - axle_y) / 9.0) ** 2))
    free_w = cv2.GaussianBlur(free_w, (9, 9), 2.2)

    # Alternating left/right leg kicks + suspension bounce
    freq_m = 2.0 if scream else 1.0
    bob = (1.6 if not scream else 2.2) * math.sin(freq_m * t) * free_w
    if pitch_key in ("above90", "above45"):
        leg_band = np.clip((yg - (axle_y - 10.0)) / 18.0, 0.0, 1.0) * (np.abs(xg - cx) > 14.0) * (np.abs(xg - cx) < 68.0) * free_w
    else:
        leg_band = np.clip(((axle_y - 8.0) - yg) / 18.0, 0.0, 1.0) * (np.abs(xg - cx) > 14.0) * (np.abs(xg - cx) < 82.0) * free_w

    side_sign = np.where(xg < cx, -1.0, 1.0)
    dy_leg = (3.4 if not scream else 5.2) * math.sin(freq_m * t) * side_sign * leg_band
    dx_leg = (1.4 if not scream else 2.8) * math.cos(freq_m * t) * side_sign * leg_band

    if scream:
        vib_x = 1.5 * math.sin(4.0 * t) * free_w
        dx_leg = dx_leg - vib_x

    rgba = _premul_remap(rgba, (xg + dx_leg).astype(np.float32), (yg + bob + dy_leg).astype(np.float32))

    # Traveling 3D rubber tire tread lugs on both wheels!
    rf = rgba.astype(np.float32)
    pa = rf[..., 3] > 80
    lum = rf[..., :3].mean(axis=2)
    is_tire = pa & tire_zone & (lum < 84.0)
    # Top of tire moves forward (+y in above views); bottom of tire moves backward (+y toward back in below90, +y down in below45)
    tread_dir = +1.0 if pitch_key in ("above90", "above45", "below90") else -1.0
    theta_y = (yg - cy) / 52.0
    wave = np.sin(9.5 * theta_y - tread_dir * phase_01 * 2.0 * math.pi * 2.0) * 14.5 + np.maximum(0.0, np.cos(3.0 * theta_y - tread_dir * phase_01 * 2.0 * math.pi)) * 12.0
    rf[..., :3] = np.clip(rf[..., :3] + (wave * is_tire)[..., None], 0.0, 255.0)

    if scream:
        # Warm crimson strain flush on skin + outward acoustic scream arcs!
        is_skin = pa & ((rf[..., 0] - rf[..., 2]) > 14.0) & (rf[..., 0] > 80.0)
        rf[..., 0] = np.clip(rf[..., 0] + is_skin * 22.0, 0, 255)
        rf[..., 1] = np.clip(rf[..., 1] - is_skin * 6.0, 0, 255)
        rf[..., 2] = np.clip(rf[..., 2] - is_skin * 8.0, 0, 255)

    out_im = Image.fromarray(rf.astype(np.uint8), "RGBA")

    if scream:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        hy_s = 112.0 if pitch_key == "above90" else (128.0 if pitch_key == "above45" else (112.0 if pitch_key == "below45" else 212.0))
        for ri in range(3):
            prog = (phase_01 * 2.0 + ri / 3.0) % 1.0
            rad_r = 28.0 + prog * 40.0
            a_r = int(round((1.0 - prog) * 165.0))
            if a_r > 12:
                col_r = (255, int(235 - 70 * prog), int(140 - 90 * prog), a_r)
                dr.arc([cx - rad_r, hy_s - rad_r * 0.8, cx + rad_r, hy_s + rad_r * 0.8], start=145, end=215, fill=col_r, width=2)
                dr.arc([cx - rad_r, hy_s - rad_r * 0.8, cx + rad_r, hy_s + rad_r * 0.8], start=-35, end=35, fill=col_r, width=2)
        out_im.alpha_composite(ov)

    return out_im
