"""Chroma-keying, 2D/3D rubber-whip deformation, and 3D (X, Y, Z) comedy chaos FX
for the Crazy Rubber Finger 360° Character Sprite in BakersfieldQuake."""

from __future__ import annotations

import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage


# ---------------------------------------------------------------------------
# 1. Zero-Fringe Studio #FF00FF Chroma Key (Safe for Flesh/Rubber & Red Mouths!)
# ---------------------------------------------------------------------------

def key_magenta_studio_safe(im_rgb: Image.Image) -> np.ndarray:
    """Zero-fringe #FF00FF studio chroma key that:
      - Protects interior mouth/tongue/lip reds via border-connected flood fill + closed loop check
      - Protects warm peach/tan rubber-finger & skin tones (where R >> B)
      - Un-premultiplies boundary AA pixels and propagates clean interior RGB to eliminate pink/green halos.
    """
    arr = np.asarray(im_rgb.convert("RGB"), dtype=np.float32)
    H, W = arr.shape[:2]
    r, g, b = arr[..., 0].copy(), arr[..., 1].copy(), arr[..., 2].copy()

    # Pure #FF00FF has high R, high B, low G, and R ≈ B (whereas flesh/rubber has R >> B!)
    m = np.minimum(r, b) - g
    rb_diff = np.abs(r - b)

    raw_bg = (m > 58.0) & (r > 95.0) & (b > 95.0) & (rb_diff < 85.0)

    # Flood-fill from image border so interior mouth/lips never get keyed out,
    # while still allowing genuine enclosed #FF00FF holes (e.g. between arm & torso or legs) where m > 105!
    border_seed = np.zeros((H, W), dtype=bool)
    border_seed[0, :] = raw_bg[0, :]
    border_seed[-1, :] = raw_bg[-1, :]
    border_seed[:, 0] = raw_bg[:, 0]
    border_seed[:, -1] = raw_bg[:, -1]
    ext_bg = ndimage.binary_propagation(border_seed, mask=raw_bg)
    enclosed_pure_magenta = (m > 115.0) & (r > 165.0) & (b > 165.0) & (g < 75.0) & (rb_diff < 55.0)
    bg = ext_bg | enclosed_pure_magenta

    dist = ndimage.distance_transform_edt(~bg)

    alpha = np.ones((H, W), dtype=np.float32)
    alpha[bg] = 0.0

    # Smooth AA alpha ramp ONLY on pixels adjacent to background where R and B are both elevated over G
    edge = (~bg) & (dist <= 8.0) & (rb_diff < 82.0)
    a_ramp = np.clip(1.0 - (m - 12.0) / 52.0, 0.0, 1.0)
    use_r = edge & (m > 12.0)
    alpha[use_r] = np.where(a_ramp[use_r] <= 0.05, 0.0, a_ramp[use_r])

    # Un-premultiply #FF00FF contribution on semi-transparent boundary pixels
    semi = (alpha > 0.0) & (alpha < 0.995)
    inv = 1.0 - alpha[semi]
    denom = np.maximum(alpha[semi], 0.25)
    r[semi] = np.clip((r[semi] - inv * 255.0) / denom, 0.0, 255.0)
    g[semi] = np.clip(g[semi] / denom, 0.0, 255.0)
    b[semi] = np.clip((b[semi] - inv * 255.0) / denom, 0.0, 255.0)

    # Propagate clean interior solid RGB outward across outer rim so neither pink nor green halos appear
    rgb = np.dstack([r, g, b])
    core = ndimage.minimum_filter((alpha > 0.98) & (m < 14.0), size=3)
    if np.any(core):
        _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
        rim = (alpha > 0.0) & (~core) & (dist <= 6.0) & (m > 10.0)
        rgb[rim] = rgb[iy[rim], ix[rim]]

    # Gentle neutral despill ONLY on cool magenta bounce (where R ≈ B, never on warm flesh/rubber where R > B + 22!)
    r2, g2, b2 = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m2 = np.minimum(r2, b2) - g2
    cool_bounce = (alpha > 0.0) & (dist <= 16.0) & (m2 > 6.0) & ((r2 - b2) < 22.0)
    if np.any(cool_bounce):
        excess = m2[cool_bounce] - 4.0
        r2[cool_bounce] = np.clip(r2[cool_bounce] - 0.70 * excess, 0.0, 255.0)
        b2[cool_bounce] = np.clip(b2[cool_bounce] - 0.78 * excess, 0.0, 255.0)
        g2[cool_bounce] = np.clip(g2[cool_bounce] + 0.15 * excess, 0.0, 255.0)

    alpha = np.clip((alpha - 0.05) / 0.95, 0.0, 1.0)

    out = np.dstack([
        np.clip(np.round(r2), 0, 255).astype(np.uint8),
        np.clip(np.round(g2), 0, 255).astype(np.uint8),
        np.clip(np.round(b2), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])
    return keep_main_character_rgba(out)


def keep_main_character_rgba(rgba: np.ndarray, min_rel_area: float = 0.015) -> np.ndarray:
    """Keeps the main character connected component (and any nearby large prop component), removing stray specks."""
    mask = rgba[..., 3] > 20
    lbl, num = ndimage.label(mask)
    if num <= 1:
        return rgba
    sizes = ndimage.sum(mask, lbl, range(1, num + 1))
    max_sz = float(np.max(sizes))
    keep_ids = [1 + i for i, s in enumerate(sizes) if s >= max_sz * min_rel_area]
    keep = ndimage.binary_dilation(np.isin(lbl, keep_ids), iterations=2)
    out = rgba.copy()
    out[~keep] = 0
    return out


# ---------------------------------------------------------------------------
# 2. Canvas Normalization, Premultiplied Resize & Affine / Elastic Whip Warping
# ---------------------------------------------------------------------------

def resize_rgba_premul(rgba: np.ndarray, tw: int, th: int) -> np.ndarray:
    """Premultiplied-alpha Lanczos resize for crisp, halo-free silhouettes."""
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)
    pm_u8 = np.clip(np.round(pm), 0, 255).astype(np.uint8)
    pm_im = Image.fromarray(pm_u8, "RGBA").resize((tw, th), Image.Resampling.LANCZOS)
    p = np.asarray(pm_im, dtype=np.float32)
    pa = p[..., 3:4] / 255.0
    rgb = np.where(pa > 1e-3, p[..., :3] / np.maximum(pa, 1e-3), 0.0)
    a_out = np.where(p[..., 3] < 8.0, 0.0, p[..., 3])
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(a_out), 0, 255).astype(np.uint8),
    ])


