r"""Validates all 4 Quake Sky-Vehicle MD3s and builds G:\Quake\Combat\BakersfieldQuake\sky_vehicle_vote.html:
A 100% self-contained, offline WebGL2 3D Sky-Vehicle Voting Studio packing the exact 56-frame Quake .md3 files
(skyveh_v1.md3 .. skyveh_v4.md3), sRGB + additive glow textures, and 4 source-video reference thumbnails.

Usage:
    python3.13 source/mm_tools/build_sky_vehicle_vote_html.py
"""
import base64
import gzip
import io
import json
import os
import struct
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")
OUT_DIR = os.path.join(HERE, "out", "skyveh")
TEMPLATE = os.path.join(HERE, "sky_vehicle_vote.template.html")
OUT_HTML = os.path.join(MOD, "sky_vehicle_vote.html")

UPLOAD_DIR = r"C:\Users\qxdc\.gemini\antigravity\brain\7eaea46a-2e55-469f-9e43-8368b8dfe4ff\.user_uploaded"

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import md3lib


def validate_quake_assets():
    """Verifies binary IDP3 v15 compliance, surface vertex/tri caps, coordinate bounds, skin/shader paths, and Lie_Rest z=0."""
    print("1. Validating Quake MD3 / Skin / Shader / Texture integrity...", flush=True)
    req_pngs = [
        "veh_van_tex.png",
        "veh_van_tex_glow.png",
        "skyveh_bigears.png",
        "skyveh_pinklady.png",
        "mmw_chrome_axle.png",
        "mmw_wheel.png",
        "skyveh_fx.png",
    ]
    for fn in req_pngs:
        p = os.path.join(PROGS, fn)
        assert os.path.isfile(p), f"Missing DarkPlaces texture: {p}"

    shader_p = os.path.join(SCRIPTS, "skyveh.shader")
    assert os.path.isfile(shader_p), f"Missing shader file: {shader_p}"
    sh_txt = open(shader_p, "r", encoding="ascii").read()

    for vid in ("v1", "v2", "v3", "v4"):
        md3_p = os.path.join(PROGS, f"skyveh_{vid}.md3")
        skin_p = os.path.join(PROGS, f"skyveh_{vid}.md3_0.skin")
        assert os.path.isfile(md3_p), f"Missing MD3: {md3_p}"
        assert os.path.isfile(skin_p), f"Missing skin: {skin_p}"

        with open(md3_p, "rb") as f:
            hdr = f.read(108)
        ident, ver = struct.unpack("<4si", hdr[:8])
        assert ident == b"IDP3" and ver == 15, f"Bad MD3 header in {md3_p}: {ident}, {ver}"

        m = md3lib.read(md3_p)
        assert m["nframes"] == 56, f"Expected 56 frames in {md3_p}, got {m['nframes']}"
        assert len(m["surfaces"]) == 8, f"Expected 8 surfaces in {md3_p}"

        solid_z44 = []
        for s in m["surfaces"]:
            nv, nt = len(s["st"]), len(s["tris"])
            assert 0 < nv <= 4096, f"Surface {s['name']} nv={nv} exceeds Quake MD3 4096 cap!"
            assert 0 < nt <= 8192, f"Surface {s['name']} nt={nt} exceeds Quake MD3 8192 cap!"
            assert s["shader"] in sh_txt, f"Shader {s['shader']} missing from scripts/skyveh.shader!"
            all_v = np.asarray([fr[0] for fr in s["frames"]], dtype=np.float32)
            all_n = np.asarray([fr[1] for fr in s["frames"]], dtype=np.float32)
            assert np.isfinite(all_v).all() and np.isfinite(all_n).all(), f"NaN/Inf in {md3_p}:{s['name']}"
            assert np.max(np.abs(all_v)) < 511.5, f"MD3 int16 overflow risk in {md3_p}:{s['name']}"
            if s["name"] != "thruster_fx":
                solid_z44.append(float(all_v[44, :, 2].min()))

        z_min_lie = min(solid_z44)
        assert abs(z_min_lie) < 0.05, f"{md3_p} Lie_Rest frame 44 z_min={z_min_lie:.3f} (expected ~0.0)"
        print(f"   [OK] skyveh_{vid}.md3 : IDP3 v15, 56 frames, 8 surfs, Lie_Rest z_min={z_min_lie:.3f}", flush=True)


