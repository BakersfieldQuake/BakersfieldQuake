r"""Blender 5.2 Rigged 3D Character + Stainless-Steel Two-Wheel Contraption Builder
for Green-Suit Wheelman (v2 — Solid Sculpted BMesh Anatomy, Silky Blended Shadow, Electric Chroma-Green Spandex).
"""
from __future__ import annotations

import math
import os
from typing import Dict, Tuple

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(HERE, "tex")


# ---------------------------------------------------------------------------
# 1. Studio Scene, Camera Orbit Rig & High-Contrast Chrome/Spandex World
# ---------------------------------------------------------------------------

def setup_studio_scene(res_w: int = 440, res_h: int = 440, samples: int = 16) -> Tuple[bpy.types.Scene, bpy.types.Object, bpy.types.Object]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = res_w
    sc.render.resolution_y = res_h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"

    for vt in ("AgX", "Standard"):
        try:
            sc.view_settings.view_transform = vt
            break
        except Exception:
            pass
    for lk in ("Medium High Contrast", "None"):
        try:
            sc.view_settings.look = lk
            break
        except Exception:
            pass

    if hasattr(sc, "eevee"):
        for attr, val in (("taa_render_samples", samples), ("use_raytracing", True), ("use_shadows", True)):
            if hasattr(sc.eevee, attr):
                try:
                    setattr(sc.eevee, attr, val)
                except Exception:
                    pass

    # Procedural Studio Softbox Reflection World (gives mirror-polished stainless steel crisp gleaming bands!)
    world = bpy.data.worlds.new("GreenWheelStudio")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    n_out = nt.nodes.new("ShaderNodeOutputWorld")
    n_bg = nt.nodes.new("ShaderNodeBackground")
    n_tc = nt.nodes.new("ShaderNodeTexCoord")
    n_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    n_ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = n_ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (0.16, 0.18, 0.20, 1.0)
    els[1].position = 0.45
    els[1].color = (0.24, 0.26, 0.30, 1.0)
    e2 = n_ramp.color_ramp.elements.new(0.54)
    e2.color = (0.98, 0.99, 1.00, 1.0)
    e3 = n_ramp.color_ramp.elements.new(0.76)
    e3.color = (0.58, 0.62, 0.68, 1.0)
    e4 = n_ramp.color_ramp.elements.new(0.92)
    e4.color = (1.00, 0.99, 0.97, 1.0)
    n_bg.inputs["Strength"].default_value = 0.78
    nt.links.new(n_tc.outputs["Generated"], n_sep.inputs["Vector"])
    nt.links.new(n_sep.outputs["Z"], n_ramp.inputs["Fac"])
    nt.links.new(n_ramp.outputs["Color"], n_bg.inputs["Color"])
    nt.links.new(n_bg.outputs["Background"], n_out.inputs["Surface"])

    cam_rig = bpy.data.objects.new("CameraRig", None)
    sc.collection.objects.link(cam_rig)

    cam_data = bpy.data.cameras.new("SpriteCam")
    cam_data.lens = 56.0
    cam_obj = bpy.data.objects.new("SpriteCam", cam_data)
    sc.collection.objects.link(cam_obj)
    cam_obj.parent = cam_rig
    set_camera_framing(cam_obj, 2.25, 0.62, 0.44)
    sc.camera = cam_obj

    lights = [
        ("KeyLight",   ( 2.1, -2.8, 2.5), 118.0, (1.00, 0.99, 0.96), 1.9),
        ("FillLight",  (-2.5, -2.4, 1.5),  62.0, (0.90, 0.95, 1.00), 2.3),
        ("RimLight",   ( 0.0,  2.7, 2.4),  95.0, (0.95, 1.00, 0.92), 1.8),
        ("GroundFill", ( 0.0, -2.0, 0.18), 32.0, (0.98, 0.98, 0.95), 2.1),
    ]
    for name, loc, energy, col, sz in lights:
        ld = bpy.data.lights.new(name, type="AREA")
        ld.energy = energy
        ld.color = col
        ld.size = sz
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.parent = cam_rig
        lo.location = loc
        lv = Vector((0.0, 0.0, 0.70)) - Vector(loc)
        lo.rotation_euler = lv.to_track_quat("-Z", "Y").to_euler()

    return sc, cam_rig, cam_obj


def set_camera_framing(cam_obj: bpy.types.Object, dist: float = 2.25, cam_z: float = 0.62, target_z: float = 0.44) -> None:
    cam_obj.location = (0.0, -dist, cam_z)
    dvec = Vector((0.0, 0.0, target_z)) - cam_obj.location
    cam_obj.rotation_euler = dvec.to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------------------
# 2. PBR Materials (Electric Chroma-Green Spandex, Unified Hood+Photo Face, Chrome Rig, VFX)
# ---------------------------------------------------------------------------

SUIT_LINEAR_COL = (0.165, 0.840, 0.024, 1.0)
SUIT_EMIT_COL = (0.12, 0.65, 0.018, 1.0)


