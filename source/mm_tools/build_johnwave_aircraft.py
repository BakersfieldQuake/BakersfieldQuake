r"""Builds 3 Outrageously Funny, Quake-Ready 3D Aircraft Combining:
  - JOHN WAVE'S 3D HEADS (Giant Screaming Wind-Whipped Mane Head + Deadpan Calm Lush-Beard Head + Tidal-Wave Surf Ring)
  - THE MEGA MAN BAR (Gleaming Chrome Bullet Shaft, TIG Cross-Axle & Concave White-Dish Pneumatic Rubber Tires)

Produces 4 Quake/DarkPlaces-ready 72-frame MD3 models in progs/:
  - progs/jw_aircraft.md3 (Flagship alias of V1)
  - progs/jw_air_v1.md3 : F-69 "THE MOUTH-BREATHER"   (Cigar-Chomping Mustache-Propeller Hair-Wing Biplane)
  - progs/jw_air_v2.md3 : SR-99 "IN-ONE-EAR"          (Ear-Skewered Beats-By-Mega-Man Tilt-Rotor Supersonic Jet)
  - progs/jw_air_v3.md3 : CH-99 "THE HAIR-ICOPTER"    (Push-Me-Pull-You Propeller-Beanie Tandem Chinook)

Each MD3 contains 72 frames across 5 seamless Quake animations (flying, stunts, hover & lying/landed):
  - Frames  0..15 (16f @ 12 fps) : fly_cruise      — Shampoo-wave hair-wing flapping, rhythmic jaw-chomping, spinning tire-props
  - Frames 16..31 (16f @ 18 fps) : fly_boost       — MAXIMUM OVERBITE Mach-5 scream, swept hair, tidal-wave afterburner
  - Frames 32..43 (12f @ 10 fps) : fly_hover       — Buoyant VTOL hair-sculling hover & vertical rotor downdraft
  - Frames 44..55 (12f @  8 fps) : lie_rest        — Landed / parked on z=0 runway on Mega-Man wheels, sleepy snoring jaw
  - Frames 56..71 (16f @ 16 fps) : fly_barrel_roll — Full 360-degree unhinged aileron barrel-roll stunt!

Also exports:
  - progs/jw_aircraft.md3_0.skin, progs/jw_air_v1..v3.md3_0.skin
  - progs/jw_air_scream.png, progs/jw_air_calm.png, progs/jw_air_wave.png, progs/jw_air_fx.png
  - scripts/jw_aircraft.shader
  - progs/jw_aircraft_frames.txt
  - source/mm_tools/out/jw_air/jw_aircraft_check.png (multi-angle verification sheet rendered from written MD3s)
"""
import math
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")
OUT_DIR = os.path.join(HERE, "out", "jw_air")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_head_grenade as bhg
import md3lib
import mmw_geometry as mmg

ANIM_CLIPS = [
    ("fly_cruise",      0,  16, 12.0, "Shampoo-Wave Cruise & Rhythmic Jaw-Chomp"),
    ("fly_boost",       16, 16, 18.0, "MAXIMUM OVERBITE Mach-5 Afterburner Scream"),
    ("fly_hover",       32, 12, 10.0, "Buoyant Hair-Sculling VTOL Hover"),
    ("lie_rest",        44, 12,  8.0, "Parked / Lying on Runway (Snoring Idle)"),
    ("fly_barrel_roll", 56, 16, 16.0, "Unhinged 360° Aileron Barrel-Roll Stunt"),
]
TOTAL_FRAMES = 72


# --------------------------------------------------------------------------- Vectorized 3D Transform Helpers
def rot_x_mat(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float32)


def rot_y_mat(deg):
    """+deg pitches +X UP toward +Z and tilts +Z AFT toward -X (with row-vector v @ R.T)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]], dtype=np.float32)


def rot_z_mat(deg):
    """+deg yaws +X toward +Y (port/left)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)


def euler_mat(roll_deg=0.0, pitch_deg=0.0, yaw_deg=0.0):
    return rot_z_mat(yaw_deg) @ rot_y_mat(pitch_deg) @ rot_x_mat(roll_deg)


def xform_vn(verts, norms, scale=1.0, R=None, offset=(0.0, 0.0, 0.0)):
    if isinstance(scale, (tuple, list, np.ndarray)):
        sc = np.asarray(scale, dtype=np.float32)
        v = verts * sc
        n = norms / np.maximum(np.abs(sc), 1e-6)
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


class SurfBuilder:
    def __init__(self, name, shader):
        self.name = name
        self.shader = shader
        self.parts = []

    def add_mesh_part(self, mp, scale=1.0, R=None, offset=(0.0, 0.0, 0.0)):
        self.add_arrays(
            np.asarray(mp.verts, dtype=np.float32),
            np.asarray(mp.norms, dtype=np.float32),
            np.asarray(mp.st, dtype=np.float32),
            np.asarray(mp.tris, dtype=np.int32),
            scale=scale, R=R, offset=offset,
        )

    def add_arrays(self, va, na, ua, ta, scale=1.0, R=None, offset=(0.0, 0.0, 0.0)):
        vt, nt = xform_vn(va, na, scale=scale, R=R, offset=offset)
        self.parts.append((vt, nt, ua.astype(np.float32), ta.astype(np.int32)))

    def finalize_chunks(self, max_v=3600, max_t=7200):
        """Packs whole parts into MD3-compliant surface chunks (<= max_v verts, <= max_t tris)."""
        chunks = []
        cur_v_list, cur_n_list, cur_u_list, cur_t_list = [], [], [], []
        cur_v, cur_t = 0, 0

        def flush():
            nonlocal cur_v_list, cur_n_list, cur_u_list, cur_t_list, cur_v, cur_t
            if not cur_v_list:
                return
            idx = len(chunks)
            cname = self.name if idx == 0 else f"{self.name}_{idx}"
            chunks.append((
                cname,
                self.shader,
                np.vstack(cur_v_list).astype(np.float32),
                np.vstack(cur_n_list).astype(np.float32),
                np.vstack(cur_u_list).astype(np.float32),
                np.vstack(cur_t_list).astype(np.int32),
            ))
            cur_v_list, cur_n_list, cur_u_list, cur_t_list = [], [], [], []
            cur_v, cur_t = 0, 0

        for vt, nt, ua, ta in self.parts:
            if cur_v_list and (cur_v + len(vt) > max_v or cur_t + len(ta) > max_t):
                flush()
            cur_v_list.append(vt)
            cur_n_list.append(nt)
            cur_u_list.append(ua)
            cur_t_list.append(ta + cur_v)
            cur_v += len(vt)
            cur_t += len(ta)
        flush()
        return chunks


# --------------------------------------------------------------------------- Custom Lite Pneumatic Wheel Builder
def build_wheel_pair_custom(segs=22):
    """Builds left (+1) and right (-1) Mega-Man concave white-dish pneumatic wheels with configurable radial segments
    so multiple wheel assemblies fit comfortably inside Quake MD3's 4096-vertex-per-surface limit."""
    out = {}
    for side_nm, side_sign in (("l", +1), ("r", -1)):
        wp = mmg.MeshPart("wheel")
        hp = mmg.MeshPart("chrome_axle")
        axis = (0.0, float(side_sign), 0.0)
        up_h = (0.0, 0.0, 1.0)

        # 1) Inner White Steel Hub Disc
        wp.add_lathe(
            (0.0, 0.0, 0.0), axis,
            [(-0.86, 0.00, 0.0, 2.38), (-0.86, 0.58, 0.25, 2.38), (-0.74, 1.92, 0.80, 2.38),
             (-0.90, 2.22, 0.93, 2.38), (-0.86, 2.38, 1.00, 2.38)],
            segs=segs, uv_mode="polar", uv_rect=(0.51, 0.51, 0.99, 0.99), up_hint=up_h,
        )
        # 2) Inner Rubber Tire Sidewall
        wp.add_lathe(
            (0.0, 0.0, 0.0), axis,
            [(-0.86, 2.38, 0.59, 4.02), (-0.98, 2.85, 0.71, 4.02), (-1.06, 3.38, 0.84, 4.02),
             (-1.00, 3.82, 0.95, 4.02), (-0.84, 3.95, 0.98, 4.02)],
            segs=segs, uv_mode="polar", uv_rect=(0.51, 0.01, 0.99, 0.49), up_hint=up_h,
        )
        # 3) 5-Ribbed Sculpted Rubber Tread Crown
        X_w, Y_w, Z_w = mmg.basis_from_axis(axis, up_hint=up_h)
        tread_prof = [
            (-0.84, 3.95, 0.02), (-0.68, 4.03, 0.12), (-0.48, 3.92, 0.21), (-0.32, 4.04, 0.30),
            (-0.16, 3.92, 0.40), (+0.00, 4.04, 0.50), (+0.16, 3.92, 0.60), (+0.32, 4.04, 0.70),
            (+0.48, 3.92, 0.79), (+0.68, 4.03, 0.88), (+0.84, 3.95, 0.98),
        ]
        cols = segs + 1
        b_tr = len(wp.verts)
        tr_pts = []
        for sp, rp, ut in tread_prof:
            for j in range(cols):
                th = 2.0 * math.pi * (j / float(segs))
                cth, sth = math.cos(th), math.sin(th)
                pos = mmg.vadd(mmg.vmul(X_w, sp), mmg.vadd(mmg.vmul(Y_w, rp * cth), mmg.vmul(Z_w, rp * sth)))
                tr_pts.append(pos)
                wp.st.append((0.01 + 0.48 * ut, 0.01 + 0.48 * (j / float(segs))))
        tr_acc = [[0.0, 0.0, 0.0] for _ in tr_pts]
        tr_tris = []
        for i in range(len(tread_prof) - 1):
            for j in range(segs):
                a = i * cols + j
                b, c, d = a + 1, a + cols, a + cols + 1
                for t_tri in ((a, b, c), (b, d, c)):
                    fn = mmg.vcross(mmg.vsub(tr_pts[t_tri[1]], tr_pts[t_tri[0]]), mmg.vsub(tr_pts[t_tri[2]], tr_pts[t_tri[0]]))
                    tr_tris.append(t_tri)
                    for vi in t_tri:
                        tr_acc[vi][0] += fn[0]
                        tr_acc[vi][1] += fn[1]
                        tr_acc[vi][2] += fn[2]
        for i in range(len(tread_prof)):
            i0, i1 = i * cols, i * cols + segs
            sn = mmg.vadd(tr_acc[i0], tr_acc[i1])
            tr_acc[i0], tr_acc[i1] = list(sn), list(sn)
        wp.verts += tr_pts
        wp.norms += [mmg.vnorm(n) for n in tr_acc]
        wp.tris += [(a + b_tr, b + b_tr, c + b_tr) for (a, b, c) in tr_tris]

        # 4) Outer Rubber Tire Sidewall
        wp.add_lathe(
            (0.0, 0.0, 0.0), axis,
            [(+0.84, 3.95, 0.98, 4.02), (+1.00, 3.82, 0.95, 4.02), (+1.06, 3.38, 0.84, 4.02),
             (+0.98, 2.85, 0.71, 4.02), (+0.88, 2.38, 0.59, 4.02)],
            segs=segs, uv_mode="polar", uv_rect=(0.51, 0.01, 0.99, 0.49), up_hint=up_h,
        )
        # 5) Concave Outer White Stamped-Steel Dish Rim
        wp.add_lathe(
            (0.0, 0.0, 0.0), axis,
            [(+0.88, 2.38, 1.00, 2.38), (+0.95, 2.20, 0.92, 2.38), (+0.82, 1.98, 0.83, 2.38),
             (+0.38, 1.56, 0.65, 2.38), (+0.34, 0.92, 0.39, 2.38), (+0.66, 0.56, 0.24, 2.38), (+0.66, 0.00, 0.00, 2.38)],
            segs=segs, uv_mode="polar", uv_rect=(0.01, 0.51, 0.49, 0.99), up_hint=up_h,
        )
        # 6) Hex Zinc Nut + Axle Tip + Yellow Cotter Pin
        hp.add_lathe((0.0, 0.0, 0.0), axis, [(+0.66, 0.40, 0.1), (+0.90, 0.40, 0.9), (+0.90, 0.22, 0.95)],
                     segs=6, uv_rect=(0.52, 0.52, 0.73, 0.73), up_hint=up_h)
        hp.add_lathe((0.0, 0.0, 0.0), axis, [(+0.88, 0.22, 0.1), (+1.08, 0.21, 0.9), (+1.08, 0.00, 1.0)],
                     segs=8, uv_rect=(0.52, 0.04, 0.96, 0.46), up_hint=up_h)
        pin_c = mmg.vmul(X_w, 0.98)
        hp.add_tube([mmg.vadd(pin_c, mmg.vmul(Z_w, -0.46)), mmg.vadd(pin_c, mmg.vmul(Z_w, +0.42))],
                    [0.06, 0.06], segs=6, uv_rect=(0.76, 0.52, 0.98, 0.73))
        out[f"wheel_{side_nm}"] = wp
        out[f"wheel_hw_{side_nm}"] = hp
    return out


