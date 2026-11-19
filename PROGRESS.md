
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