def build_materials() -> Dict[str, bpy.types.Material]:
    mats: Dict[str, bpy.types.Material] = {}

    # 1) Vibrant Electric Neon-Green Morphsuit Spandex (matches studio reference #84EC3E!)
    m_suit = bpy.data.materials.new("MatGreenSuit")
    m_suit.use_nodes = True
    nt = m_suit.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = SUIT_LINEAR_COL
    bsdf.inputs["Roughness"].default_value = 0.46
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.30
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.36
    if "Sheen Tint" in bsdf.inputs:
        bsdf.inputs["Sheen Tint"].default_value = (0.42, 1.0, 0.16, 1.0)
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = SUIT_EMIT_COL
        bsdf.inputs["Emission Strength"].default_value = 0.09

    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 22.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.09
    bump.inputs["Distance"].default_value = 0.005
    nt.links.new(tc.outputs["Generated"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mats["suit"] = m_suit

    # 2) Unified Head + Stitched Hood Rim + Swappable Real-Photo Face Shader
    m_head = bpy.data.materials.new("MatHeadFace")
    m_head.use_nodes = True
    hnt = m_head.node_tree
    hnt.nodes.clear()
    h_out = hnt.nodes.new("ShaderNodeOutputMaterial")
    h_bsdf = hnt.nodes.new("ShaderNodeBsdfPrincipled")

    uv_node = hnt.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map = "UVFace"
    uv_front = hnt.nodes.new("ShaderNodeUVMap")
    uv_front.uv_map = "UVFrontMask"

    tex_face = hnt.nodes.new("ShaderNodeTexImage")
    tex_face.name = "FaceImageNode"
    tex_face.extension = "CLIP"
    smile_path = os.path.join(TEX_DIR, "face_smile.png")
    if os.path.exists(smile_path):
        tex_face.image = bpy.data.images.load(smile_path, check_existing=True)
    hnt.links.new(uv_node.outputs["UV"], tex_face.inputs["Vector"])

    sep_uv = hnt.nodes.new("ShaderNodeSeparateXYZ")
    hnt.links.new(uv_node.outputs["UV"], sep_uv.inputs["Vector"])

    def math_node(op: str, v0=None, v1=None):
        mn = hnt.nodes.new("ShaderNodeMath")
        mn.operation = op
        if v0 is not None:
            mn.inputs[0].default_value = v0
        if v1 is not None:
            mn.inputs[1].default_value = v1
        return mn

    du = math_node("SUBTRACT", None, 0.5)
    hnt.links.new(sep_uv.outputs["X"], du.inputs[0])
    nu = math_node("DIVIDE", None, 0.258)
    hnt.links.new(du.outputs["Value"], nu.inputs[0])
    u2 = math_node("MULTIPLY")
    hnt.links.new(nu.outputs["Value"], u2.inputs[0])
    hnt.links.new(nu.outputs["Value"], u2.inputs[1])

    dv = math_node("SUBTRACT", None, 0.4765)
    hnt.links.new(sep_uv.outputs["Y"], dv.inputs[0])
    nv = math_node("DIVIDE", None, 0.305)
    hnt.links.new(dv.outputs["Value"], nv.inputs[0])
    v2 = math_node("MULTIPLY")
    hnt.links.new(nv.outputs["Value"], v2.inputs[0])
    hnt.links.new(nv.outputs["Value"], v2.inputs[1])

    r2 = math_node("ADD")
    hnt.links.new(u2.outputs["Value"], r2.inputs[0])
    hnt.links.new(v2.outputs["Value"], r2.inputs[1])
    r_oval = math_node("SQRT")
    hnt.links.new(r2.outputs["Value"], r_oval.inputs[0])

    ramp_in = hnt.nodes.new("ShaderNodeValToRGB")
    ramp_in.color_ramp.elements[0].position = 0.94
    ramp_in.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    ramp_in.color_ramp.elements[1].position = 0.99
    ramp_in.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    hnt.links.new(r_oval.outputs["Value"], ramp_in.inputs["Fac"])

    sep_fm = hnt.nodes.new("ShaderNodeSeparateXYZ")
    hnt.links.new(uv_front.outputs["UV"], sep_fm.inputs["Vector"])
    face_mask = math_node("MULTIPLY")
    hnt.links.new(ramp_in.outputs["Color"], face_mask.inputs[0])
    hnt.links.new(sep_fm.outputs["X"], face_mask.inputs[1])

    hem_ramp = hnt.nodes.new("ShaderNodeValToRGB")
    hem_ramp.color_ramp.interpolation = "B_SPLINE"
    hem_ramp.color_ramp.elements[0].position = 0.93
    hem_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    e_mid = hem_ramp.color_ramp.elements.new(1.00)
    e_mid.color = (1.0, 1.0, 1.0, 1.0)
    hem_ramp.color_ramp.elements[1].position = 1.07
    hem_ramp.color_ramp.elements[1].color = (0.12, 0.12, 0.12, 1.0)
    hnt.links.new(r_oval.outputs["Value"], hem_ramp.inputs["Fac"])

    hem_front = math_node("MULTIPLY")
    hnt.links.new(hem_ramp.outputs["Color"], hem_front.inputs[0])
    hnt.links.new(sep_fm.outputs["X"], hem_front.inputs[1])

    h_bump = hnt.nodes.new("ShaderNodeBump")
    h_bump.inputs["Strength"].default_value = 0.32
    h_bump.inputs["Distance"].default_value = 0.008
    hnt.links.new(hem_front.outputs["Value"], h_bump.inputs["Height"])
    hnt.links.new(h_bump.outputs["Normal"], h_bsdf.inputs["Normal"])

    mix_col = hnt.nodes.new("ShaderNodeMix")
    mix_col.data_type = "RGBA"
    mix_col.inputs["A"].default_value = SUIT_LINEAR_COL
    hnt.links.new(face_mask.outputs["Value"], mix_col.inputs["Factor"])
    hnt.links.new(tex_face.outputs["Color"], mix_col.inputs["B"])
    hnt.links.new(mix_col.outputs["Result"], h_bsdf.inputs["Base Color"])

    mix_rough = hnt.nodes.new("ShaderNodeMix")
    mix_rough.data_type = "FLOAT"
    mix_rough.inputs["A"].default_value = 0.48
    mix_rough.inputs["B"].default_value = 0.62
    hnt.links.new(face_mask.outputs["Value"], mix_rough.inputs["Factor"])
    hnt.links.new(mix_rough.outputs["Result"], h_bsdf.inputs["Roughness"])

    inv_face = math_node("SUBTRACT", 1.0, None)
    hnt.links.new(face_mask.outputs["Value"], inv_face.inputs[1])
    em_mul = math_node("MULTIPLY", None, 0.08)
    hnt.links.new(inv_face.outputs["Value"], em_mul.inputs[0])
    if "Emission Color" in h_bsdf.inputs:
        h_bsdf.inputs["Emission Color"].default_value = SUIT_EMIT_COL
        hnt.links.new(em_mul.outputs["Value"], h_bsdf.inputs["Emission Strength"])

    if "Specular IOR Level" in h_bsdf.inputs:
        h_bsdf.inputs["Specular IOR Level"].default_value = 0.32
    hnt.links.new(h_bsdf.outputs["BSDF"], h_out.inputs["Surface"])
    mats["head"] = m_head

    for fn in ("face_smile.png", "face_scream.png", "face_ooo.png"):
        fp = os.path.join(TEX_DIR, fn)
        if os.path.exists(fp):
            bpy.data.images.load(fp, check_existing=True)

    def simple_pbr(name: str, col: Tuple[float, float, float], metallic: float, roughness: float, emission: Tuple[float, float, float] | None = None, em_str: float = 0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1.0)
        b.inputs["Metallic"].default_value = metallic
        b.inputs["Roughness"].default_value = roughness
        if emission is not None and "Emission Color" in b.inputs:
            b.inputs["Emission Color"].default_value = (*emission, 1.0)
            b.inputs["Emission Strength"].default_value = em_str
        return m

    mats["chrome"] = simple_pbr("MatMirrorStainless", (0.90, 0.92, 0.96), metallic=0.98, roughness=0.08)
    mats["steel"] = simple_pbr("MatBrushedAxle", (0.68, 0.71, 0.76), metallic=0.92, roughness=0.22)
    mats["black_cap"] = simple_pbr("MatBlackEndCap", (0.040, 0.042, 0.048), metallic=0.08, roughness=0.36)
    mats["white_rim"] = simple_pbr("MatWhiteSteelRim", (0.92, 0.94, 0.96), metallic=0.14, roughness=0.24)
    mats["tire"] = simple_pbr("MatBlackTire", (0.030, 0.032, 0.036), metallic=0.0, roughness=0.52)
    mats["spark"] = simple_pbr("MatGoldSpark", (1.0, 0.76, 0.22), metallic=0.0, roughness=0.18, emission=(1.0, 0.62, 0.10), em_str=11.0)
    mats["fire"] = simple_pbr("MatFireBlast", (1.0, 0.36, 0.05), metallic=0.0, roughness=0.3, emission=(1.0, 0.34, 0.04), em_str=12.0)
    mats["plasma_green"] = simple_pbr("MatPlasmaTrail", (0.38, 1.0, 0.25), metallic=0.0, roughness=0.2, emission=(0.32, 1.0, 0.20), em_str=8.5)
    mats["gib_meat"] = simple_pbr("MatQuakeGib", (0.48, 0.03, 0.03), metallic=0.05, roughness=0.32)

    # Silky Smooth Alpha-Blended Contact Drop Shadow (zero stipple/noise!)
    m_shad = bpy.data.materials.new("MatDropShadow")
    m_shad.use_nodes = True
    if hasattr(m_shad, "surface_render_method"):
        m_shad.surface_render_method = "BLENDED"
    elif hasattr(m_shad, "blend_method"):
        m_shad.blend_method = "BLEND"
    snt = m_shad.node_tree
    snt.nodes.clear()
    s_out = snt.nodes.new("ShaderNodeOutputMaterial")
    s_bsdf = snt.nodes.new("ShaderNodeBsdfPrincipled")
    s_bsdf.inputs["Base Color"].default_value = (0.008, 0.010, 0.014, 1.0)
    s_bsdf.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in s_bsdf.inputs:
        s_bsdf.inputs["Specular IOR Level"].default_value = 0.0
    s_uv = snt.nodes.new("ShaderNodeTexCoord")
    s_grad = snt.nodes.new("ShaderNodeTexGradient")
    s_grad.gradient_type = "QUADRATIC_SPHERE"
    s_map = snt.nodes.new("ShaderNodeMapping")
    s_map.inputs["Location"].default_value = (-1.0, -1.0, 0.0)
    s_map.inputs["Scale"].default_value = (2.0, 2.0, 1.0)
    s_mul = snt.nodes.new("ShaderNodeMath")
    s_mul.operation = "MULTIPLY"
    s_mul.inputs[1].default_value = 0.34
    snt.links.new(s_uv.outputs["UV"], s_map.inputs["Vector"])
    snt.links.new(s_map.outputs["Vector"], s_grad.inputs["Vector"])
    snt.links.new(s_grad.outputs["Fac"], s_mul.inputs["Value"])
    snt.links.new(s_mul.outputs["Value"], s_bsdf.inputs["Alpha"])
    snt.links.new(s_bsdf.outputs["BSDF"], s_out.inputs["Surface"])
    mats["shadow"] = m_shad

    return mats


def set_face_expression(mats: Dict[str, bpy.types.Material], expr: str) -> None:
    fname = f"face_{expr}.png"
    img = bpy.data.images.get(fname)
    if img is None:
        fp = os.path.join(TEX_DIR, fname)
        if os.path.exists(fp):
            img = bpy.data.images.load(fp, check_existing=True)
    node = mats["head"].node_tree.nodes.get("FaceImageNode")
    if node is not None and img is not None and node.image != img:
        node.image = img


# ---------------------------------------------------------------------------
# 3. Solid Sculpted BMesh Humanoid Anatomy + Voxel Remesh + Native IK/FK Armature
# ---------------------------------------------------------------------------

def _bm_ellipsoid(bm: bmesh.types.BMesh, c: Tuple[float, float, float], rx: float, ry: float, rz: float, u_seg: int = 20, v_seg: int = 14) -> None:
    m = Matrix.Translation(c) @ Matrix.Diagonal((rx, ry, rz, 1.0))
    bmesh.ops.create_uvsphere(bm, u_segments=u_seg, v_segments=v_seg, radius=1.0, matrix=m)


def _bm_capsule(bm: bmesh.types.BMesh, p0: Vector, p1: Vector, r0: float, r1: float, steps: int = 10, u_seg: int = 16, v_seg: int = 12) -> None:
    """Places dense overlapping solid spheres along [p0..p1] with exact metric radii [r0..r1].
    When passed through Voxel Remesh, produces a 100% seamless, watertight organic limb/torso!"""
    for i in range(steps + 1):
        t = i / max(steps, 1)
        p = p0.lerp(p1, t)
        r = r0 + (r1 - r0) * t
        m = Matrix.Translation(p) @ Matrix.Diagonal((r, r, r, 1.0))
        bmesh.ops.create_uvsphere(bm, u_segments=u_seg, v_segments=v_seg, radius=1.0, matrix=m)


def build_sculpted_head_mesh(sc: bpy.types.Scene, mats: Dict[str, bpy.types.Material]) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=72, v_segments=56, radius=1.0)

    for v in bm.verts:
        nx, ny, nz = v.co.x, v.co.y, v.co.z
        x = nx * 0.102
        y = ny * 0.118
        z = 1.640 + nz * 0.126

        if nz < -0.10:
            jaw_t = min(1.0, (-0.10 - nz) / 0.85)
            x *= (1.0 - 0.22 * jaw_t)
            if ny < 0.0:
                y *= (1.0 - 0.07 * jaw_t)
            else:
                y *= (1.0 - 0.28 * jaw_t)

        ear_env = math.exp(-(((abs(nx) - 0.96) / 0.16) ** 2 + ((ny - 0.08) / 0.22) ** 2 + ((nz + 0.08) / 0.26) ** 2))
        x += math.copysign(0.008 * ear_env, nx)

        if ny < -0.05:
            front_w = min(1.0, (-ny - 0.05) / 0.35)
            ou = x / 0.078
            ov = (z - 1.622) / 0.092
            r_ov = math.hypot(ou, ov)

            if r_ov < 1.15:
                hem = math.exp(-((r_ov - 0.99) / 0.065) ** 2)
                x += math.copysign(0.0032 * hem * front_w, x)
                y -= 0.0038 * hem * front_w

            if r_ov < 0.98:
                in_w = min(1.0, (0.98 - r_ov) / 0.15) * front_w
                nose_z_t = (1.660 - z) / 0.048
                if -0.15 <= nose_z_t <= 1.25:
                    bridge_prof = math.sin(max(0.0, min(1.0, nose_z_t * 0.85)) * math.pi * 0.58)
                    if nose_z_t > 1.0:
                        bridge_prof *= max(0.0, 1.0 - (nose_z_t - 1.0) / 0.25)
                    nose_x_w = math.exp(-((x / (0.014 + 0.006 * max(0.0, nose_z_t))) ** 2))
                    y -= 0.024 * bridge_prof * nose_x_w * in_w

                alar = math.exp(-(((abs(x) - 0.016) / 0.009) ** 2 + ((z - 1.615) / 0.010) ** 2))
                y -= 0.009 * alar * in_w

                brow = math.exp(-(((z - 1.664) / 0.012) ** 2 + ((x / 0.054) ** 4)))
                y -= 0.0065 * brow * in_w
                socket = math.exp(-(((abs(x) - 0.032) / 0.018) ** 2 + ((z - 1.650) / 0.013) ** 2))
                eyeball = math.exp(-(((abs(x) - 0.032) / 0.010) ** 2 + ((z - 1.650) / 0.008) ** 2))
                y += (0.0045 * socket - 0.0055 * eyeball) * in_w

                cheek = math.exp(-(((abs(x) - 0.046) / 0.024) ** 2 + ((z - 1.620) / 0.024) ** 2))
                mustache = math.exp(-(((x / 0.034) ** 2) + ((z - 1.596) / 0.014) ** 2))
                chin = math.exp(-(((x / 0.036) ** 2) + ((z - 1.555) / 0.022) ** 2))
                y -= (0.005 * cheek + 0.006 * mustache + 0.009 * chin) * in_w

        v.co = Vector((x, y, z))

    # Short tucked neck base (Z = 1.548 -> 1.495) that nests cleanly inside the skinned Neck bone!
    neck_rings = 8
    neck_segs = 48
    ring_verts = []
    for ri in range(neck_rings):
        t = ri / (neck_rings - 1)
        z = 1.548 - t * 0.054
        fold = 0.0035 * math.sin(t * math.pi * 3.0)
        rx = 0.064 - 0.004 * t + fold
        ry = 0.068 - 0.004 * t + fold
        cy = 0.008 * (1.0 - t)
        row = []
        for si in range(neck_segs):
            ang = 2.0 * math.pi * si / neck_segs
            row.append(bm.verts.new((rx * math.cos(ang), cy + ry * math.sin(ang), z)))
        ring_verts.append(row)
    for ri in range(neck_rings - 1):
        for si in range(neck_segs):
            ns = (si + 1) % neck_segs
            bm.faces.new((ring_verts[ri][si], ring_verts[ri][ns], ring_verts[ri + 1][ns], ring_verts[ri + 1][si]))

    bm.normal_update()

    uv_face = bm.loops.layers.uv.new("UVFace")
    uv_fmask = bm.loops.layers.uv.new("UVFrontMask")
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co
            u = 0.5 + co.x / 0.248
            v = 0.469 + (co.z - 1.615) * 3.72
            lp[uv_face].uv = (u, v)
            fmask = 1.0 if (co.y < -0.018 and co.z > 1.518) else 0.0
            lp[uv_fmask].uv = (fmask, 0.0)
        f.smooth = True

    mesh = bpy.data.meshes.new("HeadMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("GreenSuitHead", mesh)
    sc.collection.objects.link(obj)
    obj.data.materials.append(mats["head"])
    return obj


def build_character_and_armature(
    sc: bpy.types.Scene, mats: Dict[str, bpy.types.Material]
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object, Dict[str, bpy.types.Object]]:
    """Builds a solid, athletic, 100% connected watertight humanoid mesh in T-pose using exact
    metric BMesh volumes + Voxel Remesh, bound to a native IK/FK Armature!"""

    bm = bmesh.new()

    # 1) Solid Athletic Torso: Pelvis -> Glutes -> Waist -> Abs -> Ribcage -> Pecs -> Lats -> Traps -> Neck
    torso_stack = [
        ((0.0, +0.010, 0.88), 0.162, 0.116, 0.105),  # Pelvis / Hips
        ((0.0, +0.005, 0.96), 0.150, 0.108, 0.095),  # Lower abdomen
        ((0.0,  0.000, 1.05), 0.144, 0.104, 0.100),  # Waist
        ((0.0, -0.004, 1.15), 0.160, 0.114, 0.108),  # Lower ribcage
        ((0.0, -0.006, 1.26), 0.178, 0.124, 0.118),  # Chest / Upper ribcage
        ((0.0, +0.004, 1.36), 0.194, 0.114, 0.092),  # Shoulder girdle
        ((0.0, +0.008, 1.42), 0.135, 0.088, 0.068),  # Trapezius slope
    ]
    for c, rx, ry, rz in torso_stack:
        _bm_ellipsoid(bm, c, rx, ry, rz)

    # Glutes & Pectorals
    for sx in (-1.0, +1.0):
        _bm_ellipsoid(bm, (sx * 0.082, +0.052, 0.88), 0.092, 0.084, 0.092)  # Glutes
        _bm_ellipsoid(bm, (sx * 0.078, -0.062, 1.28), 0.088, 0.062, 0.074)  # Pecs

    # Neck core
    _bm_capsule(bm, Vector((0.0, 0.006, 1.39)), Vector((0.0, 0.004, 1.54)), 0.074, 0.064, steps=6)

    # 2) Arms + Hands + Connected Fingers & Legs + Socked Feet
    for sx in (-1.0, +1.0):
        sh = Vector((sx * 0.195, 0.0, 1.385))
        el = Vector((sx * 0.465, +0.015, 1.385))
        wr = Vector((sx * 0.720, 0.0, 1.385))
        palm = Vector((sx * 0.775, -0.004, 1.385))

        _bm_ellipsoid(bm, tuple(sh), 0.080, 0.072, 0.076)                    # Deltoid cap
        _bm_capsule(bm, sh, el, 0.062, 0.050, steps=12)                      # Upper arm (bicep/tricep)
        _bm_capsule(bm, el, wr, 0.052, 0.038, steps=12)                      # Forearm
        _bm_ellipsoid(bm, tuple(palm), 0.056, 0.048, 0.026)                  # Palm

        # Connected Thumb + Index + 3 Fingers (dense steps & generous radius so Voxel Remesh never pinches!)
        _bm_capsule(bm, Vector((sx * 0.745, -0.028, 1.385)), Vector((sx * 0.805, -0.078, 1.382)), 0.021, 0.016, steps=7)
        _bm_capsule(bm, Vector((sx * 0.795, -0.030, 1.386)), Vector((sx * 0.892, -0.032, 1.386)), 0.018, 0.014, steps=8)
        for fy, flen, fr in ((-0.006, 0.092, 0.018), (0.016, 0.086, 0.017), (0.036, 0.072, 0.016)):
            _bm_capsule(bm, Vector((sx * 0.792, fy, 1.385)), Vector((sx * (0.792 + flen), fy, 1.385)), fr, fr * 0.82, steps=7)

        # Hip -> Thigh -> Knee -> Calf -> Ankle -> Socked Foot
        hip = Vector((sx * 0.110, 0.0, 0.890))
        knee = Vector((sx * 0.112, -0.010, 0.490))
        calf = Vector((sx * 0.113, +0.018, 0.345))
        ank = Vector((sx * 0.115, +0.008, 0.082))
        heel = Vector((sx * 0.115, +0.048, 0.042))
        toe = Vector((sx * 0.115, -0.162, 0.028))

        _bm_capsule(bm, hip, knee, 0.102, 0.070, steps=14)                   # Muscular thigh
        _bm_ellipsoid(bm, (sx * 0.112, -0.022, 0.490), 0.066, 0.066, 0.065)  # Knee / patella
        _bm_capsule(bm, knee, calf, 0.068, 0.070, steps=7)                   # Upper calf
        _bm_capsule(bm, calf, ank, 0.069, 0.046, steps=9)                    # Lower calf -> ankle
        _bm_capsule(bm, ank, heel, 0.048, 0.050, steps=4)                    # Ankle -> heel bridge
        _bm_capsule(bm, heel, toe, 0.050, 0.044, steps=10)                   # Solid green-socked foot!

    raw_mesh = bpy.data.meshes.new("GreenSuitBodyMesh")
    bm.to_mesh(raw_mesh)
    bm.free()

    body_obj = bpy.data.objects.new("GreenSuitBody", raw_mesh)
    sc.collection.objects.link(body_obj)

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = body_obj
    body_obj.select_set(True)
    rem = body_obj.modifiers.new("VoxelRemesh", type="REMESH")
    rem.mode = "VOXEL"
    rem.voxel_size = 0.011
    rem.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=rem.name)

    sm = body_obj.modifiers.new("PreSmooth", type="SMOOTH")
    sm.factor = 0.5
    sm.iterations = 3
    bpy.ops.object.modifier_apply(modifier=sm.name)

    for v in body_obj.data.vertices:
        if v.co.z < 0.002:
            v.co.z = 0.002
    body_obj.data.materials.append(mats["suit"])

    # 3) Build Humanoid Armature
    arm_data = bpy.data.armatures.new("WheelmanArmature")
    arm_obj = bpy.data.objects.new("WheelmanRig", arm_data)
    sc.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def add_bone(name: str, head: Tuple[float, float, float], tail: Tuple[float, float, float], parent_name: str | None = None, connect: bool = False):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.roll = 0.0
        if parent_name is not None:
            b.parent = eb[parent_name]
            b.use_connect = connect
        return b

    add_bone("Root",   (0, 0, 0.0),   (0, -0.20, 0.0))
    add_bone("Pelvis", (0, 0, 0.89),  (0, 0, 1.02),   "Root",   False)
    add_bone("Spine",  (0, 0, 1.02),  (0, 0, 1.22),   "Pelvis", True)
    add_bone("Chest",  (0, 0, 1.22),  (0, 0, 1.41),   "Spine",  True)
    add_bone("Neck",   (0, 0, 1.41),  (0, 0, 1.52),   "Chest",  True)
    add_bone("Head",   (0, 0, 1.52),  (0, 0, 1.76),   "Neck",   True)

    for side, sx in (("R", -1.0), ("L", +1.0)):
        add_bone(f"Clavicle.{side}", (sx * 0.05, 0.0, 1.385),   (sx * 0.195, 0.0, 1.385),    "Chest", False)
        add_bone(f"UpperArm.{side}", (sx * 0.195, 0.0, 1.385),  (sx * 0.465, +0.018, 1.385), f"Clavicle.{side}", True)
        add_bone(f"Forearm.{side}",  (sx * 0.465, +0.018, 1.385),(sx * 0.720, 0.0, 1.385),   f"UpperArm.{side}", True)
        add_bone(f"Hand.{side}",     (sx * 0.720, 0.0, 1.385),  (sx * 0.800, 0.0, 1.385),    f"Forearm.{side}", True)
        add_bone(f"Index.{side}",    (sx * 0.800, -0.030, 1.386),(sx * 0.892, -0.032, 1.386),f"Hand.{side}", False)
        add_bone(f"Fingers.{side}",  (sx * 0.795, +0.014, 1.385),(sx * 0.884, +0.014, 1.385),f"Hand.{side}", False)
        add_bone(f"Thumb.{side}",    (sx * 0.748, -0.028, 1.385),(sx * 0.805, -0.078, 1.382),f"Hand.{side}", False)

        add_bone(f"Thigh.{side}",    (sx * 0.110, 0.0, 0.890),  (sx * 0.112, -0.014, 0.490), "Pelvis", False)
        add_bone(f"Shin.{side}",     (sx * 0.112, -0.014, 0.490),(sx * 0.115, +0.008, 0.082),f"Thigh.{side}", True)
        add_bone(f"Foot.{side}",     (sx * 0.115, +0.008, 0.082),(sx * 0.115, -0.155, 0.028),f"Shin.{side}", True)

    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    body_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    # Preserve volume at bent knees/elbows/hips + corrective smooth!
    arm_mod = next((m for m in body_obj.modifiers if m.type == "ARMATURE"), None)
    if arm_mod is not None:
        arm_mod.use_deform_preserve_volume = True

    cs = body_obj.modifiers.new("CorrectiveSmooth", type="CORRECTIVE_SMOOTH")
    cs.factor = 0.65
    cs.iterations = 8
    cs.smooth_type = "LENGTH_WEIGHTED"

    head_obj = build_sculpted_head_mesh(sc, mats)
    head_obj.parent = arm_obj
    head_obj.parent_type = "BONE"
    head_obj.parent_bone = "Head"
    bpy.context.view_layer.update()
    head_obj.matrix_world = Matrix.Identity(4)

    # 4) Native 2-Bone IK Targets & Symmetric Elbow/Knee Poles!
    ik_ctrl: Dict[str, bpy.types.Object] = {}
    pb = arm_obj.pose.bones
    for b in pb:
        b.rotation_mode = "XYZ"

    for side, sx in (("R", -1.0), ("L", +1.0)):
        t_hand = bpy.data.objects.new(f"IK_Hand_{side}", None)
        t_hand.location = (sx * 0.720, 0.0, 1.385)
        sc.collection.objects.link(t_hand)
        p_arm = bpy.data.objects.new(f"Pole_Arm_{side}", None)
        p_arm.location = (sx * 0.465, +0.55, 1.385)
        sc.collection.objects.link(p_arm)

        c_ik = pb[f"Forearm.{side}"].constraints.new("IK")
        c_ik.name = "ArmIK"
        c_ik.target = t_hand
        c_ik.pole_target = p_arm
        # Both arms bend elbows cleanly toward Pole_Arm (+Y/outward) with -pi/2!
        c_ik.pole_angle = -math.pi * 0.5
        c_ik.chain_count = 2
        c_ik.influence = 1.0

        t_foot = bpy.data.objects.new(f"IK_Foot_{side}", None)
        t_foot.location = (sx * 0.115, +0.008, 0.082)
        sc.collection.objects.link(t_foot)
        p_leg = bpy.data.objects.new(f"Pole_Leg_{side}", None)
        p_leg.location = (sx * 0.115, -0.65, 0.50)
        sc.collection.objects.link(p_leg)

        l_ik = pb[f"Shin.{side}"].constraints.new("IK")
        l_ik.name = "LegIK"
        l_ik.target = t_foot
        l_ik.pole_target = p_leg
        l_ik.pole_angle = -math.pi * 0.5
        l_ik.chain_count = 2
        l_ik.influence = 1.0

        ik_ctrl[f"hand_{side}"] = t_hand
        ik_ctrl[f"pole_arm_{side}"] = p_arm
        ik_ctrl[f"foot_{side}"] = t_foot
        ik_ctrl[f"pole_leg_{side}"] = p_leg

    return arm_obj, body_obj, head_obj, ik_ctrl


# ---------------------------------------------------------------------------
# 4. Authentic 3D Stainless-Steel Two-Wheel Contraption ("The Chrome Rod Rig")
# ---------------------------------------------------------------------------

def build_stainless_wheel_rig(sc: bpy.types.Scene, mats: Dict[str, bpy.types.Material]) -> Dict[str, bpy.types.Object]:
    rig_root = bpy.data.objects.new("WheelRigRoot", None)
    rig_root.rotation_mode = "XYZ"
    rig_root.location = (0.0, -0.18, 0.190)
    sc.collection.objects.link(rig_root)

    def link_smooth(obj: bpy.types.Object, parent: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
        obj.parent = parent
        obj.data.materials.append(mat)
        for p in obj.data.polygons:
            p.use_smooth = True
        return obj

    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.015, depth=0.87, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
    axle = link_smooth(bpy.context.active_object, rig_root, mats["steel"])
    axle.name = "Rig_Axle"

    bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=0.035, depth=0.095, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
    collar = link_smooth(bpy.context.active_object, rig_root, mats["chrome"])
    collar.name = "Rig_CenterCollar"

    rod_pivot = bpy.data.objects.new("RodPivot", None)
    rod_pivot.parent = rig_root
    rod_pivot.rotation_euler = (math.radians(56.0), 0.0, 0.0)
    sc.collection.objects.link(rod_pivot)

    bpy.ops.mesh.primitive_cylinder_add(vertices=44, radius=0.032, depth=0.305, location=(0, 0, -0.1525))
    tube_lo = link_smooth(bpy.context.active_object, rod_pivot, mats["chrome"])
    tube_lo.name = "Rig_RodLower"

    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=0.032, location=(0, 0, -0.305))
    nose = link_smooth(bpy.context.active_object, rod_pivot, mats["chrome"])
    nose.scale = (1.0, 1.0, 1.22)
    nose.name = "Rig_RodBulletTip"

    bpy.ops.mesh.primitive_torus_add(major_segments=40, minor_segments=14, major_radius=0.0335, minor_radius=0.0035, location=(0, 0, 0.025))
    seam_ring = link_smooth(bpy.context.active_object, rod_pivot, mats["steel"])
    seam_ring.name = "Rig_RodSeamRing"

    bpy.ops.mesh.primitive_cylinder_add(vertices=44, radius=0.032, depth=0.205, location=(0, 0, 0.1025))
    tube_hi = link_smooth(bpy.context.active_object, rod_pivot, mats["chrome"])
    tube_hi.name = "Rig_RodUpper"

    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.033, depth=0.028, location=(0, 0, 0.216))
    end_cap = link_smooth(bpy.context.active_object, rod_pivot, mats["black_cap"])
    end_cap.name = "Rig_RodBlackCap"

    wheels: Dict[str, bpy.types.Object] = {}
    for side, sx in (("R", -1.0), ("L", +1.0)):
        wx = sx * 0.375
        w_piv = bpy.data.objects.new(f"WheelPivot_{side}", None)
        w_piv.rotation_mode = "XYZ"
        w_piv.parent = rig_root
        w_piv.location = (wx, 0.0, 0.0)
        sc.collection.objects.link(w_piv)

        # Join all wheel sub-parts into ONE mesh per wheel so GLB export & scene updates are ultra-clean & fast!
        parts = []
        bpy.ops.mesh.primitive_torus_add(
            major_segments=48, minor_segments=24, major_radius=0.132, minor_radius=0.056,
            location=(0, 0, 0), rotation=(0, math.pi / 2, 0),
        )
        tire = bpy.context.active_object
        tire.scale = (0.92, 1.0, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        tire.data.materials.append(mats["tire"])
        parts.append(tire)

        # Flush circumferential tread ribs following the exact torus crown profile!
        for rx_off in (-0.026, -0.013, 0.0, +0.013, +0.026):
            crown_r = 0.132 + math.sqrt(max(0.0004, 0.056 ** 2 - (rx_off / 0.92) ** 2))
            bpy.ops.mesh.primitive_torus_add(
                major_segments=48, minor_segments=10, major_radius=crown_r, minor_radius=0.0038,
                location=(rx_off, 0, 0), rotation=(0, math.pi / 2, 0),
            )
            rb = bpy.context.active_object
            rb.data.materials.append(mats["tire"])
            parts.append(rb)

        for li in range(20):
            ang = 2.0 * math.pi * li / 20.0
            ly = 0.1865 * math.cos(ang)
            lz = 0.1865 * math.sin(ang)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, ly, lz), rotation=(ang, 0.0, 0.0))
            lug = bpy.context.active_object
            lug.scale = (0.016, 0.005, 0.005)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            lug.data.materials.append(mats["tire"])
            parts.append(lug)

        bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.102, depth=0.036, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
        dish = bpy.context.active_object
        dish.data.materials.append(mats["white_rim"])
        parts.append(dish)

        for lip_s in (-1.0, +1.0):
            bpy.ops.mesh.primitive_torus_add(
                major_segments=40, minor_segments=14, major_radius=0.098, minor_radius=0.010,
                location=(lip_s * 0.030, 0, 0), rotation=(0, math.pi / 2, 0),
            )
            lip = bpy.context.active_object
            lip.data.materials.append(mats["white_rim"])
            parts.append(lip)

        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.028, depth=0.082, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
        hub = bpy.context.active_object
        hub.data.materials.append(mats["white_rim"])
        parts.append(hub)

        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.022, depth=0.022, location=(sx * 0.046, 0, 0), rotation=(0, math.pi / 2, 0))
        nut = bpy.context.active_object
        nut.data.materials.append(mats["steel"])
        parts.append(nut)

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12, radius=0.0055, depth=0.024,
            location=(sx * 0.028, 0.068, -0.032), rotation=(0.25, sx * 0.45, 0.0),
        )
        valve = bpy.context.active_object
        valve.data.materials.append(mats["black_cap"])
        parts.append(valve)

        bpy.ops.object.select_all(action="DESELECT")
        for po in parts:
            for poly in po.data.polygons:
                poly.use_smooth = True
            po.select_set(True)
        bpy.context.view_layer.objects.active = tire
        bpy.ops.object.join()
        tire.name = f"WheelMesh_{side}"
        tire.parent = w_piv
        tire.location = (0.0, 0.0, 0.0)
        wheels[side] = w_piv

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, -0.05, 0.001))
    shad = bpy.context.active_object
    shad.name = "GroundDropShadow"
    shad.scale = (1.15, 1.05, 1.0)
    shad.data.materials.append(mats["shadow"])

    return {
        "root": rig_root,
        "rod_pivot": rod_pivot,
        "wheel_R": wheels["R"],
        "wheel_L": wheels["L"],
        "axle": axle,
        "shadow": shad,
    }


