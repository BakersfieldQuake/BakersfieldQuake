"""Master builder for the BakersfieldQuake 4-Weapon Mega Man Arsenal & CoD Inspect Studio.

Builds 4 unique 89-frame 3D weapon models shooting the wheeled chrome-bar 'Mega Man' contraption:
  1. progs/v_mm_cannon.md3    (+ .skin + .glb) : V1 'The Broadside Blunder-Cannon' (Cast-Iron & Brass Slotted Cannon)
  2. progs/v_mm_slingshot.md3 (+ .skin + .glb) : V2 'The Wrist-Rocket Y-Slinger'   (Walnut Y-Fork & 4-Band Latex Slingshot)
  3. progs/v_mm_bow.md3       (+ .skin + .glb) : V3 'The Recurve Mega-Bow'         (Carbon Compound/Recurve Bow & Mega-Arrow)
  4. progs/v_mm_handthrow.md3 (+ .skin + .glb) : V4 'Bare-Handed Mega-Chuck'       (Gloved Hand-Held Grip & Overhand Throw)

All 4 models share a unified 89-frame schedule:
  - Frames  0..15 (16f): Idle — Continuous 360° wheel spin + lively contraption bobbling
  - Frames 16..35 (20f): Fire / Launch (frame 19) / Recoil / Reload
  - Frame  36     ( 1f): Empty ('empty1')
  - Frames 37..60 (24f): CoD Inspect A ('Hold Out') — Tilts & turns weapon left/right to admire + flourish
  - Frames 61..88 (28f): CoD Inspect B ('Clean the Bar') — Grabs chrome bar with red shop rag, strokes/cleans it -> ✨ glint!

Note: Existing progs/v_megaman.md3 is preserved untouched!
"""
import base64
import gzip
import io
import json
import os
import shutil
import struct
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
STAGE_DIR = os.path.join(HERE, "out", "megaman_arsenal_4v")
TEMPLATE_HTML = os.path.join(HERE, "megaman_arsenal_4v.template.html")
OUT_HTML = os.path.join(MOD, "megaman_arsenal_4v.html")

UPLOAD_VIDEO = r"C:/Users/qxdc/.gemini/antigravity/brain/7215244e-be93-410f-94c4-5dc7e4bafaa7/.user_uploaded/media_1793446833961_05412126.mp4"

sys.path.insert(0, HERE)
import md3lib
from mmw_geometry import build_megaman_payload_parts, transform_megaman_frame
import mma_geometry
import mma_textures


