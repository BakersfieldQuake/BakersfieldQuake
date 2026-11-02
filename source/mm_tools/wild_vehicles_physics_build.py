r"""960 Hz Multi-Body Catastrophic Airborne-Flip & Multi-Roll Physics Simulator
+ Standalone Multi-Clip glTF 2.0 (.glb) & DarkPlaces MD3 Asset Builder for the 3 NEW Wild Vehicles:
  - veh_hdtruck   : Heavy-Duty Crew-Cab Diesel Dually Rig Truck (6 Flying Wheels!)
  - veh_schoolbus : Full-Size Type-C Conventional Yellow School Bus (6 Flying Wheels + STOP Sign!)
  - veh_gtcar     : V8 Street Muscle Fastback Car (4 Wide Flying Alloys + Corkscrew Multi-Roll!)

Produces:
  1. Standalone Multi-Clip Animated 3D glTF 2.0 (.glb) models in BakersfieldQuake\:
       veh_hdtruck.glb, veh_schoolbus.glb, veh_gtcar.glb
  2. DarkPlaces In-Game MD3 Models, Skins, Tone-Mapped Textures & Shaders in progs\ and scripts\:
       progs/veh_<kind>.md3          (36 frames: 0..15 Idle, 16..21 Flinch, 22..35 Violent CatchFire)
       progs/veh_<kind>.md3_0.skin & _1.skin
       progs/veh_<kind>_wreck.md3    (40 frames: skyward blast launch -> airborne barrel roll -> crash & ground roll!)
       progs/veh_<kind>_wheel.md3    (16 spinning frames)
       progs/veh_<kind>_hood.md3, _door.md3, _extra.md3, _bumper.md3
       scripts/vehicles.shader       (preserves all 4 original vehicles + van glass + adds the 3 new vehicles)
  3. Compressed simulation cache in source/mm_tools/out/wild_vehicles_sim_cache.npz for the HTML inspector.
"""
import io
import json
import math
import os
import subprocess
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import md3lib
import veh_physics_sim as vps
import wild_vehicles_specs_tex as wvs

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
PARTS_JSON = os.path.join(HERE, "out", "wild_vehicles_parts.json")
SIM_CACHE_NPZ = os.path.join(HERE, "out", "wild_vehicles_sim_cache.npz")
WILD_KINDS = wvs.WILD_KINDS
ORIG_KINDS = ("truck", "sedan", "van", "coupe")


def ensure_wild_blender_parts(force=False):
    blender_script = os.path.join(HERE, "blender_build_wild_vehicles.py")
    spec_script = os.path.join(HERE, "wild_vehicles_specs_tex.py")
    newest_src = max(os.path.getmtime(blender_script), os.path.getmtime(spec_script))
    if force or (not os.path.exists(PARTS_JSON)) or (newest_src > os.path.getmtime(PARTS_JSON)):
        print("Running headless Blender 5.2 wild vehicles builder...")
        r = subprocess.run([BLENDER_EXE, "-b", "--python", blender_script, "--", PARTS_JSON])
        if r.returncode != 0:
            sys.exit("Blender wild vehicles builder failed!")
    with open(PARTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def eval_wild_sprung_pose(kind, phase_01, mode="idle"):
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
        if kind == "hdtruck":
            # Heavy 6.7L Turbo-Diesel torque rock + vibrating vertical stacks & CB antenna
            roll = 0.96 * math.sin(tau) + 0.45 * math.sin(3.0 * tau + 0.4) + 0.22 * math.sin(7.0 * tau)
            pitch = 0.30 * math.cos(tau + 0.3) + 0.15 * math.sin(4.0 * tau)
            dz = 0.48 * math.sin(2.0 * tau) + 0.18 * math.cos(6.0 * tau)
            yaw = 0.10 * math.sin(2.0 * tau)
            child["hood_open_deg"] = 0.30 * (0.5 + 0.5 * math.sin(6.0 * tau))
            child["extra_dz"] = 0.32 * math.sin(8.0 * tau)
            child["detail_rx"] = 2.4 * math.sin(3.0 * tau)
        elif kind == "schoolbus":
            # Big inline-6 school bus leaf-spring sway & diesel chug
            roll = 0.85 * math.sin(tau) + 0.28 * math.cos(2.0 * tau)
            pitch = 0.44 * math.sin(tau - 0.5) + 0.18 * math.sin(4.0 * tau)
            dz = 0.54 * math.sin(tau + 0.4) + 0.20 * math.sin(6.0 * tau)
            yaw = 0.09 * math.cos(tau)
            child["door_ajar_deg"] = 0.35 * (0.5 + 0.5 * math.sin(4.0 * tau))
            child["detail_dz"] = 0.62 * math.sin(7.0 * tau)
        elif kind == "gtcar":
            # Aggressive cammed V8 muscle lope + periodic throttle rev blip!
            blip = math.exp(-(((phase_01 - 0.38) / 0.08) ** 2))
            roll = 0.46 * math.sin(2.0 * tau) + 1.35 * blip * math.sin(7.0 * tau)
            pitch = 0.26 * math.cos(2.0 * tau) - 0.72 * blip
            dz = 0.32 * math.sin(4.0 * tau) + 0.42 * blip
            yaw = 0.08 * math.sin(3.0 * tau)
            child["hood_open_deg"] = 0.35 * blip
            child["detail_dz"] = 0.85 * math.sin(10.0 * tau)
            child["detail_dy"] = 0.55 * math.cos(8.0 * tau)
        else:
            dz = roll = pitch = yaw = 0.0

    elif mode == "flinch":
        env = math.exp(-3.4 * phase_01) * math.sin(math.pi * min(1.0, phase_01 * 2.5))
        osc = math.exp(-3.0 * phase_01) * math.sin(2.0 * math.pi * 2.2 * phase_01)
        dz = -2.8 * env + 1.1 * osc
        roll = 4.8 * osc
        pitch = -3.2 * env
        yaw = 1.1 * osc
        child["hood_open_deg"] = max(0.0, 4.8 * osc)
        child["door_ajar_deg"] = max(0.0, 2.5 * osc)
        child["detail_dz"] = 1.4 * osc

    elif mode == "fire":
        # Intense violent pre-blast cook-off: hood bucking 18..28 deg, doors rattling ajar, suspension heaving!
        roll = 2.35 * math.sin(2.0 * tau) + 1.35 * math.sin(5.0 * tau + 0.7)
        pitch = 1.65 * math.cos(2.0 * tau) + 1.05 * math.sin(6.0 * tau)
        dz = 1.45 * math.sin(3.0 * tau) + 0.75 * math.cos(7.0 * tau)
        yaw = 0.65 * math.sin(3.0 * tau)
        child["hood_open_deg"] = 19.5 + 6.5 * math.sin(5.0 * tau) + 3.2 * math.cos(9.0 * tau)
        child["door_ajar_deg"] = 4.2 + 2.8 * math.sin(4.0 * tau)
        child["detail_dz"] = 1.65 * math.sin(9.0 * tau)
        child["extra_dz"] = 1.10 * math.cos(6.0 * tau)
    else:
        dz = roll = pitch = yaw = 0.0

    return dz, roll, pitch, yaw, child


def compute_wild_part_trs(veh_data, kind, phase_01, mode="idle"):
    parts = veh_data["parts"]
    sp = veh_data["spec"]
    dz, roll, pitch, yaw, child = eval_wild_sprung_pose(kind, phase_01, mode=mode)

    rc = np.array([0.0, 0.0, sp["wheel_r"]], dtype=np.float64)
    q_body = vps.q_euler_xyz(roll, pitch, yaw)
    R_body = vps.q_to_mat3(q_body)
    t_body = np.array([0.0, 0.0, dz], dtype=np.float64)

    out = {}
    for name, p in parts.items():
        p_org = np.array(p["origin"], dtype=np.float64)
        if name.startswith("wheel_"):
            out[name] = (p_org, np.array([0.0, 0.0, 0.0, 1.0]), np.ones(3))
            continue
        if name == "wreck_chassis" or name.startswith("shrap_"):
            out[name] = (p_org, np.array([0.0, 0.0, 0.0, 1.0]), np.full(3, 0.0001))
            continue

        loc_pos = p_org.copy()
        loc_q = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)

        if name == "hood" and child["hood_open_deg"] > 0.001:
            hp = np.array(p.get("hinge", [sp["x_cowl"], 0.0, sp["z_belt"]]), dtype=np.float64)
            q_h = vps.q_from_axis_angle((0.0, 1.0, 0.0), -math.radians(child["hood_open_deg"]))
            R_h = vps.q_to_mat3(q_h)
            loc_pos = hp + R_h @ (p_org - hp)
            loc_q = q_h
        elif name in ("door_l", "door_r") and child["door_ajar_deg"] > 0.001:
            sgn = 1.0 if name == "door_l" else -1.0
            hp = np.array([sp["x_door1"], sgn * sp["hw"] * 0.92, sp["z_belt"] * 0.7], dtype=np.float64)
            q_d = vps.q_from_axis_angle((0.0, 0.0, 1.0), -sgn * math.radians(child["door_ajar_deg"]))
            R_d = vps.q_to_mat3(q_d)
            loc_pos = hp + R_d @ (p_org - hp)
            loc_q = q_d
        elif name == "detail_vib":
            loc_pos = loc_pos + np.array([0.0, child["detail_dy"], child["detail_dz"]])
            if abs(child["detail_rx"]) > 0.001 or abs(child["detail_ry"]) > 0.001:
                loc_q = vps.q_euler_xyz(child["detail_rx"], child["detail_ry"], 0.0)
        elif name == "extra_part":
            loc_pos = loc_pos + np.array([0.0, 0.0, child["extra_dz"]])

        w_pos = rc + R_body @ (loc_pos - rc) + t_body
        w_q = vps.q_norm(vps.q_mul(q_body, loc_q))
        out[name] = (w_pos, w_q, np.ones(3))

    out["blast_flash"] = (np.array([0.0, 0.0, 32.0]), np.array([0.0, 0.0, 0.0, 1.0]), np.full(3, 0.0001))
    return out


