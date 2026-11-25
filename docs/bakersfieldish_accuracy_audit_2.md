# Bakersfield-ish (`maps/bakersfieldish.bsp`) — Independent Accuracy Audit #2
**Visual, Reference-Photo, StreetView & Cohesive Downtown Accuracy Audit**

- **Auditor:** Fresh Accuracy Auditor #2 of 4 (zero prior build history; zero edits to code/map/assets; zero Zircon launches)
- **Target Artifact:** `maps/bakersfieldish.bsp` (`40,958,428` bytes, BSP2, `sha256: e84a632c84e12dfc`, identical to `source/downtown/out/bakersfieldish.bsp`)
- **Baseline Artifact:** `maps/bakersfielddowntown.bsp` (`37,081,900` bytes, BSP2, `sha256: c361b24f13af93d6`)
- **Evidence Inspected Directly:**
  - Compiled BSP geometry, Hull-0 BSP trees, entity lumps, face normals, and UV vectors parsed directly from `maps/bakersfieldish.bsp` and `maps/bakersfielddowntown.bsp`
  - 2D planimetric heightmaps, BSP-vs-BSP diff overlays, real OpenStreetMap footprint overlays (`source/downtown/refs/osm_ft.json`, `osm_plan.png`, `plan_fox.png`), east–west skyline elevation profiles, and traversal entity overlays
  - Real downtown Bakersfield aerials, Google StreetView galleries, and prior downtown HTML docs:
    - `source/downtown/refs/downtown-bakersfield/` (`005.jpg` aerial, `029.jpg` Padre 18th St, `071.jpg` Bakersfield Sign, `160.jpg` Fox Theater at 20th & H)
    - `source/downtown/refs/padre-hotel/` (`000.jpg`, `018.jpg`, `044.jpg`), `source/downtown/refs/padre-garage/` (`012.jpg` corner w/ Padre behind, `019.jpg` Eye St view of AT&T block)
    - `source/mm_tools/ref_sources/streetview_gallery1/` (`aerial-z18-hybrid.jpg`, `sv-front-118e21st-...yaw45.jpg`, `captions.txt`)
    - `source/mm_tools/ref_sources/golden_west_gallery/` (`043.jpg` Golden West Casino & purple pylon, `177.jpg` Great Castle white merlon parapet & pylon)
    - `docs/padre_hotel_redesign.html`, `docs/bakersfielddowntown_viewer_showcase.html`, `docs/bakersfield_dm_feedback_report.html`
  - Full-motion in-game capture videos, contact sheets, and full-res keyframes:
    - `docs/bakersfieldish_captures/round5/fox_r5.mp4`, `fox_r5_sheet.png`, `fox_r5_keyframes/09_rubble_clean_b.png`
    - `docs/bakersfieldish_captures/round4/padre_r4.mp4`, `padre_r4_sheet.png`, `padre_r4_keyframes/12_rubble_aftermath.png`
    - `docs/bakersfieldish_captures/round3/sign_r3.mp4`, `sign_r3_sheet.png`, `sign_r3_keyframes/12_fallen_sweep.png`
    - `docs/bakersfieldish_captures/round3/glass_r3.mp4`, `glass_r3_sheet.png`
  - Runtime destructible & traversal contracts in `source/qc_combat_decomp/bako_destruct.qc`, `bako_destruct_defs.qc`, `skypad.qc`, and `source/downtown/pieces/bakersfieldish/*.py`

---

## Overall Verdict: **FAIL**

**Summary:** The downtown fidelity, real-world Bakersfield reference accuracy, architectural integration of the 4 merged landmarks, light-handed post-apocalyptic atmosphere, 600-ft high skybox, and cinematic destructible spectacles are **strong PASSes** — genuinely cohesive, recognizable downtown Bakersfield with zero mirrored signage and crisp, non-blinding demolition sequences.

