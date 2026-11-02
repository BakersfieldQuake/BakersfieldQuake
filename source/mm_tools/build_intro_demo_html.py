r"""Builds the 100% Self-Contained Interactive HTML Showcase & Drop-In Pack for
Bakersfield Quake's `bklan5` Startup Demo (`intro.dem`):
  - G:\Quake\Combat\BakersfieldQuake\bakersfield_intro_demo.html
  - G:\Quake\Combat\BakersfieldQuake\source\mm_tools\out\bakersfield_intro_demo_pack.zip
"""
import base64
import io
import json
import os
import subprocess
import tempfile
import zipfile
from PIL import Image

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
    ("zz_shot_01_sign_white_van.png", 1, 2.8, "Card 01 • Bakersfield Sign — Solo White LAN Van Idling & Honking"),
    ("zz_shot_02_sign_all_chars.png", 2, 8.5, "Card 02 • Bakersfield Sign — All 19 Custom Characters Pile Out of the Van!"),
    ("zz_shot_03_fox_marquee_robdob.png", 3, 13.6, "Card 03 • Historic Fox Theater Marquee — Rob Dob Launcher & 'It's Not Pink!' Supercar"),
    ("zz_shot_04_fox_lounge_pickle.png", 4, 18.8, "Card 04 • Fox Theater Eva's Lounge & Live TV — Giant Diva Pickle Between Dennis & Paul"),
    ("zz_shot_05_fox_stage_wewcannon.png", 5, 23.8, "Card 05A • Fox Sunburst Stage — +58° Elastic Silver WewCannon Charge & Launch"),
    ("zz_shot_06_fox_stage_milky_drips.png", 5, 26.8, "Card 05B • Fox Sunburst Stage — Opera Milky & Full-Screen Milk Splash Drips"),
    ("zz_shot_07_padre_jetpack_float.png", 6, 30.2, "Card 06 • The Padre Hotel — Twin-Flame Jetpack 8-Story Ascent ('I'm Floating!!')"),
    ("zz_shot_08_padre_roof_spanner_sentry.png", 7, 34.0, "Card 07A • Padre 96-ft Neon Rooftop — Spanner Wrench & TF Level-2 Twin Sentry"),
    ("zz_shot_09_padre_roof_sniper_kyle.png", 7, 36.2, "Card 07B • Padre 96-ft Neon Rooftop — Sniper Laser & 'C' Bolts vs. Kyle Running With Scissors"),
    ("zz_shot_10_larry_wh_bonk_hammer.png", 8, 39.8, "Card 08 • Larry's Warehouse (118/120 E 21st St) — Bonk Hammer *CLANG!* Launches Mr. DIY"),
    ("zz_shot_11_blan130a_netsend.png", 9, 44.3, "Card 09A • B-LAN 130A CRT Party Hall — NetSend 3.5\" Floppy & Crashing PC ('It Won't Boot!!')"),
    ("zz_shot_12_blan130a_laptop_gun.png", 9, 46.8, "Card 09B • B-LAN 130A CRT Party Hall — 3D Laptop Gun & Floating Head Drone Zapping Friend Rob"),
    ("zz_shot_13_larry120a_mm_rag_polish.png", 10, 49.4, "Card 10A • Larry's 120A Mega Man Shrine — CoD Red-Rag Chrome Polish (*DING!*)"),
    ("zz_shot_14_larry120a_megaman_bed.png", 10, 51.8, "Card 10B • Larry's 120A Mega Man Shrine — Slingshot & Wheel-Driving 3D Mega Man Over His Bed"),
    ("zz_shot_15_orcom_googun_bigears.png", 11, 55.6, "Card 11 • ORCOM Connect Hall — Goo Gun Foam Mounds, Pong Balls, Giant Big-Ears & Rubber Finger"),
    ("zz_shot_16_casino_david_777.png", 12, 60.5, "Card 12 • Golden West Casino — David Ojeda's 777 Money-Bag Jackpot, Pregnant Trio & Golden Horse"),
    ("zz_shot_17_crystal_mbox_bryan.png", 13, 65.8, "Card 13 • Buck Owens' Crystal Palace & KUZZ Van — Mystery Box, Bryan ('NO WAY!') & Hell Demons"),
    ("zz_shot_18_park_johnwave_trashcan.png", 14, 70.6, "Card 14 • Amberton Park Shelter — JohnWave Head Grenade, Wheelie Riders & NASA Rocket Trash Can"),
    ("zz_shot_19_finale_white_van_sign.png", 15, 75.5, "Card 15 • Bakersfield Sign Finale — Open White LAN Van, Pink Supercar & Full-Circle Send-Off"),
]


