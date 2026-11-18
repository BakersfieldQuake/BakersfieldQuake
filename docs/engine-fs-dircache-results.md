# Engine change `fs_dircache`: build, load-time results, regression tests (2026-11-18)

Follow-up to `docs/prompts/engine-fs-probe-cache-handoff.md` and `docs/audit-2026-11-18-performance.md` section 2.
Nothing was pushed or released. Later the same day the owner asked for a test build on this PC: `engine\zircon_beta_gcc.exe`
is now this change plus two memory-leak fixes (`docs/engine-memory-leaks-2026-11-18.md`), and the released exe is kept
beside it as `zircon_beta_gcc.stock.exe`.

## Result

On `soi6` the Windows map load is **1.4 s shorter with the release layout (8.9 to 7.5 s) and 4.3 s shorter with a
separate user folder (11.5 to 7.2 s, the macOS app and test layout)**. The time inside `GetFileAttributesW` falls from
14% to 6% and from 40% to 12% of the load. Every item on the handoff's regression list passes, with results identical
to the unpatched engine.

## Where it is

| what | where |
|---|---|
| patch (fs.c only, applies with `git apply` to Zircon `e19de67`) | `source/darkplaces-fs-dircache.patch` |
| local branch, one commit `ca04460`, **not pushed** | `G:\Quake\zircon-fscache\src`, branch `fs-dircache` |
| Windows build, stock self-pack appended (drop-in candidate) | `G:\Quake\zircon-fscache\run\zircon_beta_final.exe` (sha256 `51b7f993…a407`) |
| unpatched control built with the same toolchain | `G:\Quake\zircon-fscache\run\zircon_beta_basebundled.exe` |
| test and benchmark scripts | `source/mm_tools/perf/fs_dircache/` (paths point at the scratch folder above) |
| raw logs | `G:\Quake\zircon-fscache\bench1`, `bench2`, `reg3_*`, `reg4_final`, `dl_final` |

## The change

`FS_DirMayContain` in fs.c remembers, per loose game directory (and per `.pk3dir`), whether the first folder of a
name exists. `FS_FindFile` skips the OS call when that folder is known to be missing. As in the handoff sketch,
with these differences:

- **Exact-case matching**, not `strncasecmp`. The sketch's claim that a case-insensitive match is safe on Linux is wrong:
  a cached miss for `Progs` would then hide an existing `progs/`.
- **64 entries per path, and the oldest entry is reused when the table is full.** In the sketch a full table stopped
  caching new names. A session here uses about 19 names per path, so this is headroom.
- **Names containing `..` are not cached.** On Windows `missing/../x` resolves to an existing `x`.
- **`fs_dircache_list`** prints each loose path's table (name, exists or missing, stale).
- Answers to the handoff's open points:
  - `.pk3dir`/`.dpkdir` paths keep their directory, with a trailing `/`, in `search->filename`, so they use the
    cache the same way.
  - `FS_SysFileOrDirectoryType` is already declared in `fs.h`, so no prototype was needed.
- **Invalidation** follows the sketch: every `FS_mkdir` call bumps the epoch, and so does `FS_Rescan`. `FS_CreatePath`
  calls `FS_mkdir` for every folder of every file the engine writes. That costs some caching after writes, but it also
  covers a folder that another process (the Start Server dedicated server shares the game folder) created just before
  this engine writes into it. The audit session's parallel build (`G:\Quake\_zircon_build`) bumps only when mkdir
  succeeds. Both are correct for the engine's own writes; that build loses the cross-process case.
- `exec` checks existence with `FS_Search`, a directory listing that does not go through `FS_FindFile`, so console
  `exec` never sees the cache. `which` does.

## Build

