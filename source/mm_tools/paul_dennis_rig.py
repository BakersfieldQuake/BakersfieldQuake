"""2D Skeletal Limb Mesh Warping, Studio Chroma-Keying, and Real Video Expression
Compositing for Paul ('Screaming Paul') and Dennis ('Reading Dennis') in BakersfieldQuake."""

import math
import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

CANVAS_W = 480
CANVAS_H = 640
TOP_Y = 44
GROUND_Y = 596

# Richard Williams 8-frame run cycle keyframes (facing LEFT = -X):
# (theta_hip_deg, theta_knee_deg, theta_foot_deg, sy_thigh, body_bob_dy)
RUN_8_PROFILE = [
    (+29.0,  -6.0, +12.0, 1.00, +3.0),   # f=0: Contact / Heel strike
    (+14.0, -21.0,   0.0, 0.99, +7.0),   # f=1: Down / Cushion
    ( -7.0, -13.0,  -9.0, 1.00, +1.0),   # f=2: Mid-stance / Push
    (-27.0, -18.0, -20.0, 1.01, -5.0),   # f=3: Toe-off / Drive back
    (-21.0, -58.0, -16.0, 0.98, -7.0),   # f=4: Airborne / Back kick-up
    ( +6.0, -64.0,  -8.0, 0.96, -2.0),   # f=5: Recovery / Folded pass
    (+32.0, -42.0,  +4.0, 0.95, -5.0),   # f=6: High knee drive
    (+33.0, -16.0, +13.0, 0.98, -1.0),   # f=7: Reach before strike
]


def sample_run_profile(phase_01: float) -> tuple[float, float, float, float, float]:
    """Smoothly interpolates RUN_8_PROFILE at any continuous normalized gait phase in [0, 1)."""
    u = (phase_01 % 1.0) * 8.0
    i0 = int(math.floor(u)) % 8
    i1 = (i0 + 1) % 8
    t = u - math.floor(u)
    # Cosine-eased interpolation preserves crisp extremes while smoothing inter-frame velocity
    w = 0.5 - 0.5 * math.cos(math.pi * t)
    a, b = RUN_8_PROFILE[i0], RUN_8_PROFILE[i1]
    return tuple(a[k] * (1.0 - w) + b[k] * w for k in range(5))


# ---------------------------------------------------------------------------
# 1. Zero-Fringe Studio #FF00FF Chroma Keying & Multi-Scale Fabric Inpainting
# ---------------------------------------------------------------------------

