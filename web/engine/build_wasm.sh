#!/usr/bin/env bash
# Builds darkplaces-wasm.js, DarkPlaces for the browser (WebAssembly + WebGL2), inside the emsdk Docker image.
# Run on a Linux box with Docker and git (cccbox works):   ./build_wasm.sh <out-dir>
#
# Pinned to ef764984 (2024-09-12): the last DarkPlaces commit whose wasm build compiles. The next one (f399f8b,
# capture-video readback) and later GL changes use desktop-only GL calls, see DarkPlaces issue #247.
# Our changes: pre.js (the file loader) swapped in for wasm/pre.js, and the fixes in patches/*.patch.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(mkdir -p "${1:-wasm-out}" && cd "${1:-wasm-out}" && pwd)"
WORK="${DP_WORK:-$HOME/.cache/bakoweb-dp-wasm}"
REPO="${DP_REPO:-https://github.com/DarkPlacesEngine/darkplaces.git}"
DP_REF="${DP_REF:-ef764984a324c18e7c37562cb5388b24cec1c9b0}"
EMSDK_IMAGE="${EMSDK_IMAGE:-emscripten/emsdk:7.0.0}"

mkdir -p "$WORK"
if [ ! -d "$WORK/darkplaces/.git" ]; then
	git clone "$REPO" "$WORK/darkplaces"
fi
cd "$WORK/darkplaces"
git fetch --quiet origin || true
git checkout --quiet --force "$DP_REF"
git clean -fdxq
cp -f "$HERE/pre.js" wasm/pre.js
for p in "$HERE"/patches/*.patch; do
	[ -e "$p" ] || continue
	echo "applying $(basename "$p")"
	git apply "$p"
done
echo "Building DarkPlaces wasm $(git rev-parse --short HEAD) with $EMSDK_IMAGE"

docker run --rm -v "$PWD:/src" -w /src "$EMSDK_IMAGE" \
	bash -c 'make -j"$(nproc)" emscripten-release > build.log 2>&1 || { grep -E "error:|undefined symbol" build.log | head -30; exit 1; }'

cp -f darkplaces-wasm.js "$OUT/darkplaces-wasm.js"
echo "$DP_REF" > "$OUT/darkplaces-wasm-commit.txt"
git checkout --quiet --force "$DP_REF"
ls -la "$OUT/darkplaces-wasm.js"
