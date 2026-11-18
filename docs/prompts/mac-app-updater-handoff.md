# Handoff: differential updates for the macOS app

**For:** the agent that owns `source/mac/build_app.sh` and the `macos` job in `build-zip.yml`.
**Read first:** `AGENTS.md`, `docs/auto-update-plan.md` (the status block at the top describes v1 as built), `tools/bq_update.py`.

## Where things stand

- Every release now carries `manifest-windows-x64.json`, `manifest-linux-x86_64.json` and `manifest-macos-arm64.json`.
  Each lists every file in that platform's zip (size and sha256) and the tag-specific zip URL.
- `tools/bq_update.py` (stdlib only) reads `releases/latest/download/manifest-<platform>.json`, compares the files under
  `--root`, and fetches only the changed ones out of the release zip with HTTP Range. It returns exit code 3 when
  files changed, 0 otherwise, and never blocks the game.
- Windows ships a frozen `tools/bq-update.exe`. Linux, and the macOS zip when a real Python exists, run the `.py`.
- **The `.app` has no updater.** `build_app.sh` copies `tools/` into `Contents/Resources/game/`. That now includes
  `bq_update.py`, which is harmless text. **Do not let a frozen Mach-O `bq-update` into `tools/` without signing it**,
  or notarization fails. CI deliberately doesn't build one for macOS yet.

## The problem

The signed bundle is read-only, so the updater can't write to `Resources/game/`.

## Option to check first: overlay updates into the userdir

Zircon's `fs.c` gives `-userdir` priority over `-basedir` for the same gamedir (`FS_AddGameHierarchy`). If that holds
for loose files and pk3s alike, the updater could run with `--root ~/Library/Application Support/BAKOQUAKE` and only
write the files that differ from the bundle. Nothing would need to move out of the bundle.

Catches to verify:
- **A file can't be deleted** from the bundle by writing to the userdir. A release that removes a file (for example an
  old `bm_up_N.cfg`) would leave the bundle copy visible.
- The updater's diff must be computed against the bundle plus the userdir overlay, not the userdir alone. Otherwise
  the first run downloads 1.2 GB. That means a small change to `bq_update.py`: a read-only `--base` directory for
  hashing, writes go only to `--root`. Ask Rob before changing the shared updater; Windows and Linux depend on it.
- Engine, launcher and dylib changes still need a new DMG.

## The other option

Seed the game data out of the bundle on first run into Application Support and run the updater on that copy. It's
simpler for the updater, but doubles the disk use (about 1.2 GB) and needs a first-run copy with progress.

## Deliverable

A short recommendation to Rob, with evidence from `fs.c` and a real test on the Mac. Then implement the chosen
option in `build_app.sh` and the launcher. The updater runs on Python, which the app can't count on, so it would have
to be frozen and signed, or rewritten as a small Swift or shell tool. Weigh that in the recommendation.
