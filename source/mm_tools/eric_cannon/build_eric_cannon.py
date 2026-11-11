"""Master 3D Procedural Geometry, Anatomical Facial/Ear Sculptor, Curvilinear Wew-Cannon
Wind-Up/Blast Deformer & Multi-Format Exporter for THE ERIC DEASON CANNON.

Produces:
  1. `progs/eric_tripod.md3` (+ `_0.skin`, `_1.skin`) : 4-leg bolted splayed tripod + azimuth pedestal (`z=0..29.8u`)
  2. `progs/eric_yoke.md3`   (+ `_0.skin`, `_1.skin`) : U-shaped armored elevation cradle + trunnion hubs
  3. `progs/eric_cannon.md3` (+ `_0.skin`, `_1.skin`) : 77-frame launcher tube + strapped Eric Deason head +
                                                        articulated giant human ears + additive Wew-Cannon blast FX
  4. `scripts/eric_cannon.shader`                     : DarkPlaces diffuse & additive FX shaders
  5. `eric_deason_cannon.glb`                         : Full assembled monument PBR glTF 2.0 model

77-Frame Animation Schedule (`progs/eric_cannon.md3`):
  - Frame   0     (`ref_static`, 1f) : Exact studio turntable reference pose (used for Audits 1, 2, 3)
  - Frames  1..16 (`idle1..16`, 16f) : Lifelike asymmetric giant-ear radar twitching & listening
  - Frames 17..25 (`windup1..9`, 9f) : Hilarious WEW-CANNON wind-up — olive tube bends +38 deg skyward,
                                       squashes axially, swells a +52% peristaltic cartoon belly bulge,
                                       Eric braces back while his giant ears pin flat back (-50 deg)!
  - Frames 26..29 (`blast1..4`,  4f) : Peak explosion & launch — bulge surges out flared muzzle bell,
                                       ears snap wide open (+36 deg), 3D starburst + Mach shockwave rings erupt!
  - Frames 30..32 (`liftoff1..3`,3f) : Springy S-bend whiplash settle into rocket boost climb
  - Frames 33..44 (`boost1..12`,12f) : Sky-high rocket climb — roaring Venturi shock-diamond exhaust & swept ears
  - Frames 45..60 (`glide1..16`,16f) : Sky-high cruise glide — giant ears beat & feather like fleshy wings!
  - Frames 61..68 (`dive1..8`,   8f) : Steep nose-dive (`W` held) — ears swept back (-42 deg) with aero-flutter
  - Frames 69..76 (`flare1..8`,  8f) : Parachute airbrake (`S` held) — giant ears cupped wide forward (+38 deg)
"""
import json
import math
import os
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

OUT_ROOT = os.path.join(MM_TOOLS, "out", "eric_cannon")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
STAGE_DIR = os.path.join(OUT_ROOT, "models")