def simulate_wild_explosion(veh_data, kind, intensity=1.0, fps=60, duration=7.5, substeps=16):
    """960 Hz Catastrophic Airborne-Launch, Mid-Air Secondary Blast & Multi-Turn Ground Barrel-Roll Simulator!
    - Frames 0..26 (0.00s..0.45s): Violent burning cook-off & pressure swell
    - Frame 27 (0.45s): Massive underbody detonation -> vehicle hulk launches HIGH into the air, corkscrews & flips!
    - Frame 58 (0.97s): Mid-air secondary fuel-tank rupture at the airborne tumbling car!
    - All 4 or 6 wheels blast off at extreme velocities, bounce 3..5 times elastically, bank into high-speed
      gyroscopic arcs, enter Euler-disk coin wobble, and flop onto their sidewalls!
    - Airborne car slams back onto the asphalt & executes 2.5..4+ realistic multi-contact ground barrel-rolls
      showering metallic sparks before skidding to a smoking rest!
    """
    rng = np.random.default_rng({"hdtruck": 5501, "schoolbus": 6602, "gtcar": 7703}[kind])
    parts = veh_data["parts"]
    sp = veh_data["spec"]
    n_frames = int(round(fps * duration)) + 1
    boom_frame = 27
    sec_boom_frame = 58
    dt_frame = 1.0 / fps
    dt = dt_frame / substeps
    g_acc = np.array([0.0, 0.0, -560.0], dtype=np.float64)

    wheel_names = sorted([nm for nm in parts if nm.startswith("wheel_")])
    shrap_names = sorted([nm for nm in parts if nm.startswith("shrap_")], key=lambda s: int(s.split("_")[1]))
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

    # 1. Pre-explosion violent cook-off & pressure swell (0 .. boom_frame - 1)
    for fi in range(boom_frame):
        t_frac = fi / float(boom_frame)
        pose = compute_wild_part_trs(veh_data, kind, (fi * 0.11) % 1.0, mode="fire")
        swell = 1.0 + 0.055 * (t_frac ** 3)
        for nm, (p, q, sc) in pose.items():
            tracks[nm]["pos"][fi] = p
            tracks[nm]["rot"][fi] = q
            tracks[nm]["scl"][fi] = sc * (swell if nm in ("chassis", "hood") else 1.0)

    pose_at_boom = compute_wild_part_trs(veh_data, kind, (boom_frame * 0.11) % 1.0, mode="fire")

    w_rad = sp["wheel_r"]
    w_half_w = sp["wheel_w"] * 0.5

    # 2. Extreme Flying Wheel Trajectories (all 4 or 6 wheels blast sky-high & far across the lot!)
    base_wheel_cfgs = {
        "wheel_fl":  dict(vel=[275.0,  435.0, 845.0], spin=-54.0, lean=20.0,  side=1.0,  max_b=5),
        "wheel_fr":  dict(vel=[385.0, -515.0, 560.0], spin=-62.0, lean=-25.0, side=-1.0, max_b=4),
        "wheel_rl":  dict(vel=[-335.0, 475.0, 710.0], spin=48.0,  lean=-22.0, side=-1.0, max_b=4),
        "wheel_rr":  dict(vel=[-285.0,-445.0, 775.0], spin=-46.0, lean=26.0,  side=1.0,  max_b=5),
        "wheel_rl2": dict(vel=[-155.0, 555.0, 625.0], spin=-56.0, lean=19.0,  side=1.0,  max_b=4),
        "wheel_rr2": dict(vel=[145.0, -575.0, 650.0], spin=52.0,  lean=-23.0, side=-1.0, max_b=4),
    }

    wheel_states = {}
    for wn in wheel_names:
        cfg = base_wheel_cfgs[wn]
        p0, _, _ = pose_at_boom[wn]
        vx, vy, vz = cfg["vel"]
        v0 = np.array([
            (vx + rng.uniform(-35, 35)) * intensity,
            (vy + rng.uniform(-35, 35)) * intensity,
            (vz + rng.uniform(-30, 55)) * intensity,
        ], dtype=np.float64)
        wheel_states[wn] = {
            "pos": p0 + np.array([0.0, 0.0, 3.0]),
            "vel": v0,
            "mode": "air",
            "bounces": 0,
            "max_bounces": cfg["max_b"],
            "yaw": math.atan2(v0[1], v0[0]),
            "lean": math.radians(cfg["lean"]),
            "lean_vel": cfg["side"] * 1.45,
            "side": cfg["side"],
            "spin": 0.0,
            "spin_rate": cfg["spin"] * intensity,
            "roll_spd": 0.0,
            "precess": 0.0,
        }

    # 3. Vehicle-Specific Airborne Flip & Ground Multi-Roll Launch Profiles!
    # Right-hand rule verified:
    #   vy > 0 (+Y left)  pairs with wx < 0 so airborne barrel-roll accelerates ground roll!
    #   vy < 0 (-Y right) pairs with wx > 0 so airborne barrel-roll accelerates ground roll!
    #   vx > 0 (+X fwd)   pairs with wy > 0 so nose-over-tail pitch reinforces forward tumble!
    if kind == "gtcar":
        # Lightest & wildest: skyrockets ~11.5m up, corkscrew double-flips, & barrel-rolls 3.5-4x on asphalt!
        wreck_cfg = dict(
            vel=[175.0 * intensity, 255.0 * intensity, 695.0 * intensity],
            omega=[-9.6 * intensity, 3.5 * intensity, 2.1 * intensity],
            sec_dv=[35.0 * intensity, 75.0 * intensity, 145.0 * intensity],
            sec_dw=[-2.8 * intensity, 0.9 * intensity, 0.6 * intensity],
            e=0.45, mu=0.52, lin_damp=0.14, ang_damp=0.22,
        )
    elif kind == "hdtruck":
        # Heavy diesel rig: huge torque launch ~9.5m up, nose-high double barrel-roll, & thunderous 3x ground roll!
        wreck_cfg = dict(
            vel=[155.0 * intensity, -235.0 * intensity, 625.0 * intensity],
            omega=[8.6 * intensity, 3.0 * intensity, -1.8 * intensity],
            sec_dv=[30.0 * intensity, -70.0 * intensity, 135.0 * intensity],
            sec_dw=[2.5 * intensity, 0.8 * intensity, -0.5 * intensity],
            e=0.41, mu=0.54, lin_damp=0.15, ang_damp=0.25,
        )
    else:  # schoolbus
        # 35-foot yellow school bus: double diesel tank blast heaves the entire bus into the air & barrel-rolls it!
        wreck_cfg = dict(
            vel=[130.0 * intensity, 225.0 * intensity, 585.0 * intensity],
            omega=[-7.8 * intensity, 2.1 * intensity, 1.4 * intensity],
            sec_dv=[25.0 * intensity, 68.0 * intensity, 130.0 * intensity],
            sec_dw=[-2.3 * intensity, 0.6 * intensity, 0.4 * intensity],
            e=0.39, mu=0.55, lin_damp=0.16, ang_damp=0.26,
        )

    body_launch = {
        "wreck_chassis": wreck_cfg,
        "hood":       dict(vel=[(140.0 + rng.uniform(-45, 55)) * intensity, rng.uniform(-130, 130) * intensity, (820.0 + rng.uniform(0, 110)) * intensity],
                           omega=[rng.uniform(-11, 11), -15.5 + rng.uniform(-3, 3), rng.uniform(-8, 8)],
                           e=0.44, mu=0.42, lin_damp=0.14, ang_damp=0.34),
        "door_l":     dict(vel=[rng.uniform(-95, 95) * intensity, (545.0 + rng.uniform(0, 95)) * intensity, (465.0 + rng.uniform(0, 85)) * intensity],
                           omega=[-12.5, rng.uniform(-7, 7), 8.8],
                           e=0.40, mu=0.44, lin_damp=0.16, ang_damp=0.38),
        "door_r":     dict(vel=[rng.uniform(-95, 95) * intensity, (-560.0 - rng.uniform(0, 95)) * intensity, (485.0 + rng.uniform(0, 85)) * intensity],
                           omega=[13.0, rng.uniform(-7, 7), -9.2],
                           e=0.40, mu=0.44, lin_damp=0.16, ang_damp=0.38),
        "extra_part": dict(vel=[(-345.0 + rng.uniform(-65, 45)) * intensity, rng.uniform(-155, 155) * intensity, (710.0 + rng.uniform(0, 95)) * intensity],
                           omega=[rng.uniform(-10, 10), 12.8, rng.uniform(-8, 8)],
                           e=0.42, mu=0.44, lin_damp=0.15, ang_damp=0.36),
        "bumper_f":   dict(vel=[(525.0 + rng.uniform(0, 95)) * intensity, rng.uniform(-125, 125) * intensity, (365.0 + rng.uniform(0, 75)) * intensity],
                           omega=[rng.uniform(-9, 9), 11.2, rng.uniform(-7, 7)],
                           e=0.40, mu=0.48, lin_damp=0.18, ang_damp=0.42),
        "bumper_r":   dict(vel=[(-510.0 - rng.uniform(0, 95)) * intensity, rng.uniform(-125, 125) * intensity, (345.0 + rng.uniform(0, 75)) * intensity],
                           omega=[rng.uniform(-9, 9), -11.4, rng.uniform(-7, 7)],
                           e=0.40, mu=0.48, lin_damp=0.18, ang_damp=0.42),
        "detail_vib": dict(vel=[-395.0 * intensity, -235.0 * intensity, 540.0 * intensity],
                           omega=[14.5, -11.2, 12.0],
                           e=0.46, mu=0.38, lin_damp=0.15, ang_damp=0.35),
    }
    for si, snm in enumerate(shrap_names):
        ang = 2.0 * math.pi * si / float(len(shrap_names)) + rng.uniform(-0.20, 0.20)
        spd_xy = (380.0 + rng.uniform(0.0, 410.0)) * intensity
        body_launch[snm] = dict(
            vel=[math.cos(ang) * spd_xy, math.sin(ang) * spd_xy, (420.0 + rng.uniform(40.0, 440.0)) * intensity],
            omega=[rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(-20, 20)],
            e=0.46, mu=0.42, lin_damp=0.14, ang_damp=0.34,
        )

    rb_states = {}
    for nm, cfg in body_launch.items():
        v_arr = np.array(parts[nm]["verts"], dtype=np.float64)
        if nm == "wreck_chassis" and "roll_hull" in parts[nm]:
            hull_v = np.array(parts[nm]["roll_hull"], dtype=np.float64)
        elif len(v_arr) > 48:
            step_i = max(1, len(v_arr) // 48)
            hull_v = np.vstack([v_arr[::step_i], v_arr[np.argsort(v_arr[:, 2])[:12]]])
        else:
            hull_v = v_arr

        ext = np.maximum(np.ptp(hull_v, axis=0), 5.0)
        if nm == "wreck_chassis":
            # Realistic automotive mass distribution: lower roll inertia around longitudinal X axis
            # so roof/pillar/fender impacts convert lateral motion smoothly into dramatic barrel rolls!
            ixx = ((ext[1] * 0.78) ** 2 + (ext[2] * 0.78) ** 2) / 12.0
            iyy = ((ext[0] * 0.82) ** 2 + ext[2] ** 2) / 12.0
            izz = ((ext[0] * 0.82) ** 2 + ext[1] ** 2) / 12.0
        else:
            ixx = (ext[1] ** 2 + ext[2] ** 2) / 12.0
            iyy = (ext[0] ** 2 + ext[2] ** 2) / 12.0
            izz = (ext[0] ** 2 + ext[1] ** 2) / 12.0

        p0 = np.array(parts[nm]["origin"], dtype=np.float64)
        if nm == "wreck_chassis":
            p0 = p0 + np.array([0.0, 0.0, 6.0])
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
            "bounces": 0,
            "max_z": float(p0[2]),
            "cum_rot_rad": 0.0,
        }

    # 4. Step 960 Hz simulation from boom_frame .. n_frames - 1!
    for fi in range(boom_frame, n_frames):
        age = (fi - boom_frame) * dt_frame

        # Mid-air secondary fuel-cell explosion kick when wreck_chassis is flipping in the sky!
        if fi == sec_boom_frame:
            wst = rb_states["wreck_chassis"]
            wst["vel"] += np.array(wreck_cfg["sec_dv"], dtype=np.float64)
            wst["omega"] += np.array(wreck_cfg["sec_dw"], dtype=np.float64)
            sparks.append({
                "t": round(fi * dt_frame, 3),
                "pos": [round(float(wst["pos"][0]), 2), round(float(wst["pos"][1]), 2), round(float(wst["pos"][2]), 2)],
                "intensity": 1.0,
                "kind": "airburst",
            })

        tracks["chassis"]["pos"][fi] = tracks["chassis"]["pos"][boom_frame - 1]
        tracks["chassis"]["rot"][fi] = tracks["chassis"]["rot"][boom_frame - 1]
        tracks["chassis"]["scl"][fi] = np.full(3, 0.0001, dtype=np.float32)

        # Primary detonation flash (0..0.48s) + Secondary mid-air fuel burst flash (sec_boom_frame .. +0.34s)!
        sec_age = (fi - sec_boom_frame) * dt_frame
        if age < 0.48:
            fl_s = (0.55 + 3.45 * math.sin(math.pi * min(1.0, age / 0.15))) * max(0.001, 1.0 - age / 0.48)
            tracks["blast_flash"]["pos"][fi] = [0.0, 0.0, 32.0 + age * 65.0]
            tracks["blast_flash"]["rot"][fi] = vps.q_from_axis_angle((0.0, 0.0, 1.0), age * 9.5)
            tracks["blast_flash"]["scl"][fi] = [fl_s, fl_s, fl_s]
        elif 0.0 <= sec_age < 0.34:
            fl_s = (0.45 + 2.35 * math.sin(math.pi * min(1.0, sec_age / 0.11))) * max(0.001, 1.0 - sec_age / 0.34)
            tracks["blast_flash"]["pos"][fi] = rb_states["wreck_chassis"]["pos"]
            tracks["blast_flash"]["rot"][fi] = vps.q_from_axis_angle((1.0, 0.5, 0.3), sec_age * 12.0)
            tracks["blast_flash"]["scl"][fi] = [fl_s, fl_s, fl_s]
        else:
            tracks["blast_flash"]["pos"][fi] = [0.0, 0.0, 32.0]
            tracks["blast_flash"]["rot"][fi] = [0.0, 0.0, 0.0, 1.0]
            tracks["blast_flash"]["scl"][fi] = [0.0001, 0.0001, 0.0001]

        for nm, st in rb_states.items():
            tracks[nm]["pos"][fi] = st["pos"]
            tracks[nm]["rot"][fi] = st["q"]
            tracks[nm]["scl"][fi] = [1.0, 1.0, 1.0]

        for wn, ws in wheel_states.items():
            cy, sy = math.cos(ws["yaw"]), math.sin(ws["yaw"])
            cl, sl = math.cos(ws["lean"]), math.sin(ws["lean"])
            cs, ss = math.cos(ws["spin"]), math.sin(ws["spin"])
            Rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
            Rx = np.array([[1.0, 0.0, 0.0], [0.0, cl, -sl], [0.0, sl, cl]])
            Ry = np.array([[cs, 0.0, ss], [0.0, 1.0, 0.0], [-ss, 0.0, cs]])
            tracks[wn]["pos"][fi] = ws["pos"]
            tracks[wn]["rot"][fi] = vps.mat3_to_q(Rz @ Rx @ Ry)
            tracks[wn]["scl"][fi] = [1.0, 1.0, 1.0]

        if fi == n_frames - 1:
            break

        # Advance 16 physics substeps (960 Hz!)
        for _ in range(substeps):
            # --- A. 3D Rigid Bodies w/ Multi-Vertex Weighted Contact Manifold (True Ground Barrel-Rolling!)
            for nm, st in rb_states.items():
                st["spark_cd"] = max(0.0, st["spark_cd"] - dt)
                st["vel"] += g_acc * dt
                st["vel"] *= max(0.0, 1.0 - st["lin_damp"] * dt)
                st["omega"] *= max(0.0, 1.0 - st["ang_damp"] * dt)
                st["pos"] += st["vel"] * dt
                w_mag = float(np.linalg.norm(st["omega"]))
                st["cum_rot_rad"] += w_mag * dt
                st["q"] = vps.integrate_q(st["q"], st["omega"], dt)
                if st["pos"][2] > st["max_z"]:
                    st["max_z"] = float(st["pos"][2])

                Rm = vps.q_to_mat3(st["q"])
                pts_w = st["hull"] @ Rm.T + st["pos"]
                pen_mask = pts_w[:, 2] < 0.0

                if np.any(pen_mask):
                    pens = -pts_w[pen_mask, 2]
                    max_pen = float(np.max(pens))
                    st["pos"][2] += max_pen

                    # Penetration-weighted contact centroid across all touching roof/pillar/fender vertices!
                    w_c = pens / max(1e-9, float(np.sum(pens)))
                    pt_c = np.sum(pts_w[pen_mask] * w_c[:, None], axis=0)
                    pt_c[2] = 0.0

                    r_vec = pt_c - st["pos"]
                    v_pt = st["vel"] + np.cross(st["omega"], r_vec)
                    vn = float(v_pt[2])

                    if vn < 0.0:
                        inv_I_w = Rm @ st["inv_I_body"] @ Rm.T
                        rn = np.cross(r_vec, np.array([0.0, 0.0, 1.0]))
                        denom = 1.0 + float(np.dot(np.cross(inv_I_w @ rn, r_vec), np.array([0.0, 0.0, 1.0])))

                        if vn < -60.0:
                            e_eff = st["e"]
                            st["bounces"] += 1
                        elif vn < -22.0:
                            e_eff = st["e"] * ((abs(vn) - 22.0) / 38.0)
                        else:
                            e_eff = 0.0

                        jn = -(1.0 + e_eff) * vn / max(1e-6, denom)
                        imp_n = np.array([0.0, 0.0, jn])
                        st["vel"] += imp_n
                        st["omega"] += inv_I_w @ np.cross(r_vec, imp_n)

                        # Re-evaluate tangential slip velocity after normal bounce & apply Coulomb rolling friction!
                        v_pt2 = st["vel"] + np.cross(st["omega"], r_vec)
                        vt = np.array([v_pt2[0], v_pt2[1], 0.0])
                        vt_len = float(np.linalg.norm(vt))
                        if vt_len > 1e-4:
                            t_hat = vt / vt_len
                            rt = np.cross(r_vec, t_hat)
                            denom_t = 1.0 + float(np.dot(np.cross(inv_I_w @ rt, r_vec), t_hat))
                            jt = min(st["mu"] * jn, vt_len / max(1e-6, denom_t))
                            imp_t = -jt * t_hat
                            st["vel"] += imp_t
                            st["omega"] += inv_I_w @ np.cross(r_vec, imp_t)

                        # Emit intense scraping/impact sparks on roof/fender/panel crunches!
                        impact_e = abs(vn) + 0.35 * vt_len
                        if impact_e > 75.0 and st["spark_cd"] <= 0.0 and len(sparks) < 380:
                            sparks.append({
                                "t": round(fi * dt_frame, 3),
                                "pos": [round(float(pt_c[0]), 2), round(float(pt_c[1]), 2), 1.5],
                                "intensity": round(min(1.0, impact_e / 320.0), 2),
                                "kind": "wreck" if nm == "wreck_chassis" else "metal",
                            })
                            st["spark_cd"] = 0.055 if nm == "wreck_chassis" else 0.095

                    # Natural late-stage settle damping ONLY once rolling speed has genuinely spent itself!
                    spd_tot = float(np.linalg.norm(st["vel"]))
                    if age > 4.6 and spd_tot < 48.0 and abs(st["vel"][2]) < 18.0:
                        st["vel"] *= max(0.0, 1.0 - 4.5 * dt)
                        st["omega"] *= max(0.0, 1.0 - 5.5 * dt)

            # --- B. 4 or 6 Wild Flying & Gyroscopic Rolling Wheels!
            for wn, ws in wheel_states.items():
                al = abs(ws["lean"])
                z_contact = w_rad * math.cos(al) + w_half_w * math.sin(al)

                if ws["mode"] == "air":
                    ws["vel"] += g_acc * dt
                    ws["pos"] += ws["vel"] * dt
                    ws["spin"] += ws["spin_rate"] * dt
                    ws["lean"] = max(-1.35, min(1.35, ws["lean"] + ws["lean_vel"] * dt * 0.42))
                    if math.hypot(ws["vel"][0], ws["vel"][1]) > 25.0:
                        ws["yaw"] = math.atan2(ws["vel"][1], ws["vel"][0])

                    if ws["pos"][2] <= z_contact:
                        ws["pos"][2] = z_contact
                        if len(sparks) < 380:
                            sparks.append({
                                "t": round(fi * dt_frame, 3),
                                "pos": [round(float(ws["pos"][0]), 2), round(float(ws["pos"][1]), 2), 1.2],
                                "intensity": round(min(1.0, abs(float(ws["vel"][2])) / 450.0), 2),
                                "kind": "tire",
                            })
                        if ws["vel"][2] < -65.0 and ws["bounces"] < ws["max_bounces"]:
                            ws["vel"][2] = -ws["vel"][2] * 0.76
                            ws["vel"][0] *= 0.91
                            ws["vel"][1] *= 0.91
                            ws["bounces"] += 1
                            ws["lean_vel"] = -ws["lean_vel"] * 0.68 + rng.uniform(-0.6, 0.6)
                        else:
                            ws["mode"] = "roll"
                            spd_xy = math.hypot(ws["vel"][0], ws["vel"][1])
                            ws["roll_spd"] = max(210.0, min(420.0, spd_xy))
                            ws["vel"][:] = 0.0
                            ws["lean"] = ws["side"] * math.radians(18.0 + rng.uniform(0.0, 12.0))
                else:
                    spd = ws["roll_spd"]
                    if spd > 1.5:
                        step = spd * dt
                        ws["pos"][0] += math.cos(ws["yaw"]) * step
                        ws["pos"][1] += math.sin(ws["yaw"]) * step
                        ws["spin"] -= step / max(4.0, w_rad)
                        ws["yaw"] -= math.sin(ws["lean"]) * (1.95 / max(18.0, spd * 0.13)) * step
                        ws["roll_spd"] = max(0.0, spd * (1.0 - 0.46 * dt) - 12.5 * dt)

                        spd_frac = min(1.0, ws["roll_spd"] / 230.0)
                        target_lean = math.radians(18.0 + ((1.0 - spd_frac) ** 1.8) * 69.5)
                        ws["precess"] += (12.0 + (1.0 - spd_frac) * 16.0) * dt
                        wob = math.sin(ws["precess"]) * math.radians(8.5) * spd_frac
                        ws["lean"] = ws["side"] * target_lean + wob
                        if ws["roll_spd"] < 60.0:
                            ws["yaw"] -= ws["side"] * 3.0 * dt
                    else:
                        ws["lean"] = ws["side"] * math.radians(87.5)

                    al2 = abs(ws["lean"])
                    ws["pos"][2] = w_rad * math.cos(al2) + w_half_w * math.sin(al2)

    wst = rb_states["wreck_chassis"]
    dist_xy = float(math.hypot(wst["pos"][0], wst["pos"][1]))
    rot_deg = math.degrees(wst["cum_rot_rad"])
    max_wheel_dist = max(float(math.hypot(ws["pos"][0], ws["pos"][1])) for ws in wheel_states.values())
    print(
        f"    [{kind:9s}] wreck max_z={wst['max_z']:5.1f}u ({wst['max_z']/39.37:4.1f}m) | "
        f"total_spin={rot_deg:6.0f} deg ({rot_deg/360.0:3.1f} rev) | "
        f"roll_dist={dist_xy:5.1f}u | max_wheel_dist={max_wheel_dist:5.1f}u | sparks={len(sparks)}"
    )

    return {
        "kind": kind,
        "fps": fps,
        "n_frames": n_frames,
        "boom_frame": boom_frame,
        "sec_boom_frame": sec_boom_frame,
        "tracks": tracks,
        "sparks": sparks,
    }


