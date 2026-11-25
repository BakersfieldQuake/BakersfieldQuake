# Bakersfield-ish — Independent Final Accuracy Audit #3 (Mechanics, QuakeC, Physics, Packaging & Spec Compliance)

- **Auditor:** Fresh Accuracy Auditor #3 of 4 (`audit-v2-3`, zero prior build history, zero prior audit reports read, zero Zircon launches)
- **Target Artifacts Audited:**
  - `maps/bakersfieldish.bsp` (`40,851,944 B`, BSP2) & `maps/bakersfieldish.lit` (`14,382,632 B`) vs `maps/bakersfielddowntown.bsp` (`37,081,900 B`)
  - `zz_bakersfieldish.pk3` (`440,516 B`, SHA-256 `32fb0d60e3442fd6c29699a04320106424102cf8e5714601c90b5158ee56d768`) & `source/mm_tools/build_bakersfieldish_pk3.py`
  - `progs.dat` (`3,773,670 B`), `csprogs.dat` (`617,526 B`), `menu.dat` (`152,202 B`) & QuakeC sources under `source/qc_combat_decomp/` and `source/menu_qc/`
  - `effectinfo.txt`, `server.cfg`, `.github/workflows/build-zip.yml`
  - Map composition & compile logs under `source/downtown/` and latest visual capture sheets (`docs/bakersfieldish_captures/round3..5/`)
- **Method:** Direct binary BSP2 parsing + independent Quake BSP2 Hull-0 / Hull-1 / Hull-2 collision & ballistic trajectory verification, VFS/PK3 byte-reproducibility checks, line-by-line QuakeC mechanics audit, and visual capture cross-check.

---

## Overall Verdict: **FAIL**

The map composition, merged landmarks, high skybox, texture/asset VFS completeness, PK3 reproducibility, CI wiring, CSQC corner HUD, non-blinding particle design, Fox/Padre rubble foot-climbability, and SkyPad/Jump-Pad trajectories are **exceptionally strong** and pass almost every requirement.

However, **3 concrete, mathematically proven gameplay/physics defects** fail explicit specification requirements and must be fixed before sign-off:

| # | Severity | Requirement Violated | Root Cause & Exact Location |
|---|---|---|---|
| **F1** | **CRITICAL (Blocker)** | **Bakersfield Sign fallen wreckage must be "genuinely walkable & Go-Kart rampable across H St"** (also breaks Go-Karts on Fox Roof, Padre Roof, Padre 2F, Fox/Padre rubble) | `source/qc_combat_decomp/vehicle_drive.qc:604` (`Veh_GroundSample`) calls `traceline (p, q, 3, v)` (`3 = MOVE_WORLDONLY`, **Hull 0 point trace**). `MOVE_WORLDONLY` ignores **ALL `SOLID_BSP` brush entities** (`bako_sign_rubble`, `bako_fox_rubble`, `bako_padre_rubble`, `bako_fox_piece`, `bako_padre_piece`), AND `traceline` (Hull 0) ignores `clip`-textured approach ramps (`merged_landmarks.py:1670-1674`) which exist **only** in Hull 1/2 (`clipnodes`). Go-Karts stay at `Z=0` and slam head-on into the 40u vertical arch face (`gokart.qc:542`), AND the 3 rooftop Go-Karts (`misc_gokart_2/4/5`) fall straight through their `SOLID_BSP` roofs the moment they are driven (`gokart.qc:1746-1750`). Also `gokart.qc:1586` restricts curb-step climbs to `vd_hitent == world`. |
| **F2** | **HIGH (Blocker)** | **Padre rolling boulders must "genuinely bounce ANY player/bot/vehicle they hit"** (and `Bako_LiftPlayersOnto` / `Bako_NudgePlayersClear` on parked vehicles) | `source/qc_combat_decomp/bako_destruct.qc:815-827` (`Bako_BounceTarget`) sets `victim.velocity`, `victim.veh_vz = 210`, `victim.veh_air = TRUE` on `veh_kind > 0`, which works for **driven** vehicles (`veh_driver != world`), **but NEVER sets `victim.veh_coast_until` (or wakes `victim.nextthink`) for undriven/parked vehicles**. Because parked vehicles use `MOVETYPE_NONE` and `vehicles.qc:1684` only calls `Veh_CoastStep` when `self.veh_coast_until > 0`, hit parked Go-Karts/Vans/GT Cars log `"bounced vehicle"` and play `clang2.wav` while moving **0.0 units**. The same omission in `Bako_LiftPlayersOnto` (`408-414`) and `Bako_NudgePlayersClear` (`470-476`) leaves lifted undriven vehicles frozen floating in midair. In addition, `misc_vehicle_johnbird` (2) and `misc_vehicle_rocketrider` (1) do not set `veh_kind > 0` and are completely skipped. |
| **F3** | **MEDIUM-HIGH (Blocker)** | **"clock shootable by ANY weapon (zero blood...)" / "zero blood" on Padre & Glass** | `source/qc_combat_decomp/weapons.qc:671-796` (`W_FireAxe`) relies on `trace_ent.takedamage != DAMAGE_AIM` (line 704) to skip flesh/meat effects, and only has an explicit early return for `trace_ent.lan_kind` (line 728). Because `bako_fox_clock`, `bako_padre_piece`, `bako_sign_piece`, and `func_breakable` (`style == BTYPE_GLASS`, changed to `DAMAGE_AIM` at `breakable.qc:1466`) all use `DAMAGE_AIM`, axing or kicking ANY of them falls through to **`SpawnMeatSpray(...)` (`weapons.qc:737`, spawning flying bloody `progs/zom_gib.mdl` chunks)** plus **`kickgib/gib_hit.wav` (line 738)** and **`player/axeflesh1..3.wav` / `kickflesh.wav` (lines 766-787)**. (Hitscan, nails, rockets, grenades, lightning, chainsaw, Eric Cannon, and Wheelman Cannon are all clean with zero blood/meat.) |

