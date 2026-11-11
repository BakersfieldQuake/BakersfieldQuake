#!/bin/sh
# Build the standalone 1:1 modular map "goldenwest" (Golden West Casino, 1001 S Union Ave, Bakersfield) -> maps/goldenwest.bsp + .lit
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_goldenwest_textures.py
$PY make_gw_horse.py
$PY make_gw_buddha.py
$PY make_goldenwest.py out/maps/goldenwest.map
cd out/maps
$E/qbsp.exe -bsp2 -threads 4 goldenwest.map > goldenwest-qbsp.log 2>&1
tr '\r' '\n' < goldenwest-qbsp.log | grep -i -E "leak|missing" && exit 1
$E/vis.exe -threads 4 goldenwest.bsp > goldenwest-vis.log 2>&1
$E/light.exe -extra4 -threads 4 goldenwest.bsp > goldenwest-light.log 2>&1
cp goldenwest.bsp goldenwest.lit ../../../../maps/
echo "installed goldenwest.bsp and goldenwest.lit"
