#!/bin/sh
# Rebuild the browser walk-around viewer from maps/bklan.bsp and put it, with the making-of page, on the VPS:
#   https://bakersfield.larrywew.fun/warehouse/            the viewer (web_viewer_index.html + export_web_viewer.py)
#   https://bakersfield.larrywew.fun/warehouse/making-of.html
# usage: sh deploy_web_viewer.sh            (needs the "vps" host in ~/.ssh/config)
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
W=out/web/warehouse
$PY export_web_viewer.py $W
cp web_viewer_index.html $W/index.html; cp dev_overlay.js $W/dev_overlay.js
[ -f $W/lib/three.module.min.js ] || { mkdir -p $W/lib; curl -s -L -o $W/lib/three.module.min.js https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js; }
sed 's|<meta name="viewport" content="width=device-width,initial-scale=1">|&<meta name="robots" content="noindex">|' \
    ../../making_of_larrys_warehouse.html > $W/making-of.html
ssh vps 'mkdir -p /var/www/megaman/warehouse'
scp -q -r $W/index.html $W/dev_overlay.js $W/making-of.html $W/map.json $W/map.bin $W/lightmap.png $W/lib $W/tex $W/sky vps:/var/www/megaman/warehouse/
ssh vps 'chmod -R a+rX /var/www/megaman/warehouse'
echo "deployed: https://bakersfield.larrywew.fun/warehouse/"
