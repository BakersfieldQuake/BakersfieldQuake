"""Renders an 8-panel high-resolution Blender 5.2 EEVEE verification contact sheet for the
'CHROME-ROD CONTRAPTION BAZOOKA' (`v_rodcannon.md3`, `p_rodcannon.md3` + Combat+ Ranger, `g_rodcannon.md3`).

Run via:
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python source/mm_tools/rod_cannon/render_rod_previews.py
"""
import math
import os
import struct
import sys
import zipfile
import numpy as np
import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
OUT_ROOT = os.path.join(MM_TOOLS, "out", "rod_cannon")
TEX_DIR = os.path.join(OUT_ROOT, "textures")
STAGE_DIR = os.path.join(OUT_ROOT, "models")
PREV_DIR = os.path.join(OUT_ROOT, "previews")
Q15_PK3 = r"G:\Quake\Combat\quake15\q15.pk3"
PAK_PATHS = (r"G:\Quake\Combat\id1\pak0.pak", r"G:\Quake\QBJ3\id1\pak0.pak")

if MM_TOOLS not in sys.path:
    sys.path.insert(0, MM_TOOLS)
import md3lib

SURF_STYLE = {
    "rod_chrome":   dict(tex="rod_chrome.png", metallic=0.95, rough=0.10, emit=0.0, blend=False),
    "rod_wheel":    dict(tex="rod_wheel.png",  metallic=0.12, rough=0.45, emit=0.0, blend=False),
    "ranger_hands": dict(tex="rod_hand.png",   metallic=0.22, rough=0.52, emit=0.0, blend=False),
    "rod_fx":       dict(tex="rod_fx.png",     metallic=0.00, rough=0.40, emit=3.8, blend=True),
}


