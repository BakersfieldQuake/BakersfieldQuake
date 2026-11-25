# Bakersfield-ish — Independent Final Live In-Game Zircon Verification Report (Audit #4 of 4)

**Auditor:** `audit-v2-4` (Fresh Independent Live In-Game Verification — Zero Prior Build History, Zero Prior Audit Reports Read)  
**Date:** 2026-11-25  
**Target Production Artifacts Verified Live:**
- `maps/bakersfieldish.bsp` (40,851,944 bytes, `2026-11-25 17:42:46`, `BSP2`, 89 models, 1,567 entities, world Z `-431..7211 u`)
- `maps/bakersfieldish.lit` (14,382,632 bytes, `2026-11-25 17:42:45`)
- `progs.dat` (3,773,670 bytes, `2026-11-25 17:17:03`, CRC `15907`)
- `csprogs.dat` (617,526 bytes, `2026-11-25 13:32:26`, CRC `2546`)
- `zz_bakersfieldish.pk3` (440,516 bytes, `2026-11-25 17:04:43`)

**Engine & Isolation Compliance (`CLAUDE.md`):**
- Binary: `G:\Quake\Combat\engine\zircon_beta_gcc.exe` (CWD `G:\Quake\Combat\engine`, `-basedir G:\Quake\Combat`)
- Isolation: `-userdir %TEMP%\bako_audit_v2_4`, `-port 26098`, `-window -width 1280 -height 720 -game quake15 -game BakersfieldQuake`
- Logging: `-condebug +log_file zz_audit_v2_4_<run>.log` (no `condump`), `+defer 6 "exec audit_<run>.cfg"`, every cfg ending with `quit`, PID-only cleanup, zero concurrent Zircon instances, `G:\Quake\Combat\BakersfieldQuake\config.cfg` completely untouched (mtime `2026-11-23 10:48:29`).
- Live Screenshot Archive: `docs/bakersfieldish_audit_v2_4_shots/` (45+ live 1280×720 PNG screenshots inspected directly).

---

## Overall Verdict: **FAIL** (3 Concrete Live-Verified Defects)

Almost every core pillar of **Bakersfield-ish** passed live in-game verification in `zircon_beta_gcc.exe` with impressive fidelity: **0 missing textures/models/sounds**, **0 QC/CSQC errors**, **0 frame-1 Padre telefrag (`padre_hp == 2600`)**, **6/6 shatterable glass buildings**, **full Fox Theater clock -> collapse -> rubble -> auto-rebuild (`0` worker `droptofloor` errors) -> rebuilt Fox roof SkyPad launch**, **Padre Hotel real Garage L6 Eric Deason Cannon `1.75x` strike (`-788 HP` exact!) + rocket demolition + live rolling boulders physically bouncing the player upward & across H St (`vz=430`, `+463 u` eastward) + climbable rubble + `0` floating rooftop items**, **6/6 hands-free continuous rooftop `info_skypad` loop + Larry's Courtyard Purple Sign SkyPad + `trigger_push` + Go-Kart + Jetpack flight**, **zero floating dark beam over Front Porch Music**, and **clean Garage L6 + live walkable Catwalk #3**.

However, **3 genuine, live-reproduced defects** require fixes before shipping:

