r"""Builds the 100% Self-Contained Interactive HTML Showcase & Mod Encyclopedia for
Bakersfield Quake's 8-Act Movie-Like Cinematic Showcase (`intro.dem` on `maps/downtown.bsp`):
  - Act 01 (0.0s–5.5s): Historic Fox Theater Marquee Crane-Down -> The White "6-Man LAN Van" J-Turn Drift!
  - Act 02 (5.5s–11.0s): Rear Barn Doors Blow Off -> Wheelman Stunt Trilogy (Fire-Wheels, Pipe-Jet, Wew Cannon)!
  - Act 03 (11.0s–17.0s): Clown-Car LAN Cast Pileout, 4AM Table Flip, Laptop Head, NetSend PC, Pickle Surprise & Bonk Clang!
  - Act 04 (17.0s–24.0s): Rush Hour Stampede — "IT'S SALMON!" Supercar, Bus, Bikes, Garand *PING!*, Mega Man, Mystery Box, JohnWave & Rocket Cans!
  - Act 05 (24.0s–31.0s): Milky Song Drop, H-St Milk-Puddle Spinouts & Whiplash 360° Aerial Fox Theater Orbit!
  - Act 06 (31.0s–36.2s): 50-Entity Fox Clock Tower Tornado (Milkys, Wheelmans, Pickles, Mystery Boxes, Mega Men & Rob Dobs)!
  - Act 07 (36.2s–40.5s): ALL 50 EXPLODE UP CLOSE — Dairy Geysers, 4-Tier Wheelman Sprite Fireballs & Lens Milk Drips!
  - Act 08 (40.5s–48.0s): Blazing Fox Theater, Wrecked White Van on the Marquee, Floating DAN, Jetpack Wheelman, ROB & 24 Yellow CCCs!
Plus complete interactive Mod Analysis Encyclopedia (18 Custom Weapons, Characters & .SPR32 Sprites, Vehicles & LAN Props).

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
FFMPEG = r"C:\Users\qxdc\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"

PK3_LIST = [
    os.path.join(MOD_ROOT, "bakersfield.pk3"),
    os.path.join(MOD_ROOT, "zz_bakovan.pk3"),
    os.path.join(MOD_ROOT, "zz_tone1.pk3"),
    os.path.abspath(os.path.join(MOD_ROOT, "..", "quake15", "q15.pk3")),
]

OUT_HTML = os.path.join(MOD_ROOT, "bakersfield_intro_demo.html")
OUT_ZIP = os.path.join(OUT_DIR, "bakersfield_intro_demo_pack.zip")


SHOTS_META = [
    ("zz_movie_01_act1_fox_marquee_crane.png", 1, 1.1, "Act 01A • Historic Fox Theater Marquee Crane-Down (20th & H St Opening Shot)"),
    ("zz_movie_02_act1_white_van_drift_arrival.png", 1, 4.4, "Act 01B • THE WHITE VAN ARRIVES — Tire-Smoking J-Turn Drift Under the FOX Neon!"),
    ("zz_movie_03_act2_wheelman_barndoors_burnout.png", 2, 6.3, "Act 02A • Rear Barn Doors Blow Clean Off — Wheelman Explodes Out in a Fire-Wheels Burnout!"),
    ("zz_movie_04_act2_wheelman_pipejet_wewcannon.png", 2, 9.8, "Act 02B • Wheelman Stunt Trilogy — Pipe-Jet Afterburner, 3D Roller & Wew Cannon Blast!"),
    ("zz_movie_05_act3_clowncar_tableflip_laptophead.png", 3, 12.2, "Act 03A • Clown-Car LAN Cast Pileout — 4AM Table Flip, Flying Monitors & Chomping Laptop Head!"),
    ("zz_movie_06_act3_pickle_surprise_bonk_clang.png", 3, 15.6, "Act 03B • \"PICKLE SURPRISE!!\" Diva + Goo Foam + Bonk Frying-Pan Ragdoll Launch!"),
    ("zz_movie_07_act4_supercar_bus_bikes_garand.png", 4, 18.4, "Act 04A • Rush Hour Stampede — \"IT'S SALMON!\" Supercar, School Bus, 3 Bikes & M1 Garand *PING!*"),
    ("zz_movie_08_act4_megaman_mbox_johnwave_trashcans.png", 4, 22.0, "Act 04B • Mega Man Dome, Mystery Box Confetti, JohnWave Tidal Ring & 3 Rocket Trash Cans!"),
    ("zz_movie_09_act5_hst_milkys_puddle_spinouts.png", 5, 25.5, "Act 05A • Milky Song Drop! Giant H-St Milky Invasion & Slippery Milk-Puddle Spinouts!"),
    ("zz_movie_10_act5_fox_360_aerial_orbit.png", 5, 29.2, "Act 05B • Whiplash 360° Aerial Fox Theater Orbit with 3 Close-Up Milkys & 3 Stunt Wheelman Sprites!"),
    ("zz_movie_11_act6_tower_50_tornado_reveal.png", 6, 32.4, "Act 06A • \"NO WAY!!\" — 50-Entity Tornado Swirling Around the 74-Ft Fox Clock Tower!"),
    ("zz_movie_12_act6_tower_50_tornado_peak.png", 6, 35.2, "Act 06B • Supersonic 50-Entity Belfry Vortex Peak (Milkys, Wheelmans, Pickles, Boxes & Rob Dobs)!"),
    ("zz_movie_13_act7_all50_explode_fireballs_tires.png", 7, 37.3, "Act 07A • ALL 50 EXPLODE UP CLOSE — Dairy Geysers, 4-Tier Wheelman Fireballs & Bouncing Tires!"),
    ("zz_movie_14_act7_spire_megablast_lens_milk.png", 7, 39.0, "Act 07B • Spire-Top Mega Detonation — Thick White Milk Drips Splashed Right Across the Camera Lens!"),
    ("zz_movie_15_act8_burning_fox_wreckedvan_drips.png", 8, 41.8, "Act 08A • FOX THEATER ON FIRE + Smoking Wrecked White Van Parked Right on Top of the Marquee!"),
    ("zz_movie_16_act8_floating_dan_wheelman_rob_cccs.png", 8, 45.6, "Act 08B • Grand Finale — Floating DAN, Jetpack Wheelman, ROB & 24 Yellow CCCs (\"I'm Floating!\" / \"Ah, I Can't See!\")!"),
]


CARDS_DATA = [
    {
        "card": 1, "t0": 0.0, "t1": 5.5,
        "short": "01 • Fox & White Van",
        "landmark": "20th & H St // Historic Fox Theater Opening",
        "title": "Hollywood Crane-Down & The White \"6-Man LAN Van\" J-Turn Drift!",
        "desc": "Starts high on the glowing 1930 Historic Fox Theater marquee and cranes smoothly down to the curb just as the legendary White Van (progs/veh_van.md3) comes screaming down H Street—honking, tire-smoking, clipping a trashcan sky-high, and whipping a full 180° J-turn right in front of the ticket booth!",
        "weapons": ["Hollywood Marquee Crane", "180° Tire-Smoke J-Turn"],
        "vehicles": ["White 6-Man LAN Van (veh_van.md3)", "Fox Theater Marquee"],
        "chars": ["Strolling Citizens Scattering", "Punting Trashcan"],
        "sfx_path": "sound/vehicles/lanvan.wav",
        "sfx_label": "🚐 \"6-Man LAN Van!\" Drift Arrival",
        "shots": [0, 1],
    },
    {
        "card": 2, "t0": 5.5, "t1": 11.0,
        "short": "02 • Wheelman Burst!",
        "landmark": "Curbside Stunt Stage // Enter Wheelman",
        "title": "Barn Doors Blow Off & Wheelman's Ridiculous Stunt Trilogy!",
        "desc": "The walk-in van rocks violently on its suspension until BOTH rear barn doors (veh_van_door.md3) blast clean off past the camera! Out rockets WHEELMAN—ripping a flaming Fire-Wheels burnout, B-Boy headspin, Pipe-Jet afterburner flyby, Green-Suit hype dance, 3D Wheelman Roller & Thinker pose, and firing the Eric Deason Wew Cannon!",
        "weapons": ["Eric Deason Wew Cannon (g_wewcannon.md3)", "Pipe-Jet Afterburner"],
        "vehicles": ["Walk-In Van + Flying Barn Doors"],
        "chars": ["Wheelman .SPR32 (4 Sheets)", "3D Wheelman Roller & Thinker"],
        "sfx_path": "sound/wcannon/wc_scream.wav",
        "sfx_label": "🛞🔥 Wheelman Scream & Burnout!",
        "shots": [2, 3],
    },
    {
        "card": 3, "t0": 11.0, "t1": 17.0,
        "short": "03 • Clown-Car Chaos",
        "landmark": "Fox Sidewalk // 14-Legend Clown-Car Pileout",
        "title": "Clown-Car Cast Pileout, 4AM Table Flip, Pickle Surprise & Bonk Clang!",
        "desc": "Impossible clown-car gag: 12 Bakersfield legends & LAN friends pour out of that single White Van! Daniel's Dad screams \"IT'S 4 AM!!\" and flips the LAN table (sending CRT monitors & chairs flying), a Laptop Gun head chomps across the asphalt zapping blue arcs, NetSend PC bluescreens, Pickle Surprise spins up, Goo blobs swell, and the Bonk Frying-Pan launches a fighter skyward!",
        "weapons": ["4AM Table Flip", "Laptop Gun Head", "NetSend BSOD PC", "Pickle Surprise", "Goo Gun", "Bonk Frying Pan"],
        "vehicles": ["Bouncing White Van Clown-Car", "JessKart"],
        "chars": ["Daniel + 4AM Dad", "Larry Wew", "Slot-Jackpot David", "Bryan & LAN Friends"],
        "sfx_path": "sound/pickle/surprise.wav",
        "sfx_label": "🥒💃 \"PICKLE SURPRISE!!\"",
        "shots": [4, 5],
    },
    {
        "card": 4, "t0": 17.0, "t1": 24.0,
        "short": "04 • Full Stampede!",
        "landmark": "20th & H Intersection // Total Rush Hour Mayhem",
        "title": "\"IT'S SALMON!\" Supercar, School Bus, Bikes, Garand *PING!*, Mega Man & JohnWave!",
        "desc": "Every vehicle, weapon, and summon hits the intersection at once: the Not-Pink Supercar (\"IT'S SALMON!\") powerslides opposite the yellow School Bus & Orange Forklift; 3 bicycles spin wheelies; M4A1, Tommy Gun & M1 Garand (*PING!*) crossfire with a Sentry Turret; Mega Man's plasma dome, Mystery Box confetti, JohnWave tidal ring, Rob Dobs, John-Birds, Sky Podracer & 3 Rocket Trashcans erupt!",
        "weapons": ["M4A1 + Tommy + Garand *PING!*", "Mega Man Dome", "Mystery Box", "JohnWave Ring", "Sentry Turret"],
        "vehicles": ["Not-Pink Supercar", "School Bus", "Forklift", "3 Bicycles", "Sky Podracer", "3 Rocket Cans"],
        "chars": ["Jetpack Trooper", "2 Rob Dob Riders", "3 John-Birds", "Floating Calc Heads"],
        "sfx_path": "sound/bklan/notpink.wav",
        "sfx_label": "🏎️💖 \"IT'S SALMON, NOT PINK!!\"",
        "shots": [6, 7],
    },
    {
        "card": 5, "t0": 24.0, "t1": 31.0,
        "short": "05 • Milkys & 360° Fox",
        "landmark": "H Street -> 360° Fox Aerial Orbit // Milky Song Drop!",
        "title": "Milky Song Drop, Milk-Puddle Spinouts & Whiplash 360° Fox Theater Orbit!",
        "desc": "The signature Milky Milky song (milky/song.ogg) drops and plays non-stop to the end! Ten giant 16-angle video-skin Milky Grenades bounce down H Street splashing white milk puddles that send the White Van & LAN cast spinning wildly—before the camera launches skyward into a 3.6s full 360° orbit of the Fox Theater with 3 Milkys & 3 Wheelman sprites locked right in front of the lens!",
        "weapons": ["Milky Milky Grenades (pinklady.md3)", "Slippery Milk Puddles (milksplat.md3)", "3.6s 360° Aerial Orbit"],
        "vehicles": ["Spinning-Out White Van", "360° Historic Fox Theater"],
        "chars": ["Skidding LAN Cast", "3 Lens-Locked Milkys + 3 Stunt Wheelmans"],
        "sfx_path": "sound/milky/song.ogg",
        "sfx_label": "🥛🎵 Milky Milky Song Drop!",
        "shots": [8, 9],
    },
    {
        "card": 6, "t0": 31.0, "t1": 36.2,
        "short": "06 • 50-Entity Tornado!",
        "landmark": "Fox Clock Tower // 50-Entity Supersonic Cyclone",
        "title": "\"NO WAY!!\" — 50 Milkys, Wheelmans, Pickles, Mystery Boxes & Rob Dobs Spin the Tower!",
        "desc": "Camera snaps right up to the 74-foot Fox Clock Tower belfry as Bryan yells \"NO WAY!!\"—50 entities across 5 stacked rings (20 Milkys, 21 Wheelman stunt sprites, plus cameo Pickles, Mystery Boxes, Mega Men & Rob Dob horse riders) accelerate into a hilarious supersonic tornado around the spire!",
        "weapons": ["5 Stacked Belfry Rings (5×10 = 50)", "Accelerating Cyclone Vortex"],
        "vehicles": ["74-Ft Fox Clock Tower Spire"],
        "chars": ["20 Milkys + 21 Wheelmans + 9 Cameo Icons"],
        "sfx_path": "sound/bryan/noway.wav",
        "sfx_label": "😱🌪️ Bryan: \"NO WAY!!\" (50-Tornado)",
        "shots": [10, 11],
    },
    {
        "card": 7, "t0": 36.2, "t1": 40.5,
        "short": "07 • ALL 50 EXPLODE!!",
        "landmark": "Fox Belfry Spire // Up-Close 50-Entity Chain Detonation",
        "title": "ALL 50 EXPLODE IN YOUR FACE: Dairy Geysers, 4-Tier Wheelman Fireballs & Lens Milk!",
        "desc": "Every single one of the 50 spinning entities detonates from bottom ring to spire top in a 2.5-second chain reaction: roaring white milky_boom dairy geysers, 4-tier 360° Wheelman sprite fireballs, bouncing 3D tires & axles, culminating in a spire-top mega-blast that splashes thick white milk drips directly down the camera lens!",
        "weapons": ["25+ Dairy Geysers", "4-Tier Wheelman Sprite Fireballs", "Direct Camera-Lens Milk Drips!"],
        "vehicles": ["Flying 3D Tires & Axles (mm_wheel.md3 / wc_bar.md3)"],
        "chars": ["All 50 Detonating Up Close!"],
        "sfx_path": "sound/wcannon/wc_boom.wav",
        "sfx_label": "💥🥛 50-Entity Tower Mega-Blast!",
        "shots": [12, 13],
    },
    {
        "card": 8, "t0": 40.5, "t1": 48.0,
        "short": "08 • Burning Fox Finale!",
        "landmark": "Blazing Fox Marquee // Wrecked Van + Floating Legends!",
        "title": "FOX ON FIRE + Wrecked White Van on Marquee + Floating DAN, Wheelman, ROB & 24 CCCs!",
        "desc": "Grand comedic punchline: 28 roaring flame & smoke columns engulf the Fox Theater, and parked smoking right on top of the Fox Marquee roof is the WRECKED WHITE VAN (veh_van_wreck.md3) honking pitifully! Meanwhile DAN, Jetpack Wheelman & ROB float weightlessly across the lens surrounded by 24 spinning yellow letter Cs as \"I'm floating!\" and \"Ah, I can't see!\" play us out!",
        "weapons": ["28 Fox Fire Columns", "24 Spinning Yellow CCCs (ccc.md3)", "\"I'm Floating!\" + \"Ah, I Can't See!\""],
        "vehicles": ["Wrecked White Van on the Marquee! (veh_van_wreck.md3)"],
        "chars": ["Floating DAN", "Floating Jetpack Wheelman", "Floating ROB"],
        "sfx_path": "sound/ccc/shoot.wav",
        "sfx_label": "😵🟡 \"Ah, I Can't See!\" Finale",
        "shots": [14, 15],
    },
]

EXTRA_SOUNDBOARD = [
    ("😤🪑 \"IT'S 4 AM!!\" (Daniel's Dad Table Flip)", "sound/daniel/dad_4am.wav", "Act 03"),
    ("🍳💥 Bonk Frying-Pan Metallic CLANG!", "sound/hammer/frying_pan.wav", "Act 03"),
    ("💻⚡ Laptop Gun Chomp & Shock (\"Canis!\")", "sound/ltgun/canis.wav", "Act 03"),
    ("💾🖥️ NetSend BSOD (\"Where's the Disk?!\")", "sound/netsend/wheres_disk.wav", "Act 03"),
    ("🔫🔔 M1 Garand En-Bloc Clip *PING!*", "sound/dod/garand_reload_clipding.wav", "Act 04"),
    ("🤖🔵 Mega Buster Plasma Blast!", "sound/megaman/mm_fire.wav", "Act 04"),
    ("🛞✨ \"I'm Floating!\" (Zero-G Finale)", "sound/jetpack/floating.wav", "Act 08"),
    ("🟡😂 \"CCC! C-C-C-C!\" (Daniel Yellow-C Burst)", "sound/daniel/ccc_burst.wav", "Act 08"),
]

WEAPONS_DB = [
    {"name": "Eric Deason / Wheelman Cannon", "qc": "eric_cannon.qc", "models": "v_wewcannon.md3 / g_wewcannon.md3 / wheelman.spr32", "role": "Fires screaming 8-directional Wheelman stunt sprites that ricochet on flaming tires and detonate into 4-tier 360° sprite fireballs + bouncing 3D tires/axles."},
    {"name": "Milky Milky Grenade", "qc": "milky.qc", "models": "v_milky.md3 / pinklady.md3 / milksplat.md3", "role": "16-angle video-skin bouncing grenade playing milky/song.ogg; erupts into dairy geysers and leaves slippery white milk puddles that spin out players & cars."},
    {"name": "Fun Gun (5-in-1 LAN Chaos)", "qc": "funguns.qc", "models": "daniel_table.md3 / pickle.md3 / goo.md3", "role": "Cycles chaotic LAN gag modes including the 4AM Table Flip, Pickle Surprise spinning diva bomb, Goo Gun swelling foam traps, and confetti blasts."},
    {"name": "CCC Yellow-C Launcher", "qc": "ccc.qc", "models": "ccc.md3 + ccc_trail", "role": "Rapid-fires bright yellow 3D letter 'C's that bounce around corners and blind victims' screens while shouting \"Ah, I can't see!\" and \"C-C-C-C!\""},
    {"name": "Laptop Gun (Autonomous Head)", "qc": "ltgun.qc", "models": "ltg_view.md3 / ltg_head.md3 / ltg_laser.md3", "role": "Transforms from a typing LAN laptop into a chomping autonomous head that hops after enemies firing blue shock lasers."},
    {"name": "NetSend BSOD Disk Launcher", "qc": "netsend.qc", "models": "netsend_disk.md3 / netsend_pc.md3 / netsend_scr.md3", "role": "Hurls 3.5\" floppy disks that drop a giant CRT PC onto targets' heads with a glowing Blue Screen of Death."},
    {"name": "Bonk Frying-Pan Hammer", "qc": "hammer.qc", "models": "v_hammer.mdl / w_blueflail.mdl / spark_yellow.mdl", "role": "Charged melee swing delivering an ear-ringing cast-iron frying-pan CLANG (frying_pan.wav) that launches victims into ragdoll orbit."},
    {"name": "Mega Man Plasma Buster", "qc": "megaman.qc", "models": "megaman.md3 / mm_explode.md3", "role": "Charges up a classic 8-bit/3D Mega Buster shot that expands into a huge glowing blue plasma shockwave dome."},
    {"name": "Mystery Box Launcher", "qc": "mbox.qc", "models": "proj_mysterybox.md3", "role": "Bouncing question-mark crate (drv_boing_hop.wav) that pops open into random jackpots, confetti bursts, or explosive surprises."},
    {"name": "JohnWave Tidal Attack & John-Birds", "qc": "john.qc / john_bird.qc", "models": "jw_wave.md3 / jw_splash.spr32 / john_bird_head.md3", "role": "Unleashes an expanding 360° tidal wave ring (jwthrow.wav) while summoned winged John-Birds dive-bomb from above shedding feathers."},
    {"name": "Goo Gun", "qc": "weapons.qc / custom_effects.qc", "models": "v_googun.md3 / goo.md3", "role": "Sprays sticky neon-green blobs that weld onto enemies and walls, swelling rapidly before popping in chain-reaction acid splashes."},
    {"name": "CS 1.6 M4A1 Carbine", "qc": "bm_weapons.qc", "models": "p_m4.md3", "role": "Crisp tactical rifle with authentic Counter-Strike 1.6 unsilenced bark and reload magazines (bm_reload)."},
    {"name": "WW2 Thompson Submachine Gun", "qc": "bm_weapons.qc", "models": "p_tommy.md3", "role": "High-ROF Day-of-Defeat drum Tommy Gun built for clearing crowded Bakersfield alleyways."},
    {"name": "M1 Garand (*PING!*)", "qc": "bm_weapons.qc", "models": "p_garand.md3", "role": "Hard-hitting semi-auto rifle complete with the iconic metallic en-bloc clip ejection *PING!* (garand_reload_clipding.wav)."},
    {"name": "Deployable Sentry Turret", "qc": "turret.qc", "models": "turrbase.mdl + turrgun.mdl", "role": "Two-piece tripod + tracking dual-barrel head that locks onto passing enemies and vehicles."},
    {"name": "Jetpack Thruster Pack", "qc": "jetpack.qc", "models": "jetpack.md3", "role": "Straps twin rocket thrusters to the player's back for vertical rooftop dogfights while shouting \"I'm floating!\""},
]

CHARS_DB = [
    {"name": "Wheelman (The Mascot)", "asset": "wheelman.spr32 / wheelman_historic.spr32 / wheelman_dance.spr32 / greensuit_wheelman.spr32 + 4× 3D .md3", "desc": "Bakersfield Quake's unstoppable star: 8-angle directional .spr32 sheets covering Fire-Wheels burnout, B-Boy headspin, Zen lotus, Pipe-Jet afterburner, Jetpack hover & 14-frame 4-tier explosions—plus 4 full 3D monuments (Roller, Standing, Titan, Thinker)."},
    {"name": "Daniel & 4AM Table-Flip Dad", "asset": "daniel.spr32 / daniel_dad.spr32 / daniel_table.md3", "desc": "Features Daniel's blind \"Ah, I can't see!\" squint and \"CCC!\" grin alongside his furious 4AM bathrobe Dad flipping the LAN folding table."},
    {"name": "Larry Wew (Robeguy)", "asset": "robeguy.spr32 + larry/love_to_play_quake.wav", "desc": "The bathrobe-clad host himself welcoming everyone to Bakersfield with \"Love to play Quake!\" and \"Double good!\""},
    {"name": "David (Slot-Jackpot) & Pregnant Sprite", "asset": "david.spr32 / preg_1.spr32 + slot_jackpot.wav", "desc": "Hits casino slot-machine jackpots mid-firefight across downtown H Street."},
    {"name": "Bryan (\"NO WAY!!\") & JessKart", "asset": "bryan.spr32 / jesskart.spr32", "desc": "Bryan delivers the mod's signature disbelief scream (\"NO WAY!!\") while JessKart zooms around corners in a custom sprite go-kart."},
    {"name": "The LAN Friends Roster (7 Sprites)", "asset": "fr_dennis / fr_paul / fr_mrdiy / fr_scissors / fr_rob / fr_quakeguy / fr_finger (.spr32)", "desc": "Full crew of digitized real-life friends—including mid-air bicycle-pedaling Rob (fr_rob.spr32) who stars in the zero-G finale!"},
    {"name": "Rob Dob Horse Riders & Floating Heads", "asset": "gw_horse.md3 + mm_suit_rider.md3 / floathead.mdl", "desc": "Suit-wearing riders galloping on 3D horses with giant ears (bigears.md3) while giant chattering calculator heads patrol the sky."},
    {"name": "Downtown Crowd & 3D Pedestrians", "asset": "crowd_c1..c6.spr32 + npc_randguy / afroguy / randlady / fatguy (.md3)", "desc": "Ambient street spectators and 3D Bakersfield citizens who cheer, scatter, or get launched by passing vans."},
]

VEHICLES_DB = [
    {"name": "The White \"6-Man LAN Van\"", "asset": "veh_van.md3 / van_walkin.md3 / veh_van_door.md3 / veh_van_wreck.md3", "desc": "Star vehicle of the mod & Act 1–2: driveable white cargo van with horn, tire squeal, walk-in interior variant, detachable rear barn doors, and flaming marquee-top wreck model!"},
    {"name": "Not-Pink (\"IT'S SALMON!!\") Supercar", "asset": "pink_supercar.md3 + bklan/notpink.wav", "desc": "High-speed exotic sports car whose driver aggressively insists \"IT'S SALMON, NOT PINK!!\" while drifting through intersections."},
    {"name": "Bakersfield Yellow School Bus", "asset": "veh_schoolbus.md3", "desc": "Full-size heavy battering-ram bus capable of plowing an entire deathmatch lobby down 20th Street."},
    {"name": "Orange Warehouse Forklift", "asset": "bklan/sr_vehicle_forklift_orange_a01.md3", "desc": "Compact industrial chaos machine weaving through street brawls."},
    {"name": "Sky Podracer & 3 Rideable Bicycles", "asset": "skyveh_v3.md3 + bike_cruiser / bike_bmx / bike_road (.md3)", "desc": "Low-altitude twin-pod aerial speeder plus three ring-bell bicycles (bikes/bell_ring.wav) for stylish wheelies."},
    {"name": "Rocket Trashcans & LAN Furniture", "asset": "bklan/trashcan.md3 / lan_mon1.md3 / lan_chair1.md3", "desc": "Physics-tossed street trashcans, CRT monitors, and folding LAN chairs that turn every block into a slapstick stunt set."},
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


def encode_sfx_mp3_b64(zfiles: list[zipfile.ZipFile], rel_path: str) -> str:
    raw = None
    disk_p = os.path.join(MOD_ROOT, rel_path.replace("/", os.sep))
    if os.path.isfile(disk_p):
        raw = open(disk_p, "rb").read()
    else:
        for zf in zfiles:
            if rel_path in zf.namelist():
                raw = zf.read(rel_path)
                break
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
                "-t", "4.6",
                "-ac", "1", "-ar", "24000", "-b:a", "56k",
                dst,
            ],
            check=True,
        )
        mp3_bytes = open(dst, "rb").read()
    return "data:audio/mpeg;base64," + base64.b64encode(mp3_bytes).decode("ascii")


def build_drop_in_zip() -> int:
    dem_src = os.path.join(MOD_ROOT, "intro_movie_showcase.dem")
    if not os.path.isfile(dem_src):
        dem_src = os.path.join(MOD_ROOT, "intro.dem")

    files_to_pack = [
        (dem_src, "BakersfieldQuake/intro.dem"),
        (dem_src, "BakersfieldQuake/intro_movie_showcase.dem"),
        (os.path.join(MOD_ROOT, "csprogs.dat"), "BakersfieldQuake/csprogs.dat"),
        (os.path.join(MOD_ROOT, "quake.rc"), "BakersfieldQuake/quake.rc"),
        (os.path.join(HERE, "intro_director.qc"), "BakersfieldQuake/source/mm_tools/intro_director.qc"),
        (os.path.join(HERE, "build_intro_demo.py"), "BakersfieldQuake/source/mm_tools/build_intro_demo.py"),
        (os.path.join(MOD_ROOT, "source", "qc_combat_decomp", "csqc", "bm_hud.qc"), "BakersfieldQuake/source/qc_combat_decomp/csqc/bm_hud.qc"),
    ]
    for opt_dem in ("intro_fox360_swarm.dem", "intro_downtown_tour.dem"):
        p = os.path.join(MOD_ROOT, opt_dem)
        if os.path.isfile(p):
            files_to_pack.append((p, f"BakersfieldQuake/{opt_dem}"))

    os.makedirs(OUT_DIR, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc in files_to_pack:
            zf.write(src, arc)
    return os.path.getsize(OUT_ZIP)


def main() -> None:
    print("Packing drop-in zip...")
    zip_bytes = build_drop_in_zip()
    print(f"  -> {OUT_ZIP} ({zip_bytes / (1024*1024):.2f} MB)")

    print("Encoding 16 HD 1280x720 screenshots as embedded base64...")
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

    print("Encoding 16 signature audio clips as embedded base64 MP3...")
    zfiles = [zipfile.ZipFile(p, "r") for p in PK3_LIST if os.path.isfile(p)]
    cards_payload = []
    for c in CARDS_DATA:
        sfx_uri = encode_sfx_mp3_b64(zfiles, c["sfx_path"])
        c_out = dict(c)
        c_out["sfx_uri"] = sfx_uri
        cards_payload.append(c_out)
    extra_sfx_payload = []
    for lbl, spath, badge in EXTRA_SOUNDBOARD:
        extra_sfx_payload.append({
            "label": lbl,
            "badge": badge,
            "uri": encode_sfx_mp3_b64(zfiles, spath),
        })
    for zf in zfiles:
        zf.close()

    dem_src = os.path.join(MOD_ROOT, "intro_movie_showcase.dem")
    if not os.path.isfile(dem_src):
        dem_src = os.path.join(MOD_ROOT, "intro.dem")
    dem_mb = os.path.getsize(dem_src) / (1024 * 1024)
    zip_mb = zip_bytes / (1024 * 1024)

    data_json = json.dumps({
        "shots": shots_payload,
        "cards": cards_payload,
        "extraSfx": extra_sfx_payload,
        "weaponsDb": WEAPONS_DB,
        "charsDb": CHARS_DB,
        "vehiclesDb": VEHICLES_DB,
    })

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bakersfield Quake: The Movie — 8-Act Cinematic Intro Showcase &amp; Mod Encyclopedia</title>
<style>
  :root {{
    --bg:#080b13; --panel:#111726; --panel2:#182036; --panel3:#212c47;
    --ink:#f8fafc; --dim:#94a3b8; --gold:#fbbf24; --cyan:#38bdf8;
    --red:#f43f5e; --lime:#4ade80; --pink:#f472b6; --border:#293654;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0;
    background:radial-gradient(circle at 50% -10%, #1f2b4d 0%, var(--bg) 55%);
    color:var(--ink);
    font:14px/1.52 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    min-height:100vh;
    padding:16px 14px 64px;
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:16px;
  }}
  .wrap {{ width:min(100%, 1260px); display:flex; flex-direction:column; gap:18px; }}

  header {{
    background:rgba(17,23,38,0.94);
    border:1px solid var(--border);
    border-radius:16px;
    padding:20px 22px;
    display:flex;
    flex-wrap:wrap;
    align-items:center;
    justify-content:space-between;
    gap:14px;
    box-shadow:0 16px 42px rgba(0,0,0,0.5);
  }}
  .brand {{ display:flex; flex-direction:column; gap:7px; max-width:790px; }}
  .badges {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .badge {{
    font-size:11px; font-weight:800; letter-spacing:0.05em; text-transform:uppercase;
    padding:3px 9px; border-radius:999px; border:1px solid transparent;
  }}
  .badge.gold {{ background:linear-gradient(135deg,#fde047,#f59e0b); color:#171103; }}
  .badge.cyan {{ background:rgba(56,189,248,0.15); color:#7dd3fc; border-color:rgba(56,189,248,0.38); }}
  .badge.pink {{ background:rgba(244,114,182,0.18); color:#fbcfe8; border-color:rgba(244,114,182,0.45); }}
  .badge.lime {{ background:rgba(74,222,128,0.15); color:#86efac; border-color:rgba(74,222,128,0.38); }}

  h1 {{ margin:0; font-size:clamp(21px, 2.8vw, 31px); font-weight:900; letter-spacing:-0.02em; }}
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
    background:linear-gradient(to top, rgba(5,8,15,0.95) 0%, rgba(5,8,15,0.7) 65%, transparent 100%);
    padding:26px 18px 14px; display:flex; flex-wrap:wrap; justify-content:space-between;
    align-items:flex-end; gap:10px;
  }}
  .story-cap-title {{ font-size:15px; font-weight:850; color:#fff; }}
  .story-cap-sub {{ font-size:12.5px; color:#cbd5e1; }}
  .story-controls {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}

  .chapters-strip {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(145px, 1fr)); gap:6px;
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

  .soundboard, .encyclopedia {{
    background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:18px;
    display:flex; flex-direction:column; gap:12px;
  }}
  .sec-hdr {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:baseline; gap:8px; }}
  .sec-hdr h2 {{ margin:0; font-size:18.5px; font-weight:850; color:#fff; }}
  .sec-hdr span {{ font-size:12.5px; color:var(--dim); }}
  .sfx-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr)); gap:7px; }}
  .sfx-btn {{
    background:var(--panel2); border:1px solid #304063; color:#e2e8f0;
    border-radius:9px; padding:8px 10px; font:inherit; font-size:12px; font-weight:700;
    cursor:pointer; text-align:left; transition:all 0.12s ease;
    display:flex; align-items:center; justify-content:space-between; gap:6px;
  }}
  .sfx-btn:hover {{ border-color:var(--cyan); color:#7dd3fc; transform:translateY(-1px); }}
  .sfx-btn.playing {{ border-color:var(--lime); background:#132f23; color:#86efac; }}

  .cards-grid {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(380px, 1fr)); gap:14px;
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
  .card-title {{ margin:0; font-size:15.5px; font-weight:850; color:#fff; }}
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

  .enc-tabs {{ display:flex; flex-wrap:wrap; gap:8px; border-bottom:1px solid var(--border); padding-bottom:10px; }}
  .enc-grid {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(350px, 1fr)); gap:10px;
  }}
  .enc-item {{
    background:var(--panel2); border:1px solid #293859; border-radius:11px; padding:12px 14px;
    display:flex; flex-direction:column; gap:5px;
  }}
  .enc-item h4 {{ margin:0; font-size:14.5px; font-weight:850; color:var(--gold); display:flex; justify-content:space-between; gap:8px; }}
  .enc-item code {{ font-size:11.5px; color:#7dd3fc; background:#11192c; padding:2px 6px; border-radius:5px; align-self:flex-start; }}
  .enc-item p {{ margin:0; font-size:12.8px; color:#cbd5e1; }}

  .lightbox {{
    position:fixed; inset:0; background:rgba(4,6,12,0.93); z-index:999;
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
        <span class="badge gold">48.0s 8-Act Movie Showcase</span>
        <span class="badge cyan">Act I–II: Fox Theater + White Van + Wheelman!</span>
        <span class="badge pink">Act III–V: Clown-Car Cast + Stampede + 360° Fox!</span>
        <span class="badge lime">Act VI–VIII: 50-Tornado Explosion + Burning Fox Finale!</span>
      </div>
      <h1><span>BAKERSFIELD QUAKE: THE MOVIE</span> — Cinematic Mod Showcase &amp; Arsenal Encyclopedia</h1>
      <p class="sub">
        Re-created startup intro (<code>startdemos intro</code> on <code>maps/downtown.bsp</code>): opens with a Hollywood crane-down on the <b>Historic Fox Theater</b> as <b>the White Van</b> drifts in and <b>Wheelman</b> blows the rear barn doors clean off—then escalates crazier and crazier through a <b>14-legend clown-car pileout</b>, <b>full intersection vehicle/weapon stampede</b>, <b>Milky puddle spinouts &amp; 360° aerial Fox orbit</b>, <b>50-entity Clock Tower tornado detonation</b>, and the <b>blazing Fox Theater + wrecked White Van on the marquee + floating DAN, Wheelman, ROB &amp; 24 yellow CCCs!</b>
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
        <button class="btn active" type="button" id="tabVideoBtn">🎬 Full 720p HD Movie (48.0s • All 8 Escalating Acts + Audio)</button>
        <button class="btn" type="button" id="tabStoryBtn">🖼 100% Self-Contained Offline 16-Shot HD Storyboard &amp; Sound</button>
      </div>
      <div class="now-playing" id="nowPlayingBanner">Act 01 (0:00–0:05) • Fox Theater Crane-Down &amp; The White Van Drift!</div>
    </div>

    <div class="viewport-wrap" id="videoWrap">
      <video id="heroVideo" controls playsinline preload="metadata"></video>
    </div>

    <div class="viewport-wrap hidden" id="storyWrap">
      <img id="storyImg" alt="Bakersfield Quake Movie Showcase Frame">
      <div class="story-overlay">
        <div>
          <div class="story-cap-title" id="storyTitle"></div>
          <div class="story-cap-sub" id="storySub"></div>
        </div>
        <div class="story-controls">
          <button class="btn" type="button" id="prevShotBtn">◀ Prev</button>
          <button class="btn primary" type="button" id="autoPlayBtn">▶ Auto-Play Storyboard</button>
          <button class="btn" type="button" id="nextShotBtn">Next ▶</button>
          <button class="btn" type="button" id="storySfxBtn">🔊 Play Act Audio</button>
          <button class="btn" type="button" id="zoomShotBtn">🔍 Fullscreen</button>
        </div>
      </div>
    </div>

    <div class="chapters-strip" id="chaptersStrip"></div>
  </section>

  <section class="soundboard">
    <div class="sec-hdr">
      <h2>🔊 Interactive Bakersfield Quake Soundboard (16 Offline Base64 MP3 Clips)</h2>
      <span>Click any button to hear the White Van, Wheelman, 4AM Table Flip, Pickle Surprise, Salmon Supercar, Garand *PING!*, Milky Song &amp; Finale Voices</span>
    </div>
    <div class="sfx-grid" id="sfxGrid"></div>
  </section>

  <section style="display:flex;flex-direction:column;gap:10px;">
    <div class="sec-hdr">
      <h2>🎬 All 8 Escalating Movie Acts: From Quiet Fox Marquee to Total Dairy &amp; Tire Apocalypse</h2>
      <span>Switch between Angle 1 &amp; Angle 2 on every Act card, jump the video player, or inspect in 1280×720 HD</span>
    </div>
    <div class="cards-grid" id="cardsGrid"></div>
  </section>

  <section class="encyclopedia">
    <div class="sec-hdr">
      <h2>🔬 Complete Bakersfield Quake (Combat+) Mod Analysis Encyclopedia</h2>
      <span>Analyzed across 35+ QuakeC modules (<code>source/qc_combat_decomp/</code>), 91 custom models/sprites &amp; 58+ sound banks</span>
    </div>
    <div class="enc-tabs">
      <button class="btn active" type="button" id="encTabWep">🔫 Custom Weapons &amp; Gadgets (16)</button>
      <button class="btn" type="button" id="encTabChr">🛞 Characters, Bosses &amp; .SPR32 Sprites (8 Families)</button>
      <button class="btn" type="button" id="encTabVeh">🚐 Driveable Vehicles, Bikes &amp; LAN Props (6 Classes)</button>
    </div>
    <div class="enc-grid" id="encGrid"></div>
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
const encGrid = document.getElementById('encGrid');

const REMOTE_BASE = 'https://bakersfield.larrywew.fun/intro-demo/';
const isIntroSubdir = location.pathname.includes('/intro-demo/');
const assetBase = isIntroSubdir ? './' : REMOTE_BASE;

document.getElementById('dlPackBtn').href = assetBase + 'bakersfield_intro_demo_pack.zip';
document.getElementById('dlMp4Btn').href = assetBase + 'intro_demo_downtown.mp4';
document.getElementById('dlDemBtn').href = assetBase + 'intro.dem';

video.poster = DATA.shots[2].src;
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

function playUri(uri, btnEl) {{
  if (activeAudio) {{ activeAudio.pause(); activeAudio = null; }}
  if (activeSfxBtn) activeSfxBtn.classList.remove('playing');
  const a = new Audio(uri);
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

function playCardSfx(cardIdx, btnEl) {{
  const c = DATA.cards[cardIdx];
  if (c) playUri(c.sfx_uri, btnEl);
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
    nowPlayingBanner.textContent = `Act ${{String(c.card).padStart(2,'0')}} (${{fmtTime(c.t0)}}–${{fmtTime(c.t1)}}) • ${{c.title}}`;
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
  document.getElementById('storySub').textContent = `${{c.landmark}}  •  Demo Time ${{sh.t.toFixed(1)}}s ( Frame ${{curShot + 1}} / ${{DATA.shots.length}} )`;
  highlightChapter(cardIdx);
}}

function stopAutoPlay() {{
  if (autoTimer) {{ clearInterval(autoTimer); autoTimer = null; }}
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
    }}, 3000);
  }}
}};

DATA.cards.forEach((c, idx) => {{
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'chap-btn' + (idx === 0 ? ' on' : '') + (c.card >= 5 ? ' milky' : '');
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
  b.onclick = () => playUri(ex.uri, b);
  sfxGrid.appendChild(b);
}});

DATA.cards.forEach((c, idx) => {{
  const el = document.createElement('article');
  el.className = 'landmark-card' + (c.card >= 6 ? ' milky-highlight' : '');
  let activeLocalShot = c.shots[0];

  const switchHtml = c.shots.length > 1
    ? `<div class="shot-switch">${{c.shots.map((sIdx, k) =>
        `<button type="button" class="mini-pill ${{k===0?'on':''}}" data-sidx="${{sIdx}}">Shot ${{k+1}}</button>`
      ).join('')}}</div>`
    : '';

  const tagsHtml = [
    ...c.weapons.map(w => `<span class="tag wep">🔫 ${{w}}</span>`),
    ...c.vehicles.map(v => `<span class="tag veh">🚐 ${{v}}</span>`),
    ...c.chars.map(ch => `<span class="tag chr">🛞 ${{ch}}</span>`),
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

function renderEncyclopedia(kind) {{
  document.getElementById('encTabWep').classList.toggle('active', kind === 'wep');
  document.getElementById('encTabChr').classList.toggle('active', kind === 'chr');
  document.getElementById('encTabVeh').classList.toggle('active', kind === 'veh');
  encGrid.innerHTML = '';
  if (kind === 'wep') {{
    DATA.weaponsDb.forEach(w => {{
      const d = document.createElement('div');
      d.className = 'enc-item';
      d.innerHTML = `<h4><span>${{w.name}}</span><span style="color:#94a3b8;font-size:11.5px">${{w.qc}}</span></h4><code>${{w.models}}</code><p>${{w.role}}</p>`;
      encGrid.appendChild(d);
    }});
  }} else if (kind === 'chr') {{
    DATA.charsDb.forEach(c => {{
      const d = document.createElement('div');
      d.className = 'enc-item';
      d.innerHTML = `<h4><span>${{c.name}}</span></h4><code>${{c.asset}}</code><p>${{c.desc}}</p>`;
      encGrid.appendChild(d);
    }});
  }} else {{
    DATA.vehiclesDb.forEach(v => {{
      const d = document.createElement('div');
      d.className = 'enc-item';
      d.innerHTML = `<h4><span>${{v.name}}</span></h4><code>${{v.asset}}</code><p>${{v.desc}}</p>`;
      encGrid.appendChild(d);
    }});
  }}
}}
document.getElementById('encTabWep').onclick = () => renderEncyclopedia('wep');
document.getElementById('encTabChr').onclick = () => renderEncyclopedia('chr');
document.getElementById('encTabVeh').onclick = () => renderEncyclopedia('veh');
renderEncyclopedia('wep');

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
