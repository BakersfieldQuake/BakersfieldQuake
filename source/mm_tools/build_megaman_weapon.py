"""Master builder for the BakersfieldQuake Mega Man Player Weapon ('The Mega-Slinger' Mk.II) & Interactive 3D HTML Studio.

Generates:
  1. Staging Quake-ready MD3 models & procedural PNG textures in source/mm_tools/out/megaman_weapon/:
       - v_megaman_gun.md3    (37 frames: 16 idle + 20 fire/launch/reload + 1 empty — 'THE MEGA-SLINGER' Mk.II)
       - v_megaman_hand.md3   (32 frames: 16 idle + 16 wind/throw/catch             — 'RANGER GAUNTLET THROW')
       - megaman_clean.md3    (16 frames: 16 wheel-spin drive frames                — Clean Recreated Contraption)
       - mmw_*.png            (6 procedural high-contrast Quake textures)
  2. Self-contained offline WebGL2 HTML Inspection & Review Studio:
       - G:\\Quake\\Combat\\BakersfieldQuake\\megaman_weapon.html
  3. Live in-game deployment:
       - progs/v_megaman.md3, progs/mmw_*.png, scripts/megaman_slinger.shader

Usage:
    python3.13 source/mm_tools/build_megaman_weapon.py
"""
import base64
import gzip
import io
import json
import os
import shutil
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
STAGE_DIR = os.path.join(HERE, "out", "megaman_weapon")
TEMPLATE_HTML = os.path.join(HERE, "megaman_weapon.template.html")
OUT_HTML = os.path.join(MOD, "megaman_weapon.html")
ORIG_GLB = r"g:\Downloads\Telegram Desktop\megaman1.glb"

sys.path.insert(0, HERE)
import md3lib
import mmw_textures
import mmw_animations


def check_mesh_sanity(label, surfs):
    tot_v = 0
    tot_t = 0
    for s in surfs:
        nv = len(s["st"])
        nt = len(s["tris"])
        assert nv <= 4096 and nt <= 8192, f"{label}/{s['name']} exceeds MD3 limit: nv={nv}, nt={nt}"
        v0, n0 = s["frames"][0]
        assert len(v0) == nv and len(n0) == nv
        arr_v = np.asarray(v0, dtype=np.float32)
        arr_n = np.asarray(n0, dtype=np.float32)
        assert np.all(np.isfinite(arr_v)) and np.all(np.isfinite(arr_n)), f"NaN/Inf in {label}/{s['name']}"
        tot_v += nv
        tot_t += nt
    print(f"  [OK] {label:22s}: {len(surfs)} surfaces, {tot_v:5d} verts, {tot_t:5d} tris, {len(surfs[0]['frames']):2d} frames")


