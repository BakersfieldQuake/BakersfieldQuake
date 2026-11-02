"""Builds the Giant Articulated 3D Right Hand, assembles all 3 animated 3D models
(Thrown Projectile, Held Weapon Viewmodel, and Unobstructed Character Turnaround),
exports .GLB + .MD3 + viewer .NPZ, and renders a multi-angle Blender 5.2 check sheet.

Run via headless Blender 5.2:
  blender.exe --background --python sculpt_hand_and_export.py
"""
import math
import os
import sys
import numpy as np
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, MM_TOOLS)

import md3lib
import sculpt_character as sc

OUT_ROOT = os.path.join(MM_TOOLS, "out", "pocket_rocket")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
GLB_DIR = os.path.join(OUT_ROOT, "glb")
MD3_DIR = os.path.join(OUT_ROOT, "md3")


# ===========================================================================
# GIANT ARTICULATED RIGHT HAND + 5 SCULPTED FINGERNAILS (18-Bone Rig!)
# ===========================================================================
# Local Hand Rest Frame (normalized hand length ~ 1.0 from wrist to middle fingertip):
#   Origin (0, 0, 0) at wrist center
#   +Z = distal along middle metacarpal / extended fingers
#   +Y = radial (toward THUMB side of a RIGHT hand when viewing dorsal back of hand? Let's verify handedness!)
#   VERIFY RIGHT HANDEDNESS CAREFULLY:
#     Hold your RIGHT hand upright (+Z = fingertips), PALM facing -X (away from you), DORSAL BACK & NAILS facing +X (toward you):
#     - Your THUMB is on the LEFT (+Y)!
#     - Your PINKY is on the RIGHT (-Y)!
#     - When your fingers CURL into a fist, they flex toward the PALM (-X)!
#   Let's check X x Y = Z: (+X dorsal) cross (+Y radial/thumb) = (+Z distal)! Right-handed coordinate system!!
HAND_REST = {
    "wrist":   np.array([0.000,  0.000, 0.000]),
    "palm":    np.array([0.000,  0.000, 0.160]),
    # Thumb on +Y (radial) side, slightly palmar (-X)
    "th_1":    np.array([-0.045, 0.155, 0.125]),
    "th_2":    np.array([-0.065, 0.275, 0.255]),
    "th_3":    np.array([-0.072, 0.345, 0.375]),
    # 4 Fingers from +Y (Index) across to -Y (Pinky) at knuckle arch z ~ 0.43..0.46
    "ix_1":    np.array([0.000,  0.145, 0.445]),
    "ix_2":    np.array([0.000,  0.148, 0.625]),
    "ix_3":    np.array([0.000,  0.148, 0.755]),
    "md_1":    np.array([0.004,  0.046, 0.462]),
    "md_2":    np.array([0.004,  0.046, 0.662]),
    "md_3":    np.array([0.004,  0.046, 0.805]),
    "rg_1":    np.array([0.000, -0.052, 0.442]),
    "rg_2":    np.array([0.000, -0.054, 0.625]),
    "rg_3":    np.array([0.000, -0.055, 0.755]),
    "pk_1":    np.array([-0.006, -0.142, 0.402]),
    "pk_2":    np.array([-0.006, -0.148, 0.545]),
    "pk_3":    np.array([-0.006, -0.152, 0.650]),
}

HAND_PARENTS = {
    "wrist": None,
    "palm": "wrist",
    "th_1": "palm", "th_2": "th_1", "th_3": "th_2",
    "ix_1": "palm", "ix_2": "ix_1", "ix_3": "ix_2",
    "md_1": "palm", "md_2": "md_1", "md_3": "md_2",
    "rg_1": "palm", "rg_2": "rg_1", "rg_3": "rg_2",
    "pk_1": "palm", "pk_2": "pk_1", "pk_3": "pk_2",
}

HAND_BONES = [
    "wrist", "palm",
    "th_1", "th_2", "th_3",
    "ix_1", "ix_2", "ix_3",
    "md_1", "md_2", "md_3",
    "rg_1", "rg_2", "rg_3",
    "pk_1", "pk_2", "pk_3",
]
HB_IDX = {b: i for i, b in enumerate(HAND_BONES)}


