"""Sculpts, unwraps, bakes realistic human skin for, and rigs a seamless 1-piece
anatomical male right hand & muscular forearm in Blender 5.2.

Architecture:
  1. Pure-quad watertight manifold anatomical control cage (forearm -> wrist styloid ->
     broad masculine palm w/ thenar/hypothenar pads -> 3 sloped interdigital finger webs ->
     4 arched fingers + opposable thumb -> 5 inset 3D fingernails & cuticle folds).
  2. Catmull-Clark Subdivision Surface (Level 2) + subtle 3D anatomical tendon/knuckle/crease relief.
  3. Clean UV unwrap + Cycles Ambient Occlusion bake + 3D rest-space anatomical skin synthesis
     (warm natural sunlit male skin, subsurface rosy knuckles/fingertips/palm pads, subtle dorsal veins,
     realistic pale keratin nails with lunula crescents — zero cartoon lines or muddy brown!).
  4. UV-preserving quadric decimation (~2,500 verts / ~4,950 tris, < MD3 4096v/8192t limit).
  5. Real 18-bone Blender Armature with C++ Heat-Diffusion Automatic Weights (`ARMATURE_AUTO`)
     + Volume-Preserving `CORRECTIVE_SMOOTH` modifier for studio-grade pose deformation!
"""
import math
import os
import numpy as np
import bpy
import bmesh
import mathutils


def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0 + 1e-12)))
    return t * t * (3.0 - 2.0 * t)


