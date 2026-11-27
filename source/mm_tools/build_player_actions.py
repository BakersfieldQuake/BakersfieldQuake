"""Build 3 new smooth classic Quake Ranger (`progs/player_id1.mdl`) action animations
and 100% self-contained WebGL2 HTML 3D studio (`docs/player_actions_vote.html`):

1. `flip_land` : Smooth standing backflip that rotates 360 deg in midair and lands cleanly on both feet.
2. `superman`  : Iconic horizontal Superman flying pose (launch, soar, cruise, touchdown).
3. `balloon`   : Inflates smoothly to 3x size like a giant round balloon, hovers, then deflates.

Each category ships 3 candidate variations (`a`, `b`, `c`) in the HTML studio, and
the selected winners are compiled into `progs/player_id1.mdl` via `build_player_deaths.py`.

Usage:
    python -I source/mm_tools/build_player_actions.py
    python -I source/mm_tools/build_player_actions.py --render-check
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_player_deaths as bpd
import gokart_driver as gd

REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TEMPLATE_HTML = os.path.join(HERE, "player_actions_vote.template.html")
OUT_HTML = os.path.join(REPO_ROOT, "docs", "player_actions_vote.html")
OUT_PNG_CHECK = os.path.join(HERE, "out", "player_actions_check.png")

DEFAULT_ACTION_PICKS = {
    "flip_land": "flip_land_a",
    "superman": "superman_a",
    "balloon": "balloon_a",
}


def _clamp01(t):
    return max(0.0, min(1.0, t))


def _ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


def _ease_in_out(t):
    return bpd._smootherstep(t)


def _belly_puff_verts(verts, rig, scale_mult, torso_puff, limb_puff, head_puff, float_z=0.0, yaw_deg=0.0, roll_deg=0.0):
    """Volumetrically puff torso into a seamless round balloon, plump limbs/head, and scale ~3x from ground."""
    out = [list(v) for v in verts]
    belly_c = (0.0, 0.0, 4.5)
    head_c = gd._avg([verts[vi] for vi in rig.parts["head"]])

    # Compute continuous spherical/ellipsoidal balloon expansion offset field so sockets stay welded seamlessly
    def torso_delta(pt):
        dx, dy, dz = pt[0] - belly_c[0], pt[1] - belly_c[1], pt[2] - belly_c[2]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist < 1e-4:
            return (0.0, 0.0, 0.0)
        nx, ny, nz = dx / dist, dy / dist, dz / dist
        r_target = 15.2
        tx = belly_c[0] + nx * r_target * 1.08
        ty = belly_c[1] + ny * r_target * 1.12
        tz = belly_c[2] + nz * r_target * 1.02
        return (
            (tx - pt[0]) * torso_puff,
            (ty - pt[1]) * torso_puff,
            (tz - pt[2]) * torso_puff,
        )

    if torso_puff > 1e-4:
        for vi in rig.parts["torso"]:
            x, y, z = verts[vi]
            dx, dy, dz = torso_delta((x, y, z))
            out[vi] = [x + dx, y + dy, z + dz]

        # Head follows swollen collar outward cleanly and puffs helmet/cheeks
        collar_avg = gd._avg([torso_delta(verts[vi]) for vi in rig.borders["head"]])
        hx, hy, hz = head_c[0] + collar_avg[0], head_c[1] + collar_avg[1], head_c[2] + collar_avg[2] + torso_puff * 3.2
        for vi in rig.parts["head"]:
            vx, vy, vz = verts[vi]
            vx += collar_avg[0]
            vy += collar_avg[1]
            vz += collar_avg[2] + torso_puff * 3.2
            if head_puff > 1e-4 and vi not in rig.borders["head"]:
                out[vi] = [
                    hx + (vx - hx) * (1.0 + 0.42 * head_puff),
                    hy + (vy - hy) * (1.0 + 0.42 * head_puff),
                    hz + (vz - hz) * (1.0 + 0.36 * head_puff),
                ]
            else:
                out[vi] = [vx, vy, vz]

        # Arms & legs carry their socket's exact torso expansion outward (zero seam tear!) + local plumpness
        for side_key, sy in (("l_arm", +1.0), ("r_arm", -1.0)):
            sock_delta = gd._avg([torso_delta(verts[vi]) for vi in rig.borders[side_key]])
            pc = gd._avg([verts[vi] for vi in rig.parts[side_key]])
            cx, cy, cz = pc[0] + sock_delta[0], pc[1] + sock_delta[1], pc[2] + sock_delta[2]
            for vi in rig.parts[side_key]:
                vx, vy, vz = verts[vi]
                if vi in rig.borders[side_key]:
                    dx, dy, dz = torso_delta((vx, vy, vz))
                    out[vi] = [vx + dx, vy + dy, vz + dz]
                else:
                    vx += sock_delta[0] + 0.0
                    vy += sock_delta[1] + sy * torso_puff * 1.4
                    vz += sock_delta[2]
                    out[vi] = [
                        cx + (vx - cx) * (1.0 + 0.42 * limb_puff),
                        cy + (vy - cy) * (1.0 + 0.25 * limb_puff),
                        cz + (vz - cz) * (1.0 + 0.42 * limb_puff),
                    ]

        for side_key, sy in (("l_leg", +1.0), ("r_leg", -1.0)):
            sock_delta = gd._avg([torso_delta(verts[vi]) for vi in rig.borders[side_key]])
            pc = gd._avg([verts[vi] for vi in rig.parts[side_key]])
            cx, cy, cz = pc[0] + sock_delta[0], pc[1] + sock_delta[1], pc[2] + sock_delta[2]
            for vi in rig.parts[side_key]:
                vx, vy, vz = verts[vi]
                if vi in rig.borders[side_key]:
                    dx, dy, dz = torso_delta((vx, vy, vz))
                    out[vi] = [vx + dx, vy + dy, vz + dz]
                else:
                    vx += sock_delta[0]
                    vy += sock_delta[1] + sy * torso_puff * 1.0
                    vz += sock_delta[2]
                    out[vi] = [
                        cx + (vx - cx) * (1.0 + 0.36 * limb_puff),
                        cy + (vy - cy) * (1.0 + 0.36 * limb_puff),
                        cz + (vz - cz) * (1.0 + 0.18 * limb_puff),
                    ]

    # 2. Ground-anchored 1.0 -> 3.0x balloon inflation scale + buoyant hover + comical wobble
    min_z = min(out[vi][2] for vi in rig.body)
    pivot_z = min_z
    body_c = (0.0, 0.0, pivot_z + 18.0 * scale_mult)

    final_verts = []
    for vi in range(212):
        if vi in rig.body_set:
            x, y, z = out[vi]
            sx = x * scale_mult
            sy = y * scale_mult
            sz = pivot_z + (z - pivot_z) * scale_mult
            if abs(yaw_deg) > 1e-3 or abs(roll_deg) > 1e-3:
                q = bpd._rot_zyx((sx - body_c[0], sy - body_c[1], sz - body_c[2]), yaw_deg, 0.0, roll_deg)
                sx, sy, sz = q[0] + body_c[0], q[1] + body_c[1], q[2] + body_c[2]
            final_verts.append((sx, sy, sz + float_z))
        else:
            bx, by, bz = gd._avg([out[i] for i in rig.parts["torso"]])
            cx = bx * scale_mult
            cy = by * scale_mult
            cz = pivot_z + (bz - pivot_z) * scale_mult + float_z
            if scale_mult > 1.08 or torso_puff > 0.05:
                final_verts.append((cx, cy, cz))
            else:
                wx, wy, wz = verts[vi]
                final_verts.append((wx, wy, wz + float_z))

    min_final_z = min(final_verts[vi][2] for vi in rig.body)
    floor_lim = -24.5 + max(0.0, float_z * 0.15)
    if min_final_z < floor_lim:
        dz = floor_lim - min_final_z
        final_verts = [(x, y, z + dz) for x, y, z in final_verts]

    return final_verts


# ---------------------------------------------------------------------------
# Animation 1: Backflip & Lands on His Feet (3 Variations)
# ---------------------------------------------------------------------------

def _gen_flip_land(rig, variant):
    """Smooth standing backflip that rotates cleanly 360 deg in air and lands squarely on both feet."""
    if variant == "a":
        n = 30
        title = "Var A · Standing Tuck Backflip"
        desc = "Crisp deep crouch anticipation, explosive upward whip into a tight 360 mid-air tuck, opening smoothly to absorb landing squarely on both feet."
        arc_z = 46.0
        back_dist = 22.0
        tuck_knee = 116.0
        tuck_hip = 86.0
    elif variant == "b":
        n = 32
        title = "Var B · Open Layout Whip Backflip"
        desc = "Tall gymnastics layout backflip arching backward across the sky with arms flung wide before sticking a balanced two-foot landing."
        arc_z = 54.0
        back_dist = 30.0
        tuck_knee = 28.0
        tuck_hip = 12.0
    else:
        n = 28
        title = "Var C · Snap Ninja Backflip & Low Squat"
        desc = "Fast explosive snap tuck flipping high backward, touching down into a wide cushioned martial-arts squat before rising cleanly to stand."
        arc_z = 50.0
        back_dist = 26.0
        tuck_knee = 124.0
        tuck_hip = 94.0

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.10) + max(0.0, (t - 0.90) / 0.10)
        blend_stand = min(1.0, blend_stand)

        # Phases: 0..0.20 crouch -> 0.20..0.32 launch -> 0.32..0.72 flip -> 0.72..0.82 open/land -> 0.82..1.0 recover
        crouch_u = math.sin(_clamp01(t / 0.24) * math.pi) if t < 0.24 else 0.0
        takeoff_u = bpd._smoothstep((t - 0.18) / 0.12)
        air_u = _clamp01((t - 0.20) / 0.56)
        land_u = _clamp01((t - 0.76) / 0.24)

        # Full backward rotation: 0 -> -360 deg (negative _rot_y tilts head backward toward -X!)
        flip_u = _ease_in_out(_clamp01((t - 0.22) / 0.52))
        body_pitch = -360.0 * flip_u

        # Tuck envelope peaks right through mid-flip (0.34..0.64)
        tuck_env = math.sin(_clamp01((t - 0.28) / 0.44) * math.pi) if 0.28 <= t <= 0.72 else 0.0
        tuck_env = tuck_env ** 0.75

        # Landing absorption dip right at touchdown (0.76..0.94)
        absorb_env = math.sin(_clamp01((t - 0.74) / 0.22) * math.pi) if 0.74 <= t <= 0.96 else 0.0

        # Spine & pelvis
        if variant == "b" and 0.24 <= t <= 0.72:
            # Open layout back-arch
            sp_p = -20.0 * tuck_env + 22.0 * crouch_u + 18.0 * absorb_env
            pelv_p = -14.0 * tuck_env + 18.0 * crouch_u + 14.0 * absorb_env
            hp = -26.0 * tuck_env
        else:
            sp_p = 24.0 * crouch_u + 22.0 * tuck_env + 20.0 * absorb_env
            pelv_p = 18.0 * crouch_u + 16.0 * tuck_env + 14.0 * absorb_env
            hp = 12.0 * crouch_u - 22.0 * tuck_env + 8.0 * absorb_env

        # Arms: swing back on crouch -> whip overhead at takeoff -> hug shins/flare wide -> stabilize landing
        if t < 0.20:
            arm_p = bpd._lerp(8.0, -72.0, bpd._smoothstep(t / 0.18))
            arm_abd = bpd._lerp(14.0, 24.0, t / 0.20)
            el = bpd._lerp(22.0, 18.0, t / 0.20)
        elif t < 0.34:
            u = bpd._smoothstep((t - 0.20) / 0.14)
            arm_p = bpd._lerp(-72.0, 152.0, u)
            arm_abd = bpd._lerp(24.0, 26.0, u)
            el = bpd._lerp(18.0, 28.0, u)
        elif t < 0.72:
            if variant == "b":
                arm_p = 120.0 - 40.0 * tuck_env
                arm_abd = 26.0 + 48.0 * tuck_env
                el = 22.0
            else:
                arm_p = bpd._lerp(152.0, 88.0, tuck_env)
                arm_abd = bpd._lerp(26.0, 18.0, tuck_env)
                el = bpd._lerp(28.0, 96.0, tuck_env)
        elif t < 0.84:
            u = bpd._smoothstep((t - 0.72) / 0.12)
            arm_p = bpd._lerp(88.0 if variant != "b" else 100.0, 38.0, u)
            arm_abd = bpd._lerp(36.0, 52.0, math.sin(u * math.pi))
            el = bpd._lerp(50.0, 28.0, u)
        else:
            u = bpd._smoothstep((t - 0.84) / 0.16)
            arm_p = bpd._lerp(38.0, 8.0, u)
            arm_abd = bpd._lerp(24.0, 14.0, u)
            el = bpd._lerp(28.0, 22.0, u)

        # Legs: crouch bend -> extend -> tuck/layout -> extend smoothly -> cushioned landing on both feet
        if variant == "c":
            knee = 12.0 + 72.0 * crouch_u + tuck_knee * tuck_env + 76.0 * absorb_env
            ll_p = 6.0 + 26.0 * crouch_u + tuck_hip * tuck_env + 28.0 * absorb_env
            rl_p = -6.0 + 20.0 * crouch_u + tuck_hip * tuck_env - 20.0 * absorb_env
            leg_abd = 6.0 + 18.0 * absorb_env
        else:
            knee = 12.0 + 68.0 * crouch_u + tuck_knee * tuck_env + 62.0 * absorb_env
            ll_p = 6.0 + 24.0 * crouch_u + tuck_hip * tuck_env + 18.0 * absorb_env
            rl_p = -6.0 + 20.0 * crouch_u + tuck_hip * tuck_env + 12.0 * absorb_env
            leg_abd = 6.0 + 8.0 * absorb_env

        # Slight CoM lift inside model during inverted flip so head never brushes floor when Traj is off
        inv_lift = 10.0 * math.sin(air_u * math.pi) if (0.20 <= t <= 0.76) else 0.0
        on_ground = (t <= 0.21) or (t >= 0.75)

        p = bpd._base_pose(
            spine_pitch=sp_p,
            pelvis_pitch=pelv_p,
            head_pitch=hp,
            la_pitch=arm_p, la_abd=arm_abd, la_elbow=el,
            ra_pitch=arm_p, ra_abd=arm_abd, ra_elbow=el,
            ll_pitch=ll_p, ll_abd=leg_abd, ll_knee=knee, ll_ankle=16.0 * tuck_env,
            rl_pitch=rl_p, rl_abd=leg_abd, rl_knee=knee, rl_ankle=16.0 * tuck_env,
            body_pitch=body_pitch,
            body_z=inv_lift,
            floor_clamp=1.0 if on_ground else 0.0,
            weapon_scale=1.0 if (t < 0.08 or t > 0.92) else 0.0,
            blend_stand=blend_stand,
        )
        frames.append(rig.pose(p))

        # World trajectory: smooth backward hop + crisp parabolic arc -> exact landing z = 0
        arc = math.sin(air_u * math.pi) if (0.20 <= t <= 0.76) else 0.0
        wx = -back_dist * _ease_in_out(_clamp01((t - 0.18) / 0.60))
        wz = arc_z * arc
        traj.append({"x": round(wx, 2), "y": 0.0, "z": round(wz, 2)})

    return {
        "id": f"flip_land_{variant}",
        "cat": "flip_land",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": [],
        "cam": {"yaw": -74.0, "pitch": 14.0, "dist": 132.0, "focus_z": 18.0},
        "qc": {"up": 265.0, "back": 35.0},
    }


# ---------------------------------------------------------------------------
# Animation 2: Flying Like Superman (3 Variations)
# ---------------------------------------------------------------------------

def _gen_superman(rig, variant):
    """Iconic belly-down horizontal Superman flight: fist forward, chin up, pointed aero toes."""
    if variant == "a":
        n = 38
        title = "Var A · Classic One-Fist Soar & Landing"
        desc = "Crouches, launches into iconic Superman pose (right fist punched straight forward, left fist at hip, chest proud, head up), surges through the sky, and flares cleanly back onto his feet."
        loop_seam = False
    elif variant == "b":
        n = 32
        title = "Var B · Continuous Twin-Fist Mach Loop"
        desc = "Seamless continuous horizontal Superman flight loop with both fists thrust ahead, aerodynamic side-to-side banking, and sleek hover surge."
        loop_seam = True
    else:
        n = 40
        title = "Var C · Skyrocket 360 Barrel-Roll & Land"
        desc = "Launches skyward into a one-fist Superman cruise, snaps a crisp 360 mid-flight barrel roll, then sweeps down into a clean upright landing."
        loop_seam = False

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)

        if variant == "b":
            # Pure seamless loop in horizontal Superman cruise
            phase = t * 2.0 * math.pi
            bank = 24.0 * math.sin(phase)
            surge_p = 4.0 * math.cos(phase)
            bob_z = 8.0 * math.sin(phase)
            lat_y = 14.0 * math.sin(phase)

            p = bpd._base_pose(
                spine_pitch=-14.0 + 3.0 * math.sin(phase * 2.0),
                pelvis_pitch=-6.0,
                head_pitch=-70.0 + 4.0 * math.sin(phase),
                head_yaw=10.0 * math.sin(phase),
                la_pitch=168.0, la_abd=8.0, la_elbow=8.0,
                ra_pitch=170.0, ra_abd=8.0, ra_elbow=6.0,
                ll_pitch=-6.0 + 3.0 * math.sin(phase), ll_abd=4.0, ll_knee=7.0, ll_ankle=28.0,
                rl_pitch=-4.0 - 3.0 * math.sin(phase), rl_abd=4.0, rl_knee=9.0, rl_ankle=28.0,
                body_pitch=85.0 + surge_p,
                body_roll=bank,
                body_z=18.0 + bob_z,
                weapon_scale=0.0,
            )
            frames.append(rig.pose(p))
            traj.append({"x": 0.0, "y": round(lat_y, 2), "z": round(10.0 + 6.0 * math.cos(phase), 2)})
            continue

        # Launch (0..0.18) -> Superman Soar (0.18..0.82) -> Superhero Touchdown (0.82..1.00)
        blend_stand = max(0.0, 1.0 - t / 0.09) + max(0.0, (t - 0.91) / 0.09)
        blend_stand = min(1.0, blend_stand)

        crouch_u = math.sin(_clamp01(t / 0.14) * math.pi) if t < 0.14 else 0.0
        fly_env = bpd._smoothstep((t - 0.10) / 0.15) * (1.0 - bpd._smoothstep((t - 0.78) / 0.14))
        fly_u = _clamp01((t - 0.18) / 0.62)
        climb_tilt = -16.0 * math.cos(fly_u * math.pi) * fly_env

        body_pitch = 84.0 * fly_env + climb_tilt + 18.0 * crouch_u * (1.0 - fly_env)
        sp_p = 20.0 * crouch_u * (1.0 - fly_env) - 18.0 * fly_env
        pelv_p = 14.0 * crouch_u * (1.0 - fly_env) - 7.0 * fly_env
        hp = -64.0 * fly_env + 10.0 * crouch_u * (1.0 - fly_env)

        # Right fist punches straight forward overhead in flight; Left arm stays taut near hip
        ra_p = bpd._lerp(10.0 - 45.0 * crouch_u, 170.0, fly_env)
        ra_abd = bpd._lerp(14.0, 7.0, fly_env)
        ra_el = bpd._lerp(24.0, 6.0, fly_env)

        la_p = bpd._lerp(10.0 - 45.0 * crouch_u, -10.0, fly_env)
        la_abd = bpd._lerp(14.0, 15.0, fly_env)
        la_el = bpd._lerp(24.0, 24.0, fly_env)

        # Legs extend sleek & straight back in air
        land_dip = math.sin(_clamp01((t - 0.85) / 0.14) * math.pi) if 0.85 <= t <= 0.99 else 0.0
        knee = 12.0 + 54.0 * crouch_u * (1.0 - fly_env) + 46.0 * land_dip
        knee = bpd._lerp(knee, 7.0, fly_env)
        ankle = 28.0 * fly_env
        ll_p = bpd._lerp(6.0, -5.0 + 3.0 * math.sin(fly_u * 8.0), fly_env)
        rl_p = bpd._lerp(-6.0, -3.0 - 3.0 * math.sin(fly_u * 8.0), fly_env)

        if variant == "c":
            roll_u = _ease_in_out(_clamp01((t - 0.36) / 0.34))
            roll = 360.0 * roll_u
            fly_height = 46.0 * math.sin(_clamp01((t - 0.12) / 0.78) * math.pi)
            surge_x = 120.0 * math.sin(_clamp01((t - 0.12) / 0.78) * math.pi)
        else:
            roll = 18.0 * math.sin(fly_u * 2.0 * math.pi) * fly_env
            fly_height = 34.0 * fly_env + 4.0 * math.sin(fly_u * 2.0 * math.pi) * fly_env
            surge_x = 95.0 * math.sin(_clamp01((t - 0.12) / 0.78) * math.pi)

        on_ground = (t <= 0.11) or (t >= 0.89)
        p = bpd._base_pose(
            spine_pitch=sp_p,
            pelvis_pitch=pelv_p,
            head_pitch=hp,
            head_yaw=10.0 * math.sin(fly_u * 2.0 * math.pi) * fly_env,
            la_pitch=la_p, la_abd=la_abd, la_elbow=la_el,
            ra_pitch=ra_p, ra_abd=ra_abd, ra_elbow=ra_el,
            ll_pitch=ll_p, ll_abd=5.0, ll_knee=knee, ll_ankle=ankle,
            rl_pitch=rl_p, rl_abd=5.0, rl_knee=knee, rl_ankle=ankle,
            body_pitch=body_pitch,
            body_roll=roll,
            body_z=16.0 * fly_env,
            floor_clamp=1.0 if on_ground else 0.0,
            weapon_scale=1.0 if (t < 0.08 or t > 0.92) else 0.0,
            blend_stand=blend_stand,
        )
        frames.append(rig.pose(p))
        traj.append({"x": round(surge_x, 2), "y": 0.0, "z": round(fly_height, 2)})

    return {
        "id": f"superman_{variant}",
        "cat": "superman",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": [],
        "pause_end": 0.0 if loop_seam else 0.65,
        "cam": {"yaw": -72.0, "pitch": 15.0, "dist": 136.0, "focus_z": 22.0},
        "qc": {"fwd": 420.0, "up": 180.0},
    }


# ---------------------------------------------------------------------------
# Animation 3: Inflates 3x Size Like a Big Balloon, Then Deflates (3 Variations)
# ---------------------------------------------------------------------------

def _gen_balloon(rig, variant):
    """Inflates radially & volumetrically to 3x size like a giant balloon, hovers, then deflates."""
    if variant == "a":
        n = 38
        title = "Var A · Parade Balloon Swell & Flutter Deflate"
        desc = "Smoothly puffs his chest, cheeks, and limbs outward into a giant 3x round parade balloon hovering above the floor, wobbles tautly, then flutters as air blasts out back to 1x."
    elif variant == "b":
        n = 42
        title = "Var B · Three-Pump Cartoon Mega Bloat"
        desc = "Three punchy cartoon air pumps (1.6x -> 2.3x -> 3.05x) with bouncy rubber overshoot, tight peak creak, then a squeaky spinning deflate back onto his boots."
    else:
        n = 38
        title = "Var C · Helium 3x Rise & Squeeze Drop"
        desc = "Inflates 3x enormous and lifts buoyantly upward swaying like a parade float before deflating rapidly and dropping lightly back to his feet."

    frames = []
    traj = []
    for i in range(n):
        t = i / float(n - 1)
        blend_stand = max(0.0, 1.0 - t / 0.08) + max(0.0, (t - 0.93) / 0.07)
        blend_stand = min(1.0, blend_stand)

        yaw_wobble = 0.0
        roll_wobble = 0.0
        float_z = 0.0

        if variant == "a":
            # 0..0.08 breath -> 0.08..0.46 smooth swell to 2.72x (~155u = 3.0x height!) -> 0.46..0.66 peak bob -> 0.66..0.92 flutter deflate
            if t < 0.08:
                u = _ease_in_out(t / 0.08)
                sc = 1.0 + 0.08 * u
                puff = 0.15 * u
            elif t < 0.46:
                u = bpd._smootherstep((t - 0.08) / 0.38)
                sc = 1.08 + 1.64 * u + 0.08 * math.sin(u * math.pi) * (u ** 2)
                puff = 0.15 + 0.70 * u
            elif t < 0.66:
                u = (t - 0.46) / 0.20
                sc = 2.72 + 0.06 * math.sin(u * math.pi * 4.0)
                puff = 0.85
                float_z = 8.0 * math.sin(u * math.pi)
                roll_wobble = 5.0 * math.sin(u * math.pi * 3.0)
            elif t < 0.92:
                u = (t - 0.66) / 0.26
                s = bpd._smootherstep(u)
                undershoot = -0.10 * math.sin(u * math.pi) * (u ** 1.5)
                sc = max(0.90, bpd._lerp(2.72, 1.00, s) + undershoot)
                puff = 0.85 * (1.0 - s)
                flutter = math.sin(u * math.pi)
                yaw_wobble = 22.0 * math.sin(u * 26.0) * flutter
                roll_wobble = 14.0 * math.cos(u * 22.0) * flutter
            else:
                u = bpd._smoothstep((t - 0.92) / 0.08)
                sc = bpd._lerp(0.96, 1.0, u)
                puff = 0.0

        elif variant == "b":
            # 3 punchy pumps peaking cleanly around 2.75x (~156u tall, ~3x height)
            if t < 0.16:
                u = bpd._smootherstep(t / 0.16)
                sc = 1.0 + 0.52 * u
                puff = 0.38 * u
            elif t < 0.32:
                u = bpd._smootherstep((t - 0.16) / 0.16)
                sc = 1.52 + 0.60 * u
                puff = 0.38 + 0.25 * u
            elif t < 0.48:
                u = bpd._smootherstep((t - 0.32) / 0.16)
                sc = 2.12 + 0.63 * u
                puff = 0.63 + 0.22 * u
            elif t < 0.64:
                u = (t - 0.48) / 0.16
                sc = 2.75 - 0.05 * math.sin(u * math.pi * 3.0)
                puff = 0.85
                float_z = 7.0 * math.sin(u * math.pi)
            elif t < 0.93:
                u = (t - 0.64) / 0.29
                s = _ease_in_out(u)
                sc = max(0.90, bpd._lerp(2.75, 1.0, s))
                puff = 0.85 * (1.0 - s)
                flutter = math.sin(u * math.pi)
                yaw_wobble = 30.0 * math.sin(u * 28.0) * flutter
                roll_wobble = 11.0 * math.sin(u * 19.0) * flutter
            else:
                sc = 1.0
                puff = 0.0

        else:
            # Helium balloon float (+20u rise) then drop back onto feet (~156u height at 3x)
            if t < 0.42:
                u = bpd._smootherstep(t / 0.42)
                sc = 1.0 + 1.72 * u
                puff = 0.85 * u
                float_z = 20.0 * bpd._smoothstep(max(0.0, (t - 0.20) / 0.22))
            elif t < 0.66:
                u = (t - 0.42) / 0.24
                sc = 2.72 + 0.05 * math.sin(u * math.pi * 3.0)
                puff = 0.85
                float_z = 20.0 + 5.0 * math.sin(u * math.pi * 2.0)
                roll_wobble = 9.0 * math.sin(u * math.pi * 2.0)
                yaw_wobble = 10.0 * math.cos(u * math.pi * 2.0)
            elif t < 0.90:
                u = (t - 0.66) / 0.24
                s = _ease_in_out(u)
                sc = max(0.92, bpd._lerp(2.72, 1.0, s))
                puff = 0.85 * (1.0 - s)
                float_z = 20.0 * max(0.0, 1.0 - (u ** 1.4) * 1.15)
                flutter = math.sin(u * math.pi)
                roll_wobble = 15.0 * math.sin(u * 24.0) * flutter
            else:
                u = (t - 0.90) / 0.10
                sc = 1.0
                puff = 0.0
                float_z = 0.0

        # Pose arms/legs out proportionally as balloon inflates (compactly tucked out so maxW ~ 95-115u)
        arm_spread = bpd._lerp(16.0, 48.0, min(1.0, puff * 1.15))
        arm_pitch = bpd._lerp(8.0, 18.0, min(1.0, puff * 1.15))
        leg_spread = bpd._lerp(6.0, 18.0, min(1.0, puff * 1.15))
        knee_bend = bpd._lerp(12.0, 4.0, min(1.0, puff * 1.15))

        p = bpd._base_pose(
            spine_pitch=-10.0 * min(1.0, puff * 1.2),
            pelvis_pitch=-4.0 * min(1.0, puff * 1.2),
            head_pitch=-12.0 * min(1.0, puff * 1.2),
            la_pitch=arm_pitch, la_abd=arm_spread, la_elbow=bpd._lerp(22.0, 8.0, puff),
            ra_pitch=arm_pitch, ra_abd=arm_spread, ra_elbow=bpd._lerp(22.0, 8.0, puff),
            ll_pitch=bpd._lerp(6.0, 14.0, puff), ll_abd=leg_spread, ll_knee=knee_bend,
            rl_pitch=bpd._lerp(-6.0, 10.0, puff), rl_abd=leg_spread, rl_knee=knee_bend,
            weapon_scale=1.0 if (t < 0.05 or t > 0.94) else 0.0,
        )
        base_v = rig.pose(p)
        deformed = _belly_puff_verts(
            base_v,
            rig,
            scale_mult=sc,
            torso_puff=puff,
            limb_puff=puff * 0.95,
            head_puff=puff * 0.85,
            float_z=float_z,
            yaw_deg=yaw_wobble,
            roll_deg=roll_wobble,
        )
        if blend_stand > 1e-4:
            deformed = [bpd._vlerp(v, s1, blend_stand) for v, s1 in zip(deformed, rig.stand1)]
        frames.append(deformed)
        traj.append({"x": 0.0, "y": 0.0, "z": 0.0})

    return {
        "id": f"balloon_{variant}",
        "cat": "balloon",
        "title": title,
        "desc": desc,
        "fps": 20,
        "frames": frames,
        "traj": traj,
        "gibs": [],
        "cam": {"yaw": -118.0, "pitch": 15.0, "dist": 215.0, "focus_z": 42.0},
        "qc": {"float_z": 16.0},
    }


ACTION_CATEGORIES = [
    {
        "cat": "flip_land",
        "label": "1 · Backflip & Lands on Feet",
        "badge": "ACTION #1",
        "summary": "Smooth standing backflip: crouch anticipation, 360 backward aerial rotation, clean knee-absorbed landing on both feet.",
        "gen": _gen_flip_land,
    },
    {
        "cat": "superman",
        "label": "2 · Flying Like Superman",
        "badge": "ACTION #2",
        "summary": "Belly-down heroic Superman soar: fist punched straight ahead, head up, pointed aero toes, banking smoothly through the air.",
        "gen": _gen_superman,
    },
    {
        "cat": "balloon",
        "label": "3 · 3x Balloon Inflate & Deflate",
        "badge": "ACTION #3",
        "summary": "Puffs volumetrically to 3x size like a giant round balloon, bobs buoyantly, then deflates with a fluttering hiss back to 1x.",
        "gen": _gen_balloon,
    },
]


def generate_all_action_candidates(mdl_info, rig, quantize_with_box=None):
    """Generate 9 smooth action candidate animations (3 categories x 3 variations).

    If quantize_with_box=(scale, trans) is provided, clamp & roundtrip frames to exact MDL bytes.
    """
    all_anims = []
    for cat_info in ACTION_CATEGORIES:
        for var in ("a", "b", "c"):
            anim = cat_info["gen"](rig, var)
            anim["cat_label"] = cat_info["label"]
            anim["badge"] = cat_info["badge"]
            if quantize_with_box is not None:
                sc, tr = quantize_with_box
                clamped = [bpd._clamp_to_mdl_box(fr, sc, tr) for fr in anim["frames"]]
                anim["frames"] = bpd._quantize_roundtrip(clamped, sc, tr)
            all_anims.append(anim)
    return all_anims


def compute_unified_mdl_box(base_frames_verts, extra_anims):
    """Compute unified MDL (scale, trans) covering every vertex across all base + death + action frames."""
    all_pts = []
    for fr in base_frames_verts:
        all_pts.extend(fr)
    for anim in extra_anims:
        for fr in anim["frames"]:
            all_pts.extend(fr)
    arr = np.array(all_pts, dtype=np.float64)
    mn = arr.min(axis=0) - 0.5
    mx = arr.max(axis=0) + 0.5
    span = np.maximum(mx - mn, 1.0)
    scale = tuple(float(span[k] / 255.0) for k in range(3))
    trans = tuple(float(mn[k]) for k in range(3))
    return scale, trans


def _render_card_thumb_b64(mdl_info, anim):
    """Render a compact crisp 3-panel keyframe JPEG strip for static/no-JS HTML preview fallback."""
    import base64
    import io

    cw, ch = 150, 210
    cols = 3
    im = Image.new("RGB", (cw * cols, ch), (14, 19, 30))
    dr = ImageDraw.Draw(im)
    tris = mdl_info["tris"]
    nf = len(anim["frames"])
    idxs = [0, nf // 2, min(nf - 1, (3 * nf) // 4 if anim["cat"] == "balloon" else nf - 1)]
    if anim["cat"] == "balloon":
        idxs = [0, nf // 2, nf - 1]
    elif anim["cat"] == "flip_land":
        idxs = [0, nf // 2, min(nf - 1, int(round(0.84 * (nf - 1))))]

    cam = anim.get("cam", {})
    yr = math.radians(cam.get("yaw", -74.0))
    pr = math.radians(cam.get("pitch", 14.0))
    cyw, syw = math.cos(yr), math.sin(yr)
    cpt, spt = math.cos(pr), math.sin(pr)
    sc = 1.15 if anim["cat"] == "balloon" else 1.85
    oy = int(ch * 0.76) if anim["cat"] == "balloon" else int(ch * 0.64)

    for ci, fi in enumerate(idxs):
        ox = ci * cw + cw // 2
        verts = anim["frames"][fi]
        tx = anim["traj"][fi]["x"] * 0.35 if anim.get("traj") else 0.0
        tz = anim["traj"][fi]["z"] * 0.55 if anim.get("traj") else 0.0
        proj = []
        for x, y, z in verts:
            vx, vy, vz = x + tx, y, z + tz
            rx = vx * cyw - vy * syw
            ry = vx * syw + vy * cyw
            px = rx * cpt + vz * spt
            pz = -rx * spt + vz * cpt
            proj.append((ox + ry * sc, oy - pz * sc, px))
        draw_tris = []
        for _, v0, v1, v2 in tris:
            p0, p1, p2 = verts[v0], verts[v1], verts[v2]
            fn = bpd._vcross(bpd._vsub(p1, p0), bpd._vsub(p2, p0))
            if math.sqrt(fn[0] ** 2 + fn[1] ** 2 + fn[2] ** 2) < 1e-4:
                continue
            zavg = (proj[v0][2] + proj[v1][2] + proj[v2][2]) / 3.0
            shade = max(0.30, min(1.0, 0.56 + 0.44 * bpd._vnorm(fn)[2]))
            draw_tris.append((zavg, v0, v1, v2, shade))
        draw_tris.sort(key=lambda t: t[0])
        for _, v0, v1, v2, shade in draw_tris:
            col = (int(208 * shade), int(158 * shade), int(116 * shade))
            pts = [(proj[v0][0], proj[v0][1]), (proj[v1][0], proj[v1][1]), (proj[v2][0], proj[v2][1])]
            dr.polygon(pts, fill=col, outline=(28, 34, 48))
        dr.text((ci * cw + 6, ch - 16), f"f{fi}", fill=(160, 178, 205))

    bio = io.BytesIO()
    im.save(bio, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def build_actions_html(mdl_info, rig, all_anims, picks, out_html=OUT_HTML):
    if not os.path.isfile(TEMPLATE_HTML):
        raise FileNotFoundError(f"Missing HTML template: {TEMPLATE_HTML}")

    tri_idx, uv = bpd._pack_mesh_for_js(mdl_info["tris"], mdl_info["st"], mdl_info["sw"], mdl_info["sh"])
    anims_js = []
    for anim in all_anims:
        flat_frames = [[round(c, 3) for p in fr for c in p] for fr in anim["frames"]]
        anims_js.append({
            "id": anim["id"],
            "cat": anim["cat"],
            "cat_label": anim["cat_label"],
            "badge": anim["badge"],
            "title": anim["title"],
            "desc": anim["desc"],
            "fps": anim["fps"],
            "frames": flat_frames,
            "traj": anim["traj"],
            "thumb": _render_card_thumb_b64(mdl_info, anim),
            "pause_end": anim.get("pause_end", 0.65),
            "cam": anim.get("cam", {"yaw": -108.0, "pitch": 16.0, "dist": 135.0, "focus_z": 18.0}),
            "qc": anim["qc"],
        })

    sheet_b64 = ""
    sheet_path = os.path.join(REPO_ROOT, "docs", "player_actions_bakersfield_sheet.png")
    if os.path.isfile(sheet_path):
        import base64
        import io
        sim = Image.open(sheet_path).convert("RGB")
        sim.thumbnail((1120, 960), Image.Resampling.LANCZOS)
        sbio = io.BytesIO()
        sim.save(sbio, "JPEG", quality=84, optimize=True)
        sheet_b64 = "data:image/jpeg;base64," + base64.b64encode(sbio.getvalue()).decode("ascii")

    payload = {
        "categories": [
            {"cat": c["cat"], "label": c["label"], "badge": c["badge"], "summary": c["summary"]}
            for c in ACTION_CATEGORIES
        ],
        "default_picks": picks,
        "sheet_b64": sheet_b64,
        "player": {
            "nverts": 212,
            "tris": tri_idx,
            "uv": uv,
            "stand1": [round(c, 3) for p in rig.stand1 for c in p],
            "skin": "data:image/png;base64," + bpd._png_b64(mdl_info["skin_rgb"]),
        },
        "anims": anims_js,
    }

    payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    tpl = open(TEMPLATE_HTML, "r", encoding="utf-8").read()
    html = tpl.replace("__PAYLOAD_JSON__", payload_json)
    os.makedirs(os.path.dirname(os.path.abspath(out_html)), exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote actions studio HTML: {out_html} ({os.path.getsize(out_html)} bytes)")


def render_diagnostic_png(mdl_info, all_anims, picks, out_path=OUT_PNG_CHECK):
    tris = mdl_info["tris"]
    selected = [next(a for a in all_anims if a["id"] == picks[c["cat"]]) for c in ACTION_CATEGORIES]
    cw, ch = 360, 340
    cols, rows = 5, len(selected)
    im = Image.new("RGB", (cw * cols, ch * rows), (12, 16, 26))
    dr = ImageDraw.Draw(im)

    yr, pr = math.radians(-68.0), math.radians(14.0)
    cyw, syw = math.cos(yr), math.sin(yr)
    cpt, spt = math.cos(pr), math.sin(pr)

    for r_idx, anim in enumerate(selected):
        nf = len(anim["frames"])
        sample_idxs = [0, nf // 4, nf // 2, (3 * nf) // 4, nf - 1]
        sc = 1.45 if anim["cat"] == "balloon" else 2.65
        base_oy = r_idx * ch + int(ch * 0.72) if anim["cat"] == "balloon" else r_idx * ch + int(ch * 0.60)
        for c_idx, fi in enumerate(sample_idxs):
            ox = c_idx * cw + cw // 2
            oy = base_oy
            verts = anim["frames"][fi]
            tx = anim["traj"][fi]["x"] * 0.35
            tz = anim["traj"][fi]["z"] * 0.65
            proj = []
            for x, y, z in verts:
                vx, vy, vz = x + tx, y, z + tz
                rx = vx * cyw - vy * syw
                ry = vx * syw + vy * cyw
                px = rx * cpt + vz * spt
                pz = -rx * spt + vz * cpt
                proj.append((ox + ry * sc, oy - pz * sc, px))
            draw_tris = []
            for _, v0, v1, v2 in tris:
                p0, p1, p2 = verts[v0], verts[v1], verts[v2]
                fn = bpd._vcross(bpd._vsub(p1, p0), bpd._vsub(p2, p0))
                if math.sqrt(fn[0] ** 2 + fn[1] ** 2 + fn[2] ** 2) < 1e-4:
                    continue
                zavg = (proj[v0][2] + proj[v1][2] + proj[v2][2]) / 3.0
                shade = max(0.28, min(1.0, 0.55 + 0.45 * bpd._vnorm(fn)[2]))
                draw_tris.append((zavg, v0, v1, v2, shade))
            draw_tris.sort(key=lambda t: t[0])
            for _, v0, v1, v2, shade in draw_tris:
                col = (int(205 * shade), int(158 * shade), int(116 * shade))
                pts = [(proj[v0][0], proj[v0][1]), (proj[v1][0], proj[v1][1]), (proj[v2][0], proj[v2][1])]
                dr.polygon(pts, fill=col, outline=(28, 34, 48))
            dr.rectangle([c_idx * cw, r_idx * ch, (c_idx + 1) * cw - 1, (r_idx + 1) * ch - 1], outline=(40, 48, 68))
            dr.text((c_idx * cw + 8, r_idx * ch + 6), f"{anim['id']} f{fi}/{nf-1}", fill=(255, 196, 108))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path)
    print(f"Wrote diagnostic contact sheet: {out_path}")


def main():
    ap = argparse.ArgumentParser(description="Build 3 new classic Ranger action animations & interactive WebGL2 studio.")
    ap.add_argument("--bakersfield-pk3", type=str, default=bpd.BAKER_PK3)
    ap.add_argument("--picks", type=str, default="", help="Comma-separated winners (e.g. flip_land_a,superman_b,balloon_a)")
    ap.add_argument("--render-check", action="store_true", help="Render diagnostic PNG contact sheet")
    ap.add_argument("--out-html", type=str, default=OUT_HTML)
    args = ap.parse_args()

    picks = dict(DEFAULT_ACTION_PICKS)
    if args.picks:
        for item in args.picks.split(","):
            item = item.strip()
            for cat_info in ACTION_CATEGORIES:
                c = cat_info["cat"]
                if item.startswith(c + "_"):
                    picks[c] = item

    mdl_info = bpd.load_id1_full(bakersfield_pk3=args.bakersfield_pk3)
    rig = bpd.RangerRig(mdl_info, bakersfield_pk3=args.bakersfield_pk3)
    all_anims = generate_all_action_candidates(mdl_info, rig)

    if args.render_check:
        render_diagnostic_png(mdl_info, all_anims, picks)

    build_actions_html(mdl_info, rig, all_anims, picks, out_html=args.out_html)


if __name__ == "__main__":
    main()
