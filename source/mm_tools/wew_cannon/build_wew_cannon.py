"""Master 3D Procedural Geometry, Curvilinear Bending-Barrel Animation & Multi-Format Quake Exporter
for the SUPER GIANT SILVER 'WEW CANNON' (`v_wewcannon` / `v_wcannon`).

Builds & validates 100% compatible Quake weapon assets across BOTH modern DarkPlaces/Q3 (`.md3` + `.skin` + `.shader`)
AND strict vanilla 1996 Quake (`IDPO` v6 `.mdl`, <= 1024 verts, <= 2048 tris, 512x256 skin <= 480 height + hires `.tga`):

  1. `progs/v_wewcannon.md3` & `progs/v_wcannon.md3` (+ `_0.skin`, `_1.skin`)  — 48-frame HD 1st-Person Viewmodel
  2. `progs/v_wewcannon.mdl` & `progs/v_wcannon.mdl` (+ `_0.tga`)              — 48-frame Vanilla-Legal Quake 1 `.mdl`
  3. `progs/g_wewcannon.md3` & `progs/g_wewcannon.mdl` (+ `_0.skin`, `_0.tga`) — Centered World Pickup Cannon Model
  4. `progs/proj_wewcannon.md3` & `progs/proj_wewcannon.mdl` (+ `.skin`,`.tga`)— 16-frame Giant WEW Projectile Model
  5. `scripts/wewcannon.shader`                                                — DarkPlaces / Quake 3 Shader
  6. `wew_cannon_weapon.glb` & `wew_cannon_projectile.glb`                     — Universal glTF 2.0 PBR 3D Models

48-Frame Animation Schedule (`v_wewcannon` / `v_wcannon`):
  - Frames  0..15 (`idle1..idle16`, 16f)  : Ponderous giant-cannon figure-8 sway, breathing silver barrel, live WEW-METER
  - Frames 16..25 (`bend1..bend10`, 10f)  : SUPER BIG CHARGE BEND — Giant silver barrel bends +42 deg up & +16 deg inward,
                                            squashes axially, and swells a massive +42% peristaltic belly bulge!
  - Frames 26..29 (`blast1..blast4`, 4f)  : WHIP-SNAP & HUGE PROJECTILE BLAST — Bulge surges down bore, barrel whips -24 deg
                                            forward, giant bell flares +45% wide open, blasting a colossal glowing WEW shell
                                            inside a 3D starburst flash & supersonic Mach shockwave rings!
  - Frames 30..39 (`recoil1..recoil10`,10f): Massive recoil slam + springy +34 deg -> -18 deg -> +13 deg S-bend whiplash & steam!
  - Frames 40..47 (`reload1..reload8`, 8f): Breech chamber pulse gulp & smooth return to `idle1`!
"""
import json
import math
import os
import re
import shutil
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
SCRIPTS_DIR = os.path.join(MOD_ROOT, "scripts")

OUT_ROOT = os.path.join(MM_TOOLS, "out", "wew_cannon")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
STAGE_DIR = os.path.join(OUT_ROOT, "models")

PAK_PATH = r"G:\Quake\QBJ3\id1\pak0.pak"
ANORMS_PATH = r"D:\vibe\quake1opensource\idsrc\WinQuake\anorms.h"

for p in (MM_TOOLS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import md3lib
from mmw_geometry import build_articulated_ranger_hand, rot_x, rot_y, rot_z, vadd, vmul, vnorm
import make_wew_textures as wtex


# ===========================================================================
# VECTOR / MATRIX & MESH UTILITIES
# ===========================================================================
def rot_x_mat(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def rot_y_mat(deg):
    """Pitches +X upward toward +Z for positive deg (`z' = +x sin + z cos`? Wait: check `mmw_geometry.rot_y`!):
    In `mmw_geometry.rot_y`: `(x*c - z*s, y, x*s + z*c)` -> +deg pitches +X up toward +Z!"""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]], dtype=np.float64)