Additionally, **1 minor non-blocking edge case** is documented below:
- **O1 (Minor):** `source/qc_combat_decomp/combat.qc:496` (`T_RadiusDamage`) does not filter `&& head.bako_group == 0` (unlike `eric_cannon.qc:673`). For smaller destructibles (`bako_fox_clock` half-extents `106x106x69u`, `bako_sign_piece` `half_y=83u`) or large-radius splashes (Wheelman Cannon Tier 2/3 `radius=199..231u`), an indirect ground blast can hit `T_RadiusDamage`'s center-distance loop first for reduced damage and stamp `bako_*_last_infl`, causing `BakoDestruct_RadiusSplash`'s closest-point AABB splash to be deduped.

---

## Section 1: Downtown, 4 Merged Landmarks & Packaging / CI Check — **PASS**

### 1.1 `maps/bakersfieldish.bsp` vs `maps/bakersfielddowntown.bsp`

Direct BSP2 binary comparison:

| Metric | `bakersfielddowntown.bsp` | `bakersfieldish.bsp` | Audit Result |
|---|---:|---:|---|
| Magic / Size | `BSP2` / `37,081,900 B` | `BSP2` / `40,851,944 B` | Clean BSP2 |
| World XY Bounds | `[-14111..1391] x [-7399..6731]` | `[-14111..1391] x [-7399..6731]` | Exact downtown footprint preserved |
| Skybox Max Z | `3,371.0 u` (`281 ft`) | **`7,211.0 u` (`601 ft`)** | High skybox verified (+3,840 u) |
| World Visleafs | `32,115` | **`33,264`** (`< 35k`, full `-visdist 4500` + `keep_sky_pvs`) | Lean, zero leaks (`qbsp` clean, 0 errors/leaks) |
| Bmodels / Entities | `275` / `1,576` | `89` / `1,567` | Clean |
| Lighting / Fog | `sun=245, mangle=60/-50, fog=0.26 0.437 0.466 0.506 ...` | `sun=235, mangle=52/-38, color=1 0.88 0.72, fog=0.22 0.56 0.49 0.41 ... 2200 750`, `-extra4`, `0.72x` post-scale + highlight clamp (`lit mean=51.8, p99=125`) | Warm dusty light post-apoc verified |
| Skybox `dtsky145_` | 6/6 `.png` sides present | 6/6 `.png` sides present | PASS |

### 1.2 Core Downtown Anchors & 4 Merged Landmarks Presence (Direct BSP2 Hull-0 Grid Sampling)

Every required downtown anchor and all 4 Scheme-A merged landmarks are physically compiled into `maps/bakersfieldish.bsp` at their expected footprints and heights:
- **Padre Hotel:** 20/25 grid hits, `maxZ = 1,352 u (112.7 ft)` (`7` `bako_padre_piece` + `1` `bako_padre_rubble`)
- **Fox Theater:** 25/25 grid hits, `maxZ = 960 u (80.0 ft)` (`1` `bako_fox_clock` + `7` `bako_fox_piece` + `1` `bako_fox_rubble`)
- **18th & Eye Parking Garage:** 25/25 grid hits, `maxZ = 693 u (57.8 ft)`
- **Dagny's Coffee:** 25/25 grid hits, `maxZ = 350 u (29.2 ft)` (preserved outside Slot `LW-A`, 18 `misc_lan_quakedesk` intact)
- **Nile Theater:** 6/25 grid hits, `maxZ = 442 u (36.8 ft)`
- **Golden West Casino (Slot `GW-A`):** 17/25 grid hits, `maxZ = 334 u (27.8 ft)` (with pylon, courtyard, 12 breakable glass bays)
- **The Great Castle (Slot `GC-A`):** 20/25 grid hits, `maxZ = 156 u (13.0 ft)` (with pylon, 2 breakable glass bays)
- **Larry's Warehouse (Slot `LW-A`):** 20/25 grid hits, `maxZ = 204 u (17.0 ft)` (with LAN interior props & 4 breakable glass bays)
- **Bakersfield Sign (Slot `S1` on H St):** 9/25 grid hits, `maxZ = 367 u (30.6 ft)` (`1` `bako_sign_piece` + `1` `bako_sign_rubble`)
- **Light Post-Apocalyptic Dressing:** 43 street barriers/rubbles/poles/dumpsters + 3 fixed kart ramps + 2 grounded sky-bridges (`bakersfieldish-make.log:120`), warm dusty sunlight/fog without muddy darkness.

### 1.3 Zero Missing Assets Audit (Strict DarkPlaces/Zircon VFS Rules)

