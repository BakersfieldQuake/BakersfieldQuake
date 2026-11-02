"""Master asset builder for the "WHERE'S THE DISK?" (LOL.BAT / NET SEND) gun in BakersfieldQuake.

Regenerates and installs all 3D MD3 models, skins, procedural textures, fallback sprite, shader,
frame-map documentation, and DarkPlaces effectinfo.txt block:

  Models installed to BakersfieldQuake/progs/:
    - progs/v_netsend.md3          First-person viewmodel (60 frames, 2 surfaces: disk + Ranger hand)
    - progs/netsend_pc.md3         World deployable 90s beige CRT PC (50 frames, 4 surfaces)
    - progs/netsend_pc.md3_0.skin .. _6.skin   Deterministic CRT screen state skins (self.skin = 0..6)
    - progs/netsend_arc.md3        3D additive crackling lightning arcs (8 frames: 0..7)
    - progs/netsend_disk.md3       Lone 3.5" LOL.BAT disk stuck in floor / thrown (8 frames: 0..7)
    - progs/netsend_arc.spr        Quake IDSP 8-frame lightning sprite fallback

  Shaders & Effects:
    - scripts/netsend.shader       Lit diffuse + CRT multi-stage glow + additive arc shaders
    - effectinfo.txt               netsend_zap / netsend_shot / netsend_pop between begin/end markers
                                   (backs up effectinfo.txt -> effectinfo.txt.pre_netsend first)

================================================================================
FRAME MAP & QC INTEGRATION REFERENCE (also written to source/mm_tools/netsend_frames.txt)
================================================================================

1. progs/v_netsend.md3  (First-person viewmodel, 60 frames @ ~10-12 fps)
   Origin: Quake eye (0, 0, 0), +X forward, +Y left, +Z up. Held in lower-right, clear of crosshair.
   Frames  0-39 : Seamless smug idle loop (40 frames):
                    0-7   relaxed idle hold, "LOL.BAT" paper label facing player
                    8-22  spins disk between fingers & flips 180 deg (frames 14-16 show back metal shutter & spindle hub), flips back
                    23-33 tilts disk in to inspect "LOL.BAT" label & gives two smug nods
                    34-39 settles seamlessly back into frame 0
   Frames 40-47 : Wind-up and hard downward-forward throw at floor:
                    40-42 arm & wrist draw up-back-right
                    43    explosive downward whip, disk releasing from fingertips
                    44    DISK RELEASE MOMENT — spawn world disk here! Hand is empty from frame 44 onward
                    45-47 downward throw follow-through, open empty hand
   Frames 48-53 : Empty-hand follow-through & recovery (hand empty)
   Frames 54-59 : Reload:
                    54-55 empty hand loose shake-out
                    56-59 fresh "LOL.BAT" disk slides up from bottom-right pocket & snaps into idle hold (loops to 0)

2. progs/netsend_pc.md3  (World deployable 90s beige CRT PC, 50 frames @ ~10 fps)
   Origin: (0, 0, 0) on floor (z = 0) at exact centre of ~30x30 base footprint (+X = screen/keyboard front).
   Height: ~63.2 Quake units to antenna tips (55.0 to top of CRT bezel). Suggested hull: '-16 -16 0' .. '16 16 60'.
   Spinning: Do not bake yaw; turn entity angles_y in QC — footprint is balanced round (0, 0) with zero wobble.
   Frames  0-9  : Materialize — lone angled LOL.BAT disk in floor (frame 0) -> PC pops out w/ stretch (5) & squash (7) -> rest (9).
   Frames 10-19 : Boot — green Power LED turns on (10), CRT degauss shake (10-14), amber Floppy LED flickers (11-19).
   Frames 20-39 : Active loop (20 frames, seamless 39 -> 20) — 8 keyboard key clusters visibly hammered by ghosts,
                  CRT hum/jitter, 4 rabbit-ear/whip antennas twitch & whip.
   Frames 40-49 : Shutdown — death sputter (40-41), LEDs off, floppy pops slightly out, CRT & case slump, antennas droop (49).

   CRT Screen Sync (via DP_GFX_SKINFILES progs/netsend_pc.md3_0.skin .. _6.skin — set self.skin in QC):
     self.skin = 0 : (Default) Active looping hacking/typing screen ("NET SEND * LOL", "NET SEND * WHERE'S THE DISK?",
                     "MESSAGE SENT [OK]", scrolling fake hex & live blinking cursor, 16-frame animmap + CRT glow stage)
     self.skin = 1 : Black screen / CRT off (use during frames 0-9 materialize, and at frame 49 dead)
     self.skin = 2 : Power-on CRT warm-up & white-noise static flicker (use at frames 10-11)
     self.skin = 3 : "INITIALIZING BATCH FILE..." (use at frames 12-14)
     self.skin = 4 : "C:\\> LOL.BAT" (use at frames 15-16)
     self.skin = 5 : "NET SEND * LOL" (use at frames 17-19, then switch to self.skin = 0 at frame 20!)
     self.skin = 6 : CRT shutdown collapse line -> central white phosphor dot (use at frames 40-48, then skin = 1 at 49)

   Antenna Tip Local Coordinates (for spawning outbound NET SEND beams / effects via makevectors(pc.angles)):
     Top-Left Rabbit Ear  : '+2.6 +10.4 62.8'   (2.6 * v_forward - 10.4 * v_right + '0 0 62.8')
     Top-Right Rabbit Ear : '+2.6 -10.4 62.8'   (2.6 * v_forward + 10.4 * v_right + '0 0 62.8')
     Left Side Case Whip  : '+0.6 +14.8 50.2'   (0.6 * v_forward - 14.8 * v_right + '0 0 50.2')
     Right Side Case Whip : '+0.6 -14.8 50.2'   (0.6 * v_forward + 14.8 * v_right + '0 0 50.2')

3. progs/netsend_arc.md3  (3D additive blue-white crackling electricity, 8 frames: 0..7)
   Origin matches netsend_pc.md3 (0, 0, 0 on floor). Spawn an effect entity with model "progs/netsend_arc.md3",
   keep arc.origin = pc.origin and arc.angles = pc.angles, and cycle arc.frame = (arc.frame + 1) & 7 while active!
   Fallback sprite: progs/netsend_arc.spr (8 frames). Particle effects: pointparticles(particleeffectnum("netsend_zap"), ...).

4. progs/netsend_disk.md3  (Optional world floppy disk, 8 frames: 0..7)
   Frame 0   : Flat horizontal disk (for flying thrown disk projectile)
   Frame 1   : Disk stuck at ~68-deg angle in floor (z = 0 at embedded lower corner, LOL.BAT facing +X)
   Frames 2-7: Stuck disk vibrating with electric tremor right before netsend_pc.md3 pops out

Usage:
    python3.13 source/mm_tools/build_netsend_assets.py
"""
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGS = os.path.join(MOD, "progs")
SCRIPTS = os.path.join(MOD, "scripts")

