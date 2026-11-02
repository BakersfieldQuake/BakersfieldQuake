"""Converts the author's vertex-animated MD3 models to classic Quake MDL (IDPO v6) so engines that can't load MD3 can use them.

python -I md3_to_mdl.py [--scratch DIR]

  BakersfieldQuake/progs/megaman.md3   -> QBJ3/qbj3/progs/megaman.mdl     (16 frames, world model)
  BakersfieldQuake/progs/v_megaman.md3 -> QBJ3/qbj3/progs/v_megaman.mdl   (26 frames, view model)

Stdlib + Pillow (Pillow is only used to read/resize the PNG skins).  Conventions (all verified at run time, see checks):
  * MD3 UV: u right, v DOWN from the top row of the image (the author's pov_tuner uses flipY=false with the raw UVs).
    MDL st:  s = u*W - 0.5, t = v*H - 0.5  (t=0 is the top row), i.e. NO v flip.
  * MD3 triangles are counter-clockwise seen from outside, Quake wants clockwise -> indices reversed (checked vs normals).
  * Same axes (x fwd, y left, z up): no swizzle.
  * MD3 normal: hi byte = acos(z)*255/2pi, lo byte = atan2(y,x)*255/2pi (build_viewmodel.py enc_normal), inverted exactly.
"""
import math, os, re, struct, sys

from PIL import Image

SRC = r"G:\Quake\Combat\BakersfieldQuake\progs"
DST = r"G:\Quake\QBJ3\qbj3\progs"
PAK = r"G:\Quake\QBJ3\id1\pak0.pak"
ANORMS = r"D:\vibe\quake1opensource\idsrc\WinQuake\anorms.h"
MAXSKIN = 512
MODELS = [("megaman.md3", "megaman.mdl"), ("v_megaman.md3", "v_megaman.mdl")]

scratch = None
if "--scratch" in sys.argv:
    scratch = sys.argv[sys.argv.index("--scratch") + 1]
    os.makedirs(scratch, exist_ok=True)