| ID | Severity | Category | Live-Verified Defect | Evidence |
|---|---|---|---|---|
| **L1** | **HIGH** | Visual / Geometry (Golden West North Edge) | **3 orphaned downtown awnings float in midair above 21st St directly north of Golden West Casino** (`dd_legbrown`, `dd_awn_redc`, `dd_awn_navy`: 48 BSP2 faces spanning `1,457 u` / `121 ft` across `x=-2244..-787`, `y=5633..5675`, `z=109..142 u`, casting floating drop shadows onto 21st St asphalt). Caused by `SLOTS["gw_a"]` dropping only to `D y=175.0 ft` (`uy=5520`), leaving the demolished building's overhanging 21st St sidewalk awnings (`D y=184.4..187.9 ft`) orphaned in midair. | `05b_golden_west_north_floating_awnings.png`, `04_golden_west_exterior_roof.png`, `hero_1_golden_west_roof.png` |
| **L2** | **HIGH** | Interactive Gameplay (Bakersfield Sign Go-Kart Ramp) | **Fallen Bakersfield Sign wreckage (`bako_sign_rubble`) is NOT rampable by Go-Karts in-game.** Although smoothly walkable on foot (`mt=3`, Z climbs `24 -> 45.9 -> 64.0 -> 60.4 -> 24.0 u`), driving `misc_gokart_5` straight North at full throttle slams nose-first into the hovering yellow vertical arch face at `y=-3240, z=18.5` and deflects sideways (`z` stuck at `18.5 u`), contradicting the HUD prompt `"SIGN DOWN ON H ST - RAMP OVER IT!"`. | `17c_sign_gokart_ramp.png`, Run 4A log L840–861 |
| **L3** | **MEDIUM** | Startup Entity Placement (`droptofloor`) | **1 live startup `droptofloor` failure on every map load:** `droptofloor at -5759.0 955.0 381.0 (#570 item_jetpack) - FIXED BADLY PLACED ENTITY`. The Great Castle watchtower `item_jetpack` (`origin -5759 955 357`) lifts `+24 u` to `z=381` with a `40×40×44 u` bbox directly into/against the decorative crimson crow's nest mast, violating the `0 startup droptofloor failures` requirement. | Run 1 log L505, Run 3 log L504, `06b_great_castle_jetpack570.png` |

**Minor Observation (non-blocking):** `zz_bakersfieldish.pk3` (`17:04:43`) predates the final `maps/bakersfieldish.bsp` (`17:42:46`), so `gfx/minimap/bakersfieldish.png` still shows a faint horizontal line over 19th St from the previously removed Nile->Tevis Sky-Bridge #1 even though the sky above Front Porch Music is 100% clear in-game (`11_front_porch_music_clear_sky.png`). Re-rendering the minimap into `zz_bakersfieldish.pk3` after the final BSP compile will keep it 100% in sync.

---

## 1. Clean Load & Asset Integrity (`+deathmatch 1 +map bakersfieldish`)

Executed in **Run 1** (`+developer 1 +maxplayers 4 +deathmatch 1 +set bm_botfill 0 +set crowd_on 0 +map bakersfieldish`, exited `rc=0` in 28.6 s):

| Check | Result | Live Log & Screenshot Proof |
|---|---|---|
| Precache & Asset Integrity | **PASS** | `CL_BeginDownloads_DP: precache finished in 0.61s (492 models, 622 sounds)` — **0 missing textures**, **0 missing models**, **0 missing sounds**. |
| QC / CSQC Runtime Errors | **PASS** | Server `progs.dat` (`crc 15907`) and client `csprogs.dat` (`crc 2546`) loaded with **0 `PR_RunError`, 0 `Host_Error`, 0 `VM_` warnings, 0 CSQC errors** across all 7 live runs. |
| Frame-1 Padre Telefrag Guard | **PASS** | Untouched DM spawn reported `bako_destruct: fox_st=0 fox_hp=200 \| padre_st=0 padre_hp=2600 \| sign_st=0 sign_hp=380 \| boulders=0 shards=0` (`padre_hp == 2600` intact!). |
| `levelshots/bakersfieldish.jpg` | **PASS** | `which`: in `zz_bakersfieldish.pk3`; `Draw_CachePic("levelshots/bakersfieldish.jpg"): frame 2: loading pic` (Run 1 L543). Visually inspected — clean H St Padre/Sign preview. |
| `gfx/minimap/bakersfieldish.png` & shader | **PASS** | `which`: `.png`, `.txt`, and `scripts/bakersfieldish_minimap.shader` all resolved in `zz_bakersfieldish.pk3`; `Draw_CachePic("gfx/minimap/bakersfieldish.png")` & `Draw_CachePic("gfx/minimap/bakersfieldish")` loaded on frame 5 (Run 1 L755–756) and rendered live in bottom-left HUD (`01_dm_spawn_hud.png`). |
| `info_skypad` & `sv_maxvelocity` | **PASS** | `impulse 60` (`SkyPad_Report`) confirmed all **11/11 `info_skypad`** entities spawned with `sv_maxvelocity=6500` (Run 1 L782–793). |
| Startup `droptofloor` Failures | **FAIL (L3)** | **1 failure** on every map load: `droptofloor at -5759.0 955.0 381.0 (#570 item_jetpack) - FIXED BADLY PLACED ENTITY` (Run 1 L505). All other 1,566 entities had 0 `droptofloor` failures. |

