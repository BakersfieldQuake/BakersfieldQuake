#!/bin/bash
# Build the signed, notarized, stapled BAKOQUAKE.app and BAKOQUAKE-macos-arm64.dmg (Apple Silicon).
#
#   source/mac/build_app.sh <release-tag>
#
# CI runs this (the macos job in .github/workflows/build-zip.yml) and uploads the DMG. Release DMGs come only from
# CI; run it locally with SKIP_NOTARIZE=1 to debug the script.
#
# Game data comes from that release's BAKOQUAKE-macos-arm64.zip. The engine (Zircon) and every dylib it loads are
# built from pinned sources for macOS 13.0+, so nothing in the bundle comes from Homebrew. Homebrew bottles target
# the build machine's macOS and would raise the app's minimum OS.
#
# Env:
#   SIGN_ID          SHA-1 of the "Developer ID Application" identity (default: first one in the keychain)
#   NOTARY_ENV       file to source for APPLE_ID, APPLE_TEAM_ID, APPLE_APP_SPECIFIC_PASSWORD (notarytool credentials)
#   NOTARY_PROFILE   or: a notarytool keychain profile (xcrun notarytool store-credentials)
#                    One of the two is required unless SKIP_NOTARIZE=1.
#   SKIP_NOTARIZE=1  build and sign only (for local iteration)
#   UPLOAD=1         upload the DMG to the release after notarizing
#   NO_DMG=1         stop after the app (local runs)
#   PKG_DIR          an assembled BAKOQUAKE package to bundle instead of the release's game data (make app); the tag
#                    then only names the build
#   WORK             build directory (default <repo>/build, gitignored); the deps prefix is kept there between runs
#   PYTHON           Python that freezes the updater (default python3). Its libraries go into Contents/MacOS/bq-update,
#                    so it must target macOS 13.0 or older (python.org / actions/setup-python builds do; Homebrew's
#                    does not). The script checks.
#
# Needs: Xcode, cmake, gh, git, curl, Python 3.
set -euo pipefail

TAG="${1:?usage: $0 <release-tag>}"
REPO=BakersfieldQuake/BakersfieldQuake
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="${WORK:-$ROOT/build}"
MINOS=13.0
BUNDLE_ID=com.gigglehacks.bakoquake

ZIRCON_REPO=https://github.com/rgr4y/zircon-darkplaces
ZIRCON_REF=e19de67085f6c1602a43f4cf68ccc210a1033fad
SDL_TAG=release-2.32.10
OGG_TAG=v1.3.6
VORBIS_TAG=v1.3.7
FREETYPE_TAG=VER-2-15-0
JPEG_TAG=3.2.1

PREFIX="$WORK/prefix-$MINOS"
SRC="$WORK/src"
OUT="$WORK/out"
APP="$OUT/BAKOQUAKE.app"
UPD_APP="$OUT/Update BAKOQUAKE.app"
DMG="$OUT/BAKOQUAKE-macos-arm64.dmg"
NPROC="$(sysctl -n hw.ncpu)"
export MACOSX_DEPLOYMENT_TARGET=$MINOS

step() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[ "$(uname -m)" = arm64 ] || die "build on Apple Silicon"
# shellcheck source=/dev/null
[ -n "${NOTARY_ENV:-}" ] && . "$NOTARY_ENV"
if [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ] && [ -n "${APPLE_APP_SPECIFIC_PASSWORD:-}" ]; then
    NOTARY_AUTH=(--apple-id "$APPLE_ID" --team-id "$APPLE_TEAM_ID" --password "$APPLE_APP_SPECIFIC_PASSWORD")
elif [ -n "${NOTARY_PROFILE:-}" ]; then
    NOTARY_AUTH=(--keychain-profile "$NOTARY_PROFILE")
elif [ "${SKIP_NOTARIZE:-0}" != 1 ]; then
    die "set NOTARY_ENV or NOTARY_PROFILE for notarytool, or SKIP_NOTARIZE=1"
