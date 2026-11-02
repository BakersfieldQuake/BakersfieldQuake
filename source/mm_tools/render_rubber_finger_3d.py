r"""Headless Blender 5.2 3D Sculpted & Real-Photo-Projected Character + Giant Floppy Rubber Finger Renderer!

Renders native-alpha RGBA studio frames across all 8 360° angles:
  - 8 standing crazed-idle directions:      raw_idle_d{0..7}.png
  - 8 directions x 8 frantic wag-run frames: raw_run_d{0..7}_f{0..7}.png
  - 8 escalating 'FOREHEAD BONK!' frames:    raw_bonk_{00..07}.png

Run test preview (5 frames):
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P source/mm_tools/render_rubber_finger_3d.py -- --test

Run full 80-frame render:
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P source/mm_tools/render_rubber_finger_3d.py
"""

from __future__ import annotations

import math
import os
import sys
import numpy as np
import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(HERE, "ref", "rubber_finger")
TEX_DIR = os.path.join(REF_DIR, "tex")
OUT_RAW = os.path.join(REF_DIR, "renders_3d")
os.makedirs(OUT_RAW, exist_ok=True)

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST_MODE = "--test" in ARGV


# ---------------------------------------------------------------------------
# 1. Scene, Transparent Studio Lighting & PBR / Hybrid Photo Materials
# ---------------------------------------------------------------------------

