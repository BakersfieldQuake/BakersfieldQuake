#!/bin/sh
# Build the map "bklan5": combines The Historic Bakersfield Fox Theater & Downtown Bakersfield (fox.map)
# directly inside bklan4's south-central pocket (Box D: x = -420..+650, y = -1322..-340), connecting S Union Ave /
# Golden West Casino on the west, Larry's Warehouse / E 21st St / Sonora St on the north, and Buck Owens Blvd /
# Crystal Palace / Bakersfield Sign / Amberton Park on the east.
#
# usage:
#   sh build_bklan5.sh                -> full vis + light -extra -> maps/bklan5.bsp + .lit installed
#   BK5_FAST=1 sh build_bklan5.sh     -> vis -fast + fast light, for rapid testing
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw

[ -s out/maps/bklan.wad ]  || $PY build_bklan_textures.py ref_sources/bklan_wmv_frames ref_sources/streetview_gallery2
[ -s out/maps/bklan3.wad ] || $PY build_v3_textures.py
[ -s out/maps/bklan4.wad ] || $PY build_v4_textures.py
[ -s out/maps/bklan5.wad ] || $PY build_v5_textures.py
[ out/maps/fox.wad -nt build_fox_textures.py ] || $PY build_fox_textures.py
$PY build_v6_textures.py

mkdir -p out/bk4 out/bk5
if [ ! -s out/bk4/gw.map ]; then
    GW_SEG="gw -130 400" GW_FAST=1 $PY make_goldenwest.py out/bk4/gw.map > out/bk4/gw.log 2>&1 || true
fi
[ -s out/bk4/gw.map ] || { echo "make_goldenwest.py wrote nothing"; tail -5 out/bk4/gw.log; exit 1; }

$PY make_fox.py out/bk5/fox.map > out/bk5/fox.log 2>&1
[ -s out/bk5/fox.map ] || { echo "make_fox.py wrote nothing"; tail -5 out/bk5/fox.log; exit 1; }

$PY -I make_bklan5.py out/maps/bklan5.map
$PY plan_map.py out/maps/bklan5.map out/plan_b5.png -830 -1535 1880 800 0.6

cd out/maps
$E/qbsp.exe -bsp2 -threads 4 bklan5.map > bklan5-qbsp.log 2>&1
tr '\r' '\n' < bklan5-qbsp.log | grep -i -E "leak" && exit 1

if [ -n "$BK5_FAST" ]; then
    $E/vis.exe -fast -threads 4 bklan5.bsp > bklan5-vis.log 2>&1
    $E/light.exe -threads 4 bklan5.bsp > bklan5-light.log 2>&1
else
    $E/vis.exe -threads 4 bklan5.bsp > bklan5-vis.log 2>&1
    $E/light.exe -extra -threads 4 bklan5.bsp > bklan5-light.log 2>&1
fi

cp bklan5.bsp bklan5.lit ../../../../maps/
echo "installed maps/bklan5.bsp and maps/bklan5.lit"