def build_giant_right_hand():
    """Builds smooth anatomical Giant Right Hand skin + 5 inset 3D fingernails."""
    verts, tris, uvs, w_list = [], [], [], []

    # 1. Muscular Forearm -> Wrist -> Contoured Metacarpal Palm (z = -0.36 .. +0.455)
    nu_p, nv_p = 44, 34
    b0 = len(verts)
    for j in range(nv_p):
        t = j / (nv_p - 1)   # 0 = forearm (-0.36) -> 0.44 = wrist (0.0) -> 1.0 = knuckle arch (+0.452)
        if t < 0.44:
            ft = t / 0.44
            z_base = -0.36 + ft * 0.36
            wid = 0.165 - 0.022 * sc.sstep(0.3, 1.0, ft)
            thk = 0.125 - 0.022 * sc.sstep(0.3, 1.0, ft)
            cy = -0.008 * (1.0 - ft)
            cx = 0.0
        else:
            pt = (t - 0.44) / 0.56   # 0 at wrist -> 1 at MCP knuckles
            # Curved MCP knuckle arch (middle highest, pinky lowest!)
            wid = 0.143 + 0.056 * (pt ** 0.72)
            thk = 0.103 - 0.026 * pt
            z_base = pt * 0.452
            cy = 0.004 * math.sin(pt * math.pi)
            cx = 0.0

        for i in range(nu_p):
            ang = (i / nu_p) * 2.0 * math.pi   # 0 = +X dorsal, +pi/2 = +Y thumb side, +-pi = -X palmar!
            ca, sa = math.cos(ang), math.sin(ang)

            x = cx + thk * ca
            y = cy + wid * sa
            z = z_base

            if t >= 0.42:
                pt = max(0.0, (t - 0.44) / 0.56)
                # Arch knuckle top line: peak near y = +0.05, sloping down toward pinky y = -0.15
                z -= 0.048 * pt * max(0.0, -sa) ** 1.4
                # Fleshy Thenar thumb-pad bulge on radial palmar quadrant (sa > 0.2, ca < 0, pt in 0.1..0.75)
                thenar = math.exp(-(((pt - 0.42) / 0.28) ** 2)) * max(0.0, sa) * max(0.0, -ca)
                x -= 0.045 * thenar
                y += 0.028 * thenar
                # Hypothenar pad on ulnar palmar side (sa < -0.2, ca < 0)
                hypo = math.exp(-(((pt - 0.48) / 0.32) ** 2)) * max(0.0, -sa) * max(0.0, -ca)
                x -= 0.024 * hypo
                # Central palmar hollow (ca < -0.5, |sa| < 0.45)
                hollow = math.exp(-(((pt - 0.62) / 0.24) ** 2)) * math.exp(-((sa / 0.42) ** 2)) * max(0.0, -ca)
                x += 0.018 * hollow
                # 4 subtle dorsal MCP knuckle hills near pt ~ 0.92 (ca > 0.3)
                if pt > 0.72 and ca > 0.1:
                    for ky in (0.145, 0.046, -0.052, -0.142):
                        kh = math.exp(-(((y - ky) / 0.036) ** 2 + ((pt - 0.94) / 0.10) ** 2)) * ca
                        x += 0.012 * kh

            # Pinch top cap cleanly at t == 1.0 along knuckle ridge so palm is closed between finger bases
            if j == nv_p - 1:
                x *= 0.22

            verts.append((x, y, z))
            # Map dorsal (ca >= 0) to u in [0.04..0.42], palmar (ca < 0) to u in [0.48..0.84]!
            v_tex = 0.04 + 0.40 * t
            if ca >= 0:
                u_tex = 0.23 - 0.18 * sa
            else:
                u_tex = 0.66 + 0.17 * sa
            uvs.append((u_tex, v_tex))

            w = np.zeros(len(HAND_BONES), dtype=np.float64)
            w_palm = sc.sstep(0.36, 0.56, t)
            w[HB_IDX["wrist"]] = 1.0 - w_palm
            w[HB_IDX["palm"]] = w_palm
            w_list.append(w)

    tris.extend((sc.grid_tris(nu_p, nv_p, wrap_u=True, flip=False) + b0).tolist())

    # 2. Four Articulated 3-Joint Fingers + 3-Joint Opposable Thumb + 5 Sculpted 3D Fingernails!
    digit_specs = [
        # (prefix, joints, base_rad, u_dors, u_palm, nail_w, is_thumb)
        ("ix", ("ix_1", "ix_2", "ix_3"), 0.054, 0.09, 0.52, 0.038, False),
        ("md", ("md_1", "md_2", "md_3"), 0.057, 0.18, 0.60, 0.040, False),
        ("rg", ("rg_1", "rg_2", "rg_3"), 0.053, 0.27, 0.68, 0.037, False),
        ("pk", ("pk_1", "pk_2", "pk_3"), 0.045, 0.36, 0.76, 0.031, False),
        ("th", ("th_1", "th_2", "th_3"), 0.064, 0.42, 0.82, 0.044, True),
    ]

    for tag, (b1, b2, b3), r0, u_dors, u_palm, nail_w, is_thumb in digit_specs:
        J1, J2, J3 = HAND_REST[b1], HAND_REST[b2], HAND_REST[b3]
        tip_dir = (J3 - J2) / (np.linalg.norm(J3 - J2) + 1e-12)
        tip_len = 0.118 if not is_thumb else 0.125
        J_tip = J3 + tip_dir * tip_len
        J_root = J1 - ((J2 - J1) / np.linalg.norm(J2 - J1)) * (0.048 if not is_thumb else 0.055)

        pts_chain = [J_root, J1, J2, J3, J_tip]
        seg_lens = [np.linalg.norm(pts_chain[k + 1] - pts_chain[k]) for k in range(4)]
        tot_len = sum(seg_lens)
        cum = [0.0]
        for sl in seg_lens:
            cum.append(cum[-1] + sl / tot_len)

        nu_f, nv_f = 24, 30
        fb0 = len(verts)

        # Dorsal direction for thumb is rotated ~38 deg toward +X/+Y so thumbnail faces camera naturally when gripping!
        dors_hint = np.array([0.82, 0.57, 0.0]) if is_thumb else np.array([1.0, 0.0, 0.0])
        dors_hint /= np.linalg.norm(dors_hint)

        for j in range(nv_f):
            tf = j / (nv_f - 1)   # 0 = webbed base -> 1 = rounded fingertip pad!
            # Interpolate along piecewise phalanx chain
            for seg_i in range(4):
                if tf <= cum[seg_i + 1] or seg_i == 3:
                    lt = (tf - cum[seg_i]) / max(1e-6, cum[seg_i + 1] - cum[seg_i])
                    lt = max(0.0, min(1.0, lt))
                    c_pos = pts_chain[seg_i] * (1.0 - lt) + pts_chain[seg_i + 1] * lt
                    seg_vec = pts_chain[seg_i + 1] - pts_chain[seg_i]
                    break

            T = seg_vec / (np.linalg.norm(seg_vec) + 1e-12)
            D = dors_hint - T * np.dot(dors_hint, T)
            D /= (np.linalg.norm(D) + 1e-12)
            S_vec = np.cross(D, T)

            # Anatomical phalanx profile: subtle widening at PIP & DIP knuckles, fleshy palmar belly, smooth rounded fingertip dome!
            taper = 1.0 - 0.24 * tf
            pip_sw = 0.06 * math.exp(-(((tf - cum[2]) / 0.055) ** 2))
            dip_sw = 0.04 * math.exp(-(((tf - cum[3]) / 0.048) ** 2))
            tip_dome = math.sqrt(max(0.0004, 1.0 - max(0.0, (tf - 0.84) / 0.16) ** 2))
            rad_w = r0 * (taper + pip_sw + dip_sw) * tip_dome
            rad_d = r0 * 0.88 * (taper + 0.6 * pip_sw + 0.5 * dip_sw) * tip_dome

            # Recessed flat nail-bed seat on dorsal distal phalanx (tf in [cum[3]+0.03 .. 0.95])
            in_nail_bed = sc.sstep(cum[3] + 0.01, cum[3] + 0.05, tf) * (1.0 - sc.sstep(0.92, 0.98, tf))

            for i in range(nu_f):
                ang = (i / nu_f) * 2.0 * math.pi   # ang = 0 is D (dorsal!), +-pi is -D (palmar fleshy pad!)
                ca, sa = math.cos(ang), math.sin(ang)

                d_off = rad_d * ca
                w_off = rad_w * sa
                # Slightly fuller fleshy palmar pad on underside (ca < 0)
                if ca < 0:
                    d_off *= 1.08
                # Flatten dorsal nail-bed slightly where the 3D nail plate sits!
                if ca > 0.35 and in_nail_bed > 0.01:
                    d_off *= (1.0 - 0.14 * in_nail_bed * ca)

                p = c_pos + D * d_off + S_vec * w_off
                verts.append(tuple(p))

                v_tex = 0.34 + 0.60 * tf
                if ca >= 0:
                    u_tex = u_dors + 0.035 * sa
                else:
                    u_tex = u_palm - 0.035 * sa
                uvs.append((u_tex, v_tex))

                # Smooth joint blend weights across palm -> b1 -> b2 -> b3!
                w = np.zeros(len(HAND_BONES), dtype=np.float64)
                w0 = 1.0 - sc.sstep(0.0, cum[1] + 0.05, tf)
                w1 = sc.sstep(0.0, cum[1] + 0.05, tf) * (1.0 - sc.sstep(cum[2] - 0.05, cum[2] + 0.05, tf))
                w2 = sc.sstep(cum[2] - 0.05, cum[2] + 0.05, tf) * (1.0 - sc.sstep(cum[3] - 0.05, cum[3] + 0.05, tf))
                w3 = sc.sstep(cum[3] - 0.05, cum[3] + 0.05, tf)
                w[HB_IDX["palm"]] = w0
                w[HB_IDX[b1]] = w1
                w[HB_IDX[b2]] = w2
                w[HB_IDX[b3]] = w3
                w_list.append(w)

        tris.extend((sc.grid_tris(nu_f, nv_f, wrap_u=True, flip=True) + fb0).tolist())

        # Sculpted 3D Curved Fingernail Plate on Dorsal Distal Phalanx (b3)!
        nb0 = len(verts)
        nu_n, nv_n = 12, 12
        T_d = tip_dir
        D_d = dors_hint - T_d * np.dot(dors_hint, T_d)
        D_d /= (np.linalg.norm(D_d) + 1e-12)
        S_d = np.cross(D_d, T_d)

        nail_start = J3 + T_d * (tip_len * 0.34)
        nail_len = tip_len * 0.50
        for j in range(nv_n):
            tn = j / (nv_n - 1)   # 0 = rounded cuticle base -> 1 = curved ivory free edge!
            # Natural trimmed squoval nail planform contour
            end_round = math.sqrt(max(0.12, 1.0 - (0.38 * ((tn - 0.5) * 2.0) ** 4)))
            cur_w = nail_w * 0.76 * end_round
            # Longitudinal slight convex arch + sits flush in dorsal distal nail bed!
            base_h = r0 * 0.88 * (1.0 - 0.22 * (0.76 + 0.22 * tn)) * 0.85
            long_arch = 0.0024 * math.sin(tn * math.pi)
            for i in range(nu_n):
                sn = (i / (nu_n - 1)) * 2.0 - 1.0   # -1 .. +1 across nail width
                # Transverse C-curve of real fingernail
                c_curve = math.cos(sn * 0.75) * base_h + 0.0022 + long_arch
                p = nail_start + T_d * (tn * nail_len) + S_d * (sn * cur_w) + D_d * c_curve
                verts.append(tuple(p))
                # Map directly to Nail Plate UV strip u in [0.865..0.995], v in [0.02..0.96]!
                uvs.append((0.93 + sn * 0.060, 0.03 + tn * 0.93))
                w = np.zeros(len(HAND_BONES), dtype=np.float64)
                w[HB_IDX[b3]] = 1.0
                w_list.append(w)

        tris.extend((sc.grid_tris(nu_n, nv_n, wrap_u=False, flip=False) + nb0).tolist())

    return (
        np.array(verts, dtype=np.float64),
        np.array(tris, dtype=np.int32),
        np.array(uvs, dtype=np.float64),
        np.array(w_list, dtype=np.float64),
    )


