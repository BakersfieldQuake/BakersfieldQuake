#!/usr/bin/env bash
# BAKOQUAKE - Play (Linux, and the macOS zip for people who run from a terminal; the macOS app uses
# source/mac/launcher.sh instead).
# Joins the LAN server if one is up. Otherwise opens into the BakersfieldQuake Main Menu.
# Extra engine args (e.g. -window) can be passed with:  COMBAT_ARGS="-window" ./Play.sh
# Tier overrides: BQ_TIER=normal|lowmem|ultralow|safemode  (or BQ_SAFEMODE=1, BQ_ULTRALOW=1, BQ_LOWMEM=1|0)
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"   # no readlink -f: macOS before 12.3 lacks it
cd "$ROOT" || exit 1
# macOS zip: darkplaces-sdl links Homebrew SDL2 and dlopen()s freetype/vorbis/jpeg by bare name; Homebrew's lib dir is
# not searched by default. (PNG is built in. The macOS app bundles its own libraries and doesn't need this.)
[ "$(uname)" = Darwin ] && export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:+$DYLD_FALLBACK_LIBRARY_PATH:}/opt/homebrew/lib:/usr/local/lib"
SCAN="$ROOT/tools/lanscan.py"
[ -f "$SCAN" ] || SCAN="$ROOT/lanscan.py"

# A zip made on Windows carries no Unix permission bits: make the engines and scripts runnable.
chmod +x "$ROOT"/darkplaces-sdl "$ROOT"/darkplaces-dedicated "$ROOT"/Start-Server.sh "$ROOT"/tools/lanscan.py 2>/dev/null || true

# Client engine: the one in this folder, else a system DarkPlaces (distro package).
ENGINE=""
for c in "$ROOT/darkplaces-sdl" "$ROOT/darkplaces"; do
    [ -x "$c" ] && ENGINE="$c" && break
done
if [ -z "$ENGINE" ]; then
    ENGINE="$(command -v darkplaces-sdl || command -v darkplaces || true)"
fi
if [ -z "$ENGINE" ]; then
    echo "Could not find the DarkPlaces client (darkplaces-sdl) next to Play.sh." >&2
    echo "Unpack the whole BAKOQUAKE folder and run ./Play.sh from inside it (see README-LINUX.txt)." >&2
    exit 1
fi

