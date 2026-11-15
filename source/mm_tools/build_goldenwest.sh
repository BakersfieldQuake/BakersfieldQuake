#!/bin/sh
# Build the standalone 1:1 modular map "goldenwest" (Golden West Casino, 1001 S Union Ave, Bakersfield)
# -> source/mm_tools/goldenwest/out/goldenwest.map -> maps/goldenwest.bsp + .lit + .spots.json
set -e
cd "$(dirname "$0")"

if command -v py >/dev/null 2>&1; then
    PY="py -3.13"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    PY="/c/Users/qxdc/AppData/Local/Microsoft/WindowsApps/python3.13.exe"
fi

echo "[build_goldenwest] Using Python: $PY"
$PY goldenwest/build_textures.py
$PY goldenwest/build_sky.py
$PY goldenwest/make_gw.py goldenwest/out/goldenwest.map
$PY goldenwest/compile_gw.py --map goldenwest/out/goldenwest.map "$@"
echo "[build_goldenwest] Built & installed goldenwest.bsp, goldenwest.lit, and goldenwest.spots.json"
