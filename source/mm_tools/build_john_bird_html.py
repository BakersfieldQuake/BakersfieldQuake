"""Pack 'progs/john_bird_head.md3', 'progs/john_bird_feather.md3', textures (intact, white,
and battle-scorched 3-4 rocket plumage), mastered wing-flapping + random 'John' audio clips,
breakdown cards, and multi-angle showcase tiles into a 100% self-contained single-file
WebGL2 3D Inspector & Playable Fast-Flight / 5-Rocket Shootdown Showcase HTML page:
  G:/Quake/Combat/BakersfieldQuake/john_bird_head.html
"""
import base64
import gzip
import io
import json
import math
import os
import sys
import wave

import numpy as np
from PIL import Image, ImageOps
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3lib

ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(HERE, "out", "john_bird")
PROGS_DIR = os.path.join(ROOT_DIR, "progs")
SND_DIR = os.path.join(ROOT_DIR, "sound", "john_bird")
TEMPLATE = os.path.join(HERE, "john_bird_head.template.html")
OUT_HTML = os.path.join(ROOT_DIR, "john_bird_head.html")


def img_to_data_uri(im, w=420, h=300, quality=88):
    thumb = ImageOps.fit(im.convert("RGB"), (w, h), method=Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    thumb.save(bio, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def compact_wav_bytes(wav_path, target_sr=16000):
    """Read 22050 Hz mono 16-bit WAV and compact to 16000 Hz 16-bit mono WAV for tiny embedded WebAudio."""
    with wave.open(wav_path, "rb") as w:
        sr, ch, sw, nf = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(nf)
    arr = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    if ch > 1:
        arr = arr.reshape(-1, ch).mean(axis=1)
    if sr != target_sr:
        g = math.gcd(sr, target_sr)
        arr = signal.resample_poly(arr, target_sr // g, sr // g)
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

    def add_tex_file(self, path, max_dim=1024, jpeg_q=91):
        im = Image.open(path).convert("RGB")
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


def pack_md3(packer, md3_path, surf_mats):
    m = md3lib.read(md3_path)
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


def pack_audio(packer):
    sfx_names = ["flap1", "flap2", "flap3", "flap4", "takeoff", "swoop", "feather_hit", "shootdown", "jv_hurt"]
    sfx_out = {}
    for k in sfx_names:
        p = os.path.join(SND_DIR, f"{k}.wav")
        sfx_out[k] = packer.add_bytes(compact_wav_bytes(p, 16000))

    manifest_p = os.path.join(OUT_DIR, "voice_manifest.json")
    manifest = json.load(open(manifest_p, "r", encoding="utf-8"))
    voices_out = []
    for item in manifest:
        p = os.path.join(SND_DIR, item["file"])
        voices_out.append(dict(
            id=item["file"].replace(".wav", ""),
            quote=item["quote"],
            duration=item["duration"],
            buf=packer.add_bytes(compact_wav_bytes(p, 16000)),
        ))
    return dict(sfx=sfx_out, voices=voices_out)


def build_breakdown_cards():
    src_im = Image.open(os.path.join(OUT_DIR, "uploaded_head_greenscreen.jpg")).convert("RGB")
    src_crop = src_im.crop((290, 56, 725, 476))
    hair_tile = Image.open(os.path.join(OUT_DIR, "t1_closeup_hair.png")).convert("RGB")
    wing_im = Image.open(os.path.join(OUT_DIR, "john_bird_wings.png")).convert("RGB")
    hurt_im = Image.open(os.path.join(PROGS_DIR, "john_bird_wings_hurt.png")).convert("RGB")

    return [
        dict(
            step="Layer 1 · 3D Head & 64 Breezy Hair Locks",
            title="7,832 Verts / 14,560 Tris / 72 Frames",
            desc="Chroma-keyed portrait reconstructed into a 3D skull with 64 wind-swept flapping hair locks (swept bangs, crown plumes, side tufts & nape) + live Wind Gust control.",
            uri=img_to_data_uri(hair_tile, 420, 300),
        ),
        dict(
            step="Layer 2 · Fast Flyable Quake Vehicle",
            title="940 u/s Cruise · 1,460 u/s Falcon Swoop",
            desc="Mount perched Winged John with H (impulse 86) or summon & fly anywhere with P (impulse 98). Full 3D mouse steering, aerodynamic turn banking, climb boost & dive-ram!",
            uri=img_to_data_uri(src_crop, 420, 300),
        ),
        dict(
            step="Layer 3 · Flapping & Random 'John' Audio",
            title="Synced Wingbeats + 14 Iconic John Clips",
            desc="4 organic wing-flap variations synced to climb/cruise/hover cadence on CHAN_BODY while random 'John' voice lines ('Hmm... I'm floating!', 'Do you have hairspray?') play on CHAN_VOICE!",
            uri=img_to_data_uri(wing_im, 420, 300),
        ),
        dict(
            step="Layer 4 · Exact 5-Rocket Shootdown",
            title="500 HP · Scorched Plumage · 3D Feathers",
            desc="Survives 4 direct rockets (shedding 3D john_bird_feather.md3 plumes & switching to scorched ember wings at <=200 HP) and explodes on the exact 5th rocket!",
            uri=img_to_data_uri(hurt_im, 420, 300),
        ),
    ]


def build_angle_cards():
    specs = [
        ("t0_hero_flap.png",    "3/4 Cruising Wingbeat",          0, math.radians(28),  math.radians(14), 138.0, 48.0),
        ("t1_closeup_hair.png", "Close-Up: Breezy Flapping Hair", 0, math.radians(16),  math.radians(9),   66.0, 51.0),
        ("t2_side_profile.png", "Side Profile: 3D Nose & Wing",   0, math.radians(-72), math.radians(14), 134.0, 48.0),
        ("t3_rear_roots.png",   "Rear Skull & Feathered Roots",   0, math.radians(152), math.radians(18), 138.0, 48.0),
        ("t4_upstroke.png",     "Feathered Upstroke Recovery",    0, math.radians(32),  math.radians(15), 138.0, 48.0),
        ("t5_soar_glide.png",   "Windy Thermal Soar / Glide",     1, math.radians(26),  math.radians(20), 148.0, 49.0),
        ("t6_hover_scull.png",  "Rapid Hover & Wild Breeze",      2, math.radians(34),  math.radians(15), 138.0, 48.0),
        ("t7_perch_fold.png",   "Folded-Wing Perch + Breeze",     4, math.radians(34),  math.radians(14),  90.0, 35.0),
    ]
    cards = []
    for fn, lbl, clip_i, az, el, dist, tz in specs:
        im = Image.open(os.path.join(OUT_DIR, fn)).convert("RGB")
        cards.append(dict(
            label=lbl,
            clipIdx=clip_i,
            az=round(az, 4),
            el=round(el, 4),
            dist=dist,
            tgtZ=tz,
            uri=img_to_data_uri(im, 420, 340, quality=87),
        ))
    return cards


def main():
    md3_p = os.path.join(PROGS_DIR, "john_bird_head.md3")
    feather_p = os.path.join(PROGS_DIR, "john_bird_feather.md3")
    assert os.path.isfile(md3_p), f"Missing {md3_p}"
    assert os.path.isfile(feather_p), f"Missing {feather_p}"

    packer = ArenaPacker()
    t_head = packer.add_tex_file(os.path.join(PROGS_DIR, "john_bird_head.png"), max_dim=1024, jpeg_q=92)
    t_hair = packer.add_tex_file(os.path.join(PROGS_DIR, "john_bird_hair.png"), max_dim=512, jpeg_q=91)
    t_wing_hawk = packer.add_tex_file(os.path.join(PROGS_DIR, "john_bird_wings.png"), max_dim=1024, jpeg_q=90)
    t_wing_white = packer.add_tex_file(os.path.join(OUT_DIR, "john_bird_wings_white.png"), max_dim=1024, jpeg_q=89)
    t_wing_hurt = packer.add_tex_file(os.path.join(PROGS_DIR, "john_bird_wings_hurt.png"), max_dim=1024, jpeg_q=89)

    surf_mats = {
        "head":        dict(tex=t_head, roughness=0.62, spec=0.28),
        "hair_breezy": dict(tex=t_hair, roughness=0.38, spec=0.56),
        "wings_bird":  dict(tex=t_wing_hawk, altTex=t_wing_white, hurtTex=t_wing_hurt, roughness=0.52, spec=0.36),
    }

    model_dict = pack_md3(packer, md3_p, surf_mats)
    feather_dict = pack_md3(packer, feather_p, {"feather": dict(tex=t_wing_hawk, roughness=0.52, spec=0.32)})
    audio_dict = pack_audio(packer)

    raw_arena = bytes(packer.buf)
    gz_arena = gzip.compress(raw_arena, compresslevel=9)
    print(f"Binary arena (MD3 + Feather + 23 WAVs): {len(raw_arena)/1e6:.2f} MB raw -> {len(gz_arena)/1e6:.2f} MB gzipped")

    payload = dict(
        textures=packer.tex_list,
        model=model_dict,
        feather=feather_dict,
        audio=audio_dict,
        breakdown=build_breakdown_cards(),
        angles=build_angle_cards(),
        binGz=base64.b64encode(gz_arena).decode("ascii"),
    )

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    marker = "/*__JBIRD_DATA__*/null"
    assert marker in tpl, f"Missing marker {marker}"
    html = tpl.replace(marker, json.dumps(payload, separators=(",", ":")), 1)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote self-contained 3D HTML showcase: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
