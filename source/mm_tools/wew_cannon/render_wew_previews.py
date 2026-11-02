"""Renders an 8-panel high-resolution Blender 5.2 EEVEE verification contact sheet of `v_wewcannon.md3` & `g_wewcannon.md3`
(projectile excluded — separate entity model in Quake), showcasing the Windows 98 CRT monitor on top of the WEW CANNON
browsing `goodwebsites.html`, `zxc.cc`, `biblefirst.com`, and `wxcs.com/rob` across the 48-frame bending & shooting cycle.

Run via:
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python source/mm_tools/wew_cannon/render_wew_previews.py
"""
import math
import os
import sys
import numpy as np
import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
OUT_ROOT = os.path.join(MM_TOOLS, "out", "wew_cannon")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
STAGE_DIR = os.path.join(OUT_ROOT, "models")
PREV_DIR = os.path.join(OUT_ROOT, "previews")

if MM_TOOLS not in sys.path:
    sys.path.insert(0, MM_TOOLS)
import md3lib


SURF_STYLE = {
    "cannon_silver": dict(tex="wew_silver.png", metallic=0.88, rough=0.18, emit=0.0,  blend=False, crt=False),
    "ranger_hands":  dict(tex="wew_hand.png",   metallic=0.20, rough=0.50, emit=0.0,  blend=False, crt=False),
    "cannon_core":   dict(tex="wew_core.png",   metallic=0.25, rough=0.22, emit=2.4,  blend=False, crt=False),
    "crt_screen":    dict(tex="wew_crt_00.png", metallic=0.02, rough=0.22, emit=1.15, blend=False, crt=True),
    "cannon_fx":     dict(tex="wew_fx.png",     metallic=0.00, rough=0.40, emit=3.6,  blend=True,  crt=False),
}


