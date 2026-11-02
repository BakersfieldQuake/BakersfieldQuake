r"""Builds 4 Distinct, Fully Animated Quake Sky-Vehicle Models Combining All 4 Source Videos:
  1. Chrome Shaft + Cross-Axle + Twin White-Dish Pneumatic Tires ('Mega Man' contraption)
  2. White High-Roof Ram ProMaster Walk-In Cargo Van with Swung-Open Rear Barn Doors
  3. 3D Reconstructed Hot-Pink Buoyant Twin-Sphere Lady with Raised V-Arms & Tie-Ribbons
  4. 3D Reconstructed Giant-Eared Screaming Head with Articulated Ornithopter Ear-Wings

Produces 4 Quake/DarkPlaces-ready 56-frame MD3 models in progs/:
  - progs/skyveh_v1.md3 : "THE EAR-NITHOPTER SKY-GALLEON" (Dirigible Figurehead Blimp-Gunship)
  - progs/skyveh_v2.md3 : "THE VALKYRIE V-22 TILT-ROTOR"  (Twin-Nacelle Osprey Assault Dropship)
  - progs/skyveh_v3.md3 : "THE PODRACER SKY-CHARIOT"      (Screaming Tractor-Pod & Autogyro Rotor Rig)
  - progs/skyveh_v4.md3 : "THE BIOMECH MECHA-WYVERN"      (Beetle-Elytra Wing-Shell Sky-Dragon)

Each MD3 contains 56 frames across 4 seamless animations (working for BOTH 'flying' and 'lying'):
  - Frames  0..15 (16f @ 12 fps) : fly_cruise  — Sky-cruising flight, ornithopter ear-flapping, spinning rotors
  - Frames 16..31 (16f @ 18 fps) : fly_boost   — High-speed sky sprint / nose-down dive, rapid flap, max afterburners
  - Frames 32..43 (12f @ 10 fps) : fly_hover   — Buoyant sky hover, vertical VTOL downdraft, ear sculling
  - Frames 44..55 (12f @  8 fps) : lie_rest    — Lying / landed on ground (z=0), folded ear-wings, open boarding doors

Also exports:
  - progs/skyveh_v1..v4.md3_0.skin
  - progs/skyveh_bigears.png, progs/skyveh_pinklady.png, progs/skyveh_fx.png
  - scripts/skyveh.shader
  - progs/skyveh_frames.txt
  - source/mm_tools/out/skyveh/all_4_vehicles_check.png (multi-angle verification render of the written MD3s)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")
OUT_DIR = os.path.join(HERE, "out", "skyveh")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib
import mmw_geometry as mmg

# Animation table shared by all 4 sky vehicles (56 frames total)
ANIM_CLIPS = [
    ("fly_cruise", 0,  16, 12.0, "Sky Cruise (Flapping & Rotor Flight)"),
    ("fly_boost",  16, 16, 18.0, "Sky Boost / Dive Sprint (Afterburners)"),
    ("fly_hover",  32, 12, 10.0, "Sky Hover / VTOL Loiter"),
    ("lie_rest",   44, 12,  8.0, "Lying / Landed at Rest (Boarding Open)"),
]
TOTAL_FRAMES = 56


# --------------------------------------------------------------------------- Fast Vectorized 3D Transform Helpers
def rot_x_mat(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float32)


def rot_y_mat(deg):
    """Positive deg pitches +X UP toward +Z (around -Y? Wait: Ry(+r) on [1,0,0]: let's make +deg pitch nose UP +Z!)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]], dtype=np.float32)


def rot_z_mat(deg):
    """Positive deg yaws +X toward +Y (port/left)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)


def euler_mat(roll_deg=0.0, pitch_deg=0.0, yaw_deg=0.0):
    return rot_z_mat(yaw_deg) @ rot_y_mat(pitch_deg) @ rot_x_mat(roll_deg)


def xform_vn(verts, norms, scale=1.0, R=None, offset=(0.0, 0.0, 0.0)):
    if isinstance(scale, (tuple, list, np.ndarray)):
        sc = np.asarray(scale, dtype=np.float32)
        v = verts * sc
        n = norms / np.maximum(sc, 1e-6)
    else:
        v = verts * float(scale)
        n = norms.copy()
    if R is not None:
        v = v @ R.T
        n = n @ R.T
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8)
    v = v + np.asarray(offset, dtype=np.float32)
    return v, n


def smoothstep01(x):
    t = np.clip(x, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# --------------------------------------------------------------------------- Procedural Texture Generator for FX & Calibrated Skins
def build_skyveh_textures():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROGS, exist_ok=True)

    # 1. Calibrate Big-Ears texture for DarkPlaces HDR while preserving full sRGB copy for HTML viewer
    be_src = Image.open(os.path.join(PROGS, "bigears.png")).convert("RGB")
    be_src.save(os.path.join(OUT_DIR, "bigears_srgb.png"), "PNG")
    be_dp = ImageEnhance.Contrast(be_src).enhance(1.10)
    be_dp = ImageEnhance.Brightness(be_dp).enhance(0.60)
    be_dp.save(os.path.join(PROGS, "skyveh_bigears.png"), "PNG", optimize=True)

    # 2. Build 256x256 Additive Ion / Afterburner / Pink-Plasma FX Texture
    S = 256
    fx = np.zeros((S, S, 3), dtype=np.float32)
    yy, xx = np.meshgrid(np.linspace(0.0, 1.0, S // 2), np.linspace(0.0, 1.0, S // 2), indexing="ij")

    # Top-left Q1 (u: 0..0.5, v: 0..0.5): Electric Cyan-Blue Ion Thruster Plume (v=0 nozzle core -> v=1 tail fade)
    core_c = np.exp(-((yy * 1.45) ** 1.6)) * (0.65 + 0.35 * np.sin(xx * math.pi * 6.0) ** 2)
    hot_c = np.exp(-((yy * 2.8) ** 2))
    q1 = np.stack([
        0.35 * core_c + 0.65 * hot_c,
        0.78 * core_c + 0.22 * hot_c,
        1.00 * np.clip(core_c * 1.25, 0.0, 1.0),
    ], axis=-1) * np.clip(1.0 - yy, 0.0, 1.0)[..., None] ** 0.75
    fx[:S // 2, :S // 2] = q1

    # Top-right Q2 (u: 0.5..1.0, v: 0..0.5): Hot-Pink / Magenta Anti-Grav Plasma Plume & Ring
    core_m = np.exp(-((yy * 1.35) ** 1.5)) * (0.70 + 0.30 * np.cos(xx * math.pi * 4.0) ** 2)
    hot_m = np.exp(-((yy * 2.6) ** 2))
    q2 = np.stack([
        1.00 * np.clip(core_m * 1.2, 0.0, 1.0),
        0.22 * core_m + 0.72 * hot_m,
        0.76 * core_m + 0.24 * hot_m,
    ], axis=-1) * np.clip(1.0 - yy, 0.0, 1.0)[..., None] ** 0.75
    fx[:S // 2, S // 2:] = q2

    # Bottom-left Q3 (u: 0..0.5, v: 0.5..1.0): Superheated Amber-Orange Turbo Afterburner Plume
    core_a = np.exp(-((yy * 1.30) ** 1.5))
    hot_a = np.exp(-((yy * 2.5) ** 2))
    q3 = np.stack([
        1.00 * np.clip(core_a * 1.3, 0.0, 1.0),
        0.55 * core_a + 0.42 * hot_a,
        0.12 * core_a + 0.68 * hot_a,
    ], axis=-1) * np.clip(1.0 - yy, 0.0, 1.0)[..., None] ** 0.70
    fx[S // 2:, :S // 2] = q3

    # Bottom-right Q4 (u: 0.5..1.0, v: 0.5..1.0): Radial Rotor Vortex Ring / Energy Disc
    dx, dy = (xx - 0.5) * 2.0, (yy - 0.5) * 2.0
    rr = np.sqrt(dx * dx + dy * dy)
    ring = np.exp(-(((rr - 0.72) / 0.16) ** 2)) + 0.45 * np.exp(-((rr / 0.32) ** 2))
    q4 = np.stack([0.35 * ring, 0.85 * ring, 1.0 * ring], axis=-1) * (rr <= 1.0)[..., None]
    fx[S // 2:, S // 2:] = q4

    fx_u8 = np.clip(np.rint(fx * 255.0), 0, 255).astype(np.uint8)
    im_fx = Image.fromarray(fx_u8, "RGB")
    im_fx.save(os.path.join(OUT_DIR, "skyveh_fx_srgb.png"), "PNG")
    ImageEnhance.Brightness(im_fx).enhance(0.68).save(os.path.join(PROGS, "skyveh_fx.png"), "PNG", optimize=True)


# --------------------------------------------------------------------------- Biological Deformers for Big-Ears & Pink-Lady
def deform_bigears(verts0, norms0, flap_deg=0.0, twist_deg=0.0, sweep_deg=0.0, jaw_open=0.0):
    """Smoothly flaps & feathers the giant left (+Y) and right (-Y) ears around their anatomical temple hinges
    (|y| = 4.6) with zero distortion on the central face, plus optional screaming jaw opening."""
    v = verts0.copy()
    n = norms0.copy()

    # Optional screaming jaw drop on lower-front chin/mouth (x > 1.2, z < -3.0)
    if abs(jaw_open) > 1e-4:
        jw = smoothstep01((v[:, 0] - 1.2) / 5.5) * smoothstep01((-3.0 - v[:, 2]) / 5.5)
        v[:, 2] -= float(jaw_open) * jw
        v[:, 0] -= float(jaw_open) * 0.22 * jw

    # Smooth ear skinning weight outside temple crease |y| > 4.4 (ear tips reach |y| = 15.0)
    ay = np.abs(v[:, 1])
    lat = np.clip((ay - 4.4) / 10.6, 0.0, 1.0)
    mask = lat > 1e-4
    if not np.any(mask):
        return v, n

    w_flap = smoothstep01(lat[mask] / 0.22) * (0.42 + 0.58 * (lat[mask] ** 0.78))
    w_twist = smoothstep01(lat[mask] / 0.30) * (lat[mask] ** 1.05)
    sgn = np.sign(v[mask, 1])  # +1 port (left ear), -1 starboard (right ear)

    # Local hinge pivot at temple root (x_vert, sgn * 4.5, 0.2)
    piv_y = sgn * 4.5
    piv_z = 0.25
    dy = v[mask, 1] - piv_y
    dz = v[mask, 2] - piv_z
    dx = v[mask, 0] + 0.5  # pitch/twist pivot near ear mid-chord x = -0.5

    # 1) Pitch twist around spanwise Y axis (aerodynamic figure-8 feathering!)
    tw_r = np.radians(twist_deg) * w_twist
    ct, st = np.cos(tw_r), np.sin(tw_r)
    dx1 = dx * ct - dz * st
    dz1 = dx * st + dz * ct
    nx1 = n[mask, 0] * ct - n[mask, 2] * st
    nz1 = n[mask, 0] * st + n[mask, 2] * ct
    ny1 = n[mask, 1].copy()

    # 2) Forward/aft wing sweep around Z axis
    sw_r = np.radians(sweep_deg) * w_flap * (-sgn)
    cs, ss = np.cos(sw_r), np.sin(sw_r)
    dx2 = dx1 * cs - dy * ss
    dy2 = dx1 * ss + dy * cs
    nx2 = nx1 * cs - ny1 * ss
    ny2 = nx1 * ss + ny1 * cs

    # 3) Primary ornithopter dihedral flap around X axis (+flap_deg lifts BOTH ear tips UP +Z!)
    fl_r = np.radians(flap_deg) * w_flap * sgn
    cf, sf = np.cos(fl_r), np.sin(fl_r)
    dy3 = dy2 * cf - dz1 * sf
    dz3 = dy2 * sf + dz1 * cf
    ny3 = ny2 * cf - nz1 * sf
    nz3 = ny2 * sf + nz1 * cf

    v[mask, 0] = dx2 - 0.5
    v[mask, 1] = piv_y + dy3
    v[mask, 2] = piv_z + dz3
    n[mask, 0] = nx2
    n[mask, 1] = ny3
    n[mask, 2] = nz3
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8)
    return v, n


def deform_pinklady(verts0, norms0, arm_wave_deg=0.0, arm_fore_deg=0.0, pod_breath=0.0, pod_bob=0.0,
                    ribbon_back=0.0, ribbon_sway=0.0):
    """Animates the 3D Pink Lady's 3 natural zones:
      1. Raised V-Arms & Open Hands (hinged smoothly at shoulders z=4.5, y=+-5.2)
      2. Buoyant Hot-Pink Twin Spheres (radial inflation breathing + suspension secondary bob)
      3. Dangling Hot-Pink Tie-Ribbons (slipstream backward trail & lateral flutter below z=-16.0)
    """
    v = verts0.copy()
    n = norms0.copy()

    # 1. Raised V-Arms (z > 3.5 and outside head corridor |y| > 4.2 + 0.14*(z - 3.5))
    z_arm = v[:, 2] - 3.8
    ay = np.abs(v[:, 1])
    arm_lat = ay - np.where(v[:, 2] < 13.5, 4.3, 1.5)
    w_arm = smoothstep01(z_arm / 5.5) * smoothstep01(arm_lat / 2.8)
    m_arm = w_arm > 1e-4
    if np.any(m_arm) and (abs(arm_wave_deg) > 1e-4 or abs(arm_fore_deg) > 1e-4):
        sgn = np.sign(v[m_arm, 1])
        py = sgn * 5.2
        pz = 4.2
        dx = v[m_arm, 0] + 1.2
        dy = v[m_arm, 1] - py
        dz = v[m_arm, 2] - pz
        wa = w_arm[m_arm]

        # Outward/inward V-wave around X
        ra = np.radians(arm_wave_deg) * wa * sgn
        ca, sa = np.cos(ra), np.sin(ra)
        dy1 = dy * ca - dz * sa
        dz1 = dy * sa + dz * ca
        ny1 = n[m_arm, 1] * ca - n[m_arm, 2] * sa
        nz1 = n[m_arm, 1] * sa + n[m_arm, 2] * ca

        # Forward/back arm pitch around Y
        rf = np.radians(arm_fore_deg) * wa
        cf, sf = np.cos(rf), np.sin(rf)
        dx2 = dx * cf - dz1 * sf
        dz2 = dx * sf + dz1 * cf
        nx2 = n[m_arm, 0] * cf - nz1 * sf
        nz2 = n[m_arm, 0] * sf + nz1 * cf

        v[m_arm, 0] = dx2 - 1.2
        v[m_arm, 1] = py + dy1
        v[m_arm, 2] = pz + dz2
        n[m_arm, 0] = nx2
        n[m_arm, 1] = ny1
        n[m_arm, 2] = nz2

    # 2. Buoyant Twin Spheres breathing & secondary bob (z in [-17.5 .. +2.5], x > -2.0)
    w_pod = smoothstep01((v[:, 0] + 2.0) / 5.5) * smoothstep01((v[:, 2] + 17.5) / 3.5) * smoothstep01((2.8 - v[:, 2]) / 3.5)
    if abs(pod_breath) > 1e-5 or abs(pod_bob) > 1e-5:
        v[:, 0] += v[:, 0] * float(pod_breath) * w_pod
        v[:, 1] += v[:, 1] * float(pod_breath) * 0.85 * w_pod
        v[:, 2] += float(pod_bob) * w_pod

    # 3. Dangling Hot-Pink Tie-Ribbons flutter (z < -15.8)
    t_rib = np.clip((-15.8 - v[:, 2]) / 13.2, 0.0, 1.0)
    m_rib = t_rib > 1e-4
    if np.any(m_rib):
        tr = t_rib[m_rib]
        v[m_rib, 0] -= float(ribbon_back) * (tr ** 1.45)
        v[m_rib, 1] += float(ribbon_sway) * (tr ** 1.30)
        v[m_rib, 2] += 0.18 * abs(float(ribbon_back)) * (tr ** 1.6)

    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8)
    return v, n


# --------------------------------------------------------------------------- Mesh Accumulator Helper
class SurfBuilder:
    def __init__(self, name, shader):
        self.name = name
        self.shader = shader
        self.verts = []
        self.norms = []
        self.uvs = []
        self.tris = []

    def add_mesh_part(self, mp, scale=1.0, R=None, offset=(0.0, 0.0, 0.0)):
        va = np.asarray(mp.verts, dtype=np.float32)
        na = np.asarray(mp.norms, dtype=np.float32)
        ua = np.asarray(mp.st, dtype=np.float32)
        ta = np.asarray(mp.tris, dtype=np.int32)
        self.add_arrays(va, na, ua, ta, scale=scale, R=R, offset=offset)

    def add_arrays(self, va, na, ua, ta, scale=1.0, R=None, offset=(0.0, 0.0, 0.0)):
        vt, nt = xform_vn(va, na, scale=scale, R=R, offset=offset)
        base = sum(len(x) for x in self.verts)
        self.verts.append(vt)
        self.norms.append(nt)
        self.uvs.append(ua.astype(np.float32))
        self.tris.append(ta.astype(np.int32) + base)

    def finalize_static(self):
        return (
            np.vstack(self.verts).astype(np.float32),
            np.vstack(self.norms).astype(np.float32),
            np.vstack(self.uvs).astype(np.float32),
            np.vstack(self.tris).astype(np.int32),
        )


def make_thruster_bell_part(p0, axis_dir, r_base, r_exit, length, uv_rect=(0.04, 0.54, 0.46, 0.96)):
    """Builds a 3D machined ribbed rocket/ion thruster bell nozzle using mmg.MeshPart."""
    mp = mmg.MeshPart("chrome_axle")
    prof = [
        (0.0, 0.0, 0.05),
        (0.0, r_base * 0.88, 0.12),
        (length * 0.22, r_base, 0.28),
        (length * 0.30, r_base * 0.78, 0.38),  # throat!
        (length * 0.58, r_exit * 0.86, 0.65),
        (length * 0.85, r_exit * 0.98, 0.86),
        (length, r_exit, 0.96),
        (length, r_exit * 0.88, 0.98),
        (length * 0.35, r_base * 0.58, 0.50),  # hollow inner cone!
        (length * 0.35, 0.0, 0.45),
    ]
    mp.add_lathe(tuple(p0), tuple(axis_dir), prof, segs=20, uv_rect=uv_rect)
    return mp


def make_plume_cone_arrays(p0, axis_dir, radius, length, uv_quad="cyan"):
    """Builds a double-layered volumetric additive plasma plume cone + cross-fin for glowing exhaust."""
    uv_map = {
        "cyan":    (0.02, 0.02, 0.48, 0.48),
        "magenta": (0.52, 0.02, 0.98, 0.48),
        "amber":   (0.02, 0.52, 0.48, 0.98),
    }
    u0, v0, u1, v1 = uv_map[uv_quad]
    mp = mmg.MeshPart("fx")
    # Outer plasma cone (v=0 at nozzle hot base -> v=1 at faded tip!)
    mp.add_lathe(
        tuple(p0), tuple(axis_dir),
        [
            (0.0, radius * 0.55, 0.02),
            (length * 0.18, radius, 0.16),
            (length * 0.55, radius * 0.68, 0.55),
            (length, 0.02, 0.98),
        ],
        segs=14, uv_rect=(u0, v0, u1, v1),
    )
    # Inner bright shock-diamond core
    mp.add_lathe(
        tuple(p0), tuple(axis_dir),
        [
            (0.0, radius * 0.30, 0.01),
            (length * 0.32, radius * 0.45, 0.22),
            (length * 0.68, 0.01, 0.85),
        ],
        segs=10, uv_rect=(u0, v0, u1, v1),
    )
    return (
        np.asarray(mp.verts, dtype=np.float32),
        np.asarray(mp.norms, dtype=np.float32),
        np.asarray(mp.st, dtype=np.float32),
        np.asarray(mp.tris, dtype=np.int32),
    )


def make_rotor_disc_arrays(center, normal_axis, r_inner, r_outer):
    """Glowing additive vortex halo ring around spinning pneumatic tire rotors."""
    mp = mmg.MeshPart("fx")
    mp.add_lathe(
        tuple(center), tuple(normal_axis),
        [
            (-0.2, r_inner, 0.58, r_outer),
            (0.0, 0.5 * (r_inner + r_outer), 0.78, r_outer),
            (+0.2, r_outer, 0.98, r_outer),
            (-0.2, r_inner, 0.58, r_outer),
        ],
        segs=24, uv_mode="polar", uv_rect=(0.52, 0.52, 0.98, 0.98),
    )
    return (
        np.asarray(mp.verts, dtype=np.float32),
        np.asarray(mp.norms, dtype=np.float32),
        np.asarray(mp.st, dtype=np.float32),
        np.asarray(mp.tris, dtype=np.int32),
    )


# --------------------------------------------------------------------------- Load Shared Base Source Assets
def load_source_assets():
    # 1. ProMaster Van parts
    with open(os.path.join(HERE, "out", "vehicles_parts.json"), "r", encoding="utf-8") as f:
        van_raw = json.load(f)["van"]["parts"]

    def part_world(p_name):
        p = van_raw[p_name]
        org = np.asarray(p["origin"], dtype=np.float32)
        va = np.asarray(p["verts"], dtype=np.float32) + org
        na = np.asarray(p["norms"], dtype=np.float32)
        ua = np.asarray(p["uvs"], dtype=np.float32)
        ta = np.asarray(p["tris"], dtype=np.int32)
        return va, na, ua, ta, org

    # Split extra_part (swung-open rear barn doors) into left (+Y) and right (-Y) doors around their D-pillar hinges!
    ex_v, ex_n, ex_u, ex_t, _ = part_world("extra_part")
    tri_y = ex_v[ex_t].mean(axis=1)[:, 1]

    def sub_mesh(va, na, ua, ta, mask):
        sel_t = ta[mask]
        used, inv = np.unique(sel_t.ravel(), return_inverse=True)
        return va[used], na[used], ua[used], inv.reshape(-1, 3)

    rdoor_l = sub_mesh(ex_v, ex_n, ex_u, ex_t, tri_y >= 0.0)
    rdoor_r = sub_mesh(ex_v, ex_n, ex_u, ex_t, tri_y < 0.0)

    # Assemble static van_body (chassis + bumpers + hood + cab doors)
    sb_body = SurfBuilder("van_body", "progs/skyveh_van")
    for pn in ("chassis", "bumper_f", "bumper_r", "hood", "door_l", "door_r"):
        va, na, ua, ta, _ = part_world(pn)
        sb_body.add_arrays(va, na, ua, ta)
    van_body_static = sb_body.finalize_static()

    van_detail = part_world("detail_vib")[:4]
    van_wheels = {}
    for wn in ("wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"):
        p = van_raw[wn]
        van_wheels[wn] = (
            np.asarray(p["verts"], dtype=np.float32),
            np.asarray(p["norms"], dtype=np.float32),
            np.asarray(p["uvs"], dtype=np.float32),
            np.asarray(p["tris"], dtype=np.int32),
            np.asarray(p["origin"], dtype=np.float32),
        )

    # 2. Big-Ears Head (split into port >=0 & starboard <0 triangle halves so each surface is ~2320 verts << 4096!)
    be_md3 = md3lib.read(os.path.join(PROGS, "bigears.md3"))
    be_s = be_md3["surfaces"][0]
    be_v = np.asarray(be_s["frames"][0][0], dtype=np.float32)
    be_n = np.asarray(be_s["frames"][0][1], dtype=np.float32)
    be_u = np.asarray(be_s["st"], dtype=np.float32)
    be_t = np.asarray(be_s["tris"], dtype=np.int32)
    be_tri_y = be_v[be_t].mean(axis=1)[:, 1]
    bigears_l = sub_mesh(be_v, be_n, be_u, be_t, be_tri_y >= 0.0)
    bigears_r = sub_mesh(be_v, be_n, be_u, be_t, be_tri_y < 0.0)

    # 3. 3D Pink Lady
    pl_d = np.load(os.path.join(OUT_DIR, "pinklady3d.npz"))
    pinklady = (
        pl_d["verts"].astype(np.float32),
        pl_d["norms"].astype(np.float32),
        pl_d["uvs"].astype(np.float32),
        pl_d["tris"].astype(np.int32),
    )
    # Exact palm centers in Pink Lady local space (z > 24.5)
    pl_v = pinklady[0]
    palm_l = pl_v[(pl_v[:, 2] > 24.5) & (pl_v[:, 1] > 0.0)].mean(axis=0)
    palm_r = pl_v[(pl_v[:, 2] > 24.5) & (pl_v[:, 1] < 0.0)].mean(axis=0)

    # 4. Mega-Man Contraption (chrome bar/axle + left/right pneumatic wheels & hub hardware)
    mm_parts = mmg.build_megaman_payload_parts()

    return {
        "van_body": van_body_static,
        "van_detail": van_detail,
        "rdoor_l": rdoor_l,
        "rdoor_r": rdoor_r,
        "van_wheels": van_wheels,
        "bigears_l": bigears_l,
        "bigears_r": bigears_r,
        "pinklady": pinklady,
        "palm_l": palm_l,
        "palm_r": palm_r,
        "mm_parts": mm_parts,
    }


# --------------------------------------------------------------------------- Per-Frame Motion Parameter Evaluator
def frame_kinematics(fi):
    """Returns normalized animation mode + smooth periodic phase p in [0, 1) + kinematic signals for frame fi in 0..55."""
    if fi < 16:
        mode = "cruise"
        n = 16
        p = fi / float(n)
    elif fi < 32:
        mode = "boost"
        n = 16
        p = (fi - 16) / float(n)
    elif fi < 44:
        mode = "hover"
        n = 12
        p = (fi - 32) / float(n)
    else:
        mode = "lie"
        n = 12
        p = (fi - 44) / float(n)

    tau = 2.0 * math.pi * p
    s1, c1 = math.sin(tau), math.cos(tau)
    s2, c2 = math.sin(2.0 * tau), math.cos(2.0 * tau)

    if mode == "cruise":
        return dict(
            mode=mode, p=p, tau=tau,
            alt_z=26.0 + 4.8 * s1,
            surge_x=1.6 * c1,
            sway_y=2.2 * math.sin(tau - 0.5),
            hull_pitch=2.5 + 2.8 * c1,
            hull_roll=3.8 * math.sin(tau + 0.4),
            hull_yaw=1.8 * s1,
            ear_flap=34.0 * s1 + 5.0,
            ear_twist=-20.0 * c1,
            ear_sweep=7.0 * c1,
            jaw_open=0.5 + 0.5 * max(0.0, s1),
            wheel_spin=360.0 * p,          # 1 full smooth turn per 16 frames (22.5 deg/frame)
            mm_tilt=52.0 + 4.0 * c1,       # forward-tilted cruise thrust
            van_wheel_fold=84.0,           # DeLorean flat hover-pads!
            rdoor_open=0.0 + 6.0 * s1,     # breathing open barn-door rudders
            arm_wave=9.5 * s1,
            arm_fore=4.5 * c1,
            pod_breath=0.035 * math.sin(tau - 0.6),
            pod_bob=-1.2 * c1,
            rib_back=5.8 + 1.8 * s2,
            rib_sway=2.4 * s1,
            plume_scale=1.00 + 0.16 * s2,
        )
    elif mode == "boost":
        return dict(
            mode=mode, p=p, tau=tau,
            alt_z=24.0 + 3.2 * s1,
            surge_x=4.5 + 3.0 * s1,
            sway_y=1.2 * c1,
            hull_pitch=-10.5 + 2.2 * c1,   # aggressive nose-down sprint!
            hull_roll=5.2 * s1,
            hull_yaw=1.2 * c1,
            ear_flap=46.0 * s1 + 4.0,      # deep power-strokes!
            ear_twist=-28.0 * c1,
            ear_sweep=12.0 * c1,
            jaw_open=2.6 + 0.9 * s2,       # full sonic war-cry!
            wheel_spin=360.0 * p,          # played at 18 FPS -> blistering turbo spin!
            mm_tilt=82.0 + 2.5 * s2,       # tilted nearly horizontal forward prop-jet!
            van_wheel_fold=88.0,
            rdoor_open=-18.0 + 4.0 * s2,   # swept back aerodynamically!
            arm_wave=14.0 * s1,
            arm_fore=-8.0 + 4.0 * c1,
            pod_breath=0.045 * s2,
            pod_bob=-1.5 * c1,
            rib_back=10.5 + 2.4 * c2,      # whipping straight back in slipstream!
            rib_sway=3.6 * s2,
            plume_scale=1.85 + 0.28 * c2,  # blazing afterburner cones!
        )
    elif mode == "hover":
        return dict(
            mode=mode, p=p, tau=tau,
            alt_z=30.0 + 6.2 * s1,         # deep buoyant hover bobbing
            surge_x=-1.5 * c1,
            sway_y=1.8 * c1,
            hull_pitch=7.0 + 2.4 * s1,     # nose-up VTOL hover attitude
            hull_roll=2.5 * c1,
            hull_yaw=2.2 * s1,
            ear_flap=24.0 * s1 + 12.0,     # high dihedral sculling
            ear_twist=18.0 * s1,
            ear_sweep=16.0 * c1,           # sweeping forward & back scull!
            jaw_open=0.4 * (0.5 + 0.5 * s1),
            wheel_spin=360.0 * p,          # 30 deg/frame smooth VTOL rotor spin
            mm_tilt=6.0 * s1,              # vertical VTOL lift!
            van_wheel_fold=86.0,
            rdoor_open=10.0 + 5.0 * s1,
            arm_wave=6.5 * s1,
            arm_fore=5.0 * s1,
            pod_breath=0.052 * s1,         # big buoyant helium-pod breathing
            pod_bob=1.8 * math.sin(tau - 0.7),
            rib_back=1.8 + 1.2 * s1,
            rib_sway=2.8 * c1,
            plume_scale=1.15 + 0.18 * s1,
        )
    else:
        # "lie" (Lie_Rest: landed / lying peacefully on z=0 ground, boarding doors wide open, sleepy ear-wing breathing)
        return dict(
            mode=mode, p=p, tau=tau,
            alt_z=0.0 + 0.35 * s1,         # grounded at z ~ 0!
            surge_x=0.0,
            sway_y=0.0,
            hull_pitch=0.3 * s1,
            hull_roll=0.4 * c1,
            hull_yaw=0.0,
            ear_flap=-36.0 + 3.2 * s1,     # giant ear-wings folded/drooped down in relaxed rest!
            ear_twist=6.0 + 1.5 * c1,
            ear_sweep=-4.0,
            jaw_open=0.2 * (0.5 + 0.5 * s1),
            wheel_spin=0.0,                # parked wheels stationary on ground!
            mm_tilt=0.0,                   # landing gear down!
            van_wheel_fold=0.0,            # street tires vertical on pavement!
            rdoor_open=12.0 + 1.2 * s1,    # rear barn doors swung wide open for boarding!
            arm_wave=-6.0 + 2.2 * s1,      # relaxed gentle breathing wave
            arm_fore=2.0 * c1,
            pod_breath=0.025 * s1,
            pod_bob=0.4 * s1,
            rib_back=0.4 + 0.3 * s1,       # ribbons hanging vertically in calm air
            rib_sway=0.5 * c1,
            plume_scale=0.20 + 0.05 * s2,  # tiny idle pilot-light glow
        )


# --------------------------------------------------------------------------- Custom Hardware Builders per Version
def build_version_static_hardware(vid, assets):
    """Builds bespoke chrome trusses, mounting saddles, hydraulic struts, and rocket thruster bells
    for version vid in ('v1', 'v2', 'v3', 'v4') so every joint is 100% physically bolted to the hull!"""
    hw = mmg.MeshPart("chrome_axle")
    uv_chr = (0.04, 0.04, 0.96, 0.46)
    uv_dark = (0.04, 0.54, 0.46, 0.96)
    palm_l, palm_r = assets["palm_l"], assets["palm_r"]

    # Every version gets twin ion thruster bells mounted inside the open rear cargo bay (x=-94+van_dx, y=+-14.5, z=44)
    van_dx = -28.0 if vid == "v3" else 0.0
    for sy in (-1.0, 1.0):
        bell = make_thruster_bell_part((-94.0 + van_dx, sy * 14.5, 44.0), (-1.0, 0.0, 0.0), 7.5, 11.2, 16.0)
        hw.append_part(bell)
        # Mounting frame cross-brace to cargo ribs
        hw.add_tube([(-96.0 + van_dx, sy * 33.5, 44.0), (-96.0 + van_dx, sy * 14.5, 44.0)], [1.4, 1.8], segs=8, uv_rect=uv_chr)
        hw.add_tube([(-96.0 + van_dx, sy * 14.5, 19.0), (-96.0 + van_dx, sy * 14.5, 44.0)], [1.5, 1.5], segs=8, uv_rect=uv_chr)

    if vid == "v1":
        # V1: EAR-NITHOPTER SKY-GALLEON
        # 1) Dorsal chrome turret collar & 4 splayed struts on high roof (z=88.5 -> z=104 at x=-10) for Big-Ears Wing-Head
        hw.add_lathe((-10.0, 0.0, 88.0), (0.0, 0.0, 1.0), [(0.0, 18.0, 0.1), (4.0, 15.5, 0.5), (9.0, 12.5, 0.9)], segs=20, uv_rect=uv_dark)
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                hw.add_tube([(-10.0 + sx * 24.0, sy * 28.0, 87.5), (-10.0 + sx * 9.0, sy * 9.0, 97.0)], [1.6, 1.3], segs=8, uv_rect=uv_chr)

        # 2) Twin gleaming chrome bowsprit booms from cab roof-step & front bumper straight into Pink Lady's raised palms!
        # Pink Lady in V1 is placed at offset=(118, 0, 56), scale=1.18, pitch=+16 deg (tilted forward like galleon figurehead)
        R_pl = euler_mat(0.0, -16.0, 0.0)
        for p_loc, sy in ((palm_l, 1.0), (palm_r, -1.0)):
            p_world = (p_loc * 1.18) @ R_pl.T + np.array([118.0, 0.0, 56.0], dtype=np.float32)
            # Upper suspension boom from roof brow (22, sy*26, 86) -> palm!
            hw.add_tube([(20.0, sy * 26.0, 85.0), (68.0, sy * 22.0, 88.0), tuple(p_world)], [2.1, 1.8, 1.4], segs=10, uv_rect=uv_chr)
            # Lower prow A-frame cradle from front bumper (104, sy*22, 18) -> Pink Lady waist saddle (112, sy*8, 42)
            hw.add_tube([(102.0, sy * 22.0, 18.0), (113.0, sy * 7.5, 42.0)], [2.0, 1.5], segs=10, uv_rect=uv_chr)
        hw.add_lathe((113.0, 0.0, 42.0), (1.0, 0.0, 0.2), [(-4.0, 9.5, 0.1), (2.0, 10.5, 0.8)], segs=16, uv_rect=uv_dark)

        # 3) Belly hydraulic gimbal pylon at (86, +-18, 16 -> 96, +-10, 10) cradling the forward Mega-Man Pitot-Cannon & Tilt-Wheels
        for sy in (-1.0, 1.0):
            hw.add_tube([(74.0, sy * 20.0, 18.0), (96.0, sy * 10.0, 10.0)], [1.9, 1.5], segs=8, uv_rect=uv_chr)
            hw.add_tube([(102.0, sy * 22.0, 18.0), (96.0, sy * 10.0, 10.0)], [1.9, 1.5], segs=8, uv_rect=uv_chr)

    elif vid == "v2":
        # V2: VALKYRIE V-22 OSPREY TILT-ROTOR DROPSHIP
        # 1) Massive structural chrome wing-spar box across upper hull (x=-16, y=-82..+82, z=76) + diagonal struts
        hw.add_chamfer_box(-23.0, -9.0, -80.0, 80.0, 73.0, 79.0, ch=1.2, uv_rect=uv_chr)
        for sy in (-1.0, 1.0):
            # Heavy diagonal lift-strut from lower sill (-16, sy*37, 22) up to wingtip nacelle hub (-16, sy*78, 75)
            hw.add_tube([(-16.0, sy * 36.5, 22.0), (-16.0, sy * 78.0, 75.0)], [2.6, 2.2], segs=10, uv_rect=uv_chr)
            # Wingtip gimbal drum
            hw.add_lathe((-16.0, sy * 80.0, 76.0), (0.0, sy, 0.0), [(-3.0, 7.5, 0.1), (5.0, 6.6, 0.9)], segs=16, uv_rect=uv_dark)

        # 2) Dorsal "Atlas" cupola at (-16, 0, 88) for Pink Lady + overhead cable stays from her palms to wingtips!
        hw.add_lathe((-16.0, 0.0, 87.5), (0.0, 0.0, 1.0), [(0.0, 15.0, 0.2), (6.0, 11.0, 0.8)], segs=18, uv_rect=uv_dark)
        for p_loc, sy in ((palm_l, 1.0), (palm_r, -1.0)):
            p_world = p_loc * 1.18 + np.array([-16.0, 0.0, 114.0], dtype=np.float32)
            hw.add_tube([tuple(p_world), (-16.0, sy * 80.0, 80.0)], [1.1, 1.3], segs=8, uv_rect=uv_chr)

        # 3) Armored nose-collar ring bolting Big-Ears Canard Head cleanly ahead of the snub hood/grille (x=100..112, z=38)
        hw.add_lathe((98.0, 0.0, 38.0), (1.0, 0.0, -0.08), [(0.0, 21.0, 0.1), (12.0, 17.5, 0.9)], segs=20, uv_rect=uv_dark)

    elif vid == "v3":
        # V3: PODRACER SKY-CHARIOT + OVERHEAD AUTOGYRO TWIN-TIRE ROTOR
        # Van hull is shifted aft by dx_van = -28 so total length stays compact & balanced!
        # 1) Twin chrome Podracer tow-booms from van front bumper (76, +-24, 18) forward to Big-Ears Tractor Engine (126, 0, 38)
        for sy in (-1.0, 1.0):
            hw.add_tube([(74.0, sy * 25.0, 19.0), (102.0, sy * 18.0, 27.0), (122.0, sy * 9.0, 36.0)],
                        [2.2, 1.8, 1.5], segs=10, uv_rect=uv_chr)
        # Central dorsal chrome spine brace to back of Big-Ears' skull + lower chin-mounted Chrome Bullet Splitter Ram!
        hw.add_tube([(58.0, 0.0, 42.0), (92.0, 0.0, 40.0), (118.0, 0.0, 40.0)], [2.2, 2.0, 2.4], segs=10, uv_rect=uv_chr)
        hw.add_lathe((118.0, 0.0, 40.0), (1.0, 0.0, 0.0), [(-3.0, 11.5, 0.1), (4.0, 9.5, 0.9)], segs=18, uv_rect=uv_dark)
        # Lower splitter strut & polished bullet ram-lance beneath tractor chin (zero face occlusion!)
        hw.add_tube([(102.0, 0.0, 22.0), (122.0, 0.0, 11.0)], [1.8, 2.2], segs=8, uv_rect=uv_chr)
        hw.add_lathe((116.0, 0.0, 11.0), (1.0, 0.0, 0.0),
                     [(0.0, 0.0, 0.95), (0.0, 4.6, 0.88), (28.0, 4.6, 0.45), (40.0, 3.0, 0.20), (48.0, 0.0, 0.02)], segs=18, uv_rect=uv_chr)

        # 2) Roof pedestal at (-26, 0, 88.5) supporting Pink Lady + V-yoke from her raised palms to Rotor Bearing Collar (-26, 0, 132)!
        hw.add_lathe((-26.0, 0.0, 88.0), (0.0, 0.0, 1.0), [(0.0, 14.5, 0.1), (6.0, 10.5, 0.9)], segs=18, uv_rect=uv_dark)
        for p_loc in (palm_l, palm_r):
            p_world = p_loc * 1.12 + np.array([-26.0, 0.0, 114.0], dtype=np.float32)
            hw.add_tube([tuple(p_world), (-26.0, 0.0, 134.0)], [1.3, 1.7], segs=8, uv_rect=uv_chr)
        hw.add_lathe((-26.0, 0.0, 131.0), (0.0, 0.0, 1.0), [(0.0, 5.2, 0.1), (8.0, 4.2, 0.9)], segs=16, uv_rect=uv_dark)

    elif vid == "v4":
        # V4: BIOMECH MECHA-WYVERN (Beetle-Shell Thorax + Dragon Neck + Siren Prow + Scorpion Stinger Tail)
        # 1) Segmented biomechanical chrome Wyvern Neck curving up & forward from cab roof (22, 0, 72) -> head (78, 0, 106)
        neck_pts = [(18.0, 0.0, 72.0), (38.0, 0.0, 88.0), (58.0, 0.0, 100.0), (74.0, 0.0, 106.0)]
        hw.add_tube(neck_pts, [7.5, 6.2, 5.2, 6.0], segs=14, uv_rect=uv_chr)
        for pt_r, rr in zip(neck_pts[1:], (7.4, 6.4, 6.8)):
            hw.add_lathe(pt_r, (0.85, 0.0, 0.52), [(-1.8, rr, 0.1), (1.8, rr, 0.9)], segs=14, uv_rect=uv_dark)

        # 2) Front Harpy/Siren Prow Cradle bolting Pink Lady across front grille (x=108, z=38)
        for sy in (-1.0, 1.0):
            hw.add_tube([(96.0, sy * 28.0, 22.0), (108.0, sy * 10.0, 34.0)], [2.0, 1.6], segs=8, uv_rect=uv_chr)
            hw.add_tube([(86.0, sy * 24.0, 44.0), (106.0, sy * 9.0, 44.0)], [1.6, 1.4], segs=8, uv_rect=uv_chr)

        # 3) Curved Chrome Scorpion Tail-Boom arching out of open rear cargo hold (-96, 0, 52) -> tail crest (-146, 0, 102)
        tail_pts = [(-94.0, 0.0, 48.0), (-118.0, 0.0, 56.0), (-138.0, 0.0, 76.0), (-146.0, 0.0, 102.0)]
        hw.add_tube(tail_pts, [5.8, 4.8, 4.0, 3.6], segs=12, uv_rect=uv_chr)
        for pt_t, rt in zip(tail_pts[1:], (5.8, 5.0, 4.5)):
            hw.add_lathe(pt_t, (-0.5, 0.0, 0.86), [(-1.6, rt, 0.1), (1.6, rt, 0.9)], segs=12, uv_rect=uv_dark)

    return hw


# --------------------------------------------------------------------------- Full 56-Frame Vehicle Assembler
def build_sky_vehicle_version(vid, title, assets):
    """Builds all 8 animated MD3 surfaces across all 56 frames for version vid ('v1'..'v4')."""
    van_body_v, van_body_n, van_body_u, van_body_t = assets["van_body"]
    vdet_v, vdet_n, vdet_u, vdet_t = assets["van_detail"]
    rdl_v, rdl_n, rdl_u, rdl_t = assets["rdoor_l"]
    rdr_v, rdr_n, rdr_u, rdr_t = assets["rdoor_r"]
    be_l_v, be_l_n, be_l_u, be_l_t = assets["bigears_l"]
    be_r_v, be_r_n, be_r_u, be_r_t = assets["bigears_r"]
    pl_v, pl_n, pl_u, pl_t = assets["pinklady"]
    mm_parts = assets["mm_parts"]

    hw_static = build_version_static_hardware(vid, assets)
    van_dx = -28.0 if vid == "v3" else 0.0
    van_shift = np.array([van_dx, 0.0, 0.0], dtype=np.float32)

    # Pre-collect per-surface topology (st & tris are invariant across all 56 frames!)
    surf_defs = {}

    def record_frame(sname, shader, uvs, tris, vv, nn):
        if sname not in surf_defs:
            surf_defs[sname] = dict(
                name=sname,
                shader=shader,
                st=[tuple(map(float, u)) for u in uvs],
                tris=[tuple(map(int, t)) for t in tris],
                frames=[],
            )
        surf_defs[sname]["frames"].append((
            [tuple(map(float, p)) for p in vv],
            [tuple(map(float, n)) for n in nn],
        ))

    for fi in range(TOTAL_FRAMES):
        K = frame_kinematics(fi)
        R_hull = euler_mat(K["hull_roll"], K["hull_pitch"], K["hull_yaw"])
        hull_pivot = np.array([0.0, 0.0, 40.0], dtype=np.float32)
        hull_ofs = np.array([K["surge_x"], K["sway_y"], K["alt_z"]], dtype=np.float32)

        def to_hull(v_arr, n_arr):
            v_rel = v_arr - hull_pivot
            return (v_rel @ R_hull.T) + hull_pivot + hull_ofs, (n_arr @ R_hull.T)

        # ---- 1. surface: van_body ----
        vb_f, nb_f = to_hull(van_body_v + van_shift, van_body_n)
        record_frame("van_body", "progs/skyveh_van", van_body_u, van_body_t, vb_f, nb_f)

        # ---- 2. surface: van_interior (detail + articulated barn doors + folding DeLorean hover-wheels!) ----
        sb_int = SurfBuilder("van_interior", "progs/skyveh_van")
        sb_int.add_arrays(vdet_v + van_shift, vdet_n, vdet_u, vdet_t)

        if vid == "v4":
            # In V4 (Mecha-Wyvern), the two tall white barn doors hinge on the dorsal roof rails as giant flaring Beetle Elytra wing-shells!
            out_flare = (58.0 + 16.0 * math.sin(K["tau"])) if K["mode"] != "lie" else 166.0
            sweep_back = 24.0 if K["mode"] != "lie" else 4.0
            for d_v, d_n, d_u, d_t, sy in ((rdl_v, rdl_n, rdl_u, rdl_t, 1.0), (rdr_v, rdr_n, rdr_u, rdr_t, -1.0)):
                piv_orig = np.array([-120.0, sy * 38.0, 18.0], dtype=np.float32)
                d_loc = (d_v - piv_orig) * np.array([1.45, 1.0, 1.22], dtype=np.float32)
                # Swing +Z door height outward (+sy*Y) & upward (+Z), swept back along fuselage!
                R_el = rot_z_mat(sy * sweep_back) @ rot_x_mat(-sy * out_flare)
                dv = (d_loc @ R_el.T) + np.array([-28.0, sy * 35.5, 83.0], dtype=np.float32)
                dn = d_n @ R_el.T
                dn /= np.maximum(np.linalg.norm(dn, axis=1, keepdims=True), 1e-8)
                sb_int.add_arrays(dv, dn, d_u, d_t)
        else:
            # Articulated D-pillar rear barn-door airbrakes / boarding doors
            open_ang = K["rdoor_open"]
            for d_v, d_n, d_u, d_t, sy in ((rdl_v, rdl_n, rdl_u, rdl_t, 1.0), (rdr_v, rdr_n, rdr_u, rdr_t, -1.0)):
                hinge = np.array([-105.5, sy * 38.0, 50.0], dtype=np.float32)
                R_d = rot_z_mat(-sy * open_ang)
                dv = ((d_v - hinge) @ R_d.T) + hinge + van_shift
                dn = d_n @ R_d.T
                sb_int.add_arrays(dv, dn, d_u, d_t)

        # Van 4 street wheels: fold 85 deg inward as DeLorean quad hover-thrusters in flight, unfold 0 deg onto z=0 in Lie_Rest!
        w_fold = K["van_wheel_fold"]
        for wn, (wv, wnrm, wuv, wtr, worg) in assets["van_wheels"].items():
            sy = 1.0 if wn.endswith("l") else -1.0
            # Fold around top of tire so folded hover-pad sits flush under wheel well!
            R_wf = rot_x_mat(sy * w_fold)
            R_ws = rot_y_mat(-K["wheel_spin"] * 0.5) if w_fold < 30.0 else np.eye(3, dtype=np.float32)
            R_tot = R_wf @ R_ws
            ofs_w = worg + van_shift + np.array([0.0, -sy * 3.5 * (w_fold / 90.0), 3.0 * (w_fold / 90.0)], dtype=np.float32)
            sb_int.add_arrays(wv, wnrm, wuv, wtr, scale=1.0, R=R_tot, offset=ofs_w)

        vi_v, vi_n, vi_u, vi_t = sb_int.finalize_static()
        vi_vf, vi_nf = to_hull(vi_v, vi_n)
        record_frame("van_interior", "progs/skyveh_van", vi_u, vi_t, vi_vf, vi_nf)

        # ---- 3 & 4. surfaces: bigears_l & bigears_r (Giant-Eared Head with flapping ornithopter ear-wings!) ----
        if vid == "v1":
            be_scale, be_ofs, be_rot = 4.25, (-10.0, 0.0, 114.0), euler_mat(0.0, 4.0, 0.0)
        elif vid == "v2":
            # Nose-cone canard head ahead of snub hood with wide flapping canard dive-ears!
            be_scale, be_ofs, be_rot = 3.55, (115.0, 0.0, 38.0), euler_mat(0.0, -4.0, 0.0)
        elif vid == "v3":
            # Forward Podracer screaming tractor-engine head!
            be_scale = 3.95
            be_ofs = (132.0, 0.0, 41.0 + (2.5 * math.sin(K["tau"] + 0.5) if K["mode"] != "lie" else -2.0))
            be_rot = euler_mat(4.0 * math.cos(K["tau"]) if K["mode"] != "lie" else 0.0, -3.0, 0.0)
        else:
            # V4: Articulated Wyvern Dragon Head banking & looking (socketed cleanly onto neck tip across all 56 frames)!
            be_scale = 4.35
            wy_yaw = 7.0 * math.sin(K["tau"]) if K["mode"] != "lie" else 0.0
            wy_pitch = (-8.0 + 5.0 * math.cos(K["tau"])) if K["mode"] != "lie" else -18.0
            be_ofs = (83.0, 0.0, 111.0 if K["mode"] != "lie" else 108.0)
            be_rot = euler_mat(0.0, wy_pitch, wy_yaw)

        for sname, (bv0, bn0, bu0, bt0) in (("bigears_l", assets["bigears_l"]), ("bigears_r", assets["bigears_r"])):
            dv, dn = deform_bigears(bv0, bn0, flap_deg=K["ear_flap"], twist_deg=K["ear_twist"],
                                    sweep_deg=K["ear_sweep"], jaw_open=K["jaw_open"])
            dv, dn = xform_vn(dv, dn, scale=be_scale, R=be_rot, offset=be_ofs)
            dv, dn = to_hull(dv, dn)
            record_frame(sname, "progs/skyveh_bigears", bu0, bt0, dv, dn)

        # ---- 5. surface: pinklady (3D Pink Lady with buoyant twin-spheres, waving V-arms & fluttering ribbons!) ----
        if vid == "v1":
            pl_scale, pl_ofs, pl_rot = 1.18, (118.0, 0.0, 56.0), euler_mat(0.0, -16.0, 0.0)
        elif vid == "v2":
            pl_scale, pl_ofs, pl_rot = 1.18, (-16.0, 0.0, 114.0), euler_mat(0.0, 0.0, 0.0)
        elif vid == "v3":
            pl_scale, pl_ofs, pl_rot = 1.12, (-26.0, 0.0, 114.0), euler_mat(0.0, 2.0, 0.0)
        else:
            # V4: Harpy/Siren chest-core prow fused onto front grille, arms swept back framing windshield!
            pl_scale, pl_ofs, pl_rot = 1.22, (112.0, 0.0, 42.0), euler_mat(0.0, 24.0, 0.0)

        pdv, pdn = deform_pinklady(
            pl_v, pl_n,
            arm_wave_deg=K["arm_wave"] if vid not in ("v2", "v3") else K["arm_wave"] * 0.25,
            arm_fore_deg=K["arm_fore"] if vid not in ("v2", "v3") else 0.0,
            pod_breath=K["pod_breath"],
            pod_bob=K["pod_bob"],
            ribbon_back=K["rib_back"],
            ribbon_sway=K["rib_sway"],
        )
        pdv, pdn = xform_vn(pdv, pdn, scale=pl_scale, R=pl_rot, offset=pl_ofs)
        pdv, pdn = to_hull(pdv, pdn)
        record_frame("pinklady", "progs/skyveh_pinklady", pl_u, pl_t, pdv, pdn)

        # ---- 6 & 7. surfaces: mm_chrome & mm_wheels (Mega-Man Chrome Shaft/Axle + Spinning Pneumatic Tires!) ----
        sb_chr = SurfBuilder("mm_chrome", "progs/skyveh_chrome")
        sb_whl = SurfBuilder("mm_wheels", "progs/skyveh_wheel")
        sb_fx = SurfBuilder("thruster_fx", "progs/skyveh_fx")

        # Add static vehicle chrome trusses & rear cargo thruster bells
        sb_chr.add_mesh_part(hw_static)

        # Rear cargo bay twin ion thruster plumes
        p_len = 36.0 * K["plume_scale"]
        p_rad = 9.0 * (0.7 + 0.3 * K["plume_scale"])
        q_col = "amber" if K["mode"] == "boost" else "cyan"
        for sy in (-1.0, 1.0):
            pv, pn, pu, pt = make_plume_cone_arrays((-110.0 + van_dx, sy * 14.5, 44.0), (-1.0, 0.0, 0.0), p_rad, p_len, q_col)
            sb_fx.add_arrays(pv, pn, pu, pt)

        spin_deg = K["wheel_spin"]

        if vid == "v1":
            # Forward Chin Pitot-Cannon (chrome bullet bar jutting out under Pink Lady's prow!) + Tilting Cross-Axle Hover-Wheels!
            mm_sc = 5.4
            sb_chr.add_mesh_part(mm_parts["bar_axle"], scale=mm_sc, R=euler_mat(0.0, 0.0, 0.0), offset=(98.0, 0.0, 10.0))
            w_rx = 0.0 if K["mode"] == "lie" else 76.0
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                R_spin = rot_y_mat(-spin_deg)
                R_tilt = rot_x_mat(sy * w_rx)
                R_w = R_tilt @ R_spin
                w_pos = (98.0, sy * (mmg.MM_WHEEL_Y * mm_sc), 18.0 if K["mode"] == "lie" else 10.0)
                sb_whl.add_mesh_part(mm_parts[f"wheel_{side_nm}"], scale=mm_sc * 0.94, R=R_w, offset=w_pos)
                sb_chr.add_mesh_part(mm_parts[f"wheel_hw_{side_nm}"], scale=mm_sc * 0.94, R=R_w, offset=w_pos)
                disc_sc = 0.01 if K["mode"] == "lie" else 1.0
                rv, rn, ru, rt = make_rotor_disc_arrays(w_pos, (0.0, 0.0, -1.0), 10.0 * disc_sc, 22.0 * disc_sc)
                sb_fx.add_arrays(rv, rn, ru, rt)

        elif vid == "v2":
            # Dorsal Mega-Man Chrome Turbine Pod + Twin Wingtip V-22 Osprey Tilt-Rotor Nacelles!
            sb_chr.add_mesh_part(mm_parts["bar_axle"], scale=5.8, R=euler_mat(0.0, 0.0, 0.0), offset=(32.0, 0.0, 82.0))
            nac_sc = 4.6
            # tilt_up: 0 deg = straight UP (+Z helicopter hover), 52 deg = forward cruise, 82 deg = turbo airplane mode!
            tilt_up = 85.0 if K["mode"] == "lie" else K["mm_tilt"]
            nac_body = mmg.MeshPart("chrome_axle")
            nac_body.add_lathe(
                (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                [(-18.0, 0.0, 0.95), (-18.0, 6.2, 0.90), (-12.0, 7.6, 0.72), (6.0, 7.4, 0.35), (15.0, 5.2, 0.16), (22.0, 0.0, 0.02)],
                segs=20, uv_rect=(0.04, 0.04, 0.96, 0.46),
            )
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                # rot_y_mat(+(90 - tilt_up)) sends +X bullet nose to +Z UP at tilt_up=0, and +X FORWARD at tilt_up=90!
                R_nac = rot_y_mat(90.0 - tilt_up)
                nac_pos = (-16.0, sy * 84.0, 76.0)
                sb_chr.add_mesh_part(nac_body, scale=1.0, R=R_nac, offset=nac_pos)

                # Giant Pneumatic Tire spins AROUND the chrome bullet-shaft axis (like a massive Osprey prop-rotor!)
                R_align = rot_z_mat(-90.0 * sy)
                R_spin = rot_x_mat(spin_deg * sy)
                R_w = R_nac @ R_spin @ R_align
                prop_tip = np.array([13.0, 0.0, 0.0], dtype=np.float32) @ R_nac.T + np.asarray(nac_pos, dtype=np.float32)
                sb_whl.add_mesh_part(mm_parts[f"wheel_{side_nm}"], scale=nac_sc * 1.38, R=R_w, offset=tuple(prop_tip))
                sb_chr.add_mesh_part(mm_parts[f"wheel_hw_{side_nm}"], scale=nac_sc * 1.38, R=R_w, offset=tuple(prop_tip))

                prop_axis = np.array([1.0, 0.0, 0.0], dtype=np.float32) @ R_nac.T
                disc_sc = 0.01 if K["mode"] == "lie" else 1.0
                rv, rn, ru, rt = make_rotor_disc_arrays(tuple(prop_tip), tuple(prop_axis), 15.0 * disc_sc, 29.0 * disc_sc)
                sb_fx.add_arrays(rv, rn, ru, rt)
                thrust_axis = -prop_axis
                pv, pn, pu, pt = make_plume_cone_arrays(
                    np.asarray(nac_pos) + thrust_axis * 18.0, thrust_axis, 8.2, 26.0 * K["plume_scale"], "magenta"
                )
                sb_fx.add_arrays(pv, pn, pu, pt)

        elif vid == "v3":
            # Overhead Helicopter / Autogyro Rotor Mast held above Pink Lady's V-hands at (-26, 0, 156)!
            # rot_y_mat(+90) points gleaming chrome bullet tip +Z UP into the sky while cross-axle + twin tires spin in XY!
            mast_pos = (-26.0, 0.0, 156.0)
            R_mast = rot_z_mat(spin_deg) @ rot_y_mat(90.0)
            sb_chr.add_mesh_part(mm_parts["bar_axle"], scale=5.4, R=R_mast, offset=mast_pos)
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                R_local_spin = rot_y_mat(-spin_deg)
                local_ofs = np.array([0.0, sy * mmg.MM_WHEEL_Y * 5.4, 0.0], dtype=np.float32) @ R_mast.T
                w_ofs = np.asarray(mast_pos, dtype=np.float32) + local_ofs
                R_w = R_mast @ R_local_spin
                sb_whl.add_mesh_part(mm_parts[f"wheel_{side_nm}"], scale=5.0, R=R_w, offset=tuple(w_ofs))
                sb_chr.add_mesh_part(mm_parts[f"wheel_hw_{side_nm}"], scale=5.0, R=R_w, offset=tuple(w_ofs))
            disc_sc = 0.01 if K["mode"] == "lie" else 1.0
            rv, rn, ru, rt = make_rotor_disc_arrays((mast_pos[0], mast_pos[1], mast_pos[2] + 2.0), (0.0, 0.0, 1.0), 18.0 * disc_sc, 50.0 * disc_sc)
            sb_fx.add_arrays(rv, rn, ru, rt)

        else:
            # V4: Scorpion Stinger Chrome Tail-Rotor at (-146, 0, 104)!
            # Bullet stinger points menacingly forward & slightly down over the dorsal shell, twin wheels whirl on cross-axle!
            st_pitch = -18.0 + (6.0 * math.sin(K["tau"]) if K["mode"] != "lie" else 14.0)
            st_pos = (-146.0, 0.0, 104.0)
            R_st = euler_mat(0.0, st_pitch, 0.0)
            sb_chr.add_mesh_part(mm_parts["bar_axle"], scale=5.6, R=R_st, offset=st_pos)
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                R_local_spin = rot_y_mat(-spin_deg)
                local_ofs = np.array([0.0, sy * mmg.MM_WHEEL_Y * 5.6, 0.0], dtype=np.float32) @ R_st.T
                w_ofs = np.asarray(st_pos, dtype=np.float32) + local_ofs
                R_w = R_st @ R_local_spin
                sb_whl.add_mesh_part(mm_parts[f"wheel_{side_nm}"], scale=5.2, R=R_w, offset=tuple(w_ofs))
                sb_chr.add_mesh_part(mm_parts[f"wheel_hw_{side_nm}"], scale=5.2, R=R_w, offset=tuple(w_ofs))
            # Glowing magenta Twin-Core chest plasma halo in cargo reactor bay
            pv, pn, pu, pt = make_plume_cone_arrays((-45.0, 0.0, 58.0), (0.0, 0.0, 1.0), 14.0, 26.0 * K["plume_scale"], "magenta")
            sb_fx.add_arrays(pv, pn, pu, pt)

        cv, cn, cu, ct = sb_chr.finalize_static()
        cv, cn = to_hull(cv, cn)
        record_frame("mm_chrome", "progs/skyveh_chrome", cu, ct, cv, cn)

        wv, wn, wu, wt = sb_whl.finalize_static()
        wv, wn = to_hull(wv, wn)
        record_frame("mm_wheels", "progs/skyveh_wheel", wu, wt, wv, wn)

        fv, fn, fu, ft = sb_fx.finalize_static()
        fv, fn = to_hull(fv, fn)
        record_frame("thruster_fx", "progs/skyveh_fx", fu, ft, fv, fn)

    # Ensure Lie_Rest frames (44..55) sit cleanly on z=0 ground plane!
    # Measure minimum solid Z on frame 44 (excluding additive thruster_fx) and shift all frames by -z_ground if needed
    solid_names = [k for k in surf_defs if k != "thruster_fx"]
    z_lie_min = min(min(p[2] for p in surf_defs[sn]["frames"][44][0]) for sn in solid_names)
    dz_fix = -z_lie_min
    for sn, sd in surf_defs.items():
        new_frames = []
        for vv, nn in sd["frames"]:
            vv_s = [(p[0], p[1], p[2] + dz_fix) for p in vv]
            new_frames.append((vv_s, nn))
        sd["frames"] = new_frames

    surfs_list = [
        surf_defs["van_body"],
        surf_defs["van_interior"],
        surf_defs["bigears_l"],
        surf_defs["bigears_r"],
        surf_defs["pinklady"],
        surf_defs["mm_chrome"],
        surf_defs["mm_wheels"],
        surf_defs["thruster_fx"],
    ]

    model_name = f"skyveh_{vid}"
    md3_path = os.path.join(PROGS, f"{model_name}.md3")
    md3lib.write(md3_path, dict(name=model_name, surfaces=surfs_list, nframes=TOTAL_FRAMES))

    skin_path = os.path.join(PROGS, f"{model_name}.md3_0.skin")
    with open(skin_path, "w", encoding="ascii") as f:
        for s in surfs_list:
            f.write(f"{s['name']},{s['shader']}\n")

    tot_v = sum(len(s["st"]) for s in surfs_list)
    tot_t = sum(len(s["tris"]) for s in surfs_list)
    max_sv = max(len(s["st"]) for s in surfs_list)
    print(f"  Wrote {md3_path}: {TOTAL_FRAMES} frames, {len(surfs_list)} surfaces (max_surf_verts={max_sv}), {tot_v} verts, {tot_t} tris ({title})", flush=True)
    return md3_path


def write_shader_and_frame_docs():
    os.makedirs(SCRIPTS, exist_ok=True)
    shader_path = os.path.join(SCRIPTS, "skyveh.shader")
    with open(shader_path, "w", encoding="ascii") as f:
        f.write("""// Quake / DarkPlaces shaders for Sky Vehicles (skyveh_v1 .. skyveh_v4)
progs/skyveh_van
{
\tcull none
\t{
\t\tmap progs/veh_van_tex
\t\trgbGen lightingDiffuse
\t}
\t{
\t\tmap progs/veh_van_tex_glow
\t\tblendfunc add
\t\trgbGen identity
\t}
}

progs/skyveh_bigears
{
\tcull none
\t{
\t\tmap progs/skyveh_bigears
\t\trgbGen lightingDiffuse
\t}
}

progs/skyveh_pinklady
{
\tcull none
\t{
\t\tmap progs/skyveh_pinklady
\t\trgbGen lightingDiffuse
\t}
}

progs/skyveh_chrome
{
\tcull none
\t{
\t\tmap progs/mmw_chrome_axle
\t\trgbGen lightingDiffuse
\t}
}

progs/skyveh_wheel
{
\tcull none
\t{
\t\tmap progs/mmw_wheel
\t\trgbGen lightingDiffuse
\t}
}

progs/skyveh_fx
{
\tcull none
\t{
\t\tmap progs/skyveh_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
""")

    frames_txt = os.path.join(PROGS, "skyveh_frames.txt")
    with open(frames_txt, "w", encoding="utf-8") as f:
        f.write("// Quake MD3 Frame Table for progs/skyveh_v1.md3 .. progs/skyveh_v4.md3 (56 frames)\n")
        for clip_id, start, count, fps, desc in ANIM_CLIPS:
            f.write(f"// {clip_id:12s} : frames {start:2d}..{start + count - 1:2d} ({count:2d} frames @ {fps:4.1f} fps) - {desc}\n")
        f.write("\n$frame " + " ".join(f"fly{i}" for i in range(16)) + "\n")
        f.write("$frame " + " ".join(f"boost{i}" for i in range(16)) + "\n")
        f.write("$frame " + " ".join(f"hover{i}" for i in range(12)) + "\n")
        f.write("$frame " + " ".join(f"lie{i}" for i in range(12)) + "\n")
    print(f"  Wrote {shader_path} and {frames_txt}", flush=True)


# --------------------------------------------------------------------------- Multi-Angle Verification Renderer (Reads Written MD3s!)
def render_all_vehicles_verification(md3_paths, out_png):
    """Reads back the 4 written .md3 files from progs/ and renders a 4x4 grid:
    Rows = V1..V4, Columns = [Front-3/4 Cruise (f=4), Side Boost (f=20), Rear-3/4 Cruise (f=12), Lie_Rest Grounded (f=46)]."""
    tex_lookup = {
        "progs/skyveh_van":      np.array(Image.open(os.path.join(HERE, "out", "vehicles", "veh_van_atlas.png")).convert("RGB")),
        "progs/skyveh_bigears":  np.array(Image.open(os.path.join(OUT_DIR, "bigears_srgb.png")).convert("RGB")),
        "progs/skyveh_pinklady": np.array(Image.open(os.path.join(OUT_DIR, "pinklady3d_srgb.png")).convert("RGB")),
        "progs/skyveh_chrome":   np.array(Image.open(os.path.join(HERE, "out", "megaman_weapon", "mmw_chrome_axle.png")).convert("RGB")),
        "progs/skyveh_wheel":    np.array(Image.open(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png")).convert("RGB")),
        "progs/skyveh_fx":       np.array(Image.open(os.path.join(OUT_DIR, "skyveh_fx_srgb.png")).convert("RGB")),
    }

    W_c, H_c = 420, 300
    cols_cfg = [
        (4,  38.0,  18.0),   # Front-3/4 Cruise (ears lifted!)
        (20, 90.0,  10.0),   # Side Profile Boost (nose down, long afterburners!)
        (12, 146.0, 20.0),   # Rear-3/4 Cruise (open cargo doors + thrusters!)
        (46, 35.0,  15.0),   # Lie_Rest (landed on z=0, drooped ear-wings!)
    ]
    sheet = np.full((H_c * len(md3_paths), W_c * len(cols_cfg), 3), 20, dtype=np.uint8)
    light_dir = np.array([0.48, -0.38, 0.79], dtype=np.float32)
    light_dir /= np.linalg.norm(light_dir)

    for r_idx, path in enumerate(md3_paths):
        m = md3lib.read(path)
        # Compute stable bounding box across cruise frame 0 solid surfaces
        pts0 = np.vstack([np.asarray(s["frames"][0][0], dtype=np.float32) for s in m["surfaces"] if s["name"] != "thruster_fx"])
        ctr = 0.5 * (pts0.min(axis=0) + pts0.max(axis=0))
        span = float(np.max(pts0.max(axis=0) - pts0.min(axis=0)))
        sc = (W_c * 0.78) / span

        for c_idx, (fi, yaw_deg, el_deg) in enumerate(cols_cfg):
            zb = np.full((H_c, W_c), -1e9, dtype=np.float32)
            # Sky gradient background
            grad = np.linspace(0.0, 1.0, H_c)[:, None]
            cb = np.broadcast_to(
                np.clip(
                    np.array([22, 34, 58])[None, None, :] * (1.0 - grad[..., None])
                    + np.array([46, 68, 96])[None, None, :] * grad[..., None],
                    0, 255,
                ).astype(np.float32),
                (H_c, W_c, 3),
            ).copy()

            ry = math.radians(yaw_deg)
            re = math.radians(el_deg)
            cy_a, sy_a = math.cos(ry), math.sin(ry)
            ce_a, se_a = math.cos(re), math.sin(re)

            # Render opaque surfaces first, then additive thruster_fx
            ordered_surfs = [s for s in m["surfaces"] if s["name"] != "thruster_fx"] + [s for s in m["surfaces"] if s["name"] == "thruster_fx"]
            for s in ordered_surfs:
                is_add = s["name"] == "thruster_fx"
                tex = tex_lookup[s["shader"]]
                th, tw = tex.shape[:2]
                va = np.asarray(s["frames"][fi][0], dtype=np.float32) - ctr
                na = np.asarray(s["frames"][fi][1], dtype=np.float32)
                ua = np.asarray(s["st"], dtype=np.float32)
                ta = np.asarray(s["tris"], dtype=np.int32)

                # Yaw around Z, then elevate camera
                x1 = va[:, 0] * cy_a + va[:, 1] * sy_a
                y1 = -va[:, 0] * sy_a + va[:, 1] * cy_a
                z1 = va[:, 2]
                depth = x1 * ce_a + z1 * se_a
                z_scr = -x1 * se_a + z1 * ce_a

                nx1 = na[:, 0] * cy_a + na[:, 1] * sy_a
                ny1 = -na[:, 0] * sy_a + na[:, 1] * cy_a
                nz1 = na[:, 2]

                sx = (W_c * 0.5) - y1 * sc
                sy_px = (H_c * 0.54) - z_scr * sc

                for a, b, c in ta:
                    x_min = max(0, int(min(sx[a], sx[b], sx[c])))
                    x_max = min(W_c - 1, int(max(sx[a], sx[b], sx[c])) + 1)
                    y_min = max(0, int(min(sy_px[a], sy_px[b], sy_px[c])))
                    y_max = min(H_c - 1, int(max(sy_px[a], sy_px[b], sy_px[c])) + 1)
                    if x_max < x_min or y_max < y_min:
                        continue
                    den = (sy_px[b] - sy_px[c]) * (sx[a] - sx[c]) + (sx[c] - sx[b]) * (sy_px[a] - sy_px[c])
                    if abs(den) < 1e-4:
                        continue
                    gx, gy = np.meshgrid(np.arange(x_min, x_max + 1) + 0.5, np.arange(y_min, y_max + 1) + 0.5)
                    w0 = ((sy_px[b] - sy_px[c]) * (gx - sx[c]) + (sx[c] - sx[b]) * (gy - sy_px[c])) / den
                    w1 = ((sy_px[c] - sy_px[a]) * (gx - sx[c]) + (sx[a] - sx[c]) * (gy - sy_px[c])) / den
                    w2 = 1.0 - w0 - w1
                    ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
                    if not ins.any():
                        continue
                    zz = w0[ins] * depth[a] + w1[ins] * depth[b] + w2[ins] * depth[c]
                    yi, xi = gy[ins].astype(np.int32), gx[ins].astype(np.int32)
                    vis = zz > zb[yi, xi]
                    if not vis.any():
                        continue
                    yi, xi, zz = yi[vis], xi[vis], zz[vis]
                    w0v, w1v, w2v = w0[ins][vis], w1[ins][vis], w2[ins][vis]
                    if not is_add:
                        zb[yi, xi] = zz

                    uu = np.mod((w0v * ua[a, 0] + w1v * ua[b, 0] + w2v * ua[c, 0]), 1.0)
                    vv = np.mod((w0v * ua[a, 1] + w1v * ua[b, 1] + w2v * ua[c, 1]), 1.0)
                    ui = np.clip((uu * (tw - 1)).astype(np.int32), 0, tw - 1)
                    vi = np.clip((vv * (th - 1)).astype(np.int32), 0, th - 1)

                    if is_add:
                        cb[yi, xi] = np.clip(cb[yi, xi] + tex[vi, ui].astype(np.float32) * 0.85, 0.0, 255.0)
                    else:
                        nnx = w0v * nx1[a] + w1v * nx1[b] + w2v * nx1[c]
                        nny = w0v * ny1[a] + w1v * ny1[b] + w2v * ny1[c]
                        nnz = w0v * nz1[a] + w1v * nz1[b] + w2v * nz1[c]
                        nl = np.maximum(np.sqrt(nnx * nnx + nny * nny + nnz * nnz), 1e-6)
                        ndotl = np.abs(nnx * light_dir[0] + nny * light_dir[1] + nnz * light_dir[2]) / nl
                        lit = 0.42 + 0.65 * ndotl
                        cb[yi, xi] = np.clip(tex[vi, ui].astype(np.float32) * lit[:, None], 0.0, 255.0)

            sheet[r_idx * H_c:(r_idx + 1) * H_c, c_idx * W_c:(c_idx + 1) * W_c] = cb.astype(np.uint8)

    Image.fromarray(sheet, "RGB").save(out_png, "PNG")
    print(f"  Wrote 4x4 MD3 verification render sheet: {out_png}", flush=True)


def main():
    versions = [
        ("v1", "Version 1: The Ear-nithopter Sky-Galleon"),
        ("v2", "Version 2: The Valkyrie V-22 Tilt-Rotor"),
        ("v3", "Version 3: The Podracer Sky-Chariot & Rotor"),
        ("v4", "Version 4: The Biomech Mecha-Wyvern"),
    ]
    if "--only-v4" in sys.argv:
        assets = load_source_assets()
        build_sky_vehicle_version("v4", "Version 4: The Biomech Mecha-Wyvern", assets)
        md3_paths = [os.path.join(PROGS, f"skyveh_{vid}.md3") for vid, _ in versions]
    elif "--render-only" not in sys.argv:
        print("1. Generating calibrated DarkPlaces & WebGL2 sky-vehicle textures...", flush=True)
        build_skyveh_textures()

        print("2. Loading 4 source 3D assets (ProMaster Van, Big-Ears Head, 3D Pink Lady, Mega-Man Axle/Wheels)...", flush=True)
        assets = load_source_assets()

        print("3. Building 4 Quake 56-frame MD3 models (Cruise / Boost / Hover / Lie_Rest)...", flush=True)
        md3_paths = [build_sky_vehicle_version(vid, title, assets) for vid, title in versions]

        print("4. Writing DarkPlaces shader & QuakeC frame manifest...", flush=True)
        write_shader_and_frame_docs()
    else:
        md3_paths = [os.path.join(PROGS, f"skyveh_{vid}.md3") for vid, _ in versions]

    print("5. Rendering 4x4 multi-angle verification sheet from written MD3s...", flush=True)
    check_png = os.path.join(OUT_DIR, "all_4_vehicles_check.png")
    render_all_vehicles_verification(md3_paths, check_png)
    print("ALL 4 QUAKE SKY VEHICLES BUILT SUCCESSFULLY!", flush=True)


if __name__ == "__main__":
    main()