def load_decimated_original_glb(glb_path, out_dir):
    """Loads megaman1.glb and performs seam-preserving voxel+UV vertex clustering (~15k tris) for reference Tab 4."""
    with open(glb_path, "rb") as f:
        magic, ver, _ = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF"
        jlen, _ = struct.unpack("<I4s", f.read(8))
        gltf = json.loads(f.read(jlen))
        blen, _ = struct.unpack("<I4s", f.read(8))
        bin_data = f.read(blen)

    def get_acc(idx):
        acc = gltf["accessors"][idx]
        bv = gltf["bufferViews"][acc["bufferView"]]
        off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        cnt = acc["count"]
        ctype = {5123: np.uint16, 5125: np.uint32, 5126: np.float32}[acc["componentType"]]
        ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[acc["type"]]
        arr = np.frombuffer(bin_data, dtype=ctype, count=cnt * ncomp, offset=off)
        return arr.reshape(cnt, ncomp) if ncomp > 1 else arr

    im_info = gltf["images"][0]
    bv = gltf["bufferViews"][im_info["bufferView"]]
    raw_im = bin_data[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
    orig_im = Image.open(io.BytesIO(raw_im)).convert("RGB")
    orig_tex_path = os.path.join(out_dir, "mmw_orig_scan.jpg")
    orig_im.resize((1024, 1024), Image.LANCZOS).save(orig_tex_path, "JPEG", quality=86, optimize=True)

    pr = gltf["meshes"][0]["primitives"][0]
    pos_gltf = get_acc(pr["attributes"]["POSITION"]).astype(np.float32)
    uv_gltf = get_acc(pr["attributes"]["TEXCOORD_0"]).astype(np.float32)
    idx_gltf = get_acc(pr["indices"]).reshape(-1, 3)

    S = 11.4
    pos_q = np.stack([pos_gltf[:, 2] * S, -pos_gltf[:, 0] * S, pos_gltf[:, 1] * S], axis=1)

    mn = pos_q.min(axis=0)
    span = np.maximum(pos_q.max(axis=0) - mn, 1e-5)
    qx = np.floor((pos_q[:, 0] - mn[0]) / span[0] * 48.0).astype(np.int64)
    qy = np.floor((pos_q[:, 1] - mn[1]) / span[1] * 48.0).astype(np.int64)
    qz = np.floor((pos_q[:, 2] - mn[2]) / span[2] * 48.0).astype(np.int64)
    qu = np.floor(np.clip(uv_gltf[:, 0], 0.0, 0.9999) * 22.0).astype(np.int64)
    qv = np.floor(np.clip(uv_gltf[:, 1], 0.0, 0.9999) * 22.0).astype(np.int64)
    keys = (((qx * 64 + qy) * 64 + qz) * 32 + qu) * 32 + qv

    uniq_keys, inv = np.unique(keys, return_inverse=True)
    n_new = len(uniq_keys)

    new_pos = np.zeros((n_new, 3), dtype=np.float32)
    new_uv = np.zeros((n_new, 2), dtype=np.float32)
    counts = np.bincount(inv).astype(np.float32)
    for c in range(3):
        new_pos[:, c] = np.bincount(inv, weights=pos_q[:, c]) / counts
    for c in range(2):
        new_uv[:, c] = np.bincount(inv, weights=uv_gltf[:, c]) / counts

    new_tris = inv[idx_gltf]
    keep = (new_tris[:, 0] != new_tris[:, 1]) & (new_tris[:, 1] != new_tris[:, 2]) & (new_tris[:, 0] != new_tris[:, 2])
    new_tris = new_tris[keep].astype(np.uint32)

    p0 = new_pos[new_tris[:, 0]]
    p1 = new_pos[new_tris[:, 1]]
    p2 = new_pos[new_tris[:, 2]]
    fn = np.cross(p1 - p0, p2 - p0)
    new_nrm = np.zeros_like(new_pos)
    for k in range(3):
        np.add.at(new_nrm, new_tris[:, k], fn)
    nl = np.linalg.norm(new_nrm, axis=1, keepdims=True)
    new_nrm = np.where(nl > 1e-8, new_nrm / np.maximum(nl, 1e-8), np.array([0.0, 0.0, 1.0], dtype=np.float32))

    print(f"  [OK] Original GLB Ref  : decimated {len(pos_gltf)}v/{len(idx_gltf)}t -> {n_new}v/{len(new_tris)}t")
    return new_pos, new_nrm, new_uv, new_tris, orig_tex_path


# --------------------------------------------------------------------------- Binary Arena Packer for WebGL2 Studio
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
        if path.lower().endswith(".jpg"):
            im.convert("RGB").save(bio, "JPEG", quality=86, optimize=True)
            mime = "image/jpeg"
        else:
            im.save(bio, "PNG", optimize=True)
            mime = "image/png"
        uri = f"data:{mime};base64," + base64.b64encode(bio.getvalue()).decode("ascii")
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


MAT_PROPS = {
    "chrome_axle": dict(metallic=0.92, roughness=0.12, spec=1.60, unlit=0, additive=0),
    "wheel":       dict(metallic=0.12, roughness=0.46, spec=0.52, unlit=0, additive=0),
    "gun_metal":   dict(metallic=0.72, roughness=0.25, spec=1.18, unlit=0, additive=0),
    "hand":        dict(metallic=0.22, roughness=0.44, spec=0.48, unlit=0, additive=0),
    "gauge_glow":  dict(metallic=0.00, roughness=0.50, spec=0.00, unlit=1, additive=0),
    "fx":          dict(metallic=0.00, roughness=0.50, spec=0.00, unlit=1, additive=1),
    "orig_scan":   dict(metallic=0.15, roughness=0.55, spec=0.25, unlit=1, additive=0, twoSided=1),
}


def pack_md3_model(packer, tex_ids, model_id, meta, surfs, frame_names):
    nf = len(frame_names)
    surfs_out = []
    all_pts = []
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
        all_pts.append(pos_f[0])

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
            twoSided=mp.get("twoSided", 0),
        ))

    pts0 = np.vstack(all_pts)
    bmin = pts0.min(axis=0).round(3).tolist()
    bmax = pts0.max(axis=0).round(3).tolist()

    out = dict(
        id=model_id,
        nf=nf,
        nv=tot_v,
        nt=tot_t,
        nsurfs=len(surfs_out),
        frameNames=frame_names,
        bbox=[bmin, bmax],
        surfaces=surfs_out,
    )
    out.update(meta)
    return out


