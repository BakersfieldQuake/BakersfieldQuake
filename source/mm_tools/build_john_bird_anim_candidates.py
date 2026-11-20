"""Build 12 candidate animation clips (192 frames) for Winged Breezy-Hair John.

Outputs under source/mm_tools/out/john_bird/vote_candidates/:
  - john_bird_candidates.md3       (192 frames: 3 categories x 4 variants x 16 frames)
  - candidates_manifest.json       (metadata for all 12 clips & 3 categories)
  - verify_fast_fly.png            (4x4 visual contact sheet for F1..F4)
  - verify_hit_flail.png           (4x4 visual contact sheet for H1..H4)
  - verify_skypad_hyper.png        (4x4 visual contact sheet for S1..S4)

Reuses the head, hair-lock topology, and 3-joint winged rig from
build_john_bird_head.py without modifying build_john_bird_head.py,
progs/john_bird_head.md3, progs.dat, or any .pk3 file.
"""
import json
import math
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_john_bird_head as JBH
import md3lib

OUT_VOTE_DIR = os.path.join(JBH.OUT_DIR, "vote_candidates")
BASE_Z = JBH.BASE_Z
FRAMES_PER_CLIP = 16


def _wing_side(
    hum_flap, hum_sweep, hum_pitch,
    elbow_flap, elbow_sweep, elbow_pitch,
    wrist_flap, wrist_sweep, wrist_pitch,
    aero_load, aero_twist,
    fold=0.0, alula_open=0.0,
    fx_phase=0.0, flutter_amp=0.0, splay_sweep=0.0, splay_dihedral=0.0,
    chord_stretch=1.0,
):
    return dict(
        hum_flap=hum_flap,
        hum_sweep=hum_sweep,
        hum_pitch=hum_pitch,
        elbow_flap=elbow_flap,
        elbow_sweep=elbow_sweep,
        elbow_pitch=elbow_pitch,
        wrist_flap=wrist_flap,
        wrist_sweep=wrist_sweep,
        wrist_pitch=wrist_pitch,
        aero_load=aero_load,
        aero_twist=aero_twist,
        fold=fold,
        alula_open=alula_open,
        fx_phase=fx_phase,
        flutter_amp=flutter_amp,
        splay_sweep=splay_sweep,
        splay_dihedral=splay_dihedral,
        chord_stretch=chord_stretch,
    )


def eval_candidate_wing(wing_builder, wing_pose, head_rot, head_pos):
    """Evaluate articulated 3-joint feathered wings with optional per-feather flutter/splay."""
    n_verts = len(wing_builder.uvs)
    V = np.zeros((n_verts, 3), dtype=np.float32)

    L_HUM = 13.5
    L_ULNA = 16.5
    L_HAND = 16.5

    for side in (1.0, -1.0):
        wp = wing_pose["L" if side > 0 else "R"]
        p0 = np.array([-3.2, side * 11.0, 2.6], dtype=np.float32)

        R0 = (
            JBH.rot_z(side * wp["hum_sweep"])
            @ JBH.rot_x(side * wp["hum_flap"])
            @ JBH.rot_y(-wp["hum_pitch"])
        )
        p1 = p0 + R0 @ np.array([0.0, side * L_HUM, 0.0], dtype=np.float32)

        R1 = (
            R0
            @ JBH.rot_z(side * wp["elbow_sweep"])
            @ JBH.rot_x(side * wp["elbow_flap"])
            @ JBH.rot_y(-wp["elbow_pitch"])
        )
        p2 = p1 + R1 @ np.array([0.0, side * L_ULNA, 0.0], dtype=np.float32)

        R2 = (
            R1
            @ JBH.rot_z(side * wp["wrist_sweep"])
            @ JBH.rot_x(side * wp["wrist_flap"])
            @ JBH.rot_y(-wp["wrist_pitch"])
        )
        p3 = p2 + R2 @ np.array([0.0, side * L_HAND, 0.0], dtype=np.float32)

        segs = [
            (p0, p1, R0, L_HUM),
            (p1, p2, R1, L_ULNA),
            (p2, p3, R2, L_HAND),
        ]

        arm = [a for a in wing_builder.arm_rings if a["side"] == side][0]
        arm_stations = [
            (0, 0.00, 2.35, 1.80),
            (0, 0.50, 2.05, 1.50),
            (0, 1.00, 1.80, 1.30),
            (1, 0.50, 1.55, 1.10),
            (1, 1.00, 1.35, 0.95),
            (2, 0.50, 1.05, 0.72),
            (2, 1.00, 0.58, 0.44),
        ]
        for si, (sg_i, st_t, rx_a, rz_a) in enumerate(arm_stations):
            sa, sb, sR, _ = segs[sg_i]
            cen = sa * (1.0 - st_t) + sb * st_t + sR @ np.array([0.55 * rx_a, 0.0, 0.10], dtype=np.float32)
            r0 = arm["base"] + si * (arm["n_ring"] + 1)
            for k in range(arm["n_ring"] + 1):
                ang = 2.0 * math.pi * (k / float(arm["n_ring"]))
                loc = np.array([rx_a * math.cos(ang), 0.0, rz_a * math.sin(ang)], dtype=np.float32)
                V[r0 + k] = cen + sR @ loc
        tip_idx = arm["base"] + arm["n_st"] * (arm["n_ring"] + 1)
        V[tip_idx] = p3 + R2 @ np.array([0.35, side * 0.85, 0.0], dtype=np.float32)

        aero_load = wp["aero_load"]
        aero_twist = wp["aero_twist"]
        fold_amt = wp.get("fold", 0.0)
        fx_phase = wp.get("fx_phase", 0.0)
        flutter_amp = wp.get("flutter_amp", 0.0)
        splay_sweep = wp.get("splay_sweep", 0.0)
        splay_dihedral = wp.get("splay_dihedral", 0.0)
        chord_stretch = wp.get("chord_stretch", 1.0)

        f_idx = 0
        for f in wing_builder.feathers:
            if f["side"] != side:
                continue
            f_idx += 1
            sa, sb, sR, _ = segs[f["seg"]]
            t_p = f["pos_t"]
            anchor = sa * (1.0 - t_p) + sb * t_p + sR @ np.array([f["x_off"], 0.0, f["z_off"]], dtype=np.float32)

            sw_jitter = splay_sweep * math.sin(f_idx * 2.17 + fx_phase)
            dh_jitter = splay_dihedral * math.cos(f_idx * 1.83 + fx_phase * 0.5)
            sw_rad = math.radians(f["sweep_deg"] - fold_amt * (24.0 if f["seg"] == 2 else 10.0) + sw_jitter)
            dh_rad = math.radians(
                f["dihedral_deg"]
                + (8.0 * wp.get("alula_open", 0.0) if f.get("alula") else 0.0)
                + dh_jitter
            )

            t_loc = np.array([
                math.sin(sw_rad) * math.cos(dh_rad),
                side * math.cos(sw_rad) * math.cos(dh_rad),
                math.sin(dh_rad),
            ], dtype=np.float32)
            t_loc /= max(1e-6, float(np.linalg.norm(t_loc)))

            up_loc = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            n_loc = up_loc - np.dot(up_loc, t_loc) * t_loc
            nl = float(np.linalg.norm(n_loc))
            n_loc = (n_loc / nl) if nl > 1e-5 else up_loc
            lead_loc = np.cross(n_loc, t_loc) * side
            lead_loc /= max(1e-6, float(np.linalg.norm(lead_loc)))

            T_w = sR @ t_loc
            N_w = sR @ n_loc
            L_w = sR @ lead_loc

            Lf = f["length"] * (1.0 + (chord_stretch - 1.0) * (0.45 + 0.55 * f["flex_gain"]))
            wl = f["w_lead"]
            wt = f["w_trail"]
            thk = f["thick"]
            cmb = f["camber"]
            fg = f["flex_gain"]
            tg = f["twist_gain"]
            emarg = f.get("emarginated", False)

            b_idx = f["base"]
            V[b_idx] = anchor

            N_FS = 5
            for si in range(N_FS + 1):
                s = (si + 1) / float(N_FS + 1)
                flut_bend = (
                    flutter_amp
                    * (0.35 + 0.95 * fg)
                    * (s ** 1.45)
                    * math.sin(fx_phase - 3.6 * s + f_idx * 1.41)
                )
                flut_lat = (
                    flutter_amp
                    * 0.42
                    * (0.35 + 0.95 * fg)
                    * (s ** 1.5)
                    * math.cos(fx_phase - 2.9 * s + f_idx * 1.93)
                )
                bend_up = (aero_load * fg * 3.8 * (s ** 1.95)) - cmb * 0.85 * (s ** 1.5) + flut_bend
                aft_curve = -cmb * 0.55 * (s ** 1.7) + flut_lat
                c_pt = anchor + T_w * (Lf * s) + N_w * bend_up + L_w * aft_curve

                if si == N_FS:
                    V[b_idx + 1 + N_FS * 4] = c_pt
                    break

                tw_ang = aero_twist * tg * s + 0.14 * flutter_amp * fg * s * math.sin(fx_phase + f_idx * 1.1)
                ct, st = math.cos(tw_ang), math.sin(tw_ang)
                n_s = ct * N_w + st * L_w
                l_s = -st * N_w + ct * L_w

                prof = math.sin(min(1.0, s * 1.18) * math.pi * 0.78) * (1.0 - 0.36 * (s ** 2.6))
                notch = (1.0 - 0.34 * JBH.smoothstep(0.52, 0.76, s)) if (emarg and s > 0.52) else 1.0

                w_l = wl * prof * notch
                w_t = wt * prof * notch
                h_s = thk * (1.0 - 0.62 * (s ** 1.6))

                vi = b_idx + 1 + si * 4
                V[vi + 0] = c_pt + n_s * h_s
                V[vi + 1] = c_pt + l_s * w_l - n_s * (0.18 * h_s)
                V[vi + 2] = c_pt - n_s * (0.32 * h_s)
                V[vi + 3] = c_pt - l_s * w_t - n_s * (0.42 * h_s)

    return (V @ head_rot.T) + head_pos[None, :]


