#!/bin/bash
# BAKOQUAKE.app main executable (Contents/MacOS/BAKOQUAKE). Installed by source/mac/build_app.sh.
# Updates the game data, finds the player's Quake paks, then execs the engine. Everything the game writes goes to
# ~/Library/Application Support/BAKOQUAKE (-userdir), so the signed bundle stays read-only.
# There is no terminal, so every message goes through a dialog or a notification.
set -u

APP="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE_GAME="$APP/Resources/game"
GAME="$BUNDLE_GAME"
USERDIR="$HOME/Library/Application Support/BAKOQUAKE"
mkdir -p "$USERDIR/id1"

alert() {   # alert <title> <message>
    osascript - "$1" "$2" <<'EOF' >/dev/null 2>&1
on run argv
    display alert (item 1 of argv) message (item 2 of argv) as critical
end run
EOF
}

# 0. Game data updates. The signed bundle can't change, so the game runs from a clone of the bundle's game data in
#    $USERDIR/game, and the updater (Contents/MacOS/bq-update: tools/bq_update.py, frozen) patches that clone with
#    the files that changed in the latest release (manifest-macos-app.json). An APFS clone shares the bundle's
#    blocks: it is instant and takes no disk until a file is replaced. A new DMG (new release-tag) gets a fresh clone.
#    On another volume than the bundle (run from the DMG, App Translocation, an external drive) a clone would be a
#    1.2 GB copy, so the game runs from the bundle without updates. If a new DMG is required, the updater downloads
#    and opens it and exits 4 so the old engine does not launch.
#    BQ_NO_UPDATE=1 skips the update check; BQ_MANIFEST_URL / BQ_FALLBACK_URL override endpoints for testing.
DATA="$USERDIR/game"
TAG="$(cat "$APP/Resources/release-tag" 2>/dev/null)"
if [ -n "$TAG" ] && [ "$(stat -f %d "$BUNDLE_GAME")" = "$(stat -f %d "$USERDIR")" ]; then
    if [ "$(cat "$DATA/.bq/bundle-tag" 2>/dev/null)" != "$TAG" ]; then
        rm -rf "$DATA.new" "$DATA.old"
        if cp -cR "$BUNDLE_GAME" "$DATA.new" 2>/dev/null && mkdir -p "$DATA.new/.bq" \
                && echo "$TAG" >"$DATA.new/.bq/bundle-tag"; then
            { [ ! -e "$DATA" ] || mv "$DATA" "$DATA.old"; } && mv "$DATA.new" "$DATA"
        fi
        rm -rf "$DATA.new" "$DATA.old"
    fi
    if [ "$(cat "$DATA/.bq/bundle-tag" 2>/dev/null)" = "$TAG" ]; then
        GAME="$DATA"
        if [ "${BQ_NO_UPDATE:-0}" != 1 ]; then
            # The frozen Python carries no CA list of its own; every macOS has this one.
            export SSL_CERT_FILE=/etc/ssl/cert.pem
            UPD=("$APP/MacOS/bq-update" --launch --root "$DATA" --platform macos-app)
            [ -f "$APP/Resources/mac-inputs" ] && UPD+=(--bundle-mac-inputs "$APP/Resources/mac-inputs")
            [ -n "${BQ_MANIFEST_URL:-}" ] && UPD+=(--manifest-url "$BQ_MANIFEST_URL")
            [ -n "${BQ_FALLBACK_URL+x}" ] && UPD+=(--fallback-url "$BQ_FALLBACK_URL")
            "${UPD[@]}"
            _rc=$?
            [ "$_rc" = 4 ] && exit 0
            [ "$_rc" -ne 0 ] && [ "$_rc" -ne 3 ] && exit "$_rc"
        fi
    fi
fi

has_paks() {   # has_paks <dir>: prints the pak0/pak1 paths (any case) if both are there
    local p0 p1
    p0="$(_bq_pick "$1" pak0.pak)" && p1="$(_bq_pick "$1" pak1.pak)" && printf '%s\n%s\n' "$p0" "$p1"
}

# 1. Quake paks: search the usual places (Steam, GOG, ~/Downloads...), then ask.
if [ ! -f "$USERDIR/id1/pak0.pak" ] || [ ! -f "$USERDIR/id1/pak1.pak" ]; then
    # shellcheck source=../../tools/find-quake-paks.sh
    . "$GAME/tools/find-quake-paks.sh"
    bq_install_paks "$USERDIR" >/dev/null 2>&1
