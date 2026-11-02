"""Unattended DarkPlaces in-game verification for the 4 Random People NPCs on `+map start`.
Follows `CLAUDE.md` strictly:
  - Checks `Get-Process darkplaces*` before launching.
  - Never uses `dm6` or `launch_left.ps1`; launches `G:\\Quake\\Combat\\darkplaces.exe` windowed 1280x720 on `+map start`.
  - Uses `+defer` config ending in `quit`, then moves screenshots to `source/mm_tools/out/random_npcs/ingame/` and cleans up temp cfg/log.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MM_TOOLS = os.path.dirname(HERE)
MOD_ROOT = os.path.abspath(os.path.join(MM_TOOLS, "..", ".."))
COMBAT_ROOT = os.path.dirname(MOD_ROOT)
DP_EXE = os.path.join(COMBAT_ROOT, "darkplaces.exe")
OUT_INGAME = os.path.join(MM_TOOLS, "out", "random_npcs", "ingame")

CFG_PATH = os.path.join(MOD_ROOT, "zz_rnpc_test.cfg")
LOG_PATH = os.path.join(MOD_ROOT, "zz_rnpc.log")

CFG_TEXT = """sv_cheats 1
god
notarget
r_shadows 1
v_glslgamma 1
fov 98
r_drawviewmodel 0
rnpc_stay 1
rnpc_mode 1
impulse 55
defer 1.1 "screenshot zz_rnpc_01_walk_lineup.png"
defer 1.9 "rnpc_mode 2"
defer 2.7 "screenshot zz_rnpc_02_run_lineup.png"
defer 3.3 "rnpc_mode 3"
defer 4.0 "screenshot zz_rnpc_03_funny_emotes.png"
defer 4.5 "chase_active 1; chase_back 125; chase_up 16; +forward"
defer 5.10 "-forward; rnpc_mode 1"
defer 5.8 "screenshot zz_rnpc_04_player_size_compare.png"
defer 6.4 "chase_active 0; rnpc_stay 0; rnpc_mode 0; impulse 51"
defer 7.6 "screenshot zz_rnpc_05_roaming_hall.png"
defer 8.3 "quit"
"""


def main() -> None:
    chk = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process darkplaces* -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
        capture_output=True,
        text=True,
    )
    pids = [ln.strip() for ln in chk.stdout.splitlines() if ln.strip()]
    if pids:
        sys.exit(f"ABORT: Existing darkplaces process(es) active ({pids}); waiting per CLAUDE.md.")

    os.makedirs(OUT_INGAME, exist_ok=True)
    for old in glob.glob(os.path.join(OUT_INGAME, "zz_rnpc_*.png")):
        os.remove(old)

    with open(CFG_PATH, "w", encoding="ascii") as fp:
        fp.write(CFG_TEXT)

    cmd = [
        DP_EXE,
        "-nomouse",
        "-window", "-width", "1280", "-height", "720",
        "-game", "quake15",
        "-game", "BakersfieldQuake",
        "-condebug",
        "+log_file", "zz_rnpc.log",
        "+maxplayers", "2",
        "+deathmatch", "0",
        "+sv_cheats", "1",
        "+map", "start",
        "+defer", "2.5", "exec zz_rnpc_test.cfg",
    ]
    print("Launching DarkPlaces on +map start...")
    proc = subprocess.Popen(cmd, cwd=COMBAT_ROOT)
    try:
        proc.wait(timeout=28)
        print(f"DarkPlaces exited cleanly (code={proc.returncode}, pid={proc.pid}).")
    except subprocess.TimeoutExpired:
        print(f"DarkPlaces timed out; stopping ONLY our PID {proc.pid}...")
        proc.terminate()
        proc.wait(timeout=5)

    # Move screenshots to OUT_INGAME
    found = []
    for pat in (
        os.path.join(MOD_ROOT, "zz_rnpc_*.png"),
        os.path.join(MOD_ROOT, "screenshots", "zz_rnpc_*.png"),
    ):
        for p in sorted(glob.glob(pat)):
            dst = os.path.join(OUT_INGAME, os.path.basename(p))
            shutil.move(p, dst)
            found.append(dst)

    if os.path.isfile(LOG_PATH):
        shutil.copy2(LOG_PATH, os.path.join(OUT_INGAME, "zz_rnpc.log"))
        os.remove(LOG_PATH)
    if os.path.isfile(CFG_PATH):
        os.remove(CFG_PATH)

    print("CAPTURED IN-GAME SCREENSHOTS:", found)


if __name__ == "__main__":
    main()
