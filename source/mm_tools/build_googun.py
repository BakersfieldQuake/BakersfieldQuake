"""The Goo Gun models (it replaces the single-barrel shotgun, see goo.qc), written straight into BakersfieldQuake/progs:
  v_googun.md3   first-person model: 0 idle, 1-6 the fire kick (player_shot1..6 drive weaponframe like v_shot.mdl)
  p_googun.md3   third-person model in the player's hands: it rides p_shot.md3's 259 frames (the shotgun is rigid,
                 so every frame is the shotgun's frame-0 -> frame-N transform applied to the goo gun)
  goo.md3        a goo blob: a cluster of lumpy puffs. 0 full size, 1 squeezed into a small glob (the shot in flight),
                 2-5 the splat growing out of the glob with a little overshoot (DarkPlaces lerps between them)
  googun_*.png, goo.png  the textures (procedural; Combat+ lights models ~2x bright, so they are authored dark)

The gun is modelled in gun space: x forward (rear end at 0, muzzle at ~47), y left, z up. All primitives are lathes
(surfaces of revolution, optionally elliptical) and boxes; each material is one md3 surface.
python -I build_googun.py [progs_dir]"""
import io
import math
import os
import random
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib

from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else r"G:\Quake\Combat\BakersfieldQuake\progs"
Q15_PK3 = r"G:\Quake\Combat\quake15\q15.pk3"


# ------------------------------------------------------------------ vector helpers
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


# a frame is (origin, X, Y, Z): columns of a rotation plus a translation
def frame_apply(f, p):
    o, X, Y, Z = f
    return (o[0] + X[0] * p[0] + Y[0] * p[1] + Z[0] * p[2],
            o[1] + X[1] * p[0] + Y[1] * p[1] + Z[1] * p[2],
            o[2] + X[2] * p[0] + Y[2] * p[1] + Z[2] * p[2])


def frame_rot(f, n):
    return frame_apply(((0, 0, 0),) + tuple(f[1:]), n)


def frame_along(origin, axis, up_hint=(0, 0, 1)):
    """frame whose local +X runs along axis"""
    X = norm(axis)
    if abs(dot(X, up_hint)) > 0.95:
        up_hint = (0, 1, 0) if abs(X[1]) < 0.9 else (1, 0, 0)
    Y = norm(cross(up_hint, X))
    Z = cross(X, Y)
    return (origin, X, Y, Z)


IDENT = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))


# ------------------------------------------------------------------ mesh building
class Mesh:
    def __init__(self):
        self.mats = {}      # material -> [verts, norms, st, tris]

    def put(self, mat, verts, norms, st, tris, f=IDENT):
        m = self.mats.setdefault(mat, [[], [], [], []])
        base = len(m[0])
        m[0] += [frame_apply(f, v) for v in verts]
        m[1] += [norm(frame_rot(f, n)) for n in norms]
        m[2] += st
        m[3] += [(a + base, b + base, c + base) for a, b, c in tris]


def smooth_normals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        n = cross(sub(verts[b], verts[a]), sub(verts[c], verts[a]))
        for i in (a, b, c):
            for k in range(3):
                acc[i][k] += n[k]
    return [norm(a) for a in acc]


def lathe(mesh, mat, profile, f=IDENT, segs=16, sy=1.0, sz=1.0, a0=0.0, a1=360.0, ustretch=1.0, flat=False, vscale=None):
    """surface of revolution round local +X. profile = [(x, r), ...] from one end to the other; a repeated point
    makes a hard edge. sy/sz squash the circle into an ellipse; a0..a1 a partial sweep (degrees, 0 = +Z/up)."""
    cols = segs + 1
    xs = [p[0] for p in profile]
    span = (max(xs) - min(xs)) or 1.0
    verts, st, tris = [], [], []
    for i, (x, r) in enumerate(profile):
        for j in range(cols):
            th = math.radians(a0 + (a1 - a0) * j / segs)
            verts.append((x, -math.sin(th) * r * sy, math.cos(th) * r * sz))
            v = (x - min(xs)) / span if vscale is None else (x - min(xs)) * vscale
            st.append((j / segs * ustretch, v))
    for i in range(len(profile) - 1):
        if profile[i] == profile[i + 1]:
            continue
        for j in range(segs):
            a = i * cols + j
            b, c, d = a + 1, a + cols, a + cols + 1
            tris.append((a, b, c))
            tris.append((b, d, c))
    if flat:
        uv, us, ut = [], [], []
        for t in tris:
            for k in t:
                uv.append(verts[k])
                us.append(st[k])
            ut.append((len(uv) - 3, len(uv) - 2, len(uv) - 1))
        verts, st, tris = uv, us, ut
    norms = smooth_normals(verts, tris)     # a repeated profile point is not joined, so that row gets its own normals: a hard edge
    mesh.put(mat, verts, norms, st, tris, f)


