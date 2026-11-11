"""Copy the shared Mega Man / fun gun sources into qc_combat_decomp (with the COMBATPLUS guard), compile with fteqcc64
and install progs.dat into BakersfieldQuake. Does not touch the patched game code, so it is safe after any edit to
megaman.qc / pickle.qc / funguns.qc / banana.qc (unlike re-running the patch_*.py chain).
python -I build_combat.py"""
import shutil
import subprocess
import sys

D = "G:\Quake\Combat\BakersfieldQuake\source\qc_combat_decomp\\"
T = "G:\Quake\Combat\BakersfieldQuake\source\mm_tools\\"
GUARD = "#ifndef COMBATPLUS\n#define COMBATPLUS\n#endif\n"

for n in ("megaman_defs.qc", "megaman.qc", "banana_defs.qc", "banana.qc", "funguns_defs.qc", "greenjar_defs.qc", "funguns.qc", "pickle.qc", "greenjar.qc", "hitsound.qc",
          "bm_defs.qc", "bm_reload.qc", "bm_match.qc", "bm_fun.qc", "jg_splash.qc", "floathead.qc", "bryan.qc", "david.qc", "daniel.qc", "bklan5_npcs.qc", "random_npcs.qc", "crowd_npcs.qc","goo_defs.qc", "goo.qc", "sniper_defs.qc", "sniper.qc", "ltgun_defs.qc", "ltgun.qc", "hammer_defs.qc", "hammer.qc", "sentry_defs.qc", "netsend_defs.qc", "netsend.qc", "mbox_defs.qc", "mbox.qc", "wcannon_defs.qc", "wcannon.qc", "m4_defs.qc", "m4.qc", "tommy_defs.qc", "tommy.qc", "garand_defs.qc", "garand.qc", "jetpack_defs.qc", "jetpack.qc", "milky_defs.qc", "milky.qc", "vehicles_defs.qc", "vehicles.qc", "vehicle_drive.qc", "john_bird_defs.qc", "john_bird.qc", "bklan_tv_data.qc", "bklan_tv.qc", "bklan_movers.qc", "lan_props_defs.qc", "lan_props.qc", "bicycles_defs.qc", "bicycles.qc", "skypad.qc", "bm_bots.qc"):
    s = open(T + n, encoding="utf-8", errors="surrogateescape", newline="").read().replace("\r\n", "\n")
    if not s.startswith(GUARD):
        s = GUARD + s
    open(D + n, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s)
    print("copied", n)

open(D + "underdog.qc", "w", encoding="utf-8").write(open(T + "underdog.qc", encoding="utf-8").read())
print("copied underdog.qc")

import os
qcc = "D:/vibe/quake1opensource/engines/win64/fteqcc64.exe"
if not os.path.exists(qcc):
    qcc = "G:/Quake/LOLQuake/tools/fteqcc64.exe"
r = subprocess.run([qcc, "-srcfile", "progs.src"], cwd=D)
if r.returncode:
    sys.exit("compile failed")
shutil.copy(D + "progs.dat", "G:\Quake\Combat\BakersfieldQuake\progs.dat")
print("installed progs.dat")