def sstep_np(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ===========================================================================
# ANATOMICAL JOINT POSITIONS (Right-Handed Rest Frame:
#   Origin (0,0,0) = Wrist center
#   +Z = Distal along middle metacarpal / fingers
#   -X = PALM (volar); +X = DORSAL (back of hand & nails)
#   -Y = RADIAL (thumb side); +Y = ULNAR (pinky side)
# )
# ===========================================================================
HAND_JOINTS = {
    "forearm": np.array([ 0.010,  0.018, -1.320]),
    "wrist":   np.array([ 0.000,  0.000,  0.000]),
    "palm":    np.array([ 0.000, -0.004,  0.175]),
    # Opposable Thumb (abducted cleanly in natural relaxed 42° radial-palmar opposition)
    "th_1":    np.array([-0.042, -0.155,  0.115]),
    "th_2":    np.array([-0.075, -0.285,  0.245]),
    "th_3":    np.array([-0.095, -0.375,  0.365]),
    "th_tip":  np.array([-0.108, -0.448,  0.472]),
    # Index Finger (slight radial fan -9°)
    "ix_1":    np.array([ 0.002, -0.156,  0.448]),
    "ix_2":    np.array([-0.004, -0.184,  0.642]),
    "ix_3":    np.array([-0.010, -0.202,  0.778]),
    "ix_tip":  np.array([-0.015, -0.218,  0.898]),
    # Middle Finger (longest, -2° fan)
    "md_1":    np.array([ 0.008, -0.050,  0.468]),
    "md_2":    np.array([ 0.002, -0.058,  0.682]),
    "md_3":    np.array([-0.004, -0.064,  0.828]),
    "md_tip":  np.array([-0.010, -0.069,  0.955]),
    # Ring Finger (+5° ulnar fan)
    "rg_1":    np.array([ 0.003,  0.054,  0.445]),
    "rg_2":    np.array([-0.003,  0.072,  0.642]),
    "rg_3":    np.array([-0.009,  0.084,  0.778]),
    "rg_tip":  np.array([-0.014,  0.095,  0.898]),
    # Pinky Finger (+13° ulnar fan)
    "pk_1":    np.array([-0.006,  0.148,  0.400]),
    "pk_2":    np.array([-0.012,  0.182,  0.552]),
    "pk_3":    np.array([-0.018,  0.206,  0.660]),
    "pk_tip":  np.array([-0.023,  0.228,  0.762]),
}


def build_seamless_hand_cage_bmesh():
    """Constructs a 100% pure-quad, watertight manifold control cage of a male right hand & forearm."""
    bm = bmesh.new()

    # 8 Y-grid lines defining 4 sturdy masculine finger columns (0, 2, 4, 6) + 3 interdigital web clefts (1, 3, 5)
    y_knuckle = np.array([-0.214, -0.122, -0.098, -0.008, 0.016, 0.102, 0.124, 0.204], dtype=np.float64)
    # 3 X-grid lines: 0 = Palmar (-X), 1 = Midplane (0), 2 = Dorsal (+X)
    x_norm = np.array([-1.0, 0.0, 1.0], dtype=np.float64)

    # Ordered 18-index perimeter of an (8 x 3) grid (CCW when viewed from +Z distal so normals face OUTWARD!):
    # Let's check CCW around +Z (+X right, +Y up):
    #   +X dorsal edge: iy from 0 -> 7 at ix=2 (tangent +Y, cross +Z -> +X outward? Wait: (+Y) x (+Z_extrude) = +X! YES!)
    #   +Y ulnar edge:  ix from 2 -> 0 at iy=7 (tangent -X, (-X) x (+Z) = +Y outward! YES!)
    #   -X palmar edge: iy from 7 -> 0 at ix=0 (tangent -Y, (-Y) x (+Z) = -X outward! YES!)
    #   -Y radial edge: ix from 0 -> 2 at iy=0 (tangent +X, (+X) x (+Z) = -Y outward! YES!)
    perim_ij = (
        [(iy, 2) for iy in range(0, 8)] +      # 0..7   dorsal (+X)
        [(7, 1)] +                             # 8      ulnar mid (+Y)
        [(iy, 0) for iy in range(7, -1, -1)] + # 9..16  palmar (-X)
        [(0, 1)]                               # 17     radial mid (-Y)
    )
    assert len(perim_ij) == 18

    # 10 axial stations from full proximal muscular forearm (z = -1.32, exits off-screen cleanly!) up to MCP knuckle arch (+0.435)
    # (z, half_width_scale, half_thick, cy_shift, cx_shift, roundness)
    stations = [
        (-1.320, 1.08, 0.168,  0.020,  0.008, 0.94),  # 0: muscular upper forearm (well past viewport edge — no stump!)
        (-0.820, 1.03, 0.156,  0.014,  0.006, 0.91),  # 1: brachioradialis / flexor belly swell
        (-0.420, 0.90, 0.134,  0.009,  0.003, 0.86),  # 2: mid-distal forearm taper
        (-0.150, 0.80, 0.112,  0.004,  0.001, 0.78),  # 3: above wrist
        (-0.035, 0.77, 0.102,  0.002,  0.000, 0.72),  # 4: sturdy masculine wrist + ulnar styloid
        ( 0.045, 0.81, 0.106,  0.000, -0.005, 0.58),  # 5: carpal heel (thumb socket bottom!)
        ( 0.145, 0.93, 0.114, -0.010, -0.010, 0.45),  # 6: thumb socket mid / meaty thenar swell
        ( 0.255, 1.00, 0.108, -0.010, -0.006, 0.36),  # 7: thumb socket top / mid palm
        ( 0.355, 1.02, 0.096, -0.004, -0.002, 0.28),  # 8: distal palm hollow
        ( 0.435, 1.01, 0.082,  0.000,  0.000, 0.22),  # 9: broad masculine MCP knuckle arch!
    ]

    def eval_station_grid(st_idx):
        z0, w_sc, h_thk, cy, cx, rnd = stations[st_idx]
        grid_pts = np.zeros((8, 3, 3), dtype=np.float64)
        for iy in range(8):
            yn = (y_knuckle[iy] + 0.006) / 0.198  # normalized in [-1, +1]
            for ix in range(3):
                xn = x_norm[ix]  # -1, 0, +1
                # Blend rectangular hand palm cross-section with elliptical forearm cross-section!
                ang = math.atan2(yn, xn + 1e-9)
                r_box_y = y_knuckle[iy] * w_sc
                r_box_x = xn * h_thk
                # Elliptical cross-section at same perimeter parameter
                ell_y = 0.198 * w_sc * math.sin(ang) if (ix in (0, 2) or iy in (0, 7)) else r_box_y
                ell_x = h_thk * math.cos(ang) if (ix in (0, 2) or iy in (0, 7)) else r_box_x
                # Smooth corner rounding on palm too so side edges (ix=0,2 at iy=0,7) are rounded, never sharp!
                if iy in (0, 7) and ix in (0, 2):
                    r_box_x *= 0.72
                    r_box_y *= 0.92
                elif ix in (0, 2) and iy not in (0, 7):
                    # Gentle arch across dorsal back (+X) & palmar cup (-X)
                    arch = 1.0 - 0.14 * (yn * yn)
                    r_box_x *= arch

                x = cx + (1.0 - rnd) * r_box_x + rnd * ell_x
                y = cy + (1.0 - rnd) * r_box_y + rnd * ell_y
                z = z0

                # Anatomical sculpting on wrist & palm!
                # 1. Ulnar styloid wrist bone bump on +Y dorsal-ulnar wrist (st_idx == 4)
                if st_idx in (3, 4) and iy >= 6 and ix >= 1:
                    styl = (1.0 if st_idx == 4 else 0.45) * (0.6 if ix == 1 else 0.85)
                    y += 0.014 * styl
                    x += 0.008 * styl

                # 2. Muscular Thenar thumb-pad bulge on radial-palmar palm (st_idx 5..7, iy <= 2, ix <= 1)
                if st_idx in (5, 6, 7) and iy <= 3 and ix <= 1:
                    w_th = {5: 0.55, 6: 1.0, 7: 0.70}[st_idx] * max(0.0, 1.0 - iy / 3.2)
                    if ix == 0:
                        x -= 0.038 * w_th
                    y -= 0.022 * w_th

                # 3. Muscular Hypothenar pad along ulnar-palmar heel (st_idx 5..8, iy >= 5, ix == 0)
                if st_idx in (5, 6, 7, 8) and iy >= 5 and ix == 0:
                    w_hy = {5: 0.65, 6: 1.0, 7: 0.85, 8: 0.45}[st_idx] * ((iy - 4) / 3.0)
                    x -= 0.024 * w_hy
                    y += 0.008 * w_hy

                # 4. Central Palmar Hollow (st_idx 7..8, iy in 2..5, ix == 0)
                if st_idx in (7, 8) and 2 <= iy <= 5 and ix == 0:
                    x += 0.018 * (1.0 if st_idx == 7 else 0.7)

                # 5. Curved MCP Knuckle Arch & Dorsal Knuckle Hills (st_idx 8..9)
                if st_idx >= 8:
                    k_fac = 0.45 if st_idx == 8 else 1.0
                    # Middle finger knuckle highest (+0.026), index (+0.008), ring (+0.005), pinky lowest (-0.038)!
                    arch_z = 0.024 - 0.022 * ((yn + 0.22) ** 2) * 1.9
                    if iy >= 5:
                        arch_z -= 0.018 * ((iy - 4) / 3.0)
                    z += k_fac * arch_z
                    # Dorsal MCP knuckle prominences on finger columns (0..1, 2..3, 4..5, 6..7)
                    if st_idx == 9 and ix == 2:
                        in_cleft = iy in (1, 2, 3, 4, 5, 6)
                        # Valley dip in cleft edges vs knuckle crown
                        if iy in (0, 7):
                            x += 0.006
                        else:
                            x += 0.014

                grid_pts[iy, ix] = (x, y, z)
        return grid_pts

    # Build vertex grids for stations 0 (full 8x3 for clean base cap), 1..8 (perimeter 18), and 9 (full 8x3 for finger sockets!)
    ring_verts = []
    grid0_bm = [[None] * 3 for _ in range(8)]
    g0 = eval_station_grid(0)
    for iy in range(8):
        for ix in range(3):
            grid0_bm[iy][ix] = bm.verts.new(tuple(g0[iy, ix]))
    # Cap proximal forearm at st_idx=0 (outward normal -Z -> reverse quad winding!)
    for iy in range(7):
        for ix in range(2):
            v00 = grid0_bm[iy][ix]
            v10 = grid0_bm[iy + 1][ix]
            v11 = grid0_bm[iy + 1][ix + 1]
            v01 = grid0_bm[iy][ix + 1]
            # Check normal: (v01 - v00) = +X, (v10 - v00) = +Y -> (+X) x (+Y) = +Z, so (v00, v10, v11, v01) has (+Y) x (+X) = -Z!
            bm.faces.new((v00, v10, v11, v01))
    ring_verts.append([grid0_bm[iy][ix] for (iy, ix) in perim_ij])

    for st_i in range(1, 9):
        gp = eval_station_grid(st_i)
        rv = [bm.verts.new(tuple(gp[iy, ix])) for (iy, ix) in perim_ij]
        ring_verts.append(rv)

    grid9_bm = [[None] * 3 for _ in range(8)]
    g9 = eval_station_grid(9)
    # Slope the 3 interdigital finger-web clefts naturally (palmar web sits distally, dorsal cleft slopes proximally!)
    for iy in (1, 2, 3, 4, 5, 6):
        g9[iy, 2, 2] -= 0.022  # dorsal knuckle valley slopes back!
        g9[iy, 2, 0] -= 0.010  # valley depression between MCP knuckles!
        g9[iy, 0, 2] += 0.008  # palmar natatory web fold extends slightly distally!
    for iy in range(8):
        for ix in range(3):
            grid9_bm[iy][ix] = bm.verts.new(tuple(g9[iy, ix]))
    ring_verts.append([grid9_bm[iy][ix] for (iy, ix) in perim_ij])

    # Connect perimeter tubes across stations 0..9, EXCEPT leave the 2x2 radial thumb socket open at st_i 5..7!
    # Look at perim_ij around radial side (-Y, iy=0):
    #   k = 16 is (0, 0) [radial palmar]
    #   k = 17 is (0, 1) [radial mid]
    #   k = 0  is (0, 2) [radial dorsal]
    # So perimeter segments k=16 (16->17) and k=17 (17->0) between st_i=5->6 and st_i=6->7 ARE the 2x2 radial thumb socket!
    for st_i in range(9):
        rA = ring_verts[st_i]
        rB = ring_verts[st_i + 1]
        for k in range(18):
            k1 = (k + 1) % 18
            if st_i in (5, 6) and k in (16, 17):
                continue  # Leave open for seamless 8-edge thumb extrusion!
            # Winding: rA[k] -> rA[k1] (along CCW perimeter) -> rB[k1] (+Z) -> rB[k]
            # Normal = (perim_tangent) x (+Z) = OUTWARD!
            bm.faces.new((rA[k], rA[k1], rB[k1], rB[k]))

    # Cap the 3 interdigital web cleft columns (col = 1, 3, 5) at station 9!
    for col_cleft in (1, 3, 5):
        for ix in range(2):
            v00 = grid9_bm[col_cleft][ix]
            v10 = grid9_bm[col_cleft + 1][ix]
            v11 = grid9_bm[col_cleft + 1][ix + 1]
            v01 = grid9_bm[col_cleft][ix + 1]
            # Normal +Z distal: (+X) x (+Y) = +Z -> (v00, v01, v11, v10)!
            bm.faces.new((v00, v01, v11, v10))

    # =======================================================================
    # EXTRUDE 4 ANATOMICAL FINGERS + RECESSED 3D FINGERNAILS FROM COLUMNS 0, 2, 4, 6
    # =======================================================================
    finger_defs = [
        # (col, j1, j2, j3, jtip, base_rx, base_ry) — sturdy adult male finger proportions!
        (0, HAND_JOINTS["ix_1"], HAND_JOINTS["ix_2"], HAND_JOINTS["ix_3"], HAND_JOINTS["ix_tip"], 0.052, 0.055),
        (2, HAND_JOINTS["md_1"], HAND_JOINTS["md_2"], HAND_JOINTS["md_3"], HAND_JOINTS["md_tip"], 0.055, 0.058),
        (4, HAND_JOINTS["rg_1"], HAND_JOINTS["rg_2"], HAND_JOINTS["rg_3"], HAND_JOINTS["rg_tip"], 0.051, 0.054),
        (6, HAND_JOINTS["pk_1"], HAND_JOINTS["pk_2"], HAND_JOINTS["pk_3"], HAND_JOINTS["pk_tip"], 0.044, 0.047),
    ]

    nail_faces_to_inset = []

    for col, J1, J2, J3, Jtip, rx0, ry0 in finger_defs:
        # Socket loop of 6 vertices around this finger base (CCW viewed from +Z distal!):
        #   0: (col,   2) dorsal-radial
        #   1: (col+1, 2) dorsal-ulnar
        #   2: (col+1, 1) mid-ulnar
        #   3: (col+1, 0) palmar-ulnar
        #   4: (col,   0) palmar-radial
        #   5: (col,   1) mid-radial
        sock_ring = [
            grid9_bm[col][2],
            grid9_bm[col + 1][2],
            grid9_bm[col + 1][1],
            grid9_bm[col + 1][0],
            grid9_bm[col][0],
            grid9_bm[col][1],
        ]

        # Axis stations along the 3 phalanges (8 stations along finger!)
        # (chain_pos, rx_scale, ry_scale, palmar_pad_bulge, dorsal_flat)
        d12 = J2 - J1
        d23 = J3 - J2
        d3t = Jtip - J3
        f_stations = [
            (J1 + 0.22 * d12, 0.98, 0.98, 0.08, 0.0),  # 0: proximal phalanx base
            (J1 + 0.62 * d12, 0.91, 0.92, 0.12, 0.1),  # 1: proximal phalanx shaft
            (J2,              0.95, 0.98, 0.02, 0.0),  # 2: PIP knuckle joint (wider laterally!)
            (J2 + 0.48 * d23, 0.84, 0.86, 0.10, 0.1),  # 3: middle phalanx shaft
            (J3,              0.85, 0.88, 0.02, 0.0),  # 4: DIP knuckle joint
            (J3 + 0.26 * d3t, 0.80, 0.83, 0.14, 0.25), # 5: nail fold / cuticle base!
            (J3 + 0.76 * d3t, 0.72, 0.76, 0.20, 0.30), # 6: distal nail-bed end / fleshy pad!
            (Jtip,            0.46, 0.52, 0.06, 0.15), # 7: rounded fingertip apex
        ]

        T_ax = (Jtip - J1) / np.linalg.norm(Jtip - J1)
        D_ax = np.array([1.0, 0.0, 0.0]) - T_ax * T_ax[0]
        D_ax /= np.linalg.norm(D_ax)
        U_ax = np.cross(T_ax, D_ax)  # points +Y ulnar!

        # Local unit offsets (d_x, u_y) for the 6-vertex octagonal-style cross-section (CCW around +T_ax!):
        # Check: D_ax x U_ax = (+X) x (+Y) = +T_ax (+Z)!
        #   0: (+D, -U) -> 1: (+D, +U) [tangent +U, (+U) x (+T) = +D outward! YES!]
        local_6 = [
            ( 0.88, -0.78),  # 0: dorsal-radial
            ( 0.88,  0.78),  # 1: dorsal-ulnar
            ( 0.02,  1.05),  # 2: mid-ulnar
            (-0.92,  0.76),  # 3: palmar-ulnar
            (-0.92, -0.76),  # 4: palmar-radial
            ( 0.02, -1.05),  # 5: mid-radial
        ]

        prev_ring = sock_ring
        ring_history = []
        for fs_i, (c_pt, sx, sy, p_bulge, d_flat) in enumerate(f_stations):
            cur_ring = []
            for vi, (ld, lu) in enumerate(local_6):
                dd = ld * rx0 * sx
                uu = lu * ry0 * sy
                if ld < -0.5:
                    dd -= rx0 * p_bulge  # fleshy palmar finger pad!
                if ld > 0.5 and d_flat > 0.0:
                    dd *= (1.0 - 0.22 * d_flat)  # flat dorsal nail bed!
                # PIP & DIP dorsal knuckle ridge
                if fs_i in (2, 4) and ld > 0.5:
                    dd += 0.0045
                pt = c_pt + D_ax * dd + U_ax * uu
                cur_ring.append(bm.verts.new(tuple(pt)))

            for k in range(6):
                k1 = (k + 1) % 6
                f_new = bm.faces.new((prev_ring[k], prev_ring[k1], cur_ring[k1], cur_ring[k]))
                # k == 0 between station 5 (cuticle) -> 6 (nail tip) is the DORSAL FINGERNAIL BED!
                if fs_i == 6 and k == 0:
                    nail_faces_to_inset.append((f_new, D_ax, T_ax))
            prev_ring = cur_ring
            ring_history.append(cur_ring)

        # Cap fingertip cleanly with 2 quads matching the 6-vertex ring: (0,1,2,5) and (5,2,3,4)!
        # Check normal: (v1 - v0) = +U, (v5 - v0) = -D -> (+U) x (-D) = +(D x U) = +T_ax OUTWARD!
        tip_r = ring_history[-1]
        bm.faces.new((tip_r[0], tip_r[1], tip_r[2], tip_r[5]))
        bm.faces.new((tip_r[5], tip_r[2], tip_r[3], tip_r[4]))

    # =======================================================================
    # EXTRUDE ANATOMICAL OPPOSABLE THUMB + RECESSED 3D THUMBNAIL FROM RADIAL SOCKET
    # =======================================================================
    # Recall the 2x2 radial opening at st_i = 5, 6, 7 on k = 16 (palmar), 17 (mid), 0 (dorsal)!
    # Let's list its 8 boundary vertices in CCW order viewed from the thumb's distal axis (-Y, -X, +Z)!
    # Check thumb outward direction T_th ~ (-0.25, -0.78, +0.56):
    # Viewed from tip looking back at palm, UP is +Z (st_i 5 -> 7), RIGHT is +X (k=16 palmar -> k=17 -> k=0 dorsal):
    # Wait: let's check cross product of edge (r5[16] -> r5[17], which is +X) with thumb extrusion T_th (-Y):
    #   (+X) x (-Y) = -Z (outward bottom of thumb!) -> Wait: we want outward normal of bottom of thumb to be -Z!
    #   In `bm.faces.new((prev[k], prev[k1], cur[k1], cur[k]))`, normal is `(prev[k1] - prev[k]) x (cur[k] - prev[k])`!
    #   At bottom edge (st_i = 5, going from k=16 to k=17 -> +X): `(+X) x T_th(-Y) = -Z` (OUTWARD bottom!!)!
    #   At dorsal edge (k = 0, going from st_i=5 to st_i=7 -> +Z): `(+Z) x (-Y) = +X` (OUTWARD dorsal!!)!
    #   At top edge (st_i = 7, going from k=0 to k=16 -> -X): `(-X) x (-Y) = +Z` (OUTWARD top!!)!
    #   At palmar edge (k = 16, going from st_i=7 to st_i=5 -> -Z): `(-Z) x (-Y) = -X` (OUTWARD palmar!!)!
    # EXACT 100% VERIFIED CCW 8-VERTEX SOCKET LOOP!!
    r5, r6, r7 = ring_verts[5], ring_verts[6], ring_verts[7]
    thumb_sock = [
        r5[16], r5[17], r5[0],   # bottom edge (+X)
        r6[0],                   # dorsal mid (+Z)
        r7[0], r7[17], r7[16],   # top edge (-X)
        r6[16],                  # palmar mid (-Z)
    ]

    TJ1, TJ2, TJ3, TJtip = HAND_JOINTS["th_1"], HAND_JOINTS["th_2"], HAND_JOINTS["th_3"], HAND_JOINTS["th_tip"]
    T_th = (TJtip - TJ1) / np.linalg.norm(TJtip - TJ1)
    # Thumb dorsal faces tilted (+0.78 X, -0.58 Y, +0.22 Z) orthogonalized against T_th!
    D_th = np.array([0.82, -0.48, 0.30])
    D_th = D_th - T_th * np.dot(D_th, T_th)
    D_th /= np.linalg.norm(D_th)
    # U_th such that D_th x U_th = T_th -> U_th = T_th x D_th (points roughly toward +Z / index finger side!)
    U_th = np.cross(T_th, D_th)

    # Match the 8-vertex loop ordering of thumb_sock around T_th:
    #   0: (-D, -U), 1: (0, -U), 2: (+D, -U), 3: (+D, 0), 4: (+D, +U), 5: (0, +U), 6: (-D, +U), 7: (-D, 0)
    # Check tangent from 2->3->4 (dorsal edge): +U! And (+U) x T_th = +D_th (OUTWARD DORSAL!!)!
    local_8 = [
        (-0.82, -0.82),  # 0: palmar-outer
        ( 0.00, -1.00),  # 1: mid-outer
        ( 0.82, -0.82),  # 2: dorsal-outer
        ( 0.96,  0.00),  # 3: dorsal-center
        ( 0.82,  0.82),  # 4: dorsal-inner (toward index web)
        ( 0.00,  1.00),  # 5: mid-inner
        (-0.82,  0.82),  # 6: palmar-inner
        (-0.98,  0.00),  # 7: palmar-center
    ]

    td12 = TJ2 - TJ1
    td23 = TJ3 - TJ2
    td3t = TJtip - TJ3
    th_rx0, th_ry0 = 0.061, 0.065
    th_stations = [
        (TJ1 + 0.38 * td12, 1.16, 1.18, 0.14, 0.0),  # 0: muscular thenar metacarpal transition
        (TJ1 + 0.78 * td12, 0.98, 1.02, 0.10, 0.0),  # 1: thumb metacarpal neck
        (TJ2,               0.98, 1.04, 0.04, 0.0),  # 2: thumb MCP knuckle
        (TJ2 + 0.52 * td23, 0.88, 0.92, 0.08, 0.1),  # 3: proximal phalanx shaft
        (TJ3,               0.90, 0.96, 0.04, 0.0),  # 4: thumb IP joint
        (TJ3 + 0.25 * td3t, 0.85, 0.92, 0.18, 0.25), # 5: thumbnail cuticle base
        (TJ3 + 0.76 * td3t, 0.76, 0.84, 0.24, 0.30), # 6: thumbnail distal edge & broad thumb pad
        (TJtip,             0.48, 0.56, 0.08, 0.15), # 7: rounded thumb apex
    ]

    prev_th = thumb_sock
    th_nail_faces = []
    for ts_i, (c_pt, sx, sy, p_bulge, d_flat) in enumerate(th_stations):
        cur_th = []
        for ld, lu in local_8:
            dd = ld * th_rx0 * sx
            uu = lu * th_ry0 * sy
            if ld < -0.5:
                dd -= th_rx0 * p_bulge
            if ld > 0.5 and d_flat > 0.0:
                dd *= (1.0 - 0.22 * d_flat)
            if ts_i in (2, 4) and ld > 0.5:
                dd += 0.0045
            cur_th.append(bm.verts.new(tuple(c_pt + D_th * dd + U_th * uu)))

        for k in range(8):
            k1 = (k + 1) % 8
            fn = bm.faces.new((prev_th[k], prev_th[k1], cur_th[k1], cur_th[k]))
            if ts_i == 6 and k in (2, 3):  # the 2 dorsal thumbnail faces!
                th_nail_faces.append(fn)
        prev_th = cur_th

    # Cap 8-vertex thumb tip cleanly with 3 quads: (0,1,2,7), (7,2,3,6 -> wait: 2,3,4,5 & 0,1,2,5,6,7):
    # Let's check 8-gon -> 3 quads: (0, 1, 2, 7), (7, 2, 5, 6), (2, 3, 4, 5)!
    # Check normals: (1-0) = +D, (7-0) = +U -> (+D) x (+U) = +T_th OUTWARD!!
    bm.faces.new((prev_th[0], prev_th[1], prev_th[2], prev_th[7]))
    bm.faces.new((prev_th[7], prev_th[2], prev_th[5], prev_th[6]))
    bm.faces.new((prev_th[2], prev_th[3], prev_th[4], prev_th[5]))

    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))

    # =======================================================================
    # INSET 3D RECESSED CUTICLE FOLDS & SLIGHTLY CONVEX MALE FINGERNAILS!
    # =======================================================================
    nail_mat_faces = []
    for f_nail, d_vec, t_vec in nail_faces_to_inset:
        bmesh.ops.inset_individual(bm, faces=[f_nail], thickness=0.0055, depth=-0.0022)
        bmesh.ops.inset_individual(bm, faces=[f_nail], thickness=0.0020, depth=0.0034)
        nail_mat_faces.append(f_nail)

    if len(th_nail_faces) == 2:
        bmesh.ops.inset_region(bm, faces=th_nail_faces, thickness=0.0065, depth=-0.0024)
        bmesh.ops.inset_region(bm, faces=th_nail_faces, thickness=0.0022, depth=0.0036)
        nail_mat_faces.extend(th_nail_faces)

    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.normal_update()
    non_man = [e for e in bm.edges if not e.is_manifold]
    print(f"  [CAGE OK] Pure-quad hand cage: {len(bm.verts)} verts, {len(bm.faces)} faces, non-manifold edges={len(non_man)}")
    return bm, set(nail_mat_faces)