def eval_candidate_hair(locks, wind_cfg, head_rot, head_pos):
    """Evaluate 64 3D hair locks with enhanced multi-harmonic waves, ruffle, and vortex modes."""
    N_MID = 6
    verts = []

    ph1 = wind_cfg["ph1"]           # 2*pi*u
    h1 = wind_cfg.get("h1", 2)
    h2 = wind_cfg.get("h2", 4)
    style = wind_cfg["style"]       # "fast_ripple", "fast_shampoo", "fast_swept", "fast_part", "hit_panic", "hit_corkscrew", "hit_poof", "hit_thrash", "sky_shred", "sky_vortex", "sky_afterburner", "sky_storm"

    breeze = wind_cfg.get("breeze", 1.5)
    flutter = wind_cfg.get("flutter", 1.8)
    gust_z = wind_cfg.get("gust_z", 0.0)
    bang_len_mul = wind_cfg.get("bang_len_mul", 1.8)
    bang_w_mul = wind_cfg.get("bang_w_mul", 1.4)
    crown_len_mul = wind_cfg.get("crown_len_mul", 1.6)
    crown_w_mul = wind_cfg.get("crown_w_mul", 1.35)
    side_len_mul = wind_cfg.get("side_len_mul", 1.5)
    side_w_mul = wind_cfg.get("side_w_mul", 1.25)
    back_len_mul = wind_cfg.get("back_len_mul", 1.5)
    back_w_mul = wind_cfg.get("back_w_mul", 1.25)

    for lk_idx, lk in enumerate(locks):
        root = lk["root"]
        n_out = lk["n_out"]
        dir0 = lk["dir0"]
        curve = lk["curve"]
        L = lk["length"]
        W = lk["width"]
        H_th = lk["thick"]
        ph = lk["phase"]
        amp = lk["wind_amp"]
        kind = lk["kind"]

        if kind == "bang":
            L_eff = L * bang_len_mul
            W_eff = W * bang_w_mul
            H_eff = H_th * (1.0 + 0.42 * (bang_w_mul - 1.0))
        elif kind == "crown":
            L_eff = L * crown_len_mul
            W_eff = W * crown_w_mul
            H_eff = H_th * (1.0 + 0.34 * (crown_w_mul - 1.0))
        elif kind == "side":
            L_eff = L * side_len_mul
            W_eff = W * side_w_mul
            H_eff = H_th * (1.0 + 0.25 * (side_w_mul - 1.0))
        else:
            L_eff = L * back_len_mul
            W_eff = W * back_w_mul
            H_eff = H_th * (1.0 + 0.25 * (back_w_mul - 1.0))

        dir_eff = dir0
        curve_eff = curve
        side_fan = root[1] / 10.0

        if style in ("fast_ripple", "fast_shampoo", "fast_part"):
            if kind == "bang":
                fan_gain = 0.68 if style == "fast_part" else 0.44
                dir_eff = JBH.make_tangent(
                    np.array([0.65, -0.58 + fan_gain * side_fan, -0.22], dtype=np.float32),
                    n_out,
                    lift=0.07,
                )
                curve_eff = np.array([0.22, -0.32 + fan_gain * side_fan, -0.26], dtype=np.float32)
        elif style == "fast_swept":
            if kind == "bang":
                # Sleek temple-swept falcon bangs: sweep smoothly around brow & temples without rising over crown
                dir_eff = JBH.make_tangent(
                    np.array([0.35, -0.55 + 0.50 * side_fan, -0.18], dtype=np.float32),
                    n_out,
                    lift=0.06,
                )
                curve_eff = np.array([-0.75, 0.28 * side_fan, -0.28], dtype=np.float32)
        elif style.startswith("hit_"):
            if kind == "bang":
                dir_eff = JBH.make_tangent(
                    np.array([0.52, -0.25 + 0.75 * side_fan, 0.55], dtype=np.float32),
                    n_out,
                    lift=0.22 if style == "hit_poof" else 0.16,
                )
                curve_eff = np.array([0.15, 0.65 * math.sin(ph), 0.55], dtype=np.float32)
            elif kind == "crown":
                dir_eff = JBH.make_tangent(
                    np.array([-0.45, 0.45 * math.cos(ph), 0.68], dtype=np.float32),
                    n_out,
                    lift=0.20,
                )
                curve_eff = np.array([-0.45, 0.55 * math.sin(ph * 1.3), 0.45], dtype=np.float32)
        elif style.startswith("sky_"):
            # Supersonic launch: bangs peel straight back over the crown into a mega slipstream/vortex!
            if kind == "bang":
                lift_s = 0.24 if style == "sky_storm" else 0.14
                dir_eff = JBH.make_tangent(
                    np.array([-0.32, 0.42 * side_fan, 0.88], dtype=np.float32),
                    n_out,
                    lift=lift_s,
                )
                curve_eff = np.array([-1.25, 0.38 * side_fan, 0.18 if style != "sky_storm" else 0.55], dtype=np.float32)
            elif kind == "crown":
                dir_eff = JBH.make_tangent(
                    np.array([-0.94, 0.22 * side_fan, 0.26], dtype=np.float32),
                    n_out,
                    lift=0.12,
                )
                curve_eff = np.array([-1.18, 0.20 * math.sin(ph), 0.15], dtype=np.float32)
            elif kind == "side":
                sgn_y = 1.0 if root[1] >= 0.0 else -1.0
                dir_eff = JBH.make_tangent(
                    np.array([-0.92, sgn_y * 0.28, 0.14], dtype=np.float32),
                    n_out,
                    lift=0.10,
                )
                curve_eff = np.array([-1.05, sgn_y * 0.35, 0.18], dtype=np.float32)
        elif style.startswith("wild_"):
            # Crazy spin/twirl hair: flare outward into centrifugal halo / cyclone ribbons!
            r_xy = max(1e-4, math.hypot(float(root[0]), float(root[1])))
            rx, ry = float(root[0]) / r_xy, float(root[1]) / r_xy
            if style == "wild_heli":
                # Tangential swirl + horizontal centrifugal halo
                dir_eff = JBH.make_tangent(
                    np.array([rx * 0.55 + ry * 0.72, ry * 0.55 - rx * 0.72, 0.28], dtype=np.float32),
                    n_out,
                    lift=0.20,
                )
                curve_eff = np.array([ry * 0.85, -rx * 0.85, 0.35], dtype=np.float32)
            else:
                dir_eff = JBH.make_tangent(
                    np.array([rx * 0.45 - ry * 0.55, ry * 0.45 + rx * 0.55, 0.55], dtype=np.float32),
                    n_out,
                    lift=0.22,
                )
                curve_eff = np.array([-0.55 + 0.50 * math.sin(ph), 0.65 * math.cos(ph), 0.48], dtype=np.float32)

        N0 = n_out - np.dot(n_out, dir_eff) * dir_eff
        nl = float(np.linalg.norm(N0))
        N0 = (N0 / nl) if nl > 1e-5 else np.array([0.0, 0.0, 1.0], dtype=np.float32)

        s_vals = [0.0] + [(si + 1) / float(N_MID + 1) for si in range(N_MID)] + [1.0]
        spine = []
        normals = []
        binorms = []

        side_sgn = 1.0 if (root[1] >= 0.0 or (lk_idx % 2 == 0)) else -1.0
        sgn_y = 1.0 if root[1] >= 0.0 else -1.0

        for s in s_vals:
            p = root + L_eff * (dir_eff * s + 0.34 * curve_eff * (s ** 1.80))
            sw = (s ** 1.28) * amp

            w1 = math.sin(h1 * ph1 - 4.2 * s + ph * 0.9)
            w2 = math.cos(h2 * ph1 - 5.2 * s + ph * 1.45)
            w_lat = math.sin(h1 * ph1 - 3.8 * s + ph * 0.75 + 1.2)

            if style == "fast_ripple":
                # Whip-snap high-RPM flap: crisp wavy bangs across brow + sleek skull-hugging crown/nape
                if kind == "bang":
                    disp = np.array([
                        1.4 * breeze + 2.8 * w2 + 2.0 * w1,
                        side_sgn * 2.0 - 1.2 + 4.8 * w_lat + 1.8 * w2,
                        -0.6 + 1.3 * w1 + 0.7 * w2 - 1.2 * (s ** 1.8),
                    ], dtype=np.float32) * sw
                elif kind == "crown":
                    disp = np.array([
                        -3.2 * breeze + 0.9 * w2,
                        1.6 * w_lat,
                        -0.35 * breeze + 0.65 * w1,
                    ], dtype=np.float32) * sw
                elif kind == "side":
                    disp = np.array([
                        -3.4 * breeze + 1.1 * w2,
                        sgn_y * (1.4 + 1.8 * (0.35 + 0.65 * w1)),
                        -0.25 + 0.75 * w1,
                    ], dtype=np.float32) * sw
                else:
                    disp = np.array([
                        -3.8 * breeze + 1.0 * w2,
                        1.8 * w_lat,
                        -0.35 + 0.75 * w1,
                    ], dtype=np.float32) * sw

            elif style == "fast_shampoo":
                # Silky double-harmonic wavy shampoo bangs across brow + sleek combed top/back
                if kind == "bang":
                    disp = np.array([
                        2.2 * breeze + 3.6 * w2 + 2.4 * w1,
                        side_sgn * 2.6 - 1.4 + 6.8 * w_lat + 2.8 * w2,
                        -0.8 + 1.4 * w1 + 0.9 * w2 - 1.6 * (s ** 1.9),
                    ], dtype=np.float32) * sw
                elif kind == "crown":
                    disp = np.array([
                        -3.4 * breeze + 1.0 * w2,
                        1.8 * w_lat,
                        -0.35 * breeze + 0.70 * w1,
                    ], dtype=np.float32) * sw
                elif kind == "side":
                    disp = np.array([
                        -3.5 * breeze + 1.2 * w2,
                        sgn_y * (1.8 + 2.2 * (0.35 + 0.65 * w1)),
                        -0.25 + 0.80 * w1,
                    ], dtype=np.float32) * sw
                else:
                    disp = np.array([
                        -4.0 * breeze + 1.1 * w2,
                        2.0 * w_lat,
                        -0.35 + 0.80 * w1,
                    ], dtype=np.float32) * sw

            elif style == "fast_swept":
                # Swept falcon overdrive: temple-swept wavy bangs + ultra-sleek backward slipstream
                if kind == "bang":
                    disp = np.array([
                        -3.6 * breeze + 2.4 * w2,
                        side_sgn * 2.4 + 4.4 * w_lat + 1.5 * w2,
                        -0.9 + 1.1 * w1 + 0.6 * w2,
                    ], dtype=np.float32) * sw
                elif kind == "crown":
                    disp = np.array([
                        -4.2 * breeze + 0.9 * w2,
                        1.4 * w_lat,
                        -0.45 * breeze + 0.55 * w1,
                    ], dtype=np.float32) * sw
                else:
                    disp = np.array([
                        -4.6 * breeze + 1.1 * w2,
                        1.8 * w_lat + (sgn_y * 1.8 if kind == "side" else 0.0),
                        -0.35 + 0.70 * w1,
                    ], dtype=np.float32) * sw

            elif style == "fast_part":
                # Wild side-part wavy bangs framing brow & temples + sleek combed crown/back
                if kind == "bang":
                    disp = np.array([
                        1.6 * breeze + 3.2 * w2 + 1.8 * w1,
                        5.2 * side_sgn + 6.0 * w_lat + 2.4 * w2,
                        -0.7 + 1.3 * w1 + 0.8 * w2 - 1.4 * (s ** 1.8),
                    ], dtype=np.float32) * sw
                elif kind == "crown":
                    disp = np.array([
                        -3.2 * breeze + 1.0 * w2,
                        1.8 * w_lat + 1.2 * side_sgn,
                        -0.35 * breeze + 0.65 * w1,
                    ], dtype=np.float32) * sw
                elif kind == "side":
                    disp = np.array([
                        -3.4 * breeze + 1.2 * w2,
                        sgn_y * (2.2 + 2.4 * (0.35 + 0.65 * w1)),
                        -0.25 + 0.80 * w1,
                    ], dtype=np.float32) * sw
                else:
                    disp = np.array([
                        -3.8 * breeze + 1.1 * w2,
                        2.0 * w_lat,
                        -0.35 + 0.75 * w1,
                    ], dtype=np.float32) * sw

            elif style == "hit_panic":
                # Violent left-right head-jerk hair whip & disheveled cross-snap
                jerk_y = wind_cfg.get("jerk_y", 0.0)
                disp = np.array([
                    -2.5 + 6.2 * w2 + 3.5 * math.cos(h1 * ph1 + ph),
                    jerk_y * 9.5 + 10.5 * w_lat + 5.0 * side_sgn * math.sin(h2 * ph1 + ph),
                    2.2 + 7.0 * w1 + 4.5 * math.sin(h2 * ph1 - 3.5 * s + ph),
                ], dtype=np.float32) * sw + n_out * (4.5 * sw)

            elif style == "hit_corkscrew":
                # Dizzy spinning halo flare around the wobbling head
                spin_ang = h1 * ph1 + ph * 1.4 - 3.8 * s
                disp = np.array([
                    -2.8 + 6.8 * math.cos(spin_ang),
                    8.5 * math.sin(spin_ang) + 4.2 * w_lat,
                    2.8 + 6.2 * math.cos(spin_ang + 1.1),
                ], dtype=np.float32) * sw + n_out * (5.2 * sw)

            elif style == "hit_poof":
                # Startle shockwave bristle: locks flare radially outward & tremble rapidly
                jitter = math.sin(h2 * ph1 - 4.2 * s + ph * 2.1)
                disp = n_out * ((9.5 + 5.5 * w1 + 3.2 * jitter) * sw) + np.array([
                    2.8 * w2,
                    6.8 * w_lat,
                    3.5 + 4.5 * jitter,
                ], dtype=np.float32) * sw

            elif style == "hit_thrash":
                # Chaotic ragdoll feather-burst thrash: huge crossing whip angles
                whip_x = math.sin(h1 * ph1 - 4.0 * s + ph * 1.8)
                whip_y = math.cos(h2 * ph1 - 4.6 * s + ph * 1.3)
                disp = np.array([
                    -1.5 + 8.5 * whip_x + 4.0 * w2,
                    11.5 * whip_y + sgn_y * 4.5,
                    3.0 + 8.0 * w1 - 2.5 * (s ** 1.8),
                ], dtype=np.float32) * sw + n_out * (4.0 * sw)

            elif style == "sky_shred":
                # Mach-10 wind-tunnel shred: extreme aft stretch + tight supersonic shockwave jitter
                shred = math.sin(h2 * ph1 - 4.6 * s + ph * 1.7)
                disp = np.array([
                    -11.5 * breeze + 4.4 * shred,
                    (sgn_y * 4.0 if kind == "side" else side_sgn * 2.2) + 5.6 * w_lat,
                    (4.2 if kind == "bang" else 1.4) + 4.8 * w1 + 3.0 * shred,
                ], dtype=np.float32) * sw

            elif style == "sky_vortex":
                # Rocket-cone vortex spiral: strands twist in a giant helical contrail behind the head!
                helix_a = h1 * ph1 - 3.8 * s + (lk_idx * 0.48)
                rad = (4.8 + 8.5 * (s ** 0.85)) * sw
                disp = np.array([
                    (-10.5 * breeze + 3.4 * w2) * sw,
                    rad * math.cos(helix_a),
                    (2.8 if kind == "bang" else 0.8) * sw + rad * math.sin(helix_a),
                ], dtype=np.float32)

            elif style == "sky_afterburner":
                # Hyper-flutter afterburner: giant multi-harmonic crashing supersonic waves
                disp = np.array([
                    -10.0 * breeze + 6.8 * w2 + 3.8 * w1,
                    (sgn_y * 5.8 if kind == "side" else side_sgn * 3.6) + 10.2 * w_lat + 4.0 * w2,
                    (4.8 if kind == "bang" else 2.0) + 7.6 * w1 + 3.6 * w2 + 2.4 * gust_z,
                ], dtype=np.float32) * sw

            elif style == "sky_storm":
                # Supersonic feather-storm blowout: huge flared plume + violent opposing gusts
                plume_z = 7.4 if kind in ("bang", "crown") else 2.8
                disp = np.array([
                    -9.2 * breeze + 6.2 * w2,
                    sgn_y * 6.5 + 9.6 * w_lat + 4.2 * math.cos(h2 * ph1 - 3.8 * s + ph),
                    plume_z + 7.2 * w1 + 3.6 * w2,
                ], dtype=np.float32) * sw + n_out * (4.0 * sw)

            elif style == "wild_heli":
                # Centrifugal helicopter tornado halo whipping horizontally around skull!
                r_xy = max(1e-4, math.hypot(float(root[0]), float(root[1])))
                rx, ry = float(root[0]) / r_xy, float(root[1]) / r_xy
                centrif = 11.0 + 4.5 * w1
                swirl = 12.5 + 3.5 * w2
                disp = np.array([
                    rx * centrif + ry * swirl + 2.6 * w2,
                    ry * centrif - rx * swirl + 2.6 * w_lat,
                    3.2 + 4.4 * math.sin(h2 * ph1 - 3.6 * s + ph),
                ], dtype=np.float32) * sw + n_out * (3.5 * sw)

            elif style == "wild_cyclone":
                # Barrel-roll corkscrew hair ribbons spiraling outward & aft
                cyc_a = h1 * ph1 - 4.0 * s + (lk_idx * 0.55)
                rad = (6.5 + 9.0 * (s ** 0.85)) * sw
                disp = np.array([
                    (-7.5 * breeze + 4.5 * w2) * sw,
                    rad * math.cos(cyc_a),
                    (3.6 if kind == "bang" else 1.4) * sw + rad * math.sin(cyc_a),
                ], dtype=np.float32)

            else:  # "wild_chaos"
                # Unhinged somersault flip-chaos: exploding multi-directional hair waves!
                disp = np.array([
                    8.5 * math.sin(h1 * ph1 - 3.8 * s + ph * 1.4) + 3.8 * w2,
                    11.5 * math.cos(h2 * ph1 - 4.2 * s + ph * 1.1) + sgn_y * 4.5,
                    5.5 + 8.5 * w1 + 4.2 * w2,
                ], dtype=np.float32) * sw + n_out * (6.2 * sw)

            p = p + disp

            if s > 0.04:
                ell = np.array([p[0] / 12.8, p[1] / 12.6, (p[2] - 0.5) / 18.0], dtype=np.float32)
                r_e = float(np.linalg.norm(ell))
                if r_e < 1.03:
                    p = p * (1.04 / max(0.25, r_e))

            spine.append(p)

        for idx_s, s in enumerate(s_vals):
            if idx_s == 0:
                tang = spine[1] - spine[0]
            elif idx_s == len(s_vals) - 1:
                tang = spine[-1] - spine[-2]
            else:
                tang = spine[idx_s + 1] - spine[idx_s - 1]
            tang /= max(1e-6, float(np.linalg.norm(tang)))
            twist = 0.28 * flutter * math.sin(h1 * ph1 - 3.0 * s + ph) * s
            n_cur = N0 - np.dot(N0, tang) * tang
            nl = float(np.linalg.norm(n_cur))
            n_cur = (n_cur / nl) if nl > 1e-5 else N0
            b_cur = np.cross(tang, n_cur)
            b_cur /= max(1e-6, float(np.linalg.norm(b_cur)))
            ct, st = math.cos(twist), math.sin(twist)
            normals.append(ct * n_cur + st * b_cur)
            binorms.append(-st * n_cur + ct * b_cur)

        verts.append(spine[0])
        for si in range(N_MID):
            k = si + 1
            s = s_vals[k]
            w_s = W_eff * (0.75 + 0.35 * math.sin(s * math.pi * 0.75)) * (1.0 - 0.72 * (s ** 1.75))
            h_s = H_eff * (1.0 - 0.70 * (s ** 1.5))
            c_p = spine[k]
            nc, bc = normals[k], binorms[k]
            verts.append(c_p + nc * h_s)
            verts.append(c_p + bc * w_s - nc * (0.20 * h_s))
            verts.append(c_p + nc * (0.08 * h_s))
            verts.append(c_p - bc * w_s - nc * (0.20 * h_s))
        verts.append(spine[-1])

    V = np.asarray(verts, dtype=np.float32)
    return (V @ head_rot.T) + head_pos[None, :]


