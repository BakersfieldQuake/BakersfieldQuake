#!/bin/bash
# BAKOQUAKE.app main executable (Contents/MacOS/BAKOQUAKE). Installed by source/mac/build_app.sh.
# Finds the player's Quake paks, then execs the engine. Everything the game writes goes to
# ~/Library/Application Support/BAKOQUAKE (-userdir), so the signed bundle stays read-only.
# There is no terminal, so every message goes through a dialog.
set -u

APP="$(cd "$(dirname "$0")/.." && pwd)"
GAME="$APP/Resources/game"
USERDIR="$HOME/Library/Application Support/BAKOQUAKE"
mkdir -p "$USERDIR/id1"

alert() {   # alert <title> <message>
    osascript - "$1" "$2" <<'EOF' >/dev/null 2>&1
on run argv
    display alert (item 1 of argv) message (item 2 of argv) as critical
end run
EOF
}

has_paks() {   # has_paks <dir>: prints the pak0/pak1 paths (any case) if both are there
    local p0 p1
    p0="$(_bq_pick "$1" pak0.pak)" && p1="$(_bq_pick "$1" pak1.pak)" && printf '%s\n%s\n' "$p0" "$p1"
}

# 1. Quake paks: search the usual places (Steam, GOG, ~/Downloads...), then ask.
if [ ! -f "$USERDIR/id1/pak0.pak" ]; then
    # shellcheck source=../../tools/find-quake-paks.sh
    . "$GAME/tools/find-quake-paks.sh"
    bq_install_paks "$USERDIR" >/dev/null 2>&1
fi
while [ ! -f "$USERDIR/id1/pak0.pak" ]; do
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
        rm -f "$USERDIR/id1/pak0.pak"
        alert "Copy failed" "Could not copy the paks into $USERDIR/id1/"
        exit 1
    }
done

ARGS=(-basedir "$GAME" -userdir "$USERDIR" -game quake15 -game BakersfieldQuake)

# 2. First run (no saved config, or only the package's seed): login name and a random colour, like Play.sh.
CFG="$USERDIR/BakersfieldQuake/config.cfg"
if [ ! -f "$CFG" ] || grep -q BAKERSFIELD_SEED "$CFG" 2>/dev/null; then
    ARGS+=(+_cl_name "${USER:-player}" +_cl_color $(( (RANDOM % 14) * 17 )))
fi

# 3. LAN autoscan only with a real python3: without the Command Line Tools, /usr/bin/python3 is a stub that pops
#    an install dialog.
SCAN="$GAME/tools/lanscan.py"
if [ -f "$SCAN" ] && xcode-select -p >/dev/null 2>&1; then
    mkdir -p "$USERDIR/BakersfieldQuake"
    FOUND="$(python3 "$SCAN" --gamedir "$USERDIR/BakersfieldQuake" --once --timeout-ms 1500 2>/dev/null | head -1)"
    case "$FOUND" in FOUND\ *) ARGS+=(+connect "${FOUND#FOUND }") ;; esac
    # Keep lan_server.cfg fresh until the game exits (exec below keeps this PID), so F2 works.
    python3 "$SCAN" --gamedir "$USERDIR/BakersfieldQuake" --pid $$ >/dev/null 2>&1 &
fi

exec "$APP/MacOS/darkplaces-sdl" "${ARGS[@]}" "$@"