def seg_dist_grid(xg: np.ndarray, yg: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    vx, vy = x1 - x0, y1 - y0
    l2 = max(vx * vx + vy * vy, 1e-6)
    t = np.clip(((xg - x0) * vx + (yg - y0) * vy) / l2, 0.0, 1.0)
    return np.hypot(xg - (x0 + t * vx), yg - (y0 + t * vy))


def key_magenta_studio(im_rgb: Image.Image) -> np.ndarray:
    """Zero-fringe #FF00FF chroma key: smooth AA alpha + nearest-interior-solid RGB propagation
    on boundary pixels so neither magenta nor green fringe ever appears on grey hair or cuffs."""
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()
    m = np.minimum(r, b) - g

    bg = (m > 62.0) & (r > 95.0) & (b > 95.0)
    dist = ndimage.distance_transform_edt(~bg)

    alpha = np.ones_like(m, dtype=np.float32)
    alpha[bg] = 0.0
    edge = (~bg) & (dist <= 9.0)
    a_ramp = np.clip(1.0 - (m - 10.0) / 54.0, 0.0, 1.0)
    use_r = edge & (m > 10.0)
    alpha[use_r] = np.where(a_ramp[use_r] <= 0.05, 0.0, a_ramp[use_r])

    # Un-premultiply interior-facing semi-transparent pixels first
    semi = (alpha > 0.0) & (alpha < 0.995)
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.25)
    r[semi] = np.clip((r[semi] - inv * 255.0) / denom, 0.0, 255.0)
    g[semi] = np.clip(g[semi] / denom, 0.0, 255.0)
    b[semi] = np.clip((b[semi] - inv * 255.0) / denom, 0.0, 255.0)

    # Propagate clean interior solid RGB outward across outer 4px rim to eliminate BOTH pink & green halos
    rgb = np.dstack([r, g, b])
    core = ndimage.minimum_filter((alpha > 0.98) & (m < 8.0), size=3)
    if np.any(core):
        _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
        rim = (alpha > 0.0) & (~core) & (dist <= 7.0)
        rgb[rim] = rgb[iy[rim], ix[rim]]

    # Gentle neutral despill on any remaining #FF00FF bounce light on white shirt cuffs / silver hair
    # (replaces R and B excess symmetrically toward luminance, never boosting green!)
    r2, g2, b2 = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m2 = np.minimum(r2, b2) - g2
    cool_bounce = (alpha > 0.0) & (dist <= 22.0) & (m2 > 5.0) & ((r2 - b2) < 26.0)
    if np.any(cool_bounce):
        excess = m2[cool_bounce] - 3.0
        r2[cool_bounce] = np.clip(r2[cool_bounce] - 0.72 * excess, 0.0, 255.0)
        b2[cool_bounce] = np.clip(b2[cool_bounce] - 0.78 * excess, 0.0, 255.0)
        g2[cool_bounce] = np.clip(g2[cool_bounce] + 0.18 * excess, 0.0, 255.0)

    # Slightly tighten outer 0.5px AA skirt for ultra-crisp cutouts
    alpha = np.clip((alpha - 0.06) / 0.94, 0.0, 1.0)

    return np.dstack([
        np.clip(np.round(r2), 0, 255).astype(np.uint8),
        np.clip(np.round(g2), 0, 255).astype(np.uint8),
        np.clip(np.round(b2), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])


def crop_normalize_view(
    rgba: np.ndarray,
    box: tuple[int, int, int, int],
    mirror: bool = False,
    cw: int = CANVAS_W,
    ch: int = CANVAS_H,
    top_y: int = TOP_Y,
    ground_y: int = GROUND_Y,
) -> np.ndarray:
    x0, y0, x1, y1 = box
    sub = rgba[y0:y1, x0:x1].copy()
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
    sub = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h0, w0 = sub.shape[:2]
    tgt_h = ground_y - top_y
    sc = tgt_h / float(h0)
    nw = max(1, int(round(w0 * sc)))
    im = Image.fromarray(sub, "RGBA").resize((nw, tgt_h), Image.Resampling.LANCZOS)

    a_np = np.asarray(im)[..., 3].astype(np.float32)
    torso_a = a_np[int(tgt_h * 0.18):int(tgt_h * 0.56), :]
    cx_local = float((torso_a.sum(axis=0) * np.arange(nw)).sum() / max(1.0, torso_a.sum()))
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ox = int(round(cw / 2.0 - cx_local))
    canvas.alpha_composite(im, (ox, top_y))
    return np.asarray(canvas, dtype=np.uint8)


def inpaint_fabric_region(rgba: np.ndarray, hole_mask: np.ndarray) -> np.ndarray:
    """Fills an excised hand/cuff region inside opaque suit/trouser fabric using multi-scale Gaussian pull-push."""
    out = rgba.astype(np.float32).copy()
    rgb = out[..., :3]
    a = out[..., 3] / 255.0
    hole = ndimage.binary_dilation(hole_mask, iterations=3) & (a > 0.25)
    if not np.any(hole):
        return rgba

    rg = np.abs(rgb[..., 0] - rgb[..., 1]) + np.abs(rgb[..., 1] - rgb[..., 2])
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    known = (~hole) & (a > 0.88) & (lum < 110.0) & (rg < 42.0)
    if np.sum(known) < 50:
        known = (~hole) & (a > 0.85)

    seed_rgb = np.where(known[..., None], rgb, 0.0)
    seed_w = known.astype(np.float32)
    filled = np.zeros_like(rgb)
    conf = np.zeros_like(seed_w)
    for sigma in (48.0, 24.0, 12.0, 5.0):
        ks = int(sigma * 4) | 1
        ns = cv2.GaussianBlur(seed_rgb, (ks, ks), sigma)
        ds = cv2.GaussianBlur(seed_w, (ks, ks), sigma)
        layer = np.where((ds > 1e-5)[..., None], ns / np.maximum(ds[..., None], 1e-5), 0.0)
        wt = np.clip(ds * 12.0, 0.0, 1.0)
        filled = np.where(conf[..., None] == 0, layer, filled * (1.0 - wt[..., None]) + layer * wt[..., None])
        conf = np.maximum(conf, wt)

    bw = cv2.GaussianBlur(hole.astype(np.float32), (9, 9), 2.2) * (a > 0.10)
    out[..., :3] = np.clip(rgb * (1.0 - bw[..., None]) + filled * bw[..., None], 0.0, 255.0)
    return out.astype(np.uint8)


def extend_top_upward(rgba: np.ndarray, y_top: int, up_px: int = 26) -> np.ndarray:
    out = rgba.copy()
    H, W = out.shape[:2]
    for x in range(W):
        col = out[y_top:min(H, y_top + 60), x, 3]
        nz = np.nonzero(col > 180)[0]
        if len(nz):
            ty = y_top + int(nz[0])
            sample = out[min(H - 1, ty + 3), x].copy()
            for yy in range(max(0, ty - up_px), ty):
                if out[yy, x, 3] == 0:
                    out[yy, x] = sample
    return out


def shade_rgba(rgba: np.ndarray, factor: float) -> np.ndarray:
    if abs(factor - 1.0) < 1e-3:
        return rgba.copy()
    out = rgba.copy()
    out[..., :3] = np.clip(np.round(out[..., :3].astype(np.float32) * factor), 0, 255).astype(np.uint8)
    return out


def alpha_over(dst: np.ndarray, src: np.ndarray) -> np.ndarray:
    sa = src[..., 3:4].astype(np.float32) / 255.0
    da = dst[..., 3:4].astype(np.float32) / 255.0
    oa = sa + da * (1.0 - sa)
    s_rgb = src[..., :3].astype(np.float32)
    d_rgb = dst[..., :3].astype(np.float32)
    o_rgb = np.where(oa > 1e-5, (s_rgb * sa + d_rgb * da * (1.0 - sa)) / np.maximum(oa, 1e-5), 0.0)
    return np.dstack([
        np.clip(np.round(o_rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(oa[..., 0] * 255.0), 0, 255).astype(np.uint8),
    ])


def mirror_canvas_horiz(rgba: np.ndarray) -> np.ndarray:
    return rgba[:, ::-1, :].copy()


# ---------------------------------------------------------------------------
# 2. Fast C1 Smooth 3-Bone Limb Mesh Warper
# ---------------------------------------------------------------------------

def _smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / max(1e-5, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _rot2d(deg: float) -> np.ndarray:
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    return np.array([[c, -s], [s, c]], dtype=np.float32)


def warp_rigid_rgba(
    rgba: np.ndarray,
    pivot: tuple[float, float],
    angle_deg: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
    dx: float = 0.0,
    dy: float = 0.0,
) -> np.ndarray:
    H, W = rgba.shape[:2]
    px, py = pivot
    rad = math.radians(angle_deg)
    ca, sa = math.cos(rad), math.sin(rad)
    M = np.array([
        [ca * sx, -sa * sy, px + dx - ca * sx * px + sa * sy * py],
        [sa * sx,  ca * sy, py + dy - sa * sx * px - ca * sy * py],
    ], dtype=np.float32)
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)
    pm_w = cv2.warpAffine(pm, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT)
    wa = pm_w[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, pm_w[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([np.clip(np.round(rgb), 0, 255).astype(np.uint8), np.clip(np.round(pm_w[..., 3]), 0, 255).astype(np.uint8)])


def warp_limb_3bone(
    rgba: np.ndarray,
    j_root: tuple[float, float],
    j_mid: tuple[float, float],
    j_end: tuple[float, float],
    ang_upper: float = 0.0,
    ang_lower: float = 0.0,
    ang_tip: float = 0.0,
    sy_upper: float = 1.0,
    sy_lower: float = 1.0,
    scale_all: float = 1.0,
    dx: float = 0.0,
    dy: float = 0.0,
    band_mid: float = 20.0,
    band_end: float = 12.0,
) -> np.ndarray:
    if not np.any(rgba[..., 3] > 4):
        return rgba.copy()

    H, W = rgba.shape[:2]
    rx, ry = j_root
    mx, my = j_mid
    ex, ey = j_end

    R1 = _rot2d(ang_upper) * scale_all
    R2 = _rot2d(ang_upper + ang_lower) * scale_all
    R3 = _rot2d(ang_upper + ang_lower + ang_tip) * scale_all

    root_p = np.array([rx + dx, ry + dy], dtype=np.float32)
    mid_p = root_p + R1 @ np.array([mx - rx, (my - ry) * sy_upper], dtype=np.float32)
    end_p = mid_p + R2 @ np.array([ex - mx, (ey - my) * sy_lower], dtype=np.float32)

    ys_nz, xs_nz = np.nonzero(rgba[..., 3] > 2)
    x0 = max(0, int(xs_nz.min()) - 14)
    x1 = min(W - 1, int(xs_nz.max()) + 14)
    y0 = max(0, int(ys_nz.min()) - 14)
    y1 = min(H - 1, int(ys_nz.max()) + 14)

    nx, ny = 10, 22
    gx = np.linspace(x0, x1, nx, dtype=np.float32)
    gy = np.linspace(y0, y1, ny, dtype=np.float32)
    GX, GY = np.meshgrid(gx, gy)
    pts = np.stack([GX, GY], axis=-1)

    d_root = np.stack([pts[..., 0] - rx, (pts[..., 1] - ry) * sy_upper], axis=-1)
    p1 = root_p + np.einsum("ij,...j->...i", R1, d_root)
    d_mid = np.stack([pts[..., 0] - mx, (pts[..., 1] - my) * sy_lower], axis=-1)
    p2 = mid_p + np.einsum("ij,...j->...i", R2, d_mid)
    d_end = np.stack([pts[..., 0] - ex, pts[..., 1] - ey], axis=-1)
    p3 = end_p + np.einsum("ij,...j->...i", R3, d_end)

    w12 = _smoothstep(my - band_mid, my + band_mid, pts[..., 1])[..., None]
    w23 = _smoothstep(ey - band_end, ey + band_end, pts[..., 1])[..., None]
    dst_pts = p1 * (1.0 - w12) + p2 * w12
    dst_pts = dst_pts * (1.0 - w23) + p3 * w23

    map_x = np.full((H, W), -1.0, dtype=np.float32)
    map_y = np.full((H, W), -1.0, dtype=np.float32)

    for iy in range(ny - 1):
        for ix in range(nx - 1):
            s_quad = np.array([
                [GX[iy, ix], GY[iy, ix]],
                [GX[iy, ix + 1], GY[iy, ix + 1]],
                [GX[iy + 1, ix + 1], GY[iy + 1, ix + 1]],
                [GX[iy + 1, ix], GY[iy + 1, ix]],
            ], dtype=np.float32)
            sx0 = max(0, int(s_quad[:, 0].min()) - 1)
            sx1 = min(W, int(s_quad[:, 0].max()) + 2)
            sy0 = max(0, int(s_quad[:, 1].min()) - 1)
            sy1 = min(H, int(s_quad[:, 1].max()) + 2)
            if not np.any(rgba[sy0:sy1, sx0:sx1, 3] > 1):
                continue

            d_quad = np.array([
                dst_pts[iy, ix],
                dst_pts[iy, ix + 1],
                dst_pts[iy + 1, ix + 1],
                dst_pts[iy + 1, ix],
            ], dtype=np.float32)

            for tri_idx in ((0, 1, 2), (0, 2, 3)):
                st = s_quad[list(tri_idx)]
                dt = d_quad[list(tri_idx)]
                bx0 = max(0, int(math.floor(dt[:, 0].min())))
                bx1 = min(W - 1, int(math.ceil(dt[:, 0].max())))
                by0 = max(0, int(math.floor(dt[:, 1].min())))
                by1 = min(H - 1, int(math.ceil(dt[:, 1].max())))
                if bx1 < bx0 or by1 < by0:
                    continue
                den = (dt[2, 0] - dt[0, 0]) * (dt[1, 1] - dt[0, 1]) - (dt[1, 0] - dt[0, 0]) * (dt[2, 1] - dt[0, 1])
                if abs(den) < 1e-2:
                    continue
                M_inv = cv2.getAffineTransform(dt, st)
                px_g, py_g = np.meshgrid(
                    np.arange(bx0, bx1 + 1, dtype=np.float32),
                    np.arange(by0, by1 + 1, dtype=np.float32),
                )
                v0 = dt[2] - dt[0]
                v1 = dt[1] - dt[0]
                v2x = px_g - dt[0, 0]
                v2y = py_g - dt[0, 1]
                inv_d = 1.0 / den
                u = (v2x * v1[1] - v1[0] * v2y) * inv_d
                v = (v0[0] * v2y - v2x * v0[1]) * inv_d
                inside = (u >= -1e-4) & (v >= -1e-4) & (u + v <= 1.0 + 2e-4)
                if not np.any(inside):
                    continue
                map_x[by0:by1 + 1, bx0:bx1 + 1][inside] = (M_inv[0, 0] * px_g + M_inv[0, 1] * py_g + M_inv[0, 2])[inside]
                map_y[by0:by1 + 1, bx0:bx1 + 1][inside] = (M_inv[1, 0] * px_g + M_inv[1, 1] * py_g + M_inv[1, 2])[inside]

    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm_src = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)
    pm_dst = cv2.remap(pm_src, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wa = pm_dst[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, pm_dst[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(pm_dst[..., 3]), 0, 255).astype(np.uint8),
    ])


# ---------------------------------------------------------------------------
# 3. View-Specific Anatomical Layer Split & 8-Frame Run Cycle Pose Synthesis
# ---------------------------------------------------------------------------

def _extract_tapered_sleeve(
    base_rgba: np.ndarray,
    sh: tuple[float, float],
    el: tuple[float, float],
    wr: tuple[float, float],
    r_sh: float = 18.0,
    r_wr: float = 15.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Extracts a sleek tapered anatomical sleeve+hand layer with feathered inner boundary,
    returning (arm_rgba, hand_inpaint_mask)."""
    H, W = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    d_upper = seg_dist_grid(xg, yg, sh[0], sh[1], el[0], el[1])
    d_lower = seg_dist_grid(xg, yg, el[0], el[1], wr[0], wr[1])
    d_hand = np.hypot((xg - wr[0]) / 1.0, (yg - (wr[1] + 10.0)) / 1.35)

    t_y = np.clip((yg - sh[1]) / max(1.0, wr[1] - sh[1]), 0.0, 1.0)
    rad = r_sh * (1.0 - t_y) + r_wr * t_y
    d_min = np.minimum(np.minimum(d_upper, d_lower), d_hand * 0.95)

    w_arm = np.clip((rad + 2.0 - d_min) / 3.0, 0.0, 1.0) * (yg >= sh[1] - 10.0) * (yg <= wr[1] + 32.0)
    arm_rgba = base_rgba.copy()
    arm_rgba[..., 3] = np.clip(np.round(arm_rgba[..., 3].astype(np.float32) * w_arm), 0, 255).astype(np.uint8)

    # Hand + shirt cuff region to inpaint on underlying suit/trousers
    hand_hole = (d_min <= rad + 3.0) & (yg >= el[1] + 24.0) & (yg <= wr[1] + 34.0)
    return arm_rgba, hand_hole


def render_front_or_back_run_frame(
    base_rgba: np.ndarray,
    frame_idx: int,
    n_frames: int = 8,
    is_back: bool = False,
) -> np.ndarray:
    H, W = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]

    t_hip = np.clip((yg.astype(np.float32) - 245.0) / 85.0, 0.0, 1.0)
    x_cut_l = 189.0 - 13.0 * t_hip  # passes through x=176 air gap between hand & hip
    x_cut_r = 291.0 + 10.0 * t_hip  # passes through x=301 air gap between hand & hip
    arm_l_mask = (xg < x_cut_l) & (yg >= 164) & (yg <= 388) & (base_rgba[..., 3] > 0)
    arm_r_mask = (xg > x_cut_r) & (yg >= 164) & (yg <= 388) & (base_rgba[..., 3] > 0)

    # Give torso an 8px chest/shoulder overlap behind the upper arms (y=164..285) so outward arm swing never shows a gap!
    overlap = 8.5 * (1.0 - np.clip((yg.astype(np.float32) - 235.0) / 55.0, 0.0, 1.0))
    torso_l_bound = x_cut_l - overlap
    torso_r_bound = x_cut_r + overlap

    leg_zone = (yg >= 344) & (~arm_l_mask) & (~arm_r_mask)
    leg_l_mask = leg_zone & (xg < 240) & (base_rgba[..., 3] > 0)
    leg_r_mask = leg_zone & (xg >= 240) & (base_rgba[..., 3] > 0)
    torso_mask = (base_rgba[..., 3] > 0) & (yg < 350) & (
        (yg < 164) | ((xg >= torso_l_bound) & (xg <= torso_r_bound))
    )

    arm_l = extend_top_upward(np.where(arm_l_mask[..., None], base_rgba, 0), 164, up_px=12)
    arm_r = extend_top_upward(np.where(arm_r_mask[..., None], base_rgba, 0), 164, up_px=12)
    torso = np.zeros_like(base_rgba); torso[torso_mask] = base_rgba[torso_mask]
    for yy in range(345, 350):
        torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((350 - yy) / 5.0)).astype(np.uint8)

    leg_l = extend_top_upward(np.where(leg_l_mask[..., None], base_rgba, 0), 344, up_px=26)
    leg_r = extend_top_upward(np.where(leg_r_mask[..., None], base_rgba, 0), 344, up_px=26)

    phase_01 = (frame_idx % n_frames) / float(n_frames)
    phase = 2.0 * math.pi * phase_01
    s_l = math.cos(phase - 0.35)
    s_r = -s_l
    bob_dy = sample_run_profile(phase_01)[4] * 0.85
    sway_dx = -3.6 * math.sin(phase)
    tilt_deg = 1.8 * math.sin(phase)

    def pose_leg(leg_im, side_sign, s_val):
        hx = 212.0 if side_sign < 0 else 268.0
        kx = 210.0 if side_sign < 0 else 270.0
        ax = 204.0 if side_sign < 0 else 276.0
        if s_val > 0.0:
            lift = s_val
            if not is_back:
                return warp_limb_3bone(
                    leg_im, (hx, 344.0), (kx, 464.0), (ax, 576.0),
                    ang_upper=-side_sign * 3.5 * lift,
                    ang_lower=side_sign * 4.5 * lift,
                    sy_upper=1.0 - 0.25 * lift,
                    sy_lower=1.0 - 0.16 * lift,
                    scale_all=1.0 + 0.045 * lift,
                    dx=sway_dx, dy=bob_dy - 14.0 * lift,
                )
            else:
                return warp_limb_3bone(
                    shade_rgba(leg_im, 1.0 - 0.08 * lift),
                    (hx, 344.0), (kx, 464.0), (ax, 576.0),
                    ang_upper=-side_sign * 2.5 * lift,
                    ang_lower=side_sign * 3.0 * lift,
                    sy_upper=1.0 - 0.10 * lift,
                    sy_lower=1.0 - 0.36 * lift,
                    scale_all=1.0 - 0.03 * lift,
                    dx=sway_dx, dy=bob_dy - 10.0 * lift,
                )
        else:
            p = -s_val
            return warp_limb_3bone(
                leg_im, (hx, 344.0), (kx, 464.0), (ax, 576.0),
                ang_upper=side_sign * 2.5 * p,
                ang_lower=-side_sign * 1.5 * p,
                sy_upper=1.0 + 0.02 * p,
                sy_lower=1.0 + 0.02 * p,
                dx=sway_dx, dy=max(0.0, bob_dy * 0.4),
            )

    def pose_arm(arm_im, side_sign, arm_swing):
        sx0 = 180.0 if side_sign < 0 else 300.0
        ex0 = 174.0 if side_sign < 0 else 306.0
        wx0 = 172.0 if side_sign < 0 else 308.0
        if arm_swing > 0.0:
            u = arm_swing
            im_s = shade_rgba(arm_im, 1.0 + 0.03 * u if not is_back else 1.0 - 0.08 * u)
            return warp_limb_3bone(
                im_s, (sx0, 174.0), (ex0, 265.0), (wx0, 342.0),
                ang_upper=side_sign * 7.0 * u,
                ang_lower=-side_sign * 22.0 * u,
                sy_upper=1.0 - 0.10 * u,
                sy_lower=1.0 - 0.28 * u,
                dx=sway_dx, dy=bob_dy - 8.0 * u,
            )
        else:
            b = -arm_swing
            im_s = shade_rgba(arm_im, 1.0 - 0.10 * b if not is_back else 1.0 + 0.03 * b)
            return warp_limb_3bone(
                im_s, (sx0, 174.0), (ex0, 265.0), (wx0, 342.0),
                ang_upper=-side_sign * 8.0 * b,
                ang_lower=-side_sign * 10.0 * b,
                sy_upper=1.0 - 0.12 * b,
                sy_lower=1.0 - 0.18 * b,
                dx=sway_dx, dy=bob_dy - 5.0 * b,
            )

    leg_l_p = pose_leg(leg_l, -1.0, s_l)
    leg_r_p = pose_leg(leg_r, +1.0, s_r)
    torso_p = warp_rigid_rgba(torso, (240.0, 260.0), angle_deg=tilt_deg, dx=sway_dx, dy=bob_dy)
    arm_l_p = pose_arm(arm_l, -1.0, s_r)
    arm_r_p = pose_arm(arm_r, +1.0, s_l)

    out = np.zeros_like(base_rgba)
    if (s_l >= s_r) != is_back:
        out = alpha_over(alpha_over(out, leg_r_p), leg_l_p)
    else:
        out = alpha_over(alpha_over(out, leg_l_p), leg_r_p)

    if (s_r >= s_l) != is_back:
        out = alpha_over(alpha_over(alpha_over(out, arm_r_p), torso_p), arm_l_p)
    else:
        out = alpha_over(alpha_over(alpha_over(out, arm_l_p), torso_p), arm_r_p)
    return out


def render_side_or_diag_run_frame(
    base_rgba: np.ndarray,
    view_deg: int,
    frame_idx: int,
    n_frames: int = 8,
) -> np.ndarray:
    """Synthesizes frame f of an 8-frame run cycle for 45°, 90°, or 135° (facing screen-left -X)."""
    H, W = base_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]

    if view_deg == 90:
        sh_pt, el_pt, wr_pt = (244.0, 180.0), (249.0, 266.0), (241.0, 344.0)
        near_arm, hand_hole = _extract_tapered_sleeve(base_rgba, sh_pt, el_pt, wr_pt, r_sh=18.5, r_wr=14.5)
        far_arm = shade_rgba(near_arm, 0.78)

        body_clean = inpaint_fabric_region(base_rgba, hand_hole)
        torso = np.zeros_like(base_rgba)
        torso[yg < 348] = body_clean[yg < 348]
        for yy in range(343, 348):
            torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((348 - yy) / 5.0)).astype(np.uint8)

        near_leg = np.zeros_like(base_rgba)
        near_leg[yg >= 342] = body_clean[yg >= 342]
        near_leg = extend_top_upward(near_leg, 342, up_px=28)
        far_leg = shade_rgba(near_leg, 0.82)

        stride_scale = 1.00
        lean_deg = 5.8
        hip_pt, knee_pt, ankle_pt = (242.0, 342.0), (242.0, 464.0), (244.0, 574.0)
        far_dx = -6.0
        far_sh, far_el, far_wr = (sh_pt[0] - 10.0, sh_pt[1]), (el_pt[0] - 10.0, el_pt[1]), (wr_pt[0] - 10.0, wr_pt[1])

    elif view_deg == 45:
        # Far (screen-left) arm & near (screen-right) tapered sleeve + solid torso ribcage overlap (zero shoulder/armpit gap!)
        far_arm_m = (xg < 196) & (yg >= 170) & (yg <= 376) & (base_rgba[..., 3] > 0)
        far_arm = extend_top_upward(np.where(far_arm_m[..., None], base_rgba, 0), 170, up_px=14)

        sh_pt, el_pt, wr_pt = (278.0, 178.0), (288.0, 266.0), (284.0, 344.0)
        near_arm_raw, hand_hole = _extract_tapered_sleeve(base_rgba, sh_pt, el_pt, wr_pt, r_sh=20.0, r_wr=15.0)
        near_arm = extend_top_upward(near_arm_raw, 170, up_px=14)

        # Inpaint the resting near hand/cuff on the underlying hip/jacket, and keep full natural ribcage width
        body_clean = inpaint_fabric_region(base_rgba, hand_hole)
        t_rib = np.clip((yg.astype(np.float32) - 180.0) / 160.0, 0.0, 1.0)
        rib_l = 186.0 + 10.0 * t_rib   # overlaps behind far_arm at shoulder, tapers inward to waist
        rib_r = 286.0 - 15.0 * t_rib   # keeps full right shoulder/chest behind near_arm, tapers inward past elbow/hand!
        torso_m = (yg < 348) & (body_clean[..., 3] > 0) & (
            (yg < 170) | ((xg >= rib_l) & (xg <= rib_r))
        )
        torso = np.where(torso_m[..., None], body_clean, 0)
        for yy in range(343, 348):
            torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((348 - yy) / 5.0)).astype(np.uint8)

        # Extract the complete, rounded near (right-side) trouser leg with smooth inner-thigh taper
        near_hand_outer = (xg > 274) & (yg >= 330) & (yg <= 382)
        leg_zone = (yg >= 342) & (~far_arm_m) & (~near_hand_outer) & (body_clean[..., 3] > 0)
        near_raw = np.where((leg_zone & (xg >= 235))[..., None], body_clean, 0)
        # Smoothly round the upper inner seam (x=235..243, y=342..422) so high knee never shows a straight edge
        seam_band = (yg >= 342) & (yg <= 425) & (xg >= 235) & (xg <= 243)
        if np.any(seam_band):
            w_seam = np.clip((xg.astype(np.float32) - 235.0) / 7.0, 0.0, 1.0)
            near_raw[seam_band, 3] = np.round(near_raw[seam_band, 3].astype(np.float32) * w_seam[seam_band]).astype(np.uint8)
        near_leg = extend_top_upward(near_raw, 342, up_px=28)
        # Build far leg from the same clean rounded leg shifted onto the left hip socket for 100% seamless scissoring!
        far_leg = shade_rgba(warp_rigid_rgba(near_leg, (254.0, 342.0), dx=-28.0, dy=-2.0), 0.86)

        stride_scale = 0.78
        lean_deg = 4.4
        hip_pt, knee_pt, ankle_pt = (254.0, 342.0), (255.0, 464.0), (256.0, 574.0)
        far_dx = -28.0
        far_sh, far_el, far_wr = (182.0, 178.0), (176.0, 268.0), (174.0, 344.0)

    else:  # view_deg == 135
        sh_pt, el_pt, wr_pt = (204.0, 180.0), (198.0, 266.0), (194.0, 344.0)
        near_arm, hand_hole = _extract_tapered_sleeve(base_rgba, sh_pt, el_pt, wr_pt, r_sh=17.0, r_wr=13.5)
        far_arm = shade_rgba(near_arm, 0.78)

        body_clean = inpaint_fabric_region(base_rgba, hand_hole)
        torso = np.zeros_like(base_rgba)
        torso[yg < 348] = body_clean[yg < 348]
        for yy in range(343, 348):
            torso[yy, :, 3] = np.round(torso[yy, :, 3].astype(np.float32) * ((348 - yy) / 5.0)).astype(np.uint8)

        # Check whether the 135° studio pose has two separated leg columns (Dennis) or overlapped profile legs (Paul)
        mid_cols = body_clean[450:475, 234:262, 3].max(axis=0)
        if np.any(mid_cols < 20):
            split_x = 234 + int(np.argmin(mid_cols))
            leg_zone = (yg >= 342) & (body_clean[..., 3] > 0)
            near_raw = np.where((leg_zone & (xg <= split_x))[..., None], body_clean, 0)
            far_raw = np.where((leg_zone & (xg > split_x))[..., None], body_clean, 0)
            # Feather upper inner crotch split (y=342..410) for smooth scissoring
            crotch = (yg >= 342) & (yg <= 410) & (np.abs(xg - split_x) <= 5)
            if np.any(crotch):
                wn = np.clip((split_x + 4.0 - xg.astype(np.float32)) / 8.0, 0.0, 1.0)
                near_raw[crotch, 3] = np.round(near_raw[crotch, 3].astype(np.float32) * wn[crotch]).astype(np.uint8)
                far_raw[crotch, 3] = np.round(far_raw[crotch, 3].astype(np.float32) * (1.0 - wn[crotch])).astype(np.uint8)
            near_leg = extend_top_upward(near_raw, 342, up_px=28)
            far_leg = shade_rgba(extend_top_upward(far_raw, 342, up_px=28), 0.85)
            hip_pt, knee_pt, ankle_pt = (218.0, 342.0), (216.0, 464.0), (214.0, 574.0)
            far_dx = +58.0
        else:
            near_leg = np.zeros_like(base_rgba)
            near_leg[yg >= 342] = body_clean[yg >= 342]
            near_leg = extend_top_upward(near_leg, 342, up_px=28)
            far_leg = shade_rgba(near_leg, 0.82)
            hip_pt, knee_pt, ankle_pt = (246.0, 342.0), (248.0, 464.0), (250.0, 574.0)
            far_dx = -8.0

        stride_scale = 0.80
        lean_deg = 4.6
        far_sh, far_el, far_wr = (sh_pt[0] + 10.0, sh_pt[1]), (el_pt[0] + 10.0, el_pt[1]), (wr_pt[0] + 10.0, wr_pt[1])

    ph_01 = (frame_idx % n_frames) / float(n_frames)
    kf_near = sample_run_profile(ph_01)
    kf_far = sample_run_profile((ph_01 + 0.5) % 1.0)
    bob_dy = kf_near[4]

    far_hip = (hip_pt[0] + far_dx, hip_pt[1])
    far_knee = (knee_pt[0] + far_dx, knee_pt[1])
    far_ank = (ankle_pt[0] + far_dx, ankle_pt[1])

    near_leg_p = warp_limb_3bone(
        near_leg, hip_pt, knee_pt, ankle_pt,
        ang_upper=kf_near[0] * stride_scale,
        ang_lower=kf_near[1] * stride_scale,
        ang_tip=kf_near[2] * stride_scale,
        sy_upper=kf_near[3],
        dy=bob_dy,
    )
    far_leg_p = warp_limb_3bone(
        far_leg, far_hip, far_knee, far_ank,
        ang_upper=kf_far[0] * stride_scale,
        ang_lower=kf_far[1] * stride_scale,
        ang_tip=kf_far[2] * stride_scale,
        sy_upper=kf_far[3],
        dy=bob_dy,
    )

    phase = 2.0 * math.pi * frame_idx / float(n_frames)
    swing_near = -math.cos(phase - 0.25)
    swing_far = -swing_near
    elbow_bend = 26.0 * stride_scale

    near_arm_p = warp_limb_3bone(
        near_arm, sh_pt, el_pt, wr_pt,
        ang_upper=24.0 * stride_scale * swing_near,
        ang_lower=elbow_bend,
        sy_lower=0.92,
        dx=-3.0, dy=bob_dy,
    )
    far_arm_p = warp_limb_3bone(
        far_arm, far_sh, far_el, far_wr,
        ang_upper=24.0 * stride_scale * swing_far,
        ang_lower=elbow_bend,
        sy_lower=0.90,
        dx=-6.0, dy=bob_dy,
    )

    torso_p = warp_rigid_rgba(torso, (240.0, 335.0), angle_deg=-lean_deg, dx=-2.5, dy=bob_dy)

    out = np.zeros_like(base_rgba)
    out = alpha_over(out, far_arm_p)
    out = alpha_over(out, far_leg_p)
    out = alpha_over(out, near_leg_p)
    out = alpha_over(out, torso_p)
    out = alpha_over(out, near_arm_p)
    return out


# ---------------------------------------------------------------------------
# 4. Photorealistic Video Expression & Hand-Gesture Grafting
# ---------------------------------------------------------------------------

def clean_paul_video_caption(rgb_frame: np.ndarray) -> np.ndarray:
    """Removes the white 'PAUL' text watermark if present in lower center (y=740..935, x=365..600)."""
    out = rgb_frame.copy()
    roi = out[740:935, 365:600]
    r, g, b = roi[..., 0].astype(np.float32), roi[..., 1].astype(np.float32), roi[..., 2].astype(np.float32)
    span = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    txt = (r > 200) & (g > 198) & (b > 194) & (span < 26)
    if np.sum(txt) < 12:
        return out
    mask = np.zeros(out.shape[:2], dtype=np.uint8)
    mask[740:935, 365:600] = txt.astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=1)
    bgr_clean = cv2.inpaint(cv2.cvtColor(out, cv2.COLOR_RGB2BGR), mask, 6, cv2.INPAINT_TELEA)
    return cv2.cvtColor(bgr_clean, cv2.COLOR_BGR2RGB)


def graft_video_face(
    studio_rgba: np.ndarray,
    vid_rgb: np.ndarray,
    src_eye_l: tuple[float, float],
    src_eye_r: tuple[float, float],
    dst_eye_l: tuple[float, float],
    dst_eye_r: tuple[float, float],
    oval_cy_offset: float = 17.5,
    oval_rx: float = 21.0,
    oval_ry_top: float = 18.5,
    oval_ry_bot: float = 30.0,
    oval_dx: float = 0.0,
    chin_drop_shadow: bool = False,
    src_mouth: tuple[float, float] | None = None,
    dst_mouth: tuple[float, float] | None = None,
) -> np.ndarray:
    """Eye-aligned similarity (or 3-point perspective-foreshortened affine for 45°) face graft
    with automatic neutral DSLR skin-tone calibration."""
    H, W = studio_rgba.shape[:2]

    if src_mouth is not None and dst_mouth is not None:
        s3 = np.array([src_eye_l, src_eye_r, src_mouth], dtype=np.float32)
        d3 = np.array([dst_eye_l, dst_eye_r, dst_mouth], dtype=np.float32)
        M = cv2.getAffineTransform(s3, d3)
    else:
        sv = np.array(src_eye_r, dtype=np.float64) - np.array(src_eye_l, dtype=np.float64)
        dv = np.array(dst_eye_r, dtype=np.float64) - np.array(dst_eye_l, dtype=np.float64)
        scale = float(np.linalg.norm(dv) / max(1e-6, np.linalg.norm(sv)))
        ang = math.atan2(dv[1], dv[0]) - math.atan2(sv[1], sv[0])
        ca, sa = math.cos(ang) * scale, math.sin(ang) * scale
        sx, sy = src_eye_l
        dx, dy = dst_eye_l
        M = np.array([
            [ca, -sa, dx - (ca * sx - sa * sy)],
            [sa,  ca, dy - (sa * sx + ca * sy)],
        ], dtype=np.float32)

    warped_rgb = cv2.warpAffine(vid_rgb, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

    mid_x = 0.5 * (dst_eye_l[0] + dst_eye_r[0]) + oval_dx
    mid_y = 0.5 * (dst_eye_l[1] + dst_eye_r[1])
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    sample_zone = (np.abs(xg - mid_x) < 14.0) & (yg >= mid_y - 14.0) & (yg <= mid_y + 10.0) & (studio_rgba[..., 3] > 240)
    st_rgb = studio_rgba[..., :3].astype(np.float32)
    s_lum = 0.299 * st_rgb[..., 0] + 0.587 * st_rgb[..., 1] + 0.114 * st_rgb[..., 2]
    w_lum = 0.299 * warped_rgb[..., 0] + 0.587 * warped_rgb[..., 1] + 0.114 * warped_rgb[..., 2]
    skin_pair = sample_zone & (s_lum > 90.0) & (w_lum > 80.0)
    if np.sum(skin_pair) > 20:
        gain = np.clip(st_rgb[skin_pair].mean(axis=0) / np.maximum(1.0, warped_rgb[skin_pair].mean(axis=0)), 0.72, 1.28)
        tooth_or_dark = (w_lum < 55.0) | ((w_lum > 185.0) & ((warped_rgb[..., 0] - warped_rgb[..., 2]) < 32.0))
        cal_rgb = np.clip(warped_rgb * gain[None, None, :], 0.0, 255.0)
        w_keep = cv2.GaussianBlur(tooth_or_dark.astype(np.float32), (5, 5), 1.2)[..., None]
        warped_rgb = cal_rgb * (1.0 - 0.65 * w_keep) + warped_rgb * (0.65 * w_keep)

    cy = mid_y + oval_cy_offset
    ry = np.where(yg < cy, oval_ry_top, oval_ry_bot)
    r2 = ((xg - mid_x) / oval_rx) ** 2 + ((yg - cy) / ry) ** 2
    alpha = np.clip((1.08 - np.sqrt(r2)) / 0.24, 0.0, 1.0)
    head_allow = (studio_rgba[..., 3] > 200).astype(np.float32)
    alpha = alpha * head_allow

    out = studio_rgba.copy()
    if chin_drop_shadow:
        sh_r2 = ((xg - mid_x) / (oval_rx * 0.82)) ** 2 + ((yg - (cy + oval_ry_bot - 1.5)) / 5.5) ** 2
        sh_w = np.clip(1.0 - sh_r2, 0.0, 1.0) * 0.34 * head_allow * (1.0 - alpha)
        out[..., :3] = np.clip(np.round(out[..., :3].astype(np.float32) * (1.0 - sh_w[..., None])), 0, 255).astype(np.uint8)

    patch = np.dstack([
        np.clip(np.round(warped_rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])
    return alpha_over(out, patch)


def open_paul_jaw_90_photoreal(view90_rgba: np.ndarray) -> np.ndarray:
    """Photorealistically opens Paul's 90° left-profile mouth at his actual lip line (y=103.5)
    by rotating his real lower jaw downward around his jaw hinge (236, 102) with a natural indented profile notch."""
    out = view90_rgba.copy()
    H, W = out.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    # Extract lower jaw/chin with a soft feathered top edge along y=104..107 so no horizontal cheek seam appears
    jaw_w = (
        np.clip((xg - 205.0) / 1.5, 0.0, 1.0)
        * np.clip((237.0 - xg) / 4.0, 0.0, 1.0)
        * np.clip((yg - 103.8) / 2.6, 0.0, 1.0)
        * np.clip((122.0 - yg) / 2.0, 0.0, 1.0)
    )
    jaw_patch = out.copy()
    jaw_patch[..., 3] = np.round(jaw_patch[..., 3].astype(np.float32) * jaw_w).astype(np.uint8)

    # Carve clean C-notch open-air indentation at front of lips (x < 214.5, y = 103.5..114.5) before dropping jaw
    clear_tip = (xg < 215.0) & (yg >= 103.8) & (yg <= 116.5)
    out[clear_tip] = 0

    # Subtle recessed rounded inner mouth behind lip corner (x=212..217, y=103.5..111.5), leaving x<212 open air!
    cavity = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(cavity)
    dr.pieslice([207, 103, 217, 112], start=-85, end=85, fill=(66, 26, 28, 235))
    dr.line([(210, 103), (214, 103)], fill=(228, 222, 214, 215), width=1)
    cav_arr = cv2.GaussianBlur(np.asarray(cavity, dtype=np.float32), (3, 3), 0.65).astype(np.uint8)

    jaw_dropped = warp_rigid_rgba(jaw_patch, (236.0, 102.0), angle_deg=-11.5, dy=1.8)
    out = alpha_over(out, cav_arr)
    out = alpha_over(out, jaw_dropped)
    return out


def graft_dennis_lecture_gesture(
    studio_front_rgba: np.ndarray,
    vid_rgb: np.ndarray,
    src_eye_l: tuple[float, float],
    src_eye_r: tuple[float, float],
    hand_raise_t: float,
) -> np.ndarray:
    """Composites Dennis's speaking face AND raises his right suit arm + real gesturing hand (hand_raise_t in 0..1)."""
    H, W = studio_front_rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W]

    # Step 1: Graft Dennis's real speaking face onto studio_front_rgba
    dst_el, dst_er = (229.0, 82.5), (251.0, 81.5)
    base = graft_video_face(
        studio_front_rgba, vid_rgb,
        src_eye_l=src_eye_l, src_eye_r=src_eye_r,
        dst_eye_l=dst_el, dst_eye_r=dst_er,
        oval_cy_offset=16.0, oval_rx=19.5, oval_ry_top=14.0, oval_ry_bot=24.5,
    )

    if hand_raise_t <= 0.02:
        return base

    # Step 2: Separate Dennis's studio right arm cleanly through the air gap between hand & hip
    t_hip = np.clip((yg.astype(np.float32) - 245.0) / 85.0, 0.0, 1.0)
    x_cut_l = 189.0 - 11.0 * t_hip
    arm_l_m = (xg < x_cut_l) & (yg >= 166) & (yg <= 388) & (base[..., 3] > 0)
    arm_l = np.where(arm_l_m[..., None], base, 0)
    body_no_rarm = base.copy()
    body_no_rarm[arm_l_m] = 0
    # Darken any stray 1px bright skin bounce on outer trouser seam (x=178..183, y=355..385)
    hip_rim = (xg >= 177) & (xg <= 183) & (yg >= 355) & (yg <= 386) & (body_no_rarm[..., 0] > 90)
    body_no_rarm[hip_rim, :3] = (24, 26, 30)

    # Extract upper-sleeve + forearm (fading out resting hand below wrist y=332 once real video hand takes over)
    sleeve_only = arm_l.copy()
    if hand_raise_t > 0.35:
        fade_w = np.clip((hand_raise_t - 0.35) / 0.30, 0.0, 1.0)
        fade_hand = 1.0 - fade_w * (1.0 - np.clip((332.0 - yg.astype(np.float32)) / 14.0, 0.0, 1.0))
        sleeve_only[..., 3] = np.round(sleeve_only[..., 3].astype(np.float32) * fade_hand).astype(np.uint8)

    # Kinematics: foreshorten upper arm forward (elbow at (176, 217)) and swing forearm up-right so wrist
    # lands directly at (208, 145) right under Dennis's real gesturing video hand!
    t = hand_raise_t
    raised_sleeve = warp_limb_3bone(
        sleeve_only,
        (182.0, 176.0), (176.0, 262.0), (174.0, 330.0),
        ang_upper=+4.0 * t,
        ang_lower=-160.0 * t,
        sy_upper=1.0 - 0.50 * t,
        sy_lower=1.0 + 0.16 * t,
        dx=2.0 * t, dy=-2.0 * t,
    )
    out = alpha_over(body_no_rarm, raised_sleeve)

    # Step 3: Extract real gesturing right hand from video frame (x=180..595, y=565..960 in 944x960)
    if hand_raise_t > 0.35:
        sv = np.array(src_eye_r, dtype=np.float64) - np.array(src_eye_l, dtype=np.float64)
        dv = np.array(dst_er, dtype=np.float64) - np.array(dst_el, dtype=np.float64)
        sc = float(np.linalg.norm(dv) / max(1e-6, np.linalg.norm(sv)))
        ang = math.atan2(dv[1], dv[0]) - math.atan2(sv[1], sv[0])
        ca, sa = math.cos(ang) * sc, math.sin(ang) * sc
        M = np.array([
            [ca, -sa, dst_el[0] - (ca * src_eye_l[0] - sa * src_eye_l[1])],
            [sa,  ca, dst_el[1] - (sa * src_eye_l[0] + ca * src_eye_l[1])],
        ], dtype=np.float32)

        # Skin segmentation on lower-left quadrant of video where raised hand appears (above dark suit & red backdrop)
        vh, vw = vid_rgb.shape[:2]
        vy, vx = np.mgrid[0:vh, 0:vw]
        rf = vid_rgb.astype(np.float32)
        vr, vg, vb = rf[..., 0], rf[..., 1], rf[..., 2]
        vlum = 0.299 * vr + 0.587 * vg + 0.114 * vb
        # Hand skin has moderate red-over-green (12..68) & warm brightness, whereas red studio bg has vr - vg > 78!
        hand_skin = (
            (vy >= 565) & (vx >= 165) & (vx <= 585)
            & (vlum > 52.0)
            & ((vr - vb) > 16.0)
            & ((vr - vg) < 72.0)
            & (vg > 42.0)
        )
        # Exclude neck/chin above y=725 when x > 380
        neck_excl = (vx > 388) & (vy < 745)
        hand_skin = hand_skin & (~neck_excl)
        hand_skin = ndimage.binary_closing(hand_skin, structure=np.ones((5, 5), bool))
        lbl, num = ndimage.label(hand_skin)
        if num > 0:
            sizes = ndimage.sum(hand_skin, lbl, range(1, num + 1))
            best = 1 + int(np.argmax(sizes))
            if sizes[best - 1] > 1800:
                hmask = (lbl == best).astype(np.float32)
                hmask = cv2.GaussianBlur(hmask, (7, 7), 1.6)
                # Feather bottom edge y=935..960 where wrist meets suit sleeve
                bot_fade = np.clip((vh - 2.0 - vy.astype(np.float32)) / 24.0, 0.0, 1.0)
                hmask = hmask * bot_fade

                # Neutralize warm red studio cast on hand skin
                hand_rgb = rf.copy()
                hand_rgb[..., 0] = np.clip(hand_rgb[..., 0] * 0.90, 0, 255)
                hand_rgb[..., 1] = np.clip(hand_rgb[..., 1] * 0.98, 0, 255)
                hand_rgb[..., 2] = np.clip(hand_rgb[..., 2] * 1.06, 0, 255)

                pm_h = np.concatenate([hand_rgb * hmask[..., None], (hmask * 255.0)[..., None]], axis=-1)
                pm_hw = cv2.warpAffine(pm_h, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT)
                wa = pm_hw[..., 3:4] / 255.0
                w_blend = np.clip((hand_raise_t - 0.35) / 0.35, 0.0, 1.0)
                wrgb = np.where(wa > 1e-4, pm_hw[..., :3] / np.maximum(wa, 1e-4), 0.0)
                hand_layer = np.dstack([
                    np.clip(np.round(wrgb), 0, 255).astype(np.uint8),
                    np.clip(np.round(pm_hw[..., 3] * w_blend), 0, 255).astype(np.uint8),
                ])
                out = alpha_over(out, hand_layer)

    return out