def populate_scene_from_md3(md3_model, frame_idx, crt_tex="wew_crt_00.png"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for s in md3_model["surfaces"]:
        sname = s["name"]
        cfg = SURF_STYLE[sname].copy()
        if sname == "crt_screen":
            cfg["tex"] = crt_tex
        V_f, N_f = s["frames"][frame_idx]
        # Quake (+X fwd, +Y left, +Z up) -> Blender (+X right = -Y_q, +Y fwd = +X_q, +Z up = +Z_q)
        b_verts = [(-p[1], p[0], p[2]) for p in V_f]
        b_norms = [(-n[1], n[0], n[2]) for n in N_f]
        # Flip MD3 CW-outward -> Blender CCW-outward!
        b_faces = []
        seen = set()
        for a, b, c in s["tris"]:
            fa, fb, fc = a, c, b
            if fa == fb or fb == fc or fa == fc:
                continue
            key = tuple(sorted((fa, fb, fc)))
            if key in seen:
                continue
            pa, pb, pc = np.array(b_verts[fa]), np.array(b_verts[fb]), np.array(b_verts[fc])
            if np.linalg.norm(np.cross(pb - pa, pc - pa)) > 1e-5:
                seen.add(key)
                b_faces.append((fa, fb, fc))
        if not b_faces:
            continue

        me = bpy.data.meshes.new(sname)
        me.from_pydata(b_verts, [], b_faces)
        me.validate(verbose=False)
        me.update()
        for poly in me.polygons:
            poly.use_smooth = True
        me.normals_split_custom_set_from_vertices(b_norms)

        uv_layer = me.uv_layers.new(name="UVMap")
        st = s["st"]
        for loop in me.loops:
            u, v = st[loop.vertex_index]
            uv_layer.data[loop.index].uv = (u, 1.0 - v)

        mat = bpy.data.materials.new(name=sname + "_mat")
        mat.use_nodes = True
        mat.use_backface_culling = False
        if cfg["blend"]:
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "BLENDED"
            if hasattr(mat, "blend_method"):
                mat.blend_method = "BLEND"

        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        bsdf.inputs["Metallic"].default_value = cfg["metallic"]
        bsdf.inputs["Roughness"].default_value = cfg["rough"]
        tex_node = nt.nodes.new("ShaderNodeTexImage")
        tex_node.image = bpy.data.images.load(os.path.join(TEX_DIR, cfg["tex"]), check_existing=True)
        if cfg.get("crt"):
            tex_node.interpolation = "Closest"
            bsdf.inputs["Base Color"].default_value = (0.015, 0.018, 0.024, 1.0)
        else:
            nt.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
        if cfg["blend"]:
            nt.links.new(bsdf.inputs["Alpha"], tex_node.outputs["Alpha"])
        if cfg["emit"] > 0.0:
            if "Emission Color" in bsdf.inputs:
                nt.links.new(bsdf.inputs["Emission Color"], tex_node.outputs["Color"])
            elif "Emission" in bsdf.inputs:
                nt.links.new(bsdf.inputs["Emission"], tex_node.outputs["Color"])
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = cfg["emit"]

        me.materials.append(mat)
        ob = bpy.data.objects.new(sname, me)
        if cfg["blend"] and hasattr(ob, "visible_shadow"):
            ob.visible_shadow = False
        bpy.context.collection.objects.link(ob)


def main():
    os.makedirs(PREV_DIR, exist_ok=True)
    vm = md3lib.read(os.path.join(STAGE_DIR, "v_wewcannon.md3"))
    pk = md3lib.read(os.path.join(STAGE_DIR, "g_wewcannon.md3"))

    panels = [
        ("01_pov_idle",        "1 · MILITARY IDLE (f0) — WEW-TAC 98: goodwebsites.html",   vm,  0, (0, 0, 0), (24.0, -1.2, -1.5), 16.5, "wew_crt_00.png"),
        ("02_pov_charge_mid",  "2 · SEAR COCKING 50% (f20) — WEW-TAC 98: zxc.cc",          vm, 20, (0, 0, 0), (24.0, -1.2, -1.5), 16.5, "wew_crt_04.png"),
        ("03_pov_charge_max",  "3 · FULL CHARGE (+5.5° Steel Flex, f25) — biblefirst.com", vm, 25, (0, 0, 0), (24.0, -1.2, -1.5), 16.5, "wew_crt_10.png"),
        ("04_pov_ignition",    "4 · MUZZLE-BRAKE IGNITION (f26) — wxcs.com/rob",           vm, 26, (0, 0, 0), (24.0, -1.2, -1.5), 16.5, "wew_crt_12.png"),
        ("05_pov_blast",       "5 · TWIN SIDE-BRAKE JETS & AXIAL RECOIL (f27)",            vm, 27, (0, 0, 0), (24.0, -1.2, -1.5), 16.5, "wew_crt_14.png"),
        ("06_pov_full_stroke", "6 · FULL -6.3u BARREL RECOIL & SHOCK-RINGS (f28)",         vm, 28, (0, 0, 0), (24.0, -1.2, -1.5), 16.5, "wew_crt_05.png"),
        ("07_pov_recuperate",  "7 · HYDROPNEUMATIC RETURN-TO-BATTERY (f31)",               vm, 31, (0, 0, 0), (24.0, -1.2, -1.5), 16.5, "wew_crt_11.png"),
        ("08_exterior_orbit",  "8 · MILITARY ORDNANCE PICKUP (`g_wewcannon`)",             pk,  0, (24.0, -35.0, 19.0), (1.0, 0.0, 11.5), 33.0, "wew_crt_00.png"),
    ]

    eevee_id = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    ] else "BLENDER_EEVEE"

    rendered_imgs = []
    for tag, label, mdl, fidx, cam_q, tgt_q, lens_mm, crt_tex in panels:
        populate_scene_from_md3(mdl, fidx, crt_tex=crt_tex)
        scene = bpy.context.scene
        scene.render.engine = eevee_id
        scene.render.resolution_x = 800
        scene.render.resolution_y = 500
        scene.world = bpy.data.worlds.new("World")
        scene.world.use_nodes = True
        bg = scene.world.node_tree.nodes.get("Background")
        bg.inputs["Color"].default_value = (0.055, 0.068, 0.105, 1.0)
        bg.inputs["Strength"].default_value = 1.35

        for nm, from_q, to_q, col_l, eng in (
            ("SunKey",   (4.0,  +18.0, 22.0), (18.0, -5.0, -3.0), (1.00, 0.98, 0.95), 3.6),
            ("SunFront", (-2.0,  +6.0,  4.0), (18.0, -6.0, -4.0), (0.92, 0.96, 1.00), 2.1),
            ("SunRim",   (32.0, -18.0, 16.0), (14.0, -4.0, -2.0), (0.75, 0.88, 1.00), 2.4),
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
        cam_d.clip_end = 500.0
        cam_o = bpy.data.objects.new("Cam", cam_d)
        bpy.context.collection.objects.link(cam_o)
        scene.camera = cam_o

        c_pos = mathutils.Vector((-cam_q[1], cam_q[0], cam_q[2]))
        t_pos = mathutils.Vector((-tgt_q[1], tgt_q[0], tgt_q[2]))
        cam_o.location = c_pos
        cam_o.rotation_euler = (t_pos - c_pos).to_track_quat("-Z", "Y").to_euler()

        out_p = os.path.join(PREV_DIR, f"{tag}.png")
        scene.render.filepath = out_p
        bpy.ops.render.render(write_still=True)
        rendered_imgs.append((label, out_p))

    print(f"[RENDERS OK] Rendered {len(rendered_imgs)} panels in {PREV_DIR}")


if __name__ == "__main__":
    main()