def box(mesh, mat, lo, hi, f=IDENT, uvscale=0.08):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    faces = [  # (normal, 4 corners counter-clockwise seen from outside)
        ((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]),
        ((-1, 0, 0), [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)]),
        ((0, 1, 0), [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)]),
        ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),
        ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
        ((0, 0, -1), [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)]),
    ]
    verts, norms, st, tris = [], [], [], []
    for n, quad in faces:
        b = len(verts)
        for p in quad:
            verts.append(p)
            norms.append(n)
            if n[0]:
                st.append((p[1] * uvscale, p[2] * uvscale))
            elif n[1]:
                st.append((p[0] * uvscale, p[2] * uvscale))
            else:
                st.append((p[0] * uvscale, p[1] * uvscale))
        tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    mesh.put(mat, verts, norms, st, tris, f)


def torus_arc(mesh, mat, R, r, a0, a1, f=IDENT, segs=14, sides=8):
    """a ring of radius R (tube radius r) in the local XZ plane, swept from angle a0 to a1 (degrees, 0 = +X, 90 = +Z)"""
    verts, st, tris = [], [], []
    for i in range(segs + 1):
        th = math.radians(a0 + (a1 - a0) * i / segs)
        c = (math.cos(th) * R, 0.0, math.sin(th) * R)
        out = (math.cos(th), 0.0, math.sin(th))
        for j in range(sides + 1):
            ph = 2 * math.pi * j / sides
            d = add(mul(out, math.cos(ph)), mul((0, 1, 0), math.sin(ph)))
            verts.append(add(c, mul(d, r)))
            st.append((i / segs, j / sides))
    for i in range(segs):
        for j in range(sides):
            a = i * (sides + 1) + j
            b, c2, d = a + 1, a + sides + 1, a + sides + 2
            tris.append((a, c2, b))
            tris.append((b, c2, d))
    mesh.put(mat, verts, smooth_normals(verts, tris), st, tris, f)


def rod(mesh, mat, p0, p1, r, segs=8):
    L = math.sqrt(dot(sub(p1, p0), sub(p1, p0)))
    lathe(mesh, mat, [(0, 0), (0, r), (0, r), (L, r), (L, r), (L, 0)], frame_along(p0, sub(p1, p0)), segs=segs)


