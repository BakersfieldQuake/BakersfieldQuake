"""360° Standing / Character Pickle Surprise Animation Engine & 3D Inflatable Mesh Builder.

Eliminates all jank in the original `progs/pickle.md3` & `pickle3d`:
  1. Decontaminates white studio rim bleed and restores rich studio sRGB from `progs/pickle_00..15.png`.
  2. Repairs the `MinFilter` profile eye cutout notch on `pickle_06` and `pickle_07`.
  3. Builds 4 full-16-angle expressive pose sets (64 textures -> `progs/pickle.md3_0..63.skin`):
       - Set 0 (`0..15`):  Singing Diva ("Pickle...")
       - Set 1 (`16..31`): Cheeky Puffed-Cheek Kissy Wink-Blink (grafted from `vpk_14` + 360° warps)
       - Set 2 (`32..47`): Wild Bug-Eyes + Sticking-Out Pink Tongue ("...Surprise!", grafted from `vpk_24`)
       - Set 3 (`48..63`): Full 360° Over-Pressurized Giant Pre-Blast SCREAM across all 16 angles!
  4. Builds a 36-frame base-planted 3D deforming `9x17` ribbon-grid `progs/pickle.md3` (ZERO collapsed
     cards, so DarkPlaces NEVER shrinks/pulses when changing views or expressions; `self.skin` swaps
     views/faces instantaneously while `self.frame` hardware-lerps smooth 3D S-curve inflatable waves,
     squash-and-stretch, and pre-explosion balloon swelling!).
  5. Upgrades `progs/pickle_face_*.png` (`pickle_bomb.md3` sticky grenade animated face) to a smooth
     multi-expression loop (sing -> cheeky pucker -> bug-eyed tongue -> gasp).
  6. Rebuilds the watertight 3D `pickle3d` mesh with a bright sRGB texture & 4 multi-frame 3D clips!
"""
from __future__ import annotations

import math
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage, sparse
from skimage import measure

import pickle_throw_rig as ptr


# Front & 3/4 facial landmarks in 512x512 turntable space:
# view_idx -> (left_eye, right_eye, mouth, third_eye, cos_yaw_foreshorten)
FRONT_LANDMARKS: dict[int, tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float], float]] = {
    0:  ((231.0, 368.0), (281.0, 368.0), (256.0, 441.0), (256.0, 282.0), 1.00),
    1:  ((224.0, 368.0), (276.0, 368.0), (248.0, 440.0), (250.0, 282.0), 0.92),
    2:  ((207.0, 365.0), (263.0, 366.0), (233.0, 440.0), (239.0, 282.0), 0.74),
    3:  ((195.0, 366.0), (244.0, 367.0), (216.0, 440.0), (224.0, 283.0), 0.46),
    15: ((240.0, 365.0), (292.0, 368.0), (270.0, 441.0), (266.0, 282.0), 0.92),
    14: ((252.0, 366.0), (305.0, 367.0), (284.0, 440.0), (277.0, 282.0), 0.74),
    13: ((268.0, 367.0), (318.0, 366.0), (298.0, 440.0), (290.0, 283.0), 0.46),
}

# Profile facial landmarks: view_idx -> (profile_eye, profile_mouth, ear_wing_center, dir_sign [-1=looking left, +1=looking right])
PROFILE_LANDMARKS: dict[int, tuple[tuple[float, float], tuple[float, float], tuple[float, float], float]] = {
    4:  ((226.0, 367.0), (199.0, 441.0), (296.0, 405.0), -1.0),
    5:  ((216.0, 367.0), (192.0, 440.0), (305.0, 405.0), -1.0),
    6:  ((206.0, 367.0), (188.0, 439.0), (308.0, 405.0), -1.0),
    12: ((286.0, 367.0), (313.0, 441.0), (216.0, 405.0), +1.0),
    11: ((296.0, 367.0), (320.0, 440.0), (207.0, 405.0), +1.0),
    10: ((304.0, 367.0), (322.0, 439.0), (204.0, 405.0), +1.0),
}


