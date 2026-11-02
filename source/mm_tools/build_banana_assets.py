"""Builds the banana gun's assets for BakersfieldQuake:
  progs/v_banana.md3 + progs/v_banana.png   first-person banana gun: a big yellow tube
  progs/banana.md3   + progs/banana.png     the banana it shoots (from the NVIDIA SimReady export, CC-BY)
  sound/weapons/bananafire.wav, bananasplat.wav, bananapop.wav

v_banana.md3 frames:  0-7 idle bob   8-15 fire recoil
python -I build_banana_assets.py [outdir]     (default G:\\Quake\\Combat\\BakersfieldQuake)"""
import math
import os
import random
import shutil
import struct
import sys
import wave
import zlib

OUT = sys.argv[1] if len(sys.argv) > 1 else "G:\\Quake\\Combat\\BakersfieldQuake"
EXPORT = "G:\\Downloads\\banana\\export\\progs"
RATE = 22050

# ---------------------------------------------------------------- tuning (view space: x forward, y left, z up)
BASE = (21.0, -10.5, -9.5)    # where the middle of the tube sits in front of the eye
YAW = 9.0                      # turns the muzzle towards the crosshair
PITCH = 5.0                    # nose up
SIDES = 16
SW = {"yellow": 0, "rim": 1, "dark": 2, "green": 3, "light": 4, "stripe": 5}


def uv_of(name):
    return ((SW[name] * 8 + 4) / 64.0, 0.5)


def norm(a):
    l = math.sqrt(sum(c * c for c in a)) or 1.0
    return tuple(c / l for c in a)


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


# ---------------------------------------------------------------- geometry: lathe bands about the X axis
quads = []      # per band: (list of ring0 pts, ring1 pts, normals0, normals1, swatch)
surf_v, surf_n, surf_uv, surf_t = [], [], [], []


def lathe(x0, r0, x1, r1, sw, inward=False):
    """a band of the tube from (x0,r0) to (x1,r1) about the X axis; outward normals (inward flips them)"""
    dx, dr = x1 - x0, r1 - r0
    # profile normal: perpendicular to the segment, pointing away from the axis
    nx, nr = -dr, dx
    l = math.hypot(nx, nr) or 1.0
    nx, nr = nx / l, nr / l
    if nr < 0 or (nr == 0 and nx < 0) and False:
        nx, nr = -nx, -nr
    if dx == 0:                       # flat disc / ring: normal along the axis
        nx, nr = (1.0 if dr < 0 else -1.0), 0.0
        # a disc whose radius shrinks to the axis faces forward at the front, backward at the back (set by caller)
    if inward:
        nx, nr = -nx, -nr
    base = len(surf_v)
    for k in range(SIDES + 1):
        a = 2 * math.pi * k / SIDES
        ca, sa = math.cos(a), math.sin(a)
        for (x, r) in ((x0, r0), (x1, r1)):
            surf_v.append((x, r * ca, r * sa))
            surf_n.append(norm((nx, nr * ca, nr * sa)))
            surf_uv.append(uv_of(sw))
    for k in range(SIDES):
        a, b, c, d = base + 2 * k, base + 2 * k + 1, base + 2 * k + 3, base + 2 * k + 2
        for tri in ((a, b, c), (a, c, d)):
            p0, p1, p2 = (surf_v[i] for i in tri)
            g = cross(sub(p1, p0), sub(p2, p0))
            if dot(g, surf_n[tri[0]]) < 0:
                tri = (tri[0], tri[2], tri[1])
            if math.sqrt(dot(g, g)) > 1e-9:
                surf_t.append(tri)


def disc(x, r, sw, facing):
    """a flat disc at x of radius r, facing +1 (forward) or -1 (back)"""
    base = len(surf_v)
    surf_v.append((x, 0.0, 0.0)); surf_n.append((float(facing), 0.0, 0.0)); surf_uv.append(uv_of(sw))
    for k in range(SIDES + 1):
        a = 2 * math.pi * k / SIDES
        surf_v.append((x, r * math.cos(a), r * math.sin(a))); surf_n.append((float(facing), 0.0, 0.0)); surf_uv.append(uv_of(sw))
    for k in range(SIDES):
        tri = (base, base + 1 + k, base + 2 + k)
        p0, p1, p2 = (surf_v[i] for i in tri)
        if cross(sub(p1, p0), sub(p2, p0))[0] * facing < 0:
            tri = (tri[0], tri[2], tri[1])
        surf_t.append(tri)


