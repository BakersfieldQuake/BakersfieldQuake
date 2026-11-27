#!/bin/bash
# Update BAKOQUAKE.app main executable (Contents/MacOS/UpdateBAKOQUAKE). Installed by source/mac/build_app.sh.
# Finds sibling BAKOQUAKE.app, ensures the APFS game clone exists in ~/Library/Application Support/BAKOQUAKE/game,
# and runs bq-update --standalone.
set -u

UPD_APP="$(cd "$(dirname "$0")/../.." && pwd)"
APP_PARENT="$(dirname "$UPD_APP")"
USERDIR="$HOME/Library/Application Support/BAKOQUAKE"
mkdir -p "$USERDIR/id1"

alert() {
    osascript - "$1" "$2" <<'EOF' >/dev/null 2>&1
on run argv
    display alert (item 1 of argv) message (item 2 of argv) as critical
end run
EOF
}

MAIN_APP=""
for cand in "$APP_PARENT/BAKOQUAKE.app" "/Applications/BAKOQUAKE.app" "$HOME/Applications/BAKOQUAKE.app"; do
    if [ -x "$cand/Contents/MacOS/bq-update" ] && [ -d "$cand/Contents/Resources/game" ]; then
        MAIN_APP="$cand"
        break
    fi
done

if [ -z "$MAIN_APP" ]; then
    alert "BAKOQUAKE Not Found" "Could not find BAKOQUAKE.app next to Update BAKOQUAKE.app or in /Applications.

Drag both BAKOQUAKE and Update BAKOQUAKE into your Applications folder."
    exit 1
fi

BUNDLE_GAME="$MAIN_APP/Contents/Resources/game"
DATA="$USERDIR/game"
TAG="$(cat "$MAIN_APP/Contents/Resources/release-tag" 2>/dev/null)"

if [ "$(stat -f %d "$BUNDLE_GAME")" != "$(stat -f %d "$USERDIR")" ]; then
    alert "Move to Applications First" "Drag both BAKOQUAKE and Update BAKOQUAKE into your Applications folder before updating."
    exit 1
fi

if [ -n "$TAG" ] && [ "$(cat "$DATA/.bq/bundle-tag" 2>/dev/null)" != "$TAG" ]; then
    rm -rf "$DATA.new" "$DATA.old"
    if cp -cR "$BUNDLE_GAME" "$DATA.new" 2>/dev/null && mkdir -p "$DATA.new/.bq" \
            && echo "$TAG" >"$DATA.new/.bq/bundle-tag"; then
        { [ ! -e "$DATA" ] || mv "$DATA" "$DATA.old"; } && mv "$DATA.new" "$DATA"
    fi
    rm -rf "$DATA.new" "$DATA.old"
fi

if [ ! -d "$DATA/BakersfieldQuake" ]; then
    alert "BAKOQUAKE Updater" "Could not initialize game data in:

$DATA"
    exit 1
fi

export SSL_CERT_FILE=/etc/ssl/cert.pem
UPD=("$MAIN_APP/Contents/MacOS/bq-update" --standalone --root "$DATA" --platform macos-app)
# A local build (make build, tag local-*) is newer than any DMG; never send it to download one.
[ -f "$MAIN_APP/Contents/Resources/mac-inputs" ] && [ "${TAG#local-}" = "$TAG" ] && UPD+=(--bundle-mac-inputs "$MAIN_APP/Contents/Resources/mac-inputs")
[ -n "${BQ_MANIFEST_URL:-}" ] && UPD+=(--manifest-url "$BQ_MANIFEST_URL")
[ -n "${BQ_FALLBACK_URL+x}" ] && UPD+=(--fallback-url "$BQ_FALLBACK_URL")
exec "${UPD[@]}"
