r"""Builds G:\Quake\Combat\BakersfieldQuake\all_custom_assets.html:
A 100% self-contained, offline interactive WebGL2 + 2D Sprite Studio packing ALL ~120 custom assets
in BakersfieldQuake (and archived vaults):
  1. Custom Guns, Viewmodels, 3rd-Person Rigs & Pickups (MD3, MDL, SPR32, 2D Video Shaders)
  2. Custom 3D Characters, Sculpted Heads, Mega-Man Riders & Automated Sentries
  3. Custom 2D Sprites (.SPR32, .SPR) & 360-Degree Multi-Angle Turnarounds
  4. Exotic Pink Supercar, Driveable Ground Vehicles, Walk-In Van, Aircraft & Flight Gear
  5. Deployable PCs, Projectiles, Contraptions, Explosions, Debris & Shader FX
  + Live Drag-and-Drop / File Picker for any .MD3, .MDL, .SPR32, .SPR (+ .PNG/.JPG/.WEBP skin) on disk!

Usage:
    python3.13 source/mm_tools/build_all_custom_assets_html.py
"""
import base64
import glob
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
from scipy import ndimage, sparse
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(MOD, ".."))
PROGS = os.path.join(MOD, "progs")
SOUND = os.path.join(MOD, "sound")
SCRIPTS = os.path.join(MOD, "scripts")
BKP_CHARS = os.path.join(ROOT, "_backups", "player_bodies_removed_2026-10-30", "progs")
ID1_PAK0 = os.path.join(ROOT, "id1", "pak0.pak")
ANORM_JSON = os.path.join(ROOT, "monster_page", "anorm.json")
TEMPLATE = os.path.join(HERE, "all_custom_assets.template.html")
OUT_HTML = os.path.join(MOD, "all_custom_assets.html")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_head_grenade as bhg
import build_sky_vehicles as bsv


# --------------------------------------------------------------------------- PAK, Palette & Quake Normals
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


def pack_voice_soundboard():
    specs = [
        (os.path.join(SOUND, "john", "jwthrow.wav"),      '🌊 "JOHN WAVE!"'),
        (os.path.join(SOUND, "funny", "waveofhair.wav"),  '💇 "Wave of Hair!"'),
        (os.path.join(SOUND, "john", "jv00.wav"),         '🎙 John Quip #1'),
        (os.path.join(SOUND, "john", "jv01.wav"),         '🎙 John Quip #2'),
        (os.path.join(SOUND, "john", "jv02.wav"),         '🎙 John Quip #3'),
        (os.path.join(SOUND, "weapons", "pk_surprise.wav"), '🥒 "Pickle Surprise!"'),
        (os.path.join(SOUND, "netsend", "ns_beep.wav"),   '💾 NetSend Beep'),
    ]
    out = []
    for wav_p, label in specs:
        if os.path.isfile(wav_p) and os.path.getsize(wav_p) < 600_000:
            b64 = base64.b64encode(open(wav_p, "rb").read()).decode("ascii")
            out.append(dict(label=label, uri=f"data:audio/wav;base64,{b64}"))
    return out


# --------------------------------------------------------------------------- Binary Arena & WebP Texture/Atlas Store
class ArenaPacker:
    def __init__(self):
        self.buf = bytearray()
        self.tex_map = {}
        self.tex_list = []

    def add_bytes(self, raw_bytes):
        while len(self.buf) & 7:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(raw_bytes)
        return [off, len(raw_bytes)]

    def add_tex_pil(self, cache_key, label_key, im, max_dim=768, quality=85,
                    force_png=False, nearest=False, wrap=False, lift=1.0):
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
            rgb = np.clip(((arr[:, :, :3] / 255.0) ** 0.86) * float(lift), 0.0, 1.0)
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
            mime = "image/png"
        else:
            im.save(bio, "WEBP", quality=quality, method=4)
            mime = "image/webp"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[cache_key] = idx
        self.tex_list.append(dict(
            key=label_key,
            w=w,
            h=h,
            uri=uri,
            alpha=bool(has_alpha),
            nearest=bool(nearest or max(w0, h0) <= 16),
            noMip=False,
            wrap=bool(wrap),
            cols=1,
            rows=1,
            tileW=w,
            tileH=h,
            pad=0,
            count=1,
        ))
        return idx

    def add_tex_file(self, path, max_dim=768, quality=85, force_png=False, nearest=False, wrap=False, lift=1.0):
        abs_p = os.path.abspath(path)
        ck = ("file", abs_p, max_dim, bool(force_png), bool(nearest), bool(wrap), round(float(lift), 2))
        if ck in self.tex_map:
            return self.tex_map[ck]
        im = Image.open(abs_p)
        im.load()
        return self.add_tex_pil(
            ck, os.path.basename(abs_p), im,
            max_dim=max_dim, quality=quality, force_png=force_png, nearest=nearest, wrap=wrap, lift=lift,
        )

    def add_atlas(self, atlas_id, frames_pil, max_tile_dim=224, pad=2, quality=84, nearest=False):
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

        # Ensure final atlas stays well inside WebGL2's 4096x4096 minimum guarantee
        cols = max(1, int(math.ceil(math.sqrt(n * (th / float(max(1, tw)))))))
        rows = int(math.ceil(n / float(cols)))
        while max(cols * (tw + 2 * pad), rows * (th + 2 * pad)) > 4000 and max(tw, th) > 32:
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
                # Preserve aspect ratio centered inside (tw, th) if source frames vary in width (like .spr32)
                if im_rgba.size[0] != mw0 or im_rgba.size[1] != mh0:
                    canvas = Image.new("RGBA", (mw0, mh0), (0, 0, 0, 0))
                    ox = (mw0 - im_rgba.size[0]) // 2
                    oy = mh0 - im_rgba.size[1]
                    canvas.paste(im_rgba, (ox, oy))
                    im_rgba = canvas
                im_rgba = im_rgba.resize((tw, th), resample)
            arr = np.asarray(im_rgba, dtype=np.uint8)
            if pad > 0:
                padded = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
            else:
                padded = arr
            c, r = idx_f % cols, idx_f // cols
            atlas_np[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = padded

        atlas_im = Image.fromarray(atlas_np, "RGBA")
        bio = io.BytesIO()
        if nearest and max(aw, ah) <= 512:
            atlas_im.save(bio, "PNG", optimize=True)
            mime = "image/png"
        else:
            atlas_im.save(bio, "WEBP", quality=quality, method=4)
            mime = "image/webp"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        t_idx = len(self.tex_list)
        self.tex_map[ck] = t_idx
        self.tex_list.append(dict(
            key=atlas_id,
            w=aw,
            h=ah,
            uri=uri,
            alpha=True,
            nearest=bool(nearest),
            noMip=True,
            wrap=False,
            cols=cols,
            rows=rows,
            tileW=tw,
            tileH=th,
            pad=pad,
            count=n,
        ))
        return t_idx


# --------------------------------------------------------------------------- Fast Vectorized Geometry & Encoders
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
    assert nv < 65535, f"Surface {sname} nv={nv} exceeds Uint16 limit!"
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
        name=sname,
        shader=shader,
        nv=int(nv),
        nt=int(nt),
        ne=int(len(edges_u16)),
        nfGeom=int(nf),
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
        roughness=float(mat.get("roughness", 0.50)),
        spec=float(mat.get("spec", 0.40)),
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


def read_md3_fast(path):
    d = open(path, "rb").read()
    ident, ver, name_b, flags, nf, ntags, ns, nsk, ofs_f, ofs_t, ofs_s, ofs_e = struct.unpack("<4si64s9i", d[:108])
    assert ident == b"IDP3" and ver == 15, f"Invalid MD3: {path}"
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
    return dict(
        name=name_b.split(b"\0", 1)[0].decode("ascii", "replace"),
        nframes=nf,
        frame_names=fnames,
        surfaces=surfaces,
    )


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
        err = float(np.max(np.abs((P0 @ A + t) - Pf)))
        if err > 0.04:
            return None
        mats[f, 0:3] = A[0, :]
        mats[f, 3:6] = A[1, :]
        mats[f, 6:9] = A[2, :]
        mats[f, 9:12] = t
    return mats


def parse_raw_mdl(path):
    d = open(path, "rb").read() if isinstance(path, str) else path
    h = struct.unpack_from("<4si3f3ff3f8if", d, 0)
    assert h[0] == b"IDPO" and h[1] == 6
    scale = np.array(h[2:5], dtype=np.float32)
    trans = np.array(h[5:8], dtype=np.float32)
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
    names, pos_u8, nrm_u8 = [], [], []
    for _ in range(nf):
        kind = struct.unpack_from("<i", d, o)[0]
        assert kind == 0
        o += 12
        names.append(d[o:o + 16].split(b"\0", 1)[0].decode("ascii", "replace").strip())
        o += 16
        v = np.frombuffer(d, np.uint8, nvo * 4, o).reshape(nvo, 4)
        o += nvo * 4
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

    return dict(
        sw=sw, sh=sh, nv=len(vmap), nt=nt, nf=nf,
        names=names,
        uv=np.asarray(uv, dtype="<f4"),
        tris=np.asarray(tris, dtype=np.int32),
        all_v=pos_stack,
        all_n=nrm_stack,
        skins8=skins8,
    )


PLAYER_259_NAMES = None


def get_player_259_names():
    global PLAYER_259_NAMES
    if PLAYER_259_NAMES is None:
        r = parse_raw_mdl(load_pak_entry(ID1_PAK0, "progs/player.mdl"))
        nms = list(r["names"])
        while len(nms) < 259:
            nms.append(f"ext{len(nms) - 142}")
        PLAYER_259_NAMES = nms[:259]
    return PLAYER_259_NAMES


def auto_clips_from_names(names, nf, default_fps=11.0):
    if nf <= 1:
        return [dict(id="static", label="🗿 Static Mesh (Frame 0)", start=0, count=1, fps=10.0, lie=True)]
    groups = []
    for i, raw_nm in enumerate(names):
        base = re.sub(r"[_\-\s]*\d+$", "", raw_nm or "").strip().lower()
        if not base or base in ("f", "frame"):
            base = "anim"
        if groups and groups[-1][0] == base:
            groups[-1][2] += 1
        else:
            groups.append([base, i, 1])
    if len(groups) <= 1 or len(groups) > 18:
        if nf == 259:
            return [
                dict(id="stand", label="🧍 Stand (5f)", start=12, count=5, fps=10.0),
                dict(id="run", label="🏃 Run (6f)", start=6, count=6, fps=12.0),
                dict(id="shotatt", label="🔫 Shoot (6f)", start=113, count=6, fps=12.0),
                dict(id="nailatt", label="⚡ Rapid Fire (2f)", start=103, count=2, fps=10.0),
                dict(id="pain", label="💢 Pain (6f)", start=29, count=6, fps=10.0),
                dict(id="all", label="🎬 All 259 Poses", start=0, count=259, fps=14.0),
            ]
        return [dict(id="all", label=f"🎬 All {nf} Frames", start=0, count=nf, fps=default_fps)]
    clips = []
    for base, st, cnt in groups:
        if base == "gone" and cnt == 1:
            continue
        nice = base.replace("_", " ").title()
        clips.append(dict(id=f"{base}_{st}", label=f"▶ {nice} ({cnt}f)", start=st, count=cnt, fps=default_fps))
    clips.append(dict(id="all", label=f"🎬 All {nf}f", start=0, count=nf, fps=default_fps))
    return clips


# --------------------------------------------------------------------------- High-Level MD3, MDL, Sprite & Procedural Builders
def auto_resolve_mat(packer, shader, model_dir, stem, lift_default=1.25):
    base = os.path.basename(shader)
    # Check van_walkin TGA textures
    if shader.startswith("textures/van_walkin/"):
        p = os.path.join(MOD, shader + ".tga")
        tid = packer.add_tex_file(p, max_dim=512)
        is_glass = "glass" in base
        is_lit = base in ("cabin_light", "headlamp", "marker_amber", "tail_red")
        is_chr = base in ("chrome", "steel_rim")
        return dict(
            tex=tid,
            metallic=0.82 if is_chr else (0.55 if is_glass else 0.14),
            roughness=0.18 if (is_chr or is_glass) else 0.54,
            spec=0.88 if (is_chr or is_glass) else 0.35,
            unlit=is_lit,
            alphaBlend=is_glass,
        )

    # Pocket rocket texture mapping
    if base.startswith("pr_"):
        pr_tex_dir = os.path.join(HERE, "out", "pocket_rocket", "textures")
        pr_name = base.replace("pr_char_", "tex_").replace("pr_", "tex_") + ".png"
        p = os.path.join(pr_tex_dir, pr_name)
        is_fx = "speedlines" in base
        tid = packer.add_tex_file(p, max_dim=768 if not is_fx else 256, force_png=is_fx)
        return dict(
            tex=tid,
            metallic=0.06,
            roughness=0.52,
            spec=0.32,
            unlit=is_fx,
            additive=is_fx,
            alphaTest=packer.tex_list[tid]["alpha"] and not is_fx,
        )

    cands = []
    if stem == "v_banana_girl":
        cands.append(os.path.join(model_dir, "v_banana_girl.png"))
    cands.extend([
        os.path.join(model_dir, base + ".png"),
        os.path.join(model_dir, base + ".tga"),
        os.path.join(PROGS, base + ".png"),
        os.path.join(PROGS, base + ".tga"),
        os.path.join(HERE, "out", "progs", base + ".png"),
        os.path.join(HERE, "out", "megaman_weapon", base + ".png"),
        os.path.join(model_dir, stem + ".png"),
    ])
    found = next((c for c in cands if os.path.isfile(c)), None)
    assert found is not None, f"Cannot resolve texture for shader={shader} stem={stem} dir={model_dir}"
    is_add = any(k in base for k in ("zap", "laser", "flash", "fx", "arc", "aura"))
    is_unlit = is_add or any(k in base for k in ("scr", "leds", "glow", "foam", "tank", "hm_scr"))
    max_d = 768 if base in ("girl", "v_banana_girl", "megaman", "pickle3d") else 512
    lift = 1.0 if (is_unlit or "out" in found.replace("\\", "/")) else lift_default
    tid = packer.add_tex_file(found, max_dim=max_d, force_png=is_add, lift=lift)
    has_a = packer.tex_list[tid]["alpha"]
    return dict(
        tex=tid,
        metallic=0.35 if "metal" in base else 0.14,
        roughness=0.36 if "metal" in base else 0.54,
        spec=0.55 if "metal" in base else 0.36,
        unlit=is_unlit,
        additive=is_add,
        alphaTest=has_a and not is_add,
    )


def pack_md3_asset(packer, path, meta, surf_mats=None, bbox_frames=None,
                   allow_rigid=True, frame_stride=1, lift_default=1.25, extra_surfaces=None):
    m = read_md3_fast(path)
    mdir = os.path.dirname(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    surf_mats = surf_mats or {}

    if frame_stride > 1 and m["nframes"] > frame_stride:
        idx_keep = list(range(0, m["nframes"], frame_stride))
        m["nframes"] = len(idx_keep)
        m["frame_names"] = [m["frame_names"][i] for i in idx_keep]
        for s in m["surfaces"]:
            if len(s["all_v"]) > frame_stride:
                s["all_v"] = s["all_v"][idx_keep]
                s["all_n"] = s["all_n"][idx_keep]

    nf = m["nframes"]
    rigid_mats = try_rigid_fit_fast(m) if (allow_rigid and nf >= 24) else None
    is_rigid = rigid_mats is not None

    if bbox_frames is None:
        if nf == 259:
            bbox_frames = list(range(12, 17))
        elif nf >= 16 and stem.startswith("v_"):
            bbox_frames = list(range(0, 8))
        else:
            bbox_frames = list(range(min(nf, 6)))

    surfs_out = []
    tot_v, tot_t = 0, 0
    solid_pts = []

    for s in m["surfaces"]:
        sname, shader = s["name"], s["shader"]
        nv, nt = len(s["st"]), len(s["tris"])
        tot_v += nv
        tot_t += nt

        mat = surf_mats.get(sname) or surf_mats.get(shader)
        if mat is None:
            mat = auto_resolve_mat(packer, shader, mdir, stem, lift_default=lift_default)

        if not mat.get("additive", False):
            for fi in bbox_frames:
                if 0 <= fi < len(s["all_v"]):
                    vv = s["all_v"][fi]
                    if stem == "pickle" and np.allclose(vv, 0.0):
                        continue
                    solid_pts.append(vv)

        v_pack = s["all_v"][:1] if is_rigid else s["all_v"]
        n_pack = s["all_n"][:1] if is_rigid else s["all_n"]
        surfs_out.append(encode_surface(packer, sname, shader, s["st"], s["tris"], v_pack, n_pack, mat))

    if extra_surfaces:
        for es in extra_surfaces:
            surfs_out.append(es)
            tot_v += es["nv"]
            tot_t += es["nt"]

    if not solid_pts:
        solid_pts = [m["surfaces"][0]["all_v"][0]]
    pts_cat = np.vstack(solid_pts)
    bmin = pts_cat.min(axis=0).round(2).tolist()
    bmax = pts_cat.max(axis=0).round(2).tolist()

    names = get_player_259_names() if nf == 259 else m["frame_names"]
    clips = meta.get("clips") or auto_clips_from_names(names, nf, default_fps=meta.get("fps", 12.0))

    out = dict(
        fmt="MD3",
        status="active",
        nf=int(nf),
        nv=int(tot_v),
        nt=int(tot_t),
        names=names,
        bbox=[bmin, bmax],
        surfaces=surfs_out,
        clips=clips,
    )
    if is_rigid:
        out["rigidMats"] = packer.add_bytes(rigid_mats.tobytes())
    out.update(meta)
    return out


def load_mdl_skins(packer, path, r, skin_labels=None):
    tids = []
    for i in range(6):
        tp = f"{path}_{i}.tga"
        if os.path.isfile(tp):
            tids.append(packer.add_tex_file(tp, max_dim=768))
    if not tids:
        for si, s8 in enumerate(r["skins8"]):
            rgb = PALETTE_U8[s8]
            im = Image.fromarray(rgb.astype(np.uint8), "RGB")
            near = max(r["sw"], r["sh"]) <= 320
            tid = packer.add_tex_pil(
                ("mdl_skin", os.path.abspath(path), si),
                f"{os.path.basename(path)}_skin{si}",
                im, max_dim=768, force_png=near, nearest=near,
            )
            tids.append(tid)
    skins = []
    if len(tids) > 1:
        for si, tid in enumerate(tids):
            lbl = skin_labels[si] if (skin_labels and si < len(skin_labels)) else f"Skin {si}"
            skins.append(dict(label=lbl, map={"mdl_body": dict(tex=tid)}))
    return tids, skins


def pack_mdl_asset(packer, path, meta, skin_labels=None, unlit=False, additive=False):
    r = parse_raw_mdl(path)
    tids, skins = load_mdl_skins(packer, path, r, skin_labels=skin_labels)
    idle_idx = [i for i, nm in enumerate(r["names"]) if nm != "gone"][:16] or [0]
    pts_idle = r["all_v"][idle_idx].reshape(-1, 3)
    bmin = pts_idle.min(axis=0).round(2).tolist()
    bmax = pts_idle.max(axis=0).round(2).tolist()

    mat = dict(
        tex=tids[0],
        metallic=0.18,
        roughness=0.52,
        spec=0.38,
        unlit=unlit,
        additive=additive,
    )
    s_enc = encode_surface(packer, "mdl_body", os.path.basename(path), r["uv"], r["tris"], r["all_v"], r["all_n"], mat)
    clips = meta.get("clips") or auto_clips_from_names(r["names"], r["nf"], default_fps=meta.get("fps", 10.0))

    out = dict(
        fmt="MDL",
        status="active",
        nf=int(r["nf"]),
        nv=int(s_enc["nv"]),
        nt=int(s_enc["nt"]),
        names=r["names"],
        bbox=[bmin, bmax],
        surfaces=[s_enc],
        clips=clips,
    )
    if skins:
        out["skins"] = skins
    out.update(meta)
    return out


def parse_spr_frames(path):
    d = open(path, "rb").read()
    magic, ver, tp, rad, mw, mh, nf = struct.unpack_from("<4siifiii", d, 0)
    assert magic == b"IDSP", path
    o = 36
    frames = []
    for _ in range(nf):
        grp = struct.unpack_from("<i", d, o)[0]
        assert grp == 0, f"Sprite group frames unsupported in {path}"
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
        frames.append((Image.fromarray(rgba, "RGBA"), ox, oy, fw, fh))
    return dict(ver=ver, type=tp, mw=mw, mh=mh, nf=nf, frames=frames)


def make_quad_surface(packer, sname, shader, v_quad, n_quad, mat):
    uv = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], dtype="<f4")
    tris = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int32)
    return encode_surface(
        packer, sname, shader, uv, tris,
        np.asarray(v_quad, dtype=np.float32)[None, :, :],
        np.asarray(n_quad, dtype=np.float32)[None, :, :],
        mat,
    )


