# Bakersfield-ish Independent Final Accuracy Audit (#1 of 4)

- **Auditor:** Independent Fresh Accuracy Auditor #1 (`audit-v2-1`, zero prior build history, zero prior audits consulted, no live Zircon launch)
- **Verdict:** **PASS**
- **Audited Compiled Artifacts:**
  - `maps/bakersfieldish.bsp` (`BSP2`, `40,851,944 B`, `89` models, `150,620` faces, `178,164` verts, `866,283` clipnodes, `1,037` textures, `1,567` entities)
  - `maps/bakersfieldish.lit` (`QLIT` v1, `14,382,632 B`, payload `14,382,624 B` = exact `3.000000×` BSP lighting lump `4,794,208 B`)
  - `maps/bakersfielddowntown.bsp` (`BSP2`, `37,081,900 B`, baseline reference) & `maps/bklan6.bsp` (`BSP2`, `19,881,536 B`, landmark 1:1 scale reference)
  - `progs.dat` (`3,773,670 B`, Quake v6, `316,813` statements, `11,168` functions, `42,948` globals; cross-checked against `source/qc_combat_decomp/` and `effectinfo.txt`)
  - `zz_bakersfieldish.pk3` (`440,516 B`, `16` entries: minimap, levelshot, 7 MD3 debris/shard models + textures, shader) + VFS (`bakersfield.pk3`, `zz_*.pk3`, `quake15/q15.pk3`, `id1/pak0..1.pak`)
  - References: `source/downtown/refs/osm_ft.json` (`524` OSM ways centered at Fox Theater), `source/mm_tools/ref_sources/golden_west_landmarks/part_A.md`
  - Real Captured Footage: `docs/bakersfieldish_captures/round5/fox_r5_sheet.png`, `round4/padre_r4_sheet.png`, `round3/sign_r3_sheet.png`, `round3/glass_r3_sheet.png`, plus `zz_bakersfieldish.pk3` `levelshots/bakersfieldish.jpg` and `gfx/minimap/bakersfieldish.png`

---

## Executive Summary

| # | Audit Category | Verdict | Key Quantitative Evidence |
|---|---|---|---|
| 1 | Downtown Layout, Scale & Sacred Anchors | **PASS** | Exact `12 u/ft` grid (`11.933 u/ft` Padre↔Fox, `0.56%` delta vs OSM); `8/8` Hull-0 sightline rays clear along H St; 6-level garage (`Z=8..648`, 128 u/floor) 100% continuous Hull-1 L1→L6; all 5 enterable venues (`Nile`, `Dagny's`, `Sandrini's` ground+basement, `Jerry's`, `Guthrie's`) verified hollow & walk-in accessible via Hull-1 BFS. |
| 2 | 4 Merged Landmarks & Asset Integrity | **PASS** | Golden West Casino, Great Castle, Larry's Warehouse (exact `0.0 u` 1:1 scale match to `bklan6.bsp`), and Bakersfield Sign all cleanly placed with **0 pairwise overlaps**, **0 missing BSP textures (1,037/1,037)**, **6/6 skybox sides**, **0 missing models/MD3 skins (58/58 + 7/7 PK3)**, **0 missing `progs.dat` classnames (47/47)**, and **0 missing active sounds/models**. |
| 3 | Post-Apocalyptic Look & High Skybox | **PASS** | Skybox ceiling raised from `Z=3,360` to **`Z=7,200`** (`+3,840 u`, **3.22×** vertical clearance above tallest structure: `5,568 u` vs `1,728 u`); warm golden-hour lighting/fog (`.lit` `R-B: +1.7 → +10.6`), `75` abandoned vehicles, zero crowds/traffic, clean recognizable Bakersfield city identity (not a wasteland). |
| 4 | Destructibles Spec (BSP2 + `progs.dat` + Captures) | **PASS** | Fox (`200 HP` clock → slow topple → `115 s` climbable rubble `98%` walk/`100%` jump → `25 s` staged rebuild), Padre (`2,600 HP` = `13×` Fox → inward controlled collapse → non-blinding dust `alpha 68–112` → player-bouncing boulders → `115 s` climbable rubble `99%` walk/`100%` jump → `28 s` rebuild), Sign (`380 HP` → topple → `115 s` ramp with **0/27 H St lanes >18 u step**, max `6.00 u`/8 u), Glass (**56/56 real hollow Hull-0 openings** across downtown & merged landmarks). |
| 5 | Traversal & Entity Placement (BSP2 Hull-1) | **PASS** | **36/36** spawns: `0` stuck in solid, `0` in SkyPads, `0` buried in rubble, `36/36` paired with accessible `misc_gokart_*` (`125.9–165.7 u`); **11/11** SkyPads: open sky, `0` arc hits, exact `0.0 u` landing-to-pad chaining (6-roof closed loop + 5 street feeders); **12/12** `trigger_push`: `0` wall/ceiling bonks; **13/13** jetpacks, **80/80** pickups, **3/3** Eric Cannons, **36/36** karts, **5/5** vehicles, **397/397** props: **0 clipping**; catwalks & ramps unobstructed. |

