"""Automated DarkPlaces in-engine verification & screenshot capture on `start` and `downtownsmall`.
Uses an isolated `-userdir` and `-port 26098`, checks no other `darkplaces.exe` is running,
auto-quits via `defer`, and verifies console logs + captured PNG screenshots.
"""
import glob
import os
import shutil
import subprocess
import sys
import time

MOD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
COMBAT_ROOT = os.path.abspath(os.path.join(MOD_DIR, ".."))
DARKPLACES = os.path.join(COMBAT_ROOT, "darkplaces.exe")
OUT_DIR = os.path.join(MOD_DIR, "source", "mm_tools", "out", "eric_cannon")
SHOTS_DIR = os.path.join(OUT_DIR, "ingame_shots")
USERDIR = os.path.join(OUT_DIR, "dp_userdir")


def ensure_no_darkplaces():
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process darkplaces -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True,
    )
    pids = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    if pids:
        print(f"ERROR: darkplaces.exe already running (PIDs={pids}); refusing to disturb user session!")
        sys.exit(1)


def prep_isolated_userdir():
    if os.path.exists(USERDIR):
        shutil.rmtree(USERDIR, ignore_errors=True)
    bk = os.path.join(USERDIR, "BakersfieldQuake")
    os.makedirs(bk, exist_ok=True)
    os.makedirs(SHOTS_DIR, exist_ok=True)
    # Minimal clean config in isolated userdir so HUD/gamma/FOV are crisp and user's real config.cfg is untouched
    open(os.path.join(bk, "config.cfg"), "w", encoding="ascii").write(
        'unbindall\n'
        'bind w "+forward"\n'
        'bind s "+back"\n'
        'bind a "+moveleft"\n'
        'bind d "+moveright"\n'
        'bind h "impulse 86"\n'
        'bind MOUSE1 "+attack"\n'
        'vid_mouse 0\n'
        'm_pitch 0\n'
        'm_yaw 0\n'
        'con_notify 0\n'
        'fov 95\n'
        'v_gamma 1.12\n'
        'r_hdr_scenebrightness 1.25\n'
        'cl_bob 0\n'
        'crosshair 1\n'
        'scr_screenshot_jpeg 0\n'
        'scr_screenshot_png 1\n'
    )
    return bk