def pack_spr_asset(packer, path, meta, scale_u=0.5, mode="auto", max_tile_dim=224):
    sp = parse_spr_frames(path)
    pil_frames = [f[0] for f in sp["frames"]]
    nearest = (sp["ver"] == 1) or max(sp["mw"], sp["mh"]) <= 64
    tid = packer.add_atlas(os.path.basename(path), pil_frames, max_tile_dim=max_tile_dim, pad=2, nearest=nearest)
    nf = sp["nf"]
    hw = sp["mw"] * scale_u * 0.5
    hh = sp["mh"] * scale_u

    if mode == "pov_hand":
        # Eye-space first-person hand card in front of camera (+X)
        vq = [[16.0, +13.0, -13.5], [16.0, +13.0, +2.5], [16.0, -13.0, +2.5], [16.0, -13.0, -13.5]]
        nq = [[-1.0, 0.0, 0.0]] * 4
        bbox = [[15.0, -13.0, -13.5], [17.0, 13.0, 2.5]]
        bb = 0
        anim_fps = 14.0
    elif mode == "floor":
        # Oriented horizontal floor ripple at z=0.5
        vq = [[-hw, -hw, 0.5], [+hw, -hw, 0.5], [+hw, +hw, 0.5], [-hw, +hw, 0.5]]
        nq = [[0.0, 0.0, 1.0]] * 4
        bbox = [[-hw, -hw, 0.0], [hw, hw, 2.0]]
        bb = 0
        anim_fps = 12.0
    else:
        vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
        nq = [[-1.0, 0.0, 0.0]] * 4
        bbox = [[-hw, -hw, 0.0], [hw, hw, hh]]
        bb = 1
        anim_fps = 10.0 if nf > 1 else 0.0

    is_add = meta.get("additive", False)
    s_enc = make_quad_surface(packer, "sprite_quad", os.path.basename(path), vq, nq, dict(
        tex=tid,
        animFps=anim_fps if bb == 0 else 0.0,
        unlit=True,
        additive=is_add,
        alphaTest=not is_add,
        alphaBlend=not is_add,
        billboard=bb,
    ))

    # Determine clip layout
    turn_dirs = 0
    if "clips" in meta:
        clips = meta["clips"]
        turn_dirs = meta.get("turnDirs", 0)
    elif nf == 56:
        # MegaKart / Friend 8-direction layout: 0..7 idle (8x1), 8..55 run (8x6)
        turn_dirs = 8
        clips = [
            dict(id="run", label="🏃 Run Loop (8-Dir × 6f)", start=0, count=6, fps=10.0,
                 sprMode=dict(base=8, dirs=8, fpd=6, fps=10.0)),
            dict(id="idle", label="🧍 Idle Stand (8-Dir × 1f)", start=0, count=1, fps=8.0,
                 sprMode=dict(base=0, dirs=8, fpd=1, fps=8.0)),
        ]
    elif mode == "turn16" or (nf == 16 and "head" in os.path.basename(path)):
        turn_dirs = 16
        clips = [
            dict(id="turn", label="🔄 360° Turnaround (16 Angles)", start=0, count=1, fps=10.0,
                 sprMode=dict(base=0, dirs=16, fpd=1, fps=10.0)),
        ]
    else:
        clips = [
            dict(id="anim", label=f"🎬 Sprite Sequence ({nf}f)", start=0, count=nf, fps=anim_fps or 10.0,
                 sprMode=dict(base=0, dirs=1, fpd=nf, fps=anim_fps or 10.0)),
        ]

    out = dict(
        fmt="SPR32" if sp["ver"] == 32 else "SPR",
        status="active",
        nf=int(nf),
        nv=4,
        nt=2,
        bbox=bbox,
        isSprite=True,
        turnDirs=int(turn_dirs),
        turnSign=-1 if turn_dirs > 1 else 1,
        surfaces=[s_enc],
        clips=clips,
    )
    out.update(meta)
    return out


# --------------------------------------------------------------------------- Special Procedural & Voxel-Hull Models
def build_calm_john_asset(packer, t_calm):
    calm_m = bhg.build()
    MH, NH = bhg.MH, bhg.NH
    V_raw = calm_m["V"]
    ring_V = V_raw[:MH * NH].reshape(MH, NH, 3)
    bot_pole, top_pole = V_raw[MH * NH], V_raw[MH * NH + 1]

    verts_c, uvs_c, tris_c = [], [], []
    cols = NH + 1
    for j in range(MH):
        vv_uv = (MH - 1 - j) / float(MH - 1)
        for k in range(cols):
            verts_c.append(ring_V[j, k % NH])
            uvs_c.append((k / float(NH), vv_uv))
    i_bot = len(verts_c)
    verts_c.append(bot_pole)
    uvs_c.append((0.5, 1.0))
    i_top = len(verts_c)
    verts_c.append(top_pole)
    uvs_c.append((0.5, 0.0))

    verts_c = np.asarray(verts_c, dtype=np.float32) * 2.2
    verts_c[:, 2] -= float(verts_c[:, 2].min())
    uvs_c = np.asarray(uvs_c, dtype=np.float32)

    def add_outward_tri(a, b, c, out_dir):
        fn = np.cross(verts_c[b] - verts_c[a], verts_c[c] - verts_c[a])
        if float(np.dot(fn, out_dir)) < 0.0:
            b, c = c, b
        tris_c.append((a, b, c))

    for j in range(MH - 1):
        rc = 0.5 * (ring_V[j].mean(axis=0) + ring_V[j + 1].mean(axis=0)) * 2.2
        rc[2] = 0.5 * (verts_c[j * cols:(j + 1) * cols, 2].mean() + verts_c[(j + 1) * cols:(j + 2) * cols, 2].mean())
        for k in range(NH):
            a = j * cols + k
            b, d = a + 1, (j + 1) * cols + k
            c = d + 1
            cen = 0.25 * (verts_c[a] + verts_c[b] + verts_c[c] + verts_c[d])
            add_outward_tri(a, b, c, cen - rc)
            add_outward_tri(a, c, d, cen - rc)
    for k in range(NH):
        add_outward_tri(k, k + 1, i_bot, np.array([0.0, 0.0, -1.0], dtype=np.float32))
        top_row = (MH - 1) * cols
        add_outward_tri(top_row + k, top_row + k + 1, i_top, np.array([0.0, 0.0, +1.0], dtype=np.float32))

    tris_c = np.asarray(tris_c, dtype=np.int32)
    norms_c = np.zeros_like(verts_c)
    fn_all = np.cross(verts_c[tris_c[:, 1]] - verts_c[tris_c[:, 0]], verts_c[tris_c[:, 2]] - verts_c[tris_c[:, 0]])
    for c_i in range(3):
        np.add.at(norms_c, tris_c[:, c_i], fn_all)
    for j in range(MH):
        i0, i1 = j * cols, j * cols + NH
        sn = norms_c[i0] + norms_c[i1]
        norms_c[i0], norms_c[i1] = sn, sn
    norms_c /= np.maximum(np.linalg.norm(norms_c, axis=1, keepdims=True), 1e-8)

    s_enc = encode_surface(packer, "calm_john_head", "progs/jw_air_calm", uvs_c, tris_c,
                           verts_c[None, ...], norms_c[None, ...],
                           dict(tex=t_calm, metallic=0.05, roughness=0.58, spec=0.28))
    return dict(
        id="calm_john", cat="chars", status="active", fmt="MD3",
        badge="3D HEAD · DEADPAN JOHN",
        title="Deadpan Calm Lush-Hair 3D John Wave Bust",
        file="source/mm_tools/build_head_grenade.py (3D Bust)",
        script="source/mm_tools/build_head_grenade.py",
        desc="3D sculpted calm, lush-bearded John Wave portrait head reconstructed from front & back studio photos—serves as aviator co-pilot & Chinook fuselage!",
        nf=1, nv=s_enc["nv"], nt=s_enc["nt"],
        bbox=[verts_c.min(axis=0).round(2).tolist(), verts_c.max(axis=0).round(2).tolist()],
        surfaces=[s_enc],
        clips=[dict(id="static", label="🗿 3D Bust Mesh", start=0, count=1, fps=10.0, lie=True)],
    )


def build_pinklady3d_asset(packer, t_pink):
    npz = np.load(os.path.join(HERE, "out", "skyveh", "pinklady3d.npz"))
    v_base = npz["verts"].astype(np.float32)
    n_base = npz["norms"].astype(np.float32)
    uv_arr = npz["uvs"].astype(np.float32)
    tri_arr = npz["tris"].astype(np.int32)
    nf = 16
    sc = 1.65
    z_off = -float(v_base[:, 2].min()) * sc
    v_frames, n_frames = [], []
    for fi in range(nf):
        ph = 2.0 * math.pi * (fi / float(nf))
        vp, np_ = bsv.deform_pinklady(
            v_base, n_base,
            arm_wave_deg=14.0 * math.sin(ph),
            arm_fore_deg=6.0 * math.cos(ph),
            pod_breath=0.05 * math.sin(ph * 2.0),
            pod_bob=0.9 * math.sin(ph),
            ribbon_back=5.5 + 3.0 * math.sin(ph * 2.0),
            ribbon_sway=4.2 * math.cos(ph),
        )
        vp = vp * sc
        vp[:, 2] += z_off
        v_frames.append(vp)
        n_frames.append(np_)
    all_v = np.stack(v_frames, axis=0)
    all_n = np.stack(n_frames, axis=0)
    s_enc = encode_surface(packer, "pinklady_3d", "progs/skyveh_pinklady", uv_arr, tri_arr, all_v, all_n,
                           dict(tex=t_pink, metallic=0.06, roughness=0.50, spec=0.36))
    return dict(
        id="pinklady3d", cat="chars", status="active", fmt="MD3",
        badge="3D FIGURE · 16f",
        title="3D Hot-Pink Buoyant Twin-Sphere V-Arm Lady",
        file="source/mm_tools/out/skyveh/pinklady3d.npz",
        script="source/mm_tools/build_sky_vehicles.py",
        desc="Full watertight 3D figure reconstructed from Video 3 with articulated V-arms, breathing twin buoyant spheres, gold choker & fluttering ribbons!",
        nf=nf, nv=s_enc["nv"], nt=s_enc["nt"],
        bbox=[all_v[0].min(axis=0).round(2).tolist(), all_v[0].max(axis=0).round(2).tolist()],
        surfaces=[s_enc],
        clips=[
            dict(id="wave", label="💖 V-Arm Wave & Flutter (16f)", start=0, count=16, fps=12.0),
            dict(id="pose", label="🗿 Neutral Pose (Frame 0)", start=0, count=1, fps=10.0, lie=True),
        ],
    )


def build_pickle3d_asset(packer):
    N = 16
    GOOD = [k for k in range(N) if k != 9]
    UNIT, C, STEP = 20.0 / 512.0, 256.0, 2.0
    CROP = (148, 16, 364, 496)
    TILE_W, TILE_H = CROP[2] - CROP[0], CROP[3] - CROP[1]
    COLS, sgn = 5, -1

    masks = []
    for k in range(N):
        im = Image.open(os.path.join(PROGS, f"pickle_{k:02d}.png")).convert("RGBA")
        masks.append(ndimage.binary_dilation(np.asarray(im.getchannel("A")) > 128, iterations=2))

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
    vol = ndimage.binary_closing((cnt >= len(GOOD) - 1).reshape(gx.shape), iterations=1)
    lab, nlab = ndimage.label(vol)
    if nlab > 1:
        sizes = ndimage.sum(vol, lab, range(1, nlab + 1))
        vol = lab == (1 + int(np.argmax(sizes)))
    field = ndimage.gaussian_filter(vol.astype(np.float32), 1.0)
    verts, faces, _, _ = measure.marching_cubes(field, 0.5, spacing=(STEP, STEP, STEP), step_size=3)
    verts = verts + np.array([xs[0], ys[0], zs[0]])

    nv0 = len(verts)
    rows = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2], faces[:, 1], faces[:, 2], faces[:, 0]])
    cols = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0], faces[:, 0], faces[:, 1], faces[:, 2]])
    adj = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(nv0, nv0)).tocsr()
    adj.data[:] = 1.0
    deg = np.maximum(np.asarray(adj.sum(1)).ravel(), 1.0)[:, None]
    for _ in range(4):
        for f_w in (0.5, -0.53):
            verts = verts + f_w * ((adj @ verts) / deg - verts)

    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    fn = np.cross(b - a, c - a)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
    cen = (a + b + c) / 3.0
    flip = ((fn[:, 0] * cen[:, 0] + fn[:, 1] * cen[:, 1]) < 0) & ~(np.abs(cen[:, 2]) > 220)
    fn[flip] *= -1
    faces = faces.copy()
    faces[flip] = faces[flip][:, ::-1]

    cams = {k: np.array([-math.cos(math.radians(sgn * k * 360.0 / N)),
                         math.sin(math.radians(sgn * k * 360.0 / N)), 0.0]) for k in GOOD}
    score = np.stack([fn @ cams[k] for k in GOOD], 1)
    view = np.array(GOOD)[np.argmax(score, 1)]
    tile_idx = {k: i for i, k in enumerate(GOOD)}
    AW, AH = COLS * TILE_W, ((len(GOOD) + COLS - 1) // COLS) * TILE_H

    vn = np.zeros_like(verts)
    for fc, nrm in zip(faces, fn):
        for vi in fc:
            vn[vi] += nrm
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)

    out_v, out_n, out_st, out_t, key = [], [], [], [], {}
    for fc, k in zip(faces, view):
        tri = []
        ti = tile_idx[int(k)]
        phi = math.radians(sgn * int(k) * 360.0 / N)
        for vi in fc:
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
        out_t.append(tri)

    v_np = np.asarray(out_v, dtype=np.float32)
    n_np = np.asarray(out_n, dtype=np.float32)
    tid = packer.add_tex_file(os.path.join(HERE, "out", "progs", "pickle3d.png"), max_dim=768)
    s_enc = encode_surface(packer, "pickle3d_hull", "progs/pickle3d", out_st, out_t,
                           v_np[None, ...], n_np[None, ...],
                           dict(tex=tid, metallic=0.08, roughness=0.58, spec=0.30))
    return dict(
        id="pickle3d", cat="chars", status="vault", fmt="MD3",
        badge="VOXEL HULL · VAULT",
        title="Standing Pickle (3D Marching-Cubes Voxel Hull)",
        file="source/mm_tools/make_pickle3d.py + out/progs/pickle3d.png",
        script="source/mm_tools/make_pickle3d.py",
        desc="Experimental solid 3D marching-cubes visual hull carved from 15 turntable silhouettes of Pickle Surprise with Taubin smoothing.",
        nf=1, nv=s_enc["nv"], nt=s_enc["nt"],
        az=3.45, el=0.14,
        bbox=[v_np.min(axis=0).round(2).tolist(), v_np.max(axis=0).round(2).tolist()],
        surfaces=[s_enc],
        clips=[dict(id="static", label="🗿 3D Voxel Hull", start=0, count=1, fps=10.0, lie=True)],
    )


