# Rocket Rider Plane — Engineering & 3-Variant Design Plan

**Status:** Pre-vote 3-variant design & animation spec (**no `.qc`, `progs.dat`, or `.pk3` files modified yet**)  
**Shared Core:** `source/mm_tools/rocket_rider/common.py`  
**Vote Showcase:** `source/mm_tools/out/rocket_rider/rocket_rider_vote.html` (8.01 MB self-contained 3-column WebGL2 vote studio packing all 3 × 100-frame MD3s and 10 deduplicated textures, built by `source/mm_tools/rocket_rider/build_vote_html.py`)

---

## 1. Concept: "He's Just Holding On!"

The **Rocket Rider** is a fast, flyable Quake plane/sky-mount inspired directly by **Winged Breezy-Hair John** (`misc_vehicle_johnbird`), replacing the winged head with an oversized rideable Quake rocket straddled by the authentic **1996 Quake 1 Ranger** (`source/mm_tools/id1/player.mdl`).

- **Core visual gag:** Unlike a cockpit jet, the Ranger simply straddles the rocket body, knees clamped around the fuselage, boots braced on pegs/fins, and **both hands gripping tight** — leaning into dives, hunkering through afterburner boost, jolting white-knuckled when shot, and getting pinned back holding on for dear life during supersonic `info_skypad` launches.
- **Scale & readability:** Fuselage length `~105–135 u` (radius `~11–16 u`), Ranger at `scale = 1.18` (`~34.5 u` seated height, matching `gokart_driver.py`), giving a bold unmistakable silhouette at Winged John's `148 u` third-person chase camera and `[-28 -36 -4] .. [28 36 58]` flight hull.
- **Axes:** Standard Quake/MD3 (`+X` forward nose, `+Y` port/left, `+Z` up). Flying frames hover around `Z ~ 28–38 u`; `idle_ground` (`56..67`) rests cleanly on `Z = 0.0`.

---

## 2. John Bird-Modeled Animation Schedule (7 Clips, 100 Frames)

Every clip is a seamless periodic loop (`phase = 2*pi*k / count`, wrapping cleanly from `count - 1` back to `0` for hardware vertex interpolation in both WebGL2 and DarkPlaces/Zircon):

| Frames | Count | Clip ID | Default FPS | John Bird Reference | Flight State & Rider / Flame Behavior |
|---|---:|---|---:|---|---|
| `0..15` | 16 | `fly_cruise` | 14 | `fly_breezy (0..15)` | Level cruising flight (`780 u/s`). Steady rhythmic thrust hum, gentle aerodynamic roll/bob, medium orange/plasma exhaust cone, Ranger leaning forward gripping tight. |
| `16..31` | 16 | `fly_boost` | 22 | `fast_fly (100..115)` | Shift/carve boost (`>= 950 u/s`). Blazing elongated afterburner + Mach shock diamonds + subtle slipstream ribbons, high-frequency airframe vibration, Ranger crouched low holding on. |
| `32..43` | 12 | `fly_hover` | 12 | `hover_flutter (32..47)` | Hover / climb (`climb_in > 0.2 || hspd < 230`). Nose pitched `+18..24°` up, buoyant altitude bob, pulsing hover exhaust, Ranger braced upright holding steady. |
| `44..55` | 12 | `swoop_dive` | 16 | `swoop_dive (48..59)` | Steep downward dive (`velocity_z < -420`). Nose pitched `-20..-28°` down, streamlined trailing plume, Ranger tucked chest-down tight over the rocket nose. |
| `56..67` | 12 | `idle_ground` | 8 | `perch_breeze (60..71)` | Parked / landed on `Z = 0.0`. Low warm pilot-light exhaust flicker, soft idle engine thrum, relaxed seated grip ready for launch. |
| `68..83` | 16 | `hit_flail` | 26 | `hit_flail (116..131)` | Damage reaction (`JB_Pain`, `0.65 s` window). Erratic roll/pitch bucking wobble, sputtering asymmetrical flame, Ranger jolted & hanging on white-knuckled (hands still clamped!). |
| `84..99` | 16 | `skypad_hyper` | 30 | `skypad_hyper (132..147)` | Supersonic `info_skypad` arc (`>= 1500 u/s`). Massive roaring hyper-afterburner + intense shock diamonds + full slipstream speed ribbons, Ranger stretched backward holding on for dear life! |