sys.path.insert(0, HERE)
import md3lib
import netsend_models
import netsend_textures


def verify_md3_limits(label, model_dict, tri_budget=None):
    nf = model_dict["nframes"]
    assert 1 <= nf <= 1024, f"{label}: invalid frame count {nf}"
    assert 1 <= len(model_dict["surfaces"]) <= 32, f"{label}: invalid surface count"
    tot_v, tot_t = 0, 0
    gmin = [1e9, 1e9, 1e9]
    gmax = [-1e9, -1e9, -1e9]
    for s in model_dict["surfaces"]:
        assert len(s["name"]) < 64 and len(s["shader"]) < 64
        nv = len(s["st"])
        nt = len(s["tris"])
        assert nv <= 4096, f"{label}/{s['name']}: {nv} verts > 4096 MD3 limit"
        assert nt <= 8192, f"{label}/{s['name']}: {nt} tris > 8192 MD3 limit"
        assert len(s["frames"]) == nf, f"{label}/{s['name']}: frame count mismatch"
        for fi, (vv, nn) in enumerate(s["frames"]):
            assert len(vv) == nv and len(nn) == nv
            av = np.asarray(vv, dtype=np.float64)
            an = np.asarray(nn, dtype=np.float64)
            assert np.all(np.isfinite(av)) and np.all(np.isfinite(an)), f"NaN/Inf in {label} frame {fi}"
            assert np.all(np.abs(av) < 500.0), f"{label} frame {fi} exceeds +/-500 MD3 16-bit safe range"
            for k in range(3):
                gmin[k] = min(gmin[k], float(av[:, k].min()))
                gmax[k] = max(gmax[k], float(av[:, k].max()))
        tot_v += nv
        tot_t += nt
    if tri_budget is not None:
        assert tot_t <= tri_budget, f"{label}: {tot_t} tris exceeds budget {tri_budget}"
    print(
        f"  [OK] {label:22s}: {len(model_dict['surfaces'])} surf, {tot_v:4d} verts, {tot_t:4d} tris, "
        f"{nf:2d} frames | bounds ({gmin[0]:.1f},{gmin[1]:.1f},{gmin[2]:.1f})..({gmax[0]:.1f},{gmax[1]:.1f},{gmax[2]:.1f})"
    )
    return tot_v, tot_t, gmin, gmax


