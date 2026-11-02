"""Complete 360° Sprite & Showcase Builder for Tinfoil-Hat Bryan & His Demons (BakersfieldQuake).

Generates:
  1. G:\\Quake\\Combat\\BakersfieldQuake\\progs\\bryan.spr32 (264 frames, 320x288, origin=(-160, 263), DarkPlaces HDR-toned):
       0..7             8-dir Solo Bryan Standing Idle (d = 0..7, NO demons)
       8 + d*6 + k      8-dir Solo Bryan 360° Running Cycle (d = 0..7, k = 0..5, NO demons)  [mbox.qc compatible!]
       56 + d*6 + k     8-dir Solo Bryan Paranoid RGB Detector Scan (d = 0..7, k = 0..5, NO demons)
       104 + d*8 + k    8-dir "A DEMON! NO WAY!" 3D Giant-Swing Demon-Whirl Attack (d = 0..7, k = 0..7)
       168 + d*8 + k    8-dir 3-Demon Trio EMF Overload Surge (d = 0..7, k = 0..7)
       232..263         32-frame 4-Act Hell Portal Drag-Down Death -> Smoking Tinfoil Hat & Broken Detector!
  2. G:\\Quake\\Combat\\BakersfieldQuake\\bryan_sprite\\ (high-res 360x324 untoned PNGs, spr32/ previews, contact sheets, GIFs).
"""
import math
import os
import random
import struct
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

MOD_DIR = r"G:\Quake\Combat\BakersfieldQuake"
RIGS_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "out", "bryan_rigs")
WEB_DIR = os.path.join(MOD_DIR, "bryan_sprite")
SPR_PREVIEW_DIR = os.path.join(WEB_DIR, "spr32")
PROGS_DIR = os.path.join(MOD_DIR, "progs")
SPR_PATH = os.path.join(PROGS_DIR, "bryan.spr32")

os.makedirs(WEB_DIR, exist_ok=True)
os.makedirs(SPR_PREVIEW_DIR, exist_ok=True)
os.makedirs(PROGS_DIR, exist_ok=True)

# High-res showcase canvas (10:9 aspect) and DarkPlaces .spr32 canvas (exact 8/9 scale)
CW, CH = 360, 324
GROUND_Y = 296

