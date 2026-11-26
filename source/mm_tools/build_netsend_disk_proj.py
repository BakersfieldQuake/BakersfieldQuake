"""THE DISK projectile: progs/netsend_disk.md3 + progs/netsend_disk.png rebuilt to match the held disk in the new
viewmodel (build_netsend_disk_view.py): a blue 3.5" floppy labelled THE DISK, textured from the user's own video
frames (front from v1 f240, back from v2 f90; each face rectified, the glove inpainted out, a little cleanup).

Same atlas layout as before, so netsend_pc.md3's slot/floor disk (which shares the progs/netsend_disk shader) turns
blue too:  Q1 front (label side), Q2 back (hub side), Q3 metal shutter, Q4 plastic rim.
Same frame map as before:  0 flying flat (label up), 1 stuck in the floor at an angle, 2-7 trembling there.
New mesh: rounded corners, the 45-degree corner notch, a recessed label well and a shutter sized like the video's.

python3 build_netsend_disk_proj.py [--videos DIR] [--out MODDIR] [--json PREVIEW_JSON]
"""
import argparse
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import disk_keyer as dk  # noqa: E402
import md3lib  # noqa: E402
from build_netsend_disk_view import VIDEO_DIR, VIDEO_NAMES  # noqa: E402

TEX = 512
T = TEX // 2
DIM = 0.62           # baked dim, like the other netsend textures (rgbGen lightingDiffuse renders ~2x bright here)


