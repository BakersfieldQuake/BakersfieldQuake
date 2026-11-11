"""Build and record BakersfieldQuake/intro.dem in an isolated temp directory without touching progs.dat.

Usage:
  python -I build_intro_demo.py --compile-only
  python -I build_intro_demo.py
  python -I build_intro_demo.py --verify
"""
import math
import os
import re
import shutil
import struct
import subprocess
import sys

ROOT = r"G:\Quake\Combat"
MOD = os.path.join(ROOT, "BakersfieldQuake")
SRC_QC = os.path.join(MOD, "source", "qc_combat_decomp")
TOOLS = os.path.join(MOD, "source", "mm_tools")
BUILD_DIR = os.path.join(TOOLS, "out", "qc_intro_build")
USERDIR = os.path.join(TOOLS, "out", "dp_intro_userdir")
FTEQCC = (
    r"D:\vibe\quake1opensource\engines\win64\fteqcc64.exe"
    if os.path.isfile(r"D:\vibe\quake1opensource\engines\win64\fteqcc64.exe")
    else r"G:\Quake\LOLQuake\tools\fteqcc64.exe"
)
DARKPLACES = os.path.join(ROOT, "darkplaces.exe")
DEMO_OUT = os.path.join(MOD, "intro.dem")
DEMO_NAMED_OUT = os.path.join(MOD, "intro_movie_showcase.dem")


def patch_once(path: str, needle: str, replacement: str) -> None:
    raw = open(path, "rb").read().decode("latin1")
    if needle not in raw:
        alt_needle = needle.replace("\n", "\r\n")
        alt_rep = replacement.replace("\n", "\r\n")
        if alt_needle not in raw:
            raise RuntimeError(f"Expected snippet not found in {path}: {needle!r}")
        raw = raw.replace(alt_needle, alt_rep, 1)
    else:
        raw = raw.replace(needle, replacement, 1)
    open(path, "wb").write(raw.encode("latin1"))


_SKIP_MDL_PREFIXES = (
    "progs/v_",
    "progs/centered/",
    "progs/QC/v_",
    "progs/ltg_view.md3",
    "progs/ltg_v3d.md3",
    "progs/ltg_type_",
    "progs/netsend_scr.md3",
    "progs/p_",
    "progs/QC/p_",
    "progs/gib",
    "progs/h_",
    "progs/w_",
    "progs/zom_gib.mdl",
    "progs/bloodpool.mdl",
    "progs/corpse_pent.mdl",
    "progs/casing.mdl",
    "progs/nailcasing.mdl",
    "progs/missilecasing.mdl",
    "progs/chop.mdl",
    "progs/coal.mdl",
    "progs/wallsplat.mdl",
    "progs/rebreather.mdl",
    "progs/rebr_glass.spr",
    "progs/pack_attach.mdl",
    "progs/spider",
    "progs/warlord",
    "progs/torment",
    "progs/carnivean",
    "progs/yakman",
    "progs/voreling",
    "progs/mon_freddie",
    "progs/mon_jim",
    "progs/afrit",
    "progs/hydra",
    "progs/reiver",
    "progs/ghost_follower",
    "progs/ghost.mdl",
    "progs/soldier",
    "progs/skull.mdl",
    "progs/wings.mdl",
    "progs/web.mdl",
    "progs/lavacrack.mdl",
    "progs/face",
)

_SKIP_SND_PREFIXES = (
    "spider/",
    "warlord/",
    "torment/",
    "carnivean/",
    "yakman/",
    "voreling/",
    "freddie/",
    "jim/",
    "hydra/",
    "reiver/",
    "lostsoul/",
    "vengeance/",
    "soul/",
    "kickgib/",
    "gib/",
    "face/",
    "ghost/",
    "walk/",
    "custom/flesh",
    "buzz/",
    "debris/",
)


