"""The floating head monster: progs/floathead.mdl (+ .mdl_0.tga closed mouth, .mdl_1.tga open mouth).

Built like the JohnWave grenade head (build_head_grenade.py): rings of the mesh follow the outline of the face photo
(out/chars/ref/floathead_face.png), the cross-sections are a flattish face in front and a rounder skull behind, and
the nose is pushed out.  The photo is cropped at the top of the hair, so the dome above it and the back of the head
are hair tiled from the photo's top rows.  There is no back photo.

Skin 0 is the photo as it is.  Skin 1 has a big open mouth painted between the lips; the open frames drop the jaw
so that painted mouth stretches open.

Frames (floathead.qc's $frame list must match):
  idle1-8   bob and wobble, mouth shut      (skin 0)
  open1-4   the jaw drops                   (skin 1)
  rush1-4   wide open, shaking, cheeks out  (skin 1)
  pain1-4   knocked back, "ow"              (skin 1)

python3 -E -P build_floathead.py [--preview DIR] [--out DIR] [--size UNITS] [--bright X]
"""
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_char_models as B
from build_head_grenade import smoothstep, bleed

ARG = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
OUT = ARG("--out", B.PROGS)
PREVIEW = ARG("--preview", None)
HEIGHT = float(ARG("--size", 40))        # quake units, top of the skull to the bottom of the beard: a big head
BRIGHT = float(ARG("--bright", 1.6))
FRONT = os.path.join(B.REF, "floathead_face.png")

PAD = 110                                # synthesised skull above the photo (canvas row = photo row + PAD)
NH, MH = 36, 52                          # ring vertices (vertex 0 at the back of the head), rings (0 = chin)
SW, SKIN_H = 384, 256
TGA_MUL = 3
# head outline in photo pixels: (row, left edge, right edge), ears included
PROFILE = [(0, 114, 458), (40, 104, 462), (100, 106, 466), (150, 109, 470), (185, 70, 497), (240, 68, 498),
           (285, 82, 482), (320, 108, 456), (360, 124, 445), (400, 147, 432), (430, 170, 415), (455, 204, 396),
           (470, 238, 362), (478, 270, 325)]
NOSE = (252, 268 + PAD)                  # nose tip
MOUTH = (283, 349 + PAD)                 # middle of the lips
MOUTH_RX, MOUTH_TOP, MOUTH_BOT = 64, 336 + PAD, 364 + PAD
JAW = 62                                 # canvas pixels the chin drops when the mouth is fully open


def canvas():
    """the photo on a taller canvas, with hair tiled into the cropped-off skull above it; plus the head mask"""
    ph = np.asarray(Image.open(FRONT).convert("RGB")).astype(np.float32)
    H, W = ph.shape[0] + PAD, ph.shape[1]
    rgb = np.zeros((H, W, 3), np.float32)
    rgb[PAD:] = ph
    BL = 28                                                         # rows where the tiled hair fades into the photo
    hr = hair(ph, (PAD + BL, W), seed=3)
    ramp = smoothstep(0, BL, np.arange(BL))[:, None, None]
    rgb[:PAD] = hr[:PAD]
    rgb[PAD:PAD + BL] = hr[PAD:] * (1 - ramp) + ph[:BL] * ramp
    # mask from the outline: rows interpolated, the skull above the photo is a half ellipse
    rows = np.arange(H) - PAD
    py = np.array([p[0] for p in PROFILE], float)
    lo = np.interp(rows, py, [p[1] for p in PROFILE])
    hi = np.interp(rows, py, [p[2] for p in PROFILE])
    top = rows < 0
    c, h = (lo + hi) / 2, (hi - lo) / 2
    k = np.sqrt(np.clip(1 - (rows / -PAD) ** 2, 0, 1))
    h[top] = h[PAD] * k[top]
    lo, hi = c - h, c + h
    xs = np.arange(W)[None]
    m = (xs >= lo[:, None]) & (xs <= hi[:, None]) & (rows[:, None] <= PROFILE[-1][0])
    return rgb, m


