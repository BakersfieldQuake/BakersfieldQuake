"""Builds fanpage/assets/models_data.js for the BakersfieldQuake 90s GeoCities fanpage!
Packs ONLY 42 100% active, verified in-game 3D models (.md3, .mdl) and 360° multi-angle sprites (.spr32 / shader PNGs)
directly from bakersfield.pk3, cross-checked against progs.dat / csprogs.dat / maps/*.bsp!

Zero prototypes, zero removed guns, zero disabled roster entries:
  - Raunchy (8): v_milky, pinklady_spr, milksplat, skyveh_v3, v_pickle, pickle_diva (all 4 skins!), pickle_bomb, pink_supercar
  - Wheelman (4): v_wewcannon (5 CRT skins), wheelman_spr, wheelman_dance_spr (8 dances), wc_bar
  - Mega Man (5): v_megaman, megaman (+ EF_BLUE Blue Shell skin), mm_explode, mm_wheel, mm_rig (Room 120A Shrine)
  - Gore & Chasers (9): floathead, v_robdob, grenade_jw, ltg_head (24-angle Laptop drone), scissors_spr (#11),
                        bryan_spr (#17), finger_spr (#22), mrdiy_spr (#21), veh_van_wreck
  - LAN Arsenal & World (16): v_mysterybox, proj_mysterybox, lan_friends_spr (#18 Dennis / #19 Paul / #20 QuakeGuy),
                              jesskart_spr (#10), ltg_v3d (Key 4 3D Laptop), v_googun, goo_blob, ccc_proj (Key 8 CCC),
                              v_hammer (255f), v_netsend, netsend_pc (+ arcs), veh_van (3 skins), jetpack, aura,
                              gw_horse (Casino Bronze Horse), bk_trashcan (Rocket Park Trashcan)
"""
import base64
import glob
import gzip
import io
import json
import math
import os
import struct
import zipfile
import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
COMBAT_ROOT = os.path.abspath(os.path.join(MOD_ROOT, ".."))
DEV_ROOT = os.path.join(COMBAT_ROOT, "_bakersfield_dev")
OUT_ROOT = os.path.join(HERE, "out")
PK3_PATH = os.path.join(MOD_ROOT, "bakersfield.pk3")
PAK0_PATH = os.path.join(COMBAT_ROOT, "id1", "pak0.pak")
ANORM_JSON = os.path.join(COMBAT_ROOT, "monster_page", "anorm.json")
ASSETS_OUT = os.path.join(MOD_ROOT, "fanpage", "assets", "models_data.js")

os.makedirs(os.path.dirname(ASSETS_OUT), exist_ok=True)

PK3 = zipfile.ZipFile(PK3_PATH, "r")
PK3_SET = set(PK3.namelist())
PK3_LOWER = {n.lower(): n for n in PK3_SET}

# Build ground-truth blob of progs.dat + csprogs.dat + maps/*.bsp entity lumps to verify EVERY model!
ACTIVE_BIN_BLOBS = [
    open(os.path.join(MOD_ROOT, "progs.dat"), "rb").read(),
    open(os.path.join(MOD_ROOT, "csprogs.dat"), "rb").read(),
]
for bsp_p in glob.glob(os.path.join(MOD_ROOT, "maps", "*.bsp")):
    d_bsp = open(bsp_p, "rb").read()
    o0, l0 = struct.unpack("<2i", d_bsp[4:12])
    ACTIVE_BIN_BLOBS.append(d_bsp[o0:o0 + l0])


def assert_active_ingame_model(pk3_rel):
    norm = pk3_rel.replace("\\", "/").lstrip("/")
    assert norm in PK3_SET or norm.lower() in PK3_LOWER, f"Model NOT in bakersfield.pk3: {norm}"
    needle = norm.encode("ascii")
    assert any(needle in blob for blob in ACTIVE_BIN_BLOBS), f"Model NOT referenced in progs.dat/csprogs.dat/maps/*.bsp: {norm}"


def load_palette():
    with open(PAK0_PATH, "rb") as f:
        ident, ofs, length = struct.unpack("<4sii", f.read(12))
        f.seek(ofs)
        raw = f.read(length)
        for i in range(0, length, 64):
            nm = raw[i:i + 56].split(b"\0", 1)[0].decode("ascii", "replace").lower()
            pos, _ = struct.unpack("<ii", raw[i + 56:i + 64])
            if nm == "gfx/palette.lmp":
                f.seek(pos)
                return np.frombuffer(f.read(768), dtype=np.uint8).reshape((256, 3))
    raise RuntimeError("Missing gfx/palette.lmp")


PALETTE_U8 = load_palette()
ANORMS = np.array(json.load(open(ANORM_JSON, "r", encoding="utf-8")), dtype=np.float32).reshape((-1, 3))


def read_asset_bytes(rel_or_abs):
    """Read asset from bakersfield.pk3 first (authoritative shipped game archive!), with texture fallback if needed."""
    norm = rel_or_abs.replace("\\", "/").lstrip("/")
    if norm in PK3_SET:
        return PK3.read(norm)
    if norm.lower() in PK3_LOWER:
        return PK3.read(PK3_LOWER[norm.lower()])
    if os.path.isfile(rel_or_abs):
        return open(rel_or_abs, "rb").read()
    p_mod = os.path.join(MOD_ROOT, norm)
    if os.path.isfile(p_mod):
        return open(p_mod, "rb").read()
    raise FileNotFoundError(f"Asset not found in bakersfield.pk3 or mod dir: {rel_or_abs}")


def open_asset_image(rel_or_abs):
    raw = read_asset_bytes(rel_or_abs)
    im = Image.open(io.BytesIO(raw))
    im.load()
    return im


def try_find_tex_image(shader_name, hint_dirs=()):
    base = shader_name.replace("\\", "/").lstrip("/")
    stem = os.path.splitext(base)[0] if base.lower().endswith((".png", ".tga", ".jpg", ".webp")) else base
    short = os.path.basename(stem)
    candidates = []
    for ext in (".png", ".tga", ".jpg"):
        candidates.append(stem + ext)
        candidates.append("progs/" + short + ext)
        candidates.append("textures/" + short + ext)
        for hd in hint_dirs:
            candidates.append(os.path.join(hd, short + ext))
    for c in candidates:
        try:
            return open_asset_image(c), c
        except FileNotFoundError:
            continue
    return None, None


