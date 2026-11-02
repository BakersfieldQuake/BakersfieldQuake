r"""Headless Blender 5.2 3D PBR Asset Renderer for Wheelman's New Animations:
1. whirl_d{0..7}_f{0..11}.png (96 frames): 3D PBR Helicopter/Hammer-Throw Whirling Wheel-Barbell
2. robot_d{0..7}_p{0..4}.png  (40 frames): Full 3D PBR Cybernetic Mecha-Wheelman Robot across all 8 angles (360°)
"""
import math
import os
import bpy
from mathutils import Euler, Vector

OUT_DIR = r"G:\Quake\Combat\BakersfieldQuake\source\mm_tools\wheelman_actions\extra3d"
os.makedirs(OUT_DIR, exist_ok=True)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = eng
            break
        except Exception:
            continue
    scene.render.resolution_x = 360
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    if hasattr(scene, "eevee"):
        for attr, val in (("taa_render_samples", 16), ("use_raytracing", True)):
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
    bg_hi = nt.nodes.new("ShaderNodeBackground")
    bg_hi.inputs["Color"].default_value = (0.72, 0.78, 0.88, 1.0)
    bg_hi.inputs["Strength"].default_value = 1.35
    nt.links.new(bg_hi.outputs["Background"], out_w.inputs["Surface"])

    # Studio 3-point + dramatic rim lights
    lights = [
        ("KeyLight", (2.6, -2.8, 3.6), 950.0, (1.0, 0.96, 0.90), 1.1),
        ("FillLight", (-3.0, -2.0, 1.8), 420.0, (0.78, 0.88, 1.0), 1.6),
        ("RimLight", (0.2, 3.2, 2.8), 780.0, (0.85, 0.93, 1.0), 1.2),
        ("FloorBounce", (0.0, -1.5, -1.2), 220.0, (1.0, 0.82, 0.68), 1.8),
    ]
    for name, loc, energy, col, sz in lights:
        ld = bpy.data.lights.new(name, type="AREA")
        ld.energy = energy
        ld.color = col
        ld.size = sz
        lo = bpy.data.objects.new(name, ld)
        scene.collection.objects.link(lo)
        lo.location = loc
        direction = Vector((0.0, 0.0, 0.85)) - Vector(loc)
        lo.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    return scene


