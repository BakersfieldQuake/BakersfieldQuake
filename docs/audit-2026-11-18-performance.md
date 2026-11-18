# BAKOQUAKE audit: crashes, load time, bloat and sync (2026-11-18)

Scope: the mod as installed in `G:\Quake\Combat`, the public server (VPS 72.62.241.93) and the GitHub repo, with the
focus on the big custom maps. Everything here was measured unless a line says otherwise.
The 2026-11-17 and 2026-11-18 code audits (`G:\Quake\Combat\audit_reports\`) covered gameplay bugs; this one covers
stability, load time, memory and sync, re-checks which of their findings are still open, and fixes what it found.

Test machine: Ryzen 7 7700X, RTX 4070 Ti, NVMe, Windows 11, files in the disk cache. It is a fast PC: every time
below is a best case.

## Summary

| problem | cause | state |
|---|---|---|
| Public server dropped everyone about every 12 minutes | health check and demo recorder shared one address; the server answers one status query per address per second | fixed on the VPS |
| Hosted game with bots dies: "server runaway loop counter hit limit" | FrikBot's `wisible` visibility check loops for ever between two brush entities | found on spruce, fixed, released, live on the VPS |
| Game stops mid-load with "Mem_Alloc: out of memory" on small PCs | 3.1 to 4.4 GB of committed memory per map | reproduced with a memory cap. Normal settings now need 0.6 to 0.8 GB less; launchers switch to a 2.2 to 2.5 GB mode under 10 GB of RAM |
| Map loads of 7 to 11 s (13 to 20 s on the macOS app layout), 7 s of it the same on every map | the engine probes the disk about 40 times per texture per loose folder | engine patch written, built and measured: 6 to 8.6 s. Released for Windows in `build-20261118-0ebe292`; Linux and macOS wait for the engine pull request (section 8) |
| Server script time on soi6 with 15 bots | Combat+ gib physics ran on every gib every frame | switched off: 57% less script work |
| Every map loaded the tank, LAN props, Eric cannon, random NPCs, sky pads and all eight vehicle kinds | unconditional precache | they now load only where a map places them: 230 to 370 MB less video memory per map |
| Server, release and source out of step | VPS had this PC's builds of two packs; the two newest releases carried older `progs.dat` and `csprogs.dat` and lacked four packs | one release built from the current source; VPS identical to it |
| terminal21 at 46 fps with dips to 10 on a fast PC (same recorded match every time) | the engine's visibility rays test wall faces one by one, thousands per BSP node on these maps | the client code now picks the classic cheap test on the eight maps where it is exact: 311 fps, dips to 121. Released in `build-20261118-52bbdb8` (section 10) |
| A third of each frame on bakersfielddowntown spent on model lighting, a tenth on empty controller slots | engine: a BSP walk per model per frame; `XInputGetState` per slot per frame | engine with five changes built and validated: 378 to 752 fps on that demo. Released for Windows in `build-20261118-0ebe292` |
| Memory grows by about 70 MB on every map change | engine: lightmap update buffers and the server script VM are never freed (`docs/engine-memory-leaks-2026-11-18.md`) | fixed in the same engine: flat over twelve map loads. Released for Windows in `build-20261118-0ebe292` |
| Weak graphics start with full settings | launchers looked at RAM only | launchers now also read video memory: low-memory textures, and Simple Mode once, under 3 GB. Released in `build-20261118-52bbdb8` |

**Shipped.** With the owner's go-ahead the work was pushed, released as `build-20261118-74b8bd0` ("Latest") and
deployed to the VPS, which matches that release on all 106 game files. An existing player's updater downloads 17
files, 17.9 MB. Three more releases followed (section 8). The third, `build-20261118-0ebe292`, carries the patched
Windows engine; the fourth, `build-20261118-041eb0b`, is "Latest" and adds a game log per session and a "Report a
Problem" tool. The VPS matches it on all 109 game files.

While preparing the release it turned out that the two releases before it (`build-20261118-c34bfc0` and
`build-20261118-7f30a1e`) had been built on a stale draft base and had quietly put older game code back
(section 6). The new release corrects that.

## 1. Crashes

### Public server restart loop (fixed)

- `quake-healthcheck.timer` sends one `getstatus` a minute from 127.0.0.1 and restarts the server after three misses.
- `demo_recorder.py` went live on 2026-11-18 02:01 UTC and polls `getstatus` from 127.0.0.1 every 2 s.
- DarkPlaces answers one `getstatus` per source address per second and drops the rest. A probe from the VPS showed
  exactly that: one answer, then 0.9 s of silence, repeating.
- The health check's query was dropped about 45% of the time, and three drops in a row restarted a healthy server:
  **41 restarts between 02:14 and 10:24 UTC**, the first 13 minutes after the recorder started.
- Fix (live since 10:46 UTC): the check sends from 127.0.0.2, which has its own flood slot, and tries three times
  before counting a miss. Source: `G:\Quake\Combat\vps\quake-healthcheck.py`; the old script is
  `/usr/local/bin/quake-healthcheck.py.bak-20261118` on the VPS. No health-check restart in the 1 h 49 min to the
  last check at 12:35 UTC (that span used to see about nine). Worth a look at `journalctl -t quake-healthcheck`
  after a day.

### Server crash with bots: runaway loop (found and fixed)

A 15-bot match on spruce ended 18 s in with `Host_Error: server runaway loop counter hit limit of 10000000 jumps`,
which drops every player. The engine's crash report names the place: `wisible` (frikbot.bot_misc.qc), called from
`DynamicWaypoint`, from `BotPreFrame`; the profile shows one call making ten million tracelines.

- `wisible` traces from A to B, and when it hits a brush entity it restarts the trace from the middle of that entity,
  ignoring only that one. Two brush entities in line send it back and forth for ever.
- The loop is in the released game code. It needs a bot standing in the wrong place, so it is intermittent: one crash
  in five 15-bot runs on spruce here. Over a 60-minute match on the public server, which runs spruce around the clock,
  the odds are far higher. This is the best candidate for "the game crashes when someone hosts".
- Fix: at most eight hops, then "not visible". After it: thirteen maps, two minutes each with 15 bots (results in
  the list at the end of this section).

### Out of memory on small PCs (reproduced, then fixed)

`loadtime.py --memcap` runs the engine inside a Windows job object with a commit limit, which is what a PC with little
free memory looks like to the game.

| limit | old defaults | today's defaults | low-memory mode |
|---|---|---|---|
| bakersfielddowntown, 4.2 GB | loads (uses 4.17 GB) | loads | loads |
| bakersfielddowntown, 3.8 GB | not run | loads (uses 3.79 GB) | loads |
| bakersfielddowntown, 3.0 GB | **Engine Error: Mem_Alloc: out of memory** after 13 s | **same error** | loads |
| bakersfielddowntown / soi6 / bklan6, 2.8 GB | not run | bklan6: **same error** | all three load (2.2 to 2.5 GB) |

The error box is "Engine Error: Mem_Alloc: out of memory (alloc of size ... at image_png.c:81)": the game dies while
decoding textures. Ask whoever sees crashes whether that is the message.

Fixes:
- `lowmem.cfg` (new): model textures at half size (`gl_picmip_other 1`) and a smaller shadow atlas. Walls, sprites, HUD
  and menu are untouched. bakersfielddowntown: 945 MB of textures and 2.4 GB committed instead of 2,155 MB and 3.8 GB.
- All five launchers (Play / Start Server for Windows and Linux, and the macOS app launcher) add `+exec lowmem.cfg`
  when the PC has under 10 GB of RAM. `BQ_LOWMEM=1` forces it on, `BQ_LOWMEM=0` off. Windows reads the RAM size once
  and keeps it in `%LOCALAPPDATA%\BAKOQUAKE\ram-gb.txt`. The logic was tested for 8, 9, 10, 16 and 32 GB, both
  overrides and a corrupt cache file.
- The normal settings also need less now (sections 3 and 4).

### Finding out what a crash was, on a PC nobody else can look at (added 2026-11-19)

The game left nothing behind when it died: no log unless it was started with `-condebug`. The crash on the owner's
other PC (16 GB, integrated graphics) could therefore not be confirmed from here, only reproduced by capping memory.

- All five launchers now start the engine with `+log_file bq_game.log` (the dedicated server window of Start Server
  with `bq_server.log`). The engine appends to its log, so the launcher first moves the previous one to
  `bq_game_prev.log`: one file for this session, one for the session before. The engine writes each line straight
  through, so the last line before a crash is on disk. A two-minute start writes about 50 KB.
- `Report a Problem.cmd` (new, next to Play) runs `tools\bq-report.ps1`, which writes `BAKOQUAKE-report.txt` to the
  Desktop and opens it: package version and file hashes, Windows, CPU, RAM and commit limit, every graphics adapter
  with its video memory and driver date, what the launcher decided (the RAM and video-memory cache files, the
  overrides), a few saved graphics settings, the error lines and the last 60 lines of both game logs, and the
  crashes Windows recorded for the engine in the last 30 days (faulting module and exception code). Nothing is
  sent anywhere.
- Tested in a scratch copy laid out like the package: Play.cmd twice (log written, previous one kept), then the
  capped-memory crash. The report shows one error line, `Engine Error: Mem_Alloc: out of memory (alloc of size ...
  at image_png.c:81)`. On this PC it also lists the one engine crash Windows recorded (below).
- So the next crash on that PC answers the question: run Report a Problem there and read the "Game log" and
  "Crashes Windows recorded" parts. An error box is in the game log; a driver crash names the graphics driver's
  module in the Windows part.

### This PC

Windows logged one engine crash in the last 30 days (2026-11-17 21:32). The dump shows a call through a null pointer
from the screenshot code before the video backend existed: a screenshot command run at startup by a test.

### Stress runs

- Before the changes: 75-second matches with 15 bots on bakersfielddowntown, soi6 and bklan6. No errors.
- With the changes but before the `wisible` fix: 60-second matches on soi6, spruce, bakersfielddowntown and bklan6.
  spruce crashed with the runaway loop above; the others were clean.
- Release game code on spruce, twice for 90 s: no crash (the loop needs a bot in the wrong spot).
- Final game code: **two-minute matches with 15 bots on thirteen maps** (spruce, soi6, soicowboy_bkk,
  bakersfielddowntown, bklan6, goldenwest, terminal21, little_st_james, morrorock, fox, lolmap1, slo_bike_kitchen,
  ooika_lawrenceville), plus soi6 on the patched engine. Every run ended normally with no `Host_Error`, runaway
  loop, overflow, edict or precache error, and the server held its frame rate.
- The host's frame rate with 15 bots on soi6 went from 114 fps to between 123 and 212 fps across runs (it depends
  on where the host spawns and on whether the window has focus).

## 2. Load time

"Load" is the time from the `map` command to "entered the game" when hosting, new-player settings, release layout
(user folder = game folder, as Play.cmd runs it). Engine start to the menu adds about 3 s.

| map | before | now, shipped engine | now, patched engine |
|---|---|---|---|
| start (stock Quake map) | 7.1 s | 6.4 s | 5.5 s |
| goldenwest | 7.5 s | 6.7 s | 6.4 s |
| terminal21 | 7.5 s | 7.0 s | 5.9 s |
| little_st_james | 7.6 s | 7.5 s | 6.4 s |
| spruce | 7.7 s | 7.5 s | 6.3 s |
| soicowboy_bkk | 8.3 s | 7.9 s | 6.8 s |
| soi6 | 8.6 s | 8.3 s | 6.6 s |
| bakersfielddowntown | 10.9 s | 10.8 s | 8.6 s |
| bklan6 | 11.0 s | 11.0 s | 8.3 s |

With a separate user folder (the macOS app, and every test run that follows the recipe in `CLAUDE.md`) soi6 takes
13.0 s on the shipped engine and 7.9 s on the patched one. The Windows dedicated server is ready in 3.6 s: it loads
no textures.

### Where the time goes

- **About 7 s was the mod itself, on every map.** Every map loads 600 to 900 models and about 1,900 textures, of
  which about 1,200 are animation frames for nine hand-held gun models (`v_milky` 248 frames, `v_pickle` 120,
  `v_dookie` 114, `v_greenjar` 112, four `v_robhead*` at 112 each, `pickle` 64).
- **It is the number of files, not their size.** Controlled tests on soi6 (separate user folder, baseline 12.7 s):
  the 1,230 frames as 8x8 images 11.1 s; at half resolution 11.4 s; every second frame reused 11.8 s; all model
  textures at half size 12.9 s; three fewer loose folders to search 8.6 s.
- **Profile of the load** (main thread sampled every 3 ms): with a separate user folder 45% of the load is inside
  `GetFileAttributesW`; with the release layout 20%. Decompression is 5 to 10%, the graphics driver under 5%.
  For every texture the engine looks for about 40 optional files (`_norm`, `_glow`, `_gloss`, `_pants`... as
  `.tga/.png/.jpg/.pcx`) in every loose game folder. An antivirus filter or a slow disk multiplies that cost, which
  fits "unusually long on another computer".
- Not the cause: unused files (at most 28 MB of the 500 MB pack looks unreferenced), duplicate files (3.4 MB),
  texture upload, the loading log.

### The engine patch

`fs_dircache`: per loose folder, remember which first-level subfolders exist, and skip the disk lookup for names
under a subfolder that is not there. Design and evidence: `docs/prompts/engine-fs-probe-cache-handoff.md`.

- Built from rgr4y/zircon-darkplaces at `e19de67` with MSYS2 MINGW64 (gcc 15.2, `make DP_LINK_SDL=static
  sdl-release`), no build fixes needed. Output in `G:\Quake\_zircon_build\out`: `zircon_fsdircache.exe`,
  `zircon_stock_rebuild.exe` (same tree and compiler, no patch) and the patch. Both import the same system DLLs as
  the shipped binary.
- soi6: shipped engine 8.7 s, same-compiler rebuild 8.9 s, patched 7.3 s, patched with `fs_dircache 0` 8.3 s.
  Separate user folder: 13.0 s, 12.9 s, 7.9 s.
- Regression run, identical on patched and shipped: a file in a folder that does not exist is not found; the engine
  then writes it; it is found on the very next lookup. Screenshot written. All nine maps above load with it.
- A second session built the same change independently (`docs/engine-fs-dircache-results.md`,
  `source/darkplaces-fs-dircache.patch`) and ran the rest of the regression list on it: a download into `dlcache/`
  used on the next launch, demo record and playback, screenshots, a new player's first `config.cfg`, a folder created
  by another program. All pass, with a negative control that fails.
- Checked later on the installed build:
  - Four maps in one session (soi6, bakersfielddowntown, spruce, bklan6): all load, no error lines, clean exit.
  - A ten-minute match with 15 bots on bakersfielddowntown: clean exit, no error lines, the server held 72 frames a
    second, peak commit 3.8 GB (the same as the shipped engine).
  - Desktop fullscreen at 1920x1080 with sound: starts, renders, exits cleanly.
  - Its start-up log differs from the shipped engine's only in the build stamp, the missing ODE probe and the SDL
    version (2.32.10 against 2.28.5). Both use the SDL video and sound backends.
- Still not covered: a human playing a real match on it (mouse, keys, alt-tab, a controller), and Linux and macOS
  builds.
- **Installed on this PC only** (soi6 with the test recipe's separate user folder: 7.9 s, was 12.6 s). It is a
  different compiler and build setup from the shipped `zircon_beta_gcc.exe`, so it is not in the release. Linux and macOS binaries come from the engine fork's CI, so merging the patch
  there covers them.

### Other options, measured

- Packing the gun frames into atlases: the upper bound, with every frame costing nothing at all, is 8.7 to 6.4 s on
  the shipped engine and 7.3 to 5.6 s on the patched one. A real atlas keeps the pixels, so about 1.4 s and under 1 s,
  for about 134 MB of extra download. A second session ("Gun animation frames as atlas overlay pk3") is building it;
  whether it is worth the download is the owner's call.

## 3. Memory

Peak per map, new-player settings, release layout:

| map | textures before | textures now | commit before | commit now | low-memory mode |
|---|---|---|---|---|---|
| start | 1,690 MB | 1,352 MB | 3.1 GB | 2.3 GB | |
| goldenwest | 1,765 MB | 1,429 MB | 3.5 GB | 2.7 GB | |
| terminal21 | 1,777 MB | 1,441 MB | 3.5 GB | 2.7 GB | |
| little_st_james | 1,790 MB | 1,518 MB | 3.3 GB | 2.6 GB | |
| spruce | 1,795 MB | 1,539 MB | 3.4 GB | 2.8 GB | |
| soicowboy_bkk | 2,153 MB | 1,897 MB | 3.8 GB | 3.0 GB | |
| soi6 | 2,156 MB | 1,819 MB | 4.1 GB | 3.4 GB | 871 MB / 2.2 GB |
| bklan6 | 2,194 MB | 1,917 MB | 4.2 GB | 3.5 GB | |
| bakersfielddowntown | 2,381 MB | 2,155 MB | 4.4 GB | 3.8 GB | 945 MB / 2.4 GB |

What changed:
- `r_shadow_shadowmapping_texturesize 4096` in `default.cfg`. The engine default is one 8192x8192 texture (256 MB)
  for rocket and muzzle-flash shadows. 192 MB less, same picture.
- The tank, LAN props, Eric cannon, random NPCs and sky pads no longer load on maps that do not place them (section 4).

Where the rest goes (soi6): the gun animation frames 625 MB, the Soi 6 NPC sheets about 400 MB (this map only),
world textures under 100 MB. Shipping the gun frames at half resolution would save another 470 MB for a 44 MB
download, but they are video frames at 384x510 and the loss shows at 1080p and above, so that was not done; the
low-memory mode does it for the PCs that need it.

## 4. Game code and server load

Server script work in 75 s with 15 bots (statements executed):

| map | total | gib physics | bot routing |
|---|---|---|---|
| soi6, before | 1,785 M | 1,089 M (61%) | 194 M |
| soi6, `gyroset 0` | 760 M | 0 | 206 M |
| bklan6, before | 818 M | 61 M | 358 M (44%) |
| bakersfielddowntown, before | 561 M | 51 M | 83 M |

Changed:
- **`gyroset 0`** in `quake.rc`, `server.cfg` and the VPS config. Combat+'s "Gyro" physics ran about eight script
  calls for every gib on every server frame for its 30 to 40 s life, and one rocket into a Soi 6 bar makes about 150
  gibs. Gibs still fly and bounce; they no longer float or tumble. The host's frame rate with 15 bots on soi6 went
  from 114 to 147 fps. `gyroset 2` brings it back.
- **Precache gating** (`bm_match.qc`, `weapons.qc`): `RandomNPCs_Precache`, `EricCannon_Precache`, `MMTank_Precache`,
  `SkyPad_Precache` and `LanProps_Precache` are no longer called for every map. Each feature already precaches itself
  in its own init function, so maps that place them (and the test impulses) still load them. Checked first that no
  other feature depends on those calls for its own models or sounds. All ten maps load with no precache warning.
- **Vehicles per kind** (`vehicles.qc`): `Vehicles_Precache` loaded all eight kinds, 57 models, as soon as a map had
  any vehicle. `Veh_InitEntity` now precaches the body, wreck and loose parts of the kind being spawned. Checked by
  spawning three kinds with the test impulse on a map that has no vehicles: bodies, wrecks and parts loaded on demand.
- **Gib budget for Soi 6 NPCs** (`soi6_npcs.qc`): the first four gib showers in any 10 s are full (14 gibs, a heart,
  5 splats); the rest of that window throw three gibs and a splat, as the street crowd does.
- **`wisible` bounded** (`frikbot.bot_misc.qc`): the crash fix from section 1.
- **NPC cards face the viewer's position, in 3 degree steps** (`soi6_npcs.qc`, `htb_npcs.qc`, `beach_uncle.qc`).
  They used to copy the viewer's view angle, which changed every NPC in range on every frame the player moved the
  mouse, so each one was re-sent each frame. Looking straight at an NPC the two angles are the same. Checked in game.

Open, from the review agent's reading of the code (not re-traced here):
- Soi 6: the per-viewer hook still runs for all 728 NPCs on every frame sent (69,000 calls a second per player; an
  NPC out of range costs about ten statements). The change above removes the resend, not the calls. **Measured, and
  it costs nothing that shows:** a Windows dedicated server on soi6 at 100 frames a second used 4.3%, 7.4% and 17.7%
  of one core with 0, 1 and 4 players connected; the same build with the hook taken out used 1.9%, 8.0% and 16.0%.
  The differences are inside the run-to-run noise. With 4 players the server's main thread was asleep in 98% of the
  samples. The public server's CPU is about 0.62 times as fast as this PC's, which still leaves it mostly idle. Left
  as it is.
- Ten minutes with 15 bots on bakersfielddowntown ran 3,750 million script statements on the server (6 million a
  second, a few percent of one core) and 20 million on the client. Script code is not what limits the frame rate.
- bakersfielddowntown has no bot waypoint file, so bots route by search (15% of script work there).
- `gyro.gyro_physics.qc:426-437` holds four loops that never end. Nothing calls them, and `gyroset 0` keeps it so.

Status of the 2026-11-18 code audit (re-read by a review agent): H01 to H06, H08, H09 and M01 to M17 are fixed
except M18 (`bm_up_13.cfg` binds SHIFT over an existing bind), and partly H07, M06, M10 and L12.

## 5. Bloat inventory

| item | size | note |
|---|---|---|
| `bakersfield.pk3` | 503 MB, 16,442 files | PNG 320 MB (4,832 files), models 69 MB, sprites 52 MB, sound 51 MB, 8,590 skin files |
| `q15.pk3` (Combat+) | 477 MB | includes 24 MB of Photoshop sky templates and work-in-progress sounds; cannot change under the no-repack rule |
| loose maps | 268 MB | 14 maps with their .lit files |
| release zip | 1.13 GB | |
| `G:\Quake\Combat\dist` | 17 GB | every release zip since v1.0 |
| `source/` in the repo folder | 5 GB, 1,728 untracked files | build inputs and vote pages; not in GitHub |
| VPS `/opt/quake/backup` | 4.3 GB, 38 folders | disk is 79% full |
| VPS `BakersfieldQuake/maps` | 730 MB, 84 files | 54 are maps no longer in the release |

Deleting any of the last four is the owner's call; nothing was deleted.

## 6. Sync: GitHub, this PC, the server

State after the first release (2026-11-18 14:00 UTC). After the fourth release (section 8) "Latest" is
`build-20261118-041eb0b`, built from `main` at `041eb0b`, and the VPS matches it on 109 of 109 game files:

| | game code | state |
|---|---|---|
| GitHub `main` | `74b8bd0` | all of this audit's commits, on top of the collaborator's two |
| Latest release | `build-20261118-74b8bd0` (build 27) | `progs.dat` is a byte-for-byte compile of `74b8bd0`; `csprogs.dat` and `menu.dat` as compiled from the source; all seven overlay packs |
| VPS | same | 106 of 106 game files identical to the release; restarted empty, clean log; a test client joined, six bots played a minute on spruce, no errors |
| This PC | same `progs.dat`, `csprogs.dat`, packs and maps | the shared checkout is still on the pre-rebase copies of the commits (it lacks `version.cfg` and the two lines in `quake.rc` that show the release tag) because another session has uncommitted work in `.github/workflows/build-zip.yml`; `git pull --rebase` after that is committed |

How it got there:
- At the start GitHub `main` = local `HEAD` = `0141a39`, and the committed source compiled to the shipped game code
  byte for byte (`progs.dat`, `menu.dat`; `csprogs.dat` differs only in the two patched header CRC bytes).
- The VPS matched release `build-20261118-0141a39` on 99 of 103 files: `zz_karts.pk3` and `zz_bakovan.pk3` were this
  PC's builds (same contents, different bytes) and two configs had Windows line endings. Fixed from the release's
  own files, checked against its manifest.
- **Release regression found.** `build-20261118-c34bfc0` and `build-20261118-7f30a1e` were run with
  `base_tag=build-20261118-584fa4a-draft`, a draft from that morning. The release workflow compiles nothing: it
  takes `progs.dat`, `csprogs.dat` and the packs from the base zip. So those two releases carried an older
  `progs.dat` (3,438,402 bytes against 3,441,354) and `csprogs.dat`, and dropped `zz_conback.pk3`, `zz_gfuel.pk3`,
  `zz_johnbird.pk3` and `zz_mmtank.pk3` from the manifest. Players who updated in that window ran older game code than
  the server, and new installs lacked the John Bird and tank packs.
- Fix: a new base built on this PC (`base-v1.12`, draft), checked file by file (129 of 142 files identical to the
  last good release, both big packs and the engine unchanged), a draft run of the workflow whose manifest was checked,
  a smoke test of exactly that combination, then the real run.
- **For future releases: leave `base_tag` empty (it then takes the latest release) or pass `base-v1.12`.** Any
  older draft as base puts old game code back. A check in the workflow that compares the base's `progs.dat` with the
  latest release's would catch it; not added, because the workflow file has another session's uncommitted edits.
- The four replaced files were also replaced on this PC (old ones in
  `G:\Quake\Combat\_backups\pre_release_sync_2026-11-18`), so `vps/deploy.py`, which compares sizes, does not push
  local builds back.
- The VPS web server (port 8097) serves every pack the server offers to clients.

## 7. Changes made

| where | change |
|---|---|
| VPS `/usr/local/bin/quake-healthcheck.py` | own source address, three tries |
| VPS `server_vps.cfg` | `set gyroset 0` |
| VPS game files | the four mismatched files replaced by the release builds |
| `quake.rc`, `server.cfg` | `gyroset 0` |
| `default.cfg` | `r_shadow_shadowmapping_texturesize 4096` |
| `lowmem.cfg`, `lowmem_off.cfg` | new |
| `launchers/*`, `source/mac/launcher.sh`, `lan\` copies, `lan\make_lan_package.ps1` | automatic low-memory mode; the two configs added to the package list |
| `source/qc_combat_decomp/bm_match.qc`, `weapons.qc`, `vehicles.qc`, `spruce_bus.qc` | precache gating, vehicles per kind |
| `source/qc_combat_decomp/frikbot.bot_misc.qc` | runaway-loop crash fix |
| `source/mm_tools/soi6_npcs.qc`, `source/qc_combat_decomp/htb_npcs.qc`, `beach_uncle.qc` | NPC facing, gib budget |
| `progs.dat` | rebuilt with the above (0 errors) |
| `lan\make_lan_package.ps1` | engine guard (ships only the released engine); `lowmem*.cfg` in the package list |
| `engine\zircon_beta_gcc.exe` on this PC | patched build; released one kept as `zircon_beta_gcc.stock.exe` |
| GitHub | eight commits on `main`, draft `base-v1.12`, release `build-20261118-74b8bd0` |
| VPS game files | updated to that release |
| `source/mm_tools/perf/` | `loadtime.py`, `breakdown.py`, `sampler.py`, `dedtime.py` |
| `docs/prompts/engine-fs-probe-cache-handoff.md` | the engine change |

Every VPS restart was done with nobody connected and came up clean; each replaced file has a backup beside it or
under `/opt/quake/backup`.

## 8. Shipped, and what is left

Done on 2026-11-18 with the owner's go-ahead:
- Source pushed to GitHub `main` (eight commits, rebased onto the collaborator's work in a separate worktree).
- Base package v1.12 built with `lan\make_lan_package.ps1 -SkipPk3` and uploaded as draft `base-v1.12`.
- Release `build-20261118-74b8bd0` published. From the previous "Latest" the updater fetches 17 files, 17.9 MB; from
  `build-20261118-0141a39` 12 files, 3.5 MB. Neither big pack changed.
- VPS updated from the release (backup `/opt/quake/backup/20261118-135658-release-74b8bd0`).
- Patched engine installed on this PC as `engine\zircon_beta_gcc.exe`; the released one is beside it as
  `zircon_beta_gcc.stock.exe`. `make_lan_package.ps1` now refuses to ship anything but the released engine and
  packages the stock copy instead, so a package built here stays correct.

Second release, 2026-11-19, with the owner's go-ahead ("settings and map fix"; the engine stays as released):
- GitHub `main` at `52bbdb8`. Base package v1.13 (`dist\BAKOQUAKE_v1.13.zip`, draft `base-v1.13`): against v1.12 only
  `csprogs.dat` differs.
- Release `build-20261118-52bbdb8` (build 29) is "Latest". From the previous release the updater fetches 9 files,
  0.52 MB: `csprogs.dat`, `lowgpu.cfg`, `lowgpu_off.cfg`, `lowmem.cfg`, `lowmem_off.cfg`, `version.cfg`, `Play.cmd`,
  `Start Server.cmd`, `VERSION.txt`. Game code, engine and both big packs are unchanged.
- Checked before publishing: the base zip file by file against the previous manifest, a draft build's manifest, and
  that exact file set in game (terminal21, soi6, bakersfielddowntown with the released engine; a start with
  `lowmem.cfg` and `lowgpu.cfg`: 1.4 GB commit, 494 MB of textures on spruce).
- VPS: the six changed game files taken from the published zip, checked against the manifest, installed while the
  server was empty (backup `/opt/quake/backup/20261118-221412-release-52bbdb8`), service restarted. All 108 game
  files match the release. A client with the released engine joined and entered the game on spruce.
- This PC: the same `csprogs.dat`, and the engine candidate `zircon_beta_perf3.exe` as the installed engine.

Third release, 2026-11-19, with the owner's go-ahead ("ship it now", the engine with all five changes):
- Base package v1.14 (`dist\BAKOQUAKE_v1.14.zip`, draft `base-v1.14`): v1.13 with `engine/zircon_beta_gcc.exe`
  replaced by `zircon_beta_perf3.exe` (sha256 `9be0edb3...c682948`, 8,921,537 bytes) and `VERSION.txt`. Nothing else.
- Release `build-20261118-0ebe292` (build 31) is "Latest". From the previous release the Windows updater fetches 4
  files, 9.0 MB: the engine, `zz_gunnomip.pk3` (new, built by CI from `0ebe292`), `version.cfg`, `VERSION.txt`.
  All three jobs finished; the macOS DMG is attached.
- Checked before publishing, on that engine: the file-lookup regression list (11 of 11) and the download list
  (4 of 4), a dedicated server with a joining client, a six-map session with 15 bots, twelve map loads with memory
  sampled (flat; the old engine gained about 70 MB a load), a draft build's manifest, and the published file set in
  game.
- VPS: the changed game files taken from the published zip while the server was empty (backup
  `/opt/quake/backup/20261118-224519-release-0ebe292`). All 109 game files match the release. The server itself is a
  Linux DarkPlaces build and is not affected by the Windows engine.
- `lan\make_lan_package.ps1`: `$StockEngineSha` is now that engine's sha256, so a base built on this PC ships it.
  `engine\zircon_beta_gcc.stock.exe` is the engine from before (sha256 `bc7e8fe7...`).
- Engine fork: all five changes are in one pull request, https://github.com/rgr4y/zircon-darkplaces/pull/1 (open,
  no review yet). The Linux and macOS builds take the engine from that fork (`ZIRCON_REF`), so they stay on the old
  engine until it is merged and the pin is moved.
- After the release, a scripted check on the installed engine (soi6, windowed): W and S moved the player, a mouse
  sweep turned the view, the game kept running while another window had focus and took keys again afterwards, and
  it quit with exit code 0. Somebody was using the PC during two of the three runs, so single inputs went missing
  on both the new and the old engine; it shows the input path works, it does not replace a person playing.

Fourth release, 2026-11-19, with the owner's go-ahead (the game log and "Report a Problem", section 1):
- A first draft of it was built on `base-v1.13` while the third release was being published by another session. Its
  manifest showed the old engine coming back, so it was cancelled and deleted, and the release was built on
  `base-v1.14`, the same base as the third. This is the `base_tag` trap of section 6 once more, caught by comparing
  the draft's manifest with the live one before publishing.
- Release `build-20261118-041eb0b` (build 34) is "Latest". From the third release the Windows updater fetches 5
  files, 37 KB: `Play.cmd`, `Start Server.cmd`, `Report a Problem.cmd` (new), `tools/bq-report.ps1` (new) and
  `version.cfg`. Linux gets `Play.sh` and `Start-Server.sh`. Engine, game code and every pack are unchanged.
- Checked before publishing: the draft's manifest against the live release, and that exact file set started through
  `Play.cmd` in a scratch copy of the package (soi6 and terminal21 with bots on the new engine: both logs written,
  the previous one kept, no error lines; the report tool reads them).
- VPS: only `version.cfg` differed (the third release's game files were already there). Replaced while the server was
  empty (backup `/opt/quake/backup/20261118-230845-release-041eb0b`), service restarted, all 109 game files match.
- This PC: 126 of 128 game and engine files are identical to the release. The two others are the player's own
  `config.cfg` and `version.cfg`, which reads "dev" in the source tree on purpose.

Left for the owner:
1. Play a real session on the release (fullscreen, sound, mouse, a controller if anyone uses one). Nobody has yet.
   To go back on one PC: copy `engine\zircon_beta_gcc.stock.exe` over `zircon_beta_gcc.exe`. To go back for
   everyone: release again from `base-v1.13`.
2. The crash on the other PC is not identified. Start the game there once so it updates to the fourth release. The
   next time it crashes, double-click "Report a Problem" in the game folder and send the `BAKOQUAKE-report.txt` it
   puts on the Desktop: it holds the error line from the game log, the PC's RAM and graphics adapters, and any crash
   Windows recorded. Until then the out-of-memory crash, which was reproduced and fixed, is only the most likely
   candidate.
3. Tell everyone who cuts releases about `base_tag` (section 6): leave it empty or use `base-v1.14`. An older base
   puts the old engine back.
4. Get the engine pull request merged, then move `ZIRCON_REF` so Linux and macOS get the same engine.
5. Housekeeping in section 5. The drafts `build-20261118-74b8bd0-draft`, `build-20261118-52bbdb8-draft` and
   `build-20261118-52bbdb8-enginetest-draft` (the verification runs) can be deleted; keep `base-v1.14`.
6. A new map: run `source/mm_tools/perf/fence_solid.py` on it and add it to `BM_TraceCullSetup` only if it reports 0.

## 9. Limits

- One fast PC. No run on a weak machine, on macOS or over the internet with real players. The out-of-memory crash
  was reproduced with an artificial limit, not on the PC that crashes.
- Load times were taken while two other sessions were building and testing on the same machine; repeats differ by
  up to 0.5 s.
- The low-memory launcher logic was tested in isolation, and `lowmem.cfg` in game; a full launch through Play.cmd on
  an 8 GB PC was not.
- The Soi 6 network saving is reasoned from the code; it was not measured on the wire.
- An unrelated service on the VPS (`tailscale-map`) is crash-looping on an invalid API token and writes its PIN and
  token to the system journal on every start. It is not part of the mod and was not touched.

## 10. Frame rate on the big maps (added 2026-11-19)

The owner's direction after the release: optimization first, leave the crash diagnosis. The PC that struggles has
16 GB of RAM and integrated graphics. This section is what came of that. The per-map setting and the weak-graphics
launchers are released (section 8); the engine candidate is installed on this PC only.

### How it was measured

- **Function names.** The shipped engine has none, so the profiler could only say "inside the exe". An unstripped
  rebuild gives `sampler.py` a symbol map (`BQ_SYMS`), and it now reports self time per engine function.
- **Recorded matches.** A live match with 15 bots is useless for comparing settings: what the bots do moves the
  frame rate more than most settings. Three settings looked good or bad in live runs and were all noise. So a
  one-minute 15-bot match is recorded once per map (`loadtime.py --record`) and played back flat out
  (`timedemo.py`). Playback has no server in it, two runs agree within 2%, and every number below is from it:
  shipped settings, 1280x720 window, RTX 4070 Ti.

### Finding 1: visibility rays (terminal21: 46 fps, dips to 10)

The engine decides whether a model or a dynamic light is hidden by firing rays at it (`r_cullentities_trace`,
`r_shadow_culllights_trace`). With `r_cullentities_trace_entityocclusion 1`, the engine default, each ray tests wall
faces one by one, and these maps keep thousands of coplanar faces on a single BSP node. On terminal21 71% of the main
thread was inside `Mod_Q1BSP_TraceLineAgainstSurfaces`.

| same demo, shipped engine | terminal21 | morrorock | soi6 | bakersfielddowntown |
|---|---|---|---|---|
| shipped settings | 46 fps (worst second 10) | 139 (74) | 712 (255) | 376 (255) |
| model rays off | 79 (26) | 117 (66) | 709 | 377 |
| light rays off | 68 (17) | 139 (73) | 704 | 377 |
| both off | 184 (84) | 118 (66) | 702 | 379 |
| **world-only rays (`entityocclusion 0`)** | **311 (121)** | **146 (75)** | 708 | 378 |

- Turning the rays off is not the answer: on morrorock they hide enough to be worth 16%.
- The world-only test is the classic one (a BSP line-of-sight check). It keeps the culling and costs almost nothing.
- **It cannot be used everywhere.** It is blocked by see-through faces that sit on solid world brushes: on
  bakersfielddowntown 1,979 faces (fire-escape gratings, window panes), on spruce 174, bklan6 57, fox 45, goldenwest
  18. A player seen only through one of those would vanish after a second. The other nine maps have none
  (`source/mm_tools/perf/fence_solid.py` checks a map; shader-made transparency was checked too, none on world
  geometry).
- **So the client code picks it per map** (`BM_TraceCullSetup` in `csqc/bm_hud.qc`, called from `CSQC_Init`): the
  world-only test on terminal21, morrorock, soi6, soicowboy_bkk, lolmap1, little_st_james, ooika_lawrenceville and
  slo_bike_kitchen; the engine default on every other map. `bm_tracecull_auto 0` switches the automatism off.
- Checked in game with the new client code: the setting reads 0 on terminal21, morrorock and soi6, and 1 on
  bakersfielddowntown, spruce and start. A live 15-bot match on terminal21 gave the host 146 fps; the one recorded
  before the change gave 45 (two different matches, so only an indication).
- The corona and decal settings, particle quality and dynamic-light shadows made no difference on this demo.
  Dynamic lights off, which is what the menu's Simple Mode does, gave 71 fps where the per-map setting gives 311.

### Finding 2: lighting lookup per model, and the controller check (engine)

On bakersfielddowntown 35% of the frame was `Mod_BSP_LightPoint`: every frame, for every model, a walk down the BSP
tree that scans up to 9,500 faces, mostly for furniture and pickups that never move. Another 11% was the engine
asking Windows about four empty controller slots, every frame. Both need an engine change. A candidate build with
both, the file-lookup cache from section 2 and a hint for AMD dual-graphics laptops is described in
`docs/engine-perf-patches-2026-11-18.md`:

| same demo | shipped engine | candidate engine |
|---|---|---|
| bakersfielddowntown | 378 fps | **752 fps** |
| soi6 | 702 fps | **806 fps** |
| morrorock, with the per-map setting | 146 fps | **162 fps** |
| terminal21, with the per-map setting | 311 fps | **370 fps** |

The cache was checked against the uncached walk on a million lookups per map: no difference. The final candidate,
`zircon_beta_perf3.exe`, also carries the two map-change leak fixes from `docs/engine-memory-leaks-2026-11-18.md`. It
passed the file-lookup regression suite, the download test, the cache self test on four maps, four maps in one
session, a ten-minute match with 15 bots and a fullscreen start. Nobody has played on it yet. With the owner's
go-ahead it is now `engine\zircon_beta_gcc.exe` on this PC (sha256 `9be0edb3...`); the released engine is beside it as
`zircon_beta_gcc.stock.exe`, the previous test build as `zircon_beta_gcc.leakfix_46ddb110.exe`. Packages built here
still carry the released engine.

### Finding 3: weak graphics

- A map loads 1.4 to 2.2 GB of textures. Play.cmd and Start Server.cmd now read the largest video memory of any
  graphics adapter (cached in `vram-mb.txt`). Under 3 GB they start with `lowmem.cfg` every time, as they already did
  under 10 GB of RAM, and the first time also with the new `lowgpu.cfg`: the menu's Simple Mode plus no anti-aliasing
  and 4x filtering. After that those are ordinary saved settings. `BQ_LOWGPU=1/0` and `BQ_LOWMEM=1/0` override.
  The owner's 16 GB integrated-graphics PC gets both. Tested with simulated adapters from 64 MB to 12 GB.
- Not measured on integrated graphics: this PC's game window always runs on the RTX card. On the CPU side Simple Mode
  is worth 46 to 73 fps on the terminal21 demo.
- The engine asks NVIDIA laptops for the fast card (`NvOptimusEnablement`) but not AMD ones; the candidate adds that.
- Linux and macOS launchers keep the RAM rule only.

### What the load still consists of (soi6 on the patched engine, 7.2 s)

PNG decoding 20% (the engine's built-in decoder, `lodepng`), unpacking from the pk3 9%, file reads 11%, remaining
lookups 3.5%, texture upload 5%. The decoder is the next engine target (see the candidate's notes). Nothing on the
content side shortens this without a large download: the pixels have to be decoded once per map.

### Checked and found not to matter

- Server script load: ten minutes with 15 bots is 6 million statements a second, a few percent of a core.
- The public server: 4% of one core, no bots, one map.
- `sv_gameplayfix_q1bsptracelinereportstexture` is already 0. Set to 1 it takes bakersfielddowntown from 109 to
  between 9 and 16 fps, which is the same face-by-face trace on the server side. Leave it at 0.
- Network: prediction (`cl_movement`) is on by default in this engine.
- The main menu does not load a background map any more; `menu_background*` in `autoexec.cfg` is read by nothing.

## How to re-measure

```
python -I source/mm_tools/perf/loadtime.py <tag> <map> [--quiet] [--bots 15 --hold 75] [--memcap 3000] [--exe <engine>]
```

By default it uses an isolated user folder and port 26098, so it never writes the real `config.cfg`. That isolation
adds three loose folders to the engine's search path and about 4 s to every load. For release-layout numbers build a
scratch copy of the package (hard-link the pk3s, copy the configs) and pass `--basedir <copy> --same-userdir`; reset
the copy's `config.cfg` before each run, because the engine saves command-line cvars into it. Check that no other
`zircon*` process is running.
