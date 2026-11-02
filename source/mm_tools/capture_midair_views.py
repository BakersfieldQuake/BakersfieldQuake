"""capture_midair_views.py — Automated camera + live jump-pad launch test for `maps/midair.bsp`.

Follows CLAUDE.md rules strictly:
- Waits if another `darkplaces.exe` process is running
- Backs up and restores `BakersfieldQuake/config.cfg`
- Launches from `G:/Quake/Combat` on the primary monitor, short unattended run ending with `quit`
- Only terminates its own spawned PID on timeout
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "out", "maps")
MOD_DIR = os.path.abspath(os.path.join(HERE, "..", ".."))
MOD_MAPS = os.path.join(MOD_DIR, "maps")
COMBAT_DIR = os.path.abspath(os.path.join(MOD_DIR, ".."))
DP_EXE = os.path.join(COMBAT_DIR, "darkplaces.exe")
ERICW = r"D:\vibe\quake1opensource\tools\ericw"
PY = sys.executable


def wait_no_darkplaces():
    while True:
        res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq darkplaces.exe"], capture_output=True, text=True)
        if "darkplaces.exe" not in res.stdout.lower():
            return
        time.sleep(2.5)


def run_dp(args, timeout_s=35):
    wait_no_darkplaces()
    cfg = os.path.join(MOD_DIR, "config.cfg")
    bak = os.path.join(OUT_DIR, ".midair_cfg_bak")
    if os.path.exists(cfg):
        shutil.copy2(cfg, bak)
    proc = subprocess.Popen([DP_EXE] + args, cwd=COMBAT_DIR)
    try:
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/F"], capture_output=True)
    finally:
        if os.path.exists(bak):
            shutil.copy2(bak, cfg)
            os.remove(bak)


def capture_spots(spots):
    src_bsp = os.path.join(OUT_DIR, "midair.bsp")
    src_lit = os.path.join(OUT_DIR, "midair.lit")
    tst_bsp = os.path.join(OUT_DIR, "midairtest.bsp")
    tst_lit = os.path.join(OUT_DIR, "midairtest.lit")
    tst_map = os.path.join(OUT_DIR, "midairtest.map")

    shutil.copy2(src_bsp, tst_bsp)
    shutil.copy2(src_lit, tst_lit)

    try:
        for name, start_spec, grav in spots:
            env = dict(os.environ, MIDAIR_START=start_spec)
            subprocess.run([PY, os.path.join(HERE, "make_midair.py"), tst_map], cwd=HERE, env=env, check=True)
            subprocess.run(
                [os.path.join(ERICW, "qbsp.exe"), "-bsp2", "-onlyents", "midairtest.map", "midairtest.bsp"],
                cwd=OUT_DIR,
                check=True,
                capture_output=True,
            )
            shutil.copy2(tst_bsp, os.path.join(MOD_MAPS, "midairtest.bsp"))
            shutil.copy2(tst_lit, os.path.join(MOD_MAPS, "midairtest.lit"))

            out_rel = f"zm_{name}.png"
            out_full = os.path.join(MOD_DIR, out_rel)
            if os.path.exists(out_full):
                os.remove(out_full)

            dp_args = [
                "-window", "-width", "1280", "-height", "720",
                "-game", "quake15", "-game", "BakersfieldQuake",
                "+vid_mouse", "0", "+joystick", "0", "+m_pitch", "0", "+m_yaw", "0",
                "+r_drawviewmodel", "0", "+viewsize", "120", "+crosshair", "0", "+cl_bob", "0", "+fov", "95",
                "+deathmatch", "0", "+coop", "0", "+sv_gravity", str(grav),
                "+map", "midairtest",
                "+defer", "5", f"screenshot {out_rel}",
                "+defer", "6.2", "quit",
            ]
            run_dp(dp_args)
            print(f"Captured {out_rel}: exists={os.path.exists(out_full)}")
    finally:
        for p in (
            os.path.join(MOD_MAPS, "midairtest.bsp"),
            os.path.join(MOD_MAPS, "midairtest.lit"),
            tst_bsp,
            tst_lit,
            tst_map,
        ):
            if os.path.exists(p):
                os.remove(p)


def main():
    spots = [
        # 1. Ground-level arena view looking across the glowing central hole toward the moonlit night sky!
        ("01_arena_moon", "760 -940 84 129 -8", 0),
        # 2. Looking directly down into the glowing central hole & Hyper-Jump Pad!
        ("02_center_hole", "-260 0 190 0 46", 0),
    ]
    capture_spots(spots)


if __name__ == "__main__":
    main()