---

## 2. Visual & Layout Fidelity In-Game (Run 2b & Run 6 Live Inspection)

All screenshots inspected directly via `read_file` from `docs/bakersfieldish_audit_v2_4_shots/`:

| Visual Checkpoint | Verdict | Live Visual Findings |
|---|---|---|
| **H St Hero Corridor (Padre <-> Sign <-> Fox + Parking Garage)** | **PASS** | `02_hst_hero_padre_sign_fox.png`, `03_padre_garage_south_view.png`, `hero_4_hst_padre_sign_fox.png`: Padre Hotel stands faithfully on the SW corner directly opposite the 6-level Parking Garage across H St (identical `12 u/ft` scale and world XY bounds `-14111..-7399` to `1391..6731` vs `bakersfielddowntown.bsp`), the Bakersfield Sign spans H St cleanly mid-corridor, and Fox Theater rises north down H St. |
| **Golden West Casino + Flat Roof SkyPad** | **FAIL (L1)** | Core casino (`04_golden_west_exterior_roof.png`, `05_golden_west_flat_roof_close.png`, `hero_1_golden_west_roof.png`) looks great: 12-sided conical terracotta Rotunda, 45° NE portico + bronze horse monument, purple neon pylon, and dead-flat north roof deck holding SkyPad #4, Go-Kart #2, and Jetpack cleanly. **HOWEVER**, `05b_golden_west_north_floating_awnings.png` (and background of `04`/`hero_1`) exposes **Defect L1**: 3 orphaned brown/red/blue awnings hovering `9–12 ft` in midair over 21st St north of Golden West (`x=-2244..-787`, `y=5633..5675`, `z=109..142 u`). |
| **The Great Castle + Clean Indoor Kart Path** | **PASS** *(exc. L3 jetpack)* | `06_great_castle_exterior.png` & `hero_2_great_castle.png`: Castellated white CMU parapets & merlons, SW watchtower + crimson crow's nest, crimson arched barrel canopy, merlon pylon sign, and roof SkyPad #5 cleanly integrated beside PG&E tower. `07_great_castle_indoor_kart_path.png`: Wide open indoor kart corridor through the dining hall with red lattice screens, crimson swirl carpet, and unobstructed kart clearance. (`06b_great_castle_jetpack570.png` shows L3 watchtower jetpack clipping the crow's nest mast.) |
| **Larry's Warehouse + Clear Forklifts + Cut-Out Glass + Courtyard Purple Sign SkyPad** | **PASS** | `08_larrys_warehouse_exterior_courtyard.png` & `hero_3_larrys_warehouse.png`: Full B76 + Courtyard + B45/Unit 130A complex with `LARRY'S WAREHOUSE` signage, roof SkyPad #3, Bako Van, and the unmistakable courtyard **Purple Sign SkyPad #11** (`LAUNCH PAD TO GOLDEN WEST CASINO`). `09_larrys_warehouse_interior_forklifts.png`: Clear orange & blue forklifts + pallet jack down a wide concrete aisle, pallet racks, Daniel posters/CRT bay, and open roll-ups. `08b_larrys_warehouse_north_glass.png`: Crisp newly cut-out hollow glass windows punched cleanly through the north concrete wall. |
| **The Bakersfield Sign Spanning H St** | **PASS** | `10_bakersfield_sign_closeup.png`: Crisp yellow parabolic arch with upright navy `BAKERSFIELD` lettering (`bk5_bsign`), twin Spanish Mission towers with City Seal medallions, generous roadway clearance (`277 u` at crown; rockets fired at `z=225` flew straight under the arch!). |
| **Light-Handed Post-Apoc Feel & High Skybox (`Z=7200 u`)** | **PASS** | `14_skybox_high_altitude.png` & `14b_skybox_z6900_ceiling_check.png`: Subtle warm desert-dust atmospheric haze (`fog`), tasteful barricades/ramps/weathered props without cluttering sightlines. Live player physically verified at `p='-8700.0 -2000.0 6900.0'` (Run 2b L828) and Eric Cannon ejection reached `z=7139.9` (Run 4B L806) inside the compiled `Z=7211 u` skybox (2.14× taller than `bakersfielddowntown`'s `3371 u`). |
| **ZERO Floating Dark Beam over Front Porch Music** | **PASS** | `11_front_porch_music_clear_sky.png` & `11b_front_porch_music_wide.png`: Completely open blue/tan sky over Front Porch Music, Nile Theater, and 19th St — **0 floating beams**. |
| **Garage L6 Separation & Accessible Catwalk #3** | **PASS** | `12_garage_l6_layout.png`, `13_garage_l6_catwalk3_close.png`, `13b_garage_l6_johnbird_jetpack.png`: Eric Cannon (`-7404,-5520,654`) is `645 u` clear of Go-Kart #3 (`-6762,-5580,672`) and `388 u` clear of SkyPad #6; Jetpack (`-5436,-5580,674`) sits completely clear on the east deck (`528.5 u` from the `misc_vehicle_johnbird` anchor, which also intentionally self-removes since Winged John is summon-only via `impulse 98`). **Live Catwalk #3 foot walk test (Run 6 L760–778, `28_catwalk3_standing_on_deck.png`):** walked seamlessly in `mt=3` from Garage L6 deck (`-6300, -4840, 672.0`) up the south ramp (`z=686.6`), over the parapet bridge crest (`z=728.9`), down the north ramp (`z=709.3`), and onto Catwalk #3's overlook deck (`-6300, -4498.0, 681.2`). |

---

## 3. Live Interactive Gameplay Tests (Runs 3, 4A, 4B, 5, 6)

Every interactive mechanic below was triggered live in `zircon_beta_gcc.exe` using real weapons, real vehicles, and real `MOVETYPE_WALK` (`mt=3`) physics:

### 3.1 Historic Fox Theater — **PASS** (Run 3)
- **Real Rocket Clock Damage:** Firing real rockets (`impulse 7`) at `bako_fox_clock` (`-9292, 2530, 976`) dropped `fox_hp: 200 -> 60 -> 0` and triggered `fox_st=1` (Run 3 L893–900).
- **Coupled Collapse & Clean HUD:** `18_fox_collapsing.png` shows the blown-out clock belfry, hinging 2-piece clock tower, non-blinding street dust, and clean top-right HUD `FOX CLOCK HIT - TOWER COLLAPSING!`.
- **Climbable Rubble:** Settled cleanly to `fox_st=2` (`19_fox_rubble.png`, `FOX COLLAPSED - CLIMB THE RUBBLE!`, `0` floating roof props). On-foot climb test (`mt=3`) moved up the SE rubble slope (`z: 74.9 -> 76.7 -> 83.0 u`).
- **Slow Auto-Rebuild & Zero Worker `droptofloor` Errors:** Automatically transitioned `fox_st=2 -> fox_st=3` via `bako_auto_rebuild 1` (`20_fox_rebuilding.png`, `FOX REBUILDING 68%`, orange-vest `npc_bako_worker` crew visible hammering on 20th St with golden welding sparks). Verified **0 `npc_bako_worker` `droptofloor` errors** in Run 3's `developer 1` log.
- **Restored Intact & Rebuilt Roof `info_skypad` Works:** Automatically completed to `fox_st=0, fox_hp=200` (`21_fox_restored.png`) and logged `bako_roof: restored info_skypad mins='-40.0 -40.0 -26.0' maxs=' 40.0  40.0  36.0'` (Run 3 L971). Stepping onto the rebuilt Fox Roof SkyPad in `mt=3` immediately fired `Sky Pad -> Larry's Warehouse Roof` (`z` climbed to `2972.3 u`, `vz=1418 -> -1702`) and landed dead-center on Larry's Roof SkyPad, chaining automatically to `Sky Pad -> Golden West Casino Roof` (`vz=1978`, Run 3 L981–1027).