def extract_video_thumbnails():
    """Extracts 4 crisp thumbnails from the 4 uploaded .mp4 videos (and caches them in OUT_DIR)."""
    os.makedirs(OUT_DIR, exist_ok=True)
    specs = [
        ("media_1793417816004_653d9c84.mp4", 28, "src_thumb_1.jpg",
         "Video 1 · Chrome Shaft & Tires", "Bullet shaft, cross-axle & twin pneumatic wheels"),
        ("media_1793417816011_73e25749.mp4", 35, "src_thumb_2.jpg",
         "Video 2 · Ram ProMaster Van", "White high-roof walk-in cargo van & open barn doors"),
        ("media_1793417816011_5c97eac8.mp4", 8,  "src_thumb_3.jpg",
         "Video 3 · 3D Hot-Pink V-Arm Lady", "Buoyant twin spheres, raised V-arms & pink ribbons"),
        ("media_1793417816018_5b5f0a16.mp4", 12, "src_thumb_4.jpg",
         "Video 4 · Giant-Eared 3D Head", "Shocked floating head with articulated ear-wings"),
    ]
    out = []
    for mp4_name, frame_idx, cache_jpg, title, sub in specs:
        cache_p = os.path.join(OUT_DIR, cache_jpg)
        mp4_p = os.path.join(UPLOAD_DIR, mp4_name)
        if os.path.isfile(mp4_p):
            cap = cv2.VideoCapture(mp4_p)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, bgr = cap.read()
            cap.release()
            if ok and bgr is not None:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                im = Image.fromarray(rgb)
                # Center-crop 4:3 aspect and resize to 220x165
                w, h = im.size
                tgt_asp = 4.0 / 3.0
                if w / float(h) > tgt_asp:
                    nw = int(round(h * tgt_asp))
                    x0 = (w - nw) // 2
                    im = im.crop((x0, 0, x0 + nw, h))
                else:
                    nh = int(round(w / tgt_asp))
                    y0 = max(0, int((h - nh) * 0.35))
                    im = im.crop((0, y0, w, y0 + nh))
                im = im.resize((220, 165), Image.Resampling.LANCZOS)
                im.save(cache_p, "JPEG", quality=88, optimize=True)
        assert os.path.isfile(cache_p), f"Missing thumbnail {cache_p}"
        b64 = base64.b64encode(open(cache_p, "rb").read()).decode("ascii")
        out.append(dict(title=title, sub=sub, uri=f"data:image/jpeg;base64,{b64}"))
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

    def add_tex_file(self, path, max_dim=1024, jpeg_q=88, force_png=False):
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


