"""Master builder for the BakersfieldQuake 3-Version Mega Man Yeet-Gun Voting Studio.

Combines Input 1 (The Mega Man Contraption video) + Input 2 (Heavy Shop-Welded Steel Rotary Launcher Rig photo)
into 3 distinct, funny, playable 37-frame Quake weapon viewmodels + a self-contained WebGL2 Voting & Range HTML:

  - progs/v_mm_yeet_v1.md3 (+ .skin) : V1 'The Whirly-Yeet 9000' (4-Arm Helicopter Centrifuge Sling Cannon)
  - progs/v_mm_yeet_v2.md3 (+ .skin) : V2 'The Nut-Cracker Siege Ballista' (Wheelbarrow-Cam Crossbow & Tailpipe Spanker)
  - progs/v_mm_yeet_v3.md3 (+ .skin) : V3 'The Burnout Pitching-Bazooka' (Twin Counter-Rotating Burnout Tire Railgun)
  - progs/mmy_rig_steel.png, progs/mmy_fx.png, scripts/mm_yeet_gun.shader
  - megaman_yeet_vote.html           : Self-contained 3-card WebGL2 1,650u Firing Range & Voting Studio

Note: Existing progs/v_megaman.md3 is intentionally preserved untouched until the user votes!
"""
import base64
import gzip
import io
import json
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
STAGE_DIR = os.path.join(HERE, "out", "megaman_yeet_vote")
TEMPLATE_HTML = os.path.join(HERE, "megaman_yeet_vote.template.html")
OUT_HTML = os.path.join(MOD, "megaman_yeet_vote.html")

UPLOAD_VIDEO = r"C:/Users/qxdc/.gemini/antigravity/brain/32a2b780-e842-4ac0-9dba-2fd02c89d622/.user_uploaded/media_1793444306332_70974abc.mp4"
UPLOAD_PHOTO = r"C:/Users/qxdc/.gemini/antigravity/brain/32a2b780-e842-4ac0-9dba-2fd02c89d622/.user_uploaded/media_1793444475266_c2cf4b34.png"

sys.path.insert(0, HERE)
import md3lib
from mmw_geometry import build_megaman_payload_parts, transform_megaman_frame
import mmy_geometry
import mmy_textures


MAT_PROPS = {
    "rig_steel":   dict(metallic=0.62, roughness=0.31, spec=0.96, unlit=0, additive=0, twoSided=1),
    "chrome_axle": dict(metallic=0.88, roughness=0.14, spec=1.48, unlit=0, additive=0, twoSided=1),
    "wheel":       dict(metallic=0.10, roughness=0.48, spec=0.46, unlit=0, additive=0, twoSided=1),
    "hand":        dict(metallic=0.20, roughness=0.46, spec=0.45, unlit=0, additive=0, twoSided=1),
    "fx":          dict(metallic=0.00, roughness=0.50, spec=0.00, unlit=1, additive=1, twoSided=1),
}


class BinaryPacker:
    def __init__(self):
        self.buf = bytearray()
        self.tex_map = {}
        self.tex_list = []

    def add_bytes(self, b):
        while len(self.buf) & 3:
            self.buf.append(0)
        off = len(self.buf)
        self.buf.extend(b)
        return [off, len(b)]

    def add_texture(self, key, path, label):
        if key in self.tex_map:
            return self.tex_map[key]
        im = Image.open(path)
        im.load()
        w, h = im.size
        has_alpha = im.mode == "RGBA"
        bio = io.BytesIO()
        im.save(bio, "PNG", optimize=True)
        uri = "data:image/png;base64," + base64.b64encode(bio.getvalue()).decode("ascii")
        idx = len(self.tex_list)
        self.tex_map[key] = idx
        self.tex_list.append(dict(
            key=key,
            label=label,
            file=os.path.basename(path),
            w=w,
            h=h,
            alpha=has_alpha,
            uri=uri,
        ))
        return idx


