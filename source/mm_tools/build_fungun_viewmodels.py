"""Builds the first-person models for the fun guns (progs/v_<gun>.md3) from the converted SimReady props.

Each prop is placed in front of the eye (x forward, y left, z up), turned so it reads as held, and given
22 frames that the QC plays (FunGun_ViewFrame):
  0-15  idle bob (10 fps loop)
  16-18 fire kick, settling
  19    gone (thrown guns: the prop has left the hand)
  20-21 coming back up into view
The textures are the props' own (same shader names), so copy progs/<prop>_*.png next to the v_ models.
python -I build_fungun_viewmodels.py <props_dir> <outdir>"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

props_dir, outdir = sys.argv[1:3]

# prop, out name, scale, (roll, pitch, yaw) degrees, position of the prop's centre in eye space
GUNS = [
    ("sledge", "v_sledge", 2.06, (13, 81, 116), (14.0, -8.5, -9.6)),
    ("paddle", "v_paddle", 1.1, (0, -100, -20), (17, -6.5, -1)),     # held up, handle down, face to you
    ("hackmon_a", "v_hackmon", 2.2, (0, -8, 180), (19, -6.5, -6.5)),     # the monitor, screen turned towards you
]


def rot_x(p, d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rot_y(p, d):       # positive tips +X down towards -Z
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rot_z(p, d):       # positive turns +X towards +Y (left)
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def pose(p, roll, pitch, yaw):
    return rot_z(rot_y(rot_x(p, roll), pitch), yaw)


# per frame: (dx, dz, pitch kick)
FRAMES = []
for i in range(16):
    ph = 2 * math.pi * i / 16
    FRAMES.append((0.0, 0.35 * math.sin(ph), 1.2 * math.sin(ph + 0.7)))
FRAMES += [(-3.5, 0.6, -9.0), (-1.8, 0.3, -4.5), (-0.6, 0.1, -1.5),
           (0.0, -45.0, 0.0), (0.0, -14.0, 3.0), (0.0, -4.0, 1.0)]

if os.environ.get("ONLY"):
    GUNS = [g for g in GUNS if g[1] == os.environ["ONLY"]]
os.makedirs(os.path.join(outdir, "progs"), exist_ok=True)
for prop, out, scale, (roll, pitch, yaw), pos in GUNS:
    m = md3lib.read(os.path.join(props_dir, prop + ".md3"))
    allv = [v for s in m["surfaces"] for v in s["frames"][0][0]]
    ctr = [(min(v[k] for v in allv) + max(v[k] for v in allv)) / 2 for k in range(3)]
    for s in m["surfaces"]:
        vv0, nn0 = s["frames"][0]
        base_v = [pose(((v[0] - ctr[0]) * scale, (v[1] - ctr[1]) * scale, (v[2] - ctr[2]) * scale), roll, pitch, yaw) for v in vv0]
        base_n = [pose(n, roll, pitch, yaw) for n in nn0]
        frames = []
        for dx, dz, kick in FRAMES:
            vv = [rot_y(v, kick) for v in base_v]
            nn = [rot_y(n, kick) for n in base_n]
            vv = [(v[0] + pos[0] + dx, v[1] + pos[1], v[2] + pos[2] + dz) for v in vv]
            frames.append((vv, nn))
        s["frames"] = frames
    m["name"] = out
    path = os.path.join(outdir, "progs", out + ".md3")
    md3lib.write(path, m)
    print("wrote", path, os.path.getsize(path), "bytes,", len(FRAMES), "frames")


# ---------------------------------------------------------------- small projectiles: a paint blob and a ping-pong ball
def sphere(name, radius, rgb, lumps=0.0, segs=12, rings=8):
    import random
    import struct
    import zlib
    random.seed(name)
    verts, norms, st, tris = [], [], [], []
    for r in range(rings + 1):
        th = math.pi * r / rings
        for s in range(segs + 1):
            ph = 2 * math.pi * s / segs
            n = (math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))
            k = radius * (1 + (random.uniform(-lumps, lumps) if 0 < r < rings and s < segs else 0))
            verts.append((n[0] * k, n[1] * k, n[2] * k))
            norms.append(n)
            st.append((s / segs, r / rings))
    for r in range(rings):
        for s in range(segs):
            a = r * (segs + 1) + s
            b, c, d = a + 1, a + segs + 1, a + segs + 2
            tris.append((a, c, b))
            tris.append((b, c, d))
    m = dict(name=name, surfaces=[dict(name=name, shader="progs/" + name, tris=tris, st=st, frames=[(verts, norms)])])
    md3lib.write(os.path.join(outdir, "progs", name + ".md3"), m)
    # 8x8 flat-colour png
    raw = b"".join(b"\0" + bytes(rgb) * 8 for _ in range(8))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    open(os.path.join(outdir, "progs", name + ".png"), "wb").write(png)
    print("wrote", name)


sphere("fg_pongball", 2.2, (255, 140, 30))


# ---------------------------------------------------------------- the props' textures, darkened: Combat+ lights models
# about 2x too bright for these photo-real colours (same fix as the Mega Man hand)
def darken_textures(factor=0.5):
    from PIL import Image
    import glob
    for prop, *_ in GUNS:
        for src in glob.glob(os.path.join(props_dir, prop + "_*.png")):
            im = Image.open(src).convert("RGB")
            im = im.point(lambda v: int(v * factor))
            im.save(os.path.join(outdir, "progs", os.path.basename(src)))
    print("darkened prop textures x%.2f" % factor)


darken_textures()
