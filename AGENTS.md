# AGENTS.md

Instructions for AI coding agents working in this repo.

## Where docs go

- Every doc you write goes under `docs/`: plans, specs, notes, screenshots, reports. Never put docs in the repo
  root or next to source.
- Agent prompts and handoffs go in `docs/prompts/`.
- The repo root holds only `README.md`, `AGENTS.md`, `CLAUDE.md`, `PROGRESS.md`, `Makefile` and files the game itself
  reads.
  The `.gitignore` only excludes local build data (the unpacked `BAKOQUAKE/` package and logs).

## Commits and pushing

- **Don't push right after committing.** Commit locally, keep working, and push once a piece of work is finished
  and checked. Pushes trigger CI builds (some workflows already do, the rest will), and each build costs time and
  produces artifacts nobody needs.
- **Before pushing, squash small commits into large, logical ones** (`git commit --fixup` plus
  `git rebase -i --autosquash`, or a soft reset and recommit). One commit per logical change: "add go-karts"
  rather than "fix typo", "fix again", "tweak texture".
- **Only rewrite commits that haven't been pushed.** Never force-push `main`.
- No AI session links or `Claude-Session:` trailers in commit messages or PR descriptions.

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

## macOS app

- The signed, notarized `BAKOQUAKE-macos-arm64.dmg` is built **only in CI** (the `macos` job in
  `.github/workflows/build-zip.yml`, which runs `source/mac/build_app.sh`). Never upload a locally built DMG or app
  to a release. Local runs (`SKIP_NOTARIZE=1`) are for debugging the script.
- Do not run any builds for the macOS app or for assets on a mac - use CI!
One logical change per commit.
