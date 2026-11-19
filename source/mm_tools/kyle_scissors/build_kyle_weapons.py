"""Master builder for the 5 Kyle Tillet Scissor Weapon Viewmodels (.md3 + PNG skins + manifest.json).

Outputs to:
  C:\\Users\\qxdc\\.gemini\\antigravity\\brain\\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671\\scratch\\kyle_stage\\weapons\\

Models (36 frames each: Idle 0..15, Hold-to-Lock 16..27, Fire/Launch+Reload 28..35):
  1. v_kyle_v1_cannon.md3   — 'The Kyle Cannon'
  2. v_kyle_v2_hand.md3     — 'Hand-Held Kyle Dart'
  3. v_kyle_v3_register.md3 — 'Commission Cash-Register Launcher'
  4. v_kyle_v4_shears.md3   — 'Giant Barber-Shears Railgun'
  5. v_kyle_v5_invoice.md3  — 'Paper-Plane Invoice Cannon'
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS_DIR = os.path.abspath(os.path.join(HERE, ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if MM_TOOLS_DIR not in sys.path:
    sys.path.insert(0, MM_TOOLS_DIR)

import md3lib
import kw_textures
import kw_geometry

OUT_DIR = r"C:\Users\qxdc\.gemini\antigravity\brain\35ddac3e-c123-4eaf-9fc7-8fdfe6fb4671\scratch\kyle_stage\weapons"

MATERIAL_DEFS = {
    "metals": dict(
        texture="kyle_metals.png",
        metallic=0.72,
        roughness=0.28,
        spec=1.10,
        alphaTest=0,
        translucent=0,
        unlit=0,
        additive=0,
        twoSided=1,
    ),
    "hand": dict(
        texture="kyle_hand.png",
        metallic=0.18,
        roughness=0.48,
        spec=0.42,
        alphaTest=0,
        translucent=0,
        unlit=0,
        additive=0,
        twoSided=1,
    ),
    "cutout": dict(
        texture="kyle_cutout.png",
        metallic=0.04,
        roughness=0.65,
        spec=0.22,
        alphaTest=1,
        alphaCutoff=0.35,
        translucent=0,
        unlit=0,
        additive=0,
        twoSided=1,
    ),
    "glass": dict(
        texture="kyle_glass.png",
        metallic=0.15,
        roughness=0.08,
        spec=1.35,
        alphaTest=0,
        translucent=1,
        depthWrite=0,
        unlit=0,
        additive=0,
        twoSided=1,
    ),
    "fx": dict(
        texture="kyle_fx.png",
        metallic=0.0,
        roughness=0.5,
        spec=0.0,
        alphaTest=0,
        translucent=1,
        depthWrite=0,
        unlit=1,
        additive=1,
        twoSided=1,
    ),
}


def compute_bounds(surfs, frame_indices):
    pts = []
    for s in surfs:
        if s["mat"] == "fx":
            continue
        for fi in frame_indices:
            arr = np.asarray(s["frames"][fi][0], dtype=np.float32)
            # Ignore micro-scaled hidden frames
            if arr.shape[0] > 0:
                pts.append(arr)
    all_p = np.vstack(pts)
    mn = all_p.min(axis=0)
    mx = all_p.max(axis=0)
    ctr = 0.5 * (mn + mx)
    return dict(
        min=[round(float(x), 2) for x in mn],
        max=[round(float(x), 2) for x in mx],
        center=[round(float(x), 2) for x in ctr],
    )


def export_and_verify_md3(model_id, surfs, frame_names, out_dir):
    nf = len(frame_names)
    tot_v, tot_t = 0, 0
    surf_meta = []

    for s in surfs:
        nv = len(s["st"])
        nt = len(s["tris"])
        assert nv <= 4096 and nt <= 8192, f"{model_id}/{s['name']} exceeds MD3 limit: nv={nv}, nt={nt}"
        assert len(s["frames"]) == nf, f"{model_id}/{s['name']} frames={len(s['frames'])} != {nf}"
        for fi, (vv, nn) in enumerate(s["frames"]):
            assert len(vv) == nv and len(nn) == nv
            arr_v = np.asarray(vv, dtype=np.float32)
            arr_n = np.asarray(nn, dtype=np.float32)
            assert np.all(np.isfinite(arr_v)) and np.all(np.isfinite(arr_n)), f"NaN in {model_id}/{s['name']} f{fi}"
            assert np.max(np.abs(arr_v)) < 500.0, f"MD3 int16 overflow risk in {model_id}/{s['name']} f{fi}"
        tot_v += nv
        tot_t += nt

        mat_k = s["mat"]
        md = MATERIAL_DEFS[mat_k]
        surf_meta.append(dict(
            name=s["name"],
            material=mat_k,
            shader=s["shader"],
            texture=md["texture"],
            verts=nv,
            tris=nt,
            **{k: v for k, v in md.items() if k != "texture"},
        ))

    md3_name = f"{model_id}.md3"
    md3_path = os.path.join(out_dir, md3_name)
    md3lib.write(md3_path, dict(
        name=model_id,
        surfaces=surfs,
        nframes=nf,
        frame_names=frame_names,
    ))

    # Round-trip verification with md3lib.read
    rt = md3lib.read(md3_path)
    assert rt["nframes"] == nf, f"Readback nframes mismatch: {rt['nframes']} != {nf}"
    assert len(rt["surfaces"]) == len(surfs), "Readback surface count mismatch"
    for s_orig, s_rt in zip(surfs, rt["surfaces"]):
        assert s_orig["name"] == s_rt["name"]
        assert len(s_orig["tris"]) == len(s_rt["tris"])
        assert len(s_orig["st"]) == len(s_rt["st"])
        assert len(s_rt["frames"]) == nf

    skin_path = os.path.join(out_dir, f"{model_id}_0.skin")
    with open(skin_path, "w", encoding="ascii", newline="\n") as f:
        for s in surfs:
            f.write(f"{s['name']},{s['shader']}\n")

    idle_bounds = compute_bounds(surfs, range(0, 16))
    lock_bounds = compute_bounds(surfs, range(16, 28))
    fire_bounds = compute_bounds(surfs, range(28, 36))

    print(
        f"  [OK] {md3_name:24s} | {len(surfs)} surfs | {tot_v:4d} verts | {tot_t:4d} tris | {nf} frames | "
        f"idle center={idle_bounds['center']}"
    )
    return dict(
        md3=md3_name,
        skin=f"{model_id}_0.skin",
        nframes=nf,
        verts=tot_v,
        tris=tot_t,
        surfaces=surf_meta,
        bounds=dict(idle=idle_bounds, lock=lock_bounds, fire=fire_bounds),
        sizeBytes=os.path.getsize(md3_path),
    )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("1. Building high-res PNG skins & studio-keyed Kyle cutouts...")
    tex_paths = kw_textures.build_all_weapon_textures(OUT_DIR)
    for k, p in tex_paths.items():
        print(f"   - {k:8s}: {os.path.basename(p)} ({os.path.getsize(p)/1024:.1f} KB)")

    print("2. Building & md3lib-verifying all 5 36-frame Quake viewmodels...")
    builders = [
        kw_geometry.build_v1_cannon,
        kw_geometry.build_v2_hand,
        kw_geometry.build_v3_register,
        kw_geometry.build_v4_shears,
        kw_geometry.build_v5_invoice,
    ]
    frame_names = kw_geometry.FRAME_NAMES_36
    models_out = []

    for fn in builders:
        surfs, meta = fn()
        exp = export_and_verify_md3(meta["id"], surfs, frame_names, OUT_DIR)
        entry = dict(
            id=meta["id"],
            title=meta["title"],
            subtitle=meta["subtitle"],
            flavor=meta["flavor"],
            md3=exp["md3"],
            skin=exp["skin"],
            sizeBytes=exp["sizeBytes"],
            nframes=exp["nframes"],
            verts=exp["verts"],
            tris=exp["tris"],
            frameNames=frame_names,
            frameRanges=dict(
                idle=[0, 15],
                lock=[16, 27],
                fire=[28, 35],
                launchFrame=28,
            ),
            muzzle=meta["muzzle"],
            orbitCenter=meta["orbitCenter"],
            orbitDist=meta["orbitDist"],
            bounds=exp["bounds"],
            surfaces=exp["surfaces"],
        )
        models_out.append(entry)

    manifest = dict(
        version=1,
        coordSystem="Quake 1st-person viewmodel (+X forward, +Y left, +Z up)",
        textures={k: os.path.basename(v) for k, v in tex_paths.items()},
        materials=MATERIAL_DEFS,
        models=models_out,
    )
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"3. Wrote manifest: {manifest_path}")


if __name__ == "__main__":
    main()
