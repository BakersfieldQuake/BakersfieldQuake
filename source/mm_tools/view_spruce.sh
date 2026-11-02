#!/bin/sh
# Screenshots of "spruce" from fixed spots: sh view_spruce.sh "name x y z yaw" ... -> BakersfieldQuake/zsp_<name>.png
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
CFG=../../config.cfg
BAK=out/maps/.spruce_cfg_bak
mkdir -p out/maps

FIRST=1
[ "$SPRUCE_REUSE_BSP" = "1" ] && [ -f out/maps/sprucetest.bsp ] && FIRST=0
for v in "$@"; do
    set -- $v
    name=$1; x=$2; y=$3; z=$4; yaw=$5
    SPRUCE_CLEAN_SHOTS=1 SPRUCE_START="$x $y $z $yaw" $PY make_spruce.py out/maps/sprucetest.map > out/maps/sprucetest.log || { echo "$name: build failed"; tail -5 out/maps/sprucetest.log; continue; }
    if [ "$FIRST" = "1" ]; then
        (cd out/maps && $E/qbsp.exe -threads 4 sprucetest.map > sprucetest-qbsp.log 2>&1 && $E/light.exe -threads 4 sprucetest.bsp > sprucetest-light.log 2>&1) || { echo "$name: qbsp/light failed"; tail -8 out/maps/sprucetest-qbsp.log; exit 1; }
        FIRST=0
    else
        (cd out/maps && $E/qbsp.exe -onlyents sprucetest.map sprucetest.bsp > sprucetest-ents.log 2>&1) || { echo "$name: onlyents failed"; exit 1; }
    fi
    cp out/maps/sprucetest.bsp out/maps/sprucetest.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    [ -f "$CFG" ] && cp "$CFG" "$BAK"
    (cd /g/Quake/Combat && timeout 60 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +vid_mouse 0 +joystick 0 +m_pitch 0 +m_yaw 0 +r_drawviewmodel 0 +viewsize 120 +crosshair 0 +cl_bob 0 +fov 90 \
        +deathmatch 0 +coop 0 +sv_gravity 0 +map sprucetest \
        +defer 8 "force_centerview" +defer 9 "screenshot zsp_$name.png" +defer 10 "quit" > /dev/null 2>&1)
    [ -f "$BAK" ] && cp "$BAK" "$CFG" && rm -f "$BAK"
    echo "$name done"
done
rm -f ../../maps/sprucetest.bsp ../../maps/sprucetest.lit
