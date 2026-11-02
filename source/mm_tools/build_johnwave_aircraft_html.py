r"""Validates all John Wave x Mega Man Quake Aircraft MD3s and builds G:\Quake\Combat\BakersfieldQuake\johnwave_aircraft.html:
A 100% self-contained, offline WebGL2 3D Aircraft Hangar, Voice-Horn Soundboard & Voting Studio packing:
  - progs/jw_air_v1.md3 (= progs/jw_aircraft.md3) : F-69 "THE MOUTH-BREATHER"
  - progs/jw_air_v2.md3                           : SR-99 "IN-ONE-EAR"
  - progs/jw_air_v3.md3                           : CH-99 "THE HAIR-ICOPTER"
  - All 72-frame vertex animations (Cruise, Scream Boost, 360 Barrel Roll, VTOL Hover, Landed/Snoring)
  - Real John Wave voice clips (sound/john/jwthrow.wav, sound/funny/waveofhair.wav, sound/john/jv00..jv04.wav)

Usage:
    python3.13 source/mm_tools/build_johnwave_aircraft_html.py
"""
import base64
import gzip
import io
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")
SOUND = os.path.join(MOD, "sound")
OUT_DIR = os.path.join(HERE, "out", "jw_air")
TEMPLATE = os.path.join(HERE, "johnwave_aircraft.template.html")
OUT_HTML = os.path.join(MOD, "johnwave_aircraft.html")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import md3lib


def validate_quake_assets():
    print("1. Validating Quake MD3 / Skin / Shader / Texture integrity...", flush=True)
    req_pngs = [
        "jw_air_scream.png",
        "jw_air_calm.png",
        "jw_air_fedora.png",
        "jw_air_wave.png",
        "jw_air_fx.png",
        "mmw_chrome_axle.png",
        "mmw_wheel.png",
    ]
    for fn in req_pngs:
        p = os.path.join(PROGS, fn)
        assert os.path.isfile(p), f"Missing DarkPlaces texture: {p}"

    shader_p = os.path.join(SCRIPTS, "jw_aircraft.shader")
    assert os.path.isfile(shader_p), f"Missing shader file: {shader_p}"
    sh_txt = open(shader_p, "r", encoding="ascii").read()

    for mname in ("jw_aircraft", "jw_air_v1", "jw_air_v2", "jw_air_v3"):
        md3_p = os.path.join(PROGS, f"{mname}.md3")
        skin_p = os.path.join(PROGS, f"{mname}.md3_0.skin")
        assert os.path.isfile(md3_p), f"Missing MD3: {md3_p}"
        assert os.path.isfile(skin_p), f"Missing skin: {skin_p}"

        with open(md3_p, "rb") as f:
            hdr = f.read(108)
        ident, ver = struct.unpack("<4si", hdr[:8])
        assert ident == b"IDP3" and ver == 15, f"Bad MD3 header in {md3_p}: {ident}, {ver}"

        m = md3lib.read(md3_p)
        assert m["nframes"] == 72, f"Expected 72 frames in {md3_p}, got {m['nframes']}"
        assert 1 <= len(m["surfaces"]) <= 32, f"Surface count {len(m['surfaces'])} out of MD3 [1..32] bounds!"

        solid_z44 = []
        for s in m["surfaces"]:
            nv, nt = len(s["st"]), len(s["tris"])
            assert 0 < nv <= 4096, f"Surface {s['name']} nv={nv} exceeds Quake MD3 4096 cap!"
            assert 0 < nt <= 8192, f"Surface {s['name']} nt={nt} exceeds Quake MD3 8192 cap!"
            assert s["shader"] in sh_txt, f"Shader {s['shader']} missing from scripts/jw_aircraft.shader!"
            all_v = np.asarray([fr[0] for fr in s["frames"]], dtype=np.float32)
            all_n = np.asarray([fr[1] for fr in s["frames"]], dtype=np.float32)
            assert np.isfinite(all_v).all() and np.isfinite(all_n).all(), f"NaN/Inf in {md3_p}:{s['name']}"
            assert np.max(np.abs(all_v)) < 511.5, f"MD3 int16 overflow risk in {md3_p}:{s['name']}"
            if s["shader"] not in ("progs/jw_air_fx", "progs/jw_air_wave"):
                solid_z44.append(float(all_v[44, :, 2].min()))

        z_min_lie = min(solid_z44)
        assert abs(z_min_lie) < 0.05, f"{md3_p} Lie_Rest frame 44 z_min={z_min_lie:.3f} (expected ~0.0)"
        print(
            f"   [OK] {mname}.md3 : IDP3 v15, 72f, {len(m['surfaces'])} surfs, Lie_Rest z_min={z_min_lie:.3f}",
            flush=True,
        )