def write_skin_files():
    """Writes DP_GFX_SKINFILES progs/netsend_pc.md3_0.skin .. _6.skin with all 4 surfaces explicitly bound."""
    skin_shaders = [
        (0, "progs/netsend_scr_loop"),   # Default: active hacking/typing loop
        (1, "progs/netsend_scr_off"),    # Off (black CRT glass)
        (2, "progs/netsend_scr_noise"),  # Power-on white-noise warm-up flicker
        (3, "progs/netsend_scr_init"),   # INITIALIZING BATCH FILE...
        (4, "progs/netsend_scr_lol"),    # C:\> LOL.BAT
        (5, "progs/netsend_scr_first"),  # NET SEND * LOL
        (6, "progs/netsend_scr_dot"),    # Shutdown CRT white phosphor dot collapse
    ]
    for idx, scr_sh in skin_shaders:
        skin_path = os.path.join(PROGS, f"netsend_pc.md3_{idx}.skin")
        lines = [
            "netsend_pc_body,progs/netsend_pc_body",
            "netsend_disk,progs/netsend_disk",
            f"netsend_screen,{scr_sh}",
            "netsend_leds,progs/netsend_leds",
            "",
        ]
        with open(skin_path, "w", encoding="ascii", newline="\n") as f:
            f.write("\n".join(lines))


def write_shader_file():
    os.makedirs(SCRIPTS, exist_ok=True)
    shader_path = os.path.join(SCRIPTS, "netsend.shader")

    loop_maps = " ".join(f"progs/netsend_s_l{i:02d}" for i in range(16))

    def crt_shader(name, stage1_line):
        # Single-stage shader required by DarkPlaces Q3 shader loader (phosphor bloom & scanlines baked into PNGs)
        return (
            f"{name}\n"
            "{\n"
            "\tcull none\n"
            "\t{\n"
            f"\t\t{stage1_line}\n"
            "\t\trgbGen identity\n"
            "\t}\n"
            "}\n"
        )

    blocks = [
        "// written by source/mm_tools/build_netsend_assets.py\n",
        "progs/netsend_disk\n{\n\tcull none\n\t{\n\t\tmap progs/netsend_disk\n\t\trgbGen lightingDiffuse\n\t}\n}\n",
        "progs/netsend_hand\n{\n\tcull none\n\t{\n\t\tmap progs/netsend_hand\n\t\trgbGen lightingDiffuse\n\t}\n}\n",
        "progs/netsend_pc_body\n{\n\tcull none\n\t{\n\t\tmap progs/netsend_pc_body\n\t\trgbGen lightingDiffuse\n\t}\n}\n",
        "progs/netsend_leds\n{\n\tcull none\n\t{\n\t\tmap progs/netsend_leds\n\t\trgbGen identity\n\t}\n}\n",
        "progs/netsend_arc\n{\n\tcull none\n\t{\n\t\tmap progs/netsend_arc\n\t\tblendfunc add\n\t\trgbGen identity\n\t}\n}\n",
        crt_shader("progs/netsend_scr_off",   "map progs/netsend_s_off"),
        crt_shader("progs/netsend_scr_noise", "animmap 14 progs/netsend_s_n0 progs/netsend_s_n1 progs/netsend_s_n2"),
        crt_shader("progs/netsend_scr_init",  "animmap 4 progs/netsend_s_init0 progs/netsend_s_init1"),
        crt_shader("progs/netsend_scr_lol",   "animmap 4 progs/netsend_s_lol0 progs/netsend_s_lol1"),
        crt_shader("progs/netsend_scr_first", "animmap 3 progs/netsend_s_fst0 progs/netsend_s_fst1"),
        crt_shader("progs/netsend_scr_loop",  f"animmap 6 {loop_maps}"),
        crt_shader("progs/netsend_scr_dot",   "animmap 3 progs/netsend_s_dot0 progs/netsend_s_dot1"),
    ]
    with open(shader_path, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(blocks))
    print(f"  [OK] Shader written         : {shader_path}")