for p in (MM_TOOLS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import md3lib
import make_eric_cannon_textures as etex


# ==============================================================================
# MONUMENT CALIBRATION CONSTANTS (0.169065 u/px on 1168x768 turntable -> 94.2u tall)
# ==============================================================================
YOKE_BASE_Z = 24.0          # Top of stout cast-iron tripod pedestal drum -> base of yawing yoke
CANNON_REST_Z = 56.8        # World Z of barrel centerline above yaw axis in resting +15.6 deg pose
CANNON_REST_X = 0.0         # World X of barrel centerline origin in resting pose
REST_PITCH_DEG = 15.6       # Resting barrel elevation in reference video (+angles_x tilts +X UP!)

# Barrel stations along local +X axis (`s = 0` at saddle center `(0, 0, 0)`):
S_REAR = -76.5              # Rearmost venturi rim lip
S_MUZZLE = 49.0             # Frontmost black muzzle bell lip (total tube length = 125.5u)

# Eric Head center sits in the UPPER portion of the R=19.6u muzzle opening (`z_muzzle = 69.9u`):
#   Crown `z = 94.2u` (+4.7u above top lip), Chin `z = 61.0u` (+10.7u above bottom lip -> bold black muzzle crescent below chin!)
HEAD_WORLD_CENTER = (59.8, 0.0, 77.6)
HEAD_HALF_H = 16.6          # Total head height = 33.2u


# ==============================================================================
# MATH & SURFACE BUILDER HELPERS
# ==============================================================================
def vnorm(v):
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    l = math.sqrt(x * x + y * y + z * z)
    if l < 1e-9:
        return (1.0, 0.0, 0.0)
    return (x / l, y / l, z / l)


def rot_x_pt(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y_up_pt(p, deg):
    """Positive `deg` pitches `+X` UPWARD toward `+Z` (matching DarkPlaces `+angles_x`!)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[2] * s, p[1], p[0] * s + p[2] * c)


def rot_z_pt(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def world_rest_to_cannon_local(p_world):
    """Converts a point in resting monument world space into `eric_cannon.md3` local space
    (where barrel axis is `+X` and resting world pose pitches cannon by `+REST_PITCH_DEG` at `z=CANNON_REST_Z`)."""
    dx = p_world[0] - CANNON_REST_X
    dy = p_world[1]
    dz = p_world[2] - CANNON_REST_Z
    return rot_y_up_pt((dx, dy, dz), -REST_PITCH_DEG)


def world_dir_to_cannon_local(n_world):
    return rot_y_up_pt(n_world, -REST_PITCH_DEG)


class SurfBuilder:
    def __init__(self, name, shader, mat_key):
        self.name = name
        self.shader = shader
        self.mat = mat_key
        self.verts = []
        self.norms = []
        self.st = []
        self.tris = []          # Stored CCW-outward; converted to CW-outward on MD3 pack
        self.tags = []          # Per-vertex deformation tag

    def add_part(self, verts, norms, st, tris_ccw, tag="barrel"):
        base = len(self.verts)
        self.verts.extend(verts)
        self.norms.extend(norms)
        self.st.extend(st)
        self.tags.extend([tag] * len(verts))
        for a, b, c in tris_ccw:
            pa, pb, pc = verts[a], verts[b], verts[c]
            e1 = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])
            e2 = (pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2])
            fn = (
                e1[1] * e2[2] - e1[2] * e2[1],
                e1[2] * e2[0] - e1[0] * e2[2],
                e1[0] * e2[1] - e1[1] * e2[0],
            )
            vn = (
                norms[a][0] + norms[b][0] + norms[c][0],
                norms[a][1] + norms[b][1] + norms[c][1],
                norms[a][2] + norms[b][2] + norms[c][2],
            )
            if fn[0] * vn[0] + fn[1] * vn[1] + fn[2] * vn[2] < -1e-9:
                self.tris.append((base + a, base + c, base + b))
            else:
                self.tris.append((base + a, base + b, base + c))


# ==============================================================================
# PRIMITIVE MESH GENERATORS
# ==============================================================================
def build_lathe_x(profile_xr, radial_segs, uv_rect, offset=(0.0, 0.0, 0.0), inward=False):
    """Revolves `(x, r)` profile around `+X` axis (`phi = pi` at `-Z` bottom seam)."""
    u0, v0, u1, v1 = uv_rect
    ox, oy, oz = offset
    nr = len(profile_xr)
    verts, norms, st, tris = [], [], [], []

    slopes = []
    for j in range(nr):
        j0, j1 = max(0, j - 1), min(nr - 1, j + 1)
        dx = profile_xr[j1][0] - profile_xr[j0][0]
        dr = profile_xr[j1][1] - profile_xr[j0][1]
        if abs(dx) < 1e-6:
            nx, nrad = (-1.0 if dr > 0 else 1.0), 0.2
        else:
            nx, nrad = -dr, dx
            if dx < 0:
                nx, nrad = -nx, -nrad
        l = math.hypot(nx, nrad) or 1.0
        nx, nrad = nx / l, nrad / l
        if inward:
            nx, nrad = -nx, -nrad
        slopes.append((nx, nrad))

    for j, (x, r) in enumerate(profile_xr):
        tv = j / max(1, nr - 1)
        nx_s, nr_s = slopes[j]
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
            b = a + 1
            c = a + stride + 1
            d = a + stride
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, norms, st, tris


def build_lathe_z(profile_zr, radial_segs, uv_rect, offset=(0.0, 0.0, 0.0)):
    """Revolves `(z, r)` profile around vertical `+Z` axis."""
    u0, v0, u1, v1 = uv_rect
    ox, oy, oz = offset
    nr = len(profile_zr)
    verts, norms, st, tris = [], [], [], []

    slopes = []
    for j in range(nr):
        j0, j1 = max(0, j - 1), min(nr - 1, j + 1)
        dz = profile_zr[j1][0] - profile_zr[j0][0]
        dr = profile_zr[j1][1] - profile_zr[j0][1]
        if abs(dz) < 1e-6:
            nz, nrad = (-1.0 if dr > 0 else 1.0), 0.2
        else:
            nz, nrad = -dr, dz
            if dz < 0:
                nz, nrad = -nz, -nrad
        l = math.hypot(nz, nrad) or 1.0
        slopes.append((nz / l, nrad / l))

    for j, (z, r) in enumerate(profile_zr):
        tv = 1.0 - (j / max(1, nr - 1))
        nz_s, nr_s = slopes[j]
        for i in range(radial_segs + 1):
            tu = i / radial_segs
            phi = tu * 2.0 * math.pi
            cp, sp = math.cos(phi), math.sin(phi)
            verts.append((ox + r * cp, oy + r * sp, oz + z))
            norms.append((nr_s * cp, nr_s * sp, nz_s))
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))

    stride = radial_segs + 1
    for j in range(nr - 1):
        for i in range(radial_segs):
            a = j * stride + i
            b = a + 1
            c = a + stride + 1
            d = a + stride
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, norms, st, tris


def build_box(x0, x1, y0, y1, z0, z1, uv_rect, xform=None):
    """Builds a crisp 24-vert flat-shaded 3D box with optional point/normal transform."""
    u0, v0, u1, v1 = uv_rect
    faces = [
        # +X front
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1.0, 0.0, 0.0)),
        # -X back
        ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1.0, 0.0, 0.0)),
        # +Y left
        ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0.0, 1.0, 0.0)),
        # -Y right
        ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0.0, -1.0, 0.0)),
        # +Z top
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0.0, 0.0, 1.0)),
        # -Z bottom
        ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0.0, 0.0, -1.0)),
    ]
    verts, norms, st, tris = [], [], [], []
    uvs = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    for pts, nrm in faces:
        b = len(verts)
        for p, uv in zip(pts, uvs):
            if xform is not None:
                p, n_out = xform(p, nrm)
            else:
                n_out = nrm
            verts.append(p)
            norms.append(vnorm(n_out))
            st.append(uv)
        tris.append((b, b + 1, b + 2))
        tris.append((b, b + 2, b + 3))
    return verts, norms, st, tris


def build_curved_barrel_decal(s0, s1, r_fn, phi_top_deg, phi_bot_deg, ns, nphi, uv_rect, flip_u=False, lift=0.22):
    """Curved decal patch hugging the olive tube / conical flare (`phi=0` at `+Z` top, `-90` right `-Y`, `+90` left `+Y`)."""
    u0, v0, u1, v1 = uv_rect
    verts, norms, st, tris = [], [], [], []
    for j in range(nphi + 1):
        tv = j / nphi
        phi = math.radians(phi_top_deg + (phi_bot_deg - phi_top_deg) * tv)
        sp, cp = math.sin(phi), math.cos(phi)
        for i in range(ns + 1):
            tx = i / ns
            s = s0 + (s1 - s0) * tx
            r = r_fn(s) + lift
            verts.append((s, r * sp, r * cp))
            norms.append((0.0, sp, cp))
            tu = (1.0 - tx) if flip_u else tx
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))
    stride = ns + 1
    for j in range(nphi):
        for i in range(ns):
            a = j * stride + i
            b = a + 1
            c = a + stride + 1
            d = a + stride
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, norms, st, tris


def build_ribbon_tube(path_pts, width, thickness, uv_rect):
    """Extrudes a rectangular webbing strap ribbon along `path_pts` in 3D space."""
    u0, v0, u1, v1 = uv_rect
    n = len(path_pts)
    verts, norms, st, tris = [], [], [], []
    hw, ht = width * 0.5, thickness * 0.5

    # Compute smooth Frenet frames using outward radial direction from head center
    frames = []
    for i, p in enumerate(path_pts):
        p0 = path_pts[max(0, i - 1)]
        p1 = path_pts[min(n - 1, i + 1)]
        tang = vnorm((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]))
        # Outward normal points away from head center `HEAD_WORLD_CENTER`
        out_raw = (p[0] - HEAD_WORLD_CENTER[0], p[1], p[2] - HEAD_WORLD_CENTER[2])
        dot_to = out_raw[0] * tang[0] + out_raw[1] * tang[1] + out_raw[2] * tang[2]
        n_out = (out_raw[0] - dot_to * tang[0], out_raw[1] - dot_to * tang[1], out_raw[2] - dot_to * tang[2])
        if math.hypot(n_out[0], math.hypot(n_out[1], n_out[2])) < 1e-4:
            n_out = (0.0, 0.0, 1.0)
        n_out = vnorm(n_out)
        b_side = vnorm((
            tang[1] * n_out[2] - tang[2] * n_out[1],
            tang[2] * n_out[0] - tang[0] * n_out[2],
            tang[0] * n_out[1] - tang[1] * n_out[0],
        ))
        frames.append((tang, n_out, b_side))

    # 4-corner ring per station
    ring_offsets = [(-hw, ht, (0.0, 1.0)), (hw, ht, (0.0, 1.0)), (hw, -ht, (0.0, -1.0)), (-hw, -ht, (0.0, -1.0))]
    for i, (p, (_, n_out, b_side)) in enumerate(zip(path_pts, frames)):
        tv = i / max(1, n - 1)
        for k, (bw, nh, _) in enumerate(ring_offsets):
            tu = k / 4.0
            vx = p[0] + b_side[0] * bw + n_out[0] * nh
            vy = p[1] + b_side[1] * bw + n_out[1] * nh
            vz = p[2] + b_side[2] * bw + n_out[2] * nh
            nx = b_side[0] * (bw / max(hw, 1e-4)) * 0.35 + n_out[0] * (1.0 if nh > 0 else -1.0)
            ny = b_side[1] * (bw / max(hw, 1e-4)) * 0.35 + n_out[1] * (1.0 if nh > 0 else -1.0)
            nz = b_side[2] * (bw / max(hw, 1e-4)) * 0.35 + n_out[2] * (1.0 if nh > 0 else -1.0)
            verts.append((vx, vy, vz))
            norms.append(vnorm((nx, ny, nz)))
            st.append((u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv))
        # Repeat first vertex for clean UV wrap
        bw, nh, _ = ring_offsets[0]
        verts.append((p[0] + b_side[0] * bw + n_out[0] * nh,
                      p[1] + b_side[1] * bw + n_out[1] * nh,
                      p[2] + b_side[2] * bw + n_out[2] * nh))
        norms.append(vnorm((b_side[0] * -0.35 + n_out[0], b_side[1] * -0.35 + n_out[1], b_side[2] * -0.35 + n_out[2])))
        st.append((u1, v0 + (v1 - v0) * tv))

    stride = 5
    for i in range(n - 1):
        for k in range(4):
            a = i * stride + k
            b = a + 1
            c = a + stride + 1
            d = a + stride
            tris.append((a, b, c))
            tris.append((a, c, d))
    return verts, norms, st, tris


# ==============================================================================
# 1. STATIC 4-LEG BOLTED TRIPOD (`progs/eric_tripod.md3`, `z = 0..24.0u`)
# ==============================================================================
def build_tripod_model():
    sb = SurfBuilder("tripod_metal", "progs/eric_cannon_metal", "metal")

    # Stout military cast-iron hub, wide bolted azimuth flange (`R = 19.2u` at `z = 14.2..17.2`), and turret drum
    ped_prof = [
        (6.0,  0.5),
        (6.0,  15.5),
        (13.8, 14.5),
        (14.3, 19.2),
        (17.1, 19.2),
        (17.6, 15.6),
        (22.4, 15.4),
        (22.8, 16.8),
        (24.1, 16.8),
        (24.1, 0.5),
    ]
    v, n, st, t = build_lathe_z(ped_prof, 28, etex.UV_CAST_OLIVE)
    sb.add_part(v, n, st, t, tag="static")

    # Lower structural tie collar (`z = 4.2..8.2u`)
    ring_prof = [(4.2, 15.0), (4.2, 21.4), (8.2, 18.8), (8.2, 14.0), (4.2, 15.0)]
    v, n, st, t = build_lathe_z(ring_prof, 20, etex.UV_OLIVE_TUBE)
    sb.add_part(v, n, st, t, tag="static")

    for leg_deg in (45.0, 135.0, 225.0, 315.0):
        def xf_yaw(p, nm, d=leg_deg):
            return rot_z_pt(p, d), rot_z_pt(nm, d)

        v, n, st, t = build_box(22.5, 33.8, -5.2, 5.2, 0.0, 2.0, etex.UV_CAST_OLIVE, xform=xf_yaw)
        sb.add_part(v, n, st, t, tag="static")
        v, n, st, t = build_box(24.2, 31.4, -4.0, 4.0, 2.0, 4.8, etex.UV_OLIVE_TUBE, xform=xf_yaw)
        sb.add_part(v, n, st, t, tag="static")

        def xf_leg(p, nm, d=leg_deg):
            p1 = rot_y_up_pt(p, -142.0)
            n1 = rot_y_up_pt(nm, -142.0)
            p2 = (p1[0] + 28.8, p1[1], p1[2] + 2.2)
            return rot_z_pt(p2, d), rot_z_pt(n1, d)

        v, n, st, t = build_box(0.0, 21.2, -4.2, 4.2, -2.3, 2.3, etex.UV_CAST_OLIVE, xform=xf_leg)
        sb.add_part(v, n, st, t, tag="static")
        v, n, st, t = build_box(1.5, 19.2, -2.6, 2.6, 2.3, 3.5, etex.UV_OLIVE_TUBE, xform=xf_leg)
        sb.add_part(v, n, st, t, tag="static")

    md3_surfs = pack_md3_surfaces([sb], [[(sb.verts, sb.norms)]])
    write_md3_with_skins("eric_tripod", md3_surfs, ["tripod0"], ["eric_tripod"])
    return md3_surfs


# ==============================================================================
# 2. YAWING ARMORED ELEVATION YOKE (`progs/eric_yoke.md3`, origin at `(0,0,24.0u)`)
# ==============================================================================
def build_yoke_model():
    """Built in local coordinates with `(0,0,0)` at `(0, 0, YOKE_BASE_Z = 24.0u)`."""
    sb = SurfBuilder("yoke_metal", "progs/eric_cannon_metal", "metal")
    z0 = YOKE_BASE_Z

    v, n, st, t = build_box(-14.5, 14.5, -16.0, 16.0, 24.0 - z0, 28.5 - z0, etex.UV_CAST_OLIVE)
    sb.add_part(v, n, st, t, tag="static")

    v, n, st, t = build_box(-20.0, 14.2, -13.2, 13.2, 28.0 - z0, 34.0 - z0, etex.UV_OLIVE_TUBE)
    sb.add_part(v, n, st, t, tag="static")

    for sgn in (-1.0, 1.0):
        ya = 12.8 * sgn
        yb = 17.8 * sgn
        ylo, yhi = min(ya, yb), max(ya, yb)

        def xf_cheek(p, nm, yl=ylo, yh=yhi):
            pr = rot_y_up_pt(p, 13.5)
            nr = rot_y_up_pt(nm, 13.5)
            return (pr[0] - 2.5, pr[1], pr[2] + (37.5 - z0)), nr

        v, n, st, t = build_box(-21.5, 16.5, ylo, yhi, -7.2, 6.8, etex.UV_CAST_OLIVE, xform=xf_cheek)
        sb.add_part(v, n, st, t, tag="static")
        v, n, st, t = build_box(-2.0, 13.5, ylo + 0.3, yhi - 0.3, 41.5 - z0, 51.0 - z0, etex.UV_OLIVE_TUBE)
        sb.add_part(v, n, st, t, tag="static")
        v, n, st, t = build_box(12.8, 15.2, ylo - 0.5, yhi + 0.5, 29.5 - z0, 49.5 - z0, etex.UV_BLACK_COLLAR)
        sb.add_part(v, n, st, t, tag="static")

    hub_prof = [
        (-20.6, 0.4),
        (-20.6, 5.8),
        (-18.2, 6.4),
        (-17.6, 6.4),
        (17.6, 6.4),
        (18.2, 6.4),
        (20.6, 5.8),
        (20.6, 0.4),
    ]
    vx, nx, stx, tx = build_lathe_x(hub_prof, 20, etex.UV_TRUNNION_HUB)
    vy = [(5.8 + p[2], p[0], (38.0 - z0) + p[1]) for p in vx]
    ny = [(nm[2], nm[0], nm[1]) for nm in nx]
    sb.add_part(vy, ny, stx, tx, tag="static")

    for sx0, sx1, sz0, sz1 in ((-18.5, -11.0, 40.0, 44.8), (-1.5, 7.0, 42.8, 47.8)):
        v, n, st, t = build_box(sx0, sx1, -13.4, 13.4, sz0 - z0, sz1 - z0, etex.UV_BLACK_COLLAR)
        sb.add_part(v, n, st, t, tag="static")

    md3_surfs = pack_md3_surfaces([sb], [[(sb.verts, sb.norms)]])
    write_md3_with_skins("eric_yoke", md3_surfs, ["yoke0"], ["eric_yoke"])
    return md3_surfs


# ==============================================================================
# 3. SCULPTED 3D ERIC DEASON HEAD & GIANT CUPPED HUMAN EARS
# ==============================================================================
def _gauss(x, mu, sig):
    z = (x - mu) / sig
    return math.exp(-0.5 * z * z)


def _sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / max(1e-8, b - a)))
    return t * t * (3.0 - 2.0 * t)


def eval_eric_head_world(phi, tv):
    """Parametric 3D anatomical sculpt of Eric Deason's head in resting world space!"""
    cx, cy, cz = HEAD_WORLD_CENTER
    cp, sp = math.cos(phi), math.sin(phi)
    ap = abs(phi)

    dome_sin = math.sin(min(1.0, tv / 0.19) * (math.pi * 0.5)) if tv < 0.19 else 1.0
    z_loc = HEAD_HALF_H * (1.0 - 2.0 * tv)

    # Broader upper cranium/temples (`10.85u`) tapering cleanly through cheeks (`9.95u`) to chin (`6.2u`)
    jaw_taper = _sstep(0.52, 0.96, tv)
    chin_round = _sstep(0.85, 1.00, tv)

    rx_f = (14.6 - 1.8 * jaw_taper - 2.1 * chin_round) * dome_sin
    rx_b = (16.8 - 2.5 * _sstep(0.62, 0.98, tv)) * (math.sin(min(1.0, tv / 0.15) * (math.pi * 0.5)) if tv < 0.15 else 1.0)
    ry_s = (10.85 - 2.15 * jaw_taper - 2.45 * chin_round) * dome_sin

    rx = rx_f if cp >= 0.0 else rx_b
    x_base = rx * cp
    y_base = ry_s * sp

    dx_face = 0.0
    dy_face = 0.0
    dz_face = 0.0

    # 1. Bowl-cut bangs volume (`tv = 0.04..0.245`)
    bangs_w = (1.0 - _sstep(0.21, 0.255, tv)) * _sstep(0.03, 0.10, tv) * (0.45 + 0.55 * max(0.0, cp))
    dx_face += 0.65 * bangs_w * cp
    dy_face += 0.35 * bangs_w * sp

    if cp > 0.04:
        # 2. Smooth forehead & supraorbital brow ridge
        forehead_mask = (1.0 - _sstep(0.52, 0.82, ap))
        brow_arch = 0.385 - 0.014 * math.cos(phi * 4.2)
        brow = _gauss(tv, brow_arch, 0.068) * forehead_mask
        forehead_fill = _sstep(0.12, 0.34, tv) * (1.0 - _sstep(0.38, 0.48, tv)) * forehead_mask
        dx_face += 1.45 * brow + 0.85 * forehead_fill

        # 3. Deep-set orbital sockets + convex staring eyeballs
        for sgn in (-1.0, 1.0):
            ep = 0.509 * sgn
            d_orb = ((phi - ep) / 0.20) ** 2 + ((tv - 0.462) / 0.056) ** 2
            socket = math.exp(-0.5 * d_orb)
            d_ball = ((phi - ep) / 0.115) ** 2 + ((tv - 0.462) / 0.035) ** 2
            eyeball = math.exp(-0.5 * d_ball)
            dx_face += -1.30 * socket + 1.65 * eyeball

        # 4. Broad anatomical dorsal nasal bridge, rounded fleshy pronasale (`tv=0.618`), and alar wings
        bridge_t = _sstep(0.42, 0.615, tv) * (1.0 - _sstep(0.620, 0.685, tv))
        nose_ridge = _gauss(phi, 0.0, 0.115) * bridge_t
        nose_tip = _gauss(phi, 0.0, 0.135) * _gauss(tv, 0.618, 0.045)
        nostril_w = (_gauss(phi, -0.155, 0.068) + _gauss(phi, 0.155, 0.068)) * _gauss(tv, 0.632, 0.030)
        dx_face += 2.35 * nose_ridge + 1.95 * nose_tip + 1.05 * nostril_w
        dz_face -= 0.30 * nose_tip

        # 5. Zygomatic cheekbones + forward prognathic maxillary muzzle arch
        zyg = _gauss(ap, 0.56, 0.19) * _gauss(tv, 0.555, 0.070)
        maxilla = _gauss(phi, 0.0, 0.38) * _sstep(0.62, 0.74, tv) * (1.0 - _sstep(0.90, 0.99, tv))
        dx_face += 0.75 * zyg + 1.45 * maxilla
        dy_face += 0.55 * zyg * (1.0 if sp >= 0 else -1.0)

        # 6. Snarling bared-teeth lips & dental arch
        mouth_w = _gauss(phi, 0.0, 0.27)
        upper_lip = mouth_w * _gauss(tv, 0.736, 0.028)
        lower_lip = mouth_w * _gauss(tv, 0.848, 0.030)
        teeth_cav = _gauss(phi, 0.0, 0.21) * _gauss(tv, 0.794, 0.030)
        dx_face += 1.65 * upper_lip + 1.55 * lower_lip + 0.55 * teeth_cav

        # 7. Strong rounded chin prominence
        chin_prom = _gauss(phi, 0.0, 0.30) * _gauss(tv, 0.922, 0.045)
        sub_crease = _gauss(phi, 0.0, 0.24) * _gauss(tv, 0.878, 0.020)
        dx_face += 2.35 * chin_prom - 0.55 * sub_crease

    return (cx + x_base + dx_face, cy + y_base + dy_face, cz + z_loc + dz_face)


def build_eric_head_mesh(sb_head):
    """Builds high-detail sculpted 3D head + dark-shadowed collar plug deep inside the black muzzle bore."""
    nu, nv = 42, 26
    verts_w = []
    st = []

    for j in range(nv + 1):
        tv = j / nv
        for i in range(nu + 1):
            tu = i / nu
            phi = (tu - 0.5) * 2.0 * math.pi
            p_w = eval_eric_head_world(phi, tv)
            verts_w.append(p_w)
            st.append((min(0.998, max(0.002, tu)), min(0.996, max(0.004, tv))))

    stride = nu + 1
    norms_w = [(1.0, 0.0, 0.0)] * len(verts_w)
    for j in range(nv + 1):
        j0, j1 = max(0, j - 1), min(nv, j + 1)
        for i in range(nu + 1):
            iw = i % nu
            i_prev = (iw - 1) % nu
            i_next = (iw + 1) % nu
            p_l = verts_w[j * stride + i_prev]
            p_r = verts_w[j * stride + i_next]
            p_u = verts_w[j0 * stride + iw]
            p_d = verts_w[j1 * stride + iw]
            du = (p_r[0] - p_l[0], p_r[1] - p_l[1], p_r[2] - p_l[2])
            dv = (p_d[0] - p_u[0], p_d[1] - p_u[1], p_d[2] - p_u[2])
            nx = dv[1] * du[2] - dv[2] * du[1]
            ny = dv[2] * du[0] - dv[0] * du[2]
            nz = dv[0] * du[1] - dv[1] * du[0]
            if j == 0:
                nx, ny, nz = 0.0, 0.0, 1.0
            elif j == nv:
                nx, ny, nz = 0.25, 0.0, -0.96
            norms_w[j * stride + i] = vnorm((nx, ny, nz))

    tris = []
    for j in range(nv):
        for i in range(nu):
            a = j * stride + i
            b = a + 1
            c = a + stride + 1
            d = a + stride
            tris.append((a, d, c))
            tris.append((a, c, b))

    verts_loc = [world_rest_to_cannon_local(p) for p in verts_w]
    norms_loc = [world_dir_to_cannon_local(nm) for nm in norms_w]
    sb_head.add_part(verts_loc, norms_loc, st, tris, tag="head")

    # Dark hair/nape inner-bore neck plug strictly INSIDE the muzzle (`s = +30..+47u`), mapped to dark hair UV!
    neck_prof = [(30.0, 8.8), (39.0, 9.4), (46.8, 9.8)]
    vn, nn, stn, tn = build_lathe_x(neck_prof, 18, (0.02, 0.02, 0.22, 0.14), offset=(0.0, 0.0, 1.2))
    sb_head.add_part(vn, nn, stn, tn, tag="head")


def build_giant_ears_mesh(sb_ears):
    """Builds Left (+Y) and Right (-Y) C-shaped anatomical 3D human auricles matching `f240`, `f001`, `f185`:
      - Free semicircular superior helix dome (`y_apex = 21.2u` at `z_w = 91.8u` — NO flat top shelf!),
      - Skull root attachment (`|y| = 10.2u`) strictly along `tv in [0.22..0.78]`,
      - Free pendulous semicircular earlobe (`y_apex = 15.0u` at `z_w = 60.2u`),
      - Direct bounding-box `(y_norm, tv)` UV projection onto `eric_cannon_ears.png`!
    """
    nu, nv = 10, 16

    for side_sgn, tag_name in ((-1.0, "ear_r"), (1.0, "ear_l")):
        front_pts, back_pts = [], []
        front_st, back_st = [], []

        for j in range(nv + 1):
            tv = 0.5 * (1.0 - math.cos((j / nv) * math.pi))
            z_w = 93.0 - 33.0 * tv

            if tv < 0.22:
                ut = (0.22 - tv) / 0.22
                y_in = 10.1 + (18.4 - 10.1) * (1.0 - math.sqrt(max(0.0, 1.0 - ut * ut)))
            elif tv > 0.78:
                ub = (tv - 0.78) / 0.22
                y_in = 10.1 + (14.6 - 10.1) * (1.0 - math.sqrt(max(0.0, 1.0 - ub * ub)))
            else:
                y_in = 10.1

            if tv <= 0.28:
                ut = (0.28 - tv) / 0.28
                y_out = 18.4 + (28.0 - 18.4) * math.sqrt(max(0.0, 1.0 - ut * ut))
            elif tv < 0.76:
                sm = (tv - 0.28) / 0.48
                y_out = 28.0 - 6.2 * _sstep(0.0, 1.0, sm)
            else:
                ub = (tv - 0.76) / 0.24
                y_out = 14.6 + (21.8 - 14.6) * math.sqrt(max(0.0, 1.0 - ub * ub))

            for i in range(nu + 1):
                ts = i / nu
                y_abs = y_in + ts * (y_out - y_in)
                y_norm = max(0.0, min(1.0, (y_abs - 10.1) / (28.0 - 10.1)))

                x_mid = 53.2 + 7.2 * (y_norm ** 1.18) - 1.8 * ((tv - 0.46) ** 2) * 3.4
                concha = -3.3 * _gauss(y_norm, 0.38, 0.16) * _gauss(tv, 0.50, 0.16)
                antihelix = 1.40 * _gauss(y_norm, 0.64, 0.11) * (1.0 - _sstep(0.72, 0.92, tv))
                helix_curl = 2.05 * _sstep(0.76, 1.00, ts) * (1.0 - 0.40 * _sstep(0.78, 1.00, tv))
                top_curl = 1.45 * (1.0 - _sstep(0.0, 0.18, tv)) * _sstep(0.15, 0.85, y_norm)

                thick = 1.55 + 1.25 * _sstep(0.78, 1.00, ts) + 1.50 * _sstep(0.76, 1.00, tv) * (1.0 - 0.4 * y_norm)
                edge_pinch = math.sin(min(1.0, (1.0 - ts) / 0.14) * (math.pi * 0.5)) if ts > 0.86 else 1.0
                if tv < 0.22 and ts < 0.14:
                    edge_pinch *= math.sin((ts / 0.14) * (math.pi * 0.5))
                elif tv > 0.78 and ts < 0.14:
                    edge_pinch *= math.sin((ts / 0.14) * (math.pi * 0.5))

                half_t = 0.5 * thick * edge_pinch
                x_front = x_mid + concha + antihelix + helix_curl + top_curl + half_t
                x_back  = x_mid + 0.55 * concha - half_t

                front_pts.append((x_front, side_sgn * y_abs, z_w))
                back_pts.append((x_back, side_sgn * y_abs, z_w))

                front_st.append((0.068 + 0.404 * y_norm, 0.052 + 0.896 * tv))
                back_st.append((0.558 + 0.390 * y_norm, 0.052 + 0.896 * tv))

        stride = nu + 1

        def grid_normals(pts, sign_x):
            out = []
            for j in range(nv + 1):
                j0, j1 = max(0, j - 1), min(nv, j + 1)
                for i in range(nu + 1):
                    i0, i1 = max(0, i - 1), min(nu, i + 1)
                    pa, pb = pts[j * stride + i0], pts[j * stride + i1]
                    pu, pd = pts[j0 * stride + i], pts[j1 * stride + i]
                    du = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2])
                    dv = (pd[0] - pu[0], pd[1] - pu[1], pd[2] - pu[2])
                    c = (
                        du[1] * dv[2] - du[2] * dv[1],
                        du[2] * dv[0] - du[0] * dv[2],
                        du[0] * dv[1] - du[1] * dv[0],
                    )
                    if c[0] * sign_x < 0:
                        c = (-c[0], -c[1], -c[2])
                    out.append(vnorm(c))
            return out

        fn_w = grid_normals(front_pts, +1.0)
        bn_w = grid_normals(back_pts, -1.0)

        tris_f, tris_b = [], []
        for j in range(nv):
            for i in range(nu):
                a = j * stride + i
                b = a + 1
                c = a + stride + 1
                d = a + stride
                tris_f.append((a, b, c))
                tris_f.append((a, c, d))
                tris_b.append((a, c, b))
                tris_b.append((a, d, c))

        sb_ears.add_part(
            [world_rest_to_cannon_local(p) for p in front_pts],
            [world_dir_to_cannon_local(nm) for nm in fn_w],
            front_st,
            tris_f,
            tag=tag_name,
        )
        sb_ears.add_part(
            [world_rest_to_cannon_local(p) for p in back_pts],
            [world_dir_to_cannon_local(nm) for nm in bn_w],
            back_st,
            tris_b,
            tag=tag_name,
        )


