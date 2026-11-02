#!/bin/sh
# The browser viewer for bklan4 -> https://bakersfield.larrywew.fun/warehouse4/ (needs maps/bklan4.bsp; "vps" host in ssh config)
# usage: sh deploy_v4_viewer.sh            export + upload
#        V4_NOUPLOAD=1 sh deploy_v4_viewer.sh     export only (look at it locally: python -m http.server in out/web/warehouse4)
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
W=out/web/warehouse4
$PY export_web_viewer.py $W bklan4
mkdir -p $W/lib
[ -f $W/lib/three.module.min.js ] || cp out/web/warehouse/lib/three.module.min.js $W/lib/
sed -e "s|<title>Larry's Warehouse</title>|<title>Larry's Warehouse - bklan4</title>|" \
    -e "s|<h1>Larry's Warehouse</h1>|<h1>Larry's Warehouse - version 4: Golden West Casino</h1>|" \
    -e 's|<a href="making-of.html" target="_blank">The Making Of</a>|<a href="../warehouse3/">Version 3</a>|' \
    -e 's|<script type="module" src="dev_overlay.js"></script>|&<script type="module" src="dev_review.js"></script>|' \
    web_viewer_index.html > $W/index.html
cp dev_overlay.js dev_review.js $W/
[ -n "$V4_NOUPLOAD" ] && { echo "exported to $W (no upload)"; exit 0; }
ssh vps 'mkdir -p /var/www/megaman/warehouse4'
scp -q -r $W/index.html $W/dev_overlay.js $W/dev_review.js $W/map.json $W/map.bin $W/lightmap.png $W/lib $W/tex $W/sky vps:/var/www/megaman/warehouse4/
ssh vps 'chmod -R a+rX /var/www/megaman/warehouse4'
echo "deployed: https://bakersfield.larrywew.fun/warehouse4/"