def pack_raw_scan_model(packer, tex_id, pos, nrm, uv, tris):
    nv = len(pos)
    nt = len(tris)
    e01 = np.sort(tris[:, [0, 1]], axis=1)
    e12 = np.sort(tris[:, [1, 2]], axis=1)
    e20 = np.sort(tris[:, [2, 0]], axis=1)
    edges = np.unique(np.vstack([e01, e12, e20]), axis=0).astype(np.uint32)

    nrm_i8 = np.clip(np.round(nrm * 127.0), -127, 127).astype(np.int8)
    mp = MAT_PROPS["orig_scan"]
    surf = dict(
        name="megaman1_scan",
        mat="orig_scan",
        tex=tex_id,
        nv=nv,
        nt=nt,
        ne=len(edges),
        uint32Idx=1,
        uv=packer.add_bytes(uv.astype(np.float32).tobytes()),
        tris=packer.add_bytes(tris.astype(np.uint32).tobytes()),
        edges=packer.add_bytes(edges.tobytes()),
        pos=packer.add_bytes(pos[None, :, :].astype(np.float32).tobytes()),
        nrm=packer.add_bytes(nrm_i8[None, :, :].tobytes()),
        metallic=mp["metallic"],
        roughness=mp["roughness"],
        spec=mp["spec"],
        unlit=mp["unlit"],
        additive=0,
        twoSided=1,
    )
    bmin = pos.min(axis=0).round(3).tolist()
    bmax = pos.max(axis=0).round(3).tolist()
    return dict(
        id="orig_scan",
        tabLabel="4 · Original GLB Scan",
        badge="REFERENCE",
        title="Original megaman1.glb Scan (Reference)",
        subtitle="Raw 3D photogrammetry/scan input (decimated from 167,500 tris for side-by-side comparison)",
        md3File="megaman1.glb (source reference)",
        hasPov=False,
        defaultPov=False,
        fps=10,
        idleRange=[0, 0],
        fireRange=[0, 0],
        launchFrame=-1,
        orbitCenter=[0.0, 0.0, 6.2],
        orbitDist=24.0,
        orbitAz=0.68,
        orbitEl=0.28,
        presets=[
            ["3/4 Scan View", 0.68, 0.28, 24.0],
            ["Front Axle", 0.0, 0.20, 24.0],
            ["Wheel Dish Side", 1.57, 0.16, 22.0],
            ["Top Cross View", 0.40, 1.25, 25.0],
        ],
        highlights=[
            "Original 111,379-vertex / 167,500-triangle unlit emissive scan from megaman1.glb.",
            "Reveals the exact reference proportions: 1.90m wheel-to-wheel span, 5-ribbed pneumatic tires, concave white steel dish rims, yellow cotter pins, Schrader valve stems, and -34.7° tilted chrome central bar.",
            "Compare directly against Tab 1 (Mega-Slinger Mk.II), Tab 2 (Ranger Gauntlet Throw), and Tab 3 (Clean Recreated Payload) to see how all scan artifacts & UV noise were replaced with clean, hard-edged specular Quake geometry.",
        ],
        nf=1,
        nv=nv,
        nt=nt,
        nsurfs=1,
        frameNames=["scan1"],
        bbox=[bmin, bmax],
        surfaces=[surf],
    )


