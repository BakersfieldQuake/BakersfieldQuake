"""The sniper rifle assets (it replaces the nailgun, see sniper.qc), written straight into BakersfieldQuake:
  progs/v_srifle.mdl    first-person model, Team Fortress 2.8's own (0 idle, 1-6 the fire kick: player_shot1..6)
  progs/sight.spr       TF's red laser dot
  sound/weapons/sniper.wav  TF's rifle shot
  progs/g_srifle.mdl    the pickup: v_srifle's frame 0 without the hand, centred and spinning like g_nail.mdl
  progs/p_srifle.md3    third-person model in the player's hands: the same handless rifle riding p_shot.md3's 259 frames
                        (the shotgun is rigid, so every frame is the shotgun's frame-0 -> frame-N motion applied to the rifle)
  progs/p_srifle.png    its texture (v_srifle's skin through the Quake palette)
Team Fortress art: Valve owns it now, so keep these to the private LAN (see _reference\\REPORT.md).
python -I build_srifle.py"""
import math
import os
import shutil
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md3lib
from build_googun import add, sub, mul, dot, cross, norm, basis3, pca_axis, pshot_frames

from PIL import Image

ROOT = r"G:\Quake\Combat\BakersfieldQuake"
TF = r"G:\Quake\Combat\_reference\TeamFortress\extracted\tf28\FORTRESS\PAK0_pak"
ID1_PAK0 = r"G:\Quake\Combat\id1\pak0.pak"
PROGS = os.path.join(ROOT, "progs")

HAND_S = ((88, 252), (333, 492))    # skin columns that hold the hand (the skin has two hand pictures): those triangles are dropped
PICKUP_SCALE = 0.9
HELD_LENGTH = 1.35      # held rifle length / p_shot's shotgun length


def pak_file(pak, name):
    d = open(pak, "rb").read()
    off, ln = struct.unpack("<ii", d[4:12])
    for i in range(ln // 64):
        e = d[off + i * 64:off + i * 64 + 64]
        if e[:56].split(b"\0")[0].decode() == name:
            fo, fl = struct.unpack("<ii", e[56:64])
            return d[fo:fo + fl]
    raise KeyError(name)


def read_mdl(b):
    scale = struct.unpack("<3f", b[8:20])
    tr = struct.unpack("<3f", b[20:32])
    nsk, sw, sh, nv, nt, nf, sync, flags = struct.unpack("<8i", b[48:80])
    p = 84
    assert nsk == 1 and struct.unpack("<i", b[p:p + 4])[0] == 0
    skin = b[p + 4:p + 4 + sw * sh]
    p += 4 + sw * sh
    st = [struct.unpack("<3i", b[p + i * 12:p + i * 12 + 12]) for i in range(nv)]
    p += 12 * nv
    tris = [struct.unpack("<4i", b[p + i * 16:p + i * 16 + 16]) for i in range(nt)]
    p += 16 * nt
    assert struct.unpack("<i", b[p:p + 4])[0] == 0      # frame 0 is a single frame
    p += 4 + 8 + 16
    verts = [tuple(b[p + i * 4 + k] * scale[k] + tr[k] for k in range(3)) for i in range(nv)]
    nidx = [b[p + i * 4 + 3] for i in range(nv)]
    return dict(sw=sw, sh=sh, skin=skin, st=st, tris=tris, verts=verts, nidx=nidx)


def rifle_only(m):
    """drop the hand: the connected mesh pieces that are mostly textured from the hand's columns of the skin"""
    parent = list(range(len(m["verts"])))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for t in m["tris"]:
        for i in t[2:]:
            parent[find(i)] = find(t[1])
    votes = {}
    for t in m["tris"]:
        s = sum(m["st"][i][1] for i in t[1:]) / 3.0
        v = votes.setdefault(find(t[1]), [0, 0])
        v[any(a <= s <= b for a, b in HAND_S)] += 1
    keep = []
    hand = set()
    for t in m["tris"]:
        rifle, handy = votes[find(t[1])]
        if handy > rifle:
            hand.update(t[1:])
        else:
            keep.append(t)
    used = sorted({i for t in keep for i in t[1:]})
    return keep, used, sorted(hand)


def write_mdl(path, m, tris, used, xf, flags):
    """one-frame MDL of the used vertices, positions through xf (uniform scale + shift, so the normal indices still hold)"""
    remap = {old: new for new, old in enumerate(used)}
    pts = [xf(m["verts"][i]) for i in used]
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    scale = [max(hi[k] - lo[k], 1e-3) / 255.0 for k in range(3)]
    radius = max(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) for p in pts)
    out = bytearray()
    out += struct.pack("<4si3f3ff3f", b"IDPO", 6, *scale, *lo, radius, 0, 0, 0)
    out += struct.pack("<8if", 1, m["sw"], m["sh"], len(used), len(tris), 1, 0, flags, 8.0)
    out += struct.pack("<i", 0) + m["skin"]
    for i in used:
        out += struct.pack("<3i", *m["st"][i])
    for t in tris:
        out += struct.pack("<4i", t[0], remap[t[1]], remap[t[2]], remap[t[3]])
    packed = [tuple(int(round((p[k] - lo[k]) / scale[k])) for k in range(3)) for p in pts]
    out += struct.pack("<i", 0)
    out += bytes((0, 0, 0, 0, 255, 255, 255, 0)) + b"srifle".ljust(16, b"\0")
    for q, i in zip(packed, used):
        out += bytes((q[0], q[1], q[2], m["nidx"][i]))
    open(path, "wb").write(bytes(out))
    print("wrote %s: %d verts, %d tris, box %s..%s" % (path, len(used), len(tris),
                                                        ["%.1f" % v for v in lo], ["%.1f" % v for v in hi]))


