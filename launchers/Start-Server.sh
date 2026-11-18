#!/usr/bin/env bash
# BAKOQUAKE - Start Server (Linux, and the macOS zip). Host PC only.
# Starts the dedicated server (BakersfieldQuake/server.cfg) in the background, then joins it on this PC.
# Stop the server with:  ./Start-Server.sh stop
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
if [ ! -f "$ROOT/id1/pak0.pak" ] && [ -f "$ROOT/tools/find-quake-paks.sh" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/tools/find-quake-paks.sh" && bq_install_paks "$ROOT"
fi
if [ ! -f "$ROOT/id1/pak0.pak" ]; then
    echo "id1/pak0.pak is missing. Copy pak0.pak and pak1.pak from your Quake install into $ROOT/id1/" >&2
    exit 1
fi

# Update: fetch only the files that changed in the newest release (BQ_NO_UPDATE=1 skips it, e.g. offline at a LAN).
# macOS python3 is a stub that asks to install the developer tools, so only use a real one there.
# One compound command: bash reads a running script from disk, so when files changed (exit 3) the updated launcher
# restarts.
if [ -f "$ROOT/tools/bq_update.py" ] && command -v python3 >/dev/null 2>&1 \
        && { [ "$(uname)" != Darwin ] || xcode-select -p >/dev/null 2>&1; }; then
    python3 "$ROOT/tools/bq_update.py" --launch --root "$ROOT"
    [ $? = 3 ] && exec "$ROOT/$(basename "${BASH_SOURCE[0]}")" "$@"
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
    nohup "$DEDICATED" "${COMMON[@]}" -dedicated 16 +exec server.cfg >"$LOG" 2>&1 &
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

# Join it from this PC with the normal client launcher.
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

# Low-memory mode (lowmem.cfg): with the normal settings the game needs about 4 GB of memory of its own, and with 8 GB of
# RAM the map load can end in "Mem_Alloc: out of memory". Under 10 GB the game starts with half-size model textures.
# BQ_LOWMEM=1 forces it on, BQ_LOWMEM=0 off.
LOWMEM=()
RAM_GB=0
if [ -r /proc/meminfo ]; then
    RAM_GB=$(( $(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0) / 1048576 ))
elif [ "$(uname)" = Darwin ]; then
    RAM_GB=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
fi
if [ "${BQ_LOWMEM:-}" = 1 ] || { [ "${BQ_LOWMEM:-}" != 0 ] && [ "$RAM_GB" -gt 0 ] && [ "$RAM_GB" -lt 10 ]; }; then
    LOWMEM=(+exec lowmem.cfg)
fi

echo " Joining the game..."
# shellcheck disable=SC2086
"$CLIENT" "${COMMON[@]}" ${FIRST[@]+"${FIRST[@]}"} ${LOWMEM[@]+"${LOWMEM[@]}"} $COMBAT_ARGS +connect 127.0.0.1 &
GAME=$!
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --pid "$GAME" >/dev/null 2>&1 &
fi
wait "$GAME"
