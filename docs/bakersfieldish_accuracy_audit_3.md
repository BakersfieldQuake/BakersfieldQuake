# Bakersfield-ish Accuracy Audit #3 — End-to-End Mechanics, Destructibles Logic, Traversal Physics & Spec-Compliance

**Auditor:** Fresh Accuracy Auditor #3 of 4 (`audit-3`, zero prior build history, read-only independent audit)  
**Target Build Inspected:**
- `maps/bakersfieldish.bsp` (`40,958,428` bytes, BSP2, `33,382` visleafs) + `maps/bakersfieldish.lit` (`14,382,320` bytes, valid `QLIT v1`) vs `maps/bakersfielddowntown.bsp` (`37,081,900` bytes)
- `progs.dat` (`3,768,278` bytes) & `csprogs.dat` (`617,526` bytes) — verified newer than all `.qc` / `csqc/*.qc` sources
- `zz_bakersfieldish.pk3` (`339,596` bytes, 13 entries) + `source/mm_tools/build_bakersfieldish_pk3.py`
- `effectinfo.txt` (lines 22128–22438) & `.github/workflows/build-zip.yml`
- QuakeC & CSQC: `bako_destruct_defs.qc`, `bako_destruct.qc`, `combat.qc`, `eric_cannon.qc`, `wcannon.qc`, `wcannon_defs.qc`, `breakable.qc`, `weapons.qc`, `dn3_fx.qc`, `skypad.qc`, `jetpack.qc`, `gokart.qc`, `vehicles.qc`, `vehicle_drive.qc`, `triggers.qc`, `subs.qc`, `world.qc`, `bm_match.qc`, `csqc/bm_hud.qc`, `csqc/csqc.main.qc`, `csqc/hud_common.qc`, `csqc/bm_minimap_hud.qc`, `csqc/minimap_bounds.qc`
- Captured Gameplay Videos & Keyframes (watched in full + inspected contact sheets & full-res PNGs):
  - `docs/bakersfieldish_captures/round5/fox_r5.mp4`, `fox_r5_sheet.png`, `fox_r5_keyframes/*.png`
  - `docs/bakersfieldish_captures/round4/padre_r4.mp4`, `padre_r4_sheet.png`, `padre_r4_keyframes/*.png`
  - `docs/bakersfieldish_captures/round3/sign_r3.mp4`, `sign_r3_sheet.png`, `sign_r3_keyframes/*.png`
  - `docs/bakersfieldish_captures/round3/glass_r3.mp4`, `glass_r3_sheet.png`, `glass_r3_keyframes/*.png`

---

## Executive Verdict: **FAIL**

While the **demolition cinematography, non-blinding FX/HUD discipline, asset integrity, PK3 reproducibility, Fox rebuild visuals, Padre controlled-demolition visuals, and shatterable glass openings are genuinely high quality**, independent BSP2 Hull-0/Hull-1 collision simulation, QuakeC code tracing, and capture verification uncovered **2 BLOCKER** and **5 MAJOR** objective spec/physics failures (plus 3 moderate and 4 minor defects) that prevent a PASS:

