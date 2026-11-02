#!/bin/sh
# Deploys the Fox Theater & Padre Hotel browser viewer, self-contained showcase HTML,
# and live Quake dedicated server assets to root@72.62.241.93 ("vps" SSH alias).
set -e
cd "$(dirname "$0")"
PY=/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe
W=out/web/fox

[ -f "$W/map.bin" ] || $PY export_web_viewer.py "$W" fox
cp ../../fox_showcase.html "$W/showcase.html"

ssh vps 'mkdir -p /var/www/megaman/fox'
tar -cf - -C "$W" . | ssh vps 'tar -xf - -C /var/www/megaman/fox && chmod -R a+rX /var/www/megaman/fox'
scp -q ../../fox_showcase.html vps:/var/www/megaman/fox_showcase.html
ssh vps 'chmod a+r /var/www/megaman/fox_showcase.html'

# Update /opt/quake/BakersfieldQuake with fox_map_pack.zip
ssh vps 'python3 -c "import zipfile; zipfile.ZipFile(\"/var/www/megaman/fox/fox_map_pack.zip\").extractall(\"/opt/quake/BakersfieldQuake\")" && chown -R quake:quake /opt/quake/BakersfieldQuake/maps /opt/quake/BakersfieldQuake/progs/fox /opt/quake/BakersfieldQuake/scripts /opt/quake/BakersfieldQuake/textures && chmod -R a+rX /opt/quake/BakersfieldQuake/maps /opt/quake/BakersfieldQuake/progs/fox /opt/quake/BakersfieldQuake/scripts /opt/quake/BakersfieldQuake/textures'

echo "Deployed showcase: https://bakersfield.larrywew.fun/fox_showcase.html"
echo "Deployed 3D viewer: https://bakersfield.larrywew.fun/fox/"