def build_head_harness_and_buckles(sb_metal):
    """Builds the olive tactical webbing straps & matte-black quick-release side buckles
    hugging Eric's lean `10.35u` head & anchoring directly into the wide black muzzle bore (`f240`, `f001`, `f087`)."""
    # 1. Front Crown-to-Cheeks-to-Chin continuous webbing hoop (IN FRONT of giant ears!)
    hoop_pts_w = []
    n_hoop = 28
    for i in range(n_hoop + 1):
        th = (i / n_hoop) * 2.0 * math.pi
        ct, st_a = math.cos(th), math.sin(th)
        z_w = 77.8 + 17.3 * ct
        y_w = 10.65 * st_a * (1.0 - 0.16 * max(0.0, -ct))
        x_w = 64.2 - 2.4 * ct + 1.5 * (st_a ** 2)
        hoop_pts_w.append((x_w, y_w, z_w))

    vw, nw, stw, tw = build_ribbon_tube(hoop_pts_w, width=2.8, thickness=0.85, uv_rect=etex.UV_WEBBING_STRAP)
    sb_metal.add_part(
        [world_rest_to_cannon_local(p) for p in vw],
        [world_dir_to_cannon_local(nm) for nm in nw],
        stw,
        tw,
        tag="head",
    )

    # 2. Rear Occiput Crown Strap looping BEHIND the giant ears right at the muzzle lip (`x_w ~ 50.5u`)
    rear_pts_w = []
    for i in range(17):
        th = -0.82 * math.pi + (i / 16.0) * 1.64 * math.pi
        ct, st_a = math.cos(th), math.sin(th)
        z_w = 77.4 + 16.5 * ct
        y_w = 10.4 * st_a
        x_w = 50.8 + 2.0 * ct
        rear_pts_w.append((x_w, y_w, z_w))
    vw, nw, stw, tw = build_ribbon_tube(rear_pts_w, width=2.6, thickness=0.75, uv_rect=etex.UV_WEBBING_STRAP)
    sb_metal.add_part(
        [world_rest_to_cannon_local(p) for p in vw],
        [world_dir_to_cannon_local(nm) for nm in nw],
        stw,
        tw,
        tag="head",
    )

    # 3. 2 Matte-Black Quick-Release Cheek Buckles (`y_w = +-10.95u, z_w = 70.5..79.5u, x_w = 65.5u`)
    for sgn in (-1.0, 1.0):
        def xf_bkl(p, nm, s=sgn):
            p1 = rot_x_pt(p, -9.0 * s)
            n1 = rot_x_pt(nm, -9.0 * s)
            pw = (65.4 + p1[0], s * 10.95 + p1[1], 74.8 + p1[2])
            return world_rest_to_cannon_local(pw), world_dir_to_cannon_local(n1)

        vb, nb, stb, tb = build_box(-1.9, 1.9, -0.75, 0.75, -4.3, 4.3, etex.UV_BUCKLE_POLY, xform=xf_bkl)
        sb_metal.add_part(vb, nb, stb, tb, tag="head")
        vb, nb, stb, tb = build_box(-1.4, 1.4, -1.05, 1.05, -1.4, 1.4, etex.UV_BLACK_COLLAR, xform=xf_bkl)
        sb_metal.add_part(vb, nb, stb, tb, tag="head")

        # 4. Short taut olive tether straps anchoring cheek harness directly into the black muzzle bore!
        for z_off, z_bore in ((8.2, 82.5), (-7.2, 67.5)):
            tether_w = [
                (64.6, sgn * 10.3, 74.8 + z_off),
                (55.0, sgn * 11.2, 75.0 + z_off * 0.85),
                (43.0, sgn * 11.8, z_bore),
            ]
            vt, nt, stt, tt = build_ribbon_tube(tether_w, width=2.2, thickness=0.65, uv_rect=etex.UV_WEBBING_STRAP)
            sb_metal.add_part(
                [world_rest_to_cannon_local(p) for p in vt],
                [world_dir_to_cannon_local(nm) for nm in nt],
                stt,
                tt,
                tag="head",
            )

    # Under-chin black buckle keeper pad
    def xf_chin(p, nm):
        pw = (66.2 + p[0], p[1], 60.1 + p[2])
        return world_rest_to_cannon_local(pw), world_dir_to_cannon_local(nm)

    vc, nc, stc, tc = build_box(-2.3, 2.3, -2.8, 2.8, -0.75, 0.75, etex.UV_BUCKLE_POLY, xform=xf_chin)
    sb_metal.add_part(vc, nc, stc, tc, tag="head")