# --------------------------------------------------------------------------- Multi-Asset Constellations, Video Shaders & Studio Sprites
def build_sentry_assembly(packer):
    rb = parse_raw_mdl(os.path.join(PROGS, "turrbase.mdl"))
    rg = parse_raw_mdl(os.path.join(PROGS, "turrgun.mdl"))
    tb_tids, _ = load_mdl_skins(packer, os.path.join(PROGS, "turrbase.mdl"), rb)
    tg_tids, _ = load_mdl_skins(packer, os.path.join(PROGS, "turrgun.mdl"), rg)

    s_base = encode_surface(
        packer, "turrbase", "progs/turrbase.mdl", rb["uv"], rb["tris"], rb["all_v"], rb["all_n"],
        dict(tex=tb_tids[0], metallic=0.45, roughness=0.42, spec=0.58),
    )
    s_gun = encode_surface(
        packer, "turrgun", "progs/turrgun.mdl", rg["uv"], rg["tris"], rg["all_v"], rg["all_n"],
        dict(tex=tg_tids[0], metallic=0.52, roughness=0.38, spec=0.65),
    )
    pts = np.vstack([rb["all_v"][0], rg["all_v"][0]])
    skins = [
        dict(label=f"Sentry Level {i + 1}", map={"turrgun": dict(tex=tg_tids[i])})
        for i in range(len(tg_tids))
    ]
    return dict(
        id="sentry_turret", cat="chars", status="active", fmt="MDL",
        badge="ENGINEER SENTRY · 3 SKINS",
        title="Automated Sentry Gun Assembly (Base + 3-Skin Turret)",
        file="progs/turrbase.mdl + progs/turrgun.mdl",
        script="source/mm_tools/build_sentry.py",
        desc="Composite Team Fortress / Combat+ automated sentry gun combining the tripod base (turrbase.mdl) and 9-frame recoiling turret head (turrgun.mdl) across all 3 upgrade skins!",
        nf=int(rg["nf"]),
        nv=int(s_base["nv"] + s_gun["nv"]),
        nt=int(s_base["nt"] + s_gun["nt"]),
        names=rg["names"],
        bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
        skins=skins,
        surfaces=[s_base, s_gun],
        clips=auto_clips_from_names(rg["names"], rg["nf"], default_fps=10.0),
    )


def build_sentry_gibs(packer):
    surfs = []
    pts_all = []
    offsets = [(-14.0, 0.0, 6.0), (0.0, 0.0, 10.0), (+14.0, 0.0, 6.0)]
    for idx, (fn, off) in enumerate(zip(("tgib1.mdl", "tgib2.mdl", "tgib3.mdl"), offsets)):
        p = os.path.join(PROGS, fn)
        r = parse_raw_mdl(p)
        tids, _ = load_mdl_skins(packer, p, r)
        v_shifted = r["all_v"] + np.array(off, dtype=np.float32)[None, None, :]
        v_shifted[:, :, 2] -= min(0.0, float(v_shifted[:, :, 2].min()))
        pts_all.append(v_shifted[0])
        surfs.append(encode_surface(
            packer, f"tgib{idx + 1}", f"progs/{fn}", r["uv"], r["tris"], v_shifted, r["all_n"],
            dict(tex=tids[0], metallic=0.48, roughness=0.42, spec=0.55),
        ))
    pts = np.vstack(pts_all)
    return dict(
        id="sentry_gibs", cat="chars", status="active", fmt="MDL",
        badge="SENTRY DEBRIS · 3 PIECES",
        title="Destroyed Sentry Gun Gibs Pack (tgib1–3)",
        file="progs/tgib1.mdl + tgib2.mdl + tgib3.mdl",
        script="source/mm_tools/build_sentry.py",
        desc="All 3 metal shrapnel & barrel gibs thrown outward when an Engineer Sentry Gun explodes—use Solo in Surfaces to inspect each piece.",
        nf=1,
        nv=sum(s["nv"] for s in surfs),
        nt=sum(s["nt"] for s in surfs),
        bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
        surfaces=surfs,
        clips=[dict(id="static", label="💥 3-Piece Gibs Constellation", start=0, count=1, fps=10.0, lie=True)],
    )


def build_sparks_mdl(packer):
    rb = parse_raw_mdl(os.path.join(PROGS, "spark_blue.mdl"))
    ry = parse_raw_mdl(os.path.join(PROGS, "spark_yellow.mdl"))
    tb, _ = load_mdl_skins(packer, os.path.join(PROGS, "spark_blue.mdl"), rb)
    ty, _ = load_mdl_skins(packer, os.path.join(PROGS, "spark_yellow.mdl"), ry)
    s_enc = encode_surface(
        packer, "spark_burst", "progs/spark_blue.mdl", rb["uv"], rb["tris"], rb["all_v"], rb["all_n"],
        dict(tex=tb[0], unlit=True),
    )
    pts = rb["all_v"][:6].reshape(-1, 3)
    return dict(
        id="sparks_mdl", cat="props", status="active", fmt="MDL",
        badge="3D SPARK FX · 21f",
        title="3D Electric Spark Burst (Blue & Yellow Skins)",
        file="progs/spark_blue.mdl + progs/spark_yellow.mdl",
        desc="21-frame expanding 3D electric spark burst mesh with switchable Blue & Yellow skins!",
        nf=int(rb["nf"]),
        nv=int(s_enc["nv"]),
        nt=int(s_enc["nt"]),
        names=rb["names"],
        bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
        skins=[
            dict(label="⚡ Blue Spark", map={"spark_burst": dict(tex=tb[0])}),
            dict(label="✨ Yellow Spark", map={"spark_burst": dict(tex=ty[0])}),
        ],
        surfaces=[s_enc],
        clips=[dict(id="burst", label="⚡ 21f Spark Burst", start=0, count=int(rb["nf"]), fps=16.0)],
    )


def build_constellation_md3(packer, item_specs, meta, radius=18.0):
    """Packs multiple related single/animated MD3s into a clean ring constellation where every piece is a named surface."""
    surfs = []
    pts_all = []
    max_nf = 1
    n_items = len(item_specs)
    for idx, (label, path, mat_override) in enumerate(item_specs):
        m = read_md3_fast(path)
        mdir = os.path.dirname(path)
        stem = os.path.splitext(os.path.basename(path))[0]
        max_nf = max(max_nf, m["nframes"])
        if n_items > 1 and radius > 0.0:
            ang = 2.0 * math.pi * (idx / float(n_items))
            off = np.array([radius * math.cos(ang), radius * math.sin(ang), 0.0], dtype=np.float32)
        else:
            off = np.zeros(3, dtype=np.float32)
        for s in m["surfaces"]:
            v = s["all_v"].copy()
            # Center piece locally if placing on a ring
            if radius > 0.0 and n_items > 1:
                c_xy = 0.5 * (v[0, :, :2].min(axis=0) + v[0, :, :2].max(axis=0))
                z_min = float(v[0, :, 2].min())
                v[:, :, 0] += off[0] - c_xy[0]
                v[:, :, 1] += off[1] - c_xy[1]
                v[:, :, 2] += max(0.0, -z_min) + 2.0
            mat = mat_override or auto_resolve_mat(packer, s["shader"], mdir, stem)
            sname = label if len(m["surfaces"]) == 1 else f"{label}_{s['name']}"
            surfs.append(encode_surface(packer, sname, s["shader"], s["st"], s["tris"], v, s["all_n"], mat))
            pts_all.append(v[0])
    pts = np.vstack(pts_all)
    out = dict(
        fmt="MD3",
        status="active",
        nf=int(max_nf),
        nv=sum(s["nv"] for s in surfs),
        nt=sum(s["nt"] for s in surfs),
        bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
        surfaces=surfs,
        clips=[
            dict(id="all", label=f"🎬 {'Spin Loop' if max_nf > 1 else 'Constellation'} ({max_nf}f)",
                 start=0, count=max_nf, fps=14.0, lie=(max_nf == 1))
        ],
    )
    out.update(meta)
    return out


def build_anim_atlas_from_files(packer, atlas_id, frame_paths, max_tile_dim=256, quality=84):
    uniq_paths = []
    path_to_tile = {}
    for p in frame_paths:
        ap = os.path.abspath(p)
        if ap not in path_to_tile:
            path_to_tile[ap] = len(uniq_paths)
            uniq_paths.append(ap)
    imgs = [Image.open(ap).convert("RGBA") for ap in uniq_paths]
    tid = packer.add_atlas(atlas_id, imgs, max_tile_dim=max_tile_dim, pad=2, quality=quality)
    order = [path_to_tile[os.path.abspath(p)] for p in frame_paths]
    return tid, order


def build_jesskart_studio(packer):
    anim_dir = os.path.join(MOD, "jesskart_sprite", "anim")
    clean_dir = os.path.join(MOD, "jesskart_sprite", "clean")
    clean_imgs = [Image.open(os.path.join(clean_dir, f"jesskart_clean_{d:02d}.png")).convert("RGBA") for d in range(24)]
    turbo_imgs = [
        Image.open(os.path.join(anim_dir, f"turbo_{d:02d}_f{f}.png")).convert("RGBA")
        for d in range(24) for f in range(6)
    ] + clean_imgs
    wheelie_imgs = [
        Image.open(os.path.join(anim_dir, f"wheelie_{d:02d}_f{f}.png")).convert("RGBA")
        for d in range(24) for f in range(6)
    ] + clean_imgs

    tid_turbo = packer.add_atlas("jesskart_burnout_24x6", turbo_imgs, max_tile_dim=152, pad=2, quality=83)
    tid_wheel = packer.add_atlas("jesskart_wheelie_24x6", wheelie_imgs, max_tile_dim=152, pad=2, quality=83)

    hw, hh = 34.0, 68.0
    vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
    nq = [[-1.0, 0.0, 0.0]] * 4
    s_enc = make_quad_surface(packer, "jesskart_card", "jesskart_sprite", vq, nq, dict(
        tex=tid_turbo, unlit=True, alphaTest=True, alphaBlend=True, billboard=1,
    ))
    return dict(
        id="jesskart_studio", cat="sprites", status="active", fmt="SPR32",
        badge="24-ANGLE · 2 SKINS · 6f",
        title="JessKart 360° Studio Turnaround (Burnout, Wheelie & Clean)",
        file="jesskart_sprite/anim/* + jesskart_sprite/clean/*",
        script="source/mm_tools/build_jesskart_sprite.py",
        desc="Full 24-angle 360° studio sprite sheet with 2 skins (Nitro Flame Burnout & Chrome Sparks Wheelie) plus Clean 24-angle turnaround—drag horizontally or click 2D Pixel View!",
        nf=144, nv=4, nt=2,
        bbox=[[-hw, -hw, 0.0], [hw, hw, hh]],
        isSprite=True, turnDirs=24, turnSign=-1,
        skins=[
            dict(label="🔥 Nitro Burnout (24×6f)", map={"jesskart_card": dict(tex=tid_turbo)}),
            dict(label="⚡ Chrome Wheelie (24×6f)", map={"jesskart_card": dict(tex=tid_wheel)}),
        ],
        surfaces=[s_enc],
        clips=[
            dict(id="anim", label="🏁 360° Action Loop (24-Dir × 6f)", start=0, count=6, fps=12.0,
                 sprMode=dict(base=0, dirs=24, fpd=6, fps=12.0)),
            dict(id="clean", label="🏎️ Clean Kart Turnaround (24-Dir × 1f)", start=0, count=1, fps=10.0,
                 sprMode=dict(base=144, dirs=24, fpd=1, fps=10.0)),
        ],
    )


def build_scissor_studio(packer):
    sdir = os.path.join(MOD, "scissor_sprite")
    run_imgs = [
        Image.open(os.path.join(sdir, f"scissor_d{d}_f{f}.png")).convert("RGBA")
        for d in range(8) for f in range(8)
    ]
    turn12_imgs = [Image.open(os.path.join(sdir, f"scissor_{k:02d}.png")).convert("RGBA") for k in range(12)]
    tid = packer.add_atlas("scissor_studio_76", run_imgs + turn12_imgs, max_tile_dim=192, pad=2, quality=84)

    hw, hh = 34.0, 68.0
    vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
    nq = [[-1.0, 0.0, 0.0]] * 4
    s_enc = make_quad_surface(packer, "scissor_card", "scissor_sprite", vq, nq, dict(
        tex=tid, unlit=True, alphaTest=True, alphaBlend=True, billboard=1,
    ))
    return dict(
        id="scissor_studio", cat="sprites", status="active", fmt="SPR32",
        badge="8-DIR × 8f + 12-ANGLE",
        title="Giant Running Scissors High-Res Studio Turnaround",
        file="scissor_sprite/scissor_d0_f0..d7_f7.png + scissor_00..11.png",
        script="source/mm_tools/build_scissor_sprite.py",
        desc="High-resolution studio renders of the Giant Running Scissors: 8-direction × 8-frame snipping run cycle plus 12-angle turnaround sheet!",
        nf=64, nv=4, nt=2,
        bbox=[[-hw, -hw, 0.0], [hw, hw, hh]],
        isSprite=True, turnDirs=8, turnSign=-1,
        surfaces=[s_enc],
        clips=[
            dict(id="run8", label="✂️ 360° Running Snip (8-Dir × 8f)", start=0, count=8, fps=12.0,
                 sprMode=dict(base=0, dirs=8, fpd=8, fps=12.0)),
            dict(id="turn12", label="🔄 12-Angle Turnaround (12-Dir × 1f)", start=0, count=1, fps=10.0,
                 sprMode=dict(base=64, dirs=12, fpd=1, fps=10.0)),
        ],
    )


def build_earhead_studio(packer):
    edir = os.path.join(MOD, "earhead_sprite")
    imgs = [Image.open(os.path.join(edir, f"earhead_{d:02d}.png")).convert("RGBA") for d in range(24)]
    tid = packer.add_atlas("earhead_24", imgs, max_tile_dim=216, pad=2, quality=85)
    hw, hh = 28.0, 56.0
    vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
    nq = [[-1.0, 0.0, 0.0]] * 4
    s_enc = make_quad_surface(packer, "earhead_card", "earhead_sprite", vq, nq, dict(
        tex=tid, unlit=True, alphaTest=True, alphaBlend=True, billboard=1,
    ))
    return dict(
        id="earhead_studio", cat="sprites", status="active", fmt="SPR32",
        badge="24-ANGLE TURNAROUND",
        title="Ear-Head 24-Angle High-Res Studio Turnaround",
        file="earhead_sprite/earhead_00..23.png",
        desc="Crisp 24-angle (every 15°) studio turnaround of the screaming Big-Ears head—orbit 360°, click any degree button, or toggle 2D Pixel View!",
        nf=24, nv=4, nt=2,
        bbox=[[-hw, -hw, 0.0], [hw, hw, hh]],
        isSprite=True, turnDirs=24, turnSign=-1,
        surfaces=[s_enc],
        clips=[
            dict(id="turn24", label="🔄 360° Turnaround (24 Angles)", start=0, count=1, fps=10.0,
                 sprMode=dict(base=0, dirs=24, fpd=1, fps=10.0)),
        ],
    )


def build_ltg_head_md3(packer):
    """Packs progs/ltg_head.md3 (24-frame MD3 turntable) + progs/ltg_aura.md3 (8-frame animated Wi-Fi/cable aura)."""
    m_head = read_md3_fast(os.path.join(PROGS, "ltg_head.md3"))
    m_aura = read_md3_fast(os.path.join(PROGS, "ltg_aura.md3"))
    aura_paths = [os.path.join(PROGS, f"ltg_aura_{k:02d}.png") for k in range(8)]
    tid_aura, _ = build_anim_atlas_from_files(packer, "ltg_aura_8f", aura_paths, max_tile_dim=256)

    surfs = []
    pts_all = []
    for s in m_head["surfaces"]:
        base = os.path.basename(s["shader"]).replace("ltg_head_v", "ltg_head_") + ".png"
        tid = packer.add_tex_file(os.path.join(PROGS, base), max_dim=256)
        surfs.append(encode_surface(
            packer, s["name"], s["shader"], s["st"], s["tris"], s["all_v"], s["all_n"],
            dict(tex=tid, unlit=True, alphaTest=True),
        ))
        for fi in range(m_head["nframes"]):
            if not np.allclose(s["all_v"][fi], 0.0):
                pts_all.append(s["all_v"][fi])

    sa = m_aura["surfaces"][0]
    s_aura_enc = encode_surface(
        packer, "wifi_cable_aura", sa["shader"], sa["st"], sa["tris"], sa["all_v"], sa["all_n"],
        dict(tex=tid_aura, animFps=10.0, unlit=True, additive=True),
    )
    surfs.append(s_aura_enc)
    pts = np.vstack(pts_all)
    return dict(
        id="ltg_head_md3", cat="sprites", status="active", fmt="MD3",
        badge="24-VIEW MD3 + AURA",
        title="Laptop Gun Summoned Ear-Head + Wi-Fi/Cable Aura",
        file="progs/ltg_head.md3 + progs/ltg_aura.md3",
        script="source/mm_tools/build_ltgun_assets.py",
        desc="In-game 24-surface camera-reactive MD3 head paired with its 8-frame additive Wi-Fi & Ethernet cable aura (toggle aura via Skins or Surfaces!).",
        nf=24,
        nv=sum(s["nv"] for s in surfs),
        nt=sum(s["nt"] for s in surfs),
        bbox=[pts.min(axis=0).round(2).tolist(), pts.max(axis=0).round(2).tolist()],
        isSprite=False, turnDirs=24, turnSign=-1,
        skins=[
            dict(label="⚡ With Wi-Fi/Cable Aura", map={"wifi_cable_aura": dict(nodraw=False)}),
            dict(label="🗿 Clean Head Only", map={"wifi_cable_aura": dict(nodraw=True)}),
        ],
        surfaces=surfs,
        clips=[
            dict(id="turn", label="🔄 360° Turntable + Aura (24 Angles)", start=0, count=24, fps=10.0, turnaround=True, lie=True),
            dict(id="spin", label="🎬 Spin All 24 Frames", start=0, count=24, fps=10.0, lie=True),
        ],
    )