def build_vfx_pool(sc: bpy.types.Scene, mats: Dict[str, bpy.types.Material]) -> Dict[str, list[bpy.types.Object]]:
    pool: Dict[str, list[bpy.types.Object]] = {"sparks": [], "flames": [], "trails": [], "gibs": []}

    for i in range(18):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.022, location=(0, 0, -10))
        sp = bpy.context.active_object
        sp.name = f"VFX_Spark_{i}"
        sp.scale = (0.35, 2.8, 0.35)
        sp.data.materials.append(mats["spark"])
        sp.hide_render = True
        pool["sparks"].append(sp)

    for i in range(14):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.095, location=(0, 0, -10))
        fl = bpy.context.active_object
        fl.name = f"VFX_Flame_{i}"
        fl.data.materials.append(mats["fire"] if i % 3 != 0 else mats["spark"])
        for p in fl.data.polygons:
            p.use_smooth = True
        fl.hide_render = True
        pool["flames"].append(fl)

    for i in range(6):
        bpy.ops.mesh.primitive_torus_add(major_segments=36, minor_segments=10, major_radius=0.45, minor_radius=0.014, location=(0, 0, -10))
        tr = bpy.context.active_object
        tr.name = f"VFX_Trail_{i}"
        tr.data.materials.append(mats["plasma_green"] if i % 2 == 0 else mats["spark"])
        for p in tr.data.polygons:
            p.use_smooth = True
        tr.hide_render = True
        pool["trails"].append(tr)

    for i in range(16):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.058, location=(0, 0, -10))
        gb = bpy.context.active_object
        gb.name = f"VFX_Gib_{i}"
        gb.scale = (1.3, 0.85, 0.95)
        gb.data.materials.append(mats["suit"] if i % 3 == 0 else mats["gib_meat"])
        for p in gb.data.polygons:
            p.use_smooth = True
        gb.hide_render = True
        pool["gibs"].append(gb)

    return pool
