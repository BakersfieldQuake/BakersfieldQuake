"""360° + Above/Below Stunt Animations Engine for BakersfieldQuake Wheelman:
  1) 🔥 Fire-Wheels Hyper-Burnout  : Wheels spin at blur speed, tires/rims glow molten cherry-orange,
                                     erupting in continuous roaring centrifugal flames, 88-MPH fire trails & sparks!
  2) 📏 Super-Long Bar & Wheels    : Steel axle bar, gleaming chrome cannon & 3D cylindrical steamroller wheels
                                     telescope super long across all 360° + Above/Below views while keeping
                                     Wheelman's human body 100% naturally proportioned!
  3) 🚀 Jetpack Hover + Rotor Spin : Twin-thruster metallic Quake jetpack strapped to his bare back blasting dual
                                     supersonic Mach-diamond rocket plumes while he floats mid-air & the bar + wheels spin!
"""
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from scipy import ndimage

import wheelman_fx as fx


def _fill_profile_hip_arc(rgba_im, d_idx):
    """Fills the circular wheel-occlusion bite on Wheelman's hip/butt in profile views (d=2, 6)
    using surrounding bare skin so his side-profile body is 100% solid when wheels move/spin!"""
    arr = np.array(rgba_im).astype(np.float32)
    H, W = arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    # Smooth anatomical hip/thigh bridge connecting upper thigh to lower back/hip in profile
    if d_idx == 2:
        # Left profile: thigh at (156, 152), hip/butt at (212, 214), arm below at y~222
        cx_h, cy_h, rx_h, ry_h, ang_h = 186.0, 184.0, 36.0, 26.0, 34.0
    else:
        cx_h, cy_h, rx_h, ry_h, ang_h = W - 186.0, 184.0, 36.0, 26.0, -34.0

    rad = math.radians(ang_h)
    ca, sa = math.cos(rad), math.sin(rad)
    du = ((xg - cx_h) * ca + (yg - cy_h) * sa) / rx_h
    dv = (-(xg - cx_h) * sa + (yg - cy_h) * ca) / ry_h
    bridge = (du * du + dv * dv) <= 1.0

    # Also scrub any dark 1-2px tire rim outline bordering the cut inside the hip zone
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    dark_rim_edge = bridge & (arr[..., 3] > 10) & (((arr[..., 0] - arr[..., 2]) < 15.0) | (lum < 78.0))
    arr[dark_rim_edge, 3] = 0.0

    need_fill = bridge & (arr[..., 3] < 210.0)
    if not np.any(need_fill):
        return rgba_im

    skin_src = (arr[..., 3] > 215) & ((arr[..., 0] - arr[..., 2]) > 16.0) & (yg > 120) & (yg < 225)
    if np.sum(skin_src) < 40:
        return rgba_im
    mean_rgb = arr[..., :3][skin_src].mean(axis=0)

    seed_rgb = np.where((arr[..., 3:4] > 215), arr[..., :3], 0.0)
    seed_w = (arr[..., 3] > 215).astype(np.float32)
    num_s = cv2.GaussianBlur(seed_rgb, (35, 35), 10.5)
    den_s = cv2.GaussianBlur(seed_w, (35, 35), 10.5)
    fill_rgb = np.where(den_s[..., None] > 1e-3, num_s / np.maximum(den_s[..., None], 1e-3), mean_rgb[None, None, :])

    comb_m = (arr[..., 3] > 140) | bridge
    dist_in = ndimage.distance_transform_edt(comb_m)
    shade = 0.88 + 0.12 * np.clip(dist_in / 12.0, 0.0, 1.0)
    new_a = np.maximum(arr[..., 3], np.clip(dist_in / 1.6, 0.0, 1.0) * 255.0 * bridge)
    blend = np.clip((235.0 - arr[..., 3]) / 185.0, 0.0, 1.0) * bridge
    arr[..., :3] = arr[..., :3] * (1.0 - blend[..., None]) + (fill_rgb * shade[..., None]) * blend[..., None]
    arr[..., 3] = np.clip(new_a, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def extract_stunt_sprite_kit(norm_views, vert_norm, parts_360):
    """Extracts razor-clean wheel-free Wheelman bodies (preserving bare arms/hands & solid profile hips!),
    chrome pipe sprites, and 10-angle shaded metallic Twin-Thruster Jetpack + Harness sprites."""
    body_only_8 = []
    jetpacks_8 = []

    for d in range(8):
        base_im, c_specs = norm_views[d]
        arr = np.array(base_im).copy()
        H, W = arr.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

        rf = arr[..., :3].astype(np.float32)
        pa = arr[..., 3] > 40
        # Warm bare human skin mask — keep ONLY largest connected human body skin components so warm tire specks vanish!
        raw_skin = pa & ((rf[..., 0] - rf[..., 2]) > 15.5) & ((rf[..., 0] - rf[..., 1]) > 7.5) & (rf[..., 0] > 82.0)
        lbl_s, num_s = ndimage.label(raw_skin)
        skin_clean = np.zeros_like(raw_skin)
        if num_s > 0:
            sizes = ndimage.sum(raw_skin, lbl_s, range(1, num_s + 1))
            for cid, sz in enumerate(sizes, start=1):
                if sz >= 95:  # Eliminates tiny warm specks on outer rubber rims!
                    skin_clean |= (lbl_s == cid)
        skin_keep = ndimage.binary_dilation(skin_clean, iterations=1)

        # In d=0 and d=4, outer tire zones beyond hands (|x - 160| > 82, y > 168) have ZERO human body pixels
        if d in (0, 4):
            skin_keep &= ~((np.abs(xg - 160.0) > 82.0) & (yg > 168.0))

        wheel_union = np.zeros((H, W), dtype=bool)
        for ws in c_specs:
            ang = math.radians(ws["ang"])
            ca, sa = math.cos(ang), math.sin(ang)
            du = ((xg - ws["cx"]) * ca + (yg - ws["cy"]) * sa) / max(ws["rx"] + 5.0, 1.0)
            dv = (-(xg - ws["cx"]) * sa + (yg - ws["cy"]) * ca) / max(ws["ry"] + 5.0, 1.0)
            wheel_union |= (du * du + dv * dv) <= 1.08

        y_ax = sum(ws["cy"] for ws in c_specs) / len(c_specs)
        outer_bar = (np.abs(yg - y_ax) < 12.0) & (np.abs(xg - 160.0) > 56.0) & (~skin_keep)
        # In profile d=2,6, completely remove the forward chrome pipe below y=195 (feet are high up at y<168!)
        prof_pipe = ((xg < 112.0) if d == 2 else ((xg > 208.0) if d == 6 else np.zeros_like(pa))) & (yg > 192.0)

        erase_m = ((wheel_union | outer_bar) & (~skin_keep)) | prof_pipe
        keep_m = (arr[..., 3] > 20) & (~erase_m)
        # Drop any tiny isolated floating islands (< 45 px) left over from tire rims
        lbl_k, num_k = ndimage.label(keep_m)
        if num_k > 1:
            ksizes = ndimage.sum(keep_m, lbl_k, range(1, num_k + 1))
            for cid, sz in enumerate(ksizes, start=1):
                if sz < 45:
                    keep_m[lbl_k == cid] = False
                    erase_m[lbl_k == cid] = True

        dist_in = ndimage.distance_transform_edt(keep_m)
        arr[..., 3] = np.where(erase_m, 0, np.minimum(arr[..., 3], np.clip(dist_in / 1.5, 0.0, 1.0) * 255.0)).astype(np.uint8)
        b_im = Image.fromarray(arr, "RGBA")
        if d in (2, 6):
            b_im = _fill_profile_hip_arc(b_im, d)
        body_only_8.append(b_im)

        # Build 3D-shaded Metallic Twin-Thruster Jetpack Sprite for angle d!
        jetpacks_8.append(_build_jetpack_sprite_dir(d))

    body_above90 = _strip_vertical_wheels(vert_norm["above90"])
    body_below90 = _strip_vertical_wheels(vert_norm["below90"])
    jetpack_above = _build_jetpack_vertical(above=True)
    jetpack_below = _build_jetpack_vertical(above=False)

    return dict(
        body_only=body_only_8,
        body_above90=body_above90,
        body_below90=body_below90,
        jetpacks=jetpacks_8,
        jetpack_above=jetpack_above,
        jetpack_below=jetpack_below,
    )


def _strip_vertical_wheels(v_im):
    arr = np.array(v_im).copy()
    H, W = arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    rf = arr[..., :3].astype(np.float32)
    # Hands/arms sit inside 88..232; anything outside 96..224 that isn't large connected arm skin is wheel/spacer!
    raw_sk = (arr[..., 3] > 50) & ((rf[..., 0] - rf[..., 2]) > 15.0) & (rf[..., 0] > 84.0) & (xg > 84.0) & (xg < W - 84.0)
    erase = ((xg < 106.0) | (xg > W - 106.0)) & (~raw_sk)
    keep = (arr[..., 3] > 20) & (~erase)
    lbl, num = ndimage.label(keep)
    if num > 1:
        sizes = ndimage.sum(keep, lbl, range(1, num + 1))
        main_id = 1 + int(np.argmax(sizes))
        arr[lbl != main_id, 3] = 0
    arr[erase, 3] = 0
    return Image.fromarray(arr, "RGBA")


def _draw_shaded_cylinder(im, x0, y0, w, h, base_rgb=(135, 145, 158), stripe_y=None):
    """Renders a 3D cylindrical brushed-steel tank with specular highlight, rivets & hazard stripe."""
    arr = np.array(im)
    H, W = arr.shape[:2]
    ix0, iy0 = max(0, int(x0)), max(0, int(y0))
    ix1, iy1 = min(W, int(x0 + w)), min(H, int(y0 + h))
    if ix1 <= ix0 or iy1 <= iy0:
        return
    yg, xg = np.mgrid[iy0:iy1, ix0:ix1].astype(np.float32)
    u = (xg - x0) / max(w, 1.0)
    v = (yg - y0) / max(h, 1.0)
    cap_r = 0.15
    in_cyl = np.ones_like(u, dtype=bool)
    top_zone = v < cap_r
    in_cyl[top_zone] = (((u[top_zone] - 0.5) / 0.5) ** 2 + ((v[top_zone] - cap_r) / cap_r) ** 2) <= 1.0
    lit = 0.40 + 0.64 * np.sin(np.clip(u, 0, 1) * math.pi)
    spec = np.exp(-((u - 0.30) / 0.11) ** 2) * 0.68
    rgb = np.zeros((iy1 - iy0, ix1 - ix0, 3), dtype=np.float32)
    for c in range(3):
        rgb[..., c] = np.clip(base_rgb[c] * lit + 195.0 * spec, 0, 255)
    if stripe_y is not None:
        band = (v > stripe_y) & (v < stripe_y + 0.16)
        stripe = ((xg + yg * 0.85) // 6) % 2 == 0
        rgb[band & stripe] = np.clip(np.array([248, 185, 28]) * lit[band & stripe, None], 0, 255)
        rgb[band & (~stripe)] = np.clip(np.array([30, 33, 40]) * lit[band & (~stripe), None], 0, 255)
    rings = ((np.abs(v - 0.22) < 0.03) | (np.abs(v - 0.78) < 0.03))
    rgb[rings] = np.clip(rgb[rings] * 0.62 + 48.0, 0, 255)

    patch = arr[iy0:iy1, ix0:ix1]
    patch[in_cyl, :3] = rgb[in_cyl].astype(np.uint8)
    patch[in_cyl, 3] = 255
    arr[iy0:iy1, ix0:ix1] = patch
    im.paste(Image.fromarray(arr, "RGBA"))


def _build_jetpack_sprite_dir(d_idx):
    """Builds a 160x160 RGBA sprite of the Twin-Thruster Quake Jetpack + Harness for viewer direction d_idx (0..7)."""
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if d_idx == 4:
        # 180° Direct Back HERO VIEW: Twin brushed-steel tanks, central glowing reactor core & twin flared nozzles!
        dr.rounded_rectangle([46, 42, 114, 98], radius=8, fill=(52, 58, 68, 255), outline=(25, 28, 34, 255), width=2)
        _draw_shaded_cylinder(im, 30, 24, 35, 84, base_rgb=(148, 158, 172), stripe_y=0.46)
        _draw_shaded_cylinder(im, 95, 24, 35, 84, base_rgb=(148, 158, 172), stripe_y=0.46)
        dr = ImageDraw.Draw(im)
        dr.ellipse([66, 54, 94, 82], fill=(24, 34, 48, 255), outline=(210, 220, 232, 255), width=2)
        dr.ellipse([71, 59, 89, 77], fill=(56, 225, 255, 255))
        dr.ellipse([75, 63, 85, 73], fill=(235, 255, 255, 255))
        for nx_c in (47, 113):
            dr.polygon([(nx_c - 10, 106), (nx_c + 10, 106), (nx_c + 16, 128), (nx_c - 16, 128)], fill=(64, 70, 80, 255), outline=(28, 32, 38, 255))
            dr.ellipse([nx_c - 14, 123, nx_c + 14, 132], fill=(255, 195, 70, 255), outline=(45, 50, 58, 255))
    elif d_idx in (3, 5):
        # 135° / 225° Back-3/4 Twin Tanks
        _draw_shaded_cylinder(im, 36, 28, 34, 80, base_rgb=(142, 152, 166), stripe_y=0.46)
        _draw_shaded_cylinder(im, 78, 24, 36, 84, base_rgb=(156, 166, 180), stripe_y=0.46)
        dr = ImageDraw.Draw(im)
        for nx_c, ny_c in ((53, 106), (96, 106)):
            dr.polygon([(nx_c - 10, ny_c), (nx_c + 10, ny_c), (nx_c + 15, ny_c + 21), (nx_c - 15, ny_c + 21)], fill=(62, 68, 78, 255), outline=(28, 30, 36, 255))
            dr.ellipse([nx_c - 13, ny_c + 17, nx_c + 13, ny_c + 25], fill=(255, 195, 70, 255))
        if d_idx == 5:
            im = ImageOps.mirror(im)
    elif d_idx in (2, 6):
        # 90° / 270° Profile Jetpack Tank mounted ON THE OUTSIDE OF HIS ARCHED BACK!
        # In d=2, his spine slopes '/' (+32° CW from vertical), with his bare back facing down-right!
        dr.rounded_rectangle([46, 44, 66, 96], radius=5, fill=(44, 48, 56, 255))  # Backplate cushion against spine
        _draw_shaded_cylinder(im, 58, 26, 38, 82, base_rgb=(152, 162, 176), stripe_y=0.45)
        dr = ImageDraw.Draw(im)
        dr.polygon([(66, 106), (88, 106), (95, 128), (59, 128)], fill=(62, 68, 78, 255), outline=(26, 30, 36, 255))
        dr.ellipse([61, 123, 93, 132], fill=(255, 195, 70, 255))
        im = im.rotate(-30, resample=Image.BICUBIC, expand=False)
        if d_idx == 6:
            im = ImageOps.mirror(im)
    else:
        # d=0, 1, 7 (Front & Front-3/4): Twin tank domes + side booster nozzles peeking wide behind shoulders!
        _draw_shaded_cylinder(im, 20, 24, 32, 82, base_rgb=(138, 148, 162), stripe_y=0.48)
        _draw_shaded_cylinder(im, 108, 24, 32, 82, base_rgb=(138, 148, 162), stripe_y=0.48)
        dr = ImageDraw.Draw(im)
        for nx_c in (36, 124):
            dr.polygon([(nx_c - 9, 104), (nx_c + 9, 104), (nx_c + 14, 124), (nx_c - 14, 124)], fill=(58, 64, 74, 255), outline=(26, 30, 36, 255))
            dr.ellipse([nx_c - 12, 120, nx_c + 12, 128], fill=(255, 195, 70, 255))
        if d_idx == 1:
            im = im.rotate(-10, resample=Image.BICUBIC)
        elif d_idx == 7:
            im = im.rotate(+10, resample=Image.BICUBIC)
    return im


def _build_jetpack_vertical(above=True):
    im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if above:
        for cx in (44, 96):
            dr.ellipse([cx - 19, 46, cx + 19, 84], fill=(148, 158, 172, 255), outline=(42, 48, 58, 255), width=3)
            dr.ellipse([cx - 9, 56, cx + 9, 74], fill=(225, 235, 245, 255))
        dr.rectangle([56, 56, 84, 74], fill=(56, 215, 250, 255), outline=(35, 42, 52, 255), width=2)
    else:
        for cx in (44, 96):
            dr.ellipse([cx - 21, 45, cx + 21, 87], fill=(55, 60, 70, 255), outline=(25, 28, 34, 255), width=3)
            dr.ellipse([cx - 14, 52, cx + 14, 80], fill=(255, 150, 25, 255))
            dr.ellipse([cx - 8, 58, cx + 8, 74], fill=(255, 252, 225, 255))
    return im


# ---------------------------------------------------------------------------
# 1) STUNT 1: 🔥 WHEELS SPIN SO FAST THEY CATCH FIRE (360° + Above/Below)
# ---------------------------------------------------------------------------

def _draw_continuous_wheel_inferno(stage, wx, wy, rx, ry, ang_deg, phase_01, wake_dx, fire_p, seed=1):
    """Wraps an entire spinning tire in a continuous roaring sheet of centrifugal flames, molten cherry-orange
    rim heat, upward-licking fire tongues, and high-velocity tangential friction sparks!"""
    W_s, H_s = stage.size
    rad_a = math.radians(ang_deg)
    ca, sa = math.cos(rad_a), math.sin(rad_a)
    rng = np.random.default_rng(seed)

    # 1) Soft roaring outer flame corona + upward-streaming fire sheet around the entire tire ellipse
    glow = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(glow)
    n_tongues = 22
    for i in range(n_tongues):
        th = (i / float(n_tongues)) * 2.0 * math.pi + phase_01 * 2.0 * math.pi * 2.0
        px = wx + (rx * math.cos(th)) * ca - (ry * math.sin(th)) * sa
        py = wy + (rx * math.cos(th)) * sa + (ry * math.sin(th)) * ca
        flick = 0.65 + 0.35 * math.sin(th * 3.0 - phase_01 * 25.0 + i)
        # Flames lick strongly UPWARD (-Y) and slightly along wake_dx!
        tip_x = px + math.cos(th) * 12.0 + wake_dx * (0.18 + 0.20 * flick)
        tip_y = py + math.sin(th) * 8.0 - (24.0 + 34.0 * flick)
        w_b = 9.5 + 5.0 * flick
        gdr.polygon(
            [(px - w_b, py + 4), (px + w_b, py + 4), (tip_x, tip_y)],
            fill=(255, int(75 + 75 * flick), 12, 205),
        )
        gdr.polygon(
            [(px - w_b * 0.52, py + 2), (px + w_b * 0.52, py + 2), (tip_x * 0.65 + px * 0.35, tip_y * 0.68 + py * 0.32)],
            fill=(255, 232, 115, 235),
        )

    # Molten incandescent tire perimeter halo
    pts_outer = []
    for i in range(36):
        th = (i / 36.0) * 2.0 * math.pi
        pts_outer.append((
            wx + ((rx + 3.0) * math.cos(th)) * ca - ((ry + 3.0) * math.sin(th)) * sa,
            wy + ((rx + 3.0) * math.cos(th)) * sa + ((ry + 3.0) * math.sin(th)) * ca,
        ))
    gdr.line(pts_outer + [pts_outer[0]], fill=(255, 95, 16, 210), width=10)
    gdr.line(pts_outer + [pts_outer[0]], fill=(255, 238, 135, 240), width=4)
    stage.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=2.4)))

    # Blend 2 large rising photographic pyrotechnic crests off the top/wake of the burning tire
    if fire_p is not None:
        for k in range(2):
            pr = (phase_01 * 2.0 + k * 0.5) % 1.0
            fx._blit_evolving_vfx_fireball(
                stage, fire_p,
                wx + wake_dx * (0.18 + 0.45 * pr),
                wy - ry * 0.55 - pr * 38.0,
                0.22 + pr * 0.48,
                max_diam=max(76.0, rx * 1.45 + 48.0),
                rot_deg=phase_01 * 360.0 + k * 140.0,
            )

    # Crisp white-hot tangential friction sparks spraying off the spinning tire!
    spk = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(spk)
    for _ in range(18):
        u_s = rng.uniform(0.0, 1.0)
        th_s = rng.uniform(-0.8, 2.4)
        sx0 = wx + (rx * math.cos(th_s)) * ca + wake_dx * u_s * 0.95 + rng.uniform(-8, 8)
        sy0 = wy + (ry * math.sin(th_s)) * 0.65 - u_s * rng.uniform(14.0, 74.0)
        dx_s = wake_dx * 0.26 + rng.uniform(-10, 10)
        dy_s = -rng.uniform(7.0, 16.0)
        al = int(250 * (1.0 - 0.75 * u_s))
        sdr.line([(sx0, sy0), (sx0 + dx_s, sy0 + dy_s)], fill=(255, 180, 55, al), width=3)
        sdr.line([(sx0, sy0), (sx0 + dx_s * 0.6, sy0 + dy_s * 0.6)], fill=(255, 252, 210, al), width=1)
    stage.alpha_composite(spk)


