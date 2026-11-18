# Gun-frame atlas pack (`zz_gunframes.pk3`), 2026-11-18

Follow-up to `docs/audit-2026-11-18-performance.md` (section 2): map load time scales with the number of texture
files, and 882 of the textures every map loads are per-frame PNGs of six animated gun models. The audit counted
about 1,200 across nine models, but three of those are never loaded (see below).
This pack puts those frames into atlases, with one shader per original frame name, so the `.skin` files, the models
and the QuakeC stay as they are.

**Status: not shipping (owner's decision, 2026-11-18).** About half a second per map load on a Windows install is not
worth 92.1 MB of download now that the engine change gives 1.4 s for a 9 MB file. The builder stays in the repo. The
CI step is not in the workflow: it is kept as `docs/gunframes-atlas/build-zip-ci-step.patch` (`git apply` it to
`.github/workflows/build-zip.yml` to ship the pack later). The pack is not installed in the game folder and not on
the server.

## What it is

- Builder: `source/mm_tools/build_gunframe_atlas_pk3.py <bakersfield.pk3> [out.pk3]`. It reads everything from
  `bakersfield.pk3` and needs no other inputs.
- 882 frame textures become 47 atlases (`progs/gunatlas/<model>[_<surface>]_<n>.png`, at most 2048x2048), plus six
  rewritten shader files.
- `v_robhead`, `v_robhead_baseball` and `v_robhead_wizard` (336 frames) are left out on the owner's call. The
  QuakeC precaches only `v_robhead_drone`, so no map loads the other three, and packing them would have added
  35.6 MB of download for nothing. Their base shaders stay as they are.

| model | frames | frame size | atlases |
|---|---|---|---|
| v_milky | 248 | 384x510 | 17 |
| v_pickle | 120 | 416x455 | 8 |
| v_dookie | 114 | 420x360 | 6 |
| v_greenjar | 112 | 360x386 | 5 |
| v_robhead_drone (card) | 112 | 360x386 | 5 |
| v_robhead_drone (head) | 112 | 220x220 | 2 |
| pickle (world model) | 64 | 512x512 | 4 |

- **Reproducible:** two builds gave the same sha256,
  `09af8b486bfa50b891ac6ce5203df31b81b215545627537d6a9a0cc8bbeb469a` (92,100,332 bytes, Pillow 13.0.0 and numpy
  2.5.4, as pinned in CI). The game tests below ran with an earlier build that also held the three unused robhead
  sets (sha256 `7d00520c…3825`, 127.7 MB, three identical builds). Every entry of the current pack is
  byte-identical to that build, and those tests loaded only these 47 atlases, so the results carry over. Zip entries are sorted, dated 1980-01-01, with fixed attributes; the PNGs are stored and
  the shaders deflated at level 9. A CI build may differ in bytes from this local one if the runner's Pillow wheel
  bundles a different zlib. That is harmless: CI caches its own build, so players re-download only when the base
  pack or the builder changes.
- The builder checks every atlas cell against its source frame pixel for pixel, and checks that each PNG decodes back
  to the same pixels.

## How the look is kept

The frames already had shaders in `bakersfield.pk3` (`scripts/milkyvm.shader`, `picklevm`, `dookievm`, `greenjarvm`,
`rh_dronevm`, `pickle`): `cull none`, `clampmap`, `blendfunc blend`, `rgbGen lightingDiffuse` (lit like any model
skin), and `rgbGen identity` for the pickle world model. The overlay replaces those six files with copies that
differ only in the image line:

```
progs/mvm_a_00
{
	cull none
	nomipmaps
	{
		clampmap progs/gunatlas/v_milky_0
		tcMod transform 0.19793814 0 0 0.33073930 0.00103093 0.00129702
		blendfunc blend
		rgbGen lightingDiffuse
	}
}
```

Each step below was checked against the Zircon source in `G:\Quake\zircon-fscache\src`:

- **Replacing files, not adding shaders.** `FS_Search("scripts/*.shader")` lists each file name once and loads it
  from the highest-priority pack, while a second definition of a shader name is ignored (`Q3Shader_AddToHash`: the
  first one wins). So a `zz_` file with the same name is the only way to change these shaders. All other shaders in
  those files (the 8 `pthr_*` and two `pickle_*` shaders in `pickle.shader`) are copied unchanged.
- **`tcMod transform a b c d e f`** gives `s' = a*s + c*t + e` and `t' = b*s + d*t + f` (`gl_rmain.c`). The cards
  map 0..1 exactly, so each frame's shader scales and offsets onto its cell.
- **2048 cap, keep picmip.** Shader textures without `nopicmip` are capped by `gl_max_size` (default 2048, and the
  mod doesn't raise it), so a 4096 atlas would be halved. `nopicmip` would avoid the cap but take the guns out of
  `gl_picmip` / `gl_picmip_other` (the planned low-memory option). With 2048 atlases picmip behaves as before.
- **Gutters.** The view-model frames have opaque pixels on their edges, where the arms leave the frame, and are
  drawn with `clampmap`. A transparent gutter would fade those edges by half a texel. So each cell gets a 2 px
  gutter that repeats the frame's own edge pixels, which is exactly what clamp-to-edge filtering samples. Wherever
  a frame's edge is transparent, its gutter is too.
- **Mipmaps.** The five view-model sets are drawn with `nomipmaps`. `v_milky` and `v_pickle` already were; the
  dookie, greenjar and drone sets used mipmaps before, which would bleed between cells. View models are drawn at
  roughly 1:1, so mipmaps barely apply. The pickle world model is seen at a distance and keeps its mipmaps: its
  frames have at least 5 px of transparent margin, so they sit gutter-free on a 512 grid in 2048x2048 atlases, and
  every mip level stays aligned to its own cell.

### In-game comparison

Map `start`, isolated user folder, port 26098, 1280x720, new-player settings. Each gun was raised in the brightest
and the darkest of nine probed spots (scene brightness 70 and 29 out of 255), then game time was frozen for the
shot. Sheets (before | after | difference x4) are in `docs/gunframes-atlas/`:

| sheet | scene / gun brightness, before → after |
|---|---|
| `compare_milky.jpg` | bright 69.9 / 130.2 → 69.9 / 129.9; dark 29.5 / 111.1 → 29.5 / 111.4 |
| `compare_drone.jpg` | bright 71.0 / 69.5 → 71.0 / 69.3; dark 30.3 / 31.9 → 30.1 / 31.7 |
| `compare_greenjar.jpg` | bright 70.4 / 84.8 → 70.4 / 84.7; dark 27.8 / 41.6 → 28.2 / 41.8 |
| `compare_pickle.jpg` | bright 70.8 / 90.3 → 70.9 / 90.6; dark 29.0 / 50.8 → 28.5 / 50.6 |
| `compare_dookie.jpg` | bright 71.1 / 119.2 → 71.1 / 119.0; dark 28.4 / 100.4 → 28.4 / 100.4 |
| `compare_pickleworld.jpg` | still balloon, brightness of the pickle area: near 80.1 → 80.0, mid 83.8 → 83.9; the "side" pair is spoiled (see below) |

- Gun brightness matches within 0.3 levels in every pair, so the lighting is unchanged.
- The difference images show only thin outlines. The view-model sway is driven by game time, which moves the gun by
  a fraction of a pixel between runs, and the dookie flags flutter.
- No seam, fringe or fade appears at the card edges where hands and arms leave the frame.
- The FPS counter reads 20 in several "after" shots. That is `cl_maxidlefps` (20, unfocused window), not the
  atlas: the load-time runs below reached 160 to 227 fps with the pack.
- The pickle world model only exists for 0.42 s of game time before it explodes, so it was frozen by hand. A thrown
  pickle (`pk_test 0`, so it never trips) was switched to `progs/pickle.md3` with `prvm_edictset` (scale 5.7,
  frame 6, fixed angles, no think) and shot near, mid-distance and from the side. Near and mid match apart from the
  animated flames and sky. In the "after" side shot a green dynamic light tints the whole room, walls and floor
  included; a texture cannot do that, so that pair says nothing about the atlas.

## Load time and memory (soi6)

`source/mm_tools/perf/loadtime.py <tag> soi6 --quiet`, before and after alternating. "Release layout" is the scratch
copy `G:\Quake\_bq_perf_base` with `--same-userdir`, as Play.cmd runs it. "Isolated user folder" is the
`loadtime.py` default, with the pack placed in the run's own user folder.

| layout | before (s) | after (s) | saved per pair (s) |
|---|---|---|---|
| release layout | 8.2, 9.2, 8.9, 7.8, 7.8 (mean 8.4) | 7.7, 8.5, 8.8, 7.5, 7.2 (mean 7.9) | 0.5, 0.7, 0.1, 0.3, 0.6 (**mean 0.45**) |
| isolated user folder | 12.5, 12.1, 13.0 (mean 12.5) | 10.3, 10.8, 9.9 (mean 10.3) | 2.2, 1.3, 3.1 (**mean 2.2**) |

A sixth release-layout pair is left out: the audit session's engine started on the same scratch copy during the
"after" run, and that run's texture total (1,466 MB) matches no other run.

| | before | after |
|---|---|---|
| gun frame / atlas textures loaded per map | 882 | 47 |
| textures listed by `r_texturestats` | 3,614 | 2,778 |
| texture memory, release layout | 1,819 MB | 1,767 MB (−52 MB) |
| texture memory, isolated user folder | 1,748 to 1,754 MB | 1,696 MB |
| peak commit, release layout | 3,282 to 3,360 MB | 3,141 to 3,188 MB (about −150 MB) |

- 882, not the audit's ~1,200: `v_robhead`, `v_robhead_baseball` and `v_robhead_wizard` are never precached by the
  QuakeC (only `v_robhead_drone` is), so their frames were never loaded. That is why the pack leaves them out.
- The memory drop comes from the three view-model sets (dookie, greenjar, drone) that no longer build mipmaps.
- The gain is real on both layouts (every pair positive), but on the release layout it is below the audit's
  estimate of 1.3 to 1.5 s. That layout has fewer loose folders to probe, so each file costs less there, and the
  pixels still have to be decoded and uploaded. On the separate-userdir layout (the macOS app's) the gain is 2.2 s,
  more than the 1.6 s the audit measured with 8x8 frames, which still kept 1,230 files.
- Loads vary by ±0.6 s between runs on this PC. Treat the release-layout figure as "about half a second".
- All runs above used the released engine. Since then `G:\Quake\Combat\engine\zircon_beta_gcc.exe` on this PC is the
  fs_dircache test build, and the released one is `zircon_beta_gcc.stock.exe` beside it. To repeat these numbers, pass
  `--exe` with the stock copy to `loadtime.py`.

### With the fs_dircache engine

Four more alternating pairs, release layout, same method, with the fs_dircache build installed as
`zircon_beta_gcc.exe` (sha256 `038c070a…`):

| | before | after |
|---|---|---|
| load (s) | 6.9, 6.8, 6.7, 6.7 (mean 6.78) | 6.8, 6.8, 6.6, 6.8 (mean 6.75) |
| texture memory | 1,819 MB | 1,767 MB (−52 MB) |
| peak commit | 3,308 to 3,320 MB | 3,187 to 3,200 MB (about −120 MB) |

- The engine change removes the per-file lookup cost the atlas was saving, so the pack gains nothing on load time
  there (0.03 s, well inside the noise).
- The memory saving stays. It comes from the dookie, greenjar and drone frames no longer building mipmaps, and a
  small overlay that only adds `nomipmaps` to `dookievm`, `greenjarvm` and `rh_dronevm.shader` gives it without
  the 92 MB download: `zz_gunnomip.pk3` (56.5 KB, −68 MB texture memory), see `docs/gunnomip-2026-11-19.md`. It
  replaces the same shader files as this pack, so the two must not ship together.

## CI

`.github/workflows/build-zip.yml`:

- "Cache zz_gunframes.pk3" step. Its key is the base `bakersfield.pk3` sha256, the pinned numpy/pillow and the
  builder's hash; the builder reads nothing else.
- "Build zz_gunframes.pk3" step, which runs only on a cache miss. The pinned dependency install now also runs when
  only this cache misses.
- "Add overlay pk3s to the package" copies it in.
- "Check the package" fails the run if any of the three overlay packs is missing, if `zz_gunframes.pk3` holds no
  shaders, or if one of its shaders names a `progs/gunatlas/` image that isn't in the pack. Tested against this
  build, and against a copy with one atlas removed, which it caught.
- Release notes list the pack. The macOS app manifest picks it up through `BakersfieldQuake/`.

## Needs a decision (decided 2026-11-18: do not ship)

1. **Ship it at all: +92.1 MB per player, once.** The old frame PNGs stay unused inside `bakersfield.pk3`, which
   the no-repack rule forbids touching, so the package grows from about 1.13 to 1.22 GB. Players re-download the
   pack only when the base pack or the builder changes.
2. **The server needs nothing.** The dedicated server loads no textures. Don't add the pack to the VPS until it is in
   a release, so the server keeps carrying the release's files (audit section 6).

Decided: the three unused robhead variants are left out of the pack (owner, 2026-11-18).

## Not done

- Not installed in `G:\Quake\Combat\BakersfieldQuake` and not deployed to the VPS. The builder and this report are
  committed (`12c3da9`); the CI step is only kept as a patch.
- Measured on one fast PC, on soi6 only.
- Not checked with `gl_picmip_other 1`: the atlases are halved like any picmip texture, and the 2 px gutters become
  1 px, which is still enough for bilinear filtering.
- The test scripts (screenshot harness, alternating perf runner) live in the session scratchpad, not the repo. The
  method is described above.
