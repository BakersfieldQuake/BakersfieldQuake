"""Tiny MD3 reader / writer shared by the fun-gun build scripts (pure Python).

read(path)  -> dict(name, frames=[(mins, maxs, radius, name)], surfaces=[dict(name, shader, tris, st, frames=[(verts, norms)])])
write(path, model)  writes the same structure back out (frame bounds are recomputed).
"""
import math
import struct


def _name(b):
    return b.split(b"\0", 1)[0].decode("ascii", "replace")


def dec_normal(n):
    lng = (n >> 8) * 2 * math.pi / 255
    lat = (n & 255) * 2 * math.pi / 255
    return (math.sin(lng) * math.cos(lat), math.sin(lng) * math.sin(lat), math.cos(lng))


def enc_normal(n):
    x, y, z = n
    l = math.sqrt(x * x + y * y + z * z) or 1.0
    x, y, z = x / l, y / l, z / l
    lng = int(round(math.acos(max(-1.0, min(1.0, z))) * 255 / (2 * math.pi))) & 255
    lat = int(round(math.atan2(y, x) * 255 / (2 * math.pi))) & 255
    return (lng << 8) | lat


def read(path):
    d = open(path, "rb").read()
    ident, ver, name, flags, nf, ntags, ns, nsk, ofs_f, ofs_t, ofs_s, ofs_e = struct.unpack("<4si64s9i", d[:108])
    assert ident == b"IDP3" and ver == 15, path
    frames = []
    for i in range(nf):
        o = ofs_f + 56 * i
        v = struct.unpack("<10f16s", d[o:o + 56])
        frames.append((v[0:3], v[3:6], v[9], _name(v[10])))
    surfaces = []
    o = ofs_s
    for _ in range(ns):
        h = struct.unpack("<4s64s10i", d[o:o + 108])
        sname, sflags, snf, nsh, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end = _name(h[1]), *h[2:]
        tris = [struct.unpack("<3i", d[o + o_tri + 12 * i:o + o_tri + 12 * i + 12]) for i in range(nt)]
        shader = _name(d[o + o_sh:o + o_sh + 64])
        st = [struct.unpack("<2f", d[o + o_st + 8 * i:o + o_st + 8 * i + 8]) for i in range(nv)]
        fr = []
        for f in range(snf):
            base = o + o_xyz + f * nv * 8
            vv, nn = [], []
            for i in range(nv):
                x, y, z, n = struct.unpack("<3hH", d[base + 8 * i:base + 8 * i + 8])
                vv.append((x / 64.0, y / 64.0, z / 64.0))
                nn.append(dec_normal(n))
            fr.append((vv, nn))
        surfaces.append(dict(name=sname, shader=shader, tris=tris, st=st, frames=fr))
        o += o_end
    return dict(name=_name(name), surfaces=surfaces, nframes=nf)


def _n64(s):
    return s.encode("ascii")[:63].ljust(64, b"\0")


def _i16(v):
    return max(-32768, min(32767, int(round(v * 64))))


def write(path, model):
    nf = len(model["surfaces"][0]["frames"])
    fmin = [[1e9] * 3 for _ in range(nf)]
    fmax = [[-1e9] * 3 for _ in range(nf)]
    blobs = []
    for s in model["surfaces"]:
        nv, nt = len(s["st"]), len(s["tris"])
        tri_b = b"".join(struct.pack("<3i", *t) for t in s["tris"])
        sh_b = _n64(s["shader"]) + struct.pack("<i", 0)
        st_b = b"".join(struct.pack("<2f", *t) for t in s["st"])
        xyz = []
        for fi, (vv, nn) in enumerate(s["frames"]):
            assert len(vv) == nv
            for p, n in zip(vv, nn):
                for k in range(3):
                    fmin[fi][k] = min(fmin[fi][k], p[k])
                    fmax[fi][k] = max(fmax[fi][k], p[k])
                xyz.append(struct.pack("<3hH", _i16(p[0]), _i16(p[1]), _i16(p[2]), enc_normal(n)))
        xyz_b = b"".join(xyz)
        o_tri = 108
        o_sh = o_tri + len(tri_b)
        o_st = o_sh + len(sh_b)
        o_xyz = o_st + len(st_b)
        o_end = o_xyz + len(xyz_b)
        blobs.append(b"IDP3" + _n64(s["name"]) + struct.pack("<10i", 0, nf, 1, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end)
                     + tri_b + sh_b + st_b + xyz_b)
    fnames = model.get("frame_names")
    fr_b = b""
    for fi in range(nf):
        mn, mx = fmin[fi], fmax[fi]
        rad = max(math.sqrt(a * a + b * b + c * c) for a in (mn[0], mx[0]) for b in (mn[1], mx[1]) for c in (mn[2], mx[2]))
        fn = fnames[fi] if (fnames and fi < len(fnames)) else ("f%d" % fi)
        fr_b += struct.pack("<10f", *mn, *mx, 0.0, 0.0, 0.0, rad) + (fn.encode("ascii")[:15].ljust(16, b"\0"))
    hdr = b"IDP3" + struct.pack("<i", 15) + _n64(model["name"]) + struct.pack(
        "<9i", 0, nf, 0, len(blobs), 0, 108, 108 + len(fr_b), 108 + len(fr_b), 108 + len(fr_b) + sum(len(b) for b in blobs))
    open(path, "wb").write(hdr + fr_b + b"".join(blobs))
