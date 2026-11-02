#!/bin/sh
# Build one later segment of the street: sh build_union.sh union2 3800 8300   (or union3 8200 12200)
set -e
cd "$(dirname "$0")"
NAME=$1; Y0=$2; Y1=$3
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
GW_SEG="$NAME $Y0 $Y1" $PY make_union.py out/maps/$NAME.map
cd out/maps
$E/qbsp.exe $NAME.map > $NAME-qbsp.log 2>&1
tr '\r' '\n' < $NAME-qbsp.log | grep -i -E "leak" && exit 1
$E/vis.exe -fast $NAME.bsp > $NAME-vis.log 2>&1
$E/light.exe -extra $NAME.bsp > $NAME-light.log 2>&1
cp $NAME.bsp $NAME.lit ../../../../maps/
echo "installed $NAME"
