# Low-End PC Crash & Freeze Fix Report (`bakersfielddowntown` & System-Wide Low-Spec Stability)

**Date:** 2026-11-22  
**Workspace:** `G:\Quake\Combat\BakersfieldQuake` (engine deployed to `G:\Quake\Combat\engine\zircon_beta_gcc.exe`)  
**Backups Root:** `G:\Quake\Combat\_backups\lowspec_fix_20261122\`  
**Test Host (Dev Desktop):** MSI MS-7D75, AMD Ryzen 7 7700X, 31.1 GiB RAM, NVIDIA GeForce RTX 4070 Ti (12,282 MiB 64-bit VRAM) + AMD Radeon iGPU (512 MiB) + Parsec Virtual Display Adapter (`ROOT\DISPLAY\0000`), Windows 11 25H2 Build 26200.10075  
**Target Reproducing Laptop (User Report):** ASUS Zenbook S 13 UX5304VA, Intel Core i5-1335U, 15.6 GB RAM (~0.2 GB free at launch, 13 GB SSD pagefile), Intel Iris Xe iGPU (shared system RAM, WMI 2 GB `AdapterRAM`, driver `32.0.101.5768`), Parsec Virtual Display Adapter, Windows 11 26200

---

## 1. Executive Summary & Root Cause

### The Problem
On the low-end Zenbook laptop (15.6 GB RAM with ~0.2 GB free, Intel Iris Xe unified RAM), launching `maps/bakersfielddowntown.bsp` with `lowspec 1`, `lowmem.cfg`, and `lowgpu.cfg` hung the window (`Not Responding`) with no `Mem_Alloc: out of memory` line, stopping deterministically in `bq_game.log` right after:

```text
Stats for q1bsp model "maps/bakersfielddowntown.bsp": 105173 faces, 55657 nodes, 32148 leafs, 31200 visleafs, 0 visleafportals, mesh: 447186 vertices, 236840 triangles, 105173 surfaces
Mem_Alloc: pool Temporary Memory, image_png.c:81, 16.0 MB
Mem_Alloc: pool texture management, gl_textures.c:984, 16.0 MB
Mem_Alloc: pool texture management, gl_textures.c:985, 16.0 MB
```

### Exact 3-Part Root Cause (Proven by Source Audit + Live Profiling + Bounded Commit-Cap Repro)

1. **`progs/megaman.png` `16.0 MB × 3` Decode/Upload Trigger (`image_png.c:81` -> `gl_textures.c:984-985`)**
   - `Stats for q1bsp model` (`model_brush.c:4570`) is the **final line** of `Mod_Q1BSP_Load()` — the world BSP itself had already finished loading.
   - Immediately afterward, `worldspawn()` precaches `progs/megaman.md3` (`world.qc:172` -> `weapons.qc:13` -> `MegaMan_Precache()` -> `megaman.qc:50`) on **every** map (even `aerowalk`). Its skin `progs/megaman.png` (`2048×2048`, 692,517 B RGB-8b PNG in `bakersfield.pk3`) triggers:
     - `lodepng_decode32` (`image_png.c:67`): raw `malloc` 16.0 MB (untracked by `Mem_Alloc`),
     - `PNG_LoadImage_BGRA` (`image_png.c:81`): a second **16.0 MB** in `tempmempool` while `lodepng_data` is still live (**32 MB peak**), held by `R_SkinFrame_LoadExternal_SkinFrame` (`gl_rmain.c:2804`) across companion texture loads,
     - `R_UploadFullTexture` -> `R_MakeResizeBufferBigger` (`gl_textures.c:984-985`): unconditionally allocates **two resident 16.0 MB buffers** (`resizebuffer` + unused dead `colorconvertbuffer`) BEFORE `gl_picmip_other 1` downsamples it, holding both in `texturemempool` until `R_Textures_Frame()` after map load completes.

2. **Silent Phase 2 Texture Flood (~85% of Load Time) + High Non-Texture CPU Commit Floor**
   - `bq_game.log` writes unbuffered per-line via raw CRT `write(fd)` (`console.c:627` -> `fs.c:111`), so nothing was stuck in stdio buffers. The log deterministically went silent after `gl_textures.c:985` because `developer_memorylargerthanmb` defaults to **16 MB** (`zone.c:96,406`): once `resizebuffer` reached 16 MB it never reallocated, and Phase 2 (`1.1 s -> ~10.5 s` on desktop — **~85% of total load time**) silently decoded and uploaded **~6,700 more model/weapon/sprite textures** (every one `< 16 MB`; largest is `progs/reeseice.spr32` at `15.86 MB`), pushing `bakersfielddowntown` to **`7,734–7,742` textures (`1,028 MB` uploaded / `1,859 MB` original RGBA)** under old `lowmem+lowgpu` (`~2,368 MB` uploaded under high-spec).
   - Beneath textures sat a **`~1.45 GB` non-texture CPU commit floor**: `116.0–123.7 MB` quadratic uncompressed PVS bitmatrix (`model_brush.c:3089`, `31,200 × 3,900 B`; up to `284.2 MB` on `soi6`), `31.7 MB` resident surfmesh (`model_shared.c:1028`), `17.2 MB` peak / `9.0 MB` resident `render_bih` (`model_brush.c:7736`), `23 MB` BSP + `27.3 MB` VBO staging overlap, `39.8–52 MB` FreeType, and up to `232 MB` of Zircon auto-grown archived `r_buffermegs_*` / `r_framedatasize` bloat in `config.cfg`.
   - Total commit under old `lowmem+lowgpu` reached **`2,540–3,039 MB`** (and **`3,318 MB`** on map change `soi6 -> bakersfielddowntown` / `menu_background 1` `+750 MB` spike). On Intel Iris Xe unified memory with `0.2 GB` free RAM, both CPU and OpenGL allocations come from system RAM, grinding into multi-minute SSD pagefile thrashing or commit exhaustion.

3. **Missing Win32/SDL Message Pump (Event 1002), OOM Deadlock/Recursion Bug, and Under-Tiering Launchers**
   - **No loading message pump (`vid_sdl.c:1263`, `host.c:747`)**: `Sys_SendKeyEvents()` was called in only one place (`Host_Frame()`), never during map/texture/model/lightmap/GLSL loading. Even on a Ryzen 7 7700X + NVMe + RTX 4070 Ti, **every map exceeded Windows' 5.0 s Event 1002 "Not Responding" threshold** (`5.84 s` on 632 KB `aerowalk`, `9.47–10.56 s` on `bakersfielddowntown`, `16.26 s` on stock 8/30 engine).
   - **Broken OOM & late logging (`zone.c:154-171,404-421`, `console.c:677`, `sys_sdl.c:65-86`, `host.c:1197-1199`)**: Under commit exhaustion (reproduced verbatim at a `2000 MB` Windows Job Object cap -> **exact silent hang right after `gl_textures.c:985` with 0 OOM line and 0 dialog**, and at `2500 MB` on `soi6 -> bdt` -> **`48.09 s` hang + `0xC0000005` crash**), `_Mem_Alloc` held `mem_mutex` while calling `Mem_PrintList` -> `Log_ConPrint`, which called `Mem_Alloc(tempmempool, len+1)` (`log_file_stripcolors 1`), triggering recursive 500-iteration `attempt_malloc` `Sleep(1)` stalls (`0.5–7.8 s` each) and deadlock. Additionally, `Log_Start()` ran after `CL_StartVideo()` (leaving zero `bq_game.log` on startup `+map` OOM) and `Sys_Error` exited without `Log_Close()`.
   - **Under-tiering & config clobbering (`launchers/Play.cmd`, `Start Server.cmd`, `Play.sh`, `Start-Server.sh`, `source/mac/launcher.sh`, `bm_up_legacy.cfg`)**: Windows launchers cached total RAM once (15.6 GB rounded to 16 GB >= 10 GB), never checked **live free RAM** (`0.2 GB`), used 32-bit WMI `AdapterRAM` `-Maximum` without excluding virtual adapters (`Parsec VDD`, `ROOT\DISPLAY\0000`) or identifying iGPUs, lacked `ultralow`/`safemode` tiers, wrote `lowgpu-applied.txt` prematurely right after async `start ""` (breaking persistence if run #1 froze), and allowed `bm_up_legacy.cfg` to overwrite saved `lowspec 1` settings on legacy upgrades.

### Headline Solution & Impact
We delivered a coordinated 4-layer fix — **engine stability/memory patch**, **auto-tiering launcher + preflight + watchdog + configs + diagnostic/updater guardrails**, **optional lightweight `bakersfielddowntown_lite` map**, and **automated regression harness** — while preserving **100% untouched high-spec visuals (`normal` tier)**, untouched base `.pk3` archives (`bakersfield.pk3`, `q15.pk3`), and untouched shipped `maps/bakersfielddowntown.bsp`/`.lit`:

- **Max `Not Responding` Streak (`bakersfielddowntown`)**: `9.47–10.56 s` -> **`0.61–0.73 s`** (**-15× to -16×**; high-spec `normal`: `9.86 s` -> **`0.62–0.71 s`**) — eliminates Windows Event 1002 across all 18 maps.
- **Peak Commit (`bakersfielddowntown`)**: `4,933 MB` (high) / `2,540–3,039 MB` (old low) -> **`1,320–1,542 MB`** (`ultralow.cfg`) / **`1,294 MB`** (`safemode.cfg`, no S3TC) — passes both `2048 MB` and tight `1500 MB` Job Object commit caps.
- **Peak Commit (`bakersfielddowntown_lite`)**: **`1,089–1,135 MB`** (`ultralow.cfg`) / **`1,053 MB`** (`safemode.cfg`) — **-72% to -79%** vs high-spec (`365 MB` headroom under 1.5 GB cap).
- **Peak GPU VRAM (`bakersfielddowntown`)**: `5,515 MB` (high) / `1,346–2,263 MB` (old low) -> **`349–402 MB`** (`ultralow`) / **`280 MB`** (`safemode`) (**-85% to -95%**).
- **Map Change (`soi6 -> bakersfielddowntown`)**: `3,318 MB` / `48.09 s` hang + `0xC0000005` crash @ 2500 MB cap -> **`1,379 MB` / `0.84 s` hang PASS @ 2048 MB cap** (**-58.4%** commit).
- **Gameplay `timedemo` FPS**: High-spec `normal` **`374.9 -> 392.2 fps (+4.6%)`** (zero regression); `ultralow.cfg` **`542.5 fps`** with 1s min FPS **`256 fps`** (**+32%** vs old low `194 fps`).
- **All 18 Shipped Maps + Map Change + 400 MB Graceful OOM**: **20 / 20 PASS** under `2048 MB` commit cap; post-deploy verification on `G:\Quake\Combat\engine\zircon_beta_gcc.exe` **3 / 3 PASS**.

---

## 2. Step 1 Hypothesis Table (All 8 Hypotheses)

| # | Hypothesis | Test Performed | Measured Result | Verdict |
|---|---|---|---|---|
| **H1** | Corrupt/mismatched `.bsp`, `.lit`, PNG textures, or a rogue/stray `zz_bakersfielddowntown.pk3` (8.2 MB reported on Zenbook) | Inventoried all `bakersfielddowntown` copies across repo, `dist/BAKOQUAKE`, `BAKOQUAKE*.zip` (`v1.0`–`v1.14`), `source/mm_tools/map_backups`, `source/downtown/out`, plus all 17 loose maps; decoded all 987 world PNGs + 6 skybox faces via PIL; verified `QLIT v1` (`len == 8 + 3 * lighting_bytes`); searched repo/dist/zips/git history/CI for `zz_bakersfielddowntown.pk3`. | **0 corrupt PNGs, 0 `.bsp`/`.lit` mismatches** across all copies. Shipped `dist/BAKOQUAKE` BSP (`23.05 MiB`, SHA256 `6ec3b1cbf61d2e0e`) + `.lit` (`10.93 MiB`, `42b73b12102a3f56`) match the Zenbook's `Stats for q1bsp model` line digit-for-digit. **`zz_bakersfielddowntown.pk3` does NOT exist** in repo, `dist`, releases, or CI (likely an unmanaged stray file on the laptop or misread for `zz_johnbird.pk3` 7.66 MB / `zz_pinklady.pk3` 6.91 MB). *(Zenbook-local disk & `_backup_before_server_sync\maps\` could not be inspected from this desktop.)* | **REFUTED for shipped content**; **UNVERIFIED locally on Zenbook** (stray detection added to `bq_update.py` & `bq-report.ps1`). |
| **H2** | Oversized `2048×2048` PNG decode/upload spike (`image_png.c:81`, `gl_textures.c:984-985`, 16 MB × 3) & global/map texture RGBA footprint | Scanned every texture across `bakersfield.pk3`, `q15.pk3`, all `zz_*.pk3`, and loose folders; audited `image_png.c:62-85`, `gl_textures.c:975-995`, `gl_rmain.c:2804`; ran live `developer_loading 1` trace on `zircon_beta_gcc.exe`. | **Exact trigger confirmed**: `progs/megaman.png` (`2048×2048`, 692,517 B in `bakersfield.pk3`, loaded by `progs/megaman.md3` right after `Mod_Q1BSP_Load` on EVERY map) allocates 16 MB raw `lodepng` + 16 MB `image_png.c:81` + 16 MB × 2 resident `gl_textures.c:984-985` BEFORE `gl_picmip_other 1` downscales it. World textures are all `<= 512×512` (or `2048×128`), yet `bakersfielddowntown` uploads `7,734–7,742` textures (`1,028 MB` uploaded / `1,859 MB` orig under old low; `~2,368 MB` high-spec). Also discovered 20× `2048²` + 20× `2048×1024` (`480 MiB`) `nopicmip` NPC sheets on `soi6`/HTB. | **CONFIRMED (Primary Trigger & Major Memory Driver)** |
| **H3** | Missing Win32/SDL OS message pump during map load triggers Windows "Not Responding" (Event 1002 > 5.0 s) | Audited all event-pump call sites in Zircon source (`vid_sdl.c:1263`, `host.c:747`, `cl_screen.c`, `model_brush.c`); measured continuous `SendMessageTimeoutW` (`SMTO_ABORTIFHUNG`) non-responsive streaks every 200–250 ms across 14 maps on desktop. | `Sys_SendKeyEvents()` was called ONLY in `Host_Frame()` (`host.c:747`) — never during map, texture, model, lightmap, or GLSL loading. **Every map exceeded 5.0 s even on a Ryzen 7 7700X + NVMe + RTX 4070 Ti**: `5.84 s` (`aerowalk`), `9.47–10.56 s` (`bakersfielddowntown`), `16.26 s` (stock 8/30 engine). *(Zenbook Windows Event 1002 log itself could not be read from this host.)* | **CONFIRMED (Primary Root Cause of "Not Responding" Freeze)** |
| **H4** | System RAM / commit exhaustion, SSD pagefile thrashing, and broken `Mem_Alloc` OOM / deadlock path | Audited `zone.c:154-171,404-421`, `console.c:677`, `sys_sdl.c:65-86`, `host.c:1197-1199`, `model_brush.c:3089,7736`, `model_shared.c:1028`; executed bounded Windows Job Object commit-cap tests (`2500 / 2200 / 2000 / 1500 MB`) and `soi6 -> bdt` map-change tests. | Old `lowmem+lowgpu` needed `2,540–3,039 MB` commit (`3,318 MB` on `soi6 -> bdt`) on top of a `~1.45 GB` non-texture CPU floor (`116–124 MB` PVS, `31.7 MB` mesh, `17.2 MB` BIH, `52 MB` FreeType, up to `232 MB` `r_buffermegs_*` archive bloat). At **2000 MB commit cap**, stock 11/19 engine reproduced the **exact Zenbook silent hang** right after `gl_textures.c:985` (`0` OOM line, `0` dialog, hung until killed); at **2500 MB**, `soi6 -> bdt` hung `48.09 s` then crashed `0xC0000005`. Source confirmed `_Mem_Alloc` holds `mem_mutex` into `Log_ConPrint` -> `Mem_Alloc` recursion + 500× `Sleep(1)` retry stalls, and startup `+map` OOM wrote zero `bq_game.log`. | **CONFIRMED (Primary Root Cause of Silent Hang & Crash under Low Free RAM)** |
| **H5** | Stdio log buffering hiding subsequent loading steps after `gl_textures.c:985` | Audited `Log_ConPrint` (`console.c:627`) -> `FS_Write` (`fs.c:3427`) -> `WriteAll` (`fs.c:164`) -> `write(fd)` (`fs.c:111`); compared `developer 0` vs `developer_loading 1` live traces. | `bq_game.log` uses **unbuffered per-line raw OS `write(fd)`** — nothing is held in stdio buffers. Silence after `gl_textures.c:985` happens because `developer_memorylargerthanmb` is `16 MB` and all ~6,700 Phase 2 model/sprite textures are `< 16 MB` (0 log lines during 85% of load time). Separately, `Log_Start()` ran after `CL_StartVideo()`, causing missing logs on startup `+map` OOM. | **REFUTED for stdio buffering**; **CONFIRMED for silent Phase 2 + late `Log_Start()`** |
| **H6** | Launcher auto-tiering misclassification & config override bugs (`Play.cmd`, `lowmem.cfg`, `lowgpu.cfg`, `bm_up_legacy.cfg`, `menu_background`) | Audited all Windows/Linux/macOS launchers and startup config chain (`quake.rc`, `default.cfg`, `lowmem.cfg`, `lowgpu.cfg`, `bm_up_legacy.cfg`, `config.cfg`); probed live WMI vs 64-bit registry VRAM on desktop (incl. Parsec VDD). | Found **6 bugs**: (1) total RAM cached once (`15.6 GB` rounded to `16 GB` passed `<10 GB`), live free RAM never read; (2) WMI `uint32` `AdapterRAM` caps/wraps at `4095 MB` (verified live on RTX 4070 Ti: WMI `4095 MB` vs registry `12282 MB`) and `-Maximum` didn't filter virtual adapters (`Parsec VDD` `ROOT\DISPLAY\0000`) or detect iGPUs; (3) no `ultralow`/`safemode` tier (`lowmem.cfg` only set 2 cvars); (4) `Play.cmd:103` wrote `lowgpu-applied.txt` immediately after async `start ""` before clean exit; (5) `bm_up_legacy.cfg:64-74` overwrote `lowspec 1` after `config.cfg`; (6) `menu_background 1` added a `+750 MB` map-change spike. | **CONFIRMED (Primary Root Cause of Under-Tiering)** |
| **H7** | Extreme `bakersfielddowntown` BSP complexity (visleaf explosion, face count, world texture count, stacked entity precaches) | Compared `bakersfielddowntown` (dist & repo) against all 17 loose maps + `start.bsp`; audited `source/downtown/` (`make_downtown.py`, `build_downtown.sh`, `qbsp.log`) and Zircon BSPX support. | `bakersfielddowntown` has `105,173` faces (`116,400` repo), `31,200` visleafs (`32,209` repo — `8,669` `func_detail_wall` brushes split Hull-0 leaves -> `116–124 MiB` dense PVS matrix), `929` miptex (`218 MiB` world RGBA, **4.5–15×** other large maps), AND simultaneously loads `npc_crowd` (`109 MiB`), all 6 go-kart classes (`155 MiB`), 7/8 vehicle classes (`90 MiB`), and `143` `misc_model`s (`35 MiB`). Also proved Zircon has **zero BSPX support** (native WAD2 miptex scaling required). | **CONFIRMED (Major Secondary Amplifier — addressed by on-demand PVS, `ultralow.cfg`, and `bakersfielddowntown_lite`)** |
| **H8** | Intel Iris Xe OpenGL driver (`32.0.101.5768`) GLSL/S3TC stall, Parsec VDD adapter interference, and laptop `ezquake.exe` crash dump | Verified Parsec VDD WMI behavior live on desktop; checked Zircon `R_GLSL_CompilePermutation` + S3TC (`gl_texturecompression 1`) on RTX 4070 Ti; verified `HANDOFF_memory_diet.md` (unrelated ezQuake doc). | Parsec VDD virtual adapter hazard verified live and excluded in `bq-preflight.ps1` / `bq-report.ps1`; `R_GLSL_CompilePermutation` now pumps OS events & logs slow compiles; `safemode.cfg` keeps `gl_texturecompression 0` + `gl_max_size 256` as an S3TC-free fallback. **Live Intel Iris Xe `32.0.101.5768` driver behavior, Zenbook Event `1000`/`1002`/`4101`/`2004` logs, and Zenbook `%LOCALAPPDATA%\CrashDumps` (`ezquake.exe` dump) could NOT be inspected on this desktop.** | **PARTIALLY ADDRESSED / UNVERIFIED ON LIVE IRIS XE HARDWARE** |

---

## 3. Before vs After Measurements

All live runs executed in isolated temporary `-userdir` folders at `1280×800` windowed (except `safemode.cfg`, `1024×640` windowed), leaving the host `config.cfg` untouched. Pre-quit Peak WS / Commit / GPU metrics exclude NVIDIA OpenGL `glDeleteTextures` shutdown bursts.

### 3.1 Headline Before vs After Comparison (`bakersfielddowntown` & `bakersfielddowntown_lite`)

| Configuration | Engine | Load (s) | Max Load Hang (s) | Peak WS (MB) | Peak Commit (MB) | Peak GPU Ded (MB) | Gameplay `timedemo` FPS *(1s min / avg / max)* | Bounded Cap Result (`2048 MB` / `1500 MB`) |
|---|---|---:|---:|---:|---:|---:|---|---|
| **Before: High-Spec `normal`** | stock 11/19 (`9be0edb3`) | 10.43 | **9.86** *(Event 1002)* | 1,111 | 3,993–4,933 | 2,686–5,515 | 374.9 (`204 / 429 / 842`) | N/A (high-spec) |
| **Before: Old `lowmem+lowgpu`** | stock 11/19 (`9be0edb3`) | 10.03–11.29 | **9.47–10.56** *(Event 1002)* | 1,047–1,148 | 2,540–3,039 | 1,346–2,263 | 472.6 (`194 / 539 / 893`) | **FAIL** @ 2500 / **SILENT HANG** @ 2000 |
| **After: High-Spec `normal`** | **`zircon_beta_gcc.exe` (`8b566489`)** | **9.90** | **0.62–0.71** (**-15×**) | 1,021–1,033 | **3,901** *(-92 MB)* | **2,639** | **392.2 (+4.6%)** (`207 / 448 / 840`) | **ZERO high-spec regression (faster + 15× more responsive)** |
| **After: `lowmem+lowgpu`** | **`zircon_beta_gcc.exe` (`8b566489`)** | — | **0.51** (**-19×**) | 928 | **2,414** *(-151 MB)* | **1,330** | **547.5 (+15.8%)** (`247 / 614 / 1042`) | — |
| **After: `ultralow.cfg` (`bdt`)** | **`zircon_beta_gcc.exe` (`8b566489`)** | **9.13–9.32** | **0.61–0.73** (**-16×**) | **887–1,029** | **1,320–1,542** (**-65% vs high**) | **349–402** (**-85% vs high**) | **542.5 (+14.8% vs old low)** (**`256 / 607 / 1053`**, **+32% min FPS**) | **PASS 2048 MB** AND **PASS 1500 MB** (`1,339.9 MB`) |
| **After: `safemode.cfg` (`bdt`)** | **`zircon_beta_gcc.exe` (`8b566489`)** | **8.93** | **0.61** | **942** | **1,294** | **280** | — *(no S3TC, 1024×640)* | **PASS 2048 MB** (`754 MB` headroom) |
| **After: `ultralow.cfg` (`bdt_lite`)** | **`zircon_beta_gcc.exe` (`8b566489`)** | **7.07–7.26** | **0.61–1.01** | **739–744** | **1,089–1,135** (**-72% vs high**) | **283–323** | `timerefresh`: **948.1 fps** | **PASS 2048 MB** AND **PASS 1500 MB** (`1,135.2 MB`, `365 MB` headroom) |
| **After: `safemode.cfg` (`bdt_lite`)** | **`zircon_beta_gcc.exe` (`8b566489`)** | **7.06** | **0.61** | **750** | **1,053** | **245** | — *(no S3TC, 1024×640)* | **PASS 2048 MB** (`995 MB` headroom) |
| **Map Change `soi6 -> bdt`** | stock -> **`8b566489`** | — -> **7.52** | **48.09 s -> 0.84 s** | — -> **1,012** | **3,318 -> 1,379 (-58.4%)** | **1,722 -> 354** | — | **CRASH `0xC0000005` @ 2500 MB -> PASS @ 2048 MB** |

*(Gameplay `timedemo` used `demos/2026-11-18_09-07_bakersfielddowntown_1_local-2`, 4,227 frames.)*

### 3.2 Suite 1A & 1B: 3× Consecutive Cold Starts (`ultralow`) + Non-S3TC `safemode` (`CommitCapMB = 2048`)

| Suite & Run | Tier | Status | Load (s) | Max Hang (s) | Peak Commit (MB) | Peak GPU Ded (MB) |
|---|---|---|---:|---:|---:|---:|
| **Suite 1A** `bakersfielddowntown` (run 1 / 2 / 3) | `ultralow` | **3/3 PASS** | `9.30 / 9.13 / 9.28` | **`0.62 / 0.61 / 0.61`** | **`1,320.1 / 1,451.2 / 1,366.6`** | `349.3 / 372.6 / 353.6` |
| **Suite 1A** `bakersfielddowntown_lite` (run 1 / 2 / 3) | `ultralow` | **3/3 PASS** | `7.08 / 7.07 / 7.26` | **`0.63 / 0.61 / 0.62`** | **`1,088.6 / 1,089.9 / 1,122.4`** | `283.1 / 290.0 / 299.0` |
| **Suite 1B** `bakersfielddowntown` | `safemode` *(no S3TC)* | **PASS** | `8.93` | **`0.61`** | **`1,293.9`** | **`280.2`** |
| **Suite 1B** `bakersfielddowntown_lite` | `safemode` *(no S3TC)* | **PASS** | `7.06` | **`0.61`** | **`1,052.5`** | **`244.8`** |

### 3.3 Suite 2A & 2B: ALL 18 Shipped Maps + Map Change + Graceful OOM (`CommitCapMB = 2048`, `ultralow`) + Tight `1500 MB` Cap

**Suite 2A (`s2a_allmaps`, exit `0`, 20 / 20 PASS — budgets: Load `<= 30 s`, Hang `<= 4.5 s`, Commit `<= 2000 MB`):**

| # | Map / Check | Status | Load (s) | Max Hang (s) | Peak Commit (MB) | Peak GPU Ded (MB) | Notes / Before Comparison |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | `bakersfielddowntown` | **PASS** | 9.32 | **0.61** | **1,542.1** | 402.4 | Before: `2,540–3,039 MB`, `9.47–10.56 s` hang |
| 2 | `bakersfielddowntown_lite` | **PASS** | 7.07 | **0.62** | **1,091.9** | 287.0 | New lightweight variant (`-450 MB` vs `bdt`) |
| 3 | `bklan6` | **PASS** | 10.28 | **1.65** | **1,477.2** | 386.1 | Before: `2,600 MB`, `10.35 s` hang |
| 4 | `morrorock` | **PASS** | 7.46 | **0.61** | **1,503.9** | 391.1 | Before: `1,860 MB`, `7.45 s` hang |
| 5 | `lolmap1` | **PASS** | 9.37 | **1.86** | **1,200.9** | 304.2 | — |
| 6 | `slo_bike_kitchen` | **PASS** | 6.96 | **0.62** | **1,197.8** | 318.4 | — |
| 7 | `goldenwest` | **PASS** | 7.09 | **0.61** | **1,182.9** | 298.2 | Before: `2,306 MB` (`139 MB` PVS -> on-demand), `7.35 s` hang |
| 8 | `spruce` | **PASS** | 7.27 | **0.62** | **1,179.6** | 299.4 | Before: `1,855 MB`, `7.66 s` hang |
| 9 | `terminal21` | **PASS** | 6.81 | **0.62** | **1,164.3** | 305.3 | Before: `2,090 MB` (`131 MB` PVS -> on-demand), `7.26 s` hang |
| 10 | `soi6` | **PASS** | 7.65 | **0.62** | **1,162.9** | 309.8 | Before: `2,549 MB` (**-54.4%!** `284 MB` PVS -> `5.7 MB`, 14× 16 MB PNGs -> 0×) |
| 11 | `practice` | **PASS** | 8.22 | **0.61** | **1,094.6** | 269.5 | Before: `2,042 MB`, `8.75 s` hang |
| 12 | `soicowboy_bkk` | **PASS** | 7.45 | **0.62** | **1,074.4** | 292.9 | — |
| 13 | `fox` | **PASS** | 8.00 | **0.61** | **1,067.6** | 295.8 | Before: `2,234 MB`, `8.14 s` hang |
| 14 | `little_st_james` | **PASS** | 7.08 | **0.62** | **1,045.4** | 288.0 | Before: `1,710 MB`, `7.54 s` hang |
| 15 | `hart` | **PASS** | 6.03 | **0.61** | **963.6** | 266.2 | `82.5 MB` PVS -> on-demand |
| 16 | `ooika_lawrenceville` | **PASS** | 6.36 | **0.61** | **942.9** | 272.0 | — |
| 17 | `aerowalk` | **PASS** | 5.94 | **0.62** | **859.4** | 287.6 | Before: `1,340 MB`, `5.84 s` hang |
| 18 | `kyle_range` | **PASS** | 5.85 | **0.63** | **838.6** | 293.5 | — |
| 19 | `mapchange_soi6_to_bakersfielddowntown` | **PASS** | 7.52 | **0.84** | **1,379.4** | 353.7 | Before: `3,318 MB` uncapped; `48.09 s` hang + `0xC0000005` @ 2500 MB cap |
| 20 | `oom_graceful_bakersfielddowntown_400mb` | **PASS** | — | **0.61** | 399.8 | — | Flushed readable `Engine Error: Mem_Alloc: out of memory (1.656MB at model_brush.c:2509)` — zero silent hang |

**Suite 2B — Tight `1500 MB` Commit Cap (`ultralow`, exit `0`, 2 / 2 PASS):**
- `bakersfielddowntown`: load `9.24 s`, max hang **`0.62 s`**, peak commit **`1,339.9 MB`** (`160 MB` headroom under 1.5 GB cap).
- `bakersfielddowntown_lite`: load `7.15 s`, max hang **`1.01 s`**, peak commit **`1,135.2 MB`** (`365 MB` headroom under 1.5 GB cap).

### 3.4 Post-Deploy Smoke Verification (`G:\Quake\Combat\engine\zircon_beta_gcc.exe`, SHA256 `8b566489...`)

Command: `source/ci/test_lowmem_maps.ps1 -Maps bakersfielddowntown,bakersfielddowntown_lite -Tier ultralow -CommitCapMB 2048 -TestOOMGraceful` -> **3 / 3 PASS (exit `0`, 0 stray Zircon processes)**:

| Run | Status | Load (s) | Longest Hang (s) | Peak WS (MB) | Peak Commit (MB) | Peak GPU Ded (MB) | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `bakersfielddowntown` | **PASS** | 10.12 | **0.61** | 949.5 | **1,438.9** | 387.6 | Under `2048 MB` Job Object cap |
| `bakersfielddowntown_lite` | **PASS** | 7.84 | **0.61** | 736.9 | **1,153.2** | 329.8 | Under `2048 MB` Job Object cap |
| `oom_graceful (400 MB)` | **PASS** | — (2.40 s wall) | **0.64** | 173.1 | 389.1 | 169.0 | Clean flushed `Engine Error: Mem_Alloc: out of memory (11.827MB at sv_ccmds.c:189)` |

Independent post-deploy verification (`@verifier`) additionally confirmed byte-for-byte identity of `G:\Quake\Combat\engine\zircon_beta_gcc.exe` (`8b566489...`) vs `zircon_beta_lowmem.exe`, intact original engine backup (`9be0edb3...`), intact `source/zircon-lowmem-stability.patch` (`ca10ac1a...`), and `0` AST errors / `aerowalk` `-MinFps 100` PASS (`1,347.4 fps`, `0.61 s` hang) on the finalized `source/ci/test_lowmem_maps.ps1`.

### 3.5 Map-Side Optimization Comparison (`bakersfielddowntown` vs `bakersfielddowntown_lite`)

| Metric | `bakersfielddowntown` (DIST shipped) | `bakersfielddowntown` (REPO full) | **`bakersfielddowntown_lite`** | Delta vs DIST (vs REPO) |
|---|---:|---:|---:|---:|
| **BSP size (MiB)** | 23.05 (`24,167,204 B`) | 24.89 (`26,104,056 B`) | **18.47** (`19,366,972 B`) | **-19.9%** (-25.8%) |
| **LIT size (MiB)** | 10.93 (`11,462,588 B`) | 11.15 (`11,690,612 B`) | **6.69** (`7,016,960 B`) | **-38.8%** (-40.0%) |
| **Lighting lump / Vis lump (MiB)** | `3.64 / 4.82` | `3.72 / 5.45` | **`2.23 / 3.35`** | **-38.8% / -30.5%** |
| **Avg visible leafs / cluster** | ~6,722 | 6,722 | **3,720** | **-44.7%** |
| **Faces / Verts / Tris** | `105,173 / 447,186 / 236,840` | `116,400 / 493,733 / 260,933` | **`89,993 / 384,056 / 204,070`** | **-14.4% / -14.1% / -13.8%** |
| **Nodes / Leafs / Visleafs** | `55,657 / 32,148 / 31,200` | `58,560 / 34,039 / 32,209` | **`50,951 / 29,693 / 28,780`** | **-8.5% / -7.6% / -7.8%** |
| **Uncompressed PVS (MiB, stock)** | 116.0 | 123.7 | **98.8** *(3.9 MB w/ on-demand)* | **-14.9%** (-20.1%) |
| **Unique MipTex / Entity Precache Diet** | 929 / baseline | 927 / +23 MiB | **871 / -325 MiB RGBA (-415 w/mips)** | `0` leaks, `0` missing tex, `lint_entities.py` `0` err/`0` warn |

### 3.6 Launcher, Preflight, Diagnostic & Updater Verification
- **`tools/bq-preflight.ps1` end-to-end suite** (isolated `-StateDir`, 0 AST errors):
  - Real desktop (`31.1 GB`, `5,110–5,718 MB` free, RTX 4070 Ti `12,282 MB [dGPU]`, AMD `[iGPU]`, Parsec `[VIRTUAL]` excluded) -> **`normal`** (`ARGS=""`).
  - Simulated Zenbook (`15.6 GB`, `200 MB` free, Iris Xe `2,048 MB [iGPU]`) -> **`ultralow`** (`+exec ultralow.cfg`, `MARK_LOWGPU=1`).
  - Simulated 8 GB laptop (`4,000 MB` free) -> **`ultralow`**.
  - Simulated 16 GB + 6 GB dGPU (`8,000 MB` free) -> **`normal`** (`ARGS=""`).
  - Simulated clean Zenbook (`15.6 GB`, `8,000 MB` free, Iris Xe `2,048 MB [iGPU]`) -> **`lowmem`** (`+exec lowmem.cfg +exec lowgpu.cfg`).
  - Unclean exit (`session-active.flag`) -> **`safemode`** (`+exec safemode.cfg`), preserved `bq_game_crash.log`, snapshotted & restored `config.pre-temp.cfg` cleanly (both watchdog-exit and watchdog-skipped fallback).
  - Live `cmd.exe` test of `Play.cmd` + `bq-preflight.ps1` + C# stub binary confirmed `USED_PREFLIGHT=1`, `BQ_PRE_ARGS`, `BQ_PRE_CANCEL=1`, `-WatchMarkLowGpu`, `-WatchRestoreConfig`, and updater exit-code blocking (`0, 1, 2, 3, 4, 5, -1073741819`).
- **Updater tests (`python -m unittest discover -s source/ci/tests -v`)**: **26 / 26 PASSED** (incl. lock wait/exit 4, unexpected error exit 4, `fsync`, post-replace `.bsp`/`.lit`/`.pk3` re-hash + rollback, `UpdateCancelled` during verify rollback, lagging fallback repair/block, strict `fetch_url`, unmanaged stray detection).
- **Shell launchers (`bash -n` + pure LF check)**: `launchers/Play.sh`, `launchers/Start-Server.sh`, `launchers/Update.sh`, `source/mac/launcher.sh` — **ALL PASS**.
- **Diagnostic reporter (`tools/bq-report.ps1` + `Report a Problem.cmd`)**: Tested live against `G:\Quake\Combat` (7.4 KB zip, 50 asset SHA256s, RTX 4070 Ti 12,282 MB 64-bit reg vs WMI 4,095 MB, Parsec `[VIRTUAL]`, Event 1000 separated) + synthetic mock install (**11 / 11 assertions PASS**).

---

## 4. Complete Change Log & Undo Instructions

All 21 modified files were backed up **before** our Phase 2 edits into `G:\Quake\Combat\_backups\lowspec_fix_20261122\` (preserving the user's pre-existing uncommitted Updater v2 / MenuQC edits). Every backup file below has been **verified present on disk with exact byte size and SHA-256**.

### 4.1 Untouched Protected Assets (Verified Unchanged)
- `G:\Quake\Combat\BakersfieldQuake\bakersfield.pk3` — `502,843,735 B`, SHA256 `341c939d7138d2d67c7591ff8b0046c402eea08fbed733cf2c5399156c2e2af9`
- `G:\Quake\Combat\quake15\q15.pk3` — `476,862,746 B`, SHA256 `1e7d903a601658187e90dd345583d299c93918a8cadf1fdea659931d2831a7ea`
- `G:\Quake\Combat\BakersfieldQuake\maps\bakersfielddowntown.bsp` — `26,104,056 B`, SHA256 `963d269e59909e8910c535eabbdcb2bbcc8ab64756b10f9354d0766156ce64ce`
- `G:\Quake\Combat\BakersfieldQuake\maps\bakersfielddowntown.lit` — `11,690,612 B`, SHA256 `b30cded792ad269bbd4882b5ce113d796e602d0c72342ff10a5bbafb10830338`

### 4.2 Modified Existing Files (All 21 Backed Up & Verified)

| File | Backup Location (`G:\Quake\Combat\_backups\lowspec_fix_20261122\...`) | Before *(size / sha256-12)* | After *(size / sha256-12)* | Why | Exact Undo Command (PowerShell) |
|---|---|---|---|---|---|
| `G:\Quake\Combat\engine\zircon_beta_gcc.exe` | `engine\zircon_beta_gcc.exe` | `8,921,537 B` (`9be0edb3fe88`) — Nov 19 build (`0910498`), no load pump, no `mod_freebeforeload`, 16 MB × 3 PNG spike, dense PVS, OOM deadlock | `8,934,337 B` (`8b5664891bd1`) — `lowmem-stability` (`66bcfa2`): load event pump, `mod_freebeforeload`, PNG/resize fix, gated norm/gloss, lazy `render_bih` (default `0`), on-demand PVS LRU, 3D-only `gl_picmip_force`, OOM deadlock fix + early log flush | Eliminates >5 s Event 1002 hangs (-15×), cuts 115–283 MB PVS + 48 MB PNG/resize spike, prevents OOM silent deadlock | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\engine\zircon_beta_gcc.exe' 'G:\Quake\Combat\engine\zircon_beta_gcc.exe'` |
| `lowmem.cfg` | `lowmem.cfg` | `938 B` (`54fb1c432d44`) — only `gl_picmip_other 1` & `r_shadow_shadowmapping_texturesize 2048` | `1,230 B` (`3615200fa207`) — shadow atlas `1024`, `mod_freebeforeload 1`, `mod_q1bsp_pvs_ondemand 1`, `mod_q1bsp_lazy_render_bih 1`, `menu_background 0`, reset `r_buffermegs_*`/`r_framedatasize` | Enables engine memory-diet cvars and eliminates `+750 MB` `menu_background` & `232 MB` archived buffer bloat | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\lowmem.cfg' 'G:\Quake\Combat\BakersfieldQuake\lowmem.cfg'` |
| `lowmem_off.cfg` | `lowmem_off.cfg` | `375 B` (`4ddf2a727558`) — only restored `gl_picmip_other 0` & shadowmap `4096` | `632 B` (`15dfd6c6ece1`) — restores all `gl_picmip*`, `gl_picmip_force 0`, `gl_max_size 2048`, `gl_texturecompression 0`, `menu_background 1`, `r_buffermegs_*` | Cleanly undoes `lowmem.cfg` / `ultralow.cfg` / `safemode.cfg` | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\lowmem_off.cfg' 'G:\Quake\Combat\BakersfieldQuake\lowmem_off.cfg'` |
| `lowgpu.cfg` | `lowgpu.cfg` | `1,419 B` (`1cd3139f9cdd`) — omitted normal/gloss load gates & FPS cap | `1,108 B` (`8479268c2cac`) — added `r_load_normalmap 0`, `r_load_gloss 0`, `r_shadow_usenormalmap 0`, `r_glsl_deluxemapping 0`, `cl_maxfps 60` (no `saveconfig` so temporary tiers never poison `config.cfg`) | Stops iGPUs from uploading unused `_norm`/`_gloss` textures and reduces laptop GPU/thermal load | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\lowgpu.cfg' 'G:\Quake\Combat\BakersfieldQuake\lowgpu.cfg'` |
| `lowgpu_off.cfg` | `lowgpu_off.cfg` | `752 B` (`42743d9b47eb`) — restored older `lowgpu.cfg` subset | `906 B` (`59d3fc3ce6f5`) — restores `r_load_normalmap/gloss 1`, `r_shadow_usenormalmap 1`, `r_glsl_deluxemapping 1`, `r_dynamic 1`, `r_lerplightstyles 1`, `gl_texturemode`, `cl_maxfps 250`, `menu_background 1`, `saveconfig` | Cleanly restores high-spec defaults | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\lowgpu_off.cfg' 'G:\Quake\Combat\BakersfieldQuake\lowgpu_off.cfg'` |
| `bm_up_legacy.cfg` | `bm_up_legacy.cfg` | `2,959 B` (`566f1a6fd7da`) — unconditionally forced anisotropy 16 / bloom / RT shadows / offsetmapping after `config.cfg` | `3,124 B` (`5cda7233dbfe`) — guarded high-quality overrides behind `_bm_leg_gfx_$lowspec` (100% unchanged for `lowspec 0`, no-op for `lowspec 1`) | Prevents legacy migrations (`bm_defver` 1–11) from clobbering saved `lowspec 1` settings | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\bm_up_legacy.cfg' 'G:\Quake\Combat\BakersfieldQuake\bm_up_legacy.cfg'` |
| `launchers\Play.cmd` | `launchers\Play.cmd` | `8,243 B` (`e1e35b112fcb`) — cached total RAM & 32-bit WMI VRAM, no live free RAM / watchdog / crash recovery, wrote `lowgpu-applied.txt` prematurely, only blocked updater exit `4` | `9,060 B` (`44f269aba31d`) — calls `tools\bq-preflight.ps1` + detached watchdog (with hoisted vars & batch fallback), blocks any non-0/non-3 updater exit, locked-safe log rotation | Enables 4-tier live auto-tiering, low-RAM warning, safe-mode crash recovery, and safe updater gating | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\launchers\Play.cmd' 'G:\Quake\Combat\BakersfieldQuake\launchers\Play.cmd'` |
| `launchers\Start Server.cmd` | `launchers\Start Server.cmd` | `9,708 B` (`6c686b0f4c31`) — same tiering/updater/premature-write gaps as `Play.cmd` | `10,078 B` (`dad09334c6e3`) — integrated `bq-preflight.ps1 -ServerMode` + detached watchdog + non-0/non-3 updater block + locked-safe log rotation | Brings LAN server client launches to parity with `Play.cmd` without offering `+map` before `+connect` | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\launchers\Start Server.cmd' 'G:\Quake\Combat\BakersfieldQuake\launchers\Start Server.cmd'` |
| `launchers\Play.sh` | `launchers\Play.sh` | `5,900 B` (`9852a157f933`) — total RAM `<10 GB` check only | `7,497 B` (`8bdd6f5ada87`) — live `MemAvailable` + 4-tier (`normal`/`lowmem`/`ultralow`/`safemode`), updater non-0/non-3 block, `bq_game_crash.log` preservation | Linux live-memory auto-tiering and crash-log preservation | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\launchers\Play.sh' 'G:\Quake\Combat\BakersfieldQuake\launchers\Play.sh'` |
| `launchers\Start-Server.sh` | `launchers\Start-Server.sh` | `6,469 B` (`b398f0c3f40b`) — total RAM `<10 GB` check only | `8,247 B` (`470e97f9e386`) — live `MemAvailable` + 4-tier auto-tiering, updater block, crash log preservation | Linux LAN-server parity with `Play.sh` | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\launchers\Start-Server.sh' 'G:\Quake\Combat\BakersfieldQuake\launchers\Start-Server.sh'` |
| `source\mac\launcher.sh` | `source\mac\launcher.sh` | `6,385 B` (`364a16234d71`) — `hw.memsize` `<10 GB` check only | `7,394 B` (`2759779ea90b`) — live `vm_stat` available RAM + 4-tier auto-tiering (`ultralow`/`safemode`), updater block | macOS live-memory auto-tiering parity | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\source\mac\launcher.sh' 'G:\Quake\Combat\BakersfieldQuake\source\mac\launcher.sh'` |
| `launchers\Report a Problem.cmd` | `launchers\Report a Problem.cmd` | `1,268 B` (`398a69ddc84c`) — ran `bq-report.ps1` without PowerShell error pause/reporting | `1,774 B` (`f0151b87b0a6`) — readable error reporting + pause on failure, prints Desktop zip path & opens Explorer `/select` | Reliable one-click crash diagnostic bundle for players | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\launchers\Report a Problem.cmd' 'G:\Quake\Combat\BakersfieldQuake\launchers\Report a Problem.cmd'` |
| `tools\bq-report.ps1` | `tools\bq-report.ps1` | `6,619 B` (`f77c231d838f`) — single plain `.txt` with truncated logs, 20-cvar grep, 32-bit VRAM, English-only Event regex | `32,882 B` (`34aa65fe8457`) — creates `Desktop\BAKOQUAKE-report-YYYYMMDD-HHMMSS.zip` (full raw logs, `config.cfg`, `.bq/*`, `last-launch.txt`, rich `summary.txt`: 64-bit VRAM + `[VIRTUAL]`/`[iGPU]`/`[dGPU]`, locale-independent Events `1000/1001/1002/4101/2004`, active map + GL renderer, full SHA-256 asset & stray audit) | Captures complete root-cause evidence from any player PC in one zip | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\tools\bq-report.ps1' 'G:\Quake\Combat\BakersfieldQuake\tools\bq-report.ps1'` |
| `tools\bq_update.py` | `tools\bq_update.py` | `69,088 B` (`c711779008b4`) — lock race returned `0`, unexpected `--launch` errors returned `0`, no `fsync` or post-replace re-hash, lagging fallback skipped local verification, strays invisible | `78,928 B` (`67d55c0a0499`) — lock wait up to 20 s then exit `4`, unexpected errors exit `4`, `_fsync_file()` on staged downloads & `state.json`, post-replace size + SHA-256 re-hash w/ atomic rollback (incl. `UpdateCancelled`), lagging-fallback integrity verification, strict `fetch_url`, `find_unmanaged_strays()` warnings | Guarantees half-written or mismatched `.bsp`/`.lit`/`.pk3`/`.exe` files cannot slip through updates | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\tools\bq_update.py' 'G:\Quake\Combat\BakersfieldQuake\tools\bq_update.py'` |
| `source\ci\tests\test_bq_update.py` | `source\ci\tests\test_bq_update.py` | `20,196 B` (`684e6c11df43`) — 18 unit tests | `30,044 B` (`7a2f19a1acf1`) — 26 unit tests (+8 covering lock exit 4, error exit 4, fsync, post-replace rollback, cancel-during-verify rollback, lagging fallback, strict `fetch_url`, stray detection) | Proves updater integrity & rollback fixes stay regression-free | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\source\ci\tests\test_bq_update.py' 'G:\Quake\Combat\BakersfieldQuake\source\ci\tests\test_bq_update.py'` |
| `.github\workflows\build-zip.yml` | `.github\workflows\build-zip.yml` | `41,118 B` (`603d32d15271`) — package check omitted new configs/tools & `_lite` map check | `41,946 B` (`e22a33b743d7`) — added `lowmem.cfg`, `lowgpu.cfg`, `ultralow.cfg`, `safemode.cfg`, `Report a Problem.cmd`, `tools/bq-preflight.ps1`, `tools/bq-report.ps1` + `bakersfielddowntown_lite` `.bsp`/`.lit` pairing verification | Ensures CI releases verify all new low-spec files ship cleanly | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\.github\workflows\build-zip.yml' 'G:\Quake\Combat\BakersfieldQuake\.github\workflows\build-zip.yml'` |
| `source\downtown\tools\build_downtown.sh` | `source\downtown\tools\build_downtown.sh` | `3,060 B` (`a88cfeb3aa81`) — full build only; missing `/g/Quake/Combat/tools/ericw` lookup | `3,727 B` (`51a2ed12e117`) — added `DT_LITE=1` reproducible build mode (`VISDIST=2500`, `qbsp -maxnodesize 2048`, `light -extra`, outputs `bakersfielddowntown_lite.*`) + local ericw fallback; `DT_LITE=0`/unset 100% unchanged | Reproducibly builds `bakersfielddowntown_lite` without altering full `bakersfielddowntown` | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\source\downtown\tools\build_downtown.sh' 'G:\Quake\Combat\BakersfieldQuake\source\downtown\tools\build_downtown.sh'` |
| `source\downtown\tools\make_downtown.py` | `source\downtown\tools\make_downtown.py` | `17,969 B` (`02df070175fe`) — full map generation only | `25,130 B` (`dd78df852f0e`) — added `ctx.is_lite`, native WAD2 lightmap density diet (`out/dt_all_lite.wad`, zero BSPX), and `apply_lite_diet(ctx)` (`-325 MiB` entity precache RGBA, micro-brush trim) | Cuts `bakersfielddowntown_lite` BSP -20%, LIT -39%, avg visible leafs -45%, commit -25% vs full `bdt` | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\source\downtown\tools\make_downtown.py' 'G:\Quake\Combat\BakersfieldQuake\source\downtown\tools\make_downtown.py'` |
| `source\downtown\pieces\lighting.py` | `source\downtown\pieces\lighting.py` | `16,473 B` (`d4a8f0463c81`) — single fog range `3650..5250` | `16,684 B` (`bb119c0962d3`) — tighter fog `2400..3600` when `ctx.is_lite` (matched to `VISDIST=2500`) | Hides `VISDIST=2500` vis cutoff smoothly in `_lite` | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\source\downtown\pieces\lighting.py' 'G:\Quake\Combat\BakersfieldQuake\source\downtown\pieces\lighting.py'` |
| `source\downtown\pieces\streets.py` | `source\downtown\pieces\streets.py` | `100,193 B` (`207dd39e2d72`) — always emitted 707 `build_markings` illus brushes | `100,408 B` (`ca30531d0a51`) — `is_bd_kart()` supports `bakersfielddowntown_lite`; skips 707 pavement marking brushes when `ctx.is_lite` | Cuts surface/face count on `_lite` with minimal visual difference | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\source\downtown\pieces\streets.py' 'G:\Quake\Combat\BakersfieldQuake\source\downtown\pieces\streets.py'` |
| `source\downtown\pieces\padre.py` | `source\downtown\pieces\padre.py` | `84,500 B` (`5f3081677517`) — emitted 131 `func_breakable` panes + ~780 `0.12`-ft casings | `84,639 B` (`dbbc948cfc26`) — skips 131 `func_breakable` panes & tiny casings when `ctx.is_lite` | Cuts 131 bmodels and ~11k tiny faces on `_lite` | `Copy-Item -Force 'G:\Quake\Combat\_backups\lowspec_fix_20261122\source\downtown\pieces\padre.py' 'G:\Quake\Combat\BakersfieldQuake\source\downtown\pieces\padre.py'` |

