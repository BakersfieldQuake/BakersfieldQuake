"""Build the Bakersfield 3rd-Person 360 Combat & Custom Death Showcase MP4 and send over Telegram.

Outputs:
  docs/player_deaths_bakersfield.mp4   (1280x720@30fps H.264 MP4)
  source/mm_tools/out/pd_video/        (temp frames & verification PNGs)

Usage:
  python -E -P source/mm_tools/build_player_deaths_video.py --all
  python -E -P source/mm_tools/build_player_deaths_video.py --capture
  python -E -P source/mm_tools/build_player_deaths_video.py --telegram
"""
import argparse
import bisect
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parent.parent
ROOT = MOD.parent
SRC_QC = MOD / "source" / "qc_combat_decomp"

ZIRCON = ROOT / "engine" / "zircon_beta_gcc.exe"
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

OUT_ROOT = HERE / "out" / "pd_video"
OUT_MP4 = MOD / "docs" / "player_deaths_bakersfield.mp4"
FRAMES_DIR = OUT_ROOT / "frames"

CHAT_ID = "-4993867752"

_SKIP_MDL_PREFIXES = (
    "progs/boss", "progs/wizard", "progs/demon", "progs/shambler", "progs/knight",
    "progs/ogre", "progs/soldier", "progs/zombie", "progs/dog", "progs/tarbaby",
    "progs/hknight", "progs/fish", "progs/shalrath", "progs/enforcer", "progs/oldone",
    "progs/spider", "progs/afrit", "progs/hydra", "progs/warlord", "progs/torment",
    "progs/carnivean", "progs/yakman", "progs/reiver", "progs/voreling", "progs/wrath",
    "progs/lavaman", "progs/dfury", "progs/freddie", "progs/jim", "progs/slime",
    "progs/ghost", "progs/soul", "progs/lostsoul", "progs/k_spike", "progs/v_spike",
    "progs/w_spike", "progs/zom_gib", "progs/h_boss", "progs/h_demon", "progs/h_dog",
    "progs/h_guard", "progs/h_hell", "progs/h_knight", "progs/h_mega", "progs/h_ogre",
    "progs/h_shal", "progs/h_shams", "progs/h_wizard", "progs/h_zombie",
    "progs/kickgib", "progs/face", "progs/buzz", "progs/pend", "progs/trap",
)

_SKIP_SND_PREFIXES = (
    "spider/", "warlord/", "torment/", "carnivean/", "yakman/", "voreling/",
    "freddie/", "jim/", "hydra/", "reiver/", "lostsoul/", "vengeance/", "soul/",
    "kickgib/", "gib/", "face/", "ghost/", "custom/flesh", "buzz/", "debris/",
)


def _find_fteqcc() -> Path:
    for cand in (
        Path(r"D:\vibe\quake1opensource\engines\win64\fteqcc64.exe"),
        Path(r"G:\Quake\LOLQuake\tools\fteqcc64.exe"),
        Path(r"D:\vibe\fteqw\2025-09-27-github\fteqcc64.exe"),
    ):
        if cand.is_file():
            return cand
    raise FileNotFoundError("fteqcc64.exe not found")


