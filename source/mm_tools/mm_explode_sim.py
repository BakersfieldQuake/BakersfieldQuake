"""3D Rigid-Body, Gyroscopic Wheel-Rolling & Cylinder-Bar Physics Simulator + glTF 2.0 (.glb) Exporter
for Mega Man's Explosion (megaman1.glb).

Simulates 31 3D bodies at 480 Hz substeps (sampled at 60 FPS, 270 frames = 4.50s):
  - Pre-explosion overdrive wheel spin & mechanical pressure shudder (0.00s - 0.35s)
  - Violent T-collar rupture + 3D volumetric shock-starburst flash at t = 0.35s
  - Two intact wheels (wheel_left, wheel_right) blasting off opposite ends of the axle,
    bouncing with elastic tire rebound, catching traction, carving sweeping banked curves
    across the floor via non-holonomic rolling-disk mechanics, entering an Euler-disk
    coin-wobble precession, and flopping flat on their sidewalls
  - Main brushed stainless steel bar (main_bar) blasting upward end-over-end, clanging
    off its nose and tail endpoints, settling horizontal, and rolling smoothly across
    the floor around its cylindrical axis before rocking to a rest
  - Blown-off black Delrin rear end-cap (rear_cap) & two snapped steel cross-axles
    (axle_left, axle_right) clattering and rolling
  - 24 Voronoi-fractured random 3D shrapnel pieces (sheared steel, scorched core,
    white rim shards, ribbed black rubber chunks) with exact convex-hull vertex floor
    impulses, angular momentum tumble, and Coulomb sliding friction.
"""
import io
import json
import math
import os
import struct
import numpy as np
from PIL import Image, ImageDraw


# --------------------------------------------------------------------------- Quaternion & Rotation Math
def q_mul(a, b):
    """Hamilton product of two (x, y, z, w) quaternions."""
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
    """Orthonormal 3x3 matrix (columns = basis vectors) -> (x, y, z, w) unit quaternion."""
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