def stem(cx, cz, r, h, sw):
    """a short upright cylinder (the banana stem on top): built as a lathe about X then turned to Z"""
    n0 = len(surf_v)
    lathe(0.0, r, h, r * 0.8, sw)
    lathe(h, r * 0.8, h, 0.0, sw)
    for i in range(n0, len(surf_v)):
        x, y, z = surf_v[i]
        surf_v[i] = (cx + y, z, cz + x)          # axis X -> Z
        nx, ny, nz = surf_n[i]
        surf_n[i] = (ny, nz, nx)
    # the axis swap mirrors the mesh; flip winding of what we just added
    for j in range(len(surf_t)):
        if min(surf_t[j]) >= n0:
            t = surf_t[j]
            surf_t[j] = (t[0], t[2], t[1])


# tube: local axis X, centred on the origin
disc(-14.0, 3.8, "dark", -1)
lathe(-14.0, 3.8, -12.5, 4.4, "rim")
lathe(-12.5, 4.4, 11.0, 4.4, "yellow")
for x0 in (-5.0, 3.0):
    lathe(x0, 4.4, x0, 4.8, "stripe")
    lathe(x0, 4.8, x0 + 2.0, 4.8, "stripe")
    lathe(x0 + 2.0, 4.8, x0 + 2.0, 4.4, "stripe")
lathe(11.0, 4.4, 12.5, 5.4, "rim")
lathe(12.5, 5.4, 14.0, 5.4, "rim")
lathe(14.0, 5.4, 14.0, 3.7, "rim")
lathe(14.0, 3.7, 9.0, 3.7, "dark", inward=True)
disc(9.0, 3.7, "dark", 1)
stem(-9.0, 4.2, 0.8, 2.2, "green")
BASE_COUNT = len(surf_v)

# ---------------------------------------------------------------- frames
FR = []
for i in range(8):
    ph = 2 * math.pi * i / 8
    FR.append((0.0 + 0.6 * math.sin(ph), 0.0, 0.35 * math.sin(ph + 0.6), 0.5 * math.sin(ph)))
# fire recoil: (dx, dy, dz, extra pitch)
FR += [(-1.5, 0.0, 0.2, 2.0), (-5.5, 0.0, 0.8, 7.0), (-7.0, 0.0, 1.0, 9.0), (-6.0, 0.0, 0.8, 7.0),
       (-4.0, 0.0, 0.5, 5.0), (-2.4, 0.0, 0.3, 3.0), (-1.2, 0.0, 0.1, 1.5), (-0.4, 0.0, 0.0, 0.5)]
NFRAMES = len(FR)


def xform(p, fr, is_n=False):
    dx, dy, dz, dp = fr
    a = math.radians(PITCH + dp)
    x = p[0] * math.cos(a) - p[2] * math.sin(a)
    z = p[0] * math.sin(a) + p[2] * math.cos(a)
    y = p[1]
    c, s = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
    x, y = x * c - y * s, x * s + y * c
    if is_n:
        return (x, y, z)
    return (x + BASE[0] + dx, y + BASE[1] + dy, z + BASE[2] + dz)


# ---------------------------------------------------------------- MD3 writer
def name64(s): return s.encode("ascii")[:63].ljust(64, b"\0")


def enc_normal(n):
    x, y, z = norm(n)
    lng = int(round(math.acos(max(-1.0, min(1.0, z))) * 255 / (2 * math.pi))) & 255
    lat = int(round(math.atan2(y, x) * 255 / (2 * math.pi))) & 255
    return (lng << 8) | lat


def write_md3(path, modelname, shader):
    nv, nt = len(surf_v), len(surf_t)
    tri_b = b"".join(struct.pack("<3i", *t) for t in surf_t)
    sh_b = name64(shader) + struct.pack("<i", 0)
    st_b = b"".join(struct.pack("<2f", u, v) for u, v in surf_uv)
    xyz, frames_b = [], b""
    for fr in FR:
        pts = [xform(p, fr) for p in surf_v]
        mn = [min(p[k] for p in pts) for k in range(3)]
        mx = [max(p[k] for p in pts) for k in range(3)]
        rad = max(math.sqrt(sum(c * c for c in p)) for p in pts)
        frames_b += struct.pack("<3f3f3ff", *mn, *mx, 0.0, 0.0, 0.0, rad) + name64("f")[:16]
        for p, n in zip(pts, surf_n):
            xyz.append(struct.pack("<3hH", *[max(-32768, min(32767, int(round(c * 64)))) for c in p], enc_normal(xform(n, fr, True))))
    xyz_b = b"".join(xyz)
    hs = 4 + 64 + 40
    o_tri = hs; o_sh = o_tri + len(tri_b); o_st = o_sh + len(sh_b); o_xyz = o_st + len(st_b); o_end = o_xyz + len(xyz_b)
    surf = b"IDP3" + name64("tube") + struct.pack("<10i", 0, NFRAMES, 1, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end) + tri_b + sh_b + st_b + xyz_b
    HDR = 108
    hdr = b"IDP3" + struct.pack("<i", 15) + name64(modelname) + struct.pack("<9i", 0, NFRAMES, 0, 1, 0, HDR, HDR + len(frames_b), HDR + len(frames_b), HDR + len(frames_b) + len(surf))
    open(path, "wb").write(hdr + frames_b + surf)
    print("wrote", path, os.path.getsize(path), "bytes;", nt, "tris;", NFRAMES, "frames")


