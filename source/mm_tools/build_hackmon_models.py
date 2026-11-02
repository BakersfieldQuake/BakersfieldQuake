"""Hack Attack models, written straight into BakersfieldQuake/progs:
  hackmon_a/b/c.md3  the NVIDIA SimReady monitor (monitor_a01) with three screen textures that flicker in flight
  fedora.md3         a red fedora (surface of revolution)
  zap1..3.md3        crossed-ribbon lightning bolts, fullbright + additive in game
python -I build_hackmon_models.py <src_md3_dir> <progs_dir>
<src_md3_dir> = G:/Downloads/simready_out/md3/progs (hackmon.md3 + hackmon_N.png from convert.py)"""
import math
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

from PIL import Image, ImageDraw, ImageFont

random.seed(7)
SRC, OUT = sys.argv[1], sys.argv[2]
SCREEN_YAW = float(os.environ.get("HM_SCREEN_YAW", "0"))   # degrees to spin the monitor so its screen faces +X


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


def font(size):
    for f in ("consolab.ttf", "consola.ttf", "cour.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", f), size)
        except OSError:
            pass
    return ImageFont.load_default()


# ------------------------------------------------------------------ monitor
def screen_texture(path, bg, fg, lines, scan):
    im = Image.new("RGB", (256, 192), bg)
    d = ImageDraw.Draw(im)
    for y in range(0, 192, 4):
        d.line([(0, y), (256, y)], fill=tuple(int(c * 0.78) for c in bg), width=1)
    y = 12
    for text, size in lines:
        f = font(size)
        d.text((14, y), text, font=f, fill=fg)
        y += size + 8
    for _ in range(26):                                    # glitch bars
        gy = random.randint(0, 191)
        gh = random.randint(1, 5)
        gx = random.randint(0, 120)
        d.rectangle([gx, gy, gx + random.randint(30, 130), gy + gh], fill=scan)
    im.save(path)


def build_monitor():
    base = md3lib.read(os.path.join(SRC, "hackmon.md3"))
    variants = {
        "a": ((0, 18, 0), (60, 255, 80), [("> HACKING", 44), ("> HACKING", 44), ("> sudo rm -rf", 22), ("  /your/health", 22), ("[#######..] 72%", 22)], (0, 120, 30)),
        "b": ((20, 0, 0), (255, 60, 40), [("ACCESS", 48), ("DENIED", 48), ("   (just kidding)", 18), ("", 10), ("HACKING...", 30)], (140, 0, 0)),
        "c": ((0, 40, 170), (255, 255, 255), [(":(", 54), ("FATAL ERROR", 30), ("HACKING_HACKING", 22), ("0xDEADBEEF", 22)], (80, 120, 255)),
    }
    for k, (bg, fg, lines, scan) in variants.items():
        m = md3lib.read(os.path.join(SRC, "hackmon.md3"))
        for si, s in enumerate(m["surfaces"]):
            if si == 0:
                xs = [p[0] for p in s["frames"][0][0]]
                zs = [p[2] for p in s["frames"][0][0]]
                x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
                s["st"] = [((p[0] - x0) / (x1 - x0), 1.0 - (p[2] - z0) / (z1 - z0)) for p in s["frames"][0][0]]
                s["shader"] = "progs/hm_scr_%s" % k
                s["tris"] = list(s["tris"]) + [(a, c, b) for a, b, c in s["tris"]]     # visible from both sides
        # optional spin about Z so the screen faces +X
        if SCREEN_YAW:
            c, sn = math.cos(math.radians(SCREEN_YAW)), math.sin(math.radians(SCREEN_YAW))
            for s in m["surfaces"]:
                nf = []
                for vv, nn in s["frames"]:
                    nf.append(([(p[0] * c - p[1] * sn, p[0] * sn + p[1] * c, p[2]) for p in vv],
                               [(n[0] * c - n[1] * sn, n[0] * sn + n[1] * c, n[2]) for n in nn]))
                s["frames"] = nf
        m["name"] = "hackmon_" + k
        md3lib.write(os.path.join(OUT, "hackmon_%s.md3" % k), m)
        screen_texture(os.path.join(OUT, "hm_scr_%s.png" % k), bg, fg, lines, scan)
    for f in os.listdir(SRC):
        if f.startswith("hackmon_") and f.endswith(".png"):
            im = Image.open(os.path.join(SRC, f)).convert("RGB")      # fullbright in game, so tone the body down
            im = im.point(lambda v: int(v * 0.6))
            im.save(os.path.join(OUT, f))