def _sym_wings(
    hum_flap, hum_sweep, hum_pitch,
    elbow_flap, elbow_sweep, elbow_pitch,
    wrist_flap, wrist_sweep, wrist_pitch,
    aero_load, aero_twist,
    fold=0.0, alula_open=0.0, bank_asym=0.0,
    fx_phase=0.0, flutter_amp=0.0, splay_sweep=0.0, splay_dihedral=0.0,
    chord_stretch=1.0,
):
    L = _wing_side(
        hum_flap + bank_asym, hum_sweep, hum_pitch,
        elbow_flap, elbow_sweep, elbow_pitch,
        wrist_flap + 0.5 * bank_asym, wrist_sweep, wrist_pitch,
        aero_load, aero_twist, fold, alula_open,
        fx_phase, flutter_amp, splay_sweep, splay_dihedral, chord_stretch,
    )
    R = _wing_side(
        hum_flap - bank_asym, hum_sweep, hum_pitch,
        elbow_flap, elbow_sweep, elbow_pitch,
        wrist_flap - 0.5 * bank_asym, wrist_sweep, wrist_pitch,
        aero_load, aero_twist, fold, alula_open,
        fx_phase + 0.7, flutter_amp, splay_sweep, splay_dihedral, chord_stretch,
    )
    return dict(L=L, R=R)


# ==============================================================================
# CANDIDATE CLIP DEFINITIONS (12 CLIPS x 16 FRAMES = 192 FRAMES)
# ==============================================================================

