# BAKOQUAKE - find Quake's pak0.pak/pak1.pak and copy them into <package>\id1\ (Windows).
# Called by the Windows launcher:  powershell -NoProfile -ExecutionPolicy Bypass -File tools\find-quake-paks.ps1 -Root <package>
#
# Looks in Steam (registry + library folders), GOG (registry), the usual install folders on every drive, then
# %USERPROFILE%\Downloads. Wants an id1 folder holding BOTH pak0 and pak1: the 2021 rerelease ships only a
# different pak0.pak, so rerelease / "Quake Enhanced" folders are skipped. Exit code 0 = paks are in place.
param([Parameter(Mandatory = $true)][string]$Root)

$ErrorActionPreference = 'SilentlyContinue'
$Pak0Md5 = '5906E5998FC3D896DDAF5E6A62E03ABB'   # Quake 1.06 pak0.pak
$Pak1Md5 = 'D76B3E5678F0B64AC74CE5E340E6A685'   # Quake pak1.pak (registered)
$Root = (Resolve-Path $Root).Path.TrimEnd('\')

if (Test-Path "$Root\id1\pak0.pak") { exit 0 }

function Get-CandidateDirs {
    # Steam: install path from the registry, plus every library folder in libraryfolders.vdf.
    $steams = @(
        (Get-ItemProperty 'HKCU:\Software\Valve\Steam').SteamPath,
        (Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam').InstallPath,
        (Get-ItemProperty 'HKLM:\SOFTWARE\Valve\Steam').InstallPath
    ) | Where-Object { $_ } | ForEach-Object { $_ -replace '/', '\' } | Select-Object -Unique
    foreach ($s in $steams) {
        "$s\steamapps\common\Quake"
        $vdf = "$s\steamapps\libraryfolders.vdf"
        if (Test-Path $vdf) {
            Select-String -Path $vdf -Pattern '^\s*"path"\s*"(.+)"\s*$' | ForEach-Object {
                ($_.Matches[0].Groups[1].Value -replace '\\\\', '\') + '\steamapps\common\Quake'
            }
        }
    }
    # GOG: each installed game has a key with gameName + path.
    foreach ($k in 'HKLM:\SOFTWARE\WOW6432Node\GOG.com\Games', 'HKLM:\SOFTWARE\GOG.com\Games') {
        Get-ChildItem $k | ForEach-Object {
            $g = Get-ItemProperty $_.PSPath
            if ($g.gameName -like 'Quake*' -and $g.gameName -notlike '*Enhanced*' -and $g.path) { $g.path }
        }
    }
    # Usual folders on every drive (same list Quakestarter checks, original-game entries only).
    $tops = @('Program Files (x86)', 'Program Files', 'Games', '')
    $subs = @('Quake', 'Steam\steamapps\common\Quake', 'GOG Games\Quake', 'GOG Galaxy\Games\Quake')
    foreach ($drive in (Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' })) {
        foreach ($t in $tops) { foreach ($s in $subs) { Join-Path (Join-Path $drive.Root $t) $s } }
    }
}

# Given a folder, return the id1 folder under it (or the folder itself) that holds pak0 + pak1.
function Find-Id1 ([string]$dir) {
    foreach ($d in @($dir, (Join-Path $dir 'id1'))) {
        if ($d -match 'rerelease|Quake Enhanced') { continue }
        if ((Test-Path -LiteralPath "$d\pak0.pak") -and (Test-Path -LiteralPath "$d\pak1.pak")) { return $d }
    }
    return $null
}

Write-Host 'Looking for your Quake pak0.pak / pak1.pak...'
$found = $null
foreach ($c in (Get-CandidateDirs | Select-Object -Unique)) {
    if ($c.TrimEnd('\') -eq $Root) { continue }
    $found = Find-Id1 $c
    if ($found) { break }
}

if (-not $found) {
    $dl = Join-Path $env:USERPROFILE 'Downloads'
    if (Test-Path $dl) {
        Write-Host '  not in the usual install folders; checking Downloads...'
        foreach ($p in (Get-ChildItem -LiteralPath $dl -Recurse -Depth 5 -Filter 'pak0.pak' -File)) {
            if ($p.DirectoryName -like "$Root*") { continue }
            $found = Find-Id1 $p.DirectoryName
            if ($found) { break }
        }
    }
}

if (-not $found) {
    Write-Host '  no Quake install found.'
    # The launcher console may be hidden (PLAY BAKERSFIELDQUAKE.exe), so also say it in a dialog.
    try {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            "Couldn't find Quake's pak0.pak and pak1.pak (looked in Steam, GOG and Downloads).`n`n" +
            "Copy them from your own Quake install into:`n$Root\id1\", 'BAKOQUAKE') | Out-Null
    } catch {}
    exit 1
}

Write-Host "  found: $found"
if ((Get-FileHash -LiteralPath "$found\pak0.pak" -Algorithm MD5).Hash -ne $Pak0Md5) {
    Write-Host '  warning: pak0.pak is not the Quake 1.06 version; trying it anyway.'
}
if ((Get-FileHash -LiteralPath "$found\pak1.pak" -Algorithm MD5).Hash -ne $Pak1Md5) {
    Write-Host '  warning: pak1.pak does not match the known registered pak1; trying it anyway.'
}
New-Item -ItemType Directory -Force -Path "$Root\id1" | Out-Null
Copy-Item -LiteralPath "$found\pak0.pak" "$Root\id1\pak0.pak" -ErrorAction Stop
Copy-Item -LiteralPath "$found\pak1.pak" "$Root\id1\pak1.pak" -ErrorAction Stop
Write-Host "  copied pak0.pak + pak1.pak into $Root\id1\"
exit 0
