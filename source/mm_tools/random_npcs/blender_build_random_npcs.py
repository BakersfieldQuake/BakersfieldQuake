r"""Headless Blender 5.2 Sculpted + Rigged 3D Humanoid Builder & 50-Frame MD3 / GLB Exporter
for the 4 BakersfieldQuake "Random People" NPCs:

  1. progs/npc_randguy.md3   — Random Guy with 6 Random Comedy Shirts (_0.._5.skin) & 64oz Mega Gulp
  2. progs/npc_afroguy.md3   — Black Guy with Volumetric 70s Afro, Afro Pick & Chrome Boombox
  3. progs/npc_randlady.md3  — Neighborhood Lady with High Bun, Sunglasses, 3 Tops (_0.._2.skin) & Purse
  4. progs/npc_fatguy.md3    — Really Big Fat Guy with Stretched Shirt, Bare Jiggling Belly & XXL Burrito

Scale & Coordinate Space (100% matched to Quake `player.mdl` & `VEC_HULL_MIN/MAX`):
  - Forward = +X, Left = +Y, Up = +Z
  - Soles of shoes at Z = -24.0, standing skull crown at Z = +29.5..+30.5 (~54 Quake units tall, identical to player.mdl!)
  - Hull: '-16 -16 -24' to '16 16 32'

50-Frame Shared Animation Schedule:
  -  0..7  (idle1..idle8,    8f) : Breathing, weight shift, look-around & subtle character quirk
  -  8..19 (walk1..walk12,  12f) : Full 2-step realistic walk gait w/ character swagger/waddle
  - 20..29 (run1..run10,    10f) : Energetic comedic sprint / panic run
  - 30..39 (funny1..funny10,10f) : Signature funny emote (Spill Shrug / Disco Point / Purse Scold / Belly Slap)
  - 40..43 (pain1..pain4,    4f) : Startled jump-flinch reaction
  - 44..49 (death1..death6,  6f) : Dramatic comedic collapse to floor (Z ~ -22)

Usage:
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P source/mm_tools/random_npcs/blender_build_random_npcs.py
"""
from __future__ import annotations

import math
import os
import shutil
import sys
from typing import Dict, List, Tuple

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
OUT_ROOT = os.path.join(MM_TOOLS, "out", "random_npcs")
SRGB_DIR = os.path.join(OUT_ROOT, "tex_srgb")
PREVIEW_DIR = os.path.join(OUT_ROOT, "previews")
PROGS_DIR = os.path.join(MOD_ROOT, "progs")
SCRIPTS_DIR = os.path.join(MOD_ROOT, "scripts")

for p in (HERE, MM_TOOLS):
    if p not in sys.path:
        sys.path.insert(0, p)

import md3lib

os.makedirs(PREVIEW_DIR, exist_ok=True)
os.makedirs(PROGS_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)

SOLE_Z = -24.0
TAU = 2.0 * math.pi