CLIP_SPECS = [
    # --- Category 1: fast_fly (F1..F4) ---
    dict(
        id="fast_fly_f1",
        category="fast_fly",
        badge="F1",
        title="Whip-Snap High-RPM Flap",
        subtitle="2 snap-power wingbeats + sleek crown + crisp wavy bangs",
        description="Asymmetric power-stroke cadence snaps the wings down violently and tucks tight on the upstroke, while sleek combed top hair hugs the skull and forehead bangs ripple in crisp 4-harmonic waves.",
        defaultFps=24,
        recommendedSound="john_bird/flap1.wav",
        highlights=["2x snap power-strokes per loop", "Sleek skull-hugging top & nape hair", "Crisp 4-harmonic wavy brow bangs"],
        chips=["Snap-Power Flap", "Sleek Top Hair", "Crisp Bang Ripple"],
    ),
    dict(
        id="fast_fly_f2",
        category="fast_fly",
        badge="F2",
        title="Broad Flap + Lush Silky Ripple Bangs",
        subtitle="Broad 2-beat wingbeat + sleek top + 1.85x wavy shampoo bangs",
        description="Showcases the full feathered airfoil span in a rapid 2-beat overdrive stroke while sleek combed crown/back hair streams cleanly aft and 1.85x forehead bangs roll in silky multi-harmonic S-waves across the brow.",
        defaultFps=22,
        recommendedSound="john_bird/flap2.wav",
        highlights=["1.85x silky wavy brow bangs", "Zero spiky crown hair on top", "Broad high-camber wing chord"],
        chips=["Silky Bangs 1.85x", "Double-Wave Brow", "Broad Airfoil Arc"],
    ),
    dict(
        id="fast_fly_f3",
        category="fast_fly",
        badge="F3",
        title="Swept Falcon Overdrive Flap",
        subtitle="3-beat delta-swept sprint + sleek temple-swept wavy bangs",
        description="Aggressive forward nose-down sprint with wings swept strongly aft into a peregrine delta silhouette, pumping 3 rapid wingbeats per loop while wavy bangs sweep around the temples and top hair stays razor-sleek.",
        defaultFps=26,
        recommendedSound="john_bird/swoop.wav",
        highlights=["3 wingbeats per 16-frame loop", "Swept-back falcon delta wings", "Temple-swept bangs & sleek crown"],
        chips=["3-Beat Sprint", "Delta Sweep", "Temple Streamline"],
    ),
    dict(
        id="fast_fly_f4",
        category="fast_fly",
        badge="F4",
        title="Turbo Figure-8 + Rolling Side-Part Bangs",
        subtitle="High-RPM sculling figure-8 wings + parted wavy brow bangs",
        description="Wings trace a continuous 3D figure-8 sculling loop with alternating carve bank as John's crown stays sleek and his parted forehead bangs roll smoothly to both temples.",
        defaultFps=24,
        recommendedSound="john_bird/flap3.wav",
        highlights=["3D figure-8 wingtip sculling", "Dynamic side-carve head bank", "Parted wavy brow & temple bangs"],
        chips=["Figure-8 Scull", "Carve Bank", "Parted Brow Wave"],
    ),

    # --- Category 2: hit_flail (H1..H4) ---
    dict(
        id="hit_flail_h1",
        category="hit_flail",
        badge="H1",
        title="Asymmetric Panic Roll & Cross-Flap",
        subtitle="Out-of-phase L/R flapping + violent side-to-side head jerks",
        description="Left and right wings fire 135 degrees out of phase at mismatched sweeps while John's head snaps violently side-to-side in roll and yaw, whipping bangs across his face.",
        defaultFps=26,
        recommendedSound="john_bird/feather_hit.wav",
        highlights=["135-deg out-of-phase L/R wings", "Sharp +-24 deg panic roll jerks", "Ruffled cross-whipped bangs"],
        chips=["Out-of-Phase Wings", "Panic Roll Jerk", "Cross-Whip Hair"],
    ),
    dict(
        id="hit_flail_h2",
        category="hit_flail",
        badge="H2",
        title="Dizzy Corkscrew Wobble",
        subtitle="Counter-paddling wings + orbiting dazed head tilt + hair halo",
        description="Staggered counter-paddling wing strokes send John into a dazed 3D Lissajous head wobble with full alula spread and a spiraling halo of ruffled hair.",
        defaultFps=24,
        recommendedSound="john_bird/flap4.wav",
        highlights=["Counter-paddling L/R wings", "Dazed 3D Lissajous head wobble", "Spiraling radial hair halo"],
        chips=["Counter-Paddle", "Dizzy Orbit", "Halo Hair Flare"],
    ),
    dict(
        id="hit_flail_h3",
        category="hit_flail",
        badge="H3",
        title="Rapid Startle Snap-Back Flail",
        subtitle="4-beat startled micro-flail + chin-up recoil + poofed bristle",
        description="High-frequency 4-beat startled flutter with inverted braking wing pitches, sudden chin-up recoil, and radially poofed shockwave hair locks.",
        defaultFps=28,
        recommendedSound="john_bird/jv_hurt.wav",
        highlights=["4-beat frantic micro-flail", "Inverted L/R braking pitch", "Radially bristled shock hair"],
        chips=["4-Beat Micro-Flail", "Chin-Up Recoil", "Bristle Poof"],
    ),
    dict(
        id="hit_flail_h4",
        category="hit_flail",
        badge="H4",
        title="Chaotic Ragdoll Feather-Burst Thrash",
        subtitle="Multi-axis unhinged thrash + splayed feathers + wild tumble",
        description="Full 3-joint multi-axis thrashing where one wing over-folds while the other sweeps across the brow, shaking individual feathers loose in turbulent impact splay.",
        defaultFps=26,
        recommendedSound="john_bird/feather_hit.wav",
        highlights=["Opposing fold/sweep wing thrash", "Individual feather splay & flutter", "Multi-axis ragdoll head snap"],
        chips=["Ragdoll Thrash", "Feather Splay", "Disheveled Whip"],
    ),

    # --- Category 3: skypad_hyper (S1..S4) ---
    dict(
        id="skypad_hyper_s1",
        category="skypad_hyper",
        badge="S1",
        title="Mach-10 Wind-Tunnel Shred",
        subtitle="3.8x extreme aft hair shred + pinned delta supersonic flutter",
        description="At 4,000+ u/s off an info_skypad, bangs peel straight back over the crown and stretch 3.8x behind the skull with high-frequency shockwave ripples while pinned delta wings vibrate violently.",
        defaultFps=30,
        recommendedSound="skypad/launch.wav",
        highlights=["3.8x supersonic aft hair stretch", "High-RPM trailing-edge wing flutter", "Mach buffet head pitch & shake"],
        chips=["3.8x Wind Shred", "Pinned Delta", "Mach Buffet"],
    ),
    dict(
        id="skypad_hyper_s2",
        category="skypad_hyper",
        badge="S2",
        title="Rocket-Cone Vortex Spiral",
        subtitle="Corkscrew contrail hair helix + opposing vortex-twisted wings",
        description="Hair stretches into a screaming 3D corkscrew vortex spiraling behind John's head while counter-twisted swept wings flex under extreme G-load during skyward rocket ascent.",
        defaultFps=28,
        recommendedSound="skypad/launch.wav",
        highlights=["3D helical vortex hair contrail", "Counter-twisted aero wing flex", "Skyward rocket-climb attitude"],
        chips=["Vortex Helix", "Counter-Twist Wings", "Rocket Climb"],
    ),
    dict(
        id="skypad_hyper_s3",
        category="skypad_hyper",
        badge="S3",
        title="Hyper-Flutter Afterburner",
        subtitle="4-beat unhinged afterburner thrash + giant crashing hair waves",
        description="John flaps at an unhinged 4-beat afterburner tempo atop supersonic SkyPad speed, sending huge crashing multi-harmonic shockwaves through 3.4x stretched hair.",
        defaultFps=32,
        recommendedSound="skypad/launch.wav",
        highlights=["4-beat hyper-speed wing thrash", "3.4x crashing shockwave hair", "Forward/aft afterburner surge"],
        chips=["4-Beat Afterburner", "Shockwave Hair", "Launch Surge"],
    ),
    dict(
        id="skypad_hyper_s4",
        category="skypad_hyper",
        badge="S4",
        title="Supersonic Feather-Storm",
        subtitle="Extreme per-feather turbulence + upward supersonic plume blowout",
        description="Individual primary and secondary feathers vibrate and splay wildly in supersonic turbulence as asymmetric wing snaps meet an explosive upward hair-plume blowout.",
        defaultFps=30,
        recommendedSound="skypad/launch.wav",
        highlights=["Extreme per-feather storm flutter", "Upward supersonic hair plume", "Asymmetric shock-buffet snaps"],
        chips=["Feather-Storm", "Plume Blowout", "Shock Turbulence"],
    ),

    # --- Category 4: crazy_wild (W1..W3) ---
    dict(
        id="crazy_wild_w1",
        category="crazy_wild",
        badge="W1",
        title="Helicopter Skull-Spin",
        subtitle="Full 360-deg rotor yaw spin + pitched wing blades + tornado hair halo",
        description="John becomes a human avian helicopter: seamless 360-degree yaw spin with opposing rotor-pitched wings and hair flung horizontally outward into a swirling centrifugal tornado halo.",
        defaultFps=28,
        recommendedSound="john_bird/flap4.wav",
        highlights=["Full 360-deg helicopter yaw spin", "Opposing L/R rotor-blade wing pitch", "Centrifugal tornado hair halo"],
        chips=["360° Yaw Spin", "Rotor Wings", "Tornado Halo"],
    ),
    dict(
        id="crazy_wild_w2",
        category="crazy_wild",
        badge="W2",
        title="Barrel-Roll Cyclone Twirl",
        subtitle="Full 360-deg barrel-roll corkscrew + ribbon wings + spiral hair",
        description="Seamless 360-degree barrel-roll combined with a dizzy corkscrew yaw/pitch figure-8, counter-sweeping ribbon wings, and spiraling helical hair trails.",
        defaultFps=28,
        recommendedSound="john_bird/swoop.wav",
        highlights=["Full 360-deg barrel-roll twirl", "Counter-sweeping ribbon wings", "Spiraling cyclone hair ribbons"],
        chips=["360° Barrel Roll", "Corkscrew Twirl", "Spiral Ribbons"],
    ),
    dict(
        id="crazy_wild_w3",
        category="crazy_wild",
        badge="W3",
        title="Unhinged Somersault Flip-Chaos",
        subtitle="Full 360-deg diagonal flip + rubbery paddling + exploding hair/feathers",
        description="Total aerial anarchy: seamless 360-degree diagonal somersault flip while one wing over-folds high and the other paddles low amid heavy feather splay and exploding multi-directional hair waves.",
        defaultFps=30,
        recommendedSound="john_bird/feather_hit.wav",
        highlights=["Full 360-deg diagonal somersault", "Wild asymmetric rubbery paddling", "Exploding hair & feather splay"],
        chips=["360° Flip-Chaos", "Rubbery Paddle", "Feather Explosion"],
    ),
]


