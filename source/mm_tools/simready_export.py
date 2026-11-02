"""Blender (5.x) side of the SimReady -> Quake prop pipeline: imports one SimReady USD asset, joins it, decimates it to
about TARGET triangles and writes its triangles per material as JSON (units: Quake units, 1 m = 39.37; origin at the
middle of the base) for simready_props.py to turn into an MD3 + textures.
blender -b --python simready_export.py -- <root .usd> <out .json> <target tris> [inst]   (inst: leave USD instances out)"""
import json
import sys

import bpy
import bmesh

argv = sys.argv[sys.argv.index("--") + 1:]
src, out, target = argv[0], argv[1], int(argv[2])
QU = 39.37

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.usd_import(filepath=src, support_scene_instancing=(len(argv) > 3 and argv[3] == "inst"))   # instanced parts as real meshes, unless "inst"
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for o in bpy.data.objects:
    o.select_set(o.type == "MESH")
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")      # parent empties carry scale/rotation: bake it in before joining
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
me = ob.data

# triangulate, then collapse-decimate to the target
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces)
before = len(bm.faces)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)      # welds the split seams so collapse can work across them
# drop loose bits too small to see at Quake scale (screws, rivets, label edges): islands under 2.5% of the size
bm.faces.index_update()
diag = max((max(v.co[k] for v in bm.verts) - min(v.co[k] for v in bm.verts)) for k in range(3))
seen = set()
kill = []
for f0 in bm.faces:
    if f0.index in seen:
        continue
    stack, island = [f0], []
    seen.add(f0.index)
    while stack:
        f = stack.pop()
        island.append(f)
        for e in f.edges:
            for g in e.link_faces:
                if g.index not in seen:
                    seen.add(g.index)
                    stack.append(g)
    vs = {v for f in island for v in f.verts}
    size = max(max(v.co[k] for v in vs) - min(v.co[k] for v in vs) for k in range(3))
    if size < diag * 0.025:
        kill += island
bm.faces.index_update()
bmesh.ops.delete(bm, geom=list(set(kill)), context="FACES")
bm.to_mesh(me)
bm.free()
for _ in range(4):                                           # collapse stalls on fine detail; go round again
    n = len(me.polygons)
    if n <= target * 1.15:
        break
    bak = me.copy()
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = max(0.02, target / n)
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    me = ob.data
    if any(max(v.co[k] for v in me.vertices) - min(v.co[k] for v in me.vertices) > diag * 1.03 for k in range(3)):
        ob.data = bak                                        # collapse flung vertices out (open sheets): undo, the grid clustering below takes over
        me = bak
        break
    if len(me.polygons) > n * 0.9:                           # no progress: grilles / wire mesh made of loose bits
        break
me = ob.data
if len(me.polygons) > target * 1.5:                          # open sheets / tubes: collapse can't touch the boundaries, so cluster vertices on a grid
    import numpy as np
    me.calc_loop_triangles()
    nv, nt = len(me.vertices), len(me.loop_triangles)
    co = np.empty(nv * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    tv = np.empty(nt * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", tv)
    tv = tv.reshape(-1, 3)
    lo = co.min(0)

    def cluster(cell):
        g = np.floor((co - lo) / cell).astype(np.int64)
        key = g[:, 0] + g[:, 1] * 100003 + g[:, 2] * 100003 * 100003
        _, first, inv = np.unique(key, return_index=True, return_inverse=True)
        a, b, c = inv[tv[:, 0]], inv[tv[:, 1]], inv[tv[:, 2]]
        return inv, first, int(((a != b) & (b != c) & (a != c)).sum())

    cell = diag / 200
    while True:
        inv, first, alive = cluster(cell)
        if alive <= target * 1.3 or cell > diag / 5:
            break
        cell *= 1.12
    mean = np.zeros((len(first), 3))
    cnt = np.zeros(len(first))
    np.add.at(mean, inv, co)
    np.add.at(cnt, inv, 1)
    mean /= cnt[:, None]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    rep = [bm.verts[int(i)] for i in first]
    tmap = {}
    for vi in range(nv):
        r = rep[inv[vi]]
        if bm.verts[vi] is not r:
            tmap[bm.verts[vi]] = r
    for k, r in enumerate(rep):
        r.co = mean[k]
    bmesh.ops.weld_verts(bm, targetmap=tmap)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
me = ob.data
me.calc_loop_triangles()

xs = [v.co.x for v in me.vertices]
ys = [v.co.y for v in me.vertices]
zs = [v.co.z for v in me.vertices]
cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)


def mat_info(m):
    """Colour map path (if any) and a flat base colour for one material."""
    info = {"name": m.name if m else "default", "image": None, "color": [0.6, 0.6, 0.6]}
    if not m or not m.use_nodes:
        if m:
            info["color"] = list(m.diffuse_color[:3])
        return info
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            bc = n.inputs["Base Color"]
            info["color"] = list(bc.default_value[:3])
            if bc.links:
                node = bc.links[0].from_node
                while node and node.type != "TEX_IMAGE" and node.inputs:
                    ins = [i for i in node.inputs if i.links]
                    node = ins[0].links[0].from_node if ins else None
                if node and node.type == "TEX_IMAGE" and node.image:
                    info["image"] = bpy.path.abspath(node.image.filepath, library=node.image.library)
    return info


uv = me.uv_layers.active.data if me.uv_layers.active else None
surfs = {}
for lt in me.loop_triangles:
    mi = lt.material_index
    s = surfs.setdefault(mi, {"keys": {}, "verts": [], "norms": [], "st": [], "tris": []})
    tri = []
    for li in lt.loops:
        vi = me.loops[li].vertex_index
        co = me.vertices[vi].co
        n = lt.normal if not lt.use_smooth else me.loops[li].normal
        t = uv[li].uv if uv else (0.0, 0.0)
        key = (vi, round(t[0], 4), round(t[1], 4), round(n[0], 2), round(n[1], 2), round(n[2], 2))
        if key not in s["keys"]:
            s["keys"][key] = len(s["verts"])
            s["verts"].append([(co.x - cx) * QU, (co.y - cy) * QU, (co.z - z0) * QU])
            s["norms"].append([n[0], n[1], n[2]])
            s["st"].append([t[0], 1.0 - t[1]])
        tri.append(s["keys"][key])
    s["tris"].append(tri)

res = {"tris_before": before, "tris": len(me.loop_triangles),
       "size": [(max(xs) - min(xs)) * QU, (max(ys) - min(ys)) * QU, (max(zs) - z0) * QU], "surfaces": []}
for mi, s in sorted(surfs.items()):
    m = me.materials[mi] if mi < len(me.materials) else None
    res["surfaces"].append({"material": mat_info(m), "verts": s["verts"], "norms": s["norms"], "st": s["st"], "tris": s["tris"]})
json.dump(res, open(out, "w"))
print("RESULT", before, "->", len(me.loop_triangles), "tris,", len(surfs), "surfaces, size", [round(v) for v in res["size"]])
