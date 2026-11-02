#!/bin/sh
# Build the map "bklan2": bklan + make_bklan_v3.py (the owner's feedback of 2026-10-31 09:36: jump pads, teleports, sprite
# trees, filler streets and blocks, open units, perimeter wall, Larry's signs, vehicle models for the cars).
# Independent of the plain bklan build, so another agent can keep changing bklan while this one is reviewed.
# usage: sh build_bklan2.sh        -> maps/bklan2.bsp + .lit installed
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_v3_textures.py
BKLAN_V3=1 $PY -I make_bklan.py out/maps/bklan2.map
cd out/maps
$E/qbsp.exe bklan2.map > bklan2-qbsp.log 2>&1
tr '\r' '\n' < bklan2-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe bklan2.bsp > bklan2-vis.log 2>&1
$E/light.exe -extra bklan2.bsp > bklan2-light.log 2>&1
cp bklan2.bsp bklan2.lit ../../../../maps/
echo "installed bklan2"