### 3.2 The Padre Hotel — **PASS** (Run 4B)
- **Real Garage L6 Eric Deason Cannon (`1.75x` Structural Splash Confirmed Numerically!):** Mounted the real Garage L6 `misc_eric_cannon` (`-7404, -5520, 654`) via `impulse 86`, launched due West (`yaw=174°`) holding `+forward` power-dive. The ICBM arced across H St (`-8965.6, -5352.4, 2010.6`) and struck Padre Hotel directly, dropping `padre_hp: 2600 -> 1812` — **exactly `-788 HP` from a single 450-peak ICBM (`450 × 1.75 = 787.5 HP`)**, triggering `PADRE HOTEL 70%` / `PADRE FACADE CRACKING (75%)` (`22a_padre_eric_cannon_hit.png`, Run 4B L779–806).
- **Real Rocket Damage & Toughness (13× Fox):** Sustained real rocket barrage from H St (`mt=3`) dealt `~108–114 HP/rocket` (`1652 -> 1217 -> 679 -> 110 -> 0 HP`), crossing the 75%, 50%, and 25% milestones with dark grey outer facade window smoke and top-right HUD (`22b_padre_mid_damage_hud.png`: `PADRE HOTEL 27%`) before triggering `padre_st=1` (Run 4B L808–880). Padre (`2,600 HP`) required 1 Eric Cannon ICBM + ~16 rockets vs Fox Clock's 2 rockets (`200 HP`).
- **Controlled Demolition & LIVE Rolling Boulder Bounce on Player:** Standing stationary on H St (`-8680.0, -5280.0, 24.0`, `mt=3`, `vz=0`) as Padre imploded (`22_padre_collapse.png`, `boulders: 2 -> 10 -> 18 -> 26`), a rolling concrete boulder struck our player at Run 4B L906:
  - **`bako_boulder: bounced player vz=430`**
  - Next tick (`PADRE_WATCH_6`): player flung upward & eastward to **`(-8484.3, -5277.9, 117.9)`, `vz=182`** (`+93.9 u` vertical lift!)
  - Touchdown (`PADRE_WATCH_7`, `23_padre_boulder_bounce.png`): **`(-8217.0, -5272.9, 45.0)`** — hurled **`+463.0 u` eastward across H St!** Multiple weathered concrete boulders are visibly rolling past the white Go-Kart (`L918: bako_boulder: bounced vehicle misc_gokart_2 vz=210`).
