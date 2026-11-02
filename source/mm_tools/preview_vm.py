"""blender -b -P preview_vm.py -- <previewdir> <outdir> <frame> [frame ...]
Renders the view model as the player would see it (eye at the origin, looking +X)."""
import bpy, math, sys, os

args = sys.argv[sys.argv.index("--") + 1:]
pdir, odir = args[0], args[1]
frames = [int(a) for a in args[2:]]
os.makedirs(odir, exist_ok=True)

for fr in frames:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.wm.obj_import(filepath=os.path.join(pdir, "f%02d.obj" % fr), forward_axis='Y', up_axis='Z')
    for ob in sc.objects:
        if ob.type != 'MESH':
            continue
        for p in ob.data.polygons:
            p.use_smooth = True
        ob.color = (0.8, 0.8, 0.85, 1) if "__mm" in ob.name else (0.15, 0.45, 0.95, 1)
        if ob.name.startswith(("wheelL", "wheelR")):
            ob.color = (0.06, 0.06, 0.06, 1)
        if ob.name.startswith(("palm", "finger", "thumb")):
            ob.color = (0.4, 0.75, 1.0, 1)
        if ob.name.startswith("cuff"):
            ob.color = (0.35, 0.85, 0.95, 1)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.location = (0, 0, 0)
    cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle = math.radians(80)
    cam.data.clip_start = 0.3
    sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'OBJECT'
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.filepath = os.path.join(odir, "vm_f%02d.png" % fr)
    # crosshair marker far down the view axis
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(0, 120, 0))
    bpy.context.object.color = (1, 0, 0, 1)
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)