# ------------------------------------------------------------------ palette + anorms
def read_pak_file(pak, name):
    d = open(pak, "rb").read()
    ident, ofs, ln = struct.unpack_from("<4sii", d, 0)
    assert ident == b"PACK"
    for i in range(ln // 64):
        n, o, s = struct.unpack_from("<56sii", d, ofs + 64 * i)
        if n.split(b"\0")[0].decode("ascii").lower() == name:
            return d[o:o + s]
    raise KeyError(name)

pal_raw = read_pak_file(PAK, "gfx/palette.lmp")
assert len(pal_raw) == 768
PALETTE = [tuple(pal_raw[3 * i:3 * i + 3]) for i in range(256)]
USABLE = PALETTE[:224]          # 224..255 are fullbright

txt = re.sub(r"//.*", "", open(ANORMS).read())
ANORM = [tuple(map(float, m)) for m in re.findall(r"\{\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\}", txt)]
assert len(ANORM) == 162, len(ANORM)

def nearest_anorm(n):
    best, bi = -9, 0
    for i, a in enumerate(ANORM):
        d = a[0] * n[0] + a[1] * n[1] + a[2] * n[2]
        if d > best:
            best, bi = d, i
    return bi

def decode_normal(v):
    zen = ((v >> 8) & 255) * 2 * math.pi / 255      # acos(z)
    az = (v & 255) * 2 * math.pi / 255              # atan2(y, x)
    return (math.sin(zen) * math.cos(az), math.sin(zen) * math.sin(az), math.cos(zen))

_pcache = {}
def nearest_pal(c):
    r = _pcache.get(c)
    if r is None:
        best = 1 << 30
        for i, p in enumerate(USABLE):
            d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
            if d < best:
                best, r = d, i
        _pcache[c] = r
    return r

# ------------------------------------------------------------------ MD3 reader
def read_md3(path):
    d = open(path, "rb").read()
    ident, ver = struct.unpack_from("<4si", d, 0)
    assert ident == b"IDP3" and ver == 15
    name = d[8:72].split(b"\0")[0].decode()
    flags, nframes, ntags, nsurf, nskins, ofs_frames, ofs_tags, ofs_surf, ofs_end = struct.unpack_from("<9i", d, 72)
    assert ntags == 0 and ofs_end == len(d)
    surfs = []
    o = ofs_surf
    for _ in range(nsurf):
        sid, sname, sflags, snf, nsh, nv, nt, ot, osh, ost, oxyz, oend = struct.unpack_from("<4s64s10i", d, o)
        assert sid == b"IDP3" and snf == nframes and nsh == 1
        sname = sname.split(b"\0")[0].decode()
        shader = struct.unpack_from("<64si", d, o + osh)[0].split(b"\0")[0].decode()
        tris = [struct.unpack_from("<3i", d, o + ot + 12 * i) for i in range(nt)]
        sts = [struct.unpack_from("<2f", d, o + ost + 8 * i) for i in range(nv)]
        frames = []
        for f in range(nframes):
            pos, nor = [], []
            for i in range(nv):
                x, y, z, n = struct.unpack_from("<3hH", d, o + oxyz + (f * nv + i) * 8)
                pos.append((x / 64.0, y / 64.0, z / 64.0))
                nor.append(decode_normal(n))
            frames.append((pos, nor))
        for t in tris:
            assert all(0 <= i < nv for i in t)
        surfs.append(dict(name=sname, shader=shader, tris=tris, st=sts, frames=frames))
        o += oend
    assert o == ofs_end
    return name, nframes, surfs

# ------------------------------------------------------------------ atlas
def build_atlas(shaders, srcdir):
    """Stack the textures vertically.  Returns (RGB image, {shader: (x0, y0, w, h)}, transparent?)."""
    imgs, transparent = {}, False
    for sh in shaders:
        im = Image.open(os.path.join(srcdir, os.path.basename(sh) + ".png"))
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
            if min(im.getchannel("A").getdata()) < 128:
                transparent = True
        imgs[sh] = im
    small = [s for s in shaders if imgs[s].size[1] <= 64 and imgs[s].size[0] <= MAXSKIN]
    big = [s for s in shaders if s not in small]
    budget = MAXSKIN - sum(imgs[s].size[1] for s in small)
    placed, y = {}, 0
    rgb = {}
    for sh in shaders:
        im = imgs[sh]
        w, h = im.size
        if sh in big:
            w2 = min(w, MAXSKIN)
            h2 = min(h, max(1, budget // len(big)))
            if (w2, h2) != (w, h):
                im = im.convert("RGBA" if transparent else "RGB").resize((w2, h2), Image.BOX)   # area average
            w, h = w2, h2
        rgb[sh] = im.convert("RGBA" if transparent else "RGB")
        placed[sh] = (0, y, w, h)
        y += h
    W = max(p[2] for p in placed.values())
    H = y
    atlas = Image.new("RGBA" if transparent else "RGB", (W, H))
    for sh, (x0, y0, w, h) in placed.items():
        atlas.paste(rgb[sh], (x0, y0))
        if w < W:       # fill the unused right part with the last column (keeps clamping sane)
            col = rgb[sh].crop((w - 1, 0, w, h)).resize((W - w, h), Image.NEAREST)
            atlas.paste(col, (w, y0))
    return atlas, placed, transparent

def quantize(atlas, transparent):
    W, H = atlas.size
    px = list(atlas.getdata())
    out = bytearray(W * H)
    for i, c in enumerate(px):
        if transparent and len(c) == 4 and c[3] < 128:
            out[i] = 255
        else:
            out[i] = nearest_pal(tuple(c[:3]))
    return bytes(out)

# ------------------------------------------------------------------ conversion
def convert(md3name, mdlname):
    print("=" * 70)
    name, nframes, surfs = read_md3(os.path.join(SRC, md3name))
    print(md3name, "->", mdlname, "|", nframes, "frames,", len(surfs), "surfaces:",
          ", ".join("%s(%dv/%dt,%s)" % (s["name"], len(s["st"]), len(s["tris"]), s["shader"]) for s in surfs))

    shaders = []
    for s in surfs:
        if s["shader"] not in shaders:
            shaders.append(s["shader"])
    atlas, placed, transparent = build_atlas(shaders, SRC)
    SW, SH = atlas.size
    print("atlas %dx%d, layout %s, transparency used: %s" % (SW, SH, placed, transparent))
    skin = quantize(atlas, transparent)
    used = sorted(set(skin))
    print("skin palette indices used: %d distinct, max index %d, any>=224: %s" % (len(used), max(used), any(i >= 224 and i != 255 for i in used)))
    if scratch:
        pim = Image.new("RGB", (SW, SH))
        pim.putdata([PALETTE[i] for i in skin])
        pim.save(os.path.join(scratch, mdlname + "_skin.png"))
        atlas.convert("RGB").save(os.path.join(scratch, mdlname + "_atlas_rgb.png"))

    # --- merge surfaces: per-vertex ST in atlas pixels, positions per frame
    # (pos[f], nrm[f]) lists over merged verts; triangles with offset indices
    mpos = [[] for _ in range(nframes)]
    mnor = [[] for _ in range(nframes)]
    mst = []          # (s, t) ints
    muv = []          # (u_atlas_px, v_atlas_px) floats pre-rounding, for the sampling check
    muvsrc = []       # (shader, u, v) original MD3
    tris = []
    for s in surfs:
        x0, y0, w, h = placed[s["shader"]]
        base = len(mst)
        for (u, v) in s["st"]:
            fx = x0 + u * w            # atlas pixel position (continuous, pixel edges)
            fy = y0 + v * h            # v is measured from the TOP row -> no flip
            muv.append((fx, fy))
            muvsrc.append((s["shader"], u, v))
            si = max(0, min(SW - 1, int(round(fx - 0.5))))
            ti = max(0, min(SH - 1, int(round(fy - 0.5))))
            mst.append((si, ti))
        for f in range(nframes):
            mpos[f].extend(s["frames"][f][0])
            mnor[f].extend(s["frames"][f][1])
        tris.extend((base + a, base + b, base + c) for a, b, c in s["tris"])
    nv0, nt = len(mst), len(tris)

    # --- winding check against the MD3 normals (CCW seen from outside <=> cross(b-a,c-a) . n > 0)
    def wind_stats(tlist, fi):
        pos, nor = mpos[fi], mnor[fi]
        agree = disagree = 0
        for a, b, c in tlist:
            pa, pb, pc = pos[a], pos[b], pos[c]
            e1 = (pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]); e2 = (pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2])
            g = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            n = tuple(nor[a][k] + nor[b][k] + nor[c][k] for k in range(3))
            d = g[0] * n[0] + g[1] * n[1] + g[2] * n[2]
            if d > 1e-9: agree += 1
            elif d < -1e-9: disagree += 1
        return agree, disagree
    for fi in (0, nframes - 1):
        ag, dis = wind_stats(tris, fi)
        print("MD3 winding vs normals, frame %d: CCW-outward %d, CW-outward %d (rest degenerate)" % (fi, ag, dis))
    ag, dis = wind_stats(tris, 0)
    reverse = ag >= dis
    print("MD3 is %s -> %s" % ("CCW (as Q3)" if reverse else "CW", "reversing winding for Quake" if reverse else "keeping winding"))
    if reverse:
        tris = [(a, c, b) for a, b, c in tris]
    ag2, dis2 = wind_stats(tris, 0)
    print("converted (Quake, want CW-outward): CW-outward %d, CCW-outward %d" % (dis2, ag2))
    assert dis2 > ag2

    # --- model-wide quantisation over ALL frames
    mn = [1e18] * 3; mx = [-1e18] * 3
    for f in range(nframes):
        for p in mpos[f]:
            for k in range(3):
                mn[k] = min(mn[k], p[k]); mx[k] = max(mx[k], p[k])
    scale = [max((mx[k] - mn[k]) / 255.0, 1e-6) for k in range(3)]
    origin = list(mn)
    print("scale", ["%.5f" % s for s in scale], "origin", ["%.3f" % o for o in origin])

    def qv(p):
        return tuple(max(0, min(255, int(round((p[k] - origin[k]) / scale[k])))) for k in range(3))
    qpos = [[qv(p) for p in mpos[f]] for f in range(nframes)]
    qnrm = [[nearest_anorm(n) for n in mnor[f]] for f in range(nframes)]
    ang = []
    for f in (0, nframes // 2, nframes - 1):
        for n, i in list(zip(mnor[f], qnrm[f]))[::7]:
            a = ANORM[i]
            ang.append(math.degrees(math.acos(max(-1, min(1, n[0] * a[0] + n[1] * a[1] + n[2] * a[2])))))
    print("normal snap error (deg): mean %.2f max %.2f" % (sum(ang) / len(ang), max(ang)))

    # --- weld identical vertices (same st and same packed data in every frame): exact, shrinks vert count
    keymap, remap, keep = {}, [0] * nv0, []
    for i in range(nv0):
        key = (mst[i], tuple((qpos[f][i], qnrm[f][i]) for f in range(nframes)))
        j = keymap.get(key)
        if j is None:
            j = len(keep); keymap[key] = j; keep.append(i)
        remap[i] = j
    tris = [(remap[a], remap[b], remap[c]) for a, b, c in tris]
    nv = len(keep)
    print("verts: %d merged -> %d after exact weld; tris %d" % (nv0, nv, nt))

    radius = 0.0
    for f in range(nframes):
        for i in keep:
            p = qpos[f][i]
            r = math.sqrt(sum((p[k] * scale[k] + origin[k]) ** 2 for k in range(3)))
            radius = max(radius, r)

    # --- write
    out = bytearray()
    out += struct.pack("<4si", b"IDPO", 6)
    out += struct.pack("<3f3ff3f", *scale, *origin, radius, 0.0, 0.0, 0.0)
    out += struct.pack("<iiiiiiiif", 1, SW, SH, nv, nt, nframes, 0, 0, 0.0)
    out += struct.pack("<i", 0) + skin
    for i in keep:
        out += struct.pack("<3i", 0, *mst[i])
    for a, b, c in tris:
        out += struct.pack("<4i", 1, a, b, c)
    for f in range(nframes):
        pk = [qpos[f][i] + (qnrm[f][i],) for i in keep]
        bmin = [min(p[k] for p in pk) for k in range(3)]
        bmax = [max(p[k] for p in pk) for k in range(3)]
        out += struct.pack("<i", 0) + bytes(bmin) + b"\0" + bytes(bmax) + b"\0"
        out += ("frame%d" % f).encode().ljust(16, b"\0")
        for p in pk:
            out += bytes(p)
    path = os.path.join(DST, mdlname)
    open(path, "wb").write(out)
    print("wrote", path, len(out), "bytes")

    # --- sampling check: MD3 uv convention on the source image vs MDL st on the palettised skin
    check_sampling(muvsrc, mst, keep, remap, skin, SW, SH, placed, surfs)
    return path

def check_sampling(muvsrc, mst, keep, remap, skin, SW, SH, placed, surfs):
    # MD3 convention: sample the ORIGINAL (full-res) png at (u*w, v*h), v from top.  MDL: skin[t*SW+s] via palette.
    cache = {}
    def src(shader):
        if shader not in cache:
            cache[shader] = Image.open(os.path.join(SRC, os.path.basename(shader) + ".png")).convert("RGB")
        return cache[shader]
    tot = totf = 0.0
    n = 0
    step = max(1, len(muvsrc) // 400)
    for i in range(0, len(muvsrc), step):
        sh, u, v = muvsrc[i]
        im = src(sh)
        w, h = im.size
        ref = im.getpixel((min(w - 1, int(u * w)), min(h - 1, int(v * h))))
        reff = im.getpixel((min(w - 1, int(u * w)), min(h - 1, int((1 - v) * h))))   # control: v flipped
        s, t = mst[i]
        col = PALETTE[skin[t * SW + s]]
        tot += sum(abs(a - b) for a, b in zip(ref, col)) / 3.0
        totf += sum(abs(a - b) for a, b in zip(reff, col)) / 3.0
        n += 1
    print("sampling check (%d verts): mean |RGB| error MD3-uv vs MDL-st %.2f ; control with v flipped %.2f" % (n, tot / n, totf / n))

# ------------------------------------------------------------------ MDL reader / validator
def read_mdl(path):
    d = open(path, "rb").read()
    ident, ver = struct.unpack_from("<4si", d, 0)
    assert ident == b"IDPO" and ver == 6
    scale = struct.unpack_from("<3f", d, 8); origin = struct.unpack_from("<3f", d, 20)
    radius = struct.unpack_from("<f", d, 32)[0]
    eye = struct.unpack_from("<3f", d, 36)
    nskins, sw, sh, nv, nt, nf, sync, flags = struct.unpack_from("<8i", d, 48)
    size = struct.unpack_from("<f", d, 80)[0]
    o = 84
    assert nskins == 1
    g = struct.unpack_from("<i", d, o)[0]; assert g == 0
    o += 4 + sw * sh
    st = [struct.unpack_from("<3i", d, o + 12 * i) for i in range(nv)]; o += 12 * nv
    tr = [struct.unpack_from("<4i", d, o + 16 * i) for i in range(nt)]; o += 16 * nt
    assert all(0 <= s < sw and 0 <= t < sh and q == 0 for q, s, t in st)
    assert all(t[0] == 1 and all(0 <= i < nv for i in t[1:]) for t in tr)
    gmin = [255] * 3; gmax = [0] * 3
    fr = []
    for f in range(nf):
        typ = struct.unpack_from("<i", d, o)[0]; assert typ == 0
        bmin = d[o + 4:o + 7]; bmax = d[o + 8:o + 11]
        nm = d[o + 12:o + 28].split(b"\0")[0].decode()
        o += 28
        vs = [struct.unpack_from("<4B", d, o + 4 * i) for i in range(nv)]; o += 4 * nv
        assert all(v[3] < 162 for v in vs)
        for k in range(3):
            assert min(v[k] for v in vs) == bmin[k] and max(v[k] for v in vs) == bmax[k]
            gmin[k] = min(gmin[k], bmin[k]); gmax[k] = max(gmax[k], bmax[k])
        fr.append(nm)
    assert o == len(d), (o, len(d))
    wmin = [gmin[k] * scale[k] + origin[k] for k in range(3)]; wmax = [gmax[k] * scale[k] + origin[k] for k in range(3)]
    print("  MDL check OK: %s | %d bytes | verts %d tris %d frames %d (%s..%s) | skin %dx%d | synctype %d flags %d size %g"
          % (os.path.basename(path), len(d), nv, nt, nf, fr[0], fr[-1], sw, sh, sync, flags, size))
    print("  radius %.2f eye %s | bbox(all frames) min %s max %s" % (radius, eye, [round(x, 2) for x in wmin], [round(x, 2) for x in wmax]))
    return nv, nt, nf, sw, sh

if __name__ == "__main__":
    for a, b in MODELS:
        p = convert(a, b)
        print("re-reading:")
        read_mdl(p)
