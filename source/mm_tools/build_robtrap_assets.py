"""Rob booby trap laser beam, written straight into BakersfieldQuake/progs:
  laser.md3      a 100 unit long thin crossed ribbon along +X, fullbright + additive in game (scale = length / 100)
  laser_red.png  its red gradient texture
python -I build_robtrap_assets.py [progs_dir]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "G:/Quake/Combat/BakersfieldQuake/progs"


def laser():
    L = 100.0
    hw = 0.5
    verts, st, tris = [], [], []
    for axis in ((0, 1, 0), (0, 0, 1)):                     # two crossed ribbons
        base = len(verts)
        for i, x in enumerate((0.0, L)):
            for side, v in ((-1, 1.0), (1, 0.0)):
                verts.append((x, axis[1] * side * hw, axis[2] * side * hw))
                st.append((float(i), v))
        a, b, c, d = base, base + 1, base + 2, base + 3
        tris += [(a, b, c), (b, d, c), (a, c, b), (b, c, d)]   # both sides
    surf = dict(name="beam", shader="progs/laser_red", tris=tris, st=st, frames=[(verts, [(0, 0, 1)] * len(verts))])
    md3lib.write(os.path.join(OUT, "laser.md3"), dict(name="laser", surfaces=[surf], nframes=1))


def laser_texture():
    im = Image.new("RGB", (8, 16))
    px = im.load()
    for y in range(16):
        t = abs(y - 7.5) / 7.5                       # 0 centre .. 1 edge
        g = int(255 * (1 - t) ** 1.2)
        for x in range(8):
            px[x, y] = (g, int(g * 0.08), int(g * 0.08))
    im.save(os.path.join(OUT, "laser_red.png"))


os.makedirs(OUT, exist_ok=True)
laser()
laser_texture()
print("laser written to", OUT)
