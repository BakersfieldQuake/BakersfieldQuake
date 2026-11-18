"""Time a listen-server ("host game") map load in Zircon and collect memory, texture and QC profile numbers.

    python -I loadtime.py <tag> <map> [--hold N] [--bots N] [--personal] [--quiet] [--exe <engine.exe>]
                          [--basedir <scratch copy> --same-userdir] [extra engine args...]

The engine runs with an isolated -userdir (%TEMP%/bq_perf/ud_<tag>, or $BQ_PERF_DIR) and port 26098, windowed 1280x720, so nothing is
written to the real config.cfg. By default an EMPTY personal.cfg / personal_post.cfg in that userdir shadows the
owner's private ones, so the run uses the settings a release player gets (--personal keeps the owner's files).
The map is started from a deferred cfg so the console log is already open and every line can be timestamped.
Writes <work dir>/runs/<tag>.timed.log (seconds since launch + console line) and prints a summary.

Anything put in <work dir>/ud_<tag>/BakersfieldQuake/ before the run (a zz_test.pk3, loose .skin files...) overrides
the real mod for that run only, which is how asset experiments are measured without touching the install.
Check that no other zircon_beta_gcc.exe is running first (CLAUDE.md), and never test on dm6.
"""
import ctypes
import ctypes.wintypes as wt
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.environ.get("BQ_PERF_DIR") or os.path.join(tempfile.gettempdir(), "bq_perf")
ENGINE_DIR = r"G:\Quake\Combat\engine"
EXE = os.path.join(ENGINE_DIR, "zircon_beta_gcc.exe")
argv = sys.argv[1:]
tag, mapname, rest = argv[0], argv[1], argv[2:]
hold, bots, personal, quiet, extra = 8, 0, False, False, []
basedir, same, memcap = r"G:\Quake\Combat", False, 0
i = 0
while i < len(rest):
    if rest[i] == "--hold":
        hold = int(rest[i + 1]); i += 2
    elif rest[i] == "--bots":
        bots = int(rest[i + 1]); i += 2
    elif rest[i] == "--personal":
        personal = True; i += 1
    elif rest[i] == "--basedir":    # another install tree (default G:\Quake\Combat)
        basedir = rest[i + 1]; i += 2
    elif rest[i] == "--same-userdir":  # -userdir = -basedir, as Play.cmd does. ONLY with a scratch --basedir:
        same = True; i += 1            # the engine saves config.cfg into it on quit
    elif rest[i] == "--memcap":     # MB of committed memory the engine may use (Windows job object): simulates a small PC
        memcap = int(rest[i + 1]); i += 2
    elif rest[i] == "--exe":        # another engine binary (still started from the engine folder, for its bin64 DLLs)
        EXE = rest[i + 1]; i += 2
    elif rest[i] == "--quiet":      # no developer_loading: real load time, but no per-model breakdown
        quiet = True; i += 1
    else:
        extra.append(rest[i]); i += 1
ud = os.path.join(HERE, "ud_" + tag)
if same:
    if os.path.normcase(os.path.abspath(basedir)) == os.path.normcase(r"G:\Quake\Combat"):
        sys.exit("--same-userdir needs a scratch --basedir: it would overwrite the real config.cfg")
    ud = basedir
gd = os.path.join(ud, "BakersfieldQuake")
os.makedirs(gd, exist_ok=True)
os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
logname = "zz_audit_%s.log" % tag


def put(name, text):
    with open(os.path.join(gd, name), "w", newline="\n") as f:
        f.write(text)


if not personal:
    put("personal.cfg", "// empty: audit run uses release-player settings\n")
    put("personal_post.cfg", "// empty: audit run uses release-player settings\n")
