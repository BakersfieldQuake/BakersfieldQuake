#!/bin/sh
# Build the map "goldenwest" (Golden West Casino + its block, from the Street View / aerial gallery) -> maps/goldenwest.bsp
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_gw_textures.py
$PY build_gw_casino_textures.py
$PY make_gw_horse.py
$PY make_goldenwest.py out/maps/goldenwest.map
cd out/maps
$E/qbsp.exe goldenwest.map > goldenwest-qbsp.log 2>&1
tr '\r' '\n' < goldenwest-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe goldenwest.bsp > goldenwest-vis.log 2>&1
$E/light.exe -extra goldenwest.bsp > goldenwest-light.log 2>&1
cp goldenwest.bsp goldenwest.lit ../../../../maps/
echo "installed goldenwest"
