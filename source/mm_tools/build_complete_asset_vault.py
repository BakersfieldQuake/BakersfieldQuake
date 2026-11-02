#!/usr/bin/env python3
r"""Master Builder for BakersfieldQuake's Complete Custom Asset Vault:
  1. Live Website Bundle -> source/mm_tools/out/custom_assets_web/
       (uploaded to https://bakersfield.larrywew.fun/custom-assets/)
  2. Self-Contained Single-File HTML -> G:\Quake\Combat\BakersfieldQuake\all_custom_assets.html
       (also uploaded to https://bakersfield.larrywew.fun/all_custom_assets.html)
  3. Local Master All-In-One ZIP -> G:\Quake\Combat\BakersfieldQuake\bakersfield_all_custom_assets.zip

Packs EVERY SINGLE custom 3D model & 360-degree sprite (354 shipped in bakersfield.pk3 + 8 archived vault models = 362),
links/embeds all 318 custom sounds, all 1,044 custom textures & skyboxes, all 15 .GLB 3D source models,
all 27 .shader scripts, and all 13 custom .BSP/.LIT maps.
"""
import base64
import glob
import gzip
import io
import json
import math
import os
import re
import shutil
import struct
import time
import zipfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(MOD, ".."))
PK3_PATH = os.path.join(MOD, "bakersfield.pk3")
VAULT_ZIP_OUT = os.path.join(HERE, "out", "vault_extras.zip")
VAULT_ZIP_TMP = os.path.join(os.environ.get("TEMP", "/tmp"), "vault_extras.zip")
VPS_MAN_PATH = os.path.join(HERE, "out", "vps_manifest.json")
VPS_GLB_DIR = os.path.join(HERE, "out", "vps_glb")
ID1_PAK0 = os.path.join(ROOT, "id1", "pak0.pak")
ANORM_JSON = os.path.join(ROOT, "monster_page", "anorm.json")
TEMPLATE_PATH = os.path.join(HERE, "complete_asset_vault.template.html")
WEB_OUT_DIR = os.path.join(HERE, "out", "custom_assets_web")
SELF_HTML_OUT = os.path.join(MOD, "all_custom_assets.html")
LOCAL_MASTER_ZIP = os.path.join(MOD, "bakersfield_all_custom_assets.zip")


def canon_id(rel_path):
    return rel_path.replace("\\", "/").lstrip("/").lower().replace("/", "__").replace(".", "_")


def load_pak_entry(pak_path, entry_name):
    with open(pak_path, "rb") as f:
        ident, ofs, length = struct.unpack("<4sii", f.read(12))
        assert ident == b"PACK", pak_path
        f.seek(ofs)
        raw = f.read(length)
        target = entry_name.lower()
        for i in range(0, length, 64):
            nm = raw[i:i + 56].split(b"\0", 1)[0].decode("ascii", "replace").lower()
            pos, sz = struct.unpack("<ii", raw[i + 56:i + 64])
            if nm == target:
                f.seek(pos)
                return f.read(sz)
    raise KeyError(entry_name)


PALETTE_U8 = np.frombuffer(load_pak_entry(ID1_PAK0, "gfx/palette.lmp"), dtype=np.uint8).reshape(256, 3)
ANORM_F32 = np.asarray(json.load(open(ANORM_JSON, encoding="utf-8")), dtype=np.float32).reshape(-1, 3)
PLAYER_259_NAMES = None


def get_player_259_names():
    global PLAYER_259_NAMES
    if PLAYER_259_NAMES is None:
        d = load_pak_entry(ID1_PAK0, "progs/player.mdl")
        h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
        nsk, sw, sh, nvo, nt, nf = h[12:18]
        o = 84 + nsk * (4 + sw * sh) + nvo * 12 + nt * 16
        nms = []
        for _ in range(nf):
            o += 12
            nms.append(d[o:o + 16].split(b"\0", 1)[0].decode("ascii", "replace").strip())
            o += 16 + nvo * 4
        while len(nms) < 259:
            nms.append(f"ext{len(nms) - 142}")
        PLAYER_259_NAMES = nms[:259]
    return PLAYER_259_NAMES


class VFS:
    """Fast unified reader over bakersfield.pk3 + vault_extras.zip."""
    def __init__(self, pk3_path, vault_zip_path):
        self.z_pk3 = zipfile.ZipFile(pk3_path, "r")
        self.z_vault = zipfile.ZipFile(vault_zip_path, "r")
        self.entries = {}
        self.real_path = {}
        for zf in (self.z_pk3, self.z_vault):
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = info.filename.replace("\\", "/").lstrip("/")
                k = rel.lower()
                self.entries[k] = (zf, info.filename)
                self.real_path[k] = rel

    def exists(self, rel):
        return rel.replace("\\", "/").lstrip("/").lower() in self.entries

    def read(self, rel):
        zf, member = self.entries[rel.replace("\\", "/").lstrip("/").lower()]
        return zf.read(member)

    def open_pil(self, rel):
        im = Image.open(io.BytesIO(self.read(rel)))
        im.load()
        return im


