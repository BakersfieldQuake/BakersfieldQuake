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
FTEQCC = r"D:\vibe\quake1opensource\engines\win64\fteqcc64.exe"
DARKPLACES = os.path.join(ROOT, "darkplaces.exe")
DEMO_OUT = os.path.join(MOD, "intro.dem")


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
        "bm_fun.qc\nworld.qc",
        "bm_fun.qc\nintro_director.qc\nworld.qc",
    )
    patch_once(
        os.path.join(BUILD_DIR, "world.qc"),
        "\tBM_Stats();",
        "\tBM_Stats();\n\tIntro_Stats();\n\tIntro_Precache();\n\tIntro_StartDirector();",
    )
    patch_once(
        os.path.join(BUILD_DIR, "client.qc"),
        "\tFloatHead_StartSpawner();\t// floating heads in deathmatch (floathead.qc)",
        "\tFloatHead_StartSpawner();\n\tIntro_SyncPlayer(self);",
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
        "\tAttachVwep();\n\tAttachVAxe();\n\tAttachLegs();\n\tAttachPack();\n\tif ((self.ishuman == 1))\n\t{\n\t\tSNGHeater();\n\t}",
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


def backup_file(path: str):
    if os.path.isfile(path):
        return open(path, "rb").read()
    return None


def restore_file(path: str, data) -> None:
    if data is not None:
        open(path, "wb").write(data)
    elif os.path.isfile(path):
        os.remove(path)


def check_no_darkplaces() -> None:
    chk = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process darkplaces* -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
        capture_output=True,
        text=True,
    )
    if chk.stdout.strip():
        sys.exit(f"Refusing to launch darkplaces.exe while existing process is running: {chk.stdout.strip()}")


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
    if t < 4.4:
        u = t / 4.4
        cpos = _vlerp((11520, -2736, 98), (11700, -2736, 62), u)
        look = _vlerp((12180, -2736, 86), (12160, -2736, 68), u)
    elif t < 11.4:
        u = (t - 4.4) / 7.0
        cpos = _vlerp((11700, -2736, 62), (11540, -2736, 128), u)
        look = _vlerp((12160, -2736, 68), (12160, -2736, 88), u)
    elif t < 16.4:
        u = (t - 11.4) / 5.0
        cpos = _vlerp((1340, -11560, 84), (1120, -11340, 62), u)
        look = _vlerp((780, -11040, 138), (780, -11040, 125), u)
    elif t < 21.4:
        u = (t - 16.4) / 5.0
        cpos = _vlerp((618, -10268, 46), (618, -10198, 43), u)
        look = _vlerp((610, -10065, 56), (610, -10055, 64), u)
    elif t < 27.0:
        u = (t - 21.4) / 5.6
        cpos = _vlerp((48, -9520, 94), (48, -9250, 78), u)
        look = _vlerp((48, -9030, 84), (48, -9020, 78), u)
    elif t < 32.0:
        u = (t - 27.0) / 5.0
        cpos = _vlerp((860, -17220, 560), (780, -17300, 1185), u)
        look = _vlerp((520, -17510, 760), (280, -17555, 1235), u)
    elif t < 37.0:
        u = (t - 32.0) / 5.0
        cpos = _vlerp((-240, -18120, 1212), (-110, -17980, 1206), u)
        look = _vlerp((60, -17660, 1208), (90, -17640, 1208), u)
    elif t < 42.0:
        u = (t - 37.0) / 5.0
        cpos = _vlerp((-744, -755, 36), (-744, -675, 32), u)
        look = _vlerp((-744, -565, 48), (-744, -565, 52), u)
    elif t < 47.4:
        u = (t - 42.0) / 5.4
        cpos = _vlerp((436, -758, 30), (472, -758, 27), u)
        look = (548, -758, 38)
    elif t < 52.8:
        u = (t - 47.4) / 5.4
        cpos = _vlerp((-1050, -2195, 29), (-1098, -2195, 26), u)
        look = _vlerp((-1215, -2190, 40), (-1225, -2188, 40), u)
    elif t < 57.8:
        u = (t - 52.8) / 5.0
        cpos = _vlerp((6300, 1134, 34), (6235, 1134, 30), u)
        look = (6125, 1134, 38)
    elif t < 62.8:
        u = (t - 57.8) / 5.0
        cpos = _vlerp((-6397, -12145, 34), (-6397, -12085, 29), u)
        look = (-6397, -11990, 48)
    elif t < 67.8:
        u = (t - 62.8) / 5.0
        cpos = _vlerp((11730, -3745, 34), (11730, -3792, 29), u)
        look = (11730, -3870, 44)
    elif t < 72.8:
        u = (t - 67.8) / 5.0
        cpos = _vlerp((14575, -14090, 34), (14625, -14090, 29), u)
        look = _vlerp((14755, -14090, 48), (14755, -14090, 54), u)
    else:
        u = (t - 72.8) / 5.2
        cpos = _vlerp((11710, -2736, 68), (11520, -2736, 126), u)
        look = _vlerp((12190, -2736, 92), (12280, -2736, 155), u)
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


