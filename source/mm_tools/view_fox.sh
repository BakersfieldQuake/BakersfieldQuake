#!/bin/sh
# Screenshots of "fox" from fixed spots: sh view_fox.sh "name x y z yaw [pitch]" ... -> BakersfieldQuake/zf_<name>.png
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
CFG=../../config.cfg
BAK=out/maps/.fox_cfg_bak
mkdir -p out/maps

if [ -f out/maps/fox.bsp ] && [ -f out/maps/fox.lit ]; then
    cp out/maps/fox.bsp out/maps/foxtest.bsp
    cp out/maps/fox.lit out/maps/foxtest.lit
    HAVE_BSP=1
else
    HAVE_BSP=0
fi

for v in "$@"; do
    set -- $v
    name=$1; shift
    FOX_START="$*" $PY make_fox.py out/maps/foxtest.map > out/maps/foxtest.log || { echo "$name: build failed"; tail -5 out/maps/foxtest.log; continue; }
    if [ "$HAVE_BSP" = "0" ]; then
        (cd out/maps && $E/qbsp.exe -bsp2 -threads 4 foxtest.map > foxtest-qbsp.log 2>&1 && $E/light.exe -threads 4 foxtest.bsp > foxtest-light.log 2>&1) || { echo "$name: qbsp/light failed"; exit 1; }
        HAVE_BSP=1
    else
        (cd out/maps && $E/qbsp.exe -bsp2 -onlyents foxtest.map foxtest.bsp > foxtest-ents.log 2>&1) || { echo "$name: onlyents failed"; exit 1; }
    fi
    cp out/maps/foxtest.bsp out/maps/foxtest.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    [ -f "$CFG" ] && cp "$CFG" "$BAK"
    (cd /g/Quake/Combat && timeout 60 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +vid_mouse 0 +joystick 0 +m_pitch 0 +m_yaw 0 +r_drawviewmodel 0 +viewsize 120 +crosshair 0 +cl_bob 0 +fov 90 \
        +deathmatch 0 +coop 0 +sv_gravity 0 +map foxtest \
        +defer 5 "screenshot zf_$name.png" +defer 6 "quit" > /dev/null 2>&1)
    [ -f "$BAK" ] && cp "$BAK" "$CFG" && rm -f "$BAK"
    echo "$name done"
done
rm -f ../../maps/foxtest.bsp ../../maps/foxtest.lit out/maps/foxtest.bsp out/maps/foxtest.lit