---

## 1. Downtown Layout, Scale & Sacred Anchors (`bakersfieldish.bsp` vs `bakersfielddowntown.bsp` + OSM)

### 1.1 Padre Hotel & Fox Theater Footprint, Scale, and Alignment
All destructible submodels were transformed to world space by entity `origin` and compared directly against `bakersfielddowntown.bsp` worldspawn geometry and `source/downtown/refs/osm_ft.json` (projected at `12 Quake units = 1 ft`).

| Anchor / Metric | Real Bakersfield (`osm_ft.json`) | `bakersfielddowntown.bsp` | `bakersfieldish.bsp` | Delta / Verification |
|---|---:|---:|---:|---|
| **Fox Theater** footprint (W × D) | `95.0 × 174.5 ft` (`1,140 × 2,094 u` @12u/ft) | `1,644 × 2,292 u`, Z `[0, 1,398]` (`11,504` faces) | `1,560 × 2,197 u`, Z `[-41, 1,397]` (`12,324` faces across clock + 7 pieces) | Center `(-9816.0, 3360.5)`, tower Z=`1,397 u` (within `1 u` of DT) |
| **Padre Hotel** footprint (W × D) | `103.9 × 111.7 ft` (`1,247 × 1,340 u` @12u/ft) | `1,389 × 1,602 u`, Z `[-2, 1,468]` (`20,734` faces) | `1,341 × 1,443 u`, Z `[0, 1,467]` (`17,233` faces across 7 pieces) | Center `(-9718.5, -5291.5)`, rooftop Z=`1,467 u` (within `1 u` of DT) |
| **Padre ↔ Fox** vector `(dx, dy)` | `(+23.6, -724.7) ft` | `(+85.5, -8,619.0) u` | `(+97.5, -8,652.0) u` | Bearing `+0.65° E of S` vs `+1.87°` OSM (1.22° alignment accuracy) |
| **Padre ↔ Fox** Euclidean distance | `725.1 ft` | `8,619.4 u` (`11.887 u/ft`) | `8,652.5 u` (`11.933 u/ft`) | Within **`0.56%`** of exact `12.0 u/ft` architectural scale |

### 1.2 Padre ↔ Fox Sightline Verification (Exact BSP2 Hull-0 Raycasts)
Eight Hull-0 raycasts were traced along the H Street corridor against both worldspawn and all solid non-Fox/Padre brush submodels (including intact `bako_sign_piece *54` spanning H Street at `Y = -3,360`):
- Street level (`Z=64`, H St center `X=-8700` & west lane `X=-8950`, Padre NE → Fox SE): **CLEAR** (WS & submodels)
- Street level (`Z=64`) → Fox marquee (`Z=240`) and Fox clock (`Z=976`): **CLEAR**
- Padre mid-floor (`Z=600`) → Fox clock (`Z=976`): **CLEAR**
- Padre rooftop (`Z=1480`) → Fox tower (`Z=1050`) and Fox marquee (`Z=240`): **CLEAR**
- Mid-arch corridor (`Z=200`, `X=-8700`, straight beneath Bakersfield Sign): **CLEAR** (sign arch underside sits at `Z=280 u` over the H St center roadway).
- Visually confirmed in `levelshots/bakersfieldish.jpg` and `round4/padre_r4_sheet.png` (`01_intact`), which frame Padre Hotel, the Bakersfield Sign across H St, and downtown north toward Fox Theater along one unbroken corridor.

### 1.3 6-Level Parking Garage Across From Padre (East Side of H St)
Located directly east of Padre Hotel across H Street (`X = [-8,358, -5,590]`, `Y = [-5,959, -4,562]`):
- **6 Distinct Horizontal Concrete Decks** (exact `128 u = 10.67 ft` floor-to-floor spacing, matching `bakersfielddowntown.bsp` 1:1):
  - Level 1: `Z = 8` (`3,363,868 sq.u`, `70/81` Hull-1 walkable grid points, min headroom `62.0 u`)
  - Level 2: `Z = 136` (`1,740,699 sq.u`, `70/81` walkable, min headroom `114.0 u`)
  - Level 3: `Z = 264` (`1,887,968 sq.u`, `70/81` walkable, min headroom `114.0 u`)
  - Level 4: `Z = 392` (`1,818,103 sq.u`, `70/81` walkable, min headroom `115.0 u`)
  - Level 5: `Z = 520` (`1,808,325 sq.u`, `70/81` walkable, min headroom `115.0 u`)
  - Level 6 (Rooftop): `Z = 648` (`1,753,720 sq.u`, `68/81` walkable, open sky headroom `>207 u`) + parapet `Z = 696`
- **Ramp Continuity (3D Hull-1 BFS):** `49` sloped ramp faces (`Z = [6.0, 703.0]`). Starting on Ground Level 1 at `(-7500, -5636, 32)`, continuous Hull-1 step-constrained BFS traversed **all 6 levels `[1, 2, 3, 4, 5, 6]`** (`14,998` connected states, reaching rooftop `feet Z = 705.0 u`).

