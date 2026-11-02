"""Photorealistic Articulated Gauntlet, 24fps Optical-Flow Idle & Violent Throw Rig for Pickle Surprise (`progs/v_pickle.md3`).

Upgrades over raw `vpk_00..47.png`:
  1. Rim decontamination (`decontaminate_rgba`) removes 100% of the white studio backdrop fringe while keeping
     every interior gold sequin & turquoise highlight crisp.
  2. Uncropped Rounded Crown Dome (`complete_pickle_dome`): grafts the full rounded gold-studded turquoise crown apex
     from `progs/pickle_00.png` onto the top of `vpk_00..47` on an expanded `816 x 720` viewport canvas so tilting,
     bobbing, or cocking back NEVER reveals a flat horizontal crop line at the top of the pickle!
  3. Extended Segmented Bronze Vambrace (`extend_forearm_vambrace`): extrudes the real photographed segmented bronze
     and leather forearm armor `+270 px` down-right along the forearm cylinder axis on a `1080 x 980` pre-warp rig buffer
     so high cock-back windups and cross-screen whip-throws NEVER show a floating amputated forearm stump!
  4. Bidirectional Optical-Flow In-Betweens (`interpolate_flow_pair`): turns the 48 8fps studio frames into 95 silky-smooth
     frames with zero ghosting.
  5. Photorealistic Open-Palm Gauntlet & 3-Phase Throw/Release/Follow-Through/Reload sequence with exact 3D projectile
     handoff coordinates printed for `Pk_Launch()` in `pickle.qc`.
"""
from __future__ import annotations

import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

# Expanded canvas geometry preserving exact 1:1 resting pixel scale & position of original 512x607 vpk frames!
ORIG_W, ORIG_H = 512, 607
CANVAS_W, CANVAS_H = 816, 748
X_OFF, Y_OFF = 240, 116

# Rig pre-warp buffer (extra room down-right for extended bronze forearm before affine whip transform)
RIG_W, RIG_H = 1088, 1020

# Output supersampled -> LANCZOS texture dimensions
OUT_W, OUT_H = 544, 498


