"""The standing Pickle Surprise as a real 3D model (progs/pickle.md3 + progs/pickle3d.png), rebuilt from the 16 turntable
cut-outs (progs/pickle_00..15.png: one turn of the pickle in 22.5 degree steps) by carving a voxel visual hull, then marching cubes,
a little smoothing, and the photo projected back on from the best-facing view.

Same box as the old flat card: 20 units tall (512 px of the cut-outs), centred on the origin, the face looks along -X, picture-left
is +Y, up is +Z, so the game code that turns and sways the card does the same to this.  Frame 9 of the video is a bad cut-out
(a smear), so it is left out of the carving and the texture.

python make_pickle3d.py [progs_dir]       (needs numpy, scipy, scikit-image, PIL; run it without -I)"""
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

PROGS = sys.argv[1] if len(sys.argv) > 1 else r"G:\Quake\Combat\BakersfieldQuake\progs"
N = 16
BAD = {9}
GOOD = [k for k in range(N) if k not in BAD]
UNIT = 20.0 / 512.0                       # game units per pixel
C = 256.0                                 # the picture's centre, where the turntable axis and the origin are
STEP = 2.0                                # voxel size, px
CROP = (148, 16, 364, 496)                # the box each texture tile is cut from (x0, y0, x1, y1)
TILE_W, TILE_H = CROP[2] - CROP[0], CROP[3] - CROP[1]
COLS = 5


def load():
    ims, masks = [], []
    for k in range(N):
        im = Image.open(os.path.join(PROGS, "pickle_%02d.png" % k)).convert("RGBA")
        ims.append(np.array(im))
        a = np.array(im.getchannel("A")) > 128
        masks.append(ndimage.binary_dilation(a, iterations=2))     # a little slack: the cut-out is a touch tight
    return ims, masks


def project(p, k, sgn):
    """object-space points (n,3) in px -> picture (u, v) of turntable frame k"""
    phi = math.radians(sgn * k * 360.0 / N)
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    yr = x * math.sin(phi) + y * math.cos(phi)          # the object turned by phi about Z; the camera looks along +X
    return C - yr, C - z


def carve(masks, sgn):
    xs = np.arange(-110, 110 + STEP, STEP)
    ys = np.arange(-110, 110 + STEP, STEP)
    zs = np.arange(-250, 250 + STEP, STEP)
    gx, gy, gz = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], 1)
    cnt = np.zeros(len(pts), np.int16)
    for k in GOOD:
        u, v = project(pts, k, sgn)
        ui, vi = np.round(u).astype(int), np.round(v).astype(int)
        ok = (ui >= 0) & (ui < 512) & (vi >= 0) & (vi < 512)
        ins = np.zeros(len(pts), bool)
        ins[ok] = masks[k][vi[ok], ui[ok]]
        cnt += ins
    vol = (cnt >= len(GOOD) - 1).reshape(gx.shape)       # inside nearly all of them (one bad view is forgiven)
    return vol, (xs, ys, zs)


def smooth_mesh(verts, faces, iters=4, lam=0.5, mu=-0.53):
    """Taubin smoothing (a shrink step and a slightly bigger grow step, so the pickle keeps its size)"""
    from scipy import sparse
    n = len(verts)
    rows = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2], faces[:, 1], faces[:, 2], faces[:, 0]])
    cols = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0], faces[:, 0], faces[:, 1], faces[:, 2]])
    adj = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    adj.data[:] = 1.0
    deg = np.maximum(np.asarray(adj.sum(1)).ravel(), 1.0)[:, None]
    v = verts.copy()
    for _ in range(iters):
        for f in (lam, mu):
            v = v + f * ((adj @ v) / deg - v)
    return v