# ------------------------------------------------------------------ the gun
def build_gun():
    m = Mesh()
    T = 15  # degrees: the pistol grip leans back, the tank bottom swings back

    # rear section: black foam-covered tube with a rubber end cap
    lathe(m, "foam", [(0.0, 0.0), (0.0, 2.2), (0.35, 2.75), (0.9, 2.95), (0.9, 2.95), (1.3, 2.8), (14.6, 2.8), (14.6, 2.8), (14.6, 0.0)],
          segs=18, vscale=0.07, ustretch=2)
    # yellow decal wrapped over the top of the rear tube (hazard chevrons, no logos)
    lathe(m, "decal", [(3.6, 2.84), (10.8, 2.84)], segs=10, a0=-62, a1=62)
    # collar into the metal tube
    lathe(m, "dark", [(14.2, 0), (14.2, 3.05), (14.2, 3.05), (16.0, 3.05), (16.0, 3.05), (16.0, 2.1)], segs=18)
    # main metal tube
    lathe(m, "metal", [(16.0, 2.05), (37.0, 2.05)], segs=18, vscale=0.05, ustretch=1)
    # rings along the tube
    for x in (25.6, 30.4):
        lathe(m, "dark", [(x, 2.05), (x, 2.4), (x, 2.4), (x + 0.8, 2.4), (x + 0.8, 2.4), (x + 0.8, 2.05)], segs=18)
    # front head: chunky housing, a hex nut, the nozzle
    lathe(m, "dark", [(36.6, 2.05), (36.6, 3.1), (36.6, 3.1), (37.2, 3.25), (41.6, 3.25), (42.3, 3.0), (42.3, 3.0), (42.3, 2.2)],
          segs=18, vscale=0.08)
    lathe(m, "metal", [(42.3, 2.2), (42.3, 2.75), (44.4, 2.75), (44.4, 2.75), (44.4, 1.9)], segs=6, flat=True, a0=30, a1=390)
    lathe(m, "metal", [(44.4, 1.9), (44.4, 1.75), (46.6, 1.55), (46.9, 1.45), (46.9, 1.45), (46.9, 1.05)], segs=16)
    lathe(m, "hole", [(46.9, 1.05), (46.3, 1.05), (46.3, 0.0)], segs=16)
    # grinder-style gear cap on top of the head
    lathe(m, "dark", [(0, 0), (0, 2.3), (0, 2.3), (1.6, 2.3), (2.0, 2.0), (2.0, 2.0), (2.0, 0)],
          frame_along((39.4, 0, 2.6), (0, 0, 1), (1, 0, 0)), segs=16)
    lathe(m, "metal", [(0, 0), (0, 1.0), (0, 1.0), (0.7, 1.0), (0.7, 1.0), (0.7, 0)],
          frame_along((39.4, 0, 4.6), (0, 0, 1), (1, 0, 0)), segs=10)

    # top valve block with fittings and a hose into the head
    box(m, "metal", (24.6, -1.55, 1.7), (31.8, 1.55, 4.0))
    box(m, "dark", (26.6, -1.15, 4.0), (29.8, 1.15, 5.0))
    rod(m, "metal", (31.0, -0.6, 3.6), (31.0, -0.6, 6.0), 0.45)
    lathe(m, "dark", [(0, 0), (0, 0.95), (0, 0.95), (0.45, 0.95), (0.45, 0.95), (0.45, 0)],
          frame_along((31.0, -0.6, 6.0), (0, 0, 1), (1, 0, 0)), segs=10)
    rod(m, "rubber", (31.8, 0.9, 3.0), (37.4, 0.9, 2.9), 0.42)
    rod(m, "metal", (25.2, 1.2, 4.0), (25.2, 1.2, 5.3), 0.35)

    # mount block under the tube that the tank hangs from
    box(m, "dark", (18.8, -1.7, -3.1), (24.6, 1.7, -1.2))

    # the goo tank: tilted canister, label texture runs along it
    tank_top = (22.4, 0.0, -2.9)
    tank_dir = (-math.sin(math.radians(T)), 0.0, -math.cos(math.radians(T)))
    tf = frame_along(tank_top, tank_dir, (1, 0, 0))
    lathe(m, "metal", [(0, 1.45), (1.1, 1.45), (1.1, 1.45), (1.1, 2.7), (1.7, 3.15), (2.3, 3.3), (2.3, 3.3), (2.3, 3.3)], tf, segs=20)
    lathe(m, "tank", [(2.3, 3.3), (11.2, 3.3)], tf, segs=20)
    lathe(m, "metal", [(11.2, 3.3), (11.8, 3.05), (12.2, 2.4), (12.35, 1.2), (12.4, 0.0)], tf, segs=20)
    lathe(m, "black", [(9.3, 3.3), (9.3, 3.48), (9.3, 3.48), (10.3, 3.48), (10.3, 3.48), (10.3, 3.3)], tf, segs=20)
    lathe(m, "black", [(2.6, 3.3), (2.6, 3.42), (2.6, 3.42), (3.1, 3.42), (3.1, 3.42), (3.1, 3.3)], tf, segs=20)

    # pistol grip (elliptical, leaning back) with a trigger and guard
    gf = frame_along((10.6, 0.0, -2.2), (-math.sin(math.radians(T)), 0, -math.cos(math.radians(T))), (1, 0, 0))
    lathe(m, "black", [(0.0, 1.55), (0.6, 1.62), (2.4, 1.5), (4.4, 1.62), (6.6, 1.5), (8.6, 1.7), (9.3, 1.75), (9.3, 1.75), (9.6, 1.4), (9.6, 1.4), (9.6, 0.0)],
          gf, segs=14, sy=0.78, sz=1.0)
    # (in the grip's frame local Z points along gun -X/+X; the ellipse is long front-to-back)
    torus_arc(m, "black", 2.7, 0.34, 180, 360, ((14.2, 0, -2.6), (1, 0, 0), (0, 1, 0), (0, 0, 1)), segs=12)
    box(m, "metal", (12.6, -0.32, -5.0), (13.3, 0.32, -2.4))

    # front side handle: metal stem, ribbed black grip, flared end knob
    hf = frame_along((33.4, 0.0, -1.9), (math.sin(math.radians(8)), 0, -1.0), (1, 0, 0))
    lathe(m, "metal", [(0, 1.0), (1.6, 1.0), (1.6, 1.0), (1.6, 1.3)], hf, segs=12)
    prof = [(1.6, 1.3)]
    x = 1.6
    while x < 9.6:
        prof += [(x + 0.35, 1.38), (x + 0.75, 1.2)]
        x += 0.8
    prof += [(9.8, 1.25), (10.2, 1.7), (10.8, 1.75), (11.1, 1.5), (11.1, 1.5), (11.1, 0.0)]
    lathe(m, "rubber", prof, hf, segs=12)
    return m


