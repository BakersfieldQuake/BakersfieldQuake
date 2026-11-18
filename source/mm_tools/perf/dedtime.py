"""Run the Windows dedicated server like Start Server.cmd does, timestamp its console log, probe getstatus.
    python -I dedtime.py [seconds] [extra engine args...]
The server needs a console of its own (as `start` gives it): started without one it never answers queries.
Isolated -userdir, port 26098; stops only the process it started."""
import os, socket, subprocess, sys, tempfile, time
HERE = os.environ.get("BQ_PERF_DIR") or os.path.join(tempfile.gettempdir(), "bq_perf")
os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
ENGINE_DIR = r"G:\Quake\Combat\engine"
ud = os.path.join(HERE, "ud_ded2"); gd = os.path.join(ud, "BakersfieldQuake"); os.makedirs(gd, exist_ok=True)
log = os.path.join(gd, "zz_ded.log")
if os.path.exists(log): os.remove(log)
limit = float(sys.argv[1]) if len(sys.argv) > 1 else 150
args = [os.path.join(ENGINE_DIR, "zircon_beta_gcc.exe"), "-dedicated", "16", "-basedir", r"G:\Quake\Combat", "-userdir", ud,
        "-port", "26098", "-game", "quake15", "-game", "BakersfieldQuake", "-condebug", "+log_file", "zz_ded.log",
        "+developer_loading", "1"] + sys.argv[2:] + ["+exec", "server.cfg"]
t0 = time.perf_counter()
si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 7  # minimized, not activated
p = subprocess.Popen(args, cwd=ENGINE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=si)  # own console, like "start" in Start Server.cmd
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(0.2)
out = open(os.path.join(HERE, "runs", "ded.timed.log"), "w", encoding="utf-8", errors="replace")
pos = 0; buf = b""; ans = None; nextq = 0
while time.perf_counter() - t0 < limit and p.poll() is None:
    now = time.perf_counter() - t0
    if ans is None and now >= nextq:
        nextq = now + 1.2
        try:
            s.sendto(b"\xff\xff\xff\xffgetstatus", ("127.0.0.1", 26098))
            if b"statusResponse" in s.recv(4096): ans = time.perf_counter() - t0
        except OSError: pass
    if os.path.exists(log):
        with open(log, "rb") as f:
            f.seek(pos); c = f.read(); pos += len(c)
        buf += c
        while b"\n" in buf:
            l, buf = buf.split(b"\n", 1); out.write("%8.2f %s\n" % (now, l.decode("latin-1").rstrip("\r")))
    if ans is not None and now > ans + 4: break
    time.sleep(0.05)
out.close()
print("exited by itself with code", p.returncode) if p.poll() is not None else None
print("answered getstatus after:", ans, "s; log bytes", pos)
p.kill(); print("stopped pid", p.pid)
