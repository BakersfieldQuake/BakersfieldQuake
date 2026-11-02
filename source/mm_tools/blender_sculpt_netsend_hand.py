"""Blender 5.2 anatomical human right hand sculptor, Cycles SSS + micro-bump baker,
60-frame armature rigger, and preview renderer for `progs/v_netsend.md3` ('LOL.BAT' gun).

Invoked headless by `build_netsend_vm_remake.py`:
    blender.exe --background --python blender_sculpt_netsend_hand.py -- <strip.png> <out_dir> <out_npz>
"""
import math
import os
import sys

import bmesh
import bpy
import mathutils
import numpy as np


def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0 + 1e-12)))
    return t * t * (3.0 - 2.0 * t)


def smoother(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def sstep_np(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ==============================================================================
# 1. ANATOMICAL ADULT MALE RIGHT HAND & MUSCULAR FOREARM (REST FRAME)
#    Origin (0,0,0) = Wrist center
#    +Z = Distal (fingers), -Z = Proximal (forearm to elbow)
#    -X = PALMAR (volar),   +X = DORSAL (back of hand & fingernails)
#    -Y = RADIAL (thumb),   +Y = ULNAR  (pinky)
#    Verified right-handed: (+X dorsal) x (+Y ulnar) = (+Z distal).
# ==============================================================================
HAND_JOINTS = {
    "forearm": np.array([ 0.012,  0.022, -1.620]),
    "wrist":   np.array([ 0.000,  0.000,  0.000]),
    "palm":    np.array([ 0.002, -0.004,  0.180]),
    # Opposable Thumb (natural 40 deg radial-palmar opposition)
    "th_1":    np.array([-0.044, -0.156,  0.118]),
    "th_2":    np.array([-0.082, -0.288,  0.258]),
    "th_3":    np.array([-0.106, -0.380,  0.382]),
    "th_tip":  np.array([-0.122, -0.452,  0.492]),
    # Index Finger (gentle natural palmar arch & radial fan)
    "ix_1":    np.array([ 0.004, -0.156,  0.452]),
    "ix_2":    np.array([-0.004, -0.182,  0.648]),
    "ix_3":    np.array([-0.016, -0.198,  0.786]),
    "ix_tip":  np.array([-0.028, -0.212,  0.906]),
    # Middle Finger (longest, central arch peak)
    "md_1":    np.array([ 0.010, -0.048,  0.474]),
    "md_2":    np.array([ 0.002, -0.055,  0.690]),
    "md_3":    np.array([-0.012, -0.060,  0.838]),
    "md_tip":  np.array([-0.026, -0.064,  0.964]),
    # Ring Finger
    "rg_1":    np.array([ 0.004,  0.056,  0.448]),
    "rg_2":    np.array([-0.005,  0.073,  0.646]),
    "rg_3":    np.array([-0.018,  0.085,  0.784]),
    "rg_tip":  np.array([-0.032,  0.095,  0.902]),
    # Pinky Finger (dropped metacarpal arch)
    "pk_1":    np.array([-0.008,  0.150,  0.398]),
    "pk_2":    np.array([-0.018,  0.184,  0.552]),
    "pk_3":    np.array([-0.030,  0.208,  0.662]),
    "pk_tip":  np.array([-0.042,  0.228,  0.764]),
}


def build_anatomical_hand_bmesh():
    """Constructs a 100% pure-quad, watertight manifold cage of an adult male right hand & forearm."""
    bm = bmesh.new()

    # Smooth uniform Y distribution for stations 0..8 (eliminates longitudinal plank creases!)
    y_even = np.linspace(-0.208, 0.202, 8, dtype=np.float64)
    # Station 9 gathers smoothly into 4 finger columns (0,2,4,6) + 3 narrow interdigital webs (1,3,5)
    y_mcp = np.array([-0.214, -0.122, -0.098, -0.006, 0.018, 0.104, 0.126, 0.206], dtype=np.float64)
    x_norm = np.array([-1.0, 0.0, 1.0], dtype=np.float64)

    perim_ij = (
        [(iy, 2) for iy in range(0, 8)] +
        [(7, 1)] +
        [(iy, 0) for iy in range(7, -1, -1)] +
        [(0, 1)]
    )

    # 10 axial stations from upper muscular forearm (-1.62) to MCP knuckle arch (+0.440)
    stations = [
        (-1.620, 1.14, 0.182,  0.024,  0.010, 0.96, 0.00),  # 0: muscular upper forearm (well off-screen!)
        (-1.120, 1.09, 0.170,  0.018,  0.008, 0.94, 0.00),  # 1: brachioradialis / extensor belly
        (-0.660, 0.96, 0.148,  0.012,  0.005, 0.89, 0.00),  # 2: mid forearm taper
        (-0.260, 0.83, 0.120,  0.005,  0.002, 0.82, 0.00),  # 3: distal forearm
        (-0.040, 0.78, 0.104,  0.002,  0.000, 0.74, 0.00),  # 4: wrist crease + ulnar styloid process
        ( 0.048, 0.83, 0.108, -0.002, -0.005, 0.58, 0.05),  # 5: carpal heel (thumb socket bottom)
        ( 0.158, 0.95, 0.116, -0.012, -0.010, 0.44, 0.12),  # 6: thumb socket mid / meaty thenar swell
        ( 0.285, 1.01, 0.108, -0.010, -0.006, 0.34, 0.25),  # 7: thumb socket top (diagonal thumb-index web!)
        ( 0.368, 1.03, 0.095, -0.004, -0.002, 0.26, 0.55),  # 8: distal palm & metacarpal heads
        ( 0.440, 1.01, 0.082,  0.000,  0.000, 0.18, 1.00),  # 9: MCP knuckle arch & finger sockets
    ]

    def eval_station_grid(st_idx):
        z0, w_sc, h_thk, cy, cx, rnd, mcp_blend = stations[st_idx]
        y_arr = (1.0 - mcp_blend) * y_even + mcp_blend * y_mcp
        grid_pts = np.zeros((8, 3, 3), dtype=np.float64)
        for iy in range(8):
            yn = (y_arr[iy] + 0.003) / 0.206
            for ix in range(3):
                xn = x_norm[ix]
                ang = math.atan2(yn, xn + 1e-9)
                r_box_y = y_arr[iy] * w_sc
                r_box_x = xn * h_thk
                ell_y = 0.205 * w_sc * math.sin(ang) if (ix in (0, 2) or iy in (0, 7)) else r_box_y
                ell_x = h_thk * math.cos(ang) if (ix in (0, 2) or iy in (0, 7)) else r_box_x

                if iy in (0, 7) and ix in (0, 2):
                    r_box_x *= 0.78
                    r_box_y *= 0.95
                elif ix in (0, 2) and iy not in (0, 7):
                    # Smooth transverse dorsal arch (+X) and palmar cup (-X)
                    r_box_x *= (1.0 - 0.12 * (yn * yn))

                x = cx + (1.0 - rnd) * r_box_x + rnd * ell_x
                y = cy + (1.0 - rnd) * r_box_y + rnd * ell_y
                z = z0

                # 1. Ulnar styloid wrist bone prominence (dorsal-ulnar wrist)
                if st_idx in (3, 4) and iy >= 6 and ix >= 1:
                    styl = (1.0 if st_idx == 4 else 0.45) * (0.65 if ix == 1 else 0.90)
                    y += 0.015 * styl
                    x += 0.009 * styl

                # 2. Meaty Thenar thumb-base muscle pad (radial-palmar) + First Dorsal Interosseous web swell!
                if st_idx in (5, 6, 7, 8) and iy <= 3:
                    w_th = {5: 0.55, 6: 1.0, 7: 0.82, 8: 0.35}[st_idx] * max(0.0, 1.0 - iy / 3.3)
                    if ix == 0:
                        x -= 0.042 * w_th  # plump palmar thenar eminence
                    elif ix == 2 and st_idx in (6, 7, 8):
                        x += 0.018 * w_th  # dorsal first-interosseous muscle belly!
                    y -= 0.024 * w_th
                    # Slope radial thumb-web edge diagonally upward at st_idx == 7 so thumb web joins high near index base!
                    if st_idx == 7 and iy <= 1:
                        z += 0.042 * (1.0 - 0.5 * iy)

                # 3. Smooth fleshy Hypothenar muscle pad along outer ulnar palm (no pinky-base pinch!)
                if st_idx in (5, 6, 7, 8, 9) and iy >= 5:
                    w_hy = {5: 0.60, 6: 0.95, 7: 1.0, 8: 0.78, 9: 0.40}[st_idx] * ((iy - 4.3) / 2.7)
                    if ix == 0:
                        x -= 0.026 * w_hy
                    y += 0.014 * w_hy

                # 4. Cupped central palmar hollow
                if st_idx in (7, 8) and 2 <= iy <= 5 and ix == 0:
                    x += 0.019 * (1.0 if st_idx == 7 else 0.72)

                # 5. Gradual curved metacarpal arch (st_idx 7..9 so pinky drops smoothly without pinching!)
                if st_idx >= 7:
                    k_fac = {7: 0.18, 8: 0.52, 9: 1.0}[st_idx]
                    arch_z = 0.026 - 0.020 * ((yn + 0.22) ** 2) * 1.85
                    if iy >= 5:
                        arch_z -= 0.020 * ((iy - 4) / 3.0)
                    z += k_fac * arch_z
                    # Prominent rounded dorsal MCP knuckle domes on finger columns
                    if st_idx == 9 and ix == 2:
                        x += 0.006 if iy in (0, 7) else 0.016

                grid_pts[iy, ix] = (x, y, z)
        return grid_pts

    uv_grp = bm.faces.layers.int.new("uv_grp")
    # UV Groups (7 pure topological disks -> ZERO seams on fingertips, nails, knuckles, or palm!):
    #   0: CAP (off-screen proximal forearm cap)
    #   1: HAND_DORSAL (visible dorsal wrist, back of hand, knuckles, nails & dorsal fingers)
    #   2: HAND_PALMAR (visible volar wrist, palm, thenar/hypothenar & palmar fingers)
    #   3: THUMB_DORSAL (dorsal thumb + thumbnail)
    #   4: THUMB_PALMAR (volar thumb pad & opposition web)
    #   5: FOREARM_DORSAL_PROX (off-screen upper forearm z < -0.66, scaled compactly in UV)
    #   6: FOREARM_PALMAR_PROX (off-screen upper forearm z < -0.66, scaled compactly in UV)

    ring_verts = []
    grid0_bm = [[None] * 3 for _ in range(8)]
    g0 = eval_station_grid(0)
    for iy in range(8):
        for ix in range(3):
            grid0_bm[iy][ix] = bm.verts.new(tuple(g0[iy, ix]))
    for iy in range(7):
        for ix in range(2):
            fc = bm.faces.new((grid0_bm[iy][ix], grid0_bm[iy + 1][ix], grid0_bm[iy + 1][ix + 1], grid0_bm[iy][ix + 1]))
            fc[uv_grp] = 0
    ring_verts.append([grid0_bm[iy][ix] for (iy, ix) in perim_ij])

    for st_i in range(1, 9):
        gp = eval_station_grid(st_i)
        ring_verts.append([bm.verts.new(tuple(gp[iy, ix])) for (iy, ix) in perim_ij])

    grid9_bm = [[None] * 3 for _ in range(8)]
    g9 = eval_station_grid(9)
    # Sloped natatory interdigital webs: palmar web fold sits high/distally, dorsal valley slopes back between knuckles!
    for iy in (1, 2, 3, 4, 5, 6):
        g9[iy, 2, 2] -= 0.026
        g9[iy, 2, 0] -= 0.012
        g9[iy, 0, 2] += 0.014
    for iy in range(8):
        for ix in range(3):
            grid9_bm[iy][ix] = bm.verts.new(tuple(g9[iy, ix]))
    ring_verts.append([grid9_bm[iy][ix] for (iy, ix) in perim_ij])

    dors_k_set = {0, 1, 2, 3, 4, 5, 6, 7, 17}
    for st_i in range(9):
        rA, rB = ring_verts[st_i], ring_verts[st_i + 1]
        is_prox = (st_i < 2)  # z in [-1.62 .. -0.66] is off-screen upper forearm!
        for k in range(18):
            k1 = (k + 1) % 18
            if st_i in (5, 6) and k in (16, 17):
                continue  # 2x2 radial thumb socket opening
            fw = bm.faces.new((rA[k], rA[k1], rB[k1], rB[k]))
            if k in dors_k_set:
                fw[uv_grp] = 5 if is_prox else 1
            else:
                fw[uv_grp] = 6 if is_prox else 2

    # Cap the 3 sloped interdigital web clefts
    for col_cleft in (1, 3, 5):
        for ix in range(2):
            fc = bm.faces.new((
                grid9_bm[col_cleft][ix],
                grid9_bm[col_cleft][ix + 1],
                grid9_bm[col_cleft + 1][ix + 1],
                grid9_bm[col_cleft + 1][ix],
            ))
            fc[uv_grp] = 1 if ix == 1 else 2

    # ==========================================================================
    # EXTRUDE 4 ANATOMICAL FINGERS + RECESSED CUTICLES & CONVEX 3D NAILS
    # ==========================================================================
    finger_defs = [
        (0, HAND_JOINTS["ix_1"], HAND_JOINTS["ix_2"], HAND_JOINTS["ix_3"], HAND_JOINTS["ix_tip"], 0.052, 0.056),
        (2, HAND_JOINTS["md_1"], HAND_JOINTS["md_2"], HAND_JOINTS["md_3"], HAND_JOINTS["md_tip"], 0.055, 0.059),
        (4, HAND_JOINTS["rg_1"], HAND_JOINTS["rg_2"], HAND_JOINTS["rg_3"], HAND_JOINTS["rg_tip"], 0.051, 0.055),
        (6, HAND_JOINTS["pk_1"], HAND_JOINTS["pk_2"], HAND_JOINTS["pk_3"], HAND_JOINTS["pk_tip"], 0.044, 0.048),
    ]

    nail_faces_to_inset = []
    local_6 = [
        ( 0.88, -0.78),  # 0: dorsal-radial
        ( 0.88,  0.78),  # 1: dorsal-ulnar
        ( 0.02,  1.06),  # 2: mid-ulnar
        (-0.92,  0.76),  # 3: palmar-ulnar
        (-0.92, -0.76),  # 4: palmar-radial
        ( 0.02, -1.06),  # 5: mid-radial
    ]

    for col, J1, J2, J3, Jtip, rx0, ry0 in finger_defs:
        sock_ring = [
            grid9_bm[col][2],
            grid9_bm[col + 1][2],
            grid9_bm[col + 1][1],
            grid9_bm[col + 1][0],
            grid9_bm[col][0],
            grid9_bm[col][1],
        ]
        d12, d23, d3t = J2 - J1, J3 - J2, Jtip - J3
        # Bicondylar joint widths at PIP (2) & DIP (4), waisted shafts (1, 3), fuller rounded distal fingertip dome!
        f_stations = [
            (J1 + 0.24 * d12, 0.97, 0.97, 0.10, 0.00),
            (J1 + 0.64 * d12, 0.89, 0.90, 0.14, 0.08),
            (J2,              0.94, 1.00, 0.02, 0.00),  # PIP bicondylar joint
            (J2 + 0.50 * d23, 0.82, 0.84, 0.13, 0.10),
            (J3,              0.84, 0.90, 0.02, 0.00),  # DIP bicondylar joint
            (J3 + 0.24 * d3t, 0.80, 0.85, 0.17, 0.24),  # cuticle base
            (J3 + 0.72 * d3t, 0.74, 0.79, 0.26, 0.28),  # distal nail free-edge & plump pulp pad
            (J3 + 0.93 * d3t, 0.58, 0.63, 0.16, 0.18),  # smooth pre-apex rounding ring!
            (Jtip,            0.36, 0.40, 0.06, 0.10),  # rounded fingertip apex
        ]

        prev_ring = sock_ring
        ring_history = []
        for fs_i, (c_pt, sx, sy, p_bulge, d_flat) in enumerate(f_stations):
            if fs_i <= 1:
                seg_dir = d12
            elif fs_i <= 3:
                seg_dir = d23
            else:
                seg_dir = d3t
            T_ax = seg_dir / np.linalg.norm(seg_dir)
            D_ax = np.array([1.0, 0.0, 0.0]) - T_ax * T_ax[0]
            D_ax /= np.linalg.norm(D_ax)
            U_ax = np.cross(T_ax, D_ax)

            cur_ring = []
            for ld, lu in local_6:
                dd = ld * rx0 * sx
                uu = lu * ry0 * sy
                if ld < -0.5:
                    dd -= rx0 * p_bulge
                if ld > 0.5 and d_flat > 0.0:
                    dd *= (1.0 - 0.20 * d_flat)
                if fs_i in (2, 4) and ld > 0.5:
                    dd += 0.0052
                cur_ring.append(bm.verts.new(tuple(c_pt + D_ax * dd + U_ax * uu)))

            for k in range(6):
                k1 = (k + 1) % 6
                f_new = bm.faces.new((prev_ring[k], prev_ring[k1], cur_ring[k1], cur_ring[k]))
                f_new[uv_grp] = 1 if k in (5, 0, 1) else 2
                if fs_i == 6 and k == 0:
                    nail_faces_to_inset.append(f_new)
            prev_ring = cur_ring
            ring_history.append(cur_ring)

        tip_r = ring_history[-1]
        ft_d = bm.faces.new((tip_r[0], tip_r[1], tip_r[2], tip_r[5]))
        ft_p = bm.faces.new((tip_r[5], tip_r[2], tip_r[3], tip_r[4]))
        ft_d[uv_grp] = 1
        ft_p[uv_grp] = 2

    # ==========================================================================
    # EXTRUDE ANATOMICAL OPPOSABLE THUMB + BROAD 3D THUMBNAIL
    # ==========================================================================
    r5, r6, r7 = ring_verts[5], ring_verts[6], ring_verts[7]
    thumb_sock = [r5[16], r5[17], r5[0], r6[0], r7[0], r7[17], r7[16], r6[16]]

    TJ1, TJ2, TJ3, TJtip = HAND_JOINTS["th_1"], HAND_JOINTS["th_2"], HAND_JOINTS["th_3"], HAND_JOINTS["th_tip"]
    T_th = (TJtip - TJ1) / np.linalg.norm(TJtip - TJ1)
    D_th = np.array([0.80, -0.50, 0.32])
    D_th = D_th - T_th * np.dot(D_th, T_th)
    D_th /= np.linalg.norm(D_th)
    U_th = np.cross(T_th, D_th)

    local_8 = [
        (-0.82, -0.82),
        ( 0.00, -1.00),
        ( 0.82, -0.82),
        ( 0.96,  0.00),
        ( 0.82,  0.82),
        ( 0.00,  1.00),
        (-0.82,  0.82),
        (-0.98,  0.00),
    ]
    td12, td23, td3t = TJ2 - TJ1, TJ3 - TJ2, TJtip - TJ3
    th_rx0, th_ry0 = 0.062, 0.068
    th_stations = [
        (TJ1 + 0.36 * td12, 1.18, 1.22, 0.16, 0.00),
        (TJ1 + 0.78 * td12, 0.98, 1.04, 0.10, 0.00),
        (TJ2,               0.96, 1.04, 0.04, 0.00),  # thumb MCP knuckle
        (TJ2 + 0.52 * td23, 0.85, 0.91, 0.08, 0.08),
        (TJ3,               0.88, 0.95, 0.04, 0.00),  # thumb IP knuckle
        (TJ3 + 0.30 * td3t, 0.82, 0.88, 0.15, 0.22),  # thumbnail cuticle base & mid-pulp pad
        (TJ3 + 0.78 * td3t, 0.70, 0.76, 0.08, 0.26),  # thumbnail distal free-edge (sleek human taper!)
        (TJ3 + 0.93 * td3t, 0.50, 0.55, 0.02, 0.16),  # smooth parabolic pre-apex dome
        (TJtip,             0.28, 0.32, 0.00, 0.08),
    ]

    prev_th = thumb_sock
    th_nail_faces = []
    for ts_i, (c_pt, sx, sy, p_bulge, d_flat) in enumerate(th_stations):
        cur_th = []
        for ld, lu in local_8:
            dd = ld * th_rx0 * sx
            uu = lu * th_ry0 * sy
            # Opposed thumb anatomy: (-0.82*D_th - 0.57*U_th) is dorsal back/thumbnail;
            # (+D_th, +U_th) is the fleshy palmar thumb pad pressing into the disk!
            dors_proj = -0.82 * ld - 0.57 * lu
            if dors_proj < -0.45:
                dd += th_rx0 * p_bulge * 0.85
                uu += th_ry0 * p_bulge * 0.45
            if dors_proj > 0.50 and d_flat > 0.0:
                dd *= (1.0 - 0.18 * d_flat)
                uu *= (1.0 - 0.12 * d_flat)
            if ts_i in (2, 4) and dors_proj > 0.50:
                dd -= 0.0044
                uu -= 0.0028
            cur_th.append(bm.verts.new(tuple(c_pt + D_th * dd + U_th * uu)))

        for k in range(8):
            k1 = (k + 1) % 8
            fn = bm.faces.new((prev_th[k], prev_th[k1], cur_th[k1], cur_th[k]))
            fn[uv_grp] = 3 if k in (6, 7, 0) else 4
            if ts_i == 6 and k in (7, 0):
                th_nail_faces.append(fn)
        prev_th = cur_th

    # Clean tip quads splitting THUMB_DORSAL (3) vs THUMB_PALMAR (4) along straight chord (6, 1)!
    ft_th_d = bm.faces.new((prev_th[6], prev_th[7], prev_th[0], prev_th[1]))
    ft_th_p1 = bm.faces.new((prev_th[6], prev_th[1], prev_th[2], prev_th[5]))
    ft_th_p2 = bm.faces.new((prev_th[5], prev_th[2], prev_th[3], prev_th[4]))
    ft_th_d[uv_grp] = 3
    ft_th_p1[uv_grp] = 4
    ft_th_p2[uv_grp] = 4

    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))

    # Inset 3D eponychium/paronychium cuticle folds & convex keratin nail plates
    nail_mat_faces = []
    for f_nail in nail_faces_to_inset:
        res1 = bmesh.ops.inset_individual(bm, faces=[f_nail], thickness=0.0052, depth=-0.0022)
        for rf in res1.get("faces", []):
            rf[uv_grp] = 1
        res2 = bmesh.ops.inset_individual(bm, faces=[f_nail], thickness=0.0018, depth=0.0036)
        for rf in res2.get("faces", []):
            rf[uv_grp] = 1
        f_nail[uv_grp] = 1
        nail_mat_faces.append(f_nail)

    if len(th_nail_faces) == 2:
        res1 = bmesh.ops.inset_region(bm, faces=th_nail_faces, thickness=0.0062, depth=-0.0024)
        for rf in res1.get("faces", []):
            rf[uv_grp] = 3
        res2 = bmesh.ops.inset_region(bm, faces=th_nail_faces, thickness=0.0020, depth=0.0040)
        for rf in res2.get("faces", []):
            rf[uv_grp] = 3
        for tf in th_nail_faces:
            tf[uv_grp] = 3
        nail_mat_faces.extend(th_nail_faces)

    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.normal_update()
    non_man = [e for e in bm.edges if not e.is_manifold]
    assert len(non_man) == 0, f"Hand cage has {len(non_man)} non-manifold edges!"

    # Mark clean anatomical glove UV seams ONLY where `uv_grp` differs across an edge!
    seam_count = 0
    for e in bm.edges:
        f0, f1 = e.link_faces[0], e.link_faces[1]
        if f0[uv_grp] != f1[uv_grp]:
            e.seam = True
            seam_count += 1
        else:
            e.seam = False

    print(f"  [CAGE OK] Watertight quad hand cage: {len(bm.verts)} verts, {len(bm.faces)} faces, seams={seam_count}, non-manifold=0")
    return bm, set(nail_mat_faces)


