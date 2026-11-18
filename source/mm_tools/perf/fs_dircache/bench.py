"""Old vs new engine on soi6: timed runs (loadtime.py --quiet) interleaved, then one sampled run per config.
    python -I bench.py <outdir> [rounds]
Waits before each launch until no zircon* process is running (another session's test or the owner's game)."""
import ctypes
import ctypes.wintypes as wt
import json
import os
import re
import statistics
import subprocess
import sys
import time

PERF = r"G:\Quake\Combat\BakersfieldQuake\source\mm_tools\perf"
RUN = r"G:\Quake\zircon-fscache\run"
PKG = r"G:\Quake\zircon-fscache\pkg"
MAP = "soi6"
out, rounds = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3
os.makedirs(out, exist_ok=True)

EXES = {"shipped": "zircon_beta_shipped.exe", "base": "zircon_beta_base.exe", "fscache": "zircon_beta_fscache.exe",
        "final": "zircon_beta_final.exe"}
CONFIGS = []
for layout in ("sep", "same"):
    for eng, extra in (("shipped", []), ("base", []), ("fscache", []), ("fscache0", ["+set", "fs_dircache", "0"]),
                       ("final", []), ("final0", ["+set", "fs_dircache", "0"])):
        exe = EXES[eng[:-1] if eng.endswith("0") else eng]
        args = ["--exe", os.path.join(RUN, exe)] + (["--basedir", PKG, "--same-userdir"] if layout == "same" else []) + extra
        CONFIGS.append(("%s_%s" % (layout, eng), exe, args))


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", wt.LONG), ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


k32 = ctypes.WinDLL("kernel32")
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE


def procs():
    snap = k32.CreateToolhelp32Snapshot(2, 0)
    e = PE32()
    e.dwSize = ctypes.sizeof(e)
    res = []
    ok = k32.Process32FirstW(snap, ctypes.byref(e))
    while ok:
        res.append((e.th32ProcessID, e.szExeFile.lower()))
        ok = k32.Process32NextW(snap, ctypes.byref(e))
    k32.CloseHandle(snap)
    return res


BUSY = r"C:\Users\qxdc\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_e5def20f-17f0-45bd-9a05-6cb1db38ebd2\gunframes-engine-busy.txt"


def wait_free():
    t = time.time()
    while os.path.exists(BUSY) or any(n.startswith("zircon") for _, n in procs()):
        if time.time() - t > 3600:
            sys.exit("another zircon has been running for 30 min; giving up")
        time.sleep(5)


def run(tag, exe, args, sample_secs=0):
    wait_free()
    timed = os.path.join(os.environ.get("BQ_PERF_DIR") or os.path.join(os.environ["TEMP"], "bq_perf"), "runs", tag + ".timed.log")
    if os.path.exists(timed):
        os.remove(timed)
    p = subprocess.Popen([sys.executable, "-I", os.path.join(PERF, "loadtime.py"), tag, MAP, "--quiet", "--hold", "6" if sample_secs else "1"] + args,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    samp = None
    if sample_secs:
        pid = None
        while p.poll() is None and pid is None:
            pid = next((i for i, n in procs() if n == exe.lower()), None)
            time.sleep(0.05)
        while p.poll() is None:  # start sampling at the map command
            if os.path.exists(timed) and "BQ_GO" in open(timed, encoding="utf-8", errors="replace").read():
                break
            time.sleep(0.02)
        samp = subprocess.run([sys.executable, "-I", os.path.join(PERF, "sampler.py"), str(pid), "%.1f" % sample_secs, "3"],
                              capture_output=True, text=True)
        samp = samp.stdout + samp.stderr
    so = p.communicate()[0]
    m = re.search(r"LOAD \(quiet\): in game ([\d.]+) s", so)
    return (float(m.group(1)) if m else None), so, samp


if len(sys.argv) > 3:
    CONFIGS = [c for c in CONFIGS if c[0] in sys.argv[3].split(",")]
results = {c[0]: [] for c in CONFIGS}
# warm-up: fills the disk cache and lets each user folder write its first config.cfg
for tag, exe, args in CONFIGS:
    t, so, _ = run(tag, exe, args)
    print("warmup", tag, t, flush=True)
for r in range(rounds):
    for tag, exe, args in CONFIGS:
        t, so, _ = run(tag, exe, args)
        results[tag].append(t)
        open(os.path.join(out, "%s_r%d.txt" % (tag, r)), "w").write(so)
        print("round", r, tag, t, flush=True)
summary = {}
for tag, exe, args in CONFIGS:
    vals = [v for v in results[tag] if v is not None]
    med = statistics.median(vals) if vals else None
    summary[tag] = {"runs": results[tag], "median": med}
    t, so, samp = run(tag, exe, args, sample_secs=med or 10)
    open(os.path.join(out, "%s_sampled.txt" % tag), "w").write("load during sampling: %s\n\n%s\n\n%s" % (t, so, samp))
    m = re.search(r"^\s*([\d.]+)%\s+kernelbase\.dll!GetFileAttributesW", samp or "", re.M)
    summary[tag]["sampled_load"] = t
    summary[tag]["getfileattributesw_pct"] = float(m.group(1)) if m else None
    print("sampled", tag, t, summary[tag]["getfileattributesw_pct"], flush=True)
json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)
for k, v in summary.items():
    print("%-16s median %-6s runs %-28s GetFileAttributesW %s%%" % (k, v["median"], v["runs"], v["getfileattributesw_pct"]))