def setup_scene(res_w: int = 640, res_h: int = 680) -> bpy.types.Scene:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = eng
            break
        except Exception:
            continue

    scene.render.resolution_x = res_w
    scene.render.resolution_y = res_h
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    # AgX Medium High Contrast prevents any highlight clipping on pale rubber & skin while keeping punchy darks!
    for vt in ("AgX", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = vt
            break
        except Exception:
            continue
    for lk in ("Medium High Contrast", "High Contrast", "None"):
        try:
            scene.view_settings.look = lk
            break
        except Exception:
            continue

    if hasattr(scene, "eevee"):
        for attr, val in (("taa_render_samples", 24), ("use_raytracing", False)):
            if hasattr(scene.eevee, attr):
                try:
                    setattr(scene.eevee, attr, val)
                except Exception:
                    pass

    world = bpy.data.worlds.new("StudioWorld")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out_w = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.72, 0.75, 0.80, 1.0)
    bg.inputs["Strength"].default_value = 0.42
    nt.links.new(bg.outputs["Background"], out_w.inputs["Surface"])

    # Camera rig that orbits cleanly around Z so every angle gets balanced studio 3-point key/fill/rim light!
    cam_rig = bpy.data.objects.new("CameraRig", None)
    scene.collection.objects.link(cam_rig)

    cam_data = bpy.data.cameras.new("SpriteCam")
    cam_data.lens = 56.0
    cam_obj = bpy.data.objects.new("SpriteCam", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.parent = cam_rig
    cam_obj.location = (0.0, -4.55, 1.06)
    look_vec = Vector((0.0, 0.0, 1.00)) - cam_obj.location
    cam_obj.rotation_euler = look_vec.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    # Calibrated studio lights (zero overexposure on rubber finger knuckles & fingernail!)
    light_specs = [
        ("KeyLight",   ( 2.2, -3.2, 2.7), 115.0, (1.00, 0.97, 0.93), 1.7),
        ("FillLight",  (-2.6, -2.6, 1.6),  52.0, (0.86, 0.92, 1.00), 2.1),
        ("RimLight",   ( 0.0,  2.9, 2.6),  92.0, (0.94, 0.97, 1.00), 1.6),
        ("BottomFill", ( 0.0, -2.2, 0.1),  24.0, (1.00, 0.94, 0.88), 1.8),
    ]
    for name, loc, energy, col, sz in light_specs:
        ld = bpy.data.lights.new(name, type="AREA")
        ld.energy = energy
        ld.color = col
        ld.size = sz
        lo = bpy.data.objects.new(name, ld)
        scene.collection.objects.link(lo)
        lo.parent = cam_rig
        lo.location = loc
        dvec = Vector((0.0, 0.0, 1.05)) - Vector(loc)
        lo.rotation_euler = dvec.to_track_quat("-Z", "Y").to_euler()

    return scene


def make_tex_material(
    name: str,
    img_path: str,
    roughness: float = 0.55,
    specular: float = 0.35,
    unlit_mix: float = 0.0,
    subsurf: float = 0.0,
) -> tuple[bpy.types.Material, bpy.types.ShaderNodeTexImage]:
    """Creates an image-textured Principled BSDF material, optionally blending `unlit_mix` emission
    so real DSLR facial photographs preserve 100% crisp micro-contrast alongside 3D form shading."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path, check_existing=True)
    tex.interpolation = "Cubic"

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    if subsurf > 0.0 and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurf
        if "Subsurface Scale" in bsdf.inputs:
            bsdf.inputs["Subsurface Scale"].default_value = 0.025

    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if unlit_mix > 0.0:
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.inputs["Strength"].default_value = 0.96
        nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = unlit_mix
        nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
        nt.links.new(emit.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    else:
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat, tex


def make_solid_material(name: str, rgb: tuple[float, float, float], roughness: float = 0.45, metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


# ---------------------------------------------------------------------------
# 2. Parametric 3D Sculpted Mesh Builders (Organic Quad Meshes w/ Exact UVs!)
# ---------------------------------------------------------------------------

def build_uv_quad_mesh(name: str, pos_grid: np.ndarray, uv_grid: np.ndarray, mat: bpy.types.Material, cap_ends: bool = True) -> bpy.types.Object:
    """Builds a smooth-shaded quad mesh from `(N_v, N_u, 3)` positions where `N_u` has duplicate seam column
    (`pos_grid[:, 0] == pos_grid[:, -1]`) so cylindrical UVs wrap 0..1 with ZERO back-seam stretching!"""
    nv, nu_plus1, _ = pos_grid.shape
    nu = nu_plus1 - 1  # number of unique circumferential vertices around ring

    bm = bmesh.new()
    v_rows = []
    for iv in range(nv):
        row = []
        for iu in range(nu):
            p = pos_grid[iv, iu]
            row.append(bm.verts.new((float(p[0]), float(p[1]), float(p[2]))))
        v_rows.append(row)

    uv_layer = bm.loops.layers.uv.new("UVMap")

    for iv in range(nv - 1):
        for iu in range(nu):
            iu_next = (iu + 1) % nu
            # Winding so outward normal points away from centerline
            v00 = v_rows[iv][iu]
            v10 = v_rows[iv][iu_next]
            v11 = v_rows[iv + 1][iu_next]
            v01 = v_rows[iv + 1][iu]
            try:
                f = bm.faces.new((v00, v10, v11, v01))
                f.smooth = True
                uvs = [
                    uv_grid[iv, iu],
                    uv_grid[iv, iu + 1],
                    uv_grid[iv + 1, iu + 1],
                    uv_grid[iv + 1, iu],
                ]
                for loop, uv in zip(f.loops, uvs):
                    loop[uv_layer].uv = (float(uv[0]), float(uv[1]))
            except ValueError:
                pass

    if cap_ends:
        # Bottom cap (iv = 0) and Top cap (iv = nv - 1)
        p_bot = pos_grid[0, :nu].mean(axis=0)
        c_bot = bm.verts.new((float(p_bot[0]), float(p_bot[1]), float(p_bot[2])))
        for iu in range(nu):
            iu_next = (iu + 1) % nu
            f = bm.faces.new((c_bot, v_rows[0][iu_next], v_rows[0][iu]))
            f.smooth = True
            for lp in f.loops:
                lp[uv_layer].uv = (0.5, float(uv_grid[0, iu, 1]))

        p_top = pos_grid[-1, :nu].mean(axis=0)
        c_top = bm.verts.new((float(p_top[0]), float(p_top[1]), float(p_top[2])))
        for iu in range(nu):
            iu_next = (iu + 1) % nu
            f = bm.faces.new((c_top, v_rows[-1][iu], v_rows[-1][iu_next]))
            f.smooth = True
            for lp in f.loops:
                lp[uv_layer].uv = (0.5, float(uv_grid[-1, iu, 1]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def create_sculpted_photo_head(mat_head: bpy.types.Material) -> bpy.types.Object:
    """Creates the 1:3.2 oversized 3D sculpted head mesh (local origin at neck pivot (0,0,0), crown at +0.60m)
    aligned 1:1 with the DSLR head wrap texture (`u=0.5` is -Y front, `u=0.25` is -X right ear, `u=0.75` is +X left ear)!
    Includes real 3D nose bridge/tip, supraorbital brow, eyeballs, cheekbones, full jutting beard, ears & pompadour hair!"""
    nv, nu = 64, 96
    v_lin = np.linspace(0.0, 1.0, nv, dtype=np.float32)       # 0 = neck base, 1 = top hair spike crown
    u_lin = np.linspace(0.0, 1.0, nu + 1, dtype=np.float32)   # 0..1 around head (0.5 = front -Y)

    U, V = np.meshgrid(u_lin, v_lin)
    PHI = (U - 0.5) * 2.0 * math.pi                           # -pi..+pi (0 = Front -Y)
    deg = np.degrees(PHI)
    abs_deg = np.abs(deg)

    # Vertical Z profile from neck pivot (0.00) to top hair crown (0.61m)
    Z = V * 0.61

    # Sleek, natural masculine oval head + tucked slender neck (zero lower-temple boxiness or nape bulge!)
    rx_base = np.interp(V, [0.00, 0.13, 0.24, 0.42, 0.62, 0.80, 0.91, 0.975, 1.00],
                           [0.082, 0.092, 0.148, 0.166, 0.168, 0.156, 0.122, 0.062, 0.012])
    ry_base = np.interp(V, [0.00, 0.13, 0.24, 0.42, 0.62, 0.80, 0.91, 0.975, 1.00],
                           [0.085, 0.096, 0.158, 0.188, 0.194, 0.182, 0.142, 0.072, 0.014])

    # Anatomical 3D sculptural relief (in meters along outward ray):
    relief = np.zeros_like(U)

    # 1. Full thick 3D Beard & Chin projection on front-lower hemisphere (v=0.14..0.44, |deg| < 78°)
    beard_front = np.exp(-((deg / 54.0) ** 2)) * np.exp(-(((V - 0.26) / 0.12) ** 2))
    relief += 0.038 * beard_front

    # Mustache ridge under nose (v=0.39..0.45, |deg| < 28°)
    mustache = np.exp(-(((deg - 3.0) / 22.0) ** 2 + ((V - 0.415) / 0.032) ** 2))
    relief += 0.018 * mustache

    # Recessed open mouth hollow
    mouth_hollow = np.exp(-(((deg - 8.0) / 14.0) ** 2 + ((V - 0.345) / 0.035) ** 2))
    relief -= 0.016 * mouth_hollow

    # 2. Prominent 3D Nose Bridge & Nose Tip
    nose_tip = np.exp(-(((deg - 3.0) / 9.5) ** 2 + ((V - 0.495) / 0.042) ** 2))
    nose_bridge = np.exp(-(((deg - 1.5) / 8.0) ** 2 + ((V - 0.565) / 0.055) ** 2))
    relief += 0.036 * nose_tip + 0.020 * nose_bridge

    # 3. Supraorbital Brow Ridge + Bulging Bug-Eyeballs
    brow = np.exp(-((deg / 34.0) ** 2 + ((V - 0.675) / 0.026) ** 2))
    relief += 0.015 * brow
    for edeg in (-18.5, +18.5):
        socket = np.exp(-(((deg - edeg) / 11.5) ** 2 + ((V - 0.615) / 0.036) ** 2))
        eyeball = np.exp(-(((deg - edeg) / 6.8) ** 2 + ((V - 0.615) / 0.022) ** 2))
        relief += -0.009 * socket + 0.015 * eyeball

    # 4. 3D Sculpted Ears at |deg| = 94°, v = 0.43..0.58
    ear_bump = np.exp(-(((abs_deg - 94.0) / 7.5) ** 2 + ((V - 0.505) / 0.065) ** 2))
    relief += 0.022 * ear_bump

    # 5. Slicked-back Hair Pompadour sweep at top-front crown + smooth back occiput above hairline
    pomp = np.exp(-((deg / 35.0) ** 2 + ((V - 0.91) / 0.065) ** 2))
    occiput = np.exp(-(((abs_deg - 180.0) / 55.0) ** 2 + ((V - 0.66) / 0.16) ** 2))
    relief += 0.022 * pomp + 0.014 * occiput

    sin_p = np.sin(PHI)
    cos_p = np.cos(PHI)
    X = (rx_base + relief * 0.88) * sin_p
    # Remember: Front (PHI = 0) points along -Y!
    Y = -(ry_base + relief) * cos_p + 0.012 * beard_front * (-1.0)

    pos_grid = np.stack([X, Y, Z], axis=-1)
    uv_grid = np.stack([U, V], axis=-1)
    head_obj = build_uv_quad_mesh("CharHead", pos_grid, uv_grid, mat_head, cap_ends=True)
    return head_obj


def create_henley_torso(mat_henley: bpy.types.Material) -> bpy.types.Object:
    """Creates a muscular male torso in the fitted dark charcoal 2-button henley shirt (local Z = 0.00 waist .. 0.46 neck)."""
    nv, nu = 28, 48
    v_lin = np.linspace(0.0, 1.0, nv, dtype=np.float32)
    u_lin = np.linspace(0.0, 1.0, nu + 1, dtype=np.float32)
    U, V = np.meshgrid(u_lin, v_lin)
    PHI = (U - 0.5) * 2.0 * math.pi

    # Broad masculine chest/shoulders with a clean untucked shirt hem over the jeans waist (zero Z-fighting!)
    rx = np.interp(V, [0.00, 0.06, 0.25, 0.70, 0.88, 0.96, 1.00],
                      [0.190, 0.194, 0.188, 0.228, 0.236, 0.145, 0.108])
    ry = np.interp(V, [0.00, 0.06, 0.25, 0.70, 0.88, 0.96, 1.00],
                      [0.146, 0.150, 0.140, 0.158, 0.148, 0.118, 0.106])

    # Subtle pectoral chest fullness & smooth mid-shirt drape (zero wave at bottom hem V=0!)
    chest = np.exp(-((np.degrees(PHI) / 52.0) ** 2 + ((V - 0.68) / 0.18) ** 2)) * 0.016
    folds = 0.0025 * np.sin(PHI * 6.0 + V * 8.0) * np.sin(math.pi * V)

    X = (rx + chest * 0.4 + folds) * np.sin(PHI)
    Y = -(ry + chest + folds) * np.cos(PHI)
    Z = V * 0.46

    pos_grid = np.stack([X, Y, Z], axis=-1)
    uv_grid = np.stack([U, V], axis=-1)
    return build_uv_quad_mesh("CharTorso", pos_grid, uv_grid, mat_henley, cap_ends=True)


def create_pelvis_hips(mat_jeans: bpy.types.Material) -> bpy.types.Object:
    """Creates the jeans belt, fly & rounded seat/hip block (local Z = -0.13 crotch .. +0.13 waist) tucked cleanly inside shirt hem!"""
    nv, nu = 18, 40
    v_lin = np.linspace(0.0, 1.0, nv, dtype=np.float32)
    u_lin = np.linspace(0.0, 1.0, nu + 1, dtype=np.float32)
    U, V = np.meshgrid(u_lin, v_lin)
    PHI = (U - 0.5) * 2.0 * math.pi

    rx = np.interp(V, [0.00, 0.24, 0.52, 0.80, 1.00], [0.115, 0.176, 0.180, 0.162, 0.146])
    ry = np.interp(V, [0.00, 0.24, 0.52, 0.80, 1.00], [0.095, 0.130, 0.136, 0.120, 0.108])
    # Seat fullness on rear (+Y, |PHI| > 110°), tapering off at waist top
    seat = np.exp(-(((np.abs(np.degrees(PHI)) - 155.0) / 38.0) ** 2 + ((V - 0.42) / 0.24) ** 2)) * 0.022

    X = rx * np.sin(PHI)
    Y = -(ry * np.cos(PHI)) + seat
    Z = -0.13 + V * 0.26
    # Map belt + upper jeans region (v_uv = 0.65 .. 1.00 of jeans_tex.png)
    UV = np.stack([U, 0.65 + V * 0.35], axis=-1)
    return build_uv_quad_mesh("CharPelvis", np.stack([X, Y, Z], axis=-1), UV, mat_jeans, cap_ends=True)


def build_tube_along_curve(
    pts_center: np.ndarray,
    radii_xy: np.ndarray,
    nu: int = 28,
    v_uv_range: tuple[float, float] = (0.0, 1.0),
    forward_ref: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Sweeps an elliptical cross-section `radii_xy = (N_v, 2)` along a 3D spine `pts_center = (N_v, 3)`
    using parallel-transport (Bishop) frames so twisting/kinking NEVER occurs!"""
    nv = len(pts_center)
    tangents = np.zeros_like(pts_center)
    tangents[0] = pts_center[1] - pts_center[0]
    tangents[-1] = pts_center[-1] - pts_center[-2]
    if nv > 2:
        tangents[1:-1] = pts_center[2:] - pts_center[:-2]
    tangents /= np.maximum(np.linalg.norm(tangents, axis=-1, keepdims=True), 1e-6)

    # Initial reference normal pointing toward front (-Y) or provided `forward_ref`
    ref = np.array([0.0, -1.0, 0.0], dtype=np.float32) if forward_ref is None else np.asarray(forward_ref, dtype=np.float32)
    t0 = tangents[0]
    n0 = ref - np.dot(ref, t0) * t0
    if np.linalg.norm(n0) < 1e-4:
        n0 = np.array([1.0, 0.0, 0.0], dtype=np.float32) - t0[0] * t0
    n0 /= np.linalg.norm(n0)
    b0 = np.cross(t0, n0)

    normals = np.zeros_like(pts_center)
    binormals = np.zeros_like(pts_center)
    normals[0], binormals[0] = n0, b0

    for i in range(1, nv):
        ti_prev, ti = tangents[i - 1], tangents[i]
        axis = np.cross(ti_prev, ti)
        s_len = np.linalg.norm(axis)
        c_val = float(np.clip(np.dot(ti_prev, ti), -1.0, 1.0))
        if s_len > 1e-5:
            axis /= s_len
            ang = math.atan2(s_len, c_val)
            # Rodrigues rotation of previous normal
            ni = normals[i - 1] * c_val + np.cross(axis, normals[i - 1]) * s_len + axis * np.dot(axis, normals[i - 1]) * (1.0 - c_val)
            # Note: use exact sin(ang) = s_len, cos(ang) = c_val!
        else:
            ni = normals[i - 1].copy()
        ni -= np.dot(ni, ti) * ti
        ni /= max(float(np.linalg.norm(ni)), 1e-6)
        normals[i] = ni
        binormals[i] = np.cross(ti, ni)

    u_lin = np.linspace(0.0, 1.0, nu + 1, dtype=np.float32)
    v_lin = np.linspace(v_uv_range[0], v_uv_range[1], nv, dtype=np.float32)
    U, V = np.meshgrid(u_lin, v_lin)
    PHI = (U - 0.5) * 2.0 * math.pi  # PHI=0 -> along +normal (front -Y), PHI=+pi/2 -> along +binormal (+X)

    cp = np.cos(PHI)[..., None]
    sp = np.sin(PHI)[..., None]
    rx = radii_xy[:, 0][:, None, None]
    ry = radii_xy[:, 1][:, None, None]

    pos_grid = (
        pts_center[:, None, :]
        + sp * rx * binormals[:, None, :]
        + cp * ry * normals[:, None, :]
    )
    uv_grid = np.stack([U, V], axis=-1)
    return pos_grid.astype(np.float32), uv_grid.astype(np.float32)


def update_mesh_positions(obj: bpy.types.Object, pos_grid: np.ndarray, cap_ends: bool = True) -> None:
    """Fast in-place vertex coordinate update for a `build_uv_quad_mesh` object across animation frames!"""
    nv, nu_plus1, _ = pos_grid.shape
    nu = nu_plus1 - 1
    verts_flat = pos_grid[:, :nu, :].reshape(-1, 3)
    if cap_ends:
        p_bot = pos_grid[0, :nu].mean(axis=0, keepdims=True)
        p_top = pos_grid[-1, :nu].mean(axis=0, keepdims=True)
        verts_all = np.vstack([verts_flat, p_bot, p_top]).astype(np.float32)
    else:
        verts_all = verts_flat.astype(np.float32)

    obj.data.vertices.foreach_set("co", verts_all.ravel())
    obj.data.update()


def eval_giant_rubber_finger_grid(spine_pts: np.ndarray, dorsal_ref: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Evaluates the 48-station sculpted Giant Floppy Novelty Rubber Index Finger along `spine_pts = (48, 3)`!
    Includes:
      - Molded novelty rubber grip collar & ribs (`s = 0..0.14`)
      - Proximal, middle & distal phalanges (`s = 0.14..1.00`)
      - 3D PIP (`s=0.42`) & DIP (`s=0.69`) dorsal knuckle joint swells & wrinkle ridges
      - 3D inset dorsal fingernail plate (`s=0.79..0.97`) & rounded fingertip dome!
    Note: `dorsal_ref` points where `u = 0.5` (`PHI = 0`) faces — the fingernail & dorsal knuckles!
    """
    nv = len(spine_pts)
    nu = 40
    s = np.linspace(0.0, 1.0, nv, dtype=np.float32)

    # Base finger radius taper (chunky, unmistakable 15cm-thick comedy giant rubber finger!)
    r_base = np.interp(s, [0.00, 0.03, 0.13, 0.16, 0.42, 0.55, 0.69, 0.85, 0.94, 0.985, 1.00],
                          [0.088, 0.094, 0.078, 0.074, 0.076, 0.069, 0.068, 0.061, 0.050, 0.028, 0.004])
    # Molded rubber grip ribs at base (s = 0.02..0.13)
    grip_ribs = 0.0045 * np.sin(s * 2.0 * math.pi * 32.0) * ((s >= 0.02) & (s <= 0.13))
    r_w = r_base + grip_ribs
    r_d = r_base * 0.93 + grip_ribs

    pos_grid, uv_grid = build_tube_along_curve(
        spine_pts,
        np.stack([r_w, r_d], axis=-1),
        nu=nu,
        v_uv_range=(0.0, 1.0),
        forward_ref=dorsal_ref,
    )

    # Add circumferential 3D anatomical knuckle swells & inset fingernail plate along normal direction!
    u_lin = np.linspace(0.0, 1.0, nu + 1, dtype=np.float32)
    U, S_g = np.meshgrid(u_lin, s)
    PHI = (U - 0.5) * 2.0 * math.pi  # PHI = 0 is dorsal (fingernail & knuckles!)

    # Compute local outward radial unit vectors from spine
    vecs = pos_grid - spine_pts[:, None, :]
    nrms = vecs / np.maximum(np.linalg.norm(vecs, axis=-1, keepdims=True), 1e-5)

    # 3D dorsal knuckle joint swells + subtle wrinkle ripples at PIP (0.42) & DIP (0.69)
    dorsal_cos = np.maximum(0.0, np.cos(PHI))
    pip_swell = np.exp(-((S_g - 0.42) / 0.045) ** 2) * (0.006 * dorsal_cos + 0.003 * (np.sin(PHI) ** 2))
    dip_swell = np.exp(-((S_g - 0.69) / 0.038) ** 2) * (0.005 * dorsal_cos + 0.0025 * (np.sin(PHI) ** 2))
    wrinkle = 0.0018 * np.cos((S_g - 0.42) * 190.0) * np.exp(-((S_g - 0.42) / 0.035) ** 2) * (dorsal_cos ** 2)

    # Slight 3D fingernail plate flattening & raised cuticle rim on dorsal tip (S_g = 0.79..0.96, |PHI| < 38°)
    nail_mask = (np.abs(np.degrees(PHI)) < 38.0) & (S_g >= 0.79) & (S_g <= 0.965)
    nail_plate = np.where(nail_mask, 0.0032, 0.0)

    disp = (pip_swell + dip_swell + wrinkle + nail_plate)[..., None]
    pos_grid = pos_grid + nrms * disp
    return pos_grid.astype(np.float32), uv_grid


# ---------------------------------------------------------------------------
# 3. Exact 3D Two-Bone Limb IK & Sneaker / Gripping Fist Helpers
# ---------------------------------------------------------------------------

def solve_2bone_ik(root: np.ndarray, target: np.ndarray, l1: float, l2: float, pole_dir: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Exact analytical 3D two-bone IK returning `(mid_joint, clamped_end)`."""
    d_vec = target - root
    dist = float(np.linalg.norm(d_vec))
    max_reach = (l1 + l2) * 0.985
    min_reach = abs(l1 - l2) + 0.02
    clamped_d = np.clip(dist, min_reach, max_reach)
    u_dir = d_vec / max(dist, 1e-6)
    end_pt = root + u_dir * clamped_d

    cos_a = np.clip((l1 * l1 + clamped_d * clamped_d - l2 * l2) / (2.0 * l1 * clamped_d), -1.0, 1.0)
    sin_a = math.sqrt(max(0.0, 1.0 - cos_a * cos_a))

    p_orth = pole_dir - np.dot(pole_dir, u_dir) * u_dir
    if np.linalg.norm(p_orth) < 1e-5:
        p_orth = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    p_orth /= np.linalg.norm(p_orth)

    mid_pt = root + u_dir * (l1 * cos_a) + p_orth * (l1 * sin_a)
    return mid_pt.astype(np.float32), end_pt.astype(np.float32)


def sample_3pt_limb_curve(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, nv: int = 24) -> np.ndarray:
    """Builds a smooth C1 rounded-elbow/knee limb spine through `(p0, p1, p2)`."""
    s = np.linspace(0.0, 1.0, nv, dtype=np.float32)[:, None]
    # Piecewise linear with quadratic corner rounding around s=0.5 (joint p1)
    lin = np.where(s < 0.5, p0 + (p1 - p0) * (s * 2.0), p1 + (p2 - p1) * ((s - 0.5) * 2.0))
    bez = ((1.0 - s) ** 2) * p0 + 2.0 * (1.0 - s) * s * p1 + (s ** 2) * p2
    w_round = np.exp(-((s - 0.5) / 0.18) ** 2)
    return (lin * (1.0 - 0.55 * w_round) + bez * (0.55 * w_round)).astype(np.float32)


def create_sneaker_assembly(name_prefix: str, mat_upper: bpy.types.Material, mat_sole: bpy.types.Material, mat_tread: bpy.types.Material) -> bpy.types.Object:
    """Creates a realistic athletic sneaker (black upper + crisp white rubber midsole + dark waffle tread underneath!).
    Local origin `(0, 0, 0)` is the ANKLE joint; sole touches local `Z = -0.10`, toe points along `-Y`!"""
    grp = bpy.data.objects.new(name_prefix, None)
    bpy.context.scene.collection.objects.link(grp)

    # Sculpted sneaker upper
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=1.0, location=(0.0, -0.045, -0.052))
    up = bpy.context.active_object
    up.name = f"{name_prefix}_Upper"
    up.parent = grp
    # Flatten bottom of shoe upper cleanly at z = -0.082
    for v in up.data.vertices:
        x, y, z = v.co
        # Taper width toward rounded toe (y < 0)
        w_taper = 0.068 * (1.0 - 0.18 * max(0.0, -y))
        z_scaled = max(-0.032, z * 0.048)
        if y < -0.15:
            z_scaled *= 0.78  # sleeker toe box!
        v.co = (x * w_taper, y * 0.132, z_scaled)
    bpy.ops.object.shade_smooth()
    up.data.materials.append(mat_upper)

    # Crisp white rubber midsole slab
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=1.0, depth=0.024, location=(0.0, -0.046, -0.086))
    sole = bpy.context.active_object
    sole.name = f"{name_prefix}_Midsole"
    sole.parent = grp
    sole.scale = (0.071, 0.138, 1.0)
    bpy.ops.object.shade_smooth()
    sole.data.materials.append(mat_sole)

    # Dark rubber tread outsole at very bottom (visible when foot kicks up in 180° Back!)
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=1.0, depth=0.008, location=(0.0, -0.046, -0.100))
    trd = bpy.context.active_object
    trd.name = f"{name_prefix}_Tread"
    trd.parent = grp
    trd.scale = (0.069, 0.135, 1.0)
    bpy.ops.object.shade_smooth()
    trd.data.materials.append(mat_tread)

    # White laces detail across instep
    for i in range(3):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.035 - i * 0.022, -0.016 - i * 0.006))
        lc = bpy.context.active_object
        lc.parent = grp
        lc.scale = (0.046, 0.007, 0.006)
        lc.data.materials.append(mat_sole)

    return grp


