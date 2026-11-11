r"""Builds the 100% Self-Contained Interactive HTML Showcase & Drop-In Pack for
Bakersfield Quake's Up-Close Sprite-Only Fox 360° -> 50-Swarm Explosion -> Burning Fox + Floating CCCs, DAN & ROB Intro (`intro.dem` on `maps/downtown.bsp`):
  - Card 201 (0.0s–6.6s): Up-Close 360° Orbit of the Historic Fox Theater with 3 Milkys + 3 Pure .SPR32 Wheelman Sprites & Non-Stop Milky Song!
  - Card 202 (6.6s–11.8s): Sudden Close-Up — 50 Milkys & Wheelman Sprites (25 + 25, Zero 3D Wheelman Models) Spinning Around the Fox Clock Tower!
  - Card 203 (11.8s–15.3s): ALL 50 EXPLODE UP CLOSE — 25 Milky Geysers + 25 360° Wheelman Sprite Fireballs + Lens Milk Drips!
  - Card 204 (15.3s–22.5s): FOX ON FIRE + 24 Floating Yellow CCCs + Floating DAN & ROB ("I'm floating!" & "Ah, I can't see!")!
Outputs:
  - G:\Quake\Combat\BakersfieldQuake\bakersfield_intro_demo.html
  - G:\Quake\Combat\BakersfieldQuake\source\mm_tools\out\bakersfield_intro_demo_pack.zip
"""
import base64
import json
import os
import subprocess
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(HERE, "out")
SHOTS_DIR = os.path.join(OUT_DIR, "dp_intro_userdir", "BakersfieldQuake")
PK3_PATH = os.path.join(MOD_ROOT, "bakersfield.pk3")
PAK0_PATH = os.path.abspath(os.path.join(MOD_ROOT, "..", "quake15", "q15.pk3"))
FFMPEG = r"C:\Users\qxdc\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"

OUT_HTML = os.path.join(MOD_ROOT, "bakersfield_intro_demo.html")
OUT_ZIP = os.path.join(OUT_DIR, "bakersfield_intro_demo_pack.zip")


SHOTS_META = [
    ("zz_f360v2_01_fox360_se_closeup_3milkys_3wheelmans.png", 1, 0.9, "Up-Close 360° Fox Orbit (SE Marquee) — 3 Milkys & 3 Wheelman Sprites Right in Front of the Lens!"),
    ("zz_f360v2_02_fox360_east_hst_closeup.png", 1, 2.4, "Up-Close 360° Fox Orbit (East H St) — Fire-Wheels & Jetpack Wheelman Sprites + 3 Milkys Whipping Past FOX Neon!"),
    ("zz_f360v2_03_fox360_north_flytower_closeup.png", 1, 4.1, "Up-Close 360° Fox Orbit (North Fly-Tower) — Zero-G Close-Up Formation Behind the Historic Auditorium!"),
    ("zz_f360v2_04_fox360_west_20thst_pipejet.png", 1, 5.7, "Up-Close 360° Fox Orbit (West → South 20th St) — Pipe-Jet Afterburner Wheelman Sprite Completing the 360°!"),
    ("zz_f360v2_05_tower_closeup_50_swarm_reveal.png", 2, 7.3, "UP-CLOSE TOWER REVEAL — 50 Milkys & Wheelman Sprites (25 + 25) Surrounding the Fox Clock Tower!"),
    ("zz_f360v2_06_tower_closeup_50_sprites_milkys_spin.png", 2, 9.6, "50-Sprite Clock Tower Cyclone — Pure .SPR32 Wheelman Sprites & Milkys Whipping Past the Lens!"),
    ("zz_f360v2_07_tower_closeup_50_cyclone_peak.png", 2, 11.3, "Supersonic Vortex Peak — 25 Milkys + 25 Wheelman Sprites Spinning at Full Speed Around the Belfry!"),
    ("zz_f360v2_08_all50_explode_wave1_lower_fireballs.png", 3, 12.6, "ALL 50 EXPLODE UP CLOSE (Wave 1) — Lower Rings Erupting in Milky Geysers & 360° Wheelman Sprite Fireballs!"),
    ("zz_f360v2_09_all50_explode_wave2_upper_fireballs.png", 3, 13.6, "ALL 50 EXPLODE UP CLOSE (Wave 2) — Escalating 4-Tier Wheelman Fireball Sprites Climbing the Spire!"),
    ("zz_f360v2_10_spire_megablast_lens_milk_drips.png", 3, 14.5, "Spire-Top Mega Detonation — Thick White Milk Drips Splashed Right Across the Camera Lens!"),
    ("zz_f360v2_11_burning_fox_floating_cccs_dan_rob_drips.png", 4, 16.4, "FOX ON FIRE + FLOATING CCCs, DAN & ROB — Roaring Flames Engulf the Fox While Yellow Cs, DAN & ROB Levitate!"),
    ("zz_f360v2_12_burning_fox_floating_cccs_dan_rob_clear.png", 4, 19.6, "\"I'm Floating!\" & \"Ah, I Can't See!\" — 24 Spinning Yellow Cs Around Floating DAN & ROB Over the Blazing Fox!"),
]


