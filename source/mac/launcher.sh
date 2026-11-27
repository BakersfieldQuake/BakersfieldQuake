#!/bin/bash
# BAKOQUAKE.app main executable (Contents/MacOS/BAKOQUAKE). Installed by source/mac/build_app.sh.
# Reopens itself in a visible iTerm/Terminal window, updates the game data, finds the player's Quake paks, then runs
# the engine (crash log + Safe Mode retry on abnormal exit). Everything the game writes goes to
# ~/Library/Application Support/BAKOQUAKE (-userdir), so the signed bundle stays read-only.
# Errors still go through dialogs, so they show even with BQ_NO_TERMINAL=1.
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

# Visible terminal: double-clicking the app reopens this launcher in an iTerm window (Terminal.app if iTerm isn't
# installed), so the engine's console output shows. Updates use the same GUI window as Windows/Linux.
# BQ_NO_TERMINAL=1 keeps it hidden.
# iTerm is driven by AppleScript (macOS asks once to allow BAKOQUAKE to control iTerm); Terminal runs .command files.
if [ -z "${BQ_IN_TERMINAL:-}" ] && [ "${BQ_NO_TERMINAL:-0}" != 1 ]; then
    RUN="${TMPDIR:-/tmp}/bakoquake-run.command"   # TMPDIR has no spaces, which iTerm's command string needs
    # The terminal starts a fresh environment: carry the BQ_* overrides (BQ_NO_UPDATE from `make run`, ...) across.
    { echo '#!/bin/bash'; for v in $(compgen -e | grep '^BQ_'); do printf '%s=%q ' "$v" "${!v}"; done
      printf 'BQ_IN_TERMINAL=1 exec %q' "$0"; [ $# -gt 0 ] && printf ' %q' "$@"; echo; } >"$RUN" \
        && chmod 755 "$RUN" || RUN=""
    if [ -n "$RUN" ]; then
        if open -Ra iTerm >/dev/null 2>&1 \
                && osascript -e "tell application \"iTerm\" to create window with default profile command \"$RUN\"" >/dev/null 2>&1; then
            exit 0
        fi
        open -a Terminal "$RUN" && exit 0
    fi
fi

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
            # A local build (make build, tag local-*) is newer than any DMG; never send it to download one.
            [ -f "$APP/Resources/mac-inputs" ] && [ "${TAG#local-}" = "$TAG" ] && UPD+=(--bundle-mac-inputs "$APP/Resources/mac-inputs")
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

# 1a. Quake's own lightning gun back, from your pak0.pak. A loose file in the userdir's BakersfieldQuake (the last folder
#     the engine adds) beats every pk3, in the bundle too. Never stops the game.
if [ -f "$GAME/tools/find-quake-paks.sh" ]; then
    # shellcheck source=../../tools/find-quake-paks.sh
    . "$GAME/tools/find-quake-paks.sh" && bq_restore_stock_lg "$USERDIR"
fi

# 1b. Display & Graphics Picker: run the frozen GUI picker (without --no-gui so the native picker window opens).
BQ_PICK_CANCEL=0
BQ_PICK_PRESET=""
BQ_PICK_MODE=""
BQ_PICK_WIDTH=""
BQ_PICK_HEIGHT=""
BQ_PICK_HZ=""
BQ_PICK_MON_X=""
BQ_PICK_MON_Y=""
BQ_PICK_MON_W=""
BQ_PICK_MON_H=""
BQ_PICK_MON_PRIMARY=""
BQ_PICK_CFG=""
if [ -x "$APP/MacOS/bq-update" ]; then
    _bq_tmp="${TMPDIR:-/tmp}"
    _bq_tmp="${_bq_tmp%/}"
    _bq_pick_env="$(mktemp "$_bq_tmp/bq-pick.XXXXXX")"
    _bq_pick_cmd=("$APP/MacOS/bq-update" --picker --root "$GAME" --userdir "$USERDIR" --out-env "$_bq_pick_env" --env-format sh)
    [ "${BQ_SETUP:-0}" = 1 ] && _bq_pick_cmd+=(--setup)
    "${_bq_pick_cmd[@]}"
    _bq_pick_rc=$?
    if [ -f "$_bq_pick_env" ]; then
        # shellcheck source=/dev/null
        . "$_bq_pick_env"
        rm -f "$_bq_pick_env"
    fi
    if [ "$_bq_pick_rc" = 4 ] || [ "${BQ_PICK_CANCEL:-0}" = 1 ]; then
        exit 0
    fi
fi

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
#     Apple Silicon shares unified memory between CPU & GPU, so <=8 GB Macs or low free RAM start in ultralow.cfg
#     unless the player picked an explicit graphics preset in Display Setup.
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
        elif [ -n "${BQ_PICK_PRESET:-}" ]; then
            TIER="preset-${BQ_PICK_PRESET}"
        elif { [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 2048 ]; } || { [ "$RAM_GB" -gt 0 ] && [ "$RAM_GB" -le 8 ]; }; then
            TIER="ultralow"
        elif { [ "$RAM_GB" -gt 0 ] && [ "$RAM_GB" -lt 10 ]; } || { [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 3584 ]; }; then
            TIER="lowmem"
        fi
        if [ "${BQ_LOWMEM:-}" = 1 ] && [ "$TIER" = normal ]; then TIER="lowmem"; fi
        if [ "${BQ_LOWMEM:-}" = 0 ] && [ "$TIER" = lowmem ]; then TIER="normal"; fi
        ;;
esac

if [ -n "${BQ_PICK_CFG:-}" ]; then
    ARGS+=(+exec "$BQ_PICK_CFG")
fi
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
fi

# 4. Run the engine and wait (no exec), so an abnormal exit keeps its log and offers Safe Mode.
run_engine() {   # run_engine <extra engine args...>
    "$APP/MacOS/darkplaces-sdl" "${ARGS[@]}" "$@" &
    local pid=$!
    # Keep lan_server.cfg fresh until the game exits, so F3 works.
    if [ -f "$SCAN" ] && xcode-select -p >/dev/null 2>&1; then
        python3 "$SCAN" --gamedir "$USERDIR/BakersfieldQuake" --pid "$pid" >/dev/null 2>&1 &
    fi
    wait "$pid"
}

run_engine "$@"
RC=$?
LOG="$USERDIR/BakersfieldQuake/bq_game.log"
if [ "$RC" -ne 0 ] && [ -f "$LOG" ]; then
    cp -f "$LOG" "$USERDIR/BakersfieldQuake/bq_game_crash.log" 2>/dev/null
    [ "$TIER" = safemode ] && { alert "BAKOQUAKE crashed" "Exit code $RC, in Safe Mode. Log: $USERDIR/BakersfieldQuake/bq_game_crash.log"; exit "$RC"; }
    BTN="$(osascript - "$RC" "$USERDIR/BakersfieldQuake/bq_game_crash.log" <<'EOF2' 2>/dev/null
on run argv
    button returned of (display alert "BAKOQUAKE exited abnormally" message "Exit code " & (item 1 of argv) & ". Crash log saved to " & (item 2 of argv) as critical buttons {"Close", "Retry in Safe Mode"} default button 2)
end run
EOF2
)"
    if [ "$BTN" = "Retry in Safe Mode" ]; then
        mv -f "$LOG" "$USERDIR/BakersfieldQuake/bq_game_prev.log" 2>/dev/null
        run_engine "$@" +exec safemode.cfg
        RC=$?
    fi
fi
exit "$RC"
