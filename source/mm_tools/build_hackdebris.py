"""Computer junk thrown out when a hacking Rob blows up: keyboard, mouse, floppy disk, CD, circuit board (procedural).
The fedora comes from build_hackmon_models.py, the monitor and the sledgehammer are the NVIDIA SimReady props.
python -I build_hackdebris.py <progs_dir>"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib
from PIL import Image, ImageDraw

OUT = sys.argv[1]
random.seed(11)


def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


def vnormals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = [p1[i] - p0[i] for i in range(3)]
        w = [p2[i] - p0[i] for i in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        for i in (a, b, c):
            for k in range(3):
                acc[i][k] += n[k]
    return [norm(a) for a in acc]


def surface(name, shader, verts, st, tris):
    return dict(name=name, shader=shader, tris=tris, st=st, frames=[(verts, vnormals(verts, tris))])


def box(w, d, h, name, top_tex, side_tex):
    """w along X, d along Y, h along Z, centred. Top face textured with top_tex, everything else side_tex."""
    x, y, z = w / 2, d / 2, h / 2
    # faces as CCW quads seen from outside
    top = [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    top_st = [(0, 1), (1, 1), (1, 0), (0, 0)]
    sides = [
        [(-x, -y, -z), (-x, y, -z), (x, y, -z), (x, -y, -z)],     # bottom
        [(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z)],     # -Y
        [(x, -y, -z), (x, y, -z), (x, y, z), (x, -y, z)],         # +X
        [(x, y, -z), (-x, y, -z), (-x, y, z), (x, y, z)],         # +Y
        [(-x, y, -z), (-x, -y, -z), (-x, -y, z), (-x, y, z)],     # -X
    ]
    tv, tt = list(top), [(0, 1, 2), (0, 2, 3)]
    sv, sst, stt = [], [], []
    for q in sides:
        b = len(sv)
        sv += q
        sst += [(0, 0), (1, 0), (1, 1), (0, 1)]
        stt += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    return [surface(name + "_top", top_tex, tv, top_st, tt), surface(name + "_side", side_tex, sv, sst, stt)]


def disc(r, h, name, top_tex, side_tex, segs=20):
    z = h / 2
    tv, tst, tt = [(0, 0, z)], [(0.5, 0.5)], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        tv.append((r * math.cos(a), r * math.sin(a), z))
        tst.append((0.5 + 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a)))
    for i in range(segs):
        tt.append((0, 1 + i, 1 + (i + 1) % segs))
    sv, sst, stt = [], [], []
    for i in range(segs):
        a0, a1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
        b = len(sv)
        sv += [(r * math.cos(a0), r * math.sin(a0), -z), (r * math.cos(a1), r * math.sin(a1), -z),
               (r * math.cos(a1), r * math.sin(a1), z), (r * math.cos(a0), r * math.sin(a0), z)]
        sst += [(0, 0), (1, 0), (1, 1), (0, 1)]
        stt += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    b = len(sv)
    sv.append((0, 0, -z))
    sst.append((0, 0))
    for i in range(segs):
        a0, a1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
        sv += [(r * math.cos(a1), r * math.sin(a1), -z), (r * math.cos(a0), r * math.sin(a0), -z)]
        sst += [(0, 0), (0, 0)]
        stt.append((b, b + 1 + 2 * i, b + 2 + 2 * i))
    return [surface(name + "_top", top_tex, tv, tst, tt), surface(name + "_side", side_tex, sv, sst, stt)]


def save(name, surfs):
    md3lib.write(os.path.join(OUT, name + ".md3"), dict(name=name, surfaces=surfs, nframes=1))


def solid(path, rgb):
    Image.new("RGB", (8, 8), rgb).save(os.path.join(OUT, path))


# ---- keyboard
im = Image.new("RGB", (256, 96), (40, 40, 44))
d = ImageDraw.Draw(im)
for row in range(5):
    cols = 14 if row < 4 else 1
    for c in range(cols):
        if row == 4:
            d.rectangle([60, 78, 196, 90], fill=(215, 215, 220))
        else:
            x0 = 6 + c * 17.5 + (row % 2) * 4
            d.rectangle([x0, 6 + row * 15, x0 + 14, 6 + row * 15 + 12], fill=(215, 215, 220))
im.save(os.path.join(OUT, "hd_kbd_top.png"))
solid("hd_kbd_side.png", (30, 30, 34))
save("hd_kbd", box(30, 10.5, 2, "kbd", "progs/hd_kbd_top", "progs/hd_kbd_side"))

# ---- mouse
im = Image.new("RGB", (64, 96), (200, 200, 205))
d = ImageDraw.Draw(im)
d.line([(32, 0), (32, 40)], fill=(60, 60, 60), width=2)
d.line([(0, 40), (64, 40)], fill=(60, 60, 60), width=2)
d.rectangle([28, 10, 36, 26], fill=(90, 90, 95))
im.save(os.path.join(OUT, "hd_mouse_top.png"))
solid("hd_mouse_side.png", (170, 170, 175))
save("hd_mouse", box(7, 11, 3.5, "mouse", "progs/hd_mouse_top", "progs/hd_mouse_side"))

# ---- floppy disk
im = Image.new("RGB", (128, 128), (25, 40, 120))
d = ImageDraw.Draw(im)
d.rectangle([34, 0, 94, 40], fill=(190, 190, 195))
d.rectangle([76, 6, 88, 32], fill=(60, 60, 65))
d.rectangle([20, 62, 108, 122], fill=(235, 235, 230))
d.line([(28, 82), (100, 82)], fill=(120, 120, 140), width=2)
d.line([(28, 98), (100, 98)], fill=(120, 120, 140), width=2)
im.save(os.path.join(OUT, "hd_floppy_top.png"))
solid("hd_floppy_side.png", (20, 30, 90))
save("hd_floppy", box(14, 14, 1, "floppy", "progs/hd_floppy_top", "progs/hd_floppy_side"))

# ---- CD
im = Image.new("RGB", (128, 128), (0, 0, 0))
px = im.load()
for yy in range(128):
    for xx in range(128):
        r = math.hypot(xx - 63.5, yy - 63.5) / 64.0
        a = math.atan2(yy - 63.5, xx - 63.5)
        if r > 1.0 or r < 0.12:
            px[xx, yy] = (30, 30, 30)
        else:
            v = 150 + int(70 * math.sin(a * 3 + r * 9))
            px[xx, yy] = (v, min(255, v + 20), min(255, v + 40)) if r > 0.3 else (210, 210, 215)
im.save(os.path.join(OUT, "hd_cd_top.png"))
solid("hd_cd_side.png", (190, 190, 195))
save("hd_cd", disc(8, 0.8, "cd", "progs/hd_cd_top", "progs/hd_cd_side"))

# ---- circuit board
im = Image.new("RGB", (160, 112), (20, 110, 50))
d = ImageDraw.Draw(im)
for _ in range(40):
    x0, y0 = random.randint(0, 150), random.randint(0, 100)
    if random.random() < 0.5:
        d.line([(x0, y0), (x0 + random.randint(10, 60), y0)], fill=(200, 170, 60), width=2)
    else:
        d.line([(x0, y0), (x0, y0 + random.randint(10, 40))], fill=(200, 170, 60), width=2)
d.rectangle([20, 20, 60, 60], fill=(25, 25, 30))
d.rectangle([80, 30, 108, 50], fill=(25, 25, 30))
d.rectangle([110, 70, 146, 96], fill=(25, 25, 30))
for k in range(8):
    d.line([(20 + k * 5, 14), (20 + k * 5, 20)], fill=(210, 210, 210), width=2)
im.save(os.path.join(OUT, "hd_board_top.png"))
solid("hd_board_side.png", (15, 80, 35))
save("hd_board", box(20, 14, 1.2, "board", "progs/hd_board_top", "progs/hd_board_side"))

# closed-box sanity: every model should have positive signed volume (same winding as the working props)
for n in ("hd_kbd", "hd_mouse", "hd_floppy", "hd_cd", "hd_board"):
    m = md3lib.read(os.path.join(OUT, n + ".md3"))
    V = 0
    for s in m["surfaces"]:
        v = s["frames"][0][0]
        for a, b, c in s["tris"]:
            p, q, r = v[a], v[b], v[c]
            V += (p[0] * (q[1] * r[2] - q[2] * r[1]) - p[1] * (q[0] * r[2] - q[2] * r[0]) + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6
    print(n, "volume", round(V, 1))