fi
SIGN_ID="${SIGN_ID:-$(security find-identity -v -p codesigning | awk '/"Developer ID Application/ {print $2; exit}')}"
[ -n "$SIGN_ID" ] || die "no Developer ID Application identity in the keychain"
echo "signing identity: $SIGN_ID"
mkdir -p "$WORK" "$SRC" "$OUT"

# --- game data -----------------------------------------------------------------------------------------------
if [ -n "${PKG_DIR:-}" ]; then
    PKG="$PKG_DIR"
    step "game data from $PKG"
else
    step "download $TAG"
    # gh writes straight to the target name, so download into a fresh directory that is removed afterwards.
    rm -rf "$WORK/dl" "$WORK/game"
    gh release download "$TAG" -R "$REPO" -p BAKOQUAKE-macos-arm64.zip -D "$WORK/dl"
    step "unpack game data"
    mkdir -p "$WORK/game"
    ditto -x -k "$WORK/dl/BAKOQUAKE-macos-arm64.zip" "$WORK/game"
    rm -rf "$WORK/dl"
    PKG="$WORK/game/BAKOQUAKE"
fi
[ -d "$PKG/BakersfieldQuake" ] && [ -d "$PKG/quake15" ] || die "unexpected game data layout in $PKG"

# --- dependencies (cached in $PREFIX) ------------------------------------------------------------------------
fetch() {   # fetch <name> <repo-url> <tag>
    local d="$SRC/$1-$3"
    [ -d "$d" ] || git -c advice.detachedHead=false clone -q --depth 1 -b "$3" "$2" "$d"
    echo "$d"
}
cmake_build() {   # cmake_build <name> <repo-url> <tag> [cmake args...]
    local name=$1 url=$2 tag=$3; shift 3
    local stamp="$PREFIX/.built-$name-$tag"
    [ -f "$stamp" ] && { echo "$name $tag: cached"; return; }
    step "build $name $tag"
    local d; d="$(fetch "$name" "$url" "$tag")"
    rm -rf "$d/_build"
    cmake -S "$d" -B "$d/_build" -G "Unix Makefiles" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$PREFIX" \
        -DCMAKE_PREFIX_PATH="$PREFIX" \
        -DCMAKE_IGNORE_PREFIX_PATH="/opt/homebrew;/usr/local" \
        -DCMAKE_OSX_DEPLOYMENT_TARGET=$MINOS \
        -DCMAKE_OSX_ARCHITECTURES=arm64 \
        -DCMAKE_INSTALL_NAME_DIR=@rpath \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DBUILD_SHARED_LIBS=ON \
        "$@" >"$d/_build.log" 2>&1 || { tail -30 "$d/_build.log"; die "$name configure failed"; }
    cmake --build "$d/_build" -j"$NPROC" >>"$d/_build.log" 2>&1 || { tail -30 "$d/_build.log"; die "$name build failed"; }
    cmake --install "$d/_build" >>"$d/_build.log" 2>&1 || die "$name install failed"
    touch "$stamp"
}
mkdir -p "$PREFIX"
cmake_build sdl2 https://github.com/libsdl-org/SDL $SDL_TAG -DSDL_TEST=OFF -DSDL_STATIC=OFF
cmake_build ogg https://github.com/xiph/ogg $OGG_TAG -DINSTALL_DOCS=OFF
cmake_build vorbis https://github.com/xiph/vorbis $VORBIS_TAG
cmake_build freetype https://github.com/freetype/freetype $FREETYPE_TAG \
    -DFT_DISABLE_PNG=ON -DFT_DISABLE_BROTLI=ON -DFT_DISABLE_BZIP2=ON -DFT_DISABLE_HARFBUZZ=ON -DFT_REQUIRE_ZLIB=ON
