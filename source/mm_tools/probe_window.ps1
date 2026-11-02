param([int]$ProcId)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class QProbe {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
[void][QProbe]::SetProcessDPIAware()
$p = Get-Process -Id $ProcId
$p.Refresh()
$r = New-Object QProbe+RECT
[void][QProbe]::GetWindowRect($p.MainWindowHandle, [ref]$r)
'window {0},{1} to {2},{3}  ({4}x{5})  title: {6}' -f $r.Left, $r.Top, $r.Right, $r.Bottom, ($r.Right - $r.Left), ($r.Bottom - $r.Top), $p.MainWindowTitle