def create_gripping_fist(name_prefix: str, mat_skin: bpy.types.Material, is_left: bool = True) -> bpy.types.Object:
    """Creates a sculpted masculine hand with 4 curled fingers + wrapped thumb gripping around local Z axis!"""
    grp = bpy.data.objects.new(name_prefix, None)
    bpy.context.scene.collection.objects.link(grp)
    sgn = 1.0 if is_left else -1.0

    # Broad palm / dorsum wrapping beside the rubber handle (handle sits at local (0, 0, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=12, radius=1.0, location=(sgn * 0.068, 0.022, 0.0))
    palm = bpy.context.active_object
    palm.parent = grp
    palm.scale = (0.032, 0.052, 0.056)
    bpy.ops.object.shade_smooth()
    palm.data.materials.append(mat_skin)

    # 4 curled fingers wrapping tightly around the front (-Y) of the rubber grip collar!
    for fi in range(4):
        fz = 0.036 - fi * 0.024
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.076,
            minor_radius=0.0135,
            major_segments=20,
            minor_segments=10,
            location=(0.0, 0.0, fz),
        )
        fg = bpy.context.active_object
        fg.parent = grp
        # Keep front-outer 220° arc by squashing slightly so fingers hug the rubber shaft snugly!
        fg.scale = (1.02, 1.02, 0.92)
        bpy.ops.object.shade_smooth()
        fg.data.materials.append(mat_skin)

    # Opposable thumb wrapped over the top-side
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=10, radius=1.0, location=(-sgn * 0.035, -0.068, 0.048))
    th = bpy.context.active_object
    th.parent = grp
    th.scale = (0.036, 0.020, 0.018)
    th.rotation_euler = Euler((0.0, 0.0, sgn * 0.45), "XYZ")
    bpy.ops.object.shade_smooth()
    th.data.materials.append(mat_skin)

    return grp


