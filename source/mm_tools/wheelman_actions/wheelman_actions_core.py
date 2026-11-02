r"""Core Chroma-Key, Bare-Skin Calibration, Seamless Shorts-to-Skin Diffusion,
Articulated Biomechanical Warping & DarkPlaces SPR32 Utilities for Wheelman Actions."""
import base64
import io
import math
import os
import struct
import cv2
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ORIG_REF_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "ref")

CANVAS_WH = (360, 360)
GROUND_Y = 332


def key_studio_magenta(im_rgb):
    """High-precision #FF00FF chroma key with edge un-premultiply and warm-skin-safe despill."""
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()
    m = np.minimum(r, b) - g

    # Pure magenta studio background (#FF00FF and slight JPEG/lighting variations)
    bg_strict = (m > 58.0) & (r > 95.0) & (b > 95.0)
    # Flood-fill from image borders as well so any slightly shadowed magenta corner is caught cleanly
    bg_loose = (m > 38.0) & (r > 75.0) & (b > 75.0)
    lbl_bg, n_bg = ndimage.label(bg_loose)
    if n_bg > 0:
        border_ids = set(np.unique(lbl_bg[0, :])) | set(np.unique(lbl_bg[-1, :])) | set(np.unique(lbl_bg[:, 0])) | set(np.unique(lbl_bg[:, -1]))
        border_ids.discard(0)
        if border_ids:
            bg_strict = bg_strict | np.isin(lbl_bg, list(border_ids))

    dist = ndimage.distance_transform_edt(~bg_strict)
    alpha = np.ones_like(m, dtype=np.float32)
    alpha[bg_strict] = 0.0

    edge = (~bg_strict) & (dist <= 8.0)
    a_ramp = np.clip(1.0 - (m - 10.0) / 50.0, 0.0, 1.0)
    use_ramp = edge & (m > 10.0)
    alpha[use_ramp] = np.where(a_ramp[use_ramp] <= 0.05, 0.0, a_ramp[use_ramp])

    semi = (alpha > 0.0) & (alpha < 0.995)
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.25)
    r[semi] = np.clip((r[semi] - inv * 255.0) / denom, 0.0, 255.0)
    g[semi] = np.clip(g[semi] / denom, 0.0, 255.0)
    b[semi] = np.clip((b[semi] - inv * 255.0) / denom, 0.0, 255.0)

    dsp = (alpha > 0.0) & (dist <= 7.0)
    spill = np.maximum(0.0, b[dsp] - g[dsp])
    is_mag = (r[dsp] - g[dsp]) > 8.0
    b[dsp] = np.where(is_mag, b[dsp] - spill, b[dsp])
    r[dsp] = np.where(is_mag, np.maximum(g[dsp], r[dsp] - 0.62 * spill), r[dsp])

    lbl, num = ndimage.label(alpha > 0.08)
    if num > 1:
        sizes = ndimage.sum(alpha > 0.08, lbl, range(1, num + 1))
        main_id = 1 + int(np.argmax(sizes))
        keep = ndimage.binary_dilation(lbl == main_id, iterations=7)
        alpha[~keep] = 0.0

    rgba = np.dstack([
        np.clip(np.round(r), 0, 255).astype(np.uint8),
        np.clip(np.round(g), 0, 255).astype(np.uint8),
        np.clip(np.round(b), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])
    return Image.fromarray(rgba, "RGBA")


_GROIN_RATIO_CACHE = None


def get_authentic_groin_ratio():
    """Extracts lighting-invariant photographic groin albedo ratio (patch / local_skin_base) from wheelman_body.jpg
    with an elliptical cosine feather to 1.0 at borders so front nudity grafts seamlessly onto any lighting."""
    global _GROIN_RATIO_CACHE
    if _GROIN_RATIO_CACHE is not None:
        return _GROIN_RATIO_CACHE
    body_path = os.path.join(ORIG_REF_DIR, "wheelman_body.jpg")
    rgb = np.asarray(Image.open(body_path).convert("RGB"), dtype=np.float32)
    # Clean surrounding lower-belly/inner-thigh skin reference in wheelman_body.jpg (1280x958)
    skin_ring = rgb[240:300, 520:670]
    base_col = np.median(skin_ring.reshape(-1, 3), axis=0)
    patch = rgb[282:452, 536:692].copy()  # 170 x 156 authentic front groin anatomy
    ph, pw = patch.shape[:2]
    yg, xg = np.mgrid[0:ph, 0:pw].astype(np.float32)
    nx = (xg - pw * 0.5) / (pw * 0.47)
    ny = (yg - ph * 0.48) / (ph * 0.48)
    r = np.hypot(nx, ny)
    feather = 0.5 * (1.0 + np.cos(np.pi * np.clip((r - 0.38) / 0.62, 0.0, 1.0)))
    feather[r >= 1.0] = 0.0
    raw_ratio = np.clip((patch / np.maximum(base_col[None, None, :], 15.0)) ** 0.72, 0.54, 1.12)
    _GROIN_RATIO_CACHE = 1.0 + (raw_ratio - 1.0) * (feather[..., None] * 0.88)
    return _GROIN_RATIO_CACHE


def load_authentic_skin_ref():
    """Loads authentic chest/thigh bare skin tone & high-frequency pore grain from wheelman_body.jpg."""
    body_path = os.path.join(ORIG_REF_DIR, "wheelman_body.jpg")
    rgb = np.asarray(Image.open(body_path).convert("RGB"), dtype=np.float32)
    # Clean bare chest & thigh regions in wheelman_body.jpg
    chest_patch = rgb[120:320, 420:700]
    lum = 0.299 * chest_patch[..., 0] + 0.587 * chest_patch[..., 1] + 0.114 * chest_patch[..., 2]
    skin_m = ((chest_patch[..., 0] - chest_patch[..., 2]) > 18.0) & (lum > 75.0) & (lum < 215.0)
    skin_samples = chest_patch[skin_m]
    grain_src = rgb[150:290, 450:630]
    grain_hi = grain_src - cv2.GaussianBlur(grain_src, (15, 15), 3.8)
    return skin_samples, grain_hi


def calibrate_skin_to_ref(rgba_im, ref_skin_samples, strength=0.52):
    """Harmonizes warm skin tone across generated plates to match authentic Wheelman skin."""
    arr = np.array(rgba_im).astype(np.float32)
    rgb = arr[..., :3]
    a = arr[..., 3] / 255.0
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    rg = rgb[..., 0] - rgb[..., 1]
    rb = rgb[..., 0] - rgb[..., 2]
    skin_m = (a > 0.85) & (rb > 18.0) & (rg > 11.0) & (lum > 65.0) & (lum < 218.0)
    if np.sum(skin_m) < 200:
        return rgba_im
    src_mean = rgb[skin_m].mean(axis=0)
    tgt_mean = ref_skin_samples.mean(axis=0)
    gain = np.clip(tgt_mean / np.maximum(src_mean, 1.0), 0.84, 1.22)
    w_s = (np.clip((rb - 12.0) / 16.0, 0.0, 1.0) * np.clip((lum - 44.0) / 28.0, 0.0, 1.0) * strength)[..., None]
    scaled = np.clip(rgb * gain[None, None, :], 0.0, 255.0)
    arr[..., :3] = rgb * (1.0 - w_s) + scaled * w_s
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def detect_mech_hardware_mask(arr_float, pelvis_box_px=None):
    """Automatically detects white wheel dishes, surrounding black rubber tires, mirror-chrome cylinder,
    and steel axle bar so shorts-to-skin diffusion NEVER touches the wheels or metal bar."""
    H, W = arr_float.shape[:2]
    rgb = arr_float[..., :3]
    a = arr_float[..., 3] > 40.0
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    chroma = np.max(rgb, axis=-1) - np.min(rgb, axis=-1)

    # 1) Bright white painted wheel dishes (high luminance, low saturation, upright wheel aspect ratio)
    white_dish = a & (lum > 182.0) & (chroma < 30.0)
    lbl_w, nw = ndimage.label(white_dish)
    tire_guard = np.zeros((H, W), dtype=bool)
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    for cid in range(1, nw + 1):
        comp = lbl_w == cid
        area = int(np.sum(comp))
        if area < 140:
            continue
        ys, xs = np.nonzero(comp)
        cy, cx = float(ys.mean()), float(xs.mean())
        ry = (ys.max() - ys.min()) * 0.5
        rx = (xs.max() - xs.min()) * 0.5
        # Filter out flat horizontal specular bars on steel axles (real upright wheel dishes have ry >= 22 and rx/ry <= 1.35)
        if ry < 22.0 or (rx / max(ry, 1.0)) > 1.35:
            continue
        # Measured exact tire-to-dish ratio across studio plates is 1.40x..1.54x
        tr_y = ry * 1.57
        tr_x = max(rx * 1.57, ry * 0.44)
        ell = (((xg - cx) / tr_x) ** 2 + ((yg - cy) / tr_y) ** 2) <= 1.04
        non_skin = ((rgb[..., 0] - rgb[..., 2]) < 17.0) | (lum < 85.0) | (lum > 175.0)
        tire_guard |= (ell & non_skin & a)

    # 2) Mirror-chrome specular highlights & metallic reflections (tight 3px guard so axles never bleed onto shorts cuffs)
    silver_hi = a & (lum > 152.0) & (chroma < 20.0)
    chrome_zone = ndimage.binary_dilation(silver_hi, iterations=3) & a & (((rgb[..., 0] - rgb[..., 2]) < 14.0) & (chroma < 22.0))

    return tire_guard | chrome_zone


def diffuse_shorts_to_bare_skin(
    rgba_im,
    grain_hi,
    rel_box=(0.24, 0.34, 0.76, 0.74),
    has_attached_rig=True,
    is_rear=False,
    extra_protect_boxes=None,
    view_kind=None,
):
    """Converts matte-black athletic compression shorts in rel_box=(x0f, y0f, x1f, y1f) of character bbox
    into seamless bare warm skin + authentic front/rear nudity detail from wheelman_body.jpg."""
    arr = np.array(rgba_im).astype(np.float32)
    H, W = arr.shape[:2]
    rgb = arr[..., :3]
    a = arr[..., 3] / 255.0
    ys, xs = np.nonzero(a > 0.15)
    if len(xs) < 100:
        return rgba_im

    bx0, bx1 = float(xs.min()), float(xs.max())
    by0, by1 = float(ys.min()), float(ys.max())
    bw, bh = max(1.0, bx1 - bx0), max(1.0, by1 - by0)

    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    rx0 = bx0 + rel_box[0] * bw
    ry0 = by0 + rel_box[1] * bh
    rx1 = bx0 + rel_box[2] * bw
    ry1 = by0 + rel_box[3] * bh
    in_roi = (xg >= rx0) & (xg <= rx1) & (yg >= ry0) & (yg <= ry1)

    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    rb = rgb[..., 0] - rgb[..., 2]

    mech_mask = detect_mech_hardware_mask(arr) if has_attached_rig else np.zeros((H, W), dtype=bool)
    if extra_protect_boxes:
        for (px0, py0, px1, py1) in extra_protect_boxes:
            mech_mask |= (
                (xg >= bx0 + px0 * bw) & (xg <= bx0 + px1 * bw)
                & (yg >= by0 + py0 * bh) & (yg <= by0 + py1 * bh)
                & (a > 0.15)
            )

    dark_cloth = in_roi & (a > 0.18) & (~mech_mask) & (rb < 18.5) & (lum < 104.0)

    y_d, x_d = np.ogrid[-3:4, -3:4]
    disk3 = (x_d * x_d + y_d * y_d) <= 9
    cloth_core = ndimage.binary_opening(dark_cloth, structure=disk3)
    if not np.any(cloth_core):
        cloth_core = dark_cloth

    warm_skin = (a > 0.80) & (rb > 17.5) & (lum > 66.0) & (lum < 236.0)
    near_warm = ndimage.binary_dilation(warm_skin, iterations=8)
    lbl_c, nc = ndimage.label(cloth_core)
    hole_mask = np.zeros((H, W), dtype=bool)
    for cid in range(1, nc + 1):
        comp = lbl_c == cid
        if np.sum(comp) >= 30 and np.any(comp & near_warm):
            hole_mask |= comp

    if np.sum(hole_mask) < 30:
        return rgba_im

    hole = ndimage.binary_dilation(hole_mask, iterations=6) & (a > 0.12) & (~mech_mask) & ((rb < 24.0) & (lum < 132.0))
    hole = ndimage.binary_dilation(hole, iterations=5) & (a > 0.12) & (~mech_mask)
    known = (~hole) & warm_skin & (~ndimage.binary_dilation(hole, iterations=2))
    if np.sum(known) < 120:
        known = (~hole) & warm_skin
    if np.sum(known) < 120:
        return rgba_im

    seed_rgb = np.where(known[..., None], rgb, 0.0)
    seed_w = known.astype(np.float32)

    filled = np.zeros_like(rgb)
    total_conf = np.zeros_like(seed_w)
    for sigma in (96.0, 48.0, 24.0, 11.0, 4.8):
        ksize = int(sigma * 4) | 1
        num_s = cv2.GaussianBlur(seed_rgb, (ksize, ksize), sigma)
        den_s = cv2.GaussianBlur(seed_w, (ksize, ksize), sigma)
        valid = den_s > 1e-5
        layer = np.where(valid[..., None], num_s / np.maximum(den_s[..., None], 1e-5), 0.0)
        w_take = np.clip(den_s * 14.0, 0.0, 1.0)
        filled = np.where(total_conf[..., None] == 0, layer, filled * (1.0 - w_take[..., None]) + layer * w_take[..., None])
        total_conf = np.maximum(total_conf, w_take)

    dist_sil = ndimage.distance_transform_edt(a > 0.5)
    sil_shade = 0.84 + 0.16 * np.clip(dist_sil / 30.0, 0.0, 1.0)
    filled = filled * sil_shade[..., None]

    if grain_hi is not None:
        gh, gw = grain_hi.shape[:2]
        tiled = np.tile(grain_hi, (H // gh + 2, W // gw + 2, 1))[:H, :W]
        filled = filled + tiled * 0.65

    # Authentic front/rear bare nudity anatomy detailing
    hys, hxs = np.nonzero(hole)
    mid_hx = float(np.median(hxs))
    hy_top, hy_bot = float(hys.min()), float(hys.max())
    hx_w = max(24.0, float(np.percentile(hxs, 92) - np.percentile(hxs, 8)))
    hy_h = max(24.0, hy_bot - hy_top)

    vk = view_kind or ("rear" if is_rear else "front")
    if vk in ("rear", "rear135"):
        # Crisp anatomical intergluteal cleft + twin rounded lower gluteal fold shadows
        cleft_x = mid_hx + (-0.06 * hx_w if vk == "rear135" else 0.0)
        cleft = (
            np.exp(-((xg - cleft_x) / max(4.5, hx_w * 0.042)) ** 2)
            * np.clip((yg - (hy_top + 0.14 * hy_h)) / max(8.0, 0.32 * hy_h), 0.0, 1.0)
            * np.clip((hy_bot - yg) / max(8.0, 0.16 * hy_h), 0.0, 1.0)
            * 0.30
        )
        fold_y = hy_top + 0.66 * hy_h
        l_fold = np.exp(-(((xg - (cleft_x - 0.22 * hx_w)) / (0.20 * hx_w)) ** 2 + ((yg - fold_y) / (0.075 * hy_h)) ** 2)) * 0.16
        r_fold = np.exp(-(((xg - (cleft_x + 0.22 * hx_w)) / (0.20 * hx_w)) ** 2 + ((yg - fold_y) / (0.075 * hy_h)) ** 2)) * 0.16
        # Subtle highlight on upper glute crowns
        crown_y = hy_top + 0.40 * hy_h
        crown_hi = (
            np.exp(-(((xg - (cleft_x - 0.21 * hx_w)) / (0.18 * hx_w)) ** 2 + ((yg - crown_y) / (0.18 * hy_h)) ** 2))
            + np.exp(-(((xg - (cleft_x + 0.21 * hx_w)) / (0.18 * hx_w)) ** 2 + ((yg - crown_y) / (0.18 * hy_h)) ** 2))
        ) * 0.06
        filled = filled * (1.0 - (cleft + l_fold + r_fold)[..., None] + crown_hi[..., None])
    elif vk in ("front", "front45"):
        # Graft lighting-invariant photographic groin anatomy ratio from wheelman_body.jpg!
        g_ratio = get_authentic_groin_ratio()
        f_scale = 0.72 if vk == "front45" else 1.0
        gw_px = max(24, int(round(hx_w * 0.46 * f_scale)))
        gh_px = max(26, int(round(hy_h * 0.56)))
        gx_c = int(round(mid_hx + (-0.09 * hx_w if vk == "front45" else 0.0)))
        gy_c = int(round(hy_top + (0.35 if extra_protect_boxes else 0.46) * hy_h))
        g_rsz = cv2.resize(g_ratio, (gw_px, gh_px), interpolation=cv2.INTER_LINEAR)
        x0g = gx_c - gw_px // 2
        y0g = gy_c - gh_px // 2
        ix0, iy0 = max(0, x0g), max(0, y0g)
        ix1, iy1 = min(W, x0g + gw_px), min(H, y0g + gh_px)
        if ix1 > ix0 and iy1 > iy0:
            sub_r = g_rsz[iy0 - y0g:iy1 - y0g, ix0 - x0g:ix1 - x0g]
            in_body = (dist_sil[iy0:iy1, ix0:ix1] > 8.0) & (~mech_mask[iy0:iy1, ix0:ix1])
            eff_r = np.where(in_body[..., None], sub_r, 1.0)
            filled[iy0:iy1, ix0:ix1] = np.clip(filled[iy0:iy1, ix0:ix1] * eff_r, 0.0, 255.0)
        # Subtle iliac V-furrows
        v_l = np.exp(-((xg - (gx_c - 0.24 * hx_w) - (yg - hy_top) * 0.28) / max(3.5, hx_w * 0.035)) ** 2) * np.clip((gy_c - yg) / (0.38 * hy_h), 0.0, 1.0) * 0.09
        v_r = np.exp(-((xg - (gx_c + 0.24 * hx_w) + (yg - hy_top) * 0.28) / max(3.5, hx_w * 0.035)) ** 2) * np.clip((gy_c - yg) / (0.38 * hy_h), 0.0, 1.0) * 0.09
        filled = filled * (1.0 - (v_l + v_r)[..., None])

    blend_w = cv2.GaussianBlur(hole.astype(np.float32), (11, 11), 2.5) * (a > 0.10) * (~mech_mask)
    orig_arr = np.array(rgba_im).astype(np.float32)
    arr[..., :3] = np.clip(rgb * (1.0 - blend_w[..., None]) + filled * blend_w[..., None], 0.0, 255.0)
    arr[mech_mask] = orig_arr[mech_mask]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def normalize_to_canvas(im_rgba, target_h=268.0, max_w=332.0, ground_y=GROUND_Y, canvas_wh=CANVAS_WH, center_mode="bbox"):
    """Normalizes RGBA character sprite onto 360x360 canvas with lowest foot/wheel planted at ground_y."""
    Wc, Hc = canvas_wh
    arr = np.array(im_rgba)
    ys, xs = np.nonzero(arr[..., 3] > 24)
    if len(xs) == 0:
        return Image.new("RGBA", canvas_wh, (0, 0, 0, 0))
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = float(ys.min()), float(ys.max())
    sw = max(1.0, x1 - x0)
    sh = max(1.0, y1 - y0)

    scale = min(max_w / sw, target_h / sh, (ground_y - 12.0) / sh)
    rw = max(2, int(round(im_rgba.width * scale)))
    rh = max(2, int(round(im_rgba.height * scale)))
    rsz = im_rgba.resize((rw, rh), Image.LANCZOS)

    if center_mode == "torso":
        # Center on upper-middle body mass so outstretched thrown arms don't shift torso sideways
        mid_band = (arr[..., 3] > 40)
        my_lo = int(y0 + 0.25 * sh)
        my_hi = int(y0 + 0.75 * sh)
        sub_xs = np.nonzero(mid_band[my_lo:my_hi, :])[1]
        cx_src = float(np.median(sub_xs)) if len(sub_xs) > 20 else 0.5 * (x0 + x1)
    else:
        cx_src = 0.5 * (x0 + x1)

    ox = int(round(Wc * 0.5 - cx_src * scale))
    oy = int(round(ground_y - y1 * scale))
    out = Image.new("RGBA", canvas_wh, (0, 0, 0, 0))
    out.paste(rsz, (ox, oy), rsz)
    return out


def premul_remap(rgba, map_x, map_y):
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, a * 255.0], axis=-1)
    warped = cv2.remap(pm, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    wa = warped[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, warped[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), np.clip(warped[..., 3], 0, 255).astype(np.uint8)])


def paste_rotated_rgba(stage_rgba, sprite_pil, cx, cy, angle_deg=0.0, sx=1.0, sy=1.0, alpha_mul=1.0):
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
    stage_rgba.alpha_composite(im, (px, py))


def tone_for_darkplaces(im_rgba):
    rgb = ImageEnhance.Contrast(im_rgba.convert("RGB")).enhance(1.20)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.50)
    rgb.putalpha(im_rgba.getchannel("A"))
    return rgb


def write_spr32(path, frames, ground_y=GROUND_Y):
    w, h = frames[0].size
    rad = math.hypot(w / 2.0, h)
    ox = -(w // 2)
    oy = ground_y
    buf = bytearray(b"IDSP" + struct.pack("<iifiiifi", 32, 0, rad, w, h, len(frames), 0.0, 0))
    for im in frames:
        buf += struct.pack("<i", 0) + struct.pack("<iiii", ox, oy, w, h) + im.tobytes()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(buf)
    print(f"Wrote DarkPlaces SPR32: {path} ({len(frames)} frames, {w}x{h}, origin=({ox},{oy}), {len(buf)/1e6:.2f} MB)")


def pil_to_data_uri(im, max_wh=None):
    if max_wh is not None and im.size != max_wh:
        im = im.resize(max_wh, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
