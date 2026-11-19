"""Procedural 3D MD3 Builder & Texture Generator for Go-Kart Turtle Shell (`progs/gokart_shell.md3`).

Outputs:
  - progs/gokart_shell.md3             (16-frame 360-deg Z-spin MD3, 4 surfaces: carapace, rim, belly, cavity)
  - progs/gokart_shell.md3_0.skin       (Skin 0: Classic Green Shell)
  - progs/gokart_shell.md3_1.skin       (Skin 1: Red Homing-Style Shell)
  - progs/gokart_shell.md3_2.skin       (Skin 2: Blue / Cobalt Shell)
  - progs/gk_shell_green.png            (512x512 scute-aligned carapace texture)
  - progs/gk_shell_red.png              (512x512 scute-aligned carapace texture)
  - progs/gk_shell_blue.png             (512x512 scute-aligned carapace texture)
  - progs/gk_shell_trim.png             (512x512 shared rim, plastron belly & hollow cavity atlas)
  - source/mm_tools/out/gk_shell_meta.json

Coordinate system (Quake / DarkPlaces MD3 standard):
  +X = forward (head arch), +Y = left, +Z = up, ground contact plane at Z = 0.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_DIR = os.path.join(REPO_ROOT, "progs")
OUT_DIR = os.path.join(HERE, "out")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib
from mmw_geometry import MeshPart, rot_z, smoothstep, vadd, vcross, vdot, vnorm, vsub


# ---------------------------------------------------------------------------
# Shell Proportions & Constants (Quake units; go-kart is ~94u x 64u x 28u)
# ---------------------------------------------------------------------------
RX = 15.4
RY = 13.8
Z_PEAK = 16.4
N_THETA = 64
N_PHI = 22
N_FRAMES = 16

SKIN_VARIANTS = [
    (0, "green", "progs/gk_shell_green", "Classic Green Shell"),
    (1, "red",   "progs/gk_shell_red",   "Crimson Red Shell"),
    (2, "blue",  "progs/gk_shell_blue",  "Cobalt Blue Shell"),
]

# Trim atlas layout (512x512):
#   Top-left  (u in [0.04, 0.46], v in [0.04, 0.46]) -> Cream/ivory outer rim lip
#   Top-right (u in [0.54, 0.96], v in [0.04, 0.46]) -> Segmented ventral plastron belly
#   Bottom    (u in [0.04, 0.96], v in [0.54, 0.96]) -> Deep shadowed shell cavity lining
UV_TRIM_RIM = (0.04, 0.04, 0.46, 0.46)
UV_TRIM_BELLY = (0.54, 0.04, 0.96, 0.46)
UV_TRIM_CAVITY = (0.06, 0.56, 0.94, 0.94)


# ---------------------------------------------------------------------------
# Shared Scute Field (drives BOTH 3D dome relief AND 2D carapace textures)
# ---------------------------------------------------------------------------
# Classic turtle carapace layout in normalized dome coordinates (nx, ny):
#   - 3 large central hexagonal vertebral scutes along spine (ny = 0)
#   - 4 costal scutes on each flank (8 total)
#   - Outer marginal ring (r_norm > 0.77) split into 12 radial scutes
_SCUTE_CENTERS = [
    # Vertebral spine (slightly wider weighting along Y so central hexes look bold)
    (-0.46, 0.00, 0.92),
    ( 0.00, 0.00, 0.90),
    (+0.46, 0.00, 0.92),
    # Left & Right costal plates
    (-0.56, +0.49, 1.00),
    (-0.19, +0.52, 0.98),
    (+0.19, +0.52, 0.98),
    (+0.56, +0.49, 1.00),
    (-0.56, -0.49, 1.00),
    (-0.19, -0.52, 0.98),
    (+0.19, -0.52, 0.98),
    (+0.56, -0.49, 1.00),
]
_MARGINAL_R = 0.77


def eval_scute_field_np(nx, ny):
    """Vectorized scute SDF & plate ID on normalized dome coordinates (nx, ny).

    Returns:
      seam_dist : signed-like distance to nearest scute groove (>= 0; 0 right on groove)
      plate_val : normalized 0..1 depth inside the scute plate (0 at groove, 1 at scute dome center)
      cell_id   : integer scute ID (for subtle per-plate tint variation)
    """
    nx = np.asarray(nx, dtype=np.float32)
    ny = np.asarray(ny, dtype=np.float32)
    r = np.sqrt(nx * nx + ny * ny)
    ang = np.arctan2(ny, nx)

    # Organic wobble on Voronoi boundary so scutes look biological rather than rigid CAD
    wob = 0.014 * np.sin(ang * 5.0 + r * 4.0)

    d1 = np.full(nx.shape, 1e6, dtype=np.float32)
    d2 = np.full(nx.shape, 1e6, dtype=np.float32)
    cid = np.zeros(nx.shape, dtype=np.int32)

    for idx, (cx, cy, wt) in enumerate(_SCUTE_CENTERS):
        dx = (nx - cx) * wt
        dy = (ny - cy)
        dist = np.sqrt(dx * dx + dy * dy) + wob * 0.35
        m1 = dist < d1
        d2 = np.where(m1, d1, np.minimum(d2, dist))
        d1 = np.where(m1, dist, d1)
        cid = np.where(m1, idx + 1, cid)

    voronoi_edge = (d2 - d1) * 0.5

    # Outer marginal ring border + 12 radial marginal seams (offset by 15 deg so front/back have whole scutes)
    marg_ring_edge = np.abs(r - _MARGINAL_R + wob * 0.4)
    n_marg = 12.0
    ang_m = (ang + math.pi + math.pi / n_marg) % (2.0 * math.pi / n_marg)
    sector = np.floor(((ang + math.pi + math.pi / n_marg) % (2.0 * math.pi)) / (2.0 * math.pi / n_marg)).astype(np.int32)
    half_step = math.pi / n_marg
    radial_edge = np.abs(ang_m - half_step) * np.maximum(r, 0.35)

    in_marg = r > _MARGINAL_R
    seam_dist = np.where(in_marg, np.minimum(marg_ring_edge, radial_edge), np.minimum(voronoi_edge, marg_ring_edge))
    cid = np.where(in_marg, 20 + sector, cid)

    # Plate puff profile (smooth ramp from 0 at seam -> 1 across plate center)
    plate_val = np.clip((seam_dist - 0.018) / 0.14, 0.0, 1.0)
    plate_val = plate_val * plate_val * (3.0 - 2.0 * plate_val)
    return seam_dist, plate_val, cid


def eval_scute_height(nx, ny):
    """Scalar 3D radial/vertical displacement for one dome vertex in normalized coords."""
    sd, pv, _ = eval_scute_field_np(np.array([nx], dtype=np.float32), np.array([ny], dtype=np.float32))
    seam = float(sd[0])
    plate = float(pv[0])
    # Sharp groove right along seam, rounded raised pillow across scute face
    groove = math.exp(-(seam * seam) / 0.00055)
    return 0.50 * plate - 0.36 * groove


# ---------------------------------------------------------------------------
# Planform & Cutout Arch Functions
# ---------------------------------------------------------------------------
def shell_oval_xy(theta, scale=1.0):
    """Organic turtle planform at azimuth theta (0=+X front, pi=-X rear)."""
    c = math.cos(theta)
    s = math.sin(theta)
    shoulder = 1.0 + 0.035 * (s * s) - 0.025 * c
    return (RX * scale * shoulder * c, RY * scale * shoulder * s)


def _ang_diff(a, b):
    d = (a - b + math.pi) % (2.0 * math.pi) - math.pi
    return abs(d)


def rim_arch_z(theta):
    """Arched rim elevation around head, tail, and 4 limb cutouts."""
    head = 1.45 * math.exp(-(_ang_diff(theta, 0.0) / 0.38) ** 2)
    tail = 0.85 * math.exp(-(_ang_diff(theta, math.pi) / 0.28) ** 2)
    leg_fl = 0.95 * math.exp(-(_ang_diff(theta, math.radians(44.0)) / 0.24) ** 2)
    leg_fr = 0.95 * math.exp(-(_ang_diff(theta, math.radians(-44.0)) / 0.24) ** 2)
    leg_rl = 0.90 * math.exp(-(_ang_diff(theta, math.radians(136.0)) / 0.24) ** 2)
    leg_rr = 0.90 * math.exp(-(_ang_diff(theta, math.radians(-136.0)) / 0.24) ** 2)
    return 4.15 + head + tail + leg_fl + leg_fr + leg_rl + leg_rr


# ---------------------------------------------------------------------------
# Procedural Textures (deterministic, DarkPlaces lightingDiffuse calibrated)
# ---------------------------------------------------------------------------
def _fbm(h, w, seed, octaves=(4, 8, 16, 48)):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    amp = 1.0
    tot = 0.0
    for g in octaves:
        grid = rng.uniform(-1.0, 1.0, (g, g)).astype(np.float32)
        im = Image.fromarray(((grid * 0.5 + 0.5) * 255.0).astype(np.uint8), mode="L")
        im = im.resize((w, h), Image.Resampling.BICUBIC)
        acc += (np.asarray(im, dtype=np.float32) / 127.5 - 1.0) * amp
        tot += amp
        amp *= 0.5
    return acc / max(tot, 1e-6)


def _tex_carapace(path, base_rgb, hi_rgb, seam_rgb, seed):
    """512x512 scute-aligned carapace texture matching dome planar UV projection."""
    W = H = 512
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = xx / float(W - 1)
    v = yy / float(H - 1)

    # Same planar projection used in build_carapace(): u = 0.5 + 0.45*nx, v = 0.5 - 0.45*ny
    nx = (u - 0.5) / 0.45
    ny = (0.5 - v) / 0.45
    r = np.sqrt(nx * nx + ny * ny)

    seam_dist, plate_val, cid = eval_scute_field_np(nx, ny)
    noise = _fbm(H, W, seed=seed, octaves=(6, 12, 28, 64))

    # Concentric keratin growth rings inside each scute plate
    rings = 0.5 + 0.5 * np.sin(seam_dist * 115.0 + noise * 2.4)
    groove = np.exp(-(seam_dist * seam_dist) / 0.00048)

    # Deterministic per-plate subtle hue/value modulation
    plate_jitter = (((cid * 73 + seed) % 11) - 5.0) * 0.018

    # Radial dome sheen + subtle kart battle scuffs near outer shoulder
    scuff = np.clip((r - 0.65) * 2.2, 0.0, 1.0) * np.clip(noise * 1.4 - 0.25, 0.0, 1.0)

    t_hi = np.clip(plate_val * (0.68 + 0.24 * rings) + plate_jitter + 0.08 * noise, 0.0, 1.0)
    t_seam = np.clip(groove * 0.92 + 0.10 * (1.0 - plate_val), 0.0, 1.0)

    rgb = np.zeros((H, W, 3), dtype=np.float32)
    for c in range(3):
        col = base_rgb[c] * (1.0 - t_hi) + hi_rgb[c] * t_hi
        col = col * (1.0 - t_seam) + seam_rgb[c] * t_seam
        # Light ivory/grey scuff marks on shoulder
        col = col * (1.0 - 0.35 * scuff) + 205.0 * (0.35 * scuff)
        rgb[:, :, c] = np.clip(col + 5.0 * noise, 10.0, 244.0)

    Image.fromarray(rgb.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)


def _tex_trim(path):
    """512x512 shared atlas: cream/ivory rim (TL), tan segmented plastron belly (TR), dark cavity (B)."""
    W = H = 512
    arr = np.zeros((H, W, 3), dtype=np.float32)
    noise = _fbm(H, W, seed=777, octaves=(6, 14, 32, 64))
    yy, xx = np.mgrid[0:256, 0:256].astype(np.float32)
    u = xx / 255.0
    v = yy / 255.0

    # Top-Left: Warm ivory/cream outer rim lip with subtle cross-rib shading & clearcoat sheen
    sheen = 0.94 + 0.08 * np.sin(v * math.pi)
    rim_streak = 0.03 * np.sin(u * 40.0 + noise[:256, :256] * 2.0)
    arr[:256, :256, 0] = np.clip(226.0 * (sheen + rim_streak) + 4.0 * noise[:256, :256], 20, 245)
    arr[:256, :256, 1] = np.clip(218.0 * (sheen + rim_streak) + 4.0 * noise[:256, :256], 20, 240)
    arr[:256, :256, 2] = np.clip(182.0 * (sheen + rim_streak) + 3.5 * noise[:256, :256], 16, 215)

    # Top-Right: Segmented turtle plastron belly (center midline seam + 3 transverse seams)
    mid_seam = np.exp(-((u - 0.50) ** 2) / 0.00055)
    cross_seam = (
        np.exp(-((v - 0.28) ** 2) / 0.00055)
        + np.exp(-((v - 0.52) ** 2) / 0.00055)
        + np.exp(-((v - 0.74) ** 2) / 0.00055)
    )
    seams = np.clip(mid_seam + cross_seam, 0.0, 1.0)
    grain = 0.96 + 0.05 * np.sin(u * 30.0 + v * 12.0 + noise[:256, 256:] * 2.2)
    b_r = 208.0 * grain + 5.0 * noise[:256, 256:]
    b_g = 192.0 * grain + 5.0 * noise[:256, 256:]
    b_b = 142.0 * grain + 4.0 * noise[:256, 256:]
    arr[:256, 256:, 0] = np.clip(b_r * (1.0 - 0.62 * seams) + 52.0 * seams, 16, 232)
    arr[:256, 256:, 1] = np.clip(b_g * (1.0 - 0.65 * seams) + 46.0 * seams, 14, 220)
    arr[:256, 256:, 2] = np.clip(b_b * (1.0 - 0.68 * seams) + 32.0 * seams, 10, 180)

    # Bottom half: Deep dark hollow interior shell lining (so limb/head tunnels look deep & hollow)
    rib_cav = 0.88 + 0.12 * np.sin(np.mgrid[0:256, 0:512][0].astype(np.float32) * 0.25)
    n_bot = noise[256:, :]
    arr[256:, :, 0] = np.clip(22.0 * rib_cav + 3.0 * n_bot, 8, 42)
    arr[256:, :, 1] = np.clip(20.0 * rib_cav + 3.0 * n_bot, 8, 40)
    arr[256:, :, 2] = np.clip(18.0 * rib_cav + 2.5 * n_bot, 8, 36)

    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, "PNG", optimize=True)


def build_all_textures(progs_dir=PROGS_DIR):
    os.makedirs(progs_dir, exist_ok=True)
    # Green Shell: lush emerald mid, lime highlight, deep forest seams
    _tex_carapace(
        os.path.join(progs_dir, "gk_shell_green.png"),
        base_rgb=(36.0, 152.0, 52.0),
        hi_rgb=(96.0, 212.0, 74.0),
        seam_rgb=(16.0, 58.0, 22.0),
        seed=101,
    )
    # Red Shell: vivid crimson mid, warm coral-red highlight, dark burgundy seams
    _tex_carapace(
        os.path.join(progs_dir, "gk_shell_red.png"),
        base_rgb=(188.0, 34.0, 28.0),
        hi_rgb=(236.0, 86.0, 52.0),
        seam_rgb=(66.0, 12.0, 12.0),
        seed=202,
    )
    # Blue Shell: cobalt mid, electric sky-blue highlight, deep navy seams
    _tex_carapace(
        os.path.join(progs_dir, "gk_shell_blue.png"),
        base_rgb=(26.0, 88.0, 204.0),
        hi_rgb=(74.0, 168.0, 242.0),
        seam_rgb=(12.0, 32.0, 84.0),
        seed=303,
    )
    _tex_trim(os.path.join(progs_dir, "gk_shell_trim.png"))


# ---------------------------------------------------------------------------
# 3D Sub-Assembly Builders
# ---------------------------------------------------------------------------
def _compute_smooth_grid_normals(part, n_rings, n_cols, base_idx, has_apex=False, apex_idx=-1):
    """Area-weighted vertex normals with periodic seam welding across col 0 == n_cols - 1."""
    nv = len(part.verts)
    acc = [[0.0, 0.0, 0.0] for _ in range(nv)]
    for a, b, c in part.tris:
        pa, pb, pc = part.verts[a], part.verts[b], part.verts[c]
        fn = vcross(vsub(pb, pa), vsub(pc, pa))
        for vi in (a, b, c):
            acc[vi][0] += fn[0]
            acc[vi][1] += fn[1]
            acc[vi][2] += fn[2]

    # Weld seam normals across periodic wrap column
    for r in range(n_rings):
        i0 = base_idx + r * n_cols
        i1 = i0 + (n_cols - 1)
        nx = acc[i0][0] + acc[i1][0]
        ny = acc[i0][1] + acc[i1][1]
        nz = acc[i0][2] + acc[i1][2]
        acc[i0] = [nx, ny, nz]
        acc[i1] = [nx, ny, nz]

    if has_apex and apex_idx >= 0:
        acc[apex_idx] = [0.0, 0.0, 1.0]

    for i in range(base_idx, nv):
        part.norms[i] = vnorm(tuple(acc[i]))


def build_carapace():
    """Domed carapace with 3D sculpted hexagonal scutes matching texture UVs 1:1."""
    part = MeshPart("carapace")
    cols = N_THETA + 1
    base = len(part.verts)

    for r_idx in range(N_PHI):
        # v goes from 0.0 (lower lip tucked inside rim) to 0.95 (near crown); apex cap closes top
        v = 0.955 * (r_idx / float(N_PHI - 1))
        rad_scale = (math.cos(v * math.pi * 0.5) ** 0.86) * 0.985
        z_t = math.sin(v * math.pi * 0.5)
        # Edge blend keeps rim seam flush with rim lip while inner dome shows bold scutes
        relief_blend = smoothstep(min(1.0, v / 0.11))

        for j in range(cols):
            th = 2.0 * math.pi * (j / float(N_THETA))
            bx, by = shell_oval_xy(th, scale=rad_scale)
            z_edge = rim_arch_z(th) + 0.65
            z_base = z_edge * (1.0 - z_t ** 1.45) + Z_PEAK * (z_t ** 1.08)

            nx = bx / RX
            ny = by / RY
            dh = eval_scute_height(nx, ny) * relief_blend

            # Displace along approximate outward dome direction
            n_dir = vnorm((nx, ny, 0.55 + 1.8 * z_t))
            pos = (bx + n_dir[0] * dh, by + n_dir[1] * dh, z_base + n_dir[2] * dh)

            u = 0.5 + 0.45 * nx
            tv = 0.5 - 0.45 * ny
            part.verts.append(pos)
            part.norms.append(n_dir)
            part.st.append((u, tv))

    for r_idx in range(N_PHI - 1):
        row0 = base + r_idx * cols
        row1 = base + (r_idx + 1) * cols
        for j in range(N_THETA):
            a = row0 + j
            b = a + 1
            c = row1 + j
            d = c + 1
            part.tris += [(a, b, d), (a, d, c)]

    # Smooth apex center cap (guaranteed outward +Z normal)
    apex_idx = len(part.verts)
    apex_dh = eval_scute_height(0.0, 0.0)
    part.verts.append((0.0, 0.0, Z_PEAK + apex_dh))
    part.norms.append((0.0, 0.0, 1.0))
    part.st.append((0.5, 0.5))

    top_row = base + (N_PHI - 1) * cols
    for j in range(N_THETA):
        part.tris.append((top_row + j, top_row + j + 1, apex_idx))

    _compute_smooth_grid_normals(part, N_PHI, cols, base, has_apex=True, apex_idx=apex_idx)
    return part


def build_rim():
    """Chunky rounded cream/ivory perimeter bumper lip around the carapace skirt."""
    part = MeshPart("rim")
    # Cross-section offsets (dr_outward, dz_up) forming a bold rounded D-bead lip
    prof = [
        (-1.10, +0.90),  # tucked under carapace
        (-0.20, +1.38),  # upper shoulder
        (+0.75, +1.36),  # upper roll
        (+1.42, +0.85),  # outer upper curve
        (+1.68, +0.10),  # outermost bumper equator
        (+1.48, -0.68),  # lower outer curve
        (+0.78, -1.18),  # bottom lip
        (-0.15, -1.25),  # inner lower edge
        (-0.95, -0.75),  # inner cavity tuck
        (-1.15, +0.10),  # inner wall
        (-1.10, +0.90),  # close loop
    ]
    n_prof = len(prof)
    cols = N_THETA + 1
    u0, v0, u1, v1 = UV_TRIM_RIM
    base = len(part.verts)

    for p_idx, (dr, dz) in enumerate(prof):
        tv = v0 + (v1 - v0) * (p_idx / float(n_prof - 1))
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(N_THETA))
            bx, by = shell_oval_xy(th, scale=1.0)
            out_dir = vnorm((bx, by, 0.0))
            zc = rim_arch_z(th)
            pos = (bx + out_dir[0] * dr, by + out_dir[1] * dr, zc + dz)
            tu = u0 + (u1 - u0) * (j / float(N_THETA))
            part.verts.append(pos)
            part.norms.append(out_dir)
            part.st.append((tu, tv))

    for p_idx in range(n_prof - 1):
        row0 = base + p_idx * cols
        row1 = base + (p_idx + 1) * cols
        for j in range(N_THETA):
            a = row0 + j
            b = a + 1
            c = row1 + j
            d = c + 1
            # Winding: outward along (bx, by) x +Z
            part.tris += [(a, d, b), (a, c, d)]

    _compute_smooth_grid_normals(part, n_prof, cols, base)
    return part


def build_belly():
    """Segmented ventral plastron plate sitting flush on ground plane Z = 0.0."""
    part = MeshPart("belly")
    # Radial profile from outer tucked edge (t=0) down to flat ground contact pad (t=1)
    rings_spec = [
        (0.86, 2.70),
        (0.84, 1.80),
        (0.78, 0.85),
        (0.68, 0.22),
        (0.55, 0.00),
        (0.32, 0.00),
    ]
    n_rings = len(rings_spec)
    cols = N_THETA + 1
    u0, v0, u1, v1 = UV_TRIM_BELLY
    base = len(part.verts)

    for r_idx, (r_sc, z_val) in enumerate(rings_spec):
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(N_THETA))
            # Pull inward gently around head/tail/leg arches to reveal dark limb tunnels
            notch = (
                0.08 * math.exp(-(_ang_diff(th, 0.0) / 0.34) ** 2)
                + 0.06 * math.exp(-(_ang_diff(th, math.pi) / 0.26) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(44.0)) / 0.22) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(-44.0)) / 0.22) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(136.0)) / 0.22) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(-136.0)) / 0.22) ** 2)
            )
            sc = r_sc * (1.0 - notch)
            bx, by = shell_oval_xy(th, scale=sc)
            tu = 0.5 * (u0 + u1) + 0.44 * (u1 - u0) * (bx / RX)
            tv = 0.5 * (v0 + v1) - 0.44 * (v1 - v0) * (by / RY)
            part.verts.append((bx, by, z_val))
            part.norms.append((0.0, 0.0, -1.0))
            part.st.append((tu, tv))

    for r_idx in range(n_rings - 1):
        row0 = base + r_idx * cols
        row1 = base + (r_idx + 1) * cols
        for j in range(N_THETA):
            a = row0 + j
            b = a + 1
            c = row1 + j
            d = c + 1
            # Bottom-facing outward normal (-Z)
            part.tris += [(a, d, b), (a, c, d)]

    center_idx = len(part.verts)
    part.verts.append((0.0, 0.0, 0.0))
    part.norms.append((0.0, 0.0, -1.0))
    part.st.append((0.5 * (u0 + u1), 0.5 * (v0 + v1)))
    inner_row = base + (n_rings - 1) * cols
    for j in range(N_THETA):
        part.tris.append((inner_row + j, center_idx, inner_row + j + 1))

    _compute_smooth_grid_normals(part, n_rings, cols, base)
    part.norms[center_idx] = (0.0, 0.0, -1.0)
    return part


def build_cavity():
    """Dark recessed hollow shell lining bridging rim underside to ventral plastron."""
    part = MeshPart("cavity")
    cols = N_THETA + 1
    u0, v0, u1, v1 = UV_TRIM_CAVITY
    base = len(part.verts)
    # 5 vertical slices from inner upper rim down to belly edge
    slices = [
        (0.00, 0.94, +0.20),
        (0.25, 0.85, -0.35),
        (0.50, 0.80, -0.90),
        (0.75, 0.82, -1.45),
        (1.00, 0.86, 0.00),
    ]
    n_sl = len(slices)

    for s_idx, (t, sc, _dz) in enumerate(slices):
        tv = v0 + (v1 - v0) * t
        for j in range(cols):
            th = 2.0 * math.pi * (j / float(N_THETA))
            notch = (
                0.08 * math.exp(-(_ang_diff(th, 0.0) / 0.34) ** 2)
                + 0.06 * math.exp(-(_ang_diff(th, math.pi) / 0.26) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(44.0)) / 0.22) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(-44.0)) / 0.22) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(136.0)) / 0.22) ** 2)
                + 0.05 * math.exp(-(_ang_diff(th, math.radians(-136.0)) / 0.22) ** 2)
            )
            r_sc = sc * (1.0 - notch * t)
            bx, by = shell_oval_xy(th, scale=r_sc)
            z_top = rim_arch_z(th) - 0.50
            z_bot = 2.40
            z = z_top * (1.0 - t) + z_bot * t
            tu = u0 + (u1 - u0) * (j / float(N_THETA))
            part.verts.append((bx, by, z))
            part.norms.append(vnorm((bx, by, 0.0)))
            part.st.append((tu, tv))

    for s_idx in range(n_sl - 1):
        row0 = base + s_idx * cols
        row1 = base + (s_idx + 1) * cols
        for j in range(N_THETA):
            a = row0 + j
            b = a + 1
            c = row1 + j
            d = c + 1
            # Outward-facing normal away from shell interior
            part.tris += [(a, d, b), (a, c, d)]

    _compute_smooth_grid_normals(part, n_sl, cols, base)
    return part


def build_model():
    """Assembles the 4-surface, 16-frame spinning turtle shell MD3."""
    parts = [
        ("carapace", "progs/gk_shell_green", build_carapace()),
        ("rim",      "progs/gk_shell_trim",  build_rim()),
        ("belly",    "progs/gk_shell_trim",  build_belly()),
        ("cavity",   "progs/gk_shell_trim",  build_cavity()),
    ]

    frame_names = [f"spin_{fi:02d}" for fi in range(N_FRAMES)]
    surfaces = []
    for name, shader, part in parts:
        frames = []
        for fi in range(N_FRAMES):
            deg = 360.0 * (fi / float(N_FRAMES))
            if fi == 0:
                vv = list(part.verts)
                nn = list(part.norms)
            else:
                vv = [rot_z(p, deg) for p in part.verts]
                nn = [vnorm(rot_z(n, deg)) for n in part.norms]
            frames.append((vv, nn))
        surfaces.append(dict(name=name, shader=shader, tris=part.tris, st=part.st, frames=frames))

    return dict(name="progs/gokart_shell.md3", frame_names=frame_names, surfaces=surfaces)


# ---------------------------------------------------------------------------
# Skins, Meta, Verification & Entry Point
# ---------------------------------------------------------------------------
def write_skins_and_meta(model, progs_dir=PROGS_DIR, meta_dir=OUT_DIR):
    for s_idx, slug, carapace_shader, _label in SKIN_VARIANTS:
        skin_path = os.path.join(progs_dir, f"gokart_shell.md3_{s_idx}.skin")
        with open(skin_path, "w", encoding="ascii", newline="\n") as f:
            for s in model["surfaces"]:
                sh = carapace_shader if s["name"] == "carapace" else s["shader"]
                f.write(f"{s['name']},{sh}\n")

    if meta_dir is None:
        return
    os.makedirs(meta_dir, exist_ok=True)
    meta = {
        "id": "gokart_shell",
        "name": "Go-Kart Turtle Shell",
        "tagline": "3D sculpted scute carapace, arched ivory rim, plastron belly & 3 skins (Green/Red/Blue)",
        "bounds_hint": {"rx": RX, "ry": RY, "z_peak": Z_PEAK},
        "skins": [
            {"index": idx, "slug": slug, "label": lbl, "carapace_shader": sh}
            for idx, slug, sh, lbl in SKIN_VARIANTS
        ],
        "textures": {
            "progs/gk_shell_green": "progs/gk_shell_green.png",
            "progs/gk_shell_red":   "progs/gk_shell_red.png",
            "progs/gk_shell_blue":  "progs/gk_shell_blue.png",
            "progs/gk_shell_trim":  "progs/gk_shell_trim.png",
        },
        "materials": {
            "progs/gk_shell_green": {"metallic": 0.08, "roughness": 0.42, "spec": 0.55},
            "progs/gk_shell_red":   {"metallic": 0.08, "roughness": 0.42, "spec": 0.55},
            "progs/gk_shell_blue":  {"metallic": 0.12, "roughness": 0.36, "spec": 0.65},
            "progs/gk_shell_trim":  {"metallic": 0.04, "roughness": 0.58, "spec": 0.32},
        },
    }
    meta_path = os.path.join(meta_dir, "gk_shell_meta.json")
    with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)


def verify_md3(md3_path):
    m = md3lib.read(md3_path)
    assert m["nframes"] == N_FRAMES, f"Expected {N_FRAMES} frames, got {m['nframes']}"
    expected_surfs = {"carapace", "rim", "belly", "cavity"}
    got_surfs = {s["name"] for s in m["surfaces"]}
    assert expected_surfs == got_surfs, f"Surface mismatch: {got_surfs} != {expected_surfs}"

    for s in m["surfaces"]:
        nv = len(s["st"])
        nt = len(s["tris"])
        assert 0 < nv <= 4096, f"{s['name']} nv={nv} > 4096"
        assert 0 < nt <= 8192, f"{s['name']} nt={nt} > 8192"
        assert s["shader"].startswith("progs/gk_shell_"), f"Bad shader {s['shader']}"
        for fi, (vv, nn) in enumerate(s["frames"]):
            for p, n in zip(vv, nn):
                assert all(math.isfinite(c) and abs(c) < 511.5 for c in p), f"Bad coord on {s['name']} f={fi}: {p}"
                assert all(math.isfinite(c) for c in n), f"Bad norm on {s['name']} f={fi}"

    for fi in range(N_FRAMES):
        all_z = [p[2] for s in m["surfaces"] for p in s["frames"][fi][0]]
        assert abs(min(all_z)) <= 0.05, f"Frame {fi} z_min={min(all_z):.4f} != 0.0"

    f0_pts = [p for s in m["surfaces"] for p in s["frames"][0][0]]
    xs = [p[0] for p in f0_pts]
    ys = [p[1] for p in f0_pts]
    zs = [p[2] for p in f0_pts]
    print(f"Verified {md3_path}: {m['nframes']} frames, {len(m['surfaces'])} surfaces")
    print(f"Frame 0 bounds: X=[{min(xs):.2f}, {max(xs):.2f}] Y=[{min(ys):.2f}, {max(ys):.2f}] Z=[{min(zs):.2f}, {max(zs):.2f}]")
    for s in m["surfaces"]:
        print(f"  {s['name']:10s} shader={s['shader']:22s} verts={len(s['st']):4d} tris={len(s['tris']):4d}")


def main(progs_dir=PROGS_DIR, meta_dir=OUT_DIR):
    build_all_textures(progs_dir=progs_dir)
    model = build_model()
    md3_path = os.path.join(progs_dir, "gokart_shell.md3")
    md3lib.write(md3_path, model)
    write_skins_and_meta(model, progs_dir=progs_dir, meta_dir=meta_dir)
    verify_md3(md3_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build Go-Kart Turtle Shell MD3, 3 skins, and textures.")
    p.add_argument("--out-dir", default=None, help="Output directory for MD3, skins, and PNGs")
    p.add_argument("--meta-dir", default=None, help="Optional directory for gk_shell_meta.json")
    args = p.parse_args()
    progs_dir = args.out_dir if args.out_dir is not None else PROGS_DIR
    meta_dir = args.meta_dir if args.meta_dir is not None else (OUT_DIR if args.out_dir is None else None)
    main(progs_dir=progs_dir, meta_dir=meta_dir)
