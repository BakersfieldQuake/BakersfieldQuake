"""Master 3D Procedural Geometry, Slapstick Rubbery-Swell & Burnout-Wheel Deformer, and Multi-Format Quake Exporter
for the 'CHROME-ROD CONTRAPTION BAZOOKA' (`rod_cannon`).

Inspired directly by the stainless-steel two-wheel contraption video — literally blown up to absurd
shoulder/hip-slung Quake bazooka proportions, with wide pneumatic white-rim hand-truck tires sticking
way out both sides, mirror-chrome rounded bullet-dome breech, machined seam ring, open black-collared
cannon mouth, slapstick peristaltic swell, burnout wheel spin, and springy barbell-axle kickback!

Standalone outputs (does NOT modify any active weapon slots or `progs.dat`):
  1. `progs/v_rodcannon.md3` (+ `_0.skin`, `_1.skin`)  — 48-frame HD 1st-Person Viewmodel
  2. `progs/v_rodcannon.mdl` (+ `_0.tga`)              — 48-frame Strict Vanilla-Legal Quake 1 `.mdl`
  3. `progs/p_rodcannon.md3` (+ `_0.skin`, `_1.skin`)  — 259-frame 3rd-Person Held `vwep` (rides `p_rock2.md3`!)
  4. `progs/g_rodcannon.md3` & `progs/g_rodcannon.mdl` — Centered World Pickup Model (posed at video's 35° cannon tilt!)
  5. `scripts/rodcannon.shader`                        — DarkPlaces / Quake 3 Chrome + Diffuse + FX Shader
  6. `rod_cannon_weapon.glb`, `rod_cannon_thirdperson.glb`, `rod_cannon_pickup.glb` — Self-contained PBR glTF 2.0
"""
import json
import math
import os
import re
import shutil
import struct
import sys
import zipfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
SCRIPTS_DIR = os.path.join(MOD_ROOT, "scripts")

OUT_ROOT = os.path.join(MM_TOOLS, "out", "rod_cannon")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
STAGE_DIR = os.path.join(OUT_ROOT, "models")

Q15_PK3 = r"G:\Quake\Combat\quake15\q15.pk3"
PAK_PATHS = (r"G:\Quake\Combat\id1\pak0.pak", r"G:\Quake\QBJ3\id1\pak0.pak")
ANORMS_PATH = r"D:\vibe\quake1opensource\idsrc\WinQuake\anorms.h"

