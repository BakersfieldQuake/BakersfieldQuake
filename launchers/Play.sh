#!/usr/bin/env bash
# BAKOQUAKE - Play (Linux).
# Joins the LAN server if one is up. Otherwise it starts the game on its own, and quake.rc then plays the
# BAKOQUAKE intro demo (intro.dem). In the intro, F1 joins the online server and F2 the LAN game.
# Extra engine args (e.g. -window) can be passed with:  COMBAT_ARGS="-window" ./Play.sh
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"   # no readlink -f: macOS before 12.3 lacks it
cd "$ROOT" || exit 1
# macOS: darkplaces-sdl dlopen()s libpng/freetype/vorbis/curl by bare name; Homebrew's lib dir is not searched by
# default, and without libpng every PNG texture fails to decode.
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
if [ ! -f "$ROOT/id1/pak0.pak" ] && [ -f "$ROOT/tools/find-quake-paks.sh" ]; then
    # shellcheck source=/dev/null
    . "$ROOT/tools/find-quake-paks.sh" && bq_install_paks "$ROOT"
fi
if [ ! -f "$ROOT/id1/pak0.pak" ]; then
    echo "id1/pak0.pak is missing. Copy pak0.pak and pak1.pak from your Quake install into $ROOT/id1/" >&2
    exit 1
fi

# Saved settings live in this folder (BakersfieldQuake/config.cfg), same as on Windows, not in ~/.darkplaces.
COMMON=(-basedir "$ROOT" -userdir "$ROOT" -game quake15 -game BakersfieldQuake)

# First run (no saved config yet, or only the placeholder from the package): use the login name and a random colour.
FIRST=()
CFG="$ROOT/BakersfieldQuake/config.cfg"
if [ ! -f "$CFG" ] || grep -q BAKERSFIELD_SEED "$CFG" 2>/dev/null; then
    FIRST=(+_cl_name "${USER:-player}" +_cl_color $(( (RANDOM % 14) * 17 )))
fi

# Quick scan (~1.5 s) for a server on the LAN.
JOIN=()
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    FOUND="$(python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --once --timeout-ms 1500 2>/dev/null | head -1)"
    case "$FOUND" in FOUND\ *) JOIN=(+connect "${FOUND#FOUND }") ;; esac
fi

# Keys (F1 = online server, F2 = LAN) are defaults in default.cfg, not forced here, so a player's rebinds are saved.
# shellcheck disable=SC2086
"$ENGINE" "${COMMON[@]}" ${FIRST[@]+"${FIRST[@]}"} ${COMBAT_ARGS:-} ${JOIN[@]+"${JOIN[@]}"} &
GAME=$!

# Keep lan_server.cfg fresh until the game exits, so F2 works.
if command -v python3 >/dev/null 2>&1 && [ -f "$SCAN" ]; then
    python3 "$SCAN" --gamedir "$ROOT/BakersfieldQuake" --pid "$GAME" >/dev/null 2>&1 &
fi
wait "$GAME"