def render_fire_wheels_frame(base_im, c_specs, d_idx, phase_01, animate_fn, vfx_plates, stage_wh=(480, 340), ground_y=308):
    """Renders 360° Hyper-Burnout Fire-Wheels: 5x blur-speed wheel spin, molten glowing rubber tires,
    continuous roaring centrifugal flames, 88-MPH twin ground fire tracks & tangential spark showers!"""
    W_s, H_s = stage_wh
    cx_s = W_s * 0.5
    ox = int(round(cx_s - base_im.width * 0.5))
    oy = int(round(ground_y - 288))

    # Average 4 micro-stepped wheel phases for high-speed radial motion blur!
    acc = None
    for sub in (-0.09, -0.03, +0.03, +0.09):
        ph_fast = (phase_01 * 5.0 + sub) % 1.0
        fr_sub = np.array(animate_fn(base_im, d_idx, ph_fast, c_specs, mode="roll"), dtype=np.float32)
        acc = fr_sub if acc is None else (acc + fr_sub)
    wm_arr = (acc / 4.0).astype(np.uint8)
    wm_im = fx.apply_scream_face_and_body(Image.fromarray(wm_arr, "RGBA"), d_idx, phase_01, c_specs, intensity=0.92, sound_waves=False)

    # Heat the rubber tires to incandescent cherry-orange + warm under-lighting across Wheelman's body!
    wa = np.array(wm_im, dtype=np.float32)
    hy, hx = np.mgrid[0:wa.shape[0], 0:wa.shape[1]].astype(np.float32)
    pa = wa[..., 3] > 60
    lum = wa[..., :3].mean(axis=2)
    for ws in c_specs:
        ang = math.radians(ws["ang"])
        ca, sa = math.cos(ang), math.sin(ang)
        du = ((hx - ws["cx"]) * ca + (hy - ws["cy"]) * sa) / max(ws["rx"], 1.0)
        dv = (-(hx - ws["cx"]) * sa + (hy - ws["cy"]) * ca) / max(ws["ry"], 1.0)
        r_e = np.sqrt(du * du + dv * dv)
        tire_heat = pa & (r_e <= 1.05) & (r_e >= 0.52) & (lum < 95.0)
        rim_heat = np.clip((r_e - 0.55) / 0.45, 0.0, 1.0) * tire_heat
        wa[..., 0] = np.clip(wa[..., 0] + rim_heat * 195.0, 0, 255)
        wa[..., 1] = np.clip(wa[..., 1] + rim_heat * 82.0, 0, 255)
        wa[..., 2] = np.clip(wa[..., 2] + rim_heat * 14.0, 0, 255)

    under_lit = np.clip((hy - 130.0) / 145.0, 0.0, 1.0) * pa
    wa[..., 0] = np.clip(wa[..., 0] + under_lit * 52.0, 0, 255)
    wa[..., 1] = np.clip(wa[..., 1] + under_lit * 20.0, 0, 255)
    wm_im = Image.fromarray(wa.astype(np.uint8), "RGBA")

    stage = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    fire_p = vfx_plates.get("fire")
    wake_dx = 78.0 if d_idx in (1, 2, 3) else (-78.0 if d_idx in (5, 6, 7) else 0.0)

    # 1) Twin 88-MPH Scorching Ground Flame Tracks behind/under each spinning tire!
    flr = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    fdr = ImageDraw.Draw(flr)
    for ws in c_specs:
        wx = ox + ws["cx"]
        wy = ground_y + 1.0
        xL_t = min(wx - 44, wx + wake_dx * 1.25 - 30)
        xR_t = max(wx + 44, wx + wake_dx * 1.25 + 30)
        fdr.ellipse([xL_t, wy - 10, xR_t, wy + 10], fill=(255, 80, 12, 205))
        fdr.ellipse([xL_t + 14, wy - 5, xR_t - 14, wy + 5], fill=(255, 238, 130, 240))
    stage.alpha_composite(flr.filter(ImageFilter.GaussianBlur(radius=4.0)))

    # 2) Composite vibrating hyper-spinning Wheelman
    vib_x = int(round(math.sin(phase_01 * math.pi * 8.0) * 1.8))
    vib_y = int(round(math.cos(phase_01 * math.pi * 12.0) * 1.4))
    stage.alpha_composite(wm_im, (ox + vib_x, oy + vib_y))

    # 3) Continuous Roaring Centrifugal Tire Inferno around every wheel!
    for wi, ws in enumerate(c_specs):
        _draw_continuous_wheel_inferno(
            stage,
            ox + ws["cx"] + vib_x,
            oy + ws["cy"] + vib_y,
            ws["rx"], ws["ry"], ws["ang"],
            phase_01, wake_dx, fire_p,
            seed=4400 + d_idx * 30 + wi * 13 + int(phase_01 * 100),
        )

    return stage


