"""Takes the front windshield glass out of progs/veh_van.md3 (the van has no windshield: you see straight out).

The MD3's 'glass' surface (last surface) holds the curved windshield, the cab-door / quarter side windows and the wire-mesh
bulkhead screen. The windshield is the part ahead of the bulkhead and inside the side windows: every vertex has x > 40 and
|y| < 37.5 (the side windows sit at |y| ~ 40+, the mesh screen at x = 31.6). Those triangles are dropped, and so are the
vertices nothing uses any more. Safe to run again (nothing left to remove).

  python3.13 -I van_windshield.py [path\\to\\veh_van.md3]      (default: BakersfieldQuake\\progs\\veh_van.md3)
build_vehicles_assets.py calls strip_windshield() right after it writes the van, so a rebuild does not bring the glass back.
"""
import struct
import sys

DEFAULT = "G:\\Quake\\Combat\\BakersfieldQuake\\progs\\veh_van.md3"


def is_windshield(verts, tri):
    return all(verts[i][0] > 40.0 and abs(verts[i][1]) < 37.5 for i in tri)


def strip_windshield(path=DEFAULT):
    d = bytearray(open(path, "rb").read())
    flags, nf, nt, ns, nsk, ofs_f, ofs_t, ofs_s, ofs_e = struct.unpack("<9i", d[72:108])
    s = ofs_s
    last = None
    for _ in range(ns):
        last = s
        s += struct.unpack("<i", d[s + 104:s + 108])[0]
    name = bytes(d[last + 4:last + 68]).split(b"\0")[0]
    if name != b"glass":
        raise SystemExit("last surface is %r, expected glass" % name)
    (sflags, snf, nshader, nverts, ntris, ofs_tri, ofs_shader, ofs_st, ofs_xyz, ofs_send) = struct.unpack("<10i", d[last + 68:last + 108])
    tris = [struct.unpack("<3i", d[last + ofs_tri + t * 12:last + ofs_tri + t * 12 + 12]) for t in range(ntris)]
    v0 = [tuple(c / 64.0 for c in struct.unpack("<3h", d[last + ofs_xyz + v * 8:last + ofs_xyz + v * 8 + 6])) for v in range(nverts)]
    keep = [t for t in tris if not is_windshield(v0, t)]
    if len(keep) == len(tris):
        print("no windshield triangles left in", path)
        return 0
    used = sorted({i for t in keep for i in t})
    remap = {old: new for new, old in enumerate(used)}
    shaders = bytes(d[last + ofs_shader:last + ofs_shader + nshader * 68])
    st = [bytes(d[last + ofs_st + v * 8:last + ofs_st + v * 8 + 8]) for v in range(nverts)]
    xyz = [[bytes(d[last + ofs_xyz + f * nverts * 8 + v * 8:last + ofs_xyz + f * nverts * 8 + v * 8 + 8]) for v in range(nverts)] for f in range(snf)]

    tri_b = b"".join(struct.pack("<3i", *(remap[i] for i in t)) for t in keep)
    st_b = b"".join(st[i] for i in used)
    xyz_b = b"".join(b"".join(fr[i] for i in used) for fr in xyz)
    hdr_len = 108
    o_tri = hdr_len
    o_shader = o_tri + len(tri_b)
    o_st = o_shader + len(shaders)
    o_xyz = o_st + len(st_b)
    o_end = o_xyz + len(xyz_b)
    hdr = bytearray(d[last:last + hdr_len])
    struct.pack_into("<10i", hdr, 68, sflags, snf, nshader, len(used), len(keep), o_tri, o_shader, o_st, o_xyz, o_end)
    out = bytes(d[:last]) + bytes(hdr) + tri_b + shaders + st_b + xyz_b
    out = bytearray(out)
    struct.pack_into("<i", out, 72 + 32, len(out))		# ofs_eof
    open(path, "wb").write(out)
    print("%s: glass surface %d -> %d triangles (windshield removed), %d -> %d vertices" % (path, ntris, len(keep), nverts, len(used)))
    return ntris - len(keep)


if __name__ == "__main__":
    strip_windshield(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