def normalize_character_to_stage(
    rgba: np.ndarray,
    canvas_w: int = 640,
    canvas_h: int = 680,
    ground_y: int = 626,
    target_body_h: int = 520,
    mirror: bool = False,
) -> np.ndarray:
    """Places a keyed character onto a unified (canvas_w x canvas_h) stage with feet anchored at ground_y
    and horizontal torso center of mass aligned to canvas_w / 2.
    Uses core body height (excluding extreme high/wide whip tips via horizontal torso column bounds) if needed,
    or full height scaled consistently so every angle matches head/body scale!
    """
    src = rgba[:, ::-1, :].copy() if mirror else rgba.copy()
    mask = src[..., 3] > 28
    if not np.any(mask):
        return np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

    ys, xs = np.nonzero(mask)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    sub = src[y0:y1, x0:x1]
    h0, w0 = sub.shape[:2]

    sc = target_body_h / float(h0)
    nw = max(2, int(round(w0 * sc)))
    nh = max(2, int(round(h0 * sc)))
    scaled = resize_rgba_premul(sub, nw, nh)

    # Compute horizontal center of mass across torso/hips band (40%..80% down from top) so wide sideways finger wags
    # NEVER shift the character's spine off-center!
    a_f = scaled[..., 3].astype(np.float32)
    r_top = int(nh * 0.42)
    r_bot = int(nh * 0.82)
    band = a_f[r_top:r_bot, :]
    if band.sum() > 100.0:
        cx_local = float((band.sum(axis=0) * np.arange(nw)).sum() / band.sum())
    else:
        cx_local = nw * 0.5

    ox = int(round(canvas_w * 0.5 - cx_local))
    oy = int(round(ground_y - nh))

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    im_s = Image.fromarray(scaled, "RGBA")
    # Safely composite even if ox/oy is slightly negative
    canvas.alpha_composite(
        im_s,
        dest=(max(0, ox), max(0, oy)),
        source=(max(0, -ox), max(0, -oy), min(nw, canvas_w - ox), min(nh, canvas_h - oy)),
    )
    return np.asarray(canvas, dtype=np.uint8)


def warp_affine_premul(
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
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(pm_w[..., 3]), 0, 255).astype(np.uint8),
    ])


