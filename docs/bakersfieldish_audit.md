# Bakersfield-ish — Phase 1 Audit & Layout Blueprint

> **Audit Scope:** Complete geometric, architectural, pipeline, and integration audit of the existing Bakersfield Downtown map (`bakersfielddowntown`) in `G:\Quake\Combat\BakersfieldQuake`, establishing the layout blueprint for the new remastered post-apocalyptic custom map **"Bakersfield-ish"** (`bakersfieldish`).
> **Constraint Check:** Read-only audit; zero game assets, `.bsp`/`.lit` files, PK3s, or source files modified.

---

## 1. Current Bakersfield Downtown Source Pipeline & Reference Inventory

### 1.1 Map Source Architecture (Composable Python Pipeline)
`bakersfielddowntown` is **not** a hand-edited `.map` file. It is generated deterministically by a modular Python composer in `source/downtown/` that ingests six upstream Bakersfield venue `.map` files (from `source/mm_tools/`), registers each against real OpenStreetMap building footprints (`source/downtown/refs/osm_ft.json`), runs per-district plug-in piece scripts (`source/downtown/pieces/*.py`), builds the real street/sidewalk/hull layer, places gameplay & lighting, merges all WAD2 textures into one `dt_all.wad`, and compiles via ericw-tools (`qbsp -bsp2` → `vis` → `light -extra4`).

- **Primary Build Entrypoint:** `source/downtown/tools/build_downtown.sh`
  - Exact command that builds `bakersfielddowntown`:
    ```sh
    DT_WINDOW="-340 -900 950 275" DT_TAG=bakersfielddowntown DT_INSTALL=bakersfielddowntown DT_FAST= sh source/downtown/tools/build_downtown.sh
    ```
  - Also supports a low-VRAM variant (`DT_LITE=1` → `bakersfielddowntown_lite`) and fast single-block window test builds (`DT_WINDOW="x0 y0 x1 y1" DT_TAG=test`).
  - Post-compile steps in `build_downtown.sh`: `keep_sky_pvs.py` (restores pure `sky_bk` hull leaves under `-visdist 4000` so sky never HOMs), `scale_bklan_light85.py` (`post_light_scale = 0.69`), `clamp_bd_sb25.py`, `strip_miptex_pixels.py`, and `save_bd_presets.py`.
- **Core Composer Modules (`source/downtown/tools/`):**
  - `make_downtown.py` — Master orchestrator, WAD2 merger (`dt_all.wad` from 20 WADs), entity/group emitter, `write_map()`.
  - `dt_regs.py` — Coordinate datum, `SHIFT`, `SKY_Z`, street centrelines, source registration offsets, and priority `WINDOWS`.
  - `dt_ctx.py` — Build context `Ctx` (`box`, `prism`, `ent`, `brush_ent`, `to_breakable`, `drop_rect`, `point_free`, unit conversions).
  - `dt_sources.py` & `dt_mapio.py` — Source `.map` parser/mover/road-carver.
  - `dt_streets.py` — OSM-stepped street segments, sub-grade basement hole carving, sidewalk greedy-rect pads, sealed sky/clip/hint hull.
  - `dt_filler.py`, `dt_hull.py`, `lint_entities.py`, `bsp_stats.py`, `export_bd_web.py`.
- **Plug-in District Pieces (`source/downtown/pieces/`):**
  - `fox.py` + `fox_clock_tower.py` — Historic Fox Theater (refitted from `source/mm_tools/make_fox.py` + hollow climbable clock tower).
  - `padre.py` + `padre_lobby.py` + `padre_core.py` + `padre_rooms.py` — Full redesigned Padre Hotel (basement gym, 1F lobby/Farmacy/Brimstone, 2F Prairie Fire, 4F/6F/8F suites, dual `func_train` elevators, stairwell, roof deck, Clover/Old Post Office wing, 18th St south buildings).
  - `padre_garage.py` — 6-level 18th & Eye Public Parking Garage + 1812/1818 H St boutique + SW billboard lot + SE monument plaza (called from `filler_west.py`).
  - `nile.py` — Nile Theater (re-registered from `nile.map`), Campo/West storefront, Front Porch Music, surface lot.
  - `dagnys.py` — Dagny's Coffee / James Building (via `source/mm_tools/dagnys_module.py`) + Bare Studios, American Legion, AT&T, `59521020`, `59522422`, north lots.
  - `jerrys.py` — Jerry's Pizza & Guthrie's Alley Cat (from `jerrys.map`) + Tattoo Tower, Vest's Market, Mama Roomba, State Farm, Mike's Uniform, Wall St concrete alley.
  - `sandrinis.py` — Sandrini's Public House (from `sandrinis.map`) + SE 20th/Eye Mural Plaza, City Glow, Stars Theater, Mechanics Bank, Tina Marie's, She Shed, 1915 Chester, Sub Station/SWAT PC, JIN Sushi/Tegeler Hotel, 19th & H Hotel/Ovation, PG&E + 136-ft radio tower.
  - `filler.py` → `filler_west.py` & `filler_east.py` — Photo-audited facades for all remaining OSM blocks west of Chester and east of Chester / south of 18th.
  - `streets.py` — Street paving zones (asphalt, 19th St concrete, Eye St plaza), curbs, 39 kart curb ramps, crosswalks, markings, trees, traffic signals, 4 map-edge skyline cards.
  - `gameplay.py` + `gameplay_bq_upgrade.py` + `gameplay_bd_fun.py` — Spawns, pickups, ladders, express lifts, jump pads, skypads, go-karts, vehicles, Eric Cannons, NPCs (cached in `out/gameplay_cache.json`).
  - `lighting.py` — Global sun/dome/minlight/fog keys, dimmed emissive swaps (`dtlt.wad`), interior light zones, alley fill lights.
  - *(Note: `mint.py` exists for full `downtown` east of K St, but outputs 0 brushes in `bakersfielddowntown` because `x_max = 950 < K = 1190`.)*

### 1.2 Installed Map Artifacts, PK3 Dependencies & Docs/Viewers
| Category | Files / Paths | Notes |
|---|---|---|
| **Installed Map (loose)** | `maps/bakersfielddowntown.bsp` (37.1 MB), `maps/bakersfielddowntown.lit` (11.7 MB) | Loose per `AGENTS.md` (never put maps in base pk3s). Also `bakersfielddowntown.bsp.{json,geometry.obj,lm_0.png}`. |
| **Compiled Source Output** | `source/downtown/out/downtown_bakersfielddowntown.{map,bsp,lit,json,content.json,texinfo.json}` | `.map` is 8.73 MB (15,089 brushes, 1,584 entities). |
| **Base PK3 Assets** | `bakersfield.pk3` contains `gfx/env/dtsky145_*.png`, `scripts/dtlt.shader`, `scripts/fox_props.shader`, `progs/fox/*.md3`, and `textures/` overrides | **Never edit `bakersfield.pk3` or `q15.pk3`.** Any new Bakersfield-ish textures/skybox/models must ship in a small overlay pk3 (e.g., `zz_bakersfieldish.pk3`). |
| **Levelshot & Minimap** | `levelshots/bakersfielddowntown.jpg` (512×320), `zz_minimap.pk3` (`gfx/minimap/bakersfielddowntown.{png,txt}`) | Minimap bounds registered in `source/qc_combat_decomp/csqc/minimap_bounds.qc`. |
| **Design Docs & Handoffs** | `source/HANDOFF_MERGE_MAPS_GENERIC.md`, `source/downtown/{SPEC.md,STATE.md,BAKERSFIELDDOWNTOWN_PROMPT.md,HANDOFF_PERF_FOG.md,pieces/README.md}` | Full history of OSM registration, performance/PVS passes, lighting calibration, and audit rounds. |
| **HTML Viewers & Showcases** | `docs/bakersfielddowntown_viewer_showcase.html`, `docs/padre_hotel_redesign.html`, `source/downtown/web_viewer/`, `source/downtown/tools/export_bd_web.py` | Existing WebGL/Three.js viewer + showcase templates ready to adapt for Bakersfield-ish. |
| **StreetView / Photo Refs** | `source/downtown/refs/`: `downtown-bakersfield` (218), `fox-block` (425), `fox-theater` (118), `padre-hotel` (200), `padre-garage` (102), `nile-theater` (123), `dagnys-coffee` (97), `jerrys-pizza` (96), `sandrinis-bar` (77), `mint-bar` (87), plus `dt.osm` & `osm_ft.json`.<br>`source/mm_tools/ref_sources/`: `bklan_wmv_frames` (3,175), `orcom_mpg_frames` (1,916), `golden_west_gallery` (361), `gwc_gallery_20261103` (192), `streetview_gallery1` (78), `streetview_gallery2` (102), `review_2026-10-30_*` (385), `golden_west_landmarks` (4), `osm/`, `osm_route/`. | Complete photographic ground truth for downtown AND all 4 incoming landmarks. |

### 1.3 Coordinate Frame & Map Envelope
All composer code operates in **D-frame feet** (origin = Fox Theater OSM centroid `35.3775561°N, 119.0215878°W`; `+X` = East, `+Y` = North, `+Z` = Up from road surface `Z = 0`):
- **Scale:** `1 ft = 12 Quake map units` (`U = 12`).
- **Map Origin Shift:** `SHIFT = (835.0, -285.0)` D ft (`u_x = (D_x - 835) × 12`, `u_y = (D_y + 285) × 12`, `u_z = D_z × 12`).
- **Active `bakersfielddowntown` Playable Envelope:**
  - **D-frame feet:** `X ∈ [-340.0, +950.0]` (`1,290 ft` E–W), `Y ∈ [-900.0, +275.0]` (`1,175 ft` N–S), `Z ∈ [-36.0, +281.0]` (play floor `0.0` road / `0.5` sidewalk; deepest basement `-26.0 ft`; clip ceiling `+280.0 ft`).
  - **Quake map units:** `X ∈ [-14100, +1380]` (`15,480 u`), `Y ∈ [-7380, +6720]` (`14,100 u`), `Z ∈ [-432, +3372]` (`sky_bk` lid `3,360..3,372 u`).