MAT_PROPS = {
    "arsenal":     dict(metallic=0.46, roughness=0.34, spec=0.92, unlit=0, additive=0, twoSided=1),
    "chrome_axle": dict(metallic=0.90, roughness=0.13, spec=1.55, unlit=0, additive=0, twoSided=1),
    "wheel":       dict(metallic=0.12, roughness=0.45, spec=0.48, unlit=0, additive=0, twoSided=1),
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
    md3lib.write(stage_md3, dict(name=model_name, surfaces=surfs, nframes=nf, frame_names=frame_names))
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

    print(f"  [MD3 OK] {model_name:18s}: {len(surfs)} surfs, {tot_v:5d} verts, {tot_t:5d} tris, {nf:2d} frames")


def export_static_hero_glb(model_name, surfs, tex_paths, hero_frame=2):
    """Exports a self-contained glTF 2.0 binary (.glb) with embedded PNG textures for external 3D DCC tools."""
    bin_buf = bytearray()
    buffer_views = []
    accessors = []
    images = []
    textures = []
    materials = []
    mat_idx_map = {}
    primitives = []

    def push_bv(raw_bytes, target=None):
        while len(bin_buf) & 3:
            bin_buf.append(0)
        off = len(bin_buf)
        bin_buf.extend(raw_bytes)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw_bytes)}
        if target is not None:
            bv["target"] = target
        idx = len(buffer_views)
        buffer_views.append(bv)
        return idx

    for s in surfs:
        if s.get("additive"):
            continue
        mat_k = s["mat"]
        if mat_k not in mat_idx_map:
            with open(tex_paths[mat_k], "rb") as tf:
                png_bytes = tf.read()
            img_bv = push_bv(png_bytes)
            img_i = len(images)
            images.append({"bufferView": img_bv, "mimeType": "image/png", "name": mat_k})
            tex_i = len(textures)
            textures.append({"source": img_i, "name": mat_k})
            mp = MAT_PROPS[mat_k]
            mat_i = len(materials)
            materials.append({
                "name": mat_k,
                "doubleSided": True,
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": tex_i},
                    "metallicFactor": float(mp["metallic"]),
                    "roughnessFactor": float(mp["roughness"]),
                },
            })
            mat_idx_map[mat_k] = mat_i

        vv, nn = s["frames"][hero_frame]
        qv = np.asarray(vv, dtype=np.float32)
        qn = np.asarray(nn, dtype=np.float32)
        # Right-handed Quake (+X fwd, +Y left, +Z up) -> glTF (-Z fwd, -X left/+X right, +Y up), scaled to meters
        sc = 0.025
        gv = np.stack([-qv[:, 1] * sc, qv[:, 2] * sc, -qv[:, 0] * sc], axis=1).astype(np.float32)
        gn = np.stack([-qn[:, 1], qn[:, 2], -qn[:, 0]], axis=1).astype(np.float32)
        gn /= np.maximum(1e-6, np.linalg.norm(gn, axis=1, keepdims=True))
        uv = np.asarray(s["st"], dtype=np.float32)
        idx_arr = np.asarray(s["tris"], dtype=np.uint16).reshape(-1)

        bv_pos = push_bv(gv.tobytes(), 34962)
        bv_nrm = push_bv(gn.tobytes(), 34962)
        bv_uv = push_bv(uv.tobytes(), 34962)
        bv_idx = push_bv(idx_arr.tobytes(), 34963)

        acc_pos = len(accessors)
        accessors.append({
            "bufferView": bv_pos, "componentType": 5126, "count": len(gv), "type": "VEC3",
            "min": [float(c) for c in gv.min(axis=0)], "max": [float(c) for c in gv.max(axis=0)],
        })
        acc_nrm = len(accessors)
        accessors.append({"bufferView": bv_nrm, "componentType": 5126, "count": len(gn), "type": "VEC3"})
        acc_uv = len(accessors)
        accessors.append({"bufferView": bv_uv, "componentType": 5126, "count": len(uv), "type": "VEC2"})
        acc_idx = len(accessors)
        accessors.append({"bufferView": bv_idx, "componentType": 5123, "count": len(idx_arr), "type": "SCALAR"})

        primitives.append({
            "attributes": {"POSITION": acc_pos, "NORMAL": acc_nrm, "TEXCOORD_0": acc_uv},
            "indices": acc_idx,
            "material": mat_idx_map[mat_k],
        })

    while len(bin_buf) & 3:
        bin_buf.append(0)

    gltf = {
        "asset": {"version": "2.0", "generator": "BakersfieldQuake Mega Man 4-Arsenal Builder"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": model_name, "mesh": 0}],
        "meshes": [{"name": model_name, "primitives": primitives}],
        "materials": materials,
        "textures": textures,
        "images": images,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_buf)}],
    }
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) & 3:
        json_bytes += b" "

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_buf)
    out_glb = os.path.join(STAGE_DIR, f"{model_name}.glb")
    with open(out_glb, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total_len))
        f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
        f.write(json_bytes)
        f.write(struct.pack("<II", len(bin_buf), 0x004E4942))
        f.write(bin_buf)
    print(f"  [GLB OK] {model_name}.glb ({total_len // 1024} KB)")


def build_flying_megaman_surfaces():
    """16-frame spinning Mega Man world projectile oriented nose-forward (+X) for downrange flight."""
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
        dict(name="megaman_whl", shader="progs/mma_wheel",       mat="wheel",       tris=wh_tris, st=wh_st, frames=wh_frames),
    ], names


