# Engine candidate `zircon_beta_perf3`: five changes, measured (2026-11-19)

Follow-up to `docs/audit-2026-11-18-performance.md` (section 10), `docs/engine-fs-dircache-results.md` and
`docs/engine-memory-leaks-2026-11-18.md`.
Nothing here is installed, released or pushed. It is a candidate for the owner to try and for the engine fork to merge.

## What it is

`G:\Quake\_zircon_rc\out\zircon_beta_perf3.exe`, sha256 `9be0edb3fe885da2c3f0c3e3a7039515044eb2fc25a9a10826c33c2d0c682948`,
8,921,537 bytes. (`zircon_beta_perf2.exe` beside it, sha256 `ec455548...`, is the same without the leak fixes; the
frame-rate tables below were measured on it.)

- Source: branch `fs-dircache` of the second session's clone (`G:\Quake\zircon-fscache\src`, commit `ca04460`, Zircon
  `e19de67` plus the file-lookup cache), cloned to `G:\Quake\_zircon_rc\src`, plus the four patches below it in
  the table.
- Built like the shipped engine: MSYS2 MINGW64 gcc 15.2, SDL2 2.28.3 linked statically
  (`source/mm_tools/perf/fs_dircache/build.sh`), the shipped exe's built-in data pack appended.
- It imports the same 14 system DLLs as the shipped `zircon_beta_gcc.exe`.
- `G:\Quake\_zircon_rc\out\zircon_beta_perf3.map` is the function list of the same link, for `sampler.py`.

| patch (applies to Zircon `e19de67` with `git apply`) | file | what it does |
|---|---|---|
| `source/darkplaces-fs-dircache.patch` | fs.c | skips disk lookups under folders that do not exist (second session; map load 8.9 to 7.5 s) |
| `source/zircon-memory-leaks.patch` | gl_textures.c, prvm_edict.c | frees two things that leaked on every map change (third session; about 70 MB per change) |
| `source/darkplaces-lightpoint-cache.patch` | model_brush.c | remembers which lightmap texel a point resolved to, so models that do not move skip the BSP walk |
| `source/darkplaces-xinput-poll.patch` | vid_shared.c | asks Windows about empty controller slots once a second instead of every frame |
| `source/darkplaces-amd-hybrid-gpu.patch` | gl_rmain.c | exports `AmdPowerXpressRequestHighPerformance`, the AMD twin of the NVIDIA line already there |

## Why: where the client's frame goes

Function-level profile of the main thread (`sampler.py` with a symbol map, an unstripped rebuild of the engine),
bakersfielddowntown, frame rate uncapped:

- **35% in `Mod_BSP_LightPoint_RecursiveBSPNode`.** Every frame the engine looks up the floor lighting under every
  model. The lookup walks the map's BSP tree downwards and, at each node it crosses, scans every face stored on that
  node. These maps have nodes with thousands of coplanar faces (one big ground or roof plane). A test build that
  counts them: up to 9,564 faces scanned per lookup, 245 models per frame, 0.73 ms per frame. The most expensive
  models are props that never move: jetpack pickups and the Fox Theater furniture (stools, banquet sets, chandeliers).
- **11% in the per-frame controller check** (`VID_Shared_SetJoystick`): `XInputGetState` on each of the four slots.
  On an empty slot that call enumerates devices: 25 microseconds each with `xinput1_3.dll`, measured outside the game
  as well (0.10 ms per frame for four empty slots).
- The rest is drawing (`R_DrawModelSurfaces`, world visibility) and the graphics driver.

## The light point cache

`mod_bsp_lightpointcache` (default 1). A 4,096-entry table keyed on the exact point. An entry holds the face and the
lightmap texel the walk found; the light-style scaling is redone on every call with the same arithmetic as the walk,
so animated styles stay live and the result is the same number. A model that moves asks for a new point and walks
as before. Entries die when any map loads its light data.

`mod_bsp_lightpointcache 2` is a self test: it also does the walk and prints any difference.

| map, 15 bots | model lighting per frame, walk | with the cache | models per frame |
|---|---|---|---|
| bakersfielddowntown | 0.454 ms | 0.005 ms | about 200 |
| bklan6 | 0.537 ms | 0.386 ms | 590 to 750 |
| soi6 | 0.391 ms | 0.296 ms | 820 to 1,060 |

