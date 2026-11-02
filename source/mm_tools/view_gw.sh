#!/bin/sh
# Screenshots of "goldenwest" from fixed spots: sh view_gw.sh "name x y z yaw" ...  -> BakersfieldQuake/zg_<name>.png (test map goldenwesttest, no vis)
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
for v in "$@"; do
    set -- $v
    name=$1; shift
    GW_START="$*" $PY make_goldenwest.py out/maps/goldenwesttest.map > out/maps/gwtest.log || { echo "$name: build failed"; tail -3 out/maps/gwtest.log; continue; }
    (cd out/maps && $E/qbsp.exe goldenwesttest.map > /dev/null 2>&1 && $E/light.exe goldenwesttest.bsp > /dev/null 2>&1)
    cp out/maps/goldenwesttest.bsp out/maps/goldenwesttest.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    (cd /g/Quake/Combat && timeout 90 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +deathmatch 0 +coop 0 +map goldenwesttest +defer 9 "screenshot zg_$name.png" +defer 10 "quit" > /dev/null 2>&1)
    echo "$name done"
done
rm -f ../../maps/goldenwesttest.bsp ../../maps/goldenwesttest.lit