def run_dp_cfg(map_name, cfg_name, cfg_body, log_name, timeout_s=75):
    ensure_no_darkplaces()
    bk = os.path.join(USERDIR, "BakersfieldQuake")
    cfg_path = os.path.join(bk, cfg_name)
    open(cfg_path, "w", encoding="ascii").write(cfg_body)

    cmd = [
        DARKPLACES,
        "-basedir", COMBAT_ROOT,
        "-userdir", USERDIR,
        "-port", "26098",
        "-window",
        "-width", "1280",
        "-height", "720",
        "-game", "quake15",
        "-game", "BakersfieldQuake",
        "-condebug",
        "+vid_mouse", "0",
        "+log_file", log_name,
        "+sv_cheats", "1",
        "+deathmatch", "1",
        "+bm_botfill", "0",
        "+bm_warmup", "0",
        "+maxplayers", "4",
        "+stopdemo",
        "+map", map_name,
        "+defer", "5.5", f"exec {cfg_name}",
    ]
    print(f"Launching DarkPlaces verification on +{map_name} ({cfg_name})...")
    proc = subprocess.Popen(cmd, cwd=COMBAT_ROOT)
    try:
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print(f"Timeout ({timeout_s}s) on {map_name}; terminating our own PID {proc.pid}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main():
    bk = prep_isolated_userdir()

    # --------------------------------------------------------------------------
    # RUN 1: `+map start` — Cheat spawn (`impulse 128`), inspect, mount, blast!
    # --------------------------------------------------------------------------
    cfg_start = (
        "sv_cheats 1\n"
        "bm_botfill 0\n"
        "god\n"
        "r_drawviewmodel 0\n"
        'defer 0.4 "impulse 128"\n'
        'defer 1.0 "impulse 130"\n'
        'defer 1.5 "screenshot shots/ec_01_start_inspect_34.png"\n'
        'defer 2.1 "impulse 86"\n'
        'defer 2.6 "screenshot shots/ec_02_start_mounted_aim.png"\n'
        'defer 3.0 "+attack"\n'
        'defer 3.2 "-attack"\n'
        'defer 3.45 "screenshot shots/ec_03_start_windup_bend.png"\n'
        'defer 3.70 "screenshot shots/ec_04_start_blast_shockring.png"\n'
        'defer 5.20 "screenshot shots/ec_05_start_flight_explosion.png"\n'
        'defer 7.20 "quit"\n'
    )
    run_dp_cfg("start", "zz_ec_start.cfg", cfg_start, "zz_ec_start.log", timeout_s=45)

    # --------------------------------------------------------------------------
    # RUN 2: `+map downtownsmall` — Fox Theater & Padre Hotel monuments,
    #        walk-around inspection, aiming, Wew-Cannon wind-up/shockwaves,
    #        2600u sky-high Bakersfield flight, ear-flapping dive & PC-parts nuke!
    # --------------------------------------------------------------------------
    cfg_dt = (
        "sv_cheats 1\n"
        "bm_botfill 0\n"
        "r_drawviewmodel 0\n"
        # 1) Teleport to Fox Theater Marquee Cannon #1 (front & 3/4 inspection!)
        'defer 0.5 "impulse 131"\n'
        'defer 1.2 "screenshot shots/ec_10_dt_fox_front_face.png"\n'
        # Toggle impulse 130 twice so we cycle Padre -> back to Fox 3/4 hero angle!
        'defer 1.7 "impulse 131"\n'
        'defer 2.3 "screenshot shots/ec_11_dt_padre_front.png"\n'
        'defer 2.8 "impulse 130"\n'
        'defer 3.4 "screenshot shots/ec_12_dt_fox_34_marquee.png"\n'
        # 2) Mount Fox Theater Cannon with H (`impulse 86`) & show over-breech aim down H St!
        'defer 4.0 "impulse 86"\n'
        'defer 4.6 "screenshot shots/ec_13_dt_fox_mounted_aim.png"\n'
        # 3) Click FIRE (`+attack`) -> Wew-Cannon rubber skyward bend + Mach shockrings + canislupusfantasy2.wav!
        'defer 5.0 "+attack"\n'
        'defer 5.2 "-attack"\n'
        'defer 5.44 "screenshot shots/ec_14_dt_windup_rubber_bend.png"\n'
        'defer 5.72 "screenshot shots/ec_15_dt_blast_shockrings.png"\n'
        # 4) Sky-high 2500u+ 3rd-person flight over Downtown Bakersfield & Fox Theater!
        'defer 7.10 "screenshot shots/ec_16_dt_sky_climb_boost.png"\n'
        'defer 8.75 "screenshot shots/ec_17_dt_sky_apex_2600u_glide.png"\n'
        # 5) Hold W (`+forward`) + tilt view down (`cl_pitchspeed 45; +lookdown`) to dive steeply onto H Street!
        'defer 8.90 "cl_pitchspeed 35; +lookdown; +forward"\n'
        'defer 9.80 "-lookdown"\n'
        'defer 10.15 "screenshot shots/ec_18_dt_steep_dive_ears.png"\n'
        'defer 11.75 "screenshot shots/ec_19_dt_impact_explosion_a.png"\n'
        'defer 12.05 "-forward"\n'
        'defer 12.15 "screenshot shots/ec_20_dt_impact_pc_parts_b.png"\n'
        'defer 12.65 "screenshot shots/ec_21_dt_impact_pc_parts_c.png"\n'
        'defer 13.30 "screenshot shots/ec_22_dt_impact_pc_parts_d.png"\n'
        'defer 15.20 "quit"\n'
    )
    run_dp_cfg("downtownsmall", "zz_ec_dt.cfg", cfg_dt, "zz_ec_dt.log", timeout_s=75)

    # Copy all captured screenshots to SHOTS_DIR
    found = sorted(glob.glob(os.path.join(bk, "shots", "*.png")) + glob.glob(os.path.join(USERDIR, "**", "*.png"), recursive=True))
    copied = []
    for p in found:
        bn = os.path.basename(p)
        if bn.startswith("ec_"):
            dst = os.path.join(SHOTS_DIR, bn)
            shutil.copy2(p, dst)
            copied.append(dst)
    print(f"Copied {len(copied)} in-game screenshots to {SHOTS_DIR}:")
    for c in copied:
        print(" ", os.path.basename(c), f"({os.path.getsize(c)//1024} KB)")

    # Check logs for errors/warnings related to eric_cannon
    for lg in ("zz_ec_start.log", "zz_ec_dt.log"):
        lp = os.path.join(bk, lg)
        if not os.path.exists(lp):
            lp2 = os.path.join(MOD_DIR, lg)
            if os.path.exists(lp2):
                lp = lp2
        if os.path.exists(lp):
            txt = open(lp, encoding="latin1", errors="replace").read()
            bad = [ln for ln in txt.splitlines() if any(k in ln.lower() for k in ("error", "fail", "missing", "unprecached", "eric_cannon", "blasted sky-high"))]
            print(f"=== Log highlights ({lg}) ===")
            for ln in bad[:30]:
                print(" ", ln)


if __name__ == "__main__":
    main()
