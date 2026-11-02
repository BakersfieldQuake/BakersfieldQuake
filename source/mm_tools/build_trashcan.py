"""bklan3 review 2 (video 2026-10-31 17:48): "this trash can needs to be way more defined". The old bin was a SimReady office
basket with one flat beige colour. This builds a park trash can: a green slatted steel drum with two bands, "TRASH" in
white, a dark open mouth with a black bag heaped and knotted in it. Written to progs/bklan/trashcan.md3 (drawn at scale 1)
and progs/bklan/bk_trash.png.   usage: python build_trashcan.py"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib  # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, "..", "..", "progs", "bklan"))
N = 20
FLIP = False
W = 512
H = 512

V, ST, TRI, NRM = [], [], [], []


def uv(px, py):
    return (px / W, py / H)


def vert(p, n, st):
    V.append(p)
    NRM.append(n)
    ST.append(st)
    return len(V) - 1


def tri(a, b, c):
    TRI.append((a, c, b) if FLIP else (a, b, c))


def strip(rings, cell=None, wrap=None):
    """rings: [(z, r, nz)] bottom to top; a tube round the z axis. wrap=(u0, u1, v0, v1) maps the whole tube onto that area of
    the texture; cell=(x, y) puts every vertex on one flat texel."""
    base = []
    for k, (z, r, nz) in enumerate(rings):
        row = []
        for i in range(N + 1):
            a = 2 * math.pi * i / N
            ca, sa = math.cos(a), math.sin(a)
            n = (ca, sa, nz)
            if wrap:
                u0, u1, v0, v1 = wrap
                s = uv(u0 + (u1 - u0) * i / N, v1 + (v0 - v1) * k / (len(rings) - 1))
            else:
                s = uv(*cell)
            row.append(vert((r * ca, r * sa, z), n, s))
        base.append(row)
    for k in range(len(rings) - 1):
        for i in range(N):
            a0, a1, b0, b1 = base[k][i], base[k][i + 1], base[k + 1][i], base[k + 1][i + 1]
            tri(a0, a1, b0)
            tri(a1, b1, b0)


def disc(z, r, cell, up=True):
    c = vert((0, 0, z), (0, 0, 1 if up else -1), uv(*cell))
    ring = [vert((r * math.cos(2 * math.pi * i / N), r * math.sin(2 * math.pi * i / N), z), (0, 0, 1 if up else -1), uv(*cell))
            for i in range(N + 1)]
    for i in range(N):
        if up:
            tri(c, ring[i], ring[i + 1])
        else:
            tri(c, ring[i + 1], ring[i])


def dome(z0, rx, h, cell, rings=5):
    rs = []
    for k in range(rings + 1):
        a = (math.pi / 2) * k / rings
        rs.append((z0 + h * math.sin(a), rx * math.cos(a) + 0.01, math.sin(a)))
    strip(rs, cell=cell)


def build():
    steel, dark, bag, black = (60, 300), (190, 300), (320, 300), (450, 300)
    # the drum: slight taper, a rolled rim at the top; body texture is the top half of the atlas
    strip([(0.0, 14.5, -0.2), (3.0, 17.0, 0.0), (44.0, 19.0, 0.0)], wrap=(0, 512, 5, 250))
    strip([(44.0, 19.0, 0.3), (46.5, 20.6, 0.8), (48.5, 20.2, 0.6), (49.5, 18.6, 0.2)], cell=steel)       # the rolled rim
    strip([(49.5, 18.6, -0.2), (49.5, 17.0, -0.4), (38.0, 16.4, -0.1)], cell=dark)                        # inside wall
    disc(38.0, 16.4, dark)
    strip([(7.5, 19.4, 0.0), (7.5, 19.8, 1.0), (11.0, 19.8, 1.0), (11.0, 19.4, 0.0)], cell=steel)          # two steel bands
    strip([(33.0, 19.0, 0.0), (33.0, 19.4, 1.0), (36.5, 19.4, 1.0), (36.5, 19.0, 0.0)], cell=steel)
    disc(0.0, 14.5, black, up=False)
    # the bag: a heaped black bag with a knot, leaning out of the mouth
    dome(43.0, 15.5, 14.0, bag)
    knot = [(56.0, 3.2, 0.0), (59.5, 2.0, 0.6), (62.0, 0.2, 1.0)]
    strip(knot, cell=bag)
    return dict(name="trashcan", surfaces=[dict(name="s0", shader="progs/bklan/bk_trash", tris=TRI, st=ST,
                                                frames=[(V, NRM)])])


def texture():
    im = Image.new("RGB", (W, H), (40, 40, 44))
    d = ImageDraw.Draw(im)
    r = random.Random(7)
    # body: green slats with dark grooves, "TRASH" twice, white arrow-loop badge under it
    for x in range(0, W, 16):
        g = 118 + r.randint(-6, 6)
        d.rectangle([x, 0, x + 13, 255], fill=(26, g, 46))
        d.rectangle([x + 14, 0, x + 15, 255], fill=(10, 40, 18))
    d.rectangle([0, 0, W, 10], fill=(14, 60, 26))
    d.rectangle([0, 244, W, 255], fill=(14, 60, 26))
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf", 52)
    except OSError:
        f = ImageFont.load_default()
    for cx in (128, 384):
        d.rectangle([cx - 104, 60, cx + 104, 150], fill=(238, 238, 226))
        d.text((cx, 105), "TRASH", font=f, fill=(14, 80, 30), anchor="mm")
        d.arc([cx - 24, 160, cx + 24, 208], 30, 300, fill=(238, 238, 226), width=7)
        d.polygon([(cx + 22, 166), (cx + 40, 176), (cx + 20, 188)], fill=(238, 238, 226))
    # flat cells for the rest (bottom half)
    cells = {(0, 255, 256, 511): (0, 0, 0)}
    d.rectangle([0, 256, W, H], fill=(20, 20, 22))
    d.rectangle([0, 270, 127, 400], fill=(168, 174, 182))        # steel
    d.rectangle([128, 270, 255, 400], fill=(16, 16, 18))         # inside of the drum
    d.rectangle([256, 270, 383, 400], fill=(64, 68, 84))         # the bag
    d.rectangle([384, 270, 511, 400], fill=(8, 8, 8))            # underside
    return im


def main():
    m = build()
    md3lib.write(os.path.join(OUT, "trashcan.md3"), m)
    texture().save(os.path.join(OUT, "bk_trash.png"))
    print("trashcan.md3:", len(V), "verts", len(TRI), "tris")


if __name__ == "__main__":
    main()
