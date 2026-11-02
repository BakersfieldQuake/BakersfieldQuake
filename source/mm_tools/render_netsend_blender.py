"""Headless Blender 5.2 renderer & contact-sheet builder for the "WHERE'S THE DISK?" MD3 models.

Usage:
  1. Run inside Blender 5.2 to render individual PNG views & save .blend scenes:
       "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P source/mm_tools/render_netsend_blender.py
  2. Run with python3.13 --composite to assemble labeled turntables & animation contact sheets:
       python3.13 source/mm_tools/render_netsend_blender.py --composite
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS_DIR = os.path.join(MOD_DIR, "progs")
OUT_DIR = os.path.join(HERE, "out", "netsend_renders")

if HERE not in sys.path:
    sys.path.insert(0, HERE)


def run_blender_renders():
    import bpy
    import md3lib

    os.makedirs(OUT_DIR, exist_ok=True)

    def make_material(name, tex_png, emission_strength=0.0, boost_diffuse=2.25, additive=False):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        if hasattr(mat, "use_backface_culling"):
            mat.use_backface_culling = False
        nt = mat.node_tree
        nt.nodes.clear()

        out_n = nt.nodes.new("ShaderNodeOutputMaterial")
        out_n.location = (620, 0)

        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.location = (-360, 0)
        img_path = os.path.join(PROGS_DIR, tex_png)
        tex_n.image = bpy.data.images.load(img_path, check_existing=True)

        if additive:
            # Additive electric arc shader: black -> transparent, bright blue-white -> emission
            if hasattr(mat, "blend_method"):
                mat.blend_method = "BLEND"
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "BLENDED"
            add_sh = nt.nodes.new("ShaderNodeAddShader")
            add_sh.location = (420, 0)
            trans_n = nt.nodes.new("ShaderNodeBsdfTransparent")
            trans_n.location = (180, -120)
            emis_n = nt.nodes.new("ShaderNodeEmission")
            emis_n.location = (180, 100)
            emis_n.inputs["Strength"].default_value = 3.2
            nt.links.new(tex_n.outputs["Color"], emis_n.inputs["Color"])
            nt.links.new(emis_n.outputs["Emission"], add_sh.inputs[0])
            nt.links.new(trans_n.outputs["BSDF"], add_sh.inputs[1])
            nt.links.new(add_sh.outputs["Shader"], out_n.inputs["Surface"])
            return mat

        if emission_strength > 0.0:
            emis_n = nt.nodes.new("ShaderNodeEmission")
            emis_n.location = (220, 0)
            emis_n.inputs["Strength"].default_value = emission_strength
            nt.links.new(tex_n.outputs["Color"], emis_n.inputs["Color"])
            nt.links.new(emis_n.outputs["Emission"], out_n.inputs["Surface"])
            return mat

        # Lit diffuse material: compensate for DarkPlaces 0.42x pre-dimmed textures so Blender matches in-game 2.5x look
        mul_n = nt.nodes.new("ShaderNodeVectorMath")
        mul_n.operation = "SCALE"
        mul_n.inputs["Scale"].default_value = boost_diffuse
        mul_n.location = (-60, 0)

        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (220, 0)
        bsdf.inputs["Roughness"].default_value = 0.58
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.35

        nt.links.new(tex_n.outputs["Color"], mul_n.inputs[0])
        nt.links.new(mul_n.outputs["Vector"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs["BSDF"], out_n.inputs["Surface"])
        return mat

    def import_md3_to_scene(md3_filename, mat_map, prefix=""):
        m = md3lib.read(os.path.join(PROGS_DIR, md3_filename))
        objs = []
        for s in m["surfaces"]:
            sname = prefix + s["name"]
            verts0, norms0 = s["frames"][0]
            mesh = bpy.data.meshes.new(sname)
            # Note: MD3 triangle winding in Quake vs Blender normals — load vertices & faces directly
            mesh.from_pydata(verts0, [], s["tris"])
            mesh.update()

            uv_layer = mesh.uv_layers.new(name="UVMap")
            st = s["st"]
            for poly in mesh.polygons:
                poly.use_smooth = True
                for li in poly.loop_indices:
                    vi = mesh.loops[li].vertex_index
                    u, v = st[vi]
                    uv_layer.data[li].uv = (u, 1.0 - v)

            ob = bpy.data.objects.new(sname, mesh)
            bpy.context.scene.collection.objects.link(ob)

            mat = mat_map.get(s["name"])
            if mat is not None:
                mesh.materials.append(mat)

            # Add shape keys for every vertex frame so we can switch frames cleanly & save animated .blend
            ob.shape_key_add(name="Basis", from_mix=False)
            for fi, (vv, _) in enumerate(s["frames"]):
                sk = ob.shape_key_add(name=f"frame_{fi:02d}", from_mix=False)
                for vi, co in enumerate(vv):
                    sk.data[vi].co = co
                sk.value = 0.0

            objs.append(ob)
        return objs

    def set_md3_frame(objs, frame_idx):
        target = f"frame_{frame_idx:02d}"
        for ob in objs:
            if not ob.data.shape_keys:
                continue
            for kb in ob.data.shape_keys.key_blocks:
                if kb.name == "Basis":
                    continue
                kb.value = 1.0 if kb.name == target else 0.0

    def setup_eevee_and_world(res_x, res_y, bg_rgb=(0.055, 0.062, 0.075)):
        sc = bpy.context.scene
        engines = {"BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"}
        avail = {e.identifier for e in sc.render.bl_rna.properties["engine"].enum_items}
        sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in avail else ("BLENDER_EEVEE" if "BLENDER_EEVEE" in avail else "CYCLES")
        sc.render.resolution_x = res_x
        sc.render.resolution_y = res_y
        sc.render.film_transparent = False

        world = bpy.data.worlds.new("PreviewWorld")
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (*bg_rgb, 1.0)
            bg.inputs[1].default_value = 1.15
        sc.world = world
        return sc

    def add_three_point_lights(center, dist):
        specs = [
            ("KeyLight",   (center[0] + dist * 0.85, center[1] - dist * 0.70, center[2] + dist * 0.75), 1400.0 * (dist / 25.0) ** 2, (1.0, 0.97, 0.92)),
            ("FillLight",  (center[0] + dist * 0.60, center[1] + dist * 0.85, center[2] + dist * 0.45),  850.0 * (dist / 25.0) ** 2, (0.88, 0.94, 1.0)),
            ("BackLight1", (center[0] - dist * 0.85, center[1] + dist * 0.55, center[2] + dist * 0.65),  950.0 * (dist / 25.0) ** 2, (0.94, 0.97, 1.0)),
            ("BackLight2", (center[0] - dist * 0.80, center[1] - dist * 0.60, center[2] + dist * 0.50),  800.0 * (dist / 25.0) ** 2, (0.98, 0.95, 0.90)),
        ]
        for nm, loc, pwr, col in specs:
            ld = bpy.data.lights.new(nm, type="POINT")
            ld.energy = pwr
            ld.color = col
            ld.shadow_soft_size = dist * 0.18
            lo = bpy.data.objects.new(nm, ld)
            lo.location = loc
            bpy.context.scene.collection.objects.link(lo)

    def aim_camera(cam_obj, eye, target):
        import mathutils
        cam_obj.location = eye
        direction = mathutils.Vector(target) - mathutils.Vector(eye)
        rot_quat = direction.to_track_quat("-Z", "Y")
        cam_obj.rotation_euler = rot_quat.to_euler()

    # ==========================================================================
    # SCENE 1: VIEWMODEL (progs/v_netsend.md3)
    # ==========================================================================
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = setup_eevee_and_world(960, 540, bg_rgb=(0.06, 0.068, 0.082))

    mat_disk = make_material("m_disk", "netsend_disk.png", boost_diffuse=2.25)
    mat_hand = make_material("m_hand", "netsend_hand.png", boost_diffuse=2.25)
    vm_objs = import_md3_to_scene("v_netsend.md3", {"netsend_disk": mat_disk, "netsend_hand": mat_hand})
    add_three_point_lights((15.5, -8.5, -3.5), 22.0)

    # First-person Quake player eye camera at (0, 0, 0) looking +X (90 deg H-FOV -> ~59 deg V-FOV at 16:9)
    cam_fp = bpy.data.objects.new("CamFP", bpy.data.cameras.new("CamFP"))
    sc.collection.objects.link(cam_fp)
    aim_camera(cam_fp, (0.0, 0.0, 0.0), (20.0, 0.0, 0.0))
    cam_fp.data.sensor_fit = "HORIZONTAL"
    cam_fp.data.angle = math.radians(90.0)
    cam_fp.data.clip_start = 0.5

    # Small crosshair reticle at (+30, 0, 0)
    emis_ret = bpy.data.materials.new("RetMat")
    emis_ret.use_nodes = True
    emis_ret.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.25, 0.2, 1.0)
    emis_ret.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(30.0, 0.0, 0.0))
    ret_ob = bpy.context.active_object
    ret_ob.data.materials.append(emis_ret)

    # Save v_netsend.blend
    set_md3_frame(vm_objs, 0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "v_netsend_preview.blend"))

    # Render 12 key frames from 1st-person view
    sc.camera = cam_fp
    vm_key_frames = [0, 10, 15, 20, 28, 39, 42, 43, 44, 50, 54, 57]
    for fr in vm_key_frames:
        set_md3_frame(vm_objs, fr)
        sc.render.resolution_x, sc.render.resolution_y = 640, 360
        sc.render.filepath = os.path.join(OUT_DIR, f"vm_fp_{fr:02d}.png")
        bpy.ops.render.render(write_still=True)

    # High-res 1280x720 FP renders for frame 0 (LOL.BAT) and frame 15 (flipped back shutter)
    for fr in (0, 15):
        set_md3_frame(vm_objs, fr)
        sc.render.resolution_x, sc.render.resolution_y = 1280, 720
        sc.render.filepath = os.path.join(OUT_DIR, f"vm_hires_fp_{fr:02d}.png")
        bpy.ops.render.render(write_still=True)

    # Hide reticle and render 8-angle turntable around disk+hand center (14.2, -13.5, -6.2) at frame 0
    ret_ob.hide_render = True
    set_md3_frame(vm_objs, 0)
    cam_tt = bpy.data.objects.new("CamTT", bpy.data.cameras.new("CamTT"))
    sc.collection.objects.link(cam_tt)
    cam_tt.data.angle = math.radians(46.0)
    sc.camera = cam_tt
    sc.render.resolution_x, sc.render.resolution_y = 560, 560
    vm_center = (15.8, -8.6, -3.6)
    for ai in range(8):
        ang = math.radians(180.0 + ai * 45.0)  # ai=0 looks from eye side (-X) toward +X
        ex = vm_center[0] + 19.5 * math.cos(ang)
        ey = vm_center[1] + 19.5 * math.sin(ang)
        ez = vm_center[2] + 3.5
        aim_camera(cam_tt, (ex, ey, ez), vm_center)
        sc.render.filepath = os.path.join(OUT_DIR, f"vm_turn_{ai:02d}.png")
        bpy.ops.render.render(write_still=True)

    # ==========================================================================
    # SCENE 2: WORLD DEPLOYABLE PC + ARCS + STUCK DISK
    # ==========================================================================
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = setup_eevee_and_world(640, 640, bg_rgb=(0.055, 0.060, 0.072))

    # Subtle reference floor disc (radius 16 = 32-unit footprint diameter!) + outer checkerboard floor
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=16.0, depth=0.2, location=(0.0, 0.0, -0.11))
    fp_disc = bpy.context.active_object
    m_floor = bpy.data.materials.new("FloorDisc")
    m_floor.use_nodes = True
    m_floor.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.14, 0.17, 1.0)
    m_floor.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    fp_disc.data.materials.append(m_floor)

    mat_pc_body = make_material("m_pc_body", "netsend_pc_body.png", boost_diffuse=2.25)
    mat_pc_disk = make_material("m_pc_disk", "netsend_disk.png", boost_diffuse=2.25)
    mat_pc_leds = make_material("m_pc_leds", "netsend_leds.png", emission_strength=1.5)
    mat_arc     = make_material("m_arc",     "netsend_arc.png",  additive=True)

    scr_mats = {
        "off":   make_material("s_off",   "netsend_s_off.png",  emission_strength=1.0),
        "noise": make_material("s_noise", "netsend_s_n1.png",   emission_strength=1.45),
        "init":  make_material("s_init",  "netsend_s_init0.png", emission_strength=1.55),
        "cmd":   make_material("s_cmd",   "netsend_s_lol0.png",  emission_strength=1.55),
        "send":  make_material("s_send",  "netsend_s_fst0.png",  emission_strength=1.55),
        "loopA": make_material("s_loopA", "netsend_s_l06.png",  emission_strength=1.55),
        "loopB": make_material("s_loopB", "netsend_s_l11.png",  emission_strength=1.55),
        "dot":   make_material("s_dot",   "netsend_s_dot1.png", emission_strength=1.60),
    }

    pc_objs = import_md3_to_scene("netsend_pc.md3", {
        "netsend_pc_body": mat_pc_body,
        "netsend_disk":    mat_pc_disk,
        "netsend_screen":  scr_mats["loopB"],
        "netsend_leds":    mat_pc_leds,
    }, prefix="pc_")
    arc_objs = import_md3_to_scene("netsend_arc.md3", {"netsend_arc": mat_arc}, prefix="arc_")
    dsk_objs = import_md3_to_scene("netsend_disk.md3", {"netsend_disk": mat_pc_disk}, prefix="solo_")

    scr_obj = [o for o in pc_objs if o.name == "pc_netsend_screen"][0]

    add_three_point_lights((0.0, 0.0, 32.0), 82.0)

    cam_pc = bpy.data.objects.new("CamPC", bpy.data.cameras.new("CamPC"))
    sc.collection.objects.link(cam_pc)
    cam_pc.data.angle = math.radians(48.0)
    sc.camera = cam_pc

    # Hide solo disk while saving & rendering PC turntable
    for o in dsk_objs:
        o.hide_render = True
    set_md3_frame(pc_objs, 24)
    set_md3_frame(arc_objs, 2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "netsend_pc_preview.blend"))

    # 1. 8-angle turntable of active PC + crackling electric arcs around (0, 0, 31)
    sc.render.resolution_x, sc.render.resolution_y = 560, 680
    for ai in range(8):
        ang = math.radians(ai * 45.0)  # ai=0 is directly in front (+X)
        r_cam = 86.0
        aim_camera(cam_pc, (r_cam * math.cos(ang), r_cam * math.sin(ang), 42.0), (0.0, 0.0, 30.5))
        set_md3_frame(pc_objs, 20 + (ai * 2) % 20)
        set_md3_frame(arc_objs, ai % 8)
        sc.render.filepath = os.path.join(OUT_DIR, f"pc_turn_{ai:02d}.png")
        bpy.ops.render.render(write_still=True)

    # 2. Close-up CRT Screen & Keyboard hero shot (40 units from screen!)
    sc.render.resolution_x, sc.render.resolution_y = 960, 720
    set_md3_frame(pc_objs, 24)
    set_md3_frame(arc_objs, 1)
    scr_obj.data.materials[0] = scr_mats["loopB"]
    aim_camera(cam_pc, (48.5, -5.0, 44.0), (8.5, 0.0, 42.5))
    sc.render.filepath = os.path.join(OUT_DIR, "pc_closeup_screen.png")
    bpy.ops.render.render(write_still=True)

    # 3. 12-panel PC animation contact sheet renders (from 3/4 front-left angle so screen, keyboard, slot disk & antennas all read!)
    sc.render.resolution_x, sc.render.resolution_y = 520, 600
    pc_sequence = [
        # (tag, solo_disk_only_frame, pc_frame, screen_key, show_arcs, arc_frame)
        ("00_solo_disk", 1,  0, "off",   False, 0),
        ("01_mat_f00",  -1,  0, "off",   False, 0),
        ("02_mat_f02",  -1,  2, "off",   False, 0),
        ("03_mat_f05",  -1,  5, "off",   False, 0),
        ("04_mat_f07",  -1,  7, "off",   False, 0),
        ("05_boot_f10", -1, 10, "noise", False, 0),
        ("06_boot_f13", -1, 13, "init",  False, 0),
        ("07_boot_f15", -1, 15, "cmd",   True,  0),
        ("08_boot_f18", -1, 18, "send",  True,  2),
        ("09_act_f24",  -1, 24, "loopA", True,  3),
        ("10_act_f31",  -1, 31, "loopB", True,  6),
        ("11_off_f49",  -1, 49, "dot",   False, 0),
    ]
    for tag, solo_fr, p_fr, skey, use_arc, a_fr in pc_sequence:
        if solo_fr >= 0:
            for o in pc_objs + arc_objs:
                o.hide_render = True
            for o in dsk_objs:
                o.hide_render = False
            set_md3_frame(dsk_objs, solo_fr)
            aim_camera(cam_pc, (22.0, -10.0, 12.5), (0.0, 0.0, 3.8))
        else:
            for o in dsk_objs:
                o.hide_render = True
            for o in pc_objs:
                o.hide_render = False
            for o in arc_objs:
                o.hide_render = not use_arc
            set_md3_frame(pc_objs, p_fr)
            set_md3_frame(arc_objs, a_fr)
            scr_obj.data.materials[0] = scr_mats[skey]
            aim_camera(cam_pc, (76.0, -26.0, 41.0), (1.0, 0.0, 31.0))

        sc.render.filepath = os.path.join(OUT_DIR, f"pc_seq_{tag}.png")
        bpy.ops.render.render(write_still=True)


def run_composite_sheets():
    from PIL import Image, ImageDraw, ImageFont

    def load_font(sz):
        for p in (r"C:\Windows\Fonts\consolab.ttf", r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
            if os.path.exists(p):
                return ImageFont.truetype(p, sz)
        return ImageFont.load_default()

    f_hdr = load_font(22)
    f_lbl = load_font(15)

    def make_grid(title, items, cols, cell_w, cell_h, out_name):
        rows = (len(items) + cols - 1) // cols
        pad = 12
        top_h = 48
        lbl_h = 28
        W = pad + cols * (cell_w + pad)
        H = top_h + rows * (cell_h + lbl_h + pad) + pad
        canvas = Image.new("RGB", (W, H), (14, 17, 22))
        d = ImageDraw.Draw(canvas)
        d.text((pad + 4, 12), title, font=f_hdr, fill=(130, 235, 155))
        for idx, (fname, caption) in enumerate(items):
            r, c = divmod(idx, cols)
            x0 = pad + c * (cell_w + pad)
            y0 = top_h + r * (cell_h + lbl_h + pad)
            im = Image.open(os.path.join(OUT_DIR, fname)).convert("RGB").resize((cell_w, cell_h), Image.LANCZOS)
            canvas.paste(im, (x0, y0))
            d.rectangle([x0, y0, x0 + cell_w - 1, y0 + cell_h + lbl_h - 1], outline=(55, 68, 82), width=1)
            d.rectangle([x0, y0 + cell_h, x0 + cell_w - 1, y0 + cell_h + lbl_h - 1], fill=(22, 27, 34))
            d.text((x0 + 8, y0 + cell_h + 5), caption, font=f_lbl, fill=(225, 232, 240))
        out_p = os.path.join(OUT_DIR, out_name)
        canvas.save(out_p)
        print(f"  [OK] Composite saved: {out_p}")

    # 1. Viewmodel Turntable (4x2)
    make_grid(
        "progs/v_netsend.md3 - 8-Angle Turntable (714 tris, 2 surfaces)",
        [(f"vm_turn_{i:02d}.png", f"Yaw {i * 45} deg") for i in range(8)],
        cols=4, cell_w=380, cell_h=380, out_name="sheet_vm_turntable.png",
    )

    # 2. Viewmodel 60-Frame Animation Contact Sheet (4x3)
    vm_caps = [
        ("vm_fp_00.png", "f00: Idle Hold (LOL.BAT legible)"),
        ("vm_fp_10.png", "f10: Finger Spin Launch"),
        ("vm_fp_15.png", "f15: Flipped 180 (Metal Shutter & Hub)"),
        ("vm_fp_20.png", "f20: Flip Return"),
        ("vm_fp_28.png", "f28: Inspect Tilt & Smug Nod"),
        ("vm_fp_39.png", "f39: Idle Loop End (-> f00)"),
        ("vm_fp_42.png", "f42: Throw Wind-Up"),
        ("vm_fp_43.png", "f43: Hard Downward Whip"),
        ("vm_fp_44.png", "f44: Release! (Hand Empty f44+)"),
        ("vm_fp_50.png", "f50: Empty Follow-Through"),
        ("vm_fp_54.png", "f54: Empty Wrist Shake-Out"),
        ("vm_fp_57.png", "f57: Fresh Disk Slides In (Reload)"),
    ]
    make_grid(
        "progs/v_netsend.md3 - First-Person Animation Key Frames (0..59, Red Dot = Crosshair)",
        vm_caps, cols=4, cell_w=440, cell_h=248, out_name="sheet_vm_frames.png",
    )

    # 3. Deployable PC + Arcs Turntable (4x2)
    make_grid(
        "progs/netsend_pc.md3 (1354 tris) + netsend_arc.md3 (224 tris) - 8-Angle Base-Origin Spin Turntable",
        [(f"pc_turn_{i:02d}.png", f"Entity Yaw {i * 45} deg (32u Floor Disc)") for i in range(8)],
        cols=4, cell_w=380, cell_h=460, out_name="sheet_pc_turntable.png",
    )

    # 4. Deployable PC 50-Frame Animation + CRT Screen Sequence Contact Sheet (4x3)
    pc_caps = [
        ("pc_seq_00_solo_disk.png", "netsend_disk f01: Stuck in Floor"),
        ("pc_seq_01_mat_f00.png",   "f00: Materialize Start (Floor Disk)"),
        ("pc_seq_02_mat_f02.png",   "f02: Rising Out of Disk"),
        ("pc_seq_03_mat_f05.png",   "f05: Cartoon Stretch Overshoot"),
        ("pc_seq_04_mat_f07.png",   "f07: Heavy Squash Settle"),
        ("pc_seq_05_boot_f10.png",  "f10: Boot Degauss + White Noise"),
        ("pc_seq_06_boot_f13.png",  "f13: INITIALIZING BATCH FILE..."),
        ("pc_seq_07_boot_f15.png",  "f15: C:\\> LOL.BAT + Floppy LED"),
        ("pc_seq_08_boot_f18.png",  "f18: NET SEND * LOL"),
        ("pc_seq_09_act_f24.png",   "f24: Active Ghost-Typing + Arcs A"),
        ("pc_seq_10_act_f31.png",   "f31: Active WHERE'S THE DISK? Loop B"),
        ("pc_seq_11_off_f49.png",   "f49: Shutdown White Dot & Slump"),
    ]
    make_grid(
        "progs/netsend_pc.md3 - Animation Key Frames (0..49) & CRT Screen Sequence",
        pc_caps, cols=4, cell_w=390, cell_h=450, out_name="sheet_pc_frames.png",
    )


if __name__ == "__main__":
    if "--composite" in sys.argv:
        run_composite_sheets()
    else:
        run_blender_renders()
