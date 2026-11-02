#!/bin/sh
# Build the standalone map "gallup" (7705 Gallup Dr & Laurelglen Neighborhood, Bakersfield, CA 93309) -> maps/gallup.bsp + maps/gallup.lit
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_gallup_textures.py
$PY make_gallup.py out/maps/gallup.map
cd out/maps
$E/qbsp.exe -threads 4 gallup.map > gallup-qbsp.log 2>&1
tr '\r' '\n' < gallup-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe -threads 4 gallup.bsp > gallup-vis.log 2>&1
$E/light.exe -threads 4 -extra4 gallup.bsp > gallup-light.log 2>&1
cp gallup.bsp gallup.lit ../../../../maps/
echo "installed gallup.bsp and gallup.lit"