# ------------------------------------------------------------------ textures
def noise_img(w, h, base, amp, seed, streak=False, blur=0.8):
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        row = rnd.uniform(-amp, amp) if streak else 0
        for x in range(w):
            k = row + rnd.uniform(-amp, amp) * (0.35 if streak else 1)
            px[x, y] = tuple(max(0, min(255, int(c + k))) for c in base)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im


def save(im, name):
    p = os.path.join(OUT, name + ".png")
    im.save(p)
    print("wrote", p)


def build_textures():
    # brushed steel: streaks run along the tube (texture v), so streak rows on the transposed image
    save(noise_img(64, 64, (96, 98, 102), 12, 1, streak=True).transpose(Image.Transpose.TRANSPOSE), "googun_metal")
    save(noise_img(64, 64, (58, 60, 64), 8, 2, streak=True).transpose(Image.Transpose.TRANSPOSE), "googun_dark")
    save(noise_img(64, 64, (20, 20, 22), 5, 3), "googun_black")
    save(noise_img(64, 64, (16, 16, 17), 4, 6, blur=0), "googun_rubber")
    foam = noise_img(64, 64, (24, 24, 26), 7, 4, blur=0.4)
    save(foam, "googun_foam")
    save(Image.new("RGB", (8, 8), (3, 3, 3)), "googun_hole")

    # decal: yellow plate, black chevrons, a thin black border
    d = Image.new("RGB", (128, 64), (196, 150, 12))
    dr = ImageDraw.Draw(d)
    dr.rectangle([0, 0, 127, 63], outline=(15, 15, 15), width=3)
    for i in range(3):
        x = 70 + i * 16
        dr.polygon([(x, 14), (x + 9, 14), (x + 19, 32), (x + 9, 50), (x, 50), (x + 10, 32)], fill=(15, 15, 15))
    dr.rectangle([12, 18, 58, 24], fill=(15, 15, 15))
    dr.rectangle([12, 30, 50, 34], fill=(15, 15, 15))
    dr.rectangle([12, 40, 56, 44], fill=(15, 15, 15))
    save(d.transpose(Image.Transpose.TRANSPOSE), "googun_decal")

    # tank: brushed silver with a pale label band and warning text bars
    t = noise_img(128, 128, (94, 96, 100), 10, 5, streak=True)
    tr = ImageDraw.Draw(t)
    tr.rectangle([0, 34, 127, 92], fill=(150, 148, 140))
    tr.rectangle([0, 34, 127, 37], fill=(30, 30, 30))
    tr.rectangle([0, 89, 127, 92], fill=(30, 30, 30))
    for k, x in enumerate(range(6, 128, 32)):
        tr.text((x, 42), "GOO", fill=(25, 25, 25))
        tr.rectangle([x, 58, x + 22, 60], fill=(60, 60, 60))
        tr.rectangle([x, 65, x + 16, 67], fill=(60, 60, 60))
        tr.polygon([(x + 4, 84), (x + 10, 72), (x + 16, 84)], outline=(25, 25, 25), fill=(196, 150, 12))
    save(t, "googun_tank")

    save(goo_texture(), "goo")


