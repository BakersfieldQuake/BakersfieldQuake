# BAKOQUAKE auto-updater: plan

Status: v1 implemented 2026-11-18: `tools/bq_update.py`, `source/ci/make_manifest.py`, the `updater` job and the
manifest steps in `build-zip.yml`, and hooks in all four launchers. Tests: `python -m unittest discover -s source/ci/tests`.

**What v1 covers, and how it differs from the plan below:**
- Windows: frozen `tools/bq-update.exe`. Linux, and the macOS zip when a real Python exists: `python3 tools/bq_update.py`.
- **No `release.json` on main.** The pointer is `releases/latest/download/manifest-<platform>.json`. GitHub redirects it
  anonymously to the newest non-draft release (verified 2026-11-18), so CI makes no commit to main per release, and
  the 5-minute raw-URL cache is gone. Each manifest names its own tag-specific zip URL, so the pair is consistent.
- **macOS app:** the signed bundle can't change, so `source/mac/launcher.sh` runs the game from an APFS clone of the
  bundle's game data in `~/Library/Application Support/BAKOQUAKE/game` (instant, no extra disk) and updates that clone
  with `Contents/MacOS/bq-update` (this script frozen and signed by `build_app.sh`) against `manifest-macos-app.json`,
  which lists only `BakersfieldQuake/`, `quake15/` and `tools/`. A new DMG gets a fresh clone. Engine changes still
  need a new DMG. Overlaying updates into the userdir was rejected: Zircon searches every userdir pk3 before every
  basedir file, so an updated `bakersfield.pk3` would shadow the bundle's `zz_*.pk3` overrides. Validation:
  `docs/updater-validation.md`.
- Exit code 3 means files changed. The launchers then re-run themselves, because cmd and bash read a running script
  from disk line by line, and the update may have just replaced it. Each hook is a single parsed block for that reason.
- No tkinter window: `PLAY BAKERSFIELDQUAKE.exe` starts `Play.cmd` with `CreateNoWindow`, so the updater opens its own
  console (`AllocConsole`) only when it has something to download, and uses a MessageBox for errors.
- `make_manifest.py` lives in `source/ci/`, not `tools/`: everything in `tools/` ships to players.

## Goal

When a player launches the game, or runs a separate "Update" launcher first, the updater fetches the newest
release. It downloads only the files that changed, applies them safely and then starts the game. It must never
stop someone from playing: if the player is offline, GitHub is down or anything else goes wrong, the game starts
on the version already installed.

## What the release history says (measured 2026-11-17)

These numbers come from the release zips' central directories (HTTP range reads), including the entries inside
the stored `.pk3` files.

| | |
|---|---|
| Package | 1222 MB, 98 files |
| `build-20261111` to `build-20261118` | 20 files changed, **6.6 MB** |
| `v1.0` to `build-20261118` | 23 files changed, 6.6 MB |
| `bakersfield.pk3`, `q15.pk3` (most of the 1.2 GB) | **unchanged** in every release so far |
| The 6.5 MB of that | `zz_bakovan.pk3`, whose entries are byte-identical; only zip timestamps differ, because `build_van_bako_pk3.py` uses `writestr(name, …)`, which stamps "now" |

Where content lives today: `progs.dat`/`csprogs.dat` (QC) and the maps (`maps/*.bsp`, `.lit`; up to 43 MB each)
ship as **loose files**. Models, sounds and textures are packed into `bakersfield.pk3` (442 MB, 5726 entries) and
`q15.pk3` (477 MB). CI rebuilds neither; `bakersfield.pk3` only changes when someone rebuilds it locally and
re-uploads the base zip.

Conclusion: a file-level diff turns a 1.2 GB re-download into kilobytes for QC, config and map changes, once the pk3
build is reproducible. The weak spot is new models and sounds (like the go-karts in `92b5cdc`). If those get
repacked into `bakersfield.pk3`, every player downloads 442 MB again. See the content rule below.

Verified hosting facts:
- Release assets on the public repo serve HTTP Range without auth (302 to `release-assets.githubusercontent.com`, then `206`).
- `raw.githubusercontent.com` sends `cache-control: max-age=300`, so a new release reaches clients within about 5 minutes.

## Design decisions

