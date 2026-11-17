#!/bin/sh
# Build the standalone map "spruce" (Spruce St / Westchester Neighborhood & Water Tower, Bakersfield, CA 93301) -> maps/spruce.bsp + maps/spruce.lit
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_spruce_textures.py
$PY make_spruce.py out/maps/spruce.map
cd out/maps
$E/qbsp.exe -threads 4 spruce.map > spruce-qbsp.log 2>&1
tr '\r' '\n' < spruce-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe -visdist 7200 -threads 8 spruce.bsp > spruce-vis.log 2>&1
$E/light.exe -threads 4 -extra4 spruce.bsp > spruce-light.log 2>&1
$PY ../../fog_vis_tools.py prune-pvs spruce.bsp --visdist 7200 --no-backup
$PY ../../fog_vis_tools.py set-fog spruce.bsp --start-ft 300 --end-ft 575 --rgb 0.56 0.70 0.82 --top-ft 45 --fade-ft 35 --no-backup
cp spruce.bsp spruce.lit ../../../../maps/
echo "installed spruce.bsp and spruce.lit"