def check_and_export_md3(model_name, surfs, frame_names, write_progs=True):
    tot_v = 0
    tot_t = 0
    nf = len(frame_names)
    for s in surfs:
        nv = len(s["st"])
        nt = len(s["tris"])
        assert nv <= 4096 and nt <= 8192, f"{model_name}/{s['name']} exceeds MD3 limit: nv={nv}, nt={nt}"
        assert len(s["frames"]) == nf, f"{model_name}/{s['name']} frames={len(s['frames'])} != {nf}"
        for fi, (vv, nn) in enumerate(s["frames"]):
            assert len(vv) == nv and len(nn) == nv
            arr_v = np.asarray(vv, dtype=np.float32)
            arr_n = np.asarray(nn, dtype=np.float32)
            assert np.all(np.isfinite(arr_v)) and np.all(np.isfinite(arr_n)), f"NaN in {model_name}/{s['name']} f{fi}"
            assert np.max(np.abs(arr_v)) < 500.0, f"MD3 int16 overflow risk in {model_name}/{s['name']} f{fi}"
        tot_v += nv
        tot_t += nt

    stage_md3 = os.path.join(STAGE_DIR, f"{model_name}.md3")
    md3lib.write(stage_md3, dict(name=model_name, surfaces=surfs, nframes=nf))
    # Verify round-trip read via md3lib
    rt = md3lib.read(stage_md3)
    assert rt["nframes"] == nf and len(rt["surfaces"]) == len(surfs)

    skin_lines = [f"{s['name']},{s['shader']}" for s in surfs]
    skin_txt = "\n".join(skin_lines) + "\n"
    with open(stage_md3 + "_0.skin", "w", encoding="ascii", newline="\n") as f:
        f.write(skin_txt)

    if write_progs:
        progs_md3 = os.path.join(MOD, "progs", f"{model_name}.md3")
        shutil.copy2(stage_md3, progs_md3)
        with open(progs_md3 + "_0.skin", "w", encoding="ascii", newline="\n") as f:
            f.write(skin_txt)

    print(f"  [OK] {model_name:18s}: {len(surfs)} surfs, {tot_v:5d} verts, {tot_t:5d} tris, {nf:2d} frames")


def build_flying_megaman_surfaces():
    """16-frame spinning Mega Man world projectile oriented nose-forward (+X) for downrange ballistic flight."""
    mm_parts = build_megaman_payload_parts()
    ca_st, ca_tris = [], []
    vo = 0
    for k in ("bar_axle", "wheel_hw_l", "wheel_hw_r"):
        sp = mm_parts[k]
        ca_st += sp.st
        ca_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    wh_st, wh_tris = [], []
    vo = 0
    for k in ("wheel_l", "wheel_r"):
        sp = mm_parts[k]
        wh_st += sp.st
        wh_tris += [(a + vo, b + vo, c + vo) for (a, b, c) in sp.tris]
        vo += len(sp.verts)

    ca_frames, wh_frames, names = [], [], []
    for i in range(16):
        names.append(f"fly{i + 1}")
        xf = transform_megaman_frame(
            mm_parts,
            spin_deg=i * 22.5,
            bar_pitch_deg=0.0,
            pos=(0.0, 0.0, 0.0),
            scale=1.55,
        )
        ca_frames.append((
            xf["bar_axle"][0] + xf["wheel_hw_l"][0] + xf["wheel_hw_r"][0],
            xf["bar_axle"][1] + xf["wheel_hw_l"][1] + xf["wheel_hw_r"][1],
        ))
        wh_frames.append((
            xf["wheel_l"][0] + xf["wheel_r"][0],
            xf["wheel_l"][1] + xf["wheel_r"][1],
        ))

    return [
        dict(name="megaman_bar", shader="progs/mmw_chrome_axle", mat="chrome_axle", tris=ca_tris, st=ca_st, frames=ca_frames),
        dict(name="megaman_whl", shader="progs/mmw_wheel",       mat="wheel",       tris=wh_tris, st=wh_st, frames=wh_frames),
    ], names


def rig_orbit_center(surfs):
    pts = np.vstack([np.asarray(s["frames"][0][0], dtype=np.float32) for s in surfs if s["name"] not in ("yeet_fx", "hands")])
    mid = 0.5 * (pts.min(axis=0) + pts.max(axis=0))
    return [round(float(c), 2) for c in mid]