- **Climbable Rubble & Zero Floating Rooftop Items:** Walked on foot (`mt=3`) straight onto settled Padre rubble (`padre_st=2`), climbing `+132.2 u` (`z: 24.0 -> 77.7 -> 156.2 u`, Run 4B L937–947). Overhead inspection (`24_padre_rubble_no_floating.png`) confirms **0 floating rooftop items** across Padre's former `Z=1256` skyline (SkyPad, Go-Kart, Jetpack, and roof spawns cleanly hidden).

### 3.3 The Bakersfield Sign — **FAIL (L2: Foot Walk PASS, Go-Kart Ramp FAIL)** (Runs 4A & 6)
- **Real Rocket Damage & Topple (`PASS`):** Firing real rockets at the yellow banner (`z=320`) dropped `sign_hp: 380 -> 265 -> 0` -> `sign_st=1` (`16_sign_toppling.png`, `BAKERSFIELD SIGN TOPPLING!`, clean shear off pier stumps with sparks), settling to `sign_st=2` (`17_sign_fallen_wreckage.png`, `SIGN DOWN ON H ST - RAMP OVER IT!`, full-width dust veil).
- **On-Foot Walkability (`PASS`):** In Run 6 (`29_sign_clean_foot_walk.png`, L786–807), walking straight South->North in `mt=3` smoothly ascended and crossed the fallen sign wreckage: `y=-3400 (z=24.0) -> -3194.3 (z=45.9) -> -3082.8 (z=64.0) -> -2990.0 (z=60.4) -> -2892.0 (z=24.0)`.
- **Go-Kart Rampability (`FAIL — Defect L2`):** In Run 4A (`17c_sign_gokart_ramp.png`, L838–861), boarding H St `misc_gokart_5` (`-8700, -3843, 18.5`) and driving straight North at full throttle slammed directly into the hovering yellow vertical arch face at `y=-3239.4, z=18.5` and slid sideways along the wall (`-8881.1, -3247.3, 18.5`) with zero upward climb (`z` frozen at `18.5 u`).