def smooth01(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def uv_bl(u: float, t_top: float) -> Tuple[float, float]:
    """Converts (u, t_from_top) into Blender/glTF bottom-left UV (u, 1 - t)."""
    return (float(u), float(1.0 - t_top))


# ==============================================================================
# 1. PARAMETRIC ANATOMICAL LOFTING & SCULPTED HEAD HELPERS (WITH BONE WEIGHTS)
# ==============================================================================

class WeightedMeshBuilder:
    """Builds clean, smooth, UV-mapped anatomical meshes with explicit smooth bone weights."""

    def __init__(self, name: str):
        self.name = name
        self.verts: List[Tuple[float, float, float]] = []
        self.faces: List[Tuple[int, ...]] = []
        self.face_uvs: List[List[Tuple[float, float]]] = []
        self.weights: List[Dict[str, float]] = []

    def add_vert(self, co: Tuple[float, float, float], w: Dict[str, float]) -> int:
        idx = len(self.verts)
        self.verts.append((float(co[0]), float(co[1]), float(co[2])))
        tot = sum(w.values()) or 1.0
        self.weights.append({k: v / tot for k, v in w.items() if v > 1e-4})
        return idx

    def add_quad(
        self,
        i0: int, i1: int, i2: int, i3: int,
        uv0: Tuple[float, float], uv1: Tuple[float, float], uv2: Tuple[float, float], uv3: Tuple[float, float],
    ) -> None:
        self.faces.append((i0, i1, i2, i3))
        self.face_uvs.append([uv0, uv1, uv2, uv3])

    def add_tri(
        self,
        i0: int, i1: int, i2: int,
        uv0: Tuple[float, float], uv1: Tuple[float, float], uv2: Tuple[float, float],
    ) -> None:
        self.faces.append((i0, i1, i2))
        self.face_uvs.append([uv0, uv1, uv2])

    def to_blender_object(self, sc: bpy.types.Scene, mat: bpy.types.Material) -> bpy.types.Object:
        me = bpy.data.meshes.new(self.name + "_Mesh")
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")
        dvert_layer = bm.verts.layers.deform.new()

        # Collect all bone group names in deterministic order
        bone_names: List[str] = []
        bone_idx: Dict[str, int] = {}
        for wd in self.weights:
            for bn in wd:
                if bn not in bone_idx:
                    bone_idx[bn] = len(bone_names)
                    bone_names.append(bn)

        bm_verts = []
        for co, wd in zip(self.verts, self.weights):
            bv = bm.verts.new(co)
            dv = bv[dvert_layer]
            for bn, wval in wd.items():
                dv[bone_idx[bn]] = float(wval)
            bm_verts.append(bv)
        bm.verts.ensure_lookup_table()

        for f_idx, uvs in zip(self.faces, self.face_uvs):
            try:
                bf = bm.faces.new([bm_verts[i] for i in f_idx])
                bf.smooth = True
                for lp, uv in zip(bf.loops, uvs):
                    lp[uv_layer].uv = uv_bl(uv[0], uv[1])
            except ValueError:
                pass

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()

        obj = bpy.data.objects.new(self.name, me)
        sc.collection.objects.link(obj)
        for bn in bone_names:
            obj.vertex_groups.new(name=bn)
        obj.data.materials.append(mat)
        return obj


def blend_weights(w_a: Dict[str, float], w_b: Dict[str, float], t: float) -> Dict[str, float]:
    s = smooth01(t)
    out: Dict[str, float] = {}
    for k, v in w_a.items():
        out[k] = out.get(k, 0.0) + v * (1.0 - s)
    for k, v in w_b.items():
        out[k] = out.get(k, 0.0) + v * s
    return out


def add_lofted_tube(
    mb: WeightedMeshBuilder,
    stations: List[Tuple[Vector, Vector, Vector, float, float, Dict[str, float], float]],
    n_seg: int,
    uv_fn,
    cap_start: bool = False,
    cap_end: bool = False,
) -> None:
    """Lofts a smooth anatomical tube through `stations`:
    Each station = (center, axis_u_fwd, axis_v_left, r_u, r_v, weights, v_param).
    `uv_fn(theta_0_to_2pi, theta_signed, v_param, station_idx)` -> `(u, t_top)`.
    Note: creates seam-safe duplicate UV loop per quad so `u` never wraps backwards across 1->0!
    """
    rings: List[List[int]] = []
    for si, (ctr, ax_u, ax_v, ru, rv, w_dict, _) in enumerate(stations):
        ring: List[int] = []
        for k in range(n_seg):
            th = -math.pi + TAU * (k / n_seg)  # -pi .. +pi
            p = ctr + ax_u * (ru * math.cos(th)) + ax_v * (rv * math.sin(th))
            ring.append(mb.add_vert((p.x, p.y, p.z), w_dict))
        rings.append(ring)

    for si in range(len(stations) - 1):
        vp0 = stations[si][6]
        vp1 = stations[si + 1][6]
        r0, r1 = rings[si], rings[si + 1]
        for k in range(n_seg):
            kn = (k + 1) % n_seg
            th0 = -math.pi + TAU * (k / n_seg)
            th1 = -math.pi + TAU * ((k + 1) / n_seg)  # Unwrapped at +pi for seam-free UVs!
            f0 = k / n_seg
            f1 = (k + 1) / n_seg
            mb.add_quad(
                r0[k], r0[kn], r1[kn], r1[k],
                uv_fn(f0, th0, vp0, si),
                uv_fn(f1, th1, vp0, si),
                uv_fn(f1, th1, vp1, si + 1),
                uv_fn(f0, th0, vp1, si + 1),
            )

    if cap_start:
        ctr0, _, _, _, _, w0, vp0 = stations[0]
        c_idx = mb.add_vert((ctr0.x, ctr0.y, ctr0.z), w0)
        uv_c = uv_fn(0.5, 0.0, vp0, 0)
        r0 = rings[0]
        for k in range(n_seg):
            kn = (k + 1) % n_seg
            th0 = -math.pi + TAU * (k / n_seg)
            th1 = -math.pi + TAU * ((k + 1) / n_seg)
            mb.add_tri(c_idx, r0[kn], r0[k], uv_c, uv_fn((k + 1) / n_seg, th1, vp0, 0), uv_fn(k / n_seg, th0, vp0, 0))

    if cap_end:
        ctr1, _, _, _, _, w1, vp1 = stations[-1]
        c_idx = mb.add_vert((ctr1.x, ctr1.y, ctr1.z), w1)
        uv_c = uv_fn(0.5, 0.0, vp1, len(stations) - 1)
        r1 = rings[-1]
        for k in range(n_seg):
            kn = (k + 1) % n_seg
            th0 = -math.pi + TAU * (k / n_seg)
            th1 = -math.pi + TAU * ((k + 1) / n_seg)
            mb.add_tri(r1[k], r1[kn], c_idx, uv_fn(k / n_seg, th0, vp1, len(stations) - 1), uv_fn((k + 1) / n_seg, th1, vp1, len(stations) - 1), uv_c)


def add_uv_ellipsoid(
    mb: WeightedMeshBuilder,
    center: Vector,
    rx: float, ry: float, rz: float,
    w_dict: Dict[str, float],
    uv_rect: Tuple[float, float, float, float],
    u_seg: int = 20, v_seg: int = 14,
    lobe_amp: float = 0.0,
    rot_euler: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    """Adds a smooth UV-mapped ellipsoid (with optional curly Afro bumpy lobes!) mapped into `uv_rect=(u0,t0,u1,t1)`."""
    u0, t0, u1, t1 = uv_rect
    rot_m = Euler(rot_euler, "XYZ").to_matrix()
    grid: List[List[int]] = []
    for iv in range(v_seg + 1):
        vf = iv / v_seg
        phi = math.pi * vf  # 0 (top +Z) -> pi (bottom -Z)
        sp, cp = math.sin(phi), math.cos(phi)
        row: List[int] = []
        for iu in range(u_seg + 1):
            uf = iu / u_seg
            th = -math.pi + TAU * uf
            bump = 1.0
            if lobe_amp > 0.0:
                bump += lobe_amp * (
                    0.55 * math.sin(7.0 * th) * math.sin(6.0 * phi)
                    + 0.45 * math.cos(11.0 * th + 1.3) * math.sin(9.0 * phi)
                )
            local = Vector((rx * sp * math.cos(th) * bump, ry * sp * math.sin(th) * bump, rz * cp * bump))
            p = center + (rot_m @ local)
            row.append(mb.add_vert((p.x, p.y, p.z), w_dict))
        grid.append(row)

    for iv in range(v_seg):
        vf0, vf1 = iv / v_seg, (iv + 1) / v_seg
        for iu in range(u_seg):
            uf0, uf1 = iu / u_seg, (iu + 1) / u_seg
            mb.add_quad(
                grid[iv][iu], grid[iv + 1][iu], grid[iv + 1][iu + 1], grid[iv][iu + 1],
                (u0 + (u1 - u0) * uf0, t0 + (t1 - t0) * vf0),
                (u0 + (u1 - u0) * uf0, t0 + (t1 - t0) * vf1),
                (u0 + (u1 - u0) * uf1, t0 + (t1 - t0) * vf1),
                (u0 + (u1 - u0) * uf1, t0 + (t1 - t0) * vf0),
            )


def add_round_box(
    mb: WeightedMeshBuilder,
    center: Vector,
    hx: float, hy: float, hz: float,
    w_dict: Dict[str, float],
    uv_rect: Tuple[float, float, float, float],
    rot_euler: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    side_uv: Tuple[float, float, float, float] | None = None,
    front_faces: Tuple[int, ...] = (0, 1),
) -> None:
    """Adds a clean 3D box prop (boombox, purse, phone, holster, pick) with `uv_rect` on `front_faces`
    and `side_uv` (defaults to `uv_rect`) on edge/top/bottom faces."""
    u0, t0, u1, t1 = uv_rect
    su0, st0, su1, st1 = side_uv if side_uv is not None else uv_rect
    rot_m = Euler(rot_euler, "XYZ").to_matrix()
    corners = [
        Vector((-hx, -hy, -hz)), Vector((+hx, -hy, -hz)), Vector((+hx, +hy, -hz)), Vector((-hx, +hy, -hz)),
        Vector((-hx, -hy, +hz)), Vector((+hx, -hy, +hz)), Vector((+hx, +hy, +hz)), Vector((-hx, +hy, +hz)),
    ]
    w_pts = [center + (rot_m @ c) for c in corners]
    v_ids = [mb.add_vert((p.x, p.y, p.z), w_dict) for p in w_pts]
    quads = [
        (4, 5, 1, 0),  # 0: -Y face
        (6, 7, 3, 2),  # 1: +Y face
        (5, 6, 2, 1),  # 2: +X face
        (7, 4, 0, 3),  # 3: -X face
        (7, 6, 5, 4),  # 4: +Z top face
        (0, 1, 2, 3),  # 5: -Z bottom face
    ]
    for qi, (a, b, c, d) in enumerate(quads):
        if qi in front_faces:
            mb.add_quad(v_ids[a], v_ids[b], v_ids[c], v_ids[d], (u0, t0), (u1, t0), (u1, t1), (u0, t1))
        else:
            mb.add_quad(v_ids[a], v_ids[b], v_ids[c], v_ids[d], (su0, st0), (su1, st0), (su1, st1), (su0, st1))


# ==============================================================================
# 2. SCULPTED REALISTIC 3D HUMAN HEAD + VOLUMETRIC HAIR / AFRO / BUN / GLASSES
# ==============================================================================

def build_sculpted_head_surface(
    key: str,
    z_neck_base: float,
    z_chin: float,
    z_crown: float,
    rx_skull: float,
    ry_skull: float,
    double_chin: float = 0.0,
) -> WeightedMeshBuilder:
    """Sculpts a continuous, realistic anatomical human skull + jaw + chin + neck + ears + nose,
    with cylindrical-spherical UVs matched 1:1 to `make_npc_textures.py` (`t in [0.006..0.852]`)."""
    mb = WeightedMeshBuilder(f"head_{key}")
    n_u = 48
    n_v = 36

    z_head_mid = 0.5 * (z_chin + z_crown)
    rz_skull = 0.5 * (z_crown - z_chin)

    rings: List[List[int]] = []
    ring_tg: List[float] = []

    for iv in range(n_v + 1):
        tg = iv / n_v  # 0.0 = crown, 0.42 = eyes, 0.78 = chin/jawline, 1.0 = collar base
        ring_tg.append(tg)
        row: List[int] = []

        # Smooth blend from Head bone (above jawline) into Neck and Chest (tucked inside collar)
        w_neck = smooth01((tg - 0.72) / 0.22)
        w_chest = smooth01((tg - 0.86) / 0.14) * 0.65
        w_dict = {
            "Head": max(0.0, 1.0 - w_neck),
            "Neck": max(0.0, w_neck - w_chest),
            "Chest": w_chest,
        }

        # Continuous vertical height z(tg): round cranial dome -> face -> chin -> collar base
        if tg <= 0.78:
            s_h = tg / 0.78
            # Smooth hemispherical dome at top (s_h < 0.5), nearly linear through lower face to z_chin
            phi_z = (0.04 + 0.90 * s_h) * math.pi
            z_sphere = z_head_mid + rz_skull * math.cos(phi_z)
            z_lin = z_crown * (1.0 - s_h) + z_chin * s_h
            z_base = z_sphere * (1.0 - 0.45 * s_h) + z_lin * (0.45 * s_h)
        else:
            s_n = (tg - 0.78) / 0.22
            z_base = z_chin * (1.0 - s_n) + z_neck_base * s_n

        # Continuous anatomical cross-section radii (dome -> full temples/cheeks -> rounded jaw -> smooth neck)
        if tg < 0.36:
            dome_r = math.sin((0.06 + 0.44 * (tg / 0.36)) * math.pi)
        else:
            dome_r = 1.0

        # Jawline & neck transition: crisp human jawline stepping smoothly into a natural-width neck!
        jaw_u = smooth01((tg - 0.52) / 0.25)     # 0 at cheekbones -> 1 at chin/submental
        neck_u = smooth01((tg - 0.77) / 0.11)    # 0 at jawline -> 1 in neck shaft
        collar_flare = smooth01((tg - 0.89) / 0.11) * 0.09

        ry_neck_frac = 0.45 + 0.27 * min(1.0, double_chin)
        rx_neck_frac = 0.46 + 0.25 * min(1.0, double_chin)

        ry_cur = ry_skull * dome_r * (
            (1.0 - (0.22 if double_chin < 0.1 else 0.05) * jaw_u) * (1.0 - neck_u)
            + (ry_neck_frac + collar_flare) * neck_u
        )

        for iu in range(n_u):
            th = -math.pi + TAU * (iu / n_u)  # 0 = +X nose, +pi/2 = +Y left ear, -pi/2 = -Y right ear
            ct, st = math.cos(th), math.sin(th)

            # Front jaw stays proud down to chin (tg~0.76), then tucks smoothly under chin into throat;
            # Back occiput rounds smoothly inward into nape from tg=0.52..0.80.
            if ct >= 0.0:
                rx_head_frac = 1.0 - 0.08 * jaw_u
            else:
                occ_u = smooth01((tg - 0.50) / 0.28)
                rx_head_frac = 1.0 - 0.34 * occ_u

            rx_cur = rx_skull * dome_r * (
                rx_head_frac * (1.0 - neck_u) + (rx_neck_frac + collar_flare) * neck_u
            )

            # Slight forward/backward center shift for natural neck posture & double-chin fullness
            cx_cur = (-0.25 + 0.45 * double_chin) * neck_u * (1.0 - 0.5 * collar_flare)

            x = cx_cur + rx_cur * ct
            y = ry_cur * st
            z = z_base

            # Built-in natural 3D hair volume on skull crown/temples/nape (replaces floating mushroom cap!)
            if key in ("randguy", "fatguy") and tg < 0.56:
                front_open = math.exp(-((th / 1.08) ** 2))
                hline = (0.54 if key == "randguy" else 0.48) * (1.0 - 0.68 * front_open)
                hair_v = smooth01((hline - tg) / 0.08)
                quiff = math.exp(-(((tg - 0.09) / 0.075) ** 2)) * math.exp(-((th / 0.85) ** 2))
                h_push = (0.42 if key == "randguy" else 0.30) * hair_v + (0.65 if key == "randguy" else 0.40) * quiff
                x += h_push * ct * 0.85
                y += h_push * st * 0.90
                z += h_push * max(0.0, 1.0 - tg * 2.2)

            # Anatomical 3D facial relief on front hemisphere (above neck)
            face_mask = (1.0 - neck_u) * (smooth01((ct - 0.05) / 0.45) if ct > 0.05 else 0.0)
            if face_mask > 0.001:
                # 3D nose bridge & tip around tg ~ 0.42..0.55
                nose_v = math.exp(-(((tg - 0.49) / 0.080) ** 2))
                nose_u = math.exp(-((st / 0.145) ** 2))
                x += 1.32 * nose_v * nose_u * face_mask
                # Nostril alar wings
                alar = math.exp(-(((abs(st) - 0.13) / 0.065) ** 2 + ((tg - 0.535) / 0.035) ** 2))
                x += 0.36 * alar * face_mask
                # Brow ridge & subtle eye sockets (tg ~ 0.36..0.44)
                brow = math.exp(-(((tg - 0.36) / 0.038) ** 2 + ((st / 0.48) ** 4)))
                socket = math.exp(-(((abs(st) - 0.27) / 0.12) ** 2 + ((tg - 0.42) / 0.042) ** 2))
                x += (0.42 * brow - 0.28 * socket) * face_mask
                # Rounded cheekbones & natural human chin prominence
                cheek = math.exp(-(((abs(st) - 0.44) / 0.20) ** 2 + ((tg - 0.52) / 0.09) ** 2))
                chin_b = math.exp(-(((st / 0.32) ** 2) + ((tg - 0.73) / 0.065) ** 2))
                x += (0.38 * cheek + 0.55 * chin_b) * face_mask
                y += math.copysign(0.26 * cheek * face_mask, st)

            # Subtle, realistic 3D Ears at |th| ~ pi/2, tg ~ 0.43..0.55 (no diamond spikes!)
            ear_w = (1.0 - neck_u) * math.exp(-(((abs(th) - 1.52) / 0.14) ** 2 + ((tg - 0.485) / 0.068) ** 2))
            y += math.copysign(0.46 * ear_w, st)
            x -= 0.12 * ear_w

            # Jolly double-chin & wide round jowls on Fat Guy!
            if double_chin > 0.0 and tg < 0.88:
                jowl = smooth01((tg - 0.50) / 0.24) * (1.0 - smooth01((tg - 0.80) / 0.09)) * max(0.0, ct + 0.25)
                x += double_chin * 0.85 * jowl
                y += math.copysign(double_chin * 0.55 * jowl * abs(st), st)

            row.append(mb.add_vert((x, y, z), w_dict))
        rings.append(row)

    # Connect rings with cylindrical UVs mapped into rows [0..880] -> t_top in [0.005 .. 0.852]
    for iv in range(n_v):
        t0 = 0.006 + ring_tg[iv] * 0.846
        t1 = 0.006 + ring_tg[iv + 1] * 0.846
        r0, r1 = rings[iv], rings[iv + 1]
        for iu in range(n_u):
            iun = (iu + 1) % n_u
            u0 = iu / n_u
            u1 = (iu + 1) / n_u
            mb.add_quad(r0[iu], r0[iun], r1[iun], r1[iu], (u0, t0), (u1, t0), (u1, t1), (u0, t1))

    # Cap crown apex cleanly
    c_top = mb.add_vert((0.0, 0.0, z_crown + (0.35 if key == "randguy" else 0.15)), {"Head": 1.0})
    for iu in range(n_u):
        iun = (iu + 1) % n_u
        mb.add_tri(c_top, rings[0][iun], rings[0][iu], (0.5, 0.004), ((iu + 1) / n_u, 0.006), (iu / n_u, 0.006))

    # Character-specific 3D Afro / High Bun / Head-Accessories!
    HAIR_UV = (0.03, 0.89, 0.47, 0.99)
    GOLD_UV = (0.53, 0.89, 0.73, 0.99)
    DARK_UV = (0.78, 0.89, 0.98, 0.99)

    if key == "afroguy":
        # MAGNIFICENT 3D Coiled Spherical 70s Afro Halo framing his face WITHOUT covering his eyes/brow/grin!
        afro_c = Vector((-1.85, 0.0, z_head_mid + 4.55))
        afro_rx, afro_ry, afro_rz = 7.45, 8.35, 6.85
        u_seg, v_seg = 30, 22
        u0, t0, u1, t1 = HAIR_UV
        afro_grid: List[List[int]] = []
        for iv in range(v_seg + 1):
            vf = iv / v_seg
            phi = math.pi * vf
            sp, cp = math.sin(phi), math.cos(phi)
            row_a: List[int] = []
            for iu in range(u_seg + 1):
                uf = iu / u_seg
                th = -math.pi + TAU * uf
                bump = 1.0 + 0.055 * (
                    0.55 * math.sin(7.0 * th) * math.sin(6.0 * phi)
                    + 0.45 * math.cos(11.0 * th + 1.3) * math.sin(9.0 * phi)
                )
                p = afro_c + Vector((afro_rx * sp * math.cos(th) * bump, afro_ry * sp * math.sin(th) * bump, afro_rz * cp * bump))
                # Carve clean open facial arch in front of forehead/temples so eyes, brow & shades stay 100% visible!
                if p.x > 0.8 and p.z < z_crown - 1.35:
                    recess_z = smooth01(((z_crown - 1.35) - p.z) / 2.2)
                    recess_y = smooth01((5.8 - abs(p.y)) / 2.2)
                    pull = recess_z * recess_y
                    p.x = p.x * (1.0 - pull) + 0.65 * pull
                    p.z = p.z + 1.45 * pull
                row_a.append(mb.add_vert((p.x, p.y, p.z), {"Afro": 0.88, "Head": 0.12}))
            afro_grid.append(row_a)
        for iv in range(v_seg):
            vf0, vf1 = iv / v_seg, (iv + 1) / v_seg
            for iu in range(u_seg):
                uf0, uf1 = iu / u_seg, (iu + 1) / u_seg
                mb.add_quad(
                    afro_grid[iv][iu], afro_grid[iv + 1][iu], afro_grid[iv + 1][iu + 1], afro_grid[iv][iu + 1],
                    (u0 + (u1 - u0) * uf0, t0 + (t1 - t0) * vf0),
                    (u0 + (u1 - u0) * uf0, t0 + (t1 - t0) * vf1),
                    (u0 + (u1 - u0) * uf1, t0 + (t1 - t0) * vf1),
                    (u0 + (u1 - u0) * uf1, t0 + (t1 - t0) * vf0),
                )
        # Jaunty 3D Gold Afro Pick stuck visibly into the upper-left side of his Afro!
        add_round_box(
            mb, Vector((+0.4, 7.35, z_head_mid + 6.5)), 0.22, 2.25, 1.05,
            {"Afro": 0.95, "Head": 0.05}, GOLD_UV,
            rot_euler=(math.radians(-30.0), 0.0, math.radians(-10.0)),
        )
        # Retro tinted gold-wire shades resting coolly on his upper brow hairline!
        for sy in (-1.0, +1.0):
            add_round_box(mb, Vector((rx_skull * 0.92, sy * 1.62, z_crown - 2.25)), 0.24, 1.18, 0.54, {"Head": 1.0}, DARK_UV, rot_euler=(0.0, math.radians(-16.0), sy * math.radians(-8.0)))
        add_round_box(mb, Vector((rx_skull * 0.98, 0.0, z_crown - 2.15)), 0.16, 0.75, 0.12, {"Head": 1.0}, GOLD_UV)

    elif key == "lady":
        # Sculpted 3D High Messy Bun on crown + Gold Hoop Earrings + Sleek Sunglasses perched on head!
        add_uv_ellipsoid(mb, Vector((-0.7, 0.0, z_crown + 1.35)), 2.75, 2.95, 2.15, {"Head": 1.0}, HAIR_UV, 18, 12, lobe_amp=0.05)
        for sy in (-1.0, +1.0):
            # Gold hoop earrings at earlobes
            add_uv_ellipsoid(mb, Vector((-0.15, sy * (ry_skull + 0.35), z_head_mid - 1.05)), 0.60, 0.16, 0.70, {"Head": 1.0}, GOLD_UV, 12, 8)
            # Sleek oversized sunglasses perched on top of her head!
            add_round_box(mb, Vector((rx_skull * 0.68, sy * 1.68, z_crown - 1.15)), 0.26, 1.28, 0.56, {"Head": 1.0}, DARK_UV, rot_euler=(0.0, math.radians(-28.0), sy * math.radians(-6.0)))
        add_round_box(mb, Vector((rx_skull * 0.76, 0.0, z_crown - 1.05)), 0.16, 0.65, 0.12, {"Head": 1.0}, GOLD_UV)

    return mb


# ==============================================================================
# 3. ANATOMICAL BODY + CLOTHES + SHOES + FUNNY 3D PROPS BUILDER
# ==============================================================================

CHAR_CONFIGS: Dict[str, Dict] = {
    "randguy": dict(
        md3_name="npc_randguy",
        skins=6,
        z_crown=30.2, z_chin=19.2, z_neck=17.2, z_sh=15.6, z_chest=8.5, z_waist=2.2, z_hip=-1.8, z_knee=-13.2, z_ank=-21.8,
        rx_skull=4.45, ry_skull=4.15, double_chin=0.0,
        torso_rx=(4.5, 4.7, 5.1, 4.9),   # hip, waist, chest, shoulder_chest
        torso_ry=(6.4, 6.1, 7.2, 8.2),
        belly_fwd=0.55,
        sh_y=8.9, el_y=9.8, wr_y=10.3,   # Slight relaxed A-pose
        arm_r=(2.05, 1.65, 1.48, 1.12),  # shoulder, elbow, forearm, wrist
        hip_y=3.65, thigh_r=3.15, knee_r=2.15, calf_r=2.20, ank_r=1.45,
        pants_end_s=0.92,                # Cargo shorts end right around the knee!
        has_crew_socks=True,
    ),
    "afroguy": dict(
        md3_name="npc_afroguy",
        skins=1,
        z_crown=29.8, z_chin=19.0, z_neck=17.0, z_sh=15.5, z_chest=8.6, z_waist=2.5, z_hip=-1.6, z_knee=-13.0, z_ank=-21.8,
        rx_skull=4.35, ry_skull=4.00, double_chin=0.0,
        torso_rx=(4.2, 4.1, 5.0, 4.8),
        torso_ry=(6.0, 5.7, 7.3, 8.4),
        belly_fwd=0.15,
        sh_y=9.0, el_y=9.9, wr_y=10.4,
        arm_r=(2.10, 1.68, 1.50, 1.12),
        hip_y=3.55, thigh_r=3.05, knee_r=2.10, calf_r=2.25, ank_r=2.45,  # Flared 70s jeans cuff!
        pants_end_s=1.88,                # Full-length flared jeans down to high-tops!
        has_crew_socks=False,
    ),
    "lady": dict(
        md3_name="npc_randlady",
        skins=3,
        z_crown=28.8, z_chin=18.4, z_neck=16.4, z_sh=14.8, z_chest=8.2, z_waist=2.8, z_hip=-1.6, z_knee=-13.0, z_ank=-21.9,
        rx_skull=4.15, ry_skull=3.90, double_chin=0.0,
        torso_rx=(4.7, 3.8, 5.1, 4.2),   # Feminine hips, tapered waist, natural bust contour!
        torso_ry=(6.8, 5.2, 6.4, 7.1),
        belly_fwd=0.0,
        bust_fwd=1.45,
        sh_y=7.6, el_y=8.5, wr_y=9.1,
        arm_r=(1.72, 1.38, 1.25, 0.96),
        hip_y=3.55, thigh_r=3.05, knee_r=1.92, calf_r=1.95, ank_r=1.25,
        pants_end_s=1.55,                # Mid-calf yoga capris!
        has_crew_socks=False,
    ),
    "fatguy": dict(
        md3_name="npc_fatguy",
        skins=1,
        z_crown=30.0, z_chin=18.8, z_neck=16.8, z_sh=15.4, z_chest=8.2, z_waist=1.2, z_hip=-2.4, z_knee=-13.2, z_ank=-21.8,
        rx_skull=5.15, ry_skull=5.05, double_chin=1.35,
        # REALLY BIG FAT GUY: Same height as player (~54u), gloriously huge round overhanging gut & wide love-handles!
        torso_rx=(8.4, 11.4, 9.2, 6.8),
        torso_ry=(10.2, 12.2, 10.8, 9.8),
        belly_fwd=4.65,                  # Big spherical overhanging belly!
        sh_y=11.0, el_y=12.8, wr_y=13.8,
        arm_r=(3.05, 2.45, 2.10, 1.42),
        hip_y=4.85, thigh_r=4.55, knee_r=2.95, calf_r=2.85, ank_r=1.82,
        pants_end_s=0.95,                # Denim jorts!
        has_crew_socks=True,
    ),
}


def build_body_surface_and_rig(sc: bpy.types.Scene, key: str, mat_head: bpy.types.Material, mat_body: bpy.types.Material):
    cfg = CHAR_CONFIGS[key]
    mb = WeightedMeshBuilder(f"body_{key}")

    z_hip = cfg["z_hip"]
    z_waist = cfg["z_waist"]
    z_chest = cfg["z_chest"]
    z_sh = cfg["z_sh"]
    z_neck = cfg["z_neck"]
    z_knee = cfg["z_knee"]
    z_ank = cfg["z_ank"]

    # ------------------------------------------------------------------
    # A. Unified Torso + Pelvis Loft (Hip base -> Pelvis -> Waist/Gut -> Chest -> Shoulders -> Collar)
    # ------------------------------------------------------------------
    rx_h, rx_w, rx_c, rx_s = cfg["torso_rx"]
    ry_h, ry_w, ry_c, ry_s = cfg["torso_ry"]
    bfwd = cfg["belly_fwd"]
    bust = cfg.get("bust_fwd", 0.0)
    is_fat = key == "fatguy"

    # Pelvis / Belt / Shorts-Top Loft (Q1 Pants UV) + Overlapping Shirt / Belly Loft (Q0 Shirt UV)
    # Kept as two clean overlapping lofts so shirt hem overhangs waistband with zero cross-atlas UV stretch!
    pelvis_profile = [
        (z_hip - 2.4, -0.2,              rx_h * 0.80, ry_h * 0.82, 0.22, {"Pelvis": 0.90, "Thigh.L": 0.05, "Thigh.R": 0.05}),
        (z_hip,       -0.1,              rx_h * 0.98, ry_h * 0.98, 0.10, {"Pelvis": 1.00}),
        (z_hip + 2.5, +0.18 * bfwd,      rx_h * 0.96, ry_h * 0.96, 0.01, {"Pelvis": 0.78, "Spine": 0.22}),
    ]
    pelvis_stations = [(Vector((xc, 0.0, z)), Vector((1, 0, 0)), Vector((0, 1, 0)), rx, ry, wd, vp) for z, xc, rx, ry, vp, wd in pelvis_profile]
    add_lofted_tube(
        mb, pelvis_stations, n_seg=28,
        uv_fn=lambda uf, _th, vp, _si: (0.53 + 0.44 * uf, 0.012 + vp * 0.42),
        cap_start=True, cap_end=True,
    )

    shirt_profile = [
        (z_hip + 2.0, +0.38 * bfwd,               rx_w * 0.99, ry_w * 0.99, 0.96, {"Pelvis": 0.45, "Spine": 0.30, "Belly": 0.25 if is_fat else 0.0}),
        (z_waist,     +0.95 * bfwd,               rx_w * 1.04, ry_w * 1.02, 0.76, {"Spine": 0.45 if is_fat else 0.85, "Pelvis": 0.15, "Belly": 0.40 if is_fat else 0.0}),
        (z_waist + 3.2,+0.85 * bfwd,              rx_w * 1.00, ry_w * 0.99, 0.56, {"Spine": 0.55 if is_fat else 0.70, "Chest": 0.20, "Belly": 0.25 if is_fat else 0.0}),
        (z_chest,     +0.30 * bfwd + bust,        rx_c,        ry_c,        0.36, {"Chest": 0.82, "Spine": 0.18}),
        (z_chest + 3.8,+0.10 * bfwd + 0.4 * bust, rx_c * 0.97, ry_c * 1.03, 0.19, {"Chest": 0.95, "Spine": 0.05}),
        (z_sh,         0.0,                       rx_s * 0.92, ry_s * 0.96, 0.08, {"Chest": 0.92, "Neck": 0.08}),
        (z_neck + 0.35,-0.12,                     cfg["rx_skull"] * (0.72 if is_fat else 0.53), cfg["ry_skull"] * (0.74 if is_fat else 0.54), 0.02, {"Chest": 0.60, "Neck": 0.40}),
    ]
    torso_stations = [(Vector((xc, 0.0, z)), Vector((1, 0, 0)), Vector((0, 1, 0)), rx, ry, wd, vp) for z, xc, rx, ry, vp, wd in shirt_profile]

    def torso_uv(_uf: float, th: float, vp: float, _si: int) -> Tuple[float, float]:
        t = 0.018 + vp * 0.468
        if abs(th) <= math.pi * 0.5:
            u = 0.125 + 0.116 * math.sin(th)
        else:
            ang_b = math.atan2(math.sin(th), -math.cos(th))
            u = 0.375 - 0.116 * math.sin(ang_b)
        return (u, t)

    add_lofted_tube(mb, torso_stations, n_seg=32, uv_fn=torso_uv, cap_start=False, cap_end=True)

    # ------------------------------------------------------------------
    # B. Left & Right Arms + Hands + Thumb/Fingers (Smooth Rounded Shoulders & Horizontal Cross-Sections!)
    # ------------------------------------------------------------------
    for side, sy in (("R", -1.0), ("L", +1.0)):
        sh_tuck = Vector((-0.05, sy * (ry_s * 0.72), z_sh - 0.25))
        sh_p = Vector((0.0, sy * (cfg["sh_y"] - 0.55), z_sh - 1.15))
        bicep_cuff = Vector((0.10, sy * (cfg["sh_y"] + 0.35), z_sh - 4.55))
        el_p = Vector((-0.30, sy * cfg["el_y"], z_sh - 9.4))
        wr_p = Vector((0.45, sy * cfg["wr_y"], z_sh - 17.2))
        palm_p = Vector((0.75, sy * (cfg["wr_y"] + 0.15), z_sh - 19.3))
        tip_p = Vector((0.95, sy * (cfg["wr_y"] + 0.10), z_sh - 21.8))

        r_sh, r_el, r_fa, r_wr = cfg["arm_r"]
        uarm_b = f"UpperArm.{side}"
        farm_b = f"Forearm.{side}"
        hand_b = f"Hand.{side}"

        # 1) Rounded Deltoid + Short Shirt Sleeve (mapped to clean upper-back Q0 fabric band t=0.048..0.112 — zero text!)
        ax_sh = Vector((0.0, 0.90, -0.42 * sy)).normalized()
        ax_lat = Vector((0.0, 0.98, -0.18 * sy)).normalized()
        sleeve_stations = [
            (sh_tuck, Vector((1, 0, 0)), ax_sh, r_sh * 1.12, r_sh * 1.05, {"Chest": 0.72, uarm_b: 0.28}, 0.048),
            (sh_p, Vector((1, 0, 0)), ax_lat, r_sh * 1.14, r_sh * 1.12, {"Chest": 0.38, uarm_b: 0.62}, 0.068),
            (sh_p.lerp(bicep_cuff, 0.58), Vector((1, 0, 0)), Vector((0, 1, 0)), r_sh * 1.08, r_sh * 1.06, {"Chest": 0.12, uarm_b: 0.88}, 0.090),
            (bicep_cuff, Vector((1, 0, 0)), Vector((0, 1, 0)), r_sh * 1.02, r_sh * 1.00, {uarm_b: 1.0}, 0.112),
        ]
        add_lofted_tube(
            mb, sleeve_stations, n_seg=16,
            uv_fn=lambda uf, _th, vp, _si: (0.29 + 0.16 * uf, vp),
            cap_start=True, cap_end=False,
        )

        # 2) Bare Arm + Forearm + Hand + Mitten-Sculpted Fingers mapped to Q2 Bare Skin!
        arm_stations = [
            (bicep_cuff + Vector((0, 0, 0.45)), Vector((1, 0, 0)), Vector((0, 1, 0)), r_sh * 0.90, r_sh * 0.88, {uarm_b: 1.0}, 0.54),
            (bicep_cuff.lerp(el_p, 0.60), Vector((1, 0, 0)), Vector((0, 1, 0)), r_el * 1.04, r_el * 1.00, {uarm_b: 0.90, farm_b: 0.10}, 0.64),
            (el_p, Vector((1, 0, 0)), Vector((0, 1, 0)), r_el, r_el * 0.96, {uarm_b: 0.45, farm_b: 0.55}, 0.72),
            (el_p.lerp(wr_p, 0.42), Vector((1, 0, 0)), Vector((0, 1, 0)), r_fa * 1.05, r_fa * 0.98, {farm_b: 1.0}, 0.80),
            (wr_p, Vector((1, 0, 0)), Vector((0, 1, 0)), r_wr, r_wr * 0.82, {farm_b: 0.45, hand_b: 0.55}, 0.88),
            (palm_p, Vector((1, 0, 0)), Vector((0, 1, 0)), r_wr * 1.28, r_wr * 0.62, {hand_b: 1.0}, 0.93),
            (tip_p, Vector((1, 0, 0)), Vector((0, 1, 0)), r_wr * 0.96, r_wr * 0.44, {hand_b: 1.0}, 0.97),
        ]
        add_lofted_tube(
            mb, arm_stations, n_seg=14,
            uv_fn=lambda uf, _th, vp, _si: (0.04 + 0.42 * uf, vp),
            cap_start=False, cap_end=True,
        )
        # Sculpted Thumb on front (+X) edge of palm
        add_uv_ellipsoid(
            mb, palm_p + Vector((r_wr * 1.15, -sy * 0.25, -0.15)),
            r_wr * 0.85, r_wr * 0.42, r_wr * 0.55,
            {hand_b: 1.0}, (0.12, 0.82, 0.28, 0.94), 8, 6,
            rot_euler=(0.0, math.radians(32.0), 0.0),
        )

    # ------------------------------------------------------------------
    # C. Left & Right Legs (Pants/Shorts -> Bare Knee/Calf -> Socks -> Contoured Sneakers!)
    # ------------------------------------------------------------------
    for side, sy in (("R", -1.0), ("L", +1.0)):
        hip_p = Vector((0.0, sy * cfg["hip_y"], z_hip + 0.6))
        mid_th = Vector((0.15, sy * (cfg["hip_y"] + 0.15), 0.5 * (z_hip + z_knee)))
        kn_p = Vector((0.20, sy * (cfg["hip_y"] + 0.20), z_knee))
        calf_p = Vector((-0.25, sy * (cfg["hip_y"] + 0.22), z_knee - 3.2))
        ank_p = Vector((-0.15, sy * (cfg["hip_y"] + 0.22), z_ank))

        th_b = f"Thigh.{side}"
        sh_b = f"Shin.{side}"
        ft_b = f"Foot.{side}"
        rt, rk, rc, ra = cfg["thigh_r"], cfg["knee_r"], cfg["calf_r"], cfg["ank_r"]
        p_end = cfg["pants_end_s"]  # 0..1 = thigh, 1..2 = shin

        # 1) Pants / Shorts / Jeans / Yoga Capris tube
        if p_end <= 1.05:
            # Shorts / Jorts ending at knee!
            cuff_p = hip_p.lerp(kn_p, p_end)
            pants_st = [
                (hip_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rt * 1.06, rt * 1.04, {"Pelvis": 0.35, th_b: 0.65}, 0.08),
                (mid_th, Vector((1, 0, 0)), Vector((0, 1, 0)), rt * 0.98, rt * 0.98, {th_b: 1.0}, 0.20),
                (cuff_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rk * 1.18, rk * 1.18, {th_b: 0.65, sh_b: 0.35}, 0.31),
            ]
        elif p_end <= 1.65:
            # Calf-length Capris (Random Lady)
            cuff_p = kn_p.lerp(ank_p, p_end - 1.0)
            pants_st = [
                (hip_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rt * 1.04, rt * 1.02, {"Pelvis": 0.35, th_b: 0.65}, 0.08),
                (mid_th, Vector((1, 0, 0)), Vector((0, 1, 0)), rt * 0.92, rt * 0.92, {th_b: 1.0}, 0.16),
                (kn_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rk * 1.02, rk * 1.00, {th_b: 0.45, sh_b: 0.55}, 0.23),
                (cuff_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rc * 0.98, rc * 0.98, {sh_b: 1.0}, 0.31),
            ]
        else:
            # Full-length flared 70s jeans (Afro Guy)
            pants_st = [
                (hip_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rt * 1.05, rt * 1.03, {"Pelvis": 0.35, th_b: 0.65}, 0.08),
                (mid_th, Vector((1, 0, 0)), Vector((0, 1, 0)), rt * 0.94, rt * 0.94, {th_b: 1.0}, 0.15),
                (kn_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rk * 1.02, rk * 1.00, {th_b: 0.45, sh_b: 0.55}, 0.22),
                (calf_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rc * 1.04, rc * 1.04, {sh_b: 1.0}, 0.27),
                (ank_p + Vector((0.3, 0, 0.3)), Vector((1, 0, 0)), Vector((0, 1, 0)), ra * 1.08, ra * 1.02, {sh_b: 0.70, ft_b: 0.30}, 0.32),
            ]

        add_lofted_tube(
            mb, pants_st, n_seg=16,
            uv_fn=lambda uf, _th, vp, _si: (0.53 + 0.44 * uf, vp),
            cap_start=True, cap_end=False,
        )

        # 2) Exposed Lower Leg + Crew Sock (when wearing shorts or capris)
        if p_end < 1.80:
            sock_top_z = z_ank + (3.6 if cfg["has_crew_socks"] else 0.9)
            sock_top = Vector((-0.20, sy * (cfg["hip_y"] + 0.22), sock_top_z))
            leg_start = cuff_p + Vector((0, 0, 0.4))
            skin_leg_st = [
                (leg_start, Vector((1, 0, 0)), Vector((0, 1, 0)), rk * 0.96, rk * 0.94, {th_b: 0.35 if p_end <= 1.05 else 0.0, sh_b: 0.65 if p_end <= 1.05 else 1.0}, 0.58),
            ]
            if p_end <= 1.05:
                skin_leg_st.append((calf_p, Vector((1, 0, 0)), Vector((0, 1, 0)), rc, rc * 0.96, {sh_b: 1.0}, 0.72))
            skin_leg_st.append((sock_top, Vector((1, 0, 0)), Vector((0, 1, 0)), ra * 1.12, ra * 1.08, {sh_b: 1.0}, 0.86))
            add_lofted_tube(
                mb, skin_leg_st, n_seg=14,
                uv_fn=lambda uf, _th, vp, _si: (0.04 + 0.42 * uf, vp),
                cap_start=False, cap_end=False,
            )

            # Sock cuff down to ankle
            sock_st = [
                (sock_top + Vector((0, 0, 0.15)), Vector((1, 0, 0)), Vector((0, 1, 0)), ra * 1.16, ra * 1.12, {sh_b: 0.90, ft_b: 0.10}, 0.345),
                (ank_p, Vector((1, 0, 0)), Vector((0, 1, 0)), ra * 1.06, ra * 1.04, {sh_b: 0.45, ft_b: 0.55}, 0.430),
            ]
            add_lofted_tube(
                mb, sock_st, n_seg=14,
                uv_fn=lambda uf, _th, vp, _si: (0.76 + 0.22 * uf, vp),
                cap_start=False, cap_end=False,
            )

        # 3) Contoured 3D Sneaker / Slide Shoe with flat sole resting right at SOLE_Z = -24.0!
        cy_f = sy * (cfg["hip_y"] + 0.22)
        shoe_w = max(2.15, ra * 1.25)
        shoe_stations = [
            (Vector((-0.3, cy_f, z_ank + 0.3)),  Vector((1, 0, 0)), Vector((0, 1, 0)), 2.4, shoe_w * 0.88, {sh_b: 0.30, ft_b: 0.70}, 0.350),
            (Vector((+1.1, cy_f, SOLE_Z + 1.45)),Vector((1, 0, 0)), Vector((0, 1, 0)), 4.1, shoe_w * 1.02, {ft_b: 1.0}, 0.435),
            (Vector((+1.3, cy_f, SOLE_Z + 0.35)),Vector((1, 0, 0)), Vector((0, 1, 0)), 4.3, shoe_w * 1.05, {ft_b: 1.0}, 0.492),
            (Vector((+1.3, cy_f, SOLE_Z + 0.02)),Vector((1, 0, 0)), Vector((0, 1, 0)), 4.1, shoe_w * 0.98, {ft_b: 1.0}, 0.498),
        ]
        add_lofted_tube(
            mb, shoe_stations, n_seg=16,
            uv_fn=lambda uf, _th, vp, _si: (0.525 + 0.215 * uf, vp),
            cap_start=True, cap_end=True,
        )

    # ------------------------------------------------------------------
    # D. Character-Specific Funny 3D Props (Weighted to Hands / Hips!)
    # ------------------------------------------------------------------
    r_hand_c = Vector((1.1, -(cfg["wr_y"] + 0.2), z_sh - 19.6))
    l_hand_c = Vector((1.1, +(cfg["wr_y"] + 0.2), z_sh - 19.6))

    if key == "randguy":
        # 1) Giant 64oz Gas-Station MEGA GULP Cup + Lid + Red-Striped Bendy Straw in Right Hand!
        cup_st = [
            (r_hand_c + Vector((1.6, 0.0, -2.4)), Vector((1, 0, 0)), Vector((0, 1, 0)), 1.45, 1.45, {"Hand.R": 1.0}, 0.86),
            (r_hand_c + Vector((1.6, 0.0, +2.6)), Vector((1, 0, 0)), Vector((0, 1, 0)), 2.05, 2.05, {"Hand.R": 1.0}, 0.53),
            (r_hand_c + Vector((1.6, 0.0, +3.1)), Vector((1, 0, 0)), Vector((0, 1, 0)), 2.18, 2.18, {"Hand.R": 1.0}, 0.52),
        ]
        add_lofted_tube(mb, cup_st, 14, lambda uf, _th, vp, _si: (0.52 + 0.24 * uf, vp), cap_start=True, cap_end=True)
        # Bendy Straw rising out of lid
        straw_st = [
            (r_hand_c + Vector((1.6, 0.0, +3.1)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.22, 0.22, {"Hand.R": 1.0}, 0.72),
            (r_hand_c + Vector((1.2, 0.2, +5.6)), Vector((1, 0, 0)), Vector((0, 1, 0)), 0.22, 0.22, {"Hand.R": 1.0}, 0.63),
        ]
        add_lofted_tube(mb, straw_st, 8, lambda uf, _th, vp, _si: (0.78 + 0.20 * uf, vp), cap_start=False, cap_end=True)
        # Dad Belt-Clip Phone Holster on right hip!
        add_round_box(mb, Vector((0.8, -(ry_h + 0.35), z_hip + 1.8)), 1.15, 0.55, 1.65, {"Pelvis": 1.0}, (0.79, 0.75, 0.98, 0.98))

    elif key == "afroguy":
        # Retro Chrome 80s Boombox held coolly in Left Hand (speakers on front face only, brushed chrome sides!)
        add_round_box(
            mb, l_hand_c + Vector((0.6, 1.4, -1.8)), 3.6, 1.45, 2.25,
            {"Hand.L": 1.0},
            uv_rect=(0.515, 0.515, 0.825, 0.835),
            rot_euler=(0.0, 0.0, math.radians(90.0)),
            side_uv=(0.514, 0.504, 0.528, 0.518),
            front_faces=(0,),
        )
        add_round_box(mb, l_hand_c + Vector((0.6, 1.4, +0.85)), 2.2, 0.25, 0.42, {"Hand.L": 1.0}, (0.86, 0.54, 0.98, 0.80), rot_euler=(0.0, 0.0, math.radians(90.0)))
        # Shiny 3D Gold Funk Medallion on front chest!
        add_uv_ellipsoid(mb, Vector((rx_c + 0.32, 0.0, z_chest + 2.4)), 0.28, 1.05, 1.05, {"Chest": 1.0}, (0.86, 0.54, 0.98, 0.82), 12, 8)

    elif key == "lady":
        # Quilted Faux-Designer Handbag dangling from Right Forearm/Hand + Pink Smartphone in Left Hand!
        add_round_box(
            mb, r_hand_c + Vector((0.5, -1.1, -2.6)), 2.75, 1.10, 2.30,
            {"Hand.R": 1.0},
            uv_rect=(0.52, 0.52, 0.80, 0.85),
            rot_euler=(0.0, 0.0, math.radians(85.0)),
            side_uv=(0.525, 0.525, 0.620, 0.630),
            front_faces=(0, 1),
        )
        # Purse handle arch
        add_round_box(mb, r_hand_c + Vector((0.5, -1.0, +0.3)), 1.35, 0.25, 0.85, {"Hand.R": 1.0}, (0.54, 0.89, 0.96, 0.98), rot_euler=(0.0, 0.0, math.radians(85.0)))
        # Pink Smartphone in Left Hand!
        add_round_box(
            mb, l_hand_c + Vector((1.25, 0.1, -0.3)), 1.25, 0.65, 0.16,
            {"Hand.L": 1.0},
            uv_rect=(0.83, 0.53, 0.99, 0.84),
            rot_euler=(math.radians(20.0), math.radians(-25.0), 0.0),
            side_uv=(0.832, 0.505, 0.852, 0.525),
            front_faces=(4,),
        )

    elif key == "fatguy":
        # Giant Foil-Wrapped Bakersfield XXL Monster Burrito gripped proudly in Right Hand!
        burrito_st = [
            (r_hand_c + Vector((0.4, 0.2, -2.5)), Vector((1, 0, 0)), Vector((0, 1, 0)), 1.55, 1.45, {"Hand.R": 1.0}, 0.98),
            (r_hand_c + Vector((1.4, -0.4, +0.4)), Vector((1, 0, 0)), Vector((0, 1, 0)), 1.72, 1.62, {"Hand.R": 1.0}, 0.72),
            (r_hand_c + Vector((2.3, -1.0, +3.2)), Vector((1, 0, 0)), Vector((0, 1, 0)), 1.65, 1.55, {"Hand.R": 1.0}, 0.52),
        ]
        add_lofted_tube(mb, burrito_st, 14, lambda uf, _th, vp, _si: (0.52 + 0.28 * uf, vp), cap_start=True, cap_end=False)
        # Delicious open bitten top cap mapped to carne-asada/guac/cheddar cross-section (u=0.82..0.98, t=0.61..0.78)!
        add_uv_ellipsoid(
            mb, r_hand_c + Vector((2.35, -1.05, +3.25)), 1.58, 1.48, 0.42,
            {"Hand.R": 1.0}, (0.82, 0.61, 0.98, 0.78), 12, 6,
            rot_euler=(math.radians(12.0), math.radians(18.0), 0.0),
        )

    # ------------------------------------------------------------------
    # E. Build Head Object + Body Object + Armature in Blender Scene
    # ------------------------------------------------------------------
    head_mb = build_sculpted_head_surface(
        key,
        z_neck_base=z_sh - 1.25,
        z_chin=cfg["z_chin"],
        z_crown=cfg["z_crown"],
        rx_skull=cfg["rx_skull"],
        ry_skull=cfg["ry_skull"],
        double_chin=cfg["double_chin"],
    )
    head_obj = head_mb.to_blender_object(sc, mat_head)
    body_obj = mb.to_blender_object(sc, mat_body)

    arm_data = bpy.data.armatures.new(f"Arm_{key}")
    arm_obj = bpy.data.objects.new(f"Rig_{key}", arm_data)
    sc.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def add_b(bname: str, h: Tuple[float, float, float], t: Tuple[float, float, float], par: str | None = None):
        b = eb.new(bname)
        b.head = Vector(h)
        b.tail = Vector(t)
        b.roll = 0.0
        if par:
            b.parent = eb[par]
        return b

    add_b("Root",   (0, 0, SOLE_Z), (1.0, 0, SOLE_Z))
    add_b("Pelvis", (0, 0, z_hip),  (0, 0, z_waist), "Root")
    add_b("Spine",  (0, 0, z_waist),(0, 0, z_chest), "Pelvis")
    add_b("Belly",  (2.0, 0, z_waist + 0.5), (8.0, 0, z_waist + 0.5), "Spine")
    add_b("Chest",  (0, 0, z_chest),(0, 0, z_neck),  "Spine")
    add_b("Neck",   (0, 0, z_neck), (0, 0, cfg["z_chin"] + 0.5), "Chest")
    add_b("Head",   (0, 0, cfg["z_chin"] + 0.5), (0, 0, cfg["z_crown"]), "Neck")
    add_b("Afro",   (-0.8, 0, cfg["z_chin"] + 5.5), (-0.8, 0, cfg["z_crown"] + 5.0), "Head")

    for side, sy in (("R", -1.0), ("L", +1.0)):
        sh_h = (0.0, sy * (cfg["sh_y"] - 0.9), z_sh - 0.5)
        el_h = (-0.3, sy * cfg["el_y"], z_sh - 9.4)
        wr_h = (0.45, sy * cfg["wr_y"], z_sh - 17.2)
        tp_h = (0.95, sy * (cfg["wr_y"] + 0.10), z_sh - 21.8)
        add_b(f"UpperArm.{side}", sh_h, el_h, "Chest")
        add_b(f"Forearm.{side}",  el_h, wr_h, f"UpperArm.{side}")
        add_b(f"Hand.{side}",     wr_h, tp_h, f"Forearm.{side}")

        hp_h = (0.0, sy * cfg["hip_y"], z_hip + 0.6)
        kn_h = (0.20, sy * (cfg["hip_y"] + 0.20), z_knee)
        an_h = (-0.15, sy * (cfg["hip_y"] + 0.22), z_ank)
        ft_t = (+3.2, sy * (cfg["hip_y"] + 0.22), SOLE_Z + 0.5)
        add_b(f"Thigh.{side}", hp_h, kn_h, "Pelvis")
        add_b(f"Shin.{side}",  kn_h, an_h, f"Thigh.{side}")
        add_b(f"Foot.{side}",  an_h, ft_t, f"Shin.{side}")

    bpy.ops.object.mode_set(mode="OBJECT")

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = "XYZ"

    for mesh_obj in (head_obj, body_obj):
        mesh_obj.parent = arm_obj
        am = mesh_obj.modifiers.new("Armature", type="ARMATURE")
        am.object = arm_obj
        am.use_deform_preserve_volume = True
        cs = mesh_obj.modifiers.new("CorrectiveSmooth", type="CORRECTIVE_SMOOTH")
        cs.factor = 0.45
        cs.iterations = 4
        cs.smooth_type = "LENGTH_WEIGHTED"

    return arm_obj, head_obj, body_obj


# ==============================================================================
# 4. EXPRESSIVE 50-FRAME POSE ENGINE (IDLE, WALK, RUN, FUNNY, PAIN, DEATH)
# ==============================================================================

def set_world_bone_rot(arm_obj: bpy.types.Object, bname: str, pitch_deg: float = 0.0, roll_deg: float = 0.0, yaw_deg: float = 0.0, loc_delta: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> None:
    """Applies world-aligned rotation around bone's rest axes:
      - `pitch_deg > 0`: swings downward-hanging limb FORWARD (+X) or pitches upright spine/head FORWARD (+X)!
      - `roll_deg > 0`: rolls/abducts toward +Y (left) / tilts right-ear down!
      - `yaw_deg > 0`: twists CCW around +Z (looking left)!
    """
    pb = arm_obj.pose.bones[bname]
    rest_m = pb.bone.matrix_local.to_3x3()
    # World rotation matrix: Rz(yaw) * Rx(roll) * Ry_fwd(pitch)
    # Wait: in right-handed (+X fwd, +Y left, +Z up):
    #   Rotation around +Y by +alpha maps:
    #     +Z -> (+sin a, 0, cos a)  (upright torso leans FORWARD +X!)
    #     -Z -> (-sin a, 0, -cos a) (downward limb swings BACKWARD -X!)
    # So we distinguish upright bones (Pelvis/Spine/Chest/Neck/Head/Afro) vs downward limbs!
    rest_dir = (pb.bone.tail_local - pb.bone.head_local).normalized()
    is_down_limb = rest_dir.z < -0.35
    ry_rad = math.radians(-pitch_deg if is_down_limb else pitch_deg)
    rx_rad = math.radians(roll_deg)
    rz_rad = math.radians(yaw_deg)

    R_world = (
        Matrix.Rotation(rz_rad, 3, "Z")
        @ Matrix.Rotation(rx_rad, 3, "X")
        @ Matrix.Rotation(ry_rad, 3, "Y")
    )
    local_r = rest_m.inverted() @ R_world @ rest_m
    M = local_r.to_4x4()
    if any(abs(v) > 1e-5 for v in loc_delta):
        M.translation = rest_m.inverted() @ Vector(loc_delta)
    pb.matrix_basis = M


def reset_pose(arm_obj: bpy.types.Object) -> None:
    for pb in arm_obj.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)


def apply_character_frame(arm_obj: bpy.types.Object, key: str, fi: int) -> None:
    """Poses `arm_obj` at frame `fi` in 0..49."""
    reset_pose(arm_obj, )
    is_fat = key == "fatguy"
    is_afro = key == "afroguy"
    is_lady = key == "lady"
    is_rand = key == "randguy"

    # ------------------------------------------------------------------
    # CLIP 0: IDLE (frames 0..7)
    # ------------------------------------------------------------------
    if 0 <= fi <= 7:
        ph = TAU * (fi / 8.0)
        s1, c1 = math.sin(ph), math.cos(ph)
        set_world_bone_rot(arm_obj, "Pelvis", pitch_deg=1.5 * s1, roll_deg=2.2 * s1, yaw_deg=3.0 * c1, loc_delta=(0.0, 0.35 * s1, 0.25 * abs(s1)))
        set_world_bone_rot(arm_obj, "Spine", pitch_deg=2.0 * s1, yaw_deg=3.5 * s1)
        set_world_bone_rot(arm_obj, "Chest", pitch_deg=1.8 * c1, roll_deg=-1.8 * s1)
        set_world_bone_rot(arm_obj, "Head", pitch_deg=-3.0 * s1, yaw_deg=11.0 * s1)

        if is_rand:
            # Holding 64oz Mega Gulp casually in right hand
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=24.0 + 3.0 * s1, roll_deg=-6.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=52.0 + 4.0 * c1)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=-4.0 * s1, roll_deg=5.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=14.0)
        elif is_afro:
            # Smooth funk groove head-nod & boombox carry
            set_world_bone_rot(arm_obj, "Head", pitch_deg=7.0 * math.sin(2 * ph), yaw_deg=9.0 * s1)
            set_world_bone_rot(arm_obj, "Afro", pitch_deg=-5.0 * math.cos(2 * ph))
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=14.0, roll_deg=10.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=28.0)
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=-6.0 * s1, roll_deg=-8.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=18.0)
        elif is_lady:
            # Sassy purse on forearm + checking phone
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=16.0, roll_deg=-8.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=64.0 + 4.0 * s1)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=26.0, roll_deg=6.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=58.0 + 5.0 * c1)
        elif is_fat:
            # Happy heavy breathing belly + admiring XXL burrito!
            set_world_bone_rot(arm_obj, "Belly", pitch_deg=4.5 * s1, loc_delta=(0.35 * s1, 0.0, 0.25 * c1))
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=28.0 + 5.0 * s1, roll_deg=-12.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=56.0 + 6.0 * s1)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=6.0, roll_deg=14.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=22.0)

    # ------------------------------------------------------------------
    # CLIP 1: WALK (frames 8..19, 12 frames)
    # ------------------------------------------------------------------
    elif 8 <= fi <= 19:
        ph = TAU * ((fi - 8) / 12.0)
        s1, c1 = math.sin(ph), math.cos(ph)
        s2, c2 = math.sin(2.0 * ph), math.cos(2.0 * ph)

        stride = 28.0 if not is_fat else 22.0
        waddle_roll = 8.5 if is_fat else (5.0 if is_lady else 3.5)
        lean_fwd = -5.5 if is_afro else (4.0 if is_lady else (-3.0 if is_fat else 2.5))
        bob_z = 0.85 * (0.5 + 0.5 * c2)

        set_world_bone_rot(
            arm_obj, "Pelvis",
            pitch_deg=lean_fwd + 2.0 * c2,
            roll_deg=waddle_roll * s1,
            yaw_deg=6.5 * s1,
            loc_delta=(0.0, (1.1 if is_fat else 0.55) * s1, bob_z),
        )
        set_world_bone_rot(arm_obj, "Spine", pitch_deg=2.0, roll_deg=-0.45 * waddle_roll * s1, yaw_deg=-7.5 * s1)
        set_world_bone_rot(arm_obj, "Chest", pitch_deg=1.5 * s2, yaw_deg=-5.5 * s1)
        set_world_bone_rot(arm_obj, "Head", pitch_deg=(6.5 * s2 if is_afro else -2.0 * s2), yaw_deg=4.5 * s1)

        if is_fat:
            set_world_bone_rot(arm_obj, "Belly", pitch_deg=9.0 * math.sin(2 * ph - 0.7), roll_deg=6.0 * c1, loc_delta=(0.25, 0.0, -0.55 * math.sin(2 * ph - 0.6)))
        if is_afro:
            set_world_bone_rot(arm_obj, "Afro", pitch_deg=-6.0 * math.sin(2 * ph - 0.5))

        # Realistic 2-step leg cycle (L = ph, R = ph + pi)
        for side, leg_ph in (("L", ph), ("R", ph + math.pi)):
            ls, lc = math.sin(leg_ph), math.cos(leg_ph)
            hip_ang = stride * ls
            # Knee bends strongly during forward swing (lc > 0) + slight cushion on stance!
            knee_bend = max(0.0, lc) * 42.0 + max(0.0, -ls) * 8.0
            foot_ang = -14.0 * ls + 10.0 * max(0.0, lc)
            set_world_bone_rot(arm_obj, f"Thigh.{side}", pitch_deg=hip_ang)
            set_world_bone_rot(arm_obj, f"Shin.{side}", pitch_deg=-knee_bend)
            set_world_bone_rot(arm_obj, f"Foot.{side}", pitch_deg=foot_ang)

        # Counter-swinging arms with prop awareness!
        if is_rand:
            # Right hand carries Mega Gulp with gentle bob; Left arm swings naturally
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=22.0 + 8.0 * (-s1), roll_deg=-6.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=48.0 + 6.0 * c2)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=24.0 * (-s1), roll_deg=6.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=18.0 + 12.0 * max(0.0, -s1))
        elif is_afro:
            # Funk strut swagger!
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=30.0 * (-s1), roll_deg=-10.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=24.0 + 16.0 * max(0.0, -s1))
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=12.0 + 12.0 * s1, roll_deg=12.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=26.0)
        elif is_lady:
            # Power-walk swinging quilted purse on right forearm + holding phone in left
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=18.0 + 16.0 * (-s1), roll_deg=-9.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=66.0 + 8.0 * c1)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=24.0 + 10.0 * s1, roll_deg=7.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=54.0)
        elif is_fat:
            # Wide burrito waddle!
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=30.0 + 12.0 * (-s1), roll_deg=-14.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=58.0 + 8.0 * s2)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=24.0 * s1, roll_deg=16.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=26.0 + 10.0 * max(0.0, s1))

    # ------------------------------------------------------------------
    # CLIP 2: RUN / COMEDIC SPRINT (frames 20..29, 10 frames)
    # ------------------------------------------------------------------
    elif 20 <= fi <= 29:
        ph = TAU * ((fi - 20) / 10.0)
        s1, c1 = math.sin(ph), math.cos(ph)
        s2, c2 = math.sin(2.0 * ph), math.cos(2.0 * ph)

        stride = 48.0 if not is_fat else 38.0
        lean_fwd = 14.0 if not is_fat else 7.0
        flight_z = 2.1 * (0.5 + 0.5 * s2)

        set_world_bone_rot(
            arm_obj, "Pelvis",
            pitch_deg=lean_fwd + 3.5 * c2,
            roll_deg=(10.5 if is_fat else 5.5) * s1,
            yaw_deg=10.0 * s1,
            loc_delta=(0.0, (1.4 if is_fat else 0.7) * s1, flight_z),
        )
        set_world_bone_rot(arm_obj, "Spine", pitch_deg=6.0, yaw_deg=-11.0 * s1)
        set_world_bone_rot(arm_obj, "Chest", pitch_deg=4.0 + 3.0 * s2, yaw_deg=-9.0 * s1)
        set_world_bone_rot(arm_obj, "Head", pitch_deg=-10.0 + 5.0 * c2, yaw_deg=8.0 * c1)

        if is_fat:
            # Glorious rapid secondary belly jiggle!
            set_world_bone_rot(arm_obj, "Belly", pitch_deg=18.0 * math.sin(2 * ph - 0.8), roll_deg=10.0 * c1, loc_delta=(0.45, 0.0, -1.25 * math.sin(2 * ph - 0.7)))
        if is_afro:
            set_world_bone_rot(arm_obj, "Afro", pitch_deg=-12.0 * math.sin(2 * ph - 0.6), roll_deg=6.0 * c1)

        for side, leg_ph in (("L", ph), ("R", ph + math.pi)):
            ls, lc = math.sin(leg_ph), math.cos(leg_ph)
            hip_ang = stride * ls + 10.0
            knee_bend = 18.0 + max(0.0, lc) * 68.0 + max(0.0, -ls) * 24.0
            foot_ang = -22.0 * ls + 16.0 * max(0.0, lc)
            set_world_bone_rot(arm_obj, f"Thigh.{side}", pitch_deg=hip_ang)
            set_world_bone_rot(arm_obj, f"Shin.{side}", pitch_deg=-knee_bend)
            set_world_bone_rot(arm_obj, f"Foot.{side}", pitch_deg=foot_ang)

        if is_rand:
            # "DON'T SPILL THE SODA!" — Right arm holds cup out front; Left arm flails high in panic!
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=58.0 + 8.0 * s2, roll_deg=-10.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=34.0 - 8.0 * s2)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=115.0 + 28.0 * s1, roll_deg=26.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=32.0 + 20.0 * c1)
        elif is_afro:
            # Right hand reaches up to hold his giant bouncing Afro while sprinting!
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=118.0 + 8.0 * s2, roll_deg=-24.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=75.0)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=24.0 + 36.0 * s1, roll_deg=14.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=55.0)
        elif is_lady:
            # Full "AAAH MANAGER!!" arms-up purse-flailing panic sprint!
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=108.0 + 30.0 * (-s1), roll_deg=-28.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=42.0 + 18.0 * c1)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=108.0 + 30.0 * s1, roll_deg=28.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=42.0 - 18.0 * c1)
        elif is_fat:
            # Maximum-effort piston arms thunder-waddle protecting his burrito!
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=44.0 + 26.0 * (-s1), roll_deg=-20.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=72.0)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=48.0 * s1, roll_deg=24.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=68.0)

    # ------------------------------------------------------------------
    # CLIP 3: SIGNATURE FUNNY EMOTE (frames 30..39, 10 frames)
    # ------------------------------------------------------------------
    elif 30 <= fi <= 39:
        u = (fi - 30) / 10.0
        ph = TAU * u
        env = math.sin(math.pi * u)

        if is_rand:
            # Sips Mega Gulp -> drips on shirt -> looks down at chest & shrugs "AW COME ON!"
            look_down = 28.0 * smooth01((u - 0.25) / 0.25) * (1.0 - smooth01((u - 0.80) / 0.20))
            shrug = math.sin(math.pi * max(0.0, min(1.0, (u - 0.25) / 0.65)))
            set_world_bone_rot(arm_obj, "Head", pitch_deg=look_down, yaw_deg=10.0 * math.sin(2 * ph) * shrug)
            set_world_bone_rot(arm_obj, "Chest", pitch_deg=6.0 * shrug)
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=55.0 - 25.0 * shrug, roll_deg=-22.0 * shrug)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=75.0 - 35.0 * shrug)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=35.0 * shrug, roll_deg=48.0 * shrug)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=52.0 * shrug)
        elif is_afro:
            # SATURDAY NIGHT DISCO SKY-POINT & HIP POP!
            groove = math.sin(ph)
            set_world_bone_rot(arm_obj, "Pelvis", roll_deg=11.0 * groove, yaw_deg=-15.0 * env, loc_delta=(0.0, 1.4 * groove, -0.8 * abs(groove)))
            set_world_bone_rot(arm_obj, "Chest", roll_deg=-9.0 * groove, yaw_deg=18.0 * env)
            set_world_bone_rot(arm_obj, "Head", pitch_deg=-14.0 * env, yaw_deg=-16.0 * env)
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=148.0 * env, roll_deg=-32.0 * env)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=12.0)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=18.0, roll_deg=18.0)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=38.0)
        elif is_lady:
            # SASSY HOA HAND-ON-HIP + AGGRESSIVE PURSE-SWING SCOLD!
            wag = math.sin(2.0 * ph) * env
            set_world_bone_rot(arm_obj, "Pelvis", roll_deg=-8.0 * env, loc_delta=(0.0, -1.0 * env, 0.0))
            set_world_bone_rot(arm_obj, "Chest", pitch_deg=10.0 * env, yaw_deg=14.0 * wag)
            set_world_bone_rot(arm_obj, "Head", pitch_deg=6.0 * env, yaw_deg=-18.0 * wag)
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=-10.0, roll_deg=36.0 * env)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=78.0 * env)
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=78.0 * env + 26.0 * wag, roll_deg=-18.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=45.0 + 25.0 * wag)
        elif is_fat:
            # TWO BELLY-DRUM SLAPS + JIGGLE + TRIUMPHANT XXL BURRITO SALUTE!
            slap = abs(math.sin(2.0 * ph)) * env
            set_world_bone_rot(arm_obj, "Pelvis", pitch_deg=-8.0 * env, loc_delta=(0.0, 0.0, 0.5 * slap))
            set_world_bone_rot(arm_obj, "Chest", pitch_deg=-12.0 * env)
            set_world_bone_rot(arm_obj, "Head", pitch_deg=-16.0 * env, yaw_deg=8.0 * math.sin(ph))
            set_world_bone_rot(arm_obj, "Belly", pitch_deg=22.0 * math.sin(3.0 * ph) * env, loc_delta=(0.7 * slap, 0.0, 0.8 * math.cos(3.0 * ph) * env))
            # Right arm hoists burrito overhead!
            set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=30.0 + 105.0 * env, roll_deg=-18.0)
            set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=50.0 - 25.0 * env)
            # Left hand slaps belly rhythmically!
            set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=38.0 * env, roll_deg=18.0 - 28.0 * slap)
            set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=65.0 * slap + 25.0)

    # ------------------------------------------------------------------
    # CLIP 4: STARTLED PAIN FLINCH (frames 40..43, 4 frames)
    # ------------------------------------------------------------------
    elif 40 <= fi <= 43:
        env = math.sin(math.pi * ((fi - 39.5) / 4.5))
        set_world_bone_rot(arm_obj, "Pelvis", pitch_deg=-14.0 * env, yaw_deg=14.0 * env, loc_delta=(-1.2 * env, 0.0, 2.8 * env))
        set_world_bone_rot(arm_obj, "Chest", pitch_deg=-16.0 * env)
        set_world_bone_rot(arm_obj, "Head", pitch_deg=-22.0 * env, yaw_deg=-18.0 * env)
        set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=85.0 * env, roll_deg=-42.0 * env)
        set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=85.0 * env, roll_deg=42.0 * env)
        set_world_bone_rot(arm_obj, "Thigh.L", pitch_deg=22.0 * env)
        set_world_bone_rot(arm_obj, "Shin.L", pitch_deg=-35.0 * env)

    # ------------------------------------------------------------------
    # CLIP 5: COMEDIC COLLAPSE DEATH (frames 44..49, 6 frames)
    # ------------------------------------------------------------------
    else:
        t = smooth01((fi - 44) / 5.0)
        # Spins & tips backward onto floor so back rests cleanly near SOLE_Z = -24!
        drop_z = (SOLE_Z + 4.2 - CHAR_CONFIGS[key]["z_hip"]) * (t ** 1.15)
        set_world_bone_rot(
            arm_obj, "Pelvis",
            pitch_deg=-88.0 * t,
            roll_deg=12.0 * t,
            yaw_deg=32.0 * t,
            loc_delta=(-6.0 * t, 0.0, drop_z),
        )
        set_world_bone_rot(arm_obj, "Spine", pitch_deg=-4.0 * (1.0 - t))
        set_world_bone_rot(arm_obj, "Head", pitch_deg=18.0 * t, yaw_deg=28.0 * t)
        set_world_bone_rot(arm_obj, "UpperArm.R", pitch_deg=15.0 * (1.0 - t), roll_deg=-58.0 * t)
        set_world_bone_rot(arm_obj, "Forearm.R", pitch_deg=22.0 * t)
        set_world_bone_rot(arm_obj, "UpperArm.L", pitch_deg=10.0 * (1.0 - t), roll_deg=64.0 * t)
        set_world_bone_rot(arm_obj, "Forearm.L", pitch_deg=18.0 * t)
        set_world_bone_rot(arm_obj, "Thigh.R", pitch_deg=8.0 * (1.0 - t), roll_deg=-16.0 * t)
        set_world_bone_rot(arm_obj, "Thigh.L", pitch_deg=-6.0 * (1.0 - t), roll_deg=18.0 * t)
        set_world_bone_rot(arm_obj, "Shin.R", pitch_deg=-12.0 * (1.0 - t))
        set_world_bone_rot(arm_obj, "Shin.L", pitch_deg=-10.0 * (1.0 - t))