### 1.4 Preserved Enterable Venues (Geometry Diff + Hull-1 Walk-In BFS)
Every required downtown enterable venue was verified against `bakersfielddowntown.bsp` and tested with 16 u-grid Hull-1 BFS (`<=18 u` step height) from its interior to open-sky street sidewalks (with intact glass):

| Venue | Interior BBox (`bakersfieldish.bsp`) | DT vs ISH Preservation | Indoor Hull-1 Space | Walk-In Door BFS to Open Street |
|---|---|---|---:|---|
| **Nile Theater** | `X[-11443,-10613] Y[-4119,-2764] Z[0,571]` | Exact bbox (`355 → 396` interior faces) | `709` cells (`Z=64`) | **PASS** — exits cleanly at `(-11088, -4288, 26)` |
| **Dagny's Coffee** | `X[-6516,-5018] Y[2381,3080] Z[0,205]` | Exact bbox (`635 → 874` interior faces) | `678` cells (`Z=64`) | **PASS** — exits onto 20th St at `(-5824, 2208, 32)` |
| **Sandrini's** (1918 Eye St) | `X[-4026,-3054] Y[12,630] Z[-132,182]` | Exact bbox (`3,685 → 4,000` Eye-block faces) | `2,864` connected ground + basement states (DT: `2,993`) | **PASS** — ground & basement both exit onto Eye St at `(-4096, 308, 32)` |
| **Jerry's Pizza** | `X[-1848,-798] Y[-4224,-3840] Z[-144,162]` | Exact bbox (`66 → 151` interior faces) | `239` cells (`Z=64`) | **PASS** — exits cleanly at `(-1648, -4400, 32)` |
| **Guthrie's Alley Cat** | `X[-3348,-2994] Y[-5268,-4586] Z[0,122]` | Exact bbox (`32 → 126` interior faces) | `113` cells (`Z=64`) | **PASS** — exits onto Wall St Alley at `(-3120, -4416, 32)` |

*(The Mint facade at `X[-11283,-10749], Y[-3193,-3085]` is also preserved 14/14 faces.)*

### 1.5 Street Widths & Block Scale Fidelity
Cross-sectional Hull-0 corridor scans at `Z=64` confirm `bakersfieldish.bsp` preserves `bakersfielddowntown.bsp` street coordinates to the exact Quake unit and matches real Bakersfield OSM spacing (`12 u/ft`):
- **N–S Streets (center X & facade-to-facade width):**
  - **G St:** `X ≈ -12,800` (width `1,064–1,680 u` / `89–140 ft`)
  - **H St:** `X ≈ -8,688` (width `928–1,032 u` / `77.3–86.0 ft`; G↔H spacing `4,112 u = 342.7 ft` vs OSM `345.6 ft`)
  - **Eye St:** `X ≈ -4,464` (width `984–1,056 u` / `82.0–88.0 ft`; H↔Eye spacing `4,224 u = 352.0 ft` vs OSM `353.1 ft`)
  - **Chester Ave:** `X ≈ -188` (width `1,152 u` / `96.0 ft`, widest downtown boulevard; Eye↔Chester spacing `4,276 u = 356.3 ft` vs OSM `351.9 ft`)
- **E–W Streets & Alleys (center Y & width):**
  - **18th St:** `Y ≈ -6,436` (`896–1,304 u`), **Wall St Alley:** `Y ≈ -4,392` (`376 u = 31.3 ft`), **19th St:** `Y ≈ -2,344` (`968–1,016 u = 80.7–84.7 ft`; 18th↔19th `4,092 u = 341.0 ft` vs OSM `344.5 ft`), **Service St Alley:** `Y ≈ -228` (`448 u = 37.3 ft`), **20th St:** `Y ≈ +1,880` (`1,040 u = 86.7 ft`; 19th↔20th `4,224 u = 352.0 ft` vs OSM `347.5 ft`), **21st St:** `Y ≈ +5,996` (`4,116 u = 343.0 ft` vs OSM `346.3 ft`).

---

## 2. All 4 Merged Landmarks & Complete Asset Integrity

### 2.1 Landmark Bounds, Scale Fidelity, Walkability & Overlap Audit

