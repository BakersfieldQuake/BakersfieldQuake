# BAKOQUAKE Auto-Updater v2: Design & VPS Setup

Status: Implementing v2 (strict online update enforcement, GitHub -> VPS failover, dark-theme GUI with live speed & ETA, zero-missing-assets verification, macOS DMG auto-prompt, and standalone **Update** launchers/shortcuts on Windows, macOS, and Linux).

Builds on v1 (`docs/auto-update-plan.md`).

---

## Goals & Guarantees

1. **No outdated online play:** Whenever the player launches the game (`Play` or `Start Server`) and has internet access, the updater verifies the install against the newest release. If an update or repair is needed, the player sees **Update** and **Exit** — declining or closing exits cleanly without starting the game or server.
2. **Offline LAN resilience:** If **both** GitHub and the VPS fallback are unreachable (e.g. an offline LAN party), `--launch` exits `0` so the installed game starts normally. (`BQ_NO_UPDATE=1` remains available as an explicit dev/LAN skip flag.)
3. **Zero missing assets (models, sounds, maps, pk3s, engine):** `tools/bq_update.py` never short-circuits on `build == installed` alone. On every launch it `stat()`s every managed file in `manifest-<platform>.json` (<5 ms across ~110 files). Any missing, truncated, or unexpectedly modified file (`.pk3`, `.bsp`, `.dat`, configs, engine) is automatically flagged and repaired.
4. **GitHub primary + deduplicated VPS fallback:**
   - **Manifest check:** Fetches `https://github.com/BakersfieldQuake/BakersfieldQuake/releases/latest/download/manifest-<platform>.json` first (`4s` timeout); if unavailable, fails over to `https://bakersfield.larrywew.fun/updates/manifest-<platform>.json` (`5s` timeout).
   - **File downloads:** When GitHub is primary, pulls only changed/missing files straight out of the GitHub release zip via HTTP `Range` requests. If GitHub fails or drops mid-transfer, automatically fails over per-file to `https://bakersfield.larrywew.fun/updates/files/<sha256>`. Every downloaded file is verified by exact byte size and SHA-256 before staging/replacement.
5. **macOS DMG / Engine updates:** `manifest-macos-app.json` carries `mac_inputs`, `dmg_url`, `dmg_vps_url`, `dmg_size`, and `dmg_sha256`. Normal mod updates patch the APFS clone in `~/Library/Application Support/BAKOQUAKE/game` seamlessly. When a release bumps `mac_inputs` (new engine/launcher), the updater prompts **New BAKOQUAKE App Required**, downloads and SHA-256-verifies `BAKOQUAKE-macos-arm64.dmg` into `~/Downloads/` (with speed & ETA and VPS fallback), opens it in Finder, tells the user to drag both apps into `Applications`, and exits `4` so the old engine doesn't run.
6. **Seamless UI with live Speed & ETA:**
   - `--launch`: stays invisible during fast (<1.5s) up-to-date/offline checks. Shows `"Checking for updates..."` only if the network check exceeds 1.5s, or opens immediately when an update/repair is needed (old -> new version, file count, MB, short *"What's new"* notes, **Update** / **Exit**). During download, shows determinate `%`, `downloaded / total`, EWMA-smoothed speed (`MB/s` / `KB/s`), ETA (`~12s remaining`), current file, and active source (`GitHub` or `VPS fallback`).
   - `--standalone`: opens immediately, checks GitHub/VPS, and acts as a pure updater (never auto-launches the game). When up to date, shows version + verified file count with **Close** and **Verify & Repair All Files** (full SHA-256 scan).

---

## Exit Codes

| Code | Meaning | Launcher behavior |
|---:|---|---|
| `0` | Up to date (all managed files verified) or genuinely offline during `--launch` | Start engine / server |
| `3` | Files updated or repaired cleanly (`--launch` / CLI) | Re-exec launcher script, then start engine / server |
| `4` | Outdated / repair needed and user exited, update failed after prompt, or macOS DMG update required | Exit cleanly — do **not** start engine / server |
| `10` | `--check` mode only: update or repair is available | Print summary |

*(In `--standalone` mode, closing after `"Up to date"` or `"Updated!"` returns `0`.)*

---

## Standalone "Update" Entry Points

- **Windows:** Dedicated `Update.exe` directly in the `BAKOQUAKE/` package root (PyInstaller freeze of `tools/bq_update.py` with dedicated green sync icon `source/icons/bakoquake-update.ico`, `--noconsole`). Double-clicking runs `--standalone` automatically; `Play.cmd` / `Start Server.cmd` call `Update.exe --launch`. `tools/install-shortcuts.ps1` adds **Update BAKOQUAKE** (using `bakoquake-update.ico`) to Start Menu (`Programs\BAKOQUAKE`) and Desktop.
- **Linux:** Root `launchers/Update.sh` running `python3 "$ROOT/tools/bq_update.py" --standalone --root "$ROOT"`. `tools/install-shortcuts.sh` installs `bakoquake-update.desktop` (with `bakoquake-update-256.png`) to `~/.local/share/applications/` and the Desktop.
- **macOS:** Signed & notarized `Update BAKOQUAKE.app` (with dedicated `bakoquake-update.icns`) right next to `BAKOQUAKE.app` inside `BAKOQUAKE-macos-arm64.dmg` (`source/mac/update_launcher.sh` -> invokes `BAKOQUAKE.app/Contents/MacOS/bq-update --standalone`).