| Severity | ID | Summary |
|---|---|---|
| **BLOCKER** | **B-1** | **Golden West Casino Roof buried in solid geometry (`z = 210..218u` vs actual roof `z = 368u` / Hull-1 top `396u`)**: embeds Spawn #19 (instant player stuck), Go-Kart #19, `SkyPad #03`, `weapon_lightning`, and Mega Health inside solid world geometry, AND **severs the continuous 6-roof `info_skypad` loop** (incoming SkyPads #02 & #08 land 142u above buried SkyPad #03's trigger!). |
| **BLOCKER** | **B-2** | **`Bako_RestoreRoofProps` permanently breaks rebuilt Fox & Padre rooftop `info_skypad`s (and corrupts roof jetpacks/karts)**: `Bako_HideOneRoofEnt` calls `setmodel(e, "")` (zeroing `mins`/`maxs` to `'0 0 0'`), and `Bako_RestoreRoofProps` never saves/restores `setsize` — shrinking both rebuilt rooftop SkyPads from `80×80×62u` to a `2×2×2u` point speck, overwriting roof `item_jetpack` / `misc_gokart` hulls, and risking permanently dead `nextthink` loops. |
| **MAJOR** | **M-1** | **4 of 12 regular `trigger_push` jump pads cannot reach their roofs even with full W air-control (and 4 more fail hands-off)**: `PUSH #00` (Fox West Alley) is completely buried inside solid concrete Ramp 5c (`z = 3..53u` trigger inside `z = 6..57u` ramp); `PUSH #01` (Wall St → Padre Roof) ceiling-bonks Padre's crown overhang at `96.8 ft`; `PUSH #03` & `#04` (Garage L6) bonk Garage walls/overhangs and fail to reach L6 (`54 ft`). |
| **MAJOR** | **M-2** | **Fallen Bakersfield Sign (`bako_sign_rubble`) is NOT kart-rampable or walk-climbable**: confirmed in both BSP2 BFS (`0%` walk-reachable at `dz <= 18u`) and `sign_r3.mp4` (`12_fallen_sweep.png`) — the fallen arch lies across H St as a sheer **46–50u vertical slab** with zero ramp skirts (blocking Go-Karts with `22u` max curb step-up and exceeding Quake's `45.5u` jump height on the 50u north face), contradicting the `"SIGN DOWN ON H ST - RAMP OVER IT!"` HUD prompt and spec. |
| **MAJOR** | **M-3** | **Eric Cannon (`EC_NukeBlastDamage`) dedup race silently drops `1.75x` nuke damage (`~787` dmg) on Padre & Bakersfield Sign**: `findradius(..., 750)` runs *before* `BakoDestruct_RadiusSplash(..., is_nuke=TRUE)` and hits large pieces at `1.0x` center-falloff (`~60–400` dmg on Padre; `~97` dmg on a direct Sign pier hit), setting `bako_*_last_infl` and blocking the `787.5` dmg AABB nuke splash — a direct Eric Cannon nuke on the Sign pier fails to topple the 380 HP Sign! |
| **MAJOR** | **M-4** | **Earthquake is NOT whole-map**: `Bako_TickSmoothShake` zeroes shake beyond `bako_eq_rad` (`4800–5600u` for Fox, `6400–7800u` for Padre) on a `15,502 × 14,130u` map (`20,975u` diagonal). Players at Padre (`8,652u` from Fox), Garage (`9,340u`), Great Castle (`6,050u`), or Golden West (`7,336u`) feel **zero earthquake** during Fox collapse; players at Fox/Larry's/Golden West feel **zero earthquake** during Padre collapse. |
| **MAJOR** | **M-5** | **Padre 1F glass (10 `func_breakable` panes) respawns mid-rubble while Padre is still collapsed**: shattered at collapse `t = 0` (or earlier at 50% HP) with `wait = 120s`, while Padre stays collapsed for `12s collapse + 120s rubble + 28s rebuild = 160s` — all 10 panes re-solidify inside the Padre rubble mound at `t = 120s` (before rebuild even begins at `t = 132s`). |
| **MODERATE** | **D-1** | **Rolling boulder `SOLID_TRIGGER` + `MOVETYPE_BOUNCE` bounce reliability gaps**: `SV_PushEntity` moves `SOLID_TRIGGER` boulders with `MOVE_NOMONSTERS` so boulder motion alone never fires `Bako_BoulderTouch` against players; `Bako_BoulderThink` adds a proximity sweep *only* for `veh_kind > 0` (not `bm_player_head`!), and gates the vehicle sweep on `hspd > 75` (skipping steep downward impacts). |
| **MODERATE** | **D-2** | **Vehicle entombment during Fox/Padre rebuild**: `Bako_NudgePlayersClear` skips `p.movetype == MOVETYPE_NONE` (all vehicle/kart drivers per `vehicle_drive.qc:1407, 1997`) and ignores `veh_kind > 0` entities, trapping drivers on Fox/Padre rubble when walls re-solidify. |
| **MODERATE** | **D-3** | **CI / Minimap / Levelshot packaging gaps**: `.github/workflows/build-zip.yml` does not yet build/cache/ship `zz_bakersfieldish.pk3`; `zz_minimap.pk3` lacks `gfx/minimap/bakersfieldish.png` (minimap renders as an empty dark disc in all 4 captured videos); `levelshots/bakersfieldish.jpg` is missing. |
| **MINOR** | **N-1..N-4** | Nailgun/Super Nailgun spray Q1.5 blood (`blood_saw`/`ThrowBloodSplat`) on `bako_*` concrete/metal/glass (`weapons.qc:4231, 4615`); rooftop spawns relocate to `rubble_max_z + 42` during the 8.6–12s collapse before rubble rises (and lack a kart while collapsed); `Bako_TriggerPadreCollapse` slightly mutates `bako_dur` in-place across collapses #1–#3; `Bako_RestoreGlassPane` does not re-bind `g.touch`. |

---

## Section 1: Layout, Scale, 4 Merged Landmarks & Asset/PK3 Integrity (`bakersfieldish.bsp` vs `bakersfielddowntown.bsp`)

### 1.1 World Bounds, Scale & Skybox — **PASS**
- **Coordinate system & horizontal footprint:** Identical D-frame scale (`1 ft = 12 u`, `SHIFT = (835, -285)`) and exact same X/Y world bounds as `bakersfielddowntown.bsp`:
  - `bakersfielddowntown.bsp`: `mins = [-14111, -7399, -431]`, `maxs = [1391, 6731, 3371]` (`15502 × 14130 × 3802u`, `32,115` visleafs, `275` bmodels).
  - `bakersfieldish.bsp`: `mins = [-14111, -7399, -431]`, `maxs = [1391, 6731, 7211]` (`15502 × 14130 × 7642u`, `33,382` visleafs, `85` bmodels).
- **High Skybox:** Raised by `+3,840u` to `SKY_Z = 7,200u` (`600 ft`), with horizontal `hint` cap at `z = 140 ft` keeping visleafs lean (`33,382`), zero leaks, clean `vis` (`keep_sky_pvs` patched `3035/3923` clusters), and valid `maps/bakersfieldish.lit` (`QLIT v1`, 14.38 MB).

### 1.2 Core Anchors & Padre ↔ Fox Alignment — **PASS**
Independently measured from compiled BSP faces and `bako_*` bmodel unions:
- **Padre Hotel** (`7` `bako_padre_piece` bmodels `*65..*71`): World bbox `[-10389, -6013, 0] .. [-9048, -4570, 1467]` (`D(-30.8, -786.1, 0) .. D(81.0, -665.8, 122.2 ft)`), center `W(-9718.5, -5291.5)` / `D(25.1, -726.0)`. Static world geometry in Padre's slot dropped from `21,678` faces (`bakersfielddowntown.bsp`) to `1,376` faces (sidewalk/floor/1F base only; zero duplicate static upper tower).
- **Fox Theater** (`bako_fox_clock *56` + `7` `bako_fox_piece` `*57..*63`): World bbox `[-10596, 2262, -41] .. [-9036, 4459, 1397]` (`D(-48.0, -96.5, -3.4) .. D(82.0, 86.6, 116.4 ft)`), center `W(-9816.0, 3360.5)` / `D(17.0, -5.0)`. Static world geometry in Fox's slot dropped from `11,886` faces to `865` faces (floor/sidewalk base only).
- **Padre ↔ Fox Alignment:** Delta `dX = -97.5u (-8.1 ft)`, `dY = +8652.0u (+721.0 ft)` — accurately aligned N–S along the H Street spine, matching `bakersfielddowntown.bsp`, with `info_player_start` placed on H St looking straight North between Padre (left) and Parking Garage (right) through the Bakersfield Sign toward Fox Theater!
- **18th & Eye Parking Garage (across from Padre):** Preserved directly east across H St from Padre at `W[-8334, -6252, 0] .. [-4690, -4470, 864]` (`12,851` world faces, `pg_conc`/`pg_deck`/`pg_brick`), center `W(-6459, -5360)` (`dY` from Padre = `-68.5u`, directly across H St).

### 1.3 All 4 Merged Landmarks — **PASS (Geometry/Assets) / FAIL on Golden West Roof Anchor**
Verified compiled BSP faces & textures in each Scheme-A slot against `bakersfielddowntown.bsp`:
1. **Golden West Casino** (`GW-A`, `Eye–Chester / 20th–21st`): Replaced `3,003` downtown filler faces with **`12,593` world faces** (`91` `gwc_*` textures: `gwc_dark`, `gwc_leather`, `gwc_stone`, `gwc_beam`, `gwc_carpet`, `gwc_glass`, etc.) + `12` breakable glass bays, bbox `W[-4218, 2221, 0] .. [-564, 5658, 388]`. **Defect (B-1):** Actual roof at `D(622, 62)` rises to `z = 368u (30.7 ft)` (pitched ridge), whereas `landmark_anchors["golden_west"]["roof_main"]` reported `17.5 ft` (`210u`), burying gameplay entities placed there.
2. **The Great Castle** (`GC-A`, `H–Eye / Service–20th`): Replaced `635` downtown lot faces with **`5,607` world faces** (`gwc_wood`, `gwc_gccmu`, `gwc_red`, `gwc_goldurn`, `gwc_gccarp`) + `2` breakable glass bays, bbox `W[-7099, -132, 0] .. [-4792, 1446, 378]`.
3. **Larry's Warehouse** (`LW-A`, `H–Eye / 20th–21st` N/W, preserving Dagny's Coffee): Replaced `1,584` lot faces with **`6,627` world faces** (`bk_steel`, `bk_asphalt`, `bk_wall`, `bk_wood`, `bk_leg`, `bk3_larry`) + `3` `bk_tv` + `149` LAN props (`36` chairs, `36` monitors, `33` PCs, `18` quakedesks, `26` tables), bbox `W[-8340, 2868, 0] .. [-4794, 5682, 384]`.
4. **The Bakersfield Sign** (`S1`, spanning H St at `D(110, -565)`): Static base piers (`bk_bstucco`, `bk_btan`) + destructible `bako_sign_piece *50` (`727` faces, `W[-9311, -3443, 61] .. [-8089, -3277, 371]`) + `bako_sign_rubble *51` (`826` faces).

