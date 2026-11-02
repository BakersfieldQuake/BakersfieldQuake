#!/bin/sh
# Build the map "bklan4": bklan3 (make_bklan_v3.py + make_bklan_v4.py) + make_bklan_v5.py: Golden West Casino on a new
# box south of E 21st down Union Ave, the accuracy pass on Larry's warehouse / the Bakersfield Sign / Manning St / Amberton
# Park, the casino gameplay (spawns, items, roof pads, launch pads, teleports, the drive loop down Union).
# The casino piece is make_goldenwest.py's output (GW_FAST=1, no street) read back from out/bk4/gw.map.
# usage: sh build_bklan4.sh        -> maps/bklan4.bsp + .lit installed        (BK4_FAST=1: vis -fast, for a quick look)
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_bklan_textures.py ref_sources/bklan_wmv_frames ref_sources/streetview_gallery2
$PY build_v3_textures.py
$PY build_v4_textures.py
$PY build_v5_textures.py
$PY build_bklan_sky.py
$PY make_bklan_sounds.py
mkdir -p out/bk4
GW_SEG="gw -130 400" GW_FAST=1 $PY make_goldenwest.py out/bk4/gw.map > out/bk4/gw.log 2>&1 || true    # exits 1 on its own street-item check; the map is written first
[ -s out/bk4/gw.map ] || { echo "make_goldenwest.py wrote nothing"; tail -5 out/bk4/gw.log; exit 1; }
BKLAN_V3=1 BKLAN_V4=1 BKLAN_V5=1 $PY -I make_bklan.py out/maps/bklan4.map
cd out/maps
$E/qbsp.exe bklan4.map > bklan4-qbsp.log 2>&1
tr '\r' '\n' < bklan4-qbsp.log | grep -i -E "leak" && exit 1
if [ -n "$BK4_FAST" ]; then $E/vis.exe -fast bklan4.bsp > bklan4-vis.log 2>&1; else $E/vis.exe bklan4.bsp > bklan4-vis.log 2>&1; fi
$E/light.exe -extra bklan4.bsp > bklan4-light.log 2>&1
cp bklan4.bsp bklan4.lit ../../../../maps/
echo "installed bklan4"
