"""3D Multi-Body Vehicle Idle, Catch-Fire & 480 Hz Explosion/Tire-Rolling Physics Simulator
+ Multi-Clip glTF 2.0 (.glb) Exporter for BakersfieldQuake's 4 Unique Vehicles.

Generates for each vehicle ('truck', 'sedan', 'van', 'coupe'):
  1. Named glTF 2.0 animations inside standalone <veh_kind>.glb:
       - 'Idle'      (120 frames @ 60 FPS = 2.00s seamless loop, unique per vehicle!)
       - 'CatchFire' (180 frames @ 60 FPS = 3.00s: bullet-hit suspension jolts -> hood pops ajar -> burning cook-off!)
       - 'Explode'   (360 frames @ 60 FPS = 6.00s @ 480 Hz physics: pre-blast cookoff -> detonation starburst ->
                      crumpled charred wreck leaps & slams down -> ALL 4 UNIQUE TIRES bounce elastically, catch
                      traction, carve banked gyroscopic curves, coin-wobble & flop flat -> hood, both doors,
                      rollbar/trunk/barn-doors/wing, bumpers, exhaust & 10 shrapnel chunks fly & clang everywhere!)
  2. MD3 vertex-animation helper tracks for DarkPlaces in-game models.
"""
import io
import json
import math
import struct
import numpy as np


# --------------------------------------------------------------------------- Quaternion & Rotation Math
def q_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ], dtype=np.float64)


def q_norm(q):
    n = math.sqrt(float(np.dot(q, q)))
    return q / n if n > 1e-12 else np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)


def q_from_axis_angle(axis, rad):
    ax = np.asarray(axis, dtype=np.float64)
    n = math.sqrt(float(np.dot(ax, ax)))
    if n < 1e-12 or abs(rad) < 1e-12:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    ax = ax / n
    h = 0.5 * rad
    s = math.sin(h)
    return np.array([ax[0] * s, ax[1] * s, ax[2] * s, math.cos(h)], dtype=np.float64)


def q_euler_xyz(rx_deg, ry_deg, rz_deg):
    qx = q_from_axis_angle((1.0, 0.0, 0.0), math.radians(rx_deg))
    qy = q_from_axis_angle((0.0, 1.0, 0.0), math.radians(ry_deg))
    qz = q_from_axis_angle((0.0, 0.0, 1.0), math.radians(rz_deg))
    return q_norm(q_mul(qz, q_mul(qy, qx)))


def q_to_mat3(q):
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz),       2.0 * (xz + wy)],
        [2.0 * (xy + wz),       1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy),       2.0 * (yz + wx),       1.0 - 2.0 * (xx + yy)],
    ], dtype=np.float64)


def mat3_to_q(m):
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif (m[0, 0] > m[1, 1]) and (m[0, 0] > m[2, 2]):
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    return q_norm(np.array([x, y, z, w], dtype=np.float64))


def integrate_q(q, omega_world, dt):
    w_norm = math.sqrt(float(np.dot(omega_world, omega_world)))
    if w_norm < 1e-9:
        return q
    dq = q_from_axis_angle(omega_world / w_norm, w_norm * dt)
    return q_norm(q_mul(dq, q))


# --------------------------------------------------------------------------- Volumetric Blast Starburst Mesh
def build_blast_starburst_mesh():
    verts, norms, uvs, tris = [], [], [], []
    n_spikes = 20
    for i in range(n_spikes):
        phi = math.acos(1.0 - 2.0 * (i + 0.5) / n_spikes)
        theta = math.pi * (1.0 + 5.0 ** 0.5) * i
        d = np.array([math.sin(phi) * math.cos(theta), math.sin(phi) * math.sin(theta), abs(math.cos(phi)) * 0.85 + 0.15])
        d /= np.linalg.norm(d)
        up = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.85 else np.array([1.0, 0.0, 0.0])
        u = np.cross(d, up); u /= np.linalg.norm(u)
        v = np.cross(d, u)
        length = 52.0 + (i % 4) * 18.0
        rad_b = 9.5
        b0 = len(verts)
        verts.extend([
            (u * rad_b).tolist(),
            (-u * rad_b * 0.5 + v * rad_b * 0.86).tolist(),
            (-u * rad_b * 0.5 - v * rad_b * 0.86).tolist(),
            (d * length).tolist(),
        ])
        norms.extend([u.tolist(), v.tolist(), (-v).tolist(), d.tolist()])
        uvs.extend([(0.88, 0.88), (0.92, 0.84), (0.84, 0.92), (0.96, 0.96)])
        tris.extend([(b0, b0 + 1, b0 + 3), (b0 + 1, b0 + 2, b0 + 3), (b0 + 2, b0, b0 + 3)])
    return {"name": "blast_flash", "origin": [0.0, 0.0, 28.0], "verts": verts, "norms": norms, "uvs": uvs, "tris": tris}


# --------------------------------------------------------------------------- Sprung Pose Evaluator (Idle / Flinch / Fire)
SPRUNG_PARTS = ("chassis", "hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib")
WHEEL_PARTS = ("wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr")