for p in (MM_TOOLS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import md3lib
from mmw_geometry import build_articulated_ranger_hand, rot_x, vnorm
import make_rod_textures as rtex


# ===========================================================================
# VECTOR / MATRIX & MESH UTILITIES
# ===========================================================================
def rot_x_mat(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def rot_y_mat(deg):
    """Positive deg pitches +X upward toward +Z."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]], dtype=np.float64)


def rot_z_mat(deg):
    """Positive deg yaws +X toward +Y (left)."""
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
        self.tris = []          # Stored CCW-outward; converted to CW-outward for MD3/MDL
        self.deform_tags = []

    def add_part(self, verts, norms, st, tris_ccw, tag="tube"):
        base = len(self.verts)
        self.verts.extend(verts)
        self.norms.extend(norms)
        self.st.extend(st)
        self.deform_tags.extend([tag] * len(verts))
        for a, b, c in tris_ccw:
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


def build_lathe_x(profile_xr, radial_segs, uv_rect, axis_offset=(0.0, 0.0, 0.0), inward_normals=False):
    """Revolves `(x, r)` around +X (`phi=pi` at -Z bottom seam, `phi=0/2pi` at -Z, `tu=0.5` at +Z top)."""
    u0, v0, u1, v1 = uv_rect
    ox, oy, oz = axis_offset
    nr = len(profile_xr)
    verts, norms, st, tris = [], [], [], []

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


def build_lathe_y(profile_yr, radial_segs, uv_rect, axis_offset=(0.0, 0.0, 0.0)):
    """Revolves `(y, r)` around +Y (the horizontal axle axis!). `tu=0.5` is +Z top, `tu=0/1` is -Z bottom."""
    u0, v0, u1, v1 = uv_rect
    ox, oy, oz = axis_offset
    nr = len(profile_yr)
    verts, norms, st, tris = [], [], [], []

    dr_dy = []
    for j in range(nr):
        j0 = max(0, j - 1)
        j1 = min(nr - 1, j + 1)
        dy = profile_yr[j1][0] - profile_yr[j0][0]
        dr = profile_yr[j1][1] - profile_yr[j0][1]
        if abs(dy) < 1e-6:
            ny, nrad = (-1.0 if dr > 0 else 1.0), 0.25
        else:
            ny, nrad = -dr, dy
            if dy < 0:
                ny, nrad = -ny, -nrad
        l = math.hypot(ny, nrad) or 1.0
        dr_dy.append((ny / l, nrad / l))

    for j, (y, r) in enumerate(profile_yr):
        tv = j / max(1, nr - 1)
        ny_s, nr_s = dr_dy[j]
        for i in range(radial_segs + 1):
            tu = i / radial_segs
            phi = math.pi + tu * 2.0 * math.pi
            sp, cp = math.sin(phi), math.cos(phi)  # x = r*sp, z = r*cp
            verts.append((ox + r * sp, oy + y, oz + r * cp))
            norms.append((nr_s * sp, ny_s, nr_s * cp))
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))

    stride = radial_segs + 1
    for j in range(nr - 1):
        for i in range(radial_segs):
            a = j * stride + i
            b = j * stride + i + 1
            c = (j + 1) * stride + i + 1
            d = (j + 1) * stride + i
            tris.append((a, c, b))
            tris.append((a, d, c))
    return verts, norms, st, tris


def build_pneumatic_wheel(y_center, side_sign, is_hd=True):
    """Builds one complete pneumatic hand-truck wheel centered at `(0, y_center, 0)` with axle along `Y`:
    - Black ribbed pneumatic torus tire (`UV_TIRE_TREAD`)
    - Inner & Outer glossy white 4-hole concave stamped-steel dish rims + 6203-2RS ball bearings (`UV_WHITE_RIM`)
    - Angled black/brass Schrader valve stem (`UV_VALVE_STEM`)
    - Outer stainless hex nyloc axle locknut & inner hub collar (`UV_HEX_NUT`)
    Returns `(wheel_parts, axle_nut_parts)` so the wheel spins while the axle locknut rides the axle tip!
    """
    maj_seg = 28 if is_hd else 12
    min_seg = 12 if is_hd else 6
    dish_seg = 24 if is_hd else 10

    R_maj = 6.65
    r_xz = 2.85    # outer tire radius = 6.65 + 2.85 = 9.50 (19.0u tall!), inner bead = 3.80
    r_y  = 2.48    # tire width = 4.96u

    # 1. Pneumatic Rubber Torus Tire (`v` goes inner-bead -> outer sidewall -> crown -> inner sidewall -> inner-bead)
    u0, v0, u1, v1 = rtex.UV_TIRE_TREAD
    tv_list, tn_list, tst_list, ttris = [], [], [], []
    for j in range(min_seg + 1):
        fv = j / min_seg
        # alpha = -pi (inner bead, -Y/+Y) -> 0 (tread crown, outward) -> +pi (inner bead)
        alpha = -math.pi + fv * 2.0 * math.pi
        ca, sa = math.cos(alpha), math.sin(alpha)
        rad = R_maj + r_xz * ca
        ly = y_center + side_sign * r_y * sa
        for i in range(maj_seg + 1):
            fu = i / maj_seg
            theta = fu * 2.0 * math.pi
            ct, st_a = math.cos(theta), math.sin(theta)
            lx = rad * ct
            lz = rad * st_a
            nx = (ca / r_xz) * ct
            ny = side_sign * (sa / r_y)
            nz = (ca / r_xz) * st_a
            nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            tv_list.append((lx, ly, lz))
            tn_list.append((nx / nl, ny / nl, nz / nl))
            tst_list.append((u0 + (u1 - u0) * fu, v0 + (v1 - v0) * fv))

    stride = maj_seg + 1
    for j in range(min_seg):
        for i in range(maj_seg):
            a = j * stride + i
            b = j * stride + i + 1
            c = (j + 1) * stride + i + 1
            d = (j + 1) * stride + i
            ttris.append((a, b, c))
            ttris.append((a, c, d))

    wheel_parts = [(tv_list, tn_list, tst_list, ttris)]

    # 2. Glossy White Concave Stamped-Steel Dish Rims on BOTH Faces (`dir_y = +1` and `-1`)
    #    Planar radial UV projection onto `UV_WHITE_RIM` so the 4 oval holes, rolled lip, and 6203 bearing align!
    ru0, rv0, ru1, rv1 = rtex.UV_WHITE_RIM
    rc_u = 0.5 * (ru0 + ru1)
    rc_v = 0.5 * (rv0 + rv1)
    rr_u = 0.46 * (ru1 - ru0)
    rr_v = 0.46 * (rv1 - rv0)
    R_dish_max = 4.30  # tucks cleanly inside the rubber tire bead (3.80)!

    # Radial profile `(r, axial_depth_from_center)`: rolled outer bead lip -> concave bowl -> raised bearing boss!
    dish_rings = (
        [(0.00, 1.52), (1.05, 1.56), (1.35, 1.18), (3.45, 0.96), (4.05, 1.58), (4.30, 1.35)]
        if is_hd else
        [(0.00, 1.48), (1.30, 1.15), (4.25, 1.48)]
    )
    for face_dir in (-1.0, +1.0):
        dv, dn, dst, dtr = [], [], [], []
        nr_d = len(dish_rings)
        for ri, (rr, y_off) in enumerate(dish_rings):
            r_prev, y_prev = dish_rings[max(0, ri - 1)]
            r_next, y_next = dish_rings[min(nr_d - 1, ri + 1)]
            dr_s = r_next - r_prev
            dy_s = (y_next - y_prev) * face_dir
            # Outward normal pointing toward `face_dir * Y`
            ny_c = face_dir * max(0.25, abs(dr_s))
            nr_c = -dy_s * face_dir
            nl_d = math.hypot(ny_c, nr_c) or 1.0
            ny_c, nr_c = ny_c / nl_d, nr_c / nl_d
            for i in range(dish_seg + 1):
                theta = (i / dish_seg) * 2.0 * math.pi
                ct, st_a = math.cos(theta), math.sin(theta)
                dv.append((rr * ct, y_center + face_dir * y_off, rr * st_a))
                dn.append((nr_c * ct, ny_c, nr_c * st_a))
                # Flip horizontal UV on opposite face so 6203 bearing & 4 oval holes read cleanly
                u_p = rc_u + (rr / R_dish_max) * ct * rr_u * face_dir
                v_p = rc_v - (rr / R_dish_max) * st_a * rr_v
                dst.append((u_p, v_p))
        st_d = dish_seg + 1
        for ri in range(nr_d - 1):
            for i in range(dish_seg):
                a = ri * st_d + i
                b = ri * st_d + i + 1
                c = (ri + 1) * st_d + i + 1
                d = (ri + 1) * st_d + i
                dtr.append((a, b, c))
                dtr.append((a, c, d))
        wheel_parts.append((dv, dn, dst, dtr))

    # 3. Angled Schrader Valve Stem on BOTH Inner & Outer Dish Faces (or visible side — in the video, one crisp valve per wheel;
    #    putting it protruding on the outer face AND a matching valve base on inner face? Wait: in the video `00:00` & `00:03`,
    #    the valve stem is on ONE side of each wheel—let's put it on the INNER face for 1st-person visibility OR angled out at
    #    both? No, let's check: in video `00:00` the valve stem is on the OUTER side, and in `00:03` it's on the OUTER side!
    #    Wait: why not orient the wheels with valve stems on the camera-visible dish face in 1st-person OR put a small valve
    #    stem on the outer dish AND a grease zerk / valve on inner dish so BOTH views have a clear rotational marker on top of
    #    the 4 big oval holes!)
    if is_hd:
        for f_dir, v_len, th_deg in ((side_sign, 1.35, -38.0), (-side_sign, 1.05, +142.0)):
            va = math.radians(th_deg)
            vx0, vz0 = 2.65 * math.cos(va), 2.65 * math.sin(va)
            vy0 = y_center + f_dir * 1.12
            # Tilted outward radially + axially
            dir_v = vnorm((0.32 * math.cos(va), f_dir * 0.90, 0.32 * math.sin(va)))
            up_v = vnorm((-math.sin(va), 0.0, math.cos(va)))
            rt_v = np.cross(dir_v, up_v)
            vv_l, vn_l, vst_l, vtr_l = [], [], [], []
            vu0, vv0, vu1, vv1 = rtex.UV_VALVE_STEM
            v_segs = 6
            rings_v = [(0.0, 0.28), (v_len * 0.72, 0.26), (v_len, 0.22), (v_len + 0.06, 0.02)]
            for rj, (s_d, r_rad) in enumerate(rings_v):
                tv_v = rj / (len(rings_v) - 1)
                c_pt = np.array([vx0, vy0, vz0]) + np.array(dir_v) * s_d
                for vi in range(v_segs + 1):
                    tu_v = vi / v_segs
                    ang_v = tu_v * 2.0 * math.pi
                    n_rad = np.array(up_v) * math.cos(ang_v) + rt_v * math.sin(ang_v)
                    pt_v = c_pt + n_rad * r_rad
                    vv_l.append(tuple(pt_v))
                    vn_l.append(tuple(vnorm(tuple(n_rad + np.array(dir_v) * (0.8 if rj == len(rings_v) - 1 else 0.1)))))
                    vst_l.append((vu0 + (vu1 - vu0) * tu_v, vv0 + (vv1 - vv0) * tv_v))
            st_v = v_segs + 1
            for rj in range(len(rings_v) - 1):
                for vi in range(v_segs):
                    a = rj * st_v + vi
                    b = a + 1
                    c = a + st_v + 1
                    d = a + st_v
                    vtr_l.append((a, b, c))
                    vtr_l.append((a, c, d))
            wheel_parts.append((vv_l, vn_l, vst_l, vtr_l))

    # 4. Outer Stainless Hex Nyloc Locknut & Washer + Inner Retaining Collar (rides axle tip without spinning!)
    nut_segs = 6
    y_out0 = y_center + side_sign * 1.52
    y_out3 = y_center + side_sign * 2.85
    if side_sign > 0:
        nut_prof = [(y_out0, 0.95), (y_out0 + 0.18, 1.52), (y_out0 + 0.35, 1.52), (y_out0 + 0.38, 1.28),
                    (y_out3 - 0.15, 1.28), (y_out3, 0.92), (y_out3 + 0.25, 0.05)]
    else:
        nut_prof = [(y_out3 - 0.25, 0.05), (y_out3, 0.92), (y_out3 + 0.15, 1.28),
                    (y_out0 - 0.38, 1.28), (y_out0 - 0.35, 1.52), (y_out0 - 0.18, 1.52), (y_out0, 0.95)]
    nv_p, nn_p, nst_p, ntr_p = build_lathe_y(nut_prof, nut_segs, rtex.UV_HEX_NUT)
    axle_nut_parts = [(nv_p, nn_p, nst_p, ntr_p)]

    return wheel_parts, axle_nut_parts


# ===========================================================================
# CANNON REST GEOMETRY (`lod="hd"` for MD3/GLB, `lod="mdl"` for <=1024v MDL)
# ===========================================================================
X_REAR_TIP   = -16.4   # Rounded mirror-chrome bullet-dome rear tip (100% visible in 90° POV!)
X_SEAM_RING  =  -2.8   # Machined circumferential seam groove behind axle
X_AXLE       =   0.0   # Central T-sleeve collar & horizontal wheel axle
X_CAP_START  = +19.0   # Start of matte-black Delrin/rubber muzzle collar
X_MUZZLE_TIP = +21.6   # Open cannon pipe mouth
Y_WHEEL      = +18.4   # Half-span to Left (+Y) and Right (-Y) wheel centers!

R_TUBE       =   3.18  # Giant gleaming 304 stainless-steel cannon pipe radius


def build_contraption_rest_surfaces(lod="hd", include_hands=True, include_fx=True):
    is_hd = (lod == "hd")
    rad_tube = 24 if is_hd else 8
    rad_axle = 12 if is_hd else 6

    surf_chrome = SurfBuilder("rod_chrome",   "progs/rod_chrome", "chrome")
    surf_wheel  = SurfBuilder("rod_wheel",    "progs/rod_wheel",  "wheel")
    surf_hands  = SurfBuilder("ranger_hands", "progs/rod_hand",   "hand")
    surf_fx     = SurfBuilder("rod_fx",       "progs/rod_fx",     "fx")

    # 1. REAR MIRROR-CHROME BULLET-DOME BREECH + MACHINED SEAM GROOVE (`x = -16.4 .. -1.65`, `tag="tube"`)
    #    Exact match to video frames 00:00-00:03 & 00:08: smooth parabolic/hemispherical silver bullet tip!
    n_dome = 7 if is_hd else 4
    rear_xr = []
    dome_len = 4.5
    for k in range(n_dome + 1):
        u = k / n_dome  # 0 at tip -> 1 at cylinder tangent
        ang = u * (math.pi * 0.5)
        xk = X_REAR_TIP + dome_len * (1.0 - math.cos(ang))
        rk = max(0.04, R_TUBE * (math.sin(ang) ** 0.88))
        rear_xr.append((xk, rk))

    if is_hd:
        rear_xr.extend([
            (-9.6, R_TUBE),
            (-7.0, R_TUBE),
            (-4.8, R_TUBE),
            (-3.25, R_TUBE),
            (-3.05, R_TUBE - 0.22),  # Crisp machined recessed seam groove (`Rig_RodSeamRing` in video!)
            (-2.65, R_TUBE - 0.22),
            (-2.45, R_TUBE),
            (-1.65, R_TUBE),
        ])
    else:
        rear_xr.extend([
            (-7.8, R_TUBE),
            (-3.0, R_TUBE - 0.18),
            (-2.5, R_TUBE),
            (-1.6, R_TUBE),
        ])
    v, n, s, t = build_lathe_x(rear_xr, rad_tube, rtex.UV_CHROME_TUBE)
    surf_chrome.add_part(v, n, s, t, tag="tube")

    # 2. CENTER CNC-MACHINED / TIG-WELDED CHROME T-SLEEVE COLLAR (`x = -1.75 .. +1.75`, `tag="tube"`)
    collar_xr = [
        (-1.82, R_TUBE - 0.08),
        (-1.62, R_TUBE + 0.30),
        ( 0.00, R_TUBE + 0.34),
        (+1.62, R_TUBE + 0.30),
        (+1.82, R_TUBE - 0.08),
    ]
    v, n, s, t = build_lathe_x(collar_xr, rad_tube, rtex.UV_CHROME_COLLAR)
    surf_chrome.add_part(v, n, s, t, tag="tube")

    # 3. FORWARD MIRROR-CHROME CANNON BARREL (`x = +1.65 .. +19.15`, `tag="tube"`)
    n_fwd = 10 if is_hd else 4
    fwd_xr = [(1.65 + (X_CAP_START + 0.10 - 1.65) * (k / n_fwd), R_TUBE) for k in range(n_fwd + 1)]
    v, n, s, t = build_lathe_x(fwd_xr, rad_tube, rtex.UV_CHROME_TUBE)
    surf_chrome.add_part(v, n, s, t, tag="tube")

    # 4. MATTE-BLACK DELRIN / RUBBER MUZZLE COLLAR BUSHING (`x = +18.95 .. +21.65`, `tag="tube"`)
    #    Exact match to video frames 00:05 & 00:06! Flared rubbery lip during blast!
    R_cap = R_TUBE + 0.22
    R_bore = 2.58
    cap_xr = (
        [
            (18.92, R_TUBE - 0.06),
            (19.08, R_cap),
            (20.40, R_cap),
            (21.42, R_cap),
            (21.65, R_cap - 0.18),
            (21.65, R_bore),
        ]
        if is_hd else
        [
            (18.95, R_TUBE - 0.05),
            (19.10, R_cap),
            (21.60, R_cap),
            (21.65, R_bore),
        ]
    )
    v, n, s, t = build_lathe_x(cap_xr, rad_tube, rtex.UV_BLACK_CAP)
    surf_chrome.add_part(v, n, s, t, tag="tube")

    # 5. DEEP DARK HOLLOW SMOOTHBORE INTERIOR (`x = +21.62` back to `x = +2.8`, `tag="tube"`)
    bore_xr = (
        [(21.62, R_bore), (18.5, R_bore - 0.04), (12.0, R_bore - 0.10), (4.2, R_bore - 0.18), (2.8, 0.06)]
        if is_hd else
        [(21.62, R_bore), (10.0, R_bore - 0.10), (3.0, 0.06)]
    )
    v, n, s, t = build_lathe_x(bore_xr, rad_tube, rtex.UV_DARK_BORE)
    surf_chrome.add_part(v, n, s, t, tag="tube")

    # 6. WIDE SOLID STAINLESS-STEEL HORIZONTAL AXLE BAR (`y = -21.2 .. +21.2`, `tag="axle"`)
    #    Subdivided along Y so the spindly steel axle bends & whips like a springy barbell!
    n_ax = 16 if is_hd else 6
    R_axle = 0.92
    axle_yr = [(-21.1 + 42.2 * (k / n_ax), R_axle) for k in range(n_ax + 1)]
    v, n, s, t = build_lathe_y(axle_yr, rad_axle, rtex.UV_CHROME_AXLE)
    surf_chrome.add_part(v, n, s, t, tag="axle")

    # Cross-sleeve weld boss where the axle exits the central chrome T-collar (`y in [-4.3 .. +4.3]`)
    boss_yr = [(-4.35, R_axle - 0.05), (-4.15, 1.38), (+4.15, 1.38), (+4.35, R_axle - 0.05)]
    v, n, s, t = build_lathe_y(boss_yr, rad_axle, rtex.UV_CHROME_COLLAR)
    surf_chrome.add_part(v, n, s, t, tag="axle")

    # 7. LEFT (+Y) & RIGHT (-Y) GIANT PNEUMATIC HAND-TRUCK WHEELS (`tag="wheel_L"` / `"wheel_R"`)
    for side_sgn, wtag in ((+1.0, "wheel_L"), (-1.0, "wheel_R")):
        w_parts, nut_parts = build_pneumatic_wheel(side_sgn * Y_WHEEL, side_sgn, is_hd=is_hd)
        for pv, pn, pst, ptr in w_parts:
            surf_wheel.add_part(pv, pn, pst, ptr, tag=wtag)
        for pv, pn, pst, ptr in nut_parts:
            surf_wheel.add_part(pv, pn, pst, ptr, tag="axle")

    # 8. RANGER LEATHER & BRONZE GAUNTLETS GRIPPING THE CHROME AXLE & REAR TUBE (`v_rodcannon` only!)
    #    Note: in `build_articulated_ranger_hand`, `+U` is dorsal (knuckle armor) and fingers curl toward `-U`!
    if include_hands:
        if is_hd:
            # Left hand: overhand handlebar grip on the left stainless axle rod at `y = +7.8`!
            # Dorsal knuckle plate faces up-back toward camera; fingers curl down-forward around the `x=0, z=0` axle!
            lh = build_articulated_ranger_hand(
                palm_center=(-1.05, +7.8, +1.18),
                fwd_dir=(+0.91, -0.06, +0.41),
                up_dir=(-0.40, +0.12, +0.91),
                side_sign=+1.0,
                finger_curls=(0.86, 0.90, 0.93, 0.95),
                thumb_curl=0.78,
                thumb_abd=36.0,
                hand_scale=0.92,
                forearm_len=14.0,
                forearm_dir=(-0.80, +0.30, -0.52),
            )
            # Right hand: cradling the `R=3.18` mirror-chrome rear barrel around `x = -6.6` (leaving the rounded
            # chrome bullet-dome breech `x = -9.5 .. -16.4` completely uncovered & gleaming in lower-right POV!)
            rh = build_articulated_ranger_hand(
                palm_center=(-6.6, -2.95, -2.25),
                fwd_dir=(+0.78, +0.20, -0.59),
                up_dir=(-0.24, -0.82, -0.52),
                side_sign=-1.0,
                finger_curls=(0.56, 0.62, 0.66, 0.70),
                thumb_curl=0.58,
                thumb_abd=34.0,
                hand_scale=0.96,
                forearm_len=13.5,
                forearm_dir=(-0.74, -0.44, -0.50),
            )
            surf_hands.add_part(lh.verts, lh.norms, lh.st, lh.tris, tag="hand_L")
            surf_hands.add_part(rh.verts, rh.norms, rh.st, rh.tris, tag="hand_R")
        else:
            # Low-poly vanilla MDL gauntlets
            for (x0, x1, y0, y1, z0, z1), htag in (
                ((-2.2, +1.2, +6.2, +9.4, -0.6, +2.0), "hand_L"),
                ((-8.4, -4.8, -4.2, -1.2, -4.0, -1.0), "hand_R"),
            ):
                bv = [
                    (x1, y0, z1), (x1, y1, z1), (x1, y1, z0), (x1, y0, z0),
                    (x0, y1, z1), (x0, y0, z1), (x0, y0, z0), (x0, y1, z0),
                ]
                bn = [(+1, 0, 0)] * 4 + [(-1, 0, 0)] * 4
                bst = [(0.1, 0.1), (0.4, 0.1), (0.4, 0.4), (0.1, 0.4)] * 2
                btr = [(0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7), (0, 4, 1), (4, 5, 1)]
                surf_hands.add_part(bv, bn, bst, btr, tag=htag)

    # 9. SLAPSTICK CANNON BLAST STARBURST, CARTOON SMOKE-RINGS & TIRE-BURNOUT SMOKE/SPARKS (`surf_fx`)
    if include_fx:
        bu0, bv0, bu1, bv1 = rtex.UV_FX_STARBURST
        if is_hd:
            for ang_deg in (0.0, 45.0, 90.0, 135.0):
                pts = [rot_x((lx, lr, 0.0), ang_deg) for lx, lr in ((-0.5, 12.5), (23.5, 19.5), (23.5, -19.5), (-0.5, -12.5))]
                nrm = rot_x((0.0, 0.0, 1.0), ang_deg)
                surf_fx.add_part(pts, [nrm] * 4, [(bu0, bv0), (bu1, bv0), (bu1, bv1), (bu0, bv1)], [(0, 1, 2), (0, 2, 3)], tag="fx_burst")
            pts_d = [(2.8, -18.5, +18.5), (2.8, +18.5, +18.5), (2.8, +18.5, -18.5), (2.8, -18.5, -18.5)]
            surf_fx.add_part(pts_d, [(-1.0, 0.0, 0.0)] * 4, [(bu0, bv0), (bu1, bv0), (bu1, bv1), (bu0, bv1)], [(0, 1, 2), (0, 2, 3)], tag="fx_burst")

            ru0, rv0, ru1, rv1 = rtex.UV_FX_SHOCKRING
            for rtag in ("fx_ring1", "fx_ring2"):
                pts_r = [(0.0, -11.5, +11.5), (0.0, +11.5, +11.5), (0.0, +11.5, -11.5), (0.0, -11.5, -11.5)]
                surf_fx.add_part(pts_r, [(-1.0, 0.0, 0.0)] * 4, [(ru0, rv0), (ru1, rv0), (ru1, rv1), (ru0, rv1)], [(0, 1, 2), (0, 2, 3)], tag=rtag)

            # Burnout tire-screech smoke & spark plumes under BOTH wheels during high-RPM charge & blast!
            su0, sv0, su1, sv1 = rtex.UV_FX_SMOKE
            pu0, pv0, pu1, pv1 = rtex.UV_FX_SPARKS
            for sgn in (-1.0, +1.0):
                wy = sgn * Y_WHEEL
                pts_sm = [(-2.0, wy - 2.6, -7.2), (-9.8, wy - 4.4, -4.5), (-9.8, wy + 4.4, -10.8), (-2.0, wy + 2.6, -9.8)]
                surf_fx.add_part(pts_sm, [(-0.6, 0.0, 0.8)] * 4, [(su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1)], [(0, 1, 2), (0, 2, 3)], tag="fx_burnout")
                pts_sp = [(+1.0, wy, -8.5), (-8.5, wy - 1.5, -6.0), (-8.5, wy + 1.5, -10.5), (+1.0, wy, -9.8)]
                surf_fx.add_part(pts_sp, [(0.0, 1.0, 0.0)] * 4, [(pu0, pv0), (pu1, pv0), (pu1, pv1), (pu0, pv1)], [(0, 1, 2), (0, 2, 3)], tag="fx_sparks")

            # Post-blast muzzle smoke puff
            pts_ms = [(0.5, -6.5, +6.5), (0.5, +6.5, +6.5), (8.5, +8.5, -3.5), (8.5, -8.5, -3.5)]
            surf_fx.add_part(pts_ms, [(-0.7, 0.0, 0.7)] * 4, [(su0, sv0), (su1, sv0), (su1, sv1), (su0, sv1)], [(0, 1, 2), (0, 2, 3)], tag="fx_muzzlesmoke")
        else:
            for k in range(5):
                a0 = math.radians(k * 72.0)
                a1 = math.radians(k * 72.0 + 32.0)
                am = 0.5 * (a0 + a1)
                pts_sp = [(0.0, 3.0 * math.sin(a0), 3.0 * math.cos(a0)),
                          (0.0, 3.0 * math.sin(a1), 3.0 * math.cos(a1)),
                          (8.0, 9.5 * math.sin(am), 9.5 * math.cos(am))]
                surf_fx.add_part(pts_sp, [(-0.7, 0.5 * math.sin(am), 0.5 * math.cos(am))] * 3,
                                 [(0.5 * (bu0 + bu1), 0.5 * (bv0 + bv1)), (bu1, bv0), (bu1, bv1)], [(0, 1, 2)], tag="fx_burst")

    out = [surf_chrome, surf_wheel]
    if include_hands and len(surf_hands.verts) > 0:
        out.append(surf_hands)
    if include_fx and len(surf_fx.verts) > 0:
        out.append(surf_fx)
    return out


# ===========================================================================
# 48-FRAME SLAPSTICK RUBBERY-SWELL, BURNOUT-TIRE & WHEELIE-KICKBACK SCHEDULE
# ===========================================================================
def build_48_frame_schedule():
    """48-frame cartoon physics schedule (`0..15` idle, `16..25` swell & burnout, `26..29` blast, `30..39` whiplash, `40..47` gulp):
    Every adjacent frame step keeps wheel rotation `|d_spin| <= 42 deg` and lands on exact `720.0 deg` (`0 mod 360`)
    at `f47` so DarkPlaces linear vertex interpolation never shrinks wheel radius or snaps at loop boundaries!"""
    sched = []

    # --- 1. Frames 0..15: Awkward Giant Contraption Heft & Lazy Free-Rolling Wheels (`idle1..idle16`) ---
    for i in range(16):
        ph = 2.0 * math.pi * (i / 16.0)
        sched.append(dict(
            name=f"idle{i + 1}",
            rig_dx=0.22 * math.sin(ph),
            rig_dy=0.20 * math.cos(ph),
            rig_dz=0.28 * math.sin(ph * 2.0 + 0.35),
            rig_pitch=0.75 * math.sin(ph + 0.3),
            rig_yaw=0.55 * math.sin(ph),
            rig_roll=0.95 * math.cos(ph),
            tube_bend=0.35 * math.sin(ph + 0.5),
            tube_s=0.0,
            axial_sc=1.0,
            bulge_amp=0.0,
            bulge_x=-8.0,
            bulge_w=4.5,
            muzzle_flare=0.0,
            axle_swept=0.35 * math.sin(ph),
            axle_droop=-0.45 + 0.30 * math.sin(ph * 2.0),
            spin_L=+24.0 * math.sin(ph),
            spin_R=-20.0 * math.cos(ph),
            burst=0.0, ring1=0.0, ring1_x=0.0, ring2=0.0, ring2_x=0.0,
            burnout=0.0, sparks=0.0, muzzlesmoke=0.0,
        ))

    # --- 2. Frames 16..25: SLAPSTICK PYTHON-BELLY BREECH SWELL & BURNOUT TIRE SPIN-UP (`swell1..swell10`) ---
    spin_steps_charge = [14, 20, 26, 30, 34, 36, 36, 36, 36, 32]  # Cumulative = +300.0 deg!
    cum_spin = 0.0
    for k in range(10):
        u = (k + 1) / 10.0
        ease = u * u * (3.0 - 2.0 * u)
        cum_spin += spin_steps_charge[k]
        vib = (0.45 if k >= 4 else 0.12) * (1.0 if (k % 2 == 0) else -1.0) * u
        sched.append(dict(
            name=f"swell{k + 1}",
            rig_dx=-1.85 * ease + vib * 0.30,
            rig_dy=+0.45 * ease + vib * 0.18,
            rig_dz=-0.65 * ease + vib * 0.25,
            rig_pitch=+3.2 * ease,
            rig_yaw=+1.6 * ease,
            rig_roll=-2.0 * ease + vib * 1.4,
            tube_bend=+15.5 * (u ** 1.2) + vib * 0.9,
            tube_s=-2.5 * ease,
            axial_sc=1.0 - 0.095 * ease,
            bulge_amp=0.56 * (u ** 1.1),          # Massive +56% cartoon belly bulge in the shiny chrome breech!
            bulge_x=-11.5 + 6.5 * ease,           # Bulge creeps forward toward the axle T-collar!
            bulge_w=4.8 - 0.6 * ease,
            muzzle_flare=-0.08 * ease,            # Muzzle pinches slightly tight right before blowing wide open!
            axle_swept=-3.8 * ease + vib * 0.4,   # Skinny axle bows backward (-3.8u at tips) as wheels rev hard!
            axle_droop=-1.4 * ease,
            spin_L=cum_spin,
            spin_R=cum_spin,
            burst=0.0, ring1=0.0, ring1_x=0.0, ring2=0.0, ring2_x=0.0,
            burnout=max(0.0, (u - 0.35) / 0.65) * 0.95,
            sparks=max(0.0, (u - 0.45) / 0.55) * 1.00,
            muzzlesmoke=0.0,
        ))

    # --- 3. Frames 26..29: PERISTALTIC GULP LAUNCH, TRUMPET-BELL FLARE & VIOLENT WHEELIE (`blast1..blast4`) ---
    # Continue wheel spin smoothly from 300 deg -> 456 deg across the 4 blast frames!
    sched.extend([
        # 26 (`blast1` — Peristaltic Surge Past Axle!): Giant +62% bulge rockets down the forward chrome pipe!
        dict(name="blast1",
             rig_dx=-1.4, rig_dy=+0.2, rig_dz=+0.2, rig_pitch=+1.0, rig_yaw=+1.0, rig_roll=+0.6,
             tube_bend=+5.0, tube_s=+4.5, axial_sc=0.96,
             bulge_amp=0.62, bulge_x=+11.2, bulge_w=4.4, muzzle_flare=+0.22,
             axle_swept=-1.2, axle_droop=-0.6, spin_L=340.0, spin_R=340.0,
             burst=0.58, ring1=0.45, ring1_x=1.5, ring2=0.0, ring2_x=0.0,
             burnout=1.10, sparks=1.15, muzzlesmoke=0.20),

        # 27 (`blast2` — PEAK TRUMPET-BELL BLAST!): Black rubber collar flares +68% wide open! Colossal flash!
        dict(name="blast2",
             rig_dx=-3.8, rig_dy=-0.2, rig_dz=+1.4, rig_pitch=+12.5, rig_yaw=+2.0, rig_roll=+2.6,
             tube_bend=-8.5, tube_s=+3.0, axial_sc=1.06,
             bulge_amp=0.38, bulge_x=+19.8, bulge_w=3.8, muzzle_flare=+0.68,
             axle_swept=+2.8, axle_droop=+1.2, spin_L=382.0, spin_R=382.0,
             burst=1.22, ring1=1.12, ring1_x=7.0, ring2=0.72, ring2_x=2.4,
             burnout=1.25, sparks=0.90, muzzlesmoke=0.55),

        # 28 (`blast3` — FULL SLAPSTICK WHEELIE KICKBACK!): Contraption slams -6.6u back & +24 deg up while
        # heavy outer tires whip +4.8u FORWARD on the springy stainless axle!
        dict(name="blast3",
             rig_dx=-6.4, rig_dy=-0.5, rig_dz=+2.8, rig_pitch=+23.5, rig_yaw=+0.8, rig_roll=+4.2,
             tube_bend=+14.0, tube_s=-4.5, axial_sc=0.97,
             bulge_amp=0.0, bulge_x=+20.0, bulge_w=4.0, muzzle_flare=+0.24,
             axle_swept=+4.8, axle_droop=+2.6, spin_L=422.0, spin_R=422.0,
             burst=0.68, ring1=1.32, ring1_x=15.5, ring2=1.08, ring2_x=7.5,
             burnout=0.65, sparks=0.35, muzzlesmoke=0.95),

        # 29 (`blast4` — Peak Wheelie Hangtime):
        dict(name="blast4",
             rig_dx=-6.8, rig_dy=-0.4, rig_dz=+3.1, rig_pitch=+25.5, rig_yaw=-0.6, rig_roll=+3.8,
             tube_bend=+16.5, tube_s=-3.5, axial_sc=0.98,
             bulge_amp=0.0, bulge_x=+10.0, bulge_w=4.0, muzzle_flare=-0.06,
             axle_swept=+4.2, axle_droop=+2.2, spin_L=458.0, spin_R=458.0,
             burst=0.18, ring1=0.0, ring1_x=18.0, ring2=1.25, ring2_x=13.5,
             burnout=0.25, sparks=0.0, muzzlesmoke=1.05),
    ])

    # --- 4. Frames 30..39: BOING-BOING BARBELL AXLE & RUBBERY BARREL WHIPLASH (`recoil1..recoil10`) ---
    # Spin advances smoothly from 458 -> 686 deg across 10 frames (~23 deg/frame)
    spin_recoil = [490, 520, 548, 574, 598, 620, 640, 658, 673, 686]
    for k in range(10):
        u = (k + 1) / 10.0
        decay = math.exp(-2.6 * u)
        osc = math.cos(2.3 * math.pi * u)  # +1 -> -0.8 -> +0.5 -> -0.2 -> 0
        sched.append(dict(
            name=f"recoil{k + 1}",
            rig_dx=-6.8 * ((1.0 - u) ** 1.5),
            rig_dy=-0.4 * (1.0 - u),
            rig_dz=+3.1 * ((1.0 - u) ** 1.6) - 0.6 * math.sin(math.pi * u),
            rig_pitch=+25.5 * ((1.0 - u) ** 1.65) + 3.5 * decay * osc,
            rig_yaw=-0.8 * decay * math.sin(2.0 * math.pi * u),
            rig_roll=+3.8 * ((1.0 - u) ** 1.5) + 2.0 * decay * osc,
            tube_bend=+14.0 * decay * osc,
            tube_s=-5.5 * decay * math.sin(2.3 * math.pi * u),
            axial_sc=1.0 + 0.025 * decay * osc,
            bulge_amp=0.0, bulge_x=0.0, bulge_w=4.5,
            muzzle_flare=0.08 * decay * osc,
            axle_swept=+4.2 * decay * osc,        # Big cart tires boing forward-and-back on the skinny steel axle!
            axle_droop=-0.45 + 2.6 * decay * math.cos(2.3 * math.pi * u + 0.5),
            spin_L=float(spin_recoil[k]),
            spin_R=float(spin_recoil[k]),
            burst=0.0, ring1=0.0, ring1_x=0.0, ring2=0.0, ring2_x=0.0,
            burnout=0.0, sparks=0.0,
            muzzlesmoke=max(0.0, 0.90 * (1.0 - u * 1.15)),
        ))

    # --- 5. Frames 40..47: BREECH "GULP" CHAMBERING & SMOOTH COAST INTO `idle1` (`reload1..reload8`) ---
    # Spin finishes 686 -> 720.0 deg (`720 == 0 mod 360`, zero seam step into `idle1`!)
    spin_reload = [696, 704, 710, 714.5, 717.5, 719.2, 719.8, 720.0]
    for k in range(8):
        u = (k + 1) / 8.0
        gulp_env = math.sin(math.pi * u)
        sched.append(dict(
            name=f"reload{k + 1}",
            rig_dx=-0.9 * gulp_env,
            rig_dy=+0.20 * math.cos(0.5 * math.pi * (1.0 - u)),
            rig_dz=-1.35 * math.sin(math.pi * u),
            rig_pitch=-2.8 * math.sin(math.pi * u),
            rig_yaw=0.0,
            rig_roll=+0.95 * (u ** 2),  # blends seamlessly into idle1's cos(0)=+0.95!
            tube_bend=-1.8 * gulp_env + 0.35 * math.sin(0.5) * (u ** 2),
            tube_s=0.0,
            axial_sc=1.0 - 0.03 * gulp_env,
            bulge_amp=0.30 * gulp_env,            # Satisfying cartoon "gulp" pulse from bullet tip up to seam ring!
            bulge_x=-15.5 + 12.0 * u,
            bulge_w=3.8,
            muzzle_flare=0.0,
            axle_swept=-0.8 * gulp_env,
            axle_droop=-0.45 - 0.75 * gulp_env,
            spin_L=float(spin_reload[k]),
            spin_R=float(spin_reload[k]),
            burst=0.0, ring1=0.0, ring1_x=0.0, ring2=0.0, ring2_x=0.0,
            burnout=0.0, sparks=0.0, muzzlesmoke=0.0,
        ))

    assert len(sched) == 48
    return sched


# ===========================================================================
# SLAPSTICK TUBE & BARBELL-AXLE DEFORMER + 1ST-PERSON EYE PLACEMENT
# ===========================================================================
# Framed so in Quake 90° & 110° FOV you see 100% of:
#   - Both giant pneumatic white-rim hand-truck tires sticking out left & right on the skinny chrome axle!
#   - The ENTIRE gleaming mirror-chrome rounded bullet-dome rear tip + seam ring in the lower-right!
#   - Both Ranger leather & bronze gauntlets gripping the left axle handlebar & rear barrel!
#   - The giant open black-collared chrome cannon barrel aiming toward (but cleanly below!) the crosshair!
EYE_BASE  = np.array([27.4, -3.4, -6.2], dtype=np.float64)
EYE_SCALE = 0.76
EYE_ROLL  = -3.5
EYE_PITCH = -6.5
EYE_YAW   = +10.5


def sample_tube_curve(x_rest, fr):
    """Maps rest `x in [X_REAR_TIP .. X_MUZZLE_TIP]` onto the slapstick bent & axially-squashed tube spine.
    Pivot `x = 0` (the axle T-collar) stays anchored at `(0, 0, 0)` while front & rear curve smoothly!"""
    sc = fr["axial_sc"]
    u = x_rest / 21.6  # ~[-0.86 .. +1.0]
    bend_rad = math.radians(fr["tube_bend"])
    s_rad = math.radians(fr["tube_s"])
    # Parabolic banana-arch (`z = +bend * u^2` lifts both tip & breech relative to center, OR cantilevers forward)
    # Using signed cantilevered + arch blend so positive `tube_bend` arches the cannon muzzle proudly upward!
    theta = bend_rad * u * (0.45 + 0.55 * abs(u)) + s_rad * math.sin(math.pi * u)
    x_c = x_rest * sc * math.cos(0.45 * theta)
    z_c = (x_rest * sc) * (0.52 * bend_rad * u + 0.35 * s_rad * math.sin(math.pi * u))
    pitch_local = bend_rad * (0.52 * 2.0 * u) + s_rad * 0.35 * math.pi * math.cos(math.pi * u)
    cp, sp = math.cos(pitch_local), math.sin(pitch_local)
    T = np.array([cp, 0.0, sp], dtype=np.float64)
    U = np.array([-sp, 0.0, cp], dtype=np.float64)
    B = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    return np.array([x_c, 0.0, z_c], dtype=np.float64), T, B, U


def sample_axle_curve(y_rest, fr):
    """Parabolic barbell-flex of the horizontal stainless-steel axle (`y in [-22..+22]`):
    `axle_swept` bends wheel tips forward (+X) / backward (-X); `axle_droop` bends tips up (+Z) / down (-Z)."""
    yn = y_rest / Y_WHEEL
    u2 = yn * yn
    dx = fr["axle_swept"] * u2
    dz = fr["axle_droop"] * u2
    # Slope derivatives `dx/dy`, `dz/dy` tilt the wheels organically when the skinny axle bows!
    dx_dy = fr["axle_swept"] * (2.0 * yn / Y_WHEEL)
    dz_dy = fr["axle_droop"] * (2.0 * yn / Y_WHEEL)
    return dx, dz, dx_dy, dz_dy


def recompute_vertex_normals(V_arr, tris_ccw, rest_norms=None):
    N = np.zeros_like(V_arr, dtype=np.float64)
    if len(tris_ccw) == 0:
        N[:, 0] = 1.0
        return N
    F = np.asarray(tris_ccw, dtype=np.int32)
    v0, v1, v2 = V_arr[F[:, 0]], V_arr[F[:, 1]], V_arr[F[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    np.add.at(N, F[:, 0], fn)
    np.add.at(N, F[:, 1], fn)
    np.add.at(N, F[:, 2], fn)
    if rest_norms is not None and len(rest_norms) == len(V_arr):
        rn_q = np.round(np.asarray(rest_norms, dtype=np.float64) * 3.0).astype(np.int64)
        qkey = np.hstack([np.round(V_arr * 128.0).astype(np.int64), rn_q])
    else:
        qkey = np.round(V_arr * 128.0).astype(np.int64)
    _, inv = np.unique(qkey, axis=0, return_inverse=True)
    N_weld = np.zeros((inv.max() + 1, 3), dtype=np.float64)
    np.add.at(N_weld, inv, N)
    N = N_weld[inv]
    lens = np.linalg.norm(N, axis=1, keepdims=True)
    return np.where(lens > 1e-11, N / np.maximum(lens, 1e-11), np.array([0.0, 0.0, 1.0]))


def evaluate_surface_for_frame(surf: SurfBuilder, fr: dict, to_eye=True):
    nv = len(surf.verts)
    V_local = np.zeros((nv, 3), dtype=np.float64)

    muz_p, muz_T, muz_B, muz_U = sample_tube_curve(X_MUZZLE_TIP, fr)

    # Precompute wheel spin & axle-tip flex transforms for Left (+Y) and Right (-Y) wheels
    wheel_xf = {}
    for wtag, sgn, spin_key in (("wheel_L", +1.0, "spin_L"), ("wheel_R", -1.0, "spin_R")):
        yc = sgn * Y_WHEEL
        dx_w, dz_w, dx_dy, dz_dy = sample_axle_curve(yc, fr)
        # Positive spin rolls top (+Z) forward (+X): `rot_y_mat(-spin)` or `x' = x*c + z*s, z' = -x*s + z*c`!
        sp_rad = math.radians(fr[spin_key])
        cs, ss = math.cos(sp_rad), math.sin(sp_rad)
        R_spin = np.array([[cs, 0.0, ss], [0.0, 1.0, 0.0], [-ss, 0.0, cs]], dtype=np.float64)
        # Tilt wheel plane perpendicular to the bent axle tangent `(dx_dy, 1, dz_dy)`
        yaw_flex = math.degrees(math.atan(dx_dy))
        roll_flex = math.degrees(math.atan(dz_dy))
        R_flex = rot_z_mat(-yaw_flex) @ rot_x_mat(roll_flex)
        wheel_xf[wtag] = (yc, np.array([dx_w, yc, dz_w], dtype=np.float64), R_flex @ R_spin)

    # Hand anchors tracking the bent axle (`hand_L` at y=+7.8) and swelling rear tube (`hand_R` at x=-6.6)
    dx_hl, dz_hl, _, _ = sample_axle_curve(+7.8, fr)
    p_hr, _, _, _ = sample_tube_curve(-6.6, fr)
    sw_hr = fr["bulge_amp"] * math.exp(-(((-6.6 - fr["bulge_x"]) / fr["bulge_w"]) ** 2))

    for i, (p, tag) in enumerate(zip(surf.verts, surf.deform_tags)):
        px, py, pz = p
        if tag == "tube":
            sp_p, T, B, U = sample_tube_curve(px, fr)
            bulge = fr["bulge_amp"] * math.exp(-(((px - fr["bulge_x"]) / fr["bulge_w"]) ** 2))
            flare = 0.0
            if px > 15.0:
                u_fl = (px - 15.0) / (X_MUZZLE_TIP - 15.0)
                flare = fr["muzzle_flare"] * (max(0.0, u_fl) ** 1.65)
            r_sc = max(0.25, 1.0 + bulge + flare)
            V_local[i] = sp_p + B * (py * r_sc) + U * (pz * r_sc)

        elif tag == "axle":
            dx_a, dz_a, _, _ = sample_axle_curve(py, fr)
            V_local[i] = (px + dx_a, py, pz + dz_a)

        elif tag in ("wheel_L", "wheel_R"):
            yc, w_ctr, R_w = wheel_xf[tag]
            rel = np.array([px, py - yc, pz], dtype=np.float64)
            V_local[i] = w_ctr + R_w @ rel

        elif tag == "hand_L":
            V_local[i] = (px + dx_hl, py, pz + dz_hl)

        elif tag == "hand_R":
            V_local[i] = (px + (p_hr[0] - (-6.6)), py - 0.85 * sw_hr, pz + p_hr[2] - 0.75 * sw_hr)

        elif tag == "fx_burst":
            sc_b = fr["burst"] if fr["burst"] > 0.02 else 0.0004
            V_local[i] = muz_p + muz_T * (px * sc_b) + muz_B * (py * sc_b) + muz_U * (pz * sc_b)

        elif tag == "fx_ring1":
            sc_r = fr["ring1"] if fr["ring1"] > 0.02 else 0.0004
            c_r = muz_p + muz_T * fr["ring1_x"]
            V_local[i] = c_r + muz_T * (px * sc_r) + muz_B * (py * sc_r) + muz_U * (pz * sc_r)

        elif tag == "fx_ring2":
            sc_r = fr["ring2"] if fr["ring2"] > 0.02 else 0.0004
            c_r = muz_p + muz_T * fr["ring2_x"]
            V_local[i] = c_r + muz_T * (px * sc_r) + muz_B * (py * sc_r) + muz_U * (pz * sc_r)

        elif tag == "fx_burnout":
            sc_sm = fr["burnout"] if fr["burnout"] > 0.02 else 0.0004
            sgn = 1.0 if py >= 0.0 else -1.0
            _, w_ctr, _ = wheel_xf["wheel_L" if sgn > 0 else "wheel_R"]
            anchor = w_ctr + np.array([0.0, 0.0, -8.5], dtype=np.float64)
            rel = np.array([px, py - sgn * Y_WHEEL, pz + 8.5], dtype=np.float64)
            V_local[i] = anchor + rel * sc_sm

        elif tag == "fx_sparks":
            sc_sp = fr["sparks"] if fr["sparks"] > 0.02 else 0.0004
            sgn = 1.0 if py >= 0.0 else -1.0
            _, w_ctr, _ = wheel_xf["wheel_L" if sgn > 0 else "wheel_R"]
            anchor = w_ctr + np.array([0.0, 0.0, -8.8], dtype=np.float64)
            rel = np.array([px, py - sgn * Y_WHEEL, pz + 8.8], dtype=np.float64)
            V_local[i] = anchor + rel * sc_sp

        elif tag == "fx_muzzlesmoke":
            sc_ms = fr["muzzlesmoke"] if fr["muzzlesmoke"] > 0.02 else 0.0004
            V_local[i] = muz_p + muz_T * (px * sc_ms) + muz_B * (py * sc_ms) + muz_U * (pz * sc_ms)

        else:
            V_local[i] = (px, py, pz)

    N_local = recompute_vertex_normals(V_local, surf.tris, rest_norms=surf.norms)
    if not to_eye:
        return V_local, N_local

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


# ===========================================================================
# 3RD-PERSON HELD `VWEP` BUILDER (`progs/p_rodcannon.md3`, 259 FRAMES!)
# ===========================================================================
def build_third_person_vwep(tex_paths):
    """Builds `progs/p_rodcannon.md3` (259 frames) riding Combat+'s `progs/p_rock2.md3` bazooka grip,
    PLUS animated rolling wheels on run frames (`0..11`) and slapstick swell/blast on attack frames (`103..118`)!"""
    with zipfile.ZipFile(Q15_PK3, "r") as z:
        tmp_p = os.path.join(STAGE_DIR, "_tmp_prock2.md3")
        open(tmp_p, "wb").write(z.read("progs/p_rock2.md3"))
    ref_md3 = md3lib.read(tmp_p)
    os.remove(tmp_p)
    ref_frames = ref_md3["surfaces"][0]["frames"]
    n_ref = len(ref_frames)  # 259

    # Recover rigid basis of `p_rock2.md3` at stand1 (frame 12) and track across all 259 frames!
    v12 = np.asarray(ref_frames[12][0], dtype=np.float64)
    ctr = v12.mean(axis=0)
    cov = (v12 - ctr).T @ (v12 - ctr)
    eigvals, eigvecs = np.linalg.eigh(cov)
    fwd12 = eigvecs[:, np.argmax(eigvals)]
    if fwd12[0] < 0:
        fwd12 = -fwd12
    proj = (v12 - ctr) @ fwd12
    ia = int(np.argmin(proj))
    ib = int(np.argmax(proj))
    offs = (v12 - ctr) - np.outer(proj, fwd12)
    ic = int(np.argmax(np.sum(offs * offs, axis=1)))

    def frame_basis(pts_arr):
        e1 = pts_arr[ib] - pts_arr[ia]
        e1 /= max(1e-9, np.linalg.norm(e1))
        v_c = pts_arr[ic] - pts_arr[ia]
        e2 = v_c - e1 * np.dot(v_c, e1)
        e2 /= max(1e-9, np.linalg.norm(e2))
        e3 = np.cross(e1, e2)
        return np.stack([e1, e2, e3], axis=1)  # columns = basis vectors (3x3)

    B12 = frame_basis(v12)
    # Canonical gun frame at stand1 (`f12`): `fwd12` forward, world-up orthogonalized for `up12`, `left12 = up x fwd`
    up_hint = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    up12 = up_hint - fwd12 * np.dot(up_hint, fwd12)
    up12 /= max(1e-9, np.linalg.norm(up12))
    left12 = np.cross(up12, fwd12)
    left12 /= max(1e-9, np.linalg.norm(left12))
    R_gun_to_12 = np.stack([fwd12, left12, up12], axis=1)

    # Place gun T-collar slightly forward of `p_rock2` center so the mirror-chrome bullet tip juts over Ranger's shoulder
    # and the wide axle + two giant pneumatic cart wheels clear Ranger's torso cleanly on both sides!
    gun_scale_3p = 0.92
    anchor12 = ctr + fwd12 * 3.2 + up12 * 1.5

    # Use clean 3rd-person LOD (`include_hands=False`, `include_fx=True`) so 259-frame MD3 stays crisp & fast (~6 MB)!
    builders_3p = build_contraption_rest_surfaces(lod="hd", include_hands=False, include_fx=True)
    idle_base = build_48_frame_schedule()[0].copy()
    idle_base.update(rig_dx=0, rig_dy=0, rig_dz=0, rig_pitch=0, rig_yaw=0, rig_roll=0,
                     tube_bend=0, axle_swept=0, axle_droop=0, spin_L=0, spin_R=0)

    def params_for_player_frame(fi):
        p = idle_base.copy()
        if 0 <= fi <= 5:      # axrun1..6: rolling wheels!
            p["spin_L"] = p["spin_R"] = (fi % 6) * 60.0
            p["axle_droop"] = -0.8 + 0.6 * math.sin(2.0 * math.pi * fi / 6.0)
        elif 6 <= fi <= 11:   # rockrun1..6: full 360° rolling hand-truck wheels!
            k = fi - 6
            p["spin_L"] = p["spin_R"] = k * 60.0
            p["axle_droop"] = -0.8 + 0.8 * math.sin(2.0 * math.pi * k / 6.0)
            p["axle_swept"] = 0.7 * math.cos(2.0 * math.pi * k / 6.0)
        elif 12 <= fi <= 16:  # stand1..5
            k = fi - 12
            p["spin_L"] = 12.0 * math.sin(2.0 * math.pi * k / 5.0)
            p["spin_R"] = -12.0 * math.sin(2.0 * math.pi * k / 5.0)
        elif 103 <= fi <= 106:  # nailatt / light: rapid burnout spin + jitter!
            k = fi - 103
            p["bulge_amp"] = 0.42
            p["bulge_x"] = -6.0 + 12.0 * (k % 2)
            p["muzzle_flare"] = 0.45 if (k % 2 == 1) else 0.10
            p["burst"] = 0.85 if (k % 2 == 1) else 0.25
            p["spin_L"] = p["spin_R"] = k * 90.0
        elif 107 <= fi <= 118:  # rockatt1..6 (107..112) & shotatt1..6 (113..118): full slapstick swell & blast!
            k = (fi - 107) % 6
            if k == 0:
                p.update(bulge_amp=0.55, bulge_x=+6.0, axial_sc=0.93, tube_bend=+9.0, muzzle_flare=+0.15,
                         axle_swept=-2.5, spin_L=60.0, spin_R=60.0, burnout=0.9, burst=0.45)
            elif k == 1:
                p.update(bulge_amp=0.35, bulge_x=+19.5, axial_sc=1.05, tube_bend=-6.0, muzzle_flare=+0.68,
                         axle_swept=+3.2, spin_L=120.0, spin_R=120.0, burst=1.15, ring1=1.0, ring1_x=6.5, burnout=1.1)
            elif k == 2:
                p.update(tube_bend=+13.0, axle_swept=+4.5, axle_droop=+2.0, spin_L=180.0, spin_R=180.0,
                         ring1=1.25, ring1_x=14.0, muzzlesmoke=0.95)
            elif k == 3:
                p.update(tube_bend=-6.5, axle_swept=-2.4, spin_L=240.0, spin_R=240.0, muzzlesmoke=0.65)
            elif k == 4:
                p.update(tube_bend=+3.0, axle_swept=+1.1, spin_L=300.0, spin_R=300.0, muzzlesmoke=0.30)
            else:
                p.update(bulge_amp=0.22, bulge_x=-10.0, spin_L=330.0, spin_R=330.0)
        return p

    # Cache unique local deformations so identical idle/death local meshes aren't recomputed 259 times!
    frames_per_surf = [[] for _ in builders_3p]
    base_cache = {}
    for fi in range(n_ref):
        pf = params_for_player_frame(fi)
        ckey = tuple(sorted(pf.items()))
        if ckey not in base_cache:
            base_cache[ckey] = [evaluate_surface_for_frame(sb, pf, to_eye=False) for sb in builders_3p]
        loc_vn_list = base_cache[ckey]

        vf_ref = np.asarray(ref_frames[fi][0], dtype=np.float64)
        Bf = frame_basis(vf_ref)
        R_12_to_f = Bf @ B12.T
        t_12_to_f = vf_ref[ia] - R_12_to_f @ v12[ia]

        R_gun_to_f = R_12_to_f @ R_gun_to_12
        orig_f = R_12_to_f @ anchor12 + t_12_to_f

        # Extra axial kickback along barrel on blast frames (`k == 1, 2` of rockatt/shotatt)
        kick_back = 0.0
        if 107 <= fi <= 118 and ((fi - 107) % 6) in (1, 2):
            kick_back = -4.2 if ((fi - 107) % 6) == 2 else -2.5
        orig_f = orig_f + (R_gun_to_f[:, 0]) * kick_back

        for si, (V_loc, N_loc) in enumerate(loc_vn_list):
            V_w = (V_loc * gun_scale_3p) @ R_gun_to_f.T + orig_f
            N_w = N_loc @ R_gun_to_f.T
            frames_per_surf[si].append((V_w, N_w))

    fnames_3p = [f"pframe{i + 1}" for i in range(n_ref)]
    p_md3 = pack_md3_surfaces(builders_3p, frames_per_surf)
    write_md3_with_skins("p_rodcannon", p_md3, fnames_3p, ["p_rodcannon"])
    return p_md3


# ===========================================================================
# MD3 + DARKPLACES VBO SURFACE ALIGNMENT + VANILLA QUAKE 1 `.MDL` + `.GLB`
# ===========================================================================
def pack_md3_surfaces(surf_builders, frames_list_per_surf):
    md3_surfs = []
    for sb, f_vn in zip(surf_builders, frames_list_per_surf):
        tris_cw = [(int(a), int(c), int(b)) for a, b, c in sb.tris]
        st_l = [(float(u), float(v)) for u, v in sb.st]
        fr_l = [
            ([(float(p[0]), float(p[1]), float(p[2])) for p in V_f],
             [(float(n[0]), float(n[1]), float(n[2])) for n in N_f])
            for V_f, N_f in f_vn
        ]
        md3_surfs.append(dict(name=sb.name, shader=sb.shader, mat=sb.mat, tris=tris_cw, st=st_l, frames=fr_l))
    return md3_surfs


def _unique_st_list(st_list, start_idx=0):
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
    """Prevents DarkPlaces `gl_vbo 1` multi-surface animated MD3 UV rebase bug with zero extra triangles."""
    if len(md3_surfs) <= 1:
        return md3_surfs
    by_priority = sorted(
        md3_surfs[1:],
        key=lambda x: {"rod_wheel": 0, "ranger_hands": 1, "rod_fx": 2}.get(x["name"], 9),
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
        assert len(s["st"]) <= 4096 and len(s["tris"]) <= 8192, (
            f"MD3 surface overflow on {model_name}/{s['name']}: nv={len(s['st'])}, nt={len(s['tris'])}"
        )
    stage_p = os.path.join(STAGE_DIR, f"{model_name}.md3")
    md3lib.write(stage_p, dict(name=model_name, surfaces=dp_surfs, nframes=nf, frame_names=frame_names))
    rt = md3lib.read(stage_p)
    assert rt["nframes"] == nf and len(rt["surfaces"]) == len(dp_surfs)

    skin_txt = "\n".join(f"{s['name']},{s['shader']}" for s in dp_surfs) + "\n"
    open(stage_p + "_0.skin", "w", encoding="ascii", newline="\n").write(skin_txt)

    for dname in deploy_names:
        dp = os.path.join(PROGS_DIR, f"{dname}.md3")
        shutil.copy2(stage_p, dp)
        open(dp + "_0.skin", "w", encoding="ascii", newline="\n").write(skin_txt)
        open(dp + "_1.skin", "w", encoding="ascii", newline="\n").write(skin_txt)

    tv = sum(len(s["st"]) for s in md3_surfs)
    tt = sum(len(s["tris"]) for s in md3_surfs)
    print(f"  [MD3 OK] {model_name:14s} -> {deploy_names}: {len(dp_surfs)} surfs, {tv:4d}v (s0={len(dp_surfs[0]['st'])}<=4096), {tt:4d}t, {nf:3d}f")
    return stage_p


def load_quake_palette_and_anorms():
    pak_p = next((p for p in PAK_PATHS if os.path.exists(p)), None)
    assert pak_p is not None, "Could not find id1/pak0.pak"
    d = open(pak_p, "rb").read()
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
    im = rgb_img.convert("RGB")
    w, h = im.size
    arr = np.asarray(im, dtype=np.uint8)
    bgr = arr[:, :, ::-1].tobytes()
    hdr = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, w, h, 24, 0x20)
    open(path, "wb").write(hdr + bgr)


def export_strict_quake_mdl(model_name, md3_surfs, frame_names, tex_paths, pal, anorms, deploy_names, flags=0):
    SW, SH = 512, 256
    atlas_lo = np.asarray(Image.open(tex_paths["mdl_atlas_lo"]).convert("RGB"), dtype=np.float32)
    atlas_hi = Image.open(tex_paths["mdl_atlas_hi"]).convert("RGB")

    flat = atlas_lo.reshape(-1, 3)
    d_lit = np.sum((flat[:, None, :] - pal[None, :224, :]) ** 2, axis=2)
    idx_lit = np.argmin(d_lit, axis=1).astype(np.uint8)
    d_fb = np.sum((flat[:, None, :] - pal[None, 224:255, :]) ** 2, axis=2)
    idx_fb = (224 + np.argmin(d_fb, axis=1)).astype(np.uint8)

    yy, xx = np.mgrid[0:SH, 0:SW]
    is_glow_zone = (xx >= 384) & (yy >= 128)
    lum = 0.299 * atlas_lo[..., 0] + 0.587 * atlas_lo[..., 1] + 0.114 * atlas_lo[..., 2]
    use_fb = (is_glow_zone & (lum > 135.0)).reshape(-1)
    skin_bytes = np.where(use_fb, idx_fb, idx_lit).astype(np.uint8).tobytes()

    uv_remap = {
        "chrome": (0.000, 0.00, 0.375, 1.00),
        "wheel":  (0.375, 0.00, 0.375, 1.00),
        "hand":   (0.750, 0.00, 0.250, 0.50),
        "fx":     (0.750, 0.50, 0.250, 0.50),
    }

    nf = len(frame_names)
    mpos = [[] for _ in range(nf)]
    mnor = [[] for _ in range(nf)]
    mst, tris = [], []

    for s in md3_surfs:
        ox, oy, sx, sy = uv_remap[s["mat"]]
        base = len(mst)
        for u, v in s["st"]:
            au = ox + np.clip(u, 0.002, 0.998) * sx
            av = oy + np.clip(v, 0.002, 0.998) * sy
            mst.append((max(0, min(SW - 1, int(round(au * SW - 0.5)))),
                        max(0, min(SH - 1, int(round(av * SH - 0.5))))))
        for fi in range(nf):
            mpos[fi].extend(s["frames"][fi][0])
            mnor[fi].extend(s["frames"][fi][1])
        tris.extend((base + a, base + b, base + c) for a, b, c in s["tris"])

    pos_np = np.array(mpos, dtype=np.float64)
    nor_np = np.array(mnor, dtype=np.float64)
    mn = pos_np.min(axis=(0, 1))
    mx = pos_np.max(axis=(0, 1))
    scale = np.maximum((mx - mn) / 255.0, 1e-6)
    origin = mn.copy()

    qpos = np.clip(np.round((pos_np - origin[None, None, :]) / scale[None, None, :]), 0, 255).astype(np.uint8)
    dots = np.einsum("fvc,nc->fvn", nor_np, anorms)
    qnrm = np.argmax(dots, axis=2).astype(np.uint8)

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
    assert nv <= 1024, f"MAXALIASVERTS (1024) exceeded in {model_name}.mdl: nv={nv}"
    assert nt <= 2048, f"MAXALIASTRIS (2048) exceeded in {model_name}.mdl: nt={nt}"

    keep_arr = np.array(keep, dtype=np.int32)
    qpos_k = qpos[:, keep_arr, :]
    qnrm_k = qnrm[:, keep_arr]
    wpos_k = qpos_k.astype(np.float64) * scale[None, None, :] + origin[None, None, :]
    radius = float(np.sqrt(np.sum(wpos_k ** 2, axis=2)).max())

    out = bytearray()
    out += struct.pack("<4si", b"IDPO", 6)
    out += struct.pack("<3f3ff3f", float(scale[0]), float(scale[1]), float(scale[2]),
                       float(origin[0]), float(origin[1]), float(origin[2]), radius, 0.0, 0.0, 0.0)
    out += struct.pack("<iiiiiiiif", 1, SW, SH, nv, nt, nf, 0, flags, 0.0)
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
        out += np.column_stack([qpos_k[fi], qnrm_k[fi]]).astype(np.uint8).tobytes()

    stage_mdl = os.path.join(STAGE_DIR, f"{model_name}.mdl")
    open(stage_mdl, "wb").write(out)

    import md3_to_mdl
    md3_to_mdl.read_mdl(stage_mdl)

    for dname in deploy_names:
        dp = os.path.join(PROGS_DIR, f"{dname}.mdl")
        shutil.copy2(stage_mdl, dp)
        write_uncompressed_tga(dp + "_0.tga", atlas_hi)

    print(f"  [MDL OK] {model_name:14s} -> {deploy_names}: {nv:4d}v (<=1024!), {nt:4d}t (<=2048!), {nf:3d}f, skin {SW}x{SH}")
    return stage_mdl


def build_world_pickup(lod, tex_paths, pal, anorms):
    """Centered World Pickup (`g_rodcannon`): posed at the exact 35° mortar/cannon tilt from video frames 00:05-00:06!"""
    is_hd = (lod == "hd")
    builders = build_contraption_rest_surfaces(lod=lod, include_hands=False, include_fx=False)
    fr0 = build_48_frame_schedule()[0].copy()
    fr0.update(tube_bend=0.0, axle_swept=0.0, axle_droop=0.0, spin_L=0.0, spin_R=0.0)
    R_tilt = rot_y_mat(+34.0)  # Tilts open black-collared pipe upward & rounded chrome tip down like a field cannon!
    pk_frames = []
    for sb in builders:
        V_loc, N_loc = evaluate_surface_for_frame(sb, fr0, to_eye=False)
        V_w = (V_loc * 0.90) @ R_tilt.T + np.array([0.0, 0.0, 16.0], dtype=np.float64)
        N_w = N_loc @ R_tilt.T
        pk_frames.append([(V_w, N_w)])
    pk_md3 = pack_md3_surfaces(builders, pk_frames)
    if is_hd:
        write_md3_with_skins("g_rodcannon", pk_md3, ["pickup1"], ["g_rodcannon"])
    else:
        # EF_ROTATE = 8 so Quake weapon pickups spin automatically!
        export_strict_quake_mdl("g_rodcannon", pk_md3, ["pickup1"], tex_paths, pal, anorms, ["g_rodcannon"], flags=8)
    return pk_md3


def export_glb_model(glb_path, md3_surfs, tex_paths, frame_idx=0):
    bin_buf = bytearray()
    buffer_views, accessors, images, textures, materials, primitives = [], [], [], [], [], []
    mat_map = {}

    mat_cfg = {
        "chrome": dict(metallic=0.95, roughness=0.11, emit=False),
        "wheel":  dict(metallic=0.14, roughness=0.46, emit=False),
        "hand":   dict(metallic=0.22, roughness=0.54, emit=False),
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
        sc = 0.03
        gv = np.stack([-qv[:, 1] * sc, qv[:, 2] * sc, -qv[:, 0] * sc], axis=1).astype(np.float32)
        gn = np.stack([-qn[:, 1], qn[:, 2], -qn[:, 0]], axis=1).astype(np.float32)
        gn /= np.maximum(1e-6, np.linalg.norm(gn, axis=1, keepdims=True))
        uv = np.asarray(s["st"], dtype=np.float32)
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
        "asset": {"version": "2.0", "generator": "BakersfieldQuake Chrome-Rod Contraption Bazooka Builder"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": os.path.splitext(os.path.basename(glb_path))[0]}],
        "meshes": [{"primitives": primitives, "name": "rod_cannon"}],
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
    shader = """// written by source/mm_tools/rod_cannon/build_rod_cannon.py

progs/rod_chrome
{
\tcull none
\t{
\t\tmap progs/rod_chrome
\t\trgbGen lightingDiffuse
\t}
}

progs/rod_wheel
{
\tcull none
\t{
\t\tmap progs/rod_wheel
\t\trgbGen lightingDiffuse
\t}
}

progs/rod_hand
{
\tcull none
\t{
\t\tmap progs/rod_hand
\t\trgbGen lightingDiffuse
\t}
}

progs/rod_fx
{
\tcull none
\tsort 10
\t{
\t\tmap progs/rod_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""
    sh_path = os.path.join(SCRIPTS_DIR, "rodcannon.shader")
    open(sh_path, "w", encoding="ascii", newline="\n").write(shader)
    print(f"  [SHADER OK] {sh_path}")


def main():
    os.makedirs(STAGE_DIR, exist_ok=True)
    print("1/6 Synthesizing studio chrome, 6-rib pneumatic cart tires, white 4-hole steel rims, Ranger glove & FX textures...")
    tex_paths = rtex.build_all_textures(TEX_DIR, PROGS_DIR)
    pal, anorms = load_quake_palette_and_anorms()

    sched = build_48_frame_schedule()
    frame_names = [fr["name"] for fr in sched]

    print("2/6 Baking 48-frame HD 1st-Person Contraption Bazooka (`progs/v_rodcannon.md3`)...")
    hd_builders = build_contraption_rest_surfaces(lod="hd", include_hands=True, include_fx=True)
    hd_frames_per_surf = [[] for _ in hd_builders]
    for fr in sched:
        for si, sb in enumerate(hd_builders):
            hd_frames_per_surf[si].append(evaluate_surface_for_frame(sb, fr, to_eye=True))
    hd_md3_surfs = pack_md3_surfaces(hd_builders, hd_frames_per_surf)
    write_md3_with_skins("v_rodcannon", hd_md3_surfs, frame_names, ["v_rodcannon"])

    print("3/6 Baking 48-frame Strict Vanilla-Legal Quake 1 `.MDL` (`progs/v_rodcannon.mdl` + `_0.tga`)...")
    mdl_builders = build_contraption_rest_surfaces(lod="mdl", include_hands=True, include_fx=True)
    mdl_frames_per_surf = [[] for _ in mdl_builders]
    for fr in sched:
        for si, sb in enumerate(mdl_builders):
            mdl_frames_per_surf[si].append(evaluate_surface_for_frame(sb, fr, to_eye=True))
    mdl_surfs_packed = pack_md3_surfaces(mdl_builders, mdl_frames_per_surf)
    export_strict_quake_mdl("v_rodcannon", mdl_surfs_packed, frame_names, tex_paths, pal, anorms, ["v_rodcannon"])

    print("4/6 Baking 259-frame 3rd-Person Held `vwep` (`progs/p_rodcannon.md3`, riding `p_rock2.md3` w/ rolling & blast anims)...")
    p_md3_surfs = build_third_person_vwep(tex_paths)

    print("5/6 Baking Centered World Pickup (`progs/g_rodcannon.md3` & `.mdl`)...")
    pk_hd_surfs = build_world_pickup("hd", tex_paths, pal, anorms)
    build_world_pickup("mdl", tex_paths, pal, anorms)

    print("6/6 Writing DarkPlaces Shader & Self-Contained PBR `.GLB` Models...")
    write_quake_shader()
    export_glb_model(os.path.join(MOD_ROOT, "rod_cannon_weapon.glb"), hd_md3_surfs, tex_paths, frame_idx=0)
    export_glb_model(os.path.join(STAGE_DIR, "rod_cannon_blast_pose.glb"), hd_md3_surfs, tex_paths, frame_idx=27)
    export_glb_model(os.path.join(MOD_ROOT, "rod_cannon_thirdperson.glb"), p_md3_surfs, tex_paths, frame_idx=12)
    export_glb_model(os.path.join(MOD_ROOT, "rod_cannon_pickup.glb"), pk_hd_surfs, tex_paths, frame_idx=0)

    meta = dict(
        nFrames=len(frame_names),
        frameNames=frame_names,
        idleRange=[0, 15],
        swellRange=[16, 25],
        blastRange=[26, 29],
        launchFrame=27,
        recoilRange=[30, 39],
        reloadRange=[40, 47],
    )
    open(os.path.join(OUT_ROOT, "rod_meta.json"), "w", encoding="utf-8").write(json.dumps(meta, indent=2))
    print("ALL CHROME-ROD CONTRAPTION BAZOOKA MODELS BUILT & VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