FRAME_NAMES: List[str] = (
    [f"idle{i+1}" for i in range(8)]
    + [f"walk{i+1}" for i in range(12)]
    + [f"run{i+1}" for i in range(10)]
    + [f"funny{i+1}" for i in range(10)]
    + [f"pain{i+1}" for i in range(4)]
    + [f"death{i+1}" for i in range(6)]
)


# ==============================================================================
# 5. MD3 DEPSGRAPH SAMPLER, SKIN/SHADER WRITER, GLB EXPORTER & PREVIEW RENDERER
# ==============================================================================

def extract_md3_surface_topology(eval_mesh: bpy.types.Mesh, surf_name: str, shader_name: str):
    """Builds deduplicated `(vert_idx, u, t_top)` vertex buffer (< 4096 verts) and outward triangle list."""
    eval_mesh.calc_loop_triangles()
    uv_layer = eval_mesh.uv_layers.active.data
    vmap: Dict[Tuple[int, int, int], int] = {}
    src_v_indices: List[int] = []
    st_list: List[Tuple[float, float]] = []
    tris: List[Tuple[int, int, int]] = []

    for lt in eval_mesh.loop_triangles:
        tri_out = []
        for vi, li in zip(lt.vertices, lt.loops):
            uv = uv_layer[li].uv
            u = float(uv[0])
            t_top = float(1.0 - uv[1])
            key = (int(vi), int(round(u * 8192)), int(round(t_top * 8192)))
            if key not in vmap:
                vmap[key] = len(src_v_indices)
                src_v_indices.append(int(vi))
                st_list.append((u, t_top))
            tri_out.append(vmap[key])
        tris.append((tri_out[0], tri_out[1], tri_out[2]))

    assert len(st_list) < 4096, f"{surf_name} exceeded MD3 4096 vertex limit ({len(st_list)})!"
    return dict(
        name=surf_name,
        shader=shader_name,
        tris=tris,
        st=st_list,
        src_vi=np.array(src_v_indices, dtype=np.int32),
        frames=[],
    )


