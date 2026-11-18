"""Regression run for the fs_dircache engine change. One engine, fresh user folder, basedir = scratch package.
    python -I regress.py <exe> <outdir>
Launch 1: new player, then in one session:
  T1 console: a cached miss on zzfc/, saveconfig zzfc/probe.cfg, exec it in the same frame
  T2 QC: CSQC_Shutdown writes data/config_menu.cfg (fopen), the next CSQC_Init reads it (nospinup 17 restored)
  T3 demo: record demos/zzreg after a cached miss on demos/, stop and playdemo 3 s later
  T4 screenshot x3 (each must get its own file)
  T5 curl --pak from a local HTTP server into dlcache/, then map fctest from that pack
  T6 a folder created outside the engine: hidden for < 5 s (cache), visible after the 5 s expiry
Launch 2: config.cfg written by launch 1 is read back (name fcregtest)."""
import http.server
import os
import re
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import zipfile

exe, out = os.path.abspath(sys.argv[1]), sys.argv[2]
PKG = r"G:\Quake\zircon-fscache\pkg"
HTTP_PORT = 26099
os.makedirs(out, exist_ok=True)
ud = os.path.join(out, "ud")
if os.path.exists(ud):
    shutil.rmtree(ud)
gd = os.path.join(ud, "BakersfieldQuake")
os.makedirs(gd)

# download pack served over HTTP
www = os.path.join(out, "www")
os.makedirs(www, exist_ok=True)
with zipfile.ZipFile(os.path.join(www, "fcreg_dl.pk3"), "w") as z:
    for name, data in (("fctest_marker.cfg", b"echo FCTEST_PACK_OK\n"),
                       ("maps/fctest.bsp", open(os.path.join(PKG, "BakersfieldQuake", "maps", "aerowalk.bsp"), "rb").read())):
        zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        z.writestr(zi, data, zipfile.ZIP_STORED)


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=www, **k)

    def log_message(self, *a):
        pass