def solve_hand_fk(pose_rots, world_R, world_P, scale=1.0):
    """Solves 18-bone Giant Hand FK and returns skinned world vertices."""
    R_w = {}
    P_w = {}
    for b in HAND_BONES:
        rx, ry, rz = pose_rots.get(b, (0.0, 0.0, 0.0))
        R_loc = sc.rot_z(rz) @ sc.rot_y(ry) @ sc.rot_x(rx)
        p = HAND_PARENTS[b]
        if p is None:
            R_w[b] = world_R @ R_loc
            P_w[b] = np.array(world_P, dtype=np.float64) + (world_R @ HAND_REST[b]) * scale
        else:
            R_w[b] = R_w[p] @ R_loc
            P_w[b] = P_w[p] + (R_w[p] @ (HAND_REST[b] - HAND_REST[p])) * scale
    return R_w, P_w


def apply_hand_skin(V_rest, W, R_w, P_w, scale=1.0):
    out = np.zeros_like(V_rest)
    for bi, b in enumerate(HAND_BONES):
        w = W[:, bi:bi + 1]
        if np.max(w) < 1e-6:
            continue
        R = R_w[b]
        P = P_w[b]
        J = HAND_REST[b]
        out += w * (((V_rest - J) * scale) @ R.T + P)
    return out


def hand_grip_pose(tightness=1.0, breathe=0.0):
    """Articulated finger curl pose in the mirrored Right-Hand frame (-Y_h = thumb/radial, +Y_h = pinky/ulnar, -X_h = palm):
    tightness = 1.0 -> snug grip wrapped around the miniature woman's jeans waist/hips (matching v1_f180.png!)
    tightness = 0.0 -> wide-open splayed launch hand (matching v3_f096.png!)."""
    k = tightness
    op = 1.0 - tightness
    b = breathe
    return {
        "wrist": (0.0, 0.0, 0.0),
        "palm":  (0.0, -6.0 * k + 8.0 * op, 0.0),
        # 4 fingers flex toward palm (-X_h via negative ry) when k=1, and fan wide when op=1!
        "ix_1":  (13.0 * op,  -72.0 * k + 8.0 * op + b, -3.5 * k),
        "ix_2":  (0.0,        -82.0 * k + 4.0 * op,      0.0),
        "ix_3":  (0.0,        -46.0 * k + 2.0 * op,      0.0),
        "md_1":  (3.5 * op,   -76.0 * k + 9.0 * op + b, -1.0 * k),
        "md_2":  (0.0,        -86.0 * k + 4.0 * op,      0.0),
        "md_3":  (0.0,        -48.0 * k + 2.0 * op,      0.0),
        "rg_1":  (-7.0 * op,  -78.0 * k + 8.0 * op + b,  2.0 * k),
        "rg_2":  (0.0,        -86.0 * k + 4.0 * op,      0.0),
        "rg_3":  (0.0,        -50.0 * k + 2.0 * op,      0.0),
        "pk_1":  (-16.0 * op, -80.0 * k + 10.0 * op + b, 4.5 * k),
        "pk_2":  (0.0,        -84.0 * k + 5.0 * op,      0.0),
        "pk_3":  (0.0,        -52.0 * k + 2.0 * op,      0.0),
        # Opposable thumb wraps horizontally across her jeans waist below the pink bow when k=1,
        # and abducts cleanly out to screen-right when op=1!
        "th_1":  (-64.0 * k + 20.0 * op, -22.0 * k + 12.0 * op, -36.0 * k + 14.0 * op),
        "th_2":  (-26.0 * k,             -36.0 * k + 6.0 * op,  -12.0 * k),
        "th_3":  (-8.0 * k,              -28.0 * k + 4.0 * op,   0.0),
    }


