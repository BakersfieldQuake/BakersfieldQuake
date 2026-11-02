#!/bin/sh
# Screenshots of the casino from fixed spots, on a private test map (gwcasino: no street, no vis, so it never touches the real build):
#   sh view_gwc.sh "name x y z yaw" ...   ->  BakersfieldQuake/zc_<name>.png      (x y z in true feet, casino frame; yaw in degrees)
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
$PY build_gw_casino_textures.py > /dev/null && $PY make_gw_horse.py > /dev/null
for v in "$@"; do
    set -- $v
    name=$1; shift
    GW_FAST=1 GW_START="$*" $PY make_goldenwest.py out/maps/gwcasino.map > out/maps/gwcasino-make.log 2>&1 || { echo "$name: build failed"; tail -5 out/maps/gwcasino-make.log; continue; }
    (cd out/maps && $E/qbsp.exe gwcasino.map > gwcasino-qbsp.log 2>&1 && $E/light.exe gwcasino.bsp > gwcasino-light.log 2>&1) || { echo "$name: qbsp/light failed"; continue; }
    cp out/maps/gwcasino.bsp out/maps/gwcasino.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    (cd /g/Quake/Combat && timeout 90 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +deathmatch 0 +coop 0 +map gwcasino +defer 9 "screenshot zc_$name.png" +defer 10 "quit" > /dev/null 2>&1)
    echo "$name done"
done
rm -f ../../maps/gwcasino.bsp ../../maps/gwcasino.lit