CARDS_DATA = [
    {
        "card": 1,
        "t0": 0.0,
        "t1": 4.4,
        "short": "01 • White Van Cold Open",
        "landmark": "Bakersfield Sign // Sillect Ave",
        "title": "Solo White LAN Van Idling & Honking",
        "desc": "Opens right under the iconic yellow BAKERSFIELD arch on Sillect Ave showing ONLY the White LAN Van (veh_van.md3) rocking on its suspension, idling, and honking twice before chaos erupts.",
        "weapons": ["Cinema Cold Open"],
        "vehicles": ["White LAN Van (veh_van.md3)"],
        "chars": ["Driver Honking Inside"],
        "sfx_path": "sound/vehicles/horn.wav",
        "sfx_label": "🚐 Van Horn (horn.wav)",
        "shots": [0],
    },
    {
        "card": 2,
        "t0": 4.4,
        "t1": 11.4,
        "short": "02 • All 19 Chars Pile Out!",
        "landmark": "Bakersfield Sign // Sillect Ave",
        "title": "Wait... Everybody's in the White Van?!",
        "desc": "The rear doors burst open (veh_van_open.md3) with a Stunt-Dancer Wheelman dancing on the roof while ALL 19 custom characters pour out across Sillect Ave, calling out signature voice lines spaced ~0.74s apart so zero voices muddle together.",
        "weapons": ["Full-Cast Roll Call"],
        "vehicles": ["Open-Door White Van", "JessKart"],
        "chars": ["All 19 Custom Characters", "Roof-Dancing Wheelman"],
        "sfx_path": "sound/friends/gowewd.wav",
        "sfx_label": "🗣 Cast Callout (gowewd.wav)",
        "shots": [1],
    },
    {
        "card": 3,
        "t0": 11.4,
        "t1": 16.4,
        "short": "03 • Fox Marquee & Rob Dob",
        "landmark": "Historic Fox Theater // Marquee & Clock Tower",
        "title": "Rob Dob Head Launcher & 'It's Not Pink!' Supercar",
        "desc": "Under the glowing FOX Bakersfield marquee and clock tower, v_robdob.mdl fires a giant spinning Fedora Rob Dob head surrounded by bouncing mini-Dobs as the gullwing 'It's Not Pink!' supercar drifts below a flying Podracer Van & Drone.",
        "weapons": ["v_robdob.mdl (Rob Dob Launcher)"],
        "vehicles": ["'It's Not Pink!' Supercar", "Sky Podracer Van", "Flying Drone"],
        "chars": ["Rob Dob (Fedora Head)", "Mini-Dobs"],
        "sfx_path": "sound/bklan/notpink.wav",
        "sfx_label": "🏎 'It's Not Pink!' (notpink.wav)",
        "shots": [2],
    },
    {
        "card": 4,
        "t0": 16.4,
        "t1": 21.4,
        "short": "04 • Eva's Lounge & Pickle",
        "landmark": "Fox Theater Interior // Eva's Lounge & Live TV",
        "title": "Giant Screaming Diva Pickle Surprise",
        "desc": "Inside Eva's Lounge with bk_tv actively playing live footage on the wall, v_pickle.md3 lobs a Pickle Bomb between Dennis and Paul that sprouts into a 2x-man-height screaming Diva Pickle, swells red-hot, and explodes into 12 flying pickle gibs!",
        "weapons": ["v_pickle.md3 (Pickle Surprise)"],
        "vehicles": ["Live Lounge TV (bk_tv)"],
        "chars": ["Dennis", "Paul", "Giant Diva Pickle"],
        "sfx_path": "sound/pickle/surprise.wav",
        "sfx_label": "🥒 Pickle Surprise! (surprise.wav)",
        "shots": [3],
    },
    {
        "card": 5,
        "t0": 21.4,
        "t1": 27.0,
        "short": "05 • Fox Stage: Wew & Milky",
        "landmark": "Fox Theater Auditorium // Golden Sunburst Stage",
        "title": "+58° WewCannon Blast & Opera Milky Screen Splash",
        "desc": "v_wewcannon.md3 bends upward +58° with belly-swell charge and blasts a screaming Stunt-Dancer Wheelman onto the sunburst stage, followed by v_milky.md3 summoning singing Opera Pink Lady who splashes creamy gfx/milkdrips right onto the camera lens!",
        "weapons": ["v_wewcannon.md3 (WewCannon)", "v_milky.md3 (Milky Gun)"],
        "vehicles": ["Sunburst Stage"],
        "chars": ["Stunt-Dancer Wheelman", "Opera Pink Lady (Milky)"],
        "sfx_path": "sound/milky/song.ogg",
        "sfx_label": "🥛 Opera Milky Aria (song.ogg)",
        "shots": [4, 5],
    },
    {
        "card": 6,
        "t0": 27.0,
        "t1": 32.0,
        "short": "06 • Padre Hotel Jetpack",
        "landmark": "The Padre Hotel // 8-Story Historic Tower",
        "title": "Twin-Flame Jetpack Skyline Ascent",
        "desc": "With the custom orange glass CSQC JET fuel gauge burning down on HUD, QuakeGuy and Ranger ignite twin jetpack.md3 exhaust flames ('I'm floating!!') and rocket all 8 stories up the historic Padre Hotel facade.",
        "weapons": ["jetpack.md3 + CSQC JET Gauge"],
        "vehicles": ["Twin-Nozzle Jetpack"],
        "chars": ["QuakeGuy", "Jetpack Ranger"],
        "sfx_path": "sound/jetpack/floating.wav",
        "sfx_label": "🚀 'I'm Floating!!' (floating.wav)",
        "shots": [6],
    },
    {
        "card": 7,
        "t0": 32.0,
        "t1": 37.0,
        "short": "07 • Padre Roof Sentry & Sniper",
        "landmark": "The Padre Hotel // 96-ft Neon Rooftop Sign",
        "title": "Spanner, TF Level-2 Sentry, Sniper Laser & 'C' Bolts",
        "desc": "Atop the 96-ft skyline roof between the giant red PADRE HOTEL neon signs, v_span.mdl deploys a twin-chaingun TF Level-2 Sentry while v_srifle.mdl paints a red laser dot and fires rapid-fire 'C' bolts (ccc.md3) chasing Kyle Running With Scissors!",
        "weapons": ["v_span.mdl (Spanner)", "TF Level-2 Sentry", "v_srifle.mdl (Sniper)", "ccc.md3 ('C' Bolts)"],
        "vehicles": ["Turret Platform"],
        "chars": ["Kyle Running With Scissors"],
        "sfx_path": "sound/weapons/sniper.wav",
        "sfx_label": "🎯 Sniper Crack (sniper.wav)",
        "shots": [7, 8],
    },
    {
        "card": 8,
        "t0": 37.0,
        "t1": 42.0,
        "short": "08 • Larry's WH Bonk Hammer",
        "landmark": "Larry's Warehouse (118/120 E 21st St) // Pallet & TV Hall",
        "title": "The Bonk Hammer (Frying-Pan Edition) vs. Mr. DIY",
        "desc": "Inside Larry's iconic warehouse hall in front of the live wall TV and orange forklift, v_hammer.mdl performs its inspect twirl, charges to maximum glow, and slams down with an ear-ringing *CLANG!* sending Mr. DIY and his burst of hammers, screwdrivers & coins flying!",
        "weapons": ["v_hammer.mdl (Bonk Hammer)"],
        "vehicles": ["Orange Warehouse Forklift"],
        "chars": ["Mr. DIY (+ Flying Tool Burst)"],
        "sfx_path": "sound/hammer/frying_pan.wav",
        "sfx_label": "🔨 Frying-Pan *CLANG!* (frying_pan.wav)",
        "shots": [9],
    },
    {
        "card": 9,
        "t0": 42.0,
        "t1": 47.4,
        "short": "09 • B-LAN 130A NetSend & Laptop",
        "landmark": "Larry's Warehouse // B-LAN 130A CRT Party Hall",
        "title": "NetSend 3.5\" Floppy PC & 3D Laptop Gun",
        "desc": "Among rows of beige CRT LAN rigs, v_netsend.md3 hurls a LOL.BAT floppy disk that materializes a crashing desktop PC ('It won't boot!!'), then swaps to ltg_v3d.md3 frantic two-hand keyboard hacking as the giant Floating Head Drone zaps Friend Rob!",
        "weapons": ["v_netsend.md3 (NetSend Floppy)", "ltg_v3d.md3 (3D Laptop Gun)"],
        "vehicles": ["ltg_head.md3 Floating Head Drone"],
        "chars": ["Friend Rob ('M'LADY')"],
        "sfx_path": "sound/larry/it_wont_boot.wav",
        "sfx_label": "💾 'It Won't Boot!!' (it_wont_boot.wav)",
        "shots": [10, 11],
    },
    {
        "card": 10,
        "t0": 47.4,
        "t1": 52.8,
        "short": "10 • Larry's 120A MegaMan Shrine",
        "landmark": "Larry's 120A Bedroom // Official Mega Man Shrine",
        "title": "CoD Red-Rag Chrome Polish, Slingshot & Wheel Mega Man",
        "desc": "Inside Larry's Mega Man bedroom shrine, v_mm_cannon.md3 triggers its Call-of-Duty red shop-rag inspect polish with a *DING!* chrome sparkle, swaps to v_mm_slingshot.md3, and launches wheel-driving 3D Mega Man over his own bed into a giant mm_explode dome!",
        "weapons": ["v_mm_cannon.md3 (CoD Rag Polish)", "v_mm_slingshot.md3 (Slingshot)"],
        "vehicles": ["Outboard Wheel-Drive Rig"],
        "chars": ["3D Mega Man"],
        "sfx_path": "sound/weapons/megahorn.wav",
        "sfx_label": "🤖 Mega Horn! (megahorn.wav)",
        "shots": [12, 13],
    },
    {
        "card": 11,
        "t0": 52.8,
        "t1": 57.8,
        "short": "11 • ORCOM Goo Gun & Pong",
        "landmark": "ORCOM Connect // Banquet LAN Tables",
        "title": "Expanding Goo Foam Mounds & Ricochet Pong Balls",
        "desc": "Across the ORCOM Connect banquet hall, v_googun.md3 sprays flanking expanding polyurethane foam mounds (goo.md3) while glowing FunGun Pong Balls (fg_pongball.md3) ricochet around Giant 3D Big-Ears and Giant Rubber Finger!",
        "weapons": ["v_googun.md3 (Goo Gun)", "fg_pongball.md3 (FunGun Pong)"],
        "vehicles": ["ORCOM Banquet Hall"],
        "chars": ["Giant 3D Big-Ears", "Giant Rubber Finger"],
        "sfx_path": "sound/weapons/goosplat.wav",
        "sfx_label": "🧪 Goo Splat! (goosplat.wav)",
        "shots": [14],
    },
    {
        "card": 12,
        "t0": 57.8,
        "t1": 62.8,
        "short": "12 • Casino 777 & Golden Horse",
        "landmark": "Golden West Casino // Giant Golden Horse Plaza",
        "title": "David Ojeda's 777 Money-Bag Jackpot & Pregnant Trio",
        "desc": "Out on the sunlit Golden West Casino plaza beneath the prancing golden horses, David Ojeda hits a 777 slot-machine payday and sprints off clutching his '$' money bag alongside all three Pregnant Sprinters!",
        "weapons": ["777 Slot Jackpot Mechanic"],
        "vehicles": ["Prancing Golden Casino Horse"],
        "chars": ["David Ojeda ($ Money Bag)", "Pregnant Sprinter Trio"],
        "sfx_path": "sound/david/slot_jackpot.wav",
        "sfx_label": "🎰 777 Jackpot! (slot_jackpot.wav)",
        "shots": [15],
    },
    {
        "card": 13,
        "t0": 62.8,
        "t1": 68.2,
        "short": "13 • Crystal Palace Mystery Box",
        "landmark": "Buck Owens' Crystal Palace // KUZZ Radio Van",
        "title": "Mystery Box, Tinfoil-Hat Bryan & Hell Pentagram",
        "desc": "Beside Buck Owens' neon guitar marquee and the parked KUZZ Radio Van, v_mysterybox.md3 tosses a spinning '?' cube that summons Tinfoil-Hat Bryan ('NO WAY!') and rips open a glowing Hell Pentagram Vortex with three Red Demons!",
        "weapons": ["v_mysterybox.md3 (Mystery Box)"],
        "vehicles": ["KUZZ Radio Broadcast Van"],
        "chars": ["Tinfoil-Hat Bryan", "3 Red Hell-Portal Demons"],
        "sfx_path": "sound/bryan/noway.wav",
        "sfx_label": "🛸 Bryan 'NO WAY!' (noway.wav)",
        "shots": [16],
    },
    {
        "card": 14,
        "t0": 68.2,
        "t1": 73.0,
        "short": "14 • Park JohnWave & Rocket Can",
        "landmark": "Amberton Park // Picnic Shelter & Playground",
        "title": "JohnWave Head Grenade & NASA Rocket Trash Can",
        "desc": "Under the Amberton Park picnic shelter, a rubber-ball bouncing JohnWave Head Grenade (johnhead3d.md3) unleashes a tidal wave ring past Suit & Squat Wheelie Riders while a giant green TRASH can ignites and blasts off into orbit!",
        "weapons": ["JohnWave Head Grenade (jw_wave.md3)"],
        "vehicles": ["NASA Rocket Trash Can (trashcan.md3)"],
        "chars": ["Suit Wheelie Rider", "Squat Wheelie Rider"],
        "sfx_path": "sound/john/jv15.wav",
        "sfx_label": "🌊 JohnWave Callout (jv15.wav)",
        "shots": [17],
    },
    {
        "card": 15,
        "t0": 73.0,
        "t1": 76.0,
        "short": "15 • Bakersfield Sign Finale",
        "landmark": "Bakersfield Sign // Sillect Ave — Tour Complete!",
        "title": "Full-Circle Send-Off Under the Bakersfield Arch",
        "desc": "Returns full-circle under the yellow BAKERSFIELD Sign with the open-door White LAN Van, 'It's Not Pink!' gullwing supercar, JessKart, Orange Forklift, roof-dancing Wheelman, and the crew waving you into the menu to start fragging!",
        "weapons": ["Seamless Loop Back to 0:00"],
        "vehicles": ["Open White Van", "'It's Not Pink!' Supercar", "JessKart", "Orange Forklift"],
        "chars": ["Full Bakersfield LAN Crew"],
        "sfx_path": "sound/vehicles/lanvan.wav",
        "sfx_label": "🏁 LAN Van Finale (lanvan.wav)",
        "shots": [18],
    },
]


