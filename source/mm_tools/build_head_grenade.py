"""JohnWave's head as the Quake grenade model (progs/grenade.mdl + grenade.mdl_0.tga).

The shape comes from the green-screen head photo (out/chars/ref/johnwave_head_green.jpg): every ring of the mesh is
as wide as the photo's outline at that height, the cross-sections are a flattish face in front and a rounder skull
behind, and a nose is pushed out where the photo has it.  The face is that photo seen straight on; the back of the
head comes from the suit back photo (colour-matched to the front hair), blended in over the ears.  The skin is a
cylindrical unwrap with the seam at the back of the head.  The model is centred so it tumbles about its middle.

python3 -E -P build_head_grenade.py [--preview DIR] [--out DIR] [--size UNITS] [--bright X]
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_char_models as B

ARG = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
OUT = ARG("--out", B.PROGS)
PREVIEW = ARG("--preview", None)
HEIGHT = float(ARG("--size", 22))        # quake units, top of the hair to the bottom of the beard
BRIGHT = float(ARG("--bright", 1.2))     # on top of the usual in-game skin darkening
FRONT = os.path.join(B.REF, "johnwave_head_green.jpg")

NH, MH = 28, 32                          # ring vertices (vertex 0 at the back of the head), rings (0 = chin)
SW, SKIN_H = 384, 256
TGA_MUL = 2
NOSE = (706, 432)                        # nose tip in the front photo


def smoothstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def bleed(rgb, m, erode=3):
    """replace everything outside the (eroded) mask by the nearest inside colour"""
    core = ndimage.binary_erosion(m, iterations=erode)
    idx = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    return rgb[idx[0], idx[1]]


def front_photo():
    rgb = np.asarray(Image.open(FRONT).convert("RGB")).astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    bg = (g > r + 25) & (g > b + 25)
    fg = ndimage.binary_opening(~bg, iterations=2)
    lab, n = ndimage.label(fg)
    m = lab == 1 + int(np.argmax(ndimage.sum(fg, lab, range(1, n + 1))))
    m = ndimage.binary_fill_holes(m)
    rgb[..., 1] = np.minimum(g, np.maximum(r, b))                  # despill: no green in hair or skin
    return bleed(rgb, m, 6), m


def outline(mask, y0, y1, n, sigma):
    """smoothed centre and half width of a mask at n rows from y0 (t=0) to y1 (t=1)"""
    ys = np.arange(mask.shape[0])
    has = mask.any(1)
    lo = mask.argmax(1).astype(float)
    hi = (mask.shape[1] - 1 - mask[:, ::-1].argmax(1)).astype(float)
    lo = np.interp(ys, ys[has], lo[has])
    hi = np.interp(ys, ys[has], hi[has])
    lo, hi = ndimage.gaussian_filter1d(lo, sigma), ndimage.gaussian_filter1d(hi, sigma)
    yt = y0 + (y1 - y0) * np.linspace(0, 1, n)
    return yt, np.interp(yt, ys, (lo + hi) / 2), np.interp(yt, ys, (hi - lo) / 2)


def hair_colour(rgb, m, y0, y1):
    sel = m.copy()
    sel[:y0], sel[y1:] = False, False
    px = rgb[sel]
    return np.median(px[px.mean(1) < 110], 0)


def build():
    frgb, fm = front_photo()
    ys = np.nonzero(fm)[0]
    ybot, ytop = ys.max() - 2.0, ys.min() + 3.0
    yt, cx, hw = outline(fm, ybot, ytop, MH, 5)
    hw = np.maximum(hw, 0.10 * hw.max())
    t = np.linspace(0, 1, MH)
    th = -np.pi / 2 + 2 * np.pi * np.arange(NH) / NH                # k=0 back of the head, k=NH/2 the face
    cs, sn = np.cos(th), np.sin(th)
    # depth: a flattish face in front; behind, the jaw/neck is shallow and the skull is deep
    db = 0.78 + 0.42 * smoothstep(0.18, 0.55, t)
    fr = np.sign(sn) * np.abs(sn) ** 0.75
    P = np.zeros((MH, NH, 3))
    P[..., 1] = cx[:, None] + hw[:, None] * cs[None]               # photo x (his left is +y)
    P[..., 0] = hw[:, None] * fr[None] * np.where(sn[None] > 0, 0.92, db[:, None])
    P[..., 2] = yt[:, None]                                         # photo row (flipped below)
    UVF = P[..., [1, 2]].copy()                                     # the front photo seen straight on
    # nose and a little brow, out along +x
    face = np.clip(sn, 0, 1)[None] ** 2
    g = np.exp(-(((UVF[..., 0] - NOSE[0]) / 20) ** 2 + ((UVF[..., 1] - NOSE[1]) / 36) ** 2))
    P[..., 0] += 30 * g * face
    g = np.exp(-(((UVF[..., 0] - NOSE[0]) / 70) ** 2 + ((UVF[..., 1] - 368) / 14) ** 2))
    P[..., 0] += 6 * g * face

    # back of the head from the suit back photo, the same heights in proportion, mirrored
    bk = B.Photo(B.SUIT["back"], B.SUIT["key"])
    byt, bcx, bhw = outline(bk.sil, 262.0, 58.0, MH, 4)
    # spread in angle, not projected: the back photo covers the sides too (a projection would smear its edge pixels)
    psi = np.angle(np.exp(1j * (th + np.pi / 2)))                   # 0 at the back, +-pi at the face
    side = np.sin(np.clip(0.65 * psi, -np.pi / 2, np.pi / 2))
    UVB = np.stack([bcx[:, None] - bhw[:, None] * side[None], np.repeat(byt[:, None], NH, 1)], -1)
    brgb = bleed(bk.rgb.astype(np.float32), bk.sil)
    fh = hair_colour(frgb, fm, int(ytop), int(ytop + 0.25 * (ybot - ytop)))
    bh = hair_colour(brgb, bk.sil, 60, 200)
    tint = np.clip((fh / fh.mean()) / (bh / bh.mean()), 0.92, 1.08)       # only a nudge in hue
    brgb *= (fh.mean() / bh.mean()) * tint

    # positions: z up, centred on the middle of the box, scaled to HEIGHT
    V = P.reshape(-1, 3).copy()
    V = np.vstack([V, [[0, cx[0], ybot + 2], [0, cx[-1], ytop - 1]]])
    V[:, 2] = -V[:, 2]
    lo, hi = V.min(0), V.max(0)
    V = (V - (lo + hi) / 2) * (HEIGHT / (hi[2] - lo[2]))
    return dict(V=V, UVF=UVF, UVB=UVB, front=frgb, back=brgb)


def skin(m, mul, gain):
    """cylindrical unwrap: each texel looked up in both photos through the mesh, blended over the ears"""
    W_, H_ = SW * mul, SKIN_H * mul
    kk = (np.arange(W_) + 0.5) / W_ * NH                            # column -> ring vertex (fractional)
    jj = np.maximum((1 - (np.arange(H_) + 0.5) / H_) * (MH - 1), 0.6)
    KK, JJ = np.meshgrid(kk, jj)
    out = np.zeros((H_, W_, 3), np.float32)
    wf = smoothstep(0.12, 0.42, np.sin(-np.pi / 2 + 2 * np.pi * KK / NH))
    for grid, rgb, w in ((m["UVF"], m["front"], wf), (m["UVB"], m["back"], 1 - wf)):
        g = np.concatenate([grid, grid[:, :1]], 1)                  # wrap column
        px = [ndimage.map_coordinates(g[..., c], [JJ, KK], order=1, mode="nearest") for c in range(2)]
        for c in range(3):
            out[..., c] += w * ndimage.map_coordinates(rgb[..., c], [px[1], px[0]], order=1, mode="nearest")
    return (out * gain).clip(0, 255).astype(np.uint8)


def mdl_data(V):
    """triangles (counter-clockwise from outside), seam copies and per-cap-triangle centre vertices for write_mdl.
    write_mdl puts a triangle on the second st set when its rad points along -x: that is the wrap set here."""
    Vl = list(V)
    st_f, st_b = [], []
    for j in range(MH):
        for k in range(NH):
            u, v = k / NH * (SW - 1), (MH - 1 - j) / (MH - 1) * (SKIN_H - 1)
            st_f.append((u, v))
            st_b.append((SW - 1 if k == 0 else u, v))               # the far side of the seam
    st_f += [(0.0, 0.0)] * 2
    st_b += [(0.0, 0.0)] * 2
    tris, rad = [], []

    def add(a, b, c, wrap, out):
        if np.cross(Vl[b] - Vl[a], Vl[c] - Vl[a]) @ out < 0:
            b, c = c, b
        tris.append((a, b, c))
        rad.append((-1.0, 0, 0) if wrap else (1.0, 0, 0))

    for j in range(MH - 1):
        for k in range(NH):
            k1 = (k + 1) % NH
            a, b, c, d = j * NH + k, j * NH + k1, (j + 1) * NH + k1, (j + 1) * NH + k
            cen = (Vl[a] + Vl[b] + Vl[c] + Vl[d]) / 4
            ring_c = (V[j * NH:(j + 1) * NH].mean(0) + V[(j + 1) * NH:(j + 2) * NH].mean(0)) / 2
            add(a, b, c, k1 == 0, cen - ring_c)
            add(a, c, d, k1 == 0, cen - ring_c)
    for j, ci0, up in ((0, NH * MH, -1.0), (MH - 1, NH * MH + 1, 1.0)):
        for k in range(NH):
            k1 = (k + 1) % NH
            ci = len(Vl)
            Vl.append(V[ci0])
            u0, v = st_f[j * NH + k]
            u1 = (k + 1) / NH * (SW - 1)
            st_f.append(((u0 + u1) / 2, v))
            st_b.append(((u0 + u1) / 2, v))
            add(j * NH + k, j * NH + k1, ci, k1 == 0, np.array([0, 0, up]))
    return np.array(Vl), np.array(tris), np.array(rad), np.array(st_f), np.array(st_b)


def main():
    m = build()
    V, tris, rad, st_f, st_b = mdl_data(m["V"])
    gain = B.SKIN_GAIN * BRIGHT
    skin8 = B.to_palette(skin(m, 1, gain))
    big = skin(m, TGA_MUL, gain)
    B.SKIN_H = SKIN_H                                   # write_mdl clamps t and writes the header from this
    path = os.path.join(OUT, "grenade.mdl")
    nv, nt = B.write_mdl(path, dict(V=V, tris=tris, rad=rad), [("frame1", V)], skin8, st_f, st_b, SW)
    Image.fromarray(big).save(path + "_0.tga", compression="tga_rle")
    print("grenade.mdl: %d verts, %d tris, skin %dx%d (tga x%d), size %s, %d bytes" % (
        nv, nt, SW, SKIN_H, TGA_MUL, np.round(V.max(0) - V.min(0), 1), os.path.getsize(path)))
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        md = B.read_mdl(path)
        name, pos, nn = md["frames"][0]
        md["frames"][0] = (name, pos + np.array([0, 0, 3.0]), nn)
        bright = skin(m, TGA_MUL, BRIGHT)               # the preview has no overbright lighting to undo
        tiles = [B.render(md, 0, yaw, size=300, zoom=300 / (HEIGHT * 1.4), tex=bright)
                 for yaw in (0, 40, 90, 140, 180, 270)]
        Image.fromarray(np.concatenate(tiles, 1)).save(os.path.join(PREVIEW, "grenade_head_views.png"))
        Image.fromarray(bright).save(os.path.join(PREVIEW, "grenade_head_skin.png"))


if __name__ == "__main__":
    main()
