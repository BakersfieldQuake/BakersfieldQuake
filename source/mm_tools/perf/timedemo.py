"""Timed playback of a recorded match: repeatable client frame rates, for comparing settings and engines.
    python -I timedemo.py <label> <engine exe> <demo name> [runs] [engine args...]
Record first, with bots, in a scratch copy of the package (never the real game folder: the engine saves config.cfg there):
    python -I loadtime.py rec <map> --record --bots 15 --hold 60 --quiet --basedir <copy> --same-userdir
That writes <copy>\\BakersfieldQuake\\zzb_<map>.dem. Then, for example:
    python -I timedemo.py "defaults" <engine> zzb_terminal21 2
    python -I timedemo.py "no trace culling" <engine> zzb_terminal21 1 +r_cullentities_trace 0 +r_shadow_culllights_trace 0
Playback has no server in it, so it measures the client only (drawing, culling, lighting, particles, the HUD script),
and two runs of one demo agree within about 2%. A live bot match does not: what the bots do swings the frame rate more
than most settings (2026-11-18: three settings looked good or bad in live A/B runs and were all noise).
BQ_PERF_BASE names the scratch copy (default G:\\Quake\\_bq_audit_base). Check that no other zircon process is running;
the script stops only the process it started."""
import os, re, subprocess, sys, time, shutil
label, exe, demo = sys.argv[1], sys.argv[2], sys.argv[3]
runs = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 1
extra = sys.argv[5:] if len(sys.argv) > 4 and sys.argv[4].isdigit() else sys.argv[4:]
BASE = os.environ.get("BQ_PERF_BASE", r"G:\Quake\_bq_audit_base")
G = os.path.join(BASE, "BakersfieldQuake")
out = []
for r in range(runs):
    shutil.copyfile(r"G:\Quake\Combat\lan\seed_config.cfg", os.path.join(G, "config.cfg"))
    log = os.path.join(G, "zz_td.log")
    if os.path.exists(log):
        os.remove(log)
    args = [exe, "-basedir", BASE, "-userdir", BASE, "-port", "26098", "-window", "-width", "1280", "-height", "720",
            "-game", "quake15", "-game", "BakersfieldQuake", "-condebug", "+log_file", "zz_td.log", "+developer_loading", "0",
            "+cl_maxidlefps", "0", "+bgmvolume", "0"] + extra + ["+defer", "3", "timedemo %s" % demo]
    p = subprocess.Popen(args, cwd=r"G:\Quake\Combat\engine")
    t0, res = time.time(), None
    while time.time() - t0 < 300 and p.poll() is None:
        time.sleep(1.0)
        try:
            txt = open(log, encoding="latin-1", errors="replace").read()
        except OSError:
            continue
        m = re.search(r"(\d+) frames ([\d.]+) seconds ([\d.]+) fps, one-second fps min/avg/max: (\d+) (\d+) (\d+)", txt)
        if m:
            res = m; break
        if "Host_Error" in txt or "Engine Error" in txt:
            break
    if p.poll() is None:
        p.kill()
    p.wait()
    time.sleep(1.0)
    out.append((float(res.group(3)), int(res.group(4)), int(res.group(1))) if res else None)
ok = [o for o in out if o]
if ok:
    print("%-34s %s fps (one-second minimum %s; %d frames)" % (label, " / ".join("%.0f" % o[0] for o in ok), " / ".join(str(o[1]) for o in ok), ok[0][2]))
else:
    print("%-34s NO RESULT" % label)