def apply_elastic_wobble(
    rgba: np.ndarray,
    phase_rad: float,
    grip_y: float = 370.0,
    top_y: float = 60.0,
    whip_amp_x: float = 14.0,
    squash_amp_y: float = 4.5,
    exclude_box: tuple[float, float, float, float] | None = None,
) -> np.ndarray:
    """Applies a smooth, continuous elastic S-curve follow-through wave above `grip_y`
    so the giant rubber finger (and maniacal upper body) jiggles and whips smoothly on every frame!
    Optionally attenuates deformation inside `exclude_box = (x0, y0, x1, y1)` (e.g. core eyes/nose)
    so his facial features stay razor-sharp while the rubber finger whips wildly!
    """
    H, W = rgba.shape[:2]
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)

    u = np.clip((grip_y - yg) / max(1.0, grip_y - top_y), 0.0, 1.25)
    # Traveling rubber whip wave: fundamental bend + 2nd-harmonic S-curve tip flick!
    wave_x = whip_amp_x * (u ** 1.85) * np.sin(phase_rad - 1.35 * u) + (whip_amp_x * 0.28) * (u ** 2.6) * np.sin(2.0 * phase_rad)
    wave_y = squash_amp_y * (u ** 1.5) * np.cos(2.0 * phase_rad - 0.8 * u)

    atten = np.ones((H, W), dtype=np.float32)
    if exclude_box is not None:
        ex0, ey0, ex1, ey1 = exclude_box
        cx, cy = 0.5 * (ex0 + ex1), 0.5 * (ey0 + ey1)
        rx, ry = max(1.0, 0.5 * (ex1 - ex0)), max(1.0, 0.5 * (ey1 - ey0))
        r2 = ((xg - cx) / rx) ** 2 + ((yg - cy) / ry) ** 2
        # Keep gentle 25% head bobble inside face oval while 100% full whip hits the rubber finger!
        atten = 0.25 + 0.75 * np.clip((np.sqrt(r2) - 0.75) / 0.55, 0.0, 1.0)

    map_x = (xg - wave_x * atten).astype(np.float32)
    map_y = (yg - wave_y * atten).astype(np.float32)

    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, f[..., 3:4]], axis=-1)
    pm_dst = cv2.remap(pm, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wa = pm_dst[..., 3:4] / 255.0
    rgb = np.where(wa > 1e-4, pm_dst[..., :3] / np.maximum(wa, 1e-4), 0.0)
    return np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(pm_dst[..., 3]), 0, 255).astype(np.uint8),
    ])


# ---------------------------------------------------------------------------
# 3. True 3D (X, Y, Z) Manic Sweat Drops, Rubber Whoosh Arcs & Comic Wobble FX
# ---------------------------------------------------------------------------