def pack_md3_model(packer, tex_ids, model_id, meta, surfs, frame_names):
    nf = len(frame_names)
    surfs_out = []
    tot_v, tot_t = 0, 0

    for s in surfs:
        nv = len(s["st"])
        nt = len(s["tris"])
        tot_v += nv
        tot_t += nt

        uv_arr = np.asarray(s["st"], dtype=np.float32)
        tri_arr = np.asarray(s["tris"], dtype=np.uint16)

        e01 = np.sort(tri_arr[:, [0, 1]], axis=1)
        e12 = np.sort(tri_arr[:, [1, 2]], axis=1)
        e20 = np.sort(tri_arr[:, [2, 0]], axis=1)
        edges = np.unique(np.vstack([e01, e12, e20]), axis=0).astype(np.uint16)

        pos_f = np.zeros((nf, nv, 3), dtype=np.float32)
        nrm_i8 = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            pos_f[fi] = np.asarray(vv, dtype=np.float32)
            nrm_i8[fi] = np.clip(np.round(np.asarray(nn, dtype=np.float32) * 127.0), -127, 127).astype(np.int8)

        mat_k = s["mat"]
        mp = MAT_PROPS[mat_k]
        surfs_out.append(dict(
            name=s["name"],
            mat=mat_k,
            tex=tex_ids[mat_k],
            nv=nv,
            nt=nt,
            ne=len(edges),
            uv=packer.add_bytes(uv_arr.tobytes()),
            tris=packer.add_bytes(tri_arr.tobytes()),
            edges=packer.add_bytes(edges.tobytes()),
            pos=packer.add_bytes(pos_f.tobytes()),
            nrm=packer.add_bytes(nrm_i8.tobytes()),
            metallic=mp["metallic"],
            roughness=mp["roughness"],
            spec=mp["spec"],
            unlit=1 if (s.get("unlit") or mp["unlit"]) else 0,
            additive=1 if (s.get("additive") or mp["additive"]) else 0,
            twoSided=mp.get("twoSided", 1),
        ))

    out = dict(
        id=model_id,
        nf=nf,
        nv=tot_v,
        nt=tot_t,
        nsurfs=len(surfs_out),
        frameNames=frame_names,
        surfaces=surfs_out,
    )
    out.update(meta)
    return out


def make_jpeg_data_uri(pil_im, max_size=(540, 390), quality=86):
    im = pil_im.convert("RGB")
    im.thumbnail(max_size, Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    im.save(bio, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode("ascii")


def build_source_thumbnails():
    sources = []
    # Input 1: Video frame of Mega Man contraption
    if os.path.isfile(UPLOAD_VIDEO):
        cap = cv2.VideoCapture(UPLOAD_VIDEO)
        n_fr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 30)
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(n_fr * 0.35)))
        ok, frame_bgr = cap.read()
        cap.release()
        if ok and frame_bgr is not None:
            im1 = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        else:
            im1 = Image.open( os.path.join(STAGE_DIR, "mmw_wheel.png") )
    else:
        im1 = Image.open(os.path.join(STAGE_DIR, "mmw_wheel.png"))

    sources.append(dict(
        badge="INPUT 1 · AMMO PAYLOAD",
        title="The 'Mega Man' Contraption",
        subtitle="Twin 5-ribbed wheelbarrow tires, white concave rims & chrome torpedo shaft",
        uri=make_jpeg_data_uri(im1),
    ))

    # Input 2: Photo of shop-welded steel rotary launcher rig
    if os.path.isfile(UPLOAD_PHOTO):
        im2 = Image.open(UPLOAD_PHOTO)
    else:
        im2 = Image.open(os.path.join(STAGE_DIR, "mmy_rig_steel.png"))

    sources.append(dict(
        badge="INPUT 2 · LAUNCHER RIG",
        title="Shop-Welded Rotary Steel Rig",
        subtitle="Drum pan + 3 hex bolts, hollow square tubes, giant hex nuts, white nylon pinion & 6-spoke bull gear",
        uri=make_jpeg_data_uri(im2),
    ))
    return sources


