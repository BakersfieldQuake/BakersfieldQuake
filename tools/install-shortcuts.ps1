# BAKOQUAKE - Start Menu and Desktop shortcuts (Windows).
# Called by Play.cmd and Start Server.cmd:  powershell -NoProfile -ExecutionPolicy Bypass -File tools\install-shortcuts.ps1 -Root <package>
#
# Creates (or overwrites) for the current user:
#   Start Menu\Programs\BAKOQUAKE\BAKOQUAKE.lnk         PLAY BAKERSFIELDQUAKE.exe (else Play.cmd, minimized)
#   Start Menu\Programs\BAKOQUAKE\BAKOQUAKE Server.lnk  Start Server.cmd
#   Start Menu\Programs\BAKOQUAKE\Update BAKOQUAKE.lnk  Update.exe (else tools\bq-update.exe --standalone)
#   Desktop\BAKOQUAKE.lnk                               same target as the Start Menu one
#   Desktop\Update BAKOQUAKE.lnk                        same target as the Start Menu updater one
# Exit code 0 = all shortcuts written. The launchers then record the package folder in
# %LOCALAPPDATA%\BAKOQUAKE\shortcut-root.txt (this script only creates that folder) and skip this script until the
# package moves. Any other exit code: the launcher tries again next time; the game starts either way.
param([Parameter(Mandatory = $true)][string]$Root)

$ErrorActionPreference = 'Stop'
try {
    $Root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')

    $exe = Join-Path $Root 'PLAY BAKERSFIELDQUAKE.exe'
    $play = Join-Path $Root 'Play.cmd'
    $server = Join-Path $Root 'Start Server.cmd'
    $updateExe = Join-Path $Root 'Update.exe'
    $bqUpdateExe = Join-Path $Root 'tools\bq-update.exe'
    if (Test-Path -LiteralPath $exe) {
        $playTarget = $exe; $playStyle = 1          # the exe runs Play.cmd without a console window
    } elseif (Test-Path -LiteralPath $play) {
        $playTarget = $play; $playStyle = 7         # 7 = minimized: only a console flash in the taskbar
    } else {
        exit 1                                      # not a package root (e.g. the dev tree): make nothing
    }
    $ico = Join-Path $Root 'tools\bakoquake.ico'
    $icon = if (Test-Path -LiteralPath $ico) { "$ico,0" } else { "$playTarget,0" }
    $updIco = Join-Path $Root 'tools\bakoquake-update.ico'
    $updIcon = if (Test-Path -LiteralPath $updIco) { "$updIco,0" } elseif (Test-Path -LiteralPath $updateExe) { "$updateExe,0" } else { $icon }

    $wsh = New-Object -ComObject WScript.Shell
    $shell = New-Object -ComObject Shell.Application
    function New-Shortcut([string]$Path, [string]$Target, [int]$Style, [string]$Description, [string]$Arguments = '', [string]$IconLoc = $icon) {
        $lnk = $wsh.CreateShortcut($Path)
        $lnk.TargetPath = $Target
        $lnk.Arguments = $Arguments
        $lnk.WorkingDirectory = $Root
        $lnk.WindowStyle = $Style
        $lnk.IconLocation = $IconLoc
        $lnk.Description = $Description
        $lnk.Save()
        # WScript.Shell squeezes paths through the ANSI code page (an L-stroke in a folder name becomes a plain L and the
        # shortcut breaks). Shell.Application's ShellLinkObject keeps them Unicode, so set the paths again with it.
        $link = $shell.NameSpace((Split-Path -LiteralPath $Path)).ParseName((Split-Path -Leaf $Path)).GetLink
        $link.Path = $Target
        $link.Arguments = $Arguments
        $link.WorkingDirectory = $Root
        $link.SetIconLocation(($IconLoc -replace ',0$', ''), 0)
        $link.Save()
    }

    # Per-user folders, resolved by the shell (follows OneDrive/redirected Desktops).
    $menu = Join-Path ([Environment]::GetFolderPath('Programs')) 'BAKOQUAKE'
    $desktop = [Environment]::GetFolderPath('Desktop')
    New-Item -ItemType Directory -Force -Path $menu | Out-Null

    New-Shortcut (Join-Path $menu 'BAKOQUAKE.lnk') $playTarget $playStyle 'Play BAKOQUAKE'
    if (Test-Path -LiteralPath $server) {
        New-Shortcut (Join-Path $menu 'BAKOQUAKE Server.lnk') $server 1 'Host a BAKOQUAKE LAN server and join it'
    }
    $updTarget = $null
    $updArgs = ''
    if (Test-Path -LiteralPath $updateExe) {
        $updTarget = $updateExe
    } elseif (Test-Path -LiteralPath $bqUpdateExe) {
        $updTarget = $bqUpdateExe
        $updArgs = "--standalone --root `"$Root`""
    }
    if ($updTarget) {
        New-Shortcut (Join-Path $menu 'Update BAKOQUAKE.lnk') $updTarget 1 'Check for and install BAKOQUAKE updates' $updArgs $updIcon
    }
    if ($desktop) {
        New-Shortcut (Join-Path $desktop 'BAKOQUAKE.lnk') $playTarget $playStyle 'Play BAKOQUAKE'
        if ($updTarget) {
            New-Shortcut (Join-Path $desktop 'Update BAKOQUAKE.lnk') $updTarget 1 'Check for and install BAKOQUAKE updates' $updArgs $updIcon
        }
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $env:LOCALAPPDATA 'BAKOQUAKE') | Out-Null
    exit 0
} catch {
    exit 1
}