def eval_candidate_pose(clip_idx, k):
    """Evaluate frame k in [0..15] for candidate clip clip_idx in [0..11]."""
    u = k / float(FRAMES_PER_CLIP)
    ph1 = 2.0 * math.pi * u
    ph2 = 4.0 * math.pi * u
    ph3 = 6.0 * math.pi * u
    ph4 = 8.0 * math.pi * u

    spec = CLIP_SPECS[clip_idx]
    cid = spec["id"]

    if cid == "fast_fly_f1":
        # Whip-Snap High-RPM Flap: 2 snappy power-stroke beats per loop
        ph_w = ph2 + 0.42 * math.sin(ph2)
        s1, c1 = math.sin(ph_w), math.cos(ph_w)
        up = max(0.0, c1)
        dn = max(0.0, -c1)
        head_pos = np.array([
            1.4 + 0.8 * math.sin(ph2 + 0.3),
            0.0,
            BASE_Z + 2.4 * math.sin(ph2 - 1.0),
        ], dtype=np.float32)
        head_rot = JBH.rot_y(0.18 + 0.06 * s1) @ JBH.rot_x(0.04 * math.sin(ph1))
        wind_cfg = dict(
            style="fast_ripple", ph1=ph1, h1=2, h2=4,
            breeze=1.15, flutter=1.55, gust_z=0.45 * dn,
            bang_len_mul=1.45, bang_w_mul=1.22,
            crown_len_mul=1.04, crown_w_mul=1.02,
            side_len_mul=1.12, side_w_mul=1.05,
            back_len_mul=1.10, back_w_mul=1.04,
        )
        wing_pose = _sym_wings(
            hum_flap=0.72 * s1 + 0.08,
            hum_sweep=0.22 * c1 + 0.10,
            hum_pitch=0.34 + 0.22 * dn - 0.26 * up,
            elbow_flap=0.32 * math.sin(ph_w - 0.55) - 0.16 * up,
            elbow_sweep=0.18 - 0.36 * up,
            elbow_pitch=0.06,
            wrist_flap=0.58 * math.sin(ph_w - 0.85) - 0.28 * up,
            wrist_sweep=-0.04 - 0.44 * up,
            wrist_pitch=0.18 * dn - 0.32 * up,
            aero_load=1.18 * dn - 0.48 * up,
            aero_twist=0.68 * up,
            fold=0.18 * up,
            alula_open=0.35 * dn,
            fx_phase=ph2, flutter_amp=0.28,
        )

    elif cid == "fast_fly_f2":
        # Double-Harmonic Shampoo-Ripple Bangs: lush broad 2-beat wing + huge 2.75x wavy bangs
        s1, c1 = math.sin(ph2), math.cos(ph2)
        up = max(0.0, c1)
        dn = max(0.0, -c1)
        head_pos = np.array([
            0.9 * math.sin(ph2 + 0.4),
            1.1 * math.sin(ph1),
            BASE_Z + 2.6 * math.sin(ph2 - 1.05),
        ], dtype=np.float32)
        head_rot = JBH.rot_y(0.11 + 0.04 * c1) @ JBH.rot_x(0.08 * math.sin(ph1)) @ JBH.rot_z(0.05 * math.cos(ph1))
        wind_cfg = dict(
            style="fast_shampoo", ph1=ph1, h1=2, h2=4,
            breeze=1.25, flutter=1.85, gust_z=0.50 * dn,
            bang_len_mul=1.85, bang_w_mul=1.42,
            crown_len_mul=1.08, crown_w_mul=1.06,
            side_len_mul=1.18, side_w_mul=1.08,
            back_len_mul=1.15, back_w_mul=1.06,
        )
        wing_pose = _sym_wings(
            hum_flap=0.66 * s1 + 0.14,
            hum_sweep=0.18 * c1 + 0.04,
            hum_pitch=0.38 + 0.18 * dn - 0.18 * up,
            elbow_flap=0.28 * math.sin(ph2 - 0.60) - 0.10 * up,
            elbow_sweep=0.16 - 0.28 * up,
            elbow_pitch=0.06,
            wrist_flap=0.52 * math.sin(ph2 - 0.88) - 0.22 * up,
            wrist_sweep=-0.04 - 0.32 * up,
            wrist_pitch=0.16 * dn - 0.22 * up,
            aero_load=1.08 * dn - 0.38 * up,
            aero_twist=0.55 * up,
            alula_open=0.45,
            fx_phase=ph2, flutter_amp=0.22,
        )

    elif cid == "fast_fly_f3":
        # Swept Falcon Overdrive Flap: 3-beat delta-swept sprint
        s1, c1 = math.sin(ph3), math.cos(ph3)
        up = max(0.0, c1)
        dn = max(0.0, -c1)
        head_pos = np.array([
            2.4 + 0.7 * math.sin(ph3),
            0.0,
            BASE_Z + 1.4 * math.sin(ph3 - 0.9),
        ], dtype=np.float32)
        head_rot = JBH.rot_y(0.28 + 0.04 * s1) @ JBH.rot_x(0.03 * math.sin(ph1))
        wind_cfg = dict(
            style="fast_swept", ph1=ph1, h1=3, h2=6,
            breeze=1.45, flutter=1.65, gust_z=0.35 * dn,
            bang_len_mul=1.50, bang_w_mul=1.20,
            crown_len_mul=1.06, crown_w_mul=1.04,
            side_len_mul=1.16, side_w_mul=1.06,
            back_len_mul=1.18, back_w_mul=1.06,
        )
        wing_pose = _sym_wings(
            hum_flap=0.46 * s1 + 0.04,
            hum_sweep=0.48 + 0.14 * c1,
            hum_pitch=0.24 + 0.18 * dn - 0.16 * up,
            elbow_flap=0.22 * math.sin(ph3 - 0.50),
            elbow_sweep=0.34 - 0.18 * up,
            elbow_pitch=0.05,
            wrist_flap=0.38 * math.sin(ph3 - 0.80),
            wrist_sweep=0.14 - 0.24 * up,
            wrist_pitch=0.12 * dn - 0.18 * up,
            aero_load=0.92 * dn - 0.30 * up,
            aero_twist=0.42 * up,
            fold=0.30,
            alula_open=0.25,
            fx_phase=ph3, flutter_amp=0.35,
        )

    elif cid == "fast_fly_f4":
        # Turbo Figure-8 + Wild Side-Part Billow
        s1, c1 = math.sin(ph2), math.cos(ph2)
        up = max(0.0, c1)
        dn = max(0.0, -c1)
        bank = 0.16 * math.cos(ph1)
        head_pos = np.array([
            1.1 * math.sin(ph2),
            2.2 * math.sin(ph1),
            BASE_Z + 2.2 * math.sin(ph2 - 0.8),
        ], dtype=np.float32)
        head_rot = JBH.rot_x(bank) @ JBH.rot_z(0.14 * math.sin(ph1)) @ JBH.rot_y(0.12)
        wind_cfg = dict(
            style="fast_part", ph1=ph1, h1=2, h2=4,
            breeze=1.25, flutter=1.75, gust_z=0.45 * dn,
            bang_len_mul=1.68, bang_w_mul=1.34,
            crown_len_mul=1.06, crown_w_mul=1.05,
            side_len_mul=1.18, side_w_mul=1.08,
            back_len_mul=1.14, back_w_mul=1.06,
        )
        wing_pose = _sym_wings(
            hum_flap=0.58 * s1 + 0.16,
            hum_sweep=0.44 * c1 + 0.12,
            hum_pitch=0.40 + 0.24 * s1,
            elbow_flap=0.30 * math.sin(ph2 - 0.55),
            elbow_sweep=0.18 - 0.24 * max(0.0, -s1),
            elbow_pitch=0.14 * c1,
            wrist_flap=0.48 * math.sin(ph2 - 0.90),
            wrist_sweep=-0.08 - 0.22 * up,
            wrist_pitch=0.26 * c1,
            aero_load=0.96 * abs(c1),
            aero_twist=0.50 * max(0.0, -s1),
            bank_asym=0.15 * math.sin(ph1),
            alula_open=0.65,
            fx_phase=ph2, flutter_amp=0.26,
        )

    elif cid == "hit_flail_h1":
        # Asymmetric Panic Roll & Cross-Flap: L and R 135 deg out of phase + sharp roll jerks
        sL, cL = math.sin(ph3), math.cos(ph3)
        sR, cR = math.sin(ph3 + 2.35), math.cos(ph3 + 2.35)
        jerk_roll = 0.36 * math.sin(ph2) + 0.14 * math.cos(ph3)
        jerk_yaw = 0.28 * math.cos(ph1) - 0.16 * math.sin(ph3)
        head_pos = np.array([
            -1.4 + 1.8 * math.sin(ph2),
            3.2 * math.sin(ph2 + 0.7),
            BASE_Z + 2.6 * math.cos(ph3),
        ], dtype=np.float32)
        head_rot = JBH.rot_x(jerk_roll) @ JBH.rot_z(jerk_yaw) @ JBH.rot_y(-0.14 + 0.20 * math.sin(ph3))
        wind_cfg = dict(
            style="hit_panic", ph1=ph1, h1=3, h2=6,
            breeze=1.25, flutter=2.45, gust_z=1.1,
            jerk_y=math.sin(ph2 + 0.5),
            bang_len_mul=1.95, bang_w_mul=1.55,
            crown_len_mul=1.75, crown_w_mul=1.45,
            side_len_mul=1.70, side_w_mul=1.40,
            back_len_mul=1.60, back_w_mul=1.35,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.78 * sL + 0.16,
                hum_sweep=0.35 * cL + 0.08,
                hum_pitch=0.35 + 0.40 * cL,
                elbow_flap=0.40 * math.sin(ph3 - 0.4),
                elbow_sweep=0.10 + 0.32 * sL,
                elbow_pitch=0.18 * sL,
                wrist_flap=0.62 * math.sin(ph3 - 0.7),
                wrist_sweep=-0.12 + 0.38 * cL,
                wrist_pitch=0.28 * cL,
                aero_load=1.10 * sL,
                aero_twist=0.65 * cL,
                alula_open=0.95,
                fx_phase=ph3, flutter_amp=0.55, splay_sweep=5.5, splay_dihedral=4.5,
            ),
            R=_wing_side(
                hum_flap=0.78 * sR + 0.10,
                hum_sweep=-0.28 * cR + 0.15,
                hum_pitch=0.28 - 0.42 * cR,
                elbow_flap=0.42 * math.sin(ph3 + 1.9),
                elbow_sweep=0.24 - 0.35 * sR,
                elbow_pitch=-0.20 * sR,
                wrist_flap=0.65 * math.sin(ph3 + 1.5),
                wrist_sweep=-0.24 - 0.32 * cR,
                wrist_pitch=-0.30 * cR,
                aero_load=1.15 * sR,
                aero_twist=-0.70 * cR,
                alula_open=0.95,
                fx_phase=ph3 + 1.7, flutter_amp=0.58, splay_sweep=6.0, splay_dihedral=4.8,
            ),
        )

    elif cid == "hit_flail_h2":
        # Dizzy Corkscrew Wobble: counter-paddling wings + Lissajous orbit + hair halo
        sL, cL = math.sin(ph2), math.cos(ph2)
        sR, cR = -sL, -cL
        head_pos = np.array([
            2.2 * math.cos(ph2),
            3.8 * math.sin(ph1),
            BASE_Z + 2.8 * math.sin(ph2 + 0.8),
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_x(0.32 * math.sin(ph1))
            @ JBH.rot_z(0.34 * math.cos(ph1))
            @ JBH.rot_y(-0.18 * math.sin(ph2))
        )
        wind_cfg = dict(
            style="hit_corkscrew", ph1=ph1, h1=2, h2=4,
            breeze=1.15, flutter=2.35, gust_z=0.9,
            bang_len_mul=1.90, bang_w_mul=1.55,
            crown_len_mul=1.80, crown_w_mul=1.50,
            side_len_mul=1.75, side_w_mul=1.40,
            back_len_mul=1.65, back_w_mul=1.35,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.62 * sL + 0.22,
                hum_sweep=0.52 * cL - 0.05,
                hum_pitch=0.45 + 0.35 * sL,
                elbow_flap=0.35 * math.sin(ph2 - 0.5),
                elbow_sweep=0.22 + 0.25 * cL,
                elbow_pitch=0.16 * cL,
                wrist_flap=0.52 * math.sin(ph2 - 0.8),
                wrist_sweep=-0.10 + 0.28 * sL,
                wrist_pitch=0.28 * cL,
                aero_load=0.95 * cL,
                aero_twist=0.60 * sL,
                alula_open=1.0,
                fx_phase=ph2, flutter_amp=0.42, splay_sweep=4.5, splay_dihedral=3.8,
            ),
            R=_wing_side(
                hum_flap=0.62 * sR + 0.18,
                hum_sweep=0.52 * cR + 0.20,
                hum_pitch=0.15 + 0.42 * sR,
                elbow_flap=0.36 * math.sin(ph2 + 2.5),
                elbow_sweep=0.28 - 0.28 * cR,
                elbow_pitch=-0.18 * cR,
                wrist_flap=0.54 * math.sin(ph2 + 2.1),
                wrist_sweep=-0.18 - 0.26 * sR,
                wrist_pitch=-0.30 * cR,
                aero_load=1.05 * cR,
                aero_twist=-0.65 * sR,
                alula_open=1.0,
                fx_phase=ph2 + 1.4, flutter_amp=0.46, splay_sweep=4.8, splay_dihedral=4.2,
            ),
        )

    elif cid == "hit_flail_h3":
        # Rapid Startle Snap-Back Flail: 4-beat startled flutter + chin-up recoil + poofed bristle
        s4, c4 = math.sin(ph4), math.cos(ph4)
        s4_opp, c4_opp = math.sin(ph4 + 1.9), math.cos(ph4 + 1.9)
        head_pos = np.array([
            -2.6 + 0.9 * math.sin(ph4),
            1.6 * math.cos(ph3),
            BASE_Z + 3.4 + 1.8 * math.sin(ph4 - 0.5),
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_y(-0.34 + 0.10 * s4)
            @ JBH.rot_z(0.22 * math.sin(ph2))
            @ JBH.rot_x(0.20 * math.cos(ph3))
        )
        wind_cfg = dict(
            style="hit_poof", ph1=ph1, h1=2, h2=4,
            breeze=1.05, flutter=2.65, gust_z=1.35,
            bang_len_mul=1.85, bang_w_mul=1.60,
            crown_len_mul=1.75, crown_w_mul=1.55,
            side_len_mul=1.65, side_w_mul=1.45,
            back_len_mul=1.60, back_w_mul=1.40,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.55 * s4 + 0.42,
                hum_sweep=-0.25 + 0.34 * c4,
                hum_pitch=0.68 + 0.28 * s4,
                elbow_flap=0.38 * c4 + 0.18,
                elbow_sweep=0.42 - 0.20 * s4,
                elbow_pitch=0.22 * s4,
                wrist_flap=0.56 * math.sin(ph4 - 0.5),
                wrist_sweep=-0.32 + 0.28 * c4,
                wrist_pitch=0.35 * c4,
                aero_load=1.10 * s4,
                aero_twist=0.55 * c4,
                fold=0.22,
                alula_open=1.0,
                fx_phase=ph4, flutter_amp=0.62, splay_sweep=6.5, splay_dihedral=5.5,
            ),
            R=_wing_side(
                hum_flap=0.55 * s4_opp + 0.38,
                hum_sweep=-0.12 - 0.36 * c4_opp,
                hum_pitch=-0.24 + 0.34 * s4_opp,
                elbow_flap=0.40 * c4_opp + 0.14,
                elbow_sweep=0.36 + 0.24 * s4_opp,
                elbow_pitch=-0.24 * s4_opp,
                wrist_flap=0.58 * math.sin(ph4 + 1.4),
                wrist_sweep=-0.28 - 0.30 * c4_opp,
                wrist_pitch=-0.36 * c4_opp,
                aero_load=1.15 * s4_opp,
                aero_twist=-0.62 * c4_opp,
                fold=0.18,
                alula_open=1.0,
                fx_phase=ph4 + 2.1, flutter_amp=0.65, splay_sweep=6.8, splay_dihedral=5.8,
            ),
        )

    elif cid == "hit_flail_h4":
        # Chaotic Ragdoll Feather-Burst Thrash
        s3, c3 = math.sin(ph3), math.cos(ph3)
        s2, c2 = math.sin(ph2), math.cos(ph2)
        head_pos = np.array([
            2.0 * math.sin(ph2 + 0.4),
            3.6 * math.cos(ph2),
            BASE_Z - 1.5 + 3.8 * math.sin(ph3 - 0.6),
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_y(0.26 * math.sin(ph2))
            @ JBH.rot_x(0.38 * math.cos(ph2))
            @ JBH.rot_z(-0.34 * math.sin(ph1 + 0.8))
        )
        wind_cfg = dict(
            style="hit_thrash", ph1=ph1, h1=3, h2=5,
            breeze=1.30, flutter=2.55, gust_z=1.1,
            bang_len_mul=2.10, bang_w_mul=1.65,
            crown_len_mul=1.85, crown_w_mul=1.50,
            side_len_mul=1.80, side_w_mul=1.45,
            back_len_mul=1.75, back_w_mul=1.45,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=-0.22 + 0.72 * s3,
                hum_sweep=0.45 * c2 + 0.15,
                hum_pitch=0.22 + 0.48 * s2,
                elbow_flap=0.45 * c3,
                elbow_sweep=0.58 * max(0.0, s2),
                elbow_pitch=0.24 * c2,
                wrist_flap=-0.52 * s3 + 0.25 * c2,
                wrist_sweep=-0.62 * max(0.0, s2),
                wrist_pitch=0.42 * s2,
                aero_load=1.35 * c3,
                aero_twist=0.90 * s2,
                fold=0.45 * max(0.0, s2),
                alula_open=1.0,
                fx_phase=ph3, flutter_amp=0.78, splay_sweep=8.5, splay_dihedral=6.5,
            ),
            R=_wing_side(
                hum_flap=0.32 - 0.76 * s2,
                hum_sweep=-0.42 * s3 + 0.12,
                hum_pitch=0.45 - 0.50 * c3,
                elbow_flap=-0.38 * s3 + 0.20,
                elbow_sweep=0.52 * max(0.0, -c2),
                elbow_pitch=-0.26 * s3,
                wrist_flap=0.58 * c3 - 0.20,
                wrist_sweep=-0.55 * max(0.0, -c2),
                wrist_pitch=-0.45 * c3,
                aero_load=-1.30 * s2,
                aero_twist=-0.92 * c3,
                fold=0.42 * max(0.0, -c2),
                alula_open=1.0,
                fx_phase=ph3 + 1.8, flutter_amp=0.82, splay_sweep=9.0, splay_dihedral=7.0,
            ),
        )

    elif cid == "skypad_hyper_s1":
        # Mach-10 Wind-Tunnel Shred: 3.6x aft hair stretch + swept delta supersonic flutter
        s4, c4 = math.sin(ph4), math.cos(ph4)
        head_pos = np.array([
            -2.0 + 0.6 * s4,
            0.4 * math.cos(ph4),
            BASE_Z + 2.2 + 0.7 * c4,
        ], dtype=np.float32)
        head_rot = JBH.rot_y(-0.22 + 0.04 * s4) @ JBH.rot_x(0.05 * math.sin(ph3)) @ JBH.rot_z(0.04 * c4)
        wind_cfg = dict(
            style="sky_shred", ph1=ph1, h1=4, h2=8,
            breeze=2.05, flutter=2.65, gust_z=1.0,
            bang_len_mul=3.65, bang_w_mul=1.85,
            crown_len_mul=3.25, crown_w_mul=1.70,
            side_len_mul=2.95, side_w_mul=1.55,
            back_len_mul=3.15, back_w_mul=1.60,
        )
        wing_pose = _sym_wings(
            hum_flap=0.20 + 0.22 * s4,
            hum_sweep=0.52 + 0.08 * c4,
            hum_pitch=0.34 + 0.16 * s4,
            elbow_flap=0.14 + 0.18 * math.sin(ph4 - 0.5),
            elbow_sweep=0.28 + 0.08 * s4,
            elbow_pitch=0.08 * c4,
            wrist_flap=0.26 * math.sin(ph4 - 0.8),
            wrist_sweep=0.18 + 0.12 * c4,
            wrist_pitch=0.20 * s4,
            aero_load=1.40 + 0.48 * s4,
            aero_twist=0.65 * c4,
            fold=0.28,
            alula_open=0.25,
            fx_phase=ph4, flutter_amp=1.05, splay_sweep=3.5, splay_dihedral=2.8,
            chord_stretch=1.18,
        )

    elif cid == "skypad_hyper_s2":
        # Rocket-Cone Vortex Spiral: corkscrew hair vortex + opposing vortex-twisted wings
        s2, c2 = math.sin(ph2), math.cos(ph2)
        head_pos = np.array([
            -1.4 + 0.9 * math.cos(ph2),
            1.4 * math.sin(ph2),
            BASE_Z + 3.2 + 1.4 * math.sin(ph2 + 0.6),
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_y(-0.28 + 0.06 * s2)
            @ JBH.rot_x(0.18 * math.sin(ph1))
            @ JBH.rot_z(0.10 * math.cos(ph1))
        )
        wind_cfg = dict(
            style="sky_vortex", ph1=ph1, h1=2, h2=4,
            breeze=1.85, flutter=2.55, gust_z=1.1,
            bang_len_mul=3.25, bang_w_mul=1.80,
            crown_len_mul=3.00, crown_w_mul=1.65,
            side_len_mul=2.80, side_w_mul=1.50,
            back_len_mul=2.95, back_w_mul=1.55,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.28 + 0.30 * s2,
                hum_sweep=0.46 + 0.14 * c2,
                hum_pitch=0.34 + 0.34 * math.sin(ph1),
                elbow_flap=0.20 * c2,
                elbow_sweep=0.24 + 0.12 * s2,
                elbow_pitch=0.24 * math.cos(ph1),
                wrist_flap=0.32 * math.sin(ph2 - 0.6),
                wrist_sweep=0.12 + 0.16 * s2,
                wrist_pitch=0.36 * math.sin(ph1),
                aero_load=1.35 + 0.45 * c2,
                aero_twist=0.85 * math.sin(ph1) + 0.45 * c2,
                fold=0.22,
                alula_open=0.50,
                fx_phase=ph3, flutter_amp=0.82, splay_sweep=3.8, splay_dihedral=3.2,
                chord_stretch=1.15,
            ),
            R=_wing_side(
                hum_flap=0.28 - 0.30 * s2,
                hum_sweep=0.46 - 0.14 * c2,
                hum_pitch=0.34 - 0.34 * math.sin(ph1),
                elbow_flap=-0.20 * c2,
                elbow_sweep=0.24 - 0.12 * s2,
                elbow_pitch=-0.24 * math.cos(ph1),
                wrist_flap=-0.32 * math.sin(ph2 - 0.6),
                wrist_sweep=0.12 - 0.16 * s2,
                wrist_pitch=-0.36 * math.sin(ph1),
                aero_load=1.35 - 0.45 * c2,
                aero_twist=-0.85 * math.sin(ph1) - 0.45 * c2,
                fold=0.22,
                alula_open=0.50,
                fx_phase=ph3 + 1.5, flutter_amp=0.82, splay_sweep=3.8, splay_dihedral=3.2,
                chord_stretch=1.15,
            ),
        )

    elif cid == "skypad_hyper_s3":
        # Hyper-Flutter Afterburner: 4-beat unhinged afterburner thrash + giant crashing hair waves
        s4, c4 = math.sin(ph4), math.cos(ph4)
        up = max(0.0, c4)
        dn = max(0.0, -c4)
        head_pos = np.array([
            1.8 * math.sin(ph4),
            0.9 * math.sin(ph2),
            BASE_Z + 2.8 + 2.2 * math.sin(ph4 - 0.9),
        ], dtype=np.float32)
        head_rot = JBH.rot_y(-0.14 + 0.12 * s4) @ JBH.rot_x(0.10 * math.sin(ph2)) @ JBH.rot_z(0.08 * math.cos(ph2))
        wind_cfg = dict(
            style="sky_afterburner", ph1=ph1, h1=3, h2=6,
            breeze=1.75, flutter=2.75, gust_z=1.25,
            bang_len_mul=3.25, bang_w_mul=2.05,
            crown_len_mul=2.85, crown_w_mul=1.80,
            side_len_mul=2.60, side_w_mul=1.60,
            back_len_mul=2.75, back_w_mul=1.65,
        )
        wing_pose = _sym_wings(
            hum_flap=0.84 * s4 + 0.12,
            hum_sweep=0.34 + 0.30 * c4,
            hum_pitch=0.36 + 0.28 * dn - 0.24 * up,
            elbow_flap=0.38 * math.sin(ph4 - 0.5) - 0.12 * up,
            elbow_sweep=0.20 - 0.22 * up,
            elbow_pitch=0.10 * c4,
            wrist_flap=0.66 * math.sin(ph4 - 0.8) - 0.24 * up,
            wrist_sweep=0.04 - 0.24 * up,
            wrist_pitch=0.22 * dn - 0.28 * up,
            aero_load=1.45 * dn - 0.65 * up,
            aero_twist=0.78 * up,
            fold=0.12,
            alula_open=0.75,
            fx_phase=ph4, flutter_amp=0.90, splay_sweep=4.0, splay_dihedral=3.5,
            chord_stretch=1.14,
        )

    elif cid == "skypad_hyper_s4":
        # Supersonic Feather-Storm: extreme per-feather turbulence + upward hair-plume blowout
        s3, c3 = math.sin(ph3), math.cos(ph3)
        s4, c4 = math.sin(ph4), math.cos(ph4)
        head_pos = np.array([
            -1.6 + 1.2 * s4,
            1.8 * math.sin(ph3),
            BASE_Z + 2.6 + 1.6 * c3,
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_y(-0.24 + 0.10 * c3)
            @ JBH.rot_x(0.22 * math.sin(ph2))
            @ JBH.rot_z(0.16 * math.cos(ph3))
        )
        wind_cfg = dict(
            style="sky_storm", ph1=ph1, h1=3, h2=6,
            breeze=1.70, flutter=2.75, gust_z=1.3,
            bang_len_mul=3.35, bang_w_mul=1.95,
            crown_len_mul=2.95, crown_w_mul=1.75,
            side_len_mul=2.70, side_w_mul=1.60,
            back_len_mul=2.85, back_w_mul=1.65,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.45 * s3 + 0.35 * c4 + 0.16,
                hum_sweep=0.42 + 0.26 * c3,
                hum_pitch=0.34 + 0.40 * s4,
                elbow_flap=0.35 * c4,
                elbow_sweep=0.24 + 0.20 * s3,
                elbow_pitch=0.20 * s3,
                wrist_flap=0.55 * math.sin(ph4 - 0.6),
                wrist_sweep=0.10 - 0.26 * c3,
                wrist_pitch=0.34 * c4,
                aero_load=1.40 * s3 + 0.35,
                aero_twist=0.95 * c4,
                fold=0.20,
                alula_open=0.95,
                fx_phase=ph4, flutter_amp=1.25, splay_sweep=5.5, splay_dihedral=4.5,
                chord_stretch=1.16,
            ),
            R=_wing_side(
                hum_flap=0.45 * math.sin(ph3 + 1.6) - 0.35 * c4 + 0.12,
                hum_sweep=0.42 - 0.26 * c3,
                hum_pitch=0.34 - 0.42 * s4,
                elbow_flap=-0.35 * c4,
                elbow_sweep=0.24 - 0.20 * s3,
                elbow_pitch=-0.22 * s3,
                wrist_flap=0.58 * math.sin(ph4 + 1.4),
                wrist_sweep=0.10 + 0.26 * c3,
                wrist_pitch=-0.36 * c4,
                aero_load=1.40 * math.cos(ph3 + 0.9) + 0.35,
                aero_twist=-0.98 * c4,
                fold=0.20,
                alula_open=0.95,
                fx_phase=ph4 + 1.9, flutter_amp=1.28, splay_sweep=5.8, splay_dihedral=4.8,
                chord_stretch=1.16,
            ),
        )

    elif cid == "crazy_wild_w1":
        # Helicopter Skull-Spin: full 360-deg yaw spin + rotor-blade wings + tornado hair halo
        s2, c2 = math.sin(ph2), math.cos(ph2)
        s4, c4 = math.sin(ph4), math.cos(ph4)
        head_pos = np.array([
            0.9 * math.cos(ph2),
            0.9 * math.sin(ph2),
            BASE_Z + 4.0 + 2.6 * s2,
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_z(ph1)
            @ JBH.rot_y(0.14 * s2)
            @ JBH.rot_x(0.12 * c2)
        )
        wind_cfg = dict(
            style="wild_heli", ph1=ph1, h1=3, h2=6,
            breeze=1.65, flutter=2.55, gust_z=0.9,
            bang_len_mul=2.20, bang_w_mul=1.65,
            crown_len_mul=2.00, crown_w_mul=1.55,
            side_len_mul=1.90, side_w_mul=1.45,
            back_len_mul=1.90, back_w_mul=1.45,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.08 + 0.14 * s4,
                hum_sweep=-0.04 + 0.10 * c4,
                hum_pitch=0.45 + 0.24 * s4,
                elbow_flap=0.06 * c4,
                elbow_sweep=0.04,
                elbow_pitch=0.14 + 0.12 * c4,
                wrist_flap=0.10 * math.sin(ph4 - 0.5),
                wrist_sweep=-0.06,
                wrist_pitch=0.22 + 0.18 * s4,
                aero_load=0.85 + 0.35 * s4,
                aero_twist=0.55 * c4,
                alula_open=0.85,
                fx_phase=ph4, flutter_amp=0.75, splay_sweep=3.5, splay_dihedral=2.8,
            ),
            R=_wing_side(
                hum_flap=0.08 - 0.14 * s4,
                hum_sweep=-0.04 - 0.10 * c4,
                hum_pitch=-0.45 - 0.24 * s4,
                elbow_flap=-0.06 * c4,
                elbow_sweep=0.04,
                elbow_pitch=-0.14 - 0.12 * c4,
                wrist_flap=-0.10 * math.sin(ph4 - 0.5),
                wrist_sweep=-0.06,
                wrist_pitch=-0.22 - 0.18 * s4,
                aero_load=-0.85 - 0.35 * s4,
                aero_twist=-0.55 * c4,
                alula_open=0.85,
                fx_phase=ph4 + 1.5, flutter_amp=0.75, splay_sweep=3.5, splay_dihedral=2.8,
            ),
        )

    elif cid == "crazy_wild_w2":
        # Barrel-Roll Cyclone Twirl: full 360-deg barrel-roll + corkscrew yaw/pitch + ribbon wings
        s1, c1 = math.sin(ph1), math.cos(ph1)
        s2, c2 = math.sin(ph2), math.cos(ph2)
        s3, c3 = math.sin(ph3), math.cos(ph3)
        head_pos = np.array([
            1.6 * c2,
            5.2 * s1,
            BASE_Z + 4.4 * math.sin(ph1 - 1.1),
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_x(ph1)
            @ JBH.rot_z(0.45 * s1)
            @ JBH.rot_y(-0.20 + 0.28 * c2)
        )
        wind_cfg = dict(
            style="wild_cyclone", ph1=ph1, h1=2, h2=4,
            breeze=1.60, flutter=2.45, gust_z=1.0,
            bang_len_mul=2.35, bang_w_mul=1.70,
            crown_len_mul=2.15, crown_w_mul=1.60,
            side_len_mul=2.05, side_w_mul=1.50,
            back_len_mul=2.10, back_w_mul=1.55,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.38 * s2 + 0.15,
                hum_sweep=0.48 * c2 + 0.12,
                hum_pitch=0.32 + 0.45 * s1,
                elbow_flap=0.34 * math.sin(ph2 - 0.7),
                elbow_sweep=0.22 + 0.24 * s3,
                elbow_pitch=0.28 * c1,
                wrist_flap=0.52 * math.sin(ph2 - 1.1),
                wrist_sweep=-0.08 + 0.28 * c3,
                wrist_pitch=0.38 * s2,
                aero_load=1.15 * c2,
                aero_twist=0.95 * s1,
                alula_open=0.80,
                fx_phase=ph3, flutter_amp=0.80, splay_sweep=4.2, splay_dihedral=3.5,
            ),
            R=_wing_side(
                hum_flap=-0.38 * s2 + 0.15,
                hum_sweep=-0.48 * c2 + 0.12,
                hum_pitch=0.32 - 0.45 * s1,
                elbow_flap=-0.34 * math.sin(ph2 - 0.7),
                elbow_sweep=0.22 - 0.24 * s3,
                elbow_pitch=-0.28 * c1,
                wrist_flap=-0.52 * math.sin(ph2 - 1.1),
                wrist_sweep=-0.08 - 0.28 * c3,
                wrist_pitch=-0.38 * s2,
                aero_load=-1.15 * c2,
                aero_twist=-0.95 * s1,
                alula_open=0.80,
                fx_phase=ph3 + 1.6, flutter_amp=0.80, splay_sweep=4.2, splay_dihedral=3.5,
            ),
        )

    else:  # "crazy_wild_w3"
        # Unhinged Somersault Flip-Chaos: full 360-deg diagonal flip + rubbery paddling + feather burst
        s1, c1 = math.sin(ph1), math.cos(ph1)
        s2, c2 = math.sin(ph2), math.cos(ph2)
        s3, c3 = math.sin(ph3), math.cos(ph3)
        head_pos = np.array([
            4.2 * s1,
            3.2 * math.sin(ph2),
            BASE_Z + 1.5 + 5.0 * s2,
        ], dtype=np.float32)
        head_rot = (
            JBH.rot_y(ph1)
            @ JBH.rot_z(0.55 * s2)
            @ JBH.rot_x(0.42 * c1)
        )
        wind_cfg = dict(
            style="wild_chaos", ph1=ph1, h1=3, h2=6,
            breeze=1.55, flutter=2.75, gust_z=1.2,
            bang_len_mul=2.45, bang_w_mul=1.80,
            crown_len_mul=2.20, crown_w_mul=1.65,
            side_len_mul=2.10, side_w_mul=1.55,
            back_len_mul=2.10, back_w_mul=1.55,
        )
        wing_pose = dict(
            L=_wing_side(
                hum_flap=0.78 * s3 + 0.25,
                hum_sweep=0.52 * c2 + 0.10,
                hum_pitch=0.35 + 0.45 * c3,
                elbow_flap=0.45 * c3,
                elbow_sweep=0.55 * max(0.0, s2),
                elbow_pitch=0.28 * s2,
                wrist_flap=-0.58 * s3 + 0.24 * c2,
                wrist_sweep=-0.55 * max(0.0, s2),
                wrist_pitch=0.45 * c2,
                aero_load=1.40 * c3,
                aero_twist=1.00 * s2,
                fold=0.52 * max(0.0, s2),
                alula_open=1.0,
                fx_phase=ph3, flutter_amp=1.25, splay_sweep=7.5, splay_dihedral=6.5,
            ),
            R=_wing_side(
                hum_flap=-0.78 * c3 - 0.15,
                hum_sweep=-0.55 * s2 + 0.12,
                hum_pitch=0.25 - 0.48 * s3,
                elbow_flap=-0.42 * s3 + 0.18,
                elbow_sweep=0.50 * max(0.0, -c2),
                elbow_pitch=-0.30 * c3,
                wrist_flap=0.62 * c3 - 0.18,
                wrist_sweep=-0.52 * max(0.0, -c2),
                wrist_pitch=-0.48 * s3,
                aero_load=-1.35 * s3,
                aero_twist=-1.05 * c3,
                fold=0.48 * max(0.0, -c2),
                alula_open=1.0,
                fx_phase=ph3 + 1.8, flutter_amp=1.28, splay_sweep=7.8, splay_dihedral=6.8,
            ),
        )

    fname = f"{cid}_{k:02d}"
    return fname, head_pos, head_rot, wind_cfg, wing_pose


