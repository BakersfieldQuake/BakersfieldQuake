# BAKOQUAKE pre-flight hardware/RAM tiering, crash/safe-mode recovery, and background hang/crash watchdog.
#
# Preflight mode (called by Play.cmd and Start Server.cmd):
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\bq-preflight.ps1 -Root <dir> [-OutEnvFile <cmd>]
#     [-UserPreset simple|normal|high] [-DryRun] [-SimulateTotalRamGB N] [-SimulateFreeRamMB N]
#     [-SimulateVramMB N] [-SimulateIGPU] [-SimulateUnclean] [-StateDir <dir>]
#
# Watchdog mode (launched detached after starting engine):
#   powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File tools\bq-preflight.ps1
#     -Root <dir> (-WatchPid <pid> | -WatchExe <exePath>) [-WatchTier <tier>] [-WatchMarkLowGpu] [-HangThresholdSec 60]
#     [-TargetMonitorRect x,y,w,h] [-TargetDisplayMode borderless|fullscreen|windowed] [-TargetSize w,h] [-TargetMonitorPrimary 0|1]
#
# Env overrides:
#   BQ_TIER=normal|lowmem|ultralow|safemode  BQ_SAFEMODE=1  BQ_ULTRALOW=1  BQ_LOWMEM=1|0  BQ_LOWGPU=1|0
#   BQ_NO_PROMPT=1 (disable interactive dialogs)  BQ_WATCHDOG=0 (disable watchdog)
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$StateDir = '',
    [string]$OutEnvFile = '',
    [string]$UserPreset = '',
    [switch]$DryRun,
    [double]$SimulateTotalRamGB = -1,
    [double]$SimulateFreeRamMB = -1,
    [double]$SimulateCommitFreeGB = -1,
    [int]$SimulateVramMB = -1,
    [switch]$SimulateIGPU,
    [switch]$SimulateUnclean,
    [switch]$ServerMode,
    [int]$WatchPid = 0,
    [string]$WatchExe = '',
    [string]$WatchTier = '',
    [switch]$WatchMarkLowGpu,
    [switch]$WatchRestoreConfig,
    [int]$HangThresholdSec = 60,
    [string]$TargetMonitorRect = '',
    [string]$TargetDisplayMode = '',
    [string]$TargetSize = '',
    [string]$TargetMonitorPrimary = ''
)

$ErrorActionPreference = 'SilentlyContinue'

try {
    $Root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
} catch {
    $Root = $Root.TrimEnd('\')
}

if (-not $StateDir) {
    $StateDir = Join-Path $env:LOCALAPPDATA 'BAKOQUAKE'
}
$gameDir = Join-Path $Root 'BakersfieldQuake'
$sessionFlag = Join-Path $StateDir 'session-active.flag'
$lastLaunchFile = Join-Path $StateDir 'last-launch.txt'
$lowGpuDoneFile = Join-Path $StateDir 'lowgpu-applied.txt'
$preTempCfgFile = Join-Path $StateDir 'config.pre-temp.cfg'
$tierFile = Join-Path $StateDir 'tier.txt'
$ramFile = Join-Path $StateDir 'ram-gb.txt'
$vramFile = Join-Path $StateDir 'vram-mb.txt'

function Copy-LockedSafe([string]$Src, [string]$Dst) {
    try {
        if (-not (Test-Path -LiteralPath $Src)) { return $false }
        $inStream = [System.IO.File]::Open($Src, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
        try {
            $outStream = [System.IO.File]::Open($Dst, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            try { $inStream.CopyTo($outStream) } finally { $outStream.Dispose() }
        } finally { $inStream.Dispose() }
        return $true
    } catch { return $false }
}

function Preserve-CrashLog {
    $logPath = Join-Path $gameDir 'bq_game.log'
    $crashPath = Join-Path $gameDir 'bq_game_crash.log'
    if (Test-Path -LiteralPath $logPath) {
        [void](Copy-LockedSafe $logPath $crashPath)
    }
}

function Append-LastLaunch([string]$Line) {
    try {
        if (-not (Test-Path -LiteralPath $StateDir)) {
            New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
        }
        [System.IO.File]::AppendAllText($lastLaunchFile, "$Line`r`n", (New-Object System.Text.UTF8Encoding($false)))
    } catch {}
}

function Show-ChoiceDialog([string]$Title, [string]$Heading, [string]$Body, [string[]]$Buttons) {
    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        [System.Windows.Forms.Application]::EnableVisualStyles()

        $form = New-Object System.Windows.Forms.Form
        $form.Text = $Title
        $form.StartPosition = 'CenterScreen'
        $form.FormBorderStyle = 'FixedDialog'
        $form.MaximizeBox = $false
        $form.MinimizeBox = $false
        $form.TopMost = $true
        $form.BackColor = [System.Drawing.Color]::FromArgb(24, 24, 30)
        $form.ForeColor = [System.Drawing.Color]::FromArgb(240, 240, 245)
        $form.ClientSize = New-Object System.Drawing.Size(500, 250)

        $lblHead = New-Object System.Windows.Forms.Label
        $lblHead.Text = $Heading
        $lblHead.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
        $lblHead.ForeColor = [System.Drawing.Color]::FromArgb(232, 174, 18)
        $lblHead.Location = New-Object System.Drawing.Point(18, 16)
        $lblHead.Size = New-Object System.Drawing.Size(464, 26)
        $form.Controls.Add($lblHead)

        $lblBody = New-Object System.Windows.Forms.Label
        $lblBody.Text = $Body
        $lblBody.Font = New-Object System.Drawing.Font('Segoe UI', 9.5)
        $lblBody.Location = New-Object System.Drawing.Point(18, 48)
        $lblBody.Size = New-Object System.Drawing.Size(464, 138)
        $form.Controls.Add($lblBody)

        $script:bqDialogResult = $Buttons[$Buttons.Count - 1]
        $btnW = [math]::Floor((464 - (($Buttons.Count - 1) * 10)) / $Buttons.Count)
        for ($i = 0; $i -lt $Buttons.Count; $i++) {
            $bText = $Buttons[$i]
            $btn = New-Object System.Windows.Forms.Button
            $btn.Text = $bText
            $btn.Font = New-Object System.Drawing.Font('Segoe UI', 9, $(if ($i -eq 0) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }))
            $btn.FlatStyle = 'Flat'
            $btn.FlatAppearance.BorderSize = 0
            if ($i -eq 0) {
                $btn.BackColor = [System.Drawing.Color]::FromArgb(232, 174, 18)
                $btn.ForeColor = [System.Drawing.Color]::FromArgb(20, 20, 24)
            } else {
                $btn.BackColor = [System.Drawing.Color]::FromArgb(46, 48, 58)
                $btn.ForeColor = [System.Drawing.Color]::FromArgb(240, 240, 245)
            }
            $btn.Location = New-Object System.Drawing.Point((18 + $i * ($btnW + 10)), 198)
            $btn.Size = New-Object System.Drawing.Size($btnW, 34)
            $btn.Tag = $bText
            $btn.Add_Click({
                $script:bqDialogResult = [string]$this.Tag
                $form.Close()
            })
            $form.Controls.Add($btn)
            if ($i -eq 0) { $form.AcceptButton = $btn }
        }
        [void]$form.ShowDialog()
        $form.Dispose()
        return $script:bqDialogResult
    } catch {
        return $Buttons[0]
    }
}

function Invoke-ProblemReport {
    $repPs = Join-Path $Root 'tools\bq-report.ps1'
    if (-not (Test-Path -LiteralPath $repPs)) { $repPs = Join-Path $gameDir 'tools\bq-report.ps1' }
    if (Test-Path -LiteralPath $repPs) {
        Start-Process powershell.exe -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $repPs, '-Root', $Root)
    }
}

