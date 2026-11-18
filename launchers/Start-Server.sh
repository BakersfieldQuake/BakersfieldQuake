#!/usr/bin/env bash
# BAKOQUAKE - Start Server (Linux). Host PC only.
# Starts the dedicated server (BakersfieldQuake/server.cfg) in the background, then joins it on this PC.
# Stop the server with:  ./Start-Server.sh stop
set -u

ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$ROOT" || exit 1
[ "$(uname)" = Darwin ] && export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:+$DYLD_FALLBACK_LIBRARY_PATH:}/opt/homebrew/lib:/usr/local/lib"  # macOS: libpng etc. from Homebrew
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

echo " Joining the game..."
# shellcheck disable=SC2086
"$CLIENT" "${COMMON[@]}" ${FIRST[@]+"${FIRST[@]}"} $COMBAT_ARGS +connect 127.0.0.1 &
GAME=$!
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --pid "$GAME" >/dev/null 2>&1 &
fi
wait "$GAME"