# Default options = the jpeg6b API: libjpeg.62.dylib, which is the only name and ABI the engine accepts.
cmake_build jpeg https://github.com/libjpeg-turbo/libjpeg-turbo $JPEG_TAG -DENABLE_STATIC=OFF -DWITH_TURBOJPEG=OFF

# --- engine --------------------------------------------------------------------------------------------------
step "build Zircon ${ZIRCON_REF:0:7}"
ZD="$SRC/zircon"
[ -d "$ZD" ] || git clone -q "$ZIRCON_REPO" "$ZD"
git -C "$ZD" fetch -q origin
git -C "$ZD" -c advice.detachedHead=false checkout -q "$ZIRCON_REF"
make -C "$ZD" -f makefile clean >/dev/null 2>&1 || true
SDLC="$PREFIX/bin/sdl2-config"
# - Cocoa: vid_sdl.c uses CFSTR; source-built sdl2-config --libs, unlike Homebrew's, does not add it.
# - rpath: the engine dlopen()s bare names (libjpeg.62.dylib...), and dyld looks those up in the main executable's
#   LC_RPATH too, so the bundled Frameworks/ are found without DYLD_* variables or entitlements.
SDLLIBS="$("$SDLC" --libs) -framework Cocoa -Wl,-rpath,@executable_path/../Frameworks"
make -C "$ZD" -f makefile -j"$NPROC" SDL_CONFIG="$SDLC" SDLCONFIG_STATICLIBS="$SDLLIBS" \
    sdl-release sv-release >"$WORK/zircon-build.log" 2>&1 || { tail -30 "$WORK/zircon-build.log"; die "engine build failed"; }

# --- updater -------------------------------------------------------------------------------------------------
# tools/bq_update.py frozen into one Mach-O, so players need no Python (without the Command Line Tools,
# /usr/bin/python3 is only an installer stub). PyInstaller signs the libraries it embeds with SIGN_ID and the hardened
# runtime, which library validation needs when they are unpacked at run time; the outer binary is signed below.
PYINSTALLER=6.22.3
step "freeze the updater (PyInstaller $PYINSTALLER)"
PYI="$WORK/pyi"
rm -rf "$PYI/build" "$PYI/dist"
"${PYTHON:-python3}" -m venv "$PYI/venv-$PYINSTALLER"
"$PYI/venv-$PYINSTALLER/bin/python" -m pip install --quiet --disable-pip-version-check "pyinstaller==$PYINSTALLER"
"$PYI/venv-$PYINSTALLER/bin/python" -m PyInstaller --onefile --console --noupx --name bq-update \
    --hidden-import tkinter --hidden-import tkinter.ttk \
    --codesign-identity "$SIGN_ID" --distpath "$PYI/dist" --workpath "$PYI/build" --specpath "$PYI" \
    "$ROOT/tools/bq_update.py" >"$PYI/pyinstaller.log" 2>&1 || { tail -30 "$PYI/pyinstaller.log"; die "freeze failed"; }
# The check-Mach-O gate below can't see inside the onefile archive: check what went into it here.
"$PYI/venv-$PYINSTALLER/bin/python" - "$PYI/build/bq-update/PKG-00.toc" "$MINOS" <<'PY' || die "updater embeds libraries newer than macOS $MINOS"
import ast, subprocess, sys
toc, want = ast.literal_eval(open(sys.argv[1]).read())[2], tuple(map(int, sys.argv[2].split(".")))
bad = 0
for name, src, kind in toc:
    if kind not in ("BINARY", "EXTENSION"):
        continue
    words = subprocess.run(["otool", "-l", src], capture_output=True, text=True).stdout.split()
    # LC_BUILD_VERSION says "minos"; the older LC_VERSION_MIN_MACOSX says "version".
    minos = "?"
    for cmd, key in (("LC_BUILD_VERSION", "minos"), ("LC_VERSION_MIN_MACOSX", "version")):
        if cmd in words:
            rest = words[words.index(cmd):]
            minos = rest[rest.index(key) + 1]
            break
    if minos == "?" or tuple(map(int, minos.split("."))) > want:
        print(f"  {name}: minos {minos}")
        bad = 1
