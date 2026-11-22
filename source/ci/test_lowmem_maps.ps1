<#
.SYNOPSIS
    Automated low-memory & responsiveness regression suite for BAKOQUAKE / Zircon.

.DESCRIPTION
    Launches Zircon in a completely isolated temporary -userdir (never modifying
    the user's config.cfg or game files) for every shipped map (or a chosen list),
    sampling every ~200 ms:
      - Wall-clock load time (launch -> first rendered frame)
      - Peak Working Set, Private Bytes, and Commit (pre-quit gameplay peak)
      - Peak Dedicated GPU Memory (via Windows PDH when available)
      - Longest continuous Win32 "Not Responding" streak (SendMessageTimeoutW
        SMTO_ABORTIFHUNG) during map load
      - Steady-state FPS (timerefresh)
      - Clean exit / absence of Mem_Alloc OOM, Sys_Error, Host_Error, or crash

    Supports optional Windows Job Object commit caps (-CommitCapMB), repeated cold
    starts (-Repeat), map-change peak testing (-TestMapChange), graceful OOM
    verification (-TestOOMGraceful), and JSON / Markdown report export.

    Exits 0 ONLY when every enabled test passes every budget; exits 1 otherwise.

.EXAMPLE
    .\source\ci\test_lowmem_maps.ps1 -Tier ultralow -CommitCapMB 2048 -OutMarkdown report.md

.EXAMPLE
    .\source\ci\test_lowmem_maps.ps1 -Engine G:\Quake\_bq_fork_engine\out\zircon_beta_lowmem.exe `
        -Maps bakersfielddowntown,bakersfielddowntown_lite,soi6 -Tier ultralow `
        -CommitCapMB 2048 -Repeat 3 -TestMapChange -TestOOMGraceful
#>
[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$Engine = "",
    [string[]]$Maps = @(),
    [ValidateSet("normal", "lowmem", "ultralow", "safemode")]
    [string]$Tier = "ultralow",
    [int]$CommitCapMB = -1,
    [double]$MaxLoadSeconds = 30.0,
    [int]$MaxPeakCommitMB = 2000,
    [double]$MaxNotRespondingSeconds = 4.5,
    [double]$MinFps = 0.0,
    [int]$Repeat = 1,
    [int]$TimeoutSeconds = 90,
    [int]$SampleMs = 200,
    [switch]$TestMapChange,
    [string]$MapChangeFrom = "soi6",
    [string]$MapChangeTo = "bakersfielddowntown",
    [switch]$TestOOMGraceful,
    [int]$OOMCapMB = 400,
    [string]$OutJson = "",
    [string]$OutMarkdown = "",
    [string]$TempRoot = "",
    [switch]$KeepLogs,
    [switch]$ForceTimeRefresh,
    [string[]]$ExtraCmds = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Resolve package / dev-tree root ---
function Resolve-GameRoot {
    param([string]$Hint)
    if ($Hint) {
        $resolved = (Resolve-Path -LiteralPath $Hint).Path.TrimEnd("\")
        return $resolved
    }
    $p1 = Split-Path -Parent $PSScriptRoot
    $p2 = if ($p1) { Split-Path -Parent $p1 } else { $null }
    $p3 = if ($p2) { Split-Path -Parent $p2 } else { $null }
    $candidates = @(
        $p1,
        $p2,
        $p3,
        $PSScriptRoot
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath (Join-Path $c "BakersfieldQuake"))) {
            if ((Test-Path -LiteralPath (Join-Path $c "engine\zircon_beta_gcc.exe")) -or
                (Test-Path -LiteralPath (Join-Path $c "id1\pak0.pak"))) {
                return (Resolve-Path -LiteralPath $c).Path.TrimEnd("\")
            }
        }
    }
    throw "Could not locate BAKOQUAKE root (containing BakersfieldQuake\ and engine\). Pass -Root explicitly."
}

$GameRoot = Resolve-GameRoot -Hint $Root
$GameDir  = Join-Path $GameRoot "BakersfieldQuake"
if (-not $Engine) {
    $Engine = Join-Path $GameRoot "engine\zircon_beta_gcc.exe"
}
if (-not (Test-Path -LiteralPath $Engine)) {
    throw "Engine binary not found: $Engine"
}
$Engine = (Resolve-Path -LiteralPath $Engine).Path

# Auto-default CommitCapMB when not explicitly set (-1)
if ($CommitCapMB -lt 0) {
    if ($Tier -eq "ultralow" -or $Tier -eq "safemode") {
        $CommitCapMB = 2048
    } else {
        $CommitCapMB = 0
    }
}

# --- Native Win32 + Job Object + PDH GPU Memory helpers ---
if (-not ("BqLowMemNative" -as [type])) {
    Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class BqLowMemNative
{
    public const uint SMTO_BLOCK = 0x0001;
    public const uint SMTO_ABORTIFHUNG = 0x0002;
    public const uint WM_NULL = 0x0000;

    public const uint JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100;
    public const uint JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200;
    public const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;
    public const int JobObjectExtendedLimitInformation = 9;

    public const uint PDH_FMT_LARGE = 0x00000400;

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsHungAppWindow(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern IntPtr SendMessageTimeoutW(
        IntPtr hWnd, uint Msg, UIntPtr wParam, IntPtr lParam,
        uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowTextW(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_MEMORY_COUNTERS_EX
    {
        public uint cb;
        public uint PageFaultCount;
        public UIntPtr PeakWorkingSetSize;
        public UIntPtr WorkingSetSize;
        public UIntPtr QuotaPeakPagedPoolUsage;
        public UIntPtr QuotaPagedPoolUsage;
        public UIntPtr QuotaPeakNonPagedPoolUsage;
        public UIntPtr QuotaNonPagedPoolUsage;
        public UIntPtr PagefileUsage;
        public UIntPtr PeakPagefileUsage;
        public UIntPtr PrivateUsage;
    }

    [DllImport("psapi.dll", SetLastError = true)]
    public static extern bool GetProcessMemoryInfo(
        IntPtr Process, out PROCESS_MEMORY_COUNTERS_EX ppsmemCounters, uint cb);

    [StructLayout(LayoutKind.Sequential)]
    public struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern IntPtr CreateJobObjectW(IntPtr lpJobAttributes, string lpName);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool SetInformationJobObject(
        IntPtr hJob, int JobObjectInfoClass, ref JOBOBJECT_EXTENDED_LIMIT_INFORMATION lpJobObjectInfo, uint cbJobObjectInfoLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr hObject);

    [StructLayout(LayoutKind.Sequential)]
    public struct PDH_FMT_COUNTERVALUE
    {
        public uint CStatus;
        public long largeValue;
    }

    [DllImport("pdh.dll", CharSet = CharSet.Unicode)]
    public static extern int PdhOpenQueryW(string szDataSource, IntPtr dwUserData, out IntPtr phQuery);

    [DllImport("pdh.dll", CharSet = CharSet.Unicode)]
    public static extern int PdhAddEnglishCounterW(IntPtr hQuery, string szFullCounterPath, IntPtr dwUserData, out IntPtr phCounter);

    [DllImport("pdh.dll")]
    public static extern int PdhCollectQueryData(IntPtr hQuery);

    [DllImport("pdh.dll")]
    public static extern int PdhGetFormattedCounterValue(IntPtr hCounter, uint dwFormat, out uint lpdwType, out PDH_FMT_COUNTERVALUE pValue);

    [DllImport("pdh.dll")]
    public static extern int PdhCloseQuery(IntPtr hQuery);

    [DllImport("pdh.dll", CharSet = CharSet.Unicode)]
    public static extern int PdhExpandWildCardPathW(string szDataSource, string szWildCardPath, char[] mszExpandedPathList, ref uint pcchPathListLength, uint dwFlags);

    public static IntPtr CreateMemoryCapJob(ulong limitBytes)
    {
        IntPtr job = CreateJobObjectW(IntPtr.Zero, null);
        if (job == IntPtr.Zero) return IntPtr.Zero;
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
        info.BasicLimitInformation.LimitFlags =
            JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        info.ProcessMemoryLimit = new UIntPtr(limitBytes);
        info.JobMemoryLimit = new UIntPtr(limitBytes);
        uint sz = (uint)Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
        if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, ref info, sz))
        {
            CloseHandle(job);
            return IntPtr.Zero;
        }
        return job;
    }

    public static List<IntPtr> FindVisibleWindows(int pid)
    {
        var list = new List<IntPtr>();
        EnumWindows((hWnd, lParam) => {
            uint wpid = 0;
            GetWindowThreadProcessId(hWnd, out wpid);
            if (wpid == (uint)pid && IsWindowVisible(hWnd))
            {
                list.Add(hWnd);
            }
            return true;
        }, IntPtr.Zero);
        return list;
    }

    public static string GetTitle(IntPtr hWnd)
    {
        var sb = new StringBuilder(256);
        GetWindowTextW(hWnd, sb, sb.Capacity);
        return sb.ToString();
    }

    public static bool CheckResponsive(IntPtr hWnd, uint timeoutMs)
    {
        UIntPtr res;
        IntPtr ok = SendMessageTimeoutW(hWnd, WM_NULL, UIntPtr.Zero, IntPtr.Zero, SMTO_ABORTIFHUNG | SMTO_BLOCK, timeoutMs, out res);
        bool hung = IsHungAppWindow(hWnd);
        return (ok != IntPtr.Zero) && !hung;
    }

    public static bool TryGetMemory(IntPtr hProcess, out double wsMB, out double peakWsMB, out double privMB, out double commitMB, out double peakCommitMB, out uint pageFaults)
    {
        PROCESS_MEMORY_COUNTERS_EX pmc;
        pmc.cb = (uint)Marshal.SizeOf(typeof(PROCESS_MEMORY_COUNTERS_EX));
        if (GetProcessMemoryInfo(hProcess, out pmc, pmc.cb))
        {
            wsMB = pmc.WorkingSetSize.ToUInt64() / 1048576.0;
            peakWsMB = pmc.PeakWorkingSetSize.ToUInt64() / 1048576.0;
            privMB = pmc.PrivateUsage.ToUInt64() / 1048576.0;
            commitMB = pmc.PagefileUsage.ToUInt64() / 1048576.0;
            peakCommitMB = pmc.PeakPagefileUsage.ToUInt64() / 1048576.0;
            pageFaults = pmc.PageFaultCount;
            return true;
        }
        wsMB = peakWsMB = privMB = commitMB = peakCommitMB = 0;
        pageFaults = 0;
        return false;
    }
}

public class BqGpuMemSampler : IDisposable
{
    private readonly int _pid;
    private IntPtr _query = IntPtr.Zero;
    private readonly List<IntPtr> _dedCounters = new List<IntPtr>();
    private DateTime _lastExpand = DateTime.MinValue;

    public BqGpuMemSampler(int pid)
    {
        _pid = pid;
    }

    private void Rebind()
    {
        if (_query != IntPtr.Zero)
        {
            BqLowMemNative.PdhCloseQuery(_query);
            _query = IntPtr.Zero;
            _dedCounters.Clear();
        }
        IntPtr q;
        if (BqLowMemNative.PdhOpenQueryW(null, IntPtr.Zero, out q) != 0) return;
        _query = q;
        string wildcard = string.Format("\\GPU Process Memory(pid_{0}_*)\\Dedicated Usage", _pid);
        uint len = 0;
        BqLowMemNative.PdhExpandWildCardPathW(null, wildcard, null, ref len, 0);
        if (len > 0)
        {
            char[] buf = new char[len + 2];
            if (BqLowMemNative.PdhExpandWildCardPathW(null, wildcard, buf, ref len, 0) == 0)
            {
                string raw = new string(buf, 0, (int)len);
                foreach (string p in raw.Split('\0'))
                {
                    if (string.IsNullOrEmpty(p)) continue;
                    IntPtr ch;
                    if (BqLowMemNative.PdhAddEnglishCounterW(_query, p, IntPtr.Zero, out ch) == 0)
                    {
                        _dedCounters.Add(ch);
                    }
                }
            }
        }
        if (_dedCounters.Count > 0)
        {
            BqLowMemNative.PdhCollectQueryData(_query);
        }
    }

    public double SampleDedicatedMB()
    {
        var now = DateTime.UtcNow;
        if (_dedCounters.Count == 0 || (now - _lastExpand).TotalSeconds > 2.0)
        {
            Rebind();
            _lastExpand = now;
        }
        if (_query == IntPtr.Zero || _dedCounters.Count == 0) return 0.0;
        if (BqLowMemNative.PdhCollectQueryData(_query) != 0) return 0.0;
        long total = 0;
        foreach (IntPtr ch in _dedCounters)
        {
            uint ctype;
            BqLowMemNative.PDH_FMT_COUNTERVALUE val;
            if (BqLowMemNative.PdhGetFormattedCounterValue(ch, BqLowMemNative.PDH_FMT_LARGE, out ctype, out val) == 0)
            {
                if (val.largeValue > 0) total += val.largeValue;
            }
        }
        return total / 1048576.0;
    }

    public void Dispose()
    {
        if (_query != IntPtr.Zero)
        {
            BqLowMemNative.PdhCloseQuery(_query);
            _query = IntPtr.Zero;
            _dedCounters.Clear();
        }
    }
}
"@ -Language CSharp
}

# --- Helper: safe text write (UTF-8 no BOM) ---
function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

# --- Helper: read log safely even while Zircon holds file open ---
function Read-LogChunk {
    param([string]$Path, [ref]$Offset)
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    try {
        $fs = New-Object System.IO.FileStream($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            if ($fs.Length -le $Offset.Value) { return "" }
            $fs.Seek($Offset.Value, [System.IO.SeekOrigin]::Begin) | Out-Null
            $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8, $true)
            $txt = $sr.ReadToEnd()
            $Offset.Value = $fs.Position
            return $txt
        } finally {
            $fs.Dispose()
        }
    } catch {
        return ""
    }
}

function Read-LogAll {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    try {
        $fs = New-Object System.IO.FileStream($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8, $true)
            return $sr.ReadToEnd()
        } finally {
            $fs.Dispose()
        }
    } catch {
        return ""
    }
}

# --- Helper: kill ONLY our spawned PID and any direct child ---
function Stop-SpawnedProcessTree {
    param([System.Diagnostics.Process]$Proc)
    if (-not $Proc) { return }
    try {
        $pidToKill = $Proc.Id
        try {
            $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $pidToKill" -ErrorAction SilentlyContinue
            foreach ($c in $children) {
                try { Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
            }
        } catch {}
        if (-not $Proc.HasExited) {
            $Proc.Kill()
            $Proc.WaitForExit(5000) | Out-Null
        }
    } catch {}
}

# --- Build isolated tier config lines & runtime exec commands ---
function Get-TierSetup {
    param([string]$TierName, [string]$BqGameDir)
    $winW = 1280
    $winH = 800
    $cfg = New-Object System.Collections.Generic.List[string]
    $cmds = New-Object System.Collections.Generic.List[string]

    if ($TierName -eq "safemode") {
        $winW = 1024
        $winH = 640
    }

    $cfg.Add("// isolated test_lowmem_maps.ps1 config")
    $cfg.Add('vid_fullscreen "0"')
    $cfg.Add('vid_desktopfullscreen "0"')
    $cfg.Add("vid_width `"$winW`"")
    $cfg.Add("vid_height `"$winH`"")
    $cfg.Add("_vid_window_width `"$winW`"")
    $cfg.Add("_vid_window_height `"$winH`"")
    $cfg.Add('vid_vsync "0"')
    $cfg.Add('cl_maxfps "0"')
    $cfg.Add('cl_maxidlefps "0"')
    $cfg.Add('cl_minfps "0"')
    $cfg.Add('bgmvolume "0"')
    $cfg.Add('volume "0"')
    $cfg.Add('seta menu_background "0"')

    $tierSource = $TierName
    switch ($TierName) {
        "normal" {
            $cfg.Add('seta lowspec "0"')
            $cfg.Add('vid_samples "4"')
            $cfg.Add('gl_texture_anisotropy "16"')
            $cfg.Add('gl_picmip "0"')
            $cfg.Add('gl_picmip_other "0"')
            $cfg.Add('gl_picmip_world "0"')
            $cfg.Add('gl_picmip_sprites "0"')
            $cfg.Add('r_bloom "1"')
            $cfg.Add('r_shadow_realtime_dlight "1"')
            $cfg.Add('r_shadow_realtime_dlight_shadows "1"')
            $cfg.Add('r_shadow_shadowmapping "1"')
            $cfg.Add('r_shadow_shadowmapping_texturesize "4096"')
            $cfg.Add('r_water "1"')
            $cmds.Add("developer 0")
        }
        "lowmem" {
            $cfg.Add('seta lowspec "1"')
            $cfg.Add('vid_samples "1"')
            $cfg.Add('gl_texture_anisotropy "4"')
            $cfg.Add('r_bloom "0"')
            $cfg.Add('r_shadow_realtime_dlight "0"')
            $cfg.Add('r_shadow_realtime_dlight_shadows "0"')
            $cfg.Add('r_shadow_shadowmapping "0"')
            $cfg.Add('r_water "0"')
            $cmds.Add("exec lowmem.cfg")
            $cmds.Add("exec lowgpu.cfg")
            $cmds.Add("developer 0")
        }
        "ultralow" {
            $cfg.Add('seta lowspec "1"')
            $cfg.Add('vid_samples "1"')
            $cfg.Add('gl_texture_anisotropy "1"')
            $cfg.Add('r_bloom "0"')
            $cfg.Add('r_shadow_realtime_dlight "0"')
            $cfg.Add('r_shadow_realtime_dlight_shadows "0"')
            $cfg.Add('r_shadow_shadowmapping "0"')
            $cfg.Add('r_water "0"')
            if (Test-Path -LiteralPath (Join-Path $BqGameDir "ultralow.cfg")) {
                $cmds.Add("exec ultralow.cfg")
                $tierSource = "ultralow.cfg"
            } else {
                # Fallback matching ultralow_512_comp if ultralow.cfg is not yet present
                $tierSource = "ultralow(fallback)"
                $cmds.Add("exec lowmem.cfg")
                $cmds.Add("exec lowgpu.cfg")
                $cmds.Add("gl_picmip_world 1")
                $cmds.Add("gl_picmip_other 2")
                $cmds.Add("gl_picmip_sprites 1")
                $cmds.Add("gl_picmip_force 1")
                $cmds.Add("gl_max_size 512")
                $cmds.Add("gl_texturecompression 1")
                $cmds.Add("gl_texturecompression_color 1")
                $cmds.Add("gl_texturecompression_q3bsplightmaps 0")
                $cmds.Add("gl_texturecompression_2d 0")
                $cmds.Add("r_shadow_shadowmapping_texturesize 512")
                $cmds.Add("r_load_normalmap 0")
                $cmds.Add("r_load_gloss 0")
                $cmds.Add("mod_freebeforeload 1")
                $cmds.Add("mod_q1bsp_pvs_ondemand 1")
                $cmds.Add("mod_q1bsp_lazy_render_bih 1")
            }
            $cmds.Add("developer 0")
        }
        "safemode" {
            $cfg.Add('seta lowspec "1"')
            $cfg.Add('vid_samples "1"')
            $cfg.Add('gl_texture_anisotropy "1"')
            $cfg.Add('r_bloom "0"')
            $cfg.Add('r_shadow_realtime_dlight "0"')
            $cfg.Add('r_shadow_realtime_dlight_shadows "0"')
            $cfg.Add('r_shadow_shadowmapping "0"')
            $cfg.Add('r_water "0"')
            if (Test-Path -LiteralPath (Join-Path $BqGameDir "safemode.cfg")) {
                $cmds.Add("exec safemode.cfg")
                $tierSource = "safemode.cfg"
            } else {
                $tierSource = "safemode(fallback)"
                $cmds.Add("exec lowmem.cfg")
                $cmds.Add("exec lowgpu.cfg")
                $cmds.Add("gl_texturecompression 0")
                $cmds.Add("gl_max_size 256")
                $cmds.Add("gl_picmip 2")
                $cmds.Add("gl_picmip_world 2")
                $cmds.Add("gl_picmip_other 2")
                $cmds.Add("gl_picmip_sprites 1")
                $cmds.Add("gl_picmip_force 1")
                $cmds.Add("r_shadow_shadowmapping_texturesize 512")
                $cmds.Add("r_load_normalmap 0")
                $cmds.Add("r_load_gloss 0")
                $cmds.Add("mod_freebeforeload 1")
                $cmds.Add("mod_q1bsp_pvs_ondemand 1")
                $cmds.Add("mod_q1bsp_lazy_render_bih 1")
            }
            $cmds.Add("developer 0")
        }
    }

    # Ensure measurement cvars aren't throttled by tier's cl_maxfps 60
    $cmds.Add("menu_background 0")
    $cmds.Add("vid_vsync 0")
    $cmds.Add("cl_maxfps 0")
    $cmds.Add("cl_maxidlefps 0")
    $cmds.Add("cl_minfps 0")
    foreach ($ec in $ExtraCmds) {
        if ($ec) {
            foreach ($part in ($ec -split ";")) {
                $t = $part.Trim()
                if ($t) { $cmds.Add($t) }
            }
        }
    }

    return [pscustomobject]@{
        WinW       = $winW
        WinH       = $winH
        CfgLines   = $cfg.ToArray()
        CmdLines   = $cmds.ToArray()
        TierSource = $tierSource
    }
}

# --- Execute a single isolated run ---
function Invoke-SingleRun {
    param(
        [string]$RunId,
        [string]$MapName,
        [string]$SecondMap = "",
        [string]$TierName,
        [int]$CapMB = 0,
        [int]$RunTimeoutSec = 90,
        [bool]$ExpectOOM = $false,
        [bool]$RunTimeRefresh = $true,
        [string]$SessionTempRoot
    )

    $runDir = Join-Path $SessionTempRoot $RunId
    $bqUserDir = Join-Path $runDir "BakersfieldQuake"
    New-Item -ItemType Directory -Path $bqUserDir -Force | Out-Null

    $tierSetup = Get-TierSetup -TierName $TierName -BqGameDir $GameDir

    # Neutralize developer personal.cfg / personal_post.cfg cleanly inside temp -userdir
    Write-Utf8NoBom -Path (Join-Path $bqUserDir "personal.cfg") -Content "// isolated regression run`n"
    Write-Utf8NoBom -Path (Join-Path $bqUserDir "personal_post.cfg") -Content "// isolated regression run`n"
    Write-Utf8NoBom -Path (Join-Path $bqUserDir "config.cfg") -Content (($tierSetup.CfgLines -join "`n") + "`n")

    $script = New-Object System.Collections.Generic.List[string]
    $script.Add("timestamps 1")
    foreach ($line in $tierSetup.CmdLines) { $script.Add($line) }

    if ($ExpectOOM) {
        # Defer map load briefly so log is guaranteed open even on unpatched engines
        $script.Add("defer 0.25 `"echo PROF_EVENT_START_LOAD; map $MapName`"")
        $script.Add("defer 2.0 `"echo PROF_EVENT_UNEXPECTED_PASS; quit`"")
    } elseif ($SecondMap) {
        $script.Add("echo PROF_EVENT_START_LOAD")
        $script.Add("map $MapName")
        $script.Add('defer 0.05 "echo PROF_EVENT_FIRST_FRAME"')
        $script.Add("defer 1.0 `"echo PROF_EVENT_MAPCHANGE; map $SecondMap`"")
        $script.Add('defer 3.0 "echo PROF_EVENT_POSTLOAD; memstats; echo PROF_EVENT_QUIT; quit"')
    } else {
        $script.Add("echo PROF_EVENT_START_LOAD")
        $script.Add("map $MapName")
        $script.Add('defer 0.05 "echo PROF_EVENT_FIRST_FRAME"')
        $post = New-Object System.Collections.Generic.List[string]
        $post.Add("echo PROF_EVENT_POSTLOAD")
        $post.Add("memstats")
        if ($RunTimeRefresh) {
            $post.Add("echo PROF_EVENT_TIMEREFRESH_START")
            $post.Add("timerefresh")
            $post.Add("echo PROF_EVENT_TIMEREFRESH_END")
        }
        $post.Add("echo PROF_EVENT_QUIT")
        $post.Add("quit")
        $script.Add('defer 2.5 "' + ($post -join '; ') + '"')
    }

    Write-Utf8NoBom -Path (Join-Path $bqUserDir "reg_test.cfg") -Content (($script.ToArray() -join "`n") + "`n")
    $logPath = Join-Path $bqUserDir "bq_game.log"

    $argList = @(
        "-basedir", "`"$GameRoot`"",
        "-userdir", "`"$runDir`"",
        "-game", "quake15",
        "-game", "BakersfieldQuake",
        "-window",
        "-width", "$($tierSetup.WinW)",
        "-height", "$($tierSetup.WinH)",
        "+log_file", "bq_game.log",
        "+timestamps", "1",
        "+exec", "reg_test.cfg"
    ) -join " "

    $jobHandle = [IntPtr]::Zero
    $proc = $null
    $gpuSampler = $null
    $exitCode = $null
    $timedOut = $false
    $oomDetected = $false
    $errorNote = ""
    $tFirstFrame = $null
    $tPostLoad = $null
    $tQuitCmd = $null
    $logOffset = [long]0
    $samples = New-Object System.Collections.Generic.List[object]
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        if ($CapMB -gt 0) {
            $limitBytes = [uint64]$CapMB * ([uint64]1048576)
            $jobHandle = [BqLowMemNative]::CreateMemoryCapJob($limitBytes)
            if ($jobHandle -eq [IntPtr]::Zero) {
                throw "CreateMemoryCapJob($CapMB MB) failed with Win32 error $([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())"
            }
        }

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Engine
        $psi.Arguments = $argList
        $psi.WorkingDirectory = (Split-Path -Parent $Engine)
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError = $false

        $proc = [System.Diagnostics.Process]::Start($psi)
        $sw.Restart()

        if ($jobHandle -ne [IntPtr]::Zero) {
            $assigned = [BqLowMemNative]::AssignProcessToJobObject($jobHandle, $proc.Handle)
            if (-not $assigned) {
                $errorNote = "AssignProcessToJobObject failed ($([System.Runtime.InteropServices.Marshal]::GetLastWin32Error()))"
            }
        }

        $gpuSampler = New-Object BqGpuMemSampler($proc.Id)
        $hwnd = [IntPtr]::Zero
        $modalTitles = New-Object System.Collections.Generic.HashSet[string]

        while ($true) {
            $loopStart = $sw.Elapsed.TotalSeconds
            if ($proc.HasExited) {
                $exitCode = $proc.ExitCode
                break
            }
            if ($loopStart -ge $RunTimeoutSec) {
                $timedOut = $true
                break
            }

            $chunk = Read-LogChunk -Path $logPath -Offset ([ref]$logOffset)
            if ($chunk) {
                if ($null -eq $tFirstFrame -and $chunk.Contains("PROF_EVENT_FIRST_FRAME")) {
                    $tFirstFrame = [math]::Round($loopStart, 2)
                }
                if ($null -eq $tPostLoad -and $chunk.Contains("PROF_EVENT_POSTLOAD")) {
                    $tPostLoad = [math]::Round($loopStart, 2)
                }
                if ($null -eq $tQuitCmd -and ($chunk.Contains("PROF_EVENT_TIMEREFRESH_START") -or $chunk.Contains("PROF_EVENT_QUIT"))) {
                    $tQuitCmd = [math]::Round($loopStart, 2)
                }
                if ($chunk -match "Engine Error:|Mem_Alloc:\s*out of memory|Sys_Error:|Host_Error:") {
                    $oomDetected = $true
                    Start-Sleep -Milliseconds 300
                    break
                }
            }

            $wsMB = 0.0; $peakWsMB = 0.0; $privMB = 0.0; $commitMB = 0.0; $peakCommitMB = 0.0; $pfs = [uint32]0
            $gotMem = $false
            try {
                $gotMem = [BqLowMemNative]::TryGetMemory($proc.Handle, [ref]$wsMB, [ref]$peakWsMB, [ref]$privMB, [ref]$commitMB, [ref]$peakCommitMB, [ref]$pfs)
            } catch {}

            $wins = [BqLowMemNative]::FindVisibleWindows($proc.Id)
            foreach ($w in $wins) {
                $t = [BqLowMemNative]::GetTitle($w)
                if ($t) { $modalTitles.Add($t) | Out-Null }
                if ($t -eq "Engine Error") { $oomDetected = $true }
            }
            if ($hwnd -eq [IntPtr]::Zero -or -not [BqLowMemNative]::IsWindowVisible($hwnd)) {
                if ($wins.Count -gt 0) { $hwnd = $wins[0] }
            }

            $resp = $null
            if ($hwnd -ne [IntPtr]::Zero) {
                $resp = [BqLowMemNative]::CheckResponsive($hwnd, 200)
            }

            $gpuDedMB = 0.0
            try { $gpuDedMB = $gpuSampler.SampleDedicatedMB() } catch {}

            $samples.Add([pscustomobject]@{
                t            = [math]::Round($loopStart, 3)
                ws_mb        = [math]::Round($wsMB, 1)
                priv_mb      = [math]::Round($privMB, 1)
                commit_mb    = [math]::Round($commitMB, 1)
                peak_com_mb  = [math]::Round($peakCommitMB, 1)
                gpu_ded_mb   = [math]::Round($gpuDedMB, 1)
                has_hwnd     = ($hwnd -ne [IntPtr]::Zero)
                resp         = $resp
            })

            if ($oomDetected) {
                Start-Sleep -Milliseconds 250
                break
            }

            $spentMs = ($sw.Elapsed.TotalSeconds - $loopStart) * 1000.0
            $remMs = [int]([math]::Max(0, $SampleMs - $spentMs))
            if ($remMs -gt 0) { Start-Sleep -Milliseconds $remMs }
        }
    } finally {
        if ($gpuSampler) { $gpuSampler.Dispose() }
        Stop-SpawnedProcessTree -Proc $proc
        if ($proc) { $proc.Dispose() }
        if ($jobHandle -ne [IntPtr]::Zero) { [BqLowMemNative]::CloseHandle($jobHandle) | Out-Null }
    }

    $wallSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
    $logText = Read-LogAll -Path $logPath

    # Compute continuous Not Responding streaks (load phase = strictly before tPostLoad / timerefresh)
    $loadEndCutoff = if ($null -ne $tPostLoad) { [math]::Max(0.0, $tPostLoad - 0.5) } elseif ($null -ne $tFirstFrame) { $tFirstFrame + 1.0 } else { $null }
    $longestHang = 0.0
    $loadLongestHang = 0.0
    $curStart = $null
    $prevT = $null
    foreach ($s in $samples) {
        if ($s.has_hwnd -and ($s.resp -eq $false)) {
            if ($null -eq $curStart) {
                if ($null -ne $prevT) { $curStart = $prevT } else { $curStart = $s.t }
            }
        } else {
            if ($null -ne $curStart) {
                $dur = [math]::Max(0.0, $s.t - $curStart)
                if ($dur -gt $longestHang) { $longestHang = $dur }
                if (($null -eq $loadEndCutoff -or $curStart -lt $loadEndCutoff) -and $dur -gt $loadLongestHang) {
                    $loadLongestHang = $dur
                }
                $curStart = $null
            }
        }
        $prevT = $s.t
    }
    if ($null -ne $curStart -and $samples.Count -gt 0) {
        $endT = $samples[$samples.Count - 1].t
        $dur = [math]::Max(0.0, $endT - $curStart)
        if ($dur -gt $longestHang) { $longestHang = $dur }
        if (($null -eq $loadEndCutoff -or $curStart -lt $loadEndCutoff) -and $dur -gt $loadLongestHang) {
            $loadLongestHang = $dur
        }
    }

    # Pre-quit / pre-timerefresh gameplay peaks (exclude synchronous timerefresh 128-frame GL burst & quit teardown spike)
    $cutoffT = $tPostLoad
    if ($null -eq $cutoffT) { $cutoffT = $tQuitCmd }
    $active = @($samples | Where-Object { $null -eq $cutoffT -or $_.t -lt $cutoffT })
    if ($active.Count -eq 0) { $active = @($samples) }

    $peakWs     = if ($active.Count -gt 0) { ($active | Measure-Object -Property ws_mb -Maximum).Maximum } else { 0.0 }
    $peakPriv   = if ($active.Count -gt 0) { ($active | Measure-Object -Property priv_mb -Maximum).Maximum } else { 0.0 }
    $peakCommit = if ($active.Count -gt 0) { ($active | Measure-Object -Property peak_com_mb -Maximum).Maximum } else { 0.0 }
    $rawPeakCom = if ($samples.Count -gt 0) { ($samples | Measure-Object -Property peak_com_mb -Maximum).Maximum } else { 0.0 }
    $peakGpu    = if ($active.Count -gt 0) { ($active | Measure-Object -Property gpu_ded_mb -Maximum).Maximum } else { 0.0 }

    $fps = $null
    if ($logText -match "([\d.]+)\s+seconds\s+\(([\d.]+)\s+fps\)") {
        $fps = [math]::Round([double]$Matches[2], 1)
    }

    $oomLines = @()
    foreach ($ln in ($logText -split "`r?`n")) {
        if ($ln -match "out of memory|Engine Error|Sys_Error|Host_Error") {
            $oomLines += $ln.Trim()
        }
    }

    $logExists = (Test-Path -LiteralPath $logPath) -and ((Get-Item -LiteralPath $logPath).Length -gt 0)

    # Evaluate pass/fail against budgets
    $reasons = New-Object System.Collections.Generic.List[string]
    if ($ExpectOOM) {
        $hasReadableOOM = ($oomLines.Count -gt 0) -and ($logText -match "out of memory|Engine Error")
        if (-not $logExists) { $reasons.Add("log_missing_or_empty") }
        if (-not $hasReadableOOM) { $reasons.Add("no_graceful_oom_message_in_log") }
        if ($timedOut) { $reasons.Add("silent_timeout_${RunTimeoutSec}s") }
        if ($logText.Contains("PROF_EVENT_UNEXPECTED_PASS")) { $reasons.Add("cap_not_enforced_loaded_under_${CapMB}MB") }
    } else {
        if ($timedOut) { $reasons.Add("timeout>${RunTimeoutSec}s") }
        if ($oomLines.Count -gt 0) { $reasons.Add("error_in_log") }
        if ($null -ne $exitCode -and $exitCode -ne 0) { $reasons.Add("exit_code_$exitCode") }
        if ($null -eq $exitCode -and -not $timedOut) { $reasons.Add("killed_on_error") }
        if ($SecondMap) {
            if ($null -eq $tPostLoad) { $reasons.Add("mapchange_did_not_finish") }
            if ($longestHang -gt $MaxNotRespondingSeconds) { $reasons.Add("hang_$([math]::Round($longestHang,2))s>${MaxNotRespondingSeconds}s") }
        } else {
            if ($null -eq $tFirstFrame) { $reasons.Add("never_reached_first_frame") }
            elseif ($tFirstFrame -gt $MaxLoadSeconds) { $reasons.Add("load_${tFirstFrame}s>${MaxLoadSeconds}s") }
            if ($loadLongestHang -gt $MaxNotRespondingSeconds) { $reasons.Add("hang_$([math]::Round($loadLongestHang,2))s>${MaxNotRespondingSeconds}s") }
            if ($MinFps -gt 0 -and ($null -eq $fps -or $fps -lt $MinFps)) { $reasons.Add("fps_${fps}<${MinFps}") }
        }
        if ($MaxPeakCommitMB -gt 0 -and $peakCommit -gt $MaxPeakCommitMB) {
            $reasons.Add("commit_$([math]::Round($peakCommit,0))MB>${MaxPeakCommitMB}MB")
        }
        if ($errorNote) { $reasons.Add($errorNote) }
    }

    $passed = ($reasons.Count -eq 0)

    if (-not $KeepLogs) {
        Remove-Item -LiteralPath $runDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    return [pscustomobject]@{
        run_id              = $RunId
        kind                = if ($ExpectOOM) { "oom_graceful" } elseif ($SecondMap) { "map_change" } else { "map_load" }
        map                 = if ($SecondMap) { "$MapName -> $SecondMap" } else { $MapName }
        tier                = $tierSetup.TierSource
        commit_cap_mb       = $CapMB
        pass                = $passed
        reasons             = ($reasons.ToArray() -join "; ")
        load_s              = $tFirstFrame
        wall_s              = $wallSec
        longest_hang_s      = [math]::Round($(if ($SecondMap) { $longestHang } else { $loadLongestHang }), 2)
        peak_ws_mb          = [math]::Round($peakWs, 1)
        peak_private_mb     = [math]::Round($peakPriv, 1)
        peak_commit_mb      = [math]::Round($peakCommit, 1)
        raw_peak_commit_mb  = [math]::Round($rawPeakCom, 1)
        peak_gpu_ded_mb     = [math]::Round($peakGpu, 1)
        timerefresh_fps     = $fps
        exit_code           = $exitCode
        timed_out           = $timedOut
        oom_lines           = $oomLines
        log_path            = if ($KeepLogs) { $logPath } else { "" }
    }
}

# --- Discover maps ---
$mapList = New-Object System.Collections.Generic.List[string]
if ($Maps -and $Maps.Count -gt 0) {
    foreach ($m in $Maps) {
        foreach ($part in ($m -split ",")) {
            $trimmed = $part.Trim() -replace "\.bsp$", ""
            if ($trimmed) { $mapList.Add($trimmed) }
        }
    }
} else {
    $mapsDir = Join-Path $GameDir "maps"
    if (-not (Test-Path -LiteralPath $mapsDir)) {
        throw "Maps folder not found: $mapsDir"
    }
    $discovered = @(Get-ChildItem -LiteralPath $mapsDir -Filter "*.bsp" -File | Select-Object -ExpandProperty BaseName | Sort-Object)
    # Put bakersfielddowntown and bakersfielddowntown_lite first
    foreach ($priority in @("bakersfielddowntown", "bakersfielddowntown_lite")) {
        if ($discovered -contains $priority) { $mapList.Add($priority) }
    }
    foreach ($d in $discovered) {
        if ($d -notin @("bakersfielddowntown", "bakersfielddowntown_lite")) {
            $mapList.Add($d)
        }
    }
}

if ($mapList.Count -eq 0 -and -not $TestMapChange -and -not $TestOOMGraceful) {
    throw "No maps found or specified."
}

$sessionStamp = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + $PID
$sessionTemp = if ($TempRoot) { Join-Path $TempRoot "bq_reg_$sessionStamp" } else { Join-Path $env:TEMP "bq_reg_$sessionStamp" }
New-Item -ItemType Directory -Path $sessionTemp -Force | Out-Null

Write-Host "=== BAKOQUAKE Low-Memory & Responsiveness Regression Suite ===" -ForegroundColor Cyan
Write-Host "Root       : $GameRoot"
Write-Host "Engine     : $Engine"
Write-Host "Tier       : $Tier  |  CommitCap: $(if ($CommitCapMB -gt 0) { "$CommitCapMB MB" } else { 'uncapped' })  |  Repeat: $Repeat"
Write-Host "Budgets    : Load <= ${MaxLoadSeconds}s, Hang <= ${MaxNotRespondingSeconds}s, PeakCommit <= ${MaxPeakCommitMB} MB$(if ($MinFps -gt 0) { ", FPS >= $MinFps" })"
Write-Host "Maps ($($mapList.Count)) : $($mapList -join ', ')"
Write-Host ""

$allResults = New-Object System.Collections.Generic.List[object]

try {
    foreach ($mapName in $mapList) {
        for ($iter = 1; $iter -le $Repeat; $iter++) {
            $runId = if ($Repeat -gt 1) { "${mapName}_r${iter}" } else { $mapName }
            Write-Host ("[{0}] Loading {1}..." -f $runId, $mapName) -NoNewline
            # Skip synchronous 128-frame timerefresh loop under strict Job Object commit caps unless -ForceTimeRefresh or -MinFps > 0:
            # CL_TimeRefresh_f queues 128 back-to-back GL frames inside one Host_Frame (+1 GB transient driver commit).
            $doTimeRefresh = ($CommitCapMB -eq 0) -or $ForceTimeRefresh.IsPresent -or ($MinFps -gt 0)
            $r = Invoke-SingleRun `
                -RunId $runId `
                -MapName $mapName `
                -TierName $Tier `
                -CapMB $CommitCapMB `
                -RunTimeoutSec $TimeoutSeconds `
                -RunTimeRefresh $doTimeRefresh `
                -SessionTempRoot $sessionTemp
            $allResults.Add($r)
            $tag = if ($r.pass) { "PASS" } else { "FAIL" }
            $color = if ($r.pass) { "Green" } else { "Red" }
            Write-Host (" {0} | load={1}s hang={2}s ws={3}MB priv={4}MB com={5}MB gpu={6}MB fps={7}{8}" -f `
                $tag, $r.load_s, $r.longest_hang_s, $r.peak_ws_mb, $r.peak_private_mb, $r.peak_commit_mb, $r.peak_gpu_ded_mb, $r.timerefresh_fps, `
                $(if ($r.reasons) { " [$($r.reasons)]" } else { "" })) -ForegroundColor $color
        }
    }

    if ($TestMapChange) {
        $runId = "mapchange_${MapChangeFrom}_to_${MapChangeTo}"
        Write-Host ("[{0}] Testing map change {1} -> {2}..." -f $runId, $MapChangeFrom, $MapChangeTo) -NoNewline
        $r = Invoke-SingleRun `
            -RunId $runId `
            -MapName $MapChangeFrom `
            -SecondMap $MapChangeTo `
            -TierName $Tier `
            -CapMB $CommitCapMB `
            -RunTimeoutSec ($TimeoutSeconds + 30) `
            -RunTimeRefresh $false `
            -SessionTempRoot $sessionTemp
        $allResults.Add($r)
        $tag = if ($r.pass) { "PASS" } else { "FAIL" }
        $color = if ($r.pass) { "Green" } else { "Red" }
        Write-Host (" {0} | wall={1}s hang={2}s priv={3}MB com={4}MB gpu={5}MB{6}" -f `
            $tag, $r.wall_s, $r.longest_hang_s, $r.peak_private_mb, $r.peak_commit_mb, $r.peak_gpu_ded_mb, `
            $(if ($r.reasons) { " [$($r.reasons)]" } else { "" })) -ForegroundColor $color
    }

    if ($TestOOMGraceful) {
        $oomMap = if ($mapList.Count -gt 0) { $mapList[0] } else { "bakersfielddowntown" }
        $runId = "oom_graceful_${oomMap}_${OOMCapMB}mb"
        Write-Host ("[{0}] Testing graceful OOM at {1} MB cap on {2}..." -f $runId, $OOMCapMB, $oomMap) -NoNewline
        $r = Invoke-SingleRun `
            -RunId $runId `
            -MapName $oomMap `
            -TierName $Tier `
            -CapMB $OOMCapMB `
            -RunTimeoutSec 30 `
            -ExpectOOM $true `
            -RunTimeRefresh $false `
            -SessionTempRoot $sessionTemp
        $allResults.Add($r)
        $tag = if ($r.pass) { "PASS" } else { "FAIL" }
        $color = if ($r.pass) { "Green" } else { "Red" }
        $oomSummary = if ($r.oom_lines.Count -gt 0) { $r.oom_lines[0] } else { "(none)" }
        Write-Host (" {0} | wall={1}s com={2}MB oom={3}{4}" -f `
            $tag, $r.wall_s, $r.peak_commit_mb, $oomSummary, `
            $(if ($r.reasons) { " [$($r.reasons)]" } else { "" })) -ForegroundColor $color
    }
} finally {
    if (-not $KeepLogs -and (Test-Path -LiteralPath $sessionTemp)) {
        Remove-Item -LiteralPath $sessionTemp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# --- Export JSON / Markdown ---
$passCount = @($allResults | Where-Object { $_.pass }).Count
$failCount = $allResults.Count - $passCount

$reportObj = [pscustomobject]@{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    engine        = $Engine
    tier          = $Tier
    commit_cap_mb = $CommitCapMB
    budgets       = [pscustomobject]@{
        max_load_s           = $MaxLoadSeconds
        max_peak_commit_mb   = $MaxPeakCommitMB
        max_not_responding_s = $MaxNotRespondingSeconds
        min_fps              = $MinFps
    }
    passed        = $passCount
    failed        = $failCount
    total         = $allResults.Count
    results       = $allResults.ToArray()
}

if ($OutJson) {
    Write-Utf8NoBom -Path $OutJson -Content ($reportObj | ConvertTo-Json -Depth 6)
    Write-Host "JSON report written: $OutJson"
}

if ($OutMarkdown) {
    $md = New-Object System.Collections.Generic.List[string]
    $md.Add("# BAKOQUAKE Low-Memory Regression Report")
    $md.Add("")
    $md.Add("- **Engine**: ``$Engine``")
    $md.Add("- **Tier**: ``$Tier`` | **Commit Cap**: ``$(if ($CommitCapMB -gt 0) { "$CommitCapMB MB" } else { 'uncapped' })`` | **Result**: **$passCount / $($allResults.Count) PASS**")
    $md.Add("- **Budgets**: Load <= ``${MaxLoadSeconds}s``, Hang <= ``${MaxNotRespondingSeconds}s``, Peak Commit <= ``${MaxPeakCommitMB} MB``")
    $md.Add("")
    $md.Add("| Run | Map | Status | Load (s) | Longest Hang (s) | Peak WS (MB) | Peak Priv (MB) | Peak Commit (MB) | Peak GPU (MB) | FPS | Notes |")
    $md.Add("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    foreach ($r in $allResults) {
        $st = if ($r.pass) { "PASS" } else { "**FAIL**" }
        $ld = if ($null -ne $r.load_s) { "$($r.load_s)" } else { "-" }
        $fp = if ($null -ne $r.timerefresh_fps) { "$($r.timerefresh_fps)" } else { "-" }
        $nt = if ($r.reasons) { $r.reasons } elseif ($r.oom_lines.Count -gt 0) { $r.oom_lines[0] } else { "" }
        $md.Add("| ``$($r.run_id)`` | $($r.map) | $st | $ld | $($r.longest_hang_s) | $($r.peak_ws_mb) | $($r.peak_private_mb) | $($r.peak_commit_mb) | $($r.peak_gpu_ded_mb) | $fp | $nt |")
    }
    Write-Utf8NoBom -Path $OutMarkdown -Content (($md.ToArray() -join "`n") + "`n")
    Write-Host "Markdown report written: $OutMarkdown"
}

Write-Host ""
$summaryColor = if ($failCount -eq 0) { "Green" } else { "Red" }
Write-Host ("=== SUMMARY: {0}/{1} PASSED ({2} FAILED) ===" -f $passCount, $allResults.Count, $failCount) -ForegroundColor $summaryColor

if ($failCount -gt 0) {
    exit 1
}
exit 0
