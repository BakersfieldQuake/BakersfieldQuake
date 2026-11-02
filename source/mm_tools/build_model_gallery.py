"""Builds G:\\Quake\\Combat\\BakersfieldQuake\\custom_models.html: a self-contained interactive 3D WebGL2 gallery
of every custom 3D model created for BakersfieldQuake (3D photo/video reconstructions, procedural weapons &
projectiles, procedural effects/hats/debris, archived prototypes, and custom-rigged hybrids).

Works 100% offline over file:// with zero external network dependencies and uses a single shared WebGL2 context
with scissor/viewport culling so all 40+ models render smoothly side by side.

Usage:
    python3.13 source/mm_tools/build_model_gallery.py [out.html]
"""
import base64
import gzip
import io
import json
import math
import os
import re
import struct
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(MOD, ".."))
PROGS = os.path.join(MOD, "progs")
BKP_CHARS = os.path.join(ROOT, "_backups", "player_bodies_removed_2026-10-30", "progs")
ID1_PAK0 = os.path.join(ROOT, "id1", "pak0.pak")
ANORM_JSON = os.path.join(ROOT, "monster_page", "anorm.json")
TEMPLATE = os.path.join(HERE, "model_gallery.template.html")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MOD, "custom_models.html")

sys.path.insert(0, HERE)
import md3lib


# --------------------------------------------------------------------------- PAK & Palette helpers
def load_pak_entry(pak_path, entry_name):
    with open(pak_path, "rb") as f:
        hdr = f.read(12)
        ident, ofs, length = struct.unpack("<4sii", hdr)
        assert ident == b"PACK"
        f.seek(ofs)
        raw = f.read(length)
        for i in range(0, length, 64):
            nm = raw[i:i + 56].split(b"\0", 1)[0].decode("ascii", "replace")
            pos, sz = struct.unpack("<ii", raw[i + 56:i + 64])
            if nm.lower() == entry_name.lower():
                f.seek(pos)
                return f.read(sz)
    raise KeyError(entry_name)


PALETTE = np.frombuffer(load_pak_entry(ID1_PAK0, "gfx/palette.lmp"), np.uint8).reshape(256, 3)
ANORM = json.load(open(ANORM_JSON, encoding="utf-8"))


# --------------------------------------------------------------------------- Binary arena & Texture store
BIN = bytearray()


def add_buf(arr_bytes):
    while len(BIN) & 3:
        BIN.append(0)
    off = len(BIN)
    BIN.extend(arr_bytes)
    return [off, len(arr_bytes)]


TEXTURES = {}       # key -> index in TEX_LIST
TEX_LIST = []       # list of dict(id, uri, w, h, alpha, nearest)


def register_image(key, im, max_dim=768, force_png=False, nearest=False, jpeg_q=86):
    if key in TEXTURES:
        return TEXTURES[key]
    has_alpha = im.mode == "RGBA" and np.array(im.getchannel("A")).min() < 250
    w0, h0 = im.size
    if max_dim and max(w0, h0) > max_dim:
        sc = max_dim / float(max(w0, h0))
        im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))), Image.LANCZOS)
    buf = io.BytesIO()
    if has_alpha or force_png or max(im.size) <= 128:
        im = im.convert("RGBA" if has_alpha else "RGB")
        im.save(buf, "PNG", optimize=True)
        mime = "image/png"
    else:
        im = im.convert("RGB")
        im.save(buf, "JPEG", quality=jpeg_q, optimize=True)
        mime = "image/jpeg"
    uri = f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    idx = len(TEX_LIST)
    TEXTURES[key] = idx
    TEX_LIST.append(dict(
        key=os.path.basename(key),
        uri=uri,
        w=w0,
        h=h0,
        alpha=bool(has_alpha),
        nearest=bool(nearest or max(w0, h0) <= 16),
    ))
    return idx


def load_tex_file(path, max_dim=768, nearest=False, force_png=False):
    im = Image.open(path)
    im.load()
    return register_image(os.path.abspath(path), im, max_dim=max_dim, force_png=force_png, nearest=nearest)


# --------------------------------------------------------------------------- Shader definitions (scripts/*.shader)
def parse_pickle_shaders():
    path = os.path.join(MOD, "scripts", "pickle.shader")
    s = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^(progs/\w+)\s*\{(.*?)^\}", s, re.S | re.M):
        name, body = m.group(1), m.group(2)
        a = re.search(r"animmap\s+([\d.]+)\s+(.*)", body)
        one = re.search(r"^\s*map\s+(\S+)", body, re.M)
        alpha = "alphafunc" in body.lower()
        cull_none = "cull none" in body.lower()
        if a:
            fps = float(a.group(1))
            frames = a.group(2).split()
            out[name] = dict(fps=fps, frames=frames, alphaTest=alpha, doubleSided=cull_none)
        elif one:
            out[name] = dict(fps=0.0, frames=[one.group(1)], alphaTest=alpha, doubleSided=cull_none)
    return out


PICKLE_SHADERS = parse_pickle_shaders()


def resolve_md3_shader(shader_name, model_dir, model_stem):
    """Returns dict(tex=[texIdx,...], fps, alphaTest, additive, scrollV, unlit, twoSidedLight)"""
    if shader_name == "progs/aura":
        t = load_tex_file(os.path.join(PROGS, "aura.png"), max_dim=256)
        return dict(tex=[t], fps=0.0, alphaTest=False, additive=True, scrollV=0.6, unlit=True)

    if shader_name == "progs/v_laptop_scr":
        t = load_tex_file(os.path.join(PROGS, "v_laptop_scr.png"), max_dim=1024, force_png=True)
        return dict(tex=[t], fps=0.0, alphaTest=False, additive=False, scrollV=0.0, unlit=True)

    if shader_name == "progs/v_laptop_zap":
        t = load_tex_file(os.path.join(PROGS, "v_laptop_zap.png"), max_dim=128, force_png=True)
        return dict(tex=[t], fps=0.0, alphaTest=False, additive=True, scrollV=0.0, unlit=True)

    if shader_name in ("progs/v_laptop_keys", "progs/v_laptop_body"):
        fn = os.path.basename(shader_name) + ".png"
        t = load_tex_file(os.path.join(PROGS, fn), max_dim=512, force_png=True)
        return dict(tex=[t], fps=0.0, alphaTest=False, additive=False, scrollV=0.0, unlit=False)

    if shader_name == "progs/jetpack_glow":
        t = load_tex_file(os.path.join(PROGS, "jetpack_glow.png"), max_dim=256)
        return dict(tex=[t], fps=0.0, alphaTest=False, additive=False, scrollV=0.0, unlit=True)

    if shader_name == "progs/jetpack_plume":
        tids = [load_tex_file(os.path.join(PROGS, f"jetpack_plume_{k}.png"), max_dim=256) for k in range(4)]
        return dict(tex=tids, fps=18.0, alphaTest=False, additive=True, scrollV=0.0, unlit=True)

    if shader_name in ("progs/zap_green", "progs/laser_red"):
        fn = os.path.basename(shader_name) + ".png"
        t = load_tex_file(os.path.join(PROGS, fn), max_dim=64)
        return dict(tex=[t], fps=0.0, alphaTest=False, additive=True, scrollV=0.0, unlit=True)

    if shader_name in PICKLE_SHADERS:
        spec = PICKLE_SHADERS[shader_name]
        tids = []
        for f in spec["frames"]:
            # Subsample vpk_ hold video frames (every 2nd frame at 256px) to keep HTML nimble
            m = re.search(r"vpk_(\d+)$", f)
            if m:
                n = int(m.group(1))
                f_use = "progs/vpk_%02d" % (n - (n % 2))
                p = os.path.join(MOD, f_use + ".png")
                tids.append(load_tex_file(p, max_dim=256))
            else:
                p = os.path.join(MOD, f + ".png")
                tids.append(load_tex_file(p, max_dim=384))
        return dict(
            tex=tids,
            fps=spec["fps"],
            alphaTest=spec["alphaTest"],
            additive=False,
            scrollV=0.0,
            unlit=False,
        )

    base = os.path.basename(shader_name)
    # Special case: archived v_banana_girl.md3 has shader 'progs/v_banana' next to 'v_banana_girl.png'
    cands = []
    if model_stem == "v_banana_girl":
        cands.append(os.path.join(model_dir, "v_banana_girl.png"))
    cands += [
        os.path.join(model_dir, base + ".png"),
        os.path.join(PROGS, base + ".png"),
        os.path.join(HERE, "out", "progs", base + ".png"),
        os.path.join(model_dir, model_stem + ".png"),
    ]
    found = next((c for c in cands if os.path.exists(c)), None)
    assert found is not None, f"Missing texture for shader {shader_name} in {model_dir}"
    max_d = 1024 if base == "bigears" else (768 if base in ("megaman", "girl", "v_banana_girl", "johnhead3d", "pickle3d") else 512)
    tid = load_tex_file(found, max_dim=max_d)
    alpha_test = TEX_LIST[tid]["alpha"]
    return dict(tex=[tid], fps=0.0, alphaTest=alpha_test, additive=False, scrollV=0.0, unlit=False)