sys.exit(bad)
PY
"$PYI/dist/bq-update" --help >/dev/null || die "frozen updater does not run"
"$PYI/dist/bq-update" --version >/dev/null || die "frozen updater --version failed"

# --- assemble ------------------------------------------------------------------------------------------------
VERSION="$(echo "$TAG" | sed -n 's/^v\([0-9][0-9.]*\).*/\1/p; s/^build-\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\).*/\1.\2.\3/p' | head -1)"
[ -n "$VERSION" ] || VERSION="$(date -u +%Y.%m.%d)"   # custom tag without a version or build date
step "assemble BAKOQUAKE.app $VERSION"
rm -rf "$APP" "$UPD_APP" "$DMG"
C="$APP/Contents"
mkdir -p "$C/MacOS" "$C/Frameworks" "$C/Resources/game/id1"
install -m 755 "$HERE/launcher.sh" "$C/MacOS/BAKOQUAKE"
install -m 755 "$ZD/zircon_beta_linux_sdl" "$C/MacOS/darkplaces-sdl"
install -m 755 "$ZD/zircon_beta_linux_dedicated_server" "$C/MacOS/darkplaces-dedicated"
install -m 755 "$PYI/dist/bq-update" "$C/MacOS/bq-update"
# The launcher re-clones the game data into Application Support when this changes (a new DMG was installed),
# and mac-inputs lets bq-update detect when a newer release shipped a new engine/bundle requiring a DMG update.
echo "$TAG" >"$C/Resources/release-tag"
if [ -z "${MAC_INPUTS:-}" ] && command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    MAC_INPUTS="$(cd "$ROOT" && git ls-files -z source/mac tools/bq_update.py source/icons/bakoquake-256.png source/icons/bakoquake-update-256.png | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')"
fi
echo "${MAC_INPUTS:-$TAG}" >"$C/Resources/mac-inputs"
# Real files plus their relative symlinks (libvorbis.dylib -> libvorbis.0.dylib etc.), so the names the engine
# dlopen()s and the @rpath install names both resolve to one file.
cp -a "$PREFIX"/lib/*.dylib "$C/Frameworks/"
cp -R "$PKG/BakersfieldQuake" "$PKG/quake15" "$PKG/tools" "$C/Resources/game/"
# Updater state for the launcher's clone of game/ (see launcher.sh): it lists the files the bundle ships, so the first
# update also removes those a newer release dropped. Build 0 means every file is compared.
mkdir -p "$C/Resources/game/.bq"
(cd "$C/Resources/game" && find BakersfieldQuake quake15 tools -type f | LC_ALL=C sort) |
    "$PYI/venv-$PYINSTALLER/bin/python" -c 'import json, sys; json.dump({"build": 0, "managed": sys.stdin.read().splitlines()}, sys.stdout)' \
    >"$C/Resources/game/.bq/state.json"

ICONSET="$WORK/bakoquake.iconset"
rm -rf "$ICONSET"; mkdir -p "$ICONSET"
# ponytail: upscaled from the 256 px source; replace with real 512/1024 art when it exists.
for s in 16 32 128 256 512; do
    sips -z $s $s "$ROOT/source/icons/bakoquake-256.png" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
    sips -z $((s*2)) $((s*2)) "$ROOT/source/icons/bakoquake-256.png" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$C/Resources/bakoquake.icns"

cat >"$C/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key><string>$BUNDLE_ID</string>
    <key>CFBundleName</key><string>BAKOQUAKE</string>
    <key>CFBundleDisplayName</key><string>BAKOQUAKE</string>
    <key>CFBundleExecutable</key><string>BAKOQUAKE</string>
    <key>CFBundleIconFile</key><string>bakoquake</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>CFBundleVersion</key><string>$VERSION</string>
    <key>LSMinimumSystemVersion</key><string>$MINOS</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>LSApplicationCategoryType</key><string>public.app-category.action-games</string>
</dict>
</plist>
EOF
plutil -lint "$C/Info.plist" >/dev/null

# Assemble companion Update BAKOQUAKE.app (shares the signed updater inside BAKOQUAKE.app, with its own icon).
UC="$UPD_APP/Contents"
mkdir -p "$UC/MacOS" "$UC/Resources"
install -m 755 "$HERE/update_launcher.sh" "$UC/MacOS/UpdateBAKOQUAKE"
UPD_ICONSET="$WORK/bakoquake-update.iconset"
rm -rf "$UPD_ICONSET"; mkdir -p "$UPD_ICONSET"
UPD_PNG="$ROOT/source/icons/bakoquake-update-256.png"
[ -f "$UPD_PNG" ] || UPD_PNG="$ROOT/source/icons/bakoquake-256.png"
for s in 16 32 128 256 512; do
    sips -z $s $s "$UPD_PNG" --out "$UPD_ICONSET/icon_${s}x${s}.png" >/dev/null
    sips -z $((s*2)) $((s*2)) "$UPD_PNG" --out "$UPD_ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$UPD_ICONSET" -o "$UC/Resources/bakoquake-update.icns"
cat >"$UC/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key><string>$BUNDLE_ID.updater</string>
    <key>CFBundleName</key><string>Update BAKOQUAKE</string>
    <key>CFBundleDisplayName</key><string>Update BAKOQUAKE</string>
    <key>CFBundleExecutable</key><string>UpdateBAKOQUAKE</string>
    <key>CFBundleIconFile</key><string>bakoquake-update</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>CFBundleVersion</key><string>$VERSION</string>
    <key>LSMinimumSystemVersion</key><string>$MINOS</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>LSApplicationCategoryType</key><string>public.app-category.utilities</string>
</dict>
</plist>
EOF
plutil -lint "$UC/Info.plist" >/dev/null

# --- gate: self-contained and macOS $MINOS ------------------------------------------------------------------
step "check Mach-O files"
bad=0
while IFS= read -r -d '' f; do
    file -b "$f" | grep -q Mach-O || continue
    minos="$(otool -l "$f" | awk '/LC_BUILD_VERSION/{b=1} b&&/minos/{print $2; exit} /LC_VERSION_MIN_MACOSX/{v=1} v&&/version/{print $2; exit}')"
    if [ -z "$minos" ]; then
        echo "  ${f#"$APP"/}: missing LC_BUILD_VERSION/LC_VERSION_MIN_MACOSX minos"; bad=1
    elif [ "$(printf '%s\n%s\n' "$minos" "$MINOS" | sort -V | tail -1)" != "$MINOS" ]; then
        echo "  ${f#"$APP"/}: minos $minos > $MINOS"; bad=1
    fi
    if otool -L "$f" | tail -n +2 | grep -E '/opt/homebrew|/usr/local|/Users/'; then
        echo "  ${f#"$APP"/}: links outside the bundle"; bad=1
    fi
done < <(find "$APP" -type f -print0)
while IFS= read -r l; do
    case "$(readlink "$l")" in /*|*..*) echo "  $l: symlink leaves Frameworks"; bad=1 ;; esac
done < <(find "$APP" -type l)
[ $bad = 0 ] || die "bundle is not self-contained"
echo "  ok"

# --- sign (inside out, no --deep) ----------------------------------------------------------------------------
step "sign"
sign() { codesign --force --timestamp --options runtime -s "$SIGN_ID" "$@"; }
find "$C/Frameworks" -type f -name '*.dylib' -print0 | while IFS= read -r -d '' f; do sign "$f"; done
sign "$C/MacOS/darkplaces-sdl" "$C/MacOS/darkplaces-dedicated" "$C/MacOS/bq-update"
sign "$APP"
sign "$UPD_APP"
codesign --verify --deep --strict --verbose=2 "$APP"
codesign --verify --deep --strict --verbose=2 "$UPD_APP"

notarize() {   # notarize <file>
    step "notarize $(basename "$1")"
    # Text output, so the upload progress and status polling show in the log as they happen.
    xcrun notarytool submit "$1" "${NOTARY_AUTH[@]}" --wait | tee "$1.notary.log"
    grep -q '^ *status: Accepted' "$1.notary.log" || {
        id="$(sed -n 's/^ *id: *\([0-9a-f-]*\).*/\1/p' "$1.notary.log" | head -1)"
        [ -n "$id" ] && xcrun notarytool log "$id" "${NOTARY_AUTH[@]}"
        die "notarization failed"
    }
}