def pack_sky_vehicle_md3(packer, md3_path, surf_mats, meta):
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
            # Use cruise frame 0 + lie frame 44 to compute representative bounding box
            solid_pts.append(all_v[0])
            solid_pts.append(all_v[44])

        # Exact 1/64-unit Quake MD3 precision + lossless modular frame-delta encoding for ~7x smaller gzip!
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
            glowTex=mat.get("glowTex", -1),
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

    print("2. Extracting 4 source-video reference thumbnails...", flush=True)
    sources = extract_video_thumbnails()

    print("3. Packing shared WebGL2 textures & 4 animated 56-frame MD3s...", flush=True)
    packer = ArenaPacker()
    t_van = packer.add_tex_file(os.path.join(HERE, "out", "vehicles", "veh_van_atlas.png"), max_dim=1024, jpeg_q=88)
    t_van_glow = packer.add_tex_file(os.path.join(PROGS, "veh_van_tex_glow.png"), max_dim=512, jpeg_q=85)
    t_bigears = packer.add_tex_file(os.path.join(OUT_DIR, "bigears_srgb.png"), max_dim=1024, jpeg_q=88)
    t_pinklady = packer.add_tex_file(os.path.join(OUT_DIR, "pinklady3d_srgb.png"), max_dim=1024, jpeg_q=90)
    t_chrome = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_chrome_axle.png"), max_dim=512, jpeg_q=90)
    t_wheel = packer.add_tex_file(os.path.join(HERE, "out", "megaman_weapon", "mmw_wheel.png"), max_dim=512, jpeg_q=90)
    t_fx = packer.add_tex_file(os.path.join(OUT_DIR, "skyveh_fx_srgb.png"), max_dim=256, force_png=True)

    surf_mats = {
        "progs/skyveh_van":      dict(tex=t_van, glowTex=t_van_glow, metallic=0.14, roughness=0.42, spec=0.45),
        "progs/skyveh_bigears":  dict(tex=t_bigears, metallic=0.05, roughness=0.62, spec=0.25),
        "progs/skyveh_pinklady": dict(tex=t_pinklady, metallic=0.06, roughness=0.52, spec=0.34),
        "progs/skyveh_chrome":   dict(tex=t_chrome, metallic=0.78, roughness=0.18, spec=0.92),
        "progs/skyveh_wheel":    dict(tex=t_wheel, metallic=0.12, roughness=0.64, spec=0.30),
        "progs/skyveh_fx":       dict(tex=t_fx, unlit=True, additive=True),
    }

    version_metas = [
        dict(
            id="v1",
            badge="VERSION 1",
            title="The Ear-nithopter Sky-Galleon",
            file="progs/skyveh_v1.md3",
            desc="Classic dirigible sky-gunship: ProMaster gondola with dorsal giant flapping ear-wings, 3D Pink Lady figurehead gripping twin chrome bowsprits, and a forward chin-mounted chrome bullet pitot-lance with tilting VTOL hover-wheels.",
            fusion=[
                ("Video 1 (Chrome/Tires)", "Forward chin pitot-cannon & tilting VTOL hover/landing wheels"),
                ("Video 2 (Cargo Van)",    "Airship gondola w/ folding DeLorean wheels & rear ion barn-doors"),
                ("Video 3 (Pink Lady)",    "Galleon prow figurehead bracing twin chrome bowsprit booms"),
                ("Video 4 (Big-Ears)",     "Giant dorsal roof turret flapping ear-wings (droops when lying)"),
            ],
            chips=["V1 Dorsal Ear-Wings", "V1 Prow Figurehead", "V1 Chin Tilt-Wheels", "V1 Open-Door Ion Bay"],
        ),
        dict(
            id="v2",
            badge="VERSION 2",
            title="The Valkyrie V-22 Tilt-Rotor",
            file="progs/skyveh_v2.md3",
            desc="Heavy military assault dropship: twin wingtip V-22 Osprey chrome nacelles spinning giant white-dish pneumatic-tire prop-rotors that tilt from vertical hover to turbo forward flight, dorsal Atlas Pink Lady rigging, and flapping Big-Ears nose canard.",
            fusion=[
                ("Video 1 (Chrome/Tires)", "Wingtip V-22 Osprey tilt-nacelles + dorsal chrome turbine pod"),
                ("Video 2 (Cargo Van)",    "Tactical dropship fuselage w/ rear cargo thruster bay"),
                ("Video 3 (Pink Lady)",    "Dorsal 'Atlas' cupola commander bracing wingtip stay-cables"),
                ("Video 4 (Big-Ears)",     "Armored snub-nose biomechanical radar & flapping dive-canards"),
            ],
            chips=["V2 Osprey Tilt-Rotors", "V2 Nose-Cone Big-Ears", "V2 Dorsal Atlas Lady", "V2 Magenta Nacelle Jets"],
        ),
        dict(
            id="v3",
            badge="VERSION 3",
            title="The Podracer Sky-Chariot & Autogyro",
            file="progs/skyveh_v3.md3",
            desc="High-speed twin-boom sky-chariot + helicopter hybrid: screaming Big-Ears tractor engine & chrome splitter-ram towing the ProMaster chariot on twin chrome booms, while Pink Lady holds a whirling overhead twin-tire autogyro rotor mast!",
            fusion=[
                ("Video 1 (Chrome/Tires)", "Spinning overhead twin-tire helicopter rotor + chin splitter-ram"),
                ("Video 2 (Cargo Van)",    "Towed sky-chariot cabin w/ open rear cargo afterburners"),
                ("Video 3 (Pink Lady)",    "Roof-top rotor mast bearer holding spinning gyro yoke"),
                ("Video 4 (Big-Ears)",     "Forward Podracer screaming tractor-pod w/ flapping ear-wings"),
            ],
            chips=["V3 Helicopter Tire-Rotor", "V3 Podracer Tow-Head", "V3 Chin Chrome Lance", "V3 Cyan Rotor Halo"],
        ),
        dict(
            id="v4",
            badge="VERSION 4",
            title="The Biomech Mecha-Wyvern",
            file="progs/skyveh_v4.md3",
            desc="Apex sky-dragon boss rig: van barn-doors re-hinged on the roof as flaring white Beetle Elytra wing-shells (folding flat when lying!), arched chrome dragon neck with Big-Ears wyvern head, Siren grille prow, and scorpion tail-rotor stinger!",
            fusion=[
                ("Video 1 (Chrome/Tires)", "Arched scorpion stinger tail-boom w/ whirling twin tail-wheels"),
                ("Video 2 (Cargo Van)",    "Armored thorax w/ barn-doors flaring as white Beetle Wing-Shells"),
                ("Video 3 (Pink Lady)",    "Harpy/Siren twin-core front grille prow framing cab windshield"),
                ("Video 4 (Big-Ears)",     "Banking dragon-neck Wyvern head w/ giant flapping ear-wings"),
            ],
            chips=["V4 Beetle Wing-Shells", "V4 Dragon-Neck Head", "V4 Scorpion Tail-Rotor", "V4 Siren Grille Prow"],
        ),
    ]

    models_out = []
    for meta in version_metas:
        md3_p = os.path.join(PROGS, f"skyveh_{meta['id']}.md3")
        models_out.append(pack_sky_vehicle_md3(packer, md3_p, surf_mats, meta))

    raw_bytes = bytes(packer.buf)
    gz_bytes = gzip.compress(raw_bytes, compresslevel=6)
    bin_gz_b64 = base64.b64encode(gz_bytes).decode("ascii")
    print(f"   Raw binary arena: {len(raw_bytes) / (1024*1024):.2f} MB -> Gzipped: {len(gz_bytes) / (1024*1024):.2f} MB", flush=True)

    payload = dict(
        sources=sources,
        textures=packer.tex_list,
        models=models_out,
        binGz=bin_gz_b64,
    )

    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    assert "/*__SKYVEH_DATA__*/null" in tpl, "Placeholder missing in template!"
    html = tpl.replace("/*__SKYVEH_DATA__*/null", json.dumps(payload, separators=(",", ":")), 1)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    sz_mb = os.path.getsize(OUT_HTML) / (1024.0 * 1024.0)
    print(f"4. Wrote standalone 3D Voting Studio: {OUT_HTML} ({sz_mb:.2f} MB)", flush=True)


if __name__ == "__main__":
    main()