SPR_W, SPR_H = 320, 288
SPR_GROUND_Y = 263
SPR_OX = -(SPR_W // 2)
SPR_OY = SPR_GROUND_Y

ANGLES = (0, 45, 90, 135, 180, 225, 270, 315)


def crop_tight_rgba(arr, alpha_thr=22):
    ys, xs = np.nonzero(arr[..., 3] > alpha_thr)
    if len(xs) == 0:
        return Image.fromarray(arr, "RGBA"), 0
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = arr[y0:y1, x0:x1].copy()
    # Center X using torso/head median so outstretched arms/legs don't skew character pivot!
    h_c = crop.shape[0]
    upper_a = crop[:max(10, int(h_c * 0.58)), :, 3] > 40
    if np.any(upper_a):
        cx = int(round(np.median(np.nonzero(upper_a)[1])))
    else:
        cx = crop.shape[1] // 2
    return Image.fromarray(crop, "RGBA"), cx


def scale_to_height(pil_im, pivot_x, target_h):
    sc = target_h / max(1.0, float(pil_im.height))
    nw = max(2, int(round(pil_im.width * sc)))
    nh = max(2, int(round(pil_im.height * sc)))
    return pil_im.resize((nw, nh), Image.LANCZOS), int(round(pivot_x * sc))


def warp_rgba_about_pivot(rgba, piv_x, piv_y, deg, shade=1.0, dx=0.0, dy=0.0):
    """Rotates and translates an RGBA limb layer cleanly around (piv_x, piv_y) using premultiplied alpha."""
    H, W = rgba.shape[:2]
    f = rgba.astype(np.float32)
    if abs(shade - 1.0) > 1e-3:
        f[..., :3] *= shade
    af = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * af, f[..., 3:4]], axis=-1)
    M = cv2.getRotationMatrix2D((float(piv_x), float(piv_y)), float(deg), 1.0)
    M[0, 2] += float(dx)
    M[1, 2] += float(dy)
    w_pm = cv2.warpAffine(pm, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wa = w_pm[..., 3:4] / 255.0
    w_rgb = np.where(wa > 1e-4, w_pm[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([np.clip(w_rgb, 0, 255).astype(np.uint8), np.clip(w_pm[..., 3], 0, 255).astype(np.uint8)])


def split_bryan_parts(run_arr, canon_ang):
    """Separates Bryan's intact rainbow unicorn t-shirt/arms/detector/head/tinfoil-hat (`upper`)
    from his two jeans legs (`lead` planted strike leg + `trail` bent-knee recovery leg) along the exact curved shirt hem."""
    H, W = run_arr.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]
    fg = run_arr[..., 3] > 25
    r = run_arr[..., 0].astype(np.float32)
    g = run_arr[..., 1].astype(np.float32)
    b = run_arr[..., 2].astype(np.float32)

    y_start = 268 if canon_ang == 45 else 254
    is_dark_denim = fg & (yg >= y_start) & (
        (yg >= 308) |
        ((r < 88) & (g < 106) & ((r + g + b) < 265) & (b >= r - 12))
    )
    if canon_ang == 45:
        is_dark_denim &= ~((xg < 192) & (yg < 295))

    is_legs = ndimage.binary_closing(is_dark_denim, iterations=2)
    is_legs = ndimage.binary_opening(is_legs, iterations=1)
    lbl_l, nl = ndimage.label(is_legs)
    if nl > 0:
        sz_l = ndimage.sum(is_legs, lbl_l, range(1, nl + 1))
        is_legs = np.isin(lbl_l, [1 + i for i, s in enumerate(sz_l) if s >= 300])

    is_upper = fg & (~is_legs)
    lbl_u, nu = ndimage.label(is_upper)
    if nu > 0:
        sz_u = ndimage.sum(is_upper, lbl_u, range(1, nu + 1))
        is_upper = np.isin(lbl_u, [1 + i for i, s in enumerate(sz_u) if s >= 60])
    is_legs = fg & (~is_upper)

    w_up = cv2.GaussianBlur(is_upper.astype(np.float32), (3, 3), 0.65)
    upper = run_arr.copy()
    upper[..., 3] = np.round(run_arr[..., 3].astype(np.float32) * np.where(yg < 248, 1.0, w_up)).astype(np.uint8)

    _, lx_top = np.nonzero(is_legs & (yg >= 265) & (yg <= 318))
    hx = int(round(np.median(lx_top)))
    hy = 278

    if canon_ang == 270:
        is_lead = is_legs & (xg >= (hx - 5 + (yg - hy) * 0.14))
        is_trail = is_legs & ((xg <= (hx + 10)) & (~((yg > 335) & (xg > hx - 2))))
    elif canon_ang == 135:
        is_lead = is_legs & (xg <= (hx + 5 - (yg - hy) * 0.14))
        is_trail = is_legs & ((xg >= (hx - 10)) & (~((yg > 335) & (xg < hx + 2))))
    else:  # 45°
        is_lead = is_legs & (xg <= (hx + 2 - (yg - hy) * 0.08))
        is_trail = is_legs & ((xg >= (hx - 10)) & (~((yg > 345) & (xg < hx - 2))))

    def make_limb(mask_l):
        arr_l = np.zeros_like(run_arr)
        m_d = ndimage.binary_dilation(mask_l, iterations=1) & is_legs
        arr_l[m_d] = run_arr[m_d]
        lb, nb = ndimage.label(arr_l[..., 3] > 20)
        if nb > 0:
            sb = ndimage.sum(arr_l[..., 3] > 20, lb, range(1, nb + 1))
            arr_l[~np.isin(lb, [1 + i for i, s in enumerate(sb) if s >= 250])] = 0
        ys_l, xs_l = np.nonzero(arr_l[..., 3] > 40)
        if len(ys_l) > 0:
            top_y = int(ys_l.min())
            top_xs = xs_l[ys_l <= top_y + 12]
            x0, x1 = int(top_xs.min()) + 2, int(top_xs.max()) - 2
            if x1 > x0:
                cx_c = 0.5 * (x0 + x1)
                rx_c = max(8.0, 0.5 * (x1 - x0))
                sub_y, sub_x = np.mgrid[max(246, top_y - 18):top_y + 4, 0:W]
                dome = (((sub_x - cx_c) / rx_c) ** 2 + ((sub_y - (top_y + 4)) / 18.0) ** 2) <= 1.0
                sl = arr_l[max(246, top_y - 18):top_y + 4]
                sl[dome & (sl[..., 3] < 40)] = [26, 39, 64, 255]
        return arr_l

    return upper, make_limb(is_lead), make_limb(is_trail), hx, hy


def build_solo_bryan_idle_and_run6(run_arr, idle_arr_fallback, d_idx):
    """Builds both a 100% clean 2-feet-planted Idle rig AND a 6-frame alternating 2-leg Run cycle
    for SOLO Tinfoil-Hat Bryan at angle index d_idx (0..7) on 512x512 RGBA."""
    H, W = run_arr.shape[:2]
    ang = ANGLES[d_idx]

    if ang in (0, 180):
        a = run_arr[..., 3] > 30
        hx = int(round(np.median(np.nonzero(a[235:270, :])[1])))
        w_min = min(96, hx, W - hx)

        stride_b = run_arr.copy().astype(np.float32)
        orig_f = run_arr.copy().astype(np.float32)
        flipped_sub = np.fliplr(orig_f[252:, hx - w_min:hx + w_min])
        blend_y = np.clip((np.arange(H - 252, dtype=np.float32)[:, None, None] - 4.0) / 10.0, 0.0, 1.0)
        stride_b[252:, hx - w_min:hx + w_min] = (
            orig_f[252:, hx - w_min:hx + w_min] * (1.0 - blend_y) + flipped_sub * blend_y
        )
        stride_b_u8 = np.clip(stride_b, 0, 255).astype(np.uint8)

        def mid_stride(s_arr):
            out = s_arr.copy()
            sa = out[..., 3] > 30
            yl = np.max(np.nonzero(sa[:, :hx])[0]) if np.any(sa[:, :hx]) else 460
            yr = np.max(np.nonzero(sa[:, hx:])[0]) if np.any(sa[:, hx:]) else 460
            hip_y = 272
            x_sl = slice(hx, W) if yr < yl else slice(0, hx)
            stretch = min(1.16, max(1.0, 1.0 + 0.48 * (((max(yl, yr) - hip_y) / max(20.0, min(yl, yr) - hip_y)) - 1.0)))
            sub = out[hip_y:, x_sl].copy()
            nh = min(H - hip_y, int(round(sub.shape[0] * stretch)))
            sub_p = Image.fromarray(sub, "RGBA").resize((sub.shape[1], nh), Image.LANCZOS)
            out[hip_y:, x_sl] = 0
            pil = Image.fromarray(out, "RGBA")
            pil.alpha_composite(sub_p, (x_sl.start, hip_y))
            return np.array(pil)

        run6 = [
            run_arr,
            mid_stride(run_arr),
            idle_arr_fallback,
            stride_b_u8,
            mid_stride(stride_b_u8),
            idle_arr_fallback,
        ]
        return idle_arr_fallback, run6

    canon_ang = {90: 270, 270: 270, 135: 135, 225: 135, 45: 45, 315: 45}[ang]
    need_flip = (ang != canon_ang)
    w_run = np.fliplr(run_arr.copy()) if need_flip else run_arr.copy()
    up, lead, trail, hx, hy = split_bryan_parts(w_run, canon_ang)
    up_pil = Image.fromarray(up, "RGBA")
    fwd = 1.0 if canon_ang == 270 else -1.0

    # 1. Clean 2-feet-planted Idle stance (zero hip stub, intact rainbow tee!)
    if canon_ang == 270:
        l_near = warp_rgba_about_pivot(lead, hx, hy, -8.0, shade=1.00, dx=-4, dy=0)
        l_far = warp_rgba_about_pivot(lead, hx, hy, -5.0, shade=0.78, dx=-14, dy=-2)
    elif canon_ang == 135:
        l_near = warp_rgba_about_pivot(lead, hx, hy, +7.0, shade=1.00, dx=+3, dy=0)
        l_far = warp_rgba_about_pivot(lead, hx, hy, +3.0, shade=0.78, dx=+16, dy=-3)
    else:  # 45°
        l_near = warp_rgba_about_pivot(lead, hx, hy, 0.0, shade=1.00, dx=-2, dy=0)
        l_far = warp_rgba_about_pivot(lead, hx, hy, -2.0, shade=0.82, dx=+28, dy=-3)

    idle_pil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    idle_pil.alpha_composite(Image.fromarray(l_far, "RGBA"))
    idle_pil.alpha_composite(Image.fromarray(l_near, "RGBA"))
    idle_pil.alpha_composite(up_pil)
    idle_clean = np.fliplr(np.array(idle_pil)) if need_flip else np.array(idle_pil)

    # 2. Clean 6-frame 2-beat alternating run cycle using BOTH real legs (lead + bent-knee trail)!
    hip_off_far = int(-8 * fwd) if canon_ang != 45 else 20
    specs = [
        (lead, 0.0 * fwd, 0, trail, 0.0 * fwd, 0),      # k=0: Full Stride A (Near lead fwd, Far trail kicked back)
        (lead, -11.0 * fwd, 0, trail, 22.0 * fwd, 2),   # k=1: Drive A (Near pushes back, Far swings down-fwd)
        (lead, -21.0 * fwd, -2, lead, 10.0 * fwd, -4),  # k=2: Passing A (Legs cross under hip)
        (trail, 0.0 * fwd, 0, lead, 1.0 * fwd, 0),      # k=3: Full Stride B (Near trail kicked back, Far lead fwd!)
        (trail, 22.0 * fwd, 2, lead, -11.0 * fwd, 0),   # k=4: Drive B
        (lead, 10.0 * fwd, -4, lead, -21.0 * fwd, -2),  # k=5: Passing B
    ]
    run6 = []
    for n_src, n_deg, n_dy, f_src, f_deg, f_dy in specs:
        f_im = warp_rgba_about_pivot(f_src, hx, hy, f_deg, shade=0.78, dx=hip_off_far, dy=f_dy - 1)
        n_im = warp_rgba_about_pivot(n_src, hx, hy, n_deg, shade=1.00, dx=0, dy=n_dy)
        cp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cp.alpha_composite(Image.fromarray(f_im, "RGBA"))
        cp.alpha_composite(Image.fromarray(n_im, "RGBA"))
        cp.alpha_composite(up_pil)
        arr_k = np.array(cp)
        run6.append(np.fliplr(arr_k) if need_flip else arr_k)

    return idle_clean, run6


def load_normalized_assets():
    """Loads all 8-direction Bryan & Demon rigs and normalizes them to crisp showcase proportions."""
    bryan_idle = {}
    bryan_run_a = {}
    bryan_run_6 = {}
    crimson = {}

    for d in range(8):
        bi_raw_orig = np.array(Image.open(os.path.join(RIGS_DIR, f"bryan_idle_d{d}.png")))
        br_raw = np.array(Image.open(os.path.join(RIGS_DIR, f"bryan_run_d{d}.png")))
        cr_raw = np.array(Image.open(os.path.join(RIGS_DIR, f"crimson_d{d}.png")))

        bi_clean, raw_6 = build_solo_bryan_idle_and_run6(br_raw, bi_raw_orig, d)

        bi_p, bi_cx = crop_tight_rgba(bi_clean)
        br_p, br_cx = crop_tight_rgba(br_raw)
        cr_p, cr_cx = crop_tight_rgba(cr_raw)

        bryan_idle[d] = scale_to_height(bi_p, bi_cx, 212)
        bryan_run_a[d] = scale_to_height(br_p, br_cx, 210)
        crimson[d] = scale_to_height(cr_p, cr_cx, 224)

        bryan_run_6[d] = []
        for k_arr in raw_6:
            kp, kcx = crop_tight_rgba(k_arr)
            bryan_run_6[d].append(scale_to_height(kp, kcx, 210))

    reaper_raw = np.array(Image.open(os.path.join(RIGS_DIR, "trio_reaper.png")))
    ram_raw = np.array(Image.open(os.path.join(RIGS_DIR, "trio_grey_ram.png")))
    rp_p, rp_cx = crop_tight_rgba(reaper_raw)
    rm_p, rm_cx = crop_tight_rgba(ram_raw)
    trio_reaper = scale_to_height(rp_p, rp_cx, 208)
    trio_ram = scale_to_height(rm_p, rm_cx, 214)

    # Extract standalone silver tinfoil hat + broken detector box from bryan_idle_d0 for Act 4 death!
    b0_im, b0_cx = bryan_idle[0]
    b0_arr = np.array(b0_im)
    hat_only = b0_arr[:38, max(0, b0_cx - 23):min(b0_im.width, b0_cx + 23)].copy()
    box_only = b0_arr[76:112, max(0, b0_cx - 23):min(b0_im.width, b0_cx + 23)].copy()

    return {
        "bryan_idle": bryan_idle,
        "bryan_run_a": bryan_run_a,
        "bryan_run_6": bryan_run_6,
        "crimson": crimson,
        "reaper": trio_reaper,
        "ram": trio_ram,
        "hat_crop": Image.fromarray(hat_only, "RGBA"),
        "box_crop": Image.fromarray(box_only, "RGBA"),
    }


def draw_ground_shadow(canvas, cx, gy, rx, ry, alpha=95, color=(8, 6, 10)):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    dr.ellipse([cx - rx, gy - ry, cx + rx, gy + ry], fill=(color[0], color[1], color[2], alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=4.5))
    canvas.alpha_composite(layer)


def paste_centered(canvas, pil_im, pivot_x, x, bottom_y, scale=1.0, rot_deg=0.0, alpha_mul=1.0, tint=None):
    im = pil_im
    px = pivot_x
    if abs(scale - 1.0) > 1e-3:
        nw = max(2, int(round(im.width * scale)))
        nh = max(2, int(round(im.height * scale)))
        im = im.resize((nw, nh), Image.LANCZOS)
        px = int(round(px * scale))
    if tint is not None or alpha_mul < 0.999:
        arr = np.array(im, dtype=np.float32)
        if tint is not None:
            arr[..., 0] = np.clip(arr[..., 0] * tint[0], 0, 255)
            arr[..., 1] = np.clip(arr[..., 1] * tint[1], 0, 255)
            arr[..., 2] = np.clip(arr[..., 2] * tint[2], 0, 255)
        if alpha_mul < 0.999:
            arr[..., 3] *= alpha_mul
        im = Image.fromarray(arr.astype(np.uint8), "RGBA")
    if abs(rot_deg) > 0.2:
        im = im.rotate(rot_deg, resample=Image.BICUBIC, expand=True)
        px = im.width // 2
    dx = int(round(x - px))
    dy = int(round(bottom_y - im.height))
    canvas.alpha_composite(im, (dx, dy))
    return dx, dy, im.width, im.height


def detector_world_pos(d_idx, bryan_x, bryan_bot_y):
    """Returns approximate (box_x, box_y, ant_tip_x, ant_tip_y, box_visible_front) on the 360x324 canvas."""
    table = {
        0: (0, -112, -11, -154, True),
        1: (-14, -112, -23, -154, True),
        2: (-29, -114, -31, -158, False),
        3: (-27, -118, -30, -156, False),
        4: (0, -116, -17, -174, False),
        5: (27, -118, 30, -156, False),
        6: (29, -114, 31, -158, False),
        7: (14, -112, 23, -154, True),
    }
    bx, by, ax, ay, vis = table[d_idx]
    return bryan_x + bx, bryan_bot_y + by, bryan_x + ax, bryan_bot_y + ay, vis


def draw_detector_fx(canvas, d_idx, bryan_x, bryan_bot_y, phase, intensity=1.0, overload=False):
    """Draws glowing R/G/B Demon Detector LEDs, radar EMF rings, and optional Tesla arcs from Bryan's antenna!"""
    bx, by, ax, ay, front_vis = detector_world_pos(d_idx, bryan_x, bryan_bot_y)
    fx = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(fx)

    # Pulsing Red / Green / Blue LED glows on the detector box when visible
    leds = [
        (-8, (255, 42, 56), 0.5 + 0.5 * math.sin(phase * 2 * math.pi)),
        (0, (42, 255, 96), 0.5 + 0.5 * math.sin(phase * 2 * math.pi + 2.1)),
        (8, (48, 165, 255), 0.5 + 0.5 * math.sin(phase * 2 * math.pi + 4.2)),
    ]
    if front_vis:
        for ox, col, p in leds:
            a_glow = int(min(245, (110 + 135 * p) * intensity))
            r_rad = 5 if not overload else 8
            dr.ellipse([bx + ox - r_rad, by - r_rad, bx + ox + r_rad, by + r_rad], fill=(col[0], col[1], col[2], a_glow))
            dr.ellipse([bx + ox - 2, by - 2, bx + ox + 2, by + 2], fill=(255, 255, 255, min(255, a_glow + 30)))
    elif d_idx != 4:
        # Side glow spill on profile/3-4 box
        col = (255, 50, 70) if math.sin(phase * 2 * math.pi) > 0 else (50, 220, 255)
        dr.ellipse([bx - 5, by - 5, bx + 5, by + 5], fill=(col[0], col[1], col[2], int(150 * intensity)))

    # Antenna tip beacon + expanding EMF radar wave rings!
    beacon_col = (255, 60, 80) if (overload or math.sin(phase * 2 * math.pi) > 0.15) else (70, 245, 255)
    dr.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], fill=(beacon_col[0], beacon_col[1], beacon_col[2], int(210 * intensity)))
    dr.ellipse([ax - 2, ay - 2, ax + 2, ay + 2], fill=(255, 255, 255, 255))

    fx_blur = fx.filter(ImageFilter.GaussianBlur(radius=2.2))
    canvas.alpha_composite(fx_blur)

    # Crisp EMF concentric rings
    ring_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring_layer)
    for r_i in range(2):
        prog = (phase + 0.5 * r_i) % 1.0
        rad_x = int(6 + prog * (28 if not overload else 46))
        rad_y = max(3, int(rad_x * 0.62))
        r_alpha = int((1.0 - prog) * (155 if not overload else 220) * intensity)
        if r_alpha > 12:
            rc = (255, 75, 110, r_alpha) if overload else (90, 245, 255, r_alpha)
            rd.ellipse([ax - rad_x, ay - rad_y, ax + rad_x, ay + rad_y], outline=rc, width=2)

    if overload:
        rng = random.Random(int(phase * 1000) + d_idx * 37)
        bolt_cols = [(90, 245, 255, 235), (255, 70, 220, 225), (120, 255, 130, 225)]
        for b_i in range(4):
            ang_b = rng.uniform(0, 2 * math.pi)
            dist_b = rng.uniform(24, 56)
            px, py = float(ax), float(ay)
            pts = [(int(px), int(py))]
            for s in range(1, 5):
                t = s / 4.0
                nx = ax + math.cos(ang_b) * dist_b * t + rng.uniform(-7, 7)
                ny = ay + math.sin(ang_b) * dist_b * t * 0.8 + rng.uniform(-7, 7)
                pts.append((int(nx), int(ny)))
            col_b = bolt_cols[b_i % len(bolt_cols)]
            rd.line(pts, fill=col_b, width=3)
            rd.line(pts, fill=(255, 255, 255, 240), width=1)

    canvas.alpha_composite(ring_layer)


