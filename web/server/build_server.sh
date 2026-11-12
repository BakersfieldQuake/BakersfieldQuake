#!/usr/bin/env bash
# Builds darkplaces-dedicated for Linux, the same engine the VPS runs: DarkPlaces 72ae1712 (2017, the protocol
# the Windows clients speak) plus the VPS patches in patches/ (spr32 stub on the dedicated server, gcc ALIGN fix).
# Runs the compiler inside Docker, so the host only needs docker and git:   ./build_server.sh <out-dir>
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(mkdir -p "${1:-server-out}" && cd "${1:-server-out}" && pwd)"
WORK="${DP_WORK:-$HOME/.cache/bakoweb-dp-server}"
REPO="${DP_REPO:-https://github.com/DarkPlacesEngine/darkplaces.git}"
DP_REF="${DP_REF:-72ae17123314e96c86e46ffd31426f1ed4a308a1}"
IMAGE="${BUILD_IMAGE:-debian:bookworm}"

mkdir -p "$WORK"
if [ ! -d "$WORK/darkplaces/.git" ]; then
	git clone "$REPO" "$WORK/darkplaces"
fi
cd "$WORK/darkplaces"
git fetch --quiet origin || true
git checkout --quiet --force "$DP_REF"
git clean -fdxq
for p in "$HERE"/patches/*.patch; do
	[ -e "$p" ] || continue
	echo "applying $(basename "$p")"
	git apply "$p"
done
echo "Building darkplaces-dedicated $(git rev-parse --short HEAD) in $IMAGE"

# -fcommon: 2017 code defines globals in headers, which gcc 10+ rejects by default
docker run --rm -v "$PWD:/src" -w /src "$IMAGE" bash -c '
	apt-get update -qq >/dev/null && apt-get install -y -qq build-essential zlib1g-dev libjpeg-dev >/dev/null &&
	make -j"$(nproc)" sv-release CFLAGS_EXTRA=-fcommon > build.log 2>&1 || { grep -E "error" build.log | head -30; exit 1; }'

cp -f darkplaces-dedicated "$OUT/darkplaces-dedicated"
echo "$DP_REF" > "$OUT/darkplaces-dedicated-commit.txt"
git checkout --quiet --force "$DP_REF"
ls -la "$OUT/darkplaces-dedicated"
