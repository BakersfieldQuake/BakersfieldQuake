# BAKOQUAKE - application menu and desktop shortcuts (Linux; does nothing on macOS).
# Sourced by Play.sh and Start-Server.sh:  . tools/install-shortcuts.sh && bq_install_shortcuts "$ROOT"
# Or run directly:                          bash tools/install-shortcuts.sh <package folder>
#
# Writes ~/.local/share/applications/bakoquake.desktop and bakoquake-server.desktop (the server entry has a
# "Stop server" action) and a copy of bakoquake.desktop on the desktop. The package folder is recorded in
# ~/.local/share/bakoquake/shortcut-root, so a normal launch only reads that file; the shortcuts are rewritten when
# the package moves. Never fails the launch: every error is ignored and retried next time.

# Desktop Entry spec, "string" values: \ becomes \\ (Path=, Icon=).
_bq_desktop_string() {
    local s="${1//\\/\\\\}"
    printf '%s' "$s"
}

# Desktop Entry spec, one quoted Exec argument: escape " ` $ \ for the quoting rule, then apply the string rule on
# top (so a literal \ ends up as \\\\), and double % so it is not read as a field code.
_bq_desktop_exec_arg() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//\`/\\\`}"
    s="${s//\$/\\\$}"
    s="${s//\\/\\\\}"
    s="${s//%/%%}"
    printf '"%s"' "$s"
}

bq_install_shortcuts() (
    root="${1:-}"
    exec 2>/dev/null   # a launcher's console is no place for these; failures just retry next launch
    [ "$(uname)" = Linux ] || exit 0
    [ -n "$root" ] && [ -n "${HOME:-}" ] || exit 0
    case "$root" in *$'\n'*|*$'\r'*) exit 0 ;; esac   # can't be written into a .desktop line

    data="${XDG_DATA_HOME:-$HOME/.local/share}"
    marker="$data/bakoquake/shortcut-root"
    old=""
    [ -f "$marker" ] && IFS= read -r old <"$marker"
    [ "$old" = "$root" ] && exit 0

    apps="$data/applications"
    mkdir -p "$apps" "$data/bakoquake" || exit 1

    # bash runs the scripts, so the shortcuts work even if Play.sh lost its exec bit (zips made on Windows).
    play="bash $(_bq_desktop_exec_arg "$root/Play.sh")"
    server="bash $(_bq_desktop_exec_arg "$root/Start-Server.sh")"
    path="$(_bq_desktop_string "$root")"
    icon="$(_bq_desktop_string "$root/tools/bakoquake-256.png")"

    tmp="$apps/.bakoquake.desktop.$$"
    cat >"$tmp" <<EOF || { rm -f "$tmp"; exit 1; }
[Desktop Entry]
Type=Application
Version=1.0
Name=BAKOQUAKE
GenericName=First-person shooter
Comment=Play BAKOQUAKE (joins a LAN server if one is up)
Exec=$play
Path=$path
Icon=$icon
Terminal=false
Categories=Game;ActionGame;
Keywords=quake;bakersfield;fps;
EOF
    mv -f "$tmp" "$apps/bakoquake.desktop" || { rm -f "$tmp"; exit 1; }

    tmp="$apps/.bakoquake-server.desktop.$$"
    cat >"$tmp" <<EOF || { rm -f "$tmp"; exit 1; }
[Desktop Entry]
Type=Application
Version=1.0
Name=BAKOQUAKE Server
GenericName=First-person shooter server
Comment=Host a BAKOQUAKE LAN server and join it
Exec=$server
Path=$path
Icon=$icon
Terminal=false
Categories=Game;ActionGame;
Keywords=quake;bakersfield;fps;server;
Actions=stop;

[Desktop Action stop]
Name=Stop server
Exec=$server stop
EOF
    mv -f "$tmp" "$apps/bakoquake-server.desktop" || { rm -f "$tmp"; exit 1; }
    chmod +x "$apps/bakoquake.desktop" "$apps/bakoquake-server.desktop" 2>/dev/null

    # Desktop copy of the Play entry. xdg-user-dir prints $HOME when no desktop folder is set: never write there.
    desk=""
    command -v xdg-user-dir >/dev/null 2>&1 && desk="$(xdg-user-dir DESKTOP 2>/dev/null)"
    if [ -z "$desk" ] || [ "$desk" = "$HOME" ] || [ ! -d "$desk" ]; then
        desk=""
        [ -d "$HOME/Desktop" ] && desk="$HOME/Desktop"
    fi
    if [ -n "$desk" ] && cp -f "$apps/bakoquake.desktop" "$desk/bakoquake.desktop" 2>/dev/null; then
        chmod +x "$desk/bakoquake.desktop" 2>/dev/null
        # GNOME (DING) launches desktop files only when trusted; needs the session bus, so it may fail outside one.
        command -v gio >/dev/null 2>&1 && gio set "$desk/bakoquake.desktop" metadata::trusted true >/dev/null 2>&1
    fi

    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$apps" >/dev/null 2>&1

    printf '%s\n' "$root" >"$marker"
    exit 0
)

# Run directly (not sourced): bash tools/install-shortcuts.sh <package folder>
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    bq_install_shortcuts "${1:-$(cd "$(dirname "$0")/.." && pwd -P)}"
fi