# ==============================================================================
# 4. OLIVE-DRAB LAUNCHER BARREL, HARDWARE, DECALS & WEW-CANNON FX SURFACES
# ==============================================================================
def barrel_outer_radius(s):
    """Exact outer radius along cannon axis `s in [-76.5 .. +49.0]` matching `f185` & `f240`."""
    if s < -71.0:
        return 14.3
    if s < 3.5:
        return 12.60
    if s < 20.0:
        t = (s - 3.5) / 16.5
        return 12.60 + (17.10 - 12.60) * t
    if s < 43.2:
        t = (s - 20.0) / 23.2
        return 17.10 + (18.60 - 17.10) * t
    return 19.65


def build_cannon_rest_surfaces():
    sb_metal = SurfBuilder("eric_metal", "progs/eric_cannon_metal", "metal")
    sb_head  = SurfBuilder("eric_head",  "progs/eric_cannon_head",  "head")
    sb_ears  = SurfBuilder("eric_ears",  "progs/eric_cannon_ears",  "ears")
    sb_fx    = SurfBuilder("eric_fx",    "progs/eric_cannon_fx",    "fx")

    n_rad = 28

    # --- A1. Rear Venturi Flange + Recessed Bolted Ring + Hollow Exhaust Throat (`s = -76.9 .. -71.0`) ---
    rear_bell = [
        (-54.0, 7.6),
        (-74.8, 8.6),
        (-76.8, 9.2),
        (-76.9, 13.4),
        (-76.5, 14.05),
        (-71.4, 14.05),
        (-71.0, 12.35),
    ]
    v, n, st, t = build_lathe_x(rear_bell, n_rad, etex.UV_BLACK_COLLAR)
    sb_metal.add_part(v, n, st, t, tag="barrel")

    # Bolted rear inner ring (`f137` shows crisp circular 8-bolt metallic ring around dark exhaust bore!)
    ring_v, ring_n, ring_st, ring_t = [], [], [], []
    u0, v0, u1, v1 = etex.UV_REAR_BORE
    uc, vc, ur, vr = 0.5 * (u0 + u1), 0.5 * (v0 + v1), 0.48 * (u1 - u0), 0.48 * (v1 - v0)
    for r_in_out, s_x in ((8.4, -76.2), (12.8, -76.75)):
        for i in range(n_rad + 1):
            phi = (i / n_rad) * 2.0 * math.pi
            sp, cp = math.sin(phi), math.cos(phi)
            ring_v.append((s_x, r_in_out * sp, r_in_out * cp))
            ring_n.append((-1.0, 0.0, 0.0))
            rr = r_in_out / 13.2
            ring_st.append((uc + ur * rr * sp, vc + vr * rr * cp))
    stride = n_rad + 1
    for i in range(n_rad):
        a, b, c, d = i, i + 1, stride + i + 1, stride + i
        ring_t.append((a, c, b))
        ring_t.append((a, d, c))
    sb_metal.add_part(ring_v, ring_n, ring_st, ring_t, tag="barrel")

    # --- A2. Main Weathered Olive-Drab Tube + Conical Flare (`s = -71.0 .. +20.0`) ---
    olive_prof = [
        (-71.0, 12.60),
        (-61.0, 12.60),
        (-52.0, 12.60),
        (-40.0, 12.60),
        (-28.0, 12.60),
        (-16.0, 12.60),
        (-5.0,  12.60),
        (3.5,   12.60),
        (9.5,   14.20),
        (15.0,  15.70),
        (20.0,  17.10),
    ]
    v, n, st, t = build_lathe_x(olive_prof, n_rad, etex.UV_OLIVE_TUBE)
    sb_metal.add_part(v, n, st, t, tag="barrel")

    # --- A3. Wide Matte-Black Muzzle Bell + Rolled Front Lip + Deep Dark Hollow Bore (`s = +20.0 .. +49.0`) ---
    black_prof = [
        (20.0, 17.10),
        (28.0, 17.65),
        (36.0, 18.15),
        (43.2, 18.60),
        (43.9, 19.65),
        (48.8, 19.65),
        (49.0, 17.75),
        (48.4, 17.05),
        (34.0, 15.20),
        (21.5, 11.90),
    ]
    v, n, st, t = build_lathe_x(black_prof, n_rad, etex.UV_BLACK_COLLAR)
    sb_metal.add_part(v, n, st, t, tag="barrel")

    # --- A4. Raised Structural Clamping Rings, Top Sight Housing & Side Muzzle Bolts (`f185`, `f001`) ---
    for s_a, s_b, r_band in ((-60.6, -56.4, 12.88), (-26.8, -23.6, 12.95), (-4.6, 3.2, 13.35)):
        band_p = [(s_a - 0.3, 12.50), (s_a, r_band), (s_b, r_band), (s_b + 0.3, 12.50)]
        v, n, st, t = build_lathe_x(band_p, 24, etex.UV_BLACK_COLLAR)
        sb_metal.add_part(v, n, st, t, tag="barrel")

    # Top optical/sight block on main clamp collar (`s = -4.2..+2.8, z = 12.7..17.0`) + side cam latch
    v, n, st, t = build_box(-4.2, 2.8, -3.4, 3.4, 12.7, 17.0, etex.UV_CAST_OLIVE)
    sb_metal.add_part(v, n, st, t, tag="barrel")
    v, n, st, t = build_box(-9.2, -5.2, 3.8, 6.4, 11.4, 14.6, etex.UV_BLACK_COLLAR)
    sb_metal.add_part(v, n, st, t, tag="barrel")

    # Side hex bolts on black muzzle collar (`s = +28.5, y = +-17.2`)
    for sgn in (-1.0, 1.0):
        v, n, st, t = build_box(27.4, 29.8, sgn * 16.6, sgn * 18.2, -1.2, 1.2, etex.UV_BUCKLE_POLY)
        sb_metal.add_part(v, n, st, t, tag="barrel")

    # Bottom cradle guide rail under tube (`s = -24..+6, z = -14.2..-11.8`)
    v, n, st, t = build_box(-24.0, 6.0, -5.8, 5.8, -14.2, -11.6, etex.UV_CAST_OLIVE)
    sb_metal.add_part(v, n, st, t, tag="barrel")

    # --- A5. Curved Yellow `DALUCTION` Plaque & Triangle Hazard Decals on BOTH Flanks! ---
    # Right flank (-Y, phi around -90 deg): muzzle is on viewer's right (`f185`), so text reads s=-52 -> -35!
    v, n, st, t = build_curved_barrel_decal(
        -52.5, -35.2, barrel_outer_radius, -68.0, -112.0, 6, 4, etex.UV_DECAL_DALUCTION, flip_u=False, lift=0.20
    )
    sb_metal.add_part(v, n, st, t, tag="barrel")
    # Left flank (+Y, phi around +90 deg): muzzle is on viewer's left (`f087`), flip_u=True so text reads left-to-right!
    v, n, st, t = build_curved_barrel_decal(
        -52.5, -35.2, barrel_outer_radius, 68.0, 112.0, 6, 4, etex.UV_DECAL_DALUCTION, flip_u=True, lift=0.20
    )
    sb_metal.add_part(v, n, st, t, tag="barrel")

    # Yellow Hazard Triangle Decal on conical olive flare (`s = +11.8 .. +19.2`)
    v, n, st, t = build_curved_barrel_decal(
        11.8, 19.2, barrel_outer_radius, -76.0, -106.0, 4, 3, etex.UV_DECAL_HAZARD, flip_u=False, lift=0.22
    )
    sb_metal.add_part(v, n, st, t, tag="barrel")
    v, n, st, t = build_curved_barrel_decal(
        11.8, 19.2, barrel_outer_radius, 76.0, 106.0, 4, 3, etex.UV_DECAL_HAZARD, flip_u=True, lift=0.22
    )
    sb_metal.add_part(v, n, st, t, tag="barrel")

    # --- B. Sculpted Eric Deason Head, Webbing Harness/Buckles, and Giant Human Ears ---
    build_eric_head_mesh(sb_head)
    build_head_harness_and_buckles(sb_metal)
    build_giant_ears_mesh(sb_ears)

    # --- C. Additive Wew-Cannon Muzzle Starburst, Mach Shockwave Rings & Rear Venturi Rocket Plume (`sb_fx`) ---
    # Built in unit normalized coordinates around `(0,0,0)`; dynamically positioned & scaled per frame!
    # 1. Crossed 3D Muzzle Starburst Quads (`fx_star`, 3 planes x 4v = 12v)
    u0, v0, u1, v1 = etex.UV_FX_STARBURST
    for rot_d in (0.0, 55.0, -55.0):
        pts = [rot_x_pt((0.0, y, z), rot_d) for y, z in ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))]
        # Tilt starburst planes into a 3D crown
        pts_3d = [
            (-0.25, pts[0][1], pts[0][2]),
            (0.25,  pts[1][1], pts[1][2]),
            (-0.25, pts[2][1], pts[2][2]),
            (0.25,  pts[3][1], pts[3][2]),
        ]
        nrms = [(1.0, 0.0, 0.0)] * 4
        sts = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        sb_fx.add_part(pts_3d, nrms, sts, [(0, 1, 2), (0, 2, 3)], tag="fx_star")

    # 2. Primary & Secondary Supersonic Mach Shockwave Rings (`fx_ring1`, `fx_ring2`)
    ru0, rv0, ru1, rv1 = etex.UV_FX_SHOCKRING
    for tag_r in ("fx_ring1", "fx_ring2"):
        rv = [(-0.08, -1.0, -1.0), (0.08, 1.0, -1.0), (-0.08, 1.0, 1.0), (0.08, -1.0, 1.0)]
        rn = [(1.0, 0.0, 0.0)] * 4
        rst = [(ru0, rv1), (ru1, rv1), (ru1, rv0), (ru0, rv0)]
        sb_fx.add_part(rv, rn, rst, [(0, 1, 2), (0, 2, 3)], tag=tag_r)

    # 3. Rear Venturi Rocket Exhaust Jet Cone + Crossed Flame Blades (`fx_jet`, ~90v)
    ju0, jv0, ju1, jv1 = etex.UV_FX_JETFLAME
    jet_prof = [(0.0, 0.58), (-0.28, 0.88), (-0.65, 0.62), (-1.0, 0.12)]
    vj, nj, stj, tj = build_lathe_x(jet_prof, 14, (ju0, jv0, ju1, jv1))
    sb_fx.add_part(vj, nj, stj, tj, tag="fx_jet")
    for ang_d in (0.0, 90.0):
        pts = [rot_x_pt((x, y, 0.0), ang_d) for x, y in ((0.0, -0.82), (0.0, 0.82), (-1.0, 0.45), (-1.0, -0.45))]
        nrms = [rot_x_pt((0.0, 0.0, 1.0), ang_d)] * 4
        sts = [(ju0, jv0), (ju1, jv0), (ju1, jv1), (ju0, jv1)]
        sb_fx.add_part(pts, nrms, sts, [(0, 1, 2), (0, 2, 3)], tag="fx_jet")

    return [sb_metal, sb_head, sb_ears, sb_fx]


