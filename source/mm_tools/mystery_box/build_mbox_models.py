"""Builds the complete 3D Mystery Box Quake Weapon Suite in headless Blender 5.2:

  1. `progs/v_mysterybox.md3`    (220 frames: 192-frame Long Crystal-Ball Idle w/ 16 REAL game
                                  ghosts [8 3D models + 8 sprites] + 28-frame Grab -> Glow -> Throw -> Summon!)
  2. `progs/proj_mysterybox.md3` (32 frames: Thrown tumbling Mystery Box projectile w/ rainbow comet wake)
  3. `mysterybox_closeup.md3`    (192 frames: Centered hero Crystal-Ball turnaround cycling all 16 visions)
  4. `scripts/mysterybox.shader` + `.skin` files in `progs/`
  5. Universal PBR + Translucent Glass + Emissive Ghost `.GLB` files:
       - `BakersfieldQuake/mystery_box_weapon.glb`
       - `BakersfieldQuake/mystery_box_projectile.glb`
       - `source/mm_tools/out/mystery_box/glb/mystery_box_closeup.glb`
  6. 8-panel high-resolution Blender 5.2 EEVEE verification renders!

Run via:
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python source/mm_tools/mystery_box/build_mbox_models.py
"""
import json
import math
import os
import shutil
import sys
import numpy as np
import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
SCRIPTS_DIR = os.path.join(MOD_ROOT, "scripts")

OUT_ROOT = os.path.join(MM_TOOLS, "out", "mystery_box")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
MD3_DIR = os.path.join(OUT_ROOT, "md3")
GLB_DIR = os.path.join(OUT_ROOT, "glb")
PREV_DIR = os.path.join(OUT_ROOT, "previews")

if MM_TOOLS not in sys.path:
    sys.path.insert(0, MM_TOOLS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import md3lib
import sculpt_realistic_hand as srh


# ===========================================================================
# MATH & MESH UTILITIES (Right-Handed Quake Space: +X fwd, +Y left, +Z up)
# ===========================================================================
def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0 + 1e-12)))
    return t * t * (3.0 - 2.0 * t)