# --------------------------------------------------------------------------- Geometry deduplication & bounds
def strip_reversed_dups(tris):
    """If a surface contains both (a,b,c) and its exact reversed winding (a,c,b), keep one copy
    since WebGL renders with CULL_FACE disabled; avoids coplanar z-fighting while preserving silhouette."""
    seen = set()
    kept = []
    had_dup = False
    for a, b, c in tris:
        fwd = (a, b, c)
        rev_keys = ((a, c, b), (c, b, a), (b, a, c))
        if any(rk in seen for rk in rev_keys):
            had_dup = True
            continue
        seen.add(fwd)
        kept.append(fwd)
    return kept, had_dup


def build_edges(tris):
    edges = set()
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            edges.add((u, v) if u < v else (v, u))
    arr = np.array(sorted(edges), dtype="<u2")
    return arr


def enc_norm_u16(nn):
    """Vectorized MD3 normal encoding (N, 3) -> uint16 (lng << 8 | lat)."""
    nn = np.asarray(nn, dtype=np.float32)
    l = np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-9)
    n = nn / l
    lng = np.round(np.arccos(np.clip(n[:, 2], -1.0, 1.0)) * 255.0 / (2.0 * math.pi)).astype(np.int32) & 255
    lat = np.round(np.arctan2(n[:, 1], n[:, 0]) * 255.0 / (2.0 * math.pi)).astype(np.int32) & 255
    return ((lng << 8) | lat).astype("<u2")