def main():
    tmp_old = os.path.join(HERE, "_stage_yeet")
    if os.path.isdir(tmp_old):
        shutil.rmtree(tmp_old, ignore_errors=True)

    os.makedirs(STAGE_DIR, exist_ok=True)
    print("1. Synthesizing procedural welded-rig steel & supersonic FX textures...")
    tex_paths = mmy_textures.ensure_yeet_textures_and_shader(MOD, STAGE_DIR)

    print("2. Building 3 combined 37-frame Quake Yeet-Gun MD3 models...")
    frame_names = mmy_geometry.FRAME_NAMES_37
    v1_surfs, v1_muz = mmy_geometry.build_v1_whirly_yeet()
    v2_surfs, v2_muz = mmy_geometry.build_v2_ballista_yeet()
    v3_surfs, v3_muz = mmy_geometry.build_v3_burnout_bazooka()
    proj_surfs, proj_names = build_flying_megaman_surfaces()

    check_and_export_md3("v_mm_yeet_v1", v1_surfs, frame_names, write_progs=True)
    check_and_export_md3("v_mm_yeet_v2", v2_surfs, frame_names, write_progs=True)
    check_and_export_md3("v_mm_yeet_v3", v3_surfs, frame_names, write_progs=True)
    check_and_export_md3("mmy_proj_preview", proj_surfs, proj_names, write_progs=False)

    print("3. Packing compressed WebGL2 binary buffers & reference thumbnails...")
    packer = BinaryPacker()
    tex_ids = {
        "rig_steel":   packer.add_texture("rig_steel",   tex_paths["rig_steel"],   "Welded Square-Tube, Drum Pan, Gears & Scale"),
        "chrome_axle": packer.add_texture("chrome_axle", tex_paths["chrome_axle"], "Polished Chrome Torpedo Bar & Cross-Axle"),
        "wheel":       packer.add_texture("wheel",       tex_paths["wheel"],       "5-Rib Pneumatic Tire & White Concave Rim"),
        "hand":        packer.add_texture("hand",        tex_paths["hand"],        "Quake Ranger Leather Glove & Bracer"),
        "fx":          packer.add_texture("fx",          tex_paths["fx"],          "Supersonic Mach Ring, Sparks & Burnout Smoke"),
    }

    m1 = pack_md3_model(
        packer, tex_ids, "yeet_v1",
        dict(
            code="V1",
            badge="VERSION 1 · CENTRIFUGE",
            title="The Whirly-Yeet 9000",
            tagline="Overclocked 4-Arm Rotary Helicopter Centrifuge Turret",
            md3File="progs/v_mm_yeet_v1.md3",
            md3Short="v_mm_yeet_v1.md3",
            accent="#ffb454",
            accentRgb=[1.00, 0.71, 0.33],
            sfxKind="v1_whirly",
            fps=13,
            idleRange=[0, 15],
            fireRange=[16, 35],
            launchFrame=19,
            muzzleEye=v1_muz,
            baseVel=[506.0, 0.0, 67.5],
            orbitCenter=rig_orbit_center(v1_surfs),
            orbitDist=21.8,
            orbitAz=2.38,
            orbitEl=0.34,
            presets=[
                ["3/4 Hero Rig",   2.38, 0.34, 19.8],
                ["Top Rotor & Gears", 2.15, 1.18, 21.0],
                ["Muzzle & Scale", 0.32, 0.20, 19.0],
                ["Drum Pan & Bolts", 3.65, -0.18, 20.5],
            ],
            highlights=[
                "Mounts Upload 2's exact <b>circular steel drum pan (3 black-oxide hex bolts)</b>, open-ended <b>hollow square-tube A-frame</b>, giant hex-nut crossbar & <b>4-arm square-tube pinwheel</b> directly in your hands.",
                "<b>White nylon spur pinion + 6-spoked bull gear</b> whip the 4-arm cross into a 360° tornado wind-up while Mega Man hangs off the front rotor fork.",
                "Diagonal trip-rod pops the <b>stainless spring plunger pin</b> at apex speed, centrifugally sling-yeeting Mega Man down the engraved <i>'10m → FRESNO → ORBIT'</i> scale chute!",
            ],
            chips=[
                "V1: 4-Arm Helicopter Centrifuge",
                "V1: Pop-Pin Sling Release",
                "V1: Upright Drum-Pan Turret",
            ],
        ),
        v1_surfs, frame_names,
    )

    m2 = pack_md3_model(
        packer, tex_ids, "yeet_v2",
        dict(
            code="V2",
            badge="VERSION 2 · SIEGE BALLISTA",
            title="The Nut-Cracker Ballista",
            tagline="Wheelbarrow-Cam Compound Crossbow & 'Tailpipe Spanker'",
            md3File="progs/v_mm_yeet_v2.md3",
            md3Short="v_mm_yeet_v2.md3",
            accent="#fb7185",
            accentRgb=[0.99, 0.44, 0.52],
            sfxKind="v2_ballista",
            fps=13,
            idleRange=[0, 15],
            fireRange=[16, 35],
            launchFrame=19,
            muzzleEye=v2_muz,
            baseVel=[522.0, 0.0, 69.0],
            orbitCenter=rig_orbit_center(v2_surfs),
            orbitDist=22.8,
            orbitAz=2.36,
            orbitEl=0.36,
            presets=[
                ["3/4 Siege View",   2.36, 0.36, 20.6],
                ["Top Cams & Cable", 2.05, 1.18, 22.0],
                ["Muzzle & Tires",   0.28, 0.16, 19.5],
                ["Rear Gear Windlass", 3.12, 0.32, 18.5],
            ],
            highlights=[
                "Turns Upload 2's <b>6-spoked bull gear + white nylon pinion + 4-arm capstan</b> into a motorized rear siege windlass hauling back a braided steel bowstring along the ruled steel spine.",
                "Hinged <b>hollow square-tube crossbow limbs</b> mount two horizontal <b>Mega Man wheelbarrow tires as giant compound-bow eccentric cams</b>!",
                "Pulling the diagonal sear rod snaps both tire-cams open, slamming a hazard-striped <b>'TAILPIPE SPANKER'</b> block square into Mega Man's rear rubber cap!",
            ],
            chips=[
                "V2: Wheelbarrow-Tire Compound Cams",
                "V2: 'Tailpipe Spanker' Striker",
                "V2: Bull-Gear Rear Windlass",
            ],
        ),
        v2_surfs, frame_names,
    )

    m3 = pack_md3_model(
        packer, tex_ids, "yeet_v3",
        dict(
            code="V3",
            badge="VERSION 3 · PITCHING BAZOOKA",
            title="The Burnout Pitching-Bazooka",
            tagline="4-Tube Hex-Nut Railgun with Twin Burnout Muzzle Tires",
            md3File="progs/v_mm_yeet_v3.md3",
            md3Short="v_mm_yeet_v3.md3",
            accent="#38bdf8",
            accentRgb=[0.22, 0.74, 0.98],
            sfxKind="v3_burnout",
            fps=13,
            idleRange=[0, 15],
            fireRange=[16, 35],
            launchFrame=19,
            muzzleEye=v3_muz,
            baseVel=[538.0, 0.0, 70.5],
            orbitCenter=rig_orbit_center(v3_surfs),
            orbitDist=22.4,
            orbitAz=2.40,
            orbitEl=0.30,
            presets=[
                ["3/4 Bazooka Cage", 2.40, 0.30, 20.2],
                ["Twin Burnout Muzzle", 0.25, 0.18, 18.8],
                ["Side Bull-Gear Drive", 1.62, 0.12, 19.5],
                ["Top Ruled Rail",   2.10, 1.15, 21.0],
            ],
            highlights=[
                "Welds 4 open-ended <b>hollow square-tube rails</b> through two <b>giant zinc-hex-nut crossbars</b> over an underslung <b>circular steel drum pan</b> magazine.",
                "Side-mounted <b>white nylon pinion + 6-spoked bull gear + 4-arm chopper</b> spin two counter-rotating <b>muzzle wheelbarrow burnout tires</b> at 5,000 RPM.",
                "Trigger rams Mega Man's gleaming chrome torpedo bar between the screaming rubber tires—<b>pinching & spitting him 1,450u downrange</b> in tire smoke & plasma!",
            ],
            chips=[
                "V3: Twin Burnout Muzzle Tires",
                "V3: 4-Tube Hex-Nut Railgun Cage",
                "V3: Side Exposed Bull-Gear Drive",
            ],
        ),
        v3_surfs, frame_names,
    )

    m_proj = pack_md3_model(
        packer, tex_ids, "flying_megaman",
        dict(code="MM", title="Launched Mega Man"),
        proj_surfs, proj_names,
    )

    gz_bytes = gzip.compress(bytes(packer.buf), compresslevel=6)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    print(f"   Binary arena: raw={len(packer.buf)/1e6:.2f} MB -> gzip={len(gz_bytes)/1e6:.2f} MB")

    payload = dict(
        binGz=b64_gz,
        binLen=len(packer.buf),
        sources=build_source_thumbnails(),
        textures=packer.tex_list,
        models=[m1, m2, m3, m_proj],
        projectileModelIndex=3,
    )

    tpl = open(TEMPLATE_HTML, encoding="utf-8").read()
    assert "/*__MMY_DATA__*/null" in tpl, "Missing /*__MMY_DATA__*/null placeholder in template!"
    html_out = tpl.replace("/*__MMY_DATA__*/null", json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"4. Wrote self-contained HTML studio: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
