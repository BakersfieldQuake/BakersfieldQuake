"""The bronze rearing-horse-and-cowboy statue in front of Golden West Casino (Street View photo, Feb 2017: a bronco buster on a
boulder in a round flower bed). Written as progs/gw_horse.md3 (+ .md3_0.skin, gw_horse.png, gw_rock.png); the map places it with
misc_model. Built from tapered tubes and ellipsoids, in feet, facing +x, origin at the middle of the boulder's base.
usage: python make_gw_horse.py [preview.png]"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib  # noqa: E402

PROGS = os.path.normpath(os.path.join(HERE, "..", "..", "progs"))
FT = 12.0
LIFT = 1.55                              # the hooves stand on the boulder
rnd = random.Random(5)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


class Mesh:
    def __init__(self):
        self.v, self.n, self.t = [], [], []

    def grid(self, rows):
        """rows: list of rings (lists of (point, normal)); closed round each ring, joined ring to ring."""
        base = len(self.v)
        m = len(rows[0])
        for ring in rows:
            for p, nn in ring:
                self.v.append(p)
                self.n.append(norm(nn))
        for r in range(len(rows) - 1):
            for k in range(m):
                a, b = base + r * m + k, base + r * m + (k + 1) % m
                c, d = base + (r + 1) * m + k, base + (r + 1) * m + (k + 1) % m
                self.t += [(a, c, b), (b, c, d)]

    def ellipsoid(self, c, axis, radii, n=12, m=8):
        a = norm(axis)
        b = norm(cross(a, (0, 0, 1))) if abs(a[2]) < 0.95 else norm(cross(a, (0, 1, 0)))
        cc = cross(a, b)
        ra, rb, rc = radii
        rows = []
        for i in range(m + 1):
            lat = -math.pi / 2 + math.pi * i / m
            ring = []
            for j in range(n):
                lon = 2 * math.pi * j / n
                x, y, z = math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)
                p = add(c, add(add(mul(a, x * ra), mul(b, y * rb)), mul(cc, z * rc)))
                nl = (x / ra, y / rb, z / rc)
                ring.append((p, add(add(mul(a, nl[0]), mul(b, nl[1])), mul(cc, nl[2]))))
            rows.append(ring)
        self.grid(rows)

    def tube(self, pts, rads, sides=8, steps=3):
        """A tapered tube along a Catmull-Rom curve through pts (radius interpolated), closed with rounded ends."""
        P = [pts[0]] + list(pts) + [pts[-1]]
        R = [rads[0]] + list(rads) + [rads[-1]]
        path = []
        for i in range(1, len(P) - 2):
            for s in range(steps):
                t = s / steps
                q = lambda f: tuple(0.5 * ((2 * f[i][k]) + (-f[i - 1][k] + f[i + 1][k]) * t + (2 * f[i - 1][k] - 5 * f[i][k] + 4 * f[i + 1][k] - f[i + 2][k]) * t * t
                                           + (-f[i - 1][k] + 3 * f[i][k] - 3 * f[i + 1][k] + f[i + 2][k]) * t ** 3) for k in range(3))
                rr = R[i] + (R[i + 1] - R[i]) * t
                path.append((q(P), rr))
        path.append((pts[-1], rads[-1]))
        rows = []
        ref = (0, 0, 1)
        for i, (p, r) in enumerate(path):
            tg = norm(sub(path[min(i + 1, len(path) - 1)][0], path[max(i - 1, 0)][0]))
            if abs(dot(tg, ref)) > 0.95:
                ref = (0, 1, 0)
            u = norm(cross(tg, ref))
            w = cross(tg, u)
            ring = []
            for k in range(sides):
                a = 2 * math.pi * k / sides
                d = add(mul(u, math.cos(a)), mul(w, math.sin(a)))
                ring.append((add(p, mul(d, r)), d))
            rows.append(ring)
        first, last = path[0], path[-1]
        cap0 = [(first[0], mul(sub(path[0][0], path[1][0]), 1))] * sides
        cap1 = [(last[0], mul(sub(path[-1][0], path[-2][0]), 1))] * sides
        self.grid([cap0] + rows + [cap1])


def horse():
    m = Mesh()
    z = (0, 0, LIFT)
    sh = lambda p: add(p, z)
    # --- body
    m.ellipsoid(sh((-1.3, 0, 4.6)), (0.5, 0, 0.86), (1.6, 1.15, 1.15))                  # hindquarters
    m.ellipsoid(sh((0.15, 0, 5.75)), (0.62, 0, 0.78), (2.6, 1.15, 1.2))                 # barrel
    m.ellipsoid(sh((1.5, 0, 6.8)), (0.6, 0, 0.8), (1.3, 1.0, 1.1))                      # chest
    m.tube([sh(p) for p in ((1.6, 0, 7.0), (2.3, 0, 8.2), (3.1, 0, 9.2))], [0.85, 0.65, 0.5], sides=10)   # neck
    m.ellipsoid(sh((3.95, 0, 9.5)), (0.85, 0, -0.5), (1.15, 0.38, 0.45))               # head
    for s in (-1, 1):
        m.tube([sh((3.1, s * 0.2, 9.9)), sh((3.0, s * 0.22, 10.5))], [0.13, 0.05], sides=5)       # ears
        # hind legs
        m.tube([sh(p) for p in ((-1.2, s * 0.8, 4.4), (-1.9, s * 0.75, 3.3), (-2.5, s * 0.65, 1.8), (-1.8, s * 0.62, 0.4))], [0.7, 0.5, 0.28, 0.24])
        m.ellipsoid(sh((-1.7, s * 0.62, 0.15)), (1, 0, 0), (0.5, 0.28, 0.18), n=8, m=5)
        # forelegs, folded
        m.tube([sh(p) for p in ((1.9, s * 0.75, 6.5), (2.8, s * 0.85, 5.6), (3.6, s * 0.8, 6.3), (3.8, s * 0.8, 5.35))], [0.5, 0.34, 0.28, 0.22])
        m.ellipsoid(sh((3.85, s * 0.8, 5.2)), (1, 0, 0), (0.28, 0.22, 0.3), n=8, m=5)
        # rider's legs and boots
        m.tube([sh(p) for p in ((-0.8, s * 0.5, 6.6), (0.2, s * 1.2, 6.0), (0.5, s * 1.45, 4.9))], [0.38, 0.3, 0.25], sides=7)
        m.ellipsoid(sh((0.75, s * 1.45, 4.65)), (1, 0, 0), (0.45, 0.2, 0.18), n=8, m=5)
    m.tube([sh(p) for p in ((-2.3, 0, 4.6), (-3.3, 0, 3.9), (-3.7, 0, 2.6), (-3.6, 0, 1.2))], [0.3, 0.4, 0.35, 0.15])   # tail
    m.tube([sh(p) for p in ((1.9, 0.0, 9.9), (1.5, 0, 8.6), (1.1, 0, 7.5))], [0.22, 0.24, 0.2], sides=6)               # mane
    # --- the cowboy
    m.tube([sh(p) for p in ((-0.8, 0, 6.5), (-0.6, 0, 7.6), (-0.45, 0, 8.45))], [0.6, 0.62, 0.55], sides=8)            # body
    m.ellipsoid(sh((-0.3, 0, 8.95)), (1, 0, 0), (0.36, 0.36, 0.42), n=8, m=6)                                           # head
    m.ellipsoid(sh((-0.3, 0, 9.5)), (1, 0, 0), (1.05, 1.05, 0.07), n=14, m=3)                                           # hat brim
    m.ellipsoid(sh((-0.3, 0, 9.78)), (1, 0, 0), (0.5, 0.5, 0.4), n=10, m=5)                                             # crown
    m.tube([sh(p) for p in ((-0.45, 0.55, 8.2), (0.5, 0.8, 7.7), (1.4, 0.55, 7.4))], [0.28, 0.22, 0.18], sides=6)       # reining arm
    m.tube([sh(p) for p in ((-0.45, -0.55, 8.2), (-1.2, -0.9, 9.0), (-1.8, -1.2, 10.0))], [0.28, 0.22, 0.18], sides=6)  # raised arm
    m.tube([sh(p) for p in ((-1.8, -1.2, 10.0), (-2.6, -1.6, 10.4), (-3.4, -1.6, 9.6))], [0.07, 0.06, 0.05], sides=4)   # quirt
    m.tube([sh(p) for p in ((1.4, 0.55, 7.4), (2.8, 0.3, 8.4), (4.3, 0.05, 8.9))], [0.04, 0.04, 0.04], sides=4)         # reins
    return m


def rock():
    m = Mesh()
    m.ellipsoid((0, 0, 0.2), (1, 0, 0), (3.7, 3.1, 1.6), n=16, m=8)
    for i, p in enumerate(m.v):                                                          # lumpy: displacement from position only
        h = math.sin(p[0] * 2.3 + 1) * math.cos(p[1] * 1.9) * 0.18 + math.sin(p[0] * 5.1 + p[1] * 3.7) * 0.06
        m.v[i] = (p[0] * (1 + h * 0.3), p[1] * (1 + h * 0.3), p[2] + h)
    return m


def finish(mesh, scale_uv):
    st = [((p[0] + p[2] * 0.4) * scale_uv, (p[1] * 0.8 + p[2]) * scale_uv) for p in mesh.v]
    return dict(tris=[tuple(t) for t in mesh.t], st=st, verts=[mul(p, FT) for p in mesh.v], norms=mesh.n)


def textures():
    S = 128
    br = Image.new("RGB", (S, S), (74, 52, 30))
    d = ImageDraw.Draw(br)
    for _ in range(420):                                                                 # dark bronze, a little verdigris in the hollows
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        c = rnd.choice([(52, 86, 70), (110, 80, 44), (92, 64, 36), (58, 40, 24), (58, 40, 24), (92, 64, 36)])
        d.ellipse([x, y, x + rnd.randint(2, 9), y + rnd.randint(4, 16)], fill=c)
    br = br.filter(ImageFilter.GaussianBlur(1.1))
    rk = Image.new("RGB", (S, S), (118, 108, 96))
    d = ImageDraw.Draw(rk)
    for _ in range(700):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        c = rnd.randint(-30, 26)
        d.ellipse([x, y, x + rnd.randint(2, 12), y + rnd.randint(2, 8)], fill=(118 + c, 108 + c, 96 + c))
    return br, rk.filter(ImageFilter.GaussianBlur(0.6))


def preview(parts, path):
    """Painter's-algorithm flat-shaded views (from the side, the front-left and the front) to check the shape."""
    W = 420
    out = Image.new("RGB", (W * 3, 520), (200, 205, 215))
    for vi, yaw in enumerate((0, 35, 90)):
        im = out.crop((vi * W, 0, vi * W + W, 520))
        d = ImageDraw.Draw(im)
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        tris = []
        for tint, part in parts:
            for a, b, c in part["tris"]:
                pts = [part["verts"][i] for i in (a, b, c)]
                rot = [(p[0] * ca + p[1] * sa, -p[0] * sa + p[1] * ca, p[2]) for p in pts]       # x = depth, y = across
                nrm = norm(cross(sub(rot[1], rot[0]), sub(rot[2], rot[0])))
                depth = sum(r[0] for r in rot) / 3
                lum = 0.45 + 0.55 * abs(dot(nrm, norm((-0.4, -0.5, 0.8))))
                tris.append((depth, [(W / 2 + r[1] * 2.9, 500 - (r[2] - 1.0) * 2.9) for r in rot], tuple(int(t * lum) for t in tint)))
        for _, poly, col in sorted(tris, key=lambda t: -t[0]):
            d.polygon(poly, fill=col)
        out.paste(im, (vi * W, 0))
    out.save(path)


def main():
    horse_m, rock_m = horse(), rock()
    parts = [("bronze", finish(horse_m, 0.15)), ("rock", finish(rock_m, 0.15))]
    surfaces = []
    for name, p in parts:
        surfaces.append(dict(name=name, shader="progs/gw_" + ("horse" if name == "bronze" else "rock"), tris=p["tris"], st=p["st"],
                             frames=[(p["verts"], p["norms"])]))
    md3lib.write(os.path.join(PROGS, "gw_horse.md3"), dict(name="gw_horse", surfaces=surfaces))
    with open(os.path.join(PROGS, "gw_horse.md3_0.skin"), "w", newline="\n") as f:
        f.write("bronze,progs/gw_horse\nrock,progs/gw_rock\n")
    br, rk = textures()
    br.save(os.path.join(PROGS, "gw_horse.png"))
    rk.save(os.path.join(PROGS, "gw_rock.png"))
    if len(sys.argv) > 1:
        preview([((176, 128, 70), parts[0][1]), ((150, 140, 128), parts[1][1])], sys.argv[1])
    print("wrote gw_horse.md3:", sum(len(p["tris"]) for _, p in parts), "triangles")


if __name__ == "__main__":
    main()