def _slim_intro_precaches(build_dir: str) -> None:
    mdl_re = re.compile(r'(precache_model2?\s*\(\s*)"([^"]+)"(\s*\))')
    snd_re = re.compile(r'(precache_sound2?\s*\(\s*)"([^"]+)"(\s*\))')
    skipped_m = set()
    skipped_s = set()

    def repl_m(m):
        s = m.group(2)
        if s in ("progs/player_shot.mdl", "progs/player_torso.mdl"):
            return m.group(0)
        if s.startswith("progs/player_") or s.startswith(_SKIP_MDL_PREFIXES):
            skipped_m.add(s)
            return f'{m.group(1)}"progs/null.spr"{m.group(3)}'
        return m.group(0)

    def repl_s(m):
        s = m.group(2)
        if s == "afrit/body_explode.wav":
            return m.group(0)
        if s.startswith("afrit/") or s.startswith(_SKIP_SND_PREFIXES):
            skipped_s.add(s)
            return f'{m.group(1)}"misc/null.wav"{m.group(3)}'
        return m.group(0)

    for name in os.listdir(build_dir):
        if not name.endswith(".qc") or name == "intro_director.qc":
            continue
        p = os.path.join(build_dir, name)
        raw = open(p, "rb").read().decode("latin1")
        new_raw = snd_re.sub(repl_s, mdl_re.sub(repl_m, raw))
        if new_raw != raw:
            open(p, "wb").write(new_raw.encode("latin1"))
    print(f"Slimmed isolated intro precaches: -{len(skipped_m)} unused models, -{len(skipped_s)} unused sounds")


def compile_isolated_progs() -> str:
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)

    for name in os.listdir(SRC_QC):
        src_path = os.path.join(SRC_QC, name)
        if os.path.isfile(src_path) and (name.endswith(".qc") or name == "progs.src"):
            shutil.copy2(src_path, os.path.join(BUILD_DIR, name))

    shutil.copy2(os.path.join(TOOLS, "intro_director.qc"), os.path.join(BUILD_DIR, "intro_director.qc"))

    patch_once(
        os.path.join(BUILD_DIR, "progs.src"),
        "\nworld.qc\n",
        "\nintro_director.qc\nworld.qc\n",
    )
    patch_once(
        os.path.join(BUILD_DIR, "world.qc"),
        "\tBM_Stats();",
        "\tBM_Stats();\n\tIntro_Stats();\n\tIntro_Precache();\n\tIntro_StartDirector();",
    )
    patch_once(
        os.path.join(BUILD_DIR, "client.qc"),
        "\tFloatHead_StartSpawner();\t// floating heads in deathmatch (floathead.qc)",
        "\t// FloatHead_StartSpawner suppressed for clean cinematic viewing\n\tIntro_SyncPlayer(self);",
    )
    patch_once(
        os.path.join(BUILD_DIR, "client.qc"),
        "void() PlayerPreThink =\n{",
        "void() PlayerPreThink =\n{\n\tif (Intro_PlayerHook())\n\t\treturn;",
    )
    patch_once(
        os.path.join(BUILD_DIR, "client.qc"),
        "void() PlayerPostThink =\n{\n\tlocal float rg_dt, rg_n;",
        "void() PlayerPostThink =\n{\n\tlocal float rg_dt, rg_n;\n\tif (Intro_PlayerHook())\n\t\treturn;",
    )
    patch_once(
        os.path.join(BUILD_DIR, "client.qc"),
        "\tif ((self.model == \"progs/player_torso.mdl\"))\n\t{\n\t\tAttachVwep();\n\t\tAttachVAxe();\n\t\tAttachLegs();\n\t\tAttachPack();\n\t}\n\tif ((self.ishuman == 1))\n\t{\n\t\tSNGHeater();\n\t}",
        "\t// suppressed player weapon/torso/legs/pack/heater attachments for clean intro.dem camera",
    )
    patch_once(
        os.path.join(BUILD_DIR, "client.qc"),
        "\tW_SetCurrentAmmo();",
        "\t// suppressed first-person weaponmodel setup for clean intro.dem camera",
    )
    patch_once(
        os.path.join(BUILD_DIR, "client.qc"),
        "\tbprint(self.netname);\n\tbprint(\" entered the game\\n\");",
        "\t// suppressed for clean intro.dem recording",
    )
    _slim_intro_precaches(BUILD_DIR)

    r = subprocess.run([FTEQCC, "-srcfile", "progs.src"], cwd=BUILD_DIR)
    if r.returncode != 0:
        sys.exit("fteqcc64 failed compiling isolated progs_intro.dat")

    out_dat = os.path.join(BUILD_DIR, "progs.dat")
    if not os.path.isfile(out_dat):
        sys.exit("progs.dat not produced in qc_intro_build")
    print(f"Compiled isolated intro progs: {out_dat} ({os.path.getsize(out_dat)} bytes)")
    return out_dat


