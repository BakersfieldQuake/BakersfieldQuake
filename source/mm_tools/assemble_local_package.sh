#!/bin/bash
# Assemble BAKOQUAKE game data from this repo for a local `make app`, without GitHub.
#
#   source/mm_tools/assemble_local_package.sh <base BAKOQUAKE dir> <out BAKOQUAKE dir>
#
# The base supplies the blobs the repo does not hold (bakersfield.pk3, q15.pk3, maps, the zz_*.pk3s that have no
# builder here). Over a clone of it this runs the release workflow's steps from the repo
# (.github/workflows/build-zip.yml: overlay configs and tools, build the overlay pk3s) and also compiles progs.dat,
# csprogs.dat and menu.dat from source, which CI does not.
#
# Env: WORK (default <repo>/build) holds the pk3 venv, the fteqcc build and the QC scratch copy.
#      PYTHON (default python3): any Python 3.12; the pk3 venv is made from it.
#      QC_HOST: compile the QC over ssh on this Linux host (e.g. QC_HOST=chonk). fteqcc built on macOS types
#               __variant builtins differently and fails on code that CI's Linux fteqcc compiles.
set -euo pipefail

BASE="${1:?usage: $0 <base BAKOQUAKE dir> <out BAKOQUAKE dir>}"
OUT="${2:?usage: $0 <base BAKOQUAKE dir> <out BAKOQUAKE dir>}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${WORK:-$ROOT/build}"
# Last fte-team/fteqw commit before the 2025-09-27 fteqcc64.exe the QC is built with on Windows.
FTEQW_REF=c781d13255ce72fcd24e47567244f970e1ba7c50
NUMPY=2.5.4 PILLOW=13.0.0   # the release workflow's pins

step() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[ -f "$BASE/BakersfieldQuake/bakersfield.pk3" ] || die "$BASE is not a BAKOQUAKE package"

step "clone base $BASE"
rm -rf "$OUT"
mkdir -p "$(dirname "$OUT")"
# Copy-on-write clone where the filesystem has it (APFS, btrfs, XFS): instant, shares blocks with the base.
if [ "$(uname -s)" = Darwin ]; then cp -Rc "$BASE" "$OUT"; else cp -R --reflink=auto "$BASE" "$OUT"; fi
G="$OUT/BakersfieldQuake"
rm -f "$G/progs/v_light.mdl"   # a played base holds id's model (the launchers extract it); never package it