# ==============================================================================
# 5. 77-FRAME SCHEDULE & CURVILINEAR WEW-CANNON + EAR-FLAP DEFORMER
# ==============================================================================
def build_77_frame_schedule():
    frames = []

    def push(name, bend_up=0.0, bend_yaw=0.0, squash=0.0, bulge_amp=0.0, bulge_t=0.35, bulge_w=0.18,
             bell_flare=0.0, head_surge=0.0, head_pitch=0.0,
             ear_l_yaw=0.0, ear_l_roll=0.0, ear_l_pitch=0.0,
             ear_r_yaw=0.0, ear_r_roll=0.0, ear_r_pitch=0.0,
             star_s=0.0, ring1_s=0.0, ring1_x=0.0, ring2_s=0.0, ring2_x=0.0, jet_len=0.0, jet_r=0.0):
        frames.append(dict(
            name=name, bend_up=bend_up, bend_yaw=bend_yaw, squash=squash,
            bulge_amp=bulge_amp, bulge_t=bulge_t, bulge_w=bulge_w,
            bell_flare=bell_flare, head_surge=head_surge, head_pitch=head_pitch,
            ear_l_yaw=ear_l_yaw, ear_l_roll=ear_l_roll, ear_l_pitch=ear_l_pitch,
            ear_r_yaw=ear_r_yaw, ear_r_roll=ear_r_roll, ear_r_pitch=ear_r_pitch,
            star_s=star_s, ring1_s=ring1_s, ring1_x=ring1_x,
            ring2_s=ring2_s, ring2_x=ring2_x, jet_len=jet_len, jet_r=jet_r,
        ))

    # Frame 0: Exact Static Reference Turntable Pose (`ref_static`)
    push("ref0")

    # Frames 1..16 (`idle1..16`): Lifelike asymmetric radar-ear twitching & perk-up
    for i in range(16):
        ph = (i / 16.0) * 2.0 * math.pi
        # Left ear perks & cups forward around i=3..6, double-flick at i=11
        l_yaw = 14.0 * math.sin(ph) + 7.5 * math.sin(2.0 * ph + 0.6)
        l_rol = 9.0 * math.sin(ph - 0.4) + 5.0 * max(0.0, math.sin(3.0 * ph))
        # Right ear swivels on offset radar rhythm
        r_yaw = -13.0 * math.sin(ph - 1.3) + 8.0 * math.cos(2.0 * ph)
        r_rol = -8.5 * math.cos(ph - 0.8) - 5.5 * max(0.0, math.sin(3.0 * ph + 1.5))
        push(f"idle{i+1}", ear_l_yaw=l_yaw, ear_l_roll=l_rol, ear_r_yaw=r_yaw, ear_r_roll=r_rol,
             head_pitch=1.2 * math.sin(ph))

    # Frames 17..25 (`windup1..9`): HILARIOUS WEW-CANNON CHARGE BEND & PERISTALTIC BELLY BULGE!
    # Barrel bends +39 deg skyward, squashes -18% axially, swells +54% belly bulge, ears sweep back cleanly outside bell!
    wind_profiles = [
        ( 6.5,  2.0, -0.03, 0.08, 0.16, -0.02, -0.8, -8.0,   3.0),
        (14.5,  5.0, -0.07, 0.18, 0.20, -0.04, -1.8, -16.0,  6.0),
        (23.5,  8.5, -0.11, 0.30, 0.25, -0.06, -3.0, -24.0,  9.0),
        (31.5, 11.0, -0.15, 0.42, 0.30, -0.08, -4.0, -30.0, 12.0),
        (36.5, 12.5, -0.17, 0.50, 0.36, -0.09, -4.6, -34.0, 14.0),
        (39.0, 13.0, -0.18, 0.55, 0.42, -0.09, -5.0, -36.0, 15.0),
        (37.5, 11.0, -0.17, 0.56, 0.50, -0.06, -4.2, -36.0, 14.0),
        (30.0,  7.0, -0.13, 0.55, 0.62,  0.04, -2.0, -30.0, 10.0),
        (16.0,  2.0, -0.06, 0.50, 0.76,  0.18,  1.5, -18.0,  5.0),
    ]
    for k, (bu, by, sq, ba, bt, bf, hs, ey, er) in enumerate(wind_profiles):
        # Tremble jitter at peak charge
        trem = (2.5 if k % 2 == 0 else -2.5) if k >= 4 else 0.0
        st_s = 14.0 if k == 8 else 0.0
        jl = 18.0 if k == 8 else 0.0
        push(f"windup{k+1}", bend_up=bu, bend_yaw=by + trem * 0.4, squash=sq,
             bulge_amp=ba, bulge_t=bt, bulge_w=0.17, bell_flare=bf,
             head_surge=hs, head_pitch=bu * 0.25,
             ear_l_yaw=ey + trem, ear_l_roll=er, ear_r_yaw=-ey - trem, ear_r_roll=-er,
             star_s=st_s, jet_len=jl, jet_r=12.0 if k == 8 else 0.0)

    # Frames 26..29 (`blast1..4`): WHIP-SNAP EXPLOSION! Bulge blasts out muzzle, bell flares +42%,
    # Eric's head & giant ears snap wide forward inside colossal starburst & supersonic Mach shockrings!
    blast_profiles = [
        (-15.0, -4.0, 0.08, 0.44, 0.90, 0.42, 11.5, 34.0, 16.0, 44.0, 26.0,  6.0, 16.0,  2.0, 48.0, 18.5),
        (-20.0, -5.5, 0.11, 0.28, 0.98, 0.36, 13.5, 38.0, 20.0, 56.0, 42.0, 18.0, 28.0,  9.0, 64.0, 21.0),
        ( -8.0, -2.0, 0.05, 0.14, 1.04, 0.20,  8.5, 26.0, 12.0, 38.0, 56.0, 32.0, 42.0, 18.0, 58.0, 19.0),
        (  6.0,  1.5, 0.01, 0.05, 1.08, 0.08,  4.0, 10.0,  5.0, 20.0, 68.0, 46.0, 54.0, 28.0, 50.0, 16.5),
    ]
    for k, (bu, by, sq, ba, bt, bf, hs, ey, er, ss, r1s, r1x, r2s, r2x, jl, jr) in enumerate(blast_profiles):
        push(f"blast{k+1}", bend_up=bu, bend_yaw=by, squash=sq,
             bulge_amp=ba, bulge_t=bt, bulge_w=0.14, bell_flare=bf,
             head_surge=hs, head_pitch=-8.0,
             ear_l_yaw=ey, ear_l_roll=er, ear_r_yaw=-ey, ear_r_roll=-er,
             star_s=ss, ring1_s=r1s, ring1_x=r1x, ring2_s=r2s, ring2_x=r2x, jet_len=jl, jet_r=jr)

    # Frames 30..32 (`liftoff1..3`): Springy S-bend whiplash settle into forward flight alignment!
    lift_profiles = [
        (12.0, 0.0, -0.02, 2.5, -14.0, -6.0, 8.0, 46.0, 15.5, 4.0),
        (-5.0, 0.0,  0.01, 1.5, -20.0, -4.0, 0.0, 44.0, 15.0, 7.5),
        ( 2.0, 0.0,  0.00, 1.0, -22.0, -2.0, 0.0, 42.0, 14.5, 9.5),
    ]
    for k, (bu, by, sq, hs, ey, er, ss, jl, jr, hp) in enumerate(lift_profiles):
        push(f"liftoff{k+1}", bend_up=bu, bend_yaw=by, squash=sq,
             head_surge=hs, head_pitch=hp,
             ear_l_yaw=ey, ear_l_roll=er, ear_r_yaw=-ey, ear_r_roll=-er,
             star_s=ss, jet_len=jl, jet_r=jr)

    # Frames 33..44 (`boost1..12`): High-thrust skyward climb — pulsing shock-diamond jet & aero ear flutter
    for i in range(12):
        ph = (i / 12.0) * 2.0 * math.pi
        flut = 6.5 * math.sin(2.0 * ph)
        jl = 44.0 + 9.0 * math.sin(3.0 * ph)
        jr = 14.8 + 2.2 * math.cos(3.0 * ph)
        push(f"boost{i+1}", head_surge=1.5, head_pitch=10.0,
             ear_l_yaw=-24.0 + flut, ear_l_roll=-6.0 + 5.0 * math.cos(2.0 * ph),
             ear_r_yaw=24.0 - flut, ear_r_roll=6.0 - 5.0 * math.cos(2.0 * ph),
             jet_len=jl, jet_r=jr)

    # Frames 45..60 (`glide1..16`): Majestic comical sky-glide — giant ears flap up & down like fleshy wings!
    for i in range(16):
        ph = (i / 16.0) * 2.0 * math.pi
        flap_roll = 36.0 * math.sin(ph)
        flap_yaw  = 16.0 * math.cos(ph) - 4.0
        flap_pit  = -14.0 * math.cos(ph)
        bob_bend  = 3.2 * math.sin(ph)
        push(f"glide{i+1}", bend_up=bob_bend, head_surge=1.2, head_pitch=10.5 - 2.0 * math.sin(ph),
             ear_l_yaw=flap_yaw, ear_l_roll=flap_roll, ear_l_pitch=flap_pit,
             ear_r_yaw=-flap_yaw, ear_r_roll=-flap_roll, ear_r_pitch=flap_pit,
             jet_len=20.0 + 3.5 * math.sin(2.0 * ph), jet_r=9.8)

    # Frames 61..68 (`dive1..8`): Steep bomb dive (`W` held) — ears swept sleekly back (-34 deg) with rapid buzz!
    for i in range(8):
        ph = (i / 8.0) * 2.0 * math.pi
        buzz = 4.5 * math.sin(2.0 * ph)
        push(f"dive{i+1}", head_surge=2.2, head_pitch=12.0,
             ear_l_yaw=-34.0 + buzz, ear_l_roll=10.0 + 3.0 * math.cos(2.0 * ph),
             ear_r_yaw=34.0 - buzz, ear_r_roll=-10.0 - 3.0 * math.cos(2.0 * ph),
             jet_len=15.0 + 3.0 * math.sin(2.0 * ph), jet_r=8.5)

    # Frames 69..76 (`flare1..8`): Parachute airbrake (`S` held) — giant ears cupped wide forward (+38 deg)!
    for i in range(8):
        ph = (i / 8.0) * 2.0 * math.pi
        cup = 37.0 + 4.0 * math.sin(ph)
        rol = 14.0 + 4.0 * math.cos(ph)
        push(f"flare{i+1}", bend_up=4.0 + 1.5 * math.sin(ph), head_surge=0.5, head_pitch=8.0,
             ear_l_yaw=cup, ear_l_roll=rol, ear_l_pitch=8.0,
             ear_r_yaw=-cup, ear_r_roll=-rol, ear_r_pitch=8.0,
             jet_len=12.0 + 2.0 * math.sin(ph), jet_r=7.5)

    assert len(frames) == 77, f"Expected 77 frames, got {len(frames)}"
    return frames


