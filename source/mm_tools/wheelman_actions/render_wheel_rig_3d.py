r"""Headless Blender 5.2 PBR 3D Renderer for Wheelman's Signature Metal Bar & Dual Wheels Rig.

Renders crisp RGBA transparent sprites of the detached 3D Wheel-Barbell Assembly:
  - Straight brushed-steel axle bar + white hub spacers + outer hex nuts
  - Central mirror-polished chrome cylinder + dark fluted/ribbed end cap
  - Twin deep-dish white painted steel rims (with 4 lug bolts + valve stem)
  - Twin thick ribbed/lugged black pneumatic rubber tires

Used for ultra-realistic 3D tumbling projectile flight & ground bounce in the 360° THROW animation!
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "rig3d")


def run_blender():
    import bpy
    import bmesh
    import mathutils

    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    sc = bpy.context.scene
    avail = {e.identifier for e in sc.render.bl_rna.properties["engine"].enum_items}
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in avail else "CYCLES"
    sc.render.film_transparent = True
    sc.render.resolution_x = 320
    sc.render.resolution_y = 320
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"

    # Rich studio reflection world so mirror chrome cylinder gleams authentically
    world = bpy.data.worlds.new("RigStudio")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    n_out = nt.nodes.new("ShaderNodeOutputWorld")
    n_bg = nt.nodes.new("ShaderNodeBackground")
    n_tex = nt.nodes.new("ShaderNodeTexGradient")
    n_coord = nt.nodes.new("ShaderNodeTexCoord")
    n_ramp = nt.nodes.new("ShaderNodeValToRGB")
    n_ramp.color_ramp.elements[0].position = 0.25
    n_ramp.color_ramp.elements[0].color = (0.14, 0.12, 0.11, 1.0)
    n_ramp.color_ramp.elements[1].position = 0.78
    n_ramp.color_ramp.elements[1].color = (0.95, 0.94, 0.92, 1.0)
    n_bg.inputs["Strength"].default_value = 1.35
    nt.links.new(n_coord.outputs["Generated"], n_tex.inputs["Vector"])
    nt.links.new(n_tex.outputs["Fac"], n_ramp.inputs["Fac"])
    nt.links.new(n_ramp.outputs["Color"], n_bg.inputs["Color"])
    nt.links.new(n_bg.outputs["Background"], n_out.inputs["Surface"])
    sc.world = world

    def make_mat(name, base_col, metallic=0.0, roughness=0.4):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*base_col, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        return m

    mat_chrome = make_mat("MirrorChrome", (0.92, 0.94, 0.97), metallic=1.0, roughness=0.06)
    mat_steel = make_mat("BrushedSteel", (0.58, 0.60, 0.64), metallic=0.92, roughness=0.24)
    mat_cap = make_mat("DarkFlutedCap", (0.20, 0.21, 0.23), metallic=0.85, roughness=0.28)
    mat_white = make_mat("WhiteRim", (0.93, 0.94, 0.95), metallic=0.12, roughness=0.26)
    mat_rubber = make_mat("BlackTire", (0.045, 0.047, 0.052), metallic=0.0, roughness=0.62)

    rig_root = bpy.data.objects.new("WheelRigRoot", None)
    sc.collection.objects.link(rig_root)

    def parent_it(obj):
        obj.parent = rig_root
        for p in obj.data.polygons:
            p.use_smooth = True

    # Coordinate convention:
    # X = axle left-right (-0.42 .. +0.42 m), Y = forward (+Y), Z = up (+Z)
    # 1) Steel Axle Bar along X
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.017, depth=0.90, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
    axle = bpy.context.active_object
    axle.data.materials.append(mat_steel)
    parent_it(axle)

    # 2) Central Mirror-Chrome Cylinder welded perpendicular along +Y (slightly angled down)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.052, depth=0.30, location=(0, 0.13, 0), rotation=(math.pi / 2, 0, 0))
    cyl = bpy.context.active_object
    cyl.data.materials.append(mat_chrome)
    parent_it(cyl)

    # Weld collar around axle
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.032, depth=0.14, location=(0, 0.0, 0), rotation=(0, math.pi / 2, 0))
    collar = bpy.context.active_object
    collar.data.materials.append(mat_chrome)
    parent_it(collar)

    # Fluted dark-chrome end cap at +Y = 0.295
    bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=0.056, depth=0.065, location=(0, 0.295, 0), rotation=(math.pi / 2, 0, 0))
    cap = bpy.context.active_object
    cap.data.materials.append(mat_cap)
    parent_it(cap)
    for fi in range(12):
        ang = fi * (2.0 * math.pi / 12.0)
        rx_f = 0.056 * math.cos(ang)
        rz_f = 0.056 * math.sin(ang)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(rx_f, 0.295, rz_f), rotation=(0, ang, 0))
        rib = bpy.context.active_object
        rib.scale = (0.004, 0.030, 0.004)
        rib.data.materials.append(mat_chrome)
        parent_it(rib)

    # 3) Left & Right Pneumatic Tires + White Steel Dishes + Spacers + Hex Nuts
    for side in (-1.0, +1.0):
        wx = side * 0.365
        # Pneumatic torus tire in YZ plane (major_radius=0.155, minor_radius=0.068 -> outer r=0.223)
        bpy.ops.mesh.primitive_torus_add(
            major_segments=48, minor_segments=24,
            major_radius=0.152, minor_radius=0.068,
            location=(wx, 0, 0), rotation=(0, math.pi / 2, 0),
        )
        tire = bpy.context.active_object
        tire.scale = (1.0, 1.0, 0.86)  # slightly flatter tread profile
        tire.data.materials.append(mat_rubber)
        parent_it(tire)

        # Raised 3D circumferential tread ribs & shoulder lugs so wheel rotation pops!
        for r_off in (-0.026, 0.0, +0.026):
            bpy.ops.mesh.primitive_torus_add(
                major_segments=48, minor_segments=12,
                major_radius=0.214, minor_radius=0.007,
                location=(wx + r_off, 0, 0), rotation=(0, math.pi / 2, 0),
            )
            tread_rib = bpy.context.active_object
            tread_rib.data.materials.append(mat_rubber)
            parent_it(tread_rib)

        for li in range(18):
            la = li * (2.0 * math.pi / 18.0)
            ly = 0.215 * math.cos(la)
            lz = 0.215 * math.sin(la)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(wx, ly, lz), rotation=(-la, 0, 0))
            lug = bpy.context.active_object
            lug.scale = (0.044, 0.011, 0.008)
            lug.data.materials.append(mat_rubber)
            parent_it(lug)

        # White painted steel wheel dish
        bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=0.118, depth=0.048, location=(wx, 0, 0), rotation=(0, math.pi / 2, 0))
        dish = bpy.context.active_object
        dish.data.materials.append(mat_white)
        parent_it(dish)

        # Recessed rim lip ring
        bpy.ops.mesh.primitive_torus_add(
            major_segments=36, minor_segments=14,
            major_radius=0.112, minor_radius=0.012,
            location=(wx + side * 0.022, 0, 0), rotation=(0, math.pi / 2, 0),
        )
        lip = bpy.context.active_object
        lip.data.materials.append(mat_white)
        parent_it(lip)

        # 4 Lug bolts on outer & inner face
        for bi in range(4):
            ba = bi * (math.pi / 2.0) + 0.35
            by, bz = 0.056 * math.cos(ba), 0.056 * math.sin(ba)
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.010, depth=0.062, location=(wx, by, bz), rotation=(0, math.pi / 2, 0))
            bolt = bpy.context.active_object
            bolt.data.materials.append(mat_steel)
            parent_it(bolt)

        # Inner white cylindrical hub spacer
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.030, depth=0.075, location=(wx - side * 0.048, 0, 0), rotation=(0, math.pi / 2, 0))
        spacer = bpy.context.active_object
        spacer.data.materials.append(mat_white)
        parent_it(spacer)

        # Outer steel hex nut
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.026, depth=0.032, location=(wx + side * 0.042, 0, 0), rotation=(0, math.pi / 2, 0))
        nut = bpy.context.active_object
        nut.data.materials.append(mat_chrome)
        parent_it(nut)

    # Studio lights
    lights = [
        ("KeyL", (1.8, 2.2, 2.0), 160.0, (1.0, 0.97, 0.93), 1.4),
        ("FillR", (-2.0, 1.8, 1.4), 110.0, (0.90, 0.95, 1.0), 1.6),
        ("RimBack", (0.0, -2.4, 1.8), 140.0, (1.0, 0.95, 0.90), 1.5),
    ]
    for nm, loc, pwr, col, sz in lights:
        ld = bpy.data.lights.new(nm, type="AREA")
        ld.energy = pwr
        ld.color = col
        ld.size = sz
        lo = bpy.data.objects.new(nm, ld)
        lo.location = loc
        lo.rotation_euler = (-mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)

    cam_data = bpy.data.cameras.new("RigCam")
    cam_data.angle = math.radians(34.0)
    cam_obj = bpy.data.objects.new("RigCam", cam_data)
    sc.collection.objects.link(cam_obj)
    sc.camera = cam_obj

    # Render 8 camera directions (d=0..7 matching 0°, 45°, 90° Left, 135°, 180°, 225°, 270° Right, 315°)
    # x 8 end-over-end tumble spin angles = 64 crisp RGBA sprites!
    dist = 1.95
    elev = math.radians(10.0)
    for d in range(8):
        # Match Wheelman convention: d=0 views +Y front (cam at +Y), d=1 Front-Left, d=2 Left Profile, d=4 Back (-Y)
        az = math.radians(90.0 + d * 45.0)
        cx = dist * math.cos(elev) * math.cos(az)
        cy = dist * math.cos(elev) * math.sin(az)
        cz = dist * math.sin(elev)
        cam_obj.location = (cx, cy, cz)
        cam_obj.rotation_euler = (-mathutils.Vector((cx, cy, cz))).to_track_quat("-Z", "Y").to_euler()

        for s in range(8):
            pitch = s * (2.0 * math.pi / 8.0)
            roll = math.sin(pitch) * 0.22
            rig_root.rotation_euler = (pitch, roll, 0.0)
            sc.render.filepath = os.path.join(OUT_DIR, f"rig_d{d}_s{s}.png")
            bpy.ops.render.render(write_still=True)

    print("DONE rendering 64 3D PBR Wheel-Rig frames!")


if __name__ == "__main__":
    run_blender()