def make_pbr_mat(name, base_col, metallic=0.0, roughness=0.4, emit_col=None, emit_str=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_col, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emit_col is not None and emit_str > 0.0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emit_col, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emit_str
    return mat


def add_part(parent, prim_fn, name, mat, loc=(0, 0, 0), rot_deg=(0, 0, 0), scale=(1, 1, 1), smooth=True, **kwargs):
    prim_fn(location=(0, 0, 0), **kwargs)
    ob = bpy.context.active_object
    ob.name = name
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = Euler((math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2])), "XYZ")
    ob.scale = scale
    if smooth:
        bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def build_wheel_assembly(parent, z_height, mats, include_hub_led=False, include_plasma=False):
    """Builds the iconic Wheelman horizontal steel axle + twin white-dish lugged rubber tires + central chrome cylinder."""
    rig_grp = bpy.data.objects.new("WheelRigGrp", None)
    bpy.context.scene.collection.objects.link(rig_grp)
    rig_grp.parent = parent
    rig_grp.location = (0.0, 0.0, z_height)

    # Horizontal steel axle along X
    add_part(
        rig_grp, bpy.ops.mesh.primitive_cylinder_add, "SteelAxle", mats["steel"],
        loc=(0, 0, 0), rot_deg=(0, 90, 0), vertices=24, radius=0.026, depth=0.96,
    )
    # Central mirror-chrome cylinder along Y (protruding behind -Y and slightly +Y)
    add_part(
        rig_grp, bpy.ops.mesh.primitive_cylinder_add, "ChromeTube", mats["chrome"],
        loc=(0, -0.16, 0), rot_deg=(90, 0, 0), vertices=32, radius=0.062, depth=0.42,
    )
    add_part(
        rig_grp, bpy.ops.mesh.primitive_cylinder_add, "ExhaustCap", mats["dark"],
        loc=(0, -0.37, 0), rot_deg=(90, 0, 0), vertices=24, radius=0.066, depth=0.07,
    )
    if include_plasma:
        plasma = add_part(
            rig_grp, bpy.ops.mesh.primitive_cone_add, "PlasmaJet", mats["plasma"],
            loc=(0, -0.54, 0), rot_deg=(-90, 0, 0), vertices=20, radius1=0.056, radius2=0.006, depth=0.34,
        )
    else:
        plasma = None

    wheels = []
    for side_s in (-1.0, 1.0):
        wx = side_s * 0.45
        w_root = bpy.data.objects.new(f"Wheel_{int(side_s)}", None)
        bpy.context.scene.collection.objects.link(w_root)
        w_root.parent = rig_grp
        w_root.location = (wx, 0.0, 0.0)

        # Black rubber torus tire in YZ plane
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.175, minor_radius=0.062, major_segments=36, minor_segments=18,
            location=(0, 0, 0), rotation=(0, math.pi * 0.5, 0),
        )
        tire = bpy.context.active_object
        tire.parent = w_root
        tire.scale = (1.12, 1.0, 1.0)
        bpy.ops.object.shade_smooth()
        tire.data.materials.append(mats["rubber"])

        # Tread lugs so wheel rotation visibly reads!
        for ti in range(14):
            ang = ti * (360.0 / 14.0)
            ar = math.radians(ang)
            add_part(
                w_root, bpy.ops.mesh.primitive_cube_add, f"Lug_{side_s}_{ti}", mats["rubber_lug"],
                loc=(0.0, math.cos(ar) * 0.232, math.sin(ar) * 0.232),
                rot_deg=(-ang, 0, 0), scale=(0.052, 0.014, 0.022), smooth=False, size=1.0,
            )

        # White painted steel dish
        add_part(
            w_root, bpy.ops.mesh.primitive_cylinder_add, f"Dish_{side_s}", mats["white_rim"],
            loc=(0, 0, 0), rot_deg=(0, 90, 0), vertices=28, radius=0.132, depth=0.036,
        )
        # Hub cap + lug bolts
        add_part(
            w_root, bpy.ops.mesh.primitive_cylinder_add, f"Hub_{side_s}", mats["chrome"],
            loc=(side_s * 0.022, 0, 0), rot_deg=(0, 90, 0), vertices=18, radius=0.032, depth=0.055,
        )
        if include_hub_led:
            bpy.ops.mesh.primitive_torus_add(
                major_radius=0.105, minor_radius=0.009, major_segments=28, minor_segments=10,
                location=(side_s * 0.020, 0, 0), rotation=(0, math.pi * 0.5, 0),
            )
            led = bpy.context.active_object
            led.parent = w_root
            led.data.materials.append(mats["red_glow"])

        wheels.append(w_root)
    return rig_grp, wheels, plasma


def render_whirl_barbell_set():
    """Renders 8 directions x 12 spin steps of the 3D whirling wheel-barbell."""
    scene = reset_scene()
    mats = {
        "rubber": make_pbr_mat("Rubber", (0.045, 0.047, 0.052), metallic=0.02, roughness=0.66),
        "rubber_lug": make_pbr_mat("RubberLug", (0.08, 0.084, 0.09), metallic=0.05, roughness=0.52),
        "white_rim": make_pbr_mat("WhiteRim", (0.94, 0.95, 0.97), metallic=0.18, roughness=0.22),
        "steel": make_pbr_mat("Steel", (0.62, 0.64, 0.68), metallic=0.92, roughness=0.22),
        "chrome": make_pbr_mat("Chrome", (0.96, 0.97, 0.99), metallic=1.0, roughness=0.06),
        "dark": make_pbr_mat("Dark", (0.05, 0.055, 0.06), metallic=0.75, roughness=0.35),
    }
    root = bpy.data.objects.new("WhirlRoot", None)
    scene.collection.objects.link(root)
    rig_grp, wheels, _ = build_wheel_assembly(root, 0.0, mats, include_hub_led=False, include_plasma=False)

    cam_d = bpy.data.cameras.new("CamWhirl")
    cam_d.lens = 52.0
    cam = bpy.data.objects.new("CamWhirl", cam_d)
    scene.collection.objects.link(cam)
    scene.camera = cam

    dist = 2.55
    elev = math.radians(14.0)
    for d in range(8):
        az = math.radians(d * 45.0)
        # Camera at d=0 stands at +Y looking toward origin (0,0,0)
        cx = -math.sin(az) * dist * math.cos(elev)
        cy = math.cos(az) * dist * math.cos(elev)
        cz = dist * math.sin(elev)
        cam.location = (cx, cy, cz)
        cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()

        for f in range(12):
            yaw = math.radians(f * 30.0)
            cant = math.radians(14.0 * math.sin(yaw))
            root.rotation_euler = Euler((cant, math.radians(8.0 * math.cos(yaw)), yaw), "XYZ")
            for w in wheels:
                w.rotation_euler = Euler((f * 0.6, 0.0, 0.0), "XYZ")
            scene.render.filepath = os.path.join(OUT_DIR, f"whirl_d{d}_f{f}.png")
            bpy.ops.render.render(write_still=True)


