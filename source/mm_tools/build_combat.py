"""Copy the shared Mega Man / fun gun sources into qc_combat_decomp (with the COMBATPLUS guard), compile with fteqcc64
and install progs.dat into BakersfieldQuake. Does not touch the patched game code, so it is safe after any edit to
megaman.qc / pickle.qc / funguns.qc / banana.qc (unlike re-running the patch_*.py chain).
python -I build_combat.py"""
import shutil
import subprocess
import sys

D = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\qc_combat_decomp\\"
T = "G:\\Quake\\Combat\\BakersfieldQuake\\source\\mm_tools\\"
GUARD = "#ifndef COMBATPLUS\n#define COMBATPLUS\n#endif\n"

import os

# NOT copied any more (2026-11-18): bm_match.qc, funguns.qc, vehicles_defs.qc, vehicles.qc, vehicle_drive.qc,
# john_bird_defs.qc, john_bird.qc. Their newest code (go-karts, Winged John combat, clientstat 93-102) was written
# straight into qc_combat_decomp, so that folder is their home now: edit them THERE. The mm_tools copies are stale.
# NOT copied any more (2026-11-19): m4.qc, garand.qc, jetpack_defs.qc, jetpack.qc, eric_cannon.qc, skypad.qc,
# underdog.qc (Option 1 lossless FPS patch written straight into qc_combat_decomp).
COPY = ("megaman_defs.qc", "megaman.qc", "banana_defs.qc", "banana.qc", "funguns_defs.qc", "greenjar_defs.qc", "dookie_defs.qc", "kyle_defs.qc", "robhead_defs.qc", "pickle.qc", "greenjar.qc", "dookie.qc", "kyle.qc", "robhead.qc", "hitsound.qc",
          "bm_defs.qc", "bm_reload.qc", "bm_fun.qc", "jg_splash.qc", "floathead.qc", "bryan.qc", "david.qc", "daniel.qc", "bklan5_npcs.qc", "random_npcs.qc", "crowd_npcs.qc", "soi6_npcs.qc", "sniper_defs.qc", "sniper.qc", "hammer_defs.qc", "hammer.qc", "sentry_defs.qc", "netsend_diskvm.qc", "netsend_defs.qc", "netsend.qc", "wcannon_defs.qc", "wcannon.qc", "m4_defs.qc", "garand_defs.qc", "milky_defs.qc", "milky.qc", "bklan_tv_data.qc", "bklan_tv.qc", "bklan_movers.qc", "traffic_cars.qc", "spruce_tower.qc", "spruce_bus.qc", "lan_props_defs.qc", "lan_props.qc", "bicycles_defs.qc", "bicycles.qc", "eric_cannon_defs.qc", "lol_props.qc", "bm_bots.qc")


def _norm(t):
    t = t.replace("\r\n", "\n")
    return t[len(GUARD):] if t.startswith(GUARD) else t


# Plan every copy first. If a build copy is NEWER than its mm_tools source and its code differs, someone edited the
# build copy directly: stop before writing anything, so that work is never overwritten.
plan = []
clash = []
for n in COPY:
    s = open(T + n, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")
    if n != "underdog.qc" and not s.startswith(GUARD):
        s = GUARD + s
    if os.path.exists(D + n):
        old = open(D + n, encoding="utf-8", errors="surrogateescape", newline="").read()
        if _norm(old) != _norm(s) and os.path.getmtime(D + n) > os.path.getmtime(T + n):
            clash.append(n)
    plan.append((n, s))
if clash:
    sys.exit("NOT BUILT: these qc_combat_decomp copies are newer than source/mm_tools and differ, so copying would "
             "destroy that work. Move the changes into mm_tools first (or drop the file from COPY): " + ", ".join(clash))
for n, s in plan:
    # Skip files that already match (ignoring line endings and the guard): rewriting them would turn CRLF files into
    # LF and show untouched files as fully changed in git.
    if os.path.exists(D + n) and _norm(open(D + n, encoding="utf-8", errors="surrogateescape", newline="").read()) == _norm(s):
        continue
    open(D + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)
    print("copied", n)

qcc = "D:/vibe/quake1opensource/engines/win64/fteqcc64.exe"
if not os.path.exists(qcc):
    qcc = "G:/Quake/LOLQuake/tools/fteqcc64.exe"
if not os.path.exists(qcc):
    qcc = "D:/vibe/fteqw/2025-09-27-github/fteqcc64.exe"
r = subprocess.run([qcc, "-srcfile", "progs.src"], cwd=D)
if r.returncode:
    sys.exit("compile failed")
shutil.copy(D + "progs.dat", "G:\\Quake\\Combat\\BakersfieldQuake\\progs.dat")
print("installed progs.dat")