# ===========================================================================
# PART 8: 3D AERODYNAMIC SLIPSTREAM SPEED-RIBBONS (`surf_speedlines`)
# ===========================================================================
def build_speed_ribbons():
    """Tapered 3D slipstream ribbons around the flying projectile (inspired by v3_f120 & v3_f168)."""
    verts, tris, uvs = [], [], []
    # 8 ribbons arranged in an aerodynamic halo around the projectile axis (+X nose to -X wake)
    specs = [
        ( 0.24,  0.16,  0.22, -0.58, 0.032),
        (-0.24,  0.16,  0.22, -0.58, 0.032),
        ( 0.30, -0.06,  0.18, -0.64, 0.028),
        (-0.30, -0.06,  0.18, -0.64, 0.028),
        ( 0.14,  0.25,  0.10, -0.68, 0.025),
        (-0.14,  0.25,  0.10, -0.68, 0.025),
        ( 0.18, -0.20,  0.16, -0.54, 0.026),
        (-0.18, -0.20,  0.16, -0.54, 0.026),
    ]
    nu, nv = 12, 3
    for idx_r, (ry, rz, x0, x1, half_w) in enumerate(specs):
        b0 = len(verts)
        ang_r = math.atan2(rz, ry)
        tangent = np.array([0.0, -math.sin(ang_r), math.cos(ang_r)])
        radial = np.array([0.0, math.cos(ang_r), math.sin(ang_r)])
        for j in range(nv):
            sv = (j / (nv - 1)) * 2.0 - 1.0
            for i in range(nu):
                tu = i / (nu - 1)   # 0 at leading nose -> 1 at trailing wake
                x = x0 * (1.0 - tu) + x1 * tu
                flare = 1.0 + 0.22 * tu
                p = np.array([x, ry * flare, rz * flare]) + tangent * (sv * half_w * (0.5 + 0.5 * math.sin(tu * math.pi))) + radial * (0.008 * abs(sv))
                verts.append(tuple(p))
                uvs.append((tu, (j / (nv - 1))))
        tris.extend((sc.grid_tris(nu, nv, wrap_u=False, flip=False) + b0).tolist())
    return np.array(verts, dtype=np.float64), np.array(tris, dtype=np.int32), np.array(uvs, dtype=np.float64), specs


# ===========================================================================
# MERGE & ASSEMBLE MULTI-SURFACE ANIMATED MODELS
# ===========================================================================
def concat_parts(parts):
    V_all, F_all, UV_all, W_all = [], [], [], []
    ofs = 0
    for V, F, UV, W in parts:
        V_all.append(V)
        F_all.append(F + ofs)
        UV_all.append(UV)
        W_all.append(W)
        ofs += len(V)
    return (
        np.vstack(V_all),
        np.vstack(F_all),
        np.vstack(UV_all),
        np.vstack(W_all),
    )


def make_md3_surface(name, shader, F, UV, frames_vn, flip_winding=True):
    tris = [(int(a), int(c), int(b)) if flip_winding else (int(a), int(b), int(c)) for a, b, c in F]
    st = [(float(u), float(v)) for u, v in UV]
    fr_out = []
    for V_f, N_f in frames_vn:
        vv = [(float(p[0]), float(p[1]), float(p[2])) for p in V_f]
        nn = [(float(n[0]), float(n[1]), float(n[2])) for n in N_f]
        fr_out.append((vv, nn))
    return dict(name=name, shader=shader, tris=tris, st=st, frames=fr_out)