### 1.4 Post-Apocalyptic Dressing — **PASS**
- Light-handed and recognizable (`post_apoc_and_traversal.py:264–380`): `19` lane-clear concrete Jersey barriers along curb/perimeter flanks, `14` sidewalk/lot-corner rubble clusters, `6` non-solid leaning light poles, `4` overturned dumpsters, `3` concrete kart stunt ramps, `3` rooftop scaffolding sky-bridges, and warm dusty late-afternoon sun/fog (`_sunlight 235`, `_sunlight_color "1 0.88 0.72"`, `fog "0.22 0.56 0.49 0.41 1 4200 7600 2200 750"`). Confirmed visually across all 4 captures: downtown remains crisp and unmistakably recognizable (not muddy wasteland). (Note: Ramp 5c collides with `PUSH #00` — see **M-1**.)

### 1.5 Asset, VFS & PK3 Reproducibility Audit — **PARTIAL FAIL (D-3)**
- **Zero missing runtime assets:**
  - `1,036 / 1,036` BSP miptex entries resolved (`0` null slots, `0` missing external textures).
  - Skybox `dtsky145_`: all `6/6` sides (`ft/bk/lf/rt/up/dn`) present in VFS.
  - `251` `misc_model` entities (`57` unique MD3 paths): `0` missing in VFS.
  - All `bako_destruct.qc` precached models (`10`), sounds (`26`), and `effectinfo.txt` effects (`11`): `0` missing.
  - All compiled BSP entity classnames exist in server QC (`progs.dat` & `csprogs.dat` up-to-date).
- **`zz_bakersfieldish.pk3` Reproducibility — PASS:**
  - `13` entries (`progs/bako_boulder1..4.{md3,png}`, `progs/bako_glass_shard1..3.md3`, `progs/bako_glass_shard.png`, `progs/bako_rebar.png`), **sorted**, all timestamps `(1980, 1, 1, 0, 0, 0)`, uniform `external_attr = 0x1a40000` (`0o644 << 16`), `ZIP_STORED` for `.png`, `ZIP_DEFLATED` level 9 for `.md3`, **zero loose copies** in `BakersfieldQuake/`.
  - Independent two-run rebuild via `python -I source/mm_tools/build_bakersfieldish_pk3.py` produced byte-identical SHA-256 matching the on-disk `zz_bakersfieldish.pk3`: `3cd13e9cc4183e9c66159f2165ac7f347deb911665c7739a0fdb32398c1e7f48`.
- **Packaging / UI Gaps (`D-3`):**
  - `.github/workflows/build-zip.yml` does **not** yet cache, build, copy, or verify `zz_bakersfieldish.pk3` (AGENTS.md requires every overlay PK3 to be CI-built & cached).
  - `zz_minimap.pk3` contains only `gfx/minimap/bakersfielddowntown.{png,txt}`, not `bakersfieldish.png`, and `bm_minimap_hud.qc:392` loads `gfx/minimap/<map>.png` with no fallback to `bakersfielddowntown.png` — confirmed in all 4 captured videos where the bottom-left circular minimap is an empty dark circle!
  - `levelshots/bakersfieldish.jpg` does not exist (despite `menu_host.qc` listing `bakersfieldish` in the Host LAN map menu).

---

## Section 2: Destructibles Mechanics, Edge Cases & Non-Blinding Audit

### 2.1 Fox Theater (`bako_fox_clock`, 7× `bako_fox_piece`, `bako_fox_rubble`) — **FAIL (B-2, M-4, D-2, N-1, N-2)**
- **Weapon registration (PASS with minor N-1):** `bako_fox_clock` (`*56`, `origin = (-9294, 2532, 976)`, `211×211×138u`, `health = 200`, `takedamage = DAMAGE_AIM`, `SOLID_BSP`) routes cleanly through `T_Damage` (`combat.qc:191–202`) -> `BakoDestruct_OnDamage` and `T_RadiusDamage` / `EC_NukeBlastDamage` -> `BakoDestruct_RadiusSplash`. Verified every weapon class:
  - Hitscan (`weapons.qc:FireBullets` 2048u range — street-to-clock distance across 20th & H is `~1055u < 2048u`; `dn3_shotgun.qc`; `m4.qc`; `garand.qc`; `sniper.qc`): all route via `TraceAttack` -> `ApplyMultiDamage` -> `T_Damage`.
  - Rockets (`100–120` dmg, 2 direct hits), Grenades, Nails/Super Nails (note **N-1**: `spike_touch`/`superspike_touch` at `weapons.qc:4231, 4615` lack `other.bako_material` bypass so nails spray Q1.5 red blood on concrete/glass/metal while still dealing damage), Lightning Gun (within 600u normal / 1800u alt range from roof/jetpack), Wheelman Cannon (`wcannon.qc:812, 906`, upward air-launch reaches `948u` vs clock bottom `907u`), Eric Cannon (`450`/`787` dmg -> 1-shot collapse).
