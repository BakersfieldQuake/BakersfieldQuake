# BAKOQUAKE problem report: writes BAKOQUAKE-report.txt to the Desktop and opens it.
# Run by "Report a Problem.cmd". Nothing is sent anywhere: the player decides who gets the file.
# It holds what is needed to tell why the game crashed or runs badly on a PC nobody else can look at:
# the package version, the PC (RAM, graphics adapters and driver), what the launcher decided (low-memory /
# weak-graphics mode), a few saved graphics settings, the last two game logs (errors and the final lines), and the
# crashes Windows recorded for the engine in the last 30 days (faulting module and exception code).
param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'SilentlyContinue'
$out = New-Object System.Collections.Generic.List[string]
function Add([string]$s) { $out.Add($s) }
function Head([string]$s) { $out.Add(''); $out.Add("== $s") }

$game = Join-Path $Root 'BakersfieldQuake'
Add "BAKOQUAKE problem report, $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Add 'Nothing was sent anywhere. This file is on your Desktop: send it to whoever is helping you.'
Add 'It contains PC details, graphics settings and the end of the last game logs (which include player names and chat).'

Head 'Package'
Add "folder: $Root"
$v = Get-Content -LiteralPath (Join-Path $Root 'VERSION.txt') -TotalCount 1
Add "VERSION.txt: $v"
$sd = Select-String -LiteralPath (Join-Path $game 'version.cfg') -Pattern 'showdate_format' | Select-Object -First 1
if ($sd) { Add "release: $($sd.Line.Trim())" }
foreach ($f in @('engine\zircon_beta_gcc.exe', 'BakersfieldQuake\progs.dat', 'BakersfieldQuake\csprogs.dat')) {
    $p = Join-Path $Root $f
    if (Test-Path -LiteralPath $p) {
        $i = Get-Item -LiteralPath $p
        $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.Substring(0, 16).ToLower()
        Add ("{0,-34} {1,10} bytes  sha256 {2}  {3:yyyy-MM-dd}" -f $f, $i.Length, $h, $i.LastWriteTime)
    } else { Add "$f  MISSING" }
}
$paks = @('id1\pak0.pak', 'id1\pak1.pak') | ForEach-Object { if (Test-Path -LiteralPath (Join-Path $Root $_)) { "$_ present" } else { "$_ MISSING" } }
Add ($paks -join ', ')

Head 'PC'
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
Add "Windows: $($os.Caption) $($os.Version)"
Add "CPU: $($cpu.Name.Trim()), $($cpu.NumberOfCores) cores"
Add ("RAM: {0:N1} GB installed, {1:N1} GB free right now" -f ($cs.TotalPhysicalMemory / 1GB), ($os.FreePhysicalMemory * 1KB / 1GB))
Add ("Commit limit (RAM + page file): {0:N1} GB, in use {1:N1} GB" -f ($os.TotalVirtualMemorySize * 1KB / 1GB), (($os.TotalVirtualMemorySize - $os.FreeVirtualMemory) * 1KB / 1GB))
$drive = (Get-Item -LiteralPath $Root).PSDrive
if ($drive) { Add ("Free space on {0}: {1:N1} GB" -f $drive.Name, ($drive.Free / 1GB)) }

Head 'Graphics adapters'
foreach ($g in Get-CimInstance Win32_VideoController) {
    $mb = if ($g.AdapterRAM) { [math]::Round($g.AdapterRAM / 1MB) } else { 0 }
    $date = if ($g.DriverDate) { $g.DriverDate.ToString('yyyy-MM-dd') } else { '?' }
    Add ("{0}: {1} MB reported (Windows caps this at 4095), driver {2} of {3}, {4}x{5}" -f $g.Name, $mb, $g.DriverVersion, $date, $g.CurrentHorizontalResolution, $g.CurrentVerticalResolution)
}

