#!/usr/bin/env bash
# BAKOQUAKE - Start Server (Linux, and the macOS zip). Host PC only.
# Starts the dedicated server (BakersfieldQuake/server.cfg) in the background, then joins it on this PC.
# Stop the server with:  ./Start-Server.sh stop
# Tier overrides: BQ_TIER=normal|lowmem|ultralow|safemode  (or BQ_SAFEMODE=1, BQ_ULTRALOW=1, BQ_LOWMEM=1|0)
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"   # no readlink -f: macOS before 12.3 lacks it
cd "$ROOT" || exit 1
[ "$(uname)" = Darwin ] && export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:+$DYLD_FALLBACK_LIBRARY_PATH:}/opt/homebrew/lib:/usr/local/lib"  # macOS zip: SDL2/freetype/vorbis from Homebrew
SCAN="$ROOT/tools/lanscan.py"
[ -f "$SCAN" ] || SCAN="$ROOT/lanscan.py"
LOG="$ROOT/BakersfieldQuake/lan_server_console.log"
PIDFILE="$ROOT/BakersfieldQuake/lan_server.pid"

# A zip made on Windows carries no Unix permission bits: make the engines and scripts runnable.
chmod +x "$ROOT"/darkplaces-sdl "$ROOT"/darkplaces-dedicated "$ROOT"/Play.sh "$ROOT"/tools/lanscan.py 2>/dev/null || true

if [ "${1:-}" = "stop" ]; then
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        kill "$(cat "$PIDFILE")" && echo "Server stopped."
    else
        echo "No server of ours is running."
    fi
    rm -f "$PIDFILE"
    exit 0
fi

DEDICATED=""
for c in "$ROOT/darkplaces-dedicated" "$ROOT/darkplaces-sdl" "$ROOT/darkplaces"; do
    [ -x "$c" ] && DEDICATED="$c" && break
done
[ -z "$DEDICATED" ] && DEDICATED="$(command -v darkplaces-dedicated || command -v darkplaces || true)"
if [ -z "$DEDICATED" ]; then
    echo "Could not find darkplaces-dedicated next to Start-Server.sh (see README-LINUX.txt)." >&2
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

# Quake's own lightning gun back for this PC's client, from your id1/pak0.pak. Never stops the game.
if [ -f "$ROOT/tools/find-quake-paks.sh" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/tools/find-quake-paks.sh" && bq_restore_stock_lg "$ROOT"
fi

# Menu and desktop shortcuts (tools/install-shortcuts.sh). Only rewritten when this folder moved; never stops the game.
if [ "$(uname)" = Linux ] && [ -f "$ROOT/tools/install-shortcuts.sh" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/tools/install-shortcuts.sh" && bq_install_shortcuts "$ROOT"
fi

COMMON=(-basedir "$ROOT" -userdir "$ROOT" -game quake15 -game BakersfieldQuake)

echo
echo " BAKOQUAKE LAN server"
echo " --------------------"
echo " If you run a firewall, allow UDP port 26000 in (ufw: sudo ufw allow 26000/udp),"
echo " otherwise the other PCs can't see or join this server."
echo

# Don't start a second server if one is already running from this folder.
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo " A server is already running on this PC - just joining it."
else
    # bash's own exec, not nohup: nohup's execvp() runs a binary built for another CPU through /bin/sh, which parses
    # the ELF bytes as a script and creates junk files. bash refuses it with "cannot execute binary file".
    ( trap '' HUP; exec "$DEDICATED" "${COMMON[@]}" -dedicated 16 +exec server.cfg ) >"$LOG" 2>&1 &
    echo $! >"$PIDFILE"
    echo " Starting the server (console log: BakersfieldQuake/lan_server_console.log)..."
    # Wait until it has loaded the map and answers LAN queries (up to ~12 s).
    if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
        for _ in $(seq 1 20); do
            python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --once --timeout-ms 600 2>/dev/null | grep -q '^FOUND' && break
        done
    else
        sleep 8
    fi
fi

# Join it from this PC with the normal client launcher, unless this is a headless box (SSH, server-only Pi).
if [ "$(uname)" = Linux ] && [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo " No display here, so not joining; the server keeps running. Stop it with: ./Start-Server.sh stop"
    exit 0
fi
export COMBAT_ARGS="${COMBAT_ARGS:-}"
CLIENT=""
for c in "$ROOT/darkplaces-sdl" "$ROOT/darkplaces"; do [ -x "$c" ] && CLIENT="$c" && break; done
[ -z "$CLIENT" ] && CLIENT="$(command -v darkplaces-sdl || command -v darkplaces || true)"
if [ -z "$CLIENT" ]; then
    echo " No client engine found; the server is running, join it from another PC." >&2
    exit 0
fi

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
        elif { [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 2048 ]; } || { [ "$RAM_GB" -gt 0 ] && [ "$RAM_GB" -le 8 ]; }; then
            TIER="ultralow"
        elif { [ "$RAM_GB" -gt 0 ] && [ "$RAM_GB" -lt 10 ]; } || { [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 3584 ]; }; then
            TIER="lowmem"
        fi
        if [ "${BQ_LOWMEM:-}" = 1 ] && [ "$TIER" = normal ]; then TIER="lowmem"; fi
        if [ "${BQ_LOWMEM:-}" = 0 ] && [ "$TIER" = lowmem ]; then TIER="normal"; fi
        ;;
esac

TIERARGS=()
case "$TIER" in
    safemode) TIERARGS=(+exec safemode.cfg) ;;
    ultralow) TIERARGS=(+exec ultralow.cfg) ;;
    lowmem)   TIERARGS=(+exec lowmem.cfg) ;;
esac
if [ "$FREE_MB" -gt 0 ] && [ "$FREE_MB" -lt 1536 ]; then
    echo "Warning: only ${FREE_MB} MB RAM free — launching client in ${TIER} mode." >&2
fi

echo " Joining the game..."
# Game log. The engine appends to its log, so the previous one is moved aside first: BakersfieldQuake/bq_game.log is
# this session, bq_game_prev.log the one before, and bq_game_crash.log is preserved if the client exits abnormally.
[ -f "$ROOT/BakersfieldQuake/bq_game.log" ] && mv -f "$ROOT/BakersfieldQuake/bq_game.log" "$ROOT/BakersfieldQuake/bq_game_prev.log" 2>/dev/null
# shellcheck disable=SC2086
"$CLIENT" "${COMMON[@]}" +log_file bq_game.log ${FIRST[@]+"${FIRST[@]}"} ${TIERARGS[@]+"${TIERARGS[@]}"} $COMBAT_ARGS +connect 127.0.0.1 &
GAME=$!
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --pid "$GAME" >/dev/null 2>&1 &
fi
wait "$GAME"
_game_rc=$?
if [ "$_game_rc" -ne 0 ] && [ -f "$ROOT/BakersfieldQuake/bq_game.log" ]; then
    cp -f "$ROOT/BakersfieldQuake/bq_game.log" "$ROOT/BakersfieldQuake/bq_game_crash.log" 2>/dev/null || true
    echo "BAKOQUAKE exited abnormally (code $_game_rc). Crash log saved to BakersfieldQuake/bq_game_crash.log." >&2
    echo "To retry in Safe Mode, run: BQ_TIER=safemode ./Start-Server.sh" >&2
fi
exit "$_game_rc"
