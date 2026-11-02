"""Blender: rebuilds John's flying head as a real 3D model from the MegaKart turntable clip (johnhead.mp4).

  1. silhouettes: green-keyed masks of every frame of the turn
  2. visual hull: voxels kept if they land inside the silhouette in >= KEEP of the views (the clip is not a rigid
     turntable: the head drifts and the hair moves, so each frame is re-aligned against the hull a few times)
  3. surface: voxel boundary -> remesh -> smooth -> decimated, UV unwrapped game mesh
  4. texture: every texel coloured from the frames that look at it most squarely (projected per texel)
  5. progs/johnhead3d.md3 + .png (face along +X, ~26 units wide) and a .glb for previews

blender -b -P build_john_head3d.py -- <frames.raw> <workdir> <progs_dir>
<frames.raw> = ffmpeg -i johnhead.mp4 -f rawvideo -pix_fmt rgb24 (145 frames of 736x400)"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

RAW, WORK, PROGS = sys.argv[sys.argv.index("--") + 1:][:3]
W, H, NF = 736, 400, 145
F = 2                      # silhouettes are worked at half resolution: 1 voxel = 2 source pixels
KEEP = 0.8                # fraction of views a voxel must be inside
LAND = [(16, 0.0), (54, 90.0), (84, 180.0), (106, 270.0), (130, 360.0)]   # 1-based frame -> turn angle
FRAMES = list(range(18, 131))   # the hair is still growing before ~18
TRI_BUDGET = 3500
WIDTH_UNITS = 26.0

os.makedirs(WORK, exist_ok=True)


def angle(f):
    for (f0, a0), (f1, a1) in zip(LAND, LAND[1:]):
        if f0 <= f <= f1:
            return a0 + (a1 - a0) * (f - f0) / (f1 - f0)
    return 0.0


# ---------------------------------------------------------------- 1. masks
print("loading frames")
vid = np.fromfile(RAW, dtype=np.uint8).reshape(NF, H, W, 3)
rgb = vid.astype(np.int16)
bg = (rgb[..., 1] > 80) & (rgb[..., 1] > rgb[..., 0] + 35) & (rgb[..., 1] > rgb[..., 2] + 35)
full = ~bg                                                   # NF x H x W, full res


def erode(m):
    o = m.copy()
    o[:, 1:, :] &= m[:, :-1, :]
    o[:, :-1, :] &= m[:, 1:, :]
    o[:, :, 1:] &= m[:, :, :-1]
    o[:, :, :-1] &= m[:, :, 1:]
    return o


def dilate(m):
    o = m.copy()
    o[:, 1:, :] |= m[:, :-1, :]
    o[:, :-1, :] |= m[:, 1:, :]
    o[:, :, 1:] |= m[:, :, :-1]
    o[:, :, :-1] |= m[:, :, 1:]
    return o


full = dilate(erode(erode(dilate(full))))                   # close specks, open spill
h2, w2 = H // F, W // F
small = full[:, :h2 * F, :w2 * F].reshape(NF, h2, F, w2, F).mean(axis=(2, 4)) > 0.5

idx = [f - 1 for f in FRAMES]
ang = np.radians(np.array([angle(f) for f in FRAMES]))
# initial alignment: silhouette centroids
cx = np.zeros(len(idx))
cz = np.zeros(len(idx))
for k, i in enumerate(idx):
    rr, cc = np.nonzero(small[i])
    cx[k], cz[k] = cc.mean(), rr.mean()

R = 125                    # half width of the voxel box (in half-res pixels)
ZH = 135                   # half height
X = np.arange(-R, R + 1, dtype=np.float32)
Y = np.arange(-R, R + 1, dtype=np.float32)
Zr = np.arange(-ZH, ZH + 1, dtype=np.float32)              # row offset (down = +)
XX, YY = np.meshgrid(X, Y, indexing="ij")


def carve(sign, cx, cz, keep=KEEP, ks=None):
    ks = range(len(idx)) if ks is None else ks
    cnt = np.zeros((len(X), len(Y), len(Zr)), dtype=np.uint16)
    for k in ks:
        i = idx[k]
        a = sign * ang[k]
        U = np.rint(cx[k] + XX * math.cos(a) - YY * math.sin(a)).astype(np.int32)
        V = np.rint(cz[k] + Zr).astype(np.int32)
        okU = (U >= 0) & (U < w2)
        okV = (V >= 0) & (V < h2)
        Uc = np.clip(U, 0, w2 - 1)
        Vc = np.clip(V, 0, h2 - 1)
        ins = small[i][Vc[None, None, :], Uc[:, :, None]] & okU[:, :, None] & okV[None, None, :]
        cnt += ins
    return cnt >= keep * len(ks)


def project(occ, sign, k, cx, cz):
    a = sign * ang[k]
    xi, yi, zi = np.nonzero(occ)
    U = np.rint(cx[k] + X[xi] * math.cos(a) - Y[yi] * math.sin(a)).astype(np.int32)
    V = np.rint(cz[k] + Zr[zi]).astype(np.int32)
    ok = (U >= 0) & (U < w2) & (V >= 0) & (V < h2)
    img = np.zeros((h2, w2), dtype=bool)
    img[V[ok], U[ok]] = True
    return img


# which way does the head turn? silhouettes cannot tell (the two answers are mirror images of each other), but the
# clip can: at +90 degrees (frame 54) the face points to SCREEN LEFT. The face is the -Y side (nearest the camera at
# angle 0); u = cx + X cos a - Y sin a puts -Y on the left at a = -90, so the turn runs with sign -1.
SIGN = -1
occ = carve(SIGN, cx, cz, 0.8)
print("turn sign", SIGN, "voxels", int(occ.sum()))

# re-align every frame against the hull, re-carve
for it in range(3):
    moved = 0
    for k, i in enumerate(idx):
        p = project(occ, SIGN, k, cx, cz)
        m = small[i]
        bestv, bd = -1, (0, 0)
        for dz in range(-5, 6):
            for dx in range(-8, 9):
                q = np.roll(np.roll(p, dz, axis=0), dx, axis=1)
                inter = np.logical_and(q, m).sum()
                uni = np.logical_or(q, m).sum()
                v = inter / max(1, uni)
                if v > bestv:
                    bestv, bd = v, (dx, dz)
        cx[k] -= bd[0]
        cz[k] -= bd[1]
        moved += abs(bd[0]) + abs(bd[1])
    occ = carve(SIGN, cx, cz)
    print("align pass", it, "shift total", moved, "voxels", int(occ.sum()))

# the clip is not rigid (the head tilts and bobs), so the full-turn hull eats the beard. The final shape is carved
# from the 8 key frames only, the same ones that paint it: seen from those angles the outline then matches the clip.
KEYS = [FRAMES.index(130)]
for t in range(45, 360, 45):
    KEYS.append(int(np.argmin(np.abs(np.degrees(ang) - t))))
# re-align the 8 key frames against each other: each frame in turn takes the shift (dx, dz) that leaves the
# fullest shared shape. Searched on a 2x coarser voxel grid; a dz shift is just a slice of a taller gather.
PAD = 24
Xc, Yc = X[::2], Y[::2]
XXc, YYc = np.meshgrid(Xc, Yc, indexing="ij")
Zc = Zr[::2]
ZcE = np.arange(Zc[0] - PAD, Zc[-1] + PAD + 1, 2, dtype=np.float32)   # PAD/2 extra coarse rows each side
EP = PAD // 2


def inside_c(k, dx, z):
    a = SIGN * ang[k]
    U = np.rint(cx[k] + dx + XXc * math.cos(a) - YYc * math.sin(a)).astype(np.int32)
    V = np.rint(cz[k] + z).astype(np.int32)
    okU = (U >= 0) & (U < w2)
    okV = (V >= 0) & (V < h2)
    return small[idx[k]][np.clip(V, 0, h2 - 1)[None, None, :], np.clip(U, 0, w2 - 1)[:, :, None]] & okU[:, :, None] & okV[None, None, :]


for it in range(3):
    total = 0
    for k in KEYS:
        A = np.ones((len(Xc), len(Yc), len(Zc)), dtype=bool)
        for j in KEYS:
            if j != k:
                A &= inside_c(j, 0, Zc)
        best = (-1, 0, 0)
        for dx in range(-14, 15):
            I = inside_c(k, dx, ZcE)
            for e in range(-EP, EP + 1):
                v = int(np.count_nonzero(A & I[:, :, EP + e:EP + e + len(Zc)]))
                if v > best[0]:
                    best = (v, dx, e)
        cx[k] += best[1]
        cz[k] += best[2] * 2         # slice +e = this frame read 2e half-pixel rows further down
        total += abs(best[1]) + abs(best[2])
    print("key align pass", it, "moved", total)
occ = carve(SIGN, cx, cz, 0.87, KEYS)       # one of the 8 may disagree (curls with gaps hide the beard from behind)
print("key-frame hull voxels", int(occ.sum()))
# DIAG: each key frame's silhouette (grey) with the hull's projection (white), centred on the alignment
tiles = []
for k in KEYS:
    m = small[idx[k]]
    pj = project(occ, SIGN, k, cx, cz)
    t = np.zeros((2 * ZH + 1, 2 * R + 1), dtype=np.uint8)
    for img_, val in ((m, 90), (pj & ~m, 255), (pj & m, 200)):
        rr, cc = np.nonzero(img_)
        rr2 = np.rint(rr - cz[k] + ZH).astype(int)
        cc2 = np.rint(cc - cx[k] + R).astype(int)
        ok = (rr2 >= 0) & (rr2 < t.shape[0]) & (cc2 >= 0) & (cc2 < t.shape[1])
        t[rr2[ok], cc2[ok]] = val
    tiles.append(t)
sheet = np.hstack(tiles)
with open(os.path.join(WORK, "diag_keys.pgm"), "wb") as fh:
    fh.write(b"P5 %d %d 255\n" % (sheet.shape[1], sheet.shape[0]))
    fh.write(sheet.tobytes())
bots = []
for k, i in enumerate(idx):
    rr, cc = np.nonzero(small[i])
    band = np.abs(cc - cx[k]) < 25
    bots.append(rr[band].max() - cz[k] if band.any() else 0)
bots = np.array(bots)
print("DIAG silhouette bottom below centre: p10 %.0f p20 %.0f p50 %.0f p90 %.0f" % tuple(np.percentile(bots, [10, 20, 50, 90])))
print("DIAG worst frames", [FRAMES[k] for k in np.argsort(bots)[:12]], np.sort(bots)[:12])
xi_, yi_, zi_ = np.nonzero(occ)
print("DIAG hull bottom below centre", Zr[zi_].max())
# keep the biggest blob only (flood fill from the centre of mass)
xi, yi, zi = np.nonzero(occ)
seed = (int(np.median(xi)), int(np.median(yi)), int(np.median(zi)))
if not occ[seed]:
    j = np.argmin((xi - seed[0]) ** 2 + (yi - seed[1]) ** 2 + (zi - seed[2]) ** 2)
    seed = (xi[j], yi[j], zi[j])
lab = np.zeros_like(occ)
lab[seed] = True
for _ in range(400):
    nl = lab.copy()
    nl[1:] |= lab[:-1]
    nl[:-1] |= lab[1:]
    nl[:, 1:] |= lab[:, :-1]
    nl[:, :-1] |= lab[:, 1:]
    nl[:, :, 1:] |= lab[:, :, :-1]
    nl[:, :, :-1] |= lab[:, :, 1:]
    nl &= occ
    if nl.sum() == lab.sum():
        break
    lab = nl
occ = lab
print("final voxels", int(occ.sum()))

# ---------------------------------------------------------------- 2. surface from the voxel boundary
p = np.pad(occ, 1)
NX, NY, NZ = p.shape
quads = []
for axis in range(3):
    a = np.take(p, range(0, p.shape[axis] - 1), axis=axis)
    b = np.take(p, range(1, p.shape[axis]), axis=axis)
    f = np.argwhere(a != b)
    # face between cell f and f+1 along axis, at corner coordinate f[axis]+1
    base = f.copy()
    base[:, axis] += 1
    o1 = [0, 0, 0]
    o2 = [0, 0, 0]
    ax1, ax2 = [d for d in range(3) if d != axis]
    c0 = base
    c1 = base.copy(); c1[:, ax1] += 1
    c2 = base.copy(); c2[:, ax1] += 1; c2[:, ax2] += 1
    c3 = base.copy(); c3[:, ax2] += 1
    quads.append(np.stack([c0, c1, c2, c3], axis=1))
quads = np.concatenate(quads)                       # n x 4 x 3 corner lattice coords
corners = quads.reshape(-1, 3)
key = (corners[:, 0] * (NY + 1) + corners[:, 1]) * (NZ + 1) + corners[:, 2]
uk, inv = np.unique(key, return_inverse=True)
cz_ = uk % (NZ + 1)
cy_ = (uk // (NZ + 1)) % (NY + 1)
cx_ = uk // ((NZ + 1) * (NY + 1))
# lattice -> head space: x right, y away from the camera at angle 0, z up
vx = X[0] - 1.5 + cx_
vy = Y[0] - 1.5 + cy_
vz = -(Zr[0] - 1.5 + cz_)
verts = np.stack([vx, vy, vz], axis=1).astype(np.float32)
faces = inv.reshape(-1, 4)
print("boundary mesh", len(verts), "verts", len(faces), "quads")

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("hull")
me.vertices.add(len(verts))
me.vertices.foreach_set("co", verts.ravel())
me.loops.add(len(faces) * 4)
me.loops.foreach_set("vertex_index", faces.ravel().astype(np.int32))
me.polygons.add(len(faces))
me.polygons.foreach_set("loop_start", (np.arange(len(faces)) * 4).astype(np.int32))
me.polygons.foreach_set("loop_total", np.full(len(faces), 4, dtype=np.int32))
me.update(calc_edges=True)
hi = bpy.data.objects.new("hi", me)
bpy.context.scene.collection.objects.link(hi)
bpy.context.view_layer.objects.active = hi
hi.select_set(True)
m = hi.modifiers.new("rm", "REMESH")
m.mode = "VOXEL"
m.voxel_size = 1.6
m2 = hi.modifiers.new("sm", "SMOOTH")
m2.factor = 0.6
m2.iterations = 6
bpy.ops.object.modifier_apply(modifier="rm")
bpy.ops.object.modifier_apply(modifier="sm")
me = hi.data
print("high mesh", len(me.vertices), "verts", len(me.polygons), "faces")

# ---------------------------------------------------------------- 3. the game mesh: decimated, unwrapped
bpy.ops.object.select_all(action="DESELECT")
hi.select_set(True)
bpy.context.view_layer.objects.active = hi
dm = hi.modifiers.new("dec", "DECIMATE")
dm.ratio = min(1.0, TRI_BUDGET / max(1, len(hi.data.polygons) * 2))
bpy.ops.object.modifier_apply(modifier="dec")
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
bpy.ops.object.mode_set(mode="OBJECT")
lo = hi
lo.name = "lo"
print("low mesh", len(lo.data.polygons), "tris")

# ---------------------------------------------------------------- 4. texture: each texel takes its colour from the frames
# that look at it most squarely (projected per texel, not per vertex, so the face stays as sharp as the clip)
TS = 1024
lme = lo.data
lme.calc_loop_triangles()
uvl = lme.uv_layers.active
nv = len(lme.vertices)
VP = np.zeros(nv * 3, dtype=np.float32)
lme.vertices.foreach_get("co", VP)
VP = VP.reshape(nv, 3)
VN = np.zeros(nv * 3, dtype=np.float32)
lme.vertices.foreach_get("normal", VN)
VN = VN.reshape(nv, 3)
sm = lo.modifiers.new("pick", "SMOOTH")
sm.factor = 1.0
sm.iterations = 80
dg = bpy.context.evaluated_depsgraph_get()
sme = lo.evaluated_get(dg).to_mesh()
VN = np.zeros(nv * 3, dtype=np.float32)
sme.vertices.foreach_get("normal", VN)
VN = VN.reshape(nv, 3)
lo.evaluated_get(dg).to_mesh_clear()
lo.modifiers.remove(sm)
TV = np.array([lt.vertices[:] for lt in lme.loop_triangles])
TUV = np.array([[uvl.data[li].uv[:] for li in lt.loops] for lt in lme.loop_triangles]) * TS
PP, NN, PX, PY = [], [], [], []
for t in range(len(TV)):
    a, b, c = TUV[t]
    x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int) - 1
    x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + 1
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, TS), min(y1, TS)
    if x1 <= x0 or y1 <= y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    v0, v1 = b - a, c - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-12:
        continue
    px_, py_ = gx - a[0], gy - a[1]
    d20 = px_ * v0[0] + py_ * v0[1]
    d21 = px_ * v1[0] + py_ * v1[1]
    l1 = (d11 * d20 - d01 * d21) / den
    l2 = (d00 * d21 - d01 * d20) / den
    l0 = 1 - l1 - l2
    ins = (l0 >= -0.05) & (l1 >= -0.05) & (l2 >= -0.05)
    if not ins.any():
        continue
    l0, l1, l2 = l0[ins], l1[ins], l2[ins]
    ia, ib, ic = TV[t]
    PP.append(l0[:, None] * VP[ia] + l1[:, None] * VP[ib] + l2[:, None] * VP[ic])
    NN.append(l0[:, None] * VN[ia] + l1[:, None] * VN[ib] + l2[:, None] * VN[ic])
    PX.append(gx[ins].astype(np.int32))
    PY.append(gy[ins].astype(np.int32))
P = np.concatenate(PP)
N = np.concatenate(NN)
N /= np.maximum(np.linalg.norm(N, axis=1), 1e-6)[:, None]
PX = np.concatenate(PX)
PY = np.concatenate(PY)
print("texels", len(P))

# the clip is not rigid, so blending many frames ghosts the face. 8 key views 45 degrees apart each own a big
# patch of the head (seen from that angle the model then matches that frame), feathered at the borders
print("key frames", [FRAMES[k] for k in KEYS])
acc = np.zeros((len(P), 3), dtype=np.float64)
wsum = np.zeros(len(P), dtype=np.float64)
sx, sy, sz = np.nonzero(occ & ~(np.roll(occ, 1, 0) & np.roll(occ, -1, 0) & np.roll(occ, 1, 1) & np.roll(occ, -1, 1)
                                  & np.roll(occ, 1, 2) & np.roll(occ, -1, 2)))
for k in KEYS:
    i = idx[k]
    a = SIGN * ang[k]
    ca, sa = math.cos(a), math.sin(a)
    U = np.rint(cx[k] + X[sx] * ca - Y[sy] * sa).astype(np.int32)
    V = np.rint(cz[k] + Zr[sz]).astype(np.int32)
    D = X[sx] * sa + Y[sy] * ca
    ok = (U >= 0) & (U < w2) & (V >= 0) & (V < h2)
    zb = np.full((h2, w2), 1e9, dtype=np.float32)
    np.minimum.at(zb, (V[ok], U[ok]), D[ok])
    u = cx[k] + P[:, 0] * ca - P[:, 1] * sa
    v = cz[k] - P[:, 2]
    d = P[:, 0] * sa + P[:, 1] * ca
    ny = N[:, 0] * sa + N[:, 1] * ca
    ui = np.clip(np.rint(u).astype(np.int32), 0, w2 - 1)
    vi = np.clip(np.rint(v).astype(np.int32), 0, h2 - 1)
    vis = d <= zb[vi, ui] + 3.0
    w = np.clip(-ny, 0, 1) ** 10 * vis
    fu = np.clip(np.rint(u * F).astype(np.int32), 0, W - 1)
    fv = np.clip(np.rint(v * F).astype(np.int32), 0, H - 1)
    w = w * full[i][fv, fu]
    acc += vid[i][fv, fu].astype(np.float64) * w[:, None]
    wsum += w
seen = wsum > 1e-9
col = np.zeros((len(P), 3))
col[seen] = acc[seen] / wsum[seen][:, None] / 255.0
col[~seen] = (0.22, 0.15, 0.10)                      # never seen squarely: dark hair brown
print("unseen texels", int((~seen).sum()), "of", len(P))

tex = np.zeros((TS, TS, 3), dtype=np.float32)
cov = np.zeros((TS, TS), dtype=bool)
tex[PY, PX] = col
cov[PY, PX] = True
for _ in range(6):                                   # bleed the islands outward so mip/filtering has no black seams
    acc2 = np.zeros_like(tex)
    n2 = np.zeros((TS, TS), dtype=np.float32)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        acc2 += np.roll(np.roll(tex * cov[..., None], dy, 0), dx, 1)
        n2 += np.roll(np.roll(cov.astype(np.float32), dy, 0), dx, 1)
    grow = (~cov) & (n2 > 0)
    tex[grow] = acc2[grow] / n2[grow][:, None]
    cov |= grow
img = bpy.data.images.new("johnhead3d", TS, TS)
img.pixels.foreach_set(np.dstack([tex, np.ones((TS, TS), dtype=np.float32)]).ravel())
img.filepath_raw = os.path.join(PROGS, "johnhead3d.png")
img.file_format = "PNG"
img.save()
mat_lo = bpy.data.materials.new("lo")
mat_lo.use_nodes = True
tn = mat_lo.node_tree.nodes.new("ShaderNodeTexImage")
tn.image = img
lo.data.materials.clear()
lo.data.materials.append(mat_lo)
print("texture saved")

# ---------------------------------------------------------------- 5. md3 + glb
lme = lo.data
lme.calc_loop_triangles()
uvl = lme.uv_layers.active
vs = np.array([v.co[:] for v in lme.vertices])
ctr = (vs.min(axis=0) + vs.max(axis=0)) / 2
scale = WIDTH_UNITS / (vs[:, 0].max() - vs[:, 0].min())
mv, mst, mn, mt, mp = [], [], [], [], {}
for lt in lme.loop_triangles:
    tri = []
    for li in lt.loops:
        vi = lme.loops[li].vertex_index
        uv = uvl.data[li].uv
        k = (vi, round(uv[0], 5), round(uv[1], 5))
        if k not in mp:
            mp[k] = len(mv)
            x, y, z = (np.array(lme.vertices[vi].co[:]) - ctr) * scale
            mv.append((-y, x, z))                    # face (-y) -> quake +X
            nx, ny, nz = lme.vertices[vi].normal[:]
            mn.append((-ny, nx, nz))
            mst.append((uv[0], 1.0 - uv[1]))
        tri.append(mp[k])
    mt.append(tuple(tri))
surf = dict(name="head", shader="progs/johnhead3d", tris=mt, st=mst, frames=[(mv, mn)])
md3lib.write(os.path.join(PROGS, "johnhead3d.md3"), dict(name="johnhead3d", surfaces=[surf], nframes=1))
print("md3", len(mv), "verts", len(mt), "tris")

bpy.ops.object.select_all(action="DESELECT")
lo.select_set(True)
bpy.context.view_layer.objects.active = lo
# glb with the baked texture through a principled shader
pr = mat_lo.node_tree.nodes.get("Principled BSDF")
if pr:
    mat_lo.node_tree.links.new(tn.outputs["Color"], pr.inputs["Base Color"])
bpy.ops.export_scene.gltf(filepath=os.path.join(WORK, "johnhead3d.glb"), export_format="GLB", use_selection=True)
print("DONE")