CARDS_DATA = [
    {
        "card": 1,
        "t0": 0.0,
        "t1": 6.6,
        "short": "01 • Up-Close 360° Fox",
        "landmark": "2001 H St // Up-Close 360° Fox Orbit (Milky Song Starts!)",
        "title": "Up-Close 360° Fox Theater Orbit: 3 Milkys + 3 Wheelman Sprites Right in Front of the Lens!",
        "desc": "The Milky Milky song (milky/song.ogg) kicks in from 0.0s and plays uninterrupted the entire intro while the camera whips a fast 6.6-second 360° orbit around the Historic Fox Theater with 3 Milky Milky Grenades and 3 pure .spr32 Wheelman sprites (Fire-Wheels Burnout, Jetpack Hover & Zen Lotus → Pipe-Jet) floating ~195 units right in front of the lens!",
        "weapons": ["Non-Stop Milky Song", "Fast 6.6s 360° Orbit", "~195u Close-Up Lens Lock"],
        "vehicles": ["1930 Historic Fox Theater"],
        "chars": ["3 Milky Milky Grenades", "3 Pure .SPR32 Wheelman Sprites"],
        "sfx_path": "sound/milky/song.ogg",
        "sfx_label": "🥛🎵 Non-Stop Milky Song (Plays Whole Time!)",
        "shots": [0, 1, 2, 3],
    },
    {
        "card": 2,
        "t0": 6.6,
        "t1": 11.8,
        "short": "02 • Close-Up 50 Spin!",
        "landmark": "Fox Clock Tower // Up-Close 50-Sprite Cyclone",
        "title": "SUDDEN CLOSE-UP: 50 Milkys & Wheelman Sprites Spinning Around the Clock Tower!",
        "desc": "Camera snaps right up to the Fox Clock Tower (~3x closer than v1, zero letterbox clipping!) as 25 Milky Milky Grenades and 25 pure .spr32 Wheelman sprites (Fire-Wheels, B-Boy Headspin, Pipe-Jet, Jetpack Hover, Screaming, Dancer & Green-Suit — zero 3D Wheelman models!) spin up into a frantic cyclone around the belfry!",
        "weapons": ["Up-Close Belfry Framing", "5 Stacked Rings (5×10 = 50)"],
        "vehicles": ["74-Ft Fox Clock Tower"],
        "chars": ["25 Milky Milky Grenades", "25 Wheelman .SPR32 Sprites Only"],
        "sfx_path": "sound/bryan/noway.wav",
        "sfx_label": "😱 'NO WAY!!' Close-Up 50-Sprite Swarm",
        "shots": [4, 5, 6],
    },
    {
        "card": 3,
        "t0": 11.8,
        "t1": 15.3,
        "short": "03 • ALL 50 EXPLODE!!",
        "landmark": "Fox Clock Tower // Up-Close 50-Entity Detonation",
        "title": "ALL 50 EXPLODE IN YOUR FACE: 25 Milky Geysers + 25 Wheelman Sprite Fireballs!",
        "desc": "All 50 spinning Milkys and Wheelman sprites detonate up close in a rapid 2.2-second chain reaction: 25 white milky_boom geysers + s_explodbig.spr blasts and 25 escalating 4-tier 360° Wheelman sprite fireball explosions (zero 3D tire/axle/dome models!), splashing thick white milk drips right across the camera lens!",
        "weapons": ["25 Milky Dairy Geysers", "25 360° Wheelman Sprite Fireballs", "Lens Milk Drips"],
        "vehicles": ["Pure Sprite & Particle Blasts"],
        "chars": ["All 50 Exploding Up Close!"],
        "sfx_path": "sound/wcannon/wc_boom.wav",
        "sfx_label": "💥🥛 50-Sprite Tower Detonation!",
        "shots": [7, 8, 9],
    },
    {
        "card": 4,
        "t0": 15.3,
        "t1": 22.5,
        "short": "04 • Burning Fox + CCCs + DAN & ROB!",
        "landmark": "Blazing Fox Theater // Floating CCCs, DAN & ROB",
        "title": "FOX THEATER ON FIRE + 24 Floating CCCCCCs + Floating DAN & ROB (\"I'm Floating!\" & \"Ah, I Can't See!\")!",
        "desc": "After everyone explodes, 28 roaring flame & black smoke columns engulf the Fox Marquee, glowing FOX sign, roofline, and Clock Tower while 24 bright yellow letter Cs (progs/ccc.md3 + ccc_trail) float all around levitating DAN (daniel.spr32 squinting blindly) and ROB (fr_rob.spr32 pedaling in mid-air) as you hear \"I'm floating!\" and \"Ah, I can't see!\" over the Milky song!",
        "weapons": ["28 Fox Fire & Smoke Columns", "24 Floating Yellow CCCCCCs", "\"I'm Floating\" + \"Ah, I Can't See!\""],
        "vehicles": ["Blazing Fox Marquee & Tower"],
        "chars": ["Floating DAN (daniel.spr32)", "Floating ROB (fr_rob.spr32)"],
        "sfx_path": "sound/ccc/shoot.wav",
        "sfx_label": "😵🟡 \"Ah, I Can't See!\" (CCC Clip)",
        "shots": [10, 11],
    },
]

EXTRA_SOUNDBOARD = [
    ("🛞✨ \"I'm Floating!\" (Floating DAN, ROB & CCCs)", "sound/jetpack/floating.wav", "Act 04"),
    ("🟡😂 \"CCC! C-C-C-C!\" (Daniel Yellow-C Burst)", "sound/daniel/ccc_burst.wav", "Act 04"),
]

ALL_CAST = [
    "1. Non-Stop Milky Milky Soundtrack (sound/milky/song.ogg playing continuously from 0.0s to 22.5s!)",
    "2. 3 Up-Close Milky Milky Grenades in Fast 360° Fox Orbit (~208u from lens, 16-angle video skins & milk_drip)",
    "3. 3 Up-Close Wheelman .SPR32 Sprites in 360° Fox Orbit — Fire-Wheels Burnout, Jetpack Hover & Zen Lotus → Pipe-Jet",
    "4. 25 Up-Close Vortex Milkys + 25 Pure .SPR32 Wheelman Sprites Spinning Around the Fox Clock Tower (Zero 3D Wheelman Models!)",
    "5. 25 Escalating 360° 14-Frame Wheelman Sprite Fireball Explosions (progs/wheelman.spr32 tiers 0..3) + 25 Milky Geysers + Lens Milk Drips!",
    "6. Blazing Historic Fox Theater — 28 Roaring Additive Flame Sprite Columns (torchflametop.spr32 + s_flame.spr) & Rising Black Smoke!",
    "7. Floating DAN Up Close (progs/daniel.spr32, ~298px tall, alternating Blind \"I Can't See!\" Squint & \"CCC!\" Grin!)",
    "8. Floating ROB Up Close (progs/fr_rob.spr32, ~299px tall, zero-gravity mid-air pedaling right beside DAN!)",
    "9. 24 Floating Bright Yellow Letter 'C's (progs/ccc.md3 + ccc_trail) Orbiting & Tumbling in Zero-G!",
    "10. Signature Finale Voice Cues: \"I'm floating!\" (jetpack/floating.wav + funny/imfloating.wav) & \"Ah, I can't see!\" (ccc/shoot.wav)!",
]