The machine has MSYS2 with MINGW64 gcc 15.2 and binutils, but no SDL2 package. I used the official
`SDL2-devel-2.28.3-mingw` archive (the same version as the shipped `bin64\SDL2.dll`), unpacked outside the repo, and
linked it statically like the shipped exe. Both builds import exactly the shipped exe's 14 system DLLs and need only
`bin64\` (`source/mm_tools/perf/fs_dircache/build.sh`). The stock exe's 1 MB self-pack was appended with the audit
session's `append_bundle.py`. `fs.c` compiles without warnings.

**Not built:** Linux and macOS. WSL Ubuntu here has no compiler, and I did not install one. The fork's CI builds both
on push, so pushing branch `fs-dircache` to the fork is the cheapest compile check. The non-Windows path uses `stat`
through the existing `FS_SysFileOrDirectoryType`. The new code has no platform branches.

## Load time (soi6, new-player settings, `map` command to "entered the game")

Median of 3 runs, configurations interleaved round by round after one warm-up each, `loadtime.py --quiet`. Release
layout = a scratch copy of the v1.11 package run as `--basedir <copy> --same-userdir`: the pk3/bsp/lit/pak files
hard-linked from the install, everything else copied, today's `default.cfg`, `quake.rc` and `server.cfg`. Separate
user folder = the install as basedir with a fresh `-userdir` under `%TEMP%`. One extra run per configuration was
sampled (main thread every 3 ms, `sampler.py`).

| layout | engine | load | runs | time in `GetFileAttributesW` |
|---|---|---|---|---|
| release (userdir = basedir) | shipped `zircon_beta_gcc.exe` | **8.9 s** | 8.9 / 8.9 / 8.9 | 14.4% |
| | patched | **7.5 s** | 7.4 / 7.6 / 7.5 | 5.6% |
| | patched, `fs_dircache 0` | 8.6 s | 8.6 / 8.6 / 8.5 | 16.7% |
| separate user folder | shipped | **11.5 s** | 11.4 / 11.7 / 11.5 | 40.3% |
| | patched | **7.2 s** | 7.3 / 7.2 / 7.2 | 11.6% |
| | patched, `fs_dircache 0` | 11.4 s | 11.4 / 11.6 / 11.4 | 39.8% |

The earlier batch (`bench1`) gave the same picture, and it adds an unpatched control from the same toolchain:

| layout | shipped | control rebuild | patched | patched, `fs_dircache 0` |
|---|---|---|---|---|
| release | 8.7 s (16.6%) | 8.6 s (16.5%) | 7.4 s (5.6%) | 8.5 s (17.6%) |
| separate user folder | 12.7 s (38.6%) | 12.2 s (39.9%) | 7.8 s (11.2%) | 12.2 s (39.7%) |

- The rebuild performs like the shipped exe, so the gain is the patch, not the compiler.
- The shipped exe's separate-folder time differs between the two batches (12.7 s, then 11.5 s). The install's cfgs
  were being edited by another session in between, which is why every comparison is made inside one interleaved batch.
- The audit session measured the same change independently: release 8.7 to 7.3-7.4 s, separate folder 13.0 to 7.9 s.
- What remains of `GetFileAttributesW`:
  - Lookups into folders that do exist: `quake15/progs/` (17 loose files from Combat+), `maps/` and `levelshots/`.
  - Names without a `/`.
  - With the separate user folder, the install folder `G:\Quake\Combat\BakersfieldQuake` is the dev tree. Its loose
    `progs/`, `textures/`, `sound/`, `gfx/` and `models/` are really probed. A player install has none of them.
- Packing `quake15/progs/` into a pk3 would remove most of the rest. It is Combat+'s folder; ask first.

## Regression tests

`regress.py` uses a fresh user folder each run, the scratch package as basedir, and a windowed game on port 26098. It
was run on the final exe, on the unpatched control, and on a **negative control**: the patch with the `FS_mkdir`
invalidation removed. The probes use `which` because it goes through `FS_FindFile`.

| test | patched | unpatched | negative control |
|---|---|---|---|
| T1 `which zzfc/x` misses, `saveconfig zzfc/x`, `which` finds it in the same frame | pass | pass | **fail** (still "isn't anywhere") |
| T2 QC: CSQC `fopen` writes `data/config_menu.cfg` at shutdown; the next CSQC init reads it back (`nospinup 17` restored) | pass | pass | pass |
| T3 demo: `which demos/zzreg.dem` misses, `record demos/zzreg`, found in the same frame; recorded on `start`, stopped, `playdemo` works | pass | pass | **fail** |
| T4 three screenshots give three files (numbering uses `FS_SysFileExists`, uncached) | pass | pass | not reached |
| T5 `curl --pak` from a local HTTP server into `dlcache/`, then the pack is found and used | pass | pass | not reached |
| T6 a folder made outside the engine | hidden at 2 s, found after the 5 s expiry | found at once | not reached |
| new player: `config.cfg` written on first quit and read back on the next launch (`name fcregtest`) | pass | pass | not reached |
| no `Host_Error`, every step reached | pass | pass | demo playback failed with a message dump and the game hung; killed after 180 s |

`regress_dl.py` tests the real download flow. The server is the unpatched build, `-dedicated`, on map `fctest`, which
exists only in a pk3 in its own folder, with `sv_curl_defaulturl` set to a local HTTP server. The client is the
patched build with a fresh user folder.

- First connect: one HTTP request, `dlcache/fcreg_dl.pk3` downloaded, the client reconnects and enters the game.
  `maps/fctest.bsp` comes from the downloaded pack. **Pass.**
- Second launch: no download; the map loads from the pack already in `dlcache/`. **Pass.**

A plain `map fctest` on a local server, as opposed to a client joining, cannot use a dlcache pack. The local server
unloads dlcache packs at spawn. That is unchanged engine behaviour and the same on both builds.

## Not tested

- Linux and macOS builds (see Build). The macOS app is where the gain is largest, so it needs a run there before
  shipping.
- A real match: no bots, no 15-player session, no human play with fullscreen, sound and input on the patched exe.
- Other maps than `soi6`. The saving is mostly per texture, so every map should gain roughly the same.
- Slow disks, network drives, antivirus filters. The saving should be larger there; not measured.
- The Windows dedicated server: the makefile's mingw server target does not link. It loads no textures, so little
  gain is expected.

## For the owner to decide

- Push branch `fs-dircache` (`G:\Quake\zircon-fscache\src`) to the fork, or apply the patch there, so CI builds Linux
  and macOS. Then point `ZIRCON_REF` in `source/mac/build_app.sh` at it.
- Whether `run\zircon_beta_final.exe` replaces `engine\zircon_beta_gcc.exe` in the package. That is an 8.9 MB file
  every player downloads once.

## How to re-run

All paths are in the scripts; the scratch folder is `G:\Quake\zircon-fscache`. Check that no `zircon*.exe` is running.

```
python -I source/mm_tools/perf/fs_dircache/make_pkg.py <empty folder>    # scratch release-layout package
python -I source/mm_tools/perf/fs_dircache/bench.py <outdir> 3 [config,...]
python -I source/mm_tools/perf/fs_dircache/regress.py <exe> <outdir>
python -I source/mm_tools/perf/fs_dircache/regress_dl.py <exe> <outdir>
```