---

## 3. Canonical Quake 1 Ranger Rig & Additive Flame Architecture

### 3.1 Quake 1 Ranger Rig (`QuakeRangerRig` in `common.py`)
- **CI-safe source:** `source/mm_tools/id1/player.mdl` (exact 1996 Quake 1.06 `IDPO v6`, 296×194 indexed Quake-palette skin decoded with embedded 768-byte `palette.lmp`, 2 px edge-dilated and upscaled 2× to `ranger_skin.png` at 592×388).
- **Mesh extraction:** Isolates the 149-vertex / 294-triangle Ranger body from frame 17 (`axstnd1`, arms free at sides, head straight), strips shotgun/axe/muzzle flash, straightens the `-8°` combat yaw, resolves MDL `onseam` UV splits into 218 MD3 vertices, and reverses MDL CW winding `(v0, v2, v1)` to verified CCW outward MD3 normals.
- **Pose solver:** `QuakeRangerRig.pose_frame(...)` drives independent torso pitch/yaw/roll + upper-body `lean_x`, upright-space head look, and twist-free 3-segment limb chains (`_pose_limb_chain_scaled`) with proportional radial scaling and shoulder/hip socket blending — landing gloved hands and boots within `< 0.5 u` of exact handlebar/fuselage/peg targets.

### 3.2 Multi-Layer Additive Rocket Flames (`FlameBuilder` & `make_flame_texture`)
- **Works identically in WebGL2 vote studio and DarkPlaces/Zircon** with zero engine-only hacks:
  - Dedicated additive MD3 surface (`unlit: 1, additive: 1`, `blendfunc add`, `rgbGen identity`, `cull none`) using a deterministic 512×512 4-quadrant RGB atlas fading to pure `(0, 0, 0)` on all edges and tips:
    1. **Q1:** Turbulent outer exhaust cone (pulsing harmonic waves + tip whip).
    2. **Q2:** Inner incandescent Mach shock-diamond core.
    3. **Q3:** 4 crossed longitudinal flame fin cards so side, top, and rear-3/4 views keep full blazing volume.
    4. **Q4:** 6–8 supersonic slipstream speed ribbons around the rocket (6 on V1/V2, 8 wingtip/V-tail ribbons on V3; collapsed to zero-area inside the nozzle during `idle_ground`/`fly_cruise`/`fly_hover`, expanded and scrolling seamlessly during `fly_boost` and `skypad_hyper`).
  - Supports multi-nozzle arrays out of the box (single main bell for V1, main + twin angled flank verniers for V2, triple core + strap-on booster nozzles for V3).
- **Post-vote DarkPlaces particles:** Layer existing `effectinfo.txt` emitters (`veh_boost` L21297, `jb_fx_hairfire` L21739, `TR_ROCKET` L5061) at nozzle world origin on top of the 3D additive plume.

---

## 4. The 3 Vote Variants (Final Built Assets)

All 3 variants ship as 3-surface, 100-frame MD3s (`rocket_body` + `glowTex`, `ranger_body`, `flame_fx` additive 2-sided) packed into the 8.01 MB self-contained 3-column WebGL2 vote page (`12,259` total verts / `17,206` total tris across V1–V3; every variant rests at `idle_ground z_min = 0.00`):