def png_chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)


def write_png(path, w, h, rows):
    raw = b"".join(b"\0" + b"".join(bytes(px) for px in row) for row in rows)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b""))


# ---------------------------------------------------------------- sounds
def write_wav(path, samples, peak):
    m = max(abs(s) for s in samples) or 1.0
    k = peak / m
    with wave.open(path, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(RATE)
        f.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s * k)) * 32767)) for s in samples))
    print("wrote", path, "%.2fs" % (len(samples) / RATE))


def lowpass(x, cutoff):
    a = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    y, out = 0.0, []
    for v in x:
        y += a * (v - y)
        out.append(y)
    return out


def fire_sound():
    """foomp: a fat thump that drops in pitch, a cartoon 'bloop' on top"""
    rng = random.Random(3)
    n = int(RATE * 0.45)
    out, ph1, ph2 = [], 0.0, 0.0
    noise = lowpass([rng.uniform(-1, 1) for _ in range(n)], 900)
    for i in range(n):
        t = i / RATE
        f1 = 55 + 140 * math.exp(-t / 0.06)
        ph1 += 2 * math.pi * f1 / RATE
        f2 = 260 + 700 * math.exp(-t / 0.05)
        ph2 += 2 * math.pi * f2 / RATE
        out.append(1.0 * math.exp(-t / 0.16) * math.sin(ph1) + 0.45 * math.exp(-t / 0.07) * math.sin(ph2) + 0.5 * math.exp(-t / 0.03) * noise[i])
    return [math.tanh(1.4 * s) for s in out]


def splat_sound():
    """squish: wet noise bursts under a low thud"""
    rng = random.Random(11)
    n = int(RATE * 0.6)
    raw = [rng.uniform(-1, 1) for _ in range(n)]
    wet = lowpass(raw, 1400)
    out = []
    for i in range(n):
        t = i / RATE
        gurgle = 0.5 + 0.5 * math.sin(2 * math.pi * (22 - 14 * t) * t * 6)
        thud = math.exp(-t / 0.09) * math.sin(2 * math.pi * (70 + 60 * math.exp(-t / 0.05)) * t)
        out.append(1.3 * thud + 1.1 * wet[i] * math.exp(-t / 0.22) * (0.35 + gurgle) + 0.6 * raw[i] * math.exp(-t / 0.012))
    return [math.tanh(1.2 * s) for s in out]


def pop_sound():
    n = int(RATE * 0.12)
    out, ph = [], 0.0
    for i in range(n):
        t = i / RATE
        ph += 2 * math.pi * (180 + 900 * math.exp(-t / 0.02)) / RATE
        out.append(math.exp(-t / 0.035) * math.sin(ph))
    return out


if __name__ == "__main__":
    pdir = os.path.join(OUT, "progs")
    sdir = os.path.join(OUT, "sound", "weapons")
    os.makedirs(pdir, exist_ok=True)
    os.makedirs(sdir, exist_ok=True)
    write_md3(os.path.join(pdir, "v_banana.md3"), "v_banana", "progs/v_banana")
    # swatches (8x8 each); the engine lights these models ~2.4x too bright, so scale the colours down like mm_hand.png
    cols = [(238, 200, 24), (196, 120, 20), (40, 30, 20), (70, 140, 40), (255, 235, 110), (120, 70, 20), (255, 255, 255), (255, 255, 255)]
    cols = [tuple(int(c * 0.5) for c in col) for col in cols]
    write_png(os.path.join(pdir, "v_banana.png"), 64, 8, [[cols[x // 8] for x in range(64)] for _ in range(8)])
    for n in ("banana.md3", "banana.png"):
        shutil.copy(os.path.join(EXPORT, n), os.path.join(pdir, n))
    write_wav(os.path.join(sdir, "bananafire.wav"), fire_sound(), 0.9)
    write_wav(os.path.join(sdir, "bananasplat.wav"), splat_sound(), 0.95)
    write_wav(os.path.join(sdir, "bananapop.wav"), pop_sound(), 0.8)
