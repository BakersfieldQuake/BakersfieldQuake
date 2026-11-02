#!/bin/sh
# Screenshots of "bakolansmall" from fixed spots: sh view_bks.sh "name x y z yaw [pitch]" ...  -> BakersfieldQuake/zs_<name>.png
# (test map bakolansmalltest: no vis, no light = fullbright; sv_gravity 0 so a spot high in the air holds still)
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
for v in "$@"; do
    set -- $v
    name=$1; shift
    BKS_REUSE=1 BKS_START="$*" $PY make_bakolansmall.py out/maps/bakolansmalltest.map > out/maps/bkstest.log || { echo "$name: build failed"; tail -3 out/maps/bkstest.log; continue; }
    (cd out/maps && $E/qbsp.exe bakolansmalltest.map > /dev/null 2>&1)
    cp out/maps/bakolansmalltest.bsp ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    (cd /g/Quake/Combat && timeout 120 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +r_drawviewmodel 0 +deathmatch 0 +coop 0 +map bakolansmalltest +defer 10 "screenshot zs_$name.png" +defer 11 "quit" > /dev/null 2>&1)
    echo "$name done"
done
rm -f ../../maps/bakolansmalltest.bsp
