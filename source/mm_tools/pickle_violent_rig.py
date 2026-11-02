"""Photorealistic Articulated Gauntlet & VIOLENT OVERHAND WHIP-THROW Rig (`progs/v_pickle.md3`).

Self-contained module (`pickle_violent_rig.py`) featuring:
  1. Interior RGB rim decontamination (`decontaminate_rgba`) — zero white studio fringe (`rb_pickle.png` fixed!).
  2. Rounded Crown Dome Completion (`complete_crown_dome`) — grafts the uncropped rounded turquoise-and-gold
     crown apex from `pickle_00.png` onto `vpk_00..47` inside an expanded `640 x 700` stage so cocking back
     or whipping forward NEVER shows a flat top-crop line!
  3. Seamless Extended Bronze Vambrace — extrudes the segmented steel/brass forearm armor `+240px` past the
     bottom-right corner so high cock-backs & cross-screen slashes NEVER show an amputated forearm stump!
  4. Silky 72-frame 24fps optical-flow idle + 48-frame VIOLENT OVERHAND WHIP-THROW:
       - Choke-crush throat squeeze + terrified bug-eyed tongue-out scream + high cock-back windup
       - Blistering cross-screen diagonal whip-slash w/ 9-tap Gaussian shutter motion blur, triple
         air-rip shockwave arcs, and snapping open-claw finger release straight into the crosshair
       - High-visibility splayed open-claw recoil shudder right across the viewport
       - Violent follow-through slash down off bottom-left + aggressive belt-snatch reload!
"""
from __future__ import annotations

import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

# Expanded stage preserving exact bottom-right anchor of original 512x607 vpk frames!
PAD_L = 128
PAD_T = 93
STAGE_W = 512 + PAD_L   # 640
STAGE_H = 607 + PAD_T   # 700


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
        ((lo > 78.0) & (sat < 0.28))
        | ((lum > 115.0) & (sat < 0.36) & (dist_in <= 3.5))
    )

    clean_seed = (dist_in > 3.2) & (~pale_rim) & fg
    if not np.any(clean_seed):
        clean_seed = (dist_in > 1.5) & fg

    if np.any(clean_seed):
        _, idx = ndimage.distance_transform_edt(~clean_seed, return_indices=True)
        nearest_rgb = rgb[idx[0], idx[1]]
        rim_blend = np.clip((dist_in - 1.4) / 2.8, 0.0, 1.0)
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


def boost_vpk_to_studio_srgb(rgba: np.ndarray) -> np.ndarray:
    rgb = rgba[..., :3].astype(np.float32) / 255.0
    a = rgba[..., 3:4]
    lifted = rgb * 1.72
    lifted = lifted / (1.0 + 0.14 * (lifted ** 2))
    lifted = np.clip(lifted, 0.0, 1.0) ** 0.94
    out_rgb = np.clip(np.round(lifted * 255.0), 0, 255).astype(np.uint8)
    out_rgb[a[..., 0] == 0] = 0
    return np.dstack([out_rgb, a])


def tone_for_quake_hdr(srgb_rgba: np.ndarray, dim: float = 0.50, contrast: float = 1.10) -> np.ndarray:
    a = srgb_rgba[..., 3]
    rgb_im = Image.fromarray(srgb_rgba[..., :3], "RGB")
    if abs(contrast - 1.0) > 1e-3:
        rgb_im = ImageEnhance.Contrast(rgb_im).enhance(contrast)
    if abs(dim - 1.0) > 1e-3:
        rgb_im = ImageEnhance.Brightness(rgb_im).enhance(dim)
    rgb_arr = np.asarray(rgb_im, dtype=np.uint8).copy()
    a_clean = np.where(a < 8, 0, a).astype(np.uint8)
    rgb_arr[a_clean == 0] = 0
    return np.dstack([rgb_arr, a_clean])


