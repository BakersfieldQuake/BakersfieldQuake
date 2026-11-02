"""Extracts, perspective-rectifies, color-matches, and builds 512x512 studio UV face textures
for Green-Suit Wheelman from the 4 real reference photos:
  1. face_smile.png   — Warm cheeky studio smile (from ref_studio_smile.png)
  2. face_scream.png  — Fierce straining battle-cry / roar (from ref_scream.jpg)
  3. face_ooo.png     — Wide-eyed 'OOOOOH!' shock / crane-point / plank expression
"""
from __future__ import annotations

import os
import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(HERE, "ref")
TEX_DIR = os.path.join(HERE, "tex")
os.makedirs(TEX_DIR, exist_ok=True)

SUIT_RGB = np.array([128.0, 230.0, 62.0], dtype=np.float32)


def piecewise_warp_to_canonical(
    src_rgb: np.ndarray,
    src_pts: np.ndarray,
    dst_pts: np.ndarray,
    out_size: int = 512,
) -> np.ndarray:
    h, w = src_rgb.shape[:2]
    corners_src = np.array(
        [[0, 0], [w * 0.5, 0], [w - 1, 0], [0, h * 0.5], [w - 1, h * 0.5], [0, h - 1], [w * 0.5, h - 1], [w - 1, h - 1]],
        dtype=np.float32,
    )
    corners_dst = np.array(
        [
            [0, 0],
            [out_size * 0.5, 0],
            [out_size - 1, 0],
            [0, out_size * 0.5],
            [out_size - 1, out_size * 0.5],
            [0, out_size - 1],
            [out_size * 0.5, out_size - 1],
            [out_size - 1, out_size - 1],
        ],
        dtype=np.float32,
    )
    sp = np.vstack([src_pts, corners_src]).astype(np.float32)
    dp = np.vstack([dst_pts, corners_dst]).astype(np.float32)

    subdiv = cv2.Subdiv2D((0, 0, out_size, out_size))
    for pt in dp:
        subdiv.insert((float(np.clip(pt[0], 0, out_size - 1.001)), float(np.clip(pt[1], 0, out_size - 1.001))))
    tri_list = subdiv.getTriangleList()

    def nearest_idx(x: float, y: float) -> int:
        d2 = (dp[:, 0] - x) ** 2 + (dp[:, 1] - y) ** 2
        return int(np.argmin(d2))

    map_x = np.zeros((out_size, out_size), dtype=np.float32)
    map_y = np.zeros((out_size, out_size), dtype=np.float32)
    yg, xg = np.mgrid[0:out_size, 0:out_size].astype(np.float32)

    for t in tri_list:
        i0 = nearest_idx(t[0], t[1])
        i1 = nearest_idx(t[2], t[3])
        i2 = nearest_idx(t[4], t[5])
        if i0 == i1 or i1 == i2 or i0 == i2:
            continue
        dtri = np.array([dp[i0], dp[i1], dp[i2]], dtype=np.float32)
        stri = np.array([sp[i0], sp[i1], sp[i2]], dtype=np.float32)

        x0 = max(0, int(np.floor(dtri[:, 0].min())))
        x1 = min(out_size - 1, int(np.ceil(dtri[:, 0].max())))
        y0 = max(0, int(np.floor(dtri[:, 1].min())))
        y1 = min(out_size - 1, int(np.ceil(dtri[:, 1].max())))
        if x1 < x0 or y1 < y0:
            continue

        mask = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=np.uint8)
        local_tri = (dtri - np.array([x0, y0], dtype=np.float32)).astype(np.int32)
        cv2.fillConvexPoly(mask, local_tri, 1)
        m_bool = mask > 0
        if not np.any(m_bool):
            continue

        M = cv2.getAffineTransform(dtri, stri)
        lx = xg[y0 : y1 + 1, x0 : x1 + 1][m_bool]
        ly = yg[y0 : y1 + 1, x0 : x1 + 1][m_bool]
        map_x[y0 : y1 + 1, x0 : x1 + 1][m_bool] = M[0, 0] * lx + M[0, 1] * ly + M[0, 2]
        map_y[y0 : y1 + 1, x0 : x1 + 1][m_bool] = M[1, 0] * lx + M[1, 1] * ly + M[1, 2]

    return cv2.remap(src_rgb, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


CANON_PTS = np.array(
    [
        [256, 98],   # 0: Forehead hood apex
        [144, 152],  # 1: Upper-left temple hood edge
        [368, 152],  # 2: Upper-right temple hood edge
        [190, 206],  # 3: Left eye pupil
        [322, 206],  # 4: Right eye pupil
        [256, 204],  # 5: Glabella
        [256, 272],  # 6: Nose tip
        [112, 278],  # 7: Left cheek hood edge
        [400, 278],  # 8: Right cheek hood edge
        [192, 330],  # 9: Left mouth corner
        [320, 330],  # 10: Right mouth corner
        [256, 334],  # 11: Mouth center
        [148, 390],  # 12: Lower-left jaw/beard hood edge
        [364, 390],  # 13: Lower-right jaw/beard hood edge
        [256, 434],  # 14: Chin bottom hood edge
    ],
    dtype=np.float32,
)


def extrude_clean_skin_and_border(face_rgb: np.ndarray) -> np.ndarray:
    """Keeps pure interior skin & beard (zero green hood hem contamination), extrudes cleanly
    past the 3D hood cutout boundary (r_oval=0.84), and transitions outside r_oval=1.04 to suit green."""
    H, W = face_rgb.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    r, g, b = face_rgb[..., 0], face_rgb[..., 1], face_rgb[..., 2]
    green_excess = g - np.maximum(r, b)

    u = (xg - 256.0) / 146.0
    v = (yg - 268.0) / 172.0
    r_oval = np.sqrt(u * u + v * v)

    # Pure interior facial pixels (strictly inside hood seam and free of green fabric)
    pure_skin = ((r_oval < 0.89) & (green_excess < 4.0)).astype(np.uint8)
    pure_skin = cv2.erode(pure_skin, np.ones((5, 5), np.uint8), iterations=1)

    _, labels = cv2.distanceTransformWithLabels(1 - pure_skin, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    coords = np.column_stack(np.where(pure_skin > 0))
    out = face_rgb.copy()
    if len(coords) > 0:
        idx = np.clip(labels - 1, 0, len(coords) - 1)
        extruded = cv2.GaussianBlur(face_rgb[coords[idx, 0], coords[idx, 1]], (0, 0), 3.0)
        keep_w = cv2.GaussianBlur(pure_skin.astype(np.float32), (0, 0), 3.5)[..., None]
        out = face_rgb * keep_w + extruded * (1.0 - keep_w)

    # Note: 3D face mesh UV maps inside r_oval <= 0.86, so extending pure skin/beard out to r_oval=1.10
    # guarantees zero green bleed on cheeks/forehead/beard while outside 1.12 is suit green!
    w_suit = np.clip((r_oval - 1.08) / 0.10, 0.0, 1.0)[..., None]
    out = out * (1.0 - w_suit) + SUIT_RGB[None, None, :] * w_suit
    return np.clip(out, 0, 255)


def match_skin_tone(src: np.ndarray, ref: np.ndarray) -> np.ndarray:
    H, W = src.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    roi = (((xg - 256.0) / 105.0) ** 2 + ((yg - 255.0) / 125.0) ** 2) < 1.0

    s_lab = cv2.cvtColor(np.clip(src, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    r_lab = cv2.cvtColor(np.clip(ref, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    out_lab = s_lab.copy()
    for c, strength in ((0, 0.70), (1, 0.88), (2, 0.88)):
        sm, ss = s_lab[roi, c].mean(), max(s_lab[roi, c].std(), 1e-3)
        rm, rs = r_lab[roi, c].mean(), max(r_lab[roi, c].std(), 1e-3)
        mapped = (s_lab[..., c] - sm) * (rs / ss) + rm
        out_lab[..., c] = s_lab[..., c] * (1.0 - strength) + mapped * strength
    return cv2.cvtColor(np.clip(out_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)


def sharpen_crisp(rgb_f: np.ndarray, amount: float = 0.42) -> np.ndarray:
    blur = cv2.GaussianBlur(rgb_f, (0, 0), 1.5)
    return np.clip(rgb_f + amount * (rgb_f - blur), 0, 255)


def build_all_faces() -> None:
    yg, xg = np.mgrid[0:512, 0:512].astype(np.float32)

    # 1) SMILE (from crop_smile.png, 130x165)
    im_smile = np.asarray(Image.open(os.path.join(REF_DIR, "crop_smile.png")).convert("RGB"), dtype=np.float32)
    smile_pts = np.array(
        [
            [83, 51],   # 0: Forehead hood apex
            [55, 67],   # 1: Upper-left temple
            [108, 69],  # 2: Upper-right temple
            [68, 77],   # 3: Left eye pupil
            [99, 79],   # 4: Right eye pupil
            [84, 77],   # 5: Glabella
            [86, 97],   # 6: Nose tip
            [44, 102],  # 7: Left cheek hood edge
            [110, 102], # 8: Right cheek hood edge
            [63, 111],  # 9: Left mouth corner
            [101, 113], # 10: Right mouth corner
            [84, 115],  # 11: Mouth center
            [51, 128],  # 12: Lower-left jaw
            [104, 128], # 13: Lower-right jaw
            [82, 144],  # 14: Chin bottom
        ],
        dtype=np.float32,
    )
    w_smile = piecewise_warp_to_canonical(im_smile, smile_pts, CANON_PTS, 512)
    # Gentle beard symmetry on outer right cheek where source was slightly 3/4
    sym_w = np.clip((xg - 344.0) / 48.0, 0.0, 0.62)[..., None] * np.clip((yg - 235.0) / 45.0, 0.0, 1.0)[..., None]
    w_smile = w_smile * (1.0 - sym_w) + w_smile[:, ::-1, :] * sym_w
    clean_smile = sharpen_crisp(extrude_clean_skin_and_border(w_smile), 0.45)

    # 2) SCREAM (from crop_scream.png, 125x165)
    im_scream = np.asarray(Image.open(os.path.join(REF_DIR, "crop_scream.png")).convert("RGB"), dtype=np.float32)
    scream_pts = np.array(
        [
            [75, 60],   # 0: Forehead hood apex
            [49, 73],   # 1: Upper-left temple
            [98, 75],   # 2: Upper-right temple
            [56, 84],   # 3: Left eye
            [92, 86],   # 4: Right eye
            [75, 85],   # 5: Glabella
            [75, 104],  # 6: Nose tip
            [35, 102],  # 7: Left cheek hood edge
            [103, 104], # 8: Right cheek hood edge
            [53, 118],  # 9: Left mouth corner
            [86, 120],  # 10: Right mouth corner
            [70, 123],  # 11: Mouth center
            [43, 132],  # 12: Lower-left jaw
            [93, 132],  # 13: Lower-right jaw
            [69, 145],  # 14: Chin bottom
        ],
        dtype=np.float32,
    )
    w_scream = piecewise_warp_to_canonical(im_scream, scream_pts, CANON_PTS, 512)
    w_scream = match_skin_tone(w_scream, clean_smile)
    clean_scream = sharpen_crisp(extrude_clean_skin_and_border(w_scream), 0.52)

    # 3) OOO / SHOCK:
    # Naturally purse the mustache/cheeks inward horizontally around the mouth, raise eyebrows,
    # widen eyes, drop the chin, and blend the rectified real 'O' mouth from crop_point_ooo.png!
    im_ooo = np.asarray(Image.open(os.path.join(REF_DIR, "crop_point_ooo.png")).convert("RGB"), dtype=np.float32)
    ooo_pts = np.array(
        [
            [50, 20], [37, 29], [60, 32],
            [45, 36], [58, 39], [53, 37],
            [55, 48], [30, 48], [61, 50],
            [45, 58], [56, 59], [51, 59],
            [34, 65], [57, 66], [47, 75],
        ],
        dtype=np.float32,
    )
    w_ooo_raw = match_skin_tone(piecewise_warp_to_canonical(im_ooo, ooo_pts, CANON_PTS, 512), clean_smile)
    ooo_sym = 0.55 * w_ooo_raw + 0.45 * w_ooo_raw[:, ::-1, :]

    # Purse mouth horizontally (sample outward from x=256 so wide smile corners pull inward into an 'O'!)
    purse_env = np.exp(-(((xg - 256.0) / 86.0) ** 2 + ((yg - 342.0) / 54.0) ** 2))
    dx_purse = (xg - 256.0) * 0.44 * purse_env
    dy_brow = 13.0 * np.exp(-(((xg - 256.0) / 108.0) ** 2 + ((yg - 168.0) / 42.0) ** 2))
    eye_env = np.exp(-(((xg - 190.0) / 34.0) ** 2 + ((yg - 206.0) / 22.0) ** 2)) + np.exp(
        -(((xg - 322.0) / 34.0) ** 2 + ((yg - 206.0) / 22.0) ** 2)
    )
    dy_eyes = (yg - 206.0) * (-0.28) * eye_env
    dy_jaw = -18.0 * np.exp(-(((xg - 256.0) / 92.0) ** 2 + ((yg - 384.0) / 62.0) ** 2))

    base_ooo = cv2.remap(
        clean_smile,
        np.clip(xg + dx_purse, 0, 511),
        np.clip(yg + dy_brow + dy_eyes + dy_jaw, 0, 511),
        interpolation=cv2.INTER_CUBIC,
    )

    mouth_blend = np.exp(-(((xg - 256.0) / 42.0) ** 2 + ((yg - 345.0) / 40.0) ** 2))[..., None]
    fused_ooo = base_ooo * (1.0 - 0.72 * mouth_blend) + ooo_sym * (0.72 * mouth_blend)

    # Photographic soft acoustic inner mouth shadow & subtle lower-lip sheen (matching Photo 1 & 2)
    o_rad = np.sqrt(((xg - 256.0) / 20.0) ** 2 + ((yg - 346.0) / 25.0) ** 2)
    cavity = np.clip((1.05 - o_rad) / 0.42, 0.0, 1.0)[..., None]
    inner_grad = np.stack(
        [
            34.0 + 18.0 * np.clip((yg - 346.0) / 25.0, -1, 1),
            15.0 + 10.0 * np.clip((yg - 346.0) / 25.0, -1, 1),
            18.0 + 10.0 * np.clip((yg - 346.0) / 25.0, -1, 1),
        ],
        axis=-1,
    ).astype(np.float32)
    lip_rim = np.exp(-((o_rad - 1.16) / 0.28) ** 2)[..., None]
    lip_tone = np.array([152.0, 96.0, 90.0], dtype=np.float32)[None, None, :]
    fused_ooo = fused_ooo * (1.0 - 0.42 * lip_rim) + lip_tone * (0.42 * lip_rim)
    fused_ooo = fused_ooo * (1.0 - 0.88 * cavity) + inner_grad * (0.88 * cavity)
    clean_ooo = sharpen_crisp(extrude_clean_skin_and_border(fused_ooo), 0.42)

    for name, arr in (("face_smile.png", clean_smile), ("face_scream.png", clean_scream), ("face_ooo.png", clean_ooo)):
        Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8), "RGB").save(os.path.join(TEX_DIR, name))

    # 4) Export glTF/WebGL2-ready unified head texture (head_glb_smile.png) matching exact SUIT_LINEAR_COL!
    # SUIT_LINEAR_COL = (0.165, 0.840, 0.024) -> sRGB (gamma 1/2.2) = (112, 236, 47)
    suit_glb_srgb = np.array([112.0, 236.0, 47.0], dtype=np.float32)
    u_sh = (xg - 256.0) / (0.258 * 512.0)
    v_sh = ((1.0 - yg / 512.0) - 0.4765) / 0.305
    r_sh = np.sqrt(u_sh * u_sh + v_sh * v_sh)
    w_skin = np.clip((0.99 - r_sh) / (0.99 - 0.94), 0.0, 1.0)[..., None]
    hem_ring = np.exp(-((r_sh - 0.985) / 0.028) ** 2)[..., None]
    suit_shaded = suit_glb_srgb[None, None, :] * (1.0 - 0.14 * hem_ring)
    head_glb = clean_smile * w_skin + suit_shaded * (1.0 - w_skin)
    head_glb[0:32, 0:32, :] = suit_glb_srgb  # Guaranteed pure suit swatch at UV (0.02, 0.02) for back of head!
    Image.fromarray(np.clip(np.round(head_glb), 0, 255).astype(np.uint8), "RGB").save(
        os.path.join(TEX_DIR, "head_glb_smile.png")
    )

    sheet = np.concatenate([clean_smile, clean_scream, clean_ooo], axis=1)
    Image.fromarray(np.clip(np.round(sheet), 0, 255).astype(np.uint8), "RGB").save(
        os.path.join(TEX_DIR, "diag_faces_3up.jpg"), quality=94
    )
    print("Updated 3 canonical face textures + head_glb_smile.png OK")


if __name__ == "__main__":
    build_all_faces()