def wrap_blur(im, r):
    """Gaussian blur that wraps at the edges, so the texture still tiles"""
    w, h = im.size
    big = Image.new(im.mode, (w * 3, h * 3))
    for i in range(3):
        for j in range(3):
            big.paste(im, (i * w, j * h))
    return big.filter(ImageFilter.GaussianBlur(r)).crop((w, h, w * 2, h * 2))


GOO_GREY = int(os.environ.get("GG_GOO_GREY", "34"))     # Combat+ lights models ~2x and r_hdr_scenebrightness is 2.5: 34 shows as a mid grey


def goo_texture():
    """goo: grey hardened foam. Lumpy cells, then lots of small pores (dark pit, light lip), tileable"""
    n = 256
    rnd = random.Random(11)
    g = GOO_GREY
    im = noise_img(n, n, (g, g, g + 2), 7, 9, blur=0)
    px = im.load()

    def dab(cx, cy, rr, fn):
        for y in range(int(cy - rr) - 1, int(cy + rr) + 2):
            for x in range(int(cx - rr) - 1, int(cx + rr) + 2):
                dd = math.hypot(x - cx, y - cy) / rr
                if dd < 1:
                    xx, yy = x % n, y % n
                    k = fn(dd)
                    px[xx, yy] = tuple(max(0, min(255, int(c + k))) for c in px[xx, yy])
    # big soft lumps: lighter tops, darker creases between them
    for _ in range(70):
        dab(rnd.uniform(0, n), rnd.uniform(0, n), rnd.uniform(14, 34), lambda d: 13 * (1 - d) ** 1.5 - (9 if d > 0.85 else 0))
    im = wrap_blur(im, 2.5)
    px = im.load()
    # pores
    for _ in range(520):
        rr = rnd.choice((1.6, 2.0, 2.4, 3.0, 3.0, 4.0, 5.5))
        dab(rnd.uniform(0, n), rnd.uniform(0, n), rr, lambda d: -34 * (1 - d / 0.75) if d < 0.75 else 12 * (1 - (d - 0.75) / 0.25))
    # fine grain
    for y in range(n):
        for x in range(n):
            k = rnd.uniform(-5, 5)
            px[x, y] = tuple(max(0, min(255, int(c + k))) for c in px[x, y])
    return wrap_blur(im, 0.6)


def to_model(mesh, name, frames_fn):
    """frames_fn(verts, norms) -> list of (verts, norms) per frame"""
    surfaces = []
    for mat, (vv, nn, st, tris) in sorted(mesh.mats.items()):
        surfaces.append(dict(name=mat, shader="progs/googun_" + mat if mat != "goo" else "progs/goo", tris=tris, st=st,
                             frames=frames_fn(vv, nn)))
    return dict(name=name, surfaces=surfaces)


# ------------------------------------------------------------------ first-person model
def rot_y(p, d):       # positive tips +X down towards -Z
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rot_z(p, d):       # positive turns +X towards +Y (left)
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def rot_x(p, d):       # positive rolls +Y towards +Z
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


VIEW_SCALE = float(os.environ.get("GG_SCALE", "0.62"))
VIEW_POS = tuple(float(v) for v in os.environ.get("GG_POS", "17,-13,-8").split(","))   # rear end of the gun, eye space
VIEW_YAW = float(os.environ.get("GG_YAW", "35"))
VIEW_PITCH = float(os.environ.get("GG_PITCH", "-4"))      # negative = nose up
VIEW_ROLL = float(os.environ.get("GG_ROLL", "10"))         # negative = top turns towards the middle of the screen

# per frame: (pull back, pitch kick up)
KICK = [(0, 0), (-2.4, -5.5), (-1.7, -3.8), (-1.0, -2.2), (-0.5, -1.1), (-0.2, -0.4), (0, 0)]


def view_frames(vv, nn):
    out = []
    for back, kick in KICK:
        def tf(p, is_n=False):
            q = p if is_n else mul(p, VIEW_SCALE)
            q = rot_x(q, VIEW_ROLL)
            q = rot_y(q, VIEW_PITCH + kick)
            q = rot_z(q, VIEW_YAW)
            if is_n:
                return q
            return (q[0] + VIEW_POS[0] + back, q[1] + VIEW_POS[1], q[2] + VIEW_POS[2])
        out.append(([tf(p) for p in vv], [tf(n, True) for n in nn]))
    return out


