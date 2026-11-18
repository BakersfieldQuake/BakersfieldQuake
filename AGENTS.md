# AGENTS.md

Instructions for AI coding agents working in this repo.

## Where docs go

- Agent prompts and handoffs go in `docs/prompts/`; other notes and plans go in `docs/`.
- The repo root holds only `README.md`, `AGENTS.md`, `CLAUDE.md` and files the game itself reads.
  The `.gitignore` is an allowlist (`*`), so add new files with `git add -f`.

## macOS app

- The signed, notarized `BAKOQUAKE-macos-arm64.dmg` is built **only in CI** (the `macos` job in
  `.github/workflows/build-zip.yml`, which runs `source/mac/build_app.sh`). Never upload a locally built DMG or app
  to a release. Local runs (`SKIP_NOTARIZE=1`) are for debugging the script.
- Bundle no Homebrew libraries. They are built for the build machine's macOS and would raise the app's minimum OS
  (13.0). Add a library by building it from a pinned source in `build_app.sh`, like the others.
- The bundle is read-only once signed. Everything the game writes goes to `~/Library/Application Support/BAKOQUAKE`
  (`-userdir`).

## Packaging game content (pk3 rules)

Players get updates through a differential updater: only files whose sha256 changed are downloaded. The package
is about 1.2 GB, almost all of it two base pk3s. If either changes, every player re-downloads it.

- **Never repack, rebuild or edit the base pk3s:** `BakersfieldQuake/bakersfield.pk3` (442 MB) and
  `quake15/q15.pk3` (477 MB).
- **Ship new or changed assets (models, sounds, textures, shaders) as small overlay pk3s**, one per feature:
  `BakersfieldQuake/zz_<feature>.pk3` (lowercase), for example `zz_karts.pk3`. `zz_bakovan.pk3` is the reference
  example.
- **Engine resolution order** (DarkPlaces/Zircon `fs.c`):
  - Within a gamedir, pk3s load in sorted filename order, and the later name wins, so `zz_*` overrides
    `bakersfield.pk3`.
  - Loose files beat every pk3, so don't leave stray loose copies of assets that live in an overlay.
  - An overlay can add or override files but cannot delete them from a base pk3. Ask before working around that.
- **Keep `progs.dat`, `csprogs.dat` and `maps/*.bsp`/`.lit` as loose files.** They already diff fine.
- **The repo is text/source only.** Generate overlay pk3s in CI from source: a build script under
  `source/mm_tools/`, plus a step in `.github/workflows/build-zip.yml` that writes to
  `out/BAKOQUAKE/BakersfieldQuake/`. Model it on the `zz_bakovan.pk3` step. Don't commit built binaries.
- **Overlay pk3s are cached in CI** (`actions/cache`, one entry per pk3). The key is the base `bakersfield.pk3`
  sha256, the pinned numpy/pillow and a hash of every repo file the builder reads. When a builder starts reading a
  new file (an import, a shader, a texture), add it to that pk3's cache key, or CI keeps shipping the stale pk3.

## Reproducible builds

An unchanged build must produce byte-identical files, or players download them again for nothing.

- Write zip entries with `zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))` and a fixed `external_attr`.
  Never use `ZipFile.write()` or `writestr()` with a bare name; that stamps the current time.
- Add entries in sorted path order. Use `ZIP_STORED` for already-compressed data (png/jpg/ogg), otherwise
  `ZIP_DEFLATED` at a fixed level.
- No current time and no unseeded randomness in generated geometry or textures.
- Pin every Python dependency the build uses (numpy, pillow, …) to exact versions in the workflow. A Pillow
  upgrade changes PNG bytes.
- Check it: build twice and compare sha256.

## Open work

1. Package the go-kart content from `92b5cdc` (MD3s, driver, `scripts/gokart.shader`, referenced textures) as a CI-built `zz_karts.pk3`.
2. Make `source/mm_tools/van_bako/build_van_bako_pk3.py` reproducible. It currently uses `writestr(name, …)`,
   which gives new timestamps on every run, so players re-download 6.5 MB per release for nothing.
3. Add a guard to `build-zip.yml`: if the sha256 of `bakersfield.pk3` or `q15.pk3` differs from the previous
   release's `BAKOQUAKE.zip`, emit a `::warning::` and a job-summary line saying the release forces every player to
   re-download about 450 MB.

One logical change per commit.