if [ "${SKIP_NOTARIZE:-0}" != 1 ]; then
    ditto -c -k --keepParent "$APP" "$OUT/app.zip"
    notarize "$OUT/app.zip"
    rm -f "$OUT/app.zip"
    xcrun stapler staple "$APP"
    spctl -a -vvv -t exec "$APP"

    ditto -c -k --keepParent "$UPD_APP" "$OUT/upd_app.zip"
    notarize "$OUT/upd_app.zip"
    rm -f "$OUT/upd_app.zip"
    xcrun stapler staple "$UPD_APP"
    spctl -a -vvv -t exec "$UPD_APP"
fi

# --- DMG -----------------------------------------------------------------------------------------------------
if [ "${NO_DMG:-0}" = 1 ]; then
    step "done: $APP (no DMG)"
    exit 0
fi
step "DMG"
STAGE="$WORK/dmg"
rm -rf "$STAGE"; mkdir -p "$STAGE"
ditto "$APP" "$STAGE/BAKOQUAKE.app"
ditto "$UPD_APP" "$STAGE/Update BAKOQUAKE.app"
ln -s /Applications "$STAGE/Applications"
# Mostly already-compressed pk3s, so ULFO (lzfse) rather than anything heavier.
hdiutil create -volname BAKOQUAKE -srcfolder "$STAGE" -fs APFS -format ULFO "$DMG"
rm -rf "$STAGE"
codesign --force --timestamp -s "$SIGN_ID" "$DMG"
if [ "${SKIP_NOTARIZE:-0}" != 1 ]; then
    notarize "$DMG"
    xcrun stapler staple "$DMG"
    spctl -a -vvv -t open --context context:primary-signature "$DMG"