def md3_mesh(m, tris, used):
    """MDL -> md3 vertex layout: back-facing triangles on the seam use the skin's back half, so seam vertices split"""
    sw, sh = float(m["sw"]), float(m["sh"])
    vmap = {}
    verts, st, out = [], [], []
    for front, *idx in tris:
        tri = []
        for i in idx:
            onseam, s, t = m["st"][i]
            back = bool(onseam) and not front
            key = (i, back)
            if key not in vmap:
                vmap[key] = len(verts)
                verts.append(m["verts"][i])
                st.append(((s + (sw / 2 if back else 0) + 0.5) / sw, (t + 0.5) / sh))
            tri.append(vmap[key])
        out.append((tri[0], tri[2], tri[1]))     # MDL winding is the other way round from md3's
    return verts, st, out


def smooth_normals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        n = cross(sub(verts[b], verts[a]), sub(verts[c], verts[a]))
        for i in (a, b, c):
            for k in range(3):
                acc[i][k] += n[k]
    # seam copies share a position: give them the same normal
    bypos = {}
    for i, v in enumerate(verts):
        bypos.setdefault(tuple(round(x, 3) for x in v), []).append(i)
    for group in bypos.values():
        s = [sum(acc[i][k] for i in group) for k in range(3)]
        for i in group:
            acc[i] = s
    return [norm(a) for a in acc]


