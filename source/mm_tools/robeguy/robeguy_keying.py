"""Zero-fringe white-studio and #00FF00 green-screen chroma keying, normalization,
and premultiplied-alpha compositing utilities for the Pink Flamingo Bathrobe Monster."""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage

CANVAS_W = 480
CANVAS_H = 640
TOP_Y = 48
GROUND_Y = 596

STAGE_W = 520
STAGE_H = 585
STAGE_CX = STAGE_W // 2
STAGE_GY = 532


def resize_rgba_premul(rgba: np.ndarray, tw: int, th: int, alpha_cut: float = 8.0) -> np.ndarray:
    """Resizes straight-RGBA via premultiplied-alpha Lanczos so transparent silhouettes never halo."""
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.clip(np.round(np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)), 0, 255).astype(np.uint8)
    pm_im = Image.fromarray(pm, "RGBA").resize((max(1, int(tw)), max(1, int(th))), Image.Resampling.LANCZOS)
    p = np.asarray(pm_im, dtype=np.float32)
    pa = p[..., 3:4] / 255.0
    rgb = np.where(pa > 1e-3, p[..., :3] / np.maximum(pa, 1e-3), 0.0)
    a_out = np.where(p[..., 3] < alpha_cut, 0.0, p[..., 3])
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(a_out), 0, 255).astype(np.uint8),
    ])