def _get_bot_token() -> str:
    tok = os.environ.get("TG_BOT_TOKEN", "").strip()
    if tok:
        return tok
    ref = HERE / "build_twerk_demo_video.py"
    if ref.is_file():
        m = re.search(r'^BOT_TOKEN\s*=\s*"([^"]+)"', ref.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    raise RuntimeError("TG_BOT_TOKEN not set and fallback not found")


def _patch_once(path: Path, old: str, new: str) -> None:
    raw = path.read_bytes().decode("latin1")
    old_e = old.replace("\n", "\r\n") if "\r\n" in raw else old
    new_e = new.replace("\n", "\r\n") if "\r\n" in raw else new
    if old_e not in raw:
        raise RuntimeError(f"Anchor not found in {path.name}: {old!r}")
    path.write_bytes(raw.replace(old_e, new_e, 1).encode("latin1"))


def _slim_precaches(build_dir: Path, keep_name: str) -> None:
    mdl_re = re.compile(r'(precache_model2?\s*\(\s*)"([^"]+)"(\s*\))')
    snd_re = re.compile(r'(precache_sound2?\s*\(\s*)"([^"]+)"(\s*\))')
    for p in build_dir.iterdir():
        if p.suffix != ".qc" or p.name == keep_name:
            continue
        raw = p.read_bytes().decode("latin1")
        new_raw = snd_re.sub(
            lambda m: f'{m.group(1)}"misc/null.wav"{m.group(3)}'
            if (m.group(2).startswith("afrit/") or m.group(2).startswith(_SKIP_SND_PREFIXES))
            else m.group(0),
            mdl_re.sub(
                lambda m: f'{m.group(1)}"progs/null.spr"{m.group(3)}'
                if m.group(2).startswith(_SKIP_MDL_PREFIXES)
                else m.group(0),
                raw,
            ),
        )
        if new_raw != raw:
            p.write_bytes(new_raw.encode("latin1"))


def compile_director_progs() -> Path:
    build_dir = Path(tempfile.gettempdir()) / "bq_pd_vid_qc"
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    for sp in SRC_QC.iterdir():
        if sp.is_file() and (sp.suffix == ".qc" or sp.name == "progs.src"):
            shutil.copy2(sp, build_dir / sp.name)
    shutil.copy2(HERE / "player_deaths_director.qc", build_dir / "player_deaths_director.qc")

    _patch_once(build_dir / "progs.src", "\nplayer_deaths_frames.qc\nplayer_deaths.qc\n", "\nplayer_deaths_frames.qc\nplayer_deaths.qc\nplayer_deaths_director.qc\n")
    _patch_once(build_dir / "defs_custom.qc", "float() PD_TryCustomPlayerDeath;", "float() PD_TryCustomPlayerDeath;\nvoid() Showcase_Precache;\nvoid() Showcase_StartDirector;\nfloat() Showcase_PlayerHook;\nvoid(entity p) Showcase_SyncPlayer;")
    _patch_once(build_dir / "world.qc", "\tBM_Stats();", "\tBM_Stats();\n\tShowcase_Precache();\n\tShowcase_StartDirector();")
    _patch_once(build_dir / "client.qc", "\tFloatHead_StartSpawner();\t// floating heads in deathmatch (floathead.qc)", "\tShowcase_SyncPlayer(self);")
    _patch_once(build_dir / "client.qc", "\tmusic_changer();", "// suppressed default map music")
    _patch_once(build_dir / "client.qc", "void() PlayerPreThink =\n{", "void() PlayerPreThink =\n{\n\tif (Showcase_PlayerHook())\n\t\treturn;")
    _patch_once(build_dir / "client.qc", "void() PlayerPostThink =\n{\n\tlocal float rg_dt, rg_n;", "void() PlayerPostThink =\n{\n\tlocal float rg_dt, rg_n;\n\tif (Showcase_PlayerHook())\n\t\treturn;")
    _patch_once(build_dir / "client.qc", "\tAttachVwep();\n\t\tAttachVAxe();\n\t\tAttachLegs();\n\t\tAttachPack();", "// showcase camera mode")
    _patch_once(build_dir / "client.qc", "\tW_SetCurrentAmmo();", "// suppressed")
    _patch_once(build_dir / "client.qc", '\tbprint(self.netname);\n\tbprint(" entered the game\\n");', "// suppressed")
    _slim_precaches(build_dir, "player_deaths_director.qc")

    fteqcc = _find_fteqcc()
    r = subprocess.run([str(fteqcc), "-srcfile", "progs.src"], cwd=build_dir, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2500:])
        sys.exit("fteqcc64 failed for player_deaths_director.qc")
    out_dat = build_dir / "progs.dat"
    print(f"Compiled director progs.dat: {out_dat.stat().st_size:,} bytes")
    return out_dat


def _parse_cam_log(log_path: Path):
    samples = []
    pat = re.compile(r"\[PDV_CAM\]\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)")
    for line in log_path.read_text(errors="replace").splitlines():
        m = pat.search(line)
        if m:
            samples.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
    if not samples:
        raise RuntimeError(f"No [PDV_CAM] samples found in {log_path}")
    samples.sort(key=lambda s: s[0])
    return samples


def _interp_cam(samples, t: float):
    ts = [s[0] for s in samples]
    if t <= ts[0]:
        return samples[0][1], samples[0][2], 0.0
    if t >= ts[-1]:
        return samples[-1][1], samples[-1][2], 0.0
    i = bisect.bisect_right(ts, t) - 1
    t0, p0, y0 = samples[i]
    t1, p1, y1 = samples[i + 1]
    u = (t - t0) / max(1e-6, t1 - t0)
    # Shortest-angle yaw wrap
    dy = (y1 - y0 + 180.0) % 360.0 - 180.0
    return p0 + (p1 - p0) * u, (y0 + dy * u) % 360.0, 0.0


