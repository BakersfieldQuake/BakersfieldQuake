r"""Headless Blender 5.2 Studio Verification Renderer for G:\Quake\Combat\BakersfieldQuake\pink_supercar.glb.

Imports the exported glTF 2.0 binary (.glb) directly into Blender 5.2, sets up a sleek dark
showroom floor + 4-point automotive softbox lighting, renders 6 verification angles + a
1440x900 hero studio render, and assembles a labeled 6-panel inspection sheet!
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
GLB_PATH = os.path.join(MOD_DIR, "pink_supercar.glb")
OUT_DIR = os.path.join(HERE, "out", "pink_supercar")


def run_blender():
    import bpy
    import mathutils

    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    sc = bpy.context.scene
    avail = {e.identifier for e in sc.render.bl_rna.properties["engine"].enum_items}
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in avail else ("BLENDER_EEVEE" if "BLENDER_EEVEE" in avail else "CYCLES")
    sc.render.film_transparent = False

    world = bpy.data.worlds.new("ShowroomWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.075, 0.082, 0.115, 1.0)
        bg.inputs[1].default_value = 1.25
    sc.world = world

    # Import pink_supercar.glb!
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)

    # Dark satin showroom floor disc at z=0
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=14.0, depth=0.06, location=(0.0, 0.0, -0.031))
    fl = bpy.context.active_object
    fl_mat = bpy.data.materials.new("ShowroomFloor")
    fl_mat.use_nodes = True
    bsdf = fl_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.045, 0.048, 0.065, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.24
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.20
    fl.data.materials.append(fl_mat)

    # 4-Point Automotive Studio Lighting (Blender meters: car is ~4.85m along Y, ~2.15m along X, ~1.55m tall)
    # Note: In Blender glTF import, +Z_gl (Car Front) -> -Y_bl, +X_gl (Car Left +Y_q) -> +X_bl, +Y_gl -> +Z_bl!
    lights = [
        ("KeyFrontLeft",  ( 4.2, -5.2, 4.4), 520.0, (1.00, 0.97, 0.95), 2.2),
        ("FillFrontRight",(-4.4, -4.8, 3.6), 420.0, (0.92, 0.96, 1.00), 2.2),
        ("RimRearLeft",   ( 4.0,  5.2, 4.0), 440.0, (0.98, 0.92, 0.98), 2.0),
        ("RimRearRight",  (-4.0,  5.0, 3.8), 380.0, (0.94, 0.97, 1.00), 2.0),
        ("OverheadSoft",  ( 0.0, -0.6, 5.8), 480.0, (1.00, 0.99, 1.00), 3.0),
    ]
    for nm, loc, pwr, col, sz in lights:
        ld = bpy.data.lights.new(nm, type="AREA")
        ld.energy = pwr
        ld.color = col
        ld.size = sz
        lo = bpy.data.objects.new(nm, ld)
        lo.location = loc
        direction = mathutils.Vector((0.0, 0.0, 0.6)) - mathutils.Vector(loc)
        lo.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)

    cam_data = bpy.data.cameras.new("StudioCam")
    cam_obj = bpy.data.objects.new("StudioCam", cam_data)
    sc.collection.objects.link(cam_obj)
    sc.camera = cam_obj

    def aim(eye, tgt, fov_deg=42.0):
        cam_obj.location = eye
        d = mathutils.Vector(tgt) - mathutils.Vector(eye)
        cam_obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cam_data.angle = math.radians(fov_deg)

    # Save .blend file for inspection
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "pink_supercar_studio.blend"))

    # Activate animation helper (select NLA / Action for ScissorDoors_Showoff on shot 6!)
    root_obj = bpy.data.objects.get("Pink_Supercar_Root")

    # 1. Hero 1440x900 render (Front-Left 3/4 showcasing hood mural + "It's not pink" + roof webcam!)
    sc.frame_set(1)
    sc.render.resolution_x, sc.render.resolution_y = 1440, 900
    aim((3.35, -4.15, 2.05), (0.0, -0.25, 0.62), fov_deg=41.0)
    sc.render.filepath = os.path.join(OUT_DIR, "pink_supercar_hero.png")
    bpy.ops.render.render(write_still=True)

    # 6-Panel Studio Inspection Shots (960 x 640 each)
    sc.render.resolution_x, sc.render.resolution_y = 960, 640
    shots = [
        ("v1_front34",    ( 3.25, -4.10, 2.05), (0.00, -0.25, 0.62), 41.0),
        ("v2_hood_macro", ( 0.00, -3.95, 2.45), (0.00, -1.48, 0.48), 44.0),
        ("v3_side_left",  ( 5.35, -0.05, 1.02), (0.00, -0.05, 0.66), 39.0),
        ("v4_side_right", (-5.35, -0.05, 1.02), (0.00, -0.05, 0.66), 39.0),
        ("v5_webcam",     ( 1.28, -1.65, 1.88), (-0.05, 0.12, 1.36), 35.0),
    ]
    for fn, eye, tgt, fov in shots:
        aim(eye, tgt, fov)
        sc.render.filepath = os.path.join(OUT_DIR, f"{fn}.png")
        bpy.ops.render.render(write_still=True)

    # Panel 6: Articulate Scissor Doors 56 deg UPWARD in Blender to verify scissor door rig + Rear 3/4!
    # Note: In Blender Z-up space (+X_bl = Car Left, -Y_bl = Car Front, +Z_bl = Car Up):
    # Rotating +56 deg around +X_bl lifts +Y_bl (rear of door!) UPWARD into +Z_bl!
    for dnm, flare_z in (("door_l", -11.0), ("door_l_glass", -11.0), ("door_r", 11.0), ("door_r_glass", 11.0)):
        ob = bpy.data.objects.get(dnm)
        if ob:
            if ob.animation_data:
                ob.animation_data_clear()
            ob.rotation_mode = "XYZ"
            ob.rotation_euler = (math.radians(56.0), 0.0, math.radians(flare_z))

    aim((-3.75, 4.35, 2.15), (0.0, 0.05, 0.78), fov_deg=44.0)
    sc.render.filepath = os.path.join(OUT_DIR, "v6_rear_scissor.png")
    bpy.ops.render.render(write_still=True)


def composite_sheet():
    from PIL import Image, ImageDraw, ImageFont
    labels = [
        ("v1_front34.png",    "1 · Front-Left 3/4 Hero (Pink Supercar + Hood + Door + Webcam)"),
        ("v2_hood_macro.png", "2 · Front Hood Mural ('Say no to drugs.' Portrait)"),
        ("v3_side_left.png",  "3 · Driver Side (+Y) Profile ('It's not pink' Left-to-Right)"),
        ("v4_side_right.png", "4 · Passenger Side (-Y) Profile ('It's not pink' Left-to-Right)"),
        ("v5_webcam.png",     "5 · Roof Webcam Macro (Clip Claw + Coated Lens + LIVE LED + USB Cord)"),
        ("v6_rear_scissor.png","6 · Rear 3/4 Showoff (Scissor Doors Open + V12 + GT Wing + 'NOT PINK')"),
    ]
    cw, ch = 960, 640
    sheet = Image.new("RGB", (cw * 2, ch * 3), (12, 14, 22))
    d = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 24)
    except Exception:
        fnt = ImageFont.load_default()

    for idx, (fn, title) in enumerate(labels):
        col, row = idx % 2, idx // 2
        px, py = col * cw, row * ch
        im = Image.open(os.path.join(OUT_DIR, fn)).convert("RGB")
        sheet.paste(im, (px, py))
        d.rectangle([px, py, px + cw - 1, py + 44], fill=(10, 14, 24))
        d.text((px + 16, py + 8), title, font=fnt, fill=(255, 130, 195))
        d.rectangle([px, py, px + cw - 1, py + ch - 1], outline=(55, 65, 90), width=2)

    out_p = os.path.join(OUT_DIR, "pink_supercar_renders.png")
    sheet.save(out_p, "PNG", optimize=True)
    print(f"Wrote verification sheet: {out_p}")


if __name__ == "__main__":
    if "--composite" in sys.argv:
        composite_sheet()
    else:
        run_blender()