def rot_x_mat(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def rot_y_mat(deg):
    """Standard right-handed rotation around +Y: x' = x c + z s, z' = -x s + z c."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def rot_z_mat(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)


def rot_axis_mat(axis, deg):
    ax = np.asarray(axis, dtype=np.float64)
    ax = ax / (np.linalg.norm(ax) + 1e-12)
    x, y, z = ax
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    oc = 1.0 - c
    return np.array([
        [c + x * x * oc,     x * y * oc - z * s, x * z * oc + y * s],
        [y * x * oc + z * s, c + y * y * oc,     y * z * oc - x * s],
        [z * x * oc - y * s, z * y * oc + x * s, c + z * z * oc    ],
    ], dtype=np.float64)


def grid_tris(nu, nv, wrap_u=False, flip=False):
    tris = []
    u_lim = nu if wrap_u else nu - 1
    for j in range(nv - 1):
        for i in range(u_lim):
            i1 = (i + 1) % nu if wrap_u else i + 1
            a = j * nu + i
            b = j * nu + i1
            c = (j + 1) * nu + i1
            d = (j + 1) * nu + i
            if not flip:
                tris.append((a, b, c))
                tris.append((a, c, d))
            else:
                tris.append((a, c, b))
                tris.append((a, d, c))
    return np.array(tris, dtype=np.int32)


def compute_normals(V, F):
    N = np.zeros_like(V, dtype=np.float64)
    v0 = V[F[:, 0]]
    v1 = V[F[:, 1]]
    v2 = V[F[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    np.add.at(N, F[:, 0], fn)
    np.add.at(N, F[:, 1], fn)
    np.add.at(N, F[:, 2], fn)
    lens = np.linalg.norm(N, axis=1, keepdims=True)
    N = np.where(lens > 1e-12, N / np.maximum(lens, 1e-12), np.array([0.0, 0.0, 1.0]))
    return N


# ===========================================================================
# 1. REALISTIC SEAMLESS MALE RIGHT HAND RIG & POSE SOLVER (`surf_man_hand`)
# ===========================================================================
# Uses `sculpt_realistic_hand.py` (1-piece Catmull-Clark subdivided bmesh + Cycles AO/SSS skin bake
# + 18-bone Blender Armature with Heat-Diffusion `ARMATURE_AUTO` weights & `CORRECTIVE_SMOOTH`).
#
# Verified Blender PoseBone Euler conventions (`align_roll((1,0,0))` on fingers/wrist/palm):
#   - `rx < 0`: curls finger into PALM (`-X_h` palmar flexion); `rx > 0`: extends dorsally (`+X_h`)
#   - `rz > 0`: abducts radially toward thumb (`-Y_h`); `rz < 0`: abducts ulnarly toward pinky (`+Y_h`)
#   - On thumb (`th_1..3`): `rx < 0` flexes thumb pad inward; `rz < 0` sweeps thumb across into opposition.
def hand_world_basis(fingers_dir, palm_dir):
    """Exact det=+1 orthonormal world basis from distal fingers_dir (+Z_h) and palm normal (-X_h)."""
    Cz = np.asarray(fingers_dir, dtype=np.float64)
    Cz /= (np.linalg.norm(Cz) + 1e-12)
    p = np.asarray(palm_dir, dtype=np.float64)
    p = p - np.dot(p, Cz) * Cz
    p /= (np.linalg.norm(p) + 1e-12)
    Cx = -p                  # +X_h dorsal = -palm_dir
    Cy = np.cross(Cz, Cx)    # +Y_h pinky = Cz x Cx -> det([Cx, Cy, Cz]) == +1!
    return np.column_stack([Cx, Cy, Cz])


def realistic_hand_pose(mode_weights, ripple_phase=0.0):
    """Blends smoothly across 3 natural human right-hand poses on the Blender Armature:
      - wc (Expressive 3/4 Telekinetic Levitation): natural semi-supinated cascade (staggered index->pinky curl + ripple)
      - wg (Pitcher C-Grip Cupping Box):            side/rear-cup grip wrapping thumb on top-right bevel & 4 fingers around far edge
      - ws (Natural Throw Follow-Through):          relaxed human index-lead release cascade (never rigid straight sticks!)
    """
    wc, wg, ws = mode_weights
    r1 = math.sin(ripple_phase)
    r2 = math.sin(ripple_phase - 0.85)
    r3 = math.sin(ripple_phase - 1.70)
    r4 = math.sin(ripple_phase - 2.55)
    rt = math.cos(ripple_phase * 0.5)

    return {
        "forearm": (0.0, 0.0, 0.0),
        "wrist":   ((-6.0 + 1.8 * rt) * wc + 6.0 * wg - 9.0 * ws, 0.0, 3.0 * wc),
        "palm":    (-4.0 * wc - 5.0 * wg + 3.0 * ws,              0.0, 0.0),
        # Index (-Y_h radial side — leads highest & most poised!)
        "ix_1":    ((-13.0 + 4.0 * r1) * wc - 34.0 * wg - 3.0 * ws,  0.0,  5.5 * wc + 2.0 * wg + 6.5 * ws),
        "ix_2":    ((-19.0 + 4.5 * r1) * wc - 38.0 * wg - 7.0 * ws,  0.0,  0.0),
        "ix_3":    ((-11.0 + 3.0 * r1) * wc - 22.0 * wg - 4.0 * ws,  0.0,  0.0),
        # Middle (natural progressive cascade)
        "md_1":    ((-20.0 + 4.0 * r2) * wc - 36.0 * wg - 7.0 * ws,  0.0,  1.0 * wc + 1.5 * ws),
        "md_2":    ((-27.0 + 4.5 * r2) * wc - 40.0 * wg - 12.0 * ws, 0.0,  0.0),
        "md_3":    ((-15.0 + 3.0 * r2) * wc - 24.0 * wg - 7.0 * ws,  0.0,  0.0),
        # Ring (curled deeper for expressive 3/4 silhouette)
        "rg_1":    ((-28.0 + 4.0 * r3) * wc - 37.0 * wg - 13.0 * ws, 0.0, -3.0 * wc - 1.5 * wg - 3.5 * ws),
        "rg_2":    ((-35.0 + 4.5 * r3) * wc - 40.0 * wg - 18.0 * ws, 0.0,  0.0),
        "rg_3":    ((-19.0 + 3.0 * r3) * wc - 24.0 * wg - 10.0 * ws, 0.0,  0.0),
        # Pinky (+Y_h ulnar side — deepest graceful curl!)
        "pk_1":    ((-35.0 + 4.5 * r4) * wc - 38.0 * wg - 19.0 * ws, 0.0, -7.0 * wc - 3.0 * wg - 8.5 * ws),
        "pk_2":    ((-42.0 + 5.0 * r4) * wc - 38.0 * wg - 24.0 * ws, 0.0,  0.0),
        "pk_3":    ((-22.0 + 3.5 * r4) * wc - 22.0 * wg - 13.0 * ws, 0.0,  0.0),
        # Opposable Thumb (poised naturally in foreground)
        "th_1":    ((-14.0 + 3.0 * rt) * wc - 22.0 * wg + 6.0 * ws,
                    4.0 * wc + 5.0 * wg - 2.0 * ws,
                    (-10.0 + 2.5 * rt) * wc - 18.0 * wg + 7.0 * ws),
        "th_2":    ((-16.0 + 2.5 * rt) * wc - 20.0 * wg - 4.0 * ws,  0.0,  0.0),
        "th_3":    ((-10.0 + 2.0 * rt) * wc - 14.0 * wg - 3.0 * ws,  0.0,  0.0),
    }


def rounded_box_sdf_world(pts_w, box_pos, box_R, box_scale, bev=0.25):
    """Exact Signed Distance Function (in Quake units) from world points `pts_w` to the rounded glass cube."""
    q = np.abs(((pts_w - box_pos[None, :]) @ box_R) / max(box_scale, 1e-6)) - (1.0 - bev)
    outside = np.linalg.norm(np.maximum(q, 0.0), axis=1)
    inside = np.minimum(np.max(q, axis=1), 0.0)
    return (outside + inside - bev) * box_scale


# ===========================================================================
# 2. FILLETED ROUNDED RAINBOW CUBE, '?' EMBLEMS, CRYSTAL CORE & ARCANE VFX
# ===========================================================================
CUBE_FACES = [
    # (normal, u_axis, v_axis) — chosen so u_axis x v_axis == normal (CCW outward!)
    (np.array([ 1.0,  0.0,  0.0]), np.array([ 0.0,  1.0,  0.0]), np.array([0.0,  0.0,  1.0])),  # +X
    (np.array([-1.0,  0.0,  0.0]), np.array([ 0.0, -1.0,  0.0]), np.array([0.0,  0.0,  1.0])),  # -X
    (np.array([ 0.0,  1.0,  0.0]), np.array([-1.0,  0.0,  0.0]), np.array([0.0,  0.0,  1.0])),  # +Y
    (np.array([ 0.0, -1.0,  0.0]), np.array([ 1.0,  0.0,  0.0]), np.array([0.0,  0.0,  1.0])),  # -Y
    (np.array([ 0.0,  0.0,  1.0]), np.array([ 0.0,  1.0,  0.0]), np.array([-1.0, 0.0,  0.0])),  # +Z
    (np.array([ 0.0,  0.0, -1.0]), np.array([ 0.0,  1.0,  0.0]), np.array([ 1.0, 0.0,  0.0])),  # -Z
]


def build_rounded_glass_cube(n_grid=9, bev=0.25):
    """Exact G1-filleted rounded crystal cube in unit [-1, 1]^3 with analytic smooth bevel normals."""
    V, N, UV, F = [], [], [], []
    inner_b = 1.0 - bev
    for nrm, ua, va in CUBE_FACES:
        b0 = len(V)
        for j in range(n_grid):
            v = j / (n_grid - 1)
            sv = 2.0 * v - 1.0
            for i in range(n_grid):
                u = i / (n_grid - 1)
                su = 2.0 * u - 1.0
                # Note: image v=0 is TOP, so map v=0 -> +va (top of cube face) and v=1 -> -va (bottom)!
                p_cube = nrm + ua * su - va * sv
                c_in = np.clip(p_cube, -inner_b, inner_b)
                d = p_cube - c_in
                dn = np.linalg.norm(d)
                n_out = d / max(dn, 1e-9)
                q = c_in + bev * n_out
                V.append(q)
                N.append(n_out)
                UV.append((u, v))
        # Check winding: i increases along +ua, j increases along -va -> (+ua) x (-va) = -(ua x va) = -nrm -> flip=True gives +nrm!
        F.extend((grid_tris(n_grid, n_grid, wrap_u=False, flip=True) + b0).tolist())
    return np.array(V, dtype=np.float64), np.array(N, dtype=np.float64), np.array(UV, dtype=np.float64), np.array(F, dtype=np.int32)


QMARK_FACE_INDICES = (2, 3)  # Opposite lateral faces (+Y, -Y) -> 1 bold '?' visible at a time + open crystal portals!


def build_qmark_face_emblems():
    """2 opposite smart '?' face decals (4x4 curved glass-conforming grids mapped to left half of mbox_qmark.png)."""
    ng = 4
    V_local_grids = []  # per emblem face: (su, sv) in [-1, 1]^2
    UV, F = [], []
    for k_idx, _ in enumerate(QMARK_FACE_INDICES):
        b0 = k_idx * ng * ng
        grid_uv = []
        for j in range(ng):
            v = j / (ng - 1)
            sv = 2.0 * v - 1.0
            for i in range(ng):
                u = i / (ng - 1)
                su = 2.0 * u - 1.0
                grid_uv.append((su, sv))
                UV.append((0.015 + 0.470 * u, 0.02 + 0.96 * v))
        V_local_grids.append(np.array(grid_uv, dtype=np.float64))
        F.extend((grid_tris(ng, ng, wrap_u=False, flip=True) + b0).tolist())
    return V_local_grids, np.array(UV, dtype=np.float64), np.array(F, dtype=np.int32)


def build_crystal_core_lens():
    """Camera-facing curved spherical crystal-ball depth portal mapped to right half of mbox_qmark.png."""
    ng = 9
    V, UV, F = [], [], []
    for j in range(ng):
        v = j / (ng - 1)
        sv = 2.0 * v - 1.0
        for i in range(ng):
            u = i / (ng - 1)
            su = 2.0 * u - 1.0
            r2 = min(1.0, su * su + sv * sv)
            # Bulge slightly toward viewer (-X) like a magnifying crystal ball!
            bulge = -0.28 * math.sqrt(max(0.0, 1.0 - r2))
            V.append((bulge, -su, -sv))
            UV.append((0.515 + 0.470 * u, 0.02 + 0.96 * v))
    F = grid_tris(ng, ng, wrap_u=False, flip=False)
    return np.array(V, dtype=np.float64), np.array(UV, dtype=np.float64), F


def build_ghost_sprite_holograms():
    """8 curved crystal-ball hologram quads (one per real BakersfieldQuake sprite cell in mbox_ghost_spr.png)."""
    ng = 4
    V_base, UV, F = [], [], []
    for idx in range(8):
        col_i = idx % 4
        row_i = idx // 4
        u0 = (col_i + 0.03) / 4.0
        u1 = (col_i + 0.97) / 4.0
        v0 = (row_i + 0.03) / 2.0
        v1 = (row_i + 0.97) / 2.0
        b0 = idx * ng * ng
        for j in range(ng):
            tj = j / (ng - 1)
            sv = 2.0 * tj - 1.0
            for i in range(ng):
                ti = i / (ng - 1)
                su = 2.0 * ti - 1.0
                r2 = min(1.0, su * su + sv * sv)
                bulge = -0.18 * math.sqrt(max(0.0, 1.0 - r2))
                # Facing viewer (-X): +su -> -Y (screen right), +sv -> -Z (screen down) so sprite is right-side up!
                V_base.append((bulge, -su, -sv))
                UV.append((u0 + (u1 - u0) * ti, v0 + (v1 - v0) * tj))
        F.extend((grid_tris(ng, ng, wrap_u=False, flip=False) + b0).tolist())
    return np.array(V_base, dtype=np.float64), np.array(UV, dtype=np.float64), np.array(F, dtype=np.int32)


def build_magic_fx_parts():
    """Builds the 4 additive VFX sub-meshes inside a single `box_fx` surface:
      - 8 rising antigravity starlight motes across the open air gap (Q1: u 0.5..1, v 0..0.5)
      - 6 orbiting 8-point sparkle motes around the box (Q1: u 0.5..1, v 0..0.5)
      - 3 crossed 3D Grab-Charge Supernova Glow Corona planes (Q2: u 0..0.5, v 0.5..1)
      - 6 spiraling Throw Rainbow Comet ribbons (Q3: u 0.5..1, v 0.5..1)
    """
    UV, F = [], []
    meta = {}
    ofs = 0

    # A. 8 Delicate Rising Antigravity Starlight Motes (8 * 4 = 32 verts — zero stiff ribbon tethers!)
    meta["wisps_start"] = ofs
    for k in range(8):
        b0 = ofs
        for j in range(2):
            for i in range(2):
                UV.append((0.52 + 0.46 * i, 0.02 + 0.46 * j))
                ofs += 1
        F.extend([(b0, b0 + 1, b0 + 3), (b0, b0 + 3, b0 + 2)])
    meta["wisps_end"] = ofs

    # B. 6 Orbiting Prismatic Sparkle Quads (6 * 4 = 24 verts)
    meta["sparks_start"] = ofs
    for k in range(6):
        b0 = ofs
        for j in range(2):
            for i in range(2):
                UV.append((0.52 + 0.46 * i, 0.02 + 0.46 * j))
                ofs += 1
        F.extend([(b0, b0 + 1, b0 + 3), (b0, b0 + 3, b0 + 2)])
    meta["sparks_end"] = ofs

    # C. 3 Crossed Grab-Charge Supernova Glow Corona Quads (3 * 4 = 12 verts)
    meta["corona_start"] = ofs
    for k in range(3):
        b0 = ofs
        for j in range(2):
            for i in range(2):
                UV.append((0.02 + 0.46 * i, 0.52 + 0.46 * j))
                ofs += 1
        F.extend([(b0, b0 + 1, b0 + 3), (b0, b0 + 3, b0 + 2)])
    meta["corona_end"] = ofs

    # D. 6 Spiraling Throw Rainbow Comet Ribbons (each 8x2 = 16 verts -> 96 verts)
    meta["comet_start"] = ofs
    for k in range(6):
        b0 = ofs
        for j in range(2):
            tv = float(j)
            for i in range(8):
                tu = i / 7.0
                UV.append((0.52 + 0.46 * tu, 0.52 + 0.46 * tv))
                ofs += 1
        F.extend((grid_tris(8, 2, wrap_u=False, flip=False) + b0).tolist())
    meta["comet_end"] = ofs
    meta["total_verts"] = ofs

    return np.array(UV, dtype=np.float64), np.array(F, dtype=np.int32), meta


# ===========================================================================
# 3. EXTRACT & DECIMATE 8 REAL 3D MODELS FROM BAKERSFIELDQUAKE VIA BLENDER 5.2!
# ===========================================================================
GHOST_3D_SPECS = [
    ("megaman",        "megaman.md3",                                  0,  "Mega Man Contraption"),
    ("mm_suit_rider",  "mm_suit_rider.md3",                            0,  "Suit Rider on Bar & Wheels"),
    ("pink_supercar",  "pink_supercar.md3",                            0,  "Exotic Pink Supercar"),
    ("mm_squat_rider", "mm_squat_rider.md3",                           0,  "Squat Rider on Bar & Wheels"),
    ("netsend_pc",     "netsend_pc.md3",                               20, "NetSend 90s CRT PC"),
    ("gw_horse",       "gw_horse.md3",                                 0,  "Golden West Casino Horse"),
    ("bigears",        "bigears.md3",                                  0,  "Sculpted Big-Ears 3D Head"),
    ("forklift",       "bklan/sr_vehicle_forklift_orange_a01.md3",     0,  "Larry's Warehouse Forklift"),
]


def load_and_decimate_real_3d_ghosts(target_verts_each=260):
    """Loads 8 real BakersfieldQuake MD3 models and uses Blender 5.2 Quadric Decimate to build crisp miniature ghosts."""
    all_V, all_N, all_UV, all_F = [], [], [], []
    slices = []
    v_ofs = 0

    for row_idx, (gid, rel_md3, fidx, label) in enumerate(GHOST_3D_SPECS):
        md3_path = os.path.join(PROGS_DIR, rel_md3)
        m = md3lib.read(md3_path)
        raw_v, raw_f = [], []
        vo = 0
        for s in m["surfaces"]:
            fi = min(fidx, len(s["frames"]) - 1)
            vv = np.array(s["frames"][fi][0], dtype=np.float64)
            # Flip MD3 clockwise -> Blender CCW!
            tt = np.array([(a, c, b) for a, b, c in s["tris"]], dtype=np.int32) + vo
            raw_v.append(vv)
            raw_f.append(tt)
            vo += len(vv)
        V0 = np.vstack(raw_v)
        F0 = np.vstack(raw_f)

        # Normalize into unit sphere centered at (0,0,0)
        mn, mx = V0.min(axis=0), V0.max(axis=0)
        ctr = 0.5 * (mn + mx)
        Vn = V0 - ctr
        rad = max(float(np.percentile(np.linalg.norm(Vn, axis=1), 99.2)), 1e-5)
        Vn = Vn / rad

        # Build mesh in Blender 5.2, weld close vertices, and apply Quadric Decimate!
        bpy.ops.wm.read_factory_settings(use_empty=True)
        me = bpy.data.meshes.new("g_src")
        me.from_pydata(Vn.tolist(), [], F0.tolist())
        me.update()
        ob = bpy.data.objects.new("g_obj", me)
        bpy.context.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=0.008)
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.mode_set(mode="OBJECT")

        cur_nv = len(ob.data.vertices)
        if cur_nv > target_verts_each:
            mod = ob.modifiers.new(name="Dec", type="DECIMATE")
            mod.decimate_type = "COLLAPSE"
            mod.ratio = max(0.02, min(1.0, target_verts_each / float(cur_nv)))
            bpy.ops.object.modifier_apply(modifier=mod.name)

        # If multi-shell model (e.g. Mega Man or Forklift) still exceeds 420 verts, weld micro-gaps & decimate once more
        if len(ob.data.vertices) > 420:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.remove_doubles(threshold=0.042)
            bpy.ops.object.mode_set(mode="OBJECT")
            if len(ob.data.vertices) > 380:
                mod2 = ob.modifiers.new(name="Dec2", type="DECIMATE")
                mod2.decimate_type = "COLLAPSE"
                mod2.ratio = max(0.05, min(1.0, 340.0 / float(len(ob.data.vertices))))
                bpy.ops.object.modifier_apply(modifier=mod2.name)

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.mode_set(mode="OBJECT")

        me_d = ob.data
        Vd = np.array([v.co[:] for v in me_d.vertices], dtype=np.float64)
        Fd = np.array([p.vertices[:] for p in me_d.polygons if len(p.vertices) == 3], dtype=np.int32)
        Nd = compute_normals(Vd, Fd)

        # Bake volumetric hologram shading into UV:
        #   u in [0.08..0.96]: combines vertical height, radial edge distance, & upward/outward normal rim!
        r_dist = np.clip(np.linalg.norm(Vd, axis=1), 0.0, 1.0)
        z_norm = np.clip((Vd[:, 2] - Vd[:, 2].min()) / max(1e-5, Vd[:, 2].max() - Vd[:, 2].min()), 0.0, 1.0)
        rim_est = np.clip(0.30 + 0.42 * (r_dist ** 1.1) + 0.28 * np.abs(Nd[:, 1]) + 0.16 * z_norm, 0.06, 0.96)
        v_band = (row_idx + 0.14 + 0.72 * z_norm) / 8.0
        UVd = np.column_stack([rim_est, v_band])

        slices.append((v_ofs, v_ofs + len(Vd), gid, label))
        all_V.append(Vd)
        all_N.append(Nd)
        all_UV.append(UVd)
        all_F.append(Fd + v_ofs)
        print(f"    [3D Ghost #{row_idx + 1}] {label:30s}: {len(Vd):4d} verts, {len(Fd):4d} tris")
        v_ofs += len(Vd)

    V_cat = np.vstack(all_V)
    N_cat = np.vstack(all_N)
    UV_cat = np.vstack(all_UV)
    F_cat = np.vstack(all_F)
    assert len(V_cat) <= 4096 and len(F_cat) <= 8192, f"Ghost 3D surface overflow: nv={len(V_cat)}, nt={len(F_cat)}"
    print(f"  [OK] Combined 8 Real 3D Ghosts in 1 surface: {len(V_cat)} verts, {len(F_cat)} tris")
    return V_cat, N_cat, UV_cat, F_cat, slices


# ===========================================================================
# 4. MASTER 16-VISION CRYSTAL-BALL SCHEDULE & 220-FRAME WEAPON CHOREOGRAPHY
# ===========================================================================
SPRITE_LABELS = [
    ("wheelman",      "Wheelman (Front Sprite)"),
    ("jesskart",      "JessKart Racer (Sprite)"),
    ("scissor",       "Scissor Man (Sprite)"),
    ("earhead",       "Earhead (Sprite)"),
    ("pickle",        "Pickle Surprise (Sprite)"),
    ("fr_rob",        "Friend Rob (Sprite)"),
    ("fr_johnhand",   "John Wave Hand (Sprite)"),
    ("wheelman_side", "Wheelman Rolling (Sprite)"),
]

# Interleave 8 Real 3D Models + 8 Real Sprites = 16 Magical Visions x 12 frames = 192 Idle Frames!
VISION_SCHEDULE = []
for k in range(8):
    VISION_SCHEDULE.append(("3d",  k, GHOST_3D_SPECS[k][2], GHOST_3D_SPECS[k][3]))
    VISION_SCHEDULE.append(("spr", k, 0,                    SPRITE_LABELS[k][1]))


def box_rotation_for_idle(fi, n_idle=192):
    """Smooth seamless multi-axis Mario-Kart tilted crystal spin over 192 frames (4 full revolutions!)."""
    u = fi / float(n_idle)
    spin_yaw = u * 4.0 * 360.0                      # 4 full 360° revolutions (7.5 deg/frame)
    wob_pitch = 22.0 * math.sin(u * 2.0 * 2.0 * math.pi + 0.4)
    wob_roll = 18.0 * math.cos(u * 2.0 * 2.0 * math.pi)
    # Base diagonal tilt like the reference Mario Kart Mystery Box!
    return rot_z_mat(spin_yaw) @ rot_y_mat(wob_pitch) @ rot_x_mat(24.0 + wob_roll)


def evaluate_vision_weights(fi, n_idle=192, frames_per_vis=12):
    """Returns list of active (kind, idx, weight, local_t) for cross-dissolving crystal-ball visions."""
    # Each vision k is centered on [k*12 .. (k+1)*12], with smooth 3-frame overlap swirl-dissolve!
    n_vis = len(VISION_SCHEDULE)
    active = []
    for v_i, (kind, sub_idx, _, _) in enumerate(VISION_SCHEDULE):
        start = v_i * frames_per_vis
        # Cyclic signed distance in frames from vision center (start + 6.0)
        center = start + 0.5 * frames_per_vis
        df = ((fi - center + 0.5 * n_idle) % n_idle) - 0.5 * n_idle
        half_span = 0.5 * frames_per_vis + 1.6  # 7.6-frame half-window -> smooth 3.2-frame crossfade!
        if abs(df) < half_span:
            w = 1.0 - sstep(0.5 * frames_per_vis - 1.6, half_span, abs(df))
            lt = (df + half_span) / (2.0 * half_span)  # 0 (materialize) -> 0.5 (peak) -> 1 (dissolve)
            if w > 0.005:
                active.append((kind, sub_idx, w, lt))
    return active


def build_all_models():
    os.makedirs(MD3_DIR, exist_ok=True)
    os.makedirs(GLB_DIR, exist_ok=True)
    os.makedirs(PREV_DIR, exist_ok=True)

    print("1/6 Extracting & Decimating 8 REAL BakersfieldQuake 3D Models via Blender 5.2...")
    # NOTE: Run ghost decimation BEFORE `build_and_bake_realistic_hand` because `load_and_decimate_real_3d_ghosts`
    # resets the Blender factory scene per ghost, whereas `hand_ob` & `arm_ob` must stay live for the 220-frame bake!
    V_g3d, N_g3d, UV_g3d, F_g3d, g3d_slices = load_and_decimate_real_3d_ghosts(target_verts_each=255)

    print("2/6 Sculpting Seamless Realistic Male Hand, Baking Cycles AO/SSS Skin & Rigging Armature...")
    hand_ob, arm_ob, orig_vi_arr, F_hand, UV_hand = srh.build_and_bake_realistic_hand(TEX_DIR, PROGS_DIR)
    print(f"  [OK] man_hand: {len(orig_vi_arr)} MD3 verts, {len(F_hand)} tris")

    print("3/6 Building Rounded Rainbow Crystal Cube, Smart '?' Emblems, Smoky Core & VFX...")
    V_glass, N_glass, UV_glass, F_glass = build_rounded_glass_cube(n_grid=9, bev=0.25)
    Q_grids, UV_qmark, F_qmark = build_qmark_face_emblems()
    V_core, UV_core, F_core = build_crystal_core_lens()
    V_gspr, UV_gspr, F_gspr = build_ghost_sprite_holograms()
    UV_fx, F_fx, fx_meta = build_magic_fx_parts()

    # =======================================================================
    # BAKE MODEL 1: FIRST-PERSON WEAPON VIEWMODEL (`progs/v_mysterybox.md3`, 220 frames)
    #   Frames   0..191 (192f): High-Floating Levitation Crystal-Ball Idle (16 Visions + huge air gap!)
    #   Frames 192..197 (  6f): GRAB (Hand surges up from below & cups box cleanly in pitcher C-grip)
    #   Frames 198..205 (  8f): GLOW / CHARGE (Box blazes w/ Supernova Corona & roulette visions!)
    #   Frames 206..212 (  7f): THROW (Arm whips forward, fingers splay open, box streaks downrange!)
    #   Frames 213..219 (  7f): RE-SUMMON (Hand lowers to open cradle, fresh box floats up in mid-air!)
    # =======================================================================
    print("4/6 Baking 220-frame First-Person Weapon Viewmodel (`v_mysterybox.md3`)...")
    NF_VM = 220
    N_IDLE = 192
    HAND_SCALE = 11.6
    R_BOX = 2.60

    fr_hand, fr_core, fr_g3d, fr_gspr, fr_glass, fr_qmark, fr_fx = [], [], [], [], [], [], []
    frame_names_vm = []

    # High-Floating Idle anchors in Quake 1st-person eye space (+X fwd, +Y screen-left, -Y screen-right, +Z up):
    #   - Expressive 3/4 semi-supinated right hand rests low in bottom-right (`Z = -10.55`, forearm exits far past corner!)
    #   - Mystery Box levitates HIGH in mid-air (`Z = +1.55`), creating ~9-11u of pure weightless open air!
    IDLE_WRIST = np.array([13.9, -6.8, -10.55], dtype=np.float64)
    IDLE_FDIR  = np.array([0.83,  0.46,  0.31], dtype=np.float64)
    IDLE_PDIR  = np.array([-0.30, 0.56,  0.77], dtype=np.float64)
    IDLE_BOX   = np.array([17.3, -3.6,  +1.55], dtype=np.float64)

    # Natural Pitcher C-Grip around right-bottom-rear of cube (thumb on top-right bevel, 4 fingers around far edge, front '?' clear!)
    GRAB_BOX   = np.array([14.8, -3.5, -0.15], dtype=np.float64)
    GRAB_FDIR  = np.array([0.78,  0.42, 0.46], dtype=np.float64)
    GRAB_PDIR  = np.array([-0.36, 0.76, 0.54], dtype=np.float64)
    GRAB_WRIST = np.array([14.55, -8.25, -3.95], dtype=np.float64)

    CHARGE_BOX   = np.array([13.85, -3.85, -0.30], dtype=np.float64)
    CHARGE_WRIST = np.array([13.60, -8.60, -4.10], dtype=np.float64)

    THROW_WRIST = np.array([17.0, -5.2, -6.30], dtype=np.float64)
    THROW_FDIR  = np.array([0.83,  0.36, 0.42], dtype=np.float64)
    THROW_PDIR  = np.array([0.36,  0.52, 0.77], dtype=np.float64)

    min_grip_sdf_raw = 999.0

    for fi in range(NF_VM):
        corona_scale = 0.0
        wisp_strength = 0.0
        spark_strength = 0.0
        comet_strength = 0.0
        force_full_qmark = False

        if fi < N_IDLE:
            # --- HIGH-FLOATING CRYSTAL-BALL IDLE (Frames 0..191) ---
            frame_names_vm.append(f"idle{fi:03d}")
            u_loop = fi / float(N_IDLE)
            bob_ph = u_loop * 6.0 * 2.0 * math.pi  # 6 weightless antigravity float cycles across 192 frames
            rip_ph = u_loop * 6.0 * 2.0 * math.pi

            # Hand breathes subtly with phase lag behind the floating box so they feel decoupled & weightless!
            hand_sway_y = 0.20 * math.sin(u_loop * 3.0 * 2.0 * math.pi - 0.55)
            hand_sway_z = 0.22 * math.sin(bob_ph - 0.65)
            wrist_pos = IDLE_WRIST + np.array([0.0, hand_sway_y, hand_sway_z])
            f_dir = IDLE_FDIR + np.array([0.0, 0.018 * math.sin(bob_ph - 0.5), 0.022 * math.sin(bob_ph - 0.65)])
            p_dir = IDLE_PDIR
            h_weights = (1.0, 0.0, 0.0)

            # Pronounced weightless mid-air levitation hover (±1.0u vertical + figure-8 drift!)
            bob_x = 0.28 * math.sin(bob_ph)
            bob_y = 0.46 * math.sin(u_loop * 3.0 * 2.0 * math.pi)
            bob_z = 0.88 * math.sin(bob_ph) + 0.18 * math.sin(bob_ph * 2.0)
            box_pos = IDLE_BOX + np.array([bob_x, bob_y, bob_z])
            box_R = box_rotation_for_idle(fi, N_IDLE)
            box_scale = R_BOX
            wisp_strength = 0.85 + 0.15 * math.sin(bob_ph * 2.0)
            spark_strength = 1.0
            corona_scale = 0.0  # Keep crystal-ball portal 100% clear during Idle!
            vis_list = evaluate_vision_weights(fi, N_IDLE, 12)

        elif fi < 198:
            # --- FIRE BEAT 1: SNATCH-GRAB OUT OF MID-AIR (Frames 192..197, 6 frames) ---
            jf = fi - 192
            frame_names_vm.append(f"grab{jf + 1}")
            kt = sstep(0.0, 1.0, (jf + 1) / 6.0)
            idle_w0 = IDLE_WRIST + np.array([0.0, 0.20 * math.sin(-0.55), 0.22 * math.sin(-0.65)])
            wrist_pos = idle_w0 * (1.0 - kt) + GRAB_WRIST * kt
            f_dir = IDLE_FDIR * (1.0 - kt) + GRAB_FDIR * kt
            p_dir = IDLE_PDIR * (1.0 - kt) + GRAB_PDIR * kt
            h_weights = (1.0 - kt, kt, 0.0)
            rip_ph = 0.0

            box_pos = IDLE_BOX * (1.0 - kt) + GRAB_BOX * kt
            # Turn +Y '?' face smoothly toward the camera as his hand snatches the floating box!
            box_R = rot_z_mat(kt * 56.0) @ box_rotation_for_idle(0, N_IDLE)
            box_scale = R_BOX * (1.0 - 0.03 * kt)
            wisp_strength = 1.0 - kt
            spark_strength = 1.0 + 0.65 * kt
            corona_scale = 0.0
            force_full_qmark = True
            vis_list = [("3d", jf % 8, 0.72, 0.5)]

        elif fi < 206:
            # --- FIRE BEAT 2: INTENSE MAGICAL GLOW / OVERCHARGE (Frames 198..205, 8 frames) ---
            jf = fi - 198
            frame_names_vm.append(f"glow{jf + 1}")
            ct = (jf + 1) / 8.0
            trem = np.array([
                0.14 * math.sin(jf * 2.7),
                0.15 * math.cos(jf * 3.4),
                0.14 * math.sin(jf * 4.1),
            ])
            wrist_pos = GRAB_WRIST * (1.0 - ct) + CHARGE_WRIST * ct + trem
            f_dir = GRAB_FDIR + np.array([-0.04 * ct, 0.0, 0.04 * ct])
            p_dir = GRAB_PDIR
            h_weights = (0.0, 1.0, 0.0)
            rip_ph = 0.0

            box_pos = GRAB_BOX * (1.0 - ct) + CHARGE_BOX * ct + trem
            box_R = rot_z_mat(56.0 + 16.0 * math.sin(ct * math.pi)) @ rot_x_mat(20.0 + 7.0 * math.sin(ct * 2.0 * math.pi))
            box_scale = R_BOX * (0.97 + 0.11 * math.sin(ct * math.pi * 0.85))
            corona_scale = 2.4 + 1.85 * math.sin(ct * math.pi * 0.85)
            spark_strength = 2.2
            force_full_qmark = True
            if jf % 2 == 0:
                vis_list = [("3d", (jf * 3) % 8, 0.72, 0.5)]
            else:
                vis_list = [("spr", (jf * 3) % 8, 0.82, 0.5)]

        elif fi < 213:
            # --- FIRE BEAT 3: WHIP-THROW & SPLAYED RELEASE (Frames 206..212, 7 frames) ---
            jf = fi - 206
            frame_names_vm.append(f"throw{jf + 1}")
            tt = sstep(0.0, 1.0, min(1.0, (jf + 1) / 3.5))
            wrist_pos = CHARGE_WRIST * (1.0 - tt) + THROW_WRIST * tt
            f_dir = GRAB_FDIR * (1.0 - tt) + THROW_FDIR * tt
            p_dir = GRAB_PDIR * (1.0 - tt) + THROW_PDIR * tt
            splay_k = sstep(0.0, 1.0, min(1.0, (jf + 0.6) / 2.2))
            h_weights = (0.0, 1.0 - splay_k, splay_k)
            rip_ph = 0.0

            if jf <= 3:
                ft_fly = (jf + 1) / 4.0
                box_pos = np.array([
                    19.4 + 43.0 * (ft_fly ** 1.12),
                    -3.2 * (1.0 - 0.78 * ft_fly),
                    0.35 + 2.2 * ft_fly,
                ], dtype=np.float64)
                box_R = rot_z_mat(106.0 + jf * 52.0) @ rot_x_mat(24.0 + jf * 32.0)
                box_scale = R_BOX * (1.06 - 0.12 * ft_fly)
                corona_scale = 4.4 * (1.0 - 0.55 * ft_fly)
                comet_strength = 1.0
                spark_strength = 1.5
                force_full_qmark = True
                vis_list = [("3d", 0, 1.0, 0.5)]
            else:
                box_pos = np.array([0.0, 0.0, -60.0], dtype=np.float64)
                box_R = np.eye(3)
                box_scale = 0.0005
                corona_scale = 0.0
                comet_strength = 0.0
                spark_strength = 0.0
                vis_list = []

        else:
            # --- FIRE BEAT 4: TELEKINETIC RE-SUMMON (Frames 213..219, 7 frames -> seamless into Frame 0!) ---
            jf = fi - 213
            frame_names_vm.append(f"summon{jf + 1}")
            rt = (jf + 1) / 7.0
            rk = sstep(0.0, 1.0, rt)
            idle_w0 = IDLE_WRIST + np.array([0.0, 0.20 * math.sin(-0.55), 0.22 * math.sin(-0.65)])
            wrist_pos = THROW_WRIST * (1.0 - rk) + idle_w0 * rk
            f_dir = THROW_FDIR * (1.0 - rk) + IDLE_FDIR * rk
            p_dir = THROW_PDIR * (1.0 - rk) + IDLE_PDIR * rk
            h_weights = (rk, 0.0, 1.0 - rk)
            rip_ph = 0.0

            # Fresh Mystery Box blooms in high mid-air levitation above his open hand!
            pop_t = sstep(0.12, 0.92, rt)
            overshoot = 1.0 + 0.08 * math.sin(pop_t * math.pi) * (1.0 - pop_t)
            box_pos = IDLE_BOX + np.array([0.0, 0.0, -2.4 * (1.0 - pop_t)])
            box_R = rot_z_mat((1.0 - pop_t) * -120.0) @ box_rotation_for_idle(0, N_IDLE)
            box_scale = max(0.001, R_BOX * pop_t * overshoot)
            wisp_strength = 0.85 * pop_t
            spark_strength = 1.8 * math.sin(rt * math.pi * 0.85) + 0.6 * pop_t
            corona_scale = 2.4 * math.sin(rt * math.pi) * (1.0 - 0.92 * pop_t)
            vis_list = evaluate_vision_weights(0, N_IDLE, 12) if pop_t > 0.35 else []

        # --- 1. Evaluate Posed Realistic Male Hand via Blender Armature + CorrectiveSmooth ---
        wR = hand_world_basis(f_dir, p_dir)
        h_pose = realistic_hand_pose(h_weights, ripple_phase=rip_ph)
        Vh_f = srh.evaluate_posed_hand(hand_ob, arm_ob, orig_vi_arr, h_pose, wR, wrist_pos, scale=HAND_SCALE)

        # Exact SDF skin-to-glass contact guard during Grab & Glow so zero skin triangles ever clip inside the cube!
        if 193 <= fi <= 205 and box_scale > 0.5:
            sdf_vals = rounded_box_sdf_world(Vh_f, box_pos, box_R, box_scale, bev=0.25)
            cur_min = float(np.min(sdf_vals))
            min_grip_sdf_raw = min(min_grip_sdf_raw, cur_min)
            if cur_min < 0.04:
                push_dir = wR[:, 0]  # +X_h dorsal (away from inner palm & box center)
                Vh_f = Vh_f + push_dir[None, :] * (0.05 - cur_min)

        Nh_f = compute_normals(Vh_f, F_hand)
        fr_hand.append((Vh_f, Nh_f))

        # --- 2. Transform Outer Rounded Rainbow Glass Cube ---
        Vg_f = (V_glass * box_scale) @ box_R.T + box_pos
        Ng_f = N_glass @ box_R.T
        fr_glass.append((Vg_f, Ng_f))

        # --- 3. Camera-Oriented Smoky Cosmic Crystal-Ball Core ---
        if box_scale < 0.01:
            Vc_f = np.broadcast_to(box_pos, V_core.shape).copy()
            Nc_f = np.broadcast_to(np.array([-1.0, 0.0, 0.0]), V_core.shape).copy()
        else:
            to_eye = -box_pos
            to_eye_n = to_eye / (np.linalg.norm(to_eye) + 1e-12)
            # Basis where -X_core faces to_eye_n (+X_core = -to_eye_n)
            cx_c = -to_eye_n
            up_c = np.array([0.0, 0.0, 1.0])
            cy_c = np.cross(up_c, cx_c)
            cy_c /= (np.linalg.norm(cy_c) + 1e-12)
            cz_c = np.cross(cx_c, cy_c)
            R_bill = np.column_stack([cx_c, cy_c, cz_c])
            # Gently swirl the cosmic nebula around cx_c!
            R_swirl = rot_axis_mat(cx_c, (fi / float(N_IDLE)) * 2.0 * 360.0) @ R_bill
            Vc_f = (V_core * (box_scale * 0.90)) @ R_swirl.T + box_pos
            Nc_f = compute_normals(Vc_f, F_core)
        fr_core.append((Vc_f, Nc_f))

        # --- 4. Smart '?' Face Emblems (2 opposite lateral faces: 1 visible at a time + open crystal window!) ---
        Vq_list, Nq_list = [], []
        to_eye_dir = -box_pos / (np.linalg.norm(box_pos) + 1e-12)
        for q_i, face_i in enumerate(QMARK_FACE_INDICES):
            fn_loc, ua_loc, va_loc = CUBE_FACES[face_i]
            fn_w = box_R @ fn_loc
            align = float(np.dot(fn_w, to_eye_dir))
            if (not force_full_qmark) and len(vis_list) > 0 and align > 0.62:
                # Smoothly iris-glide dead-center '?' into a neat corner emblem so the crystal ball stays unobstructed!
                open_k = sstep(0.62, 0.90, align)
                qm_sc = 0.72 * (1.0 - 0.52 * open_k)
                off_u = 0.44 * open_k
                off_v = -0.44 * open_k
            else:
                qm_sc = 0.78 if force_full_qmark else 0.72
                off_u = 0.0
                off_v = 0.0

            grid_uv = Q_grids[q_i]  # (16, 2) in [-1, 1]
            for su, sv in grid_uv:
                pu = off_u + su * qm_sc
                pv = off_v - sv * qm_sc
                p_loc = fn_loc * 1.012 + ua_loc * pu + va_loc * pv
                # Conform gently to rounded cube fillet so '?' never pokes past corners
                c_in = np.clip(p_loc, -0.75, 0.75)
                d_v = p_loc - c_in
                dn_v = np.linalg.norm(d_v)
                q_loc = c_in + 0.262 * (d_v / max(dn_v, 1e-9))
                Vq_list.append((q_loc * box_scale) @ box_R.T + box_pos)
                Nq_list.append(fn_w)
        fr_qmark.append((np.array(Vq_list, dtype=np.float64), np.array(Nq_list, dtype=np.float64)))

        # --- 5. Active 3D & Sprite Ghostly Visions Inside the Crystal Ball! ---
        Vg3d_f = np.broadcast_to(box_pos, V_g3d.shape).copy()
        Ng3d_f = N_g3d.copy()
        Vgspr_f = np.broadcast_to(box_pos, V_gspr.shape).copy()
        Ngspr_f = np.broadcast_to(np.array([-1.0, 0.0, 0.0]), V_gspr.shape).copy()

        if box_scale > 0.05 and len(vis_list) > 0:
            for kind, sub_idx, w_vis, lt_vis in vis_list:
                # Ethereal swirl-in / spin / swirl-out scale & rotation
                vis_sc = box_scale * 0.86 * (w_vis ** 0.55)
                bob_v = np.array([0.0, 0.0, 0.14 * box_scale * math.sin(lt_vis * 2.0 * math.pi)])
                if kind == "3d":
                    s0, s1, _, _ = g3d_slices[sub_idx]
                    # Full 3D turnaround inside the crystal ball so you see every angle of Mega Man / Riders / Supercar!
                    yaw_g = -35.0 + lt_vis * 390.0 + (fi * 3.0 if fi >= 198 else 0.0)
                    pitch_g = 14.0 * math.sin(lt_vis * math.pi)
                    R_g = rot_z_mat(yaw_g) @ rot_y_mat(pitch_g)
                    Vg3d_f[s0:s1] = (V_g3d[s0:s1] * vis_sc) @ R_g.T + (box_pos + bob_v)
                    Ng3d_f[s0:s1] = N_g3d[s0:s1] @ R_g.T
                else:
                    s0 = sub_idx * 16
                    s1 = s0 + 16
                    # Face player eye with gentle +/-22 deg ghostly crystal parallax sway!
                    sway_ang = 22.0 * math.sin((lt_vis - 0.5) * math.pi * 1.4)
                    tilt_ang = 8.0 * math.cos(lt_vis * 2.0 * math.pi)
                    R_sp = R_bill @ rot_z_mat(sway_ang) @ rot_y_mat(tilt_ang)
                    Vgspr_f[s0:s1] = (V_gspr[s0:s1] * (vis_sc * 0.96)) @ R_sp.T + (box_pos + bob_v)
                    Ngspr_f[s0:s1] = np.broadcast_to(-cx_c, (16, 3))

        fr_g3d.append((Vg3d_f, Ng3d_f))
        fr_gspr.append((Vgspr_f, Ngspr_f))

        # --- 6. Multi-Stage Arcane VFX (`box_fx`) ---
        Vfx_f = np.broadcast_to(box_pos, (fx_meta["total_verts"], 3)).copy()
        # Palm center ~ 3.6u distal along hand from wrist
        palm_ctr = wrist_pos + (wR @ np.array([-0.08, 0.0, 0.34])) * HAND_SCALE

        # A. 8 Delicate Rising Antigravity Starlight Motes across the wide open air gap (zero stiff ribbons!)
        if wisp_strength > 0.02 and box_scale > 0.05:
            idx_w = fx_meta["wisps_start"]
            R_mote = R_bill if box_scale >= 0.01 else np.eye(3)
            cyc_u = (fi % N_IDLE) / float(N_IDLE)
            gap_bot = palm_ctr + np.array([0.0, 0.0, 1.35])
            gap_top = box_pos + np.array([0.0, 0.0, -box_scale * 1.18])
            for k in range(8):
                prog = (cyc_u * 3.0 + k / 8.0) % 1.0  # 3 seamless upward rises per 192-frame loop!
                fade = math.sin(prog * math.pi)
                mid = gap_bot * (1.0 - prog) + gap_top * prog
                hel_a = prog * 2.6 + k * (2.0 * math.pi / 8.0) + cyc_u * 2.0 * math.pi
                hel_r = (1.65 - 0.55 * prog) * (0.75 + 0.25 * math.sin(k * 2.1))
                m_ctr = mid + np.array([hel_r * math.cos(hel_a), hel_r * math.sin(hel_a), 0.0])
                m_sz = (0.14 + 0.16 * max(0.0, math.sin(fi * 0.28 + k * 1.9))) * fade * wisp_strength
                for j in range(2):
                    for i in range(2):
                        su = (i * 2.0 - 1.0) * m_sz
                        sv = (j * 2.0 - 1.0) * m_sz
                        Vfx_f[idx_w] = m_ctr + R_mote @ np.array([0.0, -su, -sv])
                        idx_w += 1

        # B. 6 Orbiting 8-Point Prismatic Sparkle Stars
        if spark_strength > 0.02 and box_scale > 0.01:
            idx_s = fx_meta["sparks_start"]
            R_sp_b = R_bill if box_scale >= 0.01 else np.eye(3)
            for k in range(6):
                orb_a = (fi * 0.14) + k * (2.0 * math.pi / 6.0)
                orb_r = (R_BOX * 1.32) * (0.85 + 0.20 * math.sin(fi * 0.18 + k))
                orb_z = R_BOX * 0.72 * math.sin(orb_a * 1.5 + k)
                s_ctr = box_pos + np.array([orb_r * math.cos(orb_a), orb_r * math.sin(orb_a), orb_z])
                pulse = (0.42 + 0.24 * max(0.0, math.sin(fi * 0.32 + k * 1.7))) * spark_strength
                for j in range(2):
                    for i in range(2):
                        su = (i * 2.0 - 1.0) * pulse
                        sv = (j * 2.0 - 1.0) * pulse
                        Vfx_f[idx_s] = s_ctr + R_sp_b @ np.array([-0.1, -su, -sv])
                        idx_s += 1

        # C. 3 Counter-Rotating Supernova Glow Corona Quads (halo BEHIND the gripped box so front glass stays crisp!)
        if corona_scale > 0.02 and box_scale > 0.01:
            idx_c = fx_meta["corona_start"]
            R_c0 = R_bill if box_scale >= 0.01 else np.eye(3)
            corona_planes = [
                R_c0 @ rot_x_mat(fi * 11.0),
                R_c0 @ rot_x_mat(-fi * 8.0 + 30.0),
                R_c0 @ rot_x_mat(fi * 14.0 + 60.0),
            ]
            sc_mults = (1.05, 0.86, 0.68)
            for k in range(3):
                Rk = corona_planes[k]
                sc_c = corona_scale * sc_mults[k]
                bias = (-1.75 - 0.18 * k) * R_BOX * to_eye_dir
                for j in range(2):
                    for i in range(2):
                        su = (i * 2.0 - 1.0) * sc_c
                        sv = (j * 2.0 - 1.0) * sc_c
                        Vfx_f[idx_c] = box_pos + bias + Rk @ np.array([0.0, -su, -sv])
                        idx_c += 1

        # D. 6 Spiraling Throw Rainbow Comet Ribbons (unfurl behind hurled box!)
        if comet_strength > 0.02:
            idx_m = fx_meta["comet_start"]
            for k in range(6):
                base_a = k * (2.0 * math.pi / 6.0) + fi * 0.65
                for j in range(2):
                    sv = (j * 2.0 - 1.0) * 0.58 * comet_strength
                    for i in range(8):
                        tu = i / 7.0
                        trail_len = 18.0 * comet_strength
                        ang = base_a + tu * 2.4
                        rr = R_BOX * (0.72 * (1.0 - 0.55 * tu))
                        tang = np.array([0.0, -math.sin(ang), math.cos(ang)]) * sv * (1.0 - 0.4 * tu)
                        Vfx_f[idx_m] = box_pos + np.array([-tu * trail_len, rr * math.cos(ang), rr * math.sin(ang)]) + tang
                        idx_m += 1

        Nfx_f = compute_normals(Vfx_f, F_fx)
        fr_fx.append((Vfx_f, Nfx_f))

    print(f"  [CONTACT CHECK] Raw pre-guard min SDF during Grab/Glow: {min_grip_sdf_raw:+.3f} Quake units (post-guard >= +0.050u)")

    def pack_surf(name, shader, F_tri, UV_arr, frames_vn):
        # Flip CCW -> MD3 Clockwise winding!
        tris_cw = [(int(a), int(c), int(b)) for a, b, c in F_tri]
        st_l = [(float(u), float(v)) for u, v in UV_arr]
        fr_l = [
            ([(float(p[0]), float(p[1]), float(p[2])) for p in V_f],
             [(float(n[0]), float(n[1]), float(n[2])) for n in N_f])
            for V_f, N_f in frames_vn
        ]
        return dict(name=name, shader=shader, tris=tris_cw, st=st_l, frames=fr_l)

    # STRICT OPTICAL DRAW ORDER: Opaque Hand -> Smoky Core -> 3D Ghosts -> Sprite Ghosts -> Rainbow Glass -> '?' -> Glow FX!
    vm_surfs = [
        pack_surf("man_hand",     "progs/mbox_hand",      F_hand,  UV_hand,  fr_hand),
        pack_surf("crystal_core", "progs/mbox_core",      F_core,  UV_core,  fr_core),
        pack_surf("ghost_3d",     "progs/mbox_ghost_3d",  F_g3d,   UV_g3d,   fr_g3d),
        pack_surf("ghost_spr",    "progs/mbox_ghost_spr", F_gspr,  UV_gspr,  fr_gspr),
        pack_surf("box_glass",    "progs/mbox_glass",     F_glass, UV_glass, fr_glass),
        pack_surf("box_qmark",    "progs/mbox_qmark",     F_qmark, UV_qmark, fr_qmark),
        pack_surf("box_fx",       "progs/mbox_fx",        F_fx,    UV_fx,    fr_fx),
    ]

    def export_md3_and_skin(model_name, surfs, copy_to_progs=True):
        nf = len(surfs[0]["frames"])
        for s in surfs:
            assert len(s["st"]) <= 4096 and len(s["tris"]) <= 8192, f"Overflow on {s['name']}"
        stage_p = os.path.join(MD3_DIR, f"{model_name}.md3")
        md3lib.write(stage_p, dict(name=model_name, surfaces=surfs, nframes=nf))
        rt = md3lib.read(stage_p)
        assert rt["nframes"] == nf
        skin_txt = "\n".join(f"{s['name']},{s['shader']}" for s in surfs) + "\n"
        open(stage_p + "_0.skin", "w", encoding="ascii", newline="\n").write(skin_txt)
        if copy_to_progs:
            progs_p = os.path.join(PROGS_DIR, f"{model_name}.md3")
            shutil.copy2(stage_p, progs_p)
            open(progs_p + "_0.skin", "w", encoding="ascii", newline="\n").write(skin_txt)
        tv = sum(len(s["st"]) for s in surfs)
        tt = sum(len(s["tris"]) for s in surfs)
        sz_mb = os.path.getsize(stage_p) / 1e6
        print(f"  [MD3 OK] {model_name:20s}: {len(surfs)} surfs, {tv:4d} verts, {tt:4d} tris, {nf:3d} frames ({sz_mb:.2f} MB)")

    export_md3_and_skin("v_mysterybox", vm_surfs, copy_to_progs=True)

    # =======================================================================
    # BAKE MODEL 2: THROWN PROJECTILE (`progs/proj_mysterybox.md3`, 32 frames)
    # =======================================================================
    print("5/6 Baking 32-frame Thrown Projectile (`proj_mysterybox.md3`) & 192-frame Close-Up Crystal Turnaround...")
    NF_PROJ = 32
    R_PROJ = 6.8
    p_core, p_g3d, p_glass, p_qmark, p_fx = [], [], [], [], []
    for fi in range(NF_PROJ):
        u = fi / float(NF_PROJ)
        R_b = rot_z_mat(u * 360.0) @ rot_x_mat(25.0 + u * 360.0) @ rot_y_mat(18.0)
        p_glass.append(((V_glass * R_PROJ) @ R_b.T, N_glass @ R_b.T))
        p_core.append(((V_core * (R_PROJ * 0.88)) @ rot_z_mat(u * 360.0).T, compute_normals(V_core, F_core)))

        # Bold '?' emblems on the 2 opposite lateral faces of thrown projectile
        Vq_p, Nq_p = [], []
        for q_i, face_i in enumerate(QMARK_FACE_INDICES):
            fn_loc, ua_loc, va_loc = CUBE_FACES[face_i]
            fn_w = R_b @ fn_loc
            for su, sv in Q_grids[q_i]:
                p_loc = fn_loc * 1.012 + ua_loc * (su * 0.76) - va_loc * (sv * 0.76)
                c_in = np.clip(p_loc, -0.75, 0.75)
                d_v = p_loc - c_in
                q_loc = c_in + 0.262 * (d_v / max(np.linalg.norm(d_v), 1e-9))
                Vq_p.append((q_loc * R_PROJ) @ R_b.T)
                Nq_p.append(fn_w)
        p_qmark.append((np.array(Vq_p), np.array(Nq_p)))

        # Cycle 4 signature 3D ghosts (Mega Man, Suit Rider, Pink Supercar, Squat Rider) inside projectile!
        Vg_p = np.zeros_like(V_g3d)
        Ng_p = N_g3d.copy()
        act_idx = (fi // 8) % 4
        s0, s1, _, _ = g3d_slices[act_idx]
        Rg = rot_z_mat(u * 720.0)
        Vg_p[s0:s1] = (V_g3d[s0:s1] * (R_PROJ * 0.82)) @ Rg.T
        Ng_p[s0:s1] = N_g3d[s0:s1] @ Rg.T
        p_g3d.append((Vg_p, Ng_p))

        # Trailing rainbow comet ribbons (-X wake) + glowing aura!
        Vfx_p = np.zeros((fx_meta["total_verts"], 3), dtype=np.float64)
        idx_s = fx_meta["sparks_start"]
        for k in range(6):
            oa = u * 4.0 * math.pi + k * (math.pi / 3.0)
            s_ctr = np.array([-2.0 * k, R_PROJ * 1.25 * math.cos(oa), R_PROJ * 1.25 * math.sin(oa)])
            for j in range(2):
                for i in range(2):
                    Vfx_p[idx_s] = s_ctr + np.array([0.0, (i * 2 - 1) * 1.3, (j * 2 - 1) * 1.3])
                    idx_s += 1
        idx_c = fx_meta["corona_start"]
        for k in range(3):
            Rk = rot_z_mat(k * 60.0 + u * 360.0)
            for j in range(2):
                for i in range(2):
                    Vfx_p[idx_c] = Rk @ np.array([0.0, (i * 2 - 1) * R_PROJ * 1.35, (j * 2 - 1) * R_PROJ * 1.35])
                    idx_c += 1
        idx_m = fx_meta["comet_start"]
        for k in range(6):
            ba = k * (math.pi / 3.0) + u * 4.0 * math.pi
            for j in range(2):
                sv = (j * 2.0 - 1.0) * 1.25
                for i in range(8):
                    tu = i / 7.0
                    ang = ba + tu * 2.6
                    rr = R_PROJ * 0.78 * (1.0 - 0.5 * tu)
                    tang = np.array([0.0, -math.sin(ang), math.cos(ang)]) * sv
                    Vfx_p[idx_m] = np.array([-tu * 32.0, rr * math.cos(ang), rr * math.sin(ang)]) + tang
                    idx_m += 1
        p_fx.append((Vfx_p, compute_normals(Vfx_p, F_fx)))

    proj_surfs = [
        pack_surf("crystal_core", "progs/mbox_core",     F_core,  UV_core,  p_core),
        pack_surf("ghost_3d",     "progs/mbox_ghost_3d", F_g3d,   UV_g3d,   p_g3d),
        pack_surf("box_glass",    "progs/mbox_glass",    F_glass, UV_glass, p_glass),
        pack_surf("box_qmark",    "progs/mbox_qmark",    F_qmark, UV_qmark, p_qmark),
        pack_surf("box_fx",       "progs/mbox_fx",       F_fx,    UV_fx,    p_fx),
    ]
    export_md3_and_skin("proj_mysterybox", proj_surfs, copy_to_progs=True)

    # =======================================================================
    # BAKE MODEL 3: HERO CLOSE-UP CRYSTAL BALL TURNAROUND (`mysterybox_closeup.md3`, 192 frames)
    # =======================================================================
    R_HERO = 10.5
    c_core, c_g3d, c_gspr, c_glass, c_qmark, c_fx = [], [], [], [], [], []
    eye_dir_hero = np.array([1.0, 0.0, 0.0])  # viewer orbits from +X front by default
    for fi in range(N_IDLE):
        u_loop = fi / float(N_IDLE)
        bob_z = 0.85 * math.sin(u_loop * 6.0 * 2.0 * math.pi)
        b_pos = np.array([0.0, 0.0, bob_z])
        R_b = box_rotation_for_idle(fi, N_IDLE)

        c_glass.append(((V_glass * R_HERO) @ R_b.T + b_pos, N_glass @ R_b.T))
        # Core faces +X front viewer
        R_cb = rot_z_mat(180.0) @ rot_x_mat(u_loop * 720.0)
        c_core.append(((V_core * (R_HERO * 0.88)) @ R_cb.T + b_pos, compute_normals(V_core, F_core)))

        vis_list = evaluate_vision_weights(fi, N_IDLE, 12)
        Vq_c, Nq_c = [], []
        for q_i, face_i in enumerate(QMARK_FACE_INDICES):
            fn_loc, ua_loc, va_loc = CUBE_FACES[face_i]
            fn_w = R_b @ fn_loc
            align = float(np.dot(fn_w, eye_dir_hero))
            if len(vis_list) > 0 and align > 0.62:
                open_k = sstep(0.62, 0.90, align)
                qm_sc = 0.72 * (1.0 - 0.52 * open_k)
                off_u, off_v = 0.44 * open_k, -0.44 * open_k
            else:
                qm_sc, off_u, off_v = 0.72, 0.0, 0.0
            for su, sv in Q_grids[q_i]:
                p_loc = fn_loc * 1.012 + ua_loc * (off_u + su * qm_sc) + va_loc * (off_v - sv * qm_sc)
                c_in = np.clip(p_loc, -0.75, 0.75)
                d_v = p_loc - c_in
                q_loc = c_in + 0.262 * (d_v / max(np.linalg.norm(d_v), 1e-9))
                Vq_c.append((q_loc * R_HERO) @ R_b.T + b_pos)
                Nq_c.append(fn_w)
        c_qmark.append((np.array(Vq_c), np.array(Nq_c)))

        Vg3d_c = np.broadcast_to(b_pos, V_g3d.shape).copy()
        Ng3d_c = N_g3d.copy()
        Vgspr_c = np.broadcast_to(b_pos, V_gspr.shape).copy()
        Ngspr_c = np.broadcast_to(eye_dir_hero, V_gspr.shape).copy()
        for kind, sub_idx, w_vis, lt_vis in vis_list:
            vis_sc = R_HERO * 0.86 * (w_vis ** 0.55)
            if kind == "3d":
                s0, s1, _, _ = g3d_slices[sub_idx]
                Rg = rot_z_mat(-25.0 + lt_vis * 390.0) @ rot_y_mat(14.0 * math.sin(lt_vis * math.pi))
                Vg3d_c[s0:s1] = (V_g3d[s0:s1] * vis_sc) @ Rg.T + b_pos
                Ng3d_c[s0:s1] = N_g3d[s0:s1] @ Rg.T
            else:
                s0, s1 = sub_idx * 16, (sub_idx + 1) * 16
                # Face +X viewer (rotate 180 around Z since V_gspr faces -X by default!)
                Rsp = rot_z_mat(180.0 + 22.0 * math.sin((lt_vis - 0.5) * math.pi * 1.4))
                Vgspr_c[s0:s1] = (V_gspr[s0:s1] * (vis_sc * 0.96)) @ Rsp.T + b_pos
        c_g3d.append((Vg3d_c, Ng3d_c))
        c_gspr.append((Vgspr_c, Ngspr_c))

        Vfx_c = np.broadcast_to(b_pos, (fx_meta["total_verts"], 3)).copy()
        idx_s = fx_meta["sparks_start"]
        for k in range(6):
            oa = (fi * 0.14) + k * (math.pi / 3.0)
            s_ctr = b_pos + np.array([R_HERO * 1.26 * math.cos(oa), R_HERO * 1.26 * math.sin(oa), R_HERO * 0.65 * math.sin(oa * 1.5)])
            pulse = 1.35 + 0.55 * max(0.0, math.sin(fi * 0.32 + k * 1.7))
            for j in range(2):
                for i in range(2):
                    Vfx_c[idx_s] = s_ctr + np.array([0.0, (i * 2 - 1) * pulse, (j * 2 - 1) * pulse])
                    idx_s += 1
        c_fx.append((Vfx_c, compute_normals(Vfx_c, F_fx)))

    hero_surfs = [
        pack_surf("crystal_core", "progs/mbox_core",      F_core,  UV_core,  c_core),
        pack_surf("ghost_3d",     "progs/mbox_ghost_3d",  F_g3d,   UV_g3d,   c_g3d),
        pack_surf("ghost_spr",    "progs/mbox_ghost_spr", F_gspr,  UV_gspr,  c_gspr),
        pack_surf("box_glass",    "progs/mbox_glass",     F_glass, UV_glass, c_glass),
        pack_surf("box_qmark",    "progs/mbox_qmark",     F_qmark, UV_qmark, c_qmark),
        pack_surf("box_fx",       "progs/mbox_fx",        F_fx,    UV_fx,    c_fx),
    ]
    export_md3_and_skin("mysterybox_closeup", hero_surfs, copy_to_progs=False)

    # =======================================================================
    # WRITE QUAKE / DARKPLACES SHADER (`scripts/mysterybox.shader`)
    # =======================================================================
    shader_txt = """// written by source/mm_tools/mystery_box/build_mbox_models.py

progs/mbox_hand
{
\tcull none
\t{
\t\tmap progs/mbox_hand
\t\trgbGen lightingDiffuse
\t}
}

progs/mbox_core
{
\tcull none
\tsort 8
\t{
\t\tmap progs/mbox_qmark
\t\tblendfunc blend
\t\trgbGen identity
\t}
}

progs/mbox_ghost_3d
{
\tcull none
\tsort 9
\t{
\t\tmap progs/mbox_ghost_3d
\t\tblendfunc add
\t\trgbGen identity
\t}
}

progs/mbox_ghost_spr
{
\tcull none
\tsort 9
\t{
\t\tmap progs/mbox_ghost_spr
\t\tblendfunc add
\t\trgbGen identity
\t}
}

progs/mbox_glass
{
\tcull none
\tsort 10
\t{
\t\tmap progs/mbox_glass
\t\tblendfunc blend
\t\trgbGen identity
\t}
}

progs/mbox_qmark
{
\tsort 11
\t{
\t\tmap progs/mbox_qmark
\t\tblendfunc blend
\t\trgbGen identity
\t}
}

progs/mbox_fx
{
\tcull none
\tsort 12
\t{
\t\tmap progs/mbox_fx
\t\tblendfunc add
\t\trgbGen identity
\t}
}
"""
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    open(os.path.join(SCRIPTS_DIR, "mysterybox.shader"), "w", encoding="ascii", newline="\n").write(shader_txt)
    print("  [SHADER OK] scripts/mysterybox.shader")

    # Save vision metadata JSON for the WebGL2 Studio!
    meta_json = dict(
        nFrames=NF_VM,
        nIdle=N_IDLE,
        visions=[
            dict(
                index=vi,
                kind=kind,
                subIdx=sub_idx,
                label=lbl,
                startFrame=vi * 12,
                peakFrame=vi * 12 + 6,
                endFrame=(vi + 1) * 12 - 1,
            )
            for vi, (kind, sub_idx, _, lbl) in enumerate(VISION_SCHEDULE)
        ],
        fireBeats=dict(
            grab=[192, 197],
            glow=[198, 205],
            throw=[206, 212],
            releaseFrame=210,
            summon=[213, 219],
        ),
    )
    open(os.path.join(OUT_ROOT, "mbox_meta.json"), "w", encoding="utf-8").write(json.dumps(meta_json, indent=2))

    # =======================================================================
    # 5. EXPORT UNIVERSAL PBR + ALPHA-GLASS + EMISSIVE-HOLOGRAM `.GLB` FILES & RENDERS!
    # =======================================================================
    print("6/6 Exporting universal PBR `.GLB` files & rendering 8-panel Blender 5.2 EEVEE sheet...")

    SURF_GLB_STYLE = {
        "man_hand":     dict(tex="mbox_hand_web.png",      mode="OPAQUE", rough=0.50, spec=0.38, emit=0.0),
        "crystal_core": dict(tex="mbox_qmark.png",         mode="BLEND",  rough=0.25, spec=0.40, emit=0.30),
        "ghost_3d":     dict(tex="mbox_ghost_3d_glb.png",  mode="BLEND",  rough=0.20, spec=0.20, emit=4.20),
        "ghost_spr":    dict(tex="mbox_ghost_spr_glb.png", mode="BLEND",  rough=0.20, spec=0.20, emit=4.20),
        "box_glass":    dict(tex="mbox_glass.png",         mode="BLEND",  rough=0.08, spec=0.95, emit=0.28),
        "box_qmark":    dict(tex="mbox_qmark.png",         mode="BLEND",  rough=0.14, spec=0.80, emit=0.90),
        "box_fx":       dict(tex="mbox_fx_glb.png",        mode="BLEND",  rough=0.20, spec=0.10, emit=2.60),
    }

    def populate_blender_scene(surfs, frame_idx):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        for s in surfs:
            sname = s["name"]
            st_cfg = SURF_GLB_STYLE[sname]
            V_f, _ = s["frames"][frame_idx]
            me = bpy.data.meshes.new(sname)
            # Quake (+X fwd, +Y left, +Z up) -> Blender (+X right = -Y_q, +Y fwd = +X_q, +Z up = +Z_q)
            b_verts = [(-p[1], p[0], p[2]) for p in V_f]
            b_faces = [(t[0], t[2], t[1]) for t in s["tris"]]
            # Skip degenerate collapsed faces for single-frame static GLB cleanliness
            valid_faces = []
            seen_f = set()
            for a, b, c in b_faces:
                if a == b or b == c or a == c:
                    continue
                key = tuple(sorted((a, b, c)))
                if key in seen_f:
                    continue
                pa, pb, pc = np.array(b_verts[a]), np.array(b_verts[b]), np.array(b_verts[c])
                if np.linalg.norm(np.cross(pb - pa, pc - pa)) > 1e-6:
                    seen_f.add(key)
                    valid_faces.append((a, b, c))
            if not valid_faces:
                continue
            me.from_pydata(b_verts, [], valid_faces)
            me.validate(verbose=False)
            me.update()
            for poly in me.polygons:
                poly.use_smooth = True

            uv_layer = me.uv_layers.new(name="UVMap")
            st = s["st"]
            for loop in me.loops:
                u, v = st[loop.vertex_index]
                uv_layer.data[loop.index].uv = (u, 1.0 - v)

            mat = bpy.data.materials.new(name=sname + "_mat")
            mat.use_nodes = True
            mat.use_backface_culling = (sname in ("man_hand", "box_qmark"))
            if st_cfg["mode"] == "BLEND":
                if hasattr(mat, "surface_render_method"):
                    mat.surface_render_method = "BLENDED"
                if hasattr(mat, "blend_method"):
                    mat.blend_method = "BLEND"

            nt = mat.node_tree
            bsdf = nt.nodes.get("Principled BSDF")
            bsdf.inputs["Roughness"].default_value = st_cfg["rough"]
            tex_node = nt.nodes.new("ShaderNodeTexImage")
            tex_node.image = bpy.data.images.load(os.path.join(TEX_DIR, st_cfg["tex"]), check_existing=True)
            nt.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
            if st_cfg["mode"] == "BLEND":
                nt.links.new(bsdf.inputs["Alpha"], tex_node.outputs["Alpha"])
            if st_cfg["emit"] > 0.0:
                if "Emission Color" in bsdf.inputs:
                    nt.links.new(bsdf.inputs["Emission Color"], tex_node.outputs["Color"])
                elif "Emission" in bsdf.inputs:
                    nt.links.new(bsdf.inputs["Emission"], tex_node.outputs["Color"])
                if "Emission Strength" in bsdf.inputs:
                    bsdf.inputs["Emission Strength"].default_value = st_cfg["emit"]

            me.materials.append(mat)
            ob = bpy.data.objects.new(sname, me)
            if sname != "man_hand" and hasattr(ob, "visible_shadow"):
                ob.visible_shadow = False
            bpy.context.collection.objects.link(ob)

    def export_glb(surfs, fidx, out_paths):
        populate_blender_scene(surfs, fidx)
        primary = out_paths[0]
        bpy.ops.export_scene.gltf(filepath=primary, export_format="GLB", export_apply=True, export_yup=True)
        for extra in out_paths[1:]:
            shutil.copy2(primary, extra)
        print(f"  [GLB OK] {os.path.basename(primary):32s} ({os.path.getsize(primary) / 1024:.1f} KB)")

    # Frame 6 = Peak of Vision #0 (Mega Man Contraption glowing inside the floating rainbow Mystery Box!)
    export_glb(vm_surfs, 6, [
        os.path.join(GLB_DIR, "mystery_box_weapon.glb"),
        os.path.join(MOD_ROOT, "mystery_box_weapon.glb"),
    ])
    export_glb(proj_surfs, 3, [
        os.path.join(GLB_DIR, "mystery_box_projectile.glb"),
        os.path.join(MOD_ROOT, "mystery_box_projectile.glb"),
    ])
    export_glb(hero_surfs, 6, [
        os.path.join(GLB_DIR, "mystery_box_closeup.glb"),
    ])

    # Render 8-Panel EEVEE Inspection Contact Sheet!
    panels = [
        ("01_pov_idle_megaman",   vm_surfs,    6,  (0.0, 0.0, 0.0),      (16.8, -3.0, -3.2), 19.0, (960, 640)),
        ("02_pov_idle_wheelman",  vm_surfs,   18,  (0.0, 0.0, 0.0),      (16.8, -3.0, -3.2), 19.0, (960, 640)),
        ("03_pov_idle_suitrider", vm_surfs,   30,  (0.0, 0.0, 0.0),      (16.8, -3.0, -3.2), 19.0, (960, 640)),
        ("04_pov_fire_grab",      vm_surfs,  196,  (0.0, 0.0, 0.0),      (15.0, -3.4, -2.0), 19.5, (960, 640)),
        ("05_pov_fire_glow",      vm_surfs,  202,  (0.0, 0.0, 0.0),      (14.5, -3.5, -2.0), 19.5, (960, 640)),
        ("06_pov_fire_throw",     vm_surfs,  207,  (0.0, 0.0, 0.0),      (18.0, -2.8, -1.8), 19.5, (960, 640)),
        ("07_crystal_closeup_3d", hero_surfs, 30,  (34.0, -10.0, 6.0),   (0.0, 0.0, 0.0),    40.0, (720, 720)),
        ("08_proj_flight",        proj_surfs,  5,  (24.0, -28.0, 10.0),  (-4.0, 0.0, 0.0),   36.0, (720, 720)),
    ]

    eevee_id = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"

    for tag, surfs, fidx, cam_q, tgt_q, lens_mm, (rx, ry) in panels:
        populate_blender_scene(surfs, fidx)
        scene = bpy.context.scene
        scene.render.engine = eevee_id
        scene.render.resolution_x = rx
        scene.render.resolution_y = ry
        scene.world = bpy.data.worlds.new("World")
        scene.world.use_nodes = True
        bg = scene.world.node_tree.nodes.get("Background")
        bg.inputs["Color"].default_value = (0.048, 0.058, 0.098, 1.0)
        bg.inputs["Strength"].default_value = 1.15

        # Directional SUN studio lighting (no inverse-square falloff!) so realistic warm skin & glossy glass look natural!
        for nm, from_q, to_q, col_l, eng in (
            ("SunKey",   (4.0,  -15.0, 16.0), (16.0, -4.0, -4.0), (1.00, 0.95, 0.89), 3.1),
            ("SunFront", (0.0,   -4.0,  1.5), (16.0, -4.5, -6.5), (1.00, 0.93, 0.88), 1.45),
            ("SunRim",   (28.0,  14.0, 12.0), (16.0, -4.0, -2.0), (0.70, 0.86, 1.00), 1.15),
        ):
            ld = bpy.data.lights.new(nm, type="SUN")
            ld.color = col_l
            ld.energy = eng
            lo = bpy.data.objects.new(nm, ld)
            p_from = mathutils.Vector((-from_q[1], from_q[0], from_q[2]))
            p_to = mathutils.Vector((-to_q[1], to_q[0], to_q[2]))
            lo.location = p_from
            lo.rotation_euler = (p_to - p_from).to_track_quat("-Z", "Y").to_euler()
            bpy.context.collection.objects.link(lo)

        cam_d = bpy.data.cameras.new("Cam")
        cam_d.lens = lens_mm
        cam_d.clip_start = 0.2
        cam_d.clip_end = 400.0
        cam_o = bpy.data.objects.new("Cam", cam_d)
        bpy.context.collection.objects.link(cam_o)
        scene.camera = cam_o

        c_pos = mathutils.Vector((-cam_q[1], cam_q[0], cam_q[2]))
        t_pos = mathutils.Vector((-tgt_q[1], tgt_q[0], tgt_q[2]))
        cam_o.location = c_pos
        cam_o.rotation_euler = (t_pos - c_pos).to_track_quat("-Z", "Y").to_euler()

        scene.render.filepath = os.path.join(PREV_DIR, f"{tag}.png")
        bpy.ops.render.render(write_still=True)

    print("ALL MYSTERY BOX 3D MODELS, SHADERS, GLBS & RENDERS BUILT SUCCESSFULLY!")


if __name__ == "__main__":
    build_all_models()
