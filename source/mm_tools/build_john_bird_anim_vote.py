"""Build 100% self-contained single-file 3D WebGL2 Animation Voting Studio,
Interactive SkyPad Flight & Hit Sandbox, and QC Plan page:
  source/mm_tools/out/john_bird/john_bird_anim_vote.html

Reads base textures, feather MD3, baseline cruise MD3, and WebAudio WAVs
in-memory from bakersfield.pk3 / zz_johnbird.pk3 (zero loose file unpacking),
combined with candidate animations from:
  source/mm_tools/out/john_bird/vote_candidates/john_bird_candidates.md3
  source/mm_tools/out/john_bird/vote_candidates/candidates_manifest.json
and planned QC mechanics from:
  docs/john_bird_skypad_anim_plan.md
"""
import base64
import gzip
import io
import json
import math
import os
import struct
import sys
import wave
import zipfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(HERE, "out", "john_bird")
CAND_DIR = os.path.join(OUT_DIR, "vote_candidates")
TEMPLATE = os.path.join(HERE, "john_bird_anim_vote.template.html")
OUT_HTML = os.path.join(OUT_DIR, "john_bird_anim_vote.html")
QC_PLAN_MD = os.path.join(ROOT_DIR, "docs", "john_bird_skypad_anim_plan.md")

BAKO_PK3 = os.path.join(ROOT_DIR, "bakersfield.pk3")
JB_PK3 = os.path.join(ROOT_DIR, "zz_johnbird.pk3")

VOICE_QUOTES = [
    ("jv_fly00", "Hmm... I'm floating!"),
    ("jv_fly01", "Do you have hairspray?"),
    ("jv_fly02", "My name is John."),
    ("jv_fly03", "This is John."),
    ("jv_fly04", "Ride the wave of the future, baby!"),
    ("jv_fly05", "John Wave '99!"),
]


def _cstr(b):
    return b.split(b"\0", 1)[0].decode("ascii", "replace")


def read_md3_bytes(d, label="<memory>", max_frames=None):
    """Parse an MD3 binary buffer in-memory without touching disk."""
    ident, ver, name, _flags, nf, _ntags, ns, _nsk, ofs_f, _ofs_t, ofs_s, _ofs_e = struct.unpack("<4si64s9i", d[:108])
    assert ident == b"IDP3" and ver == 15, f"Invalid MD3 header in {label}"
    use_nf = min(nf, max_frames) if max_frames is not None else nf
    frames = []
    for i in range(use_nf):
        o = ofs_f + 56 * i
        v = struct.unpack("<10f16s", d[o:o + 56])
        frames.append((v[0:3], v[3:6], v[9], _cstr(v[10])))

    surfaces = []
    o = ofs_s
    for _ in range(ns):
        h = struct.unpack("<4s64s10i", d[o:o + 108])
        sname, _sflags, snf, _nsh, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end = _cstr(h[1]), *h[2:]
        tris = [struct.unpack("<3i", d[o + o_tri + 12 * i:o + o_tri + 12 * i + 12]) for i in range(nt)]
        shader = _cstr(d[o + o_sh:o + o_sh + 64])
        st = [struct.unpack("<2f", d[o + o_st + 8 * i:o + o_st + 8 * i + 8]) for i in range(nv)]
        fr = []
        for f in range(min(snf, use_nf)):
            base = o + o_xyz + f * nv * 8
            vv, nn = [], []
            for i in range(nv):
                x, y, z, n = struct.unpack("<3hH", d[base + 8 * i:base + 8 * i + 8])
                vv.append((x / 64.0, y / 64.0, z / 64.0))
                nn.append(md3lib.dec_normal(n))
            fr.append((vv, nn))
        surfaces.append(dict(name=sname, shader=shader, tris=tris, st=st, frames=fr))
        o += o_end
    return dict(name=_cstr(name), frames=frames, surfaces=surfaces, nframes=use_nf)