- **Compiled Map Stats (`downtown_bakersfielddowntown.map` / `bakersfielddowntown.bsp`):**
  - **15,089 brushes** (`1,673` `worldspawn`, `8,648` `func_detail_wall`, `4,493` `func_detail_illusionary`, `186` `func_breakable` across 173 entities, `91` `trigger_push`, `12` `func_train` across 2 cabs, `7` `trigger_teleport`, `2` `func_wall`).
  - **1,584 entities** (`792` `light`, `183` `misc_model`, `173` `func_breakable`, `91` `trigger_push`, `56` `info_player_deathmatch` + `1` `info_player_start`, `31` `misc_gokart_1..6`, `18` `misc_lan_quakedesk`, `17` `item_armor2` + `3` `item_jetpack`, `15` `info_skypad`, `14` `npc_crowd`, `10` drivable/traffic `misc_vehicle_*`, `6` `misc_eric_cannon`, `39` weapons, `46` ammo, `30` health, `11` green/red armor, `20` `path_corner`, `7` `trigger_teleport`, `4` `info_teleport_destination`, `2` `func_train`).
  - **BSP2 totals (`bakersfielddowntown.bsp.json`):** `105,173` faces, `32,148` leafs, `55,657` nodes, `126,706` clipnodes, `108` inline brush models (`*0..*107`), `929` textures.

---

## 2. Core Recognizable Downtown Anchors (MUST KEEP FAITHFUL)

These three anchors — plus the exact H St & 18th St spatial relationship connecting them — define Bakersfield's silhouette and **must remain on their real footprints, heights, and orientations** in Bakersfield-ish (while receiving post-apocalyptic weathering and interactive destruction upgrades in Phases 2–3).

### 2.1 The Padre Hotel (`1702 18th St`, OSM `59480517`) + Clover / Old Post Office Wing (`59779838`)
- **Source Modules:** `pieces/padre.py`, `padre_lobby.py`, `padre_core.py`, `padre_rooms.py`
- **Main Hotel L-Tower + Podium Exact Bounds:**
  - **Footprint (1F Full Podium):** `D X = -28.4..75.6` (`104.0 ft`), `Y = -779.7..-669.7` (`110.0 ft`) — incl. trim/marquees/fire escapes: `D X = -31.2..81.1` (`112.3 ft`), `Y = -786.2..-665.8` (`120.3 ft`).
  - **Map Units (total shell incl. basement & top sign):** `X = -10395..-9047`, `Y = -6014..-4570`, `Z = -143..+1468` (`-11.9..+122.3 ft`).
  - **Brushes:** `670` worldspawn + `2,271` detail/trim + **`131` existing `func_breakable` windows** (`z = 3.3..97.7 ft`, `health 1`, `alpha 0.38`, `style 3`).
- **Orientation & Facades:**
  - Faces **South onto 18th St** (`y = -779.7`, Farmacy Cafe west + Brimstone Bar east, 5 tan/blue awnings, `18th St` sidewalk) and **East onto H St** (`x = 75.6`, Spanish Mission arched entrance pediment at `y = -710.7`, `'THE PADRE'` flat canopy `-717.7..-703.7`, 4 blue/tan awnings). North face backs onto **Wall St alley** (`y = -669.7`, valet door + white 2F–8F fire-escape stack).
- **L-Tower Vertical Architecture (Playable Floors):**
  - **Basement Gym:** `D X = 23.6..71.6, Y = -771.7..-717.7, Z = -11.9..0.5 ft` (`-143..+6 u`), white walls + rubber mat floor.
  - **1F Grand Lobby + Farmacy + Brimstone (`Z = 0.5..16.5 ft`):** Full rectangle `-28.4..75.6 × -779.7..-669.7`; grand stair to 2F (`24.8..34.2, -766.5..-736.0`).
  - **2F Mezzanine + Prairie Fire Rooftop Bar/Terrace (`Z = 16.5..28.3 ft`):** NW quadrant (`-28.4..22.4 × -733.7..-669.7`) steps back into the open-air Prairie Fire outdoor terrace!
  - **Upper L-Tower (3F–8F, `Z = 31.0..102.5 ft`):** South wing (`-28.4..75.6 × -779.7..-733.7`) + East wing (`22.4..75.6 × -733.7..-669.7`); playable interior suite floors on **4F (`42.5 ft`)**, **6F (`65.5 ft`)**, and **8F Penthouse (`88.5 ft`)** with 8-ft L-corridors, 103 open/breakable windows, and exterior fire escapes.
  - **Vertical Core (`X = 24.6..44.0, Y = -703.5..-671.2`):** Two opposing-phase `func_train` elevators (`pad_el_s` / `pad_el_n`, 6 stops: `1F, 2F, 4F, 6F, 8F, Roof`, `speed 180`) + continuous switchback stairwell.
  - **Rooftop Deck (`Z = 102.5 ft` = `1,230 u`):** Full walkable L-roof (`-28.4..75.6 × -779.7..-669.7`), elevator/stair bulkhead top **`Z = 111.5 ft` (`1,338 u`)**, crown/rooftop sign peak **`Z = 122.3 ft` (`1,468 u`)**.
- **Attached West Wing — Clover Ballroom / Old Post Office (`OSM 59779838`):**
  - **Bounds:** `D X = -188.2..-50.8` (`137.4 ft`), `Y = -777.6..-682.0` (`95.6 ft`), `Z = 0.0..22.8 ft` (`U: X = -12278..-10629, Y = -5911..-4764, Z = 0..274`). Connected to Padre 1F across a `22.6 ft` courtyard (`x = -51.0..-28.4`). Enterable Clover Ballroom + L-hall + 18th St 3-arch loggia + G St south-arch portal + Wall St USPS loading dock.

### 2.2 Historic Bakersfield Fox Theater (`2001 H St`, OSM `59516616`)
- **Source Modules:** `pieces/fox.py`, `pieces/fox_clock_tower.py` (refitted from `source/mm_tools/make_fox.py`)
- **Exact Bounds:**
  - **Full Footprint (incl. advanced H St wing & wrap-around marquee):** `D X = -48.9..88.0` (`136.9 ft`), `Y = -102.5..88.4` (`190.9 ft`), `Z = -3.5..116.5 ft` (orchestra pit `-13.0 ft`).
  - **Map Units:** `X = -10607..-8964`, `Y = 2190..4481`, `Z = -156..+1398` (`-13.0..+116.5 ft`).
  - **Brushes:** `176` worldspawn + `804` detail + **`4` existing `func_breakable` clock faces** (`z = 75.8..86.8 ft`).
- **Architectural Sub-Components:**
  - **Main Auditorium & Lobby Mass:** `D X = -48.9..48.5` (`97.4 ft`), `Y = -87.3..87.3` (`174.6 ft`), roof deck `Z = 51.0..58.0 ft` (`612..696 u`), orchestra pit down to `Z = -13.0 ft` (`-156 u`). Fully enterable: terrazzo vestibule, grand lobby, grand stairs, mezzanine, balcony/projection booth, auditorium, stage, wings, dressing rooms.
  - **Stagehouse Flytower (North End):** `D X = -47.8..37.7` (`85.5 ft`), `Y = 21.1..86.7` (`65.6 ft`), roof `Z = 80.0..80.8 ft` (`960..970 u`).
  - **Advanced 1–2 Storey H St East Retail/Vestibule Wing:** Shifted `+24 ft` east from OSM auditorium wall to `D X = 72.5` (`piers 73.4`), leaving a `15.5 ft` H St west sidewalk (`72.5..88.0`). Houses Eva's Lounge, poster cases, arched courtyard pavilion, and `A&B INC.` north dressing wing.
  - **Iconic Wrap-Around Corner Marquee:** `D X = 26.5..82.1` (`55.6 ft`), `Y = -96.6..-11.0` (`85.6 ft`), `Z = 8.4..23.4 ft` (`U: X = -9702..-9035, Y = 2261..3288, Z = 101..281`). Overhangs 20th St (`y = -96.6`, 5.9 ft shy of curb) and H St (`x = 82.1`, 5.9 ft shy of curb).
  - **SE Corner Clock Tower (Key Destructible Target!):**
    - **Shaft + Pilasters:** `D X = 48.3..72.8` (`24.5 ft`), `Y = -86.2..-61.8` (`24.4 ft`), `Z = 22.0..72.2 ft` (`U: X = -9440..-9147, Y = 2386..2678, Z = 264..866`). Hollowed with 7-flight switchback stair + express ladder from East Mezzanine (`z = 22 ft`).
    - **4-Way Belfry & Shoot-Through Clocks:** `D X = 48.3..72.8, Y = -86.2..-61.8, Z = 72.2..91.8 ft` (`866..1102 u`); 4 `func_breakable` clock faces at `Z = 75.8..86.8 ft` (`910..1042 u`).
    - **Blue-Grey Dome & Spire Peak:** `D X = 51.1..72.8, Y = -83.4..-64.6, Z = 89.5..116.5 ft` (`1074..1398 u`).
- **Spatial Relationship to Padre Hotel:**
  - Directly **582.4 ft (6,989 u) straight north** along the **west side of H Street** (Padre NE corner `(75.6, -669.7)` to Fox Clock Tower SE corner `(72.8, -86.2)` = `583.5 ft`, aligned within `2.8 ft` in X!).
  - Both landmarks anchor the west edge of H St, creating the single most recognizable north–south canyon sightline in downtown Bakersfield: Fox's 116.5-ft Clock Tower & marquee at the north end, Padre's 122.3-ft L-tower at the south end.

### 2.3 18th & Eye Public Parking Garage (`1600 Eye St`, OSM `59588521`) + 1812/1818 H St Corner (`59485640`)
- **Source Module:** `pieces/padre_garage.py` (invoked from `pieces/filler_west.py`)
- **Exact Bounds (6-Level Parking Structure Proper):**
  - **D-frame feet:** `X = 194.3..419.0` (`224.7 ft` E–W), `Y = -778.7..-665.8` (`112.9 ft` N–S), `Z = -0.6..72.0 ft` (L6 walkable roof deck `54.0 ft`, parapet `58.2 ft`, SW brick tower `61.5 ft`, L6 green portal `63.4 ft`, rooftop cobra poles `72.0 ft`).
  - **Map Units:** `X = -7688..-4992` (`2,696 u`), `Y = -5924..-4570` (`1,354 u`), `Z = -7..+864`.
  - **Brushes:** `20` worldspawn + `727` detail (open concrete column bays, continuous vehicle ramps, hairpin stalls, beams, tension cables, bistro lights on Wall St).