# ---------------------------------------------------------------------------
# 4. Full Rig Assembly & Crazy Pose Evaluators (Idle, 8-Frame Wag-Run, 8-Frame Forehead Bonk!)
# ---------------------------------------------------------------------------

class RubberFingerManiacRig:
    def __init__(self):
        self.img_ooo = bpy.data.images.load(os.path.join(TEX_DIR, "head_ooo.png"), check_existing=True)
        self.img_twist = bpy.data.images.load(os.path.join(TEX_DIR, "head_twist.png"), check_existing=True)
        self.img_maniac = bpy.data.images.load(os.path.join(TEX_DIR, "head_maniac.png"), check_existing=True)

        # Head blends 42% crisp DSLR photo + 58% Principled BSDF so eyes/beard stay razor-sharp without overexposure
        self.mat_head, self.tex_head_node = make_tex_material(
            "MatHead", os.path.join(TEX_DIR, "head_ooo.png"), roughness=0.58, specular=0.28, unlit_mix=0.42
        )
        self.mat_henley, _ = make_tex_material(
            "MatHenley", os.path.join(TEX_DIR, "henley_tex.png"), roughness=0.80, specular=0.16, unlit_mix=0.05
        )
        self.mat_sleeve, _ = make_tex_material(
            "MatHenleySleeve", os.path.join(TEX_DIR, "henley_sleeve_tex.png"), roughness=0.80, specular=0.16, unlit_mix=0.05
        )
        self.mat_jeans, _ = make_tex_material(
            "MatJeans", os.path.join(TEX_DIR, "jeans_tex.png"), roughness=0.84, specular=0.14, unlit_mix=0.04
        )
        self.mat_finger, _ = make_tex_material(
            "MatRubberFinger", os.path.join(TEX_DIR, "rubber_finger_tex.png"),
            roughness=0.38, specular=0.52, unlit_mix=0.0, subsurf=0.28
        )
        self.mat_skin, _ = make_tex_material(
            "MatSkinArm", os.path.join(TEX_DIR, "skin_arm_tex.png"), roughness=0.56, specular=0.30, unlit_mix=0.0
        )
        self.mat_shoe_up = make_solid_material("MatShoeUpper", (0.032, 0.035, 0.042), roughness=0.55)
        self.mat_shoe_sole = make_solid_material("MatShoeSole", (0.78, 0.80, 0.82), roughness=0.45)
        self.mat_shoe_tread = make_solid_material("MatShoeTread", (0.07, 0.07, 0.08), roughness=0.78)

        # Build Rigid / Articulated Body Parts
        self.pelvis = create_pelvis_hips(self.mat_jeans)
        self.torso = create_henley_torso(self.mat_henley)
        self.head = create_sculpted_photo_head(self.mat_head)

        # Smooth Deltoid Shoulder Caps so zero gap ever appears at the armpit/shoulder from 180° Back or 90° Side!
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.078)
        self.deltoid_L = bpy.context.active_object
        self.deltoid_L.name = "DeltoidL"
        bpy.ops.object.shade_smooth()
        self.deltoid_L.data.materials.append(self.mat_sleeve)

        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.078)
        self.deltoid_R = bpy.context.active_object
        self.deltoid_R.name = "DeltoidR"
        bpy.ops.object.shade_smooth()
        self.deltoid_R.data.materials.append(self.mat_sleeve)

        # Limbs: 2 legs (jeans), 2 upper-arm sleeves (placket-free henley), 2 bare muscular forearms (skin), 2 gripping fists, 2 sneakers!
        dummy_line = np.stack([np.zeros(24), np.zeros(24), np.linspace(0, 0.5, 24)], axis=-1).astype(np.float32)
        leg_rad = np.stack([np.linspace(0.088, 0.056, 24), np.linspace(0.094, 0.060, 24)], axis=-1).astype(np.float32)
        lp, luv = build_tube_along_curve(dummy_line, leg_rad, nu=24, v_uv_range=(0.72, 0.02))
        self.leg_L = build_uv_quad_mesh("LegL", lp, luv, self.mat_jeans)
        self.leg_R = build_uv_quad_mesh("LegR", lp, luv, self.mat_jeans)

        slv_line = np.stack([np.zeros(16), np.zeros(16), np.linspace(0, 0.35, 16)], axis=-1).astype(np.float32)
        slv_rad = np.stack([np.linspace(0.074, 0.056, 16), np.linspace(0.074, 0.056, 16)], axis=-1).astype(np.float32)
        sp, suv = build_tube_along_curve(slv_line, slv_rad, nu=20, v_uv_range=(0.95, 0.02))
        self.sleeve_L = build_uv_quad_mesh("SleeveL", sp, suv, self.mat_sleeve)
        self.sleeve_R = build_uv_quad_mesh("SleeveR", sp, suv, self.mat_sleeve)

        arm_line = np.stack([np.zeros(14), np.zeros(14), np.linspace(0, 0.22, 14)], axis=-1).astype(np.float32)
        arm_rad = np.stack([np.linspace(0.053, 0.039, 14), np.linspace(0.053, 0.039, 14)], axis=-1).astype(np.float32)
        ap, auv = build_tube_along_curve(arm_line, arm_rad, nu=20)
        self.forearm_L = build_uv_quad_mesh("ForearmL", ap, auv, self.mat_skin)
        self.forearm_R = build_uv_quad_mesh("ForearmR", ap, auv, self.mat_skin)

        self.fist_L = create_gripping_fist("FistL", self.mat_skin, is_left=True)
        self.fist_R = create_gripping_fist("FistR", self.mat_skin, is_left=False)
        self.shoe_L = create_sneaker_assembly("ShoeL", self.mat_shoe_up, self.mat_shoe_sole, self.mat_shoe_tread)
        self.shoe_R = create_sneaker_assembly("ShoeR", self.mat_shoe_up, self.mat_shoe_sole, self.mat_shoe_tread)

        # Giant Floppy Rubber Index Finger (48 axial stations!)
        f_dummy = np.stack([np.zeros(48), np.zeros(48), np.linspace(0.9, 1.85, 48)], axis=-1).astype(np.float32)
        fg_p, fg_uv = eval_giant_rubber_finger_grid(f_dummy, np.array([0.0, -1.0, 0.0], dtype=np.float32))
        self.rubber_finger = build_uv_quad_mesh("GiantRubberFinger", fg_p, fg_uv, self.mat_finger)

    def set_expression(self, mode: str) -> None:
        if mode == "twist":
            self.tex_head_node.image = self.img_twist
        elif mode == "maniac":
            self.tex_head_node.image = self.img_maniac
        else:
            self.tex_head_node.image = self.img_ooo

    def apply_pose(
        self,
        pelvis_pos: tuple[float, float, float],
        pelvis_rot_deg: tuple[float, float, float],
        torso_lean_deg: tuple[float, float, float],
        head_rot_deg: tuple[float, float, float],
        ank_L: tuple[float, float, float],
        foot_pitch_L: float,
        ank_R: tuple[float, float, float],
        foot_pitch_R: float,
        finger_spine: np.ndarray,
        finger_dorsal_dir: np.ndarray,
        expression: str = "ooo",
    ) -> None:
        self.set_expression(expression)

        # 1. Pelvis & Torso & Oversized Sculpted Head
        p_pos = Vector(pelvis_pos)
        p_eul = Euler([math.radians(a) for a in pelvis_rot_deg], "XYZ")
        self.pelvis.location = p_pos
        self.pelvis.rotation_euler = p_eul

        t_eul = Euler([math.radians(a) for a in torso_lean_deg], "XYZ")
        t_mat = t_eul.to_matrix()
        t_origin = p_pos + Vector((0.0, 0.0, 0.025))
        self.torso.location = t_origin
        self.torso.rotation_euler = t_eul

        neck_world = t_origin + t_mat @ Vector((0.0, -0.01, 0.395))
        h_eul = Euler([math.radians(a) for a in head_rot_deg], "XYZ")
        self.head.location = neck_world
        self.head.rotation_euler = h_eul

        # 2. Legs IK & Sneakers (hips tucked cleanly inside pelvis block!)
        p_mat = p_eul.to_matrix()
        hip_L = np.array(p_pos + p_mat @ Vector((+0.102, 0.0, -0.015)), dtype=np.float32)
        hip_R = np.array(p_pos + p_mat @ Vector((-0.102, 0.0, -0.015)), dtype=np.float32)

        ank_L_np = np.array(ank_L, dtype=np.float32)
        ank_R_np = np.array(ank_R, dtype=np.float32)
        knee_L, end_L = solve_2bone_ik(hip_L, ank_L_np, 0.35, 0.34, np.array([+0.08, -1.0, 0.15], np.float32))
        knee_R, end_R = solve_2bone_ik(hip_R, ank_R_np, 0.35, 0.34, np.array([-0.08, -1.0, 0.15], np.float32))

        leg_rad = np.stack([np.linspace(0.088, 0.055, 24), np.linspace(0.094, 0.059, 24)], axis=-1).astype(np.float32)
        lp_L, _ = build_tube_along_curve(sample_3pt_limb_curve(hip_L, knee_L, end_L, 24), leg_rad, nu=24, v_uv_range=(0.72, 0.02))
        lp_R, _ = build_tube_along_curve(sample_3pt_limb_curve(hip_R, knee_R, end_R, 24), leg_rad, nu=24, v_uv_range=(0.72, 0.02))
        update_mesh_positions(self.leg_L, lp_L)
        update_mesh_positions(self.leg_R, lp_R)

        self.shoe_L.location = Vector(end_L)
        self.shoe_L.rotation_euler = Euler((math.radians(foot_pitch_L), 0.0, math.radians(-6.0)), "XYZ")
        self.shoe_R.location = Vector(end_R)
        self.shoe_R.rotation_euler = Euler((math.radians(foot_pitch_R), 0.0, math.radians(+6.0)), "XYZ")

        # 3. Giant Floppy Rubber Index Finger Mesh Update
        fg_p, _ = eval_giant_rubber_finger_grid(finger_spine, finger_dorsal_dir)
        update_mesh_positions(self.rubber_finger, fg_p)

        # 4. Exact 3D Two-Bone Arm IK + Deltoid Shoulder Caps!
        sh_L = np.array(t_origin + t_mat @ Vector((+0.192, -0.01, 0.365)), dtype=np.float32)
        sh_R = np.array(t_origin + t_mat @ Vector((-0.192, -0.01, 0.365)), dtype=np.float32)
        self.deltoid_L.location = Vector(sh_L.tolist())
        self.deltoid_R.location = Vector(sh_R.tolist())

        grip_R = finger_spine[5].copy()
        grip_L = finger_spine[2].copy()
        tang_base = finger_spine[6] - finger_spine[0]
        tang_base /= max(float(np.linalg.norm(tang_base)), 1e-6)

        wrist_L_target = grip_L + np.array([+0.052, +0.025, 0.0], dtype=np.float32)
        wrist_R_target = grip_R + np.array([-0.052, +0.025, 0.0], dtype=np.float32)

        elb_L, wr_L = solve_2bone_ik(sh_L, wrist_L_target, 0.27, 0.25, np.array([+0.90, +0.25, -0.40], np.float32))
        elb_R, wr_R = solve_2bone_ik(sh_R, wrist_R_target, 0.27, 0.25, np.array([-0.90, +0.25, -0.40], np.float32))

        for sh, elb, wr, slv_obj, fa_obj in (
            (sh_L, elb_L, wr_L, self.sleeve_L, self.forearm_L),
            (sh_R, elb_R, wr_R, self.sleeve_R, self.forearm_R),
        ):
            full_arm = sample_3pt_limb_curve(sh, elb, wr, 24)
            slv_pts = full_arm[:16]
            slv_rad = np.stack([np.linspace(0.074, 0.056, 16), np.linspace(0.074, 0.056, 16)], axis=-1).astype(np.float32)
            sp_g, _ = build_tube_along_curve(slv_pts, slv_rad, nu=20, v_uv_range=(0.95, 0.02))
            update_mesh_positions(slv_obj, sp_g)

            # Bare muscular forearm from inside cuff -> wrist (11..24)
            fa_pts = full_arm[10:]
            fa_rad = np.stack([np.linspace(0.052, 0.038, 14), np.linspace(0.052, 0.038, 14)], axis=-1).astype(np.float32)
            ap_g, _ = build_tube_along_curve(fa_pts, fa_rad, nu=20)
            update_mesh_positions(fa_obj, ap_g)

        # Orient both gripping fists cleanly along the rubber finger base tangent!
        q_base = Vector(tang_base.tolist()).to_track_quat("Z", "Y")
        self.fist_L.location = Vector(grip_L.tolist())
        self.fist_L.rotation_euler = q_base.to_euler()
        self.fist_R.location = Vector(grip_R.tolist())
        self.fist_R.rotation_euler = q_base.to_euler()


