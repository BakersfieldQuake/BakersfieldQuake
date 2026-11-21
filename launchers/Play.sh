#!/usr/bin/env bash
# BAKOQUAKE - Play (Linux, and the macOS zip for people who run from a terminal; the macOS app uses
# source/mac/launcher.sh instead).
# Joins the LAN server if one is up. Otherwise it starts the game on its own, and quake.rc then plays the
# BAKOQUAKE intro demo (intro.dem). In the intro, F1 joins the online server and F2 the LAN game.
# Extra engine args (e.g. -window) can be passed with:  COMBAT_ARGS="-window" ./Play.sh
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
# restarts; exit 4 cancels launch (user declined update or update failed).
if [ -f "$ROOT/tools/bq_update.py" ] && command -v python3 >/dev/null 2>&1 \
        && { [ "$(uname)" != Darwin ] || xcode-select -p >/dev/null 2>&1; }; then
    python3 "$ROOT/tools/bq_update.py" --launch --root "$ROOT"
    _bq_rc=$?
    [ "$_bq_rc" = 3 ] && exec "$ROOT/$(basename "${BASH_SOURCE[0]}")" ${1+"$@"}
    [ "$_bq_rc" = 4 ] && exit 0
fi

# Menu and desktop shortcuts (tools/install-shortcuts.sh). Only rewritten when this folder moved; never stops the game.
if [ "$(uname)" = Linux ] && [ -f "$ROOT/tools/install-shortcuts.sh" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/tools/install-shortcuts.sh" && bq_install_shortcuts "$ROOT"
fi

# Saved settings live in this folder (BakersfieldQuake/config.cfg), same as on Windows, not in ~/.darkplaces.
COMMON=(-basedir "$ROOT" -userdir "$ROOT" -game quake15 -game BakersfieldQuake)

# First run (no saved config yet, or only the placeholder from the package): use the login name and a random colour.
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

# Quick scan (~1.5 s) for a server on the LAN.
JOIN=()
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    FOUND="$(python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --once --timeout-ms 1500 2>/dev/null | head -1)"
    case "$FOUND" in FOUND\ *) JOIN=(+connect "${FOUND#FOUND }") ;; esac
fi

# Keys (F1 = online server, F2 = LAN) are defaults in default.cfg, not forced here, so a player's rebinds are saved.
# shellcheck disable=SC2086
# Game log. The engine appends to its log, so the previous one is moved aside first: BakersfieldQuake/bq_game.log is
# this session, bq_game_prev.log the one before. They are what to send when the game crashes or runs badly.
[ -f "$ROOT/BakersfieldQuake/bq_game.log" ] && mv -f "$ROOT/BakersfieldQuake/bq_game.log" "$ROOT/BakersfieldQuake/bq_game_prev.log" 2>/dev/null
"$ENGINE" "${COMMON[@]}" +log_file bq_game.log ${FIRST[@]+"${FIRST[@]}"} ${LOWMEM[@]+"${LOWMEM[@]}"} ${COMBAT_ARGS:-} ${JOIN[@]+"${JOIN[@]}"} &
GAME=$!

# Keep lan_server.cfg fresh until the game exits, so F2 works.
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --pid "$GAME" >/dev/null 2>&1 &
fi
wait "$GAME"
