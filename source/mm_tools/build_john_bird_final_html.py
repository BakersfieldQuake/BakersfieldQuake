"""Build 100% self-contained Final Shipped Update & Interactive 3D Showcase HTML:
  source/mm_tools/out/john_bird/john_bird_final_update.html

Reads the final shipped 164-frame progs/john_bird_head.md3 directly from
zz_johnbird.pk3 (in-memory via zipfile.ZipFile), plus john_bird_feather.md3,
textures, and WebAudio SFX from bakersfield.pk3 / zz_johnbird.pk3.
"""
import base64
import gzip
import hashlib
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
TEMPLATE = os.path.join(HERE, "john_bird_final_update.template.html")
OUT_HTML = os.path.join(OUT_DIR, "john_bird_final_update.html")

BAKO_PK3 = os.path.join(ROOT_DIR, "bakersfield.pk3")
JB_PK3 = os.path.join(ROOT_DIR, "zz_johnbird.pk3")
PROGS_DAT = os.path.join(ROOT_DIR, "progs.dat")
PROGS_LNO = os.path.join(ROOT_DIR, "progs.lno")

VOICE_QUOTES = [
    ("jv_fly00", "Hmm... I'm floating!"),
    ("jv_fly01", "Do you have hairspray?"),
    ("jv_fly02", "My name is John."),
    ("jv_fly03", "This is John."),
    ("jv_fly04", "Ride the wave of the future, baby!"),
    ("jv_fly05", "John Wave '99!"),
]

WINNERS = [
    dict(
        id="fast_fly",
        badge="F1 · Winner",
        title="Whip-Snap High-RPM Flap",
        subtitle="fast_fly · frames 100..115 (16f)",
        trigger="hspd >= 950 u/s (Shift Boost or Mouse Carve, level/climb)",
        description=(
            "Asymmetric power-stroke cadence snaps the wings down violently and tucks tight on the upstroke, "
            "while sleek skull-hugging crown hair pairs with crisp 4-harmonic S-waves rolling through oversized brow bangs."
        ),
        startFrame=100,
        frameCount=16,
        defaultFps=24,
        recommendedSound="john_bird/swoop.wav",
        highlights=[
            ["QC Trigger", "hspd >= 950 u/s when velocity_z >= -420 (22..32 fps dynamic)"],
            ["Audio Cadence", "0.14..0.24s rapid flaps @ 108..126% pitch"],
            ["Hair & Silhouette", "Sleek skull-hugging crown + crisp wavy brow bangs"],
        ],
    ),
    dict(
        id="hit_flail",
        badge="H1 · Winner",
        title="Asymmetric Panic Roll & Cross-Flap",
        subtitle="hit_flail · frames 116..131 (16f)",
        trigger="JB_Pain damage reaction (jb_hurt_until = time + 0.65s)",
        description=(
            "Left and right wings fire 135 degrees out of phase at mismatched sweeps while John's head snaps violently "
            "side-to-side in roll and yaw, whipping bangs across his face amid a 0.18s scorched hurt-wing flash and 8x feather burst."
        ),
        startFrame=116,
        frameCount=16,
        defaultFps=28,
        recommendedSound="john_bird/feather_hit.wav",
        highlights=[
            ["QC Trigger", "JB_Pain -> 0.65s flail + 0.18s skin=1 hurt flash + pilot punch"],
            ["Audio Cadence", "0.11s erratic multi-directional flaps (118 +/- 18% pitch) + feather_hit.wav"],
            ["Motion", "135-deg out-of-phase L/R wings + +-24 deg panic roll jerks"],
        ],
    ),
    dict(
        id="skypad_hyper",
        badge="S3 · Winner",
        title="Hyper-Flutter Afterburner",
        subtitle="skypad_hyper · frames 132..147 (16f)",
        trigger="info_skypad launch (jb_skypad_until > time || hspd >= 1500 u/s)",
        description=(
            "After blasting off an info_skypad at up to 4,000+ u/s (sv_maxvelocity 6500), John flaps at an unhinged "
            "4-beat afterburner tempo sending huge crashing multi-harmonic shockwaves through 3.4x stretched hair and streaming feathers."
        ),
        startFrame=132,
        frameCount=16,
        defaultFps=32,
        recommendedSound="skypad/launch.wav",
        highlights=[
            ["QC Trigger", "SkyPad_Touch + 20 Hz JB_CheckSkyPads -> ballistic arc + 0.06s feather trail"],
            ["Speed & FPS", "30..42 fps supersonic playback; preserves SkyPad launch velocity"],
            ["Audio", "skypad/launch.wav on pad impact + rapid afterburner flaps"],
        ],
    ),
    dict(
        id="crazy_flip",
        badge="W3 · Winner",
        title="Unhinged Somersault Flip-Chaos",
        subtitle="crazy_flip · frames 148..163 (16f)",
        trigger="Press R (impulse 41) while flying John Bird (1.0s cooldown)",
        description=(
            "Total aerial anarchy on demand: seamless 360-degree diagonal somersault flip while one wing over-folds high "
            "and the other paddles low amid heavy feather splay, forward/upward surge, and exploding multi-directional hair waves."
        ),
        startFrame=148,
        frameCount=16,
        defaultFps=30,
        recommendedSound="john_bird/swoop.wav",
        highlights=[
            ["QC Trigger", "R key (impulse 41) -> 0.65s crazy_flip + surge + 6x feathers + 1.0s cooldown"],
            ["Priority", "hit_flail > crazy_flip > skypad_hyper > combat_whip > swoop_dive > fast_fly"],
            ["Motion", "Seamless 360-deg diagonal somersault + rubbery asymmetric wing paddling"],
        ],
    ),
]


