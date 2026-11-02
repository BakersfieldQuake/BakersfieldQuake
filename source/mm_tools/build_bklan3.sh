#!/bin/sh
# Build the map "bklan3": bklan2 (make_bklan_v3.py) + make_bklan_v4.py, the owner's review of bklan2 (2026-10-31 16:03):
# warehouse + bedroom in 118/120, teleports moved, exploding parked cars, drivable vans, the drive loop with the pink car and
# the Podracer, the biplane, the park trash can, fewer jump pads, a 500 ft sky, no car pictures in the windows.
# usage: sh build_bklan3.sh        -> maps/bklan3.bsp + .lit installed
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_v3_textures.py
$PY build_v4_textures.py
$PY make_bklan_sounds.py
BKLAN_V3=1 BKLAN_V4=1 $PY -I make_bklan.py out/maps/bklan3.map
cd out/maps
$E/qbsp.exe bklan3.map > bklan3-qbsp.log 2>&1
tr '\r' '\n' < bklan3-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe bklan3.bsp > bklan3-vis.log 2>&1
$E/light.exe -extra bklan3.bsp > bklan3-light.log 2>&1
cp bklan3.bsp bklan3.lit ../../../../maps/
echo "installed bklan3"