def build_contact_sheet(surfaces, tex_np, category_id, out_path):
    """Render a multi-row verification contact sheet for the clips in a category."""
    cat_indices = [i for i, c in enumerate(CLIP_SPECS) if c["category"] == category_id]
    tile_w, tile_h = 360, 290
    sheet = Image.new("RGB", (tile_w * 4, tile_h * len(cat_indices)), (10, 15, 25))
    dr = ImageDraw.Draw(sheet)

    # 4 key poses across each 16-frame clip, including 3/4 front & steep side/rear angles
    if category_id == "fast_fly":
        col_views = [
            (2,   28, 14, 150.0, 50.0, "f02 3/4 Front"),
            (6,   24, 14, 150.0, 50.0, "f06 Mid-Cycle"),
            (10, -34, 15, 150.0, 50.0, "f10 Opp-3/4"),
            (13, -76, 14, 152.0, 50.0, "f13 Side Sweep"),
        ]
    elif category_id == "hit_flail":
        col_views = [
            (2,   28, 15, 154.0, 50.0, "f02 3/4 Front"),
            (6,  -28, 16, 154.0, 50.0, "f06 Opp-3/4"),
            (10,  18, 22, 154.0, 50.0, "f10 High-Front"),
            (13, -72, 16, 154.0, 50.0, "f13 Side Flail"),
        ]
    elif category_id == "crazy_wild":
        col_views = [
            (0,   28, 16, 166.0, 51.0, "f00 0deg Turn"),
            (4,   28, 16, 166.0, 51.0, "f04 90deg Turn"),
            (8,   28, 16, 166.0, 51.0, "f08 180deg Turn"),
            (12,  28, 16, 166.0, 51.0, "f12 270deg Turn"),
        ]
    else:  # skypad_hyper
        col_views = [
            (2,   30, 14, 168.0, 51.0, "f02 3/4 Front"),
            (6,  -68, 15, 174.0, 51.0, "f06 Side Streak"),
            (10, -118, 18, 174.0, 51.0, "f10 Rear-3/4"),
            (14,  24, 16, 168.0, 51.0, "f14 Front-Up"),
        ]

    for row_i, clip_idx in enumerate(cat_indices):
        spec = CLIP_SPECS[clip_idx]
        start_f = clip_idx * FRAMES_PER_CLIP
        for col_i, (k_f, az, el, dist, tz, col_tag) in enumerate(col_views):
            fi = start_f + k_f
            im_t = JBH.render_preview_tile(
                surfaces, tex_np, fi=fi,
                az_deg=az, el_deg=el, dist=dist, tgt_z=tz,
                tile_w=tile_w, tile_h=tile_h,
            )
            gx, gy = col_i * tile_w, row_i * tile_h
            sheet.paste(im_t, (gx, gy))
            dr.rectangle([gx + 6, gy + 6, gx + tile_w - 8, gy + 26], fill=(10, 16, 28))
            lbl = f"{spec['badge']} {spec['title'][:22]} | {col_tag}"
            col_fill = (125, 211, 252) if col_i == 0 else (253, 224, 71) if col_i < 3 else (110, 231, 183)
            dr.text((gx + 10, gy + 10), lbl, fill=col_fill)

    sheet.save(out_path, optimize=True)