- **6 Walkable/Drivable Levels:** `L1 = 0.5 ft` (`6 u`), `L2 = 11.2 ft` (`134 u`), `L3 = 21.9 ft` (`263 u`), `L4 = 32.6 ft` (`391 u`), `L5 = 43.3 ft` (`520 u`), `L6 Roof = 54.0 ft` (`648 u`) — all connected by continuous sloped concrete ramps (go-kart drivable!), a walkable SW switchback staircase, and an SW Express Elevator (`trigger_push` L1 → L6 at `D(241.4, -773.0)`).
- **Key Architectural Features:**
  - **18th St Main Entrance (`x = 236..270, y = -778`):** Green awning, IN/OUT ticket island, yellow barrier arms, `CLEARANCE 6'-6"` bar, vertical illuminated `[P] PARKING` blade sign (`x = 271`).
  - **SW Brick Stair/Elevator Tower:** `D X = 194.3..245.0, Y = -778.2..-712.0, Z = 0.5..61.5 ft`.
  - **Eye St East Entrance & SE Monument Plaza (`x = 417.5, y = -778..-667.5`):** Entrance bay (`y = -760..-728`), full-height tan-brick shear wall (`-728..-667.5`), curved `'BAKERSFIELD / 18TH & EYE PARKING'` stone monument + second `[P] PARKING` blade sign at SE corner.
  - **Attached West Parcels (Directly Facing Padre Hotel Across H St):**
    - **1812/1818 H St Boutique Shopfront (`OSM 59485640`):** `D X = 151.6..194.5` (`42.9 ft`), `Y = -725.6..-665.8` (`59.8 ft`), `Z = 0.5..16.2 ft` (`U: -8201..-7686, -5287..-4567, 6..194`). Enterable interior connecting H St straight into Garage L1, with **`5` `func_breakable` dark multi-pane windows/transoms**.
    - **SW Corner Landscaped Lot & Billboard:** `D X = 154.0..204.0` (`50.0 ft`), `Y = -778.0..-725.6` (`52.4 ft`), `Z = 0.5..32.8 ft` (low planter + Morgan & Morgan billboard right in front of the SW brick stair tower).
- **Spatial Relationship to Padre Hotel:**
  - Directly **East across H Street** (`52.0 ft` roadway, `x = 86.5..138.5`): Padre east wall (`x = 75.6`) → 1812 H St / SW lot (`x = 151.6`) = **`76.0 ft` (`912 u`) facade-to-facade**, and Padre east wall → Garage proper (`x = 194.3`) = **`118.7 ft` (`1,424 u`)**. From Garage Levels 2–6 (especially open L6 Roof at `z = 54 ft`), players have an unobstructed panoramic combat sightline straight into every floor of the Padre Hotel (`1F–8F` & `102.5 ft` roof) — ideal for watching/shooting the Padre Hotel destruction sequence!

---

## 3. Street Grid, Road Widths, Sightlines & Skybox Analysis

### 3.1 Street & Alley Network (`bakersfielddowntown` Region)
Streets follow real OSM stepped centrelines (0.3° grid rotation tracked per block segment) at `Z = 0.0 ft` road surface and `Z = 0.5 ft` (`6 u`) sidewalks.

