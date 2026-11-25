# Bakersfield-ish — Landmarks & Map-Compile Inventory (Phase 1)

**Workspace:** `G:\Quake\Combat\BakersfieldQuake`  
**Prepared by:** `landmarks-scout`  
**Scope:** Complete source, geometry, asset/pk3 dependency, transform/trimming, destructibility, and map-compilation inventory for the 4 landmarks to be merged into **Bakersfield-ish**, plus the installed Windows map-compile toolchain and Zircon Engine BSP limits.

---

## 1. Executive Summary

All four target landmarks exist as **1:1 scale (`12 Quake units = 1 foot`) procedural Python map generators** inside `source/mm_tools/` — matching `source/downtown/`'s exact `12 u/ft` scale — and **100% of their required PNG textures (including `_glow.png` fullbright maps) and `.md3` prop models are ALREADY shipped inside `bakersfield.pk3`** (zero custom `.shader` dependencies, zero missing assets when using the current v5/modular sources).

| Landmark | Recommended Source (Python Generator) | Format | Full Parcel Footprint (ft / u) | Trimmed Core Footprint (ft / u) | Core Brushes / Entities | In `bakersfield.pk3`? |
|---|---|---|---|---|---|---|
| **1. Golden West Casino** | `source/mm_tools/goldenwest/{gw_casino_ext.py, gw_casino_int.py}` | Valve 220 (`12 u/ft`) | `329.5 × 575.1 × 32.8 ft`<br>(`3,954 × 6,902 × 394 u`) | **Building + NE Courtyard/Horse:** `158.0 × 167.1 × 32.8 ft` (`1,896 × 2,005 × 394 u`)<br>**Freestanding Pylon:** `12.0 × 17.0 × 28.3 ft` (`144 × 204 × 340 u`) | **1,123 brushes** (26 world) + 9 pylon<br>**43 ents** (`gw_buddha.md3`, `gw_horse.md3`, 41 lights) | **100%** (75 `gwc_*` tex, 9 `_glow`, 2 `.md3`) |
| **2. The Great Castle** | `source/mm_tools/goldenwest/{gw_gc_ext.py, gw_gc_int.py}` | Valve 220 (`12 u/ft`) | `131.0 × 286.0 × 32.0 ft`<br>(`1,572 × 3,432 × 384 u`) | **Main Bldg + Watchtower + Canopy + Rock Garden:** `80.0 × 80.0 × 32.0 ft` (`960 × 960 × 384 u`)<br>**Freestanding Pylon:** `5.2 × 15.0 × 18.6 ft` | **548 brushes** (23 world) + ~12 pylon<br>**28 ents** (28 lights; 0 `.md3`) | **100%** (67 `gwc_*` tex, 5 `_glow`, 0 `.md3`) |
| **3. Larry's Warehouse** | `source/mm_tools/make_bklan.py` + `make_bklan_v{3,4,5,6}.py` (`make_bklan6.py`) | Standard Q1 (`12 u/ft`) | **Full 2-Bldg + Courtyard:** `209.0 × 181.9 × 32.0 ft`<br>(`2,508 × 2,183 × 384 u`) | **B76 (118/120 Warehouse + Mega Man Bedroom):** `89.0 × 165.1 × 26.0 ft`<br>**Courtyard:** `55.0 × 173.0 ft`<br>**B45 (Unit 130A + Bodyworks):** `82.5 × 167.7 × 32.0 ft` (or **Unit 130A hall only:** `55 × 31 × 16 ft`) | **Full Complex:** 928 brushes (301 world), 431 ents (139 `misc_model`, 182 explodable `misc_lan_*`, 3 `bk_tv`)<br>**B76 only:** 432 br, 238 ents<br>**B45 only:** 422 br, 168 ents | **100%** (71 `bk*`/`dan_*` tex, 4 `_glow`, 27 unique `.md3`) |
| **4. The Bakersfield Sign** | `source/mm_tools/bklan_sign.py` + `make_bklan_v2.py` + `make_bklan_v5.py` | Standard Q1 (`12 u/ft`) | **With hedges/pads:** `15.7 × 112.0 × 31.0 ft` (`188 × 1,344 × 372 u`) | **Pure Arch + 2 Towers:** `14.0 × 111.0 × 31.0 ft` (`168 × 1,332 × 372 u`)<br>**Tower center spacing:** `97.0 ft` (`1,164 u`); **Clear road span:** `87.0 ft` (`1,044 u`) | **108 brushes** (all `func_detail`: 42 N-tower + 42 S-tower + 24 arch)<br>**0 `.md3`** (optional 20 accent lights) | **100%** if using v5 **`bk5_bsign`** (`2048×320`); **NOTE:** old v2 `bk_bsign` is **missing** from pk3! |

