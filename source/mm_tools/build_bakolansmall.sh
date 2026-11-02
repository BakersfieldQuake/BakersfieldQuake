#!/bin/sh
# Build the map "bakolansmall": Golden West Casino + the B-LAN warehouse block on one short stretch of S Union Ave.
# make_bakolansmall.py runs make_goldenwest.py (GW_FAST=1) and make_bklan.py (BKLAN_V3=1) into out/bks/, cuts the wanted pieces out of
# their .map output and adds the street, sky, plaza and gameplay. The texture wads (goldenwest, gwcasino, bklan, bklan3) are used as they
# are in out/maps: this script does not rebuild them (other generators own them).
# usage: sh build_bakolansmall.sh        -> maps/bakolansmall.bsp + .lit installed      (BKS_REUSE=1 sh ...: skip re-running the two generators)
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY make_bakolansmall.py out/maps/bakolansmall.map
cd out/maps
$E/qbsp.exe bakolansmall.map > bakolansmall-qbsp.log 2>&1 || { tail -5 bakolansmall-qbsp.log; exit 1; }
tr '\r' '\n' < bakolansmall-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe -fast bakolansmall.bsp > bakolansmall-vis.log 2>&1
$E/light.exe -extra bakolansmall.bsp > bakolansmall-light.log 2>&1
cp bakolansmall.bsp bakolansmall.lit ../../../../maps/
echo "installed bakolansmall"
