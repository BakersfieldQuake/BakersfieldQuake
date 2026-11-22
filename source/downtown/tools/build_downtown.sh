#!/bin/sh
# Build the downtown map.
#   sh build_downtown.sh                                  full map -> maps/downtown.bsp + .lit   (vis full; DT_FAST=1 for vis -fast + light without -extra4)
#   DT_WINDOW="x0 y0 x1 y1" [DT_TAG=name] [DT_INSTALL=mapname] sh build_downtown.sh   only that D-feet window (+own sky/clip box), vis -fast -> maps/dt_<tag>.bsp
#   downtownsmall: DT_WINDOW="-340 -900 950 275" DT_TAG=small DT_INSTALL=downtownsmall DT_FAST= sh build_downtown.sh
#   bakersfielddowntown: DT_WINDOW="-340 -900 950 275" DT_TAG=bakersfielddowntown DT_INSTALL=bakersfielddowntown DT_FAST= sh build_downtown.sh
#   bakersfielddowntown_lite: DT_LITE=1 sh build_downtown.sh
# Logs: source/downtown/out/<map>-{make,qbsp,vis,light}.log
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
E=${DT_ERICW:-/d/vibe/quake1opensource/tools/ericw}
[ -d "$E" ] || E=/g/Quake/TRUEDM3/tools/ericw
[ -d "$E" ] || E=/g/Quake/Combat/tools/ericw
MODMAPS=../../../maps
THREADS=${DT_THREADS:-8}
VISDIST=${DT_VISDIST:-12200}
QBSP_EXTRA=${DT_QBSP_EXTRA:-}
LIGHT_EXTRA=${DT_LIGHT_FLAGS:--extra4}
if [ "$DT_LITE" = "1" ]; then
    export DT_LITE=1
    export DT_FUN=${DT_FUN:-1}
    DT_WINDOW=${DT_WINDOW:-"-340 -900 950 275"}
    export DT_WINDOW
    DT_TAG=${DT_TAG:-bakersfielddowntown_lite}
    DT_INSTALL=${DT_INSTALL:-bakersfielddowntown_lite}
    VISDIST=${DT_VISDIST:-2500}
    QBSP_EXTRA=${DT_QBSP_EXTRA:--maxnodesize 2048}
    LIGHT_EXTRA=${DT_LIGHT_FLAGS:--extra}
    DT_FAST=${DT_FAST-}
fi
if [ -n "$DT_WINDOW" ]; then
    if [ -z "$DT_TAG" ]; then DT_TAG=$($PY -c "import os;v=[int(round(float(t))) for t in os.environ['DT_WINDOW'].replace(',',' ').split()];print('w%d_%d_%d_%d'%tuple(v))"); fi
    export DT_TAG
    if [ "$DT_TAG" = "bakersfielddowntown" ]; then VISDIST=${DT_VISDIST:-4000}; fi
    NAME=downtown_$DT_TAG; INSTALL=${DT_INSTALL:-dt_$DT_TAG}; FAST=${DT_FAST-1}      # DT_FAST= (set but empty) = full vis + light -extra4, e.g. for downtownsmall
else
    NAME=downtown; INSTALL=downtown; FAST=${DT_FAST:-}
fi
T0=$(date +%s)
$PY make_downtown.py > ../out/$NAME-make.stdout.log 2>&1 || { tail -20 ../out/$NAME-make.stdout.log; exit 1; }
tail -3 ../out/$NAME-make.stdout.log
cd ../out
$E/qbsp.exe -bsp2 -subdivide 1024 $QBSP_EXTRA -threads $THREADS $NAME.map > $NAME-qbsp.log 2>&1 || true
if tr '\r' '\n' < $NAME-qbsp.log | grep -qiE "leak|error"; then echo "QBSP problem (leak/error) - see out/$NAME-qbsp.log"; tr '\r' '\n' < $NAME-qbsp.log | grep -iE "leak|error" | head -3; exit 1; fi
echo "qbsp ok: no leak"
T1=$(date +%s)
if [ -n "$FAST" ]; then
    $E/vis.exe -fast -threads $THREADS $NAME.bsp > $NAME-vis.log 2>&1
    $E/light.exe -threads $THREADS $NAME.bsp > $NAME-light.log 2>&1
else
    $E/vis.exe -visdist $VISDIST -threads $THREADS $NAME.bsp > $NAME-vis.log 2>&1
    $PY ../tools/keep_sky_pvs.py $NAME.bsp >> $NAME-vis.log 2>&1
    $E/light.exe $LIGHT_EXTRA -threads $THREADS $NAME.bsp > $NAME-light.log 2>&1
fi
T2=$(date +%s)
SC=$($PY -c "import json;print(json.load(open('$NAME.json'))['post_light_scale'] or '')")
if [ -n "$SC" ]; then $PY ../../mm_tools/scale_bklan_light85.py $NAME.bsp $SC > $NAME-scale.log 2>&1; fi
if [ "$DT_TAG" = "bakersfielddowntown" ] || [ "$DT_TAG" = "bakersfielddowntown_lite" ] || [ "$DT_LITE" = "1" ]; then
    $PY ../tools/clamp_bd_sb25.py $NAME.bsp >> $NAME-scale.log 2>&1
    $PY ../tools/strip_miptex_pixels.py $NAME.bsp >> $NAME-scale.log 2>&1
fi
cp $NAME.bsp $MODMAPS/$INSTALL.bsp; cp $NAME.lit $MODMAPS/$INSTALL.lit
if [ "$DT_TAG" = "bakersfielddowntown" ]; then $PY ../tools/save_bd_presets.py $MODMAPS/$INSTALL.bsp >> $NAME-scale.log 2>&1; fi
echo "installed maps/$INSTALL.bsp (+.lit): qbsp $((T1-T0))s, vis+light $((T2-T1))s"
