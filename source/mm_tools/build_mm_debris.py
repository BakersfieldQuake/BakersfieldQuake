r"""Builds Mega Man's complete 3D explosion models & debris assets from megaman1.glb:
  1. Standalone 31-node Rigid-Body + Gyroscopic Wheel/Bar Animated 3D Model:
       G:\Quake\Combat\BakersfieldQuake\megaman_explode.glb (271 frames @ 60 FPS = 4.50s)
  2. In-game DarkPlaces / Quake MD3 models & unified fracture atlas in <progs_dir>:
       - mm_debris_tex.png  (1024x1024 unified megaman1.glb + sheared steel/scorch/rubber/rim fracture atlas)
       - mm_wheel.md3       (16 wheel-spin frames around Y axle, real megaman1.glb wheel + white dish rim + zerk + valve)
       - mm_bar.md3         (real brushed stainless steel central bar + bullet nose cone, cylinder axis along +X)
       - mm_axle.md3        (snapped steel cross-axle shaft + locknut collar, axis along +X)
       - mm_cap.md3         (blown-off black Delrin rear end-cap + bezel)
       - mm_frag1..6.md3    (6 distinct Voronoi-fractured 3D shrapnel chunks: collar, steel pipe, 2x tire rubber, white rim, hub)
       - mm_explode.md3     (20-frame 3D core shatter-burst animation at the blast epicenter)

Usage:
  python3.13 build_mm_debris.py <progs_dir> [<progs_dir> ...]
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import md3lib
import mm_explode_sim

GLB_PATH = r"g:\Downloads\Telegram Desktop\megaman1.glb"
BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
PARTS_JSON = os.path.join(HERE, "out", "mm_fractured_parts.json")
OUT_GLB = os.path.join(MOD_DIR, "megaman_explode.glb")
SIM_CACHE_NPZ = os.path.join(HERE, "out", "mm_explode_sim_cache.npz")


def ensure_fractured_parts():
    if not os.path.exists(PARTS_JSON):
        print("Running Blender 5.2 Voronoi fracture on megaman1.glb...")
        r = subprocess.run([
            BLENDER_EXE, "-b", "--python",
            os.path.join(HERE, "blender_fracture_mm.py"),
            "--", GLB_PATH, PARTS_JSON,
        ])
        if r.returncode != 0:
            sys.exit("Blender fracture failed")
    return json.load(open(PARTS_JSON, encoding="utf-8"))


def make_single_frame_md3_surf(name, shader, part, scale_xyz=(1.0, 1.0, 1.0)):
    sx, sy, sz = scale_xyz
    verts = [(v[0] * sx, v[1] * sy, v[2] * sz) for v in part["verts"]]
    norms = []
    for nx, ny, nz in part["norms"]:
        vx, vy, vz = nx / sx, ny / sy, nz / sz
        ln = math.sqrt(vx * vx + vy * vy + vz * vz) or 1.0
        norms.append((vx / ln, vy / ln, vz / ln))
    return dict(
        name=name,
        shader=shader,
        tris=[tuple(t) for t in part["tris"]],
        st=[tuple(u) for u in part["uvs"]],
        frames=[(verts, norms)],
    )


def make_spinning_wheel_md3(part, shader, nframes=16):
    """Creates 16 forward-rolling spin frames around the local +Y axle (+Z top rotates toward +X forward)."""
    v0 = part["verts"]
    n0 = part["norms"]
    frames = []
    for fi in range(nframes):
        th = 2.0 * math.pi * fi / nframes
        c, s = math.cos(th), math.sin(th)
        vv = [(x * c + z * s, y, -x * s + z * c) for (x, y, z) in v0]
        nn = [(nx * c + nz * s, ny, -nx * s + nz * c) for (nx, ny, nz) in n0]
        frames.append((vv, nn))
    return dict(
        name="wheel",
        shader=shader,
        tris=[tuple(t) for t in part["tris"]],
        st=[tuple(u) for u in part["uvs"]],
        frames=frames,
    )


def make_epicenter_burst_md3(parts, sim, shader_debris, shader_flash):
    """Builds a 20-frame vertex-animated 3D shatter-burst MD3 (progs/mm_explode.md3)
    from the detonation frame onward (0.67s @ 30fps) so the contraption visibly ruptures
    into micro-splinters + shock starburst right at the blast origin."""
    bf = sim["boom_frame"]
    # Sample 20 frames starting at bf, stepping by 2 frames of 60fps (= 30fps, 0.63s)
    sample_fis = [min(sim["n_frames"] - 1, bf + k * 2) for k in range(20)]
    blast_c = np.array([-1.4, 0.0, 11.8], dtype=np.float64)

    burst_frags = [
        "frag_00", "frag_01", "frag_02", "frag_04", "frag_05", "frag_06",
        "frag_07", "frag_10", "frag_12", "frag_13", "frag_14", "frag_16",
    ]
    # Group into batches <= 3800 verts per MD3 surface
    batches = [burst_frags[:6], burst_frags[6:]]
    surfs = []

    for bi, batch in enumerate(batches):
        tris_comb = []
        st_comb = []
        v_base = 0
        part_meshes = []
        for fname in batch:
            if fname not in parts:
                continue
            p = parts[fname]
            vw, nw = sim["meshes"][fname]
            part_meshes.append((fname, vw, nw))
            st_comb.extend(tuple(u) for u in p["uvs"])
            for a, b, c in p["tris"]:
                tris_comb.append((a + v_base, b + v_base, c + v_base))
            v_base += len(vw)

        frames = []
        for k_idx, fi in enumerate(sample_fis):
            # Shrink splinters smoothly over final 5 frames so entity removal is invisible
            fade_s = 1.0 if k_idx < 14 else max(0.02, (19.5 - k_idx) / 5.5)
            vv_f, nn_f = [], []
            for fname, vw, nw in part_meshes:
                pos = sim["tracks"][fname]["pos"][fi].astype(np.float64) - blast_c
                # Keep comfortably inside MD3 [-500..+500] range; no floor clamp in air burst!
                q = sim["tracks"][fname]["rot"][fi].astype(np.float64)
                Rm = mm_explode_sim.q_to_mat3(q)
                vp = ((vw * (0.68 * fade_s)) @ Rm.T) + pos * 0.82
                vp = np.clip(vp, -480.0, 480.0)
                np_r = nw @ Rm.T
                vv_f.extend(map(tuple, vp.tolist()))
                nn_f.extend(map(tuple, np_r.tolist()))
            frames.append((vv_f, nn_f))

        surfs.append(dict(
            name=f"shatter{bi}",
            shader=shader_debris,
            tris=tris_comb,
            st=st_comb,
            frames=frames,
        ))

    # Add 3D volumetric blast starburst surface for first frames
    star = mm_explode_sim.build_blast_starburst_mesh()
    sv0 = np.array(star["verts"], dtype=np.float64)
    sn0 = np.array(star["norms"], dtype=np.float64)
    star_frames = []
    for k_idx, fi in enumerate(sample_fis):
        sc = float(sim["tracks"]["blast_flash"]["scl"][fi][0]) * 1.35
        q = sim["tracks"]["blast_flash"]["rot"][fi].astype(np.float64)
        Rm = mm_explode_sim.q_to_mat3(q)
        vp = (sv0 * max(0.01, sc)) @ Rm.T
        np_r = sn0 @ Rm.T
        star_frames.append((list(map(tuple, vp.tolist())), list(map(tuple, np_r.tolist()))))

    surfs.append(dict(
        name="flash",
        shader=shader_flash,
        tris=[tuple(t) for t in star["tris"]],
        st=[tuple(u) for u in star["uvs"]],
        frames=star_frames,
    ))
    return surfs


def signed_volume(md3_model):
    tot = 0.0
    for s in md3_model["surfaces"]:
        v = s["frames"][0][0]
        for a, b, c in s["tris"]:
            p, q, r = v[a], v[b], v[c]
            tot += (p[0]*(q[1]*r[2] - q[2]*r[1]) - p[1]*(q[0]*r[2] - q[2]*r[0]) + p[2]*(q[0]*r[1] - q[1]*r[0])) / 6.0
    return tot


def main():
    out_dirs = sys.argv[1:] or [os.path.join(MOD_DIR, "progs")]
    parts = ensure_fractured_parts()

    print("Building unified fracture texture atlas...")
    atlas_2048 = mm_explode_sim.build_fracture_atlas(GLB_PATH)

    print("Running 480 Hz 3D rigid-body + gyroscopic wheel & bar rolling simulation...")
    sim = mm_explode_sim.simulate_full_explosion(parts, fps=60, duration=4.50, substeps=8)

    # Export standalone animated 3D model (.glb)
    mm_explode_sim.export_exploded_glb(parts, sim, atlas_2048, OUT_GLB)

    # Save simulation cache so megaman_explode.html builder can package it instantaneously
    save_dict = {
        "fps": np.array([sim["fps"]], dtype=np.int32),
        "n_frames": np.array([sim["n_frames"]], dtype=np.int32),
        "boom_frame": np.array([sim["boom_frame"]], dtype=np.int32),
        "sparks_json": np.array([json.dumps(sim["sparks"])]),
    }
    for k, tr in sim["tracks"].items():
        save_dict[f"pos_{k}"] = tr["pos"]
        save_dict[f"rot_{k}"] = tr["rot"]
        save_dict[f"scl_{k}"] = tr["scl"]
    np.savez_compressed(SIM_CACHE_NPZ, **save_dict)

    # Tone-mapped 1024x1024 DarkPlaces atlas (0.72x brightness so lit models match Quake map lighting cleanly)
    atlas_1024 = atlas_2048.resize((1024, 1024), Image.LANCZOS)
    atlas_dp = ImageEnhance.Brightness(atlas_1024).enhance(0.72)

    # Warm orange-white flash swatch for mm_explode.md3 starburst
    flash_im = Image.new("RGB", (32, 32), (255, 196, 72))

    # Build MD3 model structures
    shader_tex = "progs/mm_debris_tex"
    shader_fl = "progs/mm_blast_flash"

    models_to_save = {
        "mm_wheel": [make_spinning_wheel_md3(parts["wheel_right"], shader_tex, nframes=16)],
        "mm_bar":   [make_single_frame_md3_surf("bar", shader_tex, parts["main_bar"])],
        "mm_axle":  [make_single_frame_md3_surf("axle", shader_tex, parts["axle_right"], scale_xyz=(1.0, 1.45, 1.45))],
        "mm_cap":   [make_single_frame_md3_surf("cap", shader_tex, parts["rear_cap"], scale_xyz=(1.15, 1.15, 1.15))],
        "mm_frag1": [make_single_frame_md3_surf("frag1", shader_tex, parts["frag_03"], scale_xyz=(1.15, 1.15, 1.15))],
        "mm_frag2": [make_single_frame_md3_surf("frag2", shader_tex, parts["frag_08"], scale_xyz=(1.15, 1.15, 1.15))],
        "mm_frag3": [make_single_frame_md3_surf("frag3", shader_tex, parts["frag_09"])],
        "mm_frag4": [make_single_frame_md3_surf("frag4", shader_tex, parts["frag_15"])],
        "mm_frag5": [make_single_frame_md3_surf("frag5", shader_tex, parts["frag_18"])],
        "mm_frag6": [make_single_frame_md3_surf("frag6", shader_tex, parts["frag_22"])],
        "mm_explode": make_epicenter_burst_md3(parts, sim, shader_tex, shader_fl),
    }

    for out in out_dirs:
        os.makedirs(out, exist_ok=True)
        atlas_dp.save(os.path.join(out, "mm_debris_tex.png"), "PNG", optimize=True)
        flash_im.save(os.path.join(out, "mm_blast_flash.png"), "PNG")

        for mname, surfs in models_to_save.items():
            p_md3 = os.path.join(out, mname + ".md3")
            nf = len(surfs[0]["frames"])
            md3lib.write(p_md3, dict(name=mname, surfaces=surfs, nframes=nf))
            chk = md3lib.read(p_md3)
            vol = signed_volume(chk)
            nv_tot = sum(len(s["st"]) for s in chk["surfaces"])
            nt_tot = sum(len(s["tris"]) for s in chk["surfaces"])
            print(f"  [{out}] {mname:12s}.md3 : nf={nf:2d}, nv={nv_tot:4d}, nt={nt_tot:4d}, vol={vol:8.1f}")


if __name__ == "__main__":
    main()