# --------------------------------------------------------------------------- Textures & John Wave Head Builders
def build_textures_and_calm_john():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROGS, exist_ok=True)

    # 1. Despill & Tone-Map Screaming John Head Texture (progs/johnhead3d.png)
    jh_raw = np.asarray(Image.open(os.path.join(PROGS, "johnhead3d.png")).convert("RGB"), dtype=np.float32)
    r, g, b = jh_raw[..., 0], jh_raw[..., 1], jh_raw[..., 2]
    # Remove green-screen spill on outer hair curls while preserving warm chestnut brown & skin tones
    rb_max = np.maximum(r, b)
    spill = g > rb_max + 4.0
    g_clean = np.where(spill, 0.88 * rb_max + 0.12 * g, g)
    jh_clean = np.stack([r, g_clean, b], axis=-1)

    # DarkPlaces calibrated texture (johnhead3d.png was already pre-darkened; give gentle 1.12x clarity boost)
    jh_dp = np.clip(np.rint(jh_clean * 1.12), 0, 255).astype(np.uint8)
    Image.fromarray(jh_dp, "RGB").save(os.path.join(PROGS, "jw_air_scream.png"), "PNG", optimize=True)

    # Vivid sRGB texture for WebGL2 Hangar & verification renders (lifts pre-darkened midtones cleanly)
    lin = np.clip(jh_clean / 255.0, 0.0, 1.0)
    srgb_f = 1.0 - np.exp(-2.35 * (lin ** 0.78))
    # Preserve crisp white teeth / eye highlights
    srgb_f = np.clip(srgb_f * 1.08, 0.0, 1.0)
    jh_srgb = np.clip(np.rint(srgb_f * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(jh_srgb, "RGB").save(os.path.join(OUT_DIR, "jw_scream_srgb.png"), "PNG")

    # 2. Build Deadpan Calm Lush-Hair 3D John Wave Head (from johnwave_head_green.jpg + suit_back.jpg)
    calm_m = bhg.build()
    calm_srgb = bhg.skin(calm_m, 2, 1.28)
    calm_dp = bhg.skin(calm_m, 2, 0.72)
    Image.fromarray(calm_srgb, "RGB").save(os.path.join(OUT_DIR, "jw_calm_srgb.png"), "PNG")
    Image.fromarray(calm_dp, "RGB").save(os.path.join(PROGS, "jw_air_calm.png"), "PNG", optimize=True)

    # Construct welded cylindrical MD3 mesh for Deadpan John (MH=32 rings x (NH+1)=29 cols + 2 caps = 930 verts!)
    MH, NH = bhg.MH, bhg.NH
    V_raw = calm_m["V"]
    ring_V = V_raw[:MH * NH].reshape(MH, NH, 3)
    bot_pole = V_raw[MH * NH]
    top_pole = V_raw[MH * NH + 1]

    verts_c, uvs_c, tris_c = [], [], []
    cols = NH + 1
    for j in range(MH):
        vv_uv = (MH - 1 - j) / float(MH - 1)
        for k in range(cols):
            p = ring_V[j, k % NH]
            verts_c.append(p)
            uvs_c.append((k / float(NH), vv_uv))

    i_bot = len(verts_c)
    verts_c.append(bot_pole)
    uvs_c.append((0.5, 1.0))
    i_top = len(verts_c)
    verts_c.append(top_pole)
    uvs_c.append((0.5, 0.0))

    verts_c = np.asarray(verts_c, dtype=np.float32)
    uvs_c = np.asarray(uvs_c, dtype=np.float32)

    def add_outward_tri(a, b, c, out_dir):
        fn = np.cross(verts_c[b] - verts_c[a], verts_c[c] - verts_c[a])
        if float(np.dot(fn, out_dir)) < 0.0:
            b, c = c, b
        tris_c.append((a, b, c))

    for j in range(MH - 1):
        rc = 0.5 * (ring_V[j].mean(axis=0) + ring_V[j + 1].mean(axis=0))
        for k in range(NH):
            a = j * cols + k
            b = a + 1
            d = (j + 1) * cols + k
            c = d + 1
            cen = 0.25 * (verts_c[a] + verts_c[b] + verts_c[c] + verts_c[d])
            add_outward_tri(a, b, c, cen - rc)
            add_outward_tri(a, c, d, cen - rc)

    for k in range(NH):
        add_outward_tri(k, k + 1, i_bot, np.array([0.0, 0.0, -1.0], dtype=np.float32))
        top_row = (MH - 1) * cols
        add_outward_tri(top_row + k, top_row + k + 1, i_top, np.array([0.0, 0.0, +1.0], dtype=np.float32))

    tris_c = np.asarray(tris_c, dtype=np.int32)
    # Smooth area-weighted vertex normals with welded back-seam
    norms_c = np.zeros_like(verts_c)
    v0 = verts_c[tris_c[:, 0]]
    v1 = verts_c[tris_c[:, 1]]
    v2 = verts_c[tris_c[:, 2]]
    fn_all = np.cross(v1 - v0, v2 - v0)
    for c_i in range(3):
        np.add.at(norms_c, tris_c[:, c_i], fn_all)
    for j in range(MH):
        i0, i1 = j * cols, j * cols + NH
        sn = norms_c[i0] + norms_c[i1]
        norms_c[i0] = sn
        norms_c[i1] = sn
    norms_c /= np.maximum(np.linalg.norm(norms_c, axis=1, keepdims=True), 1e-8)

    # 3. Build 256x256 Stylized Foamy "JOHN WAVE" Ocean Surf Texture (progs/jw_air_wave.png)
    W_w, H_w = 256, 256
    vv, uu = np.meshgrid(np.linspace(0.0, 1.0, H_w), np.linspace(0.0, 1.0, W_w), indexing="ij")
    # Deep Pacific teal at base (v=0) -> turquoise curl -> bright white foaming wave crest (v=0.55..0.85)
    ripple = 0.06 * np.sin(uu * math.pi * 10.0 + vv * 5.0) + 0.04 * np.cos(uu * math.pi * 18.0 - vv * 8.0)
    vn = np.clip(vv + ripple, 0.0, 1.0)
    foam = smoothstep01((vn - 0.48) / 0.34) * (0.78 + 0.22 * np.sin(uu * math.pi * 24.0 + vn * 12.0) ** 2)
    streaks = 0.16 * (np.sin(uu * math.pi * 16.0 + vn * 9.0) ** 2) * smoothstep01((vn - 0.12) / 0.5)
    wave_rgb = np.stack([
        0.08 + 0.24 * vn + 0.68 * foam + 0.18 * streaks,
        0.38 + 0.38 * vn + 0.28 * foam + 0.20 * streaks,
        0.58 + 0.32 * vn + 0.14 * foam + 0.15 * streaks,
    ], axis=-1)
    wave_u8 = np.clip(np.rint(wave_rgb * 255.0), 0, 255).astype(np.uint8)
    im_wave = Image.fromarray(wave_u8, "RGB")
    im_wave.save(os.path.join(OUT_DIR, "jw_wave_srgb.png"), "PNG")
    ImageEnhance.Brightness(im_wave).enhance(0.68).save(os.path.join(PROGS, "jw_air_wave.png"), "PNG", optimize=True)

    # 4. Build 256x256 Additive Afterburner / Ocean-Plasma / Beanie-Halo FX Texture (progs/jw_air_fx.png)
    S = 256
    fx = np.zeros((S, S, 3), dtype=np.float32)
    yy, xx = np.meshgrid(np.linspace(0.0, 1.0, S // 2), np.linspace(0.0, 1.0, S // 2), indexing="ij")

    # Q1: Electric Aqua-Cyan "John Wave" Hydro-Ion Plume
    core_c = np.exp(-((yy * 1.40) ** 1.6)) * (0.65 + 0.35 * np.sin(xx * math.pi * 6.0) ** 2)
    hot_c = np.exp(-((yy * 2.7) ** 2))
    fx[:S // 2, :S // 2] = np.stack([
        0.30 * core_c + 0.70 * hot_c,
        0.84 * core_c + 0.16 * hot_c,
        1.00 * np.clip(core_c * 1.28, 0.0, 1.0),
    ], axis=-1) * np.clip(1.0 - yy, 0.0, 1.0)[..., None] ** 0.72

    # Q2: Neon Hot-Magenta / Gold Shampoo-Power Plume
    core_m = np.exp(-((yy * 1.35) ** 1.5)) * (0.70 + 0.30 * np.cos(xx * math.pi * 4.0) ** 2)
    hot_m = np.exp(-((yy * 2.6) ** 2))
    fx[:S // 2, S // 2:] = np.stack([
        1.00 * np.clip(core_m * 1.25, 0.0, 1.0),
        0.30 * core_m + 0.68 * hot_m,
        0.82 * core_m + 0.18 * hot_m,
    ], axis=-1) * np.clip(1.0 - yy, 0.0, 1.0)[..., None] ** 0.74

    # Q3: Blazing Mach-5 Afterburner Flame (Amber-White Shock Diamonds)
    core_a = np.exp(-((yy * 1.25) ** 1.45)) * (0.78 + 0.22 * np.cos(yy * math.pi * 7.0) ** 2)
    hot_a = np.exp(-((yy * 2.5) ** 2))
    fx[S // 2:, :S // 2] = np.stack([
        1.00 * np.clip(core_a * 1.32, 0.0, 1.0),
        0.58 * core_a + 0.40 * hot_a,
        0.14 * core_a + 0.72 * hot_a,
    ], axis=-1) * np.clip(1.0 - yy, 0.0, 1.0)[..., None] ** 0.68

    # Q4: Radial Propeller / Rotor Blur Vortex Ring
    dx, dy = (xx - 0.5) * 2.0, (yy - 0.5) * 2.0
    rr = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    blades = 0.72 + 0.28 * (np.sin(ang * 4.0 + rr * 3.0) ** 2)
    ring = (np.exp(-(((rr - 0.70) / 0.18) ** 2)) + 0.50 * np.exp(-((rr / 0.34) ** 2))) * blades
    fx[S // 2:, S // 2:] = np.stack([0.42 * ring, 0.88 * ring, 1.0 * ring], axis=-1) * (rr <= 1.0)[..., None]

    im_fx = Image.fromarray(np.clip(np.rint(fx * 255.0), 0, 255).astype(np.uint8), "RGB")
    im_fx.save(os.path.join(OUT_DIR, "jw_fx_srgb.png"), "PNG")
    ImageEnhance.Brightness(im_fx).enhance(0.68).save(os.path.join(PROGS, "jw_air_fx.png"), "PNG", optimize=True)

    # 5. Build 256x256 Plush Crimson-Red Felt Fedora + Black Satin Ribbon + White/Gold Feather Texture (progs/jw_air_fedora.png)
    Sf = 256
    vv_f, uu_f = np.meshgrid(np.linspace(0.0, 1.0, Sf), np.linspace(0.0, 1.0, Sf), indexing="ij")
    rng_f = np.random.default_rng(7719)
    wool = np.asarray(
        Image.fromarray((rng_f.random((96, 96)) * 255.0).astype(np.uint8), "L").resize((Sf, Sf), Image.Resampling.BILINEAR),
        dtype=np.float32,
    ) / 255.0
    weave = 0.92 + 0.16 * (wool - 0.5) + 0.03 * np.sin(uu_f * math.pi * 28.0) * np.cos(vv_f * math.pi * 24.0)
    fed_tex = np.zeros((Sf, Sf, 3), dtype=np.float32)

    # Rows 0..0.70 : Rich Velvet Crimson-Red Wool Felt (subtle crown-to-brim tonal richness)
    felt_mask = vv_f < 0.70
    shade_v = 0.86 + 0.22 * np.sin(np.clip(vv_f / 0.70, 0.0, 1.0) * math.pi)
    crimson = np.stack([
        np.clip(0.86 * weave * shade_v, 0.0, 1.0),
        np.clip(0.09 * weave * shade_v, 0.0, 1.0),
        np.clip(0.12 * weave * shade_v, 0.0, 1.0),
    ], axis=-1)
    fed_tex[felt_mask] = crimson[felt_mask]

    # Rows 0.70..0.88 : Sleek Midnight-Black Grosgrain Silk Hatband Ribbon (subtle horizontal ribbing + sheen)
    rib_mask = (vv_f >= 0.70) & (vv_f < 0.88)
    rib_sheen = 0.11 + 0.08 * (np.sin(uu_f * math.pi * 4.0) ** 2) + 0.03 * np.sin(vv_f * math.pi * 90.0)
    ribbon = np.stack([rib_sheen * 1.05, rib_sheen * 0.95, rib_sheen * 1.12], axis=-1)
    fed_tex[rib_mask] = ribbon[rib_mask]

    # Rows 0.88..1.00 : Crisp Ivory/Gold Press-Feather & Hatband Accent Strip
    fth_mask = vv_f >= 0.88
    fth_barbs = 0.88 + 0.12 * np.sin((uu_f + vv_f * 2.0) * math.pi * 40.0)
    feather = np.stack([0.98 * fth_barbs, 0.93 * fth_barbs, 0.78 * fth_barbs], axis=-1)
    fed_tex[fth_mask] = feather[fth_mask]

    im_fed = Image.fromarray(np.clip(np.rint(fed_tex * 255.0), 0, 255).astype(np.uint8), "RGB")
    im_fed.save(os.path.join(OUT_DIR, "jw_fedora_srgb.png"), "PNG")
    ImageEnhance.Brightness(im_fed).enhance(0.74).save(os.path.join(PROGS, "jw_air_fedora.png"), "PNG", optimize=True)

    return (verts_c, norms_c, uvs_c, tris_c)


def sub_mesh(va, na, ua, ta, mask):
    sel_t = ta[mask]
    used, inv = np.unique(sel_t.ravel(), return_inverse=True)
    return va[used], na[used], ua[used], inv.reshape(-1, 3)


def load_scream_john_and_wave(calm_mesh):
    # 1. Screaming Mane 3D John Wave Head (progs/johnhead3d.md3)
    jm = md3lib.read(os.path.join(PROGS, "johnhead3d.md3"))
    js = jm["surfaces"][0]
    jv = np.asarray(js["frames"][0][0], dtype=np.float32).copy()
    jn = np.asarray(js["frames"][0][1], dtype=np.float32).copy()
    ju = np.asarray(js["st"], dtype=np.float32).copy()
    jt = np.asarray(js["tris"], dtype=np.int32).copy()

    # Add crisp 3D nose-bridge/tip relief (+2.25 in +X) so side profile has a prominent comedic nose!
    w_nose = smoothstep01((jv[:, 0] - 7.4) / 3.2) * np.exp(
        -((jv[:, 1] / 1.70) ** 2 + ((jv[:, 2] - 0.55) / 2.20) ** 2)
    )
    w_brow = smoothstep01((jv[:, 0] - 7.8) / 2.8) * np.exp(
        -((jv[:, 1] / 3.40) ** 2 + ((jv[:, 2] - 2.65) / 1.15) ** 2)
    )
    jv[:, 0] += 2.25 * w_nose + 0.55 * w_brow

    # Flare his wind-whipped outer locks slightly wider (from +-13.0 to +-15.4) for glorious hair-wingspan!
    w_mane = smoothstep01((np.abs(jv[:, 1]) - 5.2) / 6.8)
    jv[:, 1] += np.sign(jv[:, 1]) * 2.40 * w_mane

    # Split cleanly at y=0 into port (>=0) and starboard (<0) halves (~2420 verts each << 4096!)
    tri_y = jv[jt].mean(axis=1)[:, 1]
    scream_l = sub_mesh(jv, jn, ju, jt, tri_y >= 0.0)
    scream_r = sub_mesh(jv, jn, ju, jt, tri_y < 0.0)

    # 2. Tidal-Wave Ring Mesh (progs/jw_wave.md3)
    wm = md3lib.read(os.path.join(PROGS, "jw_wave.md3"))
    ws = wm["surfaces"][0]
    wave_mesh = (
        np.asarray(ws["frames"][0][0], dtype=np.float32),
        np.asarray(ws["frames"][0][1], dtype=np.float32),
        np.asarray(ws["st"], dtype=np.float32),
        np.asarray(ws["tris"], dtype=np.int32),
    )

    # 3. Mega-Man Payload Parts (full 32-seg hero + 20-seg secondary wheels)
    mm_hero = mmg.build_megaman_payload_parts()
    mm_lite = build_wheel_pair_custom(segs=20)

    return dict(
        scream_l=scream_l,
        scream_r=scream_r,
        calm=calm_mesh,
        wave=wave_mesh,
        mm_hero=mm_hero,
        mm_lite=mm_lite,
    )


# --------------------------------------------------------------------------- Comedy Deformers for John Wave Heads
def deform_scream_john(verts0, norms0, hair_flap_deg=0.0, hair_wave_phase=0.0, hair_wave_amp=0.0,
                       hair_sweep_deg=0.0, jaw_open=0.0, gforce_stretch=0.0):
    """Animates Screaming John's:
      1. Unhinged cartoon Pac-Man / screaming lower jaw & beard (x > 1.0, z < -1.6, |y| < 5.8)
      2. G-force cheek/lip slipstream stretch during Mach-5 Afterburner Scream
      3. Flapping shampoo-commercial side hair-mane wings + traveling sinusoidal 'John Wave' hair ripple!
    """
    v = verts0.copy()
    n = norms0.copy()

    # 1. Cartoon Jaw Chomp & Unhinged Scream
    if abs(jaw_open) > 1e-4:
        jw = (
            smoothstep01((v[:, 0] - 0.8) / 5.5)
            * smoothstep01((-1.5 - v[:, 2]) / 3.6)
            * smoothstep01((5.9 - np.abs(v[:, 1])) / 2.2)
        )
        v[:, 2] -= float(jaw_open) * jw
        v[:, 0] -= float(jaw_open) * 0.18 * jw

    # 2. Mach-5 G-force cheek/brow peel-back while nose stays piercing forward
    if abs(gforce_stretch) > 1e-4:
        cheek_w = smoothstep01((np.abs(v[:, 1]) - 1.4) / 3.5) * smoothstep01((5.5 - np.abs(v[:, 1])) / 2.0)
        v[:, 0] -= float(gforce_stretch) * cheek_w
        # Pop eyes slightly forward in shock!
        eye_w = smoothstep01((v[:, 0] - 7.5) / 2.5) * np.exp(-(((np.abs(v[:, 1]) - 2.3) / 1.2) ** 2 + ((v[:, 2] - 1.8) / 1.1) ** 2))
        v[:, 0] += float(gforce_stretch) * 0.85 * eye_w

    # 3. Shampoo-Commercial Hair-Wing Flap + Traveling Wave Ripple (|y| > 4.5 out to 15.4)
    ay = np.abs(v[:, 1])
    lat = np.clip((ay - 4.5) / 10.9, 0.0, 1.0)
    mask = lat > 1e-4
    if np.any(mask):
        lm = lat[mask]
        w_flap = smoothstep01(lm / 0.24) * (0.40 + 0.60 * (lm ** 0.80))
        sgn = np.sign(v[mask, 1])

        piv_y = sgn * 4.6
        piv_z = 0.55
        dx = v[mask, 0] + 0.5
        dy = v[mask, 1] - piv_y
        dz = v[mask, 2] - piv_z

        # Traveling shampoo-wave ripple along hair span!
        if abs(hair_wave_amp) > 1e-4:
            dz = dz + float(hair_wave_amp) * (lm ** 0.85) * np.sin(lm * 4.8 - float(hair_wave_phase))

        # Aft wing sweep around Z
        sw_r = np.radians(hair_sweep_deg) * w_flap * (-sgn)
        cs, ss = np.cos(sw_r), np.sin(sw_r)
        dx1 = dx * cs - dy * ss
        dy1 = dx * ss + dy * cs
        nx1 = n[mask, 0] * cs - n[mask, 1] * ss
        ny1 = n[mask, 0] * ss + n[mask, 1] * cs
        nz1 = n[mask, 2].copy()

        # Ornithopter dihedral flap around X (+hair_flap_deg lifts BOTH hair-wings UP +Z!)
        fl_r = np.radians(hair_flap_deg) * w_flap * sgn
        cf, sf = np.cos(fl_r), np.sin(fl_r)
        dy2 = dy1 * cf - dz * sf
        dz2 = dy1 * sf + dz * cf
        ny2 = ny1 * cf - nz1 * sf
        nz2 = ny1 * sf + nz1 * cf

        v[mask, 0] = dx1 - 0.5
        v[mask, 1] = piv_y + dy2
        v[mask, 2] = piv_z + dz2
        n[mask, 0] = nx1
        n[mask, 1] = ny2
        n[mask, 2] = nz2

    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8)
    return v, n


def deform_calm_john(verts0, norms0, beard_wag=0.0, hair_ripple=0.0, phase=0.0,
                     cigar_puff=0.0, cheek_puff=0.0, brow_cock=0.0):
    """Expressive deadpan comedy deformer:
      - Skeptical 'People's Eyebrow' arch on left brow + subtle squint on monocled right brow
      - Bullfrog / Dizzy-Gillespie cheek inflation in sync with cigar smoke-ring puffs
      - Rhythmic lower-jaw stogie chew + beard wag + slipstream hair ripple while eyes stay stone-cold stoic!
    """
    v = verts0.copy()
    n = norms0.copy()
    if abs(beard_wag) > 1e-4:
        bw = smoothstep01((-2.5 - v[:, 2]) / 7.5)
        v[:, 1] += float(beard_wag) * bw
        v[:, 0] += abs(float(beard_wag)) * 0.15 * bw
    if abs(cigar_puff) > 1e-4:
        cw = smoothstep01((v[:, 0] - 2.5) / 4.5) * smoothstep01((-2.6 - v[:, 2]) / 4.2)
        v[:, 2] -= float(cigar_puff) * 0.48 * cw
        v[:, 0] += float(cigar_puff) * 0.20 * cw
    if abs(cheek_puff) > 1e-4:
        # Balloon both cheeks outward & forward like a cartoon bullfrog blowing smoke rings!
        ch_y = smoothstep01((np.abs(v[:, 1]) - 1.5) / 2.2) * smoothstep01((6.8 - np.abs(v[:, 1])) / 2.0)
        ch_z = smoothstep01((v[:, 2] + 4.4) / 2.0) * smoothstep01((0.6 - v[:, 2]) / 1.8)
        ch_x = smoothstep01((v[:, 0] - 2.0) / 4.0)
        ch_w = ch_y * ch_z * ch_x
        v[:, 1] += np.sign(v[:, 1]) * float(cheek_puff) * 1.65 * ch_w
        v[:, 0] += float(cheek_puff) * 0.75 * ch_w
        v[:, 2] -= float(cheek_puff) * 0.20 * ch_w
    if abs(brow_cock) > 1e-4:
        # Cock left (+Y) eyebrow sky-high ('The Rock' skeptical stare) & squint right (-Y) monocle brow!
        br_x = smoothstep01((v[:, 0] - 4.8) / 2.8)
        br_z = smoothstep01((v[:, 2] - 1.6) / 1.4) * smoothstep01((5.4 - v[:, 2]) / 1.8)
        br_l = br_x * br_z * smoothstep01((v[:, 1] - 0.4) / 1.8) * smoothstep01((5.4 - v[:, 1]) / 1.6)
        br_r = br_x * br_z * smoothstep01((-0.4 - v[:, 1]) / 1.8) * smoothstep01((5.4 + v[:, 1]) / 1.6)
        v[:, 2] += float(brow_cock) * 1.55 * br_l - float(brow_cock) * 0.35 * br_r
        v[:, 0] += float(brow_cock) * 0.35 * br_l
    if abs(hair_ripple) > 1e-4:
        hw = smoothstep01((v[:, 2] - 3.5) / 6.0) + 0.65 * smoothstep01((np.abs(v[:, 1]) - 6.0) / 2.2) * smoothstep01((4.0 - v[:, 0]) / 6.0)
        hw = np.clip(hw, 0.0, 1.0)
        rip = float(hair_ripple) * hw * np.sin(v[:, 1] * 0.55 + v[:, 0] * 0.35 - float(phase))
        v[:, 1] += rip * 0.65
        v[:, 2] += rip * 0.45
    return v, n


# --------------------------------------------------------------------------- FX & Chrome Structural Helpers
def make_plume_cone_arrays(p0, axis_dir, radius, length, uv_quad="cyan"):
    uv_map = {
        "cyan":    (0.02, 0.02, 0.48, 0.48),
        "magenta": (0.52, 0.02, 0.98, 0.48),
        "amber":   (0.02, 0.52, 0.48, 0.98),
    }
    u0, v0, u1, v1 = uv_map[uv_quad]
    mp = mmg.MeshPart("fx")
    mp.add_lathe(
        tuple(p0), tuple(axis_dir),
        [(0.0, radius * 0.55, 0.02), (length * 0.18, radius, 0.16),
         (length * 0.55, radius * 0.68, 0.55), (length, 0.02, 0.98)],
        segs=14, uv_rect=(u0, v0, u1, v1),
    )
    mp.add_lathe(
        tuple(p0), tuple(axis_dir),
        [(0.0, radius * 0.30, 0.01), (length * 0.34, radius * 0.46, 0.22), (length * 0.72, 0.01, 0.85)],
        segs=10, uv_rect=(u0, v0, u1, v1),
    )
    return (
        np.asarray(mp.verts, dtype=np.float32),
        np.asarray(mp.norms, dtype=np.float32),
        np.asarray(mp.st, dtype=np.float32),
        np.asarray(mp.tris, dtype=np.int32),
    )


def make_rotor_disc_arrays(center, normal_axis, r_inner, r_outer):
    mp = mmg.MeshPart("fx")
    mp.add_lathe(
        tuple(center), tuple(normal_axis),
        [(-0.2, r_inner, 0.58, r_outer), (0.0, 0.5 * (r_inner + r_outer), 0.78, r_outer),
         (+0.2, r_outer, 0.98, r_outer), (-0.2, r_inner, 0.58, r_outer)],
        segs=24, uv_mode="polar", uv_rect=(0.52, 0.52, 0.98, 0.98),
    )
    return (
        np.asarray(mp.verts, dtype=np.float32),
        np.asarray(mp.norms, dtype=np.float32),
        np.asarray(mp.st, dtype=np.float32),
        np.asarray(mp.tris, dtype=np.int32),
    )


def make_thruster_bell_part(p0, axis_dir, r_base, r_exit, length):
    mp = mmg.MeshPart("chrome_axle")
    mp.add_lathe(
        tuple(p0), tuple(axis_dir),
        [(0.0, 0.0, 0.05), (0.0, r_base * 0.88, 0.12), (length * 0.22, r_base, 0.28),
         (length * 0.30, r_base * 0.78, 0.38), (length * 0.60, r_exit * 0.88, 0.66),
         (length, r_exit, 0.96), (length, r_exit * 0.86, 0.98),
         (length * 0.35, r_base * 0.55, 0.50), (length * 0.35, 0.0, 0.45)],
        segs=18, uv_rect=(0.04, 0.54, 0.46, 0.96),
    )
    return mp


# --------------------------------------------------------------------------- 72-Frame Seamless Flight & Stunt Kinematics
def frame_kinematics(fi):
    """Seamless loop kinematics across all 5 Quake animation clips (72 frames total)."""
    if fi < 16:
        # Clip 0: fly_cruise (0..15) — Shampoo-Wave Cruise & Rhythmic Jaw-Chomp
        p = fi / 16.0
        tau = 2.0 * math.pi * p
        return dict(
            mode="cruise", p=p, tau=tau,
            alt_z=22.0 + 4.2 * math.sin(tau),
            surge_x=1.8 * math.sin(tau),
            sway_y=2.8 * math.cos(tau),
            hull_roll=5.5 * math.cos(tau),
            hull_pitch=2.5 + 2.8 * math.sin(tau),
            hull_yaw=2.2 * math.sin(tau),
            hair_flap=24.0 * math.sin(tau),
            hair_wave_phase=2.0 * tau,
            hair_wave_amp=1.35,
            hair_sweep=6.0 + 5.0 * math.cos(tau),
            jaw_open=1.45 + 1.35 * math.sin(2.0 * tau),  # 2 enthusiastic YAK-YAK chomps per cycle!
            gforce=0.0,
            prop_spin=(p * 720.0),       # 2 full revolutions
            rotor_spin=(p * 720.0),      # 2 full revolutions
            wheel_roll=(p * 360.0),
            tilt_fwd_deg=0.0,            # 0 = forward tractor prop, +72 = tilted up VTOL
            gear_tuck=1.0,
            plume_scale=1.0 + 0.16 * math.sin(2.0 * tau),
            wave_spin=(p * 720.0),
            calm_yaw=20.0 * math.sin(tau),
            calm_pitch=4.0 * math.cos(tau),
            beard_wag=0.65 * math.sin(2.0 * tau),
        )
    elif fi < 32:
        # Clip 1: fly_boost (16..31) — MAXIMUM OVERBITE Mach-5 Afterburner Scream!
        p = (fi - 16) / 16.0
        tau = 2.0 * math.pi * p
        return dict(
            mode="boost", p=p, tau=tau,
            alt_z=24.0 + 2.2 * math.sin(2.0 * tau),
            surge_x=7.5 + 3.0 * math.sin(2.0 * tau),
            sway_y=1.6 * math.cos(2.0 * tau),
            hull_roll=4.5 * math.sin(2.0 * tau),
            hull_pitch=-9.5 + 2.0 * math.cos(2.0 * tau),
            hull_yaw=1.2 * math.sin(2.0 * tau),
            hair_flap=16.0 * math.sin(2.0 * tau),
            hair_wave_phase=4.0 * tau,
            hair_wave_amp=1.85,
            hair_sweep=26.0 + 5.0 * math.cos(2.0 * tau),
            jaw_open=3.85 + 0.65 * math.sin(4.0 * tau),  # UNHINGED MAX SCREAM!
            gforce=1.35 + 0.25 * math.sin(4.0 * tau),
            prop_spin=(p * 1080.0),      # 3 full supersonic turns!
            rotor_spin=(p * 1080.0),
            wheel_roll=(p * 720.0),
            tilt_fwd_deg=-6.0,
            gear_tuck=1.0,
            plume_scale=1.85 + 0.28 * math.sin(4.0 * tau),
            wave_spin=(p * 1440.0),
            calm_yaw=8.0 * math.sin(2.0 * tau),
            calm_pitch=-6.0,
            beard_wag=1.15 * math.sin(4.0 * tau),
        )
    elif fi < 44:
        # Clip 2: fly_hover (32..43) — Buoyant Hair-Sculling VTOL Hover
        p = (fi - 32) / 12.0
        tau = 2.0 * math.pi * p
        return dict(
            mode="hover", p=p, tau=tau,
            alt_z=18.0 + 6.0 * math.sin(tau),
            surge_x=0.8 * math.cos(tau),
            sway_y=1.8 * math.sin(tau),
            hull_roll=3.2 * math.sin(tau),
            hull_pitch=5.5 + 2.2 * math.cos(tau),
            hull_yaw=3.5 * math.sin(tau),
            hair_flap=6.0 + 18.0 * math.sin(tau),
            hair_wave_phase=tau,
            hair_wave_amp=1.10,
            hair_sweep=4.0 * math.cos(tau),
            jaw_open=1.20 + 0.85 * math.sin(tau),
            gforce=0.0,
            prop_spin=(p * 720.0),
            rotor_spin=(p * 720.0),
            wheel_roll=(p * 360.0),
            tilt_fwd_deg=72.0,           # Tilts props/headphones UP for VTOL downdraft!
            gear_tuck=0.5,
            plume_scale=0.85 + 0.15 * math.cos(tau),
            wave_spin=(p * 720.0),
            calm_yaw=26.0 * math.sin(tau),
            calm_pitch=5.0 * math.sin(tau),
            beard_wag=0.45 * math.cos(tau),
        )
    elif fi < 56:
        # Clip 3: lie_rest (44..55) — Parked / Lying on Runway z=0 (Snoring Idle)
        p = (fi - 44) / 12.0
        tau = 2.0 * math.pi * p
        return dict(
            mode="lie", p=p, tau=tau,
            alt_z=0.0,
            surge_x=0.0,
            sway_y=0.0,
            hull_roll=0.0,
            hull_pitch=0.0,
            hull_yaw=0.0,
            hair_flap=-30.0 + 2.2 * math.sin(tau),  # Sleepily drooped hair-wings!
            hair_wave_phase=tau,
            hair_wave_amp=0.20,
            hair_sweep=3.0,
            jaw_open=0.55 + 0.55 * math.sin(tau),   # Gentle snoring breath!
            gforce=0.0,
            prop_spin=12.0 * math.sin(tau),         # Breeze windmilling idle
            rotor_spin=8.0 * math.sin(tau),
            wheel_roll=0.0,
            tilt_fwd_deg=0.0,
            gear_tuck=0.0,
            plume_scale=0.04,
            wave_spin=(p * 360.0),
            calm_yaw=6.0 * math.sin(tau),
            calm_pitch=8.0,
            beard_wag=0.15 * math.sin(tau),
        )
    else:
        # Clip 4: fly_barrel_roll (56..71) — Full 360-Degree Aileron Barrel-Roll Stunt!
        p = (fi - 56) / 16.0
        tau = 2.0 * math.pi * p
        return dict(
            mode="roll", p=p, tau=tau,
            alt_z=24.0 + 9.0 * math.sin(tau),
            surge_x=3.5 * math.sin(tau),
            sway_y=-9.0 * (1.0 - math.cos(tau)),
            hull_roll=p * 360.0,                    # Full 360 deg barrel roll!
            hull_pitch=3.5 * math.sin(tau),
            hull_yaw=4.0 * math.cos(tau),
            hair_flap=14.0 + 14.0 * math.sin(2.0 * tau),
            hair_wave_phase=3.0 * tau,
            hair_wave_amp=1.60,
            hair_sweep=14.0,
            jaw_open=2.60 + 1.10 * math.sin(3.0 * tau),
            gforce=0.65,
            prop_spin=(p * 1080.0),
            rotor_spin=(p * 1080.0),
            wheel_roll=(p * 720.0),
            tilt_fwd_deg=0.0,
            gear_tuck=1.0,
            plume_scale=1.55 + 0.20 * math.sin(2.0 * tau),
            wave_spin=(p * 1080.0),
            calm_yaw=-25.0 * math.sin(tau),
            calm_pitch=0.0,
            beard_wag=0.95 * math.cos(2.0 * tau),
        )


# --------------------------------------------------------------------------- Static Airframe Chrome Hardware per Variant
def build_static_chrome_airframe(vid):
    mp = mmg.MeshPart("chrome_axle")
    uv_chr = (0.52, 0.04, 0.96, 0.46)
    uv_dk = (0.04, 0.54, 0.46, 0.96)
    uv_gld = (0.76, 0.52, 0.98, 0.73)

    if vid == "v1":
        # V1 uses fully articulated dynamic sub-assemblies (bobblehead spring + flapping biplane wings + cuckoo boom)!
        pass

    elif vid == "v2":
        # SR-99 "IN-ONE-EAR":
        # 1. Giant Chrome "Beats-By-Mega-Man" Headphone Arch over Giant John's Crown connecting L & R Ear Tilt-Rotors!
        arch_pts = []
        for k in range(13):
            ang = math.radians(-90.0 + 180.0 * (k / 12.0))
            arch_pts.append((12.0 - 4.0 * math.cos(ang), 66.0 * math.sin(ang), 62.0 + 54.0 * math.cos(ang)))
        mp.add_tube(arch_pts, [3.2] * len(arch_pts), segs=10, uv_rect=uv_chr)
        # Padded headphone ear-cup collars on temples
        for sy in (-1.0, 1.0):
            mp.add_lathe((12.0, sy * 48.0, 60.0), (0.0, sy, 0.0),
                         [(0.0, 14.0, 0.2), (8.0, 16.5, 0.6), (12.0, 11.0, 0.9), (12.0, 0.0, 0.95)],
                         segs=16, uv_rect=uv_dk)

        # 2. Swept Supersonic Chrome Delta-Wings + Underwing Screaming-John Ramjet Pylons & Chrome Mouth Intakes!
        for sy in (-1.0, 1.0):
            mp.add_tube([(4.0, sy * 18.0, 52.0), (-26.0, sy * 62.0, 48.0), (-48.0, sy * 98.0, 46.0)],
                        [(8.5, 2.4), (6.5, 2.0), (4.0, 1.4)], segs=10, uv_rect=uv_chr)
            mp.add_tube([(-28.0, sy * 16.0, 50.0), (-44.0, sy * 62.0, 47.0), (-56.0, sy * 98.0, 46.0)],
                        [(7.5, 2.2), (5.5, 1.8), (3.5, 1.2)], segs=10, uv_rect=uv_chr)
            # Underwing pylon + chrome ramjet lip around underwing screaming head's mouth + rear nozzle
            mp.add_chamfer_box(-28.0, -6.0, sy * 56.0 - 1.8, sy * 56.0 + 1.8, 36.0, 48.0, ch=0.6, uv_rect=uv_dk)
            mp.append_part(make_thruster_bell_part((-40.0, sy * 58.0, 32.0), (-1.0, 0.0, 0.0), 7.5, 11.0, 13.0))

        # 3. Twin Supersonic Afterburner Bells + Tail-Gunner Tub + Rear Tailwheel Strut
        for sy in (-1.0, 1.0):
            mp.append_part(make_thruster_bell_part((-74.0, sy * 11.0, 39.0), (-1.0, 0.0, 0.0), 8.5, 13.0, 18.0))
            # Twin canted vertical tailfins flanking Deadpan Tail-Gunner
            mp.add_tube([(-46.0, sy * 14.0, 58.0), (-72.0, sy * 22.0, 96.0)], [(7.0, 1.5), (4.0, 1.1)], segs=8, uv_rect=uv_chr)
        mp.add_lathe((-52.0, 0.0, 68.0), (0.0, 0.0, 1.0),
                     [(0.0, 13.0, 0.1), (5.5, 14.0, 0.6), (6.5, 11.5, 0.9)], segs=16, uv_rect=uv_dk)
        mp.add_tube([(-64.0, 0.0, 42.0), (-76.0, 0.0, 28.5)], [2.4, 1.8], segs=8, uv_rect=uv_chr)

    else:
        # CH-99 "THE HAIR-ICOPTER" (100% Screaming-Head-Free! Triple Stoic Deadpan Lush-Hair Johns!):
        # 1. Colorful Striped Gold/Chrome Propeller-Beanie Cap Domes atop BOTH Giant Deadpan Heads!
        for bx, bz, br in ((52.0, 108.0, 21.0), (-54.0, 105.0, 19.8)):
            mp.add_lathe((bx, 0.0, bz), (0.0, 0.0, 1.0),
                         [(0.0, br, 0.15), (4.5, br * 0.92, 0.45), (9.5, br * 0.62, 0.78),
                          (12.5, 5.0, 0.95), (12.5, 0.0, 0.98)],
                         segs=18, uv_rect=uv_gld)

        # 2. Midship Chrome Motorcycle Saddle + Tall Ape-Hanger Handlebars for Stoic Biker Mini-John!
        mp.add_chamfer_box(-14.0, 12.0, -9.5, 9.5, 45.0, 56.0, ch=2.2, uv_rect=uv_dk)
        for sy in (-1.0, 1.0):
            mp.add_tube([(14.0, sy * 4.0, 48.0), (18.0, sy * 15.0, 76.0), (13.0, sy * 23.0, 82.0)],
                        [1.35, 1.25, 1.45], segs=8, uv_rect=uv_chr)
            # Midship outrigger sponson pylons
            mp.add_tube([(0.0, sy * 8.0, 42.0), (0.0, sy * 28.0, 44.0)], [2.2, 2.0], segs=8, uv_rect=uv_chr)

        # 3. Chinook Pontoon Outrigger Struts + Twin Rear Hydro-Jet Exhaust Pipes (below Rear Deadpan John's chin!)
        for x_ax in (50.0, -50.0):
            for sy in (-1.0, 1.0):
                mp.add_tube([(x_ax, sy * 6.0, 39.0), (x_ax, sy * 38.0, 18.0)], [2.1, 1.7], segs=8, uv_rect=uv_chr)
        for sy in (-1.0, 1.0):
            mp.add_tube([(-58.0, sy * 8.0, 38.0), (-76.0, sy * 19.0, 30.0)], [3.2, 4.2], segs=8, uv_rect=uv_chr)
            mp.append_part(make_thruster_bell_part((-76.0, sy * 19.0, 30.0), (-1.0, 0.0, 0.0), 7.5, 11.5, 16.0))

    return mp


def build_fedora_mesh():
    """Builds a sculpted 1930s Crimson-Red Felt Fedora in unit calm_v head coordinates (scale=1.0):
      - Classic front dipped snap-brim (+X) & upturned curled side/rear welt brim
      - Proud Midnight-Black grosgrain silk hatband ribbon around the crown base + jaunty side feather
      - Authentic twin front thumb-pinches & lengthwise teardrop center crown valley crease (safely above z=+11.0 hair!)
    """
    N_th = 36
    cols = N_th + 1
    x_cen = -0.25
    z_base = 6.30
    rx0, ry0 = 8.55, 7.95
    rx_b, ry_b = 13.90, 12.25

    def brim_dz(s, c, sn):
        # Front (+X) snaps stylishly downward; sides & back curl jauntily upward!
        dip_fwd = -1.42 * (s ** 1.45) * (max(0.0, c) ** 1.35)
        curl_up = +1.38 * (s ** 1.55) * (0.82 * (sn * sn) + 0.88 * (max(0.0, -c) ** 1.25))
        welt = +0.26 * smoothstep01((s - 0.82) / 0.18)
        return dip_fwd + curl_up + welt

    def crown_pt(u_h, rho, th):
        """u_h in [0..1] along outer wall, rho in [1..0] across top crown to center valley."""
        c, sn = math.cos(th), math.sin(th)
        taper = 1.0 - 0.16 * u_h
        # Twin front-cheek thumb pinches (classic Bogart / Dick Tracy fedora wedge!)
        pinch_ang = (max(0.0, c) ** 1.35) * (0.72 * (math.sin(2.0 * th) ** 2) + 0.28 * (sn * sn))
        pinch = 0.27 * math.sin(math.pi * min(1.0, u_h * 0.92)) * pinch_ang
        rx = rx0 * taper * (1.0 + 0.04 * u_h * max(0.0, c)) * rho
        ry = ry0 * taper * (1.0 - pinch) * rho

        # Side ridges peak at z=14.95 while center lengthwise valley crease dips to z=12.40 (> +11.0 top hair!)
        wall_z = z_base + u_h * 8.15
        ridge_boost = 0.65 * (sn * sn) * smoothstep01((u_h - 0.55) / 0.45)
        dent_depth = 2.45 * (1.0 - rho * rho) * (1.0 - 0.25 * (c * c))
        rim_lip = 0.32 * math.sin(math.pi * np.clip((rho - 0.62) / 0.38, 0.0, 1.0)) if rho < 0.999 else 0.0
        z = wall_z + ridge_boost * rho + rim_lip - dent_depth
        return (x_cen + rx * c, ry * sn, z)

    # Ring schedule: (point_fn, uv_v) from under-brim inner -> outer rim -> top-brim -> ribbon -> crown wall -> top crease
    ring_specs = []
    # 1) Under-brim (s: 0.0 -> 1.0)
    for s, uv_v in ((0.0, 0.62), (0.38, 0.54), (0.76, 0.46), (1.00, 0.38)):
        ring_specs.append((lambda th, s=s: (
            x_cen + (rx0 + (rx_b - rx0) * s) * math.cos(th),
            (ry0 + (ry_b - ry0) * s) * math.sin(th),
            z_base - 0.28 + brim_dz(s, math.cos(th), math.sin(th)),
        ), uv_v))
    # 2) Rolled outer brim edge & upper brim (s: 1.0 -> 0.02)
    ring_specs.append((lambda th: (
        x_cen + (rx_b + 0.18) * math.cos(th),
        (ry_b + 0.18) * math.sin(th),
        z_base - 0.04 + brim_dz(1.0, math.cos(th), math.sin(th)),
    ), 0.34))
    for s, uv_v in ((1.00, 0.30), (0.72, 0.42), (0.36, 0.54), (0.03, 0.66)):
        ring_specs.append((lambda th, s=s: (
            x_cen + (rx0 + (rx_b - rx0) * s) * math.cos(th),
            (ry0 + (ry_b - ry0) * s) * math.sin(th),
            z_base + 0.14 + brim_dz(s, math.cos(th), math.sin(th)),
        ), uv_v))
    # 3) Proud Black Grosgrain Silk Hatband Ribbon (u_h: 0.02 -> 0.22, extruded 1.03x proud!)
    for u_h, rad_m, uv_v in ((0.02, 1.032, 0.72), (0.12, 1.035, 0.79), (0.22, 1.032, 0.86), (0.225, 1.000, 0.65)):
        ring_specs.append((lambda th, u_h=u_h, rad_m=rad_m: (
            x_cen + (crown_pt(u_h, 1.0, th)[0] - x_cen) * rad_m,
            crown_pt(u_h, 1.0, th)[1] * rad_m,
            crown_pt(u_h, 1.0, th)[2],
        ), uv_v))
    # 4) Sculpted Pinched Crimson Felt Crown Wall & Creased Teardrop Top
    for u_h, uv_v in ((0.42, 0.52), (0.64, 0.40), (0.84, 0.28), (1.00, 0.18)):
        ring_specs.append((lambda th, u_h=u_h: crown_pt(u_h, 1.0, th), uv_v))
    for rho, uv_v in ((0.82, 0.13), (0.52, 0.09), (0.22, 0.06)):
        ring_specs.append((lambda th, rho=rho: crown_pt(1.0, rho, th), uv_v))

    verts, uvs, tris = [], [], []
    n_rings = len(ring_specs)
    for r_i, (fn_pt, uv_v) in enumerate(ring_specs):
        for k in range(cols):
            th = 2.0 * math.pi * (k / float(N_th))
            verts.append(fn_pt(th))
            uvs.append((k / float(N_th), uv_v))

    i_top = len(verts)
    verts.append(crown_pt(1.0, 0.0, 0.0))
    uvs.append((0.5, 0.03))

    for r_i in range(n_rings - 1):
        for k in range(N_th):
            a = r_i * cols + k
            b = a + 1
            d = (r_i + 1) * cols + k
            c = d + 1
            tris.append((a, b, c))
            tris.append((a, c, d))
    top_row = (n_rings - 1) * cols
    for k in range(N_th):
        tris.append((top_row + k, top_row + k + 1, i_top))

    # Add a jaunty Ivory Feather tucked into the Left (+Y) Hatband Ribbon!
    f_pts = [
        (x_cen + 1.8, ry0 * 0.99, z_base + 0.9),
        (x_cen + 0.2, ry0 * 1.05, z_base + 2.8),
        (x_cen - 2.2, ry0 * 1.10, z_base + 5.2),
        (x_cen - 4.8, ry0 * 1.12, z_base + 7.4),
    ]
    f_w = [(0.12, 0.45), (0.16, 0.95), (0.14, 0.78), (0.06, 0.18)]
    mp_fth = mmg.MeshPart("fedora")
    mp_fth.add_tube(f_pts, f_w, segs=6, uv_rect=(0.05, 0.90, 0.95, 0.99))

    va = np.asarray(verts, dtype=np.float32)
    ua = np.asarray(uvs, dtype=np.float32)
    ta = np.asarray(tris, dtype=np.int32)
    na = np.zeros_like(va)
    fn_all = np.cross(va[ta[:, 1]] - va[ta[:, 0]], va[ta[:, 2]] - va[ta[:, 0]])
    # Ensure crown top pole normal points +Z!
    if fn_all[-1, 2] < 0.0:
        ta = ta[:, [0, 2, 1]]
        fn_all = -fn_all
    for ci in range(3):
        np.add.at(na, ta[:, ci], fn_all)
    for r_i in range(n_rings):
        i0, i1 = r_i * cols, r_i * cols + N_th
        sn_w = na[i0] + na[i1]
        na[i0], na[i1] = sn_w, sn_w
    na /= np.maximum(np.linalg.norm(na, axis=1, keepdims=True), 1e-8)

    # Merge feather onto fedora arrays
    fv = np.asarray(mp_fth.verts, dtype=np.float32)
    fn_m = np.asarray(mp_fth.norms, dtype=np.float32)
    fu = np.asarray(mp_fth.st, dtype=np.float32)
    ft = np.asarray(mp_fth.tris, dtype=np.int32) + len(va)
    return (
        np.vstack([va, fv]),
        np.vstack([na, fn_m]),
        np.vstack([ua, fu]),
        np.vstack([ta, ft]),
    )


def build_v1_subassemblies():
    """Pre-builds rigid comedy sub-assemblies for V1 F-69 'The Mouth-Breather' (100% Screaming-Head-Free!)."""
    uv_chr = (0.52, 0.04, 0.96, 0.46)
    uv_dk = (0.04, 0.54, 0.46, 0.96)
    uv_gld = (0.76, 0.52, 0.98, 0.73)

    # 1. Head-Local Hardware on Giant Bobblehead John (origin = Giant John head center, jh_sc = 4.65):
    head_hw = mmg.MeshPart("chrome_axle")
    # 1a. Giant 24k-Gold Monocle Bezel over Right Eye (-Y) + Dangling Catenary Gold Monocle Chain to Right Ear!
    head_hw.add_lathe(
        (41.6, -13.5, 5.6), (0.98, -0.20, 0.0),
        [(-1.4, 6.8, 0.12), (-1.4, 9.8, 0.38), (1.5, 9.8, 0.65), (1.5, 6.8, 0.90), (-1.4, 6.8, 0.12)],
        segs=18, uv_rect=uv_gld,
    )
    head_hw.add_tube(
        [(40.5, -22.2, 1.8), (35.0, -30.5, -10.5), (20.0, -36.8, -13.5), (3.0, -38.2, -2.0)],
        [0.95, 0.90, 0.90, 1.05], segs=7, uv_rect=uv_gld,
    )

    # 1b. Sweeping Curled Gold Salvador-Dali / Walrus Handlebar Mustache!
    for sy in (-1.0, 1.0):
        head_hw.add_tube(
            [(41.8, sy * 1.5, -14.5), (46.0, sy * 18.0, -16.5), (48.8, sy * 38.0, -15.2),
             (49.5, sy * 53.0, -9.5), (50.0, sy * 58.5, -0.5), (50.0, sy * 53.5, +4.8), (50.0, sy * 48.5, +0.5)],
            [3.8, 3.2, 2.5, 1.8, 1.3, 0.9, 0.5], segs=8, uv_rect=uv_gld,
        )
        # Angry-Bull Flared Chrome Nostril Nitrous Snort-Pipes!
        head_hw.add_tube(
            [(36.0, sy * 5.8, -7.8), (43.5, sy * 13.0, -10.5), (48.5, sy * 20.0, -13.2)],
            [1.8, 2.5, 3.7], segs=8, uv_rect=uv_chr,
        )
        # Ear-Level Chrome Trunnion Hinges for Flapping Biplane Wings (wide clear of the Red Fedora brim!)
        head_hw.add_lathe(
            (2.0, sy * 34.0, -4.0), (0.0, sy, 0.0),
            [(0.0, 7.5, 0.2), (5.5, 6.2, 0.7), (6.5, 0.0, 0.95)], segs=12, uv_rect=uv_gld,
        )

    # 1c. 24k-Gold Hatband Buckle on Left (+Y) Side of Giant John's Red Fedora (in Fedora-local scale=1.0 coords!)
    fed_buckle = mmg.MeshPart("chrome_axle")
    fed_buckle.add_chamfer_box(0.8, 2.8, 7.85, 8.35, 6.55, 7.85, ch=0.18, uv_rect=uv_gld)

    # 1d. Rear Cuckoo-Clock Gold Hatch Collar (z=+10) + Lower Skull Tailfin & Tidal-Wave Bell (z=-22)
    head_hw.add_lathe(
        (-36.5, 0.0, 10.0), (-1.0, 0.0, 0.0),
        [(0.0, 11.2, 0.15), (4.5, 12.4, 0.55), (6.0, 9.6, 0.90)], segs=14, uv_rect=uv_gld,
    )
    head_hw.add_tube([(-28.0, 0.0, -17.0), (-64.0, 0.0, -22.0)], [13.0, 13.8], segs=14, uv_rect=uv_dk)
    head_hw.add_chamfer_box(-96.0, -34.0, -2.2, 2.2, -16.0, +2.0, ch=0.8, uv_rect=uv_chr)
    head_hw.append_part(make_thruster_bell_part((-64.0, 0.0, -22.0), (-1.0, 0.0, 0.0), 14.0, 20.5, 22.0))

    # 2. Sculpted Crimson-Red Felt Fedora Mesh (unit head scale=1.0)
    fedora = build_fedora_mesh()

    # 3. Port (+1) & Starboard (-1) Flapping Bird-Wing WWI Biplane Wing Cells (hinge at (2, +-34, -4), clear of Fedora!)
    wings = {}
    for sname, sy in (("l", 1.0), ("r", -1.0)):
        wp = mmg.MeshPart("chrome_axle")
        y0, y1 = min(sy * 25.0, sy * 76.0), max(sy * 25.0, sy * 76.0)
        # Lower & Upper Chrome Biplane Airfoil Panels (start at wy=25 -> |hy|=59, cleanly outside +-56 Fedora brim!)
        wp.add_chamfer_box(-12.0, 14.0, y0, y1, -18.0, -14.8, ch=0.9, uv_rect=uv_chr)
        wp.add_chamfer_box(-13.0, 13.0, y0, y1, +48.0, +51.2, ch=0.9, uv_rect=uv_chr)
        # Gold/Chrome Shoulder V-Spars from Ear Hinge (0,0,0) out to Inner Biplane N-Strut (wy=27)
        wp.add_tube([(6.0, 0.0, 0.0), (8.0, sy * 27.0, -16.2)], [2.3, 1.8], segs=7, uv_rect=uv_gld)
        wp.add_tube([(-6.0, 0.0, 0.0), (-8.0, sy * 27.0, -16.2)], [2.3, 1.8], segs=7, uv_rect=uv_gld)
        wp.add_tube([(0.0, 0.0, 0.0), (0.0, sy * 27.0, +49.0)], [2.2, 1.7], segs=7, uv_rect=uv_chr)
        for wy in (27.0, 62.0):
            wp.add_tube([(8.0, sy * wy, -16.2), (8.0, sy * wy, +49.5)], [1.35, 1.35], segs=7, uv_rect=uv_chr)
            wp.add_tube([(-8.0, sy * wy, -16.2), (-8.0, sy * wy, +49.5)], [1.35, 1.35], segs=7, uv_rect=uv_chr)
            wp.add_tube([(-8.0, sy * wy, -16.2), (8.0, sy * wy, +49.5)], [1.05, 1.05], segs=7, uv_rect=uv_gld)
        wings[sname] = wp

    # 4. Lower Roller-Chassis Strut Truss (relative to gear_dz)
    chassis_hw = mmg.MeshPart("chrome_axle")
    chassis_hw.add_tube([(-16.0, 0.0, 17.5), (6.0, 0.0, 19.0), (48.0, 0.0, 15.2)], [2.6, 3.0, 2.0], segs=8, uv_rect=uv_chr)
    for sy in (-1.0, 1.0):
        chassis_hw.add_tube([(6.0, 0.0, 19.0), (-16.0, sy * 34.0, 17.0)], [2.2, 1.8], segs=8, uv_rect=uv_chr)

    # 5. Gold Cigar Band Ring around Mega-Man Stogie
    cigar_band = mmg.MeshPart("chrome_axle")
    cigar_band.add_lathe(
        (20.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        [(0.0, 2.2, 0.2), (0.0, 3.3, 0.35), (5.5, 3.3, 0.65), (5.5, 2.2, 0.8), (0.0, 2.2, 0.2)],
        segs=14, uv_rect=uv_gld,
    )
    return dict(head_hw=head_hw, fedora=fedora, fed_buckle=fed_buckle, wings=wings, chassis_hw=chassis_hw, cigar_band=cigar_band)


# --------------------------------------------------------------------------- Build One 72-Frame John Wave Aircraft MD3
def build_aircraft_md3(vid, title, assets):
    mm_hero = assets["mm_hero"]
    mm_lite = assets["mm_lite"]
    calm_v, calm_n, calm_u, calm_t = assets["calm"]
    wave_v, wave_n, wave_u, wave_t = assets["wave"]
    airframe_static = build_static_chrome_airframe(vid)
    v1_sub = build_v1_subassemblies() if vid == "v1" else None

    surf_defs = {}
    surf_order = []

    def record_frame(sname, shader, uvs, tris, vv, nn):
        if sname not in surf_defs:
            surf_defs[sname] = dict(
                name=sname,
                shader=shader,
                st=[tuple(map(float, u)) for u in uvs],
                tris=[tuple(map(int, t)) for t in tris],
                frames=[],
            )
            surf_order.append(sname)
        else:
            assert len(vv) == len(surf_defs[sname]["st"]), (
                f"{vid}:{sname} vertex mismatch {len(vv)} vs {len(surf_defs[sname]['st'])}"
            )
        surf_defs[sname]["frames"].append((
            [tuple(map(float, p)) for p in vv],
            [tuple(map(float, n)) for n in nn],
        ))

    for fi in range(TOTAL_FRAMES):
        K = frame_kinematics(fi)
        R_hull = euler_mat(K["hull_roll"], K["hull_pitch"], K["hull_yaw"])
        hull_pivot = np.array([0.0, 0.0, 58.0], dtype=np.float32)
        hull_ofs = np.array([K["surge_x"], K["sway_y"], K["alt_z"]], dtype=np.float32)

        def to_hull(v_arr, n_arr):
            return ((v_arr - hull_pivot) @ R_hull.T) + hull_pivot + hull_ofs, (n_arr @ R_hull.T)

        sb_chr = SurfBuilder("mm_chrome", "progs/jw_air_chrome")
        sb_fed = SurfBuilder("jw_fedora", "progs/jw_air_fedora")
        sb_wa = SurfBuilder("mm_wheels_a", "progs/jw_air_wheel")
        sb_wb = SurfBuilder("mm_wheels_b", "progs/jw_air_wheel")
        sb_surf = SurfBuilder("jw_surf", "progs/jw_air_wave")
        sb_fx = SurfBuilder("thruster_fx", "progs/jw_air_fx")

        if len(airframe_static.verts) > 0:
            sb_chr.add_mesh_part(airframe_static)

        # ===================================================================
        # VARIANT 1: F-69 "THE MOUTH-BREATHER" (100% Screaming-Head-Free! Maximum Slapstick Edition!)
        # ===================================================================
        if vid == "v1":
            tau = K["tau"]
            is_lie = (K["mode"] == "lie")
            is_boost = (K["mode"] == "boost")
            h_rip = 1.25 if not is_lie else 0.20

            # --- A. Roller-Skate Tricycle Landing Gear + Bouncing Gold Bobblehead Neck-Spring! ---
            gear_dz = 5.5 * K["gear_tuck"]
            bob_dz = (1.2 * math.sin(tau)) if is_lie else (4.2 * math.sin(4.0 * tau) if is_boost else 3.2 * math.sin(2.0 * tau))
            sb_chr.add_mesh_part(v1_sub["chassis_hw"], offset=(0.0, 0.0, gear_dz))
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(4.2, 6.2, 4.2), R=None, offset=(-16.0, 0.0, 16.5 + gear_dz))
            R_gspin = rot_y_mat(-K["wheel_roll"])
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                g_pos = (-16.0, sy * mmg.MM_WHEEL_Y * 6.2, 16.5 + gear_dz)
                sb_wb.add_mesh_part(mm_lite[f"wheel_{side_nm}"], scale=4.1, R=R_gspin, offset=g_pos)
                sb_chr.add_mesh_part(mm_lite[f"wheel_hw_{side_nm}"], scale=4.1, R=R_gspin, offset=g_pos)
            sb_wb.add_mesh_part(mm_lite["wheel_l"], scale=3.6, R=R_gspin, offset=(48.0, 0.0, 14.5 + gear_dz))
            sb_chr.add_mesh_part(mm_lite["wheel_hw_l"], scale=3.6, R=R_gspin, offset=(48.0, 0.0, 14.5 + gear_dz))

            # Compressible 24k-Gold Helical Bobblehead Neck-Spring (physically squashes & stretches!)
            sp_z0 = 18.8 + gear_dz
            sp_z1 = 34.5 + bob_dz
            sp_pts = []
            for si in range(29):
                sf = si / 28.0
                ang = sf * 3.5 * 2.0 * math.pi
                sp_pts.append((6.0 + 11.2 * math.cos(ang), 11.2 * math.sin(ang), sp_z0 + sf * (sp_z1 - sp_z0)))
            mp_sp = mmg.MeshPart("chrome_axle")
            mp_sp.add_tube(sp_pts, [2.15] * len(sp_pts), segs=7, uv_rect=(0.76, 0.52, 0.98, 0.73))
            sb_chr.add_mesh_part(mp_sp)

            # --- B. Giant Dashboard-Bobblehead John Coordinate Frame ---
            if is_lie:
                R_bob = euler_mat(3.0 * math.sin(tau), +7.5 + 2.2 * math.sin(tau), 2.5 * math.cos(tau))
            elif is_boost:
                R_bob = euler_mat(8.0 * math.sin(4.0 * tau), -4.5 + 3.5 * math.cos(4.0 * tau), 4.5 * math.sin(2.0 * tau))
            else:
                R_bob = euler_mat(7.0 * math.sin(2.0 * tau), 3.5 * math.cos(2.0 * tau), 6.0 * math.sin(tau))

            bob_piv = np.array([6.0, 0.0, sp_z1], dtype=np.float32)
            head_rel = np.array([0.0, 0.0, 39.5], dtype=np.float32)  # Head center at world ~(6, 0, 74)

            def head_pt(p_loc):
                return bob_piv + ((np.asarray(p_loc, dtype=np.float32) + head_rel) @ R_bob.T)

            def head_vn(va, na, scale=1.0, R_loc=None, ofs_loc=(0.0, 0.0, 0.0)):
                vt, nt = xform_vn(va, na, scale=scale, R=R_loc, offset=ofs_loc)
                vt = bob_piv + ((vt + head_rel) @ R_bob.T)
                nt = nt @ R_bob.T
                return vt, nt

            # 1. Colossal Skeptical-Eyebrow, Bullfrog-Cheek-Puffing, Monocle-Wearing Stoic John Hull!
            puff_cyc = (0.5 + 0.5 * math.sin(tau)) if is_lie else (0.5 + 0.5 * math.sin((4.0 if is_boost else 2.0) * tau))
            brow_amt = (-0.65 + 0.15 * math.sin(tau)) if is_lie else (1.50 + 0.55 * math.sin(2.0 * tau))
            hdv, hdn = deform_calm_john(
                calm_v, calm_n,
                beard_wag=K["beard_wag"] * 1.65,
                hair_ripple=h_rip,
                phase=K["hair_wave_phase"],
                cigar_puff=K["jaw_open"],
                cheek_puff=1.35 * puff_cyc,
                brow_cock=brow_amt,
            )
            hdv, hdn = head_vn(hdv, hdn, scale=4.65)
            hdv, hdn = to_hull(hdv, hdn)
            record_frame("jw_calm_hull", "progs/jw_air_calm", calm_u, calm_t, hdv, hdn)

            # Attach Head-Local Gold Monocle Bezel + Chain, Dalí Handlebar Mustache, Nostril Pipes, Cockpit & Tailfin!
            sb_chr.add_mesh_part(v1_sub["head_hw"], R=R_bob, offset=tuple(head_pt((0.0, 0.0, 0.0))))

            # Hypno-Spinning Mega-Man White-Dish Tire Monocle inside the Gold Bezel over Right Eye (-Y)!
            R_mon = R_bob @ rot_z_mat(-11.5) @ rot_x_mat(-K["prop_spin"] * 0.65) @ rot_z_mat(90.0)
            mon_pos = tuple(head_pt((41.2, -13.5, 5.6)))
            sb_wb.add_mesh_part(mm_lite["wheel_r"], scale=1.82, R=R_mon, offset=mon_pos)
            sb_chr.add_mesh_part(mm_lite["wheel_hw_r"], scale=1.82, R=R_mon, offset=mon_pos)

            # Angry-Bull Nostril Steam Jets shooting out of both flared chrome nostril pipes!
            nos_sc = 0.25 if is_lie else (0.55 + 0.65 * puff_cyc) * max(0.7, K["plume_scale"])
            for sy in (-1.0, 1.0):
                n_pos = tuple(head_pt((48.5, sy * 20.0, -13.2)))
                n_dir = np.array([0.48, sy * 0.78, -0.40], dtype=np.float32) @ R_bob.T
                n_dir /= np.linalg.norm(n_dir)
                nv_a, nn_a, nu_a, nt_a = make_plume_cone_arrays(n_pos, tuple(n_dir), 4.6, 22.0 * nos_sc, "magenta" if is_boost else "cyan")
                sb_fx.add_arrays(nv_a, nn_a, nu_a, nt_a)

            # 2. Handlebar-Mustache Mega-Man Cross-Axle + Twin Giant White-Dish Tire Propellers!
            R_stache = R_bob
            stache_pos = head_pt((48.5, 0.0, -15.0))
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(3.4, 8.6, 3.4), R=R_stache, offset=tuple(stache_pos))
            tilt_up = K["tilt_fwd_deg"]
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                p_hub = tuple(head_pt((48.5, sy * mmg.MM_WHEEL_Y * 8.6, -15.0)))
                R_prop = R_bob @ rot_y_mat(tilt_up) @ rot_x_mat(sy * K["prop_spin"]) @ rot_z_mat(-90.0 * sy)
                sb_wa.add_mesh_part(mm_hero[f"wheel_{side_nm}"], scale=4.8, R=R_prop, offset=p_hub)
                sb_chr.add_mesh_part(mm_hero[f"wheel_hw_{side_nm}"], scale=4.8, R=R_prop, offset=p_hub)
                disc_sc = 0.01 if is_lie else 1.0
                p_axis = np.array([1.0, 0.0, 0.0], dtype=np.float32) @ (R_bob @ rot_y_mat(tilt_up)).T
                rv, rn, ru, rt = make_rotor_disc_arrays(p_hub, tuple(p_axis), 11.5 * disc_sc, 22.8 * disc_sc)
                sb_fx.add_arrays(rv, rn, ru, rt)

            # 3. Jaunty Side-Mouth Lit Mega-Man Stogie + Twin Cigar-Band Turbo Tires + 3D 'John Wave' Smoke Rings!
            R_cig_loc = euler_mat(0.0, +9.5 - 1.5 * K["jaw_open"], +8.5)
            R_cig = R_bob @ R_cig_loc
            cig_loc = np.array([58.0, +7.5, -22.5], dtype=np.float32)
            cig_pos = tuple(head_pt(cig_loc))
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(8.6, 2.7, 2.7), R=R_cig, offset=cig_pos)
            sb_chr.add_mesh_part(v1_sub["cigar_band"], R=R_cig, offset=cig_pos)
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                ct_hub = head_pt(cig_loc + (np.array([0.0, sy * mmg.MM_WHEEL_Y * 2.7, 0.0], dtype=np.float32) @ R_cig_loc.T))
                R_ct = R_cig @ rot_y_mat(-K["prop_spin"] * 0.8)
                sb_wb.add_mesh_part(mm_lite[f"wheel_{side_nm}"], scale=1.45, R=R_ct, offset=tuple(ct_hub))
                sb_chr.add_mesh_part(mm_lite[f"wheel_hw_{side_nm}"], scale=1.45, R=R_ct, offset=tuple(ct_hub))

            # Glowing Amber Lit Cigar Tip + Puffing/Wafting 3D Foamy 'JOHN WAVE' Smoke Rings!
            cig_dir = np.array([1.0, 0.0, 0.0], dtype=np.float32) @ R_cig.T
            cig_tip = head_pt(cig_loc + (np.array([5.35 * 8.6, 0.0, 0.0], dtype=np.float32) @ R_cig_loc.T))
            ev, en, eu, et = make_plume_cone_arrays(tuple(cig_tip), tuple(cig_dir), 4.8, 12.0 + 6.0 * puff_cyc, "amber")
            sb_fx.add_arrays(ev, en, eu, et)

            smk_mul = 0.55 if is_lie else 1.0
            d_smk1 = 10.0 + 9.0 * (1.0 - math.cos(2.0 * tau))
            d_smk2 = 26.0 + 11.0 * (1.0 - math.cos(2.0 * tau - 1.3))
            for sm_i, (d_s, sc_s, sp_s) in enumerate(((d_smk1, (0.14 + 0.04 * puff_cyc) * smk_mul, 1.2), (d_smk2, 0.20 * smk_mul, -0.9))):
                sm_pos = cig_tip + cig_dir * d_s
                R_sm = R_cig @ rot_x_mat(sp_s * K["wave_spin"] + sm_i * 75.0) @ rot_y_mat(90.0)
                sb_surf.add_arrays(wave_v, wave_n, wave_u, wave_t, scale=sc_s, R=R_sm, offset=tuple(sm_pos))

            # 4. COLOSSAL JAUNTILY COCKED CRIMSON-RED FEDORA ON GIANT JOHN'S HEAD ('M'Biplane' Fedora-Tip!)
            fed_v, fed_n, fed_u, fed_t = v1_sub["fedora"]
            if is_lie:
                # Snoozing fedora tipped slightly forward over his brow while snoring!
                R_fed_loc = euler_mat(+5.5, -6.5 + 1.5 * math.sin(tau), +3.0)
            else:
                # Jaunty mobster/detective tilt + rhythmic 'M'Biplane' fedora-tip nod!
                tip_nod = -3.8 * (0.5 + 0.5 * math.sin(2.0 * tau))
                R_fed_loc = euler_mat(+6.5 + 1.8 * math.cos(tau), -2.0 + tip_nod, +3.5)
            R_fed = R_bob @ R_fed_loc
            fed_pos = tuple(head_pt((0.0, 0.0, 0.0)))
            sb_fed.add_arrays(fed_v, fed_n, fed_u, fed_t, scale=4.65, R=R_fed, offset=fed_pos)
            sb_chr.add_mesh_part(v1_sub["fed_buckle"], scale=4.65, R=R_fed, offset=fed_pos)

            # 5. Flapping Cartoon WWI Biplane Wings + Twin Mini-Red-Fedora Henchmen Wing-Walkers!
            if is_lie:
                flap_deg = -12.0 + 1.8 * math.sin(tau)
            elif is_boost:
                flap_deg = 6.0 + 20.0 * math.sin(4.0 * tau)
            elif K["mode"] == "hover":
                flap_deg = 12.0 + 18.0 * math.sin(2.0 * tau)
            else:
                flap_deg = 15.0 * math.sin(2.0 * tau)

            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                hinge_loc = np.array([2.0, sy * 34.0, -4.0], dtype=np.float32)
                hinge_pos = head_pt(hinge_loc)
                R_flap_loc = rot_x_mat(sy * flap_deg)
                R_wing = R_bob @ R_flap_loc
                sb_chr.add_mesh_part(v1_sub["wings"][side_nm], R=R_wing, offset=tuple(hinge_pos))

                # Swept Upper & Lower Mega-Man Chrome Bullet Wing-Bars flapping with the wing cell!
                R_wbar = R_wing @ rot_z_mat(sy * 86.0)
                up_bpos = head_pt(hinge_loc + (np.array([0.0, sy * 48.0, +49.6], dtype=np.float32) @ R_flap_loc.T))
                lo_bpos = head_pt(hinge_loc + (np.array([1.0, sy * 48.0, -16.4], dtype=np.float32) @ R_flap_loc.T))
                sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(6.2, 2.6, 2.6), R=R_wbar, offset=tuple(up_bpos))
                sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(6.0, 2.5, 2.5), R=R_wbar, offset=tuple(lo_bpos))

                # Wing-Walker Rocket Pod + Stoic Henchman Mini-John in Matching Mini Red Fedora & Tire Shades!
                rk_loc = hinge_loc + (np.array([4.0, sy * 45.0, -12.5], dtype=np.float32) @ R_flap_loc.T)
                sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(3.4, 1.8, 1.8), R=R_wing, offset=tuple(head_pt(rk_loc)))
                ww_rel = hinge_loc + (np.array([2.0, sy * 45.0, +2.5], dtype=np.float32) @ R_flap_loc.T)
                R_ww_loc = R_flap_loc @ euler_mat(0.0, 0.0, sy * 20.0 * math.sin(tau))
                R_ww = R_bob @ R_ww_loc
                ww_pos = head_pt(ww_rel)
                ww_v, ww_n = deform_calm_john(calm_v, calm_n, beard_wag=sy * K["beard_wag"], brow_cock=1.0)
                ww_v, ww_n = head_vn(ww_v, ww_n, scale=1.30, R_loc=R_ww_loc, ofs_loc=ww_rel)
                ww_v, ww_n = to_hull(ww_v, ww_n)
                record_frame(f"jw_calm_wing_{side_nm}", "progs/jw_air_calm", calm_u, calm_t, ww_v, ww_n)
                sb_fed.add_arrays(fed_v, fed_n, fed_u, fed_t, scale=1.30, R=R_ww @ euler_mat(sy * 5.0, -3.0, 0.0), offset=tuple(ww_pos))

                for g_nm, g_sy in (("l", 1.0), ("r", -1.0)):
                    wg_pos = head_pt(ww_rel + (np.array([11.8, g_sy * 4.1, 1.8], dtype=np.float32) @ R_ww_loc.T))
                    R_wg = R_ww @ rot_x_mat(g_sy * K["prop_spin"] * 0.5) @ rot_z_mat(-90.0 * g_sy)
                    sb_wb.add_mesh_part(mm_lite[f"wheel_{g_nm}"], scale=0.78, R=R_wg, offset=tuple(wg_pos))

            # 6. Rear 'Cuckoo-Clock Man-Bun' Pop-Out Mini-John (also rocking a Mini Red Fedora + Tire-Beanie!)
            cuckoo_ext = 3.0 if is_lie else (22.0 + 4.0 * math.sin(4.0 * tau) if is_boost else 9.0 + 11.0 * (0.5 + 0.5 * math.sin(2.0 * tau)))
            ck_bar_pos = tuple(head_pt((-39.0 - 0.5 * cuckoo_ext, 0.0, 10.0)))
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(4.6, 2.2, 2.2), R=R_bob @ rot_z_mat(180.0), offset=ck_bar_pos)

            ck_loc = np.array([-46.0 - cuckoo_ext, 0.0, 11.5], dtype=np.float32)
            R_ck_loc = euler_mat(0.0, 4.0 * math.sin(2.0 * tau), 180.0 - 18.0 * math.sin(tau))
            R_ck = R_bob @ R_ck_loc
            ck_pos = head_pt(ck_loc)
            ck_v, ck_n = deform_calm_john(calm_v, calm_n, beard_wag=-K["beard_wag"], cheek_puff=0.8 * puff_cyc, brow_cock=1.3)
            ck_v, ck_n = head_vn(ck_v, ck_n, scale=1.34, R_loc=R_ck_loc, ofs_loc=ck_loc)
            ck_v, ck_n = to_hull(ck_v, ck_n)
            record_frame("jw_calm_cuckoo", "progs/jw_air_calm", calm_u, calm_t, ck_v, ck_n)
            sb_fed.add_arrays(fed_v, fed_n, fed_u, fed_t, scale=1.34, R=R_ck @ euler_mat(-5.0, -2.5, 0.0), offset=tuple(ck_pos))

            # Tiny spinning Propeller-Beanie White-Dish Tire mounted right atop Cuckoo John's Red Fedora!
            ck_hat = head_pt(ck_loc + (np.array([0.0, 0.0, 21.0], dtype=np.float32) @ R_ck_loc.T))
            R_ck_tire = R_ck @ rot_z_mat(K["rotor_spin"]) @ rot_x_mat(90.0)
            sb_wb.add_mesh_part(mm_lite["wheel_l"], scale=1.80, R=R_ck_tire, offset=tuple(ck_hat))
            sb_chr.add_mesh_part(mm_lite["wheel_hw_l"], scale=1.80, R=R_ck_tire, offset=tuple(ck_hat))

            # Lower Skull Tail Boom + Rudder Tire + Twin Swirling Foamy 'JOHN WAVE' Tidal-Wave Exhaust!
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=5.8, R=R_bob @ rot_z_mat(180.0), offset=tuple(head_pt((-74.0, 0.0, -14.0))))
            R_rud = R_bob @ rot_z_mat(12.0 * math.sin(tau) if not is_lie else 0.0) @ rot_y_mat(-K["wheel_roll"])
            rud_pos = tuple(head_pt((-98.0, 0.0, -2.0)))
            sb_wa.add_mesh_part(mm_hero["wheel_l"], scale=3.6, R=R_rud, offset=rud_pos)
            sb_chr.add_mesh_part(mm_hero["wheel_hw_l"], scale=3.6, R=R_rud, offset=rud_pos)

            tail_dir = np.array([-1.0, 0.0, 0.0], dtype=np.float32) @ R_bob.T
            for wi, (wx, wsc, wspd) in enumerate(((-90.0, 0.28, 1.0), (-112.0, 0.36 * max(0.35, K["plume_scale"]), -1.4))):
                R_wv = R_bob @ rot_x_mat(wspd * K["wave_spin"] + wi * 60.0) @ rot_y_mat(90.0)
                sb_surf.add_arrays(wave_v, wave_n, wave_u, wave_t, scale=wsc, R=R_wv, offset=tuple(head_pt((wx, 0.0, -22.0))))

            q_col = "amber" if is_boost else "cyan"
            pv, pn, pu, pt = make_plume_cone_arrays(tuple(head_pt((-84.0, 0.0, -22.0))), tuple(tail_dir),
                                                    15.0, 52.0 * K["plume_scale"], q_col)
            sb_fx.add_arrays(pv, pn, pu, pt)

        # ===================================================================
        # VARIANT 2: SR-99 "IN-ONE-EAR" (Ear-Skewered Beats-By-Mega-Man Jet)
        # ===================================================================
        elif vid == "v2":
            # 1. Colossal Mega-Man Chrome Rocket Fuselage bursting straight out of Giant John's Mouth + Ear-Skewer Cross-Axle!
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(21.5, 8.2, 8.6), R=None, offset=(16.0, 0.0, 39.0))
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(5.2, 12.0, 5.2), R=None, offset=(12.0, 0.0, 60.0))

            # 2. Giant Screaming John Skewered Ear-to-Ear at (12, 0, 62)!
            for sname, (sv0, sn0, su0, st0) in (("jw_scream_l", assets["scream_l"]), ("jw_scream_r", assets["scream_r"])):
                dv, dn = deform_scream_john(
                    sv0, sn0,
                    hair_flap_deg=K["hair_flap"] * 0.65,
                    hair_wave_phase=K["hair_wave_phase"],
                    hair_wave_amp=K["hair_wave_amp"],
                    hair_sweep_deg=18.0 + K["hair_sweep"],
                    jaw_open=max(2.4, K["jaw_open"]),  # Mouth stretched wide around supersonic rocket barrel!
                    gforce_stretch=K["gforce"],
                )
                dv, dn = xform_vn(dv, dn, scale=5.5, R=None, offset=(12.0, 0.0, 62.0))
                dv, dn = to_hull(dv, dn)
                record_frame(sname, "progs/jw_air_scream", su0, st0, dv, dn)

            # 3. Twin Under-Wing Screaming John Ramjet Nacelle Pods (chomping out-of-phase under swept delta wings!)
            for pod_idx, (pod_tag, sy, ph_ofs) in enumerate((("jw_aux1", +1.0, 0.0), ("jw_aux2", -1.0, math.pi))):
                pod_jaw = 1.6 + 1.4 * math.sin(2.0 * K["tau"] + ph_ofs) if K["mode"] != "lie" else 0.5
                for half_tag, (sv0, sn0, su0, st0) in (("l", assets["scream_l"]), ("r", assets["scream_r"])):
                    dv, dn = deform_scream_john(
                        sv0, sn0,
                        hair_flap_deg=12.0 * math.sin(K["tau"] + ph_ofs) if K["mode"] != "lie" else -15.0,
                        hair_wave_phase=K["hair_wave_phase"],
                        hair_wave_amp=0.8,
                        hair_sweep_deg=22.0,
                        jaw_open=pod_jaw,
                    )
                    dv, dn = xform_vn(dv, dn, scale=2.35, R=None, offset=(-18.0, sy * 58.0, 32.0))
                    dv, dn = to_hull(dv, dn)
                    record_frame(f"{pod_tag}_{half_tag}", "progs/jw_air_scream", su0, st0, dv, dn)

                # Wingtip Mega-Man Chrome Missiles at y = +-102!
                sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=5.8, R=None, offset=(-42.0, sy * 102.0, 46.0))
                # Underwing pod surf-ring + plasma jet!
                R_pw = rot_x_mat((1.0 if pod_idx == 0 else -1.0) * K["wave_spin"]) @ rot_y_mat(90.0)
                sb_surf.add_arrays(wave_v, wave_n, wave_u, wave_t, scale=0.16, R=R_pw, offset=(-52.0, sy * 58.0, 32.0))
                pv, pn, pu, pt = make_plume_cone_arrays((-52.0, sy * 58.0, 32.0), (-1.0, 0.0, 0.0),
                                                        7.5, 28.0 * K["plume_scale"], "magenta")
                sb_fx.add_arrays(pv, pn, pu, pt)

            # 4. Rear-Facing Deadpan Calm John Tail-Gunner!
            R_gunner = euler_mat(0.0, K["calm_pitch"], 180.0 + K["calm_yaw"])
            cdv, cdn = deform_calm_john(calm_v, calm_n, beard_wag=K["beard_wag"])
            cdv, cdn = xform_vn(cdv, cdn, scale=1.45, R=R_gunner, offset=(-52.0, 0.0, 82.0))
            cdv, cdn = to_hull(cdv, cdn)
            record_frame("jw_calm", "progs/jw_air_calm", calm_u, calm_t, cdv, cdn)

            # 5. COLOSSAL "BEATS-BY-MEGA-MAN" MONSTER HEADPHONE TILT-ROTOR TIRES (scale = 9.8 -> 79 units tall!)
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                if K["mode"] == "lie":
                    # Parked on runway: giant headphone tires drop into Monster-Truck stance on z=0!
                    ear_pos = (12.0, sy * 68.5, 45.0)
                    R_ear = rot_y_mat(-K["wheel_roll"])
                    disc_sc = 0.01
                else:
                    ear_pos = (12.0, sy * 68.5, 60.0)
                    R_ear = rot_y_mat(K["tilt_fwd_deg"]) @ rot_x_mat(sy * K["prop_spin"]) @ rot_z_mat(-90.0 * sy)
                    disc_sc = 1.0
                e_axis = np.array([1.0, 0.0, 0.0], dtype=np.float32) @ rot_y_mat(K["tilt_fwd_deg"]).T
                rv, rn, ru, rt = make_rotor_disc_arrays(ear_pos, tuple(e_axis), 22.0 * disc_sc, 42.0 * disc_sc)
                sb_fx.add_arrays(rv, rn, ru, rt)
                sb_wa.add_mesh_part(mm_hero[f"wheel_{side_nm}"], scale=9.8, R=R_ear, offset=ear_pos)
                sb_chr.add_mesh_part(mm_hero[f"wheel_hw_{side_nm}"], scale=9.8, R=R_ear, offset=ear_pos)

            # Tailwheel (level with monster headphone tires on runway!) + Wingtip Wheels
            R_tw = rot_y_mat(-K["wheel_roll"])
            sb_wb.add_mesh_part(mm_lite["wheel_l"], scale=5.8, R=R_tw, offset=(-76.0, 0.0, 28.9))
            sb_chr.add_mesh_part(mm_lite["wheel_hw_l"], scale=5.8, R=R_tw, offset=(-76.0, 0.0, 28.9))
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                sb_wb.add_mesh_part(mm_lite[f"wheel_{side_nm}"], scale=2.8, R=R_tw, offset=(-42.0, sy * 112.0, 46.0))

            # Twin Rear Supersonic Afterburners + Giant Tidal-Wave Vortex!
            R_mw = rot_x_mat(K["wave_spin"]) @ rot_y_mat(90.0)
            sb_surf.add_arrays(wave_v, wave_n, wave_u, wave_t, scale=0.38 * max(0.35, K["plume_scale"]), R=R_mw, offset=(-92.0, 0.0, 39.0))
            q_col = "amber" if K["mode"] == "boost" else "cyan"
            for sy in (-1.0, 1.0):
                pv, pn, pu, pt = make_plume_cone_arrays((-92.0, sy * 11.0, 39.0), (-1.0, 0.0, 0.0),
                                                        11.0, 48.0 * K["plume_scale"], q_col)
                sb_fx.add_arrays(pv, pn, pu, pt)

        # ===================================================================
        # VARIANT 3: CH-99 "THE HAIR-ICOPTER" (100% Screaming-Head-Free! Push-Me-Pull-You Deadpan Chinook)
        # ===================================================================
        else:
            # 1. Flying Mega-Man Chrome Broomstick Spine + Twin Midship Side-Sponson Chrome Rocket Bars!
            sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(20.2, 8.2, 8.2), R=None, offset=(4.0, 0.0, 39.0))
            for sy in (-1.0, 1.0):
                sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(6.2, 3.0, 3.0), R=None, offset=(2.0, sy * 28.0, 44.0))

            h_rip = 0.85 if K["mode"] != "lie" else 0.15

            # 2. FRONT BOW: Colossal Stoic Deadpan Lush-Hair John facing FORWARD (+X) with zero emotion!
            R_front_john = euler_mat(0.0, K["calm_pitch"] * 0.55, K["calm_yaw"] * 0.40)
            fdv, fdn = deform_calm_john(calm_v, calm_n, beard_wag=K["beard_wag"] * 1.35, hair_ripple=h_rip, phase=K["hair_wave_phase"])
            fdv, fdn = xform_vn(fdv, fdn, scale=3.85, R=R_front_john, offset=(52.0, 0.0, 74.0))
            fdv, fdn = to_hull(fdv, fdn)
            record_frame("jw_calm_front", "progs/jw_air_calm", calm_u, calm_t, fdv, fdn)

            # 3. REAR STERN: Colossal Stoic Deadpan Lush-Hair John facing BACKWARD (-X) staring down pursuers!
            R_rear_john = euler_mat(0.0, -K["calm_pitch"] * 0.55, 180.0 + K["calm_yaw"] * 0.45)
            rdv, rdn = deform_calm_john(calm_v, calm_n, beard_wag=-K["beard_wag"] * 1.40, hair_ripple=h_rip, phase=K["hair_wave_phase"] + 1.5)
            rdv, rdn = xform_vn(rdv, rdn, scale=3.65, R=R_rear_john, offset=(-54.0, 0.0, 72.0))
            rdv, rdn = to_hull(rdv, rdn)
            record_frame("jw_calm_rear", "progs/jw_air_calm", calm_u, calm_t, rdv, rdn)

            # 4. MIDSHIP SADDLE: Stoic Deadpan Mini-Biker John in Hypno-Spinning Tire Shades gripping Ape-Hanger Bars!
            R_biker = euler_mat(7.0 * math.cos(K["tau"]) if K["mode"] != "lie" else 0.0, -4.0, K["calm_yaw"] * 0.85)
            biker_ofs = np.array([-1.0, 0.0, 74.5], dtype=np.float32)
            bdv, bdn = deform_calm_john(calm_v, calm_n, beard_wag=K["beard_wag"] * 0.8, hair_ripple=h_rip * 0.6, phase=K["hair_wave_phase"])
            bdv, bdn = xform_vn(bdv, bdn, scale=1.95, R=R_biker, offset=biker_ofs)
            bdv, bdn = to_hull(bdv, bdn)
            record_frame("jw_calm_biker", "progs/jw_air_calm", calm_u, calm_t, bdv, bdn)

            # Mini-Biker John's Spinning Mega-Man Wheel Aviator Goggles!
            for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                gog_loc = np.array([17.6, sy * 6.2, 3.2], dtype=np.float32)
                gog_pos = biker_ofs + (gog_loc @ R_biker.T)
                R_gog = R_biker @ rot_x_mat(sy * K["prop_spin"] * 0.5) @ rot_z_mat(-90.0 * sy)
                sb_wb.add_mesh_part(mm_lite[f"wheel_{side_nm}"], scale=1.08, R=R_gog, offset=tuple(gog_pos))
                sb_chr.add_mesh_part(mm_lite[f"wheel_hw_{side_nm}"], scale=1.08, R=R_gog, offset=tuple(gog_pos))

            # 5. TWIN COUNTER-ROTATING MEGA-MAN PROPELLER-BEANIE CHINOOK ROTORS!
            beanie_specs = [
                (+52.0, 128.0, +1.0, 0.0),    # Front Deadpan John's Beanie Rotor
                (-54.0, 125.0, -1.0, 90.0),   # Rear Deadpan John's Counter-Rotating Beanie Rotor
            ]
            for b_idx, (bx, bz, dir_s, ph_deg) in enumerate(beanie_specs):
                mast_pos = np.array([bx, 0.0, bz], dtype=np.float32)
                # rot_y_mat(+90) points gleaming chrome bullet tip STRAIGHT UP (+Z) like a propeller-beanie cap finial!
                R_mast = rot_z_mat(dir_s * K["rotor_spin"] + ph_deg) @ rot_y_mat(90.0)
                sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=5.8, R=R_mast, offset=tuple(mast_pos))

                for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                    tip_local = np.array([0.0, sy * mmg.MM_WHEEL_Y * 5.8, 0.0], dtype=np.float32) @ R_mast.T
                    w_pos = mast_pos + tip_local
                    # Tilt white-dish tires flat horizontally (rot_x_mat(82*sy)) like giant spinning helicopter rotor blades!
                    R_blade = R_mast @ rot_x_mat(82.0 * sy) @ rot_y_mat(-K["prop_spin"] * 0.5)
                    sb_wa.add_mesh_part(mm_lite[f"wheel_{side_nm}"], scale=5.2, R=R_blade, offset=tuple(w_pos))
                    sb_chr.add_mesh_part(mm_lite[f"wheel_hw_{side_nm}"], scale=5.2, R=R_blade, offset=tuple(w_pos))

                # Swirling Foamy "JOHN WAVE" Ocean Surf Halo around each Beanie Rotor!
                R_wh = rot_z_mat(dir_s * K["wave_spin"] + ph_deg)
                sb_surf.add_arrays(wave_v, wave_n, wave_u, wave_t, scale=0.44, R=R_wh, offset=(bx, 0.0, bz - 4.0))
                disc_sc = 0.01 if K["mode"] == "lie" else 1.0
                rv, rn, ru, rt = make_rotor_disc_arrays((bx, 0.0, bz + 1.0), (0.0, 0.0, 1.0), 18.0 * disc_sc, 46.0 * disc_sc)
                sb_fx.add_arrays(rv, rn, ru, rt)

            # 6. Quad Mega-Man Pontoon Landing Wheels (front & rear cross-axles on z=0!)
            R_roll = rot_y_mat(-K["wheel_roll"])
            for x_ax in (50.0, -50.0):
                sb_chr.add_mesh_part(mm_hero["bar_axle"], scale=(4.5, 7.2, 4.5), R=None, offset=(x_ax, 0.0, 17.8))
                for side_nm, sy in (("l", 1.0), ("r", -1.0)):
                    p_w = (x_ax, sy * mmg.MM_WHEEL_Y * 7.2, 17.8)
                    sb_wb.add_mesh_part(mm_lite[f"wheel_{side_nm}"], scale=4.4, R=R_roll, offset=p_w)
                    sb_chr.add_mesh_part(mm_lite[f"wheel_hw_{side_nm}"], scale=4.4, R=R_roll, offset=p_w)

            # Rear twin hydro-jet exhaust plumes (below Rear Deadpan John's chin!)
            q_col = "amber" if K["mode"] == "boost" else "cyan"
            for sy in (-1.0, 1.0):
                pv, pn, pu, pt = make_plume_cone_arrays((-92.0, sy * 19.0, 30.0), (-1.0, 0.0, 0.0),
                                                        9.5, 42.0 * K["plume_scale"], q_col)
                sb_fx.add_arrays(pv, pn, pu, pt)

        # Finalize dynamic surfaces for frame fi (auto-chunked <= 3600v / <= 7200t per MD3 surface!)
        for sb in (sb_fed, sb_chr, sb_wa, sb_wb, sb_surf, sb_fx):
            for cname, cshader, sv, sn, su, st in sb.finalize_chunks(max_v=3600, max_t=7200):
                sv, sn = to_hull(sv, sn)
                record_frame(cname, cshader, su, st, sv, sn)

    # Shift all frames vertically so Lie_Rest frame 44 rests cleanly on z = 0.000!
    solid_names = [k for k in surf_order if surf_defs[k]["shader"] not in ("progs/jw_air_fx", "progs/jw_air_wave")]
    z_lie_min = min(min(p[2] for p in surf_defs[sn]["frames"][44][0]) for sn in solid_names)
    dz_fix = -z_lie_min
    for sn in surf_order:
        sd = surf_defs[sn]
        sd["frames"] = [([(p[0], p[1], p[2] + dz_fix) for p in vv], nn) for vv, nn in sd["frames"]]

    surfs_list = [surf_defs[sn] for sn in surf_order]
    model_name = f"jw_air_{vid}"
    md3_path = os.path.join(PROGS, f"{model_name}.md3")
    md3lib.write(md3_path, dict(name=model_name, surfaces=surfs_list, nframes=TOTAL_FRAMES))

    skin_path = os.path.join(PROGS, f"{model_name}.md3_0.skin")
    with open(skin_path, "w", encoding="ascii") as f:
        for s in surfs_list:
            f.write(f"{s['name']},{s['shader']}\n")

    # Save V1 also as Flagship progs/jw_aircraft.md3 + progs/jw_aircraft.md3_0.skin!
    if vid == "v1":
        flag_md3 = os.path.join(PROGS, "jw_aircraft.md3")
        flag_skin = os.path.join(PROGS, "jw_aircraft.md3_0.skin")
        md3lib.write(flag_md3, dict(name="jw_aircraft", surfaces=surfs_list, nframes=TOTAL_FRAMES))
        shutil.copyfile(skin_path, flag_skin)

    tot_v = sum(len(s["st"]) for s in surfs_list)
    tot_t = sum(len(s["tris"]) for s in surfs_list)
    max_sv = max(len(s["st"]) for s in surfs_list)
    max_st = max(len(s["tris"]) for s in surfs_list)
    assert max_sv <= 4096 and max_st <= 8192, f"Surface cap exceeded in {model_name}: {max_sv}v, {max_st}t"
    print(
        f"  Wrote {md3_path}: {TOTAL_FRAMES}f, {len(surfs_list)} surfs (max_v={max_sv}, max_t={max_st}), "
        f"total={tot_v}v / {tot_t}t — {title}",
        flush=True,
    )
    return md3_path