def encode_shot_b64(fname: str, width: int = 1280) -> str:
    p = os.path.join(SHOTS_DIR, fname)
    if not os.path.isfile(p):
        p_alt = os.path.join(SHOTS_DIR, "screenshots", fname)
        if os.path.isfile(p_alt):
            p = p_alt
        else:
            raise FileNotFoundError(f"Missing screenshot: {p}")
    with tempfile.TemporaryDirectory() as td:
        dst = os.path.join(td, "shot.jpg")
        subprocess.run(
            [
                FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-i", p,
                "-vf", f"scale={width}:-1:flags=lanczos",
                "-q:v", "3",
                dst,
            ],
            check=True,
        )
        jpg_bytes = open(dst, "rb").read()
    return "data:image/jpeg;base64," + base64.b64encode(jpg_bytes).decode("ascii")


def encode_sfx_mp3_b64(zf_pk3: zipfile.ZipFile, zf_pak0: zipfile.ZipFile | None, rel_path: str) -> str:
    raw = None
    disk_p = os.path.join(MOD_ROOT, rel_path.replace("/", os.sep))
    if os.path.isfile(disk_p):
        raw = open(disk_p, "rb").read()
    elif rel_path in zf_pk3.namelist():
        raw = zf_pk3.read(rel_path)
    elif zf_pak0 is not None and rel_path in zf_pak0.namelist():
        raw = zf_pak0.read(rel_path)
    if not raw:
        raise FileNotFoundError(f"Missing sound asset: {rel_path}")

    ext = os.path.splitext(rel_path)[1] or ".wav"
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in" + ext)
        dst = os.path.join(td, "out.mp3")
        with open(src, "wb") as f:
            f.write(raw)
        subprocess.run(
            [
                FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                "-i", src,
                "-t", "4.4",
                "-ac", "1", "-ar", "24000", "-b:a", "56k",
                dst,
            ],
            check=True,
        )
        mp3_bytes = open(dst, "rb").read()
    return "data:audio/mpeg;base64," + base64.b64encode(mp3_bytes).decode("ascii")