However, direct compiled-BSP geometric, Hull-0 solidity, and ballistic-trajectory verification uncovered **multiple concrete, player-breaking traversal defects** that require a strict **FAIL** until fixed:
1. **3 Deathmatch Spawns co-located (`0.00 ft` XY) directly inside `info_skypad` trigger boxes** (spawning on Golden West Roof, Larry's Warehouse Roof, or Great Castle Roof immediately flings the player into the sky).
2. **2 Regular Jump Pads (`trigger_push`) ballistically slam players into the Parking Garage exterior concrete walls** (`18th St -> Garage L6` hits the south wall at `Z=56.3 ft` below the `58.17 ft` parapet; `Eye St -> Garage L6` hits the east wall at `Z=42.6 ft`, `15.5 ft` below the parapet).
3. **3 Creative Stunt Ramps & 1 Rooftop Sniper Catwalk are geometrically obstructed/dead-ended** (Ramp #5b has a steel dumpster placed directly inside the ramp; Ramp #5a clips through hedges/poles and slams into a 24-ft solid Garage column; Ramp #5c slopes into Fox Theater's sheer 58-ft blank west wall; Catwalk #3 is sealed off from Garage L6 by a `4.17 ft` / `50 u` parapet exceeding standard Quake jump height).
4. **Garage L6 `item_jetpack` and `misc_vehicle_johnbird` co-located (`0.00 ft` XY, `0.67 ft` Z).**
5. **Minor spec deviations:** Fox Theater rubble duration is `150 s` (`2.5 min`, exceeding the 1–2 min window by 30 s), and Larry's Warehouse ended up with `0` shatterable glass panes after pruning.

---

## Scorecard by Requirement

| Area | Status | Key Evidence |
|---|---|---|
| 1. Faithfulness to Original Downtown & Real Bakersfield | **PASS** | 1:1 street grid & OSM footprints; Padre, Fox, Garage, Nile, Dagny's, Bare Studios, Sandrini's, Jerry's, PG&E tower preserved; only Tier C/D generic buildings & lots replaced |
| 2. Cohesiveness of 4 Merged Landmarks | **PASS** *(1 minor note)* | All 4 fit cleanly inside street curbs with 0 mirrored signs, 0 building clipping, 0 stray parked cars inside lots; minor note on Larry's south frontage facing rear alley behind Dagny's/Bare |
| 3. Post-Apocalyptic Look & Feel + High Skybox | **PASS** | Compiled skybox raised `280 ft -> 600 ft` (`3,360 u -> 7,200 u`, 2.14×); warm dusty late-afternoon sun/haze; restrained barriers/rubble keeping all roadways open |
| 4a. Destructibles Visuals & Mechanics (Fox, Padre, Sign, Glass) | **PASS** *(1 minor timer note)* | All 4 video captures verified cinematic, slow enough to watch, non-blinding, zero floating sky items; Fox rubble timer `150 s` is 30 s over the 1–2 min spec |
| 4b. Traversal & Creative Placement Spec | **FAIL** | 36/36 spawns paired with go-karts & 10/10 SkyPads chain at `0.00 ft` with 0 clips — **BUT** 3 spawns sit inside SkyPads, 2 Garage jump pads slam into walls, 3 ramps + 1 catwalk are blocked, and Garage L6 jetpack overlaps John Bird |

---

## 1. Faithfulness to Original Bakersfield Downtown & Real Bakersfield — **PASS**

### 1.1 Compiled BSP Macro Comparison
| Metric | `maps/bakersfielddowntown.bsp` | `maps/bakersfieldish.bsp` | Notes |
|---|---:|---:|---|
| Format / Visleafs | BSP2 / `32,115` | BSP2 / `33,382` | Cleanly below 35k budget (`+1,267` visleafs) |
| Faces / Textures | `116,319` / `927` | `151,142` / `1,036` | `+34,823` faces from 4 landmarks + rubble bmodels |
| XY Footprint (D-feet) | `X[-340.9..950.9], Y[-901.6..275.9]` | `X[-340.9..950.9], Y[-901.6..275.9]` | Exact 1:1 world extent match |
| Sky Ceiling (`SKY_Z`) | `280.0 ft` (`3,360 u`) | `600.0 ft` (`7,200 u`) | **+320 ft (+2.14×)** verified in compiled sky faces |

### 1.2 Street Grid & Real OSM Alignment
Planimetric heightmap diff overlays comparing `bakersfieldish.bsp`, `bakersfielddowntown.bsp`, real OpenStreetMap (`osm_ft.json` / `osm_plan.png`), and Google Maps hybrid aerial (`source/downtown/refs/downtown-bakersfield/005.jpg`) confirm:
- All 8 primary arterial streets (`18th St`, `19th St`, `20th St`, `21st St`, `G St`, `H St`, `Eye St`, `Chester Ave` with central median) plus secondary corridors (`Wall St`, pedestrian `Guthrie's Alley`, `Service St`, `Fox West Alley`) remain at their exact real-world alignments and curb-to-curb widths (`44–66 ft`).
- Only two internal dead-end stub alleys (`20th Place` inside `GW-A` and the north stub of `Dagnys Alley` inside `LW-A`) were intentionally suppressed so asphalt strips do not slice through the Golden West Casino or Larry's Warehouse compound floors.

### 1.3 Core Downtown Anchor Verification
| Core Landmark | Compiled `bakersfieldish.bsp` Bounds (D-feet) | Reference Verification |
|---|---|---|
| **The Padre Hotel** | `X[-30.8..81.0] (111.8 ft)`, `Y[-786.1..-665.8] (120.2 ft)`, `Z[0.0..122.2 ft]` | Exact 8-story L-tower footprint at 18th & H matching `005.jpg`, `padre-hotel/044.jpg`, and `padre-garage/012.jpg`. Cream/tan stucco, dark-trimmed grid windows, red `THE PADRE` rooftop sign, right-reading `THE PADRE` black entrance canopies (`pad_canopy` `dotLR=+0.381/+0.356`), 1F open-concept checkered lobby + 2F Prairie Fire terrace + Basement Gym + Clover/Old Post Office west wing all preserved. *(Trade-off note: 3F–8F guestrooms and moving `func_train` elevators from `bakersfielddowntown.bsp` were replaced by recessed solid concrete interior cores in `destructible_padre.py` so controlled demolition does not show hollow window slits or floating elevator cabs.)* |
| **Historic Fox Theater** | `X[-48.0..82.0] (130.0 ft)`, `Y[-96.5..86.6] (183.1 ft)`, `Z[-3.4..116.4 ft]` | Exact 20th & H footprint `582.4 ft` north of Padre along H St. `fox_r5.mp4` frame `00:00` matches StreetView `downtown-bakersfield/160.jpg` 1:1: cream stucco, peach pilasters, red neon `FOX` letters on clock tower, blue-tiled dome, wrap-around cursive `Fox` marquee, 20th St signal arm, and palms — with Bare Studios (`2000 H St`, `X[146.7..264.6], Y[-88.9..-30.8]`) preserved right across H St. |
| **18th & Eye Parking Garage** | `X[152.8..425.0] (272.2 ft)`, `Y[-781.6..-658.5] (123.1 ft)`, `Z[0.5..63.4 ft]` | Exact 6-level garage directly across H St from Padre (with 1818 H St shopfront on NW corner), matching `padre-garage/012.jpg` and `padre_r4.mp4`. |
| **Other Core Venues** | Nile Theater, Clover/Old Post Office, Dagny's Coffee (`X[287.4..424.2], Y[-93.7..-26.8]`), Bare Studios, Sandrini's, Jerry's Pizza, PG&E Bldg + 136-ft Radio Tower | 100% intact on original footprints in the BSP diff map. |

### 1.4 Replaceable-Only Audit
Direct diff of `bakersfielddowntown.bsp` vs `bakersfieldish.bsp` proves **zero iconic downtown landmarks were sacrificed**:
- **`GW-A` (`Eye–Chester / 20th–21st`):** Replaced the windowless monolithic grey AT&T switchboard (`59518832` — clearly visible as an architectural eyesore in real Parking Garage rooftop photo `source/downtown/refs/padre-garage/019.jpg`), generic `59521020`/`59522422`, and fenced vacant lot `GAP-01`.
- **`LW-A` (`H–Eye / 20th–21st` north half):** Replaced surface parking lots and generic American Legion hall (`59520322`) while keeping Dagny's Coffee (`Y=-93.7..-26.8`) and Bare Studios (`Y=-88.9..-30.8`) completely untouched.
- **`GC-A` (`H–Eye / Service–20th` east half):** Replaced low generic commercial mass `59503393` and lot apron while preserving the PG&E building and 136-ft radio tower `28 ft` to the west.
- **`S1` (`H St` at `Y=-565`):** Spans H St between the vacant Nile East Lot (west tower) and the wide sidewalk apron west of Boca's Cantina (east tower).

---

## 2. Cohesiveness of the 4 Merged Landmarks — **PASS** *(1 Minor Orientation Note)*

### 2.1 Quantitative Placement, Setbacks & Sign Orientation Audit
Every vertical sign face across all 4 landmarks was checked directly in compiled `maps/bakersfieldish.bsp` using exact vertex-winding outward normals (`wn`) and texinfo UV axes (`dotLR_w > 0` = right-reading L→R; `dotTD > 0` = right-side-up):

| Landmark & Slot | Compiled Bounds (D-feet) | Height | Setbacks & Continuity | Sign UV Check (`mirrored / total`) |
|---|---|---:|---|---|
| **Golden West Casino** (`GW-A`: `Eye–Chester / 20th–21st`) | Bldg `X[542.8..709.9], Y[-29.5..128.5]`; Pylon `X[736.0..748.0], Y[-76.5..-59.5]` | `32.3 ft` (Pylon `28.5 ft`) | Sits cleanly inside 4-street block; conical rotunda fronts 20th St, 45° portico + `gw_horse.md3` courtyard open SE toward 20th & Chester, 28.5-ft purple pylon anchors 20th & Chester corner (`D(742,-68)`), flush `0.50 ft` concrete border meets `0.50 ft` downtown sidewalk. Matches `golden_west_gallery/043.jpg`. | **0 / 28 mirrored** (`gwc_pyltop` E/W, `gwc_pylled` E/W, `gwc_cashier`, `gwc_pushtoop`, `gwc_goldwin` all `[OK]`) |
| **The Great Castle** (`GC-A`: `H–Eye / Service–20th`) | Bldg `X[302.0..381.9], Y[-272.5..-192.5]`; Pylon `X[415.3..416.7], Y[-218.0..-206.0]` | `31.5 ft` (Pylon `18.6 ft`) | `28 ft` clear east of PG&E radio tower (`X=274`); watchtower, crimson barrel canopy & rock garden front 20th St across from Dagny's; 40-ft `GREAT CASTLE` wall sign (`gwc_gcwest`, `wn=(+1,0)`) and merlon pylon (`D(416,-212)`) front Eye St across from Sandrini's; rear exits open onto Service St. Matches `golden_west_gallery/177.jpg`. | **0 / 13 mirrored** (`gwc_gcwest`, `gwc_gcpylon` E/W, `gwc_gcplaque` N, `gwc_gcopen`, `gwc_gc410`, `gwc_gcrest`, `gwc_gcmural`, `gwc_gccallig`, `{gwc_gcbann` all `[OK]`) |
| **Larry's Warehouse** (`LW-A`: `H–Eye / 20th–21st` N) | `X[175.5..381.5], Y[-9.4..167.7]` | `32.0 ft` | Preserves 1:1 B76 + LAN Courtyard + B45/Unit 130A matching `aerial-z18-hybrid.jpg` & `sv-front-118e21st-...yaw45.jpg`. Clear `19 ft` open alley (`solid=[]` at `Z=4 ft` across `X=160..400`) separates south facade from Dagny's/Bare Studios; wide open north walk-out onto 21st St. Visible seamlessly behind Bare Studios in `fox_r5_keyframes/09_rubble_clean_b.png`. | **0 / 16 mirrored** (`bk3_larry` W/E roof billboard + courtyard, `bk3_pylon` S/N, `bk5_ortiz`, `bk_baterias`, `dan_4am`, `dan_shaaa` all `[OK]`) |
| **The Bakersfield Sign** (`S1`: `H St` at `Y=-565`) | `X[59.1..160.9], Y[-571.9..-558.1]` (spacing `88.0 ft` = 90.7% of real 97 ft) | `30.9 ft` | Clear `78 ft` roadway opening spans `52 ft` H St + both sidewalks; `17.5–23.1 ft` overhead clearance; West Tower sits cleanly on Nile East Lot; East Tower clears H St east curb by `10 ft` and Boca's Cantina (`X=162.6`) by `3.6 ft` base / `1.6 ft` eave; matches real StreetView `downtown-bakersfield/071.jpg`. Frames the Padre↔Fox H St hero spine in `padre_r4.mp4` and `sign_r3.mp4`. | **0 / 52 mirrored** (`bk5_bsign` all 44 N/S faces + `bk_bupper` all 8 city seal faces `[OK]`) |

### 2.2 Cohesiveness Findings & Minor Observations
- **Zero clipping / zero stray props:** Hull-0 checks confirm 0 parked cars or downtown street props trapped inside `GW-A`, `LW-A`, `GC-A`, or `Sign S1` (`gw_buddha.md3` and `gw_horse.md3` both `inside_solid=False`).
- **Sidewalk & lot elevation continuity:** Downtown sidewalks (`0.50 ft`, `ds_conc`) meet `GW-A` border (`0.50 ft`, `gwc_conc`) and `LW-A` border (`0.42 ft`, `bk_walk`) cleanly without abrupt walls or clipping curbs, stepping down smoothly to interior parking-lot asphalt (`0.08–0.17 ft`).
- **Minor Cohesiveness Note (Non-Blocking):** Because Larry's Warehouse kept native `ROT=0`, its iconic street-frontage facade (`BATERIAS $55`, `ORTIZ`, `120A`, `LARRY'S` pylon) faces **south** into the 19-ft rear alley behind Bare Studios and Dagny's Coffee, while its rear industrial yard wall faces 21st Street. The alley is 100% open and drivable, the north courtyard exits cleanly onto 21st St, and the rooftop `LARRY'S` billboard is readable from both H St and Eye St, so it remains cohesive — though slightly less immediately recognizable from 21st St than if rotated 180°.

---

## 3. Post-Apocalyptic Look & Feel + High Skybox — **PASS**

- **High Skybox:** Compiled sky ceiling is **`600.0 ft` (`7,200 u`)**, verified directly in BSP sky face vertices (`model[0] maxs_z = 7211 u`), vs `280.0 ft` (`3,360 u`) in `bakersfielddowntown.bsp`. Every rooftop SkyPad arc (`242–325 ft` apex) enjoys `275–358 ft` of open sky above its peak.
- **Atmosphere & Lighting:** Worldspawn lighting (`_sunlight 235`, `_sunlight_mangle 52 -38 0`, `_sunlight_color 1 0.88 0.72`, `_minlight 98`, `fog 0.22 0.56 0.49 0.41 1 4200 7600 2200 750`, `skyname dtsky145_`) renders a crisp warm late-afternoon dusty California sky with clean overhead blue transitioning to warm golden-tan horizon haze — verified visually across all 4 capture videos (`fox_r5.mp4`, `padre_r4.mp4`, `sign_r3.mp4`, `glass_r3.mp4`).
- **Light-Handed Dressing (NOT a Wasteland):** Visually confirmed across H St, 18th St, 19th St, and 20th St in all 4 captures. All 19 Jersey barriers sit `3–11 ft` from road curbs, keeping `30+ ft` center driving lanes wide open across every arterial; 14 small sidewalk corner rubble piles, 6 leaning light poles, and 4 alley dumpsters add understated weathered character without obscuring downtown Bakersfield's recognizable identity.

---

## 4. Destructibles & Traversal Spec Audit

### 4.1 Destructible Landmarks & Glass (Video + Keyframe + BSP/QC Audit) — **PASS** *(1 Minor Timer Deviation)*

1. **Historic Fox Theater (`fox_r5.mp4`, `fox_r5_sheet.png`, `09_rubble_clean_b.png`):**
   - **Visual & Choreography Check:** Intact building matches StreetView `160.jpg` accurately. Shooting the 4-face belfry clock (`bako_fox_clock`, `200 HP`) bursts the clock (`00:04`), initiates a slow, readable ~8.5s coupled 2-piece clock-tower topple SE cleanly clearing the 20th St traffic signal arm (`00:05–00:10`), followed by a warm matte beige-tan dust surge (non-blinding, `00:10–00:18`), revealing a substantial organic climbable ruin (`00:19–00:23`) with tilted shattered blue-tile dome wreckage, tilted broken `FOX` marquee ramp, and zero pristine floor carpet exposed. Bottom-up staged rebuild (`00:24–00:49`, `25 s`) restores stagehouse -> auditorium -> facades -> marquee -> lower tower -> upper tower with golden welding sparks and bell chime. Zero floating rooftop props during collapse (`Bako_HideRoofProps` verified visually).
   - **Minor Defect (Spec Mismatch — Rubble Timer):** `source/qc_combat_decomp/bako_destruct_defs.qc:20` sets `autocvar_bako_fox_rubble_t = 150` (**2.5 minutes**), exceeding the 1–2 minute climbable rubble requirement by 30 seconds (Padre and Sign are both `120 s` = 2 min).

2. **The Padre Hotel (`padre_r4.mp4`, `padre_r4_sheet.png`, `12_rubble_aftermath.png`):**
   - **Visual & Choreography Check:** High durability (`autocvar_bako_padre_hp = 2600`) shows clear 75% / 50% / 25% damage milestones (`00:02–00:07`) with dark-grey outer window smoke plumes and clean top-right corner HUD (zero minimap overlap). Collapse triggers 1F–3F perimeter charge pops (`00:08–00:10`) into a slow ~11–12s coherent inward V-collapse / controlled demolition (`00:10–00:19`) with solid interior backing (zero hollow zebra slits, zero hovering crown) and billowing warm tan dust clouds (non-blinding). Three waves of dark concrete boulders visibly roll and bounce down 18th St & H St (`00:15–00:26`); `bako_destruct.qc` `Bako_BounceTarget` (`L750–802`) launches players (`kick_h 380–640, kick_z 340–400`) and vehicles + triggers `Bako_SafeShake` landing quakes (`L2870, L2932, L2941`). Clears (`00:27–00:35`) to an asymmetric, jagged 2-story climbable concrete ruin (`120 s` = 2 min) with tilted floor slabs, exposed steel girders, and tilted red `THE PADRE` rooftop sign fragment. Zero floating rooftop props.

3. **The Bakersfield Sign (`sign_r3.mp4`, `sign_r3_sheet.png`, `12_fallen_sweep.png`):**
   - **Visual & Choreography Check:** Intact sign (`380 HP`) matches real StreetView `071.jpg` with crisp right-reading `BAKERSFIELD` on both faces. Pier hits trigger Plane-A fracture (`00:04`) -> smooth accelerating north topple (`00:04–00:07`, `4.2 s`) -> street slam with elastic rebound & landing quake (`00:07–00:08`) -> full-width warm tan dust surge (`00:08–00:14`) -> clears cleanly (`00:15–00:16`) to exact-pose fallen wreckage (`120 s` = 2 min) with right-reading `BAKERSFIELD` lying across H St and 6-segment invisible parabolic `clip` ramps for walk/go-kart launch over the arch.

4. **Shatterable Glass (`glass_r3.mp4`, `glass_r3_sheet.png` + BSP Hull-0 Audit):**
   - **Visual & Distribution Check:** `52` `func_breakable` bays compiled in `maps/bakersfieldish.bsp`, all standardized to `style=3, health=15, alpha=0.52, wait=120`, spanning **6 buildings/blocks**: Dagny's Coffee/James Bldg (`18`), Golden West Casino (`12`), Padre Hotel 1F (`10`), Nile Theater + 19th St block (`6`), 1818 H St / Parking Garage corner (`4`), and Great Castle (`2`). `glass_r3.mp4` confirms crisp semi-translucent shards, cool sparkle, zero blinding flash, and clean walk-through into Padre's checkered 1F lobby.
   - **Minor Notes:**
     - Larry's Warehouse has **0** compiled `func_breakable` glass panes (`bk_glass` occurs `0` times in `bakersfieldish.map`; the 1 pane emitted by `merged_landmarks.py` was filtered out during `post_apoc_and_traversal._upgrade_and_add_glass`).
     - Hull-0 testing of all 52 panes confirmed 0 solid-wall-backed fake windows; 5 Golden West Casino bays (`NE storefront` ×2, `Rotunda` ×3) retain narrow `0.2–0.4 ft` center aluminum mullions (`gwc_dark`) inside their otherwise hollow openings (shoot-through is clean; mullions reflect real framing).

---

### 4.2 Traversal, Spawns & Creative Touches Audit — **FAIL**

#### What Passed
- **Go-Kart near EVERY spawn:** **36 / 36 spawns (100% — 1 `info_player_start` + 35 `info_player_deathmatch`)** have a paired `misc_gokart_1..6` within **`11.0–11.5 ft`** (`132–138 u`, median `11.0 ft`).
- **Chained Cross-Map Super Jump Pad (`info_skypad`) Loop:** All **10** `info_skypad` entities (6-landmark closed rooftop loop: `Padre Roof -> Fox Roof -> Larry's Roof -> Golden West Roof -> Great Castle Roof -> Parking Garage L6 Roof -> Padre Roof`, plus 4 street feeders) chain at **`0.00 ft`** destination-to-next-pad error, have **`0` mid-air building collisions**, and peak at `242–325 ft` (`275–358 ft` below the 600-ft sky ceiling).
- **Jetpacks:** **13 `item_jetpack`** pickups placed across high rooftops (Padre 8F, Fox Roof, Garage L6, Golden West, Larry's B76 & B45, Great Castle Watchtower) and far perimeter corners (`21st & G`, `18th & G`, `18th & Chester`, `H St Sign Plaza`).
- **Working Creative Sky-Bridges & Bonus Touches:** Sky-Bridge #1 (Nile Roof `35.5 ft` -> deck `36.92 ft` -> Tevis Roof `36.83 ft`) and Sky-Bridge #2 (Dagny's Roof `28.0 ft` -> deck `28.92 ft` -> sloped ramp down to Larry's B45 Roof `17.0 ft`) connect cleanly; 3 Eric Cannons and 5 bonus vehicles (`2× johnbird`, `rocketrider`, `van`, `gtcar`) are placed.

#### Verified Blocking & Non-Blocking Defects Found

##### [CRITICAL] Defect 1 — Three Deathmatch Spawns Co-Located (`0.00 ft`) Inside `info_skypad` Triggers
`skypad.qc:603` gives every `info_skypad` a `SOLID_TRIGGER` box of `'-40 -40 -26'` to `'40 40 36'` (`±3.33 ft` horizontally) bound to `SkyPad_Touch`. In compiled `maps/bakersfieldish.bsp`, three `info_player_deathmatch` spawns sit **dead center** inside rooftop `info_skypad` triggers (caused by `post_apoc_and_traversal.py` reusing exact `gw_roof`, `lw_roof`, and `gc_roof` anchors for both `spawn_candidates` and `loop_defs`):
1. **Golden West Roof:** `info_player_deathmatch` at `D(622.0, 62.0, 18.2)` vs `info_skypad` (`Great Castle Roof`) at `D(622.0, 62.0, 18.2)` — **`dxy = 0.00 ft, dz = 0.08 ft`** (`1 u`).
2. **Larry's Warehouse Roof:** `info_player_deathmatch` at `D(220.0, 82.0, 19.2)` vs `info_skypad` (`Golden West Casino Roof`) at `D(220.0, 82.0, 19.2)` — **`dxy = 0.00 ft, dz = 0.08 ft`** (`1 u`).
3. **Great Castle Roof:** `info_player_deathmatch` at `D(352.0, -242.0, 18.0)` vs `info_skypad` (`Parking Garage L6 Roof`) at `D(352.0, -242.0, 17.9)` — **`dxy = 0.00 ft, dz = 0.08 ft`** (`1 u`).

**Impact:** Players/bots spawning at any of these 3 spots are instantaneously launched involuntarily across the map into the chained rooftop SkyPad loop.
**Fix:** Offset those 3 rooftop spawns (and re-run go-kart pairing) at least `16–24 ft` away from the `info_skypad` node on each roof.

---

##### [CRITICAL] Defect 2 — Two Street-to-Garage `trigger_push` Jump Pads Slam Into the Parking Garage Exterior Walls
Exact ballistic simulation (`g = 800 u/s²`) of all 12 `trigger_push` entities in compiled `maps/bakersfieldish.bsp` against Hull-0 worldspawn geometry shows **2 of 12 regular jump pads fail to clear the Parking Garage walls**:
1. **`18th St -> Garage L6 Roof`** at `D(292.0, -788.0, 2.8)` (`angles "-81.2 90.0 0"`, `speed 116.9`, `v = (0, +179, +1155) u/s`): Pad sits only `11.2 ft` south of the Garage south facade (`Y=-776.8`, top of L6 parapet `Z=58.17 ft`). On ascent at `t = 0.75 s`, the trajectory strikes the solid Garage south wall at **`D(292.0, -776.8, 56.3)`** (`1.9 ft` below the parapet top) and drops back onto 18th Street.
2. **`Eye St -> Garage L6 Roof`** at `D(430.0, -736.0, 2.8)` (`angles "-72.2 190.5 0"`, `speed 121.3`, `v = (-365, -68, +1155) u/s`): Pad sits only `15.2 ft` east of the Garage east facade (`X=414.8`). On ascent at `t = 0.50 s`, the trajectory slams squarely into the 4F/5F Garage exterior wall at **`D(414.8, -738.8, 42.6)`** — **`15.5 ft` below the `58.17 ft` L6 parapet!**

**Fix:** Either raise `apex_extra_ft` (e.g. `34–42 ft` so the arc clears `Z > 60 ft` before crossing the facade plane) or move the launch pads further outward from the Garage walls and verify every ballistic arc clears worldspawn via `dt_hull.World`.

---

##### [MODERATE] Defect 3 — Three Creative Rubble Stunt Ramps & One Rooftop Sniper Catwalk Are Obstructed or Dead-Ended
Hull-0 cross-section verification of the 3 rubble stunt ramps and 3 sky-bridges/catwalks in `post_apoc_and_traversal.py:353-378` revealed **4 of 6** have physical geometry defects:
1. **Ramp #5b (`Wall St -> 1818 H St / Garage L2`, `X=164..180, Y=-664..-640, Z=9.5..0.9`):** The post-apocalyptic steel dumpster placed by `post_apoc_and_traversal.py:342` (`X=166..173, Y=-648..-643.5, Z=0.5..4.6`) sits **directly inside the middle of the ramp**, blocking the driving line with a solid `4.6 ft` vertical wall; furthermore, the ramp top at `Y=-664, Z=9.5 ft` terminates in front of the `1818 H St` overhang wall (`Y=-668, Z=12..15.67 ft`), not Garage L2.
2. **Ramp #5a (`18th St -> Garage SW Corner`, `X=160..204, Y=-776..-760, Z=1.0..11.4`):** Existing street hedge/tree/pole brushes (`ds_hedge`, `ds_bark`, `ds_pole` at `Z=6.2..13.2 ft`) protrude through the ramp surface across `X=160..180`, and the ramp crest at `X=204, Z=11.4 ft` slams directly into a **solid `24 ft`-tall concrete Garage column (`Z=1..23 ft`)**.
3. **Ramp #5c (`Fox West Alley`, `X=-67.5..-50.0, Y=12..28, Z=0.9..8.5`):** Slopes **east** (`+X`) into Fox Theater's solid 58-ft-tall blank west auditorium wall (`X=-47.8`, zero window/ledge/roof at `Z=8.5 ft`). The low 15-ft warehouse roof sits on the **west** side of the alley (`X <= -70`), indicating the ramp slope direction was inverted.
4. **Catwalk #3 (`Garage L6 North Overlook -> Wall St Sniper Balcony`, `X=295..325, Y=-668.5..-658, Z=54.4`):** Between Garage L6 deck (`Z=54.0 ft`, `Y <= -672`) and the balcony (`Y = -668.5..-658`), the intact Garage L6 north concrete parapet (`Y = -670.5..-669.5`) rises to **`Z = 58.17 ft`** (`50 Quake units` above the deck) — taller than standard Quake jump height (`~45.5 u`), trapping walking players from stepping onto the balcony without a jetpack/rocket-jump.

**Fix:** Remove/relocate the Wall St dumpster; clear hedges/poles on Ramp #5a and aim it into an open L2 bay (or relocate); flip Ramp #5c to slope west onto the low warehouse roof; add a short 2-step stair/ramp over the Garage L6 north parapet onto Catwalk #3.

---

##### [MODERATE] Defect 4 — `item_jetpack` and `misc_vehicle_johnbird` Co-Located on Parking Garage L6 Roof
In compiled `maps/bakersfieldish.bsp`:
- `item_jetpack` at `D(355.0, -748.0, 56.2)`
- `misc_vehicle_johnbird` at `D(355.0, -748.0, 55.5)`
- Separation: **`dxy = 0.00 ft, dz = 0.67 ft` (`8 u`)** (both hardcoded to `(355.0, -748.0, 54.0)` in `post_apoc_and_traversal.py:899,940`).

**Fix:** Separate the Garage L6 jetpack and Winged John Bird by at least `25–40 ft` on the expansive L6 roof deck.

---

##### [MINOR] Defect 5 — Spec Polish Items
1. **Fox Theater rubble duration (`bako_destruct_defs.qc:20`):** `autocvar_bako_fox_rubble_t = 150` (`2.5 min`) exceeds the 1–2 min climbable rubble spec; set to `120` (or `90–120`) to match Padre (`120 s`) and Sign (`120 s`).
2. **Larry's Warehouse shatterable glass:** `0` compiled `func_breakable` panes in `LW-A` because the single `bk_glass` door transom pane was dropped during post-apoc glass filtering; restore `2–4` real cut-out glass bays in `LW-A` (e.g., Unit 120A & 130A storefront windows) if Larry's should participate in glass shattering alongside Padre, Dagny's, Golden West, Great Castle, Nile, and 1818 H St.

---

## Conclusion
`maps/bakersfieldish.bsp` is remarkably faithful to real downtown Bakersfield and `maps/bakersfielddowntown.bsp`, integrates all 4 merged landmarks with zero mirrored signs and zero building collisions, nails the light-handed post-apocalyptic aesthetic + 600-ft high skybox, and delivers genuinely cinematic, non-blinding destructible landmarks. Fixing the **4 verified traversal/geometry defects** (3 spawn-in-SkyPad collisions, 2 wall-slamming Garage jump pads, 3 obstructed ramps + parapet-blocked Catwalk #3, and the Garage L6 jetpack/John Bird overlap) plus trimming Fox's rubble timer from `150 s` to `120 s` will turn this into a clean **PASS**.
