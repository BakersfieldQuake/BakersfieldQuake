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
| Hosted game with bots dies: "server runaway loop counter hit limit" | FrikBot's `wisible` visibility check loops for ever between two brush entities | found on spruce, fixed in the game code |
| Game stops mid-load with "Mem_Alloc: out of memory" on small PCs | 3.1 to 4.4 GB of committed memory per map | reproduced with a memory cap. Normal settings now need 0.6 to 0.8 GB less; launchers switch to a 2.2 to 2.5 GB mode under 10 GB of RAM |
| Map loads of 7 to 11 s (13 to 20 s on the macOS app layout), 7 s of it the same on every map | the engine probes the disk about 40 times per texture per loose folder | engine patch written, built and measured: 6 to 8.6 s. Not installed |
| Server script time on soi6 with 15 bots | Combat+ gib physics ran on every gib every frame | switched off: 57% less script work |
| Every map loaded the tank, LAN props, Eric cannon, random NPCs, sky pads and all eight vehicle kinds | unconditional precache | they now load only where a map places them: 230 to 370 MB less video memory per map |
| Server packs differed from the release | VPS had this PC's builds of two packs | VPS now matches the release on all 103 game files |

What is on this PC but not yet with players: the new `progs.dat`, the configs, the launchers and `lowmem.cfg`.
They reach players and the server with the next release. Nothing was pushed or released.

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
- Not covered: a download into `dlcache/` used on the next map, demo record and playback, a long match, and
  fullscreen, sound and input in a human's hands. A second session ("Engine: skip loose-folder file probes") was
  started from this audit and is working on those.
- **Not installed.** It is a different compiler and build setup from the shipped `zircon_beta_gcc.exe`, and it would
  replace the engine for every player. Linux and macOS binaries come from the engine fork's CI, so merging the patch
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
  NPC out of range costs about ten statements). The change above removes the resend, not the calls. Putting NPCs
  with nobody near to sleep would cut the calls only while few players are on: with 16 spread along the street nearly
  every NPC has someone in range. The server held its full rate in every run, so this was left as it is.
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

- GitHub `main` = local `HEAD` = `0141a39` at the time of the check. The committed source compiled to the shipped
  game code byte for byte (`progs.dat`, `menu.dat`; `csprogs.dat` differs only in the two patched header CRC bytes).
- Since then a collaborator pushed `c34bfc0` ("Show the release tag in game") and published release
  `build-20261118-c34bfc0` from it. This audit's commits were rebased onto the collaborator's newest commit in a separate worktree, where
  they compile to exactly the `progs.dat` that was tested, and pushed. The shared checkout still holds the
  pre-rebase copies plus another session's uncommitted `.github/workflows/build-zip.yml`; `git pull --rebase` there
  drops the duplicates once that file is committed.
- The VPS matches release `build-20261118-0141a39`. The newer `build-20261118-c34bfc0` differs from it only in
  `quake.rc` and the new `version.cfg`, which draw the release tag on screen for players.
- **VPS against the latest release `build-20261118-0141a39`: 103 of 103 game files identical** after today's sync.
  Before it, 99: `zz_karts.pk3` and `zz_bakovan.pk3` were this PC's builds (same contents, different bytes) and two
  configs had Windows line endings. The release's own files were fetched, checked against the release manifest and
  swapped in while the server was empty (backup `/opt/quake/backup/20261118-120856-release-sync`).
- The same four files were replaced on this PC (old ones in `G:\Quake\Combat\_backups\pre_release_sync_2026-11-18`),
  so `vps/deploy.py`, which compares sizes, does not push the local builds back.
- The VPS web server (port 8097) serves every pack the server offers to clients.
- Ahead of the release on this PC, by design: `progs.dat`, `quake.rc`, `default.cfg`, `server.cfg`, the launchers,
  `lowmem.cfg`, `lowmem_off.cfg`. The VPS runs its own `server_vps.cfg`, which already has `gyroset 0`.

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
| `source/mm_tools/perf/` | `loadtime.py`, `breakdown.py`, `sampler.py`, `dedtime.py` |
| `docs/prompts/engine-fs-probe-cache-handoff.md` | the engine change |

Every VPS restart was done with nobody connected and came up clean; each replaced file has a backup beside it or
under `/opt/quake/backup`.

## 8. To ship

1. Rebase the five local commits onto `origin/main`, review and push them, then run the release workflow. That carries the new `progs.dat` inputs, configs,
   launchers and `lowmem.cfg` to players through the updater.
2. Deploy the server from that release, not from the dev tree.
3. Decide on the engine: try `G:\Quake\_zircon_build\out\zircon_fsdircache.exe` in place of
   `engine\zircon_beta_gcc.exe` on this PC first; if a session of real play is fine, ship it and merge the patch into
   the engine fork for the Linux and macOS builds.

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

## How to re-measure

```
python -I source/mm_tools/perf/loadtime.py <tag> <map> [--quiet] [--bots 15 --hold 75] [--memcap 3000] [--exe <engine>]
```

By default it uses an isolated user folder and port 26098, so it never writes the real `config.cfg`. That isolation
adds three loose folders to the engine's search path and about 4 s to every load. For release-layout numbers build a
scratch copy of the package (hard-link the pk3s, copy the configs) and pass `--basedir <copy> --same-userdir`; reset
the copy's `config.cfg` before each run, because the engine saves command-line cvars into it. Check that no other
`zircon*` process is running.