def check_no_darkplaces() -> None:
    # Runs in an isolated -userdir and -port 26099; never touch any user darkplaces.exe process.
    return


def _smooth(u: float) -> float:
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return u * u * (3.0 - 2.0 * u)


def _vlerp(a, b, u: float):
    s = _smooth(u)
    return (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, a[2] + (b[2] - a[2]) * s)


def _look_angles(cpos, look):
    dx = look[0] - cpos[0]
    dy = look[1] - cpos[1]
    dz = look[2] - cpos[2]
    fwd = math.hypot(dx, dy)
    yaw = 0.0 if fwd == 0.0 else (math.degrees(math.atan2(dy, dx)) % 360.0)
    pitch = -math.degrees(math.atan2(dz, fwd))
    return (pitch, yaw, 0.0)


def eval_cam_angles(t: float):
    if t < 2.2:
        u = t / 2.2
        cpos = _vlerp((-8590, 2115, 128), (-8695, 2182, 64), u)
        look = _vlerp((-9340, 2485, 310), (-9030, 2435, 88), u)
    elif t < 5.5:
        u = (t - 2.2) / 3.3
        cpos = _vlerp((-8695, 2182, 64), (-8752, 2224, 55), u)
        look = _vlerp((-9030, 2435, 88), (-8990, 2382, 62), u)
    elif t < 11.0:
        u = (t - 5.5) / 5.5
        cpos = _vlerp((-8720, 2205, 50), (-8758, 2235, 56), u)
        look = _vlerp((-8890, 2320, 48), (-8875, 2310, 56), u)
    elif t < 17.0:
        u = (t - 11.0) / 6.0
        cpos = _vlerp((-8645, 2152, 68), (-8595, 2118, 88), u)
        look = _vlerp((-8925, 2345, 58), (-8910, 2335, 72), u)
    elif t < 24.0:
        u = (t - 17.0) / 7.0
        cpos = _vlerp((-8565, 2095, 76), (-8465, 2025, 162), u)
        look = _vlerp((-9060, 2375, 96), (-9240, 2420, 205), u)
    elif t < 27.4:
        u = (t - 24.0) / 3.4
        cpos = _vlerp((-8635, 2145, 78), (-8725, 2210, 92), u)
        look = _vlerp((-8975, 2375, 96), (-9045, 2415, 112), u)
    elif t < 31.0:
        u = max(0.0, min(1.0, (t - 27.4) / 3.6))
        u_orb = 0.72 * u + 0.28 * _smooth(u)
        deg = -48.0 + 360.0 * u_orb
        rad = deg * 0.01745329
        cpos = (
            -9990.0 + math.cos(rad) * 1420.0,
            3440.0 + math.sin(rad) * 2010.0,
            450.0 + 150.0 * math.sin(u * 3.1415927),
        )
        look = (
            -9990.0 + math.cos(rad) * 140.0,
            3440.0 + math.sin(rad) * 200.0,
            415.0,
        )
    elif t < 36.2:
        u = (t - 31.0) / 5.2
        cpos = _vlerp((-8860, 2050, 815), (-8920, 2290, 860), u)
        look = _vlerp((-9565, 2525, 875), (-9565, 2525, 890), u)
    elif t < 40.5:
        u = (t - 36.2) / 4.3
        cpos = _vlerp((-8920, 2290, 860), (-8820, 2090, 835), u)
        look = _vlerp((-9565, 2525, 890), (-9565, 2525, 885), u)
    else:
        u = (t - 40.5) / 7.5
        cpos = _vlerp((-8985, 2285, 285), (-9050, 2348, 302), u)
        look = _vlerp((-9485, 2545, 375), (-9505, 2565, 410), u)
    return _look_angles(cpos, look)