# --------------------------------------------------------------------------- Experimental 3D Hull Pickle (in-memory)
def build_pickle3d_in_memory():
    """Runs make_pickle3d.py's voxel visual-hull + marching cubes + Taubin smoothing in memory
    without overwriting progs/pickle.md3, pairing with source/mm_tools/out/progs/pickle3d.png."""
    from scipy import sparse

    N = 16
    BAD = {9}
    GOOD = [k for k in range(N) if k not in BAD]
    UNIT = 20.0 / 512.0
    C = 256.0
    STEP = 2.0
    CROP = (148, 16, 364, 496)
    TILE_W, TILE_H = CROP[2] - CROP[0], CROP[3] - CROP[1]
    COLS = 5
    sgn = -1

    # Note: progs/pickle_09.png was fixed by make_pickle_views, and pickle3d.png was baked from GOOD
    masks = []
    for k in range(N):
        im = Image.open(os.path.join(PROGS, "pickle_%02d.png" % k)).convert("RGBA")
        a = np.array(im.getchannel("A")) > 128
        masks.append(ndimage.binary_dilation(a, iterations=2))

    xs = np.arange(-110, 110 + STEP, STEP)
    ys = np.arange(-110, 110 + STEP, STEP)
    zs = np.arange(-250, 250 + STEP, STEP)
    gx, gy, gz = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], 1)
    cnt = np.zeros(len(pts), np.int16)
    for k in GOOD:
        phi = math.radians(sgn * k * 360.0 / N)
        yr = pts[:, 0] * math.sin(phi) + pts[:, 1] * math.cos(phi)
        ui, vi = np.round(C - yr).astype(int), np.round(C - pts[:, 2]).astype(int)
        ok = (ui >= 0) & (ui < 512) & (vi >= 0) & (vi < 512)
        ins = np.zeros(len(pts), bool)
        ins[ok] = masks[k][vi[ok], ui[ok]]
        cnt += ins
    vol = (cnt >= len(GOOD) - 1).reshape(gx.shape)
    vol = ndimage.binary_closing(vol, iterations=1)
    lab, nlab = ndimage.label(vol)
    if nlab > 1:
        sizes = ndimage.sum(vol, lab, range(1, nlab + 1))
        vol = lab == (1 + int(np.argmax(sizes)))
    field = ndimage.gaussian_filter(vol.astype(np.float32), 1.0)
    verts, faces, _, _ = measure.marching_cubes(field, 0.5, spacing=(STEP, STEP, STEP), step_size=3)
    verts = verts + np.array([xs[0], ys[0], zs[0]])

    # Taubin smoothing
    n = len(verts)
    rows = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2], faces[:, 1], faces[:, 2], faces[:, 0]])
    cols = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0], faces[:, 0], faces[:, 1], faces[:, 2]])
    adj = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    adj.data[:] = 1.0
    deg = np.maximum(np.asarray(adj.sum(1)).ravel(), 1.0)[:, None]
    for _ in range(4):
        for f in (0.5, -0.53):
            verts = verts + f * ((adj @ verts) / deg - verts)

    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    fn = np.cross(b - a, c - a)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
    cen = (a + b + c) / 3
    flip = (fn[:, 0] * cen[:, 0] + fn[:, 1] * cen[:, 1]) < 0
    top = np.abs(cen[:, 2]) > 220
    flip &= ~top
    fn[flip] *= -1
    faces = faces.copy()
    faces[flip] = faces[flip][:, ::-1]

    cams = {k: np.array([-math.cos(math.radians(sgn * k * 360.0 / N)),
                         math.sin(math.radians(sgn * k * 360.0 / N)), 0.0]) for k in GOOD}
    score = np.stack([fn @ cams[k] for k in GOOD], 1)
    view = np.array(GOOD)[np.argmax(score, 1)]
    tile_idx = {k: i for i, k in enumerate(GOOD)}
    AW = COLS * TILE_W
    AH = ((len(GOOD) + COLS - 1) // COLS) * TILE_H

    vn = np.zeros_like(verts)
    for f, nrm in zip(faces, fn):
        for vi in f:
            vn[vi] += nrm
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)

    out_v, out_n, out_st, out_t, key = [], [], [], [], {}
    for f, k in zip(faces, view):
        tri = []
        ti = tile_idx[int(k)]
        phi = math.radians(sgn * int(k) * 360.0 / N)
        for vi in f:
            kk = (int(vi), int(k))
            if kk not in key:
                p = verts[vi]
                yr = p[0] * math.sin(phi) + p[1] * math.cos(phi)
                u, v = C - yr, C - p[2]
                tu = (ti % COLS) * TILE_W + (u - CROP[0])
                tv = (ti // COLS) * TILE_H + (v - CROP[1])
                key[kk] = len(out_v)
                out_v.append((p[0] * UNIT, p[1] * UNIT, p[2] * UNIT))
                out_n.append(tuple(vn[vi]))
                out_st.append((float(np.clip(tu / AW, 0, 1)), float(np.clip(tv / AH, 0, 1))))
            tri.append(key[kk])
        out_t.append((tri[0], tri[1], tri[2]))
    surf = dict(name="pickle3d", shader="progs/pickle3d", tris=out_t, st=out_st, frames=[(out_v, out_n)])
    return dict(name="pickle3d", surfaces=[surf], nframes=1)


# --------------------------------------------------------------------------- MDL & MD3 Bakers
def parse_raw_mdl(d):
    h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
    assert h[0] == b"IDPO" and h[1] == 6
    scale, trans = h[2:5], h[5:8]
    nsk, sw, sh, nvo, nt, nf = h[12:18]
    o = 84
    skins8 = []
    for _ in range(nsk):
        kind = struct.unpack_from("<i", d, o)[0]
        assert kind == 0
        skins8.append(np.frombuffer(d, np.uint8, sw * sh, o + 4).reshape(sh, sw).copy())
        o += 4 + sw * sh
    st = np.frombuffer(d, "<i4", nvo * 3, o).reshape(nvo, 3)
    o += nvo * 12
    tri = np.frombuffer(d, "<i4", nt * 4, o).reshape(nt, 4)
    o += nt * 16
    names, pos, nrm = [], [], []
    for _ in range(nf):
        kind = struct.unpack_from("<i", d, o)[0]
        assert kind == 0
        o += 12
        names.append(d[o:o + 16].split(b"\0", 1)[0].decode("ascii", "replace"))
        o += 16
        v = np.frombuffer(d, np.uint8, nvo * 4, o).reshape(nvo, 4)
        o += nvo * 4
        pos.append(v[:, :3])
        nrm.append(v[:, 3])

    # Expand seam vertices for back-facing triangles
    key, vmap, uv, tris = {}, [], [], []
    for front, a, b, c in tri:
        t = []
        for v in (a, b, c):
            back = int(st[v, 0] != 0 and not front)
            kk = (int(v), back)
            if kk not in key:
                key[kk] = len(vmap)
                vmap.append(int(v))
                s_px = st[v, 1] + back * (sw // 2)
                t_px = st[v, 2]
                uv.append(((s_px + 0.5) / sw, (t_px + 0.5) / sh))
            t.append(key[kk])
        tris.append(tuple(t))
    return dict(
        scale=scale, trans=trans, sw=sw, sh=sh, nvo=nvo, nv=len(vmap), nt=nt, nf=nf,
        names=names, vmap=np.array(vmap, dtype="<u2"),
        uv=np.array(uv, dtype="<f4"), tris=tris,
        pos=np.array(pos, dtype=np.uint8), nrm=np.array(nrm, dtype=np.uint8),
        skins8=skins8,
    )


def bake_mdl(spec):
    path = spec["path"]
    r = parse_raw_mdl(open(path, "rb").read())
    assert r["nv"] < 65535
    # External .tga skins if present, else embedded 8-bit palette skin
    tgas = []
    for i in range(4):
        tp = f"{path}_{i}.tga"
        if os.path.exists(tp):
            tgas.append(load_tex_file(tp, max_dim=768))
    if not tgas:
        for s8 in r["skins8"]:
            rgb = PALETTE[s8]
            # Quake fullbright indices >= 224
            im = Image.fromarray(rgb.astype(np.uint8), "RGB")
            tgas.append(register_image(path + f":skin{len(tgas)}", im, max_dim=512, force_png=True, nearest=True))

    tris_clean, had_dup = strip_reversed_dups(r["tris"])
    tri_arr = np.array(tris_clean, dtype="<u2")
    edges_arr = build_edges(tris_clean)

    # Compute idle bounds (exclude 'gone' frame on v_robdob!)
    idle_frames = spec.get("idle_frames") or [i for i, nm in enumerate(r["names"]) if nm != "gone"][:16] or [0]
    pts_idle = r["pos"][idle_frames].astype(np.float32) * np.array(r["scale"], dtype=np.float32) + np.array(r["trans"], dtype=np.float32)
    mn = pts_idle.reshape(-1, 3).min(0)
    mx = pts_idle.reshape(-1, 3).max(0)

    surf_out = dict(
        name="body",
        nv=r["nv"],
        nt_draw=len(tris_clean),
        tris=add_buf(tri_arr.tobytes()),
        edges=add_buf(edges_arr.tobytes()),
        n_edges=len(edges_arr),
        uv=add_buf(r["uv"].tobytes()),
        wrap=False,
        shader=dict(tex=tgas, fps=0.0, alphaTest=False, additive=False, scrollV=0.0, unlit=False),
    )

    return dict(
        kind="mdl",
        nvo=r["nvo"],
        nt=r["nt"],
        nv=r["nv"],
        nf=r["nf"],
        nsurfs=1,
        scale=[round(float(x), 6) for x in r["scale"]],
        trans=[round(float(x), 6) for x in r["trans"]],
        vmap=add_buf(r["vmap"].tobytes()),
        pos=add_buf(r["pos"].tobytes()),
        nrm=add_buf(r["nrm"].tobytes()),
        names=r["names"],
        frameSkin=spec.get("frameSkin"),   # e.g. 8 means frames >= 8 use skin 1
        surfaces=[surf_out],
        bbox=[mn.round(2).tolist(), mx.round(2).tolist()],
        twoSided=bool(had_dup or spec.get("twoSided")),
    )


def try_rigid_fit(m):
    """Checks if an animated MD3 (nf >= 6) is a pure rigid/affine transform of frame 0 across all surfaces.
    Returns float32 array of shape (nf, 12) [col0(3), col1(3), col2(3), trans(3)] if max error < 0.035u, else None."""
    nf = m["nframes"]
    if nf < 6:
        return None
    P0 = np.vstack([np.array(s["frames"][0][0], dtype=np.float64) for s in m["surfaces"]])
    if len(P0) < 12:
        return None
    # Check rank (flat cards can't fit 3D affine uniquely)
    c0 = P0.mean(0)
    X = P0 - c0
    if np.linalg.matrix_rank(X, tol=1e-2) < 3:
        return None
    mats = np.zeros((nf, 12), dtype=np.float32)
    mats[0] = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
    for f in range(1, nf):
        Pf = np.vstack([np.array(s["frames"][f][0], dtype=np.float64) for s in m["surfaces"]])
        cf = Pf.mean(0)
        Y = Pf - cf
        A, _, _, _ = np.linalg.lstsq(X, Y, rcond=None)   # X @ A ~= Y => p_row @ A + (cf - c0 @ A)
        t = cf - c0 @ A
        pred = P0 @ A + t
        err = float(np.max(np.abs(pred - Pf)))
        if err > 0.035:
            return None
        # Column-major 4x3 for GLSL: M * vec4(p, 1) where col0=A[0,:], col1=A[1,:], col2=A[2,:], col3=t
        mats[f, 0:3] = A[0, :]
        mats[f, 3:6] = A[1, :]
        mats[f, 6:9] = A[2, :]
        mats[f, 9:12] = t
    return mats


PLAYER_259_NAMES = None


def get_pshot_frame_names():
    """Generate clean clip names for 259-frame third-person player weapon models (p_googun, p_srifle)."""
    # Standard Quake player frames 0..142 + extended Combat+/Q15 weapon frames 143..258
    r = parse_raw_mdl(load_pak_entry(ID1_PAK0, "progs/player.mdl"))
    names = list(r["names"])
    while len(names) < 259:
        names.append(f"ext{len(names) - 142}")
    return names[:259]


def bake_md3(spec):
    if spec.get("in_memory_md3") is not None:
        m = spec["in_memory_md3"]
        mdir = os.path.join(HERE, "out", "progs")
        stem = "pickle3d"
    else:
        path = spec["path"]
        m = md3lib.read(path)
        mdir = os.path.dirname(path)
        stem = os.path.splitext(os.path.basename(path))[0]

    nf = m["nframes"]
    rigid_mats = None if spec.get("no_rigid") else try_rigid_fit(m)
    is_rigid = rigid_mats is not None

    total_nv = 0
    total_nt = 0
    any_dup = False
    surfs_out = []

    idle_frames = spec.get("idle_frames")
    if not idle_frames:
        if nf == 259:
            idle_frames = list(range(12, 17))     # stand1..stand5
        elif nf >= 16 and stem.startswith("v_"):
            idle_frames = list(range(0, 8))
        else:
            idle_frames = list(range(min(nf, 8)))

    bbox_pts = []

    for s in m["surfaces"]:
        nv = len(s["st"])
        nt = len(s["tris"])
        assert nv < 65535, f"Surface {s['name']} has {nv} >= 65535 verts"
        total_nv += nv
        total_nt += nt

        tris_clean, had_dup = strip_reversed_dups(s["tris"])
        if had_dup:
            any_dup = True
        tri_arr = np.array(tris_clean, dtype="<u2")
        edges_arr = build_edges(tris_clean)
        uv_arr = np.array(s["st"], dtype="<f4")
        wrap = bool(uv_arr.min() < -0.01 or uv_arr.max() > 1.01)

        sh = resolve_md3_shader(s["shader"], mdir, stem)
        if sh["scrollV"] != 0.0:
            wrap = True

        for fi in idle_frames:
            vv_i = np.array(s["frames"][fi][0], dtype=np.float32)
            if len(vv_i):
                # Ignore collapsed origin dummy cards in pickle.md3 when computing bounds
                if stem == "pickle" and np.allclose(vv_i, 0.0):
                    continue
                bbox_pts.append(vv_i)

        frames_to_pack = [s["frames"][0]] if (nf == 1 or is_rigid) else s["frames"]
        xyz_list, nrm_list = [], []
        for vv, nn in frames_to_pack:
            xyz_i16 = np.clip(np.round(np.asarray(vv, dtype=np.float32) * 64.0), -32768, 32767).astype("<i2")
            nrm_u16 = enc_norm_u16(nn)
            xyz_list.append(xyz_i16)
            nrm_list.append(nrm_u16)

        xyz_bytes = np.concatenate(xyz_list, axis=0).tobytes()
        nrm_bytes = np.concatenate(nrm_list, axis=0).tobytes()

        surfs_out.append(dict(
            name=s["name"],
            nv=nv,
            nt_draw=len(tris_clean),
            tris=add_buf(tri_arr.tobytes()),
            edges=add_buf(edges_arr.tobytes()),
            n_edges=len(edges_arr),
            uv=add_buf(uv_arr.tobytes()),
            wrap=wrap,
            xyz=add_buf(xyz_bytes),
            nrm=add_buf(nrm_bytes),
            shader=sh,
        ))

    all_idle = np.vstack(bbox_pts)
    mn, mx = all_idle.min(0), all_idle.max(0)

    if spec.get("frame_names"):
        names = spec["frame_names"]
    elif nf == 259:
        names = get_pshot_frame_names()
    else:
        names = [f"frame{i + 1}" for i in range(nf)]

    out = dict(
        kind="md3",
        nt=total_nt,
        nv=total_nv,
        nf=nf,
        nsurfs=len(surfs_out),
        rigid=bool(is_rigid),
        names=names,
        surfaces=surfs_out,
        bbox=[mn.round(2).tolist(), mx.round(2).tolist()],
        twoSided=bool(any_dup or spec.get("twoSided")),
    )
    if is_rigid:
        out["rigidMats"] = add_buf(rigid_mats.tobytes())
    return out


# --------------------------------------------------------------------------- Clip Definitions
def vm22_names():
    return (
        [f"idle{i + 1}" for i in range(16)]
        + [f"fire{i + 1}" for i in range(3)]
        + ["gone"]
        + ["raise1", "raise2"]
    )


def vm_megaman_names():
    return (
        [f"idle{i + 1}" for i in range(16)]
        + ["wind1", "wind2", "throw1", "throw2"]
        + ["empty1", "empty2"]
        + ["pop1", "pop2", "pop3", "pop4"]
    )


def banana_names():
    return [f"idle{i + 1}" for i in range(8)] + [f"fire{i + 1}" for i in range(8)]


def girl_vm_names():
    return [f"idle{i + 1}" for i in range(8)] + [f"throw{i + 1}" for i in range(8)]


def googun_vm_names():
    return ["idle1"] + [f"kick{i + 1}" for i in range(6)]


def goo_names():
    return ["puff1", "glob1", "splat1", "splat2", "splat3", "splat4"]


def pickle_view_names():
    return [f"view{i + 1}" for i in range(16)] + [f"scream{i + 1}" for i in range(4)]


# --------------------------------------------------------------------------- Complete Custom Models Catalog
def build_catalog():
    pickle3d_md3 = build_pickle3d_in_memory()

    return [
        # ==================== 1. 3D RECONSTRUCTIONS (CHARACTERS & HEADS) ====================
        dict(
            id="bigears",
            name="Giant-Eared 3D Floating Head",
            cat="reconstructions",
            status="active",
            file="progs/bigears.md3",
            script="source/mm_tools/build_bigears_head.py",
            path=os.path.join(PROGS, "bigears.md3"),
            gain=1.02,
            az=-0.34,
            el=0.08,
            presets=[
                ["Front Face", 0.0, 0.05, 0.90],
                ["3/4 View", -0.58, 0.08, 0.92],
                ["Left Giant Ear", 1.38, 0.08, 0.92],
                ["Back of Head", 3.14, 0.10, 0.94],
                ["Right Profile", -1.48, 0.08, 0.92],
            ],
            summary="True 3D head + sculpted giant curved ears reconstructed from 48 turntable views, Blender-remeshed & region-pure 1024px textured.",
            how=[
                "Segments head, hair, and giant ears from the 145-frame turntable clip via Lab chroma + luma studio background subtraction (excluding pedestal & shadow).",
                "Separates central cranium/face from the two giant cupped ears to prevent visual-hull cheek webbing, carving real 3D nose/lips/chin + embossed ear cartilage.",
                "Voxel-remeshed, smoothed, decimated (5,600 tris), and UV-unwrapped in Blender 5.2, then region-pure baked at 1024×1024 with 3D k-NN crease inpainting.",
            ],
            role="Custom 3D floating head reconstructed from Grok 360° turntable video (head only).",
        ),
        dict(
            id="floathead",
            name="Rob Dob Floating Head (v2)",
            cat="reconstructions",
            status="active",
            file="progs/floathead.mdl",
            script="source/mm_tools/build_floathead.py",
            path=os.path.join(PROGS, "floathead.mdl"),
            gain=1.45,
            az=-0.28,
            el=0.14,
            frameSkin=8,
            summary="3D floating head reconstructed from 6 turnaround video views with jaw rig and dual closed/screaming skins.",
            how=[
                "Carved from 6 calibrated angles of a turnaround video onto a 48×60 superellipse skull ring grid, preserving real nose bridge and ear silhouettes.",
                "Multi-view cylindrical unwrap blends video frames by surface normal facing angle; skin 1 paints an open cartoon mouth, teeth, and tongue.",
                "Frames 0–7 (idle1–8) bob gently with closed mouth; frames 8–19 (open, rush, pain) drop the jaw vertices and swap to skin 1.",
            ],
            role="Spawned by the Rob Dob Trap (monster_robdob): hovers, screams, and rushes enemy players.",
        ),
        dict(
            id="v_robdob",
            name="Held Rob Dob Head (Viewmodel)",
            cat="reconstructions",
            status="active",
            file="progs/v_robdob.mdl",
            script="source/mm_tools/build_floathead.py",
            path=os.path.join(PROGS, "v_robdob.mdl"),
            gain=1.45,
            az=2.85,
            el=0.18,
            pov=True,
            summary="First-person held Rob Dob head hovering in the lower-right corner, turned back to look at you.",
            how=[
                "Scaled-down 15.2-unit copy of the turntable head oriented via robdob_vm.py / robdob_viewmodel_tuner.html.",
                "Frames 0–7 (bob1–8) sway in the player's hand; frame 8 (gone) drops below screen while recharging.",
            ],
            role="First-person weapon viewmodel for the Rob Dob Trap launcher.",
        ),
        dict(
            id="floathead_v1",
            name="Rob Dob Floating Head (1-Photo v1)",
            cat="reconstructions",
            status="archived",
            file="source/mm_tools/preview/floathead/floathead.mdl",
            script="source/mm_tools/build_floathead_photo.py",
            path=os.path.join(HERE, "preview", "floathead", "floathead.mdl"),
            gain=1.85,
            az=-0.28,
            el=0.14,
            frameSkin=8,
            summary="Earlier single-photograph 3D Rob Dob head prototype built before the turnaround video existed.",
            how=[
                "Extruded a single front portrait onto an analytic cranial lathe and synthesized hair wrap around the back of the head.",
                "Includes the same 20-frame idle/open/rush/pain animation layout and dual mouth skins.",
            ],
            role="Archived v1 prototype (superseded by the 6-view turnaround reconstruction).",
        ),
        dict(
            id="johnhead3d",
            name="John's Flying 3D Head",
            cat="reconstructions",
            status="active",
            file="progs/johnhead3d.md3",
            script="source/mm_tools/build_john_head3d.py",
            path=os.path.join(PROGS, "johnhead3d.md3"),
            gain=1.75,
            az=-0.28,
            el=0.15,
            summary="True 3D voxel visual-hull head carved in Blender from 113 green-screen turntable video frames.",
            how=[
                "Green-keyed 145 frames of johnhead.mp4 and iteratively re-aligned drifting head silhouettes against the 3D hull.",
                "Remeshed, smoothed, and decimated to 3,500 triangles in Blender, then projected every texel from the most squarely facing video frame.",
            ],
            role="Flying screaming projectile head launched by the JohnWave weapon.",
        ),
        dict(
            id="grenade",
            name="JohnWave 3D Head Grenade",
            cat="reconstructions",
            status="active",
            file="progs/grenade.mdl",
            script="source/mm_tools/build_head_grenade.py",
            path=os.path.join(PROGS, "grenade.mdl"),
            gain=1.65,
            az=-0.28,
            el=0.16,
            summary="Custom 3D head grenade carved from front and back photos, replacing Quake's stock pineapple grenade.",
            how=[
                "Fits front and rear head silhouettes onto a 32×32 ring mesh with nose protrusion and cylindrical high-res TGA skin.",
            ],
            role="Replaces progs/grenade.mdl for bounced grenade launcher & cluster projectiles.",
        ),
        dict(
            id="suitguy",
            name="Suit Guy (Player Model)",
            cat="reconstructions",
            status="archived",
            file="_backups/player_bodies_removed_2026-10-30/progs/suitguy.mdl",
            script="source/mm_tools/build_char_models.py",
            path=os.path.join(BKP_CHARS, "suitguy.mdl"),
            gain=1.8,
            az=-0.28,
            el=0.2,
            summary="Full 143-frame Quake player model built from front & back photos of a man in a business suit.",
            how=[
                "Segments torso, legs, arms, and head silhouettes from front/back photos into anatomical elliptical cross-section tubes.",
                "Procedurally poses joints across all 143 classic Quake player.qc animation frames (stand, rockrun, axrun, shotatt, axatt, pain, death).",
            ],
            role="Custom player character model (archived to _backups/ on 2026-10-30).",
        ),
        dict(
            id="robeguy",
            name="Robe Guy (Player Model)",
            cat="reconstructions",
            status="archived",
            file="_backups/player_bodies_removed_2026-10-30/progs/robeguy.mdl",
            script="source/mm_tools/build_char_models.py",
            path=os.path.join(BKP_CHARS, "robeguy.mdl"),
            gain=1.75,
            az=-0.28,
            el=0.2,
            summary="Full 143-frame Quake player model built from front & back photos in a white bathrobe.",
            how=[
                "Uses wider robed torso/skirt silhouette profiles while driving all 143 standard Quake skeletal animations.",
            ],
            role="Custom player character model (archived to _backups/ on 2026-10-30).",
        ),
        dict(
            id="wifeguy",
            name="Wife (Player Model)",
            cat="reconstructions",
            status="archived",
            file="_backups/player_bodies_removed_2026-10-30/progs/wifeguy.mdl",
            script="source/mm_tools/build_char_models.py",
            path=os.path.join(BKP_CHARS, "wifeguy.mdl"),
            gain=1.8,
            az=-0.28,
            el=0.2,
            summary="Full 143-frame Quake player model built from front & back photos, complete with custom high-colour TGA skin.",
            how=[
                "Silhouette-fitted limb/torso tubes + procedural 143-frame Quake animation rig from build_char_models.py.",
            ],
            role="Custom player character model (archived to _backups/ on 2026-10-30).",
        ),
        dict(
            id="girl",
            name="Girlfriend Runner (Video Hull)",
            cat="reconstructions",
            status="archived",
            file="source/mm_tools/out/removed_guns_src/girl_assets/progs/girl.md3",
            script="source/mm_tools/girl_pipeline/girl_md3.py",
            path=os.path.join(HERE, "out", "removed_guns_src", "girl_assets", "progs", "girl.md3"),
            gain=1.05,
            az=-0.28,
            el=0.18,
            frame_names=[f"run{i + 1}" for i in range(8)],
            summary="26,000-triangle full-body 3D human reconstruction from a turnaround video, split across 5 MD3 surfaces.",
            how=[
                "Built via multi-stage silhouette segmentation, optical-flow turnaround tracking, visual-hull carving, and 2048px atlas baking.",
                "Split into five <=4,000-vertex MD3 surfaces with an 8-frame running lean/roll/bob cycle.",
            ],
            role="Chasing companion projectile from the archived Girlfriend Gun.",
        ),
        dict(
            id="v_banana_girl",
            name="Held Girlfriend (Viewmodel)",
            cat="reconstructions",
            status="archived",
            file="source/mm_tools/out/removed_guns_src/girl_assets/progs/v_banana_girl.md3",
            script="source/mm_tools/girl_pipeline/girl_md3.py",
            path=os.path.join(HERE, "out", "removed_guns_src", "girl_assets", "progs", "v_banana_girl.md3"),
            gain=1.05,
            az=2.8,
            el=0.18,
            pov=True,
            no_rigid=True,
            frame_names=girl_vm_names(),
            summary="Decimated 8-unit miniature 3D Girlfriend model held in the player's hand with 16 sway & throw frames.",
            how=[
                "Lower-poly bake from girl_pipeline (baked_lo.npz) split across 2 MD3 surfaces with idle sway (0–7) and wind-up toss (8–15).",
            ],
            role="First-person viewmodel for the archived Girlfriend Gun.",
        ),

        # ==================== 2. CUSTOM WEAPONS, VIEWMODELS & PROJECTILES ====================
        dict(
            id="v_laptop",
            name="AOL Dial-Up Hacker Laptop Gun (Viewmodel)",
            cat="weapons",
            status="active",
            file="progs/v_laptop.md3",
            script="source/mm_tools/build_laptop_gun.py",
            path=os.path.join(PROGS, "v_laptop.md3"),
            gain=1.65,
            az=2.82,
            el=0.22,
            pov=True,
            defaultPov=True,
            animFps=12,
            no_rigid=True,
            defaultClipName="__all__",
            idle_frames=list(range(0, 12)),
            frame_names=[f"idle{i + 1}" for i in range(12)] + [f"shoot{i + 1}" for i in range(22)],
            presets=[
                ["3/4 Orbit (Hands & Screen)", 2.72, 0.24, 0.94],
                ["Screen & Keyboard Close-Up", 3.12, 0.14, 0.72],
                ["Side & Electric Bolts", 1.85, 0.16, 1.15],
                ["Outer Lid Emblem", 0.15, 0.16, 0.92],
            ],
            summary="Black laptop held in the right hand showing 'Hacking internet lag' + AOL Dial-Up & Download; shooting brings in the left hand typing fast and fires 3D electric bolts.",
            how=[
                "Held in the player's right hand (thumb clamped over the right palm-rest, four fingers curled under the matte-black chassis) with a 3D sculpted QWERTY keyboard, red TrackPoint, and 56k RJ-11 phone cord.",
                "Lossless 1024×1024 unlit LCD screen displays 'Hacking internet lag' alongside Windows 98 AOL 5.0 Dial-Up & AOL File Download windows.",
                "On shoot (shoot1–22): the left hand whips up onto the keyboard and hammers the 3D keys at high speed, flipping the screen into 'Hacking internet lag' overdrive and discharging 3D cyan-white electric lightning bolts.",
            ],
            role="First-person AOL Dial-Up / Internet Lag electric hacker laptop weapon (34 frames: 12 idle + 22 fast-typing & electric discharge).",
        ),
        dict(
            id="jetpack",
            name="Twin-Thruster Jetpack (JP-02)",
            cat="weapons",
            status="active",
            file="progs/jetpack.md3",
            script="source/mm_tools/build_jetpack.py",
            path=os.path.join(PROGS, "jetpack.md3"),
            gain=1.65,
            az=2.55,
            el=0.16,
            defaultClipName="thrust",
            presets=[
                ["Rear Thrusters", 2.72, 0.14, 0.96],
                ["Front Harness", 0.45, 0.16, 0.96],
                ["Underneath Nozzles", 2.95, -0.58, 0.82],
                ["Side Winglet", 1.57, 0.10, 0.95],
            ],
            idle_frames=list(range(0, 8)),
            frame_names=[f"thrust{i + 1}" for i in range(8)] + [f"idle{i + 1}" for i in range(8)],
            summary="Procedural 9-surface twin-cylinder rocket jetpack with plasma core, pressure dial, harness, joysticks & shock-diamond plumes.",
            how=[
                "Twin brushed-titanium propellant tanks with 'JP-02' stencil bands, top bleed valves, roll-bar hoops, swept hazard winglets, and navigation strobes.",
                "Central gunmetal turbopump spine with unlit cyan plasma core window, analog PSI gauge dial, and braided Catmull-Rom fuel hoses.",
                "Padded EVA backplate, contoured over-the-shoulder straps, quick-release buckles, fold-down twin pilot throttle sticks, and gimballed de Laval nozzles with 4-frame additive Mach shock-diamond exhaust plumes.",
            ],
            role="Wearable twin-thruster rocket pack & world pickup (16 frames: 8 full afterburner thrust + 8 standby pilot-flame idle).",
        ),
        dict(
            id="v_megaman",
            name="Mega Man Launcher (Viewmodel)",
            cat="weapons",
            status="active",
            file="progs/v_megaman.md3",
            script="source/mm_tools/build_viewmodel.py",
            path=os.path.join(PROGS, "v_megaman.md3"),
            gain=2.15,
            az=2.65,
            el=0.22,
            pov=True,
            frame_names=vm_megaman_names(),
            summary="Procedural blue gloved fist & articulated fingers gripping the wheeled 'Mega Man' Segway-pipe contraption across 26 frames.",
            how=[
                "Constructs palm, thumb, and four multi-knuckle fingers procedurally around Mega Man's central metal pipe.",
                "Frames 0–15 spin Mega Man's wheels with idle bob; 16–19 uncurl fingers and hurl him forward; 20–21 show empty open hand; 22–25 pop a new Mega Man into grip.",
            ],
            role="First-person weapon viewmodel for the Mega Man Launcher (Impulse 14).",
        ),
        dict(
            id="megaman",
            name="Wheeled Mega Man Contraption",
            cat="weapons",
            status="active",
            file="progs/megaman.md3",
            script="source/mm_tools/megaman.qc",
            path=os.path.join(PROGS, "megaman.md3"),
            gain=2.15,
            az=0.6,
            el=0.22,
            frame_names=[f"drive{i + 1}" for i in range(16)],
            summary="Two-wheeled Segway-style axle & pipe contraption ('Mega Man') with 3 surfaces (central pipe + spinning left/right wheels).",
            how=[
                "Converted from megaman1.glb into wheelL, wheelR, and central pipe surfaces with 16 wheel-rotation frames driven by megaman.qc as it steers, honks, hops, and leaps.",
            ],
            role="Thrown autonomous wheeled bomb contraption that chases and leaps onto enemies.",
        ),
        dict(
            id="v_googun",
            name="Goo Gun (First-Person Viewmodel)",
            cat="weapons",
            status="active",
            file="progs/v_googun.md3",
            script="source/mm_tools/build_googun.py",
            path=os.path.join(PROGS, "v_googun.md3"),
            gain=1.95,
            az=2.45,
            el=0.24,
            pov=True,
            frame_names=googun_vm_names(),
            summary="100% procedural sci-fi foam cannon built from lathes and boxes with 8 procedural material surfaces.",
            how=[
                "Every barrel rib, nozzle cone, sight block, grip, and pressurized side goo tank is generated mathematically in Python.",
                "Includes 8 procedural textures (brushed metal, rubber grip, hazard stripes decal, bubbling green goo tank) and 7 recoil frames.",
            ],
            role="First-person viewmodel replacing the single-barrel shotgun (goo.qc).",
        ),
        dict(
            id="p_googun",
            name="Goo Gun (3rd-Person Player Rig)",
            cat="weapons",
            status="active",
            file="progs/p_googun.md3",
            script="source/mm_tools/build_googun.py",
            path=os.path.join(PROGS, "p_googun.md3"),
            gain=1.95,
            az=0.65,
            el=0.22,
            summary="Third-person Goo Gun rigidly fitted to all 259 Quake 1.5 player shotgun hand animations.",
            how=[
                "Extracts per-frame PCA/SVD rigid transforms from Quake 1.5's 259-frame p_shot.md3 and applies them to the procedural Goo Gun.",
            ],
            role="Exterior weapon model visible in other players' hands during multiplayer.",
        ),
        dict(
            id="goo",
            name="Expanding Goo Foam Blob",
            cat="weapons",
            status="active",
            file="progs/goo.md3",
            script="source/mm_tools/build_googun.py",
            path=os.path.join(PROGS, "goo.md3"),
            gain=2.5,
            az=0.6,
            el=0.28,
            frame_names=goo_names(),
            summary="Cluster of lumpy polyurethane foam puffs that morphs from a tight flying glob into an expanding wall/player splat.",
            how=[
                "Frame 0 is full hardened foam size; frame 1 squeezes into a compact in-flight shot; frames 2–5 animate the expanding splat with overshoot.",
                "Paired with a procedural cellular-pore tileable foam texture (goo.png).",
            ],
            role="Projectile & sticky movement-snaring foam splat fired by the Goo Gun.",
        ),
        dict(
            id="pickle_bomb",
            name="Thrown 3D Pickle Bomb",
            cat="weapons",
            status="active",
            file="progs/pickle_bomb.md3",
            script="source/mm_tools/build_pickle_assets.py",
            path=os.path.join(PROGS, "pickle_bomb.md3"),
            gain=2.4,
            az=2.5,
            el=0.25,
            summary="Procedural bent, bumpy 3D gherkin mesh with an animated wandering-eye Pickle Surprise face.",
            how=[
                "Generated as a curved, wart-displaced tube with procedural gherkin skin and a 5 fps animmap shader (pickle_bombskin) cycling 4 face frames.",
            ],
            role="Sticky thrown bomb for the Pickle Surprise weapon before it inflates into the giant balloon.",
        ),
        dict(
            id="pickle_gib",
            name="3D Pickle Blast Shrapnel",
            cat="weapons",
            status="active",
            file="progs/pickle_gib.md3",
            script="source/mm_tools/build_pickle_assets.py",
            path=os.path.join(PROGS, "pickle_gib.md3"),
            gain=2.4,
            az=0.7,
            el=0.28,
            summary="3D bumpy warty gherkin shrapnel model showered outward when a Pickle Surprise balloon detonates.",
            how=[
                "Shares the bent warty 3D gherkin geometry with a full-wrap procedural warty skin texture (pickle_skin.png).",
            ],
            role="Bouncing shrapnel pickles spawned in a shower by Pickle Surprise explosions.",
        ),
        dict(
            id="pickle",
            name="Standing Pickle (16-View Turntable)",
            cat="weapons",
            status="active",
            file="progs/pickle.md3",
            script="source/mm_tools/make_pickle_views.py",
            path=os.path.join(PROGS, "pickle.md3"),
            gain=2.5,
            az=3.45,
            el=0.08,
            turntable16=True,
            twoSided=True,
            frame_names=pickle_view_names(),
            summary="Camera-reactive 16-angle turntable model + 4 screaming pre-blast faces—drag to orbit around all 360°!",
            how=[
                "Packs 20 card surfaces (16 turntable cutouts every 22.5° + 4 wide-mouthed scream faces). In frame k only surface k is expanded.",
                "In game (Pk_Customize) and in this viewer, orbiting around the pickle swaps frames to show the true side/back/front angle from where you stand.",
            ],
            role="Giant inflating Pickle Surprise balloon bomb in game (screaming right before detonation).",
        ),
        dict(
            id="pickle3d",
            name="Standing Pickle (3D Voxel Hull)",
            cat="weapons",
            status="archived",
            file="source/mm_tools/make_pickle3d.py + out/progs/pickle3d.png",
            script="source/mm_tools/make_pickle3d.py",
            in_memory_md3=pickle3d_md3,
            gain=2.5,
            az=3.45,
            el=0.14,
            summary="Experimental solid 3D marching-cubes visual hull carved from 15 turntable cutouts of the Pickle.",
            how=[
                "Carves a 2px voxel grid across 15 good silhouettes of the turntable video, extracts the isosurface via marching cubes, and applies Taubin smoothing.",
                "Projects each triangle onto its most squarely facing turntable tile in a 1080×1440 atlas (out/progs/pickle3d.png).",
            ],
            role="Archived 3D hull experiment (superseded by the sharper 16-view turntable sprite model).",
        ),
        dict(
            id="v_pickle",
            name="Held Pickle Surprise (Viewmodel)",
            cat="weapons",
            status="active",
            file="progs/v_pickle.md3",
            script="source/mm_tools/build_pickle_assets.py",
            path=os.path.join(PROGS, "v_pickle.md3"),
            gain=1.65,
            az=3.14,
            el=0.05,
            pov=True,
            swayOnly=True,
            twoSided=True,
            summary="First-person held Pickle Surprise viewmodel playing a 94-step ping-pong video shader of an armored fist.",
            how=[
                "Keyed-out hold video frames (vpk_00..47.png) driven by scripts/pickle.shader's 8 fps ping-pong animmap.",
            ],
            role="First-person weapon viewmodel when holding the Pickle Surprise Bomb.",
        ),
        dict(
            id="ccc",
            name="Extruded 3D 'C' Bolt (CCC Gun)",
            cat="weapons",
            status="active",
            file="progs/ccc.md3",
            script="source/mm_tools/build_ccc.py",
            path=os.path.join(PROGS, "ccc.md3"),
            gain=1.15,
            az=0.45,
            el=0.2,
            summary="Procedural extruded 3D yellow letter 'C' projectile with bevelled arc segments and lemon-gold gradient.",
            how=[
                "Sweeps an inner/outer C-arc polygon in Python and extrudes front, back, and bevelled side walls.",
            ],
            role="Rapid-fire flying 'C' projectile for the CCC weapon.",
        ),
        dict(
            id="fg_pongball",
            name="Rally Master Ping-Pong Ball",
            cat="weapons",
            status="active",
            file="progs/fg_pongball.md3",
            script="source/mm_tools/build_fungun_viewmodels.py",
            path=os.path.join(PROGS, "fg_pongball.md3"),
            gain=1.15,
            az=0.6,
            el=0.25,
            summary="Procedural 2.2-unit orange ping-pong sphere that gains damage with every wall ricochet.",
            how=[
                "Generated via build_fungun_viewmodels.py's UV-sphere builder with an embedded 8×8 orange PNG texture.",
            ],
            role="Ricocheting projectile hit by the Rally Master ping-pong paddle.",
        ),
        dict(
            id="v_banana",
            name="Procedural Banana Tube Gun",
            cat="weapons",
            status="archived",
            file="source/mm_tools/out/removed_guns_src/banana_assets/progs/v_banana.md3",
            script="source/mm_tools/build_banana_assets.py",
            path=os.path.join(HERE, "out", "removed_guns_src", "banana_assets", "progs", "v_banana.md3"),
            gain=1.35,
            az=2.4,
            el=0.22,
            pov=True,
            frame_names=banana_names(),
            summary="Procedural yellow cylindrical bazooka tube with dark muzzle interior and 16 bob/recoil frames.",
            how=[
                "16-sided procedural tube mesh in eye space: frames 0–7 sway gently, frames 8–15 kick backward on firing.",
            ],
            role="First-person viewmodel from the archived Banana Gun.",
        ),
        dict(
            id="banana",
            name="Slippery Banana Projectile",
            cat="weapons",
            status="archived",
            file="source/mm_tools/out/removed_guns_src/banana_assets/progs/banana.md3",
            script="source/mm_tools/build_banana_assets.py",
            path=os.path.join(HERE, "out", "removed_guns_src", "banana_assets", "progs", "banana.md3"),
            gain=1.25,
            az=0.8,
            el=0.3,
            summary="3D banana projectile paired with the procedural Banana Tube Gun.",
            how=[
                "Converted from CC-BY SimReady fruit asset and scaled/oriented for Quake projectile physics in build_banana_assets.py.",
            ],
            role="Projectile from the archived Banana Gun.",
        ),

        # ==================== 3. PROCEDURAL EFFECTS, HATS & DEBRIS ====================
        dict(
            id="aura",
            name="Spawn-Protection Aura Bubble",
            cat="effects",
            status="active",
            file="progs/aura.md3",
            script="source/mm_tools/build_aura_assets.py",
            path=os.path.join(PROGS, "aura.md3"),
            gain=1.8,
            az=0.6,
            el=0.22,
            twoSided=True,
            summary="Glowing cyan energy shell with additive blending and continuous vertical UV scrolling.",
            how=[
                "Procedural 672-triangle spheroid paired with scripts/aura.shader (cull none, blendfunc add, tcmod scroll 0 0.6).",
            ],
            role="Surrounds players during spawn protection / invulnerability.",
        ),
        dict(
            id="jw_wave",
            name="JohnWave Rippled Tidal Ring",
            cat="effects",
            status="active",
            file="progs/jw_wave.md3",
            script="source/mm_tools/build_john_assets.py",
            path=os.path.join(PROGS, "jw_wave.md3"),
            gain=1.25,
            az=0.6,
            el=0.45,
            twoSided=True,
            summary="Procedural cresting blue-and-white water wave ring that expands across the floor.",
            how=[
                "Sinusoidally rippled annular mesh with a procedural foaming crest texture (jw_wave.png).",
            ],
            role="Expanding shockwave ring spawned by JohnWave blasts.",
        ),
        dict(
            id="fedora",
            name="Hack Attack Red Fedora",
            cat="effects",
            status="active",
            file="progs/fedora.md3",
            script="source/mm_tools/build_hackmon_models.py",
            path=os.path.join(PROGS, "fedora.md3"),
            gain=1.35,
            az=0.65,
            el=0.28,
            twoSided=True,
            summary="Procedural pinched-crown, curled-brim 'Red Hat' Linux fedora worn by hacked victims.",
            how=[
                "Mathematically sculpted crown dent, side pinches, rolled brim, and dark hatband surface in build_hackmon_models.py.",
            ],
            role="Placed on enemy players' heads while they are hacked by the Hack Attack CRT.",
        ),
        dict(
            id="hd_kbd",
            name="Hack Debris: PC Keyboard",
            cat="effects",
            status="active",
            file="progs/hd_kbd.md3",
            script="source/mm_tools/build_hackdebris.py",
            path=os.path.join(PROGS, "hd_kbd.md3"),
            gain=1.15,
            az=-1.2,
            el=0.65,
            summary="Procedural beige AT/PS2 mechanical keyboard gib with drawn keycap blocks and LEDs.",
            how=[
                "Wedge-profile box mesh with a procedurally drawn 256×96 keycap layout (function row, spacebar, arrow cluster, lock LEDs).",
            ],
            role="Flies out in a shower of 2001 LAN hardware when a Hack Attack monitor shatters.",
        ),
        dict(
            id="hd_mouse",
            name="Hack Debris: Beige 2-Button Mouse",
            cat="effects",
            status="active",
            file="progs/hd_mouse.md3",
            script="source/mm_tools/build_hackdebris.py",
            path=os.path.join(PROGS, "hd_mouse.md3"),
            gain=1.1,
            az=-1.1,
            el=0.6,
            summary="Procedural retro 2-button serial/PS2 ball mouse debris model.",
            how=[
                "Bevelled box mesh with procedurally drawn left/right button seam and scroll wheel.",
            ],
            role="Computer debris gib spawned by Hack Attack CRT impacts.",
        ),
        dict(
            id="hd_floppy",
            name='Hack Debris: 3.5" Floppy Disk',
            cat="effects",
            status="active",
            file="progs/hd_floppy.md3",
            script="source/mm_tools/build_hackdebris.py",
            path=os.path.join(PROGS, "hd_floppy.md3"),
            gain=1.15,
            az=-1.2,
            el=0.68,
            summary='Procedural 3.5-inch floppy diskette complete with sliding metal shutter and striped paper label.',
            how=[
                "Thin slab mesh + procedural 128×128 diskette top texture generated by build_hackdebris.py.",
            ],
            role="Computer debris gib spawned by Hack Attack CRT impacts.",
        ),
        dict(
            id="hd_cd",
            name="Hack Debris: Rainbow CD-ROM",
            cat="effects",
            status="active",
            file="progs/hd_cd.md3",
            script="source/mm_tools/build_hackdebris.py",
            path=os.path.join(PROGS, "hd_cd.md3"),
            gain=1.15,
            az=-1.0,
            el=0.7,
            summary="Procedural 16-sided annular CD-ROM disc with iridescent rainbow diffraction bands.",
            how=[
                "Ring cylinder with an actual center spindle hole and angular HSV rainbow sheen texture (hd_cd_top.png).",
            ],
            role="Spinning CD-ROM shrapnel from Hack Attack explosions.",
        ),
        dict(
            id="hd_board",
            name="Hack Debris: Green Mother-PCB",
            cat="effects",
            status="active",
            file="progs/hd_board.md3",
            script="source/mm_tools/build_hackdebris.py",
            path=os.path.join(PROGS, "hd_board.md3"),
            gain=1.25,
            az=-1.2,
            el=0.68,
            summary="Procedural green circuit board populated with DIP IC chips, gold edge fingers, and copper traces.",
            how=[
                "PCB slab with procedurally drawn silicon packages, pin rows, traces, and capacitors (hd_board_top.png).",
            ],
            role="Circuit-board debris gib from Hack Attack explosions.",
        ),
        dict(
            id="mm_wheel",
            name="Mega Man Debris: Detached Wheel",
            cat="effects",
            status="active",
            file="progs/mm_wheel.md3",
            script="source/mm_tools/build_mm_debris.py",
            path=os.path.join(PROGS, "mm_wheel.md3"),
            gain=1.35,
            az=0.7,
            el=0.35,
            summary="Procedural rubber tire and blue-rimmed hubcap bounced around when a Mega Man bot explodes.",
            how=[
                "3-surface cylindrical tire + dual hubcap discs generated by build_mm_debris.py.",
            ],
            role="Bouncing wheel gib spawned when Mega Man blows up.",
        ),
        dict(
            id="mm_axle",
            name="Mega Man Debris: Steel Axle",
            cat="effects",
            status="active",
            file="progs/mm_axle.md3",
            script="source/mm_tools/build_mm_debris.py",
            path=os.path.join(PROGS, "mm_axle.md3"),
            gain=1.2,
            az=0.8,
            el=0.3,
            summary="Procedural steel axle bar with end caps thrown from exploding Mega Man bots.",
            how=[
                "3-surface hexagonal rod + end-cap flanges generated by build_mm_debris.py.",
            ],
            role="Spinning metal axle gib spawned when Mega Man blows up.",
        ),
        dict(
            id="zap1",
            name="Hack Zap Bolt #1",
            cat="effects",
            status="active",
            file="progs/zap1.md3",
            script="source/mm_tools/build_hackmon_models.py",
            path=os.path.join(PROGS, "zap1.md3"),
            gain=1.9,
            az=-1.15,
            el=0.25,
            twoSided=True,
            summary="Jagged green crossed-ribbon electric arc (#1 of 3 random variants) for Hack Attack zaps.",
            how=[
                "Orthogonal crossed zig-zag ribbons along +X with soft green core-glow texture rendered additively.",
            ],
            role="Arcing green electricity between Hack Attack monitors and nearby victims.",
        ),
        dict(
            id="zap2",
            name="Hack Zap Bolt #2",
            cat="effects",
            status="active",
            file="progs/zap2.md3",
            script="source/mm_tools/build_hackmon_models.py",
            path=os.path.join(PROGS, "zap2.md3"),
            gain=1.9,
            az=-1.15,
            el=0.25,
            twoSided=True,
            summary="Jagged green crossed-ribbon electric arc (#2 of 3, medium zig-zag seed).",
            how=[
                "64-triangle crossed-ribbon lightning variant generated with seed #2 in build_hackmon_models.py.",
            ],
            role="Arcing green electricity variant #2 for Hack Attack.",
        ),
        dict(
            id="zap3",
            name="Hack Zap Bolt #3",
            cat="effects",
            status="active",
            file="progs/zap3.md3",
            script="source/mm_tools/build_hackmon_models.py",
            path=os.path.join(PROGS, "zap3.md3"),
            gain=1.9,
            az=-1.15,
            el=0.25,
            twoSided=True,
            summary="Jagged green crossed-ribbon electric arc (#3 of 3, wildest zig-zag seed).",
            how=[
                "72-triangle crossed-ribbon lightning variant generated with seed #3 in build_hackmon_models.py.",
            ],
            role="Arcing green electricity variant #3 for Hack Attack.",
        ),
        dict(
            id="laser",
            name="Rob Trap Red Laser Beam",
            cat="effects",
            status="active",
            file="progs/laser.md3",
            script="source/mm_tools/build_robtrap_assets.py",
            path=os.path.join(PROGS, "laser.md3"),
            gain=2.0,
            az=-1.15,
            el=0.22,
            twoSided=True,
            summary="100-unit crossed-ribbon red tripwire/beam scaled dynamically in QuakeC.",
            how=[
                "Crossed horizontal + vertical 100-unit quads along +X with a glowing red falloff strip (laser_red.png).",
            ],
            role="Additive red tripwire / targeting laser beam for Rob Trap.",
        ),

        # ==================== 4. ADAPTED & CUSTOM-RIGGED HYBRIDS ====================
        dict(
            id="v_hackmon",
            name='Hack Attack "> HACKING" CRT (Viewmodel)',
            cat="adapted",
            status="active",
            file="progs/v_hackmon.md3",
            script="source/mm_tools/build_hackmon_models.py + build_fungun_viewmodels.py",
            path=os.path.join(PROGS, "v_hackmon.md3"),
            gain=1.85,
            az=2.85,
            el=0.16,
            pov=True,
            frame_names=vm22_names(),
            summary="CRT monitor given a custom procedural green phosphor '> HACKING' screen and 22-frame held animation rig.",
            how=[
                "Replaces the SimReady CRT's blank screen surface with a procedural scanlined '> HACKING' terminal texture (hm_scr_a.png).",
                "Posed screen-towards-player and animated across 22 idle/throw/raise frames by build_fungun_viewmodels.py.",
            ],
            role="First-person viewmodel for the Hack Attack thrown CRT weapon.",
        ),
        dict(
            id="hackmon_a",
            name='Thrown "> HACKING" CRT Monitor',
            cat="adapted",
            status="active",
            file="progs/hackmon_a.md3",
            script="source/mm_tools/build_hackmon_models.py",
            path=os.path.join(PROGS, "hackmon_a.md3"),
            gain=1.85,
            az=0.45,
            el=0.18,
            summary="World projectile CRT monitor with custom procedural '> HACKING' green scanline screen.",
            how=[
                "19-surface CRT mesh with custom phosphor terminal texture on surface 0 and darkened beige/rubber housing.",
            ],
            role="Thrown monitor projectile that zaps nearby enemies and puts red fedoras on them.",
        ),
        dict(
            id="v_sledge",
            name="Whack-a-Mole Sledgehammer (Viewmodel)",
            cat="adapted",
            status="active",
            file="progs/v_sledge.md3",
            script="source/mm_tools/build_fungun_viewmodels.py",
            path=os.path.join(PROGS, "v_sledge.md3"),
            gain=1.85,
            az=2.5,
            el=0.2,
            pov=True,
            frame_names=vm22_names(),
            summary="Sledgehammer posed in first-person grip and rigged with 22 idle-bob, swing-kick, and reload frames.",
            how=[
                "Adapted from SimReady sledgehammer mesh, darkened 0.5× for Combat+ lighting, and driven through 22 procedural viewmodel frames.",
            ],
            role="First-person viewmodel for Whack-a-Mole (bonks enemies to 45% size).",
        ),
        dict(
            id="v_paddle",
            name="Rally Master Paddle (Viewmodel)",
            cat="adapted",
            status="active",
            file="progs/v_paddle.md3",
            script="source/mm_tools/build_fungun_viewmodels.py",
            path=os.path.join(PROGS, "v_paddle.md3"),
            gain=1.85,
            az=2.6,
            el=0.2,
            pov=True,
            frame_names=vm22_names(),
            summary="Table-tennis paddle posed in eye space and animated with 22 idle-sway and serve-swing frames.",
            how=[
                "Adapted from SimReady wood/rubber paddle and animated across 22 first-person frames in build_fungun_viewmodels.py.",
            ],
            role="First-person viewmodel for the Rally Master ricochet ping-pong gun.",
        ),
        dict(
            id="v_robrocket",
            name="Rob Rocket Bazooka (Viewmodel)",
            cat="adapted",
            status="archived",
            file="source/mm_tools/out/fungun/progs/v_robrocket.md3",
            script="source/mm_tools/build_fungun_viewmodels.py",
            path=os.path.join(HERE, "out", "fungun", "progs", "v_robrocket.md3"),
            gain=1.7,
            az=2.45,
            el=0.2,
            pov=True,
            frame_names=vm22_names(),
            summary="Bazooka launcher rigged with 22 procedural idle/recoil frames in the fun-gun build output.",
            how=[
                "Built by an earlier fun-gun pass of build_fungun_viewmodels.py into source/mm_tools/out/fungun/progs/.",
            ],
            role="Archived fun-gun bazooka viewmodel prototype.",
        ),
        dict(
            id="g_srifle",
            name="Hand-Stripped Sniper Pickup",
            cat="adapted",
            status="active",
            file="progs/g_srifle.mdl",
            script="source/mm_tools/build_srifle.py",
            path=os.path.join(PROGS, "g_srifle.mdl"),
            gain=1.75,
            az=0.7,
            el=0.22,
            summary="Team Fortress 2.8 sniper rifle with the player's hand surgically removed via connected-component UV voting.",
            how=[
                "build_srifle.py finds connected triangle components of TF's v_srifle.mdl and excises the hand mesh by skin-palette color voting, then centers the bare rifle.",
            ],
            role="Spinning floor weapon pickup for the Sniper Rifle (sniper.qc).",
        ),
        dict(
            id="p_srifle",
            name="Third-Person Sniper Rifle Rig",
            cat="adapted",
            status="active",
            file="progs/p_srifle.md3",
            script="source/mm_tools/build_srifle.py",
            path=os.path.join(PROGS, "p_srifle.md3"),
            gain=1.75,
            az=0.65,
            el=0.22,
            summary="Hand-stripped Sniper Rifle rigidly transformed onto all 259 Quake 1.5 third-person player weapon poses.",
            how=[
                "Converts g_srifle's mesh + palette skin to MD3/PNG and rides p_shot.md3's 259 rigid hand transforms.",
            ],
            role="Exterior Sniper Rifle visible in players' hands during multiplayer.",
        ),
    ]


def main():
    catalog = build_catalog()
    models_out = []
    for idx, spec in enumerate(catalog):
        if spec.get("in_memory_md3") is not None or spec["path"].endswith(".md3"):
            baked = bake_md3(spec)
        else:
            baked = bake_mdl(spec)

        for k in ("id", "name", "cat", "status", "file", "script", "gain", "az", "el",
                  "pov", "defaultPov", "animFps", "turntable16", "swayOnly", "defaultClipName", "presets", "summary", "how", "role"):
            if k in spec and spec[k] is not None:
                baked[k] = spec[k]
        baked["order"] = idx
        models_out.append(baked)
        print(
            f"[{idx + 1:2d}/{len(catalog)}] {baked['id']:16s} ({baked['kind'].upper()}) "
            f"surfs={baked['nsurfs']:2d} nv={baked['nv']:5d} nt={baked['nt']:5d} nf={baked['nf']:3d}"
            f"{' [rigid]' if baked.get('rigid') else ''}"
        )

    gz_bin = gzip.compress(bytes(BIN), compresslevel=9)
    bin_b64 = base64.b64encode(gz_bin).decode("ascii")
    print(
        f"\nBinary geometry arena: raw={len(BIN) / 1e6:.2f} MB -> gzip={len(gz_bin) / 1e6:.2f} MB "
        f"(base64={len(bin_b64) / 1e6:.2f} MB), textures={len(TEX_LIST)}"
    )

    payload = dict(
        anorm=[round(float(x), 4) for x in ANORM],
        binGz=bin_b64,
        binLen=len(BIN),
        textures=TEX_LIST,
        models=models_out,
    )

    tpl = open(TEMPLATE, encoding="utf-8").read()
    assert tpl.count("/*__GALLERY_DATA__*/null") == 1, "Template placeholder missing"
    html = tpl.replace("/*__GALLERY_DATA__*/null", json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT} ({os.path.getsize(OUT) / 1e6:.2f} MB)")

    # Also emit lightweight standalone full-screen viewers for individual showcase models
    import copy

    def write_standalone(model_id, filename):
        src = next((m for m in models_out if m["id"] == model_id), None)
        if src is None:
            return
        one = copy.deepcopy(src)
        sub_bin = bytearray()
        sub_tex = []
        tex_remap = {}

        def remap_buf(ref):
            while len(sub_bin) & 3:
                sub_bin.append(0)
            off, ln = ref
            new_off = len(sub_bin)
            sub_bin.extend(BIN[off:off + ln])
            return [new_off, ln]

        if "rigidMats" in one:
            one["rigidMats"] = remap_buf(one["rigidMats"])
        for bk in ("vmap", "pos", "nrm"):
            if bk in one and isinstance(one[bk], list):
                one[bk] = remap_buf(one[bk])
        for s in one["surfaces"]:
            for bk in ("tris", "edges", "uv", "xyz", "nrm"):
                if bk in s:
                    s[bk] = remap_buf(s[bk])
            new_tids = []
            for tid in s["shader"]["tex"]:
                if tid not in tex_remap:
                    tex_remap[tid] = len(sub_tex)
                    sub_tex.append(TEX_LIST[tid])
                new_tids.append(tex_remap[tid])
            s["shader"]["tex"] = new_tids
        one["order"] = 0

        one_gz = gzip.compress(bytes(sub_bin), compresslevel=9)
        one_payload = dict(
            anorm=[round(float(x), 4) for x in ANORM],
            binGz=base64.b64encode(one_gz).decode("ascii"),
            binLen=len(sub_bin),
            textures=sub_tex,
            models=[one],
            standalone=dict(id=model_id, galleryHref=os.path.basename(OUT), totalCount=len(models_out)),
        )
        out_p = os.path.join(MOD, filename)
        out_html = tpl.replace("/*__GALLERY_DATA__*/null", json.dumps(one_payload, separators=(",", ":"), ensure_ascii=False))
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(out_html)
        print(f"Wrote {out_p} ({os.path.getsize(out_p) / 1e6:.2f} MB)")

    write_standalone("jetpack", "jetpack.html")
    write_standalone("bigears", "bigears_head.html")
    write_standalone("v_laptop", "laptop_gun.html")


if __name__ == "__main__":
    main()