srv = socketserver.TCPServer(("127.0.0.1", HTTP_PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()

CFG = {
    "zz_reg1.cfg": 'echo REG1\nname fcregtest\nmap start\ndefer 8 "exec zz_reg2.cfg"\n',
    # probes use "which" (FS_FindFile); "exec" checks with FS_Search, a directory listing that bypasses the cache
    "zz_reg2.cfg": 'echo REG2_T1\nwhich zzfc/probe.cfg\nsaveconfig zzfc/probe.cfg\nwhich zzfc/probe.cfg\nexec zzfc/probe.cfg\n'
                   'echo REG2_T2\nnospinup 17\nexec data/config_menu.cfg\ndisconnect\nexec data/config_menu.cfg\n'
                   'nospinup 3\nmap start\ndefer 8 "exec zz_reg3.cfg"\n',
    "zz_reg3.cfg": 'echo REG3_T2_RESULT\nnospinup\necho REG3_T3\ndisconnect\nwhich demos/zzreg.dem\nrecord demos/zzreg\n'
                   'which demos/zzreg.dem\necho REG3_T3_MAP\nmap start\ndefer 9 "exec zz_reg4.cfg"\n',
    "zz_reg4.cfg": 'echo REG4\nstop\nplaydemo demos/zzreg\ndefer 4 "exec zz_reg5.cfg"\n',
    "zz_reg5.cfg": 'echo REG5_T4\nscreenshot\ndefer 0.5 "screenshot"\ndefer 1 "screenshot"\n'
                   'defer 2 "exec zz_reg5b.cfg"\n',
    "zz_reg5b.cfg": 'echo REG5_T5\ndisconnect\ncurl --pak http://127.0.0.1:%d/fcreg_dl.pk3\n'
                    'defer 4 "exec zz_reg6.cfg"\n' % HTTP_PORT,
    "zz_reg6.cfg": 'echo REG6\nwhich fctest_marker.cfg\nexec fctest_marker.cfg\nmap fctest\ndefer 8 "exec zz_reg7.cfg"\n',
    "zz_reg7.cfg": 'echo REG7_T6\nwhich zzext/probe.cfg\nfs_dircache_list\necho REG_EXT_CREATE\ndefer 2 "exec zz_reg8.cfg"\n',
    "zz_reg8.cfg": 'echo REG8_T6_2S\nwhich zzext/probe.cfg\ndefer 5 "exec zz_reg9.cfg"\n',
    "zz_reg9.cfg": 'echo REG9_T6_7S\nwhich zzext/probe.cfg\nexec zzext/probe.cfg\necho REG_END\nquit\n',
    "zz_regb.cfg": 'echo REGB\nname\necho REGB_END\nquit\n',
}
for k, v in CFG.items():
    open(os.path.join(gd, k), "w", newline="\n").write(v)


BUSY = r"C:\Users\qxdc\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_e5def20f-17f0-45bd-9a05-6cb1db38ebd2\gunframes-engine-busy.txt"


def engine_free():
    """no zircon*.exe running and no other session's busy marker"""
    if os.path.exists(BUSY):
        return False
    r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout.lower()
    return '"zircon' not in r


def launch(cfg, log, watch_ext=False):
    t = time.time()
    while not engine_free():
        if time.time() - t > 3600:
            sys.exit("engine busy for an hour; giving up")
        time.sleep(5)
    args = [exe, "-basedir", PKG, "-userdir", ud, "-port", "26098", "-window", "-width", "1280", "-height", "720",
            "-game", "quake15", "-game", "BakersfieldQuake", "-condebug", "+log_file", log,
            "+deathmatch", "1", "+maxplayers", "4", "+defer", "2", "exec " + cfg]
    p = subprocess.Popen(args, cwd=os.path.dirname(exe))
    lp = os.path.join(gd, log)
    created = False
    t0 = time.time()
    while p.poll() is None:
        if time.time() - t0 > 180:
            p.kill()
            print("KILLED after 180 s")
            break
        if watch_ext and not created and os.path.exists(lp) and "REG_EXT_CREATE" in open(lp, errors="replace").read():
            os.makedirs(os.path.join(gd, "zzext"), exist_ok=True)
            open(os.path.join(gd, "zzext", "probe.cfg"), "w").write("echo ZZEXT_OK\n")
            created = time.time()
        time.sleep(0.05)
    return open(lp, errors="replace").read()


log1 = launch("zz_reg1.cfg", "zz_reg1.log", watch_ext=True)
log2 = launch("zz_regb.cfg", "zz_reg2.log")
srv.shutdown()


def between(text, a, b):
    i = text.find(a)
    j = text.find(b, i + 1) if i >= 0 else -1
    return text[i:j] if i >= 0 and j >= 0 else ""


res = []
t1 = between(log1, "REG2_T1", "REG2_T2")
res.append(("T1 miss, write, found in the same frame (zzfc/)", t1.count("zzfc/probe.cfg isn't anywhere") == 1
            and "zzfc/probe.cfg is file" in t1 and "execing zzfc/probe.cfg" in t1))
t2a = between(log1, "REG2_T2", "REG3_T2_RESULT")
t2 = between(log1, "REG3_T2_RESULT", "REG3_T3")
res.append(("T2 QC fopen write at shutdown, console read same frame", "execing data/config_menu.cfg" in t2a))
res.append(("T2 QC fopen read on next CSQC_Init (nospinup 17)", bool(re.search(r'nospinup"? is "17"', t2))))
t3w = between(log1, "REG3_T3", "REG3_T3_MAP")
res.append(("T3 demo: miss, record, found in the same frame (demos/)", "demos/zzreg.dem isn't anywhere" in t3w
            and "demos/zzreg.dem is file" in t3w))
t3 = between(log1, "REG4", "REG5_T4")
res.append(("T3 demo record + playdemo", "couldn't open" not in t3 and bool(re.search(r"(?i)playing demo", t3))))
shots = os.listdir(os.path.join(gd, "screenshots")) if os.path.isdir(os.path.join(gd, "screenshots")) else []
res.append(("T4 three screenshots, three files (%d)" % len(shots), len(shots) == 3))
t5 = between(log1, "REG6", "REG7_T6")
dl = os.path.exists(os.path.join(gd, "dlcache", "fcreg_dl.pk3"))
res.append(("T5 curl --pak into dlcache, pack used (marker + map fctest)",
            dl and "FCTEST_PACK_OK" in t5 and "fcreg_dl.pk3" in t5 and "fctest" in log1[log1.find("REG7_T6") - 3000:log1.find("REG7_T6")]
            and "Host_Error" not in t5))
t6a = between(log1, "REG8_T6_2S", "REG9_T6_7S")
t6b = between(log1, "REG9_T6_7S", "REG_END")
res.append(("T6 outside-made folder at ~2 s: %s (informational)" % ("hidden (cached)" if "zzext/probe.cfg isn't anywhere" in t6a else "visible"), True))
res.append(("T6 outside-made folder visible after expiry (~7 s)", "zzext/probe.cfg is file" in t6b and "ZZEXT_OK" in t6b))
tb = between(log2, "REGB", "REGB_END")
res.append(("first launch: config.cfg written and read back (name fcregtest)", "fcregtest" in tb))
res.append(("no Host_Error / crash lines", "Host_Error" not in log1 + log2 and "REG_END" in log1 and "REGB_END" in log2))
with open(os.path.join(out, "result.txt"), "w") as f:
    for n, ok in res:
        line = "%-4s %s" % ("PASS" if ok else "FAIL", n)
        print(line)
        f.write(line + "\n")