- **BSP Textures (`1,037` Lump-2 entries):** `1,031` resolved directly in `textures/<name>.{png,tga,jpg,dds}` (strict root-level resolution, **0 subdir-only**, **0 truly missing**), `5` compiler specials (`skip`, `clip`, `hint`, `origin`, `trigger`), `1` embedded `m0 != 0`.
- **Entity Models & Sounds:** `0` missing entity `mdl`/`model` entries, `0` missing entity `noise`/`sound` entries.
- **QuakeC `bako_destruct.qc` Assets:** All 10 precached models (`bako_boulder1..4.md3`, `bako_glass_shard1..3.md3`, `gib1..3.mdl`, plus `npc_randguy/afroguy/fatguy.md3` via `RandomNPCs_Precache`), all 25 referenced sounds, and all 11 particle effects exist in VFS / `effectinfo.txt`.
- **Progs Classname Coverage:** All `49` non-worldspawn classnames in `maps/bakersfieldish.bsp` resolve to valid spawn functions in `progs.dat` (`0` missing).
- **Compiled Binary Freshness:** `progs.dat`, `csprogs.dat`, and `menu.dat` are all newer than every QC source file (`newer_sources=[]`), and all three contain `bakersfieldish` (`progs.dat` contains all `bako_*` destructible symbols; `menu_host.qc` lists `Bakersfield-ish`; `csqc/minimap_bounds.qc` includes `bakersfieldish` with matching bounds `-6360.00 -330.00 8796.80`).

### 1.4 `zz_bakersfieldish.pk3` Reproducibility, Packaging & CI Wiring

- **Independent Reproducibility Verification:** Built twice into a fresh temporary directory via `python -I source/mm_tools/build_bakersfieldish_pk3.py`:
  - On-disk `zz_bakersfieldish.pk3`: `32fb0d60e3442fd6c29699a04320106424102cf8e5714601c90b5158ee56d768` (`440,516 B`)
  - Fresh Run 1: `32fb0d60e3442fd6c29699a04320106424102cf8e5714601c90b5158ee56d768`
  - Fresh Run 2: `32fb0d60e3442fd6c29699a04320106424102cf8e5714601c90b5158ee56d768`
  - **100% byte-identical across disk, run 1, and run 2.**
- **ZIP Metadata Hygiene:** All 17 entries strictly sorted alphabetically; every entry has `date_time=(1980, 1, 1, 0, 0, 0)` and `external_attr=0x01a40000` (`0o644 << 16`); `ZIP_STORED` (0) for all `.png`/`.jpg` entries, `ZIP_DEFLATED` (8, level 9) for `.md3`/`.txt`/`.shader`.
- **Contents Verified:** `progs/bako_boulder1..4.md3` + textures + `bako_rebar.png`, `progs/bako_glass_shard1..3.md3` + `bako_glass_shard.png` (all 7 MD3s valid `IDP3` v15 with `ofs_end == file_size`), `levelshots/bakersfieldish.jpg`, `gfx/minimap/bakersfieldish.png`, `gfx/minimap/bakersfieldish.txt` (`-6360.00 -330.00 8796.80\n`), `scripts/bakersfieldish_minimap.shader`.
- **Zero Loose Shadows:** Zero stray loose copies of any `zz_bakersfieldish.pk3` entry exist under `BakersfieldQuake/{levelshots,progs,gfx,scripts}`.
- **Base PK3s Untouched:** `BakersfieldQuake/bakersfield.pk3` (`502,843,735 B`, mtime Nov 18) and `quake15/q15.pk3` (`476,862,746 B`, mtime 2021) are untouched; `maps/bakersfielddowntown.bsp` (mtime Nov 24) is untouched.
- **CI Wiring (`.github/workflows/build-zip.yml`):**
  - `Cache zz_bakersfieldish.pk3` (lines 342-347) pins `numpy2.5.4-pillow13.0.0` and hashes `build_bakersfieldish_pk3.py`, `md3lib.py`, and `bakersfieldish_assets/**` (complete input set).
  - `Install pk3 build dependencies` `if:` condition includes `steps.cache_bakersfieldish.outputs.cache-hit != 'true'` (line 350).
  - `Build zz_bakersfieldish.pk3` runs with `--verify-repro` (lines 441-445).
  - Copied into `out/BAKOQUAKE/BakersfieldQuake/` (line 449) and verified for all 11 required files in `Check the package` (lines 770-790).
  - *(Cosmetic note: release notes string on line 931 does not list `zz_bakersfieldish.pk3`, and `server.cfg` intentionally places `bakersfieldish` in `bm_votemaps` rather than `bm_maplist` until a base `BAKOQUAKE.zip` carries `maps/bakersfieldish.bsp`.)*

---

## Section 2: Destructibles, QuakeC Mechanics, Effects & Edge-Case Audit — **FAIL (3 Bugs Found)**