def main():
    os.makedirs(STAGE_DIR, exist_ok=True)
    print("1. Synthesizing high-resolution procedural Quake textures...")
    tex_paths = mmw_textures.build_all_textures(STAGE_DIR)

    print("2. Building sleek Mk.II articulated 3D weapon & payload geometries...")
    slinger_surfs, slinger_names = mmw_animations.build_slinger_gun_md3_surfaces()
    hand_surfs, hand_names = mmw_animations.build_hand_throw_md3_surfaces()
    payload_surfs, payload_names = mmw_animations.build_standalone_megaman_md3_surfaces()

    check_mesh_sanity("v_megaman_gun.md3", slinger_surfs)
    check_mesh_sanity("v_megaman_hand.md3", hand_surfs)
    check_mesh_sanity("megaman_clean.md3", payload_surfs)

    md3lib.write(os.path.join(STAGE_DIR, "v_megaman_gun.md3"), dict(name="v_megaman_gun", surfaces=slinger_surfs, nframes=len(slinger_names), frame_names=slinger_names))
    md3lib.write(os.path.join(STAGE_DIR, "v_megaman_hand.md3"), dict(name="v_megaman_hand", surfaces=hand_surfs, nframes=len(hand_names), frame_names=hand_names))
    md3lib.write(os.path.join(STAGE_DIR, "megaman_clean.md3"), dict(name="megaman_clean", surfaces=payload_surfs, nframes=len(payload_names), frame_names=payload_names))

    print("3. Preparing decimated original megaman1.glb reference mesh...")
    scan_pos, scan_nrm, scan_uv, scan_tris, orig_tex_path = load_decimated_original_glb(ORIG_GLB, STAGE_DIR)

    print("4. Packing binary WebGL2 geometry arena & textures...")
    packer = BinaryPacker()
    tex_ids = {
        "chrome_axle": packer.add_texture("chrome_axle", tex_paths["chrome_axle"], "Mirror Chrome Bar, Weld & Axle"),
        "wheel":       packer.add_texture("wheel",       tex_paths["wheel"],       "5-Rib Tire & 4-Cutout White Rim"),
        "gun_metal":   packer.add_texture("gun_metal",   tex_paths["gun_metal"],   "Gunmetal Titanium, Mag-Rails & Coils"),
        "hand":        packer.add_texture("hand",        tex_paths["hand"],        "Ranger Leather Glove & Bracer"),
        "gauge_glow":  packer.add_texture("gauge_glow",  tex_paths["gauge_glow"],  "250 PSI Dial, Rail Chevrons & Core"),
        "fx":          packer.add_texture("fx",          tex_paths["fx"],          "Starburst Flash, Mach Cone & Plasma"),
        "orig_scan":   packer.add_texture("orig_scan",   orig_tex_path,            "Original megaman1.glb Scan Atlas"),
    }

    m_slinger = pack_md3_model(
        packer, tex_ids, "slinger_gun",
        dict(
            tabLabel="1 · Mega-Slinger Mk.II ★",
            badge="PRIMARY IN-GAME WEAPON",
            title="The Mega-Slinger Mk.II · Mag-Pneumatic Rail-Catapult",
            subtitle="Sleek multi-faceted gunmetal/titanium rail-catapult w/ glowing cyan accelerator chevrons, 250 PSI dial & 4-cutout spinning wheels",
            md3File="progs/v_megaman.md3",
            hasPov=True,
            defaultPov=True,
            fps=13,
            idleRange=[0, 15],
            fireRange=[16, 35],
            launchFrame=19,
            hiddenPayloadFrames=[20, 21, 22, 23, 24, 36],
            noPayloadLerpFrames=[19, 24, 35, 36],
            muzzleEye=[24.8, -1.0, -1.8],
            orbitCenter=[15.8, -3.2, -2.6],
            orbitDist=22.0,
            orbitAz=2.45,
            orbitEl=0.25,
            presets=[
                ["3/4 Hero Orbit", 2.45, 0.25, 22.0],
                ["Muzzle, Coils & 4-Cutout Wheels", 0.22, 0.14, 20.5],
                ["Breech, Reflex Core & PSI Dial", 3.00, 0.28, 17.5],
                ["Left Profile (Tanks & Rollers)", 1.62, 0.14, 23.0],
                ["Top Mag-Rail Chevron Track", 2.20, 1.15, 23.5],
            ],
            highlights=[
                "Sleek swept gunmetal-titanium chassis with inlaid electric-cyan '>>>' linear-accelerator chevrons, cantilevered copper booster cowls, low-profile CNC V-cradles, and razor-sharp hard-edge bevel normals.",
                "Zero-clipping mechanical layout: tucked copper 250 PSI accumulator bottles, forward-swept outrigger arms with mathematically tangent brass drive rollers, contoured foregrip, and prominent canted PSI dial + holographic MEGA-CORE sight in 1st-person POV.",
                "Visceral firing feel: coiled overcharge whine, instantaneous rail slam, 3D starburst muzzle flash + feathered Mach cone + dynamic muzzle illumination + forward compensator gas blowoff, followed by full-scale elevator pop-up & tactile jaw clamp lock!",
            ],
        ),
        slinger_surfs, slinger_names,
    )

    m_hand = pack_md3_model(
        packer, tex_ids, "ranger_hand",
        dict(
            tabLabel="2 · Ranger Hand-Throw",
            badge="ALTERNATE VARIANT",
            title="Quake Ranger Gauntlet · Hand-Held Thrower",
            subtitle="Articulated Quake Ranger leather glove & riveted bronze bracer gripping, revving, and hurling Mega Man",
            md3File="out/megaman_weapon/v_megaman_hand.md3",
            hasPov=True,
            defaultPov=True,
            fps=13,
            idleRange=[0, 15],
            fireRange=[16, 31],
            launchFrame=20,
            hiddenPayloadFrames=[23, 24],
            noPayloadLerpFrames=[22, 24],
            muzzleEye=[20.5, -2.2, -1.5],
            orbitCenter=[15.2, -4.2, -2.8],
            orbitDist=20.5,
            orbitAz=2.42,
            orbitEl=0.22,
            presets=[
                ["3/4 Hand & Wheels", 2.42, 0.22, 20.5],
                ["Front Tires & Torpedo Nose", 0.30, 0.15, 20.0],
                ["Glove Grip & Knuckle Plate", 1.45, -0.05, 16.5],
                ["Top Axle Span", 2.10, 1.10, 22.0],
            ],
            highlights=[
                "Sculpted Quake Ranger combat hand with distressed brown leather stitching, 4-stud bronze knuckle plate, buckled iron-brass forearm gauntlet, and 5 individually articulated 3-phalanx fingers wrapped around the tilted chrome bar.",
                "Idle animation (idle1–16): Organic figure-8 breathing sway, continuous 4-cutout wheel rotation showing spinning Schrader valve stems & yellow cotter pins, and subtle thumb-grip flex.",
                "Fire / Throw animation (wind1–settle3): Draws back & cocks wrist upward while wheels rev fast, whips forward uncurling all 5 fingers to hurl Mega Man with a jagged plasma wake, reaches to belt, and swings up a fresh unit with a crisp wrist-catch!",
            ],
        ),
        hand_surfs, hand_names,
    )

    m_payload = pack_md3_model(
        packer, tex_ids, "clean_payload",
        dict(
            tabLabel="3 · Recreated Payload",
            badge="CLEAN RECREATION",
            title="Recreated 'Mega Man' Contraption (Clean Quake Mesh)",
            subtitle="Artifact-free hard-edged recreation of megaman1.glb with 4-cutout concave white rims, 5-ribbed lugged tires, valve stems & mirror-chrome bar",
            md3File="out/megaman_weapon/megaman_clean.md3",
            hasPov=False,
            defaultPov=False,
            fps=12,
            idleRange=[0, 15],
            fireRange=[0, 15],
            launchFrame=-1,
            orbitCenter=[0.0, 0.0, 5.2],
            orbitDist=25.0,
            orbitAz=0.68,
            orbitEl=0.28,
            presets=[
                ["3/4 Contraption View", 0.68, 0.28, 25.0],
                ["Front Chrome Nose", 0.0, 0.20, 24.0],
                ["4-Cutout Dish, Nut & Valve", 1.57, 0.14, 18.0],
                ["Rear Cap & TIG Weld", 3.14, 0.22, 24.0],
            ],
            highlights=[
                "Faithfully recreates every proportion of megaman1.glb with crisp hard-edge machined crease normals (down from 167,500 noisy scan tris).",
                "True 32-segment 3D concave white stamped-steel wheel rims with 4 bold oval ventilation cutouts, sealed center ball-bearing race, 3D hex zinc axle nuts, bright yellow cotter pins, angled Schrader valve stems, and lugged 5-rib rubber tire treads.",
                "Mirror-polished anisotropic chrome central bar with stepped matte-black rubber rear cap, TIG-welded cross-sleeve & retaining collars, and ogive bullet nose.",
            ],
        ),
        payload_surfs, payload_names,
    )

    m_scan = pack_raw_scan_model(packer, tex_ids["orig_scan"], scan_pos, scan_nrm, scan_uv, scan_tris)

    gz_bytes = gzip.compress(bytes(packer.buf), compresslevel=9)
    b64_gz = base64.b64encode(gz_bytes).decode("ascii")
    print(f"   Binary arena: raw={len(packer.buf)/1e6:.2f} MB -> gzip={len(gz_bytes)/1e6:.2f} MB")

    payload_json = dict(
        binGz=b64_gz,
        binLen=len(packer.buf),
        textures=packer.tex_list,
        models=[m_slinger, m_hand, m_payload, m_scan],
        projectileModelIndex=2,
    )

    tpl = open(TEMPLATE_HTML, encoding="utf-8").read()
    assert "/*__MMW_DATA__*/null" in tpl, "Placeholder /*__MMW_DATA__*/null missing in template!"
    html_out = tpl.replace("/*__MMW_DATA__*/null", json.dumps(payload_json, separators=(",", ":"), ensure_ascii=False))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"5. Wrote {OUT_HTML} ({os.path.getsize(OUT_HTML)/1e6:.2f} MB)")
    install_slinger_into_mod()