def build_pinklady_sprite(packer):
    turn_imgs = [Image.open(os.path.join(PROGS, f"pinklady_{d:02d}.png")).convert("RGBA") for d in range(16)]
    bounce_fwd = [Image.open(os.path.join(PROGS, f"pinklady_b{k:02d}.png")).convert("RGBA") for k in range(0, 36, 2)]
    bounce_pingpong = bounce_fwd + bounce_fwd[-2:0:-1]  # 34 ping-pong frames
    tid = packer.add_atlas("pinklady_turn16_bounce34", turn_imgs + bounce_pingpong, max_tile_dim=224, pad=2, quality=84)

    hw, hh = 26.0, 56.0
    vq = [[0.0, -hw, 0.0], [0.0, -hw, hh], [0.0, +hw, hh], [0.0, +hw, 0.0]]
    nq = [[-1.0, 0.0, 0.0]] * 4
    s_enc = make_quad_surface(packer, "pinklady_card", "progs/pinklady_v00", vq, nq, dict(
        tex=tid, unlit=True, alphaTest=True, alphaBlend=True, billboard=1,
    ))
    return dict(
        id="pinklady_sprite", cat="sprites", status="active", fmt="2D SHADER",
        badge="16-ANGLE + 36f BOUNCE",
        title="Hot-Pink Lady 16-Angle Turnaround & Bounce Sprite",
        file="progs/pinklady.md3 + scripts/pinklady.shader",
        script="source/mm_tools/build_pinklady_assets.py",
        desc="In-game billboard card featuring both the 16-angle 360° turnaround skins and the ping-pong front bounce animation!",
        nf=len(bounce_pingpong), nv=4, nt=2,
        bbox=[[-hw, -hw, 0.0], [hw, hw, hh]],
        isSprite=True, turnDirs=16, turnSign=-1,
        surfaces=[s_enc],
        clips=[
            dict(id="bounce", label="💖 Front Bounce Ping-Pong (34f)", start=0, count=len(bounce_pingpong), fps=4.0,
                 sprMode=dict(base=16, dirs=1, fpd=len(bounce_pingpong), fps=4.0)),
            dict(id="turn16", label="🔄 360° Turnaround (16 Angles)", start=0, count=1, fps=10.0,
                 sprMode=dict(base=0, dirs=16, fpd=1, fps=10.0)),
        ],
    )