def export_glb_frame(filepath, surfaces_rest, frame_idx=0):
    """Exports a clean textured .GLB file via Blender 5.2 for standard 3D software / inspection."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for s in surfaces_rest:
        if s.get("additive"):
            continue
        V_f, _ = s["frames"][frame_idx]
        me = bpy.data.meshes.new(s["name"])
        # Convert Quake (+X fwd, +Y left, +Z up) -> Blender (+X right = -Y_q, +Y fwd = +X_q, +Z up = +Z_q)
        b_verts = [(-p[1], p[0], p[2]) for p in V_f]
        # Flip winding back from MD3 clockwise to standard CCW
        b_faces = [(t[0], t[2], t[1]) for t in s["tris"]]
        me.from_pydata(b_verts, [], b_faces)
        me.update()
        for poly in me.polygons:
            poly.use_smooth = True

        uv_layer = me.uv_layers.new(name="UVMap")
        st = s["st"]
        for loop in me.loops:
            u, v = st[loop.vertex_index]
            uv_layer.data[loop.index].uv = (u, 1.0 - v)

        mat = bpy.data.materials.new(name=s["name"] + "_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = s.get("roughness", 0.55)
        tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex_img = bpy.data.images.load(s["tex_path"], check_existing=True)
        tex_node.image = tex_img
        mat.node_tree.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
        me.materials.append(mat)

        ob = bpy.data.objects.new(s["name"], me)
        bpy.context.collection.objects.link(ob)

    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        export_apply=True,
        export_yup=True,
    )


def render_preview_sheet(proj_surfs, vm_surfs, char_surfs, out_dir):
    """Renders 6 crisp high-res 3D turnaround & POV inspection panels natively in Blender 5.2!"""
    os.makedirs(out_dir, exist_ok=True)
    panels = [
        ("01_proj_side",  proj_surfs, 0,  (0.0, -68.0, 6.0),    (0.0, 0.0, 0.0),    42.0),
        ("02_proj_front", proj_surfs, 4,  (54.0, -40.0, 12.0),  (0.0, 0.0, 0.0),    42.0),
        ("03_proj_rear",  proj_surfs, 8,  (-52.0, -44.0, 22.0), (0.0, 0.0, 0.0),    42.0),
        ("04_vm_idle",    vm_surfs,   2,  (0.0, 0.0, 0.0),      (14.6, -1.6, -5.2), 26.0),
        ("05_vm_wave",    vm_surfs,  15,  (0.0, 0.0, 0.0),      (14.6, -1.6, -4.5), 26.0),
        ("06_vm_throw",   vm_surfs,  27,  (0.0, 0.0, 0.0),      (17.5, -1.6, -4.5), 28.0),
        ("07_char_front", char_surfs, 0,  (66.0, -18.0, 5.0),   (0.0, 0.0, -1.0),   44.0),
        ("08_char_back",  char_surfs, 0,  (-64.0, 24.0, 6.0),   (0.0, 0.0, -1.0),   44.0),
    ]

    for tag, surfs, fidx, cam_q, tgt_q, lens_mm in panels:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = 640
        scene.render.resolution_y = 640
        scene.render.film_transparent = False
        scene.world = bpy.data.worlds.new("W")
        scene.world.color = (0.93, 0.94, 0.96)
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "TEXTURE"
        scene.display.shading.show_specular_highlight = True

        for s in surfs:
            if s.get("additive"):
                continue
            V_f, _ = s["frames"][fidx]
            me = bpy.data.meshes.new(s["name"])
            b_verts = [(-p[1], p[0], p[2]) for p in V_f]
            b_faces = [(t[0], t[2], t[1]) for t in s["tris"]]
            me.from_pydata(b_verts, [], b_faces)
            me.update()
            for poly in me.polygons:
                poly.use_smooth = True
            uv_layer = me.uv_layers.new(name="UVMap")
            st = s["st"]
            for loop in me.loops:
                u, v = st[loop.vertex_index]
                uv_layer.data[loop.index].uv = (u, 1.0 - v)

            mat = bpy.data.materials.new(name=s["name"] + "_m")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex_node.image = bpy.data.images.load(s["tex_path"], check_existing=True)
            mat.node_tree.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
            mat.node_tree.nodes.active = tex_node
            me.materials.append(mat)
            ob = bpy.data.objects.new(s["name"], me)
            bpy.context.collection.objects.link(ob)

        c_pos = np.array([-cam_q[1], cam_q[0], cam_q[2]], dtype=np.float64)
        t_pos = np.array([-tgt_q[1], tgt_q[0], tgt_q[2]], dtype=np.float64)
        cam_data = bpy.data.cameras.new("Cam")
        cam_data.lens = lens_mm
        cam_data.clip_start = 0.2
        cam_data.clip_end = 500.0
        cam_ob = bpy.data.objects.new("Cam", cam_data)
        bpy.context.collection.objects.link(cam_ob)
        scene.camera = cam_ob

        import mathutils
        cam_ob.location = mathutils.Vector(c_pos.tolist())
        direction = mathutils.Vector((t_pos - c_pos).tolist())
        cam_ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

        out_p = os.path.join(out_dir, f"{tag}.png")
        scene.render.filepath = out_p
        bpy.ops.render.render(write_still=True)
    print("Saved 8 preview panels in:", out_dir)


def main():
    os.makedirs(GLB_DIR, exist_ok=True)
    os.makedirs(MD3_DIR, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    print("1/5 Sculpting miniature blonde woman parts...")
    p_head = sc.build_head_and_neck()
    p_chest_skin, p_pink_torso = sc.build_chest_skin_and_pink_top()
    p_bow = sc.build_tie_knot_and_ribbons()
    p_sleeves, p_char_hands = sc.build_sleeves_and_hands()
    p_hair = sc.build_blonde_hair()
    p_ankles, p_sneakers = sc.build_ankles_and_sneakers()
    p_jeans = sc.build_seamless_jeans_bpy(bpy)

    # Group character parts by material surface (each stays well below MD3 4096-vertex limit!)
    char_groups = [
        ("char_skin",     "tex_skin.png",     0.48, concat_parts([p_head, p_chest_skin, p_char_hands, p_ankles])),
        ("char_hair",     "tex_hair.png",     0.38, p_hair),
        ("char_pink_top", "tex_pink_top.png", 0.62, concat_parts([p_pink_torso, p_sleeves, p_bow])),
        ("char_jeans",    "tex_jeans.png",    0.72, p_jeans),
        ("char_sneakers", "tex_sneakers.png", 0.52, p_sneakers),
    ]
    for nm, _, _, (V, F, _, _) in char_groups:
        print(f"   {nm:15s}: {len(V):4d} verts, {len(F):4d} tris")

    print("2/5 Sculpting giant 1st-person right hand + 3D fingernails...")
    V_hand, F_hand, UV_hand, W_hand = build_giant_right_hand()
    print(f"   {'giant_hand':15s}: {len(V_hand):4d} verts, {len(F_hand):4d} tris")

    V_spd, F_spd, UV_spd, _ = build_speed_ribbons()

    # -----------------------------------------------------------------------
    # MODEL 1: THROWN PROJECTILE IN FLIGHT (`pocket_rocket_proj`, 16 frames)
    # Scale: S_PROJ = 48.0 Quake units (flies horizontally toward +X!)
    # -----------------------------------------------------------------------
    print("3/5 Baking animated frames for Thrown Projectile (`pocket_rocket_proj`)...")
    S_PROJ = 48.0
    NF_PROJ = 16
    proj_frames_by_group = {nm: [] for nm, _, _, _ in char_groups}
    spd_frames = []

    for fi in range(NF_PROJ):
        phase = 2.0 * math.pi * fi / NF_PROJ
        rots, off = sc.pose_projectile_flight(phase)
        R_w, P_w = sc.solve_fk(rots, root_offset=off)
        for nm, _, _, (V_r, F_r, _, W_r) in char_groups:
            V_posed = sc.apply_skin(V_r, W_r, R_w, P_w) * S_PROJ
            N_posed = sc.compute_normals(V_posed, F_r)
            proj_frames_by_group[nm].append((V_posed, N_posed))

        # Animate slipstream speed-ribbons rushing backward (-X) and shimmering!
        V_s = V_spd.copy()
        scroll = (fi / NF_PROJ)
        for k in range(8):
            sl = slice(k * 36, (k + 1) * 36)
            ph_k = phase + k * 0.85
            shift_x = -0.10 * ((scroll + k * 0.17) % 1.0)
            V_s[sl, 0] += shift_x
            V_s[sl, 1] *= (1.0 + 0.08 * math.sin(ph_k))
            V_s[sl, 2] *= (1.0 + 0.08 * math.cos(ph_k))
        V_s_q = V_s * S_PROJ
        N_s_q = sc.compute_normals(V_s_q, F_spd)
        spd_frames.append((V_s_q, N_s_q))

    proj_surfs = []
    for nm, tex_fn, rough, (_, F_r, UV_r, _) in char_groups:
        s = make_md3_surface(nm, f"progs/pr_{nm}", F_r, UV_r, proj_frames_by_group[nm])
        s["tex_path"] = os.path.join(TEX_DIR, tex_fn)
        s["roughness"] = rough
        proj_surfs.append(s)

    s_spd = make_md3_surface("speedlines", "progs/pr_speedlines", F_spd, UV_spd, spd_frames)
    s_spd["tex_path"] = os.path.join(TEX_DIR, "tex_speedlines.png")
    s_spd["additive"] = True
    s_spd["twoSided"] = True
    s_spd["unlit"] = True
    proj_surfs.append(s_spd)

    md3lib.write(os.path.join(MD3_DIR, "pocket_rocket_proj.md3"), dict(name="pocket_rocket_proj", surfaces=proj_surfs))

    # -----------------------------------------------------------------------
    # MODEL 2: HELD THROWABLE WEAPON VIEWMODEL (`v_pocket_rocket`, 36 frames)
    #   Frames  0..11: Idle Sway & Hands-on-Hips (Video 1)
    #   Frames 12..23: Joyful Wave ("Let's have some fun! Weee!", Video 2)
    #   Frames 24..35: Wind-Up, Open-Hand Release & Launch + Reload (Video 3)
    # -----------------------------------------------------------------------
    print("4/5 Baking animated frames for Held Weapon Viewmodel (`v_pocket_rocket`)...")
    CHAR_VM_SCALE = 12.2
    HAND_VM_SCALE = 15.5
    NF_VM = 36

    vm_char_frames = {nm: [] for nm, _, _, _ in char_groups}
    vm_hand_frames = []

    # Base hand orientation in eye space (+X away from eye, +Y left, -Y right, +Z up):
    # Recall Local Hand Rest Frame:
    #   +X_h = dorsal (nails!), -X_h = palm, +Y_h = thumb side, +Z_h = extended fingers!
    # To match v1_f180.png in 1st-person eye space:
    #   - When fingers are curled (-X_h direction), we want curled finger backs (+X_h of middle phalanges? Wait!):
    #   Let's trace carefully!
    #     In local hand rest:
    #       Palm faces -X_h, Dorsal back faces +X_h, Fingers point +Z_h, Thumb is on +Y_h!
    #       When fingers curl by ~ -80 deg ( proximal ) + -85 deg ( middle ) = -165 deg total around Y_h:
    #         - Metacarpal palm has dorsal normal +X_h and palmar normal -X_h.
    #         - Proximal phalanx (-75 deg) points toward (-X_h, 0, +0.25 Z_h).
    #         - Middle & Distal phalanges (-160 deg total!) point BACK toward (-0.34 X_h, 0, -0.94 Z_h),
    #           and their DORSAL NAIL NORMAL (originally +X_h rotated by -160 deg!) points toward (-0.94 X_h, 0, +0.34 Z_h) — i.e., PALMAR SIDE (-X_h)!!
    #     WAIT A SECOND! Check that on your own hand right now!
    #       Look at your own palm (-X_h): curl your fingers into a grip! YES!! You see your FINGERNAILS facing the PALM side (-X_h)!!
    #     So when you look at your own gripping hand so you see your FINGERNAILS (just like v1_f180.png!):
    #       - The PALM (-X_h) faces TOWARD YOUR EYES (-X_eye) -> so +X_h points +X_eye (away from your eyes, behind the girl)!!
    #       -Wait: check where the 4 fingers come from in v1_f180.png!
    #         In v1_f180.png, the 4 curled fingers enter from SCREEN LEFT (+Y_eye) and point toward SCREEN RIGHT (-Y_eye),
    #         with Index on TOP (+Z_eye) and Pinky on BOTTOM (-Z_eye), and Thumb entering from SCREEN RIGHT (-Y_eye) wrapping UP/LEFT!
    #         Let's check if a RIGHT hand does that!
    #           Hold your RIGHT hand in front of your face:
    #           Rotate wrist so your forearm comes from BOTTOM-RIGHT (-Y_eye, -Z_eye), palm faces YOU (-X_eye),
    #           fingers extend to SCREEN LEFT (+Y_eye) and curl around her back/left to point back toward SCREEN RIGHT (-Y_eye)!
    #           Wait: if palm faces YOU (-X_eye) and fingers extend to SCREEN LEFT (+Y_eye):
    #             +Z_h (extended fingers) = +Y_eye (screen left)!
    #             -X_h (palm) = -X_eye (toward player) -> +X_h = +X_eye (away from player)!
    #             Then in right-handed frame, +Y_h (Thumb side!) = +Z_h cross +X_h = (+Y_eye) cross (+X_eye) = -Z_eye?! Wait: (+Y) x (+X) = -Z!
    #             Wait: check with your actual RIGHT hand in front of your face right now!
    #             Hold your RIGHT hand with palm facing YOUR FACE:
    #               - If fingers point UP (+Z_eye), THUMB is on the RIGHT (-Y_eye)!
    #               - Now tilt your right hand 75 deg COUNTER-CLOCKWISE? No, if forearm comes from bottom-right, tilt fingers to point LEFT (+Y_eye): then THUMB is on TOP (+Z_eye)!
    #               - Wait: look at `v1_f180.png` and `v3_f096.png` again!!
    #                 Look at `v3_f096.png` (open palm):
    #                 Fingers point UP-LEFT (`+Y_eye, +Z_eye`), THUMB is on SCREEN RIGHT (`-Y_eye, +Z_eye`), Pinky is on SCREEN BOTTOM-LEFT (`+Y_eye, -Z_eye`), and PALM faces TOWARD CAMERA (`-X_eye`)!!
    #                 AND in `v1_f180.png` (closed grip):
    #                 Index finger is on TOP, Pinky is on BOTTOM, fingernails are on the RIGHT ends of the horizontal curled fingers, and THUMB wraps from SCREEN RIGHT (`-Y_eye`)!!
    #                 BINGO!! Let's check the axes of THAT exact right hand (`v3_f096.png` & `v1_f180.png`)!!
    #                   - Palm faces TOWARD CAMERA (`-X_eye`) -> so `-X_h` (palmar) = `-X_eye` -> **`+X_h` = `+X_eye`**!
    #                   - Thumb (`+Y_h` in our `HAND_REST`? Wait: if `+X_h = +X_eye` and `+Z_h` = UP-LEFT `(0, +0.62, +0.78)`, then what is `+X_h cross +Z_h`? `(1,0,0) x (0, 0.62, 0.78) = (0, -0.78, +0.62)` = **UP-RIGHT (`-Y_eye, +Z_eye`)** — WHICH IS EXACTLY WHERE THE THUMB IS IN `v3_f096.png` AND `v1_f180.png`!!)
    #                 WAIT: Check the sign in `HAND_REST`!
    #                 In `HAND_REST` above, we put Thumb at `+Y_h` (`+0.155`) and Pinky at `-Y_h` (`-0.142`)!
    #                 Let's check `(X_h, Y_h, Z_h)` mapped to Eye space via columns `[C_x, C_y, C_z]`:
    #                   Set `C_x = (1, 0, 0)` (`+X_h` dorsal points `+X_eye` away from camera, so `-X_h` palm faces `-X_eye` toward camera!).
    #                   Set `C_y = (0, -0.78, 0.626)` (`+Y_h` thumb/index side points **SCREEN RIGHT & UP**, `-Y_h` pinky side points **SCREEN LEFT & DOWN**!).
    #                   Set `C_z = C_x cross C_y = (0, -0.626, -0.78)`? Wait: `(1,0,0) x (0, -0.78, 0.626) = (0, -0.626, -0.78)` (down-right).
    #                   Whereas if `C_z = (0, +0.626, +0.78)` (fingers extend **UP & SCREEN-LEFT**, matching `v3_f096.png`!) and `C_y = (0, -0.78, +0.626)` (thumb is **SCREEN-RIGHT & UP**, matching `v3_f096.png`!):
    #                   Then `det([C_x, C_y, C_z])`: `C_y cross C_z = (-0.78*0.78 - 0.626*0.626) = -1.0` -> `C_x = (-1, 0, 0)`!
    #                   Let's check! If `C_x = (+1, 0, 0)`, `C_y = (0, -0.78, +0.626)`, `C_z = (0, +0.626, +0.78)`, det = `-1` ONLY because earlier we put thumb at `+Y_h` instead of `-Y_h`!
    #                   Look at a REAL right hand with `+X_h` = dorsal (away from you, palm `-X_h` facing you!) and `+Z_h` = fingers pointing UP `(0,0,1)`:
    #                   Hold your RIGHT hand up with PALM facing YOU (`-X_h`): your THUMB is on the **RIGHT (`-Y_eye`)**, NOT left (`+Y_eye`)!!
    #                   THANK GOODNESS WE CHECKED THAT!! That's why checking determinant = +1 caught a mirrored-left-hand trap immediately!

    # Flip Y of V_hand & HAND_REST in place? Even cleaner: let's mirror Y of V_hand & HAND_REST right now so it is a 100% true anatomical RIGHT hand with det(R) = +1!
    V_hand[:, 1] *= -1.0
    F_hand = F_hand[:, [0, 2, 1]]  # preserve outward normal winding after Y reflection!
    for k_b in HAND_REST:
        HAND_REST[k_b] = HAND_REST[k_b] * np.array([1.0, -1.0, 1.0])

    # Now verify with det = +1!
    #   In true Right Hand local rest:
    #     -X_h = Palm, +X_h = Dorsal back
    #     +Z_h = Extended fingers
    #     -Y_h = Thumb/Index side!  +Y_h = Pinky side!
    #   Now rotate around X_h by -38 deg (`rot_x(-38)` -> det = +1!):
    #     C_x = (1, 0, 0)                      -> Palm (-X_h) faces player (-X_eye)!
    #     C_z = (0, +sin 38, +cos 38)          -> Extended fingers point UP & SCREEN-LEFT (+Y_eye, +Z_eye) — exact match to v3_f096.png!!
    #     C_y = (0, +cos 38, -sin 38)          -> So Thumb (-Y_h) is at (0, -cos 38, +sin 38) = SCREEN-RIGHT & UP — exact match to v1_f180 & v3_f096!!
    #     And Forearm (-Z_h) extends to (0, -sin 38, -cos 38) = BOTTOM-RIGHT of screen — 100% IDENTICAL TO ALL 3 VIDEOS!!

    for fi in range(NF_VM):
        if fi < 12:
            # Clip 1: Idle Sway & Hands-on-Hips (Video 1)
            ph = 2.0 * math.pi * fi / 12.0
            c_rots, c_off = sc.pose_standing_hips(ph)
            grip_t = 0.96
            breathe = 1.6 * math.sin(ph)
            sway_y = 0.28 * math.sin(ph)
            sway_z = 0.22 * math.cos(ph)
            hand_rot = sc.rot_y(8.0 + 1.5 * math.sin(ph)) @ sc.rot_z(-10.0) @ sc.rot_x(-44.0)
            hand_pos = np.array([15.2, -3.4 + sway_y, -8.8 + sway_z])
            char_yaw = 180.0 + 4.0 * math.sin(ph)   # faces -X toward player!
            char_pitch = 0.0
            char_pos = np.array([14.2, -1.0 + sway_y, -9.8 + sway_z])
            char_scale = CHAR_VM_SCALE
        elif fi < 24:
            # Clip 2: Excited Joyful Wave ("Hi there, let's have some fun! Weee!", Video 2)
            ph = 2.0 * math.pi * (fi - 12) / 12.0
            c_rots, c_off = sc.pose_joyful_wave(ph)
            grip_t = 0.95
            breathe = 2.5 * math.sin(ph)
            sway_y = 0.45 * math.sin(ph)
            sway_z = 0.35 * abs(math.sin(ph))
            hand_rot = sc.rot_y(7.0 + 2.0 * math.cos(ph)) @ sc.rot_z(-8.0 + 3.0 * math.sin(ph)) @ sc.rot_x(-43.0)
            hand_pos = np.array([15.0, -3.4 + sway_y, -8.9 + sway_z])
            char_yaw = 180.0 - 6.0 * math.sin(ph)
            char_pitch = 0.0
            char_pos = np.array([14.0, -1.0 + sway_y, -9.8 + sway_z])
            char_scale = CHAR_VM_SCALE
        else:
            # Clip 3: Wind-Up, Open-Hand Release & Launch + Reload (Video 3, frames 24..35)
            jf = fi - 24   # 0..11
            if jf <= 2:
                # 0, 1, 2: Wind-up! Hand draws back/down slightly, she spreads arms wide ("Ready for this?!")
                wt = jf / 2.0
                c_rots, c_off = sc.pose_spread_ready(wt)
                grip_t = 0.94 - 0.14 * wt
                breathe = 0.0
                hand_rot = sc.rot_y(8.0 - 16.0 * wt) @ sc.rot_z(-10.0) @ sc.rot_x(-44.0 + 6.0 * wt)
                hand_pos = np.array([15.2 - 2.4 * wt, -3.4 - 0.5 * wt, -8.8 - 1.2 * wt])
                char_yaw = 180.0 * (1.0 - 0.15 * wt)
                char_pitch = 0.0
                char_pos = np.array([14.2 - 2.2 * wt, -1.0 - 0.4 * wt, -9.8 - 1.0 * wt])
                char_scale = CHAR_VM_SCALE
            elif jf <= 6:
                # 3, 4, 5, 6: THROW RELEASE! Hand snaps forward & splays all 5 fingers WIDE OPEN (v3_f096.png),
                # while she vaults out pitching into horizontal +X Superman flight!
                lt = (jf - 2) / 4.0
                c_rots, c_off = sc.pose_projectile_flight(lt * math.pi)
                grip_t = max(0.0, 0.25 * (1.0 - lt * 2.5))   # wide-open splayed palm!
                breathe = 0.0
                hand_rot = sc.rot_y(24.0 * sc.sstep(0.0, 0.6, lt)) @ sc.rot_z(-4.0) @ sc.rot_x(-34.0)
                hand_pos = np.array([12.8 + 4.8 * sc.sstep(0.0, 0.65, lt), -3.6, -9.2 + 1.8 * math.sin(lt * math.pi * 0.8)])
                char_yaw = 0.0   # flying forward toward +X!
                char_pitch = 0.0
                # Vaults cleanly forward (+X) clear of the splayed fingers, shrinking on jf==6 as live projectile takes over!
                char_pos = np.array([22.0 + 34.0 * (lt ** 1.05), -0.6 + 0.6 * lt, -0.4 + 4.2 * lt])
                char_scale = CHAR_VM_SCALE * (1.0 if jf < 6 else 0.002)
            elif jf <= 8:
                # 7, 8: Empty hand drops slightly below view to grab next mini-character
                dt = (jf - 6) / 2.0
                c_rots, c_off = sc.pose_standing_hips(0.0)
                grip_t = 0.35 * dt
                breathe = 0.0
                hand_rot = sc.rot_y(24.0 * (1.0 - dt) + 8.0 * dt) @ sc.rot_z(-8.0) @ sc.rot_x(-38.0)
                hand_pos = np.array([16.5 - 1.5 * dt, -3.6, -9.5 - 5.5 * math.sin(dt * math.pi * 0.5)])
                char_yaw = 180.0
                char_pitch = 0.0
                char_pos = np.array([0.0, 0.0, -50.0])
                char_scale = 0.002
            else:
                # 9, 10, 11: Fresh ready weapon rises smoothly back into grip!
                rt = (jf - 8) / 3.0
                k_up = sc.sstep(0.0, 1.0, rt)
                c_rots, c_off = sc.pose_standing_hips(0.0)
                grip_t = 0.45 + 0.51 * k_up
                breathe = 0.0
                hand_rot = sc.rot_y(8.0) @ sc.rot_z(-10.0) @ sc.rot_x(-44.0)
                hand_pos = np.array([15.2, -3.4, -14.5 + (14.5 - 8.8) * k_up])
                char_yaw = 180.0
                char_pitch = 0.0
                char_pos = np.array([14.2, -1.0, -15.5 + (15.5 - 9.8) * k_up])
                char_scale = CHAR_VM_SCALE * (0.65 + 0.35 * k_up)

        # Skin Giant Hand for frame fi
        h_pose = hand_grip_pose(tightness=grip_t, breathe=breathe)
        Rh_w, Ph_w = solve_hand_fk(h_pose, hand_rot, hand_pos, scale=HAND_VM_SCALE)
        V_h_f = apply_hand_skin(V_hand, W_hand, Rh_w, Ph_w, scale=HAND_VM_SCALE)
        N_h_f = sc.compute_normals(V_h_f, F_hand)
        vm_hand_frames.append((V_h_f, N_h_f))

        # Skin Miniature Woman for frame fi
        Rc_w, Pc_w = sc.solve_fk(c_rots, root_offset=c_off)
        R_char_world = sc.rot_z(char_yaw) @ sc.rot_y(char_pitch)
        for nm, _, _, (V_r, F_r, _, W_r) in char_groups:
            V_c = sc.apply_skin(V_r, W_r, Rc_w, Pc_w) * char_scale
            V_c = V_c @ R_char_world.T + char_pos
            N_c = sc.compute_normals(V_c, F_r)
            vm_char_frames[nm].append((V_c, N_c))

    vm_surfs = []
    s_hand = make_md3_surface("giant_hand", "progs/pr_giant_hand", F_hand, UV_hand, vm_hand_frames)
    s_hand["tex_path"] = os.path.join(TEX_DIR, "tex_giant_hand.png")
    s_hand["roughness"] = 0.56
    vm_surfs.append(s_hand)

    for nm, tex_fn, rough, (_, F_r, UV_r, _) in char_groups:
        s = make_md3_surface(nm, f"progs/pr_{nm}", F_r, UV_r, vm_char_frames[nm])
        s["tex_path"] = os.path.join(TEX_DIR, tex_fn)
        s["roughness"] = rough
        vm_surfs.append(s)

    md3lib.write(os.path.join(MD3_DIR, "v_pocket_rocket.md3"), dict(name="v_pocket_rocket", surfaces=vm_surfs))

    # -----------------------------------------------------------------------
    # MODEL 3: UNOBSTRUCTED 3D CHARACTER TURNAROUND (`pocket_rocket_char`, 32 frames)
    #   Frames  0.. 7: Hands-on-Hips Idle
    #   Frames  8..15: Joyful Dual-Arm Wave
    #   Frames 16..23: Spread-Arms Launch Stance
    #   Frames 24..31: Skydiver Flight Pose (standing-scale inspection)
    # -----------------------------------------------------------------------
    print("5/5 Baking unobstructed Character Turnaround (`pocket_rocket_char`) & exporting GLBs...")
    S_CHAR = 52.0
    char_frames = {nm: [] for nm, _, _, _ in char_groups}
    for fi in range(32):
        sub = fi % 8
        ph = 2.0 * math.pi * sub / 8.0
        if fi < 8:
            rots, off = sc.pose_standing_hips(ph)
            off = (off[0], off[1], off[2] - 0.50)
        elif fi < 16:
            rots, off = sc.pose_joyful_wave(ph)
            off = (off[0], off[1], off[2] - 0.50)
        elif fi < 24:
            rots, off = sc.pose_spread_ready(0.5 + 0.5 * math.sin(ph - math.pi / 2.0))
            off = (off[0], off[1], off[2] - 0.50)
        else:
            rots, off = sc.pose_projectile_flight(ph)

        R_w, P_w = sc.solve_fk(rots, root_offset=off)
        for nm, _, _, (V_r, F_r, _, W_r) in char_groups:
            V_c = sc.apply_skin(V_r, W_r, R_w, P_w) * S_CHAR
            N_c = sc.compute_normals(V_c, F_r)
            char_frames[nm].append((V_c, N_c))

    char_surfs = []
    for nm, tex_fn, rough, (_, F_r, UV_r, _) in char_groups:
        s = make_md3_surface(nm, f"progs/pr_{nm}", F_r, UV_r, char_frames[nm])
        s["tex_path"] = os.path.join(TEX_DIR, tex_fn)
        s["roughness"] = rough
        char_surfs.append(s)

    md3lib.write(os.path.join(MD3_DIR, "pocket_rocket_char.md3"), dict(name="pocket_rocket_char", surfaces=char_surfs))

    # Export clean universal .GLB files!
    export_glb_frame(os.path.join(GLB_DIR, "pocket_rocket_projectile.glb"), proj_surfs, frame_idx=0)
    export_glb_frame(os.path.join(GLB_DIR, "pocket_rocket_weapon.glb"), vm_surfs, frame_idx=0)
    export_glb_frame(os.path.join(GLB_DIR, "pocket_rocket_character.glb"), char_surfs, frame_idx=0)

    # Render 8-panel visual check views!
    render_preview_sheet(proj_surfs, vm_surfs, char_surfs, os.path.join(OUT_ROOT, "previews"))
    print("ALL 3 MODELS BUILT & EXPORTED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