| Variant | ID & Title | Style, Posture & Signature Details | Flame & Glow | Verts / Tris | Bounds (`fly` / `idle` in Quake u) |
|---|---|---|---|---:|---|
| **V1** | `v1_classic` — **Classic Quake Munition** | 112 u upscaled 1996 id1 `progs/missile.mdl` warhead (`r=13.5 u`) with stepped yellow/black hazard collar, brass/copper fuse tip, riveted olive-drab & gunmetal plates stenciled `"ID1 // BAKO-01"`, copper flank fuel lines, 4 swept `±45°` X-fins (lower tips act as landing skids), curved quilted leather saddle pad, **bolted steel U-shaped grab hoop**, and rear knurled foot-pegs for a bronco straddle. | `"classic"` single main bell plume (molten orange-amber + cream-gold Mach core, 6 ribbons) + `v1_rocket_glow.png` furnace throat. | `3,590 v / 4,870 t` | Fly `[-56.3, -23.4, 9.1]`..`[56.0, 23.4, 83.7]`; Idle `[-56.9, -22.5, 0.0]`..`[55.7, 22.4, 75.6]` |
| **V2** | `v2_acme` — **Retro ACME Rocket** | 105.6 u plump Art-Deco cigar rocket (`r=15.6 u`) with **glossy crimson warhead + chrome needle spire**, cream-and-crimson checkerbands, `"ACME // Q1-EXP"` flank badges, 2 riveted chrome rings, **bolted forward nose-collar strap** (low bear-hug cling + SkyPad windsock legs, no saddle), 4 curved retro-swept fins with **chrome bullet fin pods**, and 2 angled flank vernier thrusters. | `"cartoon"` 3-nozzle fireball plume (main bell + twin side verniers, vivid red-orange + lemon-yellow core, 6 ribbons) + `v2_rocket_glow.png` incandescent nozzle/vernier throats. | `4,367 v / 6,662 t` | Fly `[-52.4, -28.8, 6.2]`..`[54.6, 28.8, 73.3]`; Idle `[-51.0, -27.5, 0.0]`..`[54.6, 27.5, 61.6]` |
| **V3** | `v3_twin` — **Twin-Booster Tactical Afterburner** | 128 u sleek stealth-charcoal cruise missile (`r=11.5 u`) stenciled `"BAKO-X3 // MACH"`, flanked by twin strap-on solid boosters (`r=6.2 u`) on bolted cross-struts, swept delta winglets, **canted twin V-tail**, **stitched leather saddle** + booster stirrups, and **twin forward bullhorn grab handles + HUD riser** for an upright dirt-bike straddle. | `"plasma"` **triple-nozzle** afterburner (core + twin boosters, cobalt-cyan + blue-white-gold Mach diamonds, asymmetric hit misfire, **8 slipstream ribbons**) + `v3_rocket_glow.png` throats, radiator louvers & dash HUD. | `4,302 v / 5,674 t` | Fly `[-62.3, -44.6, 19.4]`..`[66.0, 44.6, 86.4]`; Idle `[-62.0, -43.3, 0.0]`..`[66.0, 43.3, 61.6]` |

---

## 5. Post-Vote Packaging & QuakeC Integration Plan (`AGENTS.md` Compliant)

1. **Zero base pk3 edits:** Never modify `BakersfieldQuake/bakersfield.pk3` or `quake15/q15.pk3`.
2. **Reproducible overlay pk3:** Add `source/mm_tools/rocket_rider/build_rocketrider_pk3.py` (modeled on `source/mm_tools/build_gokart_pk3.py`) producing `BakersfieldQuake/zz_rocketrider.pk3`:
   - `progs/rocket_rider.md3` + `progs/rocket_rider.md3_0.skin` (+ optional damaged `_1.skin`)
   - `progs/rr_*.png` textures + `scripts/rocket_rider.shader`
   - Deterministic `ZipInfo(name, (1980, 1, 1, 0, 0, 0))`, `create_system = 3`, `external_attr = 0o644 << 16`, sorted entries, `ZIP_STORED` for `.png`/`.wav`, `ZIP_DEFLATED` (`compresslevel=6`) for `.md3`/`.skin`/`.shader`, pure Python 3.12 + pinned `numpy==2.5.4 pillow==13.0.0` (no `scipy`).
   - Add a cached build step to `.github/workflows/build-zip.yml` hashing every read script and `source/mm_tools/id1/player.mdl`.
3. **QuakeC vehicle integration (`source/qc_combat_decomp/`):**
   - Implement `rocket_rider_defs.qc` + `rocket_rider.qc` mirroring `john_bird.qc` (3D flight controller, Shift afterburner boost, mouse-carve speed, `JB_SlideMove`-style hull sliding, `info_skypad` ballistic arc support, `hit_flail` pain override, `veh_boost`/`TR_ROCKET` exhaust particles, and 3rd/1st-person chase cam toggle).
   - Keep compiled `progs.dat` as a loose file (diffs cleanly via the differential updater).