def stamp_demo_headers(demo_path: str) -> None:
    buf = bytearray(open(demo_path, "rb").read())
    nl = buf.index(b"\n") + 1
    off = nl
    t0 = None
    last_ang = eval_cam_angles(0.0)
    pkts = 0
    while off < len(buf):
        ln = struct.unpack_from("<i", buf, off)[0]
        if ln >= 5 and buf[off + 16] == 7:
            sv_t = struct.unpack_from("<f", buf, off + 17)[0]
            if t0 is None:
                t0 = sv_t
            last_ang = eval_cam_angles(max(0.0, sv_t - t0))
        struct.pack_into("<fff", buf, off + 4, last_ang[0], last_ang[1], last_ang[2])
        off += 16 + ln
        pkts += 1
    if off != len(buf):
        raise RuntimeError(f"Demo packet framing mismatch: {off} != {len(buf)}")
    open(demo_path, "wb").write(buf)
    print(f"Stamped {pkts} clean cinema viewangle packet headers into {demo_path}")
    if pkts < 400:
        raise RuntimeError(f"Recorded demo has too few packets ({pkts}); aborting!")


def prepare_userdir() -> str:
    if os.path.exists(USERDIR):
        shutil.rmtree(USERDIR)
    ud_bk = os.path.join(USERDIR, "BakersfieldQuake")
    ud_q15 = os.path.join(USERDIR, "quake15")
    os.makedirs(ud_bk, exist_ok=True)
    os.makedirs(ud_q15, exist_ok=True)
    for src, dst in [
        (os.path.join(MOD, "config.cfg"), os.path.join(ud_bk, "config.cfg")),
        (os.path.join(MOD, "csprogs.dat"), os.path.join(ud_bk, "csprogs.dat")),
        (os.path.join(ROOT, "quake15", "config.cfg"), os.path.join(ud_q15, "config.cfg")),
    ]:
        if os.path.isfile(src):
            shutil.copy2(src, dst)
    return ud_bk