# --------------------------------------------------------------------------- Unified Texture Atlas Builder
def build_fracture_atlas(glb_path):
    """Loads megaman1.glb's 2048x2048 PNG and paints 4 detailed fracture-interior swatches
    into the unused right-hand strip u in [0.89, 0.99]."""
    with open(glb_path, "rb") as f:
        magic, _, _ = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF"
        jlen, _ = struct.unpack("<I4s", f.read(8))
        gltf = json.loads(f.read(jlen))
        blen, _ = struct.unpack("<I4s", f.read(8))
        bin_data = f.read(blen)

    im_info = gltf["images"][0]
    bv = gltf["bufferViews"][im_info["bufferView"]]
    raw_im = bin_data[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
    atlas = Image.open(io.BytesIO(raw_im)).convert("RGB")
    W, H = atlas.size
    arr = np.array(atlas, dtype=np.float32)

    rng = np.random.default_rng(77)
    x0, x1 = int(W * 0.885), int(W * 0.995)
    sw = x1 - x0

    # 1. Sheared Stainless Steel (v: 0.04..0.26)
    y0, y1 = int(H * 0.04), int(H * 0.26)
    sh = y1 - y0
    yy, xx = np.mgrid[0:sh, 0:sw]
    streaks = 16.0 * np.sin(xx * 0.21 + yy * 0.04) + 11.0 * np.cos(yy * 0.37)
    grain = rng.normal(0.0, 12.0, (sh, sw))
    base_s = 186.0 + streaks + grain
    arr[y0:y1, x0:x1, 0] = np.clip(base_s - 4.0, 90, 248)
    arr[y0:y1, x0:x1, 1] = np.clip(base_s, 95, 250)
    arr[y0:y1, x0:x1, 2] = np.clip(base_s + 9.0, 105, 255)

    # 2. Scorched Blast Core Gunmetal / Soot (v: 0.29..0.51)
    y0, y1 = int(H * 0.29), int(H * 0.51)
    sh = y1 - y0
    yy, xx = np.mgrid[0:sh, 0:sw]
    pits = rng.normal(0.0, 14.0, (sh, sw))
    ember = np.maximum(0.0, np.sin(xx * 0.13 + yy * 0.09) * np.cos(yy * 0.17 - xx * 0.05)) ** 3
    base_c = 42.0 + pits
    arr[y0:y1, x0:x1, 0] = np.clip(base_c + ember * 145.0, 14, 235)
    arr[y0:y1, x0:x1, 1] = np.clip(base_c + ember * 68.0, 14, 180)
    arr[y0:y1, x0:x1, 2] = np.clip(base_c + ember * 18.0, 16, 120)

    # 3. Torn Matte Vulcanized Tire Rubber + Cord Flecks (v: 0.54..0.76)
    y0, y1 = int(H * 0.54), int(H * 0.76)
    sh = y1 - y0
    rub = 26.0 + rng.normal(0.0, 6.5, (sh, sw))
    cords = (rng.random((sh, sw)) > 0.985).astype(np.float32) * 95.0
    arr[y0:y1, x0:x1, 0] = np.clip(rub + cords, 10, 165)
    arr[y0:y1, x0:x1, 1] = np.clip(rub + cords, 10, 165)
    arr[y0:y1, x0:x1, 2] = np.clip(rub + 2.0 + cords, 12, 170)

    # 4. Chipped White Stamped-Steel Rim (v: 0.78..0.98)
    y0, y1 = int(H * 0.78), int(H * 0.98)
    sh = y1 - y0
    yy, xx = np.mgrid[0:sh, 0:sw]
    chip_mask = (np.sin(xx * 0.09) * np.cos(yy * 0.08) + rng.normal(0, 0.25, (sh, sw))) > 0.45
    rim_v = np.where(chip_mask, 138.0 + rng.normal(0, 10, (sh, sw)), 228.0 + rng.normal(0, 5, (sh, sw)))
    arr[y0:y1, x0:x1, 0] = np.clip(rim_v, 95, 250)
    arr[y0:y1, x0:x1, 1] = np.clip(rim_v + 2.0, 98, 252)
    arr[y0:y1, x0:x1, 2] = np.clip(rim_v + 6.0, 102, 255)

    return Image.fromarray(arr.astype(np.uint8), "RGB")


# --------------------------------------------------------------------------- World-Space Local Geometry Helper
def part_world_aligned_mesh(part):
    """Converts a part's local (verts, norms) into world-aligned local coordinates centered at part['origin']
    so at rotation q=(0,0,0,1) and translation=part['origin'] it sits in its exact rest pose."""
    axes = np.array(part["axes"], dtype=np.float64)  # rows: ax_x, ax_y, ax_z in world Quake coords
    v_loc = np.array(part["verts"], dtype=np.float64)
    n_loc = np.array(part["norms"], dtype=np.float64)
    # p_world_rel = v_loc @ axes
    v_w = v_loc @ axes
    n_w = n_loc @ axes
    norms_len = np.linalg.norm(n_w, axis=1, keepdims=True)
    n_w = n_w / np.maximum(norms_len, 1e-9)
    return v_w, n_w


def build_blast_starburst_mesh():
    """Creates a 3D jagged volumetric starburst + shockwave ring mesh for the detonation flash."""
    rng = np.random.default_rng(99)
    verts, norms, uvs, tris = [], [], [], []
    # 18 3D spikes radiating from origin
    n_spikes = 18
    for i in range(n_spikes):
        phi = math.acos(1.0 - 2.0 * (i + 0.5) / n_spikes)
        theta = math.pi * (1.0 + 5.0 ** 0.5) * i
        d = np.array([math.sin(phi) * math.cos(theta), math.sin(phi) * math.sin(theta), math.cos(phi)])
        up = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.85 else np.array([1.0, 0.0, 0.0])
        u = np.cross(d, up); u /= np.linalg.norm(u)
        v = np.cross(d, u)
        L = rng.uniform(7.5, 13.5)
        w = rng.uniform(1.1, 2.0)
        b = len(verts)
        tip = d * L
        p0 = u * w
        p1 = -0.5 * u * w + 0.866 * v * w
        p2 = -0.5 * u * w - 0.866 * v * w
        verts.extend([tip.tolist(), p0.tolist(), p1.tolist(), p2.tolist()])
        norms.extend([d.tolist(), u.tolist(), v.tolist(), (-v).tolist()])
        uvs.extend([(0.5, 0.5)] * 4)
        tris.extend([[b, b + 1, b + 2], [b, b + 2, b + 3], [b, b + 3, b + 1]])
    return dict(verts=verts, norms=norms, uvs=uvs, tris=tris)


# --------------------------------------------------------------------------- Full Physics Simulation
def simulate_full_explosion(parts, fps=60, duration=4.50, substeps=8):
    """Runs the 480 Hz physics simulation and returns sampled TRS keyframes & impact spark events."""
    n_frames = int(round(fps * duration)) + 1
    dt_frame = 1.0 / fps
    dt = dt_frame / substeps
    t_boom = 0.35
    boom_frame = int(round(t_boom * fps))
    g = 390.0  # Quake units / s^2 (~17.7 m/s^2 for crisp, weighty scale physics)

    blast_center = np.array([-1.4, 0.0, 11.8], dtype=np.float64)
    pipe_dir = np.array([0.8221, -0.0009, -0.5693], dtype=np.float64)
    pipe_dir /= np.linalg.norm(pipe_dir)

    # Precompute world-aligned local meshes & support hull samples for floor collision
    meshes = {}
    hull_pts = {}
    rng = np.random.default_rng(20261030)

    for name, p in parts.items():
        vw, nw = part_world_aligned_mesh(p)
        meshes[name] = (vw, nw)
        # Pick 32 extreme directional support vertices for ultra-accurate, fast floor contact
        dirs = rng.normal(size=(48, 3))
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        idx = np.unique(np.argmax(vw @ dirs.T, axis=0))
        hull_pts[name] = vw[idx]

    tracks = {name: {"pos": np.zeros((n_frames, 3), dtype=np.float32),
                     "rot": np.zeros((n_frames, 4), dtype=np.float32),
                     "scl": np.ones((n_frames, 3), dtype=np.float32)} for name in parts}
    tracks["blast_flash"] = {
        "pos": np.repeat(blast_center[None, :].astype(np.float32), n_frames, axis=0),
        "rot": np.repeat(np.array([[0, 0, 0, 1]], dtype=np.float32), n_frames, axis=0),
        "scl": np.zeros((n_frames, 3), dtype=np.float32),
    }

    spark_events = []  # list of dict(t, pos, intensity, kind)

    # ==================== 1. PRE-DETONATION FRAMES (0 .. boom_frame-1) ====================
    w_spin_accum = 0.0
    for fi in range(boom_frame):
        t = fi * dt_frame
        prog = t / t_boom  # 0..1
        # Accelerating wheel rev-up + chassis torque pitch + high-freq overload shudder
        omega_rev = 8.0 + 48.0 * (prog ** 2)
        w_spin_accum += omega_rev * dt_frame
        pitch_rock = math.radians(5.5 * math.sin(prog * math.pi * 5.0) * prog)
        shudder = (prog ** 2.5) * 0.42 * np.array([
            math.sin(t * 240.0),
            math.cos(t * 295.0) * 0.8,
            abs(math.sin(t * 210.0)) * 0.7,
        ])
        swell = 1.0 + 0.045 * (prog ** 4)

        q_wheel = q_from_axis_angle([0.0, 1.0, 0.0], w_spin_accum)
        q_rock = q_from_axis_angle([0.0, 1.0, 0.0], pitch_rock)

        for name, p in parts.items():
            orig = np.array(p["origin"], dtype=np.float64)
            if name in ("wheel_left", "wheel_right"):
                tracks[name]["pos"][fi] = orig + shudder
                tracks[name]["rot"][fi] = q_wheel
                tracks[name]["scl"][fi] = [1.0, 1.0, 1.0]
            elif name in ("main_bar", "rear_cap", "axle_left", "axle_right"):
                # Pivot rock about axle center (-1.4, orig_y, 11.8)
                piv = np.array([-1.4, orig[1], 11.8])
                rel = orig - piv
                tracks[name]["pos"][fi] = piv + (q_to_mat3(q_rock) @ rel) + shudder
                tracks[name]["rot"][fi] = q_rock
                tracks[name]["scl"][fi] = [swell, swell, swell] if name in ("main_bar", "rear_cap") else [1.0, 1.0, 1.0]
            else:
                # Hide internal/overlapping Voronoi shrapnel cleanly before detonation
                tracks[name]["pos"][fi] = orig
                tracks[name]["rot"][fi] = [0.0, 0.0, 0.0, 1.0]
                tracks[name]["scl"][fi] = [0.0005, 0.0005, 0.0005]

    # Detonation flash event
    spark_events.append(dict(t=round(t_boom, 3), pos=blast_center.round(2).tolist(), intensity=3.0, kind="detonation"))

    for fi in range(boom_frame, n_frames):
        dt_b = (fi - boom_frame) * dt_frame
        if dt_b < 0.28:
            u = dt_b / 0.28
            sc = (0.35 + 2.6 * (u ** 0.45)) * max(0.0, 1.0 - u ** 1.4)
            tracks["blast_flash"]["scl"][fi] = [sc, sc, sc]
            tracks["blast_flash"]["rot"][fi] = q_from_axis_angle([0.3, 0.5, 0.8], dt_b * 14.0)

    # ==================== 2. TWO WHEELS: BOUNCE -> BANKING ROLL ARCS -> COIN PRECESSION ====================
    wheel_configs = [
        # (name, vel0, spin0, yaw0_rate, lean0, lean_sign, R, half_w)
        ("wheel_left",  np.array([52.0, -34.0, 120.0]),  28.0,  0.65,  0.34, +1.0, 12.01, 4.95),
        ("wheel_right", np.array([-48.0, 44.0, 134.0]),  31.0, -0.70, -0.35, -1.0, 12.01, 4.95),
    ]
    for wname, vel0, spin0, yaw_r0, lean0, lsign, R_w, W_w in wheel_configs:
        pos = np.array(parts[wname]["origin"], dtype=np.float64)
        vel = vel0.copy()
        mode = "air"
        psi_m = 0.0
        phi = 0.0
        phi_vel = lsign * 1.15
        psi_vel = yaw_r0
        theta = w_spin_accum
        spin_rate = spin0
        roll_speed = 0.0
        bounces = 0
        wobble_t = 0.0

        for fi in range(boom_frame, n_frames):
            # Compose rotation: R_world = Rz(psi_m) @ Rx(phi) @ Ry(theta)
            qz = q_from_axis_angle([0.0, 0.0, 1.0], psi_m)
            qx = q_from_axis_angle([1.0, 0.0, 0.0], phi)
            qy = q_from_axis_angle([0.0, 1.0, 0.0], theta)
            q_tot = q_mul(qz, q_mul(qx, qy))

            tracks[wname]["pos"][fi] = pos
            tracks[wname]["rot"][fi] = q_tot
            tracks[wname]["scl"][fi] = [1.0, 1.0, 1.0]

            if fi == n_frames - 1:
                break

            for _ in range(substeps):
                if mode == "air":
                    vel[2] -= g * dt
                    pos += vel * dt
                    theta += spin_rate * dt
                    psi_m += psi_vel * dt
                    phi = max(-0.85, min(0.85, phi + phi_vel * dt))

                    sin_p = abs(math.sin(phi))
                    cos_p = abs(math.cos(phi))
                    z_ground = R_w * cos_p + W_w * sin_p
                    if pos[2] < z_ground and vel[2] < 0.0:
                        pos[2] = z_ground
                        bounces += 1
                        impact_vz = -vel[2]
                        spark_events.append(dict(t=round(fi * dt_frame, 3), pos=[round(pos[0], 1), round(pos[1], 1), 0.5], intensity=min(1.0, impact_vz / 160.0), kind="rubber"))
                        if impact_vz > 58.0 and bounces <= 1:
                            vel[2] = impact_vz * 0.48
                            # Tire tread spin bites into floor and kicks wheel along its rolling tangent!
                            fwd_2d = np.array([math.cos(psi_m), math.sin(psi_m)])
                            vel[:2] = 0.55 * vel[:2] + fwd_2d * 48.0
                            psi_vel = lsign * -0.9
                            phi_vel = -phi * 1.8 + lsign * 0.65
                            spin_rate = max(16.0, np.linalg.norm(vel[:2]) / R_w)
                        else:
                            # Transition seamlessly into continuous non-holonomic banked ground rolling!
                            mode = "roll"
                            # Keep psi_m continuous (no orientation snap!) and sign roll_speed along fwd_2d
                            fwd_2d = np.array([math.cos(psi_m), math.sin(psi_m)])
                            v_proj = float(np.dot(vel[:2], fwd_2d))
                            roll_sign = 1.0 if v_proj >= -10.0 else -1.0
                            roll_speed = roll_sign * max(82.0, min(105.0, np.linalg.norm(vel[:2]) * 1.15))
                            phi = max(-0.48, min(0.48, phi if abs(phi) > 0.25 else lsign * 0.32))
                            phi_vel = 0.0

                elif mode == "roll":
                    wobble_t += dt
                    pos[0] += math.cos(psi_m) * roll_speed * dt
                    pos[1] += math.sin(psi_m) * roll_speed * dt
                    theta += (roll_speed / R_w) * dt

                    # Strong banked curvature so both wheels carve sweeping 260-320 deg arcs around the arena!
                    r_sgn = 1.0 if roll_speed >= 0.0 else -1.0
                    turn_rate = -r_sgn * (g * 0.68 * math.sin(phi)) / max(abs(roll_speed), 24.0)
                    psi_m += turn_rate * dt

                    # Progressive rolling decay & gyroscopic lean toward Euler-disk coin wobble
                    spd_abs = max(0.0, abs(roll_speed) * (1.0 - 0.52 * dt) - 16.5 * dt)
                    roll_speed = math.copysign(spd_abs, roll_speed)
                    speed_frac = min(1.0, spd_abs / 90.0)
                    target_abs_phi = 0.30 + (1.0 - speed_frac) ** 1.45 * (0.5 * math.pi - 0.32)
                    wobble = 0.10 * speed_frac * math.sin(wobble_t * (12.0 + 10.0 * (1.0 - speed_frac)))
                    desired_phi = lsign * target_abs_phi + wobble
                    phi += (desired_phi - phi) * min(1.0, 6.2 * dt)

                    sin_p = abs(math.sin(phi))
                    cos_p = abs(math.cos(phi))
                    pos[2] = R_w * cos_p + W_w * sin_p

                    if spd_abs < 12.0 or abs(phi) > 1.28:
                        mode = "coin"
                        phi_vel = lsign * 2.1

                elif mode == "coin":
                    # Classic Euler's disk / wobbling rim settle onto flat sidewall (|phi| -> pi/2)
                    wobble_t += dt
                    rem = max(0.0, 0.5 * math.pi - abs(phi))
                    if rem > 0.003 or abs(phi_vel) > 0.06:
                        phi_vel += lsign * 11.5 * max(0.12, math.cos(abs(phi))) * dt
                        phi += phi_vel * dt
                        prec_rate = -lsign * min(16.0, 3.2 / max(rem + 0.13, 0.13)) * min(1.0, rem * 4.8)
                        psi_m += prec_rate * dt
                        theta -= prec_rate * math.sin(abs(phi)) * dt * 0.35
                        if abs(phi) >= 0.5 * math.pi:
                            phi = lsign * 0.5 * math.pi
                            if abs(phi_vel) > 0.55:
                                phi_vel = -phi_vel * 0.28
                                spark_events.append(dict(t=round(fi * dt_frame, 3), pos=[round(pos[0], 1), round(pos[1], 1), 0.3], intensity=0.35, kind="rubber"))
                            else:
                                phi_vel = 0.0
                    sin_p = abs(math.sin(phi))
                    cos_p = abs(math.cos(phi))
                    pos[2] = R_w * cos_p + W_w * sin_p

    # ==================== 3. MAIN STAINLESS STEEL BAR: END-OVER-END CLANG -> FLOOR ROLL ====================
    bar_orig = np.array(parts["main_bar"]["origin"], dtype=np.float64)
    bar_pos = bar_orig.copy()
    bar_vel = np.array([26.0, 18.0, 178.0], dtype=np.float64)
    bar_q = tracks["main_bar"]["rot"][boom_frame - 1].astype(np.float64)
    # Strong end-over-end tumble + axial spin so it lands nearly horizontal around t ~ 1.45s and rolls 4+ turns!
    bar_omega = np.array([-2.8, 10.6, 4.4], dtype=np.float64)
    R_bar = 1.92
    end_a_local = -pipe_dir * 14.4
    end_b_local = +pipe_dir * 14.4
    bar_mode = "tumble"
    bar_spin = 0.0
    bar_roll_vel = 0.0
    bar_rock_phase = 0.0
    bar_bounces = 0

    for fi in range(boom_frame, n_frames):
        tracks["main_bar"]["pos"][fi] = bar_pos
        tracks["main_bar"]["rot"][fi] = bar_q
        tracks["main_bar"]["scl"][fi] = [1.0, 1.0, 1.0]
        if fi == n_frames - 1:
            break

        for _ in range(substeps):
            if bar_mode == "tumble":
                bar_vel[2] -= g * dt
                bar_vel *= (1.0 - 0.14 * dt)
                bar_pos += bar_vel * dt
                bar_q = integrate_q(bar_q, bar_omega, dt)
                Rm = q_to_mat3(bar_q)

                # Test both capsule endpoints against Z = R_bar
                for r_loc in (end_a_local, end_b_local):
                    r_w = Rm @ r_loc
                    p_end = bar_pos + r_w
                    if p_end[2] < R_bar:
                        pen = R_bar - p_end[2]
                        bar_pos[2] += pen
                        v_pt = bar_vel + np.cross(bar_omega, r_w)
                        if v_pt[2] < 0.0:
                            bar_bounces += 1
                            m_bar = 1.0
                            I_bar = (1.0 / 12.0) * (28.8 ** 2)
                            r_xy2 = r_w[0] ** 2 + r_w[1] ** 2
                            k_eff = (1.0 / m_bar) + (r_xy2 / I_bar)
                            e_steel = 0.42 if (-v_pt[2] > 38.0 and bar_bounces <= 3) else 0.12
                            jn = -(1.0 + e_steel) * v_pt[2] / k_eff
                            imp = np.array([0.0, 0.0, jn])
                            vt = np.array([v_pt[0], v_pt[1], 0.0])
                            vt_len = np.linalg.norm(vt)
                            if vt_len > 1e-5:
                                jt = min(0.24 * jn, vt_len / k_eff)
                                imp -= (vt / vt_len) * jt
                            bar_vel += imp / m_bar
                            bar_omega += np.cross(r_w, imp) / I_bar
                            bar_omega *= 0.84
                            if jn > 20.0:
                                spark_events.append(dict(t=round(fi * dt_frame, 3), pos=[round(p_end[0], 1), round(p_end[1], 1), 1.0], intensity=min(1.5, jn / 85.0), kind="sparks"))

                # Check if bar has settled nearly horizontal on the floor -> transition to smooth cylinder rolling!
                cur_axis = q_to_mat3(bar_q) @ pipe_dir
                if abs(cur_axis[2]) < 0.14 and bar_pos[2] < R_bar + 0.75 and abs(bar_vel[2]) < 22.0:
                    bar_mode = "roll_bar"
                    ax_h = np.array([cur_axis[0], cur_axis[1], 0.0])
                    ax_h /= max(np.linalg.norm(ax_h), 1e-6)
                    # Snap slight tilt cleanly onto horizontal plane without twist jump
                    tilt_corr = np.cross(cur_axis / max(np.linalg.norm(cur_axis), 1e-6), ax_h)
                    q_level = q_from_axis_angle(tilt_corr, math.asin(min(1.0, np.linalg.norm(tilt_corr))))
                    bar_q = q_norm(q_mul(q_level, bar_q))
                    bar_axis_h = ax_h
                    perp_h = np.array([-ax_h[1], ax_h[0], 0.0])
                    v_perp = float(np.dot(bar_vel, perp_h))
                    if abs(v_perp) < 52.0:
                        v_perp = 58.0 if v_perp >= 0.0 else -58.0
                    bar_roll_vel = v_perp
                    bar_vel[:] = perp_h * bar_roll_vel
                    bar_pos[2] = R_bar
                    bar_q_roll0 = bar_q.copy()
                    bar_spin = 0.0

            elif bar_mode == "roll_bar":
                perp_h = np.array([-bar_axis_h[1], bar_axis_h[0], 0.0])
                bar_pos += perp_h * bar_roll_vel * dt
                bar_pos[2] = R_bar
                bar_spin -= (bar_roll_vel / R_bar) * dt
                bar_roll_vel *= (1.0 - 0.82 * dt)
                if abs(bar_roll_vel) > 3.0:
                    bar_roll_vel -= math.copysign(11.5 * dt, bar_roll_vel)
                else:
                    # Gentle out-of-round collar-scar settle oscillation
                    bar_rock_phase += dt * 7.8
                    bar_roll_vel *= 0.82
                    bar_spin += 0.022 * math.sin(bar_rock_phase) * math.exp(-bar_rock_phase * 0.28)
                q_tw = q_from_axis_angle(bar_axis_h, bar_spin)
                bar_q = q_norm(q_mul(q_tw, bar_q_roll0))

    # ==================== 4. SNAPPED AXLES, REAR CAP & 24 VORONOI FRAGMENTS ====================
    frag_names = ["rear_cap", "axle_left", "axle_right"] + [k for k in sorted(parts.keys()) if k.startswith("frag_")]
    for idx_f, fname in enumerate(frag_names):
        p = parts[fname]
        pos = np.array(p["origin"], dtype=np.float64)
        q = tracks[fname]["rot"][boom_frame - 1].astype(np.float64)
        h_pts = hull_pts[fname]
        pmat = p.get("phys_mat", "metal")

        # Blast impulse vector from central T-collar
        radial = pos - blast_center
        r_dist = np.linalg.norm(radial)
        r_dir = radial / max(r_dist, 0.5)

        if fname == "rear_cap":
            # Blows off the back of the stainless bar like a mortar plug!
            vel = -pipe_dir * 118.0 + np.array([rng.uniform(-18, 18), rng.uniform(-28, 28), 88.0])
            omega = np.array([14.0, -19.0, 11.0])
            rest_e, mu_f, drag = 0.50, 0.42, 0.28
        elif fname in ("axle_left", "axle_right"):
            sgn = -1.0 if fname == "axle_left" else 1.0
            vel = np.array([rng.uniform(-45, 45), sgn * rng.uniform(55, 88), rng.uniform(115, 155)])
            omega = np.array([rng.uniform(-16, 16), rng.uniform(-18, 18), sgn * 22.0])
            rest_e, mu_f, drag = 0.46, 0.30, 0.20
        else:
            # 24 Voronoi random pieces: wide chaotic 360-degree shrapnel spray!
            az_rand = rng.uniform(0, 2 * math.pi)
            horiz_burst = np.array([math.cos(az_rand), math.sin(az_rand), 0.0])
            mix_dir = 0.55 * r_dir + 0.45 * horiz_burst
            mix_dir[2] = abs(mix_dir[2]) * 0.45 + rng.uniform(0.45, 1.05)
            mix_dir /= np.linalg.norm(mix_dir)
            vol = max(10.0, float(p["volume"]))
            speed = rng.uniform(82.0, 168.0) * ((45.0 / vol) ** 0.16)
            vel = mix_dir * speed
            omega = rng.normal(0.0, 16.5, size=3)
            if pmat == "rubber":
                rest_e, mu_f, drag = 0.62, 0.60, 0.30
            elif pmat == "rim":
                rest_e, mu_f, drag = 0.45, 0.36, 0.24
            else:
                rest_e, mu_f, drag = 0.42, 0.34, 0.22

        # Approximate radius of gyration from hull points for realistic corner-impact torque
        rg2 = max(1.8, float(np.mean(np.sum(h_pts ** 2, axis=1))) * 0.55)
        b_cnt = 0

        for fi in range(boom_frame, n_frames):
            tracks[fname]["pos"][fi] = pos
            tracks[fname]["rot"][fi] = q
            tracks[fname]["scl"][fi] = [1.0, 1.0, 1.0]
            if fi == n_frames - 1:
                break

            for _ in range(substeps):
                vel[2] -= g * dt
                vel *= (1.0 - drag * dt)
                pos += vel * dt
                q = integrate_q(q, omega, dt)

                Rm = q_to_mat3(q)
                w_pts = (h_pts @ Rm.T) + pos
                min_idx = int(np.argmin(w_pts[:, 2]))
                min_z = float(w_pts[min_idx, 2])
                if min_z < 0.0:
                    pos[2] -= min_z
                    # Average all vertices within 0.35 units of the floor (stabilizes flat-face resting!)
                    low_mask = (w_pts[:, 2] - min_z) < 0.35
                    r_contact = np.mean(w_pts[low_mask] - pos, axis=0)
                    v_pt = vel + np.cross(omega, r_contact)
                    if v_pt[2] < 0.0:
                        r_xy2 = r_contact[0] ** 2 + r_contact[1] ** 2
                        k_eff = 1.0 + r_xy2 / rg2
                        e_use = rest_e if -v_pt[2] > 32.0 else 0.0
                        jn = -(1.0 + e_use) * v_pt[2] / k_eff
                        imp = np.array([0.0, 0.0, jn])
                        vt = np.array([v_pt[0], v_pt[1], 0.0])
                        vt_len = np.linalg.norm(vt)
                        if vt_len > 1e-5:
                            jt = min(mu_f * jn, vt_len / k_eff)
                            imp -= (vt / vt_len) * jt
                        vel += imp
                        omega += np.cross(r_contact, imp) / rg2
                        omega *= 0.84 if np.sum(low_mask) >= 3 else 0.92
                        b_cnt += 1
                        if b_cnt <= 2 and jn > 36.0 and pmat != "rubber":
                            spark_events.append(dict(t=round(fi * dt_frame, 3), pos=[round(pos[0], 1), round(pos[1], 1), 0.6], intensity=min(1.0, jn / 110.0), kind="sparks"))

                    # Settle damping when resting on floor with tiny velocity
                    if abs(vel[2]) < 8.0 and np.linalg.norm(vel[:2]) < 10.0 and np.linalg.norm(omega) < 2.2:
                        vel *= (1.0 - 8.0 * dt)
                        omega *= (1.0 - 9.0 * dt)

    return dict(
        fps=fps,
        n_frames=n_frames,
        duration=duration,
        boom_frame=boom_frame,
        t_boom=t_boom,
        meshes=meshes,
        tracks=tracks,
        sparks=spark_events,
    )


# --------------------------------------------------------------------------- Binary glTF 2.0 (.glb) Exporter
def export_exploded_glb(parts, sim, atlas_im, out_glb_path):
    """Exports the complete 31-node animated physics scene to a binary glTF 2.0 (.glb) file
    in the exact physical meter scale (/ 22.0) and coordinate frame of megaman1.glb."""
    SCALE_INV = 1.0 / 22.0
    bin_buf = bytearray()
    buffer_views = []
    accessors = []
    meshes_gltf = []
    nodes_gltf = []
    samplers = []
    channels = []

    def align4():
        while len(bin_buf) & 3:
            bin_buf.append(0)

    def add_bv(raw_bytes, target=None):
        align4()
        off = len(bin_buf)
        bin_buf.extend(raw_bytes)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw_bytes)}
        if target is not None:
            bv["target"] = target
        idx = len(buffer_views)
        buffer_views.append(bv)
        return idx

    def add_acc(arr, comp_type, acc_type, target=None, with_minmax=False):
        bv_idx = add_bv(arr.tobytes(), target=target)
        acc = {
            "bufferView": bv_idx,
            "componentType": comp_type,
            "count": int(len(arr)),
            "type": acc_type,
        }
        if with_minmax:
            if arr.ndim == 1:
                acc["min"] = [float(arr.min())]
                acc["max"] = [float(arr.max())]
            else:
                acc["min"] = [float(x) for x in arr.min(axis=0)]
                acc["max"] = [float(x) for x in arr.max(axis=0)]
        idx = len(accessors)
        accessors.append(acc)
        return idx

    # 1. Embed 2048x2048 PNG texture
    png_io = io.BytesIO()
    atlas_im.save(png_io, format="PNG", compress_level=6)
    tex_bv = add_bv(png_io.getvalue())

    # 2. Shared time keyframe input accessor (0 .. duration)
    times = (np.arange(sim["n_frames"], dtype=np.float32) / float(sim["fps"]))
    time_acc = add_acc(times, 5126, "SCALAR", with_minmax=True)

    # 3. Add all 30 contraption/shrapnel parts + blast_flash mesh
    blast_mesh_dict = build_blast_starburst_mesh()
    all_items = [(name, parts[name], sim["meshes"][name][0], sim["meshes"][name][1], 0) for name in parts]
    all_items.append((
        "blast_flash",
        blast_mesh_dict,
        np.array(blast_mesh_dict["verts"], dtype=np.float64),
        np.array(blast_mesh_dict["norms"], dtype=np.float64),
        1,
    ))

    child_indices = []
    for name, pdict, vw, nw, mat_idx in all_items:
        # Even cyclic permutation Quake (X_q, Y_q, Z_q) -> glTF (X_g, Y_g, Z_g) = (Y_q, Z_q, X_q) / 22.0
        pos_g = np.column_stack([vw[:, 1], vw[:, 2], vw[:, 0]]).astype(np.float32) * SCALE_INV
        nrm_g = np.column_stack([nw[:, 1], nw[:, 2], nw[:, 0]]).astype(np.float32)
        nrm_g /= np.maximum(np.linalg.norm(nrm_g, axis=1, keepdims=True), 1e-8)
        uv_g = np.array(pdict["uvs"], dtype=np.float32)
        tris_g = np.array(pdict["tris"], dtype=np.uint16).reshape(-1)

        acc_pos = add_acc(pos_g, 5126, "VEC3", target=34962, with_minmax=True)
        acc_nrm = add_acc(nrm_g, 5126, "VEC3", target=34962)
        acc_uv = add_acc(uv_g, 5126, "VEC2", target=34962)
        acc_idx = add_acc(tris_g, 5123, "SCALAR", target=34963)

        mesh_idx = len(meshes_gltf)
        meshes_gltf.append({
            "name": name,
            "primitives": [{
                "attributes": {"POSITION": acc_pos, "NORMAL": acc_nrm, "TEXCOORD_0": acc_uv},
                "indices": acc_idx,
                "material": mat_idx,
            }],
        })

        tr = sim["tracks"][name]
        # Permute Quake pos & quaternion -> glTF pos & quaternion
        tr_pos_q = tr["pos"]
        tr_rot_q = tr["rot"]
        tr_scl_q = tr["scl"]

        anim_pos = np.column_stack([tr_pos_q[:, 1], tr_pos_q[:, 2], tr_pos_q[:, 0]]).astype(np.float32) * SCALE_INV
        anim_rot = np.column_stack([tr_rot_q[:, 1], tr_rot_q[:, 2], tr_rot_q[:, 0], tr_rot_q[:, 3]]).astype(np.float32)
        anim_rot /= np.maximum(np.linalg.norm(anim_rot, axis=1, keepdims=True), 1e-8)
        anim_scl = np.column_stack([tr_scl_q[:, 1], tr_scl_q[:, 2], tr_scl_q[:, 0]]).astype(np.float32)

        node_idx = len(nodes_gltf)
        nodes_gltf.append({
            "name": name,
            "mesh": mesh_idx,
            "translation": [float(x) for x in anim_pos[0]],
            "rotation": [float(x) for x in anim_rot[0]],
            "scale": [float(x) for x in anim_scl[0]],
        })
        child_indices.append(node_idx)

        acc_t = add_acc(anim_pos, 5126, "VEC3")
        acc_r = add_acc(anim_rot, 5126, "VEC4")
        s_t = len(samplers); samplers.append({"input": time_acc, "interpolation": "LINEAR", "output": acc_t})
        s_r = len(samplers); samplers.append({"input": time_acc, "interpolation": "LINEAR", "output": acc_r})
        channels.append({"sampler": s_t, "target": {"node": node_idx, "path": "translation"}})
        channels.append({"sampler": s_r, "target": {"node": node_idx, "path": "rotation"}})

        # Include scale track only when animated (fragments & blast_flash & bar swell)
        if not np.allclose(anim_scl, 1.0, atol=1e-4):
            acc_s = add_acc(anim_scl, 5126, "VEC3")
            s_s = len(samplers); samplers.append({"input": time_acc, "interpolation": "STEP" if name.startswith("frag_") else "LINEAR", "output": acc_s})
            channels.append({"sampler": s_s, "target": {"node": node_idx, "path": "scale"}})

    root_idx = len(nodes_gltf)
    nodes_gltf.append({"name": "MegaMan_Explode_Root", "children": child_indices})

    gltf_doc = {
        "asset": {"version": "2.0", "generator": "BakersfieldQuake mm_explode_sim.py"},
        "scene": 0,
        "scenes": [{"name": "Scene", "nodes": [root_idx]}],
        "nodes": nodes_gltf,
        "meshes": meshes_gltf,
        "materials": [
            {
                "name": "MegaMan_Atlas",
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0},
                    "metallicFactor": 0.22,
                    "roughnessFactor": 0.58,
                },
                "doubleSided": False,
            },
            {
                "name": "Blast_Core_Flash",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [1.0, 0.72, 0.22, 1.0],
                    "metallicFactor": 0.0,
                    "roughnessFactor": 1.0,
                },
                "emissiveFactor": [1.0, 0.55, 0.12],
                "doubleSided": True,
            },
        ],
        "textures": [{"sampler": 0, "source": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "images": [{"bufferView": tex_bv, "mimeType": "image/png", "name": "megaman_explode_atlas"}],
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_buf)}],
        "animations": [{"name": "MegaMan_Explode", "samplers": samplers, "channels": channels}],
    }

    json_bytes = json.dumps(gltf_doc, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) & 3:
        json_bytes += b" "
    align4()

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_buf)
    os.makedirs(os.path.dirname(os.path.abspath(out_glb_path)), exist_ok=True)
    with open(out_glb_path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total_len))
        f.write(struct.pack("<I4s", len(json_bytes), b"JSON"))
        f.write(json_bytes)
        f.write(struct.pack("<I4s", len(bin_buf), b"BIN\x00"))
        f.write(bin_buf)

    print(f"Wrote GLB: {out_glb_path} ({os.path.getsize(out_glb_path) / 1e6:.2f} MB, "
          f"{len(all_items)} animated nodes, {sim['n_frames']} frames @ {sim['fps']} fps)")