# ---------------------------------------------------------------------------
# 2) STUNT 2: 📏 METAL BAR AND WHEELS GET SUPER LONG (360° + Above/Below)
# ---------------------------------------------------------------------------

def _draw_extruded_long_wheel(stage, w_im, p_inner, p_outer, rot_deg, scale_r=1.0, n_slices=7, ground_y=308):
    """Extrudes an authentic photographic wheel along the 3D axle from p_inner to p_outer into a
    SUPER-LONG 3D cylindrical steamroller tire! Works cleanly across all 360° angles without hiding Wheelman!"""
    # Order slices strictly back-to-front by camera depth p[2]
    t_vals = np.linspace(0.0, 1.0, n_slices)
    pts = []
    for tv in t_vals:
        sx = p_inner[0] + (p_outer[0] - p_inner[0]) * tv
        sy = p_inner[1] + (p_outer[1] - p_inner[1]) * tv
        dp = p_inner[2] + (p_outer[2] - p_inner[2]) * tv
        pr = p_inner[3] + (p_outer[3] - p_inner[3]) * tv
        pts.append((dp, tv, sx, sy, pr))
    pts.sort(key=lambda item: item[0])

    # Darkened ribbed rubber barrel body slice for interior cylinder rings so the drum reads as solid 3D rubber!
    w_arr = np.array(w_im, dtype=np.float32)
    barrel_arr = w_arr.copy()
    barrel_arr[..., :3] *= 0.62  # Deep rubber cylinder shadow between end caps
    barrel_im = Image.fromarray(barrel_arr.astype(np.uint8), "RGBA")

    for idx, (dp, tv, sx, sy, pr) in enumerate(pts):
        is_cap = (tv < 0.05) or (tv > 0.95) or (idx == len(pts) - 1)
        src = w_im if is_cap else barrel_im
        fx._paste_rotated_rgba(stage, src, sx, sy, rot_deg, sx=scale_r * pr, sy=scale_r * pr, max_bottom_y=ground_y + 14)


