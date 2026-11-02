"""The CCC gun's bolt: a yellow 3D letter C, written straight into BakersfieldQuake/progs:
  ccc.md3        a letter C lying in the Y-Z plane (the bolt flies along +X, so you see the C from behind and the bolt's
                 roll spin turns it like a wheel). About 18 units across, 3 deep; the opening faces the pilot's right.
  ccc_yellow.png its yellow texture
Also appends ccc_effectinfo.txt (the ccc_trail / ccc_impact particles) to BakersfieldQuake/effectinfo.txt once.
python -I build_ccc.py [BakersfieldQuake dir]"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

from PIL import Image

MOD = sys.argv[1] if len(sys.argv) > 1 else "G:/Quake/Combat/BakersfieldQuake"
PROGS = os.path.join(MOD, "progs")

R_OUT = 9.0         # outer radius of the C
R_IN = 5.2          # inner radius
HALF = 1.6          # half the depth along the flight direction
GAP = 42.0          # half the opening, degrees
STEPS = 28          # segments round the arc


def ccc():
    verts, st, tris = [], [], []

    def vert(x, ang, r, v):
        a = math.radians(ang)
        verts.append((x, r * math.cos(a), r * math.sin(a)))      # ang 0 = +Y, 90 = +Z
        st.append((0.5, v))
        return len(verts) - 1

    def quad(a, b, c, d):
        tris.extend([(a, b, c), (a, c, d), (a, c, b), (a, d, c)])  # both sides: the C is seen from every angle

    # the opening faces -Y (the pilot's right from behind): sweep from 180+GAP round through 0 to 180-GAP
    start = 180.0 + GAP
    sweep = 360.0 - 2 * GAP
    rings = []
    for i in range(STEPS + 1):
        ang = start + sweep * i / STEPS
        rings.append((vert(HALF, ang, R_OUT, 0.0), vert(-HALF, ang, R_OUT, 0.3),
                      vert(HALF, ang, R_IN, 1.0), vert(-HALF, ang, R_IN, 0.7)))
    for i in range(STEPS):
        of0, ob0, if0, ib0 = rings[i]
        of1, ob1, if1, ib1 = rings[i + 1]
        quad(of0, of1, if1, if0)        # front face
        quad(ob0, ib0, ib1, ob1)        # back face
        quad(of0, ob0, ob1, of1)        # outer wall
        quad(if0, if1, ib1, ib0)        # inner wall
    for ring in (rings[0], rings[-1]):  # flat end caps
        of, ob, if_, ib = ring
        quad(of, if_, ib, ob)
    surf = dict(name="ccc", shader="progs/ccc_yellow", tris=tris, st=st, frames=[(verts, [(1, 0, 0)] * len(verts))])
    md3lib.write(os.path.join(PROGS, "ccc.md3"), dict(name="ccc", surfaces=[surf], nframes=1))


def texture():
    im = Image.new("RGB", (8, 16))
    px = im.load()
    for y in range(16):
        t = y / 15.0                                  # 0 bright lemon .. 1 deeper gold
        c = (255, int(240 - 70 * t), int(40 * (1 - t)))
        for x in range(8):
            px[x, y] = c
    im.save(os.path.join(PROGS, "ccc_yellow.png"))


def effects():
    here = os.path.dirname(os.path.abspath(__file__))
    add = open(os.path.join(here, "ccc_effectinfo.txt"), encoding="utf-8").read()
    path = os.path.join(MOD, "effectinfo.txt")
    cur = open(path, encoding="utf-8", errors="surrogateescape").read()
    if "effect ccc_trail" in cur:
        print("effectinfo.txt already has the CCC effects")
        return
    with open(path, "a", encoding="utf-8", errors="surrogateescape") as f:
        f.write("\n" + add)
    print("appended CCC effects to", path)


os.makedirs(PROGS, exist_ok=True)
ccc()
texture()
effects()
print("ccc.md3 and ccc_yellow.png written to", PROGS)