def build_drop_in_zip() -> int:
    dem_src = os.path.join(MOD_ROOT, "intro_fox360_swarm.dem")
    if not os.path.isfile(dem_src):
        dem_src = os.path.join(MOD_ROOT, "intro.dem")

    files_to_pack = [
        (dem_src, "BakersfieldQuake/intro.dem"),
        (dem_src, "BakersfieldQuake/intro_fox360_swarm.dem"),
        (os.path.join(MOD_ROOT, "csprogs.dat"), "BakersfieldQuake/csprogs.dat"),
        (os.path.join(MOD_ROOT, "quake.rc"), "BakersfieldQuake/quake.rc"),
        (os.path.join(HERE, "intro_director.qc"), "BakersfieldQuake/source/mm_tools/intro_director.qc"),
        (os.path.join(HERE, "build_intro_demo.py"), "BakersfieldQuake/source/mm_tools/build_intro_demo.py"),
        (os.path.join(MOD_ROOT, "source", "qc_combat_decomp", "csqc", "bm_hud.qc"), "BakersfieldQuake/source/qc_combat_decomp/csqc/bm_hud.qc"),
    ]
    tour_dem = os.path.join(MOD_ROOT, "intro_downtown_tour.dem")
    if os.path.isfile(tour_dem):
        files_to_pack.append((tour_dem, "BakersfieldQuake/intro_downtown_tour.dem"))
    tour_qc = os.path.join(HERE, "intro_director_downtown_tour.qc")
    if os.path.isfile(tour_qc):
        files_to_pack.append((tour_qc, "BakersfieldQuake/source/mm_tools/intro_director_downtown_tour.qc"))

    os.makedirs(OUT_DIR, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc in files_to_pack:
            zf.write(src, arc)
    return os.path.getsize(OUT_ZIP)


def main() -> None:
    print("Packing drop-in zip...")
    zip_bytes = build_drop_in_zip()
    print(f"  -> {OUT_ZIP} ({zip_bytes / (1024*1024):.2f} MB)")

    print("Encoding 12 HD 1280x720 screenshots as embedded base64...")
    shots_payload = []
    for idx, (fname, card_no, ts, cap) in enumerate(SHOTS_META):
        uri = encode_shot_b64(fname)
        shots_payload.append({
            "idx": idx,
            "file": fname,
            "card": card_no,
            "t": ts,
            "caption": cap,
            "src": uri,
        })

    print("Encoding signature Milky Song, Explosion, 'I'm Floating' & 'Ah, I Can't See!' audio clips as embedded base64 MP3...")
    zf_pk3 = zipfile.ZipFile(PK3_PATH, "r")
    zf_pak0 = zipfile.ZipFile(PAK0_PATH, "r") if os.path.isfile(PAK0_PATH) else None
    cards_payload = []
    for c in CARDS_DATA:
        sfx_uri = encode_sfx_mp3_b64(zf_pk3, zf_pak0, c["sfx_path"])
        c_out = dict(c)
        c_out["sfx_uri"] = sfx_uri
        cards_payload.append(c_out)
    extra_sfx_payload = []
    for lbl, spath, badge in EXTRA_SOUNDBOARD:
        extra_sfx_payload.append({
            "label": lbl,
            "badge": badge,
            "uri": encode_sfx_mp3_b64(zf_pk3, zf_pak0, spath),
        })
    zf_pk3.close()
    if zf_pak0:
        zf_pak0.close()

    dem_src = os.path.join(MOD_ROOT, "intro_fox360_swarm.dem")
    if not os.path.isfile(dem_src):
        dem_src = os.path.join(MOD_ROOT, "intro.dem")
    dem_mb = os.path.getsize(dem_src) / (1024 * 1024)
    zip_mb = zip_bytes / (1024 * 1024)

    data_json = json.dumps({
        "shots": shots_payload,
        "cards": cards_payload,
        "extraSfx": extra_sfx_payload,
        "castList": ALL_CAST,
    })

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bakersfield Quake — Up-Close Sprite-Only Fox 360° → 50-Swarm Explosion → Burning Fox + Floating CCCs, DAN &amp; ROB (intro.dem)</title>
<style>
  :root {{
    --bg:#090c14; --panel:#111726; --panel2:#182036; --panel3:#212c47;
    --ink:#f8fafc; --dim:#94a3b8; --gold:#fbbf24; --gold-dim:#453209;
    --cyan:#38bdf8; --red:#f43f5e; --lime:#4ade80; --pink:#f472b6;
    --border:#293654;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0;
    background:radial-gradient(circle at 50% -10%, #1c2847 0%, var(--bg) 55%);
    color:var(--ink);
    font:14px/1.5 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    min-height:100vh;
    padding:16px 14px 64px;
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:16px;
  }}
  .wrap {{ width:min(100%, 1240px); display:flex; flex-direction:column; gap:16px; }}

  header {{
    background:rgba(17,23,38,0.92);
    border:1px solid var(--border);
    border-radius:16px;
    padding:18px 20px;
    display:flex;
    flex-wrap:wrap;
    align-items:center;
    justify-content:space-between;
    gap:14px;
    box-shadow:0 16px 40px rgba(0,0,0,0.45);
  }}
  .brand {{ display:flex; flex-direction:column; gap:6px; max-width:760px; }}
  .badges {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .badge {{
    font-size:11px; font-weight:800; letter-spacing:0.05em; text-transform:uppercase;
    padding:3px 9px; border-radius:999px; border:1px solid transparent;
  }}
  .badge.gold {{ background:linear-gradient(135deg,#fde047,#f59e0b); color:#171103; }}
  .badge.cyan {{ background:rgba(56,189,248,0.15); color:#7dd3fc; border-color:rgba(56,189,248,0.38); }}
  .badge.pink {{ background:rgba(244,114,182,0.18); color:#fbcfe8; border-color:rgba(244,114,182,0.45); }}
  .badge.lime {{ background:rgba(74,222,128,0.15); color:#86efac; border-color:rgba(74,222,128,0.38); }}

  h1 {{ margin:0; font-size:clamp(20px, 2.7vw, 29px); font-weight:900; letter-spacing:-0.02em; }}
  h1 span {{ color:var(--gold); }}
  .sub {{ margin:0; color:var(--dim); font-size:13.5px; }}
  .sub code {{ background:#1f2a44; color:#fde68a; padding:2px 6px; border-radius:5px; font-weight:700; }}

  .actions {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
  .btn {{
    background:var(--panel2); color:var(--ink); border:1px solid #36486e;
    border-radius:10px; padding:9px 13px; font:inherit; font-size:12.5px; font-weight:750;
    cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; gap:6px;
    transition:all 0.14s ease;
  }}
  .btn:hover {{ border-color:var(--gold); color:var(--gold); transform:translateY(-1px); }}
  .btn.primary {{
    background:linear-gradient(135deg, #f59e0b 0%, #eab308 100%);
    color:#140e02; border-color:#fde047; font-weight:900;
  }}
  .btn.primary:hover {{ filter:brightness(1.07); color:#000; }}
  .btn.active {{
    background:linear-gradient(135deg, #1d3557 0%, #172554 100%);
    border-color:var(--cyan); color:#bae6fd;
    box-shadow:0 0 18px rgba(56,189,248,0.25);
  }}

  .stage-card {{
    background:var(--panel); border:1px solid var(--border); border-radius:16px;
    padding:16px; box-shadow:0 18px 46px rgba(0,0,0,0.45);
    display:flex; flex-direction:column; gap:12px;
  }}
  .mode-tabs {{
    display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:10px;
    border-bottom:1px solid var(--border); padding-bottom:12px;
  }}
  .tab-pair {{ display:flex; flex-wrap:wrap; gap:8px; }}
  .now-playing {{
    font-size:12.5px; color:#fde68a; background:rgba(251,191,36,0.1);
    border:1px solid rgba(251,191,36,0.32); padding:6px 12px; border-radius:999px; font-weight:700;
  }}

  .viewport-wrap {{
    position:relative; width:100%; aspect-ratio:16/9; background:#04060b;
    border-radius:12px; overflow:hidden; border:1px solid #2c3b5e;
  }}
  video#heroVideo, img#storyImg {{
    width:100%; height:100%; object-fit:contain; display:block; background:#000;
  }}
  .story-overlay {{
    position:absolute; inset:auto 0 0 0;
    background:linear-gradient(to top, rgba(5,8,15,0.94) 0%, rgba(5,8,15,0.68) 65%, transparent 100%);
    padding:26px 18px 14px; display:flex; flex-wrap:wrap; justify-content:space-between;
    align-items:flex-end; gap:10px;
  }}
  .story-cap-title {{ font-size:15px; font-weight:850; color:#fff; }}
  .story-cap-sub {{ font-size:12.5px; color:#cbd5e1; }}
  .story-controls {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}

  .chapters-strip {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(190px, 1fr)); gap:6px;
  }}
  .chap-btn {{
    background:var(--panel2); border:1px solid #2b3a59; color:#cbd5e1;
    border-radius:8px; padding:7px 9px; font:inherit; font-size:11.5px; font-weight:700;
    cursor:pointer; text-align:left; transition:all 0.12s ease;
    display:flex; justify-content:space-between; align-items:center; gap:4px;
  }}
  .chap-btn:hover {{ border-color:var(--gold); color:#fff; }}
  .chap-btn.milky {{ border-color:rgba(244,114,182,0.55); color:#fbcfe8; }}
  .chap-btn.on {{
    background:linear-gradient(135deg, #3b2a0a 0%, #241a07 100%);
    border-color:var(--gold); color:#fde68a;
    box-shadow:0 0 14px rgba(251,191,36,0.22);
  }}
  .chap-time {{ font-family:ui-monospace, Consolas, monospace; font-size:10.5px; color:#94a3b8; }}
  .chap-btn.on .chap-time {{ color:#fcd34d; }}

  .soundboard {{
    background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:16px;
    display:flex; flex-direction:column; gap:10px;
  }}
  .sec-hdr {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:baseline; gap:8px; }}
  .sec-hdr h2 {{ margin:0; font-size:18px; font-weight:850; color:#fff; }}
  .sec-hdr span {{ font-size:12.5px; color:var(--dim); }}
  .sfx-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(215px, 1fr)); gap:7px; }}
  .sfx-btn {{
    background:var(--panel2); border:1px solid #304063; color:#e2e8f0;
    border-radius:9px; padding:8px 10px; font:inherit; font-size:12px; font-weight:700;
    cursor:pointer; text-align:left; transition:all 0.12s ease;
    display:flex; align-items:center; justify-content:space-between; gap:6px;
  }}
  .sfx-btn:hover {{ border-color:var(--cyan); color:#7dd3fc; transform:translateY(-1px); }}
  .sfx-btn.playing {{ border-color:var(--lime); background:#132f23; color:#86efac; }}

  .cards-grid {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(370px, 1fr)); gap:14px;
  }}
  .landmark-card {{
    background:var(--panel); border:1px solid var(--border); border-radius:14px;
    overflow:hidden; display:flex; flex-direction:column;
    transition:border-color 0.15s ease, transform 0.15s ease;
  }}
  .landmark-card.milky-highlight {{
    border-color:rgba(244,114,182,0.65);
    box-shadow:0 0 26px rgba(244,114,182,0.16);
  }}
  .landmark-card:hover {{ border-color:#4b6394; transform:translateY(-2px); }}
  .card-thumb-wrap {{ position:relative; aspect-ratio:16/9; background:#000; cursor:pointer; }}
  .card-thumb-wrap img {{ width:100%; height:100%; object-fit:cover; display:block; }}
  .card-num-pill {{
    position:absolute; top:9px; left:9px; background:rgba(9,12,20,0.88);
    border:1px solid rgba(251,191,36,0.6); color:var(--gold);
    font-size:11px; font-weight:850; padding:3px 9px; border-radius:999px;
  }}
  .card-time-pill {{
    position:absolute; top:9px; right:9px; background:rgba(9,12,20,0.88);
    border:1px solid rgba(56,189,248,0.45); color:#bae6fd;
    font-family:ui-monospace, Consolas, monospace; font-size:11px; font-weight:750;
    padding:3px 8px; border-radius:999px;
  }}
  .shot-switch {{
    position:absolute; bottom:8px; right:8px; display:flex; gap:5px; flex-wrap:wrap;
  }}
  .mini-pill {{
    background:rgba(9,12,20,0.9); color:#e2e8f0; border:1px solid #475569;
    border-radius:6px; padding:3px 8px; font-size:11px; font-weight:750; cursor:pointer;
  }}
  .mini-pill.on {{ border-color:var(--gold); color:var(--gold); }}

  .card-body {{ padding:14px; display:flex; flex-direction:column; gap:9px; flex:1; }}
  .card-loc {{ font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; color:var(--cyan); }}
  .card-title {{ margin:0; font-size:16px; font-weight:850; color:#fff; }}
  .card-desc {{ margin:0; font-size:13px; color:#cbd5e1; flex:1; }}
  .tag-row {{ display:flex; flex-wrap:wrap; gap:5px; }}
  .tag {{
    font-size:11px; font-weight:700; padding:2px 7px; border-radius:6px;
    background:var(--panel2); border:1px solid #2d3d5e; color:#cbd5e1;
  }}
  .tag.wep {{ border-color:rgba(244,63,94,0.4); color:#fecdd3; background:rgba(244,63,94,0.1); }}
  .tag.veh {{ border-color:rgba(251,191,36,0.4); color:#fef08a; background:rgba(251,191,36,0.09); }}
  .tag.chr {{ border-color:rgba(74,222,128,0.4); color:#bbf7d0; background:rgba(74,222,128,0.09); }}

  .card-foot {{
    display:flex; flex-wrap:wrap; gap:6px; padding-top:8px; border-top:1px solid #1f2a44;
  }}
  .sm-btn {{
    background:var(--panel2); color:#e2e8f0; border:1px solid #334469;
    border-radius:7px; padding:6px 10px; font:inherit; font-size:11.5px; font-weight:750;
    cursor:pointer; transition:all 0.12s ease;
  }}
  .sm-btn:hover {{ border-color:var(--gold); color:var(--gold); }}

  .two-col {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(360px, 1fr)); gap:16px; }}
  .info-box {{
    background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:18px;
    display:flex; flex-direction:column; gap:10px;
  }}
  .info-box h3 {{ margin:0; font-size:17px; font-weight:850; color:var(--gold); }}
  .cast-list {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:6px;
    margin:0; padding:0; list-style:none;
  }}
  .cast-list li {{
    background:var(--panel2); border:1px solid #283654; border-radius:7px;
    padding:6px 9px; font-size:12px; color:#e2e8f0; font-weight:650;
  }}
  .tech-list {{ margin:0; padding-left:18px; display:flex; flex-direction:column; gap:8px; color:#cbd5e1; font-size:13px; }}
  .tech-list b {{ color:#fff; }}
  .tech-list code {{ background:#1d2842; color:#fde68a; padding:1px 5px; border-radius:4px; }}

  .lightbox {{
    position:fixed; inset:0; background:rgba(4,6,12,0.92); z-index:999;
    display:none; flex-direction:column; align-items:center; justify-content:center;
    padding:20px; gap:12px;
  }}
  .lightbox.open {{ display:flex; }}
  .lightbox img {{ max-width:96vw; max-height:82vh; border-radius:10px; border:1px solid var(--gold); }}
  .lightbox-bar {{ display:flex; align-items:center; gap:12px; color:#fff; font-weight:750; flex-wrap:wrap; justify-content:center; }}

  .hidden {{ display:none !important; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <div class="badges">
        <span class="badge gold">22.5s Tight Cut • Non-Stop Milky Song</span>
        <span class="badge cyan">0–6.6s: Up-Close 360° Fox (3+3)</span>
        <span class="badge pink">6.6–15.3s: 50 Sprites &amp; Milkys Spin &amp; Explode!</span>
        <span class="badge lime">15.3–22.5s: Burning Fox + CCCs + DAN &amp; ROB!</span>
      </div>
      <h1><span>BAKERSFIELD QUAKE</span> — Up-Close Sprite-Only Fox 360° → 50-Swarm Explosion → Burning Fox + Floating CCCs, DAN &amp; ROB</h1>
      <p class="sub">
        Punchy 22.5-second startup movie (<code>startdemos intro</code> on <code>maps/downtown.bsp</code>): <b>Milky Song playing the entire time</b>, strictly <b>Wheelman <code>.spr32</code> sprites only</b> (zero 3D Wheelman models), <b>up-close camera framing</b> across the 360° Fox orbit &amp; 50-entity Clock Tower explosion, culminating in the <b>Fox Theater on fire</b> as <b>24 yellow <code>CCCCCC</code>s + floating <code>DAN</code> &amp; <code>ROB</code></b> drift across the lens with <i>&ldquo;I&rsquo;m floating!&rdquo;</i> &amp; <i>&ldquo;Ah, I can&rsquo;t see!&rdquo;</i>
      </p>
    </div>
    <div class="actions">
      <a class="btn primary" id="dlPackBtn" href="https://bakersfield.larrywew.fun/intro-demo/bakersfield_intro_demo_pack.zip" download>⬇ Drop-In Quake Pack (.zip • {zip_mb:.1f} MB)</a>
      <a class="btn" id="dlMp4Btn" href="https://bakersfield.larrywew.fun/intro-demo/intro_demo_downtown.mp4" target="_blank" rel="noopener">🎬 Full 720p MP4 + Audio</a>
      <a class="btn" id="dlDemBtn" href="https://bakersfield.larrywew.fun/intro-demo/intro.dem" download>📼 Raw intro.dem ({dem_mb:.2f} MB)</a>
      <button class="btn" type="button" id="copyCmdBtn">📋 Copy <code>playdemo intro</code></button>
    </div>
  </header>

  <section class="stage-card">
    <div class="mode-tabs">
      <div class="tab-pair">
        <button class="btn active" type="button" id="tabVideoBtn">🎬 Full 720p HD Video (22.5s Up-Close Sprite Cut + Milky Song)</button>
        <button class="btn" type="button" id="tabStoryBtn">🖼 100% Self-Contained Offline 12-Shot Storyboard &amp; Audio</button>
      </div>
      <div class="now-playing" id="nowPlayingBanner">Act 01 (0:00–0:06) • Up-Close 360° Fox Theater — 3 Milkys + 3 Wheelman Sprites!</div>
    </div>

    <div class="viewport-wrap" id="videoWrap">
      <video id="heroVideo" controls playsinline preload="metadata"></video>
    </div>

    <div class="viewport-wrap hidden" id="storyWrap">
      <img id="storyImg" alt="Bakersfield Quake Fox 360 Swarm Frame">
      <div class="story-overlay">
        <div>
          <div class="story-cap-title" id="storyTitle"></div>
          <div class="story-cap-sub" id="storySub"></div>
        </div>
        <div class="story-controls">
          <button class="btn" type="button" id="prevShotBtn">◀ Prev</button>
          <button class="btn primary" type="button" id="autoPlayBtn">▶ Auto-Play Storyboard</button>
          <button class="btn" type="button" id="nextShotBtn">Next ▶</button>
          <button class="btn" type="button" id="storySfxBtn">🔊 Play Audio Clip</button>
          <button class="btn" type="button" id="zoomShotBtn">🔍 Fullscreen</button>
        </div>
      </div>
    </div>

    <div class="chapters-strip" id="chaptersStrip"></div>
  </section>

  <section class="soundboard">
    <div class="sec-hdr">
      <h2>🔊 Milky Song, 50-Sprite Explosion, &ldquo;I&rsquo;m Floating!&rdquo; &amp; &ldquo;Ah, I Can&rsquo;t See!&rdquo; Soundboard (Offline Base64 Audio)</h2>
      <span>Preview the non-stop Milky song, 50-sprite reveal &amp; explosion, floating cue, and CCC &ldquo;Ah, I can&rsquo;t see!&rdquo; line</span>
    </div>
    <div class="sfx-grid" id="sfxGrid"></div>
  </section>

  <section style="display:flex;flex-direction:column;gap:10px;">
    <div class="sec-hdr">
      <h2>🛞🥛🔥 All 4 Tight Acts: Up-Close 360° Fox → Close-Up 50 Spin → All 50 Explode → Burning Fox + Floating CCCs, DAN &amp; ROB</h2>
      <span>Click any card thumbnail to inspect in 1280×720 HD, switch camera angles, or jump the video player</span>
    </div>
    <div class="cards-grid" id="cardsGrid"></div>
  </section>

  <section class="two-col">
    <div class="info-box">
      <h3>🎭 Featured Sprites, Milkys, Fire &amp; Floating Finale Cast</h3>
      <ul class="cast-list" id="castList"></ul>
    </div>
    <div class="info-box">
      <h3>⚙ Up-Close Pure-Sprite Choreography &amp; Finale FX</h3>
      <ul class="tech-list">
        <li><b>Wheelman Sprites ONLY + Non-Stop Milky Song (0.0s – 22.5s):</b> Strictly <code>.spr32</code> Wheelman sprites (<code>wheelman.spr32</code>, <code>wheelman_historic.spr32</code>, <code>greensuit_wheelman.spr32</code>, <code>wheelman_dance.spr32</code> — zero 3D Wheelman, tire, axle, or dome MD3s!) while <code>milky/song.ogg</code> plays continuously from start to finish.</li>
        <li><b>3× Closer Camera Framing (0.0s – 15.3s):</b> Act 1 locks 3 Milkys + 3 Wheelman sprites at <code>~195u</code> right in front of the lens (<code>~205–255 px</code> tall) during a fast 6.6s 360° Fox orbit; Acts 2–3 move the camera right up to <code>~417u</code> from the 50-entity Clock Tower rings so every sprite &amp; 360° fireball fills the screen with zero letterbox clipping!</li>
        <li><b>Blazing Fox + Floating <code>CCCCCC</code>s, <code>DAN</code> &amp; <code>ROB</code> (15.3s – 22.5s):</b> 28 additive fire &amp; black smoke columns engulf the Fox Marquee, <code>FOX</code> sign &amp; Clock Tower while 24 spinning yellow <code>progs/ccc.md3</code> letters orbit floating <code>DAN</code> (<code>daniel.spr32</code>) &amp; <code>ROB</code> (<code>fr_rob.spr32</code>) as <code>jetpack/floating.wav</code> (<i>&ldquo;I&rsquo;m floating!&rdquo;</i>) and <code>ccc/shoot.wav</code> (<i>&ldquo;Ah, I can&rsquo;t see!&rdquo;</i>) ring out!</li>
        <li><b>All Cuts Preserved &amp; Live <code>progs.dat</code> Untouched:</b> <code>csprogs.dat</code> supports this new 22.5s cut (<code>cards 201..204</code>), v1 36s Fox 360 (<code>intro_fox360_v1.dem</code>, <code>101..105</code>), and the 90s Downtown Tour (<code>intro_downtown_tour.dem</code>, <code>1..20</code>) without modifying <code>progs.dat</code>.</li>
      </ul>
    </div>
  </section>
</div>

<div class="lightbox" id="lightbox">
  <img id="lbImg" alt="HD Frame">
  <div class="lightbox-bar">
    <button class="btn" type="button" id="lbPrev">◀ Prev</button>
    <span id="lbCaption"></span>
    <button class="btn" type="button" id="lbNext">Next ▶</button>
    <button class="btn primary" type="button" id="lbClose">✕ Close (Esc)</button>
  </div>
</div>

<script>
const DATA = {data_json};

const video = document.getElementById('heroVideo');
const videoWrap = document.getElementById('videoWrap');
const storyWrap = document.getElementById('storyWrap');
const tabVideoBtn = document.getElementById('tabVideoBtn');
const tabStoryBtn = document.getElementById('tabStoryBtn');
const nowPlayingBanner = document.getElementById('nowPlayingBanner');
const chaptersStrip = document.getElementById('chaptersStrip');
const sfxGrid = document.getElementById('sfxGrid');
const cardsGrid = document.getElementById('cardsGrid');
const castList = document.getElementById('castList');

const REMOTE_BASE = 'https://bakersfield.larrywew.fun/intro-demo/';
const isIntroSubdir = location.pathname.includes('/intro-demo/');
const assetBase = isIntroSubdir ? './' : REMOTE_BASE;

document.getElementById('dlPackBtn').href = assetBase + 'bakersfield_intro_demo_pack.zip';
document.getElementById('dlMp4Btn').href = assetBase + 'intro_demo_downtown.mp4';
document.getElementById('dlDemBtn').href = assetBase + 'intro.dem';

video.poster = DATA.shots[10].src;
video.src = assetBase + 'intro_demo_downtown.mp4';
video.addEventListener('error', () => {{
  if (video.src !== REMOTE_BASE + 'intro_demo_downtown.mp4') {{
    video.src = REMOTE_BASE + 'intro_demo_downtown.mp4';
  }} else {{
    setMode('story');
  }}
}});

let mode = 'video';
let curShot = 0;
let curCardIdx = 0;
let autoTimer = null;
let activeAudio = null;
let activeSfxBtn = null;

function fmtTime(sec) {{
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return m + ':' + String(s).padStart(2, '0');
}}

function playCardSfx(cardIdx, btnEl) {{
  const c = DATA.cards[cardIdx];
  if (!c) return;
  if (activeAudio) {{
    activeAudio.pause();
    activeAudio = null;
  }}
  if (activeSfxBtn) activeSfxBtn.classList.remove('playing');
  const a = new Audio(c.sfx_uri);
  activeAudio = a;
  if (btnEl) {{
    activeSfxBtn = btnEl;
    btnEl.classList.add('playing');
  }}
  a.onended = () => {{
    if (activeSfxBtn === btnEl && btnEl) btnEl.classList.remove('playing');
  }};
  a.play().catch(() => {{}});
}}

function setMode(m) {{
  mode = m;
  if (m === 'video') {{
    stopAutoPlay();
    videoWrap.classList.remove('hidden');
    storyWrap.classList.add('hidden');
    tabVideoBtn.classList.add('active');
    tabStoryBtn.classList.remove('active');
  }} else {{
    video.pause();
    videoWrap.classList.add('hidden');
    storyWrap.classList.remove('hidden');
    tabVideoBtn.classList.remove('active');
    tabStoryBtn.classList.add('active');
    renderStoryShot(curShot);
  }}
}}

tabVideoBtn.onclick = () => setMode('video');
tabStoryBtn.onclick = () => setMode('story');

function highlightChapter(cardIdx) {{
  curCardIdx = cardIdx;
  const c = DATA.cards[cardIdx];
  if (c) {{
    nowPlayingBanner.textContent = `Act ${{String(c.card).padStart(2,'0')}} (${{fmtTime(c.t0)}}–${{fmtTime(c.t1)}}) • ${{c.landmark}} — ${{c.title}}`;
  }}
  document.querySelectorAll('.chap-btn').forEach((b, i) => {{
    b.classList.toggle('on', i === cardIdx);
  }});
}}

function renderStoryShot(idx) {{
  curShot = (idx + DATA.shots.length) % DATA.shots.length;
  const sh = DATA.shots[curShot];
  const cardIdx = sh.card - 1;
  const c = DATA.cards[cardIdx];
  document.getElementById('storyImg').src = sh.src;
  document.getElementById('storyTitle').textContent = sh.caption;
  document.getElementById('storySub').textContent = `${{c.landmark}}  •  Demo Time ${{sh.t.toFixed(1)}}s ( Shot ${{curShot + 1}} / ${{DATA.shots.length}} )`;
  highlightChapter(cardIdx);
}}

function stopAutoPlay() {{
  if (autoTimer) {{
    clearInterval(autoTimer);
    autoTimer = null;
  }}
  document.getElementById('autoPlayBtn').textContent = '▶ Auto-Play Storyboard';
}}

document.getElementById('prevShotBtn').onclick = () => {{ stopAutoPlay(); renderStoryShot(curShot - 1); }};
document.getElementById('nextShotBtn').onclick = () => {{ stopAutoPlay(); renderStoryShot(curShot + 1); }};
document.getElementById('storySfxBtn').onclick = (e) => playCardSfx(curCardIdx, e.currentTarget);
document.getElementById('autoPlayBtn').onclick = () => {{
  if (autoTimer) {{
    stopAutoPlay();
  }} else {{
    playCardSfx(curCardIdx, null);
    document.getElementById('autoPlayBtn').textContent = '⏸ Pause Storyboard';
    autoTimer = setInterval(() => {{
      const prevCard = curCardIdx;
      renderStoryShot(curShot + 1);
      if (curCardIdx !== prevCard) playCardSfx(curCardIdx, null);
    }}, 3200);
  }}
}};

DATA.cards.forEach((c, idx) => {{
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'chap-btn' + (idx === 0 ? ' on' : '') + ((c.card === 3 || c.card === 4) ? ' milky' : '');
  b.innerHTML = `<span>${{c.short}}</span><span class="chap-time">${{fmtTime(c.t0)}}</span>`;
  b.onclick = () => {{
    highlightChapter(idx);
    if (mode === 'video') {{
      video.currentTime = c.t0 + 0.08;
      video.play().catch(() => {{}});
    }} else {{
      stopAutoPlay();
      renderStoryShot(c.shots[0]);
      playCardSfx(idx, null);
    }}
  }};
  chaptersStrip.appendChild(b);
}});

video.addEventListener('timeupdate', () => {{
  const t = video.currentTime;
  for (let i = DATA.cards.length - 1; i >= 0; i--) {{
    if (t >= DATA.cards[i].t0) {{
      if (curCardIdx !== i) highlightChapter(i);
      break;
    }}
  }}
}});

DATA.cards.forEach((c, idx) => {{
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'sfx-btn';
  b.innerHTML = `<span>${{c.sfx_label}}</span><span style="color:#94a3b8;font-size:11px">Act ${{String(c.card).padStart(2,'0')}}</span>`;
  b.onclick = () => playCardSfx(idx, b);
  sfxGrid.appendChild(b);
}});
(DATA.extraSfx || []).forEach((ex) => {{
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'sfx-btn';
  b.innerHTML = `<span>${{ex.label}}</span><span style="color:#94a3b8;font-size:11px">${{ex.badge}}</span>`;
  b.onclick = () => {{
    if (activeAudio) {{ activeAudio.pause(); activeAudio = null; }}
    if (activeSfxBtn) activeSfxBtn.classList.remove('playing');
    const a = new Audio(ex.uri);
    activeAudio = a;
    activeSfxBtn = b;
    b.classList.add('playing');
    a.onended = () => {{ if (activeSfxBtn === b) b.classList.remove('playing'); }};
    a.play().catch(() => {{}});
  }};
  sfxGrid.appendChild(b);
}});

DATA.cards.forEach((c, idx) => {{
  const el = document.createElement('article');
  el.className = 'landmark-card' + ((c.card === 3 || c.card === 4) ? ' milky-highlight' : '');
  let activeLocalShot = c.shots[0];

  const switchHtml = c.shots.length > 1
    ? `<div class="shot-switch">${{c.shots.map((sIdx, k) =>
        `<button type="button" class="mini-pill ${{k===0?'on':''}}" data-sidx="${{sIdx}}">Angle ${{k+1}}</button>`
      ).join('')}}</div>`
    : '';

  const tagsHtml = [
    ...c.weapons.map(w => `<span class="tag wep">🎬 ${{w}}</span>`),
    ...c.vehicles.map(v => `<span class="tag veh">🏛 ${{v}}</span>`),
    ...c.chars.map(ch => `<span class="tag chr">✨ ${{ch}}</span>`),
  ].join('');

  el.innerHTML = `
    <div class="card-thumb-wrap">
      <img src="${{DATA.shots[activeLocalShot].src}}" alt="${{c.title}}">
      <span class="card-num-pill">ACT ${{String(c.card).padStart(2,'0')}}</span>
      <span class="card-time-pill">${{c.t0.toFixed(1)}}s – ${{c.t1.toFixed(1)}}s</span>
      ${{switchHtml}}
    </div>
    <div class="card-body">
      <div class="card-loc">${{c.landmark}}</div>
      <h3 class="card-title">${{c.title}}</h3>
      <p class="card-desc">${{c.desc}}</p>
      <div class="tag-row">${{tagsHtml}}</div>
      <div class="card-foot">
        <button type="button" class="sm-btn seek-btn">▶ Jump Video (${{fmtTime(c.t0)}})</button>
        <button type="button" class="sm-btn sfx-trig">🔊 Hear Clip</button>
        <button type="button" class="sm-btn zoom-trig">🔍 720p HD</button>
      </div>
    </div>
  `;

  const imgEl = el.querySelector('img');
  el.querySelectorAll('.mini-pill').forEach(pb => {{
    pb.onclick = (ev) => {{
      ev.stopPropagation();
      activeLocalShot = Number(pb.dataset.sidx);
      imgEl.src = DATA.shots[activeLocalShot].src;
      el.querySelectorAll('.mini-pill').forEach(x => x.classList.toggle('on', x === pb));
    }};
  }});
  imgEl.onclick = () => openLightbox(activeLocalShot);
  el.querySelector('.zoom-trig').onclick = () => openLightbox(activeLocalShot);
  el.querySelector('.sfx-trig').onclick = (ev) => playCardSfx(idx, ev.currentTarget);
  el.querySelector('.seek-btn').onclick = () => {{
    setMode('video');
    highlightChapter(idx);
    video.currentTime = c.t0 + 0.08;
    video.play().catch(() => {{}});
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }};
  cardsGrid.appendChild(el);
}});

DATA.castList.forEach(item => {{
  const li = document.createElement('li');
  li.textContent = item;
  castList.appendChild(li);
}});

const lb = document.getElementById('lightbox');
let lbIdx = 0;
function openLightbox(sIdx) {{
  lbIdx = (sIdx + DATA.shots.length) % DATA.shots.length;
  document.getElementById('lbImg').src = DATA.shots[lbIdx].src;
  document.getElementById('lbCaption').textContent = DATA.shots[lbIdx].caption;
  lb.classList.add('open');
}}
document.getElementById('zoomShotBtn').onclick = () => openLightbox(curShot);
document.getElementById('lbPrev').onclick = () => openLightbox(lbIdx - 1);
document.getElementById('lbNext').onclick = () => openLightbox(lbIdx + 1);
document.getElementById('lbClose').onclick = () => lb.classList.remove('open');
lb.onclick = (e) => {{ if (e.target === lb) lb.classList.remove('open'); }};

window.addEventListener('keydown', (e) => {{
  if (lb.classList.contains('open')) {{
    if (e.key === 'Escape') lb.classList.remove('open');
    if (e.key === 'ArrowLeft') openLightbox(lbIdx - 1);
    if (e.key === 'ArrowRight') openLightbox(lbIdx + 1);
    return;
  }}
  if (mode === 'story') {{
    if (e.key === 'ArrowLeft') {{ stopAutoPlay(); renderStoryShot(curShot - 1); }}
    if (e.key === 'ArrowRight') {{ stopAutoPlay(); renderStoryShot(curShot + 1); }}
  }}
}});

document.getElementById('copyCmdBtn').onclick = (e) => {{
  navigator.clipboard.writeText('playdemo intro');
  const b = e.currentTarget;
  const old = b.innerHTML;
  b.textContent = '✓ Copied: playdemo intro';
  setTimeout(() => {{ b.innerHTML = old; }}, 1600);
}});

renderStoryShot(0);
</script>
</body>
</html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote self-contained HTML showcase: {OUT_HTML} ({os.path.getsize(OUT_HTML) / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