### 4.3 Newly Created Files

| New File | Size / SHA-256 (12) | Purpose | Exact Undo Command (PowerShell) |
|---|---|---|---|
| `source\zircon-lowmem-stability.patch` | `66,273 B` (`ca10ac1af70b`) | Exported git patch (`4891861..66bcfa2` on branch `lowmem-stability` in `G:\Quake\_bq_fork_engine\src`, `git apply --check --reverse` PASS) reproducing the deployed `zircon_beta_gcc.exe` | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\source\zircon-lowmem-stability.patch'` |
| `ultralow.cfg` | `1,771 B` (`1f2569dd6a21`) | Automatic ultra-low tier (`picmip_world 1`, `picmip_other 2`, `picmip_sprites 1`, `gl_picmip_force 1`, `gl_max_size 512`, S3TC `gl_texturecompression 1`, engine memory-diet cvars, `alias bdt_lite`) | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\ultralow.cfg'` |
| `safemode.cfg` | `1,498 B` (`68995a09ddb6`) | Maximum-stability crash-recovery / non-S3TC fallback (`gl_texturecompression 0`, `gl_max_size 256`, `gl_picmip 2`, `1024×640` windowed, `gl_picmip_force 1`, engine diet cvars) | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\safemode.cfg'` |
| `tools\bq-preflight.ps1` | `30,489 B` (`2e335329cee7`) | Windows 64-bit VRAM + live free-RAM hardware probe, `[VIRTUAL]`/`[iGPU]`/`[dGPU]` classification, 4-tier selection, low-RAM interactive dialog, temporary `config.pre-temp.cfg` snapshot/restore, crash recovery, and detached `SendMessageTimeoutW` watchdog | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\tools\bq-preflight.ps1'` |
| `source\ci\test_lowmem_maps.ps1` | `44,935 B` (`4dfd20f9c7d8`) | Permanent automated low-memory regression harness (isolated `-userdir`, Job Object commit cap, `SendMessageTimeoutW` hang tracking, all-maps, map-change, `-MinFps` enforcement, and 400 MB graceful OOM tests) | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\source\ci\test_lowmem_maps.ps1'` |
| `maps\bakersfielddowntown_lite.bsp` | `19,366,972 B` (`51ca9704a831`) | Optional lightweight Bakersfield Downtown variant (`DT_LITE=1`, 89,993 faces, `VISDIST=2500`, -325 MiB entity precache RGBA) | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\maps\bakersfielddowntown_lite.bsp'` |
| `maps\bakersfielddowntown_lite.lit` | `7,016,960 B` (`b7c853f6bffd`) | Exact `QLIT v1` lightmap companion for `bakersfielddowntown_lite.bsp` (`7,016,960 == 8 + 3 * 2,338,984`) | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\maps\bakersfielddowntown_lite.lit'` |
| `levelshots\bakersfielddowntown_lite.jpg` | `52,701 B` (`4b8bdc68162f`) | Loading-screen levelshot for `bakersfielddowntown_lite` | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\levelshots\bakersfielddowntown_lite.jpg'` |
| `docs\lowspec_crash_fix_report_2026-11-22.md` | *(this report)* | Full forensic report, measurements, change log, undo guide, and Zenbook runbook | `Remove-Item -Force 'G:\Quake\Combat\BakersfieldQuake\docs\lowspec_crash_fix_report_2026-11-22.md'` |