### Critical Technical Findings Upfront
1. **Mixed Standard Q1 + Valve 220 `.map` Proven Working on `qbsp.exe`:** Verified live with `G:\Quake\Combat\tools\ericw\qbsp.exe` (`ericw-tools 2.0.0-alpha11`): a single `.map` file can mix Standard Quake 1 brushes (Downtown + Larry's + Sign) and Valve 220 brushes (Golden West + Great Castle) with **zero errors/warnings** (`-bsp2 -leaktest`). Even better, Valve 220 supports arbitrary-angle rotation with exact UV preservation (`[ ux uy uz uoff ] [ vx vy vz voff ]`).
2. **Do NOT run `goldenwest/build_textures.py` or `build_v*_textures.py` blindly into `BakersfieldQuake/textures/`:** Per `AGENTS.md`, loose files beat pk3s and base `bakersfield.pk3` must never be edited. All landmark PNGs already live in `bakersfield.pk3`, while `gw2.wad`, `bklan4.wad`, `bklan5.wad`, and `bklan6.wad` are currently **not on disk** in `source/mm_tools/out/maps/`. For `qbsp.exe` compile-time texture dimensions, synthesize a combined compile-only WAD2 inside `source/downtown/out/` (extracting miptex headers directly from `source/mm_tools/goldenwest/out/goldenwest.bsp` and `maps/bklan6.bsp`, or `bakersfield.pk3` PNG headers) and strip embedded miptex pixels post-light via `strip_miptex_pixels.py`.
3. **Only `G:\Quake\Combat\tools\ericw\` exists on this Windows host** (`D:\vibe\quake1opensource\tools\ericw` and `G:\Quake\TRUEDM3\tools\ericw` referenced in legacy scripts do not exist). All 16 CPU threads are available.
4. **Zircon Engine Limits (verified from `G:\Quake\_bq_fork_engine\src\`):**
   - `MAX_MODELS_8192 = 8192` (under `PROTOCOL_DARKPLACES7`, so inline `*1..*N` destructible brush submodels have massive headroom beyond `bakersfielddowntown.bsp`'s current 275 models).
   - `MAX_EDICTS_32768 = 32768`, `MAX_SOUNDS_4096 = 4096`, `MAX_LIGHTSTYLES_256 = 256`, `MAX_STATICENTITIES_4096 = 4096`.
   - **Zero BSPX support in Zircon** — use native WAD2 miptex downsampling (as in `make_downtown.py`) if lightmap size needs dieting.
   - **Worldspawn `"wad"` key hard cap: 127 characters** — always merge WADs into a single combined compile WAD (`dt_all.wad` pattern).
   - **Avoid `func_detail_wall` hull-0 visleaf bloat** (caused `32,209` visleafs / `116+ MB` PVS matrix in downtown); keep solid building exteriors as structural `worldspawn` and interior/facade greebles as `func_detail` / `func_detail_illusionary`.

---

## 2. Existing Merge & Composer Infrastructure

Before detailing each landmark, these existing repo tools provide proven patterns for composing multi-source Quake maps in `BakersfieldQuake`:

| File | Role & Capabilities | Notes for Bakersfield-ish |
|---|---|---|
| `source/HANDOFF_MERGE_MAPS_GENERIC.md` | Architecture playbook ("Gauntlet Loop"): single shared frame (`12 u/ft`), composer with plug-in `build(ctx)` / `post(ctx)` pieces, single merged WAD (<127-char `wad` key), fast `DT_WINDOW` test builds, lighting presets (`r_hdr_scenebrightness`), vis/fog performance budgets. | Directly governs how `source/downtown/` was built. |
| `source/downtown/tools/make_downtown.py` | Master composer for `bakersfielddowntown.bsp`. Merges 21 WADs into `dt_all.wad` (with optional miptex downsampling for lightmap density control), runs piece plugins (`source/downtown/pieces/*.py`), handles `DT_WINDOW` slicing, and writes Standard Q1 `.map`. | **Recommended host composer** to fork/extend for Bakersfield-ish (or add new piece modules under a dedicated `bakersfieldish` build path without breaking `bakersfielddowntown`). |
| `source/downtown/tools/dt_mapio.py` | Float-capable Standard Q1 `.map` reader/writer with UV-preserving `Brush.moved(d)`, `Brush.clipped(win)`, and `Ent.moved(d)`. | Does **not** parse Valve 220 faces or rotate brushes yet — needs either a Valve 220 parser/transformer (for Golden West & Great Castle) or direct import of `gw_casino_*` / `gw_gc_*` via a thin transform wrapper around `MapBuilder`. |
| `source/downtown/tools/dt_ctx.py` | Shared piece context (`ctx`) with `world`/`detail`/`fence`/`illus`/`clip` brush groups, `box()`, `prism()`, `ent()`, `light()`, `Fit`, `tspec`. | Can easily accept raw Valve 220 brush strings in its group lists since `qbsp.exe` accepts mixed Standard + Valve 220. |
| `source/mm_tools/bks_mapio.py` | Integer-coordinate Standard Q1 `.map` reader/window-cutter/mover used by `make_bakolansmall.py` and `make_bklan_v5.py` / `v6.py`. | Superseded by float-capable `dt_mapio.py`, but useful reference for cutting `make_bklan.py` windows (exact Larry's & Sign cut windows already documented in `make_bakolansmall.py:71-76`). |
| `source/mm_tools/make_bakolansmall.py` | Prior proof-of-concept merging Legacy Golden West Casino + Larry's Warehouse + Bakersfield Sign + ORCOM onto one stretch of Union Ave, with `SKY_Z = 2500 ft` (`30,000 u`). | Useful reference for high-skybox settings (`SKY_Z`), entity stripping (`DROP`), and jump-pad math; see also `docs/BAKOLANSMALL_NOTES.md`. |
| `source/mm_tools/make_bklan6.py` + `make_bklan_v6.py` + `make_bklan_v7.py` | Prior city merge combining Larry's Warehouse + Legacy Golden West + Bakersfield Sign + old Fox/Padre (`fox.map`), with `SKY_Z = 280 ft`, structural VIS walls, and LAN entity thinning. | Shows how `make_bklan.py` layers `v2`..`v7` via `exec()` and how `bklan6` thinned ~30% of LAN chair/monitor/PC entities to save edicts. |

---

## 3. Landmark-by-Landmark Inventory

### 3.1 Golden West Casino (1001 S Union Ave)

#### A. Source Files & Two Existing Versions
Two complete implementations exist in the repo. **Use the Modular 2026 version (`source/mm_tools/goldenwest/`)** — it is vastly higher fidelity, exact 1:1 OSM footprint, zero legacy texture clutter, cleanly split into interior/exterior sub-builders, and passes Hull-1 (`32×32×56`) navigation validation.

* **Recommended (Modular 1:1, Valve 220):**
  * `source/mm_tools/goldenwest/gw_lib.py` — Shared `12 u/ft` coordinate contracts (`CASINO_POLY_FT`, `CASINO_BOUNDS_FT`, `CASINO_LOT_FT`, `CASINO_ROTUNDA_*`), Valve 220 `MapBuilder`, Hull-1 validator.
  * `source/mm_tools/goldenwest/gw_casino_int.py` (1,598 lines) — Enterable casino shell & all 7 interior zones (`build_casino_int(mb)`).
  * `source/mm_tools/goldenwest/gw_casino_ext.py` (1,337 lines) — Roof superstructure, 12-sided conical rotunda roof, NE 45° portico, courtyard monuments (bronze horse), freestanding purple neon pylon, guard booth, Union frontage, parking lot (`build_casino_ext(mb)`).
  * `source/mm_tools/goldenwest/make_gw.py` — Master orchestrator combining Casino + Great Castle + Union corridor.
  * `source/mm_tools/goldenwest/build_textures.py` — 100% procedural PIL/NumPy generator for `gwc_*.png`, `{gwc_*.png`, `*_glow.png`, and `gw2.wad`.
  * `source/mm_tools/goldenwest/compile_gw.py` & `source/mm_tools/build_goldenwest.sh` — Compile pipeline.
  * **Prebuilt outputs & audits on disk:** `source/mm_tools/goldenwest/out/goldenwest.map` (4.23 MB), `goldenwest.bsp` (22.4 MB), `goldenwest.lit`, `compile_stats.json`, `texture_manifest.json`, `AUDITS_LOG.md`, `goldenwest_showcase.html`; also archived at `G:\Quake\Combat\_removed_maps_2026-11-23\maps\goldenwest.bsp/.lit` and `source/mm_tools/out/maps/goldenwest.bsp`.
* **Legacy (Standard Q1, older `gw_*` / `bk_*` textures — NOT recommended):**
  * `source/mm_tools/make_goldenwest_legacy.py`, `source/mm_tools/gw_casino.py`, `source/mm_tools/gwbase.py` (uses `K = 1.585` traced-aerial correction), `build_goldenwest_textures.py`, `build_gw_casino_textures.py`, `out/maps/goldenwest.wad`. Delegated by `source/mm_tools/make_goldenwest.py` only when `GW_SEG` env var is set (for `bklan6` / `bakolansmall` compatibility).
* **Custom 3D Models:**
  * `source/mm_tools/make_gw_horse.py` → `progs/gw_horse.md3` (`progs/gw_horse.md3_0.skin`, `gw_horse.png`, `gw_pedestal.png`, `gw_rock.png`) — **already in `bakersfield.pk3`**.
  * `source/mm_tools/make_gw_buddha.py` → `progs/gw_buddha.md3` (`progs/gw_buddha.md3_0.skin`, `gw_gold.png`) — **already in `bakersfield.pk3`**.

#### B. Measured Dimensions, Sub-Builder Breakdown & Brush/Entity Counts
All coordinates in `gw_lib.py` local feet (`12 u/ft`, origin `(0, 0)` near center of Casino):

| Sub-Assembly / Function | Local X (ft) | Local Y (ft) | Local Z (ft) | Size W × D × H (ft) | Size (Quake u) | Brushes | Entities |
|---|---|---|---|---|---|---|---|
| `gw_casino_int.build_casino_int` *(walls + 7 interior rooms)* | `-54.1 .. +102.2` | `-71.7 .. +89.7` | `-0.5 .. +16.0` | `156.2 × 161.4 × 16.5` | `1,875 × 1,936 × 198` | **961** *(26 world, 835 detail, 95 illus, 4 fence, 1 clip)* | **37** *(36 light, 1 `gw_buddha.md3`)* |
| `gw_casino_ext._build_roof_superstructure` *(roofs, rotunda cone, NE portico, flags, awnings)* | `-54.5 .. +103.5` | `-77.2 .. +89.9` | `+0.2 .. +31.1` | `158.0 × 167.1 × 30.9` | `1,896 × 2,005 × 371` | **129** | **4** *(lights)* |
| `gw_casino_ext._build_courtyard_monuments` *(NE flagstone plaza + bronze horse monument)* | `+45.4 .. +100.0` | `-2.0 .. +60.0` | `+0.4 .. +32.3` | `54.6 × 62.0 × 31.9` | `655 × 744 × 383` | **33** | **2** *(1 `gw_horse.md3`, 1 light)* |
| **→ RECOMMENDED CORE (Int + Roofs + Courtyard/Horse)** | **`-54.5 .. +103.5`** | **`-77.2 .. +89.9`** | **`-0.5 .. +32.3`** | **`158.0 × 167.1 × 32.8`** | **`1,896 × 2,005 × 394`** | **1,123** *(26 world)* | **43** *(2 `.md3`, 41 lights)* |
| `gw_casino_ext._build_pylon_marquee` *(freestanding purple neon pylon — detach & place curbside!)* | `+149.0 .. +161.0` | `-8.5 .. +8.5` | `+0.2 .. +28.5` | `12.0 × 17.0 × 28.3` | `144 × 204 × 340` | **9** | **2** *(lights)* |
| `gw_casino_ext._build_guard_booth` *(optional)* | `+114.0 .. +166.5` | `+151.0 .. +202.5` | `0.0 .. +13.6` | `52.5 × 51.5 × 13.6` | `630 × 618 × 163` | **51** | **1** |
| `gw_casino_ext._build_union_frontage` *(stone/iron fence)* | `+167.0 .. +172.0` | `-270.0 .. +303.5` | `+0.5 .. +10.0` | `5.0 × 573.5 × 9.5` | `60 × 6,882 × 114` | **40** | **6** |
| `gw_casino_ext._build_lot_pavement_and_plaza` + `_build_parking_details` | `-157.5 .. +172.0` | `-270.9 .. +304.2` | `-0.1 .. +26.2` | `329.5 × 575.1 × 26.3` | `3,954 × 6,902 × 316` | **339** | **8** |
| **FULL PARCEL (`build_casino_ext` + `build_casino_int`)** | `-157.5 .. +172.0` | `-270.9 .. +304.2` | `-0.5 .. +32.3` | `329.5 × 575.1 × 32.8` | `3,954 × 6,902 × 394` | **1,562** *(26 world, 1,248 detail, 273 illus, 13 fence, 2 clip)* | **60** *(58 light, 2 `misc_model`)* |

**Locked Doorways (all Hull-1 compliant `>= 96 u` wide × `108 u` high):**
- Primary **NE 45° Entrance Vestibule**: chord `(43, 7) -> (62.28, -12.28)` (`x + y = 50`, faces **NE / yaw 45°**).
- **South Center Exit**: `x = 24..34, y = -71.6` (10 ft / 120 u wide).
- **SW Service Exit**: `x = -42..-34, y = -68.4` (8 ft / 96 u wide).
- **North Parking Lot Double Exit**: `x = 20..28, y = +70.5` (8 ft / 96 u wide).

#### C. Texture, Model & WAD Dependencies
- **75 unique textures** (all `gwc_*` / `{gwc_*`): **0 missing from `bakersfield.pk3`**.
- **9 glowing emissive textures** with `_glow.png` in `bakersfield.pk3`: `gwc_cashier`, `gwc_menu`, `gwc_pylled`, `gwc_pyltop`, `gwc_security`, `gwc_troffer`, `gwc_tvscr`, `{gwc_bjneon`, `{gwc_lgneon`.
- **2 MD3 models** (`progs/gw_horse.md3`, `progs/gw_buddha.md3`): **0 missing from `bakersfield.pk3`**. Note: `misc_model` entities MUST use key `"mdl"` (not `"model"`), which `gw_casino_*.py` already enforces.
- **0 custom `.shader` files.**
- **WAD2 status:** `gw2.wad` is not currently on disk; extract its 179 miptex headers directly from `source/mm_tools/goldenwest/out/goldenwest.bsp` (Lump 2) into the merged compile WAD so zero loose PNGs are ever written to `BakersfieldQuake/textures/`.

#### D. Key Recognizable Visual Features (Preserve!)
1. **12-sided conical terracotta-shingle Rotunda** on the east flank (`R = 23.1 ft`, apex `29.4 ft` with bronze spire) housing the **Blackjack Lounge Bar** with radial laminated wood arch ribs, curved granite bar, Coors tap towers, 7 leather barstools, and cyan neon `{gwc_bjneon` ("Blackjack") + `{gwc_lgneon` ("Lounge").
2. **45° NE Portico Gable** with clerestory transoms, twin angled US flagpoles (`{gwc_usflag`), and stamped flagstone entrance courtyard featuring the **Cowboy-on-Horse bronze monument** (`progs/gw_horse.md3`).
3. **28.5-ft Fluted Royal-Purple Neon Pylon Marquee** (`gwc_pyltop` + `gwc_pylled` glowing cabinets) — MUST be preserved and placed prominently on the adjacent downtown sidewalk/corner!
4. **Enterable Main Poker Pit** with heavy timber cross-ties, 13 burgundy-red felt oval/octagon tables (no green felt), hanging flat-screen TVs (`gwc_tvscr`), west **2-Bay Cashier Cage** (`gwc_cageshut` corrugated shutters + vault), and the **South Alcove Golden Laughing Buddha Shrine** (`progs/gw_buddha.md3` flanked by gold urns).

#### E. Repositioning, Rotation, Scaling & Trimming Feasibility
- **Very Easy to Trim:** Call ONLY `build_casino_int(mb)`, `_build_roof_superstructure(mb)`, `_build_courtyard_monuments(mb)`, plus the tiny 9-brush NE plaza flagstone slice (from `_build_lot_pavement_and_plaza` lines 408–425) and independently position `_build_pylon_marquee(mb)` at the street edge. This drops 379 parking-lot/fence/guard-booth brushes and shrinks the footprint from `330 × 575 ft` down to a tight **`158 × 167 ft`** urban block (roughly half a downtown city block!).
- **Easy to Reposition & Rotate (90°/180°/270°):** Because every brush is Valve 220, rotating `(x, y)` and texture axis vectors `[ ux uy uz ]`, `[ vx vy vz ]` around a pivot preserves every single texture alignment losslessly (update `misc_model` `angles` yaw + `light` origins too). Best placed on a **SW or NW corner** of a downtown intersection so the **45° NE Portico + Horse Courtyard + East Rotunda** open directly toward the corner intersection!
- **Scaling:** Do **not** shrink below ~85% — interior doorways (`96–120 u`) and table aisles are already tuned tightly to Quake Hull-1 (`32×32×56`). If a slightly narrower lot is needed, trim the BOH/west service wall (`x = -54..-41`, saves ~13 ft) rather than non-uniformly squashing the rotunda.

---

### 3.2 The Great Castle Chinese Restaurant (410 Union Ave)

#### A. Source Files
Built cleanly as a modular subsystem inside `source/mm_tools/goldenwest/`:
- `source/mm_tools/goldenwest/gw_lib.py` — Shared `12 u/ft` coordinate contracts (`GC_POLY_FT`, `GC_BLDG_BOUNDS_FT`, `GC_LOT_FT`, `GC_DOORS_FT`, `GC_TOWER_BOUNDS_FT`, `GC_ANNEX_BOUNDS_FT`).
- `source/mm_tools/goldenwest/gw_gc_int.py` (1,028 lines) — Complete enterable interior & hermetic worldspawn VIS-seal shell (`build_gc_int(mb)`): SW Reception Vestibule, Main Dining Hall, Restroom Alcove, Kitchen/BOH.
- `source/mm_tools/goldenwest/gw_gc_ext.py` (830 lines) — Roofs, castellated parapets & merlons, SW Watchtower + crimson crow's nest, crimson arched barrel-vault entry canopy, SW river-rock garden & monolith, SE Annex, Union pylon sign, lot paving (`build_gc_ext(mb)`).
- **Prebuilt outputs:** Compiled inside `source/mm_tools/goldenwest/out/goldenwest.map` and `goldenwest.bsp`.

#### B. Measured Dimensions, Sub-Builder Breakdown & Brush/Entity Counts
Local `gw_lib.py` feet (`12 u/ft`, anchored around `X = 336..413.5, Y = 996..1067.5`):

| Sub-Assembly / Function | Local X (ft) | Local Y (ft) | Local Z (ft) | Size W × D × H (ft) | Size (Quake u) | Brushes | Entities |
|---|---|---|---|---|---|---|---|
| `gw_gc_int.build_gc_int` *(walls + vestibule, dining hall, restrooms, kitchen)* | `336.0 .. 413.5` | `996.0 .. 1067.5` | `-0.5 .. +12.0` | `77.5 × 71.5 × 12.5` | `930 × 858 × 150` | **408** *(23 world, 328 detail, 50 illus, 7 fence)* | **23** *(lights)* |
| `gw_gc_ext._build_gc_roofs_and_watchtower` *(TPO decks, parapets, merlons, SW Watchtower + crimson crow's nest + mast)* | `336.0 .. 413.5` | `996.0 .. 1067.5` | `+10.5 .. +31.5` | `77.5 × 71.5 × 21.0` | `930 × 858 × 252` | **81** | **0** |
| `gw_gc_ext._build_gc_facades_and_canopies` *(West channel sign, `410` sconce, `城堡` plaque, `OPEN`, 6-seg crimson barrel canopy, E service awning)* | `335.9 .. 414.0` | `987.5 .. 1057.0` | `+0.5 .. +16.5` | `78.0 × 69.5 × 16.0` | `936 × 834 × 192` | **39** | **5** *(lights)* |
| `gw_gc_ext._build_gc_sw_rock_garden` *(SW notch river-rock garden & monolith boulder)* | `334.0 .. 354.0` | `996.0 .. 1067.5` | `0.0 .. +6.1` | `20.0 × 71.5 × 6.1` | `240 × 858 × 73` | **20** | **0** |
| **→ RECOMMENDED CORE (Int + Roofs/Tower + Canopies + Rock Garden)** | **`334.0 .. 414.0`** | **`987.5 .. 1067.5`** | **`-0.5 .. +31.5`** | **`80.0 × 80.0 × 32.0`** | **`960 × 960 × 384`** | **548** *(23 world)* | **28** *(28 lights)* |
| Union Two-Post Pylon (`gw_gc_ext.py:660-672`, "GREAT CASTLE / RESTAURANT" + 6 mini merlons) | `283.0 .. 288.2` | `978.5 .. 993.5` | `+0.17 .. +18.6` | `5.2 × 15.0 × 18.4` | `62 × 180 × 221` | **~11** | **2** *(lights)* |
| `gw_gc_ext._build_gc_se_annex` *(optional white-CMU roll-up annex)* | `379.5 .. 411.4` | `899.0 .. 948.0` | `+0.2 .. +16.0` | `31.9 × 49.0 × 15.8` | `383 × 588 × 190` | **27** | **2** |
| `gw_gc_ext._build_gc_lot_paving` + rest of `_build_gc_signs_fences_props` | `283.0 .. 414.0` | `882.0 .. 1168.0` | `0.0 .. +24.2` | `131.0 × 286.0 × 24.2` | `1,572 × 3,432 × 290` | **~161** | **~3** |
| **FULL PARCEL (`build_gc_ext` + `build_gc_int`)** | `283.0 .. 414.0` | `882.0 .. 1168.0` | `-0.5 .. +31.5` | `131.0 × 286.0 × 32.0` | `1,572 × 3,432 × 384` | **747** *(23 world, 574 detail, 130 illus, 7 fence, 13 clip)* | **35** *(lights)* |

**Locked Doorways (all Hull-1 compliant `84–96 u` wide × `102 u` high):**
- **South Main Entry** (under crimson arched barrel canopy): `x = 362..370, y = 996..997` (8 ft wide, enters SW Watchtower vestibule).
- **North Dining Exit**: `x = 358..365, y = 1066.5..1067.5` (7 ft wide).
- **North Kitchen Exit**: `x = 398..405, y = 1066.5..1067.5` (7 ft wide).

#### C. Texture, Model & WAD Dependencies
- **67 unique textures** (all `gwc_*` / `{gwc_*`, heavily overlapping Golden West Casino's shared concrete/CMU/wood/glass textures): **0 missing from `bakersfield.pk3`**.
- **5 glowing emissive textures** with `_glow.png` in `bakersfield.pk3`: `gwc_gcdome`, `gwc_gclant`, `gwc_gcopen`, `gwc_gcplaque`, `gwc_troffer`.
- **0 MD3 models**, **0 custom shaders** — 100% self-contained brush geometry!
- **WAD2 status:** Shares `gw2.wad` (same Lump 2 extract from `goldenwest.bsp`).

#### D. Key Recognizable Visual Features (Preserve!)
1. **Castellated White CMU Parapets & Merlons** (`gwc_gccmu`, `gwc_gcmerlon`) wrapping the entire roofline (`z = 12..16.5 ft`).
2. **Raised SW Watchtower Bastion (`20 × 14 ft`, `z = 19.5..21.3 ft` merlons) topped with the Signature Crimson Crow's Nest & Mast (`z = 31.5 ft`)**, illuminated yellow **"城堡"** plaque (`gwc_gcplaque`), **"410"** sconce, and **"OPEN"** neon (`gwc_gcopen`).
3. **6-Segment Crimson Arched Barrel-Vault Entry Canopy** jutting `8.5 ft` south (`y = 987.5..996.0`) over the propped-open red double entry doors, flanked by the **SW River-Rock Garden & Monolith Boulder** (`x = 334..354`).
4. **Two-Post Merlon-Capped Pylon Sign ("GREAT CASTLE / RESTAURANT", `gwc_gcpylon`)** — detach lines 660–672 of `gw_gc_ext.py` and place curbside!
5. **Sumptuous Enterable Chinese Restaurant Interior:** Stamped antique-bronze coffered vestibule ceiling (`gwc_gccoff`), dragon-scroll cornice (`gwc_gccorn`), carved oxblood `{gwc_gcfret` lattice bays, `{gwc_gcbann` brocade valance & `{gwc_gcfan` fan, golden dining hall ceiling with **14 glowing hanging lanterns (`gwc_gclant`)**, **Guilin jade mountain mural (`gwc_gcmural`)**, Tang Maple Bridge calligraphy scroll (`gwc_gccallig`), 4 screen-divided booths, **6 Lazy Susan round tables** with crimson chairs, plus pass-through restrooms and stainless wok-hood kitchen!

#### E. Repositioning, Rotation, Scaling & Trimming Feasibility
- **Easiest of all 4 landmarks to place!** At **`80 × 80 × 32 ft` (`960 × 960 × 384 u`)** and only **548 brushes / 28 lights / 0 models**, the entire Great Castle core drops straight onto almost any single mid-block or corner downtown lot!
- **Zero lot bloat needed:** Simply omit `_build_gc_lot_paving`, `_build_gc_se_annex`, and the parking-lot portions of `_build_gc_signs_fences_props` (keeping only the 11-brush merlon pylon sign!).
- **Arbitrary 90°/180°/270° Rotation:** Valve 220 transforms cleanly without UV drift; align the **South Watchtower + Crimson Barrel Canopy** and **West Channel Sign (`gwc_gcwest`)** onto a **NE street corner** (its natural real-world orientation: Watchtower facing South, big `GREAT CASTLE` wall sign facing West!).
- **Do not shrink:** Interior dining aisles (`>= 72 u`) and BOH ceiling (`112 u` clear) are right at Hull-1 minimums.

---

### 3.3 Larry's Warehouse (118/120 E 21st St + Unit 130A B-LAN Party Hall + LAN Courtyard)

#### A. Source Files & Layered Evolution
"Larry's Warehouse" in BakersfieldQuake is a **two-building + central courtyard complex** from the `bklan` map series (`make_bklan.py`, 12 u/ft, Standard Quake 1 `.map`), progressively detailed across versions `v1 -> v6`:
- `source/mm_tools/make_bklan.py` (1,233 lines) — Base geometry:
  - **Building 76 (`118/120 E 21st St`, `B76 = (-229, 24, -143, 187)`):** Street facade (`BATERIAS`, `120A`, `120B` red/blue piers, tall parapet, roof HVACs).
  - **Building 45 (`Celebrity Bodyworks / Unit 130A`, `B45 = (-88, 23, -33, 184)`):** North end (`y = 154..184`, `55 × 30 ft`) is the authentic **2001 `bklan.wmv` Unit 130A B-LAN Party Hall** + back room with sky mural (`bk_mural`), corner bathroom, open roll-up door, galvanized ducting + unit heater, office box, 2001 CRT LAN rows (`misc_lan_table/monitor/pc/chair`), soda bottles, Razor kick scooters, magenta neon rack, and outdoor cardboard-and-foil `B-LAN 130A ENTER ->` delineator cone + mustard dumpster + roof-climb crate stack.
  - **LAN Courtyard (`x = -143..-88, y = 23..187`):** `55 ft`-wide fenced parking lot between B76 and B45 with E 21st rolled-open iron gate, pole light, canopy tents, parked vehicles, and `STOP` / `UNION AVE ->` wall signs.
- `source/mm_tools/make_bklan_v3.py` (lines 159–172, 572–647) — Adds **Larry's Warehouse signs** (`bk3_larry` over 130A roll-up and double-sided roof billboard on B45; `bk3_pylon` street pylon at E 21st courtyard gate) AND hollows out **7 roll-up bays** on B76 east wall + **5 roll-up bays** on B45 west wall.
- `source/mm_tools/make_bklan_v4.py` (lines 59–188) — Transforms B76's entire interior into **Larry's Warehouse Hall** (open concrete hall with joists, tube lights, **70 SimReady industrial pallet racks**, **orange & blue forklifts**, pallet jack, cardboard pallets, **SE LAN Party Bay** & **North TV LAN Pod**) + converts the SW `120A` room (`x = -228..-183, y = 25..61`) into the **Mega Man Bedroom** (carpet, quilt bed with **`progs/bklan/mm_rig.md3` Mega Man sitting on the bed**, CRT desk, rug, poster, bedside lamp) + opens the north courtyard wall walk-out gap (`x = -100..-88`).
- `source/mm_tools/make_bklan_v5.py` (lines 500–585) — Accuracy pass: white 2026 front stucco/fascia (`bk5_white`, `bk5_fascia`), steel-mesh security cage inside courtyard gate, repositioned 16-ft blue & white pyramid canopy tents, rooftop shopping cart over `BATERIAS`, roof A-frame mast, updated 120B storefront panels, lime `ORTIZ Auto Body` fascia banner (`bk5_ortiz`), and white B45 street facade + `bk5_cblogo`.
- `source/mm_tools/make_bklan_v6.py` (lines 558–634) — Adds **Daniel meme wall posters** (`dan_4am`, `dan_shaaa`) and **5 `bk_tv` video TVs** across Warehouse, Courtyard, and Unit 130A.
- `source/mm_tools/make_bklan_v7.py` + `make_bklan6.py` + `build_bklan6.sh` — Final `maps/bklan6.bsp` + `.lit` (trims outlying Manning/Park areas and thins ~30% of LAN monitor/pc/chair edicts while keeping all tables).
- **Texture & Prop Generators:** `build_bklan_textures.py`, `build_v3_textures.py`, `build_v4_textures.py`, `build_v5_textures.py`, `build_v6_textures.py`, `simready_props.py`, `lan_screens.py`, `bklan_tv.qc` (`build_bklan_tv.py`), `make_bklan_simready.py`.
- **Prebuilt outputs:** `maps/bklan6.bsp` (17.2 MB), `maps/bklan6.lit`, `source/mm_tools/out/maps/bklan.wad`, `bklan3.wad`.

#### B. Measured Dimensions & Brush/Entity Counts
Measured from in-memory execution of `make_bklan.py` (`BKLAN_V3=1 BKLAN_V4=1 BKLAN_V5=1`, `OX = -110, OY = 225, U = 12 u/ft`):

| Sub-Zone | Local X (ft) | Local Y (ft) | Local Z (ft) | Size W × D × H (ft) | Size (Quake u) | Brushes | Entities |
|---|---|---|---|---|---|---|---|
| **B76: Larry's Warehouse Hall + 120A Mega Man Bedroom** | `-230.5 .. -141.5` | `22.4 .. 187.5` | `0.0 .. 26.0` | **`89.0 × 165.1 × 26.0`** | `1,068 × 1,981 × 312` | **432** *(188 world, 239 detail, 2 fence, 3 illus)* | **238** *(96 `misc_model`, 84 `misc_lan_*`, 49 light, 2 `bk_tv`, etc.)* |
| **LAN Courtyard (Lot between B76 & B45)** | `-143.0 .. -88.0` | `22.7 .. 195.7` | `0.0 .. 27.0` | **`55.0 × 173.0 × 27.0`** | `660 × 2,076 × 324` | **89** *(3 world, 76 detail, 10 fence)* | **26** *(8 light, 7 `misc_model`, 3 vehicles, 1 `bk_tv`, etc.)* |
| **B45: Celebrity Bodyworks + Unit 130A B-LAN Hall** | `-104.0 .. -21.5` | `20.0 .. 187.7` | `0.0 .. 32.0` | **`82.5 × 167.7 × 32.0`** | `990 × 2,012 × 384` | **422** *(110 world, 297 detail, 1 fence, 14 illus)* | **168** *(98 `misc_lan_*`, 35 `misc_model`, 20 light, 1 `bk_tv`, etc.)* |
| **FULL COMPLEX (B76 + Courtyard + B45)** | **`-230.5 .. -21.5`** | **`18.6 .. 200.5`** | **`0.0 .. 32.0`** | **`209.0 × 181.9 × 32.0`** | **`2,508 × 2,183 × 384`** | **928** *(301 world, 597 detail, 13 fence, 17 illus)* | **431** *(182 `misc_lan_*`, 139 `misc_model`, 76 light, 3 `bk_tv`, etc.)* |
| *(Compact Sub-Option: Unit 130A North End ONLY)* | `-88.0 .. -33.0` | `153.3 .. 184.0` | `0.0 .. 18.0` | `55.0 × 30.7 × 18.0` | `660 × 368 × 216` | ~180 | ~115 |

*(Note: Adding `make_bklan_v6.py`'s Daniel meme posters & TVs adds ~8 brush frames and ~4 `bk_tv` entities. Entity counts above include v1–v5 spawns/items/teleports/pads which should be stripped on merge and re-placed by Bakersfield-ish gameplay!)*

#### C. Texture, Model & WAD Dependencies
- **71 unique textures** (`bk_*`, `bk3_*`, `bk4_*`, `bk5_*`, `{chain`, `{iron`, plus `dan_4am` & `dan_shaaa` from v6): **0 missing from `bakersfield.pk3`**.
- **4 glowing emissive textures** with `_glow.png` in `bakersfield.pk3`: `bk_tube`, `bk_neon`, `bk3_jump`, `bk4_launch`.
- **27 unique `.md3` models** (`139` `misc_model` instances, all under `progs/bklan/`): **0 missing from `bakersfield.pk3`**:
  - Warehouse racks/equipment: `sr_rack_composition_a04.md3` (×35), `sr_rack_composition_a05.md3` (×18), `sr_rack_bulk_storage_a03.md3` (×17), `sr_pallet_block_a01.md3` (×10), `sr_vehicle_forklift_orange_a01.md3`, `sr_vehicle_forklift_blue_a01.md3`, `sr_palletJack_heavyDuty_a01.md3`, `sr_box_cardboard_large_a02.md3` (×4), `sr_pallet_wood_wing_a01.md3` (×3), `sr_crate_plywood_a04.md3`, `sr_pallet_collar_wood_a06.md3`, `sr_handTruck_convertible_aluminum_a04.md3`, `sr_drum_steel_a01.md3`, `sr_table_metal_stainless_a03.md3`.
  - Mega Man hero prop: **`progs/bklan/mm_rig.md3`** (scale 2.6, sitting on bed in 120A!).
  - Unit 130A props: `soda_can.md3` (×11), `cup.md3` (×9), `soda_bottle.md3` (×8), `duct.md3` (×3), `duct_bend.md3`, `fan_pedestal.md3` (×3), `heater.md3`, `extinguisher.md3` (×2), `box_large.md3` (×2), `trashcan.md3`, `cord_reel.md3`, `drum.md3`.
  - Explodable LAN QC entities (already wired in `progs.dat` + `progs/bklan/lan_*.md3` in `bakersfield.pk3`): `misc_lan_table` (26), `misc_lan_monitor` (54, animated Q3A/CS/Win98 skins!), `misc_lan_pc` (49), `misc_lan_chair` (53).
  - Video TVs: `bk_tv` (already wired in `progs.dat` / `bklan_tv.qc`!).
- **WAD2 status:** `bklan.wad` and `bklan3.wad` exist in `source/mm_tools/out/maps/` (and are ALREADY in `make_downtown.py`'s `WADS` list!); `bklan4.wad`, `bklan5.wad`, and `bklan6.wad` are not on disk — extract missing `bk4_*`/`bk5_*`/`dan_*` miptex headers directly from `maps/bklan6.bsp` (Lump 2) into the merged compile WAD.

#### D. Key Recognizable Visual Features (Preserve!)
1. **Larry's Warehouse Branding (`bk3_larry`, `bk3_pylon`)**: Huge 24-ft `LARRY'S WAREHOUSE` fascia sign over Unit 130A's roll-up, 30-ft double-sided roof billboard on B45, and E 21st St courtyard pylon sign.
2. **118/120 E 21st Street Frontage**: Bright white stucco + tall parapet (`bk5_white`, `bk5_fascia`), `BATERIAS` + lime `ORTIZ Auto Body` banner + **rooftop shopping cart** + A-frame roof mast + red/blue `120B` storefront panels.
3. **Mega Man Bedroom (`120A`)**: Carpeted bedroom with **`mm_rig.md3` Mega Man sitting on the quilt bed**, CRT PC desk, bedside lamp, rug, and wall poster — doorway leads straight into the main warehouse!
4. **Full-Blown Warehouse Hall**: 7 open roll-up bays along the courtyard, exposed ceiling joists & glowing tube lights (`bk_tube`), rows of industrial pallet racks, **orange & blue forklifts**, SE & North **explodable CRT LAN Party bays** (`misc_lan_*`), and Daniel `bk_tv` screens + `dan_4am`/`dan_shaaa` posters.
5. **Unit 130A (2001 `bklan.wmv` LAN Hall)**: Cardboard-and-foil `B-LAN 130A ENTER ->` cone & mustard dumpster outside, open roll-up door, galvanized HVAC ducting + hung unit heater, office box, dense explodable CRT LAN rows, Razor kick scooters, magenta neon rack, back room with painted sky mural (`bk_mural`) & tiny corner bathroom.
6. **LAN Courtyard**: Steel-mesh security cage, 16-ft blue & white pyramid canopy tents, rolled-open E 21st iron gate, parked exploding vehicles, and roof-climb crate stack.

#### E. Repositioning, Rotation, Scaling & Trimming Feasibility
- **Three Clean Footprint Tiers** (all axis-aligned Standard Q1 boxes — trivial to translate or rotate by 90°/180°/270° using `dt_mapio` or converting to Valve 220!):
  1. **Full Authentic Complex (`209 × 182 × 32 ft`, ~928 brushes):** Keeps B76 + Courtyard + B45/130A intact — ideal if replacing a large downtown block (~220×200+ ft).
  2. **Squeezed Courtyard Complex (`~179 × 168 × 32 ft`):** Narrow the 55-ft courtyard down to 25–30 ft (still wide enough for tents, 1 lane of vehicles, and full sightline between B76 roll-ups and Unit 130A!) — saves 25–30 ft of width with **zero** lost buildings or interiors!
  3. **Single-Lot Compact Option (`B76 Only`: `89 × 165 × 26 ft`, OR `B76 + Unit 130A grafted onto east/north flank`: `~145 × 165 ft`):** Drops B45's generic south Celebrity Bodyworks units (`y = 23..153`, saving ~130 ft of redundant units) while keeping 100% of Larry's Warehouse Hall, Mega Man Bedroom, AND Unit 130A B-LAN Hall!
- **Edict / Performance Tip:** Just like `make_bklan_v7.py:606`, thinning ~30–40% of `misc_lan_chair/monitor/pc` and reducing redundant `sr_rack_composition_*` from 70 to ~35–45 racks keeps the exact visual silhouette while saving ~100 edicts and draw calls.

---

### 3.4 The Bakersfield Sign (1949 Union Ave Arch / Sillect Ave Rebuild)

#### A. Source Files & Format
The Bakersfield Sign is **NOT** a standalone `.bsp` or `.md3` — it is a **100% parametric procedural brush structure** (`108` brushes, all `func_detail`, Standard Q1 format, `12 u/ft`) defined across three Python files:
1. **`source/mm_tools/bklan_sign.py`** (33 lines) — Shared parametric dimensions and parabolic arch equations `zt(s)` and `zb(s)` (measured directly from satellite + 2026-10-30 user photos).
2. **`source/mm_tools/make_bklan_v2.py`** (lines 288–354) — Builds the two twin Spanish-Mission towers (`tower(tx, ty, inner)`) and the 24-segment parabolic arch band (`N = 24`), originally centered at `SIGN_X = 915, yc = -3`.
3. **`source/mm_tools/make_bklan_v5.py`** (lines 278–335) — **CRITICAL accuracy upgrade (MUST use this version!):**
   - Swaps `bk_bsign` (missing from `bakersfield.pk3`) → **`bk5_bsign`** (`2048×320` PNG in `bakersfield.pk3`, upright plumb `BAKERSFIELD` navy letters on yellow arch).
   - Thickens the clad arch truss depth along the road from `1.6 ft` → **`DEPTH5 = 2.6 ft` (`31.2 u`)**.
   - Adds the projecting **tan impost mouldings** around all 4 faces of both tower bases at `z = 7.0..7.7 ft`.
   - Adds low wrap-around hedges (`2.4 ft`) and warm golden architectural accent lights along both arch faces and towers.
- **Texture Generators:** `source/mm_tools/build_bklan_textures.py` (`build_v2` → `bk_bstucco`, `bk_btan`, `bk_btrim`, `bk_bupper`, `bk_broof`, `bk_bband`) and `source/mm_tools/build_v5_textures.py` (`bk5_bsign`).

#### B. Exact Parametric Geometry & Brush-by-Brush Inventory
At default `1:1` real-world dimensions (`bklan_sign.py` + `make_bklan_v5.py`, spanning Y across an E-W road at `x = SIGN_X`, `y_center = -3`):

- **Overall Pure Sign Bounding Box:**
  - **Along-road thickness (X):** `14.0 ft` (`168 u`, set by tower eaves `±7.0 ft`; tower base is `10.0 ft` / `120 u`; shaft is `9.5 ft` / `114 u`; arch band is `2.6 ft` / `31.2 u`).
  - **Across-road total width (Y):** **`111.0 ft`** (`1,332 u`, outer eaves to outer eaves; tower bases outer-to-outer = `107.0 ft` / `1,284 u`; tower center-to-center `SPACING = 97.0 ft` / `1,164 u`).
  - **Clear Roadway Opening Between Towers:** `87.0 ft` (`1,044 u`) between tower bases; `83.0 ft` (`996 u`) between overhanging eaves.
  - **Total Height (Z):** **`31.0 ft`** (`372 u`) to both pyramid roof peaks; arch crown top = `30.6 ft` (`367 u`).
  - **Vertical Road Clearance Under Arch (`zb(s)`):** **`17.5 ft` (`210 u`)** at tower junctions (`s = ±48.5 ft`), rising parabolically to **`23.1 ft` (`277 u`)** at center crown (`s = 0`) — plenty of headroom for players, go-karts, vans, buses, and jump arcs!
- **Total Brush Count: Exactly `108` brushes (all `func_detail`)** — zero worldspawn brushes, zero models:

| Structural Component | Z Range (ft / u) | Plan Size (ft) | Brush Count | Textures Used |
|---|---|---|---:|---|
| **Plinth (×2 towers)** | `0.0 .. 0.3 ft` (`0..4 u`) | `10.0 × 10.0` | `2` (1/tower) | `bk_btan` |
| **4 Corner Base Piers (×2 towers)** | `0.0 .. 7.0 ft` (`0..84 u`) + `7.0 .. 8.6 ft` (`84..103 u`) | `2.9 × 2.9` each around `4.2 ft` wide pass-through in all 4 faces! | `16` (8/tower) | `bk_bstucco`, `bk_btrim` |
| **Stepped Pass-Through Arch Spandrels (×2 towers)** | `7.0 .. 8.6 ft` (`84..103 u`) | 5 stepped tiers (`hw = 1.95, 1.64, 1.22, 0.73, 0.0`) on N/S & E/W arches | `36` (18/tower) | `bk_bstucco`, `bk_btrim` |
| **Projecting Impost Mouldings (×2 towers, v5)** | `7.0 .. 7.7 ft` (`84..92 u`) | 8 small trim bars per tower flanking base arches | `16` (8/tower) | `bk_btan` |
| **Lower Solid Shaft above Arches (×2 towers)** | `8.6 .. 10.5` + `10.5 .. 14.3 ft` (`103..172 u`) | `10.0 × 10.0` | `4` (2/tower) | `bk_bstucco`, `bk_btrim` |
| **Projecting Tan Belt-Course Ledge (×2 towers)** | `14.3 .. 16.3 ft` (`172..196 u`) | `10.6 × 10.6` | `2` (1/tower) | `bk_btan` |
| **Upper Medallion Shaft (×2 towers)** | `16.3 .. 26.4 ft` (`196..317 u`) | `9.5 × 9.5` (City Seal medallion on 3 outer faces; inner face meets arch) | `2` (1/tower) | `bk_bupper`, `bk_bstucco` |
| **Tan Cap Band (×2 towers)** | `26.4 .. 28.9 ft` (`317..347 u`) | `10.0 × 10.0` | `2` (1/tower) | `bk_btan` |
| **Roof Eaves + 4-Face Terracotta Pyramid Roof (×2 towers)** | `28.9 .. 29.3` + `29.3 .. 31.0 ft` (`347..372 u`) | `14.0 × 14.0` tapering to apex | `4` (2/tower) | `bk_broof` |
| **Parabolic `BAKERSFIELD` Arch Band (`N = 24` segments)** | `zb(s) = 17.5..23.1 ft` to `zt(s) = 25.0..30.6 ft` | `2.6 ft` deep (`31.2 u`) × `97.0 ft` span (`7.5 ft` vertical band depth) | **`24`** | `bk5_bsign` (both E/W faces), `bk_bband` (top/bot/ends) |
| **TOTAL PURE SIGN** | **`0.0 .. 31.0 ft`** | **`14.0 × 111.0 ft`** | **`108` brushes** | **8 unique textures** |

#### C. Texture Dependencies (All 8 in `bakersfield.pk3`!)
| Texture | Pixel Size in `bakersfield.pk3` | Used For |
|---|---:|---|
| **`bk5_bsign`** | `2048 × 320` | Parabolic yellow arch banner w/ upright navy **`BAKERSFIELD`** letters on both front & back faces (**MUST use `bk5_bsign`, NOT v2's `bk_bsign` which is absent from `bakersfield.pk3`**) |
| `bk_bband` | `128 × 128` | Top, bottom & end edges of the 2.6-ft-deep clad arch truss |
| `bk_bstucco` | `256 × 256` | Cream stucco tower shafts |
| `bk_btan` | `128 × 128` | Base plinth, impost mouldings, mid-tower ledge, and cap band |
| `bk_btrim` | `256 × 128` | Tan arched pass-through trim bands (`z = 7.0..10.5 ft`) |
| `bk_bupper` | `256 × 256` | Upper shaft panels carrying the **6.4-ft Bakersfield City Seal medallion** (3 outer faces per tower) |
| `bk_broof` | `128 × 128` | Spanish red-tile eaves & pyramid roofs |
| *(optional)* `bk_hedge` | `128 × 128` | Low `2.4 ft` wrap-around planter hedges at tower bases |

#### D. Repositioning, Rotation & Street-Width Adaptation
- **Trivial to Reposition & Rotate 90°:** Because `tower()` and the 24-segment arch are only ~65 lines of pure parametric Python (`bklan_sign.py`), we can emit the Sign directly in the Bakersfield-ish composer along **either** an E-W street (towers N & S, sign faces E & W) **or** a N-S street like Chester Ave / H St / Eye St (towers E & W, sign faces N & S) using Valve 220 or swapped axes!
- **Adapting `SPACING` to Downtown Street Widths:** Real-world `SPACING = 97.0 ft` (`87 ft` clear between tower bases) matches a wide 6-lane boulevard (like Chester Ave's ~80–90 ft paired corridor or a plaza entry). On narrower downtown streets (e.g. 60–70 ft ROW like 19th St / 20th St / H St):
  - **Option 1 (Preferred — Zero Distortion):** Place it spanning Chester Ave or an open plaza / wide intersection apron so the authentic `97 ft` span stands completely clear of adjacent facades.
  - **Option 2 (Parametric Narrowing):** Reduce `BS.SPACING` (e.g. `72–82 ft`, clear road `62–72 ft`) and keep `wspec("bk5_bsign", yc - HALF, yc + HALF, ZMAX, ZMIN)` — `bk5_bsign` auto-fits the exact span; keep `ZT_CROWN - ZB_CROWN = 7.5 ft` (or scale arch vertical height proportionally ~0.85× so letter aspect ratio stays crisp).

#### E. Destructibility & Clean Toppling-Over Geometry Analysis
The Bakersfield Sign's geometry is **naturally engineered for a dramatic, clean, high-FPS topple**:

1. **Natural Architectural Fracture Planes (Where to Split Static Stumps vs Falling Assembly):**
   - **Plane A — Base Corner Pier Shear (`Z = 0.3..7.0 ft`, RECOMMENDED):** Each tower stands on **4 slender `2.9 × 2.9 ft` corner piers** surrounding a `4.2 ft` hollow arched pass-through! Splitting right at **`Z = 3.5..6.5 ft`** (jagged broken stucco pier stumps left as static `worldspawn`/`func_detail` on both sidewalks, `8–16` brushes total) leaves unmistakable ruined arch-base pedestals standing on both curbs while the **entire upper sign (`Z = 6.5..31.0 ft`: upper shafts + city seal medallions + terracotta pyramid roofs + entire 97-ft `BAKERSFIELD` arch = ~76–92 brushes)** tips forward/backward cleanly around the street axis!
   - **Plane B — Mid-Tower Tan Ledge Shear (`Z = 14.3 ft`):** Leaves both full lower arch-tunnel tower bases (`0..14.3 ft`, walkable pedestrian pass-throughs!) permanently intact while the **upper twin medallion shafts + pyramid roofs + `BAKERSFIELD` arch (`Z = 14.3..31.0 ft`, ONLY `32` brushes total: 4+4 tower upper brushes + 24 arch segments!)** shear off the belt-course ledge and crash onto the street!
   - **Plane C — Full Base Plinth Hinge (`Z = 0.3 ft`):** Entire `106`-brush assembly (everything above the 0.3-ft plinth) tips over as one colossal 111-ft-wide × 31-ft-tall gate, slamming flat across the roadway.
2. **Exact Pivot & Footprint When Toppled (Assuming Sign spans Y, tips along ±X roadway):**
   - **Hinge Axis:** Parallel to the arch span (Y-axis through tower centers `x = SIGN_X ± 4.75 ft` at break height `Z_break`).
   - **Landing Footprint on Roadway:**
     - If breaking at **Plane A (`Z_break ≈ 5 ft`)**: Falling height = `26 ft` (`312 u`) → toppled sign lies across the road covering **`26 ft` along the road × `111 ft` across the road**, forming a **`9.5–14 ft` high climbable/rampable barricade** right across the avenue (with the `BAKERSFIELD` yellow arch lying face-up in the rubble!).
     - If breaking at **Plane B (`Z_break = 14.3 ft`)**: Falling height = `16.7 ft` (`200 u`) → only **32 brushes**, drops smoothly down `14.3 ft` + rotates `90°` to lie flat on the asphalt (`2.6 ft` thick arch band + `9.5 ft` upper tower cubes) — players & go-karts can still drive/jump right over the fallen `2.6 ft` arch center!
3. **Two Clean Engine Representations (for `@qc-tech-scout` coordination):**
   - **Inline BSP Brush Submodel(s) with `origin` Brush (`*N`):** At only **32–108 brushes**, the falling upper sign (either 1 unified submodel OR 3 synchronized submodels: Left Tower Upper + Right Tower Upper + 24-brush Arch so one tower can buckle first and snap the arch slightly off-axis!) fits trivially inside Zircon's `8,192` model limit, gets **real baked lightmaps** before toppling, has exact **`SOLID_BSP` collision** (climbable once fallen!), and pivots cleanly around an explicit `origin` brush at `(SIGN_X, yc, Z_break)`!
   - **Exported `.md3` Model (Optional Alternative):** Those 32–108 convex brushes convert cleanly to a low-poly `~400–900` triangle `.md3` using the exact same `bk5_bsign` / `bk_bupper` / `bk_bstucco` textures in `bakersfield.pk3`, allowing smooth client-side pitch/roll/bounce animation (paired with simple `SOLID_BBOX` / `SOLID_BSP` fallen-debris collision brushes).
   - **Clearance Check:** Ensure at least **`32 ft` (`384 u`) of clear open street** on the fall direction side so the toppled arch lands cleanly on the roadway without clipping into Padre Hotel, Fox Theater, or adjacent buildings!

---

## 4. Installed Windows Map Compilation Pipeline

### 4.1 Exact Installed Toolchain on This Machine
- **Location:** `G:\Quake\Combat\tools\ericw\` *(Verified: `D:\vibe\quake1opensource\tools\ericw` and `G:\Quake\TRUEDM3\tools\ericw` do NOT exist on this machine — always point `DT_ERICW` / build scripts to `G:\Quake\Combat\tools\ericw`!)*
- **Version:** **`ericw-tools 2.0.0-alpha11`** (64-bit Windows, with Intel Embree 4 + TBB raytracing acceleration in `light.exe`)
- **Installed Binaries:**
  - `qbsp.exe` — BSP compiler (supports `-bsp2`, mixed Standard Q1 + Valve 220 `.map`, `-convert valve`, `-subdivide`, `-maxnodesize`, `-leaktest`, `-onlyents`, `-wadpath`, `-threads`)
  - `vis.exe` — Portal visibility compiler (supports `-fast`, `-visdist <units>`, `-threads`)
  - `light.exe` — Embree-accelerated lightmap & `.lit` RGB baker (supports `-extra`, `-extra4`, `-bounce`, `-bouncescale`, `-onlyents`, `-threads`)
  - `bspinfo.exe` — Lump table & statistics dumper *(WARNING: writes `<map>.bsp.{lm_0.png,geometry.obj,json}` next to the `.bsp` by default — never run casually on `maps/*.bsp` without cleaning outputs!)*
  - `bsputil.exe`, `maputil.exe`, `lightpreview.exe`
- **Host Hardware:** 16 logical CPU threads (AMD Ryzen 7 7700X, 31.1 GiB RAM, RTX 4070 Ti).
- **Python Environment:** Python 3.13 (`C:/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe` / `python` on PATH, with `PIL` / `numpy` installed).

### 4.2 Exact Flags Used Across Existing Build Scripts

| Pipeline | `qbsp.exe` Flags | `vis.exe` Flags | `light.exe` Flags | Post-Compile Passes |
|---|---|---|---|---|
| **Downtown (`source/downtown/tools/build_downtown.sh`, `bakersfielddowntown`)** | `-bsp2 -subdivide 1024 -threads 8` *(add `-maxnodesize 2048` in `DT_LITE=1`)* | **Full:** `-visdist 4000 -threads 8`<br>**Fast (`DT_FAST=1`):** `-fast -threads 8` | **Full:** `-extra4 -threads 8`<br>**Fast (`DT_FAST=1`):** `-threads 8` (1×) | 1. `keep_sky_pvs.py` *(prevents HOM past `-visdist` if fog disabled)*<br>2. `scale_bklan_light85.py <bsp> 0.69` *(bright-day calibration)*<br>3. `clamp_bd_sb25.py` *(clamps highlight blowout for `r_hdr_scenebrightness`)*<br>4. `strip_miptex_pixels.py` *(strips ~7.4 MB embedded WAD pixels -> 100 KB stubs, keeps `*teleport`/`sky_bk`/`clip`/`skip`/`trigger`)*<br>5. `save_bd_presets.py` |
| **Golden West (`source/mm_tools/goldenwest/compile_gw.py`)** | `-bsp2 -leaktest -threads 16 -wadpath <dir> -subdivide 512` | `-threads 16 -visdist 8400` | **Full:** `-extra4 -bounce 1 -bouncescale 0.65 -threads 16`<br>**Fast:** `-extra -threads 16` | `fog_vis_tools.prune_pvs(..., visdist=8400, keep_sky=True)` |
| **bklan6 (`source/mm_tools/build_bklan6.sh`)** | `-bsp2 -threads 16` *(default subdivide 240)* | **Full:** `-visdist 7500 -threads 16`<br>**Fast (`BK6_FAST=1`):** `-fast -visdist 7500 -threads 16` | **Full:** `-extra -threads 16`<br>**Fast:** `-threads 16` | 1. `fog_vis_tools.py keep-sky-pvs`<br>2. `scale_bklan_light85.py <bsp> 0.85` |

### 4.3 Measured Compile Times & Recommended Iteration Strategy
Actual logged compile times on this 16-thread desktop:

| Map | Brushes | `make` | `qbsp` | `vis` | `light` | Post-proc | **Total Wall Time** |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`bakersfielddowntown`** *(full, 8 threads, `-subdivide 1024`, `-visdist 4000`, `-extra4`)* | 15,089 | 5.5 s | 54.2 s | 24.5 s | 72.3 s | ~5 s | **~2 min 42 s (162 s)** |
| **`bakersfielddowntown_lite`** *(full, 8 threads, `-maxnodesize 2048`, `-visdist 2500`, `-extra`)* | ~11,000 | ~4 s | 38.4 s | 23.5 s | 72.0 s | ~4 s | **~2 min 22 s (142 s)** |
| **`goldenwest`** *(full, 16 threads, `-subdivide 512`, `-visdist 8400`, `-extra4 -bounce 1`)* | ~7,500 | ~4 s | 15.9 s | 16.6–38.8 s | **780.1 s (13 min!)** | ~2 s | **~13 min 33 s (813 s)** |

**Why `bakersfielddowntown` compiles 5× faster than `goldenwest`:**
1. **`-subdivide 1024`** (instead of `512` or `240`) drastically cuts face/luxel count on big outdoor streets/roofs while staying legal for Zircon (`surface extents` are fine in BSP2 + DarkPlaces/Zircon; `bspinfo` only warns about vanilla Q1).
2. **WAD2 miptex downsampling** on large street/sidewalk/plaza textures in `make_downtown.py:157-180` (`ds_asph`/`ds_conc` halved to `128×128` / `64×64` in WAD2 while external PNGs in `bakersfield.pk3` stay full-res) cuts lightmap luxels by 4× without changing visual resolution!
3. **Use `-threads 16`** on this machine (downtown only used `-threads 8`), plus **dev fast preset** (`vis -fast` + `light -threads 16` without `-extra4`, or `DT_WINDOW` local slices) to get **~35–60 s** full-map edit-compile-test cycles, reserving `-visdist 4500..6000` + `light -extra4` for final builds!

---

## 5. BSP Lump Comparison & Quake BSP / Zircon Engine Limits

### 5.1 Current Shipped Maps — Measured BSP2 Lump Usage

| BSP Lump | `bakersfielddowntown.bsp` | `bklan6.bsp` | `goldenwest.bsp` | BSP29 Hard Limit | BSP2 Format Limit | Zircon Engine Practical Limit |
|---|---:|---:|---:|---:|---:|---|
| **Format** | `BSP2` | `BSP2` | `BSP2` | `29` | `BSP2` (`2PSB` / `BSP2`) | `BSP2` native (`model_brush.c`) |
| **Models (`*0`..`*N`)** | **275** | **65** | **48** | 256 *(Q1 protocol)* | `2^31 - 1` | **`8,192` total precached models** (`MAX_MODELS_8192`, shared with `.md3`/`.spr`/weapons!) |
| **Planes** | 31,068 | 17,263 | 23,805 | 32,767 | `2^31 - 1` | RAM-bound |
| **Vertexes** | 144,520 | 113,235 | 96,111 | 65,535 | `2^31 - 1` | RAM/VBO-bound |
| **Nodes** | 58,555 | 35,791 | 48,901 | 32,767 | `2^31 - 1` | RAM-bound |
| **Texinfos** | 5,424 | 1,938 | 4,360 | 32,767 | `2^31 - 1` | RAM-bound |
| **Faces** | **116,319** | **97,477** | **73,212** | 65,535 | `2^31 - 1` | RAM/draw-call bound (~120–150k healthy) |
| **Clipnodes** | **129,879** | **79,388** | **65,773** | **32,767** *(exceeded 4×!)* | `2^31 - 1` | RAM-bound (`int32` children in BSP2) |
| **Leafs** | **34,169** | **24,222** | **35,190** | 8,192 *(32,767 ext)* | `2^31 - 1` | **CRITICAL:** Keep `< 35,000` — PVS bitmatrix scales `O(visleafs²)` (~120 MB at 32k leafs!) |
| **Marksurfaces** | 162,583 | 122,783 | 120,160 | 65,535 | `2^31 - 1` | RAM-bound (`uint32` in BSP2) |
| **Edges / Surfedges** | 267k / 493k | 213k / 418k | 171k / 315k | 65,535 / 2^31 | `2^31 - 1` | RAM-bound |
| **Textures (miptex)** | **927** *(101 KB stripped)* | **344** *(2.31 MB)* | **179** *(3.74 MB)* | 512–4096 | Unlimited | **Watch VRAM/RAM:** each unique world PNG uploads to GPU (`927` = 218 MiB RGBA on high-spec; keep total unique textures `<= ~950–1,050` by dropping replaced downtown filler textures!) |
| **Lightdata (Lump 8)** | **3.90 MB** *(+11.7 MB `.lit`)* | **3.92 MB** | **5.46 MB** *(21.8 MB total w/ `.lit`)* | ~2 MB (vanilla) | Unlimited (`int32` offsets) | Keep Lump 8 `<= ~6–8 MB` (`<= 24 MB` `.lit`) for fast load & low-spec compatibility |
| **Visdata (Lump 4)** | **16.68 MB** | **1.55 MB** | **1.15 MB** | ~2 MB (vanilla) | Unlimited | Use `-visdist` + structural world walls so visdata stays lean |
| **Entdata (Lump 0)** | 153.8 KB | 118.6 KB | 31.2 KB | 128 KB | Unlimited | Zircon `MAX_EDICTS_32768` (`32,768` live edicts; keep map spawns `< 2,000` for smooth low-spec & fast network baseline) |

### 5.2 Key Engine & Compiler Guardrails for Bakersfield-ish
1. **ALWAYS compile with `-bsp2`:** `bakersfielddowntown` already exceeds BSP29's `32,767` clipnode/node limit by 4× and `65,535` face/vertex/marksurface limit by 2×. BSP2 removes all 16-bit index caps.
2. **Inline Submodel (`*1..*N`) Budget for Destructibles:** Verified in `G:\Quake\_bq_fork_engine\src\qdefs.h:50` and `sv_main.c:1155`: under Zircon's `PROTOCOL_DARKPLACES7`, `MAX_MODELS_8192 = 8192` (shared across world `*0`, inline brush entities `*1..*N`, weapons, players, monsters, and `misc_model`s). Current `bakersfielddowntown.bsp` uses `275` inline models (mostly `trigger_push`, `trigger_teleport`, `func_wall` fence chunks, etc.) + ~200 mod/prop models = `< 600` total — leaving **> 7,500 model slots** available for destructible Fox Theater, Padre Hotel, Bakersfield Sign, and shatterable glass brush submodels!
3. **High Skybox Coordinate Bounds (`±32,768 u`):** `make_bakolansmall.py` proved `SKY_Z = 2500 ft` (`30,000 u`) works cleanly inside Quake's `±32,768 u` safe envelope; for Bakersfield-ish, setting `SKY_Z = 600..1200 ft` (`7,200..14,400 u`) gives vast vertical room for jetpacks, super jump pads, Padre Hotel collapse arcs, and aerial combat while keeping skybox portal/vis overhead low!
4. **Visleaf Discipline (Low-Spec Stability):** Per `docs/lowspec_crash_fix_report_2026-11-22.md` (H7), `bakersfielddowntown`'s `32,209` visleafs came largely from `8,669` `func_detail_wall` brushes splitting Hull-0 leaves. For Bakersfield-ish:
   - Keep **building outer shells** in `worldspawn` (blocks VIS cleanly!).
   - Put interior furniture, signage, awnings, trees, and the Bakersfield Sign in **`func_detail`** or **`func_detail_illusionary`** (never `func_detail_wall` for small greebles).
   - Keep total visleafs **`< 35,000`** and run `keep_sky_pvs.py` after `vis.exe -visdist`.
5. **Worldspawn `wad` 127-Char Limit & No Loose Texture Leaks:**
   - Merge all needed WADs (existing downtown WADs + extracted `gw2.wad` + extracted `bklan4/5/6` headers) into **one** compile-time WAD (e.g. `source/downtown/out/bakersfieldish_all.wad`) referenced by short relative name `"wad" "bakersfieldish_all.wad"`.
   - Always run `strip_miptex_pixels.py` post-light so the shipped `maps/bakersfieldish.bsp` stays compact (dropping 8–12 MB of redundant WAD pixels while loading full-res PNGs from `bakersfield.pk3`).
   - **Never** modify `bakersfield.pk3` or `q15.pk3`, and **never** leave loose PNGs in `BakersfieldQuake/textures/`. If Bakersfield-ish introduces ANY brand-new textures/models/sounds (e.g., post-apocalyptic cracked concrete, rubble decals, custom skybox, collapse sounds), package them in a reproducible CI-built overlay **`BakersfieldQuake/zz_bakersfieldish.pk3`** per `AGENTS.md`.
6. **Zero BSPX Support in Zircon:** Do not rely on `light.exe -bspx` / `DECOUPLED_LM`; use `make_downtown.py`'s native WAD2 miptex downsampling trick (`_downsample_miptex`) if lightmap RAM/compile time needs tuning.