def main():
    ims, masks = load()
    # The video turns the pickle so its face goes to picture-LEFT (+Y) as the frames go on (frames 4..7 show it looking left),
    # which is a turn of -22.5 degrees per frame in the frame used here. (The silhouettes alone can not tell: the hull has the
    # same volume either way, it only comes out mirrored.)
    sgn = -1
    vol, (xs, ys, zs) = carve(masks, sgn)
    print("hull:", int(vol.sum()), "voxels")
    vol = ndimage.binary_closing(vol, iterations=1)
    lab, nlab = ndimage.label(vol)
    if nlab > 1:
        sizes = ndimage.sum(vol, lab, range(1, nlab + 1))
        vol = lab == (1 + int(np.argmax(sizes)))
    field = ndimage.gaussian_filter(vol.astype(np.float32), 1.0)
    verts, faces, _, _ = measure.marching_cubes(field, 0.5, spacing=(STEP, STEP, STEP), step_size=3)
    verts = verts + np.array([xs[0], ys[0], zs[0]])
    verts = smooth_mesh(verts, faces, iters=4)
    print("mesh:", len(verts), "verts", len(faces), "tris")

    # face normals, and which turntable frame sees each face best
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    fn = np.cross(b - a, c - a)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
    # make the normals point outward (away from the centre line) so lighting and texturing agree
    cen = (a + b + c) / 3
    flip = (fn[:, 0] * cen[:, 0] + fn[:, 1] * cen[:, 1]) < 0
    top = np.abs(cen[:, 2]) > 220
    flip &= ~top
    fn[flip] *= -1
    faces = faces.copy()
    faces[flip] = faces[flip][:, ::-1]
    cams = {}
    for k in GOOD:
        phi = math.radians(sgn * k * 360.0 / N)
        cams[k] = np.array([-math.cos(phi), math.sin(phi), 0.0])       # toward the camera, in object space
    score = np.stack([fn @ cams[k] for k in GOOD], 1)
    view = np.array(GOOD)[np.argmax(score, 1)]

    # texture atlas: a tile per good frame, transparent pixels filled with the nearest photo pixel (no black fringes)
    tiles = {}
    for i, k in enumerate(GOOD):
        t = ims[k][CROP[1]:CROP[3], CROP[0]:CROP[2]].astype(np.float32)
        opaque = t[..., 3] > 128
        idx = ndimage.distance_transform_edt(~opaque, return_distances=False, return_indices=True)
        t = t[idx[0], idx[1]]
        tiles[k] = (i, t[..., :3])
    rows = (len(GOOD) + COLS - 1) // COLS
    atlas = np.zeros((rows * TILE_H, COLS * TILE_W, 3), np.float32)
    for k, (i, t) in tiles.items():
        atlas[(i // COLS) * TILE_H:(i // COLS + 1) * TILE_H, (i % COLS) * TILE_W:(i % COLS + 1) * TILE_W] = t
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8)).save(os.path.join(PROGS, "pickle3d.png"))
    AW, AH = atlas.shape[1], atlas.shape[0]

    # one vertex per (vertex, frame) pair, so each frame's faces keep their own picture coordinates
    out_v, out_n, out_st, out_t, key = [], [], [], [], {}
    vn = np.zeros_like(verts)
    for f, n in zip(faces, fn):
        for vi in f:
            vn[vi] += n
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)
    for f, k in zip(faces, view):
        tri = []
        i, _ = tiles[k]
        for vi in f:
            kk = (int(vi), int(k))
            if kk not in key:
                p = verts[vi]
                u, v = project(p[None, :], k, sgn)
                tu = (i % COLS) * TILE_W + (u[0] - CROP[0])
                tv = (i // COLS) * TILE_H + (v[0] - CROP[1])
                key[kk] = len(out_v)
                out_v.append((p[0] * UNIT, p[1] * UNIT, p[2] * UNIT))
                out_n.append(tuple(vn[vi]))
                out_st.append((float(np.clip(tu / AW, 0, 1)), float(np.clip(tv / AH, 0, 1))))
            tri.append(key[kk])
        out_t.append((tri[0], tri[1], tri[2]))
    out_t += [(t[0], t[2], t[1]) for t in out_t]                       # both sides, like the card: it can not be seen through
    surf = dict(name="pickle", shader="progs/pickle3d", tris=out_t, st=out_st, frames=[(out_v, out_n)])
    path = os.path.join(PROGS, "pickle.md3")
    md3lib.write(path, dict(name="pickle", surfaces=[surf], nframes=1))
    mn = np.min(out_v, 0)
    mx = np.max(out_v, 0)
    print("wrote", path, len(out_v), "verts", len(out_t), "tris; size (units)", np.round(mx - mn, 2), "atlas", AW, "x", AH)


main()