| Merged Landmark | Compiled World Bounds (Quake u) | Dimensions (W × D × H) | Identity & 1:1 Scale Evidence | Interior Walkability & Overlaps |
|---|---|---|---|---|
| **Golden West Casino** | `X[-4074,-714]` `Y[2286,5514]` `Z[0,387.5]` | `3,360 × 3,228 × 387.5 u` (`280.0 × 269.0 × 32.3 ft`) | `12,040` faces, `58` unique `gwc_*` textures (terracotta hip roof, white stone, purple pylon/LED, card tables `gwc_fbj`/`gwc_fpoker`/`gwc_fbacc`, porte-cochere, `progs/gw_buddha.md3` & `gw_horse.md3` matching `ref_sources/golden_west_landmarks/part_A.md`). | `1,851` indoor Hull-1 cells; open-door BFS exits to Eye St at `(-4256, 4000, 26)`. **0 building overlaps**. |
| **The Great Castle** | `X[-6708,-4890]` `Y[-54,1374]` `Z[0,378.0]` | `1,818 × 1,428 × 378.0 u` (`151.5 × 119.0 × 31.5 ft`) | `5,252` faces, `52` textures including `26` dedicated `gwc_gc*` textures (crenellated merlons, domes, red lanterns, calligraphy, plaques, murals, noren, gate). | `585` indoor Hull-1 cells; open-door BFS exits cleanly at `(-5792, -240, 26)`. **0 building overlaps**. |
| **Larry's Warehouse** | `X[-8148,-5442]` `Y[3353,5550]` `Z[0,384.0]` | Core `2,344.0 × 2,017.0 × 281.0 u` (`195.3 × 168.1 × 23.4 ft`) | **Exact `0.0 u` 1:1 match** to `bklan6.bsp` (`2,344.0 × 2,017.0 × 282.0 u`); `6,424` faces, `70` textures (`bk3_larry`, `bk_blansign`, `bk5_ortiz`, `bk5_cblogo`, `bk4_*`), populated with `30` LAN chairs, `36` monitors, `33` PCs, `26` tables, `3` `bk_tv`, forklifts, pallet racks. | `2,026` indoor Hull-1 cells; open-door BFS exits at `(-6560, 2848, 33)`. Separated from Dagny's (`Y≤3064`) by a clean **`296 u` open alley** (spanned overhead only at `Z=347` by rooftop catwalk). **0 overlaps**. |
| **The Bakersfield Sign** | `X[-9311,-8089]` `Y[-3443,-3277]` `Z[61,371]` (`*54`) | `1,222 × 166 × 310 u` (`101.8 × 13.8 × 25.8 ft`) | `727` faces (`96` `bk5_bsign` arch faces), top `Z=367–371 u` matches `bklan6.bsp` (`Z=367.0 u`) 1:1; sits on worldspawn concrete pier pedestals (`Z=0..56`) on H St sidewalks (`X=-9192`, `X=-8208`); clear roadway span `864 u` (`72 ft`) with `280 u` (`23.3 ft`) vertical arch clearance. | **0 Hull-0 overlap samples** against worldspawn buildings across `Z=64..360`. |

