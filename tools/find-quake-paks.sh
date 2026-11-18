# BAKOQUAKE - find Quake's pak0.pak/pak1.pak and copy them into <package>/id1/ (Linux + macOS).
# Sourced by Play.sh and Start-Server.sh:  . tools/find-quake-paks.sh && bq_install_paks "$ROOT"
#
# Looks in the usual Steam / GOG / other-engine install folders first, then ~/Downloads. Wants an id1 folder
# holding BOTH pak0 and pak1 (any case): the 2021 rerelease ships only a different pak0.pak, so it is skipped.

BQ_PAK0_MD5=5906e5998fc3d896ddaf5e6a62e03abb   # Quake 1.06 pak0.pak
BQ_PAK1_MD5=d76b3e5678f0b64ac74ce5e340e6a685   # Quake pak1.pak (registered)

_bq_md5() {
    if command -v md5sum >/dev/null 2>&1; then md5sum "$1" | cut -d' ' -f1; else md5 -q "$1"; fi
}

# Print candidate Quake install folders, most likely first.
_bq_candidate_dirs() {
    local h="$HOME" s
    local steams=(
        "$h/.steam/steam"
        "$h/.local/share/Steam"
        "$h/.var/app/com.valvesoftware.Steam/.local/share/Steam"
        "$h/Library/Application Support/Steam"
    )
    for s in "${steams[@]}"; do
        echo "$s/steamapps/common/Quake"
        # Extra Steam library folders (other disks).
        if [ -f "$s/steamapps/libraryfolders.vdf" ]; then
            sed -n 's/^[[:space:]]*"path"[[:space:]]*"\(.*\)"[[:space:]]*$/\1/p' "$s/steamapps/libraryfolders.vdf" |
                while IFS= read -r lib; do echo "$lib/steamapps/common/Quake"; done
        fi
    done
    echo "$h/GOG Games/Quake"
    echo "$h/Games/Heroic/Quake"
    echo "$h/Games/quake"
    echo "$h/Games/Quake"
    echo "/usr/share/games/quake"
    echo "/usr/local/share/games/quake"
    # Other engines' own data folders.
    echo "$h/.darkplaces"
    echo "$h/.quakespasm"
    echo "$h/.vkquake"
    echo "$h/.ironwail"
    echo "$h/.quake"
    echo "/Applications/Quake"
}

# Given a folder, print the id1 directory under it that holds pak0+pak1 (any case), if any.
_bq_id1_with_paks() {
    local d="$1" id1
    [ -d "$d" ] || return 1
    for id1 in "$d" "$d"/[iI][dD]1; do
        [ -d "$id1" ] || continue
        case "$id1" in *[Rr]erelease*|*"Quake Enhanced"*) continue ;; esac
        if ls "$id1" 2>/dev/null | grep -qix 'pak0.pak' && ls "$id1" 2>/dev/null | grep -qix 'pak1.pak'; then
            echo "$id1"; return 0
        fi
    done
    return 1
}

_bq_pick() {   # case-insensitive file lookup inside a dir
    local f; f="$(ls "$1" 2>/dev/null | grep -ix "$2" | head -1)"; [ -n "$f" ] && echo "$1/$f"
}

bq_install_paks() {
    local root="$1" found="" d id1
    [ -f "$root/id1/pak0.pak" ] && return 0

    echo "Looking for your Quake pak0.pak / pak1.pak..."
    while IFS= read -r d; do
        [ "$d" = "$root" ] && continue
        if id1="$(_bq_id1_with_paks "$d")"; then found="$id1"; break; fi
    done < <(_bq_candidate_dirs)

    if [ -z "$found" ] && [ -d "$HOME/Downloads" ]; then
        echo "  not in the usual install folders; checking ~/Downloads..."
        while IFS= read -r p; do
            d="$(dirname "$p")"
            case "$d" in "$root"|"$root"/*) continue ;; esac
            if id1="$(_bq_id1_with_paks "$d")"; then found="$id1"; break; fi
        done < <(find "$HOME/Downloads" -maxdepth 5 -iname 'pak0.pak' 2>/dev/null)
    fi

    if [ -z "$found" ]; then
        echo "  no Quake install found." >&2
        return 1
    fi

    local p0 p1
    p0="$(_bq_pick "$found" pak0.pak)"; p1="$(_bq_pick "$found" pak1.pak)"
    echo "  found: $found"
    [ "$(_bq_md5 "$p0")" = "$BQ_PAK0_MD5" ] || echo "  warning: pak0.pak is not the Quake 1.06 version; trying it anyway."
    [ "$(_bq_md5 "$p1")" = "$BQ_PAK1_MD5" ] || echo "  warning: pak1.pak does not match the known registered pak1; trying it anyway."
    mkdir -p "$root/id1" &&
        cp "$p0" "$root/id1/pak0.pak" &&
        cp "$p1" "$root/id1/pak1.pak" &&
        echo "  copied pak0.pak + pak1.pak into $root/id1/"
}
