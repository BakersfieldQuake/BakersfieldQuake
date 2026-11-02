"""Assets for the Wheelman Cannon: progs/wc_bar.md3, the long metal bar (a barbell: shaft + two plates) that flies out of
the crash, and its texture progs/wc_bar.png.
python3.13 build_wcannon_assets.py        (PIL; run it without -I)"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

MOD = os.path.abspath(os.path.join(HERE, "..", ".."))


def cylinder(x0, x1, r, sides=14, uv=(0.0, 0.0, 1.0, 1.0)):
    """A tube along +X from x0 to x1 with end caps; returns (verts, normals, st, tris)."""
    verts, norms, st, tris = [], [], [], []
    u0, v0, u1, v1 = uv
    base = len(verts)
    for i in range(sides + 1):
        a = 2 * math.pi * i / sides
        y, z = math.cos(a) * r, math.sin(a) * r
        n = (0.0, math.cos(a), math.sin(a))
        for x in (x0, x1):
            verts.append((x, y, z))
            norms.append(n)
            st.append((u0 + (u1 - u0) * i / sides, v0 + (v1 - v0) * (0 if x == x0 else 1)))
    for i in range(sides):
        a, b, c, d = base + 2 * i, base + 2 * i + 1, base + 2 * i + 2, base + 2 * i + 3
        tris += [(a, c, b), (b, c, d)]
    for x, nx, flip in ((x0, -1.0, True), (x1, 1.0, False)):
        cb = len(verts)
        verts.append((x, 0.0, 0.0))
        norms.append((nx, 0.0, 0.0))
        st.append(((u0 + u1) / 2, (v0 + v1) / 2))
        for i in range(sides + 1):
            a = 2 * math.pi * i / sides
            verts.append((x, math.cos(a) * r, math.sin(a) * r))
            norms.append((nx, 0.0, 0.0))
            st.append(((u0 + u1) / 2 + math.cos(a) * 0.1, (v0 + v1) / 2 + math.sin(a) * 0.1))
        for i in range(sides):
            p, q = cb + 1 + i, cb + 2 + i
            tris.append((cb, q, p) if flip else (cb, p, q))
    return verts, norms, st, tris


def merge(parts):
    V, N, S, T = [], [], [], []
    for v, n, s, t in parts:
        o = len(V)
        V += v
        N += n
        S += s
        T += [(a + o, b + o, c + o) for a, b, c in t]
    return V, N, S, T


def texture(path):
    """Brushed steel: horizontal streaks over a light-grey gradient (the plates take the darker lower half)."""
    img = Image.new("RGB", (64, 64))
    px = img.load()
    for y in range(64):
        for x in range(64):
            streak = ((x * 7 + y * 13) % 11) * 2
            if y < 32:
                base = 150 + 70 * math.sin(math.pi * y / 31.0)
            else:
                base = 55 + 30 * math.sin(math.pi * (y - 32) / 31.0)
            v = max(0, min(255, int(base + streak - 10)))
            px[x, y] = (v, v, min(255, v + 8))
    img.save(path)


def main():
    shaft = cylinder(-36, 36, 2.0, uv=(0.0, 0.0, 1.0, 0.45))
    plate_a = cylinder(-34, -28, 7.5, uv=(0.0, 0.55, 1.0, 1.0))
    plate_b = cylinder(28, 34, 7.5, uv=(0.0, 0.55, 1.0, 1.0))
    v, n, s, t = merge([shaft, plate_a, plate_b])
    model = dict(name="wc_bar", surfaces=[dict(name="bar", shader="progs/wc_bar", tris=t, st=s, frames=[(v, n)])], nframes=1)
    md3lib.write(os.path.join(MOD, "progs", "wc_bar.md3"), model)
    texture(os.path.join(MOD, "progs", "wc_bar.png"))
    print("wrote progs/wc_bar.md3 (%d verts, %d tris) and progs/wc_bar.png" % (len(v), len(t)))


if __name__ == "__main__":
    main()