def draw_demon_aura_and_eyes(canvas, cx, cy_top, w, h, d_idx, col=(255, 36, 24), alpha=65):
    """Adds subtle fiery rim-glow aura around a demon."""
    aura = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ad = ImageDraw.Draw(aura)
    ad.ellipse([cx - int(w * 0.44), cy_top + int(h * 0.06), cx + int(w * 0.44), cy_top + int(h * 0.88)],
               fill=(col[0], col[1], col[2], alpha))
    aura = aura.filter(ImageFilter.GaussianBlur(radius=9.0))
    canvas.alpha_composite(aura)


def local_to_screen_3d(lx, ly, d_idx):
    """Projects a local offset (lx=forward, ly=left) in Bryan's body frame to screen (sx, depth_z)
    for viewer angle index d_idx (rel = d_idx * 45 deg CCW from +X).
    Convention matching Quake Customize & LABELS:
      d=0 (viewer at +X looking -X): Bryan forward (+lx) -> depth_z < 0 (closer to camera),
                                     Bryan left (+ly)    -> screen LEFT (-sx)! Wait:
      Let's check! At d=1 (45° Front-Left, viewer at +X,+Y), Bryan's nose (+lx) points SCREEN LEFT (-sx)!
      Formula:
        phi = math.radians(d_idx * 45.0)
        viewer_pos = (cos(phi), sin(phi))
        view_fwd   = (-cos(phi), -sin(phi))   # into screen (+depth_z)
        view_right = (-sin(phi), +cos(phi))   # wait: at phi=45°, dot((1,0), view_right) = -sin(45°) < 0 (SCREEN LEFT)!
      Wait: at phi=0° (Front): view_right = (0, +1) -> Bryan's left (+ly) has dot((0,1),(0,1)) = +1 (Screen Right, i.e. viewer's right = Bryan's left!).
      YES!! In a front photo of Bryan, Bryan's LEFT arm is on the VIEWER'S RIGHT (+sx)!
      And depth_z (distance into screen away from camera):
        depth_z = lx * (-cos(phi)) + ly * (-sin(phi))
      When depth_z > 0, the point is FURTHER from the camera (BEHIND Bryan)!
      When depth_z < 0, the point is CLOSER to the camera (IN FRONT OF Bryan)!
    """
    phi = math.radians(d_idx * 45.0)
    sx = -lx * math.sin(phi) + ly * math.cos(phi)
    depth_z = -lx * math.cos(phi) - ly * math.sin(phi)
    return sx, depth_z