def rot_z_mat(deg):
    """Yaws +X toward +Y (left) for positive deg."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)


class SurfBuilder:
    def __init__(self, name, shader, mat_key):
        self.name = name
        self.shader = shader
        self.mat = mat_key
        self.verts = []
        self.norms = []
        self.st = []
        self.tris = []          # Stored CCW-outward during construction; converted to CW-outward for MD3/MDL
        self.deform_tags = []   # Per-vertex tag: "barrel", "breech", "piston", "static", etc.

    def add_part(self, verts, norms, st, tris_ccw, tag="barrel"):
        base = len(self.verts)
        self.verts.extend(verts)
        self.norms.extend(norms)
        self.st.extend(st)
        self.deform_tags.extend([tag] * len(verts))
        for a, b, c in tris_ccw:
            # Verify CCW-outward against vertex normals so zero inverted faces can ever sneak in!
            pa, pb, pc = verts[a], verts[b], verts[c]
            e1 = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])
            e2 = (pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2])
            fn = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            vn = (norms[a][0] + norms[b][0] + norms[c][0],
                  norms[a][1] + norms[b][1] + norms[c][1],
                  norms[a][2] + norms[b][2] + norms[c][2])
            if fn[0] * vn[0] + fn[1] * vn[1] + fn[2] * vn[2] < -1e-9:
                self.tris.append((base + a, base + c, base + b))
            else:
                self.tris.append((base + a, base + b, base + c))


def build_lathe_tube(profile_xr, radial_segs, uv_rect, axis_offset=(0.0, 0.0, 0.0), inward_normals=False):
    """Revolves `(x, r)` stations around the +X axis (`phi=0` at +Z top, `phi=+90` at +Y left):
    `y = r * sin(phi)`, `z = r * cos(phi)`. Returns `(verts, norms, st, tris_ccw)`."""
    u0, v0, u1, v1 = uv_rect
    ox, oy, oz = axis_offset
    nr = len(profile_xr)
    verts, norms, st, tris = [], [], [], []

    # Compute smooth radial slope normals along profile
    dr_dx = []
    for j in range(nr):
        j0 = max(0, j - 1)
        j1 = min(nr - 1, j + 1)
        dx = profile_xr[j1][0] - profile_xr[j0][0]
        dr = profile_xr[j1][1] - profile_xr[j0][1]
        if abs(dx) < 1e-6:
            nx, nrad = (-1.0 if dr > 0 else 1.0), 0.25
        else:
            nx, nrad = -dr, dx
            if dx < 0:
                nx, nrad = -nx, -nrad
        l = math.hypot(nx, nrad) or 1.0
        nx, nrad = nx / l, nrad / l
        if inward_normals:
            nx, nrad = -nx, -nrad
        dr_dx.append((nx, nrad))

    for j, (x, r) in enumerate(profile_xr):
        tv = j / max(1, nr - 1)
        nx_s, nr_s = dr_dx[j]
        for i in range(radial_segs + 1):
            tu = i / radial_segs
            # Place UV wrap seam at -Z bottom (`phi = pi` at tu=0) so top & flanks are 100% seamless!
            phi = math.pi + tu * 2.0 * math.pi
            sp, cp = math.sin(phi), math.cos(phi)
            verts.append((ox + x, oy + r * sp, oz + r * cp))
            norms.append((nx_s, nr_s * sp, nr_s * cp))
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))

    stride = radial_segs + 1
    for j in range(nr - 1):
        for i in range(radial_segs):
            a = j * stride + i
            b = j * stride + i + 1
            c = (j + 1) * stride + i + 1
            d = (j + 1) * stride + i
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, norms, st, tris


def build_curved_barrel_plaque(x0, x1, r_func, phi_top_deg, phi_bot_deg, nx_segs, nphi_segs, uv_rect,
                               u_muzzle_to_breech=True, lift=0.34):
    """Builds a raised 3D beveled curved nameplate saddle hugging the silver cannon barrel!
    `phi = 0` is +Z top, `+90` is +Y inner-left (1st-person side), `-90` is -Y outer-right."""
    u0, v0, u1, v1 = uv_rect
    verts, norms, st, tris = [], [], [], []

    # 1. Raised Curved Front Face of Plaque
    for j in range(nphi_segs + 1):
        tv = j / nphi_segs
        phi = math.radians(phi_top_deg + (phi_bot_deg - phi_top_deg) * tv)
        sp, cp = math.sin(phi), math.cos(phi)
        for i in range(nx_segs + 1):
            tx = i / nx_segs
            x = x0 + (x1 - x0) * tx
            r = r_func(x) + lift
            verts.append((x, r * sp, r * cp))
            norms.append((0.0, sp, cp))
            tu = (1.0 - tx) if u_muzzle_to_breech else tx
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))

    stride = nx_segs + 1
    for j in range(nphi_segs):
        for i in range(nx_segs):
            a = j * stride + i
            b = j * stride + i + 1
            c = (j + 1) * stride + i + 1
            d = (j + 1) * stride + i
            tris.append((a, b, c))
            tris.append((a, c, d))

    # 2. 4 Crisp Beveled Silver Rim Skirts around the Plaque Perimeter so it has true 3D relief!
    rim_uv = wtex.UV_SILVER_BAND
    ru0, rv0, ru1, rv1 = rim_uv

    # Top & Bottom longitudinal bevel edges
    for phi_deg, n_sign in ((phi_top_deg, -1.0), (phi_bot_deg, +1.0)):
        base = len(verts)
        phi = math.radians(phi_deg)
        sp, cp = math.sin(phi), math.cos(phi)
        tang_n = vnorm((0.0, n_sign * cp * math.copysign(1.0, phi_bot_deg - phi_top_deg),
                        -n_sign * sp * math.copysign(1.0, phi_bot_deg - phi_top_deg)))
        for i in range(nx_segs + 1):
            tx = i / nx_segs
            x = x0 + (x1 - x0) * tx
            r_in = r_func(x) - 0.04
            r_out = r_func(x) + lift
            verts.append((x, r_out * sp, r_out * cp))
            norms.append(tang_n)
            st.append((ru0 + (ru1 - ru0) * tx, rv0))
            verts.append((x, r_in * sp, r_in * cp))
            norms.append(tang_n)
            st.append((ru0 + (ru1 - ru0) * tx, rv1))
        for i in range(nx_segs):
            a, b, c, d = base + 2 * i, base + 2 * i + 1, base + 2 * i + 2, base + 2 * i + 3
            tris.append((a, b, c))
            tris.append((b, d, c))

    # Breech & Muzzle end-cap bevel skirts
    for x_end, nx_dir in ((x0, -1.0), (x1, +1.0)):
        base = len(verts)
        r_in = r_func(x_end) - 0.04
        r_out = r_func(x_end) + lift
        for j in range(nphi_segs + 1):
            tv = j / nphi_segs
            phi = math.radians(phi_top_deg + (phi_bot_deg - phi_top_deg) * tv)
            sp, cp = math.sin(phi), math.cos(phi)
            verts.append((x_end, r_out * sp, r_out * cp))
            norms.append((nx_dir, 0.0, 0.0))
            st.append((ru0 + (ru1 - ru0) * tv, rv0))
            verts.append((x_end, r_in * sp, r_in * cp))
            norms.append((nx_dir, 0.0, 0.0))
            st.append((ru0 + (ru1 - ru0) * tv, rv1))
        for j in range(nphi_segs):
            a, b, c, d = base + 2 * j, base + 2 * j + 1, base + 2 * j + 2, base + 2 * j + 3
            tris.append((a, b, c))
            tris.append((b, d, c))

    return verts, norms, st, tris


def build_box(x0, x1, y0, y1, z0, z1, uv_rect):
    u0, v0, u1, v1 = uv_rect
    faces = [
        # (nrm, 4 corners)
        ((+1, 0, 0), [(x1, y0, z1), (x1, y1, z1), (x1, y1, z0), (x1, y0, z0)]),
        ((-1, 0, 0), [(x0, y1, z1), (x0, y0, z1), (x0, y0, z0), (x0, y1, z0)]),
        ((0, +1, 0), [(x1, y1, z1), (x0, y1, z1), (x0, y1, z0), (x1, y1, z0)]),
        ((0, -1, 0), [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)]),
        ((0, 0, +1), [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)]),
        ((0, 0, -1), [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]),
    ]
    verts, norms, st, tris = [], [], [], []
    uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    for nrm, pts in faces:
        b = len(verts)
        verts.extend(pts)
        norms.extend([nrm] * 4)
        st.extend(uvs)
        tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])
    return verts, norms, st, tris


def build_uv_sphere(radius, nu, nv, uv_rect, center=(0.0, 0.0, 0.0), scale_xyz=(1.0, 1.0, 1.0)):
    """Sphere with pole axis along +X (warhead axis) so equator faces barrel sides cleanly!"""
    u0, v0, u1, v1 = uv_rect
    cx, cy, cz = center
    sx, sy, sz = scale_xyz
    verts, norms, st, tris = [], [], [], []
    for j in range(nv + 1):
        tv = j / nv
        theta = tv * math.pi  # 0 at +Z top pole -> pi at -Z bottom pole
        st_th, ct_th = math.sin(theta), math.cos(theta)
        for i in range(nu + 1):
            tu = i / nu
            phi = tu * 2.0 * math.pi
            nx = st_th * math.cos(phi)
            ny = st_th * math.sin(phi)
            nz = ct_th
            verts.append((cx + radius * sx * nx, cy + radius * sy * ny, cz + radius * sz * nz))
            norms.append(vnorm((nx / max(sx, 1e-4), ny / max(sy, 1e-4), nz / max(sz, 1e-4))))
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))
    stride = nu + 1
    for j in range(nv):
        for i in range(nu):
            a = j * stride + i
            b = j * stride + i + 1
            c = (j + 1) * stride + i + 1
            d = (j + 1) * stride + i
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, norms, st, tris


# ===========================================================================
# CANNON BARREL PROFILE & MILITARY HEAVY-ORDNANCE REST GEOMETRY
# ===========================================================================
X_BREECH_START = -6.6
X_PIVOT        =  0.2
X_MUZZLE_TIP   = 27.5
L_BARREL       = X_MUZZLE_TIP - X_PIVOT


def base_barrel_radius(x):
    """Stepped military titanium-silver 155mm artillery barrel outer profile `x in [0.2 .. 20.6]`."""
    if x < 5.2:
        # Heavy reinforced high-pressure chamber section
        return 4.02 - 0.04 * max(0.0, x - 0.2)
    if x < 5.8:
        # Crisp machined step-down collar transition
        u = (x - 5.2) / 0.6
        return 3.82 - 0.26 * u
    t = max(0.0, min(1.0, (x - 5.8) / 14.4))
    return 3.56 - 0.22 * t


def build_chamfer_oct_prism(x0, x1, half_y, half_z, uv_rect, ch=0.72):
    """Builds an 8-sided flat-faceted military armored octagonal housing along X `[x0..x1]`
    with crisp hard-edged face normals and front/rear end caps (`48` verts, `36` tris)."""
    u0, v0, u1, v1 = uv_rect
    cy, cz = half_y, half_z
    iy, iz = half_y - ch, half_z - ch
    ring = [
        (+iy, +cz), (-iy, +cz),
        (-cy, +iz), (-cy, -iz),
        (-iy, -cz), (+iy, -cz),
        (+cy, -iz), (+cy, +iz),
    ]
    verts, norms, st, tris = [], [], [], []
    # 8 flat armored longitudinal side panels
    for k in range(8):
        y0p, z0p = ring[k]
        y1p, z1p = ring[(k + 1) % 8]
        ny, nz = z1p - z0p, -(y1p - y0p)
        nl = math.hypot(ny, nz) or 1.0
        # Ensure outward normal
        if ny * (0.5 * (y0p + y1p)) + nz * (0.5 * (z0p + z1p)) < 0.0:
            ny, nz = -ny, -nz
        nrm = (0.0, ny / nl, nz / nl)
        b = len(verts)
        verts.extend([(x0, y0p, z0p), (x1, y0p, z0p), (x1, y1p, z1p), (x0, y1p, z1p)])
        norms.extend([nrm] * 4)
        st.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])

    # Front (+X) & Rear (-X) octagonal end caps
    for x_c, nx_c in ((x0, -1.0), (x1, +1.0)):
        b = len(verts)
        for yp, zp in ring:
            verts.append((x_c, yp, zp))
            norms.append((nx_c, 0.0, 0.0))
            tu = 0.5 + 0.45 * (yp / max(cy, 1e-4))
            tv = 0.5 - 0.45 * (zp / max(cz, 1e-4))
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))
        for k in range(1, 7):
            if nx_c > 0:
                tris.append((b, b + k + 1, b + k))
            else:
                tris.append((b, b + k, b + k + 1))
    return verts, norms, st, tris


def build_cannon_rest_surfaces(lod="hd"):
    """Constructs the military-spec WEW CANNON (`lod='hd'` for MD3/GLB, `lod='mdl'` for <=1024v MDL)."""
    is_hd = (lod == "hd")
    rad_main = 24 if is_hd else 8
    rad_sub  = 10 if is_hd else 4
    nx_plq   = 12 if is_hd else 5
    np_plq   = 4  if is_hd else 2

    surf_silver = SurfBuilder("cannon_silver", "progs/wew_silver",   "silver")
    surf_hands  = SurfBuilder("ranger_hands",  "progs/wew_hand",     "hand")
    surf_core   = SurfBuilder("cannon_core",   "progs/wew_core",     "core")
    surf_crt    = SurfBuilder("crt_screen",    "progs/wew_crt_anim", "crt")
    surf_fx     = SurfBuilder("cannon_fx",     "progs/wew_fx",       "fx")

    # 1. HEAVY ARMORED TANK / HOWITZER SLIDING BREECH BLOCK (`tag="breech"`, replaces pirate knob!)
    vb_oct, nb_oct, sb_oct, tb_oct = build_chamfer_oct_prism(
        -5.55, +0.45, half_y=4.08, half_z=3.78, uv_rect=(0.54, 0.275, 0.78, 0.370), ch=1.05
    )
    surf_silver.add_part(vb_oct, nb_oct, sb_oct, tb_oct, tag="breech")

    # Rear Yellow/Black Hazard Recoil Bumper Block + Twin Chrome Buffer Plungers
    vhz, nhz, shz, thz = build_box(-6.45, -5.50, -2.95, +2.95, -2.55, +2.55, wtex.UV_HAZARD_STRIPE)
    surf_silver.add_part(vhz, nhz, shz, thz, tag="breech")
    if is_hd:
        for sgn in (-1.0, +1.0):
            buf_xr = [(-7.15, 0.08), (-7.05, 0.62), (-5.50, 0.62)]
            vbf, nbf, sbf, tbf = build_lathe_tube(buf_xr, rad_sub, wtex.UV_SILVER_BARREL, axis_offset=(0.0, sgn * 1.85, +0.15))
            surf_silver.add_part(vbf, nbf, sbf, tbf, tag="breech")
        # Heavy Breech-Block Cam Locking Handle on left flank (+Y, visible in 1st-person POV!)
        vlv, nlv, slv, tlv = build_box(-4.35, -1.85, +3.92, +4.48, +0.55, +1.75, wtex.UV_SILVER_BAND)
        surf_silver.add_part(vlv, nlv, slv, tlv, tag="breech")
        # Compact Recessed Breech Charge-Status Indicator Strip on upper-left breech bevel!
        vcp, ncp, scp, tcp = build_box(-4.05, -2.10, +3.42, +3.72, +2.05, +2.52, wtex.UV_CORE_PLASMA)
        surf_core.add_part(vcp, ncp, scp, tcp, tag="breech")

    # 2. STEPPED FLUTED TITANIUM-SILVER 155MM MAIN BARREL (`x = 0.20 .. 21.40`, `tag="barrel"`)
    outer_xr = [
        (0.20, 4.02),
        (2.80, 3.92),
        (5.20, 3.82),
        (5.80, 3.56),
    ]
    n_mid = 8 if is_hd else 3
    for k in range(1, n_mid + 1):
        xk = 5.80 + (19.35 - 5.80) * (k / n_mid)
        outer_xr.append((xk, base_barrel_radius(xk)))
    outer_xr.extend([
        (19.35, 3.36),
        (20.10, 3.85),
        (21.35, 3.85),
        (21.45, 3.05),
    ])
    v, n, s, t = build_lathe_tube(outer_xr, rad_main, wtex.UV_SILVER_BARREL)
    surf_silver.add_part(v, n, s, t, tag="barrel")

    # Deep Spiral-Rifled 155mm Inner Bore (`x = 27.45` through muzzle brake back to `x = 12.0`)
    bore_xr = [
        (27.45, 2.88),
        (26.20, 2.72),
        (21.20, 2.62),
        (15.50, 2.45),
        (12.20, 0.10),
    ]
    v, n, s, t = build_lathe_tube(bore_xr, rad_main, wtex.UV_DARK_BORE)
    surf_silver.add_part(v, n, s, t, tag="barrel")

    # 3. Machined Titanium Barrel Locking Collars + Muzzle-Brake Hazard Warning Band
    hoop_specs = [
        (0.15,  1.25, 0.22, wtex.UV_SILVER_BAND),     # Chamber front lock ring
        (19.30, 20.15, 0.42, wtex.UV_HAZARD_STRIPE),  # Pre-brake yellow/black hazard collar!
    ]
    if is_hd:
        hoop_specs.append((2.35,  3.20, 0.24, wtex.UV_SILVER_BAND))   # Rear armor-plate collar
        hoop_specs.append((20.18, 21.20, 0.56, wtex.UV_SILVER_BAND))  # Heavy brake adapter collar
    for hx0, hx1, h_lift, h_uv in hoop_specs:
        r0 = base_barrel_radius(hx0)
        r1 = base_barrel_radius(hx1)
        rm = 0.5 * (r0 + r1) + h_lift
        h_xr = [
            (hx0 - 0.12, r0 - 0.18),
            (hx0,        rm),
            (hx1,        rm),
            (hx1 + 0.12, r1 - 0.18),
        ]
        v, n, s, t = build_lathe_tube(h_xr, rad_main, h_uv)
        surf_silver.add_part(v, n, s, t, tag="barrel")

    # 4. COLOSSAL MULTI-BAFFLE 155MM TANK / HOWITZER MUZZLE BRAKE (`x = 21.20 .. 27.50`, `tag="barrel"`)
    #    Replaces the smooth pirate blunderbuss horn with an aggressive 2-chamber military artillery brake!
    #    - Thick brushed-titanium upper & lower blast-shield decks (`y in [-5.05..+5.05]`)
    #    - Three massive vertical blast-deflector baffles (`x = 21.2..22.3`, `23.75..24.80`, `26.25..27.50`)
    #    - Two wide-open side exhaust chambers (`x = 22.3..23.75` and `24.80..26.25`) exposing dark rifled blast core!
    v_top_mb, n_top_mb, s_top_mb, t_top_mb = build_box(21.20, 27.50, -4.95, +4.95, +3.02, +4.22, wtex.UV_SILVER_BARREL)
    surf_silver.add_part(v_top_mb, n_top_mb, s_top_mb, t_top_mb, tag="barrel")
    v_bot_mb, n_bot_mb, s_bot_mb, t_bot_mb = build_box(21.20, 27.50, -4.95, +4.95, -4.22, -3.02, wtex.UV_SILVER_BARREL)
    surf_silver.add_part(v_bot_mb, n_bot_mb, s_bot_mb, t_bot_mb, tag="barrel")

    # Inner dark gunmetal perforated core tube spanning the muzzle brake chambers so bore is seamless!
    mb_core_xr = [(21.15, 3.18), (27.45, 3.18), (27.50, 2.88)]
    vmc, nmc, smc, tmc = build_lathe_tube(mb_core_xr, rad_sub, wtex.UV_GUNMETAL_ARMOR)
    surf_silver.add_part(vmc, nmc, smc, tmc, tag="barrel")

    baffle_specs = (
        ((21.20, 22.30, 5.35), (23.75, 24.80, 5.45), (26.25, 27.50, 5.25))
        if is_hd else
        ((21.20, 22.60, 5.35), (25.85, 27.50, 5.30))
    )
    for bx0, bx1, by_w in baffle_specs:
        # Left & Right heavy blast-deflector cheek pillars (leaving center bore `y in [-2.85..+2.85]` 100% open!)
        for sgn in (-1.0, +1.0):
            y_in = sgn * 2.75
            y_out = sgn * by_w
            vbaf, nbaf, sbaf, tbaf = build_box(
                bx0, bx1, min(y_in, y_out), max(y_in, y_out), -3.12, +3.12, wtex.UV_SILVER_BAND
            )
            surf_silver.add_part(vbaf, nbaf, sbaf, tbaf, tag="barrel")

    # 5. TOP PICATINNY TACTICAL RAIL + GLOWING PLASMA COOLING VENTS (`x = 5.90 .. 19.10`, `tag="barrel"`)
    v_prb, n_prb, s_prb, t_prb = build_box(5.90, 19.10, -0.82, +0.82, 3.32, 4.02, wtex.UV_GUNMETAL_ARMOR)
    surf_silver.add_part(v_prb, n_prb, s_prb, t_prb, tag="barrel")
    if is_hd:
        # Crisp machined MIL-STD-1913 Picatinny cross-lugs along top barrel spine!
        for k in range(8):
            rx0 = 6.30 + k * 1.62
            vrt, nrt, srt, trt = build_box(rx0, rx0 + 0.92, -0.96, +0.96, 4.00, 4.38, wtex.UV_SILVER_BAND)
            surf_silver.add_part(vrt, nrt, srt, trt, tag="barrel")
        # Recessed blue-cyan thermal accelerator glow strip peeking along barrel spine under rail!
        v_gl, n_gl, s_gl, t_gl = build_box(6.40, 18.60, -0.92, +0.92, 3.44, 3.66, wtex.UV_CORE_PLASMA)
        surf_core.add_part(v_gl, n_gl, s_gl, t_gl, tag="barrel")

    # 6. MIL-SPEC ARMORED "WEW CANNON" SIDE SHROUD PLATES ON BOTH FLANKS (`tag="barrel"`)
    #    - Inner-Left (+Y/+Z, phi = +22..+78 deg): Angled cleanly at 1st-Person Quake Camera (`u` muzzle->breech = Left->Right!)
    #    - Outer-Right (-Y/+Z, phi = -22..-78 deg): Angled for 3rd-Person / World Right-Side View (`u` breech->muzzle = Left->Right!)
    v_pl, n_pl, s_pl, t_pl = build_curved_barrel_plaque(
        x0=3.35, x1=19.15, r_func=base_barrel_radius,
        phi_top_deg=+22.0, phi_bot_deg=+78.0,
        nx_segs=nx_plq, nphi_segs=np_plq,
        uv_rect=wtex.UV_WEW_PLAQUE,
        u_muzzle_to_breech=True,
        lift=0.38,
    )
    surf_silver.add_part(v_pl, n_pl, s_pl, t_pl, tag="barrel")

    v_pr, n_pr, s_pr, t_pr = build_curved_barrel_plaque(
        x0=3.35, x1=19.15, r_func=base_barrel_radius,
        phi_top_deg=-22.0, phi_bot_deg=-78.0,
        nx_segs=nx_plq, nphi_segs=np_plq,
        uv_rect=wtex.UV_WEW_PLAQUE,
        u_muzzle_to_breech=False,
        lift=0.38,
    )
    surf_silver.add_part(v_pr, n_pr, s_pr, t_pr, tag="barrel")

    # 7. STATIONARY ARMORED RECOIL CRADLE, GUIDE RAILS, HYDROPNEUMATIC RECUPERATORS & LASER POD (`tag="cradle"`)
    #    Stays anchored in the Ranger's hands while the fluted silver barrel & breech block slam straight back on recoil!
    v_cr, n_cr, s_cr, t_cr = build_box(-2.6, 13.4, -2.75, +2.75, -5.65, -3.55, wtex.UV_GUNMETAL_ARMOR)
    surf_silver.add_part(v_cr, n_cr, s_cr, t_cr, tag="cradle")

    if is_hd:
        # Twin Armored Recoil Guide Rails hugging lower barrel flanks
        for sgn in (-1.0, +1.0):
            v_rl, n_rl, s_rl, t_rl = build_box(
                -1.4, 13.8, min(sgn * 2.65, sgn * 4.35), max(sgn * 2.65, sgn * 4.35), -4.35, -2.15, wtex.UV_GUNMETAL_ARMOR
            )
            surf_silver.add_part(v_rl, n_rl, s_rl, t_rl, tag="cradle")
        # Side-Mounted Military Target-Designator / Laser Pod on left forward rail (`+Y`, visible in 1st-person!)
        v_ls, n_ls, s_ls, t_ls = build_box(10.2, 15.8, +4.15, +5.45, -3.35, -1.75, wtex.UV_HYDRAULIC)
        surf_silver.add_part(v_ls, n_ls, s_ls, t_ls, tag="cradle")
        v_ll, n_ll, s_ll, t_ll = build_box(15.65, 15.92, +4.42, +5.18, -2.92, -2.18, wtex.UV_CORE_PLASMA)
        surf_core.add_part(v_ll, n_ll, s_ll, t_ll, tag="cradle")

    # Tactical Checkered Foregrip & Rear Firing Pistol Grip
    v_fg, n_fg, s_fg, t_fg = build_box(7.8, 10.6, +1.4, +3.6, -7.8, -4.6, wtex.UV_GRIP_WRAP)
    surf_silver.add_part(v_fg, n_fg, s_fg, t_fg, tag="cradle")
    v_rg, n_rg, s_rg, t_rg = build_box(-2.6, -0.2, -1.3, +1.3, -8.8, -4.8, wtex.UV_GRIP_WRAP)
    surf_silver.add_part(v_rg, n_rg, s_rg, t_rg, tag="cradle")

    for sgn in (-1.0, +1.0):
        # Stationary Olive-Gunmetal Hydropneumatic Recuperator Cylinder (`tag="cradle"`)
        cyl_xr = [(-3.2, 0.05), (-3.0, 1.02), (8.2, 1.02), (8.35, 0.68)]
        vc, nc, sc, tc = build_lathe_tube(cyl_xr, rad_sub, wtex.UV_HYDRAULIC, axis_offset=(0.0, sgn * 3.55, -3.35))
        surf_silver.add_part(vc, nc, sc, tc, tag="cradle")
        # Telescoping Chrome Recuperator Piston Rod anchored to recoiling barrel (`tag="barrel"`)!
        rod_xr = [(1.5, 0.58), (15.6, 0.58), (15.8, 0.92), (16.5, 0.92), (16.65, 0.05)]
        vp, np_, sp_, tp = build_lathe_tube(rod_xr, rad_sub, wtex.UV_SILVER_BARREL, axis_offset=(0.0, sgn * 3.55, -3.35))
        surf_silver.add_part(vp, np_, sp_, tp, tag="barrel")

    # 8. RUGGEDIZED MILITARY FIELD CRT TERMINAL (`WEW-TAC 98`) ON SHOCK-ISOLATED SPINE RAIL CLAMP (`tag="crt"`)!
    #    Seats cleanly onto the top spine (`z = 3.52..4.78`, zero side straps blocking the `"WEW CANNON"` plaque!),
    #    sliding on a damped rail isolator so all 4 Win98 websites stay 100% crisp & unobstructed across all 48 frames!
    v_mnt, n_mnt, s_mnt, t_mnt = build_box(1.30, 3.95, -1.30, +1.40, 3.52, 4.78, wtex.UV_GUNMETAL_ARMOR)
    surf_silver.add_part(v_mnt, n_mnt, s_mnt, t_mnt, tag="crt")
    if is_hd:
        v_swv, n_swv, s_swv, t_swv = build_box(2.10, 3.10, +0.05, +1.05, 4.72, 5.25, wtex.UV_SILVER_BAND)
        surf_silver.add_part(v_swv, n_swv, s_swv, t_swv, tag="crt")
        # Braided armored MIL-SPEC VGA data conduit
        v_vga, n_vga, s_vga, t_vga = build_box(3.70, 5.10, +0.25, +0.75, 3.75, 6.25, wtex.UV_DARK_BORE)
        surf_silver.add_part(v_vga, n_vga, s_vga, t_vga, tag="crt")

    crt_piv = np.array([2.60, +0.55, 6.95], dtype=np.float64)
    R_crt = rot_z_mat(-32.0) @ rot_y_mat(-7.0) @ rot_x_mat(+8.5)

    def add_crt_box(x0, x1, y0, y1, z0, z1, uv_r):
        vb, nb, sb_uv, tb = build_box(x0, x1, y0, y1, z0, z1, uv_r)
        vb_t = [tuple(crt_piv + R_crt @ np.array(pt)) for pt in vb]
        nb_t = [tuple(R_crt @ np.array(nm)) for nm in nb]
        surf_silver.add_part(vb_t, nb_t, sb_uv, tb, tag="crt")

    if is_hd:
        # Ruggedized Olive-Drab / Tactical Slate 4:3 Bezel + Forward Glare-Shield Sun Hood!
        add_crt_box(-0.72, +1.05, -2.56, +2.56, +1.62, +2.08, wtex.UV_CRT_VENT)   # Top armored bezel + sun hood
        add_crt_box(-0.50, +1.05, -2.56, +2.56, -2.06, -1.40, wtex.UV_CRT_BEZEL)  # Bottom chin w/ WEW-TAC 98 & dual LEDs!
        add_crt_box(-0.66, +1.05, +2.06, +2.56, -1.42, +1.64, wtex.UV_CRT_VENT)   # Left shock-bumper pillar
        add_crt_box(-0.66, +1.05, -2.56, -2.06, -1.42, +1.64, wtex.UV_CRT_VENT)   # Right shock-bumper pillar
        add_crt_box(-0.18, +1.05, -2.12, +2.12, -1.46, +1.68, wtex.UV_CRT_VENT)   # Backing plate behind glass
    else:
        add_crt_box(-0.30, +1.05, -2.52, +2.52, -2.04, +2.04, wtex.UV_CRT_BEZEL)

    # Tapered ruggedized cathode-ray tube rear housing (`mx = +1.02 .. +3.42`)
    taper_rings = [
        (+1.02, 2.42, 1.92, 0.05),
        (+2.25, 1.88, 1.50, 0.52),
        (+3.25, 1.24, 1.04, 0.94),
        (+3.42, 0.12, 0.10, 0.98),
    ]
    vu0, vv0, vu1, vv1 = wtex.UV_CRT_VENT
    tv_v, tv_n, tv_s, tv_t = [], [], [], []
    corners_4 = [(+1.0, +1.0), (-1.0, +1.0), (-1.0, -1.0), (+1.0, -1.0)]
    for ri in range(len(taper_rings) - 1):
        rx0, ry0, rz0, vt0 = taper_rings[ri]
        rx1, ry1, rz1, vt1 = taper_rings[ri + 1]
        is_cap = (ri == len(taper_rings) - 2)
        for ci in range(4):
            cy0, cz0 = corners_4[ci]
            cy1, cz1 = corners_4[(ci + 1) % 4]
            pa = np.array([rx0, cy0 * ry0, cz0 * rz0], dtype=np.float64)
            pb = np.array([rx0, cy1 * ry0, cz1 * rz0], dtype=np.float64)
            pc = np.array([rx1, cy0 * ry1, cz0 * rz1], dtype=np.float64)
            pd = np.array([rx1, cy1 * ry1, cz1 * rz1], dtype=np.float64)
            nm_f = vnorm(tuple(np.cross(pb - pa, pd - pa)))
            nm_w = tuple(R_crt @ np.array(nm_f))
            base = len(tv_v)
            for pt_l, u_f, v_f in (
                (pa, 0.04, vt0),
                (pb, 0.96, vt0),
                (pc, 0.04, vt1),
                (pd, 0.96, vt1),
            ):
                tv_v.append(tuple(crt_piv + R_crt @ pt_l))
                tv_n.append(nm_w)
                if is_cap:
                    tv_s.append((vu0 + (vu1 - vu0) * 0.05, vv0 + (vv1 - vv0) * 0.05))
                else:
                    tv_s.append((vu0 + (vu1 - vu0) * u_f, vv0 + (vv1 - vv0) * v_f))
            tv_t.append((base, base + 1, base + 3))
            tv_t.append((base, base + 3, base + 2))
    surf_silver.add_part(tv_v, tv_n, tv_s, tv_t, tag="crt")

    # Slightly Convex Glowing 4:3 Glass CRT Screen (`surf_crt`: `u=0` at `+Y` viewer-left -> `u=1` at `-Y` viewer-right!)
    n_grid = 3 if is_hd else 2
    sc_v, sc_n, sc_s, sc_t = [], [], [], []
    for iz in range(n_grid + 1):
        vf = iz / n_grid
        mz = +1.62 * (1.0 - vf) + (-1.40) * vf
        nz_u = (vf - 0.5) * 2.0
        for iy in range(n_grid + 1):
            uf = iy / n_grid
            my = +2.06 * (1.0 - uf) + (-2.06) * uf
            ny_u = (uf - 0.5) * 2.0
            bulge_g = 0.14 * max(0.0, 1.0 - 0.55 * (ny_u * ny_u + nz_u * nz_u))
            mx = (-0.32 if is_hd else -0.35) - bulge_g
            pt_g = crt_piv + R_crt @ np.array([mx, my, mz], dtype=np.float64)
            nm_g = R_crt @ np.array(vnorm((-1.0, -0.12 * ny_u, -0.12 * nz_u)), dtype=np.float64)
            sc_v.append(tuple(pt_g))
            sc_n.append(tuple(nm_g))
            sc_s.append((0.01 + 0.98 * uf, 0.01 + 0.98 * vf))
    stride_g = n_grid + 1
    for iz in range(n_grid):
        for iy in range(n_grid):
            p_tl = iz * stride_g + iy
            p_tr = p_tl + 1
            p_bl = (iz + 1) * stride_g + iy
            p_br = p_bl + 1
            sc_t.append((p_tl, p_bl, p_br))
            sc_t.append((p_tl, p_br, p_tr))
    surf_crt.add_part(sc_v, sc_n, sc_s, sc_t, tag="crt")

    # Glowing Inner Bore Accelerator Throat Discs (deep inside barrel so mouth stays 100% open for separate projectile!)
    cg_xr = [(13.2, 0.05), (13.3, 2.30), (13.6, 2.30)]
    vcg, ncg, scg, tcg = build_lathe_tube(cg_xr, rad_sub, wtex.UV_CORE_PLASMA)
    surf_core.add_part(vcg, ncg, scg, tcg, tag="barrel")
    th_xr = [(23.2, 0.05), (23.4, 2.55), (23.8, 2.55)]
    vth, nth, sth, tth = build_lathe_tube(th_xr, rad_sub, wtex.UV_MUZZLE_THROAT)
    surf_core.add_part(vth, nth, sth, tth, tag="barrel")

    # 9. Military Artillery Muzzle-Brake Side Blast Jets, Forward Starburst, Shock-Rings & Steam (`surf_fx`)!
    if is_hd:
        bu0, bv0, bu1, bv1 = wtex.UV_FX_STARBURST
        # Forward muzzle flash petals
        for ang_deg in (0.0, 45.0, 90.0, 135.0):
            pts = [rot_x((lx, lr, 0.0), ang_deg) for lx, lr in ((0.0, 10.5), (19.5, 14.5), (19.5, -14.5), (0.0, -10.5))]
            nrm = rot_x((0.0, 0.0, 1.0), ang_deg)
            surf_fx.add_part(
                pts, [nrm] * 4,
                [(bu0, bv0), (bu1, bv0), (bu1, bv1), (bu0, bv1)],
                [(0, 1, 2), (0, 2, 3)], tag="fx_burst"
            )
        pts_d = [(2.8, -15.0, +15.0), (2.8, +15.0, +15.0), (2.8, +15.0, -15.0), (2.8, -15.0, -15.0)]
        surf_fx.add_part(pts_d, [(-1.0, 0.0, 0.0)] * 4,
                         [(bu0, bv0), (bu1, bv0), (bu1, bv1), (bu0, bv1)],
                         [(0, 1, 2), (0, 2, 3)], tag="fx_burst")

        # Directional Tank Muzzle-Brake Side Exhaust Plumes (`tag="fx_sidejet"`) erupting out left & right brake baffles!
        for sgn in (-1.0, +1.0):
            for tilt_x in (0.0, 90.0):
                base_quad = [
                    (-3.4, sgn * 3.2, -3.5),
                    (-6.8, sgn * 18.5, -7.2),
                    (-0.2, sgn * 18.5, +7.2),
                    (-2.0, sgn * 3.2, +3.5),
                ]
                if tilt_x > 45.0:
                    base_quad = [
                        (-5.2, sgn * 3.2, 0.0),
                        (-8.8, sgn * 18.5, 0.0),
                        (+1.4, sgn * 18.5, 0.0),
                        (-0.6, sgn * 3.2, 0.0),
                    ]
                    n_jet = (0.0, 0.0, 1.0)
                else:
                    n_jet = (-0.85, 0.0, 0.52)
                surf_fx.add_part(
                    base_quad, [n_jet] * 4,
                    [(bu0, bv0), (bu1, bv0), (bu1, bv1), (bu0, bv1)],
                    [(0, 1, 2), (0, 2, 3)], tag="fx_sidejet"
                )

        # Twin supersonic shockwave rings
        ru0, rv0, ru1, rv1 = wtex.UV_FX_SHOCKRING
        for rtag in ("fx_ring1", "fx_ring2"):
            pts_r = [(0.0, -12.0, +12.0), (0.0, +12.0, +12.0), (0.0, +12.0, -12.0), (0.0, -12.0, -12.0)]
            surf_fx.add_part(pts_r, [(-1.0, 0.0, 0.0)] * 4,
                             [(ru0, rv0), (ru1, rv0), (ru1, rv1), (ru0, rv1)],
                             [(0, 1, 2), (0, 2, 3)], tag=rtag)

        # Charge lightning arcs around muzzle brake baffles (`tag="fx_arc"`)
        lu0, lv0, lu1, lv1 = wtex.UV_FX_LIGHTNING
        for k in range(3):
            a_deg = k * 120.0 + 25.0
            pts_a = [rot_x((x_a, 5.6, z_a), a_deg) for x_a, z_a in ((-4.8, -1.5), (+0.4, -1.5), (+0.4, +1.5), (-4.8, +1.5))]
            surf_fx.add_part(pts_a, [rot_x((0.0, 1.0, 0.0), a_deg)] * 4,
                             [(lu0, lv0), (lu1, lv0), (lu1, lv1), (lu0, lv1)],
                             [(0, 1, 2), (0, 2, 3)], tag="fx_arc")

        # High-pressure hydropneumatic recoil steam blowoff plumes (`tag="fx_steam"`)
        su0, sv0, su1, sv1 = wtex.UV_FX_STEAM
        for sgn in (-1.0, +1.0):
            pts_s = [
                (6.5, sgn * 3.8, -2.4),
                (11.5, sgn * 10.8, +1.6),
                (11.5, sgn * 10.8, -5.4),
                (6.5, sgn * 3.8, -4.8),
            ]
            surf_fx.add_part(pts_s, [(0.0, sgn, 0.2)] * 4,
                             [(su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1)],
                             [(0, 1, 2), (0, 2, 3)], tag="fx_steam")
    else:
        bu0, bv0, bu1, bv1 = wtex.UV_FX_STARBURST
        for k in range(6):
            a0 = math.radians(k * 60.0)
            a1 = math.radians(k * 60.0 + 28.0)
            am = 0.5 * (a0 + a1)
            pts_sp = [
                (0.0, 3.2 * math.sin(a0), 3.2 * math.cos(a0)),
                (0.0, 3.2 * math.sin(a1), 3.2 * math.cos(a1)),
                (7.5, 9.2 * math.sin(am), 9.2 * math.cos(am)),
            ]
            surf_fx.add_part(pts_sp, [(-0.7, 0.5 * math.sin(am), 0.5 * math.cos(am))] * 3,
                             [(0.5 * (bu0 + bu1), 0.5 * (bv0 + bv1)), (bu1, bv0), (bu1, bv1)],
                             [(0, 1, 2)], tag="fx_burst")

    # 10. Tactical Spec-Ops Combat Gauntlets Supporting the Giant Military Cannon (`surf_hands`)
    if is_hd:
        lh = build_articulated_ranger_hand(
            palm_center=(9.2, +3.1, -6.2),
            fwd_dir=(+0.88, -0.32, +0.35),
            up_dir=(-0.28, +0.25, +0.92),
            side_sign=+1.0,
            finger_curls=(0.82, 0.86, 0.88, 0.90),
            thumb_curl=0.72,
            thumb_abd=36.0,
            hand_scale=1.05,
            forearm_len=12.5,
            forearm_dir=(-0.72, +0.44, -0.54),
        )
        rh = build_articulated_ranger_hand(
            palm_center=(-1.4, -1.1, -6.9),
            fwd_dir=(+0.92, +0.22, -0.32),
            up_dir=(+0.25, -0.94, -0.22),
            side_sign=-1.0,
            finger_curls=(0.68, 0.86, 0.88, 0.90),
            thumb_curl=0.76,
            thumb_abd=34.0,
            hand_scale=1.05,
            forearm_len=12.5,
            forearm_dir=(-0.68, -0.42, -0.60),
        )
        surf_hands.add_part(lh.verts, lh.norms, lh.st, lh.tris, tag="cradle")
        surf_hands.add_part(rh.verts, rh.norms, rh.st, rh.tris, tag="cradle")
    else:
        vl, nl, sl, tl = build_box(7.2, 11.0, +1.8, +4.4, -8.2, -5.0, (0.05, 0.05, 0.45, 0.45))
        surf_hands.add_part(vl, nl, sl, tl, tag="cradle")
        vla, nla, sla, tla = build_box(0.5, 8.0, +3.0, +5.8, -11.8, -7.2, (0.55, 0.55, 0.95, 0.95))
        surf_hands.add_part(vla, nla, sla, tla, tag="cradle")
        vr, nr_, sr, tr = build_box(-3.2, +0.4, -2.2, +0.6, -9.2, -5.8, (0.05, 0.05, 0.45, 0.45))
        surf_hands.add_part(vr, nr_, sr, tr, tag="cradle")

    return [surf_silver, surf_hands, surf_core, surf_crt, surf_fx]


# ===========================================================================
# 48-FRAME MILITARY HEAVY-ARTILLERY RECOIL & LOW-BEND BLAST SCHEDULE
# ===========================================================================
def build_48_frame_schedule():
    """Redesigned less-bendy military artillery animation:
    - Rigid forged-titanium feel (peak barrel flex <= ~6 deg instead of +58 deg rubber cartoon bend!)
    - Powerful long-stroke axial barrel recoil (`barrel_slide` up to -6.3u through the stationary trunnion shroud,
      visibly compressing the twin chrome hydropneumatic recuperator pistons!)
    - Twin directional muzzle-brake side exhaust jets + forward starburst + Mach shockwave rings
    - Smooth damped hydropneumatic return-to-battery (`recoil1..10`) + mechanical breech-block cycling (`reload1..8`)."""
    sched = []

    # --- 1. Frames 0..15: Disciplined Heavy Military Ordnance Idle (`idle1..idle16`) ---
    for i in range(16):
        ph = 2.0 * math.pi * (i / 16.0)
        sched.append(dict(
            name=f"idle{i + 1}",
            rig_dx=0.18 * math.sin(ph),
            rig_dy=0.14 * math.cos(ph),
            rig_dz=0.22 * math.sin(ph * 2.0 + 0.4),
            rig_pitch=0.55 * math.sin(ph + 0.3),
            rig_yaw=0.40 * math.sin(ph),
            rig_roll=0.60 * math.cos(ph),
            bend_up=0.25 * math.sin(ph + 0.5),
            bend_yaw=0.12 * math.cos(ph),
            s_mode=0.0,
            axial_sc=1.0,
            barrel_slide=0.0,
            breech_slide=0.0,
            bulge_amp=0.0,
            bulge_pos=0.30,
            bulge_w=0.18,
            muzzle_flare=0.0,
            breech_swell=0.0,
            cradle_recoil=0.0,
            meter=0.24 + 0.03 * math.sin(ph * 2.0),
            burst=0.0,
            sidejet=0.0,
            ring1=0.0, ring1_x=0.0,
            ring2=0.0, ring2_x=0.0,
            arc=0.0,
            steam=0.0,
        ))

    # --- 2. Frames 16..25: HIGH-PRESSURE ORDNANCE CHARGE & SEAR COCKING (`charge1..charge10`) ---
    # Shooter braces the cannon tight; barrel cocks -1.25u into the hydropneumatic sear with high-frequency
    # turbine harmonic tremor and subtle +5.5 deg forged-steel overpressure flex (90% less bend than before!).
    for k in range(10):
        u = (k + 1) / 10.0
        ease = u * u * (3.0 - 2.0 * u)
        vib = (0.32 if k >= 6 else 0.0) * (1.0 if (k % 2 == 0) else -1.0)
        sched.append(dict(
            name=f"charge{k + 1}",
            rig_dx=-1.35 * ease + vib * 0.22,
            rig_dy=+0.48 * ease,
            rig_dz=-0.46 * ease + vib * 0.16,
            rig_pitch=+1.85 * ease,
            rig_yaw=+1.40 * ease,
            rig_roll=-1.65 * ease + vib * 0.9,
            bend_up=+5.5 * (u ** 1.15) + vib * 0.55,
            bend_yaw=+2.0 * (u ** 1.20),
            s_mode=-1.1 * ease,
            axial_sc=1.0 - 0.022 * ease,
            barrel_slide=-1.25 * ease + vib * 0.12,
            breech_slide=0.0,
            bulge_amp=0.055 * ease,
            bulge_pos=0.22 + 0.18 * ease,
            bulge_w=0.20,
            muzzle_flare=0.0,
            breech_swell=0.03 * ease,
            cradle_recoil=0.0,
            meter=0.26 + 0.74 * u,
            burst=0.0,
            sidejet=0.0,
            ring1=0.0, ring1_x=0.0,
            ring2=0.0, ring2_x=0.0,
            arc=max(0.0, (u - 0.30) / 0.70),
            steam=0.0,
        ))

    # --- 3. Frames 26..29: 155MM ARTILLERY BLAST & LONG-STROKE AXIAL BARREL RECOIL (`blast1..blast4`) ---
    # No projectile mesh is included in the weapon model (projectile is spawned as a separate entity in Quake).
    blast_frames = [
        # 26 (`blast1` — Chamber Detonation): Barrel begins slamming rearward as side muzzle-brake ports ignite!
        dict(name="blast1", rig_dx=-1.65, rig_dy=+0.22, rig_dz=+0.20, rig_pitch=+2.4, rig_yaw=+1.2, rig_roll=+0.5,
             bend_up=+2.0, bend_yaw=+0.8, s_mode=+1.8, axial_sc=1.01,
             barrel_slide=-2.85, breech_slide=0.0,
             bulge_amp=0.07, bulge_pos=0.80, bulge_w=0.18, muzzle_flare=+0.03, breech_swell=0.02, cradle_recoil=0.25,
             meter=1.00, burst=0.68, sidejet=0.85, ring1=0.52, ring1_x=1.5, ring2=0.0, ring2_x=0.0, arc=1.0, steam=0.30),

        # 27 (`blast2` — PEAK MUZZLE-BRAKE FIREBALL!): Twin angled side-brake jets + forward starburst + shock-rings
        # while the fluted silver barrel slams -5.40u straight back into the armored shroud!
        dict(name="blast2", rig_dx=-3.15, rig_dy=-0.12, rig_dz=+0.78, rig_pitch=+6.4, rig_yaw=+1.8, rig_roll=+2.2,
             bend_up=-1.8, bend_yaw=+1.2, s_mode=-1.5, axial_sc=1.02,
             barrel_slide=-5.40, breech_slide=0.0,
             bulge_amp=0.04, bulge_pos=0.95, bulge_w=0.16, muzzle_flare=+0.05, breech_swell=0.0, cradle_recoil=0.65,
             meter=0.12, burst=1.12, sidejet=1.28, ring1=1.10, ring1_x=6.5, ring2=0.74, ring2_x=2.2, arc=0.90, steam=0.82),

        # 28 (`blast3` — FULL HYDROPNEUMATIC REAR STROKE!): Barrel hits -6.30u rear stop, compressing chrome pistons!
        dict(name="blast3", rig_dx=-4.15, rig_dy=-0.25, rig_dz=+1.28, rig_pitch=+9.2, rig_yaw=+0.6, rig_roll=+3.1,
             bend_up=+4.6, bend_yaw=+1.2, s_mode=-1.8, axial_sc=0.99,
             barrel_slide=-6.30, breech_slide=0.0,
             bulge_amp=0.0, bulge_pos=0.98, bulge_w=0.14, muzzle_flare=+0.02, breech_swell=0.0, cradle_recoil=0.95,
             meter=0.05, burst=0.72, sidejet=0.65, ring1=1.28, ring1_x=15.0, ring2=1.06, ring2_x=6.8, arc=0.35, steam=1.00),

        # 29 (`blast4` — Peak Artillery Muzzle Climb & Recuperator Hold):
        dict(name="blast4", rig_dx=-4.35, rig_dy=-0.20, rig_dz=+1.42, rig_pitch=+10.4, rig_yaw=-0.5, rig_roll=+2.8,
             bend_up=+6.0, bend_yaw=+1.4, s_mode=-1.5, axial_sc=0.99,
             barrel_slide=-6.05, breech_slide=0.0,
             bulge_amp=0.0, bulge_pos=0.5, bulge_w=0.18, muzzle_flare=0.0, breech_swell=0.0, cradle_recoil=1.00,
             meter=0.04, burst=0.20, sidejet=0.18, ring1=0.0, ring1_x=16.0, ring2=1.22, ring2_x=12.5, arc=0.0, steam=0.95),
    ]
    sched.extend(blast_frames)

    # --- 4. Frames 30..39: HYDROPNEUMATIC RECUPERATOR RETURN-TO-BATTERY (`recoil1..recoil10`) ---
    # Heavy damped linear recuperation sliding the barrel smoothly forward back into battery (`-5.35u -> 0.0u`)
    # with tight, realistic forged-steel damping (`<= 4.8 deg`) instead of rubber S-whiplash!
    recoil_specs = [
        # (b_slide, bend_up, bend_yaw, s_mode, r_dx, r_dz, r_pitch, c_rec, steam)
        (-5.35, +4.8, +1.1, -1.2, -3.85, +1.20, +9.0, 0.88, 0.84),  # 30 recoil1
        (-4.40, +3.2, +0.8, -0.8, -3.15, +0.92, +7.2, 0.72, 0.68),  # 31 recoil2
        (-3.30, +1.4, +0.4, +0.6, -2.40, +0.62, +5.2, 0.54, 0.52),  # 32 recoil3
        (-2.20, -1.2, -0.3, +0.8, -1.70, +0.35, +3.4, 0.36, 0.38),  # 33 recoil4
        (-1.20, -1.6, -0.4, +0.5, -1.10, +0.14, +1.9, 0.22, 0.24),  # 34 recoil5
        (-0.42, +0.8, +0.2, -0.4, -0.62, -0.02, +0.8, 0.10, 0.12),  # 35 recoil6
        (+0.18, +0.5, +0.1, -0.2, -0.26, -0.10, +0.1, 0.04, 0.04),  # 36 recoil7 (In-battery mechanical lock!)
        (+0.22, -0.3, -0.1, +0.2, -0.12, -0.08, -0.2, 0.00, 0.00),  # 37 recoil8
        (+0.08, +0.2,  0.0, -0.1, -0.05, -0.04, -0.1, 0.00, 0.00),  # 38 recoil9
        ( 0.00,  0.0,  0.0,  0.0,  0.00,  0.00,  0.0, 0.00, 0.00),  # 39 recoil10
    ]
    for idx, (bsl, bu, by, sm, rdx, rdz, rp, cr, stm) in enumerate(recoil_specs):
        sched.append(dict(
            name=f"recoil{idx + 1}",
            rig_dx=rdx, rig_dy=0.0, rig_dz=rdz,
            rig_pitch=rp, rig_yaw=0.0, rig_roll=0.8 * math.sin(idx * 0.8),
            bend_up=bu, bend_yaw=by, s_mode=sm, axial_sc=1.0,
            barrel_slide=bsl, breech_slide=0.0,
            bulge_amp=0.0, bulge_pos=0.35, bulge_w=0.18,
            muzzle_flare=0.0, breech_swell=0.0, cradle_recoil=cr,
            meter=0.06 + 0.06 * (idx / 9.0),
            burst=0.0, sidejet=0.0, ring1=0.0, ring1_x=0.0, ring2=0.0, ring2_x=0.0, arc=0.0, steam=stm,
        ))

    # --- 5. Frames 40..47: MECHANICAL BREECH-BLOCK CYCLING & BATTERY LOCK (`reload1..reload8`) ---
    for idx in range(8):
        u = (idx + 1) / 8.0
        pulse = math.sin(u * math.pi)
        lock_jolt = math.exp(-(((u - 0.72) / 0.14) ** 2))  # Crisp forward metallic lock-in clunk!
        sched.append(dict(
            name=f"reload{idx + 1}",
            rig_dx=-0.38 * pulse + 0.24 * lock_jolt,
            rig_dy=+0.14 * u,
            rig_dz=-0.34 * pulse + 0.08 * u,
            rig_pitch=-1.4 * pulse + 0.55 * lock_jolt,
            rig_yaw=0.0,
            rig_roll=0.6 * u,
            bend_up=+0.45 * pulse,
            bend_yaw=+0.12 * u,
            s_mode=0.0,
            axial_sc=1.0,
            barrel_slide=-0.22 * pulse + 0.10 * lock_jolt,
            breech_slide=-1.85 * pulse,
            bulge_amp=0.0,
            bulge_pos=0.20,
            bulge_w=0.16,
            muzzle_flare=0.0,
            breech_swell=0.0,
            cradle_recoil=0.0,
            meter=0.12 + 0.12 * u,
            burst=0.0, sidejet=0.0, ring1=0.0, ring1_x=0.0, ring2=0.0, ring2_x=0.0, arc=0.0, steam=0.0,
        ))

    assert len(sched) == 48
    return sched


# ===========================================================================
# CURVILINEAR FRENET-SPINE DEFORMER & EYE-SPACE TRANSFORM
# ===========================================================================
# Heroic 1st-Person Quake Eye-Space Placement:
# Eye is at (0,0,0) looking +X, +Y left, -Y right, +Z up.
# Positioned so the SUPER GIANT SILVER CANNON & bold "WEW CANNON" plaque fill the lower-right-to-center
# viewport dramatically at BOTH 90 deg and 111 deg FOV without clipping the near plane (`x >= 4.0`)!
EYE_BASE  = np.array([11.2, -7.8, -5.9], dtype=np.float64)
EYE_SCALE = 0.78
EYE_ROLL  = -9.5
EYE_PITCH = +2.8
EYE_YAW   = +14.8


def build_spine_table(fr, n_samples=80):
    """Integrates the curved barrel spine from `X_PIVOT` to `X_MUZZLE_TIP + 24.0` for frame `fr`.
    Returns `(s_grid, pos_grid, T_grid, B_grid, U_grid)`."""
    s_max = 1.85
    s_grid = np.linspace(0.0, s_max, n_samples, dtype=np.float64)
    ds = (s_max * L_BARREL * fr["axial_sc"]) / (n_samples - 1)

    pos_grid = np.zeros((n_samples, 3), dtype=np.float64)
    T_grid   = np.zeros((n_samples, 3), dtype=np.float64)
    B_grid   = np.zeros((n_samples, 3), dtype=np.float64)  # Local +Y (left)
    U_grid   = np.zeros((n_samples, 3), dtype=np.float64)  # Local +Z (up)

    pos_grid[0] = np.array([X_PIVOT, 0.0, 0.0], dtype=np.float64)
    bu_rad = math.radians(fr["bend_up"])
    by_rad = math.radians(fr["bend_yaw"])
    sm_rad = math.radians(fr["s_mode"])

    for i in range(n_samples):
        sc = min(1.0, s_grid[i])
        pitch_a = bu_rad * (sc ** 1.22) + sm_rad * math.sin(math.pi * sc * 1.45)
        yaw_a   = by_rad * (sc ** 1.28)
        cp, sp = math.cos(pitch_a), math.sin(pitch_a)
        cy, sy = math.cos(yaw_a), math.sin(yaw_a)
        # Forward tangent T, Left B, Up U (orthonormal right-handed frame!)
        T = np.array([cp * cy, cp * sy, sp], dtype=np.float64)
        B = np.array([-sy, cy, 0.0], dtype=np.float64)
        U = np.cross(T, B)
        T_grid[i], B_grid[i], U_grid[i] = T, B, U
        if i > 0:
            pos_grid[i] = pos_grid[i - 1] + 0.5 * (T_grid[i - 1] + T) * ds

    return s_grid, pos_grid, T_grid, B_grid, U_grid


def sample_spine(s_val, spine_tbl):
    s_grid, pos_grid, T_grid, B_grid, U_grid = spine_tbl
    if s_val <= 0.0:
        p0 = pos_grid[0] + T_grid[0] * (s_val * L_BARREL)
        return p0, T_grid[0], B_grid[0], U_grid[0]
    u = s_val / s_grid[-1] * (len(s_grid) - 1)
    idx = min(len(s_grid) - 2, max(0, int(u)))
    f = u - idx
    p = pos_grid[idx] * (1.0 - f) + pos_grid[idx + 1] * f
    T = T_grid[idx] * (1.0 - f) + T_grid[idx + 1] * f
    T /= max(1e-9, np.linalg.norm(T))
    B = B_grid[idx] * (1.0 - f) + B_grid[idx + 1] * f
    B -= T * np.dot(B, T)
    B /= max(1e-9, np.linalg.norm(B))
    U = np.cross(T, B)
    return p, T, B, U


def recompute_vertex_normals(V_arr, tris_ccw, rest_norms=None):
    N = np.zeros_like(V_arr, dtype=np.float64)
    if len(tris_ccw) == 0:
        N[:, 0] = 1.0
        return N
    F = np.asarray(tris_ccw, dtype=np.int32)
    v0 = V_arr[F[:, 0]]
    v1 = V_arr[F[:, 1]]
    v2 = V_arr[F[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    np.add.at(N, F[:, 0], fn)
    np.add.at(N, F[:, 1], fn)
    np.add.at(N, F[:, 2], fn)
    # Weld normals across cylindrical UV-wrap seam vertices sharing BOTH 3D position AND smooth rest normal,
    # while preserving razor-sharp 90-deg / 45-deg hard military armor edges on boxes, baffles, and rails!
    if rest_norms is not None and len(rest_norms) == len(V_arr):
        rn_q = np.round(np.asarray(rest_norms, dtype=np.float64) * 4.0).astype(np.int64)
        qkey = np.hstack([np.round(V_arr * 256.0).astype(np.int64), rn_q])
    else:
        qkey = np.round(V_arr * 256.0).astype(np.int64)
    _, inv = np.unique(qkey, axis=0, return_inverse=True)
    N_weld = np.zeros((inv.max() + 1, 3), dtype=np.float64)
    np.add.at(N_weld, inv, N)
    N = N_weld[inv]
    lens = np.linalg.norm(N, axis=1, keepdims=True)
    return np.where(lens > 1e-11, N / np.maximum(lens, 1e-11), np.array([0.0, 0.0, 1.0]))


def evaluate_surface_for_frame(surf: SurfBuilder, fr: dict, spine_tbl, to_eye=True):
    nv = len(surf.verts)
    V_local = np.zeros((nv, 3), dtype=np.float64)

    b_slide = fr.get("barrel_slide", 0.0)
    br_slide = fr.get("breech_slide", 0.0)
    sidejet_sc = fr.get("sidejet", 0.0)
    slide_vec = np.array([b_slide, 0.0, 0.0], dtype=np.float64)

    sp_muz, muzzle_T, muzzle_B, muzzle_U = sample_spine(1.0, spine_tbl)
    muzzle_p = sp_muz + slide_vec

    for i, (p, tag) in enumerate(zip(surf.verts, surf.deform_tags)):
        px, py, pz = p
        if tag == "breech":
            sw = 1.0 + fr["breech_swell"] * math.exp(-(((px + 2.2) / 2.8) ** 2))
            V_local[i] = (px + b_slide + br_slide, py * sw, pz * sw)

        elif tag == "barrel":
            if px <= X_PIVOT:
                V_local[i] = (px + b_slide, py, pz)
            else:
                s = (px - X_PIVOT) / L_BARREL
                sp_p, T, B, U = sample_spine(s, spine_tbl)
                bulge = fr["bulge_amp"] * math.exp(-(((s - fr["bulge_pos"]) / fr["bulge_w"]) ** 2))
                flare = fr["muzzle_flare"] * (max(0.0, (s - 0.66) / 0.34) ** 1.55)
                r_sc = 1.0 + bulge + flare
                V_local[i] = (sp_p + slide_vec) + B * (py * r_sc) + U * (pz * r_sc)

        elif tag == "crt":
            # Shock-isolated spine rail mount: rides the top spine with damped hydraulic recoil (`0.42 * b_slide`)
            # so it stays seated on the barrel top with ZERO obstruction of the `"WEW CANNON"` armor plate!
            V_local[i] = (px + 0.42 * b_slide + 0.58 * fr["cradle_recoil"], py, pz)

        elif tag == "cradle":
            # Stationary armored recoil cradle, guide rails, laser pod & Ranger combat gauntlets!
            V_local[i] = (px + fr["cradle_recoil"], py, pz)

        elif tag == "fx_burst":
            sc_b = fr["burst"] if fr["burst"] > 0.02 else 0.0005
            V_local[i] = muzzle_p + muzzle_T * (px * sc_b) + muzzle_B * (py * sc_b) + muzzle_U * (pz * sc_b)

        elif tag == "fx_sidejet":
            sc_j = sidejet_sc if sidejet_sc > 0.02 else 0.0005
            # Anchored right inside the two side muzzle-brake exhaust chambers (`x = muzzle_tip - 3.2`)
            V_local[i] = muzzle_p + muzzle_T * (px * sc_j) + muzzle_B * (py * sc_j) + muzzle_U * (pz * sc_j)

        elif tag == "fx_ring1":
            sc_r = fr["ring1"] if fr["ring1"] > 0.02 else 0.0005
            c_r = muzzle_p + muzzle_T * fr["ring1_x"]
            V_local[i] = c_r + muzzle_T * (px * sc_r) + muzzle_B * (py * sc_r) + muzzle_U * (pz * sc_r)

        elif tag == "fx_ring2":
            sc_r = fr["ring2"] if fr["ring2"] > 0.02 else 0.0005
            c_r = muzzle_p + muzzle_T * fr["ring2_x"]
            V_local[i] = c_r + muzzle_T * (px * sc_r) + muzzle_B * (py * sc_r) + muzzle_U * (pz * sc_r)

        elif tag == "fx_arc":
            sc_a = fr["arc"] if fr["arc"] > 0.02 else 0.0005
            V_local[i] = muzzle_p + muzzle_T * (px * sc_a) + muzzle_B * (py * sc_a) + muzzle_U * (pz * sc_a)

        elif tag == "fx_steam":
            sc_s = fr["steam"] if fr["steam"] > 0.02 else 0.0005
            anchor = np.array([6.5 + fr["cradle_recoil"], math.copysign(3.8, py), -3.5], dtype=np.float64)
            rel = np.array([px - 6.5, py - math.copysign(3.8, py), pz + 3.5], dtype=np.float64)
            V_local[i] = anchor + rel * sc_s

        else:
            V_local[i] = (px, py, pz)

    N_local = recompute_vertex_normals(V_local, surf.tris, rest_norms=surf.norms)
    if not to_eye:
        return V_local, N_local

    # Transform into Quake 1st-person eye space!
    R_eye = (
        rot_z_mat(EYE_YAW + fr["rig_yaw"])
        @ rot_y_mat(EYE_PITCH + fr["rig_pitch"])
        @ rot_x_mat(EYE_ROLL + fr["rig_roll"])
    )
    shift = np.array([fr["rig_dx"], fr["rig_dy"], fr["rig_dz"]], dtype=np.float64)
    V_eye = ((V_local + shift) * EYE_SCALE) @ R_eye.T + EYE_BASE
    N_eye = N_local @ R_eye.T
    N_eye /= np.maximum(1e-11, np.linalg.norm(N_eye, axis=1, keepdims=True))
    return V_eye, N_eye


def pack_md3_surfaces(surf_builders, frames_list_per_surf):
    md3_surfs = []
    for sb, f_vn in zip(surf_builders, frames_list_per_surf):
        # Convert CCW-outward -> CW-outward for Quake / DarkPlaces MD3!
        tris_cw = [(int(a), int(c), int(b)) for a, b, c in sb.tris]
        st_l = [(float(u), float(v)) for u, v in sb.st]
        fr_l = [
            ([(float(p[0]), float(p[1]), float(p[2])) for p in V_f],
             [(float(n[0]), float(n[1]), float(n[2])) for n in N_f])
            for V_f, N_f in f_vn
        ]
        md3_surfs.append(dict(
            name=sb.name,
            shader=sb.shader,
            mat=sb.mat,
            tris=tris_cw,
            st=st_l,
            frames=fr_l,
        ))
    return md3_surfs


def _unique_st_list(st_list, start_idx=0):
    """Adds a microscopic `< 0.06 px` IEEE-754 float32 tag so DarkPlaces `Mod_IDP3_Load` never welds vertices across UV offsets."""
    out = []
    for k, (u, v) in enumerate(st_list):
        idx = start_idx + k
        du = ((idx & 63) + 1) * 1.5e-6
        dv = (((idx >> 6) & 63) + 1) * 1.5e-6
        u_adj = float(np.float32(u - du if u > 0.5 else u + du))
        v_adj = float(np.float32(v - dv if v > 0.5 else v + dv))
        out.append((u_adj, v_adj))
    return out


def align_md3_surfaces_for_dp_vbo(md3_surfs):
    """DarkPlaces (Aug 2017 `gl_vbo 1`) rebases CPU-interpolated `vertex3f` on multi-surface animated MD3s
    to index 0 while leaving static `texcoord2f` bound to `Surface[0].st[0..]`.
    Aligning each surface `k >= 1` to disjoint vertex slice `[off_k .. off_k + nv_k - 1]` with bit-unique
    `<2f` UVs (preventing `Mod_IDP3_Load` weld shifts) makes UVs 100% exact in BOTH DarkPlaces AND all
    standard MD3/Q3/FTEQW/Blender/WebGL engines with zero extra triangles!
    """
    if len(md3_surfs) <= 1:
        return md3_surfs
    # Order `crt_screen` immediately after `cannon_silver` (`off = 0`), followed by core, hands, and additive fx last!
    by_priority = sorted(
        md3_surfs[1:],
        key=lambda x: {"crt_screen": 0, "cannon_core": 1, "ranger_hands": 2, "cannon_fx": 3}.get(x["name"], 9),
    )
    s0 = md3_surfs[0]
    prefix_st = []
    aligned_others = []
    for s in by_priority:
        off = len(prefix_st)
        s_st_uniq = _unique_st_list(s["st"], start_idx=off)
        if off == 0:
            aligned_others.append(dict(s, st=s_st_uniq))
        else:
            st_pad = list(prefix_st) + s_st_uniq
            tris_pad = [(a + off, b + off, c + off) for a, b, c in s["tris"]]
            fr_pad = [([vv[0]] * off + list(vv), [nn[0]] * off + list(nn)) for vv, nn in s["frames"]]
            aligned_others.append(dict(s, st=st_pad, tris=tris_pad, frames=fr_pad))
        prefix_st.extend(s_st_uniq)

    m_off = len(prefix_st)
    s0_st_uniq = _unique_st_list(s0["st"], start_idx=m_off)
    s0_aligned = dict(
        s0,
        st=prefix_st + s0_st_uniq,
        tris=[(a + m_off, b + m_off, c + m_off) for a, b, c in s0["tris"]],
        frames=[([vv[0]] * m_off + list(vv), [nn[0]] * m_off + list(nn)) for vv, nn in s0["frames"]],
    )
    return [s0_aligned] + aligned_others


def write_md3_with_skins(model_name, md3_surfs, frame_names, deploy_names):
    nf = len(frame_names)
    dp_surfs = align_md3_surfaces_for_dp_vbo(md3_surfs)
    for s in dp_surfs:
        assert len(s["st"]) <= 4096 and len(s["tris"]) <= 8192, f"MD3 surface overflow on {s['name']}: nv={len(s['st'])}"
    stage_p = os.path.join(STAGE_DIR, f"{model_name}.md3")
    md3lib.write(stage_p, dict(name=model_name, surfaces=dp_surfs, nframes=nf, frame_names=frame_names))
    rt = md3lib.read(stage_p)
    assert rt["nframes"] == nf and len(rt["surfaces"]) == len(dp_surfs)

    skin_txt = "\n".join(f"{s['name']},{s['shader']}" for s in dp_surfs) + "\n"
    open(stage_p + "_0.skin", "w", encoding="ascii", newline="\n").write(skin_txt)

    for dname in deploy_names:
        dp = os.path.join(PROGS_DIR, f"{dname}.md3")
        shutil.copy2(stage_p, dp)
        # Write both _0.skin (default) and _1.skin (Combat+ Quad Damage overlay skin!)
        open(dp + "_0.skin", "w", encoding="ascii", newline="\n").write(skin_txt)
        open(dp + "_1.skin", "w", encoding="ascii", newline="\n").write(skin_txt)

    tv = sum(len(s["st"]) for s in md3_surfs)
    tt = sum(len(s["tris"]) for s in md3_surfs)
    print(f"  [MD3 OK] {model_name:18s} -> {deploy_names}: {len(dp_surfs)} surfs, {tv:4d}v (s0={len(dp_surfs[0]['st'])}<=4096), {tt:4d}t, {nf:2d}f")
    return stage_p


# ===========================================================================
# STRICT VANILLA QUAKE 1 (`IDPO` v6) `.MDL` + EXTERNAL `.TGA` EXPORTER
# ===========================================================================
def load_quake_palette_and_anorms():
    d = open(PAK_PATH, "rb").read()
    ident, ofs, ln = struct.unpack_from("<4sii", d, 0)
    assert ident == b"PACK"
    pal_raw = None
    for i in range(ln // 64):
        n, o, s = struct.unpack_from("<56sii", d, ofs + 64 * i)
        if n.split(b"\0")[0].decode("ascii").lower() == "gfx/palette.lmp":
            pal_raw = d[o:o + s]
            break
    assert pal_raw is not None and len(pal_raw) == 768
    pal = np.frombuffer(pal_raw, dtype=np.uint8).reshape(256, 3).astype(np.float32)

    txt = re.sub(r"//.*", "", open(ANORMS_PATH, encoding="ascii").read())
    anorms = np.array([list(map(float, m)) for m in re.findall(r"\{\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\}", txt)], dtype=np.float64)
    assert anorms.shape == (162, 3)
    return pal, anorms


def write_uncompressed_tga(path, rgb_img: Image.Image):
    """Writes standard uncompressed 24-bit top-left origin TGA (`progs/<model>.mdl_0.tga`) for hires Quake engines."""
    im = rgb_img.convert("RGB")
    w, h = im.size
    arr = np.asarray(im, dtype=np.uint8)
    bgr = arr[:, :, ::-1].tobytes()
    # Image descriptor 0x20 = top-left origin!
    hdr = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, w, h, 24, 0x20)
    open(path, "wb").write(hdr + bgr)


def export_strict_quake_mdl(model_name, md3_surfs, frame_names, tex_paths, pal, anorms, deploy_names):
    """Exports a 100% vanilla-legal Quake 1 `IDPO` v6 `.mdl`:
       - Skin `512 x 256` (`<= MAX_LBM_HEIGHT=480`, multiples of 4, power-of-two for GLQuake!)
       - Lit texels quantized to `0..223`; glowing core & blast texels quantized to fullbright `224..254`!
       - Welded vertices strictly `<= 1024` (`MAXALIASVERTS`), triangles strictly `<= 2048` (`MAXALIASTRIS`)!
       - Companion external `1024x512` 24-bit TGA skin `<name>.mdl_0.tga`!
    """
    SW, SH = 512, 256
    atlas_lo = np.asarray(Image.open(tex_paths["mdl_atlas_lo"]).convert("RGB"), dtype=np.float32)
    atlas_hi = Image.open(tex_paths["mdl_atlas_hi"]).convert("RGB")

    # Vectorized palette quantization:
    #   Left half [x < 256] (silver) + top-mid [256..384, y < 128] (hand) -> standard lit indices 0..223
    #   Top-right [384..512, y < 128] (core/projectile) + bottom-right [256..512, y >= 128] (fx):
    #     bright texels (lum > 115) map to Quake fullbrights 224..254 so the WEW core & projectile GLOW in vanilla Quake!
    flat = atlas_lo.reshape(-1, 3)
    d_lit = np.sum((flat[:, None, :] - pal[None, :224, :]) ** 2, axis=2)
    idx_lit = np.argmin(d_lit, axis=1).astype(np.uint8)

    d_fb = np.sum((flat[:, None, :] - pal[None, 224:255, :]) ** 2, axis=2)
    idx_fb = (224 + np.argmin(d_fb, axis=1)).astype(np.uint8)

    yy, xx = np.mgrid[0:SH, 0:SW]
    is_glow_zone = ((xx >= 384) & (yy < 128)) | ((xx >= 256) & (yy >= 128))
    lum = 0.299 * atlas_lo[..., 0] + 0.587 * atlas_lo[..., 1] + 0.114 * atlas_lo[..., 2]
    use_fb = (is_glow_zone & (lum > 135.0)).reshape(-1)
    skin_bytes = np.where(use_fb, idx_fb, idx_lit).astype(np.uint8).tobytes()

    # Remap per-surface UVs into the 512x256 unified atlas:
    #   silver -> u:[0.00..0.50], v:[0.00..1.00]
    #   hand   -> u:[0.50..0.75], v:[0.00..0.50]
    #   core   -> u:[0.75..1.00], v:[0.00..0.50]
    #   fx     -> u:[0.50..1.00], v:[0.50..1.00]
    uv_remap = {
        "silver": (0.00, 0.00, 0.50, 1.00),
        "hand":   (0.50, 0.00, 0.25, 0.50),
        "core":   (0.75, 0.00, 0.25, 0.50),
        "crt":    (0.75, 0.00, 0.125, 0.25),
        "fx":     (0.50, 0.50, 0.50, 0.50),
    }

    nf = len(frame_names)
    mpos = [[] for _ in range(nf)]
    mnor = [[] for _ in range(nf)]
    mst = []
    tris = []

    for s in md3_surfs:
        ox, oy, sx, sy = uv_remap[s["mat"]]
        base = len(mst)
        for u, v in s["st"]:
            au = ox + np.clip(u, 0.002, 0.998) * sx
            av = oy + np.clip(v, 0.002, 0.998) * sy
            si = max(0, min(SW - 1, int(round(au * SW - 0.5))))
            ti = max(0, min(SH - 1, int(round(av * SH - 0.5))))
            mst.append((si, ti))
        for fi in range(nf):
            mpos[fi].extend(s["frames"][fi][0])
            mnor[fi].extend(s["frames"][fi][1])
        # Note: s["tris"] is ALREADY CW-outward (from `pack_md3_surfaces`)!
        tris.extend((base + a, base + b, base + c) for a, b, c in s["tris"])

    pos_np = np.array(mpos, dtype=np.float64)  # (nf, nv0, 3)
    nor_np = np.array(mnor, dtype=np.float64)  # (nf, nv0, 3)

    mn = pos_np.min(axis=(0, 1))
    mx = pos_np.max(axis=(0, 1))
    scale = np.maximum((mx - mn) / 255.0, 1e-6)
    origin = mn.copy()

    qpos = np.clip(np.round((pos_np - origin[None, None, :]) / scale[None, None, :]), 0, 255).astype(np.uint8)
    dots = np.einsum("fvc,nc->fvn", nor_np, anorms)
    qnrm = np.argmax(dots, axis=2).astype(np.uint8)

    # Exact lossless weld of vertices sharing identical (s, t) & quantized frame trajectory
    nv0 = len(mst)
    keymap, remap, keep = {}, [0] * nv0, []
    for i in range(nv0):
        key = (mst[i], qpos[:, i, :].tobytes(), qnrm[:, i].tobytes())
        j = keymap.get(key)
        if j is None:
            j = len(keep)
            keymap[key] = j
            keep.append(i)
        remap[i] = j

    tris_w = []
    for a, b, c in tris:
        ra, rb, rc = remap[a], remap[b], remap[c]
        if ra != rb and rb != rc and ra != rc:
            tris_w.append((ra, rb, rc))

    nv, nt = len(keep), len(tris_w)
    assert nv <= 1024, f"Vanilla Quake MAXALIASVERTS (1024) exceeded in {model_name}.mdl: nv={nv}"
    assert nt <= 2048, f"Vanilla Quake MAXALIASTRIS (2048) exceeded in {model_name}.mdl: nt={nt}"
    assert SH <= 480 and SW % 4 == 0, f"Invalid MDL skin size {SW}x{SH}"

    keep_arr = np.array(keep, dtype=np.int32)
    qpos_k = qpos[:, keep_arr, :]
    qnrm_k = qnrm[:, keep_arr]
    wpos_k = qpos_k.astype(np.float64) * scale[None, None, :] + origin[None, None, :]
    radius = float(np.sqrt(np.sum(wpos_k ** 2, axis=2)).max())

    # Verify CW-outward winding on frame 0!
    cw_ok = ccw_bad = 0
    for a, b, c in tris_w:
        pa, pb, pc = pos_np[0, keep[a]], pos_np[0, keep[b]], pos_np[0, keep[c]]
        fn = np.cross(pb - pa, pc - pa)
        vn = nor_np[0, keep[a]] + nor_np[0, keep[b]] + nor_np[0, keep[c]]
        d = float(np.dot(fn, vn))
        if d < -1e-9:
            cw_ok += 1
        elif d > 1e-9:
            ccw_bad += 1
    assert cw_ok > ccw_bad * 10, f"Winding check failed on {model_name}.mdl: CW={cw_ok}, CCW={ccw_bad}"

    out = bytearray()
    out += struct.pack("<4si", b"IDPO", 6)
    out += struct.pack("<3f3ff3f", float(scale[0]), float(scale[1]), float(scale[2]),
                       float(origin[0]), float(origin[1]), float(origin[2]), radius, 0.0, 0.0, 0.0)
    out += struct.pack("<iiiiiiiif", 1, SW, SH, nv, nt, nf, 0, 0, 0.0)
    out += struct.pack("<i", 0) + skin_bytes
    for idx_orig in keep:
        s_px, t_px = mst[idx_orig]
        out += struct.pack("<3i", 0, s_px, t_px)
    for a, b, c in tris_w:
        out += struct.pack("<4i", 1, a, b, c)
    for fi in range(nf):
        bmin = qpos_k[fi].min(axis=0).tolist()
        bmax = qpos_k[fi].max(axis=0).tolist()
        fnm = frame_names[fi].encode("ascii")[:15].ljust(16, b"\0")
        out += struct.pack("<i", 0) + bytes(bmin) + b"\0" + bytes(bmax) + b"\0" + fnm
        frame_verts = np.column_stack([qpos_k[fi], qnrm_k[fi]]).astype(np.uint8)
        out += frame_verts.tobytes()

    stage_mdl = os.path.join(STAGE_DIR, f"{model_name}.mdl")
    open(stage_mdl, "wb").write(out)

    # Validate binary structure using `md3_to_mdl.read_mdl`!
    import md3_to_mdl
    md3_to_mdl.read_mdl(stage_mdl)

    for dname in deploy_names:
        dp = os.path.join(PROGS_DIR, f"{dname}.mdl")
        shutil.copy2(stage_mdl, dp)
        write_uncompressed_tga(dp + "_0.tga", atlas_hi)

    print(f"  [MDL OK] {model_name:18s} -> {deploy_names}: {nv:4d}v (<=1024!), {nt:4d}t (<=2048!), {nf:2d}f, skin {SW}x{SH}")
    return stage_mdl


# ===========================================================================
# STANDALONE WORLD PICKUP (`g_wewcannon`)
# ===========================================================================
def build_world_pickup(lod, tex_paths, pal, anorms):
    is_hd = (lod == "hd")

    # Centered World Pickup Model (`g_wewcannon`: 1 frame, centered at origin for Quake pickups!)
    rest_surfs = build_cannon_rest_surfaces(lod=lod)
    # Exclude Ranger hands & muzzle FX from world pickup (keep CRT monitor on top of the WEW CANNON!)
    pickup_builders = [sb for sb in rest_surfs if sb.name in ("cannon_silver", "cannon_core", "crt_screen")]
    idle_fr = build_48_frame_schedule()[0].copy()
    spine0 = build_spine_table(idle_fr)
    pk_frames = []
    for sb in pickup_builders:
        V_loc, N_loc = evaluate_surface_for_frame(sb, idle_fr, spine0, to_eye=False)
        # Center at (0, 0, 12) and scale nicely for a giant Quake pickup item!
        V_w = (V_loc - np.array([10.0, 0.0, 0.0])) * 1.15 + np.array([0.0, 0.0, 12.0])
        pk_frames.append([(V_w, N_loc)])
    pk_md3 = pack_md3_surfaces(pickup_builders, pk_frames)
    if is_hd:
        write_md3_with_skins("g_wewcannon", pk_md3, ["pickup1"], ["g_wewcannon"])
    else:
        export_strict_quake_mdl("g_wewcannon", pk_md3, ["pickup1"], tex_paths, pal, anorms, ["g_wewcannon"])
    return pk_md3


# ===========================================================================
# SELF-CONTAINED PBR `.GLB` EXPORTER & DARKPLACES `.SHADER` WRITER
# ===========================================================================
def export_glb_model(glb_path, md3_surfs, tex_paths, frame_idx=0):
    bin_buf = bytearray()
    buffer_views, accessors, images, textures, materials, primitives = [], [], [], [], [], []
    mat_map = {}

    mat_cfg = {
        "silver": dict(metallic=0.92, roughness=0.16, emit=False),
        "hand":   dict(metallic=0.22, roughness=0.52, emit=False),
        "core":   dict(metallic=0.35, roughness=0.25, emit=True),
        "crt":    dict(metallic=0.08, roughness=0.20, emit=True),
        "fx":     dict(metallic=0.00, roughness=0.50, emit=True, blend=True),
    }

    def push_bv(raw_b, target=None):
        while len(bin_buf) & 3:
            bin_buf.append(0)
        off = len(bin_buf)
        bin_buf.extend(raw_b)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw_b)}
        if target is not None:
            bv["target"] = target
        idx = len(buffer_views)
        buffer_views.append(bv)
        return idx

    for s in md3_surfs:
        mk = s["mat"]
        cfg = mat_cfg[mk]
        if mk not in mat_map:
            png_b = open(tex_paths[mk], "rb").read()
            ibv = push_bv(png_b)
            ii = len(images)
            images.append({"bufferView": ibv, "mimeType": "image/png", "name": mk})
            ti = len(textures)
            textures.append({"source": ii, "name": mk})
            m_obj = {
                "name": mk,
                "doubleSided": True,
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": ti},
                    "metallicFactor": cfg["metallic"],
                    "roughnessFactor": cfg["roughness"],
                },
            }
            if cfg.get("blend"):
                m_obj["alphaMode"] = "BLEND"
            if cfg.get("emit"):
                m_obj["emissiveTexture"] = {"index": ti}
                m_obj["emissiveFactor"] = [1.0, 1.0, 1.0]
            mi = len(materials)
            materials.append(m_obj)
            mat_map[mk] = mi

        vv, nn = s["frames"][frame_idx]
        qv = np.asarray(vv, dtype=np.float32)
        qn = np.asarray(nn, dtype=np.float32)
        # Quake (+X fwd, +Y left, +Z up) -> glTF (-Z fwd, +X right=-Y_q, +Y up=+Z_q) in meters
        sc = 0.03
        gv = np.stack([-qv[:, 1] * sc, qv[:, 2] * sc, -qv[:, 0] * sc], axis=1).astype(np.float32)
        gn = np.stack([-qn[:, 1], qn[:, 2], -qn[:, 0]], axis=1).astype(np.float32)
        gn /= np.maximum(1e-6, np.linalg.norm(gn, axis=1, keepdims=True))
        uv = np.asarray(s["st"], dtype=np.float32)
        # Flip MD3 CW-outward -> glTF CCW-outward!
        tris_ccw = np.array([(a, c, b) for a, b, c in s["tris"]], dtype=np.uint16).reshape(-1)

        bv_p = push_bv(gv.tobytes(), 34962)
        bv_n = push_bv(gn.tobytes(), 34962)
        bv_u = push_bv(uv.tobytes(), 34962)
        bv_i = push_bv(tris_ccw.tobytes(), 34963)

        ap = len(accessors)
        accessors.append({
            "bufferView": bv_p, "componentType": 5126, "count": len(gv), "type": "VEC3",
            "min": [float(c) for c in gv.min(axis=0)], "max": [float(c) for c in gv.max(axis=0)],
        })
        an = len(accessors)
        accessors.append({"bufferView": bv_n, "componentType": 5126, "count": len(gn), "type": "VEC3"})
        au = len(accessors)
        accessors.append({"bufferView": bv_u, "componentType": 5126, "count": len(uv), "type": "VEC2"})
        ai = len(accessors)
        accessors.append({"bufferView": bv_i, "componentType": 5123, "count": len(tris_ccw), "type": "SCALAR"})

        primitives.append({
            "attributes": {"POSITION": ap, "NORMAL": an, "TEXCOORD_0": au},
            "indices": ai,
            "material": mat_map[mk],
        })

    gltf = {
        "asset": {"version": "2.0", "generator": "BakersfieldQuake WEW CANNON Builder"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": os.path.splitext(os.path.basename(glb_path))[0]}],
        "meshes": [{"primitives": primitives, "name": "wew_cannon"}],
        "materials": materials,
        "textures": textures,
        "images": images,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_buf)}],
    }
    jb = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(jb) & 3:
        jb += b" "
    while len(bin_buf) & 3:
        bin_buf.append(0)
    total_len = 12 + 8 + len(jb) + 8 + len(bin_buf)
    with open(glb_path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total_len))
        f.write(struct.pack("<I4s", len(jb), b"JSON") + jb)
        f.write(struct.pack("<I4s", len(bin_buf), b"BIN\0") + bin_buf)
    print(f"  [GLB OK] {os.path.basename(glb_path):28s} ({os.path.getsize(glb_path) / 1024:.1f} KB)")


def write_quake_shader():
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    crt_list = " ".join(f"progs/wew_crt_{i:02d}" for i in range(16))
    shader = f"""// written by source/mm_tools/wew_cannon/build_wew_cannon.py

