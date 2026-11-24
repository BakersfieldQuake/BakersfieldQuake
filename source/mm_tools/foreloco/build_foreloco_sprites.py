"""Procedural 36-frame realistic 2D sprite viewmodel & edge-framed liquid smear generator for zz_foreloco.pk3.

Generates (deterministically, pure NumPy + Pillow, 2x supersampled premultiplied-alpha):
  - gfx/foreloco/vm_01.png .. vm_36.png (640x480 RGBA):
      Realistic masculine right hand (3-phalanx articulated fingers with squared dorsal
      nails, thumb-index interosseous web, dorsal tendons, ulnar wrist bump, gradual
      forearm hair, curved yellow "ERIC" hospital wristband) picking up the real
      Watermelon Four Loko tallboy can (3D ray-cast cylindrical projection from
      assets/four_loko_watermelon.jpg with non-mirrored camo wrap, rolled aluminum rim,
      recessed lid, D-opening, 3D-tilted lifted pull-tab, and chilled condensation),
      sliding up to pop the tab with pressurized CO2 mist/spray, pulling close to
      lower-center mouth level to chug (no street waterfall), pulling down cleanly via
      SLERP, white-knuckle crushing the faceted aluminum can with a foam squirt, and
      yeeting it tumbling forward (+Z) off-left with 16-tap Gaussian shutter blur.
  - gfx/foreloco/pour_stream.png (640x360 RGBA)
  - gfx/foreloco/smear_pink.png  (640x360 RGBA)
  - gfx/foreloco/smear_green.png (640x360 RGBA)
  - gfx/foreloco/smear_drips.png (640x360 RGBA)
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

VM_W = 640
VM_H = 480
SS = 2
STAGE_W = VM_W * SS  # 1280
STAGE_H = VM_H * SS  # 960

OV_W = 640
OV_H = 360

NUM_VM_FRAMES = 36


# ---------------------------------------------------------------------------
# Premultiplied-Alpha, Quaternion SLERP & 3D Basis Helpers
# ---------------------------------------------------------------------------
def _premul_from_rgba(rgba: np.ndarray) -> np.ndarray:
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    return np.dstack([f[..., :3] * a, f[..., 3:4]])


def _rgba_from_premul(pm: np.ndarray) -> np.ndarray:
    a = np.clip(pm[..., 3], 0.0, 255.0)
    denom = np.maximum(a[..., None] / 255.0, 1e-4)
    rgb = np.clip(pm[..., :3] / denom, 0.0, 255.0)
    a_u8 = np.round(a).astype(np.uint8)
    rgb_u8 = np.round(rgb).astype(np.uint8)
    rgb_u8[a_u8 == 0] = 0
    return np.dstack([rgb_u8, a_u8])


def _over_premul(dst_pm: np.ndarray, src_pm: np.ndarray) -> np.ndarray:
    sa = np.clip(src_pm[..., 3:4] / 255.0, 0.0, 1.0)
    return src_pm + dst_pm * (1.0 - sa)


def _downsample_2x(pm: np.ndarray) -> np.ndarray:
    ds = pm.reshape(VM_H, SS, VM_W, SS, 4).mean(axis=(1, 3))
    return _rgba_from_premul(ds)


def _norm3(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / (n if n > 1e-6 else 1.0)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp3(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _sstep(a: float, b: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - a) / max(1e-6, b - a)))
    return t * t * (3.0 - 2.0 * t)


def _euler_to_mat(pitch_deg: float, yaw_deg: float, roll_deg: float) -> np.ndarray:
    """Right-handed rotation matrix R = Rz(roll) @ Ry(yaw) @ Rx(pitch), det(R) == +1.0."""
    px, py, pz = map(math.radians, (pitch_deg, yaw_deg, roll_deg))
    cx, sx = math.cos(px), math.sin(px)
    cy, sy = math.cos(py), math.sin(py)
    cz, sz = math.cos(pz), math.sin(pz)
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=np.float32)
    ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float32)
    rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    return (rz @ ry @ rx).astype(np.float32)


def _mat_to_quat(R: np.ndarray) -> np.ndarray:
    """Converts 3x3 rotation matrix to unit quaternion (w, x, y, z)."""
    tr = float(R[0, 0] + R[1, 1] + R[2, 2])
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        q = np.array([0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s])
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + float(R[0, 0] - R[1, 1] - R[2, 2])) * 2.0
        q = np.array([(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s])
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + float(R[1, 1] - R[0, 0] - R[2, 2])) * 2.0
        q = np.array([(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s])
    else:
        s = math.sqrt(1.0 + float(R[2, 2] - R[0, 0] - R[1, 1])) * 2.0
        q = np.array([(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s])
    return (q / (np.linalg.norm(q) or 1.0)).astype(np.float64)


def _quat_to_mat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = map(float, q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float32)


def _slerp_mat(R0: np.ndarray, R1: np.ndarray, t: float) -> np.ndarray:
    """Shortest-arc quaternion SLERP between two proper rotation matrices (zero singularities)."""
    t = max(0.0, min(1.0, float(t)))
    q0 = _mat_to_quat(R0)
    q1 = _mat_to_quat(R1)
    dot = float(np.dot(q0, q1))
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    if dot > 0.9995:
        q = q0 + t * (q1 - q0)
        return _quat_to_mat(q / np.linalg.norm(q))
    theta0 = math.acos(min(1.0, dot))
    theta = theta0 * t
    sin0 = math.sin(theta0)
    s0 = math.cos(theta) - dot * math.sin(theta) / sin0
    s1 = math.sin(theta) / sin0
    return _quat_to_mat(s0 * q0 + s1 * q1)


def _slerp_quad(R0: np.ndarray, R_mid: np.ndarray, R1: np.ndarray, t: float) -> np.ndarray:
    """De Casteljau quadratic quaternion Bezier SLERP: C-infinity smooth arc with zero midpoint slowdown."""
    a = _slerp_mat(R0, R_mid, t)
    b = _slerp_mat(R_mid, R1, t)
    return _slerp_mat(a, b, t)


# ---------------------------------------------------------------------------
# Non-Mirrored Label Unwrapping & 3D Can Ray-Caster
# ---------------------------------------------------------------------------
def _build_unwrapped_label(assets_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Unwraps front hero label cleanly onto u in [0, 0.5] and tiles non-mirrored
    watermelon camo + subtle nutrition panel onto back u in [0.5, 1.0] (never backwards text!).
    Also builds precomputed 512x512 condensation map."""
    src = Image.open(assets_dir / "four_loko_watermelon.jpg").convert("RGB")
    src = ImageEnhance.Color(src).enhance(1.16)
    src = ImageEnhance.Contrast(src).enhance(1.06)
    arr = np.asarray(src, dtype=np.float32)

    tw, th = 512, 512
    sy = np.linspace(51.0, 449.0, th, dtype=np.float32)
    y0 = np.floor(sy).astype(np.int32)
    fy = (sy - y0)[:, None, None]
    y0c = np.clip(y0, 0, 499)
    y1c = np.clip(y0 + 1, 0, 499)

    def sample_cols(sx_arr: np.ndarray) -> np.ndarray:
        x0 = np.floor(sx_arr).astype(np.int32)
        fx = (sx_arr - x0)[None, :, None]
        x0c = np.clip(x0, 0, 499)
        x1c = np.clip(x0 + 1, 0, 499)
        c00 = arr[y0c[:, None], x0c[None, :]]
        c10 = arr[y0c[:, None], x1c[None, :]]
        c01 = arr[y1c[:, None], x0c[None, :]]
        c11 = arr[y1c[:, None], x1c[None, :]]
        return (c00 * (1 - fx) + c10 * fx) * (1 - fy) + (c01 * (1 - fx) + c11 * fx) * fy

    # Front 180 deg (cols 0..255): crisp forward-reading hero panel
    theta_front = np.linspace(-1.16, 1.16, 256, dtype=np.float32)
    sx_front = 250.0 + 70.5 * np.sin(theta_front)
    front_panel = sample_cols(sx_front)
    debake_f = np.clip(1.0 / (np.cos(theta_front * 0.65) ** 0.42), 1.0, 1.25)
    front_panel *= debake_f[None, :, None]

    # Back 180 deg (cols 256..511): seamless pure green/pink camo strips (0 white text slivers!)
    camo_edge = sample_cols(np.linspace(184.0, 199.0, 32, dtype=np.float32))
    # Replace top/bottom shoulder text rows (y_tex < 92 or > 440) with clean mid-body camo
    camo_edge[:92, :, :] = camo_edge[92:184, :, :]
    camo_edge[440:, :, :] = camo_edge[368:440, :, :]
    camo_pair = np.concatenate([camo_edge, camo_edge[:, ::-1, :]], axis=1)  # 64px seamless tile
    back_strip = np.concatenate([camo_pair, camo_pair, camo_pair, camo_pair], axis=1)
    # Subtle compact nutrition/barcode patch on far-back lower margin
    back_strip[300:395, 114:146, :] = back_strip[300:395, 114:146, :] * 0.35 + np.array([205.0, 212.0, 208.0]) * 0.65
    for row_l in range(308, 388, 9):
        back_strip[row_l:row_l + 2, 118:142, :] = 28.0
    # Smooth seam blend at u=0.5 (col 256) and u=1.0 (col 511->0)
    blend_w = 14
    alpha_s = np.linspace(0.0, 1.0, blend_w, dtype=np.float32)[None, :, None]
    back_strip[:, :blend_w] = front_panel[:, -blend_w:] * (1 - alpha_s) + back_strip[:, :blend_w] * alpha_s
    back_strip[:, -blend_w:] = back_strip[:, -blend_w:] * (1 - alpha_s) + front_panel[:, :blend_w] * alpha_s

    tex = np.concatenate([front_panel, back_strip], axis=1)
    tex = np.clip(tex, 0.0, 255.0).astype(np.float32)

    # Precomputed 512x512 chilled condensation map (dx_n, dy_n, glint, rim)
    cond = np.zeros((th, tw, 4), dtype=np.float32)
    yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32)
    rng_c = np.random.default_rng(101)
    for _ in range(160):
        cx = rng_c.uniform(10.0, tw - 10.0)
        cy = rng_c.uniform(22.0, th - 22.0)
        rx = rng_c.uniform(2.0, 4.4)
        ry = rx * rng_c.uniform(1.0, 1.35)
        x0_b, x1_b = max(0, int(cx - rx - 2)), min(tw, int(cx + rx + 3))
        y0_b, y1_b = max(0, int(cy - ry - 2)), min(th, int(cy + ry + 3))
        dx_p = (xx[y0_b:y1_b, x0_b:x1_b] - cx) / rx
        dy_p = (yy[y0_b:y1_b, x0_b:x1_b] - cy) / ry
        rr = np.hypot(dx_p, dy_p)
        in_d = rr < 1.0
        cond[y0_b:y1_b, x0_b:x1_b, 0] = np.where(in_d, dx_p * 0.42, cond[y0_b:y1_b, x0_b:x1_b, 0])
        cond[y0_b:y1_b, x0_b:x1_b, 1] = np.where(in_d, -dy_p * 0.42, cond[y0_b:y1_b, x0_b:x1_b, 1])
        gl = np.hypot(dx_p - 0.30, dy_p + 0.30) < 0.34
        cond[y0_b:y1_b, x0_b:x1_b, 2] = np.maximum(cond[y0_b:y1_b, x0_b:x1_b, 2], np.where(gl, 0.50, 0.0))
        cond[y0_b:y1_b, x0_b:x1_b, 3] = np.maximum(cond[y0_b:y1_b, x0_b:x1_b, 3], np.where(in_d & (rr > 0.72), 0.25, 0.0))

    return tex, cond