def rig_orbit_center(surfs):
    pts = np.vstack([
        np.asarray(s["frames"][0][0], dtype=np.float32)
        for s in surfs
        if s["name"] not in ("arsenal_fx", "ranger_hands")
    ])
    mid = 0.5 * (pts.min(axis=0) + pts.max(axis=0))
    return [round(float(c), 2) for c in mid]


def pack_md3_model_i16(packer, tex_ids, model_id, meta, surfs, frame_names):
    """Packs 89-frame surfaces at exact Quake MD3 1/64-unit int16 precision + int8 normals."""
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

        pos_i16 = np.zeros((nf, nv, 3), dtype=np.int16)
        nrm_i8 = np.zeros((nf, nv, 3), dtype=np.int8)
        for fi, (vv, nn) in enumerate(s["frames"]):
            pos_i16[fi] = np.clip(np.round(np.asarray(vv, dtype=np.float32) * 64.0), -32767, 32767).astype(np.int16)
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
            pos=packer.add_bytes(pos_i16.tobytes()),
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
    if os.path.isfile(UPLOAD_VIDEO):
        cap = cv2.VideoCapture(UPLOAD_VIDEO)
        n_fr = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 90))
        # Thumbnail 1: Full chrome bar + twin wheels view
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(n_fr * 0.12)))
        ok1, f1 = cap.read()
        # Thumbnail 2: Close-up of 4-oval-hole white wheel rim & ball bearing
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(n_fr * 0.62)))
        ok2, f2 = cap.read()
        cap.release()
        im1 = Image.fromarray(cv2.cvtColor(f1, cv2.COLOR_BGR2RGB)) if (ok1 and f1 is not None) else Image.open(os.path.join(STAGE_DIR, "mma_wheel.png"))
        im2 = Image.fromarray(cv2.cvtColor(f2, cv2.COLOR_BGR2RGB)) if (ok2 and f2 is not None) else Image.open(os.path.join(STAGE_DIR, "mma_arsenal.png"))
    else:
        im1 = Image.open(os.path.join(STAGE_DIR, "mma_wheel.png"))
        im2 = Image.open(os.path.join(STAGE_DIR, "mma_arsenal.png"))

    sources.append(dict(
        badge="REFERENCE VIDEO · PAYLOAD",
        title="The 'Mega Man' Contraption",
        subtitle="Gleaming stainless/chrome bullet-nose bar, rear rubber cap & cross-axle",
        uri=make_jpeg_data_uri(im1),
    ))
    sources.append(dict(
        badge="WHEEL & BEARING DETAIL",
        title="4-Oval-Cutout Stamped Rim",
        subtitle="5-ribbed wheelbarrow tires + spin-readable 4-window dish rims & hub bearing",
        uri=make_jpeg_data_uri(im2),
    ))
    return sources


