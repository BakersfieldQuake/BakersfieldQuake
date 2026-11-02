"""Assembles the animated multi-role Quake MD3 models, skins, shaders, frame docs,
and side-by-side multi-angle verification renders for:
  1. progs/mm_suit_rider.md3  (Screaming Tan-Blazer Suit Rider on Reclined Bucket-Seat Rig)
  2. progs/mm_squat_rider.md3 (Squatting Plaid-Shirt Rider on Sparking Handlebar Chariot)

Both models support Vehicle, Projectile, and Monster roles via 5 seamless animation clips (60 frames).
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib
import mmw_geometry as mg
import mm_riders_rig as rig
import reconstruct_riders_3d as rec


# --------------------------------------------------------------------------- MD3 Surface Helper (Auto-Chunking <= 3600v)
def human_npz_to_meshpart(npz_path, mat_name):
    d = np.load(npz_path)
    vp = d["verts"]
    vn = d["norms"]
    tv = d["tris"]
    tuv = d["tri_uv"]

    mp = mg.MeshPart(mat_name)
    vert_map = {}
    for ti in range(len(tv)):
        tri_idx = []
        for k in range(3):
            vi = int(tv[ti, k])
            u, v = float(tuv[ti, k, 0]), float(tuv[ti, k, 1])
            # Flip V to match PNG top-left MD3 ST convention (consistent with PY = TS - 1 - gy in baker!)
            st = (u, 1.0 - v)
            key = (vi, round(st[0], 5), round(st[1], 5))
            if key not in vert_map:
                vert_map[key] = len(mp.verts)
                mp.verts.append((float(vp[vi, 0]), float(vp[vi, 1]), float(vp[vi, 2])))
                nrm = mg.vnorm((float(vn[vi, 0]), float(vn[vi, 1]), float(vn[vi, 2])))
                mp.norms.append(nrm)
                mp.st.append(st)
            tri_idx.append(vert_map[key])
        mp.tris.append((tri_idx[0], tri_idx[1], tri_idx[2]))
    return mp


# --------------------------------------------------------------------------- Smooth Articulated Deformation for Human Riders
def deform_suit_human(V0, N0, chassis_pitch, chassis_roll, chassis_dz, fist_pump, leg_kick, head_yaw):
    """Applies smooth anatomical secondary motion (head yaw, fist pumping, leg kick) + chassis rigid motion."""
    V = V0.copy()
    N = N0.copy()

    # 1. Head turn / nod above neck (Z > 36.5)
    if abs(head_yaw) > 1e-4:
        w_head = np.clip((V0[:, 2] - 36.2) / 2.8, 0.0, 1.0)
        mask = w_head > 0.0
        if mask.any():
            ang = np.radians(head_yaw * w_head[mask])
            ca, sa = np.cos(ang), np.sin(ang)
            dx = V[mask, 0] - (-8.2)
            dy = V[mask, 1]
            V[mask, 0] = -8.2 + dx * ca - dy * sa
            V[mask, 1] = dx * sa + dy * ca
            nx, ny = N[mask, 0], N[mask, 1]
            N[mask, 0] = nx * ca - ny * sa
            N[mask, 1] = nx * sa + ny * ca

    # 2. Triumphant raised-arms fist pump (|Y| > 8.2 and Z > 26.5)
    if abs(fist_pump) > 1e-4:
        w_arm = np.clip((np.abs(V0[:, 1]) - 8.0) / 3.5, 0.0, 1.0) * np.clip((V0[:, 2] - 26.5) / 5.0, 0.0, 1.0)
        # Alternate left/right slightly or pump together
        V[:, 2] += fist_pump * w_arm
        V[:, 0] += 0.35 * fist_pump * w_arm

    # 3. Outstretched V-legs lively bounce/kick (X > 2.0 and Z < 34.0)
    if abs(leg_kick) > 1e-4:
        w_leg = np.clip((V0[:, 0] - 1.5) / 14.0, 0.0, 1.0) * np.clip((34.5 - V0[:, 2]) / 4.0, 0.0, 1.0)
        sgn_y = np.where(V0[:, 1] >= 0.0, 1.0, -1.0)
        V[:, 2] += leg_kick * w_leg * sgn_y

    return apply_chassis_xform(V, N, rig.SUIT_SPEC["wheel_r"], chassis_pitch, chassis_roll, chassis_dz)


def deform_squat_human(V0, N0, chassis_pitch, chassis_roll, chassis_dz, torso_bob, head_yaw):
    """Applies smooth squatting rider shock-absorption & head scan while keeping hands locked to handlebars!"""
    V = V0.copy()
    N = N0.copy()

    # 1. Head scan above collar (Z > 38.0)
    if abs(head_yaw) > 1e-4:
        w_head = np.clip((V0[:, 2] - 37.8) / 2.8, 0.0, 1.0)
        mask = w_head > 0.0
        if mask.any():
            ang = np.radians(head_yaw * w_head[mask])
            ca, sa = np.cos(ang), np.sin(ang)
            dx = V[mask, 0] - (-1.10)
            dy = V[mask, 1]
            V[mask, 0] = -1.10 + dx * ca - dy * sa
            V[mask, 1] = dx * sa + dy * ca
            nx, ny = N[mask, 0], N[mask, 1]
            N[mask, 0] = nx * ca - ny * sa
            N[mask, 1] = nx * sa + ny * ca

    # 2. Torso breathing / road shock bounce (fades to 0 near gripping hands at |Y|~13, Z~19!)
    if abs(torso_bob) > 1e-4:
        dist_hand = np.sqrt((np.abs(V0[:, 1]) - 13.0) ** 2 + (V0[:, 2] - 19.0) ** 2)
        hand_lock = np.clip((dist_hand - 2.2) / 4.0, 0.0, 1.0)
        w_torso = np.clip((V0[:, 2] - 18.0) / 14.0, 0.0, 1.0) * hand_lock
        V[:, 2] += torso_bob * w_torso

    return apply_chassis_xform(V, N, rig.SQUAT_SPEC["wheel_r"], chassis_pitch, chassis_roll, chassis_dz)


def apply_chassis_xform(V, N, z_ax, pitch_deg, roll_deg, dz):
    """Pitches chassis around wheel axle (X=0, Z=z_ax) and rolls around (Y=0, Z=z_ax)."""
    out_V = V.copy()
    out_N = N.copy()

    if abs(pitch_deg) > 1e-5:
        # +pitch_deg rears nose (+X) UP toward +Z!
        pr = math.radians(pitch_deg)
        cp, sp = math.cos(pr), math.sin(pr)
        x = out_V[:, 0]
        z = out_V[:, 2] - z_ax
        out_V[:, 0] = x * cp - z * sp
        out_V[:, 2] = z_ax + x * sp + z * cp
        nx, nz = out_N[:, 0], out_N[:, 2]
        out_N[:, 0] = nx * cp - nz * sp
        out_N[:, 2] = nx * sp + nz * cp

    if abs(roll_deg) > 1e-5:
        rr = math.radians(roll_deg)
        cr, sr = math.cos(rr), math.sin(rr)
        y = out_V[:, 1]
        z = out_V[:, 2] - z_ax
        out_V[:, 1] = y * cr - z * sr
        out_V[:, 2] = z_ax + y * sr + z * cr
        ny, nz = out_N[:, 1], out_N[:, 2]
        out_N[:, 1] = ny * cr - nz * sr
        out_N[:, 2] = ny * sr + nz * cr

    if abs(dz) > 1e-5:
        out_V[:, 2] += dz

    out_N /= np.maximum(np.linalg.norm(out_N, axis=1, keepdims=True), 1e-6)
    return out_V, out_N


def xform_wheel(V0, N0, wheel_y, z_ax, spin_deg, chassis_roll, chassis_dz):
    """Spins wheel around its own axle (0, wheel_y, 0), then applies chassis roll & bounce."""
    sr = math.radians(spin_deg)
    cs, ss = math.cos(sr), math.sin(sr)
    V = V0.copy()
    N = N0.copy()
    # Spin in XZ around wheel center
    x, z = V[:, 0], V[:, 2]
    V[:, 0] = x * cs - z * ss
    V[:, 2] = x * ss + z * cs
    nx, nz = N[:, 0], N[:, 2]
    N[:, 0] = nx * cs - nz * ss
    N[:, 2] = nx * ss + nz * cs

    # Translate to (0, wheel_y, z_ax)
    V[:, 1] += wheel_y
    V[:, 2] += z_ax
    return apply_chassis_xform(V, N, z_ax, 0.0, chassis_roll, chassis_dz)


# --------------------------------------------------------------------------- 60-Frame Multi-Role Animation Schedule
def get_anim_params(fi, kind):
    """Returns (pitch_deg, roll_deg, dz, wheel_l_spin, wheel_r_spin, sec1, sec2, head_yaw, spark_scale)
    for frame fi in 0..59:
      0..11  : idle       (12f @ 10fps) - Balanced hover rock
      12..27 : drive      (16f @ 16fps) - Forward driving roll + wheel spin + sparks
      28..39 : projectile (12f @ 20fps) - High-speed launched projectile / boost
      40..51 : charge     (12f @ 14fps) - Monster slalom pursuit / banking wobble
      52..59 : attack     ( 8f @ 12fps) - Monster wheelie-ram & spark slam!
    """
    is_squat = (kind == "squat")
    if 0 <= fi <= 11:
        # Clip 1: IDLE (frame 0 is exact clean reference pose for turntable comparison!)
        if fi == 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, (0.55 if is_squat else 0.0)
        t = 2.0 * math.pi * (fi / 12.0)
        pitch = 1.35 * math.sin(t)
        roll = 0.75 * math.sin(t + 0.8)
        dz = 0.18 * math.sin(2.0 * t)
        wspin = 7.0 * math.sin(t)
        sec1 = 0.35 * math.sin(t)
        sec2 = 0.30 * math.cos(t)
        hyaw = 2.8 * math.sin(t)
        spk = (0.45 + 0.22 * math.sin(3.0 * t)) if is_squat else 0.0
        return pitch, roll, dz, wspin, wspin, sec1, sec2, hyaw, spk

    elif 12 <= fi <= 27:
        # Clip 2: DRIVE (16 frames, full 360 forward wheel spin!)
        k = fi - 12
        t = 2.0 * math.pi * (k / 16.0)
        wspin = -360.0 * (k / 16.0)
        pitch = -1.5 + 1.4 * math.sin(2.0 * t)
        roll = 1.4 * math.sin(t)
        dz = 0.42 * abs(math.sin(2.0 * t))
        sec1 = 0.85 * math.sin(2.0 * t)      # fist pump / torso shock
        sec2 = 0.90 * math.sin(t)            # alternating leg kick
        hyaw = 3.2 * math.sin(t)
        spk = (0.88 + 0.28 * math.sin(4.0 * t)) if is_squat else 0.0
        return pitch, roll, dz, wspin, wspin, sec1, sec2, hyaw, spk

    elif 28 <= fi <= 39:
        # Clip 3: PROJECTILE / BOOST (12 frames, 2x ultra-fast spin + blazing sparks on BOTH!)
        k = fi - 28
        t = 2.0 * math.pi * (k / 12.0)
        wspin = -720.0 * (k / 12.0)
        pitch = -5.5 + 1.1 * math.sin(3.0 * t)  # aggressive nose-down scraping angle!
        roll = 2.2 * math.sin(2.0 * t)
        dz = 0.30 * math.sin(3.0 * t)
        sec1 = 0.65 * math.sin(3.0 * t)
        sec2 = 0.50 * math.cos(2.0 * t)
        hyaw = 0.0
        spk = 1.25 + 0.30 * math.sin(4.0 * t)
        return pitch, roll, dz, wspin, wspin, sec1, sec2, hyaw, spk

    elif 40 <= fi <= 51:
        # Clip 4: MONSTER CHARGE / SLALOM PURSUIT (12 frames, banking +-8.5 deg!)
        k = fi - 40
        t = 2.0 * math.pi * (k / 12.0)
        base_spin = -360.0 * (k / 12.0)
        diff = 22.0 * math.cos(t)
        roll = 8.2 * math.sin(t)
        pitch = -2.2 + 2.0 * math.sin(2.0 * t)
        dz = 0.55 * abs(math.sin(t))
        sec1 = 1.35 * math.sin(2.0 * t)
        sec2 = 1.40 * math.cos(t)
        hyaw = -9.5 * math.sin(t)
        spk = (0.95 + 0.30 * abs(math.cos(2.0 * t))) if is_squat else (0.55 * max(0.0, -pitch - 2.0))
        return pitch, roll, dz, base_spin - diff, base_spin + diff, sec1, sec2, hyaw, spk

    else:
        # Clip 5: MONSTER ATTACK (52..59, 8 frames: dramatic wheelie rear-up -> nose slam spark burst!)
        k = fi - 52
        # k=0,1,2: rear up to +16 deg; k=3: apex +18 deg; k=4,5: slam down to -10 deg; k=6,7: recover!
        pitch_curve = [5.0, 12.5, 17.5, 15.0, -4.0, -9.5, -5.0, -1.0]
        dz_curve = [0.2, 0.8, 1.4, 1.2, 0.3, 0.0, 0.2, 0.0]
        spk_curve = [0.0, 0.0, 0.0, 0.0, 0.85, 1.65, 1.15, 0.40]
        wspin = -360.0 * (k / 8.0)
        pitch = pitch_curve[k]
        dz = dz_curve[k]
        sec1 = 1.8 if k in (2, 3) else (-1.2 if k == 5 else 0.0)
        sec2 = 1.5 if k in (2, 3) else 0.0
        spk = spk_curve[k] if not is_squat else max(spk_curve[k], 0.35 if k >= 4 else 0.0)
        return pitch, 0.0, dz, wspin, wspin, sec1, sec2, 0.0, spk


# --------------------------------------------------------------------------- Build Single MD3 Model
def build_single_rider_md3(kind, out_dir, progs_dir):
    sp = rig.SUIT_SPEC if kind == "suit" else rig.SQUAT_SPEC
    model_name = f"mm_{kind}_rider"
    human_npz = os.path.join(out_dir, f"mm_{kind}_human_uv.npz")

    human_mp = human_npz_to_meshpart(human_npz, f"progs/mm_{kind}_human")
    frame_mp = rig.build_suit_frame() if kind == "suit" else rig.build_squat_frame()
    wheel_l_mp = rig.build_suit_wheel_local(+1.0) if kind == "suit" else rig.build_squat_wheel_local(+1.0)
    wheel_r_mp = rig.build_suit_wheel_local(-1.0) if kind == "suit" else rig.build_squat_wheel_local(-1.0)
    spark_base_mp = rig.build_spark_burst((0.0, 0.0, 0.0), scale=1.0)

    # Split rig into two surfaces (rider_frame + rider_wheels) so EVERY surface stays strictly < 4096 MD3 vertex limit!
    total_wheels_v = len(wheel_l_mp.verts) + len(wheel_r_mp.verts)
    print(
        f"[{model_name}] human={len(human_mp.verts)}v/{len(human_mp.tris)}t, "
        f"frame={len(frame_mp.verts)}v/{len(frame_mp.tris)}t, "
        f"wheels={total_wheels_v}v/{len(wheel_l_mp.tris)+len(wheel_r_mp.tris)}t, "
        f"fx={len(spark_base_mp.verts)}v"
    )

    Vh0 = np.array(human_mp.verts, dtype=np.float32)
    Nh0 = np.array(human_mp.norms, dtype=np.float32)
    Vf0 = np.array(frame_mp.verts, dtype=np.float32)
    Nf0 = np.array(frame_mp.norms, dtype=np.float32)
    Vwl0 = np.array(wheel_l_mp.verts, dtype=np.float32)
    Nwl0 = np.array(wheel_l_mp.norms, dtype=np.float32)
    Vwr0 = np.array(wheel_r_mp.verts, dtype=np.float32)
    Nwr0 = np.array(wheel_r_mp.norms, dtype=np.float32)
    Vsp0 = np.array(spark_base_mp.verts, dtype=np.float32)
    Nsp0 = np.array(spark_base_mp.norms, dtype=np.float32)

    wheels_st = list(wheel_l_mp.st) + list(wheel_r_mp.st)
    off_wr = len(wheel_l_mp.verts)
    wheels_tris = (
        list(wheel_l_mp.tris)
        + [(a + off_wr, b + off_wr, c + off_wr) for (a, b, c) in wheel_r_mp.tris]
    )

    human_frames = []
    frame_frames = []
    wheels_frames = []
    fx_frames = []

    z_ax = sp["wheel_r"]
    ty = sp["track_y"]
    tip0 = np.array([sp["shaft_p_tip"]], dtype=np.float32)

    for fi in range(60):
        pitch, roll, dz, w_l, w_r, sec1, sec2, hyaw, spk = get_anim_params(fi, kind)

        if kind == "suit":
            Vh, Nh = deform_suit_human(Vh0, Nh0, pitch, roll, dz, sec1, sec2, hyaw)
        else:
            Vh, Nh = deform_squat_human(Vh0, Nh0, pitch, roll, dz, sec1, hyaw)

        Vf, Nf = apply_chassis_xform(Vf0, Nf0, z_ax, pitch, roll, dz)
        Vwl, Nwl = xform_wheel(Vwl0, Nwl0, +ty, z_ax, w_l, roll, dz)
        Vwr, Nwr = xform_wheel(Vwr0, Nwr0, -ty, z_ax, w_r, roll, dz)

        Vwh = np.vstack([Vwl, Vwr])
        Nwh = np.vstack([Nwl, Nwr])

        # Spark burst tracks the transformed bullet tip!
        tip_xf, _ = apply_chassis_xform(tip0, np.array([[1.0, 0.0, 0.0]], dtype=np.float32), z_ax, pitch, roll, dz)
        tx, ty_p, tz = float(tip_xf[0, 0]), float(tip_xf[0, 1]), float(tip_xf[0, 2])
        if spk > 1e-3:
            ang_s = fi * 1.37
            cs, ss = math.cos(ang_s), math.sin(ang_s)
            Vsp = Vsp0 * spk
            rx = Vsp[:, 0] * cs - Vsp[:, 1] * ss
            ry = Vsp[:, 0] * ss + Vsp[:, 1] * cs
            Vsp_f = np.column_stack([rx + tx, ry + ty_p, np.maximum(0.20, Vsp[:, 2] + min(tz, 3.2))])
        else:
            Vsp_f = np.broadcast_to(np.array([[tx, ty_p, tz]], dtype=np.float32), Vsp0.shape).copy()

        human_frames.append(([tuple(p) for p in Vh.tolist()], [tuple(n) for n in Nh.tolist()]))
        frame_frames.append(([tuple(p) for p in Vf.tolist()], [tuple(n) for n in Nf.tolist()]))
        wheels_frames.append(([tuple(p) for p in Vwh.tolist()], [tuple(n) for n in Nwh.tolist()]))
        fx_frames.append(([tuple(p) for p in Vsp_f.tolist()], [tuple(n) for n in Nsp0.tolist()]))

    surfaces = [
        dict(
            name="rider_human",
            shader=f"progs/mm_{kind}_human",
            tris=human_mp.tris,
            st=human_mp.st,
            frames=human_frames,
        ),
        dict(
            name="rider_frame",
            shader=f"progs/mm_{kind}_rig",
            tris=frame_mp.tris,
            st=frame_mp.st,
            frames=frame_frames,
        ),
        dict(
            name="rider_wheels",
            shader=f"progs/mm_{kind}_rig",
            tris=wheels_tris,
            st=wheels_st,
            frames=wheels_frames,
        ),
        dict(
            name="spark_fx",
            shader="progs/mm_rider_fx",
            tris=spark_base_mp.tris,
            st=spark_base_mp.st,
            frames=fx_frames,
        ),
    ]

    md3_path = os.path.join(progs_dir, f"{model_name}.md3")
    md3lib.write(md3_path, dict(name=model_name, surfaces=surfaces, nframes=60))
    print(f"Wrote {md3_path} ({os.path.getsize(md3_path):,} bytes)")

    # Write .skin file(s)
    skin0 = (
        f"rider_human,progs/mm_{kind}_human\n"
        f"rider_frame,progs/mm_{kind}_rig\n"
        f"rider_wheels,progs/mm_{kind}_rig\n"
        f"spark_fx,progs/mm_rider_fx\n"
    )
    with open(os.path.join(progs_dir, f"{model_name}.md3_0.skin"), "w", encoding="ascii") as fh:
        fh.write(skin0)

    if kind == "squat":
        skin1 = (
            "rider_human,progs/mm_squat_human_grin\n"
            "rider_frame,progs/mm_squat_rig\n"
            "rider_wheels,progs/mm_squat_rig\n"
            "spark_fx,progs/mm_rider_fx\n"
        )
        with open(os.path.join(progs_dir, f"{model_name}.md3_1.skin"), "w", encoding="ascii") as fh:
            fh.write(skin1)

    return md3_path


# --------------------------------------------------------------------------- Shaders & Frame Table Documentation
def write_shaders_and_docs(scripts_dir, progs_dir):
    os.makedirs(scripts_dir, exist_ok=True)
    shader_txt = """// Quake / DarkPlaces shaders for Mega-Man 3D Riders (mm_suit_rider.md3 & mm_squat_rider.md3)