def decontaminate_and_boost_turntable(raw_rgba: np.ndarray) -> np.ndarray:
    """Decontaminates white studio rim on `DIM=0.30` `pickle_00..15.png` and restores vibrant studio sRGB."""
    rgb = raw_rgba[..., :3].astype(np.float32)
    a_raw = raw_rgba[..., 3].astype(np.float32) / 255.0
    fg = a_raw > 0.45

    dist_in = ndimage.distance_transform_edt(fg)
    dist_out = ndimage.distance_transform_edt(~fg)
    sdf = dist_in - dist_out

    hi = rgb.max(axis=2)
    lo = rgb.min(axis=2)
    sat = (hi - lo) / np.maximum(hi, 1.0)
    pale_rim = (dist_in <= 5.5) & (lo > 38.0) & (sat < 0.30)

    clean_seed = (dist_in > 3.2) & (~pale_rim) & fg
    if not np.any(clean_seed):
        clean_seed = (dist_in > 1.5) & fg
    if np.any(clean_seed):
        _, idx = ndimage.distance_transform_edt(~clean_seed, return_indices=True)
        nearest_rgb = rgb[idx[0], idx[1]]
        rim_w = np.clip((dist_in - 1.4) / 2.8, 0.0, 1.0)
        rim_w = np.where(pale_rim, 0.0, rim_w)[..., None]
        rgb_clean = rgb * rim_w + nearest_rgb * (1.0 - rim_w)
    else:
        rgb_clean = rgb.copy()

    # Invert `DIM=0.30, Contrast=1.3` smoothly into crisp studio sRGB (matching vpk studio brightness)
    nrm = rgb_clean / 255.0
    lifted = nrm * 3.25
    lifted = lifted / (1.0 + 0.24 * (lifted ** 2))
    lifted = np.clip(lifted, 0.0, 1.0) ** 0.92

    alpha_aa = np.clip((sdf - 0.65 + 0.65) / 1.3, 0.0, 1.0)
    a_u8 = np.clip(np.round(alpha_aa * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(lifted * 255.0), 0, 255).astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return np.dstack([rgb_u8, a_u8])


def repair_profile_eye_notches(srgb_views: list[np.ndarray]) -> list[np.ndarray]:
    """Fixes the rectangular dark artifact over the side eye on `pickle_06` and `pickle_07`
    using the clean adjacent profile eye from `pickle_05`."""
    out = [v.copy() for v in srgb_views]
    ref5 = srgb_views[5].astype(np.float32)
    H, W = ref5.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    for bad_k, dx, cx_t in ((6, -9, 204.0), (7, -18, 195.0)):
        dst = out[bad_k].astype(np.float32)
        shifted = np.roll(ref5, shift=dx, axis=1)
        # Rectangular dark box in pickle_06/07 sits at x ~ 182..226, y ~ 352..386
        w_box = np.exp(-(((xg - cx_t) / 21.0) ** 2 + ((yg - 368.0) / 16.0) ** 2))
        inside = (dst[..., 3] > 140.0) & (shifted[..., 3] > 140.0)
        blend = np.clip(w_box * 1.25, 0.0, 1.0) * inside
        blend = cv2.GaussianBlur(blend.astype(np.float32), (7, 7), 1.6)
        dst[..., :3] = dst[..., :3] * (1.0 - blend[..., None]) + shifted[..., :3] * blend[..., None]
        u8 = np.clip(np.round(dst), 0, 255).astype(np.uint8)
        u8[u8[..., 3] == 0, :3] = 0
        out[bad_k] = u8
    return out


def warp_rgba_lens(
    rgba: np.ndarray,
    center: tuple[float, float],
    radii: tuple[float, float],
    sx: float,
    sy: float,
    warp_alpha: bool = False,
) -> np.ndarray:
    """Smooth local magnification/compression around `center`."""
    h, w = rgba.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs - center[0]) / radii[0]
    ny = (ys - center[1]) / radii[1]
    q = np.clip(1.0 - (nx * nx + ny * ny), 0.0, 1.0) ** 2
    gx = 1.0 - (1.0 - 1.0 / sx) * q
    gy = 1.0 - (1.0 - 1.0 / sy) * q
    mx = (center[0] + (xs - center[0]) * gx).astype(np.float32)
    my = (center[1] + (ys - center[1]) * gy).astype(np.float32)
    if warp_alpha:
        pm = ptr.premul_from_rgba(rgba)
        w_pm = cv2.remap(pm, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        return ptr.rgba_from_premul(w_pm)
    else:
        rgb_w = cv2.remap(rgba[..., :3], mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        out = np.dstack([rgb_w, rgba[..., 3]])
        out[out[..., 3] == 0, :3] = 0
        return out


def _graft_vpk_face_onto_turntable(
    base_view: np.ndarray,
    vpk_whole_pickle_512: np.ndarray,
    view_k: int,
) -> np.ndarray:
    """Seamlessly grafts an expressive face (`pucker` from `vpk_14` or `tongue` from `vpk_24`)
    onto turntable front/3-quarter view `view_k`, matching color & perspective foreshortening!"""
    le, re_, m, _, cos_f = FRONT_LANDMARKS[view_k]
    eye_mid_dst = (0.5 * (le[0] + re_[0]), 0.5 * (le[1] + re_[1]))
    eye_to_mouth_dst = m[1] - eye_mid_dst[1]  # ~73 px in turntable 512x512

    # In vpk 512x607 space: eye_mid = (114.5, 282.5), mouth = (115.0, 362.0) -> dist ~ 79.5 px
    src_eye_mid = (114.5, 282.5)
    scale_y = eye_to_mouth_dst / 81.0
    scale_x = scale_y * (0.94 * cos_f)

    # Warp vpk face into 512x512 turntable coordinates
    src_pm = ptr.premul_from_rgba(vpk_whole_pickle_512)
    M = np.array([
        [scale_x, 0.0, eye_mid_dst[0] - scale_x * src_eye_mid[0]],
        [0.0, scale_y, eye_mid_dst[1] - scale_y * src_eye_mid[1]],
    ], dtype=np.float32)
    warped_pm = cv2.warpAffine(
        src_pm, M, (512, 512), flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
    )
    warped_rgba = ptr.rgba_from_premul(warped_pm)

    # Color-match cyan skin luminance/chroma gently to `base_view`'s forehead/cheek tone
    dst_f = base_view.astype(np.float32)
    src_f = warped_rgba.astype(np.float32)

    H, W = 512, 512
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    rx = 56.0 * cos_f
    ry_top = 44.0
    ry_bot = 68.0
    dy = yg - (eye_mid_dst[1] + 34.0)
    ry = np.where(dy < 0, ry_top, ry_bot)
    oval = np.clip(1.0 - (((xg - eye_mid_dst[0]) / max(18.0, rx)) ** 2 + (dy / ry) ** 2), 0.0, 1.0)
    mask_face = cv2.GaussianBlur(np.clip(oval * 1.9, 0.0, 1.0).astype(np.float32), (17, 17), 5.0)
    mask_face *= (src_f[..., 3] / 255.0)

    # Allow pink tongue extending below chin in tongue pose (`dy > 38`) to extend alpha cleanly!
    is_tongue = (src_f[..., 0] - src_f[..., 2] > 20.0) & (yg > m[1] - 6.0) & (src_f[..., 3] > 90.0)
    tongue_w = cv2.GaussianBlur(is_tongue.astype(np.float32), (5, 5), 1.2)
    blend = np.clip(np.maximum(mask_face, tongue_w), 0.0, 1.0)

    # Match cyan cheek color subtly while keeping pink tongue & white sclera untouched
    cyan_src = (src_f[..., 2] - src_f[..., 0]) > 35.0
    if np.any(cyan_src & (mask_face > 0.4)):
        s_med = np.median(src_f[cyan_src & (mask_face > 0.4), :3], axis=0)
        d_zone = ((dst_f[..., 2] - dst_f[..., 0]) > 35.0) & (mask_face > 0.3)
        if np.any(d_zone):
            d_med = np.median(dst_f[d_zone, :3], axis=0)
            gain = np.clip(d_med / np.maximum(s_med, 10.0), 0.78, 1.22)
            # Apply gain only to cyan pixels, not pink tongue or white eyes
            cyan_w = np.clip((src_f[..., 2] - src_f[..., 0] - 10.0) / 40.0, 0.0, 1.0)[..., None]
            src_f[..., :3] = np.clip(src_f[..., :3] * (1.0 - cyan_w + cyan_w * gain[None, None, :]), 0.0, 255.0)

    inside_base = dst_f[..., 3] / 255.0
    out_a = np.clip(np.maximum(inside_base, tongue_w * (src_f[..., 3] / 255.0)), 0.0, 1.0)
    w_rgb = blend * np.where(tongue_w > 0.25, 1.0, inside_base)
    out_rgb = dst_f[..., :3] * (1.0 - w_rgb[..., None]) + src_f[..., :3] * w_rgb[..., None]

    a_u8 = np.clip(np.round(out_a * 255.0), 0, 255).astype(np.uint8)
    rgb_u8 = np.clip(np.round(out_rgb), 0, 255).astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return np.dstack([rgb_u8, a_u8])


def build_four_16view_pose_sets(
    srgb_views: list[np.ndarray],
    rig_throw: ptr.PickleThrowRig,
) -> list[list[np.ndarray]]:
    """Builds 4 full-16-angle studio sRGB pose sets (`[set_0, set_1, set_2, set_3]`, each 16 x `512x512` RGBA):
      - Set 0: Singing Diva (clean studio base)
      - Set 1: Cheeky Puffed-Cheek Wink-Blink
      - Set 2: Wild Bug-Eyes + Pink Tongue Out
      - Set 3: Full 360° Giant Pre-Blast SCREAM!
    """
    # Extract clean 512x607 un-occluded whole pickles for pucker (14) and tongue (24)
    vpk14_whole = rig_throw._extract_whole_pickle_ext(14, scream_boost=0.0)[
        ptr.PAD_T:ptr.PAD_T + 607, ptr.PAD_L:ptr.PAD_L + 512
    ]
    vpk24_whole = rig_throw._extract_whole_pickle_ext(24, scream_boost=0.35)[
        ptr.PAD_T:ptr.PAD_T + 607, ptr.PAD_L:ptr.PAD_L + 512
    ]

    set_sing = [v.copy() for v in srgb_views]
    set_pucker: list[np.ndarray] = []
    set_tongue: list[np.ndarray] = []
    set_scream: list[np.ndarray] = []

    for k in range(16):
        base = srgb_views[k]

        # ---------------- SET 1: CHEEKY PUCKER / BLINK ----------------
        if k in (0, 1, 2, 14, 15):
            puk = _graft_vpk_face_onto_turntable(base, vpk14_whole, k)
            # Plump cheeks slightly outward for extra cartoon charm
            _, _, m, _, _ = FRONT_LANDMARKS[k]
            puk = warp_rgba_lens(puk, (m[0], m[1] - 18.0), (68.0, 48.0), 1.12, 0.96, warp_alpha=True)
            set_pucker.append(puk)
        elif k in FRONT_LANDMARKS:
            le, re_, m, _, _ = FRONT_LANDMARKS[k]
            puk = warp_rgba_lens(base, m, (42.0, 34.0), 0.72, 0.68, warp_alpha=False)
            puk = warp_rgba_lens(puk, le, (28.0, 22.0), 1.0, 0.58, warp_alpha=False)
            puk = warp_rgba_lens(puk, re_, (28.0, 22.0), 1.0, 0.58, warp_alpha=False)
            set_pucker.append(puk)
        elif k in PROFILE_LANDMARKS:
            pe, pm_xy, wing, _ = PROFILE_LANDMARKS[k]
            puk = warp_rgba_lens(base, pm_xy, (36.0, 32.0), 0.76, 0.72, warp_alpha=True)
            puk = warp_rgba_lens(puk, pe, (26.0, 22.0), 1.0, 0.62, warp_alpha=False)
            puk = warp_rgba_lens(puk, wing, (46.0, 56.0), 1.08, 1.06, warp_alpha=True)
            set_pucker.append(puk)
        else:
            # Back views (7, 8, 9): subtle ear-wing & crown breath
            puk = warp_rgba_lens(base, (256.0, 402.0), (88.0, 65.0), 1.07, 1.04, warp_alpha=True)
            set_pucker.append(puk)

        # ---------------- SET 2: BUG-EYES + PINK TONGUE OUT ----------------
        if k in (0, 1, 2, 14, 15):
            tng = _graft_vpk_face_onto_turntable(base, vpk24_whole, k)
            set_tongue.append(tng)
        elif k in FRONT_LANDMARKS:
            le, re_, m, e3, _ = FRONT_LANDMARKS[k]
            tng = warp_rgba_lens(base, m, (46.0, 42.0), 1.35, 1.48, warp_alpha=True)
            tng = warp_rgba_lens(tng, le, (36.0, 30.0), 1.65, 1.65, warp_alpha=False)
            tng = warp_rgba_lens(tng, re_, (36.0, 30.0), 1.65, 1.65, warp_alpha=False)
            tng = warp_rgba_lens(tng, e3, (34.0, 24.0), 1.28, 1.28, warp_alpha=False)
            set_tongue.append(tng)
        elif k in PROFILE_LANDMARKS:
            pe, pm_xy, wing, d_sgn = PROFILE_LANDMARKS[k]
            tng = warp_rgba_lens(base, pm_xy, (42.0, 42.0), 1.30, 1.45, warp_alpha=True)
            tng = warp_rgba_lens(tng, pe, (34.0, 28.0), 1.65, 1.65, warp_alpha=False)
            # Composite the real photographed pink tongue from `vpk24_whole` rotated sideways out of the profile mouth!
            t_crop = vpk24_whole[358:432, 92:138].copy()
            tc_rgb = t_crop[..., :3].astype(np.float32)
            # Isolate only the real pink tongue pixels (high R - B, warm pink)
            pink_m = ((tc_rgb[..., 0] - tc_rgb[..., 2]) > 22.0) & (t_crop[..., 3] > 90)
            tc_a = cv2.GaussianBlur(pink_m.astype(np.float32), (3, 3), 0.8) * (t_crop[..., 3].astype(np.float32) / 255.0)
            # Darken tongue root (top of crop) so it emerges naturally from inside the dark mouth shadow
            th_c = t_crop.shape[0]
            root_shade = (0.42 + 0.58 * np.clip(np.arange(th_c, dtype=np.float32) / 26.0, 0.0, 1.0))[:, None, None]
            tc_rgba = np.dstack([
                np.clip(np.round(tc_rgb * root_shade), 0, 255).astype(np.uint8),
                np.clip(np.round(tc_a * 255.0), 0, 255).astype(np.uint8),
            ])
            if d_sgn > 0:
                tc_rgba = tc_rgba[:, ::-1, :].copy()
            # Place into 512x512 and rotate ~54 deg outward along d_sgn
            t_canvas = np.zeros((512, 512, 4), dtype=np.uint8)
            ox_t = int(round(pm_xy[0] - 23))
            oy_t = int(round(pm_xy[1] - 8))
            t_canvas[oy_t:oy_t + tc_rgba.shape[0], ox_t:ox_t + tc_rgba.shape[1]] = tc_rgba
            t_pm = ptr.affine_premul(
                ptr.premul_from_rgba(t_canvas),
                pivot=pm_xy,
                tx=d_sgn * 5.0,
                ty=2.0,
                rot_deg=-d_sgn * 52.0,
                sx=0.68,
                sy=0.68,
                out_hw=(512, 512),
            )
            tng = ptr.rgba_from_premul(ptr.over_premul(ptr.premul_from_rgba(tng), t_pm))
            set_tongue.append(tng)
        else:
            tng = warp_rgba_lens(base, (256.0, 395.0), (92.0, 70.0), 1.12, 1.08, warp_alpha=True)
            set_tongue.append(tng)

        # ---------------- SET 3: FULL 360° GIANT PRE-BLAST SCREAM ----------------
        if k in FRONT_LANDMARKS:
            le, re_, m, e3, _ = FRONT_LANDMARKS[k]
            scr = warp_rgba_lens(base, (256.0, 395.0), (115.0, 105.0), 1.10, 1.06, warp_alpha=True)
            scr = warp_rgba_lens(scr, m, (78.0, 62.0), 1.95, 2.05, warp_alpha=True)
            scr = warp_rgba_lens(scr, le, (62.0, 48.0), 2.45, 2.45, warp_alpha=False)
            scr = warp_rgba_lens(scr, re_, (62.0, 48.0), 2.45, 2.45, warp_alpha=False)
            scr = warp_rgba_lens(scr, e3, (48.0, 34.0), 1.65, 1.65, warp_alpha=False)
            set_scream.append(scr)
        elif k in PROFILE_LANDMARKS:
            pe, pm_xy, wing, _ = PROFILE_LANDMARKS[k]
            scr = warp_rgba_lens(base, (256.0, 395.0), (118.0, 108.0), 1.12, 1.07, warp_alpha=True)
            scr = warp_rgba_lens(scr, pm_xy, (64.0, 58.0), 1.75, 1.95, warp_alpha=True)
            scr = warp_rgba_lens(scr, pe, (54.0, 44.0), 2.25, 2.25, warp_alpha=False)
            scr = warp_rgba_lens(scr, wing, (58.0, 68.0), 1.25, 1.22, warp_alpha=True)
            set_scream.append(scr)
        else:
            # Back views (7, 8, 9): swollen head & dramatic flared golden ear-wings + bulging crown!
            scr = warp_rgba_lens(base, (256.0, 395.0), (120.0, 110.0), 1.24, 1.15, warp_alpha=True)
            scr = warp_rgba_lens(scr, (256.0, 180.0), (98.0, 130.0), 1.16, 1.08, warp_alpha=True)
            set_scream.append(scr)

    return [set_sing, set_pucker, set_tongue, set_scream]


def build_deforming_balloon_md3_dict(half: float = 10.0) -> dict:
    """Builds the 36-frame base-planted 3D deforming `9x17` ribbon-grid `progs/pickle.md3`!
      - Frames `0..23`:  24-frame seamless Wacky-Waving Inflatable Diva Dance (S-curve wave + bounce)
      - Frames `24..35`: 12-frame Pre-Blast Over-Inflation Balloon Swell & Violent Shudder
    Zero collapsed cards: all 36 frames share the exact same 1-surface grid (`card`), while
    `progs/pickle.md3_0..63.skin` swaps viewing angle & facial expression instantaneously!
    """
    NU, NV = 9, 17
    st: list[tuple[float, float]] = []
    base_uv_grid: list[tuple[float, float]] = []
    for j in range(NV):
        h_frac = j / float(NV - 1)  # 0 at bottom (z=-half), 1 at top (z=+half)
        for i in range(NU):
            u_frac = i / float(NU - 1)  # 0 at +Y (picture-left), 1 at -Y (picture-right)
            st.append((u_frac, 1.0 - h_frac))
            base_uv_grid.append((u_frac, h_frac))

    tris: list[tuple[int, int, int]] = []
    for j in range(NV - 1):
        for i in range(NU - 1):
            a = j * NU + i
            b = (j + 1) * NU + i
            c = (j + 1) * NU + (i + 1)
            d = j * NU + (i + 1)
            # Front (-X) + Back (+X) triangles, matching `make_pickle_views.py`
            tris.append((a, b, c))
            tris.append((a, c, d))
            tris.append((a, c, b))
            tris.append((a, d, c))

    frames: list[tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]] = []

    # --- Frames 0..23: Wacky-Waving Inflatable Diva Dance ---
    for fi in range(24):
        ph = 2.0 * math.pi * (fi / 24.0)
        stretch = 1.0 + 0.075 * math.sin(2.0 * ph)
        width_s = 1.0 / math.sqrt(stretch)

        verts: list[tuple[float, float, float]] = []
        norms: list[tuple[float, float, float]] = []
        for u_frac, h_frac in base_uv_grid:
            y_c = half * (1.0 - 2.0 * u_frac)  # +10 .. -10
            # Base (h_frac=0) stays planted on the floor at (0, y_c, -half)!
            wave_y = (h_frac ** 1.38) * (
                2.55 * math.sin(ph - 1.90 * h_frac)
                + 0.80 * math.sin(2.0 * ph - 3.10 * h_frac)
            )
            wave_x = (h_frac ** 1.50) * 0.95 * math.cos(ph - 1.35 * h_frac)
            # Gentle 3D cylindrical relief along X so the diva feels plump, never paper-flat
            cyl_x = -0.85 * math.cos((u_frac - 0.5) * math.pi) * math.sin(math.pi * (0.08 + 0.84 * h_frac))

            px = cyl_x + wave_x
            py = y_c * width_s + wave_y
            pz = -half + (2.0 * half) * h_frac * stretch

            ny = -0.22 * (u_frac - 0.5) * 2.0
            nx = -math.sqrt(max(0.01, 1.0 - ny * ny))
            verts.append((px, py, pz))
            norms.append((nx, ny, 0.0))
        frames.append((verts, norms))

    # --- Frames 24..35: Pre-Blast Over-Inflation Balloon Swell & Shudder ---
    for si in range(12):
        s = si / 11.0
        swell = 1.0 - (1.0 - s) ** 2.2
        trem_y = 1.25 * swell * math.sin(s * math.pi * 8.0)
        trem_x = 0.65 * swell * math.cos(s * math.pi * 10.0)

        verts = []
        norms = []
        for u_frac, h_frac in base_uv_grid:
            y_c = half * (1.0 - 2.0 * u_frac)
            # Balloon belly & cheek radial expansion (anchored at base h_frac=0!)
            bulge_profile = math.sin(math.pi * (h_frac ** 0.82))
            radial = 1.0 + 0.36 * swell * (0.28 * min(1.0, h_frac * 4.0) + 0.72 * bulge_profile)
            h_grow = 1.0 + 0.11 * swell

            cyl_x = -(0.85 + 1.85 * swell * bulge_profile) * math.cos((u_frac - 0.5) * math.pi)
            px = cyl_x + (h_frac ** 1.1) * trem_x
            py = y_c * radial + (h_frac ** 1.1) * trem_y
            pz = -half + (2.0 * half) * h_frac * h_grow

            ny = -0.35 * (u_frac - 0.5) * 2.0
            nx = -math.sqrt(max(0.01, 1.0 - ny * ny))
            verts.append((px, py, pz))
            norms.append((nx, ny, 0.0))
        frames.append((verts, norms))

    surf = dict(name="card", shader="progs/pickle_s00_v00", tris=tris, st=st, frames=frames)
    return dict(name="pickle", surfaces=[surf], nframes=len(frames))


def build_animated_3d_pickle_hull(srgb_views: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Image.Image, list[dict]]:
    """Reconstructs the watertight 3D `pickle3d` mesh from the repaired sRGB turntable views,
    bakes a vibrant sRGB atlas, and computes 4 smooth multi-frame 3D vertex animation clips!
    Returns `(all_v [F,V,3], all_n [F,V,3], uv_arr [V,2], tri_arr [T,3], atlas_pil, clips_meta)`."""
    N = 16
    GOOD = list(range(N))  # All 16 views are clean now!
    UNIT, C, STEP = 20.0 / 512.0, 256.0, 2.0
    CROP = (140, 14, 372, 498)
    TILE_W, TILE_H = CROP[2] - CROP[0], CROP[3] - CROP[1]
    COLS, sgn = 4, -1

    masks = [ndimage.binary_dilation(v[..., 3] > 118, iterations=2) for v in srgb_views]

    xs = np.arange(-112, 112 + STEP, STEP)
    ys = np.arange(-112, 112 + STEP, STEP)
    zs = np.arange(-250, 250 + STEP, STEP)
    gx, gy, gz = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], 1)
    cnt = np.zeros(len(pts), np.int16)
    for k in GOOD:
        phi = math.radians(sgn * k * 360.0 / N)
        yr = pts[:, 0] * math.sin(phi) + pts[:, 1] * math.cos(phi)
        ui, vi = np.round(C - yr).astype(int), np.round(C - pts[:, 2]).astype(int)
        ok = (ui >= 0) & (ui < 512) & (vi >= 0) & (vi < 512)
        ins = np.zeros(len(pts), bool)
        ins[ok] = masks[k][vi[ok], ui[ok]]
        cnt += ins
    vol = ndimage.binary_closing((cnt >= len(GOOD) - 1).reshape(gx.shape), iterations=1)
    lab, nlab = ndimage.label(vol)
    if nlab > 1:
        sizes = ndimage.sum(vol, lab, range(1, nlab + 1))
        vol = lab == (1 + int(np.argmax(sizes)))
    field = ndimage.gaussian_filter(vol.astype(np.float32), 1.05)
    verts, faces, _, _ = measure.marching_cubes(field, 0.5, spacing=(STEP, STEP, STEP), step_size=3)
    verts = verts + np.array([xs[0], ys[0], zs[0]])

    nv0 = len(verts)
    rows = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2], faces[:, 1], faces[:, 2], faces[:, 0]])
    cols = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0], faces[:, 0], faces[:, 1], faces[:, 2]])
    adj = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(nv0, nv0)).tocsr()
    adj.data[:] = 1.0
    deg = np.maximum(np.asarray(adj.sum(1)).ravel(), 1.0)[:, None]
    for _ in range(5):
        for f_w in (0.5, -0.53):
            verts = verts + f_w * ((adj @ verts) / deg - verts)

    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    fn = np.cross(b - a, c - a)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
    cen = (a + b + c) / 3.0
    flip = ((fn[:, 0] * cen[:, 0] + fn[:, 1] * cen[:, 1]) < 0) & ~(np.abs(cen[:, 2]) > 220)
    fn[flip] *= -1
    faces = faces.copy()
    faces[flip] = faces[flip][:, ::-1]

    cams = {k: np.array([-math.cos(math.radians(sgn * k * 360.0 / N)),
                         math.sin(math.radians(sgn * k * 360.0 / N)), 0.0]) for k in GOOD}
    score = np.stack([fn @ cams[k] for k in GOOD], 1)
    view = np.array(GOOD)[np.argmax(score, 1)]

    # Build bright studio sRGB atlas with clean EDT edge extrapolation (zero dark borders!)
    n_rows = (len(GOOD) + COLS - 1) // COLS
    AW, AH = COLS * TILE_W, n_rows * TILE_H
    atlas = np.zeros((AH, AW, 3), dtype=np.uint8)
    for i, k in enumerate(GOOD):
        tile = srgb_views[k][CROP[1]:CROP[3], CROP[0]:CROP[2]]
        opaque = tile[..., 3] > 180
        idx = ndimage.distance_transform_edt(~opaque, return_distances=False, return_indices=True)
        filled_rgb = tile[..., :3][idx[0], idx[1]]
        r0, c0 = (i // COLS) * TILE_H, (i % COLS) * TILE_W
        atlas[r0:r0 + TILE_H, c0:c0 + TILE_W] = filled_rgb
    atlas_pil = Image.fromarray(atlas, "RGB")

    vn = np.zeros_like(verts)
    for fc, nrm in zip(faces, fn):
        for vi in fc:
            vn[vi] += nrm
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)

    out_v, out_n, out_st, out_t, key = [], [], [], [], {}
    for fc, k in zip(faces, view):
        tri = []
        ti = int(k)
        phi = math.radians(sgn * ti * 360.0 / N)
        for vi in fc:
            kk = (int(vi), ti)
            if kk not in key:
                p = verts[vi]
                yr = p[0] * math.sin(phi) + p[1] * math.cos(phi)
                u_px, v_px = C - yr, C - p[2]
                # Inset 2px inside tile so bilinear filtering never samples neighbor tile!
                tu = (ti % COLS) * TILE_W + np.clip(u_px - CROP[0], 2.0, TILE_W - 3.0)
                tv = (ti // COLS) * TILE_H + np.clip(v_px - CROP[1], 2.0, TILE_H - 3.0)
                key[kk] = len(out_v)
                out_v.append((p[0] * UNIT * 2.8, p[1] * UNIT * 2.8, p[2] * UNIT * 2.8))
                out_n.append(tuple(vn[vi]))
                out_st.append((float(tu / AW), float(tv / AH)))
            tri.append(key[kk])
        out_t.append(tri)

    v0 = np.asarray(out_v, dtype=np.float32)
    n0 = np.asarray(out_n, dtype=np.float32)
    z_min = float(v0[:, 2].min())
    z_max = float(v0[:, 2].max())
    H_tot = max(1e-4, z_max - z_min)
    v0[:, 2] -= z_min  # Anchor base cleanly at z = 0!
    h_nrm = np.clip(v0[:, 2] / H_tot, 0.0, 1.0)

    v_frames: list[np.ndarray] = []
    n_frames: list[np.ndarray] = []

    def rot_z_arr(arr: np.ndarray, ang_rad: np.ndarray) -> np.ndarray:
        c_a, s_a = np.cos(ang_rad), np.sin(ang_rad)
        rx = arr[:, 0] * c_a - arr[:, 1] * s_a
        ry = arr[:, 0] * s_a + arr[:, 1] * c_a
        return np.stack([rx, ry, arr[:, 2]], axis=1)

    # Clip 1 (frames 0..23, 24f): Wacky-Waving Inflatable Diva Dance
    for fi in range(24):
        ph = 2.0 * math.pi * (fi / 24.0)
        stretch = 1.0 + 0.08 * math.sin(2.0 * ph)
        rad_s = 1.0 / math.sqrt(stretch)
        twist = (h_nrm ** 1.2) * 0.24 * math.sin(ph - 1.2 * h_nrm)
        vp = rot_z_arr(v0, twist)
        np_ = rot_z_arr(n0, twist)
        vp[:, 0] = vp[:, 0] * rad_s + (h_nrm ** 1.45) * 3.8 * math.cos(ph - 1.5 * h_nrm)
        vp[:, 1] = vp[:, 1] * rad_s + (h_nrm ** 1.38) * (7.2 * math.sin(ph - 1.85 * h_nrm) + 2.2 * math.sin(2 * ph - 3.0 * h_nrm))
        vp[:, 2] = vp[:, 2] * stretch
        v_frames.append(vp.astype(np.float32))
        n_frames.append(np_.astype(np.float32))

    # Clip 2 (frames 24..39, 16f): Bouncy Totem Pogo-Sprint
    for fi in range(16):
        ph = 2.0 * math.pi * (fi / 16.0)
        air = max(0.0, math.sin(ph))
        jump_z = 14.5 * (air ** 0.85)
        # Squash on ground impact (sin(ph) < 0), stretch on launch!
        squash = 1.0 + 0.18 * math.sin(ph + 0.35)
        rad_s = 1.0 / math.sqrt(max(0.65, squash))
        vp = v0.copy()
        lean_x = -(h_nrm ** 1.25) * (5.2 + 3.2 * math.cos(ph))  # forward lean along -X
        wobble_y = (h_nrm ** 1.3) * 3.0 * math.sin(ph * 0.5)
        vp[:, 0] = vp[:, 0] * rad_s + lean_x
        vp[:, 1] = vp[:, 1] * rad_s + wobble_y
        vp[:, 2] = vp[:, 2] * squash + jump_z
        v_frames.append(vp.astype(np.float32))
        n_frames.append(n0.copy())

    # Clip 3 (frames 40..59, 20f): "PICKLE SURPRISE!" Over-Inflation Swell & Violent Shudder
    for fi in range(20):
        u = fi / 19.0
        swell = math.sin(min(1.0, u * 1.25) * math.pi * 0.5) if u < 0.82 else (1.0 - (u - 0.82) / 0.18) ** 2
        bulge = 1.0 + 0.44 * swell * (0.30 + 0.70 * np.sin(np.pi * (h_nrm ** 0.85)))
        shudder_y = (h_nrm ** 1.1) * 3.6 * swell * math.sin(u * math.pi * 12.0)
        shudder_x = (h_nrm ** 1.1) * 2.4 * swell * math.cos(u * math.pi * 14.0)
        vp = v0.copy()
        vp[:, 0] = vp[:, 0] * bulge + shudder_x
        vp[:, 1] = vp[:, 1] * bulge + shudder_y
        vp[:, 2] = vp[:, 2] * (1.0 + 0.14 * swell)
        v_frames.append(vp.astype(np.float32))
        n_frames.append(n0.copy())

    # Clip 4 (frame 60, 1f): Neutral Studio Turnaround Pose
    v_frames.append(v0.copy())
    n_frames.append(n0.copy())

    clips = [
        dict(id="wave",   label="🥒 Wacky-Waving Inflatable Dance (24f)", start=0,  count=24, fps=18.0),
        dict(id="sprint", label="🏃 Bouncy Totem Pogo-Sprint (16f)",      start=24, count=16, fps=18.0),
        dict(id="swell",  label='😱 "Pickle Surprise!" Swell & Shake (20f)', start=40, count=20, fps=16.0),
        dict(id="pose",   label="🗿 Neutral Studio Pose (1f)",            start=60, count=1,  fps=10.0),
    ]
    return (
        np.stack(v_frames, axis=0),
        np.stack(n_frames, axis=0),
        np.asarray(out_st, dtype=np.float32),
        np.asarray(out_t, dtype=np.int32),
        atlas_pil,
        clips,
    )
