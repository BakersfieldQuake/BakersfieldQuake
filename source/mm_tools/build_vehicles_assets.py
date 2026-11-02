r"""Master Asset Builder for BakersfieldQuake's 4 Unique Shootable/Explodable 3D Vehicles:
  - veh_truck : Heavy-Duty Extended-Cab 4x4 Pickup (Cobalt Blue & Silver Two-Tone)
  - veh_sedan : Late-90s Boxy 4-Door Street Sedan (Metallic Emerald Green)
  - veh_van   : Classic Ford Econoline White Cargo Van (Fleet Oxford White)
  - veh_coupe : Early-2000s 2-Door Tuner Sport Coupe / Fastback (Milano Red)

Produces:
  1. Standalone Multi-Clip Animated 3D glTF 2.0 (.glb) models in BakersfieldQuake\:
       veh_truck.glb, veh_sedan.glb, veh_van.glb, veh_coupe.glb
     Each .glb embeds 'Idle', 'CatchFire', and 'Explode' (60 FPS, 480 Hz rigid-body + 4-tire rolling physics).
  2. DarkPlaces In-Game MD3 Models, Skins, Tone-Mapped Textures & Shaders in progs\ and scripts\:
       progs/veh_<kind>.md3          (36 frames: 0..15 Idle, 16..21 Flinch, 22..35 CatchFire w/ popping hood)
       progs/veh_<kind>.md3_0.skin   (intact paint + running lights glow)
       progs/veh_<kind>.md3_1.skin   (blistered/scorched paint + glowing orange hood/engine fire)
       progs/veh_van.md3_2.skin / _3.skin  (van only: skins 0 / 1 with body_a not drawn. vehicle_drive.qc sends these to
                                      the driver while he sits in the cockpit: with the camera inside the shell, body_a
                                      paints the whole view flat grey)
       progs/veh_<kind>_wreck.md3    (20 frames: blast-leap -> pavement slam -> bounce -> smoking charred hulk)
       progs/veh_<kind>_wheel.md3    (16 forward-rolling spin frames around +Y axle for each unique wheel!)
       progs/veh_<kind>_hood.md3     (unique blown-off 3D hood)
       progs/veh_<kind>_door.md3     (unique blown-off 3D door + mirror + glass)
       progs/veh_<kind>_extra.md3    (Truck rollbar+KC+tailgate / Sedan trunk / Van barn-doors+rack / Coupe wing)
       progs/veh_<kind>_bumper.md3   (unique blown-off 3D bumper)
       progs/veh_shrap1..4.md3       (4 twisted scorched shrapnel chunks)
       progs/veh_blast.md3           (20-frame 3D core shatter-burst + volumetric shock-starburst)
       scripts/vehicles.shader       (double-sided diffuse + additive headlight/taillight/ember glow)
  3. Compressed simulation cache in source/mm_tools/out/vehicles_sim_cache.npz for vehicles_showcase.html.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import md3lib
import veh_textures
import veh_physics_sim

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
PARTS_JSON = os.path.join(HERE, "out", "vehicles_parts.json")
SIM_CACHE_NPZ = os.path.join(HERE, "out", "vehicles_sim_cache.npz")
KINDS = ("truck", "sedan", "van", "coupe")


def ensure_blender_parts(force=False):
    blender_script = os.path.join(HERE, "blender_build_vehicles.py")
    van_mesh_script = os.path.join(HERE, "promaster_van_mesh.py")
    newest_src = max(
        os.path.getmtime(blender_script),
        os.path.getmtime(van_mesh_script) if os.path.exists(van_mesh_script) else 0.0,
    )
    if force or (not os.path.exists(PARTS_JSON)) or (newest_src > os.path.getmtime(PARTS_JSON)):
        print("Running headless Blender 5.2 vehicle builder...")
        r = subprocess.run([BLENDER_EXE, "-b", "--python", blender_script, "--", PARTS_JSON])
        if r.returncode != 0:
            sys.exit("Blender vehicle builder failed!")
    with open(PARTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _slice_part_tris(part, tri_start, tri_end, sub_name):
    sub_tris_orig = part["tris"][tri_start:tri_end]
    remap = {}
    verts, norms, uvs, tris = [], [], [], []
    for t in sub_tris_orig:
        nt = []
        for vi in t:
            if vi not in remap:
                remap[vi] = len(verts)
                verts.append(part["verts"][vi])
                norms.append(part["norms"][vi])
                uvs.append(part["uvs"][vi])
            nt.append(remap[vi])
        tris.append(nt)
    return {"name": sub_name, "origin": part["origin"], "verts": verts, "norms": norms, "uvs": uvs, "tris": tris}


def build_animated_intact_md3_surfaces(veh_data, kind, shader_default):
    """Builds the 36-frame intact vehicle MD3 (all surfaces strictly < 4096 MD3 vertex limit):
       - Frames  0..15 : Unique per-vehicle Idle loop (16 frames)
       - Frames 16..21 : Bullet/blast Hit_Flinch suspension recoil (6 frames)
       - Frames 22..35 : Critical CatchFire loop (hood popped ajar 11..17 deg & rattling, body bucking, 14 frames)"""
    parts = veh_data["parts"]
    body_names = ["chassis", "hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib"]
    wheel_names = ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"]

    frame_specs = (
        [("idle", i / 16.0) for i in range(16)]
        + [("flinch", (i + 0.5) / 6.0) for i in range(6)]
        + [("fire", i / 14.0) for i in range(14)]
    )
    poses = [veh_physics_sim.compute_part_trs_in_sprung_state(veh_data, kind, ph, mode=md) for md, ph in frame_specs]

    def assemble_surface(surf_name, item_list, shader_override=None):
        tris_comb = []
        st_comb = []
        v_base = 0
        part_arrays = []
        for item in item_list:
            if isinstance(item, str):
                pnm, p = item, parts[item]
            else:
                pnm, p = item
            va = np.array(p["verts"], dtype=np.float64)
            na = np.array(p["norms"], dtype=np.float64)
            part_arrays.append((pnm, va, na))
            st_comb.extend(tuple(u) for u in p["uvs"])
            for a, b, c in p["tris"]:
                tris_comb.append((a + v_base, b + v_base, c + v_base))
            v_base += len(va)

        frames = []
        for pose in poses:
            vv_f, nn_f = [], []
            for pnm, va, na in part_arrays:
                pos, q, _ = pose[pnm]
                Rm = veh_physics_sim.q_to_mat3(q)
                vp = np.clip((va @ Rm.T) + pos, -500.0, 500.0)
                np_r = na @ Rm.T
                vv_f.extend(map(tuple, vp.tolist()))
                nn_f.extend(map(tuple, np_r.tolist()))
            frames.append((vv_f, nn_f))

        return dict(name=surf_name, shader=shader_override or shader_default, tris=tris_comb, st=st_comb, frames=frames)

    if kind == "van":
        ch = parts["chassis"]
        mid_t = len(ch["tris"]) // 2
        ch_a = _slice_part_tris(ch, 0, mid_t, "chassis_a")
        ch_b = _slice_part_tris(ch, mid_t, len(ch["tris"]), "chassis_b")
        surfs = [
            assemble_surface("body_a", [("chassis", ch_a)]),
            assemble_surface("body_b", [("chassis", ch_b)]),
            assemble_surface("interior", ["hood", "door_l", "door_r", "extra_part", "bumper_f", "bumper_r", "detail_vib"]),
            assemble_surface("wheels", wheel_names),
        ]
        if "glass_cab" in parts:
            surfs.append(assemble_surface("glass", ["glass_cab"], shader_override="progs/veh_van_glass"))
        return surfs

    return [
        assemble_surface("body", body_names),
        assemble_surface("wheels", wheel_names),
    ]


def build_wreck_md3_surface(veh_data, sim, shader_burn):
    """Builds 20-frame veh_<kind>_wreck.md3 sampled from boom_frame onward:
    Frames 0..18: buckled charred chassis leaps upward in blast wave, twists, slams down, bounces once;
    Frame 19: resting smoking hulk pose!"""
    p = veh_data["parts"]["wreck_chassis"]
    va = np.array(p["verts"], dtype=np.float64)
    na = np.array(p["norms"], dtype=np.float64)
    bf = sim["boom_frame"]
    tr = sim["tracks"]["wreck_chassis"]
    # Sample over 1.5s after detonation (90 frames / 19 steps ~ 5 frames per step) + final settled frame
    sample_fis = [min(sim["n_frames"] - 1, bf + k * 5) for k in range(19)] + [sim["n_frames"] - 1]

    frames = []
    for fi in sample_fis:
        pos = tr["pos"][fi].astype(np.float64)
        q = tr["rot"][fi].astype(np.float64)
        Rm = veh_physics_sim.q_to_mat3(q)
        # Keep wreck centered near entity XY origin while preserving full vertical blast leap, pitch & roll!
        pos_clamped = np.array([pos[0] * 0.25, pos[1] * 0.25, max(0.0, pos[2])], dtype=np.float64)
        vp = np.clip((va @ Rm.T) + pos_clamped, -500.0, 500.0)
        np_r = na @ Rm.T
        frames.append((list(map(tuple, vp.tolist())), list(map(tuple, np_r.tolist()))))

    return [dict(
        name="wreck",
        shader=shader_burn,
        tris=[tuple(t) for t in p["tris"]],
        st=[tuple(u) for u in p["uvs"]],
        frames=frames,
    )]


def build_spinning_wheel_md3_surface(wheel_part, shader_tex, nframes=16):
    """16 forward-rolling spin frames around +Y axle (+Z top rotates forward toward +X)."""
    v0 = wheel_part["verts"]
    n0 = wheel_part["norms"]
    frames = []
    for fi in range(nframes):
        th = 2.0 * math.pi * fi / nframes
        c, s = math.cos(th), math.sin(th)
        vv = [(x * c + z * s, y, -x * s + z * c) for (x, y, z) in v0]
        nn = [(nx * c + nz * s, ny, -nx * s + nz * c) for (nx, ny, nz) in n0]
        frames.append((vv, nn))
    return [dict(
        name="wheel",
        shader=shader_tex,
        tris=[tuple(t) for t in wheel_part["tris"]],
        st=[tuple(u) for u in wheel_part["uvs"]],
        frames=frames,
    )]


def build_single_part_md3_surface(part, shader_tex):
    verts = [tuple(v) for v in part["verts"]]
    norms = [tuple(n) for n in part["norms"]]
    return [dict(
        name=part["name"][:16],
        shader=shader_tex,
        tris=[tuple(t) for t in part["tris"]],
        st=[tuple(u) for u in part["uvs"]],
        frames=[(verts, norms)],
    )]


def build_blast_burst_md3_surfaces(veh_data, sim, shader_debris, shader_flash):
    """Builds 20-frame progs/veh_blast.md3 (shatter splinters + 3D volumetric shock starburst at blast center)."""
    bf = sim["boom_frame"]
    sample_fis = [min(sim["n_frames"] - 1, bf + k * 2) for k in range(20)]
    parts = veh_data["parts"]

    tris_c, st_c, p_list = [], [], []
    vb = 0
    for si in range(10):
        nm = f"shrap_{si}"
        p = parts[nm]
        va = np.array(p["verts"], dtype=np.float64)
        na = np.array(p["norms"], dtype=np.float64)
        p_list.append((nm, va, na))
        st_c.extend(tuple(u) for u in p["uvs"])
        for a, b, c in p["tris"]:
            tris_c.append((a + vb, b + vb, c + vb))
        vb += len(va)

    sh_frames = []
    for ki, fi in enumerate(sample_fis):
        fade = 1.0 if ki < 14 else max(0.02, (19.5 - ki) / 5.5)
        vv_f, nn_f = [], []
        for nm, va, na in p_list:
            pos = sim["tracks"][nm]["pos"][fi].astype(np.float64) * 0.72
            q = sim["tracks"][nm]["rot"][fi].astype(np.float64)
            Rm = veh_physics_sim.q_to_mat3(q)
            vp = np.clip(((va * fade) @ Rm.T) + pos, -480.0, 480.0)
            np_r = na @ Rm.T
            vv_f.extend(map(tuple, vp.tolist()))
            nn_f.extend(map(tuple, np_r.tolist()))
        sh_frames.append((vv_f, nn_f))

    star = veh_physics_sim.build_blast_starburst_mesh()
    sv0 = np.array(star["verts"], dtype=np.float64)
    sn0 = np.array(star["norms"], dtype=np.float64)
    st_frames = []
    for ki, fi in enumerate(sample_fis):
        sc = float(sim["tracks"]["blast_flash"]["scl"][fi][0]) * 1.45
        q = sim["tracks"]["blast_flash"]["rot"][fi].astype(np.float64)
        Rm = veh_physics_sim.q_to_mat3(q)
        vp = np.clip((sv0 * max(0.01, sc)) @ Rm.T + np.array([0.0, 0.0, 24.0]), -480.0, 480.0)
        np_r = sn0 @ Rm.T
        st_frames.append((list(map(tuple, vp.tolist())), list(map(tuple, np_r.tolist()))))

    return [
        dict(name="shatter", shader=shader_debris, tris=tris_c, st=st_c, frames=sh_frames),
        dict(name="flash", shader=shader_flash, tris=[tuple(t) for t in star["tris"]], st=[tuple(u) for u in star["uvs"]], frames=st_frames),
    ]


def write_vehicles_shader(scripts_dir):
    os.makedirs(scripts_dir, exist_ok=True)
    lines = ["// written by mm_tools/build_vehicles_assets.py\n\n"]
    for kind in KINDS:
        for variant in ("tex", "burn"):
            sh = f"progs/veh_{kind}_{variant}"
            lines.append(
                f"{sh}\n{{\n\tcull none\n"
                f"\t{{\n\t\tmap {sh}\n\t\trgbGen lightingDiffuse\n\t}}\n"
                f"\t{{\n\t\tmap {sh}_glow\n\t\tblendfunc add\n\t\trgbGen identity\n\t}}\n}}\n\n"
            )
    for g_sh in ("progs/veh_van_glass", "progs/veh_van_glass_burn"):
        lines.append(
            f"{g_sh}\n{{\n\tcull none\n\t{{\n\t\tmap {g_sh}\n\t\tblendfunc blend\n\t\trgbGen lightingDiffuse\n\t}}\n}}\n\n"
        )
    # draws nothing: the van's cockpit skins use it to leave body_a out. GL_ZERO GL_ONE keeps what is already on screen
    # and adds nothing, whatever the texture. (rgbGen const and alphaGen const are NOT honoured by this DarkPlaces, so
    # "black" or "alpha 0" paint the texture, and the shell round the cab then hazes or whitens the whole view)
    lines.append(
        "progs/veh_van_nodraw\n{\n\tcull none\n\t{\n\t\tmap progs/veh_van_glass\n\t\tblendfunc GL_ZERO GL_ONE\n\t}\n}\n\n"
    )
    lines.append(
        "progs/veh_blast_flash\n{\n\tcull none\n\t{\n\t\tmap progs/veh_blast_flash\n\t\tblendfunc add\n\t\trgbGen identity\n\t}\n}\n"
    )
    path = os.path.join(scripts_dir, "vehicles.shader")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)
    print(f"Wrote {path}")


def install_vehicles_effectinfo(mod_dir):
    import shutil
    fx = os.path.join(mod_dir, "effectinfo.txt")
    src = os.path.join(HERE, "vehicles_effectinfo.txt")
    if not os.path.exists(fx) or not os.path.exists(src):
        return
    bak = fx + ".pre_vehicles"
    if not os.path.exists(bak):
        shutil.copy(fx, bak)
    begin, end = b"// ---- Vehicles begin", b"// ---- Vehicles end"
    raw = open(fx, "rb").read()
    if begin in raw and end in raw:
        raw = raw[:raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end):].lstrip(b"\r\n")
    add = open(src, "rb").read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    open(fx, "wb").write(raw.rstrip(b"\r\n") + b"\r\n\r\n" + begin + b"\r\n" + add + end + b"\r\n")
    print(f"Installed vehicle effects into {fx}")


def write_van_cockpit_skins(progs_dir):
    """veh_van.md3_2.skin / _3.skin = skins 0 / 1 with body_a left out (vehicle_drive.qc: customizeentityforclient on the van)."""
    for idx, (sh, glass) in ((2, ("progs/veh_van_tex", "progs/veh_van_glass")), (3, ("progs/veh_van_burn", "progs/veh_van_glass_burn"))):
        text = "body_a,progs/veh_van_nodraw\n" + "".join(f"{n},{sh}\n" for n in ("body_b", "interior", "wheels")) + f"glass,{glass}\n"
        with open(os.path.join(progs_dir, f"veh_van.md3_{idx}.skin"), "w", encoding="ascii", newline="\n") as sf:
            sf.write(text)


def main():
    progs_dir = os.path.join(MOD_DIR, "progs")
    scripts_dir = os.path.join(MOD_DIR, "scripts")
    preview_dir = os.path.join(HERE, "out", "vehicles")

    all_veh = ensure_blender_parts(force=False)
    print("Generating vehicle texture atlases & DarkPlaces skins...")
    atlases = veh_textures.save_darkplaces_textures(progs_dir, preview_dir, dp_gain=0.60)
    write_vehicles_shader(scripts_dir)
    install_vehicles_effectinfo(MOD_DIR)

    cache_dict = {}
    sims = {}

    for kind in KINDS:
        print(f"Simulating 480 Hz explosion & exporting standalone veh_{kind}.glb...")
        vdata = all_veh[kind]
        sim = veh_physics_sim.simulate_vehicle_explosion(vdata, kind, fps=60, duration=6.0, substeps=8)
        sims[kind] = sim

        glb_path = os.path.join(MOD_DIR, f"veh_{kind}.glb")
        veh_physics_sim.export_vehicle_glb(
            vdata, kind, sim, atlases[kind]["intact"], glb_path, glass_rgba_im=atlases[kind].get("glass")
        )
        print(f"  -> Wrote {glb_path} ({os.path.getsize(glb_path) / 1e6:.2f} MB)")

        cache_dict[f"{kind}_fps"] = np.array([sim["fps"]], dtype=np.int32)
        cache_dict[f"{kind}_n_frames"] = np.array([sim["n_frames"]], dtype=np.int32)
        cache_dict[f"{kind}_boom_frame"] = np.array([sim["boom_frame"]], dtype=np.int32)
        cache_dict[f"{kind}_sparks"] = np.array([json.dumps(sim["sparks"])])
        for pnm, tr in sim["tracks"].items():
            cache_dict[f"{kind}_pos_{pnm}"] = tr["pos"]
            cache_dict[f"{kind}_rot_{pnm}"] = tr["rot"]
            cache_dict[f"{kind}_scl_{pnm}"] = tr["scl"]

        # Write DarkPlaces MD3s + .skin files for this vehicle!
        sh_intact = f"progs/veh_{kind}_tex"
        sh_burn = f"progs/veh_{kind}_burn"

        intact_surfs = build_animated_intact_md3_surfaces(vdata, kind, sh_intact)
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}.md3"), dict(name=f"veh_{kind}", surfaces=intact_surfs))

        if kind == "van":
            import van_windshield
            van_windshield.strip_windshield(os.path.join(progs_dir, "veh_van.md3"))		# the van has no windshield glass
            surf_names = ["body_a", "body_b", "interior", "wheels"]
            skin0_text = "".join(f"{s},{sh_intact}\n" for s in surf_names) + "glass,progs/veh_van_glass\n"
            skin1_text = "".join(f"{s},{sh_burn}\n" for s in surf_names) + "glass,progs/veh_van_glass_burn\n"
        else:
            surf_names = ["body", "wheels"]
            skin0_text = "".join(f"{s},{sh_intact}\n" for s in surf_names)
            skin1_text = "".join(f"{s},{sh_burn}\n" for s in surf_names)
        with open(os.path.join(progs_dir, f"veh_{kind}.md3_0.skin"), "w", encoding="ascii", newline="\n") as sf:
            sf.write(skin0_text)
        with open(os.path.join(progs_dir, f"veh_{kind}.md3_1.skin"), "w", encoding="ascii", newline="\n") as sf:
            sf.write(skin1_text)
        if kind == "van":
            write_van_cockpit_skins(progs_dir)

        wreck_surfs = build_wreck_md3_surface(vdata, sim, sh_burn)
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_wreck.md3"), dict(name=f"veh_{kind}_wreck", surfaces=wreck_surfs))

        wheel_surfs = build_spinning_wheel_md3_surface(vdata["parts"]["wheel_fl"], sh_intact, nframes=16)
        md3lib.write(os.path.join(progs_dir, f"veh_{kind}_wheel.md3"), dict(name=f"veh_{kind}_wheel", surfaces=wheel_surfs))

        md3lib.write(
            os.path.join(progs_dir, f"veh_{kind}_hood.md3"),
            dict(name=f"veh_{kind}_hood", surfaces=build_single_part_md3_surface(vdata["parts"]["hood"], sh_burn)),
        )
        md3lib.write(
            os.path.join(progs_dir, f"veh_{kind}_door.md3"),
            dict(name=f"veh_{kind}_door", surfaces=build_single_part_md3_surface(vdata["parts"]["door_l"], sh_intact)),
        )
        md3lib.write(
            os.path.join(progs_dir, f"veh_{kind}_extra.md3"),
            dict(name=f"veh_{kind}_extra", surfaces=build_single_part_md3_surface(vdata["parts"]["extra_part"], sh_intact)),
        )
        md3lib.write(
            os.path.join(progs_dir, f"veh_{kind}_bumper.md3"),
            dict(name=f"veh_{kind}_bumper", surfaces=build_single_part_md3_surface(vdata["parts"]["bumper_f"], sh_intact)),
        )

    # Shared shrapnel chunks (using scorched truck/van/coupe/sedan shards) + 20-frame core starburst!
    for idx, k_src in enumerate(KINDS, start=1):
        p_sh = all_veh[k_src]["parts"][f"shrap_{idx}"]
        md3lib.write(
            os.path.join(progs_dir, f"veh_shrap{idx}.md3"),
            dict(name=f"veh_shrap{idx}", surfaces=build_single_part_md3_surface(p_sh, f"progs/veh_{k_src}_burn")),
        )

    blast_surfs = build_blast_burst_md3_surfaces(all_veh["truck"], sims["truck"], "progs/veh_truck_burn", "progs/veh_blast_flash")
    md3lib.write(os.path.join(progs_dir, "veh_blast.md3"), dict(name="veh_blast", surfaces=blast_surfs))

    np.savez_compressed(SIM_CACHE_NPZ, **cache_dict)
    print(f"Saved simulation cache: {SIM_CACHE_NPZ}")
    print("All 4 vehicle GLBs and DarkPlaces MD3 assets built successfully!")


if __name__ == "__main__":
    main()