def prepare_userdir() -> str:
    if os.path.exists(USERDIR):
        shutil.rmtree(USERDIR)
    ud_bk = os.path.join(USERDIR, "BakersfieldQuake")
    ud_q15 = os.path.join(USERDIR, "quake15")
    os.makedirs(ud_bk, exist_ok=True)
    os.makedirs(ud_q15, exist_ok=True)
    for src, dst in [
        (os.path.join(MOD, "config.cfg"), os.path.join(ud_bk, "config.cfg")),
        (os.path.join(ROOT, "quake15", "config.cfg"), os.path.join(ud_q15, "config.cfg")),
    ]:
        if os.path.isfile(src):
            shutil.copy2(src, dst)
    return ud_bk


def record_demo(compiled_dat: str) -> None:
    ud_bk = prepare_userdir()
    progs_intro = os.path.join(ud_bk, "progs_intro.dat")
    rec_cfg = os.path.join(ud_bk, "zz_intro_rec.cfg")
    ud_demo = os.path.join(ud_bk, "intro.dem")

    shutil.copy2(compiled_dat, progs_intro)
    open(rec_cfg, "w", encoding="ascii").write(
        "sv_progs progs_intro.dat\n"
        "set intro_autoquit 1\n"
        "set bm_botfill 0\n"
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
        "stopdemo\n"
        "record intro bklan5\n"
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
    print("Recording smooth 100Hz intro.dem on bklan5 (~78.0s) in isolated userdir...")
    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        proc.wait(timeout=215)
    except subprocess.TimeoutExpired:
        print(f"Timeout reached; stopping our own darkplaces PID {proc.pid}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if not os.path.isfile(ud_demo) or os.path.getsize(ud_demo) < 10000:
        sys.exit("intro.dem was not created or is unexpectedly small!")
    stamp_demo_headers(ud_demo)
    tmp_out = DEMO_OUT + ".tmp"
    shutil.copy2(ud_demo, tmp_out)
    os.replace(tmp_out, DEMO_OUT)
    print(f"SUCCESS: Recorded & installed {DEMO_OUT} ({os.path.getsize(DEMO_OUT):,} bytes)")


def verify_playback() -> None:
    import glob

    ud_bk = prepare_userdir()
    shot_cfg = os.path.join(ud_bk, "zz_verify_shots.cfg")

    open(shot_cfg, "w", encoding="ascii").write(
        "volume 0.05\n"
        "scr_screenshot_jpeg 0\n"
        "scr_screenshot_png 1\n"
        "defer 2.8 \"screenshot zz_shot_01_sign_white_van.png\"\n"
        "defer 8.5 \"screenshot zz_shot_02_sign_all_chars.png\"\n"
        "defer 13.6 \"screenshot zz_shot_03_fox_marquee_robdob.png\"\n"
        "defer 18.8 \"screenshot zz_shot_04_fox_lounge_pickle.png\"\n"
        "defer 23.8 \"screenshot zz_shot_05_fox_stage_wewcannon.png\"\n"
        "defer 26.8 \"screenshot zz_shot_06_fox_stage_milky_drips.png\"\n"
        "defer 30.2 \"screenshot zz_shot_07_padre_jetpack_float.png\"\n"
        "defer 34.0 \"screenshot zz_shot_08_padre_roof_spanner_sentry.png\"\n"
        "defer 36.2 \"screenshot zz_shot_09_padre_roof_sniper_kyle.png\"\n"
        "defer 39.8 \"screenshot zz_shot_10_larry_wh_bonk_hammer.png\"\n"
        "defer 44.3 \"screenshot zz_shot_11_blan130a_netsend.png\"\n"
        "defer 46.8 \"screenshot zz_shot_12_blan130a_laptop_gun.png\"\n"
        "defer 49.4 \"screenshot zz_shot_13_larry120a_mm_rag_polish.png\"\n"
        "defer 51.8 \"screenshot zz_shot_14_larry120a_megaman_bed.png\"\n"
        "defer 55.6 \"screenshot zz_shot_15_orcom_googun_bigears.png\"\n"
        "defer 60.5 \"screenshot zz_shot_16_casino_david_777.png\"\n"
        "defer 65.8 \"screenshot zz_shot_17_crystal_mbox_bryan.png\"\n"
        "defer 70.6 \"screenshot zz_shot_18_park_johnwave_trashcan.png\"\n"
        "defer 75.8 \"screenshot zz_shot_19_finale_white_van_sign.png\"\n"
        "defer 79.5 \"quit\"\n"
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
    print("Verifying bare startup (`startdemos intro`) in isolated userdir + capturing 19 cinematic screenshots...")
    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        proc.wait(timeout=215)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    shots = sorted(glob.glob(os.path.join(ud_bk, "zz_shot_*")) + glob.glob(os.path.join(ud_bk, "screenshots", "zz_shot_*")))
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