def eval_sprung_body_pose(kind, phase_01, mode="idle"):
    """Computes unique mechanical sprung-body motion (dz, roll_deg, pitch_deg, yaw_deg)
    + per-part local child offsets (hood ajar angle, door rattle, antenna/exhaust vibration).
    phase_01 in [0, 1) is seamless periodic for 'idle' and 'fire'."""
    tau = 2.0 * math.pi * phase_01
    child = {
        "hood_open_deg": 0.0,
        "door_ajar_deg": 0.0,
        "detail_dz": 0.0,
        "detail_dy": 0.0,
        "detail_rx": 0.0,
        "detail_ry": 0.0,
        "extra_dz": 0.0,
    }

    if mode == "idle":
        if kind == "truck":
            # Heavy V8 cam-lope torque rock around +X + dual exhaust thrum + rollbar light shiver
            roll = 0.82 * math.sin(tau) + 0.38 * math.sin(3.0 * tau + 0.5) + 0.18 * math.sin(6.0 * tau)
            pitch = 0.26 * math.cos(tau + 0.3) + 0.12 * math.sin(4.0 * tau)
            dz = 0.42 * math.sin(2.0 * tau) + 0.16 * math.cos(5.0 * tau)
            yaw = 0.08 * math.sin(2.0 * tau)
            child["hood_open_deg"] = 0.22 * (0.5 + 0.5 * math.sin(6.0 * tau))
            child["detail_dz"] = 0.58 * math.sin(8.0 * tau)
            child["detail_dy"] = 0.32 * math.cos(6.0 * tau)
            child["extra_dz"] = 0.22 * math.sin(6.0 * tau + 1.1)

        elif kind == "sedan":
            # Smooth 90s 4-cyl idle with nostalgic rough-idle stumble dip + whip antenna figure-8 wave!
            stumble = math.exp(-(((phase_01 - 0.62) / 0.08) ** 2))
            roll = 0.32 * math.sin(tau) + 0.65 * stumble * math.sin(10.0 * tau)
            pitch = 0.34 * math.sin(tau + 0.8) - 0.42 * stumble
            dz = 0.34 * math.cos(tau) - 0.38 * stumble
            yaw = 0.05 * math.sin(tau)
            child["detail_rx"] = 2.9 * math.sin(2.0 * tau) + 1.2 * math.sin(5.0 * tau)
            child["detail_ry"] = 2.2 * math.cos(3.0 * tau)
            child["detail_dz"] = 0.30 * math.sin(7.0 * tau)

        elif kind == "van":
            # Soft commercial leaf-spring diesel/work-van sway + rattling ladder rack & mirrors!
            roll = 0.76 * math.sin(tau) + 0.24 * math.cos(2.0 * tau)
            pitch = 0.52 * math.sin(tau - 0.6) + 0.18 * math.sin(3.0 * tau)
            dz = 0.50 * math.sin(tau + 0.4) + 0.15 * math.sin(5.0 * tau)
            yaw = 0.10 * math.cos(tau)
            child["extra_dz"] = 0.36 * math.sin(7.0 * tau)
            child["door_ajar_deg"] = 0.25 * (0.5 + 0.5 * math.sin(5.0 * tau))
            child["detail_dy"] = 0.45 * math.sin(6.0 * tau)

        elif kind == "coupe":
            # High-RPM tuned sport idle + periodic throttle blip + energetic N1 canister shake!
            blip = math.exp(-(((phase_01 - 0.35) / 0.09) ** 2))
            roll = 0.28 * math.sin(2.0 * tau) + 0.85 * blip * math.sin(8.0 * tau)
            pitch = 0.22 * math.cos(2.0 * tau) - 0.55 * blip
            dz = 0.26 * math.sin(4.0 * tau) + 0.32 * blip
            yaw = 0.06 * math.sin(3.0 * tau)
            child["detail_dz"] = 0.72 * math.sin(10.0 * tau)
            child["detail_dy"] = 0.52 * math.cos(8.0 * tau)
            child["extra_dz"] = 0.30 * math.sin(8.0 * tau)
        else:
            dz = roll = pitch = yaw = 0.0

    elif mode == "flinch":
        # Sharp damped suspension impact recoil (phase_01 in [0..1])
        env = math.exp(-3.6 * phase_01) * math.sin(math.pi * min(1.0, phase_01 * 2.4))
        osc = math.exp(-3.2 * phase_01) * math.sin(2.0 * math.pi * 2.0 * phase_01)
        dz = -2.1 * env + 0.8 * osc
        roll = 3.6 * osc
        pitch = -2.5 * env
        yaw = 0.8 * osc
        child["hood_open_deg"] = max(0.0, 3.2 * osc)
        child["detail_dz"] = 1.1 * osc

    elif mode == "fire":
        # Critical burning engine cook-off: hood popped ajar 11..17 deg & rattling violently, body bucking!
        roll = 1.45 * math.sin(2.0 * tau) + 0.85 * math.sin(5.0 * tau + 0.7)
        pitch = 1.05 * math.cos(2.0 * tau) + 0.65 * math.sin(6.0 * tau)
        dz = 0.85 * math.sin(3.0 * tau) + 0.45 * math.cos(7.0 * tau)
        yaw = 0.35 * math.sin(3.0 * tau)
        child["hood_open_deg"] = 13.5 + 3.8 * math.sin(5.0 * tau) + 1.9 * math.cos(9.0 * tau)
        child["door_ajar_deg"] = 2.2 + 1.6 * math.sin(4.0 * tau)
        child["detail_dz"] = 1.15 * math.sin(9.0 * tau)
        child["extra_dz"] = 0.65 * math.cos(6.0 * tau)
    else:
        dz = roll = pitch = yaw = 0.0

    return dz, roll, pitch, yaw, child