def make_sweat_drop_rgba(size: int = 36) -> Image.Image:
    """Supersampled gleaming comic-studio cyan-white sweat droplet with specular highlight."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = S * 0.5
    # Teardrop pointing toward top-center (rotated along velocity vector when composited!)
    pts = []
    n_pts = 32
    for i in range(n_pts):
        t = 2.0 * math.pi * i / n_pts
        # Parametric teardrop
        rx = S * 0.21 * math.sin(t) * (0.65 + 0.35 * (1.0 - math.cos(t)) * 0.5)
        ry = -S * 0.34 * math.cos(t)
        if math.cos(t) > 0:
            # Pointed tail toward top (-Y)
            rx *= (1.0 - 0.55 * (math.cos(t) ** 1.6))
        pts.append((cx + rx, S * 0.54 + ry))
    d.polygon(pts, fill=(165, 228, 255, 225), outline=(24, 52, 78, 235), width=3)
    # Bright white inner specular highlight
    d.ellipse((cx - S * 0.09, S * 0.52, cx - S * 0.01, S * 0.68), fill=(255, 255, 255, 240))
    return im.resize((size, size), Image.Resampling.LANCZOS)


def draw_kinetic_star(canvas: Image.Image, cx: float, cy: float, radius: int = 26, angle_deg: float = 20.0, warm: bool = True) -> None:
    sz = radius * 2 + 12
    star = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    mid = sz // 2
    glow = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    gcol = (255, 220, 120, 120) if warm else (180, 235, 255, 120)
    ImageDraw.Draw(glow).ellipse((mid - radius // 2, mid - radius // 2, mid + radius // 2, mid + radius // 2), fill=gcol)
    star = Image.alpha_composite(star, glow.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(star)
    pts = [
        (mid, mid - radius), (mid + 4, mid - 4), (mid + radius, mid), (mid + 4, mid + 4),
        (mid, mid + radius), (mid - 4, mid + 4), (mid - radius, mid), (mid - 4, mid - 4),
    ]
    d.polygon(pts, fill=(255, 252, 230, 240), outline=(255, 185, 55, 210))
    r2 = int(radius * 0.48)
    pts2 = [
        (mid - r2, mid - r2), (mid, mid - 3), (mid + r2, mid - r2), (mid + 3, mid),
        (mid + r2, mid + r2), (mid, mid + 3), (mid - r2, mid + r2), (mid - 3, mid),
    ]
    d.polygon(pts2, fill=(255, 235, 145, 215))
    rot = star.rotate(angle_deg, resample=Image.Resampling.BICUBIC)
    canvas.alpha_composite(rot, (int(round(cx - mid)), int(round(cy - mid))))


def draw_rubber_whoosh_arc(
    canvas: Image.Image,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    deg_start: float,
    deg_end: float,
    color_rgb: tuple[int, int, int] = (255, 232, 205),
    max_alpha: int = 155,
    max_width: float = 11.0,
) -> None:
    """Draws a smooth tapered, anti-aliased comic motion-smear crescent arc behind the whipping rubber finger!"""
    W, H = canvas.size
    S = 2
    over = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)

    n_seg = 24
    pts_outer = []
    pts_inner = []
    for i in range(n_seg + 1):
        u = i / float(n_seg)
        ang = math.radians(deg_start + (deg_end - deg_start) * u)
        # Taper width from 0 at tail (u=0) to max at ~0.72, then rounded tip at u=1
        taper = math.sin(math.pi * (u ** 0.78))
        hw = max_width * S * 0.5 * taper
        px = (cx + rx * math.cos(ang)) * S
        py = (cy + ry * math.sin(ang)) * S
        nx = math.cos(ang)
        ny = math.sin(ang)
        pts_outer.append((px + nx * hw, py + ny * hw))
        pts_inner.append((px - nx * hw, py - ny * hw))

    poly = pts_outer + pts_inner[::-1]
    d.polygon(poly, fill=(color_rgb[0], color_rgb[1], color_rgb[2], max_alpha))

    # Secondary crisp outer speed-streak line!
    streak_pts = []
    for i in range(4, n_seg - 1):
        u = i / float(n_seg)
        ang = math.radians(deg_start + (deg_end - deg_start) * u)
        px = (cx + (rx + max_width * 0.95) * math.cos(ang)) * S
        py = (cy + (ry + max_width * 0.95) * math.sin(ang)) * S
        streak_pts.append((px, py))
    if len(streak_pts) >= 2:
        d.line(streak_pts, fill=(255, 250, 240, int(max_alpha * 1.15)), width=4)

    over_sm = over.resize((W, H), Image.Resampling.LANCZOS)
    canvas.alpha_composite(over_sm)


def build_3d_sweat_specs(n_drops: int = 14) -> list[dict]:
    """Builds 100% seamless 8-frame looping 3D manic sweat-drop trajectories around the character's head!"""
    specs = []
    golden = 2.399963229728653
    for i in range(n_drops):
        az = (i * golden) % (2.0 * math.pi)
        ux = math.cos(az)
        uz = math.sin(az) - 0.25
        nrm = math.hypot(ux, uz) + 1e-5
        ux, uz = ux / nrm, uz / nrm

        # Keep front (+Z) drops off the center of his face so his crazy eyes/mouth stay 100% clear!
        if uz > 0.20 and abs(ux) < 0.72:
            ux = -0.90 if (i % 2 == 0) else 0.90
            uz = 0.25

        specs.append({
            "emit_x": ux * 66.0,
            "emit_y": -218.0 + ((i % 4) - 1.5) * 14.0,  # head/temple height relative to cy_origin
            "emit_z": uz * 48.0,
            "vx": ux * (115.0 + (i % 4) * 24.0),
            "vy": -68.0 - (i % 3) * 22.0,
            "vz": uz * (105.0 + (i % 4) * 20.0),
            "grav": 135.0 + (i % 3) * 25.0,
            "phase0": (i * 0.61803398875) % 1.0,
            "size": 22 + (i % 3) * 5,
        })
    return specs


