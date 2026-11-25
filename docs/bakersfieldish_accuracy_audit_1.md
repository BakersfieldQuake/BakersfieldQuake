# Bakersfield-ish (`maps/bakersfieldish.bsp`) — Independent Accuracy Audit #1

**Auditor:** Fresh Accuracy Auditor #1 of 4 (`audit-1`, zero prior build history)
**Audit Date:** 2026-11-25
**Target Artifacts Audited:**
- `maps/bakersfieldish.bsp` (40,958,428 bytes, BSP2, SHA-256 prefix `e84a632c84e12dfc`, identical to `source/downtown/out/bakersfieldish.bsp`)
- `maps/bakersfieldish.lit` (14,382,320 bytes, SHA-256 prefix `5c1815dbb16c237f`)
- `maps/bakersfielddowntown.bsp` (37,081,900 bytes, baseline reference) & `maps/bklan6.bsp` (19,881,536 bytes, original landmark source)
- `zz_bakersfieldish.pk3` (339,596 bytes), `bakersfield.pk3`, `zz_*.pk3`, `progs.dat` (3,768,278 bytes), `csprogs.dat`, `effectinfo.txt`
- Real downtown Bakersfield references: `source/downtown/refs/osm_ft.json`, `source/downtown/refs/osm_plan.png`, Google Maps satellite/StreetView refs (`padre-hotel/008.jpg`, `fox-theater/008.jpg`, `padre-garage/006.jpg`)
- Build & QC source: `source/downtown/tools/make_bakersfieldish.py`, `source/downtown/tools/dt_hull.py`, `source/downtown/pieces/bakersfieldish/*.py`, `source/qc_combat_decomp/bako_destruct*.qc`, `skypad.qc`, `triggers.qc`, `combat.qc`, `eric_cannon.qc`, `breakable.qc`, `bm_match.qc`
- Live capture evidence: `docs/bakersfieldish_captures/round5/fox_r5_sheet.png` (+ `05_tower_slam.png`), `round4/padre_r4_sheet.png` (+ `07_mid_pancake.png`, `12_rubble_aftermath.png`), `round3/sign_r3_sheet.png` (+ `07_street_impact.png`), `round3/glass_r3_sheet.png`
- **Methodology:** Direct binary BSP2 lump parsing (worldspawn, submodels, faces, planes, nodes, clipnodes Hull-0/Hull-1, entities, miptexes), parabolic physics simulation against compiled BSP Hull-1 clipnodes, BFS climbability probing, virtual filesystem asset integrity sweep across all pk3s and loose directories, QuakeC runtime audit, and visual frame verification. (`zircon_beta_gcc.exe` was NOT launched.)

---

## OVERALL VERDICT: **FAIL**

### Executive Summary