*(Shortcut migration marker in Windows `Play.cmd` / `Start Server.cmd` and Linux `install-shortcuts.sh` is bumped to `v2|<ROOT>` so existing installs receive the new **Update BAKOQUAKE** shortcuts automatically on their first launch after updating.)*

---

## VPS Fallback Architecture (`/srv/bq-updates/`)

Instead of duplicating three ~1.2 GB platform zips (~3.6 GB), the VPS stores content-addressed blobs shared across Windows, Linux, and macOS (~1.3 GB total):

```text
/srv/bq-updates/
├── manifest-windows-x64.json       # Cache-Control: no-cache
├── manifest-linux-x86_64.json
├── manifest-macos-arm64.json
├── manifest-macos-app.json
├── BAKOQUAKE-macos-arm64.dmg       # Latest signed DMG
├── .keep_hashes.json               # Hashes referenced by latest 2 releases
└── files/
    └── <sha256>                    # Immutable blob shared across all OSes
```

`source/ci/sync_vps.py` runs at the end of non-draft `build-zip.yml` runs (and after the `macos` DMG job finishes). It uploads only missing `<sha256>` blobs in a single `tar` stream over SSH, atomically swaps `manifest-*.json` last, and prunes orphaned blobs not used by the newest 2 releases.

---

## One-Time VPS Setup Instructions

Run the following on the VPS (`bakersfield.larrywew.fun`) to create the update directory, restricted SSH sync account, and nginx endpoint.

### 1. Create `/srv/bq-updates` and the `bqsync` SSH user

```bash
sudo adduser --system --group --home /srv/bq-updates --shell /bin/sh bqsync
sudo mkdir -p /srv/bq-updates/files /srv/bq-updates/.incoming /srv/bq-updates/.ssh
sudo chown -R bqsync:bqsync /srv/bq-updates
sudo chmod 755 /srv/bq-updates /srv/bq-updates/files
sudo chmod 700 /srv/bq-updates/.ssh
```

Generate a dedicated Ed25519 deploy keypair on your admin box (with no passphrase):

```bash
ssh-keygen -t ed25519 -C "bakoquake-ci-vps-sync" -f bqsync_ed25519 -N ""
```

Install the **public** key (`bqsync_ed25519.pub`) on the VPS:

```bash
sudo tee /srv/bq-updates/.ssh/authorized_keys >/dev/null <<'EOF'
no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... bakoquake-ci-vps-sync
EOF
sudo chown bqsync:bqsync /srv/bq-updates/.ssh/authorized_keys
sudo chmod 600 /srv/bq-updates/.ssh/authorized_keys
```

### 2. Configure nginx (`https://bakersfield.larrywew.fun/updates/`)

Add these blocks inside the `bakersfield.larrywew.fun` `server { ... }` block:

```nginx
    # Content-addressed updater blobs (immutable by sha256)
    location ^~ /updates/files/ {
        alias /srv/bq-updates/files/;
        default_type application/octet-stream;
        add_header Cache-Control "public, max-age=31536000, immutable";
        autoindex off;
    }

    # Updater manifests & macOS DMG (always revalidate)
    location ^~ /updates/ {
        alias /srv/bq-updates/;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        autoindex off;
    }
```

Ensure `client_max_body_size` isn't restricting anything (not needed for GETs) and reload nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Verify from anywhere once deployed:

```bash
curl -I https://bakersfield.larrywew.fun/updates/manifest-windows-x64.json
```

### 3. Add GitHub Repository Secrets

In GitHub: **Repo Settings -> Secrets and variables -> Actions -> New repository secret**:

| Secret name | Value |
|---|---|
| `VPS_SYNC_HOST` | `bakersfield.larrywew.fun` (or VPS IP `72.62.241.93`) |
| `VPS_SYNC_USER` | `bqsync` |
| `VPS_SYNC_KEY` | Full contents of private key `bqsync_ed25519` |
| `VPS_SYNC_DIR` *(optional)* | `/srv/bq-updates` (default if omitted) |
| `VPS_SYNC_PORT` *(optional)* | `22` (default if omitted) |

*(If `VPS_SYNC_HOST` is not set yet, `sync_vps.py` logs a notice and exits `0` so CI releases still succeed while you finish VPS setup.)*