def _render_can_3d(
    label_tex: np.ndarray,
    cond_map: np.ndarray,
    center_cam: tuple[float, float, float],
    R_can: np.ndarray,
    tab_open: float = 0.0,
    crush: float = 0.0,
    focal: float = 1080.0,
) -> tuple[np.ndarray, dict]:
    """Ray-casts 3D tallboy with sharp faceted aluminum crush, warped rim, D-hole,
    and true 3D-tilted lifted metal pull-tab above the recessed lid."""
    R_inv = R_can.T
    C = np.array(center_cam, dtype=np.float32)
    H_half = 1.475
    R_body = 0.50
    R_rim = 0.435

    def proj(p_loc: tuple[float, float, float]) -> tuple[float, float, float]:
        pw = R_can @ np.array(p_loc, dtype=np.float32) + C
        z = max(0.25, float(pw[2]))
        return (STAGE_W * 0.5 + focal * float(pw[0]) / z, STAGE_H * 0.5 - focal * float(pw[1]) / z, z)

    corners = []
    for sx_c in (-0.60, 0.60):
        for sy_c in (-1.62, 1.72):
            for sz_c in (-0.60, 0.60):
                px, py, _ = proj((sx_c, sy_c, sz_c))
                corners.append((px, py))
    xs_c = [c[0] for c in corners]
    ys_c = [c[1] for c in corners]
    x_min = max(0, int(math.floor(min(xs_c))) - 8)
    x_max = min(STAGE_W, int(math.ceil(max(xs_c))) + 8)
    y_min = max(0, int(math.floor(min(ys_c))) - 8)
    y_max = min(STAGE_H, int(math.ceil(max(ys_c))) + 8)

    out_pm = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.float32)
    # D-opening sits at front-left (-0.15, H_half-0.05, -0.15) facing mouth;
    # Pull-tab ring sits on back-right (+0.14, H_half-0.05, +0.14) reachable by right thumb!
    anchors = {
        "top_center": proj((0.0, H_half, 0.0)),
        "drink_hole": proj((-0.14, H_half - 0.05, -0.14)),
        "tab_ring": proj((0.15, H_half - 0.02, 0.14)),
        "base_center": proj((0.0, -H_half, 0.0)),
        "proj": proj,
    }
    if x_max <= x_min or y_max <= y_min:
        return out_pm, anchors

    bw, bh = x_max - x_min, y_max - y_min
    py_g, px_g = np.mgrid[y_min:y_max, x_min:x_max].astype(np.float32)
    rx = (px_g - STAGE_W * 0.5) / focal
    ry = -(py_g - STAGE_H * 0.5) / focal
    rz = np.ones_like(rx)
    norm = np.sqrt(rx * rx + ry * ry + rz * rz)
    Dx, Dy, Dz = rx / norm, ry / norm, rz / norm

    Ox = -(R_inv[0, 0] * C[0] + R_inv[0, 1] * C[1] + R_inv[0, 2] * C[2])
    Oy = -(R_inv[1, 0] * C[0] + R_inv[1, 1] * C[1] + R_inv[1, 2] * C[2])
    Oz = -(R_inv[2, 0] * C[0] + R_inv[2, 1] * C[1] + R_inv[2, 2] * C[2])

    dx = R_inv[0, 0] * Dx + R_inv[0, 1] * Dy + R_inv[0, 2] * Dz
    dy = R_inv[1, 0] * Dx + R_inv[1, 1] * Dy + R_inv[1, 2] * Dz
    dz = R_inv[2, 0] * Dx + R_inv[2, 1] * Dy + R_inv[2, 2] * Dz

    def can_radius(y_val: np.ndarray, theta_val: np.ndarray) -> np.ndarray:
        r = np.full_like(y_val, R_body)
        t_top = np.clip((y_val - 1.15) / 0.25, 0.0, 1.0)
        r = r * (1.0 - t_top) + R_rim * t_top
        in_rim = y_val > 1.40
        r = np.where(in_rim, R_rim * (1.0 + 0.045 * np.sin(np.clip((y_val - 1.40) / 0.075, 0, 1) * math.pi)), r)
        t_bot = np.clip((-1.33 - y_val) / 0.145, 0.0, 1.0)
        r = r * (1.0 - 0.22 * t_bot)
        if crush > 0.01:
            # Sharp faceted aluminum buckle + subtle oval rim warp!
            band = np.exp(-((y_val + 0.08) / 0.48) ** 2)
            # 4 horizontal finger-pinch indentations on left + thumb pinch on front-right
            f_ind = 0.0
            for fy in (0.24, 0.06, -0.12, -0.30):
                f_ind += np.exp(-((y_val - fy) / 0.08) ** 2)
            lobe_f = np.maximum(0.0, -np.sin(theta_val + 0.25)) ** 1.3
            lobe_t = np.maximum(0.0, np.cos(theta_val - 0.45)) ** 1.6
            # Piecewise faceted ridge fold: 1 - |sin(...)| creates sharp aluminum creases!
            facet = 1.0 - np.abs(np.sin(y_val * 11.0 + theta_val * 2.2))
            pinch = crush * (0.26 * band * (lobe_f + 0.75 * lobe_t) + 0.12 * f_ind * lobe_f + 0.11 * band * facet)
            # Subtle oval rim warp at top when crushed hard
            rim_warp = crush * 0.10 * np.cos(2.0 * theta_val + 0.5) * np.clip((y_val - 0.9) / 0.55, 0.0, 1.0)
            r = r * (1.0 - pinch + rim_warp)
        return r

    a = dx * dx + dz * dz
    b = 2.0 * (Ox * dx + Oz * dz)
    c0 = Ox * Ox + Oz * Oz - R_body * R_body
    disc0 = b * b - 4.0 * a * c0
    t_cyl = (-b - np.sqrt(np.maximum(disc0, 0.0))) / np.maximum(2.0 * a, 1e-6)
    disc_i = disc0

    for _ in range(3):
        hx = Ox + dx * t_cyl
        hy = Oy + dy * t_cyl
        hz = Oz + dz * t_cyl
        th = np.arctan2(hx, -hz)
        r_target = can_radius(hy, th)
        c_i = Ox * Ox + Oz * Oz - r_target * r_target
        disc_i = b * b - 4.0 * a * c_i
        t_new = (-b - np.sqrt(np.maximum(disc_i, 0.0))) / np.maximum(2.0 * a, 1e-6)
        t_cyl = np.where(disc_i >= 0.0, t_new, t_cyl)

    hx = Ox + dx * t_cyl
    hy = Oy + dy * t_cyl
    hz = Oz + dz * t_cyl
    r_hit = np.hypot(hx, hz)
    th_hit = np.arctan2(hx, -hz)

    r_closest = np.abs(Ox * dz - Oz * dx) / np.sqrt(np.maximum(a, 1e-6))
    t_closest = -b / np.maximum(2.0 * a, 1e-6)
    y_closest = Oy + dy * t_closest
    r_targ_cl = can_radius(y_closest, np.arctan2(Ox + dx * t_closest, -(Oz + dz * t_closest)))
    px_scale = float(C[2]) / focal
    aa_w = px_scale * 1.5

    valid_y_cyl = (hy >= -H_half) & (hy <= H_half)
    t_top = (1.385 - Oy) / np.where(np.abs(dy) > 1e-5, dy, 1e-5)
    tx_top, tz_top = Ox + dx * t_top, Oz + dz * t_top
    tr_top = np.hypot(tx_top, tz_top)
    top_r_limit = R_rim * (0.96 + (crush * 0.10 * np.cos(2.0 * np.arctan2(tx_top, -tz_top) + 0.5) if crush > 0.01 else 0.0))
    hit_top = (dy < -1e-5) & (t_top > 0) & (tr_top <= top_r_limit)

    t_rim = (1.465 - Oy) / np.where(np.abs(dy) > 1e-5, dy, 1e-5)
    tx_rim, tz_rim = Ox + dx * t_rim, Oz + dz * t_rim
    tr_rim = np.hypot(tx_rim, tz_rim)
    rim_r_warp = R_rim * (1.0 + (crush * 0.10 * np.cos(2.0 * np.arctan2(tx_rim, -tz_rim) + 0.5) if crush > 0.01 else 0.0))
    hit_rim = (dy < -1e-5) & (t_rim > 0) & (tr_rim >= rim_r_warp * 0.84) & (tr_rim <= rim_r_warp * 1.04)

    t_bot = (-H_half - Oy) / np.where(np.abs(dy) > 1e-5, dy, 1e-5)
    tx_bot, tz_bot = Ox + dx * t_bot, Oz + dz * t_bot
    tr_bot = np.hypot(tx_bot, tz_bot)
    hit_bot = (dy > 1e-5) & (t_bot > 0) & (tr_bot <= R_body * 0.82)

    # 3D Ray-Plane Intersection for Lifted Pull-Tab!
    # Tab lies along diagonal axis u_tab = normalize((+1, 0, +1)) from hinge at (0, 1.40, 0),
    # pitched upward by tab_ang around perpendicular v_tab = (-1/sqrt2, 0, +1/sqrt2).
    tab_ang = math.radians(tab_open * 72.0)
    ca_t, sa_t = math.cos(tab_ang), math.sin(tab_ang)
    s2 = math.sqrt(0.5)
    # Tab plane normal in local space: n_tab = (-s2*sa_t, ca_t, -s2*sa_t)
    ntx, nty, ntz = -s2 * sa_t, ca_t, -s2 * sa_t
    denom_t = dx * ntx + dy * nty + dz * ntz
    t_tab = ((0.0 - Ox) * ntx + (1.405 - Oy) * nty + (0.0 - Oz) * ntz) / np.where(np.abs(denom_t) > 1e-5, denom_t, 1e-5)
    px_t = Ox + dx * t_tab
    py_t = Oy + dy * t_tab - 1.405
    pz_t = Oz + dz * t_tab
    # Coordinates along lifted tab: u_along along (+s2*ca_t, sa_t, +s2*ca_t), v_lat along (-s2, 0, +s2)
    u_tab = px_t * (s2 * ca_t) + py_t * sa_t + pz_t * (s2 * ca_t)
    v_tab = -px_t * s2 + pz_t * s2
    in_tab_plate = (np.abs(v_tab) < 0.075) & (u_tab > -0.09) & (u_tab < 0.27)
    in_tab_hole = np.hypot(v_tab / 0.038, (u_tab - 0.16) / 0.055) < 1.0
    hit_tab = (t_tab > 0) & (denom_t < -1e-4) & in_tab_plate & (~in_tab_hole)

    hit_side = (disc_i >= 0.0) & (t_cyl > 0) & valid_y_cyl

    t_best = np.full((bh, bw), 1e9, dtype=np.float32)
    surf_id = np.zeros((bh, bw), dtype=np.int32)  # 1=side, 2=lid, 3=rim, 4=bot, 5=3D tab
    for sid, mask, t_s in [(1, hit_side, t_cyl), (2, hit_top, t_top), (3, hit_rim, t_rim), (4, hit_bot, t_bot), (5, hit_tab, t_tab)]:
        closer = mask & (t_s < t_best)
        t_best = np.where(closer, t_s, t_best)
        surf_id = np.where(closer, sid, surf_id)

    side_sdf = r_targ_cl - r_closest
    y_sdf = np.minimum(H_half - y_closest, y_closest + H_half)
    in_cyl_aa = np.clip((np.minimum(side_sdf, y_sdf) + aa_w * 0.5) / aa_w, 0.0, 1.0)
    top_aa = np.where(dy < -1e-5, np.clip((rim_r_warp * 1.04 - tr_rim + aa_w * 0.5) / aa_w, 0.0, 1.0), 0.0)
    bot_aa = np.where(dy > 1e-5, np.clip((R_body * 0.82 - tr_bot + aa_w * 0.5) / aa_w, 0.0, 1.0), 0.0)
    alpha = np.where(surf_id > 0, 1.0, np.maximum(in_cyl_aa, np.maximum(top_aa, bot_aa)))
    alpha = np.where((surf_id == 0) & (alpha < 0.02), 0.0, alpha)

    u_tex = np.mod((th_hit / (2.0 * math.pi)) + 0.25, 1.0)
    v_tex = np.clip((1.38 - hy) / (1.38 + 1.34), 0.0, 0.999)
    th_h, th_w = label_tex.shape[:2]
    tx_f = u_tex * th_w
    ty_f = v_tex * (th_h - 1)
    ix0 = np.floor(tx_f).astype(np.int32) % th_w
    ix1 = (ix0 + 1) % th_w
    iy0 = np.clip(np.floor(ty_f).astype(np.int32), 0, th_h - 1)
    iy1 = np.clip(iy0 + 1, 0, th_h - 1)
    fx = (tx_f - np.floor(tx_f))[..., None]
    fy = (ty_f - np.floor(ty_f))[..., None]
    lbl_rgb = (
        (label_tex[iy0, ix0] * (1 - fx) + label_tex[iy0, ix1] * fx) * (1 - fy)
        + (label_tex[iy1, ix0] * (1 - fx) + label_tex[iy1, ix1] * fx) * fy
    )

    nx_l = hx / np.maximum(r_hit, 1e-4)
    nz_l = hz / np.maximum(r_hit, 1e-4)
    ny_l = np.zeros_like(nx_l)
    ny_l = np.where(hy > 1.15, 0.26, ny_l)
    ny_l = np.where(hy > 1.40, 0.48, ny_l)
    ny_l = np.where(hy < -1.33, -0.55, ny_l)
    if crush > 0.01:
        band = np.exp(-((hy + 0.08) / 0.48) ** 2)
        # Crisp metallic crease ridges without 1-px discontinuous step artifacts
        s_f = np.sin(hy * 11.0 + th_hit * 2.2)
        d_facet = np.tanh(3.5 * s_f) * np.cos(hy * 11.0 + th_hit * 2.2)
        ny_l = ny_l - crush * 1.15 * band * d_facet
        nx_l = nx_l + crush * 0.85 * band * np.sin(2.0 * (th_hit + 0.35)) * nz_l

    c_smp = cond_map[iy0, ix0]
    nx_l = nx_l + c_smp[..., 0]
    ny_l = ny_l + c_smp[..., 1]
    drop_hi = c_smp[..., 2]
    drop_rim = c_smp[..., 3]

    nlen = np.sqrt(nx_l * nx_l + ny_l * ny_l + nz_l * nz_l) + 1e-6
    nx_l, ny_l, nz_l = nx_l / nlen, ny_l / nlen, nz_l / nlen
    Nx = R_can[0, 0] * nx_l + R_can[0, 1] * ny_l + R_can[0, 2] * nz_l
    Ny = R_can[1, 0] * nx_l + R_can[1, 1] * ny_l + R_can[1, 2] * nz_l
    Nz = R_can[2, 0] * nx_l + R_can[2, 1] * ny_l + R_can[2, 2] * nz_l

    L1 = _norm3(np.array([0.48, 0.65, -0.59], dtype=np.float32))
    V = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    H1 = _norm3(L1 + V)
    ndotl = np.clip(Nx * L1[0] + Ny * L1[1] + Nz * L1[2], 0.0, 1.0)
    ndoth = np.clip(Nx * H1[0] + Ny * H1[1] + Nz * H1[2], 0.0, 1.0)
    rim_l = np.clip(-Nx * 0.75 + Ny * 0.35 - Nz * 0.25, 0.0, 1.0) ** 2.2
    spec_broad = (ndoth ** 14.0) * 0.30
    spec_sharp = (ndoth ** 72.0) * 0.56

    is_metal_band = (hy > 1.375) | (hy < -1.355)
    metal_sheen = 172.0 + 30.0 * np.cos(th_hit * 2.0 + 0.6)
    metal_base = np.stack([metal_sheen, metal_sheen + 6.0, metal_sheen + 14.0], axis=-1)
    base_side = np.where(is_metal_band[..., None], metal_base, lbl_rgb)

    lit_side = base_side * (0.42 + 0.66 * ndotl - drop_rim * 0.45)[..., None]
    lit_side += np.array([255.0, 248.0, 240.0]) * (spec_broad + spec_sharp * np.where(is_metal_band, 1.5, 0.75) + drop_hi)[..., None]
    lit_side += np.array([150.0, 195.0, 235.0]) * (rim_l * 0.22)[..., None]

    # Recessed Top Lid with front-left D-opening (-0.14, -0.14)
    lid_r = tr_top / R_rim
    lid_ang = np.arctan2(tz_top, tx_top)
    sheen = 0.80 + 0.22 * np.cos(2.0 * lid_ang + 0.7)
    score_ring = np.exp(-((lid_r - 0.88) / 0.030) ** 2) * 0.38
    Tn = R_can @ np.array([0.0, 1.0, 0.0], dtype=np.float32)
    top_ndotl = float(np.clip(np.dot(Tn, L1), 0.0, 1.0))
    top_ndoth = float(np.clip(np.dot(Tn, H1), 0.0, 1.0))
    lid_col = np.array([172.0, 182.0, 190.0], dtype=np.float32) * sheen[..., None] * (0.46 + 0.66 * top_ndotl)
    lid_col += np.array([255.0, 250.0, 244.0]) * (top_ndoth ** 20.0) * 0.50
    lid_col *= (1.0 - score_ring)[..., None]

    # Rotate coords into lid D-opening frame aligned with diagonal (-s2, -s2)
    u_hole = (tx_top + tz_top) * s2
    v_hole = (-tx_top + tz_top) * s2
    hole_d = np.hypot(v_hole / 0.135, (u_hole - (-0.19)) / 0.115)
    in_hole = (hole_d < 1.0) & (u_hole < -0.09)
    if tab_open > 0.12:
        interior = np.array([14.0, 10.0, 14.0], dtype=np.float32)
        rim_wet = np.exp(-((hole_d - 0.92) / 0.10) ** 2)
        lid_col = np.where(in_hole[..., None], interior, lid_col)
        lid_col += np.array([255.0, 58.0, 145.0]) * (rim_wet * 0.52 * tab_open)[..., None]
        # Subtle cast shadow of lifted pull-tab onto lid
        tab_shad = np.exp(-((v_hole / 0.10) ** 2 + ((u_hole - 0.12) / 0.15) ** 2)) * 0.32 * tab_open
        lid_col *= (1.0 - tab_shad)[..., None]
    else:
        score_d = np.exp(-((hole_d - 1.0) / 0.06) ** 2)
        lid_col *= (1.0 - 0.38 * score_d)[..., None]
    lid_col = np.where((np.hypot(tx_top, tz_top) < 0.036)[..., None], np.array([124.0, 132.0, 140.0]), lid_col)

    # 3D Lifted Pull-Tab shading
    TabN = R_can @ np.array([ntx, nty, ntz], dtype=np.float32)
    tab_ndotl = float(np.clip(abs(np.dot(TabN, L1)), 0.0, 1.0))
    tab_ndoth = float(np.clip(abs(np.dot(TabN, H1)), 0.0, 1.0))
    tab_col = np.array([218.0, 226.0, 234.0], dtype=np.float32) * (0.50 + 0.58 * tab_ndotl) + np.array([255.0, 250.0, 245.0]) * (tab_ndoth ** 18.0) * 0.55

    rim_ang = np.arctan2(tx_rim, -tz_rim)
    rnx, rnz, rny = np.sin(rim_ang) * 0.65, -np.cos(rim_ang) * 0.65, np.full_like(rim_ang, 0.76)
    RNx = R_can[0, 0] * rnx + R_can[0, 1] * rny + R_can[0, 2] * rnz
    RNy = R_can[1, 0] * rnx + R_can[1, 1] * rny + R_can[1, 2] * rnz
    RNz = R_can[2, 0] * rnx + R_can[2, 1] * rny + R_can[2, 2] * rnz
    r_ndotl = np.clip(RNx * L1[0] + RNy * L1[1] + RNz * L1[2], 0.0, 1.0)
    r_ndoth = np.clip(RNx * H1[0] + RNy * H1[1] + RNz * H1[2], 0.0, 1.0)
    rim_col = np.array([196.0, 205.0, 214.0], dtype=np.float32) * (0.44 + 0.64 * r_ndotl)[..., None]
    rim_col += np.array([255.0, 250.0, 245.0]) * ((r_ndoth ** 22.0) * 0.65)[..., None]

    bot_n = -Tn
    bot_ndotl = float(np.clip(np.dot(bot_n, L1), 0.0, 1.0))
    bot_col = np.array([145.0, 152.0, 160.0], dtype=np.float32) * (0.40 + 0.58 * bot_ndotl)

    rgb = np.zeros((bh, bw, 3), dtype=np.float32)
    rgb = np.where((surf_id == 1)[..., None], lit_side, rgb)
    rgb = np.where((surf_id == 2)[..., None], lid_col, rgb)
    rgb = np.where((surf_id == 3)[..., None], rim_col, rgb)
    rgb = np.where((surf_id == 4)[..., None], bot_col, rgb)
    rgb = np.where((surf_id == 5)[..., None], tab_col, rgb)
    fringe = (surf_id == 0) & (alpha > 0.0)
    rgb = np.where(fringe[..., None], np.where((tr_rim <= rim_r_warp * 1.10)[..., None], rim_col, lit_side), rgb)

    rgb = np.clip(rgb, 0.0, 255.0)
    patch_rgba = np.dstack([rgb.astype(np.uint8), np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)])
    out_pm[y_min:y_max, x_min:x_max] = _premul_from_rgba(patch_rgba)
    return out_pm, anchors