def compact_wav_bytes(raw_wav_bytes, target_sr=16000):
    """Compact an input WAV byte buffer to 16 kHz mono 16-bit PCM WAV for embedded WebAudio."""
    with wave.open(io.BytesIO(raw_wav_bytes), "rb") as w:
        sr, ch, _sw, nf = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(nf)
    arr = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    if ch > 1:
        arr = arr.reshape(-1, ch).mean(axis=1)
    if sr != target_sr and len(arr) > 1:
        n_out = max(1, int(round(len(arr) * float(target_sr) / float(sr))))
        arr = np.interp(np.linspace(0.0, len(arr) - 1, n_out), np.arange(len(arr), dtype=np.float64), arr)
    pcm = np.clip(np.round(arr * 32767.0), -32767, 32767).astype("<i2")
    bio = io.BytesIO()
    with wave.open(bio, "wb") as out_w:
        out_w.setnchannels(1)
        out_w.setsampwidth(2)
        out_w.setframerate(target_sr)
        out_w.writeframes(pcm.tobytes())
    return bio.getvalue()


class ArenaPacker:
    def __init__(self):
        self.buf = bytearray()
        self.tex_list = []

    def add_bytes(self, raw_bytes):
        while len(self.buf) & 7:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(raw_bytes)
        return [off, len(raw_bytes)]

    def add_tex_bytes(self, raw_img_bytes, max_dim=1024, jpeg_q=91):
        im = Image.open(io.BytesIO(raw_img_bytes)).convert("RGB")
        w0, h0 = im.size
        if max_dim and max(w0, h0) > max_dim:
            sc = max_dim / float(max(w0, h0))
            im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))), Image.Resampling.LANCZOS)
        bio = io.BytesIO()
        im.save(bio, "JPEG", quality=jpeg_q, optimize=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_list.append(dict(uri=uri, w=im.size[0], h=im.size[1]))
        return idx


def build_wire_edges(tri_arr):
    e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
    e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
    e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


def pack_md3_dict(packer, m, surf_mats):
    nf = m["nframes"]
    surfs_out = []
    tot_v, tot_t = 0, 0
    pts_all = []

    for s in m["surfaces"]:
        sname = s["name"]
        nv = len(s["st"])
        uv_arr = np.asarray(s["st"], dtype="<f4")
        tri_arr = np.asarray(s["tris"], dtype="<u2")
        edges_arr = build_wire_edges(tri_arr)
        nt = len(tri_arr)
        tot_v += nv
        tot_t += nt

        all_v = np.stack([np.asarray(fr[0], dtype=np.float32) for fr in s["frames"]], axis=0)
        all_n = np.stack([np.asarray(fr[1], dtype=np.float32) for fr in s["frames"]], axis=0)
        pts_all.append(all_v[0])

        pos_scale = 1.0 / 64.0
        pos_i16 = np.zeros((nf, nv, 4), dtype="<i2")
        pos_i16[:, :, :3] = np.clip(np.round(all_v * 64.0), -32767, 32767).astype("<i2")
        dpos = pos_i16.copy()
        if nf > 1:
            dpos[1:] = ((pos_i16[1:].astype(np.int32) - pos_i16[:-1].astype(np.int32)) & 0xFFFF).astype("<u2").view("<i2")

        n_len = np.maximum(np.linalg.norm(all_n, axis=2, keepdims=True), 1e-8)
        nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
        nrm_i8[:, :, :3] = np.clip(np.round((all_n / n_len) * 127.0), -127, 127).astype("<i1")
        dnrm = nrm_i8.copy()
        if nf > 1:
            dnrm[1:] = ((nrm_i8[1:].astype(np.int32) - nrm_i8[:-1].astype(np.int32)) & 0xFF).astype("<u1").view("<i1")

        mat = surf_mats[sname]
        surfs_out.append(dict(
            name=sname,
            nv=nv,
            nt=nt,
            ne=len(edges_arr),
            posScale=pos_scale,
            tris=packer.add_bytes(tri_arr.tobytes()),
            edges=packer.add_bytes(edges_arr.tobytes()),
            uv=packer.add_bytes(uv_arr.tobytes()),
            pos=packer.add_bytes(dpos.tobytes()),
            nrm=packer.add_bytes(dnrm.tobytes()),
            tex=mat["tex"],
            altTex=mat.get("altTex", mat["tex"]),
            hurtTex=mat.get("hurtTex", mat["tex"]),
            roughness=mat.get("roughness", 0.55),
            spec=mat.get("spec", 0.35),
        ))

    pts_cat = np.vstack(pts_all)
    bmin = pts_cat.min(axis=0).round(2).tolist()
    bmax = pts_cat.max(axis=0).round(2).tolist()
    return dict(nf=nf, nv=tot_v, nt=tot_t, bbox=[bmin, bmax], surfaces=surfs_out)


def read_pk3_member(z_bako, z_jb, rel_path, fallback_disk_paths=()):
    """Read an asset cleanly from zz_johnbird.pk3, bakersfield.pk3, or explicit disk fallbacks."""
    for z in (z_jb, z_bako):
        if z is not None and rel_path in z.namelist():
            return z.read(rel_path)
    for p in fallback_disk_paths:
        if p and os.path.isfile(p):
            with open(p, "rb") as f:
                return f.read()
    raise FileNotFoundError(f"Asset not found in pk3s or disk: {rel_path}")


def load_manifest():
    manifest_p = os.path.join(CAND_DIR, "candidates_manifest.json")
    assert os.path.isfile(manifest_p), f"Missing {manifest_p} (waiting for @anim-gen)"
    raw = json.load(open(manifest_p, "r", encoding="utf-8"))
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("candidates") or raw.get("clips") or raw.get("items") or []
    else:
        raise ValueError("Unsupported candidates_manifest.json format")

    norm = []
    for it in items:
        norm.append(dict(
            id=it["id"],
            category=it["category"],
            badge=it.get("badge", it["id"].upper()),
            title=it["title"],
            subtitle=it.get("subtitle", ""),
            description=it.get("description", it.get("desc", "")),
            startFrame=int(it["startFrame"]),
            frameCount=int(it.get("frameCount", 16)),
            defaultFps=float(it.get("defaultFps", 20.0)),
            recommendedSound=it.get("recommendedSound", "swoop"),
            highlights=it.get("highlights", []),
            chips=it.get("chips", []),
        ))
    return norm


def main():
    assert os.path.isfile(BAKO_PK3), f"Missing {BAKO_PK3}"
    cand_md3_p = os.path.join(CAND_DIR, "john_bird_candidates.md3")
    assert os.path.isfile(cand_md3_p), f"Missing {cand_md3_p} (waiting for @anim-gen)"
    assert os.path.isfile(QC_PLAN_MD), f"Missing {QC_PLAN_MD} (waiting for @qc-spec)"
    assert os.path.isfile(TEMPLATE), f"Missing {TEMPLATE}"

    candidates = load_manifest()
    qc_plan_md = open(QC_PLAN_MD, "r", encoding="utf-8").read()

    z_bako = zipfile.ZipFile(BAKO_PK3, "r")
    z_jb = zipfile.ZipFile(JB_PK3, "r") if os.path.isfile(JB_PK3) else None

    try:
        packer = ArenaPacker()

        # Textures (in-memory from pk3 / out_dir fallback)
        t_head = packer.add_tex_bytes(
            read_pk3_member(z_bako, z_jb, "progs/john_bird_head.png", [os.path.join(OUT_DIR, "john_bird_head.png")]),
            max_dim=1024, jpeg_q=91,
        )
        t_hair = packer.add_tex_bytes(
            read_pk3_member(z_bako, z_jb, "progs/john_bird_hair.png", [os.path.join(OUT_DIR, "john_bird_hair.png")]),
            max_dim=512, jpeg_q=90,
        )
        t_wing_hawk = packer.add_tex_bytes(
            read_pk3_member(z_bako, z_jb, "progs/john_bird_wings.png", [os.path.join(OUT_DIR, "john_bird_wings.png")]),
            max_dim=1024, jpeg_q=89,
        )
        t_wing_hurt = packer.add_tex_bytes(
            read_pk3_member(z_bako, z_jb, "progs/john_bird_wings_hurt.png"),
            max_dim=1024, jpeg_q=88,
        )
        t_wing_white = packer.add_tex_bytes(
            read_pk3_member(z_bako, z_jb, "progs/john_bird_wings_white.png", [os.path.join(OUT_DIR, "john_bird_wings_white.png")]),
            max_dim=1024, jpeg_q=88,
        )

        surf_mats = {
            "head":        dict(tex=t_head, roughness=0.62, spec=0.28),
            "hair_breezy": dict(tex=t_hair, roughness=0.38, spec=0.56),
            "wings_bird":  dict(tex=t_wing_hawk, altTex=t_wing_white, hurtTex=t_wing_hurt, roughness=0.52, spec=0.36),
        }

        # 1. Candidates MD3 (192 frames)
        cand_bytes = open(cand_md3_p, "rb").read()
        cand_raw = read_md3_bytes(cand_bytes, label=cand_md3_p)
        candidates_dict = pack_md3_dict(packer, cand_raw, surf_mats)

        # 2. Baseline Cruise MD3 (first 16 frames of john_bird_head.md3 from pk3)
        base_head_bytes = read_pk3_member(
            z_bako, z_jb, "progs/john_bird_head.md3", [os.path.join(OUT_DIR, "john_bird_head.md3")]
        )
        cruise_raw = read_md3_bytes(base_head_bytes, label="progs/john_bird_head.md3", max_frames=16)
        cruise_dict = pack_md3_dict(packer, cruise_raw, surf_mats)

        # 3. 3D Feather MD3 (in-memory from bakersfield.pk3)
        feather_bytes = read_pk3_member(z_bako, z_jb, "progs/john_bird_feather.md3")
        feather_raw = read_md3_bytes(feather_bytes, label="progs/john_bird_feather.md3")
        feather_dict = pack_md3_dict(packer, feather_raw, {"feather": dict(tex=t_wing_hawk, roughness=0.52, spec=0.32)})

        # 4. Compact WebAudio SFX + 6 John Voice Lines (in-memory from bakersfield.pk3)
        sfx_map = {
            "flap1": "sound/john_bird/flap1.wav",
            "flap2": "sound/john_bird/flap2.wav",
            "flap3": "sound/john_bird/flap3.wav",
            "flap4": "sound/john_bird/flap4.wav",
            "swoop": "sound/john_bird/swoop.wav",
            "feather_hit": "sound/john_bird/feather_hit.wav",
            "jv_hurt": "sound/john_bird/jv_hurt.wav",
            "skypad_launch": "sound/skypad/launch.wav",
        }
        sfx_out = {}
        for key, rel_p in sfx_map.items():
            wav_raw = read_pk3_member(z_bako, z_jb, rel_p)
            sfx_out[key] = packer.add_bytes(compact_wav_bytes(wav_raw, 16000))

        voices_out = []
        for vid, quote in VOICE_QUOTES:
            wav_raw = read_pk3_member(z_bako, z_jb, f"sound/john_bird/{vid}.wav")
            voices_out.append(dict(
                id=vid,
                quote=quote,
                buf=packer.add_bytes(compact_wav_bytes(wav_raw, 16000)),
            ))

    finally:
        z_bako.close()
        if z_jb is not None:
            z_jb.close()

    raw_arena = bytes(packer.buf)
    gz_arena = gzip.compress(raw_arena, compresslevel=9, mtime=0)
    print(
        f"Binary arena (Candidates {candidates_dict['nf']}f + Cruise {cruise_dict['nf']}f + Feather + {len(sfx_out)} SFX + {len(voices_out)} Voices): "
        f"{len(raw_arena)/1e6:.2f} MB raw -> {len(gz_arena)/1e6:.2f} MB gzipped"
    )

    payload = dict(
        textures=packer.tex_list,
        candidatesModel=candidates_dict,
        cruiseModel=cruise_dict,
        feather=feather_dict,
        candidates=candidates,
        audio=dict(sfx=sfx_out, voices=voices_out),
        qcPlanMd=qc_plan_md,
    )
    payload["binGz"] = base64.b64encode(gz_arena).decode("ascii")

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    marker = "/*__JBIRD_VOTE_DATA__*/null"
    assert marker in tpl, f"Missing marker {marker} in {TEMPLATE}"
    html = tpl.replace(marker, json.dumps(payload, separators=(",", ":")), 1)

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote self-contained 3D Animation Voting Studio: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