def held_frames(gverts, gnorms, grip_x, length):
    """gun space (x from the stock to the muzzle, y left, z up, barrel axis on z=0) -> p_shot's frames"""
    frames = pshot_frames()
    v0 = frames[0][0]
    ctr, ax = pca_axis(v0)
    proj = [dot(sub(p, ctr), ax) for p in v0]

    def off(p):
        d = sub(p, ctr)
        return sub(d, mul(ax, dot(d, ax)))
    gi = max(range(len(v0)), key=lambda i: dot(off(v0[i]), off(v0[i])))
    down = norm(off(v0[gi]))
    lo, hi = min(proj), max(proj)
    if abs(proj[gi] - lo) < abs(proj[gi] - hi):
        fwd = ax
    else:
        fwd = mul(ax, -1)
        proj = [-x for x in proj]
        lo, hi = -hi, -lo
    up = mul(down, -1)
    left = cross(up, fwd)
    k = (hi - lo) * HELD_LENGTH / length
    grip_along = dot(sub(v0[gi], ctr), fwd)
    origin = add(ctr, mul(fwd, grip_along + 0.25 * math.sqrt(dot(off(v0[gi]), off(v0[gi]))) - grip_x * k))
    print("p_shot: length %.1f, rifle scale %.3f" % (hi - lo, k))

    def place(p):
        return add(origin, add(add(mul(fwd, p[0] * k), mul(left, p[1] * k)), mul(up, p[2] * k)))

    def place_n(n):
        return norm(add(add(mul(fwd, n[0]), mul(left, n[1])), mul(up, n[2])))
    base = [place(p) for p in gverts]
    basen = [place_n(n) for n in gnorms]
    ia = min(range(len(v0)), key=lambda i: proj[i])
    ib = max(range(len(v0)), key=lambda i: proj[i])
    B0 = basis3(v0[ia], v0[ib], v0[gi])
    out = []
    for fv, _ in frames:
        Bf = basis3(fv[ia], fv[ib], fv[gi])

        def R(p):
            c = (dot(p, B0[0]), dot(p, B0[1]), dot(p, B0[2]))
            return add(add(mul(Bf[0], c[0]), mul(Bf[1], c[1])), mul(Bf[2], c[2]))
        t = sub(fv[ia], R(v0[ia]))
        out.append(([add(R(p), t) for p in base], [R(n) for n in basen]))
    return out


def main():
    os.makedirs(PROGS, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "sound", "weapons"), exist_ok=True)
    for rel in ("progs/v_srifle.mdl", "progs/sight.spr", "sound/weapons/sniper.wav"):
        dst = os.path.join(ROOT, rel.replace("/", os.sep))
        shutil.copyfile(os.path.join(TF, rel.replace("/", os.sep)), dst)
        print("copied", dst)

    m = read_mdl(open(os.path.join(TF, "progs", "v_srifle.mdl"), "rb").read())
    tris, used, hand = rifle_only(m)
    print("v_srifle: %d of %d triangles are the rifle" % (len(tris), len(m["tris"])))
    pts = [m["verts"][i] for i in used]
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    muzzle = [p for p in pts if p[0] > hi[0] - 2.0]
    axis_y = sum(p[1] for p in muzzle) / len(muzzle)
    axis_z = sum(p[2] for p in muzzle) / len(muzzle)
    hp = [m["verts"][i] for i in hand]
    top = max(p[2] for p in hp)
    grip_x = sum(p[0] for p in hp if p[2] > top - 3) / max(1, len([p for p in hp if p[2] > top - 3])) - lo[0]
    length = hi[0] - lo[0]
    print("rifle: x %.1f..%.1f (length %.1f), barrel axis y %.1f z %.1f, grip %.1f from the stock" % (lo[0], hi[0], length, axis_y, axis_z, grip_x))

    # the pickup: centred on the spin axis, lying a little above the floor like g_nail.mdl (z 14..35)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2

    def pick(p):
        return ((p[0] - cx) * PICKUP_SCALE, (p[1] - cy) * PICKUP_SCALE, (p[2] - lo[2]) * PICKUP_SCALE + 16)
    write_mdl(os.path.join(PROGS, "g_srifle.mdl"), m, tris, used, pick, 8)     # 8 = EF_ROTATE

    # the held model
    pal = pak_file(ID1_PAK0, "gfx/palette.lmp")
    im = Image.frombytes("P", (m["sw"], m["sh"]), m["skin"])
    im.putpalette(pal)
    im.convert("RGB").save(os.path.join(PROGS, "p_srifle.png"))
    print("wrote", os.path.join(PROGS, "p_srifle.png"))
    verts, st, mtris = md3_mesh(m, tris, used)
    gverts = [(p[0] - lo[0], p[1] - axis_y, p[2] - axis_z) for p in verts]
    gnorms = smooth_normals(gverts, mtris)
    model = dict(name="p_srifle", surfaces=[dict(name="rifle", shader="progs/p_srifle", tris=mtris, st=st,
                                                 frames=held_frames(gverts, gnorms, grip_x, length))])
    md3lib.write(os.path.join(PROGS, "p_srifle.md3"), model)
    print("wrote", os.path.join(PROGS, "p_srifle.md3"))


if __name__ == "__main__":
    main()