function Restore-TempConfig {
    try {
        $cfgPath = Join-Path $gameDir 'config.cfg'
        if (Test-Path -LiteralPath $preTempCfgFile) {
            if (Copy-LockedSafe $preTempCfgFile $cfgPath) {
                Remove-Item -LiteralPath $preTempCfgFile -Force -ErrorAction SilentlyContinue
                return $true
            }
        }
    } catch {}
    return $false
}

function Invoke-RelaunchSafeMode {
    $playCmd = Join-Path $Root 'Play.cmd'
    if (-not (Test-Path -LiteralPath $playCmd)) { $playCmd = Join-Path $gameDir 'launchers\Play.cmd' }
    if (Test-Path -LiteralPath $playCmd) {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = 'cmd.exe'
        $psi.Arguments = "/c `"`"$playCmd`"`""
        $psi.WorkingDirectory = $Root
        $psi.UseShellExecute = $false
        $psi.EnvironmentVariables['BQ_TIER'] = 'safemode'
        $psi.EnvironmentVariables['BQ_NO_PROMPT'] = '1'
        [void][System.Diagnostics.Process]::Start($psi)
    }
}

# ============================================================================================================
# MODE 1: BACKGROUND WATCHDOG (-WatchPid or -WatchExe)
# ============================================================================================================
if ($WatchPid -gt 0 -or $WatchExe) {
    $targetProc = $null
    if ($WatchPid -gt 0) {
        try { $targetProc = Get-Process -Id $WatchPid -ErrorAction Stop } catch { $targetProc = $null }
    } elseif ($WatchExe) {
        $normExe = $WatchExe.TrimEnd('\').ToLowerInvariant()
        $exeLeaf = ([System.IO.Path]::GetFileName($WatchExe)) -replace "'", "''"
        for ($try = 0; $try -lt 25 -and -not $targetProc; $try++) {
            $cands = @(Get-CimInstance Win32_Process -Filter "Name='$exeLeaf'" |
                Where-Object {
                    $_.ExecutablePath -and
                    $_.ExecutablePath.ToLowerInvariant() -eq $normExe -and
                    ($_.CommandLine -notmatch '-dedicated')
                } | Sort-Object CreationDate -Descending)
            if ($cands.Count -gt 0) {
                try { $targetProc = Get-Process -Id ([int]$cands[0].ProcessId) -ErrorAction Stop } catch { $targetProc = $null }
            }
            if (-not $targetProc) { Start-Sleep -Milliseconds 200 }
        }
    }

    if (-not $targetProc) {
        exit 0
    }

    # Acquire OS process handle while process is alive so .NET preserves real ExitCode after termination.
    $cachedHandle = [IntPtr]::Zero
    try { $cachedHandle = $targetProc.Handle } catch {}

    # P/Invoke SendMessageTimeoutW (hang probe), GetExitCodeProcess (reliable exit code), and Win32 window placement
    $win32Type = @'
using System;
using System.Runtime.InteropServices;
public static class BqWin32Probe {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct MONITORINFO {
        public uint cbSize;
        public RECT rcMonitor;
        public RECT rcWork;
        public uint dwFlags;
    }
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern IntPtr SendMessageTimeoutW(
        IntPtr hWnd, uint Msg, UIntPtr wParam, IntPtr lParam,
        uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetExitCodeProcess(IntPtr hProcess, out uint lpExitCode);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SetWindowPos(
        IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")]
    public static extern IntPtr MonitorFromRect(ref RECT lprc, uint dwFlags);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern bool GetMonitorInfoW(IntPtr hMonitor, ref MONITORINFO lpmi);
    [DllImport("user32.dll")]
    public static extern bool SetProcessDpiAwarenessContext(IntPtr value);
    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();

    public static void EnableDpiAwareness() {
        try {
            if (SetProcessDpiAwarenessContext(new IntPtr(-4))) return;
        } catch {}
        try { SetProcessDPIAware(); } catch {}
    }
    public static bool IsWindowResponding(IntPtr hWnd, uint timeoutMs) {
        if (hWnd == IntPtr.Zero) return true;
        UIntPtr res;
        IntPtr ret = SendMessageTimeoutW(hWnd, 0, UIntPtr.Zero, IntPtr.Zero, 0x0002, timeoutMs, out res);
        return ret != IntPtr.Zero;
    }
    public static int ReadExitCode(IntPtr hProcess) {
        if (hProcess == IntPtr.Zero) return -1;
        uint code = 0;
        if (GetExitCodeProcess(hProcess, out code) && code != 259) {
            return unchecked((int)code);
        }
        return -1;
    }
    public static bool PlaceWindow(IntPtr hWnd, string mode, int monX, int monY, int monW, int monH, int reqW, int reqH) {
        if (hWnd == IntPtr.Zero || monW <= 0 || monH <= 0) return false;
        const uint SWP_NOSIZE = 0x0001;
        const uint SWP_NOZORDER = 0x0004;
        const uint SWP_FRAMECHANGED = 0x0020;
        const uint SWP_SHOWWINDOW = 0x0040;
        const uint SWP_NOOWNERZORDER = 0x0200;
        IntPtr HWND_TOP = IntPtr.Zero;

        if (mode == "borderless") {
            return SetWindowPos(hWnd, HWND_TOP, monX, monY, monW, monH, SWP_NOOWNERZORDER | SWP_FRAMECHANGED | SWP_SHOWWINDOW);
        }
        if (mode == "windowed") {
            int workLeft = monX, workTop = monY, workRight = monX + monW, workBottom = monY + monH;
            RECT targetRect = new RECT { Left = monX, Top = monY, Right = monX + monW, Bottom = monY + monH };
            IntPtr hMon = MonitorFromRect(ref targetRect, 2);
            if (hMon != IntPtr.Zero) {
                MONITORINFO mi = new MONITORINFO();
                mi.cbSize = (uint)Marshal.SizeOf(typeof(MONITORINFO));
                if (GetMonitorInfoW(hMon, ref mi)) {
                    workLeft = mi.rcWork.Left;
                    workTop = mi.rcWork.Top;
                    workRight = mi.rcWork.Right;
                    workBottom = mi.rcWork.Bottom;
                }
            }
            int winW = reqW > 0 ? reqW : 1280;
            int winH = reqH > 0 ? reqH : 720;
            RECT cur;
            if (GetWindowRect(hWnd, out cur)) {
                int cw = cur.Right - cur.Left;
                int ch = cur.Bottom - cur.Top;
                if (cw > 100 && ch > 100) { winW = cw; winH = ch; }
            }
            int dstX = workLeft + Math.Max(0, ((workRight - workLeft) - winW) / 2);
            int dstY = workTop + Math.Max(0, ((workBottom - workTop) - winH) / 2);
            return SetWindowPos(hWnd, HWND_TOP, dstX, dstY, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOOWNERZORDER | SWP_SHOWWINDOW);
        }
        if (mode == "fullscreen") {
            return SetWindowPos(hWnd, HWND_TOP, monX, monY, monW, monH, SWP_NOOWNERZORDER | SWP_SHOWWINDOW);
        }
        return false;
    }
}
'@
    try { Add-Type -TypeDefinition $win32Type -ErrorAction SilentlyContinue } catch {}

    # One-shot multi-monitor window placement right after startup (never fights user drag or Alt+Enter later).
    $normMode = if ($TargetDisplayMode) { $TargetDisplayMode.Trim().ToLowerInvariant() } else { '' }
    $shouldPlace = ($WatchTier -ne 'safemode') -and $TargetMonitorRect -and (
        ($normMode -eq 'borderless') -or
        ($normMode -eq 'windowed') -or
        ($normMode -eq 'fullscreen' -and $TargetMonitorPrimary -eq '0')
    )
    if ($shouldPlace) {
        $rectParts = $TargetMonitorRect.Trim() -split ','
        if ($rectParts.Count -eq 4) {
            [int]$monX = 0; [int]$monY = 0; [int]$monW = 0; [int]$monH = 0
            $okRect = [int]::TryParse($rectParts[0].Trim(), [ref]$monX) -and
                      [int]::TryParse($rectParts[1].Trim(), [ref]$monY) -and
                      [int]::TryParse($rectParts[2].Trim(), [ref]$monW) -and
                      [int]::TryParse($rectParts[3].Trim(), [ref]$monH) -and
                      ($monW -gt 0) -and ($monH -gt 0)
            if ($okRect) {
                [int]$reqW = 0; [int]$reqH = 0
                if ($TargetSize) {
                    $szParts = $TargetSize.Trim() -split ','
                    if ($szParts.Count -eq 2) {
                        [void][int]::TryParse($szParts[0].Trim(), [ref]$reqW)
                        [void][int]::TryParse($szParts[1].Trim(), [ref]$reqH)
                    }
                }
                try { [BqWin32Probe]::EnableDpiAwareness() } catch {}
                $placeHwnd = [IntPtr]::Zero
                for ($poll = 0; $poll -lt 67 -and -not $targetProc.HasExited; $poll++) {
                    try { $targetProc.Refresh() } catch { break }
                    if ($targetProc.HasExited) { break }
                    $h = $targetProc.MainWindowHandle
                    if ($h -ne [IntPtr]::Zero) {
                        $vis = $true
                        try { $vis = [BqWin32Probe]::IsWindowVisible($h) } catch { $vis = $true }
                        if ($vis) {
                            $placeHwnd = $h
                            break
                        }
                    }
                    Start-Sleep -Milliseconds 150
                }
                if ($placeHwnd -ne [IntPtr]::Zero -and -not $targetProc.HasExited) {
                    Start-Sleep -Milliseconds 250
                    try {
                        $placed = [BqWin32Probe]::PlaceWindow($placeHwnd, $normMode, $monX, $monY, $monW, $monH, $reqW, $reqH)
                        Append-LastLaunch ("window_placed=$placed mode=$normMode rect=$monX,$monY,$monW,$monH size=$reqW,$reqH at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
                    } catch {}
                }
            }
        }
    }

    $hungSince = $null
    $userKilled = $false
    while (-not $targetProc.HasExited) {
        Start-Sleep -Seconds 2
        try { $targetProc.Refresh() } catch { break }
        if ($targetProc.HasExited) { break }

        $hwnd = $targetProc.MainWindowHandle
        if ($hwnd -ne [IntPtr]::Zero) {
            $responding = $true
            try { $responding = [BqWin32Probe]::IsWindowResponding($hwnd, 1000) } catch { $responding = $targetProc.Responding }
            if ($responding) {
                $hungSince = $null
            } else {
                if (-not $hungSince) { $hungSince = Get-Date }
                $hungSec = ((Get-Date) - $hungSince).TotalSeconds
                if ($hungSec -ge $HangThresholdSec) {
                    Preserve-CrashLog
                    Append-LastLaunch ("watchdog_hang=$([math]::Round($hungSec,1))s at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
                    if ($env:BQ_NO_PROMPT -eq '1') {
                        $hungSince = Get-Date
                        continue
                    }
                    $choice = Show-ChoiceDialog `
                        'BAKOQUAKE - Not Responding' `
                        "BAKOQUAKE appears to be frozen ($([int]$hungSec)s)" `
                        "The game window has stopped responding to Windows. Your log was saved to BakersfieldQuake\bq_game_crash.log.`n`nChoose 'Keep Waiting' if a huge map is still loading, or end the process to switch to Safe Mode or create a Problem Report." `
                        @('Keep Waiting', 'End & Safe Mode', 'End & Report Problem')
                    if ($choice -eq 'End & Safe Mode') {
                        $userKilled = $true
                        try { $targetProc.Kill() } catch {}
                        Start-Sleep -Milliseconds 500
                        Preserve-CrashLog
                        Invoke-RelaunchSafeMode
                        exit 0
                    } elseif ($choice -eq 'End & Report Problem') {
                        $userKilled = $true
                        try { $targetProc.Kill() } catch {}
                        Start-Sleep -Milliseconds 500
                        Preserve-CrashLog
                        Invoke-ProblemReport
                        exit 0
                    } else {
                        $hungSince = Get-Date
                    }
                }
            }
        }
    }

    try { [void]$targetProc.WaitForExit(2000) } catch {}
    $exitCode = -1
    $gotCode = $false
    if ($cachedHandle -ne [IntPtr]::Zero) {
        try {
            $c = [BqWin32Probe]::ReadExitCode($cachedHandle)
            if ($c -ne -1) { $exitCode = $c; $gotCode = $true }
        } catch {}
    }
    if (-not $gotCode) {
        try {
            $rawEc = $targetProc.ExitCode
            if ($rawEc -ne $null) { $exitCode = [int]$rawEc; $gotCode = $true }
        } catch {}
    }
    Append-LastLaunch ("exit_code=$exitCode tier=$WatchTier at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")

    if ($WatchRestoreConfig -and -not $userKilled) {
        Start-Sleep -Milliseconds 200
        if (Restore-TempConfig) {
            Append-LastLaunch ("restored_config=1 at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
        }
    }

    if ($exitCode -eq 0 -and -not $userKilled) {
        if (Test-Path -LiteralPath $sessionFlag) {
            Remove-Item -LiteralPath $sessionFlag -Force -ErrorAction SilentlyContinue
        }
        if ($WatchMarkLowGpu) {
            try {
                if (-not (Test-Path -LiteralPath $StateDir)) { New-Item -ItemType Directory -Force -Path $StateDir | Out-Null }
                [System.IO.File]::WriteAllText($lowGpuDoneFile, '1', (New-Object System.Text.UTF8Encoding($false)))
            } catch {}
        }
    } elseif (-not $userKilled) {
        Preserve-CrashLog
        if ($env:BQ_NO_PROMPT -ne '1') {
            $choice = Show-ChoiceDialog `
                'BAKOQUAKE - Unexpected Exit' `
                "BAKOQUAKE closed unexpectedly (exit code $exitCode)" `
                "The game exited abnormally. The session log was preserved as BakersfieldQuake\bq_game_crash.log.`n`nYou can retry in Safe Mode (256px textures, 1024x640 windowed, no texture compression) or generate a Problem Report zip." `
                @('Launch Safe Mode', 'Report a Problem', 'Close')
            if ($choice -eq 'Launch Safe Mode') {
                Invoke-RelaunchSafeMode
            } elseif ($choice -eq 'Report a Problem') {
                Invoke-ProblemReport
            }
        }
    }
    exit 0
}

# ============================================================================================================
# MODE 2: PRE-FLIGHT HARDWARE / LIVE RAM DETECTION & TIERING
# ============================================================================================================
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

function Classify-Gpu([string]$Name, [string]$Compat, [string]$Pnp, [uint64]$VramMb) {
    $isVirtual = ($Pnp -match '^(ROOT|SWD)\\') -or
        ($Name -match 'Parsec|Virtual|Indirect|Basic Display|Remote|RDP|Citrix|Meta |Oculus|Spacedesk|Immersed|LuminonCore|IDD|VDD|Hyper-V|VMware|VirtualBox|QXL|Microsoft Basic') -or
        ($Compat -match 'Parsec|Virtual|Citrix|Microsoft')
    if ($isVirtual) { return 'VIRTUAL' }

    # Arc dedicated cards report as "Intel(R) Arc(TM) A770 Graphics"; Meteor Lake's built-in "Intel(R) Arc(TM) Graphics" stays iGPU.
    # AMD APUs are "Radeon 680M/780M/880M" or "Vega 8"; "RX 6800M"/"RX 7600M XT" are dedicated (audit 2026-11-23, LN-01).
    $isIntelIgpu = (($Pnp -match 'VEN_8086') -or ($Name -match 'Intel')) -and ($Name -notmatch 'Arc(\(TM\))?\s+(Pro\s+)?[AB]\d')
    $isAmdApu = ($Pnp -match 'VEN_1002') -and ($Name -notmatch '\bRX\s') -and (
        ($Name -match '^AMD Radeon(\(TM\))? Graphics$') -or
        ($Name -match 'Radeon(\(TM\))?\s+(Vega\s+[0-9]|[678][0-9]0M\b)') -or
        ($VramMb -gt 0 -and $VramMb -le 2048 -and $Name -notmatch 'RX\s+\d|Pro\s+W|FirePro')
    )
    if ($isIntelIgpu -or $isAmdApu -or ($Name -match 'Integrated|APU')) { return 'iGPU' }
    return 'dGPU'
}

# 1. Live RAM & Commit (never cached!)
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$totalRamGB = if ($SimulateTotalRamGB -ge 0) { $SimulateTotalRamGB } else { [double]$cs.TotalPhysicalMemory / 1GB }
$freeRamMB = if ($SimulateFreeRamMB -ge 0) { $SimulateFreeRamMB } else { ([double]$os.FreePhysicalMemory * 1KB) / 1MB }
$commitLimitGB = ([double]$os.TotalVirtualMemorySize * 1KB) / 1GB
$commitFreeGB = if ($SimulateCommitFreeGB -ge 0) { $SimulateCommitFreeGB } else { ([double]$os.FreeVirtualMemory * 1KB) / 1GB }

# 2. GPU detection (64-bit registry VRAM, WMI fallback, exclude virtual adapters)
$gpuSummary = New-Object System.Collections.Generic.List[string]
$isIGPU = $false
$bestVramMB = 0

if ($SimulateVramMB -ge 0 -or $SimulateIGPU) {
    $isIGPU = [bool]$SimulateIGPU
    $bestVramMB = if ($SimulateVramMB -ge 0) { $SimulateVramMB } else { 0 }
    $tagSim = if ($isIGPU) { '[iGPU]' } else { '[dGPU]' }
    $gpuSummary.Add("$tagSim Simulated GPU ($bestVramMB MB)")
} else {
    $regGpus = @(Get-ItemProperty 'HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0*' |
        Where-Object { $_.PSChildName -match '^\d{4}$' })
    $wmiGpus = @(Get-CimInstance Win32_VideoController)
    $dgpuVrams = New-Object System.Collections.Generic.List[int]
    $igpuVrams = New-Object System.Collections.Generic.List[int]

    foreach ($g in $wmiGpus) {
        $pnp = [string]$g.PNPDeviceID
        $name = [string]$g.Name
        $compat = [string]$g.AdapterCompatibility
        $errCode = if ($g.ConfigManagerErrorCode -ne $null) { [int]$g.ConfigManagerErrorCode } else { 0 }

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
        $vramMb = [int][math]::Min([int]::MaxValue, [math]::Round($vramBytes / 1MB))
        $kind = Classify-Gpu $name $compat $pnp $vramMb
        $gpuSummary.Add("[$kind] $name | VRAM=${vramMb}MB | Driver=$($g.DriverVersion) | Err=$errCode | PNP=$pnp")

        if ($kind -eq 'VIRTUAL' -or $errCode -ne 0) { continue }
        if ($kind -eq 'dGPU') { $dgpuVrams.Add($vramMb) }
        elseif ($kind -eq 'iGPU') { $igpuVrams.Add($vramMb) }
    }

    if ($dgpuVrams.Count -gt 0) {
        $isIGPU = $false
        $bestVramMB = ($dgpuVrams | Measure-Object -Maximum).Maximum
    } elseif ($igpuVrams.Count -gt 0) {
        $isIGPU = $true
        $bestVramMB = ($igpuVrams | Measure-Object -Maximum).Maximum
    } else {
        $isIGPU = $true
        $bestVramMB = 0
    }
}

$interactive = (-not $DryRun) -and ($env:BQ_NO_PROMPT -ne '1')
$cancelLaunch = $false
$uncleanDetected = $SimulateUnclean -or (Test-Path -LiteralPath $sessionFlag)
$uncleanSafeMode = $false
$extraMapArg = ''

# 3. Unclean-exit / crash recovery check
if ($uncleanDetected) {
    if (-not $DryRun) { Preserve-CrashLog }
    $explicitTier = ($env:BQ_TIER -match '^(normal|lowmem|ultralow|safemode)$') -or ($env:BQ_SAFEMODE -eq '1') -or ($env:BQ_ULTRALOW -eq '1')
    if (-not $explicitTier) {
        if ($interactive) {
            $choice = Show-ChoiceDialog `
                'BAKOQUAKE - Crash / Freeze Recovery' `
                'Previous session did not close cleanly' `
                "BAKOQUAKE crashed or was force-closed during your last session. Your previous log was saved to BakersfieldQuake\bq_game_crash.log.`n`nSafe Mode starts in 1024x640 windowed mode with 256px textures and no texture compression for maximum stability." `
                @('Safe Mode (Recommended)', 'Normal Retry', 'Report a Problem')
            if ($choice -eq 'Safe Mode (Recommended)') {
                $uncleanSafeMode = $true
            } elseif ($choice -eq 'Report a Problem') {
                Invoke-ProblemReport
                $cancelLaunch = $true
            }
        } else {
            $uncleanSafeMode = $true
        }
    }
}

# 4. Auto-tiering decision
$tier = 'normal'
$reason = 'high-spec hardware and sufficient free RAM'
$weakGpu = $isIGPU -or ($bestVramMB -gt 0 -and $bestVramMB -lt 3000)

# One free-RAM reading swings with whatever else is open, and Windows trims other apps when the game needs memory.
# On PCs with 16 GB or more and a dedicated GPU, judge memory pressure from commit headroom instead (minus 1 GB margin):
# a 31 GB PC with 0.9 GB "free" but 9.9 GB of commit room was put on ultralow (audit 2026-11-23, LN-09).
$roomyPc = ($totalRamGB -ge 15.5) -and (-not $weakGpu)
$pressureFreeMB = if ($roomyPc) { [Math]::Max($freeRamMB, ($commitFreeGB - 1.0) * 1024) } else { $freeRamMB }
$normPreset = ''
if ($UserPreset -and ($UserPreset.Trim() -match '^(simple|normal|high)$')) {
    $normPreset = $UserPreset.Trim().ToLowerInvariant()
}

if ($env:BQ_TIER -match '^(normal|lowmem|ultralow|safemode)$') {
    $tier = $env:BQ_TIER.ToLowerInvariant()
    $reason = "forced by BQ_TIER=$tier"
} elseif ($env:BQ_SAFEMODE -eq '1') {
    $tier = 'safemode'
    $reason = 'forced by BQ_SAFEMODE=1'
} elseif ($env:BQ_ULTRALOW -eq '1') {
    $tier = 'ultralow'
    $reason = 'forced by BQ_ULTRALOW=1'
} elseif ($uncleanSafeMode) {
    $tier = 'safemode'
    $reason = 'unclean previous session recovery (session-active.flag)'
} elseif ($normPreset) {
    $tier = "preset-$normPreset"
    $reason = "user selected graphics preset '$normPreset' in Display Setup"
} elseif ($pressureFreeMB -lt 2048) {
    $tier = 'ultralow'
    $reason = ("live free RAM {0:N0} MB under 2048 MB" -f $pressureFreeMB)
} elseif ($isIGPU -and $freeRamMB -lt 3072) {
    $tier = 'ultralow'
    $reason = ("integrated GPU with live free RAM {0:N0} MB under 3072 MB" -f $freeRamMB)
} elseif ($totalRamGB -le 8.5) {
    $tier = 'ultralow'
    $reason = ("total RAM {0:N1} GB at or under 8 GB" -f $totalRamGB)
} elseif ($totalRamGB -lt 10.0) {
    $tier = 'lowmem'
    $reason = ("total RAM {0:N1} GB under 10 GB" -f $totalRamGB)
} elseif ($isIGPU) {
    $tier = 'lowmem'
    $reason = 'integrated GPU (shared system memory)'
} elseif ($bestVramMB -gt 0 -and $bestVramMB -lt 3000) {
    $tier = 'lowmem'
    $reason = "dedicated VRAM $bestVramMB MB under 3000 MB"
} elseif ($pressureFreeMB -lt 3584) {
    $tier = 'lowmem'
    $reason = ("live free RAM {0:N0} MB under 3584 MB" -f $pressureFreeMB)
}

# Legacy BQ_LOWMEM=1/0 overrides (only when BQ_TIER/BQ_SAFEMODE/BQ_ULTRALOW not explicitly set)
if (-not ($env:BQ_TIER -match '^(normal|lowmem|ultralow|safemode)$') -and $env:BQ_SAFEMODE -ne '1' -and $env:BQ_ULTRALOW -ne '1') {
    if ($env:BQ_LOWMEM -eq '1' -and $tier -eq 'normal') {
        $tier = 'lowmem'
        $reason = 'forced by BQ_LOWMEM=1'
    } elseif ($env:BQ_LOWMEM -eq '0' -and $tier -eq 'lowmem') {
        $tier = 'normal'
        $reason = 'overridden by BQ_LOWMEM=0'
    }
}

# 5. Pre-flight low free-RAM warning (< 1536 MB)
if (-not $cancelLaunch -and $pressureFreeMB -lt 1536 -and $interactive) {
    $top3 = @(Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 3 | ForEach-Object {
        "{0} ({1:N1} GB)" -f $_.ProcessName, ($_.WorkingSet64 / 1GB)
    })
    $topStr = if ($top3.Count -gt 0) { $top3 -join ', ' } else { '(unknown)' }
    $freeGbStr = "{0:N2}" -f ($freeRamMB / 1024.0)
    $totGbStr = "{0:N1}" -f $totalRamGB
    $hasLite = (-not $ServerMode) -and (Test-Path -LiteralPath (Join-Path $gameDir 'maps\bakersfielddowntown_lite.bsp'))
    $contLabel = if ($normPreset) { 'Continue Anyway' } else { 'Continue Ultra-Low' }
    $warnTail = if ($normPreset) {
        'Close Chrome/browser tabs or other apps for best results before continuing, or launch Lite Downtown to cut map memory.'
    } else {
        'Close Chrome/browser tabs or other apps for best results, or continue in Ultra-Low Mode (cuts map memory by ~70%).'
    }
    $btns = if ($hasLite) { @($contLabel, 'Launch Lite Downtown', 'Cancel') } else { @($contLabel, 'Cancel') }
    $choice = Show-ChoiceDialog `
        'BAKOQUAKE - Low Free RAM Warning' `
        "Only $freeGbStr GB RAM free (of $totGbStr GB total)" `
        "Your PC is very low on free memory right now. Top RAM apps:`n  $topStr`n`n$warnTail" `
        $btns
    if ($choice -eq 'Cancel') {
        $cancelLaunch = $true
    } elseif ($choice -eq 'Launch Lite Downtown') {
        if ($tier -ne 'safemode') { $tier = 'ultralow' }
        $extraMapArg = '+map bakersfielddowntown_lite'
    }
}

# 6. Build engine tier args, lowgpu persistence flag, and temporary-config snapshot decision
$engineArgsList = New-Object System.Collections.Generic.List[string]
$markLowGpu = $false
$lowGpuApplied = Test-Path -LiteralPath $lowGpuDoneFile
$explicitForcedLow = ($env:BQ_TIER -match '^(lowmem|ultralow)$') -or ($env:BQ_ULTRALOW -eq '1') -or ($env:BQ_LOWMEM -eq '1')
# Temporary tier: Safe Mode (always), OR a transient free-RAM-only drop on a capable PC (>=10 GB RAM, non-weak dGPU).
# Snapshotting config.cfg prevents CF_ARCHIVE cvars written on clean exit from permanently locking the player in Safe Mode / Ultra-Low.
$isTemporaryTier = ($tier -eq 'safemode') -or (
    ($tier -in @('ultralow', 'lowmem')) -and (-not $weakGpu) -and ($totalRamGB -ge 10.0) -and (-not $explicitForcedLow)
)

if ($tier -eq 'safemode') {
    $engineArgsList.Add('+exec safemode.cfg')
} elseif ($tier -eq 'ultralow') {
    $engineArgsList.Add('+exec ultralow.cfg')
    if ($weakGpu -and -not $lowGpuApplied -and $env:BQ_LOWGPU -ne '0') { $markLowGpu = $true }
} elseif ($tier -eq 'lowmem') {
    $engineArgsList.Add('+exec lowmem.cfg')
    if ($env:BQ_LOWGPU -eq '1' -or ($weakGpu -and -not $lowGpuApplied -and $env:BQ_LOWGPU -ne '0')) {
        $engineArgsList.Add('+exec lowgpu.cfg')
        if ($weakGpu -and -not $lowGpuApplied) { $markLowGpu = $true }
    }
} else {
    # normal tier: zero visual/memory overrides unless user explicitly sets BQ_LOWGPU=1
    if ($env:BQ_LOWGPU -eq '1') {
        $engineArgsList.Add('+exec lowgpu.cfg')
    }
}

if ($extraMapArg) {
    $engineArgsList.Add($extraMapArg)
}
$engineArgs = ($engineArgsList -join ' ')

# 7. Persist pre-launch telemetry, temporary config snapshot/restore, & session marker (unless -DryRun or cancelled)
$restoreConfigOnExit = $false
if (-not $DryRun -and -not $cancelLaunch) {
    try {
        if (-not (Test-Path -LiteralPath $StateDir)) { New-Item -ItemType Directory -Force -Path $StateDir | Out-Null }
        $cfgPath = Join-Path $gameDir 'config.cfg'
        if ($isTemporaryTier) {
            if ((Test-Path -LiteralPath $cfgPath) -and (-not (Test-Path -LiteralPath $preTempCfgFile))) {
                [void](Copy-LockedSafe $cfgPath $preTempCfgFile)
            }
            if (Test-Path -LiteralPath $preTempCfgFile) {
                $restoreConfigOnExit = $true
            }
        } elseif (Test-Path -LiteralPath $preTempCfgFile) {
            # Recover original config.cfg if a previous temporary session's watchdog was skipped/killed
            [void](Restore-TempConfig)
        }

        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($ramFile, ([string][math]::Round($totalRamGB)), $utf8)
        [System.IO.File]::WriteAllText($vramFile, ([string]$bestVramMB), $utf8)
        [System.IO.File]::WriteAllText($tierFile, $tier, $utf8)
        [System.IO.File]::WriteAllText($sessionFlag, ("started=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') tier=$tier"), $utf8)

        $launchInfo = @(
            "timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            "root=$Root"
            "tier=$tier"
            "user_preset=$normPreset"
            "temporary_tier=$isTemporaryTier"
            "reason=$reason"
            "ram_total_gb=$([math]::Round($totalRamGB, 2))"
            "ram_free_mb=$([math]::Round($freeRamMB, 0))"
            "commit_limit_gb=$([math]::Round($commitLimitGB, 2))"
            "commit_free_gb=$([math]::Round($commitFreeGB, 2))"
            "is_igpu=$isIGPU"
            "best_vram_mb=$bestVramMB"
            "unclean_prev=$uncleanDetected"
            "engine_args=$engineArgs"
        )
        foreach ($gs in $gpuSummary) { $launchInfo += "gpu=$gs" }
        [System.IO.File]::WriteAllLines($lastLaunchFile, $launchInfo, $utf8)
    } catch {}

    # Safe bq_game.log rotation: move if unlocked, else locked-safe copy so evidence is never lost
    $curLog = Join-Path $gameDir 'bq_game.log'
    $prevLog = Join-Path $gameDir 'bq_game_prev.log'
    if (Test-Path -LiteralPath $curLog) {
        try {
            if (Test-Path -LiteralPath $prevLog) { Remove-Item -LiteralPath $prevLog -Force -ErrorAction SilentlyContinue }
            Move-Item -LiteralPath $curLog -Destination $prevLog -Force -ErrorAction Stop
        } catch {
            [void](Copy-LockedSafe $curLog $prevLog)
        }
    }
} elseif ($DryRun -and $isTemporaryTier) {
    $restoreConfigOnExit = $true
}

$cancelInt = if ($cancelLaunch) { 1 } else { 0 }
$markInt = if ($markLowGpu) { 1 } else { 0 }
$restoreInt = if ($restoreConfigOnExit) { 1 } else { 0 }
$safeReason = $reason -replace '["\r\n&|<>^%]', ' '

if ($OutEnvFile) {
    $envLines = @(
        "set `"BQ_PRE_TIER=$tier`""
        "set `"BQ_PRE_ARGS=$engineArgs`""
        "set `"BQ_PRE_CANCEL=$cancelInt`""
        "set `"BQ_PRE_MARK_LOWGPU=$markInt`""
        "set `"BQ_PRE_RESTORE_CONFIG=$restoreInt`""
        "set `"BQ_PRE_REASON=$safeReason`""
        "set `"BQ_PRE_LOG_ROTATED=1`""
    )
    [System.IO.File]::WriteAllLines($OutEnvFile, $envLines, [System.Text.Encoding]::ASCII)
}

Write-Output "BQ_PRE_TIER=$tier"
Write-Output "BQ_PRE_ARGS=$engineArgs"
Write-Output "BQ_PRE_CANCEL=$cancelInt"
Write-Output "BQ_PRE_MARK_LOWGPU=$markInt"
Write-Output "BQ_PRE_RESTORE_CONFIG=$restoreInt"
Write-Output "BQ_PRE_TOTAL_RAM_GB=$([math]::Round($totalRamGB, 2))"
Write-Output "BQ_PRE_FREE_RAM_MB=$([math]::Round($freeRamMB, 0))"
Write-Output "BQ_PRE_VRAM_MB=$bestVramMB"
Write-Output "BQ_PRE_IS_IGPU=$isIGPU"
Write-Output "BQ_PRE_REASON=$safeReason"
exit 0
