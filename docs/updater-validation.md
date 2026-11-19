# Updater validation checklist

The macOS app updater, plus the Windows and Linux updater and the shortcuts, which haven't run through CI yet.

## Before testing (Claude, with Rob's OK)

- [ ] Squash the local work into logical commits:
  - the macOS app updater
  - the CI timeouts and `make_manifest --only`
- [ ] Push `main` (3 commits already waiting, plus these).
- [ ] Run **Build A**:
  ```
  gh workflow run build-zip.yml -R BakersfieldQuake/BakersfieldQuake -f base_tag=base-v1.10 -f draft=true
  ```
- [ ] All three jobs (`updater`, `build`, `macos`) are green.
- [ ] The release has 4 manifests, including `manifest-macos-app.json`.
- [ ] `manifest-macos-app.json` lists only `BakersfieldQuake/`, `quake15/` and `tools/`.

## 1. Build A: the app itself (mimi, by hand)

Download the DMG from the draft release in a browser, so it gets quarantined like a player's download.

- [ ] Opening the DMG shows no Gatekeeper warning.
- [ ] Drag the app to /Applications. The first launch shows no "damaged" or "unidentified developer" dialog.
- [ ] Signature and notarization pass:
  ```
  spctl -a -vvv -t exec /Applications/BAKOQUAKE.app
  ```
  Expect "accepted" and "Notarized Developer ID".
- [ ] The updater is signed, and its embedded libraries load under the hardened runtime. Check
  `codesign -dv /Applications/BAKOQUAKE.app/Contents/MacOS/bq-update`, then run it with `--help` and expect exit 0, not 137.
- [ ] The game starts and finds the paks (from Steam, GOG or Downloads, or via the folder picker).
- [ ] A clone exists at `~/Library/Application Support/BAKOQUAKE/game/`:
  - `.bq/bundle-tag` holds Build A's tag;
  - `df` shows no ~1.2 GB drop.
- [ ] `game/.bq/update.log` shows an update check: a 404 is expected while Latest has no manifests, and nothing is downloaded.
- [ ] Launching from the mounted DMG (without copying the app) runs from the bundle and makes no clone.

## 2. Promote Build A to Latest

```
gh release edit <tag A> -R BakersfieldQuake/BakersfieldQuake --draft=false --latest
```

- [ ] Relaunching the app does not download anything.
- [ ] `.bq/state.json` holds Build A's build number.

## 3. Build B: a real update on every platform

1. Commit a small visible change, for example a line in `default.cfg`.
2. Remove one file, for example a `bm_up_*.cfg`, to test deletion.
3. Run the same workflow with `draft=false`, so Build B becomes Latest.

**macOS (the app from Build A):**
- [ ] The app shows a notification "Updating BAKOQUAKE ... N files (X MB)", then "BAKOQUAKE updated".
- [ ] Only the changed files are downloaded; `update.log` and the file mtimes in the clone show it.
- [ ] The changed cfg is in the clone and the game uses it.
- [ ] The removed file is gone from the clone.
- [ ] The next launch is quiet: up to date, manifest request only.

**Windows (the win11 VM, Build A zip):**
- [ ] `PLAY BAKERSFIELDQUAKE.exe` opens a console showing progress, then the game starts.
- [ ] `config.cfg` and the `id1` paks are untouched.
- [ ] The Start Menu and Desktop shortcuts exist and launch the game.

**Linux (chonk, Build A zip):**
- [ ] `./Play.sh` updates, then starts the game.
- [ ] The `.desktop` entries appear in the app menu and launch the game.

## 4. Build C: a new DMG replaces the clone

Use any later build.

- [ ] Install the new DMG over the old app. On the first launch, `.bq/bundle-tag` changes and the clone is rebuilt.
- [ ] Your settings in `App Support/BAKOQUAKE/BakersfieldQuake/config.cfg` survive.

## Known limits

- A new engine, dylib or launcher on macOS still needs a new DMG. The updater only changes game data.
- The app shows two notifications and no progress bar. A large pk3 change (about 500 MB) means a silent wait before
  the game starts.
- `bq_update.py` is unchanged, so Windows players won't re-download `bq-update.exe`.