def make_thumb_uri(im, w=220, h=165):
    im = im.convert("RGB")
    iw, ih = im.size
    tgt = w / float(h)
    if iw / float(ih) > tgt:
        nw = int(round(ih * tgt))
        x0 = (iw - nw) // 2
        im = im.crop((x0, 0, x0 + nw, ih))
    else:
        nh = int(round(iw / tgt))
        y0 = max(0, int((ih - nh) * 0.35))
        im = im.crop((0, y0, iw, y0 + nh))
    im = im.resize((w, h), Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    im.save(bio, "JPEG", quality=88, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def build_ingredient_thumbnails():
    os.makedirs(OUT_DIR, exist_ok=True)
    out = []

    # 1. Screaming Mane 3D John Wave Head (from verification sheet Row 1 [V2] or jw_scream_srgb)
    chk_p = os.path.join(OUT_DIR, "jw_aircraft_check.png")
    if os.path.isfile(chk_p):
        chk = Image.open(chk_p).convert("RGB")
        im_scr = chk.crop((0, 310, 400, 620))
    else:
        im_scr = Image.open(os.path.join(OUT_DIR, "jw_scream_srgb.png"))
    out.append(dict(
        title="1 · Screaming John Wave 3D Head",
        sub="Used exclusively on V2 SR-99 ear-skewer & ramjets",
        uri=make_thumb_uri(im_scr),
    ))

    # 2. Deadpan Calm Lush-Hair John Wave Portrait (despilled onto dark navy studio bg)
    grn_p = os.path.join(HERE, "out", "chars", "ref", "johnwave_head_green.jpg")
    grn = np.asarray(Image.open(grn_p).convert("RGB"), dtype=np.float32)
    r, g, b = grn[..., 0], grn[..., 1], grn[..., 2]
    bg = (g > r + 22) & (g > b + 22)
    grn[..., 1] = np.minimum(g, np.maximum(r, b))
    grn[bg] = np.array([22.0, 34.0, 56.0], dtype=np.float32)
    im_calm = Image.fromarray(grn.astype(np.uint8), "RGB")
    out.append(dict(
        title="2 · Deadpan Calm John Wave 3D Head",
        sub="100% stoic hull & crew of V1 Biplane + V3 Chinook!",
        uri=make_thumb_uri(im_calm),
    ))

    # 3. Mega Man Chrome Bullet Bar & White-Dish Pneumatic Tires
    mm_thumb_p = os.path.join(HERE, "out", "skyveh", "src_thumb_1.jpg")
    if os.path.isfile(mm_thumb_p):
        im_mm = Image.open(mm_thumb_p)
    else:
        im_mm = Image.open(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png"))
    out.append(dict(
        title="3 · The Mega Man Bar & Dish Tires",
        sub="Chrome bullet cigar, ear-skewer rocket & propeller-beanie rotors",
        uri=make_thumb_uri(im_mm),
    ))

    # 4. Foamy "JOHN WAVE" Ocean Tidal-Wave Surf Ring
    im_wv = Image.open(os.path.join(OUT_DIR, "jw_wave_srgb.png"))
    out.append(dict(
        title="4 · 'John Wave' Ocean Surf Plumes",
        sub="Spinning 3D foamy tidal-wave jet exhaust & rotor hurricanes",
        uri=make_thumb_uri(im_wv),
    ))
    return out


def pack_voice_soundboard():
    specs = [
        (os.path.join(SOUND, "john", "jwthrow.wav"),      '🌊 "JOHN WAVE!"'),
        (os.path.join(SOUND, "funny", "waveofhair.wav"),  '💇 "Wave of Hair!"'),
        (os.path.join(SOUND, "john", "jv00.wav"),         '🎙 Quip #1'),
        (os.path.join(SOUND, "john", "jv01.wav"),         '🎙 Quip #2'),
        (os.path.join(SOUND, "john", "jv02.wav"),         '🎙 Quip #3'),
        (os.path.join(SOUND, "john", "jv04.wav"),         '🎙 Quip #4'),
        (os.path.join(SOUND, "john", "jv07.wav"),         '🎙 Quip #5'),
    ]
    out = []
    for wav_p, label in specs:
        if os.path.isfile(wav_p):
            b64 = base64.b64encode(open(wav_p, "rb").read()).decode("ascii")
            out.append(dict(label=label, uri=f"data:audio/wav;base64,{b64}"))
    return out


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

    def add_tex_file(self, path, max_dim=1024, jpeg_q=89, force_png=False):
        abs_p = os.path.abspath(path)
        if abs_p in self.tex_map:
            return self.tex_map[abs_p]
        im = Image.open(abs_p).convert("RGB")
        w0, h0 = im.size
        if max_dim and max(w0, h0) > max_dim:
            sc = max_dim / float(max(w0, h0))
            im = im.resize((max(1, round(w0 * sc)), max(1, round(h0 * sc))), Image.Resampling.LANCZOS)
        bio = io.BytesIO()
        if force_png:
            im.save(bio, "PNG", optimize=True)
            mime = "image/png"
        else:
            im.save(bio, "JPEG", quality=jpeg_q, optimize=True)
            mime = "image/jpeg"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[abs_p] = idx
        self.tex_list.append(dict(uri=uri, w=im.size[0], h=im.size[1]))
        return idx


def build_wire_edges(tri_arr):
    e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
    e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
    e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
    return np.unique(np.vstack([e01, e12, e20]), axis=0).astype("<u2")


def pack_aircraft_md3(packer, md3_path, surf_mats, meta):
    m = md3lib.read(md3_path)
    nf = m["nframes"]
    surfs_out = []
    tot_v, tot_t = 0, 0
    solid_pts = []

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

        mat = surf_mats[s["shader"]]
        if not mat.get("additive", False):
            solid_pts.append(all_v[0])
            solid_pts.append(all_v[44])

        pos_scale = 1.0 / 64.0
        pos_u16 = np.zeros((nf, nv, 4), dtype="<i2")
        pos_u16[:, :, :3] = np.clip(np.round(all_v * 64.0), -32767, 32767).astype("<i2")
        dpos = pos_u16.copy()
        dpos[1:] = ((pos_u16[1:].astype(np.int32) - pos_u16[:-1].astype(np.int32)) & 0xFFFF).astype("<u2").view("<i2")

        n_len = np.maximum(np.linalg.norm(all_n, axis=2, keepdims=True), 1e-8)
        nrm_i8 = np.zeros((nf, nv, 4), dtype="<i1")
        nrm_i8[:, :, :3] = np.clip(np.round((all_n / n_len) * 127.0), -127, 127).astype("<i1")
        dnrm = nrm_i8.copy()
        dnrm[1:] = ((nrm_i8[1:].astype(np.int32) - nrm_i8[:-1].astype(np.int32)) & 0xFF).astype("<u1").view("<i1")

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
            metallic=mat.get("metallic", 0.15),
            roughness=mat.get("roughness", 0.50),
            spec=mat.get("spec", 0.40),
            unlit=1 if mat.get("unlit") else 0,
            additive=1 if mat.get("additive") else 0,
        ))

    pts_cat = np.vstack(solid_pts)
    bmin = pts_cat.min(axis=0).round(2).tolist()
    bmax = pts_cat.max(axis=0).round(2).tolist()

    out = dict(nf=nf, nv=tot_v, nt=tot_t, bbox=[bmin, bmax], surfaces=surfs_out)
    out.update(meta)
    return out


def main():
    validate_quake_assets()

    print("2. Building ingredient thumbnails & packing John Wave voice clips...", flush=True)
    sources = build_ingredient_thumbnails()
    sounds = pack_voice_soundboard()
    print(f"   Packed {len(sounds)} embedded .wav voice clips.", flush=True)

    print("3. Packing sRGB textures & 3 ridiculous 72-frame Quake MD3 aircraft...", flush=True)
    packer = ArenaPacker()
    t_scream = packer.add_tex_file(os.path.join(OUT_DIR, "jw_scream_srgb.png"), max_dim=1024, jpeg_q=90)
    t_calm = packer.add_tex_file(os.path.join(OUT_DIR, "jw_calm_srgb.png"), max_dim=768, jpeg_q=90)
    t_fed = packer.add_tex_file(os.path.join(OUT_DIR, "jw_fedora_srgb.png"), max_dim=512, jpeg_q=92)
    t_chr = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_chrome_axle.png"), max_dim=512, jpeg_q=92)
    t_whl = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png"), max_dim=512, jpeg_q=92)
    t_wav = packer.add_tex_file(os.path.join(OUT_DIR, "jw_wave_srgb.png"), max_dim=256, jpeg_q=90)
    t_fx = packer.add_tex_file(os.path.join(OUT_DIR, "jw_fx_srgb.png"), max_dim=256, force_png=True)

    surf_mats = {
        "progs/jw_air_scream": dict(tex=t_scream, metallic=0.05, roughness=0.62, spec=0.28),
        "progs/jw_air_calm":   dict(tex=t_calm,   metallic=0.05, roughness=0.60, spec=0.28),
        "progs/jw_air_fedora": dict(tex=t_fed,    metallic=0.04, roughness=0.76, spec=0.24),
        "progs/jw_air_chrome": dict(tex=t_chr,    metallic=0.88, roughness=0.17, spec=0.96),
        "progs/jw_air_wheel":  dict(tex=t_whl,    metallic=0.16, roughness=0.52, spec=0.42),
        "progs/jw_air_wave":   dict(tex=t_wav,    unlit=True),
        "progs/jw_air_fx":     dict(tex=t_fx,     unlit=True, additive=True),
    }

    specs = [
        dict(
            id="jw_air_v1",
            badge="AIRCRAFT V1 · FLAGSHIP",
            title='F-69 "The Mouth-Breather" Biplane',
            file="progs/jw_aircraft.md3 (jw_air_v1.md3)",
            desc="100% Screaming-Head-Free Red-Fedora Edition! Giant Skeptical-Eyebrow, Bullfrog-Cheek-Puffing Bobblehead John bounces on a 24k-gold coil neck-spring wearing a jauntily tilted Crimson-Red Felt Fedora (with black silk ribbon, gold buckle & ivory feather!), a spinning Gold Tire-Monocle, curled Dalí Handlebar Mustache tire-props, angry-bull Nostril Steam Jets, and a lit Mega-Man Cigar puffing 3D 'John Wave' smoke rings—flanked by flapping bird-wings with Mini-Red-Fedora Henchmen Johns & a pop-out Cuckoo-Clock Man-Bun John!",
            fusion=[
                ["Red Fedora", "Jauntily cocked crimson felt fedora with pinched crown, black ribbon, gold buckle & 'M'Biplane' tip nod"],
                ["Monocle & Cigar", "Spinning gold Tire-Monocle + pumping 'Rock' eyebrow + lit Mega-Man cigar puffing 3D 'John Wave' smoke rings"],
                ["Fedora Gang", "Bird-flapping WWI biplane wings ridden by twin Mini-Red-Fedora Tire-Shades Henchmen Johns"],
                ["Cuckoo Man-Bun", "Rear pop-out Cuckoo-Clock Mini-John in a Red Fedora + tire-beanie & angry-bull nostril steam jets"],
            ],
            chips=[
                "V1 Jaunty Crimson-Red Fedora",
                "V1 Gold Tire-Monocle & Rock Brow",
                "V1 Cigar Puffing 3D Wave Smoke Rings",
                "V1 Mini-Red-Fedora Wing Henchmen",
            ],
        ),
        dict(
            id="jw_air_v2",
            badge="AIRCRAFT V2 · SUPERSONIC",
            title='SR-99 "In-One-Ear" Rocket Jet',
            file="progs/jw_air_v2.md3",
            desc="A Mach-5 Mega-Man Chrome Bullet Rocket spearing straight out of Giant John's screaming mouth AND skewering him ear-to-ear with colossal Beats-by-Dre monster tilt-rotor headphone tires, plus twin screaming-head ramjets slung under swept chrome delta-wings!",
            fusion=[
                ["Ear-Skewer", "Colossal Mega-Man cross-axle pierces in one ear & out the other"],
                ["Headphone Rotors", "71-unit white-dish monster tires tilt from turbofans to rolling truck wheels"],
                ["Wing Ramjets", "2 smaller Screaming John heads chomping air under swept chrome delta-wings"],
                ["Tail-Gunner", "Deadpan Calm John facing backward in rear tub with zero emotion"],
            ],
            chips=[
                "V2 Ear-Skewered Headphone Tires",
                "V2 Underwing Screaming Ramjets",
                "V2 Mouth-Bursting Rocket Nose",
                "V2 Backward Deadpan Tail-Gunner",
            ],
        ),
        dict(
            id="jw_air_v3",
            badge="AIRCRAFT V3 · TANDEM CHOPPER",
            title='CH-99 "The Hair-icopter" Chinook',
            file="progs/jw_air_v3.md3",
            desc="100% Screaming-Head-Free! A two-faced Push-Me-Pull-You flying chrome broomstick featuring THREE stone-cold Deadpan Lush-Hair Johns (Front Bow, Rear Stern & Midship Tire-Shades Biker) with twin Mega-Man Propeller-Beanie Helicopter Rotors spinning out of their hairdos!",
            fusion=[
                ["Beanie Rotors", "Vertical Mega-Man bullet masts + horizontal tire-blades whirling out of both hairdos"],
                ["Triple Deadpan", "Front & Rear Giant Deadpan Lush-Hair Johns staring both ways with zero emotion"],
                ["Midship Biker", "Stoic Mini-John in spinning tire-goggles gripping chrome ape-hanger handlebars"],
                ["Surf Hurricanes", "Twin spinning foamy 'John Wave' ocean surf halos & quad pontoon wheels"],
            ],
            chips=[
                "V3 Triple Stoic Deadpan Johns",
                "V3 Propeller-Beanie Hair Rotors",
                "V3 Tire-Shades Saddle Biker John",
                "V3 Flying Chrome Broomstick",
            ],
        ),
    ]

    models_out = []
    for sp in specs:
        md3_p = os.path.join(PROGS, f"{sp['id']}.md3")
        models_out.append(pack_aircraft_md3(packer, md3_p, surf_mats, sp))

    raw_bytes = bytes(packer.buf)
    gz_bytes = gzip.compress(raw_bytes, compresslevel=6)
    print(f"   Binary arena: {len(raw_bytes)/1e6:.2f} MB raw -> {len(gz_bytes)/1e6:.2f} MB gzipped", flush=True)

    payload = dict(
        sources=sources,
        sounds=sounds,
        textures=packer.tex_list,
        models=models_out,
        binGz=base64.b64encode(gz_bytes).decode("ascii"),
    )

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    marker = "/*__JWAIR_DATA__*/null"
    assert marker in tpl, f"Missing marker {marker} in {TEMPLATE}"
    html = tpl.replace(marker, json.dumps(payload, separators=(",", ":")), 1)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"4. Wrote standalone 3D Hangar & Soundboard HTML: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)", flush=True)


if __name__ == "__main__":
    main()