# First run: find pak0/pak1 in the usual Steam/GOG folders or ~/Downloads and copy them into id1/.
if { [ ! -f "$ROOT/id1/pak0.pak" ] || [ ! -f "$ROOT/id1/pak1.pak" ]; } && [ -f "$ROOT/tools/find-quake-paks.sh" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/tools/find-quake-paks.sh" && bq_install_paks "$ROOT"
fi
if [ ! -f "$ROOT/id1/pak0.pak" ] || [ ! -f "$ROOT/id1/pak1.pak" ]; then
    echo "id1/pak0.pak or id1/pak1.pak is missing. Copy pak0.pak and pak1.pak from your Quake install into $ROOT/id1/" >&2
    exit 1
fi

# Update: fetch only the files that changed in the newest release (BQ_NO_UPDATE=1 skips it, e.g. offline at a LAN).
# macOS python3 is a stub that asks to install the developer tools, so only use a real one there.
# One compound command: bash reads a running script from disk, so when files changed (exit 3) the updated launcher
# restarts; exit 4 or any other non-zero exit code cancels launch.
if [ -f "$ROOT/tools/bq_update.py" ] && command -v python3 >/dev/null 2>&1 \
        && { [ "$(uname)" != Darwin ] || xcode-select -p >/dev/null 2>&1; }; then
    python3 "$ROOT/tools/bq_update.py" --launch --root "$ROOT"
    _bq_rc=$?
    [ "$_bq_rc" = 3 ] && exec "$ROOT/$(basename "${BASH_SOURCE[0]}")" ${1+"$@"}
    [ "$_bq_rc" = 4 ] && exit 0
    [ "$_bq_rc" -ne 0 ] && exit "$_bq_rc"
fi

# Menu and desktop shortcuts (tools/install-shortcuts.sh). Only rewritten when this folder moved; never stops the game.
if [ "$(uname)" = Linux ] && [ -f "$ROOT/tools/install-shortcuts.sh" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/tools/install-shortcuts.sh" && bq_install_shortcuts "$ROOT"
fi

# Display & Graphics Picker (monitor, display mode, resolution, graphics preset).
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
if [ -f "$ROOT/tools/bq_update.py" ] && command -v python3 >/dev/null 2>&1 \
        && { [ "$(uname)" != Darwin ] || xcode-select -p >/dev/null 2>&1; }; then
    _bq_tmp="${TMPDIR:-/tmp}"
    _bq_tmp="${_bq_tmp%/}"
    _bq_pick_env="$(mktemp "$_bq_tmp/bq-pick.XXXXXX")"
    _bq_pick_cmd=(python3 "$ROOT/tools/bq_update.py" --picker --root "$ROOT" --userdir "$ROOT" --out-env "$_bq_pick_env" --env-format sh)
    [ "${BQ_SETUP:-0}" = 1 ] && _bq_pick_cmd+=(--setup)
    [ "${BQ_NO_GUI:-0}" = 1 ] && [ "${BQ_SETUP:-0}" != 1 ] && _bq_pick_cmd+=(--no-gui)
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

# Saved settings live in this folder (BakersfieldQuake/config.cfg), same as on Windows, not in ~/.darkplaces.
COMMON=(-basedir "$ROOT" -userdir "$ROOT" -game quake15 -game BakersfieldQuake)

# First run (no saved config yet, or only the placeholder from the package): use the login name and a random colour.
FIRST=()
CFG="$ROOT/BakersfieldQuake/config.cfg"
if [ ! -f "$CFG" ] || grep -q BAKERSFIELD_SEED "$CFG" 2>/dev/null; then
    FIRST=(+_cl_name "${USER:-player}" +_cl_color $(( (RANDOM % 14) * 17 )))
fi

# Live memory tiering (normal / lowmem / ultralow / safemode): checks both total RAM and live MemAvailable/vm_stat.
RAM_GB=0
FREE_MB=0
if [ -r /proc/meminfo ]; then
    _mt_kb="$(awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null || echo 0)"
    _ma_kb="$(awk '/^MemAvailable:/ {print $2; exit}' /proc/meminfo 2>/dev/null || echo 0)"
    [ "${_ma_kb:-0}" -eq 0 ] 2>/dev/null && _ma_kb="$(awk '/^MemFree:/ {print $2; exit}' /proc/meminfo 2>/dev/null || echo 0)"
    RAM_GB=$(( (${_mt_kb:-0} + 524288) / 1048576 ))
    FREE_MB=$(( ${_ma_kb:-0} / 1024 ))
elif [ "$(uname)" = Darwin ]; then
    RAM_GB=$(( ( $(sysctl -n hw.memsize 2>/dev/null || echo 0) + 536870912 ) / 1073741824 ))
    _ps="$(sysctl -n hw.pagesize 2>/dev/null || echo 4096)"
    _free_pages="$(vm_stat 2>/dev/null | awk '/Pages (free|inactive|speculative|purgeable):/ { gsub(/\./, "", $NF); s += $NF } END { print s + 0 }')"
    FREE_MB=$(( (${_free_pages:-0} * ${_ps:-4096}) / 1048576 ))
fi

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

PICKARGS=()
if [ -n "${BQ_PICK_CFG:-}" ]; then
    PICKARGS=(+exec "$BQ_PICK_CFG")
fi

TIERARGS=()
case "$TIER" in
    safemode) TIERARGS=(+exec safemode.cfg) ;;
    ultralow) TIERARGS=(+exec ultralow.cfg) ;;
    lowmem)   TIERARGS=(+exec lowmem.cfg) ;;
esac
if [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 1536 ]; then
    echo "Warning: only ${FREE_MB} MB RAM free — launching in ${TIER} mode. Close heavy apps for best performance." >&2
fi

# Quick scan (~1.5 s) for a server on the LAN.
JOIN=()
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    FOUND="$(python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --once --timeout-ms 1500 2>/dev/null | head -1)"
    case "$FOUND" in FOUND\ *) JOIN=(+connect "${FOUND#FOUND }") ;; esac
fi

# Game log. The engine appends to its log, so the previous one is moved aside first: BakersfieldQuake/bq_game.log is
# this session, bq_game_prev.log the one before, and bq_game_crash.log is preserved if the engine exits abnormally.
[ -f "$ROOT/BakersfieldQuake/bq_game.log" ] && mv -f "$ROOT/BakersfieldQuake/bq_game.log" "$ROOT/BakersfieldQuake/bq_game_prev.log" 2>/dev/null
# shellcheck disable=SC2086
"$ENGINE" "${COMMON[@]}" +log_file bq_game.log ${FIRST[@]+"${FIRST[@]}"} ${PICKARGS[@]+"${PICKARGS[@]}"} ${TIERARGS[@]+"${TIERARGS[@]}"} ${COMBAT_ARGS:-} ${JOIN[@]+"${JOIN[@]}"} &
GAME=$!

# Keep lan_server.cfg fresh until the game exits, so F3 works.
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --pid "$GAME" >/dev/null 2>&1 &
fi
wait "$GAME"
_game_rc=$?
if [ "$_game_rc" -ne 0 ] && [ -f "$ROOT/BakersfieldQuake/bq_game.log" ]; then
    cp -f "$ROOT/BakersfieldQuake/bq_game.log" "$ROOT/BakersfieldQuake/bq_game_crash.log" 2>/dev/null || true
    echo "BAKOQUAKE exited abnormally (code $_game_rc). Crash log saved to BakersfieldQuake/bq_game_crash.log." >&2
    echo "To retry in Safe Mode, run: BQ_TIER=safemode ./Play.sh" >&2
fi
exit "$_game_rc"