def build_scan_and_idle_frames(assets):
    """Builds SOLO Tinfoil-Hat Bryan (NO demons around him!):
      - 8-dir Standing Idle keyposes (0..7)
      - 8-dir x 6-frame Solo Paranoid RGB Detector Scan (56..103)
    """
    idle_8 = []
    scan_grid = [[None] * 6 for _ in range(8)]
    cx_base = CW // 2

    for d in range(8):
        b_im, b_piv = assets["bryan_idle"][d]

        for k in range(6):
            phase = k / 6.0
            canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))

            # Subtle paranoid head/body scan sway while Bryan searches the empty room for demons
            b_rot = 2.0 * math.sin(phase * 2 * math.pi)
            b_bob = int(round(1.5 * abs(math.sin(phase * math.pi))))

            draw_ground_shadow(canvas, cx_base, GROUND_Y, 32, 8, alpha=95)
            paste_centered(canvas, b_im, b_piv, cx_base, GROUND_Y - b_bob, scale=1.0, rot_deg=b_rot)
            draw_detector_fx(canvas, d, cx_base, GROUND_Y - b_bob, phase, intensity=1.05, overload=False)

            scan_grid[d][k] = canvas
            if k == 0:
                idle_8.append(canvas)

    return idle_8, scan_grid


def build_sprint_chase_frames(assets):
    """Builds 8-dir x 6-frame MAIN SOLO Tinfoil-Hat Bryan Run Cycle (frames 8..55 in .spr32, NO demons around him!)."""
    run_grid = [[None] * 6 for _ in range(8)]
    cx_base = CW // 2

    bounce_b = [-5, -2, +2, -5, -2, +2]
    lean_b = [1.8, 0.9, -0.6, -1.8, -0.9, 0.6]

    for d in range(8):
        poses_6 = assets["bryan_run_6"][d]

        for k in range(6):
            phase = k / 6.0
            canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))

            draw_ground_shadow(canvas, cx_base, GROUND_Y, 30, 7, alpha=88)

            # Subtle sneaker footstep dust puffs at GROUND_Y
            dust = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            dd = ImageDraw.Draw(dust)
            rng = random.Random(700 + d * 31 + k * 13)
            for _ in range(3):
                px = cx_base + rng.randint(-20, 20)
                py = GROUND_Y - rng.randint(0, 6)
                pr = rng.randint(3, 6)
                dd.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(195, 188, 175, 85))
            canvas.alpha_composite(dust.filter(ImageFilter.GaussianBlur(radius=0.8)))

            b_pose, b_piv = poses_6[k]
            b_gy = GROUND_Y + bounce_b[k]

            paste_centered(canvas, b_pose, b_piv, cx_base, b_gy, scale=1.0, rot_deg=lean_b[k])
            draw_detector_fx(canvas, d, cx_base, b_gy, (phase * 2.0) % 1.0, intensity=1.12, overload=False)

            run_grid[d][k] = canvas

    return run_grid