def export_wild_vehicle_glb(veh_data, kind, explode_sim, intact_atlas_im, out_glb_path):
    """Exports standalone multi-clip glTF 2.0 (.glb) with 'Idle', 'CatchFire', and 'Explode'."""
    SCALE = 1.0 / 39.37
    parts = dict(veh_data["parts"])
    parts["blast_flash"] = vps.build_blast_starburst_mesh()
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
        acc = {"bufferView": bv_idx, "componentType": comp_type, "count": int(len(arr)), "type": acc_type}
        if acc_type == "SCALAR":
            acc["min"] = [float(arr.min())]
            acc["max"] = [float(arr.max())]
        else:
            acc["min"] = [float(x) for x in arr.min(axis=0)]
            acc["max"] = [float(x) for x in arr.max(axis=0)]
        idx = len(accessors)
        accessors.append(acc)
        return idx

    png_buf = io.BytesIO()
    intact_atlas_im.save(png_buf, format="PNG", optimize=True)
    tex_bv = add_bv(png_buf.getvalue())

    meshes_gltf = []
    nodes_gltf = []
    node_map = {}
    rest_all = compute_wild_part_trs(veh_data, kind, 0.0, mode="idle")

    for nm in ordered_names:
        p = parts[nm]
        vq = np.array(p["verts"], dtype=np.float32)
        nq = np.array(p["norms"], dtype=np.float32)
        uv = np.array(p["uvs"], dtype=np.float32)
        tr = np.array(p["tris"], dtype=np.uint16).reshape(-1)

        vg = np.column_stack([vq[:, 1], vq[:, 2], vq[:, 0]]) * SCALE
        ng = np.column_stack([nq[:, 1], nq[:, 2], nq[:, 0]])
        ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-8)

        acc_p = add_acc(vg.astype(np.float32), 5126, "VEC3", target=34962)
        acc_n = add_acc(ng.astype(np.float32), 5126, "VEC3", target=34962)
        acc_u = add_acc(uv.astype(np.float32), 5126, "VEC2", target=34962)
        acc_i = add_acc(tr.astype(np.uint16), 5123, "SCALAR", target=34963)

        mesh_idx = len(meshes_gltf)
        meshes_gltf.append({
            "name": f"{kind}_{nm}",
            "primitives": [{
                "attributes": {"POSITION": acc_p, "NORMAL": acc_n, "TEXCOORD_0": acc_u},
                "indices": acc_i,
                "material": 1 if nm == "blast_flash" else 0,
            }],
        })

        rp, rq, rs = rest_all[nm]
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
    nodes_gltf.append({"name": f"Vehicle_{kind}_Root", "children": list(node_map.values())})

    def pack_clip(clip_name, fps_c, pos_dict, rot_dict, scl_dict, step_scale_set=()):
        nf = len(next(iter(pos_dict.values())))
        times = (np.arange(nf, dtype=np.float32) / float(fps_c))
        t_acc = add_acc(times, 5126, "SCALAR")
        samplers, channels = [], []
        for nm in ordered_names:
            ni = node_map[nm]
            pq, rq, sq = pos_dict[nm], rot_dict[nm], scl_dict[nm]
            pg = np.column_stack([pq[:, 1], pq[:, 2], pq[:, 0]]).astype(np.float32) * SCALE
            rg = np.column_stack([rq[:, 1], rq[:, 2], rq[:, 0], rq[:, 3]]).astype(np.float32)
            rg /= np.maximum(np.linalg.norm(rg, axis=1, keepdims=True), 1e-8)
            sg = np.column_stack([sq[:, 1], sq[:, 2], sq[:, 0]]).astype(np.float32)

            acc_t = add_acc(pg, 5126, "VEC3")
            acc_r = add_acc(rg, 5126, "VEC4")
            acc_s = add_acc(sg, 5126, "VEC3")

            st_i = len(samplers); samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": acc_t})
            sr_i = len(samplers); samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": acc_r})
            ss_i = len(samplers); samplers.append({"input": t_acc, "interpolation": "STEP" if nm in step_scale_set else "LINEAR", "output": acc_s})
            channels.append({"sampler": st_i, "target": {"node": ni, "path": "translation"}})
            channels.append({"sampler": sr_i, "target": {"node": ni, "path": "rotation"}})
            channels.append({"sampler": ss_i, "target": {"node": ni, "path": "scale"}})
        return {"name": clip_name, "samplers": samplers, "channels": channels}

    nf_idle = 121
    idle_p = {nm: np.zeros((nf_idle, 3), dtype=np.float32) for nm in ordered_names}
    idle_r = {nm: np.zeros((nf_idle, 4), dtype=np.float32) for nm in ordered_names}
    idle_s = {nm: np.ones((nf_idle, 3), dtype=np.float32) for nm in ordered_names}
    for fi in range(nf_idle):
        pose = compute_wild_part_trs(veh_data, kind, (fi / 120.0) % 1.0, mode="idle")
        for nm, (p, q, sc) in pose.items():
            idle_p[nm][fi], idle_r[nm][fi], idle_s[nm][fi] = p, q, sc

    nf_fire = 181
    fire_p = {nm: np.zeros((nf_fire, 3), dtype=np.float32) for nm in ordered_names}
    fire_r = {nm: np.zeros((nf_fire, 4), dtype=np.float32) for nm in ordered_names}
    fire_s = {nm: np.ones((nf_fire, 3), dtype=np.float32) for nm in ordered_names}
    for fi in range(nf_fire):
        t = fi / 60.0
        pose = (
            compute_wild_part_trs(veh_data, kind, (t % 0.28) / 0.28, mode="flinch")
            if t < 0.85
            else compute_wild_part_trs(veh_data, kind, ((t - 0.85) * 1.45) % 1.0, mode="fire")
        )
        for nm, (p, q, sc) in pose.items():
            fire_p[nm][fi], fire_r[nm][fi], fire_s[nm][fi] = p, q, sc

    tr_ex = explode_sim["tracks"]
    step_set = {"chassis", "wreck_chassis"} | {nm for nm in ordered_names if nm.startswith("shrap_")}
    clips = [
        pack_clip("Idle", 60, idle_p, idle_r, idle_s),
        pack_clip("CatchFire", 60, fire_p, fire_r, fire_s),
        pack_clip(
            "Explode",
            explode_sim["fps"],
            {nm: tr_ex[nm]["pos"] for nm in ordered_names},
            {nm: tr_ex[nm]["rot"] for nm in ordered_names},
            {nm: tr_ex[nm]["scl"] for nm in ordered_names},
            step_scale_set=step_set,
        ),
    ]

    import struct as _st
    gltf_doc = {
        "asset": {"version": "2.0", "generator": "BakersfieldQuake wild_vehicles_physics_build.py"},
        "scene": 0,
        "scenes": [{"name": f"Scene_{kind}", "nodes": [root_idx]}],
        "nodes": nodes_gltf,
        "meshes": meshes_gltf,
        "animations": clips,
        "materials": [
            {
                "name": f"Vehicle_{kind}_Atlas",
                "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.24, "roughnessFactor": 0.42},
                "doubleSided": True,
            },
            {
                "name": "Blast_Core_Flash",
                "pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.72, 0.20, 1.0], "metallicFactor": 0.0, "roughnessFactor": 1.0},
                "emissiveFactor": [1.0, 0.56, 0.12],
                "doubleSided": True,
            },
        ],
        "textures": [{"sampler": 0, "source": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "images": [{"bufferView": tex_bv, "mimeType": "image/png", "name": f"veh_{kind}_atlas"}],
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
        f.write(_st.pack("<4sII", b"glTF", 2, total_len))
        f.write(_st.pack("<I4s", len(json_bytes), b"JSON"))
        f.write(json_bytes)
        f.write(_st.pack("<I4s", len(bin_blob), b"BIN\x00"))
        f.write(bin_blob)


def _slice_part(part, tri_start, tri_end, sub_name):
    sub_tris_orig = part["tris"][tri_start:tri_end]
    remap = {}
    verts, norms, uvs, tris = [], [], [], []
    for t in sub_tris_orig:
        nt = []
        for vi in t:
            if vi not in remap:
                remap[vi] = len(verts)
                verts.append(part["verts"][vi])
                norms.append(part["norms"][vi])
                uvs.append(part["uvs"][vi])
            nt.append(remap[vi])
        tris.append(nt)
    return {"name": sub_name, "origin": part["origin"], "verts": verts, "norms": norms, "uvs": uvs, "tris": tris}


def build_wild_intact_md3_surfaces(veh_data, kind, shader_default):
    parts = veh_data["parts"]
    wheel_names = sorted([nm for nm in parts if nm.startswith("wheel_")])
    frame_specs = (
        [("idle", i / 16.0) for i in range(16)]
        + [("flinch", (i + 0.5) / 6.0) for i in range(6)]
        + [("fire", i / 14.0) for i in range(14)]
    )
    poses = [compute_wild_part_trs(veh_data, kind, ph, mode=md) for md, ph in frame_specs]

    def assemble(surf_name, item_list):
        tris_comb, st_comb, part_arrays = [], [], []
        v_base = 0
        for item in item_list:
            pnm, p = (item, parts[item]) if isinstance(item, str) else item
            va = np.array(p["verts"], dtype=np.float64)
            na = np.array(p["norms"], dtype=np.float64)
            part_arrays.append((pnm, va, na))
            st_comb.extend(tuple(u) for u in p["uvs"])
            for a, b, c in p["tris"]:
                tris_comb.append((a + v_base, b + v_base, c + v_base))
            v_base += len(va)
        frames = []
        for pose in poses:
            vv_f, nn_f = [], []
            for pnm, va, na in part_arrays:
                pos, q, _ = pose[pnm]
                Rm = vps.q_to_mat3(q)
                vp = np.clip((va @ Rm.T) + pos, -505.0, 505.0)
                np_r = na @ Rm.T
                vv_f.extend(map(tuple, vp.tolist()))
                nn_f.extend(map(tuple, np_r.tolist()))
            frames.append((vv_f, nn_f))
        return dict(name=surf_name, shader=shader_default, tris=tris_comb, st=st_comb, frames=frames)

    # Split body cleanly so every MD3 surface stays well below 4096 vertices!
    ch = parts["chassis"]
    if len(ch["verts"]) > 2400:
        mid_t = len(ch["tris"]) // 2
        surfs = [
            assemble("body_a", [("chassis", _slice_part(ch, 0, mid_t, "ch_a"))]),
            assemble("body_b", [("chassis", _slice_part(ch, mid_t, len(ch["tris"]), "ch_b"))]),
            assemble("panels", ["hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib"]),
            assemble("wheels", wheel_names),
        ]
    else:
        surfs = [
            assemble("body", ["chassis", "hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib"]),
            assemble("wheels", wheel_names),
        ]
    return surfs


def build_wild_wreck_md3_surfaces(veh_data, sim, shader_burn):
    """Builds 40-frame veh_<kind>_wreck.md3 capturing the full skyward launch, mid-air barrel roll,
    ground crash, and multi-turn barrel roll across the lot (clamped cleanly inside MD3 +-505 bounds)!"""
    p = veh_data["parts"]["wreck_chassis"]
    va = np.array(p["verts"], dtype=np.float64)
    na = np.array(p["norms"], dtype=np.float64)
    bf = sim["boom_frame"]
    tr = sim["tracks"]["wreck_chassis"]
    # Sample 40 frames across 5.4s of airborne flip & ground barrel-rolling!
    span = min(sim["n_frames"] - 1 - bf, int(5.4 * sim["fps"]))
    sample_fis = [bf + int(round(span * k / 38.0)) for k in range(39)] + [sim["n_frames"] - 1]

    frames = []
    for fi in sample_fis:
        pos = tr["pos"][fi].astype(np.float64)
        q = tr["rot"][fi].astype(np.float64)
        Rm = vps.q_to_mat3(q)
        # Preserve full airborne height (up to +340u) & wild roll/pitch/yaw + scaled XY ground-roll travel inside MD3 bounds!
        pos_md3 = np.array([
            max(-280.0, min(280.0, pos[0] * 0.55)),
            max(-280.0, min(280.0, pos[1] * 0.55)),
            max(0.0, min(350.0, pos[2] * 0.72)),
        ], dtype=np.float64)
        vp = np.clip((va @ Rm.T) + pos_md3, -505.0, 505.0)
        np_r = na @ Rm.T
        frames.append((list(map(tuple, vp.tolist())), list(map(tuple, np_r.tolist()))))

    return [dict(name="wreck", shader=shader_burn, tris=[tuple(t) for t in p["tris"]], st=[tuple(u) for u in p["uvs"]], frames=frames)]


def update_vehicles_shader(scripts_dir):
    os.makedirs(scripts_dir, exist_ok=True)
    lines = ["// written by mm_tools/wild_vehicles_physics_build.py (all 7 vehicles)\n\n"]
    for kind in ORIG_KINDS + WILD_KINDS:
        for variant in ("tex", "burn"):
            sh = f"progs/veh_{kind}_{variant}"
            lines.append(
                f"{sh}\n{{\n\tcull none\n"
                f"\t{{\n\t\tmap {sh}\n\t\trgbGen lightingDiffuse\n\t}}\n"
                f"\t{{\n\t\tmap {sh}_glow\n\t\tblendfunc add\n\t\trgbGen identity\n\t}}\n}}\n\n"
            )
    for g_sh in ("progs/veh_van_glass", "progs/veh_van_glass_burn"):
        lines.append(
            f"{g_sh}\n{{\n\tcull none\n\t{{\n\t\tmap {g_sh}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n\n"
        )
    lines.append(
        "progs/veh_van_nodraw\n{\n\tcull none\n\t{\n\t\tmap progs/veh_van_glass\n\t\tblendfunc GL_ZERO GL_ONE\n\t}\n}\n\n"
    )
    lines.append(
        "progs/veh_blast_flash\n{\n\tcull none\n\t{\n\t\tmap progs/veh_blast_flash\n\t\tblendfunc add\n\t\trgbGen identity\n\t}\n}\n"
    )
    path = os.path.join(scripts_dir, "vehicles.shader")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)
    print(f"Updated {path} (7 vehicles)")


def _single_part_md3(part, shader):
    return [dict(
        name=part["name"][:16],
        shader=shader,
        tris=[tuple(t) for t in part["tris"]],
        st=[tuple(u) for u in part["uvs"]],
        frames=[([tuple(v) for v in part["verts"]], [tuple(n) for n in part["norms"]])],
    )]


def _spinning_wheel_md3(wheel_part, shader, nframes=16):
    v0, n0 = wheel_part["verts"], wheel_part["norms"]
    frames = []
    for fi in range(nframes):
        th = 2.0 * math.pi * fi / nframes
        c, s = math.cos(th), math.sin(th)
        vv = [(x * c + z * s, y, -x * s + z * c) for (x, y, z) in v0]
        nn = [(nx * c + nz * s, ny, -nx * s + nz * c) for (nx, ny, nz) in n0]
        frames.append((vv, nn))
    return [dict(name="wheel", shader=shader, tris=[tuple(t) for t in wheel_part["tris"]], st=[tuple(u) for u in wheel_part["uvs"]], frames=frames)]


def main():
    progs_dir = os.path.join(MOD_DIR, "progs")
    scripts_dir = os.path.join(MOD_DIR, "scripts")
    preview_dir = os.path.join(HERE, "out", "vehicles")

    all_veh = ensure_wild_blender_parts(force=False)
    print("Generating 1024x1024 studio & burn atlases + glow maps...")
    atlases = wvs.save_wild_darkplaces_textures(progs_dir, preview_dir, dp_gain=0.60)
    update_vehicles_shader(scripts_dir)

    cache_dict = {}
    for kind in WILD_KINDS:
        print(f"Simulating 960 Hz WILD airborne-flip & multi-roll explosion for {kind}...")
        vdata = all_veh[kind]
        sim = simulate_wild_explosion(vdata, kind, intensity=1.0, fps=60, duration=7.5, substeps=16)

        glb_path = os.path.join(MOD_DIR, f"veh_{kind}.glb")
        export_wild_vehicle_glb(vdata, kind, sim, atlases[kind]["intact"], glb_path)
        print(f"  -> Wrote {glb_path} ({os.path.getsize(glb_path) / 1e6:.2f} MB)")

        cache_dict[f"{kind}_fps"] = np.array([sim["fps"]], dtype=np.int32)
        cache_dict[f"{kind}_n_frames"] = np.array([sim["n_frames"]], dtype=np.int32)
        cache_dict[f"{kind}_boom_frame"] = np.array([sim["boom_frame"]], dtype=np.int32)
        cache_dict[f"{kind}_sec_boom_frame"] = np.array([sim["sec_boom_frame"]], dtype=np.int32)
        cache_dict[f"{kind}_sparks"] = np.array([json.dumps(sim["sparks"])])
        for pnm, tr in sim["tracks"].items():
            cache_dict[f"{kind}_pos_{pnm}"] = tr["pos"]
            cache_dict[f"{kind}_rot_{pnm}"] = tr["rot"]
            cache_dict[f"{kind}_scl_{pnm}"] = tr["scl"]

        sh_intact = f"progs/veh_{kind}_tex"
        sh_burn = f"progs/veh_{kind}_burn"

        intact_surfs = build_wild_intact_md3_surfaces(vdata, kind, sh_intact)
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}.md3"), dict(name=f"veh_{kind}", surfaces=intact_surfs))

        surf_names = [s["name"] for s in intact_surfs]
        with open(os.path.join(progs_dir, f"veh_{kind}.md3_0.skin"), "w", encoding="ascii", newline="\n") as sf:
            sf.write("".join(f"{s},{sh_intact}\n" for s in surf_names))
        with open(os.path.join(progs_dir, f"veh_{kind}.md3_1.skin"), "w", encoding="ascii", newline="\n") as sf:
            sf.write("".join(f"{s},{sh_burn}\n" for s in surf_names))

        wreck_surfs = build_wild_wreck_md3_surfaces(vdata, sim, sh_burn)
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_wreck.md3"), dict(name=f"veh_{kind}_wreck", surfaces=wreck_surfs))
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_wheel.md3"), dict(name=f"veh_{kind}_wheel", surfaces=_spinning_wheel_md3(vdata["parts"]["wheel_fl"], sh_intact)))
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_hood.md3"), dict(name=f"veh_{kind}_hood", surfaces=_single_part_md3(vdata["parts"]["hood"], sh_burn)))
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_door.md3"), dict(name=f"veh_{kind}_door", surfaces=_single_part_md3(vdata["parts"]["door_l"], sh_intact)))
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_extra.md3"), dict(name=f"veh_{kind}_extra", surfaces=_single_part_md3(vdata["parts"]["extra_part"], sh_intact)))
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_bumper.md3"), dict(name=f"veh_{kind}_bumper", surfaces=_single_part_md3(vdata["parts"]["bumper_f"], sh_intact)))

    np.savez_compressed(SIM_CACHE_NPZ, **cache_dict)
    print(f"Saved wild simulation cache: {SIM_CACHE_NPZ}")


if __name__ == "__main__":
    main()