# ------------------------------------------------------------------ third-person model: ride p_shot.md3
def pshot_frames():
    z = zipfile.ZipFile(Q15_PK3)
    tmp = os.path.join(OUT, "_p_shot_tmp.md3")
    open(tmp, "wb").write(z.read("progs/p_shot.md3"))
    m = md3lib.read(tmp)
    os.remove(tmp)
    return [s for s in m["surfaces"][0]["frames"]]


def pca_axis(pts):
    c = mul(tuple(sum(p[k] for p in pts) for k in range(3)), 1.0 / len(pts))
    cov = [[sum((p[i] - c[i]) * (p[j] - c[j]) for p in pts) for j in range(3)] for i in range(3)]
    v = (1.0, 0.3, 0.2)
    for _ in range(60):
        v = norm(tuple(sum(cov[i][j] * v[j] for j in range(3)) for i in range(3)))
    return c, v


def basis3(a, b, c):
    e1 = norm(sub(b, a))
    e2 = norm(sub(sub(c, a), mul(e1, dot(sub(c, a), e1))))
    return (e1, e2, cross(e1, e2))


P_LEN = float(os.environ.get("GG_P_LEN", "1.0"))      # goo gun length / p_shot length
P_BACK = float(os.environ.get("GG_P_BACK", "2.5"))    # units it sits back from the shotgun's place


def third_person(mesh):
    frames = pshot_frames()
    v0 = frames[0][0]
    ctr, ax = pca_axis(v0)
    proj = [dot(sub(p, ctr), ax) for p in v0]
    # the grip: the point farthest from the barrel axis
    def off(p):
        d = sub(p, ctr)
        return sub(d, mul(ax, dot(d, ax)))
    gi = max(range(len(v0)), key=lambda i: dot(off(v0[i]), off(v0[i])))
    down = norm(off(v0[gi]))
    lo, hi = min(proj), max(proj)
    # the grip sits near the rear: make ax point to the muzzle
    if abs(proj[gi] - lo) < abs(proj[gi] - hi):
        fwd = ax
    else:
        fwd = mul(ax, -1)
        proj = [-x for x in proj]
        lo, hi = -hi, -lo
    length = hi - lo
    up = mul(down, -1)
    left = cross(up, fwd)
    # place: the goo gun's grip top (gun x 10.6) on the shotgun's grip, its axis on the barrel axis
    k = length * P_LEN / 47.0
    grip_along = dot(sub(v0[gi], ctr), fwd)
    # shotgun grip top is on the axis line, a little behind where the grip bottom is (it leans back)
    origin = add(ctr, mul(fwd, grip_along + 0.25 * math.sqrt(dot(off(v0[gi]), off(v0[gi]))) - 10.6 * k))
    origin = add(origin, mul(fwd, -P_BACK))     # pulled in towards the chest
    place = (origin, mul(fwd, k), mul(left, k), mul(up, k))
    print("p_shot: length %.1f, gun scale %.3f" % (length, k))

    # three far-apart reference vertices to recover each frame's rigid motion
    ia = min(range(len(v0)), key=lambda i: proj[i])
    ib = max(range(len(v0)), key=lambda i: proj[i])
    ic = gi
    B0 = basis3(v0[ia], v0[ib], v0[ic])
    worst = 0.0

    def ff(vv, nn):
        nonlocal worst
        out = []
        base = [frame_apply(place, p) for p in vv]
        basen = [norm(frame_rot(place, n)) for n in nn]
        for fv, _ in frames:
            Bf = basis3(fv[ia], fv[ib], fv[ic])

            def R(p):
                # p in frame-0 world -> coords in B0 -> world via Bf
                c = (dot(p, B0[0]), dot(p, B0[1]), dot(p, B0[2]))
                return add(add(mul(Bf[0], c[0]), mul(Bf[1], c[1])), mul(Bf[2], c[2]))
            t = sub(fv[ia], R(v0[ia]))
            out.append(([add(R(p), t) for p in base], [R(n) for n in basen]))
        return out

    # check the shotgun really is rigid
    for fi in (0, 40, 120, 200, 258):
        fv = frames[min(fi, len(frames) - 1)][0]
        Bf = basis3(fv[ia], fv[ib], fv[ic])
        for i in range(0, len(v0), 7):
            c = (dot(v0[i], B0[0]), dot(v0[i], B0[1]), dot(v0[i], B0[2]))
            c0 = (dot(v0[ia], B0[0]), dot(v0[ia], B0[1]), dot(v0[ia], B0[2]))
            pr = add(add(mul(Bf[0], c[0] - c0[0]), mul(Bf[1], c[1] - c0[1])), mul(Bf[2], c[2] - c0[2]))
            e = sub(add(fv[ia], pr), fv[i])
            worst = max(worst, math.sqrt(dot(e, e)))
    print("p_shot rigidity: worst vertex error %.3f units" % worst)
    return to_model(mesh, "p_googun", ff)


