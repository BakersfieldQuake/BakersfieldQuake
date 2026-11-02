"""The standing Pickle Surprise as a 16-view sprite: front, back and all the sides.

progs/pickle.md3 is 16 cards in one model (a surface per turntable view, pickle_00..15.png), and 16 frames. In frame f only card f has
any size, the others are collapsed to a point, so choosing the frame chooses the picture. pickle.qc (Pk_Customize, run by the engine
for every client before it sends the balloon) turns the card to face that client and picks the frame from where he stands, round the
pickle: so everybody sees the pickle from his own side, and walking round it shows the front, the sides and the back.

Frame k is the view of a viewer k * 22.5 degrees anticlockwise (seen from above) from the pickle's face.

Frames 16..19 are the SCREAM face (big eyes, wide mouth: the vote pick, out/faces/scream_*.png made by make_pickle_faces.py) for the
four views whose face shows, 0, 1, 2 and 15; pickle.qc switches to them for the last moments before the blast.

The video's frame 9 is a bad cut-out (a smear); it is replaced with a mirrored copy of frame 7 (the pickle is the same from both sides),
the original saved in out/progs/pickle_09_bad.png. Run it after build_pickle_assets.py (that script rewrites scripts/pickle.shader).

python make_pickle_views.py [BakersfieldQuake dir]      (needs PIL; run it without -I)"""
import os
import shutil
import sys

from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

MOD = sys.argv[1] if len(sys.argv) > 1 else r"G:\Quake\Combat\BakersfieldQuake"
HERE = os.path.dirname(os.path.abspath(__file__))
PROGS = os.path.join(MOD, "progs")
N = 16
SCREAM_VIEWS = [0, 1, 2, 15]         # frames 16, 17, 18, 19
NF = N + len(SCREAM_VIEWS)
HALF = 10.0                  # the card is 20 x 20 units, centred on the origin, face along -X, picture-left = +Y (as the old card)


def fix_frame_9():
    p9 = os.path.join(PROGS, "pickle_09.png")
    keep = os.path.join(HERE, "out", "progs", "pickle_09_bad.png")
    if not os.path.exists(keep):
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        shutil.copy(p9, keep)
    ImageOps.mirror(Image.open(os.path.join(PROGS, "pickle_07.png")).convert("RGBA")).save(p9)


def scream_textures():
    """progs/pickle_scream_NN.png: the scream faces from out/faces (full size, in the game's dimmed look)"""
    for v in SCREAM_VIEWS:
        shutil.copy(os.path.join(HERE, "out", "faces", "scream_%02d.png" % v), os.path.join(PROGS, "pickle_scream_%02d.png" % v))


def shaders():
    path = os.path.join(MOD, "scripts", "pickle.shader")
    s = open(path, encoding="utf-8").read()
    add = ""
    for k in range(1, N):                      # view 0 keeps progs/pickle_front: its animmap wobbles round the front
        name = "progs/pickle_v%02d" % k
        if name in s:
            continue
        add += "%s\n{\n\tcull none\n\t{\n\t\tmap progs/pickle_%02d\n\t\talphafunc GE128\n\t}\n}\n" % (name, k)
    for v in SCREAM_VIEWS:
        name = "progs/pickle_scream_front" if v == 0 else "progs/pickle_scream_v%02d" % v
        if name in s:
            continue
        if v == 0:                             # the front one wobbles through its neighbours like the normal face does
            frames = " ".join("progs/pickle_scream_%02d" % f for f in (15, 0, 1, 2, 1, 0))
            add += "%s\n{\n\tcull none\n\t{\n\t\tanimmap 5 %s\n\t\talphafunc GE128\n\t}\n}\n" % (name, frames)
        else:
            add += "%s\n{\n\tcull none\n\t{\n\t\tmap progs/pickle_scream_%02d\n\t\talphafunc GE128\n\t}\n}\n" % (name, v)
    if add:
        open(path, "a", encoding="utf-8").write("\n// the 16 views of the standing pickle (make_pickle_views.py)\n" + add)
    return len(add) > 0


def model():
    card = [(0.0, HALF, -HALF), (0.0, HALF, HALF), (0.0, -HALF, HALF), (0.0, -HALF, -HALF)]
    nothing = [(0.0, 0.0, 0.0)] * 4
    st = [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    tris = [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]          # both sides
    surfaces = []
    for k in range(NF):
        frames = [(card if f == k else nothing, [(-1.0, 0.0, 0.0)] * 4) for f in range(NF)]
        if k < N:
            shader = "progs/pickle_front" if k == 0 else "progs/pickle_v%02d" % k
        else:
            v = SCREAM_VIEWS[k - N]
            shader = "progs/pickle_scream_front" if v == 0 else "progs/pickle_scream_v%02d" % v
        surfaces.append(dict(name="view%02d" % k, shader=shader, tris=tris, st=st, frames=frames))
    md3lib.write(os.path.join(PROGS, "pickle.md3"), dict(name="pickle", surfaces=surfaces, nframes=NF))


fix_frame_9()
scream_textures()
new = shaders()
model()
old3d = os.path.join(PROGS, "pickle3d.png")
if os.path.exists(old3d):                      # the hull experiment's texture: not used any more
    os.makedirs(os.path.join(HERE, "out", "progs"), exist_ok=True)
    shutil.move(old3d, os.path.join(HERE, "out", "progs", "pickle3d.png"))
print("wrote progs/pickle.md3 (%d views + %d scream faces), shaders %s" % (N, len(SCREAM_VIEWS), "added" if new else "already there"))