| Street / Alley | Axis | Centreline (D ft) | Curb-to-Curb Width | Roadway Bounds (D ft) | Roadway Bounds (Map Units) | Facade-to-Facade Gap | Flow / Surface |
|---|---|---|---|---|---|---|---|
| **G Street** | N–S | `-236.5` to `-225.0` | `39–48 ft` (44 typ.) | `x = -256.5..-205.0` | `X = -13146..-12480` | `~87 ft` | 1-way mid / 2-way ends; asphalt |
| **Fox West Alley** | N–S | `-58.5` | `20 ft` | `x = -68.5..-48.5` (`y = -126.5..218.5`) | `X = -10842..-10602` | `20 ft` | Service alley; asphalt |
| **H Street** *(Hero Spine)* | N–S | `111.5` to `117.5` (`113` nom.) | **`52 ft`** | `x = 85.5..143.5` | `X = -8994..-8298` | **`76–91 ft`** (`151.6 ft` at Nile Lot!) | **2-way**; asphalt |
| **H–Eye South Alley** | N–S | `285.5` | `20 ft` | `x = 275.5..295.5` (`y = -475..-305`) | `X = -6714..-6474` | `53 ft` (lot) | Alley; asphalt |
| **Dagny's Alley S / N** | N–S | `280.0` / `289.5` | `20 ft` | `x = 270..299.5` (`y = -131.5..-86.5`, `175..275`) | `X = -6780..-6426` | `31 ft` | Alley; asphalt |
| **Eye Street** *(Plaza Spine)* | N–S | `459.5` to `464.0` | `46–48 ft` | `x = 435.5..488.0` | `X = -4794..-4164` | **`83–89 ft`** (`255.6 ft` at lot!) | 1-way S; stamped plaza `19th–20th` |
| **Chester Avenue** *(Boulevard)* | N–S | `821.0` | **`66 ft`** (`2×28` + `10 ft` median) | `x = 788.0..854.0` | `X = -564..+228` | **`96.5–124.5 ft`** (`114 ft` typ.) | Divided 1-way pair + 10-ft raised median |
| **18th Street** *(Padre/Garage)* | E–W | `-822.0` to `-827.0` | **`52 ft`** | `y = -853.0..-796.0` | `Y = -6816..-6132` | **`82 ft`** (Padre) / open S of Garage | **2-way**; asphalt |
| **Wall Street** | E–W | `-648.5` to `-658.5` | `18–20 ft` | `y = -667.5..-638.5` | `Y = -4590..-4242` | `27–38 ft` | Concrete alley (`Eye–Chester` = Guthrie's pedestrian alley) |
| **19th Street** *(Main Cross)* | E–W | `-473.0` to `-484.5` | **`49–50 ft`** | `y = -509.5..-448.5` | `Y = -2694..-1962` | **`82–85 ft`** (`168.2 ft` W of H!) | 1-way E; pale concrete + angled stalls |
| **Service Street** | E–W | `-299.5` to `-306.5` | `18–20 ft` | `y = -316.5..-289.5` | `Y = -378..-54` | `20–41 ft` | E–W service alley; asphalt |
| **20th Street** *(Fox/Dagny's)* | E–W | `-125.5` to `-135.5` | **`48 ft`** (`36 ft` E of Ch.) | `y = -159.5..-101.5` | `Y = +1506..+2202` | **`77.5–89 ft`** (`140.8 ft` at Eye!) | 1-way W; asphalt |
| **20th Place** | E–W | `48.0` | `22 ft` | `y = 37.0..59.0` (`x = 464..802`) | `Y = +3864..+4128` | `22–80 ft` | Short E–W alley (`Eye–Chester` only) |
| **21st Street** *(North Edge)* | E–W | `208.5` to `218.5` | **`50–52 ft`** | `y = 183.5..244.5` | `Y = +5622..+6354` | `82–173 ft` | **2-way**; asphalt |

### 3.2 Key Sightlines to Preserve & Enhance
1. **H Street Hero Corridor (`x = 87..139`, `y = -850..+215`):** Direct 582-ft sightline linking **Padre Hotel** (south, 122.3 ft) and **Fox Theater Clock Tower & Marquee** (north, 116.5 ft). Any arch (e.g., Bakersfield Sign) placed here frames both heroes; any west-side replacement block between 19th and 20th must stay `<= 35–40 ft` tall so Fox's tower and Padre's upper stories remain visible over the rooftops.
2. **18th & H Plaza Sightline (`x = 75..419`, `y = -850..-665`):** Direct 76–119 ft cross-street view between **Padre Hotel** and **18th & Eye Parking Garage** (including L6 Roof `z = 54 ft` overlooking Padre 4F–8F and Roof). Must remain 100% unobstructed.
3. **20th Street East–West Axis (`y = -155..-102`):** Connects **Fox Theater** marquee (`x = 82`) past **Dagny's Coffee** (`x = 291..417`) to **Eye St / Chester Ave**. Placing a major new landmark (Golden West Casino or Great Castle) on 20th St makes it immediately visible right from the Fox Theater steps.
4. **Eye Street Plaza Axis (`x = 437..488`):** Connects **Parking Garage** SE monument (`y = -778`), **Sandrini's / Mural Plaza** (`y = -285..-172`), and **Dagny's** (`y = -88..-28`). Wide open mid-block lot `1183500273` (`x = 243..419, y = -296..-177`) sits directly on this corridor.
5. **Chester Avenue Boulevard (`x = 788..854`):** Widest street in the map (`66 ft` curb-to-curb, `111–125 ft` facade-to-facade, raised landscaped median). Naturally accepts a full 1:1 `97 ft`-span Bakersfield Sign arch or grand casino forecourt.

### 3.3 Current Skybox Height & High-Skybox Recommendation for Bakersfield-ish
- **Current `bakersfielddowntown` Skybox (`dt_regs.py` + `dt_streets.py:build_hull`):**
  - `SKY_Z = 280.0 ft` (`3,360 u`), `sky_bk` lid `3,360..3,372 u`, perimeter `clip` wall up to `3,360 u`.
  - Tallest existing structures: PG&E radio tower `136.0 ft` (`1,632 u`), Padre Hotel `122.3 ft` (`1,468 u`), Fox Clock Spire `116.5 ft` (`1,398 u`).
  - Existing `info_skypad` apexes reach **`246–265 ft` (`2,952–3,180 u`)** — leaving **only `15–34 ft` (`180–408 u`)** of clearance below the skybox ceiling! With jetpacks or Super Jump Pads, players easily bonk the `280 ft` ceiling.
  - Current `worldspawn` fog: `"0.26 0.437 0.466 0.506 1 3650 5250 1800 450"` (`top = 1800 u = 150 ft`, `fadedepth = 450 u`).
  - Current horizontal vis-cutting `hint` planes: `z = 19.5, 30.0, 42.5, 66.0 ft`, plus 64 vertical intersection throat `hint` portals (`z = 0.5..66.0 ft`), plus sky-moat `hint` box (`zt - 4.0 ft`) for `keep_sky_pvs.py`, compiled with `vis -visdist 4000`.
- **Recommendation for Bakersfield-ish (User explicitly requested a high skybox):**
  - Raise **`SKY_Z` from `280 ft` (`3,360 u`) → `600 ft` (`7,200 u`)** (minimum `520 ft` / `6,240 u`, sweet spot `600 ft` = `7,200 u`, well under BSP2 coordinate limits `±32,768 u`).
  - **Keep PVS fast despite the tall skybox:** Keep the existing horizontal `hint` planes at `z = 19.5, 30.0, 42.5, 66.0 ft` and add **one** more horizontal `hint` cap at **`z = 140.0 ft` (`1,680 u`)** (just above the Padre/Fox/PG&E tops). Because street-level and roof-level leafs remain capped by `hint` planes and `vis -visdist`, raising `SKY_Z` to `600 ft` adds almost zero vis portals or street-level draw calls while giving jetpacks, chained Super Jump Pads (apexes `300–450 ft`), and dramatic post-apocalyptic skybox clouds / soaring Padre collapse debris massive vertical room!
  - Raise skybox fog `top` (if post-apocalyptic dust/smog haze is used) to e.g. `2200–2800 u` with `fadedepth 800–1200 u` so distant horizons blend cleanly into a dramatic dusty/amber apocalyptic skybox without flattening overhead clouds.

---

## 4. Complete Building, Block & Parking Lot Catalog

### Importance Tiers
- **Tier S (SACRED ANCHOR — KEEP FAITHFUL):** Padre Hotel (+ Clover/Post Office), Fox Theater, 18th & Eye Public Parking Garage (+ 1812 H St).
- **Tier A (ENTERABLE LANDMARK — KEEP IF POSSIBLE):** Nile Theater, Dagny's Coffee / James Building, Sandrini's Public House, Jerry's Pizza & Guthrie's Alley Cat.
- **Tier B (NOTABLE EXTERIOR — KEEP OR WEATHER):** Visually distinctive historic facades on major corridors (Tevis Block, Stars Theater / Mechanics Bank, 1915 Chester, Cristal/Crites, Buena Vista Museum, Fire Station No. 1 edge).
- **Tier C (REPLACEABLE GENERIC FILLER):** Non-enterable solid-mass boxes, low-value commercial strips, windowless warehouses, blank/boarded shells, or clipped edge fragments.
- **Tier D (PRIME OPEN / SURFACE LOT):** Empty asphalt parking lots, vacant fenced lots, demolished lots — **zero buildings lost** if repurposed!

### 4.1 Complete Block-by-Block Building Inventory (`bakersfielddowntown`, 42 OSM Buildings + Sub-Buildings)

> **Format:** D-frame feet `(X0, Y0)–(X1, Y1)` and Quake map units `(UX0, UY0)–(UX1, UY1)`, `W × D × H` (ft), `Z min..max` (ft / units).

#### Column 1: West of G Street (`D X = -340..-245`, Western Map Edge Strip)
| Block | Building / OSM ID | Piece | D-Feet `(X0,Y0)-(X1,Y1)` | Map Units `(X0,Y0)-(X1,Y1)` | Size `W×D` (ft) | `Z` Range (ft / u) | Interior? | Tier |
|---|---|---|---|---|---|---|---|---|
| W of G / S of 18th | Small SW Bldg (`59488975`) | `padre` | `(-340.0,-900.0)-(-270.9,-860.4)` | `(-14100,-7380)-(-13271,-6905)` | `69.1×39.6` | `0.0..20.2` (`0..242`) | No | **C** (edge) |
| W of G / 18th–Wall | *Demolished Greyhound Lot* (`59321997`) | — | `(-340.0,-785.7)-(-271.0,-662.3)` | `(-14100,-6008)-(-13272,-4528)` | `69.0×123.4` | `0.0..0.5` | Empty lot | **D** |
| W of G / Wall–19th | The Dream Center (`59475474`) | `filler_west` | `(-334.5,-591.2)-(-276.1,-519.1)` | `(-14034,-3674)-(-13333,-2809)` | `58.4×72.1` | `0.0..19.2` (`0..230`) | No | **C** |
| W of G / 19th–Serv | Classical Tan Brick (`59439771`) | `filler_west` | `(-340.0,-418.6)-(-282.4,-342.9)` | `(-14100,-1603)-(-13409,-695)` | `57.6×75.7` | `0.0..40.6` (`0..487`) | No | **C** (edge) |
| W of G / Serv–20th | Small G St Commercial (`59434994`) | `filler_west` | `(-317.9,-289.6)-(-274.8,-259.9)` | `(-13835,-55)-(-13318,301)` | `43.1×29.7` | `0.0..16.3` (`0..196`) | No | **C** |
| W of G / Serv–20th | SW 20th & G Victorian (`59480001`) | `filler_west` | `(-308.4,-257.2)-(-277.3,-222.2)` | `(-13721,334)-(-13348,754)` | `31.1×35.0` | `0.0..25.9` (`0..311`) | No | **C** |
| W of G / 20th–21st | Wood Cottage (`59480258`) | `filler_west` | `(-304.5,-92.3)-(-262.7,-61.3)` | `(-13674,2312)-(-13172,2684)` | `41.8×31.0` | `0.0..15.4` (`0..185`) | No | **C** |
| W of G / 20th–21st | DB & Co / Happy Whole You (`59437541`) | `filler_west` | `(-340.0,-52.1)-(-254.0,-2.3)` | `(-14100,2795)-(-13068,3392)` | `86.0×49.8` | `0.0..15.2` (`0..182`) | No | **C** |
| W of G / 20th–21st | White Cottage (`59570511`) | `filler_west` | `(-338.0,16.0)-(-290.0,41.6)` | `(-14076,3612)-(-13500,3919)` | `48.0×25.6` | `0.0..15.6` (`0..187`) | No | **C** |
| W of G / 20th–21st | Fantasy Sports Cards (`59516898`) | `filler_west` | `(-340.0,123.9)-(-265.6,188.5)` | `(-14100,4907)-(-13207,5682)` | `74.4×64.6` | `0.0..19.4` (`0..233`) | No | **C** |
| W of G / N of 21st | Poise Pilates (`59564931`, clipped) | `filler_west` | `(-340.0,266.2)-(-272.9,275.0)` | `(-14100,6614)-(-13295,6720)` | `67.1×8.8` | `0.0..26.7` (`0..320`) | No | **C** (edge) |

#### Column 2: G Street to H Street (`D X = -212..+86`, **THE PADRE–FOX HERO SPINE**)
| Block | Building / OSM ID | Piece | D-Feet `(X0,Y0)-(X1,Y1)` | Map Units `(X0,Y0)-(X1,Y1)` | Size `W×D` (ft) | `Z` Range (ft / u) | Interior? | Tier |
|---|---|---|---|---|---|---|---|---|
| G–H / S of 18th | Central Academy / 1715 18th (`59474821`, clipped) | `padre` | `(-189.4,-900.0)-(73.0,-861.7)` | `(-12293,-7380)-(-9144,-6920)` | `262.4×38.3` | `0.0..31.5` (`0..378`) | No | **B/C** (Padre backdrop) |
| G–H / 18th–Wall | **Clover / Old Post Office** (`59779838`) | `padre` | `(-182.7,-773.0)-(-51.3,-688.4)` | `(-12212,-5856)-(-10636,-4841)` | `131.4×84.6` | `0.0..22.8` (`0..274`) | **Yes** | **S** (Padre wing) |
| G–H / 18th–Wall | **THE PADRE HOTEL** (`59480517`) | `padre` | `(-28.4,-780.5)-(75.5,-668.8)` *(shell `-31.2..81.1, -786.2..-665.8`)* | `(-10395,-6014)-(-9047,-4570)` | `103.9×111.7` | **`-11.9..122.3`** (`-143..1468`) | **Yes** (B+1F/2F/4F/6F/8F+Roof) | **S (SACRED)** |
| G–H / Wall–19th | **Nile Theater Block** (`59495920`): West Campo (`-187..-120`), **Nile Theater** (`-120..-48`), Front Porch Music (`-48..11`) | `nile` | `(-187.5,-633.1)-(11.2,-506.3)` | `(-12270,-4177)-(-9886,-2656)` | `198.7×126.8` | `-0.2..58.2` (`-2..698`) | **Yes** (Nile hall + Campo/East, 8 brk wins) | **A** |
| G–H / Wall–19th | *Nile East Surface Lot* (`1183498308`) | `nile` | `(10.6,-628.8)-(73.5,-517.4)` | `(-9893,-4126)-(-9138,-2789)` | `62.9×111.4` | `0.0..0.5` | Empty lot | **D** |
| G–H / 19th–Serv | *NW 19th & G Surface Lot* (`1183500275`) | `streets` | `(-196.6,-431.5)-(-85.0,-306.1)` | `(-12379,-1758)-(-11040,-253)` | **`111.6×125.4`** | `0.0..0.5` | Empty lot | **D (PRIME SLOT)** |
| G–H / 19th–Serv | Tevis Block (`59568189`, sandstone 2F) | `filler_west` | `(-85.5,-427.7)-(67.2,-315.4)` | `(-11046,-1712)-(-9214,-365)` | `152.7×112.3` | `0.0..36.8` (`0..442`) | No | **B/C** |
| G–H / Serv–20th | Generic 2F Strip (`59507032`) | `filler_west` | `(-193.0,-287.7)-(-78.7,-164.4)` | `(-12336,-32)-(-10964,1447)` | `114.3×123.3` | `0.0..33.4` (`0..401`) | No | **C (REPLACEABLE)** |
| G–H / Serv–20th | 20th St Beige Office (`760730139`) | `filler_west` | `(-78.8,-229.5)-(71.2,-164.5)` | `(-10966,666)-(-9166,1446)` | `150.0×65.0` | `0.0..36.6` (`0..439`) | No | **C (REPLACEABLE)** |
| G–H / Serv–20th | *South-of-20th Surface Lot* (`1183500274`) | `streets` | `(-78.8,-289.3)-(72.4,-229.4)` | `(-10966,-52)-(-9151,667)` | `151.2×59.9` | `0.0..0.5` | Empty lot | **D** |
| G–H / 20th–21st | Ribbed Cream Warehouse (`59520411`) | `filler_west` | `(-169.2,-49.4)-(-68.1,-3.6)` | `(-12050,2827)-(-10837,3377)` | `101.1×45.8` | `0.0..21.5` (`0..258`) | No | **C (REPLACEABLE)** |
| G–H / 20th–21st | Windowless Cream Warehouse (`59523847`) | `filler_west` | `(-142.9,-2.4)-(-68.6,155.1)` | `(-11735,3391)-(-10843,5281)` | `74.3×157.5` | `0.0..21.2` (`0..254`) | No | **C (REPLACEABLE)** |
| G–H / 20th–21st | **HISTORIC FOX THEATER** (`59516616`) | `fox` | `(-48.9,-102.5)-(88.0,88.4)` *(OSM `-47.5..47.5` + E wing `72.5` + marquee `82.1`)* | `(-10607,2190)-(-8964,4481)` | `136.9×190.9` | **`-13.0..116.5`** (`-156..1398`) | **Yes** (Full theater + hollow clock tower) | **S (SACRED)** |
| G–H / 20th–21st | Today Cleaners Canopy (`848207739`) | `filler_west` | `(-17.2,88.3)-(69.3,174.4)` | `(-10226,4480)-(-9188,5513)` | `86.5×86.1` | `0.0..16.3` (`0..196`) | No | **C (REPLACEABLE)** |
| G–H / N of 21st | Fire Station No. 1 Front (`59333130`, clipped at `y=275`) | `filler_west` | `(-116.0,244.5)-(81.8,274.7)` | `(-11412,6354)-(-9038,6716)` | `197.8×30.2` | `0.0..46.5` (`0..558`) | No | **B** (clipped edge) |

#### Column 3: H Street to Eye Street (`D X = 138..438`, **CENTRAL DOWNTOWN & PARKING GARAGE**)
| Block | Building / OSM ID | Piece | D-Feet `(X0,Y0)-(X1,Y1)` | Map Units `(X0,Y0)-(X1,Y1)` | Size `W×D` (ft) | `Z` Range (ft / u) | Interior? | Tier |
|---|---|---|---|---|---|---|---|---|
| H–Eye / S of 18th | *South-of-18th Parking Lot* (`1183498282`) | `streets` | `(149.2,-900.0)-(350.3,-862.7)` | `(-8230,-7380)-(-5816,-6932)` | `201.1×37.3` | `0.0..0.5` | Empty lot | **D** (edge) |
| H–Eye / S of 18th | SW 18th & Eye Bldg (`59479688`, clipped) | `filler_east` | `(364.2,-900.0)-(423.7,-864.4)` | `(-5650,-7380)-(-4936,-6953)` | `59.5×35.6` | `0.0..20.0` (`0..240`) | No | **C** (edge) |
| H–Eye / 18th–Wall | **1812/1818 H St Boutique** (`59485640`) + SW Billboard Lot | `padre_garage` | `(151.6,-778.0)-(204.0,-665.8)` | `(-8201,-5916)-(-7572,-4570)` | `52.4×112.2` | `0.5..16.2` *(bb 32.8)* | **Yes** (5 brk wins) | **S** (Garage front) |
| H–Eye / 18th–Wall | **18TH & EYE 6-LEVEL PARKING GARAGE** (`59588521`) | `padre_garage` | `(194.3,-778.7)-(419.0,-665.8)` | `(-7688,-5924)-(-4992,-4570)` | `224.7×112.9` | **`-0.6..72.0`** (`L6=54.0 ft`) | **Yes** (All 6 open levels + ramps + stairs) | **S (SACRED)** |
| H–Eye / Wall–19th | Boca's Cantina / SE 19th & H (`59490021`) | `filler_west` | `(162.6,-631.6)-(251.1,-521.8)` | `(-8069,-4159)-(-7007,-2842)` | `88.5×109.8` | `0.0..27.4` (`0..329`) | No | **C (REPLACEABLE)** |
| H–Eye / Wall–19th | Cristal / Two Goats / Crites (`59474361`) | `filler_west` | `(292.3,-632.1)-(419.9,-522.0)` | `(-6512,-4165)-(-4981,-2844)` | `127.6×110.1` | `0.0..33.7` (`0..404`) | No | **B/C** |
| H–Eye / 19th–Serv | NE 19th & H 4F Hotel + Ovation (`59490321`) | `sandrinis` | `(154.5,-433.8)-(264.3,-313.7)` | `(-8166,-1786)-(-6848,-344)` | `109.8×120.1` | `0.5..46.2` (`6..554`) | No | **B/C** |
| H–Eye / 19th–Serv | JIN Sushi / Fredo's / Tegeler Hotel (`59476231`) | `sandrinis` | `(317.7,-437.2)-(424.3,-314.8)` | `(-6208,-1826)-(-4928,-358)` | `106.6×122.4` | `0.5..52.4` (`6..629`) | No | **B** |
| H–Eye / Serv–20th | PG&E Bldg (`59503393`) + **136-ft Radio Tower** (`x=258, y=-194.5`) | `sandrinis` | `(158.4,-295.6)-(243.4,-177.4)` *(tower to `x=274`)* | `(-8119,-127)-(-7099,1291)` | `85.0×118.2` | `0.5..20.8` *(tower `136.0`)* | No | **C** *(tower iconic)* |
| H–Eye / Serv–20th | *Central Eye St Parking Lot* (`1183500273`) + White Kiosk | `sandrinis` | `(243.0,-295.8)-(419.3,-177.2)` *(overlap `59483191` N)* | `(-7104,-130)-(-4988,1294)` | **`176.3×118.6`** | `0.0..0.5` *(kiosk 11 ft)* | Empty lot | **D (PRIME SLOT)** |
| H–Eye / Serv–20th | Sub Station / SWAT PC / Portrait (`59483191`) | `sandrinis` | `(315.7,-248.1)-(427.5,-175.3)` | `(-6232,443)-(-4890,1316)` | `111.8×72.8` | `0.5..39.5` (`6..474`) | No | **C (REPLACEABLE)** |
| H–Eye / 20th–21st | Bare Studios / 2000 H St (`59516526`) | `dagnys` | `(149.6,-87.3)-(260.3,-30.0)` | `(-8225,2372)-(-6896,3060)` | `110.7×57.3` | `0.0..16.2` (`0..194`) | Small 1-rm | **C (REPLACEABLE)** |
| H–Eye / 20th–21st | American Legion (`59520322`) | `dagnys` | `(159.3,47.3)-(277.6,139.9)` | `(-8108,3988)-(-6689,5099)` | `118.3×92.6` | `0.0..23.0` (`0..276`) | No | **C (REPLACEABLE)** |
| H–Eye / 20th–21st | **Dagny's Coffee / James Building** (`59521598`) | `dagnys` | `(291.0,-88.3)-(416.9,-28.5)` | `(-6528,2360)-(-5017,3078)` | `125.9×59.8` | `0.0..31.5` (`0..378`) | **Yes** (1F+2F loft, 24 brk wins) | **A** |
| H–Eye / 20th–21st | *Giant North Surface Lots* (`1183503877` + `1183503876`) | `dagnys` | `(151.5,-30.4)-(417.6,177.2)` *(around Legion)* | `(-8202,3055)-(-5009,5546)` | **`266×207` total** | `0.0..0.5` | Empty lots | **D (PRIME SLOT)** |
| H–Eye / N of 21st | Construction Fence & Open Lot (`1183508928`) | `filler_west` | `(155.4,240.5)-(425.7,275.0)` | `(-8155,6306)-(-4912,6720)` | `270.3×34.5` | `0.0..8.6` | Empty lot | **D** (edge) |

#### Column 4: Eye Street to Chester Avenue (`D X = 485..788`, **ENTERTAINMENT & COMMERCIAL CORE**)
| Block | Building / OSM ID | Piece | D-Feet `(X0,Y0)-(X1,Y1)` | Map Units `(X0,Y0)-(X1,Y1)` | Size `W×D` (ft) | `Z` Range (ft / u) | Interior? | Tier |
|---|---|---|---|---|---|---|---|---|
| Eye–Ch / S of 18th | El Charrito (`59567849`, clipped) | `filler_east` | `(575.5,-900.0)-(641.1,-859.2)` | `(-3114,-7380)-(-2327,-6890)` | `65.6×40.8` | `0.0..22.0` (`0..264`) | No | **C** (edge) |
| Eye–Ch / S of 18th | Chain Cohn Clark (`59573893`, clipped) | `filler_east` | `(641.5,-900.0)-(775.8,-859.2)` | `(-2322,-7380)-(-710,-6890)` | `134.3×40.8` | `0.0..31.3` (`0..376`) | No | **C** (edge) |
| Eye–Ch / 18th–Wall | **Guthrie's Alley Cat** + Mama Roomba + State Farm + 3F East + Jewelers + Mike's Uniform (`59475725`, `59780215`, `60082057`) | `jerrys` | `(504.6,-785.0)-(769.7,-666.6)` | `(-3965,-6000)-(-784,-4579)` | `265.1×118.4` | `0.5..44.0` (`6..528`) | **Yes** (Guthrie's bar/pool) | **A** |
| Eye–Ch / Wall–19th | **Jerry's Pizza & Pub** (E `679..769`) + Tattoo Tower (W) + 19th Frontage + Vest's Market (`59492532`) | `jerrys` | `(506.5,-634.8)-(770.3,-521.2)` | `(-3942,-4198)-(-776,-2834)` | `263.8×113.6` | **`-26.0..55.4`** (`-312..665`) | **Yes** (Jerry's 1F + Basement Stage) | **A** |
| Eye–Ch / 19th–Serv | Tina Marie's + Manna + 4F She Shed + 1915 Chester Antique Mall (`59435706`) | `sandrinis` | `(507.2,-439.1)-(771.0,-322.8)` | `(-3934,-1849)-(-768,-454)` | `263.8×116.3` | `0.0..50.5` (`0..606`) | No | **B** |
| Eye–Ch / Serv–20th | **Sandrini's Public House** (`499..585`) + Mural Plaza + City Glow + Bobby Cloud + Stars Theater + Mechanics Bank (`59478223`) | `sandrinis` | `(499.1,-285.2)-(757.5,-171.6)` | `(-4031,-2)-(-930,1361)` | `258.4×113.6` | **`-13.0..46.8`** (`-156..562`) | **Yes** (Sandrini's basement bar) | **A** (W half) / **B** (E half) |
| Eye–Ch / 20th–21st | AT&T Switching Bldg (`59518832`, 5F monolithic) | `dagnys` | `(505.0,-86.4)-(636.8,38.0)` | `(-3960,2383)-(-2378,3876)` | `131.8×124.4` | `0.0..61.3` (`0..736`) | No | **C (REPLACEABLE)** |
| Eye–Ch / 20th–21st | Boarded Storefront (`59522422`) + Fenced Vacant Lot (`y = -21..37`) | `dagnys` | `(640.0,-84.1)-(771.1,-21.2)` *(+ lot to `y=37`)* | `(-2340,2411)-(-767,3166)` | `131.1×62.9` *(+ `131×58` lot)* | `0.0..19.0` (`0..228`) | No | **C/D (REPLACEABLE)** |
| Eye–Ch / 20th–21st | Tegeler Brick + Chatinni / Carniceria Strip (`59521020`) | `dagnys` | `(501.2,58.5)-(771.7,184.4)` | `(-4006,4122)-(-760,5633)` | `270.5×125.9` | `0.0..27.1` (`0..325`) | No | **C (REPLACEABLE)** |
| Eye–Ch / N of 21st | Brick Shop (`59521336`) + Guarantee Shoe (`59516120`, clipped) | `filler_west` | `(572.5,260.5)-(769.4,275.0)` | `(-3150,6546)-(-787,6720)` | `196.9×14.5` | `0.0..22.7` (`0..272`) | No | **C** (edge) |

#### Column 5: East of Chester Avenue (`D X = 854..950`, Eastern Clipped Backdrop Strip)
| Block | Building / OSM ID | Piece | D-Feet `(X0,Y0)-(X1,Y1)` | Map Units `(X0,Y0)-(X1,Y1)` | Size `W×D` (ft) | `Z` Range (ft / u) | Interior? | Tier |
|---|---|---|---|---|---|---|---|---|
| E of Ch / S of 18th | 7-Storey SE Precast Tower (`59490243`, clipped) | `filler_east` | `(889.6,-900.0)-(950.0,-857.0)` | `(655,-7380)-(1380,-6864)` | `60.4×43.0` | `0.0..90.3` (`0..1084`) | No | **B** (skyline edge) |
| E of Ch / 18th–Wall | Doric Portico (`59565135`) + Jalisco Rest (`59571277`) + WestAmerica (`59575962`) | `filler_east` | `(879.9,-781.4)-(950.0,-667.6)` | `(539,-5957)-(1380,-4591)` | `70.1×113.8` | `0.0..44.0` (`0..528`) | No | **C** (edge) |
| E of Ch / Wall–19th | WestAmerica Mansard (`59486247`) | `filler_east` | `(893.6,-603.6)-(933.8,-550.7)` | `(703,-3823)-(1186,-3188)` | `40.2×52.9` | `0.0..30.6` (`0..367`) | No | **C** (edge) |
| E of Ch / 19th–Serv | Jalisco Jewelers 4F (`59565032`) + Stage Fright (`59571160`) | `filler_east` | `(867.6,-430.5)-(950.0,-310.9)` | `(391,-1746)-(1380,-311)` | `82.4×119.6` | `0.0..53.5` (`0..642`) | No | **B/C** (edge) |
| E of Ch / Serv–20th | Timeless Furnishings (`59487737`, clipped) | `filler_east` | `(873.6,-271.4)-(950.0,-157.8)` | `(463,163)-(1380,1526)` | `76.4×113.6` | `0.0..49.3` (`0..592`) | No | **C** (edge) |
| E of Ch / 20th–21st | Buena Vista Museum / Aura / Foxtail (`60080339`, clipped) | `filler_east` | `(885.2,-88.6)-(950.0,175.0)` | `(602,2357)-(1380,5520)` | `64.8×263.6` | `0.0..33.1` (`0..397`) | No | **B/C** (edge) |
| E of Ch / N of 21st | Kern CCD (`60081751`, clipped) | `filler_east` | `(882.0,257.5)-(950.0,275.0)` | `(564,6510)-(1380,6720)` | `68.0×17.5` | `0.0..32.0` (`0..384`) | No | **C** (edge) |

### 4.2 Major Surface Parking Lots & Open Plazas (OSM Tier D Inventory)
| Lot / Plaza | OSM ID | Block | D-Feet `(X0,Y0)-(X1,Y1)` | Dimensions (ft) | Area (sq ft) | Notes |
|---|---|---|---|---|---|---|
| **Dagny's North Lot** | `1183503876` | H–Eye / 20th–21st | `(291.7,-30.4)-(417.6,177.2)` | `125.9×207.6` | `26,137` | Huge empty asphalt lot directly north of Dagny's |
| **Central Eye St Lot** | `1183500273` | H–Eye / Serv–20th | `(243.0,-295.8)-(419.3,-177.2)` | `176.3×118.6` | `20,909` | Dead-center lot across Eye St from Sandrini's (has 11-ft kiosk + partial overlap w/ `59483191`) |
| **Bare/Legion Mid-Lot** | `1183503877` | H–Eye / 20th–21st | `(151.5,-87.3)-(277.2,44.0)` | `125.7×131.3` | `16,504` | Open asphalt lot between Bare Studios & American Legion (joins `1183503876`!) |
| **NW 19th & G Lot** | `1183500275` | G–H / 19th–Serv | `(-196.6,-431.5)-(-85.0,-306.1)` | `111.6×125.4` | `13,995` | Completely empty asphalt corner lot across 19th from Nile Theater |
| **South-of-20th Lot** | `1183500274` | G–H / Serv–20th | `(-78.8,-289.3)-(72.4,-229.4)` | `151.2×59.9` | `9,057` | Behind `760730139`, directly south of Fox Theater's block |
| **Greyhound Demolished Lot** | `59321997` | W of G / 18th–Wall | `(-340.0,-785.7)-(-271.0,-662.3)` | `69.0×123.4` | `8,515` | Former Greyhound site west of Old Post Office |
| **SE 20th & Chester Lot** | *(in `dagnys.py`)* | Eye–Ch / 20th–21st | `(640.0,-21.2)-(771.0,37.0)` | `131.0×58.2` | `7,624` | Fenced vacant lot between `59522422` & 20th Place |
| **South of Garage Lot** | `1183498282` | H–Eye / S of 18th | `(149.2,-900.0)-(350.3,-862.7)` | `201.1×37.3` | `7,501` | Open strip across 18th St from Parking Garage |
| **Nile East Lot** | `1183498308` | G–H / Wall–19th | `(10.6,-628.8)-(73.5,-517.4)` | `62.9×111.4` | `7,007` | Corner asphalt lot at SW 19th & H St — gives 151.6-ft open width across H St! |
| **H–Eye Mid-Block Lot** | `1183500272` | H–Eye / 19th–Serv | `(262.0,-433.8)-(307.3,-314.7)` | `45.3×119.1` | `5,395` | Between Ovation Theatre and Tegeler/JIN Sushi |
| **21st & H–Eye Const. Lot** | `1183508928` | H–Eye / N of 21st | `(155.4,257.1)-(425.7,275.0)` | `270.3×17.9` | `4,838` | Green-fenced north-edge strip |
| **W of G Mid-Block Lot** | `1183503878` | W of G / 20th–21st | `(-340.0,46.8)-(-266.2,112.0)` | `73.8×65.2` | `4,812` | Open lot west of G St |

---

## 5. Replaceable Buildings Summary & Candidate Slots for the 4 Merged Landmarks

### 5.1 Incoming Landmark Target Footprints (Reference Sizing)
Measured directly from existing repo generators (`source/mm_tools/goldenwest/gw_lib.py`, `source/mm_tools/make_bklan.py`, `source/mm_tools/bklan_sign.py` — cross-reference with `@landmarks-scout`'s `docs/bakersfieldish_landmarks_inventory.md`):

| Landmark | Source | Local Building Footprint (ft) | Height Envelope (ft) | Recommended Parcel / Site Size (ft) | Key Visual / Gameplay Needs |
|---|---|---|---|---|---|
| **Golden West Casino** | `source/mm_tools/goldenwest/` (`gw_lib.py`) | **`156.3 × 161.4`** (`CASINO_BOUNDS_FT`) | Parapet `21.5`, **Rotunda Dome `34.0`** | **`180 × 180` to `280 × 270`** (with front parking apron & neon pylon) | Iconic SE rounded corner rotunda (`R=23.1 ft`), neon marquee, full enterable card room / bar / lobby. |
| **The Great Castle** | `source/mm_tools/goldenwest/` (`gw_gc_ext/int.py`) | **`77.5 × 71.5`** (`GC_BLDG_BOUNDS_FT`) | Parapet `16.5`, **SW Watchtower `19.5`** | **`115 × 115` to `180 × 125`** (with compact court & curb pylon sign) | White crenellated fortress walls, merlons, SW watchtower, red awning, `GREAT CASTLE RESTAURANT` neon pylon, enterable dining/vestibule/BOH. |
| **Larry's Warehouse** | `source/mm_tools/make_bklan.py` (`B76` + lot + `B45`) | **Full Compound: `196 × 164`** (`B76` `86×163` + `55 ft` LAN lot + `B45/130A` `55×161`); **Compact: `128 × 196`** (trim unused closed storage bays) | Parapet `18–20`, antenna `~30` | **`210 × 175`** (un-trimmed 1:1) OR **`128 × 210`** (90°-rotated compact) | Unit `130A` B-LAN Party Hall + roll-up + dumpster + `B-LAN 130A ENTER` cone + central LAN courtyard + Room `120A` battery/LAN shop. |
| **The Bakersfield Sign** | `source/mm_tools/bklan_sign.py` | **Full 1:1: `97.0 ft` tower c-to-c** (`107 ft` base, `111 ft` eaves) × `14 ft` deep; **Adapted: `~80–82 ft` c-to-c** (`94 ft` eaves) | Peak **`31.0 ft`**, arch clearance **`17.5–23.1 ft`** | Spans a **`48–66 ft` roadway** + **`≥ 45 ft` clear street/lot runway** for toppling! | Iconic neon yellow/navy `BAKERSFIELD` arch; **must be destructible and topple over cleanly** without clipping into building walls. |

### 5.2 Replaceable Block & Building Inventory (Tier C + Tier D Targets)
Every block listed below contains **ZERO Tier S anchors** and **ZERO Tier A enterable downtown venues** (except Dagny's, which is preserved cleanly at the south edge of `H–Eye / 20th–21st`):

1. **`Eye–Chester / 20th–21st` Full Block (`D: 495..776 × -95..175`, net `281 × 270 ft`)** — Replaces 3 generic solid-mass buildings (`AT&T 59518832`, boarded `59522422`, 1F strip `59521020`) + fenced vacant lot + optional `20th Place` stub. **Best large-block canvas in the map.**
2. **`H–Eye / 20th–21st` North & West (`D: 152..424 × -18..178`, net `272 × 196 ft`, preserving Dagny's Coffee!)** — Replaces 2 massive empty surface lots (`1183503876` + `1183503877`, 42,600 sq ft!) + solid-mass American Legion (`59520322`). Optionally also drop Bare Studios (`59516526`) to open `x = 152..278` directly onto 20th St across from Fox Theater.
3. **`G–H / 19th–20th` Full Block (`D: -202..75 × -438..-160`, net `277 × 278 ft`)** — Replaces 2 huge parking lots (`1183500275` + `1183500274`) + generic solid-mass `59507032` & `760730139` (and optionally solid-mass Tevis Block `59568189`). Directly between Fox Theater and Nile/Padre along H St!
4. **`G–H / 20th–21st` West Half (`D: -200..-72 × -92..182`, net `128 × 274 ft`)** — Replaces 2 generic windowless warehouses (`59520411` + `59523847`) + parking lot right across Fox West Alley from the Fox Theater.
5. **`H–Eye / Service–20th` Central Lot (`D: 248..428 × -290..-170`, net `180 × 120 ft`)** — Replaces empty lot `1183500273` + tiny attendant kiosk + optionally solid-mass `59483191` (Sub Station/SWAT PC). Dead center of downtown across Eye St from Sandrini's!
6. **`G–H / 19th–Service` West Lot (`D: -204..-86 × -440..-315`, net `118 × 125 ft`)** — Replaces **ZERO buildings** (pure empty asphalt lot `1183500275` across 19th St from Nile Theater).
7. **`H–Eye / Wall–19th` West/Full Half-Block (`D: 152..288 × -634..-515`, net `136 × 119 ft`; or full `272 × 119 ft`)** — Replaces solid-mass `59490021` (and optionally `59474361`), directly north of the Parking Garage across Wall St.
8. **`G–H / 20th–21st` North of Fox (`D: -40..76 × 94..185`, net `116 × 91 ft`)** — Replaces only Today Cleaners (`848207739`) canopy immediately north of Fox stagehouse.

---

### 5.3 Concrete Candidate Replacement Slots (Recommended Master Plan + Alternatives)

#### Landmark 1: Golden West Casino (`156.3 × 161.4 ft`, dome `34 ft`)
| Option | Block & Replaces | Exact Slot Coordinates (D ft / Map Units) | Available Footprint | Orientation & Height Envelope | Assessment |
|---|---|---|---|---|---|
| **GW-A (RECOMMENDED)** | **`Eye–Chester / 20th–21st`**<br>Replaces `AT&T 59518832`, boarded `59522422` + lot, `59521020`, `20th Place` | **D:** `X = 495..776, Y = -95..175`<br>**U:** `X = -4080..-708, Y = 2280..5520` | **`281 × 270 ft`**<br>(`3,372 × 3,240 u`) | Building in NW/NE quadrant (`156×161`), **rotunda facing SE toward 20th & Chester** (or rotated 90° CCW to face **SW toward 20th & Eye / Dagny's / Fox**). Height `34 ft` (was `61 ft` AT&T — opens skyline!). | **Best overall fit.** 100% 1:1 un-trimmed casino + 100-ft parking forecourt & marquee pylon; zero enterable landmarks lost; anchors NE quadrant! |
| **GW-B (Spine Alt)** | **`G–H / 19th–20th`**<br>Replaces `59507032`, `760730139`, `Tevis 59568189` + 2 lots + local Service St | **D:** `X = -202..75, Y = -438..-160`<br>**U:** `X = -12444..-9120, Y = -1836..1500` | **`277 × 278 ft`**<br>(`3,324 × 3,336 u`) | Building at `X = -165..0, Y = -385..-220` with **SE rotunda facing 19th & H St** (`+75 ft` forecourt along H St). Height `34 ft` (keeps Fox↔Padre upper tower sightline open!). | Puts Golden West Casino right on H St between Fox & Padre; trades away Tevis Block facade. |

#### Landmark 2: Larry's Warehouse (`196 × 164 ft` full B76+Lot+B45 compound; `128 × 196 ft` compact)
| Option | Block & Replaces | Exact Slot Coordinates (D ft / Map Units) | Available Footprint | Orientation & Height Envelope | Assessment |
|---|---|---|---|---|---|
| **LW-A (RECOMMENDED)** | **`H–Eye / 20th–21st` North & West**<br>Replaces huge lots `1183503876` + `1183503877` + solid-mass American Legion `59520322` (**keeps Dagny's Coffee intact!**) | **D:** `X = 152..424, Y = -18..178`<br>**U:** `X = -8196..-4932, Y = 3204..5556` | **`272 × 196 ft`**<br>(`3,264 × 2,352 u`) | **Zero rotation needed!** `196 ft` E–W (`X = 190..386`) × `164 ft` N–S (`Y = 5..169`): B76/120A on west, 55-ft LAN courtyard opening onto 21st St (or south toward Dagny's!), B45/130A on east. Height `20–30 ft`. | **Best 1:1 fit.** Fits the ENTIRE un-trimmed B-LAN compound on 42k sq ft of dead asphalt directly east of Fox Theater & west of GW-A! Zero enterable venues lost. |
| **LW-B (Industrial Alt)** | **`G–H / 20th–21st` West of Fox West Alley**<br>Replaces windowless warehouses `59520411` + `59523847` + lot | **D:** `X = -200..-72, Y = -92..182`<br>**U:** `X = -12420..-10884, Y = 2316..5604` | **`128 × 274 ft`**<br>(`1,536 × 3,288 u`) | Rotate 90° (`196 ft` N–S × `~128 ft` E–W, trimming ~35 ft of unused closed bays off B76/B45; keeps 100% of Unit 130A, Room 120A & LAN lot opening onto G St / 20th St). Height `20–30 ft`. | Ultra-natural thematic fit (replaces generic warehouses right beside Fox Theater!); requires ~35 ft trim of closed storage bays. |

#### Landmark 3: The Great Castle (`77.5 × 71.5 ft` fortress, `19.5 ft` SW watchtower)
| Option | Block & Replaces | Exact Slot Coordinates (D ft / Map Units) | Available Footprint | Orientation & Height Envelope | Assessment |
|---|---|---|---|---|---|
| **GC-A (RECOMMENDED)** | **`H–Eye / Service–20th` Central Lot**<br>Replaces empty lot `1183500273` + 11-ft kiosk (+ optionally solid-mass `59483191` Sub Station/SWAT PC) | **D:** `X = 248..428, Y = -290..-170`<br>**U:** `X = -7044..-4884, Y = -60..1380` | **`180 × 120 ft`**<br>(`2,160 × 1,440 u`) | Building at `X = 285..363, Y = -265..-193` (or against west side `260..338`), **crenellated facade + SW watchtower facing Eye St / 20th St** with `~65 ft` forecourt & `GREAT CASTLE RESTAURANT` neon pylon right on Eye St! Height `19.5 ft` (keeps PG&E 136-ft radio tower at `x=258` or shifts it cleanly). | **Dead-center downtown showcase!** Replaces a dead asphalt lot right across Eye St from Sandrini's, 1 block SE of Fox, 1 block S of Dagny's & LW-A. |
| **GC-B (Zero-Demolition Alt)** | **`G–H / 19th–Service` West Lot**<br>Replaces **ZERO buildings** — pure empty lot `1183500275` | **D:** `X = -204..-86, Y = -440..-315`<br>**U:** `X = -12468..-11052, Y = -1860..-360` | **`118 × 125 ft`**<br>(`1,416 × 1,500 u`) | Building at `X = -168..-90, Y = -392..-320`, **SW watchtower & red barrel awning facing 19th & G St** + 48-ft south/west forecourt & pylon sign! Height `19.5 ft`. | **Zero buildings demolished!** Direct cross-street view from Nile Theater, 1 block N of Padre/Post Office. |
| **GC-C (Garage-View Alt)** | **`H–Eye / Wall–19th` West Half**<br>Replaces solid-mass `59490021` + mid-block lot | **D:** `X = 152..288, Y = -634..-515`<br>**U:** `X = -8196..-6564, Y = -4188..-2760` | **`136 × 119 ft`**<br>(`1,632 × 1,428 u`) | Faces **H St & 19th St** (directly north of Parking Garage across Wall St and directly east of Bakersfield Sign S1!). Height `19.5 ft`. | Awesome vertical view of castle crenellations from Parking Garage L6 roof & Padre upper floors! |

#### Landmark 4: The Bakersfield Sign (Destructible Arch — `97 ft` c-to-c full 1:1 or `~80 ft` c-to-c adapted, `31 ft` peak, `17.5–23.1 ft` road clearance)
| Option | Location & Span | Exact Slot Coordinates (D ft / Map Units) | Available Span & Topple Runway | Scale & Sightlines | Assessment |
|---|---|---|---|---|---|
| **S1 (RECOMMENDED — HERO SPINE)** | **Arching across H Street (`Padre ↔ Fox` Corridor, just south of 19th St at Nile Lot)** | **D:** Centre `(113.0, -565.0)`, Span `X = 66..160`, Depth `Y = -572..-558`, `Z = 0..31.0 ft`<br>**U:** Centre `(-8664, -3360)`, `X = -9228..-8100, Y = -3444..-3276, Z = 0..372` | **Clear facade gap `151.6 ft`** (`x = 11.1..162.6`, road curbs `87..139`).<br>**Topple runway:** `>120 ft` open H St roadway N & S (`52 ft` wide) + `76×111 ft` open Nile Lot immediately west! | **~82% width (`80 ft` tower c-to-c, `94 ft` eaves)** so west tower sits on Nile Lot apron (`x = 68..78`) and east tower sits on H St east sidewalk (`x = 148..158`, `4.6 ft` clear of `59490021`). Full `31 ft` height. | **Unbeatable iconic framing!** Frames **Fox Theater** looking north and **Padre Hotel** looking south; visible from Padre upper suites & Garage L6; clean unobstructed fall onto H St! *(If paired with GC-C clearing `59490021`, even 100% 1:1 `97 ft` c-to-c fits!)* |
| **S2 (1:1 UNSCALED BOULEVARD)** | **Arching across Chester Avenue (`20th & Chester` Gateway, in front of GW-A Casino & Jerry's)** | **D:** Centre `(821.0, -175.0)` (or `-555.0`), Span `X = 765.5..876.5`, Depth `14 ft`, `Z = 0..31.0 ft`<br>**U:** Centre `(-168, 1320)`, `X = -834..+498, Z = 0..372` | **Clear facade gap `114–124.5 ft`** (`x = 769..893.5`, road curbs `788..854`).<br>**Topple runway:** `66 ft` wide Chester Ave open N & S! | **100% 1:1 unscaled (`97.0 ft` c-to-c, `111 ft` eaves)** — matches original 62-ft Sillect Ave geometry to the foot! | Zero scaling required; grand eastern boulevard entry into Golden West Casino & Jerry's. Slightly further from Padre/Fox core. |
| **S3 (EYE ST PLAZA ENTRY)** | **Arching across Eye Street Plaza (`19th–20th`, framing Sandrini's & GC-A Great Castle)** | **D:** Centre `(462.0, -255.0)`, Span `X = 415..509`, Depth `14 ft`, `Z = 0..31.0 ft` | **Clear gap `255.6 ft`** on west side (Lot `1183500273`); east tower sits at Sandrini's plaza curb (`x = 490..499`). | ~80% width (`78–80 ft` c-to-c). Topples cleanly N or S down Eye St (`46 ft` roadway). | Great central plaza gateway linking Great Castle, Sandrini's, Dagny's & Garage; doesn't sit on the Padre↔Fox H St spine. |

---

### 5.4 Recommended Cohesive Master Layout ("Scheme A" — Zero Enterable Venues Lost)

```text
  Y=+275  ================ 21st Street (North Map Edge) ================
           [W] | [Warehouses]  [Today Cln] | [ LARRY'S WAREHOUSE (LW-A) ] | [ GOLDEN WEST CASINO (GW-A) ] | [E]
               |  (or LW-B)  [FOX THEATER] |  (272x196 ft, 1:1 compound)  |  (281x270 ft, 1:1 + plaza)    |
               |             [CLOCK TOWER] | [Bare]  [DAGNY'S COFFEE (A)] |     (Rotunda -> 20th/Eye)     |
  Y=-135  ================ 20th Street =================================
           [W] | [59507032]  [760730139]   | [PG&E+136ft] [ GREAT CASTLE ]| [SANDRINI'S]  [Stars/Bank]    | [E]
  Y=-306  ---- | ---- Service St ----      | --- Service   (GC-A 180x120) | ---- Service St ----          | ---
           [W] | [Lot(GC-B)] [Tevis Blk]   | [19th/H Htl] [JIN / Tegeler] | [Tina Marie / SheShed / 1915] | [E]
  Y=-475  ================ 19th Street =================================
           [W] | [NILE THEATER (A)] [Lot]  || [59490021]  [Cristal/Crites]| [Tattoo]   [JERRY'S PIZZA (A)]| [E]
  Y=-565       |                   === [BAKERSFIELD SIGN (S1)] === (H St) |                               |
  Y=-650  ---- | ---- Wall St ----         || ---- Wall St ----           | ---- Guthrie's Alley ----     | ---
           [W] | [Clover/PO] [PADRE HOTEL] || [1812 H] [ 18th & EYE      ]| [Mama Rmb][GUTHRIE'S][Mike's] | [E]
               |             [  (SACRED) ] || [SW Lot] [ PARKING GARAGE  ]|                               |
  Y=-823  ================ 18th Street =================================
           [W] | [Central Acad / 1715 18th]| [Open Lot]  [59479688]       | [Charrito] [Chain Cohn Clark] | [E]
  Y=-900  ==============================================================
           X=-340   G=-232         H=+113               Eye=+462                 Chester=+821         X=+950
```

**Why Scheme A feels like ONE coherent post-apocalyptic Bakersfield:**
- **Every sacred downtown anchor is 100% preserved in place:** Padre Hotel, Fox Theater, 18th & Eye Parking Garage, plus ALL four existing enterable downtown venues (Nile, Dagny's, Sandrini's, Jerry's/Guthrie's).
- **Every single one of the 4 incoming landmarks fits at full 1:1 interior/exterior fidelity** without awkward glue-on borders or disconnected "theme-park wings" — each snaps cleanly to Bakersfield's real downtown street curbs and sidewalks.
- **Iconic Hero Sightlines:** Standing on H St by the Padre Hotel looking north, the player sees **18th & Eye Parking Garage** to the right, **The Bakersfield Sign** arching majestically over H St ahead, and the **Fox Theater Clock Tower** rising behind it — while **The Great Castle**, **Larry's Warehouse**, and **Golden West Casino** form a seamless northeast combat crescent connected by 20th St, Eye St, and Chester Ave!

*(Alternative "Scheme B — H-St Hyper-Dense": If the coordinator prefers Golden West Casino directly between Fox & Padre instead of NE on Chester, move Golden West Casino to **GW-B** (`G–H / 19th–20th`, replacing Tevis + `59507032` + `760730139`), put Larry's Warehouse in **LW-A** (`H–Eye / 20th–21st`), Great Castle in **GC-A** (`H–Eye / Service–20th`), and Bakersfield Sign in **S1** (`H St` at `y = -565`) or **S2** (`Chester Ave`).)*

---

## 6. Map Naming, Levelshots, Menu Entries, Maplists & QC Integration Checklist

### 6.1 Map Naming Convention
All shipped maps use **lowercase ASCII identifiers without hyphens or spaces** (`bakersfielddowntown`, `morrorock`, `bklan6`, `spruce`, `soi6`, `soicowboy_bkk`, `practice`, `dm6`).
- **Recommended BSP filename:** **`bakersfieldish`** → `maps/bakersfieldish.bsp` + `maps/bakersfieldish.lit` (loose files in `maps/`, never inside `bakersfield.pk3`).
- **Display title:** `"Bakersfield-ish"` (Host menu) / `"BAKERSFIELD-ISH"` (Loading screen).
- **Custom assets overlay PK3 (per `AGENTS.md`):** `zz_bakersfieldish.pk3` (lowercase, reproducible zip timestamps `(1980,1,1,0,0,0)`, sorted paths, CI-generated from `source/mm_tools/` or `source/downtown/` with cache key in `.github/workflows/build-zip.yml`).

### 6.2 Every Repo File Requiring a `bakersfieldish` Registration Entry
| File | Location / Line | What Exists for `bakersfielddowntown` | Required Addition for `bakersfieldish` |
|---|---|---|---|
| **Map binaries** | `maps/` (loose) | `bakersfielddowntown.bsp`, `bakersfielddowntown.lit` | `maps/bakersfieldish.bsp`, `maps/bakersfieldish.lit` |
| **Levelshot** | `levelshots/` (loose) | `levelshots/bakersfielddowntown.jpg` (**512×320** JPEG; auto-discovered by `menu_ui.qc:BM_InitLevelshots()`) | `levelshots/bakersfieldish.jpg` (**512×320** JPEG) |
| **MenuQC — Host Menu** | `source/menu_qc/menu_host.qc` L3, L16–38 | `HOST_MAP_COUNT = 8`; `i == 2` → `"bakersfielddowntown"` / `"Bakersfield Downtown"` | Increment `HOST_MAP_COUNT` (`8 → 9`), add `"bakersfieldish"` / `"Bakersfield-ish"` |
| **MenuQC — Loading Screen** | `source/menu_qc/menu_loading.qc` L67 | `if (m == "bakersfielddowntown") return "BAKERSFIELD DOWNTOWN";` | Add `if (m == "bakersfieldish") return "BAKERSFIELD-ISH";` |
| **Server Config** | `server.cfg` L40–41 | `bm_maplist` & `bm_votemaps` include `bakersfielddowntown` | Add `bakersfieldish` to `bm_maplist` & `bm_votemaps` (when ready for rotation) |
| **Client Menu BG** | `autoexec.cfg` L80 *(not `config.cfg`!)* | `seta menu_background_map "soi6 soicowboy_bkk bakersfielddowntown"` | Optionally append `bakersfieldish` |
| **Server QC — Bot Waypoints** | `source/qc_combat_decomp/bm_bots.qc` L892–897, L1276–1277 | `BM_DtWayInBounds` clamps downtown bot waypoints to `X [-14100, 1380], Y [-7380, 6720]` + triggers downtown grid graph | Add `mapname == "bakersfieldish" \|\| world.model == "maps/bakersfieldish.bsp"` to both checks! |
| **Server QC — Vote Fallback** | `source/qc_combat_decomp/bm_match.qc` L780 | `BM_VoteMapList()` fallback string lists `bakersfielddowntown` | Add `bakersfieldish` to fallback string |
| **Server QC — Street NPCs** | `source/qc_combat_decomp/crowd_npcs.qc` L156, L266 | Precaches HD/MD3 street crowd models on `bakersfielddowntown` | Add `bakersfieldish` if NPCs are included (or omit if post-apocalyptic wasteland has no pedestrians) |
| **Server QC — Rocket Rider** | `source/qc_combat_decomp/rocket_rider.qc` L1386 | Spawns 1 parked Rocket Rider at `'-13910 6470 6'` (NW corner) | Optional: add `bakersfieldish` (or place via map entity) |
| **CSQC — Intro Camera** | `source/qc_combat_decomp/csqc/bm_hud.qc` L1506–1512 | Animated camera panning over Fox Theater (`'-8380 1780 210'` → `'-8490 2440 340'`) | Add `bakersfieldish` intro camera sweeping over H St / Fox / Bakersfield Sign / Padre! |
| **CSQC — Minimap** | `source/qc_combat_decomp/csqc/minimap_bounds.qc` L17–23 & `zz_minimap.pk3` | `mm_map_cx = -6360, mm_map_cy = -330, mm_map_half = 8796.80` + `gfx/minimap/bakersfielddowntown.{png,txt}` | Run `source/mm_tools/build_minimap_pk3.py` after compiling `bakersfieldish.bsp` to generate minimap PNG + update `minimap_bounds.qc` |
| **Server QC — Q1 Surface Probe** | `source/qc_combat_decomp/defs_custom.qc` L11915 | Auto-detects high-poly BSP2 maps (`>12,000` world faces) dynamically — no hardcoded map name needed | Works automatically |
