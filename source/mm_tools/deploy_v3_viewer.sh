#!/bin/sh
# The browser viewer for bklan3 -> https://bakersfield.larrywew.fun/warehouse3/ (needs maps/bklan3.bsp; "vps" host in ssh config)
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
W=out/web/warehouse3
$PY export_web_viewer.py $W bklan3
mkdir -p $W/lib
[ -f $W/lib/three.module.min.js ] || cp out/web/warehouse/lib/three.module.min.js $W/lib/
sed -e "s|<title>Larry's Warehouse</title>|<title>Larry's Warehouse - bklan3</title>|" \
    -e "s|<h1>Larry's Warehouse</h1>|<h1>Larry's Warehouse - version 3</h1>|" \
    -e 's|<a href="making-of.html" target="_blank">The Making Of</a>|<a href="../warehouse2/">Version 2</a>|' \
    -e 's|<script type="module" src="dev_overlay.js"></script>|&<script type="module" src="dev_review.js"></script>|' \
    -e 's|id="bright" type="range" min="0.5" max="5" step="0.05" value="3.6"|id="bright" type="range" min="0.5" max="5" step="0.05" value="1.2"|' \
    -e 's|const bright = { value: 3.6 };|const bright = { value: 1.2 };|' \
    web_viewer_index.html > $W/index.html
cp dev_overlay.js dev_review.js $W/
[ -n "$V3_NOUPLOAD" ] && { echo "exported to $W (no upload)"; exit 0; }
ssh vps 'mkdir -p /var/www/megaman/warehouse3'
scp -q -r $W/index.html $W/dev_overlay.js $W/dev_review.js $W/map.json $W/map.bin $W/lightmap.png $W/lib $W/tex $W/sky vps:/var/www/megaman/warehouse3/
ssh vps 'chmod -R a+rX /var/www/megaman/warehouse3'
echo "deployed: https://bakersfield.larrywew.fun/warehouse3/"