### 2.1 Fox Theater — **PASS (except F3 `W_FireAxe` meat spray & F1 rooftop Go-Kart)**
- **Clock Target & Telefrag Guard:** `bako_fox_clock` (`hp=200`, `DAMAGE_AIM`, `BAKO_MAT_GLASS`, `SOLID_BSP`) takes damage via `combat.qc:198-209` (`T_Damage`) and `BakoDestruct_RadiusSplash` (`2136-2196`). Telefrag immunity enforced in **three** places: `triggers.qc:289` (`tdeath_touch`), `combat.qc:191-197` (`T_Damage`), and `bako_destruct.qc:1984-1987` (`BakoDestruct_OnDamage`, also rejecting `damage >= 40000`).
- **Weapon Compatibility:** Hitscan (`TraceAttack` `weapons.qc:1303`), Nails (`spike_touch`/`superspike_touch` `weapons.qc:4238,4634`), Rockets/Grenades (`T_MissileTouch`/`T_RadiusDamage`), Lightning (`LightningDamage`), Chainsaw (`W_FireSaw` `weapons.qc:1094,1154`), Eric Cannon, and Wheelman Cannon all damage the clock with **zero blood**. **Defect F3:** `W_FireAxe` (`weapons.qc:737`) sprays `progs/zom_gib.mdl` meat chunks and plays flesh audio on melee hit.
- **Collapse, Debris & Whole-Map Earthquake:** Coupled 2-piece clock tower (`tower_upper` welded to `tower_lower`'s live collar via `makevectors`, shearing forward past `u_low=0.48`), ~8.6s gravity-eased (`u^2.4`) collapse, outward masonry debris/glass shards, matte non-blinding dust veil (`bako_demolition_dust_surge` / `bako_collapse_plume`), and whole-map (`radius=24000`) clamped seismic shake (`Bako_SafeShake` + `Bako_TickSmoothShake`). Visually confirmed in `docs/bakersfieldish_captures/round5/fox_r5_sheet.png`.
- **Climbable Rubble (1–2 min):** Default `autocvar_bako_fox_rubble_t = 115s` (`1.92 min`). Independent 2D BSP2 Hull-1 BFS climb test confirms **`walk_18u` reaches `366.0 / 366.0 u` (100% of summit walkable on foot without jumping)** across 1,268 elevated cells (`>= 180 u`).
- **Slow Rebuild, Re-Destructibility & Rooftop `info_skypad` Preservation:**
  - 25s (`autocvar_bako_fox_rebuild_t = 25`) bottom-up upright rebuild (`Bako_FoxRebuildWindow`), golden weld sparks, bell chime lock-in, followed by `Bako_ResetFoxIntact()` resetting HP (`200`), `DAMAGE_AIM`, piece flags, and state to `BAKO_ST_INTACT` -> **fully re-destructible across unlimited cycles**.
  - **Rooftop `info_skypad` Trigger BBox Preserved:** Verified `info_skypad` (`(-10188, 3492, 638)`) and all 5 `skypad_fx` visual entities lie inside `Bako_HideRoofProps(BAKO_GRP_FOX)` (`z > 320`), are cleanly hidden during collapse/rubble/rebuild, and `Bako_RestoreRoofProps` (`bako_destruct.qc:719-725`) calls `setsize (e, e.bako_roof_mins, e.bako_roof_maxs)` **after** `setmodel` and `setorigin`, preserving exact `'-40 -40 -26'..'40 40 36'` trigger bounds on every rebuild.
  - **Workers Safe (Zero `droptofloor`):** `Bako_SpawnFoxCrew` (`bako_destruct.qc:1440-1498`) uses `MOVETYPE_NONE` + `traceline` (zero `droptofloor`). Independent BSP2 Hull-1 check of all 3 worker positions confirms all 3 spawn in open H St / 20th St street completely outside `bako_fox_rubble`:
    - `worker[0] = (-8825.7, 2466.9, 25.0)`: `world_h1=-1, rubble_h1=-1, overlap_rub_xy=False`
    - `worker[1] = (-8825.7, 3561.8, 25.0)`: `world_h1=-1, rubble_h1=-1, overlap_rub_xy=False`
    - `worker[2] = (-9561.3, 2096.9, 25.0)`: `world_h1=-1, rubble_h1=-1, overlap_rub_xy=False`

### 2.2 Padre Hotel — **FAIL (F2 Parked/Aerial Vehicle Boulder Bounce + F3 `W_FireAxe` Meat Spray + F1 Rooftop Go-Karts)**
- **Toughness & Weapon Damage Routing:** Unified `2600 HP` (`13x` Fox clock's `200 HP`) across all 7 `bako_padre_piece` submodels (`tier1..4`, `west_wing`, `east_wing`, `crown`).
  - **Eric Cannon (`eric_cannon.qc:652-706`, `855-862`):** `EC_Detonate` spawns fresh `inf_ent` (`eric_cannon_blast`) without calling `T_Damage` on the building first; `EC_NukeBlastDamage` skips `head.bako_group != 0` at line 673 and calls `BakoDestruct_RadiusSplash(inflictor.origin, 750, 450, inflictor, attacker, TRUE)` applying **`1.75x` structural multiplier** (`up to 787.5 dmg/nuke`, ~4 nukes to topple Padre) with **ZERO dedup race**!
  - **Rockets, Wheelman Cannon, Hitscan & Nails:** All route cleanly into `BakoDestruct_OnDamage` / `BakoDestruct_RadiusSplash` with zero blood and zero telefrag vulnerability (see **O1** for minor `T_RadiusDamage` race on large splash radii and **F3** for `W_FireAxe` meat spray).
- **Controlled Demolition & Dust:** Progressive 75%/50%/25% dark-grey window smoke vents + top-right HUD integrity gauge -> 10 perimeter charge pops (`0.05..2.05s`) -> coupled 12s inward V-collapse (`crown` welded atop `tier4`) -> wide ground-hugging matte tan street dust surge (`alpha <= 112`, zero `blend add` on dust) -> whole-map landing earthquake (`radius=24000`). Visually verified in `docs/bakersfieldish_captures/round4/padre_r4_sheet.png`.
- **Climbable Rubble & Glass Suppression:** `autocvar_bako_padre_rubble_t = 115s` (`1.92 min`). Independent 2D BSP2 Hull-1 BFS confirms **`walk_18u` reaches `400.0 / 400.0 u` (100% of 2-story rubble summit walkable on foot without jumping)** across 752 elevated cells. All `10/10` Padre 1F glass panes fall inside `Bako_RestoreGlassPane`'s suppression box (`bako_destruct.qc:3518-3527`) and are suppressed (`+5s` defer) while Padre is collapsed/rubble/rebuilding.
- **DEFECT F2 — Rolling Boulders vs Vehicles:**
  - `Bako_SpawnPadreBoulderWave` spawns 3 staggered waves (24 boulders) at `dt = 4.8s, 7.8s, 10.6s` (1 aimed down the nearest street player's lane).
  - **Walking players, bots & monsters:** `Bako_BoulderTouch` + 20 Hz proximity sweep in `Bako_BoulderThink` (`84u` radius, `spd > 25`) -> `Bako_BounceTarget` (`835-846`) genuinely launches players/bots (`kick_h = 460..660`, `kick_z = 380..440`, `FL_ONGROUND` cleared). **PASS.**
  - **Driven `veh_kind > 0` vehicles (Go-Kart / Van / GT Car with driver):** `Bako_BounceTarget` (`815-827`) sets `velocity`, `veh_vz = 210`, `veh_air = TRUE`; `GK_DriveStep` (`gokart.qc:1705-1725`) and `Veh_DriveStep` (`vehicle_drive.qc:2600-2615`) integrate upward & sideways cleanly. **PASS.**
  - **UNDRIVEN / PARKED `veh_kind > 0` vehicles (`veh_driver == world`):** **FAIL.** Parked vehicles have `movetype = MOVETYPE_NONE` and `veh_coast_until = 0` (`vehicles.qc:1964`, `vehicle_drive.qc:774,801`). `Veh_Think` (`vehicles.qc:1684`) ONLY calls `Veh_CoastStep` when `self.veh_coast_until > 0`. Because `Bako_BounceTarget` never sets `victim.veh_coast_until` (or `victim.nextthink = time + 0.01`), a boulder striking any parked Go-Kart/Van/GT Car plays `clang2.wav` and logs `"bounced vehicle"`, **yet the vehicle moves 0.0 units**. The exact same bug in `Bako_LiftPlayersOnto` (`408-414`) and `Bako_NudgePlayersClear` (`470-476`) leaves lifted parked vehicles hovering frozen in midair!
  - **Non-`veh_kind` vehicles (`misc_vehicle_johnbird` x2, `misc_vehicle_rocketrider` x1):** Completely ignored by `Bako_BoulderTouch`, `Bako_BoulderThink`, `Bako_LiftPlayersOnto`, and `Bako_NudgePlayersClear`.

### 2.3 Bakersfield Sign — **FAIL (F1 Go-Kart Un-Rampable + F3 `W_FireAxe` Meat Spray)**
- **Destruction & Visual Topple:** `bako_sign_piece` (`380 HP`, `DAMAGE_AIM`, `BAKO_MAT_METAL`), pier-anchored fracture bursts, `u^2.4` north topple (`-90°` roll onto H St), 0.52s elastic rebound, dual-tower + 80-ft span warm tan dust, whole-map earthquake (`radius=24000`), and exact-pose swap to `bako_sign_rubble` (`*55`). Visually verified in `docs/bakersfieldish_captures/round3/sign_r3_sheet.png`.
- **Foot Walkability:** Independent BSP2 Hull-1 walk simulation (`STEPSIZE=18u`) across `bako_sign_rubble` on H St (`X=-8700`) passes cleanly in **both** directions (`S->N` and `N->S`, `max_player_origin_z = 64.0 u`, `blocked_at = None`), riding the smooth 16.3° `clip` ramps (`max_dz / 8u = 5.3 u` in Hull 1 & Hull 2). **PASS on foot.**
- **DEFECT F1 — Go-Kart Rampability BROKEN (Brick Wall) + Rooftop Go-Kart Fall-Through:**
  - Direct BSP2 parse of `bako_sign_rubble` (`*55`) along H St centerline (`X=-8700`) and both lanes (`X=-8820`, `-8580`):
    - **Hull 1 / Hull 2 (`clipnodes`):** smooth 16.3° `clip` ramps from `Y=-3261 (Z=3u)` up to `Y=-3141 (Z=40u)`, flat crest to `Y=-3021 (Z=40u)`, smooth ramp down to `Y=-2901 (Z=3u)`.
    - **Hull 0 (`nodes`, used by `traceline`):** **ZERO ramps** — sheer **40.0-unit vertical wall** (`Y=-3149: Z=0u` -> `Y=-3125: Z=40u`, dropping `Y=-3037: Z=40u` -> `Y=-3029: Z=0u`), because `merged_landmarks.py:1670-1674` textured the approach wedges with `clip`!
  - In `source/qc_combat_decomp/vehicle_drive.qc:604`, `Veh_GroundSample` executes:
    ```qc
    traceline (p, q, 3, v);   // 3 = MOVE_WORLDONLY!
    ```
  - This creates a **double blocker**:
    1. `3` (`MOVE_WORLDONLY`) ignores **all `SOLID_BSP` brush entities**, so Go-Karts (and Vans/GT Cars) never detect `bako_sign_rubble` (nor `bako_fox_rubble`, `bako_padre_rubble`, `bako_fox_piece`, `bako_padre_piece`) as ground!
    2. Even if `3` were changed to `1` (`MOVE_NOMONSTERS`), `traceline` is a **Hull 0** point trace and still ignores `bako_sign_rubble`'s `clip`-textured ramps!
  - Consequently, a Go-Kart driving toward the fallen Bakersfield Sign keeps `vd_gh = 0u` across `Y=-3261..-3125`, then its `GK_Sweep` (`gokart.qc:542`, `zbase=22`, `tracebox` Hull 1) **slams head-on into the 40u vertical arch face (`nz = 0 < 0.7`) and bounces backwards like a brick wall** (and `gokart.qc:1586` restricts curb-step climbs strictly to `vd_hitent == world`).
  - **Cascade Defect on Rooftop Go-Karts:** Because `bako_fox_piece:auditorium_roof`, `bako_padre_piece:crown`, and `bako_padre_piece:tier1/west_wing` are also `SOLID_BSP` bmodels (not `worldspawn`), entering and driving any of the 3 rooftop Go-Karts (`misc_gokart_2` on Fox Roof `z=636`, `misc_gokart_5` on Padre Roof `z=1254`, `misc_gokart_4` on Padre 2F `z=222`) or landing a Go-Kart on Padre Roof via `PAD Garage L6 -> Padre Roof Kart Boost` immediately evaluates `vd_found == 0` -> `v.veh_air = TRUE` (`gokart.qc:1746-1750`) and **drops the Go-Kart straight through the solid roof slab to street level**!

### 2.4 Shatterable Glass — **PASS (except F3 `W_FireAxe` Meat Spray)**
- **56/56 Real Cut-Out Hollow Openings:** Independent BSP2 Hull-0 sampling on both sides (`±10u`, `±22u` along each pane's thin normal) confirms **56/56 `func_breakable` panes (`style=3`, `alpha=0.52`) are genuinely hollow on both sides (`0` solid-backed)**.
- **Building Distribution:** Dagny's Coffee (`18`), Golden West Casino (`12`), Padre Hotel (`10` — all 10 suppressed while Padre is collapsed), Nile Theater (`6`), Larry's Warehouse (`4`), 1818 H St shopfront (`4`), Great Castle (`2`).
- **Weapons, Smash-Through & Respawn:** `breakable.qc` sets `DAMAGE_AIM` and `touch = funcbreakable_touch`; players moving `> 220 u/s` (`BakoDestruct_GlassTouchCheck`) and moving vehicles (`> 80 u/s`, 20 Hz bbox sweep in `Bako_TickGlass`) shatter glass cleanly, spawning 20 translucent faceted shard MD3s (`alpha=0.56`) + cool cyan-silver `bako_glass_sparkle`, respawning after `120s` (deferred if player overlapping or inside collapsed Padre/Fox). Zero blood on hitscan, nails, rockets, grenades, chainsaw, lightning, Eric Cannon, Wheelman Cannon (**Defect F3** applies to `W_FireAxe` melee only). Visually verified in `docs/bakersfieldish_captures/round3/glass_r3_sheet.png`.

### 2.5 Non-Blinding FX, Screen-Safety & HUD (`CLAUDE.md`) — **PASS**
- **ZERO `bf`**, **ZERO `v_cshift`**, **ZERO `centerprint`**, **ZERO `bprint`**, **ZERO `droptofloor`** in `bako_destruct.qc` and modified CSQC HUD code.
- **Smooth Clamped Whole-Map Earthquake:** `Bako_TickSmoothShake` (`bako_destruct.qc:207-270`) runs every server frame (`StartFrame` -> `BakoDestruct_Frame`) with damped-sine attenuation, per-frame slew clamp (`<= 0.42 deg/frame`), and hard `punchangle` clamps (`|pitch| <= 3.1`, `|roll| <= 2.1`, `|yaw| <= 0.7`, `0.55x` roll in vehicles).
- **Non-Blinding Particles (`effectinfo.txt:22128-22435`):** Every dust/smoke effect (`bako_demolition_dust_surge`, `bako_collapse_plume`, `bako_window_smoke`, `bako_masonry_burst`, `bako_rock_dust`) strictly uses `type alphastatic` + `blend alpha` with warm matte earth/slate colors and `alpha <= 118` (zero additive whiteout).
- **CSQC HUD (`CLAUDE.md` Compliance):** `BM_DrawBakoDestructHUD` (`csqc/bm_hud.qc:1333-1404`) draws strictly in the **top-right corner** (`w - 8`, stacking on `bm_topright_y`) using `BM_ShadowColorRight` plus a 1px underline progress bar under `PADRE HOTEL XX%`. Zero opaque center panels/boxes; invoked once per frame across HUD styles 0–4 and vehicle HUD (`csqc.main.qc:480-506`).
- **`Bako_NudgePlayersClear` (`bako_destruct.qc:422-480`):** Cleanly lifts BOTH foot players (`MOVETYPE_WALK`) AND driven vehicles along with their `MOVETYPE_NONE` drivers (`setorigin(v.veh_driver, v.origin + '0 0 20')`). *(See **F2** for undriven parked vehicles needing `veh_coast_until` so they settle back down instead of hovering.)*

---

## Section 3: Traversal Physics Audit (`info_skypad`, `trigger_push`, Go-Karts, Jetpacks) — **PASS (Placements & Arcs)**

### 3.1 Spawns (36) & Go-Karts (36)
- **35 `info_player_deathmatch` + 1 `info_player_start`:**
  - `0/36` inside intact solid (BSP2 Hull 1)
  - `0/36` ground spawns inside collapsed rubble (BSP2 Hull 1); the 3 rooftop spawns (Padre 2F `z=225`, Padre Roof `z=1257`, Fox Roof `z=639`) are safely relocated onto rubble top by `Bako_HideRoofProps` during collapse.
  - **36/36 spawns have a same-floor (`|dz| <= 80u`) Go-Kart within `161.7 u`** (top 5 distances: `161.7u`, `144.0u`, `126.0u`, `126.0u`, `126.0u`).
- **36 Go-Karts (`misc_gokart_1..6`, 6 of each):**
  - `0/36` overlapping any `info_skypad` trigger bbox (`'-40 -40 -26'..'40 40 36'`)
  - `0/36` inside intact solid (BSP2 Hull 1 at `+24z`)
  - `0/36` buried in collapsed rubble (the 3 rooftop Go-Karts on Padre 2F, Padre Roof, and Fox Roof are cleanly caught & hidden by `Bako_HideRoofProps` and restored on rebuild — though see **F1** for driving them while roofs are intact!).

### 3.2 `info_skypad` Ballistic Chain Audit (11/11 Clear in BSP2 Hull 1)

Simulated using exact `SkyPad_CalcVel` (`skypad.qc:43-64`, `g=800`, `+2u` lift) from exact standing Hull-1 origin against `worldspawn` + all intact solid bmodels:

| # | Route | Flight `tf` | Apex Z | Max Axis V | Hull-1 Collision | Landing Floor | Notes |
|---|---|---:|---:|---:|---|---|---|
| 00 | Padre Roof -> Fox Roof | `4.94s` | `3,400 u` | `1,851 u/s` | **NONE** | `bako_fox_piece:auditorium_roof` | `PadreRoofHide OK` (5u pedestal on `crown`) |
| 01 | Fox Roof -> Larry's Roof | `5.06s` | `3,000 u` | `1,943 u/s` | **NONE** | `worldspawn` | `FoxRoofHide OK` (5u pedestal on `auditorium_roof`) |
| 02 | Larry's Roof -> Golden West Roof | `5.36s` | `3,100 u` | `2,142 u/s` | **NONE** | `worldspawn` | Rooftop loop |
| 03 | Golden West Roof -> Great Castle Roof | `5.47s` | `3,200 u` | `2,182 u/s` | **NONE** | `worldspawn` | Rooftop loop |
| 04 | Great Castle Roof -> Parking Garage L6 | `5.16s` | `3,100 u` | `2,160 u/s` | **NONE** | `worldspawn` | Rooftop loop |
| 05 | Parking Garage L6 -> Padre Roof | `4.82s` | `3,300 u` | `2,049 u/s` | **NONE** | `bako_padre_piece:crown` | Closes 6-roof cross-map loop! |
| 06 | H St Sign Plaza -> Fox Roof Chain | `5.05s` | `2,900 u` | `2,141 u/s` | **NONE** | `bako_fox_piece:auditorium_roof` | Ground feeder |
| 07 | SW 18th & G -> Larry's Roof | `6.14s` | `3,900 u` | `2,487 u/s` | **NONE** | `worldspawn` | Ground feeder |
| 08 | SE 18th & Chester -> Golden West Roof | `5.98s` | `3,700 u` | `2,422 u/s` | **NONE** | `worldspawn` | Ground feeder |
| 09 | GW Courtyard -> Parking Garage L6 | `5.69s` | `3,600 u` | `2,389 u/s` | **NONE** | `worldspawn` | Ground feeder |
| 10 | Larry's Courtyard -> Golden West Roof | `5.45s` | `3,100 u` | `2,217 u/s` | **NONE** | `worldspawn` | Ground feeder |

- **11/11 PASS:** All velocities well below `sv_maxvelocity = 6500` (`max = 2,487 u/s`), all apexes well below `SKY_Z = 7,200 u` (`max = 3,900 u`), zero wall/roof/sky hits, closed 6-landmark rooftop circuit plus 5 perimeter feeders.

### 3.3 `trigger_push` Jump Pads Audit (12/12 Walkable Elevated Landings in BSP2 Hull 1)

Simulated using exact `triggers.qc:828` (`v = movedir * speed * 10`, `g=800`):
- **12/12 pads** clear all walls/eaves and land cleanly (`norm_z = 1.00`, zero wall smacks) on their target roofs/ledges:
  - `#00` Fox West Alley -> Fox Roof (`dz=+607u`, `floor=51.0 ft`)
  - `#01` Wall St -> Padre Roof (`dz=+1,219u`, `floor=102.5 ft`)
  - `#02` Wall St -> Padre 2F/3F (`min_xy` lands on 2F Prairie Fire `floor=16.5 ft`; `center`/`max_xy` lands cleanly on Padre 3F ledge `floor=26.1 ft`, `norm_z=1.00`)
  - `#03` 18th St -> Garage L6 Roof (`dz=+643u`)
  - `#04` Eye St -> Garage L6 Roof (`dz=+643u`)
  - `#05` Garage L6 -> Padre Roof Kart Boost (`dz=+577u`, `dh=2,477u`, `floor=102.5 ft`) *(Note: foot players land cleanly; Go-Karts suffer **F1** upon landing on `bako_padre_piece:crown`!)*
  - `#06` 20th St -> Fox Marquee / Belfry (`min_xy` lands on Fox Marquee `floor=22.0 ft`; `center`/`max_xy` lands cleanly on `bako_fox_piece:tower_upper` belfry ledge `floor=73.8 ft`, `norm_z=1.00`, right beside the clock!)
  - `#07` Eye St -> Great Castle Roof (`dz=+148u`)
  - `#08` 20th St -> Golden West Roof (`dz=+187u`, `dh=2,618u`)
  - `#09` H St -> Larry's Warehouse Roof (`dz=+196u`)
  - `#10` Dagny's Lot -> Dagny's Roof (`dz=+371u`)
  - `#11` Wall St Alley -> Tattoo Tower Roof (`dz=+637u`)

### 3.4 `item_jetpack` (13) & Other Vehicles / Cannons
- **13/13 `item_jetpack`** entities sit clear of solid (`solid_h0 = -1`) in sensible rooftop perches and far perimeter corners (`min_spawn_dist = 146..1,149 u`): Parking Garage L6 (`1,149 u`), Padre 2F & Roof (both covered by `PadreRoofHide`), Fox Roof (covered by `FoxRoofHide`), Golden West roof & forecourt, Larry's Warehouse roofs (`B76`, `B45`), Great Castle watchtower, and 4 far street corners (NW, SW, SE, H St).
- **3 `misc_eric_cannon`** (Garage L6, H St near Sign, Golden West) and **5 other vehicles** (2 John Birds, 1 Rocket Rider, 1 Van, 1 GT Car) all clear of solid.

---

## Required Surgical Fixes to Reach PASS

1. **Fix F1 (Go-Kart rampability over fallen Bakersfield Sign & driving on destructible `SOLID_BSP` roofs/rubble):**
   - In `source/qc_combat_decomp/vehicle_drive.qc:604` (`Veh_GroundSample`), replace:
     ```qc
     traceline (p, q, 3, v);
     ```
     with a tiny `MOVE_NOMONSTERS (1)` `tracebox` that hits `worldspawn`, all `SOLID_BSP` bmodels (`bako_sign_rubble`, `bako_fox_piece`, `bako_padre_piece`, `bako_*_rubble`), AND `clip`-textured ramps via Hull 1 while still skipping `SOLID_BBOX` parked vehicles/players/monsters:
     ```qc
     tracebox (p, '-2 -2 0', '2 2 2', q, 1, v);
     ```
   - In `source/qc_combat_decomp/gokart.qc:1586`, widen the curb-step check from `if (vd_hitent == world)` to `if (vd_hitent == world || vd_hitent.solid == SOLID_BSP)`.
2. **Fix F2 (Rolling boulders & rubble lifters on undriven/parked vehicles):**
   - In `source/qc_combat_decomp/bako_destruct.qc` inside `Bako_BounceTarget` (`815-827`), `Bako_LiftPlayersOnto` (`408-414`), and `Bako_NudgePlayersClear` (`470-476`), whenever `v.veh_driver == world`, activate coasting physics so `Veh_Think` runs `Veh_CoastStep`:
     ```qc
     if (v.veh_driver == world)
     {
         v.veh_coast_until = max (v.veh_coast_until, time + 3.0);
         v.nextthink = time + 0.01;
     }
     ```
   - *(Optional polish: also bounce `misc_vehicle_johnbird` and `misc_vehicle_rocketrider` when struck by Padre boulders.)*
3. **Fix F3 (Axe/kick melee meat gibs & flesh audio on destructibles/glass):**
   - In `source/qc_combat_decomp/weapons.qc` right next to `if (trace_ent.lan_kind)` (line 728), add an early return for `if (trace_ent.bako_material > 0 || trace_ent.classtype == CT_FUNCBREAK)` that plays material-appropriate impact FX/sound, calls `T_Damage`, and returns before `SpawnMeatSpray` (line 737).
4. **Fix O1 (Optional polish — `T_RadiusDamage` splash dedup parity with `EC_NukeBlastDamage`):**
   - In `source/qc_combat_decomp/combat.qc:496`, guard `if (head.takedamage && head.bako_group == 0)` so all splash damage on `bako_*` structures routes exclusively through closest-point AABB `BakoDestruct_RadiusSplash`.
5. Recompile `progs.dat` via `fteqcc` and re-verify live in Zircon (Go-Kart driving across fallen Bakersfield Sign + Fox/Padre roof Go-Karts, boulder hitting parked Go-Kart, and axing Fox clock/Padre/glass).
