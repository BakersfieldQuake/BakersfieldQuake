#!/bin/sh
# Screenshots of a Union Ave segment from fixed spots (true feet): sh view_union.sh union3 8200 12200 "name x y z yaw" ...  -> zg_<name>.png (test map uniontest, no vis)
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
SEG=$1; Y0=$2; Y1=$3; shift 3
for v in "$@"; do
    set -- $v
    name=$1; shift
    GW_SEG="uniontest $Y0 $Y1" UN_START="$*" $PY make_union.py out/maps/uniontest.map > out/maps/uniontest.log || { echo "$name: build failed"; tail -3 out/maps/uniontest.log; continue; }
    (cd out/maps && $E/qbsp.exe uniontest.map > /dev/null 2>&1 && $E/vis.exe -fast uniontest.bsp > /dev/null 2>&1 && $E/light.exe uniontest.bsp > /dev/null 2>&1)
    cp out/maps/uniontest.bsp out/maps/uniontest.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    (cd /g/Quake/Combat && timeout 150 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +deathmatch 0 +coop 0 +map uniontest +defer 45 "screenshot zg_$name.png" +defer 47 "quit" > /dev/null 2>&1)
    echo "$name done"
done
rm -f ../../maps/uniontest.bsp ../../maps/uniontest.lit