def hair(ph, shape, seed):
    """a hair texture of the given size, tiled from the photo's top rows with random offsets and flips"""
    rng = np.random.default_rng(seed)
    strip = ph[2:28, 150:420]                                       # dark hair right along the top edge
    H, W = shape
    out = np.zeros((H, W, 3), np.float32)
    acc = np.zeros((H, W, 1), np.float32)
    sh, sw = strip.shape[:2]
    for y in range(-sh // 2, H, sh // 2):
        for x in range(-sw // 2, W, sw // 3):
            t = strip[:, ::-1] if rng.random() < 0.5 else strip
            t = t[::-1] if rng.random() < 0.5 else t
            y0, x0 = y + rng.integers(-4, 5), x + rng.integers(-20, 21)
            ys, xs = slice(max(y0, 0), min(y0 + sh, H)), slice(max(x0, 0), min(x0 + sw, W))
            if ys.stop <= ys.start or xs.stop <= xs.start:
                continue
            ty, tx = slice(ys.start - y0, ys.stop - y0), slice(xs.start - x0, xs.stop - x0)
            wy = np.hanning(sh + 2)[1:-1][ty, None]
            wx = np.hanning(sw + 2)[1:-1][None, tx]
            w = (wy * wx)[..., None] + 1e-3
            out[ys, xs] += t[ty, tx] * w
            acc[ys, xs] += w
    return out / acc


def paint_mouth(rgb):
    """skin 1: a big cartoon mouth between the lips (dark inside, top teeth, tongue)"""
    H, W = rgb.shape[:2]
    S = 4                                                           # supersampled drawing
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    mx, my = MOUTH
    x0, x1, y0, y1 = (mx - MOUTH_RX) * S, (mx + MOUTH_RX) * S, MOUTH_TOP * S, MOUTH_BOT * S
    d.ellipse([x0, y0, x1, y1], fill=(28, 4, 6, 255))
    d.ellipse([x0 + 10 * S, y0 + 5 * S, x1 - 10 * S, y1 - 2 * S], fill=(62, 8, 12, 255))
    tc = (mx - 30) * S, (MOUTH_BOT - 3) * S                         # tongue, in the lower half
    d.ellipse([tc[0], (MOUTH_TOP + 16) * S, (mx + 34) * S, (MOUTH_BOT + 6) * S], fill=(176, 64, 74, 255))
    d.line([(mx * S, (MOUTH_TOP + 19) * S), (mx * S, (MOUTH_BOT - 2) * S)], fill=(130, 40, 48, 255), width=2 * S)
    lay = Image.composite(lay, Image.new("RGBA", lay.size, (0, 0, 0, 0)), mouth_shape(W, H, S))
    # top teeth: a row along the upper lip, clipped to the mouth
    teeth = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    t = ImageDraw.Draw(teeth)
    tw = 13
    for i in range(-5, 5):
        cx = mx + i * tw + tw / 2
        t.rounded_rectangle([(cx - tw / 2 + 1) * S, (MOUTH_TOP - 2) * S, (cx + tw / 2 - 1) * S, (MOUTH_TOP + 8) * S],
                            radius=3 * S, fill=(232, 226, 205, 255))
    teeth = Image.composite(teeth, Image.new("RGBA", lay.size, (0, 0, 0, 0)), mouth_shape(W, H, S))
    lay = Image.alpha_composite(lay, teeth)
    lay = lay.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(lay).astype(np.float32)
    al = a[..., 3:] / 255
    return rgb * (1 - al) + a[..., :3] * al


def mouth_shape(W, H, S):
    m = Image.new("L", (W * S, H * S), 0)
    mx = MOUTH[0]
    ImageDraw.Draw(m).ellipse([(mx - MOUTH_RX) * S, MOUTH_TOP * S, (mx + MOUTH_RX) * S, MOUTH_BOT * S], fill=255)
    return m


def rings(m):
    """smoothed centre / half width of the mask at MH rows, chin (t=0) to the top of the skull (t=1)"""
    ys = np.nonzero(m)[0]
    ybot, ytop = ys.max() - 1.0, ys.min() + 1.0
    rows = np.arange(m.shape[0])
    has = m.any(1)
    lo = np.interp(rows, rows[has], m.argmax(1)[has].astype(float))
    hi = np.interp(rows, rows[has], (m.shape[1] - 1 - m[:, ::-1].argmax(1))[has].astype(float))
    lo, hi = ndimage.gaussian_filter1d(lo, 4), ndimage.gaussian_filter1d(hi, 4)
    yt = ybot + (ytop - ybot) * np.linspace(0, 1, MH)
    return ybot, ytop, yt, np.interp(yt, rows, (lo + hi) / 2), np.interp(yt, rows, (hi - lo) / 2)


def build():
    rgb, m = canvas()
    ybot, ytop, yt, cx, hw = rings(m)
    hw = np.maximum(hw, 0.08 * hw.max())
    t = np.linspace(0, 1, MH)
    th = -np.pi / 2 + 2 * np.pi * np.arange(NH) / NH                # k=0 back of the head, k=NH/2 the face
    cs, sn = np.cos(th), np.sin(th)
    db = 0.72 + 0.42 * smoothstep(0.15, 0.5, t)                     # beard shallow behind, skull deep
    fr = np.sign(sn) * np.abs(sn) ** 0.75
    P = np.zeros((MH, NH, 3))
    P[..., 1] = cx[:, None] + hw[:, None] * cs[None]
    P[..., 0] = hw[:, None] * fr[None] * np.where(sn[None] > 0, 0.82, db[:, None])
    P[..., 2] = yt[:, None]
    UVF = P[..., [1, 2]].copy()
    face = np.clip(sn, 0, 1)[None] ** 2
    g = np.exp(-(((UVF[..., 0] - NOSE[0]) / 34) ** 2 + ((UVF[..., 1] - NOSE[1]) / 30) ** 2))
    P[..., 0] += 34 * g * face                                      # that nose
    g = np.exp(-(((UVF[..., 0] - NOSE[0]) / 120) ** 2 + ((UVF[..., 1] - (205 + PAD)) / 22) ** 2))
    P[..., 0] += 8 * g * face                                       # brow
    # back of the head: hair, spread round in angle so it wraps the sides
    psi = np.angle(np.exp(1j * (th + np.pi / 2)))
    side = np.sin(np.clip(0.65 * psi, -np.pi / 2, np.pi / 2))
    back = hair(np.asarray(Image.open(FRONT).convert("RGB")).astype(np.float32), rgb.shape[:2], seed=11)
    UVB = np.stack([cx[:, None] - hw[:, None] * side[None], np.repeat(yt[:, None], NH, 1)], -1)
    front = bleed(rgb, m, 7)
    opened = bleed(paint_mouth(rgb), m, 7)
    V = P.reshape(-1, 3)
    V = np.vstack([V, [[0, cx[0], ybot + 2], [0, cx[-1], ytop - 1]]])
    uv = np.vstack([UVF.reshape(-1, 2), [[cx[0], ybot], [cx[-1], ytop]]])
    fw = np.concatenate([np.repeat(sn[None], MH, 0).reshape(-1), [1.0, -1.0]])   # +1 face side .. -1 back
    return dict(V=V, uv=uv, fw=fw, UVF=UVF, UVB=UVB, front=front, opened=opened, back=back)


def jaw(V, uv, fw, J):
    """drop the jaw by J (0..1): everything under the lips moves down (and a little forward), fading out to the sides
    and the back, so the painted mouth between the lips stretches open"""
    V = V.copy()
    wv = smoothstep(MOUTH_TOP, MOUTH_BOT, uv[:, 1])
    wx = 1 - smoothstep(70, 175, np.abs(uv[:, 0] - MOUTH[0]))
    wf = smoothstep(-0.25, 0.45, fw)
    d = J * JAW * wv * wx * wf
    V[:, 2] += d
    V[:, 0] += 0.18 * d
    return V


def place(Vc, lo, hi):
    """canvas units (z down) -> quake units, z up, centred on the closed head's box"""
    V = Vc.copy()
    V[:, 2] = -V[:, 2]
    return (V - (lo + hi) / 2) * (HEIGHT / (hi[2] - lo[2]))


def rot(V, axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    i, j = [(1, 2), (2, 0), (0, 1)][axis]
    V = V.copy()
    V[:, i], V[:, j] = c * V[:, i] - s * V[:, j], s * V[:, i] + c * V[:, j]
    return V


def frames(m):
    base = m["V"].copy()
    base[:, 2] = -base[:, 2]
    lo, hi = base.min(0), base.max(0)
    rng = np.random.default_rng(5)
    out = []
    shut = place(m["V"], lo, hi)
    for i in range(8):                                              # bob and wobble like a balloon
        a = 2 * np.pi * i / 8
        out.append(("idle%d" % (i + 1), rot(shut, 0, 5 * np.sin(a)) + [0, 0, 1.4 * np.sin(a + 0.6)]))
    for i, J in enumerate((0.15, 0.45, 0.8, 1.0)):
        out.append(("open%d" % (i + 1), place(jaw(m["V"], m["uv"], m["fw"], J), lo, hi)))
    wide = place(jaw(m["V"], m["uv"], m["fw"], 1.12), lo, hi)
    low = smoothstep(0.55, 0.1, (wide[:, 2] - wide[:, 2].min()) / (wide[:, 2].max() - wide[:, 2].min()))
    for i in range(4):                                              # screaming: shake, cheeks out
        V = wide.copy()
        V[:, 1] *= 1 + (0.06 + 0.03 * (i % 2)) * low
        V = rot(V, 0, rng.uniform(-6, 6)) + rng.uniform(-0.8, 0.8, 3)
        out.append(("rush%d" % (i + 1), V))
    ow = place(jaw(m["V"], m["uv"], m["fw"], 0.4), lo, hi)
    for i, p in enumerate((-16, -12, -7, -2)):                      # knocked back: face tips up
        out.append(("pain%d" % (i + 1), rot(ow, 1, p)))
    return out


def skin(m, img, mul, gain):
    """cylindrical unwrap (as the grenade): the photo on the face, tiled hair round the back, blended at the ears"""
    W_, H_ = SW * mul, SKIN_H * mul
    kk = (np.arange(W_) + 0.5) / W_ * NH
    jj = np.maximum((1 - (np.arange(H_) + 0.5) / H_) * (MH - 1), 0.6)
    KK, JJ = np.meshgrid(kk, jj)
    out = np.zeros((H_, W_, 3), np.float32)
    wf = smoothstep(0.05, 0.35, np.sin(-np.pi / 2 + 2 * np.pi * KK / NH))
    for grid, rgb, w in ((m["UVF"], img, wf), (m["UVB"], m["back"], 1 - wf)):
        g = np.concatenate([grid, grid[:, :1]], 1)
        px = [ndimage.map_coordinates(g[..., c], [JJ, KK], order=1, mode="nearest") for c in range(2)]
        for c in range(3):
            out[..., c] += w * ndimage.map_coordinates(rgb[..., c], [px[1], px[0]], order=1, mode="nearest")
    return (out * gain).clip(0, 255).astype(np.uint8)


def add_skin(path, skin8):
    """write_mdl writes one skin: append a second one (header numskins is at byte 48, skins follow the header)"""
    d = bytearray(open(path, "rb").read())
    n = struct.unpack_from("<i", d, 48)[0]
    struct.pack_into("<i", d, 48, n + 1)
    at = 84 + n * (4 + SW * SKIN_H)
    d[at:at] = struct.pack("<i", 0) + skin8.tobytes()
    open(path, "wb").write(bytes(d))


def main():
    from build_head_grenade import mdl_data
    import build_head_grenade as G
    G.NH, G.MH, G.SW, G.SKIN_H = NH, MH, SW, SKIN_H                  # mdl_data reads the ring layout from there
    m = build()
    fr = frames(m)
    V0, tris, rad, st_f, st_b = mdl_data(fr[0][1])
    out_frames = [(name, mdl_data(V)[0]) for name, V in fr]
    gain = B.SKIN_GAIN * BRIGHT
    B.SKIN_H = SKIN_H
    path = os.path.join(OUT, "floathead.mdl")
    nv, nt = B.write_mdl(path, dict(V=V0, tris=tris, rad=rad), out_frames, B.to_palette(skin(m, m["front"], 1, gain)),
                         st_f, st_b, SW)
    add_skin(path, B.to_palette(skin(m, m["opened"], 1, gain)))
    for i, img in enumerate((m["front"], m["opened"])):
        Image.fromarray(skin(m, img, TGA_MUL, gain)).save(path + "_%d.tga" % i, compression="tga_rle")
    lo, hi = np.min([f[1].min(0) for f in out_frames], 0), np.max([f[1].max(0) for f in out_frames], 0)
    print("floathead.mdl: %d verts, %d tris, %d frames, 2 skins %dx%d (tga x%d), box %s .. %s, %d bytes" % (
        nv, nt, len(out_frames), SW, SKIN_H, TGA_MUL, np.round(lo, 1), np.round(hi, 1), os.path.getsize(path)))
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        md = B.read_mdl(path)
        texs = [skin(m, img, TGA_MUL, BRIGHT) for img in (m["front"], m["opened"])]
        zoom = 300 / (HEIGHT * 1.5)
        rows = []
        for fi in (0, 11, 13, 17):
            tex = texs[0] if fi < 8 else texs[1]
            rows.append(np.concatenate([B.render(md, fi, yaw, size=420, zoom=zoom * 1.4, tex=tex) for yaw in (0, 30, 70, 160)], 1))
        Image.fromarray(np.concatenate(rows, 0)).save(os.path.join(PREVIEW, "floathead_views.png"))
        Image.fromarray(texs[1]).save(os.path.join(PREVIEW, "floathead_skin_open.png"))


if __name__ == "__main__":
    main()
