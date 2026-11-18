"""Poor man's sampling profiler for the engine's main thread (no symbols needed for module-level answers).
    python -I sampler.py <pid> <seconds> [interval_ms]
Start a load with loadtime.py in the background, wait until the map command has run (about 3.5 s), then point this at the
zircon_beta_gcc.exe pid for the length of the load. On 2026-11-18 it showed 45% of a soi6 load in GetFileAttributesW
(loose-file probes) with a separate -userdir, 20% with -userdir = -basedir. See docs/audit-2026-11-18-performance.md.
Every few ms: suspend the main thread, read RIP and the top of its stack, resume. Reports where RIP was by module,
and for samples outside the exe, the first return address inside the exe (who called into the driver / OS / zlib)."""
import bisect
import collections
import ctypes
import ctypes.wintypes as wt
import re
import struct
import sys
import time

pid, secs = int(sys.argv[1]), float(sys.argv[2])
interval = (float(sys.argv[3]) if len(sys.argv) > 3 else 4) / 1000.0
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ThreadID", wt.DWORD), ("th32OwnerProcessID", wt.DWORD),
                ("tpBasePri", wt.LONG), ("tpDeltaPri", wt.LONG), ("dwFlags", wt.DWORD)]


class MODULEINFO(ctypes.Structure):
    _fields_ = [("lpBaseOfDll", ctypes.c_void_p), ("SizeOfImage", wt.DWORD), ("EntryPoint", ctypes.c_void_p)]


k32.OpenProcess.restype = wt.HANDLE
k32.OpenThread.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.GetThreadTimes.argtypes = [wt.HANDLE] + [ctypes.POINTER(wt.FILETIME)] * 4
psapi.EnumProcessModules.argtypes = [wt.HANDLE, ctypes.POINTER(wt.HMODULE), wt.DWORD, ctypes.POINTER(wt.DWORD)]
psapi.GetModuleInformation.argtypes = [wt.HANDLE, wt.HMODULE, ctypes.POINTER(MODULEINFO), wt.DWORD]
psapi.GetModuleFileNameExW.argtypes = [wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]

hp = k32.OpenProcess(0x0410, False, pid)  # QUERY_INFORMATION | VM_READ
if not hp:
    sys.exit("cannot open process")


def modules():
    arr = (wt.HMODULE * 1024)()
    need = wt.DWORD()
    psapi.EnumProcessModules(hp, arr, ctypes.sizeof(arr), ctypes.byref(need))
    out = []
    for i in range(need.value // ctypes.sizeof(wt.HMODULE)):
        mi = MODULEINFO()
        psapi.GetModuleInformation(hp, arr[i], ctypes.byref(mi), ctypes.sizeof(mi))
        name = ctypes.create_unicode_buffer(520)
        psapi.GetModuleFileNameExW(hp, arr[i], name, 520)
        out.append((mi.lpBaseOfDll or 0, mi.SizeOfImage, name.value.rsplit("\\", 1)[-1].lower(), name.value))
    return sorted(out)


# main thread = the oldest thread of the process
snap = k32.CreateToolhelp32Snapshot(0x4, 0)
te = THREADENTRY32()
te.dwSize = ctypes.sizeof(te)
tids = []
ok = k32.Thread32First(snap, ctypes.byref(te))
while ok:
    if te.th32OwnerProcessID == pid:
        tids.append(te.th32ThreadID)
    ok = k32.Thread32Next(snap, ctypes.byref(te))
best = None
for tid in tids:
    h = k32.OpenThread(0x0040 | 0x0002 | 0x0008, False, tid)  # QUERY_INFORMATION | SUSPEND_RESUME | GET_CONTEXT
    if not h:
        continue
    c, e, kt, ut = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    k32.GetThreadTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut))
    created = (c.dwHighDateTime << 32) | c.dwLowDateTime
    if best is None or created < best[0]:
        best = (created, tid, h)
ht = best[2]
ctx = ctypes.create_string_buffer(1232 + 16)
base = ctypes.addressof(ctx)
off = (16 - base % 16) % 16
CONTEXT_FULL = 0x100000 | 0x1 | 0x2
stackbuf = ctypes.create_string_buffer(4096)
got = ctypes.c_size_t()
samples = []
t_end = time.perf_counter() + secs
while time.perf_counter() < t_end:
    t = time.perf_counter()
    if k32.SuspendThread(ht) == 0xFFFFFFFF:
        break
    struct.pack_into("<I", ctx, off + 0x30, CONTEXT_FULL)
    if k32.GetThreadContext(ht, base + off):
        rip = struct.unpack_from("<Q", ctx, off + 0xF8)[0]
        rsp = struct.unpack_from("<Q", ctx, off + 0x98)[0]
        k32.ReadProcessMemory(hp, rsp, stackbuf, 4096, ctypes.byref(got))
        samples.append((rip, stackbuf.raw[:got.value]))
    k32.ResumeThread(ht)
    time.sleep(max(0.0, interval - (time.perf_counter() - t)))

mods = modules()
bases = [m[0] for m in mods]


def modof(a):
    i = bisect.bisect_right(bases, a) - 1
    if i >= 0 and a < mods[i][0] + mods[i][1]:
        return mods[i]
    return None


exe = next(m for m in mods if m[2].endswith(".exe"))
data = open(exe[3], "rb").read()
pe = struct.unpack_from("<I", data, 0x3c)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
optsz = struct.unpack_from("<H", data, pe + 20)[0]
secs_ = [struct.unpack_from("<8sIIII", data, pe + 24 + optsz + 40 * i) for i in range(nsec)]