# ==============================================================================
# 2. SCULPTED 3.5" 'LOL.BAT' FLOPPY DISK MESH (MAPPED TO TOP ATLAS STRIP)
# ==============================================================================
def build_floppy_disk_data(half_w=0.232, half_h=0.242, half_t=0.0155):
    """Builds a crisp 3D 3.5" floppy disk in local disk space:
      - Front face ('LOL.BAT' white paper label) faces -X.
      - Back face (brushed steel circular spindle hub) faces +X.
      - Top sliding metal shutter is +Z; bottom edge is -Z; right notch is (-W, +H).
      - UVs map into top strip `v_png in [0.004, 0.278]` of the 1024x1024 combined atlas!
    """
    verts, norms, st, tris = [], [], [], []
    W, H, T = half_w, half_h, half_t
    cham = W * 0.20

    def add_q(p0, p1, p2, p3, uv0, uv1, uv2, uv3, nrm=None):
        if nrm is None:
            e1 = np.array(p1) - np.array(p0)
            e2 = np.array(p2) - np.array(p0)
            c = np.cross(e1, e2)
            nrm = tuple(c / (np.linalg.norm(c) + 1e-12))
        b = len(verts)
        verts.extend([p0, p1, p2, p3])
        norms.extend([nrm, nrm, nrm, nrm])
        st.extend([uv0, uv1, uv2, uv3])
        tris.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])

    def add_box(x0, x1, y0, y1, z0, z1, uv_all, uv_px=None, uv_nx=None, uv_pz=None):
        upx = uv_px or uv_all
        unx = uv_nx or uv_all
        upz = uv_pz or uv_all
        add_q((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1),
              (upx[0], upx[1]), (upx[0], upx[3]), (upx[2], upx[3]), (upx[2], upx[1]), (1.0, 0.0, 0.0))
        add_q((x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1),
              (unx[0], unx[1]), (unx[0], unx[3]), (unx[2], unx[3]), (unx[2], unx[1]), (-1.0, 0.0, 0.0))
        add_q((x1, y1, z1), (x1, y1, z0), (x0, y1, z0), (x0, y1, z1),
              (uv_all[0], uv_all[1]), (uv_all[0], uv_all[3]), (uv_all[2], uv_all[3]), (uv_all[2], uv_all[1]), (0.0, 1.0, 0.0))
        add_q((x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1),
              (uv_all[0], uv_all[1]), (uv_all[0], uv_all[3]), (uv_all[2], uv_all[3]), (uv_all[2], uv_all[1]), (0.0, -1.0, 0.0))
        add_q((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
              (upz[0], upz[1]), (upz[0], upz[3]), (upz[2], upz[3]), (upz[2], upz[1]), (0.0, 0.0, 1.0))
        add_q((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0),
              (uv_all[0], uv_all[1]), (uv_all[0], uv_all[3]), (uv_all[2], uv_all[3]), (uv_all[2], uv_all[1]), (0.0, 0.0, -1.0))

    perim = [
        (+W, +H),
        (-W + cham, +H),
        (-W, +H - cham),
        (-W, -H),
        (+W, -H),
    ]

    # Atlas UV helpers (1024x1024 top strip)
    def uv_front(y, z):
        # Panel 1: x in [6..282], y in [6..282]
        u = (6.0 + 276.0 * ((W - y) / (2.0 * W))) / 1024.0
        v = (6.0 + 276.0 * ((H - z) / (2.0 * H))) / 1024.0
        return (u, v)

    def uv_back(y, z):
        # Panel 2: x in [298..574], y in [6..282]
        u = (298.0 + 276.0 * ((y + W) / (2.0 * W))) / 1024.0
        v = (6.0 + 276.0 * ((H - z) / (2.0 * H))) / 1024.0
        return (u, v)

    UV_SHUT = (590.0 / 1024.0, 6.0 / 1024.0, 850.0 / 1024.0, 282.0 / 1024.0)
    UV_SHUT_TOP = (596.0 / 1024.0, 10.0 / 1024.0, 844.0 / 1024.0, 46.0 / 1024.0)
    UV_RIM = (870.0 / 1024.0, 10.0 / 1024.0, 1014.0 / 1024.0, 278.0 / 1024.0)

    # Front (-X) & Back (+X) faces
    bf = len(verts)
    verts.append((-T, 0.0, 0.0))
    norms.append((-1.0, 0.0, 0.0))
    st.append(uv_front(0.0, 0.0))
    for y, z in perim:
        verts.append((-T, y, z))
        norms.append((-1.0, 0.0, 0.0))
        st.append(uv_front(y, z))
    for i in range(len(perim)):
        j = (i + 1) % len(perim)
        tris.append((bf, bf + 1 + j, bf + 1 + i))

    bb = len(verts)
    verts.append((+T, 0.0, 0.0))
    norms.append((+1.0, 0.0, 0.0))
    st.append(uv_back(0.0, 0.0))
    for y, z in perim:
        verts.append((+T, y, z))
        norms.append((+1.0, 0.0, 0.0))
        st.append(uv_back(y, z))
    for i in range(len(perim)):
        j = (i + 1) % len(perim)
        tris.append((bb, bb + 1 + i, bb + 1 + j))

    # Perimeter plastic rim edges
    for i in range(len(perim)):
        j = (i + 1) % len(perim)
        y0, z0 = perim[i]
        y1, z1 = perim[j]
        en = np.array([0.0, z1 - z0, -(y1 - y0)], dtype=np.float64)
        en /= np.linalg.norm(en) + 1e-12
        add_q(
            (-T, y0, z0), (-T, y1, z1), (+T, y1, z1), (+T, y0, z0),
            (UV_RIM[0], UV_RIM[1]), (UV_RIM[0], UV_RIM[3]), (UV_RIM[2], UV_RIM[3]), (UV_RIM[2], UV_RIM[1]),
            tuple(en),
        )

    # Raised 3D U-shaped brushed stainless-steel sliding shutter
    st_x = T + 0.0038
    add_box(-st_x, +st_x, -W * 0.64, +W * 0.68, +H * 0.37, +H * 1.012, UV_SHUT, uv_px=UV_SHUT, uv_nx=UV_SHUT, uv_pz=UV_SHUT_TOP)

    # Raised 3D circular brushed-steel spindle hub on the back (+X) face
    # Panel 2 hub center is at y_px = 4+168 -> (H - z)/(2H) = 164/276 = 0.5942 -> z = -0.188 * H
    hub_z = -0.188 * H
    hub_r = W * 0.355
    hx0, hx1 = T, T + 0.0042
    segs_h = 16
    bhc = len(verts)
    verts.append((hx1, 0.0, hub_z))
    norms.append((1.0, 0.0, 0.0))
    st.append(uv_back(0.0, hub_z))
    for k in range(segs_h):
        a = 2.0 * math.pi * k / segs_h
        hy, hz = hub_r * math.cos(a), hub_z + hub_r * math.sin(a)
        verts.append((hx1, hy, hz))
        norms.append((1.0, 0.0, 0.0))
        st.append(uv_back(hy, hz))
    for k in range(segs_h):
        k2 = (k + 1) % segs_h
        tris.append((bhc, bhc + 1 + k, bhc + 1 + k2))
    for k in range(segs_h):
        k2 = (k + 1) % segs_h
        a0, a1 = 2.0 * math.pi * k / segs_h, 2.0 * math.pi * k2 / segs_h
        y0, z0 = hub_r * math.cos(a0), hub_z + hub_r * math.sin(a0)
        y1, z1 = hub_r * math.cos(a1), hub_z + hub_r * math.sin(a1)
        add_q((hx1, y0, z0), (hx0, y0, z0), (hx0, y1, z1), (hx1, y1, z1),
              (UV_SHUT_TOP[0], UV_SHUT_TOP[1]), (UV_SHUT_TOP[0], UV_SHUT_TOP[3]),
              (UV_SHUT_TOP[2], UV_SHUT_TOP[3]), (UV_SHUT_TOP[2], UV_SHUT_TOP[1]))

    return (
        np.array(verts, dtype=np.float64),
        np.array(norms, dtype=np.float64),
        np.array(st, dtype=np.float64),
        np.array(tris, dtype=np.int32),
    )


# ==============================================================================
# 3. SUBDIVIDE, SCULPT MICRO-ANATOMY, BAKE CYCLES SSS + AO, SYNTHESIZE ATLAS
# ==============================================================================
def srgb_to_linear(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * (np.maximum(c, 1e-12) ** (1.0 / 2.4)) - 0.055)


def sculpt_hand_displacement(me_target):
    """Applies identical 3D anatomical tendon, brachioradialis, palmar crease, and knuckle rugae relief."""
    me_target.polygons.foreach_set("use_smooth", [True] * len(me_target.polygons))
    me_target.update()
    V = np.array([v.co[:] for v in me_target.vertices], dtype=np.float64)
    N = np.array([v.normal[:] for v in me_target.vertices], dtype=np.float64)
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    disp = np.zeros(len(V), dtype=np.float64)

    # 1. Dorsal extensor digitorum tendons converging toward wrist
    dors_mask = sstep_np(0.012, 0.055, x) * sstep_np(-0.04, 0.06, z) * (1.0 - sstep_np(0.42, 0.48, z))
    for ky in (-0.156, -0.048, 0.056, 0.150):
        t_p = np.clip(z / 0.45, 0.0, 1.0)
        y_t = ky * (0.20 + 0.80 * t_p)
        disp += 0.0048 * np.exp(-(((y - y_t) / 0.014) ** 2)) * dors_mask * (0.30 + 0.70 * t_p)

    # 2. Extensor pollicis longus tendon along dorsal-radial thumb / anatomical snuffbox
    th_line_y = -0.09 - 0.56 * np.clip(z - 0.02, 0.0, 0.42)
    epl_mask = sstep_np(0.00, 0.05, x) * sstep_np(-0.02, 0.06, z) * (1.0 - sstep_np(0.32, 0.40, z))
    disp += 0.0044 * np.exp(-(((y - th_line_y) / 0.017) ** 2)) * epl_mask

    # 3. Muscular brachioradialis & extensor carpi radialis belly on forearm
    brach = (
        sstep_np(-1.45, -0.90, z)
        * (1.0 - sstep_np(-0.24, -0.04, z))
        * np.exp(-(((y + 0.115) / 0.085) ** 2))
        * sstep_np(-0.05, 0.06, x)
    )
    disp += 0.0120 * brach

    # 4. Volar wrist flexor tendons (flexor carpi radialis + palmaris longus) & rasceta wrist creases
    volar_wrist = sstep_np(-0.02, -0.07, x) * np.exp(-(((z + 0.04) / 0.12) ** 2))
    for wy in (-0.032, 0.008):
        disp += 0.0035 * np.exp(-(((y - wy) / 0.014) ** 2)) * volar_wrist
    for wz_c in (-0.012, -0.038):
        disp -= 0.0022 * np.exp(-(((z - wz_c) / 0.0055) ** 2)) * sstep_np(-0.02, -0.07, x) * np.exp(-((y / 0.12) ** 2))

    # 5. Sculpted palmar flexion creases (thenar life-line, proximal head line, distal heart line)
    palm_m = sstep_np(-0.02, -0.06, x) * sstep_np(0.07, 0.13, z) * (1.0 - sstep_np(0.39, 0.44, z))
    d_life = np.hypot((y + 0.165) / 0.165, (z - 0.165) / 0.215) - 1.0
    disp -= 0.0026 * np.exp(-((d_life / 0.050) ** 2)) * palm_m
    d_head = (z - (0.285 - 0.18 * (y + 0.12))) / 0.009
    disp -= 0.0022 * np.exp(-(d_head * d_head)) * palm_m * sstep_np(-0.15, -0.08, y) * (1.0 - sstep_np(0.08, 0.15, y))
    d_heart = (z - (0.365 - 0.10 * (0.14 - y))) / 0.009
    disp -= 0.0022 * np.exp(-(d_heart * d_heart)) * palm_m * sstep_np(-0.06, 0.00, y)

    # 6. Concentric dorsal knuckle rugae (PIP, DIP, thumb IP) & volar interphalangeal joint creases
    nd_th_v = -0.912 * N[:, 0] - 0.206 * N[:, 1] - 0.354 * N[:, 2]
    for jn in ("ix_2", "md_2", "rg_2", "pk_2", "ix_3", "md_3", "rg_3", "pk_3", "th_2", "th_3"):
        jp = HAND_JOINTS[jn]
        dj = np.linalg.norm(V - jp[None, :], axis=1)
        if jn.startswith("th_"):
            t_ax_v = (x - jp[0]) * (-0.161) + (y - jp[1]) * (-0.612) + (z - jp[2]) * 0.774
            kn_dors = np.exp(-((dj / 0.032) ** 2)) * sstep_np(0.25, 0.65, nd_th_v)
            disp += 0.0016 * np.sin(t_ax_v * 480.0) * kn_dors
            kn_vol = np.exp(-((t_ax_v / 0.0060) ** 2)) * np.exp(-((dj / 0.048) ** 2)) * sstep_np(-0.15, -0.55, nd_th_v)
            disp -= 0.0024 * kn_vol
        else:
            kn_dors = np.exp(-((dj / 0.030) ** 2)) * sstep_np(0.00, 0.04, x - jp[0])
            disp += 0.0016 * np.sin((z - jp[2]) * 480.0) * kn_dors
            kn_vol = np.exp(-(((z - jp[2]) / 0.0055) ** 2)) * np.exp(-(((y - jp[1]) / 0.042) ** 2)) * sstep_np(-0.01, -0.04, x - jp[0])
            disp -= 0.0024 * kn_vol

    V_sculpt = V + N * disp[:, None]
    for idx, v in enumerate(me_target.vertices):
        v.co = V_sculpt[idx]
    me_target.update()


def build_bake_and_rig(strip_png_path, out_dir):
    bpy.ops.wm.read_factory_settings(use_empty=True)

    bm, nail_faces = build_anatomical_hand_bmesh()
    nail_layer = bm.faces.layers.int.new("is_nail")
    for f in bm.faces:
        f[nail_layer] = 1 if f in nail_faces else 0

    me_cage = bpy.data.meshes.new("RealHandCage")
    bm.to_mesh(me_cage)
    bm.free()
    me_cage.uv_layers.new(name="UVMap")
    me_cage.update()

    ob = bpy.data.objects.new("RealHand", me_cage)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # Unwrap the 7 pure-disk anatomical glove pelts cleanly along marked lateral seams!
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Deterministically orient (+Z distal = +V up) and fit each of the 7 pelts into dedicated
    # non-overlapping atlas slots so visible Hand & Thumb pelts receive 90% of the 1024x700 skin budget!
    slots = {
        1: (0.024, 0.024, 0.354, 0.676),  # HAND_DORSAL (back of hand, knuckles, 4 fingernails)
        2: (0.380, 0.024, 0.710, 0.676),  # HAND_PALMAR (palm creases, thenar/hypothenar, finger pads)
        3: (0.736, 0.272, 0.850, 0.676),  # THUMB_DORSAL (thumbnail, cuticle, dorsal thumb)
        4: (0.872, 0.272, 0.980, 0.676),  # THUMB_PALMAR (volar thumb pad & opposition web)
        5: (0.736, 0.024, 0.834, 0.232),  # FOREARM_DORSAL_PROX (off-screen upper forearm)
        6: (0.854, 0.024, 0.942, 0.232),  # FOREARM_PALMAR_PROX (off-screen upper forearm)
        0: (0.956, 0.024, 0.986, 0.115),  # CAP (off-screen proximal forearm endcap)
    }
    poly_grp = me_cage.attributes["uv_grp"].data
    uv_cage = me_cage.uv_layers.active.data
    grp_loops = {g: [] for g in slots}
    for pi, poly in enumerate(me_cage.polygons):
        g = int(poly_grp[pi].value)
        for lp_i in poly.loop_indices:
            grp_loops[g].append((lp_i, me_cage.loops[lp_i].vertex_index))

    for g, (su0, sv0, su1, sv1) in slots.items():
        items = grp_loops[g]
        if not items:
            continue
        pts_uv = np.array([[uv_cage[lp_i].uv[0], uv_cage[lp_i].uv[1]] for lp_i, _ in items], dtype=np.float64)
        pts_z = np.array([me_cage.vertices[vi].co.z for _, vi in items], dtype=np.float64)
        # Rotate by multiples of 90 deg so +Z (distal) points upward along +V!
        if g != 0 and np.ptp(pts_z) > 1e-4:
            best_ang = 0.0
            best_corr = -1e9
            c_uv = pts_uv.mean(axis=0)
            for ang_deg in (0.0, 90.0, 180.0, 270.0):
                ar = math.radians(ang_deg)
                ca, sa = math.cos(ar), math.sin(ar)
                v_rot = -(pts_uv[:, 0] - c_uv[0]) * sa + (pts_uv[:, 1] - c_uv[1]) * ca
                corr = float(np.dot(v_rot - v_rot.mean(), pts_z - pts_z.mean())) / (float(np.std(v_rot)) + 1e-9)
                if corr > best_corr:
                    best_corr = corr
                    best_ang = ang_deg
            ar = math.radians(best_ang)
            ca, sa = math.cos(ar), math.sin(ar)
            du = (pts_uv[:, 0] - c_uv[0]) * ca + (pts_uv[:, 1] - c_uv[1]) * sa
            dv = -(pts_uv[:, 0] - c_uv[0]) * sa + (pts_uv[:, 1] - c_uv[1]) * ca
            pts_uv = np.column_stack([du, dv])

        umin, vmin = pts_uv.min(axis=0)
        umax, vmax = pts_uv.max(axis=0)
        span_u = max(1e-6, umax - umin)
        span_v = max(1e-6, vmax - vmin)
        sw_u, sw_v = su1 - su0, sv1 - sv0
        # Preserve conformal aspect ratio inside each dedicated slot
        sc = min(sw_u / span_u, sw_v / span_v)
        off_u = su0 + 0.5 * (sw_u - span_u * sc)
        off_v = sv0 + 0.5 * (sw_v - span_v * sc)
        for idx_it, (lp_i, _) in enumerate(items):
            uv_cage[lp_i].uv[0] = float(off_u + (pts_uv[idx_it, 0] - umin) * sc)
            uv_cage[lp_i].uv[1] = float(off_v + (pts_uv[idx_it, 1] - vmin) * sc)
    me_cage.update()

    # Create Ultra-High-Poly Level-3 Catmull-Clark copy (~65k tris) purely for razor-sharp Cycles Baking!
    me_hi = me_cage.copy()
    ob_hi = bpy.data.objects.new("RealHandHiBake", me_hi)
    bpy.context.collection.objects.link(ob_hi)
    ob.hide_render = True

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob_hi
    ob_hi.select_set(True)
    sub_hi = ob_hi.modifiers.new("SubHi", type="SUBSURF")
    sub_hi.levels = 3
    sub_hi.render_levels = 3
    sub_hi.uv_smooth = "PRESERVE_BOUNDARIES"
    bpy.ops.object.modifier_apply(modifier=sub_hi.name)
    sculpt_hand_displacement(ob_hi.data)

    # Store NailCol attribute on `ob_hi.data` so Cycles Principled BSDF gives nails glossy specular roughness!
    bm_tmp = bmesh.new()
    bm_tmp.from_mesh(ob_hi.data)
    nl_l = bm_tmp.faces.layers.int.get("is_nail")
    vc_l = bm_tmp.loops.layers.color.new("NailCol")
    for f in bm_tmp.faces:
        val = 1.0 if (nl_l and f[nl_l] == 1) else 0.0
        for lp in f.loops:
            lp[vc_l] = (val, val, val, 1.0)
    bm_tmp.to_mesh(ob_hi.data)
    bm_tmp.free()
    ob_hi.data.update()

    # ==========================================================================
    # CYCLES BAKING ON `ob_hi` (AO, 3D POS, NORMAL, POINTINESS, SSS + MICRO-BUMP)
    # ==========================================================================
    RES = 1024
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.margin = 0  # Disable Blender margin so sub-pixel edge samples never smear dark halos!

    scene.world = bpy.data.worlds.new("BakeWorld")
    scene.world.use_nodes = True
    w_bg = scene.world.node_tree.nodes.get("Background")
    w_bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    w_bg.inputs["Strength"].default_value = 1.0

    def bake_pass(img_name, setup_nodes_fn, bake_type="EMIT", samples=16, return_alpha=False):
        scene.cycles.samples = samples
        img = bpy.data.images.new(img_name, width=RES, height=RES, alpha=True, float_buffer=True)
        mat = bpy.data.materials.new(img_name + "_mat")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out_n = nt.nodes.new("ShaderNodeOutputMaterial")
        setup_nodes_fn(nt, out_n)
        ti = nt.nodes.new("ShaderNodeTexImage")
        ti.image = img
        nt.nodes.active = ti
        ob_hi.data.materials.clear()
        ob_hi.data.materials.append(mat)
        bpy.ops.object.bake(type=bake_type)
        arr = np.array(img.pixels[:], dtype=np.float32).reshape((RES, RES, 4))[::-1].copy()
        bpy.data.images.remove(img)
        if return_alpha:
            return arr[:, :, :3], arr[:, :, 3]
        return arr[:, :, :3]

    def dilate_from_interior(arr, interior_bool, iters=16):
        """Extrapolates pure un-antialiased interior UV texels outward across UV seams & margins."""
        is_2d = (arr.ndim == 2)
        cur = arr[:, :, None].copy() if is_2d else arr.copy()
        msk = interior_bool.copy()
        cur[~msk] = 0.0
        shifts = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for _ in range(iters):
            need = ~msk
            if not np.any(need):
                break
            acc = np.zeros_like(cur)
            cnt = np.zeros(msk.shape, dtype=np.float32)
            for dy, dx in shifts:
                m_s = np.roll(np.roll(msk, dy, axis=0), dx, axis=1)
                c_s = np.roll(np.roll(cur, dy, axis=0), dx, axis=1)
                w = m_s.astype(np.float32)
                acc += c_s * w[:, :, None]
                cnt += w
            fill = need & (cnt > 0.0)
            cur[fill] = acc[fill] / cnt[fill, None]
            msk[fill] = True
        return (cur[:, :, 0] if is_2d else cur), msk

    def setup_pos(nt, out_n):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        vm = nt.nodes.new("ShaderNodeVectorMath")
        vm.operation = "MULTIPLY_ADD"
        vm.inputs[1].default_value = (0.25, 0.25, 0.25)
        vm.inputs[2].default_value = (0.5, 0.5, 0.5)
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(vm.inputs[0], tc.outputs["Object"])
        nt.links.new(em.inputs["Color"], vm.outputs["Vector"])
        nt.links.new(out_n.inputs["Surface"], em.outputs["Emission"])

    pos_raw = bake_pass("bake_pos", setup_pos, "EMIT", samples=4)
    # Every vertex on the mesh has x in [-0.20, +0.20] -> `pos_raw[:,:,0]` in [0.45, 0.55].
    # Any 0% background or <=75% partial-coverage edge pixel has `pos_raw[:,:,0] <= 0.415`!
    full_cov = pos_raw[:, :, 0] > 0.435
    pure_interior = (
        full_cov
        & np.roll(full_cov, 1, axis=0)
        & np.roll(full_cov, -1, axis=0)
        & np.roll(full_cov, 1, axis=1)
        & np.roll(full_cov, -1, axis=1)
    )
    pos_dil, dilated_mask = dilate_from_interior(pos_raw, pure_interior, iters=20)
    valid_mask = dilated_mask.astype(np.float32)
    pos_map = (pos_dil - 0.5) * 4.0

    ao_raw = bake_pass("bake_ao", lambda nt, o: nt.links.new(o.inputs["Surface"], nt.nodes.new("ShaderNodeBsdfDiffuse").outputs["BSDF"]), "AO", samples=28)[:, :, 0]
    ao_map, _ = dilate_from_interior(ao_raw, pure_interior, iters=20)

    def setup_nrm(nt, out_n):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        vm = nt.nodes.new("ShaderNodeVectorMath")
        vm.operation = "MULTIPLY_ADD"
        vm.inputs[1].default_value = (0.5, 0.5, 0.5)
        vm.inputs[2].default_value = (0.5, 0.5, 0.5)
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(vm.inputs[0], geo.outputs["Normal"])
        nt.links.new(em.inputs["Color"], vm.outputs["Vector"])
        nt.links.new(out_n.inputs["Surface"], em.outputs["Emission"])

    nrm_raw = bake_pass("bake_nrm", setup_nrm, "EMIT", samples=4)
    nrm_dil, _ = dilate_from_interior(nrm_raw, pure_interior, iters=20)
    nrm_map = nrm_dil * 2.0 - 1.0

    def setup_pointy(nt, out_n):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(em.inputs["Color"], geo.outputs["Pointiness"])
        nt.links.new(out_n.inputs["Surface"], em.outputs["Emission"])

    pointy_raw = np.clip(bake_pass("bake_pointy", setup_pointy, "EMIT", samples=4)[:, :, 0], 0.0, 1.0)
    pointy, _ = dilate_from_interior(pointy_raw, pure_interior, iters=20)

    # Bake Cycles Principled BSDF v2 Subsurface Scattering + Voronoi Sulci Cutis Micro-Bump!
    w_bg.inputs["Color"].default_value = (0.36, 0.38, 0.42, 1.0)
    w_bg.inputs["Strength"].default_value = 0.75

    bake_lights = []
    light_specs = [
        ("KeyRadialPalmar", (-0.95, -1.10,  0.60), 6.2, 0.85, (1.00, 0.97, 0.93)),
        ("KeyDorsal",       ( 1.15, -0.50,  0.70), 5.8, 0.88, (0.97, 0.98, 1.00)),
        ("FillUlnar",       ( 0.10,  1.25,  0.30), 2.6, 1.15, (0.95, 0.96, 1.00)),
    ]
    for lname, lpos, lpow, lsize, lcol in light_specs:
        ld = bpy.data.lights.new(lname, type="AREA")
        ld.energy = lpow
        ld.size = lsize
        ld.color = lcol
        lo = bpy.data.objects.new(lname, ld)
        bpy.context.collection.objects.link(lo)
        lo.location = lpos
        direction = mathutils.Vector((0.0, 0.0, 0.25)) - mathutils.Vector(lpos)
        lo.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bake_lights.append(lo)

    def setup_sss_microbump(nt, out_n):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "NailCol"

        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.feature = "DISTANCE_TO_EDGE"
        vor.inputs["Scale"].default_value = 185.0
        nt.links.new(vor.inputs["Vector"], tc.outputs["Object"])

        noi = nt.nodes.new("ShaderNodeTexNoise")
        noi.inputs["Scale"].default_value = 360.0
        noi.inputs["Detail"].default_value = 5.0
        nt.links.new(noi.inputs["Vector"], tc.outputs["Object"])

        math_mix = nt.nodes.new("ShaderNodeMath")
        math_mix.operation = "MULTIPLY_ADD"
        nt.links.new(math_mix.inputs[0], vor.outputs["Distance"])
        math_mix.inputs[1].default_value = 0.70
        nt.links.new(math_mix.inputs[2], noi.outputs["Fac"])

        inv_nail = nt.nodes.new("ShaderNodeMath")
        inv_nail.operation = "SUBTRACT"
        inv_nail.inputs[0].default_value = 1.0
        nt.links.new(inv_nail.inputs[1], attr.outputs["Fac"])

        bump_str = nt.nodes.new("ShaderNodeMath")
        bump_str.operation = "MULTIPLY"
        nt.links.new(bump_str.inputs[0], inv_nail.outputs["Value"])
        bump_str.inputs[1].default_value = 0.28

        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 0.0026
        nt.links.new(bump.inputs["Strength"], bump_str.outputs["Value"])
        nt.links.new(bump.inputs["Height"], math_mix.outputs["Value"])

        rough_mix = nt.nodes.new("ShaderNodeMix")
        rough_mix.data_type = "FLOAT"
        nt.links.new(rough_mix.inputs["Factor"], attr.outputs["Fac"])
        rough_mix.inputs["A"].default_value = 0.44
        rough_mix.inputs["B"].default_value = 0.12

        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (0.72, 0.70, 0.68, 1.0)
        nt.links.new(bsdf.inputs["Roughness"], rough_mix.outputs["Result"])
        nt.links.new(bsdf.inputs["Normal"], bump.outputs["Normal"])
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = 0.40
        if "Subsurface Scale" in bsdf.inputs:
            bsdf.inputs["Subsurface Scale"].default_value = 0.022
        if "Subsurface Radius" in bsdf.inputs:
            bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.38, 0.22)
        nt.links.new(out_n.inputs["Surface"], bsdf.outputs["BSDF"])

    lit_sss_raw = bake_pass("bake_sss_lit", setup_sss_microbump, "COMBINED", samples=32)
    lit_sss_lin, _ = dilate_from_interior(lit_sss_raw, pure_interior, iters=20)

    for lo in bake_lights:
        bpy.data.objects.remove(lo, do_unlink=True)
    bpy.data.objects.remove(ob_hi, do_unlink=True)
    bpy.data.meshes.remove(me_hi, do_unlink=True)
    ob.hide_render = False

    # ==========================================================================
    # SYNTHESIZE PHOTOREALISTIC MULTI-CHROMOPHORE HUMAN SKIN + ANALYTICAL 3D NAILS
    # ==========================================================================
    px, py, pz = pos_map[:, :, 0], pos_map[:, :, 1], pos_map[:, :, 2]
    nx, ny, nz = nrm_map[:, :, 0], nrm_map[:, :, 1], nrm_map[:, :, 2]

    rng = np.random.default_rng(20261101)
    skin_micro = np.zeros((RES, RES), dtype=np.float32)
    for freq, amp in ((14.0, 0.34), (36.0, 0.28), (94.0, 0.22), (245.0, 0.18)):
        kx, ky, kz, ph = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 6.283)
        kn = math.sqrt(kx * kx + ky * ky + kz * kz) + 1e-6
        skin_micro += amp * np.sin((px * kx + py * ky + pz * kz) / kn * freq + ph)

    follicle_seed = np.sin(px * 320.0 + 1.3) * np.sin(py * 305.0 - 0.7) * np.sin(pz * 155.0 + 2.1)
    forearm_hair_m = sstep_np(0.08, -0.35, pz) * sstep_np(-0.10, 0.45, nx)
    follicles = np.clip((follicle_seed - 0.72) * 3.4, 0.0, 1.0) * forearm_hair_m

    # 1. Lifelike sunlit human peach-tan dorsal skin vs warm rosy-cream palmar skin (perceptual sRGB)
    nd_th_px = -0.680 * nx - 0.540 * ny - 0.495 * nz
    th_dors_cool = 0.60 * sstep_np(-0.12, -0.34, py) * sstep_np(0.04, 0.28, pz) * sstep_np(0.05, 0.55, nd_th_px)
    palmar_w = sstep_np(0.16, -0.32, nx) * sstep_np(-0.06, 0.10, pz) * (1.0 - th_dors_cool)
    dorsal_rgb = np.array([0.84, 0.67, 0.56], dtype=np.float32)
    palmar_rgb = np.array([0.90, 0.75, 0.66], dtype=np.float32)
    forearm_tan = sstep_np(0.06, -0.55, pz)
    base = dorsal_rgb[None, None, :] * (1.0 - palmar_w[:, :, None]) + palmar_rgb[None, None, :] * palmar_w[:, :, None]
    base *= (1.0 - 0.06 * forearm_tan[:, :, None])
    base += skin_micro[:, :, None] * np.array([0.028, 0.022, 0.019], dtype=np.float32)
    base *= (1.0 - 0.16 * follicles[:, :, None])

    # Subtle fingerprint / dermatoglyphic friction-ridge texture on volar pads!
    ridge_pat = 0.5 + 0.5 * np.sin(pz * 520.0 + 3.5 * np.cos(py * 180.0))
    volar_pads = sstep_np(-0.15, -0.55, nx) * sstep_np(0.32, 0.52, pz)
    base *= (1.0 - 0.028 * ridge_pat[:, :, None] * volar_pads[:, :, None])

    # 2. Oxygenated Hemoglobin Perfusion (fingertips, knuckles, thenar/hypothenar pads, interdigital webs)
    tip_flush = np.zeros((RES, RES), dtype=np.float32)
    for tn in ("ix_tip", "md_tip", "rg_tip", "pk_tip", "th_tip"):
        tp = HAND_JOINTS[tn]
        dt = np.sqrt((px - tp[0]) ** 2 + (py - tp[1]) ** 2 + (pz - tp[2]) ** 2)
        tip_flush = np.maximum(tip_flush, np.exp(-((dt / 0.115) ** 2)))

    kn_flush = np.zeros((RES, RES), dtype=np.float32)
    for kn in ("ix_1", "md_1", "rg_1", "pk_1", "ix_2", "md_2", "rg_2", "pk_2", "th_2", "th_3"):
        kp = HAND_JOINTS[kn]
        dk = np.sqrt((px - kp[0]) ** 2 + (py - kp[1]) ** 2 + (pz - kp[2]) ** 2)
        kn_flush = np.maximum(kn_flush, np.exp(-((dk / 0.058) ** 2)))

    thenar_flush = np.exp(-(((py + 0.14) / 0.11) ** 2 + ((pz - 0.18) / 0.16) ** 2)) * palmar_w
    hypothenar_flush = np.exp(-(((py - 0.15) / 0.08) ** 2 + ((pz - 0.22) / 0.18) ** 2)) * palmar_w

    flush = np.clip(0.50 * tip_flush + 0.38 * kn_flush + 0.30 * thenar_flush + 0.26 * hypothenar_flush, 0.0, 1.0)
    sss_red = np.array([0.86, 0.55, 0.50], dtype=np.float32)
    base = base * (1.0 - 0.22 * flush[:, :, None]) + sss_red[None, None, :] * (0.22 * flush[:, :, None])

    # 3. Tendon / Bone-proximity ivory highlights on stretched extensor tendons & wrist styloid
    tendon_ivory = np.clip((pointy - 0.505) * 4.8, 0.0, 1.0) * sstep_np(0.12, 0.52, nx)
    base = base * (1.0 - 0.24 * tendon_ivory[:, :, None]) + np.array([0.95, 0.86, 0.78], dtype=np.float32) * (0.24 * tendon_ivory[:, :, None])

    # 4. Subcutaneous branching dorsal & volar-wrist venous network (subtle muted blue-teal under skin)
    dors_v_mask = sstep_np(0.20, 0.60, nx) * sstep_np(-0.48, 0.02, pz) * (1.0 - sstep_np(0.32, 0.43, pz))
    v1 = np.exp(-(((py + 0.052 - 0.11 * pz + 0.012 * np.sin(pz * 14.0)) / 0.010) ** 2))
    v2 = np.exp(-(((py - 0.058 + 0.09 * pz + 0.010 * np.cos(pz * 16.0)) / 0.009) ** 2))
    v3 = np.exp(-(((py + 0.115 - 0.06 * pz) / 0.008) ** 2))
    v_fork = np.exp(-(((py + 0.004 + 0.18 * (pz - 0.15)) / 0.008) ** 2)) * sstep_np(0.05, 0.18, pz)
    volar_v_mask = sstep_np(-0.20, -0.60, nx) * np.exp(-(((pz + 0.08) / 0.14) ** 2))
    vw1 = np.exp(-(((py + 0.025) / 0.008) ** 2)) + np.exp(-(((py - 0.022) / 0.007) ** 2))
    veins = np.clip((v1 + v2 + 0.75 * v3 + 0.65 * v_fork) * dors_v_mask + 0.75 * vw1 * volar_v_mask, 0.0, 1.0)
    base = base * (1.0 - 0.18 * veins[:, :, None]) + np.array([0.46, 0.57, 0.65], dtype=np.float32) * (0.18 * veins[:, :, None])

    # 5. Crisp Subsurface Crevice Tint in Palmar Lines, Joint Creases & Dorsal Knuckle Rugae
    cavity = np.clip((0.498 - pointy) * 4.8, 0.0, 1.0)
    p_flex_m = sstep_np(-0.01, -0.06, nx)
    d_life_px = np.hypot((py + 0.165) / 0.165, (pz - 0.165) / 0.215) - 1.0
    d_head_px = (pz - (0.285 - 0.18 * (py + 0.12))) / 0.0080
    d_heart_px = (pz - (0.365 - 0.10 * (0.14 - py))) / 0.0080
    palm_creases = (
        0.38 * np.exp(-((d_life_px / 0.038) ** 2))
        + 0.32 * np.exp(-(d_head_px ** 2)) * sstep_np(-0.15, -0.08, py) * (1.0 - sstep_np(0.08, 0.15, py))
        + 0.32 * np.exp(-(d_heart_px ** 2)) * sstep_np(-0.06, 0.00, py)
    ) * sstep_np(0.07, 0.13, pz) * (1.0 - sstep_np(0.38, 0.43, pz)) * p_flex_m

    joint_creases = np.zeros((RES, RES), dtype=np.float32)
    for jn in ("ix_1", "md_1", "rg_1", "pk_1", "ix_2", "md_2", "rg_2", "pk_2", "ix_3", "md_3", "rg_3", "pk_3", "th_2", "th_3"):
        jp = HAND_JOINTS[jn]
        if jn.startswith("th_"):
            t_ax_th = (px - jp[0]) * (-0.161) + (py - jp[1]) * (-0.612) + (pz - jp[2]) * 0.774
            d_k = np.sqrt((px - jp[0]) ** 2 + (py - jp[1]) ** 2 + (pz - jp[2]) ** 2)
            th_vol_m = sstep_np(-0.10, -0.45, nd_th_px)
            joint_creases = np.maximum(
                joint_creases,
                0.34 * np.exp(-(((t_ax_th / 0.0062) ** 2) + ((d_k / 0.048) ** 2))) * th_vol_m,
            )
            rugae = (0.5 + 0.5 * np.sin(t_ax_th * 480.0)) * np.exp(-((d_k / 0.032) ** 2)) * sstep_np(0.25, 0.60, nd_th_px)
            joint_creases = np.maximum(joint_creases, 0.24 * rugae)
        else:
            d_ax = (pz - jp[2]) / 0.0058
            d_rad = ((py - jp[1]) / 0.044) ** 2
            joint_creases = np.maximum(joint_creases, 0.34 * np.exp(-(d_ax * d_ax + d_rad)) * p_flex_m)
            if jn in ("ix_2", "md_2", "rg_2", "pk_2", "ix_3", "md_3", "rg_3", "pk_3"):
                d_k = np.sqrt((px - jp[0]) ** 2 + (py - jp[1]) ** 2 + (pz - jp[2]) ** 2)
                rugae = (0.5 + 0.5 * np.sin((pz - jp[2]) * 480.0)) * np.exp(-((d_k / 0.030) ** 2)) * sstep_np(0.02, 0.18, nx)
                joint_creases = np.maximum(joint_creases, 0.26 * rugae)

    crease_col = np.array([0.46, 0.29, 0.24], dtype=np.float32)
    tot_crease = np.clip(0.36 * cavity + palm_creases + joint_creases, 0.0, 0.58)
    base = base * (1.0 - tot_crease[:, :, None]) + crease_col[None, None, :] * tot_crease[:, :, None]

    # 6. Sub-Pixel Analytical 3D Keratin Fingernails (natural short-trimmed male proportions!)
    nail_specs = [
        ("ix_3", "ix_tip", (1.0, 0.0, 0.0), 0.028, 0.48, 0.24, 0.87),
        ("md_3", "md_tip", (1.0, 0.0, 0.0), 0.030, 0.38, 0.24, 0.87),
        ("rg_3", "rg_tip", (1.0, 0.0, 0.0), 0.027, 0.30, 0.24, 0.87),
        ("pk_3", "pk_tip", (1.0, 0.0, 0.0), 0.022, 0.22, 0.24, 0.87),
        ("th_3", "th_tip", (-0.680, -0.540, -0.495), 0.026, 0.48, 0.30, 0.86),
    ]
    nail_spec_add = np.zeros((RES, RES), dtype=np.float32)
    nail_mask_tot = np.zeros((RES, RES), dtype=np.float32)
    for j_dip, j_tip, d_hint, hw_n, lun_str, tp0, td0 in nail_specs:
        p0 = HAND_JOINTS[j_dip]
        p1 = HAND_JOINTS[j_tip]
        seg = p1 - p0
        seg_len = float(np.linalg.norm(seg))
        T_ax = seg / seg_len
        D_ax = np.array(d_hint, dtype=np.float64)
        D_ax = D_ax - T_ax * np.dot(D_ax, T_ax)
        D_ax /= np.linalg.norm(D_ax)
        U_ax = np.cross(T_ax, D_ax)

        rx_p, ry_p, rz_p = px - p0[0], py - p0[1], pz - p0[2]
        t_n = (rx_p * T_ax[0] + ry_p * T_ax[1] + rz_p * T_ax[2]) / seg_len
        u_n = (rx_p * U_ax[0] + ry_p * U_ax[1] + rz_p * U_ax[2]) / hw_n
        d_n = rx_p * D_ax[0] + ry_p * D_ax[1] + rz_p * D_ax[2]
        nd_n = nx * D_ax[0] + ny * D_ax[1] + nz * D_ax[2]

        rad_sq = rx_p * rx_p + ry_p * ry_p + rz_p * rz_p - (t_n * seg_len) ** 2
        near_digit = (rad_sq < (hw_n * 2.05) ** 2) & (d_n > 0.005) & (nd_n > 0.30)

        t_prox = tp0 + 0.12 * (u_n * u_n)
        t_dist = td0 - 0.07 * (u_n * u_n)
        m_lat = 1.0 - np.abs(u_n)
        m_prox = (t_n - t_prox) * 3.2
        m_dist = (t_dist - t_n) * 3.6
        m_in = np.minimum(m_lat, np.minimum(m_prox, m_dist))

        plate_w = sstep_np(-0.03, 0.05, m_in) * near_digit.astype(np.float32)
        nail_mask_tot = np.maximum(nail_mask_tot, plate_w)
        groove_w = np.exp(-((m_in / 0.050) ** 2)) * sstep_np(td0 + 0.02, td0 - 0.16, t_n) * near_digit.astype(np.float32)
        cuticle_lip = np.exp(-(((t_n - (t_prox + 0.020)) / 0.018) ** 2)) * plate_w

        lun_d = ((t_n - t_prox) / 0.14) ** 2 + (u_n / 0.68) ** 2
        lun_w = (1.0 - sstep_np(0.65, 1.15, lun_d)) * lun_str
        onycho_w = np.exp(-(((t_n - (t_dist - 0.068)) / 0.026) ** 2)) * 0.50
        free_w = sstep_np(t_dist - 0.058, t_dist - 0.020, t_n) * 0.82
        striae = 0.012 * np.sin(u_n * 38.0)

        c_bed = np.array([0.89, 0.69, 0.65], dtype=np.float32)[None, None, :] + striae[:, :, None]
        c_lun = np.array([0.95, 0.88, 0.84], dtype=np.float32)[None, None, :]
        c_ony = np.array([0.76, 0.48, 0.46], dtype=np.float32)[None, None, :]
        c_fre = np.array([0.95, 0.91, 0.83], dtype=np.float32)[None, None, :]

        ncol = c_bed * (1.0 - lun_w[:, :, None]) + c_lun * lun_w[:, :, None]
        ncol = ncol * (1.0 - onycho_w[:, :, None]) + c_ony * onycho_w[:, :, None]
        ncol = ncol * (1.0 - free_w[:, :, None]) + c_fre * free_w[:, :, None]
        ncol = ncol * (1.0 - 0.22 * cuticle_lip[:, :, None]) + np.array([0.92, 0.83, 0.78], dtype=np.float32) * (0.22 * cuticle_lip[:, :, None])

        base = base * (1.0 - plate_w[:, :, None]) + ncol * plate_w[:, :, None]
        base = base * (1.0 - 0.42 * groove_w[:, :, None]) + np.array([0.40, 0.24, 0.20], dtype=np.float32) * (0.42 * groove_w[:, :, None])

        spec_bar = np.exp(-(((u_n + 0.24) / 0.19) ** 2)) * sstep_np(t_prox + 0.04, t_prox + 0.14, t_n) * plate_w
        nail_spec_add = np.maximum(nail_spec_add, 0.22 * spec_bar)

    # 7. Per-Channel Normalized Linear-Light Shading + Directional Cylindrical Relief & Skin Sheen!
    # Normalizing `lit_sss_lin` per-channel prevents Cycles Random-Walk SSS red path absorption from
    # shifting overall skin chromaticity to orange while preserving warm terminator scatter!
    base_lin = srgb_to_linear(base)
    ref_rgb = np.percentile(lit_sss_lin[pure_interior], 80, axis=0).astype(np.float32)
    ref_rgb = np.maximum(ref_rgb, 0.04)
    lit_norm_rgb = lit_sss_lin / ref_rgb[None, None, :]
    lit_luma_n = np.clip(
        0.30 * lit_norm_rgb[:, :, 0] + 0.56 * lit_norm_rgb[:, :, 1] + 0.14 * lit_norm_rgb[:, :, 2],
        0.28,
        1.28,
    )
    # Subtle warm subsurface hemoglobin glow restricted strictly to shadow terminators
    sss_term = np.clip(lit_norm_rgb[:, :, 0] - lit_norm_rgb[:, :, 1], 0.0, 0.36)

    # Analytical multi-key cylindrical normal relief + hydrated skin specular ridge sheen
    # so fingers, thumb, tendons & palm mounts maintain crisp 3D volume even in flat Quake ambient sectors!
    n_len = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    nnx, nny, nnz = nx / n_len, ny / n_len, nz / n_len
    # Key 1: Palmar-radial-upper (front view hold), Key 2: Dorsal-radial-upper (flipped view hold)
    ndotl_palmar = np.clip(-0.56 * nnx - 0.62 * nny + 0.55 * nnz, 0.0, 1.0)
    ndotl_dorsal = np.clip(+0.62 * nnx - 0.52 * nny + 0.58 * nnz, 0.0, 1.0)
    cyl_relief = 0.66 + 0.34 * np.maximum(ndotl_palmar, ndotl_dorsal)
    skin_sheen = (np.maximum(ndotl_palmar, ndotl_dorsal) ** 7.0) * (1.0 - 0.75 * tot_crease) * (1.0 - nail_mask_tot)

    ao_clean = np.clip(ao_map, 0.28, 1.0)
    warm_ao_lin = np.stack([ao_clean ** 0.72, ao_clean ** 0.90, ao_clean ** 1.04], axis=-1)
    cycles_spec = np.clip(lit_luma_n - 1.04, 0.0, 0.45)[:, :, None]

    shaded_lin = (
        base_lin
        * (0.20 + 0.80 * warm_ao_lin)
        * ((0.30 + 0.70 * lit_luma_n[:, :, None]) * cyl_relief[:, :, None])
        + sss_term[:, :, None] * np.array([0.045, 0.010, 0.006], dtype=np.float32)
        + 0.07 * cycles_spec
        + skin_sheen[:, :, None] * np.array([0.055, 0.048, 0.044], dtype=np.float32)
        + srgb_to_linear(nail_spec_add[:, :, None]) * 0.58
    )
    shaded_hand_srgb = np.clip(linear_to_srgb(shaded_lin), 0.0, 1.0)

    # Fill background outside dilated margin with matching warm mid-skin tone so mipmaps never bleed!
    bg_skin = np.array([0.78, 0.61, 0.51], dtype=np.float32)[None, None, :]
    shaded_hand_srgb = shaded_hand_srgb * valid_mask[:, :, None] + bg_skin * (1.0 - valid_mask[:, :, None])

    # ==========================================================================
    # COMPOSITE TOP FLOPPY DISK STRIP (ROWS 0..299) + HAND ATLAS (ROWS 300..1023)
    # Write bit-exact 8-bit sRGB PNGs directly via zlib/struct (bypasses Blender AgX/Filmic view transform!)
    # ==========================================================================
    import struct as _struct
    import zlib as _zlib

    def read_png_rgb_u8_blender_bypass(png_path):
        """Read exact 8-bit sRGB bytes without Blender linear/AgX conversion."""
        with open(png_path, "rb") as fp:
            raw = fp.read()
        assert raw[:8] == b"\x89PNG\r\n\x1a\n"
        pos = 8
        w = h = ctype = 0
        idat_chunks = []
        while pos < len(raw):
            ln = _struct.unpack(">I", raw[pos:pos + 4])[0]
            ctype_b = raw[pos + 4:pos + 8]
            chunk = raw[pos + 8:pos + 8 + ln]
            pos += 12 + ln
            if ctype_b == b"IHDR":
                w, h, bitd, ctype, _, _, _ = _struct.unpack(">IIBBBBB", chunk)
                assert bitd == 8 and ctype in (2, 6)
            elif ctype_b == b"IDAT":
                idat_chunks.append(chunk)
            elif ctype_b == b"IEND":
                break
        bpp = 3 if ctype == 2 else 4
        stride = w * bpp
        dec = _zlib.decompress(b"".join(idat_chunks))
        out = np.zeros((h, w, bpp), dtype=np.uint8)
        prev = np.zeros(stride, dtype=np.int32)
        p_idx = 0
        for y in range(h):
            ft = dec[p_idx]
            row = np.frombuffer(dec, dtype=np.uint8, count=stride, offset=p_idx + 1).astype(np.int32)
            p_idx += 1 + stride
            if ft == 1:
                for x in range(bpp, stride):
                    row[x] = (row[x] + row[x - bpp]) & 255
            elif ft == 2:
                row = (row + prev) & 255
            elif ft == 3:
                for x in range(stride):
                    a = row[x - bpp] if x >= bpp else 0
                    row[x] = (row[x] + ((a + prev[x]) >> 1)) & 255
            elif ft == 4:
                for x in range(stride):
                    a = row[x - bpp] if x >= bpp else 0
                    b = prev[x]
                    c = prev[x - bpp] if x >= bpp else 0
                    pa = abs(b - c)
                    pb = abs(a - c)
                    pc = abs(a + b - 2 * c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    row[x] = (row[x] + pr) & 255
            prev = row
            out[y] = row.astype(np.uint8).reshape((w, bpp))
        return out[:, :, :3]

    def write_png_rgb_u8(arr_srgb_f32, path):
        u8 = np.clip(np.rint(arr_srgb_f32 * 255.0), 0.0, 255.0).astype(np.uint8)
        h, w, _ = u8.shape
        raw_rows = b"".join(b"\x00" + u8[y].tobytes() for y in range(h))

        def _chunk(tag, payload):
            crc = _zlib.crc32(tag + payload) & 0xFFFFFFFF
            return _struct.pack(">I", len(payload)) + tag + payload + _struct.pack(">I", crc)

        ihdr = _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
        png_bytes = (
            b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", _zlib.compress(raw_rows, level=6))
            + _chunk(b"IEND", b"")
        )
        with open(path, "wb") as fp:
            fp.write(png_bytes)

    strip_u8 = read_png_rgb_u8_blender_bypass(strip_png_path)
    sh, sw, _ = strip_u8.shape
    assert sw == 1024 and sh == 300
    strip_srgb = strip_u8.astype(np.float32) / 255.0

    full_srgb = np.clip(shaded_hand_srgb, 0.0, 1.0).copy()
    full_srgb[:sh, :, :] = strip_srgb

    # Calibrate DarkPlaces texture gamma & exposure (`v_gamma`/`r_hdr_scenebrightness` + `rgbGen lightingDiffuse`
    # applies `(c ^ ~0.4545) * light`, so pre-linearizing `full_srgb` preserves true Cycles SSS skin tones,
    # creases, veins, and keratin nails without blowing out beside bright torches!)
    dp_srgb = np.zeros_like(full_srgb)
    dp_srgb[sh:, :, :] = (np.clip(full_srgb[sh:, :, :], 0.0, 1.0) ** 1.74) * 0.77
    dp_srgb[:sh, :, :] = (np.clip(full_srgb[:sh, :, :], 0.0, 1.0) ** 1.55) * 0.80

    srgb_path = os.path.join(out_dir, "netsend_hand_srgb.png")
    dp_path = os.path.join(out_dir, "netsend_hand_dp.png")
    write_png_rgb_u8(full_srgb, srgb_path)
    write_png_rgb_u8(dp_srgb, dp_path)
    print(f"  [ATLAS OK] Bit-exact 1024x1024 Cycles SSS + Analytical 3D Nails & Floppy Atlas -> {dp_path}")

    # ==========================================================================
    # SUBDIVIDE RUNTIME HAND (LEVEL 2) & PROTECT FINGERTIPS/NAILS/THUMB IN DECIMATE!
    # ==========================================================================
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    sub_rt = ob.modifiers.new("SubRuntime", type="SUBSURF")
    sub_rt.levels = 2
    sub_rt.render_levels = 2
    sub_rt.uv_smooth = "PRESERVE_BOUNDARIES"
    bpy.ops.object.modifier_apply(modifier=sub_rt.name)
    sculpt_hand_displacement(ob.data)

    # Note: In Blender's DecimateModifier (`COLLAPSE`), `invert_vertex_group = True` means
    # weight `1.0` = PROTECTED (keep crisp smooth silhouette!) and `0.0` = simplify freely!
    vg = ob.vertex_groups.new(name="ProtectFingers")
    for idx, v in enumerate(ob.data.vertices):
        vx, vy, vz = v.co.x, v.co.y, v.co.z
        is_thumb = (vy < -0.14 and vz > 0.06)
        if vz >= 0.56 or (is_thumb and (vy < -0.26 or vz > 0.26)):
            w = 0.90  # ultra-smooth rounded fingertips, nails & distal thumb!
        elif vz >= 0.36 or is_thumb:
            w = 0.68  # smooth knuckles, proximal phalanges & thumb-index web!
        elif vz >= -0.08:
            w = 0.35  # palm & wrist
        else:
            w = 0.0   # off-screen straight forearm tube -> simplify freely!
        vg.add([idx], float(w), "REPLACE")

    cur_nv = len(ob.data.vertices)
    target_nv = 1440  # ~2,720 hand tris + 148 disk tris = ~2,868 total tris (<= 3,000 MD3 budget!)
    if cur_nv > target_nv:
        dec = ob.modifiers.new("DecHand", type="DECIMATE")
        dec.decimate_type = "COLLAPSE"
        dec.ratio = target_nv / float(cur_nv)
        dec.vertex_group = vg.name
        dec.invert_vertex_group = True
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")

    me_dec = ob.data
    me_dec.polygons.foreach_set("use_smooth", [True] * len(me_dec.polygons))
    me_dec.update()

    # Build UV-split vertex mapping while keeping `ob` 100% watertight for Armature + CorrectiveSmooth!
    uv_lay = me_dec.uv_layers.active.data
    vert_uv_map = {}
    orig_vi_list = []
    hand_st = []
    hand_tris = []

    for poly in me_dec.polygons:
        if len(poly.vertices) != 3:
            continue
        t_idx = []
        for lp_i in poly.loop_indices:
            vi = me_dec.loops[lp_i].vertex_index
            uv = uv_lay[lp_i].uv
            u_f = float(uv[0])
            v_f = float(1.0 - uv[1])  # Blender bottom-up -> Quake/MD3 top-down!
            key = (vi, round(u_f, 4), round(v_f, 4))
            if key not in vert_uv_map:
                vert_uv_map[key] = len(orig_vi_list)
                orig_vi_list.append(vi)
                hand_st.append((u_f, v_f))
            t_idx.append(vert_uv_map[key])
        hand_tris.append(tuple(t_idx))

    orig_vi_arr = np.array(orig_vi_list, dtype=np.int32)
    hand_st_arr = np.array(hand_st, dtype=np.float64)
    hand_tris_arr = np.array(hand_tris, dtype=np.int32)
    print(f"  [DECIMATE OK] Hand watertight={len(me_dec.vertices)}v, MD3 split={len(orig_vi_arr)}v, tris={len(hand_tris_arr)}")

    # ==========================================================================
    # 18-BONE BLENDER ARMATURE + HEAT-DIFFUSION `ARMATURE_AUTO` + `CORRECTIVE_SMOOTH`
    # ==========================================================================
    arm_data = bpy.data.armatures.new("RealHandArm")
    arm_ob = bpy.data.objects.new("RealHandArmOb", arm_data)
    bpy.context.collection.objects.link(arm_ob)
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def add_bone(name, head, tail, roll_hint, parent_name=None, connect=False):
        b = eb.new(name)
        b.head = mathutils.Vector(tuple(head))
        b.tail = mathutils.Vector(tuple(tail))
        b.align_roll(mathutils.Vector(tuple(roll_hint)))
        if parent_name is not None:
            b.parent = eb[parent_name]
            b.use_connect = connect
        return b

    dors_x = (1.0, 0.0, 0.0)
    th_dors = (0.80, -0.50, 0.32)

    add_bone("forearm", HAND_JOINTS["forearm"], HAND_JOINTS["wrist"], dors_x, None, False)
    add_bone("wrist",   HAND_JOINTS["wrist"],   HAND_JOINTS["palm"],  dors_x, "forearm", True)
    add_bone("palm",    HAND_JOINTS["palm"],    HAND_JOINTS["md_1"],  dors_x, "wrist",   True)

    for pfx in ("ix", "md", "rg", "pk"):
        add_bone(f"{pfx}_1", HAND_JOINTS[f"{pfx}_1"], HAND_JOINTS[f"{pfx}_2"],   dors_x, "palm",     False)
        add_bone(f"{pfx}_2", HAND_JOINTS[f"{pfx}_2"], HAND_JOINTS[f"{pfx}_3"],   dors_x, f"{pfx}_1", True)
        add_bone(f"{pfx}_3", HAND_JOINTS[f"{pfx}_3"], HAND_JOINTS[f"{pfx}_tip"], dors_x, f"{pfx}_2", True)

    add_bone("th_1", HAND_JOINTS["th_1"], HAND_JOINTS["th_2"],   th_dors, "wrist", False)
    add_bone("th_2", HAND_JOINTS["th_2"], HAND_JOINTS["th_3"],   th_dors, "th_1",  True)
    add_bone("th_3", HAND_JOINTS["th_3"], HAND_JOINTS["th_tip"], th_dors, "th_2",  True)

    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    cs_mod = ob.modifiers.new("VolumePreserve", type="CORRECTIVE_SMOOTH")
    cs_mod.factor = 0.55
    cs_mod.iterations = 6
    cs_mod.smooth_type = "LENGTH_WEIGHTED"
    cs_mod.use_pin_boundary = True

    return ob, arm_ob, orig_vi_arr, hand_st_arr, hand_tris_arr, srgb_path


# ==============================================================================
# 4. 60-FRAME BIOMECHANICAL ANIMATION & BLENDER PREVIEW RENDERS
# ==============================================================================
def build_60_frames_and_previews(ob, arm_ob, orig_vi_arr, hand_st, hand_tris, srgb_path, out_dir, out_npz):
    disk_v0, disk_n0, disk_st, disk_tris = build_floppy_disk_data(half_w=0.232, half_h=0.242, half_t=0.0155)

    # Combine Hand + Disk into ONE single MD3 surface (eliminates DarkPlaces multi-surface UV bug!)
    n_hv = len(orig_vi_arr)
    comb_st = np.vstack([hand_st, disk_st])
    comb_tris = np.vstack([hand_tris, disk_tris + n_hv])
    print(f"  [SURFACE OK] Single-surface v_netsend: {len(comb_st)} total verts, {len(comb_tris)} total tris")

    # ==========================================================================
    # WORLD BASIS & HAND SCALE IN QUAKE EYE SPACE (+X fwd, +Y left, +Z up)
    # ==========================================================================
    # Aligned so palm (-X_hand) faces the player/disk back closely, eliminating finger air gaps!
    Z_h = np.array([ 0.14,  0.58,  0.80], dtype=np.float64)
    Z_h /= np.linalg.norm(Z_h)
    X_h = np.array([ 0.88, -0.44,  0.18], dtype=np.float64)
    X_h = X_h - Z_h * np.dot(X_h, Z_h)
    X_h /= np.linalg.norm(X_h)
    Y_h = np.cross(Z_h, X_h)  # right-handed: X_h x Y_h = Z_h -> det(R_base) = +1.0!
    R_base = np.column_stack([X_h, Y_h, Z_h])
    assert abs(np.linalg.det(R_base) - 1.0) < 1e-6

    SCALE = 14.2  # Adult male hand (~13.6 Quake units wrist-to-tip) + 6.6x6.9 floppy disk!
    WRIST_BASE = np.array([13.2, -13.2, -6.8], dtype=np.float64)

    pb_ix1 = arm_ob.pose.bones["ix_1"]
    b_x_in_arm = np.array(pb_ix1.bone.matrix_local.col[0][:3])
    b_y_in_arm = np.array(pb_ix1.bone.matrix_local.col[1][:3])
    cross_xy = np.cross(b_x_in_arm, b_y_in_arm)
    FLEX_SIGN = -1.0 if cross_xy[0] > 0.0 else +1.0

    pb_th1 = arm_ob.pose.bones["th_1"]
    th_cross_xy = np.cross(np.array(pb_th1.bone.matrix_local.col[0][:3]), np.array(pb_th1.bone.matrix_local.col[1][:3]))
    TH_FLEX_SIGN = -1.0 if th_cross_xy[0] > 0.0 else +1.0
    print(f"  [BONE AXES] Finger palmar flex sign={FLEX_SIGN:+.0f}, Thumb palmar flex sign={TH_FLEX_SIGN:+.0f}")

    def f_curl(deg_1, deg_2, deg_3, splay_z=0.0):
        return (
            (FLEX_SIGN * deg_1, 0.0, splay_z),
            (FLEX_SIGN * deg_2, 0.0, 0.0),
            (FLEX_SIGN * deg_3, 0.0, 0.0),
        )

    def rot_x_m(deg):
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float64)

    def rot_y_m(deg):
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float64)

    def rot_z_m(deg):
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)

    def apply_pose(eulers):
        for pb in arm_ob.pose.bones:
            pb.rotation_mode = "XYZ"
            rx, ry, rz = eulers.get(pb.name, (0.0, 0.0, 0.0))
            pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
        bpy.context.view_layer.update()

    # Initial ergonomic curl cascade before exact closed-loop contact calibration
    cal_curls = {
        "ix": [24.0, 32.0, 26.0, -5.0],
        "md": [28.0, 38.0, 28.0, -1.0],
        "rg": [34.0, 44.0, 32.0, +3.0],
        "pk": [42.0, 52.0, 36.0, +7.0],
    }
    TH_BASE = ((20.0, 10.0, -16.0), (16.0, 0.0, 0.0), (18.0, 0.0, 0.0))

    def build_pose_dict(wrist_rot=(0.0, 0.0, 0.0), palm_rot=(0.0, 0.0, 0.0), ix=None, md=None, rg=None, pk=None, th=None):
        ix = ix if ix is not None else tuple(cal_curls["ix"])
        md = md if md is not None else tuple(cal_curls["md"])
        rg = rg if rg is not None else tuple(cal_curls["rg"])
        pk = pk if pk is not None else tuple(cal_curls["pk"])
        th = th if th is not None else TH_BASE
        ix1, ix2, ix3 = f_curl(*ix)
        md1, md2, md3 = f_curl(*md)
        rg1, rg2, rg3 = f_curl(*rg)
        pk1, pk2, pk3 = f_curl(*pk)
        t1, t2, t3 = th
        return {
            "forearm": (0.0, 0.0, 0.0),
            "wrist":   wrist_rot,
            "palm":    palm_rot,
            "ix_1": ix1, "ix_2": ix2, "ix_3": ix3,
            "md_1": md1, "md_2": md2, "md_3": md3,
            "rg_1": rg1, "rg_2": rg2, "rg_3": rg3,
            "pk_1": pk1, "pk_2": pk2, "pk_3": pk3,
            "th_1": (TH_FLEX_SIGN * t1[0], t1[1], t1[2]),
            "th_2": (TH_FLEX_SIGN * t2[0], t2[1], t2[2]),
            "th_3": (TH_FLEX_SIGN * t3[0], t3[1], t3[2]),
        }

    # Establish rest Disk transform anchored to the posed Thumb pad on the front lower-right corner
    apply_pose(build_pose_dict())
    th_tip_arm = np.array(arm_ob.pose.bones["th_3"].tail[:], dtype=np.float64)
    R_disk_q0 = rot_z_m(20.0) @ rot_y_m(-6.0) @ rot_x_m(-3.0)
    M_palm0 = np.array(arm_ob.pose.bones["palm"].matrix, dtype=np.float64)
    R_palm0_arm = M_palm0[:3, :3]
    p_palm0_arm = M_palm0[:3, 3]
    R_disk_in_arm0 = R_base.T @ R_disk_q0

    thumb_anchor_local = np.array([-0.044, -0.168, -0.150], dtype=np.float64)
    p_disk_in_arm0 = th_tip_arm - R_disk_in_arm0 @ thumb_anchor_local

    # Closed-loop 4-finger physical contact solver: adjusts MCP/PIP flexion so every finger pad
    # rests FLUSH against the back shell (+0.041) or beveled rim (+0.026) with ZERO air gap or poke-through!
    for _it in range(10):
        apply_pose(build_pose_dict())
        for fnm in ("ix", "md", "rg", "pk"):
            fpt = np.array(arm_ob.pose.bones[f"{fnm}_3"].tail[:], dtype=np.float64)
            d_loc = R_disk_in_arm0.T @ (fpt - p_disk_in_arm0)
            inside_face = (abs(d_loc[1]) <= 0.228) and (abs(d_loc[2]) <= 0.238)
            tgt_x = 0.041 if inside_face else 0.026
            err_x = d_loc[0] - tgt_x  # >0 means behind disk -> flex more; <0 means too far forward -> uncurl!
            cal_curls[fnm][0] = float(np.clip(cal_curls[fnm][0] + err_x * 62.0, 2.0, 68.0))
            cal_curls[fnm][1] = float(np.clip(cal_curls[fnm][1] + err_x * 42.0, 6.0, 78.0))

    make_grip_pose = build_pose_dict
    apply_pose(make_grip_pose())

    print("  [GRIP CHECK] Calibrated 5-digit physical contact in Disk local (T=+-0.016, W=+-0.232, H=+-0.242):")
    for fnm in ("th", "ix", "md", "rg", "pk"):
        fpt = np.array(arm_ob.pose.bones[f"{fnm}_3"].tail[:], dtype=np.float64)
        d_loc = R_disk_in_arm0.T @ (fpt - p_disk_in_arm0)
        print(f"    {fnm}_tip -> disk_local={np.round(d_loc, 3)} | curl={np.round(cal_curls[fnm], 1) if fnm != 'th' else 'TH_BASE'}")

    # Express disk rest transform relative to `palm` bone (`M_palm0`) so any wrist/palm rotation carries the disk!
    R_disk_rel_palm = R_palm0_arm.T @ R_disk_in_arm0
    p_disk_rel_palm = R_palm0_arm.T @ (p_disk_in_arm0 - p_palm0_arm)
    C_disk0_q = (p_disk_in_arm0 * SCALE) @ R_base.T + WRIST_BASE

    depsgraph = bpy.context.evaluated_depsgraph_get()
    all_verts = np.zeros((60, len(comb_st), 3), dtype=np.float64)
    all_norms = np.zeros((60, len(comb_st), 3), dtype=np.float64)
    frame_names = []

    ix0, md0, rg0, pk0 = (tuple(cal_curls[k]) for k in ("ix", "md", "rg", "pk"))

    for f in range(60):
        wrist_pos_q = WRIST_BASE.copy()
        R_world = R_base.copy()
        pose_eulers = make_grip_pose()
        disk_visible = True
        disk_extra_local_rot = np.eye(3, dtype=np.float64)
        disk_extra_local_ofs = np.zeros(3, dtype=np.float64)

        if f <= 39:
            ph = 2.0 * math.pi * (f / 40.0)
            bob_y = 0.15 * math.sin(ph)
            bob_z = 0.18 * math.sin(ph * 2.0)
            wrist_pos_q += np.array([0.0, bob_y, bob_z])

            if f <= 7:
                frame_names.append(f"idle_{f:02d}")
                pose_eulers = make_grip_pose(
                    wrist_rot=(1.5 * math.sin(ph), 2.0 * math.sin(ph), 0.0),
                )

            elif f <= 22:
                # 8..22: Natural forearm/wrist pronation flip (~162 deg) with roll compensation so the
                # rear brushed-steel shutter & radial spindle hub sit upright beside the dorsal hand & nails!
                frame_names.append(f"flip_{f:02d}")
                u = (f - 8) / 14.0
                if u < 0.36:
                    k = smoother(u / 0.36)
                elif u <= 0.64:
                    k = 1.0 + 0.03 * math.sin(math.pi * (u - 0.36) / 0.28)
                else:
                    k = 1.0 - smoother((u - 0.64) / 0.36)

                lift = math.sin(math.pi * u)
                # Forearm pronation (-162 deg around Z_h) + Quake-roll (-32 deg) so shutter stays upright at top!
                R_world = rot_x_m(-32.0 * k) @ R_base @ rot_z_m(-162.0 * k)
                # Anchor disk center forward (+8.6 fwd, +3.8 left, -1.7 down) so the pronated dorsal hand,
                # MCP knuckles, veins, wrist, AND rear spindle hub all sit at natural eye scale inside 16:9!
                C_tgt_q = C_disk0_q + np.array([+8.6 * k, +3.8 * k, +0.2 * lift - 1.7 * k])
                wrist_pos_q = C_tgt_q - ((p_disk_in_arm0 * SCALE) @ R_world.T) + np.array([0.0, bob_y, bob_z])
                pose_eulers = make_grip_pose(
                    wrist_rot=(3.0 * lift, 0.0, -4.0 * lift),
                )

            elif f <= 33:
                # 23..33: Smug tilt closer to eye + index finger double-tap on the back/left rim!
                frame_names.append(f"inspect_{f:02d}")
                u = (f - 23) / 10.0
                env = math.sin(math.pi * u) ** 0.8
                tap_phase = max(0.0, min(1.0, (u - 0.16) / 0.68))
                ix_lift = max(0.0, math.sin(tap_phase * 2.0 * math.pi * 2.0)) * env
                wrist_pos_q += np.array([-0.75 * env, 0.85 * env, 0.55 * env])
                pose_eulers = make_grip_pose(
                    wrist_rot=(-4.0 * env, 5.0 * env, 3.5 * env),
                    ix=(ix0[0] - 11.0 * ix_lift, ix0[1] - 12.0 * ix_lift, ix0[2] - 8.0 * ix_lift, ix0[3] - 1.5 * env),
                )

            else:
                frame_names.append(f"idle_{f:02d}")
                pose_eulers = make_grip_pose(
                    wrist_rot=(1.5 * math.sin(ph), 2.0 * math.sin(ph), 0.0),
                )

        elif f <= 47:
            # 40..47: Visceral Sidearm Frisbee / Card Flick-Throw! Disk stays in full view during windup & releases at 44!
            frame_names.append(f"throw_{f:02d}")
            if f <= 42:
                # 40..42: Cock wrist inward-left & UP into lower-center-right view, tilting disk into sidearm launch plane!
                k = smoother((f - 39) / 3.0)
                R_world = rot_z_m(+22.0 * k) @ rot_x_m(+26.0 * k) @ R_base @ rot_z_m(-24.0 * k)
                C_cock_q = C_disk0_q + np.array([-0.7 * k, +2.6 * k, +1.2 * k])
                wrist_pos_q = C_cock_q - ((p_disk_in_arm0 * SCALE) @ R_world.T)
                pose_eulers = make_grip_pose(
                    wrist_rot=(+8.0 * k, +10.0 * k, -10.0 * k),
                    ix=(ix0[0] + 6.0 * k, ix0[1] + 8.0 * k, ix0[2] + 4.0 * k, ix0[3]),
                    md=(md0[0] + 6.0 * k, md0[1] + 8.0 * k, md0[2] + 4.0 * k, md0[3]),
                )
            elif f == 43:
                # 43: Explosive forward wrist-snap whip toward crosshair! Disk launching off index & thumb tips!
                R_world = rot_z_m(-14.0) @ rot_x_m(+14.0) @ R_base @ rot_z_m(-44.0)
                wrist_pos_q = WRIST_BASE + np.array([+1.1, +2.2, +1.5])
                pose_eulers = make_grip_pose(
                    wrist_rot=(+18.0, -8.0, +12.0),
                    ix=(8.0, 12.0, 9.0, -8.0),
                    md=(12.0, 16.0, 12.0, -2.0),
                    rg=(20.0, 26.0, 18.0, +4.0),
                    pk=(28.0, 36.0, 24.0, +9.0),
                    th=((10.0, 5.0, -8.0), (8.0, 0.0, 0.0), (8.0, 0.0, 0.0)),
                )
                disk_extra_local_ofs = np.array([0.01, +0.15, +0.11])
            else:
                # 44..47: RELEASED! World disk spawns at 44; viewmodel disk hidden; realistic splayed follow-through!
                disk_visible = False
                u = smoother((f - 44) / 3.0)
                wrist_pos_q = WRIST_BASE + (1.0 - 0.55 * u) * np.array([+1.5, +2.4, +1.6]) + (0.55 * u) * np.array([+0.5, +1.6, +1.2])
                R_world = rot_z_m(-18.0 * (1.0 - u)) @ rot_x_m(+10.0 * (1.0 - u)) @ R_base @ rot_z_m(-48.0 + 22.0 * u)
                pose_eulers = make_grip_pose(
                    wrist_rot=(+22.0 - 12.0 * u, -8.0 + 4.0 * u, +14.0 - 7.0 * u),
                    ix=(5.0 + 9.0 * u, 8.0 + 12.0 * u, 6.0 + 9.0 * u, -9.0 + 3.0 * u),
                    md=(8.0 + 11.0 * u, 11.0 + 15.0 * u, 8.0 + 10.0 * u, -2.0),
                    rg=(14.0 + 14.0 * u, 18.0 + 18.0 * u, 14.0 + 12.0 * u, +4.0),
                    pk=(20.0 + 18.0 * u, 26.0 + 20.0 * u, 20.0 + 14.0 * u, +9.5),
                    th=((8.0 + 7.0 * u, 5.0, -7.0), (6.0 + 6.0 * u, 0.0, 0.0), (6.0 + 6.0 * u, 0.0, 0.0)),
                )

        elif f <= 53:
            # 48..53: Smooth recovery into natural, poised empty-hand ready stance at Frame 53
            # (Remember: `funguns.qc` holds Frame 53 while waiting for ammo regeneration!)
            frame_names.append(f"empty_{f:02d}")
            disk_visible = False
            u = smoother((f - 47) / 6.0)
            p_start = WRIST_BASE + np.array([+0.95, +1.96, +1.38])
            p_ready = WRIST_BASE + np.array([+0.20, +1.45, +1.15])
            wrist_pos_q = (1.0 - u) * p_start + u * p_ready
            R_world = R_base @ rot_z_m(-26.0 * (1.0 - u) - 10.0 * u)
            pose_eulers = make_grip_pose(
                wrist_rot=(+10.0 * (1.0 - u) - 3.0 * u, -4.0 * (1.0 - u) + 3.0 * u, +7.0 * (1.0 - u)),
                ix=(14.0 + 4.0 * u, 20.0 + 6.0 * u, 15.0 + 5.0 * u, -6.0),
                md=(19.0 + 5.0 * u, 26.0 + 8.0 * u, 18.0 + 6.0 * u, -1.5),
                rg=(28.0 + 5.0 * u, 36.0 + 6.0 * u, 26.0 + 5.0 * u, +3.5),
                pk=(38.0 + 4.0 * u, 46.0 + 5.0 * u, 34.0 + 4.0 * u, +8.5),
                th=((15.0, 8.0, -10.0), (12.0, 0.0, 0.0), (12.0, 0.0, 0.0)),
            )

        else:
            # 54..59: Dip to pocket (54..55) & snatch fresh LOL.BAT floppy disk up into idle hold (56..59 -> 0)!
            frame_names.append(f"reload_{f:02d}")
            if f in (54, 55):
                disk_visible = False
                k = 0.55 if f == 54 else 1.0
                wrist_pos_q = WRIST_BASE + np.array([+0.20 - 1.1 * k, +1.45 - 3.4 * k, +1.15 - 5.8 * k])
                R_world = R_base @ rot_z_m(-10.0 + 10.0 * k)
                pose_eulers = make_grip_pose()
            else:
                disk_visible = True
                offs_map = {
                    56: np.array([-0.8, -2.0, -4.2]),
                    57: np.array([-0.3, -0.8, -1.6]),
                    58: np.array([+0.1, +0.2, +0.30]),
                    59: np.array([ 0.0, +0.04, +0.05]),
                }
                wrist_pos_q = WRIST_BASE + offs_map[f]
                pose_eulers = make_grip_pose()

        apply_pose(pose_eulers)
        eval_ob = ob.evaluated_get(depsgraph)
        me_eval = eval_ob.to_mesh()
        V_arm = np.array([v.co[:] for v in me_eval.vertices], dtype=np.float64)
        N_arm = np.array([v.normal[:] for v in me_eval.vertices], dtype=np.float64)
        eval_ob.to_mesh_clear()

        V_hand_q = (V_arm[orig_vi_arr] * SCALE) @ R_world.T + wrist_pos_q[None, :]
        N_hand_q = N_arm[orig_vi_arr] @ R_world.T
        N_hand_q /= np.linalg.norm(N_hand_q, axis=1, keepdims=True) + 1e-12

        if disk_visible:
            M_palm_f = np.array(arm_ob.pose.bones["palm"].matrix, dtype=np.float64)
            R_palm_f = M_palm_f[:3, :3]
            p_palm_f = M_palm_f[:3, 3]
            R_disk_arm_f = R_palm_f @ R_disk_rel_palm @ disk_extra_local_rot
            p_disk_arm_f = p_palm_f + R_palm_f @ p_disk_rel_palm + R_disk_arm_f @ disk_extra_local_ofs

            V_disk_arm = disk_v0 @ R_disk_arm_f.T + p_disk_arm_f[None, :]
            V_disk_q = (V_disk_arm * SCALE) @ R_world.T + wrist_pos_q[None, :]
            N_disk_q = (disk_n0 @ R_disk_arm_f.T) @ R_world.T
            N_disk_q /= np.linalg.norm(N_disk_q, axis=1, keepdims=True) + 1e-12
        else:
            # Collapse zero-area off-screen behind/below view so single-surface topology stays constant!
            V_disk_q = np.broadcast_to(np.array([[-8.0, -20.0, -20.0]], dtype=np.float64), disk_v0.shape).copy()
            N_disk_q = np.broadcast_to(np.array([[-1.0, 0.0, 0.0]], dtype=np.float64), disk_n0.shape).copy()

        all_verts[f, :n_hv, :] = V_hand_q
        all_verts[f, n_hv:, :] = V_disk_q
        all_norms[f, :n_hv, :] = N_hand_q
        all_norms[f, n_hv:, :] = N_disk_q

    np.savez_compressed(
        out_npz,
        verts=all_verts.astype(np.float32),
        norms=all_norms.astype(np.float32),
        st=comb_st.astype(np.float32),
        tris=comb_tris.astype(np.int32),
        frame_names=np.array(frame_names),
    )
    print(f"  [ANIM OK] Exported 60 frames -> {out_npz}")

    # ==========================================================================
    # RENDER BLENDER EEVEE/CYCLES PREVIEW FRAMES FOR IMMEDIATE VISUAL CHECK!
    # ==========================================================================
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 20

    scene.world = bpy.data.worlds.new("PrevWorld")
    scene.world.use_nodes = True
    w_bg = scene.world.node_tree.nodes.get("Background")
    w_bg.inputs["Color"].default_value = (0.14, 0.16, 0.20, 1.0)
    w_bg.inputs["Strength"].default_value = 1.0

    # Create preview mesh with shape keys for all 60 frames!
    me_p = bpy.data.meshes.new("VMPreviewMesh")
    me_p.from_pydata([tuple(p) for p in all_verts[0]], [], [tuple(t) for t in comb_tris])
    me_p.polygons.foreach_set("use_smooth", [True] * len(me_p.polygons))
    uv_l = me_p.uv_layers.new(name="UVMap")
    for poly in me_p.polygons:
        for lp_i in poly.loop_indices:
            vi = me_p.loops[lp_i].vertex_index
            u, v = comb_st[vi]
            uv_l.data[lp_i].uv = (float(u), float(1.0 - v))
    me_p.update()

    ob_p = bpy.data.objects.new("VMPreview", me_p)
    bpy.context.collection.objects.link(ob_p)

    # Use crisp mix of 75% Emission + 25% Diffuse so preview renders match DarkPlaces lighting fidelity!
    mat_p = bpy.data.materials.new("VMMat")
    mat_p.use_nodes = True
    nt = mat_p.node_tree
    nt.nodes.clear()
    out_n = nt.nodes.new("ShaderNodeOutputMaterial")
    tex_n = nt.nodes.new("ShaderNodeTexImage")
    tex_n.image = bpy.data.images.load(srgb_path)
    bsdf_n = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_n.inputs["Roughness"].default_value = 0.55
    em_n = nt.nodes.new("ShaderNodeEmission")
    em_n.inputs["Strength"].default_value = 0.55
    add_s = nt.nodes.new("ShaderNodeAddShader")
    mul_c = nt.nodes.new("ShaderNodeVectorMath")
    mul_c.operation = "SCALE"
    mul_c.inputs["Scale"].default_value = 0.55
    nt.links.new(mul_c.inputs[0], tex_n.outputs["Color"])
    nt.links.new(bsdf_n.inputs["Base Color"], mul_c.outputs["Vector"])
    nt.links.new(em_n.inputs["Color"], tex_n.outputs["Color"])
    nt.links.new(add_s.inputs[0], bsdf_n.outputs["BSDF"])
    nt.links.new(add_s.inputs[1], em_n.outputs["Emission"])
    nt.links.new(out_n.inputs["Surface"], add_s.outputs["Shader"])
    ob_p.data.materials.append(mat_p)

    for lname, lpos, lpow in (("PKey", (4.0, -4.0, 10.0), 180.0), ("PFill", (20.0, -18.0, 4.0), 120.0)):
        ld = bpy.data.lights.new(lname, type="POINT")
        ld.energy = lpow
        ld.shadow_soft_size = 3.0
        lo = bpy.data.objects.new(lname, ld)
        bpy.context.collection.objects.link(lo)
        lo.location = lpos

    cam_d = bpy.data.cameras.new("FPCam")
    cam_o = bpy.data.objects.new("FPCam", cam_d)
    bpy.context.collection.objects.link(cam_o)
    scene.camera = cam_o

    def set_frame_verts(fi):
        for idx, v in enumerate(me_p.vertices):
            v.co = tuple(all_verts[fi, idx])
        me_p.update()

    # 1. Render 12 First-Person POV frames at DarkPlaces game FOV (fov 105 on 4:3 -> ~120 deg H-FOV on 16:9!)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    cam_d.lens_unit = "FOV"
    cam_d.angle = math.radians(114.0)
    cam_o.location = (0.0, 0.0, 0.0)
    # Look straight down +X_q with +Z_q up and +Y_q left!
    cam_dir = mathutils.Vector((1.0, 0.0, 0.0))
    cam_o.rotation_euler = cam_dir.to_track_quat("-Z", "Y").to_euler()

    for fi in (0, 10, 15, 20, 28, 39, 42, 43, 44, 50, 53, 57):
        set_frame_verts(fi)
        scene.render.filepath = os.path.join(out_dir, f"vm_fp_{fi:02d}.png")
        bpy.ops.render.render(write_still=True)

    # Also render a full 1280x720 hero FP shot of frame 0 and frame 15!
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    for fi in (0, 15, 53):
        set_frame_verts(fi)
        scene.render.filepath = os.path.join(out_dir, f"vm_hero_fp_{fi:02d}.png")
        bpy.ops.render.render(write_still=True)

    # 2. Render 6 Close-Up Anatomical & Grip Inspection Angles!
    scene.render.resolution_x = 720
    scene.render.resolution_y = 540
    cam_d.angle = math.radians(52.0)

    target_f0 = mathutils.Vector((12.4, -10.2, -3.6))
    closeups = [
        (0,  ( 2.0,  -4.5,  0.2), target_f0),   # 0: 1st-person close-up
        (0,  ( 5.0, -20.5, -1.0), target_f0),   # 1: Radial thumb-web & thumbnail
        (0,  (22.5, -17.5, -0.5), target_f0),   # 2: Dorsal knuckles, veins & fingernails
        (0,  (23.5,  -4.5, -1.5), target_f0),   # 3: Rear floppy hub & flush 4-finger contact
        (53, ( 2.5,  -4.5, -1.5), mathutils.Vector((12.5, -10.0, -4.2))),  # 4: Empty hand palmar creases & fingertips
        (15, ( 2.5,  -4.5,  0.2), mathutils.Vector((13.8,  -9.2, -3.4))),  # 5: Flipped f15 dorsal + hub inspection
    ]
    for ci, (fi, cpos, ctgt) in enumerate(closeups):
        set_frame_verts(fi)
        cam_o.location = cpos
        dvec = ctgt - mathutils.Vector(cpos)
        cam_o.rotation_euler = dvec.to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(out_dir, f"vm_closeup_{ci}.png")
        bpy.ops.render.render(write_still=True)

    print("  [RENDER OK] All FP & anatomical close-up previews rendered!")


def main():
    argv = sys.argv
    idx = argv.index("--")
    strip_png, out_dir, out_npz = argv[idx + 1], argv[idx + 2], argv[idx + 3]

    ob, arm_ob, orig_vi_arr, hand_st, hand_tris, srgb_path = build_bake_and_rig(strip_png, out_dir)
    build_60_frames_and_previews(ob, arm_ob, orig_vi_arr, hand_st, hand_tris, srgb_path, out_dir, out_npz)


if __name__ == "__main__":
    main()