def build_whip_finger_spine(
    base_pos: tuple[float, float, float],
    base_tilt_x_deg: float,
    base_tilt_y_deg: float,
    whip_lat_deg: float,
    whip_fwd_deg: float,
    s_harmonic_deg: float = 0.0,
    length: float = 0.90,
    nv: int = 48,
) -> np.ndarray:
    """Integrates a constant-arc-length 48-station 3D rubber finger spine with realistic silicone whip curvature!
    `whip_lat_deg`: lateral X bend (negative = toward -X viewer-left, positive = toward +X viewer-right!)
    `whip_fwd_deg`: forward/back Y bend (positive = toward -Y camera/forward, negative = backward toward +Y/head!)
    """
    pts = np.zeros((nv, 3), dtype=np.float32)
    pts[0] = np.array(base_pos, dtype=np.float32)
    ds = length / float(nv - 1)

    for i in range(1, nv):
        u = i / float(nv - 1)
        # Base rigid collar (u < 0.14) stays firm inside his fists; soft rubber shaft (u > 0.14) bends progressively!
        flex = max(0.0, (u - 0.12) / 0.88) ** 1.35
        ang_lat = math.radians(base_tilt_x_deg + whip_lat_deg * flex + s_harmonic_deg * math.sin(math.pi * 1.65 * flex))
        ang_fwd = math.radians(base_tilt_y_deg + whip_fwd_deg * flex)

        # Spherical tangent vector (0,0,1 is straight up +Z)
        tx = math.sin(ang_lat) * math.cos(ang_fwd)
        ty = -math.sin(ang_fwd) * math.cos(ang_lat)
        tz = math.cos(ang_lat) * math.cos(ang_fwd)
        t_vec = np.array([tx, ty, tz], dtype=np.float32)
        t_vec /= max(float(np.linalg.norm(t_vec)), 1e-6)
        pts[i] = pts[i - 1] + t_vec * ds

    return pts


