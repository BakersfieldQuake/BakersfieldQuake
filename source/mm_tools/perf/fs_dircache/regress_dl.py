"""dlcache regression: a client joins a server whose map is only in a pack it lacks.
    python -I regress_dl.py <client exe> <outdir>
Server: the stock engine, -dedicated, map fctest from fcreg_dl.pk3 in its own user folder, sv_curl_defaulturl = local HTTP.
Client 1st connect: no pack -> curl into dlcache/ -> reconnect -> map loads from the downloaded pack.
Client 2nd launch: pack already in dlcache/ -> no download, map loads."""
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import zipfile

cl_exe, out = os.path.abspath(sys.argv[1]), sys.argv[2]
SV_EXE = r"G:\Quake\zircon-fscache\run\zircon_beta_basebundled.exe"
PKG = r"G:\Quake\zircon-fscache\pkg"
HTTP_PORT, SV_PORT = 26099, 26098
BUSY = r"C:\Users\qxdc\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_e5def20f-17f0-45bd-9a05-6cb1db38ebd2\gunframes-engine-busy.txt"
if os.path.exists(out):
    shutil.rmtree(out)
www, sv_ud, cl_ud = (os.path.join(out, n) for n in ("www", "sv_ud", "cl_ud"))
for d in (www, os.path.join(sv_ud, "BakersfieldQuake"), os.path.join(cl_ud, "BakersfieldQuake")):
    os.makedirs(d)
pk3 = os.path.join(www, "fcreg_dl.pk3")
with zipfile.ZipFile(pk3, "w") as z:
    for name, data in (("fctest_marker.cfg", b"echo FCTEST_PACK_OK\n"),
                       ("maps/fctest.bsp", open(os.path.join(PKG, "BakersfieldQuake", "maps", "aerowalk.bsp"), "rb").read())):
        z.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), data, zipfile.ZIP_STORED)
shutil.copy(pk3, os.path.join(sv_ud, "BakersfieldQuake", "fcreg_dl.pk3"))


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=www, **k)

    def log_message(self, fmt, *a):
        open(os.path.join(out, "http.log"), "a").write((fmt % a) + "\n")


srv = socketserver.TCPServer(("127.0.0.1", HTTP_PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()


def engine_free():
    if os.path.exists(BUSY):
        return False
    return '"zircon' not in subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout.lower()


t = time.time()
while not engine_free():
    if time.time() - t > 3600:
        sys.exit("engine busy for an hour")
    time.sleep(5)

sv = subprocess.Popen([SV_EXE, "-dedicated", "-basedir", PKG, "-userdir", sv_ud, "-port", str(SV_PORT),
                       "-game", "quake15", "-game", "BakersfieldQuake", "-condebug", "+log_file", "zz_sv.log",
                       "+sv_curl_defaulturl", "http://127.0.0.1:%d/" % HTTP_PORT, "+deathmatch", "1", "+maxplayers", "4",
                       "+map", "fctest"], cwd=os.path.dirname(SV_EXE))
svlog = os.path.join(sv_ud, "BakersfieldQuake", "zz_sv.log")
t = time.time()
while time.time() - t < 60 and not (os.path.exists(svlog) and "Server spawned" in open(svlog, errors="replace").read()):
    time.sleep(0.2)

gd = os.path.join(cl_ud, "BakersfieldQuake")
open(os.path.join(gd, "zz_dl1.cfg"), "w").write('echo DL1\nconnect 127.0.0.1:%d\ndefer 20 "exec zz_dl2.cfg"\n' % SV_PORT)
open(os.path.join(gd, "zz_dl2.cfg"), "w").write('echo DL2\nwhich maps/fctest.bsp\nwhich fctest_marker.cfg\necho DL_END\nquit\n')


def client(log):
    p = subprocess.Popen([cl_exe, "-basedir", PKG, "-userdir", cl_ud, "-port", "26097", "-window", "-width", "1280",
                          "-height", "720", "-game", "quake15", "-game", "BakersfieldQuake", "-condebug", "+log_file", log,
                          "+defer", "2", "exec zz_dl1.cfg"], cwd=os.path.dirname(cl_exe))
    try:
        p.wait(120)
    except subprocess.TimeoutExpired:
        p.kill()
        print("client KILLED after 120 s")
    return open(os.path.join(gd, log), errors="replace").read()


log1 = client("zz_cl1.log")
log2 = client("zz_cl2.log")
sv.kill()
srv.shutdown()
http_lines = open(os.path.join(out, "http.log")).read() if os.path.exists(os.path.join(out, "http.log")) else ""
res = [
    ("1st connect: pack downloaded into dlcache/", "Download of dlcache/fcreg_dl.pk3: OK" in log1
     and os.path.exists(os.path.join(gd, "dlcache", "fcreg_dl.pk3"))),
    ("1st connect: map fctest loaded from the pack, in game", "maps/fctest.bsp is in package dlcache/fcreg_dl.pk3" in log1
     and "DL_END" in log1),
    ("2nd launch: no new download, map loaded from dlcache", "Downloading" not in log2
     and "maps/fctest.bsp is in package dlcache/fcreg_dl.pk3" in log2 and http_lines.count("fcreg_dl.pk3") == 1),
    ("no Host_Error", "Host_Error" not in log1 + log2),
]
with open(os.path.join(out, "result.txt"), "w") as f:
    for n, ok in res:
        line = "%-4s %s" % ("PASS" if ok else "FAIL", n)
        print(line)
        f.write(line + "\n")