ALL_19_CHARS = [
    "1. Naked Wheelman (wheelman.spr32)",
    "2. Stunt-Dancer Wheelman (wheelman_dance.spr32)",
    "3. 3D Wheel-Drive Mega Man (megaman.md3)",
    "4. Suit Wheelie Rider (mm_suit_rider.md3)",
    "5. Squat Wheelie Rider (mm_squat_rider.md3)",
    "6. Giant 3D Wheelie Big-Ears (bigears.md3)",
    "7. Opera Pink Lady / Milky (pinklady.md3)",
    "8. Fedora Rob Dob (floathead.mdl)",
    "9. Giant Screaming Diva Pickle (pickle.md3)",
    "10. David Ojeda w/ $ Money Bag (david.spr32)",
    "11. Tinfoil-Hat Bryan (bryan.spr32)",
    "12. JessKart Racer (jesskart.spr32)",
    "13. Dennis (fr_dennis.spr32)",
    "14. Paul (fr_paul.spr32)",
    "15. Mr. DIY + Flying Tools (fr_mrdiy.spr32)",
    "16. Kyle Running With Scissors (fr_scissors.spr32)",
    "17. Friend Rob 'M'LADY' (fr_rob.spr32)",
    "18. Classic QuakeGuy Sprite (fr_quakeguy.spr32)",
    "19. Giant Rubber Finger & Pregnant Trio (fr_finger / preg_1..3)",
]


