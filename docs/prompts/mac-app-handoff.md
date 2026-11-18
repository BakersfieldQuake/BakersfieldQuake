# Handoff: signed macOS BAKOQUAKE.app + DMG (build on mimi)

**For:** the agent running on `mimi` (macOS 27, Apple Silicon, Xcode installed, Rob's Developer ID in the keychain).
**Repo:** `GiggleHacks/BakersfieldQuake` (public). Read `AGENTS.md` first.
**Rules:** no Claude session URLs or `Claude-Session:` trailers in commits; one logical change per commit. Linux
shortcuts and Windows shortcuts are being done on another machine, so don't touch `launchers/*.cmd` or the
Linux `.desktop` work.

## Goal

A drag-to-install `BAKOQUAKE.dmg` that holds `BAKOQUAKE.app` and an `Applications` symlink. The app is signed with
Rob's Developer ID, uses the hardened runtime, and is notarized and stapled. It must open on a clean Mac with no
Homebrew and no Gatekeeper workaround. Deliver it as a **repeatable script** committed to the repo
(`source/mac/build_app.sh`), not a one-off.

## Inputs

- **Game data:** `BAKOQUAKE-macos-arm64.zip` from the newest release, currently draft
  `build-20261118-b164f68-draft`. Use `gh release download <tag> -R GiggleHacks/BakersfieldQuake -p 'BAKOQUAKE-macos-arm64.zip'`.
  The zip's root is `BAKOQUAKE/` and contains:
  - `BakersfieldQuake/`, `quake15/`, `tools/`, `Play.sh`, `Start-Server.sh`
  - `darkplaces-sdl` and `darkplaces-dedicated`: the Zircon engine. CI builds them in `rgr4y/zircon-darkplaces`,
    linked against Homebrew paths.
  - **No `id1` paks.** They're copyrighted; each player supplies their own.
- **Icon:** `source/icons/bakoquake-256.png`. 256 px is the largest size that exists. Upscale it for the 512 px and
  1024 px `.icns` slots for now, and note it as a follow-up for better art.
- **Engine:** prefer rebuilding Zircon natively on mimi from `github.com/rgr4y/zircon-darkplaces`
  (`make -f makefile SDLCONFIG_STATICLIBS="$(sdl2-config --libs)" sdl-release sv-release`; outputs
  `zircon_beta_linux_sdl` and `zircon_beta_linux_dedicated_server`, which are macOS binaries despite the name).
  That way you control what gets linked. The prebuilt CI binary also works as a fallback.

## App layout

```
BAKOQUAKE.app/Contents/
  Info.plist
  MacOS/BAKOQUAKE                 launcher (see below), the CFBundleExecutable
  MacOS/darkplaces-sdl            engine client
  MacOS/darkplaces-dedicated      engine server (optional for v1)
  Frameworks/                     bundled dylibs (see Libraries)
  Resources/bakoquake.icns
  Resources/game/                 -basedir: BakersfieldQuake/, quake15/, tools/, empty id1/
```

`Info.plist` keys:
- `CFBundleIdentifier` `com.gigglehacks.bakoquake`
- `CFBundleName`/`CFBundleDisplayName` `BAKOQUAKE`
- `CFBundleExecutable` `BAKOQUAKE`
- `CFBundleIconFile` `bakoquake`
- `CFBundlePackageType` `APPL`
- `CFBundleShortVersionString`: the release tag date
- `LSMinimumSystemVersion` 13.0
- `NSHighResolutionCapable` true
- `LSApplicationCategoryType` `public.app-category.action-games`

## Writable data lives outside the bundle (verified)

Everything the game writes goes to `~/Library/Application Support/BAKOQUAKE/`, passed as `-userdir`. That covers
`config.cfg`, `lan_server.cfg`, screenshots, and the player's `id1/pak0.pak` + `pak1.pak`. The bundle stays
read-only, so the signature stays valid.

Verified in Zircon `fs.c`:
- `FS_AddGameHierarchy` adds every gamedir from `basedir` and then from `userdir`, and the userdir copy has
  higher priority. So `userdir/id1/pak0.pak` is found, and a saved `userdir/BakersfieldQuake/config.cfg` beats the
  seed `config.cfg` in the bundle.
- `-userdir` appends a trailing `/` itself (`fs.c` around line 2480).

## Launcher (`Contents/MacOS/BAKOQUAKE`)

A shell script is fine for v1. If notarization or `spctl` objects to a script main executable, switch to a tiny C
launcher that does the same and `execv`s the engine. The script must:

1. Work out `APP=…/Contents`, `GAME=$APP/Resources/game` and `USERDIR=~/Library/Application Support/BAKOQUAKE`,
   then `mkdir -p "$USERDIR/id1"`.
2. If `$USERDIR/id1/pak0.pak` is missing, run the existing finder:
   `. "$GAME/tools/find-quake-paks.sh" && bq_install_paks "$USERDIR"`. It searches Steam (including extra
   libraries in `libraryfolders.vdf`), the usual folders and `~/Downloads`, and requires pak0 and pak1 together.
   If that fails, use `osascript` to show a "choose folder" dialog ("Locate your Quake id1 folder"), check that
   pak0 and pak1 are there, and copy them. If it still fails, show `display alert` and exit. There's no terminal,
   so all messages go through dialogs.
3. First run with no saved config, or a config that still contains `BAKERSFIELD_SEED`: add
   `+_cl_name "$USER" +_cl_color <random>`, the same as `Play.sh`.
4. **Skip the LAN autoscan** (`tools/lanscan.py`) unless real Python exists. `python3` on macOS is a stub that pops
   an Xcode CLT install dialog. Only run it if `xcode-select -p` succeeds.
5. `exec "$APP/MacOS/darkplaces-sdl" -basedir "$GAME" -userdir "$USERDIR" -game quake15 -game BakersfieldQuake …`
   Use `exec`, so the Dock shows one app.

## Libraries

The client links SDL2 directly and `dlopen()`s the rest **by bare filename**. Names verified in Zircon source:

| Need | Name the engine dlopens | Source |
|---|---|---|
| SDL2 | linked (`/opt/homebrew/.../libSDL2-2.0.0.dylib`) | brew `sdl2-compat` on mimi is SDL2-on-SDL3, so **also bundle `libSDL3*.dylib`** |
| JPEG textures | **`libjpeg.62.dylib` only** (`jpeg.c:513`) | **Not brew.** Brew `jpeg-turbo` builds the jpeg8 API (`libjpeg.8`), and the engine calls `jpeg_CreateDecompress` with version 62, so it would fail. Build libjpeg-turbo from source with default CMake options (jpeg6b API, produces `libjpeg.62.dylib`). |
| fonts | `libfreetype.6.dylib` | brew `freetype` (plus its deps: libpng, bzip2…) |
| ogg/vorbis audio | `libvorbis.dylib`, `libvorbisfile.dylib`, `libogg.dylib` | brew `libvorbis`/`libogg` (bundle under exactly these names) |
| curl | `libcurl.4.dylib` | system `/usr/lib`; don't bundle |
| zlib | `libz.dylib` | system; don't bundle |
| PNG | none | built in (lodepng). The `DYLD_FALLBACK_LIBRARY_PATH` line in `Play.sh` mentions libpng, which is stale for Zircon. |

Rewrite install names so nothing points at `/opt/homebrew`: use `dylibbundler`, or `install_name_tool` plus
`@executable_path/../Frameworks/`. Check with `otool -L` on every Mach-O in the bundle.

**Bare-name dlopen under the hardened runtime:** the hardened runtime ignores `DYLD_*` environment variables, so
setting `DYLD_FALLBACK_LIBRARY_PATH` in the launcher won't find the bundled libs unless the engine is signed with
the `com.apple.security.cs.allow-dyld-environment-variables` entitlement. Try that entitlement first; notarization
permits it. Verify by launching the signed, quarantined app and checking the console. "JPEG library not found" and
missing-texture spam mean it didn't work. Library validation passes as long as every bundled dylib is signed
with the same Team ID. The fallback is a small engine patch in `rgr4y/zircon-darkplaces` (Sys_LoadLibrary tries
`@executable_path/../Frameworks/<name>` first); raise that rather than doing it silently.

## Signing, notarizing, DMG

1. Sign inside out, with `--options runtime --timestamp` and Rob's "Developer ID Application" identity:
   every `Frameworks/*.dylib`, then the two engine binaries (with the entitlements plist), then the launcher, then
   the `.app`. Don't use `--deep` for the final pass; sign each nested item explicitly.
2. `ditto -c -k --keepParent BAKOQUAKE.app app.zip`, then
   `xcrun notarytool submit app.zip --keychain-profile <profile> --wait`. Ask Rob for the profile name, or have
   him create one with `xcrun notarytool store-credentials`.
3. `xcrun stapler staple BAKOQUAKE.app`.
4. DMG: a folder holding `BAKOQUAKE.app` plus `ln -s /Applications Applications`, built with `hdiutil create -fs APFS -format ULFO`
   (most of the data is already-compressed pk3, so heavier compression only costs time). Sign the DMG, notarize
   it, and staple it as well.
5. Upload: `gh release upload <tag> BAKOQUAKE-macos-arm64.dmg -R GiggleHacks/BakersfieldQuake`.

## Verify before calling it done

- `codesign --verify --deep --strict --verbose=2 BAKOQUAKE.app`, and `spctl -a -vvv -t exec BAKOQUAKE.app`
  reports "Notarized Developer ID".
- `otool -L` across the bundle shows no `/opt/homebrew` or `/usr/local` paths.
- Simulate a clean machine: copy the DMG and add quarantine
  (`xattr -w com.apple.quarantine "0081;$(printf %x $(date +%s));Safari;" BAKOQUAKE-macos-arm64.dmg`), mount it,
  drag the app to /Applications, and open it. Gatekeeper must not complain.
- Temporarily hide Homebrew from the engine, for example by running from a user account without it, to prove the
  libs come from the bundle.
- In game: no "Model … not found" for content in this package. Note that the live server may be newer than the
  package, for example `progs/jb_*.md3`; that's a separate content issue, not a packaging bug. JPEG textures load,
  sound plays, and the pak finder works from `~/Downloads`.
- Moving the app after first run still works, because all state is in Application Support.

## Known gaps, out of scope here

- The future auto-updater (`docs/auto-update-plan.md`) can't write into a signed bundle. The plan for macOS will be
  to keep game data in Application Support and update it there. Don't design for that now, but don't hard-code
  anything that blocks it.
- CI notarization needs secrets (a cert .p12 and a notary API key). Keep `build_app.sh` runnable locally; CI wiring
  comes later.
- **Disk:** `df` on mimi reports about 25 GB free. Finder shows about 293 GB because it counts purgeable space,
  which macOS frees on demand. A build needs about 4 GB (zip, extracted tree, app, DMG), so either figure is
  enough. Clean up the temporary files afterwards.