def record_demo(compiled_dat: str) -> None:
    check_no_darkplaces()
    ud_bk = prepare_userdir()
    progs_intro = os.path.join(ud_bk, "progs_intro.dat")
    rec_cfg = os.path.join(ud_bk, "zz_intro_rec.cfg")
    ud_demo = os.path.join(ud_bk, "intro.dem")

    shutil.copy2(compiled_dat, progs_intro)
    open(rec_cfg, "w", encoding="ascii").write(
        "sv_progs progs_intro.dat\n"
        "set intro_autoquit 1\n"
        "set bm_botfill 0\n"
        "set crowd_on 0\n"
        "deathmatch 0\n"
        "coop 0\n"
        "skill 1\n"
        "joy_enable 0\n"
        "sensitivity 0\n"
        "m_pitch 0\n"
        "m_yaw 0\n"
        "cl_forwardspeed 0\n"
        "cl_backspeed 0\n"
        "cl_sidespeed 0\n"
        "cl_upspeed 0\n"
        "chase_active 0\n"
        "r_drawviewmodel 1\n"
        "effects_explosion_shake 0\n"
        "cl_bob 0\n"
        "v_kicktime 0\n"
        "sys_ticrate 0.01\n"
        "cl_maxfps 150\n"
        "rate 1000000\n"
        "_cl_rate 1000000\n"
        "sv_maxrate 1000000\n"
        "r_lerpsprites 0\n"
        "volume 0.05\n"
        "showfps 0\n"
        "cl_showfps 0\n"
        "stopdemo\n"
        "record intro downtown\n"
    )

    cmd = [
        DARKPLACES,
        "-basedir", ROOT,
        "-userdir", USERDIR,
        "-port", "26099",
        "-window",
        "-width", "1280",
        "-height", "720",
        "-nosound",
        "+vid_conwidth", "624",
        "+vid_conheight", "351",
        "-game", "quake15",
        "-game", "BakersfieldQuake",
        "-condebug",
        "+log_file", "zz_intro_rec.log",
        "+stopdemo",
        "+defer", "0.5", "exec zz_intro_rec.cfg",
    ]
    print("Recording smooth 100Hz 8-Act Movie Showcase intro.dem on downtown (~48.0s) in isolated userdir...")
    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        proc.wait(timeout=240)
    except subprocess.TimeoutExpired:
        print(f"Timeout reached; stopping our own darkplaces PID {proc.pid}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if not os.path.isfile(ud_demo) or os.path.getsize(ud_demo) < 150000:
        sys.exit("intro.dem was not created or is unexpectedly small!")
    stamp_demo_headers(ud_demo)
    shutil.copy2(ud_demo, DEMO_NAMED_OUT)
    import time
    installed = False
    for attempt in range(10):
        try:
            shutil.copy2(ud_demo, DEMO_OUT)
            installed = True
            break
        except PermissionError:
            time.sleep(0.5)
    if not installed:
        print(f"WARNING: {DEMO_OUT} is currently held open by running game; saved to {DEMO_NAMED_OUT}")
    else:
        print(f"SUCCESS: Recorded & installed {DEMO_OUT} and {DEMO_NAMED_OUT} ({os.path.getsize(DEMO_OUT):,} bytes)")


def verify_playback() -> None:
    import glob

    check_no_darkplaces()
    ud_bk = prepare_userdir()
    if os.path.isfile(DEMO_NAMED_OUT):
        shutil.copy2(DEMO_NAMED_OUT, os.path.join(ud_bk, "intro.dem"))
    shot_cfg = os.path.join(ud_bk, "zz_verify_shots.cfg")

    open(shot_cfg, "w", encoding="ascii").write(
        "volume 0.05\n"
        "showfps 0\n"
        "cl_showfps 0\n"
        "scr_screenshot_jpeg 0\n"
        "scr_screenshot_png 1\n"
        'defer 1.1 "screenshot zz_movie_01_act1_fox_marquee_crane.png"\n'
        'defer 4.4 "screenshot zz_movie_02_act1_white_van_drift_arrival.png"\n'
        'defer 6.3 "screenshot zz_movie_03_act2_wheelman_barndoors_burnout.png"\n'
        'defer 9.8 "screenshot zz_movie_04_act2_wheelman_pipejet_wewcannon.png"\n'
        'defer 12.2 "screenshot zz_movie_05_act3_clowncar_tableflip_laptophead.png"\n'
        'defer 15.6 "screenshot zz_movie_06_act3_pickle_surprise_bonk_clang.png"\n'
        'defer 18.4 "screenshot zz_movie_07_act4_supercar_bus_bikes_garand.png"\n'
        'defer 22.0 "screenshot zz_movie_08_act4_megaman_mbox_johnwave_trashcans.png"\n'
        'defer 25.5 "screenshot zz_movie_09_act5_hst_milkys_puddle_spinouts.png"\n'
        'defer 29.2 "screenshot zz_movie_10_act5_fox_360_aerial_orbit.png"\n'
        'defer 32.4 "screenshot zz_movie_11_act6_tower_50_tornado_reveal.png"\n'
        'defer 35.2 "screenshot zz_movie_12_act6_tower_50_tornado_peak.png"\n'
        'defer 37.3 "screenshot zz_movie_13_act7_all50_explode_fireballs_tires.png"\n'
        'defer 39.0 "screenshot zz_movie_14_act7_spire_megablast_lens_milk.png"\n'
        'defer 41.8 "screenshot zz_movie_15_act8_burning_fox_wreckedvan_drips.png"\n'
        'defer 45.6 "screenshot zz_movie_16_act8_floating_dan_wheelman_rob_cccs.png"\n'
        'defer 48.4 "quit"\n'
    )
    cmd = [
        DARKPLACES,
        "-basedir", ROOT,
        "-userdir", USERDIR,
        "-port", "26099",
        "-window",
        "-width", "1280",
        "-height", "720",
        "-nosound",
        "+vid_conwidth", "624",
        "+vid_conheight", "351",
        "-game", "quake15",
        "-game", "BakersfieldQuake",
        "-condebug",
        "+log_file", "zz_intro_play.log",
        "+defer", "0.3", "exec zz_verify_shots.cfg",
    ]
    print("Verifying bare startup (`startdemos intro`) on downtown in isolated userdir + capturing 16 HD screenshots...")
    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        proc.wait(timeout=240)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    shots = sorted(glob.glob(os.path.join(ud_bk, "zz_movie_*")) + glob.glob(os.path.join(ud_bk, "screenshots", "zz_movie_*")))
    print(f"Captured {len(shots)} screenshots:")
    for s in shots:
        print(" ", s)


def main() -> None:
    if "--verify" in sys.argv:
        verify_playback()
        return
    if "--record-only" in sys.argv:
        out_dat = os.path.join(BUILD_DIR, "progs.dat")
        if not os.path.isfile(out_dat):
            out_dat = compile_isolated_progs()
        record_demo(out_dat)
        return
    out_dat = compile_isolated_progs()
    if "--compile-only" in sys.argv:
        return
    record_demo(out_dat)


if __name__ == "__main__":
    main()
