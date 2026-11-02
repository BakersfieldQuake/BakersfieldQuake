"""Precision 3D Mechanical Rig Geometry & Texture Atlas Builders for BakersfieldQuake:
  1. progs/mm_suit_rider.md3  ('vid1_suit' - Screaming Suit Rider on Reclined Stainless Bucket-Seat Rig)
  2. progs/mm_squat_rider.md3 ('vid2_squat' - Squatting Plaid-Shirt Rider on Sparking Handlebar Chariot)

Coordinate convention (Quake MD3):
  +X = forward, +Y = left (port), +Z = up, z = 0 at tire ground contact.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mmw_geometry as mg


# --------------------------------------------------------------------------- Exact Blueprint Specs (Quake Units)
SUIT_SPEC = dict(
    kind="suit",
    wheel_r=10.55,
    wheel_w=5.20,
    rim_r=6.42,
    track_y=18.55,       # wheel center Y = +-18.55
    axle_r=0.58,
    shaft_r=1.35,
    # Central shaft axis: passes through (0.0, 0.0, 10.55), pitched nose-down 24.0 deg
    shaft_p0=(-5.20, 0.0, 12.86),
    shaft_p_collar=(0.0, 0.0, 10.55),
    shaft_p_tip=(14.40, 0.0, 4.15),
    seat_y_half=7.35,
    seat_z_pan=13.95,
    seat_z_top=25.60,
)

SQUAT_SPEC = dict(
    kind="squat",
    wheel_r=12.05,
    wheel_w=6.00,
    rim_r=7.28,
    bore_r=1.28,
    lug_r=2.26,
    track_y=20.75,       # wheel center Y = +-20.75
    axle_r=0.74,
    shaft_r=1.76,
    # Central shaft axis: rear domed cap under seat (-10.8, 0, 17.65) -> (0, 0, 13.85) -> tip (+24.2, 0, 6.65)
    shaft_p0=(-10.80, 0.0, 17.65),
    shaft_p_collar=(0.0, 0.0, 13.85),
    shaft_p_tip=(24.20, 0.0, 6.65),
    handle_y=12.75,
    handle_z_top=18.75,
)


# Atlas UV rectangles (u0, v0, u1, v1) in normalized [0..1] top-left origin space
UV_WHEEL_FACE = (0.010, 0.010, 0.490, 0.490)    # 512x512 top-left quadrant (polar mapped dish + sidewall)
UV_TIRE_TREAD = (0.510, 0.015, 0.990, 0.485)    # 5-ribbed pneumatic tread band (v along profile)
UV_CHROME_SHAFT = (0.015, 0.515, 0.635, 0.745)  # gleaming studio-reflected brushed stainless cylinder
UV_SEAT_STEEL = (0.015, 0.760, 0.635, 0.985)    # stamped stainless bucket seat / clamp metal
UV_DARK_METAL = (0.655, 0.515, 0.985, 0.735)    # zinc hardware, bolts, dark bore
UV_BRASS_ACC = (0.655, 0.755, 0.815, 0.985)     # yellow-zinc cotter pin / hot tip tint
UV_VALVE_BLK = (0.825, 0.755, 0.985, 0.985)     # black rubber valve stem / grip sleeve


def dp_calibrate(img_rgb, brightness=0.60, contrast=1.10):
    """Calibrates sRGB texture for DarkPlaces lightingDiffuse overbright headroom."""
    out = ImageEnhance.Contrast(img_rgb).enhance(contrast)
    out = ImageEnhance.Brightness(out).enhance(brightness)
    return out


# --------------------------------------------------------------------------- Procedural 1024x1024 Rig Textures
def _paint_common_tread_and_chrome(arr, is_squat=False):
    H, W, _ = arr.shape
    # 1. Top-Right Quadrant (512..1024, 0..512): 5-Ribbed Black Pneumatic Tire Tread
    # Note: v runs 0.015 -> 0.485 across tire cross-section width!
    y0, y1 = int(0.010 * H), int(0.495 * H)
    x0, x1 = int(0.505 * W), int(0.995 * W)
    yy = np.linspace(0.0, 1.0, y1 - y0)[:, None]
    xx = np.linspace(0.0, 1.0, x1 - x0)[None, :]
    rng = np.random.default_rng(42 if not is_squat else 108)
    grain = rng.normal(0.0, 3.2, (y1 - y0, x1 - x0))

    # Base rubber tone across width (rounded shoulder falloff + 4 deep circumferential grooves -> 5 ribs!)
    shoulder = 1.0 - 0.30 * ((2.0 * yy - 1.0) ** 4)
    base_val = 38.0 * shoulder + grain
    # 4 grooves at t = 0.24, 0.39, 0.61, 0.76 (within tread crown 0.14..0.86)
    groove_centers = [0.25, 0.41, 0.59, 0.75]
    for gc in groove_centers:
        d = np.abs(yy - gc)
        groove = np.exp(-((d / 0.020) ** 2))
        edge_hi = np.exp(-(((d - 0.028) / 0.010) ** 2))
        base_val = base_val * (1.0 - 0.72 * groove) + 11.0 * edge_hi

    # Subtle circumferential micro-ribbing & rubber sheen
    sipes = 2.2 * np.sin(xx * 2.0 * math.pi * 48.0) * ((yy > 0.16) & (yy < 0.84))
    tread_c = np.clip(base_val + sipes, 8.0, 74.0)
    arr[y0:y1, x0:x1, 0] = tread_c
    arr[y0:y1, x0:x1, 1] = tread_c * 1.01
    arr[y0:y1, x0:x1, 2] = tread_c * 1.04

    # 2. Chrome / Brushed 304 Stainless Cylinder Swatch (u: 0.01..0.64, v: 0.51..0.75)
    # Authentic high-contrast studio cyclorama chrome reflection bands (dark horizon + bright softbox!)
    cy0, cy1 = int(0.510 * H), int(0.750 * H)
    cx0, cx1 = int(0.010 * W), int(0.645 * W)
    th = np.linspace(0.0, 2.0 * math.pi, cx1 - cx0)[None, :]
    lv = np.linspace(0.0, 1.0, cy1 - cy0)[:, None]
    env = (
        148.0
        + 62.0 * np.cos(th - 1.15)
        + 38.0 * np.cos(2.0 * th + 0.55)
        - 82.0 * np.exp(-(((th - 2.65) / 0.34) ** 2))
        - 68.0 * np.exp(-(((th - 4.55) / 0.38) ** 2))
        + 76.0 * np.exp(-(((th - 1.35) / 0.22) ** 2))
        + 55.0 * np.exp(-(((th - 3.55) / 0.20) ** 2))
    )
    brush = rng.normal(0.0, 2.2, (1, cx1 - cx0)) + rng.normal(0.0, 1.2, (cy1 - cy0, 1))
    seam = 1.0 - 0.62 * np.exp(-(((lv - 0.28) / 0.010) ** 2))
    c_r = np.clip((env * 0.97 + brush) * seam, 28.0, 252.0)
    c_g = np.clip((env * 0.99 + brush) * seam, 30.0, 253.0)
    c_b = np.clip((env * 1.03 + brush) * seam, 34.0, 255.0)
    if is_squat:
        heat = np.clip((lv - 0.86) / 0.14, 0.0, 1.0) ** 1.6
        c_r = np.clip(c_r + 28.0 * heat, 28.0, 255.0)
        c_g = np.clip(c_g - 4.0 * heat, 28.0, 250.0)
        c_b = np.clip(c_b - 26.0 * heat, 28.0, 245.0)
    arr[cy0:cy1, cx0:cx1, 0] = c_r
    arr[cy0:cy1, cx0:cx1, 1] = c_g
    arr[cy0:cy1, cx0:cx1, 2] = c_b

    # 3. Stamped Polished Stainless Seat / Clamp Swatch (u: 0.01..0.64, v: 0.755..0.99)
    sy0, sy1 = int(0.755 * H), int(0.992 * H)
    sx0, sx1 = int(0.010 * W), int(0.645 * W)
    su = np.linspace(0.0, 1.0, sx1 - sx0)[None, :]
    sv = np.linspace(0.0, 1.0, sy1 - sy0)[:, None]
    seat_env = (
        168.0
        + 52.0 * np.cos((su - 0.48) * math.pi * 3.2)
        - 48.0 * np.exp(-(((sv - 0.62) / 0.16) ** 2))
        + 42.0 * np.exp(-(((sv - 0.28) / 0.14) ** 2))
        + rng.normal(0.0, 1.8, (sy1 - sy0, sx1 - sx0))
    )
    arr[sy0:sy1, sx0:sx1, 0] = np.clip(seat_env * 0.98, 42, 250)
    arr[sy0:sy1, sx0:sx1, 1] = np.clip(seat_env * 0.99, 44, 252)
    arr[sy0:sy1, sx0:sx1, 2] = np.clip(seat_env * 1.02, 48, 255)

    # 4. Zinc Machined Hardware Swatch (u: 0.65..0.99, v: 0.51..0.74)
    zy0, zy1 = int(0.510 * H), int(0.740 * H)
    zx0, zx1 = int(0.650 * W), int(0.990 * W)
    zu = np.linspace(0.0, 1.0, zx1 - zx0)[None, :]
    zv = np.linspace(0.0, 1.0, zy1 - zy0)[:, None]
    zinc = 162.0 + 38.0 * np.cos(zu * 2.0 * math.pi) - 18.0 * zv + rng.normal(0.0, 3.0, (zy1 - zy0, zx1 - zx0))
    arr[zy0:zy1, zx0:zx1, 0] = np.clip(zinc * 0.98, 40, 235)
    arr[zy0:zy1, zx0:zx1, 1] = np.clip(zinc * 0.99, 40, 238)
    arr[zy0:zy1, zx0:zx1, 2] = np.clip(zinc * 1.02, 42, 242)

    # 5. Yellow-Zinc / Brass Cotter Pin Swatch (u: 0.65..0.82, v: 0.75..0.99)
    by0, by1 = int(0.750 * H), int(0.990 * H)
    bx0, bx1 = int(0.650 * W), int(0.820 * W)
    arr[by0:by1, bx0:bx1] = [208, 178, 92]

    # 6. Black Rubber Valve Stem / Grip Sleeve Swatch (u: 0.82..0.99, v: 0.75..0.99)
    vx0, vx1 = int(0.820 * W), int(0.990 * W)
    arr[by0:by1, vx0:vx1] = [28, 30, 33]


def _paint_polar_wheel_suit(arr):
    """Top-left 512x512 polar wheel face for Suit Rider:
    Black tire sidewall outside r_norm=0.61, crisp white concave stamped-steel dish rim inside,
    subtle rolled rim lip, and central zinc hub boss."""
    H, W, _ = arr.shape
    x0, y0, x1, y1 = int(0.010 * W), int(0.010 * H), int(0.490 * W), int(0.490 * H)
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    rad_max = 0.5 * (x1 - x0)

    yy, xx = np.mgrid[0:512, 0:512]
    dx = (xx - cx) / rad_max
    dy = (yy - cy) / rad_max
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)

    rim_frac = SUIT_SPEC["rim_r"] / SUIT_SPEC["wheel_r"]  # ~0.610

    # Tire sidewall (rr >= rim_frac)
    sidewall = 34.0 + 10.0 * np.exp(-(((rr - 0.80) / 0.09) ** 2)) - 8.0 * np.clip((rr - 0.92) / 0.08, 0, 1)
    # Molded sidewall ring at rr = 0.73
    sidewall += 5.0 * np.exp(-(((rr - 0.73) / 0.008) ** 2))

    # White painted concave stamped-steel dish (rr < rim_frac)
    # Concave shading: upper half slightly shadowed, lower half catches light + rolled outer lip at rim_frac!
    dish = 232.0 - 22.0 * np.exp(-((rr / 0.42) ** 2)) + 10.0 * (dy / np.maximum(rr, 0.15)) * np.clip(rr / rim_frac, 0, 1)
    # Outer rolled lip crease at rim_frac - 0.035
    lip_groove = -28.0 * np.exp(-(((rr - (rim_frac - 0.042)) / 0.011) ** 2))
    lip_hi = 14.0 * np.exp(-(((rr - (rim_frac - 0.018)) / 0.010) ** 2))
    dish = np.clip(dish + lip_groove + lip_hi, 150.0, 250.0)

    # Center zinc washer / castle nut zone (rr < 0.115)
    nut = 158.0 + 28.0 * np.cos(ang * 6.0) - 30.0 * np.exp(-(((rr - 0.105) / 0.012) ** 2))

    c_r = np.where(rr > rim_frac, sidewall, np.where(rr > 0.115, dish * 0.985, nut * 0.98))
    c_g = np.where(rr > rim_frac, sidewall * 1.01, np.where(rr > 0.115, dish * 0.995, nut * 0.98))
    c_b = np.where(rr > rim_frac, sidewall * 1.03, np.where(rr > 0.115, dish * 1.015, nut * 0.94))

    arr[0:512, 0:512, 0] = np.clip(c_r, 10, 252)
    arr[0:512, 0:512, 1] = np.clip(c_g, 10, 253)
    arr[0:512, 0:512, 2] = np.clip(c_b, 12, 255)


def _paint_polar_wheel_squat(arr):
    """Top-left 512x512 polar wheel face for Squat Rider:
    Beefy black implement tire sidewall + stepped concave light-grey (#c8ccd2) 5-lug steel rim
    with open dark center hub bore (r < 0.105) and 5 crisp silver hex lug bolts!"""
    H, W, _ = arr.shape
    x0, y0, x1, y1 = int(0.010 * W), int(0.010 * H), int(0.490 * W), int(0.490 * H)
    cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
    rad_max = 0.5 * (x1 - x0)

    yy, xx = np.mgrid[0:512, 0:512]
    dx = (xx - cx) / rad_max
    dy = (yy - cy) / rad_max
    rr = np.sqrt(dx * dx + dy * dy)

    rim_frac = SQUAT_SPEC["rim_r"] / SQUAT_SPEC["wheel_r"]   # ~0.605
    bore_frac = SQUAT_SPEC["bore_r"] / SQUAT_SPEC["wheel_r"] # ~0.105
    lug_frac = SQUAT_SPEC["lug_r"] / SQUAT_SPEC["wheel_r"]   # ~0.188

    sidewall = 32.0 + 11.0 * np.exp(-(((rr - 0.79) / 0.09) ** 2)) + 4.5 * np.exp(-(((rr - 0.71) / 0.008) ** 2))

    # Stepped silver-grey implement rim (#c4c8cf)
    dish = 196.0 + 12.0 * (dy / np.maximum(rr, 0.15)) * np.clip(rr / rim_frac, 0, 1)
    # Step rings at rr = 0.44 and outer bead lip at rim_frac - 0.038
    dish -= 26.0 * np.exp(-(((rr - 0.445) / 0.013) ** 2))
    dish += 16.0 * np.exp(-(((rr - 0.470) / 0.012) ** 2))
    dish -= 30.0 * np.exp(-(((rr - (rim_frac - 0.042)) / 0.011) ** 2))
    dish += 18.0 * np.exp(-(((rr - (rim_frac - 0.018)) / 0.010) ** 2))
    # Flat center mounting pad inside rr = 0.25 + bore lip at bore_frac
    dish += 10.0 * np.exp(-(((rr - (bore_frac + 0.014)) / 0.009) ** 2))

    # 5 lug bolt shadows/highlights on bolt circle
    for k in range(5):
        la = -0.5 * math.pi + 2.0 * math.pi * k / 5.0
        lx, ly = lug_frac * math.cos(la), lug_frac * math.sin(la)
        dl = np.sqrt((dx - lx) ** 2 + (dy - ly) ** 2)
        dish = np.where(dl < 0.026, 218.0 - 650.0 * dl, dish - 16.0 * np.exp(-((dl / 0.036) ** 2)))

    # Open dark center bore (rr < bore_frac) showing dark steel axle housing inside!
    bore = 34.0 + 22.0 * np.exp(-(((dx + 0.02) ** 2 + (dy - 0.02) ** 2) / 0.004))

    c_r = np.where(rr > rim_frac, sidewall, np.where(rr > bore_frac, dish * 0.975, bore))
    c_g = np.where(rr > rim_frac, sidewall * 1.01, np.where(rr > bore_frac, dish * 0.990, bore * 1.01))
    c_b = np.where(rr > rim_frac, sidewall * 1.03, np.where(rr > bore_frac, dish * 1.020, bore * 1.03))

    arr[0:512, 0:512, 0] = np.clip(c_r, 10, 250)
    arr[0:512, 0:512, 1] = np.clip(c_g, 10, 252)
    arr[0:512, 0:512, 2] = np.clip(c_b, 12, 255)


def build_rig_textures(out_dir, progs_dir):
    """Generates sRGB and DarkPlaces-calibrated rig atlases + additive spark FX texture."""
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(progs_dir, exist_ok=True)

    # 1. Suit Rig Atlas (1024x1024)
    arr_suit = np.full((1024, 1024, 3), 36.0, dtype=np.float32)
    _paint_common_tread_and_chrome(arr_suit, is_squat=False)
    _paint_polar_wheel_suit(arr_suit)
    im_suit = Image.fromarray(arr_suit.astype(np.uint8), "RGB")
    im_suit.save(os.path.join(out_dir, "mm_suit_rig_srgb.png"))
    dp_calibrate(im_suit, brightness=0.62, contrast=1.10).save(os.path.join(progs_dir, "mm_suit_rig.png"))

    # 2. Squat Rig Atlas (1024x1024)
    arr_squat = np.full((1024, 1024, 3), 36.0, dtype=np.float32)
    _paint_common_tread_and_chrome(arr_squat, is_squat=True)
    _paint_polar_wheel_squat(arr_squat)
    im_squat = Image.fromarray(arr_squat.astype(np.uint8), "RGB")
    im_squat.save(os.path.join(out_dir, "mm_squat_rig_srgb.png"))
    dp_calibrate(im_squat, brightness=0.62, contrast=1.10).save(os.path.join(progs_dir, "mm_squat_rig.png"))

    # 3. Additive Grinding Spark FX Texture (512x512, black background for blendfunc add)
    S = 512
    fx = np.zeros((S, S, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:S, 0:S]
    dx = (xx - S * 0.5) / (S * 0.5)
    dy = (yy - S * 0.5) / (S * 0.5)
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)

    # Hot white-yellow core at contact point
    core = np.exp(-((rr / 0.13) ** 2))
    halo = 0.45 * np.exp(-((rr / 0.34) ** 2))
    fx[..., 0] += 255.0 * (core + halo)
    fx[..., 1] += 235.0 * core + 135.0 * halo
    fx[..., 2] += 195.0 * core + 35.0 * halo

    # Sharp flying grinding spark streaks!
    rng = np.random.default_rng(777)
    im_fx = Image.fromarray(np.clip(fx, 0, 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im_fx)
    for _ in range(95):
        a = rng.uniform(-math.pi, math.pi)
        r0 = rng.uniform(0.03, 0.22) * (S * 0.5)
        r1 = r0 + rng.uniform(0.14, 0.68) * (S * 0.5)
        if r1 > S * 0.48:
            r1 = S * 0.48
        p0 = (S * 0.5 + r0 * math.cos(a), S * 0.5 + r0 * math.sin(a))
        p1 = (S * 0.5 + r1 * math.cos(a), S * 0.5 + r1 * math.sin(a))
        hot = rng.uniform(0.65, 1.0)
        col = (int(255 * hot), int(rng.uniform(145, 235) * hot), int(rng.uniform(35, 130) * hot))
        dr.line([p0, p1], fill=col, width=1 if rng.random() < 0.6 else 2)
    im_fx = im_fx.filter(ImageFilter.GaussianBlur(radius=0.55))
    # Ensure zero border so additive quads never show square edges!
    fx_arr = np.array(im_fx, dtype=np.float32)
    vig = np.clip(1.0 - ((rr - 0.68) / 0.28), 0.0, 1.0) ** 1.5
    fx_arr *= vig[..., None]
    im_fx_clean = Image.fromarray(np.clip(fx_arr, 0, 255).astype(np.uint8), "RGB")
    im_fx_clean.save(os.path.join(out_dir, "mm_rider_fx_srgb.png"))
    im_fx_clean.save(os.path.join(progs_dir, "mm_rider_fx.png"))


# --------------------------------------------------------------------------- Curved Tube Extruder Helper
def add_tube_path(part, pts, radius, segs=14, uv_rect=UV_CHROME_SHAFT, cap_start=True, cap_end=True):
    """Sweeps a smooth circular tube along a 3D polyline pts = [(x,y,z), ...]."""
    n = len(pts)
    if n < 2:
        return
    tangents = []
    for i in range(n):
        if i == 0:
            t = mg.vnorm(mg.vsub(pts[1], pts[0]))
        elif i == n - 1:
            t = mg.vnorm(mg.vsub(pts[-1], pts[-2]))
        else:
            t = mg.vnorm(mg.vadd(mg.vnorm(mg.vsub(pts[i], pts[i - 1])), mg.vnorm(mg.vsub(pts[i + 1], pts[i]))))
        tangents.append(t)

    # Parallel-transport frame along curve
    _, N0, B0 = mg.basis_from_axis(tangents[0])
    frames = [(N0, B0)]
    for i in range(1, n):
        prev_N, _ = frames[-1]
        T = tangents[i]
        N = mg.vsub(prev_N, mg.vmul(T, mg.vdot(prev_N, T)))
        if mg.vlen(N) < 1e-5:
            _, N, _ = mg.basis_from_axis(T)
        else:
            N = mg.vnorm(N)
        B = mg.vcross(T, N)
        frames.append((N, B))

    u0, v0, u1, v1 = uv_rect
    arc = [0.0]
    for i in range(1, n):
        arc.append(arc[-1] + mg.vlen(mg.vsub(pts[i], pts[i - 1])))
    total_len = max(arc[-1], 1e-6)

    cols = segs + 1
    base = len(part.verts)
    for i, (p, (N, B)) in enumerate(zip(pts, frames)):
        vv = v0 + (v1 - v0) * (arc[i] / total_len)
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(segs))
            nrm = mg.vadd(mg.vmul(N, math.cos(th)), mg.vmul(B, math.sin(th)))
            part.verts.append(mg.vadd(p, mg.vmul(nrm, radius)))
            part.norms.append(nrm)
            part.st.append((u0 + (u1 - u0) * (j / float(segs)), vv))

    for i in range(n - 1):
        for j in range(segs):
            a = base + i * cols + j
            b = a + 1
            c = a + cols
            d = c + 1
            part.tris.append((a, b, c))
            part.tris.append((b, d, c))

    uc, vc = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
    if cap_start:
        c_idx = len(part.verts)
        n_cap = mg.vmul(tangents[0], -1.0)
        part.verts.append(pts[0])
        part.norms.append(n_cap)
        part.st.append((uc, vc))
        N, B = frames[0]
        r_base = len(part.verts)
        for j in range(segs):
            th = 2.0 * math.pi * (j / float(segs))
            nrm = mg.vadd(mg.vmul(N, math.cos(th)), mg.vmul(B, math.sin(th)))
            part.verts.append(mg.vadd(pts[0], mg.vmul(nrm, radius)))
            part.norms.append(n_cap)
            part.st.append((uc, vc))
        for j in range(segs):
            part.tris.append((c_idx, r_base + (j + 1) % segs, r_base + j))

    if cap_end:
        c_idx = len(part.verts)
        n_cap = tangents[-1]
        part.verts.append(pts[-1])
        part.norms.append(n_cap)
        part.st.append((uc, vc))
        N, B = frames[-1]
        r_base = len(part.verts)
        for j in range(segs):
            th = 2.0 * math.pi * (j / float(segs))
            nrm = mg.vadd(mg.vmul(N, math.cos(th)), mg.vmul(B, math.sin(th)))
            part.verts.append(mg.vadd(pts[-1], mg.vmul(nrm, radius)))
            part.norms.append(n_cap)
            part.st.append((uc, vc))
        for j in range(segs):
            part.tris.append((c_idx, r_base + j, r_base + (j + 1) % segs))


# --------------------------------------------------------------------------- Wheel Mesh Builders (Centered at Origin, Axis +Y)
def build_suit_wheel_local(side_sign=1.0):
    """Builds one Suit Rider wheel centered at (0,0,0) with axle along +Y.
    side_sign = +1.0 for Port (+Y outer face), -1.0 for Starboard (-Y outer face)."""
    part = mg.MeshPart("mm_suit_rig")
    R = SUIT_SPEC["wheel_r"]
    hw = 0.5 * SUIT_SPEC["wheel_w"]
    R_rim = SUIT_SPEC["rim_r"]
    R_lip = R_rim - 0.35

    # Axis along outward normal (0, side_sign, 0) so s > 0 is OUTER dish face, s < 0 is INNER hub face!
    ax = (0.0, side_sign, 0.0)
    up = (0.0, 0.0, 1.0)

    # 1. Outer & Inner Sidewalls + Concave White Stamped-Steel Dish (polar mapped!)
    # March from inner axle hub (s = -0.95) -> inner rim -> inner sidewall -> tread shoulder
    inner_prof = [
        (-1.55, 0.62, 0.0, R),
        (-1.55, 1.45, 0.0, R),
        (-0.85, 1.45, 0.0, R),
        (-0.85, 1.45, 0.0, R),
        (-0.55, 2.80, 0.0, R),
        (-0.75, R_lip, 0.0, R),
        (-1.35, R_rim, 0.0, R),
        (-1.35, R_rim, 0.0, R),
        (-hw * 0.92, R * 0.76, 0.0, R),
        (-hw, R * 0.85, 0.0, R),
        (-hw * 0.90, R * 0.94, 0.0, R),
    ]
    part.add_lathe((0.0, 0.0, 0.0), ax, inner_prof, segs=32, uv_mode="polar", uv_rect=UV_WHEEL_FACE, up_hint=up)

    # 2. Tire Tread Crown across s = -hw*0.90 .. +hw*0.90 (cylindrical mapped to 5-ribbed tread swatch!)
    tread_prof = [
        (-hw * 0.90, R * 0.94, 0.04),
        (-hw * 0.72, R * 0.985, 0.16),
        (-hw * 0.42, R * 1.000, 0.32),
        (0.0,        R * 1.005, 0.50),
        (+hw * 0.42, R * 1.000, 0.68),
        (+hw * 0.72, R * 0.985, 0.84),
        (+hw * 0.90, R * 0.94, 0.96),
    ]
    part.add_lathe((0.0, 0.0, 0.0), ax, tread_prof, segs=32, uv_mode="cyl", uv_rect=UV_TIRE_TREAD, up_hint=up)

    # 3. Outer Sidewall -> Rolled White Rim Lip -> Concave White Dish -> Center Washer (marching +s -> center)
    # Note: add_lathe expects profile marching -axis to +axis for outward normals, so march center -> outer!
    outer_dish_prof = [
        (+0.35, 1.25, 0.0, R),
        (+0.22, 3.60, 0.0, R),
        (+0.62, R_lip - 0.25, 0.0, R),
        (+1.38, R_lip + 0.10, 0.0, R),
        (+1.48, R_rim, 0.0, R),
        (+1.48, R_rim, 0.0, R),
        (+hw * 0.96, R * 0.76, 0.0, R),
        (+hw, R * 0.85, 0.0, R),
        (+hw * 0.90, R * 0.94, 0.0, R),
    ]
    # Flip winding for outer face since normal points +ax while r grows! Easiest: lathe along -ax with negated s!
    outer_dish_flip = [(-s, r, tv, rmax) for (s, r, tv, rmax) in reversed(outer_dish_prof)]
    part.add_lathe((0.0, 0.0, 0.0), (-ax[0], -ax[1], -ax[2]), outer_dish_flip, segs=32, uv_mode="polar", uv_rect=UV_WHEEL_FACE, up_hint=up)

    # 4. Outer Center Zinc Washer + 6-seg Hex Castle Nut + Threaded Stub + Yellow Cotter Pin!
    nut_prof = [
        (0.32, 1.30, 0.1),
        (0.48, 1.30, 0.2),
        (0.48, 0.92, 0.3),
        (1.05, 0.88, 0.7),
        (1.05, 0.52, 0.8),
        (1.42, 0.48, 0.95),
        (1.48, 0.0,  1.0),
    ]
    part.add_lathe((0.0, 0.0, 0.0), ax, nut_prof, segs=6, uv_mode="cyl", uv_rect=UV_DARK_METAL, up_hint=up)

    # Cotter pin through axle stub at s = 1.22
    add_tube_path(
        part,
        [(0.0, side_sign * 1.22, -0.85), (0.0, side_sign * 1.22, +0.85)],
        radius=0.11, segs=6, uv_rect=UV_BRASS_ACC,
    )

    # 5. Outer Black Rubber Snap-in Valve Stem at 6 o'clock (r = 5.15, z = -5.15)
    add_tube_path(
        part,
        [(0.0, side_sign * 0.55, -5.10), (0.0, side_sign * 1.55, -4.85)],
        radius=0.28, segs=8, uv_rect=UV_VALVE_BLK,
    )
    return part


def build_squat_wheel_local(side_sign=1.0):
    """Builds one Squat Rider 5-lug stepped grey implement wheel centered at (0,0,0)."""
    part = mg.MeshPart("mm_squat_rig")
    R = SQUAT_SPEC["wheel_r"]
    hw = 0.5 * SQUAT_SPEC["wheel_w"]
    R_rim = SQUAT_SPEC["rim_r"]
    R_bore = SQUAT_SPEC["bore_r"]
    R_lug = SQUAT_SPEC["lug_r"]

    ax = (0.0, side_sign, 0.0)
    up = (0.0, 0.0, 1.0)

    # 1. Inner flanged hub collar + inner stepped grey dish + inner tire sidewall
    inner_prof = [
        (-2.60, 0.78, 0.0, R),
        (-2.60, 1.85, 0.0, R),
        (-1.45, 1.85, 0.0, R),
        (-1.45, 2.95, 0.0, R),
        (-0.75, 3.20, 0.0, R),
        (-0.95, 5.50, 0.0, R),
        (-1.75, R_rim, 0.0, R),
        (-1.75, R_rim, 0.0, R),
        (-hw * 0.94, R * 0.75, 0.0, R),
        (-hw, R * 0.85, 0.0, R),
        (-hw * 0.90, R * 0.94, 0.0, R),
    ]
    part.add_lathe((0.0, 0.0, 0.0), ax, inner_prof, segs=36, uv_mode="polar", uv_rect=UV_WHEEL_FACE, up_hint=up)

    # 2. Beefy 5-Ribbed Implement Tire Tread
    tread_prof = [
        (-hw * 0.90, R * 0.94, 0.04),
        (-hw * 0.72, R * 0.985, 0.16),
        (-hw * 0.42, R * 1.000, 0.32),
        (0.0,        R * 1.006, 0.50),
        (+hw * 0.42, R * 1.000, 0.68),
        (+hw * 0.72, R * 0.985, 0.84),
        (+hw * 0.90, R * 0.94, 0.96),
    ]
    part.add_lathe((0.0, 0.0, 0.0), ax, tread_prof, segs=36, uv_mode="cyl", uv_rect=UV_TIRE_TREAD, up_hint=up)

    # 3. Outer Sidewall -> Stepped Concave Grey Steel Rim -> Recessed Open Center Bore!
    outer_prof = [
        (-0.95, 0.0,    0.0, R),    # dark inner axle recess backplate inside open center bore!
        (-0.95, R_bore, 0.0, R),
        (+0.18, R_bore, 0.0, R),    # cylindrical wall of open center bore!
        (+0.18, R_bore, 0.0, R),
        (+0.18, 3.45,   0.0, R),    # flat 5-lug mounting pad
        (+0.68, 5.45,   0.0, R),    # first concave dish slope
        (+1.18, 5.80,   0.0, R),    # crisp stamped step ring!
        (+1.62, R_rim - 0.32, 0.0, R),
        (+1.90, R_rim,  0.0, R),    # rolled outer bead lip
        (+1.90, R_rim,  0.0, R),
        (+hw * 0.96, R * 0.75, 0.0, R),
        (+hw, R * 0.85, 0.0, R),
        (+hw * 0.90, R * 0.94, 0.0, R),
    ]
    outer_flip = [(-s, r, tv, rmax) for (s, r, tv, rmax) in reversed(outer_prof)]
    part.add_lathe((0.0, 0.0, 0.0), (-ax[0], -ax[1], -ax[2]), outer_flip, segs=36, uv_mode="polar", uv_rect=UV_WHEEL_FACE, up_hint=up)

    # 4. Five 3D Silver Hex Lug Nuts around the center bore!
    lug_prof = [
        (0.16, 0.42, 0.1),
        (0.55, 0.38, 0.7),
        (0.62, 0.0,  1.0),
    ]
    for k in range(5):
        la = 0.5 * math.pi + 2.0 * math.pi * k / 5.0
        lx = -R_lug * math.cos(la) * side_sign
        lz = R_lug * math.sin(la)
        part.add_lathe((lx, 0.0, lz), ax, lug_prof, segs=6, uv_mode="cyl", uv_rect=UV_CHROME_SHAFT, up_hint=up)

    # 5. Valve stem on outer stepped dish (at ~11 o'clock / 1 o'clock)
    va = math.radians(108.0)
    vx, vz = 6.35 * math.cos(va), 6.35 * math.sin(va)
    add_tube_path(
        part,
        [(vx, side_sign * 1.25, vz), (vx * 0.96, side_sign * 2.05, vz * 0.96)],
        radius=0.22, segs=7, uv_rect=UV_VALVE_BLK,
    )
    return part


# --------------------------------------------------------------------------- Central Frame, Bucket Seat & Handlebars
def _build_contoured_bucket_seat(part):
    """Builds Suit Rider's gleaming stamped-stainless contoured low-back bucket seat
    with rolled 3D perimeter lip + twin vertical rear tubular support ribs & shaft clamp."""
    # Spine curve in XZ plane from front lip -> deep hip pan -> reclined backrest top
    # Matches f=42 (side: backrest at X=-12.0!) and f=77 (rear: half-width ~7.35!) pixel-for-pixel!
    spine_xz = [
        (+0.85, 14.80, 6.40),   # (x, z, half_width_y) front rolled thigh lip
        (-1.60, 14.05, 7.10),
        (-4.50, 13.90, 7.35),   # lowest hip pan
        (-7.20, 14.25, 7.35),
        (-8.95, 15.20, 7.30),   # pan-to-backrest curve
        (-9.95, 17.20, 7.20),
        (-10.75, 20.10, 7.00),
        (-11.45, 23.00, 6.50),
        (-11.90, 24.95, 5.35),  # rounded upper corners
        (-12.15, 25.65, 3.50),  # top crest of backrest
    ]
    nu = len(spine_xz)
    nv = 15  # across width s in [-1..+1]
    thick = 0.28

    u0, v0, u1, v1 = UV_SEAT_STEEL
    top_grid = []
    bot_grid = []
    for i, (sx, sz, hw) in enumerate(spine_xz):
        # Compute tangent along spine to get shell normal
        i0 = max(0, i - 1)
        i1 = min(nu - 1, i + 1)
        tx, tz = spine_xz[i1][0] - spine_xz[i0][0], spine_xz[i1][1] - spine_xz[i0][1]
        tl = math.hypot(tx, tz) or 1.0
        nx_s, nz_s = tz / tl, -tx / tl

        row_t, row_b = [], []
        for j in range(nv):
            s = -1.0 + 2.0 * (j / float(nv - 1))
            py = s * hw
            # Lateral bucket dish curvature (sides curl slightly up/forward around hips & ribs!)
            curl = 0.90 * (s * s) * (1.0 - 0.45 * (i / float(nu - 1)))
            px = sx + nx_s * curl
            pz = sz + nz_s * curl
            n_top = mg.vnorm((nx_s, -0.32 * s, nz_s))
            n_bot = mg.vmul(n_top, -1.0)
            uv = (u0 + (u1 - u0) * (0.5 + 0.5 * s), v0 + (v1 - v0) * (1.0 - i / float(nu - 1)))
            row_t.append(((px, py, pz), n_top, uv))
            row_b.append(((px - n_top[0] * thick, py - n_top[1] * thick, pz - n_top[2] * thick), n_bot, uv))
        top_grid.append(row_t)
        bot_grid.append(row_b)

    # Emit top (concave inner) and bottom (gleaming outer rear!) shells
    for is_bot, grid in ((False, top_grid), (True, top_grid)):
        pass
    for is_bot, grid in ((False, top_grid), (True, bot_grid)):
        base = len(part.verts)
        for i in range(nu):
            for j in range(nv):
                p, nrm, uv = grid[i][j]
                part.verts.append(p)
                part.norms.append(nrm)
                part.st.append(uv)
        for i in range(nu - 1):
            for j in range(nv - 1):
                a = base + i * nv + j
                b = a + 1
                c = a + nv
                d = c + 1
                if not is_bot:
                    part.tris.append((a, b, c))
                    part.tris.append((b, d, c))
                else:
                    part.tris.append((a, c, b))
                    part.tris.append((b, c, d))

    # Rolled 3D stainless perimeter bead around the entire bucket seat rim!
    rim_loop = (
        [top_grid[i][nv - 1][0] for i in range(nu)]
        + [top_grid[nu - 1][j][0] for j in range(nv - 2, 0, -1)]
        + [top_grid[i][0][0] for i in range(nu - 1, -1, -1)]
        + [top_grid[0][j][0] for j in range(1, nv)]
    )
    add_tube_path(part, rim_loop, radius=0.28, segs=10, uv_rect=UV_CHROME_SHAFT, cap_start=False, cap_end=False)

    # Twin vertical/angled polished stainless spine support ribs connecting T-collar -> seat bottom -> backrest!
    for sy in (-1.15, +1.15):
        rib_pts = [
            (-0.65, sy * 0.80, 10.95),   # rises from twin split-clamp near T-collar!
            (-3.80, sy,        13.40),
            (-8.80, sy,        14.55),
            (-9.95, sy,        16.80),
            (-10.85, sy,       20.00),
            (-11.80, sy,       24.15),   # top bolted backrest boss
        ]
        add_tube_path(part, rib_pts, radius=0.40, segs=10, uv_rect=UV_CHROME_SHAFT)
        part.add_chamfer_box(-12.30, -11.70, sy - 0.55, sy + 0.55, 23.65, 24.65, ch=0.14, uv_rect=UV_DARK_METAL)

    # Under-seat twin-clamp collar around central shaft at (-3.5, 0, 12.1)
    part.add_chamfer_box(-4.45, -2.55, -1.95, +1.95, 11.20, 13.10, ch=0.25, uv_rect=UV_DARK_METAL)


def build_suit_frame():
    """Builds Suit Rider's central angled chrome bullet shaft + T-collar + cross-axle + contoured stainless seat."""
    part = mg.MeshPart("mm_suit_rig")
    p0 = SUIT_SPEC["shaft_p0"]
    ptip = SUIT_SPEC["shaft_p_tip"]
    axis_vec = mg.vsub(ptip, p0)
    L_tot = mg.vlen(axis_vec)
    axis_u = mg.vnorm(axis_vec)
    R_s = SUIT_SPEC["shaft_r"]

    # Ogive bullet shaft profile from rear end (s=0) -> collar -> seam groove -> polished ogive tip (s=L_tot)
    L_ogive = 4.10
    L_body = L_tot - L_ogive
    s_seam = 7.40  # right ahead of T-collar!
    prof = [
        (0.0,           0.0,        0.00),
        (0.0,           R_s * 0.90, 0.01),
        (0.35,          R_s,        0.03),
        (s_seam - 0.14, R_s,        0.27),
        (s_seam,        R_s * 0.88, 0.28),  # crisp turned seam ring seen in f=122!
        (s_seam + 0.14, R_s,        0.29),
        (L_body,        R_s,        0.78),
    ]
    for k in range(1, 13):
        t = k / 12.0
        # Smooth tangent parabolic/ogive bullet nose cone
        rk = R_s * math.sqrt(max(0.0, 1.0 - t * t)) * (1.0 - 0.12 * t)
        prof.append((L_body + L_ogive * t, rk if k < 12 else 0.0, 0.78 + 0.22 * t))
    part.add_lathe(p0, axis_u, prof, segs=28, uv_mode="cyl", uv_rect=UV_CHROME_SHAFT)

    # Horizontal stainless cross-axle (Y = -19.2 .. +19.2 at X=0, Z=wheel_r)
    z_ax = SUIT_SPEC["wheel_r"]
    ty = SUIT_SPEC["track_y"]
    R_ax = SUIT_SPEC["axle_r"]
    ax_prof = [
        (-ty - 0.4, R_ax, 0.02),
        (+ty + 0.4, R_ax, 0.98),
    ]
    part.add_lathe((0.0, 0.0, z_ax), (0.0, 1.0, 0.0), ax_prof, segs=18, uv_mode="cyl", uv_rect=UV_CHROME_SHAFT, up_hint=(0.0, 0.0, 1.0))

    # Central Machined Stainless Split T-Collar + Side Flanges + Socket Cap Bolts (f=122!)
    part.add_lathe(
        (0.0, 0.0, z_ax), axis_u,
        [(-1.65, R_s, 0.45), (-1.45, R_s + 0.44, 0.47), (+1.55, R_s + 0.44, 0.55), (+1.75, R_s, 0.57)],
        segs=24, uv_mode="cyl", uv_rect=UV_CHROME_SHAFT,
    )
    part.add_lathe(
        (0.0, 0.0, z_ax), (0.0, 1.0, 0.0),
        [(-2.45, R_ax, 0.4), (-2.30, R_ax + 0.55, 0.42), (+2.30, R_ax + 0.55, 0.58), (+2.45, R_ax, 0.6)],
        segs=18, uv_mode="cyl", uv_rect=UV_DARK_METAL, up_hint=(0.0, 0.0, 1.0),
    )
    # 4 clamp socket bolts on T-collar ears
    for sy in (-1.95, +1.95):
        for sz in (-0.75, +0.75):
            part.add_chamfer_box(-0.95, +0.95, sy - 0.28, sy + 0.28, z_ax + sz - 0.25, z_ax + sz + 0.25, ch=0.07, uv_rect=UV_DARK_METAL)

    # Contoured Stamped-Stainless Bucket Seat + Rolled Lip + Twin Spine Ribs
    _build_contoured_bucket_seat(part)
    return part


def build_squat_frame():
    """Builds Squat Rider's heavy scraping chrome bullet shaft + domed rear housing +
    4-bolt split T-clamp + cross-axle + twin upright curved chrome handlebars!"""
    part = mg.MeshPart("mm_squat_rig")
    p0 = SQUAT_SPEC["shaft_p0"]
    ptip = SQUAT_SPEC["shaft_p_tip"]
    axis_vec = mg.vsub(ptip, p0)
    L_tot = mg.vlen(axis_vec)
    axis_u = mg.vnorm(axis_vec)
    R_s = SQUAT_SPEC["shaft_r"]

    L_cone = 5.40
    L_body = L_tot - L_cone
    s_collar = mg.vlen(mg.vsub(SQUAT_SPEC["shaft_p_collar"], p0))
    s_seam = s_collar + 3.60

    # Rear domed housing cap -> cylinder under rider -> T-clamp -> seam groove -> conical-ogive scraping bullet tip!
    prof = [(0.0, 0.0, 0.0)]
    for k in range(1, 6):
        t = k / 5.0
        prof.append((1.45 * (1.0 - math.cos(0.5 * math.pi * t)), R_s * math.sin(0.5 * math.pi * t), 0.04 * t))
    prof += [
        (s_seam - 0.16, R_s,        0.27),
        (s_seam,        R_s * 0.89, 0.28),  # crisp circumferential seam groove seen in f=140!
        (s_seam + 0.16, R_s,        0.29),
        (L_body,        R_s,        0.82),
    ]
    for k in range(1, 13):
        t = k / 12.0
        # Sleek pointed conical-ogive nose cone (sharper taper than Suit Rider, matching f=47 & f=140!)
        rk = R_s * ((1.0 - t) ** 0.78) * (1.0 + 0.18 * math.sin(math.pi * t))
        prof.append((L_body + L_cone * t, rk if k < 12 else 0.0, 0.82 + 0.18 * t))
    part.add_lathe(p0, axis_u, prof, segs=32, uv_mode="cyl", uv_rect=UV_CHROME_SHAFT)

    # Domed differential-style rear housing bulge right behind cross-axle (seen in f=73!)
    z_ax = SQUAT_SPEC["wheel_r"]
    z_sh0 = SQUAT_SPEC["shaft_p_collar"][2]
    part.add_lathe(
        (0.0, 0.0, z_sh0), axis_u,
        [(-3.10, R_s * 0.98, 0.35), (-2.30, R_s + 0.58, 0.42), (+2.15, R_s + 0.52, 0.55), (+2.50, R_s, 0.58)],
        segs=26, uv_mode="cyl", uv_rect=UV_CHROME_SHAFT,
    )

    # Horizontal stainless cross-axle
    ty = SQUAT_SPEC["track_y"]
    R_ax = SQUAT_SPEC["axle_r"]
    part.add_lathe(
        (0.0, 0.0, z_ax), (0.0, 1.0, 0.0),
        [(-ty + 1.5, R_ax, 0.02), (+ty - 1.5, R_ax, 0.98)],
        segs=20, uv_mode="cyl", uv_rect=UV_CHROME_SHAFT, up_hint=(0.0, 0.0, 1.0),
    )

    # Heavy 4-Bolt Machined Split T-Clamp Collar joining shaft (z=13.35) & cross-axle (z=12.05)
    part.add_chamfer_box(-2.05, +2.05, -3.35, +3.35, z_ax - 1.35, z_sh0 + 1.35, ch=0.35, uv_rect=UV_SEAT_STEEL)
    part.add_lathe(
        (0.0, 0.0, z_ax), (0.0, 1.0, 0.0),
        [(-3.75, R_ax, 0.4), (-3.55, R_ax + 0.62, 0.42), (+3.55, R_ax + 0.62, 0.58), (+3.75, R_ax, 0.6)],
        segs=18, uv_mode="cyl", uv_rect=UV_SEAT_STEEL, up_hint=(0.0, 0.0, 1.0),
    )
    # 4 prominent hex clamp bolts on front & rear of split T-clamp ears
    for sy in (-2.65, +2.65):
        for sz in (-0.65, +0.95):
            part.add_chamfer_box(-2.35, +2.35, sy - 0.32, sy + 0.32, z_ax + sz - 0.28, z_ax + sz + 0.28, ch=0.08, uv_rect=UV_DARK_METAL)

    # Twin Upright Chrome Handlebar Loops + 2-Bolt Axle Split Clamps at Y = +-13.35!
    hy = SQUAT_SPEC["handle_y"]
    hz = SQUAT_SPEC["handle_z_top"]
    for sgn in (-1.0, +1.0):
        yc = sgn * hy
        # 2-bolt machined split-clamp base around cross-axle
        part.add_chamfer_box(-1.25, +1.25, yc - 0.95, yc + 0.95, z_ax - 1.18, z_ax + 1.35, ch=0.24, uv_rect=UV_SEAT_STEEL)
        for bx in (-0.72, +0.72):
            part.add_chamfer_box(bx - 0.24, bx + 0.24, yc - 1.12, yc + 1.12, z_ax + 0.85, z_ax + 1.50, ch=0.06, uv_rect=UV_DARK_METAL)

        # Curved tubular chrome riser -> horizontal fore-aft ergonomic grip bar!
        # Angles slightly outboard (+0.45u) at top grip, matching f=73 & f=140 1:1!
        grip_pts = [
            (+0.35, yc,                z_ax + 1.05),
            (+0.85, sgn * (hy + 0.15), z_ax + 3.00),
            (+1.25, sgn * (hy + 0.35), hz - 1.10),
            (+1.35, sgn * (hy + 0.45), hz - 0.22),
            (+0.85, sgn * (hy + 0.48), hz),
            (-2.05, sgn * (hy + 0.48), hz),
        ]
        add_tube_path(part, grip_pts, radius=0.42, segs=12, uv_rect=UV_CHROME_SHAFT)
        strut_pts = [
            (-0.45, yc,                z_ax + 1.05),
            (-0.95, sgn * (hy + 0.22), z_ax + 3.30),
            (-1.35, sgn * (hy + 0.48), hz - 0.10),
        ]
        add_tube_path(part, strut_pts, radius=0.34, segs=10, uv_rect=UV_CHROME_SHAFT)

    return part


def build_spark_burst(tip_pos, scale=1.0):
    """Builds a 3D multi-plane additive grinding spark starburst centered at tip_pos."""
    part = mg.MeshPart("mm_rider_fx")
    if scale <= 1e-3:
        # Degenerate tiny triangle hidden inside shaft when sparks are off
        for k in range(3):
            part.verts.append(tip_pos)
            part.norms.append((1.0, 0.0, 0.0))
            part.st.append((0.5, 0.5))
        part.tris.append((0, 1, 2))
        return part

    r = 6.2 * scale
    cx, cy, cz = tip_pos
    # 4 intersecting double-sided planes: ground splash + 2 vertical spray fans + transverse burst
    planes = [
        # Ground splash fan (just above z=0.25)
        ((cx - r * 0.85, cy - r, max(0.25, cz - r * 0.52)),
         (cx + r * 0.85, cy - r, max(0.25, cz - r * 0.52)),
         (cx + r * 0.85, cy + r, max(0.25, cz - r * 0.52)),
         (cx - r * 0.85, cy + r, max(0.25, cz - r * 0.52))),
        # Fore-aft vertical rooster-tail spray
        ((cx - r * 1.15, cy, cz - r * 0.55),
         (cx + r * 0.75, cy, cz - r * 0.55),
         (cx + r * 0.75, cy, cz + r * 0.85),
         (cx - r * 1.15, cy, cz + r * 0.85)),
        # Diagonal left spray
        ((cx - r * 0.95, cy - r * 0.75, cz - r * 0.50),
         (cx + r * 0.65, cy + r * 0.75, cz - r * 0.50),
         (cx + r * 0.65, cy + r * 0.75, cz + r * 0.75),
         (cx - r * 0.95, cy - r * 0.75, cz + r * 0.75)),
        # Diagonal right spray
        ((cx - r * 0.95, cy + r * 0.75, cz - r * 0.50),
         (cx + r * 0.65, cy - r * 0.75, cz - r * 0.50),
         (cx + r * 0.65, cy - r * 0.75, cz + r * 0.75),
         (cx - r * 0.95, cy + r * 0.75, cz + r * 0.75)),
    ]
    for p0, p1, p2, p3 in planes:
        part.add_quad(p0, p1, p2, p3, (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), two_sided=True)
    return part


# --------------------------------------------------------------------------- 3D Analytical Rig Volume & Z-Buffer Helper
def rig_exclusive_mask_3d(kind, X, Y, Z):
    """Vectorized boolean mask of 3D points (X, Y, Z) that belong strictly to the mechanical rig
    (wheels, cross-axle, protruding shaft, seat outer shell / handlebars) so human hull carving
    subtracts the rig cleanly without eating into the rider's body!"""
    sp = SUIT_SPEC if kind == "suit" else SQUAT_SPEC
    Rw = sp["wheel_r"]
    hw = 0.5 * sp["wheel_w"]
    ty = sp["track_y"]

    # 1. Left & Right Wheels (with small 0.55u clearance pad so tire rubber never fuses to jacket/pants)
    r_rad = np.sqrt(X * X + (Z - Rw) ** 2)
    in_wheel_l = (r_rad <= Rw + 0.55) & (np.abs(Y - ty) <= hw + 0.65)
    in_wheel_r = (r_rad <= Rw + 0.55) & (np.abs(Y + ty) <= hw + 0.65)

    # 2. Horizontal Cross-Axle & T-collar below the rider's seat/crotch
    r_ax = np.sqrt(X * X + (Z - Rw) ** 2)
    in_axle = (r_ax <= sp["axle_r"] + 0.75) & (np.abs(Y) <= ty + 1.2)

    # 3. Central Bullet Shaft (distance to 3D line segment p0 -> p_tip)
    p0 = np.array(sp["shaft_p0"], dtype=np.float32)
    p1 = np.array(sp["shaft_p_tip"], dtype=np.float32)
    ab = p1 - p0
    ab2 = float(np.dot(ab, ab))
    t = np.clip(((X - p0[0]) * ab[0] + (Y - p0[1]) * ab[1] + (Z - p0[2]) * ab[2]) / ab2, 0.0, 1.0)
    dx = X - (p0[0] + t * ab[0])
    dy = Y - (p0[1] + t * ab[1])
    dz = Z - (p0[2] + t * ab[2])
    d_shaft = np.sqrt(dx * dx + dy * dy + dz * dz)
    # Subtract shaft everywhere below rider's crotch or ahead of rider's pelvis
    if kind == "suit":
        in_shaft = (d_shaft <= sp["shaft_r"] + 0.55) & ((Z < 13.8) | (X > 1.2))
        # Also subtract lower T-collar & under-seat spine below Z=13.85
        in_extra = (np.abs(Y) <= 7.5) & (X >= -12.6) & (X <= 1.2) & (Z < 13.85) & (Z > 9.2)
        # Subtract rear outer face of stainless backrest (behind X = -9.2 - (Z-15)*0.26 within |Y|<=7.4)
        back_x = -9.1 - 0.26 * np.clip(Z - 15.0, 0.0, 12.0)
        in_seat_back = (np.abs(Y) <= 7.45) & (Z >= 13.7) & (Z <= 26.0) & (X <= back_x)
        in_extra = in_extra | in_seat_back
    else:
        in_shaft = (d_shaft <= sp["shaft_r"] + 0.55) & ((Z < 17.2) | (X > 1.5))
        # Handlebars riser tubes below grip top (Z < 17.3 around |Y| ~ 13.5)
        hy = sp["handle_y"] + 0.2
        in_hbar = (np.abs(np.abs(Y) - hy) <= 1.35) & (np.abs(X) <= 1.85) & (Z >= 10.8) & (Z <= 17.3)
        in_extra = in_hbar

    return in_wheel_l | in_wheel_r | in_axle | in_shaft | in_extra


def sample_rig_zbuffer_points(kind):
    """Returns dense (N, 3) surface point cloud of the 3D mechanical rig in rest pose
    so multi-view texture baking onto the human rider accurately Z-buffers wheel/axle/seat occlusion!"""
    if kind == "suit":
        parts = [
            (build_suit_frame(), (0.0, 0.0, 0.0)),
            (build_suit_wheel_local(+1.0), (0.0, +SUIT_SPEC["track_y"], SUIT_SPEC["wheel_r"])),
            (build_suit_wheel_local(-1.0), (0.0, -SUIT_SPEC["track_y"], SUIT_SPEC["wheel_r"])),
        ]
    else:
        parts = [
            (build_squat_frame(), (0.0, 0.0, 0.0)),
            (build_squat_wheel_local(+1.0), (0.0, +SQUAT_SPEC["track_y"], SQUAT_SPEC["wheel_r"])),
            (build_squat_wheel_local(-1.0), (0.0, -SQUAT_SPEC["track_y"], SQUAT_SPEC["wheel_r"])),
        ]

    pts = []
    rng = np.random.default_rng(123)
    for mp, off in parts:
        V = np.array(mp.verts, dtype=np.float32) + np.array(off, dtype=np.float32)
        T = np.array(mp.tris, dtype=np.int32)
        A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        # Sample triangle centroids + edge midpoints + dense random barycentric samples on larger faces
        pts.append((A + B + C) / 3.0)
        pts.append(0.5 * (A + B))
        pts.append(0.5 * (B + C))
        pts.append(0.5 * (C + A))
        areas = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
        counts = np.clip(np.ceil(areas * 6.0).astype(int), 1, 40)
        for ti, cnt in enumerate(counts):
            if cnt > 1:
                r1 = np.sqrt(rng.random(cnt, dtype=np.float32))[:, None]
                r2 = rng.random(cnt, dtype=np.float32)[:, None]
                p = (1.0 - r1) * A[ti] + r1 * (1.0 - r2) * B[ti] + r1 * r2 * C[ti]
                pts.append(p)
    return np.vstack(pts)


if __name__ == "__main__":
    out_d = os.path.join(HERE, "out", "mm_riders")
    progs_d = os.path.abspath(os.path.join(HERE, "..", "..", "progs"))
    build_rig_textures(out_d, progs_d)
    f_suit = build_suit_frame()
    w_suit = build_suit_wheel_local(+1.0)
    f_squat = build_squat_frame()
    w_squat = build_squat_wheel_local(+1.0)
    print(f"Suit Rig  : frame={len(f_suit.verts)}v/{len(f_suit.tris)}t, wheel={len(w_suit.verts)}v/{len(w_suit.tris)}t")
    print(f"Squat Rig : frame={len(f_squat.verts)}v/{len(f_squat.tris)}t, wheel={len(w_squat.verts)}v/{len(w_squat.tris)}t")
