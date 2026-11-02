#!/bin/sh
# The browser viewer for bklan2 -> https://bakersfield.larrywew.fun/warehouse2/ (needs maps/bklan2.bsp; "vps" host in ssh config)
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
W=out/web/warehouse2
$PY export_web_viewer.py $W bklan2
mkdir -p $W/lib
[ -f $W/lib/three.module.min.js ] || cp out/web/warehouse/lib/three.module.min.js $W/lib/
sed -e "s|<title>Larry's Warehouse</title>|<title>Larry's Warehouse - bklan2</title>|" \
    -e "s|<h1>Larry's Warehouse</h1>|<h1>Larry's Warehouse - version 2</h1>|" \
    -e 's|<a href="making-of.html" target="_blank">The Making Of</a>|<a href="../warehouse/">Version 1</a>|' \
    -e 's|<script type="module" src="dev_overlay.js"></script>|&<script type="module" src="dev_review.js"></script>|' \
    web_viewer_index.html > $W/index.html
cp dev_overlay.js dev_review.js $W/
ssh vps 'mkdir -p /var/www/megaman/warehouse2'
scp -q -r $W/index.html $W/dev_overlay.js $W/dev_review.js $W/map.json $W/map.bin $W/lightmap.png $W/lib $W/tex $W/sky vps:/var/www/megaman/warehouse2/
ssh vps 'chmod -R a+rX /var/www/megaman/warehouse2'
echo "deployed: https://bakersfield.larrywew.fun/warehouse2/"