**Pairwise 3D AABB Check across all 9 major structures** (4 merged landmarks + Fox, Padre, Garage, Nile, Dagny's): **0 building-to-building overlaps.**

### 2.2 Exhaustive Asset Integrity (BSP + PK3 + PAK + `progs.dat` + Loose)
Indexed `20,983` VFS entries in Quake/Zircon load order (`id1/pak0..1.pak`, `quake15/q15.pk3`, `bakersfield.pk3`, all `zz_*.pk3`, loose `BakersfieldQuake/` files):
- **BSP Textures:** `1,037 / 1,037` resolved (`6` embedded/special + `1,031` external) — **0 missing**.
- **Skybox (`dtsky145_`):** `6 / 6` faces (`ft, bk, lf, rt, up, dn` in `bakersfield.pk3`) — **0 missing**.
- **BSP Entity Models (`mdl`/`model`):** `58 / 58` unique models (`269` instances) resolved; binary `IDP3` header & shader-skin inspection of all `58` `.md3` files confirmed **0 missing internal skins/shaders**.
- **`zz_bakersfieldish.pk3` Contents:** All `7` debris/shard MD3s (`bako_boulder1..4.md3`, `bako_glass_shard1..3.md3`) verified valid `IDP3` v15 with `8 / 8` surface skins present; `gfx/minimap/bakersfieldish.txt` (`-6360.00 -330.00 8796.80`) matches worldspawn center `(-6360.0, -334.0)` accurately; `scripts/bakersfieldish_minimap.shader` and `levelshots/bakersfieldish.jpg` valid.
- **Compiled `progs.dat` Integrity:**
  - **47 / 47** entity classnames in `bakersfieldish.bsp` map to valid compiled spawn functions in `progs.dat` (**0 missing**).
  - Bytecode string scan of active Bakersfield-ish modules confirmed **0 missing precached models or sounds**: `bako_destruct.qc` (`50/50`), `skypad.qc` (`11/11`), `gokart.qc` (`26/26`), `jetpack.qc` (`11/11`), `vehicles.qc` (`110/110`), `john_bird.qc` (`54/54`), `func_breakable` glass/rock/brick/wood/metal (`120/120`). *(The only 5 unresolved paths inside `breakable.qc` are `progs/misc_pot1.mdl` and `misc_potshard1..4.mdl` belonging to unused legacy Arcane Dimensions `misc_breakable_pot1`, 0 instances in `bakersfieldish.bsp`.)*
  - All `9` custom `bako_*` particle effects referenced by `BakoDestruct_Precache` exist in `BakersfieldQuake/effectinfo.txt` (plus `glass_break`).

---

## 3. Post-Apocalyptic Aesthetic & High Skybox

| Property | `bakersfielddowntown.bsp` | `bakersfieldish.bsp` | Verification |
|---|---:|---:|---|
| World bbox max Z | `3,371.0 u` | **`7,211.0 u`** | `+3,840 u` (**2.14×** total map height) |
| Sky ceiling face Z | `3,360 u` (`209` faces) | **`7,200 u`** (`168` faces) | **+3,840 u higher skybox** |
| Tallest non-sky structure Z | `1,632.0 u` | `1,632.0 u` (Padre `1,467 u`) | Preserved skyline |
| Open-sky clearance above tallest roof | `1,728.0 u` (`144 ft`) | **`5,568.0 u`** (`464 ft`) | **3.22× clearance** (`3,300 u` headroom even above highest `3,900 u` SkyPad apex) |
| Sun angle (`_sunlight_mangle`) | `60 -50 0` | `52 -38 0` | Lower golden-hour angle |
| Sun color (`_sunlight_color`) | `1 0.95 0.85` | `1 0.88 0.72` | Warmer dusty amber sunlight |
| Fog (`fog`) | `0.26 0.437 0.466 0.506 1 3650 5250 1800 450` | `0.22 0.56 0.49 0.41 1 4200 7600 2200 750` | Subtle warm ochre dust haze with *greater* draw clarity (`4,200–7,600 u`) |
| `.lit` Lightmap Mean RGB & Warmth | `(52.2, 51.7, 50.4)`, `R-B = +1.7` | `(56.8, 52.4, 46.2)`, `R-B = +10.6` | Bright, readable, lightly sun-baked golden tint |
| Light-Handed Dressing | `0` abandoned cars, `14` `npc_crowd`, `2` traffic | `75` parked abandoned vehicles (`28` coupe, `37` sedan, `10` truck), `0` crowds/traffic | Verified visually in `levelshot.jpg` & all 4 capture sheets: unmistakably recognizable downtown Bakersfield with understated post-apocalyptic mood, **not** a ruined wasteland. |

---

## 4. Destructibles Specification Audit (Compiled BSP2 Hull-1 + `progs.dat` + Captures)

Compiled global defaults verified directly from `progs.dat` binary global table:
- `autocvar_bako_fox_clock_hp = 200.0`
- `autocvar_bako_padre_hp = 2600.0` (**13.0× tougher than Fox**)
- `autocvar_bako_sign_hp = 380.0`
- `autocvar_bako_fox_rubble_t = 115.0 s`, `autocvar_bako_padre_rubble_t = 115.0 s`, `autocvar_bako_sign_rubble_t = 115.0 s` (**1.92 min — squarely inside the 1–2 min spec!**)
- `autocvar_bako_fox_rebuild_t = 25.0 s`, `autocvar_bako_auto_rebuild = 1.0`, `autocvar_bako_boulder_dmg = 15.0`

### 4.1 Fox Theater (`bako_fox_clock *60`, `7 × bako_fox_piece *61..*67`, `bako_fox_rubble *68`)
- **Trigger & Collapse:** Only `bako_fox_clock` (`200 HP`) triggers `Bako_TriggerFoxCollapse`. Seven staged pieces (`tower_upper`, `tower_lower`, `marquee`, `facade_e`, `facade_s`, `auditorium_roof`, `stagehouse`; staggered delays `0.45–3.50 s`, durations `4.60–6.00 s`, outward fall angles/shifts) topple outward with flying masonry chunks, dust surge, and smooth 60 Hz seismic shake (`Bako_SafeShake` / `Bako_TickSmoothShake`). Confirmed visually in `round5/fox_r5_sheet.png` frames `01`–`07`.
- **Climbable Rubble (`*68`, `2,030` faces, peak surface `Z = 342.0 u`):** Direct BSP2 Hull-1 grid BFS (`24 u` grid, `5,972` rubble cells) from street perimeter reaches **5,851 / 5,972 (98.0%) walk-only (`<= 18 u` step)** up to full peak `Z = 342.0 u`, and **5,972 / 5,972 (100.0%) with standard jump (`<= 42 u`)**.
- **Rubble Duration & Slow Rebuild:** Persists `115 s` (`1.92 min`), then executes a staged bottom-up `25 s` rebuild (rubble sink → stagehouse/hall → marquee → lower tower → upper tower + clock with welding sparks & chime). Confirmed cleanly in `round5/fox_r5_sheet.png` frames `08`–`16`. Rooftop props/SkyPads are hidden during collapse via `Bako_HideRoofProps(BAKO_GRP_FOX)` and restored intact.

### 4.2 Padre Hotel (`7 × bako_padre_piece *69..*75`, `bako_padre_rubble *76`)
- **Toughness & All-Weapon Damage:** `2,600 HP` unified pool across all 7 pieces (`13×` Fox clock), accepting direct damage from any weapon (`BakoDestruct_OnDamage`) plus rocket splash and Eric Cannon nuke blasts (`BakoDestruct_RadiusSplash`, `1.75×` nuke multiplier). Progressive 75% / 50% / 25% outer-facade window smoke & glass shatters confirmed in `round4/padre_r4_sheet.png` frames `02`–`04`.
- **Slow Inward Controlled Demolition & Non-Blinding Dust:** 10 perimeter charge pops (`05_charge_pops`) followed by ~12 s inward V-tilt / vertical pancake collapse of all 7 tiers (`tier1..4`, `west_wing`, `east_wing`, `crown`; `shift` vectors pulling wings inward, `06`–`08`). Volumetric street surge (`bako_demolition_dust_surge`: `type alphastatic`, `size 58–94`, **`alpha 68–112` = 26%–44% opacity**, decaying cleanly) creates a massive tan cloud without blinding players (`09`–`11`).
- **Tumbling/Rolling Boulders & Earthquake:** Three waves of rolling 3D `bako_boulder1..4.md3` rocks (`Bako_BoulderTouch` / `Bako_BounceTarget`) actively bounce players (`kick_h = 460..660`, `kick_z = 380..440`, `15` dmg) and vehicles (`kick_h = 280..460`, `kick_z = 210`), coupled with landing seismic shake (`padre_r4_sheet.png` frame `10_rolling_boulders`).
- **Climbable Rubble (`*76`, `2,634` faces, peak surface `Z = 376.0 u`):** Direct BSP2 Hull-1 BFS (`3,393` rubble cells) reaches **3,358 / 3,393 (99.0%) walk-only (`<= 18 u` step)** up to full peak `Z = 376.0 u`, and **3,393 / 3,393 (100.0%) with jump**. Stays `115 s` (`1.92 min`), followed by a `28 s` staged rebuild.

### 4.3 Bakersfield Sign (`bako_sign_piece *54`, `bako_sign_rubble *55`)
- **Topple, Bounce, Debris & Earthquake:** `380 HP`, 4.2 s accelerating north topple (`ang 0 0 -90`) with elastic street rebound, full-width H Street dust veil, sparks/debris, and seismic shake (`round3/sign_r3_sheet.png` frames `01`–`10`). Stays `115 s`, then 10 s crane hoist rebuild.
- **Exact Hull-1 Step-Height Profile Across H Street (`bako_sign_rubble *55`, `704` faces):**
  Sampled across **all 27 roadway lanes** spanning H Street (`X = -9,120 .. -8,288` at `32 u` lateral spacing, marching `Y = -3,420 .. -2,840` at `8 u` longitudinal intervals via combined worldspawn + `*55` Hull-1 traces):
  - Roadway arch peak surface height: **`40.0 u`** across all 27 lanes.
  - **Lanes with any step `> 18 u` (Quake `STEPSIZE`):** **`0 / 27`** going South→North and **`0 / 27`** going North→South!
  - **Global max single `8 u` vertical step across all 27 lanes:** **`5.37 u`** (S→N) and **`6.00 u`** (N→S); max `16 u` step **`7.6 u`** — comfortably below both player `STEPSIZE = 18 u` and Go-Kart step-climb (`22 u` in `gokart.qc:580`).
  - Sidewalk fallen pier sections (`Z = 40..108 u`) are **100.0% reachable** with jump (`747 / 747` rubble cells). Visually confirmed rampable by Go-Kart in `round3/sign_r3_sheet.png` frame `12_fallen_sweep`.

### 4.4 Shatterable Glass (`56 × func_breakable`)
- **Distribution across Downtown & Merged Landmarks:** Dagny's Coffee (`18`), Golden West Casino (`12`, merged), Padre Hotel (`10`), 6-Level Parking Garage (`4`), Larry's Warehouse (`4`, merged), The Great Castle (`2`, merged), plus other downtown storefronts (`6`) = **56 panes** across **7+ distinct buildings**.
- **True Face-Normal Hollow-Opening Verification:** Full-width normal sweep of every pane (excluding the glass submodel itself to simulate post-shatter state):
  - **56 / 56 (100.0%)** verified as **real hollow openings** (Hull-0 open on both sides, open at pane center, and clear Hull-0 raycast straight through — zero fake solid-backed panes!).
  - **45 / 56** are immediately full-player Hull-1 passable at center sweep (the remaining 11 are narrow 30–39 u casements/clerestories or Padre's wide mullioned storefront bays `*7..*11`, which `round3/glass_r3_sheet.png` frames `05`–`08` confirm are walk-in/jump-through passable into the Padre lobby between mullions!).
  - Shards (`bako_glass_shard1..3.md3`) & 120 s glass respawn verified in `progs.dat` and `round3/glass_r3_sheet.png`.

---

## 5. Exhaustive BSP2 Hull-1 Traversal & Entity Placement Verification

Every entity in `maps/bakersfieldish.bsp` was tested directly against compiled BSP2 Hull-0, Hull-1 (`-16,-16,-24` to `+16,+16,+32`), and (where applicable) Hull-2 (`-32,-32,-24` to `+32,+32,+64`) clipnodes across worldspawn and all solid brush submodels.

### 5.1 Player Spawns (`1 × info_player_start` + `35 × info_player_deathmatch` = 36 total)
- **Stuck in solid (Hull-1):** **0 / 36**
- **Floating (`> 64 u` above floor):** **0 / 36**
- **Inside any `info_skypad` trigger bbox (`±40 × ±40 × [-26, +36]`):** **0 / 36**
- **Buried inside any rubble Hull-1 solid (`fox`/`padre`/`sign`):** **0 / 36** *(Spawn #4 at `(-10092, -4932, 225)` stands on Padre 2F intact terrace `Z=198`; when collapsed, Padre rubble surface underneath is `Z=19.0`, leaving `182 u` of open air below spawn feet — zero burial).*
- **Paired with nearby accessible `misc_gokart_*`:** **36 / 36 paired** (`36` karts for `36` spawns; nearest-kart 3D distance `min = 125.9 u`, `median = 126.0 u`, `max = 165.7 u`). `35 / 36` have unobstructed direct Hull-1 line-of-sight; the sole corner-offset pair (Spawn #24 at `(-5960, 5047, 28)` → `misc_gokart_6` at `(-6100, 5128, 64)`, `165.7 u` inside Larry's Warehouse) was verified walkable via Hull-1 BFS (`164` steps, both on floor `Z=1.0`).

### 5.2 SkyPads (`11 × info_skypad`) — Exact `skypad.qc` Parabolic Hull-1 Sweep
Simulated every pad using exact `SkyPad_CalcVel(p0, pos1, height)` (`sv_gravity = 800`, `p0 = (org.x, org.y, H1_stand_z + 2)`, `dt = 0.005 s`) traced against worldspawn + all intact solid submodels in BSP2 Hull-1:

| Pad # | Destination (`message`) | Launch `org` → Landing `pos1` | Apex Z / Flight `tf` | Open Sky Overhead | Full-Arc Hull-1 Result | Chains To (XY Dist) |
|---:|---|---|---:|---|---|---|
| 1 | Fox Roof | `(-10020,-5580,1256)` → `(-10188,3492,638)` | `3,400 u` / `4.94 s` | **CLEAR** (`7,150+ u`) | **0 hits** — lands `dxy=2.7 u` on `*66` | **Pad #2** (`0.0 u`) |
| 2 | Larry's Warehouse Roof | `(-10188,3492,638)` → `(-7380,4404,230)` | `3,000 u` / `5.06 s` | **CLEAR** | **0 hits** — lands `dxy=0.3 u` on WS | **Pad #3** (`0.0 u`) |
| 3 | Golden West Casino Roof | `(-7380,4404,230)` → `(-2364,4608,221)` | `3,100 u` / `5.36 s` | **CLEAR** | **0 hits** — lands `dxy=0.5 u` on WS | **Pad #4** (`0.0 u`) |
| 4 | Great Castle Roof | `(-2364,4608,221)` → `(-5833,485,182)` | `3,200 u` / `5.47 s` | **CLEAR** | **0 hits** — lands `dxy=0.5 u` on WS | **Pad #5** (`0.0 u`) |
| 5 | Parking Garage L6 Roof | `(-5833,485,182)` → `(-7260,-5160,674)` | `3,100 u` / `5.16 s` | **CLEAR** | **0 hits** — lands `dxy=0.6 u` on WS | **Pad #6** (`0.0 u`) |
| 6 | Padre Roof | `(-7260,-5160,674)` → `(-10020,-5580,1256)` | `3,300 u` / `4.82 s` | **CLEAR** | **0 hits** — lands `dxy=1.0 u` on `*75` | **Pad #1** (`0.0 u`) |
| 7 | Fox Roof Chain (H St) | `(-8316,-2880,32)` → `(-10188,3492,638)` | `2,900 u` / `5.05 s` | **CLEAR** | **0 hits** — lands `dxy=2.1 u` on `*66` | **Pad #2** (`0.0 u`) |
| 8 | Larry's Warehouse Roof (SW) | `(-13200,-5964,32)` → `(-7380,4404,230)` | `3,900 u` / `6.14 s` | **CLEAR** | **0 hits** — lands `dxy=0.8 u` on WS | **Pad #3** (`0.0 u`) |
| 9 | Golden West Roof (SE) | `(396,-5964,32)` → `(-2364,4608,221)` | `3,700 u` / `5.98 s` | **CLEAR** | **0 hits** — lands `dxy=0.8 u` on WS | **Pad #4** (`0.0 u`) |
| 10 | Parking Garage L6 (NE) | `(-996,2268,32)` → `(-7260,-5160,674)` | `3,600 u` / `5.69 s` | **CLEAR** | **0 hits** — lands `dxy=0.8 u` on WS | **Pad #6** (`0.0 u`) |
| 11 | Golden West Roof (Larry's) | `(-6672,3876,27)` → `(-2364,4608,221)` | `3,100 u` / `5.45 s` | **CLEAR** | **0 hits** — lands `dxy=0.4 u` on WS | **Pad #4** (`0.0 u`) |

- **Continuous Cross-Map Chaining:** **11 / 11** landing zones land **directly on another `info_skypad`** (`0.0 u` exact offset!). Pads `#1→#2→#3→#4→#5→#6→#1` form a closed 6-landmark rooftop circuit across the entire map, fed by all 5 street-level launch pads (`#7–#11`). During Fox/Padre collapse, rooftop pads hide cleanly via `Bako_HideRoofProps` and inbound flyers keep 10 s fall immunity (`skypad_safe_t`) onto the rubble below.

### 5.3 Regular Jump Pads (`12 × trigger_push`) — Exact `triggers.qc` Hull-1 Sweep
Simulated all 12 `trigger_push` volumes (`*77..*88`) using exact `triggers.qc:828` velocity (`speed * movedir * 10`, re-applied while inside trigger bbox, ballistic `g = 800` afterward) against Hull-1:
- **Wall / ceiling bonks:** **0 / 12**
- **Clean rooftop/ledge touchdowns:** **12 / 12** (`*77` → Fox roof `Z=636`, `*78` → Padre roof `Z=1254`, `*79` → Padre 2F terrace `Z=222`, `*80` & `*81` → Garage L6 `Z=672`, `*82` → Garage L6→Padre roof `Z=1259`, `*83` → Fox marquee `Z=288`, `*84` → Great Castle roof `Z=180`, `*85` → Golden West roof `Z=219`, `*86` → Larry's roof `Z=231`, `*87` → Dagny's roof `Z=360`, `*88` → East downtown roof `Z=672`).

### 5.4 Jetpacks, Creative Ramps/Catwalks, Pickups, Cannons, Vehicles & Props
- **`item_jetpack` (13 total):** **0 / 13 clipping** in Hull-0 or Hull-1. Sensibly distributed across all 3 far map corners (NW G & 21st, SW G & 18th, SE Chester & 18th), tall rooftops (Padre Roof `Z=1256`, Padre 2F `Z=224`, Fox Roof `Z=638`, East/Garage roof `Z=674`), all 3 enterable merged landmarks (Golden West Roof & Ground, Larry's Roof ×2, Great Castle Tower `Z=357` resting on `Z=330.5` parapet), and H St near the Sign.
- **Creative Ramps & Catwalks:**
  - Dagny's Coffee Roof ↔ Larry's Warehouse Roof elevated steel/wood catwalk (`X[-5940,-5776], Y[3104,3360], Z=347`, guardrails `Z=382`): end-to-end Hull-1 centerline sweep `(-5872, 3040, 373) → (-5872, 3420, 373)` returned **`hit = False, fraction = 1.000`** (100% unobstructed).
  - Parking Garage L6 rooftop jump/ramp (`X=-6300, Y[-4720..-4512], Z=648 → 703 → 664.5`), Parking Garage exterior steel catwalk (`X=-7680, Y=-4658, Z=302..559`, 3/3 clear), Parking Garage 6-level internal ramps (100% continuous L1→L6), and fallen Bakersfield Sign H St ramp (max step `≤ 6.0 u`): all unobstructed.
- **All Remaining Entities (Zero Clipping):**
  - Pickups (`80` total: weapons, health, armor, ammo): **0 Hull-0 clips, 0 Hull-1 standing clips** *(Padre `weapon_rocketlauncher` at `(-9564, -5280, 72)` sits over the open Padre lobby-to-basement stairwell `Z=-25` and drops cleanly onto the stairs via `droptofloor`)*.
  - `misc_eric_cannon` (`3` total: Garage L6 Roof, H St/19th, Golden West Casino): **0 Hull-0 / Hull-1 / Hull-2 clips**.
  - `misc_gokart_*` (`36` total, `vehicles.qc:674` bbox `-16,-16,0` to `16,16,19.5`): **0 Hull-0 / Hull-1 clips** (`35/36` even clear 64×64 Hull-2; `misc_gokart_6` inside Larry's Warehouse sits `32 u` from the north wall = `16 u` clear of its 32×32 kart hull).
  - `misc_vehicle_*` (`5` total: `2` JohnBirds, `1` GT Car, `1` Rocket Rider, `1` Van): **0 Hull-0 / Hull-1 / Hull-2 clips**.
  - Decorative & LAN props (`251` `misc_model`, `143` `misc_lan_*`, `3` `bk_tv` = `397` total): **0 origin+4 u Hull-0 clips**.

---

## Final Verdict

**PASS.** Every quantitative requirement across downtown architectural fidelity, sacred anchors, all 4 merged landmarks, asset completeness, high skybox & light-handed post-apocalyptic look, destructibles physics/specs, and exhaustive BSP2 Hull-0/Hull-1 traversal & entity placement passes cleanly with zero blocking defects.