*(Engine fork build artifacts outside the game repo: branch `lowmem-stability` commit `66bcfa2` in `G:\Quake\_bq_fork_engine\src` and `G:\Quake\_bq_fork_engine\out\zircon_beta_lowmem.exe` [`8,934,337 B`, SHA256 `8b5664891bd1`]. Undo branch: `git -C G:\Quake\_bq_fork_engine\src checkout main`.)*

### 4.4 One-Shot Full Rollback Command (Restores All 21 Backups & Removes New Files)

```powershell
$bak = 'G:\Quake\Combat\_backups\lowspec_fix_20261122'
$repo = 'G:\Quake\Combat\BakersfieldQuake'
Copy-Item -Force "$bak\engine\zircon_beta_gcc.exe" 'G:\Quake\Combat\engine\zircon_beta_gcc.exe'
Get-ChildItem -Path $bak -Recurse -File | Where-Object { $_.FullName -notlike "$bak\engine\*" } | ForEach-Object {
    $rel = $_.FullName.Substring($bak.Length + 1)
    Copy-Item -Force $_.FullName (Join-Path $repo $rel)
}
@(
    'source\zircon-lowmem-stability.patch','ultralow.cfg','safemode.cfg',
    'tools\bq-preflight.ps1','source\ci\test_lowmem_maps.ps1',
    'maps\bakersfielddowntown_lite.bsp','maps\bakersfielddowntown_lite.lit',
    'levelshots\bakersfielddowntown_lite.jpg','docs\lowspec_crash_fix_report_2026-11-22.md'
) | ForEach-Object { Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $repo $_) }
```