fi

if [ "${UPLOAD:-0}" = 1 ]; then
    step "upload to $TAG"
    gh release upload "$TAG" "$DMG" -R "$REPO" --clobber
    rm -f "$OUT/manifest-macos-app.json"
    if gh release download "$TAG" -R "$REPO" -p manifest-macos-app.json -D "$OUT" >/dev/null 2>&1; then
        DMG_SIZE="$("${PYTHON:-python3}" -c 'import os,sys; print(os.path.getsize(sys.argv[1]))' "$DMG")"
        DMG_SHA256="$(shasum -a 256 "$DMG" | awk '{print $1}')"
        "${PYTHON:-python3}" -I "$ROOT/source/ci/make_manifest.py" \
            --patch-manifest "$OUT/manifest-macos-app.json" \
            --output "$OUT/manifest-macos-app.json" \
            --mac-inputs "$(cat "$C/Resources/mac-inputs")" \
            --dmg-url "https://github.com/$REPO/releases/download/$TAG/BAKOQUAKE-macos-arm64.dmg" \
            --dmg-vps-url "https://bakersfield.larrywew.fun/updates/BAKOQUAKE-macos-arm64.dmg" \
            --dmg-size "$DMG_SIZE" \
            --dmg-sha256 "$DMG_SHA256"
        gh release upload "$TAG" "$OUT/manifest-macos-app.json" -R "$REPO" --clobber
    fi
fi
step "done: $DMG"
ls -lh "$DMG"