def main():
    t0 = time.time()
    os.makedirs(OUT_VOTE_DIR, exist_ok=True)

    print("1. Loading greenscreen portrait & building base head...", flush=True)
    front_rgb, front_mask = JBH.load_and_despill_front()
    head_data = JBH.build_base_head(front_rgb, front_mask)
    hair_tex = JBH.build_hair_strand_texture(front_rgb)
    wing_hawk = JBH.build_feather_atlas(front_rgb, variant="hawk")

    print("2. Building hair locks spec & wing template...", flush=True)
    hair_locks, hair_uvs, hair_tris = JBH.build_hair_locks_spec(head_data["grid_pos"])
    wing_builder = JBH.WingTemplateBuilder()

    head_v0 = head_data["verts"]
    head_tris = head_data["tris"]
    ring_meta = head_data["ring_meta"]

    head_frames = []
    hair_frames = []
    wing_frames = []
    frame_names = []

    total_frames = len(CLIP_SPECS) * FRAMES_PER_CLIP
    print(f"3. Generating {total_frames} frames across {len(CLIP_SPECS)} candidate clips...", flush=True)

    for clip_idx in range(len(CLIP_SPECS)):
        for k in range(FRAMES_PER_CLIP):
            fname, h_pos, h_rot, wind_cfg, wing_pose = eval_candidate_pose(clip_idx, k)
            frame_names.append(fname)

            # Cap scalp-cap ripple so the skull never distorts at Mach-10 speeds
            tj = ring_meta[:, 0]
            th_k = ring_meta[:, 1]
            hw_rip = ring_meta[:, 2]
            scalp_breeze = min(1.85, wind_cfg["breeze"])
            scalp_flutter = min(2.20, wind_cfg["flutter"])
            ph_s = wind_cfg["ph1"] * wind_cfg["h1"]
            rip = hw_rip * scalp_flutter * 0.36 * np.sin(ph_s - 2.5 * tj + 2.0 * th_k)
            hv = head_v0.copy()
            hv[:, 0] -= hw_rip * scalp_breeze * 0.48
            hv[:, 1] += rip * np.cos(th_k)
            hv[:, 2] += np.abs(rip) * 0.55
            hv_world = (hv @ h_rot.T) + h_pos[None, :]
            hn_world = JBH.compute_vertex_normals(hv_world, head_tris)
            head_frames.append(([tuple(map(float, p)) for p in hv_world], [tuple(map(float, n)) for n in hn_world]))

            hr_world = eval_candidate_hair(hair_locks, wind_cfg, h_rot, h_pos)
            hr_norms = JBH.compute_vertex_normals(hr_world, hair_tris)
            hair_frames.append(([tuple(map(float, p)) for p in hr_world], [tuple(map(float, n)) for n in hr_norms]))

            wg_world = eval_candidate_wing(wing_builder, wing_pose, h_rot, h_pos)
            wg_norms = JBH.compute_vertex_normals(wg_world, wing_builder.tris)
            wing_frames.append(([tuple(map(float, p)) for p in wg_world], [tuple(map(float, n)) for n in wg_norms]))

    surfaces = [
        dict(name="head", shader="progs/john_bird_head", tris=head_tris, st=head_data["uvs"], frames=head_frames),
        dict(name="hair_breezy", shader="progs/john_bird_hair", tris=hair_tris, st=hair_uvs, frames=hair_frames),
        dict(name="wings_bird", shader="progs/john_bird_wings", tris=wing_builder.tris, st=wing_builder.uvs, frames=wing_frames),
    ]

    md3_path = os.path.join(OUT_VOTE_DIR, "john_bird_candidates.md3")
    md3lib.write(md3_path, dict(name="progs/john_bird_candidates.md3", surfaces=surfaces, frame_names=frame_names))
    print(f"   Wrote {md3_path} ({os.path.getsize(md3_path)/1e6:.2f} MB, {total_frames} frames)", flush=True)

    manifest = dict(
        model="john_bird_candidates.md3",
        totalFrames=total_frames,
        framesPerClip=FRAMES_PER_CLIP,
        baseZ=BASE_Z,
        categories=[
            dict(
                id="fast_fly",
                title="High-Speed Flight",
                subtitle="Fast wingbeats + super wavy & billowing bangs (>= 950 u/s Boost / Carve)",
            ),
            dict(
                id="hit_flail",
                title="Hit / Disoriented",
                subtitle="Frantic multi-directional flapping, erratic head jerks & ruffled hair on damage",
            ),
            dict(
                id="skypad_hyper",
                title="Super Launch Pad Hyper-Speed",
                subtitle="Extreme supersonic hair & feather chaos at 3,800-4,400 u/s off info_skypad",
            ),
            dict(
                id="crazy_wild",
                title="Crazy / Wild Spin & Twirl",
                subtitle="Totally unhinged 360-deg spinning, barrel-rolling & somersaulting aerial chaos",
            ),
        ],
        clips=[],
    )
    for idx, c in enumerate(CLIP_SPECS):
        entry = dict(c)
        entry["startFrame"] = idx * FRAMES_PER_CLIP
        entry["frameCount"] = FRAMES_PER_CLIP
        manifest["clips"].append(entry)

    manifest_path = os.path.join(OUT_VOTE_DIR, "candidates_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"   Wrote {manifest_path}", flush=True)

    print("4. Rendering 4 visual verification contact sheets...", flush=True)
    tex_np = {
        "progs/john_bird_head": np.asarray(head_data["head_tex"], dtype=np.float32),
        "progs/john_bird_hair": np.asarray(hair_tex, dtype=np.float32),
        "progs/john_bird_wings": np.asarray(wing_hawk, dtype=np.float32),
    }

    for cat_id, fn in (
        ("fast_fly", "verify_fast_fly.png"),
        ("hit_flail", "verify_hit_flail.png"),
        ("skypad_hyper", "verify_skypad_hyper.png"),
        ("crazy_wild", "verify_crazy_wild.png"),
    ):
        out_png = os.path.join(OUT_VOTE_DIR, fn)
        build_contact_sheet(surfaces, tex_np, cat_id, out_png)
        print(f"   Saved {out_png}", flush=True)

    print(f"Done in {time.time() - t0:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