---

## 5. What Could NOT Be Verified on This Host

To remain strictly honest about verification boundaries, the following items **could not be executed or observed** on this desktop host (Ryzen 7 7700X / 32 GB / RTX 4070 Ti) and MUST be verified directly on the player's laptop:

1. **Live ASUS Zenbook S 13 UX5304VA hardware & SSD pagefile pressure**: Real-world load times and FPS on Intel Core i5-1335U with 15.6 GB LPDDR5 and only ~0.2 GB free RAM while background apps (Chrome/etc.) contend for the 13 GB SSD pagefile. (Simulated via Windows Job Object `2048 MB` and `1500 MB` commit caps + `bq-preflight.ps1 -Simulate*` flags on desktop, not live Iris Xe unified memory.)
2. **Intel Iris Xe OpenGL driver (`32.0.101.5768`) S3TC & GLSL behavior**: Whether Intel's OpenGL ICD handles `gl_texturecompression 1` (S3TC DXT1/5 in `ultralow.cfg`) quickly and cleanly without driver stalls or visual artifacts, and exact Iris Xe GLSL permutation compile latency. (`safemode.cfg` deliberately keeps `gl_texturecompression 0` + `gl_max_size 256` as an immediate fallback if Intel's S3TC path misbehaves.)
3. **Zenbook-local Windows Event Logs & Crash Dumps**: Actual Windows Application Events `1000` / `1001` / `1002`, System Events `4101` (GPU TDR) / `2004` (low virtual memory), and `%LOCALAPPDATA%\CrashDumps` (including any unrelated `ezquake.exe` crash dump) on the Zenbook.
4. **Zenbook-local `_backup_before_server_sync\maps\` and reported `8.2 MB` `zz_bakersfielddowntown.pk3`**: Neither exists in this repo, `dist/BAKOQUAKE`, or any release zip (`v1.0`–`v1.14`); must be checked directly on the laptop's install folder.
5. **Live macOS & Linux runtime execution**: `launchers/Play.sh`, `launchers/Start-Server.sh`, and `source/mac/launcher.sh` passed `bash -n` syntax and LF line-ending checks, but live `vm_stat` (macOS) and `/proc/meminfo` (Linux) runtime execution were not tested on macOS/Linux hosts.
6. **GitHub Actions CI run of `.github/workflows/build-zip.yml`**: Validated YAML syntax and packaging globs locally; not pushed or executed in GitHub Actions per `AGENTS.md`.

---

## 6. Recommended Next Steps on the Zenbook Laptop

1. **Collect baseline Zenbook forensics first (before deleting any stray files)**:
   - Double-click **`Report a Problem.cmd`** (once the updated `tools\bq-report.ps1` and `launchers\Report a Problem.cmd` are on the laptop) to produce `Desktop\BAKOQUAKE-report-YYYYMMDD-HHMMSS.zip`.
   - Inspect `summary.txt` inside the zip for: (a) Application Events `1000`/`1002` and System Events `4101`/`2004`, (b) any `[UNMANAGED/STRAY]` `zz_bakersfielddowntown.pk3` or `[HASH_MISMATCH]` entries, and (c) Intel Iris Xe GL driver strings.
2. **Deploy the updated build to the Zenbook**:
   - Update `engine\zircon_beta_gcc.exe` (`8,934,337 B`, SHA256 `8b5664891bd1cdd5076738022b283c1ad681f7f45be85044db322e81292c2fc6`), the updated `lowmem*.cfg`, `lowgpu*.cfg`, `bm_up_legacy.cfg`, new `ultralow.cfg` & `safemode.cfg`, updated `launchers\Play.cmd`, `Start Server.cmd`, `Report a Problem.cmd`, `tools\bq-preflight.ps1`, `tools\bq-report.ps1`, `tools\bq_update.py`, `source\ci\test_lowmem_maps.ps1`, and `maps\bakersfielddowntown_lite.bsp`/`.lit` + `levelshots\bakersfielddowntown_lite.jpg`.
   - Remove or quarantine any unmanaged stray `BakersfieldQuake\zz_bakersfielddowntown.pk3` (and verify no stale loose files sit in `_backup_before_server_sync\maps\` inside the active gamedir).
3. **Verify automatic `ultralow` tiering via `Play.cmd`**:
   - Launch **`Play.cmd`** with normal background apps open. Confirm:
     - When free RAM `< 1.5 GB`, the pre-flight dialog appears naming live free RAM + top 3 RAM apps with **Continue Ultra-Low** / **Launch Lite Downtown** / **Cancel**.
     - `%LOCALAPPDATA%\BAKOQUAKE\last-launch.txt` records `Tier: ultralow`, Intel Iris Xe `[iGPU]`, Parsec `[VIRTUAL]` excluded, and `+exec ultralow.cfg`.
     - Loading `bakersfielddowntown` keeps the window responsive (no Windows Ghost Window / "Not Responding").
4. **Run the automated 3× cold-start regression suite on the Zenbook**:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\BakersfieldQuake\source\ci\test_lowmem_maps.ps1 `
     -Maps bakersfielddowntown,bakersfielddowntown_lite -Tier ultralow -CommitCapMB 0 -Repeat 3 `
     -OutMarkdown .\zenbook_ultralow_report.md
   ```
   Confirm `0` failures, `Longest Hang <= 4.5 s`, and playable steady-state FPS.
5. **Fallback check if Intel Iris Xe driver `32.0.101.5768` dislikes S3TC (`gl_texturecompression 1`)**:
   - If `ultralow` stalls during texture upload or shows visual artifacts on Iris Xe, immediately test non-S3TC Safe Mode:
     ```powershell
     powershell -NoProfile -ExecutionPolicy Bypass -File .\BakersfieldQuake\source\ci\test_lowmem_maps.ps1 `
       -Maps bakersfielddowntown,bakersfielddowntown_lite -Tier safemode -CommitCapMB 0 -Repeat 2 `
       -OutMarkdown .\zenbook_safemode_report.md
     ```
     Or launch `Play.cmd` with `set BQ_TIER=safemode`. If `safemode` runs cleanly while `ultralow` stalls on Iris Xe, switch `ultralow.cfg` to `gl_texturecompression 0` + `gl_max_size 256` (or gate S3TC off for `VEN_8086` in `bq-preflight.ps1`).
6. **Verify crash-reporter & clean-exit config restoration**:
   - After exiting cleanly from a temporary `safemode` run, confirm `config.pre-temp.cfg` was restored and `session-active.flag` was cleared; run `Report a Problem.cmd` one more time to archive the post-fix Zenbook report zip for comparison.