def build_spine_table(fr, n_steps=160):
    """Integrates a smooth curvilinear Frenet spine from `s = S_REAR` (`t=0`) to `s = S_MUZZLE` (`t=1`)
    so the olive launcher barrel bends like rubber, squashes axially, and swells a peristaltic cartoon bulge!"""
    L0 = S_MUZZLE - S_REAR
    L_cur = L0 * (1.0 + fr["squash"])
    ds = L_cur / n_steps

    ts = np.linspace(0.0, 1.0, n_steps + 1)
    pos = np.zeros((n_steps + 1, 3), dtype=np.float64)
    tang = np.zeros((n_steps + 1, 3), dtype=np.float64)
    up_v = np.zeros((n_steps + 1, 3), dtype=np.float64)
    left_v = np.zeros((n_steps + 1, 3), dtype=np.float64)
    rad_scale = np.ones(n_steps + 1, dtype=np.float64)

    # Anchor `s = 0` (`t_anchor = (0 - S_REAR)/L0`) at `(0,0,0)` so saddle stays centered!
    p = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    for k, t in enumerate(ts):
        # Progressive quadratic bend increasing from rear saddle (`t > 0.25`) toward muzzle (`t = 1`)
        bend_prog = max(0.0, (t - 0.18) / 0.82) ** 1.35
        pitch_rad = math.radians(fr["bend_up"]) * bend_prog
        yaw_rad   = math.radians(fr["bend_yaw"]) * bend_prog

        cp, sp = math.cos(pitch_rad), math.sin(pitch_rad)
        cy, sy = math.cos(yaw_rad), math.sin(yaw_rad)
        T = np.array([cp * cy, cp * sy, sp], dtype=np.float64)
        L = np.array([-sy, cy, 0.0], dtype=np.float64)
        U = np.cross(T, L)
        # Note: T=(1,0,0), L=(0,1,0) -> T x L = (0,0,1) = +Z!

        tang[k] = T
        left_v[k] = L
        up_v[k] = U

        # Peristaltic belly bulge + blunderbuss muzzle bell flare
        bulge = fr["bulge_amp"] * math.exp(-0.5 * ((t - fr["bulge_t"]) / max(0.04, fr["bulge_w"])) ** 2)
        flare = fr["bell_flare"] * (_sstep(0.76, 1.00, t) ** 1.4)
        rad_scale[k] = 1.0 + bulge + flare

        if k < n_steps:
            p = p + T * ds
            pos[k + 1] = p

    # Shift entire spine so `t_zero = (0.0 - S_REAR) / L0` sits at `(0, 0, 0)`
    t_zero = (0.0 - S_REAR) / L0
    idx_z = min(n_steps, max(0, int(round(t_zero * n_steps))))
    pos -= pos[idx_z].copy()
    return dict(ts=ts, pos=pos, tang=tang, left=left_v, up=up_v, rad_scale=rad_scale)