0. **Content rule: never repack the big base pk3s.** New or changed models, sounds and textures ship in small
   overlay pk3s that sort after the base (for example `zz_karts.pk3`), the same mechanism `zz_bakovan.pk3`
   already uses. DarkPlaces loads a gamedir's pk3s in name order, and later ones override earlier ones.
   A content drop then costs its own size, not 442 MB. CI enforces the rule: `build-zip` warns loudly in the job
   summary if `bakersfield.pk3` or `q15.pk3` differs from the previous release ("this release makes every player
   download 442 MB"). Fold overlays back into the base only on purpose, as a rare "big update". If repacking turns
   out to be unavoidable, v2 adds member-level pk3 diffs: the client rebuilds the pk3 from its local entries plus
   the changed entries fetched by Range from the new inner pk3, verified by per-entry hashes. That is about 0.5 day
   extra, and not needed while the rule holds.

1. **The unit of difference is the whole file, identified by sha256.** The manifest has room for a later
   `patch` field (zstd `--patch-from` between versions) for when a big pk3 changes. That is not in v1.
2. **No per-file hosting.** The updater pulls changed files straight out of the current platform release zip with
   Range requests: it reads the central directory once (about 100 KB) and then fetches the byte span of each changed
   entry. CI uploads nothing new apart from a small manifest. Old releases don't matter; the client always reads from
   the newest one.
3. **The pointer is `release.json` on `main`**, fetched from the raw URL. CI commits it only after the release
   and all its assets are published, so a client never sees a pointer to missing files.
4. **The client is one stdlib-only Python file, `tools/bq_update.py`, frozen per OS in CI with PyInstaller**
   (`bq-update.exe` for Windows x64, `bq-update` for macOS arm64) and shipped in `tools/`.
   - Why freeze it: stock Windows has no Python, and macOS `python3` is a stub that prompts to install the Xcode
     Command Line Tools. Asking friends to install Python defeats "make it easy".
   - Launchers try, in order: the frozen binary, then `python3 tools/bq_update.py` (dev machines and Linux), then
     skip the update and play.
   - Risk: PyInstaller onefile executables sometimes trip Defender heuristics. Test on the win11 VM with Defender
     on. If it is flagged, fall back to `--onedir` or Nuitka.

## Files

`release.json` (on `main`, raw URL). **Not used in v1**, see the status above:

```json
{
  "schema": 1,
  "build": 57,
  "version": "build-20261125-abc1234",
  "published": "2026-11-25T03:10:00Z",
  "min_updater": 1,
  "platforms": {
    "windows-x64": { "manifest": "https://github.com/BakersfieldQuake/BakersfieldQuake/releases/download/<tag>/manifest-windows-x64.json" },
    "macos-arm64": { "manifest": "https://github.com/BakersfieldQuake/BakersfieldQuake/releases/download/<tag>/manifest-macos-arm64.json" }
  }
}
```

`build` is `github.run_number`. It only goes up, so clients compare that number instead of parsing tags.

`manifest-<platform>.json` (a release asset, generated from the zip CI just built):

```json
{
  "schema": 1,
  "build": 57,
  "zip": "https://github.com/BakersfieldQuake/BakersfieldQuake/releases/download/<tag>/BAKOQUAKE.zip",
  "root": "BAKOQUAKE/",
  "files": {
    "BakersfieldQuake/default.cfg": { "size": 9811, "sha256": "…" },
    "darkplaces.exe":               { "size": 5421056, "sha256": "…" }
  },
  "exec": ["darkplaces-sdl", "darkplaces-dedicated", "tools/bq-update"],
  "install_only": ["BakersfieldQuake/config.cfg"]
}
```

Paths are relative to the package root. `install_only` files are written only if missing, because the player owns
them after first run (for example the `config.cfg` seed).

Local state, `.bq/state.json` in the package root, records the installed build and a cache of
`{path: [size, mtime_ns, sha256]}`, so a normal launch only stats files instead of re-hashing 1.2 GB.

## Client flow

1. Load `.bq/state.json`. If it is missing (first run, or an install from before the updater), hash every managed
   file once. Expect a few seconds on an SSD.
2. Take `.bq/update.lock`. If Play and Start Server are launched together, the second one skips updating.
   GET `release.json` with a 3 s timeout. On any failure, log it and go to step 8.
3. If `build` is not newer than the installed build, go to step 8. A manifest whose `build` is lower than the
   installed build is refused, so nobody can serve a rollback. If `min_updater` is higher than this updater's
   version, update only `tools/bq-update*` first (step 6 handles replacing itself), then re-run.
4. GET the platform manifest. Compare its sha256 with the cached local hash for every file and build the lists:
   files to fetch (new or changed), and files to delete (in the previous manifest but not the new one).
5. Resolve the zip URL's 302 once per run. The redirect target is a signed URL that expires, so re-resolve it on
   403. Range-fetch each entry into `.bq/staging/`, inflating deflated entries with `zlib`. Check the sha256 against the
   manifest. On any mismatch, abort the whole update and keep playing the old version.
6. Apply: `os.replace` each staged file into place. On macOS, `chmod +x` the files listed in `exec`. The running
   updater replaces itself by renaming its own `.exe` to `.old` (Windows allows renaming a running exe), and the
   next run deletes the `.old`. If a file is locked (a dedicated server still running from this folder), roll back
   the files already replaced from `.bq/backup/`, report it, and play the old version.
7. Delete removed files and write the new state.
8. Return control to the launcher, which starts the engine.

**Files the updater never touches:** anything not in the new or previous manifest, which covers `id1/` (player's
paks), `config.cfg` after install, `lan_server.cfg`, demos, screenshots, logs and pid files. Deletions only ever
come from the previous manifest, never from a wildcard.

Files written by `urllib` don't get the `com.apple.quarantine` attribute, so updated macOS binaries won't trip
Gatekeeper. Only the first zip a player downloads in a browser needs the `xattr -dr` step.

**macOS app (DMG):** most Mac players now use the signed `BAKOQUAKE.app`, which can't be written into without
breaking its signature. Its game data has to move out of the bundle into `~/Library/Application Support/BAKOQUAKE`
(already its `-userdir`), and the updater would update it there. Engine or launcher changes still need a new DMG.

## Launcher integration

- `Play.cmd`, `Start Server.cmd` and `Play.sh` (macOS) run `tools/bq-update[.exe] --launch` before starting the
  engine, then continue whatever its exit code is.
- New standalone entry points for running the update before launch: `Update BAKOQUAKE.cmd` and
  `Update BAKOQUAKE.command`. A macOS `.command` file opens in Terminal when double-clicked; a `.sh` opens in an editor.
- Flags: `--check` (report only; exit 10 if an update is available), `--launch` (quiet when there is nothing to
  do), `--force-rehash`. `BQ_NO_UPDATE=1` skips the updater, for playing offline at a LAN.
- The updater must run **before** `Play.cmd`'s lanscan step, which hides the console ("This also hides this console
  window"). Otherwise a large download started through `PLAY BAKERSFIELDQUAKE.exe` looks like a hang.
- Output: a console progress line (`Updating BAKOQUAKE build 56 to 57: 3 files, 41 KB`), in a visible window
  whenever bytes are downloading. If the console is hidden, Windows shows a small progress window (tkinter in the
  frozen build). Errors also get a MessageBox, as the pak finder does.

## CI changes (`build-zip.yml`)

1. Make `build_van_bako_pk3.py` reproducible: use `zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))`,
   write entries in sorted order, and **pin `numpy` and `pillow`** in the workflow. A Pillow upgrade changes
   the PNG bytes and brings the churn back. Done alone, this removes the 6.5 MB of churn per release.
2. Add a `updater` matrix job (`windows-latest`, `macos-latest`) that freezes `tools/bq_update.py` with
   PyInstaller and uploads the result as an artifact. The package job puts each binary into its platform zip's
   `tools/`. The Linux zip ships the `.py`.
3. Add `tools/make_manifest.py`, which reads each built zip and writes `manifest-<platform>.json`. Attach the
   manifests to the release.
4. After a non-draft publish, write `release.json` to `main` as the last step, through the Contents API
   (`gh api -X PUT repos/BakersfieldQuake/BakersfieldQuake/contents/release.json` with the file's current `sha`), not
   `git push`. People push to `main` while CI runs, and a plain push would fail as non-fast-forward. The API
   commit doesn't trigger `build-zip` (it is `workflow_dispatch` only).
5. Add the content-rule check from decision 0.

## Security

The updater writes executables (engine, launchers, itself). Today, anyone who can publish a release to
`BakersfieldQuake/BakersfieldQuake` can put a bad zip in front of players who choose to download it. With auto-update,
that person's code runs on every player's next launch, with no human step in between. HTTPS plus sha256 protects
against corruption and network tampering, but not against a compromised repo or token.

**Decision (2026-11-18): no manifest signing.** It's a game among friends. HTTPS plus sha256 is enough.

## Testing

- Unit tests: manifest diff (new, changed, removed, `install_only`), Range extraction for stored and deflated
  entries against a local zip served by `http.server`, state cache invalidation.
- win11 VM:
  - fresh old-build install, then update
  - offline at launch
  - corrupted download (bad hash)
  - locked file (server running), then rollback
  - updater replacing itself
  - Defender scan of `bq-update.exe`
- macOS: there is no Mac here. Add a CI smoke test on a `macos-latest` runner (install build N-1, run the
  updater, check hashes), then Rob tests at home.

## Rollout

Players on current zips have no updater, so they need one last manual download. After that, every update is
automatic.

## Effort

About 1 to 1.5 days:
- 0.5 day: updater core and unit tests
- 0.5 day: CI freeze, manifest and `release.json` steps
- remainder: VM testing

Step 1 of the CI changes (the reproducible pk3) is about 10 minutes and pays off on its own.

## Resolved questions

- Content rule (decision 0): yes. Content ships as `zz_*.pk3` overlays (`zz_karts.pk3` is the first), and
  `AGENTS.md` and the base pk3 guard enforce it.
- Signing manifests: no, see Security.
- The repo is intentionally public.