# ---------------------------------------------------------------------------
# Anatomical Masculine Hand: 3-Phalanx Fingers, Squared Nails, Web & Tendons
# ---------------------------------------------------------------------------
def _make_skin_texture(seed: int = 2026) -> np.ndarray:
    rng = np.random.default_rng(seed)
    S = 512
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    low = np.sin(xx * 0.03 + 0.5) * np.cos(yy * 0.025) * 6.5 + np.sin(xx * 0.07 - yy * 0.05) * 4.0
    pore = rng.normal(0.0, 4.2, (S, S)).astype(np.float32)
    pore_im = Image.fromarray(np.clip(128 + pore * 2.0, 0, 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(0.9)
    )
    pore = (np.asarray(pore_im, dtype=np.float32) - 128.0) * 0.45
    base_r = 200.0 + low + pore
    base_g = 146.0 + low * 0.72 + pore * 0.85
    base_b = 116.0 + low * 0.55 + pore * 0.72
    return np.clip(np.dstack([base_r, base_g, base_b]), 0, 255).astype(np.float32)


def _render_eric_stamp() -> np.ndarray:
    im = Image.new("L", (160, 44), 0)
    d = ImageDraw.Draw(im)
    font = None
    for fname in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(fname, 36)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    d.text((80, 22), "ERIC", fill=255, font=font, anchor="mm")
    return np.asarray(im, dtype=np.float32) / 255.0


_ERIC_STAMP = _render_eric_stamp()


def _draw_articulated_digit(
    skin_tex: np.ndarray,
    joints: list[tuple[float, float]],
    r_base: float,
    r_tip: float,
    squeeze: float = 0.0,
    with_nail: bool = True,
    nail_angle_bias: float = -0.22,
    ao_darken: float = 0.0,
    root_fade: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Draws a crisp 3-phalanx articulated digit (straight phalanx planes + slight joint swells)
    with wide, squared-off dorsal nail plate and realistic knuckle blanching."""
    pts = np.asarray(joints, dtype=np.float32)  # 4 joint points: MCP, PIP, DIP, Tip
    xs, ys = pts[:, 0], pts[:, 1]
    pad = int(r_base * 2.3) + 18
    x0 = max(0, int(math.floor(float(xs.min()))) - pad)
    x1 = min(STAGE_W, int(math.ceil(float(xs.max()))) + pad)
    y0 = max(0, int(math.floor(float(ys.min()))) - pad)
    y1 = min(STAGE_H, int(math.ceil(float(ys.max()))) + pad)
    out = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.float32)
    shad = np.zeros((STAGE_H, STAGE_W), dtype=np.float32)
    if x1 <= x0 or y1 <= y0:
        return out, shad

    bh, bw = y1 - y0, x1 - x0
    yg, xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)

    n_seg = len(pts) - 1
    seg_lens = np.hypot(np.diff(xs), np.diff(ys))
    cum = np.concatenate([[0.0], np.cumsum(seg_lens)])
    tot = float(cum[-1]) or 1.0
    cum /= tot

    best_d = np.full((bh, bw), 1e9, dtype=np.float32)
    best_u = np.zeros((bh, bw), dtype=np.float32)
    best_v = np.zeros((bh, bw), dtype=np.float32)

    for i in range(n_seg):
        ax, ay = float(xs[i]), float(ys[i])
        bx, by = float(xs[i + 1]), float(ys[i + 1])
        vx, vy = bx - ax, by - ay
        l2 = vx * vx + vy * vy + 1e-6
        ln = math.sqrt(l2)
        t = np.clip(((xg - ax) * vx + (yg - ay) * vy) / l2, 0.0, 1.0)
        cx, cy = ax + vx * t, ay + vy * t
        dx, dy = xg - cx, yg - cy
        d = np.hypot(dx, dy)
        nx, ny = -vy / ln, vx / ln
        if ny > 0:
            nx, ny = -nx, -ny
        lat = dx * nx + dy * ny
        u_seg = float(cum[i]) + float(cum[i + 1] - cum[i]) * t
        closer = d < best_d
        best_d = np.where(closer, d, best_d)
        best_u = np.where(closer, u_seg, best_u)
        best_v = np.where(closer, lat, best_v)

    u_pip = float(cum[1])
    u_dip = float(cum[2])
    r_prof = r_base * (1.0 - best_u) + r_tip * best_u
    r_prof += r_base * 0.09 * np.exp(-((best_u - u_pip) / 0.09) ** 2)
    r_prof += r_base * 0.06 * np.exp(-((best_u - u_dip) / 0.07) ** 2)

    sdf = r_prof - best_d
    alpha = np.clip((sdf + 1.2) / 2.4, 0.0, 1.0)
    if root_fade:
        alpha *= np.clip((best_u + 0.04) / 0.14, 0.0, 1.0)

    shad[y0:y1, x0:x1] = np.clip((sdf + 9.0) / 13.0, 0.0, 1.0) * 0.42
    v_norm = np.clip(best_v / np.maximum(r_prof, 1.0), -1.0, 1.0)
    cyl = np.sqrt(np.clip(1.0 - v_norm * v_norm, 0.0, 1.0))

    tex_x = np.mod(xg, skin_tex.shape[1]).astype(np.int32)
    tex_y = np.mod(yg, skin_tex.shape[0]).astype(np.int32)
    rgb = skin_tex[tex_y, tex_x].copy()

    light = 0.54 + 0.50 * cyl - 0.22 * v_norm
    warm = (
        np.exp(-((best_u - u_pip) / 0.11) ** 2) * 0.34
        + np.exp(-((best_u - u_dip) / 0.09) ** 2) * 0.24
        + np.clip((best_u - 0.78) / 0.22, 0.0, 1.0) * 0.24
    )
    rgb[..., 0] += warm * 22.0
    rgb[..., 1] -= warm * 7.0
    rgb[..., 2] -= warm * 10.0

    pip_c = np.exp(-((best_u - u_pip) / 0.018) ** 2) * np.clip(1.0 - np.abs(v_norm) * 1.15, 0.0, 1.0)
    dip_c = np.exp(-((best_u - u_dip) / 0.016) ** 2) * np.clip(1.0 - np.abs(v_norm) * 1.15, 0.0, 1.0)
    if squeeze > 0.05:
        blanch = squeeze * (
            np.exp(-((best_u - u_pip) / 0.08) ** 2) + 0.7 * np.exp(-((best_u - u_dip) / 0.07) ** 2)
        ) * np.clip(-v_norm + 0.60, 0.0, 1.0)
        blanch = np.clip(blanch, 0.0, 1.0)
        rgb = rgb * (1.0 - 0.52 * blanch)[..., None] + np.array([248.0, 226.0, 208.0]) * (0.52 * blanch)[..., None]

    rgb *= (light * (1.0 - 0.18 * pip_c - 0.14 * dip_c - ao_darken))[..., None]

    # Wide, squared-off masculine dorsal nail plate (squircle SDF, not circular dot!)
    if with_nail:
        nu = (best_u - 0.78) / 0.19
        nv = (v_norm - nail_angle_bias) / 0.58
        # Superellipse / rounded-rectangle squircle distance (p=4)
        nail_d = ((np.abs(nu - 0.45) * 1.85) ** 4 + (np.abs(nv)) ** 4) ** 0.25
        in_nail = np.clip((0.88 - nail_d) / 0.16, 0.0, 1.0) * (best_u > 0.76) * (best_u < 0.98)
        cuticle = np.exp(-((nail_d - 0.94) / 0.12) ** 2) * (best_u > 0.74) * (best_u < 0.98)
        rgb *= (1.0 - 0.22 * cuticle)[..., None]
        nail_col = rgb * 0.48 + np.array([216.0, 166.0, 150.0], dtype=np.float32) * 0.52 * (0.76 + 0.28 * cyl)[..., None]
        # Subtle lunula & crisp squared pale free edge
        lunula = np.clip(1.0 - np.hypot((nu - 0.12) * 2.8, nv * 1.2), 0.0, 1.0) * 0.18
        nail_col += np.array([26.0, 24.0, 22.0]) * lunula[..., None]
        nail_edge = np.clip((nu - 0.78) / 0.15, 0.0, 1.0) * (1.0 - np.clip((nu - 0.97) / 0.04, 0.0, 1.0))
        nail_col += np.array([36.0, 31.0, 26.0]) * nail_edge[..., None]
        gloss = np.exp(-(((nu - 0.44) / 0.30) ** 2 + ((nv + 0.12) / 0.22) ** 2)) * 24.0
        nail_col += gloss[..., None]
        rgb = rgb * (1.0 - in_nail)[..., None] + nail_col * in_nail[..., None]

    rgba = np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])
    out[y0:y1, x0:x1] = _premul_from_rgba(rgba)
    return out, shad


def _seg_sdf(xg: np.ndarray, yg: np.ndarray, p0: tuple[float, float], p1: tuple[float, float], r0: float, r1: float) -> np.ndarray:
    ax, ay = p0
    bx, by = p1
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy + 1e-6
    t = np.clip(((xg - ax) * vx + (yg - ay) * vy) / l2, 0.0, 1.0)
    d = np.hypot(xg - (ax + vx * t), yg - (ay + vy * t))
    return (r0 * (1.0 - t) + r1 * t) - d


def _smax(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    m = np.maximum(a, b)
    return m + np.log(np.exp(np.clip((a - m) / k, -20.0, 0.0)) + np.exp(np.clip((b - m) / k, -20.0, 0.0))) * k


def _draw_unified_forearm_palm(
    skin_tex: np.ndarray,
    wrist_xy: tuple[float, float],
    elbow_xy: tuple[float, float],
    palm_top_xy: tuple[float, float],
    palm_bot_xy: tuple[float, float],
    thenar_xy: tuple[float, float],
    web_xy: tuple[float, float],
    r_wrist: float = 82.0,
    r_elbow: float = 120.0,
    squeeze: float = 0.0,
) -> np.ndarray:
    """Twist-free SDF union of forearm, ulnar wrist bump, contoured MCP palm bridge,
    thenar muscle, thumb-index web bridge, dorsal tendons, and curved ERIC wristband."""
    wx, wy = wrist_xy
    ex, ey = elbow_xy
    dx, dy = ex - wx, ey - wy
    ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / ln, dy / ln
    px, py = -uy, ux
    if py > 0:
        px, py = -px, -py

    palm_xy = ((palm_top_xy[0] + palm_bot_xy[0]) * 0.5, (palm_top_xy[1] + palm_bot_xy[1]) * 0.5)
    x0 = max(0, int(math.floor(min(wx, palm_top_xy[0], palm_bot_xy[0], thenar_xy[0], web_xy[0]) - 150.0)))
    y0 = max(0, int(math.floor(min(wy, palm_top_xy[1], palm_bot_xy[1], thenar_xy[1], web_xy[1]) - 150.0)))
    out_full = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.float32)
    if x0 >= STAGE_W or y0 >= STAGE_H:
        return out_full
    yg, xg = np.mgrid[y0:STAGE_H, x0:STAGE_W].astype(np.float32)

    sdf_arm = _seg_sdf(xg, yg, (wx, wy), (ex, ey), r_wrist, r_elbow)
    sdf_palm_t = _seg_sdf(xg, yg, (wx, wy), palm_top_xy, r_wrist * 0.90, 52.0)
    sdf_palm_b = _seg_sdf(xg, yg, (wx, wy), palm_bot_xy, r_wrist * 0.88, 46.0)
    sdf_mcp = _seg_sdf(xg, yg, palm_top_xy, palm_bot_xy, 48.0, 42.0)
    sdf_thenar = _seg_sdf(xg, yg, (wx + px * 16.0, wy + py * 16.0), thenar_xy, 58.0, 46.0)
    sdf_web = _seg_sdf(xg, yg, thenar_xy, web_xy, 40.0, 30.0)

    sdf = _smax(_smax(_smax(_smax(_smax(sdf_arm, sdf_palm_t, 16.0), sdf_palm_b, 16.0), sdf_mcp, 14.0), sdf_thenar, 18.0), sdf_web, 16.0)
    alpha = np.clip((sdf + 1.2) / 2.4, 0.0, 1.0)

    rx, ry = xg - wx, yg - wy
    s = rx * ux + ry * uy
    lat = rx * px + ry * py
    half_w = r_wrist * (1.0 - np.clip(s / ln, 0.0, 1.0)) + r_elbow * np.clip(s / ln, 0.0, 1.0)
    v_norm = np.clip(lat / np.maximum(half_w, 1.0), -1.0, 1.0)
    cyl = np.sqrt(np.clip(1.0 - v_norm * v_norm, 0.0, 1.0))

    tex_x = np.mod(xg, skin_tex.shape[1]).astype(np.int32)
    tex_y = np.mod(yg, skin_tex.shape[0]).astype(np.int32)
    rgb = skin_tex[tex_y, tex_x].copy()

    # Subcutaneous veins, ulnar wrist bone highlight, & raised dorsal extensor tendons
    vein1 = np.exp(-((lat - 16.0 - 11.0 * np.sin(s * 0.015)) / 5.5) ** 2) * (s > -20)
    vein2 = np.exp(-((lat + 18.0 + 7.0 * np.cos(s * 0.018)) / 4.5) ** 2) * (s > 10)
    rgb[..., 0] -= (vein1 + vein2) * 13.0
    rgb[..., 1] -= (vein1 + vein2) * 5.0
    rgb[..., 2] += (vein1 + vein2) * 6.0

    ulna_bump = np.exp(-(((s - 18.0) / 26.0) ** 2 + ((lat + half_w * 0.62) / 24.0) ** 2))
    tendon_ridge = (
        np.exp(-((lat - 14.0) / 6.0) ** 2) + 0.8 * np.exp(-((lat + 10.0) / 5.5) ** 2)
    ) * np.exp(-((s + 38.0) / 52.0) ** 2)

    light = 0.50 + 0.52 * cyl + 0.20 * v_norm + 0.14 * ulna_bump + 0.10 * tendon_ridge
    pcx, pcy = palm_xy
    in_hand = np.clip((-s + 30.0) / 110.0, 0.0, 1.0)
    hand_dome = np.exp(-(((xg - pcx) / 135.0) ** 2 + ((yg - pcy) / 125.0) ** 2))
    light = light * (1.0 - 0.35 * in_hand) + (0.62 + 0.42 * hand_dome) * (0.35 * in_hand)

    if squeeze > 0.05:
        kb = np.exp(-(((xg - pcx) / 58.0) ** 2 + ((yg - pcy) / 58.0) ** 2))
        bl = squeeze * (kb + 0.5 * tendon_ridge)
        bl = np.clip(bl, 0.0, 1.0)
        rgb = rgb * (1.0 - 0.36 * bl)[..., None] + np.array([244.0, 222.0, 204.0]) * (0.36 * bl)[..., None]

    rgb *= light[..., None]

    # Curved yellow "ERIC" hospital wristband with soft cast shadows on skin
    band_s0, band_s1 = 48.0, 118.0
    in_band = (s >= band_s0) & (s <= band_s1) & (alpha > 0.15)
    band_shadow = np.exp(-((np.maximum(0.0, np.maximum(band_s0 - s, s - band_s1))) / 9.0) ** 2)
    rgb *= (1.0 - 0.32 * band_shadow * (~in_band))[..., None]

    band_lit = 0.54 + 0.52 * cyl + 0.18 * v_norm + 0.22 * (cyl ** 10.0)
    band_rgb = np.zeros_like(rgb)
    band_rgb[..., 0] = 248.0
    band_rgb[..., 1] = 212.0
    band_rgb[..., 2] = 36.0
    band_rgb *= band_lit[..., None]

    bs_mid = 0.5 * (band_s0 + band_s1)
    ds_b = s - bs_mid
    dv_b = (v_norm - 0.05) * half_w
    in_cross = ((np.abs(ds_b) < 16.0) & (np.abs(dv_b) < 5.5)) | ((np.abs(ds_b) < 5.5) & (np.abs(dv_b) < 16.0))
    band_rgb = np.where(in_cross[..., None], np.array([208.0, 22.0, 32.0]) * band_lit[..., None], band_rgb)

    eric_u = np.clip((dv_b + 74.0) / 58.0 * 159.0, 0, 159).astype(np.int32)
    eric_v = np.clip((ds_b + 18.0) / 36.0 * 43.0, 0, 43).astype(np.int32)
    in_eric_box = (dv_b > -74.0) & (dv_b < -16.0) & (np.abs(ds_b) < 18.0)
    eric_m = np.where(in_eric_box, _ERIC_STAMP[eric_v, eric_u], 0.0)
    band_rgb = band_rgb * (1.0 - eric_m * 0.88)[..., None] + (np.array([24.0, 22.0, 26.0]) * band_lit[..., None]) * (eric_m * 0.88)[..., None]

    for b_pos in (24.0, 31.0, 37.0, 44.0, 50.0):
        in_bar = (np.abs(dv_b - b_pos) < 2.2) & (np.abs(ds_b) < 17.0)
        band_rgb = np.where(in_bar[..., None], np.array([34.0, 32.0, 36.0]) * band_lit[..., None], band_rgb)
    band_edge = (np.abs(s - band_s0) < 2.5) | (np.abs(s - band_s1) < 2.5)
    band_rgb = np.where(band_edge[..., None], band_rgb * 0.56, band_rgb)
    rgb = np.where(in_band[..., None], band_rgb, rgb)

    rgba = np.dstack([
        np.clip(np.round(rgb), 0, 255).astype(np.uint8),
        np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8),
    ])
    pm = _premul_from_rgba(rgba)

    # Gradual organic forearm & dorsal hand hairs (starting softly around wrist, not abrupt cutoff!)
    hair_im = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hair_im)
    rng = np.random.default_rng(909)
    for _ in range(210):
        st = rng.uniform(22.0, ln * 0.92)
        lv = rng.uniform(-0.78, 0.82)
        hw = r_wrist * (1.0 - st / ln) + r_elbow * (st / ln)
        hx = wx + ux * st + px * (lv * hw * 0.88)
        hy = wy + uy * st + py * (lv * hw * 0.88)
        hlen = rng.uniform(9.0, 20.0)
        ang_w = rng.uniform(-0.24, 0.34)
        mx = hx + (ux * math.cos(ang_w) + px * math.sin(ang_w)) * (hlen * 0.55) + px * 2.0
        my = hy + (uy * math.cos(ang_w) + py * math.sin(ang_w)) * (hlen * 0.55) + py * 2.0
        tx = hx + (ux * math.cos(ang_w + 0.18) + px * math.sin(ang_w + 0.18)) * hlen
        ty = hy + (uy * math.cos(ang_w + 0.18) + py * math.sin(ang_w + 0.18)) * hlen
        fade = min(1.0, max(0.25, (st - 22.0) / 140.0))
        dh.line([(hx, hy), (mx, my), (tx, ty)], fill=(64, 38, 22, int(rng.uniform(24, 54) * fade)), width=2)
    hair_pm = _premul_from_rgba(np.asarray(hair_im, dtype=np.uint8))[y0:STAGE_H, x0:STAGE_W]
    skin_only = np.where((alpha > 0.4) & (~in_band), alpha, 0.0)[..., None]
    out_full[y0:STAGE_H, x0:STAGE_W] = _over_premul(pm, hair_pm * skin_only)
    return out_full


# ---------------------------------------------------------------------------
# Pressurized CO2 Mist / Rim Splash / Squirt Streaks / Yeet Arcs
# ---------------------------------------------------------------------------
def _draw_liquid_fx(
    mouth_xy: tuple[float, float],
    mode: str,
    strength: float,
    phase: float,
    rng: np.random.Generator,
) -> np.ndarray:
    fx = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fx)
    mx, my = mouth_xy

    if mode == "fizz" and strength > 0.02:
        # Bold pressurized CO2 mist plume + high-velocity neon spray streaks
        mist = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        dm = ImageDraw.Draw(mist)
        for _ in range(int(64 * strength)):
            ang = rng.uniform(-2.15, -0.98)
            dist = rng.uniform(8.0, max(18.0, 310.0 * strength))
            bx = mx + math.cos(ang) * dist
            by = my + math.sin(ang) * dist
            rad = rng.uniform(14.0, 38.0) * (0.60 + 0.60 * dist / 310.0)
            col = (255, 228, 244, int(115 * strength)) if rng.random() < 0.6 else (185, 255, 200, int(98 * strength))
            dm.ellipse((bx - rad, by - rad, bx + rad, by + rad), fill=col)
        mist = mist.filter(ImageFilter.GaussianBlur(9.0))
        fx.alpha_composite(mist)

        for _ in range(int(80 * strength)):
            ang = rng.uniform(-2.12, -1.02)
            d0 = rng.uniform(6.0, max(14.0, 220.0 * strength))
            d1 = d0 + rng.uniform(22.0, max(28.0, 82.0 * strength))
            x0, y0 = mx + math.cos(ang) * d0, my + math.sin(ang) * d0
            x1, y1 = mx + math.cos(ang) * d1, my + math.sin(ang) * d1
            col = (255, 58, 152, int(225 * strength)) if rng.random() < 0.55 else (86, 255, 114, int(215 * strength))
            d.line([(x0, y0), (x1, y1)], fill=col, width=int(rng.uniform(2, 5)))

    elif mode == "chug_mouth" and strength > 0.02:
        # Messy frothy mouth-rim splash right at lower-center mouth (NOT pouring onto distant street!)
        foam = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        df = ImageDraw.Draw(foam)
        for _ in range(38):
            fx_p = mx + rng.uniform(-58.0, 58.0)
            fy_p = my + rng.uniform(-18.0, 52.0)
            fr = rng.uniform(9.0, 24.0)
            col = (255, 82, 162, int(155 * strength)) if rng.random() < 0.55 else (104, 252, 128, int(145 * strength))
            df.ellipse((fx_p - fr, fy_p - fr, fx_p + fr, fy_p + fr), fill=col)
        foam = foam.filter(ImageFilter.GaussianBlur(5.0))
        fx.alpha_composite(foam)

        for _ in range(int(48 * strength)):
            ang = rng.uniform(0.10, math.pi - 0.10)
            d0 = rng.uniform(8.0, max(14.0, 108.0 * strength))
            d1 = d0 + rng.uniform(16.0, 52.0)
            x0, y0 = mx + math.cos(ang) * d0, my + math.sin(ang) * d0
            x1, y1 = mx + math.cos(ang) * d1, my + math.sin(ang) * d1
            col = (255, 58, 150, int(205 * strength)) if rng.random() < 0.55 else (82, 252, 108, int(195 * strength))
            d.line([(x0, y0), (x1, y1)], fill=col, width=int(rng.uniform(2, 4)))

    elif mode == "squirt" and strength > 0.02:
        # Sharp directional foam jet & mist streaks squirted out when crushing the aluminum can
        mist = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
        dm = ImageDraw.Draw(mist)
        for _ in range(int(24 * strength)):
            ang = rng.uniform(-2.45, -1.55)
            dist = rng.uniform(12.0, max(20.0, 220.0 * strength))
            bx = mx + math.cos(ang) * dist
            by = my + math.sin(ang) * dist + 0.0018 * dist * dist
            rad = rng.uniform(10.0, 22.0)
            dm.ellipse((bx - rad, by - rad, bx + rad, by + rad), fill=(255, 225, 240, int(85 * strength)))
        mist = mist.filter(ImageFilter.GaussianBlur(6.0))
        fx.alpha_composite(mist)

        for _ in range(int(48 * strength)):
            ang = rng.uniform(-2.42, -1.52)
            d0 = rng.uniform(8.0, max(16.0, 175.0 * strength))
            d1 = d0 + rng.uniform(18.0, 56.0)
            x0, y0 = mx + math.cos(ang) * d0, my + math.sin(ang) * d0 + 0.0018 * d0 * d0
            x1, y1 = mx + math.cos(ang) * d1, my + math.sin(ang) * d1 + 0.0018 * d1 * d1
            col = (255, 68, 154, int(205 * strength)) if rng.random() < 0.5 else (92, 255, 116, int(195 * strength))
            d.line([(x0, y0), (x1, y1)], fill=col, width=3)

    return _premul_from_rgba(np.asarray(fx, dtype=np.uint8))


def _draw_yeet_arcs(pm: np.ndarray, whip_strength: float, whip_prog: float) -> np.ndarray:
    if whip_strength <= 0.02:
        return pm
    fx = Image.new("RGBA", (STAGE_W, STAGE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fx)
    for k_arc, (off_x, off_y, width_px, col) in enumerate([
        (0.0, 0.0, 14, (255, 195, 232)),
        (24.0, 32.0, 9, (145, 255, 170)),
    ]):
        u0 = max(0.0, whip_prog - 0.40)
        u1 = min(1.0, whip_prog + 0.16)
        if u1 - u0 < 0.08:
            continue
        pts = []
        for s_i in range(16):
            u = u0 + (u1 - u0) * (s_i / 15.0)
            p0 = (910.0 + off_x, 360.0 + off_y)
            p1 = (490.0 + off_x, 420.0 + off_y)
            p2 = (80.0 + off_x, 760.0 + off_y)
            bx = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u ** 2 * p2[0]
            by = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u ** 2 * p2[1]
            pts.append((bx, by))
        for i in range(len(pts) - 1):
            taper = math.sin(math.pi * (i + 0.5) / max(1, len(pts) - 1))
            a_val = int(round(135.0 * whip_strength * taper * (0.9 if k_arc == 0 else 0.55)))
            if a_val > 3:
                d.line([pts[i], pts[i + 1]], fill=(col[0], col[1], col[2], a_val), width=max(2, int(round(width_px * taper))))
    fx_blur = fx.filter(ImageFilter.GaussianBlur(3.2))
    return _over_premul(pm, _premul_from_rgba(np.asarray(fx_blur, dtype=np.uint8)))


# ---------------------------------------------------------------------------
# Continuous SLERP 36-Frame Animation Curve & Renderer
# ---------------------------------------------------------------------------
# Proper right-handed orientation keyframes (pitch, yaw, roll)
_R_START = _euler_to_mat(-20.0, -24.0, 16.0)
_R_HERO = _euler_to_mat(-16.0, -14.0, 10.0)
_R_TAB = _euler_to_mat(-28.0, -12.0, 8.0)
# 3/4 side-swing waypoint swinging left (-X) so tilt-in never stares down the lid barrel (#15..#17)
_R_TILT_MID = _euler_to_mat(-68.0, 44.0, -16.0)
_R_CHUG = _euler_to_mat(-114.0, 16.0, -6.0)
# Symmetric left-swing pull-down waypoint across w=0.76..0.84 (#28..#30)
_R_PULL_MID = _euler_to_mat(-66.0, 40.0, -18.0)
_R_CRUSH = _euler_to_mat(-18.0, -16.0, 14.0)
_R_COCK = _euler_to_mat(-22.0, -20.0, 20.0)

_RH_START = _euler_to_mat(-18.0, -18.0, 14.0)
_RH_HERO = _euler_to_mat(-14.0, -10.0, 10.0)
_RH_TILT_MID = _euler_to_mat(-42.0, 22.0, -10.0)
_RH_CHUG = _euler_to_mat(-64.0, 8.0, -26.0)
_RH_PULL_MID = _euler_to_mat(-40.0, 20.0, -12.0)
_RH_CRUSH = _euler_to_mat(-16.0, -12.0, 12.0)
_RH_YEET = _euler_to_mat(-24.0, -8.0, 34.0)


def _eval_drink_curve(w: float) -> dict:
    """Evaluates continuous SLERP pose state at w in [0, 1] over 2.85s."""
    w = max(0.0, min(1.0, w))

    c_start = (0.88, -1.62, 4.42)
    c_hero = (0.34, -0.26, 3.88)
    c_tab = (0.28, -0.44, 3.82)
    c_chug = (0.48, 0.04, 3.34)
    c_crush = (0.24, -0.28, 3.80)

    if w < 0.18:
        u = _sstep(0.0, 0.18, w)
        center = _lerp3(c_start, c_hero, u)
        R_can = _slerp_mat(_R_START, _R_HERO, u)
        R_hand = _slerp_mat(_RH_START, _RH_HERO, u)
        hype = max(0.0, (w - 0.12) / 0.06)
        shake = math.sin(hype * math.pi * 2.5) * 0.03 * hype
        center = (center[0] + shake, center[1] + abs(shake) * 0.4, center[2])
        return dict(
            center=center, R_can=R_can, R_hand=R_hand,
            tab_open=0.0, crush=0.0, grip_y=-0.22, thumb_to_tab=0.0, thumb_flick=0.0,
            open_hand=0.0, can_detach=(0.0, 0.0, 0.0), hand_drop=(0.0, 0.0),
            liquid_mode="none", liquid_strength=0.0, liquid_phase=w, whip_strength=0.0, whip_prog=0.0,
        )

    elif w < 0.37:
        u_slide = _sstep(0.18, 0.25, w)
        u_down = _sstep(0.31, 0.37, w)
        slide_amt = u_slide * (1.0 - u_down)

        dip = math.sin(_sstep(0.20, 0.255, w) * math.pi) * 0.05
        # Tab-pop recoil across w=0.252..0.31 so #10->#11 never holds static
        recoil = 0.0
        if w >= 0.252:
            pr = min(1.0, (w - 0.252) / 0.058)
            recoil = math.sin(pr * math.pi) * 0.055
        center = _lerp3(c_hero, c_tab, slide_amt)
        center = (center[0] + recoil * 0.35, center[1] - dip - recoil, center[2] + recoil * 0.4)
        R_can = _slerp_mat(_R_HERO, _R_TAB, slide_amt)
        if recoil > 0.002:
            R_can = _slerp_mat(R_can, _euler_to_mat(-33.0, -10.0, 11.0), recoil * 10.0)
        R_hand = _RH_HERO

        if w >= 0.252:
            p = (w - 0.252) / 0.105
            spring = 1.0 - math.exp(-p * 5.0) * math.cos(p * 11.0)
            tab_open = max(0.0, min(1.0, spring))
            flick = max(0.0, math.exp(-p * 5.5) * math.sin(p * 12.0))
        else:
            tab_open = 0.0
            flick = -0.30 * _sstep(0.21, 0.252, w)

        fizz_str = 0.0
        if 0.252 <= w <= 0.365:
            fizz_str = math.sin(((w - 0.252) / 0.113) * math.pi) ** 0.7

        return dict(
            center=center, R_can=R_can, R_hand=R_hand,
            tab_open=tab_open, crush=0.0, grip_y=_lerp(-0.22, 0.72, slide_amt),
            thumb_to_tab=slide_amt, thumb_flick=flick,
            open_hand=0.0, can_detach=(0.0, 0.0, 0.0), hand_drop=(0.0, 0.0),
            liquid_mode="fizz" if fizz_str > 0.02 else "none",
            liquid_strength=fizz_str, liquid_phase=w, whip_strength=0.0, whip_prog=0.0,
        )

    elif w < 0.76:
        # Smooth quadratic Bezier SLERP tilt-in (0.37..0.47) -> smooth chug (0.47..0.76)
        tilt_p = _sstep(0.37, 0.47, w)
        R_can = _slerp_quad(_R_HERO, _R_TILT_MID, _R_CHUG, tilt_p)
        R_hand = _slerp_quad(_RH_HERO, _RH_TILT_MID, _RH_CHUG, tilt_p)
        center = _lerp3(c_hero, c_chug, tilt_p)

        pour_str = _sstep(0.43, 0.50, w) * _sstep(0.76, 0.72, w)
        if w >= 0.47:
            cw = (w - 0.47) / 0.29
            env = math.sin(math.pi * cw) ** 0.65
            gulp = (math.sin(cw * math.pi * 4.0) * 0.5 + 0.5) * env
            tremor_x = math.sin(cw * math.pi * 12.0) * 0.010 * env
            tremor_y = math.cos(cw * math.pi * 10.0) * 0.012 * env
            center = (center[0] + tremor_x, center[1] - 0.04 * gulp + tremor_y, center[2] - 0.06 * gulp)
            R_can = _slerp_mat(R_can, _euler_to_mat(-124.0, 16.0, -8.0), 0.30 * gulp)
            R_hand = _slerp_mat(R_hand, _euler_to_mat(-68.0, 8.0, -28.0), 0.30 * gulp)
            pour_str = (0.70 + 0.35 * gulp) * env

        return dict(
            center=center, R_can=R_can, R_hand=R_hand,
            tab_open=1.0, crush=0.0, grip_y=_lerp(-0.22, -0.14, tilt_p),
            thumb_to_tab=0.0, thumb_flick=0.0,
            open_hand=0.0, can_detach=(0.0, 0.0, 0.0), hand_drop=(0.0, 0.0),
            liquid_mode="chug_mouth" if pour_str > 0.02 else "none",
            liquid_strength=min(1.0, pour_str), liquid_phase=w, whip_strength=0.0, whip_prog=0.0,
        )

    elif w < 0.90:
        # Smooth quadratic Bezier SLERP pull-down arc across w=0.76..0.84 -> Crush + cock-back on #33
        pull_p = _sstep(0.76, 0.84, w)
        R_can = _slerp_quad(_R_CHUG, _R_PULL_MID, _R_CRUSH, pull_p)
        R_hand = _slerp_quad(_RH_CHUG, _RH_PULL_MID, _RH_CRUSH, pull_p)
        center = _lerp3(c_chug, c_crush, pull_p)

        crush = _sstep(0.815, 0.875, w) * 0.96
        crush_env = math.sin(_sstep(0.82, 0.895, w) * math.pi)
        if crush_env > 0.02:
            vib = math.sin((w - 0.82) * 110.0) * 0.012 * crush_env
            center = (center[0] + vib, center[1] - 0.03 * crush_env, center[2])

        # Cock-back anticipation right before yeet (#32 -> #33)
        cock = _sstep(0.87, 0.90, w)
        if cock > 0.005:
            center = (center[0] + 0.09 * cock, center[1] + 0.04 * cock, center[2] + 0.08 * cock)
            R_can = _slerp_mat(R_can, _R_COCK, cock)
            R_hand = _slerp_mat(R_hand, _R_COCK, cock)

        squirt_str = 0.0
        if 0.825 <= w <= 0.895:
            squirt_str = math.sin(((w - 0.825) / 0.070) * math.pi) ** 0.70

        return dict(
            center=center, R_can=R_can, R_hand=R_hand,
            tab_open=1.0, crush=crush, grip_y=-0.14, thumb_to_tab=0.0, thumb_flick=0.0,
            open_hand=0.0, can_detach=(0.0, 0.0, 0.0), hand_drop=(0.0, 0.0),
            liquid_mode="squirt" if squirt_str > 0.02 else "none",
            liquid_strength=squirt_str, liquid_phase=w, whip_strength=0.0, whip_prog=0.0,
        )

    else:
        u = (w - 0.90) / 0.10
        whip = u * u * (2.1 - 1.1 * u)
        c_cock = (c_crush[0] + 0.09, c_crush[1] + 0.04, c_crush[2] + 0.08)
        center = _lerp3(c_cock, (-0.02, -0.46, 3.74), whip)
        R_hand = _slerp_mat(_R_COCK, _RH_YEET, whip)

        open_h = _sstep(0.14, 0.50, u)
        fly = max(0.0, (u - 0.22) / 0.78)
        R_can = _slerp_mat(_R_COCK, _euler_to_mat(-165.0, -35.0, 68.0), min(1.0, fly * 1.15))
        detach = (-2.95 * (fly ** 1.08), -0.45 * fly + 0.35 * math.sin(fly * math.pi), 4.40 * (fly ** 1.15)) if fly > 0.0 else (0.0, 0.0, 0.0)
        drop = (185.0 * _sstep(0.58, 1.0, u), 350.0 * _sstep(0.58, 1.0, u))
        whip_str = math.sin(min(1.0, u / 0.85) * math.pi) if u < 0.85 else 0.0

        return dict(
            center=center, R_can=R_can, R_hand=R_hand,
            tab_open=1.0, crush=0.96, grip_y=-0.14, thumb_to_tab=0.0, thumb_flick=0.0,
            open_hand=open_h, can_detach=detach, hand_drop=drop,
            liquid_mode="none", liquid_strength=0.0, liquid_phase=w,
            whip_strength=whip_str, whip_prog=min(1.0, u * 1.15),
        )


def _render_single_state(
    label_tex: np.ndarray,
    cond_map: np.ndarray,
    skin_tex: np.ndarray,
    state: dict,
    rng_seed: int,
) -> np.ndarray:
    R_can = state["R_can"]
    R_hand = state["R_hand"]
    open_h = state["open_hand"]
    # Lock gripping fingers/thumb/palm directly to R_can when closed (open_h == 0),
    # blending smoothly into R_hand follow-through as hand opens during yeet!
    R_grip = _slerp_mat(R_can, R_hand, open_h)

    C_hand = np.array(state["center"], dtype=np.float32)
    C_can = C_hand + np.array(state["can_detach"], dtype=np.float32)
    focal = 1080.0
    dx_drop, dy_drop = state["hand_drop"]

    def proj_grip(p_loc: tuple[float, float, float]) -> tuple[float, float, float]:
        pw = R_grip @ np.array(p_loc, dtype=np.float32) + C_hand
        z = max(0.25, float(pw[2]))
        return (STAGE_W * 0.5 + focal * float(pw[0]) / z + dx_drop, STAGE_H * 0.5 - focal * float(pw[1]) / z + dy_drop, z)

    def proj_arm(p_loc: tuple[float, float, float]) -> tuple[float, float, float]:
        pw = R_hand @ np.array(p_loc, dtype=np.float32) + C_hand
        z = max(0.25, float(pw[2]))
        return (STAGE_W * 0.5 + focal * float(pw[0]) / z + dx_drop, STAGE_H * 0.5 - focal * float(pw[1]) / z + dy_drop, z)

    can_pm, anc = _render_can_3d(
        label_tex, cond_map, tuple(C_can), R_can,
        tab_open=state["tab_open"], crush=state["crush"], focal=focal,
    )
    gy = state["grip_y"]
    crush = state["crush"]

    gx_s, gy_s, _ = proj_grip((0.46, gy, 0.0))
    wx, wy, _ = proj_arm((0.92, gy - 0.36, 0.14))
    wx = max(wx, gx_s + 120.0)
    wy = max(wy, gy_s + 115.0)
    ex = max(STAGE_W + 240.0, wx + 460.0)
    ey = max(STAGE_H + 240.0, wy + 520.0)

    # Contoured MCP palm bridge spanning Index..Pinky knuckle bases + thenar/web
    palm_top_xy = proj_grip((0.48 + open_h * 0.04, gy + 0.16, 0.08))[:2]
    palm_bot_xy = proj_grip((0.46 + open_h * 0.04, gy - 0.22, 0.08))[:2]
    thenar_xy = proj_grip((0.56, gy - 0.01, -0.08))[:2]
    web_xy = proj_grip((0.28, gy + 0.14, -0.22))[:2]

    stage = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.float32)
    arm_pm = _draw_unified_forearm_palm(
        skin_tex, (wx, wy), (ex, ey), palm_top_xy, palm_bot_xy, thenar_xy, web_xy, squeeze=crush
    )
    stage = _over_premul(stage, arm_pm)

    can_layer = can_pm.copy()
    finger_layers = []
    shad_total = np.zeros((STAGE_H, STAGE_W), dtype=np.float32)

    finger_specs = [
        (0.27, 0.52, 35.0, 24.0, 0.00),
        (0.10, 0.57, 36.0, 25.0, 0.04),
        (-0.07, 0.50, 34.0, 23.0, 0.08),
        (-0.23, 0.40, 30.0, 21.0, 0.12),
    ]
    for f_i, (y_off, reach, rb, rt, ao) in enumerate(finger_specs):
        rc = 0.50 - crush * 0.13
        th0, th1 = math.radians(-118.0), math.radians(-92.0)
        th2 = math.radians(-92.0 + reach * 68.0)
        th3 = math.radians(-92.0 + reach * 104.0)
        g_pts = [
            (rc * math.sin(th0), gy + y_off, -rc * math.cos(th0)),
            (rc * math.sin(th1), gy + y_off + 0.02, -rc * math.cos(th1)),
            (rc * math.sin(th2), gy + y_off + 0.01, -rc * math.cos(th2)),
            (rc * math.sin(th3), gy + y_off - 0.01, -rc * math.cos(th3)),
        ]
        if open_h > 0.01:
            curl_f = 0.25 + f_i * 0.18
            splay = (1.5 - f_i) * 0.11 * open_h
            o_pts = [
                (0.42, gy + y_off, 0.04),
                (0.10, gy + y_off + splay * 0.5, -0.28),
                (-0.22 + curl_f * 0.10, gy + y_off + splay * 0.9 - curl_f * 0.08, -0.44 + curl_f * 0.12),
                (-0.42 + curl_f * 0.24, gy + y_off + splay * 1.1 - curl_f * 0.18, -0.46 + curl_f * 0.22),
            ]
            cpts = [proj_grip(_lerp3(gp, op, open_h))[:2] for gp, op in zip(g_pts, o_pts)]
        else:
            cpts = [proj_grip(gp)[:2] for gp in g_pts]

        f_pm, f_sh = _draw_articulated_digit(
            skin_tex, cpts, rb, rt, squeeze=crush * (1.0 - open_h), with_nail=True, nail_angle_bias=-0.22, ao_darken=ao
        )
        finger_layers.append(f_pm)
        shad_total = np.maximum(shad_total, f_sh)

    # Seamless thumb base (tp0 tucked inside thenar pad + root_fade=True)
    tt = state["thumb_to_tab"]
    tf = state["thumb_flick"]
    tp0 = proj_grip((0.56, gy - 0.01, -0.08))[:2]
    tp1 = proj_grip((0.38 - 0.04 * tt - open_h * 0.02, gy + 0.08 + 0.16 * tt + open_h * 0.14, -0.34 + 0.08 * tt))[:2]
    tp2 = proj_grip((0.22 + 0.02 * tt - open_h * 0.08, gy + 0.14 + 0.34 * tt + tf * 0.09 + open_h * 0.28, -0.45 + 0.32 * tt))[:2]
    tp3 = proj_grip((0.06 + 0.08 * tt - open_h * 0.14, gy + 0.18 + 0.48 * tt + tf * 0.16 + open_h * 0.38, -0.48 + 0.52 * tt))[:2]
    thumb_pm, t_sh = _draw_articulated_digit(
        skin_tex, [tp0, tp1, tp2, tp3], 42.0, 30.0, squeeze=crush * (1.0 - open_h), with_nail=True, nail_angle_bias=-0.18, root_fade=True
    )
    shad_total = np.maximum(shad_total, t_sh)

    ao_fade = max(0.0, 1.0 - open_h * 3.0)
    if ao_fade > 0.01:
        can_layer[..., :3] *= (1.0 - shad_total[..., None] * 0.65 * ao_fade)

    if open_h > 0.25:
        for f_pm in finger_layers:
            stage = _over_premul(stage, f_pm)
        stage = _over_premul(stage, can_layer)
        stage = _over_premul(stage, thumb_pm)
    else:
        stage = _over_premul(stage, can_layer)
        if state["liquid_mode"] != "none":
            rng_l = np.random.default_rng(rng_seed)
            liq_pm = _draw_liquid_fx(anc["drink_hole"][:2], state["liquid_mode"], state["liquid_strength"], state["liquid_phase"], rng_l)
            stage = _over_premul(stage, liq_pm)
        for f_pm in finger_layers:
            stage = _over_premul(stage, f_pm)
        stage = _over_premul(stage, thumb_pm)

    if state["whip_strength"] > 0.02:
        stage = _draw_yeet_arcs(stage, state["whip_strength"], state["whip_prog"])
    return stage


def build_viewmodel_sprites(gfx_dir: Path, assets_dir: Path) -> None:
    """Writes 36 smoothly eased 640x480 RGBA frames vm_01.png..vm_36.png into gfx/foreloco/."""
    gfx_dir.mkdir(parents=True, exist_ok=True)
    for old in gfx_dir.glob("vm_*.png"):
        old.unlink()

    label_tex, cond_map = _build_unwrapped_label(assets_dir)
    skin_tex = _make_skin_texture(seed=2026)
    dw = 1.0 / NUM_VM_FRAMES

    for i in range(NUM_VM_FRAMES):
        fr = i + 1
        w_mid = (i + 0.5) * dw

        if w_mid >= 0.898:
            # 16-tap Gaussian shutter blur (~0.44*dw) for completely silky yeet streaks
            n_taps = 16
            shutter = 0.44 * dw
            offs = np.linspace(-0.5, 0.5, n_taps)
            weights = np.exp(-0.5 * (offs / 0.28) ** 2)
            weights /= weights.sum()
            acc = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.float32)
            for t_idx, (off, wt) in enumerate(zip(offs, weights)):
                wt_w = max(0.0, min(1.0, w_mid + float(off) * shutter))
                st = _eval_drink_curve(wt_w)
                acc += _render_single_state(label_tex, cond_map, skin_tex, st, 700 + i * 17 + t_idx) * float(wt)
            out_rgba = _downsample_2x(acc)
        elif (0.37 <= w_mid <= 0.47) or (0.765 <= w_mid <= 0.835):
            # 5-tap subtle motion blur on fast tilt-in and pull-down turns
            n_taps = 5
            shutter = 0.28 * dw
            offs = np.linspace(-0.5, 0.5, n_taps)
            weights = np.exp(-0.5 * (offs / 0.30) ** 2)
            weights /= weights.sum()
            acc = np.zeros((STAGE_H, STAGE_W, 4), dtype=np.float32)
            for t_idx, (off, wt) in enumerate(zip(offs, weights)):
                wt_w = max(0.0, min(1.0, w_mid + float(off) * shutter))
                st = _eval_drink_curve(wt_w)
                acc += _render_single_state(label_tex, cond_map, skin_tex, st, 700 + i * 17 + t_idx) * float(wt)
            out_rgba = _downsample_2x(acc)
        else:
            st = _eval_drink_curve(w_mid)
            stage = _render_single_state(label_tex, cond_map, skin_tex, st, 700 + i * 17)
            out_rgba = _downsample_2x(stage)

        Image.fromarray(out_rgba, "RGBA").save(gfx_dir / f"vm_{fr:02d}.png", optimize=True)


# ---------------------------------------------------------------------------
# Edge-Framed Organic Liquid Pour & Vision Smear Overlays (640x360 RGBA)
# ---------------------------------------------------------------------------
def _draw_wavy_ribbon(
    draw: ImageDraw.ImageDraw,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    w0: float,
    w1: float,
    amp: float,
    phase: float,
    col: tuple[int, int, int, int],
) -> None:
    steps = 16
    left_pts, right_pts = [], []
    for s in range(steps + 1):
        t = s / steps
        cy = y0 + (y1 - y0) * t
        cx = x0 + (x1 - x0) * t + math.sin(t * 7.5 + phase) * amp * t
        w = w0 + (w1 - w0) * t + math.sin(t * 11.0 + phase * 1.7) * 2.0
        left_pts.append((cx - w * 0.5, cy))
        right_pts.append((cx + w * 0.5, cy))
    draw.polygon(left_pts + list(reversed(right_pts)), fill=col)


def _draw_smear_swipe(
    draw: ImageDraw.ImageDraw,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    radius: float,
    col: tuple[int, int, int, int],
) -> None:
    steps = 18
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t + math.sin(t * math.pi) * 18.0
        y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * 10.0
        r = radius * (0.40 + 0.60 * math.sin(t * math.pi))
        draw.ellipse((x - r, y - r * 0.72, x + r, y + r * 0.72), fill=col)


def _draw_refractive_droplet(
    d: ImageDraw.ImageDraw,
    bx: float,
    by: float,
    br: float,
    tint: tuple[int, int, int],
    alpha_body: int,
) -> None:
    """Clear glistening liquid bead with soft edge rim + bright specular crescent."""
    d.ellipse((bx - br * 1.06, by - br * 1.04, bx + br * 1.06, by + br * 1.12), fill=(18, 12, 18, int(alpha_body * 0.45)))
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=(tint[0], tint[1], tint[2], alpha_body))
    d.ellipse((bx - br * 0.65, by - br * 0.65, bx + br * 0.45, by + br * 0.45), fill=(255, 255, 255, int(alpha_body * 0.22)))
    d.ellipse((bx - br * 0.55, by - br * 0.60, bx - br * 0.05, by - br * 0.12), fill=(255, 255, 255, 215))


def _edge_xy(rng: np.random.Generator, margin_x: float = 155.0, margin_y: float = 82.0) -> tuple[float, float]:
    """Samples coordinates strictly in the outer border / corners so center ~55% sightline stays clear!"""
    zone = rng.integers(0, 4)
    if zone == 0:    # Left edge
        return rng.uniform(10.0, margin_x), rng.uniform(12.0, OV_H - 12.0)
    elif zone == 1:  # Right edge
        return rng.uniform(OV_W - margin_x, OV_W - 10.0), rng.uniform(12.0, OV_H - 12.0)
    elif zone == 2:  # Bottom rim
        return rng.uniform(60.0, OV_W - 60.0), rng.uniform(OV_H - margin_y, OV_H - 8.0)
    else:            # Top edge corners
        x = rng.uniform(10.0, 210.0) if rng.random() < 0.5 else rng.uniform(OV_W - 210.0, OV_W - 10.0)
        return x, rng.uniform(8.0, 68.0)


def build_smear_overlays(gfx_dir: Path) -> None:
    """Generates edge-framed translucent liquid pour & smears keeping center ~55% clear."""
    gfx_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7777)

    # 1. pour_stream.png: frothy lower-edge/corner splashes & side curtains (center crosshair clear!)
    pour = Image.new("RGBA", (OV_W, OV_H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(pour)
    for k in range(12):
        # Place ribbons along left/right outer thirds + bottom mouth splash zone
        side_x = rng.uniform(18.0, 148.0) if k < 6 else rng.uniform(OV_W - 148.0, OV_W - 18.0)
        w0 = rng.uniform(6, 13)
        w1 = w0 * rng.uniform(1.3, 2.0)
        y0 = rng.uniform(0.0, 80.0)
        y1 = OV_H + 15
        drift = rng.uniform(-22, 22)
        is_pink = (k % 2 == 0)
        col = (255, 36, 130, int(rng.uniform(75, 135))) if is_pink else (64, 244, 94, int(rng.uniform(70, 128)))
        _draw_wavy_ribbon(dp, side_x, y0, side_x + drift, y1, w0, w1, amp=9.0, phase=k * 1.3, col=col)
    pour = pour.filter(ImageFilter.GaussianBlur(radius=2.2))
    dp = ImageDraw.Draw(pour)
    for _ in range(75):
        bx, by = _edge_xy(rng, margin_x=170.0, margin_y=95.0)
        br = rng.uniform(2.0, 6.5)
        _draw_refractive_droplet(dp, bx, by, br, (255, 225, 242), 85)
    pour.save(gfx_dir / "pour_stream.png", optimize=True)

    # 2. smear_pink.png: organic edge/corner watermelon smears + clear refractive droplets
    pink = Image.new("RGBA", (OV_W, OV_H), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(pink)
    for _ in range(18):
        cx, cy = _edge_xy(rng, margin_x=145.0, margin_y=78.0)
        rw = rng.uniform(28, 76)
        rh = rng.uniform(14, 42)
        d1.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=(255, 34, 128, int(rng.uniform(62, 118))))
    for _ in range(10):
        x0, y0 = _edge_xy(rng, margin_x=135.0, margin_y=70.0)
        x1 = x0 + rng.uniform(-90, 90)
        y1 = y0 + rng.uniform(-50, 75)
        _draw_smear_swipe(d1, x0, y0, x1, y1, rng.uniform(16, 28), (255, 58, 148, int(rng.uniform(68, 115))))
    pink = pink.filter(ImageFilter.GaussianBlur(radius=7.5))
    d1 = ImageDraw.Draw(pink)
    for _ in range(68):
        bx, by = _edge_xy(rng, margin_x=165.0, margin_y=88.0)
        br = rng.uniform(2.2, 8.2)
        _draw_refractive_droplet(d1, bx, by, br, (255, 72, 156), 130)
    pink.save(gfx_dir / "smear_pink.png", optimize=True)

    # 3. smear_green.png: sour-watermelon green outer-border splashes + refractive droplets
    green = Image.new("RGBA", (OV_W, OV_H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(green)
    for _ in range(18):
        cx, cy = _edge_xy(rng, margin_x=145.0, margin_y=78.0)
        rw = rng.uniform(26, 72)
        rh = rng.uniform(14, 40)
        d2.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=(64, 246, 94, int(rng.uniform(58, 112))))
    for _ in range(10):
        x0, y0 = _edge_xy(rng, margin_x=135.0, margin_y=70.0)
        x1 = x0 + rng.uniform(-85, 85)
        y1 = y0 + rng.uniform(-45, 70)
        _draw_smear_swipe(d2, x0, y0, x1, y1, rng.uniform(14, 26), (92, 255, 118, int(rng.uniform(62, 110))))
    green = green.filter(ImageFilter.GaussianBlur(radius=7.5))
    d2 = ImageDraw.Draw(green)
    for _ in range(64):
        bx, by = _edge_xy(rng, margin_x=165.0, margin_y=88.0)
        br = rng.uniform(2.2, 7.8)
        _draw_refractive_droplet(d2, bx, by, br, (86, 252, 116), 125)
    green.save(gfx_dir / "smear_green.png", optimize=True)

    # 4. smear_drips.png: 8 irregular organic viscous edge drips (NO 26 jail bars!)
    drips = Image.new("RGBA", (OV_W, OV_H), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(drips)
    edge_xs = [18, 46, 82, 126, OV_W - 124, OV_W - 84, OV_W - 48, OV_W - 18]
    for k, base_x in enumerate(edge_xs):
        dx = base_x + rng.uniform(-8, 8)
        dlen = rng.uniform(65, 225)
        dw = rng.uniform(6, 13)
        col = (255, 42, 134, int(rng.uniform(115, 165))) if k % 2 == 0 else (72, 248, 98, int(rng.uniform(108, 155)))
        _draw_wavy_ribbon(d3, dx, -6, dx + rng.uniform(-12, 12), dlen, dw * 1.4, dw * 0.55, amp=4.5, phase=k * 1.7, col=col)
        d3.ellipse((dx - dw * 0.65, dlen - dw * 0.7, dx + dw * 0.65, dlen + dw * 0.65), fill=col)
        d3.ellipse((dx - dw * 0.25, dlen - dw * 0.35, dx + dw * 0.05, dlen - dw * 0.05), fill=(255, 255, 255, 190))
    drips = drips.filter(ImageFilter.GaussianBlur(radius=1.6))
    drips.save(gfx_dir / "smear_drips.png", optimize=True)
