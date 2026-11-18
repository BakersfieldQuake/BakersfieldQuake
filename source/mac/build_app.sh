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
#   WORK             build directory (default ~/build/bakoquake-mac); the deps prefix is kept there between runs
#
# Needs: Xcode, cmake, gh, git, curl.
set -euo pipefail

TAG="${1:?usage: $0 <release-tag>}"
REPO=GiggleHacks/BakersfieldQuake
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="${WORK:-$HOME/build/bakoquake-mac}"
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
ZIP="$WORK/dl/$TAG/BAKOQUAKE-macos-arm64.zip"
if [ ! -f "$ZIP" ]; then
    step "download $TAG"
    gh release download "$TAG" -R "$REPO" -p BAKOQUAKE-macos-arm64.zip -D "$WORK/dl/$TAG"
fi
step "unpack game data"
rm -rf "$WORK/game"
mkdir -p "$WORK/game"
ditto -x -k "$ZIP" "$WORK/game"
PKG="$WORK/game/BAKOQUAKE"
[ -d "$PKG/BakersfieldQuake" ] && [ -d "$PKG/quake15" ] || die "unexpected zip layout"

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

# --- assemble ------------------------------------------------------------------------------------------------
VERSION="$(echo "$TAG" | sed -n 's/^build-\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\).*/\1.\2.\3/p')"
[ -n "$VERSION" ] || VERSION="$(date -u +%Y.%m.%d)"   # custom tag without a build date
step "assemble BAKOQUAKE.app $VERSION"
rm -rf "$APP" "$DMG"
C="$APP/Contents"
mkdir -p "$C/MacOS" "$C/Frameworks" "$C/Resources/game/id1"
install -m 755 "$HERE/launcher.sh" "$C/MacOS/BAKOQUAKE"
install -m 755 "$ZD/zircon_beta_linux_sdl" "$C/MacOS/darkplaces-sdl"
install -m 755 "$ZD/zircon_beta_linux_dedicated_server" "$C/MacOS/darkplaces-dedicated"
# Real files plus their relative symlinks (libvorbis.dylib -> libvorbis.0.dylib etc.), so the names the engine
# dlopen()s and the @rpath install names both resolve to one file.
cp -a "$PREFIX"/lib/*.dylib "$C/Frameworks/"
cp -R "$PKG/BakersfieldQuake" "$PKG/quake15" "$PKG/tools" "$C/Resources/game/"

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

# --- gate: self-contained and macOS $MINOS ------------------------------------------------------------------
step "check Mach-O files"
bad=0
while IFS= read -r -d '' f; do
    file -b "$f" | grep -q Mach-O || continue
    minos="$(otool -l "$f" | awk '/LC_BUILD_VERSION/{b=1} b&&/minos/{print $2; exit}')"
    if [ "$(printf '%s\n%s\n' "$minos" "$MINOS" | sort -V | tail -1)" != "$MINOS" ]; then
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
sign "$C/MacOS/darkplaces-sdl" "$C/MacOS/darkplaces-dedicated"
sign "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

notarize() {   # notarize <file>
    step "notarize $(basename "$1")"
    xcrun notarytool submit "$1" "${NOTARY_AUTH[@]}" --wait --output-format json | tee "$1.notary.json"
    grep -q '"status" *: *"Accepted"' "$1.notary.json" || {
        id="$(sed -n 's/.*"id" *: *"\([^"]*\)".*/\1/p' "$1.notary.json" | head -1)"
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
fi

# --- DMG -----------------------------------------------------------------------------------------------------
step "DMG"
STAGE="$WORK/dmg"
rm -rf "$STAGE"; mkdir -p "$STAGE"
ditto "$APP" "$STAGE/BAKOQUAKE.app"
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
fi
step "done: $DMG"
ls -lh "$DMG"