// Generated by source/mm_tools/build_mm_riders.py

progs/mm_suit_human
{
\tcull none
\t{
\t\tmap progs/mm_suit_human
\t\trgbGen lightingDiffuse
\t}
}

progs/mm_suit_rig
{
\tcull none
\t{
\t\tmap progs/mm_suit_rig
\t\trgbGen lightingDiffuse
\t}
}

progs/mm_squat_human
{
\tcull none
\t{
\t\tmap progs/mm_squat_human
\t\trgbGen lightingDiffuse
\t}
}

progs/mm_squat_human_grin
{
\tcull none
\t{
\t\tmap progs/mm_squat_human_grin
\t\trgbGen lightingDiffuse
\t}
}

progs/mm_squat_rig
{
\tcull none
\t{
\t\tmap progs/mm_squat_rig
\t\trgbGen lightingDiffuse
\t}
}

progs/mm_rider_fx
{
\tcull none
\t{
\t\tmap progs/mm_rider_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""
    shader_path = os.path.join(scripts_dir, "mm_riders.shader")
    with open(shader_path, "w", encoding="ascii") as fh:
        fh.write(shader_txt)
    print(f"Wrote {shader_path}")

    frames_txt = """// Quake MD3 Frame & Skin Specification for:
//   - progs/mm_suit_rider.md3   (Screaming Tan-Blazer Suit Rider on Reclined Stainless Bucket-Seat Rig)
//   - progs/mm_squat_rider.md3  (Squatting Plaid-Shirt Rider on Sparking Chrome Handlebar Chariot)
//
// Coordinate System & Bounds (+X forward, +Y left, +Z up, tire ground contact at z = 0):
//   Recommended Monster / Vehicle setsize : mins = '-20 -20 0', maxs = '24 20 48'
//   Skins on mm_squat_rider.md3           : skin 0 = Locked-in intense stare, skin 1 = Joyful toothy grin
//
// Animation Clips (60 frames total -- supports Vehicle, Projectile, and Monster roles):
//   idle       : frames  0..11 (12 frames @ 10.0 fps) - Self-balancing gyroscopic idle rock (frame 0 = exact rest pose)
//   drive      : frames 12..27 (16 frames @ 16.0 fps) - Forward rolling drive (seamless 360 wheel spin + sparks)
//   projectile : frames 28..39 (12 frames @ 20.0 fps) - High-speed launched projectile / turbo boost + full spark trail
//   charge     : frames 40..51 (12 frames @ 14.0 fps) - Monster slalom pursuit / banking charge (+-8.2 deg roll)
//   attack     : frames 52..59 ( 8 frames @ 12.0 fps) - Monster wheelie rear-up (52..55) & chrome bullet slam (56..59)

$frame idle0 idle1 idle2 idle3 idle4 idle5 idle6 idle7 idle8 idle9 idle10 idle11
$frame drive0 drive1 drive2 drive3 drive4 drive5 drive6 drive7 drive8 drive9 drive10 drive11 drive12 drive13 drive14 drive15
$frame proj0 proj1 proj2 proj3 proj4 proj5 proj6 proj7 proj8 proj9 proj10 proj11
$frame charge0 charge1 charge2 charge3 charge4 charge5 charge6 charge7 charge8 charge9 charge10 charge11
$frame attack0 attack1 attack2 attack3 attack4 attack5 attack6 attack7
"""
    frames_path = os.path.join(progs_dir, "mm_riders_frames.txt")
    with open(frames_path, "w", encoding="ascii") as fh:
        fh.write(frames_txt)
    print(f"Wrote {frames_path}")


# --------------------------------------------------------------------------- Software Z-Buffered MD3 Comparison Renderer
def render_md3_frame(md3_model, tex_dict, phi_deg, elev_deg, f_px, d_cam, cx, cy, W, H, frame_idx=0):
    """Software Z-buffered Gouraud+Textured renderer of the actual exported Quake MD3 model
    for 1:1 pixel comparison against the source studio turntable video frames!"""
    img = np.full((H, W, 3), 236.0, dtype=np.float32)
    zbuf = np.full((H, W), 1e9, dtype=np.float32)

    light_dir = mg.vnorm((0.35, 0.25, 0.90))
    ray_d = rec.view_ray_into_scene(phi_deg, elev_deg)

    # First render opaque surfaces, then additive FX surfaces
    opaque_surfs = [s for s in md3_model["surfaces"] if "fx" not in s["name"]]
    fx_surfs = [s for s in md3_model["surfaces"] if "fx" in s["name"]]

    for pass_additive, surfs in ((False, opaque_surfs), (True, fx_surfs)):
        for surf in surfs:
            tex = tex_dict[surf["shader"]]
            th, tw, _ = tex.shape
            vv, nn = surf["frames"][frame_idx]
            V = np.array(vv, dtype=np.float32)
            N = np.array(nn, dtype=np.float32)
            ST = np.array(surf["st"], dtype=np.float32)

            u, v, d = rec.project_pts(V[:, 0], V[:, 1], V[:, 2], phi_deg, elev_deg, f_px, d_cam, cx, cy)

            for i0, i1, i2 in surf["tris"]:
                x0, y0, z0 = u[i0], v[i0], d[i0]
                x1, y1, z1 = u[i1], v[i1], d[i1]
                x2, y2, z2 = u[i2], v[i2], d[i2]

                xmin = max(0, int(math.floor(min(x0, x1, x2))))
                xmax = min(W - 1, int(math.ceil(max(x0, x1, x2))))
                ymin = max(0, int(math.floor(min(y0, y1, y2))))
                ymax = min(H - 1, int(math.ceil(max(y0, y1, y2))))
                if xmax < xmin or ymax < ymin:
                    continue

                den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
                if abs(den) < 1e-5:
                    continue

                gx, gy = np.meshgrid(np.arange(xmin, xmax + 1, dtype=np.float32), np.arange(ymin, ymax + 1, dtype=np.float32))
                w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
                w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
                w2 = 1.0 - w0 - w1
                ins = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
                if not ins.any():
                    continue

                zz = w0 * z0 + w1 * z1 + w2 * z2
                zb_sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
                vis = ins & (zz < zb_sub)
                if not vis.any():
                    continue

                uu = w0[vis] * ST[i0, 0] + w1[vis] * ST[i1, 0] + w2[vis] * ST[i2, 0]
                vv_st = w0[vis] * ST[i0, 1] + w1[vis] * ST[i1, 1] + w2[vis] * ST[i2, 1]
                tx_i = np.clip((uu % 1.0) * (tw - 1), 0, tw - 1).astype(np.int32)
                ty_i = np.clip((vv_st % 1.0) * (th - 1), 0, th - 1).astype(np.int32)
                sample = tex[ty_i, tx_i]

                if pass_additive:
                    patch = img[ymin:ymax + 1, xmin:xmax + 1]
                    patch[vis] = np.clip(patch[vis] + sample * 0.85, 0.0, 255.0)
                else:
                    # Subtle studio softbox lighting (mostly baked sRGB fidelity + gentle rim/top directional)
                    nx = w0[vis] * N[i0, 0] + w1[vis] * N[i1, 0] + w2[vis] * N[i2, 0]
                    ny = w0[vis] * N[i0, 1] + w1[vis] * N[i1, 1] + w2[vis] * N[i2, 1]
                    nz = w0[vis] * N[i0, 2] + w1[vis] * N[i1, 2] + w2[vis] * N[i2, 2]
                    ndotl = np.clip(nx * light_dir[0] + ny * light_dir[1] + nz * light_dir[2], -1.0, 1.0)
                    shade = 0.88 + 0.16 * np.maximum(0.0, ndotl)
                    # Extra studio specular pop on metallic rig surface!
                    if "rig" in surf["shader"]:
                        ndotv = np.abs(nx * ray_d[0] + ny * ray_d[1] + nz * ray_d[2])
                        shade = shade + 0.14 * (ndotv ** 4.0)
                    zb_sub[vis] = zz[vis]
                    patch = img[ymin:ymax + 1, xmin:xmax + 1]
                    patch[vis] = np.clip(sample * shade[:, None], 0.0, 255.0)

    return img.astype(np.uint8)


def generate_comparison_sheet(kind, vid_path, md3_path, out_dir):
    md3_m = md3lib.read(md3_path)
    tex_dict = {
        f"progs/mm_{kind}_human": np.array(Image.open(os.path.join(out_dir, f"mm_{kind}_human_srgb.png")), dtype=np.float32),
        f"progs/mm_{kind}_rig": np.array(Image.open(os.path.join(out_dir, f"mm_{kind}_rig_srgb.png")), dtype=np.float32),
        "progs/mm_rider_fx": np.array(Image.open(os.path.join(out_dir, "mm_rider_fx_srgb.png")), dtype=np.float32),
    }

    if kind == "suit":
        landmarks = rec.SUIT_LANDMARKS
        test_frames = [
            (120, "0 deg (Front)"),
            (22,  "-52 deg (Oblique)"),
            (41,  "-90 deg (Right Profile)"),
            (76,  "180 deg (Rear)"),
            (98,  "-225 deg (Left Oblique)"),
        ]
        f_px, d_cam, elev_deg = 5250.0, 295.0, 4.6
    else:
        landmarks = rec.SQUAT_LANDMARKS
        test_frames = [
            (18,  "0 deg (Front Serious)"),
            (34,  "+38 deg (Oblique)"),
            (48,  "+90 deg (Left Profile)"),
            (75,  "180 deg (Rear)"),
            (98,  "270 deg (Right Profile)"),
        ]
        f_px, d_cam, elev_deg = 5800.0, 295.0, 4.6

    f_rgb, _ = rec.load_selected_frames(vid_path, [f for f, _ in test_frames])
    H, W, _ = next(iter(f_rgb.values())).shape
    scale_ds = 0.45
    tw, th = int(W * scale_ds), int(H * scale_ds)

    pose_json = os.path.join(out_dir, f"mm_{kind}_cam_poses.json")
    cam_poses = json.load(open(pose_json, "r", encoding="ascii")) if os.path.isfile(pose_json) else {}

    rows = []
    for fi, label in test_frames:
        if str(fi) in cam_poses:
            phi, cx, cy, f_sc = cam_poses[str(fi)]
        else:
            phi, cx, cy = rec.interp_landmarks(landmarks, fi)
            f_sc = 1.0
        real_im = Image.fromarray(f_rgb[fi]).resize((tw, th), Image.Resampling.LANCZOS)
        rend_np = render_md3_frame(
            md3_m, tex_dict, phi, elev_deg,
            f_px * f_sc * scale_ds, d_cam, cx * scale_ds, cy * scale_ds, tw, th, frame_idx=0
        )
        rend_im = Image.fromarray(rend_np)

        d1 = ImageDraw.Draw(real_im)
        d1.rectangle([8, 8, 280, 34], fill=(20, 20, 20))
        d1.text((14, 13), f"REAL VIDEO f={fi:03d} | {label}", fill=(255, 230, 90))

        d2 = ImageDraw.Draw(rend_im)
        d2.rectangle([8, 8, 300, 34], fill=(20, 20, 20))
        d2.text((14, 13), f"QUAKE MD3 3D REPLICA | {label}", fill=(90, 255, 160))

        rows.append(np.hstack([np.array(real_im), np.array(rend_im)]))

    sheet = np.vstack(rows)
    out_p = os.path.join(out_dir, f"compare_{kind}_md3.png")
    Image.fromarray(sheet).save(out_p)
    print(f"Saved side-by-side verification sheet: {out_p}")

    if kind == "squat":
        tex_grin = dict(tex_dict)
        tex_grin["progs/mm_squat_human"] = np.array(
            Image.open(os.path.join(out_dir, "mm_squat_human_grin_srgb.png")), dtype=np.float32
        )
        grin_frames = [(0, "-10 deg (Skin 1: Joyful Grin)"), (34, "+38 deg (Skin 1 Oblique)")]
        fg_g, _ = rec.load_selected_frames(vid_path, [f for f, _ in grin_frames])
        g_rows = []
        for fi, label in grin_frames:
            phi, cx, cy, f_sc = cam_poses.get(str(fi), [*rec.interp_landmarks(landmarks, fi), 1.0])
            real_im = Image.fromarray(fg_g[fi]).resize((tw, th), Image.Resampling.LANCZOS)
            rend_np = render_md3_frame(
                md3_m, tex_grin, phi, elev_deg,
                f_px * f_sc * scale_ds, d_cam, cx * scale_ds, cy * scale_ds, tw, th, frame_idx=0
            )
            rend_im = Image.fromarray(rend_np)
            d1 = ImageDraw.Draw(real_im)
            d1.rectangle([8, 8, 300, 34], fill=(20, 20, 20))
            d1.text((14, 13), f"REAL VIDEO f={fi:03d} | {label}", fill=(255, 230, 90))
            d2 = ImageDraw.Draw(rend_im)
            d2.rectangle([8, 8, 320, 34], fill=(20, 20, 20))
            d2.text((14, 13), f"QUAKE MD3 SKIN 1 | {label}", fill=(90, 255, 160))
            g_rows.append(np.hstack([np.array(real_im), np.array(rend_im)]))
        grin_p = os.path.join(out_dir, "compare_squat_grin_md3.png")
        Image.fromarray(np.vstack(g_rows)).save(grin_p)
        print(f"Saved Skin 1 verification sheet: {grin_p}")


if __name__ == "__main__":
    vid1 = r"C:\Users\qxdc\.gemini\antigravity\brain\c5cf8ed8-8a7a-43da-a12a-3541b638fe8f\.user_uploaded\media_1793428832508_e43c906a.mp4"
    vid2 = r"C:\Users\qxdc\.gemini\antigravity\brain\c5cf8ed8-8a7a-43da-a12a-3541b638fe8f\.user_uploaded\media_1793428832489_5c1853ec.mp4"
    out_d = os.path.join(HERE, "out", "mm_riders")
    progs_d = os.path.abspath(os.path.join(HERE, "..", "..", "progs"))
    scripts_d = os.path.abspath(os.path.join(HERE, "..", "..", "scripts"))

    md3_suit = build_single_rider_md3("suit", out_d, progs_d)
    md3_squat = build_single_rider_md3("squat", out_d, progs_d)
    write_shaders_and_docs(scripts_d, progs_d)

    generate_comparison_sheet("suit", vid1, md3_suit, out_d)
    generate_comparison_sheet("squat", vid2, md3_squat, out_d)
