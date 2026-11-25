# Bakersfield-ish (`maps/bakersfieldish.bsp`) — Independent Final Accuracy Audit #2

**Auditor:** `audit-v2-2` (Fresh Accuracy Auditor #2 of 4 — Independent Final Verification)  
**Target Build:** `maps/bakersfieldish.bsp` (`40,851,944 B`, `2026-11-25 17:42:46`, `SHA256: f2089fe1599e704d9cd01543705a1488b803329f6b7b915baf18162f4f1b8e47`)  
**Methodology:** 100% independent verification — zero prior build history, zero prior audit reports read, zero live engine runs (owned by Auditor #4). All findings are independently verified directly against the compiled binary BSP2 clipnodes/geometry/entities (`maps/bakersfieldish.bsp` vs `maps/bakersfielddowntown.bsp`), raw `.map` / Python builder / QC sources, real-world Google Maps / StreetView / OSM references, and captured visual frames.

---

## Executive Verdict: **FAIL**

`maps/bakersfieldish.bsp` is an **exceptionally strong map** on architectural faithfulness, downtown layout preservation, signage integrity, post-apocalyptic restraint, high skybox, cinematic destructibles, hollow shatterable glass, and the chained 11-pad SkyPad loop — **all of which PASS cleanly**.

However, direct binary BSP2 Hull-1 / Hull-2 collision auditing of the current `17:42:46` compiled BSP uncovered **5 concrete, reproducible traversal & placement defects** (1 Blocker, 1 High, 1 Medium-High, 1 Medium, 1 Low-Medium) that violate the explicit audit requirements (specifically *"no dumpsters/parapets/walls blocking ramps or catwalks"* and clean spawns/go-karts/jetpacks/jump pads):

| # | Severity | Defect Summary (Verified in `17:42:46` `maps/bakersfieldish.bsp`) |
|---|---|---|
| **1** | **BLOCKER** | **Sky-Bridge #5e (`Dagny's Roof -> Larry's B45 Roof`) is completely walk-blocked** by a legacy invisible 4-ft `clip` wall (`dagnys.py:808`, `Z=27.83..31.83 ft`, `+46.0 u` step) running right across the bridge's southern mouth (`Y=-39.17..-33.17`). |
| **2** | **HIGH** | **Great Castle Roof Spawn #28, Go-Kart #28, and Watchtower Jetpack are misplaced on a parapet, HVAC unit, and decorative spire** (`_rest_floor_ft` snagged edges): Spawn #28 hovers **+63 u (5.25 ft)** in mid-air behind the 5-ft roof divider parapet; Kart #28 hovers **+46 u (3.83 ft)** overhanging an HVAC cooler; Watchtower Jetpack hovers **+108 u (9.0 ft)** on top of the decorative crimson spire (unreachable on foot from the `18.5 ft` deck). |
| **3** | **MEDIUM-HIGH** | **Larry's Warehouse Unit 130A Go-Kart #23 (`misc_gokart_6`) spawns +39 u (3.25 ft) in mid-air directly clipping a solid 3.33-ft traffic cone** (`bk_cone` inside Hull-2 footprint), with a 4.5-ft wood crate obstructing the direct approach from Spawn #23. |
| **4** | **MEDIUM** | **Regular Jump Pad #04 (`18th St -> Garage L6 Roof`) has a 26-ft solid lamp pole `5.75 ft` directly in front of its NE launch edge** (`ds_pole` at `D(294.0, -795.0)`): passes builder's `±20 u` 9-pt grid (`9/9`), but **fails `23/25` on `±24 u`** (and slams players entering from the NE corner of the `±33.6 u` trigger into the pole). |
| **5** | **LOW-MEDIUM** | **Ramp #5a (`Nile East Lot -> H St Eastbound`) has only `5.0 ft` (`60 u`) run-up behind it** before Front Porch Music's solid east wall (`X=11.0 ft`) — shorter than a Go-Kart (`~64 u`), preventing a straight eastbound approach. |

Additionally, **1 packaging hygiene note** (`zz_bakersfieldish.pk3` and `minimap_bakersfieldish.png` are ~38 minutes older than the `17:42:46` BSP and still depict the removed 19th St Nile sky-bridge) and **2 minor pickup-perch notes** (Golden West Roof Mega Health perched on an HVAC edge; Padre 1F Rocket Launcher over the basement stairwell opening) are documented in Section 6.

### Scorecard by Audit Pillar

| Audit Pillar | Status | Notes |
|---|---|---|
| **1. Faithfulness to Original Bakersfield Downtown & Real Downtown Bakersfield** | **PASS** | Padre (96.8%), Garage (99.3%), Fox (97.5%), Nile/Dagny's/Sandrini's/Jerry's/PG&E Tower (99.7–100.0%) preserved verbatim on real OSM footprints; Padre↔Fox H St sightline intact (`569.3 ft`); only 4 replaceable slots swapped. |
| **2. Cohesiveness of All 4 Merged Landmarks** | **PASS** | Orientation matches real StreetView/showcases; **192/192** vertical sign faces & **40/40** rendered text panels **0 mirrored / 0 upside-down**; sidewalks flush (`max_adj_step <= 0.42 ft`); 19th St floating beam removed; forklifts/props/pylons clean. |
| **3. Post-Apocalyptic Look & Feel + High Skybox** | **PASS** | Binary BSP sky ceiling **600.0 ft (`7200 u`)** vs `280.0 ft` (`3360 u`) in `bakersfielddowntown.bsp` (2.14× taller); warm golden-dust lighting & 43 restrained street dressing props — unmistakably recognizable downtown, not a wasteland. |
| **4a. Destructibles & Shatterable Glass** | **PASS** | Fox (~8.6s collapse, clears 20th St signal arm, 115s climbable rubble, 25s slow rebuild), Padre (~12s inward V-collapse, 75/50/25% smoke cues + HUD toast, 115s climbable ruin), Sign (clean `Z=5.0 ft` shear, slow bounce, 4/4 continuous Hull-1 rampable rubble, 115s), Glass (**56/56** hollow cut-outs, `0/56` solid-backed, 120s respawn). |
| **4b. Traversal, Spawns, Karts, Jetpacks & Jump Pads** | **FAIL** | Chained 11-pad SkyPad loop **11/11 PASS** (0 arc hits, 0 spawns in triggers, 0 overlapping vehicles/jetpacks/cannons); Ramps #5b/#5c & Catwalk #5f **PASS**; **FAILS** on Defects #1–#5 (invisible `clip` wall blocking Sky-Bridge #5e, Great Castle roof misplacements, Unit 130A Kart #23 traffic-cone overlap, Jump Pad #04 lamp pole, Ramp #5a run-up). |

---

## 0. Verified Build Provenance & Evidence Generated

| Artifact | Size | Last Modified | SHA256 (prefix) | Notes |
|---|---|---|---|---|
| `maps/bakersfieldish.bsp` | 40,851,944 B | `2026-11-25 17:42:46` | `f2089fe1599e704d` | Matches `source/downtown/out/bakersfieldish.bsp` bit-for-bit. **1,567 entities, 89 bmodels.** |
| `maps/bakersfieldish.lit` | 14,382,632 B | `2026-11-25 17:42:45` | `1f068c2ea91442ab` | Matching lightmap build (`bakersfieldish-light.log`). |
| `maps/bakersfielddowntown.bsp` | 37,081,900 B | `2026-11-24 12:21:02` | `c361b24f13af93d6` | Reference baseline for quantitative heightmap diff. |
| `progs.dat` / `csprogs.dat` | 3,772,034 B / 608,842 B | `2026-11-25 18:15:40` | `d67f9477...` / `07df5d3f...` | Built with `bako_destruct.qc` & `bako_destruct_defs.qc`. |
| `zz_bakersfieldish.pk3` | 440,516 B | `2026-11-25 17:04:43` | `32fb0d60e3442fd6` | **38 min older than BSP** (contains stale `minimap_bakersfieldish.png`). |
| `source/mm_tools/bakersfieldish_assets/minimap_bakersfieldish.png` | 44,959 B | `2026-11-25 17:03:51` | `48eed443873327fb` | Stale pre-17:42 minimap (still renders removed 19th St sky-bridge). |

> **Timestamp Integrity Note:** Existing map overview screenshots in `docs/bakersfieldish_audit4_shots/` (`b01`–`b20`, `dt01`–`dt02`) were captured between `15:16` and `16:39`, ~1–2 hours before the `17:42:46` BSP rebuild. Accordingly, screenshots were used for aesthetic/architectural/destructible visual verification, while **every single geometric, collision, skybox, signage, spawn, kart, jetpack, ramp, catwalk, and jump-pad check was independently re-measured directly on the `17:42:46` `maps/bakersfieldish.bsp` binary**.

**Independent Visual Overlays Generated & Inspected:**
1. [audit_v2_2_planimetric_compare.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_planimetric_compare.png) — 3-panel 1 ft/px binary heightmap comparison (`bakersfielddowntown.bsp` vs `bakersfieldish.bsp` vs exact pixel diff + real OSM building footprints from `source/downtown/refs/osm_ft.json`).
2. [audit_v2_2_signage_sheet.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_signage_sheet.png) — 40 outside-viewed rendered sign faces extracted directly from compiled BSP2 UV coordinates and true polygon winding normals (`windN = (v0 - v1) x (v2 - v1)`).
3. [audit_v2_2_traversal_map.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_traversal_map.png) — Full planimetric map of all 36 spawns, 36 paired go-karts, 13 jetpacks, 12 regular jump pads, and the 11-pad chained SkyPad loop.
4. [audit_v2_2_defects_detail.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_defects_detail.png) — 2×2 exact binary BSP2 cross-section & planimetric evidence diagram of Verified Defects #1–#5.

---

## Pillar 1: Faithfulness to Original Bakersfield Downtown & Real Downtown Bakersfield — **PASS**

### 1.1 Quantitative Heightmap Fidelity (`maps/bakersfielddowntown.bsp` vs `maps/bakersfieldish.bsp`)
A `1 px = 1 ft` binary Hull-0 rooftop elevation scan across the full downtown region (`X = -340..950 ft, Y = -900..275 ft`, world shift `(+835, -285) ft`, `12 u/ft`) confirms that **all preserved civic landmarks retain their exact footprint, elevation, massing, and OSM alignment**, while **only the 4 designated replaceable slots were swapped**:

| Landmark / Preserved Building | `bakersfielddowntown` Max Z | `bakersfieldish` Max Z | Height Match (`|ΔZ| < 2 ft`) | Notes |
|---|---:|---:|---:|---|
| **Padre Hotel** (`18th & H`) | `122.3 ft` | `122.3 ft` | **96.8%** | Minor `3.2%` diff is solely the 2F Prairie Fire / rooftop traversal dressing & destructible bmodel seam. |
| **18th & Eye Parking Garage** (across from Padre) | `72.0 ft` | `72.0 ft` | **99.3%** | 6-deck helical ramp structure, stair tower, and L6 deck preserved identically. |
| **Fox Theater** (`20th & H`) | `116.5 ft` | `116.5 ft` | **97.5%** | Iconic art-deco clock tower, curved marquee, and auditorium preserved identically. |
| **Nile Theater** (`19th St`) | Preserved | Preserved | **99.8%** | Intact facade, blade sign, and roofline; earlier 19th St sky-bridge cleanly removed. |
| **Dagny's Coffee** (`20th & Eye`) | Preserved | Preserved | **99.7%** | Corner windows, exterior white steel stair, and roofline intact. |
| **Sandrini's** (`19th & Eye`) | Preserved | Preserved | **99.9%** | Exact original geometry preserved. |
| **Jerry's Pizza** (`Chester Ave`) | Preserved | Preserved | **100.0%** | Byte-identical elevation profile. |
| **PG&E Radio Tower** | `126.5 ft` | `126.5 ft` | **99.9%** | Full lattice mast preserved. |

**Only 4 Replaceable Slots Modified** (visually confirmed on the right-hand diff panel of [audit_v2_2_planimetric_compare.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_planimetric_compare.png)):
1. **`GW-A` (Golden West Casino):** `X = 489..783, Y = -98..185 ft` (NE empty/surface-lot & generic block on 20th–21st / Eye–Chester).
2. **`LW-A` (Larry's Warehouse):** `X = 146..430, Y = -23..185 ft` (north of Dagny's / east of Fox between H & Eye on 21st St).
3. **`GC-A` (The Great Castle):** `X = 274..431, Y = -294..-169 ft` (replaceable lot west of Eye St between 19th & 20th, cleanly preserving Dagny's to the north and Sandrini's across Eye St to the east).
4. **`S1` (The Bakersfield Sign):** `X = 55..165, Y = -578..-552 ft` (spanning H St just north of 19th St — zero building demolition, pure street-spanning hero portal).

### 1.2 Real-World Reference & Padre↔Fox Visual Corridor Verification
Cross-checked against Google Maps z17 hybrid satellite ([003.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/refs/downtown-bakersfield/003.jpg)), real StreetView photos ([padre-hotel/011.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/refs/padre-hotel/011.jpg), [padre-garage/012.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/refs/padre-garage/012.jpg), [fox-theater/019.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/refs/fox-theater/019.jpg), [fox-theater/024.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/refs/fox-theater/024.jpg), [fox_ref/gal_001.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/mm_tools/fox_ref/gal_001.jpg)), the HTML downtown showcase ([bakersfielddowntown_viewer_showcase.html](file:///G:/Quake/Combat/BakersfieldQuake/docs/bakersfielddowntown_viewer_showcase.html)), and in-game views (`b01`–`b04`, `dt01`–`dt02`):
- **Padre↔Fox H St Corridor:** Padre east facade sits at `X = 81.0 ft` (`Y = -785..-665.8 ft`) and Fox east facade sits at `X = 82.0 ft` (`Y = -96.5..90 ft`) — a **1.0 ft exact street-wall alignment** across the **`569.3 ft` H St vista**. Framing the iconic Bakersfield Sign (`Y = -565 ft`, `arch crown = 30.6 ft`) squarely inside the H St corridor between Padre and Fox preserves the real downtown sightline while giving an unmistakable hero-spawn vista (`info_player_start` looking north up H St through the Bakersfield Sign straight toward the Fox clock tower).
- **Padre Hotel:** Terracotta brick 8-story tower, scalloped white cornice crown, ground-floor arched arcade, red `"THE PADRE"` canopy, and 2F Prairie Fire terrace faithfully match `padre-hotel/011.jpg`.
- **Parking Garage Across from Padre:** Positioned directly east across H St (`X = 152..424, Y = -785..-668 ft`), concrete spandrel tiers, horizontal light bands, and recessed corner stairwell match `padre-garage/012.jpg`.
- **Fox Theater:** Streamline Moderne stepped cream-stucco tower, vertical `"FOX"` fins, gold/red marquee on the 20th & H corner, and adjacent 20th St traffic signal mast arm faithfully match `fox-theater/019.jpg`, `024.jpg`, and `gal_001.jpg`.

---

## Pillar 2: Cohesiveness of All 4 Merged Landmarks — **PASS**

### 2.1 Orientation & Architectural Integration
Checked against real StreetView / showcase references ([golden_west_gallery/035.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/mm_tools/ref_sources/golden_west_gallery/035.jpg), [goldenwest_showcase.html](file:///G:/Quake/Combat/BakersfieldQuake/source/mm_tools/goldenwest/out/goldenwest_showcase.html), [sv-front-118e21st-pano](file:///G:/Quake/Combat/BakersfieldQuake/source/mm_tools/ref_sources/streetview_gallery1/sv-front-118e21st-pano-zMs_Qgogu-KGknvva4xnig-yaw45.jpg), [downtown-bakersfield/071.jpg](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/refs/downtown-bakersfield/071.jpg), and `golden_west_landmarks/part_A.md` & `part_D.md`):
- **Golden West Casino (`GW-A`):** Fronts south onto 20th St with its distinctive burgundy/tan circular rotunda, courtyard horse statue (`gw_horse.md3`), interior poker room & golden Buddha (`gw_buddha.md3`), blackjack/lounge neon, and tall roadside marquee pylon at the SE corner (`D(742, -68)`). Rooftop props/entities were cleanly relocated onto the flat north deck (`Z = 16.25 ft, Y = 91..127`).
- **The Great Castle (`GC-A`):** Authentic stucco Chinese restaurant pavilion with stepped battlements, crimson crow's-nest watchtower, north entrance facing 20th St, east plaza & illuminated monument pylon facing Eye St (`D(416, -212)`), and playable interior dining hall. (Note: roof spawn/kart/jetpack placement bugs are tracked under Pillar 4 / Defect #2; the building architecture itself is clean and cohesive.)
- **Larry's Warehouse (`LW-A`):** Authentic 21st St industrial courtyard complex (`118 E 21st St` massing) with Unit 130A LAN room, Megaman office, corrugated warehouse hall, `"LARRY'S WAREHOUSE"` & `"MEGAMAN"` / `"ORTIZ"` / `"BATERIAS"` signage, street-facing purple pylon (`Y = 2.3..2.9`, `15 ft W / 11 ft N` clear of the street utility pole at `D(306, -9)`), grounded `mm_rig.md3`, and orange/blue forklifts verified **`21.4 ft`** and **`22.0 ft`** clear of all `sr_rack_*` pallet racks.
- **The Bakersfield Sign (`S1`):** Spans H St cleanly from west sidewalk tower (`X = 66`) to east sidewalk tower (`X = 154`) at `Y = -565 ft`, arch crown `30.6 ft`, faithfully replicating the historic neon Bakersfield Arch (`071.jpg`) with red/yellow arched `"BAKERSFIELD"` letters, curved upper scroll banner, and twin steel lattice pylons.

### 2.2 Signage Readability & Non-Mirroring Audit (**100% PASS**)
Every vertical signage polygon in `maps/bakersfieldish.bsp` across `GW-A`, `GC-A`, `LW-A`, `S1`, Padre, and Fox (**192 vertical sign faces total**) was audited programmatically using **true compiled BSP2 vertex-winding outward normals** (`windN = (v0 - v1) × (v2 - v1)`, avoiding `qbsp` `dface_t.side` flip artifacts on `_super_detail` / `func_detail_illusionary` brushes) and verified visually by rendering 40 representative outside-viewed text faces onto [audit_v2_2_signage_sheet.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_signage_sheet.png):
- **0 mirrored faces, 0 upside-down faces** across all inspected textures:
  - Bakersfield Sign: `bk5_bsign`, `bk_bupper` (both north and south faces right-reading).
  - Golden West Casino: `gwc_pyltop`, `gwc_pylled`, `{gwc_bjneon`, `{gwc_lgneon`, `gwc_menu` (all crisp & upright).
  - The Great Castle: `gwc_gcwest` (`城 堡`), `gwc_gcpylon`, `gwc_gcplaque`, `gwc_gcopen` (`OPEN`), `gwc_gcrest`, `gwc_gc410` (all right-reading; cross-confirmed in `b11_castle_entrance_sign.png`).
  - Larry's Warehouse: `bk3_larry`, `bk3_pylon`, `bk5_lsign5`, `bk5_ortiz`, `bk_baterias`, `bk_blansign`, `dan_4am`, `dan_shaaa` (all right-reading).
  - Preserved landmarks: `pad_canopy`, `dtl_mqfront` (`FOX`) (all right-reading).

### 2.3 Sidewalk Continuity & Floating-Geometry Check (**PASS**)
- **Sidewalk Continuity:** Perimeter Hull-0 elevation sweeps around `GW-A`, `LW-A`, and `GC-A` confirm continuous curbs/sidewalks at `Z = 0.50..0.75 ft` with `max_adj_step <= 0.42 ft` (`<= 5 u`, effortlessly steppable well below Quake's `18 u` step limit).
- **19th St Floating Beam Removed:** Probed the entire overhead corridor over Front Porch Music / 19th St (`X = -100..100, Y = -500..-450, Z = 16..40 ft`) in the `17:42:46` BSP: **0 solid overhead hits** (confirmed completely cleaned out).

---

## Pillar 3: Post-Apocalyptic Look & Feel + High Skybox — **PASS**

- **Genuinely High Skybox:** Binary inspection of `maps/bakersfieldish.bsp` confirms `sky_z_u = (0.0, 7200.0)` (**`600.0 ft`** ceiling) vs `maps/bakersfielddowntown.bsp` `(0.0, 3360.0)` (`280.0 ft`) — **2.14× taller**, giving generous overhead room above the `122.3 ft` Padre Hotel, `126.5 ft` PG&E Tower, and `~325 ft` SkyPad parabolic apexes (`2900–3900 u`), with clean blue sky overhead visually confirmed in `b20_high_skybox_lookup.png`.
- **Light-Handed Post-Apocalyptic Aesthetic (NOT a Wasteland):**
  - Worldspawn lighting & atmosphere use restrained golden-hour dust warmth (`_sunlight = 235`, `_sunlight_color = "1 0.88 0.72"`, `fog = "0.22 0.56 0.49 0.41 1 4200 7600 2200 750"`, `_dirtscale = 0.38`, `post_light_scale = 0.72`), keeping streets sunny, crisp, and legible rather than grimdark brown/grey.
  - Street dressing totals **43 restrained props** (concrete jersey barriers, small rubble piles, tilted street poles, occasional dumpsters/crates) concentrated along curbs and medians without cluttering lanes or obscuring architectural facades. Inspected frames (`b01`–`b20`) clearly read as an immediately recognizable Bakersfield downtown with light post-apocalyptic texture.

---

## Pillar 4: Destructibles & Traversal Visual/Layout Verification — **MIXED (Destructibles PASS / Traversal FAIL)**

### 4.1 Destructibles & Shatterable Glass — **PASS**
Visually inspected all required capture sheets and keyframes (`docs/bakersfieldish_captures/round5/fox_r5*`, `round4/padre_r4*`, `round3/sign_r3*`, `round3/glass_r3*`) and cross-checked entity counts & QC timings in `source/qc_combat_decomp/bako_destruct.qc` and `bako_destruct_defs.qc`:

| Destructible | Visual & QC Verification Result |
|---|---|
| **Fox Theater** (`round5/fox_r5_sheet.png`, `05_tower_slam.png`, `10_rubble_clean_c.png`) | **PASS.** Coupled 2-piece clock-tower fall (~8.6 s cinematic progression) cleanly clears the 20th St traffic signal mast arm without snagging; warm tan dust surge is atmospheric and **non-blinding**; leaves climbable organic concrete/brick rubble (`autocvar_bako_fox_rubble_t = 115 s`); executes slow, smooth bottom-up upright rebuild (`autocvar_bako_fox_rebuild_t = 25 s`); rooftop pad pedestals attached into `bako_fox_piece[auditorium_roof]` so **0 floating sky props remain**. |
| **Padre Hotel** (`round4/padre_r4_sheet.png`, `07_mid_pancake.png`, `12_rubble_aftermath.png`) | **PASS.** Escalating 75% / 50% / 25% damage smoke vents with clear top-right HUD warning toast; slow ~12 s inward V-collapse with rooftop crown locked cleanly to tier4 and rolling concrete boulders; non-blinding dust plume; leaves climbable 2-story concrete ruin (`115 s`); rooftop pad pedestal attached into `bako_padre_piece[crown]` so **0 floating sky props remain**. |
| **Bakersfield Sign** (`round3/sign_r3_sheet.png`, `05_mid_topple.png`, `12_fallen_sweep.png`) | **PASS.** Clean Plane-A shear at `Z = 5.0 ft`, slow northward topple with elastic street bounce, seamless transition into `bako_sign_rubble` (`115 s`). Independent binary Hull-1 walk/drive check across `bako_sign_rubble` confirms **4/4 continuous ramp passes** (crest `3.33 ft`, smooth step-up for players and Go-Karts). |
| **Shatterable Glass** (`round3/glass_r3_sheet.png` + binary BSP) | **PASS.** All **56/56** compiled `func_breakable` glass bays independently verified against Hull-0 solids to be **genuine hollow cut-outs (`0/56` solid-backed)**; crisp translucent shards (`alpha = 0.52`), 120 s respawn. |

### 4.2 Chained Cross-Map Super Jump Pad Loop (`info_skypad`) & Entity Separation — **PASS**
Audited all **11 `info_skypad` entities** (6-roof closed loop `S1 Padre -> S2 Fox -> S3 Larry's -> S4 Golden West -> S5 Great Castle -> S6 Garage L6 -> S1 Padre` plus 5 street/plaza feeders `S7..S11`, including `#11` at Larry's purple sign) with a 400-step binary BSP2 Hull-1 parabolic arc simulator (plotted on [audit_v2_2_traversal_map.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_traversal_map.png)):
- **11/11 PASS** — **0 launch collisions, 0 mid-arc collisions, 0 landing collisions**.
- **Exact Chaining:** `chain_d = 0.0 u` across every closed-loop link; all parabolic apexes sit between **`2900–3900 u`** (`242–325 ft`), comfortably inside the `7200 u` (`600 ft`) skybox.
- **Zero Spawns Inside SkyPad Triggers:** Nearest spawn to any SkyPad across all 36 spawns is **`>= 288 u` (`24.0 ft`)** (trigger + player half-width is `56 u`).
- **Zero Overlapping Vehicles / Jetpacks / Cannons:** All pairwise distances between vehicles, jetpacks, cannons, and SkyPads exceed `120 u` (`10 ft`); Garage L6 Roof spacing verified clean (`Winged John` well separated from Garage L6 Jetpack & SkyPad #6).
- **Zero Solid-Stuck or Rubble-Trapped Spawns:** All **36/36 spawns** (`1 info_player_start + 35 info_player_deathmatch`) are free in intact BSP Hull-1 and outside collapsed `bako_*_rubble` footprints.
- **Ramps #5b, #5c & Catwalk #5f PASS:**
  - **Ramp #5b** (Wall St eastbound): continuous Hull-1 walk (`maxStep <= 14 u`), clear approach.
  - **Ramp #5c** (Fox West Alley -> Fox West Roof): continuous Hull-1 walk (`maxStep <= 14 u`), clear approach.
  - **Catwalk #5f** (Parking Garage L6 North Overlook): 2-sided ramp over parapet + both E/W wings pass continuous Hull-1 step-walk (`maxStep <= 14 u`).

### 4.3 Verified Traversal & Placement Defects — **FAIL (See Section 5)**
Despite the strong core traversal loop above, **5 concrete geometry/placement defects exist in the compiled `17:42:46` `maps/bakersfieldish.bsp`**, illustrated in [audit_v2_2_defects_detail.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_defects_detail.png) and detailed in Section 5 below.

---

## 5. Detailed Defect Register (Blocking Final Sign-Off)

### Defect #1 [BLOCKER]: Invisible 4-ft `clip` Wall Blocks the Entire Southern Mouth of Sky-Bridge #5e (`Dagny's Roof -> Larry's Warehouse B45 Roof`)
- **Compiled BSP Evidence:**
  - Sky-Bridge #5e deck spans `D X=[340.0, 352.0], Y=[-32.0, -4.0], Z=[28.0, 28.92] ft` (steel railings at `X=339.6..340.4` and `351.6..352.4` up to `Z=31.83 ft`), descending north onto Larry's B45 roof (`Z=17.5 ft`).
  - Just **`1.17 ft` (`14 u`) south of the bridge entrance**, a compiled `func_detail` **`clip` brush** spans `D X=[294.00, 356.00], Y=[-39.17, -33.17], Z=[27.83, 31.83] ft` — sealing the ENTIRE `12 ft`-wide bridge mouth across `X=340..352`.
  - Step height from Dagny's Roof (`Z=28.00 ft`) onto the top of the `clip` wall (`31.83 ft`) is **`3.83 ft = 46.0 u`** — exceeding Quake's `STEPSIZE = 18 u` AND exceeding Quake's maximum standing jump apex (`270² / (2 × 800) = 45.56 u`). Going south from the bridge deck (`28.92 ft`), it presents a **`35.0 u`** invisible wall.
  - **1-ft grid BSP2 Hull-1 flood-fill** from Dagny's Roof center `D(360, -56, 28.0)` confirms: **`WALK (step <= 18u): reached_bridge = False` (`max_Y = -41`)**. Because it is a `clip` brush, it is completely invisible in-game and in screenshots.
- **Root Cause:** Legacy anti-ladder brush in [dagnys.py](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/pieces/dagnys.py#L807-L808):
  ```python
  # Keep west half of north roof parapet zone clear of auto-placed rooftop ladder ...
  ctx.box(294.0, -39.2, 27.8, 356.0, -33.2, 31.8, "clip", group="detail", solid=True)
  ```
- **Visual Evidence:** [audit_v2_2_defects_detail.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_defects_detail.png) (Panel 1, Top-Left).
- **Recommended Fix:** Trim the `clip` brush in `dagnys.py:808` (or filter it in `make_bakersfieldish.py`) so it ends at `X = 336.0` (leaving `X = 336..356` completely open for Sky-Bridge #5e), or remove it in `bakersfieldish` where auto-ladders are not placed on that parapet. Re-verify Hull-1 walk flood-fill from Dagny's Roof to Larry's B45 Roof.

---

### Defect #2 [HIGH]: Great Castle Roof Spawn #28, Go-Kart #28, and Watchtower Jetpack Snagged on Parapet / HVAC / Spire
- **Compiled BSP Evidence (3 co-located placement bugs on `GC-A` roof):**
  1. **Spawn #28 (`info_player_deathmatch`, `D(324.92, -252.58, 18.75 ft)`):** Placed **`63.0 u` (`5.25 ft`) floating in mid-air** above the `11.50 ft` west roof deck (`H1_gap = 63.0 u`, `H0_gap = 63.0 u`). Its inflated `SPAWN_HULL` (`±24 u`) snagged the top of the 5-ft roof divider parapet wall (`X=326.5..327.5, Z=12.0..16.5 ft`), ALSO leaving the player trapped on the west side of the `60 u`-tall parapet wall cut off from Great Castle's SkyPad #5 (`D(348.9, -244.6, 13.0)`).
  2. **Go-Kart #28 (`misc_gokart_5`, `D(314.42, -252.58, 17.33 ft)`):** Paired with Spawn #28; its `KART_HULL` (`±30 u`) snagged the edge of the rooftop HVAC swamp cooler (`X=315.5..320.5, Y=-257.21..-252.79, Z=12.17..15.33 ft`), spawning the kart **`46.0 u` (`3.83 ft`) high overhanging the HVAC edge** (`H1_surf = 15.33 ft`, while `H0_surf = 11.50 ft` directly under kart center).
  3. **Great Castle Watchtower Jetpack (`item_jetpack`, `D(355.08, -205.42, 29.75 ft)`):** `ITEM_HULL` caught the top rim of the decorative **27.54-ft crimson crow's-nest spire** (`X=349.83..354.17, Y=-209.17..-204.83, Z=27.29..27.54 ft`), placing the jetpack **`108 u` (`9.0 ft`) above the walkable `18.50 ft` watchtower roof deck** (`surfH1 = 27.54 ft`, `surfH0 = 18.50 ft`) — unreachable on foot from the watchtower deck!
- **Root Cause:** `_rest_floor_ft()` in [post_apoc_and_traversal.py](file:///G:/Quake/Combat/BakersfieldQuake/source/downtown/pieces/bakersfieldish/post_apoc_and_traversal.py#L1059) drops an inflated AABB (`SPAWN_HULL`, `KART_HULL`, `ITEM_HULL`) from above until *any* corner catches *any* brush, without requiring flat floor support directly under the entity's center (`abs(surf_hull - surf_point) <= 1.0 ft`).
- **Visual Evidence:** [audit_v2_2_defects_detail.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_defects_detail.png) (Panel 2, Top-Right).
- **Recommended Fix:**
  - Add a flat-floor sanity check inside `_rest_floor_ft()` / `_find_clear_spot()` requiring the point floor (`TINY_PROBE` / Hull-0 directly under `(x, y)`) to match the hull-resting surface within `<= 1.0 ft` (`12 u`).
  - Move `gc_roof_spawn_pt` east of the divider parapet onto the main `13.5 ft` deck near SkyPad #5 (e.g., `D(350..368, -260..-230)`), and nudge `gc_tower` jetpack onto the clear `18.5 ft` watchtower deck away from the spire (`X=350..354, Y=-209..-205`).

---

### Defect #3 [MEDIUM-HIGH]: Larry's Warehouse Unit 130A Go-Kart #23 (`misc_gokart_6`) Spawns +39 u High Clipping a Traffic Cone
- **Compiled BSP Evidence:**
  - **Go-Kart #23 (`misc_gokart_6`, `D(326.67, 142.33, 5.33 ft)`):** Paired with Spawn #23 (`D(338.33, 135.58, 2.33 ft)`). Its `KART_HULL` (`±30 u`) caught the top of a solid **`3.33-ft` traffic cone** (`bk_cone`, `X=325.25..325.75, Y=139.75..140.25, Z=0.0..3.33 ft`), spawning the kart **`39.0 u` (`3.25 ft`) in mid-air** above the `0.08 ft` floor (`Hull-2 = worldspawn` intersecting `Z=0.0..5.0 ft`).
  - Additionally, a `4.5-ft` solid wood crate (`X=331.58..333.58, Y=140.58..142.42`) sits right on the direct sightline between Spawn #23 and Kart #23.
- **Root Cause:** Same `_rest_floor_ft(hull=KART_HULL)` edge-snag mechanism as Defect #2; the traffic cone was treated as a supporting floor surface instead of an obstacle.
- **Visual Evidence:** [audit_v2_2_defects_detail.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_defects_detail.png) (Panel 3, Bottom-Left).
- **Recommended Fix:** Same flat-floor check (`abs(surf_hull - surf_point) <= 1.0 ft`) in `_rest_floor_ft()` will immediately reject the traffic cone and snap Kart #23 cleanly onto the open concrete floor of Unit 130A at `Z = 2.08 ft`.

---

### Defect #4 [MEDIUM]: Regular Jump Pad #04 (`18th St -> Garage L6 Roof`) Launches NE-Edge Players Into a 26-ft Lamp Pole
- **Compiled BSP Evidence:**
  - `trigger_push` #04 (`D(292.0, -804.0, 0.5)`, trigger box `X=289.17..294.83, Y=-806.83..-801.17`, `±33.6 u` wide, launching straight north `yaw = 90°`) passes the builder's `±20 u` 9-point grid (`9/9`).
  - However, a **26-ft solid street lamp pole** (`ds_pole`, `X=293.67..294.33, Y=-795.42..-794.58, Z=0.5..26.0 ft`) stands only **`5.75 ft`** directly north of the trigger's NE quadrant.
  - On our wider **`±24 u` 25-point sweep**, **11/12 regular jump pads pass `25/25`**, while **Jump Pad #04 fails `23/25`** — players triggering the NE quadrant slam directly into the lamp pole at `Z = 26–28 ft` (`fail = worldspawn` at `D(294, -795, 26)`). (On outer `±30 u` extreme corners, minor edge grazing also appears on Pads #03, #05, #07, #11, #12, whereas #04's pole sits right in the main forward launch lane even at `±24 u`.)
- **Visual Evidence:** [audit_v2_2_defects_detail.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_defects_detail.png) (Panel 4a, Bottom-Right Left).
- **Recommended Fix:** Shift Jump Pad #04 west by `6–8 ft` (from `X = 292.0` to `X = 284.0`) and widen `_test_push_9pt()` in `post_apoc_and_traversal.py:708` from `(-20, 0, +20)` to `(-28, 0, +28)` so trigger-edge entries can never clip adjacent street poles.

---

### Defect #5 [LOW-MEDIUM]: Ramp #5a (`Nile East Lot -> H St Eastbound`) Has Only 5.0 ft (`60 u`) Back-Wall Clearance
- **Compiled BSP Evidence:**
  - Ramp #5a spans `D X=[16.0, 46.0], Y=[-548.0, -534.0], Z=[0.5 -> 8.5] ft` climbing east toward H St.
  - Front Porch Music / Nile East Building's solid wall (`nl_stuc_tan`) sits at `X = 9.5..11.0 ft` directly behind the west entry mouth — leaving only **`5.0 ft` (`60 u`) of clearance**, which is shorter than a Go-Kart (`~64 u`), forcing an awkward sharp turn onto the ramp and preventing any straight eastbound vehicle jump.
- **Visual Evidence:** [audit_v2_2_defects_detail.png](file:///G:/Quake/Combat/BakersfieldQuake/docs/audit_v2_2_defects_detail.png) (Panel 4b, Bottom-Right Right).
- **Recommended Fix:** Shift Ramp #5a east by `10–14 ft` (to `X = 26..56`) or rotate it to launch north/south along the open lot apron so both foot and Go-Kart approaches have a clean run-up.

---

## 6. Minor Non-Blocking & Packaging Hygiene Notes

1. **Stale Packaged Assets (`zz_bakersfieldish.pk3` & `minimap_bakersfieldish.png`):** Both files are timestamped `17:03:51–17:04:43`, ~38 minutes older than `maps/bakersfieldish.bsp` (`17:42:46`). Visual inspection of [minimap_bakersfieldish.png](file:///G:/Quake/Combat/BakersfieldQuake/source/mm_tools/bakersfieldish_assets/minimap_bakersfieldish.png) confirms it still shows the removed 19th St Nile sky-bridge. Re-render the minimap and rebuild `zz_bakersfieldish.pk3` after fixing Defects #1–#5.
2. **Golden West Roof Mega Health (`item_health`, `D(616.0, 99.0, 22.5 ft)`):** Same `_rest_floor_ft` edge-snag placed it perched on the top rim of a rooftop HVAC unit (`surfH1 = 19.83 ft`, `surfH0 = 16.25 ft`, `3.58 ft` above the north roof deck). Fixing `_rest_floor_ft` will automatically ground it on the `16.25 ft` deck.
3. **Padre 1F Rocket Launcher (`weapon_rocketlauncher`, `D(38.0, -725.0, 6.0 ft)`):** Placed directly over the basement stairwell opening (`dropH1 = 89 u` down onto the basement steps at `-1.42 ft`). Recommend nudging ~8–10 ft onto the solid 1F lobby floor so it doesn't drop down the stairs on map load.

---

## 7. Sign-Off Criteria for Re-Audit

This map is **very close to a clean PASS** — its downtown fidelity, merged-landmark artistry, 100% readable signage, high skybox, balanced post-apocalyptic mood, cinematic destructibles, hollow shatterable glass, and 11-pad SkyPad loop are all genuinely impressive. Resolving the **5 items in Section 5** (trimming `dagnys.py:808`'s `clip` brush, adding a flat-floor center check to `_rest_floor_ft()` + nudging Great Castle roof spawn/jetpack, shifting Jump Pad #04 west of the lamp pole, and giving Ramp #5a proper run-up) plus rebuilding `maps/bakersfieldish.bsp` and refreshing `zz_bakersfieldish.pk3` / `minimap_bakersfieldish.png` will flip this audit cleanly to **PASS**.