def install_slinger_into_mod():
    """Installs the Mega-Slinger Mk.II directly as the live in-game Mega Man gun: progs/v_megaman.md3,
    its mmw_* textures, and scripts/megaman_slinger.shader (self-lit gauge/rail glow + additive fx)."""
    progs = os.path.join(MOD, "progs")
    deployed = os.path.join(progs, "v_megaman.md3")
    shutil.copy(os.path.join(STAGE_DIR, "v_megaman_gun.md3"), deployed)

    base = deployed + ".pre_vmedit"
    edits_path = os.path.join(MOD, "source", "viewmodel_editor", "edits.json")
    saved = json.load(open(edits_path)).get("v_megaman") if os.path.exists(edits_path) else None
    if saved:
        import apply_viewmodel_edits
        shutil.copy(deployed, base)
        apply_viewmodel_edits.bake(base, deployed, saved)
        print(f"   kept the editor pose {saved}")
    elif os.path.exists(base):
        os.remove(base)

    # Calibrated for DarkPlaces r_hdr_scenebrightness 2.5 while preserving crisp metallic & tire tread contrast!
    for k, dim in (("chrome_axle", 0.48), ("wheel", 0.42), ("gun_metal", 0.46), ("hand", 0.46), ("gauge_glow", 0.52)):
        im = np.asarray(Image.open(os.path.join(STAGE_DIR, f"mmw_{k}.png")).convert("RGB")).astype(np.float32)
        Image.fromarray(np.clip(im * dim, 0, 255).astype(np.uint8)).save(os.path.join(progs, f"mmw_{k}.png"))

    g = np.asarray(Image.open(os.path.join(STAGE_DIR, "mmw_gauge_glow.png")).convert("RGB")).astype(np.float32)
    Image.fromarray(np.clip(g * 0.48, 0, 255).astype(np.uint8)).save(os.path.join(progs, "mmw_gauge_glow_glow.png"))

    fx = np.asarray(Image.open(os.path.join(STAGE_DIR, "mmw_fx.png")).convert("RGBA")).astype(np.float32)
    rgb = fx[..., :3] * (fx[..., 3:4] / 255.0) * 0.68
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(os.path.join(progs, "mmw_fx.png"))

    shader = "// written by mm_tools/build_megaman_weapon.py\n"
    for k in ("gun_metal", "chrome_axle", "wheel", "hand"):
        shader += f"\nprogs/mmw_{k}\n{{\n\tcull none\n\t{{\n\t\tmap progs/mmw_{k}\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n"
    # Self-illuminated telemetry dial, MEGA-CORE reflex sight & cyan linear-accelerator rail chevrons!
    shader += "\nprogs/mmw_gauge_glow\n{\n\tcull none\n\t{\n\t\tmap progs/mmw_gauge_glow\n\t\trgbGen identity\n\t}\n}\n"
    shader += "\nprogs/mmw_fx\n{\n\tcull none\n\t{\n\t\tmap progs/mmw_fx\n\t\tblendfunc add\n\t\trgbGen identity\n\t}\n}\n"
    with open(os.path.join(MOD, "scripts", "megaman_slinger.shader"), "w", encoding="ascii", newline="\n") as f:
        f.write(shader)
    print(f"6. Installed v_megaman.md3 + mmw_* textures into {progs}")


if __name__ == "__main__":
    main()
