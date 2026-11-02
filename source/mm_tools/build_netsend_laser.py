"""NetSend PC: the green laser bolt it shoots like a TF sentry (owner's review 2026-10-31: "act just like the sentry gun
from TF and blast green lazers"). The old bolt was progs/laser.mdl with colormod, but that model's orange is fullbright
(glow layer), so colormod never turned it green.
Writes progs/netsend_laser.md3 (one frame, two crossed ribbons, the head at the origin and the tail trailing behind
along -X: QC sets angles = vectoangles (velocity)), progs/netsend_laser.png and scripts/netsend_laser.shader (additive).
usage: python build_netsend_laser.py   (PIL needed: the WindowsApps Python 3.13, run without -I)"""
import math
import os

from PIL import Image

import md3lib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
PROGS = os.path.join(ROOT, "progs")
SCRIPTS = os.path.join(ROOT, "scripts")
DIM = 0.6		# the game shows model textures ~2x; additive ones clip fast


def build_texture():
    w, h = 128, 32
    im = Image.new("RGB", (w, h))
    px = im.load()
    for x in range(w):
        u = x / (w - 1.0)								# 0 tail, 1 head
        along = u ** 1.6
        for y in range(h):
            v = abs((y + 0.5) / h - 0.5) * 2.0			# 0 centre line, 1 edge
            glow = math.exp(-(v / 0.45) ** 2)
            core = math.exp(-(v / 0.14) ** 2)
            r = (0.10 * glow + 0.75 * core) * along
            g = (0.95 * glow + 1.00 * core) * along
            b = (0.18 * glow + 0.75 * core) * along
            px[x, y] = tuple(max(0, min(255, int(c * DIM * 255))) for c in (r, g, b))
    im.save(os.path.join(PROGS, "netsend_laser.png"))


def build_model():
    tail, head, hw = -34.0, 4.0, 1.7
    verts, norms, st, tris = [], [], [], []
    for axis in (1, 2):									# one ribbon wide in Y, one in Z
        b = len(verts)
        for x, u in ((tail, 0.0), (head, 1.0)):
            for side, v in ((-1.0, 0.0), (1.0, 1.0)):
                p = [x, 0.0, 0.0]
                p[axis] = side * hw
                verts.append(tuple(p))
                n = [0.0, 0.0, 0.0]
                n[3 - axis] = 1.0
                norms.append(tuple(n))
                st.append((u, v))
        tris += [(b, b + 1, b + 2), (b + 1, b + 3, b + 2)]
    surf = dict(name="netsend_laser", shader="progs/netsend_laser", tris=tris, st=st, frames=[(verts, norms)])
    md3lib.write(os.path.join(PROGS, "netsend_laser.md3"), dict(name="netsend_laser", surfaces=[surf], nframes=1))


def build_shader():
    with open(os.path.join(SCRIPTS, "netsend_laser.shader"), "w", newline="\n") as f:
        f.write("// written by source/mm_tools/build_netsend_laser.py\n\n"
                "progs/netsend_laser\n{\n\tcull none\n\t{\n\t\tmap progs/netsend_laser\n"
                "\t\tblendfunc add\n\t\trgbGen identity\n\t}\n}\n")


if __name__ == "__main__":
    build_texture()
    build_model()
    build_shader()
    print("wrote progs/netsend_laser.md3, progs/netsend_laser.png, scripts/netsend_laser.shader")