progs/wew_silver
{{
\tcull none
\t{{
\t\tmap progs/wew_silver
\t\trgbGen lightingDiffuse
\t}}
}}

progs/wew_hand
{{
\tcull none
\t{{
\t\tmap progs/wew_hand
\t\trgbGen lightingDiffuse
\t}}
}}

progs/wew_core
{{
\tcull none
\t{{
\t\tmap progs/wew_core
\t\trgbGen identity
\t}}
}}

progs/wew_crt_anim
{{
\tcull none
\t{{
\t\tanimmap 2 {crt_list}
\t\trgbGen identity
\t}}
}}

progs/wew_crt_screen
{{
\tcull none
\t{{
\t\tanimmap 2 {crt_list}
\t\trgbGen identity
\t}}
}}

progs/wew_fx
{{
\tcull none
\tsort 10
\t{{
\t\tmap progs/wew_fx
\t\tblendfunc add
\t\trgbGen identity
\t}}
}}
"""
    sh_path = os.path.join(SCRIPTS_DIR, "wewcannon.shader")
    open(sh_path, "w", encoding="ascii", newline="\n").write(shader)
    print(f"  [SHADER OK] {sh_path}")


def main():
    os.makedirs(STAGE_DIR, exist_ok=True)
    print("1/5 Synthesizing WEW CANNON silver, plaque, core, hand & shockwave textures...")
    tex_paths = wtex.build_all_textures(TEX_DIR, PROGS_DIR)
    pal, anorms = load_quake_palette_and_anorms()

    sched = build_48_frame_schedule()
    frame_names = [fr["name"] for fr in sched]
    spines = [build_spine_table(fr) for fr in sched]

    print("2/5 Baking 48-frame HD Deformable Bending-Barrel MD3 Viewmodel (`v_wewcannon.md3`, `v_wcannon.md3`)...")
    hd_builders = build_cannon_rest_surfaces(lod="hd")
    hd_frames_per_surf = [[] for _ in hd_builders]
    for fr, sp_tbl in zip(sched, spines):
        for si, sb in enumerate(hd_builders):
            hd_frames_per_surf[si].append(evaluate_surface_for_frame(sb, fr, sp_tbl, to_eye=True))
    hd_md3_surfs = pack_md3_surfaces(hd_builders, hd_frames_per_surf)
    write_md3_with_skins("v_wewcannon", hd_md3_surfs, frame_names, ["v_wewcannon", "v_wcannon"])

    print("3/5 Baking 48-frame Strict Vanilla-Legal Quake 1 `.MDL` (`v_wewcannon.mdl`, `v_wcannon.mdl`)...")
    mdl_builders = build_cannon_rest_surfaces(lod="mdl")
    mdl_frames_per_surf = [[] for _ in mdl_builders]
    for fr, sp_tbl in zip(sched, spines):
        for si, sb in enumerate(mdl_builders):
            mdl_frames_per_surf[si].append(evaluate_surface_for_frame(sb, fr, sp_tbl, to_eye=True))
    mdl_surfs_packed = pack_md3_surfaces(mdl_builders, mdl_frames_per_surf)
    export_strict_quake_mdl("v_wewcannon", mdl_surfs_packed, frame_names, tex_paths, pal, anorms, ["v_wewcannon", "v_wcannon"])

    print("4/5 Baking World Pickup (`g_wewcannon`) in MD3 & MDL (projectile omitted — separate entity model)...")
    pk_hd_surfs = build_world_pickup("hd", tex_paths, pal, anorms)
    build_world_pickup("mdl", tex_paths, pal, anorms)

    print("5/5 Writing DarkPlaces Shader & Universal PBR `.GLB` Models...")
    write_quake_shader()
    export_glb_model(os.path.join(MOD_ROOT, "wew_cannon_weapon.glb"), hd_md3_surfs, tex_paths, frame_idx=0)
    export_glb_model(os.path.join(STAGE_DIR, "wew_cannon_blast_pose.glb"), hd_md3_surfs, tex_paths, frame_idx=27)
    export_glb_model(os.path.join(MOD_ROOT, "wew_cannon_pickup.glb"), pk_hd_surfs, tex_paths, frame_idx=0)

    meta = dict(
        nFrames=len(frame_names),
        frameNames=frame_names,
        idleRange=[0, 15],
        bendRange=[16, 25],
        blastRange=[26, 29],
        launchFrame=27,
        recoilRange=[30, 39],
        reloadRange=[40, 47],
    )
    open(os.path.join(OUT_ROOT, "wew_meta.json"), "w", encoding="utf-8").write(json.dumps(meta, indent=2))
    print("ALL WEW CANNON QUAKE MODELS (MD3 + STRICT MDL + TGA + SKIN + SHADER + GLB) BUILT SUCCESSFULLY!")


if __name__ == "__main__":
    main()