def complete_crown_dome_on_stage(rgba_512x607: np.ndarray, srgb_pk0_512: np.ndarray | None = None) -> np.ndarray:
    """Places `512x607` vpk frame into `(STAGE_H=700, STAGE_W=640)` and seamlessly grafts the rounded
    crown dome cap from `srgb_pk0_512` if the top of the headdress touches `y=0` in `rgba_512x607`."""
    out = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.uint8)
    out[PAD_T:PAD_T + 607, PAD_L:PAD_L + 512] = rgba_512x607
    if srgb_pk0_512 is None:
        return out

    # Measure top row span of vpk frame (`y5 in 0..8`)
    top_xs = np.nonzero(rgba_512x607[0:6, :, 3] > 120)[1]
    if len(top_xs) < 20:
        return out
    vpk_cx = 0.5 * (float(top_xs.min()) + float(top_xs.max()))
    vpk_w = float(top_xs.max() - top_xs.min())

    # Extract rounded dome cap from `srgb_pk0_512` (`y in 12..86`) where width matches `vpk_w`
    pk_cap = srgb_pk0_512[12:88, 175:337]  # 76 x 162
    cap_xs = np.nonzero(pk_cap[-8:, :, 3] > 120)[1]
    if len(cap_xs) < 15:
        return out
    cap_w = max(20.0, float(cap_xs.max() - cap_xs.min()))
    sc = (vpk_w * 1.03) / cap_w
    cw = max(16, int(round(pk_cap.shape[1] * sc)))
    ch = max(12, int(round(pk_cap.shape[0] * max(0.55, sc * 0.65))))
    cap_res = cv2.resize(pk_cap, (cw, ch), interpolation=cv2.INTER_LANCZOS4)

    # Place cap so its bottom overlaps `PAD_T .. PAD_T + 22` and crossfade smoothly!
    ox = int(round(PAD_L + vpk_cx - cw * 0.5))
    oy = int(round(PAD_T + 20 - ch))
    if oy < 2 or ox < 2 or ox + cw >= STAGE_W - 2:
        return out

    yg_c = np.arange(ch, dtype=np.float32)[:, None]
    # Above PAD_T (`yg_c < ch - 20`), cap is 100%; across overlap `ch-20..ch`, smooth fade out
    fade = np.clip((ch - 2.0 - yg_c) / 18.0, 0.0, 1.0)
    cap_f = cap_res.astype(np.float32)
    dst_roi = out[oy:oy + ch, ox:ox + cw].astype(np.float32)

    cap_a = (cap_f[..., 3] / 255.0) * fade
    dst_a = dst_roi[..., 3] / 255.0
    # Color-match dome brightness slightly to vpk top rows
    vpk_top_rgb = rgba_512x607[4:20, int(max(0, vpk_cx - 35)):int(min(512, vpk_cx + 35)), :3].astype(np.float32)
    cap_bot_rgb = cap_f[-18:-4, cw // 2 - 25:cw // 2 + 25, :3]
    if vpk_top_rgb.size > 0 and cap_bot_rgb.size > 0:
        gain = np.clip(np.mean(vpk_top_rgb, axis=(0, 1)) / np.maximum(np.mean(cap_bot_rgb, axis=(0, 1)), 12.0), 0.75, 1.30)
        cap_f[..., :3] = np.clip(cap_f[..., :3] * gain[None, None, :], 0.0, 255.0)

    out_a = cap_a + dst_a * (1.0 - cap_a)
    denom = np.maximum(out_a[..., None], 1e-4)
    out_rgb = (cap_f[..., :3] * cap_a[..., None] + dst_roi[..., :3] * dst_a[..., None] * (1.0 - cap_a[..., None])) / denom
    roi_u8 = np.dstack([
        np.clip(np.round(out_rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(out_a * 255.0), 0, 255).astype(np.uint8),
    ])
    roi_u8[roi_u8[..., 3] == 0, :3] = 0
    out[oy:oy + ch, ox:ox + cw] = roi_u8
    return out


def flow_interp_rgba(rgba0: np.ndarray, rgba1: np.ndarray, t: float) -> np.ndarray:
    if t <= 1e-4:
        return rgba0.copy()
    if t >= 1.0 - 1e-4:
        return rgba1.copy()

    def to_gray(rgba: np.ndarray) -> np.ndarray:
        a = rgba[..., 3:4].astype(np.float32) / 255.0
        comp = rgba[..., :3].astype(np.float32) * a + 128.0 * (1.0 - a)
        return cv2.cvtColor(comp.astype(np.uint8), cv2.COLOR_RGB2GRAY)

    g0, g1 = to_gray(rgba0), to_gray(rgba1)
    flow01 = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 4, 21, 3, 5, 1.2, 0)
    flow10 = cv2.calcOpticalFlowFarneback(g1, g0, None, 0.5, 4, 21, 3, 5, 1.2, 0)

    h, w = g0.shape
    grid_x, grid_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    vel_x = 0.5 * (flow01[..., 0] - flow10[..., 0])
    vel_y = 0.5 * (flow01[..., 1] - flow10[..., 1])
    mid_vx = cv2.remap(vel_x, grid_x - (t - 0.5) * vel_x, grid_y - (t - 0.5) * vel_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mid_vy = cv2.remap(vel_y, grid_x - (t - 0.5) * vel_x, grid_y - (t - 0.5) * vel_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    p0 = premul_from_rgba(rgba0)
    p1 = premul_from_rgba(rgba1)
    w0 = cv2.remap(p0, grid_x - t * mid_vx, grid_y - t * mid_vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    w1 = cv2.remap(p1, grid_x + (1.0 - t) * mid_vx, grid_y + (1.0 - t) * mid_vy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return rgba_from_premul((1.0 - t) * w0 + t * w1)


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
        pm, M, (ow, oh), flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0.0, 0.0, 0.0, 0.0),
    )


class PickleViolentThrowRig:
    """Articulated Gauntlet + Pickle rig operating in `(STAGE_H=700, STAGE_W=640)` space,
    with an extended `(960 x 900)` forearm buffer so violent cock-backs & slashes NEVER show a cut-off stump!"""

    EXT_W = STAGE_W + 260
    EXT_H = STAGE_H + 260

    def __init__(self, srgb_vpk_512: list[np.ndarray], srgb_pk0_512: np.ndarray | None = None):
        self.raw_512 = srgb_vpk_512
        self.pk0_512 = srgb_pk0_512
        self.frames = [complete_crown_dome_on_stage(f, srgb_pk0_512) for f in srgb_vpk_512]
        self.h, self.w = STAGE_H, STAGE_W
        self._build_gauntlet_and_pickle_layers()

    def _segment_hand_vs_pickle_512(self, rgba512: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        H, W = rgba512.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
        rgb = rgba512[..., :3].astype(np.float32)
        a = rgba512[..., 3].astype(np.float32) / 255.0
        fg = a > 0.15
        warm = rgb[..., 0] - rgb[..., 2]

        f_xmax = np.where(yg < 306.0, 56.0, 92.0)
        f_raw = fg & (xg < f_xmax) & (yg >= 265.0) & (yg <= 430.0) & (warm > -8.0)
        f_raw = ndimage.binary_closing(f_raw, structure=np.ones((5, 5), bool))
        f_raw = ndimage.binary_opening(f_raw, structure=np.ones((3, 3), bool))
        f_raw &= fg & (xg < (f_xmax + 1.5)) & (yg >= 264.0) & (yg <= 432.0)

        p_raw = fg & (
            (yg >= 436.0)
            | ((xg >= 181.0) & (yg >= 244.0) & (warm > 6.0))
            | ((xg >= 172.0) & (yg >= 312.0) & (warm > 2.0))
            | ((xg >= 166.0) & (yg >= 345.0) & (warm > -2.0))
            | ((yg >= 384.0) & (xg >= 52.0) & (warm > 4.0) & ~(
                (xg >= 92.0) & (xg <= 140.0) & (yg <= 432.0) & ((rgb[..., 0] - rgb[..., 1]) > 48.0)
            ))
            | ((xg < 66.0) & (yg >= 412.0) & (warm > -5.0))
        )
        p_raw = ndimage.binary_closing(p_raw, structure=np.ones((5, 5), bool))
        p_raw &= fg & (~f_raw)

        stray_chin_leather = (yg > 392.0) & ((xg < 84.0) | (xg > 150.0)) & (warm > 10.0)
        pk_raw = fg & (~f_raw) & (~p_raw) & (~stray_chin_leather) & (yg < 442.0)
        pk_raw = ndimage.binary_closing(pk_raw, structure=np.ones((5, 5), bool)) & fg & (~stray_chin_leather)

        f_m = cv2.GaussianBlur(f_raw.astype(np.float32), (3, 3), 0.7) * a
        p_m = cv2.GaussianBlur(p_raw.astype(np.float32), (3, 3), 0.7) * a
        pk_m = cv2.GaussianBlur(pk_raw.astype(np.float32), (3, 3), 0.7) * a
        return pk_m, f_m, p_m

    def extract_whole_pickle_512(self, idx: int, scream_boost: float = 0.0) -> np.ndarray:
        """Extracts complete un-occluded `512x607` Pickle Surprise from `vpk[idx]`."""
        src = self.raw_512[idx]
        pk_m, f_m, _ = self._segment_hand_vs_pickle_512(src)
        rgb = src[..., :3].astype(np.float32).copy()
        H, W = rgb.shape[:2]
        yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

        x_sym = 115.0
        mirror_x = np.clip(np.round(2.0 * x_sym - xg), 0, W - 1).astype(np.int32)
        mirror_rgb = rgb[yg.astype(np.int32), mirror_x]
        mirror_pk = pk_m[yg.astype(np.int32), mirror_x]

        occ_zone = (f_m > 0.12) & (yg >= 306.0) & (yg <= 412.0) & (mirror_pk > 0.35)
        occ_w = cv2.GaussianBlur(occ_zone.astype(np.float32), (9, 9), 2.2)
        rgb = rgb * (1.0 - occ_w[..., None]) + mirror_rgb * occ_w[..., None]
        full_a = np.maximum(pk_m, occ_w * mirror_pk)

        if scream_boost > 1e-3:
            ey = 1.0 + 1.05 * scream_boost
            mx_s = 1.0 + 0.50 * scream_boost
            my_s = 1.0 + 0.62 * scream_boost
            rgb_u8 = np.clip(rgb, 0, 255).astype(np.uint8)
            rgb_u8 = warp_lens(rgb_u8, (115.0, 368.0), (54.0, 58.0), mx_s, my_s)
            rgb_u8 = warp_lens(rgb_u8, (86.0, 282.0), (35.0, 31.0), ey, ey)
            rgb_u8 = warp_lens(rgb_u8, (143.0, 283.0), (35.0, 31.0), ey, ey)
            rgb_u8 = warp_lens(rgb_u8, (114.0, 193.0), (38.0, 26.0), 1.0 + 0.50 * scream_boost, 1.0 + 0.50 * scream_boost)
            rgb = rgb_u8.astype(np.float32)

        a_u8 = np.clip(np.round(full_a * 255.0), 0, 255).astype(np.uint8)
        rgb_u8 = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
        rgb_u8[a_u8 == 0] = 0
        return np.dstack([rgb_u8, a_u8])

    def _extract_whole_pickle_ext(self, idx: int, scream_boost: float = 0.0) -> np.ndarray:
        pk512 = self.extract_whole_pickle_512(idx, scream_boost=scream_boost)
        staged = complete_crown_dome_on_stage(pk512, self.pk0_512)
        ext = np.zeros((self.EXT_H, self.EXT_W, 4), dtype=np.uint8)
        ext[:STAGE_H, :STAGE_W] = staged
        return ext

    def _build_gauntlet_and_pickle_layers(self) -> None:
        ref512 = self.raw_512[14]
        H5, W5 = ref512.shape[:2]
        yg5, xg5 = np.mgrid[0:H5, 0:W5].astype(np.float32)
        _, f_m, p_m = self._segment_hand_vs_pickle_512(ref512)
        ref_rgb = ref512[..., :3].astype(np.float32)

        finger_bands = [
            (282, 325, (PAD_L + 64.0, PAD_T + 304.0)),
            (322, 360, (PAD_L + 64.0, PAD_T + 341.0)),
            (356, 392, (PAD_L + 66.0, PAD_T + 374.0)),
            (387, 426, (PAD_L + 68.0, PAD_T + 405.0)),
        ]
        self.closed_fingers_pm: list[tuple[np.ndarray, tuple[float, float]]] = []
        for y0, y1, piv in finger_bands:
            band_w = np.clip(1.0 - np.maximum(0.0, np.maximum(y0 - yg5, yg5 - y1)) / 4.0, 0.0, 1.0)
            fm_i = f_m * band_w
            ext_rgba = np.zeros((self.EXT_H, self.EXT_W, 4), dtype=np.uint8)
            ext_rgba[PAD_T:PAD_T + H5, PAD_L:PAD_L + W5] = np.dstack([
                np.clip(np.round(ref_rgb), 0, 255).astype(np.uint8),
                np.clip(np.round(fm_i * 255.0), 0, 255).astype(np.uint8),
            ])
            self.closed_fingers_pm.append((premul_from_rgba(ext_rgba), piv))

        thumb_poly = Image.new("L", (W5, H5), 0)
        ImageDraw.Draw(thumb_poly).polygon(
            [(168, 240), (252, 238), (256, 394), (212, 424), (168, 392)], fill=255
        )
        thumb_zone = cv2.GaussianBlur(np.asarray(thumb_poly, dtype=np.float32) / 255.0, (9, 9), 2.0)
        not_turquoise = np.where(
            xg5 < 196.0,
            np.clip(((ref_rgb[..., 0] - ref_rgb[..., 2]) + 6.0) / 14.0, 0.0, 1.0),
            1.0,
        )
        thumb_a = p_m * np.clip(thumb_zone * 1.18, 0.0, 1.0) * not_turquoise
        palm_base_a = p_m * np.clip(1.0 - thumb_zone * 1.40, 0.0, 1.0)

        ext_thumb = np.zeros((self.EXT_H, self.EXT_W, 4), dtype=np.uint8)
        ext_thumb[PAD_T:PAD_T + H5, PAD_L:PAD_L + W5] = np.dstack([
            np.clip(np.round(ref_rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(thumb_a * 255.0), 0, 255).astype(np.uint8),
        ])
        self.thumb_pm = premul_from_rgba(ext_thumb)
        self.thumb_pivot = (PAD_L + 210.0, PAD_T + 404.0)

        patch_a = cv2.resize(ref_rgb[404:458, 134:198].copy(), (220, 220), interpolation=cv2.INTER_CUBIC)
        patch_b = cv2.resize(ref_rgb[388:446, 146:206].copy(), (220, 220), interpolation=cv2.INTER_CUBIC)
        wy_l = (0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, 220, dtype=np.float32)))[:, None, None]
        leather_canvas = patch_a * (1.0 - 0.45 * wy_l) + patch_b * (0.45 * wy_l)
        patch = cv2.resize(leather_canvas, (80, 64), interpolation=cv2.INTER_AREA)
        brass_patch = ref_rgb[495:575, 245:345].copy()
        full_leather = np.zeros_like(ref_rgb)
        full_leather[260:480, 35:255] = leather_canvas

        palm_cup_im = Image.new("L", (W5, H5), 0)
        ImageDraw.Draw(palm_cup_im).polygon(
            [(148, 294), (192, 304), (218, 368), (218, 456), (82, 462), (54, 412), (68, 364), (94, 328)],
            fill=255,
        )
        cup_a = cv2.GaussianBlur(np.asarray(palm_cup_im, dtype=np.float32) / 255.0, (11, 11), 2.6)

        hollow = np.exp(-(((xg5 - 134.0) / 46.0) ** 2 + ((yg5 - 372.0) / 50.0) ** 2))
        rim_hi = np.exp(-(((xg5 - 178.0) / 34.0) ** 2 + ((yg5 - 396.0) / 48.0) ** 2))
        c1 = np.exp(-(((yg5 - (332.0 + 0.36 * (xg5 - 85.0))) / 2.6) ** 2)) * ((xg5 > 72) & (xg5 < 185))
        c2 = np.exp(-(((yg5 - (362.0 + 0.48 * (xg5 - 80.0))) / 2.8) ** 2)) * ((xg5 > 78) & (xg5 < 192))
        knuckle_ridge = np.exp(-(((yg5 - (300.0 + 1.05 * (148.0 - xg5))) / 11.0) ** 2)) * ((xg5 > 55) & (xg5 < 160))
        shade = 0.86 - 0.26 * hollow + 0.14 * rim_hi + 0.10 * knuckle_ridge - 0.28 * c1 - 0.24 * c2
        cup_rgb = np.clip(full_leather * shade[..., None], 8.0, 235.0)

        real_w = cv2.GaussianBlur(np.clip(palm_base_a * 1.15, 0.0, 1.0), (9, 9), 2.0)
        comb_a = np.maximum(palm_base_a, cup_a)
        comb_rgb = cup_rgb * (1.0 - real_w[..., None]) + ref_rgb * real_w[..., None]

        bot_feather = np.clip((float(H5 - 1) - yg5) / 15.0, 0.0, 1.0)
        rgt_feather = np.clip((float(W5 - 1) - xg5) / 15.0, 0.0, 1.0)
        edge_f = np.where(yg5 > float(H5 - 17), bot_feather, 1.0)
        edge_f = np.where((xg5 > float(W5 - 17)) & (yg5 > 460.0), np.minimum(edge_f, rgt_feather), edge_f)
        comb_a_f = comb_a * edge_f

        base_ext = np.zeros((self.EXT_H, self.EXT_W, 4), dtype=np.uint8)
        base_ext[PAD_T:PAD_T + H5, PAD_L:PAD_L + W5] = np.dstack([
            np.clip(np.round(comb_rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(comb_a_f * 255.0), 0, 255).astype(np.uint8),
        ])
        base_pm = premul_from_rgba(base_ext)

        cuff_rgba = np.dstack([
            np.clip(np.round(comb_rgb[486:H5, 140:W5]), 0, 255).astype(np.uint8),
            np.clip(np.round(comb_a[486:H5, 140:W5] * 255.0), 0, 255).astype(np.uint8),
        ])
        ch_c, cw_c = cuff_rgba.shape[:2]
        yc_c = np.arange(ch_c, dtype=np.float32)[:, None]
        top_f = np.clip(yc_c / 26.0, 0.0, 1.0)
        cuff_pm_patch = premul_from_rgba(cuff_rgba) * top_f[..., None]
        cuff_pad = np.zeros((self.EXT_H, self.EXT_W, 4), dtype=np.float32)
        y0_c, x0_c = PAD_T + 486, PAD_L + 140
        cuff_pad[y0_c:y0_c + ch_c, x0_c:x0_c + cw_c] = cuff_pm_patch

        ext_accum = np.zeros((self.EXT_H, self.EXT_W, 4), dtype=np.float32)
        for step_k in (4, 3, 2, 1):
            seg = affine_premul(
                cuff_pad,
                pivot=(x0_c + 185.0, y0_c + 60.0),
                tx=64.5 * step_k,
                ty=68.0 * step_k,
                rot_deg=0.0,
                sx=1.0 + 0.018 * step_k,
                sy=1.0 + 0.018 * step_k,
                out_hw=(self.EXT_H, self.EXT_W),
            )
            seg[..., :3] *= (1.0 - 0.045 * step_k)
            ext_accum = over_premul(ext_accum, seg)
        self.palm_vambrace_pm = over_premul(ext_accum, base_pm)

        self.open_fingers_specs = [
            ((PAD_L + 142.0, PAD_T + 306.0), 92.0, 31.0, 21.0, -120.0),
            ((PAD_L + 112.0, PAD_T + 324.0), 102.0, 32.0, 22.0, -135.0),
            ((PAD_L + 86.0,  PAD_T + 352.0), 94.0, 30.0, 20.0, -151.0),
            ((PAD_L + 66.0,  PAD_T + 388.0), 76.0, 27.0, 18.0, -167.0),
        ]
        self.open_finger_strips_pm = [
            self._make_open_finger_template(patch, brass_patch, flen, bw, tw, seed=i)
            for i, (_, flen, bw, tw, _) in enumerate(self.open_fingers_specs)
        ]

        self.pk_shock = premul_from_rgba(self._extract_whole_pickle_ext(20, scream_boost=0.65))
        self.pk_scream = premul_from_rgba(self._extract_whole_pickle_ext(24, scream_boost=0.85))
        self.pk_catch = premul_from_rgba(self._extract_whole_pickle_ext(14, scream_boost=0.0))
        self.pk_calm = premul_from_rgba(self._extract_whole_pickle_ext(0, scream_boost=0.0))

    def _make_open_finger_template(
        self, leather_patch: np.ndarray, brass_patch: np.ndarray, length: float, base_w: float, tip_w: float, seed: int
    ) -> np.ndarray:
        CW, CH = 168, 96
        px0, py0 = 26.0, 52.0
        yg, xg = np.mgrid[0:CH, 0:CW].astype(np.float32)
        u = (xg - px0) / length
        u_c = np.clip(u, 0.0, 1.0)
        center_y = py0 - 7.5 * (u_c ** 1.65)
        half_w = 0.5 * (base_w * (1.0 - u_c) + tip_w * u_c) * (1.0 + 0.06 * np.sin(u_c * math.pi * 2.0))
        v = (yg - center_y) / np.maximum(half_w, 1.0)

        dist_center = np.hypot((u - u_c) * length, yg - center_y)
        alpha = np.clip((half_w - dist_center + 0.8) / 1.5, 0.0, 1.0)

        tex = cv2.resize(np.roll(leather_patch, shift=seed * 19, axis=1), (CW, CH), interpolation=cv2.INTER_CUBIC)
        brass_tex = cv2.resize(np.roll(brass_patch, shift=seed * 23, axis=0), (CW, CH), interpolation=cv2.INTER_CUBIC)
        cyl = np.sqrt(np.clip(1.0 - v * v, 0.0, 1.0))
        light = 0.54 + 0.50 * cyl - 0.16 * v
        pip = np.exp(-(((u - 0.38) / 0.034) ** 2))
        dip = np.exp(-(((u - 0.70) / 0.030) ** 2))
        mcp_ao = np.exp(-(((u - 0.04) / 0.08) ** 2)) * 0.22
        rgb = tex * (light * (1.0 - 0.38 * pip - 0.32 * dip - mcp_ao))[..., None]

        plate1 = ((u > 0.08) & (u < 0.33)).astype(np.float32)
        plate2 = ((u > 0.43) & (u < 0.65)).astype(np.float32)
        plate_m = cv2.GaussianBlur((plate1 + plate2) * np.clip((-v - 0.10) / 0.45, 0.0, 1.0), (5, 5), 1.0)
        brass_lit = brass_tex * (0.68 + 0.46 * cyl)[..., None]
        rgb = rgb * (1.0 - 0.72 * plate_m[..., None]) + brass_lit * (0.72 * plate_m[..., None])

        tip_ao = np.clip((u - 0.82) / 0.18, 0.0, 1.0) * 0.15
        rgb *= (1.0 - tip_ao)[..., None]

        alpha = alpha * np.clip((u + 0.14) / 0.16, 0.0, 1.0)
        rgba = np.dstack([
            np.clip(np.round(rgb), 0, 255).astype(np.uint8),
            np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
        ])
        return premul_from_rgba(rgba)

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
        EH, EW = self.EXT_H, self.EXT_W
        hand_pm = np.zeros((EH, EW, 4), dtype=np.float32)

        if open_amount > 0.22:
            ext_w = min(1.0, (open_amount - 0.22) / 0.36)
            for f_i, ((mx, my), _, _, _, rest_ang) in enumerate(self.open_fingers_specs):
                spread_extra = (f_i - 1.5) * 4.2 * open_amount
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
                    out_hw=(EH, EW),
                )
                hand_pm = over_premul(hand_pm, f_pm)

        hand_pm = over_premul(hand_pm, self.palm_vambrace_pm)

        thumb_deg = -6.0 * squeeze + 26.0 * open_amount
        thumb_tx = -3.0 * squeeze + 7.5 * open_amount
        t_pm = affine_premul(
            self.thumb_pm,
            pivot=self.thumb_pivot,
            tx=thumb_tx,
            ty=-2.5 * open_amount,
            rot_deg=thumb_deg,
            out_hw=(EH, EW),
        )
        hand_pm = over_premul(hand_pm, t_pm)

        if pickle_mode != "none":
            pk_src = {
                "shock": self.pk_shock,
                "scream": self.pk_scream,
                "catch": self.pk_catch,
                "calm": self.pk_calm,
            }[pickle_mode]
            sx_pk = pk_scale_x * (1.0 - 0.16 * squeeze)
            sy_pk = pk_scale_y * (1.0 + 0.10 * squeeze)
            pk_pm = affine_premul(
                pk_src,
                pivot=(PAD_L + 115.0, PAD_T + 345.0),
                tx=pk_rel_tx,
                ty=pk_rel_ty - 5.0 * squeeze,
                rot_deg=pk_rel_rot,
                sx=sx_pk,
                sy=sy_pk,
                out_hw=(EH, EW),
            )
            hand_pm = over_premul(hand_pm, pk_pm)

        if open_amount < 0.56:
            curl_vis = np.clip(1.0 - max(0.0, open_amount - 0.16) / 0.36, 0.0, 1.0)
            for f_i, (cf_pm, piv) in enumerate(self.closed_fingers_pm):
                peel_tx = 6.0 * squeeze - 24.0 * open_amount
                peel_ty = (-3.0 + f_i * 2.0) * open_amount
                peel_rot = 4.5 * squeeze - (26.0 + f_i * 4.5) * open_amount
                w_cf = affine_premul(
                    cf_pm * curl_vis,
                    pivot=piv,
                    tx=peel_tx,
                    ty=peel_ty,
                    rot_deg=peel_rot,
                    sx=1.0 - 0.12 * open_amount,
                    sy=1.0,
                    out_hw=(EH, EW),
                )
                hand_pm = over_premul(hand_pm, w_cf)

        warped_ext = affine_premul(
            hand_pm,
            pivot=(PAD_L + 395.0, PAD_T + 575.0),
            tx=arm_tx,
            ty=arm_ty,
            rot_deg=arm_rot_deg,
            sx=arm_scale,
            sy=arm_scale,
            out_hw=(EH, EW),
        )
        return warped_ext[:STAGE_H, :STAGE_W]

    def _draw_violent_whip_slash_fx(self, pm: np.ndarray, strength: float, progress: float) -> np.ndarray:
        if strength <= 0.02:
            return pm
        H, W = self.h, self.w
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(fx)
        for k_arc, (off_x, off_y, width_px, col) in enumerate([
            (0.0, 0.0, 14, (225, 255, 255)),
            (22.0, 32.0, 8, (115, 240, 250)),
            (-16.0, 48.0, 5, (255, 248, 210)),
        ]):
            pts = []
            u0 = max(0.0, progress - 0.46)
            u1 = min(1.0, progress + 0.16)
            if u1 - u0 < 0.08:
                continue
            for s_i in range(20):
                u = u0 + (u1 - u0) * (s_i / 19.0)
                p0 = (PAD_L + 345.0 + off_x, PAD_T + 58.0 + off_y)
                p1 = (PAD_L + 135.0 + off_x, PAD_T + 88.0 + off_y)
                p2 = (PAD_L - 52.0 + off_x,  PAD_T + 295.0 + off_y)
                bx = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0]
                by = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1]
                pts.append((bx, by))
            for i in range(len(pts) - 1):
                taper = math.sin(math.pi * (i + 0.5) / max(1, len(pts) - 1))
                scale_a = (0.95 if k_arc == 0 else (0.62 if k_arc == 1 else 0.45))
                a_val = int(round(170.0 * strength * taper * scale_a))
                if a_val > 3:
                    w_seg = max(1, int(round(width_px * taper)))
                    d.line([pts[i], pts[i + 1]], fill=(col[0], col[1], col[2], a_val), width=w_seg)
        fx_blur = fx.filter(ImageFilter.GaussianBlur(2.8))
        return over_premul(pm, premul_from_rgba(np.asarray(fx_blur, dtype=np.uint8)))

    def eval_throw_curve(self, u: float) -> dict:
        def sstep(a: float, b: float, x: float) -> float:
            t = max(0.0, min(1.0, (x - a) / max(1e-6, b - a)))
            return t * t * (3.0 - 2.0 * t)

        if u < 0.22:
            w = u / 0.22
            coil = 1.0 - (1.0 - w) ** 2.6
            tremor = math.sin(w * math.pi * 6.0) * 3.5 * (w ** 1.5)
            return dict(
                arm_tx=62.0 * coil + tremor,
                arm_ty=-26.0 * coil - abs(tremor) * 0.4,
                arm_rot_deg=25.0 * coil + tremor * 0.4,
                arm_scale=1.0 + 0.05 * coil,
                open_amount=0.0,
                squeeze=min(1.05, coil * 1.18),
                pickle_mode="scream" if w > 0.38 else "shock",
                pk_rel_tx=0.0,
                pk_rel_ty=0.0,
                pk_rel_rot=0.0,
                pk_scale_x=1.0,
                pk_scale_y=1.0,
                whip_fx=0.0,
                whip_prog=0.0,
            )
        elif u < 0.39:
            w = (u - 0.22) / 0.17
            whip = w * w * (2.25 - 1.25 * w)
            whip = max(0.0, min(1.06, whip))

            arm_tx = 62.0 + (-102.0) * whip
            arm_ty = -26.0 + (-68.0) * whip
            arm_rot = 25.0 + (-58.0) * whip
            arm_sc = 1.05 + 0.08 * math.sin(w * math.pi)

            open_amt = sstep(0.18, 0.56, w)
            sqz = max(0.0, 1.05 - 1.05 * sstep(0.0, 0.28, w))

            if w < 0.24:
                pk_mode = "scream"
                pk_tx = pk_ty = pk_rot = 0.0
                pk_sx = pk_sy = 1.0
            elif w < 0.64:
                fly = (w - 0.24) / 0.40
                pk_mode = "scream"
                pk_tx = -225.0 * (fly ** 1.12)
                pk_ty = -165.0 * (fly ** 1.05)
                pk_rot = -46.0 * fly
                pk_sx = max(0.32, 1.0 - 0.56 * fly)
                pk_sy = max(0.32, 1.10 - 0.60 * fly)
            else:
                pk_mode = "none"
                pk_tx = pk_ty = pk_rot = 0.0
                pk_sx = pk_sy = 1.0

            whip_strength = math.sin(min(1.0, max(0.0, (w - 0.04) / 0.94)) * math.pi)
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
                whip_fx=whip_strength,
                whip_prog=w,
            )
        elif u < 0.49:
            w = (u - 0.39) / 0.10
            jolt = math.sin(w * math.pi * 2.5) * (1.0 - w) * 9.5
            return dict(
                arm_tx=-40.0 - 12.0 * w + jolt,
                arm_ty=-94.0 + 32.0 * (w ** 1.5) - jolt * 0.6,
                arm_rot_deg=-33.0 - 4.0 * w + jolt * 0.45,
                arm_scale=1.05 - 0.03 * w,
                open_amount=1.0,
                squeeze=0.0,
                pickle_mode="none",
                pk_rel_tx=0.0,
                pk_rel_ty=0.0,
                pk_rel_rot=0.0,
                pk_scale_x=1.0,
                pk_scale_y=1.0,
                whip_fx=0.45 * (1.0 - w),
                whip_prog=1.0,
            )
        elif u < 0.72:
            w = (u - 0.49) / 0.23
            ease = w * w * (2.0 - w)
            return dict(
                arm_tx=-52.0 + 26.0 * ease,
                arm_ty=-62.0 + 475.0 * ease,
                arm_rot_deg=-37.0 + 12.0 * ease,
                arm_scale=1.02 - 0.02 * ease,
                open_amount=1.0 - 0.25 * ease,
                squeeze=0.0,
                pickle_mode="none",
                pk_rel_tx=0.0,
                pk_rel_ty=0.0,
                pk_rel_rot=0.0,
                pk_scale_x=1.0,
                pk_scale_y=1.0,
                whip_fx=0.0,
                whip_prog=1.0,
            )
        else:
            w = (u - 0.72) / 0.28
            if w < 0.66:
                t1 = w / 0.66
                e1 = 1.0 - (1.0 - t1) ** 2.8
                arm_ty = 413.0 * (1.0 - e1) - 16.0 * e1
                arm_tx = 48.0 * (1.0 - e1)
                arm_rot = 16.0 * (1.0 - e1) - 3.0 * e1
                sqz = 0.55 * math.sin(t1 * math.pi)
            else:
                t2 = (w - 0.66) / 0.34
                e2 = sstep(0.0, 1.0, t2)
                arm_ty = -16.0 * (1.0 - e2)
                arm_tx = 0.0
                arm_rot = -3.0 * (1.0 - e2)
                sqz = 0.35 * (1.0 - e2)
            return dict(
                arm_tx=arm_tx,
                arm_ty=arm_ty,
                arm_rot_deg=arm_rot,
                arm_scale=1.0,
                open_amount=0.0,
                squeeze=sqz,
                pickle_mode="catch" if w < 0.72 else "calm",
                pk_rel_tx=0.0,
                pk_rel_ty=0.0,
                pk_rel_rot=0.0,
                pk_scale_x=1.0,
                pk_scale_y=1.0,
                whip_fx=0.0,
                whip_prog=0.0,
            )

    def render_violent_throw_sequence(self, num_frames: int = 48) -> list[np.ndarray]:
        out: list[np.ndarray] = []
        du_frame = 1.0 / float(num_frames)
        for fi in range(num_frames):
            u_mid = (fi + 0.5) / float(num_frames)
            mid_cfg = self.eval_throw_curve(u_mid)

            if 0.21 <= u_mid <= 0.40:
                n_sub = 9
                shutter = 0.48 * du_frame
            else:
                n_sub = 1
                shutter = 0.0

            if n_sub == 1:
                acc_pm = self.render_articulated_pose(
                    arm_tx=mid_cfg["arm_tx"],
                    arm_ty=mid_cfg["arm_ty"],
                    arm_rot_deg=mid_cfg["arm_rot_deg"],
                    arm_scale=mid_cfg["arm_scale"],
                    open_amount=mid_cfg["open_amount"],
                    squeeze=mid_cfg["squeeze"],
                    pickle_mode=mid_cfg["pickle_mode"],
                    pk_rel_tx=mid_cfg["pk_rel_tx"],
                    pk_rel_ty=mid_cfg["pk_rel_ty"],
                    pk_rel_rot=mid_cfg["pk_rel_rot"],
                    pk_scale_x=mid_cfg["pk_scale_x"],
                    pk_scale_y=mid_cfg["pk_scale_y"],
                )
            else:
                acc_pm = np.zeros((self.h, self.w, 4), dtype=np.float32)
                w_sum = 0.0
                for s_i in range(n_sub):
                    rel = (s_i / (n_sub - 1)) - 0.5
                    wt = math.exp(-0.5 * ((rel / 0.26) ** 2))
                    u_s = max(0.0, min(0.9999, u_mid + rel * shutter))
                    cfg = self.eval_throw_curve(u_s)
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

            if mid_cfg["whip_fx"] > 0.02:
                acc_pm = self._draw_violent_whip_slash_fx(acc_pm, mid_cfg["whip_fx"], mid_cfg["whip_prog"])
            out.append(rgba_from_premul(acc_pm))
        return out

    def render_smooth_idle_sequence(self, num_frames: int = 72) -> list[np.ndarray]:
        positions = np.linspace(0.0, len(self.frames) - 1, num_frames)
        out: list[np.ndarray] = []
        n = len(self.frames)
        for pos in positions:
            i0 = int(np.floor(pos))
            i1 = min(i0 + 1, n - 1)
            out.append(flow_interp_rgba(self.frames[i0], self.frames[i1], float(pos - i0)))
        return out