| Audit Pillar | Status | Quantitative Summary |
|---|---|---|
| **1. Downtown Layout, Scale & Sacred Anchors** | **PASS** | 1:1 faithful preservation vs `bakersfielddowntown.bsp` & real OSM/satellite Bakersfield (`0.00 ft` delta on Padre/Garage/Dagny's/PG&E; 6-level Garage & `116.42 ft` H St gap exact; Padre–Fox H St spine intact). |
| **2. All Four Merged Landmarks & Asset Integrity** | **PASS** | Golden West Casino (`1:1`), The Great Castle (`1:1`), Larry's Warehouse (`1:1`), and Bakersfield Sign (`90.7%` span) cleanly placed in non-overlapping Scheme A slots; **0 missing textures** (1,036 BSP miptexes), **0 missing models** (58 paths / 269 instances), **0 missing QC models/sounds/effects/MD3 skins**. |
| **3. Look & Feel + High Skybox** | **PASS** | Skybox raised from `3,360 u` (`280 ft`) to `7,200 u` (`600 ft`) (**2.14× taller**); warm dusty post-apoc sun/fog with light-handed dressing (~59 small props over 15,502 × 14,130 u) — unmistakably downtown Bakersfield, not a wasteland. |
| **4. Destructibles (Fox, Padre, Sign, Glass)** | **FAIL (Runtime & Clipnode Bugs)** | Core demolition visuals, physics, dust clouds, rolling boulders, smooth 60 Hz shake, Fox slow rebuild, and 52 hollow glass bays across 7 building clusters are cinema-grade — **but** 3 ground-floor Fox/Padre spawns & karts get trapped inside solid rubble on collapse, `Bako_RestoreRoofProps` wipes `info_skypad` trigger `mins`/`maxs` on rebuild, Padre 1F glass respawns prematurely inside rubble (`t=120s`), and `bako_sign_rubble` has Hull-1 clipnode spikes (`10.5–10.8 ft`) blocking fallen arch flanks. |
| **5. Traversal Completeness (Spawns, Karts, Jetpacks, Jump Pads, SkyPads)** | **FAIL (Critical Blockers)** | A proven inverted plane-normal sign bug in `dt_hull.py:160` blinded placement to all non-axial brushes: **Golden West Roof SkyPad hub (`#04`), Spawn `#20`, Kart `#20`, and Lightning Gun are buried 12+ ft inside solid `worldspawn` (`Z=15.5..30.5 ft` gable roof)** — breaking the continuous 6-landmark SkyPad chain (`#03` & `#09` hit the roof ridge at `29.8–32.3 ft`). Additionally, **6/12 regular `trigger_push` jump pads fail 0/9** (1 buried under concrete ramp, 5 slam into building walls) + **1 fails 6/9**; **3 rooftop spawns sit `0.0 u` directly inside `info_skypad` triggers**; and 5 extra pickups/cannon clip solids. |

---

## Section 1: Downtown Layout, Scale & Sacred Anchors (`bakersfieldish.bsp` vs `bakersfielddowntown.bsp` + Real Bakersfield)

All coordinates are reported in Downtown **D-frame feet** (`1 ft = 12 Quake units`, `SHIFT = (835.0, -285.0)` so `D_x = u_x / 12 + 835`, `D_y = u_y / 12 - 285`, `D_z = u_z / 12`).

### 1.1 World Bounds & Global BSP2 Metrics

| Metric | `maps/bakersfielddowntown.bsp` | `maps/bakersfieldish.bsp` | Delta / Notes |
|---|---|---|---|
| Format | BSP2 (`0x32505342`) | BSP2 (`0x32505342`) | Same format |
| File size | 37,081,900 B | 40,958,428 B | +10.5% |
| Worldspawn XY bounds (u) | `[-14111, 1391] × [-7399, 6731]` | `[-14111, 1391] × [-7399, 6731]` | **0.0 u delta** (`15,502 × 14,130 u` = `1,291.8 × 1,177.5 ft`) |
| Worldspawn Z bounds (u) | `[-431, 3371]` (sky top `3,360 u` / `280 ft`) | `[-431, 7211]` (sky top `7,200 u` / `600 ft`) | **+3,840 u (+320 ft, 2.14× sky height)** |
| Submodels (`models` lump) | 275 | 85 | Leaner (84 bmodels: 19 destructible + 52 glass + 12 push + 1 wall) |
| Faces / Vertices | 116,319 / 144,520 | 151,142 / 178,822 | +30% detail from 4 merged landmarks & organic rubble |
| Textures (miptex) | 927 | 1,036 | +109 landmark textures |
| Entities | 1,576 | 1,566 | Cleanly within engine budget |

### 1.2 Sacred Anchors & Downtown Buildings Comparison (Compiled BSP Geometry, Excluding Hidden Rubble)

| Landmark / Block | `bakersfieldish.bsp` D-feet BBox `(x0..x1, y0..y1, z0..z1)` | Dims (ft) `W × D × H` | `bakersfielddowntown.bsp` Dims (ft) | Delta `(ish − dt)` `(dx0,dy0,dz0,dx1,dy1,dz1)` | Real Bakersfield OSM / Satellite Check |
|---|---|---|---|---|---|
| **Padre Hotel** (8-story L-tower) | `(-30.83..81.08, -786.17..-665.75, -0.08..122.33)` | `111.9 × 120.4 × 122.4` | `112.3 × 120.4 × 121.8` | `(+0.42, 0.0, -0.58, 0.0, 0.0, 0.0)` | **EXACT:** OSM `59480517` core `X=-28.4..75.5 (103.9 ft)`, `Y=-780.5..-668.8 (111.7 ft)`, 8 stories (+canopies/cornices). |
| **Fox Theater** (full footprint) | `(-50.00..86.17, -100.67..88.50, -3.50..116.50)` | `136.2 × 189.2 × 120.0` | `131.1 × 185.1 × 116.5` | `(-1.0, -4.09, -3.5, +4.09, 0.0, 0.0)` | **EXACT:** OSM `59516616` core `X=-47.5..47.5 (95 ft)`, `Y=-87.3..87.3 (174.5 ft)`; SE tower top `116.5 ft`; `bako_fox_piece` marquee/walls exact (`X=-48.0..82.0, Y=-96.5..86.6`). Extra `±4.09 ft` in query box is the 20th St jump pad pedestal & pit seal. |
| **Fox Clock Tower** (`tower_upper` + `tower_lower` + `clock`) | `tower_upper`: `(48.4..72.6, -86.1..-61.9, 67.9..116.4)`<br>`tower_lower`: `(35.0..74.8, -85.8..-50.6, 21.2..74.5)` | Tower peak `116.4 ft` | Tower peak `116.5 ft` | `0.0 ft` height delta | **EXACT:** Matches `fox-theater/008.jpg` SE corner placement, blue dome, 4-face belfry clock (`75.6..87.1 ft`). |
| **Fox Marquee** (`bako_fox_piece:marquee`) | `(26.6..82.0, -96.5..-11.1, 8.5..27.1)` | `55.4 × 85.4 × 18.6` | `(26.5..82.08, -96.5..-2.4)` | Exact wrap-around corner marquee | **EXACT:** Wraps 20th & H St corner identically to real Fox Theater. |
| **Parking Garage (18th & Eye)** | `(185.50..446.75, -781.58..-664.17, 0.50..72.00)` | `261.3 × 117.4 × 71.5` | `261.3 × 117.4 × 71.5` | **`(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)`** | **EXACT:** All **6 levels** verified via BSP horizontal deck planes: L1 `0.5`, L2 `11.2`, L3 `21.9`, L4 `32.6`, L5 `43.3`, L6 Roof `54.0 ft` (parapets `58.2 ft`, stairwells `72.0 ft`). Matches `padre-garage/006.jpg`. |
| **Nile Theater** | `(-209.67..9.50, -629.83..-490.67, 0.50..58.17)` | `219.2 × 139.2 × 57.7` | `220.1 × 138.8 × 58.2` | `(-0.59, -0.33, +0.5, -1.5, 0.0, 0.0)` | **EXACT** preservation north of Padre across Wall St. |
| **Dagny's Coffee (James Bldg)** | `(287.42..424.17, -93.67..-26.75, 0.50..31.83)` | `136.8 × 66.9 × 31.3` | `136.8 × 66.9 × 31.5` | **`(0.0, 0.0, 0.0, 0.0, 0.0, -0.17)`** | **EXACT** preservation south of Larry's Warehouse (`17.4 ft` open plaza separates them). |
| **Sandrini's Bar** | `(479.83..651.00, -290.58..-165.17, -8.18..46.83)` | `171.2 × 125.4 × 55.0` | `168.2 × 122.4 × 55.0` | `(0, 0, 0, +3.0, +3.0, 0)` | **EXACT** preservation (basement intact to `-8.18 ft`; +3 ft is corner rubble prop). |
| **Jerry's Pizza / Guthrie's Alley** | `(502.67..794.17, -787.08..-491.67, 0.50..57.00)` | `291.5 × 295.4 × 56.5` | `291.0 × 296.7 × 57.9` | `(0, 0, 0, +0.5, -1.25, -1.42)` | **EXACT** preservation along Chester Ave & Wall St. |
| **Old Post Office / Clover** | `(-209.33..-47.75, -788.92..-670.25, 0.50..34.92)` | `161.6 × 118.7 × 34.4` | `161.3 × 118.7 × 34.4` | `(-0.25, 0, 0, 0, 0, 0)` | **EXACT** static preservation immediately west of Padre (verified intact in `padre_r4_sheet.png`). |
| **PG&E Bldg + 136-ft Radio Tower** | `(132.83..274.00, -297.67..-170.50, 0.50..136.00)` | `141.2 × 127.2 × 135.5` | `141.2 × 126.3 × 135.5` | `(0, 0, 0, 0, +0.83, 0)` | **EXACT** preservation immediately west of Great Castle (`28.0 ft` clear). |

*(Note: Mint Bar is at real-world D-coords `X=1758.5, Y=-558.0` east of K St, outside the `REGION = (-340..950, -900..275)` bounds of BOTH `bakersfielddowntown.bsp` and `bakersfieldish.bsp`.)*

### 1.3 Sacred Spatial Relationships & Street Widths

| Relationship / Corridor | `bakersfieldish.bsp` | `bakersfielddowntown.bsp` | Verification |
|---|---|---|---|
| **Padre North Wall -> Fox South Wall (N–S along H St)** | `-665.75` -> `-96.58` = **`569.17 ft`** (core walls; `565.08 ft` incl. jump pad) | `-665.75` -> `-96.58` = **`569.17 ft`** | **EXACT** |
| **Padre Center -> Fox Center Vector** | `(-7.0, +719.9) ft`, dist **`719.9 ft`** | `(-8.4, +721.9) ft`, dist **`722.0 ft`** | **EXACT** (aligned on H St west curb) |
| **Padre Center -> Fox Clock Tower Center** | dist **`653.6 ft`** | dist **`654.6 ft`** | **EXACT** |
| **Padre <-> Fox H Street Sightline** | Unobstructed straight down H St; Bakersfield Sign arches overhead at `Y = -565` (`17.5..23.1 ft` road clearance), framing Fox Clock Tower cleanly | Unobstructed | **PASS** (visually confirmed in `sign_r3_sheet.png` panel 01 & `padre_r4_sheet.png` panel 01) |
| **Padre East Wall <-> Parking Garage West Wall (across H St, `Z=16..50 ft`)** | `77.42` -> `193.83` = **`116.42 ft`** | `77.42` -> `193.83` = **`116.42 ft`** | **EXACT (`0.00 ft` delta)** |
| **Padre East Wall <-> 1812 H St Corner Shop (`Z=2..15 ft`)** | `81.08` -> `149.33` = **`68.25 ft`** | `81.08` -> `149.33` = **`68.25 ft`** | **EXACT (`0.00 ft` delta)** |
| **H St at Fox <-> Larry's Warehouse** | `85.33` -> `146.67` = **`61.33 ft`** | `82.08` -> `146.67` = **`64.58 ft`** | **PASS** (full 52-ft roadway + sidewalks intact) |
| **20th St at Fox** | `-160.08` -> `-96.58` = **`63.50 ft`** | `-160.08` -> `-96.58` = **`63.50 ft`** | **EXACT** |
| **20th St at Great Castle <-> Dagny's** | `-192.50` -> `-93.67` = **`98.83 ft`** (wider due to Great Castle north entry plaza) | `-171.92` -> `-93.67` = **`78.25 ft`** | **PASS** |
| **20th St at Sandrini's <-> Golden West** | `-162.08` -> `-112.67` = **`49.42 ft`** | `-163.58` -> `-114.42` = **`49.17 ft`** | **EXACT** |
| **Eye St at Larry's/Dagny's <-> Golden West** | Roadway + curbs intact (`X=424..495` = `71 ft` building-to-building; traffic signal arm at `440.7` & leaning pole at `489.8` give `49.1 ft` prop clearance) | `424.17` -> `501.00` = `76.83 ft` | **PASS** |

---

## Section 2: All Four Merged Landmarks & Asset Integrity

### 2.1 Landmark Dimensions, Scale Fidelity & Placement Cleanliness

| Merged Landmark | Slot (D-feet) | Original Source Dimensions | Compiled `bakersfieldish.bsp` Footprint & Height | Scale Fidelity | Integration & Clearance Verification |
|---|---|---|---|---|---|
| **1. Golden West Casino** (`gw_casino`) | **GW-A** (`Eye–Chester / 20th–21st`, `495..776 × -95..175`) | `gw_casino_int`: `156.3 × 161.4 ft` (Bldg `59517066`) | Bldg `542.8..709.9 × -29.5..128.5` (`167.1 × 158.0 ft`, `Z=0.5..32.3 ft`), rot `270°` + 28.5-ft purple pylon at `D(742,-68)` | **1:1 exact** | Replaces generic AT&T / surface lot; 12-sided Rotunda faces 20th St, Horse Courtyard opens toward 20th & Chester, 10,613 faces, zero overlap with streets or neighbors. |
| **2. The Great Castle** (`great_castle`) | **GC-A** (`H–Eye / Service–20th` E lot, `276..428 × -290..-170`) | `gw_gc_int`: `77.5 × 71.5 ft` core (`80 × 80 ft` w/ canopy/garden) | Bldg `302.0..382.0 × -272.5..-192.5` (`80.0 × 80.0 ft`, `Z=0.25..31.5 ft`), rot `180°` + Merlon Pylon at `D(416,-212)` | **1:1 exact** | Replaces east surface lot; stays **`28.0 ft` clear** east of PG&E radio tower (`X <= 274`); watchtower fronts 20th St across from Dagny's; 40-ft channel sign fronts Eye St across from Sandrini's; 4,371 faces. |
| **3. Larry's Warehouse** (`larrys_warehouse`) | **LW-A** (`H–Eye / 20th–21st` N/W, `152..424 × -18..178`) | `maps/bklan6.bsp`: 26 `misc_lan_table` spanning `173.8 × 154.7 ft` | Full complex `175.5..384.5 × -9.4..172.5` (`209.0 × 181.9 ft`, `Z=0.08..32.0 ft`); **all 26 `misc_lan_table` preserved at exact `173.8 × 154.7 ft` span**, 36 chairs, 36 monitors, 33 PCs, 3 `bk_tv`, `mm_rig.md3`, Daniel posters | **1:1 exact** | Replaces north surface lots/generic buildings while **preserving Dagny's Coffee intact** (`17.4 ft` open south plaza clear between `Y=-26.8` and `Y=-9.4`); north courtyard opens onto 21st St; 5,537 faces. |
| **4. The Bakersfield Sign** (`bakersfield_sign`) | **S1** (`H St Hero Spine`, center `D(110.0, -565.0)`) | Real sign: `97 ft` tower spacing; `bklan6.bsp`: `111.0 × 14.0 × 31.0 ft` | `bako_sign_piece`: `X=59.1..160.9` (**`101.8 ft` eaves, `88.0 ft` spacing = 90.7% real**), `Y=-571.9..-558.1 (13.8 ft)`, `Z=0..30.9 ft` (`17.5..23.1 ft` road clearance) | **90.7% span, 100% height** | Spans H St cleanly: West eaves **`47.85 ft` clear** of Nile/west buildings; East eaves **`1.27 ft` clear** of East H St facade (`X=162.17`); clear >90-ft northward topple runway down H St. |

### 2.2 Complete Virtual Filesystem Asset Integrity Audit (Zero Missing Assets!)

Verified across `maps/bakersfieldish.bsp`, `zz_bakersfieldish.pk3`, `bakersfield.pk3`, all `zz_*.pk3`, `../quake15/*.pk3`, and loose directories:
- **BSP Textures (`miptex` lump):** 1,036 total (4 embedded, 1,032 pixel-stripped external). **Missing external textures: `0`**.
- **Skybox (`dtsky145_`):** All 6 faces (`ft, bk, lf, rt, up, dn`) present (`1/1` each).
- **BSP Entity Models (`misc_model`, etc.):** 58 distinct model paths across 269 instances. **Missing entity models: `0`**.
- **QC Precached/Used Models (`bako_destruct.qc` + `skypad.qc`):** 18 distinct models. **Missing: `0`**.
- **QC Precached/Used Sounds (`bako_destruct.qc` + `skypad.qc`):** 29 distinct WAVs. **Missing: `0`**.
- **QC Particle Effects (`particleeffectnum`):** 12 distinct effects (`bako_demolition_dust_surge`, `bako_collapse_plume`, `bako_window_smoke`, `bako_masonry_burst`, `bako_charge_pop`, `bako_sign_sparks`, `bako_rebuild_weld`, `bako_rock_dust`, `glass_break`, `bako_glass_sparkle`, `rocket_burn`, `TE_TELEPORT`). **Missing from `effectinfo.txt`: `0`** (449 total effects indexed).
- **`zz_bakersfieldish.pk3` MD3 Internal Skins:** All 7 MD3s (`bako_boulder1..4.md3`, `bako_glass_shard1..3.md3`) parsed — all 8 skin shader paths (`progs/bako_boulder1..4`, `progs/bako_rebar`, `progs/bako_glass_shard`) resolve cleanly to PNGs inside `zz_bakersfieldish.pk3` (**`0` missing**).
- **`progs.dat` & `csprogs.dat` Parity:** `progs.dat` (modified 2026-11-25 2:52:05 PM, 3s after `bako_destruct.qc`) contains all current `bako_*` symbols (`bako_fox_clock`, `bako_padre_piece`, `bako_sign_piece`, `Bako_TickSmoothShake`, `Bako_VeilFoxTowerUpper`, `Bako_EmitPadreCenterVeil`, `Bako_EmitSignFullWidthDust`, `BakoDestruct_OnGlassBreak`); `csprogs.dat` contains the top-right HUD strings.

---

## Section 3: Look & Feel + High Skybox

- **High Skybox:** Compiled sky faces reach **`Z = 7,200.0 u` (`600.0 ft`)** vs `3,360.0 u` (`280.0 ft`) in `bakersfielddowntown.bsp` — a **+3,840 u (+114%) increase**, providing `3,300–4,300 u` of headroom above every `info_skypad` apex (`2,900–3,900 u`) and generous room for jetpacks, Winged John, and Rocket Rider. Horizontal `hint` cap at `z = 140 ft` + `keep_sky_pvs` (281 pure sky leafs, 3,035/3,923 vis clusters patched) keeps sky VIS clean.
- **Light-Handed Post-Apocalyptic Atmosphere:**
  - Worldspawn lighting shifted cleanly from crisp blue-white downtown to warm golden-dust afternoon (`_sunlight 235`, `_sunlight_color "1 0.88 0.72"`, `_minlight 98`, `_minlight_color "242 232 216"`, warm horizon haze `fog "0.22 0.56 0.49 0.41 1 4200 7600 2200 750"` keeping overhead sky crisp blue).
  - Post-apoc dressing totals **~59 light props** (19 Jersey barriers along curb flanks leaving center lanes wide open, 14 corner rubble clusters, 6 leaning poles, 4 dumpsters, 3 stunt ramps, 3 rooftop scaffolding sky-bridges, plus 10 small landmark-apron rubbles/barriers) across 151,142 faces. Visually confirmed in `fox_r5_sheet.png`, `padre_r4_sheet.png`, and `sign_r3_sheet.png`: unmistakably downtown Bakersfield with light-handed apocalyptic dressing, NOT a brown wasteland.

---

## Section 4: Destructibles Audit (Fox, Padre, Bakersfield Sign, Shatterable Glass)

### 4.1 Compiled Destructible Bmodels & Runtime Contract

| Landmark | Compiled BSP Entities | HP / Toughness | Collapse Physics & FX (QC + Captures Verified) | Rubble Climbability & Dwell | Rebuild |
|---|---|---|---|---|---|
| **Fox Theater** | `bako_fox_clock` (1, 56 faces), `bako_fox_piece` (7: `tower_upper`, `tower_lower`, `marquee`, `facade_e`, `facade_s`, `auditorium_roof`, `stagehouse`; 12,268 faces), `bako_fox_rubble` (1, 2,030 faces, `Z=-1.3..28.4 ft`) | **200 HP** (clock-only trigger; other pieces `DAMAGE_NO`) | Coupled 2-piece clock tower topple (`u^2.4` gravity curve, ~8.6s total), outward marquee & masonry bursts, radial dust ring, damped 60 Hz shake (`pitch<=3°`, `roll<=2°`, slew `<=0.42°/frame`). Visually verified in `fox_r5_sheet.png` & `05_tower_slam.png` — cinema-grade, zero hollow boxes. | **150s (2.5 min)** default (`bako_fox_rubble_t`). 2D Hull-1 BFS climb test: **walk-only (`<=18u` step) reaches `28.3/28.3 ft` peak** (`1,666/1,813` cells)! | **25s** bottom-up upright rebuild with 3 comedic NPC workers, welding sparks, bell chime (`fox_r5_sheet.png` panels 11–16). |
| **Padre Hotel** | `bako_padre_piece` (7: `tier1..4`, `west_wing`, `east_wing`, `crown`; 17,233 faces), `bako_padre_rubble` (1, 2,634 faces, `Z=-1.1..31.3 ft`) | **2,600 HP** (**13× tougher than Fox!** Unified pool across all 7 pieces; responds to rockets, Eric Cannon `1.75×` nuke splash, hitscan, projectiles via `combat.qc` + `eric_cannon.qc`) | 75/50/25% outer-facade dark window smoke + corner HUD; 10 perimeter 1F–3F charge pops (`0.05..2.05s`); ~12s inward V-collapse with crown welded to `tier4`; huge warm-tan dust cloud; **3 waves × 8 = 24 tumbling concrete boulders** bouncing players (`kick_h 380..640`, `kick_z 340..400`, `15 dmg`) & vehicles (`kick_h 240..420`); landing earthquake. Verified in `padre_r4_sheet.png` & `07_mid_pancake.png`. | **120s (2.0 min)** default (`bako_padre_rubble_t`). 2D Hull-1 BFS climb test: walk-only reaches `7.5 ft`; **walk+jump (`<=42u`) reaches `31.3/31.3 ft` peak** (`1,087/1,088` cells)! | **28s** optional auto-rebuild (`bako_auto_rebuild = 1`). |
| **Bakersfield Sign** | `bako_sign_piece` (1, 727 faces, `org=(110,-565,5)`), `bako_sign_rubble` (1, 826 faces + 12 invisible clip ramp wedges, `Z=-4.1..9.8 ft`) | **380 HP** (responds to all weapons & splash) | Pier-anchored Plane-A blasts, `u^2.4` north topple (`-88°` roll, 4.2s) + 0.52s damped elastic street rebound (`-88 -> -80 -> -88 -> -85.5 -> -88°`), full-width 80-ft dust surge, neon sparks, glass shards, earthquake. Verified in `sign_r3_sheet.png` & `07_street_impact.png`. | **120s (2.0 min)** default. Center arch (`X=110`) is smooth `0.6 -> 4.2 ft` (`max step 6u`), **BUT see Defect #6** (Hull-1 bevel spikes to `10.5–10.8 ft` at `X=85..95` & `125..135`). | **10s** crane hoist upright. |
| **Shatterable Glass** | **52 `func_breakable` bays** (`style=3`, `health=15`, `alpha=0.52`, `wait=120`, 0 kv anomalies) | **15 HP** (also breaks on go-kart ram & sprint >220 u/s) | 20 translucent faceted crystalline shard MD3s (`alpha=0.56`, ~1.5s fade) + cool silver-cyan sparkle + sound. Verified in `glass_r3_sheet.png` (clean frames & walkable interior opening!). | Distributed across **7 building clusters**: Dagny's (18), Golden West (12), Padre 1F (10), Nile (5), 1812 H St (4), Great Castle (2), Front Porch Music (1). *(0 in Larry's Warehouse — `bk_glass` has 0 faces in BSP.)* | **120s** per-pane respawn (**causes Defect #5 on Padre 1F**). |

### 4.2 Glass Hollow-Opening BSP Verification
All 52 `func_breakable` bays were tested directly against compiled BSP Hull-0 clipnodes (excluding `func_breakable`) along each pane's true face normal at `center`, `±16 u`, and `±28 u`:
- **47 / 52 panes** are 100% hollow open space (`CONTENTS_EMPTY` at center and `±16 u` / `±28 u` on both sides).
- **5 / 52 panes** (all diagonal/rotunda panes in Golden West Casino: `*40, *41, *44, *46, *47`) are open on both `±16 u` / `±28 u` sides (`CONTENTS_EMPTY`), with `3 / 27` grid points solid right on the plane due to a thin center mullion bar inside the window frame — they still shatter into visible hollow openings, though a player cannot walk cleanly through the narrow mullioned opening.
- **All 10 Padre 1F glass bays** (`110–187 u wide × 79 u tall`, sill `3.4 ft`, lintel `10.0 ft`) are 100% hollow in Hull-0 and passable by a standing player Hull-1 at `Z = 5.38–5.71 ft` (verified both mathematically and visually in `glass_r3_sheet.png` panels 05–08).

---

## Section 5: Traversal Completeness Audit (Compiled BSP Entities + Hull-1 Physics)

### 5.1 Spawns & Go-Kart Near Every Spawn (`36` Spawns, `36` Go-Karts)
- **Raw distance metric:** Every single one of the **36 spawns** (1 `info_player_start` + 35 `info_player_deathmatch`) has a paired `misc_gokart_1..6` within **`131.8–138.5 u` (`11.0–11.5 ft`)** 3D distance (`dZ = 9–10 u` for 35/36 spawns; `42 u` for Spawn `#29` Great Castle Roof).
- **HOWEVER, Hull-1 BSP solidity & placement verification exposes 3 severe spawn/kart failures:**
  1. **Spawn `#20` (`Golden West Roof`, `D(622.0, 62.0, 18.2)`) and Kart `#20` (`misc_gokart_2`, `D(614.2, 54.2, 17.5)`) are 100% embedded inside solid `worldspawn`** (Golden West Casino's pitched gable roof monitor spans solid `Z = 15.5..30.5 ft` in Hull-0, `10.0..33.0 ft` in Hull-1).
  2. **3 rooftop spawns sit `0.0 u` XY directly inside `info_skypad` trigger boxes (`±40 u`):** Spawn `#20` (`GW Roof` vs SkyPad `#04`), Spawn `#25` (`Larry's Warehouse Roof` `D(220, 82, 19.2)` vs SkyPad `#03`), and Spawn `#29` (`Great Castle Roof` `D(352, -242, 18.0)` vs SkyPad `#05`). Spawning at `#25` or `#29` triggers the SkyPad on frame 1 before the player can reach their paired go-kart!
  3. **3 ground-floor spawns & karts inside Padre and Fox get buried in solid rubble during collapse:** Spawn `#03` (`Padre 1F Lobby`, `Z=33 u`), Spawn `#12` (`Fox Grand Lobby`, `Z=33 u`), and Spawn `#13` (`Fox Stage`, `Z=73 u`) are all below `Bako_HideRoofProps`'s `min_z` cutoffs (`185 u` Padre / `320 u` Fox) and `BM_PickSpawn()` does not filter solid rubble — players spawning there during the 120–150s collapsed phase spawn stuck inside `bako_padre_rubble` / `bako_fox_rubble`.

### 5.2 Chained Super Jump Pads (`10` `info_skypad` Entities)

| # | Route | Origin (D-ft) | `pos1` (D-ft) | Apex (u) | Sky Margin (u) | Launch `H1` (`org+4u`) | Landing `H1` (`pos1+4u`) | Arc Collision Check (200 steps) | Chain to Next SkyPad |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Padre Roof -> Fox Roof | `(0.0, -750.0, 104.7)` | `(-14.0, 6.0, 53.2)` | 3400 | 3800 | CLEAR | CLEAR | **CLEAR** | `0.0 u` -> `#02` *(broken after Fox/Padre rebuild — Defect #4)* |
| 2 | Fox Roof -> Larry's Roof | `(-14.0, 6.0, 53.2)` | `(220.0, 82.0, 19.2)` | 3000 | 4200 | CLEAR | CLEAR | **CLEAR** | `0.0 u` -> `#03` |
| 3 | Larry's Roof -> **GW Roof** | `(220.0, 82.0, 19.2)` | `(622.0, 62.0, 18.2)` | 3100 | 4100 | CLEAR | **SOLID (`worldspawn`)** | **HIT at `t=0.985` `D(616.0,62.3,32.3)`** | **BROKEN — lands on 30.8-ft gable roof 12+ ft above buried `#04`!** |
| 4 | **GW Roof** -> Great Castle Roof | `(622.0, 62.0, 18.2)` | `(352.0, -242.0, 17.9)` | 3200 | 4000 | **SOLID (`worldspawn`)** | CLEAR | **HIT at `t=0.010` `D(619.3,59.0,28.3)`** | **UNREACHABLE — buried inside solid gable roof (`Z=15.5..30.5 ft`)!** |
| 5 | Great Castle Roof -> Garage L6 | `(352.0, -242.0, 17.9)` | `(230.0, -715.0, 56.2)` | 3100 | 4100 | CLEAR | CLEAR | **CLEAR** | `0.0 u` -> `#06` |
| 6 | Garage L6 -> Padre Roof | `(230.0, -715.0, 56.2)` | `(0.0, -750.0, 104.7)` | 3300 | 3900 | CLEAR | CLEAR | **CLEAR** | `0.0 u` -> `#01` |
| 7 | H St Sign Plaza -> Fox Roof | `(142.0, -525.0, 2.7)` | `(-14.0, 6.0, 53.2)` | 2900 | 4300 | CLEAR | CLEAR | **CLEAR** | `0.0 u` -> `#02` |
| 8 | SW 18th & G -> Larry's Roof | `(-265.0, -782.0, 2.7)` | `(220.0, 82.0, 19.2)` | 3900 | 3300 | CLEAR | CLEAR | **CLEAR** | `0.0 u` -> `#03` |
| 9 | SE 18th & Chester -> **GW Roof** | `(868.0, -782.0, 2.7)` | `(622.0, 62.0, 18.2)` | 3700 | 3500 | CLEAR | **SOLID (`worldspawn`)** | **HIT at `t=0.990` `D(624.5,53.6,29.8)`** | **BROKEN — lands on gable roof above buried `#04`!** |
| 10 | GW Courtyard -> Garage L6 | `(752.0, -96.0, 2.7)` | `(230.0, -715.0, 56.2)` | 3600 | 3600 | CLEAR | CLEAR | **CLEAR** | `0.0 u` -> `#06` |

*(Note: Golden West Casino's genuine flat roof deck is at `Y = 90..122, X = 562..690, Z = 16.2 ft`, directly north of the `Y = 42..74, Z = 26.2..30.8 ft` gable monitor. Moving `gw_roof` to e.g. `D(622, 108, 16.5)` fixes `#03`, `#04`, `#09`, Spawn `#20`, Kart `#20`, and Lightning Gun simultaneously!)*

### 5.3 Regular Jump Pads (`12` `trigger_push` Entities) — 9-Point Trigger Sweep Against Compiled BSP Hull-1

| # | Jump Pad | Trigger Location (D-ft) | `angles` / `speed` | Clear Launches (of 9) | Failure Mode (Exact Impact Point) |
|---|---|---|---|---|---|
| 1 | **Fox West Alley -> Fox Roof** | `(-58.5, 22.0, 0.2..4.4)` | `-78.9 325.9 0` / `115.6` | **0 / 9 (FAIL)** | **9/9 `START_SOLID`**: buried underneath the `5.4 ft`-high Fox West Alley concrete ramp (`_ramp_x(-67.5..-50, 12..28)`). Completely unreachable! |
| 2 | **Wall St -> Padre Roof** | `(46.0, -654.0, 0.2..4.4)` | `-75.2 247.3 0` / `159.9` | **0 / 9 (FAIL)** | **9/9 `WALL_HIT`**: impacts `bako_padre_piece:east_wing` north facade at `D(40.0, -668.4, 54.7)` (48 ft below roof). |
| 3 | **18th St -> Padre 2F Terrace** | `(-12.0, -790.0, 0.8..4.9)` | `-51.4 86.0 0` / `101.2` | **0 / 9 (FAIL)** | **9/9 `WALL_HIT`**: impacts `bako_padre_piece:tier1` south wall/canopy at `D(-11.6, -784.8, 9.3)`. |
| 4 | **18th St -> Garage L6 Roof** | `(292.0, -788.0, 0.8..4.9)` | `-81.2 90.0 0` / `116.9` | **0 / 9 (FAIL)** | **9/9 `WALL_HIT`**: impacts Parking Garage south facade at `D(292.0, -779.4, 47.6)` (below 58.2-ft parapet). |
| 5 | **Eye St -> Garage L6 Roof** | `(430.0, -736.0, 0.8..4.9)` | `-72.2 190.5 0` / `121.3` | **0 / 9 (FAIL)** | **9/9 `WALL_HIT`**: impacts Parking Garage east facade at `D(418.5, -738.1, 34.8)`. |
| 6 | Garage L6 -> Padre Roof Kart Boost | `(215.0, -730.0, 54.2..58.4)` | `-46.9 185.0 0` / `159.4` | **9 / 9 (PASS)** | Clean landing on `bako_padre_piece:crown` at `D(8.9, -748.0, 104.4)`. |
| 7 | **20th St -> Fox Marquee Deck** | `(58.0, -104.0, 0.8..4.9)` | `-68.3 80.6 0` / `86.3` | **0 / 9 (FAIL)** | **9/9 `WALL_HIT`**: impacts `bako_fox_piece:marquee` front/underside at `D(59.0, -97.7, 17.1)`. |
| 8 | Eye St -> Great Castle Roof | `(432.0, -230.0, 0.8..4.9)` | `-48.5 188.5 0` / `95.2` | **9 / 9 (PASS)** | Clean landing on Great Castle roof at `D(355.1, -241.5, 17.9)`. |
| 9 | 20th St -> Golden West Roof | `(580.0, -104.0, 0.8..4.9)` | `-32.2 75.8 0` / `145.9` | **6 / 9 (PARTIAL)** | Center lands on GW gable roof at `D(616.8, 41.6, 26.5)`; 3/9 edge hits wall. |
| 10 | H St -> Larry's Warehouse Roof | `(146.0, 82.0, 0.8..4.9)` | `-56.2 0.0 0` / `95.0` | **9 / 9 (PASS)** | Clean landing on Larry's B76 roof at `D(220.9, 82.0, 18.5)`. |
| 11 | **Dagny's Lot -> Dagny's Roof** | `(356.0, -18.0, 0.3..4.5)` | `-72.9 270.0 0` / `91.6` | **3 / 9 (FAIL)** | **6/9 `WALL_HIT`**: center/north launches clip Dagny's north parapet at `D(356.0, -28.3, 29.1)` (parapet `31.8 ft`). |
| 12 | Wall St Alley -> Tattoo Tower Roof | `(544.0, -654.0, 0.8..4.9)` | `-77.7 100.3 0` / `118.2` | **6 / 9 (PARTIAL)** | Center lands cleanly on Tattoo Tower roof at `D(535.9, -609.4, 55.4)`. |

### 5.4 Jetpacks (`13` `item_jetpack` Entities) & Creative Touches
- **13 / 13 jetpacks pass** exact Quake item-hull (`(-16,-16,0)..(16,16,56)`) clearance checks (`0` embedded!). Sensibly placed on far perimeter corners (NW 21st & G, SW 18th & G, SE 18th & Chester, H St Sign Plaza) and high landmark rooftops (Garage L6, Padre 2F & 8F, Fox Roof, GW Roof & Courtyard, Larry's B76 & B45 roofs, Great Castle Watchtower).
- **Creative touches present:** 3 concrete stunt ramps (18th->Garage SW, Wall->Garage L2, Fox West Alley), 3 rooftop scaffolding sky-bridges (Nile->Tevis across 19th St, Dagny's->Larry's B45 roof with ramp, Garage L6->Wall St overlook), 3 Eric Cannons, and 5 aerial/ground vehicles (`2× johnbird`, `rocketrider`, `van`, `gtcar`).

---

## Exact Numbered Defect List

### Critical Blockers (Must Fix)

1. **[CRITICAL] Root-Cause Sign Bug in `source/downtown/tools/dt_hull.py:160` Blinds Placement to ALL Non-Axial / Sloped Brushes**
   - `dt_hull._planes()` computes **outward** normals `(p0-p1) × (p2-p1)` for Quake-wound faces, where interior points satisfy `n · x < d`. However, `World.which()` line 160 tests `np.all(n · o + sup > d + eps)`, which is inverted and mathematically impossible for any closed convex solid. Axis-aligned boxes bypassed this via `pl is None`, so **every sloped/diagonal brush in the map** (Golden West gable roof, Fox West Alley ramp, Garage L1->L2 ramp) returned `overlap() == False`.
   - *Fix:* Change line 160 to test minimum support `inf_sup = np.where(n > 0, n*mn, n*mx)` with `np.all(n · o + inf_sup < d - eps)` (verify unit test against a sloped wedge and Golden West roof!).

2. **[CRITICAL] Golden West Casino Roof Hub Buried 12+ ft Inside Solid `worldspawn` — Breaks Chained SkyPad Loop, Spawn `#20`, Kart `#20`, and `weapon_lightning`**
   - `merged_landmarks.py:646` sets `roof_main = (622.0, 62.0, 17.5)`, which lies directly inside Golden West Casino's solid pitched gable roof monitor (`Y = 42..74, Z = 15.5..30.5 ft` Hull-0 solid; `10.0..33.0 ft` Hull-1 solid).
   - Because of Defect `#1`, compiled `maps/bakersfieldish.bsp` embeds **4 critical entities inside solid `worldspawn`**:
     - `info_skypad` `#04` (`Golden West Casino Roof -> Great Castle Roof` at `D(622.0, 62.0, 18.2)`) — **unreachable**, and incoming `SkyPad #03` & `#09` impact the outer roof at `Z = 29.8–32.3 ft`, severing the 6-landmark continuous chain.
     - `info_player_deathmatch` `#20` (`Golden West Roof` at `D(622.0, 62.0, 18.2)`) — players spawn trapped in solid.
     - `misc_gokart_2` `#20` (`D(614.2, 54.2, 17.5)`) — buried inside solid roof.
     - `weapon_lightning` (`D(602.0, 62.0, 18.2)`) — buried inside solid roof.
   - *Fix:* Move `golden_west.roof_main` onto the verified flat north roof deck (`Y = 96..118, X = 566..680, Z = 16.2 ft`, e.g., `D(622.0, 108.0, 16.2)`) and offset the roof spawn & weapon away from the SkyPad trigger.

3. **[CRITICAL] 6 of 12 Regular Jump Pads (`trigger_push`) 100% Non-Functional (`0/9`), Plus 1 Mostly Failing (`3/9`)**
   - `JumpPad #01` (`Fox West Alley -> Fox Roof`, `D(-58.5, 22.0)`) is completely buried beneath the solid Fox West Alley concrete ramp (`Z = 5.4 ft` over the `0.2..4.4 ft` trigger box).
   - `JumpPad #02` (`Wall St -> Padre Roof`), `#03` (`18th St -> Padre 2F`), `#04` (`18th St -> Garage L6`), `#05` (`Eye St -> Garage L6`), and `#07` (`20th St -> Fox Marquee`) crash **9/9** directly into vertical exterior walls/marquee during ascent because `_solve_push_vel` never verifies trajectory clearance over building walls/parapets.
   - `JumpPad #11` (`Dagny's Lot -> Dagny's Roof`) clips Dagny's north parapet on **6/9** launch positions.
   - *Fix:* Relocate `#01` clear of the Fox West Alley ramp (e.g., `Y = 38.0` or `Y = 2.0`), pull street-side wall pads back ~8–16 ft from vertical facades and/or raise `apex_extra_ft` (e.g. `32–48 ft` for tall roofs), and validate every `trigger_push` parabola against fixed `dt_hull` during map build!

### High-Severity Defects

4. **[HIGH] `Bako_RestoreRoofProps` in `source/qc_combat_decomp/bako_destruct.qc:662–702` Wipes `info_skypad` Trigger Size on Fox/Padre Rebuild**
   - `Bako_HideOneRoofEnt` calls `setmodel(e, "")` on rooftop `info_skypad` entities (which are `SOLID_TRIGGER` point entities with `model == ""` and explicit `setsize(self, '-40 -40 -26', '40 40 36')`). In DarkPlaces/Zircon, `setmodel(e, "")` resets `e.mins` and `e.maxs` to `'0 0 0'`. `Bako_RestoreRoofProps` never saves/restores `mins`/`maxs` via `setsize()`, leaving Padre Roof (`#01`) and Fox Roof (`#02`) SkyPads with zero-volume broken triggers after rebuild (and shrinking restored rooftop item pickup boxes).
   - *Fix:* Store `.vector bako_roof_mins, bako_roof_maxs;` in `Bako_HideOneRoofEnt` BEFORE `setmodel(e, "")`, and call `setsize(e, e.bako_roof_mins, e.bako_roof_maxs);` AFTER `setmodel`/`setorigin` in `Bako_RestoreRoofProps`.

5. **[HIGH] 3 Ground-Floor Spawns (`#03 Padre 1F`, `#12 Fox Lobby`, `#13 Fox Stage`) & Paired Karts Get Trapped Inside Solid Rubble During Collapse**
   - `Bako_HideRoofProps` uses `min_z = 185 u` (Padre) and `min_z = 320 u` (Fox), so ground-floor `info_player_deathmatch` spots (`#03` at `z=33 u`, `#12` at `z=33 u`, `#13` at `z=73 u`) are NOT relocated when `bako_padre_rubble` (`z <= 375 u`) and `bako_fox_rubble` (`z <= 341 u`) solidify, and `BM_PickSpawn()` does not check solid contents. Players respawning there during the 120–150s rubble phase spawn stuck inside solid rubble!
   - *Fix:* Relocate ALL `info_player_deathmatch` entities inside the Padre/Fox XY footprints (regardless of `z`, i.e., `min_z = -64` for `info_player_deathmatch`) onto verified open rubble/street positions during collapse, and restore on rebuild.

6. **[HIGH] 3 Rooftop Spawns Placed Directly Inside `info_skypad` Trigger Volumes (`0.0 u` XY Separation)**
   - `Spawn #20` (`GW Roof`, `D(622, 62, 18.2)`), `Spawn #25` (`Larry's Warehouse Roof`, `D(220, 82, 19.2)`), and `Spawn #29` (`Great Castle Roof`, `D(352, -242, 18.0)`) share identical `(x, y)` coordinates (`dXY = 0.0 u`, `dZ = 1.0 u`) with `SkyPad #04`, `#03`, and `#05` (trigger radius `±40 u`). Players spawning at `#25` or `#29` are insta-launched across the map on frame 1 before they can use their paired go-kart.
   - *Fix:* Pass `resolved_loop` SkyPad XY points into `avoid_pts` (with `min_sep_ft >= 12.0 ft`) when placing spawns (or offset roof spawn candidates by 14–20 ft from the SkyPad coordinate).

### Medium-Severity Defects

7. **[MEDIUM] Padre 1F Shatterable Glass Panes Respawn Inside Solid Rubble (`t=120s` vs `160s` Full Cycle)**
   - Padre's 10 ground-floor `func_breakable` bays have `wait = 120`. They shatter at collapse start (`t=0`), while Padre takes ~12s to collapse + 120s rubble + 28s rebuild = 160s. At `t=120s` (12s before rubble clears and 40s before Padre rebuilds), `Bako_TickGlass` calls `Bako_RestoreGlassPane`, popping floating intact glass panes inside/through Padre's rubble mound.
   - *Fix:* In `Bako_TickGlass` / `Bako_RestoreGlassPane`, defer restoration (`g.bako_glass_respawn_t = time + 2.0`) whenever a pane lies inside Padre's footprint while `bako_padre_state != BAKO_ST_INTACT` (and restore cleanly inside `Bako_ResetPadreIntact`).

8. **[MEDIUM] Bakersfield Sign Fallen Rubble (`bako_sign_rubble`) Has Hull-1 Clipnode Bevel Spikes (`10.5–10.8 ft`) on Arch Flanks**
   - While the dead center of the fallen yellow arch (`X=110`) has a smooth Hull-1 ramp (`0.6 -> 4.2 ft`, max step `6 u`), the left and right flanks (`X=85..95` and `X=125..135`) exhibit Hull-1 solid spikes up to **`10.5–10.8 ft`** (`126–130 u`) despite Hull-0 geometry only reaching `4.0 ft` — creating invisible ~7 ft vertical walls blocking players and go-karts crossing the flanks of the fallen arch on H St.
   - *Fix:* Add axial top cap bevel planes (or simplify the fallen clip ramp to axis-aligned-in-X wedges capped strictly at `z_arch_top`, and compile `bako_sign_rubble`'s visual rotated arch segments with `func_detail`/non-acute clip or clean bounding clip envelope).

9. **[MEDIUM] 5 Additional Gameplay Entities Clip Solid World Geometry in Compiled BSP**
   - `item_health` (`D(310, -722, 2.7)`) and `item_shells` (`D(322, -722, 2.7)`) are embedded inside the Parking Garage L1->L2 sloped concrete vehicle ramp (`pg_deck`/`pg_conc`, missed due to Defect `#1`).
   - `misc_eric_cannon` (`D(140, -498, 1.0)` at H & 19th Plaza) clips a solid green street bollard (`ds_green` at `X=140.8..141.6, Y=-498.4..-497.6, Z=0.5..3.9`).
   - `item_health` (`D(820, -180, 2.9)`) clips a Chester Ave median hedge (`ds_hedge`) and `item_health` (`D(820, 120, 2.9)`) clips a Chester Ave tree trunk (`ds_bark` at `X=820.5..821.5, Y=119.7..120.2`).
   - *Fix:* Re-run placement after fixing Defect `#1`, and nudge the H & 19th cannon and 2 Chester Ave health boxes 4–6 ft off median/bollard centers.

### Minor / Polish Defects

10. **[MINOR] Larry's Warehouse Has 0 Shatterable Glass Bays Despite Intended Code in `merged_landmarks.py:979–1002`**
    - `emit_larrys_warehouse()` checks `if "bk_glass" in mb.texs` to convert up to 4 Unit 130A transom panes into `func_breakable`, but `maps/bakersfieldish.bsp` contains **`0` faces** with texture `bk_glass` (likely stripped/textured differently in `make_bklan.py`). Overall map still has 52 glass bays across 7 other buildings, so this is minor, but adding 2–4 real cut-out glass bays to Larry's Warehouse would complete landmark coverage.

11. **[MINOR] 5 Diagonal/Rotunda Golden West Glass Panes Have Thin Center Mullions (`3/27` Grid Points Solid)**
    - Panes `*40, *41, *44, *46, *47` in Golden West Casino are hollow on both sides (`±16 u` / `±28 u`), but each contains a narrow solid mullion/frame bar at its exact midpoint (`H0_mid == -2`), preventing full walk-through after shattering (shots and sightlines still pass cleanly around the mullion).

12. **[MINOR] Compile Log Geometry & Lighting Warnings**
    - `bakersfieldish-qbsp.log`: `70 EMPTY brushes`, `118 faces crunched away by being too small`, `5 sides not found`.
    - `bakersfieldish-light.log`: `6` lights could not be nudged out of solid (`(-8184,-5214,174)`, `(-6846,-5376,806)`, `(-7044,-5652,840)`, `(-5556,-5652,840)`, `(-7044,-4836,840)`, `(-5556,-4836,840)` — upper Parking Garage/Padre perimeter lights) and `305 empty lightmaps`.