- **Collapse & Climbable Rubble (PASS visually & spatially; FAIL on M-4):**
  - Coupled 2-piece clock tower kinematics (`tower_upper` rides `tower_lower`'s rotated collar via `makevectors` then shears forward past `u_low = 0.48`), ~8.6s collapse (`bako_fox_collapse_dur`), outward debris + dust surge, confirmed smoothly in `fox_r5.mp4`.
  - `bako_fox_rubble` (`*64`, `1691×2270×357u`, peak `z = 341u`) stays `autocvar_bako_fox_rubble_t = 150s` (2.5 min). 2D BFS climbability audit confirms **100% of peak height (`341u`) and 97% of cells are walk-climbable (`dz <= 18u`)**, `100%` jump-climbable!
  - **DEFECT M-4 (Not Whole-Map Earthquake):** Fox collapse calls `Bako_SafeShake` with `radius = 4800..5600u` (`bako_destruct.qc:1563, 2224, 2296`). Since `Bako_TickSmoothShake` (`line 243`) requires `d < bako_eq_rad`, players at Padre (`8,652u`), Parking Garage (`9,340u`), Great Castle (`6,050u`), and Golden West (`7,336u`) feel **zero camera shake**.
- **Slow Visible Rebuild & 2nd Collapse Re-arming (PASS on building; BLOCKER B-2 on rooftop entities, D-2 on vehicles):**
  - After `150s`, Fox sinks rubble over `3.5s`, spawns 3 comedic construction crew NPCs, and visibly rebuilds strictly upright bottom-up over `25s` (`stagehouse` -> `auditorium_roof` -> `facade_s` -> `facade_e` -> `marquee` -> `tower_lower` -> `tower_upper` -> `clock` with welding sparks & bell chime; verified in `fox_r5.mp4` 00:24–00:50).
  - `Bako_ResetFoxIntact` cleanly restores `bako_fox_state = BAKO_ST_INTACT`, `bako_fox_hp = 200`, `bako_fox_clock_ent` (`SOLID_BSP`, `DAMAGE_AIM`, `health = 99999`), and all 7 `bako_fox_piece`s (`bako_piece_*` flags cleared) — Fox CAN be shot and collapsed again cleanly!
  - **BLOCKER B-2 (Rooftop `info_skypad` / `item_jetpack` / `misc_gokart_2` broken after rebuild):** See `bako_destruct.qc:536–560` & `684–699`. `Bako_HideOneRoofEnt` executes `setmodel(e, "")`, which in Quake/Zircon resets `e.mins = e.maxs = '0 0 0'`. `Bako_RestoreRoofProps` never saved/restores `setsize`! On Fox Roof (`x=-10720..-8880, y=2080..4580, z>320`), this hits:
    - `info_skypad` (`W(-10188, 3492, 638)`, `bako_roof_mdl == ""`): restored with `mins = maxs = '0 0 0'` (`2×2×2u` speck instead of `'-40 -40 -26'..'40 40 36'`) -> permanently broken rooftop SkyPad after rebuild!
    - `item_jetpack` (`W(-9900, 3132, 638)`): custom `'-20 -20 -24'..'20 20 20'` overwritten by MD3 bounds; `avelocity` not restored; `Jetpack_Spin` lost if `nextthink <= time` at hide time.
    - `misc_gokart_2` (`W(-10164, 3168, 630)`): custom kart `setsize` overwritten; `Veh_Think` permanently dies if `nextthink <= time` on hide tick.
  - **MODERATE D-2 (Vehicle Entombment):** `Bako_NudgePlayersClear` (`bako_destruct.qc:429`) skips `p.movetype == MOVETYPE_NONE` (true for all vehicle/go-kart drivers per `vehicle_drive.qc:1407, 1997`) and has no `veh_kind > 0` loop (unlike `Bako_LiftPlayersOnto`), so driving a kart on Fox rubble during rebuild traps the player inside solid walls.

### 2.2 Padre Hotel (7× `bako_padre_piece`, `bako_padre_rubble`) — **FAIL (B-2, M-3, M-4, M-5, D-1, D-2)**
- **Toughness & Weapon Registration (PASS on standard/Wheelman; FAIL M-3 on Eric Cannon):**
  - Unified HP pool: `autocvar_bako_padre_hp = 2600` (**13×** Fox Clock's `200 HP` and **6.8×** Bakersfield Sign's `380 HP`).
  - Rockets (`100–120` dmg, deduplicated per projectile): **~22–26 direct rockets**.
  - Wheelman Cannon (`130` T0 .. `262` T3 direct / `95..191` splash): **~10 full-charge T3 shots** (or `~20` quick taps).
  - Every standard weapon (shotgun, SSG, DN3 shotgun, M4, Garand, sniper, nailgun, super nailgun, lightning gun, grenades, rockets, melee) registers cleanly from street level against `tier1` (`z = 0..393u`) and all 7 `bako_padre_piece`s (`takedamage = DAMAGE_AIM`, `SOLID_BSP`).
  - **MAJOR M-3 (Eric Cannon `EC_NukeBlastDamage` Dedup Race):** In `eric_cannon.qc:670–705`, `findradius(inflictor.origin, 750)` loops over `bako_padre_piece` entities *before* line 705 calls `BakoDestruct_RadiusSplash(..., is_nuke = TRUE)` (`1.75x` multiplier -> `787.5` peak dmg). Because `bako_padre_piece`s are huge (`tier1` is `1324×1439u`), a nuke hitting Padre's East/South wall within `750u` of a piece center gets hit FIRST by `findradius` at `1.0x` center-falloff (e.g. `~60–350` dmg), setting `bako_padre_last_infl = inflictor; bako_padre_last_t = time;` (`bako_destruct.qc:1924–1925`), which causes `BakoDestruct_RadiusSplash`'s `~787` dmg nuke call to **silently return at line 1923**! (Exact same bug hits Bakersfield Sign: a direct nuke on the West pier `588u` from Sign center deals `450 * (1 - 588/750) = 97.2` dmg via `findradius` and drops the `787.5` dmg nuke splash, failing to collapse the 380 HP Sign!)
- **Controlled Demolition Visuals & Climbable Rubble (PASS visually & spatially; FAIL M-4, M-5, B-2):**
  - Progressive 75%/50%/25% dark-grey window smoke on visible East & South facades + top-right HUD % bar, 10 perimeter 1F–3F charge pops (`0.05..2.05s`), coupled 12s inward V-collapse (crown locked to `tier4`), massive warm-tan matte dust surge (`padre_r4.mp4`), and climbable 2-story rubble (`bako_padre_rubble *72`, peak `371u`, stays `120s`, **100% of peak / 99% of cells walk-climbable at `dz <= 18u`**).
  - **MAJOR M-5 (Padre 1F Glass Respawns Inside Collapsed Rubble):** All 10 Padre 1F `func_breakable` glass bays (`#00..#09`) are shattered at collapse `t = 0` (`bako_destruct.qc:1661`, or earlier at 50% HP on line 1964) and schedule respawn at `time + 120s` (`wait = 120`, line 3307). Padre stays collapsed for `12s collapse + 120s rubble + 28s rebuild = 160s`. Thus at `t = 120s` (while Padre is still in `BAKO_ST_RUBBLE`), `Bako_TickGlass` calls `Bako_RestoreGlassPane` on all 10 panes, re-spawning solid translucent storefront windows right inside the Padre rubble mound!
  - **MAJOR M-4:** Padre earthquake radius maxes at `7800u` (`bako_destruct.qc:2941`), missing Fox (`8,652u`), Larry's (`~9,500u`), and Golden West (`~11,500u`).
  - **BLOCKER B-2:** Padre rebuild breaks Padre Roof `info_skypad` (`W(-10020, -5580, 1256)`), 2 `item_jetpack`s (`JP #01, #02`), and 2 `misc_gokart`s (`#3, #4`) via missing `setsize` restoration.
- **Flying / Rolling Boulders Player Bounce Audit — MODERATE DEFECT (`D-1`):**
  - `Bako_SpawnBoulder` (`bako_destruct.qc:920–970`) spawns 3 waves × 8 = 24 heavy concrete boulders (`progs/bako_boulder1..4.md3`, `setsize '-22 -22 -22'..'22 22 22'`) with `movetype = MOVETYPE_BOUNCE`, `solid = SOLID_TRIGGER`, `touch = Bako_BoulderTouch`, `think = Bako_BoulderThink`.
  - When `Bako_BounceTarget` (`lines 750–807`) IS called, its knockback math is great: walking players receive `dir * bound(380, spd*0.85, 640) + '0 0 340..400'`, `FL_ONGROUND` cleared, `15` dmg + smooth shake; vehicles (`veh_kind > 0`) receive `dir * bound(240, spd*0.65, 420) + '0 0 190'`, `veh_air = TRUE`, `veh_vz >= 190`.
  - **However (`D-1`):** Because `d.solid == SOLID_TRIGGER`, Quake/Zircon `SV_PushEntity` moves boulders with `MOVE_NOMONSTERS` — so the boulder's own movement **never** generates a touch against `SOLID_SLIDEBOX` players/bots! Triggering `Bako_BoulderTouch` for a player relies solely on the player's own `SV_LinkEdict(player, true)` pass overlapping the boulder on a server frame:
    - Fast boulders (`620–1000 u/s`) or boulders hitting stationary/passenger players (`MOVETYPE_NONE`) can miss `Bako_BoulderTouch`.
    - Notably, `Bako_BoulderThink` (`lines 887–899`) explicitly works around this for `veh_kind > 0` (`MOVETYPE_NONE` vehicles!) with a `< 68u` distance poll, **but omits `bm_player_head` / `FL_MONSTER`** AND gates the vehicle poll on horizontal speed `hspd > 75` (skipping steeply falling rocks hitting a kart from above!). Adding a `bm_player_head` proximity sweep using `vlen(self.velocity) > 65` closes this completely.

### 2.3 Bakersfield Sign (`bako_sign_piece`, `bako_sign_rubble`) — **FAIL (M-2, M-3, M-4)**
- **Weapon registration:** Shootable (`bako_sign_piece *50`, `380 HP`, `SOLID_BSP`, `DAMAGE_AIM`) by all standard weapons & Wheelman Cannon (fails single-shot Eric Cannon pier nuke due to **M-3**).
- **Topple, Debris & Earthquake:** Clean pier-anchored sparks/debris, accelerating `u^2.4` north topple (`4.2s`) with `0.52s` damped elastic bounce and full-width warm-tan dust surge (`sign_r3.mp4`). Earthquake radius is `4600–5400u` (not whole-map, **M-4**). Stays down `120s` then crane-hoists upright over `10s`.
- **MAJOR M-2 (Not Rampable / Barely Jumpable Aftermath):**
  - Center-road BSP2 profile of `bako_sign_rubble *51` at H St (`x = -8700`, `y = -3136..-3024`): jumps vertically from road `z = 0` straight to **`top_z = 46u` (south edge)** and **`top_z = 50u` (north edge)** across `y = -3120..-3040` with **zero sloped ramp wedges**!
  - 2D BFS climbability check: `WALK (dz <= 18u): 0 / 614 cells (0% reachable!)`.
  - Go-Karts (`22u` max curb step-up, `gokart.qc:580`) cannot drive or ramp over a `46–50u` sheer curb — confirmed visually in `sign_r3.mp4` (`00:15–00:17`, `12_fallen_sweep.png`), where the boxy yellow arch sits across H St like a concrete roadblock right in front of the white Go-Kart! Even walking players (Quake jump peak `= 270^2 / (2*800) = 45.56u`) cannot clear the `50u` north edge without a rocket/jetpack/pad boost.

### 2.4 Shatterable Glass Windows (`func_breakable`) — **PASS (with M-5 on Padre 1F respawn)**
- **Exact Count & Building Distribution (`52` real cut-out `func_breakable` glass bays across `6` buildings):**
  1. **Dagny's Coffee / James Building:** `18` bays (`7` 1F storefront + `11` 2F ribbon/north windows)
  2. **Golden West Casino:** `12` bays (`8` 1F entryway/rotunda + `4` 2F clerestory)
  3. **Padre Hotel (1F Lobby):** `10` bays (`5` south 18th St + `5` east H St) — *subject to M-5 mid-rubble respawn*
  4. **Nile Theater / 19th St Storefronts (`D(-180..-4, -518)`):** `6` bays
  5. **1818 H St Shopfront (adjacent to Parking Garage, `D(152..181, -725..-678)`):** `4` bays
  6. **The Great Castle:** `2` bays (north entryway)
  - *(Note: Fox Theater and Larry's Warehouse currently have 0 shatterable glass bays; Padre's 121 upper-floor panes were absorbed into the collapsible bmodels.)*
- **Mechanics & Hollow Openings:** Every bay has `style 3` (`BTYPE_GLASS`), `health 15`, `alpha 0.52`, `wait 120`, `takedamage = DAMAGE_AIM` (`breakable.qc:1466`). Verified responsive to all weapons (`T_Damage`, `TraceAttack`, `BakoDestruct_RadiusSplash`), fast player smash-through (`BakoDestruct_GlassTouchCheck`: `vlen(velocity) > 220`), and go-kart/vehicle smash-through (`Bako_TickGlass` 20 Hz `58×58` sweep at `speed > 80`).
- **BSP2 Hollow-Opening Verification:** All 40 axis-aligned bays and 11/12 diagonal Golden West bays have `CONTENTS_EMPTY` (`-1`) on both sides along their true face normals (bay `#41` sits beside a doorway corner). Confirmed visually in `glass_r3.mp4`: 20 translucent faceted shards (`alpha 0.56`), cool sparkle mist, clean hollow entry into Padre 1F lobby and clear view back out!

### 2.5 Non-Blinding Guarantee — **PASS (100% Compliant)**
- **ZERO `bf` / ZERO `v_cshift`:** Audited `bako_destruct.qc`, `bako_destruct_defs.qc`, `breakable.qc`, and all modified CSQC files — zero `bf` flashes and zero `v_cshift` screen tints anywhere in the destructibles pipeline.
- **ZERO opaque center boxes (`CLAUDE.md`):** `BM_DrawBakoDestructHUD` (`csqc/bm_hud.qc:1333–1404`) draws strictly drop-shadowed top-right corner text (`BM_ShadowColorRight` stacked on `bm_topright_y`) + a 54×1px hairline underline bar under `PADRE HOTEL XX%`. Confirmed clean & mutually exclusive across all HUD modes (`hud_style 0..4` and `showHUD 0`) and visually verified across all 4 MP4 videos.
- **Strictly clamped non-blinding camera shake:** `Bako_TickSmoothShake` (`bako_destruct.qc:207–267`) runs at 60 Hz with slew clamp `<= 0.42°/frame` and hard angle clamps `pitch ∈ [-3.1°, +3.1°]`, `yaw ∈ [-0.7°, +0.7°]`, `roll ∈ [-2.1°, +2.1°]` (reduced to `0.55×` roll in vehicles).
- **Translucent matte dust:** All 5 dust/smoke particle effects in `effectinfo.txt` (`bako_demolition_dust_surge`, `bako_collapse_plume`, `bako_window_smoke`, `bako_masonry_burst`, `bako_rock_dust`) strictly use `type alphastatic` + `blend alpha` with warm stucco/concrete RGB tones and `alpha <= 118` (only tiny brief `0.34–0.50s` charge flashes and welding sparks use `blend add`). Confirmed across `fox_r5.mp4`, `padre_r4.mp4`, and `sign_r3.mp4`: zero whiteout or blinding screens!

---

## Section 3: Traversal Physics Audit (Spawns, Go-Karts, Jetpacks, Jump Pads, Chained SkyPads)

### 3.1 Spawns (36) & Go-Kart Near Every Spawn (36) — **FAIL (B-1, B-2, N-2)**
- **Pairing coverage:** `35 info_player_deathmatch + 1 info_player_start = 36` spawns, paired 1-to-1 with `36` go-karts (`6` each of `misc_gokart_1..6`), every spawn's nearest kart is `131.8–138.5u` (`11.0–11.5 ft`) away, `0` kart-kart overlaps (`<72u`) and `0` kart-spawn overlaps (`<48u`).
- **35 of 36 pairs** have completely clean Hull-1 clearance, valid floor drop, and unobstructed LOS.
- **BLOCKER B-1 — Golden West Roof Spawn #19 & Kart #19 Embedded in Solid:**
  - `Spawn #19` (`info_player_deathmatch` at `W(-2556, 4164, 218)` / `D(622.0, 62.0, 18.2)`): **World Hull-1 = `CONTENTS_SOLID (-2)`** (`Hull 0 solid: z=176..368u`, `Hull 1 solid: z=116..396u`, `178u` beneath roof surface!). Any player spawning here is instantly stuck inside solid roof geometry!
  - `Kart #19` (`misc_gokart_2` at `W(-2649, 4071, 210)` / `D(614.2, 54.2, 17.5)`): **World Hull-0 & Hull-1 = `CONTENTS_SOLID (-2)`** (`Hull 1 solid: z=144..378u`), completely buried and inaccessible.
  - Also buried in Golden West's pitched roof ridge: `weapon_lightning` (`ent #1395`, `D(602, 62, 18.2)`, `h0=-2, h1=-2`) and Mega Health (`ent #1416`, `D(622, 86, 18.2)`, `h1=-2`).
  - *Root cause:* Golden West's roof at `Dy = 60` is a `368u (30.7 ft)` ridge (`Dy = 80` is `304u / 25.3 ft`), while the flat `192u (16.0 ft)` roof decks are at `Dy = 100..120` (north) and `Dy = 20` (south).
- **Collapsible Roof Spawns & Karts (3 pairs — B-2 & N-2):**
  - `Spawn #03` + `Kart #03` (`Padre 2F Terrace`, `D(-6, -696, 18.8)`), `Spawn #04` + `Kart #04` (`Padre Roof`, `D(10, -760, 104.8)`), and `Spawn #13` + `Kart #13` (`Fox Roof`, `D(-12, -10, 53.2)`).
  - On collapse, `Bako_HideOneRoofEnt` relocates the `info_player_deathmatch` spawns onto `rubble_max_z + 42` and hides the 3 rooftop karts at `z - 2400`:
    - **N-2:** During the 8.6s–12s collapse *before* rubble rises, spawning at the relocated point drops the player ~340u onto the floor/rising rubble, and while collapsed there is no paired go-kart at that spawn.
    - **B-2:** Upon rebuild, `Bako_RestoreRoofProps` does not restore `setsize` (and risks killing `Veh_Think` if `nextthink <= time` on hide).

### 3.2 Jetpacks (`13` `item_jetpack` + `3` `item_armor2` Bonus Jetpacks) — **PASS (with B-2 on 3 rooftop packs)**
- **Distribution:** Sensibly concentrated at map perimeter corners (`NW 21st & G`, `SW 18th & G`, `SE 18th & Chester`) and elevated landmark rooftops (`Garage L6`, `Padre 2F/8F`, `Fox Roof`, `Golden West Roof/Courtyard`, `Larry's B76/B45 Roofs`, `Great Castle Watchtower`, `H St Sign Plaza`) + 3 street yellow-armor bonus jetpacks.
- **`droptofloor` verification:** Simulated exact `item_jetpack` spawn (`origin + '0 0 24'`, `setsize '-20 -20 -24'..'20 20 20'`, `droptofloor`) against BSP2 Hull-1 + intact bmodels: **13/13 pass cleanly** (`dz = 10–26u`, `0` startsolid, `0` failed drops — even `JP #04` on Golden West at `D(644, 44, 27.6)` starts at `z = 355u`, clearing `top_h1_solid = 342u` and landing cleanly `10u` down!).
- Note: The 3 jetpacks on Padre/Fox roofs (`JP #01, #02, #03`) are subject to **B-2** (`setsize` / `avelocity` not restored after rebuild).

### 3.3 Regular Jump Pads (`12` `trigger_push`) & Creative Touches — **FAIL (M-1)**
Simulated every `trigger_push` using exact Quake `SetMovedir` (`subs.qc:12–31`), `v = speed * movedir * 10` (`triggers.qc:824`), `g = 800`, and Hull-1 collision/sliding (both **hands-off** and **full W Quake air-control** `wishspeed = 30, accel = 10`):

| # | Intended Route (`make.log`) | Target Z | Hands-Off Result | Hold-W Result | Diagnosis |
|---|---|---|---|---|---|
| 00 | Fox West Alley → Fox Roof | `51.0 ft` | `10.8 ft` (FAIL) | `54.9 ft`* | **BROKEN (`M-1`):** Trigger box (`z = 3..53u`) is **completely buried inside solid concrete Ramp 5c** (`post_apoc_and_traversal.py:358`, `z = 6..57u` at `D(-58.5, 22)`) — unreachable from alley! |
| 01 | Wall St → Padre Roof | `102.5 ft` | `33.8 ft` (FAIL) | `33.8 ft` (**FAIL**) | **BROKEN (`M-1`):** Hits `east_wing` at `52.3 ft`, then **ceiling-bonks `crown` overhang at `96.8 ft`** (`< 102.5 ft`), falling to `33.8 ft`! |
| 02 | 18th St → Padre 2F Terrace | `19.1 ft` | `2.6 ft` (FAIL) | `30.5 ft` (PASS) | Wall-bonks `tier1` at `8.4 ft`; fails hands-off, requires holding W. |
| 03 | 18th St → Garage L6 Roof | `54.0 ft` | `2.6 ft` (FAIL) | `49.0 ft` (**FAIL**) | **BROKEN (`M-1`):** Wall-bonks Garage at `46.6 ft` / parapet ceiling at `55.0 ft`; misses L6 (`54 ft`). |
| 04 | Eye St → Garage L6 Roof | `54.0 ft` | `12.9 ft` (FAIL) | `27.8 ft` (**FAIL**) | **BROKEN (`M-1`):** **Ceiling-bonks** Garage overhang at `33.0..55.0 ft`; cannot reach L6! |
| 05 | Garage L6 → Padre Roof Kart Boost | `102.5 ft` | `105.0 ft` (PASS) | `105.0 ft` (PASS) | Clean arc onto Padre crown (`max 126.3 ft`). |
| 06 | 20th St → Fox Marquee Deck | `22.0 ft` | `3.1 ft` (FAIL) | `23.4 ft` (PASS) | Wall-bonks marquee at `16.3 ft`; fails hands-off, requires holding W. |
| 07 | Eye St → Great Castle Roof | `13.0 ft` | `18.3 ft` (PASS) | `18.3 ft` (PASS) | Clean unobstructed arc. |
| 08 | 20th St → Golden West Roof | `16.0 ft` | `21.4 ft` (PASS*) | `21.4 ft` (PASS*) | Bonks GW upper `26.4 ft` clerestory, lands on lower `21.4 ft` roof terrace (not `30.7 ft` ridge). |
| 09 | H St → Larry's Warehouse Roof | `17.0 ft` | `19.5 ft` (PASS) | `19.5 ft` (PASS) | Clean unobstructed arc. |
| 10 | Dagny's Lot → Dagny's Roof | `28.0 ft` | `3.0 ft` (FAIL) | `31.0 ft` (PASS) | Wall-bonks Dagny's north wall at `28.3 ft`; fails hands-off, requires holding W. |
| 11 | Wall St Alley → Tattoo Tower Roof | `54.0 ft` | `56.3 ft` (PASS) | `56.3 ft` (PASS) | Clean unobstructed arc. |

- **Creative Touches (PASS):** `3` Eric Deason Cannons (Garage L6 overlooking Padre, H & 19th Plaza overlooking Fox/Sign, Golden West Plaza), `2` Winged Johns, `1` Rocket Rider, `1` Bako Van, `1` GT Car, `3` rooftop scaffolding sky-bridges (Nile→Tevis, Dagny's→Larry's B45 with ramp, Garage L6 sniper catwalk), and `3` concrete stunt ramps (note Ramp 5c overlaps `PUSH #00`).

### 3.4 Chained Super Jump Pads (`10` `info_skypad`) — **FAIL (B-1, B-2)**
Simulated every `info_skypad` with exact `SkyPad_CalcVel(org + '0 0 2', pos1, height)` (`skypad.qc:43–64`, `g = 800`) against World Hull-1 + intact bmodels + `SKY_Z = 7200u`:

| # | Route | Apex (`SKY_Z=7200`) | Max Axis Vel (`<6500`) | Mid-Flight Obstruction | Landing Chain Dist | Status |
|---|---|---|---|---|---|---|
| 00 | Padre Roof → Fox Roof | `3400u` (`3800u` margin) | `1851 u/s` | None | `0.0u` to `#01` | **PASS** intact / **FAIL (`B-2`)** after rebuild |
| 01 | Fox Roof → Larry's Roof | `3000u` (`4200u` margin) | `1943 u/s` | None | `0.0u` to `#02` | **PASS** intact / **FAIL (`B-2`)** after rebuild |
| 02 | Larry's Roof → **GW Roof** | `3100u` (`4100u` margin) | `2142 u/s` | **HITS SOLID ROOF at `z=391u`** (`t=5.28/5.36s`) | `0.0u` nominal, **142u above buried `#03` trigger!** | **FAIL (`B-1`)** |
| 03 | **GW Roof** → Great Castle | `3200u` (`4000u` margin) | `2184 u/s` | **STARTS IN SOLID (`z=218u` vs `396u` top), hits ceiling at `t=0.065s`** | `0.0u` to `#04` | **FAIL (`B-1`)** |
| 04 | Great Castle → Garage L6 | `3100u` (`4100u` margin) | `2148 u/s` | None | `0.0u` to `#05` | **PASS** |
| 05 | Garage L6 → Padre Roof | `3300u` (`3900u` margin) | `2049 u/s` | None | `0.0u` to `#00` | **PASS** intact / **FAIL (`B-2`)** after rebuild |
| 06 | H St Sign Plaza → Fox Roof | `2900u` (`4300u` margin) | `2141 u/s` | None | `0.0u` to `#01` | **PASS** intact |
| 07 | SW 18th & G → Larry's Roof | `3900u` (`3300u` margin) | `2487 u/s` | None | `0.0u` to `#02` | **PASS** |
| 08 | SE 18th & Chester → **GW Roof** | `3700u` (`3500u` margin) | `2422 u/s` | **HITS SOLID ROOF at `z=365u`** (`t=5.91/5.98s`) | **142u above buried `#03` trigger!** | **FAIL (`B-1`)** |
| 09 | GW Courtyard → Garage L6 | `3600u` (`3600u` margin) | `2389 u/s` | None | `0.0u` to `#05` | **PASS** |

- **Velocity & Skybox Clearance:** All 10 trajectories stay well below `sv_maxvelocity 6500` (peak `2487 u/s`) and well below `SKY_Z = 7200u` (`3300–4300u` margin).
- **Chaining Broken at Golden West (`B-1`):** Although the designer wired an exact 6-roof closed loop (`0.0u` landing-to-next-pad spacing!) + 4 street feeders, the Golden West Casino roof node (`D(622, 62, 18.2)`) is **buried 178u inside the `30.7 ft` solid roof ridge**, making `SkyPad #03` unreachable from `#02` and `#08` and breaking the continuous loop! Moving the Golden West roof anchor onto either the flat north roof deck (`D(622, 108, 16.0)`, `192u`) or atop the `30.7 ft` ridge (`z >= 370u / 30.8 ft`) fixes Spawn #19, Kart #19, SkyPads #02/#03/#08, and both roof pickups simultaneously!
- **Collapsed Padre/Fox Rooftop SkyPads (`B-2`):**
  - *During collapse/rubble:* Both rooftop pad pedestals were smartly attached into `bako_padre_piece[crown]` and `bako_fox_piece[auditorium_roof]` (`post_apoc_and_traversal.py:555–563`), and `Bako_HideRoofProps` hides the `info_skypad` trigger + all 5 `skypad_fx` visual entities so nothing floats in midair. Incoming players from Garage L6 (`#05`) or H St (`#06`) fall onto the rubble protected by `skypad_safe_t = time + 10.0` (zero fall damage per `client.qc:3809`), though the roof-to-roof chain pauses until rebuild.
  - *After rebuild:* **BLOCKER B-2** breaks both rebuilt rooftop `info_skypad` triggers permanently because `Bako_RestoreRoofProps` does not restore `setsize(e, '-40 -40 -26', '40 40 36')`!

---

## Section 4: Prioritized Fix Checklist for Builders

1. **[B-1] Fix Golden West Casino roof height (`merged_landmarks.py` / `post_apoc_and_traversal.py`):** Move `golden_west.roof_main` off the `368u` (`30.7 ft`) ridge to the flat `192u` (`16.0 ft`) north deck (e.g., `D(622, 108, 16.0)`) OR raise its Z above the ridge (`31.0 ft` / `372u`), and re-verify Spawn #19, Kart #19, SkyPads #02/#03/#08, `weapon_lightning`, and Mega Health in compiled BSP Hull-1.
2. **[B-2] Save & restore `mins`/`maxs` (`setsize`), `avelocity`, and safe `nextthink` in `Bako_HideOneRoofEnt` / `Bako_RestoreRoofProps` (`bako_destruct.qc:508–702`):** Add `.vector bako_roof_min, bako_roof_max, bako_roof_avel`, call `setsize(e, e.bako_roof_min, e.bako_roof_max)` *after* `setmodel(...)` on restore, and restore `nextthink = time + max(0.05, e.bako_roof_nthink)` whenever `e.bako_roof_think != SUB_Null`.
3. **[M-1] Fix broken `trigger_push` pads (`post_apoc_and_traversal.py:876–889`):** Move `PUSH #00` out from under Ramp 5c (`x = -67.5..-50, y = 12..28`); pull `PUSH #01, #02, #03, #04, #06, #10` further out from vertical facades/overhangs (or increase `apex_extra_ft` / steepen launch) and verify every pad with a BSP Hull-1 trajectory test.
4. **[M-2] Make `bako_sign_rubble` genuinely kart-rampable (`merged_landmarks.py`):** Add tapered low-angle ramp wedges (`<= 18–22°` slope, `<= 12u` leading lip) on both north & south faces of the fallen Bakersfield Sign arch across H St so Go-Karts and walking players smoothly ramp straight over it.
5. **[M-3] Fix Eric Cannon nuke dedup race (`eric_cannon.qc:670–705` or `bako_destruct.qc:1920, 2003`):** Either skip `head.bako_group > 0` inside `EC_NukeBlastDamage`'s `findradius` loop (letting `BakoDestruct_RadiusSplash(..., is_nuke = TRUE)` be the single authoritative `1.75x` AABB splash!), or track `bako_last_dmg` so a higher same-tick damage from the same inflictor applies the delta `new_dmg - prev_dmg`.
6. **[M-4] Make collapse earthquakes genuinely whole-map (`bako_destruct.qc:242–253`):** Either set `bako_eq_rad = 24000` (with gentle distance floor e.g. `frac = bound(0.28, 1.0 - d/24000, 1.0)`) on Fox/Padre/Sign collapses so players across all of `15,502 × 14,130u` downtown feel the tremor smoothly without blinding anyone.
7. **[M-5] Hold Padre 1F glass respawn while Padre is collapsed (`bako_destruct.qc:3390–3424`):** In `Bako_RestoreGlassPane`, if `g` is within Padre's footprint and `bako_padre_state != BAKO_ST_INTACT`, defer `g.bako_glass_respawn_t = time + 5.0; return;` (and re-trigger restore on `Bako_ResetPadreIntact`).
8. **[D-1, D-2, D-3, N-1]:** Add `bm_player_head` proximity sweep (gated on `vlen(self.velocity) > 65`) in `Bako_BoulderThink`; extend `Bako_NudgePlayersClear` to lift/push `veh_kind > 0` vehicles; wire `zz_bakersfieldish.pk3` into `.github/workflows/build-zip.yml`, add `gfx/minimap/bakersfieldish.png` (or fallback in `bm_minimap_hud.qc`) and `levelshots/bakersfieldish.jpg`; add `other.bako_material` early-out in `spike_touch`/`superspike_touch` (`weapons.qc`).