def stamp_demo_headers(demo_path: Path, cam_samples) -> None:
    data = bytearray(demo_path.read_bytes())
    nl = data.find(b"\n")
    pos = nl + 1
    first_sv_t = None
    packets = 0
    while pos + 16 <= len(data):
        sz = struct.unpack_from("<I", data, pos)[0]
        if sz == 0 or pos + 16 + sz > len(data):
            break
        payload_start = pos + 16
        payload_end = payload_start + sz
        if payload_end - payload_start >= 5 and data[payload_start] == 7:
            sv_t = struct.unpack_from("<f", data, payload_start + 1)[0]
            if first_sv_t is None and 0.0 <= sv_t < 10000.0:
                first_sv_t = sv_t
            if first_sv_t is not None and 0.0 <= sv_t < 10000.0:
                p, y, r = _interp_cam(cam_samples, max(0.0, sv_t - first_sv_t))
                struct.pack_into("<fff", data, pos + 4, p, y, r)
        pos = payload_end
        packets += 1
    demo_path.write_bytes(data)
    print(f"Stamped {packets} demo packet viewangles from {len(cam_samples)} camera samples")


def capture_video() -> Path:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    progs_dat = compile_director_progs()

    userdir = Path(tempfile.gettempdir()) / "bq_pd_vid_ud"
    shutil.rmtree(userdir, ignore_errors=True)
    ud_bk = userdir / "BakersfieldQuake"
    ud_bk.mkdir(parents=True, exist_ok=True)

    for fn in ("config.cfg", "csprogs.dat"):
        src = MOD / fn
        if src.is_file():
            shutil.copy2(src, ud_bk / fn)
    shutil.copy2(progs_dat, ud_bk / "progs_pdv.dat")

    rec_cfg = ud_bk / "zz_rec.cfg"
    rec_cfg.write_text(
        "seta menu_background 0\n"
        "sv_progs progs_pdv.dat\n"
        "set intro_autoquit 1\n"
        "set bm_botfill 0\n"
        "set crowd_on 0\n"
        "set bm_hud_toys 0\n"
        "seta bm_minimap 0\nbm_minimap 0\n"
        "deathmatch 0\ncoop 0\nmaxplayers 1\n"
        "viewsize 120\ncrosshair 0\nr_drawviewmodel 0\n"
        "showfps 0\ncl_showfps 0\ncon_notify 0\nscr_centertime 0\n"
        "cl_bob 0\nv_kicktime 0\n"
        "sys_ticrate 0.02\ncl_maxfps 30\nrate 1000000\nsv_maxrate 1000000\n"
        "stopdemo\n"
        "record pd_showcase bakersfielddowntown\n",
        encoding="ascii",
    )
    boot_rec = ud_bk / "zz_boot_rec.cfg"
    boot_rec.write_text('defer 0.8 "exec zz_rec.cfg"\n', encoding="ascii")

    cmd_rec = [
        str(ZIRCON), "-basedir", str(ROOT), "-userdir", str(userdir),
        "-port", "26097", "-window", "-width", "1280", "-height", "720", "-nosound",
        "-game", "quake15", "-game", "BakersfieldQuake",
        "-condebug", "+log_file", "zz_rec.log",
        "+vid_mouse", "0", "+m_pitch", "0", "+m_yaw", "0", "+bm_minimap", "0",
        "+stopdemo", "+exec", "zz_boot_rec.cfg",
    ]
    print("Recording pd_showcase.dem on bakersfielddowntown...")
    p = subprocess.Popen(cmd_rec, cwd=ROOT)
    p.wait(timeout=180)

    dem = ud_bk / "pd_showcase.dem"
    log_rec = ud_bk / "zz_rec.log"
    if not dem.is_file() or dem.stat().st_size < 10000:
        tail = log_rec.read_text(errors="replace")[-2000:] if log_rec.is_file() else ""
        sys.exit(f"Demo missing/small: {dem}\n{tail}")
    cam_samples = _parse_cam_log(log_rec)
    stamp_demo_headers(dem, cam_samples)

    vid_dir = ud_bk / "video"
    shutil.rmtree(vid_dir, ignore_errors=True)
    cap_cfg = ud_bk / "zz_cap.cfg"
    cap_cfg.write_text(
        "seta menu_background 0\n"
        "set bm_hud_toys 0\n"
        "seta bm_minimap 0\nbm_minimap 0\n"
        "viewsize 120\ncrosshair 0\nr_drawviewmodel 0\n"
        "showfps 0\ncl_showfps 0\ncon_notify 0\nscr_centertime 0\n"
        "volume 0.90\nbgmvolume 0.20\n"
        "cl_capturevideo_ogg 0\ncl_capturevideo_fps 30\n"
        "cl_capturevideo_demo_stop 1\n"
        "cl_capturevideo_nameformat pd_cap\n"
        "cl_capturevideo 1\n"
        "playdemo pd_showcase\n"
        'defer 90.0 "cl_capturevideo 0; quit"\n',
        encoding="ascii",
    )
    boot_cap = ud_bk / "zz_boot_cap.cfg"
    boot_cap.write_text('defer 0.8 "exec zz_cap.cfg"\n', encoding="ascii")

    cmd_cap = [
        str(ZIRCON), "-basedir", str(ROOT), "-userdir", str(userdir),
        "-port", "26097", "-window", "-width", "1280", "-height", "720",
        "-game", "quake15", "-game", "BakersfieldQuake",
        "-condebug", "+log_file", "zz_cap.log",
        "+vid_mouse", "0", "+m_pitch", "0", "+m_yaw", "0", "+bm_minimap", "0",
        "+stopdemo", "+exec", "zz_boot_cap.cfg",
    ]
    print("Capturing 1280x720@30fps AVI + audio...")
    logp = ud_bk / "zz_cap.log"
    pc = subprocess.Popen(cmd_cap, cwd=ROOT)
    deadline = time.time() + 180
    while pc.poll() is None and time.time() < deadline:
        time.sleep(2.0)
        if logp.is_file():
            try:
                if "Finishing capture of" in logp.read_text(errors="replace"):
                    time.sleep(1.5)
                    pc.terminate()
                    break
            except OSError:
                pass
    try:
        pc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pc.kill()

    avis = sorted(vid_dir.glob("*.avi")) or sorted(ud_bk.glob("*.avi"))
    if not avis:
        tail = logp.read_text(errors="replace")[-2000:] if logp.is_file() else ""
        sys.exit(f"No captured AVI found!\n{tail}")
    avi = avis[0]

    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(avi)],
        capture_output=True, text=True, check=True,
    )
    dur = float(r.stdout.strip())
    fade_st = max(0.0, dur - 1.1)
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        FFMPEG, "-y", "-i", str(avi),
        "-vf", f"fade=t=out:st={fade_st:.2f}:d=1.0,format=yuv420p",
        "-af", f"afade=t=out:st={fade_st:.2f}:d=1.0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "24",
        "-maxrate", "3200k", "-bufsize", "4800k",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(OUT_MP4),
    ], check=True)
    print(f"Encoded {OUT_MP4} ({OUT_MP4.stat().st_size:,} bytes, dur={dur:.2f}s)")

    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    for label, ts in (
        ("01_ko_spin", 1.7),
        ("02_gut_slide", 5.5),
        ("03_limbs_off", 9.3),
        ("04_head_off", 12.9),
        ("05_backflip", 16.7),
        ("06_spasm", 20.6),
    ):
        ts = min(ts, max(0.0, dur - 0.2))
        op = FRAMES_DIR / f"{label}.png"
        subprocess.run(
            [FFMPEG, "-y", "-ss", f"{ts:.2f}", "-i", str(OUT_MP4), "-frames:v", "1", str(op)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        print(f"Frame: {op}")
    return OUT_MP4


def send_telegram() -> None:
    assert OUT_MP4.is_file(), f"Missing {OUT_MP4}"
    token = _get_bot_token()
    cap = (
        "Classic Quake Ranger — 6 New Custom Death Animations in Downtown Bakersfield (3rd-Person 360° Fight)\n"
        "• KO Air Spin • Gut-Fold Fly & Slide • Arms & Legs Blow Off • Head Blows Off • Wild Backflip Pancake • Violent Jitter-Spasm"
    )
    proc = subprocess.run([
        "curl.exe", "-sS", "--max-time", "300",
        "-F", f"chat_id={CHAT_ID}",
        "-F", f"caption={cap}",
        "-F", "supports_streaming=true",
        "-F", f"video=@{OUT_MP4};type=video/mp4",
        f"https://api.telegram.org/bot{token}/sendVideo",
    ], capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)
    print("Telegram sendVideo:", json.dumps({"ok": res.get("ok"), "message_id": res.get("result", {}).get("message_id")}))
    assert res.get("ok") is True, proc.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--telegram", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if not any((args.capture, args.telegram, args.all)):
        args.all = True
    if args.all or args.capture:
        capture_video()
    if args.all or args.telegram:
        send_telegram()


if __name__ == "__main__":
    main()