def main():
    print("1. Initializing ArenaPacker & voice soundboard...", flush=True)
    sounds = pack_voice_soundboard()
    packer = ArenaPacker()
    models_out = []

    # Pre-pack shared high-res sRGB studio textures so multiple models share 1 upload
    t_jw_scream = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_scream_srgb.png"), max_dim=1024, quality=88)
    t_jw_calm   = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_calm_srgb.png"), max_dim=768, quality=88)
    t_jw_fed    = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_fedora_srgb.png"), max_dim=512, quality=88)
    t_jw_wave   = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_wave_srgb.png"), max_dim=256, quality=88)
    t_jw_fx     = packer.add_tex_file(os.path.join(HERE, "out", "jw_air", "jw_fx_srgb.png"), max_dim=256, force_png=True)

    t_bigears   = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "bigears_srgb.png"), max_dim=1024, quality=88)
    t_pinklady  = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "pinklady3d_srgb.png"), max_dim=1024, quality=88)
    t_sky_fx    = packer.add_tex_file(os.path.join(HERE, "out", "skyveh", "skyveh_fx_srgb.png"), max_dim=256, force_png=True)

    t_mm_chr    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_chrome_axle.png"), max_dim=512, quality=88)
    t_mm_whl    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png"), max_dim=512, quality=88)
    t_mm_gun    = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_gun_metal.png"), max_dim=768, quality=86)
    t_mm_gauge  = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_gauge_glow.png"), max_dim=256, quality=88)
    t_mm_hand   = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_hand.png"), max_dim=512, quality=86)
    t_mm_fx     = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_fx.png"), max_dim=256, force_png=True)
    t_mm_scan   = packer.add_tex_file(os.path.join(PROGS, "megaman.png"), max_dim=768, quality=86, lift=1.60)

    # ==================== CATEGORY 1: CUSTOM GUNS, VIEWMODELS & PICKUPS ====================
    print("2. Packing Category 1: All Custom Guns, Viewmodels & Weapon Pickups...", flush=True)
    mmw_mats = {
        "progs/mmw_gun_metal":   dict(tex=t_mm_gun,   metallic=0.65, roughness=0.28, spec=0.78),
        "progs/mmw_chrome_axle": dict(tex=t_mm_chr,   metallic=0.88, roughness=0.17, spec=0.95),
        "progs/mmw_wheel":       dict(tex=t_mm_whl,   metallic=0.16, roughness=0.52, spec=0.42),
        "progs/mmw_gauge_glow":  dict(tex=t_mm_gauge, unlit=True),
        "progs/mmw_hand":        dict(tex=t_mm_hand,  metallic=0.05, roughness=0.65, spec=0.22),
        "progs/mmw_fx":          dict(tex=t_mm_fx,    unlit=True, additive=True),
    }
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_megaman.md3"),
        dict(
            id="v_megaman", cat="guns", status="active", badge="MEGA-SLINGER · 37f",
            title="Mega-Slinger Launcher (First-Person Viewmodel)",
            file="progs/v_megaman.md3", script="source/mm_tools/build_megaman_weapon.py",
            desc="37-frame heavy launcher cradle holding the lathed Mega-Man chrome bar & spinning white-dish pneumatic tires with glowing PSI gauge and Ranger hands!",
            pov=True, az=2.45, el=0.22,
            clips=[
                dict(id="all", label="🎬 Full 37f Sequence", start=0, count=37, fps=14.0),
                dict(id="idle", label="⚙ Idle Wheel Spin (8f)", start=0, count=8, fps=10.0),
                dict(id="fire", label="💥 Launch & Reload (29f)", start=8, count=29, fps=16.0),
            ],
        ),
        surf_mats=mmw_mats, allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "megaman_weapon", "v_megaman_hand.md3"),
        dict(
            id="v_megaman_hand", cat="guns", status="vault", badge="GAUNTLET HURL · 32f",
            title="Ranger Gauntlet Hurling Mega-Man (Viewmodel)",
            file="source/mm_tools/out/megaman_weapon/v_megaman_hand.md3",
            script="source/mm_tools/build_megaman_weapon.py",
            desc="32-frame bare-handed Ranger gauntlet gripping and hurling the Mega-Man bar with additive throw-wake trails.",
            pov=True, az=2.45, el=0.22,
            clips=[
                dict(id="all", label="🎬 All 32f", start=0, count=32, fps=14.0),
                dict(id="idle", label="⚙ Idle Spin (8f)", start=0, count=8, fps=10.0),
                dict(id="throw", label="🤾 Hurl & Pop-In (24f)", start=8, count=24, fps=16.0),
            ],
        ),
        surf_mats=mmw_mats, allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "progs", "v_megaman.md3"),
        dict(
            id="v_megaman_classic", cat="guns", status="vault", badge="CLASSIC FIST · 26f",
            title="Classic Blue-Gloved Mega-Man Fist (v1 Viewmodel)",
            file="source/mm_tools/out/progs/v_megaman.md3",
            script="source/mm_tools/build_viewmodel.py",
            desc="Original 26-frame procedural blue gloved fist with multi-knuckle articulated fingers gripping the scanned Mega-Man pipe.",
            pov=True, az=2.55, el=0.22,
            clips=[
                dict(id="idle", label="⚙ Idle Bob (16f)", start=0, count=16, fps=10.0),
                dict(id="throw", label="🤾 Throw & Reload (10f)", start=16, count=10, fps=12.0),
                dict(id="all", label="🎬 All 26f", start=0, count=26, fps=12.0),
            ],
        ),
        surf_mats={"progs/megaman": dict(tex=t_mm_scan, metallic=0.25, roughness=0.48, spec=0.45)},
        allow_rigid=False,
    ))

    # 3D AOL Dial-Up Hacker Laptop Gun
    t_lp_body = packer.add_tex_file(os.path.join(PROGS, "v_laptop_body.png"), max_dim=512, lift=1.55)
    t_lp_keys = packer.add_tex_file(os.path.join(PROGS, "v_laptop_keys.png"), max_dim=512, lift=1.45)
    t_lp_scr  = packer.add_tex_file(os.path.join(PROGS, "v_laptop_scr.png"), max_dim=768, lift=1.18)
    t_lp_hand = packer.add_tex_file(os.path.join(PROGS, "v_laptop_hand.png"), max_dim=512, lift=1.35)
    t_lp_zap  = packer.add_tex_file(os.path.join(PROGS, "v_laptop_zap.png"), max_dim=256, force_png=True)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_laptop.md3"),
        dict(
            id="v_laptop", cat="guns", status="active", badge="AOL HACKER · 34f",
            title="AOL Dial-Up 3D Hacker Laptop Gun (Viewmodel)",
            file="progs/v_laptop.md3", script="source/mm_tools/build_laptop_gun.py",
            desc="34-frame 3D laptop displaying 'Hacking internet lag' + AOL 5.0 Dial-Up; firing whips in the left hand hammering 3D keys & arcing lightning!",
            pov=True, az=2.78, el=0.22,
            clips=[
                dict(id="all", label="⚡ Idle + Fast Type & Zap (34f)", start=0, count=34, fps=13.0),
                dict(id="idle", label="💻 One-Hand Hold (12f)", start=0, count=12, fps=10.0),
                dict(id="shoot", label="⚡ Rapid Typing & Bolts (22f)", start=12, count=22, fps=16.0),
            ],
        ),
        surf_mats={
            "progs/v_laptop_body": dict(tex=t_lp_body, metallic=0.35, roughness=0.45, spec=0.48),
            "progs/v_laptop_keys": dict(tex=t_lp_keys, metallic=0.15, roughness=0.55, spec=0.35),
            "progs/v_laptop_scr":  dict(tex=t_lp_scr,  unlit=True),
            "progs/v_laptop_hand": dict(tex=t_lp_hand, metallic=0.05, roughness=0.68, spec=0.22),
            "progs/v_laptop_zap":  dict(tex=t_lp_zap,  unlit=True, additive=True),
        },
        allow_rigid=False, bbox_frames=list(range(0, 12)),
    ))

    # Video-Shader Laptop Gun (ltg_view.md3: Idle + Rapid Typing skins)
    ltg_idle_seq = [os.path.join(PROGS, f"ltg_i_{k:02d}.png") for k in range(0, 44, 2)]
    ltg_idle_pp = ltg_idle_seq + ltg_idle_seq[-2:0:-1]
    tid_ltg_idle, ord_ltg_idle = build_anim_atlas_from_files(packer, "ltg_idle_video", ltg_idle_pp, max_tile_dim=240)
    ltg_type_seq = [os.path.join(PROGS, f"ltg_t_{k:02d}.png") for k in range(0, 48, 2)]
    tid_ltg_type, ord_ltg_type = build_anim_atlas_from_files(packer, "ltg_type_video", ltg_type_seq, max_tile_dim=240)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "ltg_view.md3"),
        dict(
            id="ltg_view", cat="guns", status="active", fmt="2D SHADER", badge="VIDEO WEAPON · 2 SKINS",
            title="Laptop Gun Video-Shader Viewmodel (Idle & 42fps Typing)",
            file="progs/ltg_view.md3 + scripts/ltgun.shader",
            script="source/mm_tools/build_ltgun_assets.py",
            desc="First-person keyed-video Laptop Gun card with 2 switchable shader skins: Idle Sway ping-pong and manic 42fps Rapid Typing!",
            pov=True, defaultPov=True, az=3.14, el=0.06,
            skins=[
                dict(label="💻 Idle Sway (Ping-Pong)", map={"card": dict(tex=tid_ltg_idle, animFps=4.0, animOrder=ord_ltg_idle)}),
                dict(label="⚡ Rapid Typing (42fps)", map={"card": dict(tex=tid_ltg_type, animFps=21.0, animOrder=ord_ltg_type)}),
            ],
        ),
        surf_mats={"progs/ltg_idle": dict(tex=tid_ltg_idle, animFps=4.0, animOrder=ord_ltg_idle, unlit=True, alphaTest=True)},
    ))

    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "ltg_p.md3"),
        dict(
            id="ltg_p", cat="guns", status="active", badge="3RD-PERSON · 259f",
            title="Laptop Gun (3rd-Person 259-Pose Player Rig)",
            file="progs/ltg_p.md3", script="source/mm_tools/build_ltgun_assets.py",
            desc="Exterior open laptop model rigidly fitted across all 259 Quake 1.5 multiplayer player weapon frames.",
        ),
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "ltg_g.md3"),
        dict(
            id="ltg_g", cat="guns", status="active", badge="PICKUP · MD3",
            title="Laptop Gun (Spinning Floor Pickup)",
            file="progs/ltg_g.md3", script="source/mm_tools/build_ltgun_assets.py",
            desc="World floor pickup mesh for the Laptop Gun.",
        ),
    ))

    # NetSend LOL.BAT Floppy Gun
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_netsend.md3"),
        dict(
            id="v_netsend", cat="guns", status="active", badge="FLOPPY LAUNCHER · 60f",
            title='NetSend "LOL.BAT" 3.5" Floppy Disk Gun (Viewmodel)',
            file="progs/v_netsend.md3", script="source/mm_tools/build_netsend_assets.py",
            desc="60-frame articulated hand dealing & flicking 3.5-inch 'LOL.BAT' floppy diskettes that deploy retro NetSend CRT towers!",
            pov=True, az=2.55, el=0.22,
            clips=[
                dict(id="all", label="🎬 Full 60f Sequence", start=0, count=60, fps=15.0),
                dict(id="idle", label="💾 Idle Disk Fan (20f)", start=0, count=20, fps=12.0),
                dict(id="fire", label="🤾 Flick Floppy Disk (40f)", start=20, count=40, fps=18.0),
            ],
        ),
        allow_rigid=False, lift_default=1.35,
    ))

    # Goo Gun (Viewmodel + 3rd-Person)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_googun.md3"),
        dict(
            id="v_googun", cat="guns", status="active", badge="BIO-FOAM · 7f",
            title="Bio-Foam Goo Gun (First-Person Viewmodel)",
            file="progs/v_googun.md3", script="source/mm_tools/build_googun.py",
            desc="8-surface procedural pressurized bio-foam sprayer with glowing side tank, hazard decals & 7-frame recoil kick.",
            pov=True, az=2.45, el=0.22,
            clips=[
                dict(id="all", label="🧪 Fire Recoil (7f)", start=0, count=7, fps=12.0),
                dict(id="idle", label="🗿 Idle Frame 0", start=0, count=1, fps=10.0, lie=True),
            ],
        ),
        allow_rigid=False, lift_default=1.40,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "p_googun.md3"),
        dict(
            id="p_googun", cat="guns", status="active", badge="3RD-PERSON · 259f",
            title="Bio-Foam Goo Gun (3rd-Person 259-Pose Rig)",
            file="progs/p_googun.md3", script="source/mm_tools/build_googun.py",
            desc="Exterior Goo Gun rigidly fitted across all 259 multiplayer player poses.",
        ),
        lift_default=1.40,
    ))

    # Bonk Hammer (v_hammer.mdl, 255 frames)
    models_out.append(pack_mdl_asset(
        packer, os.path.join(PROGS, "v_hammer.mdl"),
        dict(
            id="v_hammer", cat="guns", status="active", badge="BONK HAMMER · 255f",
            title="Tiered Charge Bonk Hammer (255-Frame Viewmodel)",
            file="progs/v_hammer.mdl", script="source/mm_tools/hammer.qc",
            desc="255-frame heavy two-handed warhammer featuring Low/Med/High charge tiers, air-dash lunge, pogo hop, whiff & flourish spins!",
            pov=True, az=2.55, el=0.22,
            clips=[
                dict(id="idle", label="🔨 Idle Sway (40f)", start=0, count=40, fps=14.0),
                dict(id="hi_hit", label="💥 High Tier Smash (19f)", start=40, count=19, fps=18.0),
                dict(id="dash", label="🚀 Air-Dash & Hop (18f)", start=59, count=18, fps=16.0),
                dict(id="med_hit", label="⚡ Med Tier Swing (19f)", start=77, count=19, fps=18.0),
                dict(id="lo_hit", label="🔨 Low Tier Swing (19f)", start=114, count=19, fps=18.0),
                dict(id="whiff", label="💨 Whiff Recovery (27f)", start=159, count=27, fps=16.0),
                dict(id="spin", label="🌀 Flourish Inspect (69f)", start=186, count=69, fps=20.0),
                dict(id="all", label="🎬 All 255f", start=0, count=255, fps=18.0),
            ],
        ),
    ))

    # Sniper Rifle Trio (v_srifle.mdl, g_srifle.mdl, p_srifle.md3)
    models_out.append(pack_mdl_asset(
        packer, os.path.join(PROGS, "v_srifle.mdl"),
        dict(
            id="v_srifle", cat="guns", status="active", badge="SNIPER · 7f MDL",
            title="Sniper Rifle (First-Person Viewmodel)",
            file="progs/v_srifle.mdl", script="source/mm_tools/sniper.qc",
            desc="7-frame scoped sniper rifle first-person viewmodel with laser-sight zoom & recoil.",
            pov=True, az=2.45, el=0.20,
        ),
    ))
    models_out.append(pack_mdl_asset(
        packer, os.path.join(PROGS, "g_srifle.mdl"),
        dict(
            id="g_srifle", cat="guns", status="active", badge="PICKUP · MDL",
            title="Hand-Stripped Sniper Rifle (Floor Pickup)",
            file="progs/g_srifle.mdl", script="source/mm_tools/build_srifle.py",
            desc="Sniper rifle pickup with the player's hand cleanly excised via connected-component UV palette voting.",
        ),
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "p_srifle.md3"),
        dict(
            id="p_srifle", cat="guns", status="active", badge="3RD-PERSON · 259f",
            title="Sniper Rifle (3rd-Person 259-Pose Rig)",
            file="progs/p_srifle.md3", script="source/mm_tools/build_srifle.py",
            desc="Hand-stripped Sniper Rifle converted to MD3 and rigidly fitted to all 259 player poses.",
        ),
    ))

    # Held Rob Dob Head Viewmodel
    models_out.append(pack_mdl_asset(
        packer, os.path.join(PROGS, "v_robdob.mdl"),
        dict(
            id="v_robdob", cat="guns", status="active", badge="ROB TRAP VM · 9f",
            title="Held Rob Dob Head Trap (Viewmodel)",
            file="progs/v_robdob.mdl", script="source/mm_tools/build_floathead.py",
            desc="First-person held miniature Rob Dob head hovering in the lower-right corner and glancing back at you!",
            pov=True, az=2.82, el=0.18,
            clips=[
                dict(id="bob", label="👀 Idle Bob (8f)", start=0, count=8, fps=10.0),
                dict(id="all", label="🎬 All 9f (incl. Gone)", start=0, count=9, fps=10.0),
            ],
        ),
    ))

    # Fun-Gun Melee / Throw Viewmodels & World Models (Sledge, Paddle, Hackmon, Spanner)
    vm22_clips = [
        dict(id="idle", label="🌊 Idle Sway (16f)", start=0, count=16, fps=10.0),
        dict(id="fire", label="💥 Swing / Throw & Raise (6f)", start=16, count=6, fps=12.0),
        dict(id="all", label="🎬 All 22f", start=0, count=22, fps=12.0),
    ]
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_sledge.md3"),
        dict(
            id="v_sledge", cat="guns", status="active", badge="WHACK-A-MOLE · 22f",
            title="Whack-a-Mole Sledgehammer (Viewmodel)",
            file="progs/v_sledge.md3", script="source/mm_tools/build_fungun_viewmodels.py",
            desc="First-person sledgehammer that bonks enemies down to 45% miniature size!",
            pov=True, az=2.50, el=0.20, clips=vm22_clips,
        ),
        allow_rigid=False, lift_default=1.45,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "sledge.md3"),
        dict(
            id="sledge", cat="guns", status="active", badge="WORLD WEAPON · MD3",
            title="Whack-a-Mole Sledgehammer (World Mesh)",
            file="progs/sledge.md3", desc="4-surface rubber/steel sledgehammer world pickup & prop mesh.",
        ),
        lift_default=1.45,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_paddle.md3"),
        dict(
            id="v_paddle", cat="guns", status="active", badge="RALLY MASTER · 22f",
            title="Rally Master Ping-Pong Paddle (Viewmodel)",
            file="progs/v_paddle.md3", script="source/mm_tools/build_fungun_viewmodels.py",
            desc="22-frame table-tennis paddle viewmodel serving high-velocity ricochet ping-pong balls!",
            pov=True, az=2.60, el=0.20, clips=vm22_clips,
        ),
        allow_rigid=False, lift_default=1.35,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "paddle.md3"),
        dict(
            id="paddle", cat="guns", status="active", badge="WORLD WEAPON · MD3",
            title="Rally Master Ping-Pong Paddle (World Mesh)",
            file="progs/paddle.md3", desc="3,000-triangle wood & rubber table-tennis paddle world mesh.",
        ),
        lift_default=1.35,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_hackmon.md3"),
        dict(
            id="v_hackmon", cat="guns", status="active", badge='"> HACKING" · 22f',
            title='Hack Attack "> HACKING" CRT Monitor (Viewmodel)',
            file="progs/v_hackmon.md3", script="source/mm_tools/build_hackmon_models.py",
            desc="19-surface CRT monitor held screen-toward-player with a custom green phosphor '> HACKING' scanline terminal.",
            pov=True, az=2.85, el=0.16, clips=vm22_clips,
        ),
        allow_rigid=False, lift_default=1.35,
    ))
    models_out.append(pack_mdl_asset(
        packer, os.path.join(PROGS, "v_span.mdl"),
        dict(
            id="v_span", cat="guns", status="active", badge="ENGINEER · 5f MDL",
            title="Engineer Sentry Spanner Wrench (Viewmodel)",
            file="progs/v_span.mdl", script="source/mm_tools/build_sentry.py",
            desc="5-frame heavy steel spanner wrench viewmodel used to construct, repair & upgrade Sentry Guns.",
            pov=True, az=2.50, el=0.22,
        ),
    ))

    # Milky Viewmodel (v_milky.md3, 3 skins: Idle A, Idle B, Throw)
    mvm_a_seq = [os.path.join(PROGS, f"mvm_a_{k:02d}.png") for k in range(0, 39, 2)]
    mvm_a_pp = mvm_a_seq + mvm_a_seq[-2:0:-1]
    tid_mvm_a, ord_mvm_a = build_anim_atlas_from_files(packer, "milky_idle_a", mvm_a_pp, max_tile_dim=232)
    mvm_b_seq = [os.path.join(PROGS, f"mvm_b_{k:02d}.png") for k in range(0, 48, 2)]
    mvm_b_pp = mvm_b_seq + mvm_b_seq[-2:0:-1]
    tid_mvm_b, ord_mvm_b = build_anim_atlas_from_files(packer, "milky_idle_b", mvm_b_pp, max_tile_dim=232)
    mvm_f_seq = [os.path.join(PROGS, f"mvm_f_{k:02d}.png") for k in range(29)]
    tid_mvm_f, ord_mvm_f = build_anim_atlas_from_files(packer, "milky_throw_f", mvm_f_seq, max_tile_dim=232)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_milky.md3"),
        dict(
            id="v_milky", cat="guns", status="active", fmt="2D SHADER", badge="MILKY JUG · 3 SKINS",
            title="Milky Jug Launcher Viewmodel (Idle A, Idle B & Throw)",
            file="progs/v_milky.md3 + scripts/milkyvm.shader",
            script="source/mm_tools/build_milky_view.py",
            desc="First-person milk-jug weapon card packing all 3 video-shader skins: Idle Sway A, Idle Sway B, and 18fps Milk Jug Hurl!",
            pov=True, defaultPov=True, az=3.14, el=0.06,
            skins=[
                dict(label="🥛 Idle Sway A", map={"card": dict(tex=tid_mvm_a, animFps=4.0, animOrder=ord_mvm_a)}),
                dict(label="🥛 Idle Sway B", map={"card": dict(tex=tid_mvm_b, animFps=4.0, animOrder=ord_mvm_b)}),
                dict(label="💥 Hurl Milk Jug (18fps)", map={"card": dict(tex=tid_mvm_f, animFps=18.0, animOrder=ord_mvm_f)}),
            ],
        ),
        surf_mats={"progs/mvm_a": dict(tex=tid_mvm_a, animFps=4.0, animOrder=ord_mvm_a, unlit=True, alphaTest=True)},
    ))

    # Held Pickle Surprise Viewmodel (v_pickle.md3)
    vpk_seq = [os.path.join(PROGS, f"vpk_{k:02d}.png") for k in range(0, 48, 2)]
    vpk_pp = vpk_seq + vpk_seq[-2:0:-1]
    tid_vpk, ord_vpk = build_anim_atlas_from_files(packer, "v_pickle_fist", vpk_pp, max_tile_dim=232)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "v_pickle.md3"),
        dict(
            id="v_pickle", cat="guns", status="active", fmt="2D SHADER", badge="PICKLE FIST · SHADER",
            title="Held Pickle Surprise Fist (First-Person Viewmodel)",
            file="progs/v_pickle.md3 + scripts/pickle.shader",
            script="source/mm_tools/build_pickle_assets.py",
            desc="Keyed-video armored fist clutching the Pickle Surprise bomb in eye space (ping-pong animmap).",
            pov=True, defaultPov=True, az=3.14, el=0.05,
        ),
        surf_mats={"progs/pickle_hand": dict(tex=tid_vpk, animFps=4.0, animOrder=ord_vpk, unlit=True, alphaTest=True)},
    ))

    # John Wave Hand Sprite (fr_johnhand.spr32)
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "fr_johnhand.spr32"),
        dict(
            id="fr_johnhand", cat="guns", status="active", badge="JOHN WAVE · 49f SPR32",
            title="John Wave Casting Hand (49-Frame Viewmodel Sprite)",
            file="progs/fr_johnhand.spr32", script="source/mm_tools/build_john_assets.py",
            desc="49-frame 32-bit RGBA sprite viewmodel for the John Wave tidal-wave weapon—inspect in 1st-Person POV, 3D Card, or 2D Pixel View!",
            pov=True, defaultPov=True, az=3.14, el=0.05,
        ),
        mode="pov_hand", max_tile_dim=224,
    ))

    # Vault Guns: Pocket Rocket, Girlfriend Gun, Banana Gun, Rob Rocket
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "pocket_rocket", "md3", "v_pocket_rocket.md3"),
        dict(
            id="v_pocket_rocket", cat="guns", status="vault", badge="POCKET ROCKET · VAULT",
            title="Pocket Rocket Giant-Hand Launcher (Viewmodel)",
            file="source/mm_tools/out/pocket_rocket/md3/v_pocket_rocket.md3",
            desc="6-surface miniature character held in a giant first-person hand with idle, wave & hurl animations (GPU-interpolated keyframes).",
            pov=True, az=2.65, el=0.20,
            clips=[
                dict(id="all", label="🎬 Idle, Wave & Throw (18kf)", start=0, count=18, fps=6.5),
                dict(id="idle", label="👋 Idle & Wave (12kf)", start=0, count=12, fps=6.0),
                dict(id="throw", label="🚀 Launch Throw (6kf)", start=12, count=6, fps=7.5),
            ],
        ),
        allow_rigid=False, frame_stride=2,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "girl_assets", "progs", "v_banana_girl.md3"),
        dict(
            id="v_banana_girl", cat="guns", status="vault", badge="GIRLFRIEND GUN · VAULT",
            title="Held Miniature Girlfriend Gun (Viewmodel)",
            file="source/mm_tools/out/removed_guns_src/girl_assets/progs/v_banana_girl.md3",
            script="source/mm_tools/girl_pipeline/girl_md3.py",
            desc="16-frame miniature 3D human figure held in the player's hand with idle sway (0–7) and toss (8–15).",
            pov=True, az=2.75, el=0.18,
            clips=[
                dict(id="idle", label="🌊 Idle Sway (8f)", start=0, count=8, fps=10.0),
                dict(id="throw", label="🤾 Toss Forward (8f)", start=8, count=8, fps=12.0),
                dict(id="all", label="🎬 All 16f", start=0, count=16, fps=11.0),
            ],
        ),
        allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "banana_assets", "progs", "v_banana.md3"),
        dict(
            id="v_banana", cat="guns", status="vault", badge="BANANA BAZOOKA · VAULT",
            title="Procedural Yellow Banana Tube Bazooka (Viewmodel)",
            file="source/mm_tools/out/removed_guns_src/banana_assets/progs/v_banana.md3",
            script="source/mm_tools/build_banana_assets.py",
            desc="16-frame procedural yellow cylindrical bazooka tube with bobbing idle & recoil kick.",
            pov=True, az=2.40, el=0.22,
            clips=[
                dict(id="idle", label="🍌 Idle Sway (8f)", start=0, count=8, fps=10.0),
                dict(id="fire", label="💥 Recoil Kick (8f)", start=8, count=8, fps=14.0),
                dict(id="all", label="🎬 All 16f", start=0, count=16, fps=12.0),
            ],
        ),
        allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "fungun", "progs", "v_robrocket.md3"),
        dict(
            id="v_robrocket", cat="guns", status="vault", badge="ROB ROCKET · VAULT",
            title="Rob Rocket Bazooka Prototype (Viewmodel)",
            file="source/mm_tools/out/fungun/progs/v_robrocket.md3",
            script="source/mm_tools/build_fungun_viewmodels.py",
            desc="Archived 22-frame fun-gun rocket launcher viewmodel prototype.",
            pov=True, az=2.45, el=0.20, clips=vm22_clips,
        ),
        allow_rigid=False,
    ))

    # ==================== CATEGORY 2: CUSTOM 3D CHARACTERS, HEADS, RIDERS & SENTRIES ====================
    print("3. Packing Category 2: All Custom 3D Characters, Heads, Riders & Sentries...", flush=True)
    rider_clips = [
        dict(id="drive", label="🛞 Drive Roll (16f)", start=12, count=16, fps=14.0),
        dict(id="idle", label="🧍 Idle Balance (12f)", start=0, count=12, fps=10.0),
        dict(id="boost", label="🚀 Projectile Boost (12f)", start=28, count=12, fps=16.0),
        dict(id="charge", label="😤 Monster Charge (12f)", start=40, count=12, fps=15.0),
        dict(id="slam", label="💥 Wheelie Slam (8f)", start=52, count=8, fps=14.0),
        dict(id="all", label="🎬 All 60f", start=0, count=60, fps=14.0),
    ]
    t_suit_h  = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_suit_human_srgb.png"), max_dim=1024, quality=88)
    t_suit_r  = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_suit_rig_srgb.png"), max_dim=768, quality=88)
    t_squat_h = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_squat_human_srgb.png"), max_dim=1024, quality=88)
    t_squat_g = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_squat_human_grin_srgb.png"), max_dim=1024, quality=88)
    t_squat_r = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_squat_rig_srgb.png"), max_dim=768, quality=88)
    t_rid_fx  = packer.add_tex_file(os.path.join(HERE, "out", "mm_riders", "mm_rider_fx_srgb.png"), max_dim=256, force_png=True)

    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_suit_rider.md3"),
        dict(
            id="mm_suit_rider", cat="chars", status="active", badge="MEGA-MAN RIDER · 60f",
            title="Suit Guy Riding Mega-Man Contraption",
            file="progs/mm_suit_rider.md3", script="source/mm_tools/build_mm_riders.py",
            desc="60-frame articulated Suit Guy balanced atop a twin-wheel Mega-Man Segway rig with drive, boost, monster charge & wheelie-slam animations!",
            clips=rider_clips,
        ),
        surf_mats={
            "progs/mm_suit_human": dict(tex=t_suit_h, metallic=0.06, roughness=0.58, spec=0.28),
            "progs/mm_suit_rig":   dict(tex=t_suit_r, metallic=0.55, roughness=0.28, spec=0.72),
            "progs/mm_rider_fx":   dict(tex=t_rid_fx, unlit=True, additive=True),
        },
        allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_squat_rider.md3"),
        dict(
            id="mm_squat_rider", cat="chars", status="active", badge="MEGA-MAN RIDER · 2 SKINS",
            title="Squat Rider on Mega-Man Rig (Neutral & Grin Skins)",
            file="progs/mm_squat_rider.md3", script="source/mm_tools/build_mm_riders.py",
            desc="60-frame low-slung Squat Rider gripping the Mega-Man axle with 2 switchable facial skins (Focused Neutral & Manic Grin)!",
            clips=rider_clips,
            skins=[
                dict(label="😐 Neutral Face", map={"rider_human": dict(tex=t_squat_h)}),
                dict(label="😁 Grinning Face", map={"rider_human": dict(tex=t_squat_g)}),
            ],
        ),
        surf_mats={
            "progs/mm_squat_human": dict(tex=t_squat_h, metallic=0.06, roughness=0.58, spec=0.28),
            "progs/mm_squat_rig":   dict(tex=t_squat_r, metallic=0.55, roughness=0.28, spec=0.72),
            "progs/mm_rider_fx":    dict(tex=t_rid_fx,  unlit=True, additive=True),
        },
        allow_rigid=False,
    ))

    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "bigears.md3"),
        dict(
            id="bigears", cat="chars", status="active", badge="3D HEAD · BIG EARS",
            title="Giant-Eared Screaming 3D Floating Head",
            file="progs/bigears.md3", script="source/mm_tools/build_bigears_head.py",
            desc="Watertight 4,562-vertex / 5,600-triangle 3D head carved from 48 turntable views with sculpted giant cupped ears!",
            az=-0.34, el=0.10,
        ),
        surf_mats={"progs/bigears": dict(tex=t_bigears, metallic=0.05, roughness=0.60, spec=0.26)},
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "johnhead3d.md3"),
        dict(
            id="johnhead3d", cat="chars", status="active", badge="3D HEAD · SCREAMING JOHN",
            title="John Wave Screaming Flying 3D Head",
            file="progs/johnhead3d.md3", script="source/mm_tools/build_john_head3d.py",
            desc="4,837-vertex 3D visual-hull head carved in Blender from 113 green-screen turntable frames—fired by JohnWave & Aircraft!",
            az=-0.28, el=0.14,
        ),
        surf_mats={"progs/johnhead3d": dict(tex=t_jw_scream, metallic=0.05, roughness=0.60, spec=0.28)},
    ))
    models_out.append(build_calm_john_asset(packer, t_jw_calm))

    models_out.append(pack_mdl_asset(
        packer, os.path.join(PROGS, "grenade.mdl"),
        dict(
            id="grenade", cat="chars", status="active", badge="3D HEAD GRENADE",
            title="John Wave 3D Head Grenade (Replaces Pineapple)",
            file="progs/grenade.mdl + grenade.mdl_0.tga", script="source/mm_tools/build_head_grenade.py",
            desc="Custom 32×32 ring-mesh 3D John head with high-res TGA portrait wrap replacing Quake's stock grenade projectile.",
            az=-0.28, el=0.16,
        ),
    ))
    models_out.append(pack_mdl_asset(
        packer, os.path.join(PROGS, "floathead.mdl"),
        dict(
            id="floathead", cat="chars", status="active", badge="MONSTER · 2 SKINS · 20f",
            title="Rob Dob Floating Head Monster (v2 Turnaround)",
            file="progs/floathead.mdl", script="source/mm_tools/build_floathead.py",
            desc="20-frame hovering Rob Dob monster reconstructed from 6 turnaround angles with articulated jaw drop & automatic screaming mouth skin!",
            az=-0.28, el=0.14, frameSkin=8,
        ),
        skin_labels=["🙂 Closed Mouth (Idle)", "😱 Screaming Open Jaw"],
    ))
    models_out.append(pack_mdl_asset(
        packer, os.path.join(HERE, "preview", "floathead", "floathead.mdl"),
        dict(
            id="floathead_v1", cat="chars", status="vault", badge="PROTOTYPE v1 · 20f",
            title="Rob Dob Floating Head (v1 Single-Photo Prototype)",
            file="source/mm_tools/preview/floathead/floathead.mdl",
            script="source/mm_tools/build_floathead_photo.py",
            desc="Earlier single-photograph 3D Rob Dob head prototype with 20 idle/rush/pain frames and dual mouth skins.",
            az=-0.28, el=0.14, frameSkin=8,
        ),
        skin_labels=["🙂 Closed Mouth", "😱 Screaming Jaw"],
    ))

    models_out.append(build_pinklady3d_asset(packer, t_pinklady))

    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "pocket_rocket", "md3", "pocket_rocket_char.md3"),
        dict(
            id="pocket_rocket_char", cat="chars", status="vault", badge="3D CHARACTER · VAULT",
            title="Pocket Rocket Full-Body 3D Character",
            file="source/mm_tools/out/pocket_rocket/md3/pocket_rocket_char.md3",
            desc="23,159-vertex full-body character in pink crop-top, jeans & sneakers with animated pose sequence.",
            clips=[dict(id="all", label="🎬 Character Sequence (16kf)", start=0, count=16, fps=6.0)],
        ),
        allow_rigid=False, frame_stride=2,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "girl_assets", "progs", "girl.md3"),
        dict(
            id="girl", cat="chars", status="vault", badge="26K-TRI HULL · 8f",
            title="Girlfriend Chaser (26,000-Triangle 3D Video Hull)",
            file="source/mm_tools/out/removed_guns_src/girl_assets/progs/girl.md3",
            script="source/mm_tools/girl_pipeline/girl_md3.py",
            desc="Full-body 3D human reconstructed from video across 5 MD3 surfaces with an 8-frame running lean/bob cycle.",
            az=-0.28, el=0.18,
            clips=[dict(id="run", label="🏃 Run Cycle (8f)", start=0, count=8, fps=10.0)],
        ),
        allow_rigid=False,
    ))

    player143_clips = [
        dict(id="stand", label="🧍 Stand (5f)", start=12, count=5, fps=9.0),
        dict(id="run", label="🏃 Rocket Run (6f)", start=6, count=6, fps=11.0),
        dict(id="axrun", label="🪓 Axe Run (6f)", start=0, count=6, fps=11.0),
        dict(id="shot", label="🔫 Shoot (6f)", start=113, count=6, fps=11.0),
        dict(id="axe", label="🪓 Axe Swing (6f)", start=119, count=6, fps=11.0),
        dict(id="pain", label="💢 Pain (6f)", start=29, count=6, fps=10.0),
        dict(id="death", label="💀 Death A (11f)", start=50, count=11, fps=10.0),
        dict(id="all", label="🎬 All 143f", start=0, count=143, fps=11.0),
    ]
    for cid, title, fn, desc in [
        ("suitguy", "Suit Guy (143-Frame Custom Player Model)", "suitguy.mdl",
         "Full 143-frame Quake player model built from front & back studio photos in a dark business suit + high-color TGA skin."),
        ("robeguy", "Robe Guy (143-Frame Custom Player Model)", "robeguy.mdl",
         "Full 143-frame Quake player model built from front & back photos in a white bathrobe + high-color TGA skin."),
        ("wifeguy", "Wife (143-Frame Custom Player Model)", "wifeguy.mdl",
         "Full 143-frame Quake player model built from front & back photos + custom high-color TGA skin."),
    ]:
        models_out.append(pack_mdl_asset(
            packer, os.path.join(BKP_CHARS, fn),
            dict(
                id=cid, cat="chars", status="vault", badge="PLAYER MDL · 143f",
                title=title,
                file=f"_backups/player_bodies_removed_2026-10-30/progs/{fn}",
                script="source/mm_tools/build_char_models.py",
                desc=desc, az=-0.28, el=0.18, clips=player143_clips,
            ),
        ))

    models_out.append(build_pickle3d_asset(packer))
    models_out.append(build_sentry_assembly(packer))
    models_out.append(build_sentry_gibs(packer))

    # ==================== CATEGORY 3: CUSTOM 2D SPRITES & 360° TURNAROUNDS ====================
    print("4. Packing Category 3: All Custom 2D Sprites (.SPR32/.SPR) & 360° Turnarounds...", flush=True)
    models_out.append(build_jesskart_studio(packer))
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "jesskart.spr32"),
        dict(
            id="jesskart_spr32", cat="sprites", status="active", badge="8-DIR SPR32 · 56f",
            title="JessKart In-Game Chaser (.SPR32)",
            file="progs/jesskart.spr32", script="source/mm_tools/build_jesskart_sprite.py",
            desc="Active 56-frame 8-direction Quake SPR32 sprite (8 idle angles + 8×6 run frames)—orbit 360° or inspect in 2D Pixel View!",
        ),
    ))
    models_out.append(build_scissor_studio(packer))
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "fr_scissors.spr32"),
        dict(
            id="fr_scissors", cat="sprites", status="active", badge="8-DIR SPR32 · 56f",
            title="Giant Running Scissors In-Game (.SPR32)",
            file="progs/fr_scissors.spr32", script="source/mm_tools/build_scissor_sprite.py",
            desc="Active 56-frame 8-direction SPR32 sprite for the snipping Scissors hazard (8 idle + 8×6 run).",
        ),
    ))
    models_out.append(build_earhead_studio(packer))
    models_out.append(build_ltg_head_md3(packer))
    models_out.append(build_pinklady_sprite(packer))

    # Standing Pickle 16-View Turntable + 4 Scream Frames (pickle.md3)
    p_front_paths = [os.path.join(PROGS, f"pickle_{k:02d}.png") for k in (15, 0, 1, 2, 1, 0)]
    tid_pk_front, ord_pk_front = build_anim_atlas_from_files(packer, "pickle_front_6", p_front_paths, max_tile_dim=256)
    pk_mats = {"progs/pickle_front": dict(tex=tid_pk_front, animFps=5.0, animOrder=ord_pk_front, unlit=True, alphaTest=True)}
    for k in range(1, 16):
        tid_v = packer.add_tex_file(os.path.join(PROGS, f"pickle_{k:02d}.png"), max_dim=256)
        pk_mats[f"progs/pickle_v{k:02d}"] = dict(tex=tid_v, unlit=True, alphaTest=True)
    for sh_s, fn_s in [
        ("progs/pickle_scream_front", "pickle_scream_00.png"),
        ("progs/pickle_scream_v01", "pickle_scream_01.png"),
        ("progs/pickle_scream_v02", "pickle_scream_02.png"),
        ("progs/pickle_scream_v15", "pickle_scream_15.png"),
    ]:
        tid_s = packer.add_tex_file(os.path.join(PROGS, fn_s), max_dim=256)
        pk_mats[sh_s] = dict(tex=tid_s, unlit=True, alphaTest=True)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "pickle.md3"),
        dict(
            id="pickle_turntable", cat="sprites", status="active", badge="16-VIEW + SCREAM",
            title="Standing Pickle Surprise (16-Angle Turntable + Scream)",
            file="progs/pickle.md3 + scripts/pickle.shader",
            script="source/mm_tools/make_pickle_views.py",
            desc="Camera-reactive 16-angle turntable MD3 + 4 wide-mouthed pre-detonation scream frames—drag horizontally to orbit all 16 angles!",
            az=3.45, el=0.08, turnDirs=16, turnSign=-1,
            clips=[
                dict(id="turn", label="🥒 360° Turntable (16 Angles)", start=0, count=16, fps=8.0, turnaround=True, lie=True),
                dict(id="scream", label="😱 Pre-Blast Scream (4f)", start=16, count=4, fps=10.0, lie=True),
                dict(id="all", label="🎬 All 20 Frames", start=0, count=20, fps=8.0, lie=True),
            ],
        ),
        surf_mats=pk_mats, allow_rigid=False, bbox_frames=[0],
    ))

    # Rob Friend Chaser (Active) + John Flying Head Sprite (Vault) + 10 MegaKart Friends (Vault)
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "fr_rob.spr32"),
        dict(
            id="fr_rob", cat="sprites", status="active", badge="FRIEND SPR32 · 56f",
            title="Rob Chaser Companion (8-Dir × 6f .SPR32)",
            file="progs/fr_rob.spr32", script="source/mm_tools/build_friend_sprites.py",
            desc="Active 8-direction photo-cutout friend sprite (8 idle angles + 48 run frames) summoned in BakersfieldQuake!",
        ),
    ))
    models_out.append(pack_spr_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "john_assets", "progs", "fr_johnhead.spr32"),
        dict(
            id="fr_johnhead", cat="sprites", status="vault", badge="HEAD SPR32 · VAULT",
            title="John Flying Head Sprite (.SPR32 Prototype)",
            file="source/mm_tools/out/removed_guns_src/john_assets/progs/fr_johnhead.spr32",
            script="source/mm_tools/build_john_assets.py",
            desc="Archived multi-angle 32-bit RGBA sprite version of John's flying head (superseded by johnhead3d.md3).",
        ),
        mode="turn16",
    ))

    friend_names = [
        ("babydavid", "Baby David"), ("david", "David"), ("jeffery", "Jeffery"),
        ("jessa", "Jessa"), ("john", "John"), ("julian", "Julian"),
        ("larry", "Larry"), ("marc", "Marc"), ("mike", "Mike"), ("reese", "Reese"),
    ]
    for fn_key, nice_nm in friend_names:
        models_out.append(pack_spr_asset(
            packer, os.path.join(HERE, "out", "friends", "progs", f"fr_{fn_key}.spr32"),
            dict(
                id=f"fr_{fn_key}", cat="sprites", status="vault", badge="MEGAKART FRIEND · 56f",
                title=f"MegaKart Friend: {nice_nm} (8-Dir .SPR32)",
                file=f"source/mm_tools/out/friends/progs/fr_{fn_key}.spr32",
                script="source/mm_tools/build_friend_sprites.py",
                desc=f"56-frame 8-direction photo sprite for {nice_nm} (frames 0–7 directional idle, frames 8–55 8-way × 6-frame run cycle).",
            ),
        ))

    # FX & Reticle Sprites (jw_ripple.spr32, jw_splash.spr32, netsend_arc.spr, sight.spr)
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "jw_ripple.spr32"),
        dict(
            id="jw_ripple", cat="sprites", status="active", badge="FLOOR SPR32 · 10f",
            title="John Wave Expanding Floor Water Ripple (.SPR32)",
            file="progs/jw_ripple.spr32", script="source/mm_tools/build_john_assets.py",
            desc="10-frame oriented horizontal water shockwave sprite spawned flat along the floor by John Wave blasts.",
            el=0.62,
        ),
        mode="floor", scale_u=0.35,
    ))
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "jw_splash.spr32"),
        dict(
            id="jw_splash", cat="sprites", status="active", badge="SPLASH SPR32 · 8f",
            title="John Wave Foaming Water Splash (.SPR32)",
            file="progs/jw_splash.spr32", script="source/mm_tools/build_john_assets.py",
            desc="8-frame 32-bit RGBA foaming water burst sprite.",
        ),
        scale_u=0.45,
    ))
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "netsend_arc.spr"),
        dict(
            id="netsend_arc_spr", cat="sprites", status="active", badge="8-BIT SPR · 8f",
            title="NetSend Electric Spark Sprite (Classic Quake .SPR)",
            file="progs/netsend_arc.spr", script="source/mm_tools/build_netsend_assets.py",
            desc="8-frame classic Quake IDSP v1 8-bit paletted electric spark sprite.",
            additive=True,
        ),
        scale_u=0.65,
    ))
    models_out.append(pack_spr_asset(
        packer, os.path.join(PROGS, "sight.spr"),
        dict(
            id="sight_spr", cat="sprites", status="active", badge="RETICLE SPR · 1f",
            title="Sniper Rifle Laser-Sight Dot (Classic Quake .SPR)",
            file="progs/sight.spr", script="source/mm_tools/sniper.qc",
            desc="16×16 classic Quake IDSP v1 paletted red laser dot projected onto walls by the Sniper Rifle.",
        ),
        scale_u=1.5,
    ))

    # ==================== CATEGORY 4: SUPERCAR, VEHICLES, AIRCRAFT & FLIGHT GEAR ====================
    print("5. Packing Category 4: Pink Supercar, Driveable Vehicles, Aircraft & Flight Gear...", flush=True)
    t_psc_tex   = packer.add_tex_file(os.path.join(HERE, "out", "pink_supercar", "pink_supercar_atlas_2k.png"), max_dim=1280, quality=88)
    t_psc_glow  = packer.add_tex_file(os.path.join(HERE, "out", "pink_supercar", "pink_supercar_glow_2k.png"), max_dim=768, quality=85)
    t_psc_glass = packer.add_tex_file(os.path.join(HERE, "out", "pink_supercar", "pink_supercar_glass.png"), max_dim=256, force_png=True)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "pink_supercar.md3"),
        dict(
            id="pink_supercar", cat="vehicles", status="active", badge="EXOTIC V12 · 64f",
            title="Hot-Pink V12 Exotic Supercar + Roof Webcam",
            file="progs/pink_supercar.md3", script="source/mm_tools/build_pink_supercar.py",
            desc="14-surface, 64-frame metallic hot-pink V12 supercar with scanning roof webcam, opening scissor doors, pop-up hood, glowing LEDs & turbo boost!",
            clips=[
                dict(id="doors", label="🦋 Scissor Doors & Hood (16f)", start=32, count=16, fps=12.0, lie=True),
                dict(id="boost", label="🔥 Turbo Flame Boost (16f)", start=48, count=16, fps=16.0),
                dict(id="cruise", label="🏎️ Cruise Roll (16f)", start=16, count=16, fps=14.0),
                dict(id="idle", label="📷 Idle Webcam Scan (16f)", start=0, count=16, fps=10.0, lie=True),
                dict(id="all", label="🎬 All 64f", start=0, count=64, fps=14.0),
            ],
        ),
        surf_mats={
            "progs/pink_supercar_tex":   dict(tex=t_psc_tex, glowTex=t_psc_glow, metallic=0.42, roughness=0.24, spec=0.82),
            "progs/pink_supercar_glass": dict(tex=t_psc_glass, metallic=0.70, roughness=0.12, spec=0.92, alphaBlend=True),
        },
        allow_rigid=False, bbox_frames=[0],
    ))

    # Driveable Ground Vehicles (Van w/ 4 skins, Truck/Sedan/Coupe w/ 2 skins each)
    veh_clips = [
        dict(id="all", label="🎬 All 36f (Roll + Steer)", start=0, count=36, fps=14.0),
        dict(id="straight", label="🚗 Straight Roll (12f)", start=0, count=12, fps=14.0),
        dict(id="left", label="↩ Steer Left (12f)", start=12, count=12, fps=14.0),
        dict(id="right", label="↪ Steer Right (12f)", start=24, count=12, fps=14.0),
    ]
    t_van       = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_van_atlas.png"), max_dim=1024, quality=87)
    t_van_gl    = packer.add_tex_file(os.path.join(PROGS, "veh_van_tex_glow.png"), max_dim=512, quality=84)
    t_van_burn  = packer.add_tex_file(os.path.join(PROGS, "veh_van_burn.png"), max_dim=768, quality=85, lift=1.25)
    t_van_bgl   = packer.add_tex_file(os.path.join(PROGS, "veh_van_burn_glow.png"), max_dim=512, quality=84)
    t_van_glass = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_van_glass.png"), max_dim=256, force_png=True)
    t_van_glbrn = packer.add_tex_file(os.path.join(PROGS, "veh_van_glass_burn.png"), max_dim=256, force_png=True)

    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "veh_van.md3"),
        dict(
            id="veh_van", cat="vehicles", status="active", badge="WALK-IN VAN · 4 SKINS",
            title="Driveable Walk-In Ram ProMaster Cargo Van",
            file="progs/veh_van.md3", script="source/mm_tools/build_vehicles_assets.py",
            desc="36-frame driveable white cargo van with walk-in rear doors, full cab/cargo interior & 4 skins (Clean, Burned, Interior Cutaway Clean/Burned)!",
            clips=veh_clips,
            skins=[
                dict(label="🚐 Clean White", map={
                    "body_a": dict(tex=t_van, glowTex=t_van_gl, nodraw=False),
                    "body_b": dict(tex=t_van, glowTex=t_van_gl),
                    "interior": dict(tex=t_van, glowTex=t_van_gl),
                    "wheels": dict(tex=t_van, glowTex=t_van_gl),
                    "glass": dict(tex=t_van_glass),
                }),
                dict(label="🔥 Burned Scorched", map={
                    "body_a": dict(tex=t_van_burn, glowTex=t_van_bgl, nodraw=False),
                    "body_b": dict(tex=t_van_burn, glowTex=t_van_bgl),
                    "interior": dict(tex=t_van_burn, glowTex=t_van_bgl),
                    "wheels": dict(tex=t_van_burn, glowTex=t_van_bgl),
                    "glass": dict(tex=t_van_glbrn),
                }),
                dict(label="🔍 Interior Cutaway (Clean)", map={
                    "body_a": dict(nodraw=True),
                    "body_b": dict(tex=t_van, glowTex=t_van_gl),
                    "interior": dict(tex=t_van, glowTex=t_van_gl),
                    "wheels": dict(tex=t_van, glowTex=t_van_gl),
                    "glass": dict(tex=t_van_glass),
                }),
                dict(label="🔥 Interior Cutaway (Burned)", map={
                    "body_a": dict(nodraw=True),
                    "body_b": dict(tex=t_van_burn, glowTex=t_van_bgl),
                    "interior": dict(tex=t_van_burn, glowTex=t_van_bgl),
                    "wheels": dict(tex=t_van_burn, glowTex=t_van_bgl),
                    "glass": dict(tex=t_van_glbrn),
                }),
            ],
        ),
        surf_mats={
            "progs/veh_van_tex":   dict(tex=t_van, glowTex=t_van_gl, metallic=0.16, roughness=0.40, spec=0.48),
            "progs/veh_van_glass": dict(tex=t_van_glass, metallic=0.65, roughness=0.14, spec=0.90, alphaBlend=True),
        },
        allow_rigid=False,
    ))

    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "van_walkin.md3"),
        dict(
            id="van_walkin", cat="vehicles", status="active", badge="14-SURF BSP VAN",
            title="Walk-In Cargo Van High-Detail Architecture Mesh",
            file="progs/van_walkin.md3 + textures/van_walkin/*.tga",
            desc="14-material architectural walk-in cargo van with separate chrome, headlamps, amber markers, cloth seats, cargo walls & tinted glass.",
        ),
    ))

    for vid, title, desc in [
        ("veh_truck", "Driveable Pickup Truck (Clean & Burned Skins)",
         "36-frame driveable Quake pickup truck with rolling/steering wheels, open bed & Clean / Scorched Burned skins."),
        ("veh_sedan", "Driveable 4-Door Street Sedan (Clean & Burned Skins)",
         "36-frame driveable street sedan with rolling/steering wheels, emissive headlamps & Clean / Burned skins."),
        ("veh_coupe", "Driveable Two-Door Sports Coupe (Clean & Burned Skins)",
         "36-frame fast two-door sports coupe with rolling/steering wheels, emissive headlamps & Clean / Burned skins."),
    ]:
        t_clean = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", f"{vid}_atlas.png"), max_dim=768, quality=86)
        t_cgl   = packer.add_tex_file(os.path.join(PROGS, f"{vid}_tex_glow.png"), max_dim=512, quality=84)
        t_burn  = packer.add_tex_file(os.path.join(PROGS, f"{vid}_burn.png"), max_dim=768, quality=85, lift=1.25)
        t_bgl   = packer.add_tex_file(os.path.join(PROGS, f"{vid}_burn_glow.png"), max_dim=512, quality=84)
        models_out.append(pack_md3_asset(
            packer, os.path.join(PROGS, f"{vid}.md3"),
            dict(
                id=vid, cat="vehicles", status="active", badge="DRIVEABLE · 2 SKINS",
                title=title, file=f"progs/{vid}.md3", script="source/mm_tools/build_vehicles_assets.py",
                desc=desc, clips=veh_clips,
                skins=[
                    dict(label="🚗 Clean Paint + Lights", map={
                        "body": dict(tex=t_clean, glowTex=t_cgl), "wheels": dict(tex=t_clean, glowTex=t_cgl),
                    }),
                    dict(label="🔥 Scorched Burned + Embers", map={
                        "body": dict(tex=t_burn, glowTex=t_bgl), "wheels": dict(tex=t_burn, glowTex=t_bgl),
                    }),
                ],
            ),
            surf_mats={f"progs/{vid}_tex": dict(tex=t_clean, glowTex=t_cgl, metallic=0.24, roughness=0.36, spec=0.58)},
            allow_rigid=False,
        ))

    # 3 John Wave x Mega-Man Aircraft (72f) + 4 Sky-Vehicles (56f) + Jetpack (16f)
    jw_mats = {
        "progs/jw_air_scream": dict(tex=t_jw_scream, metallic=0.05, roughness=0.62, spec=0.28),
        "progs/jw_air_calm":   dict(tex=t_jw_calm,   metallic=0.05, roughness=0.60, spec=0.28),
        "progs/jw_air_fedora": dict(tex=t_jw_fed,    metallic=0.04, roughness=0.76, spec=0.24),
        "progs/jw_air_chrome": dict(tex=t_mm_chr,    metallic=0.88, roughness=0.17, spec=0.96),
        "progs/jw_air_wheel":  dict(tex=t_mm_whl,    metallic=0.16, roughness=0.52, spec=0.42),
        "progs/jw_air_wave":   dict(tex=t_jw_wave,   unlit=True),
        "progs/jw_air_fx":     dict(tex=t_jw_fx,     unlit=True, additive=True),
    }
    jw_clips = [
        dict(id="cruise", label="✈ Cruise (16f)", start=0, count=8, fps=6.0),
        dict(id="boost", label="🔥 Scream Boost (16f)", start=8, count=8, fps=9.0),
        dict(id="roll", label="🌀 360° Barrel Roll (16f)", start=28, count=8, fps=8.0),
        dict(id="hover", label="🚁 VTOL Hover (12f)", start=16, count=6, fps=5.0),
        dict(id="rest", label="🛬 Landed / Snoring (12f)", start=22, count=6, fps=4.0, lie=True),
        dict(id="all", label="🎬 All 72f (36kf)", start=0, count=36, fps=6.5),
    ]
    for vid, badge, title, fn_disp, desc in [
        ("jw_air_v1", "JW AIRCRAFT V1 · 72f", 'F-69 "The Mouth-Breather" Biplane', "progs/jw_aircraft.md3 (jw_air_v1.md3)",
         "Crimson-Fedora Giant Bobblehead John biplane with Gold Tire-Monocle, Mega-Man Cigar puffing 3D surf rings, mustache rotors & flapping henchmen wings!"),
        ("jw_air_v2", "JW AIRCRAFT V2 · 72f", 'SR-99 "In-One-Ear" Rocket Jet', "progs/jw_air_v2.md3",
         "Mach-5 Mega-Man Rocket spearing out of Giant John's mouth and skewering him ear-to-ear with tilt-rotor headphone tires & twin ramjets!"),
        ("jw_air_v3", "JW AIRCRAFT V3 · 72f", 'CH-99 "The Hair-icopter" Chinook', "progs/jw_air_v3.md3",
         "Push-Me-Pull-You twin-rotor Chinook with Deadpan Lush-Hair Johns fore & aft plus a Tire-Shades Biker midship!"),
    ]:
        models_out.append(pack_md3_asset(
            packer, os.path.join(PROGS, f"{vid}.md3"),
            dict(id=vid, cat="vehicles", status="active", badge=badge, title=title, file=fn_disp, desc=desc, clips=jw_clips),
            surf_mats=jw_mats, allow_rigid=False, frame_stride=2, bbox_frames=(0, 22),
        ))

    sky_mats = {
        "progs/skyveh_van":      dict(tex=t_van, glowTex=t_van_gl, metallic=0.14, roughness=0.42, spec=0.45),
        "progs/skyveh_bigears":  dict(tex=t_bigears,  metallic=0.05, roughness=0.62, spec=0.25),
        "progs/skyveh_pinklady": dict(tex=t_pinklady, metallic=0.06, roughness=0.52, spec=0.34),
        "progs/skyveh_chrome":   dict(tex=t_mm_chr,   metallic=0.78, roughness=0.18, spec=0.92),
        "progs/skyveh_wheel":    dict(tex=t_mm_whl,   metallic=0.12, roughness=0.64, spec=0.30),
        "progs/skyveh_fx":       dict(tex=t_sky_fx,   unlit=True, additive=True),
    }
    sky_clips = [
        dict(id="cruise", label="✈ Sky Cruise (16f)", start=0, count=8, fps=6.0),
        dict(id="boost", label="🔥 Sky Boost (16f)", start=8, count=8, fps=9.0),
        dict(id="hover", label="🚁 VTOL Hover (12f)", start=16, count=6, fps=5.0),
        dict(id="rest", label="🛬 Landed (12f)", start=22, count=6, fps=4.0, lie=True),
        dict(id="all", label="🎬 All 56f (28kf)", start=0, count=28, fps=6.0),
    ]
    for vid, badge, title, desc in [
        ("skyveh_v1", "SKY-VEHICLE V1 · 56f", "The Ear-nithopter Sky-Galleon",
         "ProMaster airship gondola with flapping giant ear-wings, 3D Pink Lady prow figurehead & forward chin chrome pitot-lance."),
        ("skyveh_v2", "SKY-VEHICLE V2 · 56f", "The Valkyrie V-22 Tilt-Rotor",
         "Heavy dropship with wingtip Osprey chrome nacelles spinning white-dish tire rotors, dorsal Atlas Pink Lady & Big-Ears canards."),
        ("skyveh_v3", "SKY-VEHICLE V3 · 56f", "The Podracer Sky-Chariot & Autogyro",
         "Screaming Big-Ears tractor pod towing the ProMaster chariot on twin chrome booms with overhead Pink Lady autogyro mast."),
        ("skyveh_v4", "SKY-VEHICLE V4 · 56f", "The Biomech Mecha-Wyvern",
         "Sky-dragon with barn-door Beetle Elytra wing-shells, arched chrome dragon neck with Big-Ears head & scorpion tail-rotor stinger."),
    ]:
        models_out.append(pack_md3_asset(
            packer, os.path.join(PROGS, f"{vid}.md3"),
            dict(id=vid, cat="vehicles", status="active", badge=badge, title=title,
                 file=f"progs/{vid}.md3", script="source/mm_tools/build_sky_vehicles.py", desc=desc, clips=sky_clips),
            surf_mats=sky_mats, allow_rigid=False, frame_stride=2, bbox_frames=(0, 22),
        ))

    jp_plumes = [os.path.join(PROGS, f"jetpack_plume_{k}.png") for k in range(4)]
    tid_jp_plume, ord_jp_plume = build_anim_atlas_from_files(packer, "jetpack_plume_4f", jp_plumes, max_tile_dim=256)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "jetpack.md3"),
        dict(
            id="jetpack", cat="vehicles", status="active", badge="FLIGHT GEAR · 16f",
            title="JP-02 Twin-Turbine Rocket Jetpack",
            file="progs/jetpack.md3", script="source/mm_tools/build_jetpack.py",
            desc="9-surface wearable rocket pack with brushed titanium tanks, cyan plasma window, PSI gauge, pilot sticks & 4-frame shock-diamond plumes!",
            az=2.55, el=0.16,
            clips=[
                dict(id="thrust", label="🔥 Afterburner Thrust (8f)", start=0, count=8, fps=15.0),
                dict(id="idle", label="🕯 Standby Pilot Flame (8f)", start=8, count=8, fps=10.0, lie=True),
                dict(id="all", label="🎬 All 16f", start=0, count=16, fps=14.0),
            ],
        ),
        surf_mats={
            "progs/jetpack_plume": dict(tex=tid_jp_plume, animFps=18.0, animOrder=ord_jp_plume, unlit=True, additive=True),
            "progs/jetpack_glow":  dict(tex=packer.add_tex_file(os.path.join(PROGS, "jetpack_glow.png"), max_dim=256), unlit=True),
            "progs/jetpack_dial":  dict(tex=packer.add_tex_file(os.path.join(PROGS, "jetpack_dial.png"), max_dim=256), unlit=True),
        },
        allow_rigid=False, bbox_frames=list(range(0, 8)),
    ))

    # ==================== CATEGORY 5: DEPLOYABLES, PROJECTILES, DEBRIS & FX ====================
    print("6. Packing Category 5: Deployables, Projectiles, Contraptions, Wrecks & FX...", flush=True)
    # NetSend PC with ALL 7 CRT screen skins + toggleable electric arc cage!
    tid_ns_loop, ord_ns_loop = build_anim_atlas_from_files(
        packer, "netsend_scr_loop16", [os.path.join(PROGS, f"netsend_s_l{k:02d}.png") for k in range(16)], max_tile_dim=256)
    tid_ns_off   = packer.add_tex_file(os.path.join(PROGS, "netsend_s_off.png"), max_dim=256)
    tid_ns_noise, ord_ns_noise = build_anim_atlas_from_files(
        packer, "netsend_scr_noise", [os.path.join(PROGS, f"netsend_s_n{k}.png") for k in range(3)], max_tile_dim=256)
    tid_ns_init, ord_ns_init = build_anim_atlas_from_files(
        packer, "netsend_scr_init", [os.path.join(PROGS, f"netsend_s_init{k}.png") for k in range(2)], max_tile_dim=256)
    tid_ns_lol, ord_ns_lol = build_anim_atlas_from_files(
        packer, "netsend_scr_lol", [os.path.join(PROGS, f"netsend_s_lol{k}.png") for k in range(2)], max_tile_dim=256)
    tid_ns_fst, ord_ns_fst = build_anim_atlas_from_files(
        packer, "netsend_scr_fst", [os.path.join(PROGS, f"netsend_s_fst{k}.png") for k in range(2)], max_tile_dim=256)
    tid_ns_dot, ord_ns_dot = build_anim_atlas_from_files(
        packer, "netsend_scr_dot", [os.path.join(PROGS, f"netsend_s_dot{k}.png") for k in range(2)], max_tile_dim=256)

    m_ns_arc = read_md3_fast(os.path.join(PROGS, "netsend_arc.md3"))
    sa_ns = m_ns_arc["surfaces"][0]
    t_ns_arc = packer.add_tex_file(os.path.join(PROGS, "netsend_arc.png"), max_dim=256, force_png=True)
    s_ns_arc_overlay = encode_surface(
        packer, "electric_arc_cage", sa_ns["shader"], sa_ns["st"], sa_ns["tris"], sa_ns["all_v"], sa_ns["all_n"],
        dict(tex=t_ns_arc, unlit=True, additive=True),
    )
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "netsend_pc.md3"),
        dict(
            id="netsend_pc", cat="props", status="active", badge="DEPLOYABLE · 8 SKINS · 50f",
            title="NetSend Retro CRT Desktop PC (All 7 Screen States + Arcs)",
            file="progs/netsend_pc.md3 + netsend_pc.md3_0..6.skin + netsend_arc.md3",
            script="source/mm_tools/build_netsend_assets.py",
            desc="50-frame deployable retro beige PC tower & CRT monitor spitting floppy disks—switch all 7 CRT boot/noise/LOL.BAT skins plus 3D Overload Electric Arcs!",
            clips=[dict(id="all", label="💾 Disk Rapid-Fire Loop (50f)", start=0, count=50, fps=15.0, lie=True)],
            skins=[
                dict(label="0: LOL Loop (16f)", map={"netsend_screen": dict(tex=tid_ns_loop, animFps=6.0, animOrder=ord_ns_loop), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="1: CRT Off", map={"netsend_screen": dict(tex=tid_ns_off, animFps=0.0, animOrder=None), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="2: Static Noise", map={"netsend_screen": dict(tex=tid_ns_noise, animFps=14.0, animOrder=ord_ns_noise), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="3: BIOS Init", map={"netsend_screen": dict(tex=tid_ns_init, animFps=4.0, animOrder=ord_ns_init), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="4: LOL.BAT Alert", map={"netsend_screen": dict(tex=tid_ns_lol, animFps=4.0, animOrder=ord_ns_lol), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="5: First Boot", map={"netsend_screen": dict(tex=tid_ns_fst, animFps=3.0, animOrder=ord_ns_fst), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="6: Cursor Blink", map={"netsend_screen": dict(tex=tid_ns_dot, animFps=3.0, animOrder=ord_ns_dot), "electric_arc_cage": dict(nodraw=True)}),
                dict(label="7: ⚡ Overload + 3D Arcs", map={"netsend_screen": dict(tex=tid_ns_loop, animFps=9.0, animOrder=ord_ns_loop), "electric_arc_cage": dict(nodraw=False)}),
            ],
        ),
        surf_mats={
            "netsend_screen": dict(tex=tid_ns_loop, animFps=6.0, animOrder=ord_ns_loop, unlit=True),
        },
        allow_rigid=False, lift_default=1.40, extra_surfaces=[s_ns_arc_overlay],
    ))

    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "netsend_disk.md3"),
        dict(
            id="netsend_disk", cat="props", status="active", badge="PROJECTILE · 8f",
            title='NetSend Spinning "LOL.BAT" 3.5" Floppy Disk',
            file="progs/netsend_disk.md3", script="source/mm_tools/build_netsend_assets.py",
            desc="8-frame spinning 3.5-inch floppy diskette projectile launched by v_netsend and netsend_pc.",
            clips=[dict(id="spin", label="💾 Frisbee Spin (8f)", start=0, count=8, fps=16.0)],
        ),
        allow_rigid=False, lift_default=1.40,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "netsend_arc.md3"),
        dict(
            id="netsend_arc", cat="props", status="active", badge="ELECTRIC FX · 8f",
            title="NetSend 3D Electric Arc Cage",
            file="progs/netsend_arc.md3", script="source/mm_tools/build_netsend_assets.py",
            desc="8-frame crackling 3D additive lightning cage enveloping overloaded NetSend PCs.",
            clips=[dict(id="arc", label="⚡ Electric Crackles (8f)", start=0, count=8, fps=15.0, lie=True)],
        ),
        surf_mats={"progs/netsend_arc": dict(tex=t_ns_arc, unlit=True, additive=True)},
        allow_rigid=False,
    ))

    # Mega-Man Contraptions, Explosion & Debris
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "megaman.md3"),
        dict(
            id="megaman", cat="props", status="active", badge="AUTONOMOUS BOT · 16f",
            title='Wheeled "Mega Man" Contraption (Scanned MD3)',
            file="progs/megaman.md3", script="source/mm_tools/megaman.qc",
            desc="16-frame two-wheeled Segway-pipe contraption that steers, honks, hops & leaps onto enemies!",
            clips=[dict(id="drive", label="⚙ Wheel Spin (16f)", start=0, count=16, fps=15.0)],
        ),
        surf_mats={"progs/megaman": dict(tex=t_mm_scan, metallic=0.25, roughness=0.48, spec=0.45)},
        allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "megaman_weapon", "megaman_clean.md3"),
        dict(
            id="megaman_clean", cat="props", status="active", badge="HIGH-DETAIL RIG · 16f",
            title="Mega-Man Precision Chrome Bar & Dish-Tires Rig",
            file="source/mm_tools/out/megaman_weapon/megaman_clean.md3",
            script="source/mm_tools/mmw_geometry.py",
            desc="Precision-lathed gleaming chrome bullet shaft, TIG cross-axle, cotter pins & 5-ribbed pneumatic rubber tires on concave white dish rims!",
            clips=[dict(id="spin", label="⚙ Dish-Tire Spin (16f)", start=0, count=16, fps=15.0)],
        ),
        surf_mats=mmw_mats, allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_explode.md3"),
        dict(
            id="mm_explode", cat="props", status="active", badge="SHATTER FX · 20f",
            title="Mega-Man 20-Frame Shatter & Fireball Explosion",
            file="progs/mm_explode.md3", script="source/mm_tools/build_mm_debris.py",
            desc="20-frame outward-flying Voronoi shell shatter + additive blast flash when a Mega-Man contraption detonates.",
            clips=[dict(id="boom", label="💥 20f Shatter Burst", start=0, count=20, fps=16.0, lie=True)],
        ),
        allow_rigid=False, bbox_frames=[2, 4],
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_wheel.md3"),
        dict(
            id="mm_wheel", cat="props", status="active", badge="DEBRIS · 16f",
            title="Mega-Man Detached Bouncing Tire Gib",
            file="progs/mm_wheel.md3", script="source/mm_tools/build_mm_debris.py",
            desc="16-frame spinning detached rubber tire & hubcap gib.",
            clips=[dict(id="spin", label="🛞 Tire Spin (16f)", start=0, count=16, fps=15.0)],
        ),
        allow_rigid=False,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_bar.md3"),
        dict(
            id="mm_bar", cat="props", status="active", badge="DEBRIS · MD3",
            title="Mega-Man Chrome Center Pipe Gib",
            file="progs/mm_bar.md3", script="source/mm_tools/build_mm_debris.py",
            desc="3,655-vertex fractured central bar gib thrown from Mega-Man explosions.",
        ),
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "mm_axle.md3"),
        dict(
            id="mm_axle", cat="props", status="active", badge="DEBRIS · MD3",
            title="Mega-Man Steel Hex Axle Gib",
            file="progs/mm_axle.md3", script="source/mm_tools/build_mm_debris.py",
            desc="Procedural hexagonal steel cross-axle rod with flanged end-caps.",
        ),
    ))
    models_out.append(build_constellation_md3(
        packer,
        [("mm_cap", os.path.join(PROGS, "mm_cap.md3"), None)]
        + [(f"mm_frag{k}", os.path.join(PROGS, f"mm_frag{k}.md3"), None) for k in range(1, 7)],
        dict(
            id="mm_shrapnel_pack", cat="props", status="active", badge="7-PIECE SHRAPNEL",
            title="Mega-Man 7-Piece Voronoi Shrapnel Constellation",
            file="progs/mm_cap.md3 + progs/mm_frag1..6.md3",
            script="source/mm_tools/build_mm_debris.py",
            desc="All 7 custom end-cap & Voronoi casing shrapnel models arranged in an inspection ring—click Solo in Surfaces to isolate any piece!",
        ),
        radius=16.0,
    ))

    # Pocket Rocket Projectile
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "pocket_rocket", "md3", "pocket_rocket_proj.md3"),
        dict(
            id="pocket_rocket_proj", cat="props", status="vault", badge="PROJECTILE · VAULT",
            title="Pocket Rocket Flying Superhero Projectile",
            file="source/mm_tools/out/pocket_rocket/md3/pocket_rocket_proj.md3",
            desc="Flying horizontal Pocket Rocket projectile complete with additive anime speedlines!",
            clips=[dict(id="fly", label="🚀 Supersonic Flight (8kf)", start=0, count=8, fps=7.0)],
        ),
        allow_rigid=False, frame_stride=2,
    ))

    # Hack Attack Monitor, Red Fedora, 5 LAN Debris Pieces, Zap Bolts & Laser Beams
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "hackmon_a.md3"),
        dict(
            id="hackmon_a", cat="props", status="active", badge='THROWN CRT · "> HACKING"',
            title='Thrown "> HACKING" CRT Monitor Projectile',
            file="progs/hackmon_a.md3", script="source/mm_tools/build_hackmon_models.py",
            desc="19-surface thrown CRT monitor with glowing green '> HACKING' terminal that zaps nearby enemies and puts Red Hat fedoras on them!",
        ),
        lift_default=1.35,
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "fedora.md3"),
        dict(
            id="fedora", cat="props", status="active", badge="HACKED HAT · MD3",
            title='Hack Attack "Red Hat" Linux Crimson Fedora',
            file="progs/fedora.md3", script="source/mm_tools/build_hackmon_models.py",
            desc="Procedural pinched-crown, curled-brim crimson fedora spawned onto hacked players' heads.",
        ),
        lift_default=1.30,
    ))
    for hid, title, desc in [
        ("hd_kbd", "Hack Debris: Retro AT/PS2 Mechanical Keyboard", "Wedge-profile beige mechanical keyboard gib with drawn keycaps & lock LEDs."),
        ("hd_mouse", "Hack Debris: Beige 2-Button Ball Mouse", "Retro 2-button serial/PS2 mouse gib from shattered Hack Attack CRTs."),
        ("hd_floppy", 'Hack Debris: 3.5" Floppy Diskette', "Procedural 3.5-inch diskette gib with metal shutter & striped label."),
        ("hd_cd", "Hack Debris: Iridescent Rainbow CD-ROM", "16-sided annular CD-ROM disc with center hole & HSV diffraction sheen."),
        ("hd_board", "Hack Debris: Green Motherboard PCB", "Green circuit board populated with DIP IC chips, gold fingers & copper traces."),
    ]:
        models_out.append(pack_md3_asset(
            packer, os.path.join(PROGS, f"{hid}.md3"),
            dict(
                id=hid, cat="props", status="active", badge="LAN DEBRIS · MD3",
                title=title, file=f"progs/{hid}.md3", script="source/mm_tools/build_hackdebris.py",
                desc=desc, el=0.52,
            ),
            lift_default=1.25,
        ))

    models_out.append(build_constellation_md3(
        packer,
        [(f"zap{k}", os.path.join(PROGS, f"zap{k}.md3"), None) for k in (1, 2, 3)],
        dict(
            id="zap_bolts", cat="props", status="active", badge="LIGHTNING FX · 3 SEEDS",
            title="Hack Attack Green Lightning Bolts (zap1, zap2, zap3)",
            file="progs/zap1.md3 + zap2.md3 + zap3.md3", script="source/mm_tools/build_hackmon_models.py",
            desc="All 3 crossed-ribbon green electric arc variants used when Hack Attack monitors zap victims (use Solo in Surfaces to inspect each bolt).",
        ),
        radius=0.0,
    ))
    models_out.append(build_constellation_md3(
        packer,
        [
            ("rob_laser_red", os.path.join(PROGS, "laser.md3"), None),
            ("ltg_laser_cyan", os.path.join(PROGS, "ltg_laser.md3"), None),
        ],
        dict(
            id="laser_beams", cat="props", status="active", badge="BEAM FX · 2 BEAMS",
            title="Rob Trap Red Laser & Laptop Gun Beam (laser + ltg_laser)",
            file="progs/laser.md3 + progs/ltg_laser.md3",
            desc="Additive crossed-ribbon laser beams for the Rob Dob Trap tripwire and Laptop Gun discharge (toggle/Solo in Surfaces).",
        ),
        radius=0.0,
    ))

    # Goo, Pickle Bomb/Gib, CCC, Pongball, Banana, JohnWave Ring, Aura, Milksplat, Sparks
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "goo.md3"),
        dict(
            id="goo", cat="props", status="active", badge="FOAM BLOB · 6f",
            title="Bio-Foam Expanding Sticky Goo Blob",
            file="progs/goo.md3", script="source/mm_tools/build_googun.py",
            desc="6-frame polyurethane bio-foam cluster morphing from a compact flying shot into an expanding sticky splat!",
            clips=[dict(id="splat", label="🧪 Glob -> Expanding Splat (6f)", start=0, count=6, fps=10.0)],
        ),
        allow_rigid=False,
    ))

    pk_bomb_paths = [os.path.join(PROGS, f"pickle_face_{k:02d}.png") for k in (15, 0, 1, 2, 1, 0)]
    tid_pk_bomb, ord_pk_bomb = build_anim_atlas_from_files(packer, "pickle_bombskin_6", pk_bomb_paths, max_tile_dim=256)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "pickle_bomb.md3"),
        dict(
            id="pickle_bomb", cat="props", status="active", badge="STICKY BOMB · ANIM",
            title="Thrown 3D Warty Pickle Bomb (Animated Face)",
            file="progs/pickle_bomb.md3 + scripts/pickle.shader",
            script="source/mm_tools/build_pickle_assets.py",
            desc="Curved, wart-displaced 3D gherkin mesh with a 5fps animmap wandering-eye Pickle Surprise face!",
            az=2.50, el=0.24,
        ),
        surf_mats={"progs/pickle_bombskin": dict(tex=tid_pk_bomb, animFps=5.0, animOrder=ord_pk_bomb, roughness=0.55)},
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "pickle_gib.md3"),
        dict(
            id="pickle_gib", cat="props", status="active", badge="SHRAPNEL · MD3",
            title="3D Warty Pickle Blast Shrapnel",
            file="progs/pickle_gib.md3", script="source/mm_tools/build_pickle_assets.py",
            desc="Bouncing 3D warty gherkin shrapnel showered outward when a Pickle Surprise balloon explodes.",
        ),
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "ccc.md3"),
        dict(
            id="ccc", cat="props", status="active", badge="CCC BOLT · MD3",
            title="Extruded 3D Yellow 'C' Bolt (CCC Gun)",
            file="progs/ccc.md3", script="source/mm_tools/build_ccc.py",
            desc="Bevelled 3D extruded yellow letter 'C' rapid-fire projectile.",
        ),
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "fg_pongball.md3"),
        dict(
            id="fg_pongball", cat="props", status="active", badge="RICOCHET · MD3",
            title="Rally Master Ricochet Ping-Pong Ball",
            file="progs/fg_pongball.md3", script="source/mm_tools/build_fungun_viewmodels.py",
            desc="2.2-unit orange table-tennis sphere that multiplies damage with every wall bounce.",
        ),
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(HERE, "out", "removed_guns_src", "banana_assets", "progs", "banana.md3"),
        dict(
            id="banana", cat="props", status="vault", badge="PROJECTILE · VAULT",
            title="Slippery 3D Banana Projectile",
            file="source/mm_tools/out/removed_guns_src/banana_assets/progs/banana.md3",
            script="source/mm_tools/build_banana_assets.py",
            desc="3D banana projectile from the archived Banana Gun.",
        ),
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "jw_wave.md3"),
        dict(
            id="jw_wave", cat="props", status="active", badge="TIDAL RING · MD3",
            title='Foamy "John Wave" Rippled Ocean Surf Ring',
            file="progs/jw_wave.md3", script="source/mm_tools/build_john_assets.py",
            desc="960-triangle curling Pacific tidal-wave ring expanding across the floor during John Wave attacks!",
            el=0.42,
        ),
        surf_mats={"progs/jw_wave": dict(tex=t_jw_wave, unlit=True)},
    ))
    t_aura = packer.add_tex_file(os.path.join(PROGS, "aura.png"), max_dim=256, wrap=True, force_png=True)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "aura.md3"),
        dict(
            id="aura", cat="props", status="active", badge="SCROLLING SHIELD",
            title="Spawn-Protection Scrolling Cyan Energy Aura",
            file="progs/aura.md3 + scripts/aura.shader",
            script="source/mm_tools/build_aura_assets.py",
            desc="672-triangle additive energy bubble with continuous vertical UV scrolling (tcmod scroll 0 0.6).",
        ),
        surf_mats={"progs/aura": dict(tex=t_aura, scrollV=0.6, unlit=True, additive=True)},
    ))
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "ltg_aura.md3"),
        dict(
            id="ltg_aura", cat="props", status="active", badge="WIFI AURA · 8f",
            title="Laptop Gun 8-Frame Wi-Fi & Cable Aura Card",
            file="progs/ltg_aura.md3 + scripts/ltgun.shader",
            script="source/mm_tools/build_ltgun_assets.py",
            desc="8-frame additive animated Wi-Fi & Ethernet cable halo card.",
        ),
        surf_mats={"progs/ltg_aura": dict(tex=packer.tex_map[("atlas", "ltg_aura_8f")], animFps=10.0, unlit=True, additive=True)},
    ))

    ms_mats = {}
    for k in range(6):
        tid_m = packer.add_tex_file(os.path.join(PROGS, f"milksplat_{k}.png"), max_dim=256, force_png=True)
        ms_mats[f"progs/milksplat_v{k}"] = dict(tex=tid_m, unlit=True, alphaBlend=True)
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "milksplat.md3"),
        dict(
            id="milksplat", cat="props", status="active", badge="6 SPLAT DECALS",
            title="Milky Impact Splatter Decals (6 Variants)",
            file="progs/milksplat.md3 + scripts/milky.shader",
            script="source/mm_tools/build_milky_assets.py",
            desc="6-frame wall/floor milk splatter decal model—play or scrub frames 0–5 to inspect all 6 splatter shapes!",
            el=0.45,
            clips=[dict(id="all", label="🥛 Cycle All 6 Splatters", start=0, count=6, fps=3.0, lie=True)],
        ),
        surf_mats=ms_mats, allow_rigid=False, bbox_frames=list(range(6)),
    ))

    models_out.append(build_sparks_mdl(packer))

    # Vehicle Explosion, 4 Exploding Wrecks & Blown-Off Vehicle Parts Constellation
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "veh_blast.md3"),
        dict(
            id="veh_blast", cat="props", status="active", badge="VEHICLE BLAST · 20f",
            title="Vehicle Explosion Shatter & Fireball (20f)",
            file="progs/veh_blast.md3", script="source/mm_tools/build_vehicles_assets.py",
            desc="20-frame outward-flying scorched vehicle hull shatter + additive fireball flash.",
            clips=[dict(id="boom", label="💥 20f Blast Burst", start=0, count=20, fps=15.0, lie=True)],
        ),
        allow_rigid=False, bbox_frames=[2, 4],
    ))
    for w_id, w_title in [
        ("veh_van_wreck", "Exploding Cargo Van Scorched Wreck (20f)"),
        ("veh_truck_wreck", "Exploding Pickup Truck Scorched Wreck (20f)"),
        ("veh_sedan_wreck", "Exploding 4-Door Sedan Scorched Wreck (20f)"),
        ("veh_coupe_wreck", "Exploding Sports Coupe Scorched Wreck (20f)"),
    ]:
        v_pre = w_id.replace("_wreck", "")
        t_wb = packer.add_tex_file(os.path.join(PROGS, f"{v_pre}_burn.png"), max_dim=768, quality=85, lift=1.25)
        t_wg = packer.add_tex_file(os.path.join(PROGS, f"{v_pre}_burn_glow.png"), max_dim=512, quality=84)
        models_out.append(pack_md3_asset(
            packer, os.path.join(PROGS, f"{w_id}.md3"),
            dict(
                id=w_id, cat="props", status="active", badge="SCORCHED WRECK · 20f",
                title=w_title, file=f"progs/{w_id}.md3", script="source/mm_tools/build_vehicles_assets.py",
                desc=f"20-frame crumpling & smoldering {v_pre.replace('veh_', '')} wreckage hull with glowing ember lightmap.",
                clips=[dict(id="wreck", label="🔥 Crumple & Smolder (20f)", start=0, count=20, fps=14.0, lie=True)],
            ),
            surf_mats={f"progs/{v_pre}_burn": dict(tex=t_wb, glowTex=t_wg, metallic=0.25, roughness=0.62, spec=0.30)},
            allow_rigid=False, bbox_frames=[0, 19],
        ))

    veh_part_specs = []
    for vp in ("van", "truck", "sedan", "coupe"):
        for pt in ("door", "hood", "bumper", "wheel", "extra"):
            veh_part_specs.append((f"{vp}_{pt}", os.path.join(PROGS, f"veh_{vp}_{pt}.md3"), None))
    for sk in range(1, 5):
        veh_part_specs.append((f"shrap{sk}", os.path.join(PROGS, f"veh_shrap{sk}.md3"), None))
    models_out.append(build_constellation_md3(
        packer,
        veh_part_specs,
        dict(
            id="veh_blown_parts", cat="props", status="active", badge="24 BLOWN-OFF PARTS",
            title="Blown-Off Vehicle Doors, Hoods, Bumpers, Wheels & Shrapnel (All 24)",
            file="progs/veh_*_{door,hood,bumper,wheel,extra}.md3 + veh_shrap1..4.md3",
            script="source/mm_tools/build_vehicles_assets.py",
            desc="Complete 24-piece constellation of every blown-off door, scorched hood, bumper, 16-frame spinning wheel & shrapnel chunk across all 4 vehicles—use Solo in Surfaces to inspect any piece!",
        ),
        radius=95.0,
    ))

    # Bronze Horse Monument
    models_out.append(pack_md3_asset(
        packer, os.path.join(PROGS, "gw_horse.md3"),
        dict(
            id="gw_horse", cat="props", status="active", badge="MONUMENT · 3,692t",
            title="Rearing Bronze Horse Statue on Rocky Plinth",
            file="progs/gw_horse.md3",
            desc="3,692-triangle sculpted bronze stallion monument rearing atop a rugged stone plinth.",
        ),
        surf_mats={
            "progs/gw_horse": dict(tex=packer.add_tex_file(os.path.join(PROGS, "gw_horse.png"), max_dim=512, lift=1.40),
                                   metallic=0.72, roughness=0.30, spec=0.80),
            "progs/gw_rock":  dict(tex=packer.add_tex_file(os.path.join(PROGS, "gw_rock.png"), max_dim=512, lift=1.35),
                                   metallic=0.05, roughness=0.82, spec=0.18),
        },
    ))

    # ==================== INTEGRITY VALIDATION & HTML OUTPUT ====================
    print(f"7. Validating {len(models_out)} packed custom assets & {len(packer.tex_list)} textures/atlases...", flush=True)
    seen_ids = set()
    arena_len = len(packer.buf)
    num_tex = len(packer.tex_list)
    cat_counts = {}

    for m in models_out:
        mid = m["id"]
        assert mid not in seen_ids, f"Duplicate model id: {mid}"
        seen_ids.add(mid)
        assert m["cat"] in ("guns", "chars", "sprites", "vehicles", "props"), f"Bad cat on {mid}: {m['cat']}"
        cat_counts[m["cat"]] = cat_counts.get(m["cat"], 0) + 1
        assert m["nf"] >= 1 and len(m["surfaces"]) >= 1 and len(m["clips"]) >= 1, f"Empty model {mid}"
        if "rigidMats" in m:
            off, ln = m["rigidMats"]
            assert 0 <= off and off + ln <= arena_len and ln == m["nf"] * 48, f"Bad rigidMats on {mid}"
        surf_names = {s["name"] for s in m["surfaces"]}
        for s in m["surfaces"]:
            assert s["nfGeom"] >= 1, f"Missing nfGeom on {mid}:{s['name']}"
            for bk in ("tris", "edges", "uv", "pos", "nrm"):
                off, ln = s[bk]
                assert 0 <= off and off + ln <= arena_len, f"Out-of-bounds slice {bk} on {mid}:{s['name']}"
            assert -1 <= s["tex"] < num_tex, f"Bad tex index {s['tex']} on {mid}:{s['name']}"
            assert -1 <= s["glowTex"] < num_tex, f"Bad glowTex index {s['glowTex']} on {mid}:{s['name']}"
        for sk in m.get("skins", []):
            for sk_surf, ov in sk["map"].items():
                assert sk_surf in surf_names, f"Skin {sk['label']} references unknown surface {sk_surf} on {mid}"
                if "tex" in ov:
                    assert -1 <= ov["tex"] < num_tex, f"Bad skin tex on {mid}"
                if "glowTex" in ov:
                    assert -1 <= ov["glowTex"] < num_tex, f"Bad skin glowTex on {mid}"

    print("   Category breakdown:", cat_counts, "-> TOTAL:", len(models_out), flush=True)

    raw_bytes = bytes(packer.buf)
    gz_bytes = gzip.compress(raw_bytes, compresslevel=6)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    tex_uri_bytes = sum(len(t["uri"]) for t in packer.tex_list)
    print(
        f"   Geometry arena: {len(raw_bytes)/1e6:.2f} MB raw -> {len(gz_bytes)/1e6:.2f} MB gzip ({len(b64_gz)/1e6:.2f} MB b64)\n"
        f"   Textures/Atlases: {num_tex} items ({tex_uri_bytes/1e6:.2f} MB data URIs)",
        flush=True,
    )

    meta_obj = dict(
        palette=PALETTE_U8.ravel().tolist(),
        anorm=ANORM_F32.round(4).ravel().tolist(),
        sounds=sounds,
        textures=packer.tex_list,
        models=models_out,
    )
    meta_json = json.dumps(meta_obj, separators=(",", ":"))

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    assert "/*__META_JSON__*/" in tpl, "Missing /*__META_JSON__*/ in template!"
    assert "/*__BIN_GZ__*/" in tpl, "Missing /*__BIN_GZ__*/ in template!"
    html = tpl.replace("/*__META_JSON__*/", meta_json, 1).replace("/*__BIN_GZ__*/", b64_gz, 1)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"8. Wrote Master All-Assets Inspector HTML: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)", flush=True)


if __name__ == "__main__":
    main()