def foff(rva):
    for n, vs, va, rs, rp in secs_:
        if va <= rva < va + max(vs, rs):
            return rp + (rva - va) if rva - va < rs else None


def cstr(rva):
    o = foff(rva)
    if o is None:
        return None
    e = data.find(b"\0", o)
    s = data[o:e]
    return s.decode("latin-1") if 3 < len(s) < 90 and all(32 <= c < 127 for c in s) else None


def hint(rva):
    """strings referenced by rip-relative lea within ~700 bytes of this code address"""
    o = foff(rva)
    if o is None:
        return ""
    blk = data[max(0, o - 500): o + 300]
    start = rva - (o - max(0, o - 500))
    out = []
    for m in re.finditer(rb"[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", blk):
        p = m.start()
        if p + 7 > len(blk):
            break
        rel = struct.unpack_from("<i", blk, p + 3)[0]
        s = cstr(start + p + 7 + rel)
        if s and s not in out:
            out.append(s)
    return " | ".join(out[:5])


def exports(path):
    """name table of a system DLL: sorted (rva, name)"""
    try:
        d = open(path, "rb").read()
    except OSError:
        return []
    pe_ = struct.unpack_from("<I", d, 0x3c)[0]
    ns = struct.unpack_from("<H", d, pe_ + 6)[0]
    osz = struct.unpack_from("<H", d, pe_ + 20)[0]
    sc = [struct.unpack_from("<8sIIII", d, pe_ + 24 + osz + 40 * i) for i in range(ns)]

    def fo(rva):
        for n_, vs, va, rs, rp in sc:
            if va <= rva < va + max(vs, rs):
                return rp + rva - va
        return None
    exp_rva = struct.unpack_from("<I", d, pe_ + 24 + 112)[0]
    eo = fo(exp_rva)
    if eo is None:
        return []
    nfun, nnames, afun, anames, aords = struct.unpack_from("<IIIII", d, eo + 20)
    out = []
    for i in range(nnames):
        nrva = struct.unpack_from("<I", d, fo(anames) + 4 * i)[0]
        o = struct.unpack_from("<H", d, fo(aords) + 2 * i)[0]
        frva = struct.unpack_from("<I", d, fo(afun) + 4 * o)[0]
        no = fo(nrva)
        out.append((frva, d[no:d.index(bytes(1), no)].decode("latin-1")))
    return sorted(out)


exp_cache = {}


def sysname(a):
    m = modof(a)
    if not m:
        return "(unknown)"
    if m[2] not in exp_cache:
        exp_cache[m[2]] = exports(m[3])
    ex = exp_cache[m[2]]
    i = bisect.bisect_right([e[0] for e in ex], a - m[0]) - 1
    return "%s!%s" % (m[2], ex[i][1] if i >= 0 else "?")


TEXT_END = next(va + max(vs, rs) for n_, vs, va, rs, rp in secs_ if n_.startswith(b".text"))
bymod = collections.Counter()
exefn = collections.Counter()
sysfn = collections.Counter()
chains = collections.Counter()
outer = collections.Counter()
for rip, st in samples:
    m = modof(rip)
    name = m[2] if m else "(unknown/jit)"
    bymod[name] += 1
    if m and m[0] == exe[0]:
        exefn[(rip - exe[0]) & ~0x1FF] += 1
        continue
    sysfn[sysname(rip)] += 1
    # stack: system frames (named) then the first two exe .text return addresses
    sysframes, exeframes = [], []
    for o in range(0, len(st) - 7, 8):
        v = struct.unpack_from("<Q", st, o)[0]
        mm = modof(v)
        if not mm:
            continue
        if mm[0] == exe[0]:
            if 0x1000 <= v - exe[0] < TEXT_END:
                exeframes.append((v - exe[0]) & ~0xFF)
                if len(exeframes) == 2:
                    break
        elif not exeframes and len(sysframes) < 3:
            nm = sysname(v)
            if nm not in sysframes:
                sysframes.append(nm)
    outer[" <- ".join(sysframes[-2:]) or sysname(rip)] += 1
    if exeframes:
        chains[(name, tuple(exeframes))] += 1
n = len(samples)
print("samples: %d over %.1f s (main thread)" % (n, secs))
print("== where the main thread was, by module")
for k, v in bymod.most_common(10):
    print("  %5.1f%%  %s" % (100.0 * v / n, k))
print("== system functions at the sample point")
for k, v in sysfn.most_common(14):
    print("  %5.1f%%  %s" % (100.0 * v / n, k))
print("== outermost system calls seen on the stack below the exe")
for k, v in outer.most_common(14):
    print("  %5.1f%%  %s" % (100.0 * v / n, k))
print("== hottest code regions inside the exe (512-byte buckets), with nearby strings")
for k, v in exefn.most_common(10):
    print("  %5.1f%%  exe+0x%x  %s" % (100.0 * v / n, k, hint(k + 0x100)[:140]))
print("== samples outside the exe: nearest exe callers (.text only)")
for (name, fr), v in chains.most_common(14):
    print("  %5.1f%%  %-12s <- %s" % (100.0 * v / n, name, "  <-  ".join("exe+0x%x [%s]" % (f, hint(f + 0x80)[:70]) for f in fr)))
