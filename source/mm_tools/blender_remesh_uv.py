"""Headless Blender 5.2 Remesh + Smooth + Decimate + Smart UV Unwrap helper.

Usage:
  blender.exe -b -P blender_remesh_uv.py -- <in_quads.npz> <out_mesh.npz> <voxel_size> <tri_budget>
"""
import math
import sys
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
IN_NPZ = argv[0]
OUT_NPZ = argv[1]
VOXEL_SIZE = float(argv[2]) if len(argv) > 2 else 0.34
TRI_BUDGET = int(argv[3]) if len(argv) > 3 else 3350

data = np.load(IN_NPZ)
verts = data["verts"].astype(np.float32)
faces = data["faces"].astype(np.int32)

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("hull")
me.vertices.add(len(verts))
me.vertices.foreach_set("co", verts.ravel())
me.loops.add(len(faces) * 4)
me.loops.foreach_set("vertex_index", faces.ravel())
me.polygons.add(len(faces))
me.polygons.foreach_set("loop_start", (np.arange(len(faces), dtype=np.int32) * 4))
me.polygons.foreach_set("loop_total", np.full(len(faces), 4, dtype=np.int32))
me.update(calc_edges=True)

obj = bpy.data.objects.new("rider_human", me)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# 1. Voxel Remesh into clean isotropic manifold surface
m_rm = obj.modifiers.new("rm", "REMESH")
m_rm.mode = "VOXEL"
m_rm.voxel_size = VOXEL_SIZE
m_rm.adaptivity = 0.0
bpy.ops.object.modifier_apply(modifier="rm")

# 2. Smooth organic surface before decimation so normals and UV islands stay contiguous & clean
m_sm = obj.modifiers.new("sm", "SMOOTH")
m_sm.factor = 0.50
m_sm.iterations = 8
bpy.ops.object.modifier_apply(modifier="sm")

# 3. Ensure consistent outward normals
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Decimate to game-ready MD3 single-surface budget (~3450 tris -> ~2800 UV-split verts < 4096 limit!)
cur_tris = len(obj.data.polygons) * 2
if cur_tris > TRI_BUDGET:
    m_dec = obj.modifiers.new("dec", "DECIMATE")
    m_dec.ratio = min(1.0, float(TRI_BUDGET) / float(max(1, cur_tris)))
    bpy.ops.object.modifier_apply(modifier="dec")

# 5. Triangulate & Smart UV Project with large contiguous islands (82 deg) & clean margin
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(82.0), island_margin=0.006, area_weight=0.25)
bpy.ops.object.mode_set(mode="OBJECT")

# Shade smooth for clean vertex normals
for poly in obj.data.polygons:
    poly.use_smooth = True

lme = obj.data
lme.calc_loop_triangles()
uvl = lme.uv_layers.active

nv = len(lme.vertices)
vp = np.zeros(nv * 3, dtype=np.float32)
lme.vertices.foreach_get("co", vp)
vp = vp.reshape(nv, 3)

vn = np.zeros(nv * 3, dtype=np.float32)
lme.vertices.foreach_get("normal", vn)
vn = vn.reshape(nv, 3)

# Also compute heavily smoothed normals for view-selection weighting (prevents noisy creases from switching cameras mid-cheek!)
m_pick = obj.modifiers.new("pick", "SMOOTH")
m_pick.factor = 1.0
m_pick.iterations = 45
dg = bpy.context.evaluated_depsgraph_get()
sme = obj.evaluated_get(dg).to_mesh()
vn_smooth = np.zeros(nv * 3, dtype=np.float32)
sme.vertices.foreach_get("normal", vn_smooth)
vn_smooth = vn_smooth.reshape(nv, 3)
obj.evaluated_get(dg).to_mesh_clear()
obj.modifiers.remove(m_pick)

tri_v = np.array([lt.vertices[:] for lt in lme.loop_triangles], dtype=np.int32)
tri_uv = np.array([[uvl.data[li].uv[:] for li in lt.loops] for lt in lme.loop_triangles], dtype=np.float32)

print(f"BLENDER_REMESH_UV DONE: {nv} verts, {len(tri_v)} tris")
np.savez_compressed(
    OUT_NPZ,
    verts=vp,
    norms=vn,
    norms_smooth=vn_smooth,
    tris=tri_v,
    tri_uv=tri_uv,
)