Head 'What the launcher decided'
$cache = Join-Path $env:LOCALAPPDATA 'BAKOQUAKE'
foreach ($f in @('ram-gb.txt', 'vram-mb.txt', 'lowgpu-applied.txt')) {
    $p = Join-Path $cache $f
    if (Test-Path -LiteralPath $p) { Add "$f = $((Get-Content -LiteralPath $p -TotalCount 1))" } else { Add "$f = (not there)" }
}
Add "BQ_LOWMEM = '$($env:BQ_LOWMEM)'  BQ_LOWGPU = '$($env:BQ_LOWGPU)'  COMBAT_ARGS = '$($env:COMBAT_ARGS)'"
Add 'Low-memory textures start under 10 GB of RAM or under 3000 MB of video memory; Simple Mode once under 3000 MB.'

Head 'Saved settings (config.cfg)'
$cfg = Join-Path $game 'config.cfg'
if (Test-Path -LiteralPath $cfg) {
    $want = '^"?(vid_width|vid_height|vid_fullscreen|vid_desktopfullscreen|vid_samples|vid_vsync|gl_picmip|gl_picmip_other|gl_texture_anisotropy|lowspec|r_bloom|r_shadow_realtime_dlight|r_shadow_realtime_dlight_shadows|r_shadow_shadowmapping_texturesize|r_glsl_offsetmapping|r_water|cl_maxfps|cl_particles_quality|gyroset|bm_defver)"? '
    Select-String -LiteralPath $cfg -Pattern $want | ForEach-Object { Add $_.Line.Trim() }
} else { Add 'no config.cfg yet (the game has not been closed normally on this PC)' }

$bad = 'Engine Error|Host_Error|out of memory|runaway loop|GL_OUT_OF_MEMORY|Sys_Error|no free edicts|SZ_GetSpace: overflow|PRVM_ExecuteProgram|server crash|could not create|video mode failed|unable to'
foreach ($name in @('bq_game.log', 'bq_game_prev.log', 'bq_server.log', 'bq_server_prev.log')) {
    $p = Join-Path $game $name
    if (-not (Test-Path -LiteralPath $p)) { continue }
    $i = Get-Item -LiteralPath $p
    Head ("Game log {0} ({1:N0} bytes, last written {2:yyyy-MM-dd HH:mm:ss})" -f $name, $i.Length, $i.LastWriteTime)
    $lines = Get-Content -LiteralPath $p
    $hits = @($lines | Select-String -Pattern $bad | Where-Object { $_.Line -notmatch 'GL_ARB_|GL_EXT_|font-file' } | Select-Object -Last 30)
    Add "-- lines that look like errors: $($hits.Count)"
    foreach ($h in $hits) { Add ("   " + $h.Line) }
    Add '-- last 60 lines'
    $lines | Select-Object -Last 60 | ForEach-Object { Add ("   " + $_) }
}
if (-not (Test-Path -LiteralPath (Join-Path $game 'bq_game.log'))) {
    Head 'Game log'
    Add 'no bq_game.log: the game was not started with Play / Start Server from this package version yet'
}

Head 'Crashes Windows recorded for the engine (30 days)'
$ev = @(Get-WinEvent -FilterHashtable @{ LogName = 'Application'; Id = 1000, 1001, 1002; StartTime = (Get-Date).AddDays(-30) } |
    Where-Object { $_.Message -match 'zircon|darkplaces' } | Select-Object -First 12)
if ($ev.Count -eq 0) {
    Add 'none. (An "Engine Error" box or a drop back to the menu is not a Windows crash: look at the game log above.)'
}
foreach ($e in $ev) {
    Add ("{0:yyyy-MM-dd HH:mm:ss}  event {1}  {2}" -f $e.TimeCreated, $e.Id, $e.ProviderName)
    ($e.Message -split "`r?`n") | Where-Object { $_ -match 'module|exception|offset|Fault|P[0-9]:|hang' } | Select-Object -First 10 | ForEach-Object { Add ("   " + $_.Trim()) }
}

$dest = Join-Path ([Environment]::GetFolderPath('Desktop')) 'BAKOQUAKE-report.txt'
if ($env:BQ_REPORT_OUT) { $dest = $env:BQ_REPORT_OUT }   # tests write somewhere else
[System.IO.File]::WriteAllLines($dest, $out)
Write-Host "Report written: $dest"
if (-not $env:BQ_REPORT_NO_OPEN) { Start-Process notepad.exe -ArgumentList "`"$dest`"" }
