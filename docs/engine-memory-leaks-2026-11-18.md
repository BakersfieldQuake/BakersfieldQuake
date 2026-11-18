# Engine memory leaks on map change, found and fixed (2026-11-18)

Follow-up to `docs/audit-2026-11-18-performance.md` and `docs/engine-fs-dircache-results.md`.

## Result

The Zircon engine leaked memory on every map change. Two causes, both a few lines. **Fixed for players since release
`build-20261118-0ebe292` (2026-11-18 22:42 UTC)**, whose Windows engine is the `perf3` build: these two fixes, the
file-lookup cache and three frame-rate changes (`docs/engine-perf-patches-2026-11-18.md`).

| leak | when | per event | fix |
|---|---|---|---|
| `R_FreeTexture` never frees a texture's update buffer (`bufferpixels`). Every lightmap page has one. | every map change, on every client | about 29 MB on these maps | free it in `R_FreeTexture` |
| `PRVM_Prog_Reset` frees the server script VM only when `prog->loaded` is set, but `SV_Shutdown` and `CL_Disconnect` clear that flag first | every `map` command (console, the Host Game menu); not `changelevel`, which the map rotation and votes use | 20 to 30 MB | free the pool in `PRVM_Prog_Reset` whenever it exists |

With the default 15-minute matches the first leak costs a client about 120 MB an hour. It is slow, so it is not the
crash someone sees ten minutes after hosting, but on an 8 GB PC it eats the headroom the low-memory mode buys over a
long LAN session.

## How it was found

1. One session, 15 bots, six maps in a row (soi6, spruce, bakersfielddowntown, bklan6, soicowboy_bkk, goldenwest),
   release layout, released game code. No errors on the released engine or the `fs_dircache` build, but peak
   commit was 5.33 GB against 3.8 GB for the heaviest of those maps alone.
2. The same three maps four times over, no bots, memory sampled every 5 s. Committed memory while playing soi6:

   | pass | released engine | released engine, low-memory mode | with the two fixes |
   |---|---|---|---|
   | 1 | 3,210 MB | 2,157 MB | 3,205 MB |
   | 2 | 3,416 MB | 2,381 MB | 3,458 MB |
   | 3 | 3,597 MB | 2,562 MB | 3,334 MB |
   | 4 | 3,866 MB | 2,795 MB | 3,458 MB |

   The released engine gains about 70 MB per map change with no sign of levelling off, the same in low-memory mode,
   so it is not texture memory. The fixed build moves within about 250 MB with no trend.
3. `memlist` after the first and the seventh load (both soi6). On the released engine the pools grew from 724 MB to
   1,016 MB, all of it in two pools: "texture management" 9.6 MB to 181.6 MB and "Server Progs" 24.2 MB to 147.2 MB.
4. `memlist all` after the first and the fourth load, grouped by source line: `gl_textures.c:1497` (the
   `bufferpixels` allocation) 8.4 MB to 96.5 MB, and every allocation of the server VM (`prvm_edict.c:107`, `114`,
   `143`, `3339` to `3344`) at exactly four times its first size.
5. Source, `rgr4y/zircon-darkplaces` at `e19de67`:
   - `gl_textures.c`, `R_FreeTexture`: frees `inputtexels`, never `bufferpixels`. Lightmaps are created with
     `TEXF_ALLOWUPDATES` (`model_brush.c:2784`), which allocates it.
   - `cl_main.c:425` (`SVVM_prog->loaded = false` in `CL_Disconnect`) and `sv_main.c:1723` (same in `SV_Shutdown`),
     then `PRVM_Prog_Reset` (`prvm_edict.c:3159`): `if (prog->loaded) { ... Mem_FreePool(&prog->progs_mempool); }`
     followed by `memset(prog, 0, ...)`, which drops the only pointer to the pool.

## The fix