def _cstr(b):
    return b.split(b"\0", 1)[0].decode("ascii", "replace")


def read_md3_bytes(d, label="<memory>"):
    ident, ver, name, _flags, nf, _ntags, ns, _nsk, ofs_f, _ofs_t, ofs_s, _ofs_e = struct.unpack("<4si64s9i", d[:108])
    assert ident == b"IDP3" and ver == 15, f"Invalid MD3 header in {label}"
    frames = []
    for i in range(nf):
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
        for f in range(snf):
            base = o + o_xyz + f * nv * 8
            vv, nn = [], []
            for i in range(nv):
                x, y, z, n = struct.unpack("<3hH", d[base + 8 * i:base + 8 * i + 8])
                vv.append((x / 64.0, y / 64.0, z / 64.0))
                nn.append(md3lib.dec_normal(n))
            fr.append((vv, nn))
        surfaces.append(dict(name=sname, shader=shader, tris=tris, st=st, frames=fr))
        o += o_end
    return dict(name=_cstr(name), frames=frames, surfaces=surfaces, nframes=nf)


def compact_wav_bytes(raw_wav_bytes, target_sr=16000):
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


def read_pk3_member(z_primary, z_secondary, rel_path):
    for z in (z_primary, z_secondary):
        if z is not None and rel_path in z.namelist():
            return z.read(rel_path)
    raise FileNotFoundError(f"Asset not found in pk3s: {rel_path}")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    assert os.path.isfile(BAKO_PK3), f"Missing {BAKO_PK3}"
    assert os.path.isfile(JB_PK3), f"Missing {JB_PK3}"
    assert os.path.isfile(PROGS_DAT), f"Missing {PROGS_DAT}"
    assert os.path.isfile(TEMPLATE), f"Missing {TEMPLATE}"

    z_bako = zipfile.ZipFile(BAKO_PK3, "r")
    z_jb = zipfile.ZipFile(JB_PK3, "r")

    try:
        # Read final shipped 164-frame MD3 directly from zz_johnbird.pk3
        jb_md3_bytes = z_jb.read("progs/john_bird_head.md3")
        jb_raw = read_md3_bytes(jb_md3_bytes, label="zz_johnbird.pk3:progs/john_bird_head.md3")
        assert jb_raw["nframes"] == 164, f"Expected 164 frames in zz_johnbird.pk3 progs/john_bird_head.md3, got {jb_raw['nframes']}"
        jb_entries = [dict(name=info.filename, size=info.file_size) for info in z_jb.infolist()]

        packer = ArenaPacker()
        t_head = packer.add_tex_bytes(read_pk3_member(z_jb, z_bako, "progs/john_bird_head.png"), max_dim=1024, jpeg_q=91)
        t_hair = packer.add_tex_bytes(read_pk3_member(z_jb, z_bako, "progs/john_bird_hair.png"), max_dim=512, jpeg_q=90)
        t_wing_hawk = packer.add_tex_bytes(read_pk3_member(z_jb, z_bako, "progs/john_bird_wings.png"), max_dim=1024, jpeg_q=89)
        t_wing_hurt = packer.add_tex_bytes(read_pk3_member(z_jb, z_bako, "progs/john_bird_wings_hurt.png"), max_dim=1024, jpeg_q=88)
        t_wing_white = packer.add_tex_bytes(read_pk3_member(z_jb, z_bako, "progs/john_bird_wings_white.png"), max_dim=1024, jpeg_q=88)

        surf_mats = {
            "head":        dict(tex=t_head, roughness=0.62, spec=0.28),
            "hair_breezy": dict(tex=t_hair, roughness=0.38, spec=0.56),
            "wings_bird":  dict(tex=t_wing_hawk, altTex=t_wing_white, hurtTex=t_wing_hurt, roughness=0.52, spec=0.36),
        }

        final_model = pack_md3_dict(packer, jb_raw, surf_mats)

        feather_bytes = read_pk3_member(z_jb, z_bako, "progs/john_bird_feather.md3")
        feather_raw = read_md3_bytes(feather_bytes, label="progs/john_bird_feather.md3")
        feather_dict = pack_md3_dict(packer, feather_raw, {"feather": dict(tex=t_wing_hawk, roughness=0.52, spec=0.32)})

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
            sfx_out[key] = packer.add_bytes(compact_wav_bytes(read_pk3_member(z_jb, z_bako, rel_p), 16000))

        voices_out = []
        for vid, quote in VOICE_QUOTES:
            voices_out.append(dict(
                id=vid,
                quote=quote,
                buf=packer.add_bytes(compact_wav_bytes(read_pk3_member(z_jb, z_bako, f"sound/john_bird/{vid}.wav"), 16000)),
            ))
    finally:
        z_bako.close()
        z_jb.close()

    raw_arena = bytes(packer.buf)
    gz_arena = gzip.compress(raw_arena, compresslevel=9, mtime=0)
    print(
        f"Final Arena (164f shipped john_bird_head.md3 + Feather + {len(sfx_out)} SFX + {len(voices_out)} Voices): "
        f"{len(raw_arena)/1e6:.2f} MB raw -> {len(gz_arena)/1e6:.2f} MB gzipped"
    )

    artifacts = dict(
        pk3Name="zz_johnbird.pk3",
        pk3Size=os.path.getsize(JB_PK3),
        pk3Sha256=file_sha256(JB_PK3),
        pk3Entries=jb_entries,
        progsSize=os.path.getsize(PROGS_DAT),
        progsSha256=file_sha256(PROGS_DAT),
        lnoSize=os.path.getsize(PROGS_LNO) if os.path.isfile(PROGS_LNO) else 0,
        lnoSha256=file_sha256(PROGS_LNO) if os.path.isfile(PROGS_LNO) else "",
    )

    payload = dict(
        textures=packer.tex_list,
        model=final_model,
        feather=feather_dict,
        winners=WINNERS,
        audio=dict(sfx=sfx_out, voices=voices_out),
        artifacts=artifacts,
        binGz=base64.b64encode(gz_arena).decode("ascii"),
    )

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    marker = "/*__JBIRD_FINAL_DATA__*/null"
    assert marker in tpl, f"Missing marker {marker} in {TEMPLATE}"
    html = tpl.replace(marker, json.dumps(payload, separators=(",", ":")), 1)

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote Final Shipped Update HTML: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