step "overlay repo configs and tools"
# lan_server.cfg is written at run time by tools/lanscan, so the repo copy is not shipped (as in CI).
for f in "$ROOT"/*.cfg "$ROOT/quake.rc" "$ROOT/effectinfo.txt"; do
    [ "$(basename "$f")" = lan_server.cfg ] && continue
    cmp -s "$f" "$G/$(basename "$f")" || echo "  updated $(basename "$f")"
    cp "$f" "$G/"
done
mkdir -p "$OUT/tools"
for f in "$ROOT"/tools/* "$ROOT"/source/icons/*; do
    [ -f "$f" ] || continue
    cmp -s "$f" "$OUT/tools/$(basename "$f")" || echo "  updated tools/$(basename "$f")"
    cp "$f" "$OUT/tools/"
done

step "overlay pk3s"
VENV="$WORK/venv-pk3-numpy$NUMPY-pillow$PILLOW"
if [ ! -x "$VENV/bin/python" ]; then
    "${PYTHON:-python3}" -m venv "$VENV"
    "$VENV/bin/python" -m pip install --quiet --disable-pip-version-check "numpy==$NUMPY" "pillow==$PILLOW"
fi
M="$ROOT/source/mm_tools"
B="$BASE/BakersfieldQuake/bakersfield.pk3"
# Built pk3s are cached in $WORK/pk3cache and reused while their key matches. The key covers every repo file
# outside the QC, docs, CI and the mac app (tracked, modified and untracked), the base package's pk3s and
# levelshots, the numpy/pillow pins and the builder's arguments.
# ponytail: one key for all builders, so any asset or tool change rebuilds them all; per-pk3 inputs like CI's
# cache keys if that gets slow.
CACHE="$WORK/pk3cache"
LOCAL=()   # overlays made here, checked against the workflow's list below
mkdir -p "$CACHE"
EXCL=(':!docs' ':!source/qc_combat_decomp' ':!source/menu_qc' ':!source/mac' ':!.github' ':!*.md')
SRCKEY="$({
    echo "numpy=$NUMPY pillow=$PILLOW"
    git -C "$ROOT" ls-files -s -- . "${EXCL[@]}"
    git -C "$ROOT" diff HEAD -- . "${EXCL[@]}"
    (cd "$ROOT" && git ls-files -oz --exclude-standard -- . "${EXCL[@]}" ':!build' | xargs -0 sha256sum 2>/dev/null) || true
    find "$BASE" -type f \( -name '*.pk3' -o -path '*/levelshots/*' \) | sort | while IFS= read -r f; do
        echo "$f $(wc -c <"$f") $(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f")"
    done
} | sha256sum | cut -d' ' -f1)"
pk3() {   # pk3 <name> <python args...>: build zz_<name>.pk3 (or reuse the cached one) into the package
    local n=$1; shift
    local key; key="$(printf '%s\n' "$SRCKEY" "$@" | sha256sum | cut -d' ' -f1)"
    if [ -f "$CACHE/zz_$n.pk3" ] && [ "$(cat "$CACHE/zz_$n.key" 2>/dev/null)" = "$key" ]; then
        echo "  zz_$n.pk3 (cached)"
    else
        echo "  zz_$n.pk3"
        rm -f "$CACHE/zz_$n.key"
        "$VENV/bin/python" "$@" "$CACHE/zz_$n.pk3" >"$WORK/zz_$n.log" 2>&1 || { tail -20 "$WORK/zz_$n.log"; die "zz_$n.pk3 failed"; }
        echo "$key" >"$CACHE/zz_$n.key"
    fi
    cp "$CACHE/zz_$n.pk3" "$G/zz_$n.pk3"
    LOCAL+=("zz_$n.pk3")
}
pk3 bakovan "$M/van_bako/build_van_bako_pk3.py" "$B"
pk3 karts -I "$M/build_gokart_pk3.py" "$B"
pk3 gunnomip -I "$M/build_gunnomip_pk3.py" "$B"
pk3 minimap -I "$M/build_minimap_pk3.py" "$BASE/BakersfieldQuake"
pk3 pinklady -I "$M/build_pinklady_pk3.py" "$B"
pk3 kyle -I "$M/kyle_scissors/build_kyle_pk3.py" "$B"
pk3 rocketrider -I "$M/rocket_rider/build_rocketrider_pk3.py" "$B"
pk3 quakedesk -I "$M/quake_desk/build_quakedesk_pk3.py" "$B"
pk3 dn3shotgun -I "$M/dn3_shotgun/build_dn3shotgun_pk3.py" "$B"
pk3 dn3chaingun -I "$M/dn3_chaingun/build_dn3chaingun_pk3.py" "$B"
pk3 foreloco -I "$M/foreloco/build_foreloco_pk3.py" "$B"
pk3 triple_wheeled -I "$M/triple_wheeled/build_triple_wheeled_pk3.py" "$BASE/quake15/q15.pk3"
pk3 dn3fx -I "$M/dn3_fx/build_dn3fx_pk3.py" "$B"
pk3 loading -I "$M/loading_screen/build_loading_pk3.py" "$B"
pk3 cyrax -I "$M/cyrax/build_cyrax_pk3.py" "$B"
pk3 gunwheel -I "$M/gunwheel/build_gunwheel_pk3.py"
pk3 selected_sounds -I "$M/selected_sounds/build_selected_sounds_pk3.py"
pk3 console -I "$M/console/build_console_pk3.py"
# The rest of build-zip.yml's overlays: the base package predates them. Keep this list in step with the workflow.
pk3 wewcannon -I "$M/wew_cannon/build_wewcannon_pk3.py" "$B"
pk3 bakersfieldish -I "$M/build_bakersfieldish_pk3.py"
pk3 player_deaths -I "$M/build_player_deaths.py" --bakersfield-pk3 "$B" --skip-html --no-qc --out-pk3
pk3 robdrone -I "$M/build_robdrone_pk3.py"
pk3 jumppads -I "$M/build_jumppads_pk3.py"
pk3 m4 -I "$M/build_m4_pk3.py" "$B"
pk3 hitsound -I "$M/make_hitsound.py" --pk3
pk3 netsend_sentry -I "$M/disc_sentry/build_netsend_sentry_pk3.py" --out
pk3 levelshots -I "$M/build_levelshots_pk3.py" "$G" --pk3 "$G/zz_bakersfieldish.pk3"
# Pinned binaries with no builder in the repo, fetched like CI does.
fetch_pk3() {   # fetch_pk3 <name> <url> <sha256>
    local f="$CACHE/zz_$1.pk3"
    if echo "$3  $f" | sha256sum -c --quiet - >/dev/null 2>&1; then
        echo "  zz_$1.pk3 (pinned, cached)"
    else
        echo "  zz_$1.pk3 (pinned)"
        timeout 300 curl -fsSL --retry 3 -o "$f" "$2" || die "zz_$1.pk3 download failed"
        echo "$3  $f" | sha256sum -c --quiet - || die "zz_$1.pk3 sha256 mismatch"
    fi
    cp "$f" "$G/zz_$1.pk3"
    LOCAL+=("zz_$1.pk3")
}
fetch_pk3 netsend_disk https://bakersfield.larrywew.fun/pk3/zz_netsend_disk-e557aa2b.pk3 \
    e557aa2b2488481fb753296f8ca13124d873d0a0ceb65ccf2b1d7f77b745712d
fetch_pk3 hats https://bakersfield.larrywew.fun/pk3/zz_hats-5522f13f.pk3 \
    5522f13ffc5203c1a08807357b1932d4fa06ca03154b347f9e60c2a541955bb5
pk3 johnbird -I "$M/build_john_bird_pk3.py" --base-pk3 "$BASE/BakersfieldQuake/zz_johnbird.pk3" --out-pk3
# Every overlay the release workflow makes must be made here too, or a local change to its source never ships in the
# local build (the base only has the last release's copy).
for f in $(grep -o 'pk3cache/zz_[a-z0-9_]*\.pk3' "$ROOT/.github/workflows/build-zip.yml" | sort -u); do
    f="${f#pk3cache/}"
    printf '%s\n' "${LOCAL[@]}" | grep -qx "$f" \
        || echo "  WARNING: build-zip.yml makes $f but this script does not; using the last release's copy"
done
if [ -f "$G/maps/bakersfielddowntown.bsp" ]; then
    echo "  patch maps/bakersfielddowntown.bsp (Dagny's upstairs LAN party)"
    "${PYTHON:-python3}" -I "$M/patch_dagnys_lan_bsp.py" "$G/maps/bakersfielddowntown.bsp"
    echo "  patch maps/bakersfielddowntown.bsp (ForeLoco powerups)"
    "${PYTHON:-python3}" -I "$M/foreloco/patch_foreloco_maps.py" "$G/maps/bakersfielddowntown.bsp"
fi

step "fteqcc ${FTEQW_REF:0:7}${QC_HOST:+ on $QC_HOST}"
FTE="$WORK/src/fteqw-${FTEQW_REF:0:7}"
QCC="$FTE/engine/qclib/fteqcc.bin"
if [ -z "${QC_HOST:-}" ] && [ ! -x "$QCC" ]; then
    rm -rf "$FTE"
    git init -q "$FTE"
    git -C "$FTE" fetch -q --depth 1 https://github.com/fte-team/fteqw "$FTEQW_REF"
    git -C "$FTE" checkout -q FETCH_HEAD
    make -C "$FTE/engine/qclib" -j"$(getconf _NPROCESSORS_ONLN)" qcc CC=cc >"$WORK/fteqcc-build.log" 2>&1 ||
        { tail -20 "$WORK/fteqcc-build.log"; die "fteqcc build failed"; }
fi

step "compile QC"
# progs.src writes its output next to the sources, so compile a scratch copy.
QC="$WORK/qc"
rm -rf "$QC"; mkdir -p "$QC"
cp -R "$ROOT/source/qc_combat_decomp" "$ROOT/source/menu_qc" "$QC/"
if [ -n "${QC_HOST:-}" ]; then
    # Remote: build fteqcc once in ~/.cache on the host, compile a copy of the sources there, pull the results back.
    R=".cache/bq-qc"
    timeout 60 rsync -a --delete "$QC/" "$QC_HOST:$R/src/" || die "rsync to $QC_HOST failed"
    timeout 600 ssh "$QC_HOST" bash -s "$FTEQW_REF" <<'REMOTE' || die "fteqcc build on $QC_HOST failed"
set -e
F="$HOME/.cache/bq-qc/fteqw-${1:0:7}"
if [ ! -x "$F/engine/qclib/fteqcc.bin" ]; then
    echo "  building fteqcc ${1:0:7} on $(hostname)"
    rm -rf "$F"; git init -q "$F"
    git -C "$F" fetch -q --depth 1 https://github.com/fte-team/fteqw "$1"
    git -C "$F" checkout -q FETCH_HEAD
    make -C "$F/engine/qclib" -j"$(nproc)" qcc >"$F.log" 2>&1 || { tail -20 "$F.log"; exit 1; }
fi
REMOTE
    QCC="\$HOME/$R/fteqw-${FTEQW_REF:0:7}/engine/qclib/fteqcc.bin"
fi
qc() {   # qc <dir> <output> <dest> [flags...]
    local d=$1 o=$2 dest=$3; shift 3
    if [ -n "${QC_HOST:-}" ]; then
        local rd="$R/src/${d#"$QC"/}"
        timeout 120 ssh "$QC_HOST" "cd $rd && $QCC $* -srcfile progs.src" >"$d.log" 2>&1 \
            && timeout 60 rsync -a "$QC_HOST:$rd/$o" "$d/$o" || { grep -i error "$d.log" | head -20; die "$d failed on $QC_HOST"; }
    else
        (cd "$d" && "$QCC" "$@" -srcfile progs.src) >"$d.log" 2>&1 || { grep -i error "$d.log" | head -20; die "$d failed"; }
    fi
    cp "$d/$o" "$dest"
    echo "  $(basename "$dest") ($(grep -c warning "$d.log" || true) warnings)"
}
qc "$QC/qc_combat_decomp" progs.dat "$G/progs.dat"
qc "$QC/menu_qc" menu.dat "$G/menu.dat"
qc "$QC/qc_combat_decomp/csqc" progs.dat "$G/csprogs.dat"
# The decompiled system defs give another header CRC than the original CSQC; DarkPlaces finds CSQC globals by name,
# so stamp back the CRC of the quake15 csprogs.dat it was decompiled from (as source/mm_tools/build_csqc.py does).
"${PYTHON:-python3}" - "$OUT/quake15/csprogs.dat" "$G/csprogs.dat" <<'PY'
import struct, sys
crc = struct.unpack_from("<i", open(sys.argv[1], "rb").read(), 4)[0]
d = bytearray(open(sys.argv[2], "rb").read())
struct.pack_into("<i", d, 4, crc)
open(sys.argv[2], "wb").write(d)
print(f"  csprogs.dat header CRC set to {crc}")
PY

step "done: $OUT"
