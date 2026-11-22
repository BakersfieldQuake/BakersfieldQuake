# BAKOQUAKE problem report: collects logs, config, hardware/OS details, structured Windows crash/hang/TDR/OOM events,
# and map/pk3 SHA-256 integrity data into one zip on the Desktop: BAKOQUAKE-report-YYYYMMDD-HHMMSS.zip.
# Run by "Report a Problem.cmd". Nothing is sent anywhere: the player decides who gets the zip.
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$OutDir = ''
)

$ErrorActionPreference = 'SilentlyContinue'
$out = New-Object System.Collections.Generic.List[string]
function Add([string]$s) { $out.Add($s) }
function Head([string]$s) { $out.Add(''); $out.Add("== $s") }

function Strip-QuakeColors([string]$s) {
    if (-not $s) { return '' }
    return ($s -replace '\^x[0-9a-fA-F]{3}', '' -replace '\^[0-9]', '')
}

function Copy-LockedSafe([string]$Src, [string]$Dst) {
    try {
        $inStream = [System.IO.File]::Open($Src, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
        try {
            $outStream = [System.IO.File]::Open($Dst, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            try {
                $inStream.CopyTo($outStream)
            } finally {
                $outStream.Dispose()
            }
        } finally {
            $inStream.Dispose()
        }
        return $true
    } catch {
        return $false
    }
}

function Read-LinesSafe([string]$Path) {
    try {
        $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
        try {
            $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8, $true)
            try {
                $list = New-Object System.Collections.Generic.List[string]
                while (($line = $sr.ReadLine()) -ne $null) { $list.Add($line) }
                return $list.ToArray()
            } finally {
                $sr.Dispose()
            }
        } finally {
            $fs.Dispose()
        }
    } catch {
        return @()
    }
}

function Get-Sha256Safe([string]$Path) {
    try {
        $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
        try {
            $sha = [System.Security.Cryptography.SHA256]::Create()
            try {
                $hashBytes = $sha.ComputeHash($fs)
                return ([BitConverter]::ToString($hashBytes) -replace '-', '').ToLowerInvariant()
            } finally {
                $sha.Dispose()
            }
        } finally {
            $fs.Dispose()
        }
    } catch {
        return ''
    }
}

function Get-RegVramBytes($regEntry) {
    if (-not $regEntry) { return [uint64]0 }
    $qw = $regEntry.'HardwareInformation.qwMemorySize'
    if ($qw -ne $null) {
        try {
            $v = [uint64]$qw
            if ($v -gt 0) { return $v }
        } catch {}
    }
    $ms = $regEntry.'HardwareInformation.MemorySize'
    if ($ms -ne $null) {
        if ($ms -is [byte[]]) {
            if ($ms.Length -ge 8) { return [BitConverter]::ToUInt64($ms, 0) }
            if ($ms.Length -ge 4) { return [uint64][BitConverter]::ToUInt32($ms, 0) }
        } else {
            try {
                $v = [uint64]$ms
                if ($v -gt 0) { return $v }
            } catch {}
        }
    }
    return [uint64]0
}

function Get-GpuTag([string]$Name, [string]$Compat, [string]$Pnp, [uint64]$VramMb) {
    $isVirtual = ($Pnp -match '^(ROOT|SWD)\\') -or
        ($Name -match 'Parsec|Virtual|Indirect|Basic Display|Remote|RDP|Citrix|Meta |Oculus|Spacedesk|Immersed|LuminonCore|IDD|VDD|Hyper-V|VMware|VirtualBox|QXL|Microsoft Basic') -or
        ($Compat -match 'Parsec|Virtual|Citrix|Microsoft')
    if ($isVirtual) { return '[VIRTUAL]' }

    $isIntelIgpu = (($Pnp -match 'VEN_8086') -or ($Name -match 'Intel')) -and ($Name -notmatch 'Arc\s+(A|B|Pro)\d')
    $isAmdApu = ($Pnp -match 'VEN_1002') -and (
        ($Name -match '^AMD Radeon(\(TM\))? Graphics$') -or
        ($Name -match 'Radeon.*(Vega\s+[0-9]|6[0-9]0M|7[0-9]0M|8[0-9]0M)') -or
        ($VramMb -gt 0 -and $VramMb -le 2048 -and $Name -notmatch 'RX\s+\d|Pro\s+W|FirePro')
    )
    if ($isIntelIgpu -or $isAmdApu -or ($Name -match 'Integrated|APU')) { return '[iGPU]' }
    return '[dGPU]'
}

function Parse-EventXml($ev) {
    $res = @{
        kv   = @{}
        vals = New-Object System.Collections.Generic.List[string]
        xml  = $null
    }
    try {
        $x = [xml]$ev.ToXml()
        $res.xml = $x
        if ($x.Event.EventData -and $x.Event.EventData.Data) {
            foreach ($d in @($x.Event.EventData.Data)) {
                if ($d -is [string]) {
                    $res.vals.Add($d)
                } else {
                    $val = if ($d.'#text' -ne $null) { [string]$d.'#text' } else { '' }
                    $res.vals.Add($val)
                    if ($d.Name) { $res.kv[$d.Name] = $val }
                }
            }
        }
    } catch {}
    if ($res.vals.Count -eq 0 -and $ev.Properties) {
        foreach ($p in $ev.Properties) {
            $res.vals.Add($(if ($p.Value -ne $null) { [string]$p.Value } else { '' }))
        }
    }
    return $res
}

function Get-EvField($parsed, [string]$Name, [int]$Idx) {
    if ($parsed.kv.ContainsKey($Name) -and $parsed.kv[$Name] -ne '') { return $parsed.kv[$Name] }
    if ($Idx -ge 0 -and $Idx -lt $parsed.vals.Count) { return $parsed.vals[$Idx] }
    return ''
}

try {
    $Root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
} catch {
    $Root = $Root.TrimEnd('\')
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$game = Join-Path $Root 'BakersfieldQuake'
$cacheDir = Join-Path $env:LOCALAPPDATA 'BAKOQUAKE'
$bqDir = Join-Path $Root '.bq'

# Determine destination zip path
$zipName = "BAKOQUAKE-report-$stamp.zip"
if ($OutDir) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    $zipPath = Join-Path $OutDir $zipName
} elseif ($env:BQ_REPORT_OUT) {
    if ($env:BQ_REPORT_OUT -match '\.zip$') {
        $parent = Split-Path -Parent $env:BQ_REPORT_OUT
        if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        $zipPath = $env:BQ_REPORT_OUT
    } else {
        New-Item -ItemType Directory -Force -Path $env:BQ_REPORT_OUT | Out-Null
        $zipPath = Join-Path $env:BQ_REPORT_OUT $zipName
    }
} else {
    $desk = [Environment]::GetFolderPath('Desktop')
    if (-not $desk -or -not (Test-Path -LiteralPath $desk)) { $desk = $env:USERPROFILE }
    $zipPath = Join-Path $desk $zipName
}

$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("bq-report-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $stage | Out-Null

try {
    $bundledFiles = New-Object System.Collections.Generic.List[string]
    $bundledFiles.Add('summary.txt')

    # Copy raw artifacts into staging before summarizing so we know what was bundled
    $rawSources = @(
        @{ Src = (Join-Path $game 'bq_game.log');            Dst = 'bq_game.log' },
        @{ Src = (Join-Path $game 'bq_game_prev.log');       Dst = 'bq_game_prev.log' },
        @{ Src = (Join-Path $game 'bq_game_crash.log');      Dst = 'bq_game_crash.log' },
        @{ Src = (Join-Path $game 'bq_server.log');          Dst = 'bq_server.log' },
        @{ Src = (Join-Path $game 'bq_server_prev.log');     Dst = 'bq_server_prev.log' },
        @{ Src = (Join-Path $game 'config.cfg');             Dst = 'config.cfg' },
        @{ Src = (Join-Path $bqDir 'update.log');            Dst = 'update.log' },
        @{ Src = (Join-Path $bqDir 'state.json');            Dst = 'state.json' },
        @{ Src = (Join-Path $cacheDir 'last-launch.txt');    Dst = 'last-launch.txt' }
    )
    foreach ($item in $rawSources) {
        if (Test-Path -LiteralPath $item.Src) {
            if (Copy-LockedSafe $item.Src (Join-Path $stage $item.Dst)) {
                $bundledFiles.Add($item.Dst)
            }
        }
    }

    Add "BAKOQUAKE problem report, $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Add "Bundle: $zipPath"
    Add ("Included files: " + ($bundledFiles -join ', '))
    Add 'Nothing was sent anywhere. Send this zip file to whoever is helping you.'
    Add 'Note: bundled game logs include player names and chat; config.cfg includes your saved settings.'

    # ---- Package -------------------------------------------------------------------------------------------
    Head 'Package'
    Add "folder: $Root"
    $vPath = Join-Path $Root 'VERSION.txt'
    $v = if (Test-Path -LiteralPath $vPath) { (Get-Content -LiteralPath $vPath -TotalCount 1) } else { '(missing)' }
    Add "VERSION.txt: $v"
    $vcfgPath = Join-Path $game 'version.cfg'
    if (Test-Path -LiteralPath $vcfgPath) {
        $sd = Select-String -LiteralPath $vcfgPath -Pattern 'showdate_format' | Select-Object -First 1
        if ($sd) { Add "release: $($sd.Line.Trim())" }
    }
    foreach ($f in @('engine\zircon_beta_gcc.exe', 'BakersfieldQuake\progs.dat', 'BakersfieldQuake\csprogs.dat', 'BakersfieldQuake\menu.dat', 'Update.exe')) {
        $p = Join-Path $Root $f
        if (Test-Path -LiteralPath $p) {
            $i = Get-Item -LiteralPath $p
            $h = Get-Sha256Safe $p
            $hShort = if ($h.Length -ge 16) { $h.Substring(0, 16) } else { '?' }
            Add ("{0,-34} {1,11} bytes  sha256 {2}  {3:yyyy-MM-dd HH:mm}" -f $f, $i.Length, $hShort, $i.LastWriteTime)
        } else {
            Add "$f  MISSING"
        }
    }
    $paks = @('id1\pak0.pak', 'id1\pak1.pak') | ForEach-Object {
        $pp = Join-Path $Root $_
        if (Test-Path -LiteralPath $pp) { "$_ present ($((Get-Item -LiteralPath $pp).Length) B)" } else { "$_ MISSING" }
    }
    Add ($paks -join ', ')

    # ---- Hardware & OS -------------------------------------------------------------------------------------
    Head 'Hardware & OS'
    $os = Get-CimInstance Win32_OperatingSystem
    $cs = Get-CimInstance Win32_ComputerSystem
    $cpus = @(Get-CimInstance Win32_Processor)
    $cv = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $dispVer = if ($cv.DisplayVersion) { $cv.DisplayVersion } elseif ($cv.ReleaseId) { $cv.ReleaseId } else { '?' }
    $buildNum = if ($cv.CurrentBuildNumber) { $cv.CurrentBuildNumber } else { $os.BuildNumber }
    $ubr = if ($cv.UBR -ne $null) { ".$($cv.UBR)" } else { '' }
    Add ("Windows: {0} {1} (Build {2}{3}, OS Version {4}, {5})" -f $os.Caption.Trim(), $dispVer, $buildNum, $ubr, $os.Version, $os.OSArchitecture)

    if ($cpus.Count -gt 0) {
        $totCores = ($cpus | Measure-Object -Property NumberOfCores -Sum).Sum
        $totThreads = ($cpus | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
        Add ("CPU: {0} | {1} cores / {2} threads | max {3} MHz" -f $cpus[0].Name.Trim(), $totCores, $totThreads, $cpus[0].MaxClockSpeed)
    }

    $ramTotalGb = $cs.TotalPhysicalMemory / 1GB
    $ramFreeGb = ($os.FreePhysicalMemory * 1KB) / 1GB
    $ramUsedGb = $ramTotalGb - $ramFreeGb
    $ramPct = if ($ramTotalGb -gt 0) { ($ramUsedGb / $ramTotalGb) * 100 } else { 0 }
    Add ("RAM: {0:N2} GB total | {1:N2} GB free right now ({2:N2} GB / {3:N0}% in use)" -f $ramTotalGb, $ramFreeGb, $ramUsedGb, $ramPct)

    $commitLimGb = ($os.TotalVirtualMemorySize * 1KB) / 1GB
    $commitUsedGb = (($os.TotalVirtualMemorySize - $os.FreeVirtualMemory) * 1KB) / 1GB
    $commitFreeGb = ($os.FreeVirtualMemory * 1KB) / 1GB
    Add ("Commit (RAM + pagefile): {0:N2} GB limit | {1:N2} GB in use | {2:N2} GB free" -f $commitLimGb, $commitUsedGb, $commitFreeGb)

    $pfs = @(Get-CimInstance Win32_PageFileUsage)
    if ($pfs.Count -gt 0) {
        foreach ($pf in $pfs) {
            Add ("Pagefile {0}: {1:N2} GB allocated ({2} MB), {3:N2} GB used ({4} MB), peak {5:N2} GB" -f $pf.Name, ($pf.AllocatedBaseSize / 1024), $pf.AllocatedBaseSize, ($pf.CurrentUsage / 1024), $pf.CurrentUsage, ($pf.PeakUsage / 1024))
        }
    } else {
        Add 'Pagefile: (none reported by Win32_PageFileUsage)'
    }

    $drive = (Get-Item -LiteralPath $Root).PSDrive
    if ($drive) { Add ("Free disk space on {0}: {1:N1} GB" -f $drive.Name, ($drive.Free / 1GB)) }

    # ---- Graphics adapters (64-bit registry VRAM + WMI fallback + [iGPU]/[VIRTUAL]/[dGPU] tags) ------------
    Head 'Graphics adapters'
    $regGpus = @(Get-ItemProperty 'HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0*' |
        Where-Object { $_.PSChildName -match '^\d{4}$' })
    $wmiGpus = @(Get-CimInstance Win32_VideoController)
    foreach ($g in $wmiGpus) {
        $pnp = [string]$g.PNPDeviceID
        $name = [string]$g.Name
        $compat = [string]$g.AdapterCompatibility
        $matchReg = $null
        if ($pnp) {
            $cands = @($regGpus | Where-Object { $_.MatchingDeviceId -and $pnp.ToLowerInvariant().StartsWith(([string]$_.MatchingDeviceId).ToLowerInvariant()) })
            if ($cands.Count -gt 1) {
                $exact = $cands | Where-Object { $_.DriverDesc -eq $name } | Select-Object -First 1
                $matchReg = if ($exact) { $exact } else { $cands[0] }
            } elseif ($cands.Count -eq 1) {
                $matchReg = $cands[0]
            }
        }
        if (-not $matchReg -and $name) {
            $matchReg = $regGpus | Where-Object { $_.DriverDesc -eq $name } | Select-Object -First 1
        }

        $regBytes = Get-RegVramBytes $matchReg
        $wmiBytes = if ($g.AdapterRAM) { [uint64]$g.AdapterRAM } else { [uint64]0 }
        $vramBytes = if ($regBytes -gt 0) { $regBytes } else { $wmiBytes }
        $vramSrc = if ($regBytes -gt 0) { '64-bit reg' } elseif ($wmiBytes -gt 0) { 'WMI 32-bit' } else { 'none' }
        $vramMb = [uint64][math]::Round($vramBytes / 1MB)
        $wmiMb = [uint64][math]::Round($wmiBytes / 1MB)
        $tag = Get-GpuTag $name $compat $pnp $vramMb
        $date = if ($g.DriverDate) { $g.DriverDate.ToString('yyyy-MM-dd') } else { '?' }
        $res = if ($g.CurrentHorizontalResolution -and $g.CurrentVerticalResolution) { "$($g.CurrentHorizontalResolution)x$($g.CurrentVerticalResolution)" } else { 'inactive/headless' }
        Add ("{0} {1} | VRAM: {2} MB ({3}; WMI {4} MB) | Driver: {5} ({6}) | Mode: {7}" -f $tag, $name, $vramMb, $vramSrc, $wmiMb, $g.DriverVersion, $date, $res)
        Add ("    PNP: {0} | Vendor: {1} | Status: {2} (err {3})" -f $pnp, $compat, $g.Status, $g.ConfigManagerErrorCode)
    }

    # ---- Top 5 RAM-consuming processes ---------------------------------------------------------------------
    Head 'Top 5 RAM-consuming processes (right now)'
    $topProcs = @(Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5)
    foreach ($pr in $topProcs) {
        Add ("{0,-28} PID {1,-7} WS {2,7:N0} MB  Private {3,7:N0} MB" -f $pr.ProcessName, $pr.Id, ($pr.WorkingSet64 / 1MB), ($pr.PrivateMemorySize64 / 1MB))
    }

    # ---- Launcher decisions & last-launch snapshot ---------------------------------------------------------
    Head 'Launcher decisions & state'
    foreach ($f in @('ram-gb.txt', 'vram-mb.txt', 'lowgpu-applied.txt', 'tier.txt', 'session-active.flag')) {
        $p = Join-Path $cacheDir $f
        if (Test-Path -LiteralPath $p) {
            Add "$f = $((Get-Content -LiteralPath $p -TotalCount 1))"
        } else {
            Add "$f = (not present)"
        }
    }
    Add "Env: BQ_LOWMEM='$($env:BQ_LOWMEM)' BQ_LOWGPU='$($env:BQ_LOWGPU)' BQ_ULTRALOW='$($env:BQ_ULTRALOW)' BQ_SAFEMODE='$($env:BQ_SAFEMODE)' BQ_NO_UPDATE='$($env:BQ_NO_UPDATE)' COMBAT_ARGS='$($env:COMBAT_ARGS)'"
    $lastLaunch = Join-Path $cacheDir 'last-launch.txt'
    if (Test-Path -LiteralPath $lastLaunch) {
        Add '-- last-launch.txt:'
        foreach ($line in Read-LinesSafe $lastLaunch) { Add "   $line" }
    }

    # ---- Saved settings (config.cfg extract) ---------------------------------------------------------------
    Head 'Saved settings extract (full config.cfg is inside this zip)'
    $cfg = Join-Path $game 'config.cfg'
    if (Test-Path -LiteralPath $cfg) {
        $want = '^"?(seta\s+)?"?(vid_width|vid_height|_vid_window_width|_vid_window_height|vid_fullscreen|vid_desktopfullscreen|vid_samples|vid_vsync|vid_refreshrate|gl_max_size|gl_picmip|gl_picmip_world|gl_picmip_other|gl_picmip_sprites|gl_picmip_force|gl_texture_anisotropy|gl_texturemode|gl_texturecompression|lowspec|r_bloom|r_shadow_realtime_dlight|r_shadow_realtime_dlight_shadows|r_shadow_shadowmapping|r_shadow_shadowmapping_texturesize|r_shadow_gloss|r_shadow_usenormalmap|r_glsl_offsetmapping|r_glsl_offsetmapping_reliefmapping|r_glsl_deluxemapping|r_dynamic|r_water|r_viewscale|r_buffermegs_vertex|r_buffermegs_index16|r_buffermegs_index32|r_buffermegs_uniform|r_framedatasize|cl_maxfps|cl_particles_quality|cl_decals|cl_decals_max|mod_bsp_portalize|mod_freebeforeload|mod_q1bsp_pvs_ondemand|mod_q1bsp_lazy_render_bih|r_load_normalmap|r_load_gloss|gyroset|bm_defver)"? '
        foreach ($line in Read-LinesSafe $cfg) {
            if ($line.Trim() -match $want) { Add $line.Trim() }
        }
    } else {
        Add 'no config.cfg yet (the game has not been closed normally on this PC)'
    }

    # ---- Parsed game & server logs -------------------------------------------------------------------------
    $errPat = 'Engine Error|Host_Error|Sys_Error|Mem_Alloc|out of memory|runaway loop|GL_OUT_OF_MEMORY|GL_INVALID|shader.*fail|compile.*fail|link.*fail|no free edicts|SZ_GetSpace|PRVM_ExecuteProgram|server crash|could not create|video mode failed|unable to|Couldn''t load|ERROR:|WARNING:'
    $tierPat = 'execing\s+.*(lowmem|lowgpu|ultralow|safemode|graphics|pretty)\.cfg|low-memory|weak-graphics|ultra-low|safe mode'
    $anyLog = $false

    foreach ($name in @('bq_game.log', 'bq_game_prev.log', 'bq_game_crash.log', 'bq_server.log', 'bq_server_prev.log')) {
        $p = Join-Path $game $name
        if (-not (Test-Path -LiteralPath $p)) { continue }
        $anyLog = $true
        $i = Get-Item -LiteralPath $p
        $rawLines = Read-LinesSafe $p
        $cleanLines = @($rawLines | ForEach-Object { Strip-QuakeColors $_ })
        Head ("Log {0} ({1:N0} bytes, {2} lines, last written {3:yyyy-MM-dd HH:mm:ss})" -f $name, $i.Length, $cleanLines.Count, $i.LastWriteTime)

        # Extract GL info
        $glLines = @($cleanLines | Where-Object { $_ -match '^\s*(GL_VENDOR|GL_RENDERER|GL_VERSION):' } | Select-Object -Last 6)
        if ($glLines.Count -gt 0) {
            Add '-- OpenGL renderer:'
            foreach ($gl in $glLines) { Add "   $($gl.Trim())" }
        }

        # Extract active / loaded maps (exclude ammo/health b_ models and sub-folders like ad_brk/)
        $mapsSeen = New-Object System.Collections.Generic.List[string]
        foreach ($cl in $cleanLines) {
            $mName = $null
            if ($cl -match 'Stats for q1bsp model "maps/([^/"]+)\.bsp"') {
                $cand = $Matches[1]
                if ($cand -notmatch '^b_') { $mName = $cand }
            } elseif ($cl -match 'Using map\s+"?([^"\s]+)"?' -or $cl -match 'Loading map\s+"?([^"\s]+)"?' -or $cl -match '^map\s+([A-Za-z0-9_\-]+)\s*$') {
                $mName = $Matches[1] -replace '^maps/', '' -replace '\.bsp$', ''
            }
            if ($mName) {
                if ($mapsSeen.Count -eq 0 -or $mapsSeen[$mapsSeen.Count - 1] -ne $mName) {
                    $mapsSeen.Add($mName)
                }
            }
        }
        if ($mapsSeen.Count -gt 0) {
            $lastMap = $mapsSeen[$mapsSeen.Count - 1]
            Add ("-- Active / last map: {0}  (history: {1})" -f $lastMap, ($mapsSeen -join ' -> '))
        } else {
            Add '-- Active / last map: (none detected in log)'
        }

        # Loaded tier / graphics configs
        $tierLines = @($cleanLines | Where-Object { $_ -match $tierPat } | Select-Object -Last 15)
        if ($tierLines.Count -gt 0) {
            Add '-- Loaded tier/graphics configs:'
            foreach ($tl in $tierLines) { Add "   $($tl.Trim())" }
        }

        # Errors / Mem_Alloc / GL / shader lines
        $hits = @($cleanLines | Where-Object { ($_ -match $errPat) -and ($_ -notmatch 'GL_ARB_|GL_EXT_|GL_NV_|GL_ATI_|GL_SGIS_|font-file') } | Select-Object -Last 60)
        Add "-- Error / Mem_Alloc / GL / shader lines: $($hits.Count)"
        foreach ($h in $hits) { Add "   $h" }

        Add '-- Last 40 lines (full raw log is inside this zip):'
        $cleanLines | Select-Object -Last 40 | ForEach-Object { Add "   $_" }
    }
    if (-not $anyLog) {
        Head 'Game logs'
        Add 'No bq_game.log found: the game has not been started with Play / Start Server from this folder yet.'
    }

    # ---- Structured Windows Event Logs (locale-independent via XML / Properties) ---------------------------
    Head 'Windows Application Events 1000 / 1001 / 1002 - Zircon / BAKOQUAKE (30 days)'
    $since30 = (Get-Date).AddDays(-30)
    $since7 = (Get-Date).AddDays(-7)
    $appEvents = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; Id = 1000, 1001, 1002; StartTime = $since30 } |
        Where-Object { $_.ProviderName -in @('Application Error', 'Application Hang', 'Windows Error Reporting') })

    $bqEvLines = New-Object System.Collections.Generic.List[string]
    $otherEvLines = New-Object System.Collections.Generic.List[string]
    $bqMatchPat = 'zircon|darkplaces|bakoquake|bq-update'

    foreach ($e in $appEvents) {
        $p = Parse-EventXml $e
        $allText = ($p.vals -join ' ')
        $isBq = ($allText -match $bqMatchPat)

        $summaryLine = ''
        $detailLine = ''
        if ($e.Id -eq 1000) {
            $app = Get-EvField $p 'AppName' 0
            $appVer = Get-EvField $p 'AppVersion' 1
            $mod = Get-EvField $p 'ModuleName' 3
            $modVer = Get-EvField $p 'ModuleVersion' 4
            $exc = Get-EvField $p 'ExceptionCode' 6
            $off = Get-EvField $p 'FaultingOffset' 7
            $appPath = Get-EvField $p 'AppPath' 10
            $modPath = Get-EvField $p 'ModulePath' 11
            $summaryLine = ("{0:yyyy-MM-dd HH:mm:ss}  Event 1000 (Crash)  App={1} ({2})  Module={3} ({4})  Exc=0x{5}  Offset=0x{6}" -f $e.TimeCreated, $app, $appVer, $mod, $modVer, ($exc -replace '^0x', ''), ($off -replace '^0x', ''))
            if ($appPath -or $modPath) { $detailLine = "   AppPath=$appPath | ModPath=$modPath" }
        } elseif ($e.Id -eq 1002) {
            $app = Get-EvField $p 'AppName' 0
            $appVer = Get-EvField $p 'AppVersion' 1
            $pidStr = Get-EvField $p 'ProcessId' 2
            $termT = Get-EvField $p 'TerminationTime' 4
            $appPath = Get-EvField $p 'AppPath' 5
            $hangType = Get-EvField $p 'HangType' 7
            if (-not $hangType -and $p.vals.Count -gt 6) { $hangType = $p.vals[$p.vals.Count - 1] }
            $summaryLine = ("{0:yyyy-MM-dd HH:mm:ss}  Event 1002 (Hang)   App={1} ({2})  PID={3}  HangType={4}  TermTime={5}" -f $e.TimeCreated, $app, $appVer, $pidStr, $hangType, $termT)
            if ($appPath) { $detailLine = "   AppPath=$appPath" }
        } elseif ($e.Id -eq 1001) {
            $evName = Get-EvField $p 'EventName' 2
            $p1 = Get-EvField $p 'P1' 5
            $p2 = Get-EvField $p 'P2' 6
            $p4 = Get-EvField $p 'P4' 8
            $p7 = Get-EvField $p 'P7' 11
            $bucket = Get-EvField $p 'Bucket' 0
            if (-not $isBq -and $evName -notmatch 'APPCRASH|AppHang|BEX|MoAppCrash|MoAppHang') { continue }
            $summaryLine = ("{0:yyyy-MM-dd HH:mm:ss}  Event 1001 (WER)    Type={1}  App={2} ({3})  Mod/P4={4}  Code/P7={5}  Bucket={6}" -f $e.TimeCreated, $evName, $p1, $p2, $p4, $p7, $bucket)
        }

        if ($isBq) {
            if ($bqEvLines.Count -lt 30) {
                $bqEvLines.Add($summaryLine)
                if ($detailLine) { $bqEvLines.Add($detailLine) }
            }
        } elseif ($e.TimeCreated -ge $since7 -and $otherEvLines.Count -lt 8) {
            $otherEvLines.Add($summaryLine)
        }
    }

    if ($bqEvLines.Count -eq 0) {
        Add 'None recorded for Zircon / BAKOQUAKE in the last 30 days.'
    } else {
        foreach ($l in $bqEvLines) { Add $l }
    }

    Head 'Other recent application crashes / hangs (last 7 days, non-Zircon, max 8)'
    if ($otherEvLines.Count -eq 0) {
        Add 'None.'
    } else {
        foreach ($l in $otherEvLines) { Add $l }
    }

    Head 'Windows System Events 4101 (GPU TDR driver reset) & 2004 (Low Virtual Memory) (30 days)'
    $tdrEvents = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Id = 4101; StartTime = $since30 } | Select-Object -First 10)
    if ($tdrEvents.Count -eq 0) {
        Add 'Event 4101 (Display TDR): none in last 30 days.'
    } else {
        Add "Event 4101 (Display TDR): $($tdrEvents.Count) event(s)"
        foreach ($e in $tdrEvents) {
            $p = Parse-EventXml $e
            $drv = Get-EvField $p 'DisplayDriver' 0
            Add ("   {0:yyyy-MM-dd HH:mm:ss}  Provider={1}  Driver={2}" -f $e.TimeCreated, $e.ProviderName, $drv)
        }
    }

    $oomEvents = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Id = 2004; StartTime = $since30 } | Select-Object -First 10)
    if ($oomEvents.Count -eq 0) {
        Add 'Event 2004 (Resource-Exhaustion-Detector / Low Virtual Memory): none in last 30 days.'
    } else {
        Add "Event 2004 (Resource-Exhaustion-Detector / Low Virtual Memory): $($oomEvents.Count) event(s)"
        foreach ($e in $oomEvents) {
            $p = Parse-EventXml $e
            $info = $null
            if ($p.xml -and $p.xml.Event.UserData) { $info = $p.xml.Event.UserData.MemoryExhaustionInfo }
            if ($info) {
                $si = $info.SystemInfo
                $limGb = ([double]$si.SystemCommitLimit) / 1GB
                $chgGb = ([double]$si.SystemCommitCharge) / 1GB
                $topList = New-Object System.Collections.Generic.List[string]
                foreach ($pk in @('Process_1', 'Process_2', 'Process_3')) {
                    $pr = $info.ProcessInfo.$pk
                    if ($pr -and $pr.Name) {
                        $gb = ([double]$pr.CommitCharge) / 1GB
                        $topList.Add(("{0} ({1:N2} GB)" -f $pr.Name, $gb))
                    }
                }
                Add ("   {0:yyyy-MM-dd HH:mm:ss}  Commit={1:N2}/{2:N2} GB  Top: {3}" -f $e.TimeCreated, $chgGb, $limGb, ($topList -join ', '))
            } else {
                Add ("   {0:yyyy-MM-dd HH:mm:ss}  Provider={1}" -f $e.TimeCreated, $e.ProviderName)
            }
        }
    }

    # ---- Asset Integrity Table (maps/*.bsp, maps/*.lit, *.pk3 vs .bq/state.json) ---------------------------
    Head 'Asset integrity table (maps/*.bsp, maps/*.lit, *.pk3)'
    $statePath = Join-Path $bqDir 'state.json'
    $stateObj = $null
    $managedSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    $cacheMap = @{}
    if (Test-Path -LiteralPath $statePath) {
        try {
            $stateObj = (Get-Content -LiteralPath $statePath -Raw) | ConvertFrom-Json
            Add ("Updater state.json: build=$($stateObj.build) version='$($stateObj.version)' updater=$($stateObj.updater) managed=$($stateObj.managed.Count)")
            foreach ($m in @($stateObj.managed)) { [void]$managedSet.Add(([string]$m -replace '\\', '/')) }
            if ($stateObj.cache) {
                foreach ($prop in $stateObj.cache.PSObject.Properties) {
                    $cacheMap[($prop.Name -replace '\\', '/').ToLowerInvariant()] = $prop.Value
                }
            }
        } catch {
            Add 'Updater state.json: present but failed to parse!'
        }
    } else {
        Add 'Updater state.json: not present (cannot distinguish managed vs stray files).'
    }

    $assetFiles = New-Object System.Collections.Generic.List[object]
    foreach ($dirSpec in @(
        @{ Dir = $game;                     Filter = '*.pk3'; Prefix = 'BakersfieldQuake' },
        @{ Dir = (Join-Path $Root 'quake15'); Filter = '*.pk3'; Prefix = 'quake15' },
        @{ Dir = (Join-Path $game 'maps');  Filter = '*.bsp'; Prefix = 'BakersfieldQuake/maps' },
        @{ Dir = (Join-Path $game 'maps');  Filter = '*.lit'; Prefix = 'BakersfieldQuake/maps' }
    )) {
        if (Test-Path -LiteralPath $dirSpec.Dir) {
            foreach ($fi in @(Get-ChildItem -LiteralPath $dirSpec.Dir -Filter $dirSpec.Filter -File | Sort-Object Name)) {
                $assetFiles.Add([pscustomobject]@{
                    Rel  = "$($dirSpec.Prefix)/$($fi.Name)"
                    Item = $fi
                })
            }
        }
    }

    $bspStatus = @{}
    $litStatus = @{}
    $flagCount = 0

    foreach ($af in ($assetFiles | Sort-Object Rel)) {
        $rel = $af.Rel
        $fi = $af.Item
        $sha = Get-Sha256Safe $fi.FullName
        $flags = New-Object System.Collections.Generic.List[string]
        $isManaged = $managedSet.Contains($rel)
        if ($stateObj -and -not $isManaged) {
            $flags.Add('UNMANAGED/STRAY')
        }
        $key = $rel.ToLowerInvariant()
        if ($cacheMap.ContainsKey($key)) {
            $entry = $cacheMap[$key]
            if ($entry -and $entry.Count -ge 3) {
                if ([int64]$entry[0] -ne $fi.Length) { $flags.Add("SIZE_MISMATCH(expected $($entry[0]))") }
                if ($sha -and ([string]$entry[2]).ToLowerInvariant() -ne $sha) { $flags.Add("HASH_MISMATCH(expected $($entry[2].Substring(0,12)))") }
            }
        }
        if ($rel -match '^BakersfieldQuake/maps/(.+)\.bsp$') {
            $bspStatus[$Matches[1].ToLowerInvariant()] = @{ Managed = $isManaged; Flags = $flags; Size = $fi.Length; Mtime = $fi.LastWriteTime }
        } elseif ($rel -match '^BakersfieldQuake/maps/(.+)\.lit$') {
            $litStatus[$Matches[1].ToLowerInvariant()] = @{ Managed = $isManaged; Flags = $flags; Size = $fi.Length; Mtime = $fi.LastWriteTime }
        }
        if ($flags.Count -gt 0) { $flagCount += $flags.Count }
        $flagStr = if ($flags.Count -gt 0) { '  [' + ($flags -join ', ') + ']' } else { '' }
        Add ("{0,-48} {1,12:N0} B  {2}{3}" -f $rel, $fi.Length, $sha, $flagStr)
    }

    # Check for missing managed .bsp/.lit/.pk3 files
    if ($stateObj) {
        foreach ($m in ($managedSet | Sort-Object)) {
            if ($m -match '\.(bsp|lit|pk3)$') {
                $full = Join-Path $Root ($m -replace '/', '\')
                if (-not (Test-Path -LiteralPath $full)) {
                    $flagCount++
                    Add ("{0,-48} MISSING [MANAGED_FILE_MISSING]" -f $m)
                }
            }
        }
    }

    # Check .bsp / .lit pairing anomalies
    $pairIssues = New-Object System.Collections.Generic.List[string]
    foreach ($mapKey in ($litStatus.Keys | Sort-Object)) {
        if (-not $bspStatus.ContainsKey($mapKey)) {
            $pairIssues.Add("maps/$mapKey.lit has NO matching .bsp [ORPHAN_LIT]")
        } elseif ($stateObj -and ($bspStatus[$mapKey].Managed -ne $litStatus[$mapKey].Managed)) {
            $pairIssues.Add("maps/$mapKey .bsp/.lit managed-status mismatch (bsp=$($bspStatus[$mapKey].Managed), lit=$($litStatus[$mapKey].Managed)) [BSP_LIT_MISMATCH]")
        } elseif (($bspStatus[$mapKey].Flags.Count -gt 0) -or ($litStatus[$mapKey].Flags.Count -gt 0)) {
            $pairIssues.Add("maps/$mapKey .bsp/.lit integrity flag mismatch [BSP_LIT_MISMATCH]")
        }
    }
    if ($pairIssues.Count -gt 0) {
        Add '-- BSP/LIT pairing issues:'
        foreach ($pi in $pairIssues) { Add "   $pi" }
    }
    Add ("Total assets checked: {0} | Anomalies flagged: {1}" -f $assetFiles.Count, ($flagCount + $pairIssues.Count))

    # Write summary.txt (UTF-8 no BOM) and package everything into one zip
    $summaryPath = Join-Path $stage 'summary.txt'
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($summaryPath, $out, $utf8NoBom)

    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zipPath -CompressionLevel Optimal -Force

    if (-not (Test-Path -LiteralPath $zipPath)) {
        throw "Failed to create zip archive at $zipPath"
    }

    $zipSizeKb = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1KB, 1)
    Write-Host "Problem report created: $zipPath ($zipSizeKb KB, $($bundledFiles.Count) files)"
    if (-not $env:BQ_REPORT_NO_OPEN) {
        Start-Process explorer.exe -ArgumentList "/select,`"$zipPath`""
    }
} catch {
    Write-Error "Failed to create BAKOQUAKE problem report: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $stage) {
        Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
}
exit 0