# ------------------------------------------------------------------ fedora
def fedora():
    prof = [(2.3, 0.0), (4.1, 0.0), (4.5, 0.3), (4.2, 0.5), (3.5, 0.22), (2.3, 0.3), (2.15, 1.0), (2.1, 2.0), (1.95, 3.1),
            (1.4, 3.4), (0.6, 2.9), (0.0, 2.8)]
    N = 20
    verts, st, tris = [], [], []
    for i, (r, z) in enumerate(prof):
        for j in range(N + 1):
            th = 2 * math.pi * j / N
            rr = r * (1 + 0.07 * math.cos(2 * th) * min(1.0, z / 2))       # pinched crown
            zz = z - 1.5 + (0.22 * math.sin(th) * min(1.0, r / 4.2) if r > 2.4 else 0.0)   # rolled brim
            if r == 0.0:
                rr = 0.0
            verts.append((rr * math.cos(th), rr * math.sin(th), zz))
            st.append((j / N, i / (len(prof) - 1)))
    W = N + 1
    for i in range(len(prof) - 1):
        for j in range(N):
            a, b, c, d = i * W + j, i * W + j + 1, (i + 1) * W + j, (i + 1) * W + j + 1
            tris += [(a, b, c), (b, d, c)]
    tris = tris + [(a, c, b) for a, b, c in tris]            # double sided: no inside-out hats
    surf_hat = dict(name="hat", shader="progs/fedora_red", tris=tris, st=st, frames=[(verts, vnormals(verts, tris))])

    # band around the crown
    bv, bs, bt = [], [], []
    for i, z in enumerate((0.35, 1.05)):
        for j in range(N + 1):
            th = 2 * math.pi * j / N
            rr = 2.26 + 0.01 * i
            rr = rr * (1 + 0.07 * math.cos(2 * th) * 0.4)
            bv.append((rr * math.cos(th), rr * math.sin(th), z - 1.5))
            bs.append((j / N, i))
    for j in range(N):
        a, b, c, d = j, j + 1, W + j, W + j + 1
        bt += [(a, b, c), (b, d, c)]
    bt = bt + [(a, c, b) for a, b, c in bt]
    surf_band = dict(name="band", shader="progs/fedora_band", tris=bt, st=bs, frames=[(bv, vnormals(bv, bt))])
    md3lib.write(os.path.join(OUT, "fedora.md3"), dict(name="fedora", surfaces=[surf_hat, surf_band], nframes=1))
    Image.new("RGB", (8, 8), (170, 8, 12)).save(os.path.join(OUT, "fedora_red.png"))
    Image.new("RGB", (8, 8), (28, 22, 22)).save(os.path.join(OUT, "fedora_band.png"))


# ------------------------------------------------------------------ lightning
def zap(idx):
    L = 32.0
    pts = [(0.0, 0.0, 0.0)]
    segs = random.randint(6, 9)
    for s in range(1, segs):
        pts.append((L * s / segs, random.uniform(-3.5, 3.5), random.uniform(-3.5, 3.5)))
    pts.append((L, 0.0, 0.0))
    verts, st, tris = [], [], []
    hw = 0.9
    for axis in ((0, 1, 0), (0, 0, 1)):                     # two crossed ribbons
        base = len(verts)
        for i, p in enumerate(pts):
            for side, v in ((-1, 1.0), (1, 0.0)):
                verts.append((p[0], p[1] + axis[1] * side * hw, p[2] + axis[2] * side * hw))
                st.append((i / (len(pts) - 1), v))
        for i in range(len(pts) - 1):
            a, b, c, d = base + 2 * i, base + 2 * i + 1, base + 2 * i + 2, base + 2 * i + 3
            tris += [(a, b, c), (b, d, c), (a, c, b), (b, c, d)]   # both sides
    surf = dict(name="bolt", shader="progs/zap_green", tris=tris, st=st, frames=[(verts, [(0, 0, 1)] * len(verts))])
    md3lib.write(os.path.join(OUT, "zap%d.md3" % idx), dict(name="zap%d" % idx, surfaces=[surf], nframes=1))


def zap_texture():
    im = Image.new("RGB", (8, 16))
    px = im.load()
    for y in range(16):
        t = abs(y - 7.5) / 7.5                       # 0 centre .. 1 edge
        g = int(255 * (1 - t) ** 1.3)
        for x in range(8):
            px[x, y] = (int(g * 0.3), g, int(g * 0.3))
    im.save(os.path.join(OUT, "zap_green.png"))


os.makedirs(OUT, exist_ok=True)
build_monitor()
fedora()
for i in (1, 2, 3):
    zap(i)
zap_texture()
print("hackmon models written to", OUT)
