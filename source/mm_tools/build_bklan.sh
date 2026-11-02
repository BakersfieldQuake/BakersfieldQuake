#!/bin/sh
# Rebuild bklan: textures + wad, .map, qbsp -> vis -> light, install into BakersfieldQuake/maps.
# usage: sh build_bklan.sh <frames dir> <gallery dir>   (see build_bklan_textures.py)
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
[ -n "$1" ] && { $PY build_bklan_textures.py "$1" "$2"; $PY sunny_pass.py 1.1 1.35; }
$PY -I make_bklan.py out/maps/bklan.map
cd out/maps
$E/qbsp.exe bklan.map > bklan-qbsp.log 2>&1
grep -i -E "leak" bklan-qbsp.log && exit 1
$E/vis.exe bklan.bsp > bklan-vis.log 2>&1
$E/light.exe -extra bklan.bsp > bklan-light.log 2>&1
cp bklan.bsp bklan.lit ../../../../maps/
echo installed bklan