def encode_shot_b64(fname: str, width: int = 1280, quality: int = 87) -> str:
    p = os.path.join(SHOTS_DIR, fname)
    im = Image.open(p).convert("RGB")
    if im.width != width:
        h = int(round(im.height * (width / float(im.width))))
        im = im.resize((width, h), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


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
                "-t", "3.8",
                "-ac", "1", "-ar", "24000", "-b:a", "56k",
                dst,
            ],
            check=True,
        )
        mp3_bytes = open(dst, "rb").read()
    return "data:audio/mpeg;base64," + base64.b64encode(mp3_bytes).decode("ascii")


def build_drop_in_zip() -> int:
    files_to_pack = [
        (os.path.join(MOD_ROOT, "intro.dem"), "BakersfieldQuake/intro.dem"),
        (os.path.join(MOD_ROOT, "csprogs.dat"), "BakersfieldQuake/csprogs.dat"),
        (os.path.join(MOD_ROOT, "quake.rc"), "BakersfieldQuake/quake.rc"),
        (os.path.join(HERE, "intro_director.qc"), "BakersfieldQuake/source/mm_tools/intro_director.qc"),
        (os.path.join(HERE, "build_intro_demo.py"), "BakersfieldQuake/source/mm_tools/build_intro_demo.py"),
        (os.path.join(MOD_ROOT, "source", "qc_combat_decomp", "csqc", "bm_hud.qc"), "BakersfieldQuake/source/qc_combat_decomp/csqc/bm_hud.qc"),
    ]
    os.makedirs(OUT_DIR, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc in files_to_pack:
            zf.write(src, arc)
    return os.path.getsize(OUT_ZIP)


def main() -> None:
    print("Packing drop-in zip...")
    zip_bytes = build_drop_in_zip()
    print(f"  -> {OUT_ZIP} ({zip_bytes / (1024*1024):.2f} MB)")

    print("Encoding 19 HD 1280x720 screenshots as embedded base64...")
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

    print("Encoding 15 signature Quake sound clips as embedded base64 MP3...")
    zf_pk3 = zipfile.ZipFile(PK3_PATH, "r")
    zf_pak0 = zipfile.ZipFile(PAK0_PATH, "r") if os.path.isfile(PAK0_PATH) else None
    cards_payload = []
    for c in CARDS_DATA:
        sfx_uri = encode_sfx_mp3_b64(zf_pk3, zf_pak0, c["sfx_path"])
        c_out = dict(c)
        c_out["sfx_uri"] = sfx_uri
        cards_payload.append(c_out)
    zf_pk3.close()
    if zf_pak0:
        zf_pak0.close()

    dem_mb = os.path.getsize(os.path.join(MOD_ROOT, "intro.dem")) / (1024 * 1024)
    zip_mb = zip_bytes / (1024 * 1024)

    data_json = json.dumps({
        "shots": shots_payload,
        "cards": cards_payload,
        "cast19": ALL_19_CHARS,
    })

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bakersfield Quake — bklan5 Startup Demo (intro.dem) Interactive Showcase</title>
<style>
  :root {{
    --bg:#090c14; --panel:#111726; --panel2:#182036; --panel3:#212c47;
    --ink:#f8fafc; --dim:#94a3b8; --gold:#fbbf24; --gold-dim:#453209;
    --cyan:#38bdf8; --red:#f43f5e; --lime:#4ade80; --purple:#c084fc;
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
  .badge.red {{ background:rgba(244,63,94,0.15); color:#fda4af; border-color:rgba(244,63,94,0.38); }}
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

  /* HERO STAGE */
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

  /* CHAPTER TIMELINE */
  .chapters-strip {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:6px;
  }}
  .chap-btn {{
    background:var(--panel2); border:1px solid #2b3a59; color:#cbd5e1;
    border-radius:8px; padding:7px 9px; font:inherit; font-size:11.5px; font-weight:700;
    cursor:pointer; text-align:left; transition:all 0.12s ease;
    display:flex; justify-content:space-between; align-items:center; gap:4px;
  }}
  .chap-btn:hover {{ border-color:var(--gold); color:#fff; }}
  .chap-btn.on {{
    background:linear-gradient(135deg, #3b2a0a 0%, #241a07 100%);
    border-color:var(--gold); color:#fde68a;
    box-shadow:0 0 14px rgba(251,191,36,0.22);
  }}
  .chap-time {{ font-family:ui-monospace, Consolas, monospace; font-size:10.5px; color:#94a3b8; }}
  .chap-btn.on .chap-time {{ color:#fcd34d; }}

  /* SOUNDBOARD BAR */
  .soundboard {{
    background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:16px;
    display:flex; flex-direction:column; gap:10px;
  }}
  .sec-hdr {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:baseline; gap:8px; }}
  .sec-hdr h2 {{ margin:0; font-size:18px; font-weight:850; color:#fff; }}
  .sec-hdr span {{ font-size:12.5px; color:var(--dim); }}
  .sfx-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(210px, 1fr)); gap:7px; }}
  .sfx-btn {{
    background:var(--panel2); border:1px solid #304063; color:#e2e8f0;
    border-radius:9px; padding:8px 10px; font:inherit; font-size:12px; font-weight:700;
    cursor:pointer; text-align:left; transition:all 0.12s ease;
    display:flex; align-items:center; justify-content:space-between; gap:6px;
  }}
  .sfx-btn:hover {{ border-color:var(--cyan); color:#7dd3fc; transform:translateY(-1px); }}
  .sfx-btn.playing {{ border-color:var(--lime); background:#132f23; color:#86efac; }}

  /* 15-CARD GRID */
  .cards-grid {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(370px, 1fr)); gap:14px;
  }}
  .landmark-card {{
    background:var(--panel); border:1px solid var(--border); border-radius:14px;
    overflow:hidden; display:flex; flex-direction:column;
    transition:border-color 0.15s ease, transform 0.15s ease;
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
    position:absolute; bottom:8px; right:8px; display:flex; gap:5px;
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

  /* CAST & TECH */
  .two-col {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(360px, 1fr)); gap:16px; }}
  .info-box {{
    background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:18px;
    display:flex; flex-direction:column; gap:10px;
  }}
  .info-box h3 {{ margin:0; font-size:17px; font-weight:850; color:var(--gold); }}
  .cast-list {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:6px;
    margin:0; padding:0; list-style:none;
  }}
  .cast-list li {{
    background:var(--panel2); border:1px solid #283654; border-radius:7px;
    padding:6px 9px; font-size:12px; color:#e2e8f0; font-weight:650;
  }}
  .tech-list {{ margin:0; padding-left:18px; display:flex; flex-direction:column; gap:8px; color:#cbd5e1; font-size:13px; }}
  .tech-list b {{ color:#fff; }}
  .tech-list code {{ background:#1d2842; color:#fde68a; padding:1px 5px; border-radius:4px; }}

  /* LIGHTBOX */
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
        <span class="badge gold">Bakersfield Quake • Startup Demo</span>
        <span class="badge cyan">maps/bklan5.bsp</span>
        <span class="badge lime">All 19 Custom Characters</span>
        <span class="badge red">13 Custom Guns + Vehicles</span>
      </div>
      <h1><span>BAKERSFIELD</span> Sign-to-Sign Comedy Tour (<code>intro.dem</code>)</h1>
      <p class="sub">
        Starts automatically on launch via <code>startdemos intro</code> in <code>quake.rc</code> — opening with just the solo
        <b>White LAN Van</b> honking under the yellow <b>BAKERSFIELD</b> Sign before all 19 custom characters pile out for a smooth 15-landmark tour across <code>bklan5</code>!
      </p>
    </div>
    <div class="actions">
      <a class="btn primary" id="dlPackBtn" href="https://bakersfield.larrywew.fun/intro-demo/bakersfield_intro_demo_pack.zip" download>⬇ Drop-In Quake Pack (.zip • {zip_mb:.1f} MB)</a>
      <a class="btn" id="dlMp4Btn" href="https://bakersfield.larrywew.fun/intro-demo/intro_demo_bklan5.mp4" target="_blank" rel="noopener">🎬 Full 720p MP4 + Audio</a>
      <a class="btn" id="dlDemBtn" href="https://bakersfield.larrywew.fun/intro-demo/intro.dem" download>📼 Raw intro.dem ({dem_mb:.2f} MB)</a>
      <button class="btn" type="button" id="copyCmdBtn">📋 Copy <code>playdemo intro</code></button>
    </div>
  </header>

  <!-- HERO DUAL-MODE CINEMA PLAYER -->
  <section class="stage-card">
    <div class="mode-tabs">
      <div class="tab-pair">
        <button class="btn active" type="button" id="tabVideoBtn">🎬 Full 76s HD Recorded Video + Stereo Audio</button>
        <button class="btn" type="button" id="tabStoryBtn">🖼 100% Self-Contained Offline 19-Shot Tour &amp; SFX</button>
      </div>
      <div class="now-playing" id="nowPlayingBanner">Card 01 • Bakersfield Sign — Solo White LAN Van Idling &amp; Honking</div>
    </div>

    <!-- VIDEO VIEWPORT -->
    <div class="viewport-wrap" id="videoWrap">
      <video id="heroVideo" controls playsinline preload="metadata"></video>
    </div>

    <!-- OFFLINE STORYBOARD VIEWPORT -->
    <div class="viewport-wrap hidden" id="storyWrap">
      <img id="storyImg" alt="Bakersfield Quake bklan5 Tour Frame">
      <div class="story-overlay">
        <div>
          <div class="story-cap-title" id="storyTitle"></div>
          <div class="story-cap-sub" id="storySub"></div>
        </div>
        <div class="story-controls">
          <button class="btn" type="button" id="prevShotBtn">◀ Prev</button>
          <button class="btn primary" type="button" id="autoPlayBtn">▶ Auto-Play Tour</button>
          <button class="btn" type="button" id="nextShotBtn">Next ▶</button>
          <button class="btn" type="button" id="storySfxBtn">🔊 Play Card SFX</button>
          <button class="btn" type="button" id="zoomShotBtn">🔍 Fullscreen</button>
        </div>
      </div>
    </div>

    <!-- 15 INTERACTIVE CHAPTER PILLS -->
    <div class="chapters-strip" id="chaptersStrip"></div>
  </section>

  <!-- EMBEDDED OFFLINE QUAKE SOUNDBOARD -->
  <section class="soundboard">
    <div class="sec-hdr">
      <h2>🔊 Embedded Bakersfield Quake Signature Soundboard (100% Offline Base64 Audio)</h2>
      <span>Click any clip to preview the exact voice lines, horns &amp; weapon gags heard in <code>intro.dem</code></span>
    </div>
    <div class="sfx-grid" id="sfxGrid"></div>
  </section>

  <!-- 15-CARD LANDMARK TOUR GRID -->
  <section style="display:flex;flex-direction:column;gap:10px;">
    <div class="sec-hdr">
      <h2>🗺 All 15 <code>bklan5</code> Landmarks, Custom Guns, Vehicles &amp; Gags (0:00 – 1:16)</h2>
      <span>Click any card thumbnail to zoom in 1280×720 HD, jump the video player, or trigger its gag audio</span>
    </div>
    <div class="cards-grid" id="cardsGrid"></div>
  </section>

  <!-- FULL CAST ROLL CALL & TECHNICAL ARCHITECTURE -->
  <section class="two-col">
    <div class="info-box">
      <h3>🚐 All 19 Custom Characters Piling Out of the White Van</h3>
      <ul class="cast-list" id="castList"></ul>
    </div>
    <div class="info-box">
      <h3>⚙ Smooth Camera &amp; Zero-Conflict Engineering</h3>
      <ul class="tech-list">
        <li><b>White Van Cold Open → Staggered Roll Call:</b> Card 1 (<code>0.0–4.4s</code>) shows <i>only</i> <code>progs/veh_van.md3</code> idling, rocking on suspension &amp; honking under the yellow <code>BAKERSFIELD</code> Sign. At <code>4.4s</code>, the rear doors burst open (<code>veh_van_open.md3</code>) and all 19 custom characters fan out with signature voice cues spaced <code>~0.74s</code> apart so zero lines muddle together.</li>
        <li><b>150+ Hz Smooth Camera + <code>.dem</code> Header Stamping:</b> <code>BM_UpdateIntroCam</code> in <code>csprogs.dat</code> evaluates C1 smoothstep tracking splines at full monitor refresh rate (<code>VF_ANGLES</code> / <code>VF_CL_VIEWANGLES</code>) with clean hard cuts between landmarks and zero view-bobbing, while <code>stamp_demo_headers()</code> writes matching 100 Hz angles into all <code>7,437</code> <code>.dem</code> packets.</li>
        <li><b>Zero-Server-Slot CSQC Viewmodel Showcase:</b> <code>bklan5.bsp</code> uses <code>106</code> inline brush submodels. Rendering all 13 custom first-person guns (<code>v_robdob.mdl</code>, <code>v_pickle.md3</code>, <code>v_wewcannon.md3</code>, <code>v_milky.md3</code>, <code>v_span.mdl</code>, <code>v_srifle.mdl</code>, <code>v_hammer.mdl</code>, <code>v_netsend.md3</code>, <code>ltg_v3d.md3</code>, <code>v_mm_cannon.md3</code>, <code>v_mm_slingshot.md3</code>, <code>v_googun.md3</code>, <code>v_mysterybox.md3</code>) in CSQC (<code>RF_VIEWMODEL | RF_DEPTHHACK</code>) consumes <code>0</code> server <code>MAX_MODELS (256)</code> slots!</li>
        <li><b>Live Gameplay <code>progs.dat</code> Untouched:</b> <code>intro_director.qc</code> compiles strictly inside an isolated build folder (<code>source/mm_tools/out/qc_intro_build/</code>) to record <code>intro.dem</code>, leaving live multiplayer <code>progs.dat</code> 100% untouched.</li>
      </ul>
    </div>
  </section>
</div>

<!-- FULLSCREEN LIGHTBOX -->
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

// Smart relative/hosted URL setup so page works at /intro-demo/, /bakersfield_intro_demo.html, or offline file://
const REMOTE_BASE = 'https://bakersfield.larrywew.fun/intro-demo/';
const isIntroSubdir = location.pathname.includes('/intro-demo/');
const assetBase = isIntroSubdir ? './' : REMOTE_BASE;

document.getElementById('dlPackBtn').href = assetBase + 'bakersfield_intro_demo_pack.zip';
document.getElementById('dlMp4Btn').href = assetBase + 'intro_demo_bklan5.mp4';
document.getElementById('dlDemBtn').href = assetBase + 'intro.dem';

video.poster = DATA.shots[0].src;
video.src = assetBase + 'intro_demo_bklan5.mp4';
video.addEventListener('error', () => {{
  if (video.src !== REMOTE_BASE + 'intro_demo_bklan5.mp4') {{
    video.src = REMOTE_BASE + 'intro_demo_bklan5.mp4';
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
    nowPlayingBanner.textContent = `Card ${{String(c.card).padStart(2,'0')}} (${{fmtTime(c.t0)}}–${{fmtTime(c.t1)}}) • ${{c.landmark}} — ${{c.title}}`;
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
  document.getElementById('autoPlayBtn').textContent = '▶ Auto-Play Tour';
}}

document.getElementById('prevShotBtn').onclick = () => {{ stopAutoPlay(); renderStoryShot(curShot - 1); }};
document.getElementById('nextShotBtn').onclick = () => {{ stopAutoPlay(); renderStoryShot(curShot + 1); }};
document.getElementById('storySfxBtn').onclick = (e) => playCardSfx(curCardIdx, e.currentTarget);
document.getElementById('autoPlayBtn').onclick = () => {{
  if (autoTimer) {{
    stopAutoPlay();
  }} else {{
    playCardSfx(curCardIdx, null);
    document.getElementById('autoPlayBtn').textContent = '⏸ Pause Auto-Tour';
    autoTimer = setInterval(() => {{
      const prevCard = curCardIdx;
      renderStoryShot(curShot + 1);
      if (curCardIdx !== prevCard) playCardSfx(curCardIdx, null);
    }}, 3400);
  }}
}};

// Build 15 chapter pills
DATA.cards.forEach((c, idx) => {{
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'chap-btn' + (idx === 0 ? ' on' : '');
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

// Build 15 Soundboard buttons
DATA.cards.forEach((c, idx) => {{
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'sfx-btn';
  b.innerHTML = `<span>${{c.sfx_label}}</span><span style="color:#94a3b8;font-size:11px">#${{String(c.card).padStart(2,'0')}}</span>`;
  b.onclick = () => playCardSfx(idx, b);
  sfxGrid.appendChild(b);
}});

// Build 15 Landmark Cards
DATA.cards.forEach((c, idx) => {{
  const el = document.createElement('article');
  el.className = 'landmark-card';
  let activeLocalShot = c.shots[0];

  const switchHtml = c.shots.length > 1
    ? `<div class="shot-switch">${{c.shots.map((sIdx, k) =>
        `<button type="button" class="mini-pill ${{k===0?'on':''}}" data-sidx="${{sIdx}}">Shot ${{k+1}}</button>`
      ).join('')}}</div>`
    : '';

  const tagsHtml = [
    ...c.weapons.map(w => `<span class="tag wep">🔫 ${{w}}</span>`),
    ...c.vehicles.map(v => `<span class="tag veh">🚐 ${{v}}</span>`),
    ...c.chars.map(ch => `<span class="tag chr">🎭 ${{ch}}</span>`),
  ].join('');

  el.innerHTML = `
    <div class="card-thumb-wrap">
      <img src="${{DATA.shots[activeLocalShot].src}}" alt="${{c.title}}">
      <span class="card-num-pill">CARD ${{String(c.card).padStart(2,'0')}}</span>
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
        <button type="button" class="sm-btn sfx-trig">🔊 Hear Gag SFX</button>
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

// Cast list
DATA.cast19.forEach(item => {{
  const li = document.createElement('li');
  li.textContent = item;
  castList.appendChild(li);
}});

// Lightbox
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

// Copy console cmd
document.getElementById('copyCmdBtn').onclick = (e) => {{
  navigator.clipboard.writeText('playdemo intro');
  const b = e.currentTarget;
  const old = b.innerHTML;
  b.textContent = '✓ Copied: playdemo intro';
  setTimeout(() => {{ b.innerHTML = old; }}, 1600);
}};

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