def load_ranger_from_pk3(frame_idx=12):
    """Loads Combat+'s `progs/player_vwep.mdl` at `frame_idx` + baked PNG skin so Panel 7 shows the full Ranger holding `p_rodcannon`!"""
    pak_p = next(p for p in PAK_PATHS if os.path.exists(p))
    d_pak = open(pak_p, "rb").read()
    _, ofs, ln = struct.unpack_from("<4sii", d_pak, 0)
    pal = None
    for i in range(ln // 64):
        n, o, s = struct.unpack_from("<56sii", d_pak, ofs + 64 * i)
        if n.split(b"\0")[0].decode("ascii").lower() == "gfx/palette.lmp":
            pal = np.frombuffer(d_pak[o:o + s], dtype=np.uint8).reshape(256, 3)
            break

    with zipfile.ZipFile(Q15_PK3, "r") as z:
        b = z.read("progs/player_vwep.mdl")

    scale = struct.unpack_from("<3f", b, 8)
    origin = struct.unpack_from("<3f", b, 20)
    nsk, sw, sh, nv, nt, nf = struct.unpack_from("<6i", b, 48)
    p = 84
    skin_raw = None
    for k in range(nsk):
        gt = struct.unpack_from("<i", b, p)[0]
        p += 4
        if gt == 0:
            if k == 0:
                skin_raw = b[p:p + sw * sh]
            p += sw * sh
        else:
            nb = struct.unpack_from("<i", b, p)[0]
            p += 4 + 4 * nb
            if k == 0:
                skin_raw = b[p:p + sw * sh]
            p += nb * sw * sh

    skin_idx = np.frombuffer(skin_raw, dtype=np.uint8).reshape(sh, sw)
    skin_rgb = pal[skin_idx].astype(np.float32) / 255.0
    # Blender images are bottom-to-top RGBA float32
    rgba_flip = np.ones((sh, sw, 4), dtype=np.float32)
    rgba_flip[:, :, :3] = skin_rgb[::-1, :, :]
    b_img = bpy.data.images.get("RangerSkinImg")
    if b_img is None:
        b_img = bpy.data.images.new("RangerSkinImg", width=sw, height=sh, alpha=False)
    b_img.pixels.foreach_set(rgba_flip.reshape(-1))
    b_img.pack()

    st_raw = [struct.unpack_from("<3i", b, p + 12 * i) for i in range(nv)]
    p += 12 * nv
    tris_raw = [struct.unpack_from("<4i", b, p + 16 * i) for i in range(nt)]
    p += 16 * nt

    frames_verts = []
    for fi in range(nf):
        ft = struct.unpack_from("<i", b, p)[0]
        p += 4
        if ft == 0:
            p += 24
            fv = [
                (b[p + 4 * i] * scale[0] + origin[0],
                 b[p + 4 * i + 1] * scale[1] + origin[1],
                 b[p + 4 * i + 2] * scale[2] + origin[2])
                for i in range(nv)
            ]
            p += 4 * nv
            frames_verts.append(fv)
        else:
            nb = struct.unpack_from("<i", b, p)[0]
            p += 4 + 8 + 4 * nb
            fv = None
            for sub in range(nb):
                p += 24
                if sub == 0:
                    fv = [
                        (b[p + 4 * i] * scale[0] + origin[0],
                         b[p + 4 * i + 1] * scale[1] + origin[1],
                         b[p + 4 * i + 2] * scale[2] + origin[2])
                        for i in range(nv)
                    ]
                p += 4 * nv
            frames_verts.append(fv)

    fv = frames_verts[min(frame_idx, len(frames_verts) - 1)]
    vmap = {}
    out_v, out_st, out_faces = [], [], []
    for front, i0, i1, i2 in tris_raw:
        tri = []
        for idx in (i0, i1, i2):
            onseam, s_px, t_px = st_raw[idx]
            back = bool(onseam) and (front == 0)
            key = (idx, back)
            if key not in vmap:
                vmap[key] = len(out_v)
                q = fv[idx]
                out_v.append((-q[1], q[0], q[2]))  # Quake -> Blender
                su = (s_px + (sw * 0.5 if back else 0.0) + 0.5) / sw
                tv = 1.0 - (t_px + 0.5) / sh
                out_st.append((su, tv))
            tri.append(vmap[key])
        if tri[0] != tri[1] and tri[1] != tri[2] and tri[0] != tri[2]:
            out_faces.append((tri[0], tri[2], tri[1]))  # MDL CW -> Blender CCW
    return out_v, out_st, out_faces, b_img


def setup_studio_world(scene):
    world = bpy.data.worlds.new("RodStudio")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    n_out = nt.nodes.new("ShaderNodeOutputWorld")
    n_mix = nt.nodes.new("ShaderNodeMixShader")
    n_lp = nt.nodes.new("ShaderNodeLightPath")
    n_bg_refl = nt.nodes.new("ShaderNodeBackground")
    n_bg_cam = nt.nodes.new("ShaderNodeBackground")
    n_tc = nt.nodes.new("ShaderNodeTexCoord")
    n_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    n_ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = n_ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (0.06, 0.075, 0.11, 1.0)
    els[1].position = 0.46
    els[1].color = (0.14, 0.18, 0.25, 1.0)
    e2 = n_ramp.color_ramp.elements.new(0.55)
    e2.color = (0.94, 0.96, 1.00, 1.0)
    e3 = n_ramp.color_ramp.elements.new(0.76)
    e3.color = (0.30, 0.36, 0.46, 1.0)
    e4 = n_ramp.color_ramp.elements.new(0.93)
    e4.color = (0.98, 0.99, 1.00, 1.0)
    n_bg_refl.inputs["Strength"].default_value = 1.15
    n_bg_cam.inputs["Color"].default_value = (0.036, 0.046, 0.072, 1.0)
    n_bg_cam.inputs["Strength"].default_value = 1.00

    nt.links.new(n_tc.outputs["Generated"], n_sep.inputs["Vector"])
    nt.links.new(n_sep.outputs["Z"], n_ramp.inputs["Fac"])
    nt.links.new(n_ramp.outputs["Color"], n_bg_refl.inputs["Color"])
    nt.links.new(n_lp.outputs["Is Camera Ray"], n_mix.inputs["Fac"])
    nt.links.new(n_bg_refl.outputs["Background"], n_mix.inputs[1])
    nt.links.new(n_bg_cam.outputs["Background"], n_mix.inputs[2])
    nt.links.new(n_mix.outputs["Shader"], n_out.inputs["Surface"])


def populate_md3_into_blender(md3_model, frame_idx):
    for s in md3_model["surfaces"]:
        sname = s["name"]
        cfg = SURF_STYLE[sname]
        V_f, N_f = s["frames"][frame_idx]
        b_verts = [(-p[1], p[0], p[2]) for p in V_f]
        b_norms = [(-n[1], n[0], n[2]) for n in N_f]
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
        nt.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
        if cfg["blend"]:
            nt.links.new(bsdf.inputs["Alpha"], tex_node.outputs["Alpha"])
        if cfg["emit"] > 0.0:
            for nm_e in ("Emission Color", "Emission"):
                if nm_e in bsdf.inputs:
                    nt.links.new(bsdf.inputs[nm_e], tex_node.outputs["Color"])
                    break
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = cfg["emit"]

        me.materials.append(mat)
        ob = bpy.data.objects.new(sname, me)
        if cfg["blend"] and hasattr(ob, "visible_shadow"):
            ob.visible_shadow = False
        bpy.context.collection.objects.link(ob)


def add_ranger_mesh_to_blender(frame_idx):
    rv, rst, rfaces, b_img = load_ranger_from_pk3(frame_idx)
    me = bpy.data.meshes.new("RangerBody")
    me.from_pydata(rv, [], rfaces)
    me.validate(verbose=False)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    uv_layer = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uv_layer.data[loop.index].uv = rst[loop.vertex_index]
    mat = bpy.data.materials.new(name="RangerMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.65
    tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tn.image = b_img
    tn.interpolation = "Closest"
    mat.node_tree.links.new(bsdf.inputs["Base Color"], tn.outputs["Color"])
    me.materials.append(mat)
    ob = bpy.data.objects.new("RangerBody", me)
    bpy.context.collection.objects.link(ob)


def main():
    os.makedirs(PREV_DIR, exist_ok=True)
    vm = md3lib.read(os.path.join(STAGE_DIR, "v_rodcannon.md3"))
    pm = md3lib.read(os.path.join(STAGE_DIR, "p_rodcannon.md3"))
    pk = md3lib.read(os.path.join(STAGE_DIR, "g_rodcannon.md3"))

    # Note: 18mm full-frame lens (36mm sensor width) = exact 90.0 deg horizontal FOV in 16:9!
    panels = [
        ("01_pov_idle",      "1 · 1ST-PERSON IDLE (f0) — Wide Chrome Axle, Both White-Rim Cart Tires & Bullet Breech", vm,  0, (0, 0, 0), (24.0, 0.0, 0.0), 18.0, None),
        ("02_pov_swell_max", "2 · FULL CHARGE SWELL (f25) — +56% Chrome Breech Belly Bulge & 3000-RPM Tire Burnout!",  vm, 25, (0, 0, 0), (24.0, 0.0, 0.0), 18.0, None),
        ("03_pov_surge",     "3 · PERISTALTIC GULP SURGE (f26) — +62% Bulge Rockets Forward Past Axle T-Collar!",       vm, 26, (0, 0, 0), (24.0, 0.0, 0.0), 18.0, None),
        ("04_pov_blast",     "4 · PEAK TRUMPET-BELL BLAST (f27) — +68% Flared Black Collar, Starburst & Smoke-Rings!", vm, 27, (0, 0, 0), (24.0, 0.0, 0.0), 18.0, None),
        ("05_pov_wheelie",   "5 · SLAPSTICK WHEELIE KICKBACK (f28) — +24° Muzzle Climb & Barbell Axle Forward Whip!",  vm, 28, (0, 0, 0), (24.0, 0.0, 0.0), 18.0, None),
        ("06_3p_stand",      "6 · 3RD-PERSON RANGER VWEP (`p_rodcannon` Stand f12) — Slung Across Chest Like a Bazooka!", pm, 12, (62.0, -48.0, 26.0), (2.0, -2.0, 8.0), 34.0, 12),
        ("07_3p_blast",      "7 · 3RD-PERSON RANGER FIRING (`p_rodcannon` RockAtt f108) — Flared Mouth & Blast!",       pm, 108, (66.0, +42.0, 22.0), (4.0, -3.0, 10.0), 34.0, 108),
        ("08_pickup_tilt",   "8 · WORLD PICKUP (`g_rodcannon`) — Exact Video Object Tilted at 34° Cannon Elevation!",   pk,  0, (28.0, -54.0, 18.0), (-1.5, 0.0, 14.5), 34.0, None),
    ]

    eevee_id = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    ] else "BLENDER_EEVEE"

    rendered_imgs = []
    for tag, label, mdl, fidx, cam_q, tgt_q, lens_mm, ranger_f in panels:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.render.engine = eevee_id
        scene.render.resolution_x = 880
        scene.render.resolution_y = 520
        scene.render.film_transparent = False
        setup_studio_world(scene)

        populate_md3_into_blender(mdl, fidx)
        if ranger_f is not None:
            add_ranger_mesh_to_blender(ranger_f)

        for nm, from_q, to_q, col_l, eng, cast_sh in (
            ("SunKey",   (12.0, +24.0, 32.0), (16.0, -3.0, -4.0), (1.00, 0.98, 0.95), 3.4, True),
            ("SunFront", (-6.0, -14.0, 14.0), (20.0, -2.0, -4.0), (0.90, 0.95, 1.00), 2.1, False),
            ("SunRim",   (44.0, -22.0, 24.0), (14.0,  0.0,  0.0), (0.80, 0.90, 1.00), 2.3, False),
        ):
            ld = bpy.data.lights.new(nm, type="SUN")
            ld.color = col_l
            ld.energy = eng
            ld.use_shadow = cast_sh
            lo = bpy.data.objects.new(nm, ld)
            p_from = mathutils.Vector((-from_q[1], from_q[0], from_q[2]))
            p_to = mathutils.Vector((-tgt_q[1], tgt_q[0], tgt_q[2]))
            lo.location = p_from
            lo.rotation_euler = (p_to - p_from).to_track_quat("-Z", "Y").to_euler()
            bpy.context.collection.objects.link(lo)

        cam_d = bpy.data.cameras.new("Cam")
        cam_d.lens = lens_mm
        cam_d.sensor_width = 36.0
        cam_d.clip_start = 0.25
        cam_d.clip_end = 600.0
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