def render_super_long_bar_frame(d_idx, phase_01, stunt_kit, parts_360, stage_wh=(480, 340), ground_y=308):
    """Telescopes BOTH the 3D steel axle bar + gleaming forward chrome cannon AND extrudes both wheels into
    super-long 3D cylindrical steamroller drums across all 360° angles while keeping Wheelman un-squashed!"""
    W_s, H_s = stage_wh
    cx_s = W_s * 0.5
    s_wave = 0.5 - 0.5 * math.cos(2.0 * math.pi * phase_01)  # 0..1..0

    th = math.radians(d_idx * 45.0)
    ct, st = math.cos(th), math.sin(th)

    w_im = parts_360["wheels"][d_idx]
    # Normalize base wheel radius so profile/oblique wheels match natural 52px radius (never dwarfing Wheelman!)
    base_sc = min(1.02, 106.0 / max(w_im.height, 1))
    axle_y_3d = 52.0

    def proj3d(x, y, z):
        u = x * ct - z * st
        depth = x * st + z * ct
        persp = max(0.76, min(1.26, 860.0 / max(380.0, 860.0 - depth)))
        return cx_s + u * persp, (ground_y - 4.0 + depth * 0.08) - y * persp, depth, persp

    stage = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))

    # Steel axle inner hub starts at +-44 (at hands) -> stretches out to +-136, plus 56px-wide long roller wheel = +-192 (100% inside 480px!)
    inner_ax = 44.0 + 88.0 * s_wave         # 44 .. 132
    wheel_len = 14.0 + 48.0 * s_wave        # Wheel drum length grows 4.4x longer along axle!
    outer_ax = inner_ax + wheel_len         # 58 .. 180
    cyl_len = 42.0 + 132.0 * s_wave         # Forward chrome cannon stretches 4.1x super long (up to 174px)!

    # Floor shadow spanning the entire super-long axle & roller drums!
    pL_out = proj3d(-outer_ax, 0.0, 0.0)
    pR_out = proj3d(+outer_ax, 0.0, 0.0)
    sh = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(sh)
    sdr.line([(pL_out[0], ground_y + 2), (pR_out[0], ground_y + 2)], fill=(10, 10, 14, 150), width=16)
    stage.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=4.0)))

    pC = proj3d(0.0, axle_y_3d, 0.0)
    pHandL = proj3d(-38.0, axle_y_3d, 0.0)
    pHandR = proj3d(+38.0, axle_y_3d, 0.0)
    pInL = proj3d(-inner_ax, axle_y_3d, 0.0)
    pOutL = proj3d(-outer_ax, axle_y_3d, 0.0)
    pInR = proj3d(+inner_ax, axle_y_3d, 0.0)
    pOutR = proj3d(+outer_ax, axle_y_3d, 0.0)
    pCylBase = proj3d(0.0, axle_y_3d - 2.0, +16.0)
    pCylTip = proj3d(0.0, axle_y_3d - 8.0, +cyl_len)

    body_im = stunt_kit["body_only"][d_idx]
    bx_pos = int(round(pC[0] - body_im.width * 0.5))
    by_pos = int(round(pC[1] - 234.0))

    def draw_telescoping_rod(p_start, p_end, thick=10, chrome=False):
        dx = p_end[0] - p_start[0]
        dy = p_end[1] - p_start[1]
        seg_l = math.hypot(dx, dy)
        if seg_l < 3.0:
            return
        rl = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        rdr = ImageDraw.Draw(rl)
        x0, y0, x1, y1 = p_start[0], p_start[1], p_end[0], p_end[1]
        # Stepped multi-stage hydraulic telescope tubes (thick outer sleeve -> medium mid tube -> gleaming inner rod!)
        xm1, ym1 = x0 + dx * 0.42, y0 + dy * 0.42
        xm2, ym2 = x0 + dx * 0.74, y0 + dy * 0.74
        for (xa, ya, xb, yb, w_t) in ((x0, y0, xm1, ym1, thick + 4), (xm1, ym1, xm2, ym2, thick + 1), (xm2, ym2, x1, y1, max(5, thick - 2))):
            rdr.line([(xa, ya), (xb, yb)], fill=(36, 40, 48, 255), width=w_t + 3)
            rdr.line([(xa, ya), (xb, yb)], fill=(176, 188, 204, 255) if chrome else (138, 150, 166, 255), width=w_t)
            rdr.line([(xa, ya - w_t * 0.22), (xb, yb - w_t * 0.22)], fill=(245, 250, 255, 255), width=max(2, w_t // 3))
        for mx, my, col in ((xm1, ym1, (248, 188, 30, 255)), (xm2, ym2, (220, 230, 242, 255))):
            r_c = thick * 0.58 + 2
            rdr.ellipse([mx - r_c * 0.65, my - r_c, mx + r_c * 0.65, my + r_c], fill=col, outline=(32, 36, 44, 255))
        stage.alpha_composite(rl)

    def draw_super_long_chrome_cannon():
        draw_telescoping_rod(pCylBase, pCylTip, thick=18, chrome=True)
        fx._paste_rotated_rgba(stage, parts_360["shrap_cap"], pCylTip[0], pCylTip[1], phase_01 * 360.0, sx=1.18 * pCylTip[3], sy=1.18 * pCylTip[3])

    rot_w = (-1.0 if d_idx in (1, 2, 3) else 1.0) * phase_01 * 360.0 if d_idx in (2, 6) else 0.0
    sides = [
        ("L", pHandL, pInL, pOutL, 0.5 * (pInL[2] + pOutL[2])),
        ("R", pHandR, pInR, pOutR, 0.5 * (pInR[2] + pOutR[2])),
    ]
    sides.sort(key=lambda item: item[4])  # Far side first, Near side last!

    # 1) Far Super-Long Wheel Drum & Far Telescoping Steel Axle (extending from hand outward — never drawn over bare butt!)
    _, f_hand, f_in, f_out, _ = sides[0]
    _draw_extruded_long_wheel(stage, w_im, f_in, f_out, rot_w, scale_r=base_sc, n_slices=12, ground_y=ground_y)
    draw_telescoping_rod(f_hand, f_out, thick=9, chrome=False)

    # 2) Rear-pointing Super-Long Chrome Cannon (when viewed from back d=3, 4, 5 — occluded behind his torso!)
    if d_idx in (3, 4, 5):
        draw_super_long_chrome_cannon()

    # 3) Central Un-Squashed Wheelman Body!
    stage.alpha_composite(body_im, (bx_pos, by_pos))

    # 4) Front/Profile Super-Long Chrome Cannon (d=0, 1, 2, 6, 7 — shoots way out in front!)
    if d_idx not in (3, 4, 5):
        draw_super_long_chrome_cannon()

    # 5) Near Telescoping Steel Axle & Near Super-Long Cylindrical Wheel Drum!
    _, n_hand, n_in, n_out, _ = sides[1]
    draw_telescoping_rod(n_hand, n_out, thick=10, chrome=False)
    _draw_extruded_long_wheel(stage, w_im, n_in, n_out, rot_w, scale_r=base_sc, n_slices=12, ground_y=ground_y)

    return stage


# ---------------------------------------------------------------------------
# 3) STUNT 3: 🚀 FLOATING ON A JETPACK WHILE BAR & WHEELS SPIN (360° + Pitch)
# ---------------------------------------------------------------------------

def render_jetpack_hover_frame(d_idx, phase_01, stunt_kit, parts_360, vfx_plates, stage_wh=(480, 340), ground_y=308):
    """Renders Wheelman floating high in mid-air on a roaring Twin-Thruster Jetpack strapped to his bare back
    while BOTH the steel bar assembly AND both wheels spin wildly underneath him across all 360° angles!"""
    W_s, H_s = stage_wh
    cx_s = W_s * 0.5
    t = 2.0 * math.pi * phase_01
    hover_lift = 70.0 + 15.0 * math.sin(t)
    sway_x = 12.0 * math.cos(t)

    stage = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    fire_p = vfx_plates.get("fire")

    # 1) Shrinking Ground Shadow + Orange Rocket Ground-Wash + Expanding Smoke Rings on floor below!
    sh_layer = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(sh_layer)
    sh_rx = 54.0 - 0.14 * hover_lift
    sdr.ellipse([cx_s + sway_x - sh_rx, ground_y - 8, cx_s + sway_x + sh_rx, ground_y + 8], fill=(12, 10, 12, 155))
    sdr.ellipse([cx_s + sway_x - 46, ground_y - 6, cx_s + sway_x + 46, ground_y + 6], fill=(255, 135, 28, 135))
    for si in range(4):
        sp_u = (phase_01 * 2.0 + si * 0.25) % 1.0
        sx_sm = cx_s + sway_x + (si - 1.5) * 38.0 * sp_u
        sy_sm = ground_y - 5.0 - (1.0 - sp_u) * 24.0
        rad_sm = 14.0 + sp_u * 26.0
        sdr.ellipse([sx_sm - rad_sm, sy_sm - rad_sm * 0.42, sx_sm + rad_sm, sy_sm + rad_sm * 0.42], fill=(195, 190, 188, int(135 * (1.0 - sp_u))))
    stage.alpha_composite(sh_layer.filter(ImageFilter.GaussianBlur(radius=3.2)))

    body_im = stunt_kit["body_only"][d_idx]
    jp_im = stunt_kit["jetpacks"][d_idx]
    bx = int(round(cx_s + sway_x - body_im.width * 0.5))
    by = int(round(ground_y - 288 - hover_lift))

    # Calibrated 360° Jetpack mounts — sits flush on his bare back in EVERY view (including arched d=2,6 profiles!)
    jp_offsets = {
        0: (80, 56),    # Twin domes & side nozzles peeking wide behind shoulders
        1: (146, 54),   # Behind angled upper back (Front-Left 45°)
        2: (205, 88),   # Flush ON THE OUTSIDE of his arched bare back in Left Profile!
        3: (122, 50),   # Back-Left 135°
        4: (80, 66),    # Centered hero Twin-Thruster Backpack on bare back!
        5: (38, 50),    # Back-Right 225°
        6: (-45, 88),   # Flush ON THE OUTSIDE of his arched bare back in Right Profile!
        7: (14, 54),    # Behind angled upper back (Front-Right 315°)
    }
    jox, joy = jp_offsets[d_idx]

    def draw_supersonic_thruster_flames():
        fl_im = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        fdr = ImageDraw.Draw(fl_im)
        if d_idx == 2:
            # Tilted +30° along his arched back: nozzle sits at bottom-left of angled tank, shooting down-left!
            nozzles = [(bx + jox + 60, by + joy + 114, -18.0)]
        elif d_idx == 6:
            nozzles = [(bx + jox + 100, by + joy + 114, +18.0)]
        elif d_idx in (0, 1, 7):
            # Longer twin side plumes so supersonic Mach diamonds blast visibly below his hips!
            nozzles = [(bx + jox + 36, by + joy + 122, 0.0), (bx + jox + 124, by + joy + 122, 0.0)]
        else:
            nozzles = [(bx + jox + 48, by + joy + 124, 0.0), (bx + jox + 112, by + joy + 124, 0.0)]

        for ni, (nx_p, ny_p, tilt_deg) in enumerate(nozzles):
            flen = (108.0 if d_idx in (0, 1, 7) else 78.0) + 22.0 * math.sin(t * 4.0 + ni * 1.7)
            rad_t = math.radians(tilt_deg)
            tx_end = nx_p + math.sin(rad_t) * flen
            ty_end = ny_p + math.cos(rad_t) * flen
            fdr.polygon([(nx_p - 14, ny_p), (nx_p + 14, ny_p), (tx_end, ty_end)], fill=(255, 110, 18, 230))
            fdr.polygon([(nx_p - 8, ny_p), (nx_p + 8, ny_p), (nx_p + math.sin(rad_t) * flen * 0.72, ny_p + math.cos(rad_t) * flen * 0.72)], fill=(155, 242, 255, 252))
            for md in range(4):
                frac_d = 0.16 + md * 0.16
                mx_d = nx_p + math.sin(rad_t) * flen * frac_d
                my_d = ny_p + math.cos(rad_t) * flen * frac_d
                fdr.polygon([(mx_d, my_d - 5), (mx_d + 5, my_d), (mx_d, my_d + 5), (mx_d - 5, my_d)], fill=(255, 255, 255, 255))
            if fire_p is not None:
                fx._blit_evolving_vfx_fireball(stage, fire_p, nx_p + math.sin(rad_t) * flen * 0.55, ny_p + math.cos(rad_t) * flen * 0.55, 0.16 + 0.14 * ((ni + int(phase_01 * 12)) % 2), max_diam=68.0, rot_deg=180)
        stage.alpha_composite(fl_im.filter(ImageFilter.GaussianBlur(radius=1.3)))

    def draw_spinning_rotor_bar_and_wheels():
        """Spins the ENTIRE steel axle bar + chrome cylinder + blur-spinning wheels in 3D mid-air!"""
        th_rotor = d_idx * 45.0 + phase_01 * 360.0 * 2.0  # 2 full 360° revolutions per loop!
        rad_r = math.radians(th_rotor)
        ct_r, st_r = math.cos(rad_r), math.sin(rad_r)
        rot_d = int(round((th_rotor % 360.0) / 45.0)) % 8
        hub_x = cx_s + sway_x + (-18.0 if d_idx == 2 else (18.0 if d_idx == 6 else 0.0))
        hub_y = by + 236.0

        w_pts = [
            (-76.0 * ct_r, -76.0 * st_r),
            (+76.0 * ct_r, +76.0 * st_r),
        ]
        w_pts.sort(key=lambda item: item[1])

        # Glowing silver-cyan high-speed rotor motion-blur disc!
        disc = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
        ddr = ImageDraw.Draw(disc)
        ddr.ellipse([hub_x - 98, hub_y - 22, hub_x + 98, hub_y + 22], outline=(195, 235, 255, 130), width=6)
        ddr.ellipse([hub_x - 76, hub_y - 15, hub_x + 76, hub_y + 15], outline=(255, 255, 255, 90), width=2)
        stage.alpha_composite(disc.filter(ImageFilter.GaussianBlur(radius=1.4)))

        w_sp = parts_360["wheels"][rot_d]
        bar_sp = parts_360["bars"][rot_d]
        w_sc = min(0.95, 102.0 / max(w_sp.height, 1))
        w_self_spin = phase_01 * 360.0 * 4.0

        fx._paste_rotated_rgba(stage, w_sp, hub_x + w_pts[0][0], hub_y + w_pts[0][1] * 0.16, w_self_spin if rot_d in (2, 6) else 0.0, sx=w_sc * 0.90, sy=w_sc * 0.90)
        fx._paste_rotated_rgba(stage, bar_sp, hub_x, hub_y, math.sin(rad_r) * 10.0)
        fx._paste_rotated_rgba(stage, w_sp, hub_x + w_pts[1][0], hub_y + w_pts[1][1] * 0.16, w_self_spin if rot_d in (2, 6) else 0.0, sx=w_sc * 1.04, sy=w_sc * 1.04)

    jetpack_in_front = d_idx in (3, 4, 5)
    if not jetpack_in_front:
        draw_supersonic_thruster_flames()
        stage.alpha_composite(jp_im, (bx + jox, by + joy))

    if d_idx in (3, 4, 5):
        draw_spinning_rotor_bar_and_wheels()

    stage.alpha_composite(body_im, (bx, by))
    # Tactical shoulder/back harness straps so the jetpack looks physically strapped to his torso!
    st_ov = Image.new("RGBA", (W_s, H_s), (0, 0, 0, 0))
    st_dr = ImageDraw.Draw(st_ov)
    if d_idx == 0:
        for sx_st in (bx + 128, bx + 174):
            st_dr.line([(sx_st, by + 124), (sx_st, by + 166)], fill=(40, 44, 52, 235), width=6)
            st_dr.rectangle([sx_st - 4, by + 142, sx_st + 4, by + 150], fill=(210, 218, 228, 255))
    elif d_idx == 2:
        st_dr.arc([bx + 224, by + 132, bx + 266, by + 176], start=110, end=295, fill=(40, 44, 52, 230), width=5)
    elif d_idx == 6:
        st_dr.arc([bx + 54, by + 132, bx + 96, by + 176], start=-115, end=70, fill=(40, 44, 52, 230), width=5)
    stage.alpha_composite(st_ov)

    if d_idx not in (3, 4, 5):
        draw_spinning_rotor_bar_and_wheels()

    if jetpack_in_front:
        draw_supersonic_thruster_flames()
        stage.alpha_composite(jp_im, (bx + jox, by + joy))

    return stage
