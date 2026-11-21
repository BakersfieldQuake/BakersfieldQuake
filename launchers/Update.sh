#!/usr/bin/env bash
# BAKOQUAKE - Standalone Updater (Linux, and macOS zip).
# Checks GitHub (falling back to the VPS), verifies all managed files, and opens the updater GUI.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$HERE"
if [ ! -f "$ROOT/tools/bq_update.py" ] && [ -f "$ROOT/../tools/bq_update.py" ]; then
    ROOT="$(cd "$ROOT/.." && pwd -P)"
fi

if [ ! -f "$ROOT/tools/bq_update.py" ]; then
    echo "Could not find tools/bq_update.py next to Update.sh." >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1 || { [ "$(uname)" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; }; then
    msg="Python 3 is required to run Update.sh (on Debian/Ubuntu: sudo apt install python3 python3-tk)."
    echo "$msg" >&2
    if command -v zenity >/dev/null 2>&1 && { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; }; then
        zenity --error --title="BAKOQUAKE Updater" --text="$msg" --width=420 >/dev/null 2>&1 || true
    fi
    exit 1
fi

exec python3 "$ROOT/tools/bq_update.py" --standalone --root "$ROOT" ${1+"$@"}