def build_and_bake_realistic_hand(tex_dir, progs_dir):
    """Builds the subdivided sculpted male hand, bakes realistic skin texture, and rigs it to a Blender Armature."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    bm, nail_faces = build_seamless_hand_cage_bmesh()
    # Tag nail polygons via custom int layer so we know exact nail UVs after subdivision!
    nail_layer = bm.faces.layers.int.new("is_nail")
    for f in bm.faces:
        f[nail_layer] = 1 if f in nail_faces else 0

    me_cage = bpy.data.meshes.new("HandCage")
    bm.to_mesh(me_cage)
    bm.free()
    me_cage.update()

    ob = bpy.data.objects.new("ManHand", me_cage)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # Apply Catmull-Clark Subdivision Level 2 for seamless organic anatomy!
    sub = ob.modifiers.new("Subsurf", type="SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    bpy.ops.object.modifier_apply(modifier=sub.name)

    # Add subtle 3D anatomical micro-relief (extensor tendons on back of hand, knuckle creases, palmar life-line dimple)
    me_hi = ob.data
    V_hi = np.array([v.co[:] for v in me_hi.vertices], dtype=np.float64)
    # Compute smooth vertex normals
    me_hi.polygons.foreach_set("use_smooth", [True] * len(me_hi.polygons))
    me_hi.update()
    N_hi = np.array([v.normal[:] for v in me_hi.vertices], dtype=np.float64)

    x, y, z = V_hi[:, 0], V_hi[:, 1], V_hi[:, 2]
    disp = np.zeros(len(V_hi), dtype=np.float64)

    # 1. Four subtle dorsal extensor tendons fanning from wrist (0,0,0.02) to the 4 MCP knuckles!
    dors_mask = sstep_np(0.01, 0.05, x) * sstep_np(-0.02, 0.08, z) * (1.0 - sstep_np(0.41, 0.47, z))
    for ky in (-0.156, -0.050, 0.054, 0.148):
        t_prog = np.clip(z / 0.44, 0.0, 1.0)
        y_tendon = ky * (0.22 + 0.78 * t_prog)
        d_lat = (y - y_tendon) / 0.016
        disp += 0.0038 * np.exp(-(d_lat * d_lat)) * dors_mask * (0.35 + 0.65 * t_prog)

    # 2. Forearm brachioradialis muscle contour along radial-dorsal forearm (-Y, +X, z in -1.15..-0.10)
    brach = sstep_np(-1.18, -0.75, z) * (1.0 - sstep_np(-0.26, -0.05, z)) * np.exp(-(((y + 0.11) / 0.080) ** 2)) * sstep_np(-0.04, 0.06, x)
    disp += 0.0095 * brach

    # 3. Very subtle 3D palmar skin fold around thenar thumb muscle (natural contour, never a drawn line!)
    palm_mask = sstep_np(-0.02, -0.05, x) * sstep_np(0.08, 0.14, z) * (1.0 - sstep_np(0.39, 0.44, z))
    d_life = np.hypot((y + 0.16) / 0.16, (z - 0.16) / 0.21) - 1.0
    disp -= 0.0014 * np.exp(-((d_life / 0.085) ** 2)) * palm_mask

    # 4. Subtle dorsal PIP knuckle oval skin wrinkle rings
    for jn in ("ix_2", "md_2", "rg_2", "pk_2", "th_3"):
        jp = HAND_JOINTS[jn]
        dj = np.linalg.norm(V_hi - jp[None, :], axis=1)
        kn_mask = np.exp(-((dj / 0.032) ** 2)) * sstep_np(0.01, 0.04, x)
        wrink = np.sin((z - jp[2]) * 420.0)
        disp += 0.0009 * wrink * kn_mask

    V_sculpt = V_hi + N_hi * disp[:, None]
    for idx, v in enumerate(me_hi.vertices):
        v.co = V_sculpt[idx]
    me_hi.update()

    # Smart UV Project on the sculpted mesh BEFORE decimation so UVs are clean & distortion-free!
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(62.0), island_margin=0.018, area_weight=0.2)
    bpy.ops.object.mode_set(mode="OBJECT")

    # =======================================================================
    # BAKE TRUE 3D POSITION, NORMAL, NAIL MASK & CYCLES AMBIENT OCCLUSION TO 1024x1024!
    # =======================================================================
    RES = 1024
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.render.bake.margin = 12

    # World white so AO bakes pure cavity occlusion
    scene.world = bpy.data.worlds.new("BakeWorld")
    scene.world.use_nodes = True
    w_bg = scene.world.node_tree.nodes.get("Background")
    w_bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)

    def bake_pass(img_name, setup_nodes_fn, bake_type="EMIT"):
        img = bpy.data.images.new(img_name, width=RES, height=RES, alpha=False, float_buffer=True)
        mat = bpy.data.materials.new(img_name + "_mat")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out_n = nt.nodes.new("ShaderNodeOutputMaterial")
        setup_nodes_fn(nt, out_n)
        ti = nt.nodes.new("ShaderNodeTexImage")
        ti.image = img
        nt.nodes.active = ti
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        bpy.ops.object.bake(type=bake_type)
        arr = np.array(img.pixels[:], dtype=np.float32).reshape((RES, RES, 4))[:, :, :3]
        return arr[::-1].copy()  # flip Blender bottom-up -> top-down PNG row order!

    # 1. Bake Ambient Occlusion (captures finger webs, nail cuticles, palm hollow, wrist creases!)
    def setup_ao(nt, out_n):
        bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
        nt.links.new(out_n.inputs["Surface"], bsdf.outputs["BSDF"])

    ao_map = bake_pass("bake_ao", setup_ao, bake_type="AO")[:, :, 0]

    # 2. Bake Object Rest Position (mapped safely from [-2, +2] -> [0, 1] so z=-1.32 forearm never clamps!)
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

    pos_map = (bake_pass("bake_pos", setup_pos, bake_type="EMIT") - 0.5) * 4.0

    # 3. Bake Rest Normal + Pointiness Curvature! (R,G,B = normal*0.5+0.5; bake pointiness separately)
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

    nrm_map = bake_pass("bake_nrm", setup_nrm, bake_type="EMIT") * 2.0 - 1.0

    # 4. Bake Nail Mask + Pointiness Curvature!
    # Store is_nail in vertex color / attribute so Cycles bakes exact antialiased nail plates!
    bm_tmp = bmesh.new()
    bm_tmp.from_mesh(ob.data)
    nl_l = bm_tmp.faces.layers.int.get("is_nail")
    vc_l = bm_tmp.loops.layers.color.new("NailCol")
    for f in bm_tmp.faces:
        val = 1.0 if (nl_l and f[nl_l] == 1) else 0.0
        for lp in f.loops:
            lp[vc_l] = (val, val, val, 1.0)
    bm_tmp.to_mesh(ob.data)
    bm_tmp.free()
    ob.data.update()

    def setup_nail_pointy(nt, out_n):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "NailCol"
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(comb.inputs["X"], attr.outputs["Fac"])
        nt.links.new(comb.inputs["Y"], geo.outputs["Pointiness"])
        nt.links.new(em.inputs["Color"], comb.outputs["Vector"])
        nt.links.new(out_n.inputs["Surface"], em.outputs["Emission"])

    np_map = bake_pass("bake_np", setup_nail_pointy, bake_type="EMIT")
    nail_mask = np.clip(np_map[:, :, 0], 0.0, 1.0)
    pointy = np.clip(np_map[:, :, 1], 0.0, 1.0)

    # =======================================================================
    # SYNTHESIZE LIFELIKE WARM MALE HUMAN SKIN TEXTURE FROM 3D BAKED MAPS!
    # =======================================================================
    px, py, pz = pos_map[:, :, 0], pos_map[:, :, 1], pos_map[:, :, 2]
    nx, ny, nz = nrm_map[:, :, 0], nrm_map[:, :, 1], nrm_map[:, :, 2]

    # Deterministic multi-scale 3D skin micro-pore & melanin variation in rest object space (ZERO 2D UV seams!)
    rng = np.random.default_rng(77123)
    skin_var = np.zeros((RES, RES), dtype=np.float32)
    for freq, amp in ((14.0, 0.35), (34.0, 0.28), (85.0, 0.22), (210.0, 0.15)):
        kx, ky, kz, ph = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 6.28)
        kn = math.sqrt(kx * kx + ky * ky + kz * kz) + 1e-6
        skin_var += amp * np.sin((px * kx + py * ky + pz * kz) / kn * freq + ph)

    # Dorsal (+nx) vs Palmar (-nx) blend:
    # Real male hands have warm golden-peach sun-kissed dorsal skin and lighter rosy-cream palmar skin!
    palmar_w = sstep_np(0.15, -0.35, nx) * sstep_np(-0.08, 0.10, pz)
    dorsal_rgb = np.array([0.84, 0.63, 0.50], dtype=np.float32)   # Natural warm Caucasian/light-tan male skin!
    palmar_rgb = np.array([0.90, 0.71, 0.61], dtype=np.float32)   # Softer rosy-cream palm skin!
    forearm_tan = sstep_np(0.05, -0.45, pz)                       # Slight sun-warmed forearm tone
    base = dorsal_rgb[None, None, :] * (1.0 - palmar_w[:, :, None]) + palmar_rgb[None, None, :] * palmar_w[:, :, None]
    base *= (1.0 - 0.05 * forearm_tan[:, :, None])

    # Add subtle natural melanin / pore micro-texture
    base += skin_var[:, :, None] * np.array([0.022, 0.016, 0.014], dtype=np.float32)

    # Subsurface Blood Perfusion (warm coral-red flush in fingertips, knuckles, thenar/hypothenar pads!)
    tip_flush = np.zeros((RES, RES), dtype=np.float32)
    for tn in ("ix_tip", "md_tip", "rg_tip", "pk_tip", "th_tip"):
        tp = HAND_JOINTS[tn]
        dt = np.sqrt((px - tp[0]) ** 2 + (py - tp[1]) ** 2 + (pz - tp[2]) ** 2)
        tip_flush = np.maximum(tip_flush, np.exp(-((dt / 0.11) ** 2)))

    knuckle_flush = np.zeros((RES, RES), dtype=np.float32)
    for kn in ("ix_1", "md_1", "rg_1", "pk_1", "ix_2", "md_2", "rg_2", "pk_2", "th_2", "th_3"):
        kp = HAND_JOINTS[kn]
        dk = np.sqrt((px - kp[0]) ** 2 + (py - kp[1]) ** 2 + (pz - kp[2]) ** 2)
        knuckle_flush = np.maximum(knuckle_flush, np.exp(-((dk / 0.055) ** 2)))

    flush = np.clip(0.55 * tip_flush + 0.42 * knuckle_flush * sstep_np(-0.1, 0.4, nx) + 0.25 * palmar_w, 0.0, 1.0)
    sss_col = np.array([0.88, 0.40, 0.36], dtype=np.float32)
    base = base * (1.0 - 0.24 * flush[:, :, None]) + sss_col[None, None, :] * (0.24 * flush[:, :, None])

    # Subtle subcutaneous dorsal wrist/hand veins (very soft, realistic, never cartoony!)
    v_mask = sstep_np(0.25, 0.65, nx) * sstep_np(-0.35, 0.05, pz) * (1.0 - sstep_np(0.28, 0.40, pz))
    vein1 = np.exp(-(((py + 0.045 - 0.10 * pz) / 0.011) ** 2))
    vein2 = np.exp(-(((py - 0.055 + 0.08 * pz) / 0.010) ** 2))
    veins = np.clip((vein1 + vein2) * v_mask, 0.0, 1.0)
    base = base * (1.0 - 0.09 * veins[:, :, None]) + np.array([0.46, 0.56, 0.64], dtype=np.float32) * (0.09 * veins[:, :, None])

    # Apply 3D Curvature & Cycles Ambient Occlusion with WARM Subsurface Cavity Tint (never muddy black/gray!)
    # In real skin, crevices (finger webs, palm creases, cuticles) scatter warm reddish-terracotta light!
    cavity = np.clip((0.50 - pointy) * 2.8, 0.0, 1.0)
    ridge = np.clip((pointy - 0.51) * 2.6, 0.0, 1.0)
    ao_clean = np.clip(ao_map, 0.52, 1.0)
    warm_occ = np.stack([
        ao_clean ** 0.58,
        ao_clean ** 0.80,
        ao_clean ** 0.96,
    ], axis=-1)
    base = base * (0.28 + 0.72 * warm_occ)
    # Soft warm subsurface crease tint in sculpted palmar & finger joint folds (zero geometric "X" lines!)
    crease_col = np.array([0.70, 0.44, 0.36], dtype=np.float32)
    p_flex_mask = sstep_np(-0.01, -0.06, nx)
    d_life_px = np.hypot((py + 0.16) / 0.16, (pz - 0.16) / 0.21) - 1.0
    palm_lines = 0.11 * np.exp(-((d_life_px / 0.065) ** 2)) * sstep_np(0.08, 0.14, pz) * (1.0 - sstep_np(0.32, 0.38, pz)) * p_flex_mask
    joint_creases = np.zeros((RES, RES), dtype=np.float32)
    for jn in ("ix_1", "md_1", "rg_1", "pk_1", "ix_2", "md_2", "rg_2", "pk_2", "ix_3", "md_3", "rg_3", "pk_3", "th_2", "th_3"):
        jp = HAND_JOINTS[jn]
        d_ax = (pz - jp[2]) / 0.0065
        d_rad = ((py - jp[1]) / 0.044) ** 2
        joint_creases = np.maximum(joint_creases, 0.16 * np.exp(-(d_ax * d_ax + d_rad)) * p_flex_mask)

    tot_crease = np.clip(0.24 * cavity + palm_lines + joint_creases, 0.0, 0.34)
    base = base * (1.0 - tot_crease[:, :, None]) + crease_col[None, None, :] * tot_crease[:, :, None]
    base += ridge[:, :, None] * np.array([0.04, 0.035, 0.03], dtype=np.float32)

    # Realistic Male Fingernails (healthy pink keratin nail bed + pale lunula + distal free edge + subtle cuticle rim!)
    if np.max(nail_mask) > 0.05:
        nail_pink = np.array([0.90, 0.69, 0.65], dtype=np.float32)
        nail_tip = np.array([0.96, 0.92, 0.88], dtype=np.float32)
        dist_tip_w = sstep_np(0.84, 0.91, pz + 0.08 * np.maximum(0.0, -py - 0.20))
        nail_col = nail_pink[None, None, :] * (1.0 - 0.60 * dist_tip_w[:, :, None]) + nail_tip[None, None, :] * (0.60 * dist_tip_w[:, :, None])
        cuticle_rim = np.clip(nail_mask * (1.0 - nail_mask) * 4.0, 0.0, 1.0)
        nm3 = (nail_mask ** 0.70)[:, :, None]
        base = base * (1.0 - nm3) + nail_col * nm3
        base = base * (1.0 - 0.18 * cuticle_rim[:, :, None]) + crease_col[None, None, :] * (0.18 * cuticle_rim[:, :, None])

    web_u8 = np.clip(base * 255.0, 0, 255).astype(np.uint8)
    # DarkPlaces lightingDiffuse calibration (~0.62x gamma-preserving scale so in-game Quake isn't overblown!)
    dp_rgb = np.clip((base ** 1.08) * 0.64 * 255.0, 0, 255).astype(np.uint8)

    def save_blender_png(arr_rgb, out_path):
        h, w, _ = arr_rgb.shape
        rgba = np.ones((h, w, 4), dtype=np.float32)
        rgba[:, :, :3] = arr_rgb[::-1].astype(np.float32) / 255.0
        im_b = bpy.data.images.new("tmp_save", width=w, height=h, alpha=False)
        im_b.filepath_raw = out_path
        im_b.file_format = "PNG"
        im_b.pixels[:] = rgba.ravel().tolist()
        im_b.save()
        bpy.data.images.remove(im_b)

    os.makedirs(tex_dir, exist_ok=True)
    os.makedirs(progs_dir, exist_ok=True)
    save_blender_png(web_u8, os.path.join(tex_dir, "mbox_hand_web.png"))
    save_blender_png(dp_rgb, os.path.join(tex_dir, "mbox_hand.png"))
    save_blender_png(dp_rgb, os.path.join(progs_dir, "mbox_hand.png"))
    print("  [SKIN BAKE OK] Realistic 3D AO + Subsurface Male Hand Texture -> mbox_hand_web.png & progs/mbox_hand.png")

    # =======================================================================
    # UV-PRESERVING DECIMATION TO ~2,550 VERTS / ~5,000 TRIS (< MD3 4096v LIMIT)
    # =======================================================================
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    cur_nv = len(ob.data.vertices)
    target_nv = 2500
    if cur_nv > target_nv:
        dec = ob.modifiers.new("DecHand", type="DECIMATE")
        dec.decimate_type = "COLLAPSE"
        dec.ratio = target_nv / float(cur_nv)
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")

    # Split UV-seam vertices cleanly into unique (pos, uv) MD3 vertices BEFORE rigging so UV islands never smear!
    me_dec = ob.data
    uv_lay = me_dec.uv_layers.active.data
    vert_uv_map = {}
    new_verts = []
    new_uvs = []
    new_tris = []

    for poly in me_dec.polygons:
        if len(poly.vertices) != 3:
            continue
        tri_idx = []
        for lp_i in poly.loop_indices:
            vi = me_dec.loops[lp_i].vertex_index
            uv = uv_lay[lp_i].uv
            # Note: flip Blender bottom-up V -> Quake/MD3 top-down V (1.0 - uv.y)!
            uq = (round(float(uv[0]), 4), round(float(1.0 - uv[1]), 4))
            key = (vi, uq)
            if key not in vert_uv_map:
                vert_uv_map[key] = len(new_verts)
                new_verts.append(tuple(me_dec.vertices[vi].co[:]))
                new_uvs.append((float(uv[0]), float(1.0 - uv[1])))
            tri_idx.append(vert_uv_map[key])
        new_tris.append(tuple(tri_idx))

    # Build final clean rigged mesh object + weld twin seam weights via DataTransfer / Armature Auto!
    # Wait: if we parent the UNSPLIT watertight mesh `ob` to the Armature with `ARMATURE_AUTO` FIRST,
    # then every split UV-seam vertex `(vi, uq)` inherits the EXACT smooth heat-diffusion bone weights
    # AND deformed vertex positions of vertex `vi` on the watertight mesh with ZERO cracks at UV seams!!
    # GENIUS!! Think about that: `ob` stays 100% watertight during Armature + CorrectiveSmooth evaluation,
    # and we simply gather `deformed_co[vi]` via `orig_vi_per_md3_vert` for each frame!!
    orig_vi_for_md3 = [0] * len(new_verts)
    for (vi, _), md3_idx in vert_uv_map.items():
        orig_vi_for_md3[md3_idx] = vi
    orig_vi_arr = np.array(orig_vi_for_md3, dtype=np.int32)
    md3_tris = np.array(new_tris, dtype=np.int32)
    md3_uvs = np.array(new_uvs, dtype=np.float64)
    assert len(new_verts) <= 4096 and len(md3_tris) <= 8192, f"Hand MD3 overflow: nv={len(new_verts)}, nt={len(md3_tris)}"
    print(f"  [RIG MESH OK] Watertight verts={len(me_dec.vertices)}, MD3 UV-split verts={len(new_verts)}, tris={len(md3_tris)}")

    # =======================================================================
    # BUILD 18-BONE BLENDER ARMATURE + HEAT-DIFFUSION `ARMATURE_AUTO` + `CORRECTIVE_SMOOTH`!
    # =======================================================================
    arm_data = bpy.data.armatures.new("HandArmatureData")
    arm_ob = bpy.data.objects.new("HandArmature", arm_data)
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

    # Dorsal roll_hint = +X so local +Z of every finger bone points DORSAL (+X) and +X flexion curls into PALM (-X)!
    dors_x = (1.0, 0.0, 0.0)
    th_dors = (0.82, -0.48, 0.30)

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

    # Parent watertight sculpted hand to Armature using Blender's C++ Heat-Diffusion solver!
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    # Add Corrective Smooth modifier after Armature so knuckles & palm pads preserve volume cleanly when flexing!
    cs_mod = ob.modifiers.new("VolumePreserve", type="CORRECTIVE_SMOOTH")
    cs_mod.factor = 0.55
    cs_mod.iterations = 6
    cs_mod.smooth_type = "LENGTH_WEIGHTED"
    cs_mod.use_pin_boundary = True

    return ob, arm_ob, orig_vi_arr, md3_tris, md3_uvs


def evaluate_posed_hand(hand_ob, arm_ob, orig_vi_arr, pose_bone_eulers, world_R, world_wrist_pos, scale=11.8):
    """Poses the Blender Armature, evaluates Armature + CorrectiveSmooth via depsgraph, and maps into Quake eye space!"""
    for pb in arm_ob.pose.bones:
        pb.rotation_mode = "XYZ"
        rx, ry, rz = pose_bone_eulers.get(pb.name, (0.0, 0.0, 0.0))
        pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_ob = hand_ob.evaluated_get(depsgraph)
    me_eval = eval_ob.to_mesh()
    V_w = np.array([v.co[:] for v in me_eval.vertices], dtype=np.float64)
    eval_ob.to_mesh_clear()

    # Map watertight deformed vertices -> UV-split MD3 vertices -> Quake eye space!
    V_local = V_w[orig_vi_arr]
    V_quake = (V_local * scale) @ world_R.T + world_wrist_pos[None, :]
    return V_quake
