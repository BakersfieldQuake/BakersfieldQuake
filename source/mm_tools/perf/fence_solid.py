"""Can the engine's cheap visibility test be used on a map?
    python -I fence_solid.py <maps folder>
For every see-through ('{') face of the world model it asks whether the leaf just behind or just in front of the face
is solid. If so the face sits on a solid world brush (a fire-escape grating, a window pane), and the world-only
line-of-sight test (r_cullentities_trace_entityocclusion 0) is blocked by it although the player can see through it:
a model or light seen only through such a face would be hidden. A map with 0 in the "on a solid brush" column is safe
for the cheap test and can be added to BM_TraceCullSetup in source/qc_combat_decomp/csqc/bm_hud.qc; any other map must
keep the engine default. Faces on brush entities (func_wall and friends) do not count: the test ignores entities.
Shader-made transparency is not checked here; on 2026-11-18 no world texture of any shipped map had one.
BSP2 and BSP29."""
import glob, os, struct, sys

CONTENTS_SOLID = -2


def analyse(path):
    d = open(path, "rb").read()
    bsp2 = d[:4] == b"BSP2"
    L = [struct.unpack_from("<ii", d, 4 + i * 8) for i in range(15)]
    o, l = L[1]
    planes = [struct.unpack_from("<4f", d, o + 20 * i) for i in range(l // 20)]
    o, l = L[3]
    verts = [struct.unpack_from("<3f", d, o + 12 * i) for i in range(l // 12)]
    o, l = L[2]
    n = struct.unpack_from("<i", d, o)[0]
    names = []
    for i in range(n):
        mo = struct.unpack_from("<i", d, o + 4 + 4 * i)[0]
        names.append(d[o + mo:o + mo + 16].split(b"\0")[0].decode("latin-1") if mo >= 0 else "")
    o, l = L[6]
    texinfo = [struct.unpack_from("<i", d, o + 40 * i + 32)[0] for i in range(l // 40)]
    o, l = L[12]
    if bsp2:
        edges = [struct.unpack_from("<II", d, o + 8 * i) for i in range(l // 8)]
    else:
        edges = [struct.unpack_from("<HH", d, o + 4 * i) for i in range(l // 4)]
    o, l = L[13]
    surfedges = struct.unpack_from("<%di" % (l // 4), d, o)
    o, l = L[5]
    if bsp2:
        nodes = [struct.unpack_from("<iii", d, o + 44 * i) for i in range(l // 44)]
    else:
        nodes = [struct.unpack_from("<ihh", d, o + 24 * i) for i in range(l // 24)]
    o, l = L[10]
    if bsp2:
        leafs = [struct.unpack_from("<i", d, o + 44 * i)[0] for i in range(l // 44)]
    else:
        leafs = [struct.unpack_from("<i", d, o + 28 * i)[0] for i in range(l // 28)]
    fo, fl = L[7]
    fsz = 28 if bsp2 else 20
    mo_, ml = L[14]
    headnode = struct.unpack_from("<i", d, mo_ + 36)[0]
    ff, nf = struct.unpack_from("<ii", d, mo_ + 56)

    def contents(p):
        num = headnode
        while num >= 0:
            pl, c0, c1 = nodes[num]
            nx, ny, nz, dist = planes[pl]
            num = c0 if nx * p[0] + ny * p[1] + nz * p[2] - dist >= 0 else c1
        return leafs[-1 - num]

    tot = solid = 0
    bytex = {}
    for i in range(ff, ff + nf):
        b = fo + fsz * i
        if bsp2:
            pl, side, fe, ne, ti = struct.unpack_from("<iiiii", d, b)
        else:
            pl, side, fe, ne, ti = struct.unpack_from("<HhihH", d, b)
        nm = names[texinfo[ti]]
        if not nm.startswith("{"):
            continue
        cx = cy = cz = 0.0
        for k in range(ne):
            se = surfedges[fe + k]
            v = verts[edges[se][0]] if se >= 0 else verts[edges[-se][1]]
            cx += v[0]; cy += v[1]; cz += v[2]
        cx /= ne; cy /= ne; cz /= ne
        nx, ny, nz, dist = planes[pl]
        s = -1.0 if side else 1.0
        back = contents((cx - s * nx * 1.0, cy - s * ny * 1.0, cz - s * nz * 1.0))
        front = contents((cx + s * nx * 1.0, cy + s * ny * 1.0, cz + s * nz * 1.0))
        tot += 1
        e = bytex.setdefault(nm, [0, 0])
        e[0] += 1
        if back == CONTENTS_SOLID or front == CONTENTS_SOLID:
            solid += 1
            e[1] += 1
    worst = sorted(((v[1], k, v[0]) for k, v in bytex.items() if v[1]), reverse=True)[:5]
    print("%-24s see-through world faces %5d, on a solid brush %5d  %s" % (os.path.basename(path), tot, solid,
          " ".join("%s %d/%d" % (k, a, b_) for a, k, b_ in worst)))


for p in sorted(glob.glob(os.path.join(sys.argv[1], "*.bsp"))):
    try:
        analyse(p)
    except Exception as e:  # noqa
        print(os.path.basename(p), "ERROR", repr(e)[:100])