class FanpagePacker:
    def __init__(self):
        self.buf = bytearray()
        self.tex_list = []
        self.tex_map = {}

    def add_bytes(self, b):
        pad = (-len(self.buf)) & 3
        if pad:
            self.buf.extend(b"\x00" * pad)
        off = len(self.buf)
        self.buf.extend(b)
        return [off, len(b)]

    def add_tex_pil(self, cache_key, label, im, max_dim=512, quality=83, force_png=False, nearest=False, wrap=False, lift=1.0):
        if cache_key in self.tex_map:
            return self.tex_map[cache_key]
        im = im.convert("RGBA")
        if abs(lift - 1.0) > 1e-3:
            r, g, b, a = im.split()
            rgb = ImageEnhance.Brightness(Image.merge("RGB", (r, g, b))).enhance(lift)
            im = Image.merge("RGBA", (*rgb.split(), a))
        alpha_ext = im.getchannel("A").getextrema()
        has_alpha = alpha_ext[0] < 250
        w0, h0 = im.size
        if max_dim and max(w0, h0) > max_dim:
            sc = max_dim / float(max(w0, h0))
            im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))),
                           Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
        w, h = im.size
        bio = io.BytesIO()
        if force_png or nearest or max(w, h) <= 64:
            im.save(bio, "PNG", optimize=True)
            mime = "image/png"
        else:
            im.save(bio, "WEBP", quality=quality, method=4)
            mime = "image/webp"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[cache_key] = idx
        self.tex_list.append(dict(
            key=label, w=w, h=h, uri=uri, alpha=bool(has_alpha),
            nearest=bool(nearest), noMip=False, wrap=bool(wrap),
            cols=1, rows=1, tileW=w, tileH=h, pad=0, count=1,
        ))
        return idx

    def add_tex(self, rel_or_abs, max_dim=512, quality=83, force_png=False, nearest=False, wrap=False, lift=1.0):
        ck = ("tex", rel_or_abs, max_dim, force_png, nearest, wrap, round(lift, 2))
        if ck in self.tex_map:
            return self.tex_map[ck]
        im = open_asset_image(rel_or_abs)
        return self.add_tex_pil(ck, os.path.basename(rel_or_abs), im, max_dim=max_dim,
                                quality=quality, force_png=force_png, nearest=nearest, wrap=wrap, lift=lift)

    def add_atlas(self, atlas_id, frames_pil, max_tile_dim=176, pad=2, quality=82, nearest=False):
        ck = ("atlas", atlas_id)
        if ck in self.tex_map:
            return self.tex_map[ck]
        n = len(frames_pil)
        mw0 = max(im.size[0] for im in frames_pil)
        mh0 = max(im.size[1] for im in frames_pil)
        sc = min(1.0, max_tile_dim / float(max(mw0, mh0))) if max_tile_dim else 1.0
        tw, th = max(1, round(mw0 * sc)), max(1, round(mh0 * sc))
        cols = max(1, int(math.ceil(math.sqrt(n * (th / float(max(1, tw)))))))
        rows = int(math.ceil(n / float(cols)))
        while max(cols * (tw + 2 * pad), rows * (th + 2 * pad)) > 3900 and max(tw, th) > 32:
            tw = max(16, int(tw * 0.85))
            th = max(16, int(th * 0.85))
            cols = max(1, int(math.ceil(math.sqrt(n * (th / float(max(1, tw)))))))
            rows = int(math.ceil(n / float(cols)))
        cw, ch = tw + 2 * pad, th + 2 * pad
        aw, ah = cols * cw, rows * ch
        atlas_np = np.zeros((ah, aw, 4), dtype=np.uint8)
        resample = Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS
        for idx_f, im0 in enumerate(frames_pil):
            im_rgba = im0.convert("RGBA")
            if im_rgba.size != (tw, th):
                if im_rgba.size != (mw0, mh0):
                    canvas = Image.new("RGBA", (mw0, mh0), (0, 0, 0, 0))
                    canvas.paste(im_rgba, ((mw0 - im_rgba.width) // 2, (mh0 - im_rgba.height) // 2))
                    im_rgba = canvas
                im_rgba = im_rgba.resize((tw, th), resample)
            arr = np.asarray(im_rgba, dtype=np.uint8)
            padded = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge") if pad > 0 else arr
            c, r = idx_f % cols, idx_f // cols
            atlas_np[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = padded
        bio = io.BytesIO()
        Image.fromarray(atlas_np, "RGBA").save(bio, "WEBP", quality=quality, method=4)
        uri = "data:image/webp;base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[ck] = idx
        self.tex_list.append(dict(
            key=atlas_id, w=aw, h=ah, uri=uri, alpha=True, nearest=bool(nearest),
            noMip=True, wrap=False, cols=cols, rows=rows, tileW=tw, tileH=th, pad=pad, count=n,
        ))
        return idx


def build_wire_edges(tri_u16):
    if len(tri_u16) == 0:
        return np.zeros((0, 2), dtype="<u2")
    e01 = np.sort(tri_u16[:, [0, 1]], axis=1)
    e12 = np.sort(tri_u16[:, [1, 2]], axis=1)
    e20 = np.sort(tri_u16[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


def encode_surface(packer, sname, shader, uv_arr, tri_arr, all_v, all_n, mat):
    nf, nv, _ = all_v.shape
    uv_f32 = np.asarray(uv_arr, dtype="<f4")
    tri_arr = np.asarray(tri_arr, dtype=np.int32)
    if len(tri_arr) > 0 and nv > 0:
        v0 = all_v[0]
        n0 = all_n[0]
        fn = np.cross(v0[tri_arr[:, 1]] - v0[tri_arr[:, 0]], v0[tri_arr[:, 2]] - v0[tri_arr[:, 0]])
        avg_n = n0[tri_arr[:, 0]] + n0[tri_arr[:, 1]] + n0[tri_arr[:, 2]]
        score = float(np.sum(fn * avg_n))
        tri_ccw = (tri_arr[:, [0, 2, 1]] if score < 0.0 else tri_arr).astype("<u2")
    else:
        tri_ccw = tri_arr.astype("<u2")
    edges_u16 = build_wire_edges(tri_ccw)
    nt = len(tri_ccw)

    max_abs = float(np.max(np.abs(all_v))) if all_v.size else 1.0
    inv_scale = 64.0 if max_abs < 500.0 else (32000.0 / max(max_abs, 1.0))
    pos_scale = 1.0 / inv_scale

    pos_i16 = np.zeros((nf, nv, 4), dtype="<i2")
    pos_i16[:, :, :3] = np.clip(np.round(all_v * inv_scale), -32767, 32767).astype("<i2")
    dpos = pos_i16.copy()
    if nf > 1:
        dpos[1:] = ((pos_i16[1:].astype(np.int32) - pos_i16[:-1].astype(np.int32)) & 0xFFFF).astype("<u2").view("<i2")

    n_len = np.maximum(np.linalg.norm(all_n, axis=2, keepdims=True), 1e-8)
    nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
    nrm_i8[:, :, :3] = np.clip(np.round((all_n / n_len) * 127.0), -127, 127).astype("<i1")
    dnrm = nrm_i8.copy()
    if nf > 1:
        dnrm[1:] = ((nrm_i8[1:].astype(np.int32) - nrm_i8[:-1].astype(np.int32)) & 0xFF).astype("<u1").view("<i1")

    return dict(
        name=sname, shader=shader, nv=int(nv), nt=int(nt), ne=int(len(edges_u16)),
        nfGeom=int(nf), posScale=float(pos_scale),
        tris=packer.add_bytes(tri_ccw.tobytes()),
        edges=packer.add_bytes(edges_u16.tobytes()),
        uv=packer.add_bytes(uv_f32.tobytes()),
        pos=packer.add_bytes(dpos.tobytes()),
        nrm=packer.add_bytes(dnrm.tobytes()),
        tex=int(mat.get("tex", -1)),
        glowTex=int(mat.get("glowTex", -1)),
        animFps=float(mat.get("animFps", 0.0)),
        animOrder=mat.get("animOrder"),
        scrollV=float(mat.get("scrollV", 0.0)),
        metallic=float(mat.get("metallic", 0.18)),
        roughness=float(mat.get("roughness", 0.48)),
        spec=float(mat.get("spec", 0.42)),
        unlit=1 if mat.get("unlit") else 0,
        additive=1 if mat.get("additive") else 0,
        alphaTest=1 if mat.get("alphaTest") else 0,
        alphaBlend=1 if mat.get("alphaBlend") else 0,
        billboard=int(mat.get("billboard", 0)),
    )


def read_md3_bytes(raw):
    assert raw[:4] == b"IDP3"
    nf, ntags, nsurfs, nskins, ofs_frames, ofs_tags, ofs_surfs, _ = struct.unpack_from("<8i", raw, 76)
    fnames = []
    for i in range(nf):
        nm = raw[ofs_frames + i * 56 + 40: ofs_frames + i * 56 + 56].split(b"\0", 1)[0].decode("latin1")
        fnames.append(nm or f"f{i}")
    surfs = []
    pos = ofs_surfs
    for _ in range(nsurfs):
        assert raw[pos:pos + 4] == b"IDP3"
        sname = raw[pos + 4:pos + 68].split(b"\0", 1)[0].decode("latin1")
        flags, s_nf, s_nsh, nv, nt, otris, osh, ost, oxyz, oend = struct.unpack_from("<10i", raw, pos + 68)
        shader = ""
        if s_nsh > 0:
            shader = raw[pos + osh: pos + osh + 64].split(b"\0", 1)[0].decode("latin1")
        tris = np.frombuffer(raw, dtype="<i4", count=nt * 3, offset=pos + otris).reshape((nt, 3))
        st = np.frombuffer(raw, dtype="<f4", count=nv * 2, offset=pos + ost).reshape((nv, 2))
        xyzn = np.frombuffer(raw, dtype="<i2", count=s_nf * nv * 4, offset=pos + oxyz).reshape((s_nf, nv, 4))
        all_v = xyzn[:, :, :3].astype(np.float32) / 64.0
        n_u8 = np.ascontiguousarray(xyzn[:, :, 3]).view(np.uint8).reshape((s_nf, nv, 2))
        lat = n_u8[:, :, 0].astype(np.float32) * (2.0 * math.pi / 255.0)
        lng = n_u8[:, :, 1].astype(np.float32) * (2.0 * math.pi / 255.0)
        sin_lng = np.sin(lng)
        all_n = np.stack([sin_lng * np.cos(lat), sin_lng * np.sin(lat), np.cos(lng)], axis=-1).astype(np.float32)
        surfs.append(dict(name=sname, shader=shader, st=st, tris=tris, all_v=all_v, all_n=all_n))
        pos += oend
    return dict(nframes=nf, frame_names=fnames, surfaces=surfs)


def pack_md3(packer, pk3_rel_path, meta, surf_mats=None, hint_dirs=(), frame_stride=1, max_dim=512, lift=1.22, extra_surfs=None):
    assert_active_ingame_model(pk3_rel_path)
    raw = read_asset_bytes(pk3_rel_path)
    m = read_md3_bytes(raw)
    surf_mats = surf_mats or {}
    if frame_stride > 1 and m["nframes"] > frame_stride:
        keep = list(range(0, m["nframes"], frame_stride))
        m["nframes"] = len(keep)
        m["frame_names"] = [m["frame_names"][i] for i in keep]
        for s in m["surfaces"]:
            if len(s["all_v"]) > frame_stride:
                s["all_v"] = s["all_v"][keep]
                s["all_n"] = s["all_n"][keep]

    nf = m["nframes"]
    surfs_out = []
    tot_v, tot_t = 0, 0
    solid_pts = []
    for s in m["surfaces"]:
        sn, sh = s["name"], s["shader"]
        tot_v += len(s["st"])
        tot_t += len(s["tris"])
        mat = surf_mats.get(sn) or surf_mats.get(sh)
        if mat is None:
            im, found_p = try_find_tex_image(sh or sn, hint_dirs=hint_dirs)
            is_fx = any(k in (sn + sh).lower() for k in ("fx", "zap", "flash", "arc", "plume", "aura"))
            is_unlit = is_fx or any(k in (sn + sh).lower() for k in ("glow", "scr", "crt", "led", "dial", "core"))
            if im is not None:
                tid = packer.add_tex_pil(("auto", found_p, max_dim, round(lift, 2)), os.path.basename(found_p), im,
                                         max_dim=max_dim, force_png=is_fx, lift=1.0 if is_unlit else lift)
                has_a = packer.tex_list[tid]["alpha"]
            else:
                tid = -1
                has_a = False
            mat = dict(tex=tid, unlit=is_unlit, additive=is_fx, alphaTest=has_a and not is_fx)
        if not mat.get("additive"):
            for fi in range(min(nf, 6)):
                vv = s["all_v"][min(fi, len(s["all_v"]) - 1)]
                if not np.allclose(vv, 0.0):
                    solid_pts.append(vv)
        surfs_out.append(encode_surface(packer, sn, sh, s["st"], s["tris"], s["all_v"], s["all_n"], mat))

    if extra_surfs:
        for es in extra_surfs:
            surfs_out.append(es)
            tot_v += es["nv"]
            tot_t += es["nt"]

    pts = np.vstack(solid_pts) if solid_pts else m["surfaces"][0]["all_v"][0]
    bmin = pts.min(axis=0).round(2).tolist()
    bmax = pts.max(axis=0).round(2).tolist()
    clips = meta.get("clips") or [dict(id="all", label=f"Play ({nf}f)", start=0, count=nf, fps=meta.get("fps", 12.0))]
    out = dict(fmt="MD3", nf=int(nf), nv=int(tot_v), nt=int(tot_t), bbox=[bmin, bmax], surfaces=surfs_out, clips=clips)
    out.update(meta)
    return out


def pack_mdl(packer, pk3_path, meta, skin_labels=None):
    assert_active_ingame_model(pk3_path)
    raw = read_asset_bytes(pk3_path)
    ident, ver = struct.unpack_from("<4si", raw, 0)
    assert ident == b"IDPO" and ver == 6
    scale = struct.unpack_from("<3f", raw, 8)
    origin = struct.unpack_from("<3f", raw, 20)
    _, _, _, _, nskins, sw, sh, nverts, ntris, nframes, _, _, _ = struct.unpack_from("<f3f8if", raw, 32)
    pos = 84
    skins8 = []
    for _ in range(nskins):
        stype = struct.unpack_from("<i", raw, pos)[0]
        pos += 4
        if stype == 0:
            skins8.append(np.frombuffer(raw, np.uint8, sw * sh, pos).reshape((sh, sw)))
            pos += sw * sh
        else:
            ng = struct.unpack_from("<i", raw, pos)[0]
            pos += 4 + ng * 4
            for sub in range(ng):
                if sub == 0:
                    skins8.append(np.frombuffer(raw, np.uint8, sw * sh, pos).reshape((sh, sw)))
                pos += sw * sh
    st_raw = np.frombuffer(raw, dtype="<i4", count=nverts * 3, offset=pos).reshape((nverts, 3))
    pos += nverts * 12
    tris_raw = np.frombuffer(raw, dtype="<i4", count=ntris * 4, offset=pos).reshape((ntris, 4))
    pos += ntris * 16
    frames_v, frames_n, fnames = [], [], []
    for _ in range(nframes):
        ftype = struct.unpack_from("<i", raw, pos)[0]
        pos += 4
        if ftype != 0:
            ng = struct.unpack_from("<i", raw, pos)[0]
            pos += 4 + 8 + ng * 4
        else:
            ng = 1
        for sub in range(ng):
            pos += 8
            nm = raw[pos:pos + 16].split(b"\0", 1)[0].decode("latin1")
            pos += 16
            v4 = np.frombuffer(raw, np.uint8, nverts * 4, pos).reshape((nverts, 4))
            pos += nverts * 4
            if sub == 0:
                fnames.append(nm)
                xyz = v4[:, :3].astype(np.float32) * np.array(scale, np.float32) + np.array(origin, np.float32)
                nrm = ANORMS[np.minimum(v4[:, 3].astype(np.int32), len(ANORMS) - 1)]
                frames_v.append(xyz)
                frames_n.append(nrm)

    v_map = {}
    uv_list = []
    remap_idx = []
    for t_i in range(ntris):
        front = tris_raw[t_i, 0]
        tri_out = []
        for k in range(3):
            vi = int(tris_raw[t_i, 1 + k])
            onseam = int(st_raw[vi, 0])
            s_px, t_px = float(st_raw[vi, 1]), float(st_raw[vi, 2])
            if not front and onseam:
                s_px += sw * 0.5
            key = (vi, int(round(s_px * 2)))
            if key not in v_map:
                v_map[key] = (len(uv_list), vi)
                uv_list.append(((s_px + 0.5) / sw, (t_px + 0.5) / sh))
            tri_out.append(v_map[key][0])
        remap_idx.append(tri_out)

    src_vis = [vi for _, vi in sorted(v_map.values(), key=lambda x: x[0])]
    all_v = np.stack([fv[src_vis] for fv in frames_v], axis=0)
    all_n = np.stack([fn[src_vis] for fn in frames_n], axis=0)
    uv_arr = np.array(uv_list, dtype=np.float32)
    tri_arr = np.array(remap_idx, dtype=np.int32)

    tids = []
    for si in range(4):
        try:
            im_tga = open_asset_image(f"{pk3_path}_{si}.tga")
            tids.append(packer.add_tex_pil(("mdl_tga", pk3_path, si), f"{os.path.basename(pk3_path)}_{si}", im_tga, max_dim=512))
        except FileNotFoundError:
            pass
    if not tids:
        for si, s8 in enumerate(skins8):
            im8 = Image.fromarray(PALETTE_U8[s8], "RGB")
            tids.append(packer.add_tex_pil(("mdl_8", pk3_path, si), f"{os.path.basename(pk3_path)}_s{si}", im8, max_dim=512, force_png=True, nearest=True))

    skins = []
    if len(tids) > 1:
        for si, tid in enumerate(tids):
            lbl = skin_labels[si] if (skin_labels and si < len(skin_labels)) else f"Skin {si + 1}"
            skins.append(dict(label=lbl, map={"mdl_body": dict(tex=tid)}))

    s_enc = encode_surface(packer, "mdl_body", pk3_path, uv_arr, tri_arr, all_v, all_n, dict(tex=tids[0]))
    idle_i = [i for i, nm in enumerate(fnames) if nm != "gone"][:12] or [0]
    pts = all_v[idle_i].reshape((-1, 3))
    nf = len(frames_v)
    clips = meta.get("clips") or [dict(id="all", label=f"Play ({nf}f)", start=0, count=nf, fps=10.0)]
    out = dict(fmt="MDL", nf=nf, nv=s_enc["nv"], nt=s_enc["nt"], bbox=[pts.min(0).round(2).tolist(), pts.max(0).round(2).tolist()],
               surfaces=[s_enc], clips=clips)
    if skins:
        out["skins"] = skins
    out.update(meta)
    return out


def make_quad_surf(packer, sname, tid, hw=28.0, hh=58.0, pov_hand=False, anim_fps=0.0, anim_order=None):
    if pov_hand:
        vq = [[16.0, +13.5, -13.5], [16.0, +13.5, +3.0], [16.0, -13.5, +3.0], [16.0, -13.5, -13.5]]
        bb = 0
    else:
        vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
        bb = 1
    nq = [[-1.0, 0.0, 0.0]] * 4
    uv = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], dtype="<f4")
    tris = np.array([[0, 2, 1], [0, 3, 2]], dtype=np.int32)
    return encode_surface(packer, sname, sname, uv, tris, np.asarray(vq, np.float32)[None, :, :],
                          np.asarray(nq, np.float32)[None, :, :],
                          dict(tex=tid, animFps=anim_fps, animOrder=anim_order, unlit=True, alphaTest=True, alphaBlend=True, billboard=bb))


def read_spr32_subset(pk3_name, frame_indices):
    assert_active_ingame_model(pk3_name)
    raw = read_asset_bytes(pk3_name)
    ident, ver, stype, rad, maxw, maxh, nframes, beam, sync = struct.unpack_from("<4siiifiiii", raw, 0)
    assert ident == b"IDSP" and ver == 32
    pos = 36
    want = set(frame_indices)
    got = {}
    for fi in range(nframes):
        ft = struct.unpack_from("<i", raw, pos)[0]
        pos += 4
        assert ft == 0
        ox, oy, w, h = struct.unpack_from("<4i", raw, pos)
        pos += 16
        nb = w * h * 4
        if fi in want:
            got[fi] = Image.frombytes("RGBA", (w, h), raw[pos:pos + nb])
        pos += nb
        if len(got) == len(want):
            break
    return [got[i] for i in frame_indices]


def pack_turnaround_sprite(packer, model_id, cat, badge, title, file_lbl, desc, clips_pil_and_meta, skins_pil=None, hw=28.0, hh=58.0, turn_dirs=8, max_tile=168):
    all_imgs = []
    clips_out = []
    for cid, clabel, dirs, fpd, fps, imgs in clips_pil_and_meta:
        base = len(all_imgs)
        all_imgs.extend(imgs)
        clips_out.append(dict(id=cid, label=clabel, start=0, count=fpd, fps=fps,
                              sprMode=dict(base=base, dirs=dirs, fpd=fpd, fps=fps)))
    tid0 = packer.add_atlas(f"spr_{model_id}", all_imgs, max_tile_dim=max_tile, pad=2, quality=82)
    s_enc = make_quad_surf(packer, "spr_card", tid0, hw=hw, hh=hh)
    out = dict(
        id=model_id, cat=cat, fmt="SPR32", badge=badge, title=title, file=file_lbl, desc=desc,
        nf=len(all_imgs), nv=4, nt=2, bbox=[[-hw, -hw, 0.0], [hw, hw, hh]],
        isSprite=True, turnDirs=turn_dirs, turnSign=-1, surfaces=[s_enc], clips=clips_out,
    )
    if skins_pil:
        skins_out = []
        for si, (slabel, simgs) in enumerate(skins_pil):
            stid = tid0 if si == 0 else packer.add_atlas(f"spr_{model_id}_sk{si}", simgs, max_tile_dim=max_tile, pad=2, quality=82)
            skins_out.append(dict(label=slabel, map={"spr_card": dict(tex=stid)}))
        out["skins"] = skins_out
    return out


def main():
    packer = FanpagePacker()
    models = []

    print("[1/5] Packing RAUNCHY & MILKY Active In-Game Assets (8)...")
    # 1. Milky Viewmodel (progs/v_milky.md3 + milkyvm.shader)
    assert_active_ingame_model("progs/v_milky.md3")
    mvm_idle = [open_asset_image(f"progs/mvm_a_{k:02d}.png") for k in range(0, 38, 2)]
    mvm_idle = mvm_idle + mvm_idle[-2:0:-1]
    mvm_fire = [open_asset_image(f"progs/mvm_f_{k:02d}.png") for k in range(0, 56, 2)]
    tid_mvm_i = packer.add_atlas("milky_vm_idle", mvm_idle, max_tile_dim=216)
    tid_mvm_f = packer.add_atlas("milky_vm_fire", mvm_fire, max_tile_dim=216)
    models.append(dict(
        id="v_milky", cat="raunchy", fmt="2D SHADER", badge="KEY 5 · MILKY GUN",
        title="Milky Jug Gun (1st-Person Viewmodel)",
        file="progs/v_milky.md3 + milkyvm.shader",
        desc="Hurls a sloshing jug of milk that summons the 600-HP singing Pink Lady! Switch Skins to watch the 18fps Milk Jug Hurl.",
        nf=1, nv=4, nt=2, bbox=[[15, -13.5, -13.5], [17, 13.5, 3.0]],
        pov=True, defaultPov=True, az=3.14, el=0.05,
        surfaces=[make_quad_surf(packer, "card", tid_mvm_i, pov_hand=True, anim_fps=10.0)],
        skins=[
            dict(label="🥛 Sloshing Idle Sway", map={"card": dict(tex=tid_mvm_i, animFps=10.0)}),
            dict(label="💦 Hurl Milk Jug!", map={"card": dict(tex=tid_mvm_f, animFps=15.0)}),
        ],
        clips=[dict(id="hud", label="🥛 1st-Person HUD Loop", start=0, count=1, fps=10.0)],
    ))

    # 2. Pink Lady 16-Angle Turnaround + 34f Front Bounce (progs/pinklady.md3)
    assert_active_ingame_model("progs/pinklady.md3")
    pl_turn = [open_asset_image(f"progs/pinklady_{d:02d}.png") for d in range(16)]
    pl_b = [open_asset_image(f"progs/pinklady_b{k:02d}.png") for k in range(0, 36, 2)]
    pl_bpp = pl_b + pl_b[-2:0:-1]
    models.append(pack_turnaround_sprite(
        packer, "pinklady_spr", "raunchy", "600 HP · MILKS YOUR SCREEN",
        "Singing Pink Lady (16-Angle Spin + Bounce!)",
        "progs/pinklady.md3 + pinklady.shader",
        "Floats singing her song, stalks victims around corners via breadcrumbs, spurts milk when shot, and bursts for 320 DMG + white-out milk screen!",
        [
            ("bounce", "💖 Front Bounce Loop (34f)", 1, len(pl_bpp), 10.0, pl_bpp),
            ("turn16", "🔄 360° Turnaround (16 Angles)", 16, 1, 10.0, pl_turn),
        ],
        turn_dirs=16, max_tile=208,
    ))

    # 3. Milk Jug Explosion Floor/Wall Splatters (progs/milksplat.md3)
    msplat_mats = {
        f"splat{k}": dict(tex=packer.add_tex(f"progs/milksplat_{k}.png", max_dim=192, force_png=True), unlit=True, alphaBlend=True)
        for k in range(6)
    }
    models.append(pack_md3(
        packer, "progs/milksplat.md3",
        dict(id="milksplat", cat="raunchy", badge="6 SPLAT DECALS · WHITE-OUT",
             title="Milk Jug Explosion Floor/Wall Splatters (6 Variants)",
             file="progs/milksplat.md3",
             desc="Plasters walls, floors & ceilings in glossy white milk puddles every time the Milky Gun or Pink Lady bursts!",
             clips=[dict(id="splat", label="💦 6 Milk Splats Cluster", start=0, count=1, fps=2.0)]),
        surf_mats=msplat_mats,
    ))

    # 4. Pink Lady + Big-Ears Podracer Sky-Chariot (progs/skyveh_v3.md3 — active bk_cruiser cnt=2 in bklan4/5!)
    t_van = packer.add_tex("progs/veh_van_tex.png", max_dim=512)
    t_bigears = packer.add_tex("progs/skyveh_bigears.png", max_dim=512)
    t_pink_chariot = packer.add_tex("progs/skyveh_pinklady.png", max_dim=512)
    t_mm_chr = packer.add_tex("progs/mmw_chrome_axle.png", max_dim=384)
    t_mm_whl = packer.add_tex("progs/mmw_wheel.png", max_dim=384)
    t_sky_fx = packer.add_tex("progs/skyveh_fx.png", max_dim=256, force_png=True)
    models.append(pack_md3(
        packer, "progs/skyveh_v3.md3",
        dict(id="skyveh_v3", cat="raunchy", badge="RIDEABLE BKLAN CRUISER",
             title="Pink Lady & Big-Ears Sky-Chariot (bk_cruiser)",
             file="progs/skyveh_v3.md3",
             desc="Cruises across bklan4 & bklan5 (rideable on touch!): screaming Big-Ears tractor pods towing the 6-Man LAN Van under a spinning 3D Pink Lady autogyro!",
             clips=[dict(id="fly", label="🚁 Sky-Chariot Flight", start=0, count=8, fps=8.0)]),
        surf_mats={
            "progs/skyveh_van": dict(tex=t_van),
            "progs/skyveh_bigears": dict(tex=t_bigears),
            "progs/skyveh_pinklady": dict(tex=t_pink_chariot),
            "progs/skyveh_chrome": dict(tex=t_mm_chr, metallic=0.85, roughness=0.18, spec=0.92),
            "progs/skyveh_wheel": dict(tex=t_mm_whl),
            "progs/skyveh_fx": dict(tex=t_sky_fx, unlit=True, additive=True),
        },
        frame_stride=2,
    ))

    # 5. Held Pickle Surprise Fist (progs/v_pickle.md3)
    assert_active_ingame_model("progs/v_pickle.md3")
    pvm_frames = [open_asset_image(f"progs/pvm_{k:03d}.png") for k in range(0, 120, 4)]
    tid_pvm = packer.add_atlas("v_pickle_hud", pvm_frames, max_tile_dim=208)
    models.append(dict(
        id="v_pickle", cat="raunchy", fmt="2D SHADER", badge="KEY X · PICKLE SURPRISE",
        title="Held Pickle Surprise Fist (1st-Person)",
        file="progs/v_pickle.md3 + picklevm.shader",
        desc="Tosses a sticky gherkin that stands erect at 2x player height, waves like a car-lot tube man, screams 'PICKLE SURPRISE!' and explodes green!",
        nf=1, nv=4, nt=2, bbox=[[15, -13.5, -13.5], [17, 13.5, 3.0]],
        pov=True, defaultPov=True, az=3.14, el=0.05,
        surfaces=[make_quad_surf(packer, "card", tid_pvm, pov_hand=True, anim_fps=14.0)],
        clips=[dict(id="hud", label="🥒 Warty Pickle Sway & Throw", start=0, count=1, fps=14.0)],
    ))

    # 6. Erect Screaming Pickle Surprise 16-Angle Diva (progs/pickle.md3 + all 4 skins pkv_s0..s3!)
    assert_active_ingame_model("progs/pickle.md3")
    pk_skins = [
        ("🥒 Stage 1: Smirking Erect", [open_asset_image(f"progs/pkv_s0_v{v:02d}.png") for v in range(16)]),
        ("😮 Stage 2: Chanting Diva", [open_asset_image(f"progs/pkv_s1_v{v:02d}.png") for v in range(16)]),
        ("😫 Stage 3: Swelling Shriek", [open_asset_image(f"progs/pkv_s2_v{v:02d}.png") for v in range(16)]),
        ("😱 Stage 4: MAX PRE-BLAST SCREAM!", [open_asset_image(f"progs/pkv_s3_v{v:02d}.png") for v in range(16)]),
    ]
    models.append(pack_turnaround_sprite(
        packer, "pickle_diva", "raunchy", "2X MAN HEIGHT · 4 SKINS",
        "Erect Screaming Pickle Surprise (16-Angle Diva)",
        "progs/pickle.md3 + pickle.shader",
        "Sticks to floors/walls/players, stands erect at 2x player height, waves wildly & screams 'PICKLE SURPRISE!' Switch Skins for all 4 scream stages!",
        [("turn16", "🥒 360° Turntable (16 Angles)", 16, 1, 10.0, pk_skins[0][1])],
        skins_pil=pk_skins,
        hw=24.0, hh=72.0, turn_dirs=16, max_tile=184,
    ))

    # 7. Thrown 3D Warty Pickle Sticky Bomb (progs/pickle_bomb.md3)
    pk_faces = [open_asset_image(f"progs/pickle_face_{k:02d}.png") for k in range(8)]
    tid_pkb = packer.add_atlas("pickle_bomb_faces", pk_faces, max_tile_dim=192)
    models.append(pack_md3(
        packer, "progs/pickle_bomb.md3",
        dict(id="pickle_bomb", cat="raunchy", badge="3D WARTY GHERKIN",
             title="Thrown 3D Warty Pickle Sticky Bomb",
             file="progs/pickle_bomb.md3",
             desc="3D wart-displaced gherkin sticky bomb with animated wandering eyes before it sprouts into the 12-ft Diva!"),
        surf_mats={"progs/pickle_bombskin": dict(tex=tid_pkb, animFps=6.0)},
    ))

    # 8. "IT'S NOT PINK!" Exotic V12 Supercar (progs/pink_supercar.md3 — active bk_cruiser cnt=1 in bklan4/5!)
    t_psc = packer.add_tex("progs/pink_supercar_tex.png", max_dim=640, quality=86)
    t_psc_gl = packer.add_tex("progs/pink_supercar_tex_glow.png", max_dim=384)
    t_psc_gs = packer.add_tex("progs/pink_supercar_glass.png", max_dim=128, force_png=True)
    models.append(pack_md3(
        packer, "progs/pink_supercar.md3",
        dict(id="pink_supercar", cat="raunchy", badge='"IT\'S NOT PINK!!" · V12',
             title='"IT\'S NOT PINK!" Rideable V12 Supercar',
             file="progs/pink_supercar.md3",
             desc="Cruises around bklan4 & bklan5 blasting euro-club music & yelling 'IT'S NOT PINK!!'—hop on top to ride it! Features roof webcam, scissor doors & nitro boost.",
             clips=[
                 dict(id="doors", label="🦋 Open Scissor Doors & Hood", start=16, count=8, fps=6.0, lie=True),
                 dict(id="boost", label="🔥 V12 Nitro Flame Boost", start=24, count=8, fps=9.0),
                 dict(id="cam", label="📷 Roof Webcam Scan", start=0, count=8, fps=6.0, lie=True),
             ]),
        surf_mats={
            "progs/pink_supercar_tex": dict(tex=t_psc, glowTex=t_psc_gl, metallic=0.45, roughness=0.22, spec=0.85),
            "progs/pink_supercar_glass": dict(tex=t_psc_gs, alphaBlend=True),
        },
        frame_stride=2,
    ))

    print("[2/5] Packing WHEELMAN & WEW CANNON Active In-Game Assets (4)...")
    # 9. WEW CANNON (progs/v_wewcannon.md3)
    t_wew_sil = packer.add_tex("progs/wew_silver.png", max_dim=512, quality=86)
    t_wew_hnd = packer.add_tex("progs/wew_hand.png", max_dim=384)
    t_wew_cor = packer.add_tex("progs/wew_core.png", max_dim=256)
    t_wew_fx  = packer.add_tex("progs/wew_fx.png", max_dim=256, force_png=True)
    t_crt_all = packer.add_atlas("wew_crt_16", [open_asset_image(f"progs/wew_crt_{i:02d}.png") for i in range(16)], max_tile_dim=224)
    t_crt_0   = packer.add_tex("progs/wew_crt_00.png", max_dim=256)
    t_crt_4   = packer.add_tex("progs/wew_crt_04.png", max_dim=256)
    t_crt_8   = packer.add_tex("progs/wew_crt_08.png", max_dim=256)
    t_crt_12  = packer.add_tex("progs/wew_crt_12.png", max_dim=256)
    wew_mats = {
        "cannon_silver": dict(tex=t_wew_sil, metallic=0.90, roughness=0.18, spec=0.95),
        "ranger_hands": dict(tex=t_wew_hnd, metallic=0.15, roughness=0.55, spec=0.30),
        "cannon_core": dict(tex=t_wew_cor, unlit=True),
        "crt_screen": dict(tex=t_crt_all, animFps=2.5, unlit=True),
        "cannon_fx": dict(tex=t_wew_fx, unlit=True, additive=True),
    }
    models.append(pack_md3(
        packer, "progs/v_wewcannon.md3",
        dict(id="v_wewcannon", cat="wheelman", badge="KEY G · +58° BARREL BEND!",
             title='Super Giant Silver "WEW CANNON" (48f + Win98 CRT)',
             file="progs/v_wewcannon.md3",
             desc="Hold fire 1.5s: the silver barrel bends +58° and bulges +58% while its mounted Win98 CRT browses 90s sites—then WHIP-SNAPS a screaming Wheelman at 1200 u/s!",
             pov=True, az=2.38, el=0.24,
             skins=[
                 dict(label="🖥 Auto-Browse CRT", map={"crt_screen": dict(tex=t_crt_all, animFps=2.5)}),
                 dict(label="🌐 goodwebsites.html", map={"crt_screen": dict(tex=t_crt_0, animFps=0.0)}),
                 dict(label="🌐 zxc.cc", map={"crt_screen": dict(tex=t_crt_4, animFps=0.0)}),
                 dict(label="🌐 biblefirst.com", map={"crt_screen": dict(tex=t_crt_8, animFps=0.0)}),
                 dict(label="🌐 wxcs.com/rob", map={"crt_screen": dict(tex=t_crt_12, animFps=0.0)}),
             ],
             clips=[
                 dict(id="full", label="💥 Full +58° Bend, Blast & Whiplash (48f)", start=0, count=48, fps=13.0),
                 dict(id="bend", label="💪 Charge +58° Barrel Bend (10f)", start=16, count=10, fps=7.0),
                 dict(id="blast", label="🔥 Whip-Snap & S-Bend Recoil (14f)", start=26, count=14, fps=16.0),
                 dict(id="idle", label="⚙ Heavy Silver Idle Sway (16f)", start=0, count=16, fps=10.0),
             ]),
        surf_mats=wew_mats,
    ))

    # 10. Blasted Wheelman Projectile (progs/wheelman.spr32 — active flight banks in wcannon.qc!)
    wm_fire_idx = [648 + d * 6 + k for d in range(8) for k in (0, 2, 4)]
    wm_scrm_idx = [104 + d * 6 + k for d in range(8) for k in (0, 2, 4)]
    wm_driv_idx = [8 + d * 12 + k for d in range(8) for k in (0, 4, 8)]
    wm_lbar_idx = [696 + d * 6 + k for d in range(8) for k in (0, 2, 4)]
    wm_all_sub = read_spr32_subset("progs/wheelman.spr32", wm_fire_idx + wm_scrm_idx + wm_driv_idx + wm_lbar_idx)
    n24 = 24
    models.append(pack_turnaround_sprite(
        packer, "wheelman_spr", "wheelman", "1200 U/S · 185 SPLASH DMG",
        "Blasted Wheelman Projectile (Fire-Wheels / Scream / Long-Bar)",
        "progs/wheelman.spr32",
        "Screams down hallways at 1200 u/s, hops 18u steps, deals 60 direct + 185 splash DMG (aim down to Wheelman-Jump!!), and bursts into flying wheels, bars & gibs!",
        [
            ("fire", "🔥 Blazing Fire-Wheels (8-Dir)", 8, 3, 10.0, wm_all_sub[0:n24]),
            ("scream", "😱 Mid-Air Screaming (8-Dir)", 8, 3, 10.0, wm_all_sub[n24:2 * n24]),
            ("drive", "🛞 Full-Throttle Roll (8-Dir)", 8, 3, 10.0, wm_all_sub[2 * n24:3 * n24]),
            ("longbar", "📏 Extended Long-Bar Rig (8-Dir)", 8, 3, 10.0, wm_all_sub[3 * n24:4 * n24]),
        ],
        hw=34.0, hh=48.0, max_tile=168,
    ))

    # 11. Post-Crash Survivor Wheelman (progs/wheelman_dance.spr32 — ALL 8 CRAZY DANCES!)
    wd_specs = [
        ("dance", "🕺 1. Maniac Crash Dance", 160, 12),
        ("overhead", "🙌 2. Overhead Rig Sprint", 80, 10),
        ("kick", "🦵 3. Hands-Up Can-Can Kick", 256, 10),
        ("spinbar", "🌀 4. 360° Hurricane Bar Spin", 336, 12),
        ("lift", "🏋️ 5. Chrome Axle Deadlift", 432, 12),
        ("throw", "🤾 6. Yeet The Whole Rig", 528, 12),
        ("robot", "🤖 7. Morph Into Chrome Robot!", 624, 14),
        ("stuck", "🏃 8. Stuck-In-Wheels Sprint", 0, 10),
    ]
    wd_req, wd_slices = [], []
    for cid, clbl, base, klen in wd_specs:
        s0 = len(wd_req)
        ks = [0, klen // 3, (2 * klen) // 3]
        for d in range(8):
            for k in ks:
                wd_req.append(base + d * klen + k)
        wd_slices.append((cid, clbl, s0, len(wd_req)))
    wd_ims = read_spr32_subset("progs/wheelman_dance.spr32", wd_req)
    models.append(pack_turnaround_sprite(
        packer, "wheelman_dance_spr", "wheelman", "540 U/S · 8 POST-CRASH DANCES!",
        "Post-Crash Survivor Wheelman (All 8 Crazy 360° Dances!)",
        "progs/wheelman_dance.spr32",
        "After exploding, Wheelman pops out and tears around the room for 5.5s at 540 u/s performing 8 unhinged 360° stunts!",
        [(cid, clbl, 8, 3, 9.5, wd_ims[s0:s1]) for (cid, clbl, s0, s1) in wd_slices],
        hw=30.0, hh=56.0, max_tile=148,
    ))

    # 12. Wheelman Chrome Crash Handlebar Debris (progs/wc_bar.md3)
    models.append(pack_md3(
        packer, "progs/wc_bar.md3",
        dict(id="wc_bar", cat="wheelman", badge="CRASH DEBRIS · CHROME BAR",
             title="Wheelman Chrome Handlebar Crash Debris",
             file="progs/wc_bar.md3",
             desc="Bent chrome Wheelman axle bar sent clattering & bouncing across the floor alongside rolling tires whenever Wheelman detonates!"),
        surf_mats={"progs/wc_bar": dict(tex=packer.add_tex("progs/wc_bar.png", max_dim=384), metallic=0.85, roughness=0.20, spec=0.92)},
    ))

    print("[3/5] Packing CRAZY MEGA MAN Active In-Game Assets (5)...")
    # 13. Mega-Slinger Launcher (progs/v_megaman.md3 — active default Key 9 viewmodel!)
    t_mm_gun   = packer.add_tex("progs/mmw_gun_metal.png", max_dim=512)
    t_mm_gauge = packer.add_tex("progs/mmw_gauge_glow.png", max_dim=256)
    t_mm_hand  = packer.add_tex("progs/mmw_hand.png", max_dim=384)
    t_mm_fx    = packer.add_tex("progs/mmw_fx.png", max_dim=256, force_png=True)
    models.append(pack_md3(
        packer, "progs/v_megaman.md3",
        dict(id="v_megaman", cat="megaman", badge="KEY 9 · MEGA-SLINGER",
             title="Mega-Slinger Heavy Launcher (37f Viewmodel)",
             file="progs/v_megaman.md3",
             desc="Default Key 9 launcher cradling spinning white-dish pneumatic tires, chrome Mega-Man bar & glowing PSI gauge!",
             pov=True, az=2.45, el=0.22,
             clips=[
                 dict(id="all", label="💥 Spin, Launch & Reload (37f)", start=0, count=37, fps=14.0),
                 dict(id="idle", label="⚙ Spinning Tires Idle (8f)", start=0, count=8, fps=10.0),
             ]),
        surf_mats={
            "progs/mmw_gun_metal": dict(tex=t_mm_gun, metallic=0.65, roughness=0.28, spec=0.78),
            "progs/mmw_chrome_axle": dict(tex=t_mm_chr, metallic=0.88, roughness=0.17, spec=0.95),
            "progs/mmw_wheel": dict(tex=t_mm_whl),
            "progs/mmw_gauge_glow": dict(tex=t_mm_gauge, unlit=True),
            "progs/mmw_hand": dict(tex=t_mm_hand),
            "progs/mmw_fx": dict(tex=t_mm_fx, unlit=True, additive=True),
        },
    ))

    # 14. The Mega Man Contraption + Glowing EF_BLUE Underdog Blue Shell Skin (progs/megaman.md3)
    im_mm_base = open_asset_image("progs/megaman.png").convert("RGBA")
    t_mm_scan = packer.add_tex_pil(("mm_scan_std",), "megaman.png", im_mm_base, max_dim=512, lift=1.55)
    arr_bs = np.asarray(im_mm_base, dtype=np.float32).copy()
    lum = 0.299 * arr_bs[:, :, 0] + 0.587 * arr_bs[:, :, 1] + 0.114 * arr_bs[:, :, 2]
    arr_bs[:, :, 0] = np.clip(lum * 0.25 + 15.0, 0, 255)
    arr_bs[:, :, 1] = np.clip(lum * 1.15 + 75.0, 0, 255)
    arr_bs[:, :, 2] = np.clip(lum * 1.85 + 135.0, 0, 255)
    t_mm_blueshell = packer.add_tex_pil(("mm_scan_blueshell",), "megaman_blueshell.png", Image.fromarray(arr_bs.astype(np.uint8), "RGBA"), max_dim=512)
    models.append(pack_md3(
        packer, "progs/megaman.md3",
        dict(id="megaman", cat="megaman", badge="HEADCRAB + BLUE SHELL!",
             title="The Mega Man Contraption (+ BLUE SHELL Skin!)",
             file="progs/megaman.md3",
             desc="Roars like an outboard boat motor + foghorn, climbs stairs, leaps onto faces like a headcrab, and at 80%+ Underdog Boost glows EF_BLUE as the #1-hunting BLUE SHELL!",
             skins=[
                 dict(label="🛞 Standard LAN Mega Man", map={"wheelL": dict(tex=t_mm_scan, unlit=0), "wheelR": dict(tex=t_mm_scan, unlit=0), "body": dict(tex=t_mm_scan, unlit=0)}),
                 dict(label="🔵 UNDERDOG BLUE SHELL (EF_BLUE)!", map={"wheelL": dict(tex=t_mm_blueshell, unlit=1), "wheelR": dict(tex=t_mm_blueshell, unlit=1), "body": dict(tex=t_mm_blueshell, unlit=1)}),
             ],
             clips=[dict(id="roll", label="🛞 Boat-Motor Roll (16f)", start=0, count=16, fps=16.0)]),
        surf_mats={"progs/megaman": dict(tex=t_mm_scan, metallic=0.30, roughness=0.42, spec=0.55)},
    ))

    # 15. Mega Man 20f Voronoi Shatter & Fireball Explosion (progs/mm_explode.md3)
    models.append(pack_md3(
        packer, "progs/mm_explode.md3",
        dict(id="mm_explode", cat="megaman", badge="20f VORONOI SHATTER",
             title="Mega Man Explosive Voronoi Shatter & Fireball",
             file="progs/mm_explode.md3",
             desc="20-frame violent Voronoi casing shatter & fireball blast when Mega Man detonates in a victim's face!",
             clips=[dict(id="boom", label="💥 20f Shatter Detonation", start=0, count=20, fps=14.0, lie=True)]),
    ))

    # 16. Gyroscopic Rolling Tire Wreckage (progs/mm_wheel.md3 — flung by BOTH Mega Man & Wheelman!)
    models.append(pack_md3(
        packer, "progs/mm_wheel.md3",
        dict(id="mm_wheel", cat="megaman", badge="16f GYRO TIRE DEBRIS",
             title="Gyroscopic Rolling Tire Debris (Mega Man & Wheelman)",
             file="progs/mm_wheel.md3",
             desc="16-frame spinning pneumatic wheel flung out on detonation—leans into gyroscopic curves across the warehouse floor before tipping flat!",
             clips=[dict(id="spin", label="🛞 16f Gyroscopic Tire Spin", start=0, count=16, fps=16.0)]),
        surf_mats={"progs/mm_debris_tex": dict(tex=packer.add_tex("progs/mm_debris_tex.png", max_dim=512))},
    ))

    # 17. Room 120A Sacred Mega Man Bed Shrine Rig (progs/bklan/mm_rig.md3 — placed in bklan4 & bklan5!)
    models.append(pack_md3(
        packer, "progs/bklan/mm_rig.md3",
        dict(id="mm_rig", cat="megaman", badge="BKLAN ROOM 120A SHRINE",
             title="Room 120A Mega Man Bed Shrine Rig (bklan4 / bklan5)",
             file="progs/bklan/mm_rig.md3",
             desc="The gleaming chrome & white-dish Mega Man shrine resting on the bed in Suite 120A of Larry's B-LAN Warehouse!",
             clips=[dict(id="spin", label="✨ Shrine Wheel Spin (16f)", start=0, count=16, fps=12.0)]),
        surf_mats={
            "progs/mmw_chrome_axle": dict(tex=t_mm_chr, metallic=0.88, roughness=0.17, spec=0.95),
            "progs/mmw_wheel": dict(tex=t_mm_whl),
        },
    ))

    print("[4/5] Packing GOREY & FUNNY Heads, Active mb_pool Chasers & Car Wreck (9)...")
    # 18. Rob Dob Floating Head (progs/floathead.mdl)
    models.append(pack_mdl(
        packer, "progs/floathead.mdl",
        dict(id="floathead", cat="gore", badge='"HUG TIME!!" · BIG WET KISS',
             title="Rob Dob Giant Screaming Floating Head",
             file="progs/floathead.mdl",
             desc="Spawns across deathmatch & fires from Key F—shouts 'HUG TIME!', drops its jaw into a scream, and bursts into mini heads ('got a big wet kiss')!",
             az=-0.28, el=0.14),
        skin_labels=["😱 Screaming Open Jaw!", "🙂 Creepy Closed Smile"],
    ))
    if models[-1].get("skins"):
        models[-1]["skins"] = list(reversed(models[-1]["skins"]))

    # 19. Held Rob Dob Viewmodel (progs/v_robdob.mdl)
    models.append(pack_mdl(
        packer, "progs/v_robdob.mdl",
        dict(id="v_robdob", cat="gore", badge="KEY F · ROB DOB LAUNCHER",
             title="Held Rob Dob Head Launcher (1st-Person)",
             file="progs/v_robdob.mdl",
             desc="Hovers in your corner and glances back at you before you launch him down the hallway!",
             pov=True, az=2.82, el=0.18,
             clips=[dict(id="bob", label="👀 Creepy Glance Idle (8f)", start=0, count=8, fps=10.0)]),
    ))

    # 20. JohnWave 3D Head Grenade (progs/grenade.mdl)
    models.append(pack_mdl(
        packer, "progs/grenade.mdl",
        dict(id="grenade_jw", cat="gore", badge="KEY 6 / Q · HEAD GRENADE",
             title="JohnWave 3D Head Grenade (Replaces Pineapple!)",
             file="progs/grenade.mdl",
             desc="Bounces like a rubber ball, rolls face-up to stare at nearby victims, and erupts in a massive Pacific ocean splash!",
             az=-0.28, el=0.16),
    ))

    # 21. Key 4 AOL Laptop Gun 24-Angle Screaming Head Drone (progs/ltg_head.md3 + progs/ltg_head_00..23.png)
    assert_active_ingame_model("progs/ltg_head.md3")
    ltg_head_imgs = [open_asset_image(f"progs/ltg_head_{d:02d}.png") for d in range(24)]
    models.append(pack_turnaround_sprite(
        packer, "ltg_head", "gore", 'KEY 4 · "CANIS LUPUS!" DRONE',
        "AOL Laptop Gun Screaming Head Drone (24 Angles!)",
        "progs/ltg_head.md3 + ltgun.shader",
        "Summoned by the Key 4 3D Laptop Gun! Steer it with your crosshair as it yells 'Canis Lupus!', arcs 50,000V lightning & zaps campers!",
        [("turn24", "⚡ 24-Angle 360° Drone Spin", 24, 1, 10.0, ltg_head_imgs)],
        hw=32.0, hh=56.0, turn_dirs=24, max_tile=184,
    ))

    # 22. Kyle Running With Giant Scissors (progs/fr_scissors.spr32 — Active mb_pool #11!)
    scis_ims = read_spr32_subset("progs/fr_scissors.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    models.append(pack_turnaround_sprite(
        packer, "scissors_spr", "gore", "MB_POOL #11 · GIANT SCISSORS",
        "Kyle Running With Giant Snipping Scissors (360°)",
        "progs/fr_scissors.spr32",
        "Active Mystery Box monster #11! Sprints out of the box at 640 u/s snipping giant chrome blades and chopping campers into red gibs!",
        [("snip", "✂️ 360° Snipping Sprint (8-Dir)", 8, 3, 10.0, scis_ims)],
        max_tile=168,
    ))

    # 23. Tinfoil-Hat Bryan & His Whirling Demons (progs/bryan.spr32 — Active mb_pool #17!)
    bry_run = read_spr32_subset("progs/bryan.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    bry_alt = read_spr32_subset("progs/bryan.spr32", [56 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    models.append(pack_turnaround_sprite(
        packer, "bryan_spr", "gore", "MB_POOL #17 · BRYAN & DEMONS",
        "Tinfoil-Hat Bryan & His Whirling Demons (360°)",
        "progs/bryan.spr32",
        "Active Mystery Box monster #17! Yells 'NO WAY!' while orbited by 3 screeching hell-demons before exploding in a scream-launch!",
        [
            ("whirl", "👹 Demon Whirl Rush (8-Dir)", 8, 3, 9.5, bry_run),
            ("surge", "⚡ EMF Paranormal Surge (8-Dir)", 8, 3, 9.5, bry_alt),
        ],
        max_tile=168,
    ))

    # 24. Giant Rubber Finger Chaser (progs/fr_finger.spr32 — Active mb_pool #22!)
    fng_ims = read_spr32_subset("progs/fr_finger.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    models.append(pack_turnaround_sprite(
        packer, "finger_spr", "gore", "MB_POOL #22 · BOING-HOP FINGER",
        "Giant Wiggling Rubber Finger Chaser (360°)",
        "progs/fr_finger.spr32",
        "Active Mystery Box monster #22! Boing-hops at 640 u/s (`drv_boing_hop.wav`) straight into your face before blowing up!",
        [("hop", "☝️ 360° Boing-Hop Rush (8-Dir)", 8, 3, 10.0, fng_ims)],
        max_tile=168,
    ))

    # 25. Mr. DIY Workshop Chaser (progs/fr_mrdiy.spr32 — Active mb_pool #21!)
    diy_ims = read_spr32_subset("progs/fr_mrdiy.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    models.append(pack_turnaround_sprite(
        packer, "mrdiy_spr", "gore", "MB_POOL #21 · MR. DIY",
        "Mr. DIY Tool-Swinging Workshop Chaser (360°)",
        "progs/fr_mrdiy.spr32",
        "Active Mystery Box monster #21! Charges out of the rainbow crystal cube in full 8-angle 360°!",
        [("run", "🛠️ 360° Mr. DIY Sprint (8-Dir)", 8, 3, 10.0, diy_ims)],
        max_tile=168,
    ))

    # 26. Exploding Cargo Van Scorched Wreck (progs/veh_van_wreck.md3)
    t_vburn = packer.add_tex("progs/veh_van_burn.png", max_dim=512, lift=1.25)
    t_vbgl  = packer.add_tex("progs/veh_van_burn_glow.png", max_dim=384)
    models.append(pack_md3(
        packer, "progs/veh_van_wreck.md3",
        dict(id="veh_van_wreck", cat="gore", badge="20f SCORCHED CAR BOMB",
             title="Exploding Cargo Van Scorched Wreck (20f)",
             file="progs/veh_van_wreck.md3",
             desc="Shoot any parked car or van enough and it crumples & blows sky-high into scorched smoldering wreckage, doors, hoods & wheels!",
             clips=[dict(id="boom", label="🔥 20f Crumple & Smolder", start=0, count=20, fps=13.0, lie=True)]),
        surf_mats={"progs/veh_van_burn": dict(tex=t_vburn, glowTex=t_vbgl)},
    ))

    print("[5/5] Packing ACTIVE LAN ARSENAL, MYSTERY BOX, CCC, GOO, VAN & WORLD ENTITIES (16)...")
    # 27 & 28. Rainbow Mystery Box Held Viewmodel + Thrown 3D Projectile (progs/v_mysterybox.md3 & progs/proj_mysterybox.md3)
    mb_mats = {
        "man_hand": dict(tex=packer.add_tex("progs/mbox_hand.png", max_dim=512)),
        "crystal_core": dict(tex=packer.add_tex("progs/mbox_qmark.png", max_dim=256, force_png=True), unlit=True, alphaBlend=True),
        "ghost_3d": dict(tex=packer.add_tex("progs/mbox_ghost_3d.png", max_dim=512, force_png=True), unlit=True, additive=True),
        "ghost_spr": dict(tex=packer.add_tex("progs/mbox_ghost_spr.png", max_dim=512, force_png=True), unlit=True, additive=True),
        "box_glass": dict(tex=packer.add_tex("progs/mbox_glass.png", max_dim=256, force_png=True), unlit=True, alphaBlend=True),
        "box_qmark": dict(tex=packer.add_tex("progs/mbox_qmark.png", max_dim=256, force_png=True), unlit=True, alphaBlend=True),
        "box_fx": dict(tex=packer.add_tex("progs/mbox_fx.png", max_dim=256, force_png=True), unlit=True, additive=True),
    }
    models.append(pack_md3(
        packer, "progs/v_mysterybox.md3",
        dict(id="v_mysterybox", cat="arsenal", badge="KEY U · MYSTERY BOX",
             title="Rainbow Mystery Box (Sculpted Hand + Crystal Cube)",
             file="progs/v_mysterybox.md3",
             desc="Levitates above your hand cycling holographic monster visions—throw it (Key U) to unleash 640 u/s Mystery Box chasers!",
             pov=True, az=2.55, el=0.20,
             clips=[
                 dict(id="idle", label="🔮 Hologram Crystal Loop", start=0, count=48, fps=3.5),
                 dict(id="throw", label="🤾 Grab, Glow & Throw!", start=48, count=7, fps=6.0),
             ]),
        surf_mats=mb_mats, frame_stride=4,
    ))
    models.append(pack_md3(
        packer, "progs/proj_mysterybox.md3",
        dict(id="proj_mysterybox", cat="arsenal", badge="THROWN PRISM CUBE · 32f",
             title="Thrown Rainbow Mystery Box Projectile",
             file="progs/proj_mysterybox.md3",
             desc="Tumbles through the air trailing rainbow sparks before bursting into confetti and spawning active mb_pool monsters!",
             az=0.35, el=0.18,
             clips=[dict(id="spin", label="🌈 Tumbling Prism Flight (32f)", start=0, count=32, fps=12.0)]),
        surf_mats=mb_mats,
    ))

    # 29. Active mb_pool LAN Crew Trio: #18 Dennis, #19 Paul & #20 QuakeGuy (Switchable Skins!)
    den_ims = read_spr32_subset("progs/fr_dennis.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    pau_ims = read_spr32_subset("progs/fr_paul.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    qkg_ims = read_spr32_subset("progs/fr_quakeguy.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    models.append(pack_turnaround_sprite(
        packer, "lan_friends_spr", "arsenal", "MB_POOL #18 · #19 · #20",
        "Bakersfield LAN Crew Chasers (Dennis, Paul & QuakeGuy!)",
        "progs/fr_dennis.spr32 · fr_paul.spr32 · fr_quakeguy.spr32",
        "Active Mystery Box monsters #18, #19 & #20! Click 🎨 Skin to switch between Dennis, Paul, and QuakeGuy while spinning 360°!",
        [("run", "🏃 360° 640 u/s Sprint (8-Dir)", 8, 3, 10.0, den_ims)],
        skins_pil=[("😎 #18 Dennis", den_ims), ("🏃 #19 Paul", pau_ims), ("🪖 #20 QuakeGuy", qkg_ims)],
        max_tile=160,
    ))

    # 30. JessKart 360° Chaser (progs/jesskart.spr32 — Active mb_pool #10!)
    jk_ims = read_spr32_subset("progs/jesskart.spr32", [8 + d * 6 + k for d in range(8) for k in (0, 2, 4)])
    jk_idl = read_spr32_subset("progs/jesskart.spr32", list(range(8)))
    models.append(pack_turnaround_sprite(
        packer, "jesskart_spr", "arsenal", "MB_POOL #10 · JESSKART",
        "JessKart 640 u/s Turbo Kart Chaser (360°)",
        "progs/jesskart.spr32",
        "Active Mystery Box monster #10! Roars out of the Mystery Box in full 8-angle 360° and runs down campers!",
        [
            ("drive", "🏁 360° Full-Throttle Rush (8-Dir)", 8, 3, 10.0, jk_ims),
            ("idle", "🛞 8-Angle Kart Turnaround", 8, 1, 8.0, jk_idl),
        ],
        hw=34.0, hh=60.0, max_tile=168,
    ))

    # 31. Active Key 4 AOL Dial-Up 3D Laptop Gun (progs/ltg_v3d.md3!)
    models.append(pack_md3(
        packer, "progs/ltg_v3d.md3",
        dict(id="ltg_v3d", cat="arsenal", badge="KEY 4 · AOL 5.0 3D LAPTOP",
             title='AOL Dial-Up 3D Laptop Gun ("Hacking internet lag")',
             file="progs/ltg_v3d.md3",
             desc="Active Key 4 weapon! Hold fire to hammer the 3D Think-Lag keyboard with both hands, arc 50,000V lightning & steer the 24-angle Screaming Head Drone!",
             pov=True, az=2.78, el=0.22,
             clips=[
                 dict(id="all", label="⚡ Dial-Up + Manic Typing (34f)", start=0, count=34, fps=14.0),
                 dict(id="type", label="⌨️ Rapid 2-Hand Hacking (22f)", start=12, count=22, fps=16.0),
             ]),
        lift=1.35,
    ))

    # 32 & 33. Bio-Foam Goo Gun + Expanding Solid Foam Blob (progs/v_googun.md3 & progs/goo.md3)
    models.append(pack_md3(
        packer, "progs/v_googun.md3",
        dict(id="v_googun", cat="arsenal", badge="KEY 2 · BIO-FOAM BUILDER",
             title="Bio-Foam Goo Gun (Build Walls & Gum Victims!)",
             file="progs/v_googun.md3",
             desc="Pressurized polyurethane sprayer! Stack solid foam blobs into walls, bridges & stairs—or gum enemies in place ('GOOED!')!",
             pov=True, az=2.45, el=0.22),
        lift=1.40,
    ))
    models.append(pack_md3(
        packer, "progs/goo.md3",
        dict(id="goo_blob", cat="arsenal", badge="6f SOLID FOAM BLOB",
             title="Expanding Bio-Foam Wall/Bridge Blob (6f)",
             file="progs/goo.md3",
             desc="Expands on impact into a solid steppable polyurethane foam boulder—build staircases to rooftops or seal doorways!",
             clips=[dict(id="swell", label="🧪 6f Foam Swell & Harden", start=0, count=6, fps=9.0)]),
        surf_mats={"progs/goo": dict(tex=packer.add_tex("progs/goo.png", max_dim=384), roughness=0.35, spec=0.55)},
    ))

    # 34. Key 8 CCC Gun Spinning Yellow 'C' Projectile (progs/ccc.md3)
    models.append(pack_md3(
        packer, "progs/ccc.md3",
        dict(id="ccc_proj", cat="arsenal", badge="KEY 8 · CCC RICOCHET",
             title="CCC Gun Spinning Yellow 'C' Ricochet Bolt",
             file="progs/ccc.md3",
             desc="Fired by Key 8 (`weapons.qc`): hurls rapid-fire spinning yellow 3D 'C' letters that boing-ricochet (`floathead/boing.wav`) off walls!",
             clips=[dict(id="spin", label="💛 Spinning 3D 'C' Bolt", start=0, count=1, fps=10.0)]),
        surf_mats={"progs/ccc_yellow": dict(tex=packer.add_tex("progs/ccc_yellow.png", max_dim=256), metallic=0.35, roughness=0.25, spec=0.75)},
    ))

    # 35. 255f Charge Bonk Hammer (progs/v_hammer.mdl)
    models.append(pack_mdl(
        packer, "progs/v_hammer.mdl",
        dict(id="v_hammer", cat="arsenal", badge="KEY 1 · 255f BONK HAMMER",
             title="Tiered Charge Bonk Hammer (Swat, Pogo & Air-Dash!)",
             file="progs/v_hammer.mdl",
             desc="255-frame frying-pan-clang warhammer! Charge for 30/80/200 knockback swat, look down in mid-air to Pogo-Hop, or forward to Air-Dash!",
             pov=True, az=2.55, el=0.22,
             clips=[
                 dict(id="smash", label="💥 Max Charge Home-Run Smash", start=40, count=19, fps=18.0),
                 dict(id="dash", label="🚀 Mid-Air Dash & Pogo Hop", start=59, count=18, fps=16.0),
                 dict(id="spin", label="🌀 Show-Off Flourish Spin", start=186, count=69, fps=20.0),
                 dict(id="idle", label="🔨 Heavy Idle Sway", start=0, count=40, fps=14.0),
             ]),
    ))

    # 36 & 37. NetSend LOL.BAT 3.5" Floppy Gun + Win98 CRT Laser Turret (progs/v_netsend.md3 & progs/netsend_pc.md3)
    models.append(pack_md3(
        packer, "progs/v_netsend.md3",
        dict(id="v_netsend", cat="arsenal", badge='KEY B · "LOL.BAT" 3.5"',
             title='NetSend "LOL.BAT" 3.5" Floppy Diskette Gun',
             file="progs/v_netsend.md3",
             desc="Deals & flicks a 3.5-inch 'LOL.BAT' floppy disk (Key B/N) that materializes a spinning Win98 CRT PC firing green lasers!",
             pov=True, az=2.55, el=0.22,
             clips=[dict(id="all", label="💾 Fan Disks & Flick (30kf)", start=0, count=30, fps=8.0)]),
        frame_stride=2, lift=1.35,
    ))

    assert_active_ingame_model("progs/netsend_arc.md3")
    ns_screens = [open_asset_image(f"progs/netsend_s_l{k:02d}.png") for k in range(0, 16, 2)]
    tid_ns_scr = packer.add_atlas("netsend_crt_loop", ns_screens, max_tile_dim=208)
    tid_ns_lol = packer.add_tex("progs/netsend_s_lol0.png", max_dim=256)
    m_arc = read_md3_bytes(read_asset_bytes("progs/netsend_arc.md3"))
    sa_arc = m_arc["surfaces"][0]
    s_arc_enc = encode_surface(packer, "electric_arcs", "netsend_arc", sa_arc["st"], sa_arc["tris"],
                               sa_arc["all_v"][::2], sa_arc["all_n"][::2],
                               dict(tex=packer.add_tex("progs/netsend_arc.png", max_dim=256, force_png=True), unlit=True, additive=True))
    models.append(pack_md3(
        packer, "progs/netsend_pc.md3",
        dict(id="netsend_pc", cat="arsenal", badge="WIN98 CRT TURRET + ARCS",
             title="Materializing Win98 NetSend CRT PC + Lightning Cage",
             file="progs/netsend_pc.md3 + netsend_arc.md3",
             desc="Materializes mid-room, boots LOL.BAT, spins 360° sweeping green lasers & spamming Windows Messenger popups across victims' HUDs!",
             skins=[
                 dict(label="🖥 NET SEND Laser Sweep", map={"netsend_screen": dict(tex=tid_ns_scr, animFps=8.0)}),
                 dict(label="💾 C:\\> LOL.BAT Boot", map={"netsend_screen": dict(tex=tid_ns_lol, animFps=0.0)}),
             ],
             clips=[dict(id="spin", label="⚡ Materialize & Laser Spin", start=0, count=25, fps=8.0)]),
        surf_mats={"progs/netsend_scr_loop": dict(tex=tid_ns_scr, animFps=8.0, unlit=True)},
        frame_stride=2, extra_surfs=[s_arc_enc],
    ))

    # 38. Driveable 6-Man LAN Van (progs/veh_van.md3)
    t_van_gl = packer.add_tex("progs/veh_van_tex_glow.png", max_dim=384)
    t_van_gs = packer.add_tex("progs/veh_van_glass.png", max_dim=128, force_png=True)
    models.append(pack_md3(
        packer, "progs/veh_van.md3",
        dict(id="veh_van", cat="arsenal", badge="KEY H · 6-MAN LAN VAN!",
             title="Driveable 6-Man LAN Van (Clean, Cutaway & Burned!)",
             file="progs/veh_van.md3",
             desc="Press H at 1608 Manning St to hop in, chant '6-Man LAN Van!', and flatten campers! Switch Skins for Interior Cutaway or Burned Wreck.",
             skins=[
                 dict(label="🚐 Clean White LAN Van", map={"body_a": dict(tex=t_van, nodraw=False), "body_b": dict(tex=t_van), "interior": dict(tex=t_van), "wheels": dict(tex=t_van)}),
                 dict(label="🔍 Interior Cutaway View", map={"body_a": dict(nodraw=True), "body_b": dict(tex=t_van), "interior": dict(tex=t_van), "wheels": dict(tex=t_van)}),
                 dict(label="🔥 Scorched Car-Bomb Skin", map={"body_a": dict(tex=t_vburn, nodraw=False), "body_b": dict(tex=t_vburn), "interior": dict(tex=t_vburn), "wheels": dict(tex=t_vburn)}),
             ],
             clips=[dict(id="drive", label="🚐 Roll & Steer (18kf)", start=0, count=18, fps=8.0)]),
        surf_mats={
            "progs/veh_van_tex": dict(tex=t_van, glowTex=t_van_gl),
            "progs/veh_van_glass": dict(tex=t_van_gs, alphaBlend=True),
        },
        frame_stride=2,
    ))

    # 39. Duke3D Twin-Turbine Rocket Jetpack (progs/jetpack.md3)
    jp_plumes = [open_asset_image(f"progs/jetpack_plume_{k}.png") for k in range(4)]
    tid_jpp = packer.add_atlas("jp_plume_4", jp_plumes, max_tile_dim=192)
    models.append(pack_md3(
        packer, "progs/jetpack.md3",
        dict(id="jetpack", cat="arsenal", badge='KEY J · "I\'M FLOATING!!"',
             title="Duke3D Twin-Turbine Rocket Jetpack",
             file="progs/jetpack.md3",
             desc="Spawns beside every Yellow Armor—press J to ignite twin afterburners, yell 'I'm floating!', and rain Wheelmen from 2,500 ft!",
             az=2.55, el=0.16,
             clips=[dict(id="fly", label="🔥 Twin Afterburner Thrust (16f)", start=0, count=16, fps=14.0)]),
        surf_mats={
            "progs/jetpack_plume": dict(tex=tid_jpp, animFps=18.0, unlit=True, additive=True),
            "progs/jetpack_glow": dict(tex=packer.add_tex("progs/jetpack_glow.png", max_dim=256), unlit=True),
            "progs/jetpack_dial": dict(tex=packer.add_tex("progs/jetpack_dial.png", max_dim=256), unlit=True),
        },
    ))

    # 40. Golden 3.0s Spawn Protection Forcefield (progs/aura.md3 — bm_match.qc)
    models.append(pack_md3(
        packer, "progs/aura.md3",
        dict(id="aura", cat="arsenal", badge="3.0s SPAWN PROTECTION",
             title="Golden 3.0s Spawn Protection Forcefield",
             file="progs/aura.md3",
             desc="3-second golden invulnerability bubble granted on every respawn (`bm_spawnprot 3`)—drops the instant you fire so nobody can spawn-abuse it!",
             clips=[dict(id="pulse", label="✨ Spawn Shield Spin", start=0, count=1, fps=10.0)]),
    ))

    # 41. Golden West Casino Giant Bronze Horse (progs/gw_horse.md3 — placed in bklan4, bklan5 & bakolansmall!)
    models.append(pack_md3(
        packer, "progs/gw_horse.md3",
        dict(id="gw_horse", cat="arsenal", badge="GOLDEN WEST CASINO ICON",
             title="Golden West Casino Rearing Bronze Horse Statue",
             file="progs/gw_horse.md3",
             desc="Iconic rearing bronze stallion landmark standing outside Golden West Casino in bklan4, bklan5 & bakolansmall!",
             az=-0.45, el=0.16),
        surf_mats={
            "progs/gw_horse": dict(tex=packer.add_tex("progs/gw_horse.png", max_dim=512), metallic=0.78, roughness=0.26, spec=0.88),
            "progs/gw_rock": dict(tex=packer.add_tex("progs/gw_rock.png", max_dim=384), roughness=0.75, spec=0.20),
        },
    ))

    # 42. Amberton Park Sky-Rocketing Trashcan (progs/bklan/trashcan.md3 — bk_trashcan in bklan4 & bklan5!)
    models.append(pack_md3(
        packer, "progs/bklan/trashcan.md3",
        dict(id="bk_trashcan", cat="arsenal", badge="SHOOT TO LAUNCH!! · BKLAN",
             title="Amberton Park Sky-Rocketing Trashcan (bk_trashcan)",
             file="progs/bklan/trashcan.md3",
             desc="Interactive bklan4/bklan5 prop: shoot any park trashcan and it blasts off into the Bakersfield sky on a rocket trail before exploding!",
             az=-0.35, el=0.18),
        surf_mats={"progs/bklan/bk_trash": dict(tex=packer.add_tex("progs/bklan/bk_trash.png", max_dim=384))},
    ))

    # Compress & write
    arena_bytes = bytes(packer.buf)
    gz_bytes = gzip.compress(arena_bytes, compresslevel=9)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    tex_mb = sum(len(t["uri"]) for t in packer.tex_list) / 1e6

    payload = dict(
        textures=packer.tex_list,
        models=models,
        binGz=b64_gz,
    )
    js_str = "window.BQ_MODELS_PACK = " + json.dumps(payload, separators=(",", ":")) + ";\n"
    with open(ASSETS_OUT, "w", encoding="utf-8") as f:
        f.write(js_str)

    cats = {}
    for m in models:
        cats[m["cat"]] = cats.get(m["cat"], 0) + 1
    print(
        f"[MODELS OK] Packed & ground-truth verified {len(models)} pure in-game 3D/sprite assets ({cats}) & {len(packer.tex_list)} textures!\n"
        f"  Arena: {len(arena_bytes)/1e6:.2f} MB raw -> {len(gz_bytes)/1e6:.2f} MB gz | Textures: {tex_mb:.2f} MB\n"
        f"  Wrote {ASSETS_OUT} ({os.path.getsize(ASSETS_OUT)/1e6:.2f} MB total)"
    )


if __name__ == "__main__":
    main()