def write_shader_and_frame_docs():
    os.makedirs(SCRIPTS, exist_ok=True)
    shader_path = os.path.join(SCRIPTS, "jw_aircraft.shader")
    with open(shader_path, "w", encoding="ascii") as f:
        f.write("""// Quake / DarkPlaces Shaders for John Wave x Mega Man Aircraft (jw_aircraft.md3 & jw_air_v1..v3.md3)
progs/jw_air_scream
{
\tcull none
\t{
\t\tmap progs/jw_air_scream
\t\trgbGen lightingDiffuse
\t}
}

progs/jw_air_calm
{
\tcull none
\t{
\t\tmap progs/jw_air_calm
\t\trgbGen lightingDiffuse
\t}
}

progs/jw_air_fedora
{
\tcull none
\t{
\t\tmap progs/jw_air_fedora
\t\trgbGen lightingDiffuse
\t}
}

progs/jw_air_chrome
{
\tcull none
\t{
\t\tmap progs/mmw_chrome_axle
\t\trgbGen lightingDiffuse
\t}
}

progs/jw_air_wheel
{
\tcull none
\t{
\t\tmap progs/mmw_wheel
\t\trgbGen lightingDiffuse
\t}
}

progs/jw_air_wave
{
\tcull none
\t{
\t\tmap progs/jw_air_wave
\t\trgbGen identity
\t}
}

progs/jw_air_fx
{
\tcull none
\t{
\t\tmap progs/jw_air_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
""")

    frames_txt = os.path.join(PROGS, "jw_aircraft_frames.txt")
    with open(frames_txt, "w", encoding="utf-8") as f:
        f.write("// Quake MD3 Frame Table for progs/jw_aircraft.md3 & progs/jw_air_v1..v3.md3 (72 frames)\n")
        for clip_id, start, count, fps, desc in ANIM_CLIPS:
            f.write(f"// {clip_id:15s} : frames {start:2d}..{start + count - 1:2d} ({count:2d} frames @ {fps:4.1f} fps) - {desc}\n")
        f.write("\n$frame " + " ".join(f"cruise{i}" for i in range(16)) + "\n")
        f.write("$frame " + " ".join(f"boost{i}" for i in range(16)) + "\n")
        f.write("$frame " + " ".join(f"hover{i}" for i in range(12)) + "\n")
        f.write("$frame " + " ".join(f"lie{i}" for i in range(12)) + "\n")
        f.write("$frame " + " ".join(f"roll{i}" for i in range(16)) + "\n")
    print(f"  Wrote {shader_path} and {frames_txt}", flush=True)