def composite_3d_chaos_fx(
    char_rgba: np.ndarray,
    dir_idx: int,
    frame_idx: int,
    n_frames: int = 8,
    sweat_specs: list[dict] | None = None,
    sweat_drop_im: Image.Image | None = None,
    whoosh_sign: float = 0.0,
) -> np.ndarray:
    """Composites depth-sorted 3D manic sweat drops + whipping rubber finger motion arcs around `char_rgba`."""
    H, W = char_rgba.shape[:2]
    theta = math.radians(dir_idx * 45.0)
    ct, st = math.cos(theta), math.sin(theta)

    if sweat_specs is None:
        sweat_specs = build_3d_sweat_specs(14)
    if sweat_drop_im is None:
        sweat_drop_im = make_sweat_drop_rgba(36)

    cx_origin = W * 0.5
    cy_origin = H * 0.58

    back_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    front_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 1. Whipping Rubber Finger Motion-Smear Arcs on fast wag transitions!
    phase = 2.0 * math.pi * frame_idx / float(n_frames)
    vel = math.cos(phase) if abs(whoosh_sign) < 1e-3 else whoosh_sign
    if abs(vel) > 0.35:
        # Project lateral wag arc according to viewing angle
        lat_proj = ct
        fwd_proj = -st
        rx = 132.0 * abs(lat_proj) + 92.0 * abs(fwd_proj)
        ry = 96.0
        arc_cx = cx_origin + fwd_proj * 52.0
        arc_cy = H * 0.22
        if vel * (lat_proj if abs(lat_proj) >= 0.35 else fwd_proj) >= 0:
            d0, d1 = 205.0, 315.0
        else:
            d0, d1 = 335.0, 225.0
        alpha_arc = int(round(150 * min(1.0, abs(vel))))
        target_arc_layer = back_layer if dir_idx in (0, 1, 7) else front_layer
        draw_rubber_whoosh_arc(target_arc_layer, arc_cx, arc_cy, rx, ry, d0, d1, max_alpha=alpha_arc, max_width=13.0)

    # Peak reversal kinetic *WOBBLE* stars near upper whip zone on peak frames (f=2, f=6)
    if frame_idx in (2, 6):
        side = 1.0 if frame_idx == 2 else -1.0
        if dir_idx in (3, 4, 5):
            side = -side
        sx_star = cx_origin + side * (148.0 if dir_idx in (0, 4) else 96.0)
        sy_star = H * 0.29 + (frame_idx % 3) * 8.0
        draw_kinetic_star(front_layer, sx_star, sy_star, radius=22, angle_deg=18.0 * frame_idx)

    # 2. True 3D Parabolic Manic Sweat Drops!
    t_norm = frame_idx / float(n_frames)
    items = []
    for sp in sweat_specs:
        u = (t_norm + sp["phase0"]) % 1.0
        # Smooth fade-in and fade-out so 8-frame loop has zero pop!
        env = math.sin(math.pi * u)
        if env < 0.08:
            continue
        lx = sp["emit_x"] + sp["vx"] * u
        ly = sp["emit_y"] + sp["vy"] * u + 0.5 * sp["grav"] * (u ** 2)
        lz = sp["emit_z"] + sp["vz"] * u

        # Rotate character-local (lx, lz) by camera orbit angle theta
        vx_cam = lx * ct - lz * st
        vz_cam = lx * st + lz * ct

        # Slight perspective scale with depth vz_cam
        persp = 1.0 + vz_cam / 900.0
        sx = cx_origin + vx_cam * persp
        sy = cy_origin + ly * persp

        # Instantaneous screen-space velocity for teardrop orientation!
        v_lx = sp["vx"]
        v_ly = sp["vy"] + sp["grav"] * u
        v_lz = sp["vz"]
        svx = v_lx * ct - v_lz * st
        svy = v_ly
        ang_deg = math.degrees(math.atan2(svy, svx)) - 90.0  # tail points opposite velocity (-Y is tail)

        sz = max(10, int(round(sp["size"] * persp * (0.75 + 0.35 * env))))
        drop = sweat_drop_im.resize((sz, sz), Image.Resampling.LANCZOS)
        # Attenuate alpha smoothly by env
        arr_d = np.array(drop)
        arr_d[..., 3] = np.round(arr_d[..., 3].astype(np.float32) * (0.85 * env)).astype(np.uint8)
        drop_rot = Image.fromarray(arr_d, "RGBA").rotate(-ang_deg, resample=Image.Resampling.BICUBIC, expand=True)
        items.append((vz_cam, sx, sy, drop_rot))

    items.sort(key=lambda it: it[0])
    for vz_cam, sx, sy, dim in items:
        dw, dh = dim.size
        dst = back_layer if vz_cam < 0.0 else front_layer
        dst.alpha_composite(dim, (int(round(sx - dw * 0.5)), int(round(sy - dh * 0.5))))

    comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    comp.alpha_composite(back_layer)
    comp.alpha_composite(Image.fromarray(char_rgba, "RGBA"))
    comp.alpha_composite(front_layer)
    return np.asarray(comp, dtype=np.uint8)