def make_unlit_or_principled_mat(name: str, img_path: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.72
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.25
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path, check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def export_character_md3_and_glb(key: str) -> Dict:
    cfg = CHAR_CONFIGS[key]
    md3_base = cfg["md3_name"]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene

    head_tex_name = f"{md3_base}_head"
    body_tex_0 = f"{md3_base}_body_0" if cfg["skins"] > 1 else f"{md3_base}_body"

    mat_head = make_unlit_or_principled_mat(head_tex_name, os.path.join(SRGB_DIR, f"{head_tex_name}.png"))
    mat_body = make_unlit_or_principled_mat(body_tex_0, os.path.join(SRGB_DIR, f"{body_tex_0}.png"))

    arm_obj, head_obj, body_obj = build_body_surface_and_rig(sc, key, mat_head, mat_body)

    # Sample all 50 frames from evaluated Blender depsgraph (AND keyframe pose bones for animated .glb!)
    sc.frame_start = 0
    sc.frame_end = 49

    surf_head = None
    surf_body = None

    for fi in range(50):
        sc.frame_set(fi)
        apply_character_frame(arm_obj, key, fi)
        for pb in arm_obj.pose.bones:
            pb.keyframe_insert(data_path="location", frame=fi)
            pb.keyframe_insert(data_path="rotation_euler", frame=fi)

        dg = bpy.context.evaluated_depsgraph_get()

        for obj, s_tag, sh_path, holder in (
            (head_obj, "head", f"progs/{head_tex_name}", "head"),
            (body_obj, "body", f"progs/{md3_base}_body", "body"),
        ):
            ev_obj = obj.evaluated_get(dg)
            ev_me = ev_obj.to_mesh()
            if fi == 0:
                s_dict = extract_md3_surface_topology(ev_me, s_tag, sh_path)
                if holder == "head":
                    surf_head = s_dict
                else:
                    surf_body = s_dict
            s_cur = surf_head if holder == "head" else surf_body
            nv_raw = len(ev_me.vertices)
            co = np.zeros(nv_raw * 3, dtype=np.float32)
            nm = np.zeros(nv_raw * 3, dtype=np.float32)
            ev_me.vertices.foreach_get("co", co)
            ev_me.vertices.foreach_get("normal", nm)
            co = co.reshape(nv_raw, 3)[s_cur["src_vi"]]
            nm = nm.reshape(nv_raw, 3)[s_cur["src_vi"]]
            s_cur["frames"].append(
                (
                    [(float(p[0]), float(p[1]), float(p[2])) for p in co],
                    [(float(n[0]), float(n[1]), float(n[2])) for n in nm],
                )
            )
            ev_obj.to_mesh_clear()

    # Verify standing height on frame 0!
    all_z = [p[2] for p in surf_head["frames"][0][0]] + [p[2] for p in surf_body["frames"][0][0]]
    all_y = [p[1] for p in surf_body["frames"][0][0]]
    z_min, z_max = min(all_z), max(all_z)
    width_y = max(all_y) - min(all_y)

    # Write MD3
    for s in (surf_head, surf_body):
        del s["src_vi"]
    md3_path = os.path.join(PROGS_DIR, f"{md3_base}.md3")
    md3lib.write(
        md3_path,
        dict(
            name=f"progs/{md3_base}.md3",
            frame_names=FRAME_NAMES,
            surfaces=[surf_head, surf_body],
        ),
    )

    # Write .md3_N.skin files
    if cfg["skins"] > 1:
        for sk in range(cfg["skins"]):
            sk_path = os.path.join(PROGS_DIR, f"{md3_base}.md3_{sk}.skin")
            with open(sk_path, "w", encoding="ascii") as fp:
                fp.write(f"head,progs/{head_tex_name}\n")
                fp.write(f"body,progs/{md3_base}_body_{sk}\n")
    else:
        sk_path = os.path.join(PROGS_DIR, f"{md3_base}.md3_0.skin")
        with open(sk_path, "w", encoding="ascii") as fp:
            fp.write(f"head,progs/{head_tex_name}\n")
            fp.write(f"body,progs/{md3_base}_body\n")

    # Export animated glTF 2.0 (.glb) at mod root
    sc.frame_set(8)  # Default stride pose for static thumbnails
    glb_path = os.path.join(MOD_ROOT, f"{md3_base}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        export_animations=True,
        export_yup=True,
    )

    print(
        f"BUILT {md3_base}.md3: z=[{z_min:.2f}..{z_max:.2f}] (H={z_max - z_min:.2f}u, W={width_y:.2f}u) "
        f"| head_v={len(surf_head['st'])} body_v={len(surf_body['st'])} | skins={cfg['skins']}"
    )
    return dict(key=key, md3=md3_base, z_min=z_min, z_max=z_max, height=z_max - z_min, width=width_y)


def write_shader_file() -> None:
    shader_names = [
        "npc_randguy_head", "npc_randguy_body",
        *[f"npc_randguy_body_{i}" for i in range(6)],
        "npc_afroguy_head", "npc_afroguy_body",
        "npc_randlady_head", "npc_randlady_body",
        *[f"npc_randlady_body_{i}" for i in range(3)],
        "npc_fatguy_head", "npc_fatguy_body",
    ]
    lines = ["// Generated by source/mm_tools/random_npcs/blender_build_random_npcs.py\n"]
    for sn in shader_names:
        lines.append(
            f"progs/{sn}\n{{\n\tcull none\n\t{{\n\t\tmap progs/{sn}\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
        )
    sh_path = os.path.join(SCRIPTS_DIR, "random_npcs.shader")
    with open(sh_path, "w", encoding="ascii") as fp:
        fp.write("\n".join(lines))
    print(f"WROTE {sh_path}")


def render_lineup_and_action_sheet() -> str:
    """Renders a crisp Blender Eevee studio verification lineup showing all 4 NPCs side-by-side
    in Front Idle, 3/4 Walk, 3/4 Run, and Funny Emote poses (plus a 54u Quake player height gauge!)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 960
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"

    world = bpy.data.worlds.new("PreviewWorld")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.14, 0.17, 0.22, 1.0)
    bg.inputs["Strength"].default_value = 1.15

    # Studio floor plane at SOLE_Z = -24.0 + 54u player height reference bar on far left!
    bpy.ops.mesh.primitive_plane_add(size=260.0, location=(0.0, 0.0, SOLE_Z))
    fl = bpy.context.active_object
    m_fl = bpy.data.materials.new("FloorMat")
    m_fl.use_nodes = True
    m_fl.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.21, 0.26, 1.0)
    m_fl.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    fl.data.materials.append(m_fl)

    # Quake Player Height Gauge Post (-24 to +30 = 54u) at Y = -78
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -78.0, 3.0))
    bar = bpy.context.active_object
    bar.scale = (2.2, 2.2, 54.0)
    m_bar = bpy.data.materials.new("GaugeMat")
    m_bar.use_nodes = True
    m_bar.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.88, 0.48, 1.0)
    bar.data.materials.append(m_bar)

    keys = ["randguy", "afroguy", "lady", "fatguy"]
    y_slots = [-50.0, -17.0, +17.0, +53.0]

    rigs = []
    bodies = []
    for key, y_pos in zip(keys, y_slots):
        cfg = CHAR_CONFIGS[key]
        md3_base = cfg["md3_name"]
        h_mat = make_unlit_or_principled_mat(f"p_{key}_h", os.path.join(SRGB_DIR, f"{md3_base}_head.png"))
        b_tex = f"{md3_base}_body_0" if cfg["skins"] > 1 else f"{md3_base}_body"
        b_mat = make_unlit_or_principled_mat(f"p_{key}_b", os.path.join(SRGB_DIR, f"{b_tex}.png"))
        arm_obj, _ho, bo = build_body_surface_and_rig(sc, key, h_mat, b_mat)
        arm_obj.location = (0.0, y_pos, 0.0)
        rigs.append((key, arm_obj))
        bodies.append(bo)

    # Studio lights (character faces +X, so camera sits at +X looking toward -X!)
    for lname, loc, energy, col in (
        ("Key",  (135.0, -55.0, 68.0), 75000.0, (1.0, 0.99, 0.96)),
        ("Fill", (125.0, +75.0, 38.0), 48000.0, (0.92, 0.96, 1.0)),
        ("Rim",  (-95.0,   0.0, 75.0), 42000.0, (1.0, 0.97, 0.90)),
    ):
        ld = bpy.data.lights.new(lname, type="AREA")
        ld.energy = energy
        ld.color = col
        ld.size = 50.0
        lo = bpy.data.objects.new(lname, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0.0, 0.0, 4.0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

    cam_d = bpy.data.cameras.new("LineupCam")
    cam_d.lens = 45.0
    cam = bpy.data.objects.new("LineupCam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (208.0, -2.0, 8.0)
    cam.rotation_euler = (Vector((0.0, -2.0, 4.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()

    renders = []
    # 1) Front standing/idle lineup (shirt 0)
    for key, arm_obj in rigs:
        apply_character_frame(arm_obj, key, 0)
        arm_obj.rotation_euler = (0.0, 0.0, 0.0)
    p_idle = os.path.join(PREVIEW_DIR, "lineup_front_idle.png")
    sc.render.filepath = p_idle
    bpy.ops.render.render(write_still=True)
    renders.append(p_idle)

    # 2) 3/4 Walk + Random Guy wearing Hawaiian Shirt (skin 1) & Lady wearing Leopard Top (skin 1)!
    bodies[0].data.materials[0] = make_unlit_or_principled_mat("rg_s1", os.path.join(SRGB_DIR, "npc_randguy_body_1.png"))
    bodies[2].data.materials[0] = make_unlit_or_principled_mat("ld_s1", os.path.join(SRGB_DIR, "npc_randlady_body_1.png"))
    for key, arm_obj in rigs:
        apply_character_frame(arm_obj, key, 11)
        arm_obj.rotation_euler = (0.0, 0.0, math.radians(-32.0))
    p_walk = os.path.join(PREVIEW_DIR, "lineup_walk_3q.png")
    sc.render.filepath = p_walk
    bpy.ops.render.render(write_still=True)
    renders.append(p_walk)

    # 3) 3/4 Comedic Sprint + Random Guy wearing Forklift Shirt (skin 2)!
    bodies[0].data.materials[0] = make_unlit_or_principled_mat("rg_s2", os.path.join(SRGB_DIR, "npc_randguy_body_2.png"))
    for key, arm_obj in rigs:
        apply_character_frame(arm_obj, key, 22)
        arm_obj.rotation_euler = (0.0, 0.0, math.radians(34.0))
    p_run = os.path.join(PREVIEW_DIR, "lineup_run_3q.png")
    sc.render.filepath = p_run
    bpy.ops.render.render(write_still=True)
    renders.append(p_run)

    # 4) Signature Funny Emotes + Random Guy wearing Tie-Dye (skin 4)!
    bodies[0].data.materials[0] = make_unlit_or_principled_mat("rg_s4", os.path.join(SRGB_DIR, "npc_randguy_body_4.png"))
    for key, arm_obj in rigs:
        apply_character_frame(arm_obj, key, 35)
        arm_obj.rotation_euler = (0.0, 0.0, math.radians(-12.0))
    p_fun = os.path.join(PREVIEW_DIR, "lineup_funny.png")
    sc.render.filepath = p_fun
    bpy.ops.render.render(write_still=True)
    renders.append(p_fun)

    print("RENDERED PREVIEW PLATES:", renders)
    return p_idle


def main() -> None:
    write_shader_file()
    for k in ("randguy", "afroguy", "lady", "fatguy"):
        export_character_md3_and_glb(k)
    render_lineup_and_action_sheet()
    print("ALL 4 RANDOM PEOPLE 3D MODELS (.MD3 + .SKIN + .SHADER + .GLB) BUILT SUCCESSFULLY!")


if __name__ == "__main__":
    main()