def install_effectinfo():
    fx_path = os.path.join(MOD, "effectinfo.txt")
    backup_path = fx_path + ".pre_netsend"
    if not os.path.exists(backup_path):
        shutil.copy2(fx_path, backup_path)
        print(f"  [OK] Backed up effectinfo   : {backup_path}")

    begin = b"// ---- NetSend begin"
    end = b"// ---- NetSend end"
    raw = open(fx_path, "rb").read()
    if begin in raw and end in raw:
        raw = raw[:raw.index(begin)].rstrip(b"\r\n") + b"\r\n" + raw[raw.index(end) + len(end):].lstrip(b"\r\n")

    add = open(os.path.join(HERE, "netsend_effectinfo.txt"), "rb").read()
    add = add.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    out = raw.rstrip(b"\r\n") + b"\r\n\r\n" + begin + b"\r\n" + add + end + b"\r\n"
    open(fx_path, "wb").write(out)
    print(f"  [OK] Updated effectinfo.txt : markers {begin.decode()} .. {end.decode()}")


def write_frame_map_doc(stats):
    doc_path = os.path.join(HERE, "netsend_frames.txt")
    txt = f"""WHERE'S THE DISK? (LOL.BAT / NET SEND) - MODEL & FRAME MAP FOR QC
Generated by source/mm_tools/build_netsend_assets.py

================================================================================
MODEL SUMMARY & TRIANGLE COUNTS
================================================================================
  progs/v_netsend.md3    : {stats['vm'][1]:4d} tris, {stats['vm'][0]:4d} verts, 60 frames (1 surface, realistic hand + LOL.BAT atlas)
  progs/netsend_pc.md3   : {stats['pc'][1]:4d} tris, {stats['pc'][0]:4d} verts, 50 frames (4 surfaces, 7 skins)
  progs/netsend_arc.md3  : {stats['arc'][1]:4d} tris, {stats['arc'][0]:4d} verts,  8 frames (1 additive surface)
  progs/netsend_disk.md3 : {stats['disk'][1]:4d} tris, {stats['disk'][0]:4d} verts,  8 frames (1 surface)
  progs/netsend_arc.spr  : 64x64 8-frame Quake IDSP sprite fallback

================================================================================
1. VIEWMODEL: progs/v_netsend.md3 (60 frames, ~10-12 fps)
================================================================================
  Frames  0 - 39 : IDLE LOOP (40 frames, seamless 39 -> 0)
    0 -  7       : Relaxed smug hold in lower-right; "LOL.BAT" white paper label faces player
    8 - 22       : Twirls/spins disk between fingers & flips 180 deg:
                     - Frames 14 - 16 pause showing the BACK (brushed steel shutter + metal spindle hub)
                     - Frames 17 - 22 flip cleanly back to "LOL.BAT" front
   23 - 33       : Tilts disk closer to inspect "LOL.BAT" label & gives two smug nods
   34 - 39       : Smooth return to frame 0

  Frames 40 - 47 : WIND-UP & THROW (8 frames)
   40 - 42       : Arm & wrist draw back/up-right
   43            : Hard downward-forward whip toward floor
   44            : RELEASE FRAME — spawn world disk / deployable here! Hand is empty from 44 onward
   45 - 47       : Downward throw follow-through, empty open hand

  Frames 48 - 53 : FOLLOW-THROUGH (6 frames, empty hand recovers)
  Frames 54 - 59 : RELOAD (6 frames)
   54 - 55       : Empty hand loose wrist shake-out
   56 - 59       : Fresh "LOL.BAT" disk slides up from bottom-right & snaps into frame-0 idle grip

  Combat+ Viewmodel Helper Note (custom_effects.qc):
    In BakersfieldQuake, `v_weapon_position_think` (source/qc_combat_decomp/custom_effects.qc ~L2425)
    drives a `viewmodelforclient` entity when `weapon_position_fully_adjustable` is enabled (or via
    `FunGun_VModel` if wired into `IT_FUNGUN`). Set `setmodel(self, "progs/v_netsend.md3");
    self.origin = '0 0 0'; self.angles = '0 0 0';` alongside `self.owner.weaponframe`.

================================================================================
2. WORLD DEPLOYABLE PC: progs/netsend_pc.md3 (50 frames, ~10 fps)
================================================================================
  Origin   : (0, 0, 0) at exact centre of base on floor (z = 0). Front (+screen/+keyboard) faces +X.
  Size     : ~29 x 30 footprint, ~63.2 tall to antenna tips (55.0 to top of CRT). Hull: '-16 -16 0' .. '16 16 60'.
  Rotation : Turn self.angles_y in QC while active (yaw rotation around base centre has zero wobble).

  Vertex Frames:
    0 -  9 : MATERIALIZE — frame 0 is the lone LOL.BAT disk stuck in the floor; frames 1-9 pop the PC up
             out of the disk with stretch overshoot (frame 5) and squash settle (frame 7) -> upright (frame 9).
   10 - 19 : BOOT — green Power LED turns on (frame 10), CRT degauss shake (10-14), amber Floppy LED flickers
             (frames 11, 12, 14, 15, 17, 18, 19) while reading the half-inserted LOL.BAT disk.
   20 - 39 : ACTIVE LOOP (20 frames, seamless 39 -> 20) — 8 keyboard keycap clusters visibly depress as if
             typed by ghosts, CRT hums/jitters, 4 rabbit-ear & side-whip antennas twitch.
   40 - 49 : SHUTDOWN — electric sputter (40-41), LEDs turn off, floppy pops slightly out, CRT & case slump,
             all 4 antennas droop (frame 49).

  CRT Screen Skins (progs/netsend_pc.md3_0.skin .. _6.skin — switch via `self.skin` in QC):
    self.skin = 1 : Black screen / CRT off                -> use on frames  0 -  9 (materialize) & frame 49 (dead)
    self.skin = 2 : CRT warm-up & white-noise flicker     -> use on frames 10 - 11
    self.skin = 3 : "INITIALIZING BATCH FILE..."          -> use on frames 12 - 14
    self.skin = 4 : "C:\\> LOL.BAT"                       -> use on frames 15 - 16
    self.skin = 5 : "NET SEND * LOL"                      -> use on frames 17 - 19
    self.skin = 0 : Active live-typing hacking loop       -> use on frames 20 - 39 (also default skin 0!)
                    (scrolling fake hex + "NET SEND * LOL" + "NET SEND * WHERE'S THE DISK?" + "MESSAGE SENT [OK]")
    self.skin = 6 : CRT collapse line -> white dot        -> use on frames 40 - 48 (shutdown)

  Antenna Tip Local Offsets (transform via makevectors(pc.angles): org + x*v_forward - y*v_right + '0 0 z'):
    0 (Top-Left Rabbit Ear)  : x = +2.6, y = +10.4, z = 62.8
    1 (Top-Right Rabbit Ear) : x = +2.6, y = -10.4, z = 62.8
    2 (Left Case Whip)       : x = +0.6, y = +14.8, z = 50.2
    3 (Right Case Whip)      : x = +0.6, y = -14.8, z = 50.2

================================================================================
3. ELECTRICITY & FLOOR DISK
================================================================================
  progs/netsend_arc.md3  : Frames 0 - 7 (cycle at ~15-20 fps). Same (0,0,0) floor origin as netsend_pc.md3;
                           setorigin(arc, pc.origin); arc.angles = pc.angles;
  progs/netsend_disk.md3 : Frame 0 = flat flying disk; Frame 1 = stuck at ~68 deg in floor; Frames 2-7 = tremor.
  effectinfo.txt         : netsend_zap (ambient crackle), netsend_shot (beam/packet trail), netsend_pop (materialize/die).
"""
    with open(doc_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    print(f"  [OK] Frame map doc written  : {doc_path}")


def main():
    import build_netsend_vm_remake

    os.makedirs(PROGS, exist_ok=True)
    print("1. Generating procedural textures & Quake fallback sprite...")
    netsend_textures.build_all_netsend_textures(PROGS)

    print("2. Building multi-frame MD3 models (delegating v_netsend.md3 + netsend_hand.png to Blender realistic hand pipeline)...")
    build_netsend_vm_remake.main()
    vm_md3 = md3lib.read(os.path.join(PROGS, "v_netsend.md3"))
    pc_md3, _ = netsend_models.build_netsend_pc_md3()
    arc_md3, _ = netsend_models.build_netsend_arc_md3()
    dsk_md3, _ = netsend_models.build_netsend_disk_md3()

    stats = {
        "vm": verify_md3_limits("progs/v_netsend.md3", vm_md3, tri_budget=3000),
        "pc": verify_md3_limits("progs/netsend_pc.md3", pc_md3, tri_budget=4000),
        "arc": verify_md3_limits("progs/netsend_arc.md3", arc_md3, tri_budget=1000),
        "disk": verify_md3_limits("progs/netsend_disk.md3", dsk_md3, tri_budget=1000),
    }

    md3lib.write(os.path.join(PROGS, "netsend_pc.md3"), pc_md3)
    md3lib.write(os.path.join(PROGS, "netsend_arc.md3"), arc_md3)
    md3lib.write(os.path.join(PROGS, "netsend_disk.md3"), dsk_md3)

    print("3. Writing .skin variants, shader, effectinfo.txt & frame map...")
    write_skin_files()
    write_shader_file()
    install_effectinfo()
    write_frame_map_doc(stats)
    print("Done! All 'WHERE'S THE DISK?' assets installed cleanly.")


if __name__ == "__main__":
    main()