# --------------------------------------------------------------------------- Multi-Angle Verification Sheet Renderer
def render_verification_sheet(md3_paths, out_png):
    """Reads the written .md3 files from progs/ and renders a 3x5 verification grid:
    Rows = V1..V3, Cols = [Front-3/4 Cruise, Side Boost Scream, 360 Barrel Roll, Rear-3/4 Surf Exhaust, Landed z=0]."""
    tex_lookup = {
        "progs/jw_air_scream": np.array(Image.open(os.path.join(OUT_DIR, "jw_scream_srgb.png")).convert("RGB")),
        "progs/jw_air_calm":   np.array(Image.open(os.path.join(OUT_DIR, "jw_calm_srgb.png")).convert("RGB")),
        "progs/jw_air_fedora": np.array(Image.open(os.path.join(OUT_DIR, "jw_fedora_srgb.png")).convert("RGB")),
        "progs/jw_air_chrome": np.array(Image.open(os.path.join(HERE, "out", "megaman_weapon", "mmw_chrome_axle.png")).convert("RGB")),
        "progs/jw_air_wheel":  np.array(Image.open(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png")).convert("RGB")),
        "progs/jw_air_wave":   np.array(Image.open(os.path.join(OUT_DIR, "jw_wave_srgb.png")).convert("RGB")),
        "progs/jw_air_fx":     np.array(Image.open(os.path.join(OUT_DIR, "jw_fx_srgb.png")).convert("RGB")),
    }

    W_c, H_c = 400, 310
    cols_cfg = [
        (4,  34.0,  18.0),   # Front-3/4 Cruise (Jaw Chomp + Hair Wings Up!)
        (20, 86.0,  10.0),   # Side Profile Mach-5 Scream (Max Jaw Drop + Afterburners!)
        (60, 28.0,  16.0),   # Barrel Roll 90-deg Bank!
        (12, 146.0, 20.0),   # Rear-3/4 Cruise (Tidal-Wave Exhaust / Rear Deadpan John!)
        (46, 36.0,  15.0),   # Landed / Lying on Runway z=0!
    ]
    sheet = np.full((H_c * len(md3_paths), W_c * len(cols_cfg), 3), 20, dtype=np.uint8)
    light_dir = np.array([0.52, -0.36, 0.77], dtype=np.float32)
    light_dir /= np.linalg.norm(light_dir)

    for r_idx, path in enumerate(md3_paths):
        m = md3lib.read(path)
        pts0 = np.vstack([np.asarray(s["frames"][0][0], dtype=np.float32)
                          for s in m["surfaces"] if s["shader"] != "progs/jw_air_fx"])
        ctr = 0.5 * (pts0.min(axis=0) + pts0.max(axis=0))
        span = float(np.max(pts0.max(axis=0) - pts0.min(axis=0)))
        sc = (W_c * 0.78) / span

        for c_idx, (fi, yaw_deg, el_deg) in enumerate(cols_cfg):
            zb = np.full((H_c, W_c), -1e9, dtype=np.float32)
            grad = np.linspace(0.0, 1.0, H_c)[:, None]
            cb = np.broadcast_to(
                np.clip(
                    np.array([18, 30, 52])[None, None, :] * (1.0 - grad[..., None])
                    + np.array([44, 70, 102])[None, None, :] * grad[..., None],
                    0, 255,
                ).astype(np.float32),
                (H_c, W_c, 3),
            ).copy()

            ry, re = math.radians(yaw_deg), math.radians(el_deg)
            cy_a, sy_a = math.cos(ry), math.sin(ry)
            ce_a, se_a = math.cos(re), math.sin(re)

            ordered_surfs = (
                [s for s in m["surfaces"] if s["shader"] != "progs/jw_air_fx"]
                + [s for s in m["surfaces"] if s["shader"] == "progs/jw_air_fx"]
            )
            for s in ordered_surfs:
                is_add = s["shader"] == "progs/jw_air_fx"
                is_unlit = s["shader"] == "progs/jw_air_wave"
                tex = tex_lookup[s["shader"]]
                th, tw = tex.shape[:2]
                va = np.asarray(s["frames"][fi][0], dtype=np.float32) - ctr
                na = np.asarray(s["frames"][fi][1], dtype=np.float32)
                ua = np.asarray(s["st"], dtype=np.float32)
                ta = np.asarray(s["tris"], dtype=np.int32)

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

                    uu = np.mod(w0v * ua[a, 0] + w1v * ua[b, 0] + w2v * ua[c, 0], 1.0)
                    vv = np.clip(w0v * ua[a, 1] + w1v * ua[b, 1] + w2v * ua[c, 1], 0.0, 1.0)
                    tx = np.clip((uu * (tw - 1)).astype(np.int32), 0, tw - 1)
                    ty = np.clip((vv * (th - 1)).astype(np.int32), 0, th - 1)
                    col = tex[ty, tx].astype(np.float32)

                    if is_add:
                        cb[yi, xi] = np.clip(cb[yi, xi] + col * 0.90, 0.0, 255.0)
                    elif is_unlit:
                        cb[yi, xi] = np.clip(col * 1.05, 0.0, 255.0)
                    else:
                        nnx = w0v * nx1[a] + w1v * nx1[b] + w2v * nx1[c]
                        nny = w0v * ny1[a] + w1v * ny1[b] + w2v * ny1[c]
                        nnz = w0v * nz1[a] + w1v * nz1[b] + w2v * nz1[c]
                        nl = np.maximum(np.sqrt(nnx * nnx + nny * nny + nnz * nnz), 1e-6)
                        ndotl = np.abs(nnx * light_dir[0] + nny * light_dir[1] + nnz * light_dir[2]) / nl
                        shade = 0.44 + 0.64 * ndotl
                        cb[yi, xi] = np.clip(col * shade[:, None], 0.0, 255.0)

            sheet[r_idx * H_c:(r_idx + 1) * H_c, c_idx * W_c:(c_idx + 1) * W_c] = cb.astype(np.uint8)

    Image.fromarray(sheet, "RGB").save(out_png, "PNG")
    print(f"  Wrote multi-angle verification render: {out_png}", flush=True)


def main():
    print("1. Building calibrated DarkPlaces & sRGB John Wave + Surf + FX textures...", flush=True)
    calm_mesh = build_textures_and_calm_john()

    print("2. Loading 3D Screaming John Head, Tidal-Wave Ring & Mega-Man Bar Assemblies...", flush=True)
    assets = load_scream_john_and_wave(calm_mesh)

    print("3. Generating 3 Hilarious 72-Frame Quake MD3 Aircraft (+ progs/jw_aircraft.md3 flagship)...", flush=True)
    specs = [
        ("v1", 'F-69 "THE MOUTH-BREATHER" (Cigar-Chomping Mustache-Propeller Biplane)'),
        ("v2", 'SR-99 "IN-ONE-EAR" (Ear-Skewered Beats-By-Mega-Man Supersonic Jet)'),
        ("v3", 'CH-99 "THE HAIR-ICOPTER" (Push-Me-Pull-You Propeller-Beanie Chinook)'),
    ]
    paths = [build_aircraft_md3(vid, title, assets) for vid, title in specs]

    print("4. Writing DarkPlaces shader & QuakeC frame table...", flush=True)
    write_shader_and_frame_docs()

    print("5. Rendering 3x5 multi-angle verification sheet from written MD3s...", flush=True)
    render_verification_sheet(paths, os.path.join(OUT_DIR, "jw_aircraft_check.png"))
    print("Done!", flush=True)


if __name__ == "__main__":
    main()
