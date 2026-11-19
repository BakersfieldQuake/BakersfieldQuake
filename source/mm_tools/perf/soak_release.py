# Small-PC soak: the published release file set, started through the real Play.cmd, low-memory mode forced,
# engine memory capped with a Windows job object, a hosted game with 15 bots moved through the big maps.
# Needs the release's manifest-windows-x64.json in mf/b/ beside this script (gh release download <tag> -p
# manifest-windows-x64.json -D mf/b) and ZIPURL below set to the same release. ROOT is the scratch copy it builds.
# The test player is called AUTOTEST and the window is 1280x720: it is a clean new-player install with default keys.
# Environment: SOAK_MAPS=n (first n maps), SOAK_EXTRA="+cvar value ..." (extra engine arguments), SOAK_MEMLIST=1.
#   python -I soak.py build                       -> make the release copy (hard links for big files)
#   python -I soak.py run <tag> <capMB> [engine]  -> run; engine = path of an exe to put in the copy (default: release's)
import ctypes, ctypes.wintypes as wt, hashlib, io, json, os, re, shutil, subprocess, sys, time, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = r"G:\Quake\Combat"
ROOT = r"G:\Quake\_bq_fork_rel"
MANIFEST = os.path.join(HERE, "mf", "b", "manifest-windows-x64.json")
ZIPURL = "https://github.com/BakersfieldQuake/BakersfieldQuake/releases/download/build-20261118-0ebe292/BAKOQUAKE.zip"
SKIP = {"tools/bq-update.exe", "tools/install-shortcuts.ps1"}   # updater (would write through hard links), shortcuts (would repoint the owner's)
LOCK = r"G:\Quake\_bq_game.lock"
MAPS = ["bakersfielddowntown", "soi6", "spruce", "bklan6", "goldenwest", "terminal21", "soicowboy_bkk", "fox",
        "morrorock", "little_st_james", "bakersfielddowntown", "soi6", "spruce", "bklan6", "goldenwest", "terminal21"]
SLOT = 30
if os.environ.get("SOAK_MAPS"): MAPS = MAPS[:int(os.environ["SOAK_MAPS"])]
EXTRA = os.environ.get("SOAK_EXTRA", "")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()

class HttpFile(io.RawIOBase):
    def __init__(self, url):
        self.url, self.pos = url, 0
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"))
        self.size = int(r.headers["Content-Length"])
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos
    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        if n <= 0 or self.pos >= self.size: return b""
        end = min(self.size, self.pos + n) - 1
        r = urllib.request.urlopen(urllib.request.Request(self.url, headers={"Range": "bytes=%d-%d" % (self.pos, end)}))
        d = r.read(); self.pos += len(d); return d
    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)

def build():
    m = json.load(open(MANIFEST))
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)
    need = []
    for p, v in sorted(m["files"].items()):
        if p in SKIP: continue
        src = os.path.join(LOCAL, p.replace("/", os.sep)); dst = os.path.join(ROOT, p.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src) and os.path.getsize(src) == v["size"] and sha(src) == v["sha256"]:
            if v["size"] > (1 << 20) and not p.startswith("engine/"):
                os.link(src, dst)
            else:
                shutil.copyfile(src, dst)
        else:
            need.append(p)
    print("from this PC:", len(m["files"]) - len(SKIP) - len(need), "from the published zip:", len(need))
    zf = zipfile.ZipFile(io.BufferedReader(HttpFile(ZIPURL), 1 << 20))
    names = {n: n for n in zf.namelist()}
    for p in need:
        n = m.get("root", "") + p
        data = zf.read(names[n])
        dst = os.path.join(ROOT, p.replace("/", os.sep))
        with open(dst, "wb") as f: f.write(data)
    bad = 0
    for p, v in m["files"].items():
        if p in SKIP: continue
        if sha(os.path.join(ROOT, p.replace("/", os.sep))) != v["sha256"]:
            bad += 1; print("MISMATCH", p)
    for pak in ("pak0.pak", "pak1.pak"):
        os.link(os.path.join(LOCAL, "id1", pak), os.path.join(ROOT, "id1", pak))
    print("release copy at", ROOT, "files", len(m["files"]) - len(SKIP), "mismatches", bad, "(left out on purpose:", sorted(SKIP), ")")