def evaluate_surface_for_frame(sb: SurfBuilder, fr: dict, sp_tbl: dict):
    """Evaluates deformed vertex positions & normals for a single frame of `eric_cannon.md3`."""
    L0 = S_MUZZLE - S_REAR
    ts = sp_tbl["ts"]
    n_steps = len(ts) - 1

    def sample_spine(t_clamped):
        f = max(0.0, min(1.0, t_clamped)) * n_steps
        i0 = min(n_steps - 1, int(f))
        w = f - i0
        P = (1.0 - w) * sp_tbl["pos"][i0] + w * sp_tbl["pos"][i0 + 1]
        T = (1.0 - w) * sp_tbl["tang"][i0] + w * sp_tbl["tang"][i0 + 1]
        L = (1.0 - w) * sp_tbl["left"][i0] + w * sp_tbl["left"][i0 + 1]
        U = (1.0 - w) * sp_tbl["up"][i0] + w * sp_tbl["up"][i0 + 1]
        rs = (1.0 - w) * sp_tbl["rad_scale"][i0] + w * sp_tbl["rad_scale"][i0 + 1]
        T /= max(1e-9, np.linalg.norm(T))
        L /= max(1e-9, np.linalg.norm(L))
        U /= max(1e-9, np.linalg.norm(U))
        return P, T, L, U, rs

    P_muz, T_muz, L_muz, U_muz, rs_muz = sample_spine(1.0)
    P_rear, T_rear, L_rear, U_rear, _ = sample_spine(0.0)
    P_muz0 = np.array([S_MUZZLE, 0.0, 0.0], dtype=np.float64)

    # Ear pivots in cannon local rest coordinates (matching updated skull root)
    piv_l = np.array(world_rest_to_cannon_local((54.2,  10.4, 76.6)), dtype=np.float64)
    piv_r = np.array(world_rest_to_cannon_local((54.2, -10.4, 76.6)), dtype=np.float64)

    def xform_head_pt_nm(p_loc, n_loc, ear_tag=None):
        p = np.array(p_loc, dtype=np.float64)
        nm = np.array(n_loc, dtype=np.float64)

        # 1. Optional giant ear articulation around its anatomical skull root!
        if ear_tag in ("ear_l", "ear_r"):
            piv = piv_l if ear_tag == "ear_l" else piv_r
            dp = tuple(p - piv)
            dn = tuple(nm)
            if ear_tag == "ear_l":
                ey, er, ep = fr["ear_l_yaw"], fr["ear_l_roll"], fr["ear_l_pitch"]
            else:
                ey, er, ep = fr["ear_r_yaw"], fr["ear_r_roll"], fr["ear_r_pitch"]
            dp = rot_y_up_pt(rot_x_pt(rot_z_pt(dp, ey), er), ep)
            dn = rot_y_up_pt(rot_x_pt(rot_z_pt(dn, ey), er), ep)
            p = piv + np.array(dp, dtype=np.float64)
            nm = np.array(dn, dtype=np.float64)

        # 2. Head pitch alignment + axial surge relative to muzzle (`P_muz0`)
        rel = p - P_muz0
        if abs(fr["head_pitch"]) > 1e-4:
            rel = np.array(rot_y_up_pt(tuple(rel), fr["head_pitch"]), dtype=np.float64)
            nm  = np.array(rot_y_up_pt(tuple(nm),  fr["head_pitch"]), dtype=np.float64)
        rel[0] += fr["head_surge"]

        # 3. Ride seamlessly on the deformed muzzle Frenet frame `(P_muz, T_muz, L_muz, U_muz)`!
        out_p = P_muz + T_muz * rel[0] + L_muz * rel[1] + U_muz * rel[2]
        out_n = T_muz * nm[0] + L_muz * nm[1] + U_muz * nm[2]
        return tuple(out_p), vnorm(out_n)

    out_verts = []
    out_norms = []

    for p_loc, n_loc, tag in zip(sb.verts, sb.norms, sb.tags):
        if tag == "barrel":
            t = (p_loc[0] - S_REAR) / L0
            P, T, L, U, rs = sample_spine(t)
            dx_over = 0.0
            if p_loc[0] < S_REAR:
                dx_over = p_loc[0] - S_REAR
            elif p_loc[0] > S_MUZZLE:
                dx_over = p_loc[0] - S_MUZZLE
            vp = P + T * dx_over + L * (p_loc[1] * rs) + U * (p_loc[2] * rs)
            vn = T * n_loc[0] + L * n_loc[1] + U * n_loc[2]
            out_verts.append(tuple(vp))
            out_norms.append(vnorm(vn))

        elif tag in ("head", "ear_l", "ear_r"):
            vp, vn = xform_head_pt_nm(p_loc, n_loc, ear_tag=(tag if tag != "head" else None))
            out_verts.append(vp)
            out_norms.append(vn)

        elif tag == "fx_star":
            s = fr["star_s"]
            if s <= 0.05:
                out_verts.append((0.0, 0.0, 0.0))
                out_norms.append((1.0, 0.0, 0.0))
            else:
                vp = P_muz + T_muz * (4.0 + p_loc[0] * s * 0.45) + L_muz * (p_loc[1] * s) + U_muz * (p_loc[2] * s)
                vn = T_muz * n_loc[0] + L_muz * n_loc[1] + U_muz * n_loc[2]
                out_verts.append(tuple(vp))
                out_norms.append(vnorm(vn))

        elif tag in ("fx_ring1", "fx_ring2"):
            s = fr["ring1_s"] if tag == "fx_ring1" else fr["ring2_s"]
            x_off = fr["ring1_x"] if tag == "fx_ring1" else fr["ring2_x"]
            if s <= 0.05:
                out_verts.append((0.0, 0.0, 0.0))
                out_norms.append((1.0, 0.0, 0.0))
            else:
                vp = P_muz + T_muz * (x_off + p_loc[0] * 8.0) + L_muz * (p_loc[1] * s) + U_muz * (p_loc[2] * s)
                out_verts.append(tuple(vp))
                out_norms.append(vnorm(T_muz))

        elif tag == "fx_jet":
            jl, jr = fr["jet_len"], fr["jet_r"]
            if jl <= 0.05 or jr <= 0.05:
                out_verts.append((-20.0, 0.0, 0.0))
                out_norms.append((-1.0, 0.0, 0.0))
            else:
                # `p_loc[0]` is in `[-1..0]` pointing out the rear `-T_rear`!
                vp = P_rear + T_rear * (p_loc[0] * jl) + L_rear * (p_loc[1] * jr) + U_rear * (p_loc[2] * jr)
                vn = T_rear * n_loc[0] + L_rear * n_loc[1] + U_rear * n_loc[2]
                out_verts.append(tuple(vp))
                out_norms.append(vnorm(vn))
        else:
            out_verts.append(p_loc)
            out_norms.append(n_loc)

    return out_verts, out_norms


