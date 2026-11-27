
## 2026-11-01 — DarkPlaces on macOS + custom van texture

**Outcome**
- Built DarkPlaces from source (upstream 10d4863, arm64) at ~/src/darkplaces; binary copied to `darkplaces-sdl`.
- Added `Play.command` (macOS launcher): warmup by default, `./Play.command <ip>` joins + writes F2 target; caps `cl_maxfps 120`.
- Updated `BakersfieldQuake/bakersfield.pk3` + `progs.dat` from ../BAKOQUAKE (old copies kept as `.old`) — fixes missing wcannon sounds on the online server.
- Custom ProMaster front (ChatGPT-drawn) packed as `BakersfieldQuake/zz_bakovan.pk3` (overrides `progs/veh_van_tex.png` + glow).

**Build notes**
- sdl2-compat's `sdl2-config` lacks `--static-libs`: build with `SDLCONFIG_UNIXSTATICLIBS='`sdl2-config --libs`'`.
- 2k+ JPG textures: link jpeg-turbo (`DP_LINK_JPEG=shared`, include/lib from /opt/homebrew/opt/jpeg-turbo).
- png/ogg/vorbis/freetype/curl are dlopen'd: launcher sets `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`.

**Perf**
- FPS drops (5–25 fps) traced via `sample` to `glBufferSubData` forcing a Metal command-buffer flush per call (Apple GL-on-Metal).
- Patch in ~/src/darkplaces (gl_backend.c, glquake.h, vid_shared.c): unsynchronized `glMapBufferRange` for R_BufferData_Store appends. Built, NOT installed or benchmarked. Install: `mv darkplaces-sdl darkplaces-sdl.orig && cp ~/src/darkplaces/darkplaces-sdl .`

**Verification**
- Dedicated server + client smoke tests load mod/CSQC; connected to 72.62.241.93:26000 with 0 download rejections after asset update.
- Van texture not visually confirmed by me in-game.

**Follow-up**
- Benchmark the glMapBufferRange patch (`-benchmark intro`, baseline 24.6 fps avg, min 5).
- Send `zz_bakovan.pk3` to server owner / add to LAN zip.

## 2026-11-02 — LA dedicated server (GCP)

**Outcome**
- VM `quake-la` (project notarydash, us-west2-a, e2-small, Debian 13, 20 GB), external IP 34.102.92.107, tag `quake-server`.
- DarkPlaces dedicated built from upstream 10d4863 (`make sv-release`, needed `libjpeg-dev`) at ~/src/darkplaces; game data from https://larrywew.fun/bakersfield-quake/BAKOQUAKE.zip in ~/quake, plus `zz_bakovan.pk3`.
- systemd `quake.service` (enabled, Restart=always): `-dedicated 16 -game quake15 -game BakersfieldQuake -port 26000 +exec server.cfg` (bklan4).
- Firewall `allow-quake-udp-26000`: udp:26000 from 0.0.0.0/0 → tag quake-server.

**Verification**
- `getinfo` from Mac over the internet: 147 ms, infoResponse Quake_1.5 / bklan4 / 16 slots.

**Notes**
- SSH via `gcloud compute ssh quake-la --zone us-west2-a --tunnel-through-iap` (no public SSH rule).
- Logs: `journalctl -u quake -f`. Ephemeral external IP — reserve a static one if the address should survive stop/start.
- Teardown: `gcloud compute instances delete quake-la --zone us-west2-a` + `gcloud compute firewall-rules delete allow-quake-udp-26000`.

## 2026-11-02 — quake-la: high-ping kick fix (option A)

**Root cause** (same as on 72.62.241.93): Combat+ QC `stuffcmd`s `crosshair_color_*` / `v_psycho` every server frame (88 B reliable/frame at sys_ticrate 0.01); clients with RTT over about 115 ms can't drain the reliable queue → overflow → dropped. Seen on quake-la journal: "Chicken"/"TruE" dropped (Buffer overflow in net message).