`source/zircon-memory-leaks.patch` (13 lines in `gl_textures.c` and `prvm_edict.c`), on top of the `fs_dircache`
commit `ca04460`. Local commit `3337a1a` on branch `leak-fixes` in `G:\Quake\_bq_fork_engine\src`; not pushed.

After it, same test: pools 727 MB after the first load and 731 MB after the seventh; "texture management"
9,609 KB both times; "Server Progs" 23,807 KB both times.

The server VM is freed at the same point as on the normal `changelevel` path (the next `PRVM_Prog_Init`), so nothing
can use it later than before.

## The test build

`G:\Quake\_bq_fork_engine\zircon_beta_leakfix.exe`, sha256 `46ddb110019f62fe...740415`: the engine session's
`fs_dircache` source plus this patch, built with its `build.sh` (MSYS2 MINGW64, static SDL2 2.28.3), the released
exe's self-pack appended. It is installed on this PC as `engine\zircon_beta_gcc.exe`; the released exe is beside it as
`zircon_beta_gcc.stock.exe`, and `lan\make_lan_package.ps1` packages that one, so the test build cannot ship by
accident.

Tested on it: the twelve-load cycle above, and a three-map session with 15 bots changing maps with `changelevel`
(soi6, spruce, bakersfielddowntown). No errors. The `fs_dircache` regression list was run by the engine session on
the build without these two fixes, not repeated on this one.

## Shipped

- The owner chose to ship the engine without waiting for a play-test, and chose `perf3` (sha256 `9be0edb3...2948`,
  built by the main audit session from the same source plus its three patches) over the build above.
- Checked on `perf3` before it went out, besides that session's own validation: the file-lookup regression list and
  the download test (all pass); `perf3` as dedicated server with a `perf3` client joining it; bakersfielddowntown in
  low-memory mode under a 2.8 GB limit (2.43 GB used); six maps in one session with 15 bots, changing with
  `changelevel` (no errors, engine pools 619 MB at the end against 934 MB on the old engine); and the twelve-load
  cycle from this document: soi6 at 3,174 / 3,418 / 3,307 / 3,449 MB, goldenwest at 2,966 / 3,055 / 3,059 / 3,053 MB.
- Release: base `base-v1.14` is base v1.13 with only the engine replaced (every other entry byte-identical). A draft
  run was diffed against the release then current: engine, `VERSION.txt` and `version.cfg` only. The published
  release also picked up `zz_gunnomip.pk3` (56 KB, three shader files), pushed to `main` between the draft and the
  real run; the release as shipped was then loaded with 15 bots on soi6: 6.6 s to load, no errors.
- `lan\make_lan_package.ps1` now expects the `perf3` hash, so packages built on this PC carry it. The 2026-08-29
  engine is still `engine\zircon_beta_gcc.stock.exe`: copy it over `zircon_beta_gcc.exe` and put its hash back in
  `$StockEngineSha` to go back.
- Engine fork: pull request https://github.com/rgr4y/zircon-darkplaces/pull/1 carries all five changes, so its CI can
  build Linux and macOS. Those platforms still ship the old engine until it is merged and `ZIRCON_REF` in
  `source/mac/build_app.sh` points at the result.

## Not done

- Nobody has played on it yet: mouse, keys, alt-tab and a controller plugged in mid-game are untested by a person.
- Linux and macOS builds of any of the five changes.
- The dedicated server's memory was not measured. The public server runs a separate Linux DarkPlaces build, not
  Zircon, and changes maps with `changelevel`.

## How to repeat

`source/mm_tools/perf/loadtime.py <tag> soi6 --hold 520 --basedir <scratch copy> --same-userdir --exe <engine>`
with `+defer 45 "map spruce" +defer 85 "map goldenwest" +defer 125 "map soi6"` and so on, and
`+defer 38 "echo MEMLIST_1; memlist"` / `+defer 288 "echo MEMLIST_7; memlist"` for the pool lists. Sample the
process's committed memory every few seconds while it runs.