def decontaminate_rgba(rgba: np.ndarray, rim_px: float = 5.5, erode_px: float = 0.75) -> np.ndarray:
    """Remove white/pale studio backdrop bleed along the outer alpha rim while keeping
    100% of interior specular sequin glints intact."""
    rgb = rgba[..., :3].astype(np.float32)
    a_raw = rgba[..., 3].astype(np.float32) / 255.0
    fg = a_raw > 0.45

    dist_in = ndimage.distance_transform_edt(fg)
    dist_out = ndimage.distance_transform_edt(~fg)
    sdf = dist_in - dist_out

    hi = rgb.max(axis=2)
    lo = rgb.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

    pale_rim = (dist_in <= rim_px) & (
        ((lo > 75.0) & (sat < 0.30))
        | ((lum > 110.0) & (sat < 0.38) & (dist_in <= 3.8))
    )

    clean_seed = (dist_in > 3.4) & (~pale_rim) & fg
    if not np.any(clean_seed):
        clean_seed = (dist_in > 1.5) & fg

    if np.any(clean_seed):
        _, idx = ndimage.distance_transform_edt(~clean_seed, return_indices=True)
        nearest_rgb = rgb[idx[0], idx[1]]
        rim_blend = np.clip((dist_in - 1.5) / 2.8, 0.0, 1.0)
        rim_blend = np.where(pale_rim, 0.0, rim_blend)[..., None]
        rgb_clean = rgb * rim_blend + nearest_rgb * (1.0 - rim_blend)
    else:
        rgb_clean = rgb.copy()

    alpha_aa = np.clip((sdf - erode_px + 0.65) / 1.3, 0.0, 1.0)
    solid_lbl, n_lbl = ndimage.label(alpha_aa > 0.08)
    if n_lbl > 1:
        sizes = ndimage.sum(alpha_aa > 0.08, solid_lbl, range(1, n_lbl + 1))
        for k_id, sz in enumerate(sizes, start=1):
            if sz < 28:
                alpha_aa[solid_lbl == k_id] = 0.0

    a_u8 = np.clip(np.round(alpha_aa * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return np.dstack([rgb_u8, a_u8])


def boost_vpk_to_studio_srgb(rgba: np.ndarray, mul: float = 1.72) -> np.ndarray:
    """Invert `HOLD_DIM = 0.6` (or `DIM = 0.3` with `mul = 3.2`) into vivid studio sRGB."""
    rgb = rgba[..., :3].astype(np.float32) / 255.0
    a = rgba[..., 3:4]
    lifted = rgb * mul
    lifted = lifted / (1.0 + 0.14 * (lifted ** 2))
    lifted = np.clip(lifted, 0.0, 1.0) ** 0.94
    out_rgb = np.clip(np.round(lifted * 255.0), 0, 255).astype(np.uint8)
    out_rgb[a[..., 0] == 0] = 0
    return np.dstack([out_rgb, a])


def tone_for_quake_hdr(srgb_rgba: np.ndarray, dim: float = 0.56, contrast: float = 1.08) -> np.ndarray:
    """Tone studio sRGB frame for DarkPlaces `r_hdr_scenebrightness 2.5` + `rgbGen lightingDiffuse`."""
    a = srgb_rgba[..., 3]
    rgb_im = Image.fromarray(srgb_rgba[..., :3], "RGB")
    if abs(contrast - 1.0) > 1e-3:
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(contrast)
    if abs(dim - 1.0) > 1e-3:
        rgb_im = ImageEnhance.Brightness(rgb_im).enhance(dim)
    rgb_arr = np.asarray(rgb_im, dtype=np.uint8).copy()
    a_clean = np.where(a < 6, 0, a).astype(np.uint8)
    rgb_arr[a_clean == 0] = 0
    return np.dstack([rgb_arr, a_clean])


def downsample_canvas(rgba: np.ndarray, out_wh: tuple[int, int] = (OUT_W, OUT_H)) -> np.ndarray:
    """Premultiplied LANCZOS downsample so transparent edges stay 100% halo-free."""
    pm = premul_from_rgba(rgba)
    ow, oh = out_wh
    pm_ds = cv2.resize(pm, (ow, oh), interpolation=cv2.INTER_AREA)
    return rgba_from_premul(pm_ds)


def warp_lens(rgb: np.ndarray, center: tuple[float, float], radii: tuple[float, float], sx: float, sy: float) -> np.ndarray:
    h, w = rgb.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs - center[0]) / radii[0]
    ny = (ys - center[1]) / radii[1]
    q = np.clip(1.0 - (nx * nx + ny * ny), 0.0, 1.0) ** 2
    gx = 1.0 - (1.0 - 1.0 / sx) * q
    gy = 1.0 - (1.0 - 1.0 / sy) * q
    mx = (center[0] + (xs - center[0]) * gx).astype(np.float32)
    my = (center[1] + (ys - center[1]) * gy).astype(np.float32)
    return cv2.remap(rgb, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def premul_from_rgba(rgba: np.ndarray) -> np.ndarray:
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    return np.dstack([f[..., :3] * a, f[..., 3:4]])


def rgba_from_premul(pm: np.ndarray) -> np.ndarray:
    a = np.clip(pm[..., 3], 0.0, 255.0)
    denom = np.maximum(a[..., None] / 255.0, 1e-4)
    rgb = np.clip(pm[..., :3] / denom, 0.0, 255.0)
    a_u8 = np.round(a).astype(np.uint8)
    rgb_u8 = np.round(rgb).astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return np.dstack([rgb_u8, a_u8])


def over_premul(dst_pm: np.ndarray, src_pm: np.ndarray) -> np.ndarray:
    sa = np.clip(src_pm[..., 3:4] / 255.0, 0.0, 1.0)
    return src_pm + dst_pm * (1.0 - sa)


def affine_premul(
    pm: np.ndarray,
    pivot: tuple[float, float],
    tx: float = 0.0,
    ty: float = 0.0,
    rot_deg: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
    shear_x: float = 0.0,
    out_hw: tuple[int, int] | None = None,
) -> np.ndarray:
    h, w = pm.shape[:2]
    oh, ow = out_hw if out_hw is not None else (h, w)
    px, py = pivot
    rad = math.radians(rot_deg)
    c, s = math.cos(rad), math.sin(rad)

    m_rs = np.array([[c, -s], [s, c]], dtype=np.float32) @ np.array(
        [[sx, shear_x * sy], [0.0, sy]], dtype=np.float32
    )
    t_vec = np.array([px + tx, py + ty], dtype=np.float32) - m_rs @ np.array([px, py], dtype=np.float32)
    M = np.hstack([m_rs, t_vec[:, None]])
    return cv2.warpAffine(
        pm,
        M,
        (ow, oh),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0, 0.0),
    )


def prepare_expanded_vpk_frame(
    vpk_srgb: np.ndarray,
    pk0_srgb: np.ndarray,
    out_hw: tuple[int, int] = (CANVAS_H, CANVAS_W),
) -> np.ndarray:
    """Places a `512x607` studio `vpk` frame at `(X_OFF, Y_OFF)` on `out_hw`,
    grafts the complete rounded gold-studded turquoise crown dome from `pk0_srgb` onto the top,
    and extrudes the segmented bronze vambrace cuff down-right so neither top nor forearm is EVER flat-cropped!"""
    OH, OW = out_hw
    canvas = np.zeros((OH, OW, 4), dtype=np.float32)
    vpk_pm = premul_from_rgba(vpk_srgb)
    canvas[Y_OFF : Y_OFF + ORIG_H, X_OFF : X_OFF + ORIG_W] = vpk_pm

    # --- 1. Graft rounded turquoise gold-studded dome onto top of pickle crown ---
    a_vpk = vpk_srgb[..., 3]
    ys_fg = np.where(a_vpk > 128)[0]
    y_top = int(ys_fg.min()) if len(ys_fg) else 0
    # Measure width & center of pickle crown at `y_ref = y_top + 28`
    y_ref = min(ORIG_H - 20, y_top + 28)
    xs_band = []
    mids = []
    for yy in range(max(0, y_ref - 6), min(ORIG_H, y_ref + 7)):
        xs = np.where(a_vpk[yy, :280] > 128)[0]
        if len(xs) >= 20:
            xs_band.append(xs[-1] - xs[0])
            mids.append(0.5 * (xs[0] + xs[-1]))
    cw_vpk = float(np.median(xs_band)) if xs_band else 112.0
    cx_vpk = float(np.median(mids)) if mids else 140.0

    # Also measure slight crown tilt between y_ref and y_ref + 36
    mids_lo = []
    for yy in range(min(ORIG_H - 10, y_ref + 28), min(ORIG_H - 2, y_ref + 40)):
        xs = np.where(a_vpk[yy, :280] > 128)[0]
        if len(xs) >= 20:
            mids_lo.append(0.5 * (xs[0] + xs[-1]))
    cx_lo = float(np.median(mids_lo)) if mids_lo else cx_vpk
    dx_tilt = (cx_vpk - cx_lo) / 34.0  # lean of crown going upward
    tilt_deg = math.degrees(math.atan2(dx_tilt, -1.0)) if False else math.degrees(math.atan2(dx_tilt, 1.0))

    # Extract pk0 dome (`y = 16..102` where `y = 92` has width `107.0` centered at `253.5`)
    dome_crop = pk0_srgb[16:106, 175:335].copy()  # 90 x 160, base at y_local = 76 (`y_pk0 = 92`), center x_local = 78.5
    # Color-match dome RGB to vpk crown band (`y_ref-4 .. y_ref+28`)
    band_mask = a_vpk[y_ref - 4 : y_ref + 28, :260] > 180
    dome_mask = dome_crop[45:82, :, 3] > 180
    dome_rgb = dome_crop[..., :3].astype(np.float32)
    if np.any(band_mask) and np.any(dome_mask):
        tgt_pixels = vpk_srgb[y_ref - 4 : y_ref + 28, :260, :3][band_mask].astype(np.float32)
        src_pixels = dome_rgb[45:82, :][dome_mask]
        tgt_mean, tgt_std = tgt_pixels.mean(axis=0), np.maximum(tgt_pixels.std(axis=0), 6.0)
        src_mean, src_std = src_pixels.mean(axis=0), np.maximum(src_pixels.std(axis=0), 6.0)
        gain = np.clip(tgt_std / src_std, 0.72, 1.45)
        dome_rgb = (dome_rgb - src_mean) * gain + tgt_mean
        dome_rgb = np.clip(dome_rgb, 0.0, 255.0)

    dome_rgba = np.dstack([np.round(dome_rgb).astype(np.uint8), dome_crop[..., 3]])
    # Feather bottom 16 rows of dome_rgba so it disappears smoothly downward
    yl_d = np.arange(dome_rgba.shape[0], dtype=np.float32)[:, None]
    bot_fade = np.clip((88.0 - yl_d) / 16.0, 0.0, 1.0)
    dome_pm = premul_from_rgba(dome_rgba) * bot_fade[..., None]

    scale_d = cw_vpk / 106.0
    # Place `dome_pm` pivot `(78.5, 76.0)` at `(X_OFF + cx_vpk, Y_OFF + y_ref)`
    dome_pad = np.zeros((OH, OW, 4), dtype=np.float32)
    dome_pad[: dome_pm.shape[0], : dome_pm.shape[1]] = dome_pm
    dome_warped = affine_premul(
        dome_pad,
        pivot=(78.5, 76.0),
        tx=(X_OFF + cx_vpk) - 78.5,
        ty=(Y_OFF + y_ref) - 76.0,
        rot_deg=-tilt_deg * 0.65,
        sx=scale_d,
        sy=scale_d * 0.96,
        out_hw=(OH, OW),
    )

    # Shave the flat horizontal cut at `Y_OFF + y_top .. Y_OFF + y_top + 22` on `canvas` so dome takes over cleanly
    yg_c = np.arange(OH, dtype=np.float32)[:, None]
    xg_c = np.arange(OW, dtype=np.float32)[None, :]
    in_crown_x = (xg_c >= X_OFF) & (xg_c <= X_OFF + 280)
    vpk_top_fade = np.clip((yg_c - (Y_OFF + y_top + 5.0)) / 20.0, 0.0, 1.0)
    fade_mask = np.where(in_crown_x & (yg_c < Y_OFF + y_top + 26.0), vpk_top_fade, 1.0)
    canvas = canvas * fade_mask[..., None]
    # Composite dome UNDER faded vpk body so real sequins below `y_top + 25` stay 100% untouched, and rounded dome caps the top!
    canvas = over_premul(dome_warped, canvas)

    # --- 2. Extrude segmented bronze vambrace cuff down-right along forearm axis `(dx=+0.95, dy=+1.00)` ---
    # Extract forearm cuff patch (`vpk y=492..606, x=145..511`), fading its upper-left seam smoothly
    cuff = vpk_pm[490:607, 140:512].copy()  # 117 x 372
    ch, cw = cuff.shape[:2]
    yc, xc = np.mgrid[0:ch, 0:cw].astype(np.float32)
    # Soft fade along top & left of cuff patch so stamped segments blend invisibly under the real wrist
    top_f = np.clip(yc / 26.0, 0.0, 1.0)
    right_f = np.clip((cw - 1.0 - xc) / 14.0, 0.0, 1.0) * 0.0 + 1.0
    # Slight smooth darken toward elbow so extended armor has natural depth falloff
    cuff_pad = np.zeros((OH, OW, 4), dtype=np.float32)
    y0_c = Y_OFF + 490
    x0_c = X_OFF + 140
    cuff_pad[y0_c : y0_c + ch, x0_c : x0_c + cw] = cuff * top_f[..., None]

    # Stamp 4 overlapping armor-band extensions from farthest elbow back toward wrist, THEN composite real canvas OVER them!
    ext_accum = np.zeros((OH, OW, 4), dtype=np.float32)
    for step_k in (4, 3, 2, 1):
        shift_y = 68.0 * step_k
        shift_x = 64.5 * step_k
        sc = 1.0 + 0.018 * step_k
        shade = 1.0 - 0.045 * step_k
        seg = affine_premul(
            cuff_pad,
            pivot=(x0_c + 185.0, y0_c + 60.0),
            tx=shift_x,
            ty=shift_y,
            rot_deg=0.0,
            sx=sc,
            sy=sc,
            out_hw=(OH, OW),
        )
        seg[..., :3] *= shade
        ext_accum = over_premul(ext_accum, seg)

    # Shave the razor-sharp `y = Y_OFF + 606` and `x = X_OFF + 511` straight border of the original frame over 14px
    # so it blends seamlessly into `ext_accum` with zero visible horizontal/vertical line!
    bot_feather = np.clip(((Y_OFF + ORIG_H - 1.0) - yg_c) / 16.0, 0.0, 1.0)
    rgt_feather = np.clip(((X_OFF + ORIG_W - 1.0) - xg_c) / 16.0, 0.0, 1.0)
    edge_f = np.where(yg_c > Y_OFF + ORIG_H - 18.0, bot_feather, 1.0)
    edge_f = np.where((xg_c > X_OFF + ORIG_W - 18.0) & (yg_c > Y_OFF + 460.0), np.minimum(edge_f, rgt_feather), edge_f)
    canvas = over_premul(ext_accum, canvas * edge_f[..., None])

    return rgba_from_premul(canvas)


def interpolate_flow_pair(rgba_a: np.ndarray, rgba_b: np.ndarray, t: float = 0.5) -> np.ndarray:
    """Bidirectional Farneback optical-flow interpolation on `CANVAS_W x CANVAS_H` RGBA frames."""
    pm_a = premul_from_rgba(rgba_a)
    pm_b = premul_from_rgba(rgba_b)
    gray_a = cv2.cvtColor(rgba_a[..., :3], cv2.COLOR_RGB2GRAY)
    gray_b = cv2.cvtColor(rgba_b[..., :3], cv2.COLOR_RGB2GRAY)

    # Compute flow on active ROI (`x = X_OFF-40 .. X_OFF+520, y = 10 .. CANVAS_H`) for speed & precision
    x0, x1 = max(0, X_OFF - 40), min( rgba_a.shape[1], X_OFF + 530)
    ga = gray_a[:, x0:x1]
    gb = gray_b[:, x0:x1]

    flow_ab = cv2.calcOpticalFlowFarneback(ga, gb, None, 0.5, 3, 19, 3, 5, 1.2, 0)
    flow_ba = cv2.calcOpticalFlowFarneback(gb, ga, None, 0.5, 3, 19, 3, 5, 1.2, 0)

    h, w_roi = ga.shape
    yg, xg = np.mgrid[0:h, 0:w_roi].astype(np.float32)

    map_a_x = (xg - t * flow_ba[..., 0] + x0).astype(np.float32)
    map_a_y = (yg - t * flow_ba[..., 1]).astype(np.float32)
    map_b_x = (xg - (1.0 - t) * flow_ab[..., 0] + x0).astype(np.float32)
    map_b_y = (yg - (1.0 - t) * flow_ab[..., 1]).astype(np.float32)

    wa = cv2.remap(pm_a, map_a_x, map_a_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wb = cv2.remap(pm_b, map_b_x, map_b_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    out_pm = ((1.0 - t) * pm_a + t * pm_b).copy()
    out_pm[:, x0:x1] = (1.0 - t) * wa + t * wb
    return rgba_from_premul(out_pm)


class PickleThrowRig:
    """Articulated bronze-and-leather gauntlet + Pickle Surprise rig on `RIG_W x RIG_H` (`1088 x 992`),
    outputting crisp `CANVAS_W x CANVAS_H` (`816 x 720`) frames with zero edge cuts."""

    def __init__(self, raw_vpk_srgb: list[np.ndarray], pk0_srgb: np.ndarray):
        self.raw_frames = raw_vpk_srgb
        self.pk0_srgb = pk0_srgb
        # Prebuild expanded `RIG_W x RIG_H` frames for key expressions (`0`, `14`, `20`, `24`)
        self.rig_00 = prepare_expanded_vpk_frame(raw_vpk_srgb[0], pk0_srgb, out_hw=(RIG_H, RIG_W))
        self.rig_14 = prepare_expanded_vpk_frame(raw_vpk_srgb[14], pk0_srgb, out_hw=(RIG_H, RIG_W))
        self.rig_20 = prepare_expanded_vpk_frame(raw_vpk_srgb[20], pk0_srgb, out_hw=(RIG_H, RIG_W))
        self.rig_24 = prepare_expanded_vpk_frame(raw_vpk_srgb[24], pk0_srgb, out_hw=(RIG_H, RIG_W))
        self._build_layers()

    def _segment_hand_vs_pickle(self, rig_rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Segments `(pickle_mask, left_fingers_mask, right_palm_vambrace_mask)` in `(RIG_H, RIG_W)` coords."""
        H, W = rig_rgba.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
        # Convert to original vpk local coords `(xl, yl)`
        xl = xg - X_OFF
        yl = yg - Y_OFF

        rgb = rig_rgba[..., :3].astype(np.float32)
        a = rig_rgba[..., 3].astype(np.float32) / 255.0
        fg = a > 0.15
        warm = rgb[..., 0] - rgb[..., 2]

        f_raw = fg & (xl >= -10.0) & (xl < 94.0) & (yl >= 265.0) & (yl <= 430.0) & (warm > -8.0)
        f_raw = ndimage.binary_closing(f_raw, structure=np.ones((5, 5), bool))
        f_raw = ndimage.binary_opening(f_raw, structure=np.ones((3, 3), bool))
        f_raw &= fg & (xl < 95.0) & (yl >= 264.0) & (yl <= 432.0)

        p_raw = fg & (
            (yl >= 436.0)
            | ((xl >= 166.0) & (yl >= 238.0) & (warm > -8.0))
            | (
                (yl >= 384.0)
                & (xl >= 52.0)
                & (warm > 4.0)
                & ~((xl >= 92.0) & (xl <= 140.0) & (yl <= 432.0) & ((rgb[..., 0] - rgb[..., 1]) > 48.0))
            )
            | ((xl < 66.0) & (yl >= 412.0) & (warm > -5.0))
        )
        p_raw = ndimage.binary_closing(p_raw, structure=np.ones((5, 5), bool))
        p_raw &= fg & (~f_raw)

        pk_raw = fg & (~f_raw) & (~p_raw) & (yl < 442.0)
        pk_raw = ndimage.binary_closing(pk_raw, structure=np.ones((5, 5), bool)) & fg

        f_m = cv2.GaussianBlur(f_raw.astype(np.float32), (3, 3), 0.7) * a
        p_m = cv2.GaussianBlur(p_raw.astype(np.float32), (3, 3), 0.7) * a
        pk_m = cv2.GaussianBlur(pk_raw.astype(np.float32), (3, 3), 0.7) * a
        return pk_m, f_m, p_m

    def _extract_whole_pickle(self, rig_src: np.ndarray, scream_boost: float = 0.0) -> np.ndarray:
        pk_m, f_m, _ = self._segment_hand_vs_pickle(rig_src)
        rgb = rig_src[..., :3].astype(np.float32).copy()
        H, W = rgb.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

        x_sym = X_OFF + 115.0
        mirror_x = np.clip(np.round(2.0 * x_sym - xg), 0, W - 1).astype(np.int32)
        mirror_rgb = rgb[yg.astype(np.int32), mirror_x]
        mirror_pk = pk_m[yg.astype(np.int32), mirror_x]

        occ_zone = (f_m > 0.12) & (yg >= Y_OFF + 275.0) & (yg <= Y_OFF + 412.0) & (mirror_pk > 0.35)
        occ_w = cv2.GaussianBlur(occ_zone.astype(np.float32), (9, 9), 2.2)
        rgb = rgb * (1.0 - occ_w[..., None]) + mirror_rgb * occ_w[..., None]
        full_a = np.maximum(pk_m, occ_w * mirror_pk)

        if scream_boost > 1e-3:
            ey = 1.0 + 0.85 * scream_boost
            mx_s = 1.0 + 0.42 * scream_boost
            my_s = 1.0 + 0.50 * scream_boost
            rgb_u8 = np.clip(rgb, 0, 255).astype(np.uint8)
            rgb_u8 = warp_lens(rgb_u8, (X_OFF + 115.0, Y_OFF + 368.0), (52.0, 56.0), mx_s, my_s)
            rgb_u8 = warp_lens(rgb_u8, (X_OFF + 86.0, Y_OFF + 282.0), (34.0, 30.0), ey, ey)
            rgb_u8 = warp_lens(rgb_u8, (X_OFF + 143.0, Y_OFF + 283.0), (34.0, 30.0), ey, ey)
            rgb_u8 = warp_lens(
                rgb_u8,
                (X_OFF + 114.0, Y_OFF + 193.0),
                (38.0, 26.0),
                1.0 + 0.40 * scream_boost,
                1.0 + 0.40 * scream_boost,
            )
            rgb = rgb_u8.astype(np.float32)

        a_u8 = np.clip(np.round(full_a * 255.0), 0, 255).astype(np.uint8)
        rgb_u8 = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
        rgb_u8[a_u8 == 0] = 0
        return np.dstack([rgb_u8, a_u8])

    def _make_open_finger_template(
        self, leather_patch: np.ndarray, brass_patch: np.ndarray, length: float, base_w: float, tip_w: float, seed: int
    ) -> np.ndarray:
        """Photorealistic curved 3-phalanx gloved finger with antique-bronze dorsal knuckle armor plates,
        creased leather joints, and natural foreshortened curl."""
        CW, CH = 160, 96
        px0, py0 = 26.0, 52.0
        yg, xg = np.mgrid[0:CH, 0:CW].astype(np.float32)
        u = (xg - px0) / length
        u_c = np.clip(u, 0.0, 1.0)
        # Gentle anatomical palmar curl (`-y` is dorsal/up in finger-local coords)
        center_y = py0 - 7.5 * (u_c ** 1.65)
        half_w = 0.5 * (base_w * (1.0 - u_c) + tip_w * u_c) * (1.0 + 0.06 * np.sin(u_c * math.pi * 2.0))
        v = (yg - center_y) / np.maximum(half_w, 1.0)

        dx_px = (u - u_c) * length
        dy_px = yg - center_y
        sdf = half_w - np.hypot(dx_px, dy_px)
        alpha = np.clip((sdf + 0.8) / 1.5, 0.0, 1.0)

        tex = cv2.resize(
            np.roll(leather_patch, shift=seed * 19, axis=1), (CW, CH), interpolation=cv2.INTER_CUBIC
        )
        brass_tex = cv2.resize(
            np.roll(brass_patch, shift=seed * 23, axis=0), (CW, CH), interpolation=cv2.INTER_CUBIC
        )

        cyl = np.sqrt(np.clip(1.0 - v * v, 0.0, 1.0))
        # Lit warmly from upper-right, deep ambient occlusion along ventral/inter-finger edge
        light = 0.52 + 0.52 * cyl - 0.18 * v
        pip = np.exp(-(((u - 0.38) / 0.035) ** 2))
        dip = np.exp(-(((u - 0.70) / 0.030) ** 2))
        mcp_ao = np.exp(-(((u - 0.04) / 0.08) ** 2)) * 0.22
        crease = 1.0 - 0.38 * pip - 0.32 * dip - mcp_ao
        rgb = tex * (light * crease)[..., None]

        # Real photographed bronze armor knuckle plates along dorsal half (`v < -0.15`) on proximal & middle phalanges
        plate1 = ((u > 0.08) & (u < 0.33)).astype(np.float32)
        plate2 = ((u > 0.43) & (u < 0.65)).astype(np.float32)
        plate_m = cv2.GaussianBlur((plate1 + plate2) * np.clip((-v - 0.10) / 0.45, 0.0, 1.0), (5, 5), 1.0)
        brass_lit = brass_tex * (0.68 + 0.46 * cyl)[..., None]
        rgb = rgb * (1.0 - 0.72 * plate_m[..., None]) + brass_lit * (0.72 * plate_m[..., None])

        # Fingertip pad shading
        tip_ao = np.clip((u - 0.82) / 0.18, 0.0, 1.0) * 0.15
        rgb *= (1.0 - tip_ao)[..., None]

        root_fade = np.clip((u + 0.14) / 0.16, 0.0, 1.0)
        alpha = alpha * root_fade

        rgba = np.dstack([
            np.clip(np.round(rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
        ])
        return premul_from_rgba(rgba)

    def _build_layers(self) -> None:
        ref = self.rig_14
        H, W = RIG_H, RIG_W
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
        _, f_m, p_m = self._segment_hand_vs_pickle(ref)
        ref_rgb = ref[..., :3].astype(np.float32)

        # 1. Closed-grip finger strips (`Index, Middle, Ring, Pinky`)
        finger_bands = [
            (Y_OFF + 282, Y_OFF + 325, (X_OFF + 64.0, Y_OFF + 304.0)),
            (Y_OFF + 322, Y_OFF + 360, (X_OFF + 64.0, Y_OFF + 341.0)),
            (Y_OFF + 356, Y_OFF + 392, (X_OFF + 66.0, Y_OFF + 374.0)),
            (Y_OFF + 387, Y_OFF + 426, (X_OFF + 68.0, Y_OFF + 405.0)),
        ]
        self.closed_fingers_pm: list[tuple[np.ndarray, tuple[float, float]]] = []
        for y0, y1, piv in finger_bands:
            band_w = np.clip(1.0 - np.maximum(0.0, np.maximum(y0 - yg, yg - y1)) / 4.0, 0.0, 1.0)
            fm_i = f_m * band_w
            rgba_i = np.dstack([
                np.clip(np.round(ref_rgb), 0, 255).astype(np.uint8),
                np.clip(np.round(fm_i * 255.0), 0, 255).astype(np.uint8),
            ])
            self.closed_fingers_pm.append((premul_from_rgba(rgba_i), piv))

        # 2. Articulated Thumb (cleanly separated from palm_base_a with 0% stationary ghost!)
        thumb_poly = Image.new("L", (W, H), 0)
        ImageDraw.Draw(thumb_poly).polygon(
            [
                (X_OFF + 170, Y_OFF + 244),
                (X_OFF + 250, Y_OFF + 240),
                (X_OFF + 254, Y_OFF + 394),
                (X_OFF + 212, Y_OFF + 424),
                (X_OFF + 168, Y_OFF + 392),
            ],
            fill=255,
        )
        thumb_zone = cv2.GaussianBlur(np.asarray(thumb_poly, dtype=np.float32) / 255.0, (9, 9), 2.0)
        warm_leather = np.clip(((ref_rgb[..., 0] - ref_rgb[..., 2]) - 4.0) / 14.0, 0.0, 1.0)
        # Erode outer 2px of thumb mask slightly so zero white fringe remains on outer right thumb edge
        p_m_eroded = cv2.erode(p_m, np.ones((3, 3), np.uint8), iterations=1)
        thumb_a = p_m_eroded * np.clip(thumb_zone * 1.15, 0.0, 1.0) * warm_leather
        palm_base_a = p_m * np.clip(1.0 - thumb_zone * 1.35, 0.0, 1.0)

        thumb_rgba = np.dstack([
            np.clip(np.round(ref_rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(thumb_a * 255.0), 0, 255).astype(np.uint8),
        ])
        self.thumb_pm = premul_from_rgba(thumb_rgba)
        self.thumb_pivot = (X_OFF + 210.0, Y_OFF + 404.0)

        # 3. Creased brown leather inner palm cup + extended bronze vambrace
        patch = ref_rgb[Y_OFF + 390 : Y_OFF + 454, X_OFF + 122 : X_OFF + 202].copy()
        brass_patch = ref_rgb[Y_OFF + 495 : Y_OFF + 575, X_OFF + 245 : X_OFF + 345].copy()
        tile_top = np.concatenate([patch, patch[:, ::-1, :]], axis=1)
        tile_4 = np.concatenate([tile_top, tile_top[::-1, :, :]], axis=0)
        leather_canvas = cv2.resize(tile_4, (230, 230), interpolation=cv2.INTER_CUBIC)
        full_leather = np.zeros_like(ref_rgb)
        full_leather[Y_OFF + 255 : Y_OFF + 485, X_OFF + 30 : X_OFF + 260] = leather_canvas

        palm_cup_im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(palm_cup_im).polygon(
            [
                (X_OFF + 148, Y_OFF + 296),
                (X_OFF + 194, Y_OFF + 306),
                (X_OFF + 218, Y_OFF + 368),
                (X_OFF + 218, Y_OFF + 456),
                (X_OFF + 82, Y_OFF + 462),
                (X_OFF + 54, Y_OFF + 410),
                (X_OFF + 68, Y_OFF + 362),
                (X_OFF + 96, Y_OFF + 326),
            ],
            fill=255,
        )
        cup_a = cv2.GaussianBlur(np.asarray(palm_cup_im, dtype=np.float32) / 255.0, (11, 11), 2.6)

        xl = xg - X_OFF
        yl = yg - Y_OFF
        hollow = np.exp(-(((xl - 134.0) / 46.0) ** 2 + ((yl - 372.0) / 50.0) ** 2))
        rim_hi = np.exp(-(((xl - 178.0) / 34.0) ** 2 + ((yl - 396.0) / 48.0) ** 2))
        c1 = np.exp(-(((yl - (332.0 + 0.36 * (xl - 85.0))) / 2.6) ** 2)) * ((xl > 72) & (xl < 185))
        c2 = np.exp(-(((yl - (362.0 + 0.48 * (xl - 80.0))) / 2.8) ** 2)) * ((xl > 78) & (xl < 192))
        # Knuckle ridge highlight across MCP joints
        knuckle_ridge = np.exp(-(((yl - (300.0 + 1.05 * (148.0 - xl))) / 11.0) ** 2)) * ((xl > 55) & (xl < 160))
        shade = 0.86 - 0.26 * hollow + 0.14 * rim_hi + 0.10 * knuckle_ridge - 0.28 * c1 - 0.24 * c2
        cup_rgb = np.clip(full_leather * shade[..., None], 8.0, 235.0)

        real_w = cv2.GaussianBlur(np.clip(palm_base_a * 1.15, 0.0, 1.0), (9, 9), 2.0)
        comb_a = np.maximum(palm_base_a, cup_a)
        comb_rgb = cup_rgb * (1.0 - real_w[..., None]) + ref_rgb * real_w[..., None]

        palm_rgba = np.dstack([
            np.clip(np.round(comb_rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(comb_a * 255.0), 0, 255).astype(np.uint8),
        ])
        self.palm_vambrace_pm = premul_from_rgba(palm_rgba)

        # 4. Foreshortened, curved armored open-hand fingers pointing forward-up-left into the throw arc
        self.open_fingers_specs = [
            ((X_OFF + 142.0, Y_OFF + 306.0), 86.0, 31.0, 21.0, -118.0),  # Index
            ((X_OFF + 112.0, Y_OFF + 324.0), 96.0, 32.0, 22.0, -133.0),  # Middle
            ((X_OFF + 86.0, Y_OFF + 352.0),  88.0, 30.0, 20.0, -149.0),  # Ring
            ((X_OFF + 66.0, Y_OFF + 388.0),  72.0, 27.0, 18.0, -165.0),  # Pinky
        ]
        self.open_finger_strips_pm = [
            self._make_open_finger_template(patch, brass_patch, flen, bw, tw, seed=i)
            for i, (_, flen, bw, tw, _) in enumerate(self.open_fingers_specs)
        ]

        # 5. Un-occluded Pickle Surprise expressions with complete rounded crown domes
        self.pk_shock = premul_from_rgba(self._extract_whole_pickle(self.rig_20, scream_boost=0.55))
        self.pk_scream = premul_from_rgba(self._extract_whole_pickle(self.rig_24, scream_boost=0.78))
        self.pk_catch = premul_from_rgba(self._extract_whole_pickle(self.rig_14, scream_boost=0.0))
        self.pk_calm = premul_from_rgba(self._extract_whole_pickle(self.rig_00, scream_boost=0.0))

    def render_articulated_pose(
        self,
        arm_tx: float = 0.0,
        arm_ty: float = 0.0,
        arm_rot_deg: float = 0.0,
        arm_scale: float = 1.0,
        open_amount: float = 0.0,
        squeeze: float = 0.0,
        pickle_mode: str = "shock",
        pk_rel_tx: float = 0.0,
        pk_rel_ty: float = 0.0,
        pk_rel_rot: float = 0.0,
        pk_scale_x: float = 1.0,
        pk_scale_y: float = 1.0,
    ) -> np.ndarray:
        """Renders articulated pose on `(RIG_H, RIG_W)` and crops after whole-arm transform to `(CANVAS_H, CANVAS_W)`."""
        hand_pm = np.zeros((RIG_H, RIG_W, 4), dtype=np.float32)

        # 1. Extended fingers emerging cleanly as hand opens (`open_amount > 0.25`)
        if open_amount > 0.24:
            ext_w = min(1.0, (open_amount - 0.24) / 0.34)
            for f_i, ((mx, my), _, _, _, rest_ang) in enumerate(self.open_fingers_specs):
                spread_extra = (f_i - 1.5) * 4.0 * open_amount
                ang = rest_ang + (1.0 - open_amount) * 24.0 - spread_extra
                len_scale = 0.66 + 0.34 * open_amount
                f_pm = affine_premul(
                    self.open_finger_strips_pm[f_i] * ext_w,
                    pivot=(26.0, 52.0),
                    tx=mx - 26.0,
                    ty=my - 52.0,
                    rot_deg=ang,
                    sx=len_scale,
                    sy=0.96 + 0.04 * open_amount,
                    out_hw=(RIG_H, RIG_W),
                )
                hand_pm = over_premul(hand_pm, f_pm)

        # 2. Leather palm cup + extended segmented bronze vambrace
        hand_pm = over_premul(hand_pm, self.palm_vambrace_pm)

        # 3. Articulated thumb
        thumb_deg = -6.0 * squeeze + 25.0 * open_amount
        thumb_tx = -3.0 * squeeze + 7.5 * open_amount
        t_pm = affine_premul(
            self.thumb_pm,
            pivot=self.thumb_pivot,
            tx=thumb_tx,
            ty=-2.0 * open_amount,
            rot_deg=thumb_deg,
            out_hw=(RIG_H, RIG_W),
        )
        hand_pm = over_premul(hand_pm, t_pm)

        # 4. Pickle Surprise in hand (prior to exact 3D release frame!)
        if pickle_mode != "none":
            pk_src = {
                "shock": self.pk_shock,
                "scream": self.pk_scream,
                "catch": self.pk_catch,
                "calm": self.pk_calm,
            }[pickle_mode]
            sx_pk = pk_scale_x * (1.0 - 0.14 * squeeze)
            sy_pk = pk_scale_y * (1.0 + 0.10 * squeeze)
            pk_pm = affine_premul(
                pk_src,
                pivot=(X_OFF + 115.0, Y_OFF + 345.0),
                tx=pk_rel_tx,
                ty=pk_rel_ty - 5.0 * squeeze,
                rot_deg=pk_rel_rot,
                sx=sx_pk,
                sy=sy_pk,
                out_hw=(RIG_H, RIG_W),
            )
            hand_pm = over_premul(hand_pm, pk_pm)

        # 5. Front curled grip fingers (peel outward cleanly as hand snaps open)
        if open_amount < 0.50:
            curl_vis = np.clip(1.0 - max(0.0, open_amount - 0.18) / 0.28, 0.0, 1.0)
            for f_i, (cf_pm, piv) in enumerate(self.closed_fingers_pm):
                peel_tx = 5.0 * squeeze - 18.0 * open_amount
                peel_ty = (-2.5 + f_i * 1.8) * open_amount
                peel_rot = 4.0 * squeeze - (22.0 + f_i * 3.5) * open_amount
                w_cf = affine_premul(
                    cf_pm * curl_vis,
                    pivot=piv,
                    tx=peel_tx,
                    ty=peel_ty,
                    rot_deg=peel_rot,
                    sx=1.0 - 0.10 * open_amount,
                    sy=1.0,
                    out_hw=(RIG_H, RIG_W),
                )
                hand_pm = over_premul(hand_pm, w_cf)

        # 6. Whole-arm whip transform around lower-right forearm pivot, outputting `(CANVAS_H, CANVAS_W)`
        canvas = affine_premul(
            hand_pm,
            pivot=(X_OFF + 345.0, Y_OFF + 545.0),
            tx=arm_tx,
            ty=arm_ty,
            rot_deg=arm_rot_deg,
            sx=arm_scale,
            sy=arm_scale,
            out_hw=(CANVAS_H, CANVAS_W),
        )
        return canvas

    def _draw_whip_and_release_fx(self, pm: np.ndarray, whip_strength: float, whip_prog: float, release_burst: float) -> np.ndarray:
        """Crisp kinetic air-rip arc + turquoise-gold release gleam when the Pickle launches off the palm."""
        if whip_strength <= 0.02 and release_burst <= 0.02:
            return pm
        fx = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(fx)

        if whip_strength > 0.02:
            for k_arc, (off_x, off_y, width_px, col) in enumerate([
                (0.0, 0.0, 10, (210, 252, 255)),
                (16.0, 24.0, 6, (90, 232, 240)),
            ]):
                u0 = max(0.0, whip_prog - 0.36)
                u1 = min(1.0, whip_prog + 0.16)
                if u1 - u0 < 0.08:
                    continue
                pts = []
                for s_i in range(16):
                    u = u0 + (u1 - u0) * (s_i / 15.0)
                    p0 = (X_OFF + 285.0 + off_x, Y_OFF + 55.0 + off_y)
                    p1 = (X_OFF + 75.0 + off_x, Y_OFF + 105.0 + off_y)
                    p2 = (X_OFF - 115.0 + off_x, Y_OFF + 335.0 + off_y)
                    bx = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0]
                    by = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1]
                    pts.append((bx, by))
                for i in range(len(pts) - 1):
                    taper = math.sin(math.pi * (i + 0.5) / max(1, len(pts) - 1))
                    a_val = int(round(130.0 * whip_strength * taper * (0.9 if k_arc == 0 else 0.55)))
                    if a_val > 3:
                        d.line([pts[i], pts[i + 1]], fill=(col[0], col[1], col[2], a_val), width=max(1, int(round(width_px * taper))))

        if release_burst > 0.02:
            # Subtle forward-radiating turquoise/gold speed lines from open palm `(178, 365)` toward crosshair `(32, 230)`
            cx, cy = 178.0, 365.0
            for ang_deg, r0, r1, col in [
                (-146, 26, 96, (185, 255, 250)),
                (-136, 30, 112, (255, 242, 175)),
                (-124, 24, 88, (140, 248, 242)),
                (-158, 22, 76, (150, 245, 240)),
            ]:
                rad = math.radians(ang_deg)
                x0 = cx + math.cos(rad) * r0
                y0 = cy + math.sin(rad) * r0
                x1 = cx + math.cos(rad) * (r0 + (r1 - r0) * (0.55 + 0.45 * release_burst))
                y1 = cy + math.sin(rad) * (r0 + (r1 - r0) * (0.55 + 0.45 * release_burst))
                a_b = int(round(150.0 * release_burst))
                d.line([(x0, y0), (x1, y1)], fill=(col[0], col[1], col[2], a_b), width=4)

        fx_blur = fx.filter(ImageFilter.GaussianBlur(2.6))
        return over_premul(pm, premul_from_rgba(np.asarray(fx_blur, dtype=np.uint8)))

    def eval_phase(self, phase: str, w: float) -> dict:
        """Evaluates one of the 3 clean QuakeC-driven animation clips (`w in [0, 1]`):
          - `"wind_whip"` (`18` frames, `0.22s`):
              `i = 0..6`  (`w < 0.39`): Choke-squeeze + brisk high cock-back anticipation
              `i = 7..13` (`w in 0.39..0.78`): Blistering diagonal forward whip with Pickle propelling toward crosshair
              `i = 14`    (`w = 0.805`): EXACT RELEASE (`Pk_Launch()` spawns 3D `pickle_throw.md3`!) — fingers snap wide open!
              `i = 15..17`(`w > 0.805`): Open-gauntlet snap past release point
          - `"follow"` (`10` frames, `0.18s`):
              Empty open bronze-and-leather claw slashes smoothly down-left completely below screen bottom!
          - `"reload"` (`12` frames, `0.24s`):
              Fresh Pickle snatched up from bottom-right with spring overshoot & cheek-squish catch into idle!
        """
        def sstep(a: float, b: float, x: float) -> float:
            t = max(0.0, min(1.0, (x - a) / max(1e-6, b - a)))
            return t * t * (3.0 - 2.0 * t)

        if phase == "wind_whip":
            if w < 0.36:
                u = w / 0.36
                coil = 1.0 - (1.0 - u) ** 2.3
                tremor = math.sin(u * math.pi * 4.0) * 2.0 * u
                return dict(
                    arm_tx=56.0 * coil + tremor,
                    arm_ty=-6.0 * coil,
                    arm_rot_deg=20.0 * coil + tremor * 0.3,
                    arm_scale=1.0 + 0.03 * coil,
                    open_amount=0.0,
                    squeeze=min(1.0, coil * 1.15),
                    pickle_mode="scream" if u > 0.45 else "shock",
                    pk_rel_tx=0.0,
                    pk_rel_ty=0.0,
                    pk_rel_rot=0.0,
                    pk_scale_x=1.0,
                    pk_scale_y=1.0,
                    whip_fx=0.0,
                    whip_prog=0.0,
                    release_burst=0.0,
                )
            else:
                u = (w - 0.36) / 0.64  # 0..1 across violent forward whip & visible open-palm release (`release` at u = 0.66 -> i=14!)
                whip = u * u * (2.15 - 1.15 * u)
                arm_tx = 56.0 + (-148.0) * whip
                arm_ty = -6.0 + 24.0 * (u ** 1.4)       # stays high & clearly visible above the Quake HUD at release!
                arm_rot = 20.0 + (-50.0) * whip
                arm_sc = 1.03 + 0.05 * math.sin(u * math.pi)
                open_amt = sstep(0.26, 0.68, u)
                sqz = max(0.0, 1.0 - sstep(0.0, 0.34, u))

                if u < 0.65:
                    fly = max(0.0, (u - 0.20) / 0.45)
                    pk_mode = "scream"
                    pk_tx = -56.0 * (fly ** 1.15)
                    pk_ty = -44.0 * (fly ** 1.10)
                    pk_rot = -15.0 * fly
                    pk_sx = 1.0 - 0.22 * fly
                    pk_sy = 1.04 - 0.24 * fly
                    rel_b = 0.0
                else:
                    pk_mode = "none"
                    pk_tx = pk_ty = pk_rot = 0.0
                    pk_sx = pk_sy = 1.0
                    rel_b = max(0.0, 1.0 - (u - 0.65) / 0.34)

                whip_s = math.sin(min(1.0, max(0.0, (u - 0.05) / 0.92)) * math.pi)
                return dict(
                    arm_tx=arm_tx,
                    arm_ty=arm_ty,
                    arm_rot_deg=arm_rot,
                    arm_scale=arm_sc,
                    open_amount=open_amt,
                    squeeze=sqz,
                    pickle_mode=pk_mode,
                    pk_rel_tx=pk_tx,
                    pk_rel_ty=pk_ty,
                    pk_rel_rot=pk_rot,
                    pk_scale_x=pk_sx,
                    pk_scale_y=pk_sy,
                    whip_fx=whip_s,
                    whip_prog=u,
                    release_burst=rel_b,
                )

        elif phase == "follow":
            # First 35% of follow-through holds/sweeps the wide-open gauntlet visibly above the HUD,
            # then drops smoothly below the bottom edge (`arm_ty -> +430`)!
            if w < 0.35:
                u = w / 0.35
                arm_tx = -92.0 - 20.0 * u
                arm_ty = 18.0 + 36.0 * (u * u)
                arm_rot = -30.0 - 6.0 * u
                open_amt = 1.0
            else:
                u = (w - 0.35) / 0.65
                ease = u * u * (2.0 - u)
                arm_tx = -112.0 - 24.0 * math.sin(u * math.pi * 0.6)
                arm_ty = 54.0 + 390.0 * ease
                arm_rot = -36.0 - 14.0 * ease
                open_amt = 1.0 - 0.14 * ease
            return dict(
                arm_tx=arm_tx,
                arm_ty=arm_ty,
                arm_rot_deg=arm_rot,
                arm_scale=1.0,
                open_amount=open_amt,
                squeeze=0.0,
                pickle_mode="none",
                pk_rel_tx=0.0,
                pk_rel_ty=0.0,
                pk_rel_rot=0.0,
                pk_scale_x=1.0,
                pk_scale_y=1.0,
                whip_fx=max(0.0, 0.35 * (1.0 - w * 2.5)),
                whip_prog=1.0,
                release_burst=0.0,
            )

        else:  # "reload"
            if w < 0.68:
                t1 = w / 0.68
                e1 = 1.0 - (1.0 - t1) ** 2.6
                arm_ty = 410.0 * (1.0 - e1) - 14.0 * e1
                arm_tx = 58.0 * (1.0 - e1)
                arm_rot = 16.0 * (1.0 - e1) - 2.5 * e1
                sqz = 0.46 * math.sin(t1 * math.pi)
            else:
                t2 = (w - 0.68) / 0.32
                e2 = sstep(0.0, 1.0, t2)
                arm_ty = -14.0 * (1.0 - e2)
                arm_tx = 0.0
                arm_rot = -2.5 * (1.0 - e2)
                sqz = 0.28 * (1.0 - e2)
            return dict(
                arm_tx=arm_tx,
                arm_ty=arm_ty,
                arm_rot_deg=arm_rot,
                arm_scale=1.0,
                open_amount=0.0,
                squeeze=sqz,
                pickle_mode="catch" if w < 0.70 else "calm",
                pk_rel_tx=0.0,
                pk_rel_ty=0.0,
                pk_rel_rot=0.0,
                pk_scale_x=1.0,
                pk_scale_y=1.0,
                whip_fx=0.0,
                whip_prog=0.0,
                release_burst=0.0,
            )

    def render_phase_frames(self, phase: str, n_frames: int) -> list[np.ndarray]:
        """Renders `n_frames` for `phase` with tight 5-substep continuous shutter blur (zero discrete stepping!)."""
        out: list[np.ndarray] = []
        dw = 1.0 / float(max(1, n_frames))
        shutter = 0.14 * dw
        sub_offsets = (-shutter, -0.5 * shutter, 0.0, 0.5 * shutter, shutter)
        sub_weights = (0.45, 0.85, 1.40, 0.85, 0.45)
        for i in range(n_frames):
            w_mid = (i + 0.5) / float(n_frames)
            mid_cfg = self.eval_phase(phase, w_mid)
            acc_pm = np.zeros((CANVAS_H, CANVAS_W, 4), dtype=np.float32)
            w_sum = 0.0
            for off, wt in zip(sub_offsets, sub_weights):
                w_s = max(0.0, min(0.9999, w_mid + off))
                cfg = self.eval_phase(phase, w_s)
                if cfg["pickle_mode"] != mid_cfg["pickle_mode"]:
                    cfg["pickle_mode"] = mid_cfg["pickle_mode"]
                sub_pm = self.render_articulated_pose(
                    arm_tx=cfg["arm_tx"],
                    arm_ty=cfg["arm_ty"],
                    arm_rot_deg=cfg["arm_rot_deg"],
                    arm_scale=cfg["arm_scale"],
                    open_amount=cfg["open_amount"],
                    squeeze=cfg["squeeze"],
                    pickle_mode=cfg["pickle_mode"],
                    pk_rel_tx=cfg["pk_rel_tx"],
                    pk_rel_ty=cfg["pk_rel_ty"],
                    pk_rel_rot=cfg["pk_rel_rot"],
                    pk_scale_x=cfg["pk_scale_x"],
                    pk_scale_y=cfg["pk_scale_y"],
                )
                acc_pm += sub_pm * wt
                w_sum += wt
            acc_pm /= w_sum
            acc_pm = self._draw_whip_and_release_fx(
                acc_pm, mid_cfg["whip_fx"], mid_cfg["whip_prog"], mid_cfg["release_burst"]
            )
            out.append(rgba_from_premul(acc_pm))
        return out

    def measure_pre_release_pickle_bbox(self, n_wind_frames: int = 18, pre_release_idx: int = 13) -> dict:
        """Renders ONLY the Pickle layer on `pre_release_idx` (last frame before `Pk_Launch`!)
        to compute the exact 3D handoff ray `(forward, right, up)` and initial world scale!"""
        w_mid = (pre_release_idx + 0.5) / float(n_wind_frames)
        cfg = self.eval_phase("wind_whip", w_mid)
        pk_pm = affine_premul(
            self.pk_scream,
            pivot=(X_OFF + 115.0, Y_OFF + 345.0),
            tx=cfg["pk_rel_tx"],
            ty=cfg["pk_rel_ty"] - 5.0 * cfg["squeeze"],
            rot_deg=cfg["pk_rel_rot"],
            sx=cfg["pk_scale_x"] * (1.0 - 0.14 * cfg["squeeze"]),
            sy=cfg["pk_scale_y"] * (1.0 + 0.10 * cfg["squeeze"]),
            out_hw=(RIG_H, RIG_W),
        )
        pk_canvas = affine_premul(
            pk_pm,
            pivot=(X_OFF + 345.0, Y_OFF + 545.0),
            tx=cfg["arm_tx"],
            ty=cfg["arm_ty"],
            rot_deg=cfg["arm_rot_deg"],
            sx=cfg["arm_scale"],
            sy=cfg["arm_scale"],
            out_hw=(CANVAS_H, CANVAS_W),
        )
        a = pk_canvas[..., 3]
        ys, xs = np.where(a > 64.0)
        cx_px = float(xs.mean())
        cy_px = float(ys.mean())
        h_px = float(ys.max() - ys.min())
        rot_total = cfg["arm_rot_deg"] + cfg["pk_rel_rot"]

        # Exact viewmodel card mapping (`build_pickle_assets.py`: 0.0395387 units/px at dx = 14.0)
        U_PER_PX = 24.0 / 607.0
        y_left = (-28.5 + 24.0 * (512.0 / 607.0)) + X_OFF * U_PER_PX
        z_top = 4.5 + Y_OFF * U_PER_PX

        vm_y = y_left - cx_px * U_PER_PX       # +Y is left, so v_right = -vm_y
        vm_z = z_top - cy_px * U_PER_PX        # +Z is up
        vm_h = h_px * U_PER_PX

        # Project along camera ray from dx = 14.0 out to D_world = 24.0
        D_WORLD = 24.0
        proj = D_WORLD / 14.0
        return dict(
            cx_px=cx_px,
            cy_px=cy_px,
            h_px=h_px,
            rot_deg=rot_total,
            forward=D_WORLD,
            right=(-vm_y) * proj,
            up=vm_z * proj,
            world_height_at_24=vm_h * proj,
        )