### 3.4 Shatterable Glass Across 6 Buildings — **PASS (6/6)** (Runs 3 & 4A)
Every building tested individually with a real single Shotgun (`impulse 2`) blast, verified by live `shards: 0 -> 20` jump and clean shattered hollow opening screenshots:

| # | Building | BSP Pane | Pre Shards | Post Shards | Live Screenshot |
|---|---|---|---:|---:|---|
| 1 | **Padre Hotel** (H St 1F) | `*8` | `0` | **`20`** | `15_glass_1_padre.png` |
| 2 | **Nile Theater** (19th St) | `*12` | `0` | **`20`** | `15_glass_2_nile.png` |
| 3 | **Dagny's Coffee** (20th St) | `*18` | `0` | **`20`** | `15_glass_3_dagnys.png` |
| 4 | **Golden West Casino** (Rotunda) | `*45` | `0` | **`20`** | `15_glass_4_goldenwest.png` |
| 5 | **The Great Castle** (Entry Door) | `*48` | `0` | **`20`** | `15_glass_5_greatcastle.png` |
| 6 | **Larry's Warehouse** (New North Cut-Out) | `*50` | `0` | **`20`** | `15_glass_6_larrys.png` |

### 3.5 Full Traversal Suite — **PASS** (Run 5)
- **6/6 Full Rooftop `info_skypad` Loop LIVE (Hands-Free Continuous Circuit!):** Stepping onto Pad #1 (Padre Roof) in `mt=3` chained through all 6 rooftop SkyPads automatically and started Lap 2 with zero keyboard input (Run 5 L764–847, `25_skypad_rooftop_loop.png`):
  1. `Sky Pad -> Fox Roof` (apex `z=3276.2`)
  2. `Sky Pad -> Larry's Warehouse Roof` (`vz=1303`, `z=2389.5`)
  3. `Sky Pad -> Golden West Casino Roof` (flat north roof, `vz=957`, `z=2521.3`)
  4. `Sky Pad -> Great Castle Roof` (`vz=679`, `z=2904.3`)
  5. `Sky Pad -> Parking Garage L6 Roof` (`vz=403`, `z=2989.8`)
  6. `Sky Pad -> Padre Roof` (`z=3274.1`) -> auto-chained back to `Sky Pad -> Fox Roof`!
