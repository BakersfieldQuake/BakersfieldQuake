# Handoff Prompt: Update Existing BAKOQUAKE Install on Another Laptop (Differential Only)

Copy and paste the prompt below to the AI agent on your other laptop:

```text
I already have BAKOQUAKE installed on this machine — DO NOT re-download the ~1.2 GB full zip. Update my existing install in-place using BAKOQUAKE's differential updater so it only downloads files that changed or are missing (keeping my existing ~920 MB base pk3s, id1/pak0.pak, id1/pak1.pak, BakersfieldQuake/config.cfg, demos, and screenshots untouched).

Repo & update endpoints:
- GitHub repo: BakersfieldQuake/BakersfieldQuake
- Primary manifests: https://github.com/BakersfieldQuake/BakersfieldQuake/releases/latest/download/manifest-<platform>.json
- VPS fallback base: https://bakersfield.larrywew.fun/updates/
- Platforms: windows-x64 | linux-x86_64 | macos-arm64 | macos-app

Steps to follow:
1. Find my existing BAKOQUAKE folder on this machine (check Desktop, Downloads, C:\Games, ~/Games, or on macOS /Applications/BAKOQUAKE.app whose game data clone lives at "~/Library/Application Support/BAKOQUAKE/game"). Confirm BakersfieldQuake/bakersfield.pk3 and quake15/q15.pk3 exist there so we don't accidentally do a full download into an empty folder.

2. Check which updater is currently installed:
   - Windows: "<ROOT>\tools\bq-update.exe" --version (or check "<ROOT>\tools\bq_update.py").
   - Linux / Python available: python3 "<ROOT>/tools/bq_update.py" --version.
   - If the installed updater is still v1 (or missing), grab ONLY the updater script from main first:
     https://raw.githubusercontent.com/BakersfieldQuake/BakersfieldQuake/main/tools/bq_update.py
     (If you're on Windows without Python, you can instead run the existing "<ROOT>\tools\bq-update.exe" --root "<ROOT>" first — it will fetch only the changed files from the latest GitHub release, including the new bq-update.exe, Update.exe, and updated launchers.)

3. Run the differential updater in-place against <ROOT>:
   - Windows/Linux (with Python 3):
     python3 "<ROOT>/tools/bq_update.py" --root "<ROOT>" --no-gui
     (If GitHub fails/throttles, pass --manifest-url https://bakersfield.larrywew.fun/updates/manifest-<platform>.json.)
   - Windows (no Python, using frozen exe):
     "<ROOT>\tools\bq-update.exe" --root "<ROOT>" --no-gui
     (Note: exit code 3 means files were updated cleanly; exit code 0 means already up to date. Wait for self-replacement if bq-update.exe itself was updated, then run once more with --check.)
   - macOS (.app):
     Run /Applications/BAKOQUAKE.app (or `Update BAKOQUAKE.app` once installed). If a new engine/DMG is required, the v2 updater will prompt to download and open the DMG; otherwise it patches "~/Library/Application Support/BAKOQUAKE/game" in-place using manifest-macos-app.json. If running from CLI before the new DMG is installed, pass:
     --root "$HOME/Library/Application Support/BAKOQUAKE/game" --platform macos-app --no-gui

4. Refresh shortcuts so the standalone "Update BAKOQUAKE" icon is created:
   - Windows: powershell -NoProfile -ExecutionPolicy Bypass -File "<ROOT>\tools\install-shortcuts.ps1" -Root "<ROOT>"
   - Linux: bash "<ROOT>/tools/install-shortcuts.sh" "<ROOT>"

5. Verify nothing is missing or outdated:
   Run the updater with `--check --root "<ROOT>"` and confirm it reports "up to date (... files verified)" with exit code 0. Summarize what files were downloaded and their total size.
```