**Fix**: `~/quake/BakersfieldQuake/server.cfg` sets 0 for monster_health_crosshair, player_health_crosshair, weapon_range_crosshair, ghost_follower_psycho_effect, evil_faces_psycho_effect, psycho (before `map bklan4`; exec'd after q15_config_coop.cfg so it wins). Backup: server.cfg.bak_prekickfix. Service restarted.

**Map changes**: timelimit 20, bm_maplist "bklan4" → map reloads every 20 min; map votes still possible (majority).

**Not verified**: a high-ping client staying connected over 60 s.

**Follow-up**: option B (QC caches last-sent value, stuffcmd only on change) restores health crosshair; needs progs.dat rebuild by the mod owner.

## 2026-11-11 — Consolidated into the repo; one runnable tree

**Outcome**
- `BAKOQUAKE/` (David's v1.5 drop) is now the single runnable tree. Merged in from the old BakersfieldLAN folder:
  `darkplaces-sdl` (patched arm64 build), `zz_bakovan.pk3`, maps missing from v1.5 (`bklan`, `bklan4`, `bklan5`,
  `orcom`, `bfarena`), `tools/make-mac-app.sh` + `tools/AppIcon.icns`, new `README-MAC.txt`.
- `Play.command` is now a wrapper over David's `Play.sh` (sets `DYLD_FALLBACK_LIBRARY_PATH`, `cl_maxfps 120`): one launcher codepath, gets LAN scan + F2.
- Engine source moved to `source/darkplaces` (with `source/darkplaces-macos-mapbufferrange.patch`, `source/dp-build.log`); van photos to `docs/reference`.
- Tracked root configs (`autoexec.cfg bm_binds.cfg default.cfg server.cfg warmup.cfg quake.rc`) synced from v1.5. They were Nov 2 copies; the build-zip workflow overlays them onto the release, so running it would have reverted David's changes.
- Old BakersfieldLAN folder moved to Trash (`~/.Trash/BakersfieldLAN-*`); Rob's old `config.cfg` saved as `docs/config-rob-2026-11-01.cfg`.
- `~/Applications/Bakersfield Quake.app` rebuilt against the new path; works now (previous failure was TCC on ~/Downloads).

**Correction to 2026-11-01**: the installed `darkplaces-sdl` DOES include the glMapBufferRange patch (source mtimes precede the link by 9 s). Still not benchmarked.

**Verification**
- App launched via `open -a`: DP7, CSQC loaded, `-userdir` = BAKOQUAKE.
- Not verified: the five re-added maps load; root cfg diff not committed.

**Follow-up**
- Commit the root cfg sync (shared repo) so the workflow stops shipping stale configs.
- LA server still runs bklan4 + old progs; update it to v1.5 assets.

## 2026-11-11 — Missing textures + launcher crash on macOS

**Root cause**
- Missing textures: running `./Play.sh` directly skipped `DYLD_FALLBACK_LIBRARY_PATH` (only `Play.command` set it). darkplaces-sdl dlopen()s `libpng16.16.dylib` by bare name, failed to find it, and every PNG texture logged `Error loading image ... (file loaded but decode failed)`. Not a release problem: with the path set, `little_st_james` and `bklan4` load with no texture errors.
- App/Raycast crash: launched without Homebrew on PATH, `#!/usr/bin/env bash` resolves to /bin/bash 3.2; `set -u` + empty `"${FIRST[@]}"` = `FIRST[@]: unbound variable` once config.cfg exists.

**Fix** (BAKOQUAKE/, untracked)
- `Play.sh`, `Start-Server.sh`: set `DYLD_FALLBACK_LIBRARY_PATH` on Darwin; empty-array expansions use `${A[@]+"${A[@]}"}`.
- `Play.command`: now just `COMBAT_ARGS` default + `exec /bin/bash Play.sh` (forces the 3.2 path so it stays tested).

**Verification**
- `./Play.sh` with DYLD unset: engine env has the path, libpng16 mapped from /opt/homebrew.
- App via `open -a` with a real config.cfg: game runs, libpng loaded.

**Follow-up**
- Play.sh / Start-Server.sh fixes belong upstream (David's launchers); not in the repo yet.

## 2026-11-17 — Signed + notarized BAKOQUAKE.app / DMG (mimi)

**Outcome**
- `source/mac/build_app.sh <tag>` (+ `source/mac/launcher.sh`) builds `BAKOQUAKE-macos-arm64.dmg`: the app and the DMG are both signed with Developer ID 2RRH9B8AL2, notarized and stapled. Commit `d071ac0` (not pushed).
- Deviation from the handoff: Homebrew bottles on mimi are `minos 27.0`, so bundling them would make the app macOS 27+. Instead the script builds SDL2 2.32.10, ogg 1.3.6, vorbis 1.3.7, freetype 2.15.0 and libjpeg-turbo 3.2.1 (jpeg62) from source at 13.0, plus Zircon `e19de67`. The real SDL2 replaces sdl2-compat+SDL3.
- No entitlement or engine patch needed. Leaf-name `dlopen` also searches the main executable's `LC_RPATH`, so linking with `-rpath @executable_path/../Frameworks` is enough under the hardened runtime.
- Notarization creds: `NOTARY_ENV=~/workspace/screenpipe-app/.env` (Apple ID + app-specific password, same team). `NOTARY_PROFILE` works too.

**Verification**
- Notary: app `d636fd48…` and DMG `ecb6d348…`, both Accepted. `spctl` reports `Notarized Developer ID` for the app, the quarantined DMG and the installed copy in /Applications. `codesign --verify --deep --strict` and `stapler validate` pass.
- The build gate fails if any Mach-O has minos > 13.0 or links /opt/homebrew, /usr/local or /Users. It passed.
- Quarantined DMG → /Applications (copied with ditto, not dragged in Finder) → `open`: Gatekeeper did not block. It ran under App Translocation, and `vmmap` showed SDL2, jpeg, freetype, ogg, vorbis and vorbisfile all loaded from `Contents/Frameworks`.
- Pak finder copied pak0/pak1 from `~/Downloads/BAKOQUAKE/id1`, but only from a terminal launch (`env -i`), which runs under the terminal's Downloads permission. First-run name was applied. `+map bakersfielddowntown` loads and renders, `zircon_log.log` shows libjpeg/freetype/vorbis/ogg/curl loaded, and there are no not-found or decode errors.
- Not tested: a first launch through LaunchServices with no paks (Downloads TCC prompt, chooser, alert), the `gh release download` branch (zip was fetched by hand), a real macOS 13 machine (minos-checked only), a user account without Homebrew (covered by the otool gate plus vmmap), and an in-game round with sound.

**Follow-up**
- Rob: no local upload, the DMG must come from CI. Commit `9aa571c` adds a `macos` job to build-zip.yml (macos-15, Xcode 16.4, cached deps) that builds, notarizes and uploads the DMG to the release. It hasn't run yet, because the repo has no signing secrets: MACOS_CERT_P12_BASE64, MACOS_CERT_PASSWORD, APPLE_ID, APPLE_TEAM_ID, APPLE_APP_SPECIFIC_PASSWORD.
- Real 512/1024 px icon art (currently upscaled from 256).
- Dock icon switches to the Zircon "Z" after launch: `vid_sdl.c` calls `SDL_SetWindowIcon` with a built-in icon, and SDL on macOS applies it to the Dock. The `mod_info.txt` `iconbase64` override only applies to single-gamedir `#contents.pk3` mods, so it doesn't fit here. The fix is an engine change (skip it on macOS) in rgr4y/zircon-darkplaces.
- Leftovers: test install at `/Applications/BAKOQUAKE.app`; build cache at `~/build/bakoquake-mac` (~3.4 GB: zip, src, out).
- `docs/mac-app-handoff.md` "Libraries" section is now stale (brew/entitlement plan).

## 2026-11-17 (later) — macOS DMG moved to CI

**Outcome**
- Rob: no local uploads; macOS builds and notarization happen only in CI. The `macos` job in build-zip.yml (now named "Build release packages") runs `build_app.sh` on macos-15 / Xcode 16.4 and uploads the DMG to the release. Secrets set: MACOS_CERT_P12_BASE64, MACOS_CERT_PASSWORD, APPLE_ID, APPLE_TEAM_ID, APPLE_APP_SPECIFIC_PASSWORD.
- Draft run 44244719549 at `d2c28d2` succeeded: `build-20261118-d2c28d2-draft` has the Windows, Linux and macOS zips plus `BAKOQUAKE-macos-arm64.dmg` (1.10 GB). Notary accepted the app (`29a1b85e…`) and the DMG (`85515fb2…`), and both stapled.
- CI fixes along the way:
  - go-kart driver: `player.mdl` from Quake 1.06 is now shipped at `source/mm_tools/id1/player.mdl`.
  - package check: `//` comments in `quake.rc` are ignored.
  - overlay pk3s are cached with `actions/cache`.
  - docs and README updated.

**Root cause (the release 403)**
- `HTTP 403: Resource not accessible by integration` on `gh release create`: the run's commit carried an older `build-zip.yml` than `main`, because a workflow change was pushed mid-run. A GITHUB_TOKEN can't create a release/tag whose workflow files differ from the default branch's. Don't push workflow changes while a release run is in flight.
- Empty `base_tag` resolves to "latest" (`build-20261118-114a625`, pre-v1.10), which fails the package check. Use `base_tag=base-v1.10` until a v1.10-based non-draft release exists.

**Not verified**
- The CI-built DMG hasn't been downloaded and launched; Rob is on a metered connection. Only the CI notary/staple/spctl output has been checked.
- First launch with no paks (Rob, 2026-11-18): TCC never prompts for Downloads (the script main executable is a guess as the cause, not verified), so the `~/Downloads` search silently finds nothing and the "Locate your Quake id1 folder" chooser appears. Rob called it good, so the copy after choosing wasn't checked further.
- Test leftovers: `~/Library/Application Support/BAKOQUAKE.test-225302` and `.test2-235955`.
- Run 44248048258 (`a32f658`): pk3 caches hit (build job 1:47, was 4:00), mac deps cache saved, notarize progress visible in the log.

**Follow-up**
- Thin app + data in Application Support (notarize about 10 MB instead of 1 GB; needed for the updater anyway). Proposed, not started.
- Notarize step is silent (`--output-format json`); switch to text output for progress.
- Dock icon flips to the Zircon "Z" (engine `SDL_SetWindowIcon`); fix in rgr4y/zircon-darkplaces.

## 2026-11-18 — Differential updater (Windows, Linux) and game shortcuts

**Outcome**
- `tools/bq_update.py`: on launch, fetches `releases/latest/download/manifest-<platform>.json` and downloads only changed files out of the release zip, one HTTP Range request each. Everything is verified before anything is replaced. A failure rolls back and starts the installed version. It refuses rollbacks and never touches files outside the manifests (paks, `config.cfg`). Exit 3 means files changed; the launcher then restarts itself.
- `source/ci/make_manifest.py` and the CI changes:
  - New `updater` job: runs the tests on Windows and freezes `tools/bq-update.exe`, cached on the script.
  - Releases now carry `manifest-{windows-x64,linux-x86_64,macos-arm64}.json`.
  - No `release.json` on main: the latest-release redirect is the pointer (verified anonymous + Range).
- Hooks in Play/Start Server (`.cmd` and `.sh`). Each is a single parsed block, because cmd and bash read a running script from disk.
- Manifest signing dropped (Rob: game among friends).
- Start Menu/Desktop shortcuts (Windows, `tools/install-shortcuts.ps1`) and `.desktop` entries (Linux, `tools/install-shortcuts.sh`). CI ships `source/icons/*` into `tools/`. Done by a subagent on a branch, reviewed and fast-forwarded.
- `AGENTS.md`: docs only under `docs/`; batch and squash commits before pushing.
- win11 VM:
  - Clock fixed: libvirt `offset='utc'`, because the guest has `RealTimeIsUniversal=1` and w32time is disabled.
  - SSH (`ssh win11`) and autologin set up.

**Root cause**
- Windows CI test step hung 30 min: a failed update in a test opened `MessageBoxW`, which blocks forever headless. Dialogs and the console now appear only with `--launch`.

**Verification**
- Unit tests (7) pass on Linux and on the Windows runner.
- Live Range smoke test against the GitHub latest release.
- win11 VM with the draft `build-20261118-4517e29-draft`, served from the host:
  - untouched install: hashes in 2 s, downloads nothing
  - tampered/deleted files repaired; `config.cfg` and `id1` kept
  - `--check` exits 10
  - offline: exit 0 in 3 s; `BQ_NO_UPDATE` skips
  - locked engine exe: earlier swap rolled back
  - running updater replaced itself
  - tampered `Play.cmd` restored, re-executed, and the engine started
- Shortcuts: verified by the subagent on Linux (temporary HOME) and on the VM (.lnk read back); not double-clicked in a desktop session.

**Changed files**
- `tools/bq_update.py`, `tools/install-shortcuts.{ps1,sh}`
- `source/ci/make_manifest.py`, `source/ci/tests/test_bq_update.py`
- `launchers/*`, `.github/workflows/build-zip.yml`, `README.md`, `AGENTS.md`, `.gitignore`
- `docs/auto-update-plan.md`, `docs/prompts/mac-app-updater-handoff.md`

**Follow-up**
- Local `main` is 2 commits ahead (shortcuts, rollback message fix). Push, then run the next draft build.
- Publish a v1.10-based build as Latest. Until then, the default base is stale, and players' updaters find no manifest (404, harmless).
- macOS app updates: see `docs/prompts/mac-app-updater-handoff.md` (mac agent).
- The updater's console window from a hidden `PLAY BAKERSFIELDQUAKE.exe` launch (AllocConsole) was not seen in a real desktop session.

## 2026-11-19 — macOS DMG job on self-hosted ozzy-2

- Outcome: `macos` job in `.github/workflows/build-zip.yml` now runs on `[self-hosted, macOS, ARM64]` (ozzy-2). Xcode re-pinned to `/Applications/Xcode.app` 26.3 with a version assert; pinned `cmake==3.31.6` wheel (ozzy has no cmake); deps cache key includes the Xcode version. Commit `782e817`, not pushed.
- Verification: actionlint clean. On ozzy, a duplicate codesign identity across two keychains signs without ambiguity. A trial `SKIP_NOTARIZE=1 build_app.sh build-20261119-275c39e` over SSH built SDL2, ogg, vorbis, freetype, jpeg and Zircon with Xcode 26.3; the updater freeze failed there because it used Xcode's Python 3.9 and the SSH session's login keychain, neither of which CI uses.
- Not verified: freeze, signing with the temp keychain, notarization, DMG upload. Needs a manual `workflow_dispatch` after push (the DMG gate ignores workflow changes).
- Follow-up: `setup-python` installs the python.org framework system-wide on ozzy via passwordless sudo.

## 2026-11-19 — `make app` for local macOS builds

- Outcome: root `Makefile`: `make app` builds BAKOQUAKE.app signed but not notarized (newest release with a macOS zip, or `TAG=`) and opens it; `make run` relaunches. It freezes the updater with uv's Python 3.12 (python-build-standalone, macOS 11.0 target), because pyenv's 3.13 targets 27.0 and `build_app.sh` refuses it. AGENTS.md root list and README updated.
- Root cause (ditto `bakersfield.pk3: No such file or directory`): `gh release download` writes straight to the final zip name; my background test build and Rob's `make app` shared `~/build/bakoquake-mac`, and a 45 MB partial of the 1.13 GB zip got reused. `build_app.sh` now downloads into `<tag>.part` and moves the zip into place when complete. Partial zip deleted.
- Verification: `bash -n`, `make -n`. Full local build not rerun after the fix (left for Rob, to avoid another shared-WORK race).
- Follow-up: the `build_app.sh` change alters the DMG gate's input hash, so the next push builds a DMG on ozzy-2: the first real notarization test there.

## 2026-11-19 — macOS job: uv instead of setup-python

- Root cause: `actions/setup-python` sets `AGENT_TOOLSDIRECTORY=/Users/runner/hostedtoolcache` on every Mac (`src/setup-python.ts:98`), so on ozzy-2 it died with `mkdir: /Users/runner: Permission denied`.
- Outcome: the `macos` job gets Python 3.12 from uv (python-build-standalone, macOS 11.0 target, the same as `make app`) and cmake 3.31.6 from a venv in `$RUNNER_TEMP`. This replaces the earlier note: no python.org framework or sudo install on ozzy anymore.
- Verification: actionlint; on ozzy under the runner's PATH, `uv python install 3.12` gives 3.12.11 with deployment target 11.0, and the venv cmake reports 3.31.6. The CI run itself is not verified yet.

## 2026-11-19 — local mac build dir moved to ./build

- Outcome: `WORK` now defaults to `<repo>/build` in both the Makefile and `build_app.sh`, and `/build/` is gitignored. CI is unaffected because it sets `WORK` itself.
- Follow-up: `~/build/bakoquake-mac` is now unused. Its `prefix-13.0` has its absolute path baked in (`sdl2-config`, pkg-config, cmake configs), so the first `make app` rebuilds the libraries in `./build` instead of moving them. The downloaded release zips under `dl/` can be moved to `./build/dl/`.

## 2026-11-19 — `make app` fetches only changed game files

- Outcome: `build_app.sh` keeps the unpacked package in `$WORK/game` as its cache and records the release in `game/.tag`. When that folder holds another release, it runs `tools/bq_update.py` (the players' updater) against `releases/download/<tag>/manifest-macos-arm64.json`, which fetches only the files whose sha256 changed with HTTP Range requests. A follow-up `--check` must report nothing left; otherwise it falls back to the full zip download. The zip is deleted after unpacking. CI starts empty and still downloads the zip.
- Verification: `bash -n`. Synced `build/game` from `1e5859c` to `13e3e44` by hand with the same commands: 1 file fetched, 3.3 s, `--check` exit 0. A full `make app` through the new path has not been run yet.
- Follow-up: a partial `13e3e44` download in `build/dl` (3.3 MB, 05:47) came from neither me nor Rob. Probably another session; deleted.
- Later: when local `main` equals `origin/main`, `make app` passes `NO_ZIP=1`, and `build_app.sh` then only updates the cached game data. It fails instead of downloading the full zip. Override with `make app NO_ZIP=0`. Checked with `bash -n` and `make -n`.

## 2026-11-19 — `make app` builds from the repo, no GitHub

- Outcome: `make app` assembles game data from the repo onto `build/base` (a base package; `make base` downloads it, and `make app` runs that only on a fresh checkout). It uses the new `source/mm_tools/assemble_local_package.sh`, which:
  - clones the base (APFS clone);
  - overlays the repo configs and tools as `build-zip.yml` does;
  - builds `zz_bakovan`, `zz_karts`, `zz_gunnomip`, `zz_minimap` and `zz_pinklady` with numpy 2.5.4 / pillow 13.0.0;
  - builds fteqcc from fte-team/fteqw `c781d13` (2025-09-26) and compiles `progs.dat` (needs `-Wno-F313`) and `menu.dat`. CSQC does not compile with stock fteqcc (`MUL_D`/`CONV_FD` opcodes on `__variant` builtins), so `csprogs.dat` stays the base's.
- `build_app.sh`: `PKG_DIR` bundles an assembled package instead of downloading the release zip, and `NO_DMG=1` stops after the app. This removes the updater-sync and `NO_ZIP` code from `82615b3`/`d05516d`. `make run` launches with `open --env BQ_NO_UPDATE=1`, so the launcher does not patch the build back to the GitHub release.
- Verification:
  - `make build` exit 0; the bundled `progs.dat` is the compiled one (55 Kyle strings).
  - A headless `darkplaces-dedicated` on `+map start` loads it: `program loaded (crc 10838, size 3438K)`, no Host_Error.
  - Kyle models and sprites are missing (`progs/v_kyle.md3` etc. not found): the builder's inputs are on GiggleHacks's machine.
  - `zz_gunnomip` is byte-identical to CI; `zz_bakovan` and `zz_minimap` have identical pixels; `zz_karts` and `zz_pinklady` are off by 1–2 levels in a few PNGs and the kart md3s differ (cause not checked; maybe arm64 vs x86 float math).
  - Not tested in game: menu.dat and gameplay.
- Follow-up: GiggleHacks to commit the Kyle source assets and the builders for zz_johnbird/mmtank/gfuel/conback/tone1, and to say which fteqcc builds the CSQC.
- Later, after GiggleHacks's `004bce2`/`9439f1e`/`5afa94f`: the local build also compiles `csprogs.dat` (header CRC stamped from `quake15/csprogs.dat`: 23147) and builds `zz_kyle.pk3`; `-Wno-F313` is no longer needed. `make build` exit 0; a headless server on `start` loads the progs with no missing Kyle models.

## 2026-11-22 — macOS app: visible terminal, crash log + Safe Mode retry

- Outcome:
  - `source/mac/launcher.sh` reopens itself in a visible iTerm window (AppleScript `create window ... command`;
    Terminal.app via `open -a` when iTerm isn't installed). `BQ_NO_TERMINAL=1` keeps it hidden. In the terminal
    the updater runs with `--no-gui`, and `tools/bq_update.py` now treats `--no-gui --launch` on a tty as interactive
    (text progress, Y/n prompts, DMG download when the app binaries changed).
  - The launcher waits on the engine instead of `exec`. A non-zero exit copies `bq_game.log` to `bq_game_crash.log`
    and offers "Retry in Safe Mode" (`+exec safemode.cfg`). `lanscan.py --pid` now watches the engine PID.
  - Decided: keep the DMG flow for signed-binary updates (no Sparkle, no in-place app swap). Game assets keep
    updating through `manifest-macos-app.json`. The abandoned swap code is in `git stash`.
- Verification: `bash -n`; the AppleScript dialog compiles; the relaunch block was tested in a fake bundle with spaces
  in the path and args (iTerm and Terminal both ran it with `BQ_IN_TERMINAL=1` and the args intact); a frozen
  PyInstaller 6.22.3 build includes Tk; `bq_update.py --no-gui --launch` under a pty works; unit tests pass (24).
  Not run in a signed CI build yet.
- Follow-up: in the next DMG, check the one-time "BAKOQUAKE wants to control iTerm" prompt, the Dock icon with the
  engine as a child process, and that Cmd-Q exits 0 (otherwise the crash dialog shows on every quit).

## 2026-11-25 — v1.76 playtest fixes

- Outcome:
  - Host Game thumbnails: Zircon can't decode JPEG here (no jpeg62 library: `levelshots/*.jpg ... decode failed`), so the
    new CI-built `zz_levelshots.pk3` (`build_levelshots_pk3.py`) carries PNG copies; `menu_ui.qc` prefers `.png` and
    draws a named placeholder card when a shot is missing.
  - Loading screen: every menu clock (`gettime`, any timer argument) is frozen while a map load blocks (Downtown: 12 s,
    ~110 redraws on one timestamp), so the bar sat at 2% and each time jump re-picked the backdrop. Now one backdrop
    per load (a load ends at the first normal `m_draw` frame), progress follows loading redraws plus the wall clock
    (`strftime`), and the elapsed readout is real.
  - Rob Drone HUD (`csqc/robhead_xray.qc`): solid bright through-wall silhouettes with a glow shell; small labels and
    reticle; terminal types the launch's commands, shows the result, then closes; text clipped to its boxes (the
    Linux/macOS packages have no Roboto, so the wide Quake font overflowed; the HUD now detects that); pulsing radar
    contacts; Raspberry Pi board is one picture (`zz_robdrone.pk3`, `build_robdrone_pk3.py`); randomized download/upload
    readout bottom-left with no box; edge markers drawn with fills (drawline dropped them).
  - Drone performance: pilots (bots too) no longer get `EF_DIMLIGHT` (a shadow-casting dlight each); `fd_trail` is
    sparse. Note: a test window that isn't focused is capped by `cl_maxidlefps 20`, which looks exactly like the
    reported 20 FPS; with focus the drone costs ~25% render time here, ~2/3 of it the dlights.
  - Woo Cannon: no flying barbells. RL/GL back in the magazine system (54db503's reload revert undone; its damage and
    fuse values kept). John Bird: plain can, no mist cone, trail or mist clouds. Hit sound: new synthesized metallic
    "tink" (`make_hitsound.py --pk3`, `zz_hitsound.pk3`), pitch rising with damage.
  - Downtown jump pads: `q3pad.qc` lays a Quake 3 style pad (`zz_jumppads.pk3`) on the 28 plain trigger_push pads; SkyPads,
    kart boost pads and ladders untouched.
  - Go-kart cockpit: driver head is its own surface, hidden only for the driver (skin 1); eye at the driver's head,
    tilted 32° so the wheel and both hands show.
- Verification: compiled with fteqcc `c781d13`; each new pk3 built twice with identical sha256 (numpy 2.5.4 / pillow
  13.0.0); in-game screenshots on Linux Zircon (v1.76 install, isolated userdir) of the Host menu, loading log, drone
  HUD, Downtown pads and kart cockpit; RL magazine refills and the launcher stays selected. Not checked in game: Woo
  Cannon blast, John Bird spray, the hit sound by ear (tests ran muted); nothing on Windows/macOS; no CI run.
- Follow-up: `build-zip.yml` builds `zz_bakersfieldish.pk3` with `source/mm_tools/build_bakersfieldish_pk3.py`, which
  is not in the repo; it only works while that cache entry exists. (Resolved: v1.77 added the script.)

## 2026-11-25 — second playtest round, on top of v1.77

- Prompt: playtest notes on weapons, deployables, karts, effects and jump pads (follows the 1.76 round above).
- Outcome:
  - 4Loco bed: a hit on the bed is a hit on the rider (only the 3.2 s spawn protection remains); mouse or A/D steering,
    far more grip, lower top speed, no drift lock, S brakes during surges, taller hitbox.
  - Jump pads (Downtown): all 55 now have models: 28 plain, 16 kart boost pads (`q3kart60/66/72.md3`), 11 SkyPads (blue).
  - Weapons: John Bird cans pop a small mist and clink on contact; Rob drone cruise 320 -> 440 and moved by the clock,
    no electricity in its blast; M4 silencer and suppressed shots (`build_m4_pk3.py`, `zz_m4.pk3`); Woo Cannon splash
    95..191 -> 260..530 (the shooter still takes the old amount); Eric Cannon is mouse-flown, much longer range, and
    shows the blast from outside before the pilot dies.
  - Green Men drive themselves (engine bounce physics parked them on landing) and all of them climb walls.
  - Downtown: two Mega Man tanks, no ambient traffic cars, ten spawn points seat you in a go-kart.
  - Go-kart rockets lock the player near the crosshair and home on them, with a proximity fuse.
  - Merged with v1.77, which removed the Duke Nukem blood altogether, so the planned blood shrink was dropped.
- Verification (Linux Zircon, v1.77 install, isolated userdir, muted, temporary logging build that is not in the repo):
  bed protection/damage/death, drone ~440 u/s, Green Men roaming and climbing, Eric flight and crash view, kart spawns
  (7 of 7 kart-spot picks seated), homing hits on bots, Woo tap-shot kill with shooter unhurt, M4 silencer, hairspray
  mist, pads, tanks, Host menu thumbnails. Not checked: anything by ear, bed handling by feel, Windows/macOS, CI.
- Noticed, not changed (present in v1.77): client `VM_remove` / `setorigin` warnings and "effect number 65535" during
  the ForeLoco; cheat impulses 145/146 (spawn/drink ForeLoco) are taken by `BM_TestImpulses`, and 136-138 (go-kart
  tests) are now also used by Bakersfield-ish.
- Merged onto v1.80: heat-seeker HUD stats moved from 120-123 to 124-127 (Bakersfield-ish uses 120/121). Muted Linux
  smoke runs on the merged build (Downtown, kart spawns and lock-on, bed, drone, Host menu) showed no new warnings.

## 2026-11-26 — macOS updater GUI, Ranger jump frames, DMG on every release

- Outcome:
  - `source/mac/launcher.sh`: dropped `--no-gui` on the launch-time update, so the Mac app uses the same Tk updater
    window as Windows/Linux. The terminal window stays for the engine console.
  - GitHub issue #3: `build_player_deaths.py` fills `player_id1.mdl` frames 243-254 (axjump1-4, jump1-8) from the
    model's run strides (frames 2/3 and 8/9, halfway blends at 244/248). They were stand1 copies, so the classic
    Ranger froze mid-jump.
  - `build-zip.yml`: releases that build no DMG copy the newest one forward, so every release (and
    `releases/latest/download/`) has `BAKOQUAKE-macos-arm64.dmg`. Before this, the only DMG was on v1.66.
- Verification: `bash -n` on the launcher; built `zz_player_deaths.pk3` locally with `--verify-repro` and checked that
  frames 243/247 differ from stand1 and the death frames still start at 288; workflow YAML parses. Not checked: the jump
  in game, the Tk window on a Mac, and the DMG copy step (first runs on the release after next).
- Follow-up: in-game check of the jump (chasecam on `start`), then close #3.

## 2026-11-26 — macOS FPS profile, glMapBufferRange patch into the DMG engine

- Outcome: profiled the installed v1.91 app on an M2 Max (findings in `docs/macos-fps-2026-11-26.md`). The 2026-11-01
  glMapBufferRange patch (never carried over from DarkPlaces) is now engine commit `1641494` in
  BakersfieldQuake/zircon-darkplaces (macOS only via `#ifdef __APPLE__`), and the DMG builds from it.
- Root cause (measured with `sample`): 74% of main-thread time on bakersfielddowntown is spent in `glBufferSubData`.
  Every call submits a Metal command buffer (Apple GL-on-Metal). Second cause: in Zircon, `vid_samples 4` also renders
  the view at 2x per axis (gl_rmain.c:5647). On downtown at 1440p that is 42 fps with it and 104-111 fps with
  `vid_samples 1`.
- Changed: `source/mac/build_app.sh`: `ZIRCON_REPO` is BakersfieldQuake/zircon-darkplaces, `ZIRCON_REF` is `1641494`,
  and `origin` of a cached clone is re-pointed.
- Verification: `clang -fsyntax-only` passes on gl_backend.c and vid_shared.c, `bash -n` passes on build_app.sh. Not run: the engine build (CI only) and any benchmark
  of the patched engine.
- Follow-up: benchmark the CI DMG (`timedemo intro.dem`, downtown `timerefresh`). Decide on `vid_samples` in the
  picker's normal preset. `BAKOQUAKE-macos-arm64.zip` still ships the unpatched Zircon release binary. Engine repo
  BakersfieldQuake/zircon-darkplaces `main` was fast-forwarded to 1641494 (GiggleHacks commits had nothing more to
  merge); release `v20261127` there has Linux/macOS from CI run 45947270060 and the unchanged v20261122 Windows
  self-pack (CI's Windows exe is not self-packed). `ENGINE_REPO` in build-zip.yml now points there.

## 2026-11-27 — QC build fails on macOS (F313 / MUL_D)

- Outcome: `make build` compiles the QC again on ozzy/mimi. `sin`, `cos`, `sqrt` and `clienttype` now have real
  prototypes instead of decompiler `__variant(...)` ones in `defs_custom.qc`, `dpextensions.qc` and
  `csqc/csqc.csprogsdefs.qc`.
- Root cause: the arm64 macOS build of fteqcc `c781d13` mistypes a `__variant(...)` builtin's return value when it is
  used in arithmetic (`1.2 * sin(x)` gives itof emulation, warning F313, an error by default; `sin(x) * 1.2` gives
  double opcodes). Linux and Windows fteqcc accept it. New code from 2026-11-26/27 (netsend.qc, cyrax.qc, client.qc,
  bm_minimap_hud.qc) first used these builtins that way. `defs_custom.qc` declares the variant `sin` before
  `megaman_defs.qc` declares the float one, so the variant one won.
- Verification: SSQC, CSQC and menu compile with the mac fteqcc (0 errors; warning counts unchanged in kind).
  Reproduced the bug in a 7-line test file. Not run: a full `make build`, an in-game test, or a Linux/Windows compile
  of the changed defs.
- Also: `make build` on Linux (chonk). `assemble_local_package.sh` used macOS-only `cp -Rc`, `sysctl` and `CC=clang`
  (chonk has no clang). It now uses `cp -R --reflink=auto` off macOS, `getconf _NPROCESSORS_ONLN` and `CC=cc`. The
  Makefile runs `build_app.sh` only on Darwin, so on Linux `make build` stops at the assembled `build/pkg`. Checked
  with `bash -n` and `make -n`; not run on chonk.
- Also: the updater offered the older v1.107 DMG to an app built from current `main`. The release's
  `manifest-macos-app.json` keeps the newest finished DMG's `mac_inputs` until the `macos` job patches it, and runs
  110-112 never got there (110 failed, 111 and 112 were cancelled by the next push). The manifest now also carries
  `app_inputs` (this release's commit), and `bq_update.py` skips the DMG when the installed app matches it. Changed
  `tools/bq_update.py`, `source/ci/make_manifest.py`, `build-zip.yml`, plus a test in `source/ci/tests/test_bq_update.py`
  (fails without the fix). 27/27 updater tests pass. Changing `bq_update.py` changes the app inputs, so the next
  release builds a new DMG.
  A local build ahead of every release (unpushed commits) still matched neither hash, so `launcher.sh` and
  `update_launcher.sh` no longer pass `--bundle-mac-inputs` when the app's `release-tag` is `local-*`: local builds
  skip the DMG check (game data still updates). Checked with `bash -n`; not run from a rebuilt app.
- Also: `BQ_NO_UPDATE=1` (`make run`) never reached the updater. `launcher.sh` reopens itself in iTerm/Terminal
  through a `.command` file, which starts a fresh environment and carried only `BQ_IN_TERMINAL`. It now writes every
  `BQ_*` variable into that file. Checked the generated file under `env -i /bin/bash`; not run from a rebuilt app.
- Also: a local build couldn't load GiggleHacks' server ("Download rejected ... is in an archive" for
  `zz_netsend_sentry`, `zz_player_deaths`, `zz_hats` and `zz_bakersfieldish`). `build/base` dated from Nov 19, and
  `assemble_local_package.sh` built only 16 of CI's overlays. It now builds the other 9 and fetches the pinned
  `zz_netsend_disk`/`zz_hats` (the list is copied from `build-zip.yml` by hand). Built pk3s are cached in
  `build/pk3cache` under one key: repo files outside QC/docs/CI/mac, base pk3s and levelshots, pins and arguments.
  Two assemble runs: 194 s cold, 3.4 s cached, 28 overlays in the package each time. Not checked: that changing an
  asset triggers a rebuild, and loading the server with the rebuilt app.
- Karts build profile (cProfile, 103 s): PNG `optimize=True` 34 s, pure-Python `md3lib.write` 29 s plus 8.5 s
  read-back, geometry ~30 s. Each kart is 64 frames × 10-16k vertices (5.8-8.4 MB MD3), so `zz_karts.pk3` is 43 MB.
- Also: `build/base` never updated after its first download, so local apps missed maps added since (practice,
  bakersfieldish) and `zz_console.pk3`. `make build` now runs `tools/bq_update.py --root build/base/BAKOQUAKE` first:
  52 s / 235 MB the first time (build 0 to v1.116), 0.9 s when up to date. 15 maps CI drops (aerowalk, fox, ...) are
  still in the old base as strays.

## 2026-11-27 — aarch64 engine for orangepi4, arch-aware updater

- Built Zircon `1641494` (same commit as engine release v20261127) for aarch64 in an arm64 `ubuntu:24.04` container
  on the Mac, with the engine CI's deps and `make DP_LINK_JPEG=dlopen sdl-release sv-release`. The binaries need
  glibc 2.38; the Pi has 2.43. They are installed in orangepi4 `~/BakersfieldQuake/build/base/BAKOQUAKE/`, with the old
  x86 binaries kept as `*.x86_64`. The dedicated server loads progs on the Pi. The SDL client was not run.
- Root cause of the junk zero-byte file in that folder: `Start-Server.sh` started the x86 `darkplaces-dedicated` with
  `nohup`. On ENOEXEC, `execvp()` falls back to `/bin/sh`, which parsed the ELF as a script and one line read as a
  redirect. The launcher now uses bash's own `exec` in a subshell. On the Pi it gives "cannot execute binary file"
  and rc 126, and no stray file appears; `nohup` reproduces the junk file.
- `tools/bq_update.py`: when the package's platform arch (`linux-x86_64`) isn't the machine's (`aarch64`), the
  updater skips the manifest's executables (non-script `exec` entries), so it no longer replaces a natively built
  engine with the x86 one. Windows is unaffected. New test (fails without the fix); 28/28 updater tests pass.
- `Makefile`: the base zip and the updater platform are `<os>-<uname -m>` (`BAKOQUAKE-linux-aarch64.zip` on the Pi).
- Follow-up: no `linux-aarch64` zip or manifest is published yet, so `make base` / `make build` on the Pi fail with
  "no release with BAKOQUAKE-linux-aarch64.zip" (or a manifest 404) until CI builds one. The engine repo releases only
  linux-x86_64.