def key_white_studio_robe(im_or_path: Image.Image | Path | str) -> np.ndarray:
    """Keys full-res DSLR white-studio Robe Guy photos (robe_front.jpg / robe_back.jpg)
    while preserving 100% of white hibiscus flowers & polka dots inside the pink robe."""
    im = Image.open(im_or_path).convert("RGB") if not isinstance(im_or_path, Image.Image) else im_or_path.convert("RGB")
    rgb = np.asarray(im, dtype=np.float32)
    h, w, _ = rgb.shape

    hi = rgb.max(axis=-1)
    lo = rgb.min(axis=-1)
    ch = hi - lo
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]

    yy, _ = np.mgrid[0:h, 0:w]
    cand_bg = ((lum > 236.0) & (ch < 17.0)) | ((yy > int(0.895 * h)) & (lum > 196.0) & (ch < 15.0))

    lbl, _ = ndimage.label(cand_bg)
    border_ids = (
        set(np.unique(lbl[0, :]))
        | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0]))
        | set(np.unique(lbl[:, -1]))
    )
    border_ids.discard(0)
    bg = np.isin(lbl, list(border_ids))

    # Open enclosed arm-to-robe white studio gaps (>= 1200 px), keeping robe flowers (<= 350 px) solid
    holes = (~bg) & (lum > 238.0) & (ch < 14.0)
    hl, hn = ndimage.label(holes)
    if hn > 0:
        hs = ndimage.sum(holes, hl, range(1, hn + 1))
        gap_ids = [i + 1 for i, sz in enumerate(hs) if sz >= 1100]
        if gap_ids:
            bg = bg | np.isin(hl, gap_ids)

    fg_raw = ndimage.binary_opening(~bg, structure=np.ones((3, 3)))
    fl, fn = ndimage.label(fg_raw)
    if fn > 1:
        fsz = ndimage.sum(fg_raw, fl, range(1, fn + 1))
        fg_raw = fl == (1 + int(np.argmax(fsz)))

    dist_in = ndimage.distance_transform_edt(fg_raw)
    dist_out = ndimage.distance_transform_edt(~fg_raw)
    sdf = dist_in - dist_out

    # Crisp slightly-inset AA edge so mixed white border pixels vanish
    alpha = np.clip((sdf - 0.75 + 0.75) / 1.50, 0.0, 1.0)
    whiteness = np.clip((lum - 210.0) / 42.0, 0.0, 1.0) * np.clip((24.0 - ch) / 20.0, 0.0, 1.0)
    alpha = np.where(dist_in < 3.6, alpha * (1.0 - 0.88 * whiteness), alpha)

    # Decontaminate outer 4.5px rim by propagating clean interior foreground colors outward
    white_rim = (dist_in <= 5.0) & (lum > 205.0) & (ch < 22.0)
    clean_core = (dist_in > 3.5) & (~white_rim) & fg_raw
    rgb_clean = rgb.copy()
    if np.any(clean_core):
        _, (iy, ix) = ndimage.distance_transform_edt(~clean_core, return_indices=True)
        nearest = rgb[iy, ix]
        rim_w = np.clip((dist_in - 1.5) / 3.0, 0.0, 1.0)
        rim_w = np.where(white_rim, 0.0, rim_w)[..., None]
        rgb_clean = rgb * rim_w + nearest * (1.0 - rim_w)

    alpha = np.clip((alpha - 0.05) / 0.95, 0.0, 1.0)
    return np.dstack([
        np.clip(np.round(rgb_clean), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])


def key_green_studio_robe(
    im_or_path: Image.Image | Path | str,
    keep_multi: bool = False,
    min_comp_area: int = 350,
) -> np.ndarray:
    """Zero-fringe #00FF00 chroma-green studio keyer tailored for Pink Flamingo Bathrobe Guy & props.
    Protects apple-green flower leaf motifs inside the pink robe while eliminating all green spill."""
    im = Image.open(im_or_path).convert("RGB") if not isinstance(im_or_path, Image.Image) else im_or_path.convert("RGB")
    arr = np.asarray(im, dtype=np.float32)
    h, w, _ = arr.shape
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()

    mx_rb = np.maximum(r, b)
    g_ex = g - mx_rb

    # Pure chroma green background: high G excess over max(R, B)
    cand_bg = (g_ex > 64.0) & (g > 105.0)
    lbl, _ = ndimage.label(cand_bg)
    border_ids = (
        set(np.unique(lbl[0, :]))
        | set(np.unique(lbl[-1, :]))
        | set(np.unique(lbl[:, 0]))
        | set(np.unique(lbl[:, -1]))
    )
    border_ids.discard(0)
    bg = np.isin(lbl, list(border_ids))

    # Open enclosed true #00FF00 studio pockets (e.g. between arm & robe or mug handle),
    # strictly requiring strong neon green excess (g_ex > 88) so soft lime robe clovers (g_ex < 55) never open!
    enc_green = (~bg) & (g_ex > 88.0) & (g > 135.0) & (r < 115.0)
    el, en = ndimage.label(enc_green)
    if en > 0:
        esz = ndimage.sum(enc_green, el, range(1, en + 1))
        open_ids = [i + 1 for i, sz in enumerate(esz) if sz >= 18]
        if open_ids:
            bg = bg | np.isin(el, open_ids)

    dist = ndimage.distance_transform_edt(~bg)
    alpha = np.ones_like(g_ex, dtype=np.float32)
    alpha[bg] = 0.0

    edge = (~bg) & (dist <= 8.0)
    a_ramp = np.clip(1.0 - (g_ex - 12.0) / 56.0, 0.0, 1.0)
    use_r = edge & (g_ex > 12.0)
    alpha[use_r] = np.where(a_ramp[use_r] <= 0.06, 0.0, a_ramp[use_r])

    # Un-premultiply semi-transparent edge pixels against #00FF00
    semi = (alpha > 0.0) & (alpha < 0.995)
    if np.any(semi):
        inv = 1.0 - alpha[semi]
        denom = np.maximum(alpha[semi], 0.25)
        # Estimate studio green level locally (~245)
        r[semi] = np.clip(r[semi] / denom, 0.0, 255.0)
        g[semi] = np.clip((g[semi] - inv * 245.0) / denom, 0.0, 255.0)
        b[semi] = np.clip(b[semi] / denom, 0.0, 255.0)

    rgb = np.dstack([r, g, b])
    core = ndimage.minimum_filter((alpha > 0.98) & (g_ex < 14.0), size=3)
    if np.any(core):
        _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
        rim = (alpha > 0.0) & (~core) & (dist <= 6.0)
        rgb[rim] = rgb[iy[rim], ix[rim]]

    # Gentle green bounce despill strictly near outer boundary (dist <= 18) so interior lime clovers stay intact
    r2, g2, b2 = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    g_ex2 = g2 - np.maximum(r2, b2)
    spill = (alpha > 0.0) & (dist <= 18.0) & (g_ex2 > 6.0)
    if np.any(spill):
        excess = g_ex2[spill] - 4.0
        g2[spill] = np.clip(g2[spill] - 0.88 * excess, 0.0, 255.0)
        r2[spill] = np.clip(r2[spill] + 0.16 * excess, 0.0, 255.0)
        b2[spill] = np.clip(b2[spill] + 0.14 * excess, 0.0, 255.0)

    alpha = np.clip((alpha - 0.06) / 0.94, 0.0, 1.0)
    out = np.dstack([
        np.clip(np.round(r2), 0, 255).astype(np.uint8),
        np.clip(np.round(g2), 0, 255).astype(np.uint8),
        np.clip(np.round(b2), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])

    mask = out[..., 3] > 24
    fl, fn = ndimage.label(mask)
    if fn > 0:
        fsz = ndimage.sum(mask, fl, range(1, fn + 1))
        if keep_multi:
            keep_ids = [i + 1 for i, sz in enumerate(fsz) if sz >= min_comp_area]
            if not keep_ids:
                keep_ids = [1 + int(np.argmax(fsz))]
            keep = ndimage.binary_dilation(np.isin(fl, keep_ids), iterations=2)
        else:
            keep = ndimage.binary_dilation(fl == (1 + int(np.argmax(fsz))), iterations=2)
        out[~keep] = 0
    return out


def crop_normalize_robe(
    rgba: np.ndarray,
    box: tuple[int, int, int, int] | None = None,
    mirror: bool = False,
    cw: int = CANVAS_W,
    ch: int = CANVAS_H,
    top_y: int = TOP_Y,
    ground_y: int = GROUND_Y,
) -> np.ndarray:
    """Normalizes a full-body character cutout onto (cw, ch) with head at top_y and bare feet at ground_y."""
    sub = rgba[box[1]:box[3], box[0]:box[2]].copy() if box is not None else rgba.copy()
    if mirror:
        sub = sub[:, ::-1, :].copy()

    mask = sub[..., 3] > 28
    lbl, num = ndimage.label(mask)
    if num > 1:
        sizes = ndimage.sum(mask, lbl, range(1, num + 1))
        keep = ndimage.binary_dilation(lbl == (1 + int(np.argmax(sizes))), iterations=2)
        sub[~keep] = 0
        mask = sub[..., 3] > 28

    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return np.zeros((ch, cw, 4), dtype=np.uint8)

    sub = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h0, w0 = sub.shape[:2]
    tgt_h = ground_y - top_y
    sc = tgt_h / float(h0)
    nw = max(2, int(round(w0 * sc)))
    resized = resize_rgba_premul(sub, nw, tgt_h)

    a_np = resized[..., 3].astype(np.float32)
    torso_a = a_np[int(tgt_h * 0.16):int(tgt_h * 0.58), :]
    cx_local = float((torso_a.sum(axis=0) * np.arange(nw)).sum() / max(1.0, torso_a.sum()))

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ox = int(round(cw * 0.5 - cx_local))
    canvas.alpha_composite(Image.fromarray(resized, "RGBA"), (ox, top_y))
    return np.asarray(canvas, dtype=np.uint8)


def match_robe_color_grade(src_rgba: np.ndarray, ref_rgba: np.ndarray) -> np.ndarray:
    """Matches brightness/warmth of AI turnaround views to the DSLR studio front/back plates."""
    out = src_rgba.copy()
    m_s = out[..., 3] > 200
    m_r = ref_rgba[..., 3] > 200
    if np.sum(m_s) < 200 or np.sum(m_r) < 200:
        return out
    sf = out[..., :3].astype(np.float32)
    rf = ref_rgba[..., :3].astype(np.float32)
    for c in range(3):
        s_mu, s_sd = float(sf[m_s, c].mean()), float(sf[m_s, c].std() + 1e-4)
        r_mu, r_sd = float(rf[m_r, c].mean()), float(rf[m_r, c].std() + 1e-4)
        gain = np.clip(r_sd / s_sd, 0.82, 1.18)
        sf[..., c] = np.clip((sf[..., c] - s_mu) * (0.65 * gain + 0.35) + (0.72 * r_mu + 0.28 * s_mu), 0.0, 255.0)
    out[..., :3] = np.round(sf).astype(np.uint8)
    return out


def split_columns_auto(rgba: np.ndarray, n_cols: int = 3) -> list[np.ndarray]:
    """Splits a horizontal multi-figure plate cleanly along empty vertical valleys."""
    h, w = rgba.shape[:2]
    col_mass = (rgba[..., 3] > 24).sum(axis=0)
    cuts = [0]
    for i in range(1, n_cols):
        approx = int(round(w * i / n_cols))
        lo = max(1, approx - int(w * 0.10))
        hi = min(w - 1, approx + int(w * 0.10))
        valley = lo + int(np.argmin(col_mass[lo:hi]))
        cuts.append(valley)
    cuts.append(w)
    return [rgba[:, cuts[i]:cuts[i + 1]].copy() for i in range(n_cols)]


def split_quadrants_2x2(rgba: np.ndarray) -> dict[str, np.ndarray]:
    """Splits a 2x2 studio sheet along the cleanest central horizontal & vertical empty gutters."""
    h, w = rgba.shape[:2]
    col_mass = (rgba[..., 3] > 24).sum(axis=0)
    row_mass = (rgba[..., 3] > 24).sum(axis=1)
    vx = int(w * 0.38) + int(np.argmin(col_mass[int(w * 0.38):int(w * 0.62)]))
    vy = int(h * 0.38) + int(np.argmin(row_mass[int(h * 0.38):int(h * 0.62)]))
    return {
        "tl": rgba[:vy, :vx].copy(),
        "tr": rgba[:vy, vx:].copy(),
        "bl": rgba[vy:, :vx].copy(),
        "br": rgba[vy:, vx:].copy(),
    }


def crop_tight_rgba(rgba: np.ndarray, pad: int = 4) -> np.ndarray:
    ys, xs = np.nonzero(rgba[..., 3] > 20)
    if len(ys) == 0:
        return np.zeros((16, 16, 4), dtype=np.uint8)
    h, w = rgba.shape[:2]
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(w, int(xs.max()) + 1 + pad)
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(h, int(ys.max()) + 1 + pad)
    return rgba[y0:y1, x0:x1].copy()