def compute_part_trs_in_sprung_state(veh_data, kind, phase_01, mode="idle"):
    """Returns dict[part_name] -> (pos_vec3, quat_xyzw, scl_vec3) for all 25 nodes in non-exploded state."""
    parts = veh_data["parts"]
    sp = veh_data["spec"]
    dz, roll, pitch, yaw, child = eval_sprung_body_pose(kind, phase_01, mode=mode)

    # Sprung body pivots around suspension roll center (0, 0, wheel_r)
    rc = np.array([0.0, 0.0, sp["wheel_r"]], dtype=np.float64)
    q_body = q_euler_xyz(roll, pitch, yaw)
    R_body = q_to_mat3(q_body)
    t_body = np.array([0.0, 0.0, dz], dtype=np.float64)

    out = {}
    for name, p in parts.items():
        p_org = np.array(p["origin"], dtype=np.float64)

        if name in WHEEL_PARTS:
            out[name] = (p_org, np.array([0.0, 0.0, 0.0, 1.0]), np.ones(3))
            continue

        if name == "wreck_chassis" or name.startswith("shrap_"):
            out[name] = (p_org, np.array([0.0, 0.0, 0.0, 1.0]), np.full(3, 0.0001))
            continue

        # Local child transform relative to sprung body before applying body suspension rotation
        loc_pos = p_org.copy()
        loc_q = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)

        if name == "hood" and child["hood_open_deg"] > 0.001:
            # Hinge around rear cowl pivot (+Y axis negative rotation lifts +X nose UP: x' = x*c + z*s, z' = -x*s + z*c -> rad < 0)
            hp = np.array(p.get("hinge", [sp["x_cowl"], 0.0, sp["z_belt"]]), dtype=np.float64)
            q_h = q_from_axis_angle((0.0, 1.0, 0.0), -math.radians(child["hood_open_deg"]))
            R_h = q_to_mat3(q_h)
            loc_pos = hp + R_h @ (p_org - hp)
            loc_q = q_h

        elif name in ("door_l", "door_r") and child["door_ajar_deg"] > 0.001:
            sgn = 1.0 if name == "door_l" else -1.0
            hp = np.array([sp["x_door1"], sgn * sp["hw"] * 0.92, sp["z_belt"] * 0.7], dtype=np.float64)
            q_d = q_from_axis_angle((0.0, 0.0, 1.0), -sgn * math.radians(child["door_ajar_deg"]))
            R_d = q_to_mat3(q_d)
            loc_pos = hp + R_d @ (p_org - hp)
            loc_q = q_d

        elif name == "detail_vib":
            loc_pos = loc_pos + np.array([0.0, child["detail_dy"], child["detail_dz"]])
            if abs(child["detail_rx"]) > 0.001 or abs(child["detail_ry"]) > 0.001:
                loc_q = q_euler_xyz(child["detail_rx"], child["detail_ry"], 0.0)

        elif name == "extra_part":
            loc_pos = loc_pos + np.array([0.0, 0.0, child["extra_dz"]])

        w_pos = rc + R_body @ (loc_pos - rc) + t_body
        w_q = q_norm(q_mul(q_body, loc_q))
        out[name] = (w_pos, w_q, np.ones(3))

    out["blast_flash"] = (np.array([0.0, 0.0, 28.0]), np.array([0.0, 0.0, 0.0, 1.0]), np.full(3, 0.0001))
    return out


