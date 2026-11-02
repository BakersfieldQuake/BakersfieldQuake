"""Headless Blender 5.2 mesh carver & 3D Voronoi fracturer for megaman1.glb.

Imports megaman1.glb, preserves its 2048x2048 UV-mapped surface, decimates cleanly,
and uses bmesh.ops.bisect_plane + holes_fill to extract watertight, solid-capped 3D pieces:
  - wheel_left, wheel_right : Intact pneumatic tires + white dished rims + hub hardware (<= 3600 verts for MD3)
  - main_bar                : Brushed stainless steel central bar + bullet nose cone
  - rear_cap                : Blown-off black Delrin rear end-cap + collar ring
  - axle_left, axle_right   : Snapped cross-axle steel shafts + locknut collars
  - frag_00 .. frag_23      : 24 irregular 3D Voronoi-fractured shrapnel chunks carved directly
                              from the collar clamp, stainless bar casing, white steel rims,
                              ribbed rubber tires, hub boss, and valve/brass hardware.

Interior cut faces are tagged and finalized after all bisections per piece so there is zero
combinatorial cap subdivision, and UV-mapped into the unused right-hand strip (u = 0.90..0.98)
of the texture atlas according to material type:
  - steel  : v in [0.06, 0.24]
  - scorch : v in [0.31, 0.49]
  - rubber : v in [0.56, 0.74]
  - rim    : v in [0.80, 0.96]
"""
import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB_PATH = argv[0] if len(argv) > 0 else r"g:\Downloads\Telegram Desktop\megaman1.glb"
OUT_JSON = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "mm_fractured_parts.json")

MAT_UV_V = {
    "steel": (0.06, 0.24),
    "scorch": (0.31, 0.49),
    "rubber": (0.56, 0.74),
    "rim": (0.80, 0.96),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)

mesh_objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert len(mesh_objs) >= 1, "No mesh found in GLB"
src_obj = mesh_objs[0]
bpy.context.view_layer.objects.active = src_obj
src_obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Transform Blender glTF coords (X_bl=X_g, Y_bl=-Z_g, Z_bl=Y_g) -> Quake (+X=fwd, +Y=left, +Z=up) * 22.0
# det([[0,-22,0],[22,0,0],[0,0,22]]) = +22^3 > 0 (preserves outward normals & CCW winding!)
rot_m = Matrix((
    (0.0, -22.0,  0.0, 0.0),
    (22.0,  0.0,  0.0, 0.0),
    (0.0,   0.0, 22.0, 0.0),
    (0.0,   0.0,  0.0, 1.0),
))
src_obj.data.transform(rot_m)
src_obj.data.update()

bm_w = bmesh.new()
bm_w.from_mesh(src_obj.data)
bmesh.ops.remove_doubles(bm_w, verts=bm_w.verts[:], dist=0.002)
bm_w.to_mesh(src_obj.data)
bm_w.free()
src_obj.data.update()