def draw_chain_and_nunchuck(canvas, x0, y0, x1, y1, phase):
    """Draws taut iron chain links + spinning nunchuck sticks connecting Bryan's grip to the whirling Demon!"""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    steps = 11
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 0.72) / steps
        lx0 = x0 + (x1 - x0) * t0
        ly0 = y0 + (y1 - y0) * t0 + 4.0 * math.sin(t0 * math.pi)
        lx1 = x0 + (x1 - x0) * t1
        ly1 = y0 + (y1 - y0) * t1 + 4.0 * math.sin(t1 * math.pi)
        col = (195, 205, 220, 245) if i % 2 == 0 else (110, 118, 132, 245)
        dr.line([(lx0, ly0), (lx1, ly1)], fill=(30, 32, 38, 255), width=5)
        dr.line([(lx0, ly0), (lx1, ly1)], fill=col, width=2)

    # Whirling nunchuck handles near midpoint/grip (straight from Video 1!)
    mx = x0 * 0.62 + x1 * 0.38
    my = y0 * 0.62 + y1 * 0.38
    ang = phase * 4.0 * math.pi
    nx, ny = math.cos(ang) * 16.0, math.sin(ang) * 16.0
    dr.line([(mx - nx, my - ny), (mx + nx, my + ny)], fill=(45, 32, 22, 255), width=5)
    dr.line([(mx - nx * 0.85, my - ny * 0.85), (mx + nx * 0.85, my + ny * 0.85)], fill=(210, 175, 110, 255), width=2)
    canvas.alpha_composite(layer)