fi
while [ ! -f "$USERDIR/id1/pak0.pak" ] || [ ! -f "$USERDIR/id1/pak1.pak" ]; do
    DIR="$(osascript -e 'POSIX path of (choose folder with prompt "Locate your Quake id1 folder (it holds pak0.pak and pak1.pak)")' 2>/dev/null)" || {
        alert "BAKOQUAKE needs Quake" "BAKOQUAKE uses the data files from Quake (pak0.pak and pak1.pak), which you need to own. Copy them into:

$USERDIR/id1/

or run BAKOQUAKE again and pick your Quake id1 folder."
        exit 1
    }
    DIR="${DIR%/}"
    PAKS="$(has_paks "$DIR" || has_paks "$DIR/id1" || has_paks "$DIR/ID1")" || {
        alert "No Quake paks there" "That folder does not have both pak0.pak and pak1.pak. Pick the id1 folder of your Quake install."
        continue
    }
    { IFS= read -r P0; IFS= read -r P1; } <<<"$PAKS"
    cp "$P0" "$USERDIR/id1/pak0.pak" && cp "$P1" "$USERDIR/id1/pak1.pak" || {
        rm -f "$USERDIR/id1/pak0.pak" "$USERDIR/id1/pak1.pak"
        alert "Copy failed" "Could not copy the paks into $USERDIR/id1/"
        exit 1
    }
done

ARGS=(-basedir "$GAME" -userdir "$USERDIR" -game quake15 -game BakersfieldQuake)
# Game log in the user folder. The engine appends, so the previous one is moved aside first (bq_game_prev.log).
[ -f "$USERDIR/BakersfieldQuake/bq_game.log" ] && mv -f "$USERDIR/BakersfieldQuake/bq_game.log" "$USERDIR/BakersfieldQuake/bq_game_prev.log" 2>/dev/null
ARGS+=(+log_file bq_game.log)

# 2. First run (no saved config, or only the package's seed): login name and a random colour, like Play.sh.
CFG="$USERDIR/BakersfieldQuake/config.cfg"
if [ ! -f "$CFG" ] || grep -q BAKERSFIELD_SEED "$CFG" 2>/dev/null; then
    ARGS+=(+_cl_name "${USER:-player}" +_cl_color $(( (RANDOM % 14) * 17 )))
fi

# 2b. Live memory tiering (normal / lowmem / ultralow / safemode): checks total unified RAM and vm_stat available RAM.
#     Apple Silicon shares unified memory between CPU & GPU, so <=8 GB Macs or low free RAM start in ultralow.cfg.
RAM_GB=$(( ( $(sysctl -n hw.memsize 2>/dev/null || echo 0) + 536870912 ) / 1073741824 ))
_ps="$(sysctl -n hw.pagesize 2>/dev/null || echo 4096)"
_free_pages="$(vm_stat 2>/dev/null | awk '/Pages (free|inactive|speculative|purgeable):/ { gsub(/\./, "", $NF); s += $NF } END { print s + 0 }')"
FREE_MB=$(( (${_free_pages:-0} * ${_ps:-4096}) / 1048576 ))

TIER="normal"
case "${BQ_TIER:-}" in
    normal|lowmem|ultralow|safemode) TIER="$BQ_TIER" ;;
    *)
        if [ "${BQ_SAFEMODE:-}" = 1 ]; then
            TIER="safemode"
        elif [ "${BQ_ULTRALOW:-}" = 1 ]; then
            TIER="ultralow"
        elif { [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 2048 ]; } || { [ "$RAM_GB" -gt 0 ] && [ "$RAM_GB" -le 8 ]; }; then
            TIER="ultralow"
        elif { [ "$RAM_GB" -gt 0 ] && [ "$RAM_GB" -lt 10 ]; } || { [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 3584 ]; }; then
            TIER="lowmem"
        fi
        if [ "${BQ_LOWMEM:-}" = 1 ] && [ "$TIER" = normal ]; then TIER="lowmem"; fi
        if [ "${BQ_LOWMEM:-}" = 0 ] && [ "$TIER" = lowmem ]; then TIER="normal"; fi
        ;;
esac

case "$TIER" in
    safemode) ARGS+=(+exec safemode.cfg) ;;
    ultralow) ARGS+=(+exec ultralow.cfg) ;;
    lowmem)   ARGS+=(+exec lowmem.cfg) ;;
esac

# 3. LAN autoscan only with a real python3: without the Command Line Tools, /usr/bin/python3 is a stub that pops
#    an install dialog.
SCAN="$GAME/tools/lanscan.py"
if [ -f "$SCAN" ] && xcode-select -p >/dev/null 2>&1; then
    mkdir -p "$USERDIR/BakersfieldQuake"
    FOUND="$(python3 "$SCAN" --gamedir "$USERDIR/BakersfieldQuake" --once --timeout-ms 1500 2>/dev/null | head -1)"
    case "$FOUND" in FOUND\ *) ARGS+=(+connect "${FOUND#FOUND }") ;; esac
    # Keep lan_server.cfg fresh until the game exits (exec below keeps this PID), so F3 works.
    python3 "$SCAN" --gamedir "$USERDIR/BakersfieldQuake" --pid $$ >/dev/null 2>&1 &
fi

exec "$APP/MacOS/darkplaces-sdl" "${ARGS[@]}" "$@"
