#!/bin/sh
# Screenshots of bklan3 (bklan + make_bklan_v3.py) from fixed spots, like view_bklan.sh but BKLAN_V3=1 and map "bklan3test".
# Shots land in BakersfieldQuake/zv3_<name>.png.  usage: sh view_v3.sh "name x y z yaw" ...
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
for v in "$@"; do
    set -- $v
    name=$1; shift
    BKLAN_V3=1 BKLAN_START="$*" $PY -I make_bklan.py out/maps/bklan3test.map > out/maps/bklan3test.log || { echo "$name: build failed"; tail -5 out/maps/bklan3test.log; continue; }
    (cd out/maps && $E/qbsp.exe bklan3test.map > bklan3test-qbsp.log 2>&1 && $E/light.exe bklan3test.bsp > bklan3test-light.log 2>&1)
    cp out/maps/bklan3test.bsp out/maps/bklan3test.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    (cd /g/Quake/Combat && timeout 60 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +deathmatch 0 +coop 0 +map bklan3test +defer 9 "screenshot zv3_$name.png" +defer 10 "quit" > /dev/null 2>&1)
    echo "$name done"
done
rm -f ../../maps/bklan3test.bsp ../../maps/bklan3test.lit
