#!/bin/sh
# Screenshots of "gallup" from fixed spots: sh view_gallup.sh "name x y z yaw" ... -> BakersfieldQuake/zga_<name>.png
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=/d/vibe/quake1opensource/tools/ericw
CFG=../../config.cfg
BAK=out/maps/.gallup_cfg_bak
mkdir -p out/maps

FIRST=1
[ "$GALLUP_REUSE_BSP" = "1" ] && [ -f out/maps/galluptest.bsp ] && FIRST=0
for v in "$@"; do
    set -- $v
    name=$1; x=$2; y=$3; z=$4; yaw=$5
    GALLUP_CLEAN_SHOTS="${GALLUP_CLEAN_SHOTS:-0}" GALLUP_START="$x $y $z $yaw" $PY make_gallup.py out/maps/galluptest.map > out/maps/galluptest.log || { echo "$name: build failed"; tail -5 out/maps/galluptest.log; continue; }
    if [ "$FIRST" = "1" ]; then
        (cd out/maps && $E/qbsp.exe -threads 4 galluptest.map > galluptest-qbsp.log 2>&1 && $E/light.exe -threads 4 galluptest.bsp > galluptest-light.log 2>&1) || { echo "$name: qbsp/light failed"; tail -8 out/maps/galluptest-qbsp.log; exit 1; }
        FIRST=0
    else
        (cd out/maps && $E/qbsp.exe -onlyents galluptest.map galluptest.bsp > galluptest-ents.log 2>&1) || { echo "$name: onlyents failed"; exit 1; }
    fi
    cp out/maps/galluptest.bsp out/maps/galluptest.lit ../../maps/
    while tasklist | grep -qi darkplaces; do sleep 3; done
    [ -f "$CFG" ] && cp "$CFG" "$BAK"
    (cd /g/Quake/Combat && timeout 60 ./darkplaces.exe -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake \
        +vid_mouse 0 +joystick 0 +m_pitch 0 +m_yaw 0 +r_drawviewmodel 0 +viewsize 120 +crosshair 0 +cl_bob 0 +fov 90 \
        +deathmatch 0 +coop 0 +sv_gravity 0 +map galluptest \
        +defer 8 "force_centerview" +defer 9 "screenshot zga_$name.png" +defer 10 "quit" > /dev/null 2>&1)
    [ -f "$BAK" ] && cp "$BAK" "$CFG" && rm -f "$BAK"
    echo "$name done"
done
rm -f ../../maps/galluptest.bsp ../../maps/galluptest.lit
