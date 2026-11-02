#!/bin/sh
# Browser 3D viewer for bklan5 -> https://bakersfield.larrywew.fun/warehouse5/ (needs maps/bklan5.bsp + maps/bklan5.lit)
# usage: sh deploy_v5_viewer.sh            export + enhance + upload
#        V5_NOUPLOAD=1 sh deploy_v5_viewer.sh     export + enhance only
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
W=out/web/warehouse5
$PY export_web_viewer.py $W bklan5
$PY explore_bklan5_lighting.py atlases $W
$PY enhance_bklan5_web.py $W
[ -n "$V5_NOUPLOAD" ] && { echo "exported to $W (no upload)"; exit 0; }
ssh root@72.62.241.93 'mkdir -p /var/www/megaman/warehouse5'
tar -cf - -C $W . | ssh root@72.62.241.93 'tar -xf - -C /var/www/megaman/warehouse5 && chmod -R a+rX /var/www/megaman/warehouse5'
echo "deployed: https://bakersfield.larrywew.fun/warehouse5/"