def render_robot_wheelman_set():
    """Builds & renders full 3D PBR Cybernetic Mecha-Wheelman across 8 angles (360°) x 5 poses!"""
    scene = reset_scene()
    mats = {
        "titanium": make_pbr_mat("Titanium", (0.52, 0.56, 0.63), metallic=0.93, roughness=0.24),
        "armor_hi": make_pbr_mat("ArmorHi", (0.74, 0.78, 0.84), metallic=0.96, roughness=0.16),
        "chrome": make_pbr_mat("Chrome", (0.95, 0.97, 1.00), metallic=1.0, roughness=0.06),
        "dark": make_pbr_mat("DarkServo", (0.12, 0.14, 0.17), metallic=0.86, roughness=0.38),
        "rubber": make_pbr_mat("Rubber", (0.045, 0.047, 0.052), metallic=0.02, roughness=0.66),
        "rubber_lug": make_pbr_mat("RubberLug", (0.085, 0.09, 0.098), metallic=0.05, roughness=0.50),
        "white_rim": make_pbr_mat("WhiteRim", (0.93, 0.95, 0.97), metallic=0.22, roughness=0.22),
        "steel": make_pbr_mat("Steel", (0.62, 0.65, 0.70), metallic=0.92, roughness=0.20),
        "red_glow": make_pbr_mat("RedGlow", (1.0, 0.12, 0.04), metallic=0.1, roughness=0.15, emit_col=(1.0, 0.15, 0.03), emit_str=15.0),
        "plasma": make_pbr_mat("PlasmaBlue", (0.20, 0.82, 1.0), metallic=0.0, roughness=0.1, emit_col=(0.22, 0.82, 1.0), emit_str=18.0),
    }

    # Root at feet (z=0.0 = ground plane!) facing +Y so d=0 (+Y camera) sees 0° Front!
    robo = bpy.data.objects.new("MechaWheelman", None)
    scene.collection.objects.link(robo)

    # Pelvis pivot at z=0.88
    hips = bpy.data.objects.new("HipsPivot", None)
    scene.collection.objects.link(hips)
    hips.parent = robo
    hips.location = (0.0, 0.0, 0.88)

    # Armored Cyber-Pelvis & Groin Codpiece
    add_part(hips, bpy.ops.mesh.primitive_cube_add, "PelvisBlock", mats["titanium"], loc=(0, 0, 0.02), scale=(0.29, 0.19, 0.14), smooth=False)
    add_part(hips, bpy.ops.mesh.primitive_uv_sphere_add, "CyberCodpiece", mats["armor_hi"], loc=(0, 0.11, -0.04), scale=(0.085, 0.095, 0.105))
    add_part(hips, bpy.ops.mesh.primitive_uv_sphere_add, "GluteL", mats["titanium"], loc=(-0.09, -0.09, -0.01), scale=(0.095, 0.10, 0.11))
    add_part(hips, bpy.ops.mesh.primitive_uv_sphere_add, "GluteR", mats["titanium"], loc=(0.09, -0.09, -0.01), scale=(0.095, 0.10, 0.11))

    # Integrated Motorized Twin-Wheel & Chrome Butt-Thruster Assembly!
    rig_grp, wheels, plasma = build_wheel_assembly(hips, -0.03, mats, include_hub_led=True, include_plasma=True)

    # Spine & Armored Torso
    torso = bpy.data.objects.new("TorsoPivot", None)
    scene.collection.objects.link(torso)
    torso.parent = hips
    torso.location = (0.0, 0.0, 0.12)

    # Segmented hydraulic abs + twin chrome pistons
    add_part(torso, bpy.ops.mesh.primitive_cylinder_add, "WaistCore", mats["dark"], loc=(0, 0, 0.11), radius=0.145, depth=0.22)
    for side_s in (-1.0, 1.0):
        add_part(torso, bpy.ops.mesh.primitive_cylinder_add, f"AbPiston_{side_s}", mats["chrome"], loc=(side_s * 0.12, 0.06, 0.12), rot_deg=(0, side_s * -8, 0), radius=0.024, depth=0.24)

    # Heavy Titanium Pectoral Chest Armor + Glowing Red Arc Reactor Core + Rear Spine Vents
    add_part(torso, bpy.ops.mesh.primitive_cube_add, "ChestPlate", mats["armor_hi"], loc=(0, 0.02, 0.34), scale=(0.36, 0.22, 0.24), smooth=False)
    add_part(torso, bpy.ops.mesh.primitive_cylinder_add, "ChestCoreRing", mats["chrome"], loc=(0, 0.135, 0.35), rot_deg=(90, 0, 0), radius=0.068, depth=0.03)
    reactor = add_part(torso, bpy.ops.mesh.primitive_cylinder_add, "ChestReactor", mats["red_glow"], loc=(0, 0.145, 0.35), rot_deg=(90, 0, 0), radius=0.050, depth=0.025)
    # Rear dorsal spine segments & shoulder exhaust vents
    for si in range(4):
        add_part(torso, bpy.ops.mesh.primitive_cube_add, f"SpineNode_{si}", mats["chrome"], loc=(0, -0.12, 0.14 + si * 0.085), scale=(0.07, 0.06, 0.05), smooth=False)
    for side_s in (-1.0, 1.0):
        add_part(torso, bpy.ops.mesh.primitive_cylinder_add, f"BackStack_{side_s}", mats["chrome"], loc=(side_s * 0.15, -0.11, 0.49), rot_deg=(-18, side_s * 10, 0), radius=0.032, depth=0.18)

    # Neck & Mecha-Wheelman Head (Visor + Chrome Buck-Teeth + Spiky Metal Crest!)
    head = bpy.data.objects.new("HeadPivot", None)
    scene.collection.objects.link(head)
    head.parent = torso
    head.location = (0.0, 0.01, 0.50)

    add_part(head, bpy.ops.mesh.primitive_cylinder_add, "NeckServo", mats["dark"], loc=(0, 0, 0.04), radius=0.068, depth=0.11)
    add_part(head, bpy.ops.mesh.primitive_uv_sphere_add, "Cranium", mats["armor_hi"], loc=(0, 0.01, 0.17), scale=(0.125, 0.145, 0.145))
    add_part(head, bpy.ops.mesh.primitive_cube_add, "JawMask", mats["titanium"], loc=(0, 0.05, 0.09), scale=(0.18, 0.18, 0.11), smooth=False)
    # Blazing Red Terminator Visor!
    visor = add_part(head, bpy.ops.mesh.primitive_cube_add, "CyberVisor", mats["red_glow"], loc=(0, 0.132, 0.185), scale=(0.19, 0.05, 0.038), smooth=False)
    # Iconic Gleaming Chrome Robot Buck-Teeth & Open Grin!
    add_part(head, bpy.ops.mesh.primitive_cube_add, "MouthCavity", mats["dark"], loc=(0, 0.136, 0.095), scale=(0.11, 0.03, 0.045), smooth=False)
    add_part(head, bpy.ops.mesh.primitive_cube_add, "BuckToothL", mats["chrome"], loc=(-0.016, 0.146, 0.106), scale=(0.024, 0.016, 0.032), smooth=False)
    add_part(head, bpy.ops.mesh.primitive_cube_add, "BuckToothR", mats["chrome"], loc=(0.016, 0.146, 0.106), scale=(0.024, 0.016, 0.032), smooth=False)
    # Spiky Metallic Hair Crest Blades (homage to Wheelman's wild spiky hair!)
    for bi, bx in enumerate((-0.07, -0.035, 0.0, 0.035, 0.07)):
        add_part(
            head, bpy.ops.mesh.primitive_cone_add, f"HairSpike_{bi}", mats["dark"],
            loc=(bx, -0.01 + (bi % 2) * 0.02, 0.32), rot_deg=(-12 + bi * 5, bx * 260, 0),
            vertices=6, radius1=0.032, radius2=0.003, depth=0.11,
        )

    # Articulated Arms (Left & Right)
    shoulders = {}
    elbows = {}
    for side_s, tag in ((-1.0, "L"), (1.0, "R")):
        sh = bpy.data.objects.new(f"Shoulder_{tag}", None)
        scene.collection.objects.link(sh)
        sh.parent = torso
        sh.location = (side_s * 0.24, 0.0, 0.41)
        shoulders[tag] = sh

        add_part(sh, bpy.ops.mesh.primitive_uv_sphere_add, f"Pauldron_{tag}", mats["armor_hi"], loc=(side_s * 0.02, 0, 0.01), scale=(0.095, 0.095, 0.095))
        add_part(sh, bpy.ops.mesh.primitive_cylinder_add, f"UpperArm_{tag}", mats["titanium"], loc=(side_s * 0.03, 0, -0.14), radius=0.056, depth=0.24)
        add_part(sh, bpy.ops.mesh.primitive_cylinder_add, f"ArmPiston_{tag}", mats["chrome"], loc=(side_s * 0.075, 0.02, -0.14), radius=0.016, depth=0.22)

        el = bpy.data.objects.new(f"Elbow_{tag}", None)
        scene.collection.objects.link(el)
        el.parent = sh
        el.location = (side_s * 0.03, 0.0, -0.27)
        elbows[tag] = el

        add_part(el, bpy.ops.mesh.primitive_uv_sphere_add, f"ElbowJoint_{tag}", mats["dark"], loc=(0, 0, 0), scale=(0.055, 0.055, 0.055))
        add_part(el, bpy.ops.mesh.primitive_cube_add, f"Forearm_{tag}", mats["armor_hi"], loc=(0, 0.01, -0.13), scale=(0.095, 0.105, 0.22), smooth=False)
        # 3-Pronged Hydraulic Robo-Claw!
        for ci, cx_off in enumerate((-0.028, 0.0, 0.028)):
            add_part(el, bpy.ops.mesh.primitive_cube_add, f"Claw_{tag}_{ci}", mats["chrome"], loc=(cx_off, 0.03, -0.27), rot_deg=(15, 0, 0), scale=(0.018, 0.025, 0.085), smooth=False)

    # Articulated Legs (Left & Right) planted down to z=0!
    thighs = {}
    knees = {}
    for side_s, tag in ((-1.0, "L"), (1.0, "R")):
        th = bpy.data.objects.new(f"Thigh_{tag}", None)
        scene.collection.objects.link(th)
        th.parent = hips
        th.location = (side_s * 0.135, 0.0, -0.04)
        thighs[tag] = th

        add_part(th, bpy.ops.mesh.primitive_cube_add, f"ThighArmor_{tag}", mats["armor_hi"], loc=(0, 0.01, -0.19), scale=(0.145, 0.155, 0.34), smooth=False)
        add_part(th, bpy.ops.mesh.primitive_cube_add, f"ThighVent_{tag}", mats["red_glow"], loc=(side_s * 0.05, 0.075, -0.18), scale=(0.03, 0.02, 0.14), smooth=False)

        kn = bpy.data.objects.new(f"Knee_{tag}", None)
        scene.collection.objects.link(kn)
        kn.parent = th
        kn.location = (0.0, 0.0, -0.39)
        knees[tag] = kn

        add_part(kn, bpy.ops.mesh.primitive_cylinder_add, f"KneeServo_{tag}", mats["chrome"], loc=(0, 0.01, 0), rot_deg=(0, 90, 0), radius=0.068, depth=0.14)
        add_part(kn, bpy.ops.mesh.primitive_cylinder_add, f"ShinMain_{tag}", mats["titanium"], loc=(0, -0.01, -0.20), radius=0.058, depth=0.36)
        add_part(kn, bpy.ops.mesh.primitive_cylinder_add, f"ShinStrut_{tag}", mats["chrome"], loc=(0, 0.055, -0.20), radius=0.020, depth=0.34)
        # Heavy Cyber-Foot planted flat at z = -0.45 relative to knee (0.88 - 0.04 - 0.39 - 0.45 = 0.00!)
        add_part(kn, bpy.ops.mesh.primitive_cube_add, f"CyberFoot_{tag}", mats["armor_hi"], loc=(0, 0.065, -0.415), scale=(0.14, 0.25, 0.07), smooth=False)

    # Frame camera so z=0 sits near GROUND_Y=332 and crown sits near y=54 (height ~ 278px)!
    cam_d = bpy.data.cameras.new("CamRobo")
    cam_d.lens = 54.0
    cam = bpy.data.objects.new("CamRobo", cam_d)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # 5 Poses (p=0..4)
    poses = [
        # p=0: Upright alignment stance (matches human standing silhouette)
        dict(hip_z=0.88, torso_rx=0, head_rz=0, shL=(8, 0, -14), elL=(24, 0, 0), shR=(8, 0, 14), elR=(24, 0, 0), thL=(-4, 0, -4), knL=(4, 0, 0), thR=(-4, 0, 4), knR=(4, 0, 0), plasma=False, wspin=0),
        # p=1: Hydraulic power-up surge (knees braced, forearms clenching up)
        dict(hip_z=0.85, torso_rx=6, head_rz=0, shL=(28, 0, -24), elL=(68, 0, 0), shR=(28, 0, 24), elR=(68, 0, 0), thL=(14, 0, -6), knL=(-14, 0, 0), thR=(14, 0, 6), knR=(-14, 0, 0), plasma=True, wspin=18),
        # p=2: Full Mecha-Wheelman Combat Roar Flex (arms raised menacingly, plasma jet firing!)
        dict(hip_z=0.89, torso_rx=-5, head_rz=0, shL=(62, 0, -42), elL=(78, 0, 0), shR=(62, 0, 42), elR=(78, 0, 0), thL=(6, 0, -7), knL=(-6, 0, 0), thR=(6, 0, 7), knR=(-6, 0, 0), plasma=True, wspin=36),
        # p=3: Combat Scan Left + Thruster Burn
        dict(hip_z=0.87, torso_rx=4, head_rz=14, shL=(42, 0, -30), elL=(72, 0, 0), shR=(34, 0, 26), elR=(64, 0, 0), thL=(10, 0, -6), knL=(-10, 0, 0), thR=(10, 0, 6), knR=(-10, 0, 0), plasma=True, wspin=54),
        # p=4: Combat Scan Right + Servo Lock
        dict(hip_z=0.88, torso_rx=2, head_rz=-14, shL=(34, 0, -26), elL=(64, 0, 0), shR=(42, 0, 30), elR=(72, 0, 0), thL=(8, 0, -6), knL=(-8, 0, 0), thR=(8, 0, 6), knR=(-8, 0, 0), plasma=False, wspin=72),
    ]

    dist = 3.25
    target = Vector((0.0, 0.0, 0.88))
    for d in range(8):
        az = math.radians(d * 45.0)
        # Match Quake 8-direction convention: d=0 Front (+Y), d=1 45° Front-Left (-X,+Y), d=2 90° Left Profile (-X), d=4 180° Back (-Y)
        cx = -math.sin(az) * dist
        cy = math.cos(az) * dist
        cz = 1.02
        cam.location = (cx, cy, cz)
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

        for pi, p in enumerate(poses):
            hips.location = (0.0, 0.0, p["hip_z"])
            torso.rotation_euler = Euler((math.radians(p["torso_rx"]), 0, 0), "XYZ")
            head.rotation_euler = Euler((0, 0, math.radians(p["head_rz"])), "XYZ")
            shoulders["L"].rotation_euler = Euler([math.radians(v) for v in p["shL"]], "XYZ")
            elbows["L"].rotation_euler = Euler([math.radians(v) for v in p["elL"]], "XYZ")
            shoulders["R"].rotation_euler = Euler([math.radians(v) for v in p["shR"]], "XYZ")
            elbows["R"].rotation_euler = Euler([math.radians(v) for v in p["elR"]], "XYZ")
            thighs["L"].rotation_euler = Euler([math.radians(v) for v in p["thL"]], "XYZ")
            knees["L"].rotation_euler = Euler([math.radians(v) for v in p["knL"]], "XYZ")
            thighs["R"].rotation_euler = Euler([math.radians(v) for v in p["thR"]], "XYZ")
            knees["R"].rotation_euler = Euler([math.radians(v) for v in p["knR"]], "XYZ")
            if plasma is not None:
                plasma.hide_render = not p["plasma"]
            for w in wheels:
                w.rotation_euler = Euler((math.radians(p["wspin"]), 0, 0), "XYZ")

            scene.render.filepath = os.path.join(OUT_DIR, f"robot_d{d}_p{pi}.png")
            bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    print("Rendering 96 whirling wheel-barbell frames...")
    render_whirl_barbell_set()
    print("Rendering 40 Mecha-Wheelman 3D robot frames...")
    render_robot_wheelman_set()
    print("ALL 136 EXTRA 3D PBR ASSETS RENDERED SUCCESSFULLY!")