# ==============================================================================
# 6. DARKPLACES VBO-ALIGNED MD3 + SKIN + SHADER + GLB EXPORTERS
# ==============================================================================
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
    """Prevents DarkPlaces `gl_vbo 1` multi-surface animated MD3 UV offset shift."""
    if len(md3_surfs) <= 1:
        return md3_surfs
    by_priority = sorted(
        md3_surfs[1:],
        key=lambda x: {"eric_head": 0, "eric_ears": 1, "eric_fx": 2}.get(x["name"], 9),
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
    os.makedirs(STAGE_DIR, exist_ok=True)
    os.makedirs(PROGS_DIR, exist_ok=True)
    nf = len(frame_names)
    dp_surfs = align_md3_surfaces_for_dp_vbo(md3_surfs)
    for s in dp_surfs:
        assert len(s["st"]) <= 4096 and len(s["tris"]) <= 8192, (
            f"MD3 surface overflow on {s['name']}: nv={len(s['st'])}, nt={len(s['tris'])}"
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
    print(f"  [MD3 OK] {model_name:14s} -> {deploy_names}: {len(dp_surfs)} surfs, {tv:4d}v (s0={len(dp_surfs[0]['st'])}<=4096), {tt:4d}t, {nf:2d}f")
    return stage_p


def write_quake_shader():
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    shader = """// written by source/mm_tools/eric_cannon/build_eric_cannon.py

progs/eric_cannon_metal
{
\tcull none
\t{
\t\tmap progs/eric_cannon_metal
\t\trgbGen lightingDiffuse
\t}
}

progs/eric_cannon_head
{
\tcull none
\t{
\t\tmap progs/eric_cannon_head
\t\trgbGen lightingDiffuse
\t}
}

progs/eric_cannon_ears
{
\tcull none
\t{
\t\tmap progs/eric_cannon_ears
\t\trgbGen lightingDiffuse
\t}
}

progs/eric_cannon_fx
{
\tcull none
\tsort 10
\t{
\t\tmap progs/eric_cannon_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""
    sh_path = os.path.join(SCRIPTS_DIR, "eric_cannon.shader")
    open(sh_path, "w", encoding="ascii", newline="\n").write(shader)
    print(f"  [SHADER OK] {sh_path}")


def export_assembled_glb(glb_path, tripod_surfs, yoke_surfs, cannon_surfs, tex_paths, frame_idx=0, include_base=True):
    """Exports a self-contained PBR glTF 2.0 `.glb` of THE ERIC DEASON CANNON in standard glTF meters (`+Y` up, `+Z` front)."""
    bin_buf = bytearray()
    buffer_views, accessors, images, textures, materials, primitives = [], [], [], [], [], []

    def push_bv(raw_bytes, target=None):
        while len(bin_buf) & 3:
            bin_buf.append(0)
        off = len(bin_buf)
        bin_buf.extend(raw_bytes)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw_bytes)}
        if target is not None:
            bv["target"] = target
        buffer_views.append(bv)
        return len(buffer_views) - 1

    mat_defs = {
        "metal": (tex_paths["metal"], 0.35, 0.52, "OPAQUE", False),
        "head":  (tex_paths["head"],  0.00, 0.68, "OPAQUE", False),
        "ears":  (tex_paths["ears"],  0.00, 0.62, "OPAQUE", False),
        "fx":    (tex_paths["fx"],    0.00, 0.25, "BLEND",  True),
    }
    mat_map = {}
    for mk, (tp, met, rough, alpha_mode, emissive) in mat_defs.items():
        raw_png = open(tp, "rb").read()
        bv_i = push_bv(raw_png)
        img_idx = len(images)
        images.append({"bufferView": bv_i, "mimeType": "image/png", "name": mk})
        tex_idx = len(textures)
        textures.append({"source": img_idx})
        m = {
            "name": mk,
            "doubleSided": True,
            "alphaMode": alpha_mode,
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": tex_idx},
                "metallicFactor": met,
                "roughnessFactor": rough,
            },
        }
        if emissive:
            m["emissiveTexture"] = {"index": tex_idx}
            m["emissiveFactor"] = [1.0, 1.0, 1.0]
        mat_map[mk] = len(materials)
        materials.append(m)

    pieces = []
    if include_base:
        for s in tripod_surfs:
            pieces.append((s, 0, lambda p: p, lambda nm: nm))
        for s in yoke_surfs:
            pieces.append((s, 0, lambda p: (p[0], p[1], p[2] + YOKE_BASE_Z), lambda nm: nm))
    for s in cannon_surfs:
        if include_base:
            def xf_c_p(p):
                pr = rot_y_up_pt(p, REST_PITCH_DEG)
                return (pr[0] + CANNON_REST_X, pr[1], pr[2] + CANNON_REST_Z)
            def xf_c_n(nm):
                return rot_y_up_pt(nm, REST_PITCH_DEG)
        else:
            xf_c_p = lambda p: p
            xf_c_n = lambda nm: nm
        pieces.append((s, frame_idx, xf_c_p, xf_c_n))

    scale_m = 0.0254
    for s, fi, xfp, xfn in pieces:
        mk = s["mat"]
        if mk == "fx" and frame_idx == 0:
            continue
        vp_raw, vn_raw = s["frames"][fi]
        vp = np.array([xfp(p) for p in vp_raw], dtype=np.float32)
        vn = np.array([xfn(nm) for nm in vn_raw], dtype=np.float32)
        # Quake (+X front, +Y left, +Z up) -> glTF (+X right = -Y_q, +Y up = +Z_q, +Z front = +X_q)
        gv = np.stack([-vp[:, 1], vp[:, 2], vp[:, 0]], axis=1) * scale_m
        gn = np.stack([-vn[:, 1], vn[:, 2], vn[:, 0]], axis=1)
        gn /= np.maximum(np.linalg.norm(gn, axis=1, keepdims=True), 1e-6)
        uv = np.array(s["st"], dtype=np.float32)
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
        "asset": {"version": "2.0", "generator": "BakersfieldQuake ERIC DEASON CANNON Builder"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "eric_deason_cannon"}],
        "meshes": [{"primitives": primitives, "name": "eric_deason_cannon"}],
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


def build_all():
    os.makedirs(STAGE_DIR, exist_ok=True)
    print("1/4 Building multi-view photo & procedural textures...")
    tex_paths = etex.build_all_textures(TEX_DIR, PROGS_DIR)

    print("2/4 Building static 4-leg tripod (`eric_tripod.md3`) & yawing elevation yoke (`eric_yoke.md3`)...")
    tripod_surfs = build_tripod_model()
    yoke_surfs = build_yoke_model()

    print("3/4 Baking 77-frame deformable `eric_cannon.md3` (Wew-Cannon wind-up/blast + ear flapping)...")
    sched = build_77_frame_schedule()
    frame_names = [fr["name"] for fr in sched]
    spines = [build_spine_table(fr) for fr in sched]
    builders = build_cannon_rest_surfaces()
    frames_per_surf = [[] for _ in builders]
    for fr, sp_tbl in zip(sched, spines):
        for si, sb in enumerate(builders):
            frames_per_surf[si].append(evaluate_surface_for_frame(sb, fr, sp_tbl))
    cannon_surfs = pack_md3_surfaces(builders, frames_per_surf)
    write_md3_with_skins("eric_cannon", cannon_surfs, frame_names, ["eric_cannon"])

    print("4/4 Writing DarkPlaces shader, PBR `.glb` models, and `eric_meta.json`...")
    write_quake_shader()
    export_assembled_glb(os.path.join(MOD_ROOT, "eric_deason_cannon.glb"), tripod_surfs, yoke_surfs, cannon_surfs, tex_paths, frame_idx=0, include_base=True)
    export_assembled_glb(os.path.join(STAGE_DIR, "eric_cannon_blast_pose.glb"), tripod_surfs, yoke_surfs, cannon_surfs, tex_paths, frame_idx=27, include_base=True)

    meta = dict(
        nFrames=len(frame_names),
        frameNames=frame_names,
        yokeBaseZ=YOKE_BASE_Z,
        cannonRestZ=CANNON_REST_Z,
        restPitchDeg=REST_PITCH_DEG,
        ranges=dict(
            ref=[0, 0],
            idle=[1, 16],
            windup=[17, 25],
            blast=[26, 29],
            liftoff=[30, 32],
            boost=[33, 44],
            glide=[45, 60],
            dive=[61, 68],
            flare=[69, 76],
        ),
    )
    open(os.path.join(OUT_ROOT, "eric_meta.json"), "w", encoding="utf-8").write(json.dumps(meta, indent=2))
    print("ALL ERIC DEASON CANNON 3D MODELS BUILT SUCCESSFULLY!")
    return tripod_surfs, yoke_surfs, cannon_surfs, tex_paths


if __name__ == "__main__":
    build_all()