u32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CreateJobObjectW.restype = wt.HANDLE
k32.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
k32.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
k32.GetCurrentProcess.restype = wt.HANDLE
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]

class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD)] + [(n, ctypes.c_size_t) for n in (
        "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
        "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]

class BASIC(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wt.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wt.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wt.DWORD), ("SchedulingClass", wt.DWORD)]
class IOC(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("a", "b", "c", "d", "e", "f")]
class EXT(ctypes.Structure):
    _fields_ = [("Basic", BASIC), ("Io", IOC), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

def commit_mb(h):
    c = PMC(); c.cb = ctypes.sizeof(PMC)
    return c.PrivateUsage / 1048576.0 if psapi.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb) else -1

def alive(h):
    code = wt.DWORD()
    k32.GetExitCodeProcess(h, ctypes.byref(code))
    return code.value == 259, code.value

def dialogs(pid):
    out = []
    PROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def text(h):
        b = ctypes.create_unicode_buffer(600); u32.GetWindowTextW(h, b, 600); return b.value
    def top(h, _):
        p = wt.DWORD(); u32.GetWindowThreadProcessId(h, ctypes.byref(p))
        cls = ctypes.create_unicode_buffer(64); u32.GetClassNameW(h, cls, 64)
        if p.value == pid and cls.value == "#32770" and u32.IsWindowVisible(h):
            parts = [text(h)]
            def child(c, __):
                t = text(c)
                if t: parts.append(t)
                return True
            u32.EnumChildWindows(h, PROC(child), 0)
            out.append(" | ".join(parts))
        return True
    u32.EnumWindows(PROC(top), 0)
    return out

def zircon_pids():
    ps = "Get-CimInstance Win32_Process -Filter \"name like 'zircon%'\" | ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout
    res = []
    for l in out.splitlines():
        if "\t" in l:
            a, b = l.split("\t", 1); res.append((int(a), b))
    return res

def run(tag, cap, engine=None):
    T0 = time.time()
    def log(*a): print("[%6.1f]" % (time.time() - T0), *a, flush=True)
    while True:
        while zircon_pids(): time.sleep(5)      # the owner's game or another test: wait without holding the lock
        try: os.mkdir(LOCK)
        except FileExistsError:
            if not zircon_pids() and time.time() - os.path.getmtime(LOCK) > 900: os.rmdir(LOCK)
            else: time.sleep(5)
            continue
        if not zircon_pids(): break
        os.rmdir(LOCK)
    h = None
    try:
        m = json.load(open(MANIFEST))
        gd = os.path.join(ROOT, "BakersfieldQuake")
        # a new player's state every run: the seed config from the zip, no logs
        with open(os.path.join(gd, "config.cfg"), "rb") as f: seed_ok = hashlib.sha256(f.read()).hexdigest() == m["files"]["BakersfieldQuake/config.cfg"]["sha256"]
        if not seed_ok:
            shutil.copyfile(os.path.join(HERE, "soak_seed_config.cfg"), os.path.join(gd, "config.cfg"))
        else:
            shutil.copyfile(os.path.join(gd, "config.cfg"), os.path.join(HERE, "soak_seed_config.cfg"))
        for n in ("bq_game.log", "bq_game_prev.log"):
            try: os.remove(os.path.join(gd, n))
            except OSError: pass
        exe = os.path.join(ROOT, "engine", "zircon_beta_gcc.exe")
        if engine:
            shutil.copyfile(engine, exe)
        elif sha(exe) != m["files"]["engine/zircon_beta_gcc.exe"]["sha256"]:
            shutil.copyfile(os.path.join(LOCAL, "engine", "zircon_beta_gcc.exe"), exe)
        log("engine sha256", sha(exe)[:16], "release's" if sha(exe) == m["files"]["engine/zircon_beta_gcc.exe"]["sha256"] else "NOT the release's")
        with open(os.path.join(gd, "zz_soak.cfg"), "w") as f:
            f.write("volume 0\nbgmvolume 0\n")
            for i, mp in enumerate(MAPS):
                f.write('defer %d "echo SOAK_MAP %d %s; disconnect; deathmatch 1; maxplayers 16; set bm_botfill 16; map %s"\n' % (8 + i * SLOT, i + 1, mp, mp))
            f.write('defer %d "echo SOAK_DONE; quit"\n' % (8 + len(MAPS) * SLOT))
        job = k32.CreateJobObjectW(None, None)
        info = EXT(); info.Basic.LimitFlags = 0x100; info.ProcessMemoryLimit = cap << 20
        ok = (not cap) or (k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)) and k32.AssignProcessToJobObject(job, k32.GetCurrentProcess()))
        log("memory cap %d MB per process:" % cap, "applied" if ok else "FAILED %d" % ctypes.get_last_error())
        env = dict(os.environ, USERNAME="AUTOTEST", BQ_LOWMEM="1", BQ_LOWGPU="0", BQ_NO_UPDATE="1", COMBAT_ARGS="-window -width 1280 -height 720 +log_file bq_game.log +exec zz_soak.cfg " + EXTRA)
        subprocess.run(["cmd", "/c", os.path.join(ROOT, "Play.cmd")], env=env, cwd=ROOT, timeout=120)
        pid = None
        for _ in range(20):
            mine = [p for p, c in zircon_pids() if "_bq_fork_rel" in c]
            if mine: pid = mine[0]; cmdline = [c for p, c in zircon_pids() if p == pid]; break
            time.sleep(1)
        if not pid: log("FAIL: Play.cmd started no engine"); return
        log("engine pid", pid); log("command line:", cmdline[0] if cmdline else "?")
        h = k32.OpenProcess(0x1F0FFF, False, pid)
        logp = os.path.join(gd, "bq_game.log")
        peak = {}; steady = {}; cur = "menu"; result = None; last = 0
        deadline = time.time() + 8 + len(MAPS) * SLOT + 90
        while time.time() < deadline:
            a, code = alive(h)
            try: txt = open(logp, "r", errors="replace").read()
            except OSError: txt = ""
            ms = re.findall(r"SOAK_MAP (\d+) (\S+)", txt)
            if ms: cur = "%02d %s" % (int(ms[-1][0]), ms[-1][1])
            if not a:
                result = "quit normally, exit code %d" % code if "SOAK_DONE" in txt else "PROCESS ENDED EARLY on %s, exit code %d" % (cur, code)
                break
            c = commit_mb(h)
            peak[cur] = max(peak.get(cur, 0), c)
            steady[cur] = c
            if time.time() - last > 4:
                last = time.time()
                d = dialogs(pid)
                if d:
                    result = "ERROR BOX on %s: %s" % (cur, d[0][:300]); break
            time.sleep(1)
        else:
            result = "TIMEOUT on %s" % cur
        log("RESULT", tag, "cap", cap, ":", result)
        a, _ = alive(h)
        if a:
            k32.TerminateProcess(h, 1); log("stopped pid", pid)
        time.sleep(1)
        try: txt = open(logp, "r", errors="replace").read()
        except OSError: txt = ""
        for k in sorted(peak): print("   %-26s peak while loading/playing %6.0f MB   at end of slot %6.0f MB" % (k, peak[k], steady.get(k, 0)))
        print("   entered the game: %d times, bots joined lines: %d" % (len(re.findall(r"entered the game", txt)), len(re.findall(r"\[BOT\]|bot .* joined|joined the game", txt, re.I))))
        bad = [l for l in txt.splitlines() if re.search(r"Engine Error|Host_Error|runaway|out of memory|SZ_GetSpace|QC crash|lowmem|low-memory", l, re.I)]
        seen = set()
        for l in bad:
            if l not in seen:
                seen.add(l); print("   log:", l[:220])
        shutil.copyfile(logp, os.path.join(HERE, "runs", "soak_%s.log" % tag)) if os.path.exists(logp) else None
    finally:
        try: os.rmdir(LOCK)
        except OSError: pass

if sys.argv[1] == "build":
    build()
else:
    os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
    run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else None)