- **Larry's Courtyard Purple Sign SkyPad #11 LIVE:** Stepping onto `(-6672, 3876, 36)` fired `Sky Pad -> Golden West Casino Roof` (`z=2100.7`, `vz=1261`), landed dead-center on Golden West's flat roof SkyPad, and chained onward to `Sky Pad -> Great Castle Roof` (`vz=2119`, Run 5 L848–859).
- **Regular `trigger_push` Pads LIVE:** Garage L6 Pad #6 (`-7440, -5340, 678`) launched to `z=993.8, vz=980`; Larry's Pad #10 (`-8268, 4404, 36`) launched to `z=262.7, vz=645` (Run 5 L860–867).
- **Go-Karts Beside Spawns LIVE:** BSP check confirms 36/36 spawns have a paired Go-Kart within `125.9–165.7 u`. Boarded H St spawn's `misc_gokart_1` (`impulse 86`) and drove smoothly `+1,043.1 u` North down H St (`y: -5163.0 -> -4119.9`, `26_gokart_drive.png`, crisp bottom-left corner HUD).
- **Jetpack Pickup & Flight LIVE:** Picked up Garage L6 `item_jetpack` (`-5436, -5580, 672`: `jetpack picked up`), engaged flight (`impulse 71` + `+jump`: `jetpack on`), and climbed smoothly `+571.9 u` (`z: 672.0 -> 931.9 -> 1243.9`, steady `vz=260`) with the glass fuel tank HUD (`38s`) cleanly anchored on the left (`27_jetpack_flight.png`, Run 5 L880–896).

---

## 4. Recommended Fixes for the 3 Live-Verified Defects

1. **Fix L1 (Floating 21st St Awnings North of Golden West Casino):** Expand `SLOTS["gw_a"]` drop rectangle north bound from `D y = 175.0 ft` to `D y = 190.0 ft` (or specifically drop `dd_awn_navy`, `dd_awn_redc`, `dd_legbrown` brushes in `x in -2300..-750, y in 5520..5720, z > 24`) in `merged_landmarks.py` so zero orphaned awnings hover over 21st St.
2. **Fix L2 (Go-Kart Un-Rampable Fallen Bakersfield Sign):** Update vehicle ground-sampling (`Veh_GroundSample` / curb climb) to trace against `SOLID_BSP` bmodels + Hull 1 (not `MOVE_WORLDONLY` Hull 0) and/or add visible sloped debris/asphalt approach wedges to `bako_sign_rubble`'s Hull 0 geometry so Go-Karts launch smoothly over the fallen Bakersfield Sign.
3. **Fix L3 (Great Castle Watchtower `item_jetpack #570` `droptofloor` Failure):** Relocate the Great Castle `item_jetpack` (`-5759 955 357`) off the narrow crow's nest mast onto a clear `>= 48×48 u` open flat slab on the watchtower or main castle roof so `item_jetpack`'s `+24 u` lift and `'-20 -20 -24'..'20 20 20'` bbox settles with **0 startup `droptofloor` warnings**.
4. *(Housekeeping)* Regenerate `gfx/minimap/bakersfieldish.png` inside `zz_bakersfieldish.pk3` after the final BSP compile so it matches the final geometry.

---

## 5. Timeline Landmark Screenshots

Screenshot: C:\Users\qxdc\.gemini\antigravity\brain\709c43a2-6203-459b-b46f-b33c0da882e7\timeline_1_golden_west_casino.png | Golden West Casino exterior rotunda and flat roof
Screenshot: C:\Users\qxdc\.gemini\antigravity\brain\709c43a2-6203-459b-b46f-b33c0da882e7\timeline_2_great_castle.png | The Great Castle watchtower merlons and roof SkyPad
Screenshot: C:\Users\qxdc\.gemini\antigravity\brain\709c43a2-6203-459b-b46f-b33c0da882e7\timeline_3_larrys_warehouse.png | Larry's Warehouse courtyard Purple Sign SkyPad and rooftops
Screenshot: C:\Users\qxdc\.gemini\antigravity\brain\709c43a2-6203-459b-b46f-b33c0da882e7\timeline_4_hst_padre_sign_fox.png | H Street hero view Padre Sign Garage Fox
