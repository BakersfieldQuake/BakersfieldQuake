<#
Start DarkPlaces on the LEFT monitor. The 2017 engine has no "which display" setting (it always opens on the primary
one), so this starts it and then moves its window.

  -Borderless   fill the whole left monitor with no frame (use with -window -width <w> -height <h> sized to that monitor)
  otherwise     keep the window's size and just move it to the top-left of the left monitor
  -Monitor <n>  pick another monitor by position, left to right (0 = leftmost, the default)
  -KeepMouse    leave the mouse on. Without it the game starts with +vid_mouse 0: the old engine re-centres the mouse
                wrongly in a window at negative screen coordinates (the left monitor), and the view spins. Test runs
                are scripted and never need the mouse; playing on the left monitor is NOT supported until that is solved.

Everything after the switches goes to darkplaces.exe, e.g. a test run:
  powershell -NoProfile -File launch_left.ps1 -window -width 1280 -height 720 -game quake15 -game BakersfieldQuake +map start
and the way to play (what "Quake Left Monitor.bat" does):
  powershell -NoProfile -File launch_left.ps1 -Borderless -window -width 1680 -height 1050 -game quake15 -game BakersfieldQuake +mlook
Waits until the game exits, so it can be used from a script.
#>
[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$Borderless,
    [switch]$KeepMouse,
    [int]$Monitor = 0,
    [Parameter(ValueFromRemainingArguments = $true)] [string[]]$EngineArgs
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class QWin {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int w, int hgt, uint flags);
    [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr h, int idx);
    [DllImport("user32.dll")] public static extern int SetWindowLong(IntPtr h, int idx, int val);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
[void][QWin]::SetProcessDPIAware()

$screens = [System.Windows.Forms.Screen]::AllScreens | Sort-Object { $_.Bounds.X }
$scr = $screens[[Math]::Min($Monitor, $screens.Count - 1)]
$b = $scr.Bounds

$game = Join-Path (Split-Path (Split-Path (Split-Path (Split-Path $PSCommandPath)))) 'darkplaces.exe'
if (-not (Test-Path $game)) { $game = 'G:\Quake\Combat\darkplaces.exe' }
if (-not $KeepMouse) { $EngineArgs = @($EngineArgs) + @('+vid_mouse', '0') }
$proc = Start-Process -FilePath $game -ArgumentList $EngineArgs -WorkingDirectory (Split-Path $game) -PassThru

# wait for its window, then move it (the engine may re-create it once while starting up, so keep nudging for a few seconds)
$GWL_STYLE = -16; $WS_CAPTION = 0x00C00000; $WS_THICKFRAME = 0x00040000; $WS_SYSMENU = 0x00080000
$SWP_FRAMECHANGED = 0x20; $SWP_SHOWWINDOW = 0x40; $SWP_NOSIZE = 0x1; $SWP_NOZORDER = 0x4
$moved = 0; $last = [IntPtr]::Zero
for ($i = 0; $i -lt 400 -and -not $proc.HasExited; $i++) {
    $proc.Refresh()
    $h = $proc.MainWindowHandle
    if ($h -ne [IntPtr]::Zero) {
        $r = New-Object QWin+RECT
        [void][QWin]::GetWindowRect($h, [ref]$r)
        $onScreen = ($r.Left -ge $b.X -and $r.Left -lt $b.X + $b.Width)
        if ($h -ne $last -or -not $onScreen) {
            if ($Borderless) {
                $st = [QWin]::GetWindowLong($h, $GWL_STYLE)
                [void][QWin]::SetWindowLong($h, $GWL_STYLE, $st -band (-bnot ($WS_CAPTION -bor $WS_THICKFRAME -bor $WS_SYSMENU)))
                [void][QWin]::SetWindowPos($h, [IntPtr]::Zero, $b.X, $b.Y, $b.Width, $b.Height, $SWP_FRAMECHANGED -bor $SWP_SHOWWINDOW -bor $SWP_NOZORDER)
            } else {
                [void][QWin]::SetWindowPos($h, [IntPtr]::Zero, $b.X + 40, $b.Y + 40, 0, 0, $SWP_NOSIZE -bor $SWP_SHOWWINDOW -bor $SWP_NOZORDER)
            }
            $last = $h
            $moved++
        }
        if ($moved -gt 0 -and $i -gt 40 -and $onScreen) { break }
    }
    Start-Sleep -Milliseconds 100
}
$proc.WaitForExit()

# vid_mouse is an archived cvar: the engine saved the +vid_mouse 0 into config.cfg on exit, which left the user's own
# games with a dead mouse. Put it back to 1 now that the engine has finished writing.
if (-not $KeepMouse) {
    $cfg = Join-Path (Split-Path $game) 'BakersfieldQuake\config.cfg'
    if (Test-Path $cfg) {
        $text = Get-Content -Raw $cfg
        $fixed = $text -replace '(?m)^"vid_mouse" "0"', '"vid_mouse" "1"'
        if ($fixed -ne $text) { [System.IO.File]::WriteAllText($cfg, $fixed, (New-Object System.Text.UTF8Encoding($false))) }
    }
}