def main():
    os.makedirs(STAGE_DIR, exist_ok=True)
    print("1. Synthesizing 4-weapon arsenal textures & Quake shader...")
    tex_paths = mma_textures.ensure_arsenal_textures_and_shader(MOD, STAGE_DIR)

    print("2. Building 4 unique 89-frame Quake MD3 + glTF 2.0 (.glb) weapon models...")
    frame_names = mma_geometry.FRAME_NAMES_89
    v1_surfs, v1_muz = mma_geometry.build_v1_cannon()
    v2_surfs, v2_muz = mma_geometry.build_v2_slingshot()
    v3_surfs, v3_muz = mma_geometry.build_v3_bow()
    v4_surfs, v4_muz = mma_geometry.build_v4_handthrow()
    proj_surfs, proj_names = build_flying_megaman_surfaces()

    check_and_export_md3("v_mm_cannon",    v1_surfs, frame_names, write_progs=True)
    check_and_export_md3("v_mm_slingshot", v2_surfs, frame_names, write_progs=True)
    check_and_export_md3("v_mm_bow",       v3_surfs, frame_names, write_progs=True)
    check_and_export_md3("v_mm_handthrow", v4_surfs, frame_names, write_progs=True)
    check_and_export_md3("mma_proj_preview", proj_surfs, proj_names, write_progs=False)

    export_static_hero_glb("v_mm_cannon",    v1_surfs, tex_paths, hero_frame=2)
    export_static_hero_glb("v_mm_slingshot", v2_surfs, tex_paths, hero_frame=2)
    export_static_hero_glb("v_mm_bow",       v3_surfs, tex_paths, hero_frame=2)
    export_static_hero_glb("v_mm_handthrow", v4_surfs, tex_paths, hero_frame=2)

    print("3. Packing gzipped Int16 WebGL2 buffers & video reference thumbnails...")
    packer = BinaryPacker()
    tex_ids = {
        "arsenal":     packer.add_texture("arsenal",     tex_paths["arsenal"],     "Cast-Iron, Brass, Walnut, Latex, Carbon & Red Shop Rag"),
        "chrome_axle": packer.add_texture("chrome_axle", tex_paths["chrome_axle"], "Mirror Chrome Torpedo Bar, TIG Collar & Axle"),
        "wheel":       packer.add_texture("wheel",       tex_paths["wheel"],       "5-Rib Tire + 4-Oval-Cutout Stamped Rim & Bearing"),
        "hand":        packer.add_texture("hand",        tex_paths["hand"],        "Quake Ranger Leather Glove, Studs & Olive Sleeve"),
        "fx":          packer.add_texture("fx",          tex_paths["fx"],          "Cannon Blast, Air-Snap, 8-Ray Chrome Star-Glint & Spark"),
    }

    common_ranges = dict(
        fps=13,
        idleRange=[0, 15],
        fireRange=[16, 35],
        launchFrame=19,
        holdRange=[37, 60],
        cleanRange=[61, 88],
    )

    m1 = pack_md3_model_i16(
        packer, tex_ids, "v1_cannon",
        dict(
            **common_ranges,
            code="V1",
            badge="VERSION 1 · CANNON",
            title="The Broadside Blunder-Cannon",
            tagline="Slotted Cast-Iron & Riveted-Brass Naval Hand-Cannon w/ Sizzling Fuse",
            md3File="progs/v_mm_cannon.md3",
            md3Short="v_mm_cannon.md3",
            accent="#ffb454",
            accentRgb=[1.00, 0.71, 0.33],
            sfxKind="v1_cannon",
            muzzleEye=v1_muz,
            baseVel=[560.0, 0.0, 58.0],
            orbitCenter=rig_orbit_center(v1_surfs),
            orbitDist=21.5,
            orbitAz=0.58,
            orbitEl=0.28,
            presets=[
                ["3/4 Broadside", 0.58, 0.28, 21.0],
                ["Flared Muzzle", 0.12, 0.16, 18.5],
                ["Sizzling Fuse", 2.35, 0.52, 19.5],
                ["Slotted Wheel Bore", 1.48, 0.15, 19.0],
            ],
            highlights=[
                "<b>Slotted cast-iron &amp; riveted-brass barrel</b> lets Mega Man's cross-axle and <b>4-cutout wheels spin &amp; bobble right out both sides</b> while the chrome nose juts out the bell muzzle.",
                "<b>CoD Hold-Out (37–60)</b>: Heaves the heavy naval cannon sideways left &amp; right to admire the brass bands, sizzling fuse, and spinning wheels.",
                "<b>CoD Clean Bar (61–88)</b>: Pushes the chrome shaft out the brass muzzle, wraps a <b>red mechanic's shop rag</b> around the bar, polishes it 3.5× → <b>8-ray chrome star-glint!</b>",
            ],
            chips=[
                "V1: Slotted Cast-Iron & Brass Cannon",
                "V1: Sizzling Touch-Hole Fuse",
                "V1: Muzzle-Extend Rag Polish",
            ],
        ),
        v1_surfs, frame_names,
    )

    m2 = pack_md3_model_i16(
        packer, tex_ids, "v2_slingshot",
        dict(
            **common_ranges,
            code="V2",
            badge="VERSION 2 · SLINGSHOT",
            title="The Wrist-Rocket Y-Slinger",
            tagline="Carved American Walnut Y-Fork, Folding Wrist-Brace & 4-Band Surgical Latex Sling",
            md3File="progs/v_mm_slingshot.md3",
            md3Short="v_mm_slingshot.md3",
            accent="#34d399",
            accentRgb=[0.20, 0.83, 0.60],
            sfxKind="v2_slingshot",
            muzzleEye=v2_muz,
            baseVel=[515.0, 0.0, 68.0],
            orbitCenter=rig_orbit_center(v2_surfs),
            orbitDist=19.2,
            orbitAz=0.62,
            orbitEl=0.30,
            presets=[
                ["3/4 Y-Fork Hero", 0.62, 0.30, 19.2],
                ["Pouch & 4 Bands", 2.55, 0.32, 18.5],
                ["Front Fork Gap",  0.08, 0.18, 17.8],
                ["Top Sling View",  1.57, 1.15, 20.0],
            ],
            highlights=[
                "<b>Sculpted walnut Y-fork + tubular steel wrist-brace</b> with <b>4 golden surgical-latex bands</b> that dynamically stretch &amp; Poisson-thin on draw and snap-oscillate after launch.",
                "<b>Idle (0–15)</b>: Suspended in the taut leather pouch, both 4-cutout wheels spin 360° while Mega Man bounces springily on the elastic bands.",
                "<b>CoD Inspects (37–88)</b>: Holds out Y-fork with an elastic test-tug, or eases the pouch forward to <b>grab &amp; polish the chrome shaft with a red shop rag</b>!",
            ],
            chips=[
                "V2: Walnut Y-Fork Wrist-Rocket",
                "V2: 4-Strand Stretching Latex Bands",
                "V2: Springy Elastic Idle Bobble",
            ],
        ),
        v2_surfs, frame_names,
    )

    m3 = pack_md3_model_i16(
        packer, tex_ids, "v3_bow",
        dict(
            **common_ranges,
            code="V3",
            badge="VERSION 3 · BOW & ARROW",
            title="The Recurve Mega-Bow",
            tagline="Canted Carbon/Brass Compound-Recurve Battle Bow & 3-Vane Fletched Mega-Arrow",
            md3File="progs/v_mm_bow.md3",
            md3Short="v_mm_bow.md3",
            accent="#38bdf8",
            accentRgb=[0.22, 0.74, 0.97],
            sfxKind="v3_bow",
            muzzleEye=v3_muz,
            baseVel=[545.0, 0.0, 62.0],
            orbitCenter=rig_orbit_center(v3_surfs),
            orbitDist=22.0,
            orbitAz=0.55,
            orbitEl=0.24,
            presets=[
                ["3/4 Archer Bow",  0.55, 0.24, 22.0],
                ["Fletched Nock",   2.62, 0.22, 19.5],
                ["Sight & Warhead", 0.14, 0.16, 18.5],
                ["Pulley Cams",     1.45, 0.58, 22.5],
            ],
            highlights=[
                "<b>Heroic +22°-canted carbon battle bow</b> with glowing 3-pin fiber sight, flexing S-curve limbs, <b>rotating eccentric pulley cams</b>, and a <b>3-vane orange fletched arrow tail</b> mated to Mega Man!",
                "<b>CoD Hold-Out (37–60)</b>: Cants the bow across the screen to show off the cams &amp; fletching, then <b>plucks the bowstring</b> so it visibly vibrates!",
                "<b>CoD Clean Bar (61–88)</b>: Reaches past the riser with a <b>red shop cloth</b> to briskly buff the gleaming chrome warhead bar until it sparkles!",
            ],
            chips=[
                "V3: Canted Carbon Recurve/Compound Bow",
                "V3: 3-Vane Fletched Mega-Arrow",
                "V3: CoD Bowstring Pluck Inspect",
            ],
        ),
        v3_surfs, frame_names,
    )

    m4 = pack_md3_model_i16(
        packer, tex_ids, "v4_handthrow",
        dict(
            **common_ranges,
            code="V4",
            badge="VERSION 4 · HAND-HELD THROW",
            title="Bare-Handed Mega-Chuck",
            tagline="Pure Quake Ranger Gloved Grip, Wild Bucking Idle & Overhand Fastball Throw",
            md3File="progs/v_mm_handthrow.md3",
            md3Short="v_mm_handthrow.md3",
            accent="#fb7185",
            accentRgb=[0.98, 0.44, 0.52],
            sfxKind="v4_handthrow",
            muzzleEye=v4_muz,
            baseVel=[485.0, 0.0, 74.0],
            orbitCenter=rig_orbit_center(v4_surfs),
            orbitDist=17.2,
            orbitAz=0.65,
            orbitEl=0.28,
            presets=[
                ["3/4 Gloved Grip", 0.65, 0.28, 17.2],
                ["4-Hole Rim Close-Up", 1.48, 0.18, 15.8],
                ["Front Chrome Tip", 0.10, 0.18, 16.0],
                ["Rear Grip & Cap",  2.85, 0.25, 16.8],
            ],
            highlights=[
                "<b>Zero launcher hardware</b> — Ranger's studded leather glove grips the rear shaft directly while the motorized wheels spin 360° &amp; buck wildly in his hand, then winds up &amp; <b>overhand-chucks it</b>!",
                "<b>CoD Hold-Out (37–60)</b>: Holds the revving contraption dead-center, twists left/right to admire the 4-hole rims, and does a <b>mid-air palm toss-and-catch juggle</b>!",
                "<b>CoD Clean Bar (61–88)</b>: Tilts the chrome torpedo bar proudly up at +32° while the left gloved hand wraps a <b>red shop rag</b> around the shaft and buffs it to a <b>star-glint shine</b>!",
            ],
            chips=[
                "V4: Pure Bare-Handed Gloved Throw",
                "V4: Mid-Air Palm Juggle Inspect",
                "V4: Hero Close-Up Chrome Bar Polish",
            ],
        ),
        v4_surfs, frame_names,
    )

    m_proj = pack_md3_model_i16(
        packer, tex_ids, "proj_mm",
        dict(fps=24, idleRange=[0, 15], fireRange=[0, 15], launchFrame=0),
        proj_surfs, proj_names,
    )

    raw_bytes = bytes(packer.buf)
    gz_bytes = gzip.compress(raw_bytes, compresslevel=9, mtime=0)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    print(f"  Binary payload: {len(raw_bytes):,} bytes raw -> {len(gz_bytes):,} bytes gzipped ({len(b64_gz):,} chars b64)")

    data_obj = dict(
        title="BakersfieldQuake · 4-Weapon Mega Man Arsenal & CoD Inspect Studio",
        sources=build_source_thumbnails(),
        textures=packer.tex_list,
        models=[m1, m2, m3, m4, m_proj],
        projectileModelIndex=4,
        binGz=b64_gz,
    )

    with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
        tpl = f.read()
    assert "/*__MMA_DATA__*/null" in tpl, "Placeholder /*__MMA_DATA__*/null missing in megaman_arsenal_4v.template.html"

    payload_json = json.dumps(data_obj, separators=(",", ":"))
    html_out = tpl.replace("/*__MMA_DATA__*/null", payload_json, 1)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_out)

    print(f"4. Wrote standalone 4-weapon WebGL2 studio: {OUT_HTML} ({len(html_out) / (1024 * 1024):.2f} MB)")


if __name__ == "__main__":
    main()
