#!/bin/sh
# Screenshots of bklan from fixed spots: for each "name x y z angle" (feet) build a test copy (maps/bklantest.bsp)
# with the start there, run DarkPlaces single-player, screenshot, quit. Shots land in BakersfieldQuake/zv_<name>.png.
# usage: sh view_bklan.sh "front -20 -44 2.2 55" "lan 72 58 2.2 180" ...
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
for v in "$@"; do
    set -- $v
    name=$1; shift
    BKLAN_START="$*" $PY -I make_bklan.py out/maps/bklantest.map > /dev/null || { echo "$name: bad spot"; continue; }
    (cd out/maps && $E/qbsp.exe bklantest.map > /dev/null 2>&1 && $E/light.exe bklantest.bsp > /dev/null 2>&1)   # no vis: quicker, same picture
    cp out/maps/bklantest.bsp out/maps/bklantest.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done          # someone else is testing: wait for a gap
    (cd /g/Quake/Combat && timeout 60 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +deathmatch 0 +coop 0 +map bklantest +defer 9 "screenshot zv_$name.png" +defer 10 "quit" > /dev/null 2>&1)
    echo "$name done"
done
rm -f ../../maps/bklantest.bsp ../../maps/bklantest.lit