def build_demon_whirl_frames(assets):
    """Builds 8-dir x 8-frame 'A DEMON! NO WAY!' 3D Giant-Swing Demon-Whirl Slam (frames 104..167)."""
    whirl_grid = [[None] * 8 for _ in range(8)]
    cx_base = CW // 2

    for d in range(8):
        for k in range(8):
            phase = k / 8.0
            canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))

            # Bryan pivots dynamically through 360° as he swings the demon around!
            b_dir = (d + k) % 8
            b_im, b_piv = assets["bryan_run_a" if (k % 2 == 0) else "bryan_idle"][b_dir]

            # Demon is swung in a wide 3D horizontal orbit directly in front of Bryan's facing direction b_dir!
            # Screen angle of demon relative to viewer = b_dir * 45°
            theta = math.radians(b_dir * 45.0)
            # Orbit coordinates on screen:
            # At b_dir=0 (Bryan facing camera), demon is whipped right across the front (dz < 0, sx = 0 -> offset slightly along velocity so motion arc reads!)
            orbit_ang = theta + 0.38
            sx = -math.sin(orbit_ang) * 86.0
            dz = -math.cos(orbit_ang) * 70.0  # dz < 0 => IN FRONT of Bryan; dz > 0 => BEHIND Bryan!

            b_x = int(round(cx_base - sx * 0.22))
            b_gy = GROUND_Y - 2

            # Swinging demon airborne center
            d_cx = int(round(b_x + sx))
            d_cy = int(round(GROUND_Y - 108 + dz * 0.22 + 10.0 * math.sin(phase * 2 * math.pi)))
            d_scale = float(np.clip(0.84 - 0.0022 * dz, 0.70, 0.98))

            # Pick demon directional frame & tilt horizontally (~68°) like a giant hammer-throw!
            c_dir = (b_dir + 2) % 8
            c_im, _ = assets["crimson"][c_dir]
            tilt = 66.0 if sx >= 0 else -66.0
            c_rot = c_im.resize(
                (max(2, int(c_im.width * d_scale)), max(2, int(c_im.height * d_scale))),
                Image.LANCZOS,
            ).rotate(tilt, resample=Image.BICUBIC, expand=True)

            # Clamp demon inside canvas with margin so zero pixels ever clip!
            d_px = int(np.clip(d_cx - c_rot.width // 2, 4, CW - c_rot.width - 4))
            d_py = int(np.clip(d_cy - c_rot.height // 2, 6, GROUND_Y - c_rot.height + 10))
            d_cx_clamped = d_px + c_rot.width // 2
            d_cy_clamped = d_py + c_rot.height // 2

            draw_ground_shadow(canvas, b_x, GROUND_Y, 34, 8, alpha=95)
            draw_ground_shadow(canvas, d_cx_clamped, GROUND_Y + 2, 42, 9, alpha=68, color=(45, 8, 8))

            # Blazing crimson-orange 360° whirlwind motion arc at waist height!
            swoosh = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            sd = ImageDraw.Draw(swoosh)
            arc_box = [b_x - 108, GROUND_Y - 148, b_x + 108, GROUND_Y - 58]
            deg_now = math.degrees(math.atan2((d_cy_clamped - (GROUND_Y - 103)) / 45.0, (d_cx_clamped - b_x) / 108.0))
            sd.arc(arc_box, start=deg_now - 115, end=deg_now + 10, fill=(255, 48, 24, 155), width=14)
            sd.arc(arc_box, start=deg_now - 75, end=deg_now + 8, fill=(255, 195, 60, 190), width=6)
            swoosh = swoosh.filter(ImageFilter.GaussianBlur(radius=2.5))

            bx_grip, by_grip, _, _, _ = detector_world_pos(b_dir, b_x, b_gy)

            if dz > 0:
                # Demon swings BEHIND Bryan
                canvas.alpha_composite(swoosh)
                canvas.alpha_composite(c_rot, (d_px, d_py))
                draw_chain_and_nunchuck(canvas, bx_grip, by_grip, d_cx_clamped, d_cy_clamped, phase)
                paste_centered(canvas, b_im, b_piv, b_x, b_gy, scale=1.0, rot_deg=-5.0 if sx > 0 else 5.0)
                draw_detector_fx(canvas, b_dir, b_x, b_gy, phase, intensity=1.25, overload=False)
            else:
                # Demon whips IN FRONT OF Bryan!
                paste_centered(canvas, b_im, b_piv, b_x, b_gy, scale=1.0, rot_deg=-5.0 if sx > 0 else 5.0)
                draw_detector_fx(canvas, b_dir, b_x, b_gy, phase, intensity=1.25, overload=False)
                canvas.alpha_composite(swoosh)
                draw_chain_and_nunchuck(canvas, bx_grip, by_grip, d_cx_clamped, d_cy_clamped, phase)
                canvas.alpha_composite(c_rot, (d_px, d_py))

            # Impact sparks flying off whirling demon!
            sp = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            spd = ImageDraw.Draw(sp)
            rng = random.Random(1900 + d * 41 + k * 17)
            for _ in range(9):
                ang_s = rng.uniform(0, 2 * math.pi)
                r_s = rng.uniform(12, 42)
                sx0 = d_cx_clamped + math.cos(ang_s) * r_s
                sy0 = d_cy_clamped + math.sin(ang_s) * r_s * 0.7
                spd.line([(sx0, sy0), (sx0 + math.cos(ang_s) * 8, sy0 + math.sin(ang_s) * 6)],
                         fill=(255, 225, 95, 230), width=2)
            canvas.alpha_composite(sp)

            whirl_grid[d][k] = canvas

    return whirl_grid


def draw_pentagram_portal(canvas, cx, gy, rx, ry, phase, intensity=1.0):
    """Draws a glowing 3D perspective molten pentagram portal on the ground at (cx, gy)."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    if rx < 4 or ry < 2:
        return
    # Outer fiery glow & dark lava core
    dr.ellipse([cx - rx - 8, gy - ry - 4, cx + rx + 8, gy + ry + 4],
               fill=(255, 45, 12, int(135 * intensity)))
    dr.ellipse([cx - rx, gy - ry, cx + rx, gy + ry],
               fill=(36, 6, 8, int(230 * intensity)),
               outline=(255, 130, 25, int(245 * intensity)), width=3)
    dr.ellipse([cx - int(rx * 0.78), gy - int(ry * 0.78), cx + int(rx * 0.78), gy + int(ry * 0.78)],
               outline=(255, 215, 70, int(210 * intensity)), width=2)

    # Rotating 5-pointed pentagram projected onto the ground ellipse!
    pts = []
    rot0 = phase * 2.0 * math.pi
    for i in range(5):
        a = rot0 + i * (2.0 * math.pi / 5.0)
        pts.append((cx + math.cos(a) * rx * 0.76, gy + math.sin(a) * ry * 0.76))
    star_order = [0, 2, 4, 1, 3, 0]
    star_pts = [pts[idx] for idx in star_order]
    dr.line(star_pts, fill=(255, 190, 55, int(225 * intensity)), width=2)

    glow = layer.filter(ImageFilter.GaussianBlur(radius=3.2))
    canvas.alpha_composite(glow)
    canvas.alpha_composite(layer)


def build_trio_surge_frames(assets):
    """Builds 8-dir x 8-frame Demon-Trio EMF Overload Surge (frames 168..231):
    Tinfoil-Hat Bryan w/ arcing Tesla Demon Detector surrounded by ALL THREE DEMONS in 3D orbit!
    """
    surge_grid = [[None] * 8 for _ in range(8)]
    cx_base = CW // 2

    for d in range(8):
        b_im, b_piv = assets["bryan_idle"][d]
        r_im, r_piv = assets["reaper"]
        m_im, m_piv = assets["ram"]

        for k in range(8):
            phase = k / 8.0
            canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))

            # Glowing ground rune circle beneath Bryan & the 3 orbiting Demons!
            draw_pentagram_portal(canvas, cx_base, GROUND_Y, 108, 22, phase, intensity=0.72)
            draw_ground_shadow(canvas, cx_base, GROUND_Y, 32, 8, alpha=95)

            # 3 Demons spaced 120° apart in Bryan's local frame, orbiting with phase!
            base_orbit = phase * 2.0 * math.pi
            trio_specs = [
                ("crimson", 0.0),
                ("reaper", 2.0 * math.pi / 3.0),
                ("ram", 4.0 * math.pi / 3.0),
            ]
            render_list = [(0.0, "bryan", cx_base, GROUND_Y - int(2 * abs(math.sin(phase * 2 * math.pi))), 1.0)]

            for kind, off_ang in trio_specs:
                ang_local = base_orbit + off_ang
                lx = math.cos(ang_local) * 74.0
                ly = math.sin(ang_local) * 86.0
                sx, dz = local_to_screen_3d(lx, ly, d)
                # Keep center window slightly clear when right in front of Bryan's face so Bryan + Detector always pop!
                if dz < -15 and abs(sx) < 34:
                    sx = -38.0 if sx < 0 else 38.0
                px = int(np.clip(round(cx_base + sx), 44, CW - 44))
                py = int(round(GROUND_Y - dz * 0.16 - 4.0 * abs(math.sin(phase * 2 * math.pi + off_ang))))
                sc = float(np.clip(0.84 - 0.0018 * dz, 0.72, 0.94))
                render_list.append((dz, kind, px, py, sc))

            render_list.sort(key=lambda item: -item[0])  # Back-to-front painter's sort!

            for dz, kind, px, py, sc in render_list:
                if kind == "bryan":
                    jolt = 2.0 * math.sin(phase * 4 * math.pi)
                    paste_centered(canvas, b_im, b_piv, px, py, scale=1.0, rot_deg=jolt)
                    draw_detector_fx(canvas, d, px, py, phase, intensity=1.35, overload=True)
                elif kind == "crimson":
                    c_dir = int(round((d + phase * 8) % 8)) % 8
                    c_im, c_piv = assets["crimson"][c_dir]
                    draw_demon_aura_and_eyes(canvas, px, py - int(224 * sc), int(140 * sc), int(224 * sc), c_dir, alpha=55)
                    paste_centered(canvas, c_im, c_piv, px, py, scale=sc)
                elif kind == "reaper":
                    draw_demon_aura_and_eyes(canvas, px, py - int(208 * sc), int(130 * sc), int(208 * sc), 0, col=(140, 60, 255), alpha=50)
                    paste_centered(canvas, r_im, r_piv, px, py, scale=sc, alpha_mul=0.94)
                elif kind == "ram":
                    draw_demon_aura_and_eyes(canvas, px, py - int(214 * sc), int(130 * sc), int(214 * sc), 0, col=(255, 115, 30), alpha=50)
                    paste_centered(canvas, m_im, m_piv, px, py, scale=sc)

            surge_grid[d][k] = canvas

    return surge_grid


def build_portal_death_frames(assets):
    """Builds 32-frame 4-Act Hell Portal Overload & Demon Trio Drag-Down Death (frames 232..263):
      0..7:   Act 1 - Detector RGB overload sparks, Bryan jolts, tinfoil hat pops upward, lava pentagram opens!
      8..15:  Act 2 - All 3 Demons erupt around Bryan, latching on as portal widens into roaring hellfire!
      16..23: Act 3 - Demons drag Bryan down through GROUND_Y into the molten portal (clipped cleanly at portal plane)!
      24..31: Act 4 - Massive hellfire/EMF shockwave blast -> portal seals -> scorched smoking Tinfoil Hat & broken Detector rest on floor!
    """
    frames = []
    cx = CW // 2
    b_im, b_piv = assets["bryan_idle"][0]
    c_im, c_piv = assets["crimson"][0]
    r_im, r_piv = assets["reaper"]
    m_im, m_piv = assets["ram"]
    hat_crop = assets["hat_crop"]
    box_crop = assets["box_crop"]

    for f in range(32):
        canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        rng = random.Random(5000 + f * 29)

        if f < 8:
            # Act 1: Detector Overload & Portal Opening
            t = f / 7.0
            rx = int(20 + 95 * t)
            ry = int(5 + 20 * t)
            draw_pentagram_portal(canvas, cx, GROUND_Y, rx, ry, t * 0.5, intensity=0.5 + 0.5 * t)
            shake_x = cx + int(round(5.0 * math.sin(f * 2.3)))
            paste_centered(canvas, b_im, b_piv, shake_x, GROUND_Y, scale=1.0, rot_deg=4.0 * math.sin(f * 1.9))
            draw_detector_fx(canvas, 0, shake_x, GROUND_Y, t, intensity=1.5, overload=True)

        elif f < 16:
            # Act 2: Demon Trio Swarm!
            t = (f - 8) / 7.0
            draw_pentagram_portal(canvas, cx, GROUND_Y, 118, 25, 0.5 + t * 0.8, intensity=1.0)
            emerge = int(round((1.0 - t) * 48))  # Demons rise up out of portal!

            sub = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            paste_centered(sub, r_im, r_piv, cx - 64 + int(12 * t), GROUND_Y + emerge, scale=0.84)
            paste_centered(sub, m_im, m_piv, cx + 64 - int(12 * t), GROUND_Y + emerge, scale=0.84)
            paste_centered(sub, c_im, c_piv, cx, GROUND_Y - 6 + emerge, scale=0.92)
            # Clip emerging demons below GROUND_Y + 4
            sub_arr = np.array(sub)
            sub_arr[GROUND_Y + 4:, :, 3] = 0
            canvas.alpha_composite(Image.fromarray(sub_arr, "RGBA"))

            shake_x = cx + int(round(6.0 * math.sin(f * 2.7)))
            sink_start = int(round(t * 22))
            b_sub = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            paste_centered(b_sub, b_im, b_piv, shake_x, GROUND_Y + sink_start, scale=1.0, rot_deg=-6.0 * math.sin(f * 2.1))
            b_arr = np.array(b_sub)
            b_arr[GROUND_Y + 3:, :, 3] = 0
            canvas.alpha_composite(Image.fromarray(b_arr, "RGBA"))
            draw_detector_fx(canvas, 0, shake_x, GROUND_Y + sink_start, t, intensity=1.6, overload=True)

        elif f < 24:
            # Act 3: Dragged Down Into the Molten Portal + Roaring Flame Pillars!
            t = (f - 16) / 7.0
            draw_pentagram_portal(canvas, cx, GROUND_Y, int(118 - 18 * t), int(25 - 3 * t), 1.3 + t, intensity=1.0)

            sink_b = int(round(24 + t * 185))
            sink_d = int(round(t * 165))
            sub = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            paste_centered(sub, r_im, r_piv, cx - 46 + int(18 * t), GROUND_Y + sink_d, scale=0.84)
            paste_centered(sub, m_im, m_piv, cx + 46 - int(18 * t), GROUND_Y + sink_d, scale=0.84)
            paste_centered(sub, b_im, b_piv, cx + int(4 * math.sin(f * 3)), GROUND_Y + sink_b, scale=1.0 - 0.12 * t, rot_deg=12.0 * t)
            paste_centered(sub, c_im, c_piv, cx - 12, GROUND_Y + sink_d - 10, scale=0.88)
            sub_arr = np.array(sub)
            sub_arr[GROUND_Y + 2:, :, 3] = 0
            canvas.alpha_composite(Image.fromarray(sub_arr, "RGBA"))

            # Popped silver tinfoil hat launching skyward at peak drag-down!
            hat_y = GROUND_Y - 170 - int(round(55 * math.sin(t * math.pi)))
            hat_r = hat_crop.rotate(f * 28.0, resample=Image.BICUBIC, expand=True)
            canvas.alpha_composite(hat_r, (cx - hat_r.width // 2 + int(14 * t), max(6, hat_y)))

            # Hellfire plume erupting from portal!
            fire = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            fd = ImageDraw.Draw(fire)
            plume_h = int(70 + 135 * math.sin(t * math.pi * 0.85))
            for p_i in range(22):
                prog_y = rng.random()
                px = cx + int(rng.gauss(0, 26 * (1.0 - 0.35 * prog_y)))
                py = GROUND_Y - int(4 + prog_y * plume_h)
                pr = rng.randint(7, 20)
                col_f = (255, int(45 + 165 * (1.0 - prog_y)), 16, rng.randint(125, 220))
                fd.polygon([
                    (px, py - int(pr * 1.7)),
                    (px + pr, py + int(pr * 0.4)),
                    (px, py + pr),
                    (px - pr, py + int(pr * 0.4)),
                ], fill=col_f)
                if p_i < 9:
                    ir = max(3, pr // 2)
                    fd.ellipse([px - ir, py - ir, px + ir, py + ir], fill=(255, 240, 145, 210))
            fire = fire.filter(ImageFilter.GaussianBlur(radius=2.2))
            sp_dr = ImageDraw.Draw(fire)
            for _ in range(14):
                sx = cx + rng.randint(-55, 55)
                sy = GROUND_Y - rng.randint(10, plume_h + 24)
                sp_dr.line([(sx, sy), (sx + rng.randint(-3, 3), sy - rng.randint(4, 10))], fill=(255, 230, 110, 235), width=2)
            canvas.alpha_composite(fire)

        else:
            # Act 4: Hellfire Shockwave Detonation -> Scorched Smoking Tinfoil Hat & Broken Detector on Floor!
            t = (f - 24) / 7.0
            # Scorched blast crater on floor
            draw_ground_shadow(canvas, cx, GROUND_Y, 64, 13, alpha=155, color=(14, 10, 10))
            if t < 0.65:
                fade = 1.0 - (t / 0.65)
                draw_pentagram_portal(canvas, cx, GROUND_Y, int(95 * fade), int(20 * fade), 2.3 + t, intensity=fade)
                blast = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
                bd = ImageDraw.Draw(blast)
                r_b = int(35 + 115 * (t / 0.65))
                bd.ellipse([cx - r_b, GROUND_Y - 70 - int(r_b * 0.7), cx + r_b, GROUND_Y + 10],
                           outline=(255, 155, 40, int(210 * fade)), width=6)
                for _ in range(14):
                    ex = cx + rng.randint(-r_b, r_b)
                    ey = GROUND_Y - rng.randint(8, int(150 * fade) + 20)
                    er = rng.randint(4, 14)
                    bd.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, rng.randint(80, 210), 30, int(190 * fade)))
                canvas.alpha_composite(blast.filter(ImageFilter.GaussianBlur(radius=2.2)))

            # Broken sparking Demon Detector box settled on scorched floor (cx + 22, GROUND_Y)
            box_r = box_crop.rotate(-14.0, resample=Image.BICUBIC, expand=True)
            canvas.alpha_composite(box_r, (cx + 8, GROUND_Y - box_r.height + 3))
            if f % 2 == 0:
                sp = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
                sd = ImageDraw.Draw(sp)
                sd.ellipse([cx + 18, GROUND_Y - 16, cx + 26, GROUND_Y - 8], fill=(60, 220, 255, 215))
                canvas.alpha_composite(sp.filter(ImageFilter.GaussianBlur(radius=1.5)))

            # Tumbling Silver Tinfoil Hat landing & resting on floor at (cx - 18, GROUND_Y)!
            fall_t = min(1.0, t * 1.35)
            hat_y = int(round((GROUND_Y - 145) * (1.0 - fall_t ** 1.6) + (GROUND_Y - hat_crop.height + 4) * (fall_t ** 1.6)))
            hat_ang = (1.0 - fall_t) * 190.0 + 12.0
            hat_r = hat_crop.rotate(hat_ang, resample=Image.BICUBIC, expand=True)
            canvas.alpha_composite(hat_r, (cx - 32, hat_y))

            # Rising dark smoke wisps from hat & detector!
            smk = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            smd = ImageDraw.Draw(smk)
            for s_i in range(5):
                sy = GROUND_Y - 14 - int(((f * 7 + s_i * 13) % 52))
                sx = cx - 14 + int(8 * math.sin(s_i + f * 0.5))
                sr = 5 + s_i * 2
                smd.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(95, 92, 98, max(20, 95 - s_i * 15)))
            canvas.alpha_composite(smk.filter(ImageFilter.GaussianBlur(radius=2.5)))

        frames.append(canvas)

    return frames


def to_spr_frame_toned(pil_hi):
    """Resizes 360x324 showcase frame to 320x288 and applies DarkPlaces HDR lighting tone curve."""
    im = pil_hi.resize((SPR_W, SPR_H), Image.LANCZOS).convert("RGBA")
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageEnhance.Contrast(rgb).enhance(1.20)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.58)
    r2, g2, b2 = rgb.split()
    # Clean ultra-faint alpha fringe (< 12) so DarkPlaces alpha edges stay razor crisp
    a_arr = np.array(a)
    a_arr[a_arr < 12] = 0
    return Image.merge("RGBA", (r2, g2, b2, Image.fromarray(a_arr)))


def write_spr32(frames, path):
    w, h = frames[0].size
    rad = math.sqrt((w / 2.0) ** 2 + (h / 2.0) ** 2)
    with open(path, "wb") as fp:
        fp.write(b"IDSP")
        fp.write(struct.pack("<iifiiifi", 32, 0, rad, w, h, len(frames), 0.0, 0))
        for im in frames:
            fp.write(struct.pack("<iiiii", 0, SPR_OX, SPR_OY, w, h))
            fp.write(im.tobytes())


def save_contact_sheets_and_gifs(idle_8, scan_grid, run_grid, whirl_grid, surge_grid, death_frames):
    # 1. 360° 8-Angle Turnaround Sheet (Idle + Run + Whirl + Trio Surge = 4 rows x 8 cols)
    tw, th = 180, 162
    W_s, H_s = tw * 8, th * 4
    yy, xx = np.mgrid[0:H_s, 0:W_s]
    chk = np.where(((xx // 12 + yy // 12) % 2) == 0, 38, 26)[..., None].astype(np.uint8)
    sheet = Image.fromarray(np.repeat(chk, 3, axis=-1), "RGB")

    row_sources = [
        [scan_grid[d][2] for d in range(8)],
        [run_grid[d][0] for d in range(8)],
        [whirl_grid[d][0] for d in range(8)],
        [surge_grid[d][2] for d in range(8)],
    ]
    for r_i, row_ims in enumerate(row_sources):
        for c_i, im in enumerate(row_ims):
            rsz = im.resize((tw, th), Image.LANCZOS)
            gx, gy = c_i * tw, r_i * th
            sub = sheet.crop((gx, gy, gx + tw, gy + th)).convert("RGBA")
            sub.alpha_composite(rsz)
            sheet.paste(sub.convert("RGB"), (gx, gy))

    turn_png = os.path.join(WEB_DIR, "bryan_360_turnaround_sheet.png")
    sheet.save(turn_png)

    # 2. Death 4x8 Contact Sheet
    W_d, H_d = tw * 8, th * 4
    yy2, xx2 = np.mgrid[0:H_d, 0:W_d]
    chk2 = np.where(((xx2 // 12 + yy2 // 12) % 2) == 0, 36, 24)[..., None].astype(np.uint8)
    dsheet = Image.fromarray(np.repeat(chk2, 3, axis=-1), "RGB")
    for idx, im in enumerate(death_frames):
        r_i, c_i = divmod(idx, 8)
        rsz = im.resize((tw, th), Image.LANCZOS)
        gx, gy = c_i * tw, r_i * th
        sub = dsheet.crop((gx, gy, gx + tw, gy + th)).convert("RGBA")
        sub.alpha_composite(rsz)
        dsheet.paste(sub.convert("RGB"), (gx, gy))
    death_jpg = os.path.join(WEB_DIR, "bryan_death_contact_sheet.jpg")
    dsheet.save(death_jpg, quality=92)

    # 3. Animated GIFs (360° Sprint Orbit + Demon-Whirl)
    def save_rgba_gif(frames_list, out_gif, duration_ms=80):
        rgb_frames = []
        yy_g, xx_g = np.mgrid[0:CH, 0:CW]
        bg = np.where(((xx_g // 16 + yy_g // 16) % 2) == 0, 34, 24)[..., None].astype(np.uint8)
        bg_pil = Image.fromarray(np.repeat(bg, 3, axis=-1), "RGB").convert("RGBA")
        for f_im in frames_list:
            c = bg_pil.copy()
            c.alpha_composite(f_im)
            rgb_frames.append(c.convert("P", palette=Image.ADAPTIVE, colors=255))
        rgb_frames[0].save(out_gif, save_all=True, append_images=rgb_frames[1:], duration=duration_ms, loop=0)

    spin_seq = [run_grid[d][k % 6] for d in range(8) for k in range(3)]
    save_rgba_gif(spin_seq, os.path.join(WEB_DIR, "bryan_360_spin.gif"), duration_ms=75)
    save_rgba_gif(whirl_grid[0] + surge_grid[0], os.path.join(WEB_DIR, "bryan_demon_whirl.gif"), duration_ms=80)
    return turn_png, death_jpg


def main():
    print("Loading normalized 8-dir Tinfoil-Hat Bryan & Demon master rigs...")
    assets = load_normalized_assets()

    print("Synthesizing 360° Solo Bryan Idle & Paranoid RGB Detector Scan...")
    idle_8, scan_grid = build_scan_and_idle_frames(assets)

    print("Synthesizing 360° Solo Bryan Main Running Cycle...")
    run_grid = build_sprint_chase_frames(assets)

    print("Synthesizing 360° 'A DEMON! NO WAY!' Giant-Swing Demon-Whirl...")
    whirl_grid = build_demon_whirl_frames(assets)

    print("Synthesizing 360° 3-Demon Trio EMF Overload Surge...")
    surge_grid = build_trio_surge_frames(assets)

    print("Synthesizing 32-frame 4-Act Hell Portal Drag-Down Death...")
    death_frames = build_portal_death_frames(assets)

    # Save untoned web PNGs
    for d in range(8):
        idle_8[d].save(os.path.join(WEB_DIR, f"bryan_idle_d{d}.png"))
        for k in range(6):
            run_grid[d][k].save(os.path.join(WEB_DIR, f"bryan_run_d{d}_f{k}.png"))
            scan_grid[d][k].save(os.path.join(WEB_DIR, f"bryan_scan_d{d}_f{k}.png"))
        for k in range(8):
            whirl_grid[d][k].save(os.path.join(WEB_DIR, f"bryan_whirl_d{d}_f{k}.png"))
            surge_grid[d][k].save(os.path.join(WEB_DIR, f"bryan_surge_d{d}_f{k}.png"))
    for f, im in enumerate(death_frames):
        im.save(os.path.join(WEB_DIR, f"bryan_death_{f:02d}.png"))

    # Assemble exact 264-frame DarkPlaces .spr32 sequence:
    #   0..7      Idle (8)
    #   8..55     Run (8x6 = 48)
    #   56..103   Scan (8x6 = 48)
    #   104..167  Demon-Whirl (8x8 = 64)
    #   168..231  Demon-Trio Surge (8x8 = 64)
    #   232..263  Hell Portal Death (32)
    spr_hi_all = []
    spr_hi_all.extend(idle_8)
    for d in range(8):
        spr_hi_all.extend(run_grid[d])
    for d in range(8):
        spr_hi_all.extend(scan_grid[d])
    for d in range(8):
        spr_hi_all.extend(whirl_grid[d])
    for d in range(8):
        spr_hi_all.extend(surge_grid[d])
    spr_hi_all.extend(death_frames)
    assert len(spr_hi_all) == 264, f"Expected 264 frames, got {len(spr_hi_all)}"

    print("Toning 264 frames for DarkPlaces HDR & writing progs/bryan.spr32...")
    spr_toned = [to_spr_frame_toned(im) for im in spr_hi_all]
    write_spr32(spr_toned, SPR_PATH)

    # Save first 56 toned spr32 preview PNGs for HTML viewer SPR32 mode
    for idx in range(56):
        spr_toned[idx].save(os.path.join(SPR_PREVIEW_DIR, f"f_{idx:03d}.png"))

    # Measure mean opaque brightness of toned frame 0 (matching mbox.qc calibration!)
    f0_arr = np.array(spr_toned[0])
    opaque = f0_arr[..., 3] > 128
    mean_lum = float(np.mean(f0_arr[opaque, :3]))
    print(f"progs/bryan.spr32 written: {os.path.getsize(SPR_PATH):,} bytes | 264 frames ({SPR_W}x{SPR_H}, origin=({SPR_OX},{SPR_OY})) | mean opaque RGB = {mean_lum:.1f}")

    turn_png, death_jpg = save_contact_sheets_and_gifs(idle_8, scan_grid, run_grid, whirl_grid, surge_grid, death_frames)
    print("Saved sheets:", turn_png, "|", death_jpg)


if __name__ == "__main__":
    main()