class VaultPacker:
    """Packs geometry into a shared binary arena and stores textures both as raw bytes (for web_tex/) and base64 URIs."""
    def __init__(self):
        self.buf = bytearray()
        self.tex_map = {}
        self.tex_list = []
        self.tex_raw_files = []  # (ext, bytes)

    def add_bytes(self, raw_bytes):
        while len(self.buf) & 7:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(raw_bytes)
        return [off, len(raw_bytes)]

    def add_tex_pil(self, cache_key, label_key, im, max_dim=512, quality=82,
                    force_png=False, nearest=False, wrap=False, lift=1.0, raw_rel=None):
        if cache_key in self.tex_map:
            return self.tex_map[cache_key]
        has_alpha = im.mode in ("RGBA", "LA") or ("transparency" in im.info)
        im = im.convert("RGBA" if has_alpha else "RGB")
        if has_alpha:
            a_min = int(np.asarray(im.getchannel("A")).min())
            if a_min >= 252:
                has_alpha = False
                im = im.convert("RGB")
        if abs(lift - 1.0) > 1e-3:
            arr = np.asarray(im, dtype=np.float32).copy()
            rgb = np.clip(((arr[:, :, :3] / 255.0) ** 0.88) * float(lift), 0.0, 1.0)
            arr[:, :, :3] = np.rint(rgb * 255.0)
            im = Image.fromarray(arr.astype(np.uint8), "RGBA" if has_alpha else "RGB")
        w0, h0 = im.size
        if max_dim and max(w0, h0) > max_dim:
            sc = max_dim / float(max(w0, h0))
            nw, nh = max(1, round(w0 * sc)), max(1, round(h0 * sc))
            im = im.resize((nw, nh), Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
        w, h = im.size
        bio = io.BytesIO()
        if force_png or nearest or max(w, h) <= 64:
            im.save(bio, "PNG", optimize=True)
            mime, ext = "image/png", "png"
        else:
            im.save(bio, "WEBP", quality=quality, method=4)
            mime, ext = "image/webp", "webp"
        img_bytes = bio.getvalue()
        uri = f"data:{mime};base64," + base64.b64encode(img_bytes).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[cache_key] = idx
        self.tex_raw_files.append((ext, img_bytes))
        entry = dict(
            key=label_key, w=w, h=h, uri=uri,
            alpha=bool(has_alpha), nearest=bool(nearest or max(w0, h0) <= 16),
            noMip=False, wrap=bool(wrap),
            cols=1, rows=1, tileW=w, tileH=h, pad=0, count=1,
        )
        if raw_rel:
            entry["rawRel"] = raw_rel
        self.tex_list.append(entry)
        return idx

    def add_tex_vfs(self, vfs, rel, max_dim=512, quality=82, force_png=False, nearest=False, wrap=False, lift=1.0):
        k = rel.replace("\\", "/").lstrip("/").lower()
        real = vfs.real_path[k]
        ck = ("vfs", k, max_dim, bool(force_png), bool(nearest), bool(wrap), round(float(lift), 2))
        if ck in self.tex_map:
            return self.tex_map[ck]
        im = vfs.open_pil(k)
        return self.add_tex_pil(
            ck, os.path.basename(real), im,
            max_dim=max_dim, quality=quality, force_png=force_png,
            nearest=nearest, wrap=wrap, lift=lift, raw_rel=real,
        )

    def add_atlas(self, atlas_id, frames_pil, max_tile_dim=192, pad=1, quality=80, nearest=False, raw_rel=None):
        ck = ("atlas", atlas_id)
        if ck in self.tex_map:
            return self.tex_map[ck]
        n = len(frames_pil)
        assert n >= 1, f"Empty atlas {atlas_id}"
        mw0 = max(im.size[0] for im in frames_pil)
        mh0 = max(im.size[1] for im in frames_pil)
        sc = min(1.0, max_tile_dim / float(max(mw0, mh0))) if max_tile_dim else 1.0
        tw = max(1, round(mw0 * sc))
        th = max(1, round(mh0 * sc))

        cols = max(1, int(math.ceil(math.sqrt(n * (th / float(max(1, tw)))))))
        rows = int(math.ceil(n / float(cols)))
        # Strictly fit inside WebGL2 universal 4096x4096 texture bound
        if max(cols * (tw + 2 * pad), rows * (th + 2 * pad)) > 4064:
            sc_fit = min(
                (4064 // cols - 2 * pad) / float(max(1, tw)),
                (4064 // rows - 2 * pad) / float(max(1, th)),
            )
            tw = max(12, int(math.floor(tw * sc_fit)))
            th = max(12, int(math.floor(th * sc_fit)))

        cw, ch = tw + 2 * pad, th + 2 * pad
        aw, ah = cols * cw, rows * ch
        atlas_np = np.zeros((ah, aw, 4), dtype=np.uint8)
        resample = Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS

        for idx_f, im0 in enumerate(frames_pil):
            im_rgba = im0.convert("RGBA")
            if im_rgba.size != (tw, th):
                if im_rgba.size[0] != mw0 or im_rgba.size[1] != mh0:
                    canvas = Image.new("RGBA", (mw0, mh0), (0, 0, 0, 0))
                    ox = (mw0 - im_rgba.size[0]) // 2
                    oy = mh0 - im_rgba.size[1]
                    canvas.paste(im_rgba, (ox, oy))
                    im_rgba = canvas
                im_rgba = im_rgba.resize((tw, th), resample)
            arr = np.asarray(im_rgba, dtype=np.uint8)
            padded = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge") if pad > 0 else arr
            c, r = idx_f % cols, idx_f // cols
            atlas_np[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = padded

        atlas_im = Image.fromarray(atlas_np, "RGBA")
        bio = io.BytesIO()
        if nearest and max(aw, ah) <= 512:
            atlas_im.save(bio, "PNG", optimize=True)
            mime, ext = "image/png", "png"
        else:
            atlas_im.save(bio, "WEBP", quality=quality, method=4)
            mime, ext = "image/webp", "webp"
        img_bytes = bio.getvalue()
        uri = f"data:{mime};base64," + base64.b64encode(img_bytes).decode("ascii")
        t_idx = len(self.tex_list)
        self.tex_map[ck] = t_idx
        self.tex_raw_files.append((ext, img_bytes))
        entry = dict(
            key=atlas_id, w=aw, h=ah, uri=uri,
            alpha=True, nearest=bool(nearest), noMip=True, wrap=False,
            cols=cols, rows=rows, tileW=tw, tileH=th, pad=pad, count=n,
        )
        if raw_rel:
            entry["rawRel"] = raw_rel
        self.tex_list.append(entry)
        return t_idx


def strip_reversed_dups_fast(tri_arr):
    tri_arr = np.asarray(tri_arr, dtype=np.int32)
    if len(tri_arr) == 0:
        return tri_arr.astype("<u2")
    seen = set()
    keep = []
    for i, (a, b, c) in enumerate(tri_arr.tolist()):
        if (a, c, b) in seen or (c, b, a) in seen or (b, a, c) in seen:
            continue
        seen.add((a, b, c))
        keep.append(i)
    return tri_arr[keep].astype("<u2")


def build_wire_edges(tri_u16):
    if len(tri_u16) == 0:
        return np.zeros((0, 2), dtype="<u2")
    e01 = np.sort(tri_u16[:, [0, 1]], axis=1)
    e12 = np.sort(tri_u16[:, [1, 2]], axis=1)
    e20 = np.sort(tri_u16[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


def encode_surface(packer, sname, shader, uv_arr, tri_arr, all_v, all_n, mat):
    nf, nv, _ = all_v.shape
    assert nv < 65535, f"Surface {sname} nv={nv} exceeds Uint16!"
    uv_f32 = np.asarray(uv_arr, dtype="<f4")
    tri_u16 = strip_reversed_dups_fast(tri_arr)
    edges_u16 = build_wire_edges(tri_u16)
    nt = len(tri_u16)

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

    out = dict(
        name=sname, shader=shader,
        nv=int(nv), nt=int(nt), ne=int(len(edges_u16)), nfGeom=int(nf),
        posScale=float(pos_scale),
        tris=packer.add_bytes(tri_u16.tobytes()),
        edges=packer.add_bytes(edges_u16.tobytes()),
        uv=packer.add_bytes(uv_f32.tobytes()),
        pos=packer.add_bytes(dpos.tobytes()),
        nrm=packer.add_bytes(dnrm.tobytes()),
        tex=int(mat.get("tex", -1)),
        glowTex=int(mat.get("glowTex", -1)),
        animFps=float(mat.get("animFps", 0.0)),
        animOrder=mat.get("animOrder"),
        scrollV=float(mat.get("scrollV", 0.0)),
        metallic=float(mat.get("metallic", 0.15)),
        roughness=float(mat.get("roughness", 0.52)),
        spec=float(mat.get("spec", 0.38)),
        unlit=1 if mat.get("unlit") else 0,
        additive=1 if mat.get("additive") else 0,
        alphaTest=1 if mat.get("alphaTest") else 0,
        alphaBlend=1 if mat.get("alphaBlend") else 0,
        billboard=int(mat.get("billboard", 0)),
    )
    if mat.get("defaultHidden"):
        out["defaultHidden"] = True
    if "fixedTile" in mat:
        out["fixedTile"] = int(mat["fixedTile"])
    return out


def read_md3_bytes(d, label=""):
    ident, ver, name_b, flags, nf, ntags, ns, nsk, ofs_f, ofs_t, ofs_s, ofs_e = struct.unpack("<4si64s9i", d[:108])
    assert ident == b"IDP3" and ver == 15, f"Invalid MD3: {label}"
    fnames = []
    for i in range(nf):
        fo = ofs_f + 56 * i
        fn = d[fo + 40:fo + 56].split(b"\0", 1)[0].decode("ascii", "replace").strip()
        fnames.append(fn or f"f{i}")
    surfaces = []
    o = ofs_s
    scale_2pi = 2.0 * math.pi / 255.0
    for si in range(ns):
        h = struct.unpack("<4s64s10i", d[o:o + 108])
        sname = h[1].split(b"\0", 1)[0].decode("ascii", "replace") or f"surf_{si}"
        _, snf, nsh, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end = h[2:]
        shader = d[o + o_sh:o + o_sh + 64].split(b"\0", 1)[0].decode("ascii", "replace") if nsh > 0 else ""
        tris = np.frombuffer(d, dtype="<i4", count=nt * 3, offset=o + o_tri).reshape(nt, 3).copy()
        st = np.frombuffer(d, dtype="<f4", count=nv * 2, offset=o + o_st).reshape(nv, 2).copy()
        raw_i16 = np.frombuffer(d, dtype="<i2", count=snf * nv * 4, offset=o + o_xyz).reshape(snf, nv, 4)
        all_v = raw_i16[:, :, :3].astype(np.float32) / 64.0
        raw_u8 = np.frombuffer(d, dtype=np.uint8, count=snf * nv * 8, offset=o + o_xyz).reshape(snf, nv, 8)
        lat = raw_u8[:, :, 6].astype(np.float32) * scale_2pi
        lng = raw_u8[:, :, 7].astype(np.float32) * scale_2pi
        sin_lng = np.sin(lng)
        all_n = np.stack([sin_lng * np.cos(lat), sin_lng * np.sin(lat), np.cos(lng)], axis=-1).astype(np.float32)
        surfaces.append(dict(name=sname, shader=shader, tris=tris, st=st, all_v=all_v, all_n=all_n))
        o += o_end
    return dict(name=name_b.split(b"\0", 1)[0].decode("ascii", "replace"), nframes=nf, frame_names=fnames, surfaces=surfaces)


def try_rigid_fit_fast(m):
    nf = m["nframes"]
    if nf < 12:
        return None
    P0 = np.vstack([s["all_v"][0].astype(np.float64) for s in m["surfaces"]])
    if len(P0) < 12:
        return None
    c0 = P0.mean(axis=0)
    X = P0 - c0
    if np.linalg.matrix_rank(X, tol=1e-2) < 3:
        return None
    mats = np.zeros((nf, 12), dtype="<f4")
    mats[0] = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
    for f in range(1, nf):
        Pf = np.vstack([s["all_v"][f].astype(np.float64) for s in m["surfaces"]])
        cf = Pf.mean(axis=0)
        Y = Pf - cf
        A, _, _, _ = np.linalg.lstsq(X, Y, rcond=None)
        t = cf - c0 @ A
        if float(np.max(np.abs((P0 @ A + t) - Pf))) > 0.05:
            return None
        mats[f, 0:3] = A[0, :]
        mats[f, 3:6] = A[1, :]
        mats[f, 6:9] = A[2, :]
        mats[f, 9:12] = t
    return mats


def parse_mdl_bytes(d):
    h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
    assert h[0] == b"IDPO" and h[1] == 6
    scale = np.array(h[2:5], dtype=np.float32)
    trans = np.array(h[5:8], dtype=np.float32)
    nsk, sw, sh, nvo, nt, nf = h[12:18]
    o = 84
    skins8 = []
    for _ in range(nsk):
        kind = struct.unpack_from("<i", d, o)[0]
        if kind == 0:
            skins8.append(np.frombuffer(d, np.uint8, sw * sh, o + 4).reshape(sh, sw).copy())
            o += 4 + sw * sh
        else:
            nb = struct.unpack_from("<i", d, o + 4)[0]
            o += 8 + nb * 4
            skins8.append(np.frombuffer(d, np.uint8, sw * sh, o).reshape(sh, sw).copy())
            o += nb * sw * sh
    st = np.frombuffer(d, "<i4", nvo * 3, o).reshape(nvo, 3)
    o += nvo * 12
    tri = np.frombuffer(d, "<i4", nt * 4, o).reshape(nt, 4)
    o += nt * 16
    names, pos_u8, nrm_u8 = [], [], []
    for _ in range(nf):
        kind = struct.unpack_from("<i", d, o)[0]
        if kind == 0:
            o += 12
            names.append(d[o:o + 16].split(b"\0", 1)[0].decode("ascii", "replace").strip())
            o += 16
            v = np.frombuffer(d, np.uint8, nvo * 4, o).reshape(nvo, 4)
            o += nvo * 4
        else:
            nb = struct.unpack_from("<i", d, o + 4)[0]
            o += 16 + nb * 4 + 12
            names.append(d[o:o + 16].split(b"\0", 1)[0].decode("ascii", "replace").strip())
            o += 16
            v = np.frombuffer(d, np.uint8, nvo * 4, o).reshape(nvo, 4)
            o += nvo * 4 + (nb - 1) * (28 + nvo * 4)
        pos_u8.append(v[:, :3])
        nrm_u8.append(v[:, 3])

    key, vmap, uv, tris = {}, [], [], []
    for front, a, b, c in tri.tolist():
        t = []
        for v in (a, b, c):
            back = int(st[v, 0] != 0 and not front)
            kk = (v, back)
            if kk not in key:
                key[kk] = len(vmap)
                vmap.append(v)
                s_px = st[v, 1] + back * (sw // 2)
                t_px = st[v, 2]
                uv.append(((s_px + 0.5) / sw, (t_px + 0.5) / sh))
            t.append(key[kk])
        tris.append(t)

    vmap_np = np.asarray(vmap, dtype=np.int32)
    pos_stack = np.stack(pos_u8, axis=0)[:, vmap_np, :].astype(np.float32) * scale[None, None, :] + trans[None, None, :]
    nrm_idx = np.clip(np.stack(nrm_u8, axis=0)[:, vmap_np], 0, len(ANORM_F32) - 1)
    nrm_stack = ANORM_F32[nrm_idx]
    return dict(sw=sw, sh=sh, nv=len(vmap), nt=nt, nf=nf, names=names,
                uv=np.asarray(uv, dtype="<f4"), tris=np.asarray(tris, dtype=np.int32),
                all_v=pos_stack, all_n=nrm_stack, skins8=skins8)


def parse_spr_bytes(d, label=""):
    magic, ver, tp, rad, mw, mh, nf = struct.unpack_from("<4siifiii", d, 0)
    assert magic == b"IDSP", label
    o = 36
    frames = []
    for _ in range(nf):
        grp = struct.unpack_from("<i", d, o)[0]
        assert grp == 0, f"Sprite group unsupported in {label}"
        ox, oy, fw, fh = struct.unpack_from("<iiii", d, o + 4)
        o += 20
        if ver == 32:
            rgba = np.frombuffer(d, np.uint8, fw * fh * 4, o).reshape(fh, fw, 4).copy()
            o += fw * fh * 4
        else:
            idx = np.frombuffer(d, np.uint8, fw * fh, o).reshape(fh, fw)
            o += fw * fh
            rgba = np.zeros((fh, fw, 4), dtype=np.uint8)
            mask = idx != 255
            rgba[mask, :3] = PALETTE_U8[idx[mask]]
            rgba[mask, 3] = 255
        frames.append(Image.fromarray(rgba, "RGBA"))
    return dict(ver=ver, type=tp, mw=mw, mh=mh, nf=nf, frames=frames)


def auto_clips_from_names(names, nf, default_fps=12.0):
    if nf <= 1:
        return [dict(id="static", label="🗿 Static Mesh (Frame 0)", start=0, count=1, fps=10.0, lie=True)]
    if nf == 259:
        return [
            dict(id="stand", label="🧍 Stand (5f)", start=12, count=5, fps=10.0),
            dict(id="run", label="🏃 Run (6f)", start=6, count=6, fps=12.0),
            dict(id="shotatt", label="🔫 Shoot (6f)", start=113, count=6, fps=12.0),
            dict(id="pain", label="💢 Pain (6f)", start=29, count=6, fps=10.0),
            dict(id="all", label="🎬 All 259 Poses", start=0, count=259, fps=14.0),
        ]
    if nf == 143:
        return [
            dict(id="stand", label="🧍 Stand (5f)", start=12, count=5, fps=9.0),
            dict(id="run", label="🏃 Rocket Run (6f)", start=6, count=6, fps=11.0),
            dict(id="shot", label="🔫 Shoot (6f)", start=113, count=6, fps=11.0),
            dict(id="axe", label="🪓 Axe Swing (6f)", start=119, count=6, fps=11.0),
            dict(id="death", label="💀 Death (11f)", start=50, count=11, fps=10.0),
            dict(id="all", label="🎬 All 143f", start=0, count=143, fps=11.0),
        ]
    groups = []
    for i, raw_nm in enumerate(names):
        base = re.sub(r"[_\-\s]*\d+$", "", raw_nm or "").strip().lower()
        if not base or base in ("f", "frame"):
            base = "anim"
        if groups and groups[-1][0] == base:
            groups[-1][2] += 1
        else:
            groups.append([base, i, 1])
    if 1 < len(groups) <= 14:
        clips = []
        for base, st, cnt in groups:
            if base == "gone" and cnt == 1:
                continue
            clips.append(dict(id=f"{base}_{st}", label=f"▶ {base.replace('_', ' ').title()} ({cnt}f)", start=st, count=cnt, fps=default_fps))
        clips.append(dict(id="all", label=f"🎬 All {nf}f", start=0, count=nf, fps=default_fps))
        return clips
    return [dict(id="all", label=f"🎬 All {nf} Frames", start=0, count=nf, fps=default_fps)]


def parse_all_shaders(vfs):
    shaders = {}
    for k, real in sorted(vfs.real_path.items()):
        if k.startswith("scripts/") and k.endswith(".shader"):
            txt = vfs.read(k).decode("utf-8", errors="replace")
            clean = re.sub(r"//.*", "", txt)
            pos = 0
            while True:
                m = re.search(r"([^\s\{\}]+)\s*\{", clean[pos:])
                if not m:
                    break
                sh_name = m.group(1).strip().lower()
                bstart = pos + m.end()
                depth, i = 1, bstart
                while i < len(clean) and depth > 0:
                    if clean[i] == "{":
                        depth += 1
                    elif clean[i] == "}":
                        depth -= 1
                    i += 1
                shaders[sh_name] = clean[bstart:i - 1]
                pos = i
    return shaders


# --------------------------------------------------------------------------- Metadata & Curated Titles/Clips Catalog
HERO_META = {
    # CARS, BUSES, SUPERCAR & AIRCRAFT
    "progs/pink_supercar.md3": dict(
        order=1, badge="EXOTIC V12 · 64f + GLB", title="Hot-Pink V12 Exotic Supercar + Roof Webcam",
        desc="14-surface, 64-frame metallic hot-pink V12 supercar with scanning roof webcam, opening scissor doors, pop-up hood, glowing LEDs & turbo boost!",
        clips=[
            dict(id="doors", label="🦋 Scissor Doors & Hood (16f)", start=32, count=16, fps=12.0, lie=True),
            dict(id="boost", label="🔥 Turbo Flame Boost (16f)", start=48, count=16, fps=16.0),
            dict(id="cruise", label="🏎️ Cruise Roll (16f)", start=16, count=16, fps=14.0),
            dict(id="idle", label="📷 Idle Webcam Scan (16f)", start=0, count=16, fps=10.0, lie=True),
            dict(id="all", label="🎬 All 64f", start=0, count=64, fps=14.0),
        ],
    ),
    "progs/veh_van.md3": dict(
        order=2, badge="WALK-IN VAN · 4 SKINS + GLB", title="Driveable Walk-In Ram ProMaster Cargo Van",
        desc="36-frame driveable white cargo van with walk-in rear doors, full cab/cargo interior & 4 skins (Clean, Burned, Interior Cutaway)!",
    ),
    "progs/veh_schoolbus.md3": dict(
        order=3, badge="SCHOOL BUS · 36f + GLB", title="Driveable Yellow Bakersfield School Bus",
        desc="36-frame full-size driveable yellow school bus with rolling/steering wheels, glowing headlamps & Clean / Scorched Burned skins!",
    ),
    "progs/veh_hdtruck.md3": dict(
        order=4, badge="HEAVY RIG · 36f + GLB", title="Driveable Heavy-Duty Dually Commercial Truck",
        desc="36-frame heavy-duty commercial truck with steering front axle, glowing cab lights & Clean / Scorched Burned skins!",
    ),
    "progs/veh_gtcar.md3": dict(
        order=5, badge="GT MUSCLE · 36f + GLB", title="Driveable Street GT Sports Muscle Car",
        desc="36-frame widebody street GT sports car with rolling/steering wheels, glowing tailbars & Clean / Burned skins!",
    ),
    "progs/veh_truck.md3": dict(
        order=6, badge="PICKUP · 36f + GLB", title="Driveable Pickup Truck (Clean & Burned Skins)",
        desc="36-frame driveable pickup truck with open bed, rolling/steering wheels & Clean / Scorched Burned skins.",
    ),
    "progs/veh_sedan.md3": dict(
        order=7, badge="SEDAN · 36f + GLB", title="Driveable 4-Door Street Sedan (Clean & Burned)",
        desc="36-frame driveable 4-door street sedan with steering front wheels & Clean / Scorched Burned skins.",
    ),
    "progs/veh_coupe.md3": dict(
        order=8, badge="COUPE · 36f + GLB", title="Driveable 2-Door Sports Coupe (Clean & Burned)",
        desc="36-frame driveable 2-door fastback sports coupe with steering wheels & Clean / Scorched Burned skins.",
    ),
    "progs/fox/get_bus.md3": dict(
        order=9, badge="GET TRANSIT BUS · MD3", title="Golden Empire Transit (GET) Downtown City Bus",
        desc="Custom Bakersfield Golden Empire Transit city bus with glowing destination marquee & interior windows from Fox/Downtown.",
    ),
    "progs/jesskart.spr32": dict(
        order=10, badge="8-DIR SPR32 · 56f", title="JESS-KART 360° Nitro Go-Kart Chaser (.SPR32)",
        desc="56-frame 8-direction SPR32 go-kart sprite (8 idle angles + 8×6 driving frames)—drag horizontally to spin 360°!",
    ),
    "progs/jesskart.md3": dict(
        order=11, badge="16-SKIN CARD · MD3", title="JESS-KART 16-Angle Turnaround Billboard (.MD3)",
        desc="16-skin camera-reactive JESS-KART MD3 card with animated front burnout shader!",
    ),
    "progs/skyveh_v3.md3": dict(
        order=12, badge="SKY-CHARIOT · 56f", title="The Podracer Sky-Chariot & Autogyro (skyveh_v3)",
        desc="Screaming Big-Ears tractor pod towing the ProMaster chariot on twin chrome booms with overhead Pink Lady autogyro mast!",
    ),
    "vault/progs/skyveh_v1.md3": dict(
        order=13, badge="VAULT SKY-VEH · 56f", title="The Ear-nithopter Sky-Galleon (skyveh_v1)",
        desc="Archived ProMaster airship gondola with flapping giant ear-wings & 3D Pink Lady prow figurehead.",
    ),
    "vault/progs/skyveh_v2.md3": dict(
        order=14, badge="VAULT SKY-VEH · 56f", title="The Valkyrie V-22 Tilt-Rotor Dropship (skyveh_v2)",
        desc="Archived heavy dropship with wingtip Osprey chrome nacelles spinning white-dish tire rotors.",
    ),
    "vault/progs/skyveh_v4.md3": dict(
        order=15, badge="VAULT SKY-VEH · 56f", title="The Biomech Mecha-Wyvern Sky-Dragon (skyveh_v4)",
        desc="Archived sky-dragon with barn-door Beetle Elytra wing-shells, arched chrome neck & tail-rotor stinger.",
    ),
    "progs/van_walkin.md3": dict(
        order=16, badge="14-SURF ARCHITECTURE", title="Walk-In 6-Man LAN Van Architectural Mesh",
        desc="14-material walk-in cargo van interior/exterior mesh with chrome, headlamps, cloth seats & tinted glass.",
    ),

    # CUSTOM GUNS, VIEWMODELS, PICKUPS & PROJECTILES
    "progs/v_megaman.md3": dict(
        order=1, badge="MEGA-SLINGER · 37f", title="Mega-Slinger Launcher (First-Person Viewmodel)",
        desc="37-frame heavy launcher cradle holding the lathed Mega-Man chrome bar & spinning white-dish tires with glowing PSI gauge!",
        pov=True, az=2.45, el=0.22,
        clips=[
            dict(id="all", label="🎬 Full 37f Sequence", start=0, count=37, fps=14.0),
            dict(id="idle", label="⚙ Idle Wheel Spin (8f)", start=0, count=8, fps=10.0),
            dict(id="fire", label="💥 Launch & Reload (29f)", start=8, count=29, fps=16.0),
        ],
    ),
    "progs/v_wewcannon.md3": dict(
        order=2, badge="WEW CANNON · 48f + GLB", title='WEW Cannon CRT Bend-Beam Launcher (Viewmodel)',
        desc="48-frame brushed-silver WEW Cannon with animated live CRT screen, glowing plasma core & 2 skins (+ original high-poly .GLB)!",
        pov=True, az=2.45, el=0.22,
    ),
    "progs/g_wewcannon.md3": dict(
        order=3, badge="PICKUP + GLB", title="WEW Cannon (Spinning World Pickup MD3)",
        desc="High-detail world pickup mesh for the WEW Cannon with live CRT screen & 2 skins (+ original .GLB).",
    ),
    "progs/v_mysterybox.md3": dict(
        order=4, badge="MYSTERY BOX · 220f + GLB", title="Haunted Glass Mystery Box Weapon (Viewmodel)",
        desc="220-frame articulated hand holding the translucent haunted glass Mystery Box with 3D ghost & swirling crystal core!",
        pov=True, az=2.55, el=0.20,
    ),
    "progs/proj_mysterybox.md3": dict(
        order=5, badge="PROJECTILE · 32f + GLB", title="Thrown Haunted Mystery Box Projectile",
        desc="32-frame tumbling haunted glass Mystery Box projectile that unleashes Bakersfield NPC stampedes on impact!",
    ),
    "progs/v_milky.md3": dict(
        order=6, badge="MILKY GUN · 3 VIDEO SKINS", title="Milky Gun — Giant Hand Holding Pink Lady (Viewmodel)",
        desc="First-person keyed-video Milky Gun with all 3 switchable animations: Idle Sway A, Idle Sway B & Open-Palm Hurl!",
        pov=True, defaultPov=True, az=3.14, el=0.06,
    ),
    "progs/v_pickle.md3": dict(
        order=7, badge="PICKLE SURPRISE · 120 SKINS", title="Pickle Surprise Choke-Squeeze & Whip Claw (Viewmodel)",
        desc="First-person armored bronze claw clutching Pickle Surprise: switch between 24fps Idle Clutch and Brutal Choke-Squeeze Whip Throw!",
        pov=True, defaultPov=True, az=3.14, el=0.05,
    ),
    "progs/v_netsend.md3": dict(
        order=8, badge="LOL.BAT · 60f", title='NetSend "LOL.BAT" 3.5" Floppy Disk Gun (Viewmodel)',
        desc="60-frame articulated hand fanning & flicking 3.5-inch 'LOL.BAT' floppy diskettes that deploy retro CRT PCs!",
        pov=True, az=2.55, el=0.22,
        clips=[
            dict(id="all", label="🎬 Full 60f Sequence", start=0, count=60, fps=15.0),
            dict(id="idle", label="💾 Idle Disk Fan (20f)", start=0, count=20, fps=12.0),
            dict(id="fire", label="🤾 Flick Floppy Disk (40f)", start=20, count=40, fps=18.0),
        ],
    ),
    "progs/v_laptop.md3": dict(
        order=9, badge="AOL HACKER · 34f", title="AOL Dial-Up 3D Hacker Laptop Gun (Viewmodel)",
        desc="34-frame 3D laptop displaying 'Hacking internet lag' + AOL 5.0 Dial-Up; firing whips in the left hand hammering 3D keys & bolts!",
        pov=True, az=2.78, el=0.22,
        clips=[
            dict(id="all", label="⚡ Idle + Fast Type & Zap (34f)", start=0, count=34, fps=13.0),
            dict(id="idle", label="💻 One-Hand Hold (12f)", start=0, count=12, fps=10.0),
            dict(id="shoot", label="⚡ Rapid Typing & Bolts (22f)", start=12, count=22, fps=16.0),
        ],
    ),
    "progs/ltg_v3d.md3": dict(
        order=10, badge="3D LAPTOP v2 · 34f", title="3D Hacker Laptop Gun (ltg_v3d Variant)",
        desc="34-frame 3D articulated Hacker Laptop viewmodel variant.",
        pov=True, az=2.78, el=0.22,
    ),
    "progs/ltg_view.md3": dict(
        order=11, badge="VIDEO WEAPON · 2 SKINS", title="Laptop Gun Video-Shader Viewmodel (Idle & 42fps Typing)",
        desc="Keyed-video Laptop Gun card with switchable Idle Sway and manic 42fps Rapid Typing skins!",
        pov=True, defaultPov=True, az=3.14, el=0.06,
    ),
    "progs/v_googun.md3": dict(
        order=12, badge="BIO-FOAM · 7f", title="Bio-Foam Goo Gun (First-Person Viewmodel)",
        desc="8-surface pressurized bio-foam sprayer with glowing side tank, hazard decals & 7-frame recoil kick.",
        pov=True, az=2.45, el=0.22,
    ),
    "progs/v_hammer.mdl": dict(
        order=13, badge="BONK HAMMER · 255f", title="Tiered Charge Bonk Warhammer (255-Frame Viewmodel)",
        desc="255-frame heavy two-handed warhammer featuring Low/Med/High charge tiers, air-dash lunge, pogo hop & flourish spins!",
        pov=True, az=2.55, el=0.22,
        clips=[
            dict(id="idle", label="🔨 Idle Sway (40f)", start=0, count=40, fps=14.0),
            dict(id="hi_hit", label="💥 High Tier Smash (19f)", start=40, count=19, fps=18.0),
            dict(id="dash", label="🚀 Air-Dash & Hop (18f)", start=59, count=18, fps=16.0),
            dict(id="med_hit", label="⚡ Med Tier Swing (19f)", start=77, count=19, fps=18.0),
            dict(id="spin", label="🌀 Flourish Inspect (69f)", start=186, count=69, fps=20.0),
            dict(id="all", label="🎬 All 255f", start=0, count=255, fps=18.0),
        ],
    ),
    "progs/v_srifle.mdl": dict(
        order=14, badge="SNIPER · 7f MDL", title="Scoped Laser-Sight Sniper Rifle (Viewmodel)",
        desc="7-frame scoped sniper rifle first-person viewmodel with laser-sight zoom & recoil.",
        pov=True, az=2.45, el=0.20,
    ),
    "progs/v_sledge.md3": dict(
        order=15, badge="WHACK-A-MOLE · 22f", title="Whack-a-Mole Shrink Sledgehammer (Viewmodel)",
        desc="22-frame sledgehammer viewmodel that bonks enemies down to 45% miniature size!",
        pov=True, az=2.50, el=0.20,
    ),
    "progs/v_paddle.md3": dict(
        order=16, badge="RALLY MASTER · 22f", title="Rally Master Ping-Pong Paddle (Viewmodel)",
        desc="22-frame table-tennis paddle viewmodel serving high-velocity ricochet ping-pong balls!",
        pov=True, az=2.60, el=0.20,
    ),
    "progs/v_hackmon.md3": dict(
        order=17, badge='"> HACKING" · 22f', title='Hack Attack "> HACKING" CRT Monitor (Viewmodel)',
        desc="19-surface CRT monitor held screen-toward-player with green phosphor '> HACKING' scanline terminal.",
        pov=True, az=2.85, el=0.16,
    ),
    "progs/v_robdob.mdl": dict(
        order=18, badge="ROB TRAP VM · 9f", title="Held Rob Dob Head Trap (Viewmodel)",
        desc="First-person held miniature Rob Dob head hovering in the lower-right corner and glancing back at you!",
        pov=True, az=2.82, el=0.18,
    ),
    "progs/v_span.mdl": dict(
        order=19, badge="ENGINEER · 5f MDL", title="Engineer Sentry Spanner Wrench (Viewmodel)",
        desc="5-frame heavy steel spanner wrench viewmodel used to construct, repair & upgrade Sentry Guns.",
        pov=True, az=2.50, el=0.22,
    ),
    "progs/fr_johnhand.spr32": dict(
        order=20, badge="JOHN WAVE · 49f SPR32", title="John Wave Casting Hand (49-Frame Viewmodel Sprite)",
        desc="49-frame 32-bit RGBA sprite viewmodel for the John Wave tidal-wave weapon—toggle 1st-Person POV or 2D Pixel View!",
        pov=True, defaultPov=True, az=3.14, el=0.05,
    ),
    "progs/jetpack.md3": dict(
        order=21, badge="FLIGHT GEAR · 16f", title="JP-02 Twin-Turbine Wearable Rocket Jetpack",
        desc="9-surface wearable rocket pack with brushed titanium tanks, cyan plasma window, PSI dial & 4-frame shock-diamond plumes!",
        az=2.55, el=0.16,
        clips=[
            dict(id="thrust", label="🔥 Afterburner Thrust (8f)", start=0, count=8, fps=15.0),
            dict(id="idle", label="🕯 Standby Pilot Flame (8f)", start=8, count=8, fps=10.0, lie=True),
            dict(id="all", label="🎬 All 16f", start=0, count=16, fps=14.0),
        ],
    ),
    "progs/megaman.md3": dict(
        order=22, badge="MEGA-MAN BOT · 16f + GLB", title='Autonomous Wheeled "Mega Man" Contraption',
        desc="16-frame two-wheeled Segway-pipe contraption that steers, honks, hops & leaps onto enemies (+ original .GLB)!",
    ),
    "progs/netsend_pc.md3": dict(
        order=23, badge="DEPLOYABLE · 7 SKINS · 50f", title="NetSend Retro CRT Desktop PC (All 7 Screen Skins)",
        desc="50-frame deployable retro beige PC tower & CRT monitor spitting floppy disks across all 7 boot/noise/LOL.BAT screen states!",
    ),
    "vault/progs/girl.md3": dict(
        order=24, badge="VAULT · 26K-TRI HULL · 8f", title="Girlfriend Gun Chaser (26,000-Tri 3D Video Hull)",
        desc="Archived full-body 3D human chaser reconstructed from video across 5 MD3 surfaces with an 8-frame running cycle.",
        az=-0.28, el=0.18,
    ),
    "vault/progs/v_banana.md3": dict(
        order=25, badge="VAULT · BANANA BAZOOKA", title="Archived Yellow Banana Tube Bazooka (Viewmodel)",
        desc="Archived 16-frame procedural yellow cylindrical bazooka viewmodel with idle sway & recoil kick.",
        pov=True, az=2.40, el=0.22,
    ),

    # 360° SPRITES, SCULPTED HEADS & CHARACTERS
    "progs/wheelman.spr32": dict(
        order=1, badge="SPHERICAL 360° · 744f", title="Wheelman Master 360° Contraption Rider (744 Frames!)",
        desc="Spherical 8-direction + overhead/underneath + Fire-Wheels burnout + Long-Bar steamroller + 4 escalating 360° explosion tiers!",
        turnDirs=8,
        clips=[
            dict(id="roll", label="🛞 360° Full-Throttle Roll (8×12f)", start=0, count=12, fps=18.0, sprMode=dict(base=8, dirs=8, fpd=12, fps=18.0)),
            dict(id="fire", label="🔥 Stunt 1: Fire-Wheels Burnout (8×6f)", start=0, count=6, fps=15.0, sprMode=dict(base=648, dirs=8, fpd=6, fps=15.0)),
            dict(id="longbar", label="📏 Stunt 2: Steamroller Long-Bar (8×6f)", start=0, count=6, fps=15.0, sprMode=dict(base=696, dirs=8, fpd=6, fps=15.0)),
            dict(id="scream", label="😱 360° Mid-Air Scream (8×6f)", start=0, count=6, fps=16.0, sprMode=dict(base=104, dirs=8, fpd=6, fps=16.0)),
            dict(id="boom3", label="💥 Tier-4 Mega 360° Explosion (8×14f)", start=0, count=14, fps=14.0, sprMode=dict(base=536, dirs=8, fpd=14, fps=14.0)),
            dict(id="boom0", label="💥 Tier-1 360° Explosion (8×14f)", start=0, count=14, fps=14.0, sprMode=dict(base=200, dirs=8, fpd=14, fps=14.0)),
            dict(id="above", label="🦅 Overhead View Roll (8×3f)", start=0, count=3, fps=12.0, sprMode=dict(base=152, dirs=8, fpd=3, fps=12.0)),
            dict(id="idle", label="🧍 360° Eye-Level Idle (8×1f)", start=0, count=1, fps=8.0, sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
        ],
    ),
    "progs/wheelman_dance.spr32": dict(
        order=2, badge="8 DANCES · 360° · 736f", title="Wheelman 8 Crazy 360° Dances & Chrome Robot Morph (736f)",
        desc="All 8 8-direction 360° Wheelman dances: Stuck-In-Wheels, Overhead Press, Maniac Crash, Can-Can, Hurricane Spin, Deadlift, Yeet & Chrome Robot!",
        turnDirs=8,
        clips=[
            dict(id="d8", label="🤖 #8 Morph Chrome Robot (8×14f)", start=0, count=14, fps=12.0, sprMode=dict(base=624, dirs=8, fpd=14, fps=12.0)),
            dict(id="d5", label="🌪️ #5 Hurricane Bar Spin (8×12f)", start=0, count=12, fps=14.0, sprMode=dict(base=336, dirs=8, fpd=12, fps=14.0)),
            dict(id="d3", label="🤪 #3 Maniac Crash Dance (8×12f)", start=0, count=12, fps=14.0, sprMode=dict(base=160, dirs=8, fpd=12, fps=14.0)),
            dict(id="d1", label="🛞 #1 Stuck-In-Wheels (8×10f)", start=0, count=10, fps=12.0, sprMode=dict(base=0, dirs=8, fpd=10, fps=12.0)),
            dict(id="d2", label="🏋️ #2 Overhead Rig Press (8×10f)", start=0, count=10, fps=12.0, sprMode=dict(base=80, dirs=8, fpd=10, fps=12.0)),
            dict(id="d4", label="💃 #4 Can-Can Kick (8×10f)", start=0, count=10, fps=12.0, sprMode=dict(base=256, dirs=8, fpd=10, fps=12.0)),
            dict(id="d6", label="💪 #6 Heavy Deadlift (8×12f)", start=0, count=12, fps=12.0, sprMode=dict(base=432, dirs=8, fpd=12, fps=12.0)),
            dict(id="d7", label="🚀 #7 Yeet The Rig (8×12f)", start=0, count=12, fps=13.0, sprMode=dict(base=528, dirs=8, fpd=12, fps=13.0)),
        ],
    ),
    "progs/daniel.spr32": dict(
        order=3, badge="8-DIR NPC · 344f", title='Daniel "4AM Table Mover" 360° Boss NPC (344f)',
        desc="344-frame 8-direction Daniel sprite: Fast Run, 4AM Table Carry, 'CCC!' Grin, 'SHAAA!' Rage, Webcam Squint, Sorry Panic & LAN Station!",
        turnDirs=8,
        clips=[
            dict(id="table", label="🪑 4AM Table Carry (8×6f)", start=0, count=6, fps=11.0, sprMode=dict(base=56, dirs=8, fpd=6, fps=11.0)),
            dict(id="run", label="🏃 Fast Run (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=8, dirs=8, fpd=6, fps=12.0)),
            dict(id="ccc", label="😁 'CCC!' Grin (8×6f)", start=0, count=6, fps=10.0, sprMode=dict(base=104, dirs=8, fpd=6, fps=10.0)),
            dict(id="shaaa", label="🤬 'SHAAA!' Rage (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=152, dirs=8, fpd=6, fps=12.0)),
            dict(id="cam", label="📷 Webcam Squint (8×6f)", start=0, count=6, fps=10.0, sprMode=dict(base=200, dirs=8, fpd=6, fps=10.0)),
            dict(id="sorry", label="😰 Sorry Panic (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=248, dirs=8, fpd=6, fps=12.0)),
            dict(id="lan", label="🖥️ 360° LAN Station (8×6f)", start=0, count=6, fps=10.0, sprMode=dict(base=296, dirs=8, fpd=6, fps=10.0)),
            dict(id="idle", label="🧍 360° Idle (8×1f)", start=0, count=1, fps=8.0, sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
        ],
    ),
    "progs/david.spr32": dict(
        order=4, badge="8-DIR NPC · 344f", title='David "777 Jackpot & Money Bag" 360° NPC (344f)',
        desc="344-frame 8-direction David sprite: Money Bag Flex, Heist Sprint, Slot Machine Spin, 777 Jackpot Celebration & Bust!",
        turnDirs=8,
        clips=[
            dict(id="money", label="💰 Money Bag Flex (8×6f)", start=0, count=6, fps=11.0, sprMode=dict(base=104, dirs=8, fpd=6, fps=11.0)),
            dict(id="heist", label="🏃‍♂️💨 Heist Sprint (8×6f)", start=0, count=6, fps=14.0, sprMode=dict(base=152, dirs=8, fpd=6, fps=14.0)),
            dict(id="jackpot", label="🎰 777 Jackpot Win! (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=248, dirs=8, fpd=6, fps=12.0)),
            dict(id="slot", label="🎲 Slot Spin (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=200, dirs=8, fpd=6, fps=12.0)),
            dict(id="bust", label="💸 Slot Bust (8×6f)", start=0, count=6, fps=10.0, sprMode=dict(base=296, dirs=8, fpd=6, fps=10.0)),
            dict(id="turbo", label="⚡ Turbo Sprint (8×6f)", start=0, count=6, fps=14.0, sprMode=dict(base=56, dirs=8, fpd=6, fps=14.0)),
            dict(id="run", label="🏃 Fast Run (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=8, dirs=8, fpd=6, fps=12.0)),
            dict(id="idle", label="🧍 360° Idle (8×1f)", start=0, count=1, fps=8.0, sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
        ],
    ),
    "progs/robeguy.spr32": dict(
        order=5, badge="FLAMINGO FIEND · 336f", title="Bathrobe Flamingo-Laser Berserker 360° NPC (336f)",
        desc="336-frame 8-direction Bathrobe Guy: Chest-Hair Laser, Dual Flamingo & Coffee, Flamingo Whisperer, Berserker Run & Feather Explosion!",
        turnDirs=8,
        clips=[
            dict(id="laser", label="⚡ Chest-Hair Laser (8×12f)", start=0, count=12, fps=14.0, sprMode=dict(base=120, dirs=8, fpd=12, fps=14.0)),
            dict(id="dual", label="🦩☕ Dual Flamingo & Coffee (8×12f)", start=0, count=12, fps=13.0, sprMode=dict(base=216, dirs=8, fpd=12, fps=13.0)),
            dict(id="whisper", label="🦩 Flamingo Whisperer (8×8f)", start=0, count=8, fps=11.0, sprMode=dict(base=56, dirs=8, fpd=8, fps=11.0)),
            dict(id="run", label="🏃 Berserker Run (8×6f)", start=0, count=6, fps=13.0, sprMode=dict(base=8, dirs=8, fpd=6, fps=13.0)),
            dict(id="gib", label="💥 Feather & Gib Explosion (24f)", start=0, count=24, fps=14.0, sprMode=dict(base=312, dirs=1, fpd=24, fps=14.0)),
            dict(id="idle", label="🧍 360° Idle (8×1f)", start=0, count=1, fps=8.0, sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
        ],
    ),
    "progs/bryan.spr32": dict(
        order=6, badge="DEMON HUNTER · 264f", title="Bryan Metal-Detector & 3-Demon Surge 360° NPC (264f)",
        desc="264-frame 8-direction Bryan sprite: Metal-Detector Scan, Demon Whirl, 3-Demon Surge & 32-frame Hell Portal Drag-Down Death!",
        turnDirs=8,
        clips=[
            dict(id="scan", label="📡 Metal-Detector Scan (8×6f)", start=0, count=6, fps=11.0, sprMode=dict(base=56, dirs=8, fpd=6, fps=11.0)),
            dict(id="surge", label="👹 3-Demon Surge (8×8f)", start=0, count=8, fps=13.0, sprMode=dict(base=168, dirs=8, fpd=8, fps=13.0)),
            dict(id="whirl", label="🌀 Demon Whirl (8×8f)", start=0, count=8, fps=13.0, sprMode=dict(base=104, dirs=8, fpd=8, fps=13.0)),
            dict(id="portal", label="🔥 Hell Portal Drag-Down (32f)", start=0, count=32, fps=14.0, sprMode=dict(base=232, dirs=1, fpd=32, fps=14.0)),
            dict(id="run", label="🏃 Sprint (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=8, dirs=8, fpd=6, fps=12.0)),
            dict(id="idle", label="🧍 360° Idle (8×1f)", start=0, count=1, fps=8.0, sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
        ],
    ),
    "progs/greensuit_wheelman.spr32": dict(
        order=7, badge="GREEN-SUIT · 256f + GLB", title="Green-Suit Ab-Roller Wheelman 360° Sprite (256f + .GLB)",
        desc="256-frame 8-direction Green-Suit Wheelman: Seated Cruise, Scream Turbo, Crane Point, Ab-Roller Plank & 360° Gib Explosion (+ source .GLB)!",
        turnDirs=8,
        clips=[
            dict(id="cruise", label="🛞 Seated Cruise (8×6f)", start=0, count=6, fps=13.0, sprMode=dict(base=8, dirs=8, fpd=6, fps=13.0)),
            dict(id="turbo", label="😱 Scream Turbo (8×6f)", start=0, count=6, fps=15.0, sprMode=dict(base=56, dirs=8, fpd=6, fps=15.0)),
            dict(id="plank", label="🏋️ Ab-Roller Plank (8×6f)", start=0, count=6, fps=13.0, sprMode=dict(base=152, dirs=8, fpd=6, fps=13.0)),
            dict(id="crane", label="👉 Crane Point (8×6f)", start=0, count=6, fps=12.0, sprMode=dict(base=104, dirs=8, fpd=6, fps=12.0)),
            dict(id="gib", label="💥 360° Gib Explosion (8×7f)", start=0, count=7, fps=12.0, sprMode=dict(base=200, dirs=8, fpd=7, fps=12.0)),
            dict(id="idle", label="🧍 360° Idle (8×1f)", start=0, count=1, fps=8.0, sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
        ],
    ),
    "progs/pickle.md3": dict(
        order=8, badge="3D DIVA + 64 SKINS", title="Pickle Surprise 3D Diva Dance & 16-Angle Turnaround",
        desc="36-frame deforming 3D ribbon mesh (Wacky-Waving Diva Dance + Pre-Blast Balloon Swell) × 4 full 16-angle facial expressions!",
    ),
    "progs/pinklady.md3": dict(
        order=9, badge="16-ANGLE + 34f BOUNCE", title="Hot-Pink Lady 16-Angle Turnaround & Front Bounce",
        desc="In-game Pink Lady billboard card packing both the 34-frame ping-pong front bounce and all 16 360° turnaround angles!",
    ),
    "progs/mm_suit_rider.md3": dict(
        order=10, badge="3D RIDER · 60f", title="Suit Guy Riding Mega-Man Contraption (60f)",
        desc="60-frame articulated 3D Suit Guy balanced atop a twin-wheel Mega-Man rig with drive, boost, charge & wheelie-slam clips!",
    ),
    "progs/mm_squat_rider.md3": dict(
        order=11, badge="3D RIDER · 2 SKINS", title="Squat Rider on Mega-Man Rig (Neutral & Grin Skins)",
        desc="60-frame low-slung 3D Squat Rider gripping the Mega-Man axle with switchable Neutral & Manic Grin facial skins!",
    ),
    "progs/john_bird_head.md3": dict(
        order=12, badge="WINGED HEAD · 72f", title="Winged Flying John Bird-Head + Breezy Hair (72f)",
        desc="72-frame 14,560-triangle 3D sculpted John head with flapping feathered bird wings and wind-blown hair!",
    ),
    "progs/ltg_head.md3": dict(
        order=13, badge="24-VIEW MD3 + AURA", title="Laptop Gun Summoned Ear-Head (24-Angle Turntable + Aura)",
        desc="24-surface camera-reactive MD3 head paired with its 8-frame additive Wi-Fi & Ethernet cable aura!",
    ),
    "progs/floathead.mdl": dict(
        order=14, badge="MONSTER · 2 SKINS · 20f", title="Rob Dob Floating Head Monster (Closed & Screaming Jaw)",
        desc="20-frame hovering 3D Rob Dob monster with articulated jaw drop & automatic screaming mouth skin!",
        az=-0.28, el=0.14, frameSkin=8,
    ),
    "progs/bigears.md3": dict(
        order=15, badge="3D SCULPT · 5,600t", title="Giant-Eared Screaming 3D Floating Head",
        desc="Watertight 4,562-vertex / 5,600-triangle 3D head carved from 48 turntable views with sculpted giant cupped ears!",
        az=-0.34, el=0.10,
    ),
    "progs/johnhead3d.md3": dict(
        order=16, badge="3D SCULPT · JOHN", title="John Wave Screaming Flying 3D Head",
        desc="4,837-vertex 3D visual-hull head carved from 113 green-screen turntable frames!",
        az=-0.28, el=0.14,
    ),
    "vault/progs/suitguy.mdl": dict(
        order=30, badge="VAULT PLAYER · 143f", title="Suit Guy (143-Frame Custom Quake Player Model)",
        desc="Archived full 143-frame Quake player model built from front & back studio photos in a dark business suit + TGA skin.",
        az=-0.28, el=0.18,
    ),
    "vault/progs/robeguy.mdl": dict(
        order=31, badge="VAULT PLAYER · 143f", title="Bathrobe Guy (143-Frame Custom Quake Player Model)",
        desc="Archived full 143-frame Quake player model built from front & back photos in a white bathrobe + TGA skin.",
        az=-0.28, el=0.18,
    ),
    "vault/progs/wifeguy.mdl": dict(
        order=32, badge="VAULT PLAYER · 143f", title="Wife (143-Frame Custom Quake Player Model)",
        desc="Archived full 143-frame Quake player model built from front & back photos + high-color TGA skin.",
        az=-0.28, el=0.18,
    ),
    "progs/bk_tvscr.md3": dict(
        order=1, badge="37 LIVE TV CHANNELS!", title="B-LAN Big-Screen CRT/Plasma TV (All 37 BKTV Channels!)",
        desc="Interactive B-LAN television screen with all 37 switchable BKTV video channels playing live animated frames!",
        defaultSkin=1, noSpin=True, az=1.57, el=0.06,
    ),
    "progs/v_mm_cannon.md3": dict(
        order=1.5, badge="MEGA-CANNON · 45f", title="Mega-Man Heavy Shoulder Cannon (Viewmodel)",
        desc="45-frame heavy shoulder launcher firing spinning Mega-Man contraptions with glowing recoil FX.",
        pov=True, az=2.45, el=0.22,
    ),
    "progs/v_mm_slingshot.md3": dict(
        order=1.6, badge="SLINGSHOT · 45f", title="Mega-Man Giant Elastic Slingshot (Viewmodel)",
        desc="45-frame two-handed slingshot stretching and launching full-size Mega-Man rigs.",
        pov=True, az=2.45, el=0.22,
    ),
    "progs/v_mm_bow.md3": dict(
        order=1.7, badge="CROSSBOW · 45f", title="Mega-Man Tactical Crossbow Launcher (Viewmodel)",
        desc="45-frame heavy crossbow cradle loaded with a spinning Mega-Man bar & white-dish wheels.",
        pov=True, az=2.45, el=0.22,
    ),
    "progs/v_mm_handthrow.md3": dict(
        order=1.8, badge="HAND HURL · 45f", title="Mega-Man Bare-Handed Gauntlet Throw (Viewmodel)",
        desc="45-frame Ranger hands gripping and hurling a live spinning Mega-Man contraption.",
        pov=True, az=2.45, el=0.22,
    ),
    "progs/grenade.mdl": dict(
        order=18.5, badge="HEAD GRENADE · MDL", title="John Wave 3D Sculpted Head Grenade",
        desc="1,792-triangle custom 3D sculpted John head grenade replacing standard pineapple grenades.",
        az=-0.30, el=0.14,
    ),
    "progs/turrgun.mdl": dict(
        order=19.5, badge="SENTRY TURRET · 9f", title="Automated Dual-Barrel Engineer Sentry Turret",
        desc="9-frame automated dual-barrel tracking sentry gun deployed with the Engineer Spanner.",
    ),
    "progs/g_srifle.mdl": dict(
        order=14.5, badge="PICKUP · MDL", title="Scoped Sniper Rifle (World Pickup)",
        desc="Spinning world pickup mesh for the Scoped Laser-Sight Sniper Rifle.",
    ),
    "progs/bklan/sr_vehicle_forklift_orange_a01.md3": dict(
        order=17, badge="FORKLIFT · MD3", title="B-LAN Warehouse Counterbalance Forklift",
        desc="Heavy industrial orange warehouse forklift from B-LAN 2001.",
    ),
    "progs/gw_horse.md3": dict(
        order=2, badge="CASINO STATUE · MD3", title="Golden West Casino Rearing Bronze Horse",
        desc="3,692-triangle rearing bronze horse statue on rocky plinth outside Golden West Casino.",
    ),
    "progs/fedora.md3": dict(
        order=3, badge="HAT · MD3", title="Signature Red Fedora Hat",
        desc="960-triangle crimson fedora hat wearable/prop mesh.",
    ),
    "progs/daniel_webcam.md3": dict(
        order=4, badge="4AM WEBCAM · MD3", title="Daniel's 4AM Clip-On CRT Webcam",
        desc="Custom clip-on sphere webcam from Daniel's 4AM bedroom station.",
    ),
    "progs/daniel_table.md3": dict(
        order=5, badge="4AM TABLE · MD3", title="Daniel's 4AM Wood LAN Desk",
        desc="Custom wooden computer desk from Daniel's 4AM room.",
    ),
    "progs/bklan/soda_bottle.md3": dict(
        order=6, badge="BAWLS · MD3", title="Blue Dimpled BAWLS Guarana LAN Bottle",
        desc="High-detail 9,387-triangle dimpled blue glass BAWLS Guarana bottle from B-LAN 2001.",
    ),
    "progs/bklan/soda_can.md3": dict(
        order=7, badge="LAN SODA · MD3", title="2001 B-LAN Caffeinated Soda Can",
        desc="Custom aluminum soda can prop scattered across the 2001 LAN tables.",
    ),
    "progs/bklan/lan_mon1.md3": dict(
        order=8, badge="CRT MONITOR · MD3", title='2001 Beige 19" CRT Gaming Monitor',
        desc="Classic 2001 beige 19-inch CRT monitor from the B-LAN party tables.",
    ),
    "progs/bklan/lan_mon2.md3": dict(
        order=9, badge="TRINITRON CRT · MD3", title="2001 Flat-Tube Trinitron CRT Monitor",
        desc="2001 flat-aperture CRT monitor from the B-LAN party tables.",
    ),
    "progs/bklan/lan_pc1.md3": dict(
        order=10, badge="ATX TOWER · MD3", title="2001 Beige ATX Mid-Tower LAN PC",
        desc="Classic beige ATX PC tower from the 2001 B-LAN party.",
    ),
    "progs/bklan/lan_pc2.md3": dict(
        order=11, badge="CASE-MOD PC · MD3", title="2001 Windowed Case-Mod Gaming Tower",
        desc="Custom windowed 2001 gaming PC tower from B-LAN.",
    ),
    "progs/fox/fox_guitar.md3": dict(
        order=12, badge="BAKERSFIELD SOUND", title="Bakersfield Sound Electric Guitar (Fox Stage)",
        desc="Custom electric guitar on stand from the Historic Fox Theater stage.",
    ),
    "progs/fox/fox_chandelier.md3": dict(
        order=13, badge="FOX THEATER · MD3", title="Historic Fox Theater Ornate Chandelier",
        desc="1,052-triangle brass & crystal chandelier from the Fox Theater lobby.",
    ),
    "progs/fox/fox_clockpost.md3": dict(
        order=14, badge="DOWNTOWN · MD3", title="Downtown Bakersfield Sidewalk Clock Post",
        desc="Vintage ornate street clock post outside the Fox Theater & Padre Hotel.",
    ),
    "progs/fox/pad_pooltable.md3": dict(
        order=15, badge="PADRE HOTEL · MD3", title="Padre Hotel Felt Billiards Pool Table",
        desc="1,360-triangle billiards table from the Padre Hotel lounge.",
    ),
    "progs/fox/pad_jacuzzi.md3": dict(
        order=16, badge="PADRE ROOFTOP · MD3", title="Padre Hotel Rooftop Jacuzzi Hot Tub",
        desc="Custom wood-paneled rooftop hot tub from the Padre Hotel.",
    ),
}

# Curated showcase set: EVERY real custom sprite, character, gun, complete vehicle & iconic prop —
# ZERO shrapnel, gibs, blown-off car doors/bumpers, single-quad typing letters, CRT debris, or generic warehouse boxes!
CURATED_GALLERY_CATS = {
    # 1. 360° Sprites & Characters (27)
    "progs/wheelman.spr32": "sprites",
    "progs/wheelman_dance.spr32": "sprites",
    "progs/greensuit_wheelman.spr32": "sprites",
    "progs/daniel.spr32": "sprites",
    "progs/david.spr32": "sprites",
    "progs/robeguy.spr32": "sprites",
    "progs/bryan.spr32": "sprites",
    "progs/mm_suit_rider.md3": "sprites",
    "progs/mm_squat_rider.md3": "sprites",
    "progs/john_bird_head.md3": "sprites",
    "progs/pickle.md3": "sprites",
    "progs/pinklady.md3": "sprites",
    "progs/ltg_head.md3": "sprites",
    "progs/floathead.mdl": "sprites",
    "progs/bigears.md3": "sprites",
    "progs/johnhead3d.md3": "sprites",
    "progs/daniel_dad.spr32": "sprites",
    "progs/fr_dennis.spr32": "sprites",
    "progs/fr_paul.spr32": "sprites",
    "progs/fr_rob.spr32": "sprites",
    "progs/fr_mrdiy.spr32": "sprites",
    "progs/fr_quakeguy.spr32": "sprites",
    "progs/fr_scissors.spr32": "sprites",
    "progs/fr_finger.spr32": "sprites",
    "progs/preg_1.spr32": "sprites",
    "progs/preg_2.spr32": "sprites",
    "progs/preg_3.spr32": "sprites",

    # 2. Custom Guns, Weapons & Contraptions (27)
    "progs/v_megaman.md3": "guns",
    "progs/v_mm_cannon.md3": "guns",
    "progs/v_mm_slingshot.md3": "guns",
    "progs/v_mm_bow.md3": "guns",
    "progs/v_mm_handthrow.md3": "guns",
    "progs/v_wewcannon.md3": "guns",
    "progs/g_wewcannon.md3": "guns",
    "progs/v_mysterybox.md3": "guns",
    "progs/proj_mysterybox.md3": "guns",
    "progs/v_milky.md3": "guns",
    "progs/v_pickle.md3": "guns",
    "progs/v_netsend.md3": "guns",
    "progs/netsend_pc.md3": "guns",
    "progs/v_laptop.md3": "guns",
    "progs/ltg_view.md3": "guns",
    "progs/v_googun.md3": "guns",
    "progs/v_hammer.mdl": "guns",
    "progs/v_sledge.md3": "guns",
    "progs/v_paddle.md3": "guns",
    "progs/v_hackmon.md3": "guns",
    "progs/v_robdob.mdl": "guns",
    "progs/grenade.mdl": "guns",
    "progs/fr_johnhand.spr32": "guns",
    "progs/jetpack.md3": "guns",
    "progs/megaman.md3": "guns",
    "progs/v_srifle.mdl": "guns",
    "progs/turrgun.mdl": "guns",

    # 3. Complete Custom Cars, Buses, Trucks & Go-Karts (11)
    "progs/pink_supercar.md3": "cars",
    "progs/veh_gtcar.md3": "cars",
    "progs/veh_coupe.md3": "cars",
    "progs/veh_sedan.md3": "cars",
    "progs/veh_truck.md3": "cars",
    "progs/veh_hdtruck.md3": "cars",
    "progs/veh_van.md3": "cars",
    "progs/veh_schoolbus.md3": "cars",
    "progs/fox/get_bus.md3": "cars",
    "progs/jesskart.spr32": "cars",
    "progs/bklan/sr_vehicle_forklift_orange_a01.md3": "cars",

    # 4. Signature BKTV (37 Channels), 2001 LAN & Fox Props (16)
    "progs/bk_tvscr.md3": "props",
    "progs/gw_horse.md3": "props",
    "progs/fedora.md3": "props",
    "progs/daniel_webcam.md3": "props",
    "progs/daniel_table.md3": "props",
    "progs/bklan/soda_bottle.md3": "props",
    "progs/bklan/soda_can.md3": "props",
    "progs/bklan/lan_mon1.md3": "props",
    "progs/bklan/lan_mon2.md3": "props",
    "progs/bklan/lan_pc1.md3": "props",
    "progs/bklan/lan_pc2.md3": "props",
    "progs/fox/fox_guitar.md3": "props",
    "progs/fox/fox_chandelier.md3": "props",
    "progs/fox/fox_clockpost.md3": "props",
    "progs/fox/pad_pooltable.md3": "props",
    "progs/fox/pad_jacuzzi.md3": "props",
}


def auto_nice_title_and_desc(rel_low, cat, fmt, nf, nskins):
    bn = os.path.splitext(os.path.basename(rel_low))[0]
    friend_map = {
        "daniel_dad": ("Daniel's Dad 360° Chaser (.SPR32)", "56-frame 8-direction sprite of Daniel's Dad (8 idle + 8×6 run)."),
        "fr_dennis": ("LAN Friend: Dennis 360° Sprite (.SPR32)", "56-frame 8-direction sprite of Dennis from the Mystery Box / LAN crew."),
        "fr_paul": ("LAN Friend: Paul 360° Sprite (.SPR32)", "56-frame 8-direction sprite of Paul (8 idle angles + 8×6 run cycle)."),
        "fr_rob": ("LAN Friend: Rob Chaser 360° Sprite (.SPR32)", "56-frame 8-direction photo-cutout sprite of Rob (8 idle + 8×6 run)."),
        "fr_quakeguy": ("Classic Quake Ranger 360° Sprite (.SPR32)", "56-frame 8-direction sprite of Quake Ranger."),
        "fr_scissors": ("Giant Running Scissors 360° Hazard (.SPR32)", "56-frame 8-direction snipping Giant Scissors hazard sprite."),
        "fr_finger": ("Giant Hopping Middle Finger 360° Sprite (.SPR32)", "56-frame 8-direction Mystery Box hazard sprite."),
        "fr_mrdiy": ("Mr. DIY 360° Companion Sprite (.SPR32)", "56-frame 8-direction Mr. DIY sprite (8 idle + 8×6 run)."),
        "preg_1": ("Pregnant Runner #1 360° Sprite (.SPR32)", "56-frame 8-direction sprite from BakersfieldQuake's NPC chaos."),
        "preg_2": ("Pregnant Runner #2 360° Sprite (.SPR32)", "56-frame 8-direction sprite from BakersfieldQuake's NPC chaos."),
        "preg_3": ("Pregnant Runner #3 360° Sprite (.SPR32)", "56-frame 8-direction sprite from BakersfieldQuake's NPC chaos."),
    }
    if bn in friend_map:
        return friend_map[bn][0], friend_map[bn][1], f"8-DIR SPR32 · {nf}f"

    if bn.startswith("veh_"):
        clean = bn[4:].replace("_", " ").title()
        if bn.endswith("_wreck"):
            return f"Exploding Scorched Wreck: {clean}", f"{nf}-frame crumpling & smoldering {clean.lower()} hull with glowing ember lightmap.", f"WRECK · {nf}f"
        return f"Vehicle Part / Debris: {clean}", f"Custom 3D blown-off vehicle debris mesh ({rel_low}) launched during car explosions.", f"CAR PART · {fmt}"

    if rel_low.startswith("progs/fox/"):
        clean = bn.replace("fox_", "Fox Theater ").replace("pad_", "Padre Hotel ").replace("_", " ").title()
        return clean, f"Custom 3D architectural / stage / lounge prop ({rel_low}) built for Fox Theater & Padre Hotel.", f"FOX/PADRE · {fmt}"

    if rel_low.startswith("progs/bklan/"):
        if bn.startswith("dan_"):
            clean = "Daniel's 4AM Room: " + bn[4:].replace("_", " ").title()
            return clean, f"Custom 3D bedroom & desk prop ({rel_low}) from Daniel's 4AM room in bklan5.", f"DANIEL ROOM · {fmt}"
        if bn.startswith("sr_"):
            clean = "Warehouse: " + bn[3:].replace("_", " ").title()
            return clean, f"Custom 3D industrial warehouse prop ({rel_low}) from B-LAN Warehouse.", f"WAREHOUSE · {fmt}"
        clean = "2001 LAN Party: " + bn.replace("bk_", "").replace("lan_", "CRT ").replace("_", " ").title()
        sk_note = f" with {nskins} switchable screen/case skins" if nskins > 1 else ""
        return clean, f"Custom 2001 B-LAN party 3D prop ({rel_low}){sk_note}.", f"2001 LAN · {fmt}"

    clean = bn.replace("_", " ").title()
    if bn.startswith("v_"):
        clean = clean[2:] + " (Viewmodel)"
    elif bn.startswith("p_"):
        clean = clean[2:] + " (3rd-Person 259f Player Rig)"
    elif bn.startswith("g_"):
        clean = clean[2:] + " (Spinning Floor Pickup)"
    return clean, f"Custom BakersfieldQuake {fmt} asset ({rel_low}, {nf} frame{'s' if nf != 1 else ''}).", f"{fmt} · {nf}f"


def make_quad_surface(packer, sname, shader, v_quad, n_quad, mat):
    uv = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], dtype="<f4")
    tris = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int32)
    return encode_surface(
        packer, sname, shader, uv, tris,
        np.asarray(v_quad, dtype=np.float32)[None, :, :],
        np.asarray(n_quad, dtype=np.float32)[None, :, :],
        mat,
    )


def build_local_master_zip(vfs):
    if os.path.isfile(LOCAL_MASTER_ZIP) and os.path.getsize(LOCAL_MASTER_ZIP) > 400_000_000:
        print(f"   Local master zip already exists: {LOCAL_MASTER_ZIP} ({os.path.getsize(LOCAL_MASTER_ZIP)/1e6:.1f} MB)", flush=True)
        return
    print(f"   Creating local Master ZIP: {LOCAL_MASTER_ZIP} ...", flush=True)
    t0 = time.time()
    readme_txt = (
        "BAKERSFIELD QUAKE — COMPLETE CUSTOM ASSETS MASTER ARCHIVE\n"
        "=========================================================\n"
        "Live Interactive 3D & Sprite Studio: https://bakersfield.larrywew.fun/custom-assets/\n"
        "Self-Contained Showcase Page:        https://bakersfield.larrywew.fun/all_custom_assets.html\n\n"
        "Contents:\n"
        "  - progs/          All 354 shipped 3D models (.md3, .mdl), 360-degree sprites (.spr32, .spr), 622 .skin files & 3,268 model/TV textures\n"
        "  - vault/progs/    8 archived bonus models (Girlfriend Gun girl.md3 + v_banana.md3, Player Bodies robeguy/suitguy/wifeguy.mdl, Sky-Chariots v1/v2/v4)\n"
        "  - glb/            All 15 original high-poly glTF 2.0 (.glb) 3D source models\n"
        "  - sound/          All 318 custom sound effects, voice clips, Larry McCart prank lines & songs (.wav, .ogg)\n"
        "  - textures/       All 1,025 custom Bakersfield map textures, neon signs, posters & banners (.png, .tga)\n"
        "  - gfx/            All 19 custom skyboxes & HUD overlays\n"
        "  - scripts/        All 27 custom DarkPlaces / Quake 3 .shader material scripts\n"
        "  - effectinfo.txt & intro.dem\n"
    )
    written = set()
    with zipfile.ZipFile(LOCAL_MASTER_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as zout:
        zout.writestr("README_CUSTOM_ASSETS.txt", readme_txt)
        written.add("readme_custom_assets.txt")
        for k, real in sorted(vfs.real_path.items()):
            zout.writestr(real, vfs.read(k))
            written.add(k)
        if os.path.isdir(VPS_GLB_DIR):
            for gp in sorted(glob.glob(os.path.join(VPS_GLB_DIR, "*.glb"))):
                arc = "glb/" + os.path.basename(gp)
                if arc.lower() not in written:
                    zout.write(gp, arc)
                    written.add(arc.lower())
        for extra_fn in ("effectinfo.txt", "intro.dem", "readme.txt"):
            ep = os.path.join(MOD, extra_fn)
            if os.path.isfile(ep) and extra_fn.lower() not in written:
                zout.write(ep, extra_fn)
                written.add(extra_fn.lower())
    print(f"   Wrote {LOCAL_MASTER_ZIP} ({len(written)} files, {os.path.getsize(LOCAL_MASTER_ZIP)/1e6:.1f} MB) in {time.time()-t0:.1f}s", flush=True)


def main():
    t_start = time.time()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    if not os.path.isfile(VAULT_ZIP_OUT) and os.path.isfile(VAULT_ZIP_TMP):
        shutil.copy2(VAULT_ZIP_TMP, VAULT_ZIP_OUT)
    assert os.path.isfile(VAULT_ZIP_OUT), f"Missing {VAULT_ZIP_OUT}"
    assert os.path.isfile(VPS_MAN_PATH), f"Missing {VPS_MAN_PATH}"

    print("1. Loading VFS (bakersfield.pk3 + vault_extras.zip) & vps_manifest.json...", flush=True)
    vfs = VFS(PK3_PATH, VAULT_ZIP_OUT)
    vps_man = json.load(open(VPS_MAN_PATH, "r", encoding="utf-8"))
    shaders = parse_all_shaders(vfs)
    packer = VaultPacker()

    # Fix greensuit_wheelman.spr32 .glb link if present in raw/glb/greensuit_wheelman_3d.glb
    gs_cid = canon_id("progs/greensuit_wheelman.spr32")
    if gs_cid in vps_man["bundles"] and not vps_man["bundles"][gs_cid].get("glb"):
        gs_local = os.path.join(VPS_GLB_DIR, "greensuit_wheelman_3d.glb")
        if os.path.isfile(gs_local):
            vps_man["bundles"][gs_cid]["glb"] = "glb/greensuit_wheelman_3d.glb"
            vps_man["bundles"][gs_cid]["glbSize"] = os.path.getsize(gs_local)

    # Generic Q3 Shader + Texture Resolver over VFS
    shader_mat_cache = {}

    def find_vfs_image(ref, mdl_dir):
        if not ref:
            return None
        r = ref.replace("\\", "/").lstrip("/").lower()
        stem = os.path.splitext(r)[0] if r.endswith((".png", ".tga", ".jpg", ".jpeg")) else r
        bn = os.path.basename(stem)
        for cand in (
            r, stem + ".png", stem + ".tga", stem + ".jpg",
            f"{mdl_dir}/{bn}.png", f"{mdl_dir}/{bn}.tga", f"{mdl_dir}/{bn}.jpg",
            f"progs/{bn}.png", f"progs/{bn}.tga", f"progs/{bn}.jpg",
            f"textures/{bn}.png", f"textures/{bn}.tga",
        ):
            if vfs.exists(cand) and cand.endswith((".png", ".tga", ".jpg", ".jpeg")):
                return cand
        return None

    def resolve_q3_mat(ref, mdl_dir, stem):
        r = (ref or "").replace("\\", "/").lstrip("/").lower()
        ck = (r, mdl_dir)
        if ck in shader_mat_cache:
            return dict(shader_mat_cache[ck])

        sh_key = r[:-4] if r.endswith((".png", ".tga", ".jpg")) else r
        body = shaders.get(sh_key) or shaders.get(r)
        is_add = False
        is_blend = False
        is_atest = False
        is_unlit = False
        scroll_v = 0.0
        glow_rel = None
        anim_fps = 0.0
        anim_frames = []
        base_rel = None

        if body:
            low_b = body.lower()
            if "alphafunc" in low_b:
                is_atest = True
            if "rgbgen identity" in low_b:
                is_unlit = True
            scm = re.search(r"tcmod\s+scroll\s+[-\d\.]+\s+([-\d\.]+)", low_b)
            if scm:
                scroll_v = float(scm.group(1))

            # Parse stage blocks inside shader body
            stages = re.findall(r"\{([^\{\}]*)\}", body)
            for st_idx, st_txt in enumerate(stages):
                st_low = st_txt.lower()
                am = re.search(r"animmap\s+([\d\.]+)\s+([^\r\n]+)", st_txt, re.I)
                mm = re.search(r"\bmap\s+([^\s\r\n]+)", st_txt, re.I)
                stage_add = bool(re.search(r"blendfunc\s+(add|gl_one\s+gl_one)", st_low))
                stage_blend = bool(re.search(r"blendfunc\s+(blend|gl_src_alpha\s+gl_one_minus_src_alpha)", st_low))
                if am and not anim_frames:
                    anim_fps = float(am.group(1))
                    toks = am.group(2).split()
                    # Subsample huge BKTV 64-frame video chunks to 8 crisp frames so all 37 TV channels fit lightly!
                    if sh_key.startswith("progs/bktv_c") and len(toks) > 8:
                        step = max(1, len(toks) // 8)
                        toks = toks[::step][:8]
                        anim_fps = max(3.0, anim_fps / step)
                    for tok in toks:
                        img_k = find_vfs_image(tok, mdl_dir)
                        if img_k:
                            anim_frames.append(img_k)
                    if stage_add:
                        is_add = True
                        is_unlit = True
                    elif stage_blend:
                        is_blend = True
                elif mm:
                    tok = mm.group(1).strip()
                    if tok.startswith("$"):
                        continue
                    img_k = find_vfs_image(tok, mdl_dir)
                    if not img_k:
                        continue
                    if st_idx > 0 and stage_add and (base_rel or anim_frames):
                        glow_rel = img_k
                    elif base_rel is None and not anim_frames:
                        base_rel = img_k
                        if stage_add:
                            is_add = True
                            is_unlit = True
                        elif stage_blend:
                            is_blend = True

        if not anim_frames and base_rel is None:
            base_rel = find_vfs_image(r, mdl_dir) or find_vfs_image(stem, mdl_dir)

        bn = os.path.basename(sh_key)
        if not body:
            is_add = any(w in bn for w in ("zap", "laser", "flash", "fx", "arc", "aura"))
            is_unlit = is_add or any(w in bn for w in ("scr", "leds", "glow", "foam", "hm_scr"))
            if base_rel and glow_rel is None:
                gc = os.path.splitext(base_rel)[0] + "_glow.png"
                if vfs.exists(gc):
                    glow_rel = gc

        wrap = abs(scroll_v) > 1e-4
        if anim_frames:
            uniq = []
            p2t = {}
            for fk in anim_frames:
                if fk not in p2t:
                    p2t[fk] = len(uniq)
                    uniq.append(fk)
            tile_d = 160 if sh_key.startswith("progs/bktv_c") else 224
            tid = packer.add_atlas(
                f"sh_{sh_key.replace('/', '_')}",
                [vfs.open_pil(fk) for fk in uniq],
                max_tile_dim=tile_d, pad=1, quality=80,
                raw_rel=vfs.real_path[uniq[0]],
            )
            order = [p2t[fk] for fk in anim_frames]
            has_a = True
        elif base_rel:
            max_d = 768 if any(x in bn for x in ("supercar", "veh_", "girl", "megaman", "wew_silver", "bird_head")) else 512
            tid = packer.add_tex_vfs(vfs, base_rel, max_dim=max_d, force_png=is_add, wrap=wrap, lift=1.0 if is_unlit else 1.15)
            order = None
            has_a = packer.tex_list[tid]["alpha"]
        else:
            tid, order, has_a = -1, None, False

        gtid = packer.add_tex_vfs(vfs, glow_rel, max_dim=384) if glow_rel else -1
        is_glass = "glass" in bn
        is_metal = any(w in bn for w in ("chrome", "silver", "metal", "steel", "brass", "gold", "copper"))
        mat = dict(
            tex=tid,
            glowTex=gtid,
            animFps=anim_fps,
            animOrder=order,
            scrollV=scroll_v,
            metallic=0.72 if is_metal else (0.55 if is_glass else 0.14),
            roughness=0.22 if (is_metal or is_glass) else 0.52,
            spec=0.82 if (is_metal or is_glass) else 0.36,
            unlit=bool(is_unlit),
            additive=bool(is_add),
            alphaBlend=bool((is_blend or is_glass) and not is_add),
            alphaTest=bool((is_atest or (has_a and not is_blend and not is_glass)) and not is_add),
        )
        shader_mat_cache[ck] = mat
        return dict(mat)

    def pack_atlas_seq(atlas_id, rel_list, max_tile_dim=216):
        uniq, p2t = [], {}
        for rk in rel_list:
            k = rk.lower()
            if k not in p2t:
                p2t[k] = len(uniq)
                uniq.append(k)
        tid = packer.add_atlas(
            atlas_id, [vfs.open_pil(k) for k in uniq],
            max_tile_dim=max_tile_dim, pad=1, quality=80,
            raw_rel=vfs.real_path[uniq[0]],
        )
        return tid, [p2t[rk.lower()] for rk in rel_list]

    # 2. Pack ONLY the 81 curated pure-gold custom sprites, guns, complete cars & signature props (zero scrap/debris)!
    missing_curated = [ck for ck in CURATED_GALLERY_CATS if ck not in vfs.entries]
    assert not missing_curated, f"Missing curated models in VFS: {missing_curated}"
    all_model_keys = sorted(CURATED_GALLERY_CATS.keys())
    print(f"2. Packing {len(all_model_keys)} curated showcase 3D models & 360° sprites from VFS...", flush=True)

    models_out = []
    for k in all_model_keys:
        real = vfs.real_path[k]
        cid = canon_id(real)
        assert cid in vps_man["bundles"], f"Model {real} ({cid}) missing from vps_manifest.json!"
        binfo = vps_man["bundles"][cid]
        cat = CURATED_GALLERY_CATS[k]
        is_vault = k.startswith("vault/")
        mdl_dir = os.path.dirname(k)
        stem = os.path.splitext(os.path.basename(k))[0]
        hero = HERO_META.get(k, {})

        # Find numerically sorted .skin files for this model
        skin_keys = []
        skin_prefix = k + "_"
        for sk_k in vfs.entries:
            if sk_k.startswith(skin_prefix) and sk_k.endswith(".skin"):
                m_num = re.search(r"_(\d+)\.skin$", sk_k)
                skin_keys.append((int(m_num.group(1)) if m_num else 9999, sk_k))
        skin_keys.sort()

        # ---------- SPECIAL CASE A: progs/pinklady.md3 (16-angle + 34f bounce sprite card) ----------
        if k == "progs/pinklady.md3":
            turn_rels = [f"progs/pinklady_{d:02d}.png" for d in range(16)]
            bfwd = [f"progs/pinklady_b{i:02d}.png" for i in range(0, 36, 2)]
            bpp = bfwd + bfwd[-2:0:-1]
            tid, _ = pack_atlas_seq("pinklady_16_plus_bounce", turn_rels + bpp, max_tile_dim=216)
            hw, hh = 26.0, 56.0
            s_enc = make_quad_surface(
                packer, "pinklady_card", "progs/pinklady_v00",
                [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]],
                [[-1.0, 0.0, 0.0]] * 4,
                dict(tex=tid, unlit=True, alphaTest=True, alphaBlend=True, billboard=1),
            )
            entry = dict(
                id=cid, cat=cat, status="active", fmt="2D SHADER",
                badge=hero["badge"], title=hero["title"], file=real, desc=hero["desc"],
                nf=len(bpp), nv=4, nt=2, bbox=[[-hw, -hw, 0.0], [hw, hw, hh]],
                isSprite=True, turnDirs=16, turnSign=-1, surfaces=[s_enc],
                clips=[
                    dict(id="bounce", label="💖 Front Bounce Ping-Pong (34f)", start=0, count=len(bpp), fps=8.0,
                         sprMode=dict(base=16, dirs=1, fpd=len(bpp), fps=8.0)),
                    dict(id="turn16", label="🔄 360° Turnaround (16 Angles)", start=0, count=1, fps=10.0,
                         sprMode=dict(base=0, dirs=16, fpd=1, fps=10.0)),
                ],
            )

        # ---------- SPECIAL CASE B: progs/v_milky.md3 (248 per-frame skins -> 3 smooth video atlases) ----------
        elif k == "progs/v_milky.md3":
            m = read_md3_bytes(vfs.read(k), k)
            s0 = m["surfaces"][0]
            seq_a = [f"progs/mvm_a_{i:02d}.png" for i in range(0, 96, 3)]
            seq_b = [f"progs/mvm_b_{i:02d}.png" for i in range(0, 96, 3)]
            seq_f = [f"progs/mvm_f_{i:02d}.png" for i in range(0, 56, 2)]
            tid_a, ord_a = pack_atlas_seq("v_milky_a", seq_a + seq_a[-2:0:-1], max_tile_dim=216)
            tid_b, ord_b = pack_atlas_seq("v_milky_b", seq_b + seq_b[-2:0:-1], max_tile_dim=216)
            tid_f, ord_f = pack_atlas_seq("v_milky_f", seq_f, max_tile_dim=216)
            s_enc = encode_surface(
                packer, s0["name"], s0["shader"], s0["st"], s0["tris"], s0["all_v"], s0["all_n"],
                dict(tex=tid_a, animFps=8.0, animOrder=ord_a, unlit=True, alphaTest=True, alphaBlend=True),
            )
            bmin = s0["all_v"][0].min(axis=0).round(2).tolist()
            bmax = s0["all_v"][0].max(axis=0).round(2).tolist()
            entry = dict(
                id=cid, cat=cat, status="active", fmt="2D SHADER",
                badge=hero["badge"], title=hero["title"], file=real, desc=hero["desc"],
                pov=True, defaultPov=True, az=3.14, el=0.06,
                nf=1, nv=int(s_enc["nv"]), nt=int(s_enc["nt"]), bbox=[bmin, bmax],
                surfaces=[s_enc],
                skins=[
                    dict(label="🥛 Idle A (Pink Lady)", map={s0["name"]: dict(tex=tid_a, animFps=8.0, animOrder=ord_a)}),
                    dict(label="🥛 Idle B (Alt Sway)", map={s0["name"]: dict(tex=tid_b, animFps=8.0, animOrder=ord_b)}),
                    dict(label="💥 Open-Palm Launch", map={s0["name"]: dict(tex=tid_f, animFps=18.0, animOrder=ord_f)}),
                ],
                clips=[dict(id="shader", label="🎬 Live Video Shader", start=0, count=1, fps=10.0, lie=True)],
            )

        # ---------- SPECIAL CASE C: progs/v_pickle.md3 (120 per-frame skins -> Idle + Choke-Whip atlases) ----------
        elif k == "progs/v_pickle.md3":
            m = read_md3_bytes(vfs.read(k), k)
            s0 = m["surfaces"][0]
            seq_idle = [f"progs/pvm_{i:03d}.png" for i in range(0, 72, 2)]
            seq_fire = [f"progs/pvm_{i:03d}.png" for i in range(72, 120)]
            tid_i, ord_i = pack_atlas_seq("v_pickle_idle", seq_idle, max_tile_dim=216)
            tid_f, ord_f = pack_atlas_seq("v_pickle_fire", seq_fire, max_tile_dim=216)
            s_enc = encode_surface(
                packer, s0["name"], s0["shader"], s0["st"], s0["tris"], s0["all_v"], s0["all_n"],
                dict(tex=tid_f, animFps=18.0, animOrder=ord_f, unlit=True, alphaTest=True, alphaBlend=True),
            )
            bmin = s0["all_v"][0].min(axis=0).round(2).tolist()
            bmax = s0["all_v"][0].max(axis=0).round(2).tolist()
            entry = dict(
                id=cid, cat=cat, status="active", fmt="2D SHADER",
                badge=hero["badge"], title=hero["title"], file=real, desc=hero["desc"],
                pov=True, defaultPov=True, az=3.14, el=0.05,
                nf=1, nv=int(s_enc["nv"]), nt=int(s_enc["nt"]), bbox=[bmin, bmax],
                surfaces=[s_enc],
                skins=[
                    dict(label="💥 Choke-Squeeze, Scream & Whip", map={s0["name"]: dict(tex=tid_f, animFps=18.0, animOrder=ord_f)}),
                    dict(label="🥒 Smooth Idle Clutch", map={s0["name"]: dict(tex=tid_i, animFps=12.0, animOrder=ord_i)}),
                ],
                clips=[dict(id="shader", label="🎬 Live Claw Animation", start=0, count=1, fps=12.0, lie=True)],
            )

        # ---------- SPECIAL CASE D: progs/pickle.md3 (36f 3D Diva Dance + 4x16 Turnaround Skins) ----------
        elif k == "progs/pickle.md3":
            m = read_md3_bytes(vfs.read(k), k)
            s0 = m["surfaces"][0]
            skin_defs = [
                (0, "🎤 Diva Sing (16 Angles)"),
                (1, "😉 Cheeky Pucker Wink (16 Angles)"),
                (2, "😜 Bug-Eyes & Pink Tongue (16 Angles)"),
                (3, "😱 360° Pre-Blast Scream (16 Angles)"),
            ]
            tids_pk = []
            for s_idx, _ in skin_defs:
                rels_16 = [f"progs/pkv_s{s_idx}_v{v:02d}.png" for v in range(16)]
                tid_s, _ = pack_atlas_seq(f"pickle_diva_s{s_idx}", rels_16, max_tile_dim=216)
                tids_pk.append(tid_s)
            s_enc = encode_surface(
                packer, s0["name"], s0["shader"], s0["st"], s0["tris"], s0["all_v"], s0["all_n"],
                dict(tex=tids_pk[0], unlit=True, alphaTest=True, alphaBlend=True),
            )
            pts = s0["all_v"][0]
            entry = dict(
                id=cid, cat=cat, status="active", fmt="MD3",
                badge=hero["badge"], title=hero["title"], file=real, desc=hero["desc"],
                az=3.14, el=0.10, dirAtlas=True, turnDirs=16, turnSign=-1,
                nf=int(m["nframes"]), nv=int(s_enc["nv"]), nt=int(s_enc["nt"]),
                bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
                surfaces=[s_enc],
                skins=[dict(label=lbl, map={s0["name"]: dict(tex=tids_pk[i])}) for i, (_, lbl) in enumerate(skin_defs)],
                clips=[
                    dict(id="dance", label="💃 Wacky-Waving Diva Dance (24f)", start=0, count=24, fps=14.0),
                    dict(id="swell", label="🎈 Pre-Blast Balloon Swell (12f)", start=24, count=12, fps=12.0),
                    dict(id="all", label="🎬 All 36 Frames", start=0, count=36, fps=14.0),
                ],
            )

        # ---------- SPECIAL CASE E: progs/pickle_throw.md3 (8 tumbling throw skins) ----------
        elif k == "progs/pickle_throw.md3":
            m = read_md3_bytes(vfs.read(k), k)
            s0 = m["surfaces"][0]
            rels_8 = [f"progs/pthr_{i:02d}.png" for i in range(8)]
            tid_pt, ord_pt = pack_atlas_seq("pickle_throw_8f", rels_8, max_tile_dim=216)
            s_enc = encode_surface(
                packer, s0["name"], s0["shader"], s0["st"], s0["tris"], s0["all_v"], s0["all_n"],
                dict(tex=tid_pt, animFps=14.0, animOrder=ord_pt, unlit=True, alphaTest=True, alphaBlend=True, billboard=1),
            )
            pts = s0["all_v"][0]
            entry = dict(
                id=cid, cat=cat, status="active", fmt="MD3",
                badge="TUMBLING THROW · 8f", title="Thrown Screaming Pickle Surprise Card (8f Tumble)",
                file=real, desc="8-skin tumbling thrown Pickle Surprise projectile with bug-eyed pink-tongue scream frames!",
                nf=1, nv=int(s_enc["nv"]), nt=int(s_enc["nt"]),
                bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
                isSprite=True, surfaces=[s_enc],
                clips=[dict(id="tumble", label="🥒 Tumbling Throw (8f)", start=0, count=8, fps=14.0,
                            sprMode=dict(base=0, dirs=1, fpd=8, fps=14.0))],
            )

        # ---------- SPECIAL CASE F: progs/ltg_view.md3 (Idle + 42fps Typing Video Skins) ----------
        elif k == "progs/ltg_view.md3":
            m = read_md3_bytes(vfs.read(k), k)
            s0 = m["surfaces"][0]
            i_seq = [f"progs/ltg_i_{i:02d}.png" for i in range(0, 44, 2)]
            t_seq = [f"progs/ltg_t_{i:02d}.png" for i in range(0, 48, 2)]
            tid_i, ord_i = pack_atlas_seq("ltg_view_idle", i_seq + i_seq[-2:0:-1], max_tile_dim=216)
            tid_t, ord_t = pack_atlas_seq("ltg_view_type", t_seq, max_tile_dim=216)
            s_enc = encode_surface(
                packer, s0["name"], s0["shader"], s0["st"], s0["tris"], s0["all_v"], s0["all_n"],
                dict(tex=tid_i, animFps=6.0, animOrder=ord_i, unlit=True, alphaTest=True),
            )
            pts = s0["all_v"][0]
            entry = dict(
                id=cid, cat=cat, status="active", fmt="2D SHADER",
                badge=hero["badge"], title=hero["title"], file=real, desc=hero["desc"],
                pov=True, defaultPov=True, az=3.14, el=0.06,
                nf=1, nv=int(s_enc["nv"]), nt=int(s_enc["nt"]),
                bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
                surfaces=[s_enc],
                skins=[
                    dict(label="💻 Idle Sway", map={s0["name"]: dict(tex=tid_i, animFps=6.0, animOrder=ord_i)}),
                    dict(label="⚡ Rapid Typing (42fps)", map={s0["name"]: dict(tex=tid_t, animFps=21.0, animOrder=ord_t)}),
                ],
                clips=[dict(id="shader", label="🎬 Live Video Shader", start=0, count=1, fps=10.0, lie=True)],
            )

        # ---------- SPECIAL CASE G: .SPR32 & .SPR SPRITES (ALL 24) ----------
        elif k.endswith((".spr32", ".spr")):
            sp = parse_spr_bytes(vfs.read(k), k)
            nf = sp["nf"]
            nearest = (sp["ver"] == 1) or max(sp["mw"], sp["mh"]) <= 64
            max_td = 140 if nf > 400 else (180 if nf > 120 else 224)
            tid = packer.add_atlas(
                f"spr_{stem}", sp["frames"], max_tile_dim=max_td,
                pad=1, quality=80, nearest=nearest, raw_rel=real,
            )
            scale_u = 1.5 if stem == "sight" else (0.35 if stem == "jw_ripple" else 0.5)
            hw = sp["mw"] * scale_u * 0.5
            hh = sp["mh"] * scale_u
            if stem == "fr_johnhand":
                vq = [[16.0, +13.0, -13.5], [16.0, +13.0, +2.5], [16.0, -13.0, +2.5], [16.0, -13.0, -13.5]]
                nq = [[-1.0, 0.0, 0.0]] * 4
                bbox = [[15.0, -13.0, -13.5], [17.0, 13.0, 2.5]]
                bb = 0
            elif stem == "jw_ripple":
                vq = [[-hw, -hw, 0.5], [+hw, -hw, 0.5], [+hw, +hw, 0.5], [-hw, +hw, 0.5]]
                nq = [[0.0, 0.0, 1.0]] * 4
                bbox = [[-hw, -hw, 0.0], [hw, hw, 2.0]]
                bb = 0
            else:
                vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
                nq = [[-1.0, 0.0, 0.0]] * 4
                bbox = [[-hw, -hw, 0.0], [hw, hw, hh]]
                bb = 1
            is_add = (stem == "netsend_arc")
            s_enc = make_quad_surface(packer, "sprite_quad", os.path.basename(real), vq, nq, dict(
                tex=tid, animFps=12.0 if bb == 0 and nf > 1 else 0.0,
                unlit=True, additive=is_add, alphaTest=not is_add, alphaBlend=not is_add, billboard=bb,
            ))

            if "clips" in hero:
                clips = hero["clips"]
                turn_dirs = hero.get("turnDirs", 8)
            elif nf == 56:
                turn_dirs = 8
                clips = [
                    dict(id="run", label="🏃 360° Run / Drive (8-Dir × 6f)", start=0, count=6, fps=11.0,
                         sprMode=dict(base=8, dirs=8, fpd=6, fps=11.0)),
                    dict(id="idle", label="🧍 360° Idle Stand (8-Dir × 1f)", start=0, count=1, fps=8.0,
                         sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
                ]
            elif stem == "fr_johnhand":
                turn_dirs = 0
                clips = [
                    dict(id="throw", label="🌊 Cast John Wave (41f)", start=0, count=41, fps=16.0,
                         sprMode=dict(base=8, dirs=1, fpd=41, fps=16.0)),
                    dict(id="idle", label="🖐️ Idle Hand Sway (8f)", start=0, count=8, fps=10.0,
                         sprMode=dict(base=0, dirs=1, fpd=8, fps=10.0)),
                ]
            else:
                turn_dirs = 0
                clips = [dict(id="anim", label=f"🎬 Sprite Sequence ({nf}f)", start=0, count=nf, fps=11.0,
                              sprMode=dict(base=0, dirs=1, fpd=nf, fps=11.0))]

            fmt_s = "SPR32" if sp["ver"] == 32 else "SPR"
            a_title, a_desc, a_badge = auto_nice_title_and_desc(k, cat, fmt_s, nf, 1)
            entry = dict(
                id=cid, cat=cat, status="vault" if is_vault else "active", fmt=fmt_s,
                badge=hero.get("badge", a_badge), title=hero.get("title", a_title),
                file=real, desc=hero.get("desc", a_desc),
                nf=int(nf), nv=4, nt=2, bbox=bbox,
                isSprite=True, turnDirs=int(turn_dirs), turnSign=-1 if turn_dirs > 1 else 1,
                surfaces=[s_enc], clips=clips,
            )
            for opt_k in ("pov", "defaultPov", "az", "el"):
                if opt_k in hero:
                    entry[opt_k] = hero[opt_k]
            if stem == "jw_ripple":
                entry["el"] = 0.62

        # ---------- SPECIAL CASE H: ALL .MDL MESHES (21 TOTAL) ----------
        elif k.endswith(".mdl"):
            r = parse_mdl_bytes(vfs.read(k))
            tids = []
            for si_num in range(8):
                for ext_s in (".tga", ".png"):
                    cand_s = f"{k}_{si_num}{ext_s}"
                    if vfs.exists(cand_s):
                        tids.append(packer.add_tex_vfs(vfs, cand_s, max_dim=768))
                        break
            if not tids:
                for si, s8 in enumerate(r["skins8"]):
                    rgb = PALETTE_U8[s8]
                    im = Image.fromarray(rgb.astype(np.uint8), "RGB")
                    near = max(r["sw"], r["sh"]) <= 320
                    tids.append(packer.add_tex_pil(
                        ("mdl_pal", k, si), f"{os.path.basename(real)}_skin{si}",
                        im, max_dim=512, force_png=near, nearest=near, raw_rel=real,
                    ))
            skins_out = []
            if len(tids) > 1:
                for si, tid in enumerate(tids):
                    lbl = (["🙂 Closed Mouth", "😱 Screaming Jaw"][si] if stem == "floathead" and si < 2 else f"Skin {si}")
                    skins_out.append(dict(label=lbl, map={"mdl_body": dict(tex=tid)}))

            idle_idx = [i for i, nm in enumerate(r["names"]) if nm != "gone"][:16] or [0]
            pts_idle = r["all_v"][idle_idx].reshape(-1, 3)
            is_unlit = stem.startswith("spark_")
            s_enc = encode_surface(
                packer, "mdl_body", os.path.basename(real), r["uv"], r["tris"], r["all_v"], r["all_n"],
                dict(tex=tids[0], metallic=0.18, roughness=0.52, spec=0.38, unlit=is_unlit),
            )
            a_title, a_desc, a_badge = auto_nice_title_and_desc(k, cat, "MDL", r["nf"], len(tids))
            entry = dict(
                id=cid, cat=cat, status="vault" if is_vault else "active", fmt="MDL",
                badge=hero.get("badge", a_badge), title=hero.get("title", a_title),
                file=real, desc=hero.get("desc", a_desc),
                nf=int(r["nf"]), nv=int(s_enc["nv"]), nt=int(s_enc["nt"]),
                names=r["names"],
                bbox=[pts_idle.min(axis=0).round(2).tolist(), pts_idle.max(axis=0).round(2).tolist()],
                surfaces=[s_enc],
                clips=hero.get("clips") or auto_clips_from_names(r["names"], r["nf"], default_fps=11.0),
            )
            if skins_out:
                entry["skins"] = skins_out
            if stem.startswith("v_"):
                entry["pov"] = True
            for opt_k in ("pov", "defaultPov", "az", "el", "frameSkin"):
                if opt_k in hero:
                    entry[opt_k] = hero[opt_k]

        # ---------- GENERAL CASE: ALL REMAINING .MD3 MESHES (~311 MODELS) ----------
        else:
            m = read_md3_bytes(vfs.read(k), k)
            nf0 = m["nframes"]
            rigid_mats = try_rigid_fit_fast(m) if nf0 >= 16 else None
            is_rigid = rigid_mats is not None

            # Keep articulated multi-hundred-frame models compact with stride=2 & GPU linear lerp
            tot_v_raw = sum(len(s["st"]) for s in m["surfaces"])
            stride = 1
            if not is_rigid and nf0 * tot_v_raw > 420_000 and nf0 >= 32:
                stride = 2 if nf0 * tot_v_raw < 1_100_000 else 3
                idx_keep = list(range(0, nf0, stride))
                m["nframes"] = len(idx_keep)
                m["frame_names"] = [m["frame_names"][i] for i in idx_keep]
                for s in m["surfaces"]:
                    if len(s["all_v"]) > stride:
                        s["all_v"] = s["all_v"][idx_keep]
                        s["all_n"] = s["all_n"][idx_keep]

            nf = m["nframes"]
            # Parse .skin files if present
            skins_out = []
            skin0_map = {}
            for sk_i, (sk_num, sk_k) in enumerate(skin_keys):
                txt_sk = vfs.read(sk_k).decode("latin1", errors="replace")
                smap = {}
                sh_labels = []
                for ln in txt_sk.splitlines():
                    ln = ln.strip()
                    if not ln or ln.startswith("//") or "," not in ln:
                        continue
                    sname_sk, sh_sk = [x.strip() for x in ln.split(",", 1)]
                    if not sh_sk or sh_sk.lower() == "common/nodraw":
                        smap[sname_sk] = dict(nodraw=True)
                    else:
                        mat_sk = resolve_q3_mat(sh_sk, mdl_dir, stem)
                        smap[sname_sk] = mat_sk
                        sh_labels.append(os.path.basename(sh_sk))
                if sk_i == 0:
                    skin0_map = smap
                if len(skin_keys) > 1:
                    if k == "progs/bk_tvscr.md3":
                        lbl = "📺 TV Off" if sk_num == 0 else f"📺 Ch {sk_num}"
                    elif k.startswith("progs/veh_") and len(skin_keys) == 2:
                        lbl = "✨ Clean Paint" if sk_num == 0 else "🔥 Burned Wreck"
                    elif k == "progs/veh_van.md3":
                        lbl = ["🚐 Clean White", "🔥 Burned", "🔍 Cutaway Clean", "🔥 Cutaway Burned"][min(sk_i, 3)]
                    else:
                        hint = sh_labels[0] if sh_labels else f"Skin {sk_num}"
                        lbl = f"{sk_num}: {hint}"
                    skins_out.append(dict(label=lbl, map=smap))

            if nf == 259:
                bbox_frames = list(range(12, 17))
            elif k == "progs/netsend_pc.md3":
                bbox_frames = list(range(12, 22))
            elif k in ("progs/mm_explode.md3", "progs/veh_blast.md3"):
                bbox_frames = [2, 4]
            elif nf >= 16 and stem.startswith("v_"):
                bbox_frames = list(range(0, min(8, nf)))
            else:
                bbox_frames = list(range(min(nf, 6)))

            surfs_out = []
            tot_v, tot_t = 0, 0
            solid_pts = []
            for s in m["surfaces"]:
                sname, shader = s["name"], s["shader"]
                tot_v += len(s["st"])
                tot_t += len(s["tris"])
                mat = skin0_map.get(sname) or resolve_q3_mat(shader or sname, mdl_dir, stem)
                if k == "progs/ltg_head.md3":
                    # ltg_head_v00 -> progs/ltg_head_00.png
                    b_ltg = os.path.basename(shader).replace("ltg_head_v", "ltg_head_") + ".png"
                    if vfs.exists("progs/" + b_ltg):
                        mat = dict(tex=packer.add_tex_vfs(vfs, "progs/" + b_ltg, max_dim=256), unlit=True, alphaTest=True)
                if not mat.get("additive") and not mat.get("nodraw") and sname != "netsend_disk":
                    for fi in bbox_frames:
                        if 0 <= fi < len(s["all_v"]):
                            vv = s["all_v"][fi]
                            if not np.allclose(vv, 0.0):
                                solid_pts.append(vv)
                v_pack = s["all_v"][:1] if is_rigid else s["all_v"]
                n_pack = s["all_n"][:1] if is_rigid else s["all_n"]
                surfs_out.append(encode_surface(packer, sname, shader, s["st"], s["tris"], v_pack, n_pack, mat))

            if not solid_pts:
                for s in m["surfaces"]:
                    for fi in range(len(s["all_v"])):
                        if not np.allclose(s["all_v"][fi], 0.0):
                            solid_pts.append(s["all_v"][fi])
                            break
            if not solid_pts:
                solid_pts = [m["surfaces"][0]["all_v"][0]]
            pts_cat = np.vstack(solid_pts)

            names = get_player_259_names() if nf0 == 259 and stride == 1 else m["frame_names"]
            fps_def = 12.0 / stride
            if k in ("progs/veh_van.md3", "progs/veh_truck.md3", "progs/veh_sedan.md3", "progs/veh_coupe.md3",
                     "progs/veh_gtcar.md3", "progs/veh_hdtruck.md3", "progs/veh_schoolbus.md3") and nf == 36:
                clips = [
                    dict(id="all", label="🎬 All 36f (Roll + Steer)", start=0, count=36, fps=14.0),
                    dict(id="straight", label="🚗 Straight Roll (12f)", start=0, count=12, fps=14.0),
                    dict(id="left", label="↩ Steer Left (12f)", start=12, count=12, fps=14.0),
                    dict(id="right", label="↪ Steer Right (12f)", start=24, count=12, fps=14.0),
                ]
            elif k == "progs/netsend_pc.md3" and nf >= 50:
                clips = [
                    dict(id="spit", label="💾 Spit Floppy Disks (42f)", start=8, count=nf - 8, fps=14.0),
                    dict(id="all", label=f"🎬 Pop-In + Full {nf}f", start=0, count=nf, fps=14.0),
                ]
            elif k == "progs/ltg_head.md3":
                clips = [
                    dict(id="turn", label="🔄 360° Turntable (24 Angles)", start=0, count=24, fps=10.0, turnaround=True, lie=True),
                    dict(id="spin", label="🎬 Spin All 24f", start=0, count=24, fps=10.0, lie=True),
                ]
            elif "clips" in hero and stride == 1:
                clips = hero["clips"]
            else:
                clips = auto_clips_from_names(names, nf, default_fps=fps_def)

            a_title, a_desc, a_badge = auto_nice_title_and_desc(k, cat, "MD3", nf0, len(skins_out) or 1)
            entry = dict(
                id=cid, cat=cat, status="vault" if is_vault else "active", fmt="MD3",
                badge=hero.get("badge", a_badge), title=hero.get("title", a_title),
                file=real, desc=hero.get("desc", a_desc),
                nf=int(nf), nv=int(tot_v), nt=int(tot_t), names=names,
                bbox=[pts_cat.min(axis=0).round(2).tolist(), pts_cat.max(axis=0).round(2).tolist()],
                surfaces=surfs_out, clips=clips,
            )
            if is_rigid:
                entry["rigidMats"] = packer.add_bytes(rigid_mats.tobytes())
            if skins_out:
                entry["skins"] = skins_out
            if k == "progs/ltg_head.md3":
                entry["turnDirs"] = 24
                entry["turnSign"] = -1
            if stem.startswith("v_") or k == "progs/ltg_v3d.md3":
                entry["pov"] = True
                entry.setdefault("az", 2.48)
                entry.setdefault("el", 0.21)
            for opt_k in ("pov", "defaultPov", "az", "el", "defaultSkin", "noSpin"):
                if opt_k in hero:
                    entry[opt_k] = hero[opt_k]

        # Attach VPS download & GLB bundle metadata to EVERY SINGLE MODEL!
        entry["rawRel"] = binfo["rel"]
        entry["rawSize"] = binfo["rawSize"]
        entry["bundleZip"] = binfo["bundleZip"]
        entry["bundleSize"] = binfo["bundleSize"]
        entry["bundleCount"] = binfo["bundleCount"]
        if binfo.get("glb"):
            entry["glb"] = binfo["glb"]
            entry["glbSize"] = binfo["glbSize"]
        entry["_sortKey"] = (hero.get("order", 999), 0 if entry["status"] == "active" else 1, k)
        models_out.append(entry)

    # Sort models: Sprites & Characters -> Custom Guns -> Cars & Vehicles -> Signature Props!
    cat_rank = {"sprites": 0, "guns": 1, "cars": 2, "props": 3}
    models_out.sort(key=lambda m: (cat_rank.get(m["cat"], 9), m["_sortKey"]))
    for m in models_out:
        m.pop("_sortKey", None)

    assert len(models_out) == len(CURATED_GALLERY_CATS), f"Mismatch: {len(models_out)} vs {len(CURATED_GALLERY_CATS)}"
    assert all(m["id"] in vps_man["bundles"] for m in models_out), "Curated model IDs missing from VPS bundles!"
    print(f"   Successfully packed all {len(models_out)} curated 3D models & 360° sprites using {len(packer.tex_list)} GPU textures/atlases!", flush=True)

    # 3. Prepare Map Preview Screenshots & Offline Highlight Audio Clips
    shot_map = {
        "bklan5": "fanpage/media/shots/map_bklan_megaman_bed.jpg",
        "bakolansmall": "fanpage/media/shots/map_bks_hero.jpg",
        "fox": "fanpage/media/shots/map_fox_marquee.jpg",
        "nanaplaza": "fanpage/media/shots/map_nana_arch.jpg",
        "gallup": "fanpage/media/shots/map_gallup_7705_front.jpg",
        "spruce": "fanpage/media/shots/map_spruce_water_tower.jpg",
        "bklan4": "fanpage/media/shots/megaman_bed_closeup.jpg",
        "bfarena": "fanpage/media/shots/map_bfarena_1.jpg",
        "aerowalk": "fanpage/media/shots/map_aerowalk_1.jpg",
    }
    os.makedirs(os.path.join(WEB_OUT_DIR, "map_shots"), exist_ok=True)
    maps_web, maps_inline = [], []
    for mp in vps_man["maps"]:
        m_web = dict(mp)
        m_inl = dict(mp)
        sp_rel = shot_map.get(mp["stem"])
        sp_full = os.path.join(MOD, sp_rel) if sp_rel else None
        if sp_full and os.path.isfile(sp_full):
            im = Image.open(sp_full).convert("RGB")
            im.thumbnail((480, 270), Image.Resampling.LANCZOS)
            bio = io.BytesIO()
            im.save(bio, "WEBP", quality=80, method=4)
            wb = bio.getvalue()
            shot_fn = f"map_shots/{mp['stem']}.webp"
            open(os.path.join(WEB_OUT_DIR, shot_fn), "wb").write(wb)
            m_web["shotUri"] = shot_fn
            m_inl["shotUri"] = "data:image/webp;base64," + base64.b64encode(wb).decode("ascii")
        maps_web.append(m_web)
        maps_inline.append(m_inl)

    # Embed 14 iconic lightweight WAVs inline for offline file:// preview, while all 318 stream from VPS
    inline_wav_set = {
        "sound/john/jwthrow.wav", "sound/funny/waveofhair.wav", "sound/weapons/pk_surprise.wav",
        "sound/netsend/ns_beep.wav", "sound/megaman/mm_honk1.wav", "sound/vehicles/horn_car.wav",
        "sound/vehicles/horn_bus.wav", "sound/daniel/ccc.wav", "sound/daniel/shaaa.wav",
        "sound/david/jackpot.wav", "sound/bryan/noway.wav", "sound/robeguy/flamingo.wav",
    }
    sounds_web = vps_man["sounds"]
    sounds_inline = []
    for s in sounds_web:
        s_cp = dict(s)
        sl = s["rel"].lower()
        if (sl in inline_wav_set or sl.startswith("sound/larry/") and s["size"] < 140_000) and len(inline_wav_set) > 0:
            if vfs.exists(sl) and s["size"] < 180_000 and sum(1 for x in sounds_inline if "uri" in x) < 16:
                b64w = base64.b64encode(vfs.read(sl)).decode("ascii")
                s_cp["uri"] = f"data:audio/wav;base64,{b64w}"
        sounds_inline.append(s_cp)

    # 4. Write Live Website Bundle (source/mm_tools/out/custom_assets_web/)
    print("3. Writing Live Website bundle to source/mm_tools/out/custom_assets_web/ ...", flush=True)
    web_tex_dir = os.path.join(WEB_OUT_DIR, "web_tex")
    os.makedirs(web_tex_dir, exist_ok=True)
    tex_list_web = []
    for ti, (t_meta, (ext, img_bytes)) in enumerate(zip(packer.tex_list, packer.tex_raw_files)):
        rel_t = f"web_tex/tex_{ti:04d}.{ext}"
        with open(os.path.join(WEB_OUT_DIR, rel_t), "wb") as f:
            f.write(img_bytes)
        tw_copy = dict(t_meta)
        tw_copy["uri"] = rel_t
        tex_list_web.append(tw_copy)

    raw_arena = bytes(packer.buf)
    gz_arena = gzip.compress(raw_arena, compresslevel=6)
    with open(os.path.join(WEB_OUT_DIR, "geom_arena.bin.gz"), "wb") as f:
        f.write(gz_arena)

    common_fields = dict(
        rawFileCount=vps_man["rawFileCount"],
        palette=PALETTE_U8.ravel().tolist(),
        anorm=ANORM_F32.round(4).ravel().tolist(),
        models=models_out,
        vaultTextures=vps_man["textures"],
        downloads=vps_man["downloads"],
        shaders=vps_man["shaders"],
    )

    meta_web = dict(common_fields, textures=tex_list_web, soundFiles=sounds_web, maps=maps_web)
    with open(os.path.join(WEB_OUT_DIR, "catalog_meta.js"), "w", encoding="utf-8") as f:
        f.write("window.__VAULT_META__ = ")
        json.dump(meta_web, f, separators=(",", ":"))
        f.write(";\n")

    tpl = open(TEMPLATE_PATH, "r", encoding="utf-8").read()
    assert "<!--__DATA_SCRIPTS__-->" in tpl, "Missing <!--__DATA_SCRIPTS__--> in template!"

    web_inject = (
        '<script src="catalog_meta.js"></script>\n'
        '<script>window.__VAULT_CFG__ = { mode: "web", base: "" };</script>'
    )
    with open(os.path.join(WEB_OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(tpl.replace("<!--__DATA_SCRIPTS__-->", web_inject, 1))

    # 5. Write Self-Contained Single-File HTML (G:\Quake\Combat\BakersfieldQuake\all_custom_assets.html)
    print(f"4. Writing Self-Contained HTML Showcase to {SELF_HTML_OUT} ...", flush=True)
    meta_inline = dict(common_fields, textures=packer.tex_list, soundFiles=sounds_inline, maps=maps_inline)
    meta_inline_json = json.dumps(meta_inline, separators=(",", ":"))
    b64_gz = base64.b64encode(gz_arena).decode("ascii")
    inline_inject = (
        f'<script id="meta-json" type="application/json">{meta_inline_json}</script>\n'
        f'<script id="bin-gz" type="text/plain">{b64_gz}</script>\n'
        '<script>window.__VAULT_CFG__ = { mode: "inline", base: "https://bakersfield.larrywew.fun/custom-assets/" };</script>'
    )
    with open(SELF_HTML_OUT, "w", encoding="utf-8") as f:
        f.write(tpl.replace("<!--__DATA_SCRIPTS__-->", inline_inject, 1))

    # 6. Also Build Local Master ZIP on user's PC!
    print("5. Building Local Master All-In-One ZIP...", flush=True)
    build_local_master_zip(vfs)

    web_tex_total = sum(len(b) for _, b in packer.tex_raw_files)
    print(
        f"\nALL LOCAL BUILDS COMPLETE in {time.time()-t_start:.1f}s!\n"
        f"  - Models/Sprites packed: {len(models_out)} (0 missed)\n"
        f"  - GPU Textures/Atlases:  {len(packer.tex_list)} ({web_tex_total/1e6:.2f} MB WebP/PNG)\n"
        f"  - Geometry Arena:        {len(raw_arena)/1e6:.2f} MB raw -> {len(gz_arena)/1e6:.2f} MB gzip\n"
        f"  - Web index.html + JS:   {(os.path.getsize(os.path.join(WEB_OUT_DIR, 'index.html')) + os.path.getsize(os.path.join(WEB_OUT_DIR, 'catalog_meta.js')))/1e6:.2f} MB\n"
        f"  - Self-Contained HTML:   {SELF_HTML_OUT} ({os.path.getsize(SELF_HTML_OUT)/1e6:.2f} MB)\n"
        f"  - Local Master ZIP:      {LOCAL_MASTER_ZIP} ({os.path.getsize(LOCAL_MASTER_ZIP)/1e6:.1f} MB)",
        flush=True,
    )


if __name__ == "__main__":
    main()