# ------------------------------------------------------------------ goo blob
GOO_SCALE = 3.0     # the grown blob; the glob in flight keeps its own size (goo.qc GOO_HALF matches the grown size)
GOO_TILE = 2.5      # texture repeats per puff, so the pores stay small on the big blob


def build_goo():
    rnd = random.Random(23)
    puffs = [((0, 0, 0), 9.5)]
    for _ in range(9):
        d = norm((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.7, 0.9)))
        puffs.append((mul(d, rnd.uniform(6.5, 9.5)), rnd.uniform(5.5, 8.0)))
    verts_full, verts_glob, st, tris = [], [], [], []
    segs, rings = 14, 9
    for (c, r) in puffs:
        b = len(verts_full)
        ph0 = rnd.uniform(0, 6.28)
        bumps = [(norm((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))), rnd.uniform(0.08, 0.2)) for _ in range(6)]
        for i in range(rings + 1):
            th = math.pi * i / rings
            for j in range(segs + 1):
                ph = 2 * math.pi * j / segs + ph0
                n = (math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))
                k = 1.0 + sum(a * max(0.0, dot(n, bd)) ** 3 for bd, a in bumps) - 0.05 * math.sin(5 * ph) * math.sin(3 * th)
                verts_full.append(mul(add(c, mul(n, r * k)), GOO_SCALE))
                verts_glob.append(add(mul(c, 0.08), mul(n, r * k * 0.36)))
                st.append((j / segs * r / 8 * GOO_TILE, i / rings * r / 8 * GOO_TILE))
        for i in range(rings):
            for j in range(segs):
                a = b + i * (segs + 1) + j
                bb, cc, dd = a + 1, a + segs + 1, a + segs + 2
                tris.append((a, cc, bb))
                tris.append((bb, cc, dd))
    nf = smooth_normals(verts_full, tris)
    ng = smooth_normals(verts_glob, tris)

    def lerp(t):
        return [add(mul(g, 1 - t), mul(f, t)) for g, f in zip(verts_glob, verts_full)]
    frames = [(verts_full, nf), (verts_glob, ng)]
    for t in (0.5, 0.9, 1.1, 0.97):
        frames.append((lerp(t), nf))
    m = dict(name="goo", surfaces=[dict(name="goo", shader="progs/goo", tris=tris, st=st, frames=frames)])
    xs = [p[0] for p in verts_full]
    print("goo blob: %d tris, x extent %.1f..%.1f" % (len(tris), min(xs), max(xs)))
    return m


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_textures()
    gun = build_gun()
    tri_n = sum(len(v[3]) for v in gun.mats.values())
    print("goo gun: %d tris in %d materials" % (tri_n, len(gun.mats)))
    md3lib.write(os.path.join(OUT, "v_googun.md3"), to_model(gun, "v_googun", view_frames))
    print("wrote v_googun.md3")
    if not os.environ.get("GG_VIEW_ONLY"):
        md3lib.write(os.path.join(OUT, "p_googun.md3"), third_person(gun))
        print("wrote p_googun.md3")
        md3lib.write(os.path.join(OUT, "goo.md3"), build_goo())
        print("wrote goo.md3")
    # a gun-space copy for previews
    if os.environ.get("GG_RAW"):
        md3lib.write(os.environ["GG_RAW"], to_model(gun, "googun_raw", lambda vv, nn: [(vv, nn)]))