# --------------------------------------------------------------------------- 480 Hz Catastrophic Explosion Simulator
def simulate_vehicle_explosion(veh_data, kind, fps=60, duration=6.0, substeps=8):
    """Simulates a full 6.0s @ 480 Hz 3D explosion where:
      - Frames 0..26 (0.00s..0.45s): Violent burning cook-off & pressure swell
      - Frame 27 (0.45s): Fuel-tank & engine detonation!
      - Wreck chassis leaps into the air, twists, slams down with sparks & bounces to a smoking rest
      - All 4 unique wheels blast off in distinct wild trajectories, bounce elastically off the asphalt,
        engage non-holonomic banked gyroscopic rolling curves, enter Euler-disk coin wobble, and flop flat!
      - Hood, left & right doors, signature extra_part, front & rear bumpers, exhaust, and 10 shrapnel chunks
        fly, spin, bounce off their actual 3D vertices, shower sparks, and skid to rest!"""
    rng = np.random.default_rng({"truck": 1001, "sedan": 2002, "van": 3003, "coupe": 4004}[kind])
    parts = veh_data["parts"]
    sp = veh_data["spec"]
    n_frames = int(round(fps * duration)) + 1
    boom_frame = 27
    dt_frame = 1.0 / fps
    dt = dt_frame / substeps
    g_acc = np.array([0.0, 0.0, -560.0], dtype=np.float64)

    all_names = list(parts.keys()) + ["blast_flash"]
    tracks = {
        nm: {
            "pos": np.zeros((n_frames, 3), dtype=np.float32),
            "rot": np.zeros((n_frames, 4), dtype=np.float32),
            "scl": np.ones((n_frames, 3), dtype=np.float32),
        }
        for nm in all_names
    }
    sparks = []

    # 1. Pre-explosion violent burning cook-off frames (0 .. boom_frame - 1)
    for fi in range(boom_frame):
        t_frac = fi / float(boom_frame)
        # Escalating pressure swell right before boom!
        pose = compute_part_trs_in_sprung_state(veh_data, kind, (fi * 0.09) % 1.0, mode="fire")
        swell = 1.0 + 0.035 * (t_frac ** 3)
        for nm, (p, q, sc) in pose.items():
            tracks[nm]["pos"][fi] = p
            tracks[nm]["rot"][fi] = q
            tracks[nm]["scl"][fi] = sc * (swell if nm in ("chassis", "hood") else 1.0)

    # 2. Initialize rigid-body & gyroscopic wheel states at boom_frame!
    pose_at_boom = compute_part_trs_in_sprung_state(veh_data, kind, (boom_frame * 0.09) % 1.0, mode="fire")

    # Subsampled hull vertices per rigid body for fast exact 480 Hz floor contact impulses
    rb_states = {}
    wheel_states = {}

    w_rad = sp["wheel_r"]
    w_half_w = sp["wheel_w"] * 0.5

    # 4 distinct dramatic tire trajectories!
    wheel_launch_cfg = {
        "wheel_fl": dict(vel=[175.0, 295.0, 465.0], spin=-28.0, lean=18.0, side=1.0),   # High skyward left-front launcher!
        "wheel_fr": dict(vel=[235.0, -345.0, 255.0], spin=-36.0, lean=-24.0, side=-1.0), # Fast street banked curve roller!
        "wheel_rl": dict(vel=[-210.0, 320.0, 330.0], spin=26.0, lean=-20.0, side=-1.0),  # Rear-left S-curve bouncer!
        "wheel_rr": dict(vel=[-165.0, -280.0, 390.0], spin=-24.0, lean=27.0, side=1.0),  # Rear-right high camber tumbler!
    }

    for wn in WHEEL_PARTS:
        cfg = wheel_launch_cfg[wn]
        p0, _, _ = pose_at_boom[wn]
        vx, vy, vz = cfg["vel"]
        v0 = np.array([
            vx + rng.uniform(-35, 35),
            vy + rng.uniform(-35, 35),
            vz + rng.uniform(-30, 45),
        ], dtype=np.float64)
        yaw0 = math.atan2(v0[1], v0[0])
        wheel_states[wn] = {
            "pos": p0 + np.array([0.0, 0.0, 2.5]),
            "vel": v0,
            "mode": "air",
            "bounces": 0,
            "yaw": yaw0,
            "lean": math.radians(cfg["lean"]),
            "lean_vel": cfg["side"] * 0.9,
            "side": cfg["side"],
            "spin": 0.0,
            "spin_rate": cfg["spin"],
            "roll_spd": 0.0,
            "precess": 0.0,
        }

    # Rigid bodies: wreck_chassis + detachable panels + 10 shrapnel pieces
    body_launch = {
        "wreck_chassis": dict(vel=[rng.uniform(-18, 18), rng.uniform(-18, 18), 235.0],
                              omega=[rng.uniform(-1.3, 1.3), rng.uniform(-1.1, 1.1), rng.uniform(-0.8, 0.8)],
                              e=0.22, mu=0.68, lin_damp=0.45, ang_damp=1.2),
        "hood":          dict(vel=[95.0 + rng.uniform(-40, 50), rng.uniform(-95, 95), 510.0 + rng.uniform(0, 70)],
                              omega=[rng.uniform(-7.5, 7.5), -9.5 + rng.uniform(-3, 3), rng.uniform(-5, 5)],
                              e=0.38, mu=0.44, lin_damp=0.18, ang_damp=0.42),
        "door_l":        dict(vel=[rng.uniform(-65, 65), 375.0 + rng.uniform(0, 65), 295.0 + rng.uniform(0, 60)],
                              omega=[-8.5, rng.uniform(-5, 5), 6.2],
                              e=0.34, mu=0.46, lin_damp=0.20, ang_damp=0.45),
        "door_r":        dict(vel=[rng.uniform(-65, 65), -385.0 - rng.uniform(0, 65), 315.0 + rng.uniform(0, 60)],
                              omega=[8.8, rng.uniform(-5, 5), -6.5],
                              e=0.34, mu=0.46, lin_damp=0.20, ang_damp=0.45),
        "extra_part":    dict(vel=[-215.0 + rng.uniform(-45, 35), rng.uniform(-110, 110), 445.0 + rng.uniform(0, 65)],
                              omega=[rng.uniform(-7, 7), 8.4, rng.uniform(-6, 6)],
                              e=0.36, mu=0.45, lin_damp=0.18, ang_damp=0.42),
        "bumper_f":      dict(vel=[340.0 + rng.uniform(0, 65), rng.uniform(-90, 90), 215.0 + rng.uniform(0, 45)],
                              omega=[rng.uniform(-6, 6), 7.2, rng.uniform(-5, 5)],
                              e=0.35, mu=0.50, lin_damp=0.22, ang_damp=0.50),
        "bumper_r":      dict(vel=[-325.0 - rng.uniform(0, 65), rng.uniform(-90, 90), 205.0 + rng.uniform(0, 45)],
                              omega=[rng.uniform(-6, 6), -7.4, rng.uniform(-5, 5)],
                              e=0.35, mu=0.50, lin_damp=0.22, ang_damp=0.50),
        "detail_vib":    dict(vel=[-265.0, -145.0, 345.0],
                              omega=[9.5, -7.2, 8.0],
                              e=0.42, mu=0.40, lin_damp=0.18, ang_damp=0.40),
    }
    for si in range(10):
        ang = 2.0 * math.pi * si / 10.0 + rng.uniform(-0.22, 0.22)
        spd_xy = 260.0 + rng.uniform(0.0, 260.0)
        body_launch[f"shrap_{si}"] = dict(
            vel=[math.cos(ang) * spd_xy, math.sin(ang) * spd_xy, 280.0 + rng.uniform(40.0, 310.0)],
            omega=[rng.uniform(-14, 14), rng.uniform(-14, 14), rng.uniform(-14, 14)],
            e=0.42, mu=0.44, lin_damp=0.16, ang_damp=0.38,
        )

    for nm, cfg in body_launch.items():
        v_arr = np.array(parts[nm]["verts"], dtype=np.float64)
        # Keep <= 48 extreme hull points for ultra-fast vectorized floor collision
        if len(v_arr) > 48:
            step_i = max(1, len(v_arr) // 48)
            hull_v = v_arr[::step_i]
            # Always include min-Z vertices so wreck/panels never sink into floor!
            z_min_idx = np.argsort(v_arr[:, 2])[:12]
            hull_v = np.vstack([hull_v, v_arr[z_min_idx]])
        else:
            hull_v = v_arr

        ext = np.maximum(np.ptp(v_arr, axis=0), 4.0)
        # Principal inertia moments of bounding box (mass = 1)
        ixx = (ext[1] ** 2 + ext[2] ** 2) / 12.0
        iyy = (ext[0] ** 2 + ext[2] ** 2) / 12.0
        izz = (ext[0] ** 2 + ext[1] ** 2) / 12.0

        p0 = np.array(parts[nm]["origin"], dtype=np.float64)
        if nm == "wreck_chassis":
            p0 = p0 + np.array([0.0, 0.0, 4.0])
        elif nm in pose_at_boom:
            p0 = pose_at_boom[nm][0].copy()

        rb_states[nm] = {
            "pos": p0,
            "vel": np.array(cfg["vel"], dtype=np.float64),
            "q": pose_at_boom[nm][1].copy() if nm in pose_at_boom else np.array([0.0, 0.0, 0.0, 1.0]),
            "omega": np.array(cfg["omega"], dtype=np.float64),
            "hull": hull_v,
            "inv_I_body": np.diag([1.0 / ixx, 1.0 / iyy, 1.0 / izz]),
            "e": cfg["e"],
            "mu": cfg["mu"],
            "lin_damp": cfg["lin_damp"],
            "ang_damp": cfg["ang_damp"],
            "spark_cd": 0.0,
        }

    # 3. Step 480 Hz simulation from boom_frame .. n_frames - 1!
    for fi in range(boom_frame, n_frames):
        age = (fi - boom_frame) * dt_frame

        # Record current frame states
        tracks["chassis"]["pos"][fi] = tracks["chassis"]["pos"][boom_frame - 1]
        tracks["chassis"]["rot"][fi] = tracks["chassis"]["rot"][boom_frame - 1]
        tracks["chassis"]["scl"][fi] = np.full(3, 0.0001, dtype=np.float32)
        if "glass_cab" in tracks:
            tracks["glass_cab"]["pos"][fi] = tracks["glass_cab"]["pos"][boom_frame - 1]
            tracks["glass_cab"]["rot"][fi] = tracks["glass_cab"]["rot"][boom_frame - 1]
            tracks["glass_cab"]["scl"][fi] = np.full(3, 0.0001, dtype=np.float32)

        # Volumetric blast starburst flash (expands fast over 0.35s, then shrinks out)
        if age < 0.42:
            fl_s = (0.35 + 2.45 * math.sin(math.pi * min(1.0, age / 0.14))) * max(0.001, 1.0 - age / 0.42)
        else:
            fl_s = 0.0001
        tracks["blast_flash"]["pos"][fi] = [0.0, 0.0, 28.0 + age * 42.0]
        tracks["blast_flash"]["rot"][fi] = q_from_axis_angle((0.0, 0.0, 1.0), age * 7.5)
        tracks["blast_flash"]["scl"][fi] = [fl_s, fl_s, fl_s]

        # Record rigid bodies
        for nm, st in rb_states.items():
            tracks[nm]["pos"][fi] = st["pos"]
            tracks[nm]["rot"][fi] = st["q"]
            tracks[nm]["scl"][fi] = [1.0, 1.0, 1.0]

        # Record 4 gyroscopic wheels
        for wn, ws in wheel_states.items():
            # Build exact wheel orientation: yaw around Z -> lean (camber) around X -> spin around axle Y!
            cy, sy = math.cos(ws["yaw"]), math.sin(ws["yaw"])
            cl, sl = math.cos(ws["lean"]), math.sin(ws["lean"])
            cs, ss = math.cos(ws["spin"]), math.sin(ws["spin"])
            # R_yaw @ R_lean_x @ R_spin_y
            Rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
            Rx = np.array([[1.0, 0.0, 0.0], [0.0, cl, -sl], [0.0, sl, cl]])
            Ry = np.array([[cs, 0.0, ss], [0.0, 1.0, 0.0], [-ss, 0.0, cs]])
            Rw = Rz @ Rx @ Ry
            tracks[wn]["pos"][fi] = ws["pos"]
            tracks[wn]["rot"][fi] = mat3_to_q(Rw)
            tracks[wn]["scl"][fi] = [1.0, 1.0, 1.0]

        if fi == n_frames - 1:
            break

        # Advance 8 physics substeps (480 Hz)
        for _ in range(substeps):
            # --- A. Rigid Bodies (exact hull-floor impulse + torque + Coulomb friction)
            for nm, st in rb_states.items():
                st["spark_cd"] = max(0.0, st["spark_cd"] - dt)
                st["vel"] += g_acc * dt
                st["vel"] *= max(0.0, 1.0 - st["lin_damp"] * dt)
                st["omega"] *= max(0.0, 1.0 - st["ang_damp"] * dt)
                st["pos"] += st["vel"] * dt
                st["q"] = integrate_q(st["q"], st["omega"], dt)

                Rm = q_to_mat3(st["q"])
                pts_w = st["hull"] @ Rm.T + st["pos"]
                min_idx = int(np.argmin(pts_w[:, 2]))
                min_z = float(pts_w[min_idx, 2])

                if min_z < 0.0:
                    # Push out of floor
                    st["pos"][2] -= min_z
                    r_vec = pts_w[min_idx] - st["pos"]
                    r_vec[2] -= min_z
                    v_pt = st["vel"] + np.cross(st["omega"], r_vec)
                    vn = float(v_pt[2])

                    if vn < 0.0:
                        inv_I_w = Rm @ st["inv_I_body"] @ Rm.T
                        rn = np.cross(r_vec, np.array([0.0, 0.0, 1.0]))
                        denom = 1.0 + float(np.dot(np.cross(inv_I_w @ rn, r_vec), np.array([0.0, 0.0, 1.0])))
                        e_eff = st["e"] if vn < -35.0 else 0.0
                        jn = -(1.0 + e_eff) * vn / max(1e-6, denom)
                        imp_n = np.array([0.0, 0.0, jn])
                        st["vel"] += imp_n
                        st["omega"] += inv_I_w @ np.cross(r_vec, imp_n)

                        # Tangential Coulomb friction impulse
                        vt = np.array([v_pt[0], v_pt[1], 0.0])
                        vt_len = float(np.linalg.norm(vt))
                        if vt_len > 1e-4:
                            t_hat = vt / vt_len
                            rt = np.cross(r_vec, t_hat)
                            denom_t = 1.0 + float(np.dot(np.cross(inv_I_w @ rt, r_vec), t_hat))
                            jt = min(st["mu"] * jn, vt_len / max(1e-6, denom_t))
                            imp_t = -jt * t_hat
                            st["vel"] += imp_t
                            st["omega"] += inv_I_w @ np.cross(r_vec, imp_t)

                        # Emit bright metallic impact sparks on hard clangs!
                        if abs(vn) > 85.0 and st["spark_cd"] <= 0.0 and len(sparks) < 220:
                            sparks.append({
                                "t": round((fi - 0) * dt_frame, 3),
                                "pos": [round(float(pts_w[min_idx, 0]), 2),
                                        round(float(pts_w[min_idx, 1]), 2),
                                        1.2],
                                "intensity": round(min(1.0, abs(vn) / 280.0), 2),
                                "kind": "wreck" if nm == "wreck_chassis" else "metal",
                            })
                            st["spark_cd"] = 0.09

                    # Extra settle damping for wreck_chassis once on ground
                    if nm == "wreck_chassis" and abs(st["vel"][2]) < 25.0:
                        st["vel"][0] *= (1.0 - 5.0 * dt)
                        st["vel"][1] *= (1.0 - 5.0 * dt)
                        st["omega"] *= (1.0 - 6.5 * dt)

            # --- B. 4 Gyroscopic Pneumatic Wheels (Airborne Bounce -> Banked Rolling -> Coin Wobble -> Sidewall Flop!)
            for wn, ws in wheel_states.items():
                al = abs(ws["lean"])
                z_contact = w_rad * math.cos(al) + w_half_w * math.sin(al)

                if ws["mode"] == "air":
                    ws["vel"] += g_acc * dt
                    ws["pos"] += ws["vel"] * dt
                    ws["spin"] += ws["spin_rate"] * dt
                    ws["lean"] = max(-1.35, min(1.35, ws["lean"] + ws["lean_vel"] * dt * 0.35))
                    if math.hypot(ws["vel"][0], ws["vel"][1]) > 25.0:
                        ws["yaw"] = math.atan2(ws["vel"][1], ws["vel"][0])

                    if ws["pos"][2] <= z_contact:
                        ws["pos"][2] = z_contact
                        if ws["vel"][2] < -65.0 and ws["bounces"] < 3:
                            # Elastic pneumatic rubber rebound!
                            ws["vel"][2] = -ws["vel"][2] * 0.72
                            ws["vel"][0] *= 0.90
                            ws["vel"][1] *= 0.90
                            ws["bounces"] += 1
                            ws["lean_vel"] = -ws["lean_vel"] * 0.65 + rng.uniform(-0.5, 0.5)
                        else:
                            # Engage ground non-holonomic banked gyroscopic rolling!
                            ws["mode"] = "roll"
                            spd_xy = math.hypot(ws["vel"][0], ws["vel"][1])
                            ws["roll_spd"] = max(165.0, min(310.0, spd_xy))
                            ws["vel"][:] = 0.0
                            ws["lean"] = ws["side"] * math.radians(20.0 + rng.uniform(0.0, 12.0))
                else:
                    # Ground banked rolling & Euler-disk coin precession!
                    spd = ws["roll_spd"]
                    if spd > 1.5:
                        step = spd * dt
                        ws["pos"][0] += math.cos(ws["yaw"]) * step
                        ws["pos"][1] += math.sin(ws["yaw"]) * step
                        # Spin tread from distance rolled (negative spin around +Y moves +Z forward toward +X!)
                        ws["spin"] -= step / max(4.0, w_rad)
                        # Banked disk curvature: leaning wheel steers smoothly into a sweeping arc!
                        ws["yaw"] -= math.sin(ws["lean"]) * (1.85 / max(18.0, spd * 0.14)) * step
                        ws["roll_spd"] = max(0.0, spd * (1.0 - 0.52 * dt) - 14.0 * dt)

                        spd_frac = min(1.0, ws["roll_spd"] / 195.0)
                        target_lean = math.radians(20.0 + ((1.0 - spd_frac) ** 1.8) * 67.5)
                        ws["precess"] += (11.0 + (1.0 - spd_frac) * 15.0) * dt
                        wob = math.sin(ws["precess"]) * math.radians(7.5) * spd_frac
                        ws["lean"] = ws["side"] * target_lean + wob
                        if ws["roll_spd"] < 55.0:
                            ws["yaw"] -= ws["side"] * 2.8 * dt
                    else:
                        # Settled flat on rubber sidewall!
                        ws["lean"] = ws["side"] * math.radians(87.5)

                    al2 = abs(ws["lean"])
                    ws["pos"][2] = w_rad * math.cos(al2) + w_half_w * math.sin(al2)

    return {
        "kind": kind,
        "fps": fps,
        "n_frames": n_frames,
        "boom_frame": boom_frame,
        "tracks": tracks,
        "sparks": sparks,
    }


# --------------------------------------------------------------------------- Multi-Clip glTF 2.0 (.glb) Exporter
def export_vehicle_glb(veh_data, kind, explode_sim, intact_atlas_im, out_glb_path, glass_rgba_im=None):
    """Exports a standalone glTF 2.0 binary (.glb) containing:
       - Full multi-part 3D vehicle + 4 unique wheels + charred wreck + shrapnel + blast starburst
       - Embedded PNG texture atlas (+ optional RGBA glass texture)
       - 3 named glTF animations: 'Idle', 'CatchFire', 'Explode'!
    Coordinate cyclic permutation: (X_gltf, Y_gltf, Z_gltf) = (Y_q, Z_q, X_q) * (1 / 39.37) meters (det > 0)."""
    SCALE = 1.0 / 39.37  # Real-world meters in glTF (1 m = 39.37 Quake units!)
    parts = dict(veh_data["parts"])
    parts["blast_flash"] = build_blast_starburst_mesh()
    ordered_names = list(veh_data["parts"].keys()) + ["blast_flash"]

    bin_blob = bytearray()
    buffer_views = []
    accessors = []

    def pad4():
        while len(bin_blob) % 4 != 0:
            bin_blob.append(0)

    def add_bv(raw_bytes, target=None):
        pad4()
        off = len(bin_blob)
        bin_blob.extend(raw_bytes)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw_bytes)}
        if target is not None:
            bv["target"] = target
        idx = len(buffer_views)
        buffer_views.append(bv)
        return idx

    def add_acc(arr, comp_type, acc_type, target=None):
        arr = np.ascontiguousarray(arr)
        bv_idx = add_bv(arr.tobytes(), target=target)
        acc = {
            "bufferView": bv_idx,
            "componentType": comp_type,
            "count": int(len(arr)),
            "type": acc_type,
        }
        if acc_type == "SCALAR":
            acc["min"] = [float(arr.min())]
            acc["max"] = [float(arr.max())]
        else:
            acc["min"] = [float(x) for x in arr.min(axis=0)]
            acc["max"] = [float(x) for x in arr.max(axis=0)]
        idx = len(accessors)
        accessors.append(acc)
        return idx

    # Embed main PNG texture (+ optional RGBA glass PNG)
    png_buf = io.BytesIO()
    intact_atlas_im.save(png_buf, format="PNG", optimize=True)
    tex_bv = add_bv(png_buf.getvalue())

    glass_bv = None
    if glass_rgba_im is not None:
        g_buf = io.BytesIO()
        glass_rgba_im.save(g_buf, format="PNG", optimize=True)
        glass_bv = add_bv(g_buf.getvalue())

    meshes_gltf = []
    nodes_gltf = []
    node_map = {}

    for nm in ordered_names:
        p = parts[nm]
        vq = np.array(p["verts"], dtype=np.float32)
        nq = np.array(p["norms"], dtype=np.float32)
        uv = np.array(p["uvs"], dtype=np.float32)
        tr = np.array(p["tris"], dtype=np.uint16).reshape(-1)

        # (Y_q, Z_q, X_q) * SCALE
        vg = np.column_stack([vq[:, 1], vq[:, 2], vq[:, 0]]) * SCALE
        ng = np.column_stack([nq[:, 1], nq[:, 2], nq[:, 0]])
        ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-8)

        acc_p = add_acc(vg.astype(np.float32), 5126, "VEC3", target=34962)
        acc_n = add_acc(ng.astype(np.float32), 5126, "VEC3", target=34962)
        acc_u = add_acc(uv.astype(np.float32), 5126, "VEC2", target=34962)
        acc_i = add_acc(tr.astype(np.uint16), 5123, "SCALAR", target=34963)

        if nm == "blast_flash":
            mat_idx = 1
        elif nm == "glass_cab" and glass_bv is not None:
            mat_idx = 2
        else:
            mat_idx = 0
        mesh_idx = len(meshes_gltf)
        meshes_gltf.append({
            "name": f"{kind}_{nm}",
            "primitives": [{
                "attributes": {"POSITION": acc_p, "NORMAL": acc_n, "TEXCOORD_0": acc_u},
                "indices": acc_i,
                "material": mat_idx,
            }],
        })

        # Default rest pose = Idle frame 0
        rest_pose = compute_part_trs_in_sprung_state(veh_data, kind, 0.0, mode="idle")[nm]
        rp, rq, rs = rest_pose
        node_idx = len(nodes_gltf)
        node_map[nm] = node_idx
        nodes_gltf.append({
            "name": nm,
            "mesh": mesh_idx,
            "translation": [float(rp[1] * SCALE), float(rp[2] * SCALE), float(rp[0] * SCALE)],
            "rotation": [float(rq[1]), float(rq[2]), float(rq[0]), float(rq[3])],
            "scale": [float(rs[1]), float(rs[2]), float(rs[0])],
        })

    root_idx = len(nodes_gltf)
    nodes_gltf.append({"name": f"Vehicle_{kind.capitalize()}_Root", "children": list(node_map.values())})

    # Helper to convert Quake track dict -> glTF animation entry
    def pack_clip(clip_name, fps_c, pos_dict, rot_dict, scl_dict, step_scale_Set=()):
        nf = len(next(iter(pos_dict.values())))
        times = (np.arange(nf, dtype=np.float32) / float(fps_c))
        t_acc = add_acc(times, 5126, "SCALAR")
        samplers, channels = [], []

        for nm in ordered_names:
            ni = node_map[nm]
            pq = pos_dict[nm]
            rq = rot_dict[nm]
            sq = scl_dict[nm]

            pg = np.column_stack([pq[:, 1], pq[:, 2], pq[:, 0]]).astype(np.float32) * SCALE
            rg = np.column_stack([rq[:, 1], rq[:, 2], rq[:, 0], rq[:, 3]]).astype(np.float32)
            rg /= np.maximum(np.linalg.norm(rg, axis=1, keepdims=True), 1e-8)
            sg = np.column_stack([sq[:, 1], sq[:, 2], sq[:, 0]]).astype(np.float32)

            acc_t = add_acc(pg, 5126, "VEC3")
            acc_r = add_acc(rg, 5126, "VEC4")
            acc_s = add_acc(sg, 5126, "VEC3")

            st_i = len(samplers); samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": acc_t})
            sr_i = len(samplers); samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": acc_r})
            ss_i = len(samplers); samplers.append({
                "input": t_acc,
                "interpolation": "STEP" if nm in step_scale_Set else "LINEAR",
                "output": acc_s,
            })
            channels.append({"sampler": st_i, "target": {"node": ni, "path": "translation"}})
            channels.append({"sampler": sr_i, "target": {"node": ni, "path": "rotation"}})
            channels.append({"sampler": ss_i, "target": {"node": ni, "path": "scale"}})

        return {"name": clip_name, "samplers": samplers, "channels": channels}

    # Clip 1: 'Idle' (120 frames @ 60 FPS = 2.00s seamless loop)
    nf_idle = 121
    idle_p = {nm: np.zeros((nf_idle, 3), dtype=np.float32) for nm in ordered_names}
    idle_r = {nm: np.zeros((nf_idle, 4), dtype=np.float32) for nm in ordered_names}
    idle_s = {nm: np.ones((nf_idle, 3), dtype=np.float32) for nm in ordered_names}
    for fi in range(nf_idle):
        ph = (fi / 120.0) % 1.0
        pose = compute_part_trs_in_sprung_state(veh_data, kind, ph, mode="idle")
        for nm, (p, q, sc) in pose.items():
            idle_p[nm][fi], idle_r[nm][fi], idle_s[nm][fi] = p, q, sc

    # Clip 2: 'CatchFire' (180 frames @ 60 FPS = 3.00s: 3 bullet jolts -> hood pops ajar -> burning cook-off!)
    nf_fire = 181
    fire_p = {nm: np.zeros((nf_fire, 3), dtype=np.float32) for nm in ordered_names}
    fire_r = {nm: np.zeros((nf_fire, 4), dtype=np.float32) for nm in ordered_names}
    fire_s = {nm: np.ones((nf_fire, 3), dtype=np.float32) for nm in ordered_names}
    for fi in range(nf_fire):
        t = fi / 60.0
        if t < 0.85:
            # Repeated bullet impacts jolting the suspension before catching fire!
            sub_p = ((t % 0.28) / 0.28)
            pose = compute_part_trs_in_sprung_state(veh_data, kind, sub_p, mode="flinch")
        else:
            ph = ((t - 0.85) * 1.35) % 1.0
            pose = compute_part_trs_in_sprung_state(veh_data, kind, ph, mode="fire")
        for nm, (p, q, sc) in pose.items():
            fire_p[nm][fi], fire_r[nm][fi], fire_s[nm][fi] = p, q, sc

    # Clip 3: 'Explode' (from 480 Hz physics simulator)
    tr_ex = explode_sim["tracks"]
    step_set = {"chassis", "glass_cab", "wreck_chassis"} | {f"shrap_{i}" for i in range(10)}
    clips = [
        pack_clip("Idle", 60, idle_p, idle_r, idle_s),
        pack_clip("CatchFire", 60, fire_p, fire_r, fire_s),
        pack_clip(
            "Explode",
            explode_sim["fps"],
            {nm: tr_ex[nm]["pos"] for nm in ordered_names},
            {nm: tr_ex[nm]["rot"] for nm in ordered_names},
            {nm: tr_ex[nm]["scl"] for nm in ordered_names},
            step_scale_Set=step_set,
        ),
    ]

    materials_gltf = [
        {
            "name": f"Vehicle_{kind}_Atlas",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.16 if kind == "van" else 0.24,
                "roughnessFactor": 0.36 if kind == "van" else 0.46,
            },
            "doubleSided": True,
        },
        {
            "name": "Blast_Core_Flash",
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 0.72, 0.20, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 1.0,
            },
            "emissiveFactor": [1.0, 0.56, 0.12],
            "doubleSided": True,
        },
    ]
    textures_gltf = [{"sampler": 0, "source": 0}]
    images_gltf = [{"bufferView": tex_bv, "mimeType": "image/png", "name": f"veh_{kind}_atlas"}]

    if glass_bv is not None:
        textures_gltf.append({"sampler": 0, "source": 1})
        images_gltf.append({"bufferView": glass_bv, "mimeType": "image/png", "name": f"veh_{kind}_glass"})
        materials_gltf.append({
            "name": f"Vehicle_{kind}_Glass",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 1},
                "metallicFactor": 0.08,
                "roughnessFactor": 0.10,
            },
            "alphaMode": "BLEND",
            "doubleSided": True,
        })

    gltf_doc = {
        "asset": {"version": "2.0", "generator": "BakersfieldQuake veh_physics_sim.py"},
        "scene": 0,
        "scenes": [{"name": f"Scene_{kind}", "nodes": [root_idx]}],
        "nodes": nodes_gltf,
        "meshes": meshes_gltf,
        "animations": clips,
        "materials": materials_gltf,
        "textures": textures_gltf,
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "images": images_gltf,
        "bufferViews": buffer_views,
        "accessors": accessors,
        "buffers": [{"byteLength": len(bin_blob)}],
    }

    json_bytes = json.dumps(gltf_doc, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4 != 0:
        json_bytes += b" "
    pad4()

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    with open(out_glb_path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total_len))
        f.write(struct.pack("<I4s", len(json_bytes), b"JSON"))
        f.write(json_bytes)
        f.write(struct.pack("<I4s", len(bin_blob), b"BIN\x00"))
        f.write(bin_blob)