def pose_idle(rig: RubberFingerManiacRig) -> None:
    """Unhinged Wide-Stance Crazed Idle Pose (clutching the towering wobbly rubber finger clear of his bug-eyed 'OOO' face!)."""
    spine = build_whip_finger_spine(
        base_pos=(-0.20, -0.34, 0.96),
        base_tilt_x_deg=-15.0,
        base_tilt_y_deg=+8.0,
        whip_lat_deg=+28.0,
        whip_fwd_deg=-6.0,
        s_harmonic_deg=-14.0,
        length=1.02,
    )
    rig.apply_pose(
        pelvis_pos=(0.02, 0.0, 0.66),
        pelvis_rot_deg=(3.0, -3.0, 4.0),
        torso_lean_deg=(8.0, +4.0, -4.0),
        head_rot_deg=(-4.0, +9.0, -6.0),
        ank_L=(+0.19, -0.05, 0.10),
        foot_pitch_L=0.0,
        ank_R=(-0.18, +0.06, 0.10),
        foot_pitch_R=0.0,
        finger_spine=spine,
        finger_dorsal_dir=np.array([0.0, -1.0, 0.0], dtype=np.float32),
        expression="ooo",
    )


def pose_wag_run_frame(rig: RubberFingerManiacRig, f: int, n_frames: int = 8) -> None:
    """8-frame unhinged lunatic high-knee sprint + 1.05m Giant Floppy Rubber Finger whipping wildly left & right!
    Uses +pi/8 half-frame phase offset on the lateral wag so it slashes across center BETWEEN frames,
    keeping his crazy bug-eyed face 100% unobstructed on every frame while towering visibly from all 360° angles!"""
    phase = 2.0 * math.pi * f / float(n_frames)
    s1 = math.sin(phase)
    c1 = math.cos(phase)
    s2 = math.sin(2.0 * phase)

    # Half-step phase-shifted wag oscillator (never 0 on f=0..7: ±0.383 and ±0.924!)
    wag_p = phase + math.pi / 8.0
    sw = math.sin(wag_p)
    cw = math.cos(wag_p)

    # High-energy lunatic sprinting crouch & bounce!
    bob_z = 0.68 + 0.060 * math.sin(2.0 * phase - 0.5)
    sway_x = 0.048 * s1

    def leg_target(p_leg: float, side_x: float) -> tuple[tuple[float, float, float], float]:
        stride_y = -0.33 * math.sin(p_leg)
        lift = max(0.0, math.cos(p_leg - 0.50))
        back_kick = max(0.0, -math.sin(p_leg)) ** 1.35
        az = 0.10 + 0.26 * lift + 0.27 * back_kick
        pitch = -30.0 * math.sin(p_leg) + 46.0 * back_kick
        return (side_x + sway_x * 0.45, stride_y, az), pitch

    ank_L, fp_L = leg_target(phase, +0.148)
    ank_R, fp_R = leg_target(phase + math.pi, -0.148)

    torso_lean = (14.5 + 4.0 * s2, -9.5 * sw, -12.0 * c1)
    # Head tilts crazily OPPOSITE the wagging rubber finger so his expression pops dynamically!
    head_rot = (-7.5 + 6.0 * s2, -15.0 * sw, +11.5 * cw)

    if f in (0, 7):
        expr = "ooo"
    elif f in (1, 2, 3):
        expr = "maniac"
    else:
        expr = "twist"

    # Hands pump wide side-to-side & high enough that the 1.04m rubber finger towers above his head from 180° Back too!
    hand_x = 0.22 * sw
    hand_y = -0.34 - 0.04 * cw
    hand_z = bob_z + 0.27 + 0.038 * s2

    # Outward tilt + big rubbery S-curve whip!
    tilt_x = 24.0 * sw
    whip_lat = 62.0 * math.sin(wag_p - 0.44)
    whip_fwd = 24.0 * cw
    s_harm = -30.0 * cw

    spine = build_whip_finger_spine(
        base_pos=(hand_x, hand_y, hand_z),
        base_tilt_x_deg=tilt_x,
        base_tilt_y_deg=12.0 + 8.0 * cw,
        whip_lat_deg=whip_lat,
        whip_fwd_deg=whip_fwd,
        s_harmonic_deg=s_harm,
        length=1.04,
    )

    rig.apply_pose(
        pelvis_pos=(sway_x, 0.0, bob_z),
        pelvis_rot_deg=(5.0, -5.0 * s1, 8.0 * c1),
        torso_lean_deg=torso_lean,
        head_rot_deg=head_rot,
        ank_L=ank_L,
        foot_pitch_L=fp_L,
        ank_R=ank_R,
        foot_pitch_R=fp_R,
        finger_spine=spine,
        finger_dorsal_dir=np.array([0.20 * sw, -1.0, 0.0], dtype=np.float32),
        expression=expr,
    )