put("zz_audit_go.cfg", "echo BQ_GO\nmap %s\ndefer 3 \"exec zz_audit_end.cfg\"\n" % mapname)
put("zz_audit_end.cfg", "echo BQ_INGAME\ndefer %d \"exec zz_audit_end2.cfg\"\n" % hold)
put("zz_audit_end2.cfg", "echo BQ_STATS_BEGIN\necho BQ_PROFILE_SERVER\nprvm_profile server\necho BQ_PROFILE_CLIENT\n"
                         "prvm_profile client\necho BQ_MEM\nmemstats\nr_texturestats\necho BQ_STATS_END\nquit\n")
if os.path.exists(os.path.join(gd, logname)):
    os.remove(os.path.join(gd, logname))

args = [EXE, "-basedir", basedir, "-userdir", ud, "-port", "26098", "-window", "-width", "1280",
        "-height", "720", "-game", "quake15", "-game", "BakersfieldQuake", "-condebug", "+log_file", logname,
        "+developer_loading", "0" if quiet else "1"] + extra + ["+deathmatch", "1", "+maxplayers", str(max(4, bots + 1))]
if bots:
    args += ["+set", "bm_botfill", str(bots + 1)]
args += ["+defer", "2", "exec zz_audit_go.cfg"]


class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


psapi = ctypes.WinDLL("psapi")
psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]


def mem(handle):
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    if psapi.GetProcessMemoryInfo(int(handle), ctypes.byref(c), c.cb):
        return c.WorkingSetSize, c.PeakWorkingSetSize, c.PagefileUsage, c.PeakPagefileUsage
    return None


class IOC(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("r", "w", "o", "rb", "wb", "ob")]


class BASIC(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wt.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wt.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wt.DWORD), ("SchedulingClass", wt.DWORD)]


class EXT(ctypes.Structure):
    _fields_ = [("Basic", BASIC), ("IoInfo", IOC), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


def dialog_text(pid_):
    """text of any message box the process is showing (an engine error dialog blocks until someone clicks)"""
    u32 = ctypes.WinDLL("user32")
    found = []
    PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def child(h, _):
        b = ctypes.create_unicode_buffer(1024)
        u32.GetWindowTextW(h, b, 1024)
        if b.value.strip():
            found.append(b.value.strip())
        return True

    def top(h, _):
        p = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(p))
        c = ctypes.create_unicode_buffer(64)
        u32.GetClassNameW(h, c, 64)
        if p.value == pid_ and c.value == "#32770":
            b = ctypes.create_unicode_buffer(256)
            u32.GetWindowTextW(h, b, 256)
            found.append("[dialog] " + b.value)
            u32.EnumChildWindows(h, PROC(child), 0)
        return True
    u32.EnumWindows(PROC(top), 0)
    return " | ".join(found)


t0 = time.perf_counter()
proc = subprocess.Popen(args, cwd=ENGINE_DIR)
if memcap:
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.restype = wt.HANDLE
    k32.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
    k32.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
    job = k32.CreateJobObjectW(None, None)
    info = EXT()
    info.Basic.LimitFlags = 0x100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY
    info.ProcessMemoryLimit = memcap << 20
    okj = k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)) and         k32.AssignProcessToJobObject(job, int(proc._handle))
    print("memory cap %d MB commit: %s" % (memcap, "applied" if okj else "FAILED to apply (error %d)" % ctypes.get_last_error()))
out = open(os.path.join(HERE, "runs", tag + ".timed.log"), "w", encoding="utf-8", errors="replace")
logpath = os.path.join(gd, logname)
pos, buf, marks, peak, killed = 0, b"", {}, (0, 0, 0, 0), False
KEYS = ("BQ_GO", "Log started", "BQ_INGAME", "BQ_STATS_BEGIN", "BQ_STATS_END", "Server spawned", "SpawnServer",
        "entered the game", "Host_Error")