def make_decimated_copy(obj, ratio, name):
    cp = obj.copy()
    cp.data = obj.data.copy()
    cp.name = name
    bpy.context.collection.objects.link(cp)
    mod = cp.modifiers.new(name="Dec", type="DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = ratio
    mod.delimit = {"UV"}
    mod.use_collapse_triangulate = True
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = cp.evaluated_get(depsgraph)
    baked_mesh = bpy.data.meshes.new_from_object(eval_obj)
    cp.modifiers.clear()
    cp.data = baked_mesh
    print(f"  {name}: {len(cp.data.polygons)} tris, {len(cp.data.vertices)} verts")
    return cp


# hi_obj (~10,800 tris -> ~3,600 verts per wheel, well inside MD3's 4096-vert single-surface limit!)
hi_obj = make_decimated_copy(src_obj, 0.065, "mm_hi")
bar_obj = make_decimated_copy(src_obj, 0.20, "mm_bar_hi")
lo_obj = make_decimated_copy(src_obj, 0.045, "mm_lo")

PIPE_MEAN = Vector((1.052, 0.136, 11.463))
PIPE_DIR = Vector((0.8221, -0.0009, -0.5693)).normalized()
AXLE_X = -1.424
AXLE_Z = 11.825


def extract_tagged_bm(obj):
    """Creates bmesh where all original exterior faces have custom int layer is_orig = 1."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    orig_layer = bm.faces.layers.int.new("is_orig")
    for f in bm.faces:
        f[orig_layer] = 1
    return bm


def bisect_slice(bm, plane_co, plane_no, keep_positive=True):
    """Slices bmesh by plane, discards one side, and fills cut holes (new faces get is_orig = 0)."""
    orig_layer = bm.faces.layers.int.get("is_orig")
    res = bmesh.ops.bisect_plane(
        bm,
        geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        dist=0.0005,
        plane_co=plane_co,
        plane_no=plane_no,
        use_snap_center=False,
        clear_outer=not keep_positive,
        clear_inner=keep_positive,
    )
    cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge) and e.is_valid]
    if cut_edges:
        fill_res = bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)
        new_faces = [f for f in fill_res.get("faces", []) if f.is_valid]
        if not new_faces:
            ed_res = bmesh.ops.edgeloop_fill(bm, edges=cut_edges)
            new_faces = [f for f in ed_res.get("faces", []) if f.is_valid]
        out_n = (-Vector(plane_no) if keep_positive else Vector(plane_no)).normalized()
        for f in new_faces:
            f[orig_layer] = 0
            f.normal_update()
            if f.normal.dot(out_n) < 0:
                f.normal_flip()


def finalize_caps(bm, mat_type="steel", jitter=0.08, rng=None):
    """Pokes & UV-maps all interior fracture cap faces (is_orig == 0) once at the end."""
    uv_layer = bm.loops.layers.uv.verify()
    orig_layer = bm.faces.layers.int.get("is_orig")
    cap_faces = [f for f in bm.faces if f.is_valid and f[orig_layer] == 0]
    if cap_faces:
        poke_res = bmesh.ops.poke(bm, faces=cap_faces)
        poked_faces = [f for f in poke_res.get("faces", []) if f.is_valid]
        for f in poked_faces:
            f[orig_layer] = 0
        if jitter > 0.0 and rng is not None:
            for v in poke_res.get("verts", []):
                if v.is_valid:
                    v.normal_update()
                    v.co += v.normal * rng.uniform(-jitter * 0.5, jitter)
        vmin, vmax = MAT_UV_V[mat_type]
        for f in poked_faces:
            f.normal_update()
            fn = f.normal
            up_ref = Vector((0, 0, 1)) if abs(fn.z) < 0.9 else Vector((1, 0, 0))
            t1 = fn.cross(up_ref).normalized()
            t2 = fn.cross(t1).normalized()
            fc = f.calc_center_median()
            for loop in f.loops:
                rel = loop.vert.co - fc
                su = 0.94 + max(-0.036, min(0.036, rel.dot(t1) * 0.009))
                sv = 0.5 * (vmin + vmax) + max(-(vmax - vmin) * 0.44, min((vmax - vmin) * 0.44, rel.dot(t2) * 0.013))
                loop[uv_layer].uv = (su, 1.0 - sv)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()


def bm_to_dict(bm, name, custom_center=None, custom_axes=None):
    if len(bm.faces) == 0 or len(bm.verts) < 4:
        return None
    uv_layer = bm.loops.layers.uv.verify()
    orig_layer = bm.faces.layers.int.get("is_orig")

    if custom_center is not None:
        ctr = Vector(custom_center)
    else:
        ctr = sum((v.co for v in bm.verts), Vector((0, 0, 0))) / len(bm.verts)

    if custom_axes is not None:
        ax_x, ax_y, ax_z = [Vector(a).normalized() for a in custom_axes]
    else:
        ax_x, ax_y, ax_z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

    v_map = {}
    verts, norms, uvs, tris = [], [], [], []
    for f in bm.faces:
        tri_idx = []
        fn = f.normal
        is_ext = (f[orig_layer] == 1) if orig_layer is not None else True
        for loop in f.loops:
            v = loop.vert
            vn = v.normal
            n_use = vn if (is_ext and vn.dot(fn) > 0.55) else fn
            p_rel = v.co - ctr
            lp = (round(p_rel.dot(ax_x), 4), round(p_rel.dot(ax_y), 4), round(p_rel.dot(ax_z), 4))
            ln = (round(n_use.dot(ax_x), 4), round(n_use.dot(ax_y), 4), round(n_use.dot(ax_z), 4))
            luv = loop[uv_layer].uv
            st = (round(float(luv.x), 5), round(1.0 - float(luv.y), 5))
            key = (lp, ln, st)
            idx = v_map.get(key)
            if idx is None:
                idx = len(verts)
                v_map[key] = idx
                verts.append(lp)
                norms.append(ln)
                uvs.append(st)
            tri_idx.append(idx)
        if len(tri_idx) == 3 and len({tri_idx[0], tri_idx[1], tri_idx[2]}) == 3:
            tris.append(tri_idx)

    vol = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        vol += (p[0]*(q[1]*r[2] - q[2]*r[1]) - p[1]*(q[0]*r[2] - q[2]*r[0]) + p[2]*(q[0]*r[1] - q[1]*r[0])) / 6.0

    return dict(
        name=name,
        origin=[round(ctr.x, 4), round(ctr.y, 4), round(ctr.z, 4)],
        axes=[[round(c, 5) for c in ax_x], [round(c, 5) for c in ax_y], [round(c, 5) for c in ax_z]],
        nv=len(verts),
        nt=len(tris),
        volume=round(vol, 2),
        verts=verts,
        norms=norms,
        uvs=uvs,
        tris=tris,
    )


parts_out = {}
rng = random.Random(2026)

# 1. Left & Right Wheels
for wname, y_cut, keep_pos in [("wheel_left", -10.70, False), ("wheel_right", 10.70, True)]:
    bm = extract_tagged_bm(hi_obj)
    bisect_slice(bm, (0.0, y_cut, 12.0), (0.0, 1.0, 0.0), keep_positive=keep_pos)
    finalize_caps(bm, mat_type="steel", jitter=0.06, rng=rng)
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    w_ctr = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * (min(zs) + max(zs)))
    parts_out[wname] = bm_to_dict(bm, wname, custom_center=w_ctr)
    bm.free()

# 2. Main Stainless Steel Bar
bar_x = PIPE_DIR
bar_y = Vector((0.0, 1.0, 0.0))
bar_y = (bar_y - bar_x * bar_y.dot(bar_x)).normalized()
bar_z = bar_x.cross(bar_y).normalized()
cap_cut_pt = PIPE_MEAN + PIPE_DIR * (-13.1)

bm_bar = extract_tagged_bm(bar_obj)
bisect_slice(bm_bar, (0.0, -1.98, 12.0), (0.0, 1.0, 0.0), keep_positive=True)
bisect_slice(bm_bar, (0.0,  1.98, 12.0), (0.0, 1.0, 0.0), keep_positive=False)
bisect_slice(bm_bar, cap_cut_pt, PIPE_DIR, keep_positive=True)
finalize_caps(bm_bar, mat_type="scorch", jitter=0.14, rng=rng)
ts = [(v.co - PIPE_MEAN).dot(bar_x) for v in bm_bar.verts]
bar_ctr = PIPE_MEAN + bar_x * (0.5 * (min(ts) + max(ts)))
parts_out["main_bar"] = bm_to_dict(bm_bar, "main_bar", custom_center=bar_ctr, custom_axes=(bar_x, bar_y, bar_z))
bm_bar.free()

# 3. Blown-Off Black Rear Cap
bm_cap = extract_tagged_bm(bar_obj)
bisect_slice(bm_cap, (0.0, -2.02, 12.0), (0.0, 1.0, 0.0), keep_positive=True)
bisect_slice(bm_cap, (0.0,  2.02, 12.0), (0.0, 1.0, 0.0), keep_positive=False)
bisect_slice(bm_cap, cap_cut_pt, PIPE_DIR, keep_positive=False)
finalize_caps(bm_cap, mat_type="scorch", jitter=0.12, rng=rng)
parts_out["rear_cap"] = bm_to_dict(bm_cap, "rear_cap", custom_axes=(bar_x, bar_y, bar_z))
bm_cap.free()

# 4. Snapped Left & Right Cross-Axle Rods
for aname, y_in, y_out, sgn in [("axle_left", -2.02, -10.70, -1), ("axle_right", 2.02, 10.70, +1)]:
    bm_ax = extract_tagged_bm(bar_obj)
    if sgn < 0:
        bisect_slice(bm_ax, (AXLE_X, y_in, AXLE_Z), (0.0, 1.0, 0.0), keep_positive=False)
        bisect_slice(bm_ax, (AXLE_X, y_out, AXLE_Z), (0.0, 1.0, 0.0), keep_positive=True)
    else:
        bisect_slice(bm_ax, (AXLE_X, y_in, AXLE_Z), (0.0, 1.0, 0.0), keep_positive=True)
        bisect_slice(bm_ax, (AXLE_X, y_out, AXLE_Z), (0.0, 1.0, 0.0), keep_positive=False)
    finalize_caps(bm_ax, mat_type="steel", jitter=0.06, rng=rng)
    parts_out[aname] = bm_to_dict(bm_ax, aname, custom_axes=((0, 1, 0), (-1, 0, 0), (0, 0, 1)))
    bm_ax.free()

# 5. 24 Random 3D Voronoi-Fractured Shrapnel Pieces
seeds = []
# 9 central collar / stainless pipe / axle-clamp seeds
for i in range(9):
    t_s = -10.5 + i * 2.7 + rng.uniform(-0.8, 0.8)
    ang = rng.uniform(0, 2 * math.pi)
    rad = rng.uniform(0.5, 1.8)
    pt = PIPE_MEAN + PIPE_DIR * t_s + bar_y * (math.cos(ang) * rad) + bar_z * (math.sin(ang) * rad)
    mtype = "scorch" if abs(t_s + 1.5) < 4.5 else "steel"
    seeds.append((pt, mtype, "metal"))

# 9 rubber tire tread/shoulder chunks
for i in range(9):
    sgn = -1.0 if i < 5 else 1.0
    ang = i * (2 * math.pi / 4.5) + rng.uniform(-0.2, 0.2)
    wy = sgn * (15.85 + rng.uniform(-2.6, 2.6))
    wx = -2.09 + math.cos(ang) * rng.uniform(9.2, 11.4)
    wz = 12.01 + math.sin(ang) * rng.uniform(9.2, 11.4)
    seeds.append((Vector((wx, wy, wz)), "rubber", "rubber"))

# 8 white steel rim + hub/zerk/valve shards
for i in range(8):
    sgn = -1.0 if i < 4 else 1.0
    ang = (i % 4) * (0.5 * math.pi) + 0.38 + rng.uniform(-0.18, 0.18)
    wy = sgn * (15.85 + rng.uniform(-2.2, 2.2))
    r_rim = 2.0 if i in (0, 4) else rng.uniform(3.6, 5.6)
    wx = -2.09 + math.cos(ang) * r_rim
    wz = 12.01 + math.sin(ang) * r_rim
    mtype = "steel" if r_rim < 2.8 else "rim"
    seeds.append((Vector((wx, wy, wz)), mtype, "rim" if mtype == "rim" else "metal"))

guard_dirs = [
    Vector((5.8, 0.9, -0.7)), Vector((-5.8, -0.8, 0.9)),
    Vector((0.7, 5.0, 0.8)),  Vector((-0.8, -5.0, -0.6)),
    Vector((-0.6, 0.8, 5.8)), Vector((0.9, -0.7, -5.8)),
]

frag_idx = 0
for si, (pt_i, mtype, phys_mat) in enumerate(seeds):
    if frag_idx >= 24:
        break
    bm_f = extract_tagged_bm(lo_obj)
    other_pts = [pt_j for sj, (pt_j, _, _) in enumerate(seeds) if sj != si and (pt_j - pt_i).length < 12.5]
    local_guards = [pt_i + gd + Vector((rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1))) for gd in guard_dirs]
    for pt_j in other_pts + local_guards:
        mid = 0.5 * (pt_i + pt_j)
        nrm = (pt_j - pt_i).normalized()
        bisect_slice(bm_f, mid, nrm, keep_positive=False)
        if len(bm_f.faces) == 0:
            break
    if len(bm_f.faces) >= 8:
        finalize_caps(bm_f, mat_type=mtype, jitter=0.16, rng=rng)
        fname = f"frag_{frag_idx:02d}"
        d = bm_to_dict(bm_f, fname)
        if d and d["nv"] >= 12 and d["nv"] <= 3800 and d["volume"] >= 3.5:
            d["phys_mat"] = phys_mat
            d["cut_mat"] = mtype
            parts_out[fname] = d
            frag_idx += 1
    bm_f.free()

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(parts_out, f, separators=(",", ":"))

print(f"\n=== EXPORTED {len(parts_out)} WATERTIGHT 3D PARTS (ALL <= 4096 MD3 LIMIT!) ===")
for k, v in parts_out.items():
    assert v["nv"] <= 4096, f"{k} exceeds MD3 vertex limit: {v['nv']}"
    assert v["volume"] > 0, f"{k} has non-positive volume: {v['volume']}"
    print(f"  {k:14s}: nv={v['nv']:4d}, nt={v['nt']:4d}, vol={v['volume']:8.1f}, orig={v['origin']}")