def pose_forehead_bonk_frame(rig: RubberFingerManiacRig, f: int) -> None:
    """Signature 8-frame comedy solo recreating Photo 1 -> Photo 2:
      f=0: Upright towering rubber finger + Wide 'OOO' face (Photo 1!)
      f=1,2: Whips hard left w/ Maniac Scream!
      f=3,4: Whips back across in rubbery S-wave!
      f=5,6: *SMACK / BONK!* Flops across his upper brow while keeping his crazy eye & twisted side-mouth visible (Photo 2!!)!
      f=7: Boings back upright!
    """
    specs = [
        # (hand_x, hand_z, tilt_x, whip_lat, whip_fwd, s_harm, head_y, head_z, squat_dz, expr)
        (-0.20, 0.96, -12.0,  +22.0,  -2.0, -10.0,  +6.0,  -4.0,  0.00, "ooo"),     # f=0: Photo 1 upright!
        (-0.23, 0.98, -22.0,  -46.0,  +8.0, +20.0,  -8.0,  +5.0, +0.02, "ooo"),     # f=1: Wind-up wag left
        (-0.25, 0.99, -28.0,  -78.0, +12.0, +28.0, -13.0,  +8.0, +0.03, "maniac"),  # f=2: Peak whip left!
        (-0.16, 0.97,  -4.0,  -24.0,  +6.0, -36.0,  +2.0,  -2.0, +0.01, "maniac"),  # f=3: Whipping right S-curve!
        (-0.15, 0.96,  +4.0,  +44.0, -14.0, -24.0,  +9.0,  -6.0, -0.02, "twist"),   # f=4: Incoming toward forehead!
        (-0.19, 0.98,  +1.0,  +76.0, -25.0,  -8.0, +14.0,  -9.0, -0.04, "twist"),   # f=5: *BONK!* Photo 2 forehead flop!
        (-0.19, 0.97,  -1.0,  +84.0, -27.0, +12.0, +16.0, -11.0, -0.05, "twist"),   # f=6: Heavy rubbery drape across high brow!
        (-0.19, 0.96,  -8.0,  +38.0, -10.0, +18.0,  +8.0,  -5.0, -0.02, "ooo"),     # f=7: Rubber boing rebound!
    ]
    hx, hz, tx, w_lat, w_fwd, sh, hy, h_yaw, sq, expr = specs[f % 8]

    spine = build_whip_finger_spine(
        base_pos=(hx, -0.34, hz + sq),
        base_tilt_x_deg=tx,
        base_tilt_y_deg=6.0,
        whip_lat_deg=w_lat,
        whip_fwd_deg=w_fwd,
        s_harmonic_deg=sh,
        length=1.00,
    )
    rig.apply_pose(
        pelvis_pos=(0.02 * math.sin(f), 0.0, 0.67 + sq),
        pelvis_rot_deg=(3.0, 0.0, 0.0),
        torso_lean_deg=(7.0 - sq * 40.0, hy * 0.35, 0.0),
        head_rot_deg=(-4.0, hy, h_yaw),
        ank_L=(+0.185, -0.04, 0.10),
        foot_pitch_L=0.0,
        ank_R=(-0.185, +0.04, 0.10),
        foot_pitch_R=0.0,
        finger_spine=spine,
        finger_dorsal_dir=np.array([0.0, -1.0, 0.0], dtype=np.float32),
        expression=expr,
    )