deadline = t0 + (150 if memcap else 420) + hold
dialog = ""
host_error = ""
next_dialog = 5.0
while True:
    now = time.perf_counter() - t0
    m = mem(proc._handle) if proc.poll() is None else None
    if m:
        peak = tuple(max(a, b) for a, b in zip(peak, m))
    if os.path.exists(logpath):
        with open(logpath, "rb") as f:
            f.seek(pos)
            chunk = f.read()
            pos += len(chunk)
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            s = line.decode("latin-1").rstrip("\r")
            out.write("%8.2f %s\n" % (now, s))
            for key in KEYS:
                if key in s and key not in marks:
                    marks[key] = now
                    if key == "Host_Error":
                        host_error = s.strip()[:200]
    if proc.poll() is not None:
        break
    if "Host_Error" in marks and now > marks["Host_Error"] + 2:     # the game dropped to the console: no point waiting
        print("HOST ERROR after %.1f s: %s" % (marks["Host_Error"], host_error))
        proc.kill()
        killed = True
        break
    if memcap and now > next_dialog:
        next_dialog = now + 2.0
        dialog = dialog_text(proc.pid)
        if dialog:
            print("ENGINE ERROR DIALOG after %.1f s: %s" % (now, dialog[:600]))
            proc.kill()
            killed = True
            break
    if time.perf_counter() > deadline:
        proc.kill()
        killed = True
        break
    time.sleep(0.02)
out.close()

text = open(os.path.join(HERE, "runs", tag + ".timed.log"), encoding="utf-8").read()
tex_kb = 0
rt_kb = 0
for mm in re.finditer(r"^\s*[\d.]+ \[\s*(\d+)\]\s+\d+\s+\S+\s+loaded\s+(?:mip\s+)?(?:alpha\s+)?(\S.*)$", text, re.M):
    if mm.group(2).startswith("rendertarget"):
        rt_kb += int(mm.group(1))
    else:
        tex_kb += int(mm.group(1))
pools = re.search(r"memory pools, totalling [\d,]+ bytes \(([\d.]+)MB\)", text)


def calls(section, fn):
    sec = text.split(section, 1)[-1]
    mm = re.search(r"^\s*[\d.]+\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+[\d.]+%\s+" + re.escape(fn) + r"\s*$", sec, re.M)
    return int(mm.group(1)) if mm else None


span = (marks.get("BQ_STATS_BEGIN", 0) - marks.get("Server spawned", 0)) or 1
sv_frames = calls("BQ_PROFILE_SERVER", "StartFrame")
cl_frames = calls("BQ_PROFILE_CLIENT", "CSQC_UpdateView")
errs = len(re.findall(r"Host_Error|runaway loop|SZ_GetSpace|no free edicts|PRVM_.*error|VM_.*error", text))
print("tag %s map %s extra %s bots %d hold %d personal %s" % (tag, mapname, extra, bots, hold, personal))
print("exit code", proc.returncode, "KILLED (timeout)" if killed else "")
if quiet and "BQ_GO" in marks and "entered the game" in marks:
    print("LOAD (quiet): in game %.1f s after the map command" % (marks["entered the game"] - marks["BQ_GO"]))
if "SpawnServer" in marks and "entered the game" in marks:
    print("LOAD: server spawn %.1f s, in game after %.1f s (engine start to map command: %.1f s)" % (
        marks.get("Server spawned", 0) - marks["SpawnServer"], marks["entered the game"] - marks["SpawnServer"],
        marks["SpawnServer"]))
print("MEMORY: peak working set %d MB, peak commit %d MB, engine pools %s MB, textures %d MB (+%d MB render targets)" % (
    peak[1] >> 20, peak[3] >> 20, pools.group(1) if pools else "?", tex_kb >> 10, rt_kb >> 10))
print("COUNTS: models %d, images %d, sounds %d" % (text.count("loading model "), text.count("loaded image "),
                                                   text.count("loading sound ")))
print("FRAMES over %.1f s in game: server %s (%.0f/s), client %s (%.0f fps)" % (
    span, sv_frames, (sv_frames or 0) / span, cl_frames, (cl_frames or 0) / span))
print("error lines:", errs)
