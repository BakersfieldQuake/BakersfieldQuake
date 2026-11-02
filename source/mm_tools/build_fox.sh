#!/bin/sh
# Build the standalone map "fox" (Historic Fox Theater & The Padre Hotel, Downtown Bakersfield) -> maps/fox.bsp + maps/fox.lit
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_fox_textures.py
$PY build_fox_models.py
$PY make_fox.py out/maps/fox.map
cd out/maps
$E/qbsp.exe -bsp2 -threads 4 fox.map > fox-qbsp.log 2>&1
tr '\r' '\n' < fox-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe -threads 4 fox.bsp > fox-vis.log 2>&1
$E/light.exe -extra4 -threads 4 fox.bsp > fox-light.log 2>&1
cp fox.bsp fox.lit ../../../../maps/
echo "installed fox.bsp and fox.lit"