(Test build with a timer around each lookup. On soi6 and bklan6 most models are walking NPCs and players, which the
cache cannot help.)

Self test: 1,048,576 cached answers compared with a fresh walk on soi6 and again on bklan6, no difference. The
validation run below repeats it on four maps with the candidate itself.

## Frame rate: the same recorded match played back

`source/mm_tools/perf/timedemo.py`: a one-minute match with 15 bots is recorded once per map
(`loadtime.py --record`) and played back as fast as the PC can draw it. Playback has no server in it, so it measures
the client alone, and two runs agree within about 2%. Shipped settings, 1280x720 window, RTX 4070 Ti.

| demo | shipped engine | candidate | candidate, cache off |
|---|---|---|---|
| bakersfielddowntown | 378 fps | **752 fps** | 475 fps |
| soi6 | 702 fps | **806 fps** | 801 fps |
| morrorock (trace culling off) | 118 fps | **126 fps** | 122 fps |
| terminal21 (trace culling off) | 184 fps | **198 fps** | 198 fps |

So the controller change is worth 7 to 25% of the client's frame time at these rates, and the light cache doubles
bakersfielddowntown on top of it. At 60 frames a second on a slow PC the same milliseconds are a smaller share.

## Not done here, for the engine fork

- **Surface ray traces are slow on these maps for the same reason** (thousands of faces on one node, each one tested).
  `Mod_Q1BSP_TraceLineAgainstSurfaces` took 71% of the main thread on terminal21. The mod now avoids the two client
  features that fire them every frame (audit section 10). A real fix is an index over each large node's faces, in
  the engine.
- **PNG decoding is 20% of a map load** (`lodepng_inflatev` 10%, `unfilterScanline` 5.5%, the rest of lodepng 5%),
  and unpacking the same files from the pk3 another 9% (`zlib1.dll`). lodepng can be told to use the zlib the engine
  already loads (`custom_zlib` in its decoder settings), which is two to three times faster at inflating. Estimated
  0.7 s of a 7.2 s soi6 load. Not written.
- Linux and macOS builds: none of this was compiled there. All five patches are plain C; the controller and AMD ones
  are inside `#ifdef _WIN32`.

## Validation of the candidate

`gval.sh` (session scratch; the steps are the ones named here), run on `zircon_beta_perf2.exe` and again on the final
`zircon_beta_perf3.exe`. Same result on both:

| check | result |
|---|---|
| the file-lookup session's regression suite, `regress.py` (cached miss then write, QC `fopen`, demo record and playback, three screenshots, `curl --pak` into `dlcache/`, a folder made by another program, first-run `config.cfg`) | 11 of 11 pass |
| `regress_dl.py` (join a server whose map is only in a pack: download, load from it, no second download) | 4 of 4 pass |
| light cache self test, 45 s with 15 bots on soi6, bakersfielddowntown, terminal21, spruce: every cached answer compared with a fresh walk | 0 differences (over a million compared on bakersfielddowntown) |
| four maps in one session (soi6, bakersfielddowntown, spruce, bklan6) | clean exit, no errors; engine pools afterwards 617 MB with the leak fixes, 757 MB without |
| ten-minute match, 15 bots, bakersfielddowntown | clean exit, no errors, server at 72 frames a second throughout, peak commit 3.8 GB |
| desktop fullscreen at 1920x1080, sound on | starts, draws, exits cleanly |

Not covered: a person playing on it (mouse, keys, alt-tab, a controller plugged in while the game runs), Linux, macOS.

## To ship it

1. Play on it: copy `zircon_beta_perf3.exe` over `engine\zircon_beta_gcc.exe` (the released engine stays beside it as
   `zircon_beta_gcc.stock.exe`).
2. Put its sha256 into `$StockEngineSha` in `lan\make_lan_package.ps1`, build a base package, release with
   `base_tag` set to it. Every player downloads the 8.9 MB engine once.
3. Send the five patches to the engine fork (`rgr4y/zircon-darkplaces`) so its CI builds Linux and macOS, then point
   `ZIRCON_REF` in `source/mac/build_app.sh` at the new commit. The macOS app gains the most from the file-lookup
   cache (13.0 to 7.9 s per load) because its user folder is separate.