def grab(video_dir, v, i):
    cap = cv2.VideoCapture(os.path.join(video_dir, VIDEO_NAMES[v]))
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ok, bgr = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("no frame %s:%d" % (v, i))
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def rectify_face(rgb, size, back=False):
    """The disk's face, perspective-corrected to size x size (top = the shutter edge), with the glove inpainted."""
    hull = dk.disk_hull(rgb)
    ys, xs = np.nonzero(hull > 0.5)
    rect = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))
    box = cv2.boxPoints(rect)
    # order: top-left, top-right, bottom-right, bottom-left (image space)
    s = box.sum(axis=1)
    d = np.diff(box, axis=1).ravel()
    tl, br = box[np.argmin(s)], box[np.argmax(s)]
    tr, bl = box[np.argmin(d)], box[np.argmax(d)]
    src = np.float32([tl, tr, br, bl])
    dst = np.float32([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]])
    mtx = cv2.getPerspectiveTransform(src, dst)
    face = cv2.warpPerspective(rgb, mtx, (size, size), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # the glove: the big dark blob touching the right or bottom edge (the label's black letters never touch an edge)
    hsv = cv2.cvtColor(face, cv2.COLOR_RGB2HSV)
    dark = ((hsv[..., 2] < 95) & (hsv[..., 1] < 120)).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(dark, 8)
    glove = np.zeros_like(dark)
    for k in range(1, n):
        x, y, w, h, a = stats[k]
        if a > size * size * 0.01 and (x + w >= size - 2 or y + h >= size - 2):
            glove |= (lbl == k).astype(np.uint8)
    # anything outside the disk (backdrop past a rounded corner) too
    outside = (hsv[..., 1] < 40) & (hsv[..., 2] > 200)
    edge = np.zeros_like(dark)
    edge[:4, :] = edge[-4:, :] = edge[:, :4] = edge[:, -4:] = 1
    n2, lbl2, _, _ = cv2.connectedComponentsWithStats(outside.astype(np.uint8), 8)
    out_ids = np.unique(lbl2[edge > 0])
    outside = np.isin(lbl2, out_ids[out_ids > 0])
    mask = cv2.dilate(glove | outside.astype(np.uint8), np.ones((9, 9), np.uint8))
    face = cv2.inpaint(face, mask * 255, 9, cv2.INPAINT_TELEA)
    return face, mask


def plastic_noise(h, w, seed):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((h // 4, w // 4)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(n, (0, 0), 1.2)


def build_texture(video_dir):
    front, fmask = rectify_face(grab(video_dir, "v1", 240), T)
    back, bmask = rectify_face(grab(video_dir, "v2", 90), T)

    # the glove also hid the label's lower-right corner: the label is a rectangle, so rebuild that corner from its
    # own paper mirrored left-right (the lettering sits higher up, the mirrored strip is blank paper)
    hsv = cv2.cvtColor(front, cv2.COLOR_RGB2HSV)
    paper = (hsv[..., 0] >= 8) & (hsv[..., 0] <= 30) & (hsv[..., 1] >= 25) & (hsv[..., 1] <= 120) & (hsv[..., 2] > 140) & (fmask == 0)
    paper = cv2.morphologyEx(paper.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(paper, 8)
    if n > 1:
        k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        x, y, w, h = stats[k, :4]
        # the visible part may stop at the glove: the label's right edge mirrors its left edge about the face centre
        x1 = max(x + w, T - x)
        lab = front[y:y + h, x:x1].copy()
        hole = fmask[y:y + h, x:x1] > 0
        mirrored = lab[:, ::-1]
        mirrored_ok = (fmask[y:y + h, x:x1][:, ::-1] == 0)
        lab[hole & mirrored_ok] = mirrored[hole & mirrored_ok]
        front[y:y + h, x:x1] = lab
        fmask[y:y + h, x:x1][hole & mirrored_ok] = 0

    # the inpainted corners are smeary: replace those pixels with the face's own median plastic blue + grain
    for face, mask, seed in ((front, fmask, 3), (back, bmask, 4)):
        hsv = cv2.cvtColor(face, cv2.COLOR_RGB2HSV)
        blue = (hsv[..., 0] > 100) & (hsv[..., 0] < 125) & (hsv[..., 1] > 120) & (mask == 0)
        med = np.median(face[blue], axis=0)
        grain = plastic_noise(T, T, seed)[..., None] * 6.0
        fill = np.clip(med[None, None, :] + grain, 0, 255)
        m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2.0)[..., None]
        # keep the inpaint only where it is blue-ish already (it continues the edges); else plain plastic
        face[:] = np.clip(face * (1 - m) + fill * m, 0, 255).astype(np.uint8)

    atlas = np.zeros((TEX, TEX, 3), np.uint8)
    atlas[:T, :T] = front
    atlas[:T, T:] = back

    # Q3 the metal shutter: the front's own shutter strip, widened to fill the tile
    sh = front[int(T * 0.0):int(T * 0.33), int(T * 0.25):int(T * 0.75)]
    atlas[T:, :T] = cv2.resize(sh, (T, T), interpolation=cv2.INTER_CUBIC)

    # Q4 the rim: the plastic blue, darker, with a moulding line
    hsv = cv2.cvtColor(front, cv2.COLOR_RGB2HSV)
    blue = (hsv[..., 0] > 100) & (hsv[..., 0] < 125) & (hsv[..., 1] > 120)
    med = np.median(front[blue], axis=0) * 0.78
    rim = np.clip(med[None, None, :] + plastic_noise(T, T, 9)[..., None] * 5.0, 0, 255)
    rim[T // 2 - 2:T // 2 + 2] *= 0.8
    atlas[T:, T:] = rim.astype(np.uint8)

    # the in-game version is baked dim; a mild unsharp keeps the label crisp at a distance
    blur = cv2.GaussianBlur(atlas.astype(np.float32), (0, 0), 1.0)
    sharp = np.clip(atlas + 0.4 * (atlas - blur), 0, 255)
    return sharp.astype(np.uint8)


# ---------------------------------------------------------------- the mesh
def mesh(half_w=4.2, half_h=4.45, half_t=0.28):
    """Local space: front (label) faces -X, back +X, the shutter edge +Z, the notch at the top-right of the front
    (y = -W). UVs: front Q1, back Q2 (mirrored), shutter Q3, rim Q4."""
    W, H, Tt = half_w, half_h, half_t
    r = 0.35               # rounded corner radius
    cham = W * 0.16        # the 45-degree notch
    verts, norms, st, tris = [], [], [], []

    # outline (y, z), clockwise seen from the front (-X): rounded corners + the notch
    def arc(cy, cz, a0, a1, n=4):
        return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                 cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    outline = []
    outline += arc(W - r, H - r, 0, 90)                     # top-left (+y is the viewer's left)
    outline += [(-W + cham, H), (-W, H - cham)]               # the notch, top-right
    outline += arc(-W + r, -H + r, 180, 270)                # bottom-right
    outline += arc(W - r, -H + r, 270, 360)                 # bottom-left
    # orient clockwise from the front: (+y,+z) -> (-y,+z) -> (-y,-z) -> (+y,-z)
    outline = [outline[i] for i in range(len(outline))]

    def uvf(y, z):
        return (0.006 + 0.488 * ((W - y) / (2 * W)), 0.006 + 0.488 * ((H - z) / (2 * H)))

    def uvb(y, z):
        return (0.506 + 0.488 * ((y + W) / (2 * W)), 0.006 + 0.488 * ((H - z) / (2 * H)))

    def fan(x, nx, uvfn, flip):
        c = len(verts)
        verts.append((x, 0.0, 0.0)); norms.append((nx, 0, 0)); st.append(uvfn(0, 0))
        for y, z in outline:
            verts.append((x, y, z)); norms.append((nx, 0, 0)); st.append(uvfn(y, z))
        m = len(outline)
        for i in range(m):
            j = (i + 1) % m
            tris.append((c, c + 1 + j, c + 1 + i) if not flip else (c, c + 1 + i, c + 1 + j))

    fan(-Tt, -1.0, uvf, False)
    fan(+Tt, +1.0, uvb, True)
    m = len(outline)
    for i in range(m):
        j = (i + 1) % m
        y0, z0 = outline[i]
        y1, z1 = outline[j]
        nrm = (0.0, z1 - z0, -(y1 - y0))
        ln = math.hypot(nrm[1], nrm[2]) or 1.0
        nrm = (0.0, nrm[1] / ln, nrm[2] / ln)
        c = len(verts)
        for p, uv in (((-Tt, y0, z0), (0.53, 0.53)), ((-Tt, y1, z1), (0.97, 0.53)),
                      ((Tt, y1, z1), (0.97, 0.97)), ((Tt, y0, z0), (0.53, 0.97))):
            verts.append(p); norms.append(nrm); st.append(uv)
        tris += [(c, c + 1, c + 2), (c, c + 2, c + 3)]

    # the shutter: a thin box proud of both faces over the top middle (the video's shutter: 25%..75% across, top third)
    sy0, sy1 = W - 2 * W * 0.75, W - 2 * W * 0.25
    sz0, sz1 = H - 2 * H * 0.33, H + 0.02
    sx = Tt + 0.05

    def quad(p, n, uv):
        c = len(verts)
        for k in range(4):
            verts.append(p[k]); norms.append(n); st.append(uv[k])
        tris.extend([(c, c + 1, c + 2), (c, c + 2, c + 3)])
    q3 = [(0.01, 0.51), (0.49, 0.51), (0.49, 0.99), (0.01, 0.99)]
    quad([(-sx, sy1, sz1), (-sx, sy0, sz1), (-sx, sy0, sz0), (-sx, sy1, sz0)], (-1, 0, 0), q3)              # front
    quad([(sx, sy0, sz1), (sx, sy1, sz1), (sx, sy1, sz0), (sx, sy0, sz0)], (1, 0, 0), q3)                   # back
    quad([(-sx, sy0, sz1), (-sx, sy1, sz1), (sx, sy1, sz1), (sx, sy0, sz1)], (0, 0, 1),
         [(0.05, 0.52), (0.45, 0.52), (0.45, 0.56), (0.05, 0.56)])                                         # top
    for yy, ny in ((sy0, -1), (sy1, 1)):
        quad([(-sx, yy, sz1), (sx, yy, sz1), (sx, yy, sz0), (-sx, yy, sz0)], (0, ny, 0),
             [(0.05, 0.52), (0.08, 0.52), (0.08, 0.9), (0.05, 0.9)])
    return verts, norms, st, tris


def rot(p, ax, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    x, y, z = p
    if ax == "x":
        return (x, y * c - z * s, y * s + z * c)
    if ax == "y":
        return (x * c + z * s, y, -x * s + z * c)
    return (x * c - y * s, x * s + y * c, z)


def frames_for(verts, norms):
    out = []
    for f in range(8):
        vv, nn = [], []
        for p, n in zip(verts, norms):
            if f == 0:          # flying flat, the label up
                q, qn = rot(p, "y", 90.0), rot(n, "y", 90.0)
            else:               # stuck in the floor at an angle, then trembling (as before)
                tr = 0.0 if f == 1 else 3.8 * math.sin(f * 2.4)
                ty = 0.0 if f == 1 else 0.35 * math.cos(f * 3.1)
                q = rot(rot(rot(p, "z", 180.0), "y", -22.0), "x", 12.0 + tr)
                qn = rot(rot(rot(n, "z", 180.0), "y", -22.0), "x", 12.0 + tr)
                q = (q[0], q[1] + ty, q[2] + 3.65)
            vv.append(q)
            nn.append(qn)
        out.append((vv, nn))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", default=VIDEO_DIR)
    ap.add_argument("--out", default=os.path.join(REPO, "build", "netsend_disk", "game"))
    ap.add_argument("--json", default=os.path.join(REPO, "build", "netsend_disk", "disk_proj.json"))
    args = ap.parse_args()

    atlas = build_texture(args.videos)
    progs = os.path.join(args.out, "progs")
    os.makedirs(progs, exist_ok=True)
    full = os.path.join(os.path.dirname(args.json), "netsend_disk_full.png")
    cv2.imwrite(full, cv2.cvtColor(atlas, cv2.COLOR_RGB2BGR))
    game = np.clip(np.round(atlas.astype(np.float32) * DIM), 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(progs, "netsend_disk.png"), cv2.cvtColor(game, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_PNG_COMPRESSION, 9])

    verts, norms, st, tris = mesh()
    surf = dict(name="netsend_disk", shader="progs/netsend_disk", tris=tris, st=st, frames=frames_for(verts, norms))
    md3lib.write(os.path.join(progs, "netsend_disk.md3"), dict(name="netsend_disk", surfaces=[surf], nframes=8))
    # for the preview's WebGL turntable: the un-rotated mesh
    with open(args.json, "w") as f:
        fr = frames_for(verts, norms)
        json.dump(dict(st=[[round(c, 5) for c in t] for t in st], tris=tris,
                       frames=[dict(v=[[round(c, 4) for c in v] for v in fr[i][0]],
                                    n=[[round(c, 4) for c in n] for n in fr[i][1]]) for i in (0, 1)]), f)
    print("netsend_disk.md3: %d verts, %d tris, 8 frames; texture %dx%d -> %s" % (len(verts), len(tris), TEX, TEX, progs))


if __name__ == "__main__":
    main()