def set_camera_dir(d: int) -> None:
    """Rotates CameraRig so `d=0` is 0° Front, `d=2` is 90° Left Side (facing screen-left), `d=4` is 180° Back!"""
    rig_cam = bpy.data.objects["CameraRig"]
    # Wait: Camera starts at (0, -dist, z). Rotating CameraRig by +theta around Z sends (0, -dist) -> (+dist*sin(theta), -dist*cos(theta))!
    # Let's check: R_z(+90°) * (0, -dist) = (-(-dist), 0) = (+dist, 0)! YES!! +45° * d around Z!
    rig_cam.rotation_euler = Euler((0.0, 0.0, math.radians(45.0 * d)), "XYZ")


def render_to(scene: bpy.types.Scene, path: str) -> None:
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main() -> None:
    scene = setup_scene(640, 680)
    rig = RubberFingerManiacRig()

    if TEST_MODE:
        print("=== Rendering 5 diagnostic test frames ===")
        pose_idle(rig)
        set_camera_dir(0)
        render_to(scene, os.path.join(OUT_RAW, "test_idle_d0.png"))

        pose_wag_run_frame(rig, 2, 8)
        set_camera_dir(0)
        render_to(scene, os.path.join(OUT_RAW, "test_run_d0_f2.png"))

        set_camera_dir(2)
        render_to(scene, os.path.join(OUT_RAW, "test_run_d2_f2.png"))

        set_camera_dir(4)
        render_to(scene, os.path.join(OUT_RAW, "test_run_d4_f2.png"))

        pose_forehead_bonk_frame(rig, 5)
        set_camera_dir(0)
        render_to(scene, os.path.join(OUT_RAW, "test_bonk_05.png"))
        print("=== Done diagnostic test frames! ===")
        return

    print("=== 1/3 Rendering 8-Direction Crazed Idle (8 frames) ===")
    pose_idle(rig)
    for d in range(8):
        set_camera_dir(d)
        render_to(scene, os.path.join(OUT_RAW, f"raw_idle_d{d}.png"))

    print("=== 2/3 Rendering 8-Direction x 8-Frame 360° Crazy Wag-Run (64 frames) ===")
    for f in range(8):
        pose_wag_run_frame(rig, f, 8)
        for d in range(8):
            set_camera_dir(d)
            render_to(scene, os.path.join(OUT_RAW, f"raw_run_d{d}_f{f}.png"))

    print("=== 3/3 Rendering 8-Frame 'FOREHEAD BONK!' Signature Solo (8 frames) ===")
    set_camera_dir(0)
    for f in range(8):
        pose_forehead_bonk_frame(rig, f)
        render_to(scene, os.path.join(OUT_RAW, f"raw_bonk_{f:02d}.png"))

    print("=== Completed all 80 3D renders in:", OUT_RAW)


if __name__ == "__main__":
    main()
